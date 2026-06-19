"""Computer Use MCP v2 统一运行时分发。"""  # 新增代码+ComputerUseMcpV2：说明本文件是 stdio 和 agent-side 共用执行入口；如果没有这行代码，两个入口可能分裂。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，循环导入更容易失败。

import re  # 新增代码+AcceptanceEventEvidence：用于从低敏 reason 文本提取 key=value 验收字段；如果没有这一行，事件 payload 无法稳定携带 low_level_event_count。
import time  # 新增代码+ComputerUseMcpV2：导入时间模块用于 wait；如果没有这行代码，wait 工具无法真正等待。
from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，runtime 参数边界不清楚。

from .actions import perform_action  # 新增代码+ComputerUseMcpV2：导入鼠标键盘动作；如果没有这行代码，动作类工具无法执行。
from .applications import open_application  # 新增代码+ComputerUseMcpV2：导入应用启动；如果没有这行代码，open_application 无法分发。
from .batch import run_batch  # 新增代码+ComputerUseMcpV2：导入批量执行；如果没有这行代码，computer_batch 无法执行。
from .build_tools import COMPUTER_USE_MCP_TOOL_NAMES, FORBIDDEN_LEGACY_RAW_TOOL_NAMES  # 新增代码+ComputerUseMcpV2：导入允许和禁止工具清单；如果没有这行代码，runtime 无法做硬边界判断。
from .clipboard import read_clipboard, write_clipboard  # 新增代码+ComputerUseMcpV2：导入剪贴板读写；如果没有这行代码，剪贴板工具无法执行。
from .desktop_task import DESKTOP_TASK_STAGE_EVIDENCE_KEYS, run_desktop_task  # 新增代码+DesktopTaskMcpTool: 导入高层桌面任务入口和低敏证据字段；如果没有这一行，runtime 无法把自然语言任务送入 Stage Runtime。
from .errors import error_result  # 新增代码+ComputerUseMcpV2：导入统一失败结果；如果没有这行代码，runtime 失败格式会漂移。
from .observation import observe  # 新增代码+ComputerUseMcpV2：导入观察工具；如果没有这行代码，observe/screenshot 无法执行。
from .permissions import list_granted_applications, request_access  # 新增代码+ComputerUseMcpV2：导入权限工具；如果没有这行代码，授权类工具无法执行。
from .claudecode_protocol import CLAUDECODE_DEFERS_LOCK_TOOLS  # 新增代码+ClaudeCodeLockParity：导入只检查锁不取锁的工具集合；如果没有这行代码，request_access/list_granted 会错误抢占桌面锁。
from .protocol_normalizer import normalize_computer_use_arguments  # 新增代码+ClaudeCodeProtocolParity：导入 ClaudeCode 参数归一化入口；如果没有这行代码，runtime 会继续把 coordinate/region/bundle_id 当未知字段传下去。
from .result_blocks import success_result  # 新增代码+ComputerUseMcpV2：导入统一成功结果；如果没有这行代码，wait 等工具会手写结果。
from .telemetry import emit_acceptance, record_trace  # 新增代码+ComputerUseMcpV2：导入 trace 和验收事件；如果没有这行代码，执行证据链不会写入。
from .types import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2：导入上下文并在本模块重导出；如果没有这行代码，测试和 wrapper 无法构造上下文。


def normalize_tool_name(tool_name: str) -> str:  # 新增代码+ComputerUseMcpV2：函数段开始，统一处理前缀工具名；如果没有这段函数，mcp__computer-use__xxx 和 xxx 会分裂。
    return str(tool_name or "").strip().removeprefix("mcp__computer-use__")  # 新增代码+ComputerUseMcpV2：去掉 registry 前缀；如果没有这行代码，agent-side 调用会被误判未知。
# 新增代码+ComputerUseMcpV2：函数段结束，normalize_tool_name 到此结束；如果没有这个边界说明，用户不容易看出命名规范范围。


def _dict_result(value: Any) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParity：函数段开始，把锁回调返回值规范成字典；如果没有这段函数，None 或非字典结果会污染 debug。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+ClaudeCodeLockParity：只复制字典返回值；如果没有这行代码，坏回调结果会触发属性错误。
# 新增代码+ClaudeCodeLockParity：函数段结束，_dict_result 到此结束；如果没有这个边界说明，用户不容易看出锁回调规范化范围。


def _lock_success(mode: str, payload: dict[str, Any]) -> bool:  # 新增代码+ClaudeCodeLockParity：函数段开始，判断 check/acquire 是否允许继续；如果没有这段函数，锁结果字段解释会散落在 runtime。
    if mode == "acquire" and "acquired" in payload:  # 新增代码+ClaudeCodeLockParity：acquire 优先看 acquired 字段；如果没有这行代码，底层 lock_manager.acquire 的失败可能被误判成功。
        return bool(payload.get("acquired"))  # 新增代码+ClaudeCodeLockParity：返回 acquired 布尔值；如果没有这行代码，锁失败无法阻断动作。
    if "ok" in payload:  # 新增代码+ClaudeCodeLockParity：兼容通用 ok 字段；如果没有这行代码，测试或未来后端的 ok=false 可能被忽略。
        return bool(payload.get("ok"))  # 新增代码+ClaudeCodeLockParity：返回 ok 布尔值；如果没有这行代码，失败状态会继续执行工具。
    if "allowed" in payload:  # 新增代码+ClaudeCodeLockParity：兼容 allowed 字段；如果没有这行代码，只检查锁的拒绝结果可能被忽略。
        return bool(payload.get("allowed"))  # 新增代码+ClaudeCodeLockParity：返回 allowed 布尔值；如果没有这行代码，锁检查拒绝无法生效。
    return True  # 新增代码+ClaudeCodeLockParity：没有显式失败字段时按允许继续处理；如果没有这行代码，轻量回调返回摘要会被误判失败。
# 新增代码+ClaudeCodeLockParity：函数段结束，_lock_success 到此结束；如果没有这个边界说明，用户不容易看出锁成功判定范围。


def _lock_error_result(tool_name: str, lock_payload: dict[str, Any], lock_debug: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParity：函数段开始，生成锁不可用错误；如果没有这段函数，取锁失败可能被每个工具重复包装且字段不一致。
    result = error_result(tool_name, "computer_use_lock_unavailable", error_class="computer_use_lock_unavailable")  # 新增代码+ClaudeCodeLockParity：创建稳定锁失败错误；如果没有这行代码，调用方无法按错误类别恢复。
    result["payload"] = {"lock": dict(lock_payload), "desktop_action_performed": False}  # 新增代码+ClaudeCodeLockParity：明确没有执行桌面副作用；如果没有这行代码，验收可能误以为鼠标键盘已触发。
    result["debug"] = dict(lock_debug)  # 新增代码+ClaudeCodeLockParity：保留锁后端和模式调试信息；如果没有这行代码，排查时不知道是 check 还是 acquire 失败。
    return result  # 新增代码+ClaudeCodeLockParity：返回锁失败结果；如果没有这行代码，runtime 拿不到可返回对象。
# 新增代码+ClaudeCodeLockParity：函数段结束，_lock_error_result 到此结束；如果没有这个边界说明，用户不容易看出锁失败格式范围。


def _prepare_computer_use_lock(context: ComputerUseMcpV2Context, tool_name: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:  # 新增代码+ClaudeCodeLockParity：函数段开始，根据工具名执行 check 或 acquire；如果没有这段函数，ClaudeCode defers-lock 语义无法落地。
    lock_mode = "check" if tool_name in CLAUDECODE_DEFERS_LOCK_TOOLS else "acquire"  # 新增代码+ClaudeCodeLockParity：request/list 只检查，其它工具取锁；如果没有这行代码，授权查询会不必要地占用桌面锁。
    callback = context.check_computer_use_lock if lock_mode == "check" else context.acquire_computer_use_lock  # 新增代码+ClaudeCodeLockParity：选择对应锁回调；如果没有这行代码，runtime 无法区分检查和取锁。
    lock_debug: dict[str, Any] = {"lock_mode": lock_mode, "lock_backend": "unavailable", "tool_name": str(tool_name)}  # 新增代码+ClaudeCodeLockParity：预置 no-op 调试信息；如果没有这行代码，缺回调时结果不会说明锁后端不可用。
    if not callable(callback):  # 新增代码+ClaudeCodeLockParity：允许没有 agent 锁回调的测试/stdio 场景继续运行；如果没有这行代码，纯函数调用会崩溃。
        return None, lock_debug  # 新增代码+ClaudeCodeLockParity：缺回调时安全 no-op；如果没有这行代码，fallback 路径无法返回。
    try:  # 新增代码+ClaudeCodeLockParity：捕获锁后端异常；如果没有这行代码，锁文件错误会抛出裸异常中断工具调用。
        lock_payload = _dict_result(callback(tool_name))  # 新增代码+ClaudeCodeLockParity：调用 check/acquire 并规范化结果；如果没有这行代码，锁语义不会真正执行。
    except Exception as error:  # 新增代码+ClaudeCodeLockParity：处理锁后端异常；如果没有这行代码，调用方看不到稳定 lock_unavailable 错误。
        lock_payload = {"ok": False, "reason": str(error), "error_class": type(error).__name__}  # 新增代码+ClaudeCodeLockParity：把异常转换成结构化锁失败；如果没有这行代码，debug 只有异常文本没有字段。
    lock_debug.update({"lock_backend": str(lock_payload.get("lock_backend") or "callback"), "lock_result": dict(lock_payload)})  # 新增代码+ClaudeCodeLockParity：记录锁后端和原始结果；如果没有这行代码，审计无法复盘锁判断。
    if not _lock_success(lock_mode, lock_payload):  # 新增代码+ClaudeCodeLockParity：锁检查或取锁失败时阻断工具；如果没有这行代码，锁被占用时仍会触碰桌面。
        return _lock_error_result(tool_name, lock_payload, lock_debug), lock_debug  # 新增代码+ClaudeCodeLockParity：返回可直接结束分发的错误；如果没有这行代码，失败路径会继续向下执行。
    if lock_mode == "acquire" and callable(context.is_lock_held_locally):  # 新增代码+ClaudeCodeLockParity：acquire 成功后可查询本会话持锁状态；如果没有这行代码，debug 看不到本地锁是否真的持有。
        lock_debug["lock_held_locally"] = bool(context.is_lock_held_locally(tool_name))  # 新增代码+ClaudeCodeLockParity：写入本地持锁布尔值；如果没有这行代码，诊断时无法区分 acquire 返回和本地状态。
    if lock_mode == "acquire" and callable(context.register_global_escape_abort):  # 新增代码+ClaudeCodeLifecycleParity：动作或观察工具拿到锁后注册全局 Esc；如果没有这一行，用户无法用 Esc 可靠中断 Computer Use。
        try:  # 新增代码+ClaudeCodeLifecycleParity：保护 Esc 注册后端；如果没有这一行，热键注册异常会让普通 observe/click 崩溃。
            escape_report = _dict_result(context.register_global_escape_abort(tool_name))  # 新增代码+ClaudeCodeLifecycleParity：调用绑定到 Windows runtime 的注册回调；如果没有这一行，Esc 控制器不会进入主链路。
        except Exception as error:  # 新增代码+ClaudeCodeLifecycleParity：把异常转换成 debug 报告；如果没有这一行，真实后端错误无法审计。
            escape_report = {"global_hotkey_registered": False, "reason": str(error), "error_class": type(error).__name__}  # 新增代码+ClaudeCodeLifecycleParity：记录失败但不扩大副作用；如果没有这一行，用户不知道 Esc 为什么不可用。
        lock_debug["escape_abort"] = escape_report  # 新增代码+ClaudeCodeLifecycleParity：把 Esc 注册结果写入工具 debug；如果没有这一行，验收无法证明 register 发生过。
    return None, lock_debug  # 新增代码+ClaudeCodeLockParity：返回无错误和锁 debug；如果没有这行代码，正常路径无法继续分发。
# 新增代码+ClaudeCodeLockParity：函数段结束，_prepare_computer_use_lock 到此结束；如果没有这个边界说明，用户不容易看出锁准备范围。


def _merge_lock_debug(result: dict[str, Any], lock_debug: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParity：函数段开始，把锁 debug 合并进工具结果；如果没有这段函数，模型看不到每次工具的锁语义。
    existing_debug = result.get("debug") if isinstance(result.get("debug"), dict) else {}  # 新增代码+ClaudeCodeLockParity：读取已有 debug，例如 screenshot artifact；如果没有这行代码，图片调试信息可能被覆盖。
    merged_debug = dict(existing_debug)  # 新增代码+ClaudeCodeLockParity：复制已有 debug；如果没有这行代码，后续更新可能污染原字典引用。
    merged_debug.update(lock_debug)  # 新增代码+ClaudeCodeLockParity：追加锁模式和后端信息；如果没有这行代码，结果缺少 lock_mode/lock_backend。
    result["debug"] = merged_debug  # 新增代码+ClaudeCodeLockParity：写回合并后的 debug；如果没有这行代码，锁信息不会出现在最终结果。
    return result  # 新增代码+ClaudeCodeLockParity：返回同一个结果对象；如果没有这行代码，调用方拿不到合并结果。
# 新增代码+ClaudeCodeLockParity：函数段结束，_merge_lock_debug 到此结束；如果没有这个边界说明，用户不容易看出 debug 合并范围。


def _bounded_acceptance_text(value: Any, limit: int = 1200) -> str:  # 新增代码+AcceptanceEventEvidence：函数段开始，把工具失败原因裁剪成验收可记录的低敏文本；如果没有这段函数，事件可能写入过长工具结果。
    text = str(value or "").strip()  # 新增代码+AcceptanceEventEvidence：把任意输入转成干净字符串；如果没有这一行，None 或非字符串会导致后续切片不稳定。
    if len(text) <= int(limit):  # 新增代码+AcceptanceEventEvidence：判断文本是否已经在安全长度内；如果没有这一行，短 reason 也会被无意义处理。
        return text  # 新增代码+AcceptanceEventEvidence：短文本原样返回；如果没有这一行，调用方拿不到完整 marker。
    return text[: int(limit)] + "...[truncated]"  # 新增代码+AcceptanceEventEvidence：长文本只保留开头并标记截断；如果没有这一行，事件 payload 可能膨胀到难以解析。
# 新增代码+AcceptanceEventEvidence：函数段结束，_bounded_acceptance_text 到此结束；如果没有这个边界说明，用户不容易看出文本裁剪范围。


def _extract_key_value_from_text(text: str, key: str) -> str:  # 新增代码+AcceptanceEventEvidence：函数段开始，从 reason 的 key=value 行提取字段；如果没有这段函数，验收事件无法拿到资源决策和低层事件数。
    pattern = rf"(?:^|\n){re.escape(key)}\s*=\s*([^\n\r]+)"  # 新增代码+AcceptanceEventEvidence：构造只匹配整行 key=value 的正则；如果没有这一行，字段提取可能误命中正文。
    match = re.search(pattern, str(text or ""))  # 新增代码+AcceptanceEventEvidence：在 reason 文本中搜索字段；如果没有这一行，函数没有数据来源。
    return match.group(1).strip() if match else ""  # 新增代码+AcceptanceEventEvidence：命中时返回值，否则返回空字符串；如果没有这一行，调用方要重复处理 None。
# 新增代码+AcceptanceEventEvidence：函数段结束，_extract_key_value_from_text 到此结束；如果没有这个边界说明，用户不容易看出字段提取范围。


def _safe_int_or_none(value: Any) -> int | None:  # 新增代码+AcceptanceEventEvidence：函数段开始，把低层事件数字符串转成 int；如果没有这段函数，坏字段会让 runtime 事件发射失败。
    try:  # 新增代码+AcceptanceEventEvidence：捕获非数字或空值；如果没有这一行，ValueError 会中断工具返回。
        return int(str(value).strip())  # 新增代码+AcceptanceEventEvidence：执行安全整数转换；如果没有这一行，event payload 的 low_level_event_count 只能是字符串。
    except (TypeError, ValueError):  # 新增代码+AcceptanceEventEvidence：处理无法转换的输入；如果没有这一行，异常会冒泡到模型工具调用。
        return None  # 新增代码+AcceptanceEventEvidence：转换失败时返回 None；如果没有这一行，调用方无法区分 0 和坏值。
# 新增代码+AcceptanceEventEvidence：函数段结束，_safe_int_or_none 到此结束；如果没有这个边界说明，用户不容易看出数字转换范围。


def _acceptance_payload_for_tool_result(tool_name: str, result: dict[str, Any]) -> dict[str, Any]:  # 新增代码+AcceptanceEventEvidence：函数段开始，为真实终端验收事件生成低敏工具摘要；如果没有这段函数，事件只能看到 ok=false 而看不到为什么安全停止。
    event_payload = {"tool_name": str(tool_name), "ok": bool(result.get("ok"))}  # 新增代码+AcceptanceEventEvidence：保留原有工具名和成功状态；如果没有这一行，旧验收场景会失去基础字段。
    error_class = str(result.get("error_class", "") or "").strip()  # 新增代码+AcceptanceEventEvidence：读取稳定错误分类；如果没有这一行，验收无法区分资源拒绝和普通失败。
    if error_class:  # 新增代码+AcceptanceEventEvidence：只在存在错误分类时写入；如果没有这一行，成功事件会多出空字段噪音。
        event_payload["error_class"] = error_class  # 新增代码+AcceptanceEventEvidence：把错误分类写入事件；如果没有这一行，controller 无法按失败类型断言。
    result_payload = result.get("payload") if isinstance(result.get("payload"), dict) else {}  # 新增代码+AcceptanceEventEvidence：读取工具 payload；如果没有这一行，缺顶层 reason 时无法降级取 payload reason。
    reason_text = _bounded_acceptance_text(result.get("reason") or result_payload.get("reason") or "")  # 新增代码+AcceptanceEventEvidence：优先取顶层或 payload 里的低敏原因；如果没有这一行，资源 marker 不会进入事件。
    if reason_text:  # 新增代码+AcceptanceEventEvidence：只在有原因文本时写入；如果没有这一行，成功事件会多出空 reason。
        event_payload["reason"] = reason_text  # 新增代码+AcceptanceEventEvidence：把裁剪后的原因写入事件；如果没有这一行，scenario 无法搜索资源阻断 marker。
    resource_decision = _extract_key_value_from_text(reason_text, "resource_freshness_decision")  # 新增代码+AcceptanceEventEvidence：提取资源新鲜度决策；如果没有这一行，事件不能证明为什么停止。
    if resource_decision:  # 新增代码+AcceptanceEventEvidence：只在找到决策时写入；如果没有这一行，普通失败事件会多出空决策字段。
        event_payload["resource_freshness_decision"] = resource_decision  # 新增代码+AcceptanceEventEvidence：把资源决策写入事件；如果没有这一行，controller 只能翻 debug log。
    low_level_count = _safe_int_or_none(_extract_key_value_from_text(reason_text, "low_level_event_count"))  # 新增代码+AcceptanceEventEvidence：提取并转换低层事件数；如果没有这一行，事件不能证明零键鼠动作。
    if low_level_count is not None:  # 新增代码+AcceptanceEventEvidence：只在字段有效时写入；如果没有这一行，坏值可能污染事件。
        event_payload["low_level_event_count"] = low_level_count  # 新增代码+AcceptanceEventEvidence：写入整数低层事件数；如果没有这一行，真实验收无法断言没有误操作旧窗口。
    if tool_name == "desktop_task" and isinstance(result_payload, dict):  # 新增代码+DesktopTaskMcpTool: 高层任务事件额外暴露阶段证据；如果没有这一行，acceptance controller 只能看到 ok 而看不到 Stage Runtime 字段。
        for key in DESKTOP_TASK_STAGE_EVIDENCE_KEYS:  # 新增代码+DesktopTaskMcpTool: 遍历允许外露的低敏字段；如果没有这一行，字段复制会散落重复代码。
            if key in result_payload:  # 新增代码+DesktopTaskMcpTool: 只复制实际存在的证据字段；如果没有这一行，事件里会充满空噪音。
                event_payload[key] = result_payload.get(key)  # 新增代码+DesktopTaskMcpTool: 写入阶段证据到验收事件；如果没有这一行，真实终端验收无法断言阶段规划和批执行。
    return event_payload  # 新增代码+AcceptanceEventEvidence：返回低敏事件摘要；如果没有这一行，dispatch 无法发送增强事件。
# 新增代码+AcceptanceEventEvidence：函数段结束，_acceptance_payload_for_tool_result 到此结束；如果没有这个边界说明，用户不容易看出事件摘要范围。


def cleanup_computer_use_mcp_v2_turn(context: ComputerUseMcpV2Context | None = None, reason: str = "turn cleanup") -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParity：函数段开始，执行 ClaudeCode 风格 turn-end cleanup；如果没有这段函数，长任务结束后缺少统一释放锁入口。
    runtime_context = context or ComputerUseMcpV2Context()  # 新增代码+ClaudeCodeLockParity：缺省创建安全上下文；如果没有这行代码，纯测试调用 None 会崩溃。
    safe_reason = str(reason or "turn cleanup")  # 新增代码+ClaudeCodeLockParity：清理 reason 文本；如果没有这行代码，回调可能收到 None 或奇怪对象。
    runtime_context.display_pinned_by_model = False  # 新增代码+ClaudeCodeDisplayParity：turn cleanup 只清理模型临时固定显示器状态；如果没有这行代码，displayPinnedByModel 会跨 turn 残留并误导后续观察。
    if callable(runtime_context.cleanup_after_turn):  # 新增代码+ClaudeCodeLockParity：优先使用完整 cleanup 回调；如果没有这行代码，host unhide/abort 清理等完整流程会被绕过。
        return _dict_result(runtime_context.cleanup_after_turn(safe_reason)) or {"cleanup_completed": True, "reason": safe_reason}  # 新增代码+ClaudeCodeLockParity：返回完整 cleanup 结果并兜底成功摘要；如果没有这行代码，调用方无法确认清理完成。
    if callable(runtime_context.release_computer_use_lock):  # 新增代码+ClaudeCodeLockParity：没有完整 cleanup 时使用释放锁兜底；如果没有这行代码，轻量上下文无法释放锁。
        release_result = _dict_result(runtime_context.release_computer_use_lock(safe_reason))  # 新增代码+ClaudeCodeLockParity：调用释放锁回调；如果没有这行代码，锁不会被释放。
        return {"cleanup_completed": bool(release_result.get("released", True)), "lock_released": bool(release_result.get("released", True)), "release": release_result, "reason": safe_reason}  # 新增代码+ClaudeCodeLockParity：返回轻量 cleanup 摘要；如果没有这行代码，调用方不知道释放结果。
    return {"cleanup_completed": True, "lock_released": False, "reason": safe_reason, "debug": {"lock_backend": "unavailable", "lock_mode": "cleanup"}}  # 新增代码+ClaudeCodeLockParity：无回调时安全 no-op；如果没有这行代码，stdio/测试场景无法完成 cleanup 调用。
# 新增代码+ClaudeCodeLockParity：函数段结束，cleanup_computer_use_mcp_v2_turn 到此结束；如果没有这个边界说明，用户不容易看出 turn cleanup 范围。


def dispatch_computer_use_mcp_v2_tool(tool_name: str, arguments: dict[str, Any] | None, context: ComputerUseMcpV2Context | None = None) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，执行一个 v2 MCP 工具；如果没有这段函数，server 和 agent-side wrapper 没有统一入口。
    runtime_context = context or ComputerUseMcpV2Context()  # 新增代码+ComputerUseMcpV2：缺省创建上下文；如果没有这行代码，独立 selftest 调用会失败。
    raw_name = normalize_tool_name(tool_name)  # 新增代码+ComputerUseMcpV2：规范工具名；如果没有这行代码，前缀名无法执行。
    safe_arguments = normalize_computer_use_arguments(raw_name, dict(arguments or {}))  # 修改代码+ClaudeCodeProtocolParity：先把 ClaudeCode 字段归一化为 Windows runtime 字段；如果没有这行代码，coordinate/region/bundle_id/apps/actions 无法稳定执行。
    record_trace(runtime_context, "tool_started", {"tool_name": raw_name, "arguments_keys": sorted(safe_arguments.keys())})  # 新增代码+ComputerUseMcpV2：记录开始事件；如果没有这行代码，trace 无法证明 v2 被调用。
    if raw_name in FORBIDDEN_LEGACY_RAW_TOOL_NAMES:  # 新增代码+ComputerUseMcpV2：硬拒绝旧接口和蓝图外接口；如果没有这行代码，隐藏工具可被直接调用。
        result = error_result(raw_name, f"legacy_or_forbidden_tool:{raw_name}", error_class="legacy_tool_forbidden")  # 新增代码+ComputerUseMcpV2：构造 legacy 拒绝；如果没有这行代码，模型不知道为什么被拒绝。
    elif raw_name not in COMPUTER_USE_MCP_TOOL_NAMES:  # 新增代码+ComputerUseMcpV2：检查是否属于 v2 清单；如果没有这行代码，未知工具可能落入动作层。
        result = error_result(raw_name, f"unknown_computer_use_mcp_v2_tool:{raw_name}", error_class="unknown_tool")  # 新增代码+ComputerUseMcpV2：构造未知工具拒绝；如果没有这行代码，未知调用可能假成功。
    else:  # 新增代码+ComputerUseMcpV2：剩余都是鼠标键盘动作；如果没有这行代码，动作工具无法进入执行层。
        lock_error, lock_debug = _prepare_computer_use_lock(runtime_context, raw_name)  # 新增代码+ClaudeCodeLockParity：合法工具执行前先按 ClaudeCode 语义检查或取锁；如果没有这行代码，动作/观察可能绕过独占锁。
        if lock_error is not None:  # 新增代码+ClaudeCodeLockParity：锁失败时不继续分发；如果没有这行代码，锁被占用仍会触碰桌面。
            result = lock_error  # 新增代码+ClaudeCodeLockParity：使用锁失败结果；如果没有这行代码，后续 record_trace 没有结果对象。
        elif raw_name == "request_access":  # 新增代码+ComputerUseMcpV2：分发授权申请；如果没有这行代码，request_access 无法执行。
            result = request_access(runtime_context, safe_arguments)  # 新增代码+ComputerUseMcpV2：执行授权申请；如果没有这行代码，权限回调不会被调用。
        elif raw_name == "list_granted_applications":  # 新增代码+ComputerUseMcpV2：分发授权查询；如果没有这行代码，授权状态无法查看。
            result = list_granted_applications(runtime_context)  # 新增代码+ComputerUseMcpV2：执行授权查询；如果没有这行代码，模型拿不到 grant 摘要。
        elif raw_name in {"observe", "screenshot", "zoom"}:  # 修改代码+ClaudeCodeZoom：把 zoom 纳入只读观察类分发；如果没有这行代码，zoom 虽标 readOnly 但运行时仍像动作工具一样缺观察记录。
            result = observe(runtime_context, raw_name, safe_arguments)  # 新增代码+ComputerUseMcpV2：执行观察；如果没有这行代码，主循环拿不到桌面状态。
        elif raw_name == "wait":  # 新增代码+ComputerUseMcpV2：分发等待工具；如果没有这行代码，wait 会被误判未知。
            seconds = max(0.0, min(float(safe_arguments.get("seconds", 1) or 0), 30.0))  # 新增代码+ComputerUseMcpV2：限制等待时长；如果没有这行代码，模型可能让 server 长时间卡住。
            time.sleep(seconds)  # 新增代码+ComputerUseMcpV2：执行等待；如果没有这行代码，wait 不会给界面加载时间。
            result = success_result("wait", {"waited_seconds": seconds})  # 新增代码+ComputerUseMcpV2：返回等待摘要；如果没有这行代码，模型不知道等待完成。
        elif raw_name == "read_clipboard":  # 新增代码+ComputerUseMcpV2：分发读剪贴板；如果没有这行代码，read_clipboard 无法执行。
            result = read_clipboard(runtime_context)  # 新增代码+ComputerUseMcpV2：执行剪贴板读取；如果没有这行代码，模型拿不到剪贴板内容。
        elif raw_name == "write_clipboard":  # 新增代码+ComputerUseMcpV2：分发写剪贴板；如果没有这行代码，write_clipboard 无法执行。
            result = write_clipboard(runtime_context, str(safe_arguments.get("text", "")))  # 新增代码+ComputerUseMcpV2：执行剪贴板写入；如果没有这行代码，后续读取不会变化。
        elif raw_name == "open_application":  # 新增代码+ComputerUseMcpV2：分发应用启动；如果没有这行代码，open_application 无法执行。
            result = open_application(runtime_context, safe_arguments)  # 新增代码+ComputerUseMcpV2：执行应用启动；如果没有这行代码，目标应用不会打开。
        elif raw_name == "desktop_task":  # 新增代码+DesktopTaskMcpTool: 分发完整自然语言桌面任务；如果没有这一行，模型可见新工具也无法执行。
            result = run_desktop_task(runtime_context, safe_arguments)  # 新增代码+DesktopTaskMcpTool: 执行通用阶段规划、观察、批执行和验证；如果没有这一行，Stage Runtime 不会进入真实 MCP 主链路。
        elif raw_name == "computer_batch":  # 新增代码+ComputerUseMcpV2：分发批量工具；如果没有这行代码，computer_batch 无法执行。
            result = run_batch(runtime_context, safe_arguments, dispatch_computer_use_mcp_v2_tool)  # 新增代码+ComputerUseMcpV2：执行批量动作；如果没有这行代码，多步任务无法顺序执行。
        else:  # 新增代码+ComputerUseMcpV2：剩余都是鼠标键盘动作；如果没有这行代码，动作工具无法进入执行层。
            result = perform_action(runtime_context, raw_name, safe_arguments)  # 新增代码+ComputerUseMcpV2：执行原子动作；如果没有这行代码，click/type/key 等不会运行。
        result = _merge_lock_debug(result, lock_debug)  # 新增代码+ClaudeCodeLockParity：把锁模式和后端写入最终结果；如果没有这行代码，锁生命周期不可观测。
    record_trace(runtime_context, "tool_completed", {"tool_name": raw_name, "ok": bool(result.get("ok")), "error_class": result.get("error_class", "")})  # 新增代码+ComputerUseMcpV2：记录完成事件；如果没有这行代码，trace 看不到结果。
    emit_acceptance(runtime_context, "computer_use_mcp_v2_tool", _acceptance_payload_for_tool_result(raw_name, result))  # 修改代码+AcceptanceEventEvidence：发送带低敏失败摘要的验收事件；如果没有这行代码，真实终端验收看不到资源阻断 marker 和零事件证据。
    return result  # 新增代码+ComputerUseMcpV2：返回工具结果；如果没有这行代码，调用方拿不到执行输出。
# 新增代码+ComputerUseMcpV2：函数段结束，dispatch_computer_use_mcp_v2_tool 到此结束；如果没有这个边界说明，用户不容易看出 runtime 分发范围。
