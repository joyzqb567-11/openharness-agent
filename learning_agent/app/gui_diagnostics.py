"""Safe diagnostics payloads for the Desktop GUI shell."""  # 新增代码+GuiDiagnostics：说明本模块只负责 GUI 诊断和脱敏；如果没有这行代码，维护者不容易分清它和 gui_bridge 的职责。

from __future__ import annotations  # 新增代码+GuiDiagnostics：启用延迟类型解析；如果没有这行代码，类型注解在旧运行路径中可能提前求值。

import json  # 新增代码+GuiDiagnostics：读取 release gate JSON 并生成可复制诊断包；如果没有这行代码，诊断信息无法结构化保存。
import re  # 新增代码+GuiDiagnostics：执行 token 和路径脱敏；如果没有这行代码，诊断包可能泄露本地秘密。
import time  # 新增代码+GuiDiagnostics：计算 bridge uptime；如果没有这行代码，健康检查没有运行时长事实。
from pathlib import Path  # 新增代码+GuiDiagnostics：规范化 workspace 和 gate 文件路径；如果没有这行代码，Windows 路径处理容易出错。
from typing import Any  # 新增代码+GuiDiagnostics：标注动态 JSON 结构；如果没有这行代码，函数边界类型不清楚。

from learning_agent.app.gui_protocol import GUI_V2_SCHEMA_VERSION  # 新增代码+GuiDiagnostics：复用 V2 schema 事实源；如果没有这行代码，诊断协议版本会和 bridge 分裂。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+GuiDiagnostics：读取统一运行状态快照；如果没有这行代码，诊断页没有后端状态依据。


GUI_DIAGNOSTICS_SAFE_SNAPSHOT_ERROR = "状态快照暂时不可读。"  # 新增代码+GuiDiagnostics：统一安全错误文案；如果没有这行代码，异常信息可能把本地路径带到前端。
GUI_DIAGNOSTICS_RELEASE_GATE_PATHS = (Path("memory/gui_bridge/release_gate_result.json"), Path("apps/desktop/release-gate-result.json"))  # 新增代码+GuiDiagnostics：声明 release gate 结果查找位置；如果没有这行代码，诊断页无法读取最近验收结论。


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


def _snapshot_summary(snapshot: dict[str, Any]) -> dict[str, Any]:  # 新增代码+GuiDiagnostics：函数段开始，把状态快照压成安全摘要；如果没有这段函数，完整 snapshot 可能把本机路径传到诊断 UI。
    status = snapshot.get("status") if isinstance(snapshot.get("status"), dict) else {}  # 新增代码+GuiDiagnostics：读取 status 子对象；如果没有这行代码，坏 snapshot 会导致字段读取异常。
    events = status.get("events") if isinstance(status.get("events"), list) else []  # 新增代码+GuiDiagnostics：读取事件列表；如果没有这行代码，事件数量无法稳定计算。
    command_queue = snapshot.get("command_queue") if isinstance(snapshot.get("command_queue"), dict) else {}  # 新增代码+GuiDiagnostics：读取命令队列摘要；如果没有这行代码，诊断页缺少队列事实。
    task_registry = snapshot.get("task_registry") if isinstance(snapshot.get("task_registry"), dict) else {}  # 新增代码+GuiDiagnostics：读取任务注册表摘要；如果没有这行代码，诊断页缺少任务事实。
    return {  # 新增代码+GuiDiagnostics：返回安全快照摘要；如果没有这行代码，调用方无法显示诊断指标。
        "event_count": len(events),  # 新增代码+GuiDiagnostics：提供事件数量；如果没有这行代码，用户无法判断事件流活跃度。
        "queue_depth": command_queue.get("queue_depth", command_queue.get("pending_count", 0)),  # 新增代码+GuiDiagnostics：提供队列深度；如果没有这行代码，长任务拥堵不可见。
        "active_tasks": task_registry.get("active_count", task_registry.get("running_count", 0)),  # 新增代码+GuiDiagnostics：提供活跃任务数；如果没有这行代码，诊断页无法显示任务负载。
    }  # 新增代码+GuiDiagnostics：快照摘要结束；如果没有这行代码，字典语法不完整。
# 新增代码+GuiDiagnostics：函数段结束，_snapshot_summary 到此结束；如果没有这个边界，初学者不容易看出快照摘要范围。


def build_gui_diagnostics_payload(workspace: str | Path, *, bridge_token: str = "", started_at: float | None = None, now: float | None = None, last_error: object = "") -> dict[str, Any]:  # 新增代码+GuiDiagnostics：函数段开始，生成 V2 diagnostics payload；如果没有这段函数，诊断 UI 只能拼零散接口且容易泄露敏感信息。
    workspace_path = _workspace_path(workspace)  # 新增代码+GuiDiagnostics：规范化工作区；如果没有这行代码，health 和 gate 查找可能不一致。
    health = build_gui_health_payload(workspace_path, started_at=started_at, now=now)  # 新增代码+GuiDiagnostics：复用健康 payload；如果没有这行代码，诊断页和设置页会显示不同事实。
    health["workspace"] = redact_diagnostic_text(health.get("workspace", ""))  # 新增代码+GuiDiagnostics：诊断包内只保留脱敏 workspace；如果没有这行代码，复制诊断时会泄露本机绝对路径。
    status_degraded = False  # 新增代码+GuiDiagnostics：默认状态快照正常；如果没有这行代码，后续 payload 没有明确布尔值。
    safe_error = ""  # 新增代码+GuiDiagnostics：默认没有安全错误文案；如果没有这行代码，前端无法稳定读取字段。
    snapshot_summary: dict[str, Any] = {"event_count": 0, "queue_depth": 0, "active_tasks": 0}  # 新增代码+GuiDiagnostics：准备快照摘要兜底；如果没有这行代码，快照失败时 UI 会缺字段。
    try:  # 新增代码+GuiDiagnostics：保护状态快照读取；如果没有这行代码，状态文件权限问题会拖垮诊断端点。
        snapshot_summary = _snapshot_summary(build_status_snapshot(workspace_path))  # 新增代码+GuiDiagnostics：读取并压缩状态快照；如果没有这行代码，诊断页没有事件/队列/任务事实。
    except Exception:  # 新增代码+GuiDiagnostics：捕获所有快照异常并降级；如果没有这行代码，路径异常可能直接暴露为 500。
        status_degraded = True  # 新增代码+GuiDiagnostics：标记状态降级；如果没有这行代码，UI 会误以为诊断完整。
        safe_error = GUI_DIAGNOSTICS_SAFE_SNAPSHOT_ERROR  # 新增代码+GuiDiagnostics：使用固定安全文案；如果没有这行代码，原始异常可能泄露路径。
    release_gate = _safe_release_gate_result(workspace_path)  # 新增代码+GuiDiagnostics：读取最近 release gate；如果没有这行代码，诊断页无法显示验收状态。
    safe_last_error = redact_diagnostic_text(last_error) if str(last_error) else ""  # 新增代码+GuiDiagnostics：脱敏最近错误文本；如果没有这行代码，错误栏可能泄露密钥。
    diagnostic_core = {  # 新增代码+GuiDiagnostics：准备可复制诊断核心；如果没有这行代码，复制按钮没有稳定内容。
        "schema_version": GUI_V2_SCHEMA_VERSION,  # 新增代码+GuiDiagnostics：写入协议版本；如果没有这行代码，诊断包无法说明格式。
        "backend_online": True,  # 新增代码+GuiDiagnostics：写入在线状态；如果没有这行代码，诊断包缺少最基本健康事实。
        "status_degraded": status_degraded,  # 新增代码+GuiDiagnostics：写入降级状态；如果没有这行代码，排查者不知道 snapshot 是否可信。
        "safe_error": safe_error,  # 新增代码+GuiDiagnostics：写入安全错误；如果没有这行代码，复制包缺少降级原因。
        "snapshot_summary": snapshot_summary,  # 新增代码+GuiDiagnostics：写入快照摘要；如果没有这行代码，复制包缺少运行指标。
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
        "last_error": safe_last_error,  # 新增代码+GuiDiagnostics：暴露脱敏最近错误；如果没有这行代码，用户无法复制失败线索。
        "release_gate": release_gate,  # 新增代码+GuiDiagnostics：暴露 release gate 状态；如果没有这行代码，用户不知道最近验收是否通过。
        "diagnostic_bundle": {"redacted": True, "copy_text": copy_text, "log_path": "memory/gui_bridge", "evidence_path": "learning_agent/test/desktop_gui_shell_v2"},  # 新增代码+GuiDiagnostics：提供复制包和相对目录；如果没有这行代码，设置/诊断页复制按钮没有数据来源。
    }  # 新增代码+GuiDiagnostics：诊断 payload 结束；如果没有这行代码，字典语法不完整。
# 新增代码+GuiDiagnostics：函数段结束，build_gui_diagnostics_payload 到此结束；如果没有这个边界，初学者不容易看出诊断生成范围。
