"""浏览器动作执行器，负责动作生命周期事件和中断/失败状态。"""  # 新增代码+BrowserActionStage6: 说明本模块负责工具执行事件流；若没有这行代码，执行器边界不清楚。

from __future__ import annotations  # 新增代码+BrowserActionStage6: 延迟解析类型注解；若没有这行代码，类型引用更脆弱。

import time  # 新增代码+BrowserActionExecuteLayer: 执行器重试时需要短暂退避；若没有这行代码，重试会立即撞上同一个瞬时页面状态。
import threading  # 新增代码+BrowserActionStage6: 写操作串行锁需要线程锁；若没有这行代码，并发动作无法受控。
from collections.abc import Callable, Iterable  # 修改代码+BrowserActionStreaming: 标注真实工具 handler、回调函数和可迭代分段输出；若没有这行代码，流式结果识别边界不清楚。
from concurrent.futures import ThreadPoolExecutor  # 新增代码+BrowserActionBatch: 批量只读工具需要线程池并发执行；若没有这行代码，批处理只能继续串行执行。
from typing import Any  # 新增代码+BrowserActionStage6: 工具参数和事件 payload 是通用 JSON；若没有这行代码，类型边界不清楚。

from learning_agent.browser.action_policy import BrowserActionPolicy  # 新增代码+BrowserActionStage6: 导入动作策略；若没有这行代码，执行器无法区分读写。
from learning_agent.browser.runtime_models import BrowserAction  # 新增代码+BrowserActionStage6: 导入动作协议模型；若没有这行代码，动作状态无法落盘。
from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+BrowserActionStage6: 导入可选持久 store；若没有这行代码，事件无法写入浏览器 runtime。


class BrowserActionExecutor:  # 新增代码+BrowserActionStage6: 管理浏览器动作生命周期；若没有这个类，browser server 会继续散落事件写入。
    def __init__(self, store: BrowserRuntimeStore | None = None, policy: BrowserActionPolicy | None = None) -> None:  # 新增代码+BrowserActionStage6: 初始化执行器依赖；若没有这行代码，测试和生产无法指定 store。
        self.store = store  # 新增代码+BrowserActionStage6: 保存可选持久 store；若没有这行代码，事件无法落盘。
        self.policy = policy or BrowserActionPolicy()  # 新增代码+BrowserActionStage6: 保存动作策略；若没有这行代码，执行器无法知道是否串行。
        self.write_lock = threading.RLock()  # 修改代码+BrowserActionExecuteLayer: 为写动作准备可重入串行锁；若没有这行代码，browser_flow_run 这类外层工具嵌套调用内层浏览器工具时会把自己锁死。
        self.events: list[dict[str, Any]] = []  # 新增代码+BrowserActionStage6: 保存无 store 模式下的内存事件；若没有这行代码，轻量测试和调试无从观察。

    def begin_action(self, run_id: str, stage_id: str, tool_name: str, arguments: dict[str, Any] | None = None, action_id: str | None = None) -> BrowserAction:  # 修改代码+BrowserActionExecutorDelegation: 创建动作时允许 server 传入稳定 action_id；若没有这行代码，委托后 run/action/observation 关联会变成随机编号。
        action = BrowserAction.create(run_id=run_id, stage_id=stage_id, tool_name=tool_name, arguments=arguments, action_id=action_id)  # 修改代码+BrowserActionExecutorDelegation: 构建脱敏动作对象并复用调用方 id；若没有这行代码，server 分配的可读 action id 不会生效。
        action.mark_started()  # 新增代码+BrowserActionStage6: 标记 running 状态；若没有这行代码，状态页看不到工具正在执行。
        self._record(action, "browser_action_started", {"serial": self.policy.requires_serial(tool_name)})  # 新增代码+BrowserActionStage6: 写 started 事件和策略摘要；若没有这行代码，事件流无法审计动作开始。
        return action  # 新增代码+BrowserActionStage6: 返回动作对象给调用方继续完成/失败；若没有这行代码，后续状态无法更新同一个动作。

    def record_progress(self, action: BrowserAction, message: str, payload: dict[str, Any] | None = None) -> None:  # 新增代码+BrowserActionStage6: 记录长工具中间进度；若没有这行代码，流式工具执行不可见。
        self._record(action, "browser_action_progress", {"message": str(message), "payload": dict(payload or {})})  # 新增代码+BrowserActionStage6: 写 progress 事件；若没有这行代码，用户不知道工具卡在哪一步。

    def complete_action(self, action: BrowserAction, observation_id: str = "") -> BrowserAction:  # 新增代码+BrowserActionStage6: 标记动作成功完成；若没有这行代码，成功事件无法统一落盘。
        action.mark_completed(observation_id=observation_id)  # 新增代码+BrowserActionStage6: 更新动作状态和 observation 关联；若没有这行代码，成功后证据断链。
        self._record(action, "browser_action_completed", {"observation_id": observation_id})  # 新增代码+BrowserActionStage6: 写 completed 事件；若没有这行代码，结果回灌缺少事实依据。
        return action  # 新增代码+BrowserActionStage6: 返回更新后的动作；若没有这行代码，调用方无法继续使用状态。

    def fail_action(self, action: BrowserAction, error_type: str, error_message: str) -> BrowserAction:  # 新增代码+BrowserActionStage6: 标记动作失败；若没有这行代码，恢复管理器无法读取失败证据。
        action.mark_failed(str(error_type), str(error_message))  # 新增代码+BrowserActionStage6: 更新失败类型和信息；若没有这行代码，动作状态会停在 running。
        self._record(action, "browser_action_failed", {"error_type": action.error_type, "error_message": action.error_message})  # 新增代码+BrowserActionStage6: 写 failed 事件；若没有这行代码，状态页看不到失败原因。
        return action  # 新增代码+BrowserActionStage6: 返回失败动作；若没有这行代码，调用方无法检查状态。

    def interrupt_action(self, action: BrowserAction, message: str = "interrupted") -> BrowserAction:  # 新增代码+BrowserActionStage6: 标记动作中断；若没有这行代码，中断恢复无法区别普通失败。
        action.mark_interrupted(str(message))  # 新增代码+BrowserActionStage6: 更新中断状态；若没有这行代码，动作会被误判为失败或 running。
        self._record(action, "browser_action_interrupted", {"message": str(message)})  # 新增代码+BrowserActionStage6: 写 interrupted 事件；若没有这行代码，恢复时没有中断证据。
        return action  # 新增代码+BrowserActionStage6: 返回中断动作；若没有这行代码，调用方无法检查状态。

    def execute_action(self, run_id: str, stage_id: str, tool_name: str, arguments: dict[str, Any] | None, handler: Callable[[dict[str, Any]], Any], action_id: str | None = None, attempts_limit: int = 1, is_retryable_error: Callable[[Exception], bool] | None = None, classify_error: Callable[[Exception], str] | None = None, redact_output: Callable[[str], str] | None = None, observation_id_getter: Callable[[BrowserAction], str] | None = None, on_action_started: Callable[[BrowserAction], None] | None = None, on_action_finished: Callable[[BrowserAction], None] | None = None, on_attempt_success: Callable[[BrowserAction, int, str], None] | None = None, on_attempt_error: Callable[[BrowserAction, int, Exception, str], None] | None = None, on_result_chunk: Callable[[BrowserAction, int, str], None] | None = None, retry_delay_seconds: float = 0.0) -> tuple[str, BrowserAction]:  # 修改代码+BrowserActionStreaming: 统一接管动作执行并允许分段结果回调；若没有这行代码，server 仍会直接调用工具 handler 且 UI/SDK 看不到流式输出。
        action = self.begin_action(run_id, stage_id, tool_name, arguments, action_id=action_id)  # 新增代码+BrowserActionExecuteLayer: 先创建并记录 started action；若没有这行代码，真实执行没有 durable 生命周期入口。
        if on_action_started is not None:  # 新增代码+BrowserActionExecuteLayer: 如果调用方需要知道当前 action；若没有这行代码，server 无法在 handler 执行前关联 observation。
            on_action_started(action)  # 新增代码+BrowserActionExecuteLayer: 通知调用方 action 已开始；若没有这行代码，snapshot/screenshot 证据无法挂回当前 action。
        try:  # 新增代码+BrowserActionExecuteLayer: 确保执行结束后可以清理调用方活动 action；若没有这行代码，异常会让当前 action 残留。
            if self.policy.requires_serial(tool_name):  # 新增代码+BrowserActionExecuteLayer: 写工具和未知工具必须串行；若没有这行代码，点击、输入、导航可能并发污染页面。
                with self.write_lock:  # 新增代码+BrowserActionExecuteLayer: 获取写操作互斥锁；若没有这行代码，多线程写工具会同时操作同一浏览器。
                    return self._execute_attempts(action, arguments, handler, attempts_limit, is_retryable_error, classify_error, redact_output, observation_id_getter, on_attempt_success, on_attempt_error, on_result_chunk, retry_delay_seconds)  # 修改代码+BrowserActionStreaming: 在锁内执行重试循环并透传分段输出回调；若没有这行代码，串行写工具的流式结果不会进入事件流。
            return self._execute_attempts(action, arguments, handler, attempts_limit, is_retryable_error, classify_error, redact_output, observation_id_getter, on_attempt_success, on_attempt_error, on_result_chunk, retry_delay_seconds)  # 修改代码+BrowserActionStreaming: 只读工具直接执行并透传分段输出回调；若没有这行代码，快照类读工具的流式输出不可见。
        finally:  # 新增代码+BrowserActionExecuteLayer: 无论成功失败都通知调用方清理 action；若没有这行代码，失败后 observation 可能误挂旧动作。
            if on_action_finished is not None:  # 新增代码+BrowserActionExecuteLayer: 如果调用方提供清理回调；若没有这行代码，None 回调会被误调用。
                on_action_finished(action)  # 新增代码+BrowserActionExecuteLayer: 通知调用方 action 已结束；若没有这行代码，server 的 current_action_id 可能残留。

    def _execute_attempts(self, action: BrowserAction, arguments: dict[str, Any] | None, handler: Callable[[dict[str, Any]], Any], attempts_limit: int, is_retryable_error: Callable[[Exception], bool] | None, classify_error: Callable[[Exception], str] | None, redact_output: Callable[[str], str] | None, observation_id_getter: Callable[[BrowserAction], str] | None, on_attempt_success: Callable[[BrowserAction, int, str], None] | None, on_attempt_error: Callable[[BrowserAction, int, Exception, str], None] | None, on_result_chunk: Callable[[BrowserAction, int, str], None] | None, retry_delay_seconds: float) -> tuple[str, BrowserAction]:  # 修改代码+BrowserActionStreaming: 执行真实 handler 的重试循环并处理分段输出；若没有这行代码，execute_action 会过长且难测试。
        safe_arguments = dict(arguments or {})  # 新增代码+BrowserActionExecuteLayer: 复制参数避免 handler 修改调用方对象；若没有这行代码，后续审计参数可能被工具污染。
        safe_attempts_limit = max(1, int(attempts_limit or 1))  # 新增代码+BrowserActionExecuteLayer: 至少执行一次；若没有这行代码，0 次重试会让工具不执行。
        attempt = 0  # 新增代码+BrowserActionExecuteLayer: 初始化尝试次数；若没有这行代码，progress 无法说明第几次执行。
        while attempt < safe_attempts_limit:  # 新增代码+BrowserActionExecuteLayer: 按重试预算执行 handler；若没有这行代码，失败恢复不会发生。
            attempt += 1  # 新增代码+BrowserActionExecuteLayer: 进入新尝试前递增计数；若没有这行代码，事件里的 attempt 不准确。
            self.record_progress(action, "attempt_started", {"attempt": attempt, "tool_name": action.tool_name})  # 新增代码+BrowserActionExecuteLayer: 记录每次尝试开始；若没有这行代码，长工具卡顿时用户看不到进度。
            try:  # 新增代码+BrowserActionExecuteLayer: 捕获 handler 成功或失败；若没有这行代码，retry/progress/fail 都无法统一处理。
                raw_result = handler(safe_arguments)  # 新增代码+BrowserActionExecuteLayer: 调用真实浏览器工具；若没有这行代码，execute_action 只会记录不执行。
                safe_result = self._stream_result_text(action, raw_result, redact_output, on_result_chunk)  # 修改代码+BrowserActionStreaming: 把普通结果或分段结果统一转成安全文本；若没有这行代码，流式输出不会写 progress 事件。
                if on_attempt_success is not None:  # 新增代码+BrowserActionExecuteLayer: 如果调用方需要记录旧 action log；若没有这行代码，server 回放日志无法沿用执行器。
                    on_attempt_success(action, attempt, safe_result)  # 新增代码+BrowserActionExecuteLayer: 通知调用方本次尝试成功；若没有这行代码，旧 replay 审计会缺成功记录。
                observation_id = observation_id_getter(action) if observation_id_getter is not None else ""  # 新增代码+BrowserActionExecuteLayer: 完成前读取 observation id；若没有这行代码，snapshot/screenshot 证据无法回填 action。
                self.complete_action(action, observation_id=observation_id)  # 新增代码+BrowserActionExecuteLayer: 标记动作成功完成；若没有这行代码，动作会停留在 running。
                return safe_result, action  # 新增代码+BrowserActionExecuteLayer: 返回安全输出和动作对象；若没有这行代码，server 拿不到工具结果。
            except Exception as error:  # 新增代码+BrowserActionExecuteLayer: 捕获失败以便判断是否可重试；若没有这行代码，瞬时失败会直接冒泡。
                error_text = str(error)  # 新增代码+BrowserActionExecuteLayer: 把异常转成文本；若没有这行代码，进度和失败事件没有错误说明。
                safe_error_text = redact_output(error_text) if redact_output is not None else error_text  # 新增代码+BrowserActionExecuteLayer: 失败文本也要脱敏；若没有这行代码，错误里可能泄露密码或 token。
                if on_attempt_error is not None:  # 新增代码+BrowserActionExecuteLayer: 如果调用方要记录失败尝试；若没有这行代码，旧动作日志看不到失败历史。
                    on_attempt_error(action, attempt, error, safe_error_text)  # 新增代码+BrowserActionExecuteLayer: 通知调用方本次尝试失败；若没有这行代码，server 无法更新恢复摘要。
                retryable = is_retryable_error(error) if is_retryable_error is not None else False  # 新增代码+BrowserActionExecuteLayer: 调用方决定哪些错误可重试；若没有这行代码，执行器会把参数错误也当临时错误。
                if attempt >= safe_attempts_limit or not retryable:  # 新增代码+BrowserActionExecuteLayer: 达到上限或不可重试时失败收尾；若没有这行代码，失败可能无限循环。
                    error_type = classify_error(error) if classify_error is not None else "browser_action_failed"  # 新增代码+BrowserActionExecuteLayer: 生成标准失败分类；若没有这行代码，恢复管理器看不到错误类型。
                    self.fail_action(action, error_type, safe_error_text)  # 新增代码+BrowserActionExecuteLayer: 标记动作最终失败；若没有这行代码，失败 action 会停在 running。
                    raise  # 新增代码+BrowserActionExecuteLayer: 保留原失败语义交给 server/model；若没有这行代码，工具失败会被误报成功。
                self.record_progress(action, "retry_scheduled", {"attempt": attempt, "next_attempt": attempt + 1, "error": safe_error_text[:500]})  # 新增代码+BrowserActionExecuteLayer: 记录即将重试；若没有这行代码，用户看不到自动恢复过程。
                if retry_delay_seconds > 0:  # 新增代码+BrowserActionExecuteLayer: 如果调用方要求退避；若没有这行代码，永远不会等待。
                    time.sleep(float(retry_delay_seconds))  # 新增代码+BrowserActionExecuteLayer: 短暂等待页面状态恢复；若没有这行代码，连续重试可能撞同一个瞬时错误。
        self.fail_action(action, "browser_retry_exhausted", "浏览器动作重试流程异常结束。")  # 新增代码+BrowserActionExecuteLayer: 理论兜底失败收尾；若没有这行代码，静态路径可能无返回。
        raise RuntimeError("浏览器动作重试流程异常结束。")  # 新增代码+BrowserActionExecuteLayer: 理论兜底错误；若没有这行代码，调用方可能拿到空结果。

    def _stream_result_text(self, action: BrowserAction, raw_result: Any, redact_output: Callable[[str], str] | None, on_result_chunk: Callable[[BrowserAction, int, str], None] | None) -> str:  # 新增代码+BrowserActionStreaming: 把工具返回值转换为最终文本并落盘流式片段；若没有这行代码，分段输出处理会散落在重试循环里。
        if raw_result is None:  # 新增代码+BrowserActionStreaming: 兼容没有返回值的工具；若没有这行代码，None 会被转成字符串 "None"。
            return ""  # 新增代码+BrowserActionStreaming: 没有结果时返回空文本；若没有这行代码，MCP 调用方会看到误导性 None。
        if isinstance(raw_result, (str, bytes, dict)) or not isinstance(raw_result, Iterable):  # 新增代码+BrowserActionStreaming: 字符串、字节、字典和非迭代对象按普通结果处理；若没有这行代码，字符串会被错误拆成单字流。
            result_text = raw_result.decode("utf-8", errors="replace") if isinstance(raw_result, bytes) else str(raw_result)  # 新增代码+BrowserActionStreaming: 字节结果按 UTF-8 容错解码，其余对象转文本；若没有这行代码，二进制片段可能显示成 Python bytes 语法。
            return redact_output(result_text) if redact_output is not None else result_text  # 新增代码+BrowserActionStreaming: 普通结果也保持脱敏；若没有这行代码，登录后页面内容可能泄露给模型。
        result_parts: list[str] = []  # 新增代码+BrowserActionStreaming: 保存所有安全片段用于合并最终结果；若没有这行代码，MCP 兼容文本会丢失。
        chunk_index = 0  # 新增代码+BrowserActionStreaming: 初始化片段序号；若没有这行代码，事件流无法按顺序显示片段。
        for raw_chunk in raw_result:  # 新增代码+BrowserActionStreaming: 遍历工具产生的每个输出片段；若没有这行代码，生成器结果不会被消费。
            chunk_index += 1  # 新增代码+BrowserActionStreaming: 为当前片段分配从 1 开始的序号；若没有这行代码，UI/SDK 难以排序。
            chunk_text = "" if raw_chunk is None else str(raw_chunk)  # 新增代码+BrowserActionStreaming: 把片段转成文本；若没有这行代码，None 片段或对象片段会破坏拼接。
            safe_chunk = redact_output(chunk_text) if redact_output is not None else chunk_text  # 新增代码+BrowserActionStreaming: 每个片段单独脱敏；若没有这行代码，敏感信息可能先进入流式事件。
            result_parts.append(safe_chunk)  # 新增代码+BrowserActionStreaming: 保存安全片段用于最终合并；若没有这行代码，调用方只能看到流式事件看不到完整结果。
            self.record_progress(action, "result_chunk", {"chunk_index": chunk_index, "chunk": safe_chunk[:2000]})  # 新增代码+BrowserActionStreaming: 把片段作为 progress 事件落盘；若没有这行代码，长输出无法被状态页逐步观察。
            if on_result_chunk is not None:  # 新增代码+BrowserActionStreaming: 如果调用方提供流式回调则通知它；若没有这行代码，None 回调会被误调用。
                on_result_chunk(action, chunk_index, safe_chunk)  # 新增代码+BrowserActionStreaming: 把安全片段交给上层 UI/SDK；若没有这行代码，外部界面无法即时显示工具输出。
        return "".join(result_parts)  # 新增代码+BrowserActionStreaming: 返回合并后的完整安全结果；若没有这行代码，MCP 兼容返回值会为空。

    def execute_batch(self, run_id: str, stage_id: str, actions: list[dict[str, Any]], action_id_prefix: str = "browser-batch") -> list[tuple[str, BrowserAction]]:  # 新增代码+BrowserActionBatch: 批量执行多个浏览器动作并返回有序结果；若没有这行代码，上层只能逐个调用无法表达批处理。
        action_items = [dict(action_item) for action_item in actions]  # 新增代码+BrowserActionBatch: 复制批量动作参数避免调用方对象被修改；若没有这行代码，执行器可能污染上层计划。
        if not action_items:  # 新增代码+BrowserActionBatch: 兼容空批次；若没有这行代码，空列表会创建无意义线程池。
            return []  # 新增代码+BrowserActionBatch: 空批次直接返回空结果；若没有这行代码，上层需要额外判断。
        if any(self.policy.requires_serial(str(action_item.get("tool_name", ""))) for action_item in action_items):  # 新增代码+BrowserActionBatch: 只要批次含写工具就整体保守串行；若没有这行代码，点击输入可能和读取并发污染页面。
            return [self._execute_batch_item(run_id, stage_id, action_item, index, action_id_prefix) for index, action_item in enumerate(action_items)]  # 新增代码+BrowserActionBatch: 串行批次按输入顺序执行；若没有这行代码，写工具顺序可能错乱。
        max_workers = max(1, len(action_items))  # 新增代码+BrowserActionBatch: 线程池大小匹配只读动作数量；若没有这行代码，批量读取无法真正并发。
        with ThreadPoolExecutor(max_workers=max_workers) as pool:  # 新增代码+BrowserActionBatch: 创建短生命周期线程池执行只读动作；若没有这行代码，只读批处理仍会串行。
            futures = [pool.submit(self._execute_batch_item, run_id, stage_id, action_item, index, action_id_prefix) for index, action_item in enumerate(action_items)]  # 新增代码+BrowserActionBatch: 同时提交所有只读动作；若没有这行代码，线程池不会实际并发。
            return [future.result() for future in futures]  # 新增代码+BrowserActionBatch: 按输入顺序收集结果并传播异常；若没有这行代码，并发完成顺序会打乱模型上下文。

    def _execute_batch_item(self, run_id: str, stage_id: str, action_item: dict[str, Any], index: int, action_id_prefix: str) -> tuple[str, BrowserAction]:  # 新增代码+BrowserActionBatch: 执行单个批量动作；若没有这行代码，批量串行和并发路径会重复解析逻辑。
        tool_name = str(action_item.get("tool_name", ""))  # 新增代码+BrowserActionBatch: 读取批量动作工具名；若没有这行代码，execute_action 不知道执行哪个工具。
        if not tool_name:  # 新增代码+BrowserActionBatch: 拒绝缺工具名的批量动作；若没有这行代码，事件流会出现空工具名。
            raise ValueError("批量浏览器动作缺少 tool_name。")  # 新增代码+BrowserActionBatch: 给出清晰中文错误；若没有这行代码，调用方只会看到后续 KeyError。
        handler = action_item.get("handler")  # 新增代码+BrowserActionBatch: 读取真实工具 handler；若没有这行代码，批量动作无法执行。
        if not callable(handler):  # 新增代码+BrowserActionBatch: 校验 handler 必须可调用；若没有这行代码，错误会在深层调用中才暴露。
            raise ValueError(f"批量浏览器动作 {tool_name} 缺少可调用 handler。")  # 新增代码+BrowserActionBatch: 明确指出哪个工具缺 handler；若没有这行代码，新手难以定位配置错误。
        arguments = action_item.get("arguments") if isinstance(action_item.get("arguments"), dict) else {}  # 新增代码+BrowserActionBatch: 只接受字典参数并为空值兜底；若没有这行代码，handler 可能收到非 JSON 对象。
        item_stage_id = str(action_item.get("stage_id", stage_id) or stage_id)  # 新增代码+BrowserActionBatch: 允许单个动作覆盖阶段 id；若没有这行代码，批量动作无法细分阶段来源。
        action_id = str(action_item.get("action_id") or f"{action_id_prefix}-{index + 1}")  # 新增代码+BrowserActionBatch: 为批量动作生成稳定 action id；若没有这行代码，结果和事件难以按批次追踪。
        attempts_limit = int(action_item.get("attempts_limit", 1) or 1)  # 新增代码+BrowserActionBatch: 读取每个动作的重试预算；若没有这行代码，批量执行无法复用单动作恢复能力。
        return self.execute_action(run_id, item_stage_id, tool_name, arguments, handler, action_id=action_id, attempts_limit=attempts_limit, is_retryable_error=action_item.get("is_retryable_error"), classify_error=action_item.get("classify_error"), redact_output=action_item.get("redact_output"), observation_id_getter=action_item.get("observation_id_getter"), on_action_started=action_item.get("on_action_started"), on_action_finished=action_item.get("on_action_finished"), on_attempt_success=action_item.get("on_attempt_success"), on_attempt_error=action_item.get("on_attempt_error"), on_result_chunk=action_item.get("on_result_chunk"), retry_delay_seconds=float(action_item.get("retry_delay_seconds", 0.0) or 0.0))  # 新增代码+BrowserActionBatch: 复用单动作执行入口保持事件、重试和流式输出一致；若没有这行代码，批处理会变成新的旁路系统。

    def _record(self, action: BrowserAction, event_type: str, payload: dict[str, Any] | None = None) -> None:  # 新增代码+BrowserActionStage6: 内部统一写事件；若没有这行代码，每个生命周期方法会重复落盘逻辑。
        event = {"run_id": action.run_id, "action_id": action.action_id, "event_type": event_type, "payload": dict(payload or {})}  # 新增代码+BrowserActionStage6: 构造内存事件；若没有这行代码，无 store 模式无法观察。
        self.events.append(event)  # 新增代码+BrowserActionStage6: 保存内存事件；若没有这行代码，测试和调试没有事件列表。
        if self.store is not None:  # 新增代码+BrowserActionStage6: 如果接入持久 store；若没有这行代码，store=None 会报错。
            self.store.save_action(action, event_type=event_type)  # 新增代码+BrowserActionStage6: 保存动作并追加事件；若没有这行代码，磁盘状态不会更新。
