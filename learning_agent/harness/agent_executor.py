"""把 harness 阶段执行接到真实 LearningAgent 的适配器。"""  # 新增代码+HarnessCliAgentExecution: 说明本文件只负责连接 HarnessRunner 和 LearningAgent.run；若没有这行代码，维护者不清楚这里为什么存在。

from __future__ import annotations  # 新增代码+HarnessCliAgentExecution: 延迟解析类型注解；若没有这行代码，Any 和模型类型扩展时更容易受导入顺序影响。

from pathlib import Path  # 新增代码+HarnessCliAgentExecution: 默认构建真实 agent 时需要定位 learning_agent 工作区；若没有这行代码，CLI agent 模式容易找错路径。
from typing import Any  # 新增代码+HarnessCliAgentExecution: agent 实例来自核心层，适配器只要求它有 run 方法；若没有这行代码，类型边界会被写死。

from learning_agent.harness.models import HarnessRun, HarnessStage  # 新增代码+HarnessCliAgentExecution: 适配器签名需要 run 和 stage；若没有这行代码，HarnessRunner 无法类型化调用。


class AgentStageExecutor:  # 新增代码+HarnessCliAgentExecution: 把单个 harness 阶段转成一次 LearningAgent.run 调用；若没有这个类，harness 仍无法驱动真实 agent。
    def __init__(self, agent: Any, max_turns: int | None = None) -> None:  # 新增代码+HarnessCliAgentExecution: 接收已构建 agent 和轮次上限；若没有这行代码，测试和 CLI 无法注入不同 agent。
        self.agent = agent  # 新增代码+HarnessCliAgentExecution: 保存真实或假 agent；若没有这行代码，__call__ 没有执行对象。
        self.max_turns = max_turns  # 新增代码+HarnessCliAgentExecution: 保存阶段执行轮次上限；若没有这行代码，长阶段无法限制工具循环。

    def __call__(self, run: HarnessRun, stage: HarnessStage) -> str:  # 新增代码+HarnessCliAgentExecution: 实现 HarnessRunner 需要的 executor 签名；若没有这行代码，适配器不能直接传给 runner。
        _ = run  # 新增代码+HarnessCliAgentExecution: 保留 run 参数位置以匹配协议；若没有这行代码，静态检查会提示参数未使用且未来扩展不清楚。
        return str(self.agent.run(stage.prompt, max_turns=self.max_turns))  # 新增代码+HarnessCliAgentExecution: 用阶段 prompt 调用真实 agent；若没有这行代码，harness 不会真正让 agent 做阶段工作。


def build_default_learning_agent_executor(workspace: str | Path | None = None, max_turns: int | None = None) -> AgentStageExecutor:  # 新增代码+HarnessCliAgentExecution: 为 CLI agent 模式构建默认 executor；若没有这行代码，命令行无法一键接入真实 LearningAgent。
    workspace_path = Path(workspace).resolve() if workspace is not None else Path(__file__).resolve().parents[1]  # 新增代码+HarnessCliAgentExecution: 解析工作区，默认指向 learning_agent 包目录；若没有这行代码，模型、MCP 和 memory 会找错位置。
    from learning_agent.app.cli import build_model_from_env  # 新增代码+HarnessCliAgentExecution: 懒加载模型构造函数；若没有这行代码，status/list/enqueue 也会提前加载模型依赖。
    from learning_agent.core.agent import LearningAgent, ask_permission_from_terminal_customer_mode  # 新增代码+HarnessCliAgentExecution: 懒加载真实 agent 和权限函数；若没有这行代码，agent executor 无法创建可运行实例。
    from learning_agent.core.config import load_agent_runtime_config  # 新增代码+HarnessCliAgentExecution: 懒加载运行配置；若没有这行代码，prompt 预算不会沿用项目配置。
    from learning_agent.mcp.config import load_mcp_server_configs  # 新增代码+HarnessCliAgentExecution: 懒加载 MCP 配置读取；若没有这行代码，真实 agent 模式看不到外部工具。
    from learning_agent.mcp.registry import McpToolRegistry  # 新增代码+HarnessCliAgentExecution: 懒加载 MCP 注册表；若没有这行代码，MCP 配置不能变成工具入口。
    runtime_config = load_agent_runtime_config(workspace_path)  # 新增代码+HarnessCliAgentExecution: 读取 runtime_config.json 和环境变量；若没有这行代码，agent 模式会忽略项目运行策略。
    model = build_model_from_env(workspace_path)  # 新增代码+HarnessCliAgentExecution: 按环境变量构建模型适配器；若没有这行代码，真实 agent 没有模型可用。
    mcp_configs = load_mcp_server_configs(workspace_path)  # 新增代码+HarnessCliAgentExecution: 读取 MCP server 配置；若没有这行代码，阶段执行缺少外部工具能力。
    mcp_tool_registry = McpToolRegistry.from_configs(mcp_configs)  # 新增代码+HarnessCliAgentExecution: 把 MCP 配置转成注册表；若没有这行代码，LearningAgent 无法调用 MCP 工具。
    agent = LearningAgent(model=model, workspace=workspace_path, ask_permission=ask_permission_from_terminal_customer_mode, mcp_tool_registry=mcp_tool_registry, prompt_soft_token_limit=runtime_config.prompt_soft_token_limit)  # 新增代码+HarnessCliAgentExecution: 创建真实 LearningAgent；若没有这行代码，agent executor 没有执行主体。
    return AgentStageExecutor(agent=agent, max_turns=max_turns if max_turns is not None else runtime_config.max_turns)  # 新增代码+HarnessCliAgentExecution: 返回适配器并应用轮次上限；若没有这行代码，CLI agent 模式无法交给 HarnessRunner。
