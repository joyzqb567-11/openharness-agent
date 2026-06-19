"""Windows Computer Use 审批模型。"""  # 新增代码+Phase38WindowsComputerApproval: 标明本文件专门负责 Windows 桌面控制审批；如果没有这行代码，读者不知道 approval 能力集中在哪里。
from __future__ import annotations  # 新增代码+Phase38WindowsComputerApproval: 延迟解析类型注解，避免类和函数顺序影响运行；如果没有这行代码，后续类型提示在旧路径里更容易出导入问题。

import hashlib  # 新增代码+Phase38WindowsComputerApproval: 导入哈希工具用于生成稳定授权 id 辅助信息；如果没有这行代码，授权记录只能依赖不稳定文本。
import json  # 新增代码+Phase38WindowsComputerApproval: 导入 JSON 工具用于 CLI 自检输出结构化报告；如果没有这行代码，验收器难以读取完整合同结果。
from typing import Any  # 新增代码+Phase38WindowsComputerApproval: 导入 Any 表示来自工具参数的动态字典；如果没有这行代码，审批模型接口类型会不清楚。

try:  # 新增代码+Phase48WindowsSecurityPolicy: 优先按包路径导入 Phase48 细粒度安全策略；如果没有这行代码，approval 无法可选接入 observe/action/system_key/clipboard grant。
    from learning_agent.computer_use_mcp_v2.windows_runtime.security_policy import WindowsComputerUseSecurityPolicy  # 新增代码+Phase48WindowsSecurityPolicy: 导入安全策略类用于审批模型注入；如果没有这行代码，Phase48 策略只能孤立自检不能进入 controller 链路。
except ModuleNotFoundError as error:  # 新增代码+Phase48WindowsSecurityPolicy: 兼容 start_oauth_agent.bat 脚本模式下包名前缀不可用；如果没有这行代码，真实终端直接运行可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.security_policy"}:  # 新增代码+Phase48WindowsSecurityPolicy: 只允许包路径缺失时 fallback；如果没有这行代码，security_policy 内部真实 bug 会被误吞。
        raise  # 新增代码+Phase48WindowsSecurityPolicy: 重新抛出非路径类导入错误；如果没有这行代码，排查策略模块问题会很困难。
    from computer_use_mcp_v2.windows_runtime.security_policy import WindowsComputerUseSecurityPolicy  # 新增代码+Phase48WindowsSecurityPolicy: 脚本模式从本地包导入安全策略；如果没有这行代码，bat 入口无法加载 Phase48 审批策略。

PHASE38_WINDOWS_COMPUTER_APPROVAL_MARKER = "PHASE38_WINDOWS_COMPUTER_APPROVAL_READY"  # 新增代码+Phase38WindowsComputerApproval: 定义阶段完成 marker；如果没有这行代码，真实终端验收无法稳定匹配 Phase38。
PHASE38_WINDOWS_COMPUTER_APPROVAL_OK_TOKEN = "PHASE38_WINDOWS_COMPUTER_APPROVAL_OK"  # 新增代码+Phase38WindowsComputerApproval: 定义 CLI 成功 token；如果没有这行代码，验收脚本无法确认合同自检已运行。
PHASE38_APPROVAL_CONTRACT = "phase38_windows_computer_approval"  # 新增代码+Phase38WindowsComputerApproval: 定义审批模型合同名称；如果没有这行代码，状态输出无法说明当前使用哪版审批逻辑。
PHASE38_ACTIONS_EXPANDED = False  # 新增代码+Phase38WindowsComputerApproval: 明确 Phase38 不扩大真实动作面；如果没有这行代码，用户可能误以为本阶段新增了更多可执行动作。
WINDOWS_PERMISSION_UI_PROMPT_VERSION = "windows-permission-ui-v1"  # 新增代码+Windows权限UI对齐: 定义 Windows 权限提示版本；如果没有这行代码，终端状态无法证明当前已经切到 ClaudeCode 对齐版权限面板。
DEFAULT_GRANT_FLAGS: dict[str, bool] = {"observe": True, "desktopAction": True, "clipboardRead": False, "clipboardWrite": False, "systemKeyCombos": False}  # 修改代码+Phase48WindowsSecurityPolicy: 把 grant flags 扩展为 observe/action/system_key/clipboard 类别且高风险默认关闭；如果没有这行代码，Phase48 无法区分只读观察、普通动作和危险权限。
FORBIDDEN_TARGET_PATTERNS: dict[str, tuple[str, ...]] = {"shell": ("powershell.exe", "powershell", "pwsh.exe", "cmd.exe", "command prompt", "windows terminal", "windowsterminal.exe", "wt.exe"), "codex_ui": ("codex", "openai codex"), "system_settings": ("systemsettings.exe", "settings", "control panel", "regedit", "gpedit", "task manager"), "password_manager": ("password", "credential", "bitwarden", "1password", "keepass"), "auth": ("otp", "two-factor", "2fa", "authenticator", "verification code", "captcha", "login")}  # 新增代码+Phase38WindowsComputerApproval: 定义禁止自动化的高风险窗口关键词；如果没有这行代码，终端/密码/认证等目标可能被误放行。
SYSTEM_KEY_COMBO_TOKENS: tuple[str, ...] = ("ctrl+alt+delete", "win+", "windows+", "meta+", "super+", "cmd+", "alt+tab", "alt+f4", "ctrl+shift+esc", "taskmgr")  # 修改代码+ClaudeCodeParity: 定义需要额外授权的系统级组合键和 win 别名；如果没有这行代码，Alt+F4 或 meta/super/cmd 组合可能绕过 grant flag。


def _bool_token(value: bool) -> str:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，把布尔值转成小写 token；如果没有这段函数，CLI 输出容易出现 True/False 大小写不稳定。
    return "true" if bool(value) else "false"  # 新增代码+Phase38WindowsComputerApproval: 返回验收器期望的小写布尔文本；如果没有这行代码，场景断言会因为大小写不一致失败。
# 新增代码+Phase38WindowsComputerApproval: 函数段结束，_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化 helper 范围。


def _safe_text(value: Any, limit: int = 160) -> str:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，生成安全短文本；如果没有这段函数，窗口摘要可能把过长标题直接塞进日志。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase38WindowsComputerApproval: 把任意值转成单行字符串；如果没有这行代码，终端状态可能被换行污染。
    return text[:limit]  # 新增代码+Phase38WindowsComputerApproval: 限制摘要长度；如果没有这行代码，过长窗口标题会挤爆终端状态和日志。
# 新增代码+Phase38WindowsComputerApproval: 函数段结束，_safe_text 到此结束；如果没有这个边界说明，读者不容易看出文本脱敏 helper 范围。


def _window_field(window: Any, name: str) -> Any:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，兼容 dict 和对象两种窗口输入；如果没有这段函数，审批模型只能处理一种窗口格式。
    if isinstance(window, dict):  # 新增代码+Phase38WindowsComputerApproval: 判断窗口是否是普通字典；如果没有这行代码，测试和工具传入的 dict 会取不到字段。
        return window.get(name, "")  # 新增代码+Phase38WindowsComputerApproval: 从字典读取字段；如果没有这行代码，app_id/title 等摘要会丢失。
    return getattr(window, name, "")  # 新增代码+Phase38WindowsComputerApproval: 从对象读取字段；如果没有这行代码，未来强类型窗口对象无法复用审批模型。
# 新增代码+Phase38WindowsComputerApproval: 函数段结束，_window_field 到此结束；如果没有这个边界说明，读者不容易看出窗口字段读取范围。


def _target_summary(window: Any) -> dict[str, str]:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，生成不会泄露输入正文的窗口摘要；如果没有这段函数，审批结果无法解释目标是谁。
    return {"app_id": _safe_text(_window_field(window, "app_id"), 120), "process_name": _safe_text(_window_field(window, "process_name"), 120), "title_preview": _safe_text(_window_field(window, "title_preview"), 160), "window_id": _safe_text(_window_field(window, "window_id"), 120)}  # 新增代码+Phase38WindowsComputerApproval: 返回可审计但有限长度的目标摘要；如果没有这行代码，拒绝原因没有可读目标信息。
# 新增代码+Phase38WindowsComputerApproval: 函数段结束，_target_summary 到此结束；如果没有这个边界说明，读者不容易看出摘要生成范围。


def _app_key(window: Any) -> str:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，生成 session allowlist 使用的 app key；如果没有这段函数，授权无法和后续动作稳定匹配。
    summary = _target_summary(window)  # 新增代码+Phase38WindowsComputerApproval: 复用安全摘要读取 app 信息；如果没有这行代码，app key 逻辑会和状态摘要分叉。
    raw_key = summary["process_name"] or summary["app_id"] or summary["title_preview"]  # 新增代码+Phase38WindowsComputerApproval: 优先用进程名，其次 app_id 和标题；如果没有这行代码，缺少 process_name 的窗口无法授权。
    return raw_key.lower().strip()  # 新增代码+Phase38WindowsComputerApproval: 统一小写去空格便于匹配；如果没有这行代码，同一 app 可能因为大小写不同重复授权。
# 新增代码+Phase38WindowsComputerApproval: 函数段结束，_app_key 到此结束；如果没有这个边界说明，读者不容易看出 app 匹配规则范围。


def _action_key_combo_text(arguments: dict[str, Any]) -> str:  # 新增代码+ClaudeCodeParity: 函数段开始，把 key 字符串和 keys 数组统一成组合键文本；如果没有这段函数，hold_key 的数组参数会绕过审批层系统键检查。
    raw_keys = dict(arguments or {}).get("keys")  # 新增代码+ClaudeCodeParity: 优先读取 hold_key 的 keys 数组；如果没有这行代码，ClaudeCode parity 组合键列表无法参与风险判断。
    if isinstance(raw_keys, list):  # 新增代码+ClaudeCodeParity: 判断 keys 是否为列表；如果没有这行代码，字符串 keys 可能被错误按字符处理。
        cleaned = [_safe_text(item, 80).lower() for item in raw_keys if _safe_text(item, 80)]  # 新增代码+ClaudeCodeParity: 清洗键名并转小写；如果没有这行代码，大小写和空键会导致系统组合键漏检。
        return "+".join(cleaned)  # 新增代码+ClaudeCodeParity: 拼成 ctrl+alt+delete 这样的风险 token 形态；如果没有这行代码，既有 SYSTEM_KEY_COMBO_TOKENS 无法复用。
    return _safe_text(dict(arguments or {}).get("key", ""), 120).lower()  # 新增代码+ClaudeCodeParity: 回退读取旧 key 字符串；如果没有这行代码，press_key 和兼容 hold_key 字符串会失去检查。
# 新增代码+ClaudeCodeParity: 函数段结束，_action_key_combo_text 到此结束；如果没有这个边界说明，初学者不容易看出组合键文本来源范围。


def _classify_forbidden_target(window: Any) -> str | None:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，识别禁止自动化目标；如果没有这段函数，审批模型无法阻止终端和敏感窗口。
    summary = _target_summary(window)  # 新增代码+Phase38WindowsComputerApproval: 先生成安全摘要；如果没有这行代码，分类逻辑会直接依赖原始窗口对象。
    searchable = " ".join(summary.values()).lower()  # 新增代码+Phase38WindowsComputerApproval: 把摘要合并成可搜索文本；如果没有这行代码，关键词匹配要重复写多次。
    for category, patterns in FORBIDDEN_TARGET_PATTERNS.items():  # 新增代码+Phase38WindowsComputerApproval: 遍历所有高风险分类；如果没有这行代码，只能识别单一风险类型。
        if any(pattern in searchable for pattern in patterns):  # 新增代码+Phase38WindowsComputerApproval: 只要命中关键词就视为禁用目标；如果没有这行代码，PowerShell 等窗口不会被拦截。
            return category  # 新增代码+Phase38WindowsComputerApproval: 返回命中的风险分类；如果没有这行代码，拒绝结果无法说明为什么危险。
    return None  # 新增代码+Phase38WindowsComputerApproval: 未命中时返回 None 表示可继续检查授权；如果没有这行代码，安全窗口也会被误判。
# 新增代码+Phase38WindowsComputerApproval: 函数段结束，_classify_forbidden_target 到此结束；如果没有这个边界说明，读者不容易看出禁止目标分类范围。


def _required_flags_for_action(action: str, arguments: dict[str, Any]) -> list[str]:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，计算动作需要的额外 grant flags；如果没有这段函数，系统快捷键和普通点击无法区分。
    key_text = _action_key_combo_text(dict(arguments or {}))  # 修改代码+ClaudeCodeParity: 同时读取 key 字符串和 hold_key keys 数组；如果没有这行代码，hold_key 危险数组会绕过 grant flag。
    if str(action) in {"press_key", "hold_key"} and any(token in key_text for token in SYSTEM_KEY_COMBO_TOKENS):  # 修改代码+ClaudeCodeParity: press_key/hold_key 命中系统组合键都要求额外授权；如果没有这行代码，Win+R 或 Ctrl+Alt+Delete 可被普通授权放行。
        return ["systemKeyCombos"]  # 新增代码+Phase38WindowsComputerApproval: 要求显式系统组合键授权；如果没有这行代码，grant flag 不会真正生效。
    return []  # 新增代码+Phase38WindowsComputerApproval: 普通动作不需要额外 flag；如果没有这行代码，安全点击也会被错误拦截。
# 新增代码+Phase38WindowsComputerApproval: 函数段结束，_required_flags_for_action 到此结束；如果没有这个边界说明，读者不容易看出 flag 计算范围。


class WindowsComputerUseApprovalModel:  # 新增代码+Phase38WindowsComputerApproval: 类段开始，保存 Windows Computer Use 会话授权状态；如果没有这个类，审批逻辑只能写成零散函数无法被 controller 注入。
    def __init__(self, session_id: str = "learning-agent-default-session", granted_apps: dict[str, dict[str, Any]] | None = None, grant_flags: dict[str, bool] | None = None, security_policy: Any | None = None) -> None:  # 修改代码+Phase48WindowsSecurityPolicy: 函数段开始，允许可选注入 Phase48 安全策略；如果没有这段函数参数，审批模型无法按 observe/action/system_key/clipboard grant 升级。
        self.session_id = str(session_id or "learning-agent-default-session")  # 新增代码+Phase38WindowsComputerApproval: 保存会话 id；如果没有这行代码，授权记录无法和当前 agent 会话关联。
        self.granted_apps: dict[str, dict[str, Any]] = dict(granted_apps or {})  # 新增代码+Phase38WindowsComputerApproval: 保存已授权 app allowlist；如果没有这行代码，grant_for_session 的结果无法被 evaluate 使用。
        self.grant_flags: dict[str, bool] = dict(DEFAULT_GRANT_FLAGS)  # 新增代码+Phase38WindowsComputerApproval: 先复制默认 flag 状态；如果没有这行代码，危险权限可能没有默认关闭基线。
        self.grant_flags.update({str(key): bool(value) for key, value in dict(grant_flags or {}).items()})  # 新增代码+Phase38WindowsComputerApproval: 合并外部传入 flag；如果没有这行代码，测试或未来 UI 无法注入授权选择。
        self.security_policy = security_policy  # 新增代码+Phase48WindowsSecurityPolicy: 保存可选 Phase48 策略对象；如果没有这行代码，evaluate 无法把细粒度策略接入审批链。
        self.grant_history: list[dict[str, Any]] = []  # 新增代码+Phase38WindowsComputerApproval: 保存授权历史；如果没有这行代码，后续审计无法追踪 grant 来源。
        self.permission_prompt_version = WINDOWS_PERMISSION_UI_PROMPT_VERSION  # 新增代码+Windows权限UI对齐: 保存权限提示版本；如果没有这行代码，`/computer status` 不能告诉用户当前面板版本。
        self.last_permission_decision: dict[str, Any] = {}  # 新增代码+Windows权限UI对齐: 保存最近一次权限决策；如果没有这行代码，用户看不到刚才是允许、拒绝还是部分允许。
        self.denied_decision_count = 0  # 新增代码+Windows权限UI对齐: 统计完全拒绝次数；如果没有这行代码，连续权限失败不会在状态面板中暴露。
    # 修改代码+Phase48WindowsSecurityPolicy: 函数段结束，__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围和策略注入边界。

    def status(self) -> dict[str, Any]:  # 修改代码+Phase48WindowsSecurityPolicy: 函数段开始，返回机器可读审批状态并可附加安全策略状态；如果没有这段函数，controller.status 无法展示 approval 和 policy 边界。
        policy_status = self.security_policy.status() if hasattr(self.security_policy, "status") else {}  # 新增代码+Phase48WindowsSecurityPolicy: 读取可选策略状态；如果没有这行代码，Phase48 策略名称和 grant 类别不会出现在状态对象里。
        status = {"enabled": True, "approval_model": PHASE38_APPROVAL_CONTRACT, "approval_granted_app_count": len(self.granted_apps), "grant_flags": dict(self.grant_flags), "actions_expanded": PHASE38_ACTIONS_EXPANDED, "permission_prompt_version": self.permission_prompt_version, "last_permission_decision": dict(self.last_permission_decision), "denied_decision_count": self.denied_decision_count, "marker": PHASE38_WINDOWS_COMPUTER_APPROVAL_MARKER}  # 修改代码+Windows权限UI对齐: 在旧审批摘要上补充权限面板版本和最近决策；如果没有这行代码，状态接口会继续缺少用户可见的权限 UI 证据。
        if policy_status:  # 新增代码+Phase48WindowsSecurityPolicy: 仅在注入策略时追加 Phase48 字段；如果没有这行代码，未启用策略时会出现误导性状态。
            status["security_policy"] = dict(policy_status)  # 新增代码+Phase48WindowsSecurityPolicy: 写入策略状态副本；如果没有这行代码，机器可读状态拿不到 Phase48 策略证据。
        return status  # 修改代码+Phase48WindowsSecurityPolicy: 返回合并后的审批状态；如果没有这行代码，调用方拿不到状态结果。
    # 修改代码+Phase48WindowsSecurityPolicy: 函数段结束，status 到此结束；如果没有这个边界说明，读者不容易看出状态输出范围。

    def terminal_status_lines(self) -> list[str]:  # 修改代码+Phase48WindowsSecurityPolicy: 函数段开始，生成 `/computer status` 终端可见审批和策略摘要；如果没有这段函数，用户只能通过 JSON 理解安全边界。
        flag_text = ",".join(f"{name}:{_bool_token(value)}" for name, value in sorted(self.grant_flags.items()))  # 新增代码+Phase38WindowsComputerApproval: 把 flags 转成稳定短文本；如果没有这行代码，终端状态难以扫读当前危险权限。
        recent_decision = str(self.last_permission_decision.get("decision", "none") or "none")  # 新增代码+Windows权限UI对齐: 把最近决策压成短文本；如果没有这行代码，终端面板会缺少最关键的允许/拒绝结果。
        lines = ["Computer Use Approval", f"- approval_model={PHASE38_APPROVAL_CONTRACT}", f"- approval_granted_app_count={len(self.granted_apps)}", f"- grant_flags={flag_text}", f"- actions_expanded={_bool_token(PHASE38_ACTIONS_EXPANDED)}", f"- permission_prompt_version={self.permission_prompt_version} last_permission_decision={recent_decision} denied_decision_count={self.denied_decision_count}"]  # 修改代码+Windows权限UI对齐: 在 Phase38 兼容摘要中加入权限 UI 版本和最近决策；如果没有这行代码，真实终端无法验收新权限面板是否上线。
        if hasattr(self.security_policy, "terminal_status_lines"):  # 新增代码+Phase48WindowsSecurityPolicy: 检查是否注入可渲染策略；如果没有这行代码，未启用策略时会调用空对象崩溃。
            lines.extend(self.security_policy.terminal_status_lines(self.grant_flags))  # 新增代码+Phase48WindowsSecurityPolicy: 追加 Phase48 策略面板；如果没有这行代码，真实终端用户看不到 grant_classes 和高风险默认拒绝。
        return lines  # 修改代码+Phase48WindowsSecurityPolicy: 返回审批和策略组合输出；如果没有这行代码，调用方无法打印终端状态。
    # 修改代码+Phase48WindowsSecurityPolicy: 函数段结束，terminal_status_lines 到此结束；如果没有这个边界说明，读者不容易看出终端摘要范围。

    def grant_for_session(self, windows: list[Any], flags: dict[str, bool] | None = None, reason: str = "") -> dict[str, Any]:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，为安全 app 创建本会话授权；如果没有这段函数，安全窗口永远无法被允许。
        grant_id_seed = f"{self.session_id}:{len(self.grant_history) + 1}:{reason}"  # 新增代码+Phase38WindowsComputerApproval: 组装授权 id 种子；如果没有这行代码，grant_id 不够稳定也不便审计。
        grant_id = "phase38-grant-" + hashlib.sha256(grant_id_seed.encode("utf-8")).hexdigest()[:12]  # 新增代码+Phase38WindowsComputerApproval: 生成短哈希授权 id；如果没有这行代码，授权和动作结果难以关联。
        for flag_name, flag_value in dict(flags or {}).items():  # 新增代码+Phase38WindowsComputerApproval: 遍历本次用户选择的 grant flags；如果没有这行代码，systemKeyCombos 等选择不会生效。
            if flag_name in self.grant_flags:  # 新增代码+Phase38WindowsComputerApproval: 只接受已知 flag 名；如果没有这行代码，拼写错误的权限可能污染状态。
                self.grant_flags[flag_name] = bool(flag_value)  # 新增代码+Phase38WindowsComputerApproval: 写入 flag 选择；如果没有这行代码，审批模型不会记住用户授权。
        granted: list[dict[str, str]] = []  # 新增代码+Phase38WindowsComputerApproval: 准备记录成功授权的窗口摘要；如果没有这行代码，调用方不知道哪些 app 被加入 allowlist。
        denied: list[dict[str, Any]] = []  # 新增代码+Phase38WindowsComputerApproval: 准备记录因敏感目标被拒绝的窗口摘要；如果没有这行代码，危险窗口被跳过时没有解释。
        for window in list(windows or []):  # 新增代码+Phase38WindowsComputerApproval: 遍历待授权窗口；如果没有这行代码，传入多个候选 app 时只能处理一个。
            summary = _target_summary(window)  # 新增代码+Phase38WindowsComputerApproval: 生成安全窗口摘要；如果没有这行代码，授权记录可能保存原始敏感对象。
            sentinel_category = _classify_forbidden_target(window)  # 新增代码+Phase38WindowsComputerApproval: 检查窗口是否属于禁止目标；如果没有这行代码，PowerShell 等也能被授权。
            if sentinel_category is not None:  # 新增代码+Phase38WindowsComputerApproval: 判断是否命中禁用分类；如果没有这行代码，禁用结果不会分支处理。
                denied.append({"target_summary": summary, "sentinel_category": sentinel_category})  # 新增代码+Phase38WindowsComputerApproval: 记录拒绝授权原因；如果没有这行代码，用户不知道哪个窗口被排除。
                continue  # 新增代码+Phase38WindowsComputerApproval: 跳过危险窗口授权；如果没有这行代码，拒绝后仍可能写入 allowlist。
            app_key = _app_key(window)  # 新增代码+Phase38WindowsComputerApproval: 生成 app allowlist key；如果没有这行代码，后续 evaluate 无法匹配授权。
            self.granted_apps[app_key] = {"grant_id": grant_id, "app_key": app_key, "target_summary": summary, "reason": _safe_text(reason, 160)}  # 新增代码+Phase38WindowsComputerApproval: 保存 app 会话授权；如果没有这行代码，安全 app 点击仍会被 requires_approval 拒绝。
            granted.append(summary)  # 新增代码+Phase38WindowsComputerApproval: 记录成功授权摘要；如果没有这行代码，grant 返回缺少用户可读结果。
        decision_name = "allow_for_session" if granted and not denied else "allow_with_denied_targets" if granted else "deny"  # 新增代码+Windows权限UI对齐: 把本次授权结果命名为结构化决策；如果没有这行代码，状态页只能显示零散 granted/denied 列表。
        grant_record = {"grant_id": grant_id, "granted": granted, "denied": denied, "flags": dict(self.grant_flags), "reason": _safe_text(reason, 160), "decision": decision_name, "source": "windows_runtime_policy", "promptVersion": self.permission_prompt_version}  # 修改代码+Windows权限UI对齐: 生成带决策来源和提示版本的授权记录；如果没有这行代码，历史授权无法和新权限面板对应起来。
        self.grant_history.append(grant_record)  # 新增代码+Phase38WindowsComputerApproval: 把授权记录加入历史；如果没有这行代码，后续审计无法追溯授权次数。
        self.last_permission_decision = dict(grant_record)  # 新增代码+Windows权限UI对齐: 保存最近一次授权决策；如果没有这行代码，`/computer status` 无法展示刚才的结果。
        if not granted:  # 新增代码+Windows权限UI对齐: 完全没有授权成功时进入拒绝统计；如果没有这行代码，拒绝次数不会增长。
            self.denied_decision_count += 1  # 新增代码+Windows权限UI对齐: 累计完全拒绝次数；如果没有这行代码，用户无法发现权限请求一直失败。
        return grant_record  # 新增代码+Phase38WindowsComputerApproval: 返回授权结果；如果没有这行代码，调用方无法知道授权是否成功。
    # 新增代码+Phase38WindowsComputerApproval: 函数段结束，grant_for_session 到此结束；如果没有这个边界说明，读者不容易看出授权写入范围。

    def evaluate(self, action: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，评估一次桌面动作是否被本会话授权；如果没有这段函数，controller 无法在后端执行前拦截。
        raw_window = dict(arguments or {}).get("window")  # 新增代码+Phase38WindowsComputerApproval: 从动作参数读取目标窗口；如果没有这行代码，审批无法知道动作指向哪里。
        if str(action) == "screenshot":  # 新增代码+Phase38WindowsComputerApproval: 识别只读截图动作；如果没有这行代码，截图可能被错误要求 app grant。
            return {"allowed": True, "decision": "read_only_action", "approval_model": PHASE38_APPROVAL_CONTRACT, "actions_expanded": PHASE38_ACTIONS_EXPANDED}  # 新增代码+Phase38WindowsComputerApproval: 只读动作不阻断但仍给出审批标签；如果没有这行代码，只读工具会被误拒绝。
        if raw_window is None:  # 新增代码+Phase38WindowsComputerApproval: 检查写动作是否声明窗口；如果没有这行代码，裸坐标动作会绕过 app allowlist。
            return {"allowed": False, "decision": "missing_window_target", "approval_model": PHASE38_APPROVAL_CONTRACT, "actions_expanded": PHASE38_ACTIONS_EXPANDED}  # 新增代码+Phase38WindowsComputerApproval: 拒绝缺少窗口的写动作；如果没有这行代码，真实鼠标键盘可能落到未知位置。
        summary = _target_summary(raw_window)  # 新增代码+Phase38WindowsComputerApproval: 生成目标摘要；如果没有这行代码，拒绝结果无法解释目标。
        sentinel_category = _classify_forbidden_target(raw_window)  # 新增代码+Phase38WindowsComputerApproval: 判断目标是否属于禁止自动化窗口；如果没有这行代码，终端和认证窗口可能被误操作。
        if sentinel_category is not None:  # 新增代码+Phase38WindowsComputerApproval: 命中高风险目标时进入拒绝路径；如果没有这行代码，风险分类不会真正拦截。
            return {"allowed": False, "decision": "denied_forbidden_target", "sentinel_category": sentinel_category, "target_summary": summary, "approval_model": PHASE38_APPROVAL_CONTRACT, "actions_expanded": PHASE38_ACTIONS_EXPANDED}  # 新增代码+Phase38WindowsComputerApproval: 返回禁止目标拒绝结果；如果没有这行代码，controller 无法给用户明确拒绝原因。
        app_key = _app_key(raw_window)  # 新增代码+Phase38WindowsComputerApproval: 生成本次动作的 app key；如果没有这行代码，无法查 allowlist。
        grant_record = self.granted_apps.get(app_key)  # 新增代码+Phase38WindowsComputerApproval: 查找会话授权；如果没有这行代码，grant_for_session 永远不会影响 evaluate。
        if grant_record is None:  # 新增代码+Phase38WindowsComputerApproval: 判断 app 是否未授权；如果没有这行代码，未授权 app 可能直接执行。
            return {"allowed": False, "decision": "requires_approval", "target_summary": summary, "approval_model": PHASE38_APPROVAL_CONTRACT, "actions_expanded": PHASE38_ACTIONS_EXPANDED}  # 新增代码+Phase38WindowsComputerApproval: 返回需要用户授权的拒绝结果；如果没有这行代码，UI 无法提示下一步应授权。
        policy_decision: dict[str, Any] | None = None  # 新增代码+Phase48WindowsSecurityPolicy: 准备保存可选策略评估结果；如果没有这行代码，允许结果无法携带 Phase48 审计证据。
        if self.security_policy is not None:  # 新增代码+Phase48WindowsSecurityPolicy: 仅在显式注入策略时启用 Phase48 判定；如果没有这行代码，旧 Phase38 行为会被无意改变。
            policy_decision = self.security_policy.evaluate(str(action), dict(arguments or {}), grant_flags=self.grant_flags, app_granted=True)  # 新增代码+Phase48WindowsSecurityPolicy: 用细粒度 grant 评估本次动作；如果没有这行代码，system_key 和 clipboard 不会被新策略拦截。
            if not bool(policy_decision.get("allowed", False)):  # 新增代码+Phase48WindowsSecurityPolicy: 策略拒绝时立即阻断后端动作；如果没有这行代码，高风险默认拒绝不会真正生效。
                return {"allowed": False, "decision": str(policy_decision.get("decision", "denied_by_security_policy")), "missing_grant_flags": list(policy_decision.get("missing_grant_flags", [])), "readable_reason": str(policy_decision.get("readable_reason", "")), "target_summary": summary, "policy": policy_decision, "approval_model": PHASE38_APPROVAL_CONTRACT, "actions_expanded": PHASE38_ACTIONS_EXPANDED}  # 新增代码+Phase48WindowsSecurityPolicy: 返回带中文原因和策略对象的拒绝结果；如果没有这行代码，controller 无法向用户说明高风险默认拒绝。
        required_flags = _required_flags_for_action(str(action), dict(arguments or {}))  # 新增代码+Phase38WindowsComputerApproval: 计算动作需要的额外权限；如果没有这行代码，系统快捷键不会触发 flag 门禁。
        missing_flags = [flag for flag in required_flags if not self.grant_flags.get(flag, False)]  # 新增代码+Phase38WindowsComputerApproval: 找出尚未授权的危险 flag；如果没有这行代码，缺少 systemKeyCombos 仍会被放行。
        if missing_flags:  # 新增代码+Phase38WindowsComputerApproval: 判断是否有缺失 flag；如果没有这行代码，拒绝路径不会执行。
            return {"allowed": False, "decision": "missing_grant_flags", "missing_grant_flags": missing_flags, "target_summary": summary, "approval_model": PHASE38_APPROVAL_CONTRACT, "actions_expanded": PHASE38_ACTIONS_EXPANDED}  # 新增代码+Phase38WindowsComputerApproval: 返回缺少 grant flag 的拒绝结果；如果没有这行代码，用户不知道要开启哪项权限。
        active_flags = [flag for flag, enabled in sorted(self.grant_flags.items()) if enabled]  # 新增代码+Phase38WindowsComputerApproval: 计算已启用 flags；如果没有这行代码，允许结果无法说明危险权限来源。
        return {"allowed": True, "decision": "allowed_by_session_grant", "grant_id": grant_record.get("grant_id", ""), "grant_flags": active_flags, "target_summary": summary, "policy": policy_decision or {}, "approval_model": PHASE38_APPROVAL_CONTRACT, "actions_expanded": PHASE38_ACTIONS_EXPANDED}  # 修改代码+Phase48WindowsSecurityPolicy: 返回允许结果并携带可选策略证据；如果没有这行代码，controller 无法知道动作已被会话授权和策略允许。
    # 新增代码+Phase38WindowsComputerApproval: 函数段结束，evaluate 到此结束；如果没有这个边界说明，读者不容易看出审批判定范围。
# 新增代码+Phase38WindowsComputerApproval: 类段结束，WindowsComputerUseApprovalModel 到此结束；如果没有这个边界说明，读者不容易看出模型范围。


def run_phase38_approval_contract() -> dict[str, Any]:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，运行无副作用合同自检；如果没有这段函数，真实终端场景没有安全自检入口。
    safe_window = {"app_id": "notepad.exe", "window_id": "hwnd:phase38-safe", "title_preview": "Phase38 Notepad", "process_name": "notepad.exe"}  # 新增代码+Phase38WindowsComputerApproval: 构造安全窗口样本；如果没有这行代码，allowlist 自检没有正例。
    forbidden_window = {"app_id": "powershell.exe", "window_id": "hwnd:phase38-forbidden", "title_preview": "Administrator: Windows PowerShell", "process_name": "powershell.exe"}  # 新增代码+Phase38WindowsComputerApproval: 构造终端窗口样本；如果没有这行代码，禁止目标自检没有反例。
    model = WindowsComputerUseApprovalModel()  # 新增代码+Phase38WindowsComputerApproval: 创建默认审批模型；如果没有这行代码，自检没有状态容器。
    grant = model.grant_for_session([safe_window], {"systemKeyCombos": False}, reason="phase38-contract-safe-app")  # 新增代码+Phase38WindowsComputerApproval: 先授权安全 app 但关闭系统组合键；如果没有这行代码，allowlist 和 flag 门禁都无法自检。
    allowed_click = model.evaluate("click", {"window": safe_window})  # 新增代码+Phase38WindowsComputerApproval: 评估安全点击；如果没有这行代码，无法证明 session grant 会放行普通动作。
    forbidden_click = model.evaluate("click", {"window": forbidden_window})  # 新增代码+Phase38WindowsComputerApproval: 评估终端点击；如果没有这行代码，无法证明 shell 目标会被拦截。
    denied_system_key = model.evaluate("press_key", {"window": safe_window, "key": "ctrl+alt+delete"})  # 新增代码+Phase38WindowsComputerApproval: 评估未授权系统组合键；如果没有这行代码，无法证明 grant flag 默认关闭。
    model.grant_for_session([safe_window], {"systemKeyCombos": True}, reason="phase38-contract-system-keys")  # 新增代码+Phase38WindowsComputerApproval: 再显式授权系统组合键；如果没有这行代码，无法证明 flag 开启后能放行。
    allowed_system_key = model.evaluate("press_key", {"window": safe_window, "key": "ctrl+alt+delete"})  # 新增代码+Phase38WindowsComputerApproval: 再评估同一组合键；如果没有这行代码，flag 放行路径没有证据。
    terminal_status = "\n".join(model.terminal_status_lines())  # 新增代码+Phase38WindowsComputerApproval: 生成终端状态文本；如果没有这行代码，无法证明 `/computer` 风格状态可读。
    return {"marker": PHASE38_WINDOWS_COMPUTER_APPROVAL_MARKER, "ok_token": PHASE38_WINDOWS_COMPUTER_APPROVAL_OK_TOKEN, "grant_id": grant["grant_id"], "allowlist": bool(allowed_click.get("allowed") and allowed_click.get("decision") == "allowed_by_session_grant"), "forbidden_blocked": bool(not forbidden_click.get("allowed") and forbidden_click.get("decision") == "denied_forbidden_target"), "grant_flags": bool(not denied_system_key.get("allowed") and denied_system_key.get("decision") == "missing_grant_flags" and allowed_system_key.get("allowed") and "systemKeyCombos" in allowed_system_key.get("grant_flags", [])), "terminal_status": bool("approval_granted_app_count=1" in terminal_status and "actions_expanded=false" in terminal_status), "actions_expanded": PHASE38_ACTIONS_EXPANDED}  # 新增代码+Phase38WindowsComputerApproval: 返回合同自检结果；如果没有这行代码，CLI 无法拼接稳定 token。
# 新增代码+Phase38WindowsComputerApproval: 函数段结束，run_phase38_approval_contract 到此结束；如果没有这个边界说明，读者不容易看出自检范围。


def phase38_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，把合同报告转成稳定单行；如果没有这段函数，真实终端验收需要解析完整 JSON。
    return f"{PHASE38_WINDOWS_COMPUTER_APPROVAL_OK_TOKEN} allowlist={_bool_token(bool(report.get('allowlist')))} forbidden_blocked={_bool_token(bool(report.get('forbidden_blocked')))} grant_flags={_bool_token(bool(report.get('grant_flags')))} terminal_status={_bool_token(bool(report.get('terminal_status')))} actions_expanded={_bool_token(bool(report.get('actions_expanded')))} marker={PHASE38_WINDOWS_COMPUTER_APPROVAL_MARKER}"  # 新增代码+Phase38WindowsComputerApproval: 返回固定 token 顺序；如果没有这行代码，场景断言容易因为输出漂移失败。
# 新增代码+Phase38WindowsComputerApproval: 函数段结束，phase38_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 行格式范围。


def main() -> int:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，提供 `python -c` 可调用入口；如果没有这段函数，真实终端场景无法安全运行 Phase38 自检。
    report = run_phase38_approval_contract()  # 新增代码+Phase38WindowsComputerApproval: 运行合同自检；如果没有这行代码，CLI 没有真实报告。
    print(phase38_cli_line(report))  # 新增代码+Phase38WindowsComputerApproval: 打印验收器优先匹配的单行 token；如果没有这行代码，debug log 不会有稳定成功行。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase38WindowsComputerApproval: 打印结构化报告便于人工复盘；如果没有这行代码，失败时很难看出哪个合同条件不成立。
    print(PHASE38_WINDOWS_COMPUTER_APPROVAL_MARKER)  # 新增代码+Phase38WindowsComputerApproval: 单独打印阶段 marker；如果没有这行代码，验收器可能只看到 OK token 看不到 ready marker。
    return 0  # 新增代码+Phase38WindowsComputerApproval: 返回成功退出码；如果没有这行代码，终端命令可能被误判失败。
# 新增代码+Phase38WindowsComputerApproval: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出 CLI 主入口范围。


if __name__ == "__main__":  # 新增代码+Phase38WindowsComputerApproval: 允许直接运行本文件；如果没有这行代码，初学者双击或命令行运行不会执行自检。
    raise SystemExit(main())  # 新增代码+Phase38WindowsComputerApproval: 用 main 的退出码结束进程；如果没有这行代码，脚本入口没有稳定退出状态。
