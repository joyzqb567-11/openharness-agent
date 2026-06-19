"""通用 Computer Use 新目标窗口策略。"""  # 新增代码+FreshTargetPolicy：说明本模块负责判断窗口是否是本轮新目标；如果没有这一行，读者不容易知道旧窗口保护入口在哪里。
from __future__ import annotations  # 新增代码+FreshTargetPolicy：启用延迟类型注解；如果没有这一行，复杂类型在脚本入口里更容易受导入顺序影响。

import hashlib  # 新增代码+FreshTargetPolicy：导入哈希库生成窗口身份短指纹；如果没有这一行，策略只能暴露完整标题或路径。
from typing import Any  # 新增代码+FreshTargetPolicy：导入 Any 表示窗口和启动报告来自不同后端；如果没有这一行，策略输入边界不清楚。


FRESH_TARGET_ALLOWED_DECISIONS = {"fresh_target_ready", "single_instance_target_ready", "user_granted_existing_window_ready"}  # 新增代码+FreshTargetPolicy：集中列出允许建立租约的决策；如果没有这一行，多个调用点会各写一套允许条件。
SINGLE_INSTANCE_APP_HINTS = {"wechat", "weixin", "wxwork", "teams", "outlook", "onedrive", "obsidian", "wps", "word", "excel", "powerpoint", "chrome", "msedge", "edge", "firefox", "netease", "cloudmusic"}  # 新增代码+FreshTargetPolicy：保存常见单实例或近似单实例应用提示；如果没有这一行，未知/单实例策略无法给出温和分类。
APPLICATION_ALIAS_GROUPS = ({"wechat", "weixin", "微信"}, {"wxwork", "wecom", "企业微信"}, {"msedge", "edge", "microsoftedge"}, {"wps", "wpsoffice"}, {"netease", "cloudmusic", "neteasecloudmusic", "网易云音乐"})  # 新增代码+FreshTargetPolicy：集中保存常见应用别名组；如果没有这一行，wechat/Weixin 这类同一软件不同名字会被误判为两个应用。


def _fresh_safe_text(value: Any) -> str:  # 新增代码+FreshTargetPolicy：函数段开始，把任意字段转成单行文本；如果没有这段函数，None、数字、换行会污染匹配。
    return str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+FreshTargetPolicy：返回去掉换行和首尾空白的文本；如果没有这一行，窗口标题可能破坏日志结构。
# 新增代码+FreshTargetPolicy：函数段结束，_fresh_safe_text 到此结束；如果没有这个边界说明，用户不容易看出文本清洗范围。


def _fresh_normalize_token(value: Any) -> str:  # 新增代码+FreshTargetPolicy：函数段开始，归一化应用名和进程名；如果没有这段函数，notepad 和 notepad.exe 会被误判不同。
    text = _fresh_safe_text(value).replace("\\", "/").strip("\"'` ").casefold()  # 新增代码+FreshTargetPolicy：统一路径分隔符、引号和大小写；如果没有这一行，路径式 exe 会干扰比较。
    leaf = text.rsplit("/", 1)[-1] if "/" in text else text  # 新增代码+FreshTargetPolicy：只保留最后的文件名片段；如果没有这一行，本地路径会参与匹配并泄露细节。
    for suffix in (".exe", ".lnk", ".appref-ms", ".url"):  # 新增代码+FreshTargetPolicy：遍历 Windows 常见启动后缀；如果没有这一行，快捷方式和真实进程名无法归一。
        if leaf.endswith(suffix):  # 新增代码+FreshTargetPolicy：检查当前后缀是否存在；如果没有这一行，后缀处理会盲目截断文本。
            return leaf[: -len(suffix)]  # 新增代码+FreshTargetPolicy：返回去掉后缀的应用 token；如果没有这一行，wechat.exe 会和 wechat 不相等。
    return leaf  # 新增代码+FreshTargetPolicy：返回归一化后的文件名；如果没有这一行，普通应用名会得到 None。
# 新增代码+FreshTargetPolicy：函数段结束，_fresh_normalize_token 到此结束；如果没有这个边界说明，用户不容易看出应用名规范范围。


def _fresh_alias_tokens(value: Any) -> set[str]:  # 新增代码+FreshTargetPolicy：函数段开始，生成应用 token 的同义别名集合；如果没有这段函数，单实例软件常见别名无法通用匹配。
    token = _fresh_normalize_token(value)  # 新增代码+FreshTargetPolicy：先取得基础归一 token；如果没有这一行，别名扩展没有稳定起点。
    tokens = {token} if token else set()  # 新增代码+FreshTargetPolicy：只在 token 非空时加入集合；如果没有这一行，空字符串会污染匹配。
    for alias_group in APPLICATION_ALIAS_GROUPS:  # 新增代码+FreshTargetPolicy：遍历预设别名组；如果没有这一行，wechat/weixin 不能互相补全。
        normalized_group = {_fresh_normalize_token(alias) for alias in alias_group}  # 新增代码+FreshTargetPolicy：把别名组统一归一化；如果没有这一行，中英文或 exe 差异仍会漏匹配。
        if tokens.intersection(normalized_group):  # 新增代码+FreshTargetPolicy：当前 token 命中别名组时扩展整组；如果没有这一行，别名不会真正生效。
            tokens.update(alias for alias in normalized_group if alias)  # 新增代码+FreshTargetPolicy：把非空别名加入结果；如果没有这一行，策略仍只知道单个名字。
    return tokens  # 新增代码+FreshTargetPolicy：返回扩展后的别名集合；如果没有这一行，调用方拿不到匹配候选。
# 新增代码+FreshTargetPolicy：函数段结束，_fresh_alias_tokens 到此结束；如果没有这个边界说明，用户不容易看出别名扩展范围。


def _fresh_sha256_16(value: Any) -> str:  # 新增代码+FreshTargetPolicy：函数段开始，生成短哈希；如果没有这段函数，窗口身份无法在脱敏后稳定比较。
    text = _fresh_safe_text(value).casefold()  # 新增代码+FreshTargetPolicy：清洗并小写文本；如果没有这一行，大小写差异会导致不同指纹。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16] if text else ""  # 新增代码+FreshTargetPolicy：返回 16 位哈希或空串；如果没有这一行，标题指纹字段不可用。
# 新增代码+FreshTargetPolicy：函数段结束，_fresh_sha256_16 到此结束；如果没有这个边界说明，用户不容易看出脱敏范围。


def _fresh_window_texts(window: dict[str, Any]) -> list[str]:  # 新增代码+FreshTargetPolicy：函数段开始，提取窗口中可用于匹配应用的文本；如果没有这段函数，匹配逻辑会散落各处。
    return [  # 新增代码+FreshTargetPolicy：返回多个候选文本；如果没有这一行，调用方无法统一遍历窗口字段。
        _fresh_safe_text(window.get("app_id")),  # 新增代码+FreshTargetPolicy：加入 app_id；如果没有这一行，标准窗口引用无法匹配目标应用。
        _fresh_safe_text(window.get("process_name")),  # 新增代码+FreshTargetPolicy：加入进程名；如果没有这一行，真实 Win32 窗口可能无法匹配。
        _fresh_safe_text(window.get("window_executable")),  # 新增代码+FreshTargetPolicy：加入窗口可执行名；如果没有这一行，部分后端字段会被漏掉。
        _fresh_safe_text(window.get("title_preview")),  # 新增代码+FreshTargetPolicy：加入标题摘要；如果没有这一行，中文应用标题场景可能无法发现旧窗口。
        _fresh_safe_text(window.get("title")),  # 新增代码+FreshTargetPolicy：加入完整标题；如果没有这一行，只有 title 的旧快照会被漏掉。
        _fresh_safe_text(window.get("name")),  # 新增代码+FreshTargetPolicy：加入通用 name 字段；如果没有这一行，测试和第三方 provider 可能匹配不到。
    ]  # 新增代码+FreshTargetPolicy：结束候选文本列表；如果没有这一行，Python 语法不完整。
# 新增代码+FreshTargetPolicy：函数段结束，_fresh_window_texts 到此结束；如果没有这个边界说明，用户不容易看出文本来源范围。


def _fresh_window_matches_target(window: dict[str, Any], target_app: Any) -> bool:  # 新增代码+FreshTargetPolicy：函数段开始，判断窗口是否属于目标应用；如果没有这段函数，预检无法发现已打开软件。
    target_token = _fresh_normalize_token(target_app)  # 新增代码+FreshTargetPolicy：归一化用户请求的软件名；如果没有这一行，目标名不同写法会误判。
    if not target_token:  # 新增代码+FreshTargetPolicy：检查目标名是否为空；如果没有这一行，空目标可能误匹配所有窗口。
        return False  # 新增代码+FreshTargetPolicy：空目标不匹配任何窗口；如果没有这一行，预检会产生假阳性。
    target_aliases = _fresh_alias_tokens(target_app)  # 新增代码+FreshTargetPolicy：展开目标应用别名；如果没有这一行，微信这类别名窗口可能绕过预检。
    for text in _fresh_window_texts(window):  # 新增代码+FreshTargetPolicy：遍历窗口文本字段；如果没有这一行，只能检查单一字段而漏窗口。
        normalized = _fresh_normalize_token(text)  # 新增代码+FreshTargetPolicy：把窗口字段归一化；如果没有这一行，exe 后缀和大小写会影响匹配。
        window_aliases = _fresh_alias_tokens(text)  # 新增代码+FreshTargetPolicy：展开窗口字段别名；如果没有这一行，Weixin.exe 不会命中 wechat 目标。
        if target_aliases.intersection(window_aliases) or normalized == target_token or (target_token and target_token in normalized.split()):  # 新增代码+FreshTargetPolicy：优先别名/精确匹配并支持标题词命中；如果没有这一行，已打开目标窗口可能被漏掉。
            return True  # 新增代码+FreshTargetPolicy：发现匹配窗口后返回 True；如果没有这一行，预检无法阻止旧窗口接管。
        if normalized.endswith(target_token) and len(target_token) >= 3:  # 新增代码+FreshTargetPolicy：兼容 company.notepad 这类 app_id；如果没有这一行，带命名空间 app_id 会被漏掉。
            return True  # 新增代码+FreshTargetPolicy：命名空间尾部命中也视为匹配；如果没有这一行，Windows 应用 ID 可能误过预检。
    return False  # 新增代码+FreshTargetPolicy：所有字段都不命中时返回 False；如果没有这一行，函数没有稳定返回值。
# 新增代码+FreshTargetPolicy：函数段结束，_fresh_window_matches_target 到此结束；如果没有这个边界说明，用户不容易看出匹配条件范围。


def window_fresh_identity_key(window: dict[str, Any]) -> str:  # 新增代码+FreshTargetPolicy：函数段开始，生成可比较的窗口新鲜度身份；如果没有这段函数，启动前后无法判断是不是同一旧窗口。
    safe_window = dict(window or {}) if isinstance(window, dict) else {}  # 新增代码+FreshTargetPolicy：复制窗口字典并容错；如果没有这一行，坏输入可能让策略崩溃。
    app_token = _fresh_normalize_token(safe_window.get("app_id") or safe_window.get("process_name") or safe_window.get("window_executable"))  # 新增代码+FreshTargetPolicy：提取应用身份；如果没有这一行，不同应用同 hwnd 的异常数据难以区分。
    pid_text = _fresh_safe_text(safe_window.get("pid") or safe_window.get("window_process_id") or safe_window.get("process_id"))  # 新增代码+FreshTargetPolicy：提取进程 id；如果没有这一行，同应用不同进程无法区分。
    window_id = _fresh_safe_text(safe_window.get("window_id") or safe_window.get("hwnd") or safe_window.get("id"))  # 新增代码+FreshTargetPolicy：提取窗口 id 或 hwnd；如果没有这一行，同进程多窗口无法区分。
    title_hash = _fresh_safe_text(safe_window.get("title_sha256_16")) or _fresh_sha256_16(safe_window.get("title_preview") or safe_window.get("title"))  # 新增代码+FreshTargetPolicy：提取或生成标题哈希；如果没有这一行，恢复旧窗口和新空白窗口难以审计。
    return "|".join([app_token, pid_text, window_id, title_hash])  # 新增代码+FreshTargetPolicy：拼成稳定身份键；如果没有这一行，启动前后窗口列表无法做集合比较。
# 新增代码+FreshTargetPolicy：函数段结束，window_fresh_identity_key 到此结束；如果没有这个边界说明，用户不容易看出身份键组成范围。


def detect_existing_target_windows(target_app: Any, windows: list[dict[str, Any]] | None) -> list[dict[str, Any]]:  # 新增代码+FreshTargetPolicy：函数段开始，从窗口列表中找目标应用旧窗口；如果没有这段函数，controller 不能做启动前预检。
    safe_windows = [dict(window) for window in list(windows or []) if isinstance(window, dict)]  # 新增代码+FreshTargetPolicy：复制有效窗口列表；如果没有这一行，外部快照可能被策略污染。
    return [window for window in safe_windows if _fresh_window_matches_target(window, target_app)]  # 新增代码+FreshTargetPolicy：返回与目标应用匹配的窗口；如果没有这一行，预检无法知道是否已有软件打开。
# 新增代码+FreshTargetPolicy：函数段结束，detect_existing_target_windows 到此结束；如果没有这个边界说明，用户不容易看出旧窗口筛选范围。


def is_known_single_instance_candidate(target_app: Any, window: dict[str, Any] | None = None) -> bool:  # 新增代码+FreshTargetPolicy：函数段开始，判断应用是否像单实例应用；如果没有这段函数，微信这类应用无法被温和解释。
    tokens = _fresh_alias_tokens(target_app)  # 新增代码+FreshTargetPolicy：先加入用户请求目标及其别名 token；如果没有这一行，只能依赖窗口字段。
    for text in _fresh_window_texts(dict(window or {})):  # 新增代码+FreshTargetPolicy：遍历窗口文本补充 token；如果没有这一行，真实窗口里的 Weixin.exe 无法被识别。
        normalized = _fresh_normalize_token(text)  # 新增代码+FreshTargetPolicy：归一化窗口字段；如果没有这一行，exe 后缀会干扰判断。
        if normalized:  # 新增代码+FreshTargetPolicy：只加入非空 token；如果没有这一行，空字符串会污染集合。
            tokens.add(normalized)  # 新增代码+FreshTargetPolicy：保存候选 token；如果没有这一行，单实例判断信息不足。
            tokens.update(_fresh_alias_tokens(normalized))  # 新增代码+FreshTargetPolicy：同步加入窗口字段别名；如果没有这一行，Weixin.exe 仍可能无法命中 wechat 组。
    return any(token in SINGLE_INSTANCE_APP_HINTS for token in tokens if token)  # 新增代码+FreshTargetPolicy：命中提示集合时返回 True；如果没有这一行，单实例分类永远不可用。
# 新增代码+FreshTargetPolicy：函数段结束，is_known_single_instance_candidate 到此结束；如果没有这个边界说明，用户不容易看出单实例判断范围。


def decide_fresh_target_preflight(target_app: Any, windows: list[dict[str, Any]] | None, *, explicit_existing_window_request: bool = False, user_authorized_window: bool = False) -> dict[str, Any]:  # 新增代码+FreshTargetPolicy：函数段开始，启动前决定是否允许打开目标应用；如果没有这段函数，旧窗口会在启动前被忽略。
    existing_windows = detect_existing_target_windows(target_app, windows)  # 新增代码+FreshTargetPolicy：查找当前已经打开的目标应用窗口；如果没有这一行，预检不知道是否要提醒用户关闭。
    existing_keys = [window_fresh_identity_key(window) for window in existing_windows]  # 新增代码+FreshTargetPolicy：生成旧窗口身份列表；如果没有这一行，启动后无法证明是否复用了旧窗口。
    if existing_windows and user_authorized_window and explicit_existing_window_request:  # 新增代码+FreshTargetPolicy：用户明确要求并授权已有窗口时允许；如果没有这一行，合法接管旧窗口场景不可用。
        return {"allowed": True, "decision": "user_granted_existing_window_ready", "fresh_target_class": "user_granted_existing_window", "origin": "user_granted_existing_window", "existing_target_window_count": len(existing_windows), "existing_target_window_keys": existing_keys, "requires_user_to_close_existing_app": False, "allows_explicit_existing_window_authorization": True, "message": "用户已明确授权使用当前已有窗口。", "low_level_event_count": 0}  # 新增代码+FreshTargetPolicy：返回用户授权旧窗口放行报告；如果没有这一行，controller 无法区分授权和误接管。
    if existing_windows:  # 新增代码+FreshTargetPolicy：发现未授权旧窗口时进入阻断；如果没有这一行，默认会接管用户正在使用的软件。
        return {"allowed": False, "decision": "existing_target_window_requires_user_close_or_authorize", "fresh_target_class": "preexisting_target_window", "origin": "blocked_preexisting_window", "existing_target_window_count": len(existing_windows), "existing_target_window_keys": existing_keys, "requires_user_to_close_existing_app": True, "allows_explicit_existing_window_authorization": True, "message": "当前是 Computer Use 功能，检测到目标软件已经打开；请先手动关闭该软件，或在提示词中明确授权使用已有窗口后重新开启。", "low_level_event_count": 0}  # 新增代码+FreshTargetPolicy：返回旧窗口零事件拒绝报告；如果没有这一行，压力测试可能继续写入旧 Notepad。
    return {"allowed": True, "decision": "fresh_launch_candidate_ready", "fresh_target_class": "fresh_launch_candidate", "origin": "agent_owned_launch", "existing_target_window_count": 0, "existing_target_window_keys": [], "requires_user_to_close_existing_app": False, "allows_explicit_existing_window_authorization": True, "message": "未检测到目标软件已有窗口，可以尝试打开新目标。", "low_level_event_count": 0}  # 新增代码+FreshTargetPolicy：返回可启动新目标报告；如果没有这一行，正常打开新应用会被卡住。
# 新增代码+FreshTargetPolicy：函数段结束，decide_fresh_target_preflight 到此结束；如果没有这个边界说明，用户不容易看出启动前策略范围。


def decide_post_launch_freshness(target_app: Any, target_window: dict[str, Any], prelaunch_windows: list[dict[str, Any]] | None, launch_result: dict[str, Any] | None, *, user_authorized_window: bool = False) -> dict[str, Any]:  # 新增代码+FreshTargetPolicy：函数段开始，启动后判断绑定窗口是否可建租约；如果没有这段函数，旧窗口会在启动后被当新窗口。
    safe_window = dict(target_window or {}) if isinstance(target_window, dict) else {}  # 新增代码+FreshTargetPolicy：复制目标窗口；如果没有这一行，策略可能污染 session 报告。
    safe_launch = dict(launch_result or {}) if isinstance(launch_result, dict) else {}  # 新增代码+FreshTargetPolicy：复制启动报告；如果没有这一行，后续读取字段可能遇到坏类型。
    prelaunch_matches = detect_existing_target_windows(target_app, prelaunch_windows)  # 新增代码+FreshTargetPolicy：找出启动前同应用窗口；如果没有这一行，无法判断目标窗口是否早已存在。
    prelaunch_keys = {window_fresh_identity_key(window) for window in prelaunch_matches}  # 新增代码+FreshTargetPolicy：把旧窗口身份放进集合；如果没有这一行，启动后比较效率和语义都不稳定。
    target_key = window_fresh_identity_key(safe_window)  # 新增代码+FreshTargetPolicy：生成启动后目标窗口身份；如果没有这一行，策略无法和启动前快照比较。
    existed_before = bool(target_key and target_key in prelaunch_keys)  # 新增代码+FreshTargetPolicy：判断目标窗口是否启动前已存在；如果没有这一行，旧窗口复用无法被识别。
    proved_new_process = bool(safe_launch.get("owned_process_registered") and safe_launch.get("process_started") and _fresh_safe_text(safe_launch.get("process_id")))  # 新增代码+FreshTargetPolicy：判断后端是否证明新进程归 agent 所有；如果没有这一行，未知应用新开窗口不能形成正向证据。
    if user_authorized_window:  # 新增代码+FreshTargetPolicy：用户明确授权已有窗口时允许；如果没有这一行，合法旧窗口控制无法工作。
        return {"allowed": True, "decision": "user_granted_existing_window_ready", "fresh_target_class": "user_granted_existing_window", "fresh_target_identity_verified": True, "target_window_existed_before_launch": existed_before, "target_window_fresh_identity_key": target_key, "existing_target_window_keys": sorted(prelaunch_keys), "origin": "user_granted_existing_window", "low_level_event_count": 0}  # 新增代码+FreshTargetPolicy：返回用户授权旧窗口报告；如果没有这一行，租约无法记录授权来源。
    if existed_before:  # 新增代码+FreshTargetPolicy：启动后目标就是启动前旧窗口时拒绝；如果没有这一行，agent 会默认接管用户窗口。
        return {"allowed": False, "decision": "post_launch_target_was_preexisting_requires_relaunch_or_user_grant", "fresh_target_class": "preexisting_target_window", "fresh_target_identity_verified": False, "target_window_existed_before_launch": True, "target_window_fresh_identity_key": target_key, "existing_target_window_keys": sorted(prelaunch_keys), "origin": "blocked_preexisting_window", "requires_user_to_close_existing_app": True, "low_level_event_count": 0}  # 新增代码+FreshTargetPolicy：返回旧窗口绑定拒绝报告；如果没有这一行，启动后绑定会绕过预检缺口。
    if proved_new_process:  # 新增代码+FreshTargetPolicy：后端证明新进程时视为新目标；如果没有这一行，正常 launch_app 会被未知应用策略误杀。
        return {"allowed": True, "decision": "fresh_target_ready", "fresh_target_class": "fresh_agent_owned_window", "fresh_target_identity_verified": True, "target_window_existed_before_launch": False, "target_window_fresh_identity_key": target_key, "existing_target_window_keys": sorted(prelaunch_keys), "origin": "agent_owned_launch", "low_level_event_count": 0}  # 新增代码+FreshTargetPolicy：返回新目标通过报告；如果没有这一行，controller 无法建立 agent-owned lease。
    if is_known_single_instance_candidate(target_app, safe_window):  # 新增代码+FreshTargetPolicy：未见旧窗口且像单实例应用时温和放行；如果没有这一行，微信这类应用在无旧窗口时可能被误拒。
        return {"allowed": True, "decision": "single_instance_target_ready", "fresh_target_class": "single_instance_or_reused_process_without_preexisting_window", "fresh_target_identity_verified": True, "target_window_existed_before_launch": False, "target_window_fresh_identity_key": target_key, "existing_target_window_keys": sorted(prelaunch_keys), "origin": "agent_owned_launch", "low_level_event_count": 0}  # 新增代码+FreshTargetPolicy：返回单实例新目标通过报告；如果没有这一行，通用控制会对单实例应用过度悲观。
    return {"allowed": True, "decision": "fresh_target_ready", "fresh_target_class": "fresh_unknown_window_without_preexisting_match", "fresh_target_identity_verified": False, "target_window_existed_before_launch": False, "target_window_fresh_identity_key": target_key, "existing_target_window_keys": sorted(prelaunch_keys), "origin": "agent_owned_launch", "low_level_event_count": 0}  # 新增代码+FreshTargetPolicy：无旧窗口证据时允许未知应用继续由租约身份门禁兜底；如果没有这一行，通用 computer use 会卡死未知应用。
# 新增代码+FreshTargetPolicy：函数段结束，decide_post_launch_freshness 到此结束；如果没有这个边界说明，用户不容易看出启动后策略范围。


def classify_post_launch_target(target_app: Any, target_window: dict[str, Any], prelaunch_windows: list[dict[str, Any]] | None, launch_result: dict[str, Any] | None, *, user_authorized_window: bool = False) -> dict[str, Any]:  # 新增代码+FreshTargetPolicy：函数段开始，提供更直观的启动后分类别名；如果没有这段函数，测试和调用方会各自命名分类。
    return decide_post_launch_freshness(target_app, target_window, prelaunch_windows, launch_result, user_authorized_window=user_authorized_window)  # 新增代码+FreshTargetPolicy：复用启动后策略并返回报告；如果没有这一行，分类和策略可能分裂。
# 新增代码+FreshTargetPolicy：函数段结束，classify_post_launch_target 到此结束；如果没有这个边界说明，用户不容易看出别名范围。


def decide_recovery_after_drift(target_ref: Any, reason: Any = "target_lease_drift_rejected") -> dict[str, Any]:  # 新增代码+FreshTargetPolicy：函数段开始，生成漂移后的恢复动作；如果没有这段函数，漂移后可能继续用旧 target_ref 重试。
    safe_ref = _fresh_safe_text(target_ref)  # 新增代码+FreshTargetPolicy：清洗 target_ref；如果没有这一行，恢复报告可能带入空白或换行。
    safe_reason = _fresh_safe_text(reason) or "target_lease_drift_rejected"  # 新增代码+FreshTargetPolicy：清洗拒绝原因并兜底；如果没有这一行，报告可能没有稳定原因。
    return {"decision": "target_lease_invalidated", "invalidated_target_ref": safe_ref, "reason": safe_reason, "fresh_target_relaunch_required": True, "recovery_next_allowed_actions": ["observe", "launch_app"], "low_level_event_count": 0}  # 新增代码+FreshTargetPolicy：返回只允许观察或重新打开的恢复建议；如果没有这一行，agent 可能对失效窗口继续发鼠标键盘。
# 新增代码+FreshTargetPolicy：函数段结束，decide_recovery_after_drift 到此结束；如果没有这个边界说明，用户不容易看出漂移恢复范围。


__all__ = [  # 新增代码+FreshTargetPolicy：声明本模块公开 API；如果没有这一行，调用方不知道哪些 helper 可以稳定使用。
    "classify_post_launch_target",  # 新增代码+FreshTargetPolicy：导出启动后分类函数；如果没有这一行，测试无法从模块级直接导入。
    "decide_fresh_target_preflight",  # 新增代码+FreshTargetPolicy：导出启动前预检函数；如果没有这一行，controller 不能做旧窗口门禁。
    "decide_post_launch_freshness",  # 新增代码+FreshTargetPolicy：导出启动后新鲜度函数；如果没有这一行，universal session 不能记录绑定分类。
    "decide_recovery_after_drift",  # 新增代码+FreshTargetPolicy：导出漂移恢复函数；如果没有这一行，controller 无法统一失效 target_ref。
    "detect_existing_target_windows",  # 新增代码+FreshTargetPolicy：导出旧窗口检测函数；如果没有这一行，测试不能单独覆盖匹配逻辑。
    "is_known_single_instance_candidate",  # 新增代码+FreshTargetPolicy：导出单实例判断函数；如果没有这一行，调用方不能解释微信类应用策略。
    "window_fresh_identity_key",  # 新增代码+FreshTargetPolicy：导出窗口身份键函数；如果没有这一行，启动前后比较无法复用同一算法。
]  # 新增代码+FreshTargetPolicy：结束公开 API 列表；如果没有这一行，Python 语法不完整。
