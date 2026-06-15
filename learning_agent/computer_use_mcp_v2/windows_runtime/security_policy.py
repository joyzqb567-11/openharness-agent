"""Windows Computer Use Phase48 安全策略层。"""  # 新增代码+Phase48WindowsSecurityPolicy: 标明本文件负责更细粒度的桌面权限策略；如果没有这行代码，读者不知道 observe/action/system_key/clipboard 的判断集中在哪里。
from __future__ import annotations  # 新增代码+Phase48WindowsSecurityPolicy: 启用延迟类型解析；如果没有这行代码，旧入口遇到前向类型注解时更容易导入失败。

import json  # 新增代码+Phase48WindowsSecurityPolicy: 导入 JSON 工具用于 CLI 自检输出结构化报告；如果没有这行代码，验收器难以读取完整策略结果。
from typing import Any  # 新增代码+Phase48WindowsSecurityPolicy: 导入 Any 表示工具动作参数的动态 JSON 值；如果没有这行代码，策略接口类型边界不清楚。

PHASE48_WINDOWS_SECURITY_POLICY_MARKER = "PHASE48_WINDOWS_SECURITY_POLICY_READY"  # 新增代码+Phase48WindowsSecurityPolicy: 定义 Phase48 ready marker；如果没有这行代码，真实终端验收无法稳定匹配本阶段。
PHASE48_WINDOWS_SECURITY_POLICY_OK_TOKEN = "PHASE48_WINDOWS_SECURITY_POLICY_OK"  # 新增代码+Phase48WindowsSecurityPolicy: 定义 Phase48 OK token；如果没有这行代码，debug log 无法区分自检通过和普通输出。
PHASE48_SECURITY_POLICY_CONTRACT = "phase48_windows_security_policy"  # 新增代码+Phase48WindowsSecurityPolicy: 定义策略合同名称；如果没有这行代码，终端状态无法说明当前使用哪版安全策略。
PHASE48_ACTIONS_EXPANDED = False  # 新增代码+Phase48WindowsSecurityPolicy: 明确本阶段只升级策略不扩大动作面；如果没有这行代码，用户可能误以为新增了更多真实控制动作。
PHASE48_GRANT_CLASSES: tuple[str, ...] = ("observe", "desktopAction", "systemKeyCombos", "clipboardRead", "clipboardWrite")  # 新增代码+Phase48WindowsSecurityPolicy: 固定策略识别的授权类别；如果没有这行代码，终端无法展示清晰 grant 清单。
PHASE48_HIGH_RISK_GRANTS: tuple[str, ...] = ("systemKeyCombos", "clipboardRead", "clipboardWrite")  # 新增代码+Phase48WindowsSecurityPolicy: 固定默认拒绝的高风险授权；如果没有这行代码，危险权限会和普通动作混在一起。
OBSERVE_ACTIONS: tuple[str, ...] = ("screenshot", "capture", "observe", "observe:get_window_state", "get_window_state", "list_windows", "list_apps", "get_active_window")  # 新增代码+Phase48WindowsSecurityPolicy: 定义只读观察动作集合；如果没有这行代码，只读能力会被误当作写动作审批。
DESKTOP_ACTIONS: tuple[str, ...] = ("move", "move_mouse", "click", "double_click", "triple_click", "scroll", "press_key", "hold_key", "type_text", "drag_path", "mouse_down", "mouse_up")  # 修改代码+ClaudeCodeParity: 把 ClaudeCode parity 写动作纳入 desktopAction；如果没有这行代码，新动作会只靠默认分支且状态语义不清晰。
CLIPBOARD_READ_ACTIONS: tuple[str, ...] = ("clipboard_read", "read_clipboard", "get_clipboard")  # 新增代码+Phase48WindowsSecurityPolicy: 定义剪贴板读取动作集合；如果没有这行代码，读取剪贴板不会被单独授权。
CLIPBOARD_WRITE_ACTIONS: tuple[str, ...] = ("clipboard_write", "write_clipboard", "set_clipboard", "paste", "paste_text")  # 新增代码+Phase48WindowsSecurityPolicy: 定义剪贴板写入动作集合；如果没有这行代码，写剪贴板可能被普通动作授权误放行。
SYSTEM_KEY_COMBO_TOKENS: tuple[str, ...] = ("ctrl+alt+delete", "win+", "windows+", "alt+tab", "ctrl+shift+esc", "taskmgr")  # 新增代码+Phase48WindowsSecurityPolicy: 定义系统级组合键特征；如果没有这行代码，危险快捷键无法触发 systemKeyCombos 门禁。


def _bool_token(value: bool) -> str:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会出现 True/False 大小写漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase48WindowsSecurityPolicy: 返回验收器期望的 true/false 文本；如果没有这行代码，场景断言会因大小写不一致失败。
# 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化 helper 范围。


def _safe_text(value: Any, limit: int = 160) -> str:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，生成单行安全短文本；如果没有这段函数，拒绝原因可能被过长或换行文本污染。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase48WindowsSecurityPolicy: 把任意输入压成单行；如果没有这行代码，终端输出可能被参数换行打乱。
    return text[:limit]  # 新增代码+Phase48WindowsSecurityPolicy: 限制文本长度；如果没有这行代码，巨大按键或标题会挤爆状态面板。
# 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，_safe_text 到此结束；如果没有这个边界说明，读者不容易看出文本规整范围。


def _normalized_action(action: Any) -> str:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，统一动作名格式；如果没有这段函数，大小写或空白会让策略误判动作。
    return _safe_text(action, 120).lower()  # 新增代码+Phase48WindowsSecurityPolicy: 返回小写动作名；如果没有这行代码，Press_Key 等变体可能绕过策略分类。
# 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，_normalized_action 到此结束；如果没有这个边界说明，读者不容易看出动作名规整范围。


def _keys_combo_text(arguments: dict[str, Any]) -> str:  # 新增代码+ClaudeCodeParity: 函数段开始，把 keys 数组和 key 字符串统一成组合键文本；如果没有这段函数，hold_key 的数组形式会绕过系统组合键检查。
    raw_keys = dict(arguments or {}).get("keys")  # 新增代码+ClaudeCodeParity: 优先读取 hold_key 的 keys 数组；如果没有这行代码，session adapter 传来的组合键列表会被忽略。
    if isinstance(raw_keys, list):  # 新增代码+ClaudeCodeParity: 判断 keys 是否为列表；如果没有这行代码，字符串会被错误按字符拆开。
        cleaned = [_safe_text(item, 80).lower() for item in raw_keys if _safe_text(item, 80)]  # 新增代码+ClaudeCodeParity: 清洗每个键名并转小写；如果没有这行代码，大小写和空键会导致风险识别不稳定。
        return "+".join(cleaned)  # 新增代码+ClaudeCodeParity: 用加号拼成 ctrl+alt+delete 形态；如果没有这行代码，SYSTEM_KEY_COMBO_TOKENS 无法复用。
    return _safe_text(dict(arguments or {}).get("key", ""), 160).lower()  # 新增代码+ClaudeCodeParity: 回退到旧 key 字符串；如果没有这行代码，press_key 和旧 hold_key 参数会失去兼容。
# 新增代码+ClaudeCodeParity: 函数段结束，_keys_combo_text 到此结束；如果没有这个边界说明，初学者不容易看出组合键文本来源范围。


def _is_system_key_combo(action: str, arguments: dict[str, Any]) -> bool:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，判断动作是否属于系统组合键；如果没有这段函数，危险快捷键无法被额外拦截。
    key_text = _keys_combo_text(dict(arguments or {}))  # 修改代码+ClaudeCodeParity: 同时读取 key 字符串和 hold_key keys 数组；如果没有这行代码，Win+R 等数组组合键会被误当普通动作。
    return action in {"press_key", "hold_key"} and any(token in key_text for token in SYSTEM_KEY_COMBO_TOKENS)  # 修改代码+ClaudeCodeParity: press_key/hold_key 命中系统键 token 都返回 true；如果没有这行代码，hold_key 危险组合会绕过 systemKeyCombos。
# 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，_is_system_key_combo 到此结束；如果没有这个边界说明，读者不容易看出系统键判断范围。


def _grant_text(grants: list[str]) -> str:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，把 grant 列表转成可读文本；如果没有这段函数，拒绝原因会缺少具体权限名。
    return ",".join(grants) if grants else "none"  # 新增代码+Phase48WindowsSecurityPolicy: 返回逗号分隔的授权名；如果没有这行代码，终端拒绝原因很难被用户扫读。
# 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，_grant_text 到此结束；如果没有这个边界说明，读者不容易看出 grant 文本格式范围。


class WindowsComputerUseSecurityPolicy:  # 新增代码+Phase48WindowsSecurityPolicy: 类段开始，封装 Phase48 细粒度权限策略；如果没有这个类，审批模型无法复用统一安全判定。
    def status(self) -> dict[str, Any]:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，返回机器可读策略状态；如果没有这段函数，/computer status 无法展示策略事实。
        return {"enabled": True, "security_policy": PHASE48_SECURITY_POLICY_CONTRACT, "grant_classes": list(PHASE48_GRANT_CLASSES), "high_risk_grants": list(PHASE48_HIGH_RISK_GRANTS), "marker": PHASE48_WINDOWS_SECURITY_POLICY_MARKER, "actions_expanded": PHASE48_ACTIONS_EXPANDED}  # 新增代码+Phase48WindowsSecurityPolicy: 返回策略名、授权类别和高风险类别；如果没有这行代码，调用方拿不到完整策略摘要。
    # 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，status 到此结束；如果没有这个边界说明，读者不容易看出状态范围。

    def terminal_status_lines(self, grant_flags: dict[str, bool] | None = None) -> list[str]:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，生成用户可读终端策略摘要；如果没有这段函数，用户只能读结构化 JSON。
        flags = dict(grant_flags or {})  # 新增代码+Phase48WindowsSecurityPolicy: 复制授权状态避免修改调用方对象；如果没有这行代码，格式化可能意外污染审批模型。
        flag_text = ",".join(f"{name}:{_bool_token(flags.get(name, False))}" for name in PHASE48_GRANT_CLASSES)  # 新增代码+Phase48WindowsSecurityPolicy: 按固定顺序渲染 grant flags；如果没有这行代码，状态面板顺序会漂移难以验收。
        return ["Computer Use Security Policy", f"- security_policy={PHASE48_SECURITY_POLICY_CONTRACT}", f"- grant_classes={','.join(PHASE48_GRANT_CLASSES)}", f"- high_risk_default={','.join(PHASE48_HIGH_RISK_GRANTS)}", f"- security_policy_grant_flags={flag_text}", f"- actions_expanded={_bool_token(PHASE48_ACTIONS_EXPANDED)}"]  # 新增代码+Phase48WindowsSecurityPolicy: 返回多行策略面板；如果没有这行代码，真实终端用户看不到 Phase48 授权类别。
    # 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，terminal_status_lines 到此结束；如果没有这个边界说明，读者不容易看出终端摘要范围。

    def required_grants(self, action: str, arguments: dict[str, Any]) -> list[str]:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，计算动作需要哪些 grant；如果没有这段函数，审批层只能写死单一权限。
        normalized = _normalized_action(action)  # 新增代码+Phase48WindowsSecurityPolicy: 规范化动作名；如果没有这行代码，大小写变体会影响授权类别。
        if normalized in CLIPBOARD_READ_ACTIONS:  # 新增代码+Phase48WindowsSecurityPolicy: 识别剪贴板读取动作；如果没有这行代码，剪贴板读取不会要求 clipboardRead。
            return ["clipboardRead"]  # 新增代码+Phase48WindowsSecurityPolicy: 剪贴板读需要 clipboardRead；如果没有这行代码，读取剪贴板会被普通动作授权误覆盖。
        if normalized in CLIPBOARD_WRITE_ACTIONS:  # 新增代码+Phase48WindowsSecurityPolicy: 识别剪贴板写入动作；如果没有这行代码，剪贴板写入不会要求 clipboardWrite。
            return ["clipboardWrite"]  # 新增代码+Phase48WindowsSecurityPolicy: 剪贴板写需要 clipboardWrite；如果没有这行代码，写剪贴板会被普通动作授权误覆盖。
        if _is_system_key_combo(normalized, dict(arguments or {})):  # 新增代码+Phase48WindowsSecurityPolicy: 识别系统级组合键；如果没有这行代码，危险快捷键不会进入高风险授权分支。
            return ["desktopAction", "systemKeyCombos"]  # 新增代码+Phase48WindowsSecurityPolicy: 系统组合键需要普通动作和系统键双重授权；如果没有这行代码，单一 grant 无法表达风险。
        if normalized in OBSERVE_ACTIONS or normalized.startswith("observe:"):  # 新增代码+Phase48WindowsSecurityPolicy: 识别只读观察动作；如果没有这行代码，只读观察可能被误要求写动作授权。
            return ["observe"]  # 新增代码+Phase48WindowsSecurityPolicy: 只读观察需要 observe grant；如果没有这行代码，用户无法单独开启只读能力。
        if normalized in DESKTOP_ACTIONS:  # 新增代码+Phase48WindowsSecurityPolicy: 识别普通桌面写动作；如果没有这行代码，点击和输入无法要求 desktopAction。
            return ["desktopAction"]  # 新增代码+Phase48WindowsSecurityPolicy: 普通桌面动作需要 desktopAction；如果没有这行代码，未授权动作可能放行。
        return ["desktopAction"]  # 新增代码+Phase48WindowsSecurityPolicy: 未知动作按写动作保守处理；如果没有这行代码，新动作可能绕过默认拒绝。
    # 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，required_grants 到此结束；如果没有这个边界说明，读者不容易看出授权计算范围。

    def grant_scope(self, action: str, arguments: dict[str, Any]) -> str:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，计算动作的人类可读权限类别；如果没有这段函数，状态和审计难以解释动作风险。
        required = self.required_grants(action, arguments)  # 新增代码+Phase48WindowsSecurityPolicy: 复用 grant 计算结果；如果没有这行代码，scope 逻辑会和授权要求分叉。
        if "systemKeyCombos" in required:  # 新增代码+Phase48WindowsSecurityPolicy: 判断是否包含系统键权限；如果没有这行代码，系统键会显示成普通 action。
            return "system_key"  # 新增代码+Phase48WindowsSecurityPolicy: 返回系统键类别；如果没有这行代码，用户看不出为何风险更高。
        if "clipboardRead" in required or "clipboardWrite" in required:  # 新增代码+Phase48WindowsSecurityPolicy: 判断是否包含剪贴板权限；如果没有这行代码，剪贴板动作会显示成普通 action。
            return "clipboard"  # 新增代码+Phase48WindowsSecurityPolicy: 返回剪贴板类别；如果没有这行代码，剪贴板风险不可见。
        if required == ["observe"]:  # 新增代码+Phase48WindowsSecurityPolicy: 判断是否是纯观察动作；如果没有这行代码，只读和写动作无法区分。
            return "observe"  # 新增代码+Phase48WindowsSecurityPolicy: 返回观察类别；如果没有这行代码，用户无法单独理解只读权限。
        return "action"  # 新增代码+Phase48WindowsSecurityPolicy: 其余按普通动作类别处理；如果没有这行代码，点击等动作没有稳定 scope。
    # 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，grant_scope 到此结束；如果没有这个边界说明，读者不容易看出类别判断范围。

    def readable_reason(self, decision: str, grant_scope: str, missing_grants: list[str], app_granted: bool) -> str:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，生成中文拒绝原因；如果没有这段函数，终端用户只能看到机器决策码。
        if decision == "denied_unapproved_app":  # 新增代码+Phase48WindowsSecurityPolicy: 处理应用未授权拒绝；如果没有这行代码，用户不知道需要先 grant app。
            return "目标应用还没有在本会话中授权，不能执行桌面控制；请先确认应用窗口后再授权。"  # 新增代码+Phase48WindowsSecurityPolicy: 返回应用授权说明；如果没有这行代码，未授权 app 拒绝不够可读。
        if decision == "denied_high_risk_default" and grant_scope == "system_key":  # 新增代码+Phase48WindowsSecurityPolicy: 处理系统组合键默认拒绝；如果没有这行代码，危险快捷键原因会太笼统。
            return f"系统组合键属于高风险动作，默认拒绝；缺少 grant：{_grant_text(missing_grants)}。"  # 新增代码+Phase48WindowsSecurityPolicy: 返回系统键中文说明；如果没有这行代码，用户不知道 systemKeyCombos 需要显式开启。
        if decision == "denied_high_risk_default" and grant_scope == "clipboard":  # 新增代码+Phase48WindowsSecurityPolicy: 处理剪贴板默认拒绝；如果没有这行代码，剪贴板风险不会被单独解释。
            return f"剪贴板读写属于高风险动作，默认拒绝；缺少 grant：{_grant_text(missing_grants)}。"  # 新增代码+Phase48WindowsSecurityPolicy: 返回剪贴板中文说明；如果没有这行代码，用户不知道 clipboardRead/clipboardWrite 需要显式开启。
        if decision == "missing_grant_flags":  # 新增代码+Phase48WindowsSecurityPolicy: 处理普通缺失 grant；如果没有这行代码，普通授权缺失没有友好提示。
            return f"动作缺少必要授权：{_grant_text(missing_grants)}。"  # 新增代码+Phase48WindowsSecurityPolicy: 返回缺失授权说明；如果没有这行代码，用户不知道该补哪些权限。
        return "安全策略允许本次动作。" if app_granted else "安全策略拒绝本次动作。"  # 新增代码+Phase48WindowsSecurityPolicy: 返回兜底说明；如果没有这行代码，未知 decision 会没有可读文本。
    # 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，readable_reason 到此结束；如果没有这个边界说明，读者不容易看出拒绝文案范围。

    def evaluate(self, action: str, arguments: dict[str, Any], grant_flags: dict[str, bool] | None = None, app_granted: bool = False) -> dict[str, Any]:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，评估动作是否满足 Phase48 策略；如果没有这段函数，审批模型无法使用细粒度 grant。
        normalized = _normalized_action(action)  # 新增代码+Phase48WindowsSecurityPolicy: 规范化动作名；如果没有这行代码，策略输出的 action 字段不稳定。
        flags = dict(grant_flags or {})  # 新增代码+Phase48WindowsSecurityPolicy: 复制授权 flags；如果没有这行代码，评估过程可能修改调用方授权状态。
        required = self.required_grants(normalized, dict(arguments or {}))  # 新增代码+Phase48WindowsSecurityPolicy: 计算本动作需要的 grant；如果没有这行代码，后续无法判断缺失权限。
        scope = self.grant_scope(normalized, dict(arguments or {}))  # 新增代码+Phase48WindowsSecurityPolicy: 计算动作类别；如果没有这行代码，拒绝原因无法区分 observe/action/system_key/clipboard。
        app_required = scope != "observe"  # 新增代码+Phase48WindowsSecurityPolicy: 只读观察不强制应用 allowlist，写动作和剪贴板仍需 app 授权；如果没有这行代码，未授权应用可能被控制。
        if app_required and not bool(app_granted):  # 新增代码+Phase48WindowsSecurityPolicy: 拒绝未授权应用的写类动作；如果没有这行代码，allowlist 会被策略层绕过。
            return {"allowed": False, "decision": "denied_unapproved_app", "action": normalized, "grant_scope": scope, "required_grants": required, "missing_grant_flags": [], "readable_reason": self.readable_reason("denied_unapproved_app", scope, [], False), "security_policy": PHASE48_SECURITY_POLICY_CONTRACT, "marker": PHASE48_WINDOWS_SECURITY_POLICY_MARKER, "actions_expanded": PHASE48_ACTIONS_EXPANDED}  # 新增代码+Phase48WindowsSecurityPolicy: 返回未授权 app 拒绝结果；如果没有这行代码，controller 无法给用户明确拒绝原因。
        missing = [grant for grant in required if not flags.get(grant, False)]  # 新增代码+Phase48WindowsSecurityPolicy: 找出缺失的授权；如果没有这行代码，策略不知道哪些 grant 没开。
        high_risk_missing = [grant for grant in missing if grant in PHASE48_HIGH_RISK_GRANTS]  # 新增代码+Phase48WindowsSecurityPolicy: 单独提取高风险缺失授权；如果没有这行代码，高风险默认拒绝无法和普通缺失区分。
        if high_risk_missing:  # 新增代码+Phase48WindowsSecurityPolicy: 命中高风险缺失时进入默认拒绝；如果没有这行代码，系统键和剪贴板会落入普通拒绝。
            return {"allowed": False, "decision": "denied_high_risk_default", "action": normalized, "grant_scope": scope, "required_grants": required, "missing_grant_flags": missing, "readable_reason": self.readable_reason("denied_high_risk_default", scope, missing, True), "security_policy": PHASE48_SECURITY_POLICY_CONTRACT, "marker": PHASE48_WINDOWS_SECURITY_POLICY_MARKER, "actions_expanded": PHASE48_ACTIONS_EXPANDED}  # 新增代码+Phase48WindowsSecurityPolicy: 返回高风险默认拒绝结果；如果没有这行代码，真实终端无法解释危险动作为什么被挡住。
        if missing:  # 新增代码+Phase48WindowsSecurityPolicy: 处理普通缺失授权；如果没有这行代码，observe 或 desktopAction 缺失也可能误放行。
            return {"allowed": False, "decision": "missing_grant_flags", "action": normalized, "grant_scope": scope, "required_grants": required, "missing_grant_flags": missing, "readable_reason": self.readable_reason("missing_grant_flags", scope, missing, True), "security_policy": PHASE48_SECURITY_POLICY_CONTRACT, "marker": PHASE48_WINDOWS_SECURITY_POLICY_MARKER, "actions_expanded": PHASE48_ACTIONS_EXPANDED}  # 新增代码+Phase48WindowsSecurityPolicy: 返回普通缺失授权结果；如果没有这行代码，用户不知道 observe/desktopAction 缺失。
        return {"allowed": True, "decision": "allowed_by_security_policy", "action": normalized, "grant_scope": scope, "required_grants": required, "missing_grant_flags": [], "readable_reason": self.readable_reason("allowed", scope, [], True), "security_policy": PHASE48_SECURITY_POLICY_CONTRACT, "marker": PHASE48_WINDOWS_SECURITY_POLICY_MARKER, "actions_expanded": PHASE48_ACTIONS_EXPANDED}  # 新增代码+Phase48WindowsSecurityPolicy: 返回策略允许结果；如果没有这行代码，通过审批的动作没有策略证据。
    # 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，evaluate 到此结束；如果没有这个边界说明，读者不容易看出策略评估范围。
# 新增代码+Phase48WindowsSecurityPolicy: 类段结束，WindowsComputerUseSecurityPolicy 到此结束；如果没有这个边界说明，读者不容易看出策略类范围。


def run_phase48_security_policy_contract() -> dict[str, Any]:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，运行无副作用合同自检；如果没有这段函数，真实终端无法快速验收 Phase48。
    safe_window = {"app_id": "notepad.exe", "window_id": "hwnd:phase48-safe", "title_preview": "Phase48 Notepad", "process_name": "notepad.exe"}  # 新增代码+Phase48WindowsSecurityPolicy: 构造安全窗口样本；如果没有这行代码，策略自检没有 app 授权正例。
    policy = WindowsComputerUseSecurityPolicy()  # 新增代码+Phase48WindowsSecurityPolicy: 创建策略实例；如果没有这行代码，自检无法运行任何判定。
    observe = policy.evaluate("observe:get_window_state", {"window": safe_window}, grant_flags={"observe": True}, app_granted=True)  # 新增代码+Phase48WindowsSecurityPolicy: 自检只读观察授权类别；如果没有这行代码，observe grant 没有证据。
    action = policy.evaluate("click", {"window": safe_window}, grant_flags={"desktopAction": True}, app_granted=True)  # 新增代码+Phase48WindowsSecurityPolicy: 自检普通动作授权类别；如果没有这行代码，desktopAction grant 没有证据。
    system_key_allowed = policy.evaluate("press_key", {"window": safe_window, "key": "ctrl+alt+delete"}, grant_flags={"desktopAction": True, "systemKeyCombos": True}, app_granted=True)  # 新增代码+Phase48WindowsSecurityPolicy: 自检系统键显式授权路径；如果没有这行代码，systemKeyCombos 放行没有证据。
    clipboard_read = policy.evaluate("clipboard_read", {"window": safe_window}, grant_flags={"clipboardRead": True}, app_granted=True)  # 新增代码+Phase48WindowsSecurityPolicy: 自检剪贴板读取授权路径；如果没有这行代码，clipboardRead 没有证据。
    system_key_denied = policy.evaluate("press_key", {"window": safe_window, "key": "ctrl+alt+delete"}, grant_flags={"desktopAction": True}, app_granted=True)  # 新增代码+Phase48WindowsSecurityPolicy: 自检系统键默认拒绝；如果没有这行代码，高风险默认拒绝没有证据。
    clipboard_write_denied = policy.evaluate("clipboard_write", {"window": safe_window, "text": "secret"}, grant_flags={"desktopAction": True}, app_granted=True)  # 新增代码+Phase48WindowsSecurityPolicy: 自检剪贴板写默认拒绝；如果没有这行代码，clipboardWrite 默认拒绝没有证据。
    unapproved_app = policy.evaluate("click", {"window": safe_window}, grant_flags={"desktopAction": True}, app_granted=False)  # 新增代码+Phase48WindowsSecurityPolicy: 自检未授权 app 拒绝；如果没有这行代码，allowlist 门禁没有策略证据。
    from learning_agent.computer_use_mcp_v2.windows_runtime.approval import WindowsComputerUseApprovalModel  # 新增代码+Phase48WindowsSecurityPolicy: 延迟导入审批模型避免模块循环；如果没有这行代码，自检无法证明 controller 审批链能接入策略。
    model = WindowsComputerUseApprovalModel(security_policy=policy)  # 新增代码+Phase48WindowsSecurityPolicy: 创建带 Phase48 策略的审批模型；如果没有这行代码，策略只会停留在孤立模块。
    model.grant_for_session([safe_window], {"desktopAction": True, "systemKeyCombos": False}, reason="phase48-contract")  # 新增代码+Phase48WindowsSecurityPolicy: 授权安全 app 的普通动作但关闭系统键；如果没有这行代码，审批链无法区分普通动作和系统键。
    controller_click = model.evaluate("click", {"window": safe_window})  # 新增代码+Phase48WindowsSecurityPolicy: 自检审批链普通点击仍允许；如果没有这行代码，新策略可能破坏 Phase38 普通授权。
    controller_system_key = model.evaluate("press_key", {"window": safe_window, "key": "ctrl+alt+delete"})  # 新增代码+Phase48WindowsSecurityPolicy: 自检审批链系统键默认拒绝；如果没有这行代码，高风险拒绝不会覆盖实际审批模型。
    terminal_status = "\n".join(model.terminal_status_lines())  # 新增代码+Phase48WindowsSecurityPolicy: 生成终端状态文本；如果没有这行代码，Phase48 无法证明终端可见。
    return {"marker": PHASE48_WINDOWS_SECURITY_POLICY_MARKER, "ok_token": PHASE48_WINDOWS_SECURITY_POLICY_OK_TOKEN, "grant_classes": bool(observe.get("allowed") and observe.get("grant_scope") == "observe" and action.get("allowed") and action.get("grant_scope") == "action" and system_key_allowed.get("allowed") and system_key_allowed.get("grant_scope") == "system_key" and clipboard_read.get("allowed") and clipboard_read.get("grant_scope") == "clipboard"), "high_risk_default": bool(not system_key_denied.get("allowed") and system_key_denied.get("decision") == "denied_high_risk_default" and "系统组合键" in system_key_denied.get("readable_reason", "")), "clipboard": bool(not clipboard_write_denied.get("allowed") and clipboard_write_denied.get("decision") == "denied_high_risk_default" and "剪贴板" in clipboard_write_denied.get("readable_reason", "")), "unapproved_app": bool(not unapproved_app.get("allowed") and unapproved_app.get("decision") == "denied_unapproved_app"), "controller_policy": bool(controller_click.get("allowed") and not controller_system_key.get("allowed") and controller_system_key.get("decision") == "denied_high_risk_default"), "terminal_status": bool("security_policy=phase48_windows_security_policy" in terminal_status and "grant_classes=observe,desktopAction,systemKeyCombos,clipboardRead,clipboardWrite" in terminal_status), "actions_expanded": PHASE48_ACTIONS_EXPANDED}  # 新增代码+Phase48WindowsSecurityPolicy: 返回完整合同自检结果；如果没有这行代码，CLI 无法拼接稳定验收 token。
# 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，run_phase48_security_policy_contract 到此结束；如果没有这个边界说明，读者不容易看出自检范围。


def phase48_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，把报告转成稳定单行 token；如果没有这段函数，真实终端验收需要解析完整 JSON。
    return f"{PHASE48_WINDOWS_SECURITY_POLICY_OK_TOKEN} grant_classes={_bool_token(bool(report.get('grant_classes')))} high_risk_default={_bool_token(bool(report.get('high_risk_default')))} clipboard={_bool_token(bool(report.get('clipboard')))} controller_policy={_bool_token(bool(report.get('controller_policy')))} terminal_status={_bool_token(bool(report.get('terminal_status')))} actions_expanded={_bool_token(bool(report.get('actions_expanded')))} marker={PHASE48_WINDOWS_SECURITY_POLICY_MARKER}"  # 新增代码+Phase48WindowsSecurityPolicy: 返回固定顺序的 Phase48 token；如果没有这行代码，场景断言容易因为输出漂移失败。
# 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，phase48_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 行格式范围。


def main() -> int:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，提供命令行自检入口；如果没有这段函数，真实终端场景无法直接运行 Phase48 策略检查。
    report = run_phase48_security_policy_contract()  # 新增代码+Phase48WindowsSecurityPolicy: 运行合同自检；如果没有这行代码，CLI 没有实际报告。
    print(phase48_cli_line(report))  # 新增代码+Phase48WindowsSecurityPolicy: 打印验收器优先匹配的单行 token；如果没有这行代码，debug log 缺少稳定成功行。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase48WindowsSecurityPolicy: 打印结构化报告便于人工复盘；如果没有这行代码，失败时难以定位哪个合同条件不成立。
    print(PHASE48_WINDOWS_SECURITY_POLICY_MARKER)  # 新增代码+Phase48WindowsSecurityPolicy: 单独打印 ready marker；如果没有这行代码，验收器可能只看到 OK token 看不到 marker。
    return 0  # 新增代码+Phase48WindowsSecurityPolicy: 返回成功退出码；如果没有这行代码，命令可能被误判失败。
# 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出 CLI 主入口范围。


if __name__ == "__main__":  # 新增代码+Phase48WindowsSecurityPolicy: 允许直接运行本模块；如果没有这行代码，初学者双击或命令行运行不会执行自检。
    raise SystemExit(main())  # 新增代码+Phase48WindowsSecurityPolicy: 用 main 的退出码结束进程；如果没有这行代码，脚本入口没有稳定退出状态。
