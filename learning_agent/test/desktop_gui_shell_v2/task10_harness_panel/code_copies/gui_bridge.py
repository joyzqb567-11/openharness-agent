"""Desktop GUI bridge for the OpenHarness local desktop shell."""  # 修改代码+DesktopGUIBridge：说明本模块只服务桌面 GUI bridge；如果没有这行，维护者容易把它和通用 HTTP command bridge 混在一起。

from __future__ import annotations  # 修改代码+DesktopGUIBridge：启用延迟类型解析；如果没有这行，类之间互相引用时更容易受定义顺序影响。

import http.server  # 修改代码+DesktopGUIBridge：使用标准库 HTTP server 提供本地 bridge；如果没有这行，Electron 没有后端入口。
import json  # 修改代码+DesktopGUIBridge：负责请求/响应 JSON 编解码；如果没有这行，GUI 无法传输结构化中文 prompt。
import secrets  # 修改代码+DesktopGUIBridge：生成随机本地 token；如果没有这行，默认启动缺少认证保护。
import threading  # 新增代码+DesktopGUILifecycle：支持后台 turn worker 和状态锁；如果没有这行，GUI 请求会阻塞或并发写坏状态。
import time  # 新增代码+DesktopGUILifecycle：模拟可取消的后台执行节奏；如果没有这行，cancel 测试会和完成状态抢时序。
import urllib.parse  # 修改代码+DesktopGUIBridge：解析 URL path 和 query；如果没有这行，events 和动态 POST 路由无法读参数。
import uuid  # 新增代码+DesktopGUILifecycle：生成 turn/run/message id；如果没有这行，重试和恢复难以稳定区分对象。
from dataclasses import asdict, dataclass, field  # 新增代码+DesktopGUILifecycle：定义可落盘的 turn/session 数据结构；如果没有这行，状态对象会散成难维护的 dict。
from pathlib import Path  # 修改代码+DesktopGUIBridge：规范化工作区和 memory 路径；如果没有这行，字符串路径容易在 Windows 下出错。
from typing import Any, Callable  # 修改代码+DesktopGUIBridge：标注 JSON 和可插拔 runner 类型；如果没有这行，接口边界不清楚。

from learning_agent.app.gui_agent_adapter import DefaultHarnessGuiAgentAdapter, FakeStreamingGuiAgentAdapter, GuiAgentAdapter, GuiAgentRunRequest, GuiAgentRunResult  # 新增代码+GuiAgentAdapter：导入 GUI adapter 边界和 fake/real shell；如果没有这一行，bridge 仍会停留在 V1 answer runner。
from learning_agent.app.gui_diagnostics import build_gui_diagnostics_payload, build_gui_health_payload  # ????+GuiDiagnostics??? V2 ????? payload helper??????????bridge ?????/?? UI ???????
from learning_agent.app.gui_permissions import normalize_permission_decision, normalize_permission_request_fields, permission_payload_from_request, redact_permission_text  # 新增代码+DesktopGUIPermissionsV2：导入权限 V2 规范化 helper；如果没有这行，bridge 会继续手写不完整权限字段和脱敏。
from learning_agent.app.gui_protocol import GUI_V2_SCHEMA_VERSION, GUI_V2_TOKEN_HEADER, make_error_response  # 新增代码+GuiV2Protocol：复用 V2 协议常量和错误 helper；如果没有这一行，bridge 会继续维护一套重复协议。
from learning_agent.app.gui_stream import format_sse_event, select_events_after  # 新增代码+GuiV2Stream：复用 V2 事件选择和 SSE 编码 helper；如果没有这一行，stream 路由会重复协议逻辑。
from learning_agent.runtime.status_events import StatusEventStore  # 修改代码+DesktopGUIBridge：复用统一状态事件流；如果没有这行，GUI 事件会和 CLI/SDK 事实源分裂。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 修改代码+DesktopGUIBridge：复用统一状态快照；如果没有这行，GUI 首屏会旁路读取状态。


GUI_SCHEMA_VERSION = GUI_V2_SCHEMA_VERSION  # 修改代码+GuiV2Protocol：让 bridge 暴露 V2 schema 版本；如果没有这行，前端会继续误判为 V1 能力。
GUI_TOKEN_HEADER = GUI_V2_TOKEN_HEADER  # 修改代码+GuiV2Protocol：让 bridge token header 来自 V2 协议模块；如果没有这行，安全字段会再次分裂。
GUI_ALLOWED_ORIGINS = {"", "null", "file://", "http://127.0.0.1:5177", "http://localhost:5177"}  # 修改代码+DesktopGUICors：限制可访问来源并允许 Vite 本地预览域名；如果没有这行，真实 Electron/Vite 前端会被浏览器跨源策略拦住。
GUI_CORS_ALLOWED_HEADERS = f"Content-Type, {GUI_TOKEN_HEADER}"  # 新增代码+DesktopGUICors：声明浏览器预检允许的请求头；如果没有这行，带 token 的 POST 会在真正发送前被浏览器拦截。
GUI_CORS_ALLOWED_METHODS = "GET, POST, OPTIONS"  # 新增代码+DesktopGUICors：声明浏览器预检允许的方法；如果没有这行，消息提交和轮询可能无法通过 CORS 预检。
GUI_RUNNING_STATES = {"queued", "running", "needs_permission", "cancelling"}  # 新增代码+DesktopGUILifecycle：集中定义非终态；如果没有这行，busy/cancel 判断会散落重复。
GUI_TERMINAL_STATES = {"completed", "failed", "cancelled"}  # 新增代码+DesktopGUILifecycle：集中定义终态；如果没有这行，retry/resume 判断不稳定。
GuiAnswerRunner = Callable[[str, str, str], str]  # 新增代码+DesktopGUILifecycle：定义后端回答 runner 插入点；如果没有这行，未来接真实 agent 时接口不清楚。


class GuiBridgeError(Exception):  # 新增代码+DesktopGUILifecycle：异常类段开始，承载结构化 HTTP 错误；如果没有这个类，业务错误只能靠字符串猜。
    def __init__(self, status: int, code: str, message: str) -> None:  # 新增代码+DesktopGUILifecycle：初始化结构化错误；如果没有这段，handler 无法统一返回 status/code/error。
        super().__init__(message)  # 新增代码+DesktopGUILifecycle：把 message 交给 Exception；如果没有这行，调试时异常文本为空。
        self.status = status  # 新增代码+DesktopGUILifecycle：保存 HTTP 状态码；如果没有这行，handler 无法区分 400/404/409。
        self.code = code  # 新增代码+DesktopGUILifecycle：保存机器可读错误码；如果没有这行，前端无法稳定分支处理错误。
        self.message = message  # 新增代码+DesktopGUILifecycle：保存人类可读错误；如果没有这行，前端无法展示明确提示。
    # 新增代码+DesktopGUILifecycle：异常类段结束，GuiBridgeError 到此结束；如果没有边界说明，初学者不易看出它只负责错误传递。


@dataclass  # 新增代码+DesktopGUILifecycle：自动生成消息数据结构方法；如果没有这行，消息落盘需要手写重复代码。
class GuiMessage:  # 新增代码+DesktopGUILifecycle：消息类段开始，保存 GUI 会话消息；如果没有这个类，resume 返回消息形状不稳定。
    id: str  # 新增代码+DesktopGUILifecycle：消息唯一 id；如果没有这行，前端列表 key 不稳定。
    role: str  # 新增代码+DesktopGUILifecycle：消息角色；如果没有这行，用户/助手/系统消息无法区分。
    text: str  # 新增代码+DesktopGUILifecycle：消息正文；如果没有这行，恢复会话没有可显示内容。
    turn_id: str = ""  # 新增代码+DesktopGUILifecycle：关联 turn id；如果没有这行，消息和事件无法对齐。
    status: str = ""  # 新增代码+DesktopGUILifecycle：消息对应状态；如果没有这行，助手占位无法显示 running/completed。
    # 新增代码+DesktopGUILifecycle：消息类段结束，GuiMessage 到此结束；如果没有边界说明，初学者不易看出消息字段范围。


@dataclass  # 新增代码+DesktopGUILifecycle：自动生成 turn 数据结构方法；如果没有这行，turn 落盘需要手写重复代码。
class GuiTurn:  # 新增代码+DesktopGUILifecycle：turn 类段开始，保存一次 GUI prompt 生命周期；如果没有这个类，cancel/retry/resume 无法共享状态。
    turn_id: str  # 新增代码+DesktopGUILifecycle：turn 唯一 id；如果没有这行，事件无法定位具体轮次。
    run_id: str  # 新增代码+DesktopGUILifecycle：run 唯一 id；如果没有这行，状态面板无法按 run 聚合。
    session_id: str  # 新增代码+DesktopGUILifecycle：所属 session；如果没有这行，窗口重启无法恢复对应会话。
    prompt: str  # 新增代码+DesktopGUILifecycle：原始 prompt；如果没有这行，retry 无法复用用户输入。
    status: str = "queued"  # 新增代码+DesktopGUILifecycle：当前生命周期状态；如果没有这行，UI 无法显示运行态。
    answer: str = ""  # 新增代码+DesktopGUILifecycle：最终回答；如果没有这行，resume 无法带回助手输出。
    retry_of: str = ""  # 新增代码+DesktopGUILifecycle：记录重试来源 turn；如果没有这行，前端无法解释 retry 关系。
    client_request_id: str = ""  # 新增代码+DesktopGUILifecycle：记录前端请求 id；如果没有这行，客户端去重和排查会更困难。
    error: str = ""  # 新增代码+DesktopGUILifecycle：记录失败原因；如果没有这行，失败 UI 只能显示泛化错误。
    # 新增代码+DesktopGUILifecycle：turn 类段结束，GuiTurn 到此结束；如果没有边界说明，初学者不易看出生命周期字段范围。


@dataclass  # 新增代码+DesktopGUILifecycle：自动生成 session 数据结构方法；如果没有这行，会话落盘需要手写重复代码。
class GuiSession:  # 新增代码+DesktopGUILifecycle：session 类段开始，保存桌面会话消息和游标；如果没有这个类，resume endpoint 没有稳定事实源。
    session_id: str  # 新增代码+DesktopGUILifecycle：会话 id；如果没有这行，多个会话无法区分。
    messages: list[GuiMessage] = field(default_factory=list)  # 新增代码+DesktopGUILifecycle：保存会话消息；如果没有这行，窗口重启后对话会丢失。
    last_turn_id: str = ""  # 新增代码+DesktopGUILifecycle：保存最近 turn；如果没有这行，恢复后无法定位最新状态。
    title: str = ""  # 新增代码+DesktopGUISessionSearch：保存用户可改名标题；如果没有这行，侧栏 rename 只能改前端假状态，重启后会丢失。
    archived: bool = False  # 新增代码+DesktopGUISessionSearch：保存会话是否归档；如果没有这行，archive 只能隐藏当前界面，后端列表仍会返回旧会话。
    pinned: bool = False  # 新增代码+DesktopGUISessionSearch：保存会话是否固定；如果没有这行，Codex 式侧栏无法稳定区分重点会话。
    updated_at: float = field(default_factory=time.time)  # 新增代码+DesktopGUISessionSearch：保存会话最近更新时间；如果没有这行，最近会话排序只能依赖字典插入顺序。
    # 新增代码+DesktopGUILifecycle：session 类段结束，GuiSession 到此结束；如果没有边界说明，初学者不易看出会话字段范围。


@dataclass  # 新增代码+DesktopGUIPermissions：自动生成权限请求数据结构方法；如果没有这行，权限请求落盘要手写重复代码。
class GuiPermissionRequest:  # 新增代码+DesktopGUIPermissions：权限请求类段开始，保存 GUI 可回答的后端权限请求；如果没有这个类，approve/deny 无法防重复和审计。
    request_id: str  # 新增代码+DesktopGUIPermissions：权限请求唯一 id；如果没有这行，前端无法定位要回答的请求。
    turn_id: str  # 新增代码+DesktopGUIPermissions：关联的 turn id；如果没有这行，权限状态无法同步到对应消息。
    run_id: str = ""  # 新增代码+DesktopGUIPermissions：关联的 run id；如果没有这行，状态时间线无法按 run 聚合权限事件。
    session_id: str = ""  # 新增代码+DesktopGUIPermissions：关联的 session id；如果没有这行，权限事件无法归属到会话。
    tool_name: str = ""  # 新增代码+DesktopGUIPermissionsV2：保存具体工具名；如果没有这行，权限弹窗只能显示应用名，无法解释是哪种工具在请求。
    app_name: str = ""  # 新增代码+DesktopGUIPermissions：显示应用或工具名；如果没有这行，权限弹窗无法告诉用户谁在请求权限。
    action_summary: str = ""  # 新增代码+DesktopGUIPermissionsV2：保存人类可读动作摘要；如果没有这行，前端需要重复推断权限请求的动作含义。
    reason: str = ""  # 新增代码+DesktopGUIPermissions：显示请求原因；如果没有这行，用户无法理解允许或拒绝的依据。
    risk_summary: str = ""  # 新增代码+DesktopGUIPermissions：显示风险摘要；如果没有这行，GUI 只会给出裸按钮而没有安全上下文。
    status: str = "pending"  # 新增代码+DesktopGUIPermissions：保存 pending/approved/denied 状态；如果没有这行，后端无法拒绝重复回答。
    decision: str = ""  # 新增代码+DesktopGUIPermissions：保存 approve/deny 决策；如果没有这行，审计事件无法复盘用户选择。
    decision_reason: str = ""  # 新增代码+DesktopGUIPermissions：保存用户或 GUI 给出的理由；如果没有这行，审计缺少为什么允许或拒绝。
    created_at: float = field(default_factory=time.time)  # 新增代码+DesktopGUIPermissions：记录请求创建时间；如果没有这行，超时和审计排序没有依据。
    answered_at: float = 0.0  # 新增代码+DesktopGUIPermissions：记录回答时间；如果没有这行，重复回答和延迟排查不清楚。
    # 新增代码+DesktopGUIPermissions：权限请求类段结束，GuiPermissionRequest 到此结束；如果没有边界说明，初学者不易看出权限字段范围。


def _new_id(prefix: str) -> str:  # 新增代码+DesktopGUILifecycle：函数段开始，生成短唯一 id；如果没有这段，turn/run/message id 生成会重复散落。
    return f"{prefix}_{uuid.uuid4().hex[:16]}"  # 新增代码+DesktopGUILifecycle：返回带前缀的随机 id；如果没有这行，前端很难从 id 看出对象类型。
# 新增代码+DesktopGUILifecycle：函数段结束，_new_id 到此结束；如果没有边界说明，初学者不易看出它只负责 id。


def _state_memory_dir(workspace: str | Path) -> Path:  # 新增代码+DesktopGUILifecycle：函数段开始，定位 GUI bridge 状态目录；如果没有这段，session 落盘路径会散落。
    return Path(workspace).expanduser().resolve() / "memory" / "gui_bridge"  # 新增代码+DesktopGUILifecycle：返回 memory/gui_bridge 目录；如果没有这行，resume 无法跨 server 重启。
# 新增代码+DesktopGUILifecycle：函数段结束，_state_memory_dir 到此结束；如果没有边界说明，初学者不易看出它只负责路径。


def _status_store(workspace: str | Path) -> StatusEventStore:  # 修改代码+DesktopGUIBridge：函数段开始，创建统一状态事件 store；如果没有这段，事件路径会重复硬编码。
    workspace_path = Path(workspace).expanduser().resolve()  # 修改代码+DesktopGUIBridge：规范化工作区路径；如果没有这行，相对路径会导致事件写错位置。
    return StatusEventStore(workspace_path / "memory" / "status")  # 修改代码+DesktopGUIBridge：返回统一 status store；如果没有这行，GUI watcher 没有事件事实源。
# 修改代码+DesktopGUIBridge：函数段结束，_status_store 到此结束；如果没有边界说明，初学者不易看出它只负责 status store。


def _latest_sequence(workspace: str | Path) -> int:  # 新增代码+DesktopGUILifecycle：函数段开始，读取当前事件最大序号；如果没有这段，响应无法给出 events_after_sequence。
    events = _status_store(workspace).list_events(limit=1)  # 新增代码+DesktopGUILifecycle：读取最后一条事件；如果没有这行，只能全量扫描或返回不准游标。
    return events[-1].sequence if events else 0  # 新增代码+DesktopGUILifecycle：返回最新序号或 0；如果没有这行，空事件流会报错。
# 新增代码+DesktopGUILifecycle：函数段结束，_latest_sequence 到此结束；如果没有边界说明，初学者不易看出它只负责事件游标。


def build_gui_bootstrap_payload(workspace: str | Path) -> dict[str, Any]:  # 修改代码+DesktopGUIBridge：函数段开始，生成 GUI 启动首屏数据；如果没有这段，桌面壳需要调多个端点拼状态。
    workspace_path = Path(workspace).expanduser().resolve()  # 修改代码+DesktopGUIBridge：规范化工作区路径；如果没有这行，前端显示的项目身份不稳定。
    try:  # 修改代码+DesktopGUIBootstrapDegrade：保护首屏状态快照读取；如果没有这行代码，Windows 锁文件权限异常会让 GUI bootstrap 直接 traceback。
        snapshot = build_status_snapshot(workspace_path)  # 修改代码+DesktopGUIBootstrapDegrade：读取统一状态快照；如果没有这行，GUI 会和 CLI/SDK 状态分裂。
        snapshot_degraded = False  # 新增代码+DesktopGUIBootstrapDegrade：记录快照正常读取；如果没有这行代码，前端无法区分正常快照和降级快照。
    except Exception:  # 修改代码+DesktopGUIBootstrapDegrade：捕获快照读取失败；如果没有这行代码，临时文件锁问题会让 Electron 首屏失败。
        snapshot = {"sessions": [], "resume": {}, "browser": {"provider_status": {"providers": {}, "error": "状态快照暂时不可读。"}}, "degraded": True}  # 新增代码+DesktopGUIBootstrapDegrade：提供不含本机路径的降级快照；如果没有这行代码，前端会空白或暴露磁盘路径。
        snapshot_degraded = True  # 新增代码+DesktopGUIBootstrapDegrade：标记快照降级；如果没有这行代码，诊断时看不出数据来自兜底路径。
    return {  # 修改代码+DesktopGUIBridge：返回稳定 JSON 对象；如果没有这行，前端无法渲染启动页。
        "ok": True,  # 修改代码+DesktopGUIBridge：标记请求成功；如果没有这行，前端要靠异常猜状态。
        "workspace": str(workspace_path),  # 修改代码+DesktopGUIBridge：返回当前项目路径；如果没有这行，侧栏无法显示项目身份。
        "app": {"name": "OpenHarness Desktop", "schema_version": GUI_SCHEMA_VERSION},  # 修改代码+DesktopGUIBridge：返回应用名和协议版本；如果没有这行，前端无法做兼容判断。
        "snapshot": snapshot,  # 修改代码+DesktopGUIBridge：返回统一状态快照；如果没有这行，首屏看不到任务、会话和浏览器状态。
        "snapshot_degraded": snapshot_degraded,  # 新增代码+DesktopGUIBootstrapDegrade：告诉前端首屏快照是否降级；如果没有这行代码，用户只能看到空状态却不知道原因。
        "feature_flags": {  # 修改代码+DesktopGUIBridge：返回后端能力开关；如果没有这段，前端无法按能力显示 UI。
            "chat_run": True,  # 修改代码+DesktopGUIBridge：声明可发起聊天运行；如果没有这行，输入框无法判断是否可用。
            "event_polling": True,  # 修改代码+DesktopGUIBridge：声明当前支持事件轮询；如果没有这行，前端无法启动 watcher。
            "browser_panel": True,  # 修改代码+DesktopGUIBridge：声明可显示浏览器状态；如果没有这行，浏览器面板会误隐藏。
            "computer_use_panel": True,  # 修改代码+DesktopGUIBridge：声明可显示 Computer Use 状态；如果没有这行，权限面板会误隐藏。
            "streaming": False,  # 修改代码+DesktopGUIBridge：声明 V1 尚未启用 SSE 流式输出；如果没有这行，前端可能误等流。
        },  # 修改代码+DesktopGUIBridge：feature_flags 对象结束；如果没有这行，Python 字典语法不完整。
    }  # 修改代码+DesktopGUIBridge：bootstrap payload 结束；如果没有这行，函数没有返回值。
# 修改代码+DesktopGUIBridge：函数段结束，build_gui_bootstrap_payload 到此结束；如果没有边界说明，初学者不易看出它只负责首屏。


def build_gui_events_payload(workspace: str | Path, since_sequence: int | None = None, limit: int = 50) -> dict[str, Any]:  # 修改代码+DesktopGUIBridge：函数段开始，生成 GUI 事件轮询 payload；如果没有这段，前端无法增量刷新工具和任务状态。
    safe_limit = max(1, min(200, int(limit)))  # 修改代码+DesktopGUIBridge：限制事件数量；如果没有这行，大量事件会拖慢 UI。
    events = [event.to_dict() for event in _status_store(workspace).list_events(since_sequence=since_sequence, limit=safe_limit)]  # 修改代码+DesktopGUIBridge：读取并序列化事件；如果没有这行，前端收不到状态时间线。
    return {"ok": True, "events": events, "since_sequence": since_sequence, "limit": safe_limit}  # 修改代码+DesktopGUIBridge：返回稳定事件 payload；如果没有这行，前端无法记录游标。
# 修改代码+DesktopGUIBridge：函数段结束，build_gui_events_payload 到此结束；如果没有边界说明，初学者不易看出它只负责事件轮询。

def build_gui_sessions_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUISessions：函数段开始，生成 GUI 会话侧栏 payload；如果没有这段，侧栏只能继续显示静态假会话。
    try:  # 修改代码+DesktopGUISessionDegrade：保护会话快照读取；如果没有这行代码，Windows 锁文件权限异常会让 sessions helper 直接 traceback。
        snapshot = build_status_snapshot(Path(workspace).expanduser().resolve())  # 修改代码+DesktopGUISessionDegrade：复用统一状态快照读取 sessions/resume；如果没有这行，GUI 会话列表会和 CLI/SDK 状态分裂。
    except Exception:  # 修改代码+DesktopGUISessionDegrade：捕获快照读取失败；如果没有这行代码，调用方无法获得稳定 sessions payload。
        return {"ok": True, "sessions": [], "resume": {"degraded": True, "error": "状态快照暂时不可读。"}}  # 新增代码+DesktopGUISessionDegrade：返回不含本机路径的降级会话 payload；如果没有这行代码，前端可能因为异常白屏。
    sessions = snapshot.get("sessions", [])  # 新增代码+DesktopGUISessions：从快照提取最近会话；如果没有这行，前端拿不到可恢复会话列表。
    resume = snapshot.get("resume", {})  # 新增代码+DesktopGUISessions：从快照提取恢复状态；如果没有这行，侧栏无法提示恢复风险或最近恢复状态。
    safe_sessions = sessions if isinstance(sessions, list) else []  # 新增代码+DesktopGUISessions：防御坏快照中的非数组 sessions；如果没有这行，异常数据会拖垮 GUI 渲染。
    safe_resume = resume if isinstance(resume, dict) else {}  # 新增代码+DesktopGUISessions：防御坏快照中的非对象 resume；如果没有这行，前端会收到不稳定类型。
    return {"ok": True, "sessions": safe_sessions, "resume": safe_resume}  # 新增代码+DesktopGUISessions：返回稳定会话 payload；如果没有这行，client.sessions() 没有合同可依赖。
# 新增代码+DesktopGUISessions：函数段结束，build_gui_sessions_payload 到此结束；如果没有边界说明，初学者不易看出它只负责会话侧栏数据。

def build_gui_browser_providers_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIBrowserPanel：函数段开始，生成 GUI 浏览器 provider payload；如果没有这段，桌面右栏无法显示浏览器轨道健康状态。
    try:  # 修改代码+DesktopGUIProviderDegrade：保护状态快照读取；如果没有这行代码，Windows 锁文件权限异常会让 browser providers endpoint 直接 traceback。
        snapshot = build_status_snapshot(Path(workspace).expanduser().resolve())  # 修改代码+DesktopGUIProviderDegrade：读取统一状态快照；如果没有这行，GUI 浏览器状态会和 CLI/SDK 状态分裂。
    except Exception:  # 修改代码+DesktopGUIProviderDegrade：捕获快照读取失败；如果没有这行代码，右侧浏览器面板会因为临时文件锁问题拖垮整个 bridge。
        safe_provider_status = {"providers": {}, "error": "浏览器状态快照暂时不可读。"}  # 新增代码+DesktopGUIProviderDegrade：返回不含本机路径的降级 provider 状态；如果没有这行代码，前端要么空白要么暴露路径细节。
        safe_browser = {"provider_status": safe_provider_status, "degraded": True}  # 新增代码+DesktopGUIProviderDegrade：保留 browser 父级结构并标记降级；如果没有这行代码，前端无法区分正常空状态和读取失败。
        return {"ok": True, "provider_status": safe_provider_status, "browser": safe_browser, "degraded": True}  # 新增代码+DesktopGUIProviderDegrade：返回稳定 JSON payload；如果没有这行代码，Electron 轮询会因为 HTTP handler 崩溃而断掉。
    browser = snapshot.get("browser", {})  # 新增代码+DesktopGUIBrowserPanel：从快照提取 browser 区块；如果没有这行，provider_status 没有父级上下文。
    safe_browser = browser if isinstance(browser, dict) else {}  # 新增代码+DesktopGUIBrowserPanel：防御坏快照中的非对象 browser；如果没有这行，异常状态会拖垮 GUI 渲染。
    provider_status = safe_browser.get("provider_status", {})  # 新增代码+DesktopGUIBrowserPanel：读取 provider_status 子区块；如果没有这行，面板拿不到 provider 健康详情。
    safe_provider_status = provider_status if isinstance(provider_status, dict) else {}  # 新增代码+DesktopGUIBrowserPanel：防御坏快照中的非对象 provider_status；如果没有这行，前端会收到不稳定类型。
    return {"ok": True, "provider_status": safe_provider_status, "browser": safe_browser}  # 新增代码+DesktopGUIBrowserPanel：返回稳定浏览器 payload；如果没有这行，client.browserProviders() 没有合同可依赖。
# 新增代码+DesktopGUIBrowserPanel：函数段结束，build_gui_browser_providers_payload 到此结束；如果没有边界说明，初学者不易看出它只负责浏览器状态侧栏数据。

def _gui_panel_record(value: Any) -> dict[str, Any]:  # 新增代码+DesktopRuntimePanels：函数段开始，把未知 panel 值收敛为普通对象；如果没有这段，坏快照会让 panel payload 崩溃。
    return value if isinstance(value, dict) else {}  # 新增代码+DesktopRuntimePanels：只接受 dict，否则返回空对象；如果没有这行，前端可能收到不稳定类型。
# 新增代码+DesktopRuntimePanels：函数段结束，_gui_panel_record 到此结束；如果没有边界说明，初学者不易看出它只做类型收敛。

def _safe_gui_panel_error() -> str:  # 新增代码+DesktopRuntimePanels：函数段开始，返回不含路径的降级错误文案；如果没有这段，异常文本可能泄露本机目录。
    return "状态快照暂时不可读。"  # 新增代码+DesktopRuntimePanels：固定安全错误文本；如果没有这行，PermissionError 里的用户名或路径可能进入 GUI。
# 新增代码+DesktopRuntimePanels：函数段结束，_safe_gui_panel_error 到此结束；如果没有边界说明，初学者不易看出错误脱敏范围。

def _runtime_browser_panel_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DesktopRuntimePanels：函数段开始，从统一快照提取浏览器成熟面板字段；如果没有这段，V2 面板会重复理解 browser 快照结构。
    browser = _gui_panel_record(snapshot.get("browser", {}))  # 新增代码+DesktopRuntimePanels：读取 browser 区块；如果没有这行，浏览器面板没有父级上下文。
    provider_status = _gui_panel_record(browser.get("provider_status", {}))  # 新增代码+DesktopRuntimePanels：读取 provider_status；如果没有这行，provider chips 没有数据源。
    providers = _gui_panel_record(provider_status.get("providers", {}))  # 新增代码+DesktopRuntimePanels：读取 provider 集合；如果没有这行，visible Chromium/CDP/Extension 状态无法显示。
    extension = _gui_panel_record(provider_status.get("chrome_extension", {}))  # 新增代码+DesktopRuntimePanels：读取扩展状态；如果没有这行，extension host 连接状态不可见。
    tabs = _gui_panel_record(provider_status.get("tabs", {}))  # 新增代码+DesktopRuntimePanels：读取标签页摘要；如果没有这行，active target 和 tab 数量缺上下文。
    active_target = _gui_panel_record(provider_status.get("active_target", {}))  # 新增代码+DesktopRuntimePanels：读取当前目标摘要；如果没有这行，用户不知道浏览器面板指向哪个目标。
    safe_error = _safe_gui_panel_error() if provider_status.get("error") else ""  # 新增代码+DesktopRuntimePanels：把 provider 错误收敛为安全短文案；如果没有这行，原始路径错误可能进入 GUI。
    return {"providers": providers, "extension": extension, "tabs": tabs, "active_target": active_target, "status_degraded": bool(browser.get("degraded") or provider_status.get("error")), "safe_error": safe_error}  # 新增代码+DesktopRuntimePanels：返回浏览器面板安全摘要；如果没有这行，前端要继续拼接多个不稳定字段。
# 新增代码+DesktopRuntimePanels：函数段结束，_runtime_browser_panel_from_snapshot 到此结束；如果没有边界说明，初学者不易看出浏览器摘要范围。

def _computer_use_mode_root(workspace: str | Path) -> Path:  # 新增代码+DesktopRuntimePanels：函数段开始，定位 GUI 专用 Computer Use 模式状态目录；如果没有这段，测试和 GUI 会读写全局状态。
    return Path(workspace).expanduser().resolve() / "memory" / "computer_use" / "mode_sessions" / "gui"  # 新增代码+DesktopRuntimePanels：把模式状态放到当前 workspace memory；如果没有这行，临时测试可能污染真实 Computer Use 状态。
# 新增代码+DesktopRuntimePanels：函数段结束，_computer_use_mode_root 到此结束；如果没有边界说明，初学者不易看出状态目录策略。

def _computer_use_mode_status(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopRuntimePanels：函数段开始，读取 Computer Use 模式安全状态；如果没有这段，面板无法显示 full/off/observe。
    from learning_agent.computer_use_mcp_v2.windows_runtime.mode_session import ComputerUseModeSessionStore  # 新增代码+DesktopRuntimePanels：延迟导入模式 store；如果没有这行，GUI 无法复用现有 Computer Use 模式事实源。

    status = ComputerUseModeSessionStore(base_dir=_computer_use_mode_root(workspace)).status()  # 新增代码+DesktopRuntimePanels：读取隔离模式状态；如果没有这行，Computer Use 面板只能显示静态假数据。
    return status if isinstance(status, dict) else {}  # 新增代码+DesktopRuntimePanels：防御异常返回类型；如果没有这行，坏 store 会拖垮 bridge。
# 新增代码+DesktopRuntimePanels：函数段结束，_computer_use_mode_status 到此结束；如果没有边界说明，初学者不易看出模式状态读取范围。

def _runtime_computer_use_panel(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopRuntimePanels：函数段开始，生成 Computer Use 面板安全摘要；如果没有这段，用户看不到锁、急停和权限模式。
    try:  # 新增代码+DesktopRuntimePanels：保护 Computer Use 状态读取；如果没有这行，坏 JSON 或权限错误会让整个 panel 端点失败。
        mode_status = _computer_use_mode_status(workspace)  # 新增代码+DesktopRuntimePanels：读取模式状态；如果没有这行，mode/full_mode/stopped 等字段没有来源。
        mode_degraded = False  # 新增代码+DesktopRuntimePanels：记录模式读取正常；如果没有这行，前端无法区分正常 off 和降级 off。
    except Exception:  # 新增代码+DesktopRuntimePanels：捕获状态读取异常；如果没有这行，临时文件错误会打断 GUI 轮询。
        mode_status = {"mode": "off", "full_mode": False, "stopped": False, "expired": False, "allowed_action_classes": []}  # 新增代码+DesktopRuntimePanels：提供安全 off 兜底；如果没有这行，前端可能收到缺字段对象。
        mode_degraded = True  # 新增代码+DesktopRuntimePanels：标记模式摘要降级；如果没有这行，诊断页不知道 Computer Use 状态不完整。
    lock_summary = {"locked": False, "owner": "", "safe_state": "unlocked"}  # 新增代码+DesktopRuntimePanels：返回安全锁摘要默认值；如果没有这行，用户看不到 lock 字段且前端要猜。
    abort_summary = {"requested": False, "global_hotkey_registered": False, "terminal_abort_fallback": True}  # 新增代码+DesktopRuntimePanels：返回安全急停摘要默认值；如果没有这行，用户看不到 abort 字段。
    return {"mode": str(mode_status.get("mode", "off")), "full_mode": bool(mode_status.get("full_mode", False)), "stopped": bool(mode_status.get("stopped", False)), "expired": bool(mode_status.get("expired", False)), "allowed_action_classes": list(mode_status.get("allowed_action_classes", [])) if isinstance(mode_status.get("allowed_action_classes", []), list) else [], "permission_mode": str(mode_status.get("mode", "off")), "lock": lock_summary, "abort": abort_summary, "status_degraded": mode_degraded, "safe_error": _safe_gui_panel_error() if mode_degraded else ""}  # 新增代码+DesktopRuntimePanels：返回不含 state_path 的 Computer Use 面板；如果没有这行，前端可能泄露本机状态文件路径。
# 新增代码+DesktopRuntimePanels：函数段结束，_runtime_computer_use_panel 到此结束；如果没有边界说明，初学者不易看出 Computer Use 摘要范围。

def _runtime_permissions_panel_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DesktopRuntimePanels：函数段开始，从事件尾巴生成权限摘要；如果没有这段，权限状态仍只藏在原始事件流。
    raw_events = snapshot.get("status_events", [])  # 新增代码+DesktopRuntimePanels：读取状态事件列表；如果没有这行，pending 权限没有输入来源。
    events = raw_events if isinstance(raw_events, list) else []  # 新增代码+DesktopRuntimePanels：防御坏快照事件类型；如果没有这行，非列表会拖垮遍历。
    pending_events = [event for event in events if isinstance(event, dict) and str(event.get("event_type", "")) in {"permission_required", "gui_turn_needs_permission"}]  # 新增代码+DesktopRuntimePanels：筛出待权限事件；如果没有这行，权限计数会把普通事件也算进去。
    latest = pending_events[-1] if pending_events else {}  # 新增代码+DesktopRuntimePanels：读取最后一条权限事件；如果没有这行，面板无法显示最近请求摘要。
    payload = _gui_panel_record(latest.get("payload", {})) if isinstance(latest, dict) else {}  # 新增代码+DesktopRuntimePanels：读取最近权限 payload；如果没有这行，request_id/tool_name 无法安全提取。
    return {"pending_count": len(pending_events), "latest_request_id": str(payload.get("request_id", "")), "latest_tool_name": str(payload.get("tool_name", payload.get("app_name", ""))), "mode": "interactive"}  # 新增代码+DesktopRuntimePanels：返回权限安全摘要；如果没有这行，前端不能在设置/诊断里显示权限待办。
# 新增代码+DesktopRuntimePanels：函数段结束，_runtime_permissions_panel_from_snapshot 到此结束；如果没有边界说明，初学者不易看出权限摘要范围。

def build_gui_runtime_panels_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopRuntimePanels：函数段开始，生成 V2 浏览器和 Computer Use 聚合面板 payload；如果没有这段，前端要多次请求并自己拼安全状态。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+DesktopRuntimePanels：规范化 workspace；如果没有这行，模式状态目录和快照读取路径不稳定。
    try:  # 新增代码+DesktopRuntimePanels：保护统一快照读取；如果没有这行，文件锁或坏 JSON 会让 V2 panel endpoint 500。
        snapshot = build_status_snapshot(workspace_path)  # 新增代码+DesktopRuntimePanels：读取统一状态快照；如果没有这行，browser/permissions 会再次旁路读取。
        safe_snapshot = snapshot if isinstance(snapshot, dict) else {}  # 新增代码+DesktopRuntimePanels：防御非 dict 快照；如果没有这行，坏返回类型会拖垮面板。
        status_degraded = False  # 新增代码+DesktopRuntimePanels：记录快照读取正常；如果没有这行，前端无法区分正常和降级状态。
        safe_error = ""  # 新增代码+DesktopRuntimePanels：正常场景不显示错误；如果没有这行，payload 字段不稳定。
    except Exception:  # 新增代码+DesktopRuntimePanels：捕获快照读取异常；如果没有这行，Windows 权限/锁错误会导致 Electron 面板断线。
        safe_snapshot = {"browser": {"provider_status": {"providers": {}, "error": _safe_gui_panel_error()}}, "status_events": []}  # 新增代码+DesktopRuntimePanels：提供不含路径的降级快照；如果没有这行，前端会空白或收到异常详情。
        status_degraded = True  # 新增代码+DesktopRuntimePanels：标记整体降级；如果没有这行，用户不知道面板数据不完整。
        safe_error = _safe_gui_panel_error()  # 新增代码+DesktopRuntimePanels：返回安全错误文本；如果没有这行，前端不知道为什么降级。
    browser_panel = _runtime_browser_panel_from_snapshot(safe_snapshot)  # 新增代码+DesktopRuntimePanels：生成浏览器面板摘要；如果没有这行，payload 缺少 browser。
    computer_use_panel = _runtime_computer_use_panel(workspace_path)  # 新增代码+DesktopRuntimePanels：生成 Computer Use 面板摘要；如果没有这行，payload 缺少桌面自动化状态。
    permissions_panel = _runtime_permissions_panel_from_snapshot(safe_snapshot)  # 新增代码+DesktopRuntimePanels：生成权限摘要；如果没有这行，payload 缺少 permissions。
    return {"ok": True, "schema_version": GUI_SCHEMA_VERSION, "browser": browser_panel, "computer_use": computer_use_panel, "permissions": permissions_panel, "status_degraded": bool(status_degraded or browser_panel.get("status_degraded") or computer_use_panel.get("status_degraded")), "safe_error": safe_error}  # 新增代码+DesktopRuntimePanels：返回稳定 V2 聚合 payload；如果没有这行，前端无法一次刷新成熟面板。
# 新增代码+DesktopRuntimePanels：函数段结束，build_gui_runtime_panels_payload 到此结束；如果没有边界说明，初学者不易看出 V2 panel payload 范围。


def _gui_harness_text(value: Any, max_chars: int = 240) -> str:  # 新增代码+DesktopGUIHarnessPanel：函数段开始，把未知字段收敛为短文本；如果没有这段，坏 JSON 或超长 checkpoint 会撑破右侧 Harness 面板。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+DesktopGUIHarnessPanel：把 None、多行和空白变成安全单行；如果没有这行，前端会收到难以布局的原始文本。
    return text[:max_chars]  # 新增代码+DesktopGUIHarnessPanel：限制文本长度；如果没有这行，长 prompt 或输出摘要可能拖慢 GUI。
# 新增代码+DesktopGUIHarnessPanel：函数段结束，_gui_harness_text 到此结束；如果没有边界说明，初学者不易看出它只负责文本清洗。


def _gui_harness_records(value: Any) -> list[dict[str, Any]]:  # 新增代码+DesktopGUIHarnessPanel：函数段开始，把未知列表收敛为 dict 列表；如果没有这段，快照字段类型漂移会拖垮 harness payload。
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []  # 新增代码+DesktopGUIHarnessPanel：只保留普通对象；如果没有这行，字符串或数字会在后续 get() 调用时报错。
# 新增代码+DesktopGUIHarnessPanel：函数段结束，_gui_harness_records 到此结束；如果没有边界说明，初学者不易看出它只负责类型防护。


def _gui_harness_active_run(runs: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+DesktopGUIHarnessPanel：函数段开始，从 run 列表选择当前目标；如果没有这段，右侧面板不知道哪个长任务是主目标。
    active_statuses = {"running", "queued", "needs_permission", "cancelling"}  # 新增代码+DesktopGUIHarnessPanel：定义仍需要关注的状态；如果没有这行，已完成任务可能盖过正在跑的任务。
    active_runs = [run for run in runs if str(run.get("status", "")) in active_statuses]  # 新增代码+DesktopGUIHarnessPanel：优先筛选活动任务；如果没有这行，历史 run 会干扰当前目标。
    candidates = active_runs or runs  # 新增代码+DesktopGUIHarnessPanel：没有活动任务时退回最近任务；如果没有这行，刚完成的任务无法在面板中解释。
    return sorted(candidates, key=lambda run: str(run.get("updated_at", "")))[-1] if candidates else {}  # 新增代码+DesktopGUIHarnessPanel：按更新时间取最新候选；如果没有这行，面板可能展示旧目标。
# 新增代码+DesktopGUIHarnessPanel：函数段结束，_gui_harness_active_run 到此结束；如果没有边界说明，初学者不易看出它只负责选择 run。


def _gui_harness_goal_from_run(run: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DesktopGUIHarnessPanel：函数段开始，把 run 摘成 active_goal；如果没有这段，前端需要理解完整 harness run 结构。
    if not run:  # 新增代码+DesktopGUIHarnessPanel：没有 run 时返回空目标；如果没有这行，空状态会尝试读取缺失字段。
        return {}  # 新增代码+DesktopGUIHarnessPanel：返回空对象作为稳定兜底；如果没有这行，前端要处理 None。
    stages = _gui_harness_records(run.get("stages", []))  # 新增代码+DesktopGUIHarnessPanel：读取阶段列表；如果没有这行，当前步骤无法从 run 中提取。
    current_index = int(run.get("current_stage_index", 0) or 0)  # 新增代码+DesktopGUIHarnessPanel：读取当前阶段索引；如果没有这行，恢复点无法显示。
    current_stage = stages[current_index] if 0 <= current_index < len(stages) else {}  # 新增代码+DesktopGUIHarnessPanel：按索引找到当前阶段；如果没有这行，running_step 会丢失。
    return {"run_id": _gui_harness_text(run.get("run_id", ""), 120), "prompt": _gui_harness_text(run.get("prompt", ""), 320), "status": _gui_harness_text(run.get("status", ""), 80), "current_stage_index": current_index, "stage_count": len(stages), "running_step": _gui_harness_text(current_stage.get("name", ""), 160), "running_step_status": _gui_harness_text(current_stage.get("status", ""), 80), "updated_at": _gui_harness_text(run.get("updated_at", ""), 120)}  # 新增代码+DesktopGUIHarnessPanel：返回前端可直接渲染的目标摘要；如果没有这行，HarnessPanel 会被迫解析后端内部字段。
# 新增代码+DesktopGUIHarnessPanel：函数段结束，_gui_harness_goal_from_run 到此结束；如果没有边界说明，初学者不易看出它只负责目标摘要。


def _gui_harness_queue_from_snapshot(snapshot: dict[str, Any], runs: list[dict[str, Any]]) -> list[dict[str, Any]]:  # 新增代码+DesktopGUIHarnessPanel：函数段开始，生成队列摘要；如果没有这段，长任务等待项仍只藏在 runtime queue 或 runs 里。
    queue: list[dict[str, Any]] = []  # 新增代码+DesktopGUIHarnessPanel：准备队列输出列表；如果没有这行，后续无法累加命令和 run。
    for command in _gui_harness_records(snapshot.get("commands", [])):  # 新增代码+DesktopGUIHarnessPanel：遍历 runtime command queue；如果没有这行，排队 prompt 和通知不会进入 GUI。
        payload = _gui_panel_record(command.get("payload", {}))  # 新增代码+DesktopGUIHarnessPanel：读取命令 payload；如果没有这行，summary 无法从 text/prompt 中提取。
        queue.append({"id": _gui_harness_text(command.get("command_id", ""), 120), "kind": _gui_harness_text(command.get("mode", ""), 80), "status": _gui_harness_text(command.get("status", ""), 80), "priority": _gui_harness_text(command.get("priority", ""), 40), "summary": _gui_harness_text(payload.get("text", payload.get("prompt", command.get("mode", ""))), 220), "updated_at": _gui_harness_text(command.get("updated_at", ""), 120)})  # 新增代码+DesktopGUIHarnessPanel：写入命令队列条目；如果没有这行，前端看不到队列状态。
    for run in runs:  # 新增代码+DesktopGUIHarnessPanel：遍历 harness runs；如果没有这行，queued/running run 不会作为长任务队列项出现。
        if str(run.get("status", "")) not in {"queued", "running"}:  # 新增代码+DesktopGUIHarnessPanel：只展示仍需关注的 run；如果没有这行，历史完成任务会塞满队列。
            continue  # 新增代码+DesktopGUIHarnessPanel：跳过终态 run；如果没有这行，下面会错误加入历史项。
        queue.append({"id": _gui_harness_text(run.get("run_id", ""), 120), "kind": "harness_run", "status": _gui_harness_text(run.get("status", ""), 80), "priority": "", "summary": _gui_harness_text(run.get("prompt", ""), 220), "updated_at": _gui_harness_text(run.get("updated_at", ""), 120)})  # 新增代码+DesktopGUIHarnessPanel：写入 run 队列条目；如果没有这行，长任务本体不可见。
    return queue[:50]  # 新增代码+DesktopGUIHarnessPanel：限制队列输出数量；如果没有这行，大队列会拖慢右侧栏。
# 新增代码+DesktopGUIHarnessPanel：函数段结束，_gui_harness_queue_from_snapshot 到此结束；如果没有边界说明，初学者不易看出它只负责队列摘要。


def _gui_harness_checkpoints_from_snapshot(snapshot: dict[str, Any], runs: list[dict[str, Any]]) -> list[dict[str, Any]]:  # 新增代码+DesktopGUIHarnessPanel：函数段开始，生成 checkpoint 时间线；如果没有这段，用户无法判断长任务是否按阶段推进。
    checkpoints: list[dict[str, Any]] = []  # 新增代码+DesktopGUIHarnessPanel：准备 checkpoint 输出列表；如果没有这行，后续无法累加阶段和事件。
    for run in runs:  # 新增代码+DesktopGUIHarnessPanel：遍历所有 run 的阶段；如果没有这行，阶段 checkpoint 不会进入面板。
        for stage in _gui_harness_records(run.get("stages", [])):  # 新增代码+DesktopGUIHarnessPanel：遍历 run 阶段；如果没有这行，无法按阶段展示恢复点。
            checkpoint = _gui_harness_text(stage.get("checkpoint", ""), 260)  # 新增代码+DesktopGUIHarnessPanel：读取阶段 checkpoint；如果没有这行，后续无法判断是否值得显示。
            if checkpoint:  # 新增代码+DesktopGUIHarnessPanel：只显示有内容的 checkpoint；如果没有这行，空阶段会产生噪音。
                checkpoints.append({"source": "stage", "run_id": _gui_harness_text(run.get("run_id", ""), 120), "stage_index": int(stage.get("index", len(checkpoints)) or len(checkpoints)), "stage_name": _gui_harness_text(stage.get("name", ""), 160), "status": _gui_harness_text(stage.get("status", ""), 80), "checkpoint": checkpoint, "timestamp": _gui_harness_text(stage.get("completed_at", stage.get("started_at", "")), 120)})  # 新增代码+DesktopGUIHarnessPanel：写入阶段 checkpoint；如果没有这行，恢复点没有结构化字段。
    for event in _gui_harness_records(snapshot.get("status_events", [])):  # 新增代码+DesktopGUIHarnessPanel：遍历状态事件尾巴；如果没有这行，事件型 checkpoint 不会显示。
        event_type = str(event.get("event_type", ""))  # 新增代码+DesktopGUIHarnessPanel：读取事件类型；如果没有这行，无法筛选 checkpoint 事件。
        if "checkpoint" not in event_type:  # 新增代码+DesktopGUIHarnessPanel：只关注 checkpoint 相关事件；如果没有这行，普通事件会污染 checkpoint 列表。
            continue  # 新增代码+DesktopGUIHarnessPanel：跳过非 checkpoint 事件；如果没有这行，下面会错误加入。
        payload = _gui_panel_record(event.get("payload", {}))  # 新增代码+DesktopGUIHarnessPanel：读取事件 payload；如果没有这行，checkpoint 文本没有来源。
        checkpoints.append({"source": "event", "sequence": int(event.get("sequence", 0) or 0), "run_id": _gui_harness_text(event.get("run_id", payload.get("run_id", "")), 120), "stage_name": _gui_harness_text(payload.get("stage_name", payload.get("stage", "")), 160), "status": _gui_harness_text(payload.get("status", event_type), 80), "checkpoint": _gui_harness_text(payload.get("checkpoint", payload.get("summary", event_type)), 260), "timestamp": _gui_harness_text(event.get("created_at", payload.get("timestamp", "")), 120)})  # 新增代码+DesktopGUIHarnessPanel：写入事件 checkpoint；如果没有这行，事件顺序不可见。
    return checkpoints[-50:]  # 新增代码+DesktopGUIHarnessPanel：保留最近 50 条 checkpoint；如果没有这行，长期运行的任务会让 payload 过大。
# 新增代码+DesktopGUIHarnessPanel：函数段结束，_gui_harness_checkpoints_from_snapshot 到此结束；如果没有边界说明，初学者不易看出它只负责 checkpoint 摘要。


def _gui_harness_blocked_reason(snapshot: dict[str, Any], active_run: dict[str, Any]) -> str:  # 新增代码+DesktopGUIHarnessPanel：函数段开始，提取阻塞原因；如果没有这段，任务卡住时 GUI 只能显示泛化状态。
    if _gui_harness_text(active_run.get("failure_reason", "")):  # 新增代码+DesktopGUIHarnessPanel：优先使用 run 失败原因；如果没有这行，失败任务原因可能被事件覆盖。
        return _gui_harness_text(active_run.get("failure_reason", ""), 260)  # 新增代码+DesktopGUIHarnessPanel：返回脱敏短文本；如果没有这行，失败原因无法显示。
    for event in reversed(_gui_harness_records(snapshot.get("status_events", []))):  # 新增代码+DesktopGUIHarnessPanel：从最新事件向前找 blocked 原因；如果没有这行，用户看不到最近卡点。
        payload = _gui_panel_record(event.get("payload", {}))  # 新增代码+DesktopGUIHarnessPanel：读取事件 payload；如果没有这行，blocked_reason 字段不可访问。
        reason = payload.get("blocked_reason", payload.get("reason", ""))  # 新增代码+DesktopGUIHarnessPanel：兼容不同事件字段；如果没有这行，旧事件无法复用。
        if reason and "block" in str(event.get("event_type", "")).lower():  # 新增代码+DesktopGUIHarnessPanel：确认这是阻塞事件；如果没有这行，普通 reason 可能误报为阻塞。
            return _gui_harness_text(reason, 260)  # 新增代码+DesktopGUIHarnessPanel：返回阻塞原因；如果没有这行，函数会继续找旧事件。
    return ""  # 新增代码+DesktopGUIHarnessPanel：没有阻塞时返回空字符串；如果没有这行，前端要处理 None。
# 新增代码+DesktopGUIHarnessPanel：函数段结束，_gui_harness_blocked_reason 到此结束；如果没有边界说明，初学者不易看出它只负责阻塞摘要。


def build_gui_harness_status_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIHarnessPanel：函数段开始，生成 V2 长任务 Harness 面板 payload；如果没有这段，前端只能显示静态任务面板。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUIHarnessPanel：规范化 workspace；如果没有这行，快照读取路径不稳定。
    try:  # 新增代码+DesktopGUIHarnessPanel：保护统一快照读取；如果没有这行，坏 JSON 或锁文件会让 Harness 面板 500。
        snapshot = build_status_snapshot(workspace_path)  # 新增代码+DesktopGUIHarnessPanel：读取统一事实源；如果没有这行，GUI 会绕过 bridge 边界读文件。
        safe_snapshot = snapshot if isinstance(snapshot, dict) else {}  # 新增代码+DesktopGUIHarnessPanel：防御非 dict 快照；如果没有这行，坏返回类型会拖垮端点。
        safe_error = ""  # 新增代码+DesktopGUIHarnessPanel：正常读取时无错误；如果没有这行，payload 字段会不稳定。
        status_degraded = False  # 新增代码+DesktopGUIHarnessPanel：记录快照是否降级；如果没有这行，前端不知道数据可信度。
    except Exception:  # 新增代码+DesktopGUIHarnessPanel：捕获快照读取异常；如果没有这行，临时文件问题会让 Electron 右栏断线。
        safe_snapshot = {"runs": [], "commands": [], "status_events": []}  # 新增代码+DesktopGUIHarnessPanel：提供空但稳定的降级快照；如果没有这行，后续 helper 会缺输入。
        safe_error = _safe_gui_panel_error()  # 新增代码+DesktopGUIHarnessPanel：使用不含本机路径的错误文本；如果没有这行，异常可能泄露用户目录。
        status_degraded = True  # 新增代码+DesktopGUIHarnessPanel：标记降级状态；如果没有这行，UI 无法提示数据不完整。
    runs = _gui_harness_records(safe_snapshot.get("runs", []))  # 新增代码+DesktopGUIHarnessPanel：读取 harness runs；如果没有这行，active_goal 没有来源。
    active_run = _gui_harness_active_run(runs)  # 新增代码+DesktopGUIHarnessPanel：选择当前 run；如果没有这行，目标摘要无法确定。
    checkpoints = _gui_harness_checkpoints_from_snapshot(safe_snapshot, runs)  # 新增代码+DesktopGUIHarnessPanel：生成 checkpoint 列表；如果没有这行，阶段进度不可见。
    last_progress = checkpoints[-1]["checkpoint"] if checkpoints else _gui_harness_text(active_run.get("prompt", ""), 260)  # 新增代码+DesktopGUIHarnessPanel：给面板一个最近进展摘要；如果没有这行，空 checkpoint 时看不到任务上下文。
    return {"ok": True, "schema_version": GUI_SCHEMA_VERSION, "active_goal": _gui_harness_goal_from_run(active_run), "queue": _gui_harness_queue_from_snapshot(safe_snapshot, runs), "checkpoints": checkpoints, "last_progress": last_progress, "blocked_reason": _gui_harness_blocked_reason(safe_snapshot, active_run), "safe_error": safe_error, "status_degraded": status_degraded, "controls": {"pause_supported": False, "resume_supported": False}}  # 新增代码+DesktopGUIHarnessPanel：返回稳定 Harness payload；如果没有这行，前端无法渲染长任务面板。
# 新增代码+DesktopGUIHarnessPanel：函数段结束，build_gui_harness_status_payload 到此结束；如果没有边界说明，初学者不易看出它只负责面板数据。


def build_gui_harness_control_payload(action: str) -> dict[str, Any]:  # 新增代码+DesktopGUIHarnessPanel：函数段开始，返回长任务控制请求结果；如果没有这段，暂停/恢复按钮无法获得结构化反馈。
    safe_action = "resume" if action == "resume" else "pause"  # 新增代码+DesktopGUIHarnessPanel：限制动作名称；如果没有这行，未知 action 可能进入响应。
    return {"ok": True, "schema_version": GUI_SCHEMA_VERSION, "action": safe_action, "supported": False, "status": "unsupported", "message": "当前后端尚未暴露长任务暂停/恢复控制，GUI 会隐藏控制按钮。", "safe_error": ""}  # 新增代码+DesktopGUIHarnessPanel：返回结构化未支持响应；如果没有这行，前端只能把 404 当成控制失败。
# 新增代码+DesktopGUIHarnessPanel：函数段结束，build_gui_harness_control_payload 到此结束；如果没有边界说明，初学者不易看出它只负责控制响应。


class GuiRunManager:  # 新增代码+DesktopGUILifecycle：类段开始，管理 GUI turn 生命周期；如果没有这个类，handler 会堆满业务状态逻辑。
    def __init__(self, workspace: str | Path, answer_runner: GuiAnswerRunner | None = None, agent_adapter: GuiAgentAdapter | None = None) -> None:  # 修改代码+GuiAgentAdapter：初始化 run manager 并允许注入 V2 adapter；如果没有这个参数，bridge 无法从 fake adapter 平滑升级到真实 harness adapter。
        self.workspace = Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUILifecycle：保存规范化工作区；如果没有这行，状态和事件路径不稳定。
        self.state_dir = _state_memory_dir(self.workspace)  # 新增代码+DesktopGUILifecycle：定位 GUI 状态目录；如果没有这行，resume 无法落盘。
        self.state_path = self.state_dir / "state.json"  # 新增代码+DesktopGUILifecycle：保存状态文件路径；如果没有这行，load/save 没有目标文件。
        self.event_store = _status_store(self.workspace)  # 新增代码+DesktopGUILifecycle：保存统一事件 store；如果没有这行，生命周期事件无法写入事实源。
        self.answer_runner_override = answer_runner  # 新增代码+GuiAgentAdapter：记住调用方是否显式传入旧 runner；如果没有这一行，无法区分兼容测试路径和默认 V2 adapter 路径。
        self.answer_runner = answer_runner or self._default_answer_runner  # 修改代码+GuiAgentAdapter：保留 V1 runner 兼容入口；如果没有这一行，旧测试或外部注入 runner 会失效。
        self.agent_adapter = agent_adapter or FakeStreamingGuiAgentAdapter()  # 新增代码+GuiAgentAdapter：默认使用 deterministic fake streaming adapter；如果没有这一行，V2-Core 无法稳定产生 message_delta。
        self.lock = threading.RLock()  # 新增代码+DesktopGUILifecycle：保护 turns/sessions/active 状态；如果没有这行，并发请求可能写坏状态。
        self.turns: dict[str, GuiTurn] = {}  # 新增代码+DesktopGUILifecycle：保存 turn 字典；如果没有这行，cancel/retry 找不到目标 turn。
        self.sessions: dict[str, GuiSession] = {}  # 新增代码+DesktopGUILifecycle：保存 session 字典；如果没有这行，resume 没有消息来源。
        self.permissions: dict[str, GuiPermissionRequest] = {}  # 新增代码+DesktopGUIPermissions：保存权限请求字典；如果没有这行，decision endpoint 无法判断未知请求或重复回答。
        self.cancel_events: dict[str, threading.Event] = {}  # 新增代码+DesktopGUILifecycle：保存取消信号；如果没有这行，worker 无法感知 cancel。
        self.active_turn_id: str | None = None  # 新增代码+DesktopGUILifecycle：保存当前 active turn；如果没有这行，busy 检查无法生效。
        self._load_state()  # 新增代码+DesktopGUILifecycle：启动时加载上次 session；如果没有这行，窗口重启无法恢复。
    # 新增代码+DesktopGUILifecycle：初始化段结束，GuiRunManager.__init__ 到此结束；如果没有边界说明，初学者不易看出初始化范围。

    def _default_answer_runner(self, prompt: str, _session_id: str, _turn_id: str) -> str:  # 新增代码+DesktopGUILifecycle：函数段开始，提供 V1 默认回答 runner；如果没有这段，测试和无模型 bridge 无法完成 turn。
        return f"OpenHarness Desktop 已收到 GUI prompt：{prompt}"  # 新增代码+DesktopGUILifecycle：返回可读默认回答；如果没有这行，完成态没有最终 answer。
    # 新增代码+DesktopGUILifecycle：函数段结束，_default_answer_runner 到此结束；如果没有边界说明，初学者不易看出它只是临时 runner。

    def _load_state(self) -> None:  # 新增代码+DesktopGUILifecycle：函数段开始，从磁盘恢复 GUI 状态；如果没有这段，resume 只能在进程内有效。
        if not self.state_path.exists():  # 新增代码+DesktopGUILifecycle：处理首次启动无状态文件；如果没有这行，打开文件会报错。
            return  # 新增代码+DesktopGUILifecycle：无状态时直接返回；如果没有这行，首次启动会失败。
        try:  # 新增代码+DesktopGUILifecycle：容错读取状态文件；如果没有这行，坏 JSON 会拖垮 bridge。
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))  # 新增代码+DesktopGUILifecycle：读取并解析状态 JSON；如果没有这行，无法恢复 turns/sessions。
        except (OSError, json.JSONDecodeError):  # 新增代码+DesktopGUILifecycle：捕获文件或 JSON 错误；如果没有这行，坏状态会导致启动失败。
            return  # 新增代码+DesktopGUILifecycle：坏状态先跳过；如果没有这行，bridge 无法继续提供新会话。
        self.turns = {item["turn_id"]: GuiTurn(**item) for item in raw.get("turns", []) if isinstance(item, dict) and "turn_id" in item}  # 新增代码+DesktopGUILifecycle：恢复 turn 字典；如果没有这行，retry 找不到历史 turn。
        loaded_sessions: dict[str, GuiSession] = {}  # 修改代码+DesktopGUISessionSearch：先建立临时会话字典；如果没有这行，后续兼容旧 state 字段会被塞进难懂的一行推导式。
        for item in raw.get("sessions", []):  # 修改代码+DesktopGUISessionSearch：逐个恢复落盘会话；如果没有这行，V2 标题和归档字段无法安全兼容旧状态。
            if not isinstance(item, dict) or "session_id" not in item:  # 修改代码+DesktopGUISessionSearch：跳过坏会话记录；如果没有这行，损坏 state 会让 bridge 启动失败。
                continue  # 修改代码+DesktopGUISessionSearch：坏记录直接跳过；如果没有这行，后续字段读取会抛异常。
            messages = [GuiMessage(**message) for message in item.get("messages", []) if isinstance(message, dict)]  # 修改代码+DesktopGUISessionSearch：恢复消息列表；如果没有这行，resume 不会带回历史对话。
            loaded_sessions[str(item["session_id"])] = GuiSession(session_id=str(item["session_id"]), messages=messages, last_turn_id=str(item.get("last_turn_id", "")), title=str(item.get("title", "")), archived=bool(item.get("archived", False)), pinned=bool(item.get("pinned", False)), updated_at=float(item.get("updated_at", 0.0) or 0.0))  # 修改代码+DesktopGUISessionSearch：兼容恢复 V1/V2 会话字段；如果没有这行，rename/archive/pin/排序状态会在重启后丢失。
        self.sessions = loaded_sessions  # 修改代码+DesktopGUISessionSearch：把恢复结果交给 manager；如果没有这行，后续接口仍会看到空会话。
        self.permissions = {item["request_id"]: GuiPermissionRequest(**item) for item in raw.get("permissions", []) if isinstance(item, dict) and "request_id" in item}  # 新增代码+DesktopGUIPermissions：恢复权限请求字典；如果没有这行，重启后重复回答会绕过冲突检查。
        self.active_turn_id = None  # 新增代码+DesktopGUILifecycle：重启后不恢复运行中锁；如果没有这行，旧 active turn 会永久阻塞新 prompt。
    # 新增代码+DesktopGUILifecycle：函数段结束，_load_state 到此结束；如果没有边界说明，初学者不易看出恢复范围。

    def _save_state(self) -> None:  # 新增代码+DesktopGUILifecycle：函数段开始，把 GUI 状态写入磁盘；如果没有这段，窗口重启无法恢复会话。
        self.state_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+DesktopGUILifecycle：确保状态目录存在；如果没有这行，写文件会因为目录缺失失败。
        payload = {"turns": [asdict(turn) for turn in self.turns.values()], "sessions": [asdict(session) for session in self.sessions.values()], "permissions": [asdict(permission) for permission in self.permissions.values()]}  # 修改代码+DesktopGUIPermissions：构造可 JSON 化状态并包含权限请求；如果没有这行，权限决策状态无法跨重启保存。
        self.state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")  # 新增代码+DesktopGUILifecycle：写入 UTF-8 JSON；如果没有这行，中文 prompt/answer 会丢失或乱码。
    # 新增代码+DesktopGUILifecycle：函数段结束，_save_state 到此结束；如果没有边界说明，初学者不易看出保存范围。

    def _session(self, session_id: str) -> GuiSession:  # 新增代码+DesktopGUILifecycle：函数段开始，获取或创建 session；如果没有这段，消息追加前都要重复判断。
        if session_id not in self.sessions:  # 新增代码+DesktopGUILifecycle：判断 session 是否存在；如果没有这行，新会话会 KeyError。
            self.sessions[session_id] = GuiSession(session_id=session_id)  # 新增代码+DesktopGUILifecycle：创建新 session；如果没有这行，新对话没有消息容器。
        return self.sessions[session_id]  # 新增代码+DesktopGUILifecycle：返回 session；如果没有这行，调用方拿不到会话对象。
    # 新增代码+DesktopGUILifecycle：函数段结束，_session 到此结束；如果没有边界说明，初学者不易看出它只负责会话容器。

    def _touch_session(self, session: GuiSession) -> None:  # 新增代码+DesktopGUISessionSearch：函数段开始，刷新会话更新时间；如果没有这段，最近会话排序不会跟随新消息或重命名更新。
        session.updated_at = time.time()  # 新增代码+DesktopGUISessionSearch：记录当前时间；如果没有这行，sessions 列表无法稳定把最近会话排在前面。
    # 新增代码+DesktopGUISessionSearch：函数段结束，_touch_session 到此结束；如果没有边界说明，初学者不易看出它只负责更新时间。

    def _session_title(self, session: GuiSession) -> str:  # 新增代码+DesktopGUISessionSearch：函数段开始，生成会话显示标题；如果没有这段，标题逻辑会散落在列表和搜索里。
        if session.title.strip():  # 新增代码+DesktopGUISessionSearch：优先使用用户改名标题；如果没有这行，rename 后侧栏仍会显示旧 prompt。
            return session.title.strip()  # 新增代码+DesktopGUISessionSearch：返回清理后的标题；如果没有这行，标题前后空白会进入 UI。
        for message in session.messages:  # 新增代码+DesktopGUISessionSearch：遍历历史消息寻找首条用户文本；如果没有这行，未命名会话只能显示 session id。
            if message.role == "user" and message.text.strip():  # 新增代码+DesktopGUISessionSearch：只把真实用户输入当默认标题；如果没有这行，助手空占位可能成为标题。
                return message.text.strip()[:80]  # 新增代码+DesktopGUISessionSearch：截断默认标题；如果没有这行，长 prompt 会撑破侧栏。
        return session.session_id  # 新增代码+DesktopGUISessionSearch：没有消息时兜底 session id；如果没有这行，空会话没有可读标题。
    # 新增代码+DesktopGUISessionSearch：函数段结束，_session_title 到此结束；如果没有边界说明，初学者不易看出标题兜底范围。

    def _session_preview(self, session: GuiSession) -> str:  # 新增代码+DesktopGUISessionSearch：函数段开始，生成最近消息摘要；如果没有这段，侧栏和搜索结果缺少上下文。
        for message in reversed(session.messages):  # 新增代码+DesktopGUISessionSearch：从最后一条消息往前找摘要；如果没有这行，预览无法代表最近内容。
            if message.text.strip():  # 新增代码+DesktopGUISessionSearch：跳过空占位消息；如果没有这行，搜索预览可能显示空白。
                return message.text.strip()[:140]  # 新增代码+DesktopGUISessionSearch：限制摘要长度；如果没有这行，长回答会撑开搜索面板。
        return ""  # 新增代码+DesktopGUISessionSearch：没有文本时返回空摘要；如果没有这行，调用方会拿到不稳定的 None。
    # 新增代码+DesktopGUISessionSearch：函数段结束，_session_preview 到此结束；如果没有边界说明，初学者不易看出预览生成范围。

    def _session_summary(self, session: GuiSession) -> dict[str, Any]:  # 新增代码+DesktopGUISessionSearch：函数段开始，把会话转成 V2 列表条目；如果没有这段，多个接口会重复拼装 session 字段。
        latest_turn = self.turns.get(session.last_turn_id) if session.last_turn_id else None  # 新增代码+DesktopGUISessionSearch：读取最近 turn；如果没有这行，侧栏副标题无法显示当前状态。
        status_text = latest_turn.status if latest_turn else ""  # 新增代码+DesktopGUISessionSearch：安全读取最近状态；如果没有这行，空会话会访问不存在的 turn。
        preview_text = self._session_preview(session)  # 新增代码+DesktopGUISessionSearch：生成最近消息摘要；如果没有这行，搜索和侧栏没有上下文短句。
        return {"session_id": session.session_id, "id": session.session_id, "title": self._session_title(session), "subtitle": preview_text or status_text, "last_turn_id": session.last_turn_id, "message_count": len(session.messages), "archived": session.archived, "pinned": session.pinned, "updated_at": session.updated_at, "status": status_text}  # 新增代码+DesktopGUISessionSearch：返回稳定 V2 会话条目；如果没有这行，前端无法用同一结构渲染最近、固定和归档状态。
    # 新增代码+DesktopGUISessionSearch：函数段结束，_session_summary 到此结束；如果没有边界说明，初学者不易看出会话条目字段范围。

    def sessions_payload(self, include_archived: bool = False) -> dict[str, Any]:  # 修改代码+DesktopGUISessionSearch：函数段开始，生成 GUI 侧栏会话列表；如果没有这段代码，左侧“最近对话”不会显示桌面 GUI 自己创建的会话。
        with self.lock:  # 新增代码+DesktopGUISessionList：读取 sessions 时加锁；如果没有这行代码，后台 worker 写消息时列表可能读到半状态。
            visible_sessions = [session for session in self.sessions.values() if include_archived or not session.archived]  # 修改代码+DesktopGUISessionSearch：默认隐藏归档会话；如果没有这行，archive 后侧栏仍会显示旧会话。
            ordered_sessions = sorted(visible_sessions, key=lambda session: (session.pinned, session.updated_at), reverse=True)  # 新增代码+DesktopGUISessionSearch：固定会话优先且最近更新靠前；如果没有这行，侧栏顺序无法表达 Codex 式工作流。
            sessions = [self._session_summary(session) for session in ordered_sessions]  # 修改代码+DesktopGUISessionSearch：生成稳定条目列表；如果没有这行，前端拿不到 title/archive/pin/updated_at 字段。
            archived_count = sum(1 for session in self.sessions.values() if session.archived)  # 新增代码+DesktopGUISessionSearch：统计归档数量；如果没有这行，侧栏归档入口无法显示真实计数。
            latest_session_id = str(sessions[0]["session_id"]) if sessions else ""  # 新增代码+DesktopGUISessionList：记录最近会话 id；如果没有这行代码，resume 摘要没有入口。
            latest_turn_id = str(sessions[0]["last_turn_id"]) if sessions else ""  # 新增代码+DesktopGUISessionList：记录最近 turn id；如果没有这行代码，恢复提示无法定位最后一轮。
            return {"ok": True, "schema_version": GUI_SCHEMA_VERSION, "sessions": sessions, "archived_count": archived_count, "resume": {"latest_session_id": latest_session_id, "latest_turn_id": latest_turn_id}}  # 修改代码+DesktopGUISessionSearch：返回稳定 V2 sessions payload；如果没有这行代码，GET /v2/gui/sessions 无法驱动成熟侧栏。
    # 修改代码+DesktopGUISessionSearch：函数段结束，sessions_payload 到此结束；如果没有边界说明，初学者不易看出它只负责 GUI 会话列表。

    def rename_session(self, session_id: str, title: str) -> dict[str, Any]:  # 新增代码+DesktopGUISessionSearch：函数段开始，重命名已有 session；如果没有这段，侧栏 rename 只能停留在前端临时状态。
        clean_session_id = session_id.strip()  # 新增代码+DesktopGUISessionSearch：清理路径中的 session id；如果没有这行，空格会导致找不到会话。
        clean_title = title.strip()  # 新增代码+DesktopGUISessionSearch：清理新标题；如果没有这行，纯空格标题会进入 UI。
        if not clean_title:  # 新增代码+DesktopGUISessionSearch：拒绝空标题；如果没有这行，用户可能把会话改成不可见。
            raise GuiBridgeError(400, "missing_session_title", "缺少有效的会话标题。")  # 新增代码+DesktopGUISessionSearch：返回结构化标题错误；如果没有这行，前端无法提示输入问题。
        with self.lock:  # 新增代码+DesktopGUISessionSearch：保护会话改名写入；如果没有这行，并发 rename/archive 可能互相覆盖。
            session = self.sessions.get(clean_session_id)  # 新增代码+DesktopGUISessionSearch：查找已有会话；如果没有这行，rename 会意外创建新空会话。
            if session is None:  # 新增代码+DesktopGUISessionSearch：处理未知会话；如果没有这行，后续访问会抛异常。
                raise GuiBridgeError(404, "session_not_found", "未找到要重命名的会话。")  # 新增代码+DesktopGUISessionSearch：返回结构化 404；如果没有这行，前端无法区分会话不存在。
            session.title = clean_title[:120]  # 新增代码+DesktopGUISessionSearch：保存长度受控标题；如果没有这行，超长标题会撑破侧栏。
            self._touch_session(session)  # 新增代码+DesktopGUISessionSearch：更新排序时间；如果没有这行，刚改名的会话不会回到最近区域。
            self._save_state()  # 新增代码+DesktopGUISessionSearch：改名后落盘；如果没有这行，重启后标题会丢失。
            return {"ok": True, "schema_version": GUI_SCHEMA_VERSION, "session": self._session_summary(session)}  # 新增代码+DesktopGUISessionSearch：返回更新后的会话条目；如果没有这行，前端需要重新猜测新状态。
    # 新增代码+DesktopGUISessionSearch：函数段结束，rename_session 到此结束；如果没有边界说明，初学者不易看出改名范围。

    def archive_session(self, session_id: str, archived: bool = True) -> dict[str, Any]:  # 新增代码+DesktopGUISessionSearch：函数段开始，归档或恢复已有 session；如果没有这段，归档入口没有真实后端效果。
        clean_session_id = session_id.strip()  # 新增代码+DesktopGUISessionSearch：清理路径中的 session id；如果没有这行，路径空格会导致错误查找。
        with self.lock:  # 新增代码+DesktopGUISessionSearch：保护归档写入；如果没有这行，并发列表读取可能看到半状态。
            session = self.sessions.get(clean_session_id)  # 新增代码+DesktopGUISessionSearch：查找已有会话；如果没有这行，archive 会意外创建空会话。
            if session is None:  # 新增代码+DesktopGUISessionSearch：处理未知会话；如果没有这行，后续访问会抛异常。
                raise GuiBridgeError(404, "session_not_found", "未找到要归档的会话。")  # 新增代码+DesktopGUISessionSearch：返回结构化 404；如果没有这行，前端无法提示目标已失效。
            session.archived = bool(archived)  # 新增代码+DesktopGUISessionSearch：保存归档状态；如果没有这行，archive 请求不会改变列表。
            self._touch_session(session)  # 新增代码+DesktopGUISessionSearch：更新状态修改时间；如果没有这行，恢复归档时排序不稳定。
            self._save_state()  # 新增代码+DesktopGUISessionSearch：归档后落盘；如果没有这行，重启后会话又会出现。
            return {"ok": True, "schema_version": GUI_SCHEMA_VERSION, "session": self._session_summary(session), "archived": session.archived}  # 新增代码+DesktopGUISessionSearch：返回归档结果；如果没有这行，前端无法确认列表应该隐藏或恢复。
    # 新增代码+DesktopGUISessionSearch：函数段结束，archive_session 到此结束；如果没有边界说明，初学者不易看出归档范围。

    def search_sessions(self, query: str, include_archived: bool = False) -> dict[str, Any]:  # 新增代码+DesktopGUISessionSearch：函数段开始，搜索会话标题和消息；如果没有这段，搜索入口只能是空壳。
        clean_query = query.strip()  # 新增代码+DesktopGUISessionSearch：清理搜索词；如果没有这行，前后空格会造成无意义搜索。
        folded_query = clean_query.casefold()  # 新增代码+DesktopGUISessionSearch：生成大小写无关搜索词；如果没有这行，英文会话标题搜索会不稳定。
        with self.lock:  # 新增代码+DesktopGUISessionSearch：保护搜索读取；如果没有这行，后台写消息时搜索可能读到半状态。
            results: list[dict[str, Any]] = []  # 新增代码+DesktopGUISessionSearch：创建搜索结果数组；如果没有这行，后续无法累计匹配项。
            if not folded_query:  # 新增代码+DesktopGUISessionSearch：空搜索直接返回空结果；如果没有这行，用户打开搜索会看到全部历史刷屏。
                return {"ok": True, "schema_version": GUI_SCHEMA_VERSION, "query": clean_query, "results": results}  # 新增代码+DesktopGUISessionSearch：返回空搜索 payload；如果没有这行，前端需要特别处理空 query。
            for session in sorted(self.sessions.values(), key=lambda item: item.updated_at, reverse=True):  # 新增代码+DesktopGUISessionSearch：按最近更新时间遍历会话；如果没有这行，结果顺序会不符合最近工作流。
                if session.archived and not include_archived:  # 新增代码+DesktopGUISessionSearch：默认跳过归档会话；如果没有这行，归档内容会继续干扰搜索。
                    continue  # 新增代码+DesktopGUISessionSearch：跳过归档会话；如果没有这行，后续仍会匹配该会话。
                title = self._session_title(session)  # 新增代码+DesktopGUISessionSearch：读取会话标题；如果没有这行，标题匹配和结果展示会重复生成。
                title_matches = folded_query in title.casefold()  # 新增代码+DesktopGUISessionSearch：判断标题是否命中；如果没有这行，只有消息正文可搜。
                matched_message = next((message for message in session.messages if folded_query in message.text.casefold()), None)  # 新增代码+DesktopGUISessionSearch：查找首条命中消息；如果没有这行，搜索无法返回消息片段。
                if not title_matches and matched_message is None:  # 新增代码+DesktopGUISessionSearch：没有命中时跳过；如果没有这行，搜索会返回无关会话。
                    continue  # 新增代码+DesktopGUISessionSearch：继续检查下一个会话；如果没有这行，无关结果会进入列表。
                snippet = matched_message.text.strip()[:180] if matched_message is not None else self._session_preview(session)  # 新增代码+DesktopGUISessionSearch：生成结果片段；如果没有这行，用户不知道为什么命中。
                results.append({"session_id": session.session_id, "title": title, "snippet": snippet, "message_role": matched_message.role if matched_message is not None else "", "turn_id": matched_message.turn_id if matched_message is not None else session.last_turn_id, "archived": session.archived, "pinned": session.pinned, "updated_at": session.updated_at})  # 新增代码+DesktopGUISessionSearch：追加稳定搜索结果；如果没有这行，前端搜索面板没有可点击数据。
            return {"ok": True, "schema_version": GUI_SCHEMA_VERSION, "query": clean_query, "results": results}  # 新增代码+DesktopGUISessionSearch：返回搜索 payload；如果没有这行，GET /v2/gui/search 无法工作。
    # 新增代码+DesktopGUISessionSearch：函数段结束，search_sessions 到此结束；如果没有边界说明，初学者不易看出搜索范围。

    def _append_event(self, event_type: str, turn: GuiTurn, payload: dict[str, Any] | None = None) -> int:  # 新增代码+DesktopGUILifecycle：函数段开始，写入生命周期事件；如果没有这段，各事件字段会不一致。
        event_payload = {"status": turn.status, "retry_of": turn.retry_of, **(payload or {})}  # 新增代码+DesktopGUILifecycle：构造事件正文；如果没有这行，时间线缺少状态和 retry 来源。
        event = self.event_store.append(event_type, event_payload, session_id=turn.session_id, run_id=turn.run_id, turn_id=turn.turn_id)  # 新增代码+DesktopGUILifecycle：写入统一事件流；如果没有这行，GUI watcher 看不到生命周期。
        return event.sequence  # 新增代码+DesktopGUILifecycle：返回事件序号；如果没有这行，响应无法给出 events_after_sequence。
    # 新增代码+DesktopGUILifecycle：函数段结束，_append_event 到此结束；如果没有边界说明，初学者不易看出它只负责事件写入。

    def _append_adapter_event(self, turn: GuiTurn, event: dict[str, object]) -> int:  # 新增代码+GuiAgentAdapter：函数段开始，把 V2 adapter event 写入统一 status store；如果没有这段，streaming delta 只停在 adapter 内部，GUI 收不到。
        event_type = str(event.get("kind", "heartbeat"))  # 新增代码+GuiAgentAdapter：把 V2 kind 作为 status event 类型；如果没有这一行，SSE fallback 无法按原始 kind 转发。
        raw_payload = event.get("payload", {})  # 新增代码+GuiAgentAdapter：读取 adapter 原始 payload；如果没有这一行，message_delta 的文本会丢失。
        safe_payload = raw_payload if isinstance(raw_payload, dict) else {}  # 新增代码+GuiAgentAdapter：防御非 dict payload；如果没有这一行，坏 adapter 事件会拖垮 bridge worker。
        event_payload = {"adapter_event_id": str(event.get("event_id", "")), "adapter_created_at": str(event.get("created_at", "")), **safe_payload}  # 新增代码+GuiAgentAdapter：保留 adapter 元信息并合并业务载荷；如果没有这一行，诊断时难以追踪事件来源。
        stored_event = self.event_store.append(event_type, event_payload, session_id=turn.session_id, run_id=turn.run_id, turn_id=turn.turn_id)  # 新增代码+GuiAgentAdapter：写入统一事实流；如果没有这一行，轮询和 SSE 都看不到 adapter 事件。
        return stored_event.sequence  # 新增代码+GuiAgentAdapter：返回落盘序号；如果没有这一行，后续调试无法知道 adapter event 的位置。
    # 新增代码+GuiAgentAdapter：函数段结束，_append_adapter_event 到此结束；如果没有边界说明，用户不容易看出 adapter 事件落盘范围。

    def _adapter_for_turn(self, turn: GuiTurn) -> GuiAgentAdapter:  # 新增代码+GuiAgentAdapter：函数段开始，选择本轮使用 fake adapter 还是真实 harness shell；如果没有这段，真实模式触发语义会散落在 worker 中。
        if "__real_harness__" in turn.prompt or "__harness_adapter__" in turn.prompt:  # 新增代码+GuiAgentAdapter：识别显式真实 harness 触发词；如果没有这一行，调用方无法稳定验证 adapter_unavailable 边界。
            return DefaultHarnessGuiAgentAdapter(enabled=False)  # 新增代码+GuiAgentAdapter：返回禁用的真实 harness shell；如果没有这一行，V2-Core 可能误导入真实 runtime。
        return self.agent_adapter  # 新增代码+GuiAgentAdapter：默认返回注入或内置 fake adapter；如果没有这一行，普通 GUI prompt 没有执行入口。
    # 新增代码+GuiAgentAdapter：函数段结束，_adapter_for_turn 到此结束；如果没有边界说明，用户不容易看出 adapter 选择规则。

    def _run_adapter_turn(self, turn: GuiTurn) -> GuiAgentRunResult:  # 新增代码+GuiAgentAdapter：函数段开始，把 GUI turn 转交给 adapter；如果没有这段，worker 只能调用旧 answer_runner。
        adapter = self._adapter_for_turn(turn)  # 新增代码+GuiAgentAdapter：选择本轮 adapter；如果没有这一行，fake/real 分支没有统一入口。
        request = GuiAgentRunRequest(session_id=turn.session_id, turn_id=turn.turn_id, run_id=turn.run_id, prompt=turn.prompt, mode="real" if isinstance(adapter, DefaultHarnessGuiAgentAdapter) else "fake")  # 新增代码+GuiAgentAdapter：构造 adapter 请求对象；如果没有这一行，adapter 收不到 session/turn/run/prompt 身份。
        cancel_event = self.cancel_events.setdefault(turn.turn_id, threading.Event())  # 新增代码+GuiAgentAdapter：读取或创建取消信号；如果没有这一行，adapter 无法响应 GUI cancel。
        def emit_event(event: dict[str, object]) -> None:  # 新增代码+GuiAgentAdapter：回调段开始，把 adapter 事件交给 bridge；如果没有这段，adapter 和 status store 无法连接。
            self._append_adapter_event(turn, event)  # 新增代码+GuiAgentAdapter：把单个 V2 事件写入事实流；如果没有这一行，message_delta 不会出现在 GUI 事件列表。
        # 新增代码+GuiAgentAdapter：回调段结束，emit_event 到此结束；如果没有边界说明，用户不容易看出事件写入范围。
        def is_cancelled() -> bool:  # 新增代码+GuiAgentAdapter：取消检查段开始，供 adapter 在流式输出中查询；如果没有这段，fake/real adapter 无法与取消按钮协作。
            return cancel_event.is_set()  # 新增代码+GuiAgentAdapter：返回当前取消信号；如果没有这一行，adapter 会继续完成已取消 turn。
        # 新增代码+GuiAgentAdapter：取消检查段结束，is_cancelled 到此结束；如果没有边界说明，用户不容易看出取消来源。
        return adapter.run(request, emit_event, is_cancelled)  # 新增代码+GuiAgentAdapter：调用 adapter 主入口；如果没有这一行，V2 adapter 边界不会被实际使用。
    # 新增代码+GuiAgentAdapter：函数段结束，_run_adapter_turn 到此结束；如果没有边界说明，用户不容易看出 adapter 调用范围。

    def _set_turn_status(self, turn: GuiTurn, status: str, answer: str = "", error: str = "") -> int:  # 新增代码+DesktopGUILifecycle：函数段开始，统一更新 turn 状态；如果没有这段，turn 和消息状态会不同步。
        turn.status = status  # 新增代码+DesktopGUILifecycle：更新 turn 状态；如果没有这行，后端状态不会变化。
        if answer:  # 新增代码+DesktopGUILifecycle：判断是否有最终回答；如果没有这行，空回答也会覆盖旧答案。
            turn.answer = answer  # 新增代码+DesktopGUILifecycle：保存最终回答；如果没有这行，resume 无法返回 answer。
        if error:  # 新增代码+DesktopGUILifecycle：判断是否有错误文本；如果没有这行，空错误会覆盖旧错误。
            turn.error = error  # 新增代码+DesktopGUILifecycle：保存失败原因；如果没有这行，failed UI 没有具体错误。
        session = self._session(turn.session_id)  # 新增代码+DesktopGUILifecycle：读取所属 session；如果没有这行，无法同步消息状态。
        self._touch_session(session)  # 新增代码+DesktopGUISessionSearch：状态变化时刷新会话更新时间；如果没有这行，完成或失败后的会话排序不会反映最近活动。
        for message in session.messages:  # 新增代码+DesktopGUILifecycle：遍历消息列表；如果没有这行，目标消息不会更新。
            if message.turn_id == turn.turn_id and message.role == "assistant":  # 新增代码+DesktopGUILifecycle：定位助手占位消息；如果没有这行，用户消息也可能被改状态。
                message.status = status  # 新增代码+DesktopGUILifecycle：同步消息状态；如果没有这行，前端消息卡不会显示终态。
                if answer:  # 新增代码+DesktopGUILifecycle：判断是否有回答；如果没有这行，空回答可能覆盖占位文案。
                    message.text = answer  # 新增代码+DesktopGUILifecycle：同步助手消息正文；如果没有这行，完成后仍显示等待后端响应。
                if error:  # 新增代码+DesktopGUILifecycle：判断是否有错误；如果没有这行，失败消息没有正文。
                    message.text = error  # 新增代码+DesktopGUILifecycle：把错误写入助手消息；如果没有这行，失败 UI 无法展示原因。
        event_type = {"running": "gui_turn_started", "completed": "gui_turn_completed", "failed": "gui_turn_failed", "cancelled": "gui_turn_cancelled", "needs_permission": "gui_turn_needs_permission"}.get(status, "gui_turn_status_changed")  # 新增代码+DesktopGUILifecycle：把状态映射到事件类型；如果没有这行，事件命名会不稳定。
        sequence = self._append_event(event_type, turn, {"answer": answer, "error": error})  # 新增代码+DesktopGUILifecycle：写入状态事件；如果没有这行，前端 watcher 看不到变化。
        self._save_state()  # 新增代码+DesktopGUILifecycle：状态变化后落盘；如果没有这行，窗口重启会丢失最新状态。
        return sequence  # 新增代码+DesktopGUILifecycle：返回事件序号；如果没有这行，调用方无法给出事件游标。
    # 新增代码+DesktopGUILifecycle：函数段结束，_set_turn_status 到此结束；如果没有边界说明，初学者不易看出状态同步范围。

    def _permission_payload(self, permission: GuiPermissionRequest) -> dict[str, Any]:  # 修改代码+DesktopGUIPermissionsV2：函数段开始，生成 V2 脱敏权限事件 payload；如果没有这段，请求和回答事件字段会不一致。
        return permission_payload_from_request(permission)  # 修改代码+DesktopGUIPermissionsV2：复用统一 payload helper；如果没有这行，tool_name、created_at 和脱敏规则会在 bridge 内重复漂移。
    # 新增代码+DesktopGUIPermissions：函数段结束，_permission_payload 到此结束；如果没有这个边界，初学者不易看出权限 payload 脱敏范围。

    def record_permission_required(self, request_id: str, turn_id: str = "", app_name: str = "", reason: str = "", risk_summary: str = "", tool_name: str = "") -> dict[str, Any]:  # 修改代码+DesktopGUIPermissionsV2：函数段开始，把后端权限请求登记为 GUI 可见请求；如果没有这段，权限事件无法变成桌面弹窗和 needs_permission 状态。
        clean_request_id = request_id.strip() or _new_id("perm")  # 新增代码+DesktopGUIPermissions：清理或生成 request id；如果没有这行，空 request_id 会导致前端无法回传决策。
        clean_turn_id = turn_id.strip()  # 新增代码+DesktopGUIPermissions：清理 turn id；如果没有这行，空格会导致 turn 匹配失败。
        with self.lock:  # 新增代码+DesktopGUIPermissions：保护权限请求登记；如果没有这行，并发权限事件可能重复写同一 request。
            turn = self.turns.get(clean_turn_id) if clean_turn_id else None  # 新增代码+DesktopGUIPermissions：读取关联 turn；如果没有这行，权限事件无法同步消息状态。
            permission_fields = normalize_permission_request_fields(request_id=clean_request_id, turn_id=clean_turn_id, run_id=turn.run_id if turn else "", session_id=turn.session_id if turn else "", tool_name=tool_name, app_name=app_name, reason=reason, risk_summary=risk_summary)  # 新增代码+DesktopGUIPermissionsV2：统一清洗 V2 权限字段；如果没有这行，路径脱敏、tool_name 和 created_at 会被漏掉。
            permission = GuiPermissionRequest(**permission_fields)  # 修改代码+DesktopGUIPermissionsV2：创建权限请求对象；如果没有这行，后续 decision endpoint 没有可查状态。
            self.permissions[clean_request_id] = permission  # 新增代码+DesktopGUIPermissions：保存权限请求；如果没有这行，approve/deny 会返回找不到请求。
            if turn is not None and turn.status not in GUI_TERMINAL_STATES:  # 新增代码+DesktopGUIPermissions：如果 turn 还没结束就同步为等待权限；如果没有这行，消息会继续显示 running。
                turn.status = "needs_permission"  # 新增代码+DesktopGUIPermissions：标记 turn 需要权限；如果没有这行，busy/status 逻辑不知道当前卡点。
                session = self._session(turn.session_id)  # 新增代码+DesktopGUIPermissions：读取所属 session；如果没有这行，无法同步助手消息状态。
                for message in session.messages:  # 新增代码+DesktopGUIPermissions：遍历 session 消息；如果没有这行，目标助手消息不会更新。
                    if message.turn_id == turn.turn_id and message.role == "assistant":  # 新增代码+DesktopGUIPermissions：定位助手占位消息；如果没有这行，用户消息可能被误改。
                        message.status = "needs_permission"  # 新增代码+DesktopGUIPermissions：同步消息状态；如果没有这行，前端消息卡不显示权限等待。
                        message.text = "等待用户在桌面 GUI 中确认权限请求。"  # 新增代码+DesktopGUIPermissions：给等待权限提供可读说明；如果没有这行，消息正文会空白。
            payload = self._permission_payload(permission)  # 新增代码+DesktopGUIPermissions：生成脱敏事件 payload；如果没有这行，后续事件字段会重复拼接。
            event = self.event_store.append("gui_turn_needs_permission", payload, session_id=permission.session_id, run_id=permission.run_id, turn_id=permission.turn_id)  # 新增代码+DesktopGUIPermissions：写入 GUI 权限等待事件；如果没有这行，前端 turn 状态不会进入 needs_permission。
            self.event_store.append("permission_required", payload, session_id=permission.session_id, run_id=permission.run_id, turn_id=permission.turn_id)  # 新增代码+DesktopGUIPermissions：写入通用权限请求事件；如果没有这行，PermissionDialog 的事件解析无法复用统一 permission_required。
            self._save_state()  # 新增代码+DesktopGUIPermissions：登记后落盘；如果没有这行，重启后会丢失 pending 权限请求。
            return {"ok": True, "request_id": permission.request_id, "turn_id": permission.turn_id, "status": permission.status, "events_after_sequence": max(0, event.sequence - 1)}  # 新增代码+DesktopGUIPermissions：返回登记响应；如果没有这行，测试和调用方拿不到 request 状态。
    # 新增代码+DesktopGUIPermissions：函数段结束，record_permission_required 到此结束；如果没有这个边界，初学者不易看出权限请求登记范围。

    def decide_permission(self, request_id: str, turn_id: str = "", decision: str = "", reason: str = "") -> dict[str, Any]:  # 修改代码+DesktopGUIPermissionsV2：函数段开始，处理 GUI 允许或拒绝意图；如果没有这段，POST /permissions/{id}/decision 没有业务实现。
        clean_request_id = request_id.strip()  # 新增代码+DesktopGUIPermissions：清理 request id；如果没有这行，路径里的空格会造成查找异常。
        try:  # 新增代码+DesktopGUIPermissionsV2：捕获非法决策别名；如果没有这行，helper 的 ValueError 会变成 500。
            clean_decision = normalize_permission_decision(decision)  # 修改代码+DesktopGUIPermissionsV2：标准化决策文本；如果没有这行，APPROVED/Rejected 等常见写法会被误拒。
        except ValueError:  # 新增代码+DesktopGUIPermissionsV2：处理不支持的决策文本；如果没有这行，前端拿不到结构化 bad_permission_decision。
            raise GuiBridgeError(400, "bad_permission_decision", "permission decision 只允许 approve 或 deny。")  # 新增代码+DesktopGUIPermissions：返回结构化决策错误；如果没有这行，调用方不知道合法值。
        with self.lock:  # 新增代码+DesktopGUIPermissions：保护权限决策写入；如果没有这行，并发点击可能同时通过重复检查。
            permission = self.permissions.get(clean_request_id)  # 新增代码+DesktopGUIPermissions：查找权限请求；如果没有这行，无法区分未知请求和已回答请求。
            if permission is None:  # 新增代码+DesktopGUIPermissions：处理未知 request_id；如果没有这行，后续访问会抛异常。
                raise GuiBridgeError(404, "permission_not_found", "未找到该权限请求。")  # 新增代码+DesktopGUIPermissions：返回结构化 404；如果没有这行，前端无法提示请求已失效。
            if permission.status != "pending":  # 新增代码+DesktopGUIPermissions：拒绝重复回答；如果没有这行，用户可多次改写审计结果。
                raise GuiBridgeError(409, "permission_already_answered", "该权限请求已经回答过。")  # 新增代码+DesktopGUIPermissions：返回结构化冲突；如果没有这行，重复点击没有清晰反馈。
            if turn_id and permission.turn_id and turn_id.strip() != permission.turn_id:  # 新增代码+DesktopGUIPermissions：校验 body 中 turn_id 是否匹配；如果没有这行，前端可能误把一个请求回答到另一轮。
                raise GuiBridgeError(400, "permission_turn_mismatch", "权限请求和 turn_id 不匹配。")  # 新增代码+DesktopGUIPermissions：返回结构化 turn mismatch；如果没有这行，排查错位决策很困难。
            permission.decision = clean_decision  # 新增代码+DesktopGUIPermissions：保存 approve/deny；如果没有这行，审计事件缺少用户选择。
            permission.status = "approved" if clean_decision == "approve" else "denied"  # 新增代码+DesktopGUIPermissions：保存最终权限状态；如果没有这行，重复回答检查无法生效。
            permission.decision_reason = redact_permission_text(reason)  # 修改代码+DesktopGUIPermissionsV2：保存脱敏回答原因；如果没有这行，GUI 决策理由可能把本机路径或凭证写入审计。
            permission.answered_at = time.time()  # 新增代码+DesktopGUIPermissions：记录回答时间；如果没有这行，延迟和超时排查缺少事实。
            turn = self.turns.get(permission.turn_id) if permission.turn_id else None  # 新增代码+DesktopGUIPermissions：读取关联 turn；如果没有这行，拒绝权限时无法让运行显式失败。
            if clean_decision == "deny" and turn is not None and turn.status not in GUI_TERMINAL_STATES:  # 新增代码+DesktopGUIPermissions：拒绝权限时终止等待中的 turn；如果没有这行，用户拒绝后任务会悬挂。
                self._set_turn_status(turn, "failed", error="用户在桌面 GUI 中拒绝了权限请求。")  # 新增代码+DesktopGUIPermissions：写入失败终态；如果没有这行，权限拒绝不会变成可见 failed 状态。
                self.active_turn_id = None  # 新增代码+DesktopGUIPermissions：释放 active turn；如果没有这行，拒绝权限后新 prompt 仍会被 busy 阻塞。
            payload = self._permission_payload(permission)  # 修改代码+DesktopGUIPermissionsV2：生成权限回答审计 payload；如果没有这行，事件缺少 approve 布尔值、理由和 V2 审计字段。
            event = self.event_store.append("permission_answered", payload, session_id=permission.session_id, run_id=permission.run_id, turn_id=permission.turn_id)  # 新增代码+DesktopGUIPermissions：写入统一权限回答事件；如果没有这行，状态时间线无法展示允许或拒绝。
            self._save_state()  # 新增代码+DesktopGUIPermissions：回答后落盘；如果没有这行，重复回答检查在重启后会失效。
            return {"ok": True, "request_id": permission.request_id, "turn_id": permission.turn_id, "decision": permission.decision, "status": permission.status, "events_after_sequence": max(0, event.sequence - 1)}  # 新增代码+DesktopGUIPermissions：返回决策响应；如果没有这行，前端无法清楚更新弹窗。
    # 新增代码+DesktopGUIPermissions：函数段结束，decide_permission 到此结束；如果没有这个边界，初学者不易看出权限回答范围。

    def _assert_not_busy(self) -> None:  # 新增代码+DesktopGUILifecycle：函数段开始，检查是否已有 active turn；如果没有这段，多个 turn 可能并发运行。
        if self.active_turn_id and self.turns.get(self.active_turn_id, GuiTurn("", "", "", "")).status in GUI_RUNNING_STATES:  # 新增代码+DesktopGUILifecycle：判断当前 turn 是否仍运行；如果没有这行，busy 保护会失效。
            raise GuiBridgeError(409, "agent_busy", "当前已有 GUI turn 正在运行，请等待完成或先取消。")  # 新增代码+DesktopGUILifecycle：抛出结构化 busy 错误；如果没有这行，前端无法清楚提示用户。
    # 新增代码+DesktopGUILifecycle：函数段结束，_assert_not_busy 到此结束；如果没有边界说明，初学者不易看出它只负责 busy 保护。

    def start_message(self, conversation_id: str, prompt: str, client_request_id: str = "", retry_of: str = "") -> dict[str, Any]:  # 新增代码+DesktopGUILifecycle：函数段开始，提交 GUI prompt；如果没有这段，POST /messages 无法创建 turn。
        clean_prompt = prompt.strip()  # 新增代码+DesktopGUILifecycle：清理 prompt 前后空白；如果没有这行，空白任务可能进入运行。
        if not clean_prompt:  # 新增代码+DesktopGUILifecycle：拒绝空 prompt；如果没有这行，后端会产生无意义 turn。
            raise GuiBridgeError(400, "missing_prompt", "缺少 prompt 字段。")  # 新增代码+DesktopGUILifecycle：返回结构化缺参错误；如果没有这行，前端无法定位输入问题。
        session_id = conversation_id.strip() or "default"  # 新增代码+DesktopGUILifecycle：规范化 session id；如果没有这行，空 conversation 会造成无名 session。
        with self.lock:  # 新增代码+DesktopGUILifecycle：保护 turn 创建；如果没有这行，并发请求可能绕过 busy 检查。
            self._assert_not_busy()  # 新增代码+DesktopGUILifecycle：执行单 active turn 门禁；如果没有这行，多个后台 worker 会同时写状态。
            turn = GuiTurn(turn_id=_new_id("turn"), run_id=_new_id("run"), session_id=session_id, prompt=clean_prompt, retry_of=retry_of, client_request_id=client_request_id)  # 新增代码+DesktopGUILifecycle：创建新 turn；如果没有这行，生命周期没有主体。
            session = self._session(session_id)  # 新增代码+DesktopGUILifecycle：获取目标 session；如果没有这行，消息无法保存。
            session.messages.append(GuiMessage(id=_new_id("msg"), role="user", text=clean_prompt, turn_id=turn.turn_id, status="completed"))  # 新增代码+DesktopGUILifecycle：记录用户消息；如果没有这行，resume 看不到用户 prompt。
            session.messages.append(GuiMessage(id=_new_id("msg"), role="assistant", text="", turn_id=turn.turn_id, status="queued"))  # 新增代码+DesktopGUILifecycle：记录助手占位消息；如果没有这行，GUI 无法立即显示运行中占位。
            session.last_turn_id = turn.turn_id  # 新增代码+DesktopGUILifecycle：更新 session 最近 turn；如果没有这行，恢复后不知道最新轮次。
            self._touch_session(session)  # 新增代码+DesktopGUISessionSearch：提交 prompt 后刷新会话更新时间；如果没有这行，新消息不会把会话推到最近列表顶部。
            self.turns[turn.turn_id] = turn  # 新增代码+DesktopGUILifecycle：保存 turn；如果没有这行，cancel/retry 找不到它。
            self.cancel_events[turn.turn_id] = threading.Event()  # 新增代码+DesktopGUILifecycle：创建取消信号；如果没有这行，worker 无法被取消。
            self.active_turn_id = turn.turn_id  # 新增代码+DesktopGUILifecycle：设置 active turn；如果没有这行，busy 检查不会生效。
            queued_sequence = self._append_event("gui_turn_queued", turn, {"prompt": clean_prompt, "client_request_id": client_request_id})  # 新增代码+DesktopGUILifecycle：写入 queued 事件；如果没有这行，时间线缺少起点。
            self._save_state()  # 新增代码+DesktopGUILifecycle：创建后立即落盘；如果没有这行，启动后立刻关闭会丢消息。
            worker = threading.Thread(target=self._run_turn_worker, args=(turn.turn_id,), daemon=True)  # 新增代码+DesktopGUILifecycle：创建后台 worker；如果没有这行，POST /messages 会阻塞到完成。
            worker.start()  # 新增代码+DesktopGUILifecycle：启动后台 worker；如果没有这行，turn 会永远停在 queued。
        return {"ok": True, "conversation_id": session_id, "turn_id": turn.turn_id, "run_id": turn.run_id, "status": "queued", "answer": "", "events_after_sequence": max(0, queued_sequence - 1)}  # 新增代码+DesktopGUILifecycle：返回提交响应；如果没有这行，前端拿不到 turn/run id。
    # 新增代码+DesktopGUILifecycle：函数段结束，start_message 到此结束；如果没有边界说明，初学者不易看出提交流程范围。

    def _run_turn_worker(self, turn_id: str) -> None:  # 新增代码+DesktopGUILifecycle：函数段开始，后台推进 turn；如果没有这段，queued 无法进入 running/completed。
        with self.lock:  # 新增代码+DesktopGUILifecycle：锁住状态读取和 running 事件；如果没有这行，cancel 可能和 started 状态交错写坏。
            turn = self.turns.get(turn_id)  # 新增代码+DesktopGUILifecycle：读取目标 turn；如果没有这行，worker 没有运行对象。
            if turn is None:  # 新增代码+DesktopGUILifecycle：处理 turn 已不存在；如果没有这行，异常会杀掉线程。
                return  # 新增代码+DesktopGUILifecycle：目标缺失时退出；如果没有这行，后续访问会报错。
            self._set_turn_status(turn, "running")  # 新增代码+DesktopGUILifecycle：进入 running 状态；如果没有这行，GUI 看不到真正开始。
        if "__permission__" in turn.prompt:  # 新增代码+DesktopGUIPermissionSmoke：识别 GUI 权限验收触发词；如果没有这行代码，Electron 界面无法从普通 prompt 稳定触发权限弹窗。
            self.record_permission_required(_new_id("perm"), turn_id=turn.turn_id, app_name="OpenHarness Desktop Smoke", reason="GUI 可见验收需要确认一个模拟权限请求。", risk_summary="这是桌面 GUI smoke 专用的低风险模拟权限。")  # 新增代码+DesktopGUIPermissionSmoke：登记真实 bridge 权限请求；如果没有这行代码，前端只能靠假数据渲染 PermissionDialog。
        if "__tool__" in turn.prompt:  # 新增代码+DesktopGUIToolSmoke：识别 GUI 工具卡片验收触发词；如果没有这行代码，主线程很难稳定出现可见 ToolCallCard。
            self._append_event("tool_call_started", turn, {"tool_name": "smoke_tool", "summary": "GUI 可见验收工具事件已写入。", "status": "running"})  # 新增代码+DesktopGUIToolSmoke：写入带 tool_name 的工具事件；如果没有这行代码，线程区只能看到普通消息而没有工具卡片。
            self._save_state()  # 新增代码+DesktopGUIToolSmoke：工具事件写入后立即落盘；如果没有这行代码，窗口刷新或重启时可能看不到该工具事件。
        wait_cycles = 100 if "__permission_fast__" in turn.prompt else 750 if "__slow__" in turn.prompt or "__permission__" in turn.prompt else 10  # 修改代码+DesktopGUIPermissionSmoke：单元测试保留约 2 秒给权限决策，真实 GUI smoke 保留约 15 秒可点击窗口；如果没有这行代码，权限合同测试会抢时序或可见验收来不及点击。
        for _index in range(wait_cycles):  # 修改代码+DesktopGUISmokeHarness：按普通或慢速轮次给 cancel 留出可见窗口；如果没有这行，turn 可能太快完成而无法取消。
            time.sleep(0.02)  # 新增代码+DesktopGUILifecycle：短暂模拟后端处理；如果没有这行，后台 worker 会立即完成。
            if self.cancel_events.get(turn_id, threading.Event()).is_set():  # 新增代码+DesktopGUILifecycle：检查取消信号；如果没有这行，cancel endpoint 不会影响 worker。
                with self.lock:  # 新增代码+DesktopGUILifecycle：锁住取消终态写入；如果没有这行，完成和取消可能并发落盘。
                    turn = self.turns[turn_id]  # 新增代码+DesktopGUILifecycle：重新读取 turn；如果没有这行，状态可能是旧对象。
                    self._set_turn_status(turn, "cancelled", error="用户已在桌面 GUI 中取消本轮运行。")  # 新增代码+DesktopGUILifecycle：写入取消终态；如果没有这行，GUI 会一直显示 cancelling。
                    self.active_turn_id = None  # 新增代码+DesktopGUILifecycle：释放 active turn；如果没有这行，后续 prompt 会一直 busy。
                    self._save_state()  # 新增代码+DesktopGUILifecycle：释放后落盘；如果没有这行，重启后状态不一致。
                return  # 新增代码+DesktopGUILifecycle：取消后退出 worker；如果没有这行，后续可能继续写 completed。
        with self.lock:  # 新增代码+DesktopGUILifecycle：锁住最终状态写入；如果没有这行，cancel 和 completed 可能同时发生。
            turn = self.turns[turn_id]  # 新增代码+DesktopGUILifecycle：读取最终 turn；如果没有这行，无法调用 runner。
            if turn.status in GUI_TERMINAL_STATES:  # 新增代码+DesktopGUIPermissionSmoke：如果权限拒绝或取消已产生终态就停止覆盖；如果没有这行代码，worker 可能把 failed/cancelled 又改成 completed。
                self._save_state()  # 新增代码+DesktopGUIPermissionSmoke：保持已有终态落盘；如果没有这行代码，重启恢复可能看不到拒绝后的最终状态。
                return  # 新增代码+DesktopGUIPermissionSmoke：已有终态时退出 worker；如果没有这行代码，后续 answer_runner 仍会继续执行并污染状态。
            try:  # 新增代码+DesktopGUILifecycle：捕获 runner 失败；如果没有这行，后台线程异常不会变成 GUI 事件。
                if self.answer_runner_override is not None:  # 新增代码+GuiAgentAdapter：显式注入 runner 时保留 V1 兼容路径；如果没有这一行，旧测试和外部自定义 runner 会被强行改走 fake adapter。
                    if "__fail__" in turn.prompt:  # 修改代码+GuiAgentAdapter：V1 兼容路径仍保留失败触发器；如果没有这行，旧失败合同无法稳定覆盖。
                        raise RuntimeError("测试触发的 GUI turn 失败。")  # 修改代码+GuiAgentAdapter：抛出可控失败；如果没有这行，失败路径无法覆盖。
                    answer = self.answer_runner(turn.prompt, turn.session_id, turn.turn_id)  # 修改代码+GuiAgentAdapter：调用显式注入的回答 runner；如果没有这行，兼容路径没有最终回答。
                    self._set_turn_status(turn, "completed", answer=answer)  # 修改代码+GuiAgentAdapter：写入 V1 runner 完成终态；如果没有这行，GUI 无法展示兼容路径答案。
                else:  # 新增代码+GuiAgentAdapter：默认路径走 V2 adapter；如果没有这一行，普通 GUI prompt 仍不会产生 message_delta。
                    adapter_result = self._run_adapter_turn(turn)  # 新增代码+GuiAgentAdapter：执行 fake 或真实 harness shell adapter；如果没有这一行，V2 adapter 边界不会被使用。
                    if adapter_result.status == "completed":  # 新增代码+GuiAgentAdapter：处理 adapter 完成结果；如果没有这一行，完成态会被误当失败。
                        self._set_turn_status(turn, "completed", answer=adapter_result.final_text)  # 新增代码+GuiAgentAdapter：把 adapter final_text 写回助手消息；如果没有这一行，resume 看不到最终回答。
                    elif adapter_result.status == "cancelled":  # 新增代码+GuiAgentAdapter：处理 adapter 取消结果；如果没有这一行，取消会被误当失败。
                        self._set_turn_status(turn, "cancelled", error=adapter_result.error_message or "用户已在桌面 GUI 中取消本轮运行。")  # 新增代码+GuiAgentAdapter：写入取消终态；如果没有这一行，前端会停在 running。
                    else:  # 新增代码+GuiAgentAdapter：处理 adapter failed/unavailable 等其它终态；如果没有这一行，失败结果没有稳定兜底。
                        self._set_turn_status(turn, "failed", error=adapter_result.error_message or adapter_result.error_code or "GUI adapter 运行失败。")  # 新增代码+GuiAgentAdapter：写入 adapter 失败终态；如果没有这一行，真实 adapter 未启用会静默失败。
            except Exception as error:  # 新增代码+DesktopGUILifecycle：处理 runner 异常；如果没有这行，失败不会变成结构化事件。
                self._set_turn_status(turn, "failed", error=f"GUI turn 运行失败：{error}")  # 新增代码+DesktopGUILifecycle：写入失败终态；如果没有这行，前端只能看到线程静默结束。
            finally:  # 新增代码+DesktopGUILifecycle：无论成功失败都释放 active；如果没有这行，失败后会永久 busy。
                self.active_turn_id = None  # 新增代码+DesktopGUILifecycle：释放 active turn；如果没有这行，后续 prompt 无法提交。
                self._save_state()  # 新增代码+DesktopGUILifecycle：最终状态落盘；如果没有这行，resume 看不到终态。
    # 新增代码+DesktopGUILifecycle：函数段结束，_run_turn_worker 到此结束；如果没有边界说明，初学者不易看出后台推进范围。

    def cancel_turn(self, turn_id: str) -> dict[str, Any]:  # 新增代码+DesktopGUILifecycle：函数段开始，请求取消 turn；如果没有这段，POST /cancel 无法工作。
        with self.lock:  # 新增代码+DesktopGUILifecycle：保护取消状态写入；如果没有这行，cancel 可能和 worker 并发冲突。
            turn = self.turns.get(turn_id)  # 新增代码+DesktopGUILifecycle：查找目标 turn；如果没有这行，无法判断 turn 是否存在。
            if turn is None:  # 新增代码+DesktopGUILifecycle：处理未知 turn；如果没有这行，后续访问会报错。
                raise GuiBridgeError(404, "turn_not_found", "未找到要取消的 GUI turn。")  # 新增代码+DesktopGUILifecycle：返回结构化 404；如果没有这行，前端无法区分找不到和失败。
            if turn.status in GUI_TERMINAL_STATES:  # 新增代码+DesktopGUILifecycle：拒绝取消终态 turn；如果没有这行，已完成 turn 会被误改。
                raise GuiBridgeError(409, "turn_already_terminal", "该 GUI turn 已经结束，不能取消。")  # 新增代码+DesktopGUILifecycle：返回结构化冲突；如果没有这行，用户会误以为取消成功。
            turn.status = "cancelling"  # 新增代码+DesktopGUILifecycle：记录正在取消；如果没有这行，按钮状态不会及时变化。
            self.cancel_events.setdefault(turn_id, threading.Event()).set()  # 新增代码+DesktopGUILifecycle：通知 worker 取消；如果没有这行，后台仍会完成。
            sequence = self._append_event("gui_turn_cancel_requested", turn, {})  # 新增代码+DesktopGUILifecycle：写入取消请求事件；如果没有这行，时间线看不到用户动作。
            self._save_state()  # 新增代码+DesktopGUILifecycle：取消请求落盘；如果没有这行，重启后状态可能不一致。
            return {"ok": True, "turn_id": turn.turn_id, "run_id": turn.run_id, "status": "cancelling", "events_after_sequence": max(0, sequence - 1)}  # 新增代码+DesktopGUILifecycle：返回取消响应；如果没有这行，前端无法更新按钮状态。
    # 新增代码+DesktopGUILifecycle：函数段结束，cancel_turn 到此结束；如果没有边界说明，初学者不易看出取消范围。

    def retry_turn(self, turn_id: str) -> dict[str, Any]:  # 新增代码+DesktopGUILifecycle：函数段开始，重试指定 turn；如果没有这段，POST /retry 无法工作。
        with self.lock:  # 新增代码+DesktopGUILifecycle：保护 retry 和 busy 检查；如果没有这行，并发 retry 可能创建多个 turn。
            old_turn = self.turns.get(turn_id)  # 新增代码+DesktopGUILifecycle：读取旧 turn；如果没有这行，无法复用 prompt。
            if old_turn is None:  # 新增代码+DesktopGUILifecycle：处理未知 turn；如果没有这行，后续访问会报错。
                raise GuiBridgeError(404, "turn_not_found", "未找到要重试的 GUI turn。")  # 新增代码+DesktopGUILifecycle：返回结构化 404；如果没有这行，前端无法提示目标不存在。
            if old_turn.status not in GUI_TERMINAL_STATES:  # 新增代码+DesktopGUILifecycle：只允许重试终态 turn；如果没有这行，运行中 turn 会被重复执行。
                raise GuiBridgeError(409, "turn_not_terminal", "该 GUI turn 尚未结束，不能重试。")  # 新增代码+DesktopGUILifecycle：返回结构化冲突；如果没有这行，前端无法解释为何不能重试。
            self._assert_not_busy()  # 新增代码+DesktopGUILifecycle：确保当前没有 active turn；如果没有这行，retry 会绕过单 agent lock。
        response = self.start_message(old_turn.session_id, old_turn.prompt, client_request_id="", retry_of=old_turn.turn_id)  # 新增代码+DesktopGUILifecycle：用旧 prompt 创建新 turn；如果没有这行，retry 没有新生命周期。
        new_turn = self.turns[str(response["turn_id"])]  # 新增代码+DesktopGUILifecycle：读取新 turn；如果没有这行，无法写 retry 事件。
        sequence = self._append_event("gui_turn_retried", new_turn, {"retry_of": old_turn.turn_id})  # 新增代码+DesktopGUILifecycle：写入 retry 事件；如果没有这行，时间线无法解释新 turn 来源。
        response["events_after_sequence"] = max(0, sequence - 1)  # 新增代码+DesktopGUILifecycle：让前端从 retry 事件前轮询；如果没有这行，前端可能错过 retry 事件。
        return response  # 新增代码+DesktopGUILifecycle：返回 retry 的新 turn 响应；如果没有这行，前端拿不到新 turn id。
    # 新增代码+DesktopGUILifecycle：函数段结束，retry_turn 到此结束；如果没有边界说明，初学者不易看出重试范围。

    def resume_session(self, session_id: str) -> dict[str, Any]:  # 新增代码+DesktopGUILifecycle：函数段开始，恢复指定 session；如果没有这段，POST /resume 无法工作。
        with self.lock:  # 新增代码+DesktopGUILifecycle：保护 session 读取和事件写入；如果没有这行，恢复时消息可能被并发修改。
            session = self._session(session_id.strip() or "default")  # 新增代码+DesktopGUILifecycle：获取或创建 session；如果没有这行，空 session id 会报错。
            latest_turn = self.turns.get(session.last_turn_id) if session.last_turn_id else None  # 新增代码+DesktopGUILifecycle：读取最近 turn；如果没有这行，resume 事件无法关联 turn。
            if latest_turn is not None:  # 新增代码+DesktopGUILifecycle：只有存在 turn 时写关联事件；如果没有这行，空 session 会写无意义 turn。
                sequence = self._append_event("gui_turn_resumed", latest_turn, {"message_count": len(session.messages)})  # 新增代码+DesktopGUILifecycle：写入 resumed 事件；如果没有这行，窗口重启恢复不可审计。
            else:  # 新增代码+DesktopGUILifecycle：处理空 session；如果没有这行，sequence 变量可能未定义。
                sequence = _latest_sequence(self.workspace)  # 新增代码+DesktopGUILifecycle：空 session 使用当前游标；如果没有这行，响应缺少事件位置。
            self._save_state()  # 新增代码+DesktopGUILifecycle：恢复访问后保存状态；如果没有这行，空 session 创建不会落盘。
            return {"ok": True, "session_id": session.session_id, "messages": [asdict(message) for message in session.messages], "events_after_sequence": sequence}  # 新增代码+DesktopGUILifecycle：返回恢复 payload；如果没有这行，前端无法恢复消息。
    # 新增代码+DesktopGUILifecycle：函数段结束，resume_session 到此结束；如果没有边界说明，初学者不易看出恢复范围。


class DesktopGuiBridgeServer(http.server.ThreadingHTTPServer):  # 修改代码+DesktopGUIBridge：类段开始，保存 GUI bridge 共享状态；如果没有这个类，handler 无法访问 workspace/token/manager。
    def __init__(self, server_address: tuple[str, int], workspace: str | Path, token: str = "", answer_runner: GuiAnswerRunner | None = None, agent_adapter: GuiAgentAdapter | None = None) -> None:  # 修改代码+GuiAgentAdapter：初始化 server 并允许注入 V2 adapter；如果没有这个参数，测试和未来真实 harness 接线无法替换默认 fake adapter。
        super().__init__(server_address, DesktopGuiBridgeHandler)  # 修改代码+DesktopGUIBridge：绑定 handler；如果没有这行，server 不会处理 GUI 路由。
        self.workspace = Path(workspace).expanduser().resolve()  # 修改代码+DesktopGUIBridge：保存规范化工作区；如果没有这行，所有端点都不知道项目位置。
        self.token = str(token or secrets.token_hex(32))  # 修改代码+DesktopGUIBridge：保存或生成启动 token；如果没有这行，本地 bridge 默认没有认证保护。
        self.started_at = time.time()  # ????+GuiDiagnostics??? bridge ??????????????V2 health ?????? uptime?
        self.run_manager = GuiRunManager(self.workspace, answer_runner=answer_runner, agent_adapter=agent_adapter)  # 修改代码+GuiAgentAdapter：创建已接入 adapter 的生命周期 manager；如果没有这行，HTTP 层无法使用 V2 streaming adapter。
    # 修改代码+DesktopGUIBridge：初始化段结束，DesktopGuiBridgeServer.__init__ 到此结束；如果没有边界说明，初学者不易看出 server 共享状态范围。


class DesktopGuiBridgeHandler(http.server.BaseHTTPRequestHandler):  # 修改代码+DesktopGUIBridge：类段开始，处理 GUI bridge HTTP 请求；如果没有这个类，Electron 前端没有后端入口。
    server: DesktopGuiBridgeServer  # 修改代码+DesktopGUIBridge：标注 server 类型；如果没有这行，编辑器看不懂 workspace/token/run_manager 字段。

    def log_message(self, format: str, *args: Any) -> None:  # 修改代码+DesktopGUIBridge：关闭标准库访问日志；如果没有这段，轮询请求会刷屏。
        return  # 修改代码+DesktopGUIBridge：明确静默日志；如果没有这行，函数没有行为。
    # 修改代码+DesktopGUIBridge：函数段结束，log_message 到此结束；如果没有边界说明，初学者不易看出它只负责降噪。

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:  # 修改代码+DesktopGUIBridge：函数段开始，统一返回 JSON；如果没有这段，每个端点会重复 header 逻辑。
        raw_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")  # 修改代码+DesktopGUIBridge：编码 UTF-8 JSON；如果没有这行，中文状态会乱码。
        self.send_response(status)  # 修改代码+DesktopGUIBridge：写 HTTP 状态码；如果没有这行，前端无法判断成功失败。
        self.send_header("Content-Type", "application/json; charset=utf-8")  # 修改代码+DesktopGUIBridge：声明 JSON 类型；如果没有这行，前端可能按文本处理。
        self.send_header("Content-Length", str(len(raw_body)))  # 修改代码+DesktopGUIBridge：声明响应长度；如果没有这行，客户端可能等待连接关闭。
        self.send_header("Cache-Control", "no-store")  # 修改代码+DesktopGUIBridge：禁止缓存状态响应；如果没有这行，GUI 可能显示旧状态。
        self._send_cors_headers()  # 新增代码+DesktopGUICors：给允许来源补上 CORS 响应头；如果没有这行，真实浏览器会把成功响应当成 fetch 失败。
        self.end_headers()  # 修改代码+DesktopGUIBridge：结束响应头；如果没有这行，响应体不会正确发送。
        self.wfile.write(raw_body)  # 修改代码+DesktopGUIBridge：写出响应体；如果没有这行，前端收不到数据。
    # 修改代码+DesktopGUIBridge：函数段结束，_send_json 到此结束；如果没有边界说明，初学者不易看出它只负责响应封装。

    def _send_sse_events(self, events: list[dict[str, object]]) -> None:  # 新增代码+GuiV2Stream：函数段开始，统一返回 V2 SSE 事件；如果没有这段，stream 路由会重复 header 和编码逻辑。
        raw_body = b"".join(format_sse_event(event) for event in events)  # 新增代码+GuiV2Stream：把事件列表编码为 SSE 字节流；如果没有这一行，EventSource 收不到任何帧。
        self.send_response(200)  # 新增代码+GuiV2Stream：SSE 路由成功返回 200；如果没有这一行，客户端无法识别连接成功。
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")  # 新增代码+GuiV2Stream：声明事件流类型；如果没有这一行，浏览器不会按 SSE 解析。
        self.send_header("Content-Length", str(len(raw_body)))  # 新增代码+GuiV2Stream：声明本次响应长度；如果没有这一行，urllib 测试会等待连接持续不结束。
        self.send_header("Cache-Control", "no-store")  # 新增代码+GuiV2Stream：禁止缓存事件流；如果没有这一行，重连可能看到旧事件。
        self.send_header("Connection", "close")  # 新增代码+GuiV2Stream：当前 V2-Core 返回一批事件后关闭；如果没有这一行，fallback 和测试可能一直等待。
        self._send_cors_headers()  # 新增代码+GuiV2Stream：给允许来源补 CORS 头；如果没有这一行，dev renderer 不能读取 stream 响应。
        self.end_headers()  # 新增代码+GuiV2Stream：结束响应头；如果没有这一行，响应体不会正确发送。
        self.wfile.write(raw_body)  # 新增代码+GuiV2Stream：写出 SSE 字节流；如果没有这一行，前端没有事件可读。
    # 新增代码+GuiV2Stream：函数段结束，_send_sse_events 到此结束；如果没有边界说明，初学者不易看出它只负责 SSE 响应封装。

    def _send_cors_headers(self) -> None:  # 新增代码+DesktopGUICors：函数段开始，只为允许来源写入浏览器跨源响应头；如果没有这段，前端 dev server 无法调用本地 bridge。
        origin = self.headers.get("Origin", "")  # 新增代码+DesktopGUICors：读取浏览器来源；如果没有这行，后端不知道应该回写哪个 Access-Control-Allow-Origin。
        if not origin:  # 新增代码+DesktopGUICors：无来源请求通常来自 curl/urllib/Electron 内部；如果没有这行，普通本机请求会被多余 CORS 逻辑干扰。
            return  # 新增代码+DesktopGUICors：无来源时不写跨源头；如果没有这行，后续会尝试回写空来源造成语义混乱。
        if origin not in GUI_ALLOWED_ORIGINS:  # 新增代码+DesktopGUICors：只给白名单来源 CORS 权限；如果没有这行，恶意本机网页可能借浏览器读取 bridge。
            return  # 新增代码+DesktopGUICors：非法来源不写 CORS 头；如果没有这行，浏览器可能把拒绝响应暴露给不可信页面。
        self.send_header("Access-Control-Allow-Origin", origin)  # 新增代码+DesktopGUICors：回写精确来源而不是通配符；如果没有这行，浏览器不会把响应交给 GUI。
        self.send_header("Vary", "Origin")  # 新增代码+DesktopGUICors：声明响应会随 Origin 变化；如果没有这行，中间缓存可能复用错误来源响应。
        self.send_header("Access-Control-Allow-Headers", GUI_CORS_ALLOWED_HEADERS)  # 新增代码+DesktopGUICors：允许 token 和 JSON header；如果没有这行，POST 预检会失败。
        self.send_header("Access-Control-Allow-Methods", GUI_CORS_ALLOWED_METHODS)  # 新增代码+DesktopGUICors：允许 GUI 使用的 HTTP 方法；如果没有这行，OPTIONS 预检不会批准 POST。
    # 新增代码+DesktopGUICors：函数段结束，_send_cors_headers 到此结束；如果没有边界说明，初学者不易看出它只负责 CORS 响应头。

    def _send_error(self, status: int, code: str, message: str) -> None:  # 修改代码+DesktopGUIBridge：函数段开始，统一返回结构化错误；如果没有这段，前端要解析不同形状失败。
        self._send_json(status, make_error_response(code, message))  # 修改代码+GuiV2Protocol：返回 V2 结构化错误并保留 V1 error 别名；如果没有这行，前端会丢失 code/message/request_id 合同。
    # 修改代码+DesktopGUIBridge：函数段结束，_send_error 到此结束；如果没有边界说明，初学者不易看出它只负责错误封装。

    def _origin_allowed(self) -> bool:  # 修改代码+DesktopGUIBridge：函数段开始，检查浏览器来源；如果没有这段，本机恶意网页可能跨源访问 bridge。
        origin = self.headers.get("Origin", "")  # 修改代码+DesktopGUIBridge：读取 Origin header；如果没有这行，无法判断请求来源。
        return origin in GUI_ALLOWED_ORIGINS  # 修改代码+DesktopGUIBridge：只允许 file/null/dev server/无来源；如果没有这行，任意来源都能调用。
    # 修改代码+DesktopGUIBridge：函数段结束，_origin_allowed 到此结束；如果没有边界说明，初学者不易看出它只负责来源检查。

    def _authorized(self) -> bool:  # 修改代码+DesktopGUIBridge：函数段开始，检查 GUI bridge token；如果没有这段，本机其他进程可直接读状态。
        header_token = self.headers.get(GUI_TOKEN_HEADER, "")  # 修改代码+GuiV2Stream：先读取 header token；如果没有这一行，普通 fetch 请求无法认证。
        if header_token == self.server.token:  # 修改代码+GuiV2Stream：header token 匹配时直接放行；如果没有这一行，V1 和 V2 long polling 会被拒绝。
            return True  # 修改代码+GuiV2Stream：返回认证成功；如果没有这一行，合法 header 请求仍会失败。
        parsed_url = urllib.parse.urlparse(self.path)  # 新增代码+GuiV2Stream：解析当前请求路径；如果没有这一行，无法只给 EventSource route 开 query token。
        if parsed_url.path == "/v2/gui/events/stream":  # 新增代码+GuiV2Stream：只允许 V2 SSE route 使用 query token；如果没有这一行，所有路由都会暴露 URL token 入口。
            query = urllib.parse.parse_qs(parsed_url.query)  # 新增代码+GuiV2Stream：解析 stream query；如果没有这一行，无法读取 EventSource token 参数。
            return query.get("token", [""])[0] == self.server.token  # 新增代码+GuiV2Stream：比对 query token；如果没有这一行，EventSource 无法通过认证。
        return False  # 修改代码+GuiV2Stream：其它请求认证失败；如果没有这一行，缺 token 的请求可能误过。
    # 修改代码+DesktopGUIBridge：函数段结束，_authorized 到此结束；如果没有边界说明，初学者不易看出它只负责 token 校验。

    def _guard_request(self, require_token: bool) -> bool:  # 修改代码+DesktopGUIBridge：函数段开始，统一执行 Origin 和 token 门禁；如果没有这段，每个端点会重复安全判断。
        if not self._origin_allowed():  # 修改代码+DesktopGUIBridge：先检查来源；如果没有这行，错误 token 前可能接受恶意来源。
            self._send_error(403, "origin_forbidden", "请求来源不允许访问 Desktop GUI bridge。")  # 修改代码+DesktopGUIBridge：返回来源拒绝；如果没有这行，前端无法解释失败。
            return False  # 修改代码+DesktopGUIBridge：阻止后续处理；如果没有这行，被拒来源仍可能继续执行。
        if require_token and not self._authorized():  # 修改代码+DesktopGUIBridge：检查需要 token 的端点；如果没有这行，bootstrap/events/messages 会被未授权读取。
            self._send_error(401, "unauthorized", f"未授权：请提供 {GUI_TOKEN_HEADER}。")  # 修改代码+DesktopGUIBridge：返回认证拒绝；如果没有这行，客户端不知道要补哪个 header。
            return False  # 修改代码+DesktopGUIBridge：阻止后续处理；如果没有这行，未授权请求仍可能继续执行。
        return True  # 修改代码+DesktopGUIBridge：安全检查通过；如果没有这行，合法请求也无法继续。
    # 修改代码+DesktopGUIBridge：函数段结束，_guard_request 到此结束；如果没有边界说明，初学者不易看出它只负责统一门禁。

    def do_OPTIONS(self) -> None:  # 新增代码+DesktopGUICors：函数段开始，处理浏览器 CORS 预检；如果没有这段，带 token 的 GUI POST 不会真正发到后端。
        if not self._origin_allowed():  # 新增代码+DesktopGUICors：预检同样检查来源白名单；如果没有这行，任意网页都能探测 bridge CORS 能力。
            self._send_error(403, "origin_forbidden", "请求来源不允许访问 Desktop GUI bridge。")  # 新增代码+DesktopGUICors：返回来源拒绝；如果没有这行，非法来源预检会得到模糊失败。
            return  # 新增代码+DesktopGUICors：拒绝后停止处理；如果没有这行，非法来源仍可能收到允许头。
        self.send_response(204)  # 新增代码+DesktopGUICors：预检成功但不需要响应体；如果没有这行，浏览器无法确认预检通过。
        self.send_header("Content-Length", "0")  # 新增代码+DesktopGUICors：声明空响应体长度；如果没有这行，客户端可能等待不存在的 body。
        self.send_header("Cache-Control", "no-store")  # 新增代码+DesktopGUICors：禁止缓存预检响应；如果没有这行，调试 token/origin 时可能看到旧行为。
        self._send_cors_headers()  # 新增代码+DesktopGUICors：写入允许来源、请求头和方法；如果没有这行，浏览器仍会判定预检失败。
        self.end_headers()  # 新增代码+DesktopGUICors：结束预检响应头；如果没有这行，204 响应不会发送完成。
    # 新增代码+DesktopGUICors：函数段结束，do_OPTIONS 到此结束；如果没有边界说明，初学者不易看出它只负责浏览器预检。

    def _read_json_body(self) -> dict[str, Any] | str:  # 新增代码+DesktopGUILifecycle：函数段开始，读取 POST JSON body；如果没有这段，messages/cancel/retry 无法解析请求。
        raw_length = self.headers.get("Content-Length", "0")  # 新增代码+DesktopGUILifecycle：读取 body 长度；如果没有这行，rfile 不知道读多少字节。
        try:  # 新增代码+DesktopGUILifecycle：捕获非法长度；如果没有这行，坏 header 会导致 traceback。
            length = int(raw_length)  # 新增代码+DesktopGUILifecycle：把长度转整数；如果没有这行，read 不能使用字符串长度。
        except ValueError:  # 新增代码+DesktopGUILifecycle：处理非数字长度；如果没有这行，错误请求无法得到 400。
            return "Content-Length 必须是整数。"  # 新增代码+DesktopGUILifecycle：返回可读错误；如果没有这行，调用方不知道哪里错。
        if length <= 0:  # 新增代码+DesktopGUILifecycle：允许空 JSON 请求转为空对象；如果没有这行，cancel/retry 空 body 会失败。
            return {}  # 新增代码+DesktopGUILifecycle：返回空对象；如果没有这行，空 body 会被当错误。
        if length > 1_000_000:  # 新增代码+DesktopGUILifecycle：限制请求体大小；如果没有这行，大请求可能占用过多内存。
            return "请求体过大，最大 1000000 字节。"  # 新增代码+DesktopGUILifecycle：返回大小限制错误；如果没有这行，客户端不知道上限。
        raw_body = self.rfile.read(length)  # 新增代码+DesktopGUILifecycle：读取 body 字节；如果没有这行，无法解析 JSON。
        try:  # 新增代码+DesktopGUILifecycle：捕获 UTF-8/JSON 错误；如果没有这行，坏 JSON 会抛 traceback。
            payload = json.loads(raw_body.decode("utf-8"))  # 新增代码+DesktopGUILifecycle：解码并解析 JSON；如果没有这行，中文 prompt 无法稳定传入。
        except (UnicodeDecodeError, json.JSONDecodeError) as error:  # 新增代码+DesktopGUILifecycle：处理编码或 JSON 格式错误；如果没有这行，前端拿不到结构化错误。
            return f"请求体必须是 UTF-8 JSON：{error}"  # 新增代码+DesktopGUILifecycle：返回解析错误；如果没有这行，调试 HTTP 请求更困难。
        if not isinstance(payload, dict):  # 新增代码+DesktopGUILifecycle：要求顶层 JSON 是对象；如果没有这行，数组/字符串会让字段读取语义混乱。
            return "请求 JSON 顶层必须是对象。"  # 新增代码+DesktopGUILifecycle：返回结构错误；如果没有这行，客户端不知道该传对象。
        return payload  # 新增代码+DesktopGUILifecycle：返回解析后的对象；如果没有这行，POST 端点无法继续。
    # 新增代码+DesktopGUILifecycle：函数段结束，_read_json_body 到此结束；如果没有边界说明，初学者不易看出它只负责 body 解析。

    def do_GET(self) -> None:  # 修改代码+DesktopGUIBridge：函数段开始，处理 GET 请求；如果没有这段，GUI 无法读取 bootstrap/events/health。
        parsed_url = urllib.parse.urlparse(self.path)  # 修改代码+DesktopGUIBridge：解析 URL；如果没有这行，带 query 的事件请求无法读参数。
        path = parsed_url.path  # 修改代码+DesktopGUIBridge：提取 path；如果没有这行，路由无法判断端点。
        query = urllib.parse.parse_qs(parsed_url.query)  # 修改代码+DesktopGUIBridge：解析 query；如果没有这行，events 无法读取 since_sequence/limit。
        if path in {"/health", "/v1/gui/health"}:  # 修改代码+DesktopGUIBridge：识别无需 token 的探活端点；如果没有这行，Electron 启动前无法轻量探测。
            if not self._guard_request(require_token=False):  # 修改代码+DesktopGUIBridge：health 仍检查 Origin；如果没有这行，恶意来源可探测 bridge。
                return  # 修改代码+DesktopGUIBridge：门禁失败后退出；如果没有这行，会继续发送成功响应。
            self._send_json(200, {"ok": True, "app": "OpenHarness Desktop", "schema_version": GUI_SCHEMA_VERSION})  # 修改代码+DesktopGUIBridge：返回轻量健康信息；如果没有这行，前端不知道 bridge 是否在线。
            return  # 修改代码+DesktopGUIBridge：响应完成后退出；如果没有这行，handler 可能二次响应。
        if path == "/v2/gui/health":  # ????+GuiDiagnostics????? token ? V2 health ??????????????????? uptime?workspace ? feature flags?
            if not self._guard_request(require_token=True):  # ????+GuiDiagnostics?V2 health ?????????????????????????????????????
                return  # ????+GuiDiagnostics??????????????????????????????? payload?
            self._send_json(200, build_gui_health_payload(self.server.workspace, started_at=self.server.started_at))  # ????+GuiDiagnostics??? V2 health payload???????????????????????
            return  # ????+GuiDiagnostics??????????????????handler ???????????
        if path == "/v2/gui/diagnostics":  # ????+GuiDiagnostics??? V2 diagnostics ?????????????????????????
            if not self._guard_request(require_token=True):  # ????+GuiDiagnostics???????????????????????????????????????????
                return  # ????+GuiDiagnostics??????????????????????????????? payload?
            self._send_json(200, build_gui_diagnostics_payload(self.server.workspace, bridge_token=self.server.token, started_at=self.server.started_at))  # ????+GuiDiagnostics????????? payload???????????????? release gate ??????
            return  # ????+GuiDiagnostics??????????????????handler ???????????
        if path in {"/v1/gui/bootstrap", "/gui/bootstrap"}:  # 修改代码+DesktopGUIBridge：识别 bootstrap 端点；如果没有这行，首屏请求会 404。
            if not self._guard_request(require_token=True):  # 修改代码+DesktopGUIBridge：bootstrap 必须 token；如果没有这行，项目状态可能被未授权读取。
                return  # 修改代码+DesktopGUIBridge：门禁失败后退出；如果没有这行，会继续返回状态。
            self._send_json(200, build_gui_bootstrap_payload(self.server.workspace))  # 修改代码+DesktopGUIBridge：返回首屏 payload；如果没有这行，GUI 不能启动。
            return  # 修改代码+DesktopGUIBridge：响应完成后退出；如果没有这行，handler 可能二次响应。
        if path == "/v2/gui/sessions":  # 新增代码+DesktopGUISessionSearch：识别 V2 会话列表端点；如果没有这行，成熟侧栏只能继续使用缺字段的 V1 sessions。
            if not self._guard_request(require_token=True):  # 新增代码+DesktopGUISessionSearch：V2 sessions 必须 token；如果没有这行，本地未授权网页可能读取会话标题和摘要。
                return  # 新增代码+DesktopGUISessionSearch：门禁失败后退出；如果没有这行，会继续返回敏感会话列表。
            include_archived = query.get("include_archived", ["false"])[0].lower() in {"1", "true", "yes"}  # 新增代码+DesktopGUISessionSearch：读取是否包含归档会话；如果没有这行，归档视图没有后端入口。
            self._send_json(200, self.server.run_manager.sessions_payload(include_archived=include_archived))  # 新增代码+DesktopGUISessionSearch：返回 V2 会话列表；如果没有这行，前端无法拿到 pinned/archive/updated_at 字段。
            return  # 新增代码+DesktopGUISessionSearch：响应完成后退出；如果没有这行，handler 可能继续匹配旧路由。
        if path == "/v2/gui/search":  # 新增代码+DesktopGUISessionSearch：识别 V2 搜索端点；如果没有这行，搜索面板无法读取后端结果。
            if not self._guard_request(require_token=True):  # 新增代码+DesktopGUISessionSearch：search 必须 token；如果没有这行，本地未授权网页可能遍历历史消息摘要。
                return  # 新增代码+DesktopGUISessionSearch：门禁失败后退出；如果没有这行，会继续执行搜索。
            search_query = query.get("q", [""])[0]  # 新增代码+DesktopGUISessionSearch：读取搜索词；如果没有这行，后端不知道用户要查什么。
            include_archived = query.get("include_archived", ["false"])[0].lower() in {"1", "true", "yes"}  # 新增代码+DesktopGUISessionSearch：读取是否搜索归档会话；如果没有这行，归档搜索无法扩展。
            self._send_json(200, self.server.run_manager.search_sessions(search_query, include_archived=include_archived))  # 新增代码+DesktopGUISessionSearch：返回搜索结果；如果没有这行，搜索面板只能显示空状态。
            return  # 新增代码+DesktopGUISessionSearch：响应完成后退出；如果没有这行，handler 可能继续匹配其它路由。
        if path in {"/v1/gui/sessions", "/gui/sessions"}:  # 新增代码+DesktopGUISessions：识别会话列表端点；如果没有这行，侧栏无法读取真实 sessions。
            if not self._guard_request(require_token=True):  # 新增代码+DesktopGUISessions：sessions 必须 token；如果没有这行，本地未授权网页可能读取会话列表。
                return  # 新增代码+DesktopGUISessions：门禁失败后退出；如果没有这行，会继续返回敏感状态。
            self._send_json(200, self.server.run_manager.sessions_payload())  # 修改代码+DesktopGUISessionList：返回 GUI bridge 自己的真实会话列表；如果没有这行代码，侧栏会继续显示空最近对话。
            return  # 新增代码+DesktopGUISessions：响应完成后退出；如果没有这行，handler 可能二次响应。
        if path in {"/v1/gui/browser/providers", "/gui/browser/providers"}:  # 新增代码+DesktopGUIBrowserPanel：识别浏览器 provider 状态端点；如果没有这行，右侧浏览器面板无法读取状态。
            if not self._guard_request(require_token=True):  # 新增代码+DesktopGUIBrowserPanel：浏览器状态必须 token；如果没有这行，本地未授权网页可能读取标签页和扩展状态。
                return  # 新增代码+DesktopGUIBrowserPanel：门禁失败后退出；如果没有这行，会继续返回敏感状态。
            self._send_json(200, build_gui_browser_providers_payload(self.server.workspace))  # 新增代码+DesktopGUIBrowserPanel：返回 provider_status 和 browser 摘要；如果没有这行，前端 browserProviders() 没有数据。
            return  # 新增代码+DesktopGUIBrowserPanel：响应完成后退出；如果没有这行，handler 可能二次响应。
        if path == "/v2/gui/runtime/panels":  # 新增代码+DesktopRuntimePanels：识别 V2 runtime panels 聚合端点；如果没有这行，成熟右栏只能继续多端点拼接。
            if not self._guard_request(require_token=True):  # 新增代码+DesktopRuntimePanels：runtime panels 必须 token；如果没有这行，本地未授权网页可能读取浏览器和 Computer Use 状态。
                return  # 新增代码+DesktopRuntimePanels：门禁失败后退出；如果没有这行，会继续返回敏感状态。
            self._send_json(200, build_gui_runtime_panels_payload(self.server.workspace))  # 新增代码+DesktopRuntimePanels：返回浏览器、Computer Use 和权限摘要；如果没有这行，前端无法一次刷新成熟面板。
            return  # 新增代码+DesktopRuntimePanels：响应完成后退出；如果没有这行，handler 可能二次响应。
        if path == "/v2/gui/harness/status":  # 新增代码+DesktopGUIHarnessPanel：识别 V2 Harness 状态端点；如果没有这行，右侧长任务面板无法读取目标、队列和 checkpoint。
            if not self._guard_request(require_token=True):  # 新增代码+DesktopGUIHarnessPanel：Harness 状态必须 token；如果没有这行，本地未授权网页可能读取长任务摘要。
                return  # 新增代码+DesktopGUIHarnessPanel：门禁失败后退出；如果没有这行，会继续返回敏感状态。
            self._send_json(200, build_gui_harness_status_payload(self.server.workspace))  # 新增代码+DesktopGUIHarnessPanel：返回长任务面板 payload；如果没有这行，前端无法展示 Harness 状态。
            return  # 新增代码+DesktopGUIHarnessPanel：响应完成后退出；如果没有这行，handler 可能二次响应。
        if path == "/v2/gui/events":  # 新增代码+GuiV2Stream：识别 V2 JSON fallback 事件端点；如果没有这一行，断线恢复只能依赖旧 V1 轮询。
            if not self._guard_request(require_token=True):  # 新增代码+GuiV2Stream：V2 fallback 必须通过 header token；如果没有这一行，本地未授权网页可能读取事件流。
                return  # 新增代码+GuiV2Stream：门禁失败后退出；如果没有这一行，未授权请求仍可能读取事件。
            try:  # 新增代码+GuiV2Stream：捕获 query 数字解析错误；如果没有这一行，坏游标会变成 500。
                since_raw = query.get("since_sequence", [""])[0]  # 新增代码+GuiV2Stream：读取断线恢复游标；如果没有这一行，后端不知道从哪里继续。
                limit_raw = query.get("limit", ["50"])[0]  # 新增代码+GuiV2Stream：读取返回数量限制；如果没有这一行，fallback 批量大小不稳定。
                since_sequence = int(since_raw) if since_raw else None  # 新增代码+GuiV2Stream：把 since_sequence 转成整数或空；如果没有这一行，事件选择 helper 会收到字符串。
                limit = int(limit_raw) if limit_raw else 50  # 新增代码+GuiV2Stream：把 limit 转成整数；如果没有这一行，helper 无法做数值限制。
            except ValueError as error:  # 新增代码+GuiV2Stream：处理非法数字；如果没有这一行，前端拿不到结构化 bad_query。
                self._send_error(400, "bad_query", f"v2 events query 参数必须是整数：{error}")  # 新增代码+GuiV2Stream：返回低敏 query 错误；如果没有这一行，坏请求不可机器解析。
                return  # 新增代码+GuiV2Stream：参数错误后退出；如果没有这一行，会继续读取事件。
            events = select_events_after(self.server.workspace, since_sequence=since_sequence, limit=limit)  # 新增代码+GuiV2Stream：读取 V2 事件或 heartbeat；如果没有这一行，fallback 没有事件数据。
            self._send_json(200, {"ok": True, "schema_version": GUI_SCHEMA_VERSION, "events": events, "since_sequence": since_sequence, "limit": limit})  # 新增代码+GuiV2Stream：返回 V2 fallback payload；如果没有这一行，前端 long polling 没有合同可用。
            return  # 新增代码+GuiV2Stream：响应完成后退出；如果没有这一行，handler 可能继续匹配旧路由。
        if path == "/v2/gui/events/stream":  # 新增代码+GuiV2Stream：识别 V2 SSE 事件端点；如果没有这一行，EventSource 无法连接后端事件流。
            if not self._guard_request(require_token=True):  # 新增代码+GuiV2Stream：stream 需要 header token 或 query token；如果没有这一行，本地未授权网页可能读事件。
                return  # 新增代码+GuiV2Stream：门禁失败后退出；如果没有这一行，未授权请求仍可能读取事件。
            try:  # 新增代码+GuiV2Stream：捕获 stream query 数字解析错误；如果没有这一行，坏游标会变成 500。
                since_raw = query.get("since_sequence", [""])[0]  # 新增代码+GuiV2Stream：读取 stream 断线恢复游标；如果没有这一行，SSE 不能从上次位置继续。
                limit_raw = query.get("limit", ["50"])[0]  # 新增代码+GuiV2Stream：读取 stream 批量限制；如果没有这一行，SSE 返回数量不稳定。
                since_sequence = int(since_raw) if since_raw else None  # 新增代码+GuiV2Stream：转换 since_sequence；如果没有这一行，helper 会收到字符串。
                limit = int(limit_raw) if limit_raw else 50  # 新增代码+GuiV2Stream：转换 limit；如果没有这一行，helper 无法安全限制。
            except ValueError as error:  # 新增代码+GuiV2Stream：处理非法 stream query；如果没有这一行，前端拿不到结构化 bad_query。
                self._send_error(400, "bad_query", f"v2 events stream query 参数必须是整数：{error}")  # 新增代码+GuiV2Stream：返回低敏 stream query 错误；如果没有这一行，坏请求不可机器解析。
                return  # 新增代码+GuiV2Stream：参数错误后退出；如果没有这一行，会继续写 SSE。
            events = select_events_after(self.server.workspace, since_sequence=since_sequence, limit=limit)  # 新增代码+GuiV2Stream：读取 V2 stream 事件或 heartbeat；如果没有这一行，SSE 没有数据帧。
            self._send_sse_events(events)  # 新增代码+GuiV2Stream：写出 SSE 响应；如果没有这一行，EventSource 收不到事件。
            return  # 新增代码+GuiV2Stream：响应完成后退出；如果没有这一行，handler 可能继续匹配旧路由。
        if path in {"/v1/gui/events", "/gui/events"}:  # 修改代码+DesktopGUIBridge：识别事件轮询端点；如果没有这行，前端无法读取工具和任务事件。
            if not self._guard_request(require_token=True):  # 修改代码+DesktopGUIBridge：事件端点必须 token；如果没有这行，运行事件可能被未授权读取。
                return  # 修改代码+DesktopGUIBridge：门禁失败后退出；如果没有这行，会继续返回事件。
            try:  # 修改代码+DesktopGUIBridge：捕获 query 数字解析错误；如果没有这行，坏参数会变成 500。
                since_raw = query.get("since_sequence", [""])[0]  # 修改代码+DesktopGUIBridge：读取事件游标；如果没有这行，前端无法增量读取。
                limit_raw = query.get("limit", ["50"])[0]  # 修改代码+DesktopGUIBridge：读取事件数量限制；如果没有这行，默认限制不稳定。
                since_sequence = int(since_raw) if since_raw else None  # 修改代码+DesktopGUIBridge：转换游标；如果没有这行，store 无法按序过滤。
                limit = int(limit_raw) if limit_raw else 50  # 修改代码+DesktopGUIBridge：转换数量限制；如果没有这行，helper 会收到字符串。
            except ValueError as error:  # 修改代码+DesktopGUIBridge：处理非法数字；如果没有这行，前端拿不到结构化错误。
                self._send_error(400, "bad_query", f"events query 参数必须是整数：{error}")  # 修改代码+DesktopGUIBridge：返回 query 错误；如果没有这行，坏请求不可机器解析。
                return  # 修改代码+DesktopGUIBridge：参数错误后退出；如果没有这行，会继续读取事件。
            self._send_json(200, build_gui_events_payload(self.server.workspace, since_sequence=since_sequence, limit=limit))  # 修改代码+DesktopGUIBridge：返回事件 payload；如果没有这行，GUI watcher 无法工作。
            return  # 修改代码+DesktopGUIBridge：响应完成后退出；如果没有这行，handler 可能二次响应。
        self._send_error(404, "not_found", "未知 GUI bridge GET 路径。")  # 修改代码+DesktopGUIBridge：返回结构化 404；如果没有这行，前端会收到 HTML 错误页。
    # 修改代码+DesktopGUIBridge：函数段结束，do_GET 到此结束；如果没有边界说明，初学者不易看出只读端点范围。

    def do_POST(self) -> None:  # 新增代码+DesktopGUILifecycle：函数段开始，处理 GUI 生命周期 POST；如果没有这段，messages/cancel/retry/resume 全部不可用。
        parsed_url = urllib.parse.urlparse(self.path)  # 新增代码+DesktopGUILifecycle：解析 URL；如果没有这行，动态 turn/session 路径无法匹配。
        path = parsed_url.path  # 新增代码+DesktopGUILifecycle：提取 path；如果没有这行，路由判断没有输入。
        if not self._guard_request(require_token=True):  # 新增代码+DesktopGUILifecycle：所有 POST 必须通过 token；如果没有这行，未授权进程可控制 GUI turn。
            return  # 新增代码+DesktopGUILifecycle：门禁失败后退出；如果没有这行，会继续执行业务动作。
        body = self._read_json_body()  # 新增代码+DesktopGUILifecycle：读取 JSON body；如果没有这行，端点拿不到 prompt/decision。
        if isinstance(body, str):  # 新增代码+DesktopGUILifecycle：判断 body 解析是否失败；如果没有这行，错误字符串会被当 dict。
            self._send_error(400, "bad_json", body)  # 新增代码+DesktopGUILifecycle：返回 JSON 格式错误；如果没有这行，前端无法修正请求。
            return  # 新增代码+DesktopGUILifecycle：坏 body 后退出；如果没有这行，会继续访问字段。
        try:  # 新增代码+DesktopGUILifecycle：统一捕获业务结构化错误；如果没有这行，每个分支都要重复 try/except。
            if path == "/v1/gui/messages":  # 新增代码+DesktopGUILifecycle：识别发送消息端点；如果没有这行，GUI 无法创建 turn。
                payload = self.server.run_manager.start_message(str(body.get("conversation_id", "default")), str(body.get("prompt", "")), client_request_id=str(body.get("client_request_id", "")))  # 新增代码+DesktopGUILifecycle：提交 prompt 给 run manager；如果没有这行，POST /messages 没有业务效果。
                self._send_json(200, payload)  # 新增代码+DesktopGUILifecycle：返回消息提交响应；如果没有这行，前端拿不到 turn/run id。
                return  # 新增代码+DesktopGUILifecycle：响应完成后退出；如果没有这行，handler 可能继续匹配路由。
            parts = [part for part in path.split("/") if part]  # 新增代码+DesktopGUILifecycle：拆分动态路径；如果没有这行，turn_id/session_id 无法提取。
            if len(parts) == 5 and parts[:3] == ["v1", "gui", "turns"] and parts[4] == "cancel":  # 新增代码+DesktopGUILifecycle：匹配 /v1/gui/turns/{turn_id}/cancel；如果没有这行，取消 endpoint 不可用。
                self._send_json(200, self.server.run_manager.cancel_turn(parts[3]))  # 新增代码+DesktopGUILifecycle：执行取消并返回响应；如果没有这行，取消按钮没有后端效果。
                return  # 新增代码+DesktopGUILifecycle：响应完成后退出；如果没有这行，handler 可能继续匹配路由。
            if len(parts) == 5 and parts[:3] == ["v1", "gui", "turns"] and parts[4] == "retry":  # 新增代码+DesktopGUILifecycle：匹配 /v1/gui/turns/{turn_id}/retry；如果没有这行，重试 endpoint 不可用。
                self._send_json(200, self.server.run_manager.retry_turn(parts[3]))  # 新增代码+DesktopGUILifecycle：执行重试并返回新 turn；如果没有这行，retry 按钮没有后端效果。
                return  # 新增代码+DesktopGUILifecycle：响应完成后退出；如果没有这行，handler 可能继续匹配路由。
            if len(parts) == 5 and parts[:3] == ["v1", "gui", "sessions"] and parts[4] == "resume":  # 新增代码+DesktopGUILifecycle：匹配 /v1/gui/sessions/{session_id}/resume；如果没有这行，恢复 endpoint 不可用。
                self._send_json(200, self.server.run_manager.resume_session(parts[3]))  # 新增代码+DesktopGUILifecycle：执行恢复并返回消息；如果没有这行，窗口重启无法恢复会话。
                return  # 新增代码+DesktopGUILifecycle：响应完成后退出；如果没有这行，handler 可能继续匹配路由。
            if len(parts) == 5 and parts[:3] == ["v2", "gui", "sessions"] and parts[4] == "rename":  # 新增代码+DesktopGUISessionSearch：匹配 /v2/gui/sessions/{session_id}/rename；如果没有这行，前端改名没有真实后端路由。
                self._send_json(200, self.server.run_manager.rename_session(parts[3], title=str(body.get("title", body.get("name", "")))))  # 新增代码+DesktopGUISessionSearch：执行会话改名并返回新条目；如果没有这行，rename 请求不会落盘。
                return  # 新增代码+DesktopGUISessionSearch：响应完成后退出；如果没有这行，handler 可能继续匹配其它路由。
            if len(parts) == 5 and parts[:3] == ["v2", "gui", "sessions"] and parts[4] == "archive":  # 新增代码+DesktopGUISessionSearch：匹配 /v2/gui/sessions/{session_id}/archive；如果没有这行，归档按钮没有真实后端路由。
                self._send_json(200, self.server.run_manager.archive_session(parts[3], archived=bool(body.get("archived", True))))  # 新增代码+DesktopGUISessionSearch：执行归档或恢复并返回结果；如果没有这行，archive 请求不会改变列表。
                return  # 新增代码+DesktopGUISessionSearch：响应完成后退出；如果没有这行，handler 可能继续匹配其它路由。
            if path == "/v2/gui/harness/pause":  # 新增代码+DesktopGUIHarnessPanel：匹配 Harness 暂停请求；如果没有这行，前端无法得到结构化能力反馈。
                self._send_json(200, build_gui_harness_control_payload("pause"))  # 新增代码+DesktopGUIHarnessPanel：返回未支持但稳定的暂停响应；如果没有这行，按钮能力探测只能得到 404。
                return  # 新增代码+DesktopGUIHarnessPanel：响应完成后退出；如果没有这行，handler 可能继续匹配其它路由。
            if path == "/v2/gui/harness/resume":  # 新增代码+DesktopGUIHarnessPanel：匹配 Harness 恢复请求；如果没有这行，前端无法得到结构化能力反馈。
                self._send_json(200, build_gui_harness_control_payload("resume"))  # 新增代码+DesktopGUIHarnessPanel：返回未支持但稳定的恢复响应；如果没有这行，按钮能力探测只能得到 404。
                return  # 新增代码+DesktopGUIHarnessPanel：响应完成后退出；如果没有这行，handler 可能继续匹配其它路由。
            if len(parts) == 5 and parts[:3] == ["v1", "gui", "permissions"] and parts[4] == "decision":  # 新增代码+DesktopGUIPermissions：匹配 /v1/gui/permissions/{request_id}/decision；如果没有这行，权限弹窗无法把允许/拒绝交给后端。
                payload = self.server.run_manager.decide_permission(parts[3], turn_id=str(body.get("turn_id", "")), decision=str(body.get("decision", "")), reason=str(body.get("reason", "")))  # 新增代码+DesktopGUIPermissions：执行权限决策并返回审计游标；如果没有这行，前端按钮只有本地效果没有后端事实。
                self._send_json(200, payload)  # 新增代码+DesktopGUIPermissions：返回权限决策响应；如果没有这行，前端无法关闭或更新弹窗状态。
                return  # 新增代码+DesktopGUIPermissions：响应完成后退出；如果没有这行，handler 可能继续匹配路由。
        except GuiBridgeError as error:  # 新增代码+DesktopGUILifecycle：处理结构化业务错误；如果没有这行，busy/not_found 会变成 500。
            self._send_error(error.status, error.code, error.message)  # 新增代码+DesktopGUILifecycle：返回业务错误；如果没有这行，前端无法稳定识别错误。
            return  # 新增代码+DesktopGUILifecycle：错误响应后退出；如果没有这行，handler 可能继续发送第二个响应。
        self._send_error(404, "not_found", "未知 GUI bridge POST 路径。")  # 新增代码+DesktopGUILifecycle：返回结构化 POST 404；如果没有这行，前端会收到 HTML 错误页。
    # 新增代码+DesktopGUILifecycle：函数段结束，do_POST 到此结束；如果没有边界说明，初学者不易看出生命周期路由范围。


def create_gui_bridge_server(workspace: str | Path, host: str = "127.0.0.1", port: int = 8776, token: str = "", answer_runner: GuiAnswerRunner | None = None, agent_adapter: GuiAgentAdapter | None = None) -> DesktopGuiBridgeServer:  # 修改代码+GuiAgentAdapter：函数段开始，创建可注入 V2 adapter 的 GUI bridge server；如果没有这段，CLI 和测试会重复构造逻辑且无法切换 adapter。
    return DesktopGuiBridgeServer((host, port), workspace=workspace, token=token, answer_runner=answer_runner, agent_adapter=agent_adapter)  # 修改代码+GuiAgentAdapter：返回绑定 server 并透传 adapter；如果没有这行，调用方拿不到可 serve_forever 的对象。
# 修改代码+DesktopGUIBridge：函数段结束，create_gui_bridge_server 到此结束；如果没有边界说明，初学者不易看出它只负责创建 server。
