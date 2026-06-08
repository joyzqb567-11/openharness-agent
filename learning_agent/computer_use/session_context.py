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
        return {"schema_version": 1, "model": PHASE59_SESSION_CONTEXT_MODEL, "marker": PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER, "session_id": safe_session_id, "allowed_apps": [], "grant_flags": {}, "selected_display": {}, "last_screenshot_dims": {}, "hidden_windows": [], "last_action": {}, "last_error": {}, "cleanup_completed": False, "cleanup_reason": "", "created_at": now, "updated_at": now, "state_path": str(self._state_path(safe_session_id)), "actions_expanded": PHASE59_ACTIONS_EXPANDED}  # 新增代码+Phase59SessionContextAppState: 返回完整默认字段；如果没有这行代码，状态 UI 会遇到缺字段。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore._default_context 到此结束；如果没有这个边界说明，初学者不容易看出默认字段范围。

    def _normalize_context(self, session_id: Any, payload: Any) -> dict[str, Any]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，修复旧/坏 context 为标准结构；如果没有这段函数，损坏状态会拖垮 status。
        context = self._default_context(session_id)  # 新增代码+Phase59SessionContextAppState: 先创建完整默认值；如果没有这行代码，缺字段无法补齐。
        if isinstance(payload, dict):  # 新增代码+Phase59SessionContextAppState: 只有 dict 状态才合并；如果没有这行代码，坏类型会污染 context。
            context.update(dict(payload))  # 新增代码+Phase59SessionContextAppState: 合并已有字段；如果没有这行代码，持久化数据无法恢复。
        context["session_id"] = _phase59_safe_session_id(context.get("session_id", session_id))  # 新增代码+Phase59SessionContextAppState: 重新清理 session_id；如果没有这行代码，旧坏 id 会残留。
        context["allowed_apps"] = _phase59_unique_texts(context.get("allowed_apps", []))  # 新增代码+Phase59SessionContextAppState: 规范化 allowed_apps；如果没有这行代码，重复 app 会污染状态。
        context["grant_flags"] = {str(key): bool(value) for key, value in dict(context.get("grant_flags", {}) or {}).items()}  # 新增代码+Phase59SessionContextAppState: 规范化 grant_flags；如果没有这行代码，字符串 false 可能被误用。
        context["selected_display"] = dict(context.get("selected_display", {}) or {}) if isinstance(context.get("selected_display", {}), dict) else {}  # 新增代码+Phase59SessionContextAppState: 规范化显示器选择；如果没有这行代码，坏显示器字段会让 status 崩溃。
        context["last_screenshot_dims"] = dict(context.get("last_screenshot_dims", {}) or {}) if isinstance(context.get("last_screenshot_dims", {}), dict) else {}  # 新增代码+Phase59SessionContextAppState: 规范化截图尺寸；如果没有这行代码，截图状态无法安全读取。
        context["hidden_windows"] = _phase59_list_of_dicts(context.get("hidden_windows", []))  # 新增代码+Phase59SessionContextAppState: 规范化隐藏窗口列表；如果没有这行代码，坏列表会污染状态 UI。
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

    def bind_context(self, session_id: Any = DEFAULT_SESSION_CONTEXT_ID, *, allowed_apps: Any = None, grant_flags: dict[str, Any] | None = None, selected_display: dict[str, Any] | None = None, last_screenshot_dims: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，绑定当前工具调用需要的 session context；如果没有这段函数，权限和显示器状态仍会散落。
        with FileLock(self.mutex_path, timeout_seconds=self.lock_timeout_seconds):  # 新增代码+Phase59SessionContextAppState: 用互斥锁保护读改写；如果没有这行代码，并发 bind 会互相覆盖。
            context = self._read_context(session_id)  # 新增代码+Phase59SessionContextAppState: 读取已有 context；如果没有这行代码，bind 会覆盖历史状态。
            context["allowed_apps"] = _phase59_unique_texts([*context.get("allowed_apps", []), *list(allowed_apps or [])])  # 新增代码+Phase59SessionContextAppState: 合并 allowed_apps；如果没有这行代码，新授权不会进入统一事实源。
            context["grant_flags"].update({str(key): bool(value) for key, value in dict(grant_flags or {}).items()})  # 新增代码+Phase59SessionContextAppState: 合并 grant_flags；如果没有这行代码，权限选择不会进入统一事实源。
            if selected_display is not None:  # 新增代码+Phase59SessionContextAppState: 仅在调用方提供显示器时更新；如果没有这行代码，空参数会清掉已有显示器。
                context["selected_display"] = dict(selected_display)  # 新增代码+Phase59SessionContextAppState: 保存显示器选择副本；如果没有这行代码，多屏上下文无法持久化。
            if last_screenshot_dims is not None:  # 新增代码+Phase59SessionContextAppState: 仅在调用方提供截图尺寸时更新；如果没有这行代码，空参数会清掉已有截图事实。
                context["last_screenshot_dims"] = dict(last_screenshot_dims)  # 新增代码+Phase59SessionContextAppState: 保存截图尺寸副本；如果没有这行代码，高层工具无法知道最近截图大小。
            context["cleanup_completed"] = False  # 新增代码+Phase59SessionContextAppState: 新绑定说明会话重新活跃；如果没有这行代码，cleanup 后再使用会仍显示已清理。
            return self._write_context(context)  # 新增代码+Phase59SessionContextAppState: 写入并返回 context；如果没有这行代码，bind 不会持久化。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore.bind_context 到此结束；如果没有这个边界说明，初学者不容易看出绑定范围。

    def update_app_state(self, session_id: Any = DEFAULT_SESSION_CONTEXT_ID, *, hidden_windows: list[dict[str, Any]] | None = None, last_action: dict[str, Any] | None = None, last_error: dict[str, Any] | None = None, selected_display: dict[str, Any] | None = None, last_screenshot_dims: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，更新 AppState 变化；如果没有这段函数，hidden/last_action/last_error 不能进入统一事实源。
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
            return self._write_context(context)  # 新增代码+Phase59SessionContextAppState: 写入并返回更新后 context；如果没有这行代码，AppState 不会持久化。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，ComputerUseSessionContextStore.update_app_state 到此结束；如果没有这个边界说明，初学者不容易看出 AppState 更新范围。

    def cleanup_session(self, session_id: Any = DEFAULT_SESSION_CONTEXT_ID, reason: str = "session cleanup") -> dict[str, Any]:  # 新增代码+Phase59SessionContextAppState: 函数段开始，清理某个 session 的 context；如果没有这段函数，旧授权和 hidden 状态可能残留。
        with FileLock(self.mutex_path, timeout_seconds=self.lock_timeout_seconds):  # 新增代码+Phase59SessionContextAppState: 用互斥锁保护 cleanup；如果没有这行代码，cleanup 和 bind 可能交错污染。
            context = self._read_context(session_id)  # 新增代码+Phase59SessionContextAppState: 读取当前 context；如果没有这行代码，cleanup 不知道要清理谁。
            context["allowed_apps"] = []  # 新增代码+Phase59SessionContextAppState: 清空本会话 allowlist；如果没有这行代码，cleanup 后授权仍可能残留。
            context["grant_flags"] = {}  # 新增代码+Phase59SessionContextAppState: 清空 grant flags；如果没有这行代码，危险权限状态可能残留。
            context["hidden_windows"] = []  # 新增代码+Phase59SessionContextAppState: 清空隐藏窗口状态；如果没有这行代码，旧隐藏窗口会误导下轮。
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
        return ["Computer Session Context", f"- marker={PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER}", f"- context_model={PHASE59_SESSION_CONTEXT_MODEL}", f"- session_id={context.get('session_id', '')}", f"- allowed_app_count={len(context.get('allowed_apps', []))}", f"- grant_flag_count={len(context.get('grant_flags', {}))}", f"- selected_display={display.get('display_id', '')}", f"- last_screenshot_dims={dims.get('width', '')}x{dims.get('height', '')}", f"- hidden_window_count={len(context.get('hidden_windows', []))}", f"- cleanup_completed={_phase59_bool_token(context.get('cleanup_completed'))}", f"- last_action={context.get('last_action', {}).get('action', '') if isinstance(context.get('last_action', {}), dict) else ''}", f"- last_error={context.get('last_error', {}).get('code', '') if isinstance(context.get('last_error', {}), dict) else ''}", f"- session_count={status.get('session_count', 0)}", f"- state_dir={status.get('state_dir', '')}", f"- actions_expanded={_phase59_bool_token(PHASE59_ACTIONS_EXPANDED)}"]  # 新增代码+Phase59SessionContextAppState: 返回完整终端面板行；如果没有这行代码，状态 UI 无法展示统一事实源。
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


__all__ = ["DEFAULT_SESSION_CONTEXT_ID", "DEFAULT_SESSION_CONTEXT_ROOT", "PHASE59_ACTIONS_EXPANDED", "PHASE59_SESSION_CONTEXT_MODEL", "PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER", "PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_OK_TOKEN", "ComputerUseSessionContext", "ComputerUseSessionContextStore", "main", "phase59_cli_line", "run_phase59_session_context_contract"]  # 新增代码+Phase59SessionContextAppState: 限定公开导出名称；如果没有这行代码，包导入容易暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase59SessionContextAppState: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase59SessionContextAppState: 用 main 返回码退出；如果没有这行代码，命令行状态不明确。
