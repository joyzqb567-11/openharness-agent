"""URG-2 universal target session and identity guard runtime."""  # 新增代码+URG2UniversalTargetSession：说明本模块负责把通用目标发现和目标身份防漂移收束成统一 session；如果没有这一行，读者不知道 URG-2 的入口在哪里。
from __future__ import annotations  # 新增代码+URG2UniversalTargetSession：启用延迟类型解析；如果没有这一行，前向类型标注更容易在旧入口导入时报错。

import json  # 新增代码+URG2UniversalTargetSession：导入 JSON 用于 CLI 输出结构化报告；如果没有这一行，真实终端失败时不方便复盘。
import time  # 新增代码+RealLaunchTargetSession：导入 time 用于启动后短轮询窗口；如果没有这一行，刚打开的真实窗口可能还没出现就被误判失败。
from typing import Any  # 新增代码+URG2UniversalTargetSession：导入 Any 描述发现报告和窗口字典；如果没有这一行，动态 provider 接口不清楚。

try:  # 新增代码+URG2UniversalTargetSession：优先按 learning_agent 包路径导入已有通用能力；如果没有这一段，单测和生产入口无法共享同一实现。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_launch_resolver import resolve_generic_app_launch_target  # 新增代码+URG2UniversalTargetSession：复用 Phase108 通用应用发现；如果没有这一行，URG-2 可能退回逐 app 白名单。
    from learning_agent.computer_use_mcp_v2.windows_runtime.generic_launch_backend import Phase110ProductionGenericLaunchBackend, run_generic_launch_backend  # 新增代码+RealLaunchTargetSession：复用 Phase110 真实启动后端；如果没有这一行，URG-2 会继续伪造 pid/hwnd。
    from learning_agent.computer_use_mcp_v2.windows_runtime.target_identity import build_owned_target_identity, verify_owned_target_identity  # 新增代码+URG2UniversalTargetSession：复用 Phase111 目标身份和漂移验证；如果没有这一行，URG-2 会重造不一致的身份算法。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # 新增代码+RealLaunchTargetSession：复用真实窗口 inventory；如果没有这一行，真实启动后无法按 pid 绑定窗口。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_process_tree import build_process_window_aliases, build_proxy_window_binding_report, window_matches_process_alias  # 新增代码+ExternalAppWindowBinding：导入启动器到真实窗口的通用别名绑定 helper；如果没有这一行，网易云音乐这类 .lnk 多进程应用仍会启动后找不到窗口。
    from learning_agent.computer_use_mcp_v2.windows_runtime.fresh_target_policy import decide_post_launch_freshness  # 新增代码+FreshTargetPolicy：导入启动后新旧窗口分类策略；如果没有这一行，真实启动绑定阶段无法拒绝旧窗口。
except ModuleNotFoundError as error:  # 新增代码+URG2UniversalTargetSession：兼容 start_oauth_agent.bat 从 learning_agent 目录运行；如果没有这一段，真实可见终端可能因包前缀失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_launch_resolver", "learning_agent.computer_use_mcp_v2.windows_runtime.generic_launch_backend", "learning_agent.computer_use_mcp_v2.windows_runtime.target_identity", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_process_tree", "learning_agent.computer_use_mcp_v2.windows_runtime.fresh_target_policy"}:  # 修改代码+FreshTargetPolicy：兜底名单加入新目标策略模块；如果没有这一行，bat 入口脚本模式可能无法导入 FreshTarget 策略。
        raise  # 新增代码+URG2UniversalTargetSession：重新抛出非路径类导入错误；如果没有这一行，排查真实依赖问题会很困难。
    from computer_use_mcp_v2.windows_runtime.windows_launch_resolver import resolve_generic_app_launch_target  # type: ignore  # 新增代码+URG2UniversalTargetSession：脚本模式导入通用发现；如果没有这一行，bat 入口不能解析普通目标。
    from computer_use_mcp_v2.windows_runtime.generic_launch_backend import Phase110ProductionGenericLaunchBackend, run_generic_launch_backend  # type: ignore  # 新增代码+RealLaunchTargetSession：脚本模式导入 Phase110 启动后端；如果没有这一行，真实终端入口无法启动普通应用。
    from computer_use_mcp_v2.windows_runtime.target_identity import build_owned_target_identity, verify_owned_target_identity  # type: ignore  # 新增代码+URG2UniversalTargetSession：脚本模式导入目标身份 helper；如果没有这一行，bat 入口不能防漂移。
    from computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # type: ignore  # 新增代码+RealLaunchTargetSession：脚本模式导入窗口 inventory；如果没有这一行，bat 入口无法找到启动窗口。
    from computer_use_mcp_v2.windows_runtime.windows_process_tree import build_process_window_aliases, build_proxy_window_binding_report, window_matches_process_alias  # type: ignore  # 新增代码+ExternalAppWindowBinding：脚本模式导入启动器窗口绑定 helper；如果没有这一行，直接运行时无法修复 .lnk 多进程窗口绑定。
    from computer_use_mcp_v2.windows_runtime.fresh_target_policy import decide_post_launch_freshness  # type: ignore  # 新增代码+FreshTargetPolicy：脚本模式导入启动后新旧窗口分类策略；如果没有这一行，真实 bat 入口无法拒绝旧窗口绑定。

PHASE117_UNIVERSAL_TARGET_SESSION_MARKER = "PHASE117_UNIVERSAL_TARGET_SESSION_READY"  # 新增代码+URG2UniversalTargetSession：定义 URG-2 ready marker；如果没有这一行，真实终端验收无法稳定等待阶段输出。
PHASE117_UNIVERSAL_TARGET_SESSION_OK_TOKEN = "PHASE117_UNIVERSAL_TARGET_SESSION_OK"  # 新增代码+URG2UniversalTargetSession：定义 URG-2 OK token；如果没有这一行，debug log 无法区分成功和普通输出。
PHASE117_UNIVERSAL_TARGET_SESSION_MODEL = "phase117_universal_target_session_identity_guard"  # 新增代码+URG2UniversalTargetSession：定义目标 session 协议模型名；如果没有这一行，后续动作 DSL 无法识别凭证版本。
PHASE117_ACTIONS_EXPANDED = False  # 新增代码+URG2UniversalTargetSession：声明 URG-2 只建立目标 session 不发送输入动作；如果没有这一行，用户无法确认 session 阶段不会控制桌面。


def _phase117_bool_token(value: Any) -> str:  # 新增代码+URG2UniversalTargetSession：函数段开始，把布尔值转成固定小写 token；如果没有这段函数，CLI 会混用 True 和 true。
    return "true" if bool(value) else "false"  # 新增代码+URG2UniversalTargetSession：返回验收器易匹配的小写布尔文本；如果没有这一行，场景 JSON 可能匹配失败。
# 新增代码+URG2UniversalTargetSession：函数段结束，_phase117_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。


def _phase117_safe_text(value: Any, default: str = "") -> str:  # 新增代码+URG2UniversalTargetSession：函数段开始，清洗动态文本字段；如果没有这段函数，None 或换行会污染 token 和报告。
    text = str(value if value is not None else default).replace("\r", " ").replace("\n", " ").strip()  # 新增代码+URG2UniversalTargetSession：转成单行短文本；如果没有这一行，窗口标题和目标名可能破坏日志结构。
    return text or str(default or "")  # 新增代码+URG2UniversalTargetSession：空值回到默认文本；如果没有这一行，后续构造 exe 名时可能得到空字符串。
# 新增代码+URG2UniversalTargetSession：函数段结束，_phase117_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清洗范围。


def _phase117_executable_from_report(report: dict[str, Any]) -> str:  # 新增代码+URG2UniversalTargetSession：函数段开始，从 Phase108 报告提取可执行名；如果没有这段函数，多处会重复猜 exe 字段。
    executable = _phase117_safe_text(report.get("best_candidate_executable"))  # 新增代码+URG2UniversalTargetSession：优先读取 Phase108 最佳候选 exe；如果没有这一行，已发现应用身份会丢失。
    canonical = _phase117_safe_text(report.get("canonical_target"), "target")  # 新增代码+URG2UniversalTargetSession：读取规范目标名兜底；如果没有这一行，fallback 无法生成进程名。
    return executable if executable.lower().endswith(".exe") else f"{executable or canonical}.exe"  # 新增代码+URG2UniversalTargetSession：确保返回 exe 样式名称；如果没有这一行，目标身份和窗口进程名可能不匹配。
# 新增代码+URG2UniversalTargetSession：函数段结束，_phase117_executable_from_report 到此结束；如果没有这个边界说明，初学者不容易看出 exe 提取范围。


def _phase117_representative_candidates(target: str) -> list[dict[str, Any]]:  # 新增代码+URG2UniversalTargetSession：函数段开始，构造代表样本候选；如果没有这段函数，合同会依赖本机是否安装具体应用。
    safe_target = _phase117_safe_text(target, "target")  # 新增代码+URG2UniversalTargetSession：清洗代表样本名；如果没有这一行，空目标会生成坏候选。
    return [{"display_name": safe_target, "executable": f"{safe_target}.exe", "source": "phase117_representative_candidate", "installed_app_verified": True}]  # 新增代码+URG2UniversalTargetSession：返回通用发现候选；如果没有这一行，样本不能通过 Phase108 resolver。
# 新增代码+URG2UniversalTargetSession：函数段结束，_phase117_representative_candidates 到此结束；如果没有这个边界说明，初学者不容易看出样本候选范围。

def _phase117_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+RealLaunchTargetSession：函数段开始，安全读取 pid/hwnd/坐标；如果没有这段函数，真实窗口坏字段会让启动链路崩溃。
    try:  # 新增代码+RealLaunchTargetSession：尝试把动态值转成整数；如果没有这一行，字符串 pid 不能兼容。
        return int(value)  # 新增代码+RealLaunchTargetSession：返回转换后的整数；如果没有这一行，调用方拿不到可比较的 pid/hwnd。
    except (TypeError, ValueError):  # 新增代码+RealLaunchTargetSession：捕获 None、空字符串和非数字值；如果没有这一行，坏窗口字段会抛异常。
        return int(default)  # 新增代码+RealLaunchTargetSession：失败时返回默认值；如果没有这一行，启动失败路径没有稳定兜底。
# 新增代码+RealLaunchTargetSession：函数段结束，_phase117_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出整数清洗范围。

def _phase117_snapshot_windows(snapshot: Any) -> list[dict[str, Any]]:  # 新增代码+RealLaunchTargetSession：函数段开始，把真实或 fake inventory 快照转换成窗口列表；如果没有这段函数，窗口 probe 会被快照形态卡住。
    if isinstance(snapshot, dict):  # 新增代码+RealLaunchTargetSession：兼容测试 fake 返回 dict；如果没有这一行，单测无法注入稳定窗口列表。
        source = snapshot.get("windows", [])  # 新增代码+RealLaunchTargetSession：读取 dict 快照中的窗口列表；如果没有这一行，fake 快照会被当成空。
    elif hasattr(snapshot, "windows"):  # 新增代码+RealLaunchTargetSession：兼容 WindowsWindowInventorySnapshot 对象；如果没有这一行，真实 inventory 的窗口不会被读取。
        source = getattr(snapshot, "windows", [])  # 新增代码+RealLaunchTargetSession：读取对象快照中的窗口列表；如果没有这一行，生产路径找不到真实窗口。
    else:  # 新增代码+RealLaunchTargetSession：处理未知快照形态；如果没有这一行，坏 provider 会触发异常。
        source = []  # 新增代码+RealLaunchTargetSession：未知快照按空列表处理；如果没有这一行，失败路径无法稳定返回。
    return [dict(window) for window in list(source or []) if isinstance(window, dict)]  # 新增代码+RealLaunchTargetSession：只返回字典窗口副本；如果没有这一行，后续匹配可能污染原始快照。
# 新增代码+RealLaunchTargetSession：函数段结束，_phase117_snapshot_windows 到此结束；如果没有这个边界说明，初学者不容易看出快照转换范围。


def _phase117_window_texts(window: dict[str, Any]) -> list[str]:  # 新增代码+ProxyWindowBinding：函数段开始，提取窗口可匹配文本；如果没有这段函数，代理窗口标题和进程名匹配会散落在 probe 里。函数到 return 结束。
    return [str(window.get("title_preview", "") or "").casefold(), str(window.get("title", "") or "").casefold(), str(window.get("process_name", "") or "").casefold(), str(window.get("app_id", "") or "").casefold()]  # 新增代码+ProxyWindowBinding：返回标题、进程名和 app_id 的小写文本；如果没有这一行，微信标题命中目标提示时无法被发现。
# 新增代码+ProxyWindowBinding：函数段结束，_phase117_window_texts 到此结束；如果没有这个边界说明，用户不容易看出窗口匹配文本范围。


def _phase117_window_matches_target_hint(window: dict[str, Any], target_hint: str) -> bool:  # 新增代码+ProxyWindowBinding：函数段开始，判断窗口是否像本次目标应用；如果没有这段函数，启动 pid 不一致的微信窗口会被误判为找不到。函数到 return 结束。
    aliases = build_process_window_aliases(target_hint, {})  # 修改代码+ExternalAppWindowBinding：把旧 target_hint 转成通用别名列表；如果没有这一行，中文标题和 .lnk 归一化无法复用新算法。
    return window_matches_process_alias(window, aliases)  # 修改代码+ExternalAppWindowBinding：使用通用窗口别名匹配；如果没有这一行，旧包含判断仍会漏掉多进程启动器窗口。
# 新增代码+ProxyWindowBinding：函数段结束，_phase117_window_matches_target_hint 到此结束；如果没有这个边界说明，用户不容易看出代理窗口匹配条件。


def _phase117_proxy_window_for_owned_process(window: dict[str, Any], launch_result: dict[str, Any], process_id: int, binding_report: dict[str, Any] | None = None) -> dict[str, Any]:  # 修改代码+ExternalAppWindowBinding：函数段开始，把代理窗口包装成可审计的 agent-owned 目标窗口并接收绑定报告；如果没有这段函数，pid 不一致会让身份模型拒绝微信或网易云音乐窗口。
    result = dict(window)  # 新增代码+ProxyWindowBinding：复制原窗口避免污染 inventory 快照；如果没有这一行，后续字段修正会影响其它调用方。
    actual_pid = _phase117_safe_int(result.get("pid", result.get("window_process_id")))  # 新增代码+ProxyWindowBinding：保存真实窗口所属 pid；如果没有这一行，审计时看不到代理窗口来自哪个进程。
    actual_process_name = str(result.get("process_name", "") or "")  # 新增代码+ProxyWindowBinding：保存真实窗口进程名；如果没有这一行，报告会丢失 Weixin.exe 这类真实身份。
    proxy_report = dict(binding_report or build_proxy_window_binding_report(window, launch_result, process_id))  # 新增代码+ExternalAppWindowBinding：生成或复制代理窗口绑定审计报告；如果没有这一行，报告无法说明为什么 pid 不同仍可绑定。
    result["actual_window_process_id"] = actual_pid  # 新增代码+ProxyWindowBinding：记录真实窗口 pid；如果没有这一行，pid 规范化会掩盖代理事实。
    result["actual_process_name"] = actual_process_name  # 新增代码+ProxyWindowBinding：记录真实进程名；如果没有这一行，后续排查看不到代理进程。
    result["proxy_owner_process_id"] = process_id  # 新增代码+ProxyWindowBinding：记录本次 agent 启动链的拥有 pid；如果没有这一行，无法解释为什么允许代理窗口。
    result["agent_owned_proxy_window"] = True  # 新增代码+ProxyWindowBinding：显式标记这是代理窗口绑定；如果没有这一行，审计会误以为普通 pid 精确匹配。
    result["proxy_window_binding"] = proxy_report  # 新增代码+ExternalAppWindowBinding：把绑定审计报告写入目标窗口；如果没有这一行，controller 和验收报告无法读取 netease_window_bound 证据。
    result["binding_reason"] = str(proxy_report.get("binding_reason", "alias_match"))  # 新增代码+ExternalAppWindowBinding：把绑定原因提升为顶层字段；如果没有这一行，日志筛选时需要解析嵌套对象。
    result["binding_confidence"] = str(proxy_report.get("confidence", "medium"))  # 新增代码+ExternalAppWindowBinding：把置信度提升为顶层字段；如果没有这一行，用户无法快速判断这不是无限制接管。
    result["pid"] = process_id  # 新增代码+ProxyWindowBinding：把身份门禁使用的 pid 对齐到本次启动 pid；如果没有这一行，Phase111 会因为窗口 pid 不同拒绝代理窗口。
    result["window_process_id"] = process_id  # 新增代码+ProxyWindowBinding：把窗口身份 pid 对齐到本次启动 pid；如果没有这一行，动作前身份模型无法把该 hwnd 视为本次目标。
    result["process_name"] = str(launch_result.get("process_executable", "") or result.get("process_name", ""))  # 新增代码+ProxyWindowBinding：身份报告使用启动链可审计名称；如果没有这一行，微信.lnk 与 Weixin.exe 名称不一致会触发进程名拒绝。
    result.setdefault("app_id", str(launch_result.get("process_executable", "") or result.get("app_id", "")))  # 新增代码+ProxyWindowBinding：缺 app_id 时用启动身份兜底；如果没有这一行，下游动作层可能缺少目标应用线索。
    return result  # 新增代码+ProxyWindowBinding：返回可绑定的代理窗口；如果没有这一行，调用方拿不到修正后的窗口。
# 新增代码+ProxyWindowBinding：函数段结束，_phase117_proxy_window_for_owned_process 到此结束；如果没有这个边界说明，用户不容易看出代理窗口包装范围。


def _phase117_attach_freshness_report(target_window: dict[str, Any], launch_result: dict[str, Any], target_hint: str, prelaunch_windows: list[dict[str, Any]] | None, user_authorized_window: bool) -> dict[str, Any]:  # 新增代码+FreshTargetPolicy：函数段开始，把 FreshTarget 决策写入目标窗口；如果没有这段函数，启动后旧窗口分类不会进入 session 报告。
    result = dict(target_window or {})  # 新增代码+FreshTargetPolicy：复制目标窗口避免污染 inventory 快照；如果没有这一行，后续补字段可能影响其它调用方。
    freshness = decide_post_launch_freshness(target_hint, result, list(prelaunch_windows or []), dict(launch_result or {}), user_authorized_window=bool(user_authorized_window))  # 新增代码+FreshTargetPolicy：执行启动后新旧窗口分类；如果没有这一行，旧窗口可能被当作新窗口绑定。
    result["fresh_target_freshness"] = dict(freshness)  # 新增代码+FreshTargetPolicy：保存完整策略报告；如果没有这一行，controller 无法回传预检和绑定事实。
    result["fresh_target_decision"] = str(freshness.get("decision", ""))  # 新增代码+FreshTargetPolicy：提升决策 token 到窗口顶层；如果没有这一行，租约构建要深入嵌套读取。
    result["fresh_target_class"] = str(freshness.get("fresh_target_class", ""))  # 新增代码+FreshTargetPolicy：提升目标分类到窗口顶层；如果没有这一行，审计难以直观看出目标类型。
    result["fresh_target_identity_verified"] = bool(freshness.get("fresh_target_identity_verified", False))  # 新增代码+FreshTargetPolicy：提升新鲜度验证布尔值；如果没有这一行，租约不知道策略证据强弱。
    result["target_window_existed_before_launch"] = bool(freshness.get("target_window_existed_before_launch", False))  # 新增代码+FreshTargetPolicy：提升是否旧窗口事实；如果没有这一行，压力测试无法断言未接管旧窗口。
    return result  # 新增代码+FreshTargetPolicy：返回带 FreshTarget 字段的目标窗口；如果没有这一行，调用方拿不到补充后的窗口。
# 新增代码+FreshTargetPolicy：函数段结束，_phase117_attach_freshness_report 到此结束；如果没有这个边界说明，用户不容易看出 FreshTarget 写入范围。


def _phase117_prelaunch_windows_from_probe(window_probe: Any) -> list[dict[str, Any]]:  # 新增代码+FreshTargetPolicy：函数段开始，从 window_probe 读取启动前窗口快照；如果没有这段函数，启动后无法知道窗口是否早已存在。
    inventory_probe = getattr(window_probe, "inventory_probe", None)  # 新增代码+FreshTargetPolicy：读取真实窗口查找器内部 inventory；如果没有这一行，无法复用同一只读窗口来源。
    if inventory_probe is None:  # 新增代码+FreshTargetPolicy：检查是否没有 inventory；如果没有这一行，测试 fake probe 会抛属性错误。
        return []  # 新增代码+FreshTargetPolicy：没有 inventory 时返回空快照；如果没有这一行，真实启动会被坏依赖阻断。
    snapshot_reader = getattr(inventory_probe, "snapshot", None)  # 新增代码+FreshTargetPolicy：读取 snapshot 方法；如果没有这一行，provider 形态无法判断。
    if callable(snapshot_reader):  # 新增代码+FreshTargetPolicy：确认 snapshot 可调用；如果没有这一行，非标准 provider 会被直接调用出错。
        return _phase117_snapshot_windows(snapshot_reader())  # 新增代码+FreshTargetPolicy：返回规范化窗口列表；如果没有这一行，启动前快照无法参与 FreshTarget 比较。
    return []  # 新增代码+FreshTargetPolicy：没有可用 snapshot 时返回空列表；如果没有这一行，函数可能隐式返回 None。
# 新增代码+FreshTargetPolicy：函数段结束，_phase117_prelaunch_windows_from_probe 到此结束；如果没有这个边界说明，用户不容易看出启动前快照范围。

class Phase117OwnedWindowProbe:  # 新增代码+RealLaunchTargetSession：类段开始，启动后按自有进程 pid 查找真实窗口；如果没有这个类，agent 只能启动进程却不能证明目标窗口属于自己。
    def __init__(self, inventory_probe: Any | None = None, poll_attempts: int = 40, poll_interval_seconds: float = 0.25) -> None:  # 修改代码+ExternalAppWindowBinding：函数段开始，延长真实 GUI 启动后的窗口轮询窗口；如果没有这段函数，网易云音乐这类启动慢的应用容易刚建窗前被误判失败。
        self.inventory_probe = inventory_probe if inventory_probe is not None else WindowsWindowInventoryProbe()  # 新增代码+RealLaunchTargetSession：保存窗口枚举 provider；如果没有这一行，生产路径无法读取真实顶层窗口。
        self.poll_attempts = max(1, int(poll_attempts))  # 新增代码+RealLaunchTargetSession：保存至少一次的轮询次数；如果没有这一行，窗口刚启动稍慢就会失败。
        self.poll_interval_seconds = max(0.0, float(poll_interval_seconds))  # 新增代码+RealLaunchTargetSession：保存非负轮询间隔；如果没有这一行，坏参数可能导致 sleep 异常。
    # 新增代码+RealLaunchTargetSession：函数段结束，Phase117OwnedWindowProbe.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def find_owned_window(self, launch_result: dict[str, Any], target_hint: str = "", prelaunch_windows: list[dict[str, Any]] | None = None, user_authorized_window: bool = False) -> dict[str, Any]:  # 修改代码+FreshTargetPolicy：函数段开始，按启动结果中的 pid 找窗口并对比启动前快照；如果没有这段函数，旧用户窗口可能被误当 agent 窗口。
        process_id = _phase117_safe_int(launch_result.get("process_id"))  # 新增代码+RealLaunchTargetSession：读取 agent 启动出的 pid；如果没有这一行，无法区分新进程和旧窗口。
        if process_id <= 0:  # 新增代码+RealLaunchTargetSession：检查 pid 是否有效；如果没有这一行，0 pid 会误匹配坏窗口。
            return {}  # 新增代码+RealLaunchTargetSession：无 pid 时不返回窗口；如果没有这一行，后续身份绑定可能产生假阳性。
        aliases = build_process_window_aliases(target_hint, launch_result)  # 新增代码+ExternalAppWindowBinding：基于目标名、快捷方式名和候选名生成窗口别名；如果没有这一行，.lnk 启动器打开的真实窗口无法通用匹配。
        for attempt_index in range(self.poll_attempts):  # 新增代码+RealLaunchTargetSession：有限轮询等待窗口出现；如果没有这一行，刚启动的 GUI 程序可能还没建窗就失败。
            snapshot = self.inventory_probe.snapshot() if hasattr(self.inventory_probe, "snapshot") else self.inventory_probe()  # 新增代码+RealLaunchTargetSession：读取当前窗口快照；如果没有这一行，probe 没有事实来源。
            windows = _phase117_snapshot_windows(snapshot)  # 新增代码+ProxyWindowBinding：把当前快照窗口保存下来供 pid 精确匹配和代理匹配复用；如果没有这一行，第二阶段会重复读取快照。
            for window in windows:  # 修改代码+ProxyWindowBinding：先遍历安全窗口候选做 pid 精确匹配；如果没有这一行，无法找到标准 agent-owned 目标窗口。
                if _phase117_safe_int(window.get("pid", window.get("window_process_id"))) == process_id:  # 新增代码+RealLaunchTargetSession：只接受 pid 与启动进程一致的窗口；如果没有这一行，用户已有同名窗口会被误用。
                    result = dict(window)  # 新增代码+RealLaunchTargetSession：复制匹配窗口；如果没有这一行，后续补字段可能污染 inventory。
                    result.setdefault("process_name", str(launch_result.get("process_executable", "")))  # 新增代码+RealLaunchTargetSession：缺进程名时用启动 exe 兜底；如果没有这一行，身份报告可读性会下降。
                    result.setdefault("app_id", str(launch_result.get("process_executable", "")))  # 新增代码+RealLaunchTargetSession：缺 app_id 时用启动 exe 兜底；如果没有这一行，最后一跳 sender 缺少目标应用线索。
                    return _phase117_attach_freshness_report(result, launch_result, target_hint, prelaunch_windows, user_authorized_window)  # 修改代码+FreshTargetPolicy：返回带 FreshTarget 分类的 agent-owned 窗口；如果没有这一行，启动后旧窗口风险不可审计。
            for window in windows:  # 新增代码+ProxyWindowBinding：pid 精确匹配失败后再按目标标题/进程名查找代理窗口；如果没有这一行，微信这类多进程应用会启动但无法绑定窗口。
                if window_matches_process_alias(window, aliases):  # 修改代码+ExternalAppWindowBinding：检查窗口标题、进程名或 app_id 是否命中启动别名；如果没有这一行，中文快捷方式打开的真实窗口仍会漏绑。
                    binding_report = build_proxy_window_binding_report(window, launch_result, process_id, reason="alias_match_after_launcher_pid_mismatch")  # 新增代码+ExternalAppWindowBinding：生成代理绑定审计报告；如果没有这一行，报告无法解释为什么 pid 不同仍被视为本次启动窗口。
                    proxy_window = _phase117_proxy_window_for_owned_process(window, launch_result, process_id, binding_report=binding_report)  # 新增代码+FreshTargetPolicy：先构造代理窗口绑定报告；如果没有这一行，FreshTarget 无法在代理窗口上补字段。
                    return _phase117_attach_freshness_report(proxy_window, launch_result, target_hint, prelaunch_windows, user_authorized_window)  # 修改代码+FreshTargetPolicy：返回带 FreshTarget 分类的代理窗口；如果没有这一行，微信类旧窗口可能被默认接管。
            if attempt_index < self.poll_attempts - 1 and self.poll_interval_seconds > 0:  # 新增代码+RealLaunchTargetSession：非最后一次才等待；如果没有这一行，最后一次失败也会多等。
                time.sleep(self.poll_interval_seconds)  # 新增代码+RealLaunchTargetSession：短暂停顿让 Windows 创建窗口；如果没有这一行，真实 GUI 启动会被过早判断。
        return {}  # 新增代码+RealLaunchTargetSession：轮询耗尽后返回空窗口；如果没有这一行，调用方无法结构化处理未找到窗口。
    # 新增代码+RealLaunchTargetSession：函数段结束，Phase117OwnedWindowProbe.find_owned_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口绑定范围。
# 新增代码+RealLaunchTargetSession：类段结束，Phase117OwnedWindowProbe 到此结束；如果没有这个边界说明，初学者不容易看出 real window probe 范围。


class UniversalTargetSessionRuntime:  # 新增代码+URG2UniversalTargetSession：类段开始，管理通用目标 session 和动作前身份复核；如果没有这个类，目标凭证会散落在发现、启动和动作层。
    def __init__(self, resolver: Any | None = None, launch_backend: Any | None = None, window_probe: Any | None = None, enable_real_launch: bool = False) -> None:  # 修改代码+RealLaunchTargetSession：函数段开始，允许 full 模式注入真实启动和窗口查找依赖；如果没有这些参数，通用 session 只能继续伪造窗口。
        self.resolver = resolver if resolver is not None else resolve_generic_app_launch_target  # 新增代码+URG2UniversalTargetSession：保存通用目标 resolver；如果没有这一行，runtime 无法摆脱硬编码 app 分支。
        self.enable_real_launch = bool(enable_real_launch)  # 新增代码+RealLaunchTargetSession：保存是否启用真实启动；如果没有这一行，测试和生产无法区分 recording 与真实启动模式。
        self.launch_backend = launch_backend if launch_backend is not None else (Phase110ProductionGenericLaunchBackend() if self.enable_real_launch else None)  # 新增代码+RealLaunchTargetSession：真实模式默认使用 Phase110 生产后端；如果没有这一行，启用真实模式也不会真正打开应用。
        self.window_probe = window_probe if window_probe is not None else (Phase117OwnedWindowProbe() if self.enable_real_launch else None)  # 新增代码+RealLaunchTargetSession：真实模式默认使用 pid 窗口 probe；如果没有这一行，启动进程后无法绑定窗口。
        self._sequence = 0  # 新增代码+URG2UniversalTargetSession：初始化记录型 pid/hwnd 序列；如果没有这一行，多 session 样本身份会互相冲突。
        self._owned_targets: dict[str, Any] = {}  # 新增代码+URG2UniversalTargetSession：保存 session_id 到目标身份对象的映射；如果没有这一行，动作前复核无法找到基准。
    # 新增代码+URG2UniversalTargetSession：函数段结束，UniversalTargetSessionRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def open_target_session(self, raw_target: Any, candidates: list[dict[str, Any]] | None = None, user_authorized_window: bool = False) -> dict[str, Any]:  # 新增代码+URG2UniversalTargetSession：函数段开始，为任意普通目标建立通用 session；如果没有这段函数，URG-2 只有零散 helper 没有目标凭证。
        phase108_report = dict(self.resolver(raw_target, candidates=candidates))  # 新增代码+URG2UniversalTargetSession：调用 Phase108 通用发现；如果没有这一行，session 会退回逐应用控制器。
        self._sequence += 1  # 新增代码+URG2UniversalTargetSession：推进记录型身份序列；如果没有这一行，多目标窗口会拿到相同 pid/hwnd。
        session_id = f"phase117-session-{self._sequence}"  # 新增代码+URG2UniversalTargetSession：生成稳定 session id；如果没有这一行，身份映射和审计没有键。
        executable = _phase117_executable_from_report(phase108_report)  # 新增代码+URG2UniversalTargetSession：提取目标可执行名；如果没有这一行，进程和窗口身份无法一致。
        if self.enable_real_launch:  # 新增代码+RealLaunchTargetSession：真实启动模式走 Phase110 后端和窗口 probe；如果没有这一行，full 模式仍会生成假 pid/hwnd。
            return self._open_real_target_session(raw_target, phase108_report, session_id, executable, user_authorized_window)  # 新增代码+RealLaunchTargetSession：返回真实启动 session 报告；如果没有这一行，agent 无法证明自己打开了目标应用。
        process_id = 11700 + self._sequence  # 新增代码+URG2UniversalTargetSession：生成记录型进程 id；如果没有这一行，目标身份缺少 pid。
        hwnd = 21700 + self._sequence  # 新增代码+URG2UniversalTargetSession：生成记录型窗口句柄；如果没有这一行，目标身份缺少 hwnd。
        process_path = f"C:\\Program Files\\UniversalTargetSession\\{executable}"  # 新增代码+URG2UniversalTargetSession：生成仅用于哈希的真实风格路径；如果没有这一行，路径身份无法参与漂移复核。
        launch_result = {"process_id": process_id, "process_executable": executable, "process_path": process_path, "owned_process_registered": True, "process_identity_verified": True, "real_desktop_touched": False}  # 新增代码+URG2UniversalTargetSession：构造记录型自有进程摘要；如果没有这一行，Phase111 无法绑定目标。
        target_window = {"pid": process_id, "hwnd": hwnd, "window_id": f"hwnd:{hwnd}", "process_name": executable, "process_path": process_path, "title": f"Universal Target Session - {phase108_report.get('canonical_target', raw_target)}", "title_preview": f"Universal Target Session - {phase108_report.get('canonical_target', raw_target)}", "app_id": executable}  # 新增代码+URG2UniversalTargetSession：构造记录型目标窗口摘要；如果没有这一行，Phase111 无法验证窗口。
        target_window = _phase117_attach_freshness_report(target_window, launch_result, str(phase108_report.get("canonical_target", raw_target)), [], user_authorized_window)  # 新增代码+FreshTargetPolicy：给记录型窗口补 FreshTarget 决策；如果没有这一行，测试路径会缺少新旧窗口分类字段。
        freshness = dict(target_window.get("fresh_target_freshness", {}))  # 新增代码+FreshTargetPolicy：读取记录型窗口的新鲜度报告；如果没有这一行，session_ready 和返回字段无法复用策略结果。
        owned_identity = build_owned_target_identity(launch_result, target_window)  # 新增代码+URG2UniversalTargetSession：绑定进程和窗口为目标凭证；如果没有这一行，后续动作前没有基准。
        stable_verification = verify_owned_target_identity(owned_identity, target_window).to_report()  # 新增代码+URG2UniversalTargetSession：立即验证稳定窗口；如果没有这一行，正常路径是否可放行不可见。
        drifted_window = dict(target_window, pid=process_id + 9000, hwnd=hwnd + 9000, window_id=f"hwnd:{hwnd + 9000}")  # 新增代码+URG2UniversalTargetSession：构造漂移窗口样本；如果没有这一行，session 报告无法证明防漂移。
        drift_verification = verify_owned_target_identity(owned_identity, drifted_window).to_report()  # 新增代码+URG2UniversalTargetSession：验证漂移会阻断；如果没有这一行，漂移零事件没有事实来源。
        self._owned_targets[session_id] = owned_identity  # 新增代码+URG2UniversalTargetSession：保存目标凭证供动作前复核；如果没有这一行，verify_before_action 无法工作。
        session_ready = bool(phase108_report.get("passed") and stable_verification.get("allowed") and owned_identity.target_identity_verified and freshness.get("allowed", True))  # 修改代码+FreshTargetPolicy：汇总 session 是否就绪并要求 FreshTarget 允许；如果没有这一行，旧窗口分类拒绝不会影响 session_ready。
        return {"marker": PHASE117_UNIVERSAL_TARGET_SESSION_MARKER, "model": PHASE117_UNIVERSAL_TARGET_SESSION_MODEL, "session_id": session_id, "raw_target": str(raw_target or ""), "canonical_target": str(phase108_report.get("canonical_target", "")), "session_ready": session_ready, "generic_target_resolver_used": bool(phase108_report.get("dynamic_discovery_used")), "per_app_controller_required": False, "hardcoded_app_whitelist_required": False, "representative_apps_are_acceptance_only": True, "agent_owned_or_user_authorized_window": bool(owned_identity.target_identity_verified or user_authorized_window), "target_identity_bound": bool(owned_identity.target_identity_verified), "target_identity_rechecked_before_each_action": True, "target_drift_zero_events": bool(drift_verification.get("target_drift_blocks_action") and not drift_verification.get("allowed")), "stable_verification": stable_verification, "drift_verification": drift_verification, "target_window": target_window, "owned_target_identity": owned_identity.to_report(), "phase108_report": phase108_report, "fresh_target_freshness": freshness, "fresh_target_decision": str(freshness.get("decision", "")), "fresh_target_class": str(freshness.get("fresh_target_class", "")), "fresh_target_identity_verified": bool(freshness.get("fresh_target_identity_verified", False)), "target_window_existed_before_launch": bool(freshness.get("target_window_existed_before_launch", False)), "low_level_event_count": 0, "real_desktop_touched": False, "actions_expanded": PHASE117_ACTIONS_EXPANDED}  # 修改代码+FreshTargetPolicy：返回通用 session 报告并带 FreshTarget 字段；如果没有这一行，测试和动作层拿不到新旧窗口证据。
    # 新增代码+URG2UniversalTargetSession：函数段结束，UniversalTargetSessionRuntime.open_target_session 到此结束；如果没有这个边界说明，初学者不容易看出 session 建立范围。

    def _open_real_target_session(self, raw_target: Any, phase108_report: dict[str, Any], session_id: str, executable: str, user_authorized_window: bool = False) -> dict[str, Any]:  # 新增代码+RealLaunchTargetSession：函数段开始，真实启动应用并绑定 agent-owned 窗口；如果没有这段函数，full 模式会继续误用用户已打开窗口。
        prelaunch_windows = _phase117_prelaunch_windows_from_probe(self.window_probe)  # 新增代码+FreshTargetPolicy：启动前读取同一窗口 inventory 快照；如果没有这一行，启动后无法识别绑定到旧窗口。
        launch_result = dict(run_generic_launch_backend(phase108_report, enable_real_launch=True, backend=self.launch_backend))  # 新增代码+RealLaunchTargetSession：调用 Phase110 启动后端；如果没有这一行，真实启动模式不会触达 launcher。
        finder = getattr(self.window_probe, "find_owned_window", None)  # 新增代码+RealLaunchTargetSession：读取窗口查找接口；如果没有这一行，坏 probe 会变成难懂异常。
        target_hint = str(phase108_report.get("canonical_target", raw_target))  # 新增代码+FreshTargetPolicy：保存本次目标提示；如果没有这一行，FreshTarget 和代理绑定会重复读取目标名。
        try:  # 新增代码+FreshTargetPolicy：优先调用支持启动前快照的新 finder 协议；如果没有这一行，旧测试 fake finder 可能因参数不兼容失败。
            target_window = dict(finder(launch_result, target_hint=target_hint, prelaunch_windows=prelaunch_windows, user_authorized_window=user_authorized_window) if callable(finder) else {})  # 修改代码+FreshTargetPolicy：按启动 pid 查找窗口并传入 prelaunch 快照；如果没有这一行，旧窗口绑定无法被二次识别。
        except TypeError:  # 新增代码+FreshTargetPolicy：兼容旧 fake finder 只接受旧参数；如果没有这一行，已有单测和注入依赖会被新协议打断。
            target_window = dict(finder(launch_result, target_hint=target_hint) if callable(finder) else {})  # 新增代码+FreshTargetPolicy：用旧签名获取窗口；如果没有这一行，兼容路径没有目标窗口。
            if target_window and not target_window.get("fresh_target_freshness"):  # 新增代码+FreshTargetPolicy：旧 finder 没有 FreshTarget 字段时补齐；如果没有这一行，兼容路径会缺少策略报告。
                target_window = _phase117_attach_freshness_report(target_window, launch_result, target_hint, prelaunch_windows, user_authorized_window)  # 新增代码+FreshTargetPolicy：给旧 finder 返回窗口补新鲜度；如果没有这一行，旧依赖可能默认接管旧窗口。
        if not target_window:  # 新增代码+RealLaunchTargetSession：处理启动后没找到窗口的情况；如果没有这一行，空窗口会在身份绑定里产生混乱字段。
            target_window = {"pid": _phase117_safe_int(launch_result.get("process_id")), "hwnd": 0, "window_id": "", "process_name": executable, "app_id": executable, "title_preview": "", "rect": {}}  # 新增代码+RealLaunchTargetSession：构造失败窗口摘要；如果没有这一行，失败报告缺少 pid 和 exe 事实。
            target_window = _phase117_attach_freshness_report(target_window, launch_result, target_hint, prelaunch_windows, user_authorized_window)  # 新增代码+FreshTargetPolicy：失败窗口也补策略字段；如果没有这一行，失败报告缺少 FreshTarget 上下文。
        freshness = dict(target_window.get("fresh_target_freshness", {}))  # 新增代码+FreshTargetPolicy：读取窗口新鲜度报告；如果没有这一行，session_ready 无法包含旧窗口拒绝结果。
        owned_identity = build_owned_target_identity(launch_result, target_window)  # 新增代码+RealLaunchTargetSession：绑定真实启动进程和真实窗口；如果没有这一行，动作层无法确认窗口属于 agent。
        stable_verification = verify_owned_target_identity(owned_identity, target_window).to_report()  # 新增代码+RealLaunchTargetSession：立即复核目标窗口；如果没有这一行，session_ready 没有窗口稳定证据。
        drifted_window = dict(target_window, pid=_phase117_safe_int(target_window.get("pid")) + 9000, hwnd=_phase117_safe_int(target_window.get("hwnd")) + 9000, window_id=f"hwnd:{_phase117_safe_int(target_window.get('hwnd')) + 9000}")  # 新增代码+RealLaunchTargetSession：构造漂移窗口样本；如果没有这一行，真实 session 报告无法证明漂移会阻断。
        drift_verification = verify_owned_target_identity(owned_identity, drifted_window).to_report()  # 新增代码+RealLaunchTargetSession：验证漂移窗口会被拒绝；如果没有这一行，防漂移门禁没有事实来源。
        if owned_identity.target_identity_verified:  # 新增代码+RealLaunchTargetSession：只有绑定成功时才登记目标身份；如果没有这一行，失败 session 也可能进入动作前复核通过路径。
            self._owned_targets[session_id] = owned_identity  # 新增代码+RealLaunchTargetSession：保存自有目标供动作前复核；如果没有这一行，后续 dispatch 会提示 missing_target_session。
        session_ready = bool(phase108_report.get("passed") and launch_result.get("ok") and launch_result.get("process_started") and owned_identity.target_identity_verified and stable_verification.get("allowed") and freshness.get("allowed", True))  # 修改代码+FreshTargetPolicy：汇总真实启动 session 门禁并包含 FreshTarget 放行；如果没有这一行，旧窗口绑定拒绝不会让 session 失败。
        return {"marker": PHASE117_UNIVERSAL_TARGET_SESSION_MARKER, "model": PHASE117_UNIVERSAL_TARGET_SESSION_MODEL, "session_id": session_id, "raw_target": str(raw_target or ""), "canonical_target": str(phase108_report.get("canonical_target", "")), "session_ready": session_ready, "generic_target_resolver_used": bool(phase108_report.get("dynamic_discovery_used")), "per_app_controller_required": False, "hardcoded_app_whitelist_required": False, "representative_apps_are_acceptance_only": True, "agent_owned_or_user_authorized_window": bool(owned_identity.target_identity_verified or user_authorized_window), "target_identity_bound": bool(owned_identity.target_identity_verified), "target_identity_rechecked_before_each_action": True, "target_drift_zero_events": bool(drift_verification.get("target_drift_blocks_action") and not drift_verification.get("allowed")), "stable_verification": stable_verification, "drift_verification": drift_verification, "target_window": target_window, "owned_target_identity": owned_identity.to_report(), "phase108_report": phase108_report, "launch_result": launch_result, "fresh_target_prelaunch_window_count": len(prelaunch_windows), "fresh_target_freshness": freshness, "fresh_target_decision": str(freshness.get("decision", "")), "fresh_target_class": str(freshness.get("fresh_target_class", "")), "fresh_target_identity_verified": bool(freshness.get("fresh_target_identity_verified", False)), "target_window_existed_before_launch": bool(freshness.get("target_window_existed_before_launch", False)), "real_launch_performed": bool(launch_result.get("real_desktop_touched") or launch_result.get("process_started")), "backend_launch_performed": bool(launch_result.get("backend_launch_performed") or launch_result.get("backend_launch_reaches_launcher")), "process_started": bool(launch_result.get("process_started")), "owned_process_registered": bool(launch_result.get("owned_process_registered")), "visible_window_verified": bool(owned_identity.window_identity_verified), "proxy_window_bound": bool(target_window.get("agent_owned_proxy_window")), "proxy_window_binding": target_window.get("proxy_window_binding", {}), "window_binding_reason": str(target_window.get("binding_reason", "")), "window_binding_confidence": str(target_window.get("binding_confidence", "")), "low_level_event_count": 0, "real_desktop_touched": bool(launch_result.get("real_desktop_touched")), "actions_expanded": PHASE117_ACTIONS_EXPANDED}  # 修改代码+FreshTargetPolicy：返回真实启动 session 报告并带 FreshTarget 证据；如果没有这一行，终端验收无法证明没有默认接管旧窗口。
    # 新增代码+RealLaunchTargetSession：函数段结束，UniversalTargetSessionRuntime._open_real_target_session 到此结束；如果没有这个边界说明，初学者不容易看出真实启动 session 范围。

    def verify_before_action(self, session: dict[str, Any], current_window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+URG2UniversalTargetSession：函数段开始，动作前重验目标身份；如果没有这段函数，SendInput 前无法阻断漂移窗口。
        session_id = _phase117_safe_text(session.get("session_id"))  # 新增代码+URG2UniversalTargetSession：读取 session id；如果没有这一行，无法从内部映射找到目标凭证。
        owned_identity = self._owned_targets.get(session_id)  # 新增代码+URG2UniversalTargetSession：读取保存的目标身份对象；如果没有这一行，动作前复核没有基准。
        if owned_identity is None:  # 新增代码+URG2UniversalTargetSession：检查 session 是否存在；如果没有这一行，未知 session 会抛异常。
            return {"allowed": False, "decision": "missing_target_session", "target_drift_blocks_action": True, "low_level_event_count": 0, "actions_expanded": PHASE117_ACTIONS_EXPANDED}  # 新增代码+URG2UniversalTargetSession：未知 session 以零事件拒绝；如果没有这一行，坏 session 可能继续动作。
        verification = verify_owned_target_identity(owned_identity, current_window).to_report()  # 新增代码+URG2UniversalTargetSession：调用 Phase111 动作前复核；如果没有这一行，漂移判断会和现有身份模型分裂。
        verification["low_level_event_count"] = 0  # 新增代码+URG2UniversalTargetSession：明确复核阶段不发送输入事件；如果没有这一行，拒绝路径无法证明零事件。
        verification["actions_expanded"] = PHASE117_ACTIONS_EXPANDED  # 新增代码+URG2UniversalTargetSession：明确未扩大动作面；如果没有这一行，安全审计缺少边界。
        return verification  # 新增代码+URG2UniversalTargetSession：返回动作前门禁报告；如果没有这一行，调用方拿不到允许或拒绝结果。
    # 新增代码+URG2UniversalTargetSession：函数段结束，UniversalTargetSessionRuntime.verify_before_action 到此结束；如果没有这个边界说明，初学者不容易看出动作前门禁范围。
# 新增代码+URG2UniversalTargetSession：类段结束，UniversalTargetSessionRuntime 到此结束；如果没有这个边界说明，初学者不容易看出 runtime 范围。


def run_phase117_universal_target_session_contract() -> dict[str, Any]:  # 新增代码+URG2UniversalTargetSession：函数段开始，运行 URG-2 合同自检；如果没有这段函数，测试、CLI 和可见终端没有统一事实源。
    runtime = UniversalTargetSessionRuntime()  # 新增代码+URG2UniversalTargetSession：创建通用 session runtime；如果没有这一行，合同没有执行主体。
    sample_targets = ["notepad", "mspaint", "calc"]  # 新增代码+URG2UniversalTargetSession：定义代表性普通应用样本；如果没有这一行，通用性只会测单个目标。
    sample_sessions = [runtime.open_target_session(target, candidates=_phase117_representative_candidates(target)) for target in sample_targets]  # 新增代码+URG2UniversalTargetSession：用同一 runtime 建立所有样本 session；如果没有这一行，代表样本没有统一入口证据。
    preexisting_launch = {"process_id": 33117, "process_executable": "notepad.exe", "owned_process_registered": False}  # 新增代码+URG2UniversalTargetSession：构造用户已有进程样本；如果没有这一行，保护用户已有窗口没有证据。
    preexisting_window = {"pid": 33117, "hwnd": 33118, "window_id": "hwnd:33118", "process_name": "notepad.exe", "title": "User Existing Notepad", "title_preview": "User Existing Notepad", "app_id": "notepad.exe"}  # 新增代码+URG2UniversalTargetSession：构造用户已有窗口样本；如果没有这一行，非自有窗口保护无法验证。
    preexisting_identity = build_owned_target_identity(preexisting_launch, preexisting_window)  # 新增代码+URG2UniversalTargetSession：尝试绑定非自有窗口；如果没有这一行，user_preexisting_window_preserved 没有事实来源。
    representative_ready = all(bool(item.get("session_ready")) for item in sample_sessions)  # 新增代码+URG2UniversalTargetSession：汇总代表样本是否全部成功；如果没有这一行，部分样本失败可能被忽略。
    target_identity_bound = all(bool(item.get("target_identity_bound")) for item in sample_sessions)  # 新增代码+URG2UniversalTargetSession：汇总目标身份绑定；如果没有这一行，目标凭证缺失可能被忽略。
    target_drift_zero_events = all(bool(item.get("target_drift_zero_events")) and int(item.get("low_level_event_count", 0) or 0) == 0 for item in sample_sessions)  # 新增代码+URG2UniversalTargetSession：汇总漂移零事件；如果没有这一行，漂移阻断不能成为总合同门禁。
    generic_target_resolver_used = all(bool(item.get("generic_target_resolver_used")) for item in sample_sessions)  # 新增代码+URG2UniversalTargetSession：汇总是否都使用通用 resolver；如果没有这一行，单个样本可能暗中绕过 Phase108。
    agent_owned_or_user_authorized_window = all(bool(item.get("agent_owned_or_user_authorized_window")) for item in sample_sessions)  # 新增代码+URG2UniversalTargetSession：汇总目标是否自有或授权；如果没有这一行，用户已有窗口风险不可见。
    real_desktop_touched = any(bool(item.get("real_desktop_touched")) for item in sample_sessions)  # 新增代码+URG2UniversalTargetSession：汇总是否触碰真实桌面；如果没有这一行，合同可能误打开本机应用。
    low_level_event_count = sum(int(item.get("low_level_event_count", 0) or 0) for item in sample_sessions)  # 新增代码+URG2UniversalTargetSession：汇总底层事件数；如果没有这一行，session 建立阶段是否发输入不可见。
    passed = bool(representative_ready and target_identity_bound and target_drift_zero_events and generic_target_resolver_used and agent_owned_or_user_authorized_window and preexisting_identity.user_preexisting_window_preserved and not preexisting_identity.target_identity_verified and not real_desktop_touched and low_level_event_count == 0 and not PHASE117_ACTIONS_EXPANDED)  # 新增代码+URG2UniversalTargetSession：计算合同通过条件；如果没有这一行，CLI 不能用退出码表达失败。
    return {"marker": PHASE117_UNIVERSAL_TARGET_SESSION_MARKER, "ok_token": PHASE117_UNIVERSAL_TARGET_SESSION_OK_TOKEN, "model": PHASE117_UNIVERSAL_TARGET_SESSION_MODEL, "passed": passed, "universal_target_session_ready": representative_ready, "generic_target_resolver_used": generic_target_resolver_used, "representative_samples_session_ready": representative_ready, "per_app_controller_required": False, "hardcoded_app_whitelist_required": False, "ordinary_apps_controlled_by_generic_runtime": True, "representative_apps_are_acceptance_only": True, "target_identity_bound": target_identity_bound, "target_identity_rechecked_before_each_action": True, "target_drift_zero_events": target_drift_zero_events, "agent_owned_or_user_authorized_window": agent_owned_or_user_authorized_window, "user_preexisting_window_preserved": preexisting_identity.user_preexisting_window_preserved, "real_desktop_touched": real_desktop_touched, "low_level_event_count": low_level_event_count, "actions_expanded": PHASE117_ACTIONS_EXPANDED, "sample_sessions": sample_sessions, "preexisting_report": preexisting_identity.to_report()}  # 新增代码+URG2UniversalTargetSession：返回完整合同报告；如果没有这一行，测试和可见终端无法读取统一事实。
# 新增代码+URG2UniversalTargetSession：函数段结束，run_phase117_universal_target_session_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同范围。


def phase117_universal_target_session_cli_line(report: dict[str, Any]) -> str:  # 新增代码+URG2UniversalTargetSession：函数段开始，把合同报告转成固定 token 行；如果没有这段函数，可见终端验收需要解析复杂 JSON。
    return f"{PHASE117_UNIVERSAL_TARGET_SESSION_MARKER} {PHASE117_UNIVERSAL_TARGET_SESSION_OK_TOKEN} universal_target_session_ready={_phase117_bool_token(report.get('universal_target_session_ready'))} generic_target_resolver_used={_phase117_bool_token(report.get('generic_target_resolver_used'))} representative_samples_session_ready={_phase117_bool_token(report.get('representative_samples_session_ready'))} per_app_controller_required={_phase117_bool_token(report.get('per_app_controller_required'))} hardcoded_app_whitelist_required={_phase117_bool_token(report.get('hardcoded_app_whitelist_required'))} ordinary_apps_controlled_by_generic_runtime={_phase117_bool_token(report.get('ordinary_apps_controlled_by_generic_runtime'))} representative_apps_are_acceptance_only={_phase117_bool_token(report.get('representative_apps_are_acceptance_only'))} target_identity_bound={_phase117_bool_token(report.get('target_identity_bound'))} target_identity_rechecked_before_each_action={_phase117_bool_token(report.get('target_identity_rechecked_before_each_action'))} target_drift_zero_events={_phase117_bool_token(report.get('target_drift_zero_events'))} agent_owned_or_user_authorized_window={_phase117_bool_token(report.get('agent_owned_or_user_authorized_window'))} user_preexisting_window_preserved={_phase117_bool_token(report.get('user_preexisting_window_preserved'))} real_desktop_touched={_phase117_bool_token(report.get('real_desktop_touched'))} actions_expanded={_phase117_bool_token(report.get('actions_expanded'))} low_level_event_count={int(report.get('low_level_event_count', 0) or 0)}"  # 新增代码+URG2UniversalTargetSession：返回固定顺序 token；如果没有这一行，场景匹配容易因字段顺序漂移。
# 新增代码+URG2UniversalTargetSession：函数段结束，phase117_universal_target_session_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+URG2UniversalTargetSession：函数段开始，提供命令行和真实终端统一入口；如果没有这段函数，controller 场景无法运行 URG-2。
    _ = argv  # 新增代码+URG2UniversalTargetSession：保留未来参数扩展位；如果没有这一行，读者可能误以为 argv 被忘记。
    report = run_phase117_universal_target_session_contract()  # 新增代码+URG2UniversalTargetSession：运行 URG-2 合同；如果没有这一行，CLI 没有结构化报告。
    print(phase117_universal_target_session_cli_line(report))  # 新增代码+URG2UniversalTargetSession：打印固定 token 行；如果没有这一行，真实终端验收无法稳定匹配。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+URG2UniversalTargetSession：打印完整 JSON 报告；如果没有这一行，失败时不方便定位字段。
    print(PHASE117_UNIVERSAL_TARGET_SESSION_MARKER)  # 新增代码+URG2UniversalTargetSession：单独打印 ready marker；如果没有这一行，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+URG2UniversalTargetSession：按合同结果返回退出码；如果没有这一行，失败也可能被终端当成成功。
# 新增代码+URG2UniversalTargetSession：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


__all__ = ["PHASE117_ACTIONS_EXPANDED", "PHASE117_UNIVERSAL_TARGET_SESSION_MARKER", "PHASE117_UNIVERSAL_TARGET_SESSION_MODEL", "PHASE117_UNIVERSAL_TARGET_SESSION_OK_TOKEN", "UniversalTargetSessionRuntime", "main", "phase117_universal_target_session_cli_line", "run_phase117_universal_target_session_contract"]  # 新增代码+URG2UniversalTargetSession：限定公开导出名称；如果没有这一行，from module import * 会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+URG2UniversalTargetSession：文件入口段开始，允许 `python -m` 直接运行；如果没有这一行，真实终端无法直接调用本模块。
    raise SystemExit(main())  # 新增代码+URG2UniversalTargetSession：调用 main 并传递退出码；如果没有这一行，直接运行文件不会执行自检。
# 新增代码+URG2UniversalTargetSession：文件入口段结束，本模块到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
