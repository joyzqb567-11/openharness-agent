"""长任务 harness 的持久化队列和租约。"""  # 新增代码+LongTaskHarness: 说明本文件负责任务排队和领取；若没有这行代码，队列职责不清楚。

from __future__ import annotations  # 新增代码+LongTaskHarness: 延迟解析类型注解；若没有这行代码，类型引用更容易受顺序影响。

import time  # 新增代码+LongTaskHarness: 租约过期判断需要当前时间；若没有这行代码，崩溃 worker 无法释放任务。

from learning_agent.harness.models import HarnessRun  # 新增代码+LongTaskHarness: 队列保存和读取 run 对象；若没有这行代码，队列只能处理松散字典。
from learning_agent.harness.store import HarnessStore  # 新增代码+LongTaskHarness: 队列依赖持久化 store；若没有这行代码，任务状态无法跨进程保存。
from learning_agent.runtime.files import FileLock  # 新增代码+RuntimeFileSafety: 队列领取需要跨进程文件锁；若没有这行代码，两个 worker 可能同时拿到同一个 run。


class HarnessQueue:  # 新增代码+LongTaskHarness: 管理持久化任务队列；若没有这个类，长任务无法稳定排队和领取。
    def __init__(self, store: HarnessStore) -> None:  # 新增代码+LongTaskHarness: 初始化队列并注入 store；若没有这行代码，队列不知道读写哪里。
        self.store = store  # 新增代码+LongTaskHarness: 保存 store 引用；若没有这行代码，后续 enqueue/lease 无法落盘。
        self.lock_path = self.store.base_dir / "queue.lock"  # 新增代码+RuntimeFileSafety: 定义队列级领取锁；若没有这行代码，并发 lease 可能重复领取。

    def enqueue(self, run: HarnessRun) -> HarnessRun:  # 新增代码+LongTaskHarness: 把 run 放入队列；若没有这行代码，任务不能进入可执行状态。
        run.status = "queued"  # 新增代码+LongTaskHarness: 标记为排队；若没有这行代码，lease_next 不会识别为待执行。
        run.lease_worker = ""  # 新增代码+LongTaskHarness: 清空旧 worker；若没有这行代码，重排队任务可能被误认为仍被占用。
        run.lease_until = 0.0  # 新增代码+LongTaskHarness: 清空旧租约；若没有这行代码，任务可能等到旧租约过期才能执行。
        self.store.save_run(run)  # 新增代码+LongTaskHarness: 保存队列状态；若没有这行代码，进程重启后任务会丢失。
        self.store.append_event(run.run_id, "queued", {"stage_count": len(run.stages)})  # 新增代码+LongTaskHarness: 记录排队事件；若没有这行代码，审计日志看不到任务入口。
        return run  # 新增代码+LongTaskHarness: 返回更新后的 run；若没有这行代码，调用方拿不到最新状态。

    def lease_next(self, worker_id: str, lease_seconds: int = 300) -> HarnessRun | None:  # 新增代码+LongTaskHarness: 领取下一个可执行任务；若没有这行代码，多 agent 无法协作处理队列。
        with FileLock(self.lock_path):  # 新增代码+RuntimeFileSafety: 领取过程加队列锁；若没有这行代码，两个 worker 可能同时读取 queued 状态。
            now = time.time()  # 新增代码+LongTaskHarness: 读取当前时间用于租约判断；若没有这行代码，无法判断旧租约是否过期。
            for run_id in self.store.list_run_ids():  # 新增代码+LongTaskHarness: 按稳定顺序扫描 run；若没有这行代码，队列无法发现任务。
                run = self.store.try_load_run(run_id)  # 修改代码+RuntimeFileSafety: 容错读取 run 并跳过坏 JSON；若没有这行代码，单个半写状态会拖垮整个队列。
                if run is None:  # 新增代码+RuntimeFileSafety: 如果状态文件损坏或不存在；若没有这行代码，后续会访问空对象。
                    continue  # 新增代码+RuntimeFileSafety: 跳过坏任务继续扫描正常任务；若没有这行代码，恢复能力会在坏文件上停住。
                terminal = run.status in {"completed", "failed"}  # 新增代码+LongTaskHarness: 判断终态任务；若没有这行代码，已结束任务可能被重复执行。
                lease_expired = run.lease_until > 0 and run.lease_until < now  # 新增代码+LongTaskHarness: 判断运行中任务租约是否过期；若没有这行代码，崩溃 worker 会永久占用任务。
                if terminal or (run.status == "running" and not lease_expired):  # 新增代码+LongTaskHarness: 跳过终态或未过期任务；若没有这行代码，两个 worker 可能同时执行。
                    continue  # 新增代码+LongTaskHarness: 继续扫描下一个任务；若没有这行代码，队列会在不可领取任务上停住。
                if run.status not in {"queued", "running"}:  # 新增代码+LongTaskHarness: 只允许 queued 或过期 running 被领取；若没有这行代码，未知状态可能被误执行。
                    continue  # 新增代码+LongTaskHarness: 跳过未知状态；若没有这行代码，坏状态会进入 runner。
                run.status = "running"  # 新增代码+LongTaskHarness: 标记任务运行中；若没有这行代码，其他 worker 仍会把它当待执行。
                run.lease_worker = worker_id  # 新增代码+LongTaskHarness: 记录领取 worker；若没有这行代码，heartbeat 无法校验身份。
                run.lease_until = now + max(1, lease_seconds)  # 新增代码+LongTaskHarness: 设置租约过期时间；若没有这行代码，崩溃恢复没有边界。
                self.store.save_run(run)  # 新增代码+LongTaskHarness: 保存租约状态；若没有这行代码，领取只存在内存中。
                self.store.append_event(run.run_id, "leased", {"worker_id": worker_id, "lease_seconds": lease_seconds})  # 新增代码+LongTaskHarness: 记录领取事件；若没有这行代码，审计无法知道谁执行任务。
                return run  # 新增代码+LongTaskHarness: 返回已领取任务；若没有这行代码，runner 无法开始执行。
        return None  # 新增代码+LongTaskHarness: 没有可执行任务时返回 None；若没有这行代码，调用方无法区分空队列。

    def heartbeat(self, run_id: str, worker_id: str, lease_seconds: int = 300) -> HarnessRun:  # 新增代码+LongTaskHarness: 刷新运行中任务租约；若没有这行代码，长阶段可能被误判过期。
        run = self.store.load_run(run_id)  # 新增代码+LongTaskHarness: 读取当前任务状态；若没有这行代码，无法校验租约所有者。
        if run.lease_worker != worker_id:  # 新增代码+LongTaskHarness: 校验 worker 身份；若没有这行代码，其他进程可能误刷新租约。
            raise ValueError("租约 worker 不匹配，拒绝 heartbeat。")  # 新增代码+LongTaskHarness: 明确拒绝错误 worker；若没有这行代码，队列安全边界会变弱。
        run.lease_until = time.time() + max(1, lease_seconds)  # 新增代码+LongTaskHarness: 延长租约；若没有这行代码，长阶段可能被其他 worker 接管。
        self.store.save_run(run)  # 新增代码+LongTaskHarness: 保存新的租约时间；若没有这行代码，heartbeat 不会跨进程生效。
        self.store.append_event(run.run_id, "heartbeat", {"worker_id": worker_id})  # 新增代码+LongTaskHarness: 记录心跳事件；若没有这行代码，长任务活性不可审计。
        return run  # 新增代码+LongTaskHarness: 返回更新后的任务；若没有这行代码，调用方拿不到新 lease_until。

    def complete(self, run: HarnessRun) -> HarnessRun:  # 新增代码+LongTaskHarness: 标记任务完成；若没有这行代码，队列无法收束任务。
        run.status = "completed"  # 新增代码+LongTaskHarness: 设置完成状态；若没有这行代码，任务会继续被扫描。
        run.lease_worker = ""  # 新增代码+LongTaskHarness: 清空 worker；若没有这行代码，状态页会误以为还有 worker 占用。
        run.lease_until = 0.0  # 新增代码+LongTaskHarness: 清空租约；若没有这行代码，完成任务仍显示过期时间。
        self.store.save_run(run)  # 新增代码+LongTaskHarness: 保存完成状态；若没有这行代码，重启后任务仍可能是 running。
        self.store.append_event(run.run_id, "completed", {})  # 新增代码+LongTaskHarness: 记录完成事件；若没有这行代码，审计日志缺少终点。
        return run  # 新增代码+LongTaskHarness: 返回完成任务；若没有这行代码，调用方无法继续渲染。

    def fail(self, run: HarnessRun, reason: str) -> HarnessRun:  # 新增代码+LongTaskHarness: 标记任务失败；若没有这行代码，无法持久化最终错误。
        run.status = "failed"  # 新增代码+LongTaskHarness: 设置失败状态；若没有这行代码，失败任务可能被反复领取。
        run.failure_reason = reason  # 新增代码+LongTaskHarness: 保存失败原因；若没有这行代码，用户不知道任务为什么停下。
        run.lease_worker = ""  # 新增代码+LongTaskHarness: 清空 worker；若没有这行代码，失败任务仍像被占用。
        run.lease_until = 0.0  # 新增代码+LongTaskHarness: 清空租约；若没有这行代码，状态页会显示无意义过期时间。
        self.store.save_run(run)  # 新增代码+LongTaskHarness: 保存失败状态；若没有这行代码，重启后失败信息会丢失。
        self.store.append_event(run.run_id, "failed", {"reason": reason})  # 新增代码+LongTaskHarness: 记录失败事件；若没有这行代码，审计无法定位失败原因。
        return run  # 新增代码+LongTaskHarness: 返回失败任务；若没有这行代码，调用方拿不到最终状态。
