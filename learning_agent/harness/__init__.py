"""learning_agent 独立长任务 harness 公开 API。"""  # 新增代码+LongTaskHarness: 说明本包提供可被其他 agent 调用的长任务能力；若没有这行代码，包用途不清楚。

from __future__ import annotations  # 新增代码+LongTaskHarness: 延迟解析类型注解；若没有这行代码，后续导出类型更容易受顺序影响。

from learning_agent.harness.agent_executor import AgentStageExecutor  # 新增代码+HarnessCliAgentExecution: 导出真实 agent 阶段执行适配器；若没有这行代码，外部调用要知道内部文件路径。
from learning_agent.harness.models import HarnessAttempt, HarnessRun, HarnessStage, VerificationResult  # 新增代码+LongTaskHarness: 导出核心数据模型；若没有这行代码，外部调用要知道内部文件路径。
from learning_agent.harness.queue import HarnessQueue  # 新增代码+LongTaskHarness: 导出持久队列；若没有这行代码，外部 agent 无法稳定排队任务。
from learning_agent.harness.recovery import RecoveryPolicy  # 新增代码+LongTaskHarness: 导出恢复策略；若没有这行代码，外部调用无法配置失败恢复。
from learning_agent.harness.runner import HarnessRunner  # 新增代码+LongTaskHarness: 导出阶段 runner；若没有这行代码，外部调用无法执行任务。
from learning_agent.harness.status import render_harness_status  # 新增代码+LongTaskHarness: 导出状态渲染函数；若没有这行代码，外部 agent 无法直接显示状态。
from learning_agent.harness.store import HarnessStore  # 新增代码+LongTaskHarness: 导出持久 store；若没有这行代码，外部调用无法管理状态目录。
from learning_agent.harness.verifier import StageVerifier  # 新增代码+LongTaskHarness: 导出阶段验证器；若没有这行代码，外部调用无法做阶段验收。

__all__ = ["AgentStageExecutor", "HarnessAttempt", "HarnessQueue", "HarnessRun", "HarnessRunner", "HarnessStage", "HarnessStore", "RecoveryPolicy", "StageVerifier", "VerificationResult", "render_harness_status"]  # 修改代码+HarnessCliAgentExecution: 明确公开 API 并加入 AgentStageExecutor；若没有这行代码，外部 agent 无法稳定导入真实执行适配器。
