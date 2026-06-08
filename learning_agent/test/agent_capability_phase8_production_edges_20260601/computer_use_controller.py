"""OS 级 Computer Use 控制器。"""  # 新增代码+OSComputerUse: 集中管理桌面控制的安全边界；若没有这个文件，桌面动作会散落在 agent 方法里难以审计。

from __future__ import annotations  # 新增代码+OSComputerUse: 延迟解析类型注解；若没有这行代码，Protocol 等注解在旧执行路径中更容易产生导入顺序问题。

import os  # 新增代码+Phase8ProductionEdges: 读取显式启用真实 Windows 后端的环境变量；如果没有这行代码，Computer Use 后端无法做到默认安全关闭。
import sys  # 新增代码+Phase8ProductionEdges: 判断当前平台是否为 Windows；如果没有这行代码，非 Windows 环境可能误报支持真实桌面控制。
from dataclasses import dataclass  # 新增代码+OSComputerUse: 使用 dataclass 表达动作结果；若没有这行代码，结果对象需要手写大量样板代码。
from typing import Any, Protocol  # 新增代码+OSComputerUse: 引入通用 JSON 参数和后端协议类型；若没有这行代码，控制器边界不清楚。


@dataclass(frozen=True)  # 新增代码+OSComputerUse: 让动作结果不可变，避免调用方事后改写审计事实；若没有这行代码，结果对象可能被无意污染。
class ComputerUseActionResult:  # 新增代码+OSComputerUse: 定义 Computer Use 动作统一返回结构；若没有这段代码，状态、错误和数据会以散乱字符串传递。
    ok: bool  # 新增代码+OSComputerUse: 表示动作是否成功；若没有这行代码，调用方无法稳定判断成功失败。
    message: str  # 新增代码+OSComputerUse: 保存给模型和用户看的中文说明；若没有这行代码，失败原因会丢失。
    data: dict[str, Any]  # 新增代码+OSComputerUse: 保存结构化附加数据；若没有这行代码，截图摘要、坐标或后端状态无法机器读取。

    def to_text(self) -> str:  # 新增代码+OSComputerUse: 把结构化结果转成工具返回文本；若没有这段代码，agent 方法会重复拼接结果字符串。
        status = "成功" if self.ok else "失败"  # 新增代码+OSComputerUse: 把布尔状态转换成用户容易理解的中文词；若没有这行代码，输出不够直观。
        return f"computer_action {status}：{self.message}\n数据：{self.data}"  # 新增代码+OSComputerUse: 返回包含状态和数据的可读文本；若没有这行代码，模型看不到结构化结果。


class ComputerUseBackend(Protocol):  # 新增代码+OSComputerUse: 定义真实/测试桌面后端必须实现的接口；若没有这段代码，后续接 Windows 后端没有稳定契约。
    def status(self) -> dict[str, Any]:  # 新增代码+OSComputerUse: 要求后端报告可用状态；若没有这行代码，状态工具无法知道后端是否能控制桌面。
        ...  # 新增代码+OSComputerUse: Protocol 方法占位；若没有这行代码，接口声明语法不完整。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+OSComputerUse: 要求后端执行已通过安全检查的动作；若没有这行代码，控制器无法调用真实实现。
        ...  # 新增代码+OSComputerUse: Protocol 方法占位；若没有这行代码，接口声明语法不完整。


class UnavailableComputerUseBackend:  # 新增代码+OSComputerUse: 默认不可用后端，保证未配置时绝不控制真实桌面；若没有这段代码，项目初始化时可能找不到安全默认值。
    def status(self) -> dict[str, Any]:  # 新增代码+OSComputerUse: 返回默认后端状态；若没有这段代码，computer_status 无法说明为什么不可用。
        return {"available": False, "backend": "unavailable", "reason": "尚未配置真实 OS Computer Use 后端。"}  # 新增代码+OSComputerUse: 明确告诉用户后端未配置；若没有这行代码，用户只会看到模糊失败。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+OSComputerUse: 拒绝所有真实桌面动作；若没有这段代码，默认后端可能意外执行副作用。
        return ComputerUseActionResult(False, "OS Computer Use 后端尚未启用，未执行任何真实桌面操作。", {"action": action, "backend": "unavailable"})  # 新增代码+OSComputerUse: 返回清楚拒绝结果；若没有这行代码，模型可能误以为动作已执行。


class MemoryComputerUseBackend:  # 新增代码+OSComputerUse: 测试专用后端，只记录动作不碰真实桌面；若没有这段代码，自动化测试无法验证成功路径。
    def __init__(self) -> None:  # 新增代码+OSComputerUse: 初始化内存动作列表；若没有这段代码，测试无法查看后端收到哪些动作。
        self.actions: list[dict[str, Any]] = []  # 新增代码+OSComputerUse: 保存每次动作参数副本；若没有这行代码，测试无法证明动作被传递到后端。

    def status(self) -> dict[str, Any]:  # 新增代码+OSComputerUse: 返回测试后端状态；若没有这段代码，controller.status 无法在测试中表现为可用。
        return {"available": True, "backend": "memory", "reason": "测试后端只记录动作，不控制真实桌面。"}  # 新增代码+OSComputerUse: 明确说明测试后端无副作用；若没有这行代码，用户可能误解为真实控制。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+OSComputerUse: 记录已确认动作；若没有这段代码，成功路径没有可验证行为。
        payload = dict(arguments)  # 新增代码+OSComputerUse: 复制参数避免调用方后续修改记录；若没有这行代码，审计记录可能被外部可变对象污染。
        payload["action"] = action  # 新增代码+OSComputerUse: 把动作名写入记录；若没有这行代码，记录中可能缺少最关键动作类型。
        self.actions.append(payload)  # 新增代码+OSComputerUse: 保存动作记录；若没有这行代码，测试和审计无法追踪执行历史。
        return ComputerUseActionResult(True, f"测试后端已记录动作：{action}", {"action": action, "backend": "memory", "count": len(self.actions)})  # 新增代码+OSComputerUse: 返回确定性成功结果；若没有这行代码，调用方不知道后端是否收到动作。


class WindowsComputerUseBackend:  # 新增代码+Phase8ProductionEdges: 提供显式启用后的 Windows OS 控制后端；如果没有这段代码，Computer Use 只能停留在占位状态。
    def status(self) -> dict[str, Any]:  # 新增代码+Phase8ProductionEdges: 返回 Windows 后端状态；如果没有这段代码，用户无法确认真实后端是否启用。
        return {"available": sys.platform == "win32", "backend": "windows_ctypes", "reason": "通过 LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE 显式启用。"}  # 新增代码+Phase8ProductionEdges: 报告后端名称和启用来源；如果没有这行代码，状态页无法审计桌面控制来源。

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
            return ComputerUseActionResult(True, "Windows 屏幕尺寸已读取；完整截图文件保存将在后续阶段接入。", {"backend": "windows_ctypes", "action": action, "width": width, "height": height})  # 新增代码+Phase8ProductionEdges: 返回可审计屏幕尺寸；如果没有这行代码，观察动作没有输出。
        return ComputerUseActionResult(False, f"Windows 后端暂未实现动作：{action}", {"backend": "windows_ctypes", "action": action})  # 新增代码+Phase8ProductionEdges: 明确拒绝未实现动作；如果没有这行代码，未覆盖动作可能静默失败。


def build_default_computer_use_backend(environ: dict[str, str] | None = None) -> ComputerUseBackend:  # 新增代码+Phase8ProductionEdges: 集中决定默认 Computer Use 后端；如果没有这段代码，启用真实桌面控制的策略会散落在各处。
    source = os.environ if environ is None else environ  # 新增代码+Phase8ProductionEdges: 支持测试传入假环境；如果没有这行代码，测试会污染真实环境变量。
    enabled = str(source.get("LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE", "")).lower() in {"1", "true", "yes"}  # 新增代码+Phase8ProductionEdges: 只有显式设置才启用真实后端；如果没有这行代码，桌面控制可能默认打开。
    if enabled and sys.platform == "win32":  # 新增代码+Phase8ProductionEdges: 同时满足启用和 Windows 才返回真实后端；如果没有这行代码，非 Windows 会误入 Windows API。
        return WindowsComputerUseBackend()  # 新增代码+Phase8ProductionEdges: 返回真实 Windows 后端；如果没有这行代码，显式启用也不会生效。
    return UnavailableComputerUseBackend()  # 新增代码+Phase8ProductionEdges: 默认安全关闭；如果没有这行代码，未配置时没有安全兜底。


class ComputerUseController:  # 新增代码+OSComputerUse: 在 agent 和后端之间提供安全控制层；若没有这段代码，真实桌面操作缺少统一确认和参数校验。
    ALLOWED_ACTIONS: set[str] = {"screenshot", "move_mouse", "click", "double_click", "type_text", "press_key", "scroll"}  # 新增代码+OSComputerUse: 限定允许的桌面动作集合；若没有这行代码，模型可能传入任意未知动作。
    MAX_TEXT_LENGTH: int = 2000  # 新增代码+OSComputerUse: 限制一次输入文本长度；若没有这行代码，模型可能一次性向桌面注入过长文本。

    def __init__(self, backend: ComputerUseBackend | None = None) -> None:  # 新增代码+OSComputerUse: 初始化控制器并允许注入后端；若没有这段代码，测试和生产无法替换实现。
        self.backend = backend or build_default_computer_use_backend()  # 修改代码+Phase8ProductionEdges: 通过工厂选择默认安全关闭或显式启用的 Windows 后端；如果没有这行代码，真实后端无法受环境变量控制。

    def status(self) -> dict[str, Any]:  # 新增代码+OSComputerUse: 返回 Computer Use 当前状态；若没有这段代码，computer_status 工具没有实现来源。
        backend_status = self.backend.status()  # 新增代码+OSComputerUse: 向后端读取状态；若没有这行代码，状态输出无法反映真实后端。
        return {"tool": "computer_use", "actions": sorted(self.ALLOWED_ACTIONS), "backend": backend_status}  # 新增代码+OSComputerUse: 返回工具名、可用动作和后端状态；若没有这行代码，模型缺少下一步判断依据。

    def execute(self, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+OSComputerUse: 执行一次经过安全检查的桌面动作；若没有这段代码，computer_action 工具没有统一入口。
        action = str(arguments.get("action", "")).strip()  # 新增代码+OSComputerUse: 读取并清理动作名；若没有这行代码，空白动作名会进入后端。
        if action not in self.ALLOWED_ACTIONS:  # 新增代码+OSComputerUse: 拒绝未知动作；若没有这行代码，后端可能收到未设计过的危险指令。
            return ComputerUseActionResult(False, f"不支持的 Computer Use 动作：{action}", {"allowed_actions": sorted(self.ALLOWED_ACTIONS)})  # 新增代码+OSComputerUse: 告诉模型允许哪些动作；若没有这行代码，模型难以修正调用。
        if arguments.get("confirm_desktop_control") is not True:  # 新增代码+OSComputerUse: 要求模型显式承认这是桌面控制；若没有这行代码，高风险动作可能被无意触发。
            return ComputerUseActionResult(False, "缺少 confirm_desktop_control=true，已拒绝执行真实桌面动作。", {"action": action})  # 新增代码+OSComputerUse: 返回明确拒绝原因；若没有这行代码，模型不知道需要显式确认。
        text = str(arguments.get("text", ""))  # 新增代码+OSComputerUse: 读取可选输入文本；若没有这行代码，type_text 长度无法被检查。
        if action == "type_text" and len(text) > self.MAX_TEXT_LENGTH:  # 新增代码+OSComputerUse: 限制输入文本长度；若没有这行代码，过长文本可能污染桌面输入目标。
            return ComputerUseActionResult(False, f"type_text 文本过长，最多 {self.MAX_TEXT_LENGTH} 字符。", {"action": action, "text_length": len(text)})  # 新增代码+OSComputerUse: 返回长度拒绝说明；若没有这行代码，模型不知道需要缩短输入。
        return self.backend.execute(action, dict(arguments))  # 新增代码+OSComputerUse: 把通过校验的动作交给后端；若没有这行代码，Computer Use 永远不会执行到后端。
