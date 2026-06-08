"""中断 turn 恢复器，对齐 ClaudeCode interrupted-turn requeue。"""  # 新增代码+InterruptedResume: 说明本文件负责把 running run 重新入队；若没有这行代码，恢复逻辑边界不清楚。

from __future__ import annotations  # 新增代码+InterruptedResume: 延迟解析类型注解；若没有这行代码，类之间引用更容易受定义顺序影响。

from learning_agent.harness.store import HarnessStore  # 新增代码+InterruptedResume: 恢复器需要扫描 harness run 状态；若没有这行代码，无法发现 interrupted run。
from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+InterruptedResume: 恢复器需要把续跑命令写入 runtime queue；若没有这行代码，中断任务无法重新进入主循环。


class InterruptedRunResumer:  # 新增代码+InterruptedResume: 扫描 running harness run 并生成恢复命令；若没有这个类，进程崩溃后任务会卡住。
    def __init__(self, store: HarnessStore, command_queue: RuntimeCommandQueue) -> None:  # 新增代码+InterruptedResume: 初始化 harness store 和 runtime queue；若没有这行代码，调用方无法注入测试目录。
        self.store = store  # 新增代码+InterruptedResume: 保存 harness store；若没有这行代码，恢复器无法读取 run。
        self.command_queue = command_queue  # 新增代码+InterruptedResume: 保存命令队列；若没有这行代码，恢复器无法入队续跑命令。

    def enqueue_interrupted_runs(self) -> int:  # 新增代码+InterruptedResume: 把所有 interrupted run 重新入队；若没有这行代码，启动时无法批量恢复。
        restored = 0  # 新增代码+InterruptedResume: 统计恢复数量；若没有这行代码，CLI 无法打印 restored=N。
        for run_id in self.store.list_run_ids():  # 新增代码+InterruptedResume: 遍历所有 harness run；若没有这行代码，恢复器找不到历史任务。
            run = self.store.load_run(run_id)  # 新增代码+InterruptedResume: 读取 run 状态；若没有这行代码，无法判断是否 interrupted。
            if run.status != "running":  # 新增代码+InterruptedResume: 只处理 running 状态；若没有这行代码，completed/failed 会被错误恢复。
                continue  # 新增代码+InterruptedResume: 非 running 跳过；若没有这行代码，终态任务会被重新入队。
            if 0 <= run.current_stage_index < len(run.stages):  # 新增代码+InterruptedResume: 如果当前阶段索引有效；若没有这行代码，空阶段 run 会访问越界。
                stage = run.stages[run.current_stage_index]  # 新增代码+InterruptedResume: 读取当前未完成阶段；若没有这行代码，无法标记 needs_review。
                if stage.status == "running":  # 新增代码+InterruptedResume: 只有正在执行中的阶段需要审查；若没有这行代码，pending 阶段也会被误标记。
                    stage.status = "needs_review"  # 新增代码+InterruptedResume: 标记需要人工/模型审查副作用；若没有这行代码，未完成工具可能被自动重放。
            run.status = "queued"  # 新增代码+InterruptedResume: 把 run 放回队列；若没有这行代码，worker 不会重新领取。
            run.lease_worker = ""  # 新增代码+InterruptedResume: 清空旧 worker；若没有这行代码，崩溃 worker 仍显示占用。
            run.lease_until = 0.0  # 新增代码+InterruptedResume: 清空旧租约；若没有这行代码，队列可能等旧租约过期。
            self.store.save_run(run)  # 新增代码+InterruptedResume: 保存恢复后的 run；若没有这行代码，重启后仍是 running。
            self.store.append_event(run.run_id, "interrupted_requeued", {"prompt": run.prompt})  # 新增代码+InterruptedResume: 记录恢复事件；若没有这行代码，审计不知道为何重新入队。
            self.command_queue.enqueue_resume_interrupted({"run_id": run.run_id, "prompt": "Continue from where you left off.", "original_prompt": run.prompt})  # 新增代码+InterruptedResume: 写入续跑命令；若没有这行代码，主循环不会收到恢复提示。
            restored += 1  # 新增代码+InterruptedResume: 增加恢复计数；若没有这行代码，CLI 报告不准确。
        return restored  # 新增代码+InterruptedResume: 返回恢复数量；若没有这行代码，调用方无法判断是否有动作。
