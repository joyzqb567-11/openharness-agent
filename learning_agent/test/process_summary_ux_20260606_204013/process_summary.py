"""终端过程摘要渲染器：把主循环事件翻译成用户可读进度。"""  # 新增代码+ProcessSummaryUX: 说明本文件只负责显示安全过程摘要；若没有这行代码，维护者容易误把它当成模型推理实现。
from __future__ import annotations  # 新增代码+ProcessSummaryUX: 允许类型注解延迟解析；若没有这行代码，后续前向类型在旧解释顺序下更容易出错。
import sys  # 新增代码+ProcessSummaryUX: 提供默认 stdout 输出目标；若没有这行代码，真实终端入口必须额外传入 stream 才能显示摘要。
from typing import Any, TextIO  # 新增代码+ProcessSummaryUX: 标注事件和输出流的通用类型；若没有这行代码，回调接口边界会变得不清楚。

class TerminalProcessSummaryRenderer:  # 新增代码+ProcessSummaryUX: 函数段开始，定义把 AgentEvent 翻译成终端摘要的渲染器；若没有这段代码，用户只能看到最终答案，看不到 agent 正在观察、规划或调用工具的过程。本段会和 session_runtime 的 event_callback 配合，段落到类定义结束为止。
    def __init__(self, stream: TextIO | None = None, prefix: str = "Agent > ") -> None:  # 新增代码+ProcessSummaryUX: 初始化渲染器并允许测试注入 StringIO；若没有这行代码，测试无法稳定捕获真实终端文案。
        self.stream = stream or sys.stdout  # 新增代码+ProcessSummaryUX: 保存输出目标，默认写到真实终端；若没有这行代码，摘要没有地方显示给用户。
        self.prefix = prefix  # 新增代码+ProcessSummaryUX: 保存统一前缀；若没有这行代码，过程摘要和普通系统输出会混在一起。
        self._printed_once_keys: set[str] = set()  # 新增代码+ProcessSummaryUX: 记录只应显示一次的提示；若没有这行代码，run_started 等事件可能造成刷屏。

    def handle_event(self, event: Any) -> None:  # 新增代码+ProcessSummaryUX: 函数段开始，接收主循环事件并选择安全摘要文案；若没有这段代码，interactive.py 无法把 run_events 转成 Codex 风格过程提示。本段只显示摘要，不显示隐藏推理和原始工具输出，段落到函数 return 路径结束。
        event_type = str(getattr(event, "event_type", ""))  # 新增代码+ProcessSummaryUX: 读取事件类型并容错转成字符串；若没有这行代码，duck type 事件会因为属性差异中断终端显示。
        payload = self._payload_from_event(event)  # 新增代码+ProcessSummaryUX: 读取事件载荷并保证是字典；若没有这行代码，后续摘要逻辑可能直接访问非字典而报错。
        if event_type == "run_started":  # 新增代码+ProcessSummaryUX: 识别任务开始事件；若没有这行代码，用户看不到 agent 已收到任务。
            self._print_once("run_started", "我已收到任务，正在理解用户意图。")  # 新增代码+ProcessSummaryUX: 显示任务接收摘要；若没有这行代码，长任务开始阶段会像卡住。
            return  # 新增代码+ProcessSummaryUX: 当前事件处理完毕直接返回；若没有这行代码，可能继续落入无关分支。
        if event_type == "initial_messages_built":  # 新增代码+ProcessSummaryUX: 识别上下文和工具清单已装配事件；若没有这行代码，用户不知道模型即将基于哪些信息工作。
            self._print_once("initial_messages_built", "已准备上下文和工具清单，开始规划下一步。")  # 新增代码+ProcessSummaryUX: 显示安全规划摘要；若没有这行代码，用户体验不到模型主循环在做准备。
            return  # 新增代码+ProcessSummaryUX: 当前事件处理完毕直接返回；若没有这行代码，可能重复输出其他摘要。
        if event_type == "model_request_started":  # 新增代码+ProcessSummaryUX: 识别模型请求开始事件；若没有这行代码，用户看不到 agent 正在结合目标和工具做决策。
            turn_index = payload.get("turn_index", payload.get("turn", ""))  # 新增代码+ProcessSummaryUX: 尝试读取轮次编号；若没有这行代码，多轮工具循环时用户难以分辨进度。
            suffix = f"第 {turn_index} 轮" if str(turn_index).strip() else "本轮"  # 新增代码+ProcessSummaryUX: 生成自然的轮次描述；若没有这行代码，摘要会显得生硬或缺少上下文。
            self._print(f"正在结合用户目标、工具清单和当前观察规划{suffix}动作。")  # 新增代码+ProcessSummaryUX: 显示安全的规划过程摘要；若没有这行代码，模型请求阶段仍然是黑盒。
            return  # 新增代码+ProcessSummaryUX: 当前事件处理完毕直接返回；若没有这行代码，可能误进入其他分支。
        if event_type == "model_message_completed":  # 新增代码+ProcessSummaryUX: 识别模型消息完成事件；若没有这行代码，用户不知道模型是否已经产生下一步决定。
            tool_calls = payload.get("tool_calls", [])  # 新增代码+ProcessSummaryUX: 读取模型决定调用的工具列表；若没有这行代码，摘要无法说明下一步要调用工具还是输出答案。
            if isinstance(tool_calls, list) and tool_calls:  # 新增代码+ProcessSummaryUX: 判断本轮是否包含工具调用；若没有这行代码，所有模型消息都会被错误显示成最终回复。
                tool_names = ", ".join(str(item.get("name", "")) for item in tool_calls if isinstance(item, dict) and item.get("name"))  # 新增代码+ProcessSummaryUX: 提取工具名称而不展示原始参数；若没有这行代码，用户看不到工具选择，但也可能泄露过多细节。
                self._print(f"模型已决定下一步，准备使用工具：{tool_names or '未命名工具'}。")  # 新增代码+ProcessSummaryUX: 显示工具选择摘要；若没有这行代码，工具调用前缺少可读解释。
            else:  # 新增代码+ProcessSummaryUX: 处理没有工具调用的模型消息；若没有这行代码，最终回答前不会有收束提示。
                self._print("已形成回复草案，准备收束本轮任务。")  # 新增代码+ProcessSummaryUX: 显示回复收束摘要；若没有这行代码，用户不知道 agent 已经完成推理输出阶段。
            return  # 新增代码+ProcessSummaryUX: 当前事件处理完毕直接返回；若没有这行代码，可能继续处理成工具事件。
        if event_type == "tool_call_started":  # 新增代码+ProcessSummaryUX: 识别工具调用开始事件；若没有这行代码，用户看不到 agent 即将操作电脑、文件或终端。
            tool_call = payload.get("tool_call", {})  # 新增代码+ProcessSummaryUX: 读取工具调用对象；若没有这行代码，无法从事件中提取工具名称和安全摘要。
            tool_name = self._tool_name_from_call(tool_call)  # 新增代码+ProcessSummaryUX: 安全提取工具名称；若没有这行代码，终端摘要无法说明即将调用哪个工具。
            arguments = self._tool_arguments_from_call(tool_call)  # 新增代码+ProcessSummaryUX: 安全提取工具参数用于压缩摘要；若没有这行代码，摘要无法说明工具用途。
            self._print(f"准备调用 {tool_name}：{self._tool_action_summary(tool_name, arguments)}。")  # 新增代码+ProcessSummaryUX: 显示工具调用计划而不泄露完整参数；若没有这行代码，工具执行仍像黑盒。
            return  # 新增代码+ProcessSummaryUX: 当前事件处理完毕直接返回；若没有这行代码，可能误处理为完成事件。
        if event_type == "tool_call_completed":  # 新增代码+ProcessSummaryUX: 识别工具调用完成事件；若没有这行代码，用户不知道工具是否已经返回。
            tool_name = str(payload.get("tool_name", payload.get("name", "tool")))  # 新增代码+ProcessSummaryUX: 提取完成事件中的工具名称；若没有这行代码，完成摘要会缺少对象。
            self._print(f"已完成 {tool_name}：{self._tool_result_summary(tool_name, payload)}。")  # 新增代码+ProcessSummaryUX: 显示压缩后的工具结果，不展示原始输出；若没有这行代码，敏感日志可能被刷到终端。
            return  # 新增代码+ProcessSummaryUX: 当前事件处理完毕直接返回；若没有这行代码，可能继续落入失败或完成分支。
        if event_type == "run_failed":  # 新增代码+ProcessSummaryUX: 识别运行失败事件；若没有这行代码，用户只会突然看到错误文本。
            self._print("任务执行遇到错误，准备返回可读失败摘要。")  # 新增代码+ProcessSummaryUX: 显示失败收束摘要；若没有这行代码，失败体验缺少上下文。
            return  # 新增代码+ProcessSummaryUX: 当前事件处理完毕直接返回；若没有这行代码，失败事件可能继续被误处理。
        if event_type == "run_completed":  # 新增代码+ProcessSummaryUX: 识别运行完成事件；若没有这行代码，最终答案前没有明确收束信号。
            self._print("任务已收束，准备输出最终回答。")  # 新增代码+ProcessSummaryUX: 显示完成摘要；若没有这行代码，用户不知道后面的文本是最终输出。
            return  # 新增代码+ProcessSummaryUX: 当前事件处理完毕直接返回；若没有这行代码，函数会继续执行到末尾。
        return  # 新增代码+ProcessSummaryUX: 忽略未知或过细事件；若没有这行代码，未来事件可能被误展示为噪音。

    def _payload_from_event(self, event: Any) -> dict[str, Any]:  # 新增代码+ProcessSummaryUX: 函数段开始，把任意事件对象转成安全 payload 字典；若没有这段代码，渲染器会强依赖 AgentEvent 具体实现。本段为所有事件分支提供容错输入，段落到 return 结束。
        payload = getattr(event, "payload", {})  # 新增代码+ProcessSummaryUX: 从事件对象读取 payload；若没有这行代码，摘要无法获得工具名、轮次等上下文。
        if isinstance(payload, dict):  # 新增代码+ProcessSummaryUX: 确认 payload 是字典；若没有这行代码，后续 `.get` 调用可能崩溃。
            return payload  # 新增代码+ProcessSummaryUX: 返回原字典给摘要逻辑使用；若没有这行代码，合法事件也会被丢弃上下文。
        return {}  # 新增代码+ProcessSummaryUX: 非字典载荷返回空字典兜底；若没有这行代码，异常事件会中断主循环显示。

    def _tool_name_from_call(self, tool_call: Any) -> str:  # 新增代码+ProcessSummaryUX: 函数段开始，兼容字典和对象形式的工具调用；若没有这段代码，不同模型适配器的 tool_call 形态会让摘要失效。本段只提取名称，段落到 return 结束。
        if isinstance(tool_call, dict):  # 新增代码+ProcessSummaryUX: 处理 transcript 中常见的字典工具调用；若没有这行代码，测试和 JSON 事件无法显示工具名。
            return str(tool_call.get("name", "tool"))  # 新增代码+ProcessSummaryUX: 从字典读取工具名称；若没有这行代码，摘要只能显示泛化工具。
        return str(getattr(tool_call, "name", "tool"))  # 新增代码+ProcessSummaryUX: 从对象读取工具名称；若没有这行代码，真实 ToolCall 对象无法被摘要渲染。

    def _tool_arguments_from_call(self, tool_call: Any) -> dict[str, Any]:  # 新增代码+ProcessSummaryUX: 函数段开始，提取工具参数用于安全压缩；若没有这段代码，用户看不到工具调用意图。本段不会直接输出完整参数，段落到 return 结束。
        if isinstance(tool_call, dict):  # 新增代码+ProcessSummaryUX: 处理字典形态工具调用；若没有这行代码，测试事件无法生成动作摘要。
            arguments = tool_call.get("arguments", {})  # 新增代码+ProcessSummaryUX: 读取字典参数；若没有这行代码，动作摘要会缺少 app/action 信息。
            return arguments if isinstance(arguments, dict) else {}  # 新增代码+ProcessSummaryUX: 只接受字典参数并兜底；若没有这行代码，字符串参数可能让摘要逻辑崩溃。
        arguments = getattr(tool_call, "arguments", {})  # 新增代码+ProcessSummaryUX: 读取对象参数；若没有这行代码，真实 ToolCall 无法显示动作摘要。
        return arguments if isinstance(arguments, dict) else {}  # 新增代码+ProcessSummaryUX: 返回安全参数字典；若没有这行代码，非字典参数会污染摘要逻辑。

    def _tool_action_summary(self, tool_name: str, arguments: dict[str, Any]) -> str:  # 新增代码+ProcessSummaryUX: 函数段开始，把工具参数压缩成人话；若没有这段代码，终端只能显示生硬工具名。本段刻意不输出完整参数，段落到最终 return 结束。
        action = str(arguments.get("action", arguments.get("operation", "")))  # 新增代码+ProcessSummaryUX: 提取桌面或工具动作；若没有这行代码，无法区分启动应用、点击、拖拽等意图。
        if tool_name == "computer_observe":  # 新增代码+ProcessSummaryUX: 识别屏幕观察工具；若没有这行代码，观察动作会显示得过于泛化。
            return "观察屏幕和窗口状态"  # 新增代码+ProcessSummaryUX: 返回观察摘要；若没有这行代码，用户不知道 agent 正在看屏幕。
        if tool_name == "computer_action":  # 新增代码+ProcessSummaryUX: 识别桌面动作工具；若没有这行代码，鼠标键盘动作无法显示成可懂意图。
            if action == "launch_app":  # 新增代码+ProcessSummaryUX: 识别启动应用动作；若没有这行代码，打开 Paint/Notepad 等关键步骤无法被用户理解。
                app_name = str(arguments.get("app_name", arguments.get("target_app", arguments.get("app", "应用"))))  # 新增代码+ProcessSummaryUX: 提取应用名并兜底；若没有这行代码，启动动作摘要会缺少目标。
                return f"启动应用 {app_name}"  # 新增代码+ProcessSummaryUX: 返回启动应用摘要；若没有这行代码，用户看不到 agent 打算打开哪个软件。
            if action in {"click", "mouse_click"}:  # 新增代码+ProcessSummaryUX: 识别鼠标点击动作；若没有这行代码，点击会被显示成泛化桌面动作。
                return "执行鼠标点击"  # 新增代码+ProcessSummaryUX: 返回点击摘要；若没有这行代码，用户看不到下一步是点击。
            if action in {"drag_path", "drag", "mouse_drag"}:  # 新增代码+ProcessSummaryUX: 识别鼠标拖拽动作；若没有这行代码，绘画和拖动类任务缺少过程感。
                return "执行鼠标拖拽轨迹"  # 新增代码+ProcessSummaryUX: 返回拖拽摘要；若没有这行代码，用户不知道 agent 正在画线或拖动。
            if action in {"type_text", "type", "keyboard_type"}:  # 新增代码+ProcessSummaryUX: 识别键盘输入动作；若没有这行代码，输入文本步骤会显得不透明。
                return "输入文本"  # 新增代码+ProcessSummaryUX: 返回输入摘要；若没有这行代码，用户不知道 agent 准备键入内容。
            return f"执行桌面动作 {action or '未命名动作'}"  # 新增代码+ProcessSummaryUX: 返回桌面动作兜底摘要；若没有这行代码，新动作类型会没有可读提示。
        if tool_name == "computer_use":  # 新增代码+ProcessSummaryUX: 识别 Computer Use 统一工具；若没有这行代码，顶层 computer_use 调用缺少专属摘要。
            return f"执行 Computer Use {action or '操作'}"  # 新增代码+ProcessSummaryUX: 返回 Computer Use 摘要；若没有这行代码，用户难以理解桌面控制入口。
        if tool_name == "bash":  # 新增代码+ProcessSummaryUX: 识别终端命令工具；若没有这行代码，shell 操作会显示成泛化工具。
            return "运行终端命令"  # 新增代码+ProcessSummaryUX: 返回终端命令摘要；若没有这行代码，用户不知道 agent 正在调用命令行。
        if tool_name in {"read", "write", "edit"}:  # 新增代码+ProcessSummaryUX: 识别文件工具；若没有这行代码，文件读写操作缺少清楚分类。
            return f"执行文件{tool_name}操作"  # 新增代码+ProcessSummaryUX: 返回文件工具摘要；若没有这行代码，用户看不到 agent 正在处理文件。
        return "执行工具操作"  # 新增代码+ProcessSummaryUX: 返回未知工具兜底摘要；若没有这行代码，新工具会没有显示文案。

    def _tool_result_summary(self, tool_name: str, payload: dict[str, Any]) -> str:  # 新增代码+ProcessSummaryUX: 函数段开始，把工具结果压缩成安全摘要；若没有这段代码，终端可能泄露长日志或敏感字段。本段只输出统计和类别，不输出原始 output，段落到最终 return 结束。
        raw_output_chars = payload.get("raw_output_chars", "")  # 新增代码+ProcessSummaryUX: 读取原始输出长度用于统计；若没有这行代码，用户无法知道工具确实返回过结果。
        if tool_name.startswith("computer_") or tool_name == "computer_use":  # 新增代码+ProcessSummaryUX: 识别桌面工具结果；若没有这行代码，桌面观察/动作的结果会显示得不贴近任务。
            return "已返回桌面操作结果和可观察证据"  # 新增代码+ProcessSummaryUX: 返回桌面结果摘要；若没有这行代码，用户不知道屏幕动作是否有反馈。
        if str(raw_output_chars).strip():  # 新增代码+ProcessSummaryUX: 判断是否存在输出长度；若没有这行代码，普通工具结果缺少规模提示。
            return f"工具返回结果（约 {raw_output_chars} 字符）"  # 新增代码+ProcessSummaryUX: 只显示长度不显示内容；若没有这行代码，原始输出可能被直接刷屏。
        return "工具返回结果"  # 新增代码+ProcessSummaryUX: 返回通用完成摘要；若没有这行代码，无长度结果会没有可读收束。

    def _print_once(self, key: str, message: str) -> None:  # 新增代码+ProcessSummaryUX: 函数段开始，去重输出一次性提示；若没有这段代码，重复事件会让终端噪音变大。本段配合 `_printed_once_keys`，段落到函数结束。
        if key in self._printed_once_keys:  # 新增代码+ProcessSummaryUX: 检查消息是否已显示；若没有这行代码，重试或恢复时同一句会不断刷屏。
            return  # 新增代码+ProcessSummaryUX: 已显示则跳过；若没有这行代码，去重检查没有效果。
        self._printed_once_keys.add(key)  # 新增代码+ProcessSummaryUX: 标记消息已显示；若没有这行代码，下一次仍会重复输出。
        self._print(message)  # 新增代码+ProcessSummaryUX: 调用统一打印方法；若没有这行代码，一次性提示不会实际显示。

    def _print(self, message: str) -> None:  # 新增代码+ProcessSummaryUX: 函数段开始，统一写入终端并刷新；若没有这段代码，各分支会重复 print 细节且难以测试。本段是所有摘要显示的唯一出口，段落到函数结束。
        print(f"{self.prefix}{message}", file=self.stream, flush=True)  # 新增代码+ProcessSummaryUX: 打印前缀和摘要并立即刷新；若没有这行代码，用户可能直到最终答案才看到过程提示。
