"""Safe diagnostics payloads for the Desktop GUI shell."""  # 新增代码+GuiDiagnostics：说明本模块只负责 GUI 诊断和脱敏；如果没有这行代码，维护者不容易分清它和 gui_bridge 的职责。

from __future__ import annotations  # 新增代码+GuiDiagnostics：启用延迟类型解析；如果没有这行代码，类型注解在旧运行路径中可能提前求值。

import json  # 新增代码+GuiDiagnostics：读取 release gate JSON 并生成可复制诊断包；如果没有这行代码，诊断信息无法结构化保存。
import re  # 新增代码+GuiDiagnostics：执行 token 和路径脱敏；如果没有这行代码，诊断包可能泄露本地秘密。
import time  # 新增代码+GuiDiagnostics：计算 bridge uptime；如果没有这行代码，健康检查没有运行时长事实。
from pathlib import Path  # 新增代码+GuiDiagnostics：规范化 workspace 和 gate 文件路径；如果没有这行代码，Windows 路径处理容易出错。
from typing import Any  # 新增代码+GuiDiagnostics：标注动态 JSON 结构；如果没有这行代码，函数边界类型不清楚。

from learning_agent.app.gui_protocol import GUI_V2_SCHEMA_VERSION  # 新增代码+GuiDiagnostics：复用 V2 schema 事实源；如果没有这行代码，诊断协议版本会和 bridge 分裂。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+GuiDiagnostics：读取统一运行状态快照；如果没有这行代码，诊断页没有后端状态依据。
from learning_agent.tools.catalog import READ_ONLY_CONCURRENT_TOOL_NAMES, build_builtin_tool_catalog  # 新增代码+GuiDiagnosticsToolSurface：复用现有工具目录和只读白名单；如果没有这行代码，诊断页会硬编码 LSP/REPL 能力并和真实 agent 分裂。


GUI_DIAGNOSTICS_SAFE_SNAPSHOT_ERROR = "状态快照暂时不可读。"  # 新增代码+GuiDiagnostics：统一安全错误文案；如果没有这行代码，异常信息可能把本地路径带到前端。
GUI_DIAGNOSTICS_RELEASE_GATE_PATHS = (Path("memory/gui_bridge/release_gate_result.json"), Path("apps/desktop/release-gate-result.json"))  # 新增代码+GuiDiagnostics：声明 release gate 结果查找位置；如果没有这行代码，诊断页无法读取最近验收结论。
GUI_DIAGNOSTICS_LSP_TOOL_NAMES = ("lsp_symbols", "lsp_definition", "lsp_diagnostics")  # 新增代码+GuiDiagnosticsToolSurface：声明诊断页要检查的 LSP 工具名；如果没有这行代码，前端无法确认符号、跳转和语法诊断是否已接入。
GUI_DIAGNOSTICS_REPL_TOOL_NAME = "repl"  # 新增代码+GuiDiagnosticsToolSurface：声明批量只读 REPL 工具名；如果没有这行代码，诊断页无法独立显示 REPL 可用性。
GUI_DIAGNOSTICS_RECENT_EVENT_LIMIT = 8  # 新增代码+GuiDiagnosticsToolSurface：限制诊断页展示的最近事件类型数量；如果没有这行代码，长任务事件流可能让 payload 过大。
GUI_DIAGNOSTICS_WARNING_LIMIT = 5  # 新增代码+GuiDiagnosticsToolSurface：限制健康警告展示数量；如果没有这行代码，异常积累时诊断页会被警告淹没。


def redact_diagnostic_text(value: object) -> str:  # 新增代码+GuiDiagnostics：函数段开始，统一脱敏诊断文本；如果没有这段函数，token、Bearer 和本机路径会散落在各处手工处理。
    text = str(value)  # 新增代码+GuiDiagnostics：把任意异常或字段转成文本；如果没有这行代码，非字符串错误无法脱敏。
    text = re.sub(r"X-OpenHarness-Desktop-Token\s*[:=]\s*[^\s,;]+", "X-OpenHarness-Desktop-Token: [redacted-token]", text, flags=re.IGNORECASE)  # 新增代码+GuiDiagnostics：脱敏 GUI bridge header token；如果没有这行代码，本地 bridge token 可能进入诊断包。
    text = re.sub(r"\bBearer\s+[A-Za-z0-9._~+\-/=]+", "Bearer [redacted-token]", text, flags=re.IGNORECASE)  # 新增代码+GuiDiagnostics：脱敏 Bearer token；如果没有这行代码，API 密钥可能进入诊断包。
    text = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[redacted-token]", text, flags=re.IGNORECASE)  # 新增代码+GuiDiagnostics：脱敏 OpenAI 风格密钥片段；如果没有这行代码，独立出现的 sk token 可能泄露。
    text = re.sub(r"\b(token|api_key|apikey|secret)\s*[:=]\s*[^\s,;]+", r"\1=[redacted-token]", text, flags=re.IGNORECASE)  # 新增代码+GuiDiagnostics：脱敏通用 token/key 字段；如果没有这行代码，配置错误文本可能泄露凭据。
    text = re.sub(r"[A-Za-z]:[\\/][^\s\"'<>|,;]+", "[redacted-path]", text)  # 新增代码+GuiDiagnostics：脱敏 Windows 绝对路径；如果没有这行代码，用户名和本地目录结构会进入 UI。
    text = re.sub(r"/(?:Users|home)/[^\s\"'<>|,;]+", "[redacted-path]", text)  # 新增代码+GuiDiagnostics：脱敏类 Unix 用户路径；如果没有这行代码，跨平台诊断仍可能暴露本机目录。
    return text  # 新增代码+GuiDiagnostics：返回安全文本；如果没有这行代码，调用方拿不到脱敏结果。
# 新增代码+GuiDiagnostics：函数段结束，redact_diagnostic_text 到此结束；如果没有这个边界，初学者不容易看出脱敏范围。


def _feature_flags() -> dict[str, bool]:  # 新增代码+GuiDiagnostics：函数段开始，集中声明 GUI 能力开关；如果没有这段函数，health/bootstrap/settings 会出现互相不一致的能力描述。
    return {  # 新增代码+GuiDiagnostics：返回功能开关对象；如果没有这行代码，前端无法按能力显示设置和诊断入口。
        "event_polling": True,  # 新增代码+GuiDiagnostics：声明事件轮询可用；如果没有这行代码，前端可能隐藏状态时间线。
        "streaming": True,  # 新增代码+GuiDiagnostics：声明 V2 流式事件能力可用；如果没有这行代码，前端无法判断是否可升级到 stream。
        "runtime_panels": True,  # 新增代码+GuiDiagnostics：声明浏览器和 Computer Use 面板可用；如果没有这行代码，右侧成熟面板缺少能力依据。
        "settings": True,  # 新增代码+GuiDiagnostics：声明设置页可用；如果没有这行代码，前端设置入口没有后端事实。
        "diagnostics": True,  # 新增代码+GuiDiagnostics：声明诊断页可用；如果没有这行代码，前端无法确认诊断能力已接线。
    }  # 新增代码+GuiDiagnostics：功能开关对象结束；如果没有这行代码，字典语法不完整。
# 新增代码+GuiDiagnostics：函数段结束，_feature_flags 到此结束；如果没有这个边界，初学者不容易看出能力开关范围。


def _workspace_path(workspace: str | Path) -> Path:  # 新增代码+GuiDiagnostics：函数段开始，规范化 workspace；如果没有这段函数，多处路径处理会重复且容易不一致。
    return Path(workspace).expanduser().resolve()  # 新增代码+GuiDiagnostics：解析真实工作区路径；如果没有这行代码，health 和 release gate 查找可能指向不同目录。
# 新增代码+GuiDiagnostics：函数段结束，_workspace_path 到此结束；如果没有这个边界，初学者不容易看出路径规范化范围。


def _uptime_seconds(started_at: float | None, now: float | None) -> float:  # 新增代码+GuiDiagnostics：函数段开始，计算运行时长；如果没有这段函数，health payload 的 uptime 逻辑会散在调用方。
    current_time = float(now if now is not None else time.time())  # 新增代码+GuiDiagnostics：读取当前时间并允许测试注入；如果没有这行代码，测试无法稳定断言 uptime。
    started_time = float(started_at if started_at is not None else current_time)  # 新增代码+GuiDiagnostics：读取启动时间并兜底为当前时间；如果没有这行代码，未传 started_at 会产生异常。
    return round(max(0.0, current_time - started_time), 3)  # 新增代码+GuiDiagnostics：返回非负秒数；如果没有这行代码，系统时间回拨会导致负数显示。
# 新增代码+GuiDiagnostics：函数段结束，_uptime_seconds 到此结束；如果没有这个边界，初学者不容易看出运行时长范围。


def build_gui_health_payload(workspace: str | Path, *, started_at: float | None = None, now: float | None = None) -> dict[str, Any]:  # 新增代码+GuiDiagnostics：函数段开始，生成 V2 health payload；如果没有这段函数，设置页无法显示后端在线、版本和能力事实。
    workspace_path = _workspace_path(workspace)  # 新增代码+GuiDiagnostics：规范化工作区路径；如果没有这行代码，payload 可能显示相对路径。
    return {  # 新增代码+GuiDiagnostics：返回健康检查对象；如果没有这行代码，调用方拿不到结构化 health。
        "ok": True,  # 新增代码+GuiDiagnostics：标记 bridge 可响应；如果没有这行代码，前端无法判断在线状态。
        "backend_online": True,  # 新增代码+GuiDiagnostics：给诊断 UI 一个直观在线字段；如果没有这行代码，UI 需要从 ok 猜测后端状态。
        "schema_version": GUI_V2_SCHEMA_VERSION,  # 新增代码+GuiDiagnostics：暴露协议版本；如果没有这行代码，前端无法做版本兼容判断。
        "uptime_seconds": _uptime_seconds(started_at, now),  # 新增代码+GuiDiagnostics：暴露运行时长；如果没有这行代码，用户看不到 bridge 是否刚重启。
        "workspace": str(workspace_path),  # 新增代码+GuiDiagnostics：暴露当前工作区；如果没有这行代码，用户无法确认 GUI 连到哪个项目。
        "workspace_name": workspace_path.name or "OpenHarness",  # 新增代码+GuiDiagnostics：暴露短项目名；如果没有这行代码，设置页只能显示长路径。
        "feature_flags": _feature_flags(),  # 新增代码+GuiDiagnostics：暴露能力开关；如果没有这行代码，前端无法按能力渲染。
        "model_provider": {"provider": "OpenHarness", "model": "desktop-gui-bridge"},  # 新增代码+GuiDiagnostics：提供模型/后端展示名；如果没有这行代码，设置页缺少 provider/model 信息。
    }  # 新增代码+GuiDiagnostics：健康 payload 结束；如果没有这行代码，字典语法不完整。
# 新增代码+GuiDiagnostics：函数段结束，build_gui_health_payload 到此结束；如果没有这个边界，初学者不容易看出健康检查范围。


def _redact_json_like(value: Any) -> Any:  # 新增代码+GuiDiagnostics：函数段开始，递归脱敏 JSON-like 数据；如果没有这段函数，release gate 摘要中的嵌套字符串可能泄露。
    if isinstance(value, str):  # 新增代码+GuiDiagnostics：处理字符串；如果没有这行代码，文本字段不会被脱敏。
        return redact_diagnostic_text(value)  # 新增代码+GuiDiagnostics：返回脱敏字符串；如果没有这行代码，敏感文本会原样保留。
    if isinstance(value, list):  # 新增代码+GuiDiagnostics：处理数组；如果没有这行代码，数组里的字符串会漏过。
        return [_redact_json_like(item) for item in value]  # 新增代码+GuiDiagnostics：递归处理数组元素；如果没有这行代码，嵌套列表不会被清理。
    if isinstance(value, dict):  # 新增代码+GuiDiagnostics：处理对象；如果没有这行代码，JSON 对象字段不会被递归清理。
        return {str(key): _redact_json_like(item) for key, item in value.items()}  # 新增代码+GuiDiagnostics：递归处理对象值；如果没有这行代码，嵌套字段会漏过。
    return value  # 新增代码+GuiDiagnostics：数字和布尔值原样返回；如果没有这行代码，非字符串字段会丢失。
# 新增代码+GuiDiagnostics：函数段结束，_redact_json_like 到此结束；如果没有这个边界，初学者不容易看出递归脱敏范围。


def _safe_release_gate_result(workspace_path: Path) -> dict[str, Any]:  # 新增代码+GuiDiagnostics：函数段开始，读取最近 release gate 结果；如果没有这段函数，诊断面板无法告诉用户最后验收是否通过。
    for relative_path in GUI_DIAGNOSTICS_RELEASE_GATE_PATHS:  # 新增代码+GuiDiagnostics：按约定路径依次查找；如果没有这行代码，兼容旧/新 gate 输出会困难。
        gate_path = workspace_path / relative_path  # 新增代码+GuiDiagnostics：拼出候选文件路径；如果没有这行代码，无法定位 release gate 结果。
        if not gate_path.exists():  # 新增代码+GuiDiagnostics：跳过不存在的候选文件；如果没有这行代码，读取第一个缺失文件会报错。
            continue  # 新增代码+GuiDiagnostics：继续查找下一个路径；如果没有这行代码，后续兼容路径不会被尝试。
        try:  # 新增代码+GuiDiagnostics：保护 JSON 读取；如果没有这行代码，损坏的 gate 文件会拖垮诊断页。
            raw_payload = json.loads(gate_path.read_text(encoding="utf-8"))  # 新增代码+GuiDiagnostics：读取 gate JSON；如果没有这行代码，无法解析验收结果。
        except (OSError, json.JSONDecodeError) as error:  # 新增代码+GuiDiagnostics：捕获文件和 JSON 错误；如果没有这行代码，坏文件会导致 500。
            return {"present": True, "status": "unreadable", "summary": redact_diagnostic_text(error), "source": str(relative_path).replace("\\", "/")}  # 新增代码+GuiDiagnostics：返回安全不可读状态；如果没有这行代码，前端只能看到请求失败。
        payload = _redact_json_like(raw_payload if isinstance(raw_payload, dict) else {})  # 新增代码+GuiDiagnostics：只接受对象并递归脱敏；如果没有这行代码，任意 JSON 形状会污染 UI。
        return {  # 新增代码+GuiDiagnostics：返回稳定 gate 摘要；如果没有这行代码，前端需要理解任意 gate JSON。
            "present": True,  # 新增代码+GuiDiagnostics：标记已找到 gate 结果；如果没有这行代码，UI 无法区分未运行和读取成功。
            "ok": bool(payload.get("ok", False)),  # 新增代码+GuiDiagnostics：透传布尔结论；如果没有这行代码，UI 不能显示通过/失败。
            "status": str(payload.get("status", "unknown")),  # 新增代码+GuiDiagnostics：透传状态文本；如果没有这行代码，UI 无法显示 release gate 状态。
            "created_at": str(payload.get("created_at", "")),  # 新增代码+GuiDiagnostics：透传创建时间；如果没有这行代码，用户不知道结果新旧。
            "summary": str(payload.get("summary", "")),  # 新增代码+GuiDiagnostics：透传摘要；如果没有这行代码，用户看不到验收结论。
            "source": str(relative_path).replace("\\", "/"),  # 新增代码+GuiDiagnostics：只暴露相对路径；如果没有这行代码，绝对路径可能泄露。
        }  # 新增代码+GuiDiagnostics：gate 摘要结束；如果没有这行代码，字典语法不完整。
    return {"present": False, "ok": False, "status": "not_run", "created_at": "", "summary": "", "source": ""}  # 新增代码+GuiDiagnostics：没有结果时返回稳定空态；如果没有这行代码，前端需要处理 null。
# 新增代码+GuiDiagnostics：函数段结束，_safe_release_gate_result 到此结束；如果没有这个边界，初学者不容易看出 gate 读取范围。


def _as_record(value: Any) -> dict[str, Any]:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，把未知 JSON 收窄成对象；如果没有这段函数，坏 snapshot 会在字段读取时拖垮诊断页。
    return value if isinstance(value, dict) else {}  # 新增代码+GuiDiagnosticsToolSurface：只接受字典并为空值兜底；如果没有这行代码，None 或列表会触发属性读取错误。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_as_record 到此结束；如果没有这个边界，初学者不容易看出对象收窄范围。


def _as_list(value: Any) -> list[Any]:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，把未知 JSON 收窄成数组；如果没有这段函数，事件、任务和命令列表读取会不稳定。
    return value if isinstance(value, list) else []  # 新增代码+GuiDiagnosticsToolSurface：只接受列表并为空值兜底；如果没有这行代码，坏字段会让列表遍历报错。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_as_list 到此结束；如果没有这个边界，初学者不容易看出数组收窄范围。


def _safe_int(value: Any, fallback: int = 0) -> int:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，安全读取整数指标；如果没有这段函数，字符串或空值会破坏计数展示。
    try:  # 新增代码+GuiDiagnosticsToolSurface：尝试把输入转成整数；如果没有这行代码，合法数字字符串不能复用。
        return int(value)  # 新增代码+GuiDiagnosticsToolSurface：返回整数形式；如果没有这行代码，前端会收到不可预测的计数字段。
    except (TypeError, ValueError):  # 新增代码+GuiDiagnosticsToolSurface：处理无法转换的值；如果没有这行代码，坏 snapshot 会抛异常。
        return fallback  # 新增代码+GuiDiagnosticsToolSurface：返回调用方兜底值；如果没有这行代码，诊断 payload 会中断生成。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_safe_int 到此结束；如果没有这个边界，初学者不容易看出整数兜底范围。


def _safe_short_text(value: Any, fallback: str = "", limit: int = 160) -> str:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，生成脱敏短文本；如果没有这段函数，事件类型和错误摘要可能过长或泄露路径。
    if value is None:  # 修改代码+GuiDiagnosticsNoneRegression：先识别 Python None 空值；如果没有这行代码，空字段会被 str(None) 变成 GUI 上难懂的 "None"。
        return fallback  # 修改代码+GuiDiagnosticsNoneRegression：让空值使用调用方指定的人话兜底；如果没有这行代码，Trace/Compact/Resume 空态会显示错误文案。
    text = redact_diagnostic_text(value).strip()  # 新增代码+GuiDiagnosticsToolSurface：先走统一脱敏再去掉空白；如果没有这行代码，token 或本机路径可能进入诊断摘要。
    if not text:  # 新增代码+GuiDiagnosticsToolSurface：识别空文本；如果没有这行代码，空字段会显示成空白。
        return fallback  # 新增代码+GuiDiagnosticsToolSurface：返回可控兜底文案；如果没有这行代码，前端需要处理更多空态。
    if len(text) > limit:  # 新增代码+GuiDiagnosticsToolSurface：限制文本长度；如果没有这行代码，长日志片段可能撑大 payload。
        return f"{text[:limit]}..."  # 新增代码+GuiDiagnosticsToolSurface：返回截断后的安全文本；如果没有这行代码，用户看不到内容被压缩。
    return text  # 新增代码+GuiDiagnosticsToolSurface：返回短文本；如果没有这行代码，调用方拿不到字段值。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_safe_short_text 到此结束；如果没有这个边界，初学者不容易看出短文本范围。


def _status_events(snapshot: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，从快照里读取状态事件尾巴；如果没有这段函数，Trace 摘要会和 status_snapshot 字段名耦死。
    status = _as_record(snapshot.get("status"))  # 新增代码+GuiDiagnosticsToolSurface：兼容早期 status.events 形态；如果没有这行代码，旧测试 fixture 会读不到事件。
    raw_events = _as_list(snapshot.get("latest_events")) or _as_list(snapshot.get("status_events")) or _as_list(status.get("events"))  # 新增代码+GuiDiagnosticsToolSurface：按新旧字段顺序读取事件；如果没有这行代码，真实事件流可能被误判为空。
    return [dict(event) for event in raw_events if isinstance(event, dict)]  # 新增代码+GuiDiagnosticsToolSurface：只保留对象事件并复制一层；如果没有这行代码，坏事件会破坏摘要生成。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_status_events 到此结束；如果没有这个边界，初学者不容易看出事件读取范围。


def _active_status_count(items: list[Any], active_statuses: set[str]) -> int:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，统计仍在活动中的命令或任务；如果没有这段函数，队列和任务摘要会重复状态判断。
    return sum(1 for item in items if isinstance(item, dict) and _safe_short_text(item.get("status"), "unknown", 80) in active_statuses)  # 新增代码+GuiDiagnosticsToolSurface：只按白名单状态计数；如果没有这行代码，已完成任务也可能被算作 active。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_active_status_count 到此结束；如果没有这个边界，初学者不容易看出活动计数范围。


def _latest_event_summary(event: dict[str, Any]) -> dict[str, Any]:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，生成单条事件的安全摘要；如果没有这段函数，Trace/Compact/Resume 会重复挑字段且可能输出完整 payload。
    if not event:  # 新增代码+GuiDiagnosticsToolSurface：处理没有事件的情况；如果没有这行代码，空事件会显示伪造字段。
        return {}  # 新增代码+GuiDiagnosticsToolSurface：返回空对象表示暂无事件；如果没有这行代码，前端需要处理 null。
    return {  # 新增代码+GuiDiagnosticsToolSurface：返回事件白名单字段；如果没有这行代码，调用方拿不到可渲染摘要。
        "sequence": _safe_int(event.get("sequence"), 0),  # 新增代码+GuiDiagnosticsToolSurface：保留事件序号；如果没有这行代码，用户无法把 GUI 和日志游标对应起来。
        "event_type": _safe_short_text(event.get("event_type"), "unknown", 120),  # 新增代码+GuiDiagnosticsToolSurface：保留事件类型；如果没有这行代码，诊断页看不到当前运行卡点。
        "run_id": _safe_short_text(event.get("run_id"), "", 120),  # 新增代码+GuiDiagnosticsToolSurface：保留 run_id；如果没有这行代码，多 run 排查会缺少关联。
        "turn_id": _safe_short_text(event.get("turn_id"), "", 120),  # 新增代码+GuiDiagnosticsToolSurface：保留 turn_id；如果没有这行代码，单轮排查会缺少关联。
        "session_id": _safe_short_text(event.get("session_id"), "", 120),  # 新增代码+GuiDiagnosticsToolSurface：保留 session_id；如果没有这行代码，恢复报告无法快速定位会话。
    }  # 新增代码+GuiDiagnosticsToolSurface：事件摘要结束；如果没有这行代码，字典语法不完整。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_latest_event_summary 到此结束；如果没有这个边界，初学者不容易看出事件摘要范围。


def _recent_event_types(events: list[dict[str, Any]]) -> list[str]:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，提取最近事件类型；如果没有这段函数，诊断页只能显示一条最新事件。
    event_types: list[str] = []  # 新增代码+GuiDiagnosticsToolSurface：准备保存最近事件类型；如果没有这行代码，函数没有返回容器。
    for event in events[-GUI_DIAGNOSTICS_RECENT_EVENT_LIMIT:]:  # 新增代码+GuiDiagnosticsToolSurface：只遍历尾部少量事件；如果没有这行代码，大事件流会增加 payload。
        event_type = _safe_short_text(event.get("event_type"), "", 120)  # 新增代码+GuiDiagnosticsToolSurface：读取并脱敏事件类型；如果没有这行代码，异常字段可能进入 UI。
        if event_type:  # 新增代码+GuiDiagnosticsToolSurface：跳过空事件类型；如果没有这行代码，列表会出现无意义空项。
            event_types.append(event_type)  # 新增代码+GuiDiagnosticsToolSurface：保存可展示事件类型；如果没有这行代码，前端看不到近期事件脉络。
    return event_types  # 新增代码+GuiDiagnosticsToolSurface：返回事件类型列表；如果没有这行代码，Trace 摘要没有近期上下文。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_recent_event_types 到此结束；如果没有这个边界，初学者不容易看出最近事件范围。


def _snapshot_summary(snapshot: dict[str, Any]) -> dict[str, Any]:  # 新增代码+GuiDiagnostics：函数段开始，把状态快照压成安全摘要；如果没有这段函数，完整 snapshot 可能把本机路径传到诊断 UI。
    events = _status_events(snapshot)  # 修改代码+GuiDiagnosticsToolSurface：从 status_snapshot 的新旧字段读取事件；如果没有这行代码，event_count 会长期显示 0。
    counts = _as_record(snapshot.get("counts"))  # 新增代码+GuiDiagnosticsToolSurface：读取快照自带计数字段；如果没有这行代码，聚合器已有计数无法复用。
    commands = _as_list(snapshot.get("commands"))  # 修改代码+GuiDiagnosticsToolSurface：读取 runtime command 列表；如果没有这行代码，队列深度无法来自真实命令队列。
    tasks = _as_list(snapshot.get("tasks"))  # 修改代码+GuiDiagnosticsToolSurface：读取任务列表；如果没有这行代码，活跃任务数无法来自真实 task_registry。
    runs = _as_list(snapshot.get("runs"))  # 新增代码+GuiDiagnosticsToolSurface：读取 run 列表；如果没有这行代码，诊断页看不到长任务规模。
    sessions = _as_list(snapshot.get("sessions"))  # 新增代码+GuiDiagnosticsToolSurface：读取 session 列表；如果没有这行代码，恢复入口规模不可见。
    return {  # 新增代码+GuiDiagnostics：返回安全快照摘要；如果没有这行代码，调用方无法显示诊断指标。
        "event_count": _safe_int(counts.get("status_events"), len(events)),  # 修改代码+GuiDiagnosticsToolSurface：优先复用快照事件计数并兜底实际列表长度；如果没有这行代码，事件流活跃度不可信。
        "queue_depth": _active_status_count(commands, {"queued", "leased", "running", "pending"}),  # 修改代码+GuiDiagnosticsToolSurface：统计仍未完成的 runtime commands；如果没有这行代码，后台命令堵塞不可见。
        "active_tasks": _active_status_count(tasks, {"queued", "leased", "running", "pending", "in_progress"}),  # 修改代码+GuiDiagnosticsToolSurface：统计仍需关注的任务；如果没有这行代码，任务负载不可见。
        "run_count": _safe_int(counts.get("runs"), len(runs)),  # 新增代码+GuiDiagnosticsToolSurface：展示 harness run 数量；如果没有这行代码，长任务规模不可见。
        "session_count": _safe_int(counts.get("sessions"), len(sessions)),  # 新增代码+GuiDiagnosticsToolSurface：展示可恢复会话数量；如果没有这行代码，resume 规模不可见。
    }  # 新增代码+GuiDiagnostics：快照摘要结束；如果没有这行代码，字典语法不完整。
# 新增代码+GuiDiagnostics：函数段结束，_snapshot_summary 到此结束；如果没有这个边界，初学者不容易看出快照摘要范围。


def _trace_summary(snapshot: dict[str, Any], snapshot_summary: dict[str, Any]) -> dict[str, Any]:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，生成 read_trace 风格安全摘要；如果没有这段函数，GUI 只能看到粗略 event_count。
    events = _status_events(snapshot)  # 新增代码+GuiDiagnosticsToolSurface：读取统一状态事件尾巴；如果没有这行代码，Trace 摘要没有事实来源。
    latest_event = _latest_event_summary(events[-1] if events else {})  # 新增代码+GuiDiagnosticsToolSurface：取最新事件摘要；如果没有这行代码，用户无法快速判断当前阶段。
    latest_tool_event = _latest_event_summary(_as_record(_as_record(snapshot.get("tools")).get("latest_tool_event")))  # 新增代码+GuiDiagnosticsToolSurface：读取最近工具事件摘要；如果没有这行代码，工具链卡点不可见。
    return {  # 新增代码+GuiDiagnosticsToolSurface：返回 Trace 摘要；如果没有这行代码，调用方拿不到可渲染对象。
        "tool": "read_trace",  # 新增代码+GuiDiagnosticsToolSurface：声明这个区域对应 read_trace 能力；如果没有这行代码，用户不知道复用来源。
        "source": "learning_agent.runtime.status_events",  # 新增代码+GuiDiagnosticsToolSurface：说明事件来自既有状态事件 store；如果没有这行代码，GUI 像是另造日志系统。
        "event_count": _safe_int(snapshot_summary.get("event_count"), len(events)),  # 新增代码+GuiDiagnosticsToolSurface：展示事件数量；如果没有这行代码，Trace 区没有规模指标。
        "latest_event_type": _safe_short_text(latest_event.get("event_type"), "none", 120),  # 新增代码+GuiDiagnosticsToolSurface：展示最新事件类型；如果没有这行代码，用户无法一眼看出当前状态。
        "latest_event_sequence": _safe_int(latest_event.get("sequence"), 0),  # 新增代码+GuiDiagnosticsToolSurface：展示最新事件序号；如果没有这行代码，用户无法和事件轮询游标对应。
        "latest_tool_event_type": _safe_short_text(latest_tool_event.get("event_type"), "none", 120),  # 新增代码+GuiDiagnosticsToolSurface：展示最近工具事件类型；如果没有这行代码，工具调用停顿不明显。
        "recent_event_types": _recent_event_types(events),  # 新增代码+GuiDiagnosticsToolSurface：展示最近事件脉络；如果没有这行代码，诊断页缺少运行连续性。
    }  # 新增代码+GuiDiagnosticsToolSurface：Trace 摘要结束；如果没有这行代码，字典语法不完整。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_trace_summary 到此结束；如果没有这个边界，初学者不容易看出 Trace 摘要范围。


def _compact_status_summary(snapshot: dict[str, Any]) -> dict[str, Any]:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，生成 compact_status 安全摘要；如果没有这段函数，GUI 看不到上下文压缩边界。
    compact = _as_record(snapshot.get("compact"))  # 新增代码+GuiDiagnosticsToolSurface：读取 status_snapshot.compact；如果没有这行代码，压缩状态没有事实来源。
    event = _as_record(compact.get("event"))  # 新增代码+GuiDiagnosticsToolSurface：读取 compact 最近事件；如果没有这行代码，状态和事件序号无法关联。
    boundary_uuid = _safe_short_text(compact.get("latest_boundary_uuid"), "", 160)  # 新增代码+GuiDiagnosticsToolSurface：读取最近压缩边界 id；如果没有这行代码，恢复/压缩无法定位。
    return {  # 新增代码+GuiDiagnosticsToolSurface：返回 compact 摘要；如果没有这行代码，调用方拿不到可渲染对象。
        "tool": "compact_status",  # 新增代码+GuiDiagnosticsToolSurface：声明复用 compact_status 能力；如果没有这行代码，用户不知道来源。
        "state": _safe_short_text(compact.get("state"), "not_run", 120),  # 新增代码+GuiDiagnosticsToolSurface：展示 compact 状态；如果没有这行代码，压缩是否发生不可见。
        "latest_boundary_uuid": boundary_uuid,  # 新增代码+GuiDiagnosticsToolSurface：展示最近边界 id；如果没有这行代码，恢复审计缺少锚点。
        "has_boundary": bool(boundary_uuid),  # 新增代码+GuiDiagnosticsToolSurface：给前端一个直接布尔状态；如果没有这行代码，UI 要自己判断空字符串。
        "latest_event_type": _safe_short_text(event.get("event_type"), "", 120),  # 新增代码+GuiDiagnosticsToolSurface：展示来源事件类型；如果没有这行代码，压缩状态缺少证据。
        "latest_event_sequence": _safe_int(event.get("sequence"), 0),  # 新增代码+GuiDiagnosticsToolSurface：展示来源事件序号；如果没有这行代码，压缩状态无法和日志对应。
    }  # 新增代码+GuiDiagnosticsToolSurface：compact 摘要结束；如果没有这行代码，字典语法不完整。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_compact_status_summary 到此结束；如果没有这个边界，初学者不容易看出 compact 摘要范围。


def _session_id_from_value(value: Any) -> str:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，从 session 条目读取安全 id；如果没有这段函数，resume 摘要无法兼容字符串和对象两种 session 形态。
    if isinstance(value, dict):  # 新增代码+GuiDiagnosticsToolSurface：处理对象型 session 摘要；如果没有这行代码，新版 session list 会读不到 id。
        return _safe_short_text(value.get("session_id", value.get("id", "")), "", 160)  # 新增代码+GuiDiagnosticsToolSurface：优先读取 session_id 并兼容 id；如果没有这行代码，恢复报告无法定位会话。
    return _safe_short_text(value, "", 160)  # 新增代码+GuiDiagnosticsToolSurface：处理字符串型 session id；如果没有这行代码，旧版 session list 会显示为空。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_session_id_from_value 到此结束；如果没有这个边界，初学者不容易看出 session id 读取范围。


def _resume_report_summary(snapshot: dict[str, Any]) -> dict[str, Any]:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，生成 resume_report 安全摘要；如果没有这段函数，GUI 看不到恢复是否需要人工关注。
    resume = _as_record(snapshot.get("resume"))  # 新增代码+GuiDiagnosticsToolSurface：读取 status_snapshot.resume；如果没有这行代码，恢复状态没有事实来源。
    event = _as_record(resume.get("event"))  # 新增代码+GuiDiagnosticsToolSurface：读取最近恢复事件；如果没有这行代码，resume 状态无法和事件关联。
    sessions = _as_list(snapshot.get("sessions"))  # 新增代码+GuiDiagnosticsToolSurface：读取最近 session 列表；如果没有这行代码，resume_report 没有会话入口。
    state = _safe_short_text(resume.get("state"), "not_run", 120)  # 新增代码+GuiDiagnosticsToolSurface：读取恢复状态；如果没有这行代码，GUI 需要自己从事件推断。
    latest_session_id = _safe_short_text(event.get("session_id"), "", 160) or (_session_id_from_value(sessions[0]) if sessions else "")  # 新增代码+GuiDiagnosticsToolSurface：优先用事件会话并兜底最近 session；如果没有这行代码，恢复报告入口可能为空。
    return {  # 新增代码+GuiDiagnosticsToolSurface：返回 resume 摘要；如果没有这行代码，调用方拿不到可渲染对象。
        "tool": "resume_report",  # 新增代码+GuiDiagnosticsToolSurface：声明复用 resume_report 能力；如果没有这行代码，用户不知道来源。
        "state": state,  # 新增代码+GuiDiagnosticsToolSurface：展示恢复状态；如果没有这行代码，用户无法判断恢复是否安全。
        "latest_session_id": latest_session_id,  # 新增代码+GuiDiagnosticsToolSurface：展示最近可审计会话；如果没有这行代码，用户无法继续定位恢复报告。
        "session_count": len(sessions),  # 新增代码+GuiDiagnosticsToolSurface：展示可恢复会话数量；如果没有这行代码，恢复规模不可见。
        "requires_attention": state in {"resume_needs_review", "resume_blocked"},  # 新增代码+GuiDiagnosticsToolSurface：把危险恢复状态转成布尔值；如果没有这行代码，前端要重复业务判断。
        "latest_event_type": _safe_short_text(event.get("event_type"), "", 120),  # 新增代码+GuiDiagnosticsToolSurface：展示最近恢复事件类型；如果没有这行代码，状态证据不可见。
        "latest_event_sequence": _safe_int(event.get("sequence"), 0),  # 新增代码+GuiDiagnosticsToolSurface：展示最近恢复事件序号；如果没有这行代码，resume 状态无法对齐日志。
    }  # 新增代码+GuiDiagnosticsToolSurface：resume 摘要结束；如果没有这行代码，字典语法不完整。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_resume_report_summary 到此结束；如果没有这个边界，初学者不容易看出 resume 摘要范围。


def _health_status_summary(snapshot: dict[str, Any]) -> dict[str, Any]:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，生成 health_status 安全摘要；如果没有这段函数，GUI 无法显示状态生态健康警告。
    health = _as_record(snapshot.get("health"))  # 新增代码+GuiDiagnosticsToolSurface：读取 status_snapshot.health；如果没有这行代码，健康状态没有事实来源。
    warnings = [_safe_short_text(item, "", 160) for item in _as_list(health.get("warnings"))]  # 新增代码+GuiDiagnosticsToolSurface：脱敏并收集健康警告；如果没有这行代码，警告可能过长或泄露路径。
    warnings = [item for item in warnings if item][:GUI_DIAGNOSTICS_WARNING_LIMIT]  # 新增代码+GuiDiagnosticsToolSurface：移除空警告并限制数量；如果没有这行代码，异常堆积会淹没诊断页。
    return {  # 新增代码+GuiDiagnosticsToolSurface：返回健康摘要；如果没有这行代码，调用方拿不到可渲染对象。
        "tool": "health_status",  # 新增代码+GuiDiagnosticsToolSurface：声明复用 health_status 能力；如果没有这行代码，用户不知道来源。
        "ok": bool(health.get("ok", True)),  # 新增代码+GuiDiagnosticsToolSurface：展示整体健康布尔值；如果没有这行代码，UI 不能快速显示正常/异常。
        "warning_count": len(_as_list(health.get("warnings"))),  # 新增代码+GuiDiagnosticsToolSurface：展示原始警告数量；如果没有这行代码，被截断的警告规模不可见。
        "warnings": warnings,  # 新增代码+GuiDiagnosticsToolSurface：展示少量脱敏警告；如果没有这行代码，用户看不到健康风险原因。
        "run_count": _safe_int(health.get("run_count"), len(_as_list(snapshot.get("runs")))),  # 新增代码+GuiDiagnosticsToolSurface：展示 run 数量；如果没有这行代码，健康指标缺少规模背景。
        "task_count": _safe_int(health.get("task_count"), len(_as_list(snapshot.get("tasks")))),  # 新增代码+GuiDiagnosticsToolSurface：展示 task 数量；如果没有这行代码，任务健康无法快速判断。
        "event_count": _safe_int(health.get("event_count"), len(_status_events(snapshot))),  # 新增代码+GuiDiagnosticsToolSurface：展示 event 数量；如果没有这行代码，事件生态活跃度不可见。
    }  # 新增代码+GuiDiagnosticsToolSurface：健康摘要结束；如果没有这行代码，字典语法不完整。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_health_status_summary 到此结束；如果没有这个边界，初学者不容易看出健康摘要范围。


def _safe_tool_catalog_names() -> tuple[set[str], str]:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，安全读取内置工具目录名称集合；如果没有这段函数，LSP/REPL 可用性只能硬编码。
    try:  # 新增代码+GuiDiagnosticsToolSurface：保护工具目录构建；如果没有这行代码，schema 损坏会让整个诊断端点 500。
        names = {str(getattr(tool, "name", "")) for tool in build_builtin_tool_catalog()}  # 新增代码+GuiDiagnosticsToolSurface：从真实 catalog 收集工具名；如果没有这行代码，GUI 会和 agent 工具面分裂。
    except Exception:  # 新增代码+GuiDiagnosticsToolSurface：捕获目录读取失败并安全降级；如果没有这行代码，异常可能暴露内部路径。
        return set(), "工具目录暂时不可读。"  # 新增代码+GuiDiagnosticsToolSurface：返回空集合和安全文案；如果没有这行代码，调用方无法标记降级。
    return {name for name in names if name}, ""  # 新增代码+GuiDiagnosticsToolSurface：去掉空工具名并返回无错误；如果没有这行代码，空 schema 名称会污染诊断结果。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_safe_tool_catalog_names 到此结束；如果没有这个边界，初学者不容易看出工具目录读取范围。


def _lsp_diagnostics_summary(tool_names: set[str]) -> dict[str, Any]:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，生成 LSP 工具可用性摘要；如果没有这段函数，GUI 无法证明符号/定义/诊断已接入。
    missing_tools = [name for name in GUI_DIAGNOSTICS_LSP_TOOL_NAMES if name not in tool_names]  # 新增代码+GuiDiagnosticsToolSurface：找出缺失的 LSP 工具；如果没有这行代码，前端只能看到笼统 available。
    return {  # 新增代码+GuiDiagnosticsToolSurface：返回 LSP 摘要；如果没有这行代码，调用方拿不到可渲染对象。
        "tool": "lsp_diagnostics",  # 新增代码+GuiDiagnosticsToolSurface：声明主诊断工具名；如果没有这行代码，用户不知道这组能力的入口。
        "available": not missing_tools,  # 新增代码+GuiDiagnosticsToolSurface：展示整组 LSP 是否完整可用；如果没有这行代码，GUI 无法显示接入状态。
        "tool_names": list(GUI_DIAGNOSTICS_LSP_TOOL_NAMES),  # 新增代码+GuiDiagnosticsToolSurface：展示三件套工具名；如果没有这行代码，用户不知道具体覆盖了什么。
        "missing_tool_names": missing_tools,  # 新增代码+GuiDiagnosticsToolSurface：展示缺失工具；如果没有这行代码，排查缺口不明确。
        "implementation": "python_ast_minimal_lsp",  # 新增代码+GuiDiagnosticsToolSurface：说明当前复用 AST 最小实现；如果没有这行代码，用户可能误以为已接入完整语言服务器。
        "scope": "workspace_python_files",  # 新增代码+GuiDiagnosticsToolSurface：说明能力范围是工作区 Python 文件；如果没有这行代码，GUI 能力边界不清楚。
        "read_only": all(name in READ_ONLY_CONCURRENT_TOOL_NAMES for name in GUI_DIAGNOSTICS_LSP_TOOL_NAMES),  # 新增代码+GuiDiagnosticsToolSurface：展示 LSP 工具都是只读；如果没有这行代码，用户无法判断权限风险。
        "safe_error": "；".join(missing_tools) if missing_tools else "",  # 新增代码+GuiDiagnosticsToolSurface：缺失时返回安全错误摘要；如果没有这行代码，前端没有可读原因。
    }  # 新增代码+GuiDiagnosticsToolSurface：LSP 摘要结束；如果没有这行代码，字典语法不完整。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_lsp_diagnostics_summary 到此结束；如果没有这个边界，初学者不容易看出 LSP 摘要范围。


def _repl_summary(tool_names: set[str]) -> dict[str, Any]:  # 新增代码+GuiDiagnosticsToolSurface：函数段开始，生成 REPL 工具可用性摘要；如果没有这段函数，GUI 无法显示批量只读编排能力。
    available = GUI_DIAGNOSTICS_REPL_TOOL_NAME in tool_names  # 新增代码+GuiDiagnosticsToolSurface：检查 repl 是否存在于真实 catalog；如果没有这行代码，GUI 会显示假可用。
    allowed_tools = sorted(name for name in READ_ONLY_CONCURRENT_TOOL_NAMES if name in tool_names)  # 新增代码+GuiDiagnosticsToolSurface：收集 REPL 可批量调用的只读工具样本；如果没有这行代码，用户看不到安全边界。
    return {  # 新增代码+GuiDiagnosticsToolSurface：返回 REPL 摘要；如果没有这行代码，调用方拿不到可渲染对象。
        "tool": GUI_DIAGNOSTICS_REPL_TOOL_NAME,  # 新增代码+GuiDiagnosticsToolSurface：展示工具名；如果没有这行代码，用户不知道入口名称。
        "available": available,  # 新增代码+GuiDiagnosticsToolSurface：展示 REPL 是否可用；如果没有这行代码，GUI 不能显示接入状态。
        "safe_batch_only": True,  # 新增代码+GuiDiagnosticsToolSurface：声明当前 REPL 只允许安全白名单批量调用；如果没有这行代码，用户无法理解权限边界。
        "max_calls": 5,  # 新增代码+GuiDiagnosticsToolSurface：展示单批次上限；如果没有这行代码，用户不知道 REPL 控制面限制。
        "allowed_tool_count": len(allowed_tools),  # 新增代码+GuiDiagnosticsToolSurface：展示可批量工具数量；如果没有这行代码，REPL 能力规模不可见。
        "sample_allowed_tools": allowed_tools[:GUI_DIAGNOSTICS_RECENT_EVENT_LIMIT],  # 新增代码+GuiDiagnosticsToolSurface：展示少量样例工具；如果没有这行代码，用户看不到具体可用项。
        "safe_error": "" if available else "repl 工具未在内置目录注册。",  # 新增代码+GuiDiagnosticsToolSurface：不可用时给出安全文案；如果没有这行代码，前端只能显示 unknown。
    }  # 新增代码+GuiDiagnosticsToolSurface：REPL 摘要结束；如果没有这行代码，字典语法不完整。
# 新增代码+GuiDiagnosticsToolSurface：函数段结束，_repl_summary 到此结束；如果没有这个边界，初学者不容易看出 REPL 摘要范围。


def build_gui_diagnostics_payload(workspace: str | Path, *, bridge_token: str = "", started_at: float | None = None, now: float | None = None, last_error: object = "") -> dict[str, Any]:  # 新增代码+GuiDiagnostics：函数段开始，生成 V2 diagnostics payload；如果没有这段函数，诊断 UI 只能拼零散接口且容易泄露敏感信息。
    workspace_path = _workspace_path(workspace)  # 新增代码+GuiDiagnostics：规范化工作区；如果没有这行代码，health 和 gate 查找可能不一致。
    health = build_gui_health_payload(workspace_path, started_at=started_at, now=now)  # 新增代码+GuiDiagnostics：复用健康 payload；如果没有这行代码，诊断页和设置页会显示不同事实。
    health["workspace"] = redact_diagnostic_text(health.get("workspace", ""))  # 新增代码+GuiDiagnostics：诊断包内只保留脱敏 workspace；如果没有这行代码，复制诊断时会泄露本机绝对路径。
    safe_errors: list[str] = []  # 修改代码+GuiDiagnosticsToolSurface：收集各子系统的安全降级文案；如果没有这行代码，snapshot 和 catalog 同时失败时会丢掉原因。
    snapshot: dict[str, Any] = {}  # 新增代码+GuiDiagnosticsToolSurface：准备保存统一状态快照；如果没有这行代码，后续 Trace/Compact/Resume 没有共同输入。
    snapshot_summary: dict[str, Any] = {"event_count": 0, "queue_depth": 0, "active_tasks": 0, "run_count": 0, "session_count": 0}  # 修改代码+GuiDiagnosticsToolSurface：准备快照摘要兜底；如果没有这行代码，快照失败时 UI 会缺字段。
    try:  # 新增代码+GuiDiagnostics：保护状态快照读取；如果没有这行代码，状态文件权限问题会拖垮诊断端点。
        snapshot = build_status_snapshot(workspace_path)  # 修改代码+GuiDiagnosticsToolSurface：只读取一次统一快照并复用给所有摘要；如果没有这行代码，各区域可能看到不同时间点的数据。
        snapshot_summary = _snapshot_summary(snapshot)  # 修改代码+GuiDiagnosticsToolSurface：读取并压缩状态快照；如果没有这行代码，诊断页没有事件/队列/任务事实。
    except Exception:  # 新增代码+GuiDiagnostics：捕获所有快照异常并降级；如果没有这行代码，路径异常可能直接暴露为 500。
        safe_errors.append(GUI_DIAGNOSTICS_SAFE_SNAPSHOT_ERROR)  # 修改代码+GuiDiagnosticsToolSurface：记录固定安全文案；如果没有这行代码，原始异常可能泄露路径。
    tool_names, catalog_error = _safe_tool_catalog_names()  # 新增代码+GuiDiagnosticsToolSurface：读取真实工具目录名称；如果没有这行代码，LSP/REPL 可用性只能靠猜。
    if catalog_error:  # 新增代码+GuiDiagnosticsToolSurface：判断工具目录是否降级；如果没有这行代码，catalog 失败不会反馈给 UI。
        safe_errors.append(catalog_error)  # 新增代码+GuiDiagnosticsToolSurface：记录工具目录安全错误；如果没有这行代码，用户不知道 LSP/REPL 状态为何不可用。
    status_degraded = bool(safe_errors)  # 修改代码+GuiDiagnosticsToolSurface：任何子系统降级都标记整体降级；如果没有这行代码，工具目录失败可能被显示成正常。
    safe_error = "；".join(safe_errors)  # 修改代码+GuiDiagnosticsToolSurface：合并安全错误文案；如果没有这行代码，前端只能看到空错误。
    release_gate = _safe_release_gate_result(workspace_path)  # 新增代码+GuiDiagnostics：读取最近 release gate；如果没有这行代码，诊断页无法显示验收状态。
    safe_last_error = redact_diagnostic_text(last_error) if str(last_error) else ""  # 新增代码+GuiDiagnostics：脱敏最近错误文本；如果没有这行代码，错误栏可能泄露密钥。
    trace_summary = _trace_summary(snapshot, snapshot_summary)  # 新增代码+GuiDiagnosticsToolSurface：生成 Trace 安全摘要；如果没有这行代码，GUI 诊断页看不到事件流脉络。
    compact_status = _compact_status_summary(snapshot)  # 新增代码+GuiDiagnosticsToolSurface：生成 Compact 安全摘要；如果没有这行代码，GUI 诊断页看不到压缩边界。
    resume_report_summary = _resume_report_summary(snapshot)  # 新增代码+GuiDiagnosticsToolSurface：生成 Resume 安全摘要；如果没有这行代码，GUI 诊断页看不到恢复风险。
    health_status_summary = _health_status_summary(snapshot)  # 新增代码+GuiDiagnosticsToolSurface：生成 health_status 摘要；如果没有这行代码，GUI 诊断页看不到状态生态健康警告。
    lsp_diagnostics_summary = _lsp_diagnostics_summary(tool_names)  # 新增代码+GuiDiagnosticsToolSurface：生成 LSP 工具摘要；如果没有这行代码，GUI 诊断页看不到符号/定义/诊断能力。
    repl_summary = _repl_summary(tool_names)  # 新增代码+GuiDiagnosticsToolSurface：生成 REPL 工具摘要；如果没有这行代码，GUI 诊断页看不到批量只读编排能力。
    diagnostic_core = {  # 新增代码+GuiDiagnostics：准备可复制诊断核心；如果没有这行代码，复制按钮没有稳定内容。
        "schema_version": GUI_V2_SCHEMA_VERSION,  # 新增代码+GuiDiagnostics：写入协议版本；如果没有这行代码，诊断包无法说明格式。
        "backend_online": True,  # 新增代码+GuiDiagnostics：写入在线状态；如果没有这行代码，诊断包缺少最基本健康事实。
        "status_degraded": status_degraded,  # 新增代码+GuiDiagnostics：写入降级状态；如果没有这行代码，排查者不知道 snapshot 是否可信。
        "safe_error": safe_error,  # 新增代码+GuiDiagnostics：写入安全错误；如果没有这行代码，复制包缺少降级原因。
        "snapshot_summary": snapshot_summary,  # 新增代码+GuiDiagnostics：写入快照摘要；如果没有这行代码，复制包缺少运行指标。
        "trace_summary": trace_summary,  # 新增代码+GuiDiagnosticsToolSurface：写入 Trace 摘要；如果没有这行代码，复制包缺少事件流线索。
        "compact_status": compact_status,  # 新增代码+GuiDiagnosticsToolSurface：写入 Compact 摘要；如果没有这行代码，复制包缺少上下文压缩状态。
        "resume_report_summary": resume_report_summary,  # 新增代码+GuiDiagnosticsToolSurface：写入 Resume 摘要；如果没有这行代码，复制包缺少恢复风险状态。
        "health_status_summary": health_status_summary,  # 新增代码+GuiDiagnosticsToolSurface：写入 health_status 摘要；如果没有这行代码，复制包缺少健康警告。
        "lsp_diagnostics_summary": lsp_diagnostics_summary,  # 新增代码+GuiDiagnosticsToolSurface：写入 LSP 摘要；如果没有这行代码，复制包缺少代码理解能力状态。
        "repl_summary": repl_summary,  # 新增代码+GuiDiagnosticsToolSurface：写入 REPL 摘要；如果没有这行代码，复制包缺少批量编排能力状态。
        "release_gate": release_gate,  # 新增代码+GuiDiagnostics：写入 release gate 摘要；如果没有这行代码，复制包缺少验收结论。
        "last_error": safe_last_error,  # 新增代码+GuiDiagnostics：写入脱敏错误；如果没有这行代码，复制包缺少最近失败线索。
        "bridge_token_present": bool(bridge_token),  # 新增代码+GuiDiagnostics：只记录 token 是否存在；如果没有这行代码，排查者不知道是否配置鉴权。
    }  # 新增代码+GuiDiagnostics：诊断核心结束；如果没有这行代码，字典语法不完整。
    copy_text = json.dumps(diagnostic_core, ensure_ascii=False, sort_keys=True)  # 新增代码+GuiDiagnostics：生成复制文本；如果没有这行代码，前端需要自己拼诊断包。
    return {  # 新增代码+GuiDiagnostics：返回完整诊断 payload；如果没有这行代码，HTTP route 没有响应体。
        "ok": True,  # 新增代码+GuiDiagnostics：标记诊断请求成功；如果没有这行代码，前端无法区分错误响应。
        "schema_version": GUI_V2_SCHEMA_VERSION,  # 新增代码+GuiDiagnostics：暴露诊断协议版本；如果没有这行代码，前端无法兼容演进。
        "backend_online": True,  # 新增代码+GuiDiagnostics：暴露后端在线状态；如果没有这行代码，诊断页需要从 ok 猜测。
        "health": health,  # 新增代码+GuiDiagnostics：嵌入 health 摘要；如果没有这行代码，设置页需要多次请求才能显示完整信息。
        "status_degraded": status_degraded,  # 新增代码+GuiDiagnostics：暴露降级状态；如果没有这行代码，UI 无法显示降级横幅。
        "safe_error": safe_error,  # 新增代码+GuiDiagnostics：暴露安全错误文案；如果没有这行代码，UI 无法解释降级。
        "snapshot_summary": snapshot_summary,  # 新增代码+GuiDiagnostics：暴露快照摘要；如果没有这行代码，诊断页缺少运行指标。
        "trace_summary": trace_summary,  # 新增代码+GuiDiagnosticsToolSurface：暴露 Trace 摘要；如果没有这行代码，诊断页看不到 read_trace 风格状态。
        "compact_status": compact_status,  # 新增代码+GuiDiagnosticsToolSurface：暴露 Compact 摘要；如果没有这行代码，诊断页看不到压缩状态。
        "resume_report_summary": resume_report_summary,  # 新增代码+GuiDiagnosticsToolSurface：暴露 Resume 摘要；如果没有这行代码，诊断页看不到恢复报告入口。
        "health_status_summary": health_status_summary,  # 新增代码+GuiDiagnosticsToolSurface：暴露 health_status 摘要；如果没有这行代码，诊断页看不到健康警告。
        "lsp_diagnostics_summary": lsp_diagnostics_summary,  # 新增代码+GuiDiagnosticsToolSurface：暴露 LSP 摘要；如果没有这行代码，诊断页看不到代码理解工具状态。
        "repl_summary": repl_summary,  # 新增代码+GuiDiagnosticsToolSurface：暴露 REPL 摘要；如果没有这行代码，诊断页看不到批量只读编排状态。
        "last_error": safe_last_error,  # 新增代码+GuiDiagnostics：暴露脱敏最近错误；如果没有这行代码，用户无法复制失败线索。
        "release_gate": release_gate,  # 新增代码+GuiDiagnostics：暴露 release gate 状态；如果没有这行代码，用户不知道最近验收是否通过。
        "diagnostic_bundle": {"redacted": True, "copy_text": copy_text, "log_path": "memory/gui_bridge", "evidence_path": "learning_agent/test/desktop_gui_shell_v2"},  # 新增代码+GuiDiagnostics：提供复制包和相对目录；如果没有这行代码，设置/诊断页复制按钮没有数据来源。
    }  # 新增代码+GuiDiagnostics：诊断 payload 结束；如果没有这行代码，字典语法不完整。
# 新增代码+GuiDiagnostics：函数段结束，build_gui_diagnostics_payload 到此结束；如果没有这个边界，初学者不容易看出诊断生成范围。
