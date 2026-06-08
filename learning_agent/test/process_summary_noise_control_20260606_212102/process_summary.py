"""终端过程摘要渲染器：把主循环事件翻译成用户可读进度。"""  # 新增代码+ProcessSummaryUX: 说明本文件只负责显示安全过程摘要；若没有这行代码，维护者容易误把它当成模型推理实现。
from __future__ import annotations  # 新增代码+ProcessSummaryUX: 允许类型注解延迟解析；若没有这行代码，后续前向类型在旧解释顺序下更容易出错。
import sys  # 新增代码+ProcessSummaryUX: 提供默认 stdout 输出目标；若没有这行代码，真实终端入口必须额外传入 stream 才能显示摘要。
from typing import Any, TextIO  # 新增代码+ProcessSummaryUX: 标注事件和输出流的通用类型；若没有这行代码，回调接口边界会变得不清楚。

class TerminalProcessSummaryRenderer:  # 新增代码+ProcessSummaryUX: 函数段开始，定义把 AgentEvent 翻译成终端摘要的渲染器；若没有这段代码，用户只能看到最终答案，看不到 agent 正在观察、规划或调用工具的过程。本段会和 session_runtime 的 event_callback 配合，段落到类定义结束为止。
    def __init__(self, stream: TextIO | None = None, prefix: str = "Agent > ") -> None:  # 新增代码+ProcessSummaryUX: 初始化渲染器并允许测试注入 StringIO；若没有这行代码，测试无法稳定捕获真实终端文案。
        self.stream = stream or sys.stdout  # 新增代码+ProcessSummaryUX: 保存输出目标，默认写到真实终端；若没有这行代码，摘要没有地方显示给用户。
        self.prefix = prefix  # 新增代码+ProcessSummaryUX: 保存统一前缀；若没有这行代码，过程摘要和普通系统输出会混在一起。
        self._printed_once_keys: set[str] = set()  # 新增代码+ProcessSummaryUX: 记录只应显示一次的提示；若没有这行代码，run_started 等事件可能造成刷屏。
        self._tool_started_count = 0  # 修改代码+ProcessSummaryNoiseControl: 记录已显示或处理的工具开始次数；若没有这行代码，长 Computer Use 循环无法按次数节流。
        self._tool_completed_count = 0  # 修改代码+ProcessSummaryNoiseControl: 记录已处理的工具完成次数；若没有这行代码，桌面动作完成提示会在绘图任务里刷屏。
        self._final_draft_printed = False  # 修改代码+ProcessSummaryNoiseControl: 记录最终回复草案提示是否已经出现；若没有这行代码，模型多次无工具回复会重复显示收束文案。
        self._last_model_turn_printed = -1  # 修改代码+ProcessSummaryNoiseControl: 保存上次已显示的模型轮次；若没有这行代码，重复事件会把同一轮规划打印多次。

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
            turn_index = self._turn_from_payload(payload)  # 修改代码+ProcessSummaryNoiseControl: 统一读取生产事件中的 turn/turn_index；若没有这行代码，真实运行和测试事件会各走一套轮次解析。
            if not self._should_print_model_turn(turn_index):  # 修改代码+ProcessSummaryNoiseControl: 对高频模型轮次做节流；若没有这行代码，长桌面任务会像左图一样每轮刷屏。
                return  # 修改代码+ProcessSummaryNoiseControl: 当前轮次不需要显示时直接跳过；若没有这行代码，节流判断不会生效。
            suffix = f"第 {turn_index} 轮" if turn_index >= 0 else "本轮"  # 修改代码+ProcessSummaryNoiseControl: 生成稳定轮次描述；若没有这行代码，未知轮次会显示成奇怪空字符串。
            self._print(f"正在结合用户目标、工具清单和当前观察规划{suffix}动作。")  # 新增代码+ProcessSummaryUX: 显示安全的规划过程摘要；若没有这行代码，模型请求阶段仍然是黑盒。
            return  # 新增代码+ProcessSummaryUX: 当前事件处理完毕直接返回；若没有这行代码，可能误进入其他分支。
        if event_type == "model_message_completed":  # 新增代码+ProcessSummaryUX: 识别模型消息完成事件；若没有这行代码，用户不知道模型是否已经产生下一步决定。
            turn_index = self._turn_from_payload(payload)  # 修改代码+ProcessSummaryNoiseControl: 读取模型完成事件轮次用于节流；若没有这行代码，工具决策提示无法和模型轮次对齐。
            tool_calls = self._tool_calls_from_model_payload(payload)  # 修改代码+ProcessSummaryNoiseControl: 兼容生产事件 message.tool_calls；若没有这行代码，真实模型工具调用会被误显示成“回复草案”。
            if isinstance(tool_calls, list) and tool_calls:  # 新增代码+ProcessSummaryUX: 判断本轮是否包含工具调用；若没有这行代码，所有模型消息都会被错误显示成最终回复。
                if self._should_print_model_turn(turn_index):  # 修改代码+ProcessSummaryNoiseControl: 只在关键轮次显示工具选择；若没有这行代码，模型每轮选工具都会重复刷屏。
                    tool_names = self._join_tool_names(tool_calls)  # 修改代码+ProcessSummaryNoiseControl: 统一提取 name/tool_name 字段；若没有这行代码，真实工具名会丢失或显示成未命名。
                    self._print(f"模型已决定下一步，准备使用工具：{tool_names or '未命名工具'}。")  # 修改代码+ProcessSummaryNoiseControl: 显示节流后的工具选择摘要；若没有这行代码，用户看不到模型下一步意图。
            else:  # 新增代码+ProcessSummaryUX: 处理没有工具调用的模型消息；若没有这行代码，最终回答前不会有收束提示。
                if not self._final_draft_printed:  # 修改代码+ProcessSummaryNoiseControl: 最终草案提示只显示一次；若没有这行代码，多轮无工具消息会反复提示即将收束。
                    self._final_draft_printed = True  # 修改代码+ProcessSummaryNoiseControl: 标记收束提示已经显示；若没有这行代码，下一次仍会重复打印。
                    self._print("已形成回复草案，准备收束本轮任务。")  # 修改代码+ProcessSummaryNoiseControl: 显示一次回复收束摘要；若没有这行代码，用户不知道 agent 已经进入最终输出阶段。
            return  # 新增代码+ProcessSummaryUX: 当前事件处理完毕直接返回；若没有这行代码，可能继续处理成工具事件。
        if event_type == "tool_call_started":  # 新增代码+ProcessSummaryUX: 识别工具调用开始事件；若没有这行代码，用户看不到 agent 即将操作电脑、文件或终端。
            tool_call = payload.get("tool_call", {})  # 新增代码+ProcessSummaryUX: 读取工具调用对象；若没有这行代码，无法从事件中提取工具名称和安全摘要。
            tool_name = self._tool_name_from_call(tool_call)  # 新增代码+ProcessSummaryUX: 安全提取工具名称；若没有这行代码，终端摘要无法说明即将调用哪个工具。
            arguments = self._tool_arguments_from_call(tool_call)  # 新增代码+ProcessSummaryUX: 安全提取工具参数用于压缩摘要；若没有这行代码，摘要无法说明工具用途。
            self._tool_started_count += 1  # 修改代码+ProcessSummaryNoiseControl: 累计工具开始事件数量；若没有这行代码，无法判断哪些重复桌面动作应被压缩。
            if not self._should_print_tool_event(tool_name, self._tool_started_count, arguments):  # 修改代码+ProcessSummaryNoiseControl: 跳过高频重复桌面动作；若没有这行代码，鼠标拖拽会把终端刷满。
                return  # 修改代码+ProcessSummaryNoiseControl: 高频事件被压缩后直接返回；若没有这行代码，节流判断不会减少输出。
            self._print(f"准备调用 {tool_name}：{self._tool_action_summary(tool_name, arguments)}。")  # 新增代码+ProcessSummaryUX: 显示工具调用计划而不泄露完整参数；若没有这行代码，工具执行仍像黑盒。
            return  # 新增代码+ProcessSummaryUX: 当前事件处理完毕直接返回；若没有这行代码，可能误处理为完成事件。
        if event_type == "tool_call_completed":  # 新增代码+ProcessSummaryUX: 识别工具调用完成事件；若没有这行代码，用户不知道工具是否已经返回。
            tool_name = str(payload.get("tool_name", payload.get("name", "tool")))  # 新增代码+ProcessSummaryUX: 提取完成事件中的工具名称；若没有这行代码，完成摘要会缺少对象。
            self._tool_completed_count += 1  # 修改代码+ProcessSummaryNoiseControl: 累计工具完成事件数量；若没有这行代码，无法周期性展示桌面反馈进度。
            if not self._should_print_tool_event(tool_name, self._tool_completed_count, {}):  # 修改代码+ProcessSummaryNoiseControl: 对高频工具完成事件做节流；若没有这行代码，每次 observe/action 都会重复输出完成摘要。
                return  # 修改代码+ProcessSummaryNoiseControl: 被压缩的完成事件直接跳过；若没有这行代码，终端仍然会被重复完成提示占满。
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

    def _turn_from_payload(self, payload: dict[str, Any]) -> int:  # 修改代码+ProcessSummaryNoiseControl: 函数段开始，统一从事件载荷读取轮次；若没有这段代码，节流逻辑会散落在多个事件分支里。本段被模型请求和模型完成事件共用，段落到 return 结束。
        raw_turn = payload.get("turn_index", payload.get("turn", -1))  # 修改代码+ProcessSummaryNoiseControl: 同时兼容旧测试字段和生产字段；若没有这行代码，真实主循环 turn 字段会被忽略。
        try:  # 修改代码+ProcessSummaryNoiseControl: 尝试把轮次转换为整数；若没有这行代码，字符串轮次会导致取模节流失败。
            return int(raw_turn)  # 修改代码+ProcessSummaryNoiseControl: 返回可比较可取模的轮次；若没有这行代码，后续无法稳定判断关键轮次。
        except (TypeError, ValueError):  # 修改代码+ProcessSummaryNoiseControl: 捕获空值或非数字轮次；若没有这行代码，异常 payload 会中断终端显示。
            return -1  # 修改代码+ProcessSummaryNoiseControl: 用 -1 表示未知轮次；若没有这行代码，未知轮次无法有统一兜底。

    def _should_print_model_turn(self, turn_index: int) -> bool:  # 修改代码+ProcessSummaryNoiseControl: 函数段开始，决定哪些模型轮次需要展示；若没有这段代码，长任务会把每轮规划都刷到终端。本段用于模型请求和模型工具决策节流，段落到 return 结束。
        if turn_index < 0:  # 修改代码+ProcessSummaryNoiseControl: 未知轮次保守显示；若没有这行代码，缺少轮次的真实事件可能完全无提示。
            return True  # 修改代码+ProcessSummaryNoiseControl: 返回显示未知轮次；若没有这行代码，某些模型适配器事件会被静默吞掉。
        if turn_index == self._last_model_turn_printed:  # 修改代码+ProcessSummaryNoiseControl: 避免同一轮在 request/completed 两个事件里重复显示；若没有这行代码，单轮也会出现两条相似规划提示。
            return False  # 修改代码+ProcessSummaryNoiseControl: 已显示过的轮次不再显示；若没有这行代码，去重没有效果。
        should_print = turn_index <= 1 or turn_index % 5 == 0  # 修改代码+ProcessSummaryNoiseControl: 前两轮密集提示，之后每 5 轮提示一次；若没有这行代码，用户要么看不到进度要么看到刷屏。
        if should_print:  # 修改代码+ProcessSummaryNoiseControl: 只有确实要显示时才更新上次轮次；若没有这行代码，被跳过的轮次会错误占用去重状态。
            self._last_model_turn_printed = turn_index  # 修改代码+ProcessSummaryNoiseControl: 保存已显示轮次；若没有这行代码，同一轮会重复显示。
        return should_print  # 修改代码+ProcessSummaryNoiseControl: 返回节流结果；若没有这行代码，调用方无法决定是否打印。

    def _tool_calls_from_model_payload(self, payload: dict[str, Any]) -> list[Any]:  # 修改代码+ProcessSummaryNoiseControl: 函数段开始，读取模型完成事件中的工具调用；若没有这段代码，生产事件的 message.tool_calls 会被漏读。本段兼容旧字段和新字段，段落到 return 结束。
        direct_tool_calls = payload.get("tool_calls", [])  # 修改代码+ProcessSummaryNoiseControl: 先读取旧测试或未来直接字段；若没有这行代码，已有测试事件会失去兼容。
        if isinstance(direct_tool_calls, list) and direct_tool_calls:  # 修改代码+ProcessSummaryNoiseControl: 如果直接字段已有工具调用就使用它；若没有这行代码，会不必要地进入嵌套解析。
            return direct_tool_calls  # 修改代码+ProcessSummaryNoiseControl: 返回直接工具调用列表；若没有这行代码，旧事件会被误判无工具。
        message = payload.get("message", {})  # 修改代码+ProcessSummaryNoiseControl: 读取生产事件中的 message 字典；若没有这行代码，真实模型工具调用无法被发现。
        if isinstance(message, dict):  # 修改代码+ProcessSummaryNoiseControl: 只有 message 是字典时才安全读取；若没有这行代码，非字典 message 会触发异常。
            nested_tool_calls = message.get("tool_calls", [])  # 修改代码+ProcessSummaryNoiseControl: 从 message.tool_calls 读取真实主循环工具调用；若没有这行代码，终端会误报“回复草案”。
            return nested_tool_calls if isinstance(nested_tool_calls, list) else []  # 修改代码+ProcessSummaryNoiseControl: 只返回列表，异常形态兜底为空；若没有这行代码，后续遍历可能崩溃。
        return []  # 修改代码+ProcessSummaryNoiseControl: 没有工具调用时返回空列表；若没有这行代码，调用方需要处理 None。

    def _join_tool_names(self, tool_calls: list[Any]) -> str:  # 修改代码+ProcessSummaryNoiseControl: 函数段开始，把工具调用列表压缩成工具名字符串；若没有这段代码，name/tool_name 兼容会在多处重复。本段只输出工具名，不输出参数，段落到 return 结束。
        names: list[str] = []  # 修改代码+ProcessSummaryNoiseControl: 准备保存可显示工具名；若没有这行代码，无法逐个过滤空名称。
        for item in tool_calls:  # 修改代码+ProcessSummaryNoiseControl: 遍历模型决定调用的工具；若没有这行代码，多个工具无法合并显示。
            names.append(self._tool_name_from_call(item))  # 修改代码+ProcessSummaryNoiseControl: 复用工具名兼容函数；若没有这行代码，生产字段 tool_name 仍可能显示成 tool。
        return ", ".join(name for name in names if name and name != "tool")  # 修改代码+ProcessSummaryNoiseControl: 合并非空非兜底工具名；若没有这行代码，摘要会出现无意义的 tool 列表。

    def _tool_name_from_call(self, tool_call: Any) -> str:  # 新增代码+ProcessSummaryUX: 函数段开始，兼容字典和对象形式的工具调用；若没有这段代码，不同模型适配器的 tool_call 形态会让摘要失效。本段只提取名称，段落到 return 结束。
        if isinstance(tool_call, dict):  # 新增代码+ProcessSummaryUX: 处理 transcript 中常见的字典工具调用；若没有这行代码，测试和 JSON 事件无法显示工具名。
            return str(tool_call.get("tool_name", tool_call.get("name", "tool")))  # 修改代码+ProcessSummaryNoiseControl: 优先读取生产事件的 tool_name 字段；若没有这行代码，真实终端会继续显示“tool”而不是 computer_action。
        return str(getattr(tool_call, "tool_name", getattr(tool_call, "name", "tool")))  # 修改代码+ProcessSummaryNoiseControl: 对象形态也兼容 tool_name/name；若没有这行代码，新适配器对象可能丢失工具名。

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

    def _should_print_tool_event(self, tool_name: str, count: int, arguments: dict[str, Any]) -> bool:  # 修改代码+ProcessSummaryNoiseControl: 函数段开始，判断工具事件是否应展示；若没有这段代码，桌面工具在绘图任务中会产生大量重复行。本段保护终端 UX，同时保留关键启动和周期进度，段落到 return 结束。
        if not (tool_name.startswith("computer_") or tool_name == "computer_use"):  # 修改代码+ProcessSummaryNoiseControl: 非桌面工具默认显示；若没有这行代码，文件和终端工具进度可能被误压缩。
            return True  # 修改代码+ProcessSummaryNoiseControl: 普通工具不节流；若没有这行代码，用户可能看不到文件/命令操作。
        action = str(arguments.get("action", arguments.get("operation", "")))  # 修改代码+ProcessSummaryNoiseControl: 读取桌面动作类型；若没有这行代码，启动应用等关键动作无法单独放行。
        if action == "launch_app":  # 修改代码+ProcessSummaryNoiseControl: 启动应用属于关键动作；若没有这行代码，用户看不到 agent 是否真的尝试打开软件。
            return True  # 修改代码+ProcessSummaryNoiseControl: 始终显示启动应用；若没有这行代码，最重要的桌面入口会被节流吞掉。
        return count <= 3 or count % 5 == 0  # 修改代码+ProcessSummaryNoiseControl: 前三次显示，之后每五次显示一次；若没有这行代码，终端无法兼顾进度感和低噪声。

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
