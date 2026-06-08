"""OS 级 Computer Use 控制器。"""  # 新增代码+OSComputerUse: 集中管理桌面控制的安全边界；若没有这个文件，桌面动作会散落在 agent 方法里难以审计。

from __future__ import annotations  # 新增代码+OSComputerUse: 延迟解析类型注解；若没有这行代码，Protocol 等注解在旧执行路径中更容易产生导入顺序问题。

import os  # 新增代码+Phase8ProductionEdges: 读取显式启用真实 Windows 后端的环境变量；如果没有这行代码，Computer Use 后端无法做到默认安全关闭。
import sys  # 新增代码+Phase8ProductionEdges: 判断当前平台是否为 Windows；如果没有这行代码，非 Windows 环境可能误报支持真实桌面控制。
from dataclasses import dataclass  # 新增代码+OSComputerUse: 使用 dataclass 表达动作结果；若没有这行代码，结果对象需要手写大量样板代码。
from typing import Any, Protocol  # 新增代码+OSComputerUse: 引入通用 JSON 参数和后端协议类型；若没有这行代码，控制器边界不清楚。

try:  # 新增代码+Phase27ComputerUse: 包运行模式下导入窗口协议模型；如果没有这行代码，控制器无法使用强类型窗口引用。
    from learning_agent.computer_use.action_policy import build_action_evidence, prepare_action_arguments, redact_action_arguments  # 新增代码+Phase30ComputerUseActionGate: 导入动作策略、坐标转换和脱敏 helper；如果没有这行代码，controller 会继续直接保存原始动作参数。
    from learning_agent.computer_use.audit import ComputerUseAuditStore  # 新增代码+Phase31ComputerUseLockAbortEvidence: 导入落盘审计仓库；如果没有这行代码，动作前后证据只能停留在内存结果里。
    from learning_agent.computer_use.evidence import ComputerUseEvidenceStore  # 新增代码+Phase29ComputerUse: 导入窗口状态证据仓库；如果没有这行代码，Windows 后端无法把截图和 UIA 摘要落盘。
    from learning_agent.computer_use.helper_client import NullWindowObservationHelper  # 新增代码+Phase29ComputerUse: 导入默认窗口观察 helper；如果没有这行代码，未配置截图 helper 时后端无法优雅降级。
    from learning_agent.computer_use.lock import ComputerUseLockManager  # 新增代码+Phase30ComputerUseActionGate: 导入 durable lock 管理器；如果没有这行代码，动作无法要求当前会话持有桌面锁。
    from learning_agent.computer_use.models import build_window_ref, window_ref_identity  # 新增代码+Phase27ComputerUse: 读取窗口构造和身份键 helper；如果没有这行代码，未知窗口校验只能继续依赖松散 dict。
    from learning_agent.computer_use.native_helper import WindowsNativeWindowObservationHelper  # 新增代码+Phase32WindowsNativeHelper: 导入 Windows native 只读观察 helper；如果没有这行代码，显式 opt-in 后仍无法启用截图/文本桥接。
    from learning_agent.computer_use.sendinput_executor import WindowsSendInputExecutor  # 新增代码+Phase37WindowsSendInputExecutor: 导入 SendInput 动作执行器合同；如果没有这行代码，Windows 后端会继续依赖旧 mouse_event 路径。
    from learning_agent.computer_use.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase28ComputerUse: 导入真实 Windows 只读窗口 inventory probe；如果没有这行代码，Windows 后端无法执行 list_windows/list_apps。
except ModuleNotFoundError as error:  # 新增代码+Phase27ComputerUse: 捕获直接脚本运行时包名不可用的情况；如果没有这行代码，start_oauth_agent.bat 的脚本模式可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.action_policy", "learning_agent.computer_use.audit", "learning_agent.computer_use.evidence", "learning_agent.computer_use.helper_client", "learning_agent.computer_use.lock", "learning_agent.computer_use.models", "learning_agent.computer_use.native_helper", "learning_agent.computer_use.sendinput_executor", "learning_agent.computer_use.windows_backend"}:  # 修改代码+Phase37WindowsSendInputExecutor: 允许 Phase37 SendInput 执行器在脚本模式下 fallback；如果没有这行代码，bat 入口会因为新模块路径缺失而中断。
        raise  # 新增代码+Phase27ComputerUse: 重新抛出真实导入错误；如果没有这行代码，排查协议模型问题会很困难。
    from computer_use.action_policy import build_action_evidence, prepare_action_arguments, redact_action_arguments  # 新增代码+Phase30ComputerUseActionGate: 脚本模式下导入动作策略 helper；如果没有这行代码，bat 入口无法加载 Phase 30 坐标转换和脱敏逻辑。
    from computer_use.audit import ComputerUseAuditStore  # 新增代码+Phase31ComputerUseLockAbortEvidence: 脚本模式下导入落盘审计仓库；如果没有这行代码，bat 入口无法保存动作证据链。
    from computer_use.evidence import ComputerUseEvidenceStore  # 新增代码+Phase29ComputerUse: 脚本模式下导入证据仓库；如果没有这行代码，bat 入口无法保存窗口状态证据。
    from computer_use.helper_client import NullWindowObservationHelper  # 新增代码+Phase29ComputerUse: 脚本模式下导入默认观察 helper；如果没有这行代码，bat 入口无法加载 Phase 29 后端。
    from computer_use.lock import ComputerUseLockManager  # 新增代码+Phase30ComputerUseActionGate: 脚本模式下导入 durable lock 管理器；如果没有这行代码，bat 入口无法执行持锁门禁。
    from computer_use.models import build_window_ref, window_ref_identity  # 新增代码+Phase27ComputerUse: 脚本模式下从本地 computer_use 包导入模型；如果没有这行代码，bat 入口无法加载 Phase 27 协议。
    from computer_use.native_helper import WindowsNativeWindowObservationHelper  # 新增代码+Phase32WindowsNativeHelper: 脚本模式下导入 native helper；如果没有这行代码，bat 入口无法启用 Phase32 只读桥接。
    from computer_use.sendinput_executor import WindowsSendInputExecutor  # 新增代码+Phase37WindowsSendInputExecutor: 脚本模式下导入 SendInput 执行器；如果没有这行代码，start_oauth_agent.bat 无法加载 Phase37 动作层。
    from computer_use.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase28ComputerUse: 脚本模式下导入 Windows inventory probe；如果没有这行代码，bat 入口无法加载 Phase 28 只读窗口枚举。


COMPUTER_USE_OPT_IN_ENV_VAR = "LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE"  # 新增代码+Phase20ComputerUse: 集中保存真实桌面控制的启用环境变量名；如果没有这行代码，状态输出和工厂逻辑可能写出不一致的开关名。
COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR = "LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE"  # 新增代码+Phase28ComputerUse: 集中保存只读窗口观察的启用环境变量名；如果没有这行代码，用户只能为了观察窗口而误开真实鼠标键盘动作。
COMPUTER_USE_NATIVE_OBSERVE_OPT_IN_ENV_VAR = "LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE"  # 新增代码+Phase32WindowsNativeHelper: 集中保存 native 截图/文本只读 helper 开关；如果没有这行代码，只读 inventory 可能被误扩大为读取屏幕内容。


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
        return {"available": False, "backend": "unavailable", "reason": f"未设置 {COMPUTER_USE_OPT_IN_ENV_VAR}=1 或 {COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR}=1，OS Computer Use 默认安全关闭。", "real_actions_enabled": False, "read_only_inventory_enabled": False, "opt_in_env_var": COMPUTER_USE_OPT_IN_ENV_VAR, "observe_opt_in_env_var": COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR, "opt_in_enabled": False, "platform": sys.platform}  # 修改代码+Phase28ComputerUse: 同时说明真实动作开关和只读观察开关；如果没有这行代码，用户不知道如何只启用安全窗口 inventory。

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
        return {"available": True, "backend": "memory", "reason": "测试后端只记录动作，不控制真实桌面。", "real_actions_enabled": False, "read_only_inventory_enabled": True, "opt_in_env_var": COMPUTER_USE_OPT_IN_ENV_VAR, "observe_opt_in_env_var": COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR, "opt_in_enabled": False, "platform": sys.platform, "evidence_mode": "memory_only", "window_count": len(self.windows)}  # 修改代码+Phase28ComputerUse: 在测试状态里报告只读 inventory 和已知窗口数量；如果没有这行代码，调试时看不出 observe 能力边界。

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
        payload = redact_action_arguments(action, arguments)  # 修改代码+Phase30ComputerUseActionGate: 保存脱敏后的动作参数副本；若没有这行代码，内存后端测试日志可能保存原始密码或 token。
        self.actions.append(payload)  # 修改代码+Phase30ComputerUseActionGate: 保存脱敏动作记录；若没有这行代码，测试和审计无法追踪执行历史且不能证明文本已被清理。
        data = {"action": action, "backend": "memory", "count": len(self.actions)}  # 修改代码+Phase20ComputerUse: 先准备可扩展的成功数据字典；如果没有这行代码，截图证据字段难以按动作类型追加。
        if action == "screenshot":  # 新增代码+Phase20ComputerUse: 只为截图动作补充证据摘要；如果没有这行代码，验收无法证明这次动作属于屏幕观察。
            data["evidence"] = {"kind": "screenshot", "backend": "memory", "captured": False, "reason": "内存后端只记录截图请求，不读取真实屏幕。"}  # 新增代码+Phase20ComputerUse: 明确测试截图没有触碰真实桌面；如果没有这行代码，用户可能把内存证据误认为真实截图文件。
        return ComputerUseActionResult(True, f"测试后端已记录动作：{action}", data)  # 修改代码+Phase20ComputerUse: 返回包含可选证据字段的成功结果；如果没有这行代码，调用方不知道后端是否收到动作。


class WindowsComputerUseBackend:  # 新增代码+Phase8ProductionEdges: 提供显式启用后的 Windows OS 控制后端；如果没有这段代码，Computer Use 只能停留在占位状态。
    def __init__(self, inventory: Any | None = None, real_actions_enabled: bool = True, evidence_store: Any | None = None, observation_helper: Any | None = None, action_executor: Any | None = None) -> None:  # 修改代码+Phase37WindowsSendInputExecutor: 初始化 Windows 后端并允许注入 SendInput 执行器；如果没有这段代码，后端无法用安全合同替代旧 mouse_event 路径。
        self.inventory = inventory or WindowsWindowInventoryProbe()  # 新增代码+Phase28ComputerUse: 保存真实或静态窗口 inventory；如果没有这行代码，observe 无法读取窗口快照。
        self.real_actions_enabled = real_actions_enabled  # 新增代码+Phase28ComputerUse: 保存真实动作是否启用；如果没有这行代码，只读模式无法阻止 click/move_mouse。
        self.evidence_store = evidence_store or ComputerUseEvidenceStore()  # 新增代码+Phase29ComputerUse: 保存窗口状态证据仓库；如果没有这行代码，截图和 metadata 没有落盘位置。
        self.observation_helper = observation_helper or NullWindowObservationHelper()  # 新增代码+Phase29ComputerUse: 保存截图/UIA helper；如果没有这行代码，未配置 helper 时 get_window_state 会崩溃。
        self.action_executor = action_executor or WindowsSendInputExecutor(enabled=real_actions_enabled)  # 新增代码+Phase37WindowsSendInputExecutor: 保存 SendInput 动作执行器且默认真实实现为空；如果没有这行代码，真实动作仍会走旧 Win32 mouse_event 分支。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase8ProductionEdges: 返回 Windows 后端状态；如果没有这段代码，用户无法确认真实后端是否启用。
        inventory_status = self.inventory.status() if hasattr(self.inventory, "status") else {}  # 新增代码+Phase28ComputerUse: 读取 inventory 状态；如果没有这行代码，状态无法说明 helper 或平台边界。
        evidence_status = self.evidence_store.status() if hasattr(self.evidence_store, "status") else {}  # 新增代码+Phase29ComputerUse: 读取证据仓库状态；如果没有这行代码，status 无法告诉用户 evidence 保存目录。
        helper_status = self.observation_helper.status() if hasattr(self.observation_helper, "status") else {}  # 新增代码+Phase29ComputerUse: 读取观察 helper 状态；如果没有这行代码，status 无法说明截图/UIA 能力边界。
        native_observation_diagnostics = helper_status.get("diagnostics", {}) if isinstance(helper_status, dict) else {}  # 新增代码+Phase33WindowsNativeDiagnostics: 提取 helper 诊断对象；如果没有这行代码，backend.status 无法把 WGC/UIA 缺口透传给 /computer。
        action_executor_status = self.action_executor.status() if hasattr(self.action_executor, "status") else {}  # 新增代码+Phase37WindowsSendInputExecutor: 读取 SendInput 执行器状态；如果没有这行代码，用户无法看出真实动作层是否仍缺实现。
        return {"available": sys.platform == "win32" or bool(inventory_status.get("available")), "backend": "windows_ctypes", "reason": "Windows 后端已启用只读窗口 inventory 和窗口状态证据落盘；真实鼠标键盘动作现在通过 Phase37 SendInput 执行器合同控制。", "real_actions_enabled": bool(self.real_actions_enabled and sys.platform == "win32"), "read_only_inventory_enabled": True, "opt_in_env_var": COMPUTER_USE_OPT_IN_ENV_VAR, "observe_opt_in_env_var": COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR, "opt_in_enabled": bool(self.real_actions_enabled), "platform": sys.platform, "evidence_mode": evidence_status.get("evidence_mode", "window_state_artifact"), "evidence_root": evidence_status.get("evidence_root", ""), "inventory_source": inventory_status.get("source", ""), "observation_helper": helper_status.get("helper", ""), "observation_helper_available": bool(helper_status.get("available", False)), "observation_helper_reason": str(helper_status.get("reason", "")), "native_observation_diagnostics": native_observation_diagnostics, "native_helper_available": bool(inventory_status.get("native_helper_available", False)), "native_helper_reason": str(inventory_status.get("native_helper_reason", "Phase 28 只读 inventory 已接入；完整 helper 尚未接入。")), "action_executor_backend": action_executor_status.get("backend", ""), "action_executor": action_executor_status}  # 修改代码+Phase37WindowsSendInputExecutor: 同时报告 evidence/native 观察和 SendInput 动作执行器状态；如果没有这行代码，/computer status 看不到动作层的真实差距。

    def observe(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase27ComputerUse: 提供 Windows 后端只读观察占位；如果没有这段代码，控制器无法统一调用 observe 协议。
        snapshot = self.inventory.snapshot()  # 新增代码+Phase28ComputerUse: 获取只读窗口快照；如果没有这行代码，list_windows/list_apps/get_window_state 没有数据来源。
        base_data = {"action": action, "backend": "windows_ctypes", "platform": sys.platform, "captured_at": snapshot.captured_at, "source": snapshot.source, "filtered_count": snapshot.filtered_count}  # 新增代码+Phase28ComputerUse: 准备通用观察元数据；如果没有这行代码，每个 observe 分支会重复拼接字段。
        if action == "list_windows":  # 新增代码+Phase28ComputerUse: 处理只读窗口列表；如果没有这行代码，模型无法发现可观察窗口。
            data = dict(base_data)  # 新增代码+Phase28ComputerUse: 复制通用数据避免污染其他分支；如果没有这行代码，分支会共享可变对象。
            data["windows"] = [dict(window) for window in snapshot.windows]  # 新增代码+Phase28ComputerUse: 返回安全窗口列表副本；如果没有这行代码，调用方无法拿到窗口引用。
            return ComputerUseActionResult(True, "Windows 只读窗口列表已返回。", data)  # 新增代码+Phase28ComputerUse: 返回 list_windows 成功结果；如果没有这行代码，观察工具没有输出。
        if action == "list_apps":  # 新增代码+Phase28ComputerUse: 处理只读应用列表；如果没有这行代码，模型无法按应用选择窗口。
            data = dict(base_data)  # 新增代码+Phase28ComputerUse: 复制通用数据；如果没有这行代码，apps 分支会污染基础数据。
            data["apps"] = snapshot.apps()  # 新增代码+Phase28ComputerUse: 返回应用分组摘要；如果没有这行代码，list_apps 没有结果。
            return ComputerUseActionResult(True, "Windows 只读应用列表已返回。", data)  # 新增代码+Phase28ComputerUse: 返回 list_apps 成功结果；如果没有这行代码，工具调用无法完成。
        if action == "get_active_window":  # 新增代码+Phase28ComputerUse: 处理活动窗口查询；如果没有这行代码，模型无法知道当前安全活动窗口。
            data = dict(base_data)  # 新增代码+Phase28ComputerUse: 复制通用数据；如果没有这行代码，活动窗口分支会共享可变对象。
            data["window"] = dict(snapshot.active_window) if snapshot.active_window else None  # 新增代码+Phase28ComputerUse: 返回活动窗口副本或 None；如果没有这行代码，调用方无法判断当前焦点。
            return ComputerUseActionResult(snapshot.active_window is not None, "Windows 活动窗口已返回。" if snapshot.active_window else "未找到安全活动窗口。", data)  # 新增代码+Phase28ComputerUse: 返回活动窗口结果；如果没有这行代码，get_active_window 没有统一反馈。
        if action == "get_window_state":  # 新增代码+Phase28ComputerUse: 处理窗口状态查询；如果没有这行代码，动作前无法读取窗口相对几何。
            known_window = snapshot.find_window(arguments.get("window"))  # 新增代码+Phase28ComputerUse: 验证请求窗口是否在快照里；如果没有这行代码，模型可能查询伪造窗口。
            if known_window is None:  # 新增代码+Phase28ComputerUse: 判断窗口是否未知；如果没有这行代码，未知窗口会被当作可观察。
                return ComputerUseActionResult(False, "未知窗口：请先调用 computer_observe/list_windows 获取可信 window 引用。", base_data)  # 新增代码+Phase28ComputerUse: 返回未知窗口错误；如果没有这行代码，模型不知道需要先观察。
            rect = dict(known_window.get("rect", {}))  # 新增代码+Phase28ComputerUse: 读取窗口矩形；如果没有这行代码，状态无法计算截图尺寸。
            width = max(0, int(rect.get("right", 0)) - int(rect.get("left", 0)))  # 新增代码+Phase28ComputerUse: 计算窗口宽度；如果没有这行代码，截图占位尺寸会缺失。
            height = max(0, int(rect.get("bottom", 0)) - int(rect.get("top", 0)))  # 新增代码+Phase28ComputerUse: 计算窗口高度；如果没有这行代码，窗口相对坐标无法判断边界。
            payload = self.observation_helper.observe_window(known_window)  # 新增代码+Phase29ComputerUse: 调用截图/UIA helper 获取窗口观察 payload；如果没有这行代码，get_window_state 仍停留在 Phase 28 占位。
            evidence = self.evidence_store.save_window_state(window=known_window, payload=payload, fallback_width=width, fallback_height=height)  # 新增代码+Phase29ComputerUse: 保存截图和 UIA metadata artifact；如果没有这行代码，窗口状态没有可审计证据文件。
            state = {"window": known_window, "screenshot_id": evidence["screenshot_id"], "screenshot_path": evidence["screenshot_path"], "screenshot_captured": evidence["screenshot_captured"], "screenshot_width": evidence["screenshot_width"], "screenshot_height": evidence["screenshot_height"], "screenshot_origin": {"x": int(rect.get("left", 0)), "y": int(rect.get("top", 0))}, "accessibility_excerpt": evidence["accessibility_excerpt"], "accessibility_truncated": evidence["accessibility_truncated"], "accessibility_filtered_line_count": evidence["accessibility_filtered_line_count"], "focused_element": evidence["focused_element"], "selected_text_preview": evidence["selected_text_preview"], "document_text_preview": evidence["document_text_preview"], "evidence_id": evidence["evidence_id"], "evidence_path": evidence["evidence_path"], "helper_name": evidence["helper_name"], "helper_available": evidence["helper_available"], "helper_reason": evidence["helper_reason"]}  # 修改代码+Phase29ComputerUse: 返回带 evidence 文件和 bounded UIA 摘要的窗口状态；如果没有这行代码，模型无法审计截图和文本来源。
            try:  # 新增代码+Phase39WindowsCoordinates: 在窗口状态分支内导入坐标模型，避免影响其它 Computer Use 入口；如果没有这行代码，状态输出无法补充 DPI 和多显示器上下文。
                from learning_agent.computer_use.coordinates import build_coordinate_context  # 新增代码+Phase39WindowsCoordinates: 包模式导入坐标换算函数；如果没有这行代码，get_window_state 无法计算 coordinate_context。
            except ModuleNotFoundError as error:  # 新增代码+Phase39WindowsCoordinates: 捕获 start_oauth_agent 脚本模式下包名前缀不可用；如果没有这行代码，真实终端入口可能导入失败。
                if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.coordinates"}:  # 新增代码+Phase39WindowsCoordinates: 只允许目标包路径缺失时 fallback；如果没有这行代码，坐标模块内部 bug 会被误吞。
                    raise  # 新增代码+Phase39WindowsCoordinates: 重新抛出非路径类导入错误；如果没有这行代码，排查真实错误会很困难。
                from computer_use.coordinates import build_coordinate_context  # 新增代码+Phase39WindowsCoordinates: 脚本模式导入坐标换算函数；如果没有这行代码，bat 入口无法返回 Phase39 状态字段。
            coordinate_context = build_coordinate_context(known_window, 0, 0)  # 新增代码+Phase39WindowsCoordinates: 以窗口左上角为基准生成状态坐标上下文；如果没有这行代码，截图原点和动作坐标没有统一解释。
            state["coordinate_context"] = coordinate_context  # 新增代码+Phase39WindowsCoordinates: 把完整坐标上下文放进 state；如果没有这行代码，模型无法看到窗口逻辑/物理边界。
            state["coordinate_model"] = coordinate_context.get("model", "")  # 新增代码+Phase39WindowsCoordinates: 在 state 中暴露模型名；如果没有这行代码，终端输出不容易确认 Phase39 是否生效。
            state["dpi_scale"] = dict(coordinate_context.get("dpi_scale", {}))  # 新增代码+Phase39WindowsCoordinates: 在 state 中暴露 DPI 缩放；如果没有这行代码，高 DPI 问题排查需要打开深层对象。
            state["window_logical_rect"] = dict(coordinate_context.get("window_logical_rect", {}))  # 新增代码+Phase39WindowsCoordinates: 在 state 中暴露窗口逻辑矩形；如果没有这行代码，截图边界只能从旧 rect 间接推导。
            state["window_physical_rect"] = dict(coordinate_context.get("window_physical_rect", {}))  # 新增代码+Phase39WindowsCoordinates: 在 state 中暴露窗口物理矩形；如果没有这行代码，真实像素边界无法直接审计。
            data = dict(base_data)  # 新增代码+Phase28ComputerUse: 复制通用数据；如果没有这行代码，状态分支会污染基础对象。
            data["state"] = state  # 新增代码+Phase28ComputerUse: 写入窗口状态；如果没有这行代码，调用方拿不到状态主体。
            data["coordinate_context"] = coordinate_context  # 新增代码+Phase39WindowsCoordinates: 顶层同步坐标上下文，方便测试和终端状态读取；如果没有这行代码，调用方必须深入 state 查找。
            data["coordinate_model"] = coordinate_context.get("model", "")  # 新增代码+Phase39WindowsCoordinates: 顶层同步坐标模型名；如果没有这行代码，验收脚本不容易快速断言 Phase39 生效。
            data["dpi_scale"] = dict(coordinate_context.get("dpi_scale", {}))  # 新增代码+Phase39WindowsCoordinates: 顶层同步 DPI 缩放；如果没有这行代码，终端状态无法直观看到缩放信息。
            return ComputerUseActionResult(True, "Windows 只读窗口状态已返回。", data)  # 新增代码+Phase28ComputerUse: 返回窗口状态成功结果；如果没有这行代码，get_window_state 没有反馈。
        return ComputerUseActionResult(False, f"Windows 后端暂不支持观察动作：{action}", base_data)  # 新增代码+Phase28ComputerUse: 拒绝未知观察动作；如果没有这行代码，observe 错误可能静默失败。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase8ProductionEdges: 执行已通过控制器确认的 Windows 动作；如果没有这段代码，真实后端无法接收动作。
        if not self.real_actions_enabled:  # 新增代码+Phase28ComputerUse: 只读 inventory 模式拒绝所有真实动作；如果没有这行代码，为了观察窗口可能误触发鼠标键盘。
            return ComputerUseActionResult(False, "Windows Computer Use 当前是只读 inventory 模式，不执行鼠标、键盘或窗口动作。", {"backend": "windows_ctypes", "action": action, "read_only_inventory_enabled": True})  # 新增代码+Phase28ComputerUse: 返回只读拒绝结果；如果没有这行代码，模型不知道动作为什么被拒绝。
        if sys.platform != "win32":  # 新增代码+Phase8ProductionEdges: 非 Windows 平台直接拒绝；如果没有这行代码，调用 Win32 API 会崩溃。
            return ComputerUseActionResult(False, "Windows Computer Use 后端只能在 Windows 上执行。", {"backend": "windows_ctypes", "platform": sys.platform})  # 新增代码+Phase8ProductionEdges: 返回清楚的平台拒绝信息；如果没有这行代码，用户只能看到底层异常。
        if action == "screenshot":  # 新增代码+Phase8ProductionEdges: 处理屏幕观察动作；如果没有这行代码，OS 后端没有基础显示器信息入口。
            import ctypes  # 修改代码+Phase37WindowsSendInputExecutor: 仅为屏幕尺寸占位延迟导入 ctypes；如果没有这行代码，screenshot 仍拿不到主屏幕尺寸。
            user32 = ctypes.windll.user32  # 修改代码+Phase37WindowsSendInputExecutor: 仅在截图尺寸分支获取 user32；如果没有这行代码，尺寸读取没有系统入口。
            width = int(user32.GetSystemMetrics(0))  # 新增代码+Phase8ProductionEdges: 读取主屏幕宽度；如果没有这行代码，截图状态缺少尺寸证据。
            height = int(user32.GetSystemMetrics(1))  # 新增代码+Phase8ProductionEdges: 读取主屏幕高度；如果没有这行代码，截图状态缺少尺寸证据。
            return ComputerUseActionResult(True, "Windows 屏幕尺寸已读取；完整截图文件保存将在后续阶段接入。", {"backend": "windows_ctypes", "action": action, "width": width, "height": height, "evidence": {"kind": "screenshot", "backend": "windows_ctypes", "captured": False, "width": width, "height": height, "reason": "Phase 20 只记录屏幕尺寸证据，尚不保存完整截图文件。"}})  # 修改代码+Phase20ComputerUse: 返回可审计屏幕尺寸和截图证据边界；如果没有这行代码，观察动作没有可追踪证据。
        executor_result = self.action_executor.execute(action, dict(arguments))  # 新增代码+Phase37WindowsSendInputExecutor: 把鼠标键盘动作交给 SendInput 执行器；如果没有这行代码，后端仍会使用旧 mouse_event 路径或继续缺动作。
        return ComputerUseActionResult(executor_result.ok, executor_result.message, dict(executor_result.data))  # 新增代码+Phase37WindowsSendInputExecutor: 把执行器结果转换为控制器统一结果；如果没有这行代码，ComputerUseController 无法附加 audit/evidence。


def build_default_computer_use_backend(environ: dict[str, str] | None = None) -> ComputerUseBackend:  # 新增代码+Phase8ProductionEdges: 集中决定默认 Computer Use 后端；如果没有这段代码，启用真实桌面控制的策略会散落在各处。
    source = os.environ if environ is None else environ  # 新增代码+Phase8ProductionEdges: 支持测试传入假环境；如果没有这行代码，测试会污染真实环境变量。
    enabled = str(source.get(COMPUTER_USE_OPT_IN_ENV_VAR, "")).lower() in {"1", "true", "yes"}  # 修改代码+Phase20ComputerUse: 使用统一常量读取真实桌面控制开关；如果没有这行代码，状态提示和实际开关可能不一致。
    observe_enabled = str(source.get(COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR, "")).lower() in {"1", "true", "yes"}  # 新增代码+Phase28ComputerUse: 读取只读窗口观察开关；如果没有这行代码，用户无法只启用安全 inventory。
    native_observe_enabled = str(source.get(COMPUTER_USE_NATIVE_OBSERVE_OPT_IN_ENV_VAR, "")).lower() in {"1", "true", "yes"}  # 新增代码+Phase32WindowsNativeHelper: 读取 native 截图/文本只读 helper 开关；如果没有这行代码，只读 inventory 会和真实屏幕读取边界混在一起。
    observation_helper = WindowsNativeWindowObservationHelper() if native_observe_enabled and sys.platform == "win32" else None  # 新增代码+Phase32WindowsNativeHelper: 仅在显式 opt-in 且 Windows 时创建 native helper；如果没有这行代码，用户无法安全区分枚举窗口和读取屏幕内容。
    if enabled and sys.platform == "win32":  # 新增代码+Phase8ProductionEdges: 同时满足启用和 Windows 才返回真实后端；如果没有这行代码，非 Windows 会误入 Windows API。
        return WindowsComputerUseBackend(real_actions_enabled=True, observation_helper=observation_helper)  # 修改代码+Phase32WindowsNativeHelper: 返回真实动作后端并按 opt-in 挂载 native 观察 helper；如果没有这行代码，动作前后 evidence 仍无法使用 native 截图/文本。
    if observe_enabled and sys.platform == "win32":  # 新增代码+Phase28ComputerUse: 只读观察开关开启且平台是 Windows 时返回只读后端；如果没有这行代码，用户只能通过高风险动作开关观察窗口。
        return WindowsComputerUseBackend(real_actions_enabled=False, observation_helper=observation_helper)  # 修改代码+Phase32WindowsNativeHelper: 返回只读后端并仅在 native opt-in 时挂载 helper；如果没有这行代码，/computer observe 无法安全启用截图/文本证据。
    return UnavailableComputerUseBackend()  # 新增代码+Phase8ProductionEdges: 默认安全关闭；如果没有这行代码，未配置时没有安全兜底。


class ComputerUseController:  # 新增代码+OSComputerUse: 在 agent 和后端之间提供安全控制层；若没有这段代码，真实桌面操作缺少统一确认和参数校验。
    ALLOWED_ACTIONS: set[str] = {"screenshot", "move_mouse", "click", "double_click", "type_text", "press_key", "scroll"}  # 新增代码+OSComputerUse: 限定允许的桌面动作集合；若没有这行代码，模型可能传入任意未知动作。
    OBSERVE_ACTIONS: set[str] = {"list_apps", "list_windows", "get_active_window", "get_window_state"}  # 新增代码+Phase27ComputerUse: 限定只读观察动作集合；如果没有这行代码，observe 可能被滥用成任意桌面命令。
    MAX_TEXT_LENGTH: int = 2000  # 新增代码+OSComputerUse: 限制一次输入文本长度；若没有这行代码，模型可能一次性向桌面注入过长文本。

    def __init__(self, backend: ComputerUseBackend | None = None, lock_manager: ComputerUseLockManager | None = None, owner_session_id: str = "learning-agent-default-session", auto_acquire_lock: bool | None = None, audit_store: ComputerUseAuditStore | None = None, approval_model: Any | None = None) -> None:  # 修改代码+Phase38WindowsComputerApproval: 初始化控制器并允许注入 Windows approval 模型；如果没有这段代码，controller 无法在真实后端执行前执行会话授权检查。
        self.backend = backend or build_default_computer_use_backend()  # 修改代码+Phase8ProductionEdges: 通过工厂选择默认安全关闭或显式启用的 Windows 后端；如果没有这行代码，真实后端无法受环境变量控制。
        self.lock_manager = lock_manager if lock_manager is not None else (ComputerUseLockManager() if backend is None else None)  # 新增代码+Phase30ComputerUseActionGate: 生产默认启用 durable lock，注入测试后端时保持旧兼容；如果没有这行代码，真实 agent 默认动作没有当前锁门禁。
        self.owner_session_id = str(owner_session_id or "learning-agent-default-session")  # 新增代码+Phase30ComputerUseActionGate: 保存当前控制器会话 id；如果没有这行代码，锁管理器无法判断谁在请求桌面控制。
        self.auto_acquire_lock = bool(auto_acquire_lock) if auto_acquire_lock is not None else bool(backend is None and lock_manager is None)  # 新增代码+Phase30ComputerUseActionGate: 默认生产路径可在无人持锁时自动获取锁，测试注入路径保持手动；如果没有这行代码，真实 agent 可能永远卡在缺锁。
        self.audit_store = audit_store if audit_store is not None else (ComputerUseAuditStore() if backend is None else None)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 生产默认启用落盘审计而测试注入后端默认不写磁盘；如果没有这行代码，真实动作无法形成长期证据链。
        self.approval_model = approval_model  # 新增代码+Phase38WindowsComputerApproval: 保存可选审批模型；如果没有这行代码，注入的 session allowlist 不会参与动作门禁。
        self.audit_log: list[dict[str, Any]] = []  # 新增代码+Phase20ComputerUse: 保存本控制器生命周期里的桌面动作审计事件；如果没有这行代码，被拒绝或执行过的动作无法在状态里复盘。

    def status(self) -> dict[str, Any]:  # 新增代码+OSComputerUse: 返回 Computer Use 当前状态；若没有这段代码，computer_status 工具没有实现来源。
        backend_status = self.backend.status()  # 新增代码+OSComputerUse: 向后端读取状态；若没有这行代码，状态输出无法反映真实后端。
        audit_status = {"event_count": len(self.audit_log), "last_event": dict(self.audit_log[-1]) if self.audit_log else None, "store": self.audit_store.status() if self.audit_store is not None else {"enabled": False, "reason": "测试注入后端未配置落盘审计。"}}  # 修改代码+Phase31ComputerUseLockAbortEvidence: 汇总内存审计和可选落盘位置；如果没有这行代码，用户看不到 evidence chain 保存在哪里。
        lock_status = self.lock_manager.status() if self.lock_manager is not None else {"enabled": False, "reason": "测试注入后端未配置 durable lock。"}  # 新增代码+Phase30ComputerUseActionGate: 读取锁状态或说明未启用；如果没有这行代码，用户看不到当前锁/abort 边界。
        approval_status = self.approval_model.status() if self.approval_model is not None and hasattr(self.approval_model, "status") else {"enabled": False, "reason": "未配置 Phase38 approval 模型。"}  # 新增代码+Phase38WindowsComputerApproval: 读取审批模型状态或说明未启用；如果没有这行代码，用户无法知道当前动作是否受 session allowlist 保护。
        return {"tool": "computer_use", "actions": sorted(self.ALLOWED_ACTIONS), "observe_actions": sorted(self.OBSERVE_ACTIONS), "backend": backend_status, "audit": audit_status, "lock": lock_status, "approval": approval_status, "owner_session_id": self.owner_session_id, "auto_acquire_lock": self.auto_acquire_lock}  # 修改代码+Phase38WindowsComputerApproval: 返回写动作、只读观察、后端、审计、锁、approval 和自动取锁策略；如果没有这行代码，模型无法区分 observe、action、lock 和 approval 状态。

    def _record_audit(self, action: str, allowed: bool, reason: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase20ComputerUse: 记录一次桌面动作安全判断；如果没有这段函数，拒绝和执行结果无法获得统一审计 id。
        backend_status = self.backend.status()  # 新增代码+Phase20ComputerUse: 读取后端名称写入审计事件；如果没有这行代码，事后不知道动作由哪个后端处理。
        safe_arguments = redact_action_arguments(action, arguments)  # 新增代码+Phase30ComputerUseActionGate: 先把审计参数脱敏；如果没有这行代码，原始 text 可能进入 audit_log。
        event = {"audit_id": f"computer-audit-{len(self.audit_log) + 1}", "action": action, "allowed": allowed, "reason": reason, "backend": backend_status.get("backend"), "has_coordinates": "x" in safe_arguments or "y" in safe_arguments, "text_length": int(safe_arguments.get("text_length", 0)), "text_sha256_16": str(safe_arguments.get("text_sha256_16", "")), "owner_session_id": self.owner_session_id, "argument_summary": safe_arguments}  # 修改代码+Phase30ComputerUseActionGate: 只记录必要元数据和脱敏摘要；如果没有这行代码，审计日志要么不可追踪要么可能泄露敏感内容。
        self.audit_log.append(event)  # 新增代码+Phase20ComputerUse: 把事件加入审计日志；如果没有这行代码，status 里看不到最近发生的安全判断。
        return event  # 新增代码+Phase20ComputerUse: 返回事件方便结果携带同一个审计 id；如果没有这行代码，工具返回无法和审计日志关联。

    def _with_audit(self, result: ComputerUseActionResult, event: dict[str, Any], action_evidence: dict[str, Any] | None = None) -> ComputerUseActionResult:  # 修改代码+Phase30ComputerUseActionGate: 把审计 id 和可选动作证据附加到动作结果里；如果没有这段函数，调用方需要自己拼接审计字段且容易遗漏。
        data = dict(result.data)  # 新增代码+Phase20ComputerUse: 复制结果数据避免直接修改冻结结果里的原始字典；如果没有这行代码，审计字段可能污染后端返回对象。
        data["audit_id"] = event["audit_id"]  # 新增代码+Phase20ComputerUse: 在结果中写入审计 id；如果没有这行代码，用户无法把这次结果对应到状态审计事件。
        if action_evidence is not None:  # 新增代码+Phase30ComputerUseActionGate: 只有写动作准备了证据时才附加 envelope；如果没有这行代码，observe 结果会被错误加入动作证据。
            evidence = dict(action_evidence)  # 新增代码+Phase30ComputerUseActionGate: 复制证据对象避免污染调用方传入数据；如果没有这行代码，后续修改可能影响审计事实。
            evidence["audit_id"] = event["audit_id"]  # 新增代码+Phase30ComputerUseActionGate: 把同一个 audit_id 写入证据；如果没有这行代码，结果和证据无法一一对应。
            for evidence_key in ("before_evidence", "after_evidence"):  # 新增代码+Phase31ComputerUseLockAbortEvidence: 遍历动作前后证据；如果没有这行代码，before/after 子证据可能缺少同一个 audit_id。
                if isinstance(evidence.get(evidence_key), dict):  # 新增代码+Phase31ComputerUseLockAbortEvidence: 只处理字典形态的子证据；如果没有这行代码，异常类型会在复制时出错。
                    nested_evidence = dict(evidence[evidence_key])  # 新增代码+Phase31ComputerUseLockAbortEvidence: 复制子证据避免修改原对象；如果没有这行代码，调用方传入证据可能被意外污染。
                    nested_evidence["audit_id"] = event["audit_id"]  # 新增代码+Phase31ComputerUseLockAbortEvidence: 给子证据补同一个审计 id；如果没有这行代码，before/after 无法独立追溯到动作。
                    evidence[evidence_key] = nested_evidence  # 新增代码+Phase31ComputerUseLockAbortEvidence: 写回补齐后的子证据；如果没有这行代码，结果仍会保留旧的空 audit_id。
            if self.audit_store is not None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 检查是否配置了落盘审计仓库；如果没有这行代码，测试注入路径会误写真实磁盘。
                disk_record = self.audit_store.record_event(event, evidence)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 保存审计事件和证据链；如果没有这行代码，动作完成后没有可打开的链路文件。
                data["audit_events_path"] = disk_record.get("events_path", "")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 把事件日志路径返回给调用方；如果没有这行代码，用户不知道事件写到了哪里。
                if disk_record.get("chain_path"):  # 新增代码+Phase31ComputerUseLockAbortEvidence: 检查动作证据链是否保存成功；如果没有这行代码，空链路路径也可能被当作有效证据。
                    evidence["chain_path"] = disk_record["chain_path"]  # 新增代码+Phase31ComputerUseLockAbortEvidence: 把证据链路径写进动作证据；如果没有这行代码，结果和落盘链路会断开。
                    data["audit_chain_path"] = disk_record["chain_path"]  # 新增代码+Phase31ComputerUseLockAbortEvidence: 在结果顶层也暴露链路路径；如果没有这行代码，终端 UI 很难直接显示链路位置。
            data["action_evidence"] = evidence  # 新增代码+Phase30ComputerUseActionGate: 将动作证据放进结果数据；如果没有这行代码，模型和用户看不到坐标、锁和窗口证据。
        elif self.audit_store is not None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 对 observe 和拒绝事件也保存审计事件；如果没有这行代码，只有成功动作有磁盘轨迹。
            disk_record = self.audit_store.record_event(event)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 保存无动作证据的普通事件；如果没有这行代码，状态查询和拒绝门禁无法长期复盘。
            data["audit_events_path"] = disk_record.get("events_path", "")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回事件日志路径；如果没有这行代码，用户不知道普通事件写到了哪里。
        return ComputerUseActionResult(result.ok, result.message, data)  # 新增代码+Phase20ComputerUse: 返回带审计 id 的新结果；如果没有这行代码，ComputerUseActionResult 的不可变约束会被破坏。

    def _capture_action_window_evidence(self, phase: str, audit_id: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，采集动作前后窗口状态证据；如果没有这段函数，动作证据只有计划参数没有前后现场。
        raw_window = arguments.get("window")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 读取动作绑定窗口；如果没有这行代码，证据采集不知道要观察哪个窗口。
        if raw_window is None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 判断动作是否没有窗口目标；如果没有这行代码，旧截图动作可能因无窗口而报错。
            return {"audit_id": audit_id, "phase": phase, "captured": False, "reason": "missing_window"}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回未采集原因；如果没有这行代码，证据链会缺少解释。
        window_ref = build_window_ref(raw_window)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 把窗口参数转换成强类型引用；如果没有这行代码，坏窗口字段会直接传给后端。
        if window_ref is None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 判断窗口引用是否无效；如果没有这行代码，无效窗口可能导致 observe 失败异常。
            return {"audit_id": audit_id, "phase": phase, "captured": False, "reason": "invalid_window"}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回无效窗口原因；如果没有这行代码，证据链无法解释为何没有现场状态。
        probe = self.backend.observe("get_window_state", {"window": window_ref.to_dict(), "validation_only": True, "evidence_phase": phase})  # 新增代码+Phase31ComputerUseLockAbortEvidence: 通过只读 observe 获取窗口状态；如果没有这行代码，before/after 只是空壳字段。
        state_payload = probe.data.get("state", {}) if isinstance(probe.data, dict) else {}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 安全读取后端返回状态；如果没有这行代码，异常 data 类型会破坏动作执行。
        state = dict(state_payload) if isinstance(state_payload, dict) else {}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 复制状态字典避免污染后端结果；如果没有这行代码，后续审计脱敏可能改到原对象。
        return {"audit_id": audit_id, "phase": phase, "captured": bool(probe.ok), "message": probe.message, "window": window_ref.to_dict(), "backend": probe.data.get("backend", "") if isinstance(probe.data, dict) else "", "state": state}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回可落盘的现场证据；如果没有这行代码，审计链不能说明动作前后看到什么。
    # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，_capture_action_window_evidence 到此结束；如果没有这个边界说明，初学者不容易看出证据采集范围。

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

    def _reject_unapproved_action(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult | None:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，在后端执行前执行 approval 检查；如果没有这段函数，高风险窗口可能通过已有锁门禁后仍被后端执行。
        if self.approval_model is None or not hasattr(self.approval_model, "evaluate"):  # 新增代码+Phase38WindowsComputerApproval: 没有配置审批模型时保持旧路径兼容；如果没有这行代码，未启用 Phase38 的测试和旧调用会被误拦截。
            return None  # 新增代码+Phase38WindowsComputerApproval: 返回 None 表示 approval 不拦截；如果没有这行代码，正常动作会卡在空模型路径。
        if action == "screenshot":  # 新增代码+Phase38WindowsComputerApproval: 只读截图不进入写动作审批；如果没有这行代码，观察能力可能被错误要求会话授权。
            return None  # 新增代码+Phase38WindowsComputerApproval: 放行只读截图到后续路径；如果没有这行代码，状态观察会退化。
        approval = self.approval_model.evaluate(action, dict(arguments))  # 新增代码+Phase38WindowsComputerApproval: 让 approval 模型评估动作和窗口；如果没有这行代码，session allowlist 和禁止目标规则不会生效。
        if bool(approval.get("allowed", False)):  # 新增代码+Phase38WindowsComputerApproval: 判断审批是否允许；如果没有这行代码，允许动作也会被误拒绝。
            return None  # 新增代码+Phase38WindowsComputerApproval: 审批通过时继续后续窗口、锁和后端流程；如果没有这行代码，授权 app 仍无法执行动作。
        result = ComputerUseActionResult(False, "Computer Use approval 未通过，已拒绝执行桌面动作。", {"action": action, "approval": approval})  # 新增代码+Phase38WindowsComputerApproval: 构造审批拒绝结果；如果没有这行代码，用户看不到拒绝原因和目标摘要。
        event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase38WindowsComputerApproval: 记录审批拒绝审计；如果没有这行代码，approval 拦截无法在 status 和磁盘日志中复盘。
        return self._with_audit(result, event)  # 新增代码+Phase38WindowsComputerApproval: 返回带审计 id 的审批拒绝结果；如果没有这行代码，调用方无法把拒绝结果和审计事件关联。
    # 新增代码+Phase38WindowsComputerApproval: 函数段结束，_reject_unapproved_action 到此结束；如果没有这个边界说明，读者不容易看出 approval 拦截范围。

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
        approval_rejection = self._reject_unapproved_action(action, arguments)  # 新增代码+Phase38WindowsComputerApproval: 在真实后端前先执行 approval 拦截；如果没有这行代码，禁止目标和未授权 app 仍可能进入后端。
        if approval_rejection is not None:  # 新增代码+Phase38WindowsComputerApproval: 判断 approval 是否拒绝本次动作；如果没有这行代码，拒绝结果会被忽略。
            return approval_rejection  # 新增代码+Phase38WindowsComputerApproval: 返回审批拒绝而不调用后端；如果没有这行代码，表面拒绝但后端仍可能执行。
        window_rejection = self._reject_unknown_window_target(action, arguments)  # 新增代码+Phase27ComputerUse: 在执行写动作前检查窗口目标是否可信；如果没有这行代码，未知窗口可能被传给真实后端。
        if window_rejection is not None:  # 新增代码+Phase27ComputerUse: 判断窗口校验是否产生拒绝结果；如果没有这行代码，拒绝结果会被忽略。
            return window_rejection  # 新增代码+Phase27ComputerUse: 返回未知窗口拒绝而不调用后端；如果没有这行代码，后端仍可能执行危险动作。
        if self.lock_manager is not None and action != "screenshot" and arguments.get("window") is None:  # 新增代码+Phase30ComputerUseActionGate: 在启用锁门禁时要求写动作绑定可信窗口；如果没有这行代码，真实鼠标键盘可能回到全屏裸坐标模式。
            result = ComputerUseActionResult(False, "缺少可信 window：启用 Phase 30 动作门禁后，请先用 computer_observe/list_windows 获取窗口目标。", {"action": action})  # 新增代码+Phase30ComputerUseActionGate: 构造缺少窗口的拒绝结果；如果没有这行代码，模型不知道下一步应先观察窗口。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase30ComputerUseActionGate: 记录缺少窗口的拒绝审计；如果没有这行代码，门禁拒绝无法复盘。
            return self._with_audit(result, event)  # 新增代码+Phase30ComputerUseActionGate: 返回带审计 id 的拒绝结果；如果没有这行代码，工具输出无法关联状态审计。
        if self.lock_manager is not None and not self.lock_manager.has_lock(self.owner_session_id) and self.auto_acquire_lock:  # 新增代码+Phase30ComputerUseActionGate: 生产默认路径在无人持有时尝试自动取锁；如果没有这行代码，真实 agent 默认动作会永远缺少当前锁。
            acquire_result = self.lock_manager.acquire(self.owner_session_id, owner_label="learning_agent_controller")  # 新增代码+Phase30ComputerUseActionGate: 用当前会话获取 durable lock；如果没有这行代码，后续 has_lock 仍然失败。
            if not acquire_result.get("acquired", False):  # 新增代码+Phase30ComputerUseActionGate: 判断自动取锁是否被其他 session 拒绝；如果没有这行代码，抢锁失败可能继续执行动作。
                result = ComputerUseActionResult(False, "无法获取 desktop control lock，已拒绝执行桌面动作。", {"action": action, "lock": acquire_result.get("status", {})})  # 新增代码+Phase30ComputerUseActionGate: 构造自动取锁失败结果；如果没有这行代码，模型不知道动作为何被拦截。
                event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase30ComputerUseActionGate: 记录取锁失败审计；如果没有这行代码，锁冲突无法复盘。
                return self._with_audit(result, event)  # 新增代码+Phase30ComputerUseActionGate: 返回带审计 id 的取锁失败结果；如果没有这行代码，工具输出无法关联审计。
        if self.lock_manager is not None and not self.lock_manager.has_lock(self.owner_session_id):  # 新增代码+Phase30ComputerUseActionGate: 要求当前会话持有 durable desktop lock；如果没有这行代码，两个会话可能同时控制桌面。
            lock_status = self.lock_manager.status()  # 新增代码+Phase30ComputerUseActionGate: 读取当前锁状态用于返回给模型；如果没有这行代码，用户不知道是谁持有锁。
            result = ComputerUseActionResult(False, "缺少当前会话的 desktop control lock，已拒绝执行桌面动作。", {"action": action, "lock": lock_status})  # 新增代码+Phase30ComputerUseActionGate: 构造缺锁拒绝结果；如果没有这行代码，锁门禁失败没有可读解释。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase30ComputerUseActionGate: 记录缺锁拒绝审计；如果没有这行代码，安全拦截无法在 status 中复盘。
            return self._with_audit(result, event)  # 新增代码+Phase30ComputerUseActionGate: 返回带审计 id 的缺锁结果；如果没有这行代码，调用方无法关联这次拦截。
        if self.lock_manager is not None and self.lock_manager.is_abort_requested():  # 新增代码+Phase30ComputerUseActionGate: 在调用后端前检查急停标记；如果没有这行代码，用户请求 abort 后下一次动作仍可能执行。
            abort_status = self.lock_manager.abort_status()  # 新增代码+Phase30ComputerUseActionGate: 读取 abort 摘要用于结果说明；如果没有这行代码，模型不知道急停原因。
            result = ComputerUseActionResult(False, "desktop control abort flag 已触发，已拒绝执行下一次桌面动作。", {"action": action, "abort": abort_status})  # 新增代码+Phase30ComputerUseActionGate: 构造急停拒绝结果；如果没有这行代码，abort 拦截没有稳定返回对象。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase30ComputerUseActionGate: 记录急停拒绝审计；如果没有这行代码，用户无法确认 abort 生效。
            return self._with_audit(result, event)  # 新增代码+Phase30ComputerUseActionGate: 返回带审计 id 的急停结果；如果没有这行代码，调用方无法关联这次中止。
        lock_status = self.lock_manager.status() if self.lock_manager is not None else {"enabled": False, "owner_session_id": self.owner_session_id}  # 新增代码+Phase30ComputerUseActionGate: 准备动作证据里的锁状态；如果没有这行代码，action evidence 无法说明持锁会话。
        prepared_action = prepare_action_arguments(action, arguments)  # 新增代码+Phase30ComputerUseActionGate: 转换窗口相对坐标并准备后端参数；如果没有这行代码，真实后端可能收到错误坐标空间。
        backend_arguments = dict(prepared_action["backend_arguments"])  # 新增代码+Phase30ComputerUseActionGate: 复制最终后端参数；如果没有这行代码，后续审计和后端可能共享可变对象。
        before_evidence = self._capture_action_window_evidence("before", "", arguments)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 在后端执行前采集窗口状态；如果没有这行代码，动作证据无法证明执行前现场。
        result = self.backend.execute(action, backend_arguments)  # 修改代码+Phase30ComputerUseActionGate: 把通过门禁且已转换坐标的动作交给后端；若没有这行代码，Computer Use 永远不会执行到后端。
        after_evidence = self._capture_action_window_evidence("after", "", arguments)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 在后端执行后采集窗口状态；如果没有这行代码，动作证据无法证明执行后现场。
        action_evidence = build_action_evidence(action, arguments, prepared_action, lock_status)  # 新增代码+Phase30ComputerUseActionGate: 生成动作证据 envelope；如果没有这行代码，结果无法关联窗口、坐标、锁和策略版本。
        action_evidence["before_evidence"] = before_evidence  # 新增代码+Phase31ComputerUseLockAbortEvidence: 把动作前现场放进证据 envelope；如果没有这行代码，落盘链路没有 before 节点。
        action_evidence["after_evidence"] = after_evidence  # 新增代码+Phase31ComputerUseLockAbortEvidence: 把动作后现场放进证据 envelope；如果没有这行代码，落盘链路没有 after 节点。
        event = self._record_audit(action, result.ok, result.message, backend_arguments)  # 修改代码+Phase30ComputerUseActionGate: 记录脱敏后的最终后端参数；如果没有这行代码，已允许动作没有安全审计闭环。
        return self._with_audit(result, event, action_evidence)  # 修改代码+Phase30ComputerUseActionGate: 返回带审计 id 和动作证据的最终结果；如果没有这行代码，成功动作和证据链无法关联。
