"""长任务 harness 的失败分类和端点恢复策略。"""  # 新增代码+LongTaskHarness: 说明本文件负责自动恢复决策；若没有这行代码，失败后继续逻辑会散落在 runner。

from __future__ import annotations  # 新增代码+LongTaskHarness: 延迟解析类型注解；若没有这行代码，后续引用模型类更容易受顺序影响。

from learning_agent.harness.models import HarnessRun  # 新增代码+LongTaskHarness: 端点轮换需要修改 run 状态；若没有这行代码，恢复策略无法工作。


class RecoveryPolicy:  # 新增代码+LongTaskHarness: 判断失败是否可恢复并执行轻量恢复动作；若没有这个类，runner 只能把所有错误都当最终失败。
    def __init__(self, recoverable_markers: tuple[str, ...] | None = None) -> None:  # 新增代码+LongTaskHarness: 初始化可恢复错误关键词；若没有这行代码，策略无法配置。
        self.recoverable_markers = recoverable_markers or ("timeout", "endpoint", "rate limit", "temporarily", "connection")  # 新增代码+LongTaskHarness: 设置默认可恢复错误；若没有这行代码，常见端点问题不会自动重试。

    def is_recoverable(self, error_text: str) -> bool:  # 新增代码+LongTaskHarness: 判断错误是否适合自动继续；若没有这行代码，runner 无法区分临时错误和确定失败。
        lowered = error_text.lower()  # 新增代码+LongTaskHarness: 统一小写匹配；若没有这行代码，大小写差异会让关键词失效。
        return any(marker in lowered for marker in self.recoverable_markers)  # 新增代码+LongTaskHarness: 命中任意关键词即认为可恢复；若没有这行代码，恢复策略没有判断结果。

    def recover(self, run: HarnessRun, error_text: str) -> bool:  # 新增代码+LongTaskHarness: 对可恢复错误执行状态调整；若没有这行代码，端点恢复无法改变 run。
        if not self.is_recoverable(error_text):  # 新增代码+LongTaskHarness: 非可恢复错误直接拒绝；若没有这行代码，真实逻辑错误可能被盲目重试。
            return False  # 新增代码+LongTaskHarness: 返回不可恢复；若没有这行代码，调用方无法停止。
        if len(run.endpoints) > 1:  # 新增代码+LongTaskHarness: 多 endpoint 时才轮换；若没有这行代码，单 endpoint 任务会做无意义取模。
            run.endpoint_index = (run.endpoint_index + 1) % len(run.endpoints)  # 新增代码+LongTaskHarness: 切到下一个 endpoint；若没有这行代码，端点故障后仍会打原端点。
        return True  # 新增代码+LongTaskHarness: 返回已执行恢复动作；若没有这行代码，runner 无法决定是否重试。
