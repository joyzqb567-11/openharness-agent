"""Windows Computer Use 持久授权、撤销和过期门禁。"""  # 新增代码+Phase60PersistentGrants: 标明本文件负责 Phase60 生产级持久授权；如果没有这行代码，读者不知道 approve/grants/revoke 的真实逻辑集中在哪里。
from __future__ import annotations  # 新增代码+Phase60PersistentGrants: 启用延迟类型解析；如果没有这行代码，复杂类型注解在旧导入顺序下更容易失败。

import hashlib  # 新增代码+Phase60PersistentGrants: 导入哈希工具生成稳定 grant_id；如果没有这行代码，授权记录很难和动作审计关联。
import json  # 新增代码+Phase60PersistentGrants: 导入 JSON 用于 CLI 打印结构化报告；如果没有这行代码，失败时不容易复盘合同结果。
import re  # 新增代码+Phase60PersistentGrants: 导入正则清理 session/app 文本；如果没有这行代码，外部输入可能污染文件和状态。
import time  # 新增代码+Phase60PersistentGrants: 导入时间用于 TTL、过期判断和审计时间；如果没有这行代码，授权无法自动失效。
from pathlib import Path  # 新增代码+Phase60PersistentGrants: 导入 Path 统一管理 Windows 路径；如果没有这行代码，状态路径拼接更脆弱。
from typing import Any  # 新增代码+Phase60PersistentGrants: 导入 Any 描述工具参数和 JSON 状态；如果没有这行代码，接口边界不清楚。

try:  # 新增代码+Phase60PersistentGrants: 优先按包路径导入安全文件工具；如果没有这段代码，包运行模式无法原子读写授权状态。
    from learning_agent.runtime.files import FileLock, append_jsonl, atomic_write_json, read_json_or_default  # 新增代码+Phase60PersistentGrants: 复用文件锁、审计追加、原子写和容错读；如果没有这行代码，并发授权状态可能损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase60PersistentGrants: 兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行的脚本模式；如果没有这段代码，真实终端可能因包名前缀失败。
    if error.name not in {"learning_agent", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase60PersistentGrants: 只允许包路径缺失时 fallback；如果没有这行代码，runtime.files 内部真实错误会被误吞。
        raise  # 新增代码+Phase60PersistentGrants: 重新抛出非路径类导入错误；如果没有这行代码，排查底层文件工具问题会困难。
    from runtime.files import FileLock, append_jsonl, atomic_write_json, read_json_or_default  # 新增代码+Phase60PersistentGrants: 脚本模式导入同目录文件工具；如果没有这行代码，bat 入口无法保存持久授权。

PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER = "PHASE60_WINDOWS_PERSISTENT_GRANTS_READY"  # 新增代码+Phase60PersistentGrants: 定义 Phase60 ready marker；如果没有这行代码，真实终端验收没有稳定锚点。
PHASE60_WINDOWS_PERSISTENT_GRANTS_OK_TOKEN = "PHASE60_WINDOWS_PERSISTENT_GRANTS_OK"  # 新增代码+Phase60PersistentGrants: 定义 Phase60 OK token；如果没有这行代码，debug log 无法区分自检通过和普通输出。
PHASE60_PERSISTENT_GRANTS_MODEL = "phase60_windows_persistent_grants"  # 新增代码+Phase60PersistentGrants: 定义持久授权模型名；如果没有这行代码，状态 UI 无法说明当前授权版本。
PHASE60_ACTIONS_EXPANDED = False  # 新增代码+Phase60PersistentGrants: 明确本阶段只补审批 UX 不扩大真实动作面；如果没有这行代码，用户可能误以为新增了更多桌面动作。
DEFAULT_PERSISTENT_GRANT_SESSION_ID = "learning-agent-default-session"  # 新增代码+Phase60PersistentGrants: 定义默认授权 session；如果没有这行代码，终端 approve 不知道写入哪个会话。
DEFAULT_PERSISTENT_GRANTS_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "persistent_grants"  # 新增代码+Phase60PersistentGrants: 定义默认持久授权目录；如果没有这行代码，生产入口无法把 grant 落到 memory/computer_use。
PHASE60_DESKTOP_ACTIONS = {"click", "double_click", "move", "move_mouse", "scroll", "type_text", "press_key"}  # 新增代码+Phase60PersistentGrants: 定义普通桌面动作集合；如果没有这行代码，desktopAction flag 无法被实际校验。
PHASE60_SYSTEM_KEY_ACTIONS = {"press_key", "system_key", "system_key_combo"}  # 新增代码+Phase60PersistentGrants: 定义系统键动作集合；如果没有这行代码，系统组合键授权可能被普通动作授权覆盖。
PHASE60_CLIPBOARD_READ_ACTIONS = {"clipboard_read", "read_clipboard", "get_clipboard"}  # 新增代码+Phase60PersistentGrants: 定义剪贴板读取动作集合；如果没有这行代码，读取剪贴板不会要求 clipboardRead。
PHASE60_CLIPBOARD_WRITE_ACTIONS = {"clipboard_write", "write_clipboard", "set_clipboard", "paste", "paste_text"}  # 新增代码+Phase60PersistentGrants: 定义剪贴板写入动作集合；如果没有这行代码，写剪贴板不会要求 clipboardWrite。
PHASE60_WILDCARD_SCOPES = {"*", "all", "any"}  # 新增代码+Phase60PersistentGrants: 定义 action_scope 通配符；如果没有这行代码，用户无法表达短期全动作授权。


def _phase60_bool_token(value: Any) -> str:  # 新增代码+Phase60PersistentGrants: 函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会出现 True/False 漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase60PersistentGrants: 返回 true/false 文本；如果没有这行代码，验收场景匹配不稳定。
# 新增代码+Phase60PersistentGrants: 函数段结束，_phase60_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式范围。


def _phase60_timestamp(epoch_seconds: float | None = None) -> str:  # 新增代码+Phase60PersistentGrants: 函数段开始，生成 UTC 时间戳；如果没有这段函数，授权审计时间会重复手写。
    source_seconds = time.time() if epoch_seconds is None else float(epoch_seconds)  # 新增代码+Phase60PersistentGrants: 使用传入时间或当前时间；如果没有这行代码，过期记录无法复用同一时刻。
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(source_seconds))  # 新增代码+Phase60PersistentGrants: 返回可排序 UTC 文本；如果没有这行代码，用户很难判断授权新旧。
# 新增代码+Phase60PersistentGrants: 函数段结束，_phase60_timestamp 到此结束；如果没有这个边界说明，初学者不容易看出时间格式范围。


def _phase60_safe_text(value: Any, limit: int = 180) -> str:  # 新增代码+Phase60PersistentGrants: 函数段开始，把任意输入压成安全短文本；如果没有这段函数，终端输出可能被换行或超长文本污染。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase60PersistentGrants: 去掉换行和首尾空白；如果没有这行代码，用户输入可能打散状态面板。
    return text[:limit]  # 新增代码+Phase60PersistentGrants: 限制长度；如果没有这行代码，长标题或 reason 会刷爆终端。
# 新增代码+Phase60PersistentGrants: 函数段结束，_phase60_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清理范围。


def _phase60_safe_session_id(session_id: Any) -> str:  # 新增代码+Phase60PersistentGrants: 函数段开始，把 session_id 清理为审计安全文本；如果没有这段函数，外部 session 名可能携带危险字符。
    text = _phase60_safe_text(session_id or DEFAULT_PERSISTENT_GRANT_SESSION_ID, 140)  # 新增代码+Phase60PersistentGrants: 读取 session 文本并限制长度；如果没有这行代码，空 session 会生成不稳定记录。
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)  # 新增代码+Phase60PersistentGrants: 只保留文件和日志友好字符；如果没有这行代码，审计字段可能难以搜索。
    return cleaned or DEFAULT_PERSISTENT_GRANT_SESSION_ID  # 新增代码+Phase60PersistentGrants: 空结果回到默认 session；如果没有这行代码，授权可能没有会话归属。
# 新增代码+Phase60PersistentGrants: 函数段结束，_phase60_safe_session_id 到此结束；如果没有这个边界说明，初学者不容易看出 session 清理范围。


def _phase60_normalized_app(value: Any) -> str:  # 新增代码+Phase60PersistentGrants: 函数段开始，规范化应用名；如果没有这段函数，同一 app 会因大小写或空格重复授权。
    return _phase60_safe_text(value, 140).lower()  # 新增代码+Phase60PersistentGrants: 返回小写 app key；如果没有这行代码，notepad.exe 和 NOTEPAD.EXE 会被当成两个对象。
# 新增代码+Phase60PersistentGrants: 函数段结束，_phase60_normalized_app 到此结束；如果没有这个边界说明，初学者不容易看出 app 匹配范围。


def _phase60_normalized_scope_list(action_scope: Any) -> list[str]:  # 新增代码+Phase60PersistentGrants: 函数段开始，规范化 action_scope 列表；如果没有这段函数，字符串和列表输入会产生不同语义。
    raw_values = action_scope if isinstance(action_scope, list) else str(action_scope or "").split(",")  # 新增代码+Phase60PersistentGrants: 同时接受 list 和逗号字符串；如果没有这行代码，终端 scope=click,type_text 无法使用。
    result: list[str] = []  # 新增代码+Phase60PersistentGrants: 准备保存去重后的 scope；如果没有这行代码，函数没有输出容器。
    for value in list(raw_values or []):  # 新增代码+Phase60PersistentGrants: 遍历每个 scope 值；如果没有这行代码，传入范围不会被处理。
        text = _phase60_safe_text(value, 80).lower()  # 新增代码+Phase60PersistentGrants: 清理并小写动作名；如果没有这行代码，Click 和 click 匹配会漂移。
        if text and text not in result:  # 新增代码+Phase60PersistentGrants: 跳过空值和重复值；如果没有这行代码，状态文件会堆重复 scope。
            result.append(text)  # 新增代码+Phase60PersistentGrants: 保存有效动作范围；如果没有这行代码，授权无法匹配任何动作。
    return result or ["observe"]  # 新增代码+Phase60PersistentGrants: 没有显式 scope 时保守回到 observe；如果没有这行代码，空 scope 可能被误解为全权限。
# 新增代码+Phase60PersistentGrants: 函数段结束，_phase60_normalized_scope_list 到此结束；如果没有这个边界说明，初学者不容易看出 scope 清理范围。


def _phase60_normalized_flags(grant_flags: Any) -> dict[str, bool]:  # 新增代码+Phase60PersistentGrants: 函数段开始，规范化授权 flag 字典；如果没有这段函数，字符串 false 可能被误当成真。
    raw_flags = dict(grant_flags or {}) if isinstance(grant_flags, dict) else {}  # 新增代码+Phase60PersistentGrants: 只有 dict 才作为 flags 读取；如果没有这行代码，坏类型会污染授权状态。
    return {str(name): bool(enabled) for name, enabled in raw_flags.items()}  # 新增代码+Phase60PersistentGrants: 返回布尔化 flags；如果没有这行代码，后续高风险判断不稳定。
# 新增代码+Phase60PersistentGrants: 函数段结束，_phase60_normalized_flags 到此结束；如果没有这个边界说明，初学者不容易看出 flag 清理范围。


def _phase60_required_flags_for_scope(action_scope: Any) -> list[str]:  # 新增代码+Phase60PersistentGrants: 函数段开始，计算授权范围需要哪些显式 grant flags；如果没有这段函数，approve 只写文件不做安全门禁。
    scopes = _phase60_normalized_scope_list(action_scope)  # 新增代码+Phase60PersistentGrants: 先规范化 action_scope；如果没有这行代码，大小写和字符串输入会影响判定。
    required: list[str] = []  # 新增代码+Phase60PersistentGrants: 准备保存需要的 grant flags；如果没有这行代码，函数没有累计容器。
    for scope in scopes:  # 新增代码+Phase60PersistentGrants: 遍历授权动作范围；如果没有这行代码，只能处理单个固定动作。
        if scope in PHASE60_WILDCARD_SCOPES or scope in PHASE60_DESKTOP_ACTIONS:  # 新增代码+Phase60PersistentGrants: 普通桌面动作和通配符需要 desktopAction；如果没有这行代码，点击输入可能被无 flag 放行。
            required.append("desktopAction")  # 新增代码+Phase60PersistentGrants: 记录普通桌面动作权限；如果没有这行代码，授权记录缺少核心动作门禁。
        if scope in PHASE60_SYSTEM_KEY_ACTIONS or scope in PHASE60_WILDCARD_SCOPES:  # 新增代码+Phase60PersistentGrants: 系统键或全权限需要 systemKeyCombos；如果没有这行代码，高风险系统键会被普通动作覆盖。
            required.append("systemKeyCombos")  # 新增代码+Phase60PersistentGrants: 记录系统键高风险权限；如果没有这行代码，press_key 默认拒绝无法生效。
        if scope in PHASE60_CLIPBOARD_READ_ACTIONS or scope in PHASE60_WILDCARD_SCOPES:  # 新增代码+Phase60PersistentGrants: 剪贴板读取或全权限需要 clipboardRead；如果没有这行代码，读取剪贴板风险不可见。
            required.append("clipboardRead")  # 新增代码+Phase60PersistentGrants: 记录剪贴板读取权限；如果没有这行代码，clipboard_read 可被普通授权误放行。
        if scope in PHASE60_CLIPBOARD_WRITE_ACTIONS or scope in PHASE60_WILDCARD_SCOPES:  # 新增代码+Phase60PersistentGrants: 剪贴板写入或全权限需要 clipboardWrite；如果没有这行代码，写剪贴板风险不可见。
            required.append("clipboardWrite")  # 新增代码+Phase60PersistentGrants: 记录剪贴板写入权限；如果没有这行代码，clipboard_write 可被普通授权误放行。
    return list(dict.fromkeys(required))  # 新增代码+Phase60PersistentGrants: 去重并保持顺序返回；如果没有这行代码，终端会显示重复缺失权限。
# 新增代码+Phase60PersistentGrants: 函数段结束，_phase60_required_flags_for_scope 到此结束；如果没有这个边界说明，初学者不容易看出权限计算范围。


def _phase60_window_summary(arguments: dict[str, Any]) -> dict[str, str]:  # 新增代码+Phase60PersistentGrants: 函数段开始，从动作参数提取目标窗口摘要；如果没有这段函数，evaluate 不知道动作指向哪个 app/window/display。
    raw_window = dict(arguments or {}).get("window", {})  # 新增代码+Phase60PersistentGrants: 读取 window 参数；如果没有这行代码，动作目标信息会丢失。
    window = dict(raw_window or {}) if isinstance(raw_window, dict) else {}  # 新增代码+Phase60PersistentGrants: 只接受 dict 窗口对象；如果没有这行代码，坏对象会让字段读取失败。
    process_name = window.get("process_name") or dict(arguments or {}).get("process_name") or dict(arguments or {}).get("app")  # 新增代码+Phase60PersistentGrants: 优先读取进程名和 app；如果没有这行代码，授权 app 匹配可能为空。
    app_id = window.get("app_id") or dict(arguments or {}).get("app_id") or process_name  # 新增代码+Phase60PersistentGrants: 读取 app_id 并用进程名兜底；如果没有这行代码，缺 app_id 的窗口无法匹配。
    return {"app": _phase60_normalized_app(process_name or app_id), "app_id": _phase60_normalized_app(app_id), "process_name": _phase60_normalized_app(process_name), "window_id": _phase60_safe_text(window.get("window_id") or dict(arguments or {}).get("window_id"), 140), "display_id": _phase60_safe_text(window.get("display_id") or dict(arguments or {}).get("display_id"), 120), "title_preview": _phase60_safe_text(window.get("title_preview") or dict(arguments or {}).get("title_preview"), 180)}  # 新增代码+Phase60PersistentGrants: 返回可审计窗口摘要；如果没有这行代码，拒绝和允许结果无法解释目标。
# 新增代码+Phase60PersistentGrants: 函数段结束，_phase60_window_summary 到此结束；如果没有这个边界说明，初学者不容易看出窗口摘要范围。


def _phase60_scope_matches(grant_scope: Any, action: Any) -> bool:  # 新增代码+Phase60PersistentGrants: 函数段开始，判断授权范围是否覆盖动作；如果没有这段函数，evaluate 不能按 scope 精确放行。
    scopes = set(_phase60_normalized_scope_list(grant_scope))  # 新增代码+Phase60PersistentGrants: 把授权范围变成集合；如果没有这行代码，每次匹配都要重复规范化。
    normalized_action = _phase60_safe_text(action, 80).lower()  # 新增代码+Phase60PersistentGrants: 规范化动作名；如果没有这行代码，大小写不同会误拒绝。
    return bool(scopes.intersection(PHASE60_WILDCARD_SCOPES) or normalized_action in scopes)  # 新增代码+Phase60PersistentGrants: 支持通配符和精确动作匹配；如果没有这行代码，授权范围不会真正生效。
# 新增代码+Phase60PersistentGrants: 函数段结束，_phase60_scope_matches 到此结束；如果没有这个边界说明，初学者不容易看出 scope 匹配范围。


def _phase60_grant_matches(grant: dict[str, Any], session_id: Any, action: Any, target: dict[str, str]) -> bool:  # 新增代码+Phase60PersistentGrants: 函数段开始，判断某条 grant 是否匹配本次动作；如果没有这段函数，过期和撤销判断会重复出错。
    if _phase60_safe_session_id(grant.get("session_id")) != _phase60_safe_session_id(session_id):  # 新增代码+Phase60PersistentGrants: 先匹配 session；如果没有这行代码，一个 agent 会话可能使用另一个会话授权。
        return False  # 新增代码+Phase60PersistentGrants: session 不同直接不匹配；如果没有这行代码，跨会话隔离会失效。
    grant_app = _phase60_normalized_app(grant.get("app"))  # 新增代码+Phase60PersistentGrants: 读取授权 app；如果没有这行代码，后续 app 匹配没有基准。
    target_apps = {target.get("app", ""), target.get("app_id", ""), target.get("process_name", "")}  # 新增代码+Phase60PersistentGrants: 收集目标可能的 app key；如果没有这行代码，app_id/process_name 变体会误拒绝。
    if grant_app and grant_app not in target_apps:  # 新增代码+Phase60PersistentGrants: 授权 app 必须命中目标 app；如果没有这行代码，授权可能放行错误应用。
        return False  # 新增代码+Phase60PersistentGrants: app 不匹配直接拒绝本 grant；如果没有这行代码，后续范围判断会误用授权。
    if _phase60_safe_text(grant.get("window_id"), 140) and _phase60_safe_text(grant.get("window_id"), 140) != target.get("window_id", ""):  # 新增代码+Phase60PersistentGrants: 如果 grant 绑定窗口就必须匹配窗口；如果没有这行代码，窗口级授权会变成 app 级授权。
        return False  # 新增代码+Phase60PersistentGrants: 窗口不匹配直接返回；如果没有这行代码，错误窗口可能被放行。
    if _phase60_safe_text(grant.get("display_id"), 120) and _phase60_safe_text(grant.get("display_id"), 120) != target.get("display_id", ""):  # 新增代码+Phase60PersistentGrants: 如果 grant 绑定显示器就必须匹配显示器；如果没有这行代码，多屏授权边界会失效。
        return False  # 新增代码+Phase60PersistentGrants: 显示器不匹配直接返回；如果没有这行代码，动作可能落到错误屏幕。
    return _phase60_scope_matches(grant.get("action_scope", []), action)  # 新增代码+Phase60PersistentGrants: 最后检查动作范围；如果没有这行代码，scope 字段不会参与门禁。
# 新增代码+Phase60PersistentGrants: 函数段结束，_phase60_grant_matches 到此结束；如果没有这个边界说明，初学者不容易看出 grant 匹配范围。


class WindowsComputerUsePersistentGrantStore:  # 新增代码+Phase60PersistentGrants: 类段开始，管理 Windows Computer Use 持久授权；如果没有这个类，approve/grants/revoke 只能停留在终端草案。
    def __init__(self, base_dir: str | Path | None = None, lock_timeout_seconds: float = 5.0) -> None:  # 新增代码+Phase60PersistentGrants: 函数段开始，初始化授权状态目录和互斥锁；如果没有这段函数，测试和生产无法选择不同状态位置。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_PERSISTENT_GRANTS_ROOT  # 新增代码+Phase60PersistentGrants: 保存授权根目录；如果没有这行代码，store 不知道读写哪里。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase60PersistentGrants: 确保目录存在；如果没有这行代码，首次 approve 会写入失败。
        self.state_path = self.base_dir / "persistent_grants.json"  # 新增代码+Phase60PersistentGrants: 定义主状态文件；如果没有这行代码，grants 无法持久化。
        self.audit_path = self.base_dir / "persistent_grants_audit.jsonl"  # 新增代码+Phase60PersistentGrants: 定义授权审计日志；如果没有这行代码，approve/revoke/deny 无法事后回放。
        self.mutex_path = self.base_dir / ".persistent_grants.mutex"  # 新增代码+Phase60PersistentGrants: 定义互斥锁文件；如果没有这行代码，并发授权可能互相覆盖。
        self.lock_timeout_seconds = float(lock_timeout_seconds)  # 新增代码+Phase60PersistentGrants: 保存文件锁等待时间；如果没有这行代码，锁等待策略不明确。
    # 新增代码+Phase60PersistentGrants: 函数段结束，WindowsComputerUsePersistentGrantStore.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _default_state(self) -> dict[str, Any]:  # 新增代码+Phase60PersistentGrants: 函数段开始，构造空白授权状态；如果没有这段函数，首次运行没有完整 schema。
        return {"schema_version": 1, "model": PHASE60_PERSISTENT_GRANTS_MODEL, "marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, "grants": [], "state_path": str(self.state_path), "audit_path": str(self.audit_path), "actions_expanded": PHASE60_ACTIONS_EXPANDED}  # 新增代码+Phase60PersistentGrants: 返回完整默认状态；如果没有这行代码，状态 UI 会遇到缺字段。
    # 新增代码+Phase60PersistentGrants: 函数段结束，WindowsComputerUsePersistentGrantStore._default_state 到此结束；如果没有这个边界说明，初学者不容易看出默认状态范围。

    def _normalize_grant(self, grant: Any) -> dict[str, Any]:  # 新增代码+Phase60PersistentGrants: 函数段开始，修复旧/坏 grant 为标准字段；如果没有这段函数，坏状态会拖垮评估。
        raw = dict(grant or {}) if isinstance(grant, dict) else {}  # 新增代码+Phase60PersistentGrants: 只有 dict 才合并；如果没有这行代码，坏 JSON 类型会污染状态。
        normalized = {"grant_id": _phase60_safe_text(raw.get("grant_id"), 120), "session_id": _phase60_safe_session_id(raw.get("session_id")), "app": _phase60_normalized_app(raw.get("app")), "window_id": _phase60_safe_text(raw.get("window_id"), 140), "display_id": _phase60_safe_text(raw.get("display_id"), 120), "action_scope": _phase60_normalized_scope_list(raw.get("action_scope", [])), "grant_flags": _phase60_normalized_flags(raw.get("grant_flags", {})), "reason": _phase60_safe_text(raw.get("reason"), 220), "created_at": _phase60_safe_text(raw.get("created_at"), 80), "expires_at": _phase60_safe_text(raw.get("expires_at"), 80), "expires_at_epoch": float(raw.get("expires_at_epoch", 0.0) or 0.0), "revoked": bool(raw.get("revoked", False)), "revoked_at": _phase60_safe_text(raw.get("revoked_at"), 80), "revoked_reason": _phase60_safe_text(raw.get("revoked_reason"), 220)}  # 新增代码+Phase60PersistentGrants: 返回标准化 grant；如果没有这行代码，evaluate/revoke/status 要面对缺字段。
        return normalized  # 新增代码+Phase60PersistentGrants: 返回清洗后的授权；如果没有这行代码，调用方拿不到标准结果。
    # 新增代码+Phase60PersistentGrants: 函数段结束，WindowsComputerUsePersistentGrantStore._normalize_grant 到此结束；如果没有这个边界说明，初学者不容易看出 grant 清洗范围。

    def _read_state(self) -> dict[str, Any]:  # 新增代码+Phase60PersistentGrants: 函数段开始，读取并规范化授权状态；如果没有这段函数，每个方法都要重复容错读。
        payload = read_json_or_default(self.state_path, {})  # 新增代码+Phase60PersistentGrants: 容错读取 JSON；如果没有这行代码，首次运行或半写文件会崩溃。
        state = self._default_state()  # 新增代码+Phase60PersistentGrants: 先创建完整默认字段；如果没有这行代码，缺字段无法补齐。
        if isinstance(payload, dict):  # 新增代码+Phase60PersistentGrants: 只有 dict 状态才合并；如果没有这行代码，坏类型会污染主状态。
            state.update(dict(payload))  # 新增代码+Phase60PersistentGrants: 合并已有状态；如果没有这行代码，持久授权无法恢复。
        grants = state.get("grants", []) if isinstance(state.get("grants", []), list) else []  # 新增代码+Phase60PersistentGrants: 读取 grants 列表并防御坏类型；如果没有这行代码，坏 JSON 会让遍历崩溃。
        state["grants"] = [self._normalize_grant(item) for item in grants]  # 新增代码+Phase60PersistentGrants: 规范化所有授权记录；如果没有这行代码，旧字段会影响评估。
        state["model"] = PHASE60_PERSISTENT_GRANTS_MODEL  # 新增代码+Phase60PersistentGrants: 固定模型名；如果没有这行代码，旧状态可能显示错误版本。
        state["marker"] = PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER  # 新增代码+Phase60PersistentGrants: 固定 marker；如果没有这行代码，状态页缺少阶段锚点。
        state["state_path"] = str(self.state_path)  # 新增代码+Phase60PersistentGrants: 刷新主状态路径；如果没有这行代码，移动目录后状态会显示旧路径。
        state["audit_path"] = str(self.audit_path)  # 新增代码+Phase60PersistentGrants: 刷新审计路径；如果没有这行代码，用户找不到审计日志。
        state["actions_expanded"] = PHASE60_ACTIONS_EXPANDED  # 新增代码+Phase60PersistentGrants: 固定动作边界；如果没有这行代码，状态可能被误读为新增动作。
        return state  # 新增代码+Phase60PersistentGrants: 返回规范化状态；如果没有这行代码，调用方拿不到授权列表。
    # 新增代码+Phase60PersistentGrants: 函数段结束，WindowsComputerUsePersistentGrantStore._read_state 到此结束；如果没有这个边界说明，初学者不容易看出读取范围。

    def _write_state(self, state: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase60PersistentGrants: 函数段开始，原子写入授权状态；如果没有这段函数，approve/revoke 可能留下半个 JSON。
        payload = self._default_state()  # 新增代码+Phase60PersistentGrants: 先创建完整默认结构；如果没有这行代码，写入可能丢 schema 字段。
        payload.update(dict(state or {}))  # 新增代码+Phase60PersistentGrants: 合并调用方状态；如果没有这行代码，旧授权列表无法写回。
        payload["grants"] = [self._normalize_grant(item) for item in list(payload.get("grants", []))]  # 新增代码+Phase60PersistentGrants: 写入前再次规范化 grants；如果没有这行代码，坏字段会落盘。
        atomic_write_json(self.state_path, payload)  # 新增代码+Phase60PersistentGrants: 原子写入 JSON；如果没有这行代码，崩溃时可能损坏授权状态。
        return payload  # 新增代码+Phase60PersistentGrants: 返回实际写入状态；如果没有这行代码，调用方无法拿到规范化结果。
    # 新增代码+Phase60PersistentGrants: 函数段结束，WindowsComputerUsePersistentGrantStore._write_state 到此结束；如果没有这个边界说明，初学者不容易看出写入范围。

    def _audit(self, event_type: str, payload: dict[str, Any]) -> None:  # 新增代码+Phase60PersistentGrants: 函数段开始，追加授权审计事件；如果没有这段函数，approve/revoke/deny 无法回放。
        row = {"event_type": _phase60_safe_text(event_type, 80), "time": _phase60_timestamp(), "payload": dict(payload or {}), "model": PHASE60_PERSISTENT_GRANTS_MODEL, "marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER}  # 新增代码+Phase60PersistentGrants: 构造单行审计事件；如果没有这行代码，事件缺少时间和阶段来源。
        append_jsonl(self.audit_path, row)  # 新增代码+Phase60PersistentGrants: 追加 JSONL 审计；如果没有这行代码，授权动作不会落审计日志。
    # 新增代码+Phase60PersistentGrants: 函数段结束，WindowsComputerUsePersistentGrantStore._audit 到此结束；如果没有这个边界说明，初学者不容易看出审计范围。

    def _new_grant_id(self, session_id: str, app: str, action_scope: list[str], now: float) -> str:  # 新增代码+Phase60PersistentGrants: 函数段开始，生成 grant_id；如果没有这段函数，授权记录无法被 revoke 和动作结果关联。
        seed = f"{session_id}:{app}:{','.join(action_scope)}:{now}:{len(str(self.state_path))}"  # 新增代码+Phase60PersistentGrants: 组装包含会话、应用、范围和时间的种子；如果没有这行代码，grant_id 冲突概率更高。
        return "phase60-grant-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]  # 新增代码+Phase60PersistentGrants: 返回短哈希 id；如果没有这行代码，终端输出会过长或不稳定。
    # 新增代码+Phase60PersistentGrants: 函数段结束，WindowsComputerUsePersistentGrantStore._new_grant_id 到此结束；如果没有这个边界说明，初学者不容易看出 id 生成范围。

    def approve(self, session_id: Any = DEFAULT_PERSISTENT_GRANT_SESSION_ID, *, app: Any, window_id: Any = "", display_id: Any = "", action_scope: Any = None, ttl_seconds: int | float = 900, reason: str = "", grant_flags: dict[str, bool] | None = None) -> dict[str, Any]:  # 新增代码+Phase60PersistentGrants: 函数段开始，写入一条可评估的持久授权；如果没有这段函数，/computer approve 只能显示文字不能真正放行。
        safe_session_id = _phase60_safe_session_id(session_id)  # 新增代码+Phase60PersistentGrants: 清理 session_id；如果没有这行代码，授权没有稳定会话归属。
        safe_app = _phase60_normalized_app(app)  # 新增代码+Phase60PersistentGrants: 清理 app key；如果没有这行代码，同一应用无法稳定匹配。
        scopes = _phase60_normalized_scope_list(action_scope or ["observe"])  # 新增代码+Phase60PersistentGrants: 规范化动作范围；如果没有这行代码，授权范围不明确。
        flags = _phase60_normalized_flags(grant_flags or {})  # 新增代码+Phase60PersistentGrants: 规范化 grant flags；如果没有这行代码，高风险校验不可靠。
        required_flags = _phase60_required_flags_for_scope(scopes)  # 新增代码+Phase60PersistentGrants: 计算本授权范围需要的 flags；如果没有这行代码，高风险默认拒绝不会生效。
        missing_flags = [name for name in required_flags if not flags.get(name, False)]  # 新增代码+Phase60PersistentGrants: 找出缺失的显式授权；如果没有这行代码，危险权限可能被无意写入。
        high_risk_missing = [name for name in missing_flags if name in {"systemKeyCombos", "clipboardRead", "clipboardWrite"}]  # 新增代码+Phase60PersistentGrants: 单独提取高风险缺失项；如果没有这行代码，系统键和剪贴板无法给出明确默认拒绝。
        if not safe_app:  # 新增代码+Phase60PersistentGrants: 检查 app 是否为空；如果没有这行代码，空 app 授权可能匹配未知目标。
            return {"approved": False, "decision": "missing_app", "missing_grant_flags": [], "marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, "actions_expanded": PHASE60_ACTIONS_EXPANDED}  # 新增代码+Phase60PersistentGrants: 返回缺 app 拒绝；如果没有这行代码，用户不知道 approve 为什么失败。
        if high_risk_missing or missing_flags:  # 新增代码+Phase60PersistentGrants: 缺少必要 flag 时拒绝写入；如果没有这行代码，未显式授权也会落盘。
            decision = "high_risk_requires_explicit_grant" if high_risk_missing else "missing_required_grant_flags"  # 新增代码+Phase60PersistentGrants: 区分高风险和普通 flag 缺失；如果没有这行代码，用户不知道风险级别。
            return {"approved": False, "decision": decision, "app": safe_app, "action_scope": scopes, "required_grants": required_flags, "missing_grant_flags": missing_flags, "marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, "actions_expanded": PHASE60_ACTIONS_EXPANDED}  # 新增代码+Phase60PersistentGrants: 返回拒绝详情且不写状态；如果没有这行代码，高风险默认拒绝不可审计。
        now = time.time()  # 新增代码+Phase60PersistentGrants: 捕获当前时间；如果没有这行代码，TTL 和 created_at 不能对齐。
        expires_epoch = now + float(ttl_seconds)  # 新增代码+Phase60PersistentGrants: 计算过期时间；如果没有这行代码，授权永远不会自动失效。
        grant = {"grant_id": self._new_grant_id(safe_session_id, safe_app, scopes, now), "session_id": safe_session_id, "app": safe_app, "window_id": _phase60_safe_text(window_id, 140), "display_id": _phase60_safe_text(display_id, 120), "action_scope": scopes, "grant_flags": flags, "reason": _phase60_safe_text(reason, 220), "created_at": _phase60_timestamp(now), "expires_at": _phase60_timestamp(expires_epoch), "expires_at_epoch": expires_epoch, "revoked": False, "revoked_at": "", "revoked_reason": ""}  # 新增代码+Phase60PersistentGrants: 构造完整授权记录；如果没有这行代码，状态无法表达 app/window/display/scope/ttl/reason。
        with FileLock(self.mutex_path, timeout_seconds=self.lock_timeout_seconds):  # 新增代码+Phase60PersistentGrants: 用互斥锁保护读改写；如果没有这行代码，并发 approve 可能互相覆盖。
            state = self._read_state()  # 新增代码+Phase60PersistentGrants: 读取现有状态；如果没有这行代码，新授权会覆盖旧授权。
            state["grants"].append(grant)  # 新增代码+Phase60PersistentGrants: 添加新授权；如果没有这行代码，approve 不会落盘。
            self._write_state(state)  # 新增代码+Phase60PersistentGrants: 原子写回状态；如果没有这行代码，下一条 evaluate 看不到授权。
            self._audit("approve", grant)  # 新增代码+Phase60PersistentGrants: 记录 approve 审计；如果没有这行代码，授权来源无法回放。
        return {"approved": True, "decision": "approved", "grant_id": grant["grant_id"], "grant": grant, "app": safe_app, "action_scope": scopes, "required_grants": required_flags, "missing_grant_flags": [], "marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, "actions_expanded": PHASE60_ACTIONS_EXPANDED}  # 新增代码+Phase60PersistentGrants: 返回授权成功摘要；如果没有这行代码，终端无法显示 grant_id 和结果。
    # 新增代码+Phase60PersistentGrants: 函数段结束，WindowsComputerUsePersistentGrantStore.approve 到此结束；如果没有这个边界说明，初学者不容易看出授权写入范围。

    def deny(self, session_id: Any = DEFAULT_PERSISTENT_GRANT_SESSION_ID, *, app: Any = "", action_scope: Any = None, reason: str = "") -> dict[str, Any]:  # 新增代码+Phase60PersistentGrants: 函数段开始，记录一次显式拒绝；如果没有这段函数，/computer deny 没有可审计结果。
        payload = {"session_id": _phase60_safe_session_id(session_id), "app": _phase60_normalized_app(app), "action_scope": _phase60_normalized_scope_list(action_scope or ["observe"]), "reason": _phase60_safe_text(reason, 220)}  # 新增代码+Phase60PersistentGrants: 构造拒绝事件；如果没有这行代码，拒绝记录缺少对象和原因。
        with FileLock(self.mutex_path, timeout_seconds=self.lock_timeout_seconds):  # 新增代码+Phase60PersistentGrants: 用同一锁保护审计追加；如果没有这行代码，审计和状态读写可能交错。
            self._audit("deny", payload)  # 新增代码+Phase60PersistentGrants: 写入 deny 审计；如果没有这行代码，用户的拒绝选择无法回放。
        return {"denied_recorded": True, "decision": "denied_recorded", "app": payload["app"], "action_scope": payload["action_scope"], "marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, "actions_expanded": PHASE60_ACTIONS_EXPANDED}  # 新增代码+Phase60PersistentGrants: 返回拒绝记录摘要；如果没有这行代码，终端无法告诉用户 deny 是否生效。
    # 新增代码+Phase60PersistentGrants: 函数段结束，WindowsComputerUsePersistentGrantStore.deny 到此结束；如果没有这个边界说明，初学者不容易看出拒绝审计范围。

    def revoke(self, session_id: Any = DEFAULT_PERSISTENT_GRANT_SESSION_ID, *, grant_id: Any = "", app: Any = "", reason: str = "terminal revoke") -> dict[str, Any]:  # 新增代码+Phase60PersistentGrants: 函数段开始，撤销匹配授权；如果没有这段函数，持久授权无法被收回。
        safe_session_id = _phase60_safe_session_id(session_id)  # 新增代码+Phase60PersistentGrants: 清理 session_id；如果没有这行代码，撤销可能跨会话误伤。
        safe_grant_id = _phase60_safe_text(grant_id, 140)  # 新增代码+Phase60PersistentGrants: 清理 grant_id；如果没有这行代码，撤销目标不稳定。
        safe_app = _phase60_normalized_app(app)  # 新增代码+Phase60PersistentGrants: 清理 app key；如果没有这行代码，按 app 撤销会大小写漂移。
        revoked_grants: list[dict[str, Any]] = []  # 新增代码+Phase60PersistentGrants: 准备保存撤销记录；如果没有这行代码，返回结果不知道撤销了哪些 grant。
        with FileLock(self.mutex_path, timeout_seconds=self.lock_timeout_seconds):  # 新增代码+Phase60PersistentGrants: 用互斥锁保护撤销写入；如果没有这行代码，并发 revoke/approve 可能互相覆盖。
            state = self._read_state()  # 新增代码+Phase60PersistentGrants: 读取当前授权状态；如果没有这行代码，revoke 不知道有哪些 grant。
            for grant in state["grants"]:  # 新增代码+Phase60PersistentGrants: 遍历所有授权；如果没有这行代码，无法找到撤销目标。
                same_session = grant.get("session_id") == safe_session_id  # 新增代码+Phase60PersistentGrants: 判断会话是否匹配；如果没有这行代码，撤销会误跨 session。
                same_grant = bool(safe_grant_id and grant.get("grant_id") == safe_grant_id)  # 新增代码+Phase60PersistentGrants: 判断 grant_id 是否匹配；如果没有这行代码，按 id 撤销不可用。
                same_app = bool(safe_app and grant.get("app") == safe_app)  # 新增代码+Phase60PersistentGrants: 判断 app 是否匹配；如果没有这行代码，终端 revoke <app> 不可用。
                if same_session and not grant.get("revoked", False) and (same_grant or same_app):  # 新增代码+Phase60PersistentGrants: 只撤销本会话未撤销且命中的 grant；如果没有这行代码，会重复撤销或误伤。
                    grant["revoked"] = True  # 新增代码+Phase60PersistentGrants: 标记授权已撤销；如果没有这行代码，evaluate 仍会放行。
                    grant["revoked_at"] = _phase60_timestamp()  # 新增代码+Phase60PersistentGrants: 记录撤销时间；如果没有这行代码，审计无法排序撤销动作。
                    grant["revoked_reason"] = _phase60_safe_text(reason, 220)  # 新增代码+Phase60PersistentGrants: 记录撤销原因；如果没有这行代码，用户不知道为什么收回授权。
                    revoked_grants.append(dict(grant))  # 新增代码+Phase60PersistentGrants: 保存撤销副本用于返回和审计；如果没有这行代码，结果缺少证据。
            self._write_state(state)  # 新增代码+Phase60PersistentGrants: 写回撤销状态；如果没有这行代码，撤销不会持久化。
            self._audit("revoke", {"session_id": safe_session_id, "grant_id": safe_grant_id, "app": safe_app, "revoked_grants": revoked_grants, "reason": _phase60_safe_text(reason, 220)})  # 新增代码+Phase60PersistentGrants: 写入 revoke 审计；如果没有这行代码，撤销动作无法回放。
        return {"revoked": bool(revoked_grants), "revoked_count": len(revoked_grants), "revoked_grants": revoked_grants, "grant_id": safe_grant_id, "app": safe_app, "marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, "actions_expanded": PHASE60_ACTIONS_EXPANDED}  # 新增代码+Phase60PersistentGrants: 返回撤销摘要；如果没有这行代码，终端无法显示 revoked=true/false。
    # 新增代码+Phase60PersistentGrants: 函数段结束，WindowsComputerUsePersistentGrantStore.revoke 到此结束；如果没有这个边界说明，初学者不容易看出撤销范围。

    def evaluate(self, session_id: Any = DEFAULT_PERSISTENT_GRANT_SESSION_ID, *, action: Any, arguments: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase60PersistentGrants: 函数段开始，评估动作是否被持久授权允许；如果没有这段函数，approve 不能真正保护后端动作。
        safe_session_id = _phase60_safe_session_id(session_id)  # 新增代码+Phase60PersistentGrants: 清理 session_id；如果没有这行代码，跨会话隔离不稳定。
        normalized_action = _phase60_safe_text(action, 80).lower()  # 新增代码+Phase60PersistentGrants: 清理动作名；如果没有这行代码，大小写变体会误判。
        target = _phase60_window_summary(dict(arguments or {}))  # 新增代码+Phase60PersistentGrants: 提取目标窗口摘要；如果没有这行代码，app/window/display 无法参与匹配。
        required_flags = _phase60_required_flags_for_scope([normalized_action])  # 新增代码+Phase60PersistentGrants: 计算本次动作需要的 flags；如果没有这行代码，旧 grant 的高风险缺口无法在 evaluate 时兜底。
        state = self._read_state()  # 新增代码+Phase60PersistentGrants: 读取授权状态；如果没有这行代码，评估没有事实来源。
        first_expired: dict[str, Any] | None = None  # 新增代码+Phase60PersistentGrants: 准备记录第一个过期匹配授权；如果没有这行代码，过期拒绝无法指出 grant_id。
        first_revoked: dict[str, Any] | None = None  # 新增代码+Phase60PersistentGrants: 准备记录第一个撤销匹配授权；如果没有这行代码，撤销拒绝无法指出 grant_id。
        now = time.time()  # 新增代码+Phase60PersistentGrants: 捕获当前时间用于过期判断；如果没有这行代码，TTL 不会真正生效。
        for grant in list(state.get("grants", [])):  # 新增代码+Phase60PersistentGrants: 遍历所有授权记录；如果没有这行代码，无法寻找匹配 grant。
            if not _phase60_grant_matches(grant, safe_session_id, normalized_action, target):  # 新增代码+Phase60PersistentGrants: 跳过不匹配会话、app、窗口、显示器或 scope 的授权；如果没有这行代码，错误授权会误放行。
                continue  # 新增代码+Phase60PersistentGrants: 继续检查下一条 grant；如果没有这行代码，循环语义不完整。
            if bool(grant.get("revoked", False)):  # 新增代码+Phase60PersistentGrants: 撤销授权不能放行动作；如果没有这行代码，revoke 后仍可能执行。
                first_revoked = first_revoked or grant  # 新增代码+Phase60PersistentGrants: 保存第一条撤销证据；如果没有这行代码，后续拒绝缺少 grant_id。
                continue  # 新增代码+Phase60PersistentGrants: 撤销记录不参与允许；如果没有这行代码，后续会继续判过期或允许。
            if float(grant.get("expires_at_epoch", 0.0) or 0.0) < now:  # 新增代码+Phase60PersistentGrants: 过期授权不能放行动作；如果没有这行代码，TTL 形同虚设。
                first_expired = first_expired or grant  # 新增代码+Phase60PersistentGrants: 保存第一条过期证据；如果没有这行代码，用户不知道哪个 grant 过期。
                continue  # 新增代码+Phase60PersistentGrants: 过期记录不参与允许；如果没有这行代码，后续可能误放行。
            missing_flags = [name for name in required_flags if not dict(grant.get("grant_flags", {})).get(name, False)]  # 新增代码+Phase60PersistentGrants: 兜底检查 grant flags 是否覆盖动作；如果没有这行代码，旧状态可能绕过高风险门禁。
            if missing_flags:  # 新增代码+Phase60PersistentGrants: 缺 flag 时拒绝；如果没有这行代码，系统键和剪贴板风险可能漏过。
                return {"allowed": False, "decision": "grant_missing_required_flags", "grant_id": grant.get("grant_id", ""), "missing_grant_flags": missing_flags, "target_summary": target, "marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, "actions_expanded": PHASE60_ACTIONS_EXPANDED}  # 新增代码+Phase60PersistentGrants: 返回缺 flag 拒绝；如果没有这行代码，用户不知道要补什么权限。
            return {"allowed": True, "decision": "allowed_by_persistent_grant", "grant_id": grant.get("grant_id", ""), "grant_flags": dict(grant.get("grant_flags", {})), "target_summary": target, "marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, "actions_expanded": PHASE60_ACTIONS_EXPANDED}  # 新增代码+Phase60PersistentGrants: 返回授权允许结果；如果没有这行代码，controller 无法知道动作可以继续。
        if first_revoked is not None:  # 新增代码+Phase60PersistentGrants: 若只命中撤销 grant，则明确返回 revoked；如果没有这行代码，用户会误以为从未授权。
            return {"allowed": False, "decision": "grant_revoked", "grant_id": first_revoked.get("grant_id", ""), "target_summary": target, "marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, "actions_expanded": PHASE60_ACTIONS_EXPANDED}  # 新增代码+Phase60PersistentGrants: 返回撤销拒绝；如果没有这行代码，revoke 的效果不可解释。
        if first_expired is not None:  # 新增代码+Phase60PersistentGrants: 若只命中过期 grant，则明确返回 expired；如果没有这行代码，用户会误以为没有授权过。
            return {"allowed": False, "decision": "grant_expired", "grant_id": first_expired.get("grant_id", ""), "target_summary": target, "marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, "actions_expanded": PHASE60_ACTIONS_EXPANDED}  # 新增代码+Phase60PersistentGrants: 返回过期拒绝；如果没有这行代码，TTL 拒绝不可解释。
        return {"allowed": False, "decision": "requires_approval", "grant_id": "", "target_summary": target, "marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, "actions_expanded": PHASE60_ACTIONS_EXPANDED}  # 新增代码+Phase60PersistentGrants: 没有任何匹配授权时要求审批；如果没有这行代码，默认拒绝基线不存在。
    # 新增代码+Phase60PersistentGrants: 函数段结束，WindowsComputerUsePersistentGrantStore.evaluate 到此结束；如果没有这个边界说明，初学者不容易看出动作评估范围。

    def status(self, session_id: Any | None = None) -> dict[str, Any]:  # 新增代码+Phase60PersistentGrants: 函数段开始，返回持久授权状态摘要；如果没有这段函数，/computer status 和 /computer grants 不能共享事实源。
        state = self._read_state()  # 新增代码+Phase60PersistentGrants: 读取当前授权状态；如果没有这行代码，状态没有事实来源。
        now = time.time()  # 新增代码+Phase60PersistentGrants: 捕获当前时间用于 active/expired 分类；如果没有这行代码，过期数量不准确。
        safe_session = _phase60_safe_session_id(session_id) if session_id is not None else ""  # 新增代码+Phase60PersistentGrants: 可选清理 session 过滤条件；如果没有这行代码，状态无法按会话聚焦。
        grants = [grant for grant in list(state.get("grants", [])) if not safe_session or grant.get("session_id") == safe_session]  # 新增代码+Phase60PersistentGrants: 按 session 过滤授权；如果没有这行代码，终端会混入其他会话。
        active = [grant for grant in grants if not grant.get("revoked", False) and float(grant.get("expires_at_epoch", 0.0) or 0.0) >= now]  # 新增代码+Phase60PersistentGrants: 计算仍有效授权；如果没有这行代码，用户看不到当前可用 grant 数。
        revoked = [grant for grant in grants if grant.get("revoked", False)]  # 新增代码+Phase60PersistentGrants: 计算已撤销授权；如果没有这行代码，revoke 状态不可见。
        expired = [grant for grant in grants if not grant.get("revoked", False) and float(grant.get("expires_at_epoch", 0.0) or 0.0) < now]  # 新增代码+Phase60PersistentGrants: 计算已过期授权；如果没有这行代码，TTL 状态不可见。
        return {"enabled": True, "model": PHASE60_PERSISTENT_GRANTS_MODEL, "marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, "state_path": str(self.state_path), "audit_path": str(self.audit_path), "session_id": safe_session, "grant_count": len(grants), "active_count": len(active), "revoked_count": len(revoked), "expired_count": len(expired), "grants": grants, "actions_expanded": PHASE60_ACTIONS_EXPANDED}  # 新增代码+Phase60PersistentGrants: 返回机器可读状态；如果没有这行代码，renderer 无法展示授权摘要。
    # 新增代码+Phase60PersistentGrants: 函数段结束，WindowsComputerUsePersistentGrantStore.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def terminal_status_lines(self, session_id: Any | None = DEFAULT_PERSISTENT_GRANT_SESSION_ID) -> list[str]:  # 新增代码+Phase60PersistentGrants: 函数段开始，生成终端可读持久授权面板；如果没有这段函数，小白用户只能读 JSON。
        status = self.status(session_id)  # 新增代码+Phase60PersistentGrants: 读取机器状态；如果没有这行代码，终端文本没有事实来源。
        lines = ["Computer Persistent Grants", f"- marker={PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER}", f"- grant_model={PHASE60_PERSISTENT_GRANTS_MODEL}", f"- active_count={status.get('active_count', 0)} revoked_count={status.get('revoked_count', 0)} expired_count={status.get('expired_count', 0)} grant_count={status.get('grant_count', 0)}", f"- state_path={status.get('state_path', '')}", f"- audit_path={status.get('audit_path', '')}"]  # 新增代码+Phase60PersistentGrants: 构造面板头部；如果没有这行代码，用户看不到 marker、数量和文件位置。
        for grant in list(status.get("grants", []))[:6]:  # 新增代码+Phase60PersistentGrants: 最多展示前六条避免刷屏；如果没有这行代码，大量历史授权会淹没终端。
            scope_text = ",".join(list(grant.get("action_scope", [])))  # 新增代码+Phase60PersistentGrants: 格式化动作范围；如果没有这行代码，用户看不懂授权覆盖哪些动作。
            flag_text = ",".join(name for name, enabled in sorted(dict(grant.get("grant_flags", {})).items()) if enabled) or "(none)"  # 新增代码+Phase60PersistentGrants: 格式化已启用 flags；如果没有这行代码，高风险权限不可扫描。
            lines.append(f"- grant_id={grant.get('grant_id', '')} app={grant.get('app', '')} scope={scope_text} flags={flag_text} expires_at={grant.get('expires_at', '')} revoked={_phase60_bool_token(grant.get('revoked'))}")  # 新增代码+Phase60PersistentGrants: 输出单条授权摘要；如果没有这行代码，用户无法定位要撤销的 grant。
        lines.append(f"- actions_expanded={_phase60_bool_token(PHASE60_ACTIONS_EXPANDED)}")  # 新增代码+Phase60PersistentGrants: 输出动作边界；如果没有这行代码，状态面板可能被误解成动作能力扩大。
        return lines  # 新增代码+Phase60PersistentGrants: 返回终端面板行；如果没有这行代码，调用方无法打印状态。
    # 新增代码+Phase60PersistentGrants: 函数段结束，WindowsComputerUsePersistentGrantStore.terminal_status_lines 到此结束；如果没有这个边界说明，初学者不容易看出终端状态范围。
# 新增代码+Phase60PersistentGrants: 类段结束，WindowsComputerUsePersistentGrantStore 到此结束；如果没有这个边界说明，初学者不容易看出持久授权类范围。


def run_phase60_persistent_grants_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase60PersistentGrants: 函数段开始，运行 Phase60 持久授权合同自检；如果没有这段函数，CLI 和真实终端没有统一验收入口。
    store = WindowsComputerUsePersistentGrantStore(base_dir=Path(base_dir) if base_dir is not None else None)  # 新增代码+Phase60PersistentGrants: 创建指定或默认 store；如果没有这行代码，自检没有授权事实源。
    session_prefix = f"phase60-contract-{int(time.time() * 1000)}"  # 新增代码+Phase60PersistentGrants: 生成本次自检唯一会话前缀；如果没有这行代码，多次运行可能互相污染。
    safe_window = {"app_id": "notepad.exe", "process_name": "notepad.exe", "window_id": "hwnd:phase60-safe", "title_preview": "Phase60 Notepad", "display_id": "DISPLAY1"}  # 新增代码+Phase60PersistentGrants: 构造安全窗口样本；如果没有这行代码，授权评估没有正例目标。
    approve = store.approve(session_id=session_prefix + "-approve", app="notepad.exe", window_id="hwnd:phase60-safe", display_id="DISPLAY1", action_scope=["click"], ttl_seconds=60, reason="phase60-contract-approve", grant_flags={"desktopAction": True})  # 新增代码+Phase60PersistentGrants: 写入正例授权；如果没有这行代码，approve=true 没有证据。
    allowed = store.evaluate(session_id=session_prefix + "-approve", action="click", arguments={"window": safe_window})  # 新增代码+Phase60PersistentGrants: 评估正例授权；如果没有这行代码，无法证明 approve 会参与 evaluate。
    unauthorized = store.evaluate(session_id=session_prefix + "-unauthorized", action="click", arguments={"window": safe_window})  # 新增代码+Phase60PersistentGrants: 评估未授权会话；如果没有这行代码，默认拒绝没有证据。
    expired_grant = store.approve(session_id=session_prefix + "-expired", app="notepad.exe", action_scope=["click"], ttl_seconds=-1, reason="phase60-contract-expired", grant_flags={"desktopAction": True})  # 新增代码+Phase60PersistentGrants: 写入已过期授权；如果没有这行代码，expired_denied 没有样本。
    expired = store.evaluate(session_id=session_prefix + "-expired", action="click", arguments={"window": safe_window})  # 新增代码+Phase60PersistentGrants: 评估过期授权；如果没有这行代码，TTL 拒绝无法验证。
    live_grant = store.approve(session_id=session_prefix + "-revoked", app="notepad.exe", action_scope=["type_text"], ttl_seconds=60, reason="phase60-contract-revoke", grant_flags={"desktopAction": True})  # 新增代码+Phase60PersistentGrants: 写入可撤销授权；如果没有这行代码，revoked_denied 没有目标。
    revoke = store.revoke(session_id=session_prefix + "-revoked", grant_id=live_grant.get("grant_id", ""), reason="phase60-contract-revoke")  # 新增代码+Phase60PersistentGrants: 撤销刚写入的授权；如果没有这行代码，revoke 路径没有证据。
    revoked = store.evaluate(session_id=session_prefix + "-revoked", action="type_text", arguments={"window": safe_window})  # 新增代码+Phase60PersistentGrants: 评估撤销后的动作；如果没有这行代码，撤销拒绝无法验证。
    high_risk = store.approve(session_id=session_prefix + "-high-risk", app="notepad.exe", action_scope=["press_key"], ttl_seconds=60, reason="phase60-contract-high-risk", grant_flags={"desktopAction": True})  # 新增代码+Phase60PersistentGrants: 尝试未显式 systemKeyCombos 的系统键授权；如果没有这行代码，高风险默认拒绝没有证据。
    status_text = "\n".join(store.terminal_status_lines(session_prefix + "-approve"))  # 新增代码+Phase60PersistentGrants: 渲染终端授权状态；如果没有这行代码，terminal_status 无法验证。
    approve_ok = bool(approve.get("approved") and allowed.get("allowed") and allowed.get("decision") == "allowed_by_persistent_grant")  # 新增代码+Phase60PersistentGrants: 汇总 approve 正例结果；如果没有这行代码，报告无法表达授权放行是否成立。
    unauthorized_denied = bool(not unauthorized.get("allowed") and unauthorized.get("decision") == "requires_approval")  # 新增代码+Phase60PersistentGrants: 汇总未授权拒绝结果；如果没有这行代码，默认拒绝无法进入 token。
    expired_denied = bool(expired_grant.get("approved") and not expired.get("allowed") and expired.get("decision") == "grant_expired")  # 新增代码+Phase60PersistentGrants: 汇总过期拒绝结果；如果没有这行代码，TTL 验收无法进入 token。
    revoked_denied = bool(revoke.get("revoked") and not revoked.get("allowed") and revoked.get("decision") == "grant_revoked")  # 新增代码+Phase60PersistentGrants: 汇总撤销拒绝结果；如果没有这行代码，revoke 验收无法进入 token。
    high_risk_default = bool(not high_risk.get("approved") and high_risk.get("decision") == "high_risk_requires_explicit_grant" and "systemKeyCombos" in list(high_risk.get("missing_grant_flags", [])))  # 新增代码+Phase60PersistentGrants: 汇总系统键默认拒绝结果；如果没有这行代码，高风险门禁无法进入 token。
    terminal_status = bool("Computer Persistent Grants" in status_text and PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER in status_text and "active_count=" in status_text)  # 新增代码+Phase60PersistentGrants: 汇总终端状态可读结果；如果没有这行代码，状态面板接入无法验收。
    passed = bool(approve_ok and unauthorized_denied and expired_denied and revoked_denied and high_risk_default and terminal_status and not PHASE60_ACTIONS_EXPANDED)  # 新增代码+Phase60PersistentGrants: 汇总合同是否通过；如果没有这行代码，main 无法用退出码表达失败。
    return {"marker": PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, "ok_token": PHASE60_WINDOWS_PERSISTENT_GRANTS_OK_TOKEN, "approve": approve_ok, "unauthorized_denied": unauthorized_denied, "expired_denied": expired_denied, "revoked_denied": revoked_denied, "high_risk_default": high_risk_default, "terminal_status": terminal_status, "actions_expanded": PHASE60_ACTIONS_EXPANDED, "passed": passed, "state_dir": str(store.base_dir)}  # 新增代码+Phase60PersistentGrants: 返回完整合同报告；如果没有这行代码，测试和真实终端拿不到统一结果。
# 新增代码+Phase60PersistentGrants: 函数段结束，run_phase60_persistent_grants_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase60_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase60PersistentGrants: 函数段开始，把合同报告转成稳定单行 token；如果没有这段函数，真实终端场景要解析复杂 JSON。
    return f"{PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER} {PHASE60_WINDOWS_PERSISTENT_GRANTS_OK_TOKEN} approve={_phase60_bool_token(report.get('approve'))} unauthorized_denied={_phase60_bool_token(report.get('unauthorized_denied'))} expired_denied={_phase60_bool_token(report.get('expired_denied'))} revoked_denied={_phase60_bool_token(report.get('revoked_denied'))} high_risk_default={_phase60_bool_token(report.get('high_risk_default'))} terminal_status={_phase60_bool_token(report.get('terminal_status'))} actions_expanded={_phase60_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase60PersistentGrants: 返回固定顺序 token；如果没有这行代码，验收输出容易漂移。
# 新增代码+Phase60PersistentGrants: 函数段结束，phase60_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase60PersistentGrants: 函数段开始，提供命令行入口；如果没有这段函数，真实终端无法直接运行 Phase60 自检。
    _ = argv  # 新增代码+Phase60PersistentGrants: 保留 argv 供未来扩展；如果没有这行代码，参数存在但用途不清楚。
    report = run_phase60_persistent_grants_contract()  # 新增代码+Phase60PersistentGrants: 使用默认持久化目录运行合同；如果没有这行代码，CLI 不会证明真实 memory/persistent_grants 路径。
    print(phase60_cli_line(report))  # 新增代码+Phase60PersistentGrants: 打印稳定 token 行；如果没有这行代码，debug log 无法匹配 Phase60 成功。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase60PersistentGrants: 打印结构化报告；如果没有这行代码，失败时不易复盘。
    print(PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER)  # 新增代码+Phase60PersistentGrants: 单独打印 ready marker；如果没有这行代码，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase60PersistentGrants: 根据合同结果返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase60PersistentGrants: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["DEFAULT_PERSISTENT_GRANT_SESSION_ID", "DEFAULT_PERSISTENT_GRANTS_ROOT", "PHASE60_ACTIONS_EXPANDED", "PHASE60_PERSISTENT_GRANTS_MODEL", "PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER", "PHASE60_WINDOWS_PERSISTENT_GRANTS_OK_TOKEN", "WindowsComputerUsePersistentGrantStore", "main", "phase60_cli_line", "run_phase60_persistent_grants_contract"]  # 新增代码+Phase60PersistentGrants: 限定公开导出名称；如果没有这行代码，包导入容易暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase60PersistentGrants: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase60PersistentGrants: 用 main 返回码退出；如果没有这行代码，命令行状态不明确。
