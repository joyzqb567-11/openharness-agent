"""learning_agent 的长任务运行时底座。"""  # 新增代码+HarnessRuntimeAlignment: 说明 runtime 包承载主循环、队列、任务和恢复能力；若没有这行代码，维护者不清楚该包边界。

from __future__ import annotations  # 新增代码+HarnessRuntimeAlignment: 延迟解析类型注解；若没有这行代码，导出类型以后互相引用更容易出错。

__all__: list[str] = []  # 新增代码+HarnessRuntimeAlignment: 先保留空导出列表；若没有这行代码，通配导入行为不明确。
