"""OS 级 Computer Use 控制器。"""  # 新增代码+OSComputerUse: 集中管理桌面控制的安全边界；若没有这个文件，桌面动作会散落在 agent 方法里难以审计。

from __future__ import annotations  # 新增代码+OSComputerUse: 延迟解析类型注解；若没有这行代码，Protocol 等注解在旧执行路径中更容易产生导入顺序问题。

import os  # 新增代码+Phase8ProductionEdges: 读取显式启用真实 Windows 后端的环境变量；如果没有这行代码，Computer Use 后端无法做到默认安全关闭。
import sys  # 新增代码+Phase8ProductionEdges: 判断当前平台是否为 Windows；如果没有这行代码，非 Windows 环境可能误报支持真实桌面控制。
from dataclasses import dataclass  # 新增代码+OSComputerUse: 使用 dataclass 表达动作结果；若没有这行代码，结果对象需要手写大量样板代码。
from typing import Any, Protocol  # 新增代码+OSComputerUse: 引入通用 JSON 参数和后端协议类型；若没有这行代码，控制器边界不清楚。

try:  # 新增代码+Phase27ComputerUse: 包运行模式下导入窗口协议模型；如果没有这行代码，控制器无法使用强类型窗口引用。
    from learning_agent.computer_use.models import build_window_ref, window_ref_identity  # 新增代码+Phase27ComputerUse: 读取窗口构造和身份键 helper；如果没有这行代码，未知窗口校验只能继续依赖松散 dict。
except ModuleNotFoundError as error:  # 新增代码+Phase27ComputerUse: 捕获直接脚本运行时包名不可用的情况；如果没有这行代码，start_oauth_agent.bat 的脚本模式可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.models"}:  # 新增代码+Phase27ComputerUse: 只允许目标包路径缺失时 fallback；如果没有这行代码，models 内部真实 bug 会被误吞。
        raise  # 新增代码+Phase27ComputerUse: 重新抛出真实导入错误；如果没有这行代码，排查协议模型问题会很困难。
    from computer_use.models import build_window_ref, window_ref_identity  # 新增代码+Phase27ComputerUse: 脚本模式下从本地 computer_use 包导入模型；如果没有这行代码，bat 入口无法加载 Phase 27 协议。


COMPUTER_USE_OPT_IN_ENV_VAR = "LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE"  # 新增代码+Phase20ComputerUse: 集中保存真实桌面控制的启用环境变量名；如果没有这行代码，状态输出和工厂逻辑可能写出不一致的开关名。


@dataclass(frozen=True)  # 新增代码+OSComputerUse: 让动作结果不可变，避免调用方事后改写审计事实；若没有这行代码，结果对象可能被无意污染。
class ComputerUseActionResult:  # 新增代码+OSComputerUse: 定义 Computer Use 动作统一返回结构；若没有这段代码，状态、错误和数据会以散乱字符串传递。
    ok: bool  # 新增代码+OSComputerUse: 表示动作是否成功；若没有这行代码，调用方无法稳定判断成功失败。
    message: str  # 新增代码+OSComputerUse: 保存给模型和用户看的中文说明；若没有这行代码，失败原因会丢失。
    data: dict[str, Any]  # 新增代码+OSComputerUse: 保存结构化附加数据；若没有这行代码，截图摘要、坐标或后端状态无法机器读取。

    def to_text(self, tool_name: str = "computer_action") -> str:  # 修改代码+Phase27ComputerUse: 允许 observe/action 共用结果转文本；如果没有这行代码，computer_observe 会被错误显示成 computer_action。
        status = "成功" if self.ok else "失败"  # 新增代码+OSComputerUse: 把布尔状态转换成用户容易理解的中文词；若没有这行代码，输出不够直观。
        return f"{tool_name} {status}：{self.message}\n数据：{self.data}"  # 修改代码+Phase27ComputerUse: 返回对应工具名、状态和数据；如果没有这行代码，观察结果与动作结果在终端里难以区分。


class ComputerUseBackend(Protocol):  # 新增代码+OSComputerUse: 定义真实/测试桌面后端必须实现的接口；若没有这段代码，后续接 Windows 后端没有稳定契约。
    def status(self) -> dict[str, Any]:  # 新增代码+OSComputerUse: 要求后端报告可用状态；若没有这行代码，状态工具无法知道后端是否能控制桌面。
        ...  # 新增代码+OSComputerUse: Protocol 方法占位；若没有这行代码，接口声明语法不完整。

    def observe(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase27ComputerUse: 要求后端实现只读观察协议；如果没有这行代码，controller 无法在动作前列出或校验窗口。
        ...  # 新增代码+Phase27ComputerUse: Protocol 方法占位；如果没有这行代码，接口声明语法不完整。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+OSComputerUse: 要求后端执行已通过安全检查的动作；若没有这行代码，控制器无法调用真实实现。
        ...  # 新增代码+OSComputerUse: Protocol 方法占位；若没有这行代码，接口声明语法不完整。


class UnavailableComputerUseBackend:  # 新增代码+OSComputerUse: 默认不可用后端，保证未配置时绝不控制真实桌面；若没有这段代码，项目初始化时可能找不到安全默认值。
    def status(self) -> dict[str, Any]:  # 新增代码+OSComputerUse: 返回默认后端状态；若没有这段代码，computer_status 无法说明为什么不可用。
        return {"available": False, "backend": "unavailable", "reason": f"未设置 {COMPUTER_USE_OPT_IN_ENV_VAR}=1，真实 OS Computer Use 默认安全关闭。", "real_actions_enabled": False, "opt_in_env_var": COMPUTER_USE_OPT_IN_ENV_VAR, "opt_in_enabled": False, "platform": sys.platform}  # 修改代码+Phase20ComputerUse: 把默认关闭原因、真实动作状态和启用开关一次说清楚；如果没有这行代码，用户无法确认系统不会误动鼠标键盘。

    def observe(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase27ComputerUse: 默认后端拒绝只读桌面观察；如果没有这段代码，未启用时 observe 可能返回误导性空数据。
        return ComputerUseActionResult(False, "OS Computer Use 后端尚未启用，未读取任何真实窗口信息。", {"action": action, "backend": "unavailable", "windows": []})  # 新增代码+Phase27ComputerUse: 返回清楚的未启用观察结果；如果没有这行代码，模型可能误以为桌面没有窗口。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+OSComputerUse: 拒绝所有真实桌面动作；若没有这段代码，默认后端可能意外执行副作用。
        return ComputerUseActionResult(False, "OS Computer Use 后端尚未启用，未执行任何真实桌面操作。", {"action": action, "backend": "unavailable"})  # 新增代码+OSComputerUse: 返回清楚拒绝结果；若没有这行代码，模型可能误以为动作已执行。


class MemoryComputerUseBackend:  # 新增代码+OSComputerUse: 测试专用后端，只记录动作不碰真实桌面；若没有这段代码，自动化测试无法验证成功路径。
    def __init__(self, windows: list[dict[str, Any]] | None = None, window_states: dict[tuple[str, str], dict[str, Any]] | None = None) -> None:  # 修改代码+Phase27ComputerUse: 初始化动作列表和可观察窗口目录；如果没有这段代码，Phase 27 无法测试窗口身份协议。
        self.actions: list[dict[str, Any]] = []  # 新增代码+OSComputerUse: 保存每次动作参数副本；若没有这行代码，测试无法证明动作被传递到后端。
        self.windows: list[dict[str, str]] = []  # 新增代码+Phase27ComputerUse: 保存规范化后的可观察窗口；如果没有这行代码，list_windows 无法返回稳定目标。
        for raw_window in windows or []:  # 新增代码+Phase27ComputerUse: 遍历测试传入的窗口描述；如果没有这行代码，内存后端无法加载已知窗口。
            window_ref = build_window_ref(raw_window)  # 新增代码+Phase27ComputerUse: 把松散窗口 dict 转成强类型引用；如果没有这行代码，窗口身份可能缺少 app_id/window_id。
            if window_ref is not None:  # 新增代码+Phase27ComputerUse: 只保留身份完整的窗口；如果没有这行代码，坏窗口会进入可信目录。
                self.windows.append(window_ref.to_dict())  # 新增代码+Phase27ComputerUse: 保存可序列化窗口引用；如果没有这行代码，observe 结果无法返回窗口列表。
        self.window_states: dict[tuple[str, str], dict[str, Any]] = dict(window_states or {})  # 新增代码+Phase27ComputerUse: 保存可选窗口状态覆盖；如果没有这行代码，测试无法模拟焦点、截图等观察状态。

    def status(self) -> dict[str, Any]:  # 新增代码+OSComputerUse: 返回测试后端状态；若没有这段代码，controller.status 无法在测试中表现为可用。
        return {"available": True, "backend": "memory", "reason": "测试后端只记录动作，不控制真实桌面。", "real_actions_enabled": False, "opt_in_env_var": COMPUTER_USE_OPT_IN_ENV_VAR, "opt_in_enabled": False, "platform": sys.platform, "evidence_mode": "memory_only", "window_count": len(self.windows)}  # 修改代码+Phase27ComputerUse: 在测试状态里报告已知窗口数量；如果没有这行代码，调试时看不出窗口目录是否加载。

    def _find_window(self, raw_window: Any) -> dict[str, str] | None:  # 新增代码+Phase27ComputerUse: 在内存窗口目录中查找目标窗口；如果没有这段函数，observe 和 action 校验会重复写匹配逻辑。
        window_ref = build_window_ref(raw_window)  # 新增代码+Phase27ComputerUse: 先把输入转换成强类型窗口引用；如果没有这行代码，缺字段窗口可能进入匹配流程。
        if window_ref is None:  # 新增代码+Phase27ComputerUse: 判断窗口引用是否有效；如果没有这行代码，坏参数会导致身份键生成失败。
            return None  # 新增代码+Phase27ComputerUse: 无效窗口直接返回未找到；如果没有这行代码，调用方无法区分未知和异常。
        target_identity = window_ref_identity(window_ref)  # 新增代码+Phase27ComputerUse: 生成目标窗口身份键；如果没有这行代码，匹配逻辑会散落重复。
        for known_window in self.windows:  # 新增代码+Phase27ComputerUse: 遍历已知窗口目录；如果没有这行代码，后端无法判断目标是否可信。
            known_ref = build_window_ref(known_window)  # 新增代码+Phase27ComputerUse: 把目录项转换为窗口引用；如果没有这行代码，目录项字段变化会影响匹配。
            if known_ref is not None and window_ref_identity(known_ref) == target_identity:  # 新增代码+Phase27ComputerUse: 比较 app_id/window_id 是否完全一致；如果没有这行代码，伪造标题可能绕过校验。
                return dict(known_window)  # 新增代码+Phase27ComputerUse: 返回窗口副本避免外部修改目录；如果没有这行代码，调用方可能污染内存后端状态。
        return None  # 新增代码+Phase27ComputerUse: 没找到时返回 None；如果没有这行代码，未知窗口无法被明确拒绝。

    def observe(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase27ComputerUse: 实现内存后端只读观察协议；如果没有这段代码，Phase 27 无法验证 observe/action 分离。
        if action == "list_windows":  # 新增代码+Phase27ComputerUse: 处理列出窗口动作；如果没有这行代码，模型无法发现可控制目标。
            return ComputerUseActionResult(True, "测试后端已返回已知窗口列表。", {"action": action, "backend": "memory", "windows": [dict(window) for window in self.windows]})  # 新增代码+Phase27ComputerUse: 返回窗口列表副本；如果没有这行代码，调用方无法拿到可信窗口引用。
        if action == "list_apps":  # 新增代码+Phase27ComputerUse: 处理列出应用动作；如果没有这行代码，模型无法先按应用粗略选择目标。
            app_ids = sorted({window["app_id"] for window in self.windows})  # 新增代码+Phase27ComputerUse: 从窗口目录提取应用身份；如果没有这行代码，应用列表无法生成。
            apps = [{"app_id": app_id, "window_count": sum(1 for window in self.windows if window["app_id"] == app_id)} for app_id in app_ids]  # 新增代码+Phase27ComputerUse: 生成应用和窗口数量摘要；如果没有这行代码，模型不知道每个应用有几个窗口。
            return ComputerUseActionResult(True, "测试后端已返回应用列表。", {"action": action, "backend": "memory", "apps": apps})  # 新增代码+Phase27ComputerUse: 返回应用观察结果；如果没有这行代码，list_apps 没有输出。
        if action == "get_active_window":  # 新增代码+Phase27ComputerUse: 处理活动窗口查询；如果没有这行代码，模型无法知道当前默认焦点目标。
            active_window = dict(self.windows[0]) if self.windows else None  # 新增代码+Phase27ComputerUse: 在测试后端用第一个窗口模拟活动窗口；如果没有这行代码，活动窗口观察没有确定行为。
            return ComputerUseActionResult(active_window is not None, "测试后端已返回活动窗口。" if active_window else "测试后端没有已知活动窗口。", {"action": action, "backend": "memory", "window": active_window})  # 新增代码+Phase27ComputerUse: 返回活动窗口或空结果；如果没有这行代码，调用方无法判断是否有焦点窗口。
        if action == "get_window_state":  # 新增代码+Phase27ComputerUse: 处理指定窗口状态查询；如果没有这行代码，动作前无法验证目标窗口仍存在。
            known_window = self._find_window(arguments.get("window"))  # 新增代码+Phase27ComputerUse: 查找传入窗口是否在可信目录；如果没有这行代码，未知窗口会被当作可观察。
            if known_window is None:  # 新增代码+Phase27ComputerUse: 判断窗口是否未知；如果没有这行代码，未知窗口不会被拒绝。
                return ComputerUseActionResult(False, "未知窗口：请先调用 computer_observe/list_windows 获取可信 window 引用。", {"action": action, "backend": "memory"})  # 新增代码+Phase27ComputerUse: 返回未知窗口错误；如果没有这行代码，模型不知道需要先观察窗口。
            known_ref = build_window_ref(known_window)  # 新增代码+Phase27ComputerUse: 把已知窗口转换成引用对象；如果没有这行代码，状态覆盖无法生成身份键。
            state = dict(self.window_states.get(window_ref_identity(known_ref), {})) if known_ref is not None else {}  # 新增代码+Phase27ComputerUse: 读取测试注入的窗口状态；如果没有这行代码，状态观察无法携带模拟证据。
            state.setdefault("window", known_window)  # 新增代码+Phase27ComputerUse: 确保状态里包含窗口引用；如果没有这行代码，调用方拿不到当前状态对应的窗口。
            state.setdefault("screenshot_id", "")  # 新增代码+Phase27ComputerUse: 提供截图证据占位；如果没有这行代码，后续真实截图字段没有稳定位置。
            state.setdefault("accessibility_excerpt", "")  # 新增代码+Phase27ComputerUse: 提供可访问性摘要占位；如果没有这行代码，后续 UIA 文本没有稳定位置。
            return ComputerUseActionResult(True, "测试后端已返回窗口状态。", {"action": action, "backend": "memory", "state": state})  # 新增代码+Phase27ComputerUse: 返回窗口状态结果；如果没有这行代码，get_window_state 没有成功输出。
        return ComputerUseActionResult(False, f"测试后端暂不支持观察动作：{action}", {"action": action, "backend": "memory"})  # 新增代码+Phase27ComputerUse: 拒绝未知观察动作；如果没有这行代码，observe 错误会静默失败。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+OSComputerUse: 记录已确认动作；若没有这段代码，成功路径没有可验证行为。
        payload = dict(arguments)  # 新增代码+OSComputerUse: 复制参数避免调用方后续修改记录；若没有这行代码，审计记录可能被外部可变对象污染。
        payload["action"] = action  # 新增代码+OSComputerUse: 把动作名写入记录；若没有这行代码，记录中可能缺少最关键动作类型。
        self.actions.append(payload)  # 新增代码+OSComputerUse: 保存动作记录；若没有这行代码，测试和审计无法追踪执行历史。
        data = {"action": action, "backend": "memory", "count": len(self.actions)}  # 修改代码+Phase20ComputerUse: 先准备可扩展的成功数据字典；如果没有这行代码，截图证据字段难以按动作类型追加。
        if action == "screenshot":  # 新增代码+Phase20ComputerUse: 只为截图动作补充证据摘要；如果没有这行代码，验收无法证明这次动作属于屏幕观察。
            data["evidence"] = {"kind": "screenshot", "backend": "memory", "captured": False, "reason": "内存后端只记录截图请求，不读取真实屏幕。"}  # 新增代码+Phase20ComputerUse: 明确测试截图没有触碰真实桌面；如果没有这行代码，用户可能把内存证据误认为真实截图文件。
        return ComputerUseActionResult(True, f"测试后端已记录动作：{action}", data)  # 修改代码+Phase20ComputerUse: 返回包含可选证据字段的成功结果；如果没有这行代码，调用方不知道后端是否收到动作。


class WindowsComputerUseBackend:  # 新增代码+Phase8ProductionEdges: 提供显式启用后的 Windows OS 控制后端；如果没有这段代码，Computer Use 只能停留在占位状态。
    def status(self) -> dict[str, Any]:  # 新增代码+Phase8ProductionEdges: 返回 Windows 后端状态；如果没有这段代码，用户无法确认真实后端是否启用。
        return {"available": sys.platform == "win32", "backend": "windows_ctypes", "reason": f"通过 {COMPUTER_USE_OPT_IN_ENV_VAR} 显式启用。", "real_actions_enabled": sys.platform == "win32", "opt_in_env_var": COMPUTER_USE_OPT_IN_ENV_VAR, "opt_in_enabled": True, "platform": sys.platform, "evidence_mode": "windows_metrics"}  # 修改代码+Phase20ComputerUse: 报告真实动作确实由显式环境变量开启；如果没有这行代码，状态页无法审计桌面控制来源。

    def observe(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase27ComputerUse: 提供 Windows 后端只读观察占位；如果没有这段代码，控制器无法统一调用 observe 协议。
        return ComputerUseActionResult(False, "Windows 真实窗口枚举将在 Phase 28 接入，本阶段只定义 typed observe 协议。", {"action": action, "backend": "windows_ctypes", "platform": sys.platform, "windows": []})  # 新增代码+Phase27ComputerUse: 明确当前真实窗口观察尚未实现；如果没有这行代码，用户可能误以为 Phase 27 已能枚举真实窗口。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase8ProductionEdges: 执行已通过控制器确认的 Windows 动作；如果没有这段代码，真实后端无法接收动作。
        if sys.platform != "win32":  # 新增代码+Phase8ProductionEdges: 非 Windows 平台直接拒绝；如果没有这行代码，调用 Win32 API 会崩溃。
            return ComputerUseActionResult(False, "Windows Computer Use 后端只能在 Windows 上执行。", {"backend": "windows_ctypes", "platform": sys.platform})  # 新增代码+Phase8ProductionEdges: 返回清楚的平台拒绝信息；如果没有这行代码，用户只能看到底层异常。
        import ctypes  # 新增代码+Phase8ProductionEdges: 延迟导入 ctypes；如果没有这行代码，后端无法调用 user32。
        user32 = ctypes.windll.user32  # 新增代码+Phase8ProductionEdges: 获取 Windows user32 API；如果没有这行代码，鼠标动作没有系统入口。
        if action == "move_mouse":  # 新增代码+Phase8ProductionEdges: 处理移动鼠标动作；如果没有这行代码，OS 控制缺少基础定位能力。
            x = int(arguments.get("x", 0))  # 新增代码+Phase8ProductionEdges: 读取 x 坐标；如果没有这行代码，鼠标移动没有横向目标。
            y = int(arguments.get("y", 0))  # 新增代码+Phase8ProductionEdges: 读取 y 坐标；如果没有这行代码，鼠标移动没有纵向目标。
            user32.SetCursorPos(x, y)  # 新增代码+Phase8ProductionEdges: 移动真实鼠标；如果没有这行代码，动作不会发生。
            return ComputerUseActionResult(True, "Windows 鼠标已移动。", {"backend": "windows_ctypes", "action": action, "x": x, "y": y})  # 新增代码+Phase8ProductionEdges: 返回移动结果；如果没有这行代码，调用方无法审计坐标。
        if action == "click":  # 新增代码+Phase8ProductionEdges: 处理左键点击动作；如果没有这行代码，OS 控制缺少点击能力。
            x = int(arguments.get("x", 0))  # 新增代码+Phase8ProductionEdges: 读取点击 x 坐标；如果没有这行代码，点击位置不明确。
            y = int(arguments.get("y", 0))  # 新增代码+Phase8ProductionEdges: 读取点击 y 坐标；如果没有这行代码，点击位置不明确。
            user32.SetCursorPos(x, y)  # 新增代码+Phase8ProductionEdges: 点击前移动到目标位置；如果没有这行代码，点击会落在旧光标处。
            user32.mouse_event(2, 0, 0, 0, 0)  # 新增代码+Phase8ProductionEdges: 按下鼠标左键；如果没有这行代码，点击不会开始。
            user32.mouse_event(4, 0, 0, 0, 0)  # 新增代码+Phase8ProductionEdges: 松开鼠标左键；如果没有这行代码，点击不会完成。
            return ComputerUseActionResult(True, "Windows 鼠标已点击。", {"backend": "windows_ctypes", "action": action, "x": x, "y": y})  # 新增代码+Phase8ProductionEdges: 返回点击结果；如果没有这行代码，调用方无法审计点击位置。
        if action == "screenshot":  # 新增代码+Phase8ProductionEdges: 处理屏幕观察动作；如果没有这行代码，OS 后端没有基础显示器信息入口。
            width = int(user32.GetSystemMetrics(0))  # 新增代码+Phase8ProductionEdges: 读取主屏幕宽度；如果没有这行代码，截图状态缺少尺寸证据。
            height = int(user32.GetSystemMetrics(1))  # 新增代码+Phase8ProductionEdges: 读取主屏幕高度；如果没有这行代码，截图状态缺少尺寸证据。
            return ComputerUseActionResult(True, "Windows 屏幕尺寸已读取；完整截图文件保存将在后续阶段接入。", {"backend": "windows_ctypes", "action": action, "width": width, "height": height, "evidence": {"kind": "screenshot", "backend": "windows_ctypes", "captured": False, "width": width, "height": height, "reason": "Phase 20 只记录屏幕尺寸证据，尚不保存完整截图文件。"}})  # 修改代码+Phase20ComputerUse: 返回可审计屏幕尺寸和截图证据边界；如果没有这行代码，观察动作没有可追踪证据。
        return ComputerUseActionResult(False, f"Windows 后端暂未实现动作：{action}", {"backend": "windows_ctypes", "action": action})  # 新增代码+Phase8ProductionEdges: 明确拒绝未实现动作；如果没有这行代码，未覆盖动作可能静默失败。


def build_default_computer_use_backend(environ: dict[str, str] | None = None) -> ComputerUseBackend:  # 新增代码+Phase8ProductionEdges: 集中决定默认 Computer Use 后端；如果没有这段代码，启用真实桌面控制的策略会散落在各处。
    source = os.environ if environ is None else environ  # 新增代码+Phase8ProductionEdges: 支持测试传入假环境；如果没有这行代码，测试会污染真实环境变量。
    enabled = str(source.get(COMPUTER_USE_OPT_IN_ENV_VAR, "")).lower() in {"1", "true", "yes"}  # 修改代码+Phase20ComputerUse: 使用统一常量读取真实桌面控制开关；如果没有这行代码，状态提示和实际开关可能不一致。
    if enabled and sys.platform == "win32":  # 新增代码+Phase8ProductionEdges: 同时满足启用和 Windows 才返回真实后端；如果没有这行代码，非 Windows 会误入 Windows API。
        return WindowsComputerUseBackend()  # 新增代码+Phase8ProductionEdges: 返回真实 Windows 后端；如果没有这行代码，显式启用也不会生效。
    return UnavailableComputerUseBackend()  # 新增代码+Phase8ProductionEdges: 默认安全关闭；如果没有这行代码，未配置时没有安全兜底。


class ComputerUseController:  # 新增代码+OSComputerUse: 在 agent 和后端之间提供安全控制层；若没有这段代码，真实桌面操作缺少统一确认和参数校验。
    ALLOWED_ACTIONS: set[str] = {"screenshot", "move_mouse", "click", "double_click", "type_text", "press_key", "scroll"}  # 新增代码+OSComputerUse: 限定允许的桌面动作集合；若没有这行代码，模型可能传入任意未知动作。
    OBSERVE_ACTIONS: set[str] = {"list_apps", "list_windows", "get_active_window", "get_window_state"}  # 新增代码+Phase27ComputerUse: 限定只读观察动作集合；如果没有这行代码，observe 可能被滥用成任意桌面命令。
    MAX_TEXT_LENGTH: int = 2000  # 新增代码+OSComputerUse: 限制一次输入文本长度；若没有这行代码，模型可能一次性向桌面注入过长文本。

    def __init__(self, backend: ComputerUseBackend | None = None) -> None:  # 新增代码+OSComputerUse: 初始化控制器并允许注入后端；若没有这段代码，测试和生产无法替换实现。
        self.backend = backend or build_default_computer_use_backend()  # 修改代码+Phase8ProductionEdges: 通过工厂选择默认安全关闭或显式启用的 Windows 后端；如果没有这行代码，真实后端无法受环境变量控制。
        self.audit_log: list[dict[str, Any]] = []  # 新增代码+Phase20ComputerUse: 保存本控制器生命周期里的桌面动作审计事件；如果没有这行代码，被拒绝或执行过的动作无法在状态里复盘。

    def status(self) -> dict[str, Any]:  # 新增代码+OSComputerUse: 返回 Computer Use 当前状态；若没有这段代码，computer_status 工具没有实现来源。
        backend_status = self.backend.status()  # 新增代码+OSComputerUse: 向后端读取状态；若没有这行代码，状态输出无法反映真实后端。
        audit_status = {"event_count": len(self.audit_log), "last_event": dict(self.audit_log[-1]) if self.audit_log else None}  # 新增代码+Phase20ComputerUse: 汇总最近审计事件但不暴露完整长日志；如果没有这行代码，终端状态无法显示最近一次安全判断。
        return {"tool": "computer_use", "actions": sorted(self.ALLOWED_ACTIONS), "observe_actions": sorted(self.OBSERVE_ACTIONS), "backend": backend_status, "audit": audit_status}  # 修改代码+Phase27ComputerUse: 返回写动作、只读观察动作、后端和审计摘要；如果没有这行代码，模型无法区分 observe 和 action。

    def _record_audit(self, action: str, allowed: bool, reason: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase20ComputerUse: 记录一次桌面动作安全判断；如果没有这段函数，拒绝和执行结果无法获得统一审计 id。
        backend_status = self.backend.status()  # 新增代码+Phase20ComputerUse: 读取后端名称写入审计事件；如果没有这行代码，事后不知道动作由哪个后端处理。
        event = {"audit_id": f"computer-audit-{len(self.audit_log) + 1}", "action": action, "allowed": allowed, "reason": reason, "backend": backend_status.get("backend"), "has_coordinates": "x" in arguments or "y" in arguments, "text_length": len(str(arguments.get("text", ""))) if "text" in arguments else 0}  # 新增代码+Phase20ComputerUse: 只记录必要元数据并避免保存原始输入文本；如果没有这行代码，审计日志要么不可追踪要么可能泄露敏感内容。
        self.audit_log.append(event)  # 新增代码+Phase20ComputerUse: 把事件加入审计日志；如果没有这行代码，status 里看不到最近发生的安全判断。
        return event  # 新增代码+Phase20ComputerUse: 返回事件方便结果携带同一个审计 id；如果没有这行代码，工具返回无法和审计日志关联。

    def _with_audit(self, result: ComputerUseActionResult, event: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase20ComputerUse: 把审计 id 附加到动作结果里；如果没有这段函数，调用方需要自己拼接审计字段且容易遗漏。
        data = dict(result.data)  # 新增代码+Phase20ComputerUse: 复制结果数据避免直接修改冻结结果里的原始字典；如果没有这行代码，审计字段可能污染后端返回对象。
        data["audit_id"] = event["audit_id"]  # 新增代码+Phase20ComputerUse: 在结果中写入审计 id；如果没有这行代码，用户无法把这次结果对应到状态审计事件。
        return ComputerUseActionResult(result.ok, result.message, data)  # 新增代码+Phase20ComputerUse: 返回带审计 id 的新结果；如果没有这行代码，ComputerUseActionResult 的不可变约束会被破坏。

    def observe(self, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase27ComputerUse: 执行一次只读桌面观察；如果没有这段代码，computer_observe 工具没有统一安全入口。
        action = str(arguments.get("action", "")).strip()  # 新增代码+Phase27ComputerUse: 读取并清理观察动作名；如果没有这行代码，空白动作名会进入后端。
        audit_action = f"observe:{action}"  # 新增代码+Phase27ComputerUse: 给审计动作名加 observe 前缀；如果没有这行代码，观察审计和写动作审计会混在一起。
        if action not in self.OBSERVE_ACTIONS:  # 新增代码+Phase27ComputerUse: 拒绝未知观察动作；如果没有这行代码，模型可能通过 observe 传入未设计命令。
            result = ComputerUseActionResult(False, f"不支持的 Computer Use 观察动作：{action}", {"allowed_observe_actions": sorted(self.OBSERVE_ACTIONS)})  # 新增代码+Phase27ComputerUse: 构造未知观察动作拒绝结果；如果没有这行代码，错误缺少可操作提示。
            event = self._record_audit(audit_action, False, result.message, arguments)  # 新增代码+Phase27ComputerUse: 记录 observe 拒绝审计；如果没有这行代码，只读工具异常不会进入状态摘要。
            return self._with_audit(result, event)  # 新增代码+Phase27ComputerUse: 返回带审计 id 的 observe 拒绝结果；如果没有这行代码，工具输出无法关联审计。
        result = self.backend.observe(action, dict(arguments))  # 新增代码+Phase27ComputerUse: 把合法只读观察交给后端；如果没有这行代码，observe 永远不会读取窗口目录。
        event = self._record_audit(audit_action, result.ok, result.message, arguments)  # 新增代码+Phase27ComputerUse: 记录 observe 成功或失败审计；如果没有这行代码，窗口观察缺少复盘轨迹。
        return self._with_audit(result, event)  # 新增代码+Phase27ComputerUse: 返回带审计 id 的 observe 结果；如果没有这行代码，状态和结果无法互相定位。

    def _reject_unknown_window_target(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult | None:  # 新增代码+Phase27ComputerUse: 在写动作前拦截未知窗口目标；如果没有这段函数，模型可能把鼠标键盘动作发给伪造窗口。
        raw_window = arguments.get("window")  # 新增代码+Phase27ComputerUse: 读取可选窗口目标；如果没有这行代码，控制器无法知道动作是否声明了目标窗口。
        if raw_window is None:  # 新增代码+Phase27ComputerUse: 兼容旧动作调用没有 window 的情况；如果没有这行代码，Phase 20 旧测试会被误拒绝。
            return None  # 新增代码+Phase27ComputerUse: 没有窗口目标时不做未知窗口校验；如果没有这行代码，旧坐标动作无法继续兼容。
        window_ref = build_window_ref(raw_window)  # 新增代码+Phase27ComputerUse: 将传入窗口目标转换成强类型引用；如果没有这行代码，缺 app_id/window_id 的目标可能绕过校验。
        if window_ref is None:  # 新增代码+Phase27ComputerUse: 判断窗口引用是否完整；如果没有这行代码，半截窗口目标会进入后端。
            result = ComputerUseActionResult(False, "未知窗口目标：window 必须包含 app_id 和 window_id。", {"action": action})  # 新增代码+Phase27ComputerUse: 返回窗口字段缺失错误；如果没有这行代码，模型不知道如何修正参数。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase27ComputerUse: 记录窗口字段缺失拒绝；如果没有这行代码，拒绝原因不会进入审计日志。
            return self._with_audit(result, event)  # 新增代码+Phase27ComputerUse: 返回带审计 id 的拒绝结果；如果没有这行代码，调用方无法关联这次拦截。
        probe = self.backend.observe("get_window_state", {"window": window_ref.to_dict(), "validation_only": True})  # 新增代码+Phase27ComputerUse: 用只读状态查询验证窗口仍在可信目录；如果没有这行代码，未知窗口不能在动作前被发现。
        if probe.ok:  # 新增代码+Phase27ComputerUse: 后端确认窗口存在时放行动作；如果没有这行代码，已知窗口也会被误拒绝。
            return None  # 新增代码+Phase27ComputerUse: 返回 None 表示没有拦截；如果没有这行代码，execute 无法继续到后端。
        result = ComputerUseActionResult(False, "未知窗口目标，已拒绝执行桌面动作；请先调用 computer_observe/list_windows 获取可信 window。", {"action": action, "window": window_ref.to_dict(), "observe_message": probe.message})  # 新增代码+Phase27ComputerUse: 返回未知窗口拒绝结果；如果没有这行代码，模型可能继续尝试错误窗口。
        event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase27ComputerUse: 记录未知窗口拒绝审计；如果没有这行代码，安全拦截无法复盘。
        return self._with_audit(result, event)  # 新增代码+Phase27ComputerUse: 返回带审计 id 的未知窗口拒绝；如果没有这行代码，结果和审计无法关联。

    def execute(self, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+OSComputerUse: 执行一次经过安全检查的桌面动作；若没有这段代码，computer_action 工具没有统一入口。
        action = str(arguments.get("action", "")).strip()  # 新增代码+OSComputerUse: 读取并清理动作名；若没有这行代码，空白动作名会进入后端。
        if action not in self.ALLOWED_ACTIONS:  # 新增代码+OSComputerUse: 拒绝未知动作；若没有这行代码，后端可能收到未设计过的危险指令。
            result = ComputerUseActionResult(False, f"不支持的 Computer Use 动作：{action}", {"allowed_actions": sorted(self.ALLOWED_ACTIONS)})  # 修改代码+Phase20ComputerUse: 先构造拒绝结果再附加审计 id；如果没有这行代码，未知动作拒绝无法被追踪。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase20ComputerUse: 记录未知动作拒绝事件；如果没有这行代码，高风险异常调用不会进入审计日志。
            return self._with_audit(result, event)  # 修改代码+Phase20ComputerUse: 返回带审计 id 的拒绝结果；如果没有这行代码，工具输出和审计日志无法关联。
        if arguments.get("confirm_desktop_control") is not True:  # 新增代码+OSComputerUse: 要求模型显式承认这是桌面控制；若没有这行代码，高风险动作可能被无意触发。
            result = ComputerUseActionResult(False, "缺少 confirm_desktop_control=true，已拒绝执行真实桌面动作。", {"action": action})  # 修改代码+Phase20ComputerUse: 先构造缺少确认的拒绝结果；如果没有这行代码，确认门禁失败没有稳定结果对象。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase20ComputerUse: 记录缺少确认的拒绝事件；如果没有这行代码，安全门禁触发后无法复盘原因。
            return self._with_audit(result, event)  # 修改代码+Phase20ComputerUse: 返回带审计 id 的门禁拒绝结果；如果没有这行代码，用户无法定位这次拒绝事件。
        text = str(arguments.get("text", ""))  # 新增代码+OSComputerUse: 读取可选输入文本；若没有这行代码，type_text 长度无法被检查。
        if action == "type_text" and len(text) > self.MAX_TEXT_LENGTH:  # 新增代码+OSComputerUse: 限制输入文本长度；若没有这行代码，过长文本可能污染桌面输入目标。
            result = ComputerUseActionResult(False, f"type_text 文本过长，最多 {self.MAX_TEXT_LENGTH} 字符。", {"action": action, "text_length": len(text)})  # 修改代码+Phase20ComputerUse: 先构造长度拒绝结果；如果没有这行代码，过长文本拒绝无法携带审计 id。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase20ComputerUse: 记录文本过长拒绝事件；如果没有这行代码，输入保护触发后无法审计。
            return self._with_audit(result, event)  # 修改代码+Phase20ComputerUse: 返回带审计 id 的长度拒绝结果；如果没有这行代码，调用方无法关联保护事件。
        window_rejection = self._reject_unknown_window_target(action, arguments)  # 新增代码+Phase27ComputerUse: 在执行写动作前检查窗口目标是否可信；如果没有这行代码，未知窗口可能被传给真实后端。
        if window_rejection is not None:  # 新增代码+Phase27ComputerUse: 判断窗口校验是否产生拒绝结果；如果没有这行代码，拒绝结果会被忽略。
            return window_rejection  # 新增代码+Phase27ComputerUse: 返回未知窗口拒绝而不调用后端；如果没有这行代码，后端仍可能执行危险动作。
        result = self.backend.execute(action, dict(arguments))  # 修改代码+Phase20ComputerUse: 把通过校验的动作交给后端并保留结果；若没有这行代码，Computer Use 永远不会执行到后端。
        event = self._record_audit(action, result.ok, result.message, arguments)  # 新增代码+Phase20ComputerUse: 记录后端执行结果是否成功；如果没有这行代码，已允许动作也没有审计闭环。
        return self._with_audit(result, event)  # 修改代码+Phase20ComputerUse: 返回带审计 id 的最终结果；如果没有这行代码，成功动作和审计日志无法关联。
