"""Windows 真实应用 Computer Use 安全边界合同层。"""  # 新增代码+Phase72RealAppSafetyBoundary: 标明本文件负责 Phase72 真实应用安全边界；如果没有这行代码，读者不知道普通应用放行和危险窗口拒绝集中在哪里。
from __future__ import annotations  # 新增代码+Phase72RealAppSafetyBoundary: 启用延迟类型解析；如果没有这行代码，类型注解在旧导入顺序下更容易失败。

import json  # 新增代码+Phase72RealAppSafetyBoundary: 导入 JSON 用于 CLI 输出结构化报告；如果没有这行代码，真实终端失败时不易复盘。
import time  # 新增代码+Phase72RealAppSafetyBoundary: 导入时间用于生成合同隔离目录；如果没有这行代码，多次自检目录可能互相覆盖。
from pathlib import Path  # 新增代码+Phase72RealAppSafetyBoundary: 导入 Path 统一处理 Windows 路径；如果没有这行代码，状态目录拼接会更脆弱。
from typing import Any  # 新增代码+Phase72RealAppSafetyBoundary: 导入 Any 描述窗口快照和授权报告；如果没有这行代码，接口边界不清楚。

try:  # 新增代码+Phase72RealAppSafetyBoundary: 优先按包路径导入 Phase60 授权 store；如果没有这段代码，正常包运行无法复用持久授权。
    from learning_agent.computer_use.persistent_grants import DEFAULT_PERSISTENT_GRANT_SESSION_ID, DEFAULT_PERSISTENT_GRANTS_ROOT, WindowsComputerUsePersistentGrantStore  # 新增代码+Phase72RealAppSafetyBoundary: 导入持久授权事实源；如果没有这行代码，安全边界只能凭窗口字段猜测是否允许。
except ModuleNotFoundError as error:  # 新增代码+Phase72RealAppSafetyBoundary: 兼容 start_oauth_agent.bat 脚本模式导入；如果没有这段代码，直接脚本运行可能找不到 learning_agent 包名。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.persistent_grants"}:  # 新增代码+Phase72RealAppSafetyBoundary: 只对包路径缺失做 fallback；如果没有这行代码，真实内部错误会被误吞。
        raise  # 新增代码+Phase72RealAppSafetyBoundary: 重新抛出非路径类导入错误；如果没有这行代码，底层 bug 会被隐藏。
    from computer_use.persistent_grants import DEFAULT_PERSISTENT_GRANT_SESSION_ID, DEFAULT_PERSISTENT_GRANTS_ROOT, WindowsComputerUsePersistentGrantStore  # 新增代码+Phase72RealAppSafetyBoundary: 脚本模式导入持久授权 store；如果没有这行代码，bat 入口无法运行 Phase72 自检。

PHASE72_REAL_APP_SAFETY_BOUNDARY_MARKER = "PHASE72_REAL_APP_SAFETY_BOUNDARY_READY"  # 新增代码+Phase72RealAppSafetyBoundary: 定义 Phase72 ready marker；如果没有这行代码，真实终端验收没有稳定锚点。
PHASE72_REAL_APP_SAFETY_BOUNDARY_OK_TOKEN = "PHASE72_REAL_APP_SAFETY_BOUNDARY_OK"  # 新增代码+Phase72RealAppSafetyBoundary: 定义 Phase72 OK token；如果没有这行代码，debug log 无法区分自检通过和普通输出。
PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL = "phase72_windows_real_app_safety_boundary"  # 新增代码+Phase72RealAppSafetyBoundary: 定义安全边界模型名；如果没有这行代码，状态和报告无法说明当前合同版本。
PHASE72_CONTROLLED_ACTIONS_EXPANSION = True  # 新增代码+Phase72RealAppSafetyBoundary: 声明本阶段允许受控扩展普通真实应用动作；如果没有这行代码，Phase72 的能力提升边界不可见。
PHASE72_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase72RealAppSafetyBoundary: 声明本阶段不扩大无授权、无边界动作；如果没有这行代码，用户可能误以为任意窗口可控。
DEFAULT_PHASE72_REAL_APP_SAFETY_BOUNDARY_ROOT = DEFAULT_PERSISTENT_GRANTS_ROOT.parent / "real_app_safety_boundary"  # 新增代码+Phase72RealAppSafetyBoundary: 定义 Phase72 默认状态根目录；如果没有这行代码，合同运行没有稳定落点。

PHASE72_ACTION_ALIASES = {"click_control": "click", "click_by_query": "click", "click_by_visual_point": "click", "click": "click", "type_into_control": "type_text", "type_by_query": "type_text", "type_text": "type_text", "type": "type_text", "scroll_at": "scroll", "scroll": "scroll", "drag_path": "drag", "drag": "drag", "menu_navigation": "click", "open_menu": "click", "select_menu_item": "click"}  # 新增代码+Phase72RealAppSafetyBoundary: 定义高层动作到 Phase60 授权 scope 的映射；如果没有这行代码，高层动作名会和持久授权 scope 对不上。
PHASE72_TERMINAL_PROCESS_TOKENS = {"cmd.exe", "powershell.exe", "pwsh.exe", "wt.exe", "windowsterminal.exe", "terminal.exe", "conhost.exe"}  # 新增代码+Phase72RealAppSafetyBoundary: 定义终端进程黑名单；如果没有这行代码，agent 可能向 shell 发送真实输入。
PHASE72_CODEX_PROCESS_TOKENS = {"codex.exe", "codex", "openai codex"}  # 新增代码+Phase72RealAppSafetyBoundary: 定义 Codex 自身窗口黑名单；如果没有这行代码，agent 可能误控自己的控制台或调试 UI。
PHASE72_HIGH_RISK_TEXT_TOKENS = {"password", "credential", "captcha", "payment", "credit card", "bank", "login", "sign in", "authentication", "verification", "two-factor", "2fa", "otp", "admin", "administrator", "security", "defender", "firewall", "private", "secret", "api key", "access token", "recovery key", "bitlocker", "registry editor", "regedit", "task manager", "windows run", "run dialog"}  # 新增代码+Phase72RealAppSafetyBoundary: 定义标题/文本高风险关键词；如果没有这行代码，密码、支付、系统安全窗口可能被普通动作误控。
PHASE72_SYSTEM_PROCESS_TOKENS = {"regedit.exe", "taskmgr.exe", "mmc.exe", "control.exe", "systemsettings.exe", "secpol.msc", "gpedit.msc"}  # 新增代码+Phase72RealAppSafetyBoundary: 定义系统管理进程黑名单；如果没有这行代码，系统设置和管理工具可能被自动化误改。
PHASE72_BYPASS_KEYS = {"approval_bypass", "force_allowed", "force_execute", "unsafe_override", "already_approved"}  # 新增代码+Phase72RealAppSafetyBoundary: 定义不可信绕过字段名；如果没有这行代码，伪造窗口字段可能绕过持久授权。


def _phase72_bool_token(value: Any) -> str:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会出现 True/False 漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase72RealAppSafetyBoundary: 返回 true/false 文本；如果没有这行代码，验收场景匹配不稳定。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_phase72_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式范围。


def _phase72_safe_text(value: Any, limit: int = 240) -> str:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，把任意输入压成安全短文本；如果没有这段函数，窗口标题和错误文本可能刷屏或换行污染日志。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase72RealAppSafetyBoundary: 清理换行和首尾空白；如果没有这行代码，终端 token 可能被窗口标题打散。
    return text[:limit]  # 新增代码+Phase72RealAppSafetyBoundary: 限制文本长度；如果没有这行代码，长标题或异常信息可能淹没验收输出。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_phase72_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清理范围。


def _phase72_lower(value: Any, limit: int = 240) -> str:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，生成小写安全文本；如果没有这段函数，风险关键词匹配会受大小写影响。
    return _phase72_safe_text(value, limit=limit).lower()  # 新增代码+Phase72RealAppSafetyBoundary: 返回小写短文本；如果没有这行代码，PowerShell/CODEX 等大小写变体可能漏检。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_phase72_lower 到此结束；如果没有这个边界说明，初学者不容易看出大小写规范范围。


def _phase72_window_summary(window: dict[str, Any] | Any) -> dict[str, Any]:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，提取窗口安全评估摘要；如果没有这段函数，各处会重复且不一致地读取 app/title/window_id。
    source = dict(window or {}) if isinstance(window, dict) else {}  # 新增代码+Phase72RealAppSafetyBoundary: 只接受字典窗口并容错空值；如果没有这行代码，坏输入可能让安全边界崩溃。
    app = _phase72_lower(source.get("app_id") or source.get("process_name") or source.get("process") or source.get("executable") or source.get("name"), 120)  # 新增代码+Phase72RealAppSafetyBoundary: 提取 app/process key；如果没有这行代码，持久授权和风险分类没有主要目标。
    process = _phase72_lower(source.get("process_name") or source.get("process") or source.get("app_id") or source.get("executable"), 120)  # 新增代码+Phase72RealAppSafetyBoundary: 提取进程名；如果没有这行代码，终端和系统进程黑名单无法稳定匹配。
    title = _phase72_safe_text(source.get("title_preview") or source.get("title") or source.get("name") or "", 240)  # 新增代码+Phase72RealAppSafetyBoundary: 提取窗口标题预览；如果没有这行代码，登录/支付/验证码窗口无法按标题拒绝。
    window_id = _phase72_safe_text(source.get("window_id") or source.get("hwnd") or "", 120)  # 新增代码+Phase72RealAppSafetyBoundary: 提取窗口 id；如果没有这行代码，Phase60 window_id 精确匹配可能失效。
    display_id = _phase72_safe_text(source.get("display_id") or source.get("monitor_id") or "", 120)  # 新增代码+Phase72RealAppSafetyBoundary: 提取显示器 id；如果没有这行代码，多屏授权无法稳定匹配。
    return {"app": app, "process": process, "title_preview": title, "window_id": window_id, "display_id": display_id, "raw": source}  # 新增代码+Phase72RealAppSafetyBoundary: 返回规范摘要并保留原始窗口；如果没有这行代码，后续判断缺少统一事实。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_phase72_window_summary 到此结束；如果没有这个边界说明，初学者不容易看出窗口摘要范围。


def _phase72_searchable_window_text(summary: dict[str, Any]) -> str:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，拼接用于风险匹配的窗口文本；如果没有这段函数，风险分类要重复拼字段。
    raw = dict(summary.get("raw", {}))  # 新增代码+Phase72RealAppSafetyBoundary: 读取原始窗口字段；如果没有这行代码，额外字段如 url/name 无法参与敏感词检查。
    values = [summary.get("app", ""), summary.get("process", ""), summary.get("title_preview", ""), raw.get("url", ""), raw.get("class_name", ""), raw.get("automation_id", ""), raw.get("control_type", "")]  # 新增代码+Phase72RealAppSafetyBoundary: 汇总常见可见字段；如果没有这行代码，浏览器地址或控件名里的风险词会漏掉。
    return _phase72_lower(" ".join(_phase72_safe_text(value, 240) for value in values), 900)  # 新增代码+Phase72RealAppSafetyBoundary: 返回合并小写文本；如果没有这行代码，高风险关键词无法统一搜索。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_phase72_searchable_window_text 到此结束；如果没有这个边界说明，初学者不容易看出风险文本来源。


def _phase72_high_risk_category(summary: dict[str, Any]) -> str:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，判断窗口是否属于默认拒绝类别；如果没有这段函数，危险窗口可能进入真实输入层。
    app = str(summary.get("app", ""))  # 新增代码+Phase72RealAppSafetyBoundary: 读取规范 app；如果没有这行代码，终端和系统进程判断没有输入。
    process = str(summary.get("process", ""))  # 新增代码+Phase72RealAppSafetyBoundary: 读取规范进程名；如果没有这行代码，process 黑名单无法运行。
    title = _phase72_lower(summary.get("title_preview", ""), 240)  # 新增代码+Phase72RealAppSafetyBoundary: 读取小写标题；如果没有这行代码，Windows Run 等标题规则无法匹配。
    search = _phase72_searchable_window_text(summary)  # 新增代码+Phase72RealAppSafetyBoundary: 构造风险检索文本；如果没有这行代码，敏感词集合没有统一搜索对象。
    if app in PHASE72_TERMINAL_PROCESS_TOKENS or process in PHASE72_TERMINAL_PROCESS_TOKENS or "powershell" in search or "command prompt" in search:  # 新增代码+Phase72RealAppSafetyBoundary: 检查终端窗口；如果没有这行代码，agent 可能自动输入 shell 命令。
        return "terminal"  # 新增代码+Phase72RealAppSafetyBoundary: 返回终端风险类别；如果没有这行代码，审计无法说明拒绝类型。
    if app in PHASE72_CODEX_PROCESS_TOKENS or process in PHASE72_CODEX_PROCESS_TOKENS or "codex" in search:  # 新增代码+Phase72RealAppSafetyBoundary: 检查 Codex 自身 UI；如果没有这行代码，agent 可能递归控制自己的控制器。
        return "codex_ui"  # 新增代码+Phase72RealAppSafetyBoundary: 返回 Codex UI 风险类别；如果没有这行代码，审计无法说明自我控制拒绝。
    if app in PHASE72_SYSTEM_PROCESS_TOKENS or process in PHASE72_SYSTEM_PROCESS_TOKENS:  # 新增代码+Phase72RealAppSafetyBoundary: 检查系统管理进程；如果没有这行代码，注册表/任务管理器等可能被误控。
        return "system_admin"  # 新增代码+Phase72RealAppSafetyBoundary: 返回系统管理风险类别；如果没有这行代码，拒绝原因不清楚。
    if (app == "explorer.exe" or process == "explorer.exe") and title in {"run", "运行"}:  # 新增代码+Phase72RealAppSafetyBoundary: 特判 Windows Run 对话框；如果没有这行代码，短标题 Run 可能绕过普通关键词。
        return "windows_run"  # 新增代码+Phase72RealAppSafetyBoundary: 返回 Windows Run 风险类别；如果没有这行代码，审计无法说明运行框拒绝。
    for token in PHASE72_HIGH_RISK_TEXT_TOKENS:  # 新增代码+Phase72RealAppSafetyBoundary: 遍历敏感关键词集合；如果没有这行代码，密码/支付/验证码等标题无法默认拒绝。
        if token in search:  # 新增代码+Phase72RealAppSafetyBoundary: 检查关键词是否出现；如果没有这行代码，敏感窗口检测不会触发。
            return "high_risk_text"  # 新增代码+Phase72RealAppSafetyBoundary: 返回文本风险类别；如果没有这行代码，审计无法说明敏感词拒绝。
    return ""  # 新增代码+Phase72RealAppSafetyBoundary: 无风险类别时返回空字符串；如果没有这行代码，普通窗口也会被误认为危险。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_phase72_high_risk_category 到此结束；如果没有这个边界说明，初学者不容易看出风险分类范围。


def _phase72_normalized_action(action: Any) -> str:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，把高层动作名映射到持久授权 scope；如果没有这段函数，click_by_query/type_into_control 等动作无法复用 Phase60 grant。
    key = _phase72_lower(action, 120)  # 新增代码+Phase72RealAppSafetyBoundary: 清理并小写动作名；如果没有这行代码，大小写变体会导致授权不匹配。
    return PHASE72_ACTION_ALIASES.get(key, key)  # 新增代码+Phase72RealAppSafetyBoundary: 返回映射后的动作名；如果没有这行代码，高层动作可能被当成未授权新动作。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_phase72_normalized_action 到此结束；如果没有这个边界说明，初学者不容易看出动作映射范围。


def _phase72_has_approval_bypass(window: dict[str, Any] | Any) -> bool:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，识别不可信绕过字段；如果没有这段函数，伪造 previous_approval 或 force_allowed 可能取代真实授权。
    source = dict(window or {}) if isinstance(window, dict) else {}  # 新增代码+Phase72RealAppSafetyBoundary: 容错读取窗口字典；如果没有这行代码，坏输入可能让绕过检查崩溃。
    if any(bool(source.get(key)) for key in PHASE72_BYPASS_KEYS):  # 新增代码+Phase72RealAppSafetyBoundary: 检查显式绕过布尔字段；如果没有这行代码，approval_bypass=True 会被忽略。
        return True  # 新增代码+Phase72RealAppSafetyBoundary: 返回检测到绕过；如果没有这行代码，后续无法进入防绕过拒绝。
    previous = source.get("previous_approval") or source.get("approval") or source.get("policy_decision")  # 新增代码+Phase72RealAppSafetyBoundary: 读取可能伪造的旧审批结构；如果没有这行代码，dict 形式绕过不会被发现。
    return bool(isinstance(previous, dict) and previous.get("allowed"))  # 新增代码+Phase72RealAppSafetyBoundary: 旧审批显示 allowed 时视为绕过信号；如果没有这行代码，模型可能复用过期审批放行动作。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_phase72_has_approval_bypass 到此结束；如果没有这个边界说明，初学者不容易看出防绕过范围。


def _phase72_evaluate_grant(grant_store: Any, session_id: Any, action_key: str, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，调用 Phase60 持久授权评估；如果没有这段函数，安全边界会绕开已建立的授权事实源。
    if grant_store is None or not hasattr(grant_store, "evaluate"):  # 新增代码+Phase72RealAppSafetyBoundary: 检查授权 store 是否可用；如果没有这行代码，None store 会崩溃或误放行。
        return {"allowed": False, "decision": "missing_persistent_grant_store"}  # 新增代码+Phase72RealAppSafetyBoundary: 缺少授权 store 时安全拒绝；如果没有这行代码，授权系统不可用时可能被当成允许。
    try:  # 新增代码+Phase72RealAppSafetyBoundary: 捕获授权评估异常并失败关闭；如果没有这行代码，授权 store 损坏可能导致安全边界崩溃。
        result = grant_store.evaluate(session_id=session_id, action=action_key, arguments={"window": window})  # 新增代码+Phase72RealAppSafetyBoundary: 按 Phase60 接口评估授权；如果没有这行代码，普通应用动作无法证明已获授权。
    except Exception as error:  # 新增代码+Phase72RealAppSafetyBoundary: 授权评估失败时进入拒绝；如果没有这行代码，文件损坏或接口异常可能越过安全边界。
        return {"allowed": False, "decision": "persistent_grant_error", "error": _phase72_safe_text(error, 240)}  # 新增代码+Phase72RealAppSafetyBoundary: 返回失败关闭详情；如果没有这行代码，用户无法复盘授权评估为什么失败。
    return dict(result or {}) if isinstance(result, dict) else {"allowed": False, "decision": "persistent_grant_invalid_result"}  # 新增代码+Phase72RealAppSafetyBoundary: 规范化授权结果；如果没有这行代码，非 dict 返回可能污染后续判断。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_phase72_evaluate_grant 到此结束；如果没有这个边界说明，初学者不容易看出授权调用范围。


def _phase72_abort_requested(abort_gate: Any) -> bool:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，兼容 Phase61 风格 abort gate；如果没有这段函数，安全边界不能在低层发送前响应急停。
    if abort_gate is None:  # 新增代码+Phase72RealAppSafetyBoundary: 没有注入 gate 时视为未急停；如果没有这行代码，默认运行会因空 gate 崩溃。
        return False  # 新增代码+Phase72RealAppSafetyBoundary: 返回未急停；如果没有这行代码，正常动作永远无法进入授权放行。
    try:  # 新增代码+Phase72RealAppSafetyBoundary: 捕获 gate 异常并安全失败关闭；如果没有这行代码，急停状态读取失败可能导致误放行。
        if hasattr(abort_gate, "is_abort_requested"):  # 新增代码+Phase72RealAppSafetyBoundary: 支持 ComputerUseLockManager 风格接口；如果没有这行代码，Phase31/61 锁管理器不能直接接入。
            return bool(abort_gate.is_abort_requested())  # 新增代码+Phase72RealAppSafetyBoundary: 调用 is_abort_requested；如果没有这行代码，durable abort flag 不会被读取。
        if hasattr(abort_gate, "abort_requested"):  # 新增代码+Phase72RealAppSafetyBoundary: 支持轻量 gate 方法名；如果没有这行代码，测试或外部 agent 需要适配具体类名。
            return bool(abort_gate.abort_requested())  # 新增代码+Phase72RealAppSafetyBoundary: 调用 abort_requested；如果没有这行代码，自定义 gate 无法工作。
        if hasattr(abort_gate, "lock_manager") and hasattr(abort_gate.lock_manager, "is_abort_requested"):  # 新增代码+Phase72RealAppSafetyBoundary: 支持 WindowsComputerUseAbortStreamingHooks 对象；如果没有这行代码，Phase61 hooks 无法直接作为 gate。
            return bool(abort_gate.lock_manager.is_abort_requested())  # 新增代码+Phase72RealAppSafetyBoundary: 读取 hooks 内部 lock_manager；如果没有这行代码，Phase61 abort 事实源不能复用。
        if hasattr(abort_gate, "status"):  # 新增代码+Phase72RealAppSafetyBoundary: 支持返回状态字典的 gate；如果没有这行代码，状态型 gate 无法接入。
            status = abort_gate.status()  # 新增代码+Phase72RealAppSafetyBoundary: 读取 gate 状态；如果没有这行代码，abort_requested 字段无法检查。
            return bool(dict(status or {}).get("abort_requested") or dict(status or {}).get("requested"))  # 新增代码+Phase72RealAppSafetyBoundary: 从状态中读取急停字段；如果没有这行代码，状态对象不会触发拦截。
        return bool(getattr(abort_gate, "aborted", False))  # 新增代码+Phase72RealAppSafetyBoundary: 兼容属性型 gate；如果没有这行代码，简单测试替身不能使用。
    except Exception:  # 新增代码+Phase72RealAppSafetyBoundary: gate 读取异常时进入安全侧；如果没有这行代码，异常可能导致误放行或崩溃。
        return True  # 新增代码+Phase72RealAppSafetyBoundary: 读取急停失败时按已急停处理；如果没有这行代码，安全边界会在状态未知时继续发送。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_phase72_abort_requested 到此结束；如果没有这个边界说明，初学者不容易看出急停兼容范围。


def _phase72_refusal(decision: str, summary: dict[str, Any], action_key: str, *, grant_decision: dict[str, Any] | None = None, risk_category: str = "", high_risk_default_refusal: bool = False, abort_before_low_level_send: bool = False, approval_bypass_blocked: bool = False) -> dict[str, Any]:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，构造统一拒绝结果；如果没有这段函数，各拒绝路径可能遗漏 0 事件或 token 字段。
    return {"allowed": False, "decision": decision, "action": action_key, "target_summary": {key: value for key, value in summary.items() if key != "raw"}, "grant_decision": dict(grant_decision or {}), "risk_category": risk_category, "low_level_event_count": 0, "ready_for_low_level_send": False, "high_risk_default_refusal": bool(high_risk_default_refusal), "abort_before_low_level_send": bool(abort_before_low_level_send), "approval_bypass_blocked": bool(approval_bypass_blocked), "controlled_actions_expansion": PHASE72_CONTROLLED_ACTIONS_EXPANSION, "uncontrolled_actions_expanded": PHASE72_UNCONTROLLED_ACTIONS_EXPANDED, "marker": PHASE72_REAL_APP_SAFETY_BOUNDARY_MARKER, "model": PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL}  # 新增代码+Phase72RealAppSafetyBoundary: 返回失败关闭报告；如果没有这行代码，拒绝路径可能仍产生低层事件或缺少审计字段。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_phase72_refusal 到此结束；如果没有这个边界说明，初学者不容易看出拒绝报告范围。


class Phase72RecordingAbortGate:  # 新增代码+Phase72RealAppSafetyBoundary: 类段开始，提供测试和合同用的轻量 abort gate；如果没有这个类，Phase72 自检要依赖真实全局 abort 文件。
    def __init__(self, aborted: bool = False) -> None:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，初始化急停状态；如果没有这段函数，测试无法控制 gate 是开还是关。
        self.aborted = bool(aborted)  # 新增代码+Phase72RealAppSafetyBoundary: 保存是否已急停；如果没有这行代码，abort gate 没有状态来源。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，Phase72RecordingAbortGate.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def is_abort_requested(self) -> bool:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，提供 Phase31/61 风格急停读取接口；如果没有这段函数，安全边界无法用统一方法读取测试 gate。
        return bool(self.aborted)  # 新增代码+Phase72RealAppSafetyBoundary: 返回当前急停状态；如果没有这行代码，abort 测试无法触发拒绝。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，Phase72RecordingAbortGate.is_abort_requested 到此结束；如果没有这个边界说明，初学者不容易看出急停读取范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，提供状态型 gate 接口；如果没有这段函数，外部状态面板无法复用这个测试 gate。
        return {"abort_requested": bool(self.aborted), "requested": bool(self.aborted)}  # 新增代码+Phase72RealAppSafetyBoundary: 返回两种常见字段名；如果没有这行代码，不同调用方需要知道内部字段。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，Phase72RecordingAbortGate.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。
# 新增代码+Phase72RealAppSafetyBoundary: 类段结束，Phase72RecordingAbortGate 到此结束；如果没有这个边界说明，初学者不容易看出测试 gate 范围。


class WindowsRealAppSafetyBoundary:  # 新增代码+Phase72RealAppSafetyBoundary: 类段开始，组合风险分类、持久授权和急停检查；如果没有这个类，真实应用控制缺少最后统一门禁。
    def __init__(self, abort_gate: Any = None) -> None:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，初始化安全边界依赖；如果没有这段函数，生产和测试无法注入 Phase61 abort gate。
        self.abort_gate = abort_gate  # 新增代码+Phase72RealAppSafetyBoundary: 保存急停 gate；如果没有这行代码，授权后无法在发送前最后检查 abort。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，WindowsRealAppSafetyBoundary.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def evaluate(self, window: dict[str, Any] | Any, action: Any, grant_store: Any, session_id: Any = DEFAULT_PERSISTENT_GRANT_SESSION_ID) -> dict[str, Any]:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，评估真实应用动作是否能进入低层发送；如果没有这段函数，普通应用控制和危险窗口拒绝无法统一。
        summary = _phase72_window_summary(window)  # 新增代码+Phase72RealAppSafetyBoundary: 提取窗口摘要；如果没有这行代码，后续风险和授权检查没有统一目标。
        raw_window = dict(summary.get("raw", {}))  # 新增代码+Phase72RealAppSafetyBoundary: 读取原始窗口字典；如果没有这行代码，Phase60 evaluate 无法看到原始 app/window/display 字段。
        action_key = _phase72_normalized_action(action)  # 新增代码+Phase72RealAppSafetyBoundary: 规范化动作名；如果没有这行代码，高层动作和授权 scope 可能无法匹配。
        risk_category = _phase72_high_risk_category(summary)  # 新增代码+Phase72RealAppSafetyBoundary: 判断是否危险窗口；如果没有这行代码，终端/验证码/系统设置会进入授权流程甚至误放行。
        if risk_category:  # 新增代码+Phase72RealAppSafetyBoundary: 高风险窗口优先拒绝；如果没有这行代码，持久授权或伪造字段可能覆盖安全红线。
            return _phase72_refusal("high_risk_window_refused", summary, action_key, risk_category=risk_category, high_risk_default_refusal=True)  # 新增代码+Phase72RealAppSafetyBoundary: 返回高风险 0 事件拒绝；如果没有这行代码，危险窗口可能触发真实输入。
        grant_decision = _phase72_evaluate_grant(grant_store, session_id, action_key, raw_window)  # 新增代码+Phase72RealAppSafetyBoundary: 调用 Phase60 持久授权评估；如果没有这行代码，普通应用动作没有可审计授权来源。
        if not bool(grant_decision.get("allowed")):  # 新增代码+Phase72RealAppSafetyBoundary: 授权未通过时拒绝；如果没有这行代码，未授权普通应用会被放行。
            if _phase72_has_approval_bypass(raw_window):  # 新增代码+Phase72RealAppSafetyBoundary: 检查是否存在绕过授权暗示；如果没有这行代码，previous_approval=True 可能误导上层。
                return _phase72_refusal("approval_bypass_blocked", summary, action_key, grant_decision=grant_decision, approval_bypass_blocked=True)  # 新增代码+Phase72RealAppSafetyBoundary: 返回防绕过 0 事件拒绝；如果没有这行代码，伪造 approval 可能替代持久授权。
            return _phase72_refusal("requires_persistent_grant", summary, action_key, grant_decision=grant_decision)  # 新增代码+Phase72RealAppSafetyBoundary: 返回需要持久授权的 0 事件拒绝；如果没有这行代码，用户不知道要先 approve。
        if _phase72_abort_requested(self.abort_gate):  # 新增代码+Phase72RealAppSafetyBoundary: 在授权通过后、低层发送前读取急停；如果没有这行代码，用户 abort 可能拦不住已授权动作。
            return _phase72_refusal("abort_before_low_level_send", summary, action_key, grant_decision=grant_decision, abort_before_low_level_send=True)  # 新增代码+Phase72RealAppSafetyBoundary: 返回发送前急停 0 事件拒绝；如果没有这行代码，急停后仍可能发生真实输入。
        return {"allowed": True, "decision": "allowed_by_persistent_grant", "action": action_key, "target_summary": {key: value for key, value in summary.items() if key != "raw"}, "grant_decision": grant_decision, "grant_id": grant_decision.get("grant_id", ""), "low_level_event_count": 0, "ready_for_low_level_send": True, "high_risk_default_refusal": False, "abort_before_low_level_send": False, "approval_bypass_blocked": False, "controlled_actions_expansion": PHASE72_CONTROLLED_ACTIONS_EXPANSION, "uncontrolled_actions_expanded": PHASE72_UNCONTROLLED_ACTIONS_EXPANDED, "marker": PHASE72_REAL_APP_SAFETY_BOUNDARY_MARKER, "model": PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL}  # 新增代码+Phase72RealAppSafetyBoundary: 返回允许进入下游低层发送的报告；如果没有这行代码，合法普通应用动作无法继续执行。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，WindowsRealAppSafetyBoundary.evaluate 到此结束；如果没有这个边界说明，初学者不容易看出评估流程范围。

    def evaluate_with_mode_session(self, window: dict[str, Any], action: str, mode_store: Any, session_id: str) -> dict[str, Any]:  # 新增代码+Phase99UniversalComputerUseModeGate：函数段开始，先问 Phase98 mode session 再决定是否允许真实动作；如果没有这段函数，normal mode 无法替代普通 app 白名单。
        summary = _phase72_window_summary(window)  # 新增代码+Phase99UniversalComputerUseModeGate：提取窗口摘要；如果没有这行代码，mode 决策报告缺少统一目标摘要。
        raw_window = dict(summary.get("raw", {}))  # 新增代码+Phase99UniversalComputerUseModeGate：读取原始窗口字段给 mode store；如果没有这行代码，危险目标扫描会缺少 app/process/title 信息。
        action_key = _phase72_normalized_action(action)  # 新增代码+Phase99UniversalComputerUseModeGate：规范化动作名再交给 mode store；如果没有这行代码，高层 click_by_visual_point 可能无法匹配 normal 允许动作。
        mode_decision = dict(mode_store.evaluate_action(raw_window, action_key))  # 新增代码+Phase99UniversalComputerUseModeGate：先调用 Phase98 mode 决策；如果没有这行代码，真实动作会绕过 normal/observe/stopped/expired 策略。
        if not bool(mode_decision.get("allowed")):  # 新增代码+Phase99UniversalComputerUseModeGate：检查 mode 是否拒绝；如果没有这行代码，observe、stopped、expired 或危险目标可能继续进入发送前路径。
            mode_reason = str(mode_decision.get("decision", ""))  # 新增代码+Phase99UniversalComputerUseModeGate：读取原始 mode 拒绝原因；如果没有这行代码，边界层无法规范 observe 原因码。
            boundary_decision = "action_risk_exceeds_mode" if mode_reason == "observe_mode_blocks_write_action" else mode_reason  # 新增代码+Phase99UniversalComputerUseModeGate：把 observe 写动作拒绝规范成上层风险原因；如果没有这行代码，上层要绑定 Phase98 内部细节。
            return {"allowed": False, "decision": boundary_decision, "action": action_key, "target_summary": {key: value for key, value in summary.items() if key != "raw"}, "mode_decision": mode_decision, "session_id": str(session_id), "low_level_event_count": 0, "ready_for_low_level_send": False, "mode_session_used": True, "per_app_allowlist_required": False, "ordinary_apps_allowed_by_risk_policy": False, "safety_boundary_model": PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL, "model": PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL, "marker": PHASE72_REAL_APP_SAFETY_BOUNDARY_MARKER, "controlled_actions_expansion": PHASE72_CONTROLLED_ACTIONS_EXPANSION, "uncontrolled_actions_expanded": PHASE72_UNCONTROLLED_ACTIONS_EXPANDED}  # 新增代码+Phase99UniversalComputerUseModeGate：返回 mode 拒绝的零事件报告；如果没有这行代码，被拒绝动作可能缺少审计字段或误触低层发送。
        risk_category = _phase72_high_risk_category(summary)  # 修改代码+Phase99UniversalComputerUseModeGate：mode 允许后再复用 Phase72 高风险窗口分类；如果没有这行代码，task manager/login/credit card 等高风险目标会被 normal mode 误放行。
        if risk_category:  # 修改代码+Phase99UniversalComputerUseModeGate：高风险命中时优先零事件拒绝；如果没有这行代码，后续允许路径会绕过 Phase72 红线。
            return {"allowed": False, "decision": "high_risk_window_refused", "action": action_key, "target_summary": {key: value for key, value in summary.items() if key != "raw"}, "mode_decision": mode_decision, "risk_category": risk_category, "high_risk_default_refusal": True, "session_id": str(session_id), "low_level_event_count": 0, "ready_for_low_level_send": False, "mode_session_used": True, "per_app_allowlist_required": False, "ordinary_apps_allowed_by_risk_policy": False, "safety_boundary_model": PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL, "model": PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL, "marker": PHASE72_REAL_APP_SAFETY_BOUNDARY_MARKER, "controlled_actions_expansion": PHASE72_CONTROLLED_ACTIONS_EXPANSION, "uncontrolled_actions_expanded": PHASE72_UNCONTROLLED_ACTIONS_EXPANDED}  # 修改代码+Phase99UniversalComputerUseModeGate：返回 Phase72 高风险零事件拒绝并保留 mode 决策；如果没有这行代码，复审指出的高风险窗口没有可审计拦截报告。
        if _phase72_abort_requested(self.abort_gate):  # 新增代码+Phase99UniversalComputerUseModeGate：mode 允许后仍检查急停；如果没有这行代码，normal mode 会绕过用户最后一刻的 abort。
            return {"allowed": False, "decision": "abort_before_low_level_send", "action": action_key, "target_summary": {key: value for key, value in summary.items() if key != "raw"}, "mode_decision": mode_decision, "session_id": str(session_id), "low_level_event_count": 0, "ready_for_low_level_send": False, "mode_session_used": True, "per_app_allowlist_required": False, "ordinary_apps_allowed_by_risk_policy": bool(mode_decision.get("allowed")), "abort_before_low_level_send": True, "safety_boundary_model": PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL, "model": PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL, "marker": PHASE72_REAL_APP_SAFETY_BOUNDARY_MARKER, "controlled_actions_expansion": PHASE72_CONTROLLED_ACTIONS_EXPANSION, "uncontrolled_actions_expanded": PHASE72_UNCONTROLLED_ACTIONS_EXPANDED}  # 新增代码+Phase99UniversalComputerUseModeGate：返回急停零事件拒绝；如果没有这行代码，已获 normal mode 的动作可能在急停后继续发送。
        return {"allowed": True, "decision": "allowed_by_computer_use_mode", "action": action_key, "target_summary": {key: value for key, value in summary.items() if key != "raw"}, "mode_decision": mode_decision, "session_id": str(session_id), "low_level_event_count": 0, "ready_for_low_level_send": True, "mode_session_used": True, "per_app_allowlist_required": False, "ordinary_apps_allowed_by_risk_policy": True, "safety_boundary_model": PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL, "model": PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL, "marker": PHASE72_REAL_APP_SAFETY_BOUNDARY_MARKER, "controlled_actions_expansion": PHASE72_CONTROLLED_ACTIONS_EXPANSION, "uncontrolled_actions_expanded": PHASE72_UNCONTROLLED_ACTIONS_EXPANDED}  # 新增代码+Phase99UniversalComputerUseModeGate：返回 mode 允许且准备进入低层发送的报告；如果没有这行代码，普通应用 normal mode 仍无法通过真实派发前门禁。
    # 新增代码+Phase99UniversalComputerUseModeGate：函数段结束，WindowsRealAppSafetyBoundary.evaluate_with_mode_session 到此结束；如果没有这个边界说明，初学者不容易看出 mode-aware 评估范围。
# 修改代码+Phase99UniversalComputerUseModeGate：类段结束，WindowsRealAppSafetyBoundary 到此结束；如果没有这个边界说明，新增 mode-aware 方法会被误以为不属于安全边界类。


def run_phase72_real_app_safety_boundary_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，运行 Phase72 安全边界合同自检；如果没有这段函数，CLI 和真实终端没有统一验收入口。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE72_REAL_APP_SAFETY_BOUNDARY_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase72RealAppSafetyBoundary: 选择隔离合同目录；如果没有这行代码，多次自检可能互相污染。
    store = WindowsComputerUsePersistentGrantStore(base_dir=root / "grants")  # 新增代码+Phase72RealAppSafetyBoundary: 创建隔离持久授权 store；如果没有这行代码，自检无法证明 Phase60 授权对 Phase72 生效。
    boundary = WindowsRealAppSafetyBoundary()  # 新增代码+Phase72RealAppSafetyBoundary: 创建默认安全边界；如果没有这行代码，合同没有评估主体。
    session_id = f"phase72-contract-{int(time.time() * 1000)}"  # 新增代码+Phase72RealAppSafetyBoundary: 生成唯一会话 id；如果没有这行代码，多次合同运行可能匹配旧授权。
    safe_window = {"app_id": "notepad.exe", "process_name": "notepad.exe", "window_id": "hwnd:7201", "title_preview": "Untitled - Notepad", "display_id": "DISPLAY1", "safe_to_target": True}  # 新增代码+Phase72RealAppSafetyBoundary: 构造普通应用正例窗口；如果没有这行代码，authorized_real_app_actions 没有目标。
    terminal_window = {"app_id": "powershell.exe", "process_name": "powershell.exe", "window_id": "hwnd:7202", "title_preview": "Windows PowerShell", "display_id": "DISPLAY1", "safe_to_target": True}  # 新增代码+Phase72RealAppSafetyBoundary: 构造终端危险窗口；如果没有这行代码，高风险拒绝缺少终端样本。
    codex_window = {"app_id": "codex.exe", "process_name": "codex.exe", "window_id": "hwnd:7203", "title_preview": "Codex - Learning Agent", "display_id": "DISPLAY1", "safe_to_target": True}  # 新增代码+Phase72RealAppSafetyBoundary: 构造 Codex UI 危险窗口；如果没有这行代码，自我控制拒绝没有样本。
    auth_window = {"app_id": "chrome.exe", "process_name": "chrome.exe", "window_id": "hwnd:7204", "title_preview": "Login password captcha payment verification", "display_id": "DISPLAY1", "safe_to_target": True}  # 新增代码+Phase72RealAppSafetyBoundary: 构造敏感业务危险窗口；如果没有这行代码，密码验证码支付拒绝没有样本。
    unauthorized = boundary.evaluate(safe_window, "click", store, session_id)  # 新增代码+Phase72RealAppSafetyBoundary: 未授权普通应用先评估；如果没有这行代码，默认拒绝 0 事件没有证据。
    bypass_window = dict(safe_window, approval_bypass=True, previous_approval={"allowed": True})  # 新增代码+Phase72RealAppSafetyBoundary: 构造伪造绕过字段窗口；如果没有这行代码，approval_bypass_blocked 没有样本。
    bypass = boundary.evaluate(bypass_window, "click", store, session_id)  # 新增代码+Phase72RealAppSafetyBoundary: 评估绕过字段；如果没有这行代码，防绕过 token 没有证据。
    high_risk_results = [boundary.evaluate(window, "click", store, session_id) for window in [terminal_window, codex_window, auth_window]]  # 新增代码+Phase72RealAppSafetyBoundary: 评估三类危险窗口；如果没有这行代码，高风险默认拒绝覆盖不足。
    store.approve(session_id=session_id, app="notepad.exe", window_id="hwnd:7201", display_id="DISPLAY1", action_scope=["click", "type_text", "scroll", "drag"], ttl_seconds=60, reason="phase72-contract-authorized-real-app", grant_flags={"desktopAction": True})  # 新增代码+Phase72RealAppSafetyBoundary: 写入普通应用动作授权；如果没有这行代码，授权正例无法放行。
    allowed_click = boundary.evaluate(safe_window, "click", store, session_id)  # 新增代码+Phase72RealAppSafetyBoundary: 评估授权点击；如果没有这行代码，authorized_real_app_actions 少了点击证据。
    allowed_type = boundary.evaluate(safe_window, "type_into_control", store, session_id)  # 新增代码+Phase72RealAppSafetyBoundary: 评估高层输入动作映射；如果没有这行代码，受控动作扩展没有输入动作证据。
    abort_boundary = WindowsRealAppSafetyBoundary(abort_gate=Phase72RecordingAbortGate(aborted=True))  # 新增代码+Phase72RealAppSafetyBoundary: 创建已急停的边界；如果没有这行代码，abort_before_low_level_send 没有最后一跳证据。
    aborted = abort_boundary.evaluate(safe_window, "click", store, session_id)  # 新增代码+Phase72RealAppSafetyBoundary: 对已授权点击执行急停评估；如果没有这行代码，abort 可能只在未授权路径被误判。
    authorized_real_app_actions = bool(allowed_click.get("allowed") and allowed_type.get("allowed") and allowed_click.get("decision") == "allowed_by_persistent_grant" and allowed_type.get("decision") == "allowed_by_persistent_grant")  # 新增代码+Phase72RealAppSafetyBoundary: 汇总授权普通应用动作是否成功；如果没有这行代码，合同无法表达可控普通软件。
    unauthorized_window_zero_events = bool(not unauthorized.get("allowed") and unauthorized.get("decision") == "requires_persistent_grant" and unauthorized.get("low_level_event_count") == 0)  # 新增代码+Phase72RealAppSafetyBoundary: 汇总未授权拒绝 0 事件；如果没有这行代码，默认拒绝副作用无法进入 token。
    high_risk_default_refusal = bool(all((not result.get("allowed")) and result.get("decision") == "high_risk_window_refused" and result.get("low_level_event_count") == 0 and result.get("high_risk_default_refusal") for result in high_risk_results))  # 新增代码+Phase72RealAppSafetyBoundary: 汇总高风险默认拒绝；如果没有这行代码，终端/Codex/敏感页覆盖结果无法进入 token。
    abort_before_low_level_send = bool(not aborted.get("allowed") and aborted.get("decision") == "abort_before_low_level_send" and aborted.get("low_level_event_count") == 0 and aborted.get("abort_before_low_level_send"))  # 新增代码+Phase72RealAppSafetyBoundary: 汇总急停前置拦截；如果没有这行代码，abort 验收无法进入 token。
    approval_bypass_blocked = bool(not bypass.get("allowed") and bypass.get("decision") == "approval_bypass_blocked" and bypass.get("low_level_event_count") == 0 and bypass.get("approval_bypass_blocked"))  # 新增代码+Phase72RealAppSafetyBoundary: 汇总防绕过结果；如果没有这行代码，伪造 approval 风险无法进入 token。
    controlled_actions_expansion = bool(PHASE72_CONTROLLED_ACTIONS_EXPANSION and allowed_click.get("controlled_actions_expansion") and allowed_type.get("controlled_actions_expansion"))  # 新增代码+Phase72RealAppSafetyBoundary: 汇总受控动作扩展；如果没有这行代码，能力提升边界无法进入 token。
    uncontrolled_actions_expanded = bool(PHASE72_UNCONTROLLED_ACTIONS_EXPANDED)  # 新增代码+Phase72RealAppSafetyBoundary: 汇总无边界动作是否扩展；如果没有这行代码，安全声明无法进入 token。
    passed = bool(authorized_real_app_actions and unauthorized_window_zero_events and high_risk_default_refusal and abort_before_low_level_send and approval_bypass_blocked and controlled_actions_expansion and not uncontrolled_actions_expanded)  # 新增代码+Phase72RealAppSafetyBoundary: 汇总合同通过条件；如果没有这行代码，main 无法用退出码表达失败。
    return {"marker": PHASE72_REAL_APP_SAFETY_BOUNDARY_MARKER, "ok_token": PHASE72_REAL_APP_SAFETY_BOUNDARY_OK_TOKEN, "authorized_real_app_actions": authorized_real_app_actions, "unauthorized_window_zero_events": unauthorized_window_zero_events, "high_risk_default_refusal": high_risk_default_refusal, "abort_before_low_level_send": abort_before_low_level_send, "approval_bypass_blocked": approval_bypass_blocked, "controlled_actions_expansion": controlled_actions_expansion, "uncontrolled_actions_expanded": uncontrolled_actions_expanded, "passed": passed, "state_dir": str(root)}  # 新增代码+Phase72RealAppSafetyBoundary: 返回完整合同报告；如果没有这行代码，测试和真实终端拿不到统一结果。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，run_phase72_real_app_safety_boundary_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase72_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，把合同报告转成稳定 CLI token 行；如果没有这段函数，真实终端场景要解析复杂 JSON。
    return f"{PHASE72_REAL_APP_SAFETY_BOUNDARY_MARKER} {PHASE72_REAL_APP_SAFETY_BOUNDARY_OK_TOKEN} authorized_real_app_actions={_phase72_bool_token(report.get('authorized_real_app_actions'))} unauthorized_window_zero_events={_phase72_bool_token(report.get('unauthorized_window_zero_events'))} high_risk_default_refusal={_phase72_bool_token(report.get('high_risk_default_refusal'))} abort_before_low_level_send={_phase72_bool_token(report.get('abort_before_low_level_send'))} approval_bypass_blocked={_phase72_bool_token(report.get('approval_bypass_blocked'))} controlled_actions_expansion={_phase72_bool_token(report.get('controlled_actions_expansion'))} uncontrolled_actions_expanded={_phase72_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+Phase72RealAppSafetyBoundary: 返回固定顺序 token；如果没有这行代码，验收输出容易漂移。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，phase72_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，提供命令行入口；如果没有这段函数，真实终端无法直接运行 Phase72 自检。
    _ = argv  # 新增代码+Phase72RealAppSafetyBoundary: 保留 argv 供未来扩展；如果没有这行代码，参数存在但用途不清楚。
    report = run_phase72_real_app_safety_boundary_contract()  # 新增代码+Phase72RealAppSafetyBoundary: 运行合同自检；如果没有这行代码，CLI 不会生成安全边界证据。
    print(phase72_cli_line(report))  # 新增代码+Phase72RealAppSafetyBoundary: 打印稳定 token 行；如果没有这行代码，debug log 无法匹配 Phase72 成功。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase72RealAppSafetyBoundary: 打印结构化报告；如果没有这行代码，失败时不易复盘。
    print(PHASE72_REAL_APP_SAFETY_BOUNDARY_MARKER)  # 新增代码+Phase72RealAppSafetyBoundary: 单独打印 ready marker；如果没有这行代码，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase72RealAppSafetyBoundary: 根据合同结果返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["DEFAULT_PHASE72_REAL_APP_SAFETY_BOUNDARY_ROOT", "PHASE72_CONTROLLED_ACTIONS_EXPANSION", "PHASE72_REAL_APP_SAFETY_BOUNDARY_MARKER", "PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL", "PHASE72_REAL_APP_SAFETY_BOUNDARY_OK_TOKEN", "PHASE72_UNCONTROLLED_ACTIONS_EXPANDED", "Phase72RecordingAbortGate", "WindowsRealAppSafetyBoundary", "main", "phase72_cli_line", "run_phase72_real_app_safety_boundary_contract"]  # 新增代码+Phase72RealAppSafetyBoundary: 限定公开导出名称；如果没有这行代码，包导入容易暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase72RealAppSafetyBoundary: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase72RealAppSafetyBoundary: 用 main 返回码退出；如果没有这行代码，命令行状态不明确。
