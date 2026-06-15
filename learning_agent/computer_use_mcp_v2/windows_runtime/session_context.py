"""Windows Computer Use session context and AppState store."""  # 新增代码+Phase59SessionContextAppState: 标明本文件负责统一会话事实源；如果没有这行代码，读者不知道 allowed_apps、grant_flags、display、cleanup 等状态集中在哪里。
from __future__ import annotations  # 新增代码+Phase59SessionContextAppState: 启用延迟类型解析；如果没有这行代码，旧解释顺序下前向类型注解更容易失败。

import json  # 新增代码+Phase59SessionContextAppState: 导入 JSON 用于 CLI 结构化报告；如果没有这行代码，真实终端失败时不易复盘。
import re  # 新增代码+Phase59SessionContextAppState: 导入正则用于清理 session_id 文件名；如果没有这行代码，坏 session_id 可能生成危险路径。
import tempfile  # 新增代码+Phase59SessionContextAppState: 导入临时目录用于无副作用合同自检；如果没有这行代码，单元测试和 CLI 合同只能污染真实状态。
import time  # 新增代码+Phase59SessionContextAppState: 导入时间用于 created_at/updated_at；如果没有这行代码，状态文件无法审计新旧。
from pathlib import Path  # 新增代码+Phase59SessionContextAppState: 导入 Path 管理 Windows 路径；如果没有这行代码，状态目录拼接容易出错。
from typing import Any  # 新增代码+Phase59SessionContextAppState: 导入 Any 描述 JSON 风格上下文；如果没有这行代码，接口边界不清楚。

try:  # 新增代码+Phase59SessionContextAppState: 优先按包路径导入安全文件工具；如果没有这段代码，包运行模式无法原子读写 state。
    from learning_agent.runtime.files import FileLock, atomic_write_json, read_json_or_default  # 新增代码+Phase59SessionContextAppState: 复用文件锁、原子写和容错读；如果没有这行代码，并发 session state 可能损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase59SessionContextAppState: 兼容 start_oauth_agent.bat 脚本模式导入；如果没有这段代码，真实可见终端可能因包名前缀失败。
    if error.name not in {"learning_agent", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase59SessionContextAppState: 只允许包路径缺失时 fallback；如果没有这行代码，真实内部 bug 会被误吞。
        raise  # 新增代码+Phase59SessionContextAppState: 重新抛出非路径类导入错误；如果没有这行代码，排查 runtime.files 内部问题会困难。
    from runtime.files import FileLock, atomic_write_json, read_json_or_default  # 新增代码+Phase59SessionContextAppState: 脚本模式导入同目录文件工具；如果没有这行代码，bat 入口无法保存 session context。

PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER = "PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_READY"  # 新增代码+Phase59SessionContextAppState: 定义 Phase59 ready marker；如果没有这行代码，真实终端验收没有稳定锚点。
PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_OK_TOKEN = "PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_OK"  # 新增代码+Phase59SessionContextAppState: 定义 Phase59 OK token；如果没有这行代码，debug log 无法区分自检通过和普通输出。
PHASE59_SESSION_CONTEXT_MODEL = "phase59_windows_session_context_appstate"  # 新增代码+Phase59SessionContextAppState: 定义状态模型名；如果没有这行代码，状态 UI 无法说明当前事实源版本。
PHASE59_ACTIONS_EXPANDED = False  # 新增代码+Phase59SessionContextAppState: 明确 Phase59 只统一状态不扩大真实动作；如果没有这行代码，用户可能误以为本阶段新增了桌面控制。
DEFAULT_SESSION_CONTEXT_ID = "learning-agent-default-session"  # 新增代码+Phase59SessionContextAppState: 定义默认 session id；如果没有这行代码，终端状态不知道读取哪一份 context。
DEFAULT_SESSION_CONTEXT_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "session_state"  # 新增代码+Phase59SessionContextAppState: 定义默认持久化目录；如果没有这行代码，Phase59 不能满足落盘到 memory/computer_use/session_state 的目标。


def _phase59_bool_token(value: Any) -> str:  # 新增代码+Phase59SessionContextAppState: 函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会出现 True/False 漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase59SessionContextAppState: 返回 true/false 文本；如果没有这行代码，acceptance scenario 匹配不稳定。
# 新增代码+Phase59SessionContextAppState: 函数段结束，_phase59_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式范围。


def _phase59_timestamp() -> str:  # 新增代码+Phase59SessionContextAppState: 函数段开始，生成 UTC 时间戳；如果没有这段函数，状态写入会重复手写时间格式。
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())  # 新增代码+Phase59SessionContextAppState: 返回可排序 UTC 时间；如果没有这行代码，context 新旧无法审计。
# 新增代码+Phase59SessionContextAppState: 函数段结束，_phase59_timestamp 到此结束；如果没有这个边界说明，初学者不容易看出时间 helper 范围。


def _phase59_safe_session_id(session_id: Any) -> str:  # 新增代码+Phase59SessionContextAppState: 函数段开始，把任意 session_id 清理成安全文件名；如果没有这段函数，外部输入可能影响路径。
    text = str(session_id or DEFAULT_SESSION_CONTEXT_ID).strip()  # 新增代码+Phase59SessionContextAppState: 读取并去空白；如果没有这行代码，空 session_id 会生成空文件名。
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)[:120]  # 新增代码+Phase59SessionContextAppState: 只保留安全字符并限制长度；如果没有这行代码，路径穿越或超长文件名风险不可控。
    return cleaned or DEFAULT_SESSION_CONTEXT_ID  # 新增代码+Phase59SessionContextAppState: 空结果回到默认 session；如果没有这行代码，清理后可能仍然没有文件名。
# 新增代码+Phase59SessionContextAppState: 函数段结束，_phase59_safe_session_id 到此结束；如果没有这个边界说明，初学者不容易看出 id 清理范围。


def _phase59_list_of_dicts(value: Any) -> list[dict[str, Any]]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，规范化 hidden_windows 这类列表；如果没有这段函数，坏状态会污染 UI。
    return [dict(item) for item in list(value or []) if isinstance(item, dict)] if isinstance(value, list) else []  # 新增代码+Phase59SessionContextAppState: 只保留 dict 项并复制；如果没有这行代码，字符串或坏对象会让状态渲染崩溃。
# 新增代码+Phase59SessionContextAppState: 函数段结束，_phase59_list_of_dicts 到此结束；如果没有这个边界说明，初学者不容易看出列表清洗范围。


def _phase59_unique_texts(values: Any) -> list[str]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，规范化 allowed_apps 列表；如果没有这段函数，重复或空 app 会污染 allowlist。
    result: list[str] = []  # 新增代码+Phase59SessionContextAppState: 准备保存去重结果；如果没有这行代码，函数没有返回容器。
    for value in list(values or []):  # 新增代码+Phase59SessionContextAppState: 遍历输入值；如果没有这行代码，allowed_apps 不会被处理。
        text = str(value or "").strip().lower()  # 新增代码+Phase59SessionContextAppState: 清理并小写 app 名；如果没有这行代码，同一 app 会因大小写重复。
        if text and text not in result:  # 新增代码+Phase59SessionContextAppState: 跳过空值和重复项；如果没有这行代码，状态文件会越来越乱。
            result.append(text)  # 新增代码+Phase59SessionContextAppState: 记录唯一 app 名；如果没有这行代码，allowlist 会丢失有效输入。
    return result  # 新增代码+Phase59SessionContextAppState: 返回规范化列表；如果没有这行代码，调用方拿不到结果。
# 新增代码+Phase59SessionContextAppState: 函数段结束，_phase59_unique_texts 到此结束；如果没有这个边界说明，初学者不容易看出 app 清洗范围。


def _phase2_request_access_app_key(value: Any) -> str:  # 新增代码+Phase2SessionGrants：函数段开始，把目标应用名清理成授权匹配 key；如果没有这段函数，Notepad/NOTEPAD/notepad.exe 会因为写法不同误判。
    return str(value or "").strip().lower()  # 新增代码+Phase2SessionGrants：返回去空白小写文本；如果没有这一行，allowed_apps 和目标 app_id 无法稳定比较。
# 新增代码+Phase2SessionGrants：函数段结束，_phase2_request_access_app_key 到此结束；如果没有这个边界说明，用户不容易看出 app key 清理范围。


def _phase2_request_access_target_apps(target: Any) -> list[str]:  # 新增代码+Phase2SessionGrants：函数段开始，从动作目标里提取可匹配应用名；如果没有这段函数，授权判断只能看单一字段而漏掉 process_name。
    target_dict = dict(target or {}) if isinstance(target, dict) else {}  # 新增代码+Phase2SessionGrants：只接受 dict 目标并复制；如果没有这一行，坏类型会让授权判断崩溃。
    raw_values = [target_dict.get("app_id"), target_dict.get("app"), target_dict.get("process_name"), target_dict.get("launch_id")]  # 新增代码+Phase2SessionGrants：收集常见目标字段；如果没有这一行，不同调用层传入的目标名会互相不兼容。
    return _phase59_unique_texts(raw_values)  # 新增代码+Phase2SessionGrants：复用去重清洗后返回目标列表；如果没有这一行，后续匹配会重复处理空值和大小写。
# 新增代码+Phase2SessionGrants：函数段结束，_phase2_request_access_target_apps 到此结束；如果没有这个边界说明，用户不容易看出目标字段提取范围。


def _phase2_request_access_grant_expired(grant: dict[str, Any]) -> bool:  # 新增代码+Phase2SessionGrants：函数段开始，判断 request_access 授权是否过期；如果没有这段函数，TTL 字段只会记录不会阻断动作。
    if bool(grant.get("grant_expired")):  # 新增代码+Phase2SessionGrants：优先尊重显式过期标记；如果没有这一行，持久层已经判定过期的 grant 可能被重新放行。
        return True  # 新增代码+Phase2SessionGrants：显式过期时直接返回真；如果没有这一行，撤销/过期语义会变得不稳定。
    expires_at_epoch = float(grant.get("expires_at_epoch", 0.0) or 0.0)  # 新增代码+Phase2SessionGrants：读取过期时间戳；如果没有这一行，授权无法按时间自动失效。
    return bool(expires_at_epoch and expires_at_epoch < time.time())  # 新增代码+Phase2SessionGrants：当前时间超过 TTL 即过期；如果没有这一行，旧授权可能长期有效。
# 新增代码+Phase2SessionGrants：函数段结束，_phase2_request_access_grant_expired 到此结束；如果没有这个边界说明，用户不容易看出 TTL 判断范围。


def grant_scope_matches_target(grant: dict[str, Any] | None, target: dict[str, Any] | None) -> bool:  # 新增代码+Phase2SessionGrants：函数段开始，判断 request_access 授权是否覆盖目标应用；如果没有这段函数，allowed_apps 只是记录字段不会形成门禁。
    grant_dict = dict(grant or {}) if isinstance(grant, dict) else {}  # 新增代码+Phase2SessionGrants：只接受 dict 授权并复制；如果没有这一行，坏授权对象会让动作前门禁崩溃。
    allowed_apps = set(_phase59_unique_texts(grant_dict.get("allowed_apps", [])))  # 新增代码+Phase2SessionGrants：读取并规范化允许应用列表；如果没有这一行，授权范围无法比较。
    denied_apps = set(_phase59_unique_texts(grant_dict.get("denied_apps", [])))  # 新增代码+Phase2SessionGrants：读取并规范化显式拒绝应用列表；如果没有这一行，用户拒绝过的目标可能仍被通配授权放行。
    target_apps = set(_phase2_request_access_target_apps(target))  # 新增代码+Phase2SessionGrants：提取目标应用候选；如果没有这一行，门禁不知道本次动作要操作哪个 app。
    if not grant_dict or not target_apps:  # 新增代码+Phase2SessionGrants：授权或目标缺失时不能匹配；如果没有这一行，空数据可能被误认为匹配成功。
        return False  # 新增代码+Phase2SessionGrants：缺少必要事实时默认不放行；如果没有这一行，安全基线会从拒绝变成不确定。
    if denied_apps.intersection(target_apps):  # 新增代码+Phase2SessionGrants：先检查显式拒绝目标；如果没有这一行，拒绝列表会被 allowed_apps 覆盖。
        return False  # 新增代码+Phase2SessionGrants：命中拒绝列表时不匹配；如果没有这一行，被拒绝应用可能继续被控制。
    if "*" in allowed_apps or "all" in allowed_apps or "any" in allowed_apps:  # 新增代码+Phase2SessionGrants：允许短期通配授权；如果没有这一行，未来用户明确全局授权也无法表达。
        return True  # 新增代码+Phase2SessionGrants：通配授权且未命中拒绝列表时放行；如果没有这一行，通配语义不可用。
    return bool(allowed_apps.intersection(target_apps))  # 新增代码+Phase2SessionGrants：目标命中允许列表才匹配；如果没有这一行，函数没有最终匹配结果。
# 新增代码+Phase2SessionGrants：函数段结束，grant_scope_matches_target 到此结束；如果没有这个边界说明，用户不容易看出授权目标匹配范围。


def deny_action_without_request_access(grant: dict[str, Any] | None, target: dict[str, Any] | None, action: str = "desktopAction") -> dict[str, Any]:  # 新增代码+Phase2SessionGrants：函数段开始，在真实桌面动作前做 request_access 授权门禁；如果没有这段函数，动作可能先碰桌面再发现未授权。
    grant_dict = dict(grant or {}) if isinstance(grant, dict) else {}  # 新增代码+Phase2SessionGrants：复制授权对象避免外部污染；如果没有这一行，调用方后续修改会影响审计结果。
    target_dict = dict(target or {}) if isinstance(target, dict) else {}  # 新增代码+Phase2SessionGrants：复制目标对象用于返回摘要；如果没有这一行，拒绝报告缺少目标事实。
    request_access_session_id = str(grant_dict.get("request_access_session_id") or grant_dict.get("session_id") or "")  # 新增代码+Phase2SessionGrants：读取 request_access 会话 id；如果没有这一行，允许/拒绝决策无法追溯到哪次授权。
    base = {"allowed": False, "decision": "requires_approval", "requires_approval": True, "request_access_session_id": request_access_session_id, "target_summary": target_dict, "low_level_event_count": 0}  # 新增代码+Phase2SessionGrants：构造默认拒绝报告且低层事件为 0；如果没有这一行，拒绝路径无法证明没有触碰桌面。
    if not grant_dict:  # 新增代码+Phase2SessionGrants：没有 grant 时必须拒绝；如果没有这一行，空授权对象可能继续向后端流动。
        return base  # 新增代码+Phase2SessionGrants：返回需要审批的结构化拒绝；如果没有这一行，模型拿不到下一步应该 request_access 的信号。
    if bool(grant_dict.get("grant_revoked") or grant_dict.get("revoked")):  # 新增代码+Phase2SessionGrants：检查撤销标记；如果没有这一行，撤销授权仍可能有效。
        return {**base, "decision": "grant_revoked", "grant_revoked": True}  # 新增代码+Phase2SessionGrants：返回撤销拒绝；如果没有这一行，撤销和未授权会混在一起难排查。
    if _phase2_request_access_grant_expired(grant_dict):  # 新增代码+Phase2SessionGrants：检查过期状态；如果没有这一行，TTL 不会阻断旧授权。
        return {**base, "decision": "grant_expired", "grant_expired": True}  # 新增代码+Phase2SessionGrants：返回过期拒绝；如果没有这一行，用户看不出是授权超时。
    if not grant_scope_matches_target(grant_dict, target_dict):  # 新增代码+Phase2SessionGrants：检查目标 app 是否在授权范围；如果没有这一行，allowed_apps 边界不会生效。
        return {**base, "decision": "target_not_in_allowed_apps"}  # 新增代码+Phase2SessionGrants：返回目标越界拒绝；如果没有这一行，模型不知道需要重新申请哪个 app。
    flags = dict(grant_dict.get("grant_flags", {}) or {}) if isinstance(grant_dict.get("grant_flags", {}), dict) else {}  # 新增代码+Phase2SessionGrants：读取授权 flag 字典；如果没有这一行，高风险动作缺少显式权限判断。
    if action and action != "observe" and not bool(flags.get("desktopAction")):  # 新增代码+Phase2SessionGrants：非观察动作必须带 desktopAction；如果没有这一行，只读授权可能被误用来点击键盘。
        return {**base, "decision": "grant_missing_required_flags", "missing_grant_flags": ["desktopAction"]}  # 新增代码+Phase2SessionGrants：返回缺少权限位拒绝；如果没有这一行，权限不足原因不清楚。
    return {**base, "allowed": True, "decision": "allowed_by_request_access_grant", "requires_approval": False}  # 新增代码+Phase2SessionGrants：匹配授权时返回放行决策但仍不触碰桌面；如果没有这一行，授权永远无法通过。
# 新增代码+Phase2SessionGrants：函数段结束，deny_action_without_request_access 到此结束；如果没有这个边界说明，用户不容易看出动作前门禁范围。


class ComputerUseSessionContext:  # 新增代码+Phase59SessionContextAppState: 类段开始，包装单个 Computer Use session context；如果没有这个类，ClaudeCode 风格 AppState 没有清晰实体。
    def __init__(self, data: dict[str, Any]) -> None:  # 新增代码+Phase59SessionContextAppState: 函数段开始，接收规范化上下文字典；如果没有这段函数，调用方无法构造 context 对象。
        self.data = dict(data or {})  # 新增代码+Phase59SessionContextAppState: 保存字典副本避免外部污染；如果没有这行代码，调用方可能改坏内部状态。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContext.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，返回 JSON 可写状态；如果没有这段函数，store 无法安全写盘。
        return dict(self.data)  # 新增代码+Phase59SessionContextAppState: 返回浅拷贝；如果没有这行代码，外部会直接拿到内部对象。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContext.to_dict 到此结束；如果没有这个边界说明，初学者不容易看出导出范围。
# 新增代码+Phase59SessionContextAppState: 类段结束，ComputerUseSessionContext 到此结束；如果没有这个边界说明，初学者不容易看出 context 实体范围。


class ComputerUseSessionContextStore:  # 新增代码+Phase59SessionContextAppState: 类段开始，管理所有 session context 的持久化；如果没有这个类，状态会继续散落在 approval/runtime/status UI。
    def __init__(self, base_dir: str | Path | None = None, lock_timeout_seconds: float = 5.0) -> None:  # 新增代码+Phase59SessionContextAppState: 函数段开始，初始化状态目录和互斥锁；如果没有这段函数，测试和生产无法选择不同目录。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_SESSION_CONTEXT_ROOT  # 新增代码+Phase59SessionContextAppState: 保存状态根目录；如果没有这行代码，store 不知道读写哪里。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase59SessionContextAppState: 确保目录存在；如果没有这行代码，首次写入会失败。
        self.lock_timeout_seconds = float(lock_timeout_seconds)  # 新增代码+Phase59SessionContextAppState: 保存文件锁等待时间；如果没有这行代码，并发等待没有明确边界。
        self.mutex_path = self.base_dir / ".session_context.mutex"  # 新增代码+Phase59SessionContextAppState: 定义 store 级互斥锁文件；如果没有这行代码，并发写 state 可能互相覆盖。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _state_path(self, session_id: Any) -> Path:  # 新增代码+Phase59SessionContextAppState: 函数段开始，计算单个 session 的状态文件路径；如果没有这段函数，路径逻辑会散落重复。
        return self.base_dir / f"{_phase59_safe_session_id(session_id)}.json"  # 新增代码+Phase59SessionContextAppState: 返回安全文件名路径；如果没有这行代码，session_id 可能直接拼入路径。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore._state_path 到此结束；如果没有这个边界说明，初学者不容易看出路径范围。

    def _default_context(self, session_id: Any) -> dict[str, Any]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，构造空白 session context；如果没有这段函数，新会话没有统一字段。
        safe_session_id = _phase59_safe_session_id(session_id)  # 新增代码+Phase59SessionContextAppState: 清理 session_id；如果没有这行代码，默认 context 可能带危险 id。
        now = _phase59_timestamp()  # 新增代码+Phase59SessionContextAppState: 生成创建时间；如果没有这行代码，空 context 无法审计创建时刻。
        return {  # 修改代码+Phase2SessionGrants：返回完整默认字段并加入 request_access 授权事实；如果没有这一行，新会话没有统一状态容器。
            "schema_version": 1,  # 修改代码+Phase2SessionGrants：保留 schema 版本；如果没有这一行，旧状态迁移和排查无法判断结构版本。
            "model": PHASE59_SESSION_CONTEXT_MODEL,  # 修改代码+Phase2SessionGrants：保留状态模型名；如果没有这一行，状态 UI 不知道当前事实源版本。
            "marker": PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER,  # 修改代码+Phase2SessionGrants：保留 ready marker；如果没有这一行，真实终端验收缺少稳定锚点。
            "session_id": safe_session_id,  # 修改代码+Phase2SessionGrants：保存清理后的 session id；如果没有这一行，状态无法归属到具体会话。
            "request_access_session_id": safe_session_id,  # 新增代码+Phase2SessionGrants：保存 request_access 授权会话 id；如果没有这一行，授权决策无法追溯到申请会话。
            "allowed_apps": [],  # 修改代码+Phase2SessionGrants：保存允许控制的 app 列表；如果没有这一行，grant_scope_matches_target 没有 allowlist 来源。
            "denied_apps": [],  # 新增代码+Phase2SessionGrants：保存明确拒绝的 app 列表；如果没有这一行，用户拒绝过的目标可能被通配授权误放行。
            "grant_flags": {},  # 修改代码+Phase2SessionGrants：保存 desktopAction 等权限位；如果没有这一行，动作级权限无法表达。
            "grant_expires_at_epoch": 0.0,  # 新增代码+Phase2SessionGrants：保存授权过期时间戳；如果没有这一行，会话授权无法按 TTL 失效。
            "grant_expired": False,  # 新增代码+Phase2SessionGrants：保存授权是否已过期；如果没有这一行，矩阵和 UI 看不到过期状态。
            "grant_revoked": False,  # 新增代码+Phase2SessionGrants：保存授权是否已撤销；如果没有这一行，撤销语义无法进入 session 事实源。
            "selected_display": {},  # 修改代码+Phase2SessionGrants：保留选中显示器；如果没有这一行，多屏状态无法记录。
            "last_screenshot_dims": {},  # 修改代码+Phase2SessionGrants：保留最后截图尺寸；如果没有这一行，坐标换算缺少屏幕尺寸事实。
            "display_pinned": False,  # 新增代码+Phase3DisplayPin：保存当前截图是否固定到某个显示器；如果没有这一行，多屏坐标无法判断是否可复用。
            "display_origin": {},  # 新增代码+Phase3DisplayPin：保存固定显示器的逻辑和物理原点；如果没有这一行，副屏偏移会在后续动作中丢失。
            "display_scale": {"x": 1.0, "y": 1.0},  # 新增代码+Phase3DisplayPin：保存固定显示器的 DPI 缩放；如果没有这一行，高 DPI 点击会缺少换算比例。
            "hidden_windows": [],  # 修改代码+Phase2SessionGrants：保留隐藏窗口列表；如果没有这一行，cleanup 无法恢复宿主窗口状态。
            "host_windows_hidden": False,  # 新增代码+Phase4TurnCleanup：保存宿主窗口是否被隐藏；如果没有这一行，cleanup 不知道是否需要执行 unhide。
            "last_action": {},  # 修改代码+Phase2SessionGrants：保留最近动作；如果没有这一行，状态 UI 无法解释刚做了什么。
            "last_error": {},  # 修改代码+Phase2SessionGrants：保留最近错误；如果没有这一行，失败排查缺少上下文。
            "cleanup_completed": False,  # 修改代码+Phase2SessionGrants：保留 cleanup 状态；如果没有这一行，任务结束后无法证明状态已清理。
            "cleanup_reason": "",  # 修改代码+Phase2SessionGrants：保留 cleanup 原因；如果没有这一行，审计不知道为什么清理。
            "created_at": now,  # 修改代码+Phase2SessionGrants：保留创建时间；如果没有这一行，状态新旧无法审计。
            "updated_at": now,  # 修改代码+Phase2SessionGrants：保留更新时间；如果没有这一行，多轮任务无法判断状态是否新鲜。
            "state_path": str(self._state_path(safe_session_id)),  # 修改代码+Phase2SessionGrants：保留状态文件路径；如果没有这一行，排查时不知道数据落盘位置。
            "actions_expanded": PHASE59_ACTIONS_EXPANDED,  # 修改代码+Phase2SessionGrants：保留动作扩展边界；如果没有这一行，用户可能误以为本阶段扩大了真实动作面。
        }  # 修改代码+Phase2SessionGrants：默认 context 字典结束；如果没有这一行，Python 字典结构不完整。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore._default_context 到此结束；如果没有这个边界说明，初学者不容易看出默认字段范围。

    def _normalize_context(self, session_id: Any, payload: Any) -> dict[str, Any]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，修复旧/坏 context 为标准结构；如果没有这段函数，损坏状态会拖垮 status。
        context = self._default_context(session_id)  # 新增代码+Phase59SessionContextAppState: 先创建完整默认值；如果没有这行代码，缺字段无法补齐。
        if isinstance(payload, dict):  # 新增代码+Phase59SessionContextAppState: 只有 dict 状态才合并；如果没有这行代码，坏类型会污染 context。
            context.update(dict(payload))  # 新增代码+Phase59SessionContextAppState: 合并已有字段；如果没有这行代码，持久化数据无法恢复。
        context["session_id"] = _phase59_safe_session_id(context.get("session_id", session_id))  # 新增代码+Phase59SessionContextAppState: 重新清理 session_id；如果没有这行代码，旧坏 id 会残留。
        context["request_access_session_id"] = _phase59_safe_session_id(context.get("request_access_session_id") or context["session_id"])  # 新增代码+Phase2SessionGrants：规范化 request_access 会话 id；如果没有这一行，授权审计无法稳定关联会话。
        context["allowed_apps"] = _phase59_unique_texts(context.get("allowed_apps", []))  # 新增代码+Phase59SessionContextAppState: 规范化 allowed_apps；如果没有这行代码，重复 app 会污染状态。
        context["denied_apps"] = _phase59_unique_texts(context.get("denied_apps", []))  # 新增代码+Phase2SessionGrants：规范化 denied_apps；如果没有这一行，显式拒绝列表可能被坏数据污染。
        context["grant_flags"] = {str(key): bool(value) for key, value in dict(context.get("grant_flags", {}) or {}).items()}  # 新增代码+Phase59SessionContextAppState: 规范化 grant_flags；如果没有这行代码，字符串 false 可能被误用。
        context["grant_expires_at_epoch"] = float(context.get("grant_expires_at_epoch", 0.0) or 0.0)  # 新增代码+Phase2SessionGrants：规范化授权过期时间；如果没有这一行，TTL 字段可能以字符串形式误导判断。
        context["grant_expired"] = bool(context.get("grant_expired", False))  # 新增代码+Phase2SessionGrants：规范化授权过期布尔值；如果没有这一行，状态 token 可能不稳定。
        context["grant_revoked"] = bool(context.get("grant_revoked", False))  # 新增代码+Phase2SessionGrants：规范化授权撤销布尔值；如果没有这一行，撤销状态可能被字符串误用。
        context["selected_display"] = dict(context.get("selected_display", {}) or {}) if isinstance(context.get("selected_display", {}), dict) else {}  # 新增代码+Phase59SessionContextAppState: 规范化显示器选择；如果没有这行代码，坏显示器字段会让 status 崩溃。
        context["last_screenshot_dims"] = dict(context.get("last_screenshot_dims", {}) or {}) if isinstance(context.get("last_screenshot_dims", {}), dict) else {}  # 新增代码+Phase59SessionContextAppState: 规范化截图尺寸；如果没有这行代码，截图状态无法安全读取。
        context["display_pinned"] = bool(context.get("display_pinned", False))  # 新增代码+Phase3DisplayPin：规范化显示器固定布尔值；如果没有这一行，字符串 false 可能被误当真。
        context["display_origin"] = dict(context.get("display_origin", {}) or {}) if isinstance(context.get("display_origin", {}), dict) else {}  # 新增代码+Phase3DisplayPin：规范化显示器原点；如果没有这一行，坏原点字段会让坐标换算崩溃。
        context["display_scale"] = dict(context.get("display_scale", {"x": 1.0, "y": 1.0}) or {"x": 1.0, "y": 1.0}) if isinstance(context.get("display_scale", {"x": 1.0, "y": 1.0}), dict) else {"x": 1.0, "y": 1.0}  # 新增代码+Phase3DisplayPin：规范化 DPI 缩放字典；如果没有这一行，坏缩放字段会污染后续物理坐标。
        context["hidden_windows"] = _phase59_list_of_dicts(context.get("hidden_windows", []))  # 新增代码+Phase59SessionContextAppState: 规范化隐藏窗口列表；如果没有这行代码，坏列表会污染状态 UI。
        context["host_windows_hidden"] = bool(context.get("host_windows_hidden", False))  # 新增代码+Phase4TurnCleanup：规范化 host hidden 布尔值；如果没有这一行，字符串 false 可能被误当成隐藏状态。
        context["last_action"] = dict(context.get("last_action", {}) or {}) if isinstance(context.get("last_action", {}), dict) else {}  # 新增代码+Phase59SessionContextAppState: 规范化最近动作；如果没有这行代码，last_action 可能不是可读对象。
        context["last_error"] = dict(context.get("last_error", {}) or {}) if isinstance(context.get("last_error", {}), dict) else {}  # 新增代码+Phase59SessionContextAppState: 规范化最近错误；如果没有这行代码，错误状态可能打坏渲染。
        context["cleanup_completed"] = bool(context.get("cleanup_completed", False))  # 新增代码+Phase59SessionContextAppState: 规范化 cleanup 布尔值；如果没有这行代码，字符串值会导致 token 不稳定。
        context["state_path"] = str(self._state_path(context["session_id"]))  # 新增代码+Phase59SessionContextAppState: 刷新实际状态路径；如果没有这行代码，移动目录后 state_path 会过期。
        context["model"] = PHASE59_SESSION_CONTEXT_MODEL  # 新增代码+Phase59SessionContextAppState: 固定模型名；如果没有这行代码，旧状态可能显示错误模型。
        context["marker"] = PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER  # 新增代码+Phase59SessionContextAppState: 固定 marker；如果没有这行代码，状态 UI 缺少阶段锚点。
        context["actions_expanded"] = PHASE59_ACTIONS_EXPANDED  # 新增代码+Phase59SessionContextAppState: 固定动作面边界；如果没有这行代码，状态可能被误读为动作扩展。
        return context  # 新增代码+Phase59SessionContextAppState: 返回规范化 context；如果没有这行代码，调用方拿不到清洗结果。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore._normalize_context 到此结束；如果没有这个边界说明，初学者不容易看出清洗范围。

    def _read_context(self, session_id: Any) -> dict[str, Any]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，读取并规范化 context；如果没有这段函数，每个公开方法都要重复读逻辑。
        state_path = self._state_path(session_id)  # 新增代码+Phase59SessionContextAppState: 计算状态文件路径；如果没有这行代码，无法读取对应 session。
        payload = read_json_or_default(state_path, {})  # 新增代码+Phase59SessionContextAppState: 容错读取 JSON；如果没有这行代码，首次运行或半写文件会崩溃。
        return self._normalize_context(session_id, payload)  # 新增代码+Phase59SessionContextAppState: 返回规范化结果；如果没有这行代码，坏状态不会被修复。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore._read_context 到此结束；如果没有这个边界说明，初学者不容易看出读取范围。

    def _write_context(self, context: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，原子写入 context；如果没有这段函数，状态落盘会重复且不安全。
        context["updated_at"] = _phase59_timestamp()  # 新增代码+Phase59SessionContextAppState: 刷新更新时间；如果没有这行代码，多轮状态无法判断新旧。
        normalized = self._normalize_context(context.get("session_id", DEFAULT_SESSION_CONTEXT_ID), context)  # 新增代码+Phase59SessionContextAppState: 写入前再规范化；如果没有这行代码，调用方坏字段可能落盘。
        atomic_write_json(self._state_path(normalized["session_id"]), normalized)  # 新增代码+Phase59SessionContextAppState: 原子写入 JSON；如果没有这行代码，崩溃时可能留下半个 state。
        return normalized  # 新增代码+Phase59SessionContextAppState: 返回实际写入内容；如果没有这行代码，调用方拿不到 state_path 和更新时间。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore._write_context 到此结束；如果没有这个边界说明，初学者不容易看出写入范围。

    def snapshot(self, session_id: Any = DEFAULT_SESSION_CONTEXT_ID) -> dict[str, Any]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，公开读取某个 session context；如果没有这段函数，状态 UI 和 verifier 无法读同一事实源。
        return self._read_context(session_id)  # 新增代码+Phase59SessionContextAppState: 返回规范化 context；如果没有这行代码，公开读取没有结果。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore.snapshot 到此结束；如果没有这个边界说明，初学者不容易看出读取入口范围。

    def bind_context(  # 修改代码+Phase2SessionGrants：函数段开始，绑定当前工具调用和 request_access 授权事实；如果没有这段函数，权限和显示器状态仍会散落。
        self,  # 修改代码+Phase2SessionGrants：接收 store 实例；如果没有这一行，方法无法访问状态目录和文件锁。
        session_id: Any = DEFAULT_SESSION_CONTEXT_ID,  # 修改代码+Phase2SessionGrants：接收会话 id；如果没有这一行，授权无法归属到具体会话。
        *,  # 修改代码+Phase2SessionGrants：后续参数强制关键字传入；如果没有这一行，调用方容易把 allowed_apps 和 flags 顺序传错。
        request_access_session_id: Any = None,  # 新增代码+Phase2SessionGrants：接收 request_access 授权会话 id；如果没有这一行，授权申请和动作放行无法关联。
        allowed_apps: Any = None,  # 修改代码+Phase2SessionGrants：接收允许控制的应用列表；如果没有这一行，allowlist 无法写入 session context。
        denied_apps: Any = None,  # 新增代码+Phase2SessionGrants：接收明确拒绝的应用列表；如果没有这一行，用户拒绝项无法进入门禁。
        grant_flags: dict[str, Any] | None = None,  # 修改代码+Phase2SessionGrants：接收 desktopAction 等权限位；如果没有这一行，动作权限无法写入 session context。
        grant_expires_at_epoch: float | int | None = None,  # 新增代码+Phase2SessionGrants：接收授权过期时间戳；如果没有这一行，授权不能按 TTL 管理。
        grant_expired: bool = False,  # 新增代码+Phase2SessionGrants：接收授权是否过期；如果没有这一行，过期事实无法落入 session context。
        grant_revoked: bool = False,  # 新增代码+Phase2SessionGrants：接收授权是否撤销；如果没有这一行，撤销事实无法落入 session context。
        selected_display: dict[str, Any] | None = None,  # 修改代码+Phase2SessionGrants：接收选中显示器；如果没有这一行，多屏上下文无法更新。
        last_screenshot_dims: dict[str, Any] | None = None,  # 修改代码+Phase2SessionGrants：接收最后截图尺寸；如果没有这一行，坐标上下文无法更新。
        display_pinned: bool | None = None,  # 新增代码+Phase3DisplayPin：接收显示器固定状态；如果没有这一行，pin_display_for_screenshot 无法把 pin 写入统一事实源。
        display_origin: dict[str, Any] | None = None,  # 新增代码+Phase3DisplayPin：接收显示器原点；如果没有这一行，副屏坐标原点无法持久化。
        display_scale: dict[str, Any] | None = None,  # 新增代码+Phase3DisplayPin：接收显示器缩放；如果没有这一行，高 DPI 比例无法持久化。
        hidden_windows: list[dict[str, Any]] | None = None,  # 新增代码+Phase4TurnCleanup：接收隐藏 host 窗口列表；如果没有这一行，hide 阶段无法把恢复目标写入 context。
        host_windows_hidden: bool | None = None,  # 新增代码+Phase4TurnCleanup：接收宿主窗口隐藏状态；如果没有这一行，cleanup 不知道是否需要 unhide。
    ) -> dict[str, Any]:  # 修改代码+Phase2SessionGrants：返回写入后的 context；如果没有这一行，调用方拿不到落盘状态。
        with FileLock(self.mutex_path, timeout_seconds=self.lock_timeout_seconds):  # 新增代码+Phase59SessionContextAppState: 用互斥锁保护读改写；如果没有这行代码，并发 bind 会互相覆盖。
            context = self._read_context(session_id)  # 新增代码+Phase59SessionContextAppState: 读取已有 context；如果没有这行代码，bind 会覆盖历史状态。
            if request_access_session_id is not None:  # 新增代码+Phase2SessionGrants：仅在调用方提供授权会话 id 时更新；如果没有这一行，空参数会覆盖已有授权归属。
                context["request_access_session_id"] = _phase59_safe_session_id(request_access_session_id)  # 新增代码+Phase2SessionGrants：保存清理后的 request_access 会话 id；如果没有这一行，授权审计可能带危险或不稳定 id。
            context["allowed_apps"] = _phase59_unique_texts([*context.get("allowed_apps", []), *list(allowed_apps or [])])  # 新增代码+Phase59SessionContextAppState: 合并 allowed_apps；如果没有这行代码，新授权不会进入统一事实源。
            context["denied_apps"] = _phase59_unique_texts([*context.get("denied_apps", []), *list(denied_apps or [])])  # 新增代码+Phase2SessionGrants：合并 denied_apps；如果没有这一行，显式拒绝的应用不会进入统一事实源。
            context["grant_flags"].update({str(key): bool(value) for key, value in dict(grant_flags or {}).items()})  # 新增代码+Phase59SessionContextAppState: 合并 grant_flags；如果没有这行代码，权限选择不会进入统一事实源。
            if grant_expires_at_epoch is not None:  # 新增代码+Phase2SessionGrants：仅在调用方提供 TTL 时更新；如果没有这一行，空参数会把已有过期时间清掉。
                context["grant_expires_at_epoch"] = float(grant_expires_at_epoch or 0.0)  # 新增代码+Phase2SessionGrants：保存授权过期时间戳；如果没有这一行，会话授权无法按时间失效。
            context["grant_expired"] = bool(grant_expired)  # 新增代码+Phase2SessionGrants：保存过期标记；如果没有这一行，过期事实不会进入 session context。
            context["grant_revoked"] = bool(grant_revoked)  # 新增代码+Phase2SessionGrants：保存撤销标记；如果没有这一行，撤销事实不会进入 session context。
            if selected_display is not None:  # 新增代码+Phase59SessionContextAppState: 仅在调用方提供显示器时更新；如果没有这行代码，空参数会清掉已有显示器。
                context["selected_display"] = dict(selected_display)  # 新增代码+Phase59SessionContextAppState: 保存显示器选择副本；如果没有这行代码，多屏上下文无法持久化。
            if last_screenshot_dims is not None:  # 新增代码+Phase59SessionContextAppState: 仅在调用方提供截图尺寸时更新；如果没有这行代码，空参数会清掉已有截图事实。
                context["last_screenshot_dims"] = dict(last_screenshot_dims)  # 新增代码+Phase59SessionContextAppState: 保存截图尺寸副本；如果没有这行代码，高层工具无法知道最近截图大小。
            if display_pinned is not None:  # 新增代码+Phase3DisplayPin：仅在调用方提供 pin 状态时更新；如果没有这一行，空参数会意外覆盖已有 pin。
                context["display_pinned"] = bool(display_pinned)  # 新增代码+Phase3DisplayPin：保存显示器固定布尔值；如果没有这一行，后续动作不知道坐标是否绑定到具体屏幕。
            if display_origin is not None:  # 新增代码+Phase3DisplayPin：仅在调用方提供原点时更新；如果没有这一行，空参数会误清多屏偏移。
                context["display_origin"] = dict(display_origin)  # 新增代码+Phase3DisplayPin：保存显示器原点副本；如果没有这一行，副屏逻辑和物理原点无法复用。
            if display_scale is not None:  # 新增代码+Phase3DisplayPin：仅在调用方提供缩放时更新；如果没有这一行，空参数会误清 DPI 比例。
                context["display_scale"] = dict(display_scale)  # 新增代码+Phase3DisplayPin：保存 DPI 缩放副本；如果没有这一行，高 DPI 换算无法跨步骤保持一致。
            if hidden_windows is not None:  # 新增代码+Phase4TurnCleanup：仅在调用方提供 hidden windows 时更新；如果没有这一行，空参数会误清恢复目标。
                context["hidden_windows"] = _phase59_list_of_dicts(hidden_windows)  # 新增代码+Phase4TurnCleanup：保存规范化隐藏窗口列表；如果没有这一行，cleanup 无法安全恢复宿主窗口。
            if host_windows_hidden is not None:  # 新增代码+Phase4TurnCleanup：仅在调用方提供 host hidden 状态时更新；如果没有这一行，空参数会覆盖已有隐藏事实。
                context["host_windows_hidden"] = bool(host_windows_hidden)  # 新增代码+Phase4TurnCleanup：保存宿主窗口隐藏布尔值；如果没有这一行，cleanup 状态会和 hidden_windows 脱节。
            context["cleanup_completed"] = False  # 新增代码+Phase59SessionContextAppState: 新绑定说明会话重新活跃；如果没有这行代码，cleanup 后再使用会仍显示已清理。
            return self._write_context(context)  # 新增代码+Phase59SessionContextAppState: 写入并返回 context；如果没有这行代码，bind 不会持久化。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore.bind_context 到此结束；如果没有这个边界说明，初学者不容易看出绑定范围。

    def update_app_state(self, session_id: Any = DEFAULT_SESSION_CONTEXT_ID, *, hidden_windows: list[dict[str, Any]] | None = None, last_action: dict[str, Any] | None = None, last_error: dict[str, Any] | None = None, selected_display: dict[str, Any] | None = None, last_screenshot_dims: dict[str, Any] | None = None, display_pinned: bool | None = None, display_origin: dict[str, Any] | None = None, display_scale: dict[str, Any] | None = None, host_windows_hidden: bool | None = None, cleanup_completed: bool | None = None, cleanup_reason: str | None = None) -> dict[str, Any]:  # 修改代码+Phase4TurnCleanup：函数段开始，更新 AppState 变化并支持 host cleanup 状态；如果没有这段函数，turn cleanup 无法把 unhide 后的归零事实落盘。
        with FileLock(self.mutex_path, timeout_seconds=self.lock_timeout_seconds):  # 新增代码+Phase59SessionContextAppState: 用互斥锁保护 AppState 写入；如果没有这行代码，并发更新可能丢事件。
            context = self._read_context(session_id)  # 新增代码+Phase59SessionContextAppState: 读取已有 context；如果没有这行代码，更新会覆盖授权状态。
            if hidden_windows is not None:  # 新增代码+Phase59SessionContextAppState: 仅在调用方提供 hidden_windows 时更新；如果没有这行代码，空参数会误清状态。
                context["hidden_windows"] = _phase59_list_of_dicts(hidden_windows)  # 新增代码+Phase59SessionContextAppState: 保存规范化隐藏窗口；如果没有这行代码，状态 UI 无法可靠显示 hidden 数量。
            if last_action is not None:  # 新增代码+Phase59SessionContextAppState: 仅在调用方提供 last_action 时更新；如果没有这行代码，空参数会清掉动作证据。
                context["last_action"] = dict(last_action)  # 新增代码+Phase59SessionContextAppState: 保存最近动作副本；如果没有这行代码，status 和 verifier 读不到最后动作。
            if last_error is not None:  # 新增代码+Phase59SessionContextAppState: 仅在调用方提供 last_error 时更新；如果没有这行代码，空参数会清掉错误证据。
                context["last_error"] = dict(last_error)  # 新增代码+Phase59SessionContextAppState: 保存最近错误副本；如果没有这行代码，失败原因无法跨模块读取。
            if selected_display is not None:  # 新增代码+Phase59SessionContextAppState: 允许 AppState 同步显示器变化；如果没有这行代码，显示器切换无法进入状态。
                context["selected_display"] = dict(selected_display)  # 新增代码+Phase59SessionContextAppState: 保存显示器副本；如果没有这行代码，外部对象可能污染状态。
            if last_screenshot_dims is not None:  # 新增代码+Phase59SessionContextAppState: 允许 AppState 同步截图尺寸；如果没有这行代码，截图变化无法进入状态。
                context["last_screenshot_dims"] = dict(last_screenshot_dims)  # 新增代码+Phase59SessionContextAppState: 保存截图尺寸副本；如果没有这行代码，工具无法复用最近尺寸。
            if display_pinned is not None:  # 新增代码+Phase3DisplayPin：允许 AppState 同步 display pin 状态；如果没有这一行，stale display 清理无法落盘。
                context["display_pinned"] = bool(display_pinned)  # 新增代码+Phase3DisplayPin：保存 display pin 布尔值；如果没有这一行，后续仍可能误用旧坐标。
            if display_origin is not None:  # 新增代码+Phase3DisplayPin：允许 AppState 同步显示器原点；如果没有这一行，副屏偏移不能被清理或更新。
                context["display_origin"] = dict(display_origin)  # 新增代码+Phase3DisplayPin：保存显示器原点副本；如果没有这一行，坐标事实会被外部对象污染。
            if display_scale is not None:  # 新增代码+Phase3DisplayPin：允许 AppState 同步显示器缩放；如果没有这一行，DPI 比例不能被清理或更新。
                context["display_scale"] = dict(display_scale)  # 新增代码+Phase3DisplayPin：保存显示器缩放副本；如果没有这一行，高 DPI 状态可能残留旧值。
            if host_windows_hidden is not None:  # 新增代码+Phase4TurnCleanup：允许 AppState 同步 host hidden 状态；如果没有这一行，cleanup 无法关闭隐藏标记。
                context["host_windows_hidden"] = bool(host_windows_hidden)  # 新增代码+Phase4TurnCleanup：保存 host hidden 布尔值；如果没有这一行，真实终端状态可能继续显示宿主隐藏。
            if cleanup_completed is not None:  # 新增代码+Phase4TurnCleanup：允许 AppState 同步 cleanup 完成状态；如果没有这一行，run_turn_cleanup 只能返回成功不能持久化成功。
                context["cleanup_completed"] = bool(cleanup_completed)  # 新增代码+Phase4TurnCleanup：保存 cleanup 完成布尔值；如果没有这一行，后续幂等判断无法知道上一轮已清理。
            if cleanup_reason is not None:  # 新增代码+Phase4TurnCleanup：允许 AppState 同步 cleanup 原因；如果没有这一行，审计无法知道为何触发清理。
                context["cleanup_reason"] = str(cleanup_reason or "")  # 新增代码+Phase4TurnCleanup：保存 cleanup 原因文本；如果没有这一行，异常/abort/success 的清理来源会混在一起。
            return self._write_context(context)  # 新增代码+Phase59SessionContextAppState: 写入并返回更新后 context；如果没有这行代码，AppState 不会持久化。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore.update_app_state 到此结束；如果没有这个边界说明，初学者不容易看出 AppState 更新范围。

    def cleanup_session(self, session_id: Any = DEFAULT_SESSION_CONTEXT_ID, reason: str = "session cleanup") -> dict[str, Any]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，清理某个 session 的 context；如果没有这段函数，旧授权和 hidden 状态可能残留。
        with FileLock(self.mutex_path, timeout_seconds=self.lock_timeout_seconds):  # 新增代码+Phase59SessionContextAppState: 用互斥锁保护 cleanup；如果没有这行代码，cleanup 和 bind 可能交错污染。
            context = self._read_context(session_id)  # 新增代码+Phase59SessionContextAppState: 读取当前 context；如果没有这行代码，cleanup 不知道要清理谁。
            context["allowed_apps"] = []  # 新增代码+Phase59SessionContextAppState: 清空本会话 allowlist；如果没有这行代码，cleanup 后授权仍可能残留。
            context["denied_apps"] = []  # 新增代码+Phase2SessionGrants：清空本会话拒绝列表；如果没有这一行，下一轮可能继承旧拒绝导致误拦。
            context["grant_flags"] = {}  # 新增代码+Phase59SessionContextAppState: 清空 grant flags；如果没有这行代码，危险权限状态可能残留。
            context["request_access_session_id"] = _phase59_safe_session_id(session_id)  # 新增代码+Phase2SessionGrants：重置 request_access 会话 id；如果没有这一行，旧申请 id 可能继续出现在审计里。
            context["grant_expires_at_epoch"] = 0.0  # 新增代码+Phase2SessionGrants：清空授权过期时间；如果没有这一行，下轮状态可能显示旧 TTL。
            context["grant_expired"] = False  # 新增代码+Phase2SessionGrants：清空过期标记；如果没有这一行，下轮可能误显示授权已过期。
            context["grant_revoked"] = False  # 新增代码+Phase2SessionGrants：清空撤销标记；如果没有这一行，下轮可能误显示授权已撤销。
            context["selected_display"] = {}  # 新增代码+Phase3DisplayPin：清空固定显示器；如果没有这一行，cleanup 后旧屏幕 id 可能继续影响下一轮。
            context["last_screenshot_dims"] = {}  # 新增代码+Phase3DisplayPin：清空最近截图尺寸；如果没有这一行，cleanup 后旧截图比例可能继续被使用。
            context["display_pinned"] = False  # 新增代码+Phase3DisplayPin：清空 display pin 状态；如果没有这一行，cleanup 后坐标仍会被当作已固定。
            context["display_origin"] = {}  # 新增代码+Phase3DisplayPin：清空显示器原点；如果没有这一行，旧副屏偏移会残留。
            context["display_scale"] = {"x": 1.0, "y": 1.0}  # 新增代码+Phase3DisplayPin：重置显示器缩放；如果没有这一行，旧 DPI 比例会污染下一轮。
            context["hidden_windows"] = []  # 新增代码+Phase59SessionContextAppState: 清空隐藏窗口状态；如果没有这行代码，旧隐藏窗口会误导下轮。
            context["host_windows_hidden"] = False  # 新增代码+Phase4TurnCleanup：清空 host hidden 状态；如果没有这一行，cleanup 后状态仍会显示宿主隐藏。
            context["last_action"] = {}  # 新增代码+Phase59SessionContextAppState: 清空最近动作；如果没有这行代码，状态 UI 可能显示过期动作。
            context["last_error"] = {}  # 新增代码+Phase59SessionContextAppState: 清空最近错误；如果没有这行代码，旧错误会误导排查。
            context["cleanup_completed"] = True  # 新增代码+Phase59SessionContextAppState: 标记 cleanup 已完成；如果没有这行代码，verifier 无法确认清理状态。
            context["cleanup_reason"] = str(reason or "")  # 新增代码+Phase59SessionContextAppState: 保存清理原因；如果没有这行代码，审计无法知道为什么清理。
            context["cleaned_at"] = _phase59_timestamp()  # 新增代码+Phase59SessionContextAppState: 保存清理时间；如果没有这行代码，多轮清理无法排序。
            saved = self._write_context(context)  # 新增代码+Phase59SessionContextAppState: 写入清理后的 context；如果没有这行代码，cleanup 不会落盘。
            return {"cleanup_completed": True, "session_id": saved["session_id"], "context": saved, "reason": str(reason or ""), "marker": PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER, "actions_expanded": PHASE59_ACTIONS_EXPANDED}  # 新增代码+Phase59SessionContextAppState: 返回 cleanup 摘要；如果没有这行代码，调用方无法显示清理结果。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore.cleanup_session 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。

    def status(self, session_id: Any = DEFAULT_SESSION_CONTEXT_ID) -> dict[str, Any]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，返回 store 和当前 session 状态；如果没有这段函数，状态 UI 不能读取统一事实源。
        context = self.snapshot(session_id)  # 新增代码+Phase59SessionContextAppState: 读取当前 session；如果没有这行代码，status 缺少核心上下文。
        state_files = sorted(self.base_dir.glob("*.json"))  # 新增代码+Phase59SessionContextAppState: 枚举状态文件数量；如果没有这行代码，状态无法显示 session_count。
        return {"enabled": True, "marker": PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER, "model": PHASE59_SESSION_CONTEXT_MODEL, "state_dir": str(self.base_dir), "session_count": len(state_files), "current_session": context, "actions_expanded": PHASE59_ACTIONS_EXPANDED}  # 新增代码+Phase59SessionContextAppState: 返回机器可读状态；如果没有这行代码，/computer status 和 HTTP bridge 无法共享事实。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def terminal_status_lines(self, session_id: Any = DEFAULT_SESSION_CONTEXT_ID) -> list[str]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，生成终端可读 session context 面板；如果没有这段函数，小白用户只能读 JSON。
        status = self.status(session_id)  # 新增代码+Phase59SessionContextAppState: 读取机器状态；如果没有这行代码，终端文本没有事实来源。
        context = dict(status.get("current_session", {}))  # 新增代码+Phase59SessionContextAppState: 提取当前 context；如果没有这行代码，后续字段读取会重复。
        dims = dict(context.get("last_screenshot_dims", {}) or {})  # 新增代码+Phase59SessionContextAppState: 提取截图尺寸；如果没有这行代码，状态行无法显示 width/height。
        display = dict(context.get("selected_display", {}) or {})  # 新增代码+Phase59SessionContextAppState: 提取显示器选择；如果没有这行代码，状态行无法显示 display_id。
        return ["Computer Session Context", f"- marker={PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER}", f"- context_model={PHASE59_SESSION_CONTEXT_MODEL}", f"- session_id={context.get('session_id', '')}", f"- allowed_app_count={len(context.get('allowed_apps', []))}", f"- grant_flag_count={len(context.get('grant_flags', {}))}", f"- selected_display={display.get('display_id', '')}", f"- display_pinned={_phase59_bool_token(context.get('display_pinned'))}", f"- last_screenshot_dims={dims.get('width', '')}x{dims.get('height', '')}", f"- hidden_window_count={len(context.get('hidden_windows', []))}", f"- host_windows_hidden={_phase59_bool_token(context.get('host_windows_hidden'))}", f"- cleanup_completed={_phase59_bool_token(context.get('cleanup_completed'))}", f"- last_action={context.get('last_action', {}).get('action', '') if isinstance(context.get('last_action', {}), dict) else ''}", f"- last_error={context.get('last_error', {}).get('code', '') if isinstance(context.get('last_error', {}), dict) else ''}", f"- session_count={status.get('session_count', 0)}", f"- state_dir={status.get('state_dir', '')}", f"- actions_expanded={_phase59_bool_token(PHASE59_ACTIONS_EXPANDED)}"]  # 修改代码+Phase4TurnCleanup：返回完整终端面板行并暴露 host_windows_hidden；如果没有这行代码，真实终端看不出宿主窗口是否还被隐藏。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore.terminal_status_lines 到此结束；如果没有这个边界说明，初学者不容易看出终端输出范围。
# 新增代码+Phase59SessionContextAppState: 类段结束，ComputerUseSessionContextStore 到此结束；如果没有这个边界说明，初学者不容易看出 store 范围。


def run_phase59_session_context_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，运行 Phase59 合同自检；如果没有这段函数，CLI 和真实终端没有统一验收入口。
    if base_dir is None:  # 新增代码+Phase59SessionContextAppState: 判断是否需要使用真实默认目录；如果没有这行代码，CLI main 无法落盘到默认 memory。
        store = ComputerUseSessionContextStore()  # 新增代码+Phase59SessionContextAppState: 使用默认 memory/computer_use/session_state；如果没有这行代码，生产入口不满足持久化目标。
        cleanup_temp: tempfile.TemporaryDirectory[str] | None = None  # 新增代码+Phase59SessionContextAppState: 标记没有临时目录需要清理；如果没有这行代码，finally 可能引用未定义变量。
    else:  # 新增代码+Phase59SessionContextAppState: 测试传入目录时进入隔离路径；如果没有这行代码，单元测试会污染真实状态。
        cleanup_temp = None  # 新增代码+Phase59SessionContextAppState: 外部目录由调用方负责；如果没有这行代码，函数可能误删测试目录。
        store = ComputerUseSessionContextStore(base_dir=Path(base_dir))  # 新增代码+Phase59SessionContextAppState: 使用调用方指定目录；如果没有这行代码，测试无法隔离状态。
    try:  # 新增代码+Phase59SessionContextAppState: 包住合同流程便于未来清理；如果没有这行代码，临时资源扩展时缺少保护。
        store.bind_context("phase59-a", allowed_apps=["notepad.exe"], grant_flags={"desktopAction": True, "observe": True}, selected_display={"display_id": "DISPLAY1"}, last_screenshot_dims={"width": 1280, "height": 720})  # 新增代码+Phase59SessionContextAppState: 写入 A 会话核心事实；如果没有这行代码，context_persisted 没有输入。
        store.update_app_state("phase59-a", hidden_windows=[{"window_id": "hwnd:5901"}], last_action={"action": "type_text", "ok": True}, last_error={"code": "phase59-before-cleanup"})  # 新增代码+Phase59SessionContextAppState: 写入 A 会话 AppState；如果没有这行代码，hidden/last_action/last_error 无法验收。
        store.bind_context("phase59-b", allowed_apps=["calc.exe"], grant_flags={"observe": True})  # 新增代码+Phase59SessionContextAppState: 写入 B 会话用于隔离验证；如果没有这行代码，multi_session_isolated 没有反例。
        reloaded = ComputerUseSessionContextStore(base_dir=store.base_dir).snapshot("phase59-a")  # 新增代码+Phase59SessionContextAppState: 用新 store 重新读取 A；如果没有这行代码，无法证明落盘持久化。
        cleanup = store.cleanup_session("phase59-a", reason="phase59-contract-cleanup")  # 新增代码+Phase59SessionContextAppState: 清理 A 会话；如果没有这行代码，cleanup_state 无法验证。
        session_a = store.snapshot("phase59-a")  # 新增代码+Phase59SessionContextAppState: 读取清理后的 A；如果没有这行代码，无法检查归零。
        session_b = store.snapshot("phase59-b")  # 新增代码+Phase59SessionContextAppState: 读取未清理的 B；如果没有这行代码，无法检查隔离。
        status_text = "\n".join(store.terminal_status_lines("phase59-a"))  # 新增代码+Phase59SessionContextAppState: 渲染终端状态；如果没有这行代码，status_readable 无法验证。
        context_persisted = bool("notepad.exe" in reloaded.get("allowed_apps", []) and reloaded.get("grant_flags", {}).get("desktopAction") and reloaded.get("last_screenshot_dims", {}).get("width") == 1280)  # 新增代码+Phase59SessionContextAppState: 汇总持久化判断；如果没有这行代码，报告无法表达核心结果。
        multi_session_isolated = bool("calc.exe" in session_b.get("allowed_apps", []) and session_b.get("grant_flags", {}).get("observe") and session_b.get("cleanup_completed") is False)  # 新增代码+Phase59SessionContextAppState: 汇总多会话隔离判断；如果没有这行代码，报告无法证明并发边界。
        cleanup_state = bool(cleanup.get("cleanup_completed") and session_a.get("allowed_apps") == [] and session_a.get("hidden_windows") == [] and session_a.get("last_action") == {} and session_a.get("last_error") == {})  # 新增代码+Phase59SessionContextAppState: 汇总 cleanup 归零判断；如果没有这行代码，报告无法证明状态清理。
        status_readable = bool("Computer Session Context" in status_text and PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER in status_text and "cleanup_completed=true" in status_text)  # 新增代码+Phase59SessionContextAppState: 汇总终端可读判断；如果没有这行代码，状态 UI 可能没有接入。
        passed = bool(context_persisted and multi_session_isolated and cleanup_state and status_readable and not PHASE59_ACTIONS_EXPANDED)  # 新增代码+Phase59SessionContextAppState: 汇总合同通过条件；如果没有这行代码，main 无法用退出码表达失败。
        return {"marker": PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER, "ok_token": PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_OK_TOKEN, "context_persisted": context_persisted, "multi_session_isolated": multi_session_isolated, "cleanup_state": cleanup_state, "status_readable": status_readable, "actions_expanded": PHASE59_ACTIONS_EXPANDED, "passed": passed, "state_dir": str(store.base_dir), "session_a": session_a, "session_b": session_b}  # 新增代码+Phase59SessionContextAppState: 返回完整合同报告；如果没有这行代码，测试和真实终端拿不到统一事实。
    finally:  # 新增代码+Phase59SessionContextAppState: 预留清理路径；如果没有这行代码，未来临时目录扩展会容易泄漏。
        if cleanup_temp is not None:  # 新增代码+Phase59SessionContextAppState: 检查是否存在内部临时目录；如果没有这行代码，None 会被错误清理。
            cleanup_temp.cleanup()  # 新增代码+Phase59SessionContextAppState: 清理内部临时目录；如果没有这行代码，临时状态会残留。
# 新增代码+Phase59SessionContextAppState: 函数段结束，run_phase59_session_context_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase59_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase59SessionContextAppState: 函数段开始，把报告转成稳定 CLI token 行；如果没有这段函数，真实终端场景要解析复杂 JSON。
    return f"{PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER} {PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_OK_TOKEN} context_persisted={_phase59_bool_token(report.get('context_persisted'))} multi_session_isolated={_phase59_bool_token(report.get('multi_session_isolated'))} cleanup_state={_phase59_bool_token(report.get('cleanup_state'))} status_readable={_phase59_bool_token(report.get('status_readable'))} actions_expanded={_phase59_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase59SessionContextAppState: 返回固定顺序 token；如果没有这行代码，验收输出容易漂移。
# 新增代码+Phase59SessionContextAppState: 函数段结束，phase59_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase59SessionContextAppState: 函数段开始，提供命令行入口；如果没有这段函数，真实终端无法运行 Phase59 自检。
    _ = argv  # 新增代码+Phase59SessionContextAppState: 保留 argv 供未来扩展；如果没有这行代码，静态检查可能提示参数未使用。
    report = run_phase59_session_context_contract()  # 新增代码+Phase59SessionContextAppState: 使用默认持久化目录运行合同；如果没有这行代码，CLI 不会证明真实 memory/session_state 路径。
    print(phase59_cli_line(report))  # 新增代码+Phase59SessionContextAppState: 打印稳定 token 行；如果没有这行代码，debug log 无法匹配 Phase59 成功。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase59SessionContextAppState: 打印结构化脱敏报告；如果没有这行代码，失败时不易复盘。
    print(PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER)  # 新增代码+Phase59SessionContextAppState: 单独打印 ready marker；如果没有这行代码，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase59SessionContextAppState: 根据合同结果返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase59SessionContextAppState: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["DEFAULT_SESSION_CONTEXT_ID", "DEFAULT_SESSION_CONTEXT_ROOT", "PHASE59_ACTIONS_EXPANDED", "PHASE59_SESSION_CONTEXT_MODEL", "PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER", "PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_OK_TOKEN", "ComputerUseSessionContext", "ComputerUseSessionContextStore", "deny_action_without_request_access", "grant_scope_matches_target", "main", "phase59_cli_line", "run_phase59_session_context_contract"]  # 修改代码+Phase2SessionGrants：公开 request_access 授权匹配和拒绝函数；如果没有这一行，Phase 2 测试和执行层无法复用动作前门禁。


if __name__ == "__main__":  # 新增代码+Phase59SessionContextAppState: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase59SessionContextAppState: 用 main 返回码退出；如果没有这行代码，命令行状态不明确。
