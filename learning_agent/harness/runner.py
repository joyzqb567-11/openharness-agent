"""长任务 harness 的阶段 runner。"""  # 新增代码+LongTaskHarness: 说明本文件负责执行队列任务；若没有这行代码，runner 职责不清楚。

from __future__ import annotations  # 新增代码+LongTaskHarness: 延迟解析类型注解；若没有这行代码，Executor 类型引用更容易受顺序影响。

from collections.abc import Callable  # 新增代码+LongTaskHarness: 定义 executor 函数类型；若没有这行代码，注解只能退回不清楚的 Any。

from learning_agent.harness.models import HarnessAttempt, HarnessRun, HarnessStage, utc_timestamp  # 新增代码+LongTaskHarness: 导入 run/stage/attempt 模型；若没有这行代码，runner 无法更新持久状态。
from learning_agent.harness.queue import HarnessQueue  # 新增代码+LongTaskHarness: runner 从持久队列领取任务；若没有这行代码，runner 只能执行手动传入对象。
from learning_agent.harness.recovery import RecoveryPolicy  # 新增代码+LongTaskHarness: 导入恢复策略；若没有这行代码，失败后无法自动继续。
from learning_agent.harness.store import HarnessStore  # 新增代码+LongTaskHarness: 导入持久 store；若没有这行代码，runner 无法保存状态和事件。
from learning_agent.harness.verifier import StageVerifier  # 新增代码+LongTaskHarness: 导入阶段验证器；若没有这行代码，runner 无法做阶段验收。

Executor = Callable[[HarnessRun, HarnessStage], str]  # 新增代码+LongTaskHarness: 定义阶段执行函数签名；若没有这行代码，runner API 不清楚。


class HarnessRunner:  # 新增代码+LongTaskHarness: 从队列领取并执行多阶段任务；若没有这个类，长任务只能手动推进。
    def __init__(self, store: HarnessStore, executor: Executor, verifier: StageVerifier, recovery_policy: RecoveryPolicy | None = None) -> None:  # 新增代码+LongTaskHarness: 初始化 runner 依赖；若没有这行代码，测试无法注入假 executor。
        self.store = store  # 新增代码+LongTaskHarness: 保存 store；若没有这行代码，runner 无法落盘。
        self.executor = executor  # 新增代码+LongTaskHarness: 保存阶段执行器；若没有这行代码，runner 不知道如何执行阶段。
        self.verifier = verifier  # 新增代码+LongTaskHarness: 保存阶段验证器；若没有这行代码，runner 无法判断阶段是否成功。
        self.recovery_policy = recovery_policy or RecoveryPolicy()  # 新增代码+LongTaskHarness: 保存恢复策略或默认策略；若没有这行代码，可恢复失败无法处理。

    def run_once(self, worker_id: str = "harness-worker", lease_seconds: int = 300) -> HarnessRun | None:  # 新增代码+LongTaskHarness: 领取并执行一个队列任务；若没有这行代码，外部 agent 没有简单执行入口。
        queue = HarnessQueue(self.store)  # 新增代码+LongTaskHarness: 创建队列对象；若没有这行代码，runner 无法领取任务。
        run = queue.lease_next(worker_id=worker_id, lease_seconds=lease_seconds)  # 新增代码+LongTaskHarness: 领取下一个任务；若没有这行代码，runner 可能和其他 worker 冲突。
        if run is None:  # 新增代码+LongTaskHarness: 处理空队列；若没有这行代码，没有任务时会继续访问空对象。
            return None  # 新增代码+LongTaskHarness: 空队列返回 None；若没有这行代码，调用方无法知道没有执行。
        return self.run_to_completion(run)  # 新增代码+LongTaskHarness: 执行领取到的任务直到完成或失败；若没有这行代码，run_once 只会领取不执行。

    def run_to_completion(self, run: HarnessRun) -> HarnessRun:  # 新增代码+LongTaskHarness: 执行指定 run 的剩余阶段；若没有这行代码，恢复后无法从 checkpoint 继续。
        run.status = "running"  # 新增代码+LongTaskHarness: 标记任务运行中；若没有这行代码，状态页无法反映执行中。
        self.store.save_run(run)  # 新增代码+LongTaskHarness: 保存运行中状态；若没有这行代码，进程崩溃后不知道已经开始。
        while run.current_stage_index < len(run.stages):  # 新增代码+LongTaskHarness: 从当前 checkpoint 推进阶段；若没有这行代码，任务无法多阶段执行。
            stage = run.stages[run.current_stage_index]  # 新增代码+LongTaskHarness: 读取当前阶段；若没有这行代码，runner 不知道执行哪一步。
            if stage.status == "completed":  # 新增代码+LongTaskHarness: 跳过已完成阶段；若没有这行代码，恢复时会重跑成功阶段。
                run.current_stage_index += 1  # 新增代码+LongTaskHarness: 推进到下一阶段；若没有这行代码，已完成阶段会卡住循环。
                continue  # 新增代码+LongTaskHarness: 继续下一轮；若没有这行代码，已完成阶段仍会执行。
            stage_result = self._run_stage_with_retries(run, stage)  # 新增代码+LongTaskHarness: 执行当前阶段并处理重试；若没有这行代码，主循环会塞满细节。
            if not stage_result:  # 新增代码+LongTaskHarness: 阶段失败时停止整个 run；若没有这行代码，失败阶段后还会继续执行。
                self.store.save_run(run)  # 新增代码+LongTaskHarness: 保存失败后的最终状态；若没有这行代码，失败原因会留在内存。
                return run  # 新增代码+LongTaskHarness: 返回失败 run；若没有这行代码，调用方拿不到结果。
            run.current_stage_index += 1  # 新增代码+LongTaskHarness: 阶段通过后推进 checkpoint；若没有这行代码，恢复时会重复执行已完成阶段。
            self.store.save_run(run)  # 新增代码+LongTaskHarness: 保存 checkpoint；若没有这行代码，崩溃后无法从下一阶段继续。
        run.status = "completed"  # 新增代码+LongTaskHarness: 所有阶段完成后标记 run 完成；若没有这行代码，队列会以为任务仍在运行。
        run.lease_worker = ""  # 新增代码+LongTaskHarness: 清空 worker；若没有这行代码，完成任务还显示占用。
        run.lease_until = 0.0  # 新增代码+LongTaskHarness: 清空租约；若没有这行代码，状态页会显示无意义租约。
        self.store.save_run(run)  # 新增代码+LongTaskHarness: 保存完成状态；若没有这行代码，完成不会持久化。
        self.store.append_event(run.run_id, "run_completed", {"stage_count": len(run.stages)})  # 新增代码+LongTaskHarness: 记录 run 完成事件；若没有这行代码，审计日志没有终点。
        return run  # 新增代码+LongTaskHarness: 返回完成 run；若没有这行代码，调用方无法渲染结果。

    def _run_stage_with_retries(self, run: HarnessRun, stage: HarnessStage) -> bool:  # 新增代码+LongTaskHarness: 执行单阶段并处理自动重试；若没有这行代码，恢复逻辑会散在主循环。
        while len(stage.attempts) < stage.safe_max_attempts():  # 新增代码+LongTaskHarness: 在最大尝试次数内循环；若没有这行代码，阶段可能无限重试。
            if not stage.started_at:  # 新增代码+LongTaskHarness: 首次执行时记录阶段开始时间；若没有这行代码，状态页缺少开始时间。
                stage.started_at = utc_timestamp()  # 新增代码+LongTaskHarness: 写入阶段开始时间；若没有这行代码，审计时间线不完整。
            stage.status = "running"  # 新增代码+LongTaskHarness: 标记阶段运行中；若没有这行代码，状态输出无法显示当前阶段。
            attempt = HarnessAttempt(attempt_number=len(stage.attempts) + 1, status="running", endpoint=run.current_endpoint())  # 新增代码+LongTaskHarness: 创建本次尝试记录；若没有这行代码，重试过程没有审计对象。
            self.store.save_run(run)  # 新增代码+LongTaskHarness: 保存阶段开始状态；若没有这行代码，崩溃后看不到阶段已开始。
            self.store.append_event(run.run_id, "stage_started", {"stage": stage.name, "attempt": attempt.attempt_number, "endpoint": attempt.endpoint})  # 新增代码+LongTaskHarness: 记录阶段开始事件；若没有这行代码，事件流缺少阶段边界。
            try:  # 新增代码+LongTaskHarness: 捕获 executor 错误；若没有这行代码，异常会绕过状态保存。
                output = self.executor(run, stage)  # 新增代码+LongTaskHarness: 调用阶段执行器；若没有这行代码，runner 不会真正做工作。
            except Exception as error:  # 新增代码+LongTaskHarness: 处理阶段执行失败；若没有这行代码，失败无法转成可审计状态。
                if not self._record_failure_and_maybe_retry(run, stage, attempt, str(error)):  # 新增代码+LongTaskHarness: 记录失败并判断是否重试；若没有这行代码，错误处理会重复。
                    return False  # 新增代码+LongTaskHarness: 不可恢复或耗尽次数时返回失败；若没有这行代码，runner 会错误继续。
                continue  # 新增代码+LongTaskHarness: 可恢复时继续下一次尝试；若没有这行代码，重试不会发生。
            verification = self.verifier.verify(stage, output)  # 新增代码+LongTaskHarness: 验证阶段输出；若没有这行代码，阶段成功没有确定性门禁。
            attempt.output = output  # 新增代码+LongTaskHarness: 保存阶段输出；若没有这行代码，验收依据会丢失。
            attempt.status = "completed" if verification.passed else "failed"  # 新增代码+LongTaskHarness: 根据验收结果设置尝试状态；若没有这行代码，失败验收也可能显示成功。
            attempt.completed_at = utc_timestamp()  # 新增代码+LongTaskHarness: 保存尝试结束时间；若没有这行代码，审计时间线不完整。
            stage.attempts.append(attempt)  # 新增代码+LongTaskHarness: 追加尝试历史；若没有这行代码，重试记录不会保存。
            stage.acceptance = verification  # 新增代码+LongTaskHarness: 保存验收结果；若没有这行代码，状态页看不到 acceptance。
            stage.checkpoint = output[:500]  # 新增代码+LongTaskHarness: 保存输出摘要作为 checkpoint；若没有这行代码，恢复后缺少阶段产物摘要。
            if verification.passed:  # 新增代码+LongTaskHarness: 通过验收时收束阶段；若没有这行代码，阶段不会进入 completed。
                stage.status = "completed"  # 新增代码+LongTaskHarness: 标记阶段完成；若没有这行代码，下一次恢复会重跑阶段。
                stage.completed_at = utc_timestamp()  # 新增代码+LongTaskHarness: 保存阶段完成时间；若没有这行代码，状态页缺少结束时间。
                self.store.save_run(run)  # 新增代码+LongTaskHarness: 保存阶段完成状态；若没有这行代码，checkpoint 不会落盘。
                self.store.append_event(run.run_id, "stage_completed", {"stage": stage.name, "attempt": attempt.attempt_number})  # 新增代码+LongTaskHarness: 记录阶段完成事件；若没有这行代码，审计日志缺少完成边界。
                return True  # 新增代码+LongTaskHarness: 告诉主循环阶段成功；若没有这行代码，主循环无法推进。
            if len(stage.attempts) < stage.safe_max_attempts():  # 新增代码+LongTaskHarness: 验收失败但仍有次数时允许重试；若没有这行代码，一次验收失败就会终止。
                stage.status = "pending"  # 新增代码+LongTaskHarness: 重试前把阶段放回 pending；若没有这行代码，状态会一直显示 running。
                self.store.save_run(run)  # 新增代码+LongTaskHarness: 保存待重试状态；若没有这行代码，崩溃后无法继续重试。
                self.store.append_event(run.run_id, "stage_retry_scheduled", {"stage": stage.name, "reason": verification.message})  # 新增代码+LongTaskHarness: 记录验收失败重试；若没有这行代码，用户不知道为什么又跑一次。
                continue  # 新增代码+LongTaskHarness: 继续下一次尝试；若没有这行代码，重试不会发生。
            run.status = "failed"  # 新增代码+LongTaskHarness: 验收失败耗尽次数后标记 run 失败；若没有这行代码，任务会假装完成。
            run.failure_reason = verification.message  # 新增代码+LongTaskHarness: 保存失败原因；若没有这行代码，用户看不到缺失断言。
            stage.status = "failed"  # 新增代码+LongTaskHarness: 标记阶段失败；若没有这行代码，状态页无法定位失败阶段。
            self.store.append_event(run.run_id, "stage_failed", {"stage": stage.name, "reason": verification.message})  # 新增代码+LongTaskHarness: 记录阶段失败事件；若没有这行代码，审计日志没有失败边界。
            return False  # 新增代码+LongTaskHarness: 告诉主循环任务失败；若没有这行代码，后续阶段可能错误执行。
        return stage.status == "completed"  # 新增代码+LongTaskHarness: 循环结束后返回阶段是否完成；若没有这行代码，函数可能隐式返回 None。

    def _record_failure_and_maybe_retry(self, run: HarnessRun, stage: HarnessStage, attempt: HarnessAttempt, error_text: str) -> bool:  # 新增代码+LongTaskHarness: 记录执行异常并判断重试；若没有这行代码，异常处理会重复且不可审计。
        attempt.status = "failed"  # 新增代码+LongTaskHarness: 标记本次尝试失败；若没有这行代码，失败尝试可能显示 running。
        attempt.error = error_text  # 新增代码+LongTaskHarness: 保存错误文本；若没有这行代码，失败原因会丢失。
        attempt.completed_at = utc_timestamp()  # 新增代码+LongTaskHarness: 保存失败结束时间；若没有这行代码，审计时间线不完整。
        stage.attempts.append(attempt)  # 新增代码+LongTaskHarness: 记录失败尝试；若没有这行代码，重试历史不可见。
        can_retry = len(stage.attempts) < stage.safe_max_attempts() and self.recovery_policy.recover(run, error_text)  # 新增代码+LongTaskHarness: 判断是否还有次数且错误可恢复；若没有这行代码，所有失败都会终止。
        if can_retry:  # 新增代码+LongTaskHarness: 可恢复失败进入重试分支；若没有这行代码，端点恢复不会触发。
            stage.status = "pending"  # 新增代码+LongTaskHarness: 把阶段放回待执行；若没有这行代码，状态会卡在 running。
            self.store.save_run(run)  # 新增代码+LongTaskHarness: 保存恢复后的 endpoint 和阶段状态；若没有这行代码，重启后不知道已切端点。
            self.store.append_event(run.run_id, "stage_retry_scheduled", {"stage": stage.name, "reason": error_text, "next_endpoint": run.current_endpoint()})  # 新增代码+LongTaskHarness: 记录重试和下个 endpoint；若没有这行代码，端点恢复不可审计。
            return True  # 新增代码+LongTaskHarness: 告诉调用方继续重试；若没有这行代码，runner 会停止。
        run.status = "failed"  # 新增代码+LongTaskHarness: 不可恢复或耗尽次数时标记 run 失败；若没有这行代码，任务可能继续执行。
        run.failure_reason = error_text  # 新增代码+LongTaskHarness: 保存最终失败原因；若没有这行代码，用户无法定位问题。
        stage.status = "failed"  # 新增代码+LongTaskHarness: 标记阶段失败；若没有这行代码，状态页不知道失败阶段。
        self.store.append_event(run.run_id, "stage_failed", {"stage": stage.name, "reason": error_text})  # 新增代码+LongTaskHarness: 记录失败事件；若没有这行代码，审计日志缺少错误边界。
        return False  # 新增代码+LongTaskHarness: 告诉调用方停止任务；若没有这行代码，不可恢复错误可能被继续。
