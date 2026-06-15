"""一个教学用的最小私人 Agent：模型调用 + tool loop + 文件工具 + 权限确认 + memory。"""  # 作用: 用模块文档说明这个文件的学习目标

from __future__ import annotations  # 作用: 让类型注解可以延迟解析，减少类定义顺序带来的麻烦

import base64  # 作用: OAuth PKCE/JWT 解析需要 base64url 编解码
import copy  # 新增代码+MCP 工具注册表健壮性: 提供深拷贝能力保护嵌套 schema 缓存；若省略: 调用方修改返回 schema 会污染注册表内部状态
import hashlib  # 作用: OAuth PKCE 需要用 SHA-256 生成 code_challenge
import http.server  # 作用: OAuth 登录时启动本地回调 HTTP 服务接收授权 code
import json  # 作用: 读写 JSON、构造提示词、解析模型结构化输出
import secrets  # 作用: 生成安全随机 call_id、PKCE verifier、OAuth state
import signal  # 修改代码+后台命令: 向 Windows 后台命令进程组发送 CTRL_BREAK_EVENT；若没有这行代码，sandbox 下 taskkill 被拒绝时无法温和终止子进程
import sys  # 新增代码+MCP诊断: 读取命令行参数以支持 mcp-doctor 模式；若省略: 用户无法从 learning_agent.py 直接进入诊断入口
import tempfile  # 作用: Codex CLI 桥接模式需要临时保存输出 schema 和最终消息
import threading  # 新增代码+MCP stdio client 健壮性: 用后台线程读取 MCP server stdout；若省略: 主线程会被阻塞 readline 卡住
import time  # 作用: 计算 OAuth access_token 是否过期
import urllib.error  # 作用: 捕获 HTTPError 并把服务端错误体展示出来
import urllib.parse  # 作用: 构造 OAuth URL、表单请求体、解析回调 query
import urllib.request  # 作用: 使用 Python 标准库发送 HTTP 请求，避免额外依赖
import webbrowser  # 作用: 首次 OAuth 登录时自动打开系统浏览器
from dataclasses import dataclass, field  # 作用: 快速定义只保存数据的小对象，并支持默认工厂
from pathlib import Path  # 作用: 用跨平台路径对象安全处理文件路径
from typing import Any, Callable, Mapping, Protocol, Sequence  # 修改代码+交互上下文: 增加 Mapping/Sequence 标注 conversation_history；若没有这行代码，历史消息接口类型会继续不清楚。

try:  # 修改代码+CoreSplit: 优先从新 core 包导入配置与消息结构；若没有这行代码，learning_agent.py 会继续承载过多基础定义。
    import learning_agent.core.message_builders as message_builders_from_core  # 修改代码+AgentPySplitPhase8: 包运行模式下导入消息构造模块；若没有这行代码，agent.py 无法调用拆出的 OpenAI messages 字典构造实现。
    import learning_agent.core.plan_runtime as plan_runtime_from_core  # 修改代码+AgentPyPhaseEPlanRuntime: 包运行模式下导入计划模式和 worktree 真实实现；若没有这行代码，agent.py 薄包装会找不到委托目标。
    import learning_agent.core.run_helpers as run_helpers_from_core  # 新增代码+AgentPySplitPhase13: 包运行模式下导入运行记录 helper；若没有这行代码，agent.py 的 run_id/session_id/observation 薄包装没有委托目标。
    from learning_agent.core.config import (  # 修改代码+CoreSplit: 包运行模式下读取配置模块导出；若没有这行代码，测试和外部包导入无法走新分层。
        DEFAULT_PROMPT_SOFT_TOKEN_LIMIT,  # 修改代码+CoreSplit: 保留旧入口常量名；若没有这行代码，LearningAgent 默认 prompt 预算会找不到。
        AgentRuntimeConfig,  # 修改代码+CoreSplit: 保留旧入口运行配置类；若没有这行代码，旧测试和旧调用方会导入失败。
        MainArgs,  # 修改代码+CoreSplit: 保留旧入口命令行参数类；若没有这行代码，main 参数解析测试会导入失败。
        format_max_turns_status,  # 修改代码+CoreSplit: 保留旧入口状态格式化函数；若没有这行代码，启动提示会找不到格式化逻辑。
        get_local_iso_date,  # 修改代码+CoreSplit: 保留旧入口日期函数；若没有这行代码，提示词构造仍会依赖主文件内部实现。
        load_agent_runtime_config,  # 修改代码+CoreSplit: 保留旧入口运行配置加载函数；若没有这行代码，main 无法加载 runtime_config.json。
        parse_cli_max_turns_value,  # 修改代码+CoreSplit: 保留旧入口 CLI 轮次解析函数；若没有这行代码，旧测试无法验证 argparse 边界。
        parse_main_args,  # 修改代码+CoreSplit: 保留旧入口 main 参数解析函数；若没有这行代码，入口层无法解析 run/bridge/doctor。
        parse_max_turns_value,  # 修改代码+CoreSplit: 保留旧入口轮次解析函数；若没有这行代码，配置解析测试会断开。
        parse_prompt_soft_token_limit_value,  # 修改代码+CoreSplit: 保留旧入口 prompt 预算解析函数；若没有这行代码，compact 预算配置会找不到解析器。
        resolve_run_max_turns,  # 修改代码+CoreSplit: 保留旧入口轮次优先级函数；若没有这行代码，CLI 覆盖配置的规则会散落回 main。
    )  # 修改代码+CoreSplit: 结束配置模块导入列表；若没有这行代码，Python 语法无法闭合。
    from learning_agent.core.events import AgentEvent, create_agent_event  # 新增代码+Stage15C: 导入运行时事件对象和工厂；若没有这行代码，LearningAgent 无法产出统一事件流。
    from learning_agent.core.messages import ModelMessage, ToolCall  # 修改代码+CoreSplit: 包运行模式下读取消息结构；若没有这行代码，模型适配器和工具循环会继续绑定主文件定义。
    from learning_agent.core.session import SessionRecord, SessionStore  # 新增代码+Stage15G: 包运行模式下导入会话摘要保存入口；若没有这行代码，run_events 无法生成可恢复 summary。
except ModuleNotFoundError as error:  # 修改代码+CoreSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因导入路径失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.config", "learning_agent.core.events", "learning_agent.core.message_builders", "learning_agent.core.messages", "learning_agent.core.plan_runtime", "learning_agent.core.run_helpers", "learning_agent.core.session"}:  # 修改代码+AgentPyPhaseEPlanRuntime: 允许脚本模式 fallback 覆盖 plan_runtime；若没有这行代码，bat 入口路径差异会被误判成真实错误。
        raise  # 修改代码+CoreSplit: 重新抛出非路径问题；若没有这行代码，真正的导入错误会被伪装成脚本模式问题。
    import core.message_builders as message_builders_from_core  # 修改代码+AgentPySplitPhase8: 脚本模式下导入消息构造模块；若没有这行代码，start_oauth_agent.bat 无法复用拆出的 messages 字典构造实现。
    import core.plan_runtime as plan_runtime_from_core  # 修改代码+AgentPyPhaseEPlanRuntime: 脚本模式下导入计划模式和 worktree 真实实现；若没有这行代码，bat 入口调用计划工具会找不到新模块。
    import core.run_helpers as run_helpers_from_core  # 新增代码+AgentPySplitPhase13: 脚本模式下导入运行记录 helper；若没有这行代码，bat 入口调用 run_id/session_id/observation 会找不到委托模块。
    from core.config import (  # 修改代码+CoreSplit: 脚本运行模式下从同目录 core 包导入配置；若没有这行代码，双击 bat 入口无法复用新模块。
        DEFAULT_PROMPT_SOFT_TOKEN_LIMIT,  # 修改代码+CoreSplit: 脚本模式保留旧入口常量名；若没有这行代码，LearningAgent 默认 prompt 预算会找不到。
        AgentRuntimeConfig,  # 修改代码+CoreSplit: 脚本模式保留旧入口运行配置类；若没有这行代码，旧调用方会导入失败。
        MainArgs,  # 修改代码+CoreSplit: 脚本模式保留旧入口命令行参数类；若没有这行代码，main 参数解析会缺少返回类型。
        format_max_turns_status,  # 修改代码+CoreSplit: 脚本模式保留状态格式化函数；若没有这行代码，启动提示无法显示轮次策略。
        get_local_iso_date,  # 修改代码+CoreSplit: 脚本模式保留日期函数；若没有这行代码，提示词无法稳定注入当天日期。
        load_agent_runtime_config,  # 修改代码+CoreSplit: 脚本模式保留配置加载函数；若没有这行代码，runtime_config.json 不会生效。
        parse_cli_max_turns_value,  # 修改代码+CoreSplit: 脚本模式保留 CLI 解析函数；若没有这行代码，--max-turns 错误提示会断开。
        parse_main_args,  # 修改代码+CoreSplit: 脚本模式保留参数解析函数；若没有这行代码，bat 启动后的命令分支会失效。
        parse_max_turns_value,  # 修改代码+CoreSplit: 脚本模式保留轮次解析函数；若没有这行代码，配置层无法解析正整数和 none。
        parse_prompt_soft_token_limit_value,  # 修改代码+CoreSplit: 脚本模式保留 prompt 预算解析函数；若没有这行代码，软预算配置无法解析。
        resolve_run_max_turns,  # 修改代码+CoreSplit: 脚本模式保留轮次优先级函数；若没有这行代码，CLI 与配置文件优先级会丢失。
    )  # 修改代码+CoreSplit: 结束脚本模式配置导入列表；若没有这行代码，Python 语法无法闭合。
    from core.events import AgentEvent, create_agent_event  # 新增代码+Stage15C: 脚本模式下导入运行时事件对象和工厂；若没有这行代码，bat 入口无法使用事件流。
    from core.messages import ModelMessage, ToolCall  # 修改代码+CoreSplit: 脚本运行模式下读取消息结构；若没有这行代码，直接执行文件时工具调用对象会找不到。
    from core.session import SessionRecord, SessionStore  # 新增代码+Stage15G: 脚本模式下导入会话摘要保存入口；若没有这行代码，bat 入口无法生成可恢复 summary。


try:  # 修改代码+ModelsSplit: 优先从新 models 包导入模型接口和适配器；若没有这行代码，learning_agent.py 会继续承载模型实现细节。
    from learning_agent.models.base import ChatModel, stream_chat_events  # 修改代码+Stage15C: 同时导入模型接口和流式兼容入口；若没有 stream_chat_events，run_events 无法统一消费旧模型和流式模型。
    from learning_agent.models.codex_cli import CodexCliChatModel, RunCodexFunction  # 修改代码+ModelsSplit: 包运行模式下导入 Codex CLI 适配器和测试注入类型；若没有这行代码，CLI 模型入口会断开。
    from learning_agent.models.codex_oauth import CodexOAuthChatModel, LoginCallbackFunction, PostJsonFunction  # 修改代码+ModelsSplit: 包运行模式下导入 OAuth/API 模型和回调类型；若没有这行代码，OAuth 模型入口会断开。
    from learning_agent.models.fake import ToolCallingFakeModel  # 修改代码+AgentPyPhaseKFakeModel: 包运行模式下从模型层导入测试假模型；若没有这行代码，旧的 core.agent 导出会找不到假模型。
    from learning_agent.models.oauth_tokens import CodexOAuthTokenStore, CodexOAuthTokens  # 修改代码+ModelsSplit: 包运行模式下导入 OAuth token 数据和存储；若没有这行代码，token 逻辑仍会混在主文件。
    from learning_agent.models.openai_chat import OpenAIChatModel  # 修改代码+ModelsSplit: 包运行模式下导入默认 OpenAI-compatible 模型；若没有这行代码，默认模型提供方会断开。
except ModuleNotFoundError as error:  # 修改代码+ModelsSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因导入路径失败。
    if error.name not in {"learning_agent", "learning_agent.models", "learning_agent.models.base", "learning_agent.models.codex_cli", "learning_agent.models.codex_oauth", "learning_agent.models.fake", "learning_agent.models.oauth_tokens", "learning_agent.models.openai_chat"}:  # 修改代码+AgentPyPhaseKFakeModel: 允许 fake 模型路径差异进入脚本 fallback；若没有这行代码，直接运行时可能找不到新假模型模块。
        raise  # 修改代码+ModelsSplit: 重新抛出非路径问题；若没有这行代码，真正的导入错误会被伪装成脚本模式问题。
    from models.base import ChatModel, stream_chat_events  # 修改代码+Stage15C: 脚本模式下导入模型接口和流式兼容入口；若没有 stream_chat_events，bat 入口无法运行事件流主循环。
    from models.codex_cli import CodexCliChatModel, RunCodexFunction  # 修改代码+ModelsSplit: 脚本运行模式下导入 Codex CLI 适配器；若没有这行代码，bat 入口无法使用 CLI 模型。
    from models.codex_oauth import CodexOAuthChatModel, LoginCallbackFunction, PostJsonFunction  # 修改代码+ModelsSplit: 脚本运行模式下导入 OAuth/API 模型；若没有这行代码，bat 入口无法使用 OAuth 模型。
    from models.fake import ToolCallingFakeModel  # 修改代码+AgentPyPhaseKFakeModel: 脚本模式下从模型层导入测试假模型；若没有这行代码，start_oauth_agent.bat 相关脚本无法兼容旧假模型导出。
    from models.oauth_tokens import CodexOAuthTokenStore, CodexOAuthTokens  # 修改代码+ModelsSplit: 脚本运行模式下导入 OAuth token 数据和存储；若没有这行代码，OAuth token 入口会找不到。
    from models.openai_chat import OpenAIChatModel  # 修改代码+ModelsSplit: 脚本运行模式下导入默认 OpenAI-compatible 模型；若没有这行代码，默认模型入口会找不到。


try:  # 修改代码+AgentPyCompatWrapperRemovalL8: 优先从新 mcp 包导入核心仍需要的配置、客户端和 registry；若没有这行代码，LearningAgent 初始化外部 MCP 工具会断开。
    from learning_agent.mcp.auth import McpAuthChallenge, McpAuthenticationRequired  # 修改代码+McpSplit: 包运行模式下导入 MCP 鉴权挑战类型；若没有这行代码，HTTP 401 恢复入口会断开。
    from learning_agent.mcp.config import McpServerConfig, format_mcp_startup_status, load_mcp_server_configs, mcp_server_config_path  # 修改代码+McpSplit: 包运行模式下导入 MCP 配置解析和启动状态函数；若没有这行代码，mcp_servers.json 入口会断开。
    from learning_agent.mcp.http_client import McpHttpClient, McpHttpStreamEvent, McpHttpStreamState, McpSessionExpired  # 修改代码+McpSplit: 包运行模式下导入 HTTP MCP client 和流状态类型；若没有这行代码，远程 HTTP MCP 支持会断开。
    from learning_agent.mcp.registry import McpToolRegistry  # 修改代码+McpSplit: 包运行模式下导入 MCP 工具注册表；若没有这行代码，外部工具发现和路由会断开。
    from learning_agent.mcp.sse_client import McpSseClient  # 修改代码+McpSplit: 包运行模式下导入旧 SSE 边界 client；若没有这行代码，legacy SSE 配置无法被明确处理。
    from learning_agent.mcp.stdio_client import McpStdioClient  # 修改代码+McpSplit: 包运行模式下导入 stdio MCP client；若没有这行代码，本地 MCP server 无法启动。
except ModuleNotFoundError as error:  # 修改代码+McpSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因导入路径失败。
    if error.name not in {"learning_agent", "learning_agent.mcp", "learning_agent.mcp.auth", "learning_agent.mcp.config", "learning_agent.mcp.http_client", "learning_agent.mcp.registry", "learning_agent.mcp.sse_client", "learning_agent.mcp.stdio_client"}:  # 修改代码+AgentPyCompatWrapperRemovalL8: 删除 core.agent 的 doctor 文件级入口后不再把 mcp.doctor 作为核心导入依赖；若没有这行代码，真实导入错误和脚本模式 fallback 会混在一起。
        raise  # 修改代码+McpSplit: 重新抛出非路径问题；若没有这行代码，真正的导入错误会被伪装成脚本模式问题。
    from mcp.auth import McpAuthChallenge, McpAuthenticationRequired  # 修改代码+McpSplit: 脚本运行模式下导入 MCP 鉴权挑战类型；若没有这行代码，直接执行文件时鉴权边界会找不到。
    from mcp.config import McpServerConfig, format_mcp_startup_status, load_mcp_server_configs, mcp_server_config_path  # 修改代码+McpSplit: 脚本运行模式下导入 MCP 配置函数；若没有这行代码，bat 入口无法加载 mcp_servers.json。
    from mcp.http_client import McpHttpClient, McpHttpStreamEvent, McpHttpStreamState, McpSessionExpired  # 修改代码+McpSplit: 脚本运行模式下导入 HTTP MCP client 和流状态类型；若没有这行代码，远程 MCP 配置会断开。
    from mcp.registry import McpToolRegistry  # 修改代码+McpSplit: 脚本运行模式下导入 MCP registry；若没有这行代码，LearningAgent 无法发现外部工具。
    from mcp.sse_client import McpSseClient  # 修改代码+McpSplit: 脚本运行模式下导入 legacy SSE client；若没有这行代码，SSE 配置边界会找不到。
    from mcp.stdio_client import McpStdioClient  # 修改代码+McpSplit: 脚本运行模式下导入 stdio MCP client；若没有这行代码，本地 MCP server 无法启动。

try:  # 新增代码+ToolPolicyV2: 优先按包路径导入工具策略对象；若没有这行代码，LearningAgent 无法在包运行模式下复用 Task 1 的策略层
    from learning_agent.tool_policy import ToolPolicy, ToolPolicyContext, ToolPolicyDecision  # 新增代码+ToolPolicyV2: 导入策略入口、上下文和决策结果；若没有这行代码，工具池和搜索无法统一读取 visible/selectable/state/reason
except ModuleNotFoundError as error:  # 新增代码+ToolPolicyV2: 捕获脚本模式下的包路径导入失败；若没有这行代码，直接运行 learning_agent.py 可能因为包名路径不同而失败
    if error.name not in {"learning_agent", "learning_agent.tool_policy"}:  # 新增代码+ToolPolicyV2: 只允许顶层包或目标模块缺失时 fallback；若没有这行代码，tool_policy 内部依赖错误会被误吞
        raise  # 新增代码+ToolPolicyV2: 重新抛出非路径问题的导入错误；若没有这行代码，真实导入 bug 会被伪装成脚本模式 fallback
    from tool_policy import ToolPolicy, ToolPolicyContext, ToolPolicyDecision  # 新增代码+ToolPolicyV2: 脚本运行时从同目录导入策略对象；若没有这行代码，CLI 直接执行文件时策略集成不可用

try:  # 修改代码+ToolsSplit: 优先从新 tools 包导入工具类型和目录构建函数；若没有这行代码，learning_agent.py 会继续承载工具元数据实现。
    import learning_agent.tools.catalog_runtime as catalog_runtime_from_tools  # 新增代码+AgentPyPhaseHMcpToolRuntime: 包运行模式下导入工具目录/策略运行时；若没有这行代码，agent.py 薄包装会找不到委托目标。
    import learning_agent.tools.search as search_tools_from_tools  # 修改代码+AgentPyPhaseBToolSearch: 包运行模式下导入拆出的工具搜索真实实现；若没有这行代码，agent.py 薄包装仍会找不到委托目标。
    from learning_agent.tools.executor import execute_tool as execute_tool_from_registry  # 修改代码+ToolsExecutorSplit: 包运行模式下导入工具执行分发器；若没有这行代码，_execute_tool 仍要维护长 if 链。
    from learning_agent.tools.hooks import ToolHookManager  # 新增代码+Stage15E: 包运行模式下导入工具 hook 管理器；若没有这行代码，LearningAgent 无法默认挂载 hook 扩展点。
    from learning_agent.tools.orchestrator import execute_tool_calls as execute_tool_calls_from_orchestrator  # 新增代码+Stage15F: 包运行模式下导入安全并发工具编排器；若没有这行代码，主循环无法批量并发只读工具。
    from learning_agent.tools.result_storage import clamp_tool_result_inline_limit, safe_tool_artifact_name, summarize_offloaded_output  # 修改代码+ResultStorageSplit: 包运行模式下导入长结果存储 helper；若没有这行代码，文件名、inline limit 和摘要格式仍留在主入口。
    from learning_agent.tools.types import AgentTool  # 修改代码+ToolsSplit: 包运行模式下导入工具元数据类型；若没有这行代码，LearningAgent 的 catalog 类型边界会留在主文件。
except ModuleNotFoundError as error:  # 修改代码+ToolsSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因导入路径失败。
    if error.name not in {"learning_agent", "learning_agent.mcp", "learning_agent.mcp.agent_lifecycle", "learning_agent.tool_policy", "learning_agent.tools", "learning_agent.tools.catalog", "learning_agent.tools.catalog_runtime", "learning_agent.tools.executor", "learning_agent.tools.hooks", "learning_agent.tools.local_file_tools", "learning_agent.tools.orchestrator", "learning_agent.tools.pool", "learning_agent.tools.result_storage", "learning_agent.tools.search", "learning_agent.tools.types"}:  # 修改代码+AgentPyCompatWrapperRemovalL6: 删除 atom 工具包装后不再让 agent.py 直接导入 atom_tools；若没有这行代码，主类会继续把原子工具实现当成自己的导入责任。
        raise  # 修改代码+ToolsSplit: 重新抛出非路径问题；若没有这行代码，真正的导入错误会被伪装成脚本模式问题。
    import tools.catalog_runtime as catalog_runtime_from_tools  # 新增代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入工具目录/策略运行时；若没有这行代码，bat 入口调用工具池 helper 会找不到委托目标。
    import tools.search as search_tools_from_tools  # 修改代码+AgentPyPhaseBToolSearch: 脚本模式下导入拆出的工具搜索真实实现；若没有这行代码，start_oauth_agent.bat 调用 tool_search 会找不到新模块。
    from tools.executor import execute_tool as execute_tool_from_registry  # 修改代码+ToolsExecutorSplit: 脚本模式下导入工具执行分发器；若没有这行代码，直接运行时 _execute_tool 无法委托新模块。
    from tools.hooks import ToolHookManager  # 新增代码+Stage15E: 脚本模式下导入工具 hook 管理器；若没有这行代码，bat 入口无法默认挂载 hook 扩展点。
    from tools.orchestrator import execute_tool_calls as execute_tool_calls_from_orchestrator  # 新增代码+Stage15F: 脚本模式下导入安全并发工具编排器；若没有这行代码，bat 入口无法批量并发只读工具。
    from tools.result_storage import clamp_tool_result_inline_limit, safe_tool_artifact_name, summarize_offloaded_output  # 修改代码+ResultStorageSplit: 脚本模式下导入长结果存储 helper；若没有这行代码，直接执行时长输出落盘策略会断开。
    from tools.types import AgentTool  # 修改代码+ToolsSplit: 脚本模式下从同目录 tools 包导入 AgentTool；若没有这行代码，直接执行文件时工具元数据类型会找不到。

try:  # 修改代码+PromptsSplit: 优先从 prompts 包导入提示词架构组件；若没有这行代码，prompt 逻辑会继续依赖根目录旧模块入口。
    import learning_agent.prompts.dynamic_gate as dynamic_gate_from_prompts  # 修改代码+AgentPyPhaseIDynamicGate: 包运行模式下导入动态提示词门禁和提示词文件运行时；若没有这行代码，agent.py 兼容包装会找不到委托目标。
    from learning_agent.prompts.context_assembler import ContextAssembler, PromptSurfaceReport, build_long_term_memory_index  # 修改代码+PromptsSplit: 包运行模式下从 prompts 层导入上下文装配器和长期记忆索引；若没有这行代码，主 agent 无法使用新的 prompt 分层入口。
    from learning_agent.prompts.registry import build_default_prompt_registry  # 修改代码+PromptsSplit: 包运行模式下从 prompts.registry 导入默认注册表；若没有这行代码，提示词块元数据仍依赖旧路径。
except ModuleNotFoundError as error:  # 修改代码+PromptsSplit: 捕获脚本模式下包路径导入失败；若没有这行代码，直接运行 learning_agent.py 时可能找不到 prompts 包路径。
    if error.name not in {"learning_agent", "learning_agent.prompts", "learning_agent.prompts.context_assembler", "learning_agent.prompts.dynamic_gate", "learning_agent.prompts.registry"}:  # 修改代码+AgentPyCompatWrapperRemovalL4: 删除 report_tools 薄包装后不再把 report_tools 作为 agent.py 的导入依赖；若没有这行代码，脚本模式 fallback 会继续把已迁走的报告职责算作主类入口依赖。
        raise  # 修改代码+PromptsSplit: 重新抛出非路径问题；若没有这行代码，真实导入 bug 会被伪装成脚本模式 fallback。
    import prompts.dynamic_gate as dynamic_gate_from_prompts  # 修改代码+AgentPyPhaseIDynamicGate: 脚本模式下导入动态提示词门禁和提示词文件运行时；若没有这行代码，bat 入口提示词兼容包装会断开。
    from prompts.context_assembler import ContextAssembler, PromptSurfaceReport, build_long_term_memory_index  # 修改代码+PromptsSplit: 脚本模式下从 prompts 层导入上下文装配器和长期记忆索引；若没有这行代码，bat 入口无法复用新分层。
    from prompts.registry import build_default_prompt_registry  # 修改代码+PromptsSplit: 脚本模式下从 prompts.registry 导入默认注册表；若没有这行代码，直接运行时 prompt registry 会找不到。

try:  # 修改代码+BrowserSplit: 优先从 browser 包导入真实浏览器 helper；若没有这行代码，learning_agent.py 会继续承载浏览器意图和授权细节。
    import learning_agent.browser.agent_workflow as browser_agent_workflow_from_browser  # 修改代码+AgentPyPhaseFBrowserWorkflow: 包运行模式下导入浏览器 workflow 真实实现；若没有这行代码，agent.py 浏览器薄包装会找不到委托目标。
except ModuleNotFoundError as error:  # 修改代码+BrowserSplit: 捕获直接运行脚本时包路径不可用；若没有这行代码，start_oauth_agent.bat 可能找不到 learning_agent.browser。
    if error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.agent_workflow"}:  # 修改代码+AgentPyPhaseJTerminalPermissions: browser 导入块只保留 workflow 路径兜底；若没有这行代码，权限模块迁走后仍会误把 browser.permissions 当成 agent.py 依赖。
        raise  # 修改代码+BrowserSplit: 非路径问题继续抛出；若没有这行代码，真实导入错误会被伪装成脚本模式问题。
    import browser.agent_workflow as browser_agent_workflow_from_browser  # 修改代码+AgentPyPhaseFBrowserWorkflow: 脚本模式下导入浏览器 workflow 真实实现；若没有这行代码，bat 入口调用浏览器 workflow 会找不到新模块。

try:  # 修改代码+AgentPySplitPhase1: 优先从 computer_use 图片模块导入截图消息 helper；如果没有这行代码，agent.py 仍然要自己承载图片解析和转码细节。
    from learning_agent.computer_use_mcp_v2.windows_runtime.image_messages import build_computer_use_image_message_from_tool_output  # 修改代码+AgentPySplitPhase15B4: 包运行模式下只导入主循环仍直接使用的图片消息入口；如果没有这行代码，删除图片薄包装后工具截图无法回灌给模型。
except ModuleNotFoundError as error:  # 修改代码+AgentPySplitPhase1: 捕获直接运行脚本时包路径不可用的情况；如果没有这行代码，start_oauth_agent.bat 可能因为 learning_agent 包名路径不同而失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.image_messages"}:  # 修改代码+AgentPySplitPhase1: 只允许目标包路径缺失时 fallback；如果没有这行代码，image_messages 内部真实导入 bug 会被误吞。
        raise  # 修改代码+AgentPySplitPhase1: 重新抛出非路径问题；如果没有这行代码，真正的导入错误会被伪装成脚本模式问题。
    from computer_use_mcp_v2.windows_runtime.image_messages import build_computer_use_image_message_from_tool_output  # 修改代码+AgentPySplitPhase15B4: 脚本模式下只导入主循环仍直接使用的图片消息入口；如果没有这行代码，start_oauth_agent.bat 删除图片薄包装后会找不到回灌函数。

try:  # 修改代码+AgentPySplitPhase2: 优先从 computer_use 模型循环模块导入 full 模式提示和工具范围 helper；如果没有这行代码，agent.py 仍然要自己承载 full 模式提示词细节。
    from learning_agent.computer_use_mcp_v2.windows_runtime.model_loop import build_computer_use_full_model_loop_harness_message, scoped_tool_schemas_for_model_turn  # 修改代码+AgentPySplitPhase15B5: 包运行模式下只导入主循环仍直接使用的 model_loop 入口；如果没有这行代码，删除 full 模式薄包装后主循环无法生成提示或收窄工具。
except ModuleNotFoundError as error:  # 修改代码+AgentPySplitPhase2: 捕获直接运行脚本时包路径不可用的情况；如果没有这行代码，start_oauth_agent.bat 可能因为 learning_agent 包名路径不同而失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.model_loop"}:  # 修改代码+AgentPySplitPhase2: 只允许目标包路径缺失时 fallback；如果没有这行代码，model_loop 内部真实导入 bug 会被误吞。
        raise  # 修改代码+AgentPySplitPhase2: 重新抛出非路径问题；如果没有这行代码，真正的导入错误会被伪装成脚本模式问题。
    from computer_use_mcp_v2.windows_runtime.model_loop import build_computer_use_full_model_loop_harness_message, scoped_tool_schemas_for_model_turn  # 修改代码+AgentPySplitPhase15B5: 脚本模式下只导入主循环仍直接使用的 model_loop 入口；如果没有这行代码，start_oauth_agent.bat 删除 full 模式薄包装后会找不到提示和工具收窄函数。

try:  # 修改代码+AgentPySplitPhase3: 优先从 computer_use runtime_trace 模块导入运行证据 helper；如果没有这行代码，agent.py 仍然要自己承载 trace 汇总和截图登记细节。
    from learning_agent.computer_use_mcp_v2.windows_runtime.runtime_trace import computer_use_runtime_trace_report as build_computer_use_runtime_trace_report, image_artifact_recorder as build_computer_use_image_artifact_recorder, is_computer_use_tool_name, runtime_trace_recorder as build_computer_use_runtime_trace_recorder  # 修改代码+AgentPySplitPhase15B6: 包运行模式下导入 runtime trace 的公开判断、汇总和回调工厂；如果没有这行代码，删除 trace 薄包装后主循环和 Computer Use 工具入口会找不到记录函数。
except ModuleNotFoundError as error:  # 修改代码+AgentPySplitPhase3: 捕获直接运行脚本时包路径不可用的情况；如果没有这行代码，start_oauth_agent.bat 可能因为 learning_agent 包名路径不同而失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.runtime_trace"}:  # 修改代码+AgentPySplitPhase3: 只允许目标包路径缺失时 fallback；如果没有这行代码，runtime_trace 内部真实导入 bug 会被误吞。
        raise  # 修改代码+AgentPySplitPhase3: 重新抛出非路径问题；如果没有这行代码，真正的导入错误会被伪装成脚本模式问题。
    from computer_use_mcp_v2.windows_runtime.runtime_trace import computer_use_runtime_trace_report as build_computer_use_runtime_trace_report, image_artifact_recorder as build_computer_use_image_artifact_recorder, is_computer_use_tool_name, runtime_trace_recorder as build_computer_use_runtime_trace_recorder  # 修改代码+AgentPySplitPhase15B6: 脚本模式下导入 runtime trace 的公开判断、汇总和回调工厂；如果没有这行代码，start_oauth_agent.bat 删除 trace 薄包装后会找不到记录函数。

try:  # 修改代码+AgentPySplitPhase4: 优先从 computer_use 动作门禁模块导入 full 模式动作拦截和完成门 helper；如果没有这行代码，agent.py 仍然要自己承载门禁细节。
    from learning_agent.computer_use_mcp_v2.windows_runtime.action_gates import computer_use_agent_owned_launch_rejection as action_gate_agent_owned_launch_rejection, computer_use_data_has_model_visible_image as action_gate_data_has_model_visible_image, computer_use_full_completion_action_threshold as action_gate_full_completion_action_threshold, computer_use_full_completion_signal_for_action as action_gate_full_completion_signal_for_action, computer_use_full_mode_requires_agent_owned_launch as action_gate_full_mode_requires_agent_owned_launch, computer_use_full_mode_requires_model_visible_observation as action_gate_full_mode_requires_model_visible_observation, computer_use_full_recent_events_after_mode_open as action_gate_full_recent_events_after_mode_open, computer_use_full_successful_real_action_count as action_gate_full_successful_real_action_count, computer_use_has_agent_owned_launch_target as action_gate_has_agent_owned_launch_target, computer_use_has_recent_model_visible_observation as action_gate_has_recent_model_visible_observation, computer_use_observe_before_action_rejection as action_gate_observe_before_action_rejection  # 修改代码+AgentPySplitPhase4: 包运行模式下导入 Computer Use 动作门禁函数；如果没有这行代码，主 agent 无法复用拆出的新模块。
except ModuleNotFoundError as error:  # 修改代码+AgentPySplitPhase4: 捕获直接运行脚本时包路径不可用的情况；如果没有这行代码，start_oauth_agent.bat 可能因为 learning_agent 包名路径不同而失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.action_gates"}:  # 修改代码+AgentPySplitPhase4: 只允许目标包路径缺失时 fallback；如果没有这行代码，action_gates 内部真实导入 bug 会被误吞。
        raise  # 修改代码+AgentPySplitPhase4: 重新抛出非路径问题；如果没有这行代码，真正的导入错误会被伪装成脚本模式问题。
    from computer_use_mcp_v2.windows_runtime.action_gates import computer_use_agent_owned_launch_rejection as action_gate_agent_owned_launch_rejection, computer_use_data_has_model_visible_image as action_gate_data_has_model_visible_image, computer_use_full_completion_action_threshold as action_gate_full_completion_action_threshold, computer_use_full_completion_signal_for_action as action_gate_full_completion_signal_for_action, computer_use_full_mode_requires_agent_owned_launch as action_gate_full_mode_requires_agent_owned_launch, computer_use_full_mode_requires_model_visible_observation as action_gate_full_mode_requires_model_visible_observation, computer_use_full_recent_events_after_mode_open as action_gate_full_recent_events_after_mode_open, computer_use_full_successful_real_action_count as action_gate_full_successful_real_action_count, computer_use_has_agent_owned_launch_target as action_gate_has_agent_owned_launch_target, computer_use_has_recent_model_visible_observation as action_gate_has_recent_model_visible_observation, computer_use_observe_before_action_rejection as action_gate_observe_before_action_rejection  # 修改代码+AgentPySplitPhase4: 脚本模式下从同目录 computer_use 包导入动作门禁函数；如果没有这行代码，bat 入口无法复用拆出的模块。

try:  # 修改代码+AgentPySplitPhase5: 优先从 computer_use 最终证据摘要模块导入 full 模式最终回答补强 helper；如果没有这行代码，agent.py 仍然要自己承载证据摘要细节。
    from learning_agent.computer_use_mcp_v2.windows_runtime.evidence_summary import computer_use_full_collect_final_answer_evidence as evidence_summary_collect_final_answer_evidence, computer_use_full_extract_screenshot_path as evidence_summary_extract_screenshot_path, computer_use_full_extract_window_summary as evidence_summary_extract_window_summary, computer_use_full_final_answer_summary_context_active as evidence_summary_context_active, computer_use_full_final_answer_with_evidence_summary as evidence_summary_final_answer_with_evidence_summary  # 修改代码+AgentPySplitPhase5: 包运行模式下导入 Computer Use 最终证据摘要函数；如果没有这行代码，主 agent 无法复用拆出的新模块。
except ModuleNotFoundError as error:  # 修改代码+AgentPySplitPhase5: 捕获直接运行脚本时包路径不可用的情况；如果没有这行代码，start_oauth_agent.bat 可能因为 learning_agent 包名路径不同而失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.evidence_summary"}:  # 修改代码+AgentPySplitPhase5: 只允许目标包路径缺失时 fallback；如果没有这行代码，evidence_summary 内部真实导入 bug 会被误吞。
        raise  # 修改代码+AgentPySplitPhase5: 重新抛出非路径问题；如果没有这行代码，真正的导入错误会被伪装成脚本模式问题。
    from computer_use_mcp_v2.windows_runtime.evidence_summary import computer_use_full_collect_final_answer_evidence as evidence_summary_collect_final_answer_evidence, computer_use_full_extract_screenshot_path as evidence_summary_extract_screenshot_path, computer_use_full_extract_window_summary as evidence_summary_extract_window_summary, computer_use_full_final_answer_summary_context_active as evidence_summary_context_active, computer_use_full_final_answer_with_evidence_summary as evidence_summary_final_answer_with_evidence_summary  # 修改代码+AgentPySplitPhase5: 脚本模式下从同目录 computer_use 包导入最终证据摘要函数；如果没有这行代码，bat 入口无法复用拆出的模块。


try:  # 修改代码+TasksSplit: 优先从 tasks 包导入任务记录和纯 helper；若没有这行代码，learning_agent.py 会继续承载长期任务数据结构。
    from learning_agent.tasks.background import BackgroundCommand  # 修改代码+AgentPySplitPhase15B11: agent.py 只保留后台命令记录类型供状态表标注；若没有这行代码，self.background_commands 的类型边界会不清楚。
    from learning_agent.tasks.cron_monitor import CronRecord, MonitorRecord  # 修改代码+AgentPySplitPhase15B10: agent.py 只保留当前状态表需要的 Cron/Monitor 类型；若没有这行代码，__init__ 的 cron_records/monitor_records 类型边界会不清楚。
    from learning_agent.tasks.task_runs import TaskRun  # 修改代码+AgentPySplitPhase15B10: agent.py 只保留 task_runs 状态表需要的 TaskRun 类型；若没有这行代码，当前进程内 task 记录类型会不清楚。
    from learning_agent.tasks.team import TeamPeer  # 修改代码+AgentPySplitPhase15B10: agent.py 只保留 team_peers 状态表需要的 TeamPeer 类型；若没有这行代码，当前进程内 peer 记录类型会不清楚。
except ModuleNotFoundError as error:  # 修改代码+TasksSplit: 捕获直接运行脚本时包路径不可用；若没有这行代码，start_oauth_agent.bat 可能找不到 learning_agent.tasks。
    if error.name not in {"learning_agent", "learning_agent.tasks", "learning_agent.tasks.background", "learning_agent.tasks.cron_monitor", "learning_agent.tasks.task_runs", "learning_agent.tasks.team"}:  # 修改代码+AgentPySplitPhase15B10: 只允许仍被 agent.py 使用的 tasks 类型模块进入 fallback；若没有这行代码，真实导入错误会被误吞。
        raise  # 修改代码+TasksSplit: 非路径问题继续抛出；若没有这行代码，真实导入错误会被伪装成脚本模式问题。
    from tasks.background import BackgroundCommand  # 修改代码+AgentPySplitPhase15B11: 脚本模式下只保留后台命令记录类型供状态表标注；若没有这行代码，bat 入口初始化 background_commands 类型边界会不清楚。
    from tasks.cron_monitor import CronRecord, MonitorRecord  # 修改代码+AgentPySplitPhase15B10: 脚本模式下只保留当前状态表需要的 Cron/Monitor 类型；若没有这行代码，bat 入口初始化状态表时类型边界会不清楚。
    from tasks.task_runs import TaskRun  # 修改代码+AgentPySplitPhase15B10: 脚本模式下只保留 task_runs 状态表需要的 TaskRun 类型；若没有这行代码，bat 入口初始化任务记录时类型边界会不清楚。
    from tasks.team import TeamPeer  # 修改代码+AgentPySplitPhase15B10: 脚本模式下只保留 team_peers 状态表需要的 TeamPeer 类型；若没有这行代码，bat 入口初始化 peer 记录时类型边界会不清楚。

try:  # 新增代码+AgentPySplitPhase12: 优先按包路径导入后台命令运行时模块；若没有这行代码，agent.py 的后台命令薄包装没有委托目标。
    import learning_agent.runtime.background_commands as background_commands_from_runtime  # 修改代码+AgentPySplitPhase15B11: 包运行模式下保留后台命令运行时模块给公共输出长度解析使用；若没有这行代码，skill_load 的 max_chars 解析会断开。
except ModuleNotFoundError as error:  # 新增代码+AgentPySplitPhase12: 捕获脚本模式下包路径不可用；若没有这行代码，start_oauth_agent.bat 直接运行可能找不到 learning_agent.runtime。
    if error.name not in {"learning_agent", "learning_agent.runtime", "learning_agent.runtime.background_commands"}:  # 新增代码+AgentPySplitPhase12: 只允许目标路径缺失时 fallback；若没有这行代码，runtime 内部真实 bug 会被误吞。
        raise  # 新增代码+AgentPySplitPhase12: 重新抛出非路径问题；若没有这行代码，真实导入错误会被伪装成脚本模式 fallback。
    import runtime.background_commands as background_commands_from_runtime  # 修改代码+AgentPySplitPhase15B11: 脚本模式下保留后台命令运行时模块给公共输出长度解析使用；若没有这行代码，bat 入口的 skill_load 截断解析会断开。

try:  # 修改代码+ObservabilitySplit: 优先从观测层导入验收、调试、权限和运行记录 helper；若没有这行代码，learning_agent.py 会继续承载观测实现细节。
    import learning_agent.observability.debug_formatting as debug_formatting_from_observability  # 修改代码+AgentPySplitPhase15B7: 包运行模式下导入 debug 写入和 Markdown 排版模块；若没有这行代码，删除 debug 薄包装后主循环会找不到日志入口。
    from learning_agent.observability.run_records import build_final_answer_event_payload  # 修改代码+ObservabilitySplit: 包运行模式下导入最终回答事件 payload helper；若没有这行代码，验收字段仍散在入口循环。
    from learning_agent.observability.transcript import TranscriptWriter  # 新增代码+Stage15C: 导入 transcript 写入器；若没有这行代码，run_events 只能 yield 事件但不能落盘恢复。
except ModuleNotFoundError as error:  # 修改代码+ObservabilitySplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能找不到 learning_agent.observability。
    if error.name not in {"learning_agent", "learning_agent.observability", "learning_agent.observability.debug_formatting", "learning_agent.observability.debug_log", "learning_agent.observability.run_records", "learning_agent.observability.transcript"}:  # 修改代码+AgentPyCompatWrapperRemovalL4: 删除状态查询薄包装后不再让 agent.py 导入 status_tools；若没有这行代码，脚本模式 fallback 会继续把状态工具实现当成主类入口依赖。
        raise  # 修改代码+ObservabilitySplit: 重新抛出非路径导入错误；若没有这行代码，真实依赖错误会被伪装成脚本模式。
    import observability.debug_formatting as debug_formatting_from_observability  # 修改代码+AgentPySplitPhase15B7: 脚本模式下导入 debug 写入和 Markdown 排版模块；若没有这行代码，start_oauth_agent.bat 删除 debug 薄包装后会找不到日志入口。
    from observability.run_records import build_final_answer_event_payload  # 修改代码+ObservabilitySplit: 脚本模式下导入最终回答事件 payload helper；若没有这行代码，真实终端最终回答事件会断开。
    from observability.transcript import TranscriptWriter  # 新增代码+Stage15C: 脚本模式下导入 transcript 写入器；若没有这行代码，bat 入口无法写入事件 transcript。

try:  # 新增代码+ToolSchemaSplit: 包运行模式下从工具 schema 模块读取唯一事实源；若没有这行代码，core.agent 仍会继续保存大块工具定义。
    from learning_agent.tools.schemas import BUILTIN_TOOL_CAPABILITY_PACKS, DYNAMIC_SKILL_CAPABILITY_PACKS, KERNEL_TOOL_NAMES, TOOL_SCHEMAS  # 新增代码+ToolSchemaSplit: 导入内置工具、能力包和动态 skill 映射；若没有这行代码，LearningAgent 无法构建工具目录。
except ModuleNotFoundError as error:  # 新增代码+ToolSchemaSplit: 捕获直接脚本运行时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因包路径失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.schemas"}:  # 新增代码+ToolSchemaSplit: 只允许目标路径缺失时 fallback；若没有这行代码，schemas 模块内部真实 bug 会被误吞。
        raise  # 新增代码+ToolSchemaSplit: 重新抛出真实导入错误；若没有这行代码，排查工具 schema 问题会很困难。
    from tools.schemas import BUILTIN_TOOL_CAPABILITY_PACKS, DYNAMIC_SKILL_CAPABILITY_PACKS, KERNEL_TOOL_NAMES, TOOL_SCHEMAS  # 新增代码+ToolSchemaSplit: 脚本模式下从同目录 tools 包读取 schema；若没有这行代码，直接执行 learning_agent.py 会找不到工具定义。


class LearningAgent:  # 作用: 教学版 agent 主类
    def __init__(  # 修改代码+DesktopTaskPolicy：函数段开始，初始化参数保持旧调用方式并补充桌面任务策略上下文；如果没有这个函数段，agent 无法保存模型、workspace、权限和 Task 3 的 active 状态，作者意图是让 `_bash_atom` 能知道当前是否处于桌面任务，本段与 `_bash_atom` 配合到初始化字段结束。
        self,  # 修改代码: 当前 agent 对象
        model: ChatModel,  # 修改代码: 模型客户端，可能是真模型也可能是假模型
        workspace: str | Path,  # 修改代码: agent 允许读写的工作区路径
        ask_permission: Callable[[str], bool],  # 修改代码: 写文件/写记忆前询问用户的权限函数
        debug_log_path: str | Path | None = None,  # 新增代码: 可选自定义调试日志路径；不传则使用工作区 debug_logs/agent_debug.jsonl
        debug_enabled: bool = True,  # 新增代码: 是否开启调试日志；默认开启，方便初学者直接观察 agent 流程
        mcp_tool_registry: McpToolRegistry | None = None,  # 新增代码+MCP接入LearningAgent: 允许调用方注入 MCP 工具注册表；若省略: LearningAgent 无法把 Task 4 的 registry 接入模型和工具执行链路
        allowed_tool_names: set[str] | None = None,  # 新增代码+TaskAgent: 可选工具白名单供子 agent 限制可见工具；若省略: 子 agent 无法收窄工具范围
        inherited_mcp_tools_enabled: bool | None = None,  # 新增代码+TaskAgent: 子 agent 可继承父 agent 的 MCP 启用状态而不重复启动；若省略: 子 agent 会按普通 agent 流程处理 MCP
        inherited_mcp_start_error: str = "",  # 新增代码+TaskAgent: 子 agent 可继承父 agent 的 MCP 启动错误；若省略: MCP 不可用原因会在子 agent 中丢失
        stop_event: threading.Event | None = None,  # 新增代码+AsyncTask: 可选协作取消信号供后台子 agent 轮询；若省略: task_stop 无法让子 agent 在循环边界主动停止
        prompt_soft_token_limit: int = DEFAULT_PROMPT_SOFT_TOKEN_LIMIT,  # 新增代码+PromptArchitectureV1: 允许调用方配置提示词装配软预算；若没有这行代码，生产路径无法真实触发 compact summary
    ) -> None:
        self.model = model  # 作用: 保存模型客户端，可能是真模型也可能是假模型
        self.workspace = Path(workspace).expanduser().resolve()  # 作用: 保存并规范化工作区路径
        self.ask_permission = ask_permission  # 作用: 保存权限确认函数
        self.allowed_tool_names = allowed_tool_names  # 新增代码+TaskAgent: 保存工具白名单，None 表示当前 agent 不做工具过滤；若省略: _available_tool_schemas 无法判断是否需要过滤
        self.mcp_tool_registry = mcp_tool_registry or McpToolRegistry()  # 新增代码+MCP接入LearningAgent: 保存 MCP registry 并为空配置创建空注册表；若省略: 后续 schema 合并和工具分发需要反复判断 None
        self.mcp_tools_enabled = False  # 新增代码+MCP接入健壮性: 默认先禁用 MCP 工具直到启动流程明确成功；若省略: 拒绝或失败后可能继续暴露旧 registry 工具
        self.loaded_tool_names: set[str] = set()  # 新增代码+ToolArchitectureV2: 保存已经被加载进当前工具池的 deferred 工具名；若没有这行代码，agent 无法区分完整 catalog 和本轮可见工具池
        self.tool_policy = ToolPolicy()  # 新增代码+ToolPolicyV2: 保存工具策略入口供工具池、搜索和 select 复用；若没有这行代码，LearningAgent 各处会继续手写不一致的可见性规则
        self.tool_policy_context = ToolPolicyContext()  # 新增代码+ToolPolicyV2: 保存当前 agent 的策略上下文；若没有这行代码，deny/skill/workflow 状态无法在 LearningAgent 内长期维护
        self.desktop_task_context: dict[str, Any] = {"active": False}  # 新增代码+DesktopTaskPolicy：初始化桌面任务策略上下文，默认未激活；如果没有这一行，_bash_atom 无法判断何时必须阻止脚本生成最终图片制品。
        self.tool_scope_mode: str = "auto"  # 新增代码+ClaudeCodeToolSurface：默认让工具池模式根据 desktop_task_context 自动推断；如果没有这一行，catalog_runtime 无法区分代码开发和 Computer Use 操作工具面。
        self.prompt_registry = build_default_prompt_registry()  # 新增代码+PromptArchitectureV1: 保存默认提示词注册表供每轮 ContextAssembler 使用；若没有这行代码，LearningAgent 无法按 block priority 装配系统提示词
        self.last_prompt_surface_report = PromptSurfaceReport.empty()  # 新增代码+PromptArchitectureV1: 初始化空的提示词表面报告；若没有这行代码，测试或用户在首轮前读取报告会遇到属性缺失
        self.prompt_soft_token_limit = prompt_soft_token_limit  # 新增代码+PromptArchitectureV1: 保存本 agent 的提示词软预算；若没有这行代码，_build_initial_messages 无法把配置传给 ContextAssembler
        self.permission_denials: set[str] = set()  # 新增代码+ToolPolicyV2: 记录用户拒绝过的 MCP 工具和清洗后参数指纹；若没有这行代码，同一被拒请求会反复弹权限确认打扰用户
        self.tool_hooks = ToolHookManager()  # 新增代码+Stage15E: 为每个 agent 默认挂载工具 hook 管理器；若没有这行代码，外部必须手动创建属性才能接入执行器生命周期。
        try:  # 新增代码+OSComputerUse: 优先按包路径导入 Computer Use 控制器；若没有这行代码，桌面控制能力无法在 agent 初始化时挂载。
            from learning_agent.computer_use_mcp_v2.windows_runtime.controller import ComputerUseController  # 新增代码+OSComputerUse: 读取 OS 级 Computer Use 控制器；若没有这行代码，computer_status/computer_action 没有执行入口。
        except ModuleNotFoundError as error:  # 新增代码+OSComputerUse: 兼容直接脚本运行时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因导入路径崩溃。
            if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.controller"}:  # 新增代码+OSComputerUse: 只吞目标包路径缺失；若没有这行代码，控制器内部真实 bug 会被误吞。
                raise  # 新增代码+OSComputerUse: 重新抛出真实导入错误；若没有这行代码，排查 Computer Use 问题会很困难。
            from computer_use_mcp_v2.windows_runtime.controller import ComputerUseController  # 新增代码+OSComputerUse: 脚本模式下从本地包导入控制器；若没有这行代码，直接执行入口无法初始化桌面能力。
        self.computer_use_controller = ComputerUseController()  # 新增代码+OSComputerUse: 挂载默认安全关闭的 Computer Use 控制器；若没有这行代码，新工具路由会找不到后端状态。
        self.computer_use_turn_cleanup_runtime = None  # 新增代码+TurnCleanupLifecycleRootRemediation：预留 Computer Use turn cleanup runtime 注入点；如果没有这一行，主循环 finally 无法复用测试或生产 cleanup 依赖。
        self.mcp_call_progress_events: list[dict[str, Any]] = []  # 新增代码+MCPProgress: 保存 MCP 调用从权限、开始、完成到失败的结构化进度；若没有这行代码，Phase 3 的 call progress 只能靠肉眼看终端文本
        self.observation_events: list[dict[str, Any]] = []  # 新增代码+ObservationV1: 保存工具结果、权限、错误和上下文压缩相关观察事件；若没有这行代码，Phase 6 无法提供可审计的 structured observation
        self.computer_use_runtime_trace_events: list[dict[str, Any]] = []  # 新增代码+RuntimeTrace：保存 Computer Use 在模型主循环里的运行时证据；如果没有这行代码，后续瘦身只能靠静态源码猜测哪些入口真实跑过。
        self._tool_catalog_cache: list[AgentTool] | None = None  # 新增代码+ToolPolicyV2: 缓存本 agent 的完整工具目录对象；若没有这行代码，测试或运行时对 catalog 工具设置 gate 后下一次查找会丢失修改
        self.pending_loaded_tool_names: set[str] = set()  # 新增代码+ToolPolicyV2: 保存 run 当前批次中已 select 但要到下一轮才生效的工具名；若没有这行代码，同批 tool_calls 会立刻绕过下一轮工具池语义
        self.defer_tool_select_until_next_turn = False  # 新增代码+ToolPolicyV2: 标记当前是否正在 run 的一批 tool_calls 内延迟 select 生效；若没有这行代码，普通直接 select 和 run 批量 select 无法区分
        self.mcp_start_error = ""  # 新增代码+MCP接入健壮性: 保存 MCP 启动失败或拒绝的可读状态；若省略: 用户和测试无法知道 MCP 为什么不可用
        self.real_chrome_requested = False  # 新增代码+RealChromeWorkflow: 记录本轮用户是否明确要求真实桌面浏览器；若没有这行代码，工具策略无法把真实 Chrome 需求和独立 Chromium 默认路径区分开
        self.real_browser_information_task_requested = False  # 新增代码+真实浏览器客户模式: 记录本轮是否是公开信息查询类真实浏览器任务；若没有这行代码，自动授权无法只限定在天气、会议、酒店、航班、资料等查询场景
        self.visible_browser_information_task_requested = False  # 新增代码+自然可见浏览器路由: 记录本轮普通实时查询是否需要可见独立浏览器；若没有这行代码，主循环无法在首轮预加载 browser_launch_visible。
        self.plan_mode_state: dict[str, Any] = {"active": False}  # 新增代码+PlanMode: 保存当前 agent 是否处于计划模式及计划上下文；若省略: exit_plan_mode 无法判断是否先进入过计划模式
        self.worktree_state: dict[str, Any] = {"active": False}  # 新增代码+WorktreeIsolation: 保存当前 agent 是否处于轻量工作区隔离状态；若省略: exit_worktree 无法判断是否先进入过隔离上下文
        self.stop_event = stop_event  # 新增代码+AsyncTask: 保存当前 agent 的取消信号，None 表示普通同步 agent 不需要检查取消；若省略: run 循环无法响应 task_stop
        self.task_runs: dict[str, TaskRun] = {}  # 新增代码+TaskLifecycle: 保存当前 agent 进程内的 task 子任务记录；若省略: task_output/task_stop 无法按 task_id 找回任务
        self.team_peers: dict[str, TeamPeer] = {}  # 新增代码+TeamCommunication: 保存当前 agent 进程内的教学版 peer 登记表；若省略: team_create 创建后 list_peers/send_message 无法找回 peer
        self.cron_records: dict[str, CronRecord] = {}  # 新增代码+CronMonitor: 保存当前 agent 进程内的教学版定时任务记录；若省略: cron_list/delete 无法找回 cron_create 结果
        self.monitor_records: dict[str, MonitorRecord] = {}  # 新增代码+CronMonitor: 保存当前 agent 进程内的教学版监控记录；若省略: monitor list/delete/record_result 无法找回创建结果
        self.background_commands: dict[str, BackgroundCommand] = {}  # 新增代码+后台命令: 保存当前 agent 进程内启动的后台命令；若省略: read/stop 无法根据 command_id 找到进程
        from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+DurableTaskRegistry: 延迟导入运行时命令队列避免顶层循环导入；若没有这行代码，task notification 无法写入 durable queue。
        from learning_agent.runtime.task_registry import TaskRegistry  # 新增代码+DurableTaskRegistry: 延迟导入持久任务登记表；若没有这行代码，task 子任务仍只能保存在内存字典。
        from learning_agent.runtime.team_registry import TeamRegistry  # 新增代码+DurableTeamRegistry: 延迟导入持久 team 登记表；若没有这行代码，team peer 仍只能保存在当前进程内存里。
        self.runtime_command_queue = RuntimeCommandQueue(self.workspace / "memory" / "runtime")  # 新增代码+DurableTaskRegistry: 初始化主 agent 的持久命令队列；若没有这行代码，任务完成通知无法跨进程恢复。
        self.task_registry = TaskRegistry(self.workspace / "memory" / "tasks", command_queue=self.runtime_command_queue)  # 新增代码+DurableTaskRegistry: 初始化持久任务登记表并接入通知队列；若没有这行代码，task_output 无法跨 agent 实例读取旧任务。
        self.team_registry = TeamRegistry(self.workspace / "memory" / "team")  # 新增代码+DurableTeamRegistry: 初始化持久 team peer 登记表；若没有这行代码，新 agent 实例无法读取旧 peer 和 inbox。
        self.debug_enabled = debug_enabled  # 新增代码: 保存调试日志开关，测试或高级用户可以关闭自动记录
        self.debug_log_path = Path(debug_log_path).expanduser().resolve() if debug_log_path else self.workspace / "debug_logs" / "agent_debug.jsonl"  # 新增代码: 保存调试日志文件路径，默认位于工作区 debug_logs 文件夹
        self.debug_readable_log_path = self.debug_log_path.parent / "agent_debug_readable.md"  # 新增代码: 保存追加版 Markdown 可读日志路径，方便用记事本长期查看全部运行记录
        self.debug_latest_run_path = self.debug_log_path.parent / "latest_run_readable.md"  # 新增代码: 保存最新一轮 Markdown 可读日志路径，方便每次测试后只看最近一次流程
        self.tool_result_artifact_dir = self.debug_log_path.parent / "tool_results"  # 新增代码+ResultPersistence: 约定长工具结果落盘目录；若没有这行代码，大输出只能塞回模型上下文或散落到不稳定位置
        self.active_artifacts: list[str] = []  # 新增代码+ResultPersistence: 记录当前 agent 会话内仍相关的结果文件；若没有这行代码，后续 compact 或审计无法知道哪些落盘输出仍在使用
        self.workspace.mkdir(parents=True, exist_ok=True)  # 作用: 确保工作区目录存在
        self.memory_path = self.workspace / "memory.md"  # 作用: 约定长期记忆文件固定叫 memory.md
        self.todo_path = self.workspace / "todo_state.json"  # 新增代码+TodoWrite: 约定内部任务清单文件固定叫 todo_state.json；若省略: todo_read/todo_write 无法共享持久状态
        self.skills_path = self.workspace / "skills"  # 新增代码+SkillLoad: 约定本地 skills 根目录固定叫 skills；若省略: skill_list 和 skill_load 无法找到本地说明书
        self.static_prompt_path = self._resolve_static_prompt_path()  # 新增代码+PromptFiles: 解析每轮常驻的 staticprompt.md；若没有这行代码，静态系统提示词仍会被 Python helper 硬编码
        self.dynamic_prompt_path = self._resolve_dynamic_prompt_path()  # 新增代码+PromptFiles: 解析按需加载的 dynamicprompt.md；若没有这行代码，动态运行规则迁移后没有稳定入口
        self.loaded_dynamic_prompt_paths: set[str] = set()  # 新增代码+动态提示词分层: 记录本轮已经通过 read 读取过的动态提示词层级；若没有这行代码，模型可以跳过 tool_list 和父 SKILL 直接读取大量子规则
        if not self.memory_path.exists():  # 作用: 如果 memory.md 还不存在
            self.memory_path.write_text("# Memory\n\n", encoding="utf-8")  # 作用: 创建一个最小 memory 文件
        if inherited_mcp_tools_enabled is not None:  # 新增代码+TaskAgent: 如果调用方明确传入父 agent 的 MCP 状态；若省略: 子 agent 会重复走启动授权流程
            self.mcp_tools_enabled = inherited_mcp_tools_enabled  # 新增代码+TaskAgent: 复用父 agent 是否启用 MCP 的结果；若省略: 子 agent 无法继承已启动工具列表
            self.mcp_start_error = inherited_mcp_start_error  # 新增代码+TaskAgent: 复用父 agent 的 MCP 错误说明；若省略: 子 agent 遇到 MCP 不可用时缺少原因
        elif not self.mcp_tool_registry.has_servers():  # 修改代码+TaskAgent: 未继承 MCP 状态时才按普通空 registry 逻辑处理；若省略: 子 agent 继承状态后仍会被空配置覆盖
            self.mcp_tools_enabled = True  # 新增代码+MCP接入健壮性: 空 registry 视为可用但没有工具，保持旧 agent 行为；若省略: 无 MCP 场景可能误报工具不可用
        elif self.mcp_tool_registry.has_servers():  # 修改代码+MCP接入健壮性: 只有存在 MCP server 时才请求启动权限；若省略: 无法区分空 registry 与需要授权的外部 server
            server_names = ", ".join(self.mcp_tool_registry.server_names())  # 新增代码+MCP接入LearningAgent: 把 server 名组合成可读文本；若省略: 用户不知道本次要启动哪些 MCP server
            action = f"启动 MCP server：{server_names}"  # 新增代码+MCP接入LearningAgent: 构造启动权限说明；若省略: 权限回调缺少清晰操作描述
            if self.ask_permission(action):  # 新增代码+MCP接入LearningAgent: 在启动外部 MCP server 前请求用户允许；若省略: agent 会绕过权限边界直接启动外部进程或 client
                try:  # 新增代码+MCP接入健壮性: 捕获 registry.start 异常避免 agent 构造崩溃；若省略: 单个 MCP server 启动失败会拖垮整个 agent
                    self.mcp_tool_registry.start()  # 新增代码+MCP接入LearningAgent: 权限允许后启动 registry 并加载 MCP tool schemas；若省略: 模型看不到 MCP 工具且无法调用它们
                    start_errors_method = getattr(self.mcp_tool_registry, "start_errors", None)  # 新增代码+MCP启动隔离: 读取 registry 的部分失败查询方法；若省略: 上层无法展示哪些 server 启动失败
                    start_errors = start_errors_method() if callable(start_errors_method) else {}  # 新增代码+MCP启动隔离: 兼容旧测试 registry 没有 start_errors 方法；若省略: 自定义 registry 会在初始化时崩溃
                    has_available_servers_method = getattr(self.mcp_tool_registry, "has_available_servers", None)  # 新增代码+MCP启动隔离: 读取 registry 的可用 server 判断方法；若省略: 上层无法区分部分失败和全部失败
                    has_available_servers = has_available_servers_method() if callable(has_available_servers_method) else True  # 新增代码+MCP启动隔离: 旧 registry 启动未抛错时默认视为可用；若省略: 兼容测试对象会被误判为不可用
                    if has_available_servers:  # 新增代码+MCP启动隔离: 只要有成功 server 或 authenticate 伪工具就继续启用 MCP；若省略: browser_automation 坏掉会拖垮其他 MCP server
                        self.mcp_tools_enabled = True  # 修改代码+MCP启动隔离: 部分失败时仍允许暴露成功 server 的 MCP 工具；若省略: ok server 的工具会被错误隐藏
                        if start_errors:  # 新增代码+MCP启动隔离: 如果存在部分失败记录就生成用户可读提示；若省略: 用户不知道哪些 server 没启动成功
                            error_details = "；".join(f"{server}={message}" for server, message in start_errors.items())  # 新增代码+MCP启动隔离: 把失败表格式化成 server=error 文本；若省略: 错误说明不便于定位
                            self.mcp_start_error = f"部分 MCP server 启动失败：{error_details}"  # 新增代码+MCP启动隔离: 保存部分失败说明但不禁用 MCP；若省略: 用户无法排查坏 server
                    else:  # 新增代码+MCP启动隔离: 处理没有任何成功 server 或 authenticate 入口的全部失败场景；若省略: 全部失败可能仍被当成 MCP 可用
                        self.mcp_tools_enabled = False  # 新增代码+MCP启动隔离: 全部失败时禁用 MCP 工具暴露和调用；若省略: 模型可能调用不存在的 MCP route
                        error_details = "；".join(f"{server}={message}" for server, message in start_errors.items())  # 新增代码+MCP启动隔离: 汇总全部失败 server 的错误文本；若省略: 用户看不到具体失败原因
                        if error_details:  # 新增代码+MCP启动隔离: 如果 registry 提供了失败明细就写入明细；若省略: 全部失败时定位信息会丢失
                            self.mcp_start_error = f"所有 MCP server 启动失败：{error_details}"  # 新增代码+MCP启动隔离: 保存所有 server 失败说明；若省略: 用户无法区分全部失败和权限拒绝
                        else:  # 新增代码+MCP启动隔离: 处理没有明细但也没有可用 server 的异常边界；若省略: mcp_start_error 可能保持空字符串
                            self.mcp_start_error = "所有 MCP server 启动失败：没有可用 server 或 authenticate 工具。"  # 新增代码+MCP启动隔离: 提供兜底错误说明；若省略: 用户不知道 MCP 为什么不可用
                except Exception as error:  # 新增代码+MCP接入健壮性: 把 MCP 启动异常转换成状态而不是继续抛出；若省略: 构造 LearningAgent 会因外部 server 故障失败
                    self.mcp_start_error = f"MCP server 启动失败：{error}"  # 新增代码+MCP接入健壮性: 保存可读启动失败原因；若省略: 用户无法排查 MCP 启动问题
                    self.mcp_tools_enabled = False  # 新增代码+MCP接入健壮性: 启动失败后禁用 MCP 工具暴露和调用；若省略: 半启动 registry 可能仍被模型使用
                    try:  # 新增代码+MCP接入清理: 启动失败后尝试关闭已经部分启动的 MCP client；若省略: 多 server 场景下已启动进程可能残留运行
                        self.mcp_tool_registry.close()  # 新增代码+MCP接入清理: 统一调用 registry.close 清理所有 client；若省略: 成功启动但后续失败的 server 不会被释放
                    except Exception:  # 新增代码+MCP接入清理: 忽略清理阶段异常以保证 agent 构造仍然可恢复；若省略: close 失败会再次让 LearningAgent 初始化崩溃
                        pass  # 新增代码+MCP接入清理: 清理失败时保持原始启动失败状态并继续禁用 MCP；若省略: except 块语法不完整且无法安全吞掉 close 异常
            else:  # 新增代码+MCP接入健壮性: 处理用户拒绝启动 MCP server 的分支；若省略: 拒绝后没有明确禁用状态
                self.mcp_start_error = "用户拒绝启动 MCP server。"  # 新增代码+MCP接入健壮性: 保存用户拒绝启动的可读状态；若省略: 后续 MCP 不可用原因不清楚
                self.mcp_tools_enabled = False  # 新增代码+MCP接入健壮性: 用户拒绝启动时禁用 MCP 工具；若省略: 复用 registry 的旧 schema 和 route 可能继续生效

    def run(self, user_input: str, max_turns: int | None = None, event_callback: Callable[[Any], None] | None = None, conversation_history: Sequence[Mapping[str, Any]] | None = None) -> str:  # 修改代码+交互上下文: 增加可选历史消息参数；若没有这行代码，真实终端第二轮无法把第一轮问答传入模型。
        if max_turns is not None and max_turns < 1:  # 新增代码+可配置轮次: 保护直接调用 run() 时传入非法轮次；若省略: 0 或负数会导致一开始就安全停止且难以理解
            raise ValueError("max_turns 必须是正整数，或使用 None 表示不按固定轮次主动停止。")  # 新增代码+可配置轮次: 给出清楚错误；若省略: 调用方不知道应该传什么值
        # 修改代码+ModelLoopComputerUse：这里刻意不再调用 _desktop_task_runtime_answer_from_prompt；如果保留模型前抢跑，Python 分类器会替模型理解“画猫/画房子/操作任意软件”，/computer use --full 就无法像 ClaudeCode 一样由模型结合工具 schema、屏幕观察和工具结果自主规划。
        from learning_agent.runtime.session_runtime import run_agent_with_harness_session  # 新增代码+HarnessSessionRuntime: 延迟导入 harness session runtime 避免初始化阶段循环导入；若没有这行代码，真实 run() 仍会绕过 durable harness。
        return run_agent_with_harness_session(self, user_input, max_turns=max_turns, event_callback=event_callback, conversation_history=conversation_history)  # 修改代码+交互上下文: 把历史消息继续透传给 harness runtime；若没有这行代码，run_events 仍然只能看到当前输入。

    def _desktop_task_policy_context_from_prompt(self, user_input: str) -> dict[str, Any]:  # 新增代码+DesktopTaskPolicy：函数段开始，把用户自然语言 prompt 转成脱敏桌面任务策略上下文；如果没有这段函数，run_events 无法在真实模型工具循环前自动设置 active，作者意图是复用 Task 2 分类器而不保存原始 prompt，本函数与 run_events 和 _bash_atom 配合到 return 结束。
        try:  # 新增代码+DesktopTaskPolicy：优先按包运行模式导入桌面任务分类器；如果没有这一行，unittest 和包启动路径无法复用 Task 2 分类逻辑。
            from learning_agent.computer_use_mcp_v2.windows_runtime.desktop_task_router import classify_desktop_task  # 新增代码+DesktopTaskPolicy：导入自然语言桌面任务分类函数；如果没有这一行，策略上下文只能靠手动 monkeypatch。
        except ModuleNotFoundError as error:  # 新增代码+DesktopTaskPolicy：兼容直接脚本运行时 learning_agent 包路径不可用的情况；如果没有这一行，bat 入口可能因包名前缀失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.desktop_task_router"}:  # 新增代码+DesktopTaskPolicy：只对目标包路径缺失做 fallback；如果没有这一行，分类器内部真实 bug 会被误吞。
                raise  # 新增代码+DesktopTaskPolicy：重新抛出非目标导入错误；如果没有这一行，排查分类器内部问题会很困难。
            from computer_use_mcp_v2.windows_runtime.desktop_task_router import classify_desktop_task  # 新增代码+DesktopTaskPolicy：脚本模式下从本地 computer_use 包导入分类函数；如果没有这一行，start_oauth_agent.bat 可能无法加载 Task 2 分类器。
        intent = classify_desktop_task(user_input)  # 新增代码+DesktopTaskPolicy：用同一套桌面任务分类器判断当前 prompt；如果没有这一行，active 状态会和 Task 2 路由结果分裂。
        previous_context = getattr(self, "desktop_task_context", {})  # 修改代码+ComputerUseMcpV2SchemaNarrowingFix：读取 `/computer use` 已写入的上一轮桌面模式事实；如果没有这一行，下一条自然语言会覆盖 terminal_mode/runtime，导致 v2 MCP 全量工具被旧首轮收窄逻辑误删。
        previous_context = previous_context if isinstance(previous_context, dict) else {}  # 修改代码+ComputerUseMcpV2SchemaNarrowingFix：只信任字典形状的旧上下文；如果没有这一行，异常测试替身或坏缓存会让下面读取 terminal_mode 时报错。
        previous_runtime = str(previous_context.get("runtime", "") or "")  # 修改代码+ComputerUseMcpV2SchemaNarrowingFix：提取旧上下文里的运行时标记；如果没有这一行，无法判断当前是不是已打开的 computer_use_mcp_v2 会话。
        previous_terminal_mode = str(previous_context.get("terminal_mode", "") or "")  # 修改代码+ComputerUseMcpV2SchemaNarrowingFix：提取 `/computer use --full/observe/normal` 写入的终端模式；如果没有这一行，后续 model_loop 不知道这轮来自已授权 Computer Use 模式。
        current_scope_mode = str(getattr(self, "tool_scope_mode", "") or "")  # 修改代码+ComputerUseMcpV2SchemaNarrowingFix：读取当前工具池模式；如果没有这一行，仅凭旧上下文可能在 stop 后误保留 Computer Use 会话。
        keep_computer_use_v2_session = bool(previous_runtime == "computer_use_mcp_v2" and previous_terminal_mode in {"full", "normal", "observe"} and current_scope_mode in {"computer_use_operation", "computer_use_debug"})  # 修改代码+ComputerUseMcpV2SchemaNarrowingFix：只有 v2 运行时、有效终端模式、仍处于 Computer Use scope 三者同时满足才继承会话；如果没有这一行，旧模式事实可能污染普通代码任务。
        context = {  # 修改代码+ComputerUseMcpV2SchemaNarrowingFix：先构造本轮脱敏上下文字典，后面再按已打开的 v2 会话补充字段；如果没有这一行，无法安全合并 prompt 分类结果和 terminal session 状态。
            "active": bool(intent.is_desktop_task),  # 新增代码+DesktopTaskPolicy：把是否桌面任务写入 active；如果没有这一项，bash 策略不会知道何时必须拦截脚本绕路。
            "reason": intent.reason,  # 新增代码+DesktopTaskPolicy：保存分类原因而不是原始 prompt；如果没有这一项，日志难以解释为什么开启或关闭桌面任务门禁。
            "target_app_hint": intent.target_app_hint,  # 新增代码+DesktopTaskPolicy：保存目标应用提示；如果没有这一项，后续 runtime 无法复用本次识别到的 Paint/mspaint 线索。
            "task_goal": intent.task_goal,  # 新增代码+DesktopTaskPolicy：保存脱敏任务目标摘要；如果没有这一项，后续 GUI runtime 缺少稳定目标类型。
            "requires_gui_actions": bool(intent.requires_gui_actions),  # 新增代码+DesktopTaskPolicy：保存是否需要 GUI 动作；如果没有这一项，策略无法区分本地应用观察和真正操作。
            "raw_prompt_included": bool(intent.raw_prompt_included),  # 新增代码+DesktopTaskPolicy：明确记录没有保存原始 prompt；如果没有这一项，后续审计无法确认脱敏边界。
        }  # 新增代码+DesktopTaskPolicy：上下文字典结束；如果没有这一行，Python 字典语法不完整。
        if keep_computer_use_v2_session:  # 修改代码+ComputerUseMcpV2SchemaNarrowingFix：已由 `/computer use` 打开的 v2 会话要优先于本轮 prompt 的重新分类；如果没有这一行，ClaudeCode 风格 17 个 MCP 工具会在真实主循环里被错误缩成两个。
            context.update({"active": True, "requires_gui_actions": True, "runtime": "computer_use_mcp_v2", "terminal_mode": previous_terminal_mode, "terminal_command": str(previous_context.get("terminal_command", "") or ""), "computer_use_mcp_v2_session_active": True})  # 修改代码+ComputerUseMcpV2SchemaNarrowingFix：把 v2 会话事实写回本轮上下文；如果没有这一行，model_loop 无法区分“自动识别的桌面任务”和“用户已经打开 Computer Use MCP 模式”的任务。
        return context  # 修改代码+ComputerUseMcpV2SchemaNarrowingFix：返回合并后的上下文；如果没有这一行，调用方拿不到保留了 terminal_mode/runtime 的结果。
    # 新增代码+DesktopTaskPolicy：函数段结束，_desktop_task_policy_context_from_prompt 到此结束；如果没有这个边界说明，代码小白不容易看出上下文构造范围。

    def _restore_desktop_task_policy_context(self, previous_context: dict[str, Any]) -> None:  # 新增代码+DesktopTaskPolicy：函数段开始，恢复 run_events 进入前的桌面任务上下文；如果没有这段函数，桌面任务 active 可能污染下一轮普通任务，作者意图是让上下文生命周期严格绑定单次 run_events，本函数与 run_events 的 finally 配合到赋值结束。
        if isinstance(previous_context, dict):  # 新增代码+DesktopTaskPolicy：只在旧上下文确实是字典时原样恢复；如果没有这一行，异常形状可能再次污染 desktop_task_context。
            self.desktop_task_context = copy.deepcopy(previous_context)  # 新增代码+DesktopTaskPolicy：深拷贝恢复旧上下文避免共享可变对象；如果没有这一行，后续修改可能影响保存的旧值。
            return  # 新增代码+DesktopTaskPolicy：恢复完成后直接返回；如果没有这一行，下面的兜底 inactive 会覆盖合法旧上下文。
        self.desktop_task_context = {"active": False}  # 新增代码+DesktopTaskPolicy：旧上下文不是字典时兜底恢复为 inactive；如果没有这一行，异常状态可能让下一轮 bash 策略崩溃。
    # 新增代码+DesktopTaskPolicy：函数段结束，_restore_desktop_task_policy_context 到此结束；如果没有这个边界说明，代码小白不容易看出上下文恢复范围。

    def _computer_use_lock_root_for_cleanup(self) -> Path:  # 新增代码+TurnCleanupLifecycleRootRemediation：函数段开始，计算 agent 主循环使用的 Computer Use 锁目录；如果没有这段函数，run_events cleanup 可能和 `/computer` 命令写到不同位置。
        if self.workspace.name == "learning_agent":  # 新增代码+TurnCleanupLifecycleRootRemediation：兼容直接以 learning_agent 子目录作为 workspace 的运行方式；如果没有这一行，脚本入口会多嵌一层 learning_agent。
            return self.workspace / "memory" / "computer_use" / "locks"  # 新增代码+TurnCleanupLifecycleRootRemediation：返回子目录运行时的锁目录；如果没有这一行，cleanup 找不到控制器使用的 lock/abort 状态。
        return self.workspace / "learning_agent" / "memory" / "computer_use" / "locks"  # 新增代码+TurnCleanupLifecycleRootRemediation：返回项目根运行时的锁目录；如果没有这一行，真实终端和主循环状态会分裂。
    # 新增代码+TurnCleanupLifecycleRootRemediation：函数段结束，_computer_use_lock_root_for_cleanup 到此结束；如果没有这个边界说明，读者不容易看出路径规则范围。

    def _computer_use_cleanup_runtime(self) -> Any:  # 新增代码+TurnCleanupLifecycleRootRemediation：函数段开始，获取或创建 Computer Use cleanup runtime；如果没有这段函数，finally 里会混入重复导入和构造逻辑。
        existing_runtime = getattr(self, "computer_use_turn_cleanup_runtime", None)  # 新增代码+TurnCleanupLifecycleRootRemediation：优先读取测试或外部注入的 runtime；如果没有这一行，单元测试无法观察 cleanup 调用。
        if existing_runtime is not None:  # 新增代码+TurnCleanupLifecycleRootRemediation：判断是否已有 runtime；如果没有这一行，注入对象会被生产对象覆盖。
            return existing_runtime  # 新增代码+TurnCleanupLifecycleRootRemediation：返回注入 runtime；如果没有这一行，测试和未来宿主接线无法复用自己的 cleanup。
        try:  # 新增代码+TurnCleanupLifecycleRootRemediation：优先按包路径导入 cleanup runtime；如果没有这一段，正常 python -m 运行无法创建生产 cleanup。
            from learning_agent.computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager  # 新增代码+TurnCleanupLifecycleRootRemediation：导入 durable lock manager；如果没有这一行，cleanup runtime 没有 lock/abort 状态源。
            from learning_agent.computer_use_mcp_v2.windows_runtime.session_runtime import WindowsComputerUseSessionRuntime  # 新增代码+TurnCleanupLifecycleRootRemediation：导入 session cleanup runtime；如果没有这一行，主循环只能手写释放逻辑。
        except ModuleNotFoundError as error:  # 新增代码+TurnCleanupLifecycleRootRemediation：兼容 start_oauth_agent.bat 脚本路径；如果没有这一段，双击 bat 可能因包名前缀失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.lock", "learning_agent.computer_use_mcp_v2.windows_runtime.session_runtime"}:  # 新增代码+TurnCleanupLifecycleRootRemediation：只对包路径差异 fallback；如果没有这一行，真实模块内部错误会被误吞。
                raise  # 新增代码+TurnCleanupLifecycleRootRemediation：重新抛出非路径类导入错误；如果没有这一行，排查 cleanup runtime bug 会很困难。
            from computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager  # type: ignore  # 新增代码+TurnCleanupLifecycleRootRemediation：脚本模式导入 lock manager；如果没有这一行，bat 入口无法创建 cleanup runtime。
            from computer_use_mcp_v2.windows_runtime.session_runtime import WindowsComputerUseSessionRuntime  # type: ignore  # 新增代码+TurnCleanupLifecycleRootRemediation：脚本模式导入 session runtime；如果没有这一行，bat 入口无法清理 Computer Use 状态。
        lock_manager = ComputerUseLockManager(base_dir=self._computer_use_lock_root_for_cleanup())  # 新增代码+TurnCleanupLifecycleRootRemediation：创建同 workspace 的锁管理器；如果没有这一行，cleanup 会清理默认全局目录而不是当前项目目录。
        runtime = WindowsComputerUseSessionRuntime(lock_manager=lock_manager)  # 新增代码+TurnCleanupLifecycleRootRemediation：创建生产 cleanup runtime；如果没有这一行，finally 没有实际 cleanup 实现。
        self.computer_use_turn_cleanup_runtime = runtime  # 新增代码+TurnCleanupLifecycleRootRemediation：缓存 runtime 供本 agent 后续轮次复用；如果没有这一行，每次 cleanup 都会重复创建对象。
        return runtime  # 新增代码+TurnCleanupLifecycleRootRemediation：返回 cleanup runtime；如果没有这一行，调用方拿不到可执行对象。
    # 新增代码+TurnCleanupLifecycleRootRemediation：函数段结束，_computer_use_cleanup_runtime 到此结束；如果没有这个边界说明，读者不容易看出 runtime 构造范围。

    def _run_computer_use_turn_cleanup_if_needed(self, computer_use_used: bool, reason: str) -> dict[str, Any]:  # 新增代码+TurnCleanupLifecycleRootRemediation：函数段开始，按需执行 Computer Use turn cleanup；如果没有这段函数，finally 会把判断、异常保护和 observation 写入混在一起。
        if not computer_use_used:  # 新增代码+TurnCleanupLifecycleRootRemediation：只有本轮实际使用过 Computer Use 工具才清理；如果没有这一行，普通代码任务也会无意义触碰桌面控制状态。
            return {"cleanup_skipped": True, "reason": "computer_use_not_used"}  # 新增代码+TurnCleanupLifecycleRootRemediation：返回 no-op 报告；如果没有这一行，调用方无法区分未使用和清理失败。
        try:  # 新增代码+TurnCleanupLifecycleRootRemediation：保护 cleanup 不吞掉原始 run 异常；如果没有这一段，cleanup 自身失败会覆盖真正的模型或工具错误。
            runtime = self._computer_use_cleanup_runtime()  # 新增代码+TurnCleanupLifecycleRootRemediation：获取 cleanup runtime；如果没有这一行，无法调用 session cleanup。
            cleanup_method = getattr(runtime, "cleanup_turn", None)  # 新增代码+TurnCleanupLifecycleRootRemediation：读取 runtime cleanup 方法；如果没有这一行，坏注入对象会直接 AttributeError。
            if not callable(cleanup_method):  # 新增代码+TurnCleanupLifecycleRootRemediation：验证 cleanup 方法可调用；如果没有这一行，错误 runtime 会在 finally 中崩溃。
                report = {"cleanup_completed": False, "cleanup_error": "cleanup_turn_not_callable", "reason": str(reason)}  # 新增代码+TurnCleanupLifecycleRootRemediation：构造不可调用错误报告；如果没有这一行，用户看不到 cleanup 为什么没有执行。
            else:  # 新增代码+TurnCleanupLifecycleRootRemediation：runtime 方法有效时进入真实 cleanup；如果没有这一行，Python 分支语法不完整。
                report = dict(cleanup_method(reason=reason) or {})  # 新增代码+TurnCleanupLifecycleRootRemediation：执行 cleanup 并规范成字典；如果没有这一行，锁和 abort 状态不会被释放。
        except BaseException as error:  # 新增代码+TurnCleanupLifecycleRootRemediation：捕获 cleanup 自身异常；如果没有这一行，finally 可能吞掉原始 run_failed 事件。
            report = {"cleanup_completed": False, "cleanup_error": str(error), "cleanup_error_type": type(error).__name__, "reason": str(reason)}  # 新增代码+TurnCleanupLifecycleRootRemediation：记录 cleanup 失败原因；如果没有这一行，排查只能看到主流程继续但不知道 cleanup 失败。
        run_helpers_from_core.record_observation(self, "computer_use_turn_cleanup", report)  # 新增代码+TurnCleanupLifecycleRootRemediation：把 cleanup evidence 写入 observation；如果没有这一行，验收和最终回答看不到 turn cleanup 证据。
        return report  # 新增代码+TurnCleanupLifecycleRootRemediation：返回 cleanup 报告；如果没有这一行，未来调用方无法复用结果。
    # 新增代码+TurnCleanupLifecycleRootRemediation：函数段结束，_run_computer_use_turn_cleanup_if_needed 到此结束；如果没有这个边界说明，读者不容易看出按需 cleanup 范围。

    def run_events(self, user_input: str, max_turns: int | None = None, conversation_history: Sequence[Mapping[str, Any]] | None = None):  # 修改代码+交互上下文: 事件流主循环接收可选历史消息；若没有这行代码，run() 透传的终端历史无法进入模型消息。
        # 修改代码+AgentPySplitPhase14: 第 1 段是“运行前准备”，负责校验轮次、生成 session/run id、创建 transcript/status/ledger 等运行账本；若没有这个流程标记，代码小白很难看出下面这一长段还没有真正进入模型循环。
        if max_turns is not None and max_turns < 1:  # 新增代码+Stage15C: 保留旧 run 的非法轮次校验；若没有这行代码，0 或负数会产生难懂行为。
            raise ValueError("max_turns 必须是正整数，或使用 None 表示不按固定轮次主动停止。")  # 新增代码+Stage15C: 给出旧兼容错误；若没有这行代码，调用方不知道正确 max_turns 格式。
        session_id = run_helpers_from_core.new_session_id()  # 修改代码+AgentPySplitPhase15B7: 主循环直接调用 core/run_helpers.py 生成 session id；若没有这行代码，删除 `_new_session_id` 后 transcript 无法按会话归档。
        run_id = run_helpers_from_core.new_debug_run_id()  # 修改代码+AgentPySplitPhase15B7: 主循环直接调用 core/run_helpers.py 生成 debug run id；若没有这行代码，删除 `_new_debug_run_id` 后事件无法串起同一次运行。
        debug_event_writer = debug_formatting_from_observability.debug_event_writer(self.debug_enabled, self.debug_log_path, self.debug_readable_log_path, self.debug_latest_run_path)  # 修改代码+AgentPySplitPhase15B7: 从 observability/debug_formatting.py 获取调试日志写入回调；若没有这行代码，删除 `_write_debug_event` 后 JSONL 和 Markdown 调试日志会断开。
        transcript_writer = TranscriptWriter(self.workspace / "memory" / "sessions", session_id)  # 新增代码+Stage15C: 创建 transcript 写入器；若没有这行代码，事件只会在内存中一闪而过。
        session_store = SessionStore(self.workspace / "memory" / "sessions")  # 新增代码+Stage15G: 创建会话摘要 store；若没有这行代码，run_events 只能写 events.jsonl 而不能保存 resume summary。
        from learning_agent.core.compact_pipeline import prepare_messages_before_model, recover_from_context_overflow  # 修改代码+ContextCompactRepairRuntime: 主循环只调用 compact 流水线；若没有这行代码，agent.py 会继续散落压缩和 reactive compact 细节。
        from learning_agent.core.continuation_controller import decide_after_model_response  # 新增代码+ContextCompactRepairRuntime: 引入 ClaudeCode 对齐层继续/结束判断；若没有这行代码，主循环仍靠裸 if tool_calls 收束。
        from learning_agent.core.convergence_controller import assess_before_model, decide_tool_call, record_tool_result  # 新增代码+ContextCompactRepairRuntime: 引入 OpenHarness 增强收束控制；若没有这行代码，重复工具和读日志恢复任务无法统一拦截。
        from learning_agent.core.task_state import TaskState  # 新增代码+ContextCompactRepairRuntime: 引入任务状态事实源；若没有这行代码，compact 和收束无法稳定保留用户目标。
        from learning_agent.core.transcript_v2 import TranscriptV2Store  # 新增代码+CompactResumeStatus: 延迟导入 transcript v2 store；若没有这行代码，真实主循环不会写入可回放事件链。
        from learning_agent.core.turn_ledger import TurnLedger  # 新增代码+CompactResumeStatus: 延迟导入 turn ledger；若没有这行代码，中断后无法知道每一轮走到哪里。
        from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+CompactResumeStatus: 延迟导入统一状态事件 store；若没有这行代码，终端、SDK、HTTP 看不到真实主循环事件。
        transcript_v2_store = TranscriptV2Store(self.workspace / "memory" / "sessions")  # 新增代码+CompactResumeStatus: 创建 transcript v2 写入器；若没有这行代码，compact/resume 证据仍只存在旁路测试里。
        turn_ledger = TurnLedger(self.workspace / "memory" / "sessions")  # 新增代码+CompactResumeStatus: 创建轮次账本；若没有这行代码，恢复时无法跳过已完成阶段。
        status_event_store = StatusEventStore(self.workspace / "memory" / "status")  # 新增代码+CompactResumeStatus: 创建状态事件事实源；若没有这行代码，状态 UI/SDK/API 会和真实 run_events 分裂。
        session_messages: list[dict[str, Any]] = []  # 新增代码+Stage15G: 保存本轮可恢复消息快照；若没有这行代码，summary.json 无法记录上下文。
        session_tool_calls: list[dict[str, Any]] = []  # 新增代码+Stage15G: 保存本轮工具调用摘要；若没有这行代码，恢复和审计看不到模型调用过什么工具。
        session_tool_results: list[dict[str, Any]] = []  # 新增代码+Stage15G: 保存本轮工具结果摘要；若没有这行代码，恢复时缺少外部观察结果。
        sequence = 0  # 新增代码+Stage15C: 初始化事件顺序号；若没有这行代码，transcript 无法稳定排序。
        last_transcript_uuid = ""  # 新增代码+CompactResumeStatus: 保存 transcript v2 最近事件 uuid；若没有这行代码，事件链无法形成父子关系。
        current_turn_id = "turn_0"  # 新增代码+CompactResumeStatus: 保存当前轮次 id 供异常恢复使用；若没有这行代码，失败时无法更新 turn ledger。
        reactive_compact_attempted_turns: set[int] = set()  # 新增代码+ReactiveCompactRuntime: 记录哪些 turn 已经做过一次 reactive compact；若没有这行代码，模型反复报超限时可能无限重试。

        # 修改代码+AgentPySplitPhase14: 第 2 段是“事件写入器”，emit 会同时写旧 transcript、v2 transcript、status event，再把事件 yield 给外部；若没有这个流程标记，读者会误以为 emit 只是普通 print。
        def emit(event_type: str, payload: dict[str, Any]) -> AgentEvent:  # 新增代码+Stage15C: 定义统一事件创建和落盘 helper；若没有这行代码，主循环每处都要重复写事件逻辑。
            nonlocal sequence, last_transcript_uuid  # 修改代码+CompactResumeStatus: 允许内部 helper 推进顺序号并维护 transcript 父子链；若没有这行代码，事件序号和 v2 链接都无法更新。
            sequence += 1  # 新增代码+Stage15C: 每发一个事件就递增顺序；若没有这行代码，恢复 transcript 时事件顺序会不可靠。
            event = create_agent_event(event_type=event_type, run_id=run_id, sequence=sequence, session_id=session_id, payload=payload)  # 新增代码+Stage15C: 创建标准 AgentEvent；若没有这行代码，事件字段会散落成普通字典。
            transcript_writer.write_event(event)  # 新增代码+Stage15C: 把事件追加写入 JSONL；若没有这行代码，任务中断后无法恢复事件历史。
            raw_turn_marker = payload.get("turn", "run") if isinstance(payload, dict) else "run"  # 新增代码+CompactResumeStatus: 从事件载荷提取轮次标记；若没有这行代码，transcript v2 无法按 turn 归档事件。
            transcript_turn_id = f"turn_{raw_turn_marker}" if isinstance(raw_turn_marker, int) else str(raw_turn_marker)  # 新增代码+CompactResumeStatus: 把数字轮次转成稳定 turn_id；若没有这行代码，恢复器会遇到 int/string 混用。
            transcript_entry = transcript_v2_store.append_entry(session_id=session_id, run_id=run_id, turn_id=transcript_turn_id, event_type=event_type, payload=event.to_json_dict(), parent_uuid=last_transcript_uuid)  # 新增代码+CompactResumeStatus: 把同一个 AgentEvent 写入 transcript v2；若没有这行代码，run_events 与 resume 事实源仍然分裂。
            last_transcript_uuid = transcript_entry.uuid  # 新增代码+CompactResumeStatus: 推进父子链到最新事件；若没有这行代码，下一条 transcript v2 事件无法追溯上一条。
            status_event_store.append(event_type, {"sequence": sequence, "payload": copy.deepcopy(payload)}, session_id=session_id, run_id=run_id, turn_id=transcript_turn_id)  # 修改代码+StatusSchemaV2: 把 session/run/turn 写成状态事件顶层字段；若没有这行代码，SDK/API 仍要拆 payload 才能定位真实主循环事件。
            return event  # 新增代码+Stage15C: 返回事件给 yield 使用；若没有这行代码，调用方收不到事件对象。

        # 修改代码+AgentPySplitPhase14: 第 3 段是“会话摘要保存器”，最终回答出现时把消息、工具调用、权限决策和 artifact 汇总成 summary；若没有这个流程标记，读者不容易看出恢复数据在哪里落盘。
        def save_session_summary(final_answer: str) -> Path:  # 新增代码+Stage15G: 保存当前 session 的可恢复摘要；若没有这行代码，完成后只能靠原始事件手工恢复。
            permission_decisions = [event for event in self.observation_events if event.get("kind") == "permission_decided"]  # 新增代码+Stage15G: 从观察流提取权限决策；若没有这行代码，summary 无法复盘授权过程。
            record = SessionRecord(session_id=session_id, run_id=run_id, user_input=user_input, messages=copy.deepcopy(session_messages), tool_calls=copy.deepcopy(session_tool_calls), tool_results=copy.deepcopy(session_tool_results), permission_decisions=copy.deepcopy(permission_decisions), final_answer=final_answer, artifacts=list(self.active_artifacts))  # 新增代码+Stage15G: 构造会话摘要对象；若没有这行代码，store 没有完整数据可写。
            return session_store.save_summary(record)  # 新增代码+Stage15G: 写入 summary.json 并返回路径；若没有这行代码，session 摘要不会落盘。

        # 修改代码+AgentPySplitPhase14: 第 4 段是“进入主循环前的上下文保护”，先保存旧桌面任务状态，再用 try/finally 保证本轮结束后恢复；若没有这个流程标记，读者容易忽略 desktop_task_context 的生命周期。
        previous_desktop_task_context = copy.deepcopy(self.desktop_task_context) if isinstance(getattr(self, "desktop_task_context", {}), dict) else {"active": False}  # 新增代码+DesktopTaskPolicy：保存进入本轮 run_events 前的桌面任务上下文；如果没有这一行，finally 无法把 active 清回旧状态。
        computer_use_used_this_run = False  # 新增代码+TurnCleanupLifecycleRootRemediation：记录本轮是否实际使用过 Computer Use 工具；如果没有这一行，finally 不知道该不该触发 cleanup。
        try:  # 新增代码+Stage15C: 捕获主循环异常并转成 run_failed 事件；若没有这行代码，事件消费者会看到生成器直接崩溃。
            # 修改代码+AgentPySplitPhase14: 第 5 段是“接收用户输入并构造初始消息”，这里会记录 run_started、turn_accepted、用户 prompt、工具池前置状态和 harness 消息；若没有这个流程标记，读者很难分清模型请求前做了哪些准备。
            self.desktop_task_context = self._desktop_task_policy_context_from_prompt(user_input)  # 新增代码+DesktopTaskPolicy：在模型请求和工具执行前根据自然语言 prompt 设置 active；如果没有这一行，真实桌面任务的 _bash_atom 仍会按 inactive 放行脚本绕路。
            run_started_event = emit("run_started", {"user_input": user_input})  # 修改代码+CompactResumeStatus: 先创建运行开始事件再记录 turn ledger；若没有这行代码，后续账本无法引用开始事件序号。
            yield run_started_event  # 修改代码+CompactResumeStatus: 发出运行开始事件；若没有这行代码，UI 无法知道任务何时开始。
            user_entry = transcript_v2_store.append_entry(session_id=session_id, run_id=run_id, turn_id="turn_0", event_type="user_message", payload={"content": user_input}, parent_uuid=last_transcript_uuid)  # 新增代码+CompactResumeStatus: 在模型请求前持久化用户原始 prompt；若没有这行代码，中断恢复时会丢失真实输入证据。
            last_transcript_uuid = user_entry.uuid  # 新增代码+CompactResumeStatus: 把用户输入事件作为最新 checkpoint；若没有这行代码，后续模型请求无法指向 prompt。
            turn_ledger.accept_turn(session_id=session_id, run_id=run_id, turn_id="turn_0", user_input=user_input, metadata={"run_started_sequence": run_started_event.sequence, "user_entry_uuid": user_entry.uuid})  # 新增代码+CompactResumeStatus: 记录 turn_0 已接收；若没有这行代码，恢复器不知道用户 prompt 已进入主循环。
            turn_ledger.update_status(session_id=session_id, turn_id="turn_0", status="accepted", checkpoint_uuid=user_entry.uuid)  # 新增代码+CompactResumeStatus: 给 turn_0 写入第一个安全恢复点；若没有这行代码，中断后无法从用户输入处继续。
            yield emit("turn_accepted", {"turn": 0, "turn_id": "turn_0", "checkpoint_uuid": user_entry.uuid})  # 新增代码+StatusSchemaV2: 把 turn 接收写入同一条事件流；若没有这行代码，状态 CLI/API 只能从账本推测当前 turn。
            if self._stop_requested():  # 新增代码+Stage15C: 在构造上下文前检查取消信号；若没有这行代码，取消后的子 agent 仍会继续请求模型。
                turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="interrupted", checkpoint_uuid=last_transcript_uuid, metadata={"reason": "stop_requested_before_context"})  # 新增代码+CompactResumeStatus: 取消时更新 turn ledger；若没有这行代码，恢复器会误以为 turn 还在 accepted。
                yield emit("run_completed", {"text": "任务已停止：收到取消请求。", "reason": "stop_requested"})  # 新增代码+Stage15C: 把取消作为完成事件返回；若没有这行代码，事件消费者拿不到取消提示。
                return  # 新增代码+Stage15C: 取消后结束事件流；若没有这行代码，后续仍会继续构造消息。
            self.real_chrome_requested = browser_agent_workflow_from_browser.detect_real_chrome_intent(user_input)  # 修改代码+AgentPyCompatWrapperRemovalL7: 主循环直接调用 browser workflow 判断真实 Chrome 意图；若没有这行代码，删除旧兼容包装后真实浏览器策略会退化。
            self.real_browser_information_task_requested = browser_agent_workflow_from_browser.detect_real_browser_information_task(user_input)  # 修改代码+AgentPyCompatWrapperRemovalL7: 主循环直接调用 browser workflow 判断公开信息查询；若没有这行代码，客户模式自动授权会失去触发条件。
            self.visible_browser_information_task_requested = browser_agent_workflow_from_browser.detect_visible_browser_information_task(user_input)  # 修改代码+AgentPyCompatWrapperRemovalL7: 主循环直接调用 browser workflow 判断普通实时查询是否需要可见浏览器；若没有这行代码，精准 prompt 首轮仍看不到 browser_launch_visible。
            browser_agent_workflow_from_browser.load_real_chrome_tools_for_requested_task(self)  # 新增代码+RealChromeToolChain：真实 Chrome 请求首轮预加载 profile status；若没有这行代码，模型第一轮只有孤立提示而没有完整准备工具入口。
            browser_agent_workflow_from_browser.load_visible_browser_tools_for_information_task(self)  # 修改代码+AgentPyCompatWrapperRemovalL7: 主循环直接调用 browser workflow 预加载可见浏览器工具；若没有这行代码，harness 文案存在但模型仍不能调用工具。
            plan_runtime_from_core.maybe_confirm_plan_from_user_input(self, user_input)  # 修改代码+AgentPyCompatWrapperRemovalL5: 主循环直接调用 plan_runtime 处理用户确认计划；若没有这行代码，删除旧薄包装后已确认计划仍可能被副作用闸门阻断。
            debug_event_writer(run_id=run_id, event="user_input", payload={"text": user_input})  # 修改代码+AgentPySplitPhase15B7: 主循环直接用 observability 写入用户输入 debug 日志；若没有这行代码，已有排查方式会丢失。
            messages = self._build_initial_messages(user_input, conversation_history=conversation_history)  # 修改代码+交互上下文: 构造 system + 交互历史 + 当前输入；若没有这行代码，模型仍会忘记同一终端窗口里的上文。
            session_messages = messages  # 新增代码+Stage15G: 让 summary helper 使用同一份运行消息历史；若没有这行代码，summary.json 的 messages 会保持空列表。
            task_state = TaskState.from_user_input(user_input, session_id=session_id, run_id=run_id)  # 新增代码+ContextCompactRepairRuntime: 为本次任务创建可靠任务状态；若没有这行代码，compact 后仍可能忘记用户原始目标。
            task_state.add_pending_item("完成用户本轮原始请求")  # 新增代码+ContextCompactRepairRuntime: 给任务状态放入默认待办；若没有这行代码，压缩摘要的 Pending Tasks 可能为空。
            task_state.set_next_step_hint("围绕原始用户目标继续推进，证据足够时输出最终回答。")  # 新增代码+ContextCompactRepairRuntime: 写入默认下一步提示；若没有这行代码，压缩后模型可能继续读日志恢复任务。
            task_state_path = self.workspace / "memory" / "sessions" / session_id / "task_state.json"  # 新增代码+ContextCompactRepairRuntime: 规划任务状态落盘路径；若没有这行代码，compact boundary 无法指向事实源。
            task_state.save_json(task_state_path)  # 新增代码+ContextCompactRepairRuntime: 立即保存任务状态；若没有这行代码，中断或 compact 后没有可靠恢复文件。
            compact_runtime_state: dict[str, Any] = {"session_id": session_id, "run_id": run_id, "task_state_path": str(task_state_path), "compact_max_messages": 20, "compact_max_chars": max(4000, self.prompt_soft_token_limit * 4)}  # 新增代码+ContextCompactRepairRuntime: 初始化 compact/convergence 共享运行时状态；若没有这行代码，管线无法记录代次、熔断和重复工具计数。
            yield emit("task_state_initialized", {"task_state_path": str(task_state_path), "summary": task_state.to_model_summary()})  # 新增代码+ContextCompactRepairRuntime: 广播任务状态已建立；若没有这行代码，acceptance 无法确认主循环有稳定事实源。
            initial_tools = catalog_runtime_from_tools.available_tool_schemas(self)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 主循环直连 catalog_runtime 读取初始工具池快照；若没有这行代码，主循环仍会通过 agent.py 兼容包装拿工具 schema。
            initial_tool_names = catalog_runtime_from_tools.tool_schema_names(self, initial_tools)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 主循环直连 catalog_runtime 提取初始工具名；若没有这行代码，事件 payload 仍依赖 agent.py 薄包装。
            debug_event_writer(run_id=run_id, event="initial_messages", payload={"messages": messages, "tool_names": initial_tool_names})  # 修改代码+AgentPySplitPhase15B7: 主循环直接用 observability 写入初始上下文 debug 日志；若没有这行代码，select 后工具池排查会变难。
            yield emit("initial_messages_built", {"message_count": len(messages), "tool_names": initial_tool_names})  # 新增代码+Stage15C: 发出初始上下文事件；若没有这行代码，UI 无法解释第一轮上下文准备完成。
            turn = 0  # 新增代码+Stage15C: 初始化轮次；若没有这行代码，无固定上限循环无法推进。
            final_answer_retry_count = 0  # 新增代码+Stage15C: 初始化最终回答重试次数；若没有这行代码，格式重写可能无限循环。
            computer_use_trace_recorder = build_computer_use_runtime_trace_recorder(self, run_helpers_from_core.observation_recorder(self))  # 修改代码+AgentPySplitPhase15B6: 主循环直接拿 runtime_trace.py 的 trace 回调；如果没有这行代码，删除 `_record_computer_use_runtime_trace` 后模型请求、工具调用和工具结果无法写入 trace。
            # 修改代码+AgentPySplitPhase14: 第 6 段是“主工具循环”，每一轮都会建账本、检查取消、准备工具 schema、必要时压缩上下文；若没有这个流程标记，读者容易把 while 误解成普通死循环，而看不出它是 agent 反复“模型思考-工具执行”的核心。
            while max_turns is None or turn < max_turns:  # 新增代码+Stage15C: 保留可配置轮次循环；若没有这行代码，agent 无法继续多轮工具调用。
                current_turn_id = f"turn_{turn}"  # 新增代码+CompactResumeStatus: 更新当前轮次 id；若没有这行代码，异常恢复会写错 turn ledger。
                try:  # 新增代码+CompactResumeStatus: 先确认当前 turn 是否已经存在；若没有这行代码，重复 accept 会覆盖已有 checkpoint。
                    turn_ledger.get_turn(session_id, current_turn_id)  # 新增代码+CompactResumeStatus: 读取已有 turn 记录；若没有这行代码，无法判断是否需要创建新轮次。
                except KeyError:  # 新增代码+CompactResumeStatus: 当前 turn 不存在时进入创建分支；若没有这行代码，新轮次会因为 get_turn 失败而中断。
                    turn_ledger.accept_turn(session_id=session_id, run_id=run_id, turn_id=current_turn_id, user_input=user_input if turn == 0 else "", metadata={"turn_index": turn})  # 新增代码+CompactResumeStatus: 为新轮次建立持久账本；若没有这行代码，中断后无法区分已处理和未处理轮次。
                if self._stop_requested():  # 新增代码+Stage15C: 每轮模型前检查取消；若没有这行代码，已取消任务仍会消耗模型请求。
                    turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="interrupted", checkpoint_uuid=last_transcript_uuid, metadata={"reason": "stop_requested_before_model"})  # 新增代码+CompactResumeStatus: 模型前取消时更新 turn ledger；若没有这行代码，状态页会误判该轮仍在等待模型。
                    yield emit("run_completed", {"text": "任务已停止：收到取消请求。", "reason": "stop_requested"})  # 新增代码+Stage15C: 发出取消完成事件；若没有这行代码，事件消费者拿不到取消提示。
                    return  # 新增代码+Stage15C: 取消后结束循环；若没有这行代码，后续工具可能继续执行。
                computer_use_has_launch_target = lambda: action_gate_has_agent_owned_launch_target(getattr(self, "computer_use_controller", None))  # 修改代码+AgentPySplitPhase15B8: 主循环直接用 action_gates.py 判断是否已有 agent-owned 窗口；如果没有这行代码，删除 `_computer_use_has_agent_owned_launch_target` 后首轮工具收窄会找不到启动状态判断。
                tools = scoped_tool_schemas_for_model_turn(catalog_runtime_from_tools.available_tool_schemas(self), turn, getattr(self, "desktop_task_context", {}), computer_use_has_launch_target)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 主循环直连 catalog_runtime 取得本轮基础工具 schema 后交给 model_loop 收窄；若没有这行代码，本轮工具池仍会通过 agent.py 兼容包装读取。
                tool_names = catalog_runtime_from_tools.tool_schema_names(self, tools)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 主循环直连 catalog_runtime 提取本轮工具名；若没有这行代码，事件 payload 仍依赖 agent.py 薄包装。
                if any(is_computer_use_tool_name(name) for name in tool_names):  # 修改代码+AgentPySplitPhase15B6: 主循环直接用 runtime_trace.py 判断 Computer Use 工具名；如果没有这行代码，删除 `_is_computer_use_tool_name` 后 trace 过滤会断开。
                    computer_use_trace_recorder("model_request", {"turn": turn, "turn_id": current_turn_id, "tool_names": tool_names, "message_count": len(messages), "desktop_task_active": bool(self.desktop_task_context.get("active", False))})  # 修改代码+AgentPySplitPhase15B6: 主循环直接调用 runtime_trace.py 回调记录模型请求；如果没有这行代码，Computer Use schema 可见性不会进入运行证据。
                compact_runtime_state.update({"turn": turn, "turn_id": current_turn_id, "artifact_dir": self.workspace / "memory" / "compact_artifacts" / session_id})  # 新增代码+ContextCompactRepairRuntime: 每轮刷新 compact/convergence 运行状态；若没有这行代码，管线写入的 turn 和 artifact 位置会过期。
                convergence_assessment = assess_before_model(task_state, messages, compact_runtime_state)  # 新增代码+ContextCompactRepairRuntime: 模型请求前检查是否需要收束提醒；若没有这行代码，证据足够或旧摘要跑偏时无法注入提示。
                if convergence_assessment.should_inject_message and convergence_assessment.injected_message is not None:  # 新增代码+ContextCompactRepairRuntime: 只有控制器明确要求时才注入；若没有这行代码，模型会每轮收到噪音提示。
                    messages.append(convergence_assessment.injected_message)  # 新增代码+ContextCompactRepairRuntime: 把收束提醒放进模型上下文；若没有这行代码，评估结果不会影响下一次模型请求。
                    yield emit("convergence_message_injected", {"turn": turn, "turn_id": current_turn_id, **convergence_assessment.to_dict()})  # 新增代码+ContextCompactRepairRuntime: 广播收束注入事件；若没有这行代码，acceptance 看不到增强层动作。
                compact_decision = prepare_messages_before_model(messages, task_state, compact_runtime_state)  # 新增代码+ContextCompactRepairRuntime: 让 compact pipeline 统一决定是否压缩；若没有这行代码，agent.py 仍会散落 compact 判断。
                if compact_decision.compacted and compact_decision.boundary is not None:  # 新增代码+ContextCompactRepairRuntime: 只有真实 compact 后才写边界；若没有这行代码，no-op 也会误写 compact 事件。
                    yield emit("compact_started", {"turn": turn, "turn_id": current_turn_id, "reason": compact_decision.reason})  # 修改代码+ContextCompactRepairRuntime: 从 pipeline 事件中发出 compact 开始；若没有这行代码，UI/SDK 只能看到结束看不到卡在哪一步。
                    messages[:] = compact_decision.messages  # 修改代码+ContextCompactRepairRuntime: 原地替换为 pipeline 输出；若没有这行代码，summary 引用和模型上下文会分裂。
                    task_state.compact_generation = compact_decision.compact_generation  # 新增代码+ContextCompactRepairRuntime: 把 compact 代次回写 TaskState；若没有这行代码，任务状态落盘看不到压缩次数。
                    task_state.save_json(task_state_path)  # 新增代码+ContextCompactRepairRuntime: compact 后保存任务状态；若没有这行代码，中断恢复拿不到最新 compact_generation。
                    compact_entry = transcript_v2_store.append_entry(session_id=session_id, run_id=run_id, turn_id=current_turn_id, event_type="compact_boundary", payload=compact_decision.boundary.to_dict(), parent_uuid=last_transcript_uuid)  # 修改代码+ContextCompactRepairRuntime: 把 pipeline boundary 写入 transcript v2；若没有这行代码，resume loader 无法确认压缩点。
                    last_transcript_uuid = compact_entry.uuid  # 修改代码+ContextCompactRepairRuntime: 把 compact boundary 设为最新 checkpoint；若没有这行代码，中断恢复可能跳过压缩证据。
                    turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="compacted", checkpoint_uuid=compact_entry.uuid, metadata={"compact_boundary": compact_decision.boundary.to_dict(), "compact_decision": compact_decision.to_event_payload()})  # 修改代码+ContextCompactRepairRuntime: 在 turn ledger 记录 compact 决策；若没有这行代码，状态页不知道质量和恢复报告。
                    yield emit("compact_completed", {"turn": turn, "turn_id": current_turn_id, **compact_decision.to_event_payload()})  # 修改代码+ContextCompactRepairRuntime: 广播 pipeline compact 完成；若没有这行代码，终端/SDK/API 无法看到质量字段。
                elif compact_decision.circuit_breaker_open:  # 新增代码+ContextCompactRepairRuntime: compact 熔断打开时也要可见；若没有这行代码，用户只会看到没有压缩但不知道原因。
                    yield emit("compact_circuit_breaker_open", {"turn": turn, "turn_id": current_turn_id, **compact_decision.to_event_payload()})  # 新增代码+ContextCompactRepairRuntime: 广播熔断事件；若没有这行代码，acceptance 无法证明失败后不会每轮重试。
                turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="model_running", checkpoint_uuid=last_transcript_uuid, metadata={"message_count": len(messages), "tool_names": tool_names})  # 新增代码+CompactResumeStatus: 模型请求前更新轮次状态；若没有这行代码，中断恢复不知道是否已经发起模型调用。
                debug_event_writer(run_id=run_id, event="model_request", payload={"messages": messages, "tool_names": tool_names}, turn=turn)  # 修改代码+AgentPySplitPhase15B7: 主循环直接用 observability 写入模型请求 debug 日志；若没有这行代码，debug 回放会断开。
                yield emit("model_request_started", {"turn": turn, "message_count": len(messages), "tool_names": tool_names})  # 新增代码+Stage15C: 发出模型请求事件；若没有这行代码，用户无法看到 agent 正在请求模型。
                model_message: ModelMessage | None = None  # 新增代码+Stage15C: 保存完成的模型消息；若没有这行代码，流式事件结束后无法进入工具循环。
                streamed_text_parts: list[str] = []  # 新增代码+Stage15C: 保存没有 completed 事件时的文本增量兜底；若没有这行代码，只有 delta 的模型会丢失回答。
                # 修改代码+AgentPySplitPhase14: 第 7 段是“请求模型并处理上下文超限恢复”，这里真正把 messages 和工具 schema 发给模型，并在 prompt 太长时只重试一次 reactive compact；若没有这个流程标记，读者很难分清普通模型错误和可恢复的上下文超限。
                try:  # 新增代码+ReactiveCompactRuntime: 单独保护模型请求阶段以便识别上下文超限；若没有这行代码，prompt too long 会直接被外层 run_failed 捕获。
                    for model_event in stream_chat_events(self.model, messages, tools):  # 新增代码+Stage15C: 通过统一流式入口消费模型；若没有这行代码，旧模型和新流式模型会走两套逻辑。
                        if model_event.event_type == "text_delta":  # 新增代码+Stage15C: 处理文本增量事件；若没有这行代码，终端 UI 无法实时显示模型输出。
                            streamed_text_parts.append(model_event.text_delta)  # 新增代码+Stage15C: 保存文本增量用于兜底合成；若没有这行代码，只有 delta 的模型没有最终文本。
                            yield emit("model_message_delta", {"turn": turn, "text_delta": model_event.text_delta})  # 新增代码+Stage15C: 发出模型文本增量事件；若没有这行代码，外部观察不到流式输出。
                        if model_event.event_type == "model_message_completed":  # 新增代码+Stage15C: 处理完整模型消息事件；若没有这行代码，工具循环无法拿到最终 tool_calls。
                            model_message = model_event.model_message  # 新增代码+Stage15C: 保存完整模型消息；若没有这行代码，后续无法追加 assistant 消息。
                except Exception as model_error:  # 新增代码+ReactiveCompactRuntime: 捕获模型请求异常并判断是否可恢复；若没有这行代码，超限错误无法自动 compact。
                    compact_runtime_state["reactive_compact_attempted"] = turn in reactive_compact_attempted_turns  # 新增代码+ContextCompactRepairRuntime: 告诉 pipeline 本 turn 是否已 reactive 过；若没有这行代码，同一轮超限可能重复重试。
                    reactive_decision = recover_from_context_overflow(messages, task_state, model_error, compact_runtime_state)  # 修改代码+ContextCompactRepairRuntime: 通过 pipeline 恢复上下文超限；若没有这行代码，reactive compact 会绕开 TaskState 质量门禁。
                    if reactive_decision.compacted and reactive_decision.boundary is not None:  # 修改代码+ContextCompactRepairRuntime: 只有 pipeline 确认可重试才继续；若没有这行代码，普通错误可能被误吞。
                        reactive_compact_attempted_turns.add(turn)  # 新增代码+ReactiveCompactRuntime: 标记本 turn 已经重试过；若没有这行代码，持续超限会无限循环。
                        messages[:] = reactive_decision.messages  # 修改代码+ContextCompactRepairRuntime: 用 pipeline 输出替换模型上下文；若没有这行代码，下一次请求仍会超限。
                        task_state.compact_generation = reactive_decision.compact_generation  # 新增代码+ContextCompactRepairRuntime: 回写 reactive compact 代次；若没有这行代码，TaskState 不知道异常恢复发生过。
                        task_state.save_json(task_state_path)  # 新增代码+ContextCompactRepairRuntime: 保存 reactive 后状态；若没有这行代码，中断恢复会丢 compact_generation。
                        compact_entry = transcript_v2_store.append_entry(session_id=session_id, run_id=run_id, turn_id=current_turn_id, event_type="compact_boundary", payload=reactive_decision.boundary.to_dict(), parent_uuid=last_transcript_uuid)  # 修改代码+ContextCompactRepairRuntime: 把 pipeline reactive boundary 写入 transcript v2；若没有这行代码，异常恢复不可审计。
                        last_transcript_uuid = compact_entry.uuid  # 修改代码+ContextCompactRepairRuntime: 把 reactive compact 作为最新 checkpoint；若没有这行代码，中断恢复会漏掉修复点。
                        turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="compacted", checkpoint_uuid=compact_entry.uuid, metadata={"compact_boundary": reactive_decision.boundary.to_dict(), "compact_decision": reactive_decision.to_event_payload()})  # 修改代码+ContextCompactRepairRuntime: 在账本记录 reactive compact 决策；若没有这行代码，状态页不知道质量和熔断字段。
                        yield emit("reactive_compact_retry", {"turn": turn, "turn_id": current_turn_id, **reactive_decision.to_event_payload()})  # 修改代码+ContextCompactRepairRuntime: 广播即将重试模型请求；若没有这行代码，UI/SDK 看不到自动恢复动作。
                        continue  # 新增代码+ReactiveCompactRuntime: 回到同一 turn 重新请求模型；若没有这行代码，压缩后不会真正重试。
                    raise  # 新增代码+ReactiveCompactRuntime: 非可恢复错误或第二次超限交给外层失败事件；若没有这行代码，真实错误会被吞掉。
                if model_message is None:  # 新增代码+Stage15C: 处理模型只给 delta 没给 completed 的兜底情况；若没有这行代码，后续会访问 None 崩溃。
                    model_message = ModelMessage(text="".join(streamed_text_parts))  # 新增代码+Stage15C: 用文本增量合成最终消息；若没有这行代码，流式文本会丢失。
                model_payload = debug_formatting_from_observability.model_message_to_debug_dict(model_message)  # 修改代码+AgentPySplitPhase15B7: 主循环直接用 observability 转换模型消息调试字典；若没有这行代码，删除旧转换薄包装后事件和日志会缺模型结果。
                debug_event_writer(run_id=run_id, event="model_response", payload=model_payload, turn=turn)  # 修改代码+AgentPySplitPhase15B7: 主循环直接用 observability 写入模型响应 debug 日志；若没有这行代码，debug 回放会缺模型结果。
                model_completed_event = emit("model_message_completed", {"turn": turn, "message": model_payload})  # 修改代码+CompactResumeStatus: 先创建模型完成事件以便 ledger 引用 checkpoint；若没有这行代码，模型结果无法和 turn ledger 对齐。
                yield model_completed_event  # 修改代码+CompactResumeStatus: 发出模型完成事件；若没有这行代码，transcript 无法记录模型结果。
                yield emit("model_response_completed", {"turn": turn, "turn_id": current_turn_id, "message": model_payload})  # 新增代码+StatusSchemaV2: 额外发出 v2 命名的模型完成事件；若没有这行代码，UI/SDK 需要兼容旧 model_message_completed 名称。
                turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="model_completed", checkpoint_uuid=last_transcript_uuid, metadata={"tool_call_count": len(model_message.tool_calls)})  # 新增代码+CompactResumeStatus: 模型完成后更新轮次账本；若没有这行代码，恢复器不知道模型响应已经拿到。
                messages.append(message_builders_from_core.assistant_message_to_dict(model_message))  # 修改代码+AgentPySplitPhase15B4: 主循环直接调用 core/message_builders.py，不再绕 agent.py 旧消息薄包装；如果没有这一行，删除 `_assistant_message_to_dict` 后下一轮模型看不到上轮 assistant/tool_calls。
                continuation_decision = decide_after_model_response(model_message, task_state, compact_runtime_state)  # 新增代码+ContextCompactRepairRuntime: 让 continuation 控制器判断是否继续；若没有这行代码，主循环仍靠裸 tool_calls 分支收束。
                yield emit("continuation_decision", {"turn": turn, "turn_id": current_turn_id, **continuation_decision.to_dict()})  # 新增代码+ContextCompactRepairRuntime: 广播继续/结束判断；若没有这行代码，acceptance 无法区分自然停止和 hook 阻塞。
                if self._stop_requested():  # 新增代码+Stage15C: 模型后工具前检查取消；若没有这行代码，取消后仍可能执行写文件或命令。
                    turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="interrupted", checkpoint_uuid=last_transcript_uuid, metadata={"reason": "stop_requested_after_model"})  # 新增代码+CompactResumeStatus: 模型后取消时更新 ledger；若没有这行代码，恢复器会误以为还要等模型响应。
                    yield emit("run_completed", {"text": "任务已停止：收到取消请求。", "reason": "stop_requested"})  # 新增代码+Stage15C: 发出取消完成事件；若没有这行代码，事件消费者拿不到取消提示。
                    return  # 新增代码+Stage15C: 停止事件流；若没有这行代码，工具调用会继续发生。
                # 修改代码+AgentPySplitPhase14: 第 8 段是“最终回答出口”，模型没有再请求工具时就在这里重试必要格式、保存 summary、发出 run_completed；若没有这个流程标记，读者会难以看出 agent 什么时候算任务结束。
                if continuation_decision.continue_loop and not model_message.tool_calls and continuation_decision.injected_message is not None:  # 新增代码+ContextCompactRepairRuntime: hook/预算要求继续时只注入提示；若没有这行代码，stop hook 无法阻止过早最终回答。
                    messages.append(continuation_decision.injected_message)  # 新增代码+ContextCompactRepairRuntime: 把继续提示写回上下文；若没有这行代码，下一轮模型不知道要补什么。
                    turn += 1  # 新增代码+ContextCompactRepairRuntime: 注入继续也计入一次模型轮次；若没有这行代码，循环状态和账本会错位。
                    continue  # 新增代码+ContextCompactRepairRuntime: 进入下一轮模型请求；若没有这行代码，仍会落入最终回答出口。
                if not model_message.tool_calls:  # 新增代码+Stage15C: 无工具调用时进入最终回答路径；若没有这行代码，直接回答会被误当成工具循环。
                    retry_message = self._final_answer_retry_message(user_input, model_message.text)  # 新增代码+Stage15C: 保留最终回答格式补救；若没有这行代码，复合任务可能漏掉用户要求标题。
                    can_retry_final_answer = retry_message and final_answer_retry_count < 1 and (max_turns is None or turn + 1 < max_turns)  # 新增代码+Stage15C: 保留单次重试和轮次预算限制；若没有这行代码，可能无限重写。
                    if can_retry_final_answer:  # 新增代码+Stage15C: 如果可以重写最终回答；若没有这行代码，缺标题答案会提前返回。
                        final_answer_retry_count += 1  # 新增代码+Stage15C: 消耗一次重试机会；若没有这行代码，重试次数无法限制。
                        debug_event_writer(run_id=run_id, event="final_answer_retry", payload={"message": retry_message}, turn=turn)  # 修改代码+AgentPySplitPhase15B7: 主循环直接用 observability 写入最终回答重试 debug 日志；若没有这行代码，排查多一次模型调用会困难。
                        yield emit("final_answer_retry", {"turn": turn, "message": retry_message})  # 新增代码+Stage15C: 发出重试事件；若没有这行代码，transcript 无法解释为什么继续下一轮。
                        messages.append({"role": "user", "content": retry_message})  # 新增代码+Stage15C: 把修正请求放回历史；若没有这行代码，模型没有机会补全格式。
                        turn += 1  # 新增代码+Stage15C: 重试计入轮次；若没有这行代码，max_turns 不会生效。
                        continue  # 新增代码+Stage15C: 进入下一轮模型请求；若没有这行代码，会继续提前完成。
                    final_answer_text = evidence_summary_final_answer_with_evidence_summary(model_message.text, getattr(self, "desktop_task_context", {}), getattr(self, "observation_events", []))  # 修改代码+AgentPySplitPhase15B8：最终出口直接调用 evidence_summary.py 补齐真实桌面证据摘要；如果没有这一行，删除 `_computer_use_full_final_answer_with_evidence_summary` 后模型短答会丢掉 screenshot、real_desktop_touched 和 low_level_event_count。
                    debug_event_writer(run_id=run_id, event="final_answer", payload={"text": final_answer_text}, turn=turn)  # 修改代码+AgentPySplitPhase15B7：主循环直接用 observability 写入补强后的最终回答 debug 日志；如果没有这一行，真实验收失败时日志仍看不到用户实际收到的摘要。
                    turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="completed", checkpoint_uuid=last_transcript_uuid, metadata={"final_answer_chars": len(final_answer_text)})  # 修改代码+ComputerUseFinalEvidenceSummary：最终回答长度按补强文本计算；如果没有这一行，恢复账本会低估真实输出内容。
                    summary_path = save_session_summary(final_answer_text)  # 修改代码+ComputerUseFinalEvidenceSummary：保存补强后的会话摘要；如果没有这一行，resume 后仍只看到短答而缺少桌面证据。
                    yield emit("session_saved", {"summary_path": str(summary_path), "session_id": session_id})  # 新增代码+Stage15G: 发出 session_saved 事件；若没有这行代码，事件流消费者不知道 summary 已落盘。
                    yield emit("run_completed", {"text": final_answer_text, "turn": turn})  # 修改代码+ComputerUseFinalEvidenceSummary：把补强后的文本交给 run()/终端/controller；如果没有这一行，真实终端仍会打印短答并误判失败。
                    return  # 新增代码+Stage15C: 最终回答后结束事件流；若没有这行代码，循环会继续请求模型。
                # 修改代码+AgentPySplitPhase14: 第 9 段是“工具调用执行和结果回填”，模型要求调用工具时先记录开始事件，再执行工具，最后把结果塞回 messages 等下一轮模型继续判断；若没有这个流程标记，读者容易看不懂 agent 为什么会循环多轮。
                self.defer_tool_select_until_next_turn = True  # 新增代码+Stage15C: 保留同批 tool_search 延迟生效语义；若没有这行代码，deferred 工具会在同批中错误可见。
                real_tool_calls: list[ToolCall] = []  # 新增代码+ContextCompactRepairRuntime: 保存收束控制器放行的真实工具；若没有这行代码，无法把真实执行和合成结果分开。
                synthetic_tool_outputs: dict[str, str] = {}  # 新增代码+ContextCompactRepairRuntime: 保存被收束器阻断的合成工具结果；若没有这行代码，被阻断 tool_call 无法闭合协议。
                for tool_call in model_message.tool_calls:  # 修改代码+Stage15F: 先按原顺序发出本批工具开始事件；若没有这行代码，并发执行时 UI 无法看到稳定开始序列。
                    tool_decision = decide_tool_call(tool_call, task_state, compact_runtime_state)  # 新增代码+ContextCompactRepairRuntime: 让 convergence 控制器判断工具是否值得真实执行；若没有这行代码，重复工具会继续无限跑。
                    tool_payload = debug_formatting_from_observability.tool_call_to_debug_dict(tool_call)  # 修改代码+AgentPySplitPhase15B7: 主循环直接用 observability 转换工具调用载荷；若没有这行代码，删除旧转换薄包装后事件和日志会缺工具调用字段。
                    session_tool_calls.append(copy.deepcopy(tool_payload))  # 新增代码+Stage15G: 记录工具调用到 session summary；若没有这行代码，resume 摘要看不到工具调用历史。
                    yield emit("tool_convergence_decision", {"turn": turn, "turn_id": current_turn_id, "tool_call": tool_payload, "decision": tool_decision.to_dict()})  # 新增代码+ContextCompactRepairRuntime: 广播工具收束决策；若没有这行代码，acceptance 无法证明重复工具被真实控制。
                    if not tool_decision.execute_real_tool:  # 新增代码+ContextCompactRepairRuntime: 收束控制器要求阻断时不执行真实工具；若没有这行代码，重复工具仍会消耗时间和上下文。
                        synthetic_tool_outputs[tool_call.call_id] = tool_decision.synthetic_output or "convergence_controller: 工具调用已被收束控制器阻断。"  # 新增代码+ContextCompactRepairRuntime: 保存合成工具结果；若没有这行代码，模型工具协议会缺少对应 tool result。
                        if tool_decision.injected_message is not None:  # 新增代码+ContextCompactRepairRuntime: 有额外收束提示时写入上下文；若没有这行代码，模型可能不知道为什么工具没执行。
                            messages.append(tool_decision.injected_message)  # 新增代码+ContextCompactRepairRuntime: 注入收束提醒；若没有这行代码，下一轮模型仍可能重复请求。
                        debug_event_writer(run_id=run_id, event="tool_call_blocked_by_convergence", payload={"tool_call": tool_payload, "decision": tool_decision.to_dict()}, turn=turn)  # 新增代码+ContextCompactRepairRuntime: 写入 debug 日志；若没有这行代码，重复工具阻断不可排查。
                        yield emit("tool_call_blocked_by_convergence", {"turn": turn, "turn_id": current_turn_id, "tool_call": tool_payload, "decision": tool_decision.to_dict()})  # 新增代码+ContextCompactRepairRuntime: 广播阻断事件；若没有这行代码，终端/SDK 看不到真实控制动作。
                        continue  # 新增代码+ContextCompactRepairRuntime: 被阻断工具不进入真实执行列表；若没有这行代码，阻断后仍会执行工具。
                    real_tool_calls.append(tool_call)  # 新增代码+ContextCompactRepairRuntime: 记录放行的真实工具；若没有这行代码，后续 orchestrator 没有执行对象。
                    if is_computer_use_tool_name(tool_call.name):  # 修改代码+AgentPySplitPhase15B6: 主循环直接用 runtime_trace.py 识别 Computer Use 工具调用；如果没有这行代码，删除旧工具名薄包装后工具调用 trace 会断开。
                        computer_use_used_this_run = True  # 新增代码+TurnCleanupLifecycleRootRemediation：标记本轮已经进入 Computer Use 工具路径；如果没有这一行，异常或 final 后不会自动 cleanup。
                        trace_arguments = tool_payload.get("arguments", {}) if isinstance(tool_payload.get("arguments", {}), dict) else {}  # 新增代码+RuntimeTrace：读取已脱敏/可调试参数摘要；如果没有这行代码，trace 无法记录 action、operation 或 query。
                        computer_use_trace_recorder("tool_call", {"turn": turn, "turn_id": current_turn_id, "tool_name": tool_call.name, "call_id": tool_call.call_id, "action": trace_arguments.get("action", ""), "operation": trace_arguments.get("operation", ""), "query": trace_arguments.get("query", "")})  # 修改代码+AgentPySplitPhase15B6: 主循环直接调用 runtime_trace.py 回调记录工具调用；如果没有这行代码，模型实际选择的 Computer Use 工具不会进入证据链。
                    debug_event_writer(run_id=run_id, event="tool_call", payload=tool_payload, turn=turn)  # 修改代码+AgentPySplitPhase15B7: 主循环直接用 observability 写入工具调用 debug 日志；若没有这行代码，排查模型选了什么工具会困难。
                    yield emit("tool_use_seen", {"turn": turn, "turn_id": current_turn_id, "tool_call": tool_payload})  # 新增代码+StatusSchemaV2: 把工具调用以 v2 事件名暴露给状态生态；若没有这行代码，外部 agent 很难按标准事件过滤工具使用。
                    yield emit("tool_call_started", {"turn": turn, "tool_call": tool_payload})  # 新增代码+Stage15C: 发出工具开始事件；若没有这行代码，UI 无法显示工具执行进度。
                turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="tools_running", checkpoint_uuid=last_transcript_uuid, metadata={"tool_count": len(model_message.tool_calls), "real_tool_count": len(real_tool_calls), "synthetic_tool_count": len(synthetic_tool_outputs)})  # 修改代码+ContextCompactRepairRuntime: 批量工具执行前记录真实/合成数量；若没有这行代码，验收无法区分阻断和真实执行。
                tool_outputs_by_call_id: dict[str, str] = dict(synthetic_tool_outputs)  # 新增代码+ContextCompactRepairRuntime: 先放入合成工具结果；若没有这行代码，后续按原顺序回填会找不到阻断结果。
                real_tool_outputs = execute_tool_calls_from_orchestrator(self, real_tool_calls) if real_tool_calls else []  # 修改代码+ContextCompactRepairRuntime: 只执行放行的真实工具；若没有这行代码，被阻断工具仍会被 orchestrator 调用。
                for real_tool_call, real_tool_output in zip(real_tool_calls, real_tool_outputs):  # 新增代码+ContextCompactRepairRuntime: 把真实工具结果按 call_id 放入映射；若没有这行代码，原顺序回填会丢真实结果。
                    tool_outputs_by_call_id[real_tool_call.call_id] = real_tool_output  # 新增代码+ContextCompactRepairRuntime: 保存真实工具输出；若没有这行代码，后面无法统一处理真实/合成结果。
                for tool_call in model_message.tool_calls:  # 修改代码+ContextCompactRepairRuntime: 按原 tool_call 顺序发出完成事件和回填消息；若没有这行代码，并发和合成结果可能乱序。
                    tool_output = tool_outputs_by_call_id.get(tool_call.call_id, "")  # 新增代码+ContextCompactRepairRuntime: 读取真实或合成输出；若没有这行代码，阻断工具没有回填内容。
                    context_tool_output = self._offload_tool_output_if_needed(tool_call, tool_output)  # 新增代码+Stage15C: 长结果落盘并回填摘要；若没有这行代码，大输出会撑爆上下文。
                    record_tool_result(tool_call, context_tool_output, task_state, compact_runtime_state)  # 新增代码+ContextCompactRepairRuntime: 把工具结果摘要沉淀进 TaskState；若没有这行代码，compact 后模型可能反复读取同一证据。
                    task_state.save_json(task_state_path)  # 新增代码+ContextCompactRepairRuntime: 每个工具结果后保存任务状态；若没有这行代码，中断恢复会丢刚获得的证据。
                    result_payload = {"tool_name": tool_call.name, "call_id": tool_call.call_id, "output": context_tool_output, "raw_output_chars": len(tool_output)}  # 新增代码+Stage15C: 构造工具结果载荷；若没有这行代码，事件和 debug 日志字段会不一致。
                    if is_computer_use_tool_name(tool_call.name):  # 修改代码+AgentPySplitPhase15B6: 主循环直接用 runtime_trace.py 识别 Computer Use 工具结果；如果没有这行代码，删除旧工具名薄包装后工具结果 trace 会断开。
                        tool_output_lower = tool_output.lower()  # 新增代码+RuntimeTrace：生成小写文本用于低成本识别截图证据关键词；如果没有这行代码，截图标记匹配会受大小写影响。
                        computer_use_trace_recorder("tool_result", {"turn": turn, "turn_id": current_turn_id, "tool_name": tool_call.name, "call_id": tool_call.call_id, "raw_output_chars": len(tool_output), "context_output_chars": len(context_tool_output), "screenshot_returned_to_model": "image_result_count" in tool_output_lower or "screenshot" in tool_output_lower or "artifact_path" in tool_output_lower})  # 修改代码+AgentPySplitPhase15B6: 主循环直接调用 runtime_trace.py 回调记录工具结果；如果没有这行代码，截图是否回到模型不会进入 trace report。
                    session_tool_results.append(copy.deepcopy(result_payload))  # 新增代码+Stage15G: 记录工具结果到 session summary；若没有这行代码，resume 摘要缺少外部观察结果。
                    debug_event_writer(run_id=run_id, event="tool_result", payload=result_payload, turn=turn)  # 修改代码+AgentPySplitPhase15B7: 主循环直接用 observability 写入工具结果 debug 日志；若没有这行代码，旧排查方式无法看到工具输出。
                    tool_completed_event = emit("tool_call_completed", {"turn": turn, **result_payload})  # 修改代码+CompactResumeStatus: 先创建工具完成事件以便 ledger 引用 checkpoint；若没有这行代码，工具结果无法和 turn ledger 对齐。
                    yield tool_completed_event  # 修改代码+CompactResumeStatus: 发出工具完成事件；若没有这行代码，transcript 无法恢复工具结果。
                    yield emit("tool_result_seen", {"turn": turn, "turn_id": current_turn_id, **result_payload})  # 新增代码+StatusSchemaV2: 把工具结果以 v2 事件名暴露给状态生态；若没有这行代码，SDK/API 无法稳定观察工具回灌。
                    turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="tool_result_recorded", checkpoint_uuid=last_transcript_uuid, metadata={"last_tool_name": tool_call.name, "last_tool_call_id": tool_call.call_id})  # 新增代码+CompactResumeStatus: 每个工具完成后更新 checkpoint；若没有这行代码，中断后可能重复执行已完成工具。
                    messages.extend(message_builders_from_core.tool_result_messages_to_dicts(tool_call, context_tool_output, lambda image_tool_call, image_output: build_computer_use_image_message_from_tool_output(tool_name=image_tool_call.name, output=image_output, record_observation=run_helpers_from_core.observation_recorder(self)), image_source_output=tool_output))  # 修改代码+ComputerUseRawImageReinjection：文本回填使用压缩摘要但图片提取使用原始工具输出；如果没有这一行，长 observe 结果落盘后 Computer Use 截图像素不会进入下一轮模型输入。
                    if self._stop_requested():  # 新增代码+Stage15C: 每个工具后检查取消；若没有这行代码，一批工具会在取消后继续执行。
                        self.defer_tool_select_until_next_turn = False  # 新增代码+Stage15C: 停止前关闭延迟 select 标记；若没有这行代码，复用同一 agent 会污染状态。
                        turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="interrupted", checkpoint_uuid=last_transcript_uuid, metadata={"reason": "stop_requested_after_tool"})  # 新增代码+CompactResumeStatus: 工具后取消时更新 ledger；若没有这行代码，恢复器可能重复刚完成的工具。
                        yield emit("run_completed", {"text": "任务已停止：收到取消请求。", "reason": "stop_requested"})  # 新增代码+Stage15C: 发出取消完成事件；若没有这行代码，事件消费者拿不到取消提示。
                        return  # 新增代码+Stage15C: 停止事件流；若没有这行代码，后续工具可能继续执行。
                self.defer_tool_select_until_next_turn = False  # 新增代码+Stage15C: 当前批次工具处理完成后关闭延迟标记；若没有这行代码，后续 select 会被错误延迟。
                catalog_runtime_from_tools.commit_pending_loaded_tool_names(self)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 主循环直连 catalog_runtime 提交 pending select；若没有这行代码，下一轮工具池仍通过 agent.py 兼容包装合并状态。
                turn += 1  # 新增代码+Stage15C: 推进轮次；若没有这行代码，循环可能卡在同一轮。
            # 修改代码+AgentPySplitPhase14: 第 10 段是“最大轮次安全停止”，只有设置了 max_turns 且循环耗尽才会走到这里；若没有这个流程标记，读者可能误以为无限任务会自然跑到这段。
            safety_message = "已经达到最大工具循环次数，为了安全我先停止。请把任务拆小一点再试。"  # 新增代码+Stage15C: 保留安全停止提示；若没有这行代码，超轮次时用户看不到原因。
            debug_event_writer(run_id=run_id, event="safety_stop", payload={"text": safety_message, "max_turns": max_turns})  # 修改代码+AgentPySplitPhase15B7: 主循环直接用 observability 写入安全停止 debug 日志；若没有这行代码，排查长任务停止原因会困难。
            turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="interrupted", checkpoint_uuid=last_transcript_uuid, metadata={"reason": "max_turns", "max_turns": max_turns})  # 新增代码+CompactResumeStatus: 达到轮次上限时把 turn 标记为可恢复中断；若没有这行代码，恢复器可能误判任务自然完成。
            yield emit("run_completed", {"text": safety_message, "reason": "max_turns", "max_turns": max_turns})  # 新增代码+Stage15C: 把安全停止也作为完成事件返回；若没有这行代码，事件消费者会拿不到停止文本。
        # 修改代码+AgentPySplitPhase14: 第 11 段是“异常转事件”，主流程出错时不让生成器静默崩掉，而是写 turn ledger 并发出 run_failed；若没有这个流程标记，读者不容易看出错误也会被记录成可恢复证据。
        except Exception as error:  # 新增代码+Stage15C: 捕获主循环异常；若没有这行代码，事件流消费者无法收到结构化失败事件。
            failure_text = f"任务失败：{error}"  # 新增代码+Stage15C: 构造可读失败文本；若没有这行代码，事件消费者无法显示异常原因。
            try:  # 新增代码+CompactResumeStatus: 尝试把异常写入 turn ledger；若没有这行代码，失败后恢复器看不到失败 checkpoint。
                turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="failed", checkpoint_uuid=last_transcript_uuid, metadata={"error": str(error), "error_type": type(error).__name__})  # 新增代码+CompactResumeStatus: 保存失败状态和错误类型；若没有这行代码，审计只能靠终端文本猜失败原因。
            except Exception:  # 新增代码+CompactResumeStatus: ledger 写入失败时不覆盖原始异常事件；若没有这行代码，二次失败会遮住真正错误。
                pass  # 新增代码+CompactResumeStatus: 保留原始 run_failed 事件继续输出；若没有这行代码，except 块语法不完整。
            yield emit("run_failed", {"text": failure_text, "error": str(error), "error_type": type(error).__name__})  # 新增代码+Stage15C: 发出失败事件并写 transcript；若没有这行代码，失败无法恢复和审计。
        # 修改代码+AgentPySplitPhase14: 第 12 段是“运行后收尾”，无论成功、取消、失败都会恢复进入 run_events 前的桌面任务上下文；若没有这个流程标记，读者容易漏掉 finally 是保护下一次运行不被本次状态污染。
        finally:  # 修改代码+TurnCleanupLifecycleRootRemediation：无论正常完成、提前 return、异常失败都执行 Computer Use cleanup 和上下文恢复；如果没有这一行，active 或桌面控制状态可能泄漏到下一轮任务。
            self._run_computer_use_turn_cleanup_if_needed(computer_use_used_this_run, reason=f"agent run turn cleanup:{run_id}")  # 新增代码+TurnCleanupLifecycleRootRemediation：本轮用过 Computer Use 时执行 turn cleanup；如果没有这一行，S4 异常恢复后可能残留锁、abort 或目标状态。
            self._restore_desktop_task_policy_context(previous_desktop_task_context)  # 新增代码+DesktopTaskPolicy：把进入 run_events 前的上下文还原；如果没有这一行，单次桌面任务结束后 bash 策略会持续误认为 active。

    def _final_answer_retry_message(self, user_input: str, answer_text: str) -> str | None:  # 新增代码+最终答案完整性: 生成“最终回答缺少用户指定 Markdown 标题”时的单次重写提示；若没有这行代码，run() 会调用不存在的方法并导致 HTTP bridge 真实测试 500
        required_headings: list[str] = []  # 新增代码+最终答案完整性: 保存用户原话里明确写出的 Markdown 标题；若没有这行代码，后续无法知道要检查哪些标题
        for raw_line in user_input.splitlines():  # 新增代码+最终答案完整性: 逐行扫描用户输入；若没有这行代码，无法从多行需求里提取“## 天气来源”这类标题
            heading = raw_line.strip()  # 新增代码+最终答案完整性: 去掉标题前后的空白；若没有这行代码，缩进或尾随空格会导致标题匹配不稳定
            if not heading.startswith("#"):  # 新增代码+最终答案完整性: 跳过非 Markdown 标题行；若没有这行代码，普通需求文本可能被误当成必需标题
                continue  # 新增代码+最终答案完整性: 非标题行不参与完整性检查；若没有这行代码，后续会错误解析普通句子
            marker_length = len(heading) - len(heading.lstrip("#"))  # 新增代码+最终答案完整性: 计算标题前缀里有几个 #；若没有这行代码，无法区分 Markdown 标题和普通 # 符号
            if marker_length < 1 or marker_length > 6:  # 新增代码+最终答案完整性: 只接受 Markdown 支持的 1 到 6 级标题；若没有这行代码，异常数量的 # 也会触发重试
                continue  # 新增代码+最终答案完整性: 非标准标题不作为硬性要求；若没有这行代码，模型可能被无关文本反复重写
            if len(heading) <= marker_length or heading[marker_length] != " ":  # 新增代码+最终答案完整性: 要求 # 后面有空格才算规范标题；若没有这行代码，#标签 之类文本会被误判成标题
                continue  # 新增代码+最终答案完整性: 跳过不规范标题形态；若没有这行代码，普通 hashtag 可能制造误重试
            if not heading[marker_length:].strip():  # 新增代码+最终答案完整性: 确认标题正文不是空白；若没有这行代码，只有 ## 的行会被当成必须输出的标题
                continue  # 新增代码+最终答案完整性: 空标题没有可验证意义所以跳过；若没有这行代码，模型会收到无法满足的要求
            required_headings.append(heading)  # 新增代码+最终答案完整性: 记录一个必须出现在最终回答里的标题；若没有这行代码，检查阶段没有目标列表
        if not required_headings:  # 新增代码+最终答案完整性: 如果用户没有写出 Markdown 标题要求；若没有这行代码，普通问题也可能被格式检查干扰
            return None  # 新增代码+最终答案完整性: 不需要重写最终答案；若没有这行代码，run() 无法区分“无需重试”和“需要重试”
        missing_headings = [heading for heading in required_headings if heading not in answer_text]  # 新增代码+最终答案完整性: 找出最终回答里缺失的标题；若没有这行代码，无法判断第一版回答是否完整满足格式要求
        if not missing_headings:  # 新增代码+最终答案完整性: 如果所有必需标题都已经出现；若没有这行代码，完整答案也会被无意义重写
            return None  # 新增代码+最终答案完整性: 返回 None 表示接受当前最终答案；若没有这行代码，run() 会继续追加重试消息
        missing_block = "\n".join(missing_headings)  # 新增代码+最终答案完整性: 把缺失标题整理成多行文本；若没有这行代码，模型难以清楚知道漏了哪些标题
        return "你的最终回答漏掉了用户明确要求的 Markdown 小标题。请基于上文已有工具结果重写最终回答，不要重新调用工具，必须包含下面这些小标题：\n" + missing_block  # 新增代码+最终答案完整性: 返回可恢复的重写指令；若没有这行代码，模型没有机会补全旅游攻略等复合输出

    def _stop_requested(self) -> bool:  # 新增代码+AsyncTask: 统一判断当前 agent 是否收到取消信号；若省略: run 和子任务辅助函数会重复判断逻辑
        return self.stop_event is not None and self.stop_event.is_set()  # 新增代码+AsyncTask: 只有存在 stop_event 且已置位才算取消；若省略: 普通 agent 可能被误判为已取消

    def _safe_tool_artifact_name(self, tool_name: str) -> str:  # 新增代码+ResultPersistence: 把工具名转换成安全文件名片段；若没有这行代码，带斜杠或冒号的工具名可能生成非法路径
        return safe_tool_artifact_name(tool_name)  # 修改代码+ResultStorageSplit: 委托 tools.result_storage 生成安全结果文件名；若没有这行代码，文件名清洗逻辑仍留在主入口

    def _tool_result_inline_limit(self, tool_name: str) -> int:  # 新增代码+ResultPersistence: 计算工具结果可回填模型上下文的最大字符数；若没有这行代码，长输出裁剪策略会散落到 run 循环里
        catalog_tool = catalog_runtime_from_tools.find_catalog_tool(self, tool_name)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 长输出策略直连 catalog_runtime 读取工具 max_result_size_chars 元数据；若没有这行代码，结果落盘仍依赖 agent.py 兼容包装。
        configured_limit = getattr(catalog_tool, "max_result_size_chars", 8000) if catalog_tool is not None else 8000  # 新增代码+ResultPersistence: 缺少目录工具时使用 8000 字符保守默认；若没有这行代码，未知工具会触发属性访问异常
        return clamp_tool_result_inline_limit(configured_limit)  # 修改代码+ResultStorageSplit: 委托 tools.result_storage 夹紧 inline 上限；若没有这行代码，长结果大小策略仍留在主入口

    def _offload_tool_output_if_needed(self, tool_call: ToolCall, output: str) -> str:  # 新增代码+ResultPersistence: 长工具结果落盘并只把摘要回填上下文；若没有这行代码，大文件、日志或网页结果会继续撑爆模型上下文
        inline_limit = self._tool_result_inline_limit(tool_call.name)  # 新增代码+ResultPersistence: 读取当前工具的回填字符上限；若没有这行代码，后续无法判断是否需要落盘
        if len(output) <= inline_limit:  # 新增代码+ResultPersistence: 短结果无需落盘；若没有这行代码，所有工具结果都会写文件造成噪音
            return output  # 新增代码+ResultPersistence: 直接返回原始输出给模型；若没有这行代码，短结果会被无意义压缩
        try:  # 新增代码+ResultPersistence: 捕获目录创建或写文件异常；若没有这行代码，落盘失败会中断整个 tool loop
            self.tool_result_artifact_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+ResultPersistence: 确保工具结果目录存在；若没有这行代码，首次长输出保存会因目录缺失失败
            timestamp = time.strftime("%Y%m%d_%H%M%S")  # 新增代码+ResultPersistence: 用时间戳作为文件名前缀；若没有这行代码，多次保存的文件不容易按时间排序
            safe_tool_name = self._safe_tool_artifact_name(tool_call.name)  # 新增代码+ResultPersistence: 生成安全工具名文件片段；若没有这行代码，原始工具名可能包含路径非法字符
            artifact_path = self.tool_result_artifact_dir / f"{timestamp}_{safe_tool_name}_{secrets.token_hex(6)}.txt"  # 新增代码+ResultPersistence: 生成唯一完整结果文件路径；若没有这行代码，多次长输出可能互相覆盖
            artifact_path.write_text(output, encoding="utf-8")  # 新增代码+ResultPersistence: 把完整工具结果写入 UTF-8 文本文件；若没有这行代码，后续审计拿不到完整输出
            artifact_text = str(artifact_path)  # 新增代码+ResultPersistence: 把路径转成文本用于返回和观察事件；若没有这行代码，JSON/debug 输出无法直接显示 Path
            self.active_artifacts.append(artifact_text)  # 新增代码+ResultPersistence: 记录本 agent 当前关联的结果文件；若没有这行代码，后续上下文控制无法知道哪些产物属于本轮
            self.active_artifacts = self.active_artifacts[-50:]  # 新增代码+ResultPersistence: 只保留最近 50 个产物引用；若没有这行代码，长会话会无限增长文件引用列表
            run_helpers_from_core.record_observation(self, "tool_result_offloaded", {"tool_name": tool_call.name, "call_id": tool_call.call_id, "artifact_path": artifact_text, "raw_output_chars": len(output), "inline_limit": inline_limit})  # 新增代码+ResultPersistence: 记录完整输出已落盘的审计事件；若没有这行代码，模型上下文只看到摘要时无法追踪完整内容在哪里
        except OSError as error:  # 新增代码+ResultPersistence: 处理文件系统写入失败；若没有这行代码，磁盘权限或路径问题会让 agent 崩溃
            run_helpers_from_core.record_observation(self, "tool_result_offload_failed", {"tool_name": tool_call.name, "call_id": tool_call.call_id, "error": str(error), "raw_output_chars": len(output)})  # 新增代码+ResultPersistence: 记录落盘失败原因；若没有这行代码，排查只能看到被截断的结果
            return output[:inline_limit] + f"\n\n...[工具结果过长且保存完整输出失败：{error}]..."  # 新增代码+ResultPersistence: 落盘失败时至少返回截断内容和错误；若没有这行代码，模型会丢失全部工具结果
        return summarize_offloaded_output(output, inline_limit=inline_limit, artifact_text=artifact_text)  # 修改代码+ResultStorageSplit: 委托 tools.result_storage 生成长结果摘要；若没有这行代码，摘要格式仍堆在主入口

    def _build_initial_messages(self, user_input: str, conversation_history: Sequence[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:  # 修改代码+交互上下文: 构造发给模型的初始 messages 并允许插入交互历史；若没有这行代码，短句追问无法继承上文。
        memory_text = self.memory_path.read_text(encoding="utf-8", errors="replace")  # 修改代码+PromptArchitectureV1: 读取长期记忆原文供索引构建使用；若没有这行代码，长期记忆索引没有输入来源
        static_prompt_text = self._read_static_prompt()  # 新增代码+PromptFiles: 从 staticprompt.md 读取每轮常驻系统提示词；若没有这行代码，静态提示词仍会散落在 Python 代码里
        long_term_memory_text = build_long_term_memory_index(memory_text)  # 新增代码+PromptArchitectureV1: 把 memory.md 原文压缩成长期记忆索引；若没有这行代码，超长 memory.md 会继续全文挤进 system prompt
        block_contents = {  # 修改代码+PromptArchitectureV1: 把原本手工拼接的各段提示词改成 block_id 到文本的映射；若没有这行代码，ContextAssembler 没有输入可装配
            "prompt.kernel.identity": static_prompt_text,  # 修改代码+PromptFiles: 把完整静态系统提示词作为单一文件化 block 注入；若没有这行代码，staticprompt.md 不会进入模型上下文
            "context.long_term_memory_index": long_term_memory_text,  # 修改代码+PromptArchitectureV1: 映射长期记忆索引文本；若没有这行代码，memory.md 会退回全文注入或完全缺失
        }  # 修改代码+PromptArchitectureV1: 结束 block 内容映射；若没有这行代码，Python 字典语法不完整
        assembly_result = ContextAssembler(self.prompt_registry, soft_token_limit=self.prompt_soft_token_limit).assemble_static_blocks(block_contents)  # 修改代码+PromptArchitectureV1: 使用注册表和配置化软预算生成 system prompt；若没有这行代码，生产路径不会按预算生成 compact summary
        self.last_prompt_surface_report = PromptSurfaceReport(loaded_blocks=assembly_result.loaded_blocks, estimated_total_tokens=assembly_result.estimated_total_tokens, compacted=assembly_result.compacted)  # 修改代码+PromptArchitectureV1: 保存本轮提示词表面报告供测试和用户读取；若没有这行代码，loaded_blocks 不会记录到 agent 状态
        system_prompt = assembly_result.system_prompt  # 修改代码+PromptArchitectureV1: 从装配结果取出最终 system prompt；若没有这行代码，messages 无法发送装配后的提示词
        real_browser_task_harness = browser_agent_workflow_from_browser.build_real_browser_task_harness_message(user_input)  # 修改代码+AgentPyCompatWrapperRemovalL7: 初始消息构造直接调用 browser workflow 生成真实浏览器约束；若没有这行代码，删除旧 harness 包装后自然需求不会自动获得 Google 拟人搜索路线。
        if real_browser_task_harness:  # 新增代码+通用真实浏览器Harness: 只有检测到真实浏览器查询任务时才拼接；若没有这行代码，所有任务都会被浏览器 harness 污染
            system_prompt = f"{system_prompt}\n\n{real_browser_task_harness}"  # 新增代码+通用真实浏览器Harness: 把 harness 拼进首条 system 消息以保持两条 messages 结构稳定；若没有这行代码，模型看不到新增约束
        visible_browser_task_harness = browser_agent_workflow_from_browser.build_visible_browser_task_harness_message(user_input)  # 修改代码+AgentPyCompatWrapperRemovalL7: 初始消息构造直接调用 browser workflow 生成可见浏览器约束；若没有这行代码，武汉天气攻略 prompt 看不到可见窗口要求。
        if visible_browser_task_harness:  # 新增代码+自然可见浏览器路由: 只有目标查询才拼接；若没有这行代码，稳定知识和代码任务也会被浏览器规则污染。
            system_prompt = f"{system_prompt}\n\n{visible_browser_task_harness}"  # 新增代码+自然可见浏览器路由: 把可见浏览器 harness 加入系统提示；若没有这行代码，模型仍可能选择后台搜索。
        computer_use_full_harness = build_computer_use_full_model_loop_harness_message(user_input=user_input, desktop_task_context=getattr(self, "desktop_task_context", {}), loaded_tool_names=getattr(self, "loaded_tool_names", set()))  # 修改代码+AgentPySplitPhase15B5: 初始消息直接调用 computer_use/model_loop.py 生成 full 模式提示；如果没有这行代码，删除旧 harness 薄包装后模型看不到桌面任务主循环规则。
        if computer_use_full_harness:  # 新增代码+ModelLoopSemanticPlanner：只有 full 工具包和桌面任务都满足时才拼接；如果没有这一行，普通任务会被桌面控制规则污染。
            system_prompt = f"{system_prompt}\n\n{computer_use_full_harness}"  # 新增代码+ModelLoopSemanticPlanner：把 Computer Use full harness 加入系统提示；如果没有这一行，语义规划仍可能漂回 Python 兼容入口。
        messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]  # 修改代码+交互上下文: 先放系统提示词作为第一条消息；若没有这行代码，模型会失去工具规则和身份约束。
        for history_message in conversation_history or []:  # 新增代码+交互上下文: 遍历调用方注入的历史消息；若没有这行代码，上一轮用户和 assistant 内容不会进入模型。
            if not isinstance(history_message, Mapping):  # 新增代码+交互上下文: 跳过非字典历史；若没有这行代码，坏调用方可能让 .get 访问崩溃。
                continue  # 新增代码+交互上下文: 非法历史直接忽略；若没有这行代码，异常对象会污染模型消息。
            history_role = str(history_message.get("role", "")).strip()  # 新增代码+交互上下文: 读取历史消息角色；若没有这行代码，无法区分 user 和 assistant。
            history_content = str(history_message.get("content", "")).strip()  # 新增代码+交互上下文: 读取历史消息正文；若没有这行代码，空内容或非字符串可能直接发给模型。
            if history_role not in {"user", "assistant"} or not history_content:  # 新增代码+交互上下文: 只允许安全历史角色和非空正文；若没有这行代码，外部输入可能伪造 system 消息。
                continue  # 新增代码+交互上下文: 跳过不安全或空历史；若没有这行代码，系统提示词边界会被污染。
            messages.append({"role": history_role, "content": history_content})  # 新增代码+交互上下文: 把安全历史插入 system 和当前输入之间；若没有这行代码，模型不会看到终端上文。
        messages.append({"role": "user", "content": user_input})  # 修改代码+交互上下文: 最后一条永远是当前用户输入；若没有这行代码，模型不知道本轮具体请求是什么。
        return messages  # 修改代码+交互上下文: 返回完整 OpenAI-compatible messages；若没有这行代码，调用方拿不到模型请求内容。

    def _read_static_prompt(self) -> str:  # 新增代码+PromptFiles: 读取 staticprompt.md 并渲染工作区占位符；若没有这行代码，静态提示词文件不会真正接管系统提示词
        return dynamic_gate_from_prompts.read_static_prompt(self)  # 修改代码+AgentPyPhaseIDynamicGate: 委托 prompts/dynamic_gate.py 读取 staticprompt；若没有这行代码，兼容入口不会返回静态系统提示词。

    def _fallback_static_prompt(self, reason: str) -> str:  # 新增代码+PromptFiles: 构造静态提示词缺失时的最小兜底；若没有这行代码，坏文件会直接打断 agent
        return dynamic_gate_from_prompts.fallback_static_prompt(self, reason)  # 修改代码+AgentPyPhaseIDynamicGate: 委托 prompts/dynamic_gate.py 生成 staticprompt 兜底；若没有这行代码，兼容入口在坏文件场景下会断开。

    def _resolve_static_prompt_path(self) -> Path:  # 新增代码+PromptFiles: 统一解析 staticprompt.md 的加载路径；若没有这行代码，工作区覆盖和包内默认路径会散落在多个地方
        return dynamic_gate_from_prompts.resolve_static_prompt_path(self)  # 修改代码+AgentPyPhaseIDynamicGate: 委托 prompts/dynamic_gate.py 解析 staticprompt 路径；若没有这行代码，兼容入口无法定位静态提示词。

    def _resolve_dynamic_prompt_path(self) -> Path:  # 新增代码+PromptFiles: 统一解析 dynamicprompt.md 的按需加载路径；若没有这行代码，动态规则迁移后没有可审计入口
        return dynamic_gate_from_prompts.resolve_dynamic_prompt_path(self)  # 修改代码+AgentPyPhaseIDynamicGate: 委托 prompts/dynamic_gate.py 解析 dynamicprompt 路径；若没有这行代码，兼容入口无法定位动态提示词。

    def _read_prompt_context_file(self, file_path: Path, max_chars: int) -> str:  # 新增代码+PromptSurfaceV2: 读取单个上下文文件并控制长度；若没有这行代码，三件套读取会重复且容易撑爆上下文
        return dynamic_gate_from_prompts.read_prompt_context_file(file_path, max_chars)  # 修改代码+AgentPyPhaseIDynamicGate: 委托 prompts/dynamic_gate.py 读取并截断上下文文件；若没有这行代码，兼容入口不会返回 context 文件内容。

    def _execute_tool(self, tool_call: ToolCall) -> str:  # 修改代码+ToolsExecutorSplit: 根据工具名称委托 tools.executor 分发到具体工具函数；若没有这行代码，旧调用方会找不到执行入口
        return execute_tool_from_registry(self, tool_call)  # 修改代码+ToolsExecutorSplit: 把 allowed_tools、policy、plan mode、deferred 和工具名分发交给独立执行器；若没有这行代码，执行层仍会堆在 learning_agent.py 里

    def _ask_user_question(self, arguments: dict[str, Any]) -> str:  # 新增代码+AskUserQuestion: 执行内置 ask_user_question 工具；若省略: 模型无法结构化澄清需求
        raw_questions = arguments.get("questions")  # 新增代码+AskUserQuestion: 读取 questions 参数；若省略: 工具不知道模型想问哪些问题
        if not isinstance(raw_questions, list) or not 1 <= len(raw_questions) <= 3:  # 新增代码+AskUserQuestion: 校验问题数量必须是 1 到 3；若省略: 空问题或过多问题会给用户造成困扰
            return "ask_user_question 失败：questions 必须包含 1 到 3 个问题。"  # 新增代码+AskUserQuestion: 返回清楚数量错误；若省略: 模型难以修正参数
        lines = ["ask_user_question 成功：请把下面问题展示给用户，并等待用户下一轮回答。"]  # 新增代码+AskUserQuestion: 构造成功标题；若省略: 模型无法判断工具调用是否成功
        for question_index, raw_question in enumerate(raw_questions, start=1):  # 新增代码+AskUserQuestion: 逐个格式化问题；若省略: 多问题数组不会进入输出
            if not isinstance(raw_question, dict):  # 新增代码+AskUserQuestion: 校验每个问题必须是对象；若省略: 字符串或数字问题会导致后续 .get 崩溃
                return f"ask_user_question 失败：第 {question_index} 个问题必须是对象。"  # 新增代码+AskUserQuestion: 返回问题类型错误；若省略: 模型难以定位坏参数
            question_id = str(raw_question.get("id", "") or "").strip()  # 新增代码+AskUserQuestion: 读取并清理问题 id；若省略: 用户回答后难以对应具体问题
            header = str(raw_question.get("header", "") or "").strip()  # 新增代码+AskUserQuestion: 读取并清理问题标题；若省略: 问题分组信息会丢失
            question_text = str(raw_question.get("question", "") or "").strip()  # 新增代码+AskUserQuestion: 读取并清理正式问题；若省略: 用户不知道要回答什么
            options = raw_question.get("options")  # 新增代码+AskUserQuestion: 读取选项数组；若省略: 工具无法展示可选答案
            if not question_id or not header or not question_text:  # 新增代码+AskUserQuestion: 校验 id/header/question 都不能为空；若省略: 输出会出现无法对应或不可读的问题
                return f"ask_user_question 失败：第 {question_index} 个问题必须包含非空 id、header 和 question。"  # 新增代码+AskUserQuestion: 返回缺字段错误；若省略: 模型难以修正具体字段
            if not isinstance(options, list) or not 2 <= len(options) <= 4:  # 新增代码+AskUserQuestion: 校验选项数量必须是 2 到 4；若省略: 单选项或过多选项都会降低澄清质量
                return f"ask_user_question 失败：第 {question_index} 个问题的 options 必须包含 2 到 4 个选项。"  # 新增代码+AskUserQuestion: 返回选项数量错误；若省略: 模型难以修正选项数组
            lines.append(f"{question_index}. [{header}] {question_text}")  # 新增代码+AskUserQuestion: 输出问题序号、标题和正文；若省略: 用户看不到具体问题
            lines.append(f"   id：{question_id}")  # 新增代码+AskUserQuestion: 输出问题 id；若省略: 用户回答后模型难以对应答案
            for option_index, raw_option in enumerate(options, start=1):  # 新增代码+AskUserQuestion: 逐个格式化选项；若省略: 预设答案不会进入输出
                if not isinstance(raw_option, dict):  # 新增代码+AskUserQuestion: 校验每个选项必须是对象；若省略: 字符串或数字选项会导致后续 .get 崩溃
                    return f"ask_user_question 失败：第 {question_index} 个问题的第 {option_index} 个选项必须是对象。"  # 新增代码+AskUserQuestion: 返回选项类型错误；若省略: 模型难以定位坏选项
                option_label = str(raw_option.get("label", "") or "").strip()  # 新增代码+AskUserQuestion: 读取并清理选项名称；若省略: 用户看不到可选择的短名称
                option_description = str(raw_option.get("description", "") or "").strip()  # 新增代码+AskUserQuestion: 读取并清理选项说明；若省略: 用户无法理解选项取舍
                if not option_label or not option_description:  # 新增代码+AskUserQuestion: 校验选项名称和说明都不能为空；若省略: 空选项会降低澄清质量
                    return f"ask_user_question 失败：第 {question_index} 个问题的第 {option_index} 个选项必须包含非空 label 和 description。"  # 新增代码+AskUserQuestion: 返回选项缺字段错误；若省略: 模型难以修正具体选项
                lines.append(f"   {option_index}. {option_label} - {option_description}")  # 新增代码+AskUserQuestion: 输出选项名称和说明；若省略: 用户无法快速选择答案
        lines.append("请用户直接回复选项编号、选项文字，或补充自己的答案。")  # 新增代码+AskUserQuestion: 说明用户可以怎样回答；若省略: 用户可能不知道下一步输入格式
        return "\n".join(lines)  # 新增代码+AskUserQuestion: 返回完整结构化问题文本；若省略: 工具无法把澄清内容交回模型
