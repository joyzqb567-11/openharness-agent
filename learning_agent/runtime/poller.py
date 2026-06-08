"""持久任务轮询器和简单 watchdog。"""  # 新增代码+TaskPoller: 说明本文件负责扫描 running task 并生成通知；若没有这行代码，poller 逻辑边界不清楚。

from __future__ import annotations  # 新增代码+TaskPoller: 延迟解析类型注解；若没有这行代码，类型引用更容易受定义顺序影响。

from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+TaskPoller: poller 需要把卡点写入命令队列；若没有这行代码，主 agent 收不到通知。
from learning_agent.runtime.task_registry import TaskRegistry  # 新增代码+TaskPoller: poller 需要读取和更新任务登记表；若没有这行代码，无法扫描 durable task。


class TaskPoller:  # 新增代码+TaskPoller: 扫描任务状态并生成 task notification；若没有这个类，后台任务只能手动查询。
    def __init__(self, task_registry: TaskRegistry, command_queue: RuntimeCommandQueue) -> None:  # 新增代码+TaskPoller: 初始化任务登记表和命令队列；若没有这行代码，调用方无法注入存储。
        self.task_registry = task_registry  # 新增代码+TaskPoller: 保存任务登记表；若没有这行代码，poll_once 无法读取任务。
        self.command_queue = command_queue  # 新增代码+TaskPoller: 保存命令队列；若没有这行代码，poll_once 无法回灌通知。
        self.task_registry.command_queue = command_queue  # 新增代码+TaskPoller: 确保 registry 更新状态时能写通知；若没有这行代码，mark_needs_input 只改状态不通知。

    def poll_once(self) -> int:  # 新增代码+TaskPoller: 执行一次轻量轮询；若没有这行代码，CLI 和 runtime 无法主动推进后台状态。
        changed = 0  # 新增代码+TaskPoller: 统计本轮发现的状态变化；若没有这行代码，调用方不知道 poll 是否有动作。
        for record in self.task_registry.list_tasks():  # 新增代码+TaskPoller: 遍历所有持久任务；若没有这行代码，poller 没有扫描对象。
            if record.status != "running":  # 新增代码+TaskPoller: 只处理 running 任务；若没有这行代码，已完成任务会重复通知。
                continue  # 新增代码+TaskPoller: 非 running 任务跳过；若没有这行代码，后续逻辑会误改终态任务。
            tail = self.task_registry.output_store.tail(record.task_id, max_chars=200)  # 新增代码+TaskPoller: 读取输出尾部判断是否卡住；若没有这行代码，watchdog 没有证据。
            if self._looks_like_needs_input(tail):  # 新增代码+TaskPoller: 判断输出是否像交互提示；若没有这行代码，Continue? 卡点不会被识别。
                self.task_registry.mark_needs_input(record.task_id, tail or "任务可能正在等待用户输入。")  # 新增代码+TaskPoller: 标记 needs_input 并通知；若没有这行代码，主 agent 不会知道卡点。
                changed += 1  # 新增代码+TaskPoller: 更新变化计数；若没有这行代码，CLI 无法报告 changed=1。
        return changed  # 新增代码+TaskPoller: 返回变化数量；若没有这行代码，调用方拿不到 poll 结果。

    def _looks_like_needs_input(self, text: str) -> bool:  # 新增代码+TaskPoller: 判断输出是否像等待输入；若没有这行代码，规则会散落在 poll_once。
        normalized = text.strip().lower()  # 新增代码+TaskPoller: 标准化输出文本；若没有这行代码，大小写或空白会影响判断。
        if not normalized:  # 新增代码+TaskPoller: 空输出不视为卡点；若没有这行代码，所有沉默任务都会被误报。
            return False  # 新增代码+TaskPoller: 返回未卡住；若没有这行代码，空输出会继续匹配。
        prompt_markers = ["continue?", "confirm?", "are you sure?", "是否继续", "请确认", "输入 y"]  # 新增代码+TaskPoller: 定义常见交互提示词；若没有这行代码，watchdog 没有可解释规则。
        return any(marker in normalized for marker in prompt_markers)  # 新增代码+TaskPoller: 命中任一提示即认为需要输入；若没有这行代码，卡点不会触发通知。
