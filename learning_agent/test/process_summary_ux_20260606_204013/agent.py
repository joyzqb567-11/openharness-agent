"""一个教学用的最小私人 Agent：模型调用 + tool loop + 文件工具 + 权限确认 + memory。"""  # 作用: 用模块文档说明这个文件的学习目标

from __future__ import annotations  # 作用: 让类型注解可以延迟解析，减少类定义顺序带来的麻烦

import ast  # 新增代码+LSP工具: 使用 Python 标准库解析源码符号和语法诊断；若省略: LSP 最小版无法在不安装依赖的情况下理解 Python 文件
import base64  # 作用: OAuth PKCE/JWT 解析需要 base64url 编解码
import copy  # 新增代码+MCP 工具注册表健壮性: 提供深拷贝能力保护嵌套 schema 缓存；若省略: 调用方修改返回 schema 会污染注册表内部状态
import hashlib  # 作用: OAuth PKCE 需要用 SHA-256 生成 code_challenge
import http.server  # 作用: OAuth 登录时启动本地回调 HTTP 服务接收授权 code
import json  # 作用: 读写 JSON、构造提示词、解析模型结构化输出
import os  # 作用: 读取环境变量，例如模型名、token 文件路径、Codex 命令
import queue  # 新增代码+MCP stdio client 健壮性: 用线程安全队列接收 stdout reader 的消息；若省略: 请求超时无法绕开阻塞 readline
import secrets  # 作用: 生成安全随机 call_id、PKCE verifier、OAuth state
import signal  # 修改代码+后台命令: 向 Windows 后台命令进程组发送 CTRL_BREAK_EVENT；若没有这行代码，sandbox 下 taskkill 被拒绝时无法温和终止子进程
import subprocess  # 作用: Codex CLI 桥接模式需要启动 codex exec 子进程
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
from typing import Any, Callable, Protocol  # 作用: 描述模型接口、回调函数和通用 JSON 类型

try:  # 修改代码+CoreSplit: 优先从新 core 包导入配置与消息结构；若没有这行代码，learning_agent.py 会继续承载过多基础定义。
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
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.config", "learning_agent.core.events", "learning_agent.core.messages", "learning_agent.core.session"}:  # 修改代码+Stage15G: 允许脚本模式 fallback 覆盖 core.session；若没有这行代码，直接运行时 session 模块会被误判成真实错误。
        raise  # 修改代码+CoreSplit: 重新抛出非路径问题；若没有这行代码，真正的导入错误会被伪装成脚本模式问题。
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
    from learning_agent.models.oauth_tokens import CodexOAuthTokenStore, CodexOAuthTokens  # 修改代码+ModelsSplit: 包运行模式下导入 OAuth token 数据和存储；若没有这行代码，token 逻辑仍会混在主文件。
    from learning_agent.models.openai_chat import OpenAIChatModel  # 修改代码+ModelsSplit: 包运行模式下导入默认 OpenAI-compatible 模型；若没有这行代码，默认模型提供方会断开。
except ModuleNotFoundError as error:  # 修改代码+ModelsSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因导入路径失败。
    if error.name not in {"learning_agent", "learning_agent.models", "learning_agent.models.base", "learning_agent.models.codex_cli", "learning_agent.models.codex_oauth", "learning_agent.models.oauth_tokens", "learning_agent.models.openai_chat"}:  # 修改代码+ModelsSplit: 只允许目标包路径缺失时 fallback；若没有这行代码，models 内部真实 bug 会被误吞。
        raise  # 修改代码+ModelsSplit: 重新抛出非路径问题；若没有这行代码，真正的导入错误会被伪装成脚本模式问题。
    from models.base import ChatModel, stream_chat_events  # 修改代码+Stage15C: 脚本模式下导入模型接口和流式兼容入口；若没有 stream_chat_events，bat 入口无法运行事件流主循环。
    from models.codex_cli import CodexCliChatModel, RunCodexFunction  # 修改代码+ModelsSplit: 脚本运行模式下导入 Codex CLI 适配器；若没有这行代码，bat 入口无法使用 CLI 模型。
    from models.codex_oauth import CodexOAuthChatModel, LoginCallbackFunction, PostJsonFunction  # 修改代码+ModelsSplit: 脚本运行模式下导入 OAuth/API 模型；若没有这行代码，bat 入口无法使用 OAuth 模型。
    from models.oauth_tokens import CodexOAuthTokenStore, CodexOAuthTokens  # 修改代码+ModelsSplit: 脚本运行模式下导入 OAuth token 数据和存储；若没有这行代码，OAuth token 入口会找不到。
    from models.openai_chat import OpenAIChatModel  # 修改代码+ModelsSplit: 脚本运行模式下导入默认 OpenAI-compatible 模型；若没有这行代码，默认模型入口会找不到。


try:  # 修改代码+McpSplit: 优先从新 mcp 包导入配置、客户端、registry 和 doctor；若没有这行代码，learning_agent.py 会继续承载 MCP 实现细节。
    from learning_agent.mcp.auth import McpAuthChallenge, McpAuthenticationRequired  # 修改代码+McpSplit: 包运行模式下导入 MCP 鉴权挑战类型；若没有这行代码，HTTP 401 恢复入口会断开。
    from learning_agent.mcp.config import McpServerConfig, format_mcp_startup_status, load_mcp_server_configs, mcp_server_config_path  # 修改代码+McpSplit: 包运行模式下导入 MCP 配置解析和启动状态函数；若没有这行代码，mcp_servers.json 入口会断开。
    from learning_agent.mcp.doctor import run_mcp_doctor  # 修改代码+McpSplit: 包运行模式下导入 MCP Doctor；若没有这行代码，诊断入口会断开。
    from learning_agent.mcp.http_client import McpHttpClient, McpHttpStreamEvent, McpHttpStreamState, McpSessionExpired  # 修改代码+McpSplit: 包运行模式下导入 HTTP MCP client 和流状态类型；若没有这行代码，远程 HTTP MCP 支持会断开。
    from learning_agent.mcp.registry import McpToolRegistry  # 修改代码+McpSplit: 包运行模式下导入 MCP 工具注册表；若没有这行代码，外部工具发现和路由会断开。
    from learning_agent.mcp.sse_client import McpSseClient  # 修改代码+McpSplit: 包运行模式下导入旧 SSE 边界 client；若没有这行代码，legacy SSE 配置无法被明确处理。
    from learning_agent.mcp.stdio_client import McpStdioClient  # 修改代码+McpSplit: 包运行模式下导入 stdio MCP client；若没有这行代码，本地 MCP server 无法启动。
except ModuleNotFoundError as error:  # 修改代码+McpSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因导入路径失败。
    if error.name not in {"learning_agent", "learning_agent.mcp", "learning_agent.mcp.auth", "learning_agent.mcp.config", "learning_agent.mcp.doctor", "learning_agent.mcp.http_client", "learning_agent.mcp.registry", "learning_agent.mcp.sse_client", "learning_agent.mcp.stdio_client"}:  # 修改代码+McpSplit: 只允许目标包路径缺失时 fallback；若没有这行代码，mcp 内部真实 bug 会被误吞。
        raise  # 修改代码+McpSplit: 重新抛出非路径问题；若没有这行代码，真正的导入错误会被伪装成脚本模式问题。
    from mcp.auth import McpAuthChallenge, McpAuthenticationRequired  # 修改代码+McpSplit: 脚本运行模式下导入 MCP 鉴权挑战类型；若没有这行代码，直接执行文件时鉴权边界会找不到。
    from mcp.config import McpServerConfig, format_mcp_startup_status, load_mcp_server_configs, mcp_server_config_path  # 修改代码+McpSplit: 脚本运行模式下导入 MCP 配置函数；若没有这行代码，bat 入口无法加载 mcp_servers.json。
    from mcp.doctor import run_mcp_doctor  # 修改代码+McpSplit: 脚本运行模式下导入 MCP Doctor；若没有这行代码，`mcp-doctor` 命令会失败。
    from mcp.http_client import McpHttpClient, McpHttpStreamEvent, McpHttpStreamState, McpSessionExpired  # 修改代码+McpSplit: 脚本运行模式下导入 HTTP MCP client 和流状态类型；若没有这行代码，远程 MCP 配置会断开。
    from mcp.registry import McpToolRegistry  # 修改代码+McpSplit: 脚本运行模式下导入 MCP registry；若没有这行代码，LearningAgent 无法发现外部工具。
    from mcp.sse_client import McpSseClient  # 修改代码+McpSplit: 脚本运行模式下导入 legacy SSE client；若没有这行代码，SSE 配置边界会找不到。
    from mcp.stdio_client import McpStdioClient  # 修改代码+McpSplit: 脚本运行模式下导入 stdio MCP client；若没有这行代码，本地 MCP server 无法启动。

try:  # 新增代码+RealChromeDoctor: 优先按包路径导入真实 Chrome 诊断函数；若省略: 作为包运行时 doctor 无法复用 browser_real_chrome 的诊断逻辑
    from learning_agent.browser_real_chrome import diagnose_real_chrome_environment  # 新增代码+RealChromeDoctor: 导入真实 Chrome profile 环境诊断入口；若省略: run_mcp_doctor 无法输出真实 Chrome 路径、profile 和端口状态
except ModuleNotFoundError as error:  # 修改代码+RealChromeDoctor: 捕获包路径导入失败并准备区分脚本模式与内部依赖缺失；若省略: 直接运行 learning_agent.py 仍会因包名影子问题失败
    if error.name not in {"learning_agent", "learning_agent.browser_real_chrome"}:  # 修改代码+RealChromeDoctor: 只允许顶层包或目标子模块在脚本模式下缺失时 fallback；若省略: helper 内部缺依赖会被误吞掉
        raise  # 新增代码+RealChromeDoctor: 重新抛出非包名缺失的导入错误；若省略: 诊断模块内部 bug 会被错误 fallback 掩盖
    from browser_real_chrome import diagnose_real_chrome_environment  # 新增代码+RealChromeDoctor: 脚本运行时从同目录导入诊断入口；若省略: CLI 直接执行文件时 mcp-doctor 无法启动

try:  # 新增代码+ToolPolicyV2: 优先按包路径导入工具策略对象；若没有这行代码，LearningAgent 无法在包运行模式下复用 Task 1 的策略层
    from learning_agent.tool_policy import ToolPolicy, ToolPolicyContext, ToolPolicyDecision  # 新增代码+ToolPolicyV2: 导入策略入口、上下文和决策结果；若没有这行代码，工具池和搜索无法统一读取 visible/selectable/state/reason
except ModuleNotFoundError as error:  # 新增代码+ToolPolicyV2: 捕获脚本模式下的包路径导入失败；若没有这行代码，直接运行 learning_agent.py 可能因为包名路径不同而失败
    if error.name not in {"learning_agent", "learning_agent.tool_policy"}:  # 新增代码+ToolPolicyV2: 只允许顶层包或目标模块缺失时 fallback；若没有这行代码，tool_policy 内部依赖错误会被误吞
        raise  # 新增代码+ToolPolicyV2: 重新抛出非路径问题的导入错误；若没有这行代码，真实导入 bug 会被伪装成脚本模式 fallback
    from tool_policy import ToolPolicy, ToolPolicyContext, ToolPolicyDecision  # 新增代码+ToolPolicyV2: 脚本运行时从同目录导入策略对象；若没有这行代码，CLI 直接执行文件时策略集成不可用

try:  # 修改代码+ToolsSplit: 优先从新 tools 包导入工具类型和目录构建函数；若没有这行代码，learning_agent.py 会继续承载工具元数据实现。
    from learning_agent.tools.atom_tools import rewrite_tool_result_prefix  # 修改代码+AtomToolsSplit: 包运行模式下导入四原子工具结果前缀 helper；若没有这行代码，write 原子工具仍要在主类里手写文本转换。
    from learning_agent.tools.catalog import agent_tool_from_schema, build_builtin_tool_catalog, builtin_tool_capability_pack  # 修改代码+ToolsSplit: 包运行模式下导入工具 schema 包装和 catalog 构建入口；若没有这行代码，MCP 和内置工具无法共享新工具层。
    from learning_agent.tools.executor import execute_tool as execute_tool_from_registry  # 修改代码+ToolsExecutorSplit: 包运行模式下导入工具执行分发器；若没有这行代码，_execute_tool 仍要维护长 if 链。
    from learning_agent.tools.hooks import ToolHookManager  # 新增代码+Stage15E: 包运行模式下导入工具 hook 管理器；若没有这行代码，LearningAgent 无法默认挂载 hook 扩展点。
    from learning_agent.tools.orchestrator import execute_tool_calls as execute_tool_calls_from_orchestrator  # 新增代码+Stage15F: 包运行模式下导入安全并发工具编排器；若没有这行代码，主循环无法批量并发只读工具。
    from learning_agent.tools.pool import available_tool_schemas as pool_available_tool_schemas  # 修改代码+ToolsPoolSplit: 包运行模式下导入工具池到 schema 的转换函数；若没有这行代码，主类仍要手写 schema 映射。
    from learning_agent.tools.pool import current_tool_pool as pool_current_tool_pool  # 修改代码+ToolsPoolSplit: 包运行模式下导入当前工具池过滤函数；若没有这行代码，主类仍要手写 visible 过滤。
    from learning_agent.tools.pool import decide_tool_policy as pool_decide_tool_policy  # 修改代码+ToolsPoolSplit: 包运行模式下导入策略决策 helper；若没有这行代码，主类仍要手写 loaded 和真实 Chrome 阻断逻辑。
    from learning_agent.tools.pool import filter_allowed_tool_schemas as pool_filter_allowed_tool_schemas  # 修改代码+ToolsPoolSplit: 包运行模式下导入 allowed_tools 过滤函数；若没有这行代码，子 agent 白名单过滤仍散在主类。
    from learning_agent.tools.pool import tool_schema_names as pool_tool_schema_names  # 修改代码+ToolsPoolSplit: 包运行模式下导入工具名提取函数；若没有这行代码，日志和测试还要在主类里解析 schema。
    from learning_agent.tools.result_storage import clamp_tool_result_inline_limit, safe_tool_artifact_name, summarize_offloaded_output  # 修改代码+ResultStorageSplit: 包运行模式下导入长结果存储 helper；若没有这行代码，文件名、inline limit 和摘要格式仍留在主入口。
    from learning_agent.tools.types import AgentTool  # 修改代码+ToolsSplit: 包运行模式下导入工具元数据类型；若没有这行代码，LearningAgent 的 catalog 类型边界会留在主文件。
except ModuleNotFoundError as error:  # 修改代码+ToolsSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因导入路径失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.atom_tools", "learning_agent.tools.catalog", "learning_agent.tools.executor", "learning_agent.tools.hooks", "learning_agent.tools.orchestrator", "learning_agent.tools.pool", "learning_agent.tools.result_storage", "learning_agent.tools.types"}:  # 修改代码+Stage15F: 只允许目标包路径缺失时 fallback；若没有这行代码，tools 内部真实 bug 会被误吞。
        raise  # 修改代码+ToolsSplit: 重新抛出非路径问题；若没有这行代码，真正的导入错误会被伪装成脚本模式问题。
    from tools.atom_tools import rewrite_tool_result_prefix  # 修改代码+AtomToolsSplit: 脚本模式下导入四原子工具结果前缀 helper；若没有这行代码，直接执行时 write 原子工具文本转换会断开。
    from tools.catalog import agent_tool_from_schema, build_builtin_tool_catalog, builtin_tool_capability_pack  # 修改代码+ToolsSplit: 脚本模式下从同目录 tools 包导入 catalog 函数；若没有这行代码，双击 bat 入口无法复用新模块。
    from tools.executor import execute_tool as execute_tool_from_registry  # 修改代码+ToolsExecutorSplit: 脚本模式下导入工具执行分发器；若没有这行代码，直接运行时 _execute_tool 无法委托新模块。
    from tools.hooks import ToolHookManager  # 新增代码+Stage15E: 脚本模式下导入工具 hook 管理器；若没有这行代码，bat 入口无法默认挂载 hook 扩展点。
    from tools.orchestrator import execute_tool_calls as execute_tool_calls_from_orchestrator  # 新增代码+Stage15F: 脚本模式下导入安全并发工具编排器；若没有这行代码，bat 入口无法批量并发只读工具。
    from tools.pool import available_tool_schemas as pool_available_tool_schemas  # 修改代码+ToolsPoolSplit: 脚本模式下导入工具池到 schema 的转换函数；若没有这行代码，bat 入口仍会依赖主类内部映射。
    from tools.pool import current_tool_pool as pool_current_tool_pool  # 修改代码+ToolsPoolSplit: 脚本模式下导入当前工具池过滤函数；若没有这行代码，直接运行时工具池 helper 会找不到。
    from tools.pool import decide_tool_policy as pool_decide_tool_policy  # 修改代码+ToolsPoolSplit: 脚本模式下导入策略决策 helper；若没有这行代码，直接运行时策略 helper 会找不到。
    from tools.pool import filter_allowed_tool_schemas as pool_filter_allowed_tool_schemas  # 修改代码+ToolsPoolSplit: 脚本模式下导入 allowed_tools 过滤函数；若没有这行代码，直接运行时子 agent 白名单过滤会断开。
    from tools.pool import tool_schema_names as pool_tool_schema_names  # 修改代码+ToolsPoolSplit: 脚本模式下导入工具名提取函数；若没有这行代码，直接运行时日志工具名提取会断开。
    from tools.result_storage import clamp_tool_result_inline_limit, safe_tool_artifact_name, summarize_offloaded_output  # 修改代码+ResultStorageSplit: 脚本模式下导入长结果存储 helper；若没有这行代码，直接执行时长输出落盘策略会断开。
    from tools.types import AgentTool  # 修改代码+ToolsSplit: 脚本模式下从同目录 tools 包导入 AgentTool；若没有这行代码，直接执行文件时工具元数据类型会找不到。

try:  # 修改代码+PromptsSplit: 优先从 prompts 包导入提示词架构组件；若没有这行代码，prompt 逻辑会继续依赖根目录旧模块入口。
    from learning_agent.prompts.context_assembler import ContextAssembler, PromptSurfaceReport, build_long_term_memory_index  # 修改代码+PromptsSplit: 包运行模式下从 prompts 层导入上下文装配器和长期记忆索引；若没有这行代码，主 agent 无法使用新的 prompt 分层入口。
    from learning_agent.prompts.dynamic_prompt import dynamic_prompt_skill_metadata, resolve_dynamic_prompt_path  # 修改代码+PromptsSplit: 包运行模式下导入 dynamicprompt 路径和伪 skill 元信息 helper；若没有这行代码，动态规则入口仍散在主文件。
    from learning_agent.prompts.registry import build_default_prompt_registry  # 修改代码+PromptsSplit: 包运行模式下从 prompts.registry 导入默认注册表；若没有这行代码，提示词块元数据仍依赖旧路径。
    from learning_agent.prompts.static_prompt import fallback_static_prompt, read_static_prompt, resolve_static_prompt_path  # 修改代码+PromptsSplit: 包运行模式下导入 staticprompt 读取和兜底 helper；若没有这行代码，静态提示词加载仍留在主类内部。
except ModuleNotFoundError as error:  # 修改代码+PromptsSplit: 捕获脚本模式下包路径导入失败；若没有这行代码，直接运行 learning_agent.py 时可能找不到 prompts 包路径。
    if error.name not in {"learning_agent", "learning_agent.prompts", "learning_agent.prompts.context_assembler", "learning_agent.prompts.dynamic_prompt", "learning_agent.prompts.registry", "learning_agent.prompts.static_prompt"}:  # 修改代码+PromptsSplit: 只允许目标路径缺失时 fallback；若没有这行代码，prompts 内部真实错误会被误吞。
        raise  # 修改代码+PromptsSplit: 重新抛出非路径问题；若没有这行代码，真实导入 bug 会被伪装成脚本模式 fallback。
    from prompts.context_assembler import ContextAssembler, PromptSurfaceReport, build_long_term_memory_index  # 修改代码+PromptsSplit: 脚本模式下从 prompts 层导入上下文装配器和长期记忆索引；若没有这行代码，bat 入口无法复用新分层。
    from prompts.dynamic_prompt import dynamic_prompt_skill_metadata, resolve_dynamic_prompt_path  # 修改代码+PromptsSplit: 脚本模式下导入 dynamicprompt helper；若没有这行代码，直接运行时动态提示词入口会断开。
    from prompts.registry import build_default_prompt_registry  # 修改代码+PromptsSplit: 脚本模式下从 prompts.registry 导入默认注册表；若没有这行代码，直接运行时 prompt registry 会找不到。
    from prompts.static_prompt import fallback_static_prompt, read_static_prompt, resolve_static_prompt_path  # 修改代码+PromptsSplit: 脚本模式下导入 staticprompt helper；若没有这行代码，直接运行时静态提示词加载会断开。

try:  # 修改代码+BrowserSplit: 优先从 browser 包导入真实浏览器 helper；若没有这行代码，learning_agent.py 会继续承载浏览器意图和授权细节。
    from learning_agent.browser.harness import build_real_browser_task_harness_message, build_visible_browser_task_harness_message  # 修改代码+自然可见浏览器路由: 包运行模式下同时导入真实 Chrome 和普通可见浏览器 harness；若没有这行代码，普通天气攻略 prompt 无法注入可见浏览器约束。
    from learning_agent.browser.intent import detect_real_browser_information_task, detect_real_chrome_intent, detect_visible_browser_information_task, independent_browser_tool_names, real_chrome_request_blocks_independent_browser  # 修改代码+自然可见浏览器路由: 包运行模式下导入普通实时查询识别；若没有这行代码，主循环无法区分真实 Chrome 与可见 Chromium。
    from learning_agent.browser.permissions import customer_mode_can_auto_approve_terminal_permission, dangerously_skip_permission_reason, dangerously_skip_permissions_enabled, real_browser_customer_auto_approve_reason, real_browser_customer_mode_active, real_browser_customer_progress_message, visible_browser_customer_auto_approve_reason  # 修改代码+危险调试权限: 包运行模式下同时导入危险跳过权限 helper；若没有这行代码，真实调试模式无法绕过终端 y/N。
except ModuleNotFoundError as error:  # 修改代码+BrowserSplit: 捕获直接运行脚本时包路径不可用；若没有这行代码，start_oauth_agent.bat 可能找不到 learning_agent.browser。
    if error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.harness", "learning_agent.browser.intent", "learning_agent.browser.permissions"}:  # 修改代码+BrowserSplit: 只允许目标路径缺失时 fallback；若没有这行代码，browser 内部真实 bug 会被误吞。
        raise  # 修改代码+BrowserSplit: 非路径问题继续抛出；若没有这行代码，真实导入错误会被伪装成脚本模式问题。
    from browser.harness import build_real_browser_task_harness_message, build_visible_browser_task_harness_message  # 修改代码+自然可见浏览器路由: 脚本模式下同时导入两类浏览器 harness；若没有这行代码，bat 入口无法处理普通可见浏览器查询。
    from browser.intent import detect_real_browser_information_task, detect_real_chrome_intent, detect_visible_browser_information_task, independent_browser_tool_names, real_chrome_request_blocks_independent_browser  # 修改代码+自然可见浏览器路由: 脚本模式下导入普通实时查询识别；若没有这行代码，真实终端入口不会触发新增路线。
    from browser.permissions import customer_mode_can_auto_approve_terminal_permission, dangerously_skip_permission_reason, dangerously_skip_permissions_enabled, real_browser_customer_auto_approve_reason, real_browser_customer_mode_active, real_browser_customer_progress_message, visible_browser_customer_auto_approve_reason  # 修改代码+危险调试权限: 脚本模式下同时导入危险跳过权限 helper；若没有这行代码，bat 入口无法实现默认放开权限。

try:  # 修改代码+TasksSplit: 优先从 tasks 包导入任务记录和纯 helper；若没有这行代码，learning_agent.py 会继续承载长期任务数据结构。
    from learning_agent.tasks.background import BackgroundCommand, background_command_status, drain_text_queue  # 修改代码+TasksSplit: 包运行模式下导入后台命令记录和输出 helper；若没有这行代码，后台命令数据结构无法迁出主文件。
    from learning_agent.tasks.cron_monitor import CronRecord, MonitorRecord, cron_monitor_max_results, cron_monitor_state, format_cron_record, format_monitor_record, monitor_result_status  # 修改代码+TasksSplit: 包运行模式下导入 Cron/Monitor 记录和格式化 helper；若没有这行代码，定时监控记录仍会留在主文件。
    from learning_agent.tasks.task_runs import BLOCKED_TASK_TOOL_NAMES, TaskRun, task_background_enabled, task_child_prompt  # 修改代码+TasksSplit: 包运行模式下导入子任务记录和参数 helper；若没有这行代码，task 生命周期对象无法复用。
    from learning_agent.tasks.team import TeamMessage, TeamPeer, peer_status_from_pending_count  # 修改代码+TasksSplit: 包运行模式下导入 team 消息和 peer 记录；若没有这行代码，多 agent 教学记录仍留在主入口。
except ModuleNotFoundError as error:  # 修改代码+TasksSplit: 捕获直接运行脚本时包路径不可用；若没有这行代码，start_oauth_agent.bat 可能找不到 learning_agent.tasks。
    if error.name not in {"learning_agent", "learning_agent.tasks", "learning_agent.tasks.background", "learning_agent.tasks.cron_monitor", "learning_agent.tasks.task_runs", "learning_agent.tasks.team"}:  # 修改代码+TasksSplit: 只允许目标路径缺失时 fallback；若没有这行代码，tasks 内部真实 bug 会被误吞。
        raise  # 修改代码+TasksSplit: 非路径问题继续抛出；若没有这行代码，真实导入错误会被伪装成脚本模式问题。
    from tasks.background import BackgroundCommand, background_command_status, drain_text_queue  # 修改代码+TasksSplit: 脚本模式下导入后台命令记录和输出 helper；若没有这行代码，bat 入口无法复用新 tasks 层。
    from tasks.cron_monitor import CronRecord, MonitorRecord, cron_monitor_max_results, cron_monitor_state, format_cron_record, format_monitor_record, monitor_result_status  # 修改代码+TasksSplit: 脚本模式下导入 Cron/Monitor 记录和格式化 helper；若没有这行代码，直接运行时定时监控工具会找不到记录类。
    from tasks.task_runs import BLOCKED_TASK_TOOL_NAMES, TaskRun, task_background_enabled, task_child_prompt  # 修改代码+TasksSplit: 脚本模式下导入子任务记录和参数 helper；若没有这行代码，直接运行时 task 工具会找不到记录类。
    from tasks.team import TeamMessage, TeamPeer, peer_status_from_pending_count  # 修改代码+TasksSplit: 脚本模式下导入 team 消息和 peer 记录；若没有这行代码，直接运行时 team 工具会找不到记录类。

try:  # 修改代码+ObservabilitySplit: 优先从观测层导入验收、调试、权限和运行记录 helper；若没有这行代码，learning_agent.py 会继续承载观测实现细节。
    from learning_agent.observability.acceptance_events import emit_acceptance_event  # 修改代码+ObservabilitySplit: 包运行模式下导入验收事件写入器；若没有这行代码，真实终端无法暴露稳定状态。
    from learning_agent.observability.debug_log import append_debug_event_record, build_debug_event_record  # 修改代码+ObservabilitySplit: 包运行模式下导入调试日志 helper；若没有这行代码，主类仍要手写 JSONL 落盘。
    from learning_agent.observability.permission_events import build_permission_event_payload as build_permission_event_payload_from_observability  # 修改代码+ObservabilitySplit: 包运行模式下导入权限 payload 构造器；若没有这行代码，权限审计解析仍留在主文件。
    from learning_agent.observability.run_records import build_final_answer_event_payload  # 修改代码+ObservabilitySplit: 包运行模式下导入最终回答事件 payload helper；若没有这行代码，验收字段仍散在入口循环。
    from learning_agent.observability.transcript import TranscriptWriter  # 新增代码+Stage15C: 导入 transcript 写入器；若没有这行代码，run_events 只能 yield 事件但不能落盘恢复。
except ModuleNotFoundError as error:  # 修改代码+ObservabilitySplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能找不到 learning_agent.observability。
    if error.name not in {"learning_agent", "learning_agent.observability", "learning_agent.observability.acceptance_events", "learning_agent.observability.debug_log", "learning_agent.observability.permission_events", "learning_agent.observability.run_records", "learning_agent.observability.transcript"}:  # 修改代码+Stage15C: 允许脚本模式 fallback 覆盖 transcript 模块；若没有这行代码，直接运行时事件落盘会被误判成导入错误。
        raise  # 修改代码+ObservabilitySplit: 重新抛出非路径导入错误；若没有这行代码，真实依赖错误会被伪装成脚本模式。
    from observability.acceptance_events import emit_acceptance_event  # 修改代码+ObservabilitySplit: 脚本模式下导入验收事件写入器；若没有这行代码，bat 启动路径无法使用验收协议。
    from observability.debug_log import append_debug_event_record, build_debug_event_record  # 修改代码+ObservabilitySplit: 脚本模式下导入调试日志 helper；若没有这行代码，直接运行时调试日志会断开。
    from observability.permission_events import build_permission_event_payload as build_permission_event_payload_from_observability  # 修改代码+ObservabilitySplit: 脚本模式下导入权限 payload 构造器；若没有这行代码，直接运行时权限审计会断开。
    from observability.run_records import build_final_answer_event_payload  # 修改代码+ObservabilitySplit: 脚本模式下导入最终回答事件 payload helper；若没有这行代码，真实终端最终回答事件会断开。
    from observability.transcript import TranscriptWriter  # 新增代码+Stage15C: 脚本模式下导入 transcript 写入器；若没有这行代码，bat 入口无法写入事件 transcript。

try:  # 修改代码+AppSplit: 优先从 app 层导入 CLI 和 HTTP bridge 入口 helper；若没有这行代码，learning_agent.py 会继续承载启动应用层实现。
    from learning_agent.app.cli import build_model_from_env as build_model_from_env_from_app  # 修改代码+AppSplit: 包运行模式下导入模型构造 helper；若没有这行代码，模型 provider 选择仍留在主文件。
    from learning_agent.app.cli import format_cli_run_response as format_cli_run_response_from_app  # 修改代码+AppSplit: 包运行模式下导入 CLI 输出格式化 helper；若没有这行代码，JSON 输出结构仍留在主文件。
    from learning_agent.app.cli import main as app_cli_main  # 修改代码+AppSplit: 包运行模式下导入 app CLI 主入口；若没有这行代码，主文件无法瘦身为转发层。
    from learning_agent.app.http_bridge import LearningAgentCommandBridgeServer as AppLearningAgentCommandBridgeServer  # 修改代码+AppSplit: 包运行模式下导入 bridge server 类型；若没有这行代码，旧入口类型无法指向新 app 层。
    from learning_agent.app.http_bridge import create_command_bridge_server as create_command_bridge_server_from_app  # 修改代码+AppSplit: 包运行模式下导入 bridge 工厂；若没有这行代码，HTTP bridge 仍会使用主文件旧实现。
except ModuleNotFoundError as error:  # 修改代码+AppSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能找不到 learning_agent.app。
    if error.name not in {"learning_agent", "learning_agent.app", "learning_agent.app.cli", "learning_agent.app.http_bridge"}:  # 修改代码+AppSplit: 只允许目标路径缺失时 fallback；若没有这行代码，app 内部真实 bug 会被误吞。
        raise  # 修改代码+AppSplit: 重新抛出非路径导入错误；若没有这行代码，真实依赖错误会被伪装成脚本模式。
    from app.cli import build_model_from_env as build_model_from_env_from_app  # 修改代码+AppSplit: 脚本模式下导入模型构造 helper；若没有这行代码，直接运行时模型 provider 选择会断开。
    from app.cli import format_cli_run_response as format_cli_run_response_from_app  # 修改代码+AppSplit: 脚本模式下导入 CLI 输出格式化 helper；若没有这行代码，直接运行时 JSON 输出会断开。
    from app.cli import main as app_cli_main  # 修改代码+AppSplit: 脚本模式下导入 app CLI 主入口；若没有这行代码，bat 入口无法转发到 app 层。
    from app.http_bridge import LearningAgentCommandBridgeServer as AppLearningAgentCommandBridgeServer  # 修改代码+AppSplit: 脚本模式下导入 bridge server 类型；若没有这行代码，旧兼容类型无法指向新实现。
    from app.http_bridge import create_command_bridge_server as create_command_bridge_server_from_app  # 修改代码+AppSplit: 脚本模式下导入 bridge 工厂；若没有这行代码，直接运行时 HTTP bridge 会断开。

LearningAgentCommandBridgeServer = AppLearningAgentCommandBridgeServer  # 修改代码+AppSplit: 让旧入口类型名指向 app.http_bridge 的 server；若没有这行代码，旧测试或外部导入会找不到兼容 bridge server 类。

try:  # 新增代码+ToolSchemaSplit: 包运行模式下从工具 schema 模块读取唯一事实源；若没有这行代码，core.agent 仍会继续保存大块工具定义。
    from learning_agent.tools.schemas import BUILTIN_TOOL_CAPABILITY_PACKS, DYNAMIC_SKILL_CAPABILITY_PACKS, KERNEL_TOOL_NAMES, TOOL_SCHEMAS  # 新增代码+ToolSchemaSplit: 导入内置工具、能力包和动态 skill 映射；若没有这行代码，LearningAgent 无法构建工具目录。
except ModuleNotFoundError as error:  # 新增代码+ToolSchemaSplit: 捕获直接脚本运行时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因包路径失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.schemas"}:  # 新增代码+ToolSchemaSplit: 只允许目标路径缺失时 fallback；若没有这行代码，schemas 模块内部真实 bug 会被误吞。
        raise  # 新增代码+ToolSchemaSplit: 重新抛出真实导入错误；若没有这行代码，排查工具 schema 问题会很困难。
    from tools.schemas import BUILTIN_TOOL_CAPABILITY_PACKS, DYNAMIC_SKILL_CAPABILITY_PACKS, KERNEL_TOOL_NAMES, TOOL_SCHEMAS  # 新增代码+ToolSchemaSplit: 脚本模式下从同目录 tools 包读取 schema；若没有这行代码，直接执行 learning_agent.py 会找不到工具定义。


class ToolCallingFakeModel:  # 作用: 测试用假模型，不联网，按预设顺序返回 ModelMessage
    def __init__(self, responses: list[ModelMessage]) -> None:  # 作用: 初始化假模型并接收预设返回序列
        self._responses = responses  # 作用: 保存预设消息，测试时每次 chat 弹出一条
        self._index = 0  # 作用: 记录下一次应该返回第几条预设消息

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelMessage:  # 作用: 实现 ChatModel 接口，忽略真实推理
        del messages, tools  # 作用: 假模型不需要阅读上下文或工具定义
        if self._index >= len(self._responses):  # 作用: 如果预设消息已经用完
            return ModelMessage(text="假模型没有更多预设回答。")  # 作用: 返回清晰提示，避免测试静默失败
        response = self._responses[self._index]  # 作用: 取出当前这条预设消息
        self._index += 1  # 作用: 指针后移，下一次返回下一条
        return response  # 作用: 返回预设消息给 LearningAgent


def build_model_from_env(workspace: str | Path) -> ChatModel:  # 作用: 根据环境变量选择真实模型来源
    return build_model_from_env_from_app(workspace)  # 修改代码+AppSplit: 委托 app.cli 构造模型；若没有这行代码，CLI 应用层无法真正接管模型 provider 选择。


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
        self.prompt_registry = build_default_prompt_registry()  # 新增代码+PromptArchitectureV1: 保存默认提示词注册表供每轮 ContextAssembler 使用；若没有这行代码，LearningAgent 无法按 block priority 装配系统提示词
        self.last_prompt_surface_report = PromptSurfaceReport.empty()  # 新增代码+PromptArchitectureV1: 初始化空的提示词表面报告；若没有这行代码，测试或用户在首轮前读取报告会遇到属性缺失
        self.prompt_soft_token_limit = prompt_soft_token_limit  # 新增代码+PromptArchitectureV1: 保存本 agent 的提示词软预算；若没有这行代码，_build_initial_messages 无法把配置传给 ContextAssembler
        self.permission_denials: set[str] = set()  # 新增代码+ToolPolicyV2: 记录用户拒绝过的 MCP 工具和清洗后参数指纹；若没有这行代码，同一被拒请求会反复弹权限确认打扰用户
        self.tool_hooks = ToolHookManager()  # 新增代码+Stage15E: 为每个 agent 默认挂载工具 hook 管理器；若没有这行代码，外部必须手动创建属性才能接入执行器生命周期。
        try:  # 新增代码+OSComputerUse: 优先按包路径导入 Computer Use 控制器；若没有这行代码，桌面控制能力无法在 agent 初始化时挂载。
            from learning_agent.computer_use.controller import ComputerUseController  # 新增代码+OSComputerUse: 读取 OS 级 Computer Use 控制器；若没有这行代码，computer_status/computer_action 没有执行入口。
        except ModuleNotFoundError as error:  # 新增代码+OSComputerUse: 兼容直接脚本运行时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因导入路径崩溃。
            if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.controller"}:  # 新增代码+OSComputerUse: 只吞目标包路径缺失；若没有这行代码，控制器内部真实 bug 会被误吞。
                raise  # 新增代码+OSComputerUse: 重新抛出真实导入错误；若没有这行代码，排查 Computer Use 问题会很困难。
            from computer_use.controller import ComputerUseController  # 新增代码+OSComputerUse: 脚本模式下从本地包导入控制器；若没有这行代码，直接执行入口无法初始化桌面能力。
        self.computer_use_controller = ComputerUseController()  # 新增代码+OSComputerUse: 挂载默认安全关闭的 Computer Use 控制器；若没有这行代码，新工具路由会找不到后端状态。
        self.mcp_call_progress_events: list[dict[str, Any]] = []  # 新增代码+MCPProgress: 保存 MCP 调用从权限、开始、完成到失败的结构化进度；若没有这行代码，Phase 3 的 call progress 只能靠肉眼看终端文本
        self.observation_events: list[dict[str, Any]] = []  # 新增代码+ObservationV1: 保存工具结果、权限、错误和上下文压缩相关观察事件；若没有这行代码，Phase 6 无法提供可审计的 structured observation
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

    def run(self, user_input: str, max_turns: int | None = None, event_callback: Callable[[Any], None] | None = None) -> str:  # 修改代码+ProcessSummaryUX: 增加可选事件回调用于终端过程摘要；若没有这行代码，interactive.py 无法在保留 harness 的同时显示主循环进度。
        if max_turns is not None and max_turns < 1:  # 新增代码+可配置轮次: 保护直接调用 run() 时传入非法轮次；若省略: 0 或负数会导致一开始就安全停止且难以理解
            raise ValueError("max_turns 必须是正整数，或使用 None 表示不按固定轮次主动停止。")  # 新增代码+可配置轮次: 给出清楚错误；若省略: 调用方不知道应该传什么值
        # 修改代码+ModelLoopComputerUse：这里刻意不再调用 _desktop_task_runtime_answer_from_prompt；如果保留模型前抢跑，Python 分类器会替模型理解“画猫/画房子/操作任意软件”，/computer use --full 就无法像 ClaudeCode 一样由模型结合工具 schema、屏幕观察和工具结果自主规划。
        from learning_agent.runtime.session_runtime import run_agent_with_harness_session  # 新增代码+HarnessSessionRuntime: 延迟导入 harness session runtime 避免初始化阶段循环导入；若没有这行代码，真实 run() 仍会绕过 durable harness。
        return run_agent_with_harness_session(self, user_input, max_turns=max_turns, event_callback=event_callback)  # 修改代码+ProcessSummaryUX: 把可选事件回调透传给 harness runtime；若没有这行代码，终端摘要渲染器永远收不到事件。

    def _desktop_task_runtime_answer_from_prompt(self, user_input: str) -> str | None:  # 新增代码+DesktopTaskRuntimeRoute：函数段开始，把普通 prompt 分流到桌面任务 runtime；如果没有这段函数，run() 无法在模型前执行治本路由。
        normalized_input = str(user_input or "").strip()  # 新增代码+DesktopTaskRuntimeRoute：清理用户输入；如果没有这一行，None 或空白输入会让分类器边界不清楚。
        if not normalized_input or normalized_input.startswith("/"):  # 新增代码+DesktopTaskRuntimeRoute：空输入和斜杠命令不走桌面任务 runtime；如果没有这一行，/computer use --full 可能被普通任务路由误处理。
            return None  # 新增代码+DesktopTaskRuntimeRoute：返回 None 表示继续旧流程或交互层命令流程；如果没有这一行，命令边界会混乱。
        try:  # 新增代码+DesktopTaskRuntimeRoute：优先按包路径导入桌面任务分类器；如果没有这一行，项目根运行时无法复用 Task 2 路由。
            from learning_agent.computer_use.desktop_task_router import classify_desktop_task  # 新增代码+DesktopTaskRuntimeRoute：导入自然语言桌面任务分类器；如果没有这一行，run() 不知道哪些 prompt 该提前分流。
        except ModuleNotFoundError as error:  # 新增代码+DesktopTaskRuntimeRoute：兼容 start_oauth_agent.bat 从 learning_agent 目录启动；如果没有这一行，脚本模式可能因包名前缀失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.desktop_task_router"}:  # 新增代码+DesktopTaskRuntimeRoute：只对包路径缺失兜底；如果没有这一行，分类器内部 bug 会被误吞。
                raise  # 新增代码+DesktopTaskRuntimeRoute：重新抛出真实导入错误；如果没有这一行，排查分类器问题会非常困难。
            from computer_use.desktop_task_router import classify_desktop_task  # 新增代码+DesktopTaskRuntimeRoute：脚本模式导入同一分类器；如果没有这一行，bat 入口无法识别普通桌面任务。
        intent = classify_desktop_task(normalized_input)  # 新增代码+DesktopTaskRuntimeRoute：运行脱敏分类；如果没有这一行，run() 无法判断是否应交给 Computer Use runtime。
        if not bool(intent.is_desktop_task and intent.requires_gui_actions):  # 新增代码+DesktopTaskRuntimeRoute：只拦截需要 GUI 动作的桌面任务；如果没有这一行，普通解释/代码任务会被错误路由。
            return None  # 新增代码+DesktopTaskRuntimeRoute：非桌面任务保持旧模型 loop；如果没有这一行，原有 agent 能力会被破坏。
        runtime = self._desktop_task_runtime_for_current_run()  # 新增代码+DesktopTaskRuntimeRoute：取得注入或默认桌面任务 runtime；如果没有这一行，run() 没有执行 GUI 证据链的对象。
        real_actions = True  # 修改代码+源码复核门禁：自然语言桌面任务在 full 授权后必须请求真实执行路径；如果没有这一行，agent 会继续用 recording 证据冒充真实能力。
        report = runtime.run_prompt(normalized_input, real_actions=real_actions)  # 修改代码+源码复核门禁：把桌面任务交给真实动作请求路径，runtime 会在未授权或未接线时安全拒绝；如果没有这一行，用户会误以为 /computer use --full 已经能真实操作桌面。
        return self._format_desktop_task_runtime_answer(report)  # 新增代码+DesktopTaskRuntimeRoute：把报告转成用户可见答案；如果没有这一行，终端看不到稳定 token 和下一步提示。
    # 新增代码+DesktopTaskRuntimeRoute：函数段结束，_desktop_task_runtime_answer_from_prompt 到此结束；如果没有这个边界说明，代码小白不容易看出普通 prompt 分流范围。

    def _desktop_task_runtime_for_current_run(self) -> Any:  # 新增代码+DesktopTaskRuntimeRoute：函数段开始，取得当前 run 应使用的桌面任务 runtime；如果没有这段函数，测试无法注入 full-mode runtime。
        injected_runtime = getattr(self, "desktop_task_runtime", None)  # 新增代码+DesktopTaskRuntimeRoute：读取测试或上层注入的 runtime；如果没有这一行，单元测试无法隔离 full mode 状态。
        if injected_runtime is not None:  # 新增代码+DesktopTaskRuntimeRoute：如果已有注入 runtime 就直接使用；如果没有这一行，测试注入会被默认 runtime 覆盖。
            return injected_runtime  # 新增代码+DesktopTaskRuntimeRoute：返回注入对象；如果没有这一行，full-mode 正向测试无法稳定通过。
        try:  # 修改代码+UniversalDesktopAdapter：优先按包路径导入桌面任务 runtime 和通用 adapter；如果没有这一行，项目根运行时无法构造已接通用闭环的默认 runtime。
            from learning_agent.computer_use.desktop_task_runtime import ComputerUseDesktopTaskRuntime  # 新增代码+DesktopTaskRuntimeRoute：导入桌面任务运行时类；如果没有这一行，run() 无法构造默认 runtime。
            from learning_agent.computer_use.controlled_physical_sendinput import WindowsControlledPhysicalSendInputSender  # 新增代码+RealPhysicalFullMode：导入 Phase95 受控物理 sender；如果没有这一行，默认 /computer use --full 无法经过安全门发送真实鼠标键盘。
            from learning_agent.computer_use.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+RealPhysicalFullMode：导入真实 Windows SendInput 底层后端；如果没有这一行，受控 sender 背后没有能触达本机桌面的物理输入实现。
            from learning_agent.computer_use.universal_desktop_execution_loop import UniversalDesktopExecutionLoopAdapter  # 新增代码+UniversalDesktopAdapter：导入通用桌面执行 adapter；如果没有这一行，默认 full 模式会继续停在 real_execution_loop=None。
        except ModuleNotFoundError as error:  # 新增代码+DesktopTaskRuntimeRoute：兼容脚本模式包名前缀缺失；如果没有这一行，真实 bat 入口可能导入失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.desktop_task_runtime", "learning_agent.computer_use.controlled_physical_sendinput", "learning_agent.computer_use.real_sendinput_guard", "learning_agent.computer_use.universal_desktop_execution_loop"}:  # 修改代码+RealPhysicalFullMode：脚本模式兜底名单加入受控物理 sender 和真实 SendInput 后端；如果没有这一行，bat 入口可能把路径差异误当成内部 bug。
                raise  # 新增代码+DesktopTaskRuntimeRoute：重新抛出真实导入错误；如果没有这一行，排查 runtime 问题会很困难。
            from computer_use.desktop_task_runtime import ComputerUseDesktopTaskRuntime  # 新增代码+DesktopTaskRuntimeRoute：脚本模式导入同一 runtime；如果没有这一行，bat 入口无法运行桌面任务。
            from computer_use.controlled_physical_sendinput import WindowsControlledPhysicalSendInputSender  # type: ignore  # 新增代码+RealPhysicalFullMode：脚本模式导入 Phase95 受控物理 sender；如果没有这一行，start_oauth_agent.bat 下 full 模式不能接真实输入门禁。
            from computer_use.real_sendinput_guard import WindowsSendInputLowLevelSender  # type: ignore  # 新增代码+RealPhysicalFullMode：脚本模式导入真实 Windows SendInput 后端；如果没有这一行，真实可见终端入口没有物理鼠标键盘后端。
            from computer_use.universal_desktop_execution_loop import UniversalDesktopExecutionLoopAdapter  # type: ignore  # 新增代码+UniversalDesktopAdapter：脚本模式导入同一通用 adapter；如果没有这一行，真实可见终端入口无法接入通用闭环。
        runtime_root = Path(self.workspace) / "memory" / "computer_use" / "desktop_task_runtime"  # 新增代码+DesktopTaskRuntimeRoute：把默认 runtime 证据写入当前 workspace；如果没有这一行，证据路径会和当前 agent 工作区脱节。
        physical_sender_backend = WindowsSendInputLowLevelSender(platform="win32")  # 新增代码+RealPhysicalFullMode：创建真实 Windows SendInput 底层后端；如果没有这一行，默认 full 模式只能记录动作而不能触达用户本机鼠标键盘。
        controlled_physical_sender = WindowsControlledPhysicalSendInputSender(low_level_backend=physical_sender_backend, platform="win32", default_enable_physical_dispatch=True)  # 新增代码+RealPhysicalFullMode：把真实后端包进 Phase95 受控 sender 并显式开启 full 模式物理派发；如果没有这一行，真实后端不会经过安全目标门禁也不会被默认 adapter 使用。
        runtime = ComputerUseDesktopTaskRuntime(base_dir=runtime_root, real_execution_loop=UniversalDesktopExecutionLoopAdapter(controlled_physical_sender=controlled_physical_sender, enable_real_target_launch=True))  # 修改代码+RealLaunchTargetSession：默认生产路径接通用真实启动、真实观察和受控物理 sender，同时不启用 Paint/Pikachu 专用桥；如果没有这一行，/computer use --full 会再次误用用户已打开窗口。
        self.desktop_task_runtime = runtime  # 新增代码+DesktopTaskRuntimeRoute：缓存 runtime 供同一 agent 后续复用；如果没有这一行，每次 prompt 都会重复初始化证据目录。
        return runtime  # 新增代码+DesktopTaskRuntimeRoute：返回默认 runtime；如果没有这一行，调用方拿不到执行对象。
    # 新增代码+DesktopTaskRuntimeRoute：函数段结束，_desktop_task_runtime_for_current_run 到此结束；如果没有这个边界说明，代码小白不容易看出 runtime 获取范围。

    def _format_desktop_task_runtime_answer(self, report: dict[str, Any]) -> str:  # 新增代码+DesktopTaskRuntimeRoute：函数段开始，把 runtime 报告转成最终回答文本；如果没有这段函数，run() 返回会缺少稳定可验收格式。
        try:  # 新增代码+DesktopTaskRuntimeRoute：优先按包路径导入 CLI 行格式化器；如果没有这一行，终端输出格式会重复手写。
            from learning_agent.computer_use.desktop_task_runtime import computer_use_full_desktop_task_runtime_cli_line  # 新增代码+DesktopTaskRuntimeRoute：导入 Task 4 稳定 token 行函数；如果没有这一行，答案无法复用同一验收格式。
        except ModuleNotFoundError as error:  # 新增代码+DesktopTaskRuntimeRoute：兼容脚本模式包名前缀缺失；如果没有这一行，bat 入口可能导入失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.desktop_task_runtime"}:  # 新增代码+DesktopTaskRuntimeRoute：只对目标路径缺失兜底；如果没有这一行，内部错误会被误吞。
                raise  # 新增代码+DesktopTaskRuntimeRoute：重新抛出真实导入错误；如果没有这一行，排查 formatter 问题会困难。
            from computer_use.desktop_task_runtime import computer_use_full_desktop_task_runtime_cli_line  # 新增代码+DesktopTaskRuntimeRoute：脚本模式导入同一 token 行函数；如果没有这一行，bat 入口无法输出稳定 token。
        token_line = computer_use_full_desktop_task_runtime_cli_line(report)  # 新增代码+DesktopTaskRuntimeRoute：生成固定顺序 token 行；如果没有这一行，controller 无法稳定判断 GUI 路由是否生效。
        decision = str(report.get("decision", ""))  # 新增代码+源码复核门禁：读取 runtime 决策码用于选择不误导的提示文案；如果没有这一行，后续只能用模糊状态猜测原因。
        if decision == "computer_use_full_mode_required":  # 修改代码+源码复核门禁：未授权时只提示先执行 full-confirm；如果没有这一行，用户会误以为已经进入执行链路。
            guidance_line = "请先运行 /computer use --full 并按提示执行 /computer use --full-confirm <token>。"  # 修改代码+源码复核门禁：给出开启 full 的下一步；如果没有这一行，未授权失败没有可操作指引。
        elif decision == "real_actions_not_enabled_in_desktop_task_runtime":  # 新增代码+源码复核门禁：真实动作闭环未接线时单独提示；如果没有这一行，失败会被误说成录制模式证据链。
            guidance_line = "已进入真实动作请求路径，但当前 runtime 尚未接入真实桌面执行闭环，不能声明成熟完成。"  # 新增代码+源码复核门禁：明确这是能力缺口而非成功；如果没有这一行，用户会把 full 模式误读成已经能真实控制桌面。
        elif decision == "universal_desktop_execution_loop_connected_without_real_dispatch":  # 新增代码+UniversalDesktopAdapter：通用闭环已接通但未物理派发时单独提示；如果没有这一行，用户会把通用 adapter 的录制事件误读成真实桌面控制。
            guidance_line = "已接入通用 observe-plan-act-verify 桌面执行闭环，但当前仅证明通用动作链路已展开，尚未接入物理真实桌面派发，不能声明成熟完成。"  # 新增代码+UniversalDesktopAdapter：明确 adapter 的真实边界；如果没有这一行，/computer use --full 可能再次被误解为已经能随意控制本机软件。
        elif bool(report.get("passed", False)) and bool(report.get("recording_mode", False)):  # 新增代码+源码复核门禁：录制模式通过时才说录制证据链；如果没有这一行，失败路径也会被套用成功文案。
            guidance_line = "桌面任务已交给 Computer Use runtime 录制模式证据链。"  # 修改代码+源码复核门禁：保留录制模式成功说明；如果没有这一行，旧录制验收的成功语义会丢失。
        elif bool(report.get("passed", False)):  # 新增代码+源码复核门禁：非录制且通过时说明真实闭环完成本次任务；如果没有这一行，真实路径成功也会显示成录制模式。
            guidance_line = "桌面任务已交给 Computer Use runtime 真实执行闭环，并返回可复核证据。"  # 新增代码+源码复核门禁：给真实执行成功一个准确文案；如果没有这一行，用户无法区分 real 和 recording。
        else:  # 新增代码+源码复核门禁：其它失败原因走保守提示；如果没有这一行，未知失败可能没有提示文本。
            guidance_line = "Computer Use runtime 返回失败报告，请以 decision 和 report_json 为准继续排查。"  # 新增代码+源码复核门禁：让失败解释回到结构化源码事实；如果没有这一行，未知失败会被误导性文案覆盖。
        report_json = json.dumps(report, ensure_ascii=False, sort_keys=True)  # 新增代码+DesktopTaskRuntimeRoute：序列化完整脱敏报告供验收排查；如果没有这一行，失败时只能看短 token。
        return f"Computer Use Desktop Task\n- {token_line}\n- decision={report.get('decision', '')}\n- {guidance_line}\n- report_json={report_json}"  # 新增代码+DesktopTaskRuntimeRoute：返回最终文本；如果没有这一行，run() 无法把 runtime 结果展示给用户和测试。
    # 新增代码+DesktopTaskRuntimeRoute：函数段结束，_format_desktop_task_runtime_answer 到此结束；如果没有这个边界说明，代码小白不容易看出答案格式范围。

    def _desktop_task_policy_context_from_prompt(self, user_input: str) -> dict[str, Any]:  # 新增代码+DesktopTaskPolicy：函数段开始，把用户自然语言 prompt 转成脱敏桌面任务策略上下文；如果没有这段函数，run_events 无法在真实模型工具循环前自动设置 active，作者意图是复用 Task 2 分类器而不保存原始 prompt，本函数与 run_events 和 _bash_atom 配合到 return 结束。
        try:  # 新增代码+DesktopTaskPolicy：优先按包运行模式导入桌面任务分类器；如果没有这一行，unittest 和包启动路径无法复用 Task 2 分类逻辑。
            from learning_agent.computer_use.desktop_task_router import classify_desktop_task  # 新增代码+DesktopTaskPolicy：导入自然语言桌面任务分类函数；如果没有这一行，策略上下文只能靠手动 monkeypatch。
        except ModuleNotFoundError as error:  # 新增代码+DesktopTaskPolicy：兼容直接脚本运行时 learning_agent 包路径不可用的情况；如果没有这一行，bat 入口可能因包名前缀失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.desktop_task_router"}:  # 新增代码+DesktopTaskPolicy：只对目标包路径缺失做 fallback；如果没有这一行，分类器内部真实 bug 会被误吞。
                raise  # 新增代码+DesktopTaskPolicy：重新抛出非目标导入错误；如果没有这一行，排查分类器内部问题会很困难。
            from computer_use.desktop_task_router import classify_desktop_task  # 新增代码+DesktopTaskPolicy：脚本模式下从本地 computer_use 包导入分类函数；如果没有这一行，start_oauth_agent.bat 可能无法加载 Task 2 分类器。
        intent = classify_desktop_task(user_input)  # 新增代码+DesktopTaskPolicy：用同一套桌面任务分类器判断当前 prompt；如果没有这一行，active 状态会和 Task 2 路由结果分裂。
        return {  # 新增代码+DesktopTaskPolicy：返回脱敏上下文字典；如果没有这一行，_bash_atom 无法从统一字段读取 active 和目标信息。
            "active": bool(intent.is_desktop_task),  # 新增代码+DesktopTaskPolicy：把是否桌面任务写入 active；如果没有这一项，bash 策略不会知道何时必须拦截脚本绕路。
            "reason": intent.reason,  # 新增代码+DesktopTaskPolicy：保存分类原因而不是原始 prompt；如果没有这一项，日志难以解释为什么开启或关闭桌面任务门禁。
            "target_app_hint": intent.target_app_hint,  # 新增代码+DesktopTaskPolicy：保存目标应用提示；如果没有这一项，后续 runtime 无法复用本次识别到的 Paint/mspaint 线索。
            "task_goal": intent.task_goal,  # 新增代码+DesktopTaskPolicy：保存脱敏任务目标摘要；如果没有这一项，后续 GUI runtime 缺少稳定目标类型。
            "requires_gui_actions": bool(intent.requires_gui_actions),  # 新增代码+DesktopTaskPolicy：保存是否需要 GUI 动作；如果没有这一项，策略无法区分本地应用观察和真正操作。
            "raw_prompt_included": bool(intent.raw_prompt_included),  # 新增代码+DesktopTaskPolicy：明确记录没有保存原始 prompt；如果没有这一项，后续审计无法确认脱敏边界。
        }  # 新增代码+DesktopTaskPolicy：上下文字典结束；如果没有这一行，Python 字典语法不完整。
    # 新增代码+DesktopTaskPolicy：函数段结束，_desktop_task_policy_context_from_prompt 到此结束；如果没有这个边界说明，代码小白不容易看出上下文构造范围。

    def _restore_desktop_task_policy_context(self, previous_context: dict[str, Any]) -> None:  # 新增代码+DesktopTaskPolicy：函数段开始，恢复 run_events 进入前的桌面任务上下文；如果没有这段函数，桌面任务 active 可能污染下一轮普通任务，作者意图是让上下文生命周期严格绑定单次 run_events，本函数与 run_events 的 finally 配合到赋值结束。
        if isinstance(previous_context, dict):  # 新增代码+DesktopTaskPolicy：只在旧上下文确实是字典时原样恢复；如果没有这一行，异常形状可能再次污染 desktop_task_context。
            self.desktop_task_context = copy.deepcopy(previous_context)  # 新增代码+DesktopTaskPolicy：深拷贝恢复旧上下文避免共享可变对象；如果没有这一行，后续修改可能影响保存的旧值。
            return  # 新增代码+DesktopTaskPolicy：恢复完成后直接返回；如果没有这一行，下面的兜底 inactive 会覆盖合法旧上下文。
        self.desktop_task_context = {"active": False}  # 新增代码+DesktopTaskPolicy：旧上下文不是字典时兜底恢复为 inactive；如果没有这一行，异常状态可能让下一轮 bash 策略崩溃。
    # 新增代码+DesktopTaskPolicy：函数段结束，_restore_desktop_task_policy_context 到此结束；如果没有这个边界说明，代码小白不容易看出上下文恢复范围。

    def run_events(self, user_input: str, max_turns: int | None = None):  # 新增代码+Stage15C: 新增事件流主循环；若没有这行代码，UI、HTTP bridge 和 transcript 无法观察运行过程。
        if max_turns is not None and max_turns < 1:  # 新增代码+Stage15C: 保留旧 run 的非法轮次校验；若没有这行代码，0 或负数会产生难懂行为。
            raise ValueError("max_turns 必须是正整数，或使用 None 表示不按固定轮次主动停止。")  # 新增代码+Stage15C: 给出旧兼容错误；若没有这行代码，调用方不知道正确 max_turns 格式。
        session_id = self._new_session_id()  # 新增代码+Stage15C: 为本轮事件创建 session id；若没有这行代码，transcript 无法按会话归档。
        run_id = self._new_debug_run_id()  # 新增代码+Stage15C: 为本轮事件和 debug 日志创建 run id；若没有这行代码，事件无法串起同一次运行。
        transcript_writer = TranscriptWriter(self.workspace / "memory" / "sessions", session_id)  # 新增代码+Stage15C: 创建 transcript 写入器；若没有这行代码，事件只会在内存中一闪而过。
        session_store = SessionStore(self.workspace / "memory" / "sessions")  # 新增代码+Stage15G: 创建会话摘要 store；若没有这行代码，run_events 只能写 events.jsonl 而不能保存 resume summary。
        from learning_agent.core.compact import compact_messages_with_boundary, should_compact_messages  # 新增代码+CompactResumeStatus: 延迟导入 compact 策略，避免主文件启动时引入额外依赖；若没有这行代码，真实主循环不会自动压缩长上下文。
        from learning_agent.core.reactive_compact import is_prompt_too_long_error, try_reactive_compact  # 新增代码+ReactiveCompactRuntime: 延迟导入模型上下文超限恢复入口；若没有这行代码，真实主循环遇到 prompt too long 只能失败退出。
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

        def save_session_summary(final_answer: str) -> Path:  # 新增代码+Stage15G: 保存当前 session 的可恢复摘要；若没有这行代码，完成后只能靠原始事件手工恢复。
            permission_decisions = [event for event in self.observation_events if event.get("kind") == "permission_decided"]  # 新增代码+Stage15G: 从观察流提取权限决策；若没有这行代码，summary 无法复盘授权过程。
            record = SessionRecord(session_id=session_id, run_id=run_id, user_input=user_input, messages=copy.deepcopy(session_messages), tool_calls=copy.deepcopy(session_tool_calls), tool_results=copy.deepcopy(session_tool_results), permission_decisions=copy.deepcopy(permission_decisions), final_answer=final_answer, artifacts=list(self.active_artifacts))  # 新增代码+Stage15G: 构造会话摘要对象；若没有这行代码，store 没有完整数据可写。
            return session_store.save_summary(record)  # 新增代码+Stage15G: 写入 summary.json 并返回路径；若没有这行代码，session 摘要不会落盘。

        previous_desktop_task_context = copy.deepcopy(self.desktop_task_context) if isinstance(getattr(self, "desktop_task_context", {}), dict) else {"active": False}  # 新增代码+DesktopTaskPolicy：保存进入本轮 run_events 前的桌面任务上下文；如果没有这一行，finally 无法把 active 清回旧状态。
        try:  # 新增代码+Stage15C: 捕获主循环异常并转成 run_failed 事件；若没有这行代码，事件消费者会看到生成器直接崩溃。
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
            self.real_chrome_requested = self._detect_real_chrome_intent(user_input)  # 新增代码+Stage15C: 保留真实 Chrome 意图识别；若没有这行代码，真实浏览器策略会退化。
            self.real_browser_information_task_requested = self._detect_real_browser_information_task(user_input)  # 新增代码+Stage15C: 保留公开信息查询识别；若没有这行代码，客户模式自动授权会退化。
            self.visible_browser_information_task_requested = self._detect_visible_browser_information_task(user_input)  # 新增代码+自然可见浏览器路由: 识别普通实时查询是否需要可见浏览器；若没有这行代码，精准 prompt 首轮仍看不到 browser_launch_visible。
            self._load_visible_browser_tools_for_information_task()  # 新增代码+自然可见浏览器路由: 在构造初始工具池前预加载可见浏览器工具；若没有这行代码，harness 文案存在但模型仍不能调用工具。
            self._maybe_confirm_plan_from_user_input(user_input)  # 新增代码+Stage15C: 保留计划确认解锁逻辑；若没有这行代码，已确认计划仍可能被阻断。
            self._write_debug_event(run_id=run_id, event="user_input", payload={"text": user_input})  # 新增代码+Stage15C: 保留旧 debug 日志；若没有这行代码，已有排查方式会丢失。
            messages = self._build_initial_messages(user_input)  # 新增代码+Stage15C: 构造初始 messages；若没有这行代码，模型没有系统提示词和用户输入。
            session_messages = messages  # 新增代码+Stage15G: 让 summary helper 使用同一份运行消息历史；若没有这行代码，summary.json 的 messages 会保持空列表。
            initial_tools = self._available_tool_schemas()  # 新增代码+Stage15C: 读取初始工具池快照；若没有这行代码，事件和 debug 日志无法说明模型看到哪些工具。
            initial_tool_names = self._tool_schema_names(initial_tools)  # 新增代码+Stage15C: 提取初始工具名；若没有这行代码，事件 payload 会塞入冗长 schema。
            self._write_debug_event(run_id=run_id, event="initial_messages", payload={"messages": messages, "tool_names": initial_tool_names})  # 新增代码+Stage15C: 保留旧初始日志；若没有这行代码，select 后工具池排查会变难。
            yield emit("initial_messages_built", {"message_count": len(messages), "tool_names": initial_tool_names})  # 新增代码+Stage15C: 发出初始上下文事件；若没有这行代码，UI 无法解释第一轮上下文准备完成。
            turn = 0  # 新增代码+Stage15C: 初始化轮次；若没有这行代码，无固定上限循环无法推进。
            final_answer_retry_count = 0  # 新增代码+Stage15C: 初始化最终回答重试次数；若没有这行代码，格式重写可能无限循环。
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
                tools = self._scoped_tool_schemas_for_model_turn(self._available_tool_schemas(), turn)  # 修改代码+ModelLoopFirstStepLaunch：每轮先取当前工具池再按 full 桌面任务首步收窄；如果没有这一行，自然语言本机应用任务第 0 轮会继续把编码工具和桌面工具一起暴露给模型导致超时。
                tool_names = self._tool_schema_names(tools)  # 新增代码+Stage15C: 提取本轮工具名；若没有这行代码，事件 payload 会过大。
                if should_compact_messages(messages, max_messages=20, max_chars=max(4000, self.prompt_soft_token_limit * 4)):  # 新增代码+CompactResumeStatus: 在模型请求前检查上下文是否需要 compact；若没有这行代码，长任务会无限堆消息直到模型上下文爆掉。
                    yield emit("compact_started", {"turn": turn, "turn_id": current_turn_id, "reason": "run_events_pre_model_budget"})  # 新增代码+DeepCompactRuntime: 在执行 compact 前先发开始事件；若没有这行代码，UI/SDK 只能看到结束看不到卡在哪一步。
                    compact_artifact_dir = self.workspace / "memory" / "compact_artifacts" / session_id  # 新增代码+DeepCompactRuntime: 为本 session 准备 compact artifact 目录；若没有这行代码，长工具输出 snip 后没有稳定落盘位置。
                    compacted_messages, compact_boundary = compact_messages_with_boundary(messages, session_id=session_id, run_id=run_id, turn_id=current_turn_id, max_messages=20, reason="run_events_pre_model_budget", artifact_dir=compact_artifact_dir)  # 修改代码+DeepCompactRuntime: 生成多层摘要消息和 artifact 边界；若没有这行代码，压缩仍缺少完整证据落盘。
                    messages[:] = compacted_messages  # 新增代码+CompactResumeStatus: 原地替换消息列表保持 session summary 引用不丢；若没有这行代码，summary 可能继续指向未压缩旧列表。
                    compact_entry = transcript_v2_store.append_entry(session_id=session_id, run_id=run_id, turn_id=current_turn_id, event_type="compact_boundary", payload=compact_boundary.to_dict(), parent_uuid=last_transcript_uuid)  # 新增代码+CompactResumeStatus: 把 compact boundary 写入 transcript v2；若没有这行代码，resume loader 无法确认压缩点。
                    last_transcript_uuid = compact_entry.uuid  # 新增代码+CompactResumeStatus: 把 compact boundary 设为最新 checkpoint；若没有这行代码，中断恢复可能跳过压缩证据。
                    turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="compacted", checkpoint_uuid=compact_entry.uuid, metadata={"compact_boundary": compact_boundary.to_dict()})  # 新增代码+CompactResumeStatus: 在 turn ledger 记录压缩状态；若没有这行代码，状态页不知道本轮发生过 compact。
                    yield emit("compact_completed", {"turn": turn, "boundary": compact_boundary.to_dict()})  # 新增代码+CompactResumeStatus: 向事件流广播 compact 完成；若没有这行代码，终端/SDK/API 无法及时看到压缩动作。
                turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="model_running", checkpoint_uuid=last_transcript_uuid, metadata={"message_count": len(messages), "tool_names": tool_names})  # 新增代码+CompactResumeStatus: 模型请求前更新轮次状态；若没有这行代码，中断恢复不知道是否已经发起模型调用。
                self._write_debug_event(run_id=run_id, event="model_request", payload={"messages": messages, "tool_names": tool_names}, turn=turn)  # 新增代码+Stage15C: 保留旧模型请求日志；若没有这行代码，debug 回放会断开。
                yield emit("model_request_started", {"turn": turn, "message_count": len(messages), "tool_names": tool_names})  # 新增代码+Stage15C: 发出模型请求事件；若没有这行代码，用户无法看到 agent 正在请求模型。
                model_message: ModelMessage | None = None  # 新增代码+Stage15C: 保存完成的模型消息；若没有这行代码，流式事件结束后无法进入工具循环。
                streamed_text_parts: list[str] = []  # 新增代码+Stage15C: 保存没有 completed 事件时的文本增量兜底；若没有这行代码，只有 delta 的模型会丢失回答。
                try:  # 新增代码+ReactiveCompactRuntime: 单独保护模型请求阶段以便识别上下文超限；若没有这行代码，prompt too long 会直接被外层 run_failed 捕获。
                    for model_event in stream_chat_events(self.model, messages, tools):  # 新增代码+Stage15C: 通过统一流式入口消费模型；若没有这行代码，旧模型和新流式模型会走两套逻辑。
                        if model_event.event_type == "text_delta":  # 新增代码+Stage15C: 处理文本增量事件；若没有这行代码，终端 UI 无法实时显示模型输出。
                            streamed_text_parts.append(model_event.text_delta)  # 新增代码+Stage15C: 保存文本增量用于兜底合成；若没有这行代码，只有 delta 的模型没有最终文本。
                            yield emit("model_message_delta", {"turn": turn, "text_delta": model_event.text_delta})  # 新增代码+Stage15C: 发出模型文本增量事件；若没有这行代码，外部观察不到流式输出。
                        if model_event.event_type == "model_message_completed":  # 新增代码+Stage15C: 处理完整模型消息事件；若没有这行代码，工具循环无法拿到最终 tool_calls。
                            model_message = model_event.model_message  # 新增代码+Stage15C: 保存完整模型消息；若没有这行代码，后续无法追加 assistant 消息。
                except Exception as model_error:  # 新增代码+ReactiveCompactRuntime: 捕获模型请求异常并判断是否可恢复；若没有这行代码，超限错误无法自动 compact。
                    if is_prompt_too_long_error(model_error):  # 新增代码+ReactiveCompactRuntime: 只对上下文过长走 reactive compact；若没有这行代码，普通网络或权限错误会被错误重试。
                        reactive_result = try_reactive_compact(messages, session_id=session_id, run_id=run_id, turn_id=current_turn_id, has_attempted=turn in reactive_compact_attempted_turns, artifact_dir=self.workspace / "memory" / "compact_artifacts" / session_id)  # 新增代码+ReactiveCompactRuntime: 尝试生成一次更短上下文；若没有这行代码，prompt too long 没有自动修复路径。
                        if reactive_result.should_retry and reactive_result.boundary is not None:  # 新增代码+ReactiveCompactRuntime: 只有第一次成功压缩才重试；若没有这行代码，失败或第二次错误也可能错误继续。
                            reactive_compact_attempted_turns.add(turn)  # 新增代码+ReactiveCompactRuntime: 标记本 turn 已经重试过；若没有这行代码，持续超限会无限循环。
                            messages[:] = reactive_result.messages  # 新增代码+ReactiveCompactRuntime: 用压缩后的消息替换模型上下文；若没有这行代码，下一次请求仍会超限。
                            compact_entry = transcript_v2_store.append_entry(session_id=session_id, run_id=run_id, turn_id=current_turn_id, event_type="compact_boundary", payload=reactive_result.boundary.to_dict(), parent_uuid=last_transcript_uuid)  # 新增代码+ReactiveCompactRuntime: 把 reactive boundary 写入 transcript v2；若没有这行代码，异常恢复不可审计。
                            last_transcript_uuid = compact_entry.uuid  # 新增代码+ReactiveCompactRuntime: 把 reactive compact 作为最新 checkpoint；若没有这行代码，中断恢复会漏掉修复点。
                            turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="compacted", checkpoint_uuid=compact_entry.uuid, metadata={"compact_boundary": reactive_result.boundary.to_dict(), "transition_reason": reactive_result.transition_reason})  # 新增代码+ReactiveCompactRuntime: 在账本记录 reactive compact；若没有这行代码，状态页不知道模型错误后已修复。
                            yield emit("reactive_compact_retry", {"turn": turn, "turn_id": current_turn_id, "error": str(model_error), "boundary": reactive_result.boundary.to_dict()})  # 新增代码+ReactiveCompactRuntime: 广播即将重试模型请求；若没有这行代码，UI/SDK 看不到自动恢复动作。
                            continue  # 新增代码+ReactiveCompactRuntime: 回到同一 turn 重新请求模型；若没有这行代码，压缩后不会真正重试。
                    raise  # 新增代码+ReactiveCompactRuntime: 非可恢复错误或第二次超限交给外层失败事件；若没有这行代码，真实错误会被吞掉。
                if model_message is None:  # 新增代码+Stage15C: 处理模型只给 delta 没给 completed 的兜底情况；若没有这行代码，后续会访问 None 崩溃。
                    model_message = ModelMessage(text="".join(streamed_text_parts))  # 新增代码+Stage15C: 用文本增量合成最终消息；若没有这行代码，流式文本会丢失。
                model_payload = self._model_message_to_debug_dict(model_message)  # 新增代码+Stage15C: 把模型消息转成可记录字典；若没有这行代码，事件和日志会重复转换逻辑。
                self._write_debug_event(run_id=run_id, event="model_response", payload=model_payload, turn=turn)  # 新增代码+Stage15C: 保留旧模型响应日志；若没有这行代码，debug 回放会缺模型结果。
                model_completed_event = emit("model_message_completed", {"turn": turn, "message": model_payload})  # 修改代码+CompactResumeStatus: 先创建模型完成事件以便 ledger 引用 checkpoint；若没有这行代码，模型结果无法和 turn ledger 对齐。
                yield model_completed_event  # 修改代码+CompactResumeStatus: 发出模型完成事件；若没有这行代码，transcript 无法记录模型结果。
                yield emit("model_response_completed", {"turn": turn, "turn_id": current_turn_id, "message": model_payload})  # 新增代码+StatusSchemaV2: 额外发出 v2 命名的模型完成事件；若没有这行代码，UI/SDK 需要兼容旧 model_message_completed 名称。
                turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="model_completed", checkpoint_uuid=last_transcript_uuid, metadata={"tool_call_count": len(model_message.tool_calls)})  # 新增代码+CompactResumeStatus: 模型完成后更新轮次账本；若没有这行代码，恢复器不知道模型响应已经拿到。
                messages.append(self._assistant_message_to_dict(model_message))  # 新增代码+Stage15C: 把模型消息加入历史；若没有这行代码，下一轮模型看不到上轮 assistant/tool_calls。
                if self._stop_requested():  # 新增代码+Stage15C: 模型后工具前检查取消；若没有这行代码，取消后仍可能执行写文件或命令。
                    turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="interrupted", checkpoint_uuid=last_transcript_uuid, metadata={"reason": "stop_requested_after_model"})  # 新增代码+CompactResumeStatus: 模型后取消时更新 ledger；若没有这行代码，恢复器会误以为还要等模型响应。
                    yield emit("run_completed", {"text": "任务已停止：收到取消请求。", "reason": "stop_requested"})  # 新增代码+Stage15C: 发出取消完成事件；若没有这行代码，事件消费者拿不到取消提示。
                    return  # 新增代码+Stage15C: 停止事件流；若没有这行代码，工具调用会继续发生。
                if not model_message.tool_calls:  # 新增代码+Stage15C: 无工具调用时进入最终回答路径；若没有这行代码，直接回答会被误当成工具循环。
                    retry_message = self._final_answer_retry_message(user_input, model_message.text)  # 新增代码+Stage15C: 保留最终回答格式补救；若没有这行代码，复合任务可能漏掉用户要求标题。
                    can_retry_final_answer = retry_message and final_answer_retry_count < 1 and (max_turns is None or turn + 1 < max_turns)  # 新增代码+Stage15C: 保留单次重试和轮次预算限制；若没有这行代码，可能无限重写。
                    if can_retry_final_answer:  # 新增代码+Stage15C: 如果可以重写最终回答；若没有这行代码，缺标题答案会提前返回。
                        final_answer_retry_count += 1  # 新增代码+Stage15C: 消耗一次重试机会；若没有这行代码，重试次数无法限制。
                        self._write_debug_event(run_id=run_id, event="final_answer_retry", payload={"message": retry_message}, turn=turn)  # 新增代码+Stage15C: 保留重试 debug 日志；若没有这行代码，排查多一次模型调用会困难。
                        yield emit("final_answer_retry", {"turn": turn, "message": retry_message})  # 新增代码+Stage15C: 发出重试事件；若没有这行代码，transcript 无法解释为什么继续下一轮。
                        messages.append({"role": "user", "content": retry_message})  # 新增代码+Stage15C: 把修正请求放回历史；若没有这行代码，模型没有机会补全格式。
                        turn += 1  # 新增代码+Stage15C: 重试计入轮次；若没有这行代码，max_turns 不会生效。
                        continue  # 新增代码+Stage15C: 进入下一轮模型请求；若没有这行代码，会继续提前完成。
                    self._write_debug_event(run_id=run_id, event="final_answer", payload={"text": model_message.text}, turn=turn)  # 新增代码+Stage15C: 保留最终回答 debug 日志；若没有这行代码，旧验收排查会缺最终文本。
                    turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="completed", checkpoint_uuid=last_transcript_uuid, metadata={"final_answer_chars": len(model_message.text)})  # 新增代码+CompactResumeStatus: 最终回答前标记本轮完成；若没有这行代码，恢复器可能重跑已完成最终回答。
                    summary_path = save_session_summary(model_message.text)  # 新增代码+Stage15G: 保存完成会话摘要；若没有这行代码，run_completed 后无法通过 session id 恢复摘要。
                    yield emit("session_saved", {"summary_path": str(summary_path), "session_id": session_id})  # 新增代码+Stage15G: 发出 session_saved 事件；若没有这行代码，事件流消费者不知道 summary 已落盘。
                    yield emit("run_completed", {"text": model_message.text, "turn": turn})  # 新增代码+Stage15C: 发出运行完成事件；若没有这行代码，run() 无法从事件流拿最终回答。
                    return  # 新增代码+Stage15C: 最终回答后结束事件流；若没有这行代码，循环会继续请求模型。
                self.defer_tool_select_until_next_turn = True  # 新增代码+Stage15C: 保留同批 tool_search 延迟生效语义；若没有这行代码，deferred 工具会在同批中错误可见。
                for tool_call in model_message.tool_calls:  # 修改代码+Stage15F: 先按原顺序发出本批工具开始事件；若没有这行代码，并发执行时 UI 无法看到稳定开始序列。
                    tool_payload = self._tool_call_to_debug_dict(tool_call)  # 新增代码+Stage15C: 转换工具调用载荷；若没有这行代码，事件和日志会重复构造字段。
                    session_tool_calls.append(copy.deepcopy(tool_payload))  # 新增代码+Stage15G: 记录工具调用到 session summary；若没有这行代码，resume 摘要看不到工具调用历史。
                    self._write_debug_event(run_id=run_id, event="tool_call", payload=tool_payload, turn=turn)  # 新增代码+Stage15C: 保留工具调用 debug 日志；若没有这行代码，排查模型选了什么工具会困难。
                    yield emit("tool_use_seen", {"turn": turn, "turn_id": current_turn_id, "tool_call": tool_payload})  # 新增代码+StatusSchemaV2: 把工具调用以 v2 事件名暴露给状态生态；若没有这行代码，外部 agent 很难按标准事件过滤工具使用。
                    yield emit("tool_call_started", {"turn": turn, "tool_call": tool_payload})  # 新增代码+Stage15C: 发出工具开始事件；若没有这行代码，UI 无法显示工具执行进度。
                turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="tools_running", checkpoint_uuid=last_transcript_uuid, metadata={"tool_count": len(model_message.tool_calls)})  # 新增代码+CompactResumeStatus: 批量工具执行前更新账本；若没有这行代码，中断恢复不知道工具阶段已经开始。
                tool_outputs = execute_tool_calls_from_orchestrator(self, model_message.tool_calls)  # 新增代码+Stage15F: 通过安全编排器批量执行工具；若没有这行代码，run_events 仍无法并发安全只读工具。
                for tool_call, tool_output in zip(model_message.tool_calls, tool_outputs):  # 修改代码+Stage15F: 按原 tool_call 顺序发出完成事件和回填消息；若没有这行代码，并发结果可能乱序。
                    context_tool_output = self._offload_tool_output_if_needed(tool_call, tool_output)  # 新增代码+Stage15C: 长结果落盘并回填摘要；若没有这行代码，大输出会撑爆上下文。
                    result_payload = {"tool_name": tool_call.name, "call_id": tool_call.call_id, "output": context_tool_output, "raw_output_chars": len(tool_output)}  # 新增代码+Stage15C: 构造工具结果载荷；若没有这行代码，事件和 debug 日志字段会不一致。
                    session_tool_results.append(copy.deepcopy(result_payload))  # 新增代码+Stage15G: 记录工具结果到 session summary；若没有这行代码，resume 摘要缺少外部观察结果。
                    self._write_debug_event(run_id=run_id, event="tool_result", payload=result_payload, turn=turn)  # 新增代码+Stage15C: 保留工具结果 debug 日志；若没有这行代码，旧排查方式无法看到工具输出。
                    tool_completed_event = emit("tool_call_completed", {"turn": turn, **result_payload})  # 修改代码+CompactResumeStatus: 先创建工具完成事件以便 ledger 引用 checkpoint；若没有这行代码，工具结果无法和 turn ledger 对齐。
                    yield tool_completed_event  # 修改代码+CompactResumeStatus: 发出工具完成事件；若没有这行代码，transcript 无法恢复工具结果。
                    yield emit("tool_result_seen", {"turn": turn, "turn_id": current_turn_id, **result_payload})  # 新增代码+StatusSchemaV2: 把工具结果以 v2 事件名暴露给状态生态；若没有这行代码，SDK/API 无法稳定观察工具回灌。
                    turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="tool_result_recorded", checkpoint_uuid=last_transcript_uuid, metadata={"last_tool_name": tool_call.name, "last_tool_call_id": tool_call.call_id})  # 新增代码+CompactResumeStatus: 每个工具完成后更新 checkpoint；若没有这行代码，中断后可能重复执行已完成工具。
                    messages.extend(self._tool_result_messages_to_dicts(tool_call, context_tool_output))  # 修改代码+ComputerUseVisionLoop: 把工具文本和可选截图 image block 一起放回消息历史；如果没有这行代码，Computer Use 观察仍只会把截图路径当文本交给模型。
                    if self._stop_requested():  # 新增代码+Stage15C: 每个工具后检查取消；若没有这行代码，一批工具会在取消后继续执行。
                        self.defer_tool_select_until_next_turn = False  # 新增代码+Stage15C: 停止前关闭延迟 select 标记；若没有这行代码，复用同一 agent 会污染状态。
                        turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="interrupted", checkpoint_uuid=last_transcript_uuid, metadata={"reason": "stop_requested_after_tool"})  # 新增代码+CompactResumeStatus: 工具后取消时更新 ledger；若没有这行代码，恢复器可能重复刚完成的工具。
                        yield emit("run_completed", {"text": "任务已停止：收到取消请求。", "reason": "stop_requested"})  # 新增代码+Stage15C: 发出取消完成事件；若没有这行代码，事件消费者拿不到取消提示。
                        return  # 新增代码+Stage15C: 停止事件流；若没有这行代码，后续工具可能继续执行。
                self.defer_tool_select_until_next_turn = False  # 新增代码+Stage15C: 当前批次工具处理完成后关闭延迟标记；若没有这行代码，后续 select 会被错误延迟。
                self._commit_pending_loaded_tool_names()  # 新增代码+Stage15C: 批次结束后提交 pending select；若没有这行代码，下一轮工具池看不到新工具。
                turn += 1  # 新增代码+Stage15C: 推进轮次；若没有这行代码，循环可能卡在同一轮。
            safety_message = "已经达到最大工具循环次数，为了安全我先停止。请把任务拆小一点再试。"  # 新增代码+Stage15C: 保留安全停止提示；若没有这行代码，超轮次时用户看不到原因。
            self._write_debug_event(run_id=run_id, event="safety_stop", payload={"text": safety_message, "max_turns": max_turns})  # 新增代码+Stage15C: 保留安全停止 debug 日志；若没有这行代码，排查长任务停止原因会困难。
            turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="interrupted", checkpoint_uuid=last_transcript_uuid, metadata={"reason": "max_turns", "max_turns": max_turns})  # 新增代码+CompactResumeStatus: 达到轮次上限时把 turn 标记为可恢复中断；若没有这行代码，恢复器可能误判任务自然完成。
            yield emit("run_completed", {"text": safety_message, "reason": "max_turns", "max_turns": max_turns})  # 新增代码+Stage15C: 把安全停止也作为完成事件返回；若没有这行代码，事件消费者会拿不到停止文本。
        except Exception as error:  # 新增代码+Stage15C: 捕获主循环异常；若没有这行代码，事件流消费者无法收到结构化失败事件。
            failure_text = f"任务失败：{error}"  # 新增代码+Stage15C: 构造可读失败文本；若没有这行代码，事件消费者无法显示异常原因。
            try:  # 新增代码+CompactResumeStatus: 尝试把异常写入 turn ledger；若没有这行代码，失败后恢复器看不到失败 checkpoint。
                turn_ledger.update_status(session_id=session_id, turn_id=current_turn_id, status="failed", checkpoint_uuid=last_transcript_uuid, metadata={"error": str(error), "error_type": type(error).__name__})  # 新增代码+CompactResumeStatus: 保存失败状态和错误类型；若没有这行代码，审计只能靠终端文本猜失败原因。
            except Exception:  # 新增代码+CompactResumeStatus: ledger 写入失败时不覆盖原始异常事件；若没有这行代码，二次失败会遮住真正错误。
                pass  # 新增代码+CompactResumeStatus: 保留原始 run_failed 事件继续输出；若没有这行代码，except 块语法不完整。
            yield emit("run_failed", {"text": failure_text, "error": str(error), "error_type": type(error).__name__})  # 新增代码+Stage15C: 发出失败事件并写 transcript；若没有这行代码，失败无法恢复和审计。
        finally:  # 新增代码+DesktopTaskPolicy：无论正常完成、提前 return、异常失败都恢复桌面任务上下文；如果没有这一行，active 可能泄漏到下一轮普通开发任务。
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

    def _detect_real_chrome_intent(self, user_input: str) -> bool:  # 新增代码+RealChromeWorkflow: 识别用户是否明确要求桌面真实 Chrome；若没有这行代码，工具策略只能依赖模型自觉选对浏览器
        return detect_real_chrome_intent(user_input)  # 修改代码+BrowserSplit: 委托 browser.intent 判断真实 Chrome 意图；若没有这行代码，真实浏览器关键词仍会困在主文件里。

    def _detect_real_browser_information_task(self, user_input: str) -> bool:  # 新增代码+通用真实浏览器Harness: 判断真实浏览器请求是否属于可复用的信息查询任务；若没有这行代码，harness 无法区分普通打开浏览器和查资料类任务
        return detect_real_browser_information_task(user_input)  # 修改代码+BrowserSplit: 委托 browser.intent 判断真实浏览器公开信息查询；若没有这行代码，客户模式复用入口仍会散在主类。

    def _detect_visible_browser_information_task(self, user_input: str) -> bool:  # 新增代码+自然可见浏览器路由: 判断普通自然实时查询是否需要可见浏览器；若没有这行代码，武汉天气攻略 prompt 不会触发可见窗口。
        return detect_visible_browser_information_task(user_input)  # 新增代码+自然可见浏览器路由: 委托 browser.intent 做集中判断；若没有这行代码，意图规则会重新散落到主类。

    def _build_real_browser_task_harness_message(self, user_input: str) -> str:  # 新增代码+通用真实浏览器Harness: 为自然短 prompt 构造可复用真实浏览器任务约束；若没有这行代码，模型只能靠用户长 prompt 才会走完整动作链
        return build_real_browser_task_harness_message(user_input)  # 修改代码+BrowserSplit: 委托 browser.harness 构造真实浏览器任务约束；若没有这行代码，harness 文案仍会把主文件撑大。

    def _build_visible_browser_task_harness_message(self, user_input: str) -> str:  # 新增代码+自然可见浏览器路由: 为普通实时查询构造可见浏览器约束；若没有这行代码，精准 prompt 仍可能只走后台搜索。
        return build_visible_browser_task_harness_message(user_input)  # 新增代码+自然可见浏览器路由: 委托 browser.harness 生成可审计文案；若没有这行代码，主文件会堆入长文本规则。

    def _build_computer_use_full_model_loop_harness_message(self, user_input: str) -> str:  # 新增代码+ModelLoopSemanticPlanner：函数段开始，为 full 模式桌面任务生成极简模型主循环约束；如果没有这段函数，自然语言桌面任务会缺少“由模型选工具”的明确上下文。
        desktop_task_context = getattr(self, "desktop_task_context", {})  # 新增代码+ModelLoopSemanticPlanner：读取 run_events 已计算的桌面任务上下文；如果没有这一行，harness 不知道当前用户输入是否属于桌面任务。
        if not isinstance(desktop_task_context, dict):  # 新增代码+ModelLoopSemanticPlanner：防御异常上下文形状；如果没有这一行，外部注入错误状态可能让 system prompt 构造崩溃。
            return ""  # 新增代码+ModelLoopSemanticPlanner：上下文异常时不注入额外规则；如果没有这一行，普通任务可能被错误污染。
        if not bool(desktop_task_context.get("active", False)):  # 新增代码+ModelLoopSemanticPlanner：只在桌面任务 active 时启用 Computer Use harness；如果没有这一行，所有代码任务都会看到桌面控制规则。
            return ""  # 新增代码+ModelLoopSemanticPlanner：非桌面任务返回空字符串；如果没有这一行，system prompt 会出现无关约束。
        if not bool(desktop_task_context.get("requires_gui_actions", False)):  # 新增代码+ModelLoopSemanticPlanner：只处理确实需要 GUI 动作的任务；如果没有这一行，普通解释类桌面问题也会被误导去控制鼠标。
            return ""  # 新增代码+ModelLoopSemanticPlanner：无需 GUI 的桌面相关问题不注入；如果没有这一行，模型可能过度使用 Computer Use。
        loaded_computer_tools = {"computer_use", "computer_observe", "computer_action"} & set(getattr(self, "loaded_tool_names", set()))  # 新增代码+ModelLoopSemanticPlanner：确认 full 命令已经把 Computer Use 工具放入当前工具池；如果没有这一行，模型会收到规则但看不到可调用工具。
        if not {"computer_use", "computer_observe", "computer_action"}.issubset(loaded_computer_tools):  # 新增代码+ModelLoopSemanticPlanner：三个核心工具不齐时不注入 full harness；如果没有这一行，半加载状态会误导模型调用不存在的工具。
            return ""  # 新增代码+ModelLoopSemanticPlanner：工具不齐时返回空规则；如果没有这一行，错误工具池会被提示词掩盖。
        target_app_hint = str(desktop_task_context.get("target_app_hint", "") or "").strip()  # 新增代码+ModelLoopSemanticPlanner：读取脱敏目标应用提示；如果没有这一行，harness 无法把“画图/mspaint”这类安全线索传给模型。
        canonical_target_app = self._computer_use_full_canonical_target_app_hint(target_app_hint)  # 新增代码+ModelLoopFirstStepLaunch：把“画图/记事本/计算器”等用户友好提示转成模型更容易传对的启动名；如果没有这一行，模型可能把中文应用名原样传给启动器导致失败。
        task_goal = str(desktop_task_context.get("task_goal", "") or "").strip()  # 新增代码+ModelLoopSemanticPlanner：读取脱敏任务目标提示；如果没有这一行，harness 无法提醒模型当前是绘图/打开应用等 GUI 任务。
        return "\n".join([  # 新增代码+ModelLoopSemanticPlanner：拼出短提示词块；如果没有这一行，模型不会获得结构化 Computer Use full 工作方式。
            "Computer Use full 模式已开启。",  # 新增代码+ModelLoopSemanticPlanner：明确告诉模型当前处于 full 模式；如果没有这一行，模型可能不知道用户已经授权工具包。
            "用户自然语言仍在本轮 user message 中，请你在模型主循环里理解任务语义。",  # 新增代码+ModelLoopSemanticPlanner：强调语义理解由模型完成；如果没有这一行，后续维护者可能再次把 prompt 交给 Python planner。
            "本机应用任务第 0 轮只做第一步：如果规范启动应用名不是“未知”且还没有 agent-owned target_window，必须先调用 `computer_action`，action=launch_app，app_name 使用规范启动应用名；不要在第 0 轮规划完整绘图、点击画布或等待截图。",  # 修改代码+ModelLoopFirstStepLaunch：把真实终端失败的第 0 轮长规划收窄成启动绑定并使用规范应用名；如果没有这一行，自然语言“用画图画树”可能再次卡在模型第 0 轮或传错 app_name。
            "先用 `computer_use`/`computer_observe` 观察屏幕和窗口，再用 `computer_use`/`computer_action` 执行一个小步动作，随后继续观察和纠偏。",  # 新增代码+ModelLoopSemanticPlanner：描述 observe-plan-act 闭环；如果没有这一行，模型可能跳过观察直接盲点鼠标。
            "如果用户要求使用某个本机应用且该应用没有明确可用窗口，先调用 `computer_action` 的 `launch_app`，传入 `app_name`，再观察返回的 `target_window`。",  # 新增代码+ModelLoopLaunchAppTool: 告诉模型先打开软件再操作窗口；如果没有这一行，模型可能继续在未打开目标应用时盲目移动鼠标键盘。
            "除非用户明确要求复用已有窗口，否则本机应用任务优先用 `launch_app` 创建 agent-owned 新窗口，不要把用户旧窗口当成自己打开的软件。",  # 新增代码+ModelLoopLaunchAppTool: 要求模型优先创建自有窗口；如果没有这一行，真实验收会被用户预先打开的 Paint 窗口误判成功。
            "本轮目标必须始终以用户原始自然语言为准；如果截图里有旧画布或旧图形，不要把任务漂移成续画、修补或美化旧内容。",  # 新增代码+ComputerUseGoalAnchor: 固定本轮用户目标，避免观察到旧图后改去补旧画；如果没有这一行，画树任务可能像真实验收中那样跑偏成补脸/鼻子。
            "如果目标应用里已有无关旧图，优先选择空白区域、新建空白画布或清空画布，再绘制本轮目标对象。",  # 新增代码+ComputerUseGoalAnchor: 给模型处理残留画布的通用策略；如果没有这一行，旧画布会持续污染视觉规划。
            "桌面任务不要用 `bash`、`read`、`write`、`edit` 生成最终图像或替代 GUI 操作；这些工具只可用于必要诊断。",  # 新增代码+GenericDragPathToolSurface: 阻止模型回到脚本制图绕路；如果没有这一行，真实绘图任务可能被 System.Drawing 之类的离线产物冒充完成。
            "需要连续鼠标轨迹时使用 `computer_action` 的 `drag_path` 和 `points`，不要把绘图任务退化成输入文字说明。",  # 新增代码+GenericDragPathToolSurface: 提醒模型用通用拖拽原语完成绘图或拖动；如果没有这一行，模型可能继续只打字描述图像而不真实画线。
            "完成前至少观察一次结果；最终回答必须包含 computer_use、mspaint 或实际 app_id、screenshot、real_desktop_touched 和 low_level_event_count 摘要。",  # 修改代码+GenericDragPathToolSurface: 要求最终输出带稳定可见验收 token；如果没有这一行，终端只能看到“已完成”而无法机器确认真实触碰桌面。
            "不要调用 `computer_use` 的 `run_prompt` 或 `mode` 来执行整段自然语言任务；那只是旧兼容入口，不是语义规划器。",  # 新增代码+ModelLoopSemanticPlanner：阻止黑盒 prompt 执行；如果没有这一行，模型可能继续绕过主循环。
            f"脱敏目标应用提示：{target_app_hint or '未知'}；规范启动应用名：{canonical_target_app or '未知'}；脱敏任务类型提示：{task_goal or '未知'}。",  # 修改代码+ModelLoopFirstStepLaunch：同时提供用户友好提示和规范启动名；如果没有这一行，模型可能不知道应该把“画图”转换成 mspaint。
        ])  # 新增代码+ModelLoopSemanticPlanner：结束提示词行列表并返回；如果没有这一行，Python 语法不完整。
    # 新增代码+ModelLoopSemanticPlanner：函数段结束，_build_computer_use_full_model_loop_harness_message 到此结束；如果没有这个边界说明，用户不容易看出模型循环 harness 的范围。

    def _computer_use_full_canonical_target_app_hint(self, target_app_hint: str) -> str:  # 新增代码+ModelLoopFirstStepLaunch：函数段开始，把脱敏应用提示转换成稳定启动别名；如果没有这段函数，模型会在“画图”和 mspaint 之间摇摆，作者意图是只规范应用入口而不解析绘图主体。
        normalized_hint = str(target_app_hint or "").strip().lower()  # 新增代码+ModelLoopFirstStepLaunch：清理目标应用提示并统一小写；如果没有这一行，空白和大小写会让别名匹配不稳定。
        if not normalized_hint or normalized_hint == "未知":  # 新增代码+ModelLoopFirstStepLaunch：没有有效应用提示时返回空；如果没有这一行，未知目标可能被误当成可启动应用。
            return ""  # 新增代码+ModelLoopFirstStepLaunch：空提示不生成规范启动名；如果没有这一行，首轮工具收窄会错误要求 launch_app。
        alias_map = {"画图": "mspaint", "画图软件": "mspaint", "paint": "mspaint", "mspaint": "mspaint", "mspaint.exe": "mspaint", "记事本": "notepad", "notepad": "notepad", "notepad.exe": "notepad", "计算器": "calc", "calculator": "calc", "calc": "calc", "calc.exe": "calc"}  # 新增代码+ModelLoopFirstStepLaunch：保存常见安全本机应用别名；如果没有这一行，模型需要自己猜中文应用名和可执行名的对应关系。
        return alias_map.get(normalized_hint, str(target_app_hint or "").strip())  # 新增代码+ModelLoopFirstStepLaunch：优先返回规范别名，未知普通应用保留原提示给通用发现层；如果没有这一行，函数没有返回值。
    # 新增代码+ModelLoopFirstStepLaunch：函数段结束，_computer_use_full_canonical_target_app_hint 到此结束；如果没有这个边界说明，用户不容易看出这里不解析“画树/画猫”等任务主体。

    def _computer_use_full_initial_launch_required(self, turn: int) -> bool:  # 新增代码+ModelLoopFirstStepLaunch：函数段开始，判断当前模型轮次是否必须先让模型选择 launch_app；如果没有这段函数，首轮工具收窄逻辑会散落在 run_events 主循环里。
        if turn != 0:  # 新增代码+ModelLoopFirstStepLaunch：只收窄第 0 轮；如果没有这一行，后续观察、绘图和纠偏轮次会一直看不到观察/动作工具。
            return False  # 新增代码+ModelLoopFirstStepLaunch：非首轮不要求启动；如果没有这一行，任务无法进入完整 observe-plan-act 循环。
        desktop_task_context = getattr(self, "desktop_task_context", {})  # 新增代码+ModelLoopFirstStepLaunch：读取本轮桌面任务上下文；如果没有这一行，函数不知道当前是不是 full 桌面任务。
        if not isinstance(desktop_task_context, dict):  # 新增代码+ModelLoopFirstStepLaunch：防御异常上下文形状；如果没有这一行，坏状态可能让主循环崩溃。
            return False  # 新增代码+ModelLoopFirstStepLaunch：上下文异常时不收窄工具面；如果没有这一行，普通任务可能被误拦。
        if not bool(desktop_task_context.get("active", False)):  # 新增代码+ModelLoopFirstStepLaunch：只对桌面任务启用；如果没有这一行，代码开发任务第 0 轮也可能只剩 computer_action。
            return False  # 新增代码+ModelLoopFirstStepLaunch：非桌面任务保持原工具池；如果没有这一行，agent 的 coding 能力会被破坏。
        if not bool(desktop_task_context.get("requires_gui_actions", False)):  # 新增代码+ModelLoopFirstStepLaunch：只对需要真实 GUI 动作的任务启用；如果没有这一行，桌面解释类问题也会被迫启动应用。
            return False  # 新增代码+ModelLoopFirstStepLaunch：无需 GUI 动作时不收窄；如果没有这一行，普通状态询问可能被误导。
        target_app_hint = str(desktop_task_context.get("target_app_hint", "") or "").strip()  # 新增代码+ModelLoopFirstStepLaunch：读取脱敏目标应用提示；如果没有这一行，无法判断是否有可启动应用。
        if not self._computer_use_full_canonical_target_app_hint(target_app_hint):  # 新增代码+ModelLoopFirstStepLaunch：没有规范启动名时不强制 launch_app；如果没有这一行，开放式坐标任务会被错误要求启动未知软件。
            return False  # 新增代码+ModelLoopFirstStepLaunch：无目标应用时保留完整工具面；如果没有这一行，模型无法处理纯屏幕任务。
        if self._computer_use_has_agent_owned_launch_target():  # 新增代码+ModelLoopFirstStepLaunch：如果已经有 agent-owned 目标窗口就不再要求首轮启动；如果没有这一行，恢复或重入时可能重复打开应用。
            return False  # 新增代码+ModelLoopFirstStepLaunch：已有目标窗口时放开完整工具面；如果没有这一行，后续无法观察和绘制。
        return True  # 新增代码+ModelLoopFirstStepLaunch：满足条件时首轮必须先启动绑定；如果没有这一行，函数永远不会触发收窄。
    # 新增代码+ModelLoopFirstStepLaunch：函数段结束，_computer_use_full_initial_launch_required 到此结束；如果没有这个边界说明，用户不容易看出首轮收窄边界。

    def _scoped_tool_schemas_for_model_turn(self, tools: list[dict[str, Any]], turn: int) -> list[dict[str, Any]]:  # 新增代码+ModelLoopFirstStepLaunch：函数段开始，按当前轮次收窄模型可见工具；如果没有这段函数，模型首轮会继续在大工具面里超时。
        if not self._computer_use_full_initial_launch_required(turn):  # 新增代码+ModelLoopFirstStepLaunch：只有 full 本机应用任务首轮才收窄；如果没有这一行，所有任务都会被错误过滤工具。
            return tools  # 新增代码+ModelLoopFirstStepLaunch：不需要收窄时返回原工具池；如果没有这一行，普通主循环无法继续。
        scoped_tools: list[dict[str, Any]] = []  # 新增代码+ModelLoopFirstStepLaunch：准备保存首轮允许模型看到的工具；如果没有这一行，后续无法构造过滤结果。
        for tool_schema in tools:  # 新增代码+ModelLoopFirstStepLaunch：遍历当前工具池；如果没有这一行，函数无法找到 computer_action schema。
            function_schema = tool_schema.get("function", {}) if isinstance(tool_schema, dict) else {}  # 新增代码+ModelLoopFirstStepLaunch：安全读取 function 层；如果没有这一行，畸形 schema 会让过滤崩溃。
            tool_name = str(function_schema.get("name", "") or "").strip() if isinstance(function_schema, dict) else ""  # 新增代码+ModelLoopFirstStepLaunch：读取工具名；如果没有这一行，无法判断哪个 schema 是动作工具。
            if tool_name == "computer_action":  # 新增代码+ModelLoopFirstStepLaunch：首轮只保留高层动作入口；如果没有这一行，编码工具和观察工具仍会干扰模型决策。
                scoped_tools.append(tool_schema)  # 新增代码+ModelLoopFirstStepLaunch：加入 computer_action schema；如果没有这一行，模型首轮看不到任何可用启动工具。
        return scoped_tools or tools  # 新增代码+ModelLoopFirstStepLaunch：有动作工具则返回收窄工具面，缺失时回退原工具池避免死路；如果没有这一行，函数没有稳定返回。
    # 新增代码+ModelLoopFirstStepLaunch：函数段结束，_scoped_tool_schemas_for_model_turn 到此结束；如果没有这个边界说明，用户不容易看出工具面收窄范围。

    def _maybe_confirm_plan_from_user_input(self, user_input: str) -> None:  # 新增代码+PlanModeGate: 让用户自然语言确认计划后解除副作用闸门；若没有这行代码，计划确认无法从下一轮用户输入进入执行状态
        if not self.plan_mode_state.get("awaiting_confirmation"):  # 新增代码+PlanModeGate: 只有等待确认时才解析确认文本；若没有这行代码，普通“确认一下”会误改计划状态
            return  # 新增代码+PlanModeGate: 非等待确认状态直接退出；若没有这行代码，后续会做无意义字符串匹配
        lowered_input = user_input.lower()  # 新增代码+PlanModeGate: 统一英文大小写以匹配 confirm/approved；若没有这行代码，英文确认大小写会漏判
        confirm_keywords = ["确认", "同意", "按计划", "继续执行", "开始执行", "执行吧", "confirm", "approved", "go ahead"]  # 新增代码+PlanModeGate: 定义明确确认词；若没有这行代码，计划闸门无法知道哪些用户输入算授权
        if not any(keyword in lowered_input for keyword in confirm_keywords):  # 新增代码+PlanModeGate: 没有确认词时继续保持等待；若没有这行代码，任何下一轮输入都可能错误解锁副作用工具
            return  # 新增代码+PlanModeGate: 用户还没确认就直接退出；若没有这行代码，后续会错误修改状态
        self.plan_mode_state["awaiting_confirmation"] = False  # 新增代码+PlanModeGate: 取消等待确认标记；若没有这行代码，副作用工具仍会被计划闸门拦截
        self.plan_mode_state["confirmed"] = True  # 新增代码+PlanModeGate: 记录该计划已被用户确认；若没有这行代码，审计时无法区分未计划和已确认计划
        self.plan_mode_state["confirmed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+PlanModeGate: 保存确认时间；若没有这行代码，后续日志无法说明确认发生在何时
        self._record_observation("plan_confirmed", {"user_input": user_input[:500]})  # 新增代码+PlanModeGate: 把确认事件写入结构化观察；若没有这行代码，Phase 6 审计看不到计划解锁依据

    def _record_observation(self, kind: str, payload: dict[str, Any]) -> None:  # 新增代码+ObservationV1: 统一记录工具、策略、workflow 和结果持久化观察事件；若没有这行代码，Phase 6 审计只能散落在文本日志里
        event = {  # 新增代码+ObservationV1: 构造固定结构的观察事件；若没有这行代码，不同调用点会各自拼不兼容字段
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),  # 新增代码+ObservationV1: 保存事件发生时间；若没有这行代码，后续排查无法判断事件先后
            "kind": kind,  # 新增代码+ObservationV1: 保存事件类型，例如 mcp_call_progress 或 tool_result_offloaded；若没有这行代码，审计方无法按类别过滤
            "payload": copy.deepcopy(payload),  # 新增代码+ObservationV1: 保存事件载荷深拷贝；若没有这行代码，调用方后续修改参数会污染历史观察记录
        }  # 新增代码+ObservationV1: 观察事件字典结束；若没有这行代码，Python 语法不完整
        self.observation_events.append(event)  # 新增代码+ObservationV1: 把事件加入当前 agent 的观察流；若没有这行代码，调用方无法回看结构化事件
        self.observation_events = self.observation_events[-500:]  # 新增代码+ObservationV1: 只保留最近 500 条避免长期运行内存无限增长；若没有这行代码，长会话会不断累积观察对象

    def _safe_tool_artifact_name(self, tool_name: str) -> str:  # 新增代码+ResultPersistence: 把工具名转换成安全文件名片段；若没有这行代码，带斜杠或冒号的工具名可能生成非法路径
        return safe_tool_artifact_name(tool_name)  # 修改代码+ResultStorageSplit: 委托 tools.result_storage 生成安全结果文件名；若没有这行代码，文件名清洗逻辑仍留在主入口

    def _tool_result_inline_limit(self, tool_name: str) -> int:  # 新增代码+ResultPersistence: 计算工具结果可回填模型上下文的最大字符数；若没有这行代码，长输出裁剪策略会散落到 run 循环里
        catalog_tool = self._find_catalog_tool(tool_name)  # 新增代码+ResultPersistence: 读取工具自己的 max_result_size_chars 元数据；若没有这行代码，无法尊重工具目录里的输出大小提示
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
            self._record_observation("tool_result_offloaded", {"tool_name": tool_call.name, "call_id": tool_call.call_id, "artifact_path": artifact_text, "raw_output_chars": len(output), "inline_limit": inline_limit})  # 新增代码+ResultPersistence: 记录完整输出已落盘的审计事件；若没有这行代码，模型上下文只看到摘要时无法追踪完整内容在哪里
        except OSError as error:  # 新增代码+ResultPersistence: 处理文件系统写入失败；若没有这行代码，磁盘权限或路径问题会让 agent 崩溃
            self._record_observation("tool_result_offload_failed", {"tool_name": tool_call.name, "call_id": tool_call.call_id, "error": str(error), "raw_output_chars": len(output)})  # 新增代码+ResultPersistence: 记录落盘失败原因；若没有这行代码，排查只能看到被截断的结果
            return output[:inline_limit] + f"\n\n...[工具结果过长且保存完整输出失败：{error}]..."  # 新增代码+ResultPersistence: 落盘失败时至少返回截断内容和错误；若没有这行代码，模型会丢失全部工具结果
        return summarize_offloaded_output(output, inline_limit=inline_limit, artifact_text=artifact_text)  # 修改代码+ResultStorageSplit: 委托 tools.result_storage 生成长结果摘要；若没有这行代码，摘要格式仍堆在主入口

    # 新增代码+Phase41WindowsImageResults: 函数段开始，_record_computer_use_image_artifacts 把 Computer Use 图片结果登记为当前活跃产物；如果没有这段函数，截图虽然落盘但长任务恢复和会话摘要不知道它仍然重要，作者意图是让 image_result block 和 active_artifacts 配合形成可追踪闭环。
    def _record_computer_use_image_artifacts(self, result_data: dict[str, Any], tool_name: str) -> None:  # 新增代码+Phase41WindowsImageResults: 定义 Computer Use 图片 artifact 登记函数；如果没有这行代码，observe/action 需要重复写收集逻辑。
        try:  # 新增代码+Phase41WindowsImageResults: 优先用包模式导入图片块收集器；如果没有这行代码，脚本入口和包入口无法兼容。
            from learning_agent.computer_use.evidence import collect_image_result_blocks  # 新增代码+Phase41WindowsImageResults: 导入 image_result block 收集器；如果没有这行代码，agent 无法从嵌套结果里找到截图路径。
        except ModuleNotFoundError as error:  # 新增代码+Phase41WindowsImageResults: 兼容 start_oauth_agent.bat 脚本模式下包名前缀不可用；如果没有这行代码，真实终端入口可能导入失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.evidence"}:  # 新增代码+Phase41WindowsImageResults: 只允许目标包路径缺失时 fallback；如果没有这行代码，真实内部错误会被误吞。
                raise  # 新增代码+Phase41WindowsImageResults: 重新抛出非路径类导入错误；如果没有这行代码，排查 evidence bug 会很困难。
            from computer_use.evidence import collect_image_result_blocks  # 新增代码+Phase41WindowsImageResults: 脚本模式导入收集器；如果没有这行代码，bat 入口无法登记截图 artifact。
        image_results = collect_image_result_blocks(result_data)  # 新增代码+Phase41WindowsImageResults: 收集工具结果里的图片块；如果没有这行代码，agent 不知道本次结果包含截图。
        if not image_results:  # 新增代码+Phase41WindowsImageResults: 无图片块时直接返回；如果没有这行代码，普通 Computer Use 结果会产生无意义审计事件。
            return  # 新增代码+Phase41WindowsImageResults: 结束无图分支；如果没有这行代码，后续会遍历空列表浪费处理。
        recorded_paths: list[str] = []  # 新增代码+Phase41WindowsImageResults: 准备保存本次登记的路径；如果没有这行代码，observation 无法记录具体 artifact。
        for image_result in image_results:  # 新增代码+Phase41WindowsImageResults: 遍历每个图片块；如果没有这行代码，多张截图无法全部登记。
            artifact_path = str(image_result.get("artifact_path", "")).strip()  # 新增代码+Phase41WindowsImageResults: 读取并清理 artifact 路径；如果没有这行代码，空白或非字符串路径可能污染 active_artifacts。
            if not artifact_path:  # 新增代码+Phase41WindowsImageResults: 跳过空路径；如果没有这行代码，active_artifacts 可能出现不可打开的空条目。
                continue  # 新增代码+Phase41WindowsImageResults: 继续处理下一张图；如果没有这行代码，空路径会被错误登记。
            if artifact_path not in self.active_artifacts:  # 新增代码+Phase41WindowsImageResults: 避免重复登记同一截图；如果没有这行代码，长会话里相同 artifact 会挤占列表。
                self.active_artifacts.append(artifact_path)  # 新增代码+Phase41WindowsImageResults: 把截图路径加入活跃产物；如果没有这行代码，后续上下文控制找不到该截图。
            recorded_paths.append(artifact_path)  # 新增代码+Phase41WindowsImageResults: 记录本次处理路径用于审计；如果没有这行代码，observation 事件缺少具体文件。
        self.active_artifacts = self.active_artifacts[-50:]  # 新增代码+Phase41WindowsImageResults: 保持活跃产物列表上限；如果没有这行代码，长期 Computer Use 会无限累积截图路径。
        if recorded_paths:  # 新增代码+Phase41WindowsImageResults: 只有确实登记路径才写 observation；如果没有这行代码，空路径结果会制造噪音事件。
            self._record_observation("computer_use_image_result", {"tool_name": tool_name, "image_result_count": len(image_results), "artifact_paths": recorded_paths, "marker": image_results[0].get("marker", "")})  # 新增代码+Phase41WindowsImageResults: 记录图片 artifact 事件；如果没有这行代码，审计无法解释截图为何成为活跃产物。
    # 新增代码+Phase41WindowsImageResults: 函数段结束，_record_computer_use_image_artifacts 到此结束；如果没有这个结束标记，学习者不容易看出图片 artifact 登记边界。

    def _new_debug_run_id(self) -> str:  # 新增代码: 生成单轮请求的调试编号
        timestamp = time.strftime("%Y%m%d_%H%M%S")  # 新增代码: 用当前时间生成易读前缀
        return f"run_{timestamp}_{secrets.token_hex(4)}"  # 新增代码: 加上随机后缀，避免同一秒多次请求重名

    def _new_session_id(self) -> str:  # 新增代码+Stage15C: 生成事件 transcript 会话编号；若没有这行代码，run_events 无法把事件归档到稳定 session 目录。
        timestamp = time.strftime("%Y%m%d_%H%M%S")  # 新增代码+Stage15C: 使用当前时间作为可读前缀；若没有这行代码，用户难以从目录名判断会话时间。
        return f"session_{timestamp}_{secrets.token_hex(4)}"  # 新增代码+Stage15C: 加随机后缀避免同一秒多次运行重名；若没有这行代码，连续运行可能覆盖 transcript。

    def _refresh_mcp_lifecycle_notifications(self) -> None:  # 新增代码+MCPLifecycleV2: 在读取工具目录前消费 MCP list_changed 通知；若没有这行代码，registry 刷新不会传导到 ToolSearch/Tool Pool
        if not self.mcp_tools_enabled:  # 新增代码+MCPLifecycleV2: MCP 未启用时不尝试刷新外部目录；若没有这行代码，用户拒绝或启动失败后仍可能触碰外部 client
            return  # 新增代码+MCPLifecycleV2: 直接跳过刷新；若没有这行代码，后续会访问不可用 registry 状态
        refresh_method = getattr(self.mcp_tool_registry, "refresh_from_notifications", None)  # 新增代码+MCPLifecycleV2: 读取 registry 的生命周期刷新入口并兼容旧测试替身；若没有这行代码，缺少方法的 registry 会崩溃
        if not callable(refresh_method):  # 新增代码+MCPLifecycleV2: 旧 registry 或测试替身不支持通知刷新时跳过；若没有这行代码，兼容性会被破坏
            return  # 新增代码+MCPLifecycleV2: 没有刷新能力就保持当前 catalog；若没有这行代码，普通无 MCP 场景会失败
        try:  # 新增代码+MCPLifecycleV2: 捕获 lifecycle refresh 失败并转成 agent 状态；若没有这行代码，单次通知处理异常会中断工具搜索
            summary = refresh_method()  # 新增代码+MCPLifecycleV2: 消费 pending notifications 并让 registry 必要时重建 tools；若没有这行代码，ToolSearch 仍使用旧工具目录
        except Exception as error:  # 新增代码+MCPLifecycleV2: 处理外部 server 或 registry 刷新异常；若没有这行代码，用户会看到 Python traceback 或 agent 构造外的崩溃
            self.mcp_start_error = f"MCP lifecycle refresh 失败：{error}"  # 新增代码+MCPLifecycleV2: 保存可读失败原因；若没有这行代码，后续 MCP 不可用状态缺少解释
            return  # 新增代码+MCPLifecycleV2: 刷新失败时保留旧 catalog，避免一次通知错误摧毁本轮工具池；若没有这行代码，异常会继续冒泡
        if isinstance(summary, dict) and summary.get("refreshed_tools"):  # 新增代码+MCPLifecycleV2: 只有 tools/list_changed 真的重建 registry 时才清 agent catalog cache；若没有这行代码，每轮工具查询都会丢失 runtime gate 修改
            self._tool_catalog_cache = None  # 新增代码+MCPLifecycleV2: 清掉 AgentTool 目录缓存，让下一行重建读取最新 MCP schema；若没有这行代码，ToolSearch 会继续返回刷新前的旧工具

    def _tool_catalog(self) -> list[AgentTool]:  # 新增代码+ToolArchitectureV2: 返回完整工具目录，包含内置工具以及已启用 MCP 的 deferred 条目；若没有这行代码，agent 只能看到当前池而无法为后续加载保留完整目录
        self._refresh_mcp_lifecycle_notifications()  # 新增代码+MCPLifecycleV2: 先处理 MCP list_changed 再复用或重建 catalog；若没有这行代码，外部 server 动态工具变化不会进入 ToolSearch
        if self._tool_catalog_cache is not None:  # 新增代码+ToolPolicyV2: 如果本 agent 已经构建过 catalog 就复用同一批 AgentTool 对象；若没有这行代码，运行时设置的 skill_gate/deny 调试字段会在下一次查找时丢失
            return list(self._tool_catalog_cache)  # 新增代码+ToolPolicyV2: 返回缓存列表的浅拷贝以保护列表容器；若没有这行代码，调用方可能直接增删内部缓存列表
        catalog = build_builtin_tool_catalog()  # 新增代码+ToolArchitectureV2: 先把所有内置工具包装进 catalog；若没有这行代码，read_file 和 tool_search 等核心能力会从目录消失
        if not self.mcp_tools_enabled:  # 新增代码+ToolArchitectureV2: MCP 未启用、启动失败或被拒绝时停止追加外部工具；若没有这行代码，未授权或不可用的 MCP 工具会泄露进 catalog
            self._tool_catalog_cache = catalog  # 新增代码+ToolPolicyV2: 缓存仅内置工具目录供后续策略判断复用；若没有这行代码，同一 agent 内对 catalog 工具的门禁修改不会稳定保留
            return list(self._tool_catalog_cache)  # 修改代码+ToolPolicyV2: 返回缓存目录的浅拷贝；若没有这行代码，外部代码可能直接替换内部工具列表
        agent_tools_method = getattr(self.mcp_tool_registry, "agent_tools", None)  # 新增代码+ToolArchitectureV2: 读取 registry 的 AgentTool catalog 入口并兼容旧测试替身；若没有这行代码，缺少 agent_tools 的 registry 会让 agent 初始化后的工具查询崩溃
        if callable(agent_tools_method):  # 新增代码+ToolArchitectureV2: 只有 registry 真提供 agent_tools 时才追加 MCP 目录；若没有这行代码，非函数属性会被误调用
            catalog.extend(agent_tools_method())  # 新增代码+ToolArchitectureV2: 把已发现的 MCP AgentTool 条目加入完整 catalog；若没有这行代码，后续加载机制找不到 deferred MCP 工具
        self._tool_catalog_cache = catalog  # 新增代码+ToolPolicyV2: 缓存完整目录对象让 _find_catalog_tool 返回可持续修改的 AgentTool；若没有这行代码，select 前设置 skill_gate 的变更会被新对象覆盖
        return list(self._tool_catalog_cache)  # 修改代码+ToolPolicyV2: 返回完整缓存目录的浅拷贝；若没有这行代码，调用方可能直接增删内部缓存列表

    def _find_catalog_tool(self, tool_name: str) -> AgentTool | None:  # 新增代码+ToolArchitectureV2: 按名称从完整工具目录查找工具；若没有这行代码，select 分支只能重复手写遍历逻辑且容易漏掉 deferred 工具
        requested_name = tool_name.strip()  # 新增代码+ToolArchitectureV2: 清理调用方传入的工具名前后空白；若没有这行代码，select:mcp__x 后面带空格会误报找不到
        if not requested_name:  # 新增代码+ToolArchitectureV2: 防御空工具名请求；若没有这行代码，空字符串会进入 catalog 遍历并返回模糊失败
            return None  # 新增代码+ToolArchitectureV2: 空名称直接表示没有找到；若没有这行代码，调用方无法用统一 None 处理失败
        for tool in self._tool_catalog():  # 新增代码+ToolArchitectureV2: 遍历完整 catalog 而不是当前工具池；若没有这行代码，deferred MCP 工具仍然无法被 select 找到
            if tool.name == requested_name:  # 新增代码+ToolArchitectureV2: 用模型可调用的工具名做精确匹配；若没有这行代码，select 可能错误加载相似但不同的工具
                return tool  # 新增代码+ToolArchitectureV2: 返回命中的 AgentTool 元数据；若没有这行代码，调用方无法知道应加载哪个工具
        return None  # 新增代码+ToolArchitectureV2: 遍历完仍未命中时返回 None；若没有这行代码，未知工具名会导致隐式返回不清晰

    def _is_unloaded_deferred_tool(self, tool_name: str) -> bool:  # 新增代码+ToolArchitectureV2: 判断某个 catalog 工具是否仍处于未加载的 deferred 状态；若没有这行代码，执行层无法复用统一的延迟加载判定
        tool = self._find_catalog_tool(tool_name)  # 新增代码+ToolArchitectureV2: 先用完整 catalog 查找工具元数据；若没有这行代码，隐藏 MCP 工具不会被执行层识别出来
        if tool is None:  # 新增代码+ToolArchitectureV2: 未知工具不按 deferred 处理；若没有这行代码，未知名称会在后续访问属性时报错
            return False  # 新增代码+ToolArchitectureV2: 找不到工具时返回 False 交给原有未知工具逻辑；若没有这行代码，普通未知工具会被误判为延迟工具
        return tool.source == "mcp" and tool.should_defer and tool.name not in self.loaded_tool_names and not tool.always_load  # 修改代码+CapabilityPacks: 只对外部 MCP deferred 工具执行硬拦截；若没有这行代码，现有内置工具单元测试会因模型可见性优化而无法直接验证工具函数

    def _tool_policy_decision(self, tool: AgentTool) -> ToolPolicyDecision:  # 新增代码+ToolPolicyV2: 统一计算某个工具在当前 agent 上下文里的策略决策；若没有这行代码，工具池、搜索和 select 会继续各自手写状态判断
        return pool_decide_tool_policy(tool, tool_policy=self.tool_policy, tool_policy_context=self.tool_policy_context, allowed_tool_names=self.allowed_tool_names, loaded_tool_names=self.loaded_tool_names, real_chrome_blocked=self._real_chrome_request_blocks_independent_browser(tool))  # 修改代码+ToolsPoolSplit: 委托 tools.pool 计算 loaded、真实 Chrome 阻断和策略决策；若没有这行代码，主类会继续复制工具池策略逻辑

    def _real_chrome_request_blocks_independent_browser(self, tool: AgentTool) -> bool:  # 新增代码+RealChromeWorkflow: 判断当前工具是否应被真实 Chrome 需求拦截；若没有这行代码，拦截条件会散落在策略入口里
        return real_chrome_request_blocks_independent_browser(real_chrome_requested=self.real_chrome_requested, real_chrome_connected="real_chrome_connected" in self.tool_policy_context.completed_workflows, visible_browser_launched="visible_browser_launched" in self.tool_policy_context.completed_workflows, server_name=tool.server_name, original_name=tool.original_name)  # 修改代码+VisibleBrowser验收: 委托 browser.intent 判断真实 Chrome 或可见浏览器 workflow 阻断；若没有这行代码，browser_launch_visible 成功后 browser_open 仍会被隐藏。

    @staticmethod  # 新增代码+RealChromeWorkflow: 独立浏览器工具集合不依赖实例状态；若没有这行代码，测试和策略调用会需要多余对象状态
    def _independent_browser_tool_names() -> set[str]:  # 新增代码+RealChromeWorkflow: 列出真实 Chrome 连接前不应直接使用的浏览器工具；若没有这行代码，拦截范围没有统一来源
        return independent_browser_tool_names()  # 修改代码+BrowserSplit: 委托 browser.intent 返回独立浏览器工具集合；若没有这行代码，工具名单仍无法被浏览器层测试复用。

    def _plan_mode_blocks_tool_call(self, tool_call: ToolCall, catalog_tool: AgentTool | None) -> bool:  # 新增代码+PlanModeGate: 判断当前工具调用是否被计划模式副作用闸门拦截；若没有这行代码，执行入口会塞满难维护的条件判断
        if not self.plan_mode_state.get("active") and not self.plan_mode_state.get("awaiting_confirmation"):  # 新增代码+PlanModeGate: 只有计划中或等待确认时才启用闸门；若没有这行代码，普通任务会被错误拦截
            return False  # 新增代码+PlanModeGate: 不在计划闸门状态时直接放行；若没有这行代码，后续副作用判断会误伤正常流程
        if self.plan_mode_state.get("confirmed"):  # 新增代码+PlanModeGate: 用户确认过计划后允许执行；若没有这行代码，确认状态不会真正解锁工具
            return False  # 新增代码+PlanModeGate: 已确认计划不再阻断；若没有这行代码，后续实现阶段无法运行工具
        if tool_call.name in self._plan_mode_safe_tool_names():  # 新增代码+PlanModeGate: 计划相关和只读观察工具允许继续使用；若没有这行代码，模型无法读文件或输出计划
            return False  # 新增代码+PlanModeGate: 安全工具直接放行；若没有这行代码，计划模式会把自身工具也锁死
        return self._tool_call_has_side_effect(tool_call, catalog_tool)  # 新增代码+PlanModeGate: 只拦截真正可能有副作用的工具；若没有这行代码，计划模式会过度阻止无害查询

    @staticmethod  # 新增代码+PlanModeGate: 安全工具集合不依赖实例状态；若没有这行代码，调用方需要创建对象才能读取固定集合
    def _plan_mode_safe_tool_names() -> set[str]:  # 新增代码+PlanModeGate: 返回计划模式期间允许的内置工具名；若没有这行代码，安全例外没有统一来源
        return {  # 新增代码+PlanModeGate: 用 set 保存可快速匹配的工具名；若没有这行代码，后续判断会更慢更乱
            "read_file",  # 新增代码+PlanModeGate: 计划阶段必须允许读取文件证据；若没有这项，模型无法先读后计划
            "todo_read",  # 新增代码+PlanModeGate: 读取任务清单没有副作用；若没有这项，模型无法恢复当前计划上下文
            "tool_search",  # 新增代码+PlanModeGate: 搜索工具目录没有副作用；若没有这项，模型无法发现只读或计划工具
            "list_mcp_resources",  # 新增代码+PlanModeGate: 列外部资源是只读发现动作；若没有这项，MCP 资源计划无法展开
            "read_mcp_resource",  # 新增代码+PlanModeGate: 读取 MCP resource 用于收集证据；若没有这项，计划前上下文会不足
            "list_mcp_prompts",  # 新增代码+PlanModeGate: 列 MCP prompt 是只读发现动作；若没有这项，模型无法发现可用 prompt
            "read_mcp_prompt",  # 新增代码+PlanModeGate: 读取 MCP prompt 用于规划；若没有这项，prompt workflow 无法先审阅
            "listen_mcp_stream",  # 新增代码+PlanModeGate: 监听 stream 用于观察外部状态；若没有这项，长任务诊断信息可能拿不到
            "skill_list",  # 新增代码+PlanModeGate: 列 skill 是只读发现动作；若没有这项，模型无法按流程加载说明
            "skill_load",  # 新增代码+PlanModeGate: 加载 skill 只读取说明书且会更新策略上下文；若没有这项，skill gate 无法在计划阶段准备好
            "ask_user_question",  # 新增代码+PlanModeGate: 澄清问题没有本地副作用；若没有这项，模型无法在计划阶段向用户补信息
            "enter_plan_mode",  # 新增代码+PlanModeGate: 允许重复说明计划入口状态；若没有这项，计划模式工具会被自己锁住
            "exit_plan_mode",  # 新增代码+PlanModeGate: 允许输出待确认计划；若没有这项，模型无法结束计划阶段
            "verify_plan_execution",  # 新增代码+PlanModeGate: 验证计划是审计动作；若没有这项，模型无法收尾计划执行证据
            "lsp_symbols",  # 新增代码+PlanModeGate: 符号读取是只读代码理解；若没有这项，计划前无法快速理解文件结构
            "lsp_definition",  # 新增代码+PlanModeGate: 定义定位是只读代码理解；若没有这项，计划前无法定位修改点
            "lsp_diagnostics",  # 新增代码+PlanModeGate: 语法诊断是只读检查；若没有这项，计划前无法确认当前错误
            "read_background_command",  # 新增代码+PlanModeGate: 读取后台输出是观察动作；若没有这项，模型无法检查已有长任务状态
            "task_output",  # 新增代码+PlanModeGate: 读取子任务输出是观察动作；若没有这项，模型无法汇总已有子任务证据
            "task_list",  # 新增代码+PlanModeGate: 列子任务是观察动作；若没有这项，模型无法查看当前任务状态
            "task_get",  # 新增代码+PlanModeGate: 读取子任务详情是观察动作；若没有这项，模型无法审计子任务边界
        }  # 新增代码+PlanModeGate: 安全工具集合结束；若没有这行代码，Python set 语法不完整

    def _tool_call_has_side_effect(self, tool_call: ToolCall, catalog_tool: AgentTool | None) -> bool:  # 新增代码+PlanModeGate: 统一判断工具是否可能改变文件、进程、浏览器或外部系统；若没有这行代码，副作用判断会在多个分支重复
        side_effect_builtin_tools = {  # 新增代码+PlanModeGate: 列出已知内置副作用工具；若没有这行代码，写文件和命令执行无法被计划闸门识别
            "write",  # 新增代码+极简工具面: write 会修改工作区文件；若没有这项，未确认计划仍可能通过四原子工具写文件
            "edit",  # 新增代码+极简工具面: edit 会修改工作区文件；若没有这项，未确认计划仍可能通过四原子工具做定点替换
            "bash",  # 新增代码+极简工具面: bash 会执行本机命令；若没有这项，未确认计划仍可能通过四原子工具运行副作用命令
            "write_file",  # 新增代码+PlanModeGate: 写文件会修改工作区；若没有这项，未确认计划仍可能写入文件
            "append_memory",  # 新增代码+PlanModeGate: 追加长期记忆会修改持久状态；若没有这项，未确认计划可能污染记忆
            "todo_write",  # 新增代码+PlanModeGate: 写任务清单会修改状态文件；若没有这项，未确认计划可能改动任务状态
            "start_background_command",  # 新增代码+PlanModeGate: 启动后台命令会产生进程副作用；若没有这项，未确认计划可能运行命令
            "stop_background_command",  # 新增代码+PlanModeGate: 停止后台命令会改变进程状态；若没有这项，未确认计划可能终止任务
            "notebook_edit",  # 新增代码+PlanModeGate: 编辑 notebook 会修改文件；若没有这项，未确认计划可能改 notebook
            "task",  # 新增代码+PlanModeGate: 启动子 agent 会产生额外执行流程；若没有这项，未确认计划可能委派副作用
            "task_stop",  # 新增代码+PlanModeGate: 停止子任务会改变任务生命周期；若没有这项，未确认计划可能终止子 agent
            "task_update",  # 新增代码+PlanModeGate: 更新任务元信息会修改管理状态；若没有这项，未确认计划可能改任务记录
            "team_create",  # 新增代码+PlanModeGate: 创建 peer 会修改团队状态；若没有这项，未确认计划可能改变协作结构
            "send_message",  # 新增代码+PlanModeGate: 发送消息会修改 inbox；若没有这项，未确认计划可能产生协作消息
            "ack_peer_message",  # 新增代码+PlanModeGate: 确认消息会改变消息状态；若没有这项，未确认计划可能误标已处理
            "team_delete",  # 新增代码+PlanModeGate: 删除 peer 会修改团队状态；若没有这项，未确认计划可能删除协作记录
            "team_start_task",  # 新增代码+PlanModeGate: 启动团队任务会产生子任务副作用；若没有这项，未确认计划可能后台执行
            "enter_worktree",  # 新增代码+PlanModeGate: 进入隔离上下文改变执行边界状态；若没有这项，未确认计划可能切换工作上下文
            "exit_worktree",  # 新增代码+PlanModeGate: 退出隔离上下文改变执行边界状态；若没有这项，未确认计划可能关闭隔离状态
            "repl",  # 新增代码+PlanModeGate: REPL 会批量执行工具，需要在计划确认后才允许；若没有这项，未确认计划可能通过 REPL 绕过闸门
            "cron_create",  # 新增代码+PlanModeGate: 创建定时记录会修改状态；若没有这项，未确认计划可能登记长期任务
            "cron_delete",  # 新增代码+PlanModeGate: 删除定时记录会修改状态；若没有这项，未确认计划可能删记录
            "monitor",  # 新增代码+PlanModeGate: 监控工具可能登记、删除或写结果；若没有这项，未确认计划可能改变监控状态
        }  # 新增代码+PlanModeGate: 内置副作用集合结束；若没有这行代码，Python set 语法不完整
        if tool_call.name in side_effect_builtin_tools:  # 新增代码+PlanModeGate: 命中已知内置副作用工具就拦截；若没有这行代码，内置写入命令无法被计划保护
            return True  # 新增代码+PlanModeGate: 返回有副作用；若没有这行代码，调用方无法拦截
        if catalog_tool is None:  # 新增代码+PlanModeGate: 未知工具交给后续未知工具分支处理；若没有这行代码，访问 catalog 元数据会报错
            return False  # 新增代码+PlanModeGate: 未知工具暂不在计划闸门判定里处理；若没有这行代码，未知工具可能被错误分类
        if catalog_tool.source == "mcp" and not catalog_tool.is_read_only:  # 新增代码+PlanModeGate: MCP 非只读工具默认视为外部副作用；若没有这行代码，外部写入、浏览器和网络操作可能绕过计划确认
            return True  # 新增代码+PlanModeGate: 返回有副作用；若没有这行代码，外部工具会继续执行
        return catalog_tool.is_destructive or catalog_tool.is_open_world  # 新增代码+PlanModeGate: 破坏性或开放世界工具也按副作用处理；若没有这行代码，高风险 MCP metadata 不会影响计划闸门

    def _tool_denial_key(self, tool_call: ToolCall) -> str:  # 新增代码+ToolPolicyV2: 为 MCP 工具调用生成稳定拒绝记忆 key；若没有这行代码，无法按同一工具和参数去重用户拒绝
        safe_arguments = json.dumps(tool_call.arguments, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+ToolPolicyV2: 把清洗后参数转成排序 JSON；若没有这行代码，相同参数不同顺序会被误当成不同请求
        return f"{tool_call.name}:{safe_arguments}"  # 新增代码+ToolPolicyV2: 拼接工具名和参数 JSON 作为唯一指纹；若没有这行代码，不同工具的相同参数可能互相污染拒绝记录

    def _commit_pending_loaded_tool_names(self) -> None:  # 新增代码+ToolPolicyV2: 把本批 tool_calls 中延迟生效的 select 结果合并到 loaded 集合；若没有这行代码，pending 工具不会进入下一轮工具池
        if not self.pending_loaded_tool_names:  # 新增代码+ToolPolicyV2: 没有待合并工具时直接返回；若没有这行代码，每轮都会做无意义集合更新
            return  # 新增代码+ToolPolicyV2: 空 pending 不需要处理；若没有这行代码，函数会继续执行但没有实际工作
        self.loaded_tool_names.update(self.pending_loaded_tool_names)  # 新增代码+ToolPolicyV2: 批次结束后才让 select 工具正式 loaded；若没有这行代码，下一轮模型 schema 仍看不到已选择工具
        self.pending_loaded_tool_names.clear()  # 新增代码+ToolPolicyV2: 清空 pending 避免下一批重复合并旧工具；若没有这行代码，状态会残留并增加排查难度

    def _current_tool_pool(self) -> list[AgentTool]:  # 新增代码+ToolArchitectureV2: 返回当前真正暴露给模型的工具池；若没有这行代码，deferred 工具无法被默认隐藏
        return pool_current_tool_pool(self._tool_catalog(), self._tool_policy_decision)  # 修改代码+ToolsPoolSplit: 委托 tools.pool 从完整目录过滤当前可见工具；若没有这行代码，工具池过滤逻辑仍堆在 LearningAgent 大类

    def _available_tool_schemas(self) -> list[dict[str, Any]]:  # 修改代码+ToolArchitectureV2: 返回当前工具池对应的模型 schema；若没有这行代码，后续 MCP 工具无法按加载状态控制可见性
        all_tool_schemas = pool_available_tool_schemas(self._current_tool_pool())  # 修改代码+ToolsPoolSplit: 委托 tools.pool 把当前工具池转成模型 schema；若没有这行代码，schema 映射逻辑仍散在主类
        return self._filter_allowed_tool_schemas(all_tool_schemas)  # 修改代码+ToolsPoolSplit: 在当前工具池基础上继续应用子 agent 白名单；若没有这行代码，allowed_tools 参数不会真正限制模型可见工具

    def _filter_allowed_tool_schemas(self, tool_schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:  # 新增代码+TaskAgent: 根据 allowed_tool_names 过滤工具 schema；若省略: 子 agent 无法执行工具白名单策略
        return pool_filter_allowed_tool_schemas(tool_schemas, self.allowed_tool_names)  # 修改代码+ToolsPoolSplit: 委托 tools.pool 执行 allowed_tools 白名单过滤；若没有这行代码，子 agent 工具边界逻辑仍散在主类

    def _tool_schema_names(self, tools: list[dict[str, Any]] | None = None) -> list[str]:  # 修改代码: 允许传入指定工具列表并保留默认动态列表；若省略参数能力: 日志无法准确显示某一轮真实工具集合
        selected_tools = tools if tools is not None else self._available_tool_schemas()  # 新增代码: 优先使用调用方指定工具列表，否则读取本轮可用工具；若省略: 旧调用和动态工具调用无法同时兼容
        return pool_tool_schema_names(selected_tools)  # 修改代码+ToolsPoolSplit: 委托 tools.pool 从 schema 提取工具名；若没有这行代码，日志和测试解析逻辑仍留在主类

    def _model_message_to_debug_dict(self, model_message: ModelMessage) -> dict[str, Any]:  # 新增代码: 把 ModelMessage 转成可写入 JSON 的调试字典
        return {  # 新增代码: 返回结构化调试数据
            "decision_note": model_message.decision_note,  # 新增代码: 记录模型给人看的决策说明，帮助学习工具选择原因
            "text": model_message.text,  # 新增代码: 记录模型文本回答
            "tool_calls": [self._tool_call_to_debug_dict(call) for call in model_message.tool_calls],  # 新增代码: 记录模型请求的工具调用数组
        }  # 新增代码: 调试字典结束

    def _tool_call_to_debug_dict(self, tool_call: ToolCall) -> dict[str, Any]:  # 新增代码: 把 ToolCall 转成可写入 JSON 的调试字典
        return {  # 新增代码: 返回工具调用调试数据
            "tool_name": tool_call.name,  # 新增代码: 记录工具名称
            "arguments": tool_call.arguments,  # 新增代码: 记录模型传入的工具参数
            "call_id": tool_call.call_id,  # 新增代码: 记录工具调用 id，便于和 tool_result 对应
        }  # 新增代码: 工具调用调试字典结束

    def _write_debug_event(self, run_id: str, event: str, payload: dict[str, Any], turn: int | None = None) -> None:  # 新增代码: 追加写入一条 JSONL 调试事件
        if not self.debug_enabled:  # 新增代码: 如果用户关闭了调试日志
            return  # 新增代码: 直接返回，不写任何文件
        record = build_debug_event_record(run_id=run_id, event=event, payload=payload, turn=turn)  # 修改代码+ObservabilitySplit: 委托观测层构造 JSONL 记录；若没有这行代码，主类仍要维护调试日志字段结构。
        try:  # 新增代码: 捕获日志写入失败，避免调试功能影响 agent 主流程
            append_debug_event_record(self.debug_log_path, record)  # 修改代码+ObservabilitySplit: 委托观测层追加写入 JSONL；若没有这行代码，日志目录和文件写入细节会继续堆在主类。
        except OSError:  # 新增代码: 如果磁盘、权限或路径导致日志无法写入
            return  # 新增代码: 静默跳过日志，保证 agent 仍然能回答用户
        self._write_readable_debug_event(record)  # 新增代码: 同步写入 Markdown 可读日志，方便初学者直接看懂流程

    def _write_readable_debug_event(self, record: dict[str, Any]) -> None:  # 新增代码: 把一条结构化事件转换并写入 Markdown 日志
        readable_text = self._format_readable_debug_event(record)  # 新增代码: 把 JSONL 事件格式化成适合人看的 Markdown 片段
        if not readable_text:  # 新增代码: 如果某类事件暂时不需要写入可读日志
            return  # 新增代码: 直接跳过，不影响主流程
        try:  # 新增代码: 捕获 Markdown 写入失败，避免日志功能影响 agent 回答
            self.debug_readable_log_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码: 确保 debug_logs 文件夹存在
            if record.get("event") == "user_input":  # 新增代码: 每轮用户输入开始时，重置 latest 文件为本轮专用视图
                self.debug_latest_run_path.write_text("", encoding="utf-8")  # 新增代码: 清空 latest_run_readable.md，只保留最新一轮流程
            with self.debug_readable_log_path.open("a", encoding="utf-8") as file:  # 新增代码: 追加打开总可读日志，保留历史所有轮次
                file.write(readable_text)  # 新增代码: 写入当前事件对应的 Markdown 片段
            with self.debug_latest_run_path.open("a", encoding="utf-8") as file:  # 新增代码: 追加打开 latest 日志，展示当前最新一轮
                file.write(readable_text)  # 新增代码: 写入当前事件对应的 Markdown 片段
        except OSError:  # 新增代码: 如果路径、权限或磁盘导致 Markdown 日志无法写入
            return  # 新增代码: 静默跳过，保证 agent 主流程继续

    def _format_readable_debug_event(self, record: dict[str, Any]) -> str:  # 新增代码: 把单个调试事件转成中文 Markdown 片段
        event = str(record.get("event", ""))  # 新增代码: 读取事件类型，例如 user_input/tool_call/final_answer
        time_text = str(record.get("time", ""))  # 新增代码: 读取事件时间，显示给人看
        run_id = str(record.get("run_id", ""))  # 新增代码: 读取本轮运行编号，方便和 JSONL 对照
        turn = record.get("turn")  # 新增代码: 读取模型调用轮次，没有轮次时为 None
        payload = record.get("payload", {})  # 新增代码: 读取事件主体内容
        if not isinstance(payload, dict):  # 新增代码: 如果 payload 不是字典
            payload = {"value": payload}  # 新增代码: 包成字典，保证后续格式化逻辑稳定
        if event == "user_input":  # 新增代码: 用户输入事件是一轮可读日志的开头
            return self._format_readable_user_input(time_text=time_text, run_id=run_id, payload=payload)  # 新增代码: 返回运行标题和用户输入区块
        if event == "initial_messages":  # 新增代码: 初始上下文事件包含系统提示词、记忆和工具列表
            return self._format_readable_initial_messages(payload=payload)  # 新增代码: 返回系统/记忆/工具区块
        if event == "model_request":  # 新增代码: 模型请求事件用于标记第几轮模型调用开始
            return self._format_readable_model_request(turn=turn, payload=payload)  # 新增代码: 返回模型调用轮次摘要
        if event == "model_response":  # 新增代码: 模型响应事件包含文本或工具调用计划
            return self._format_readable_model_response(turn=turn, payload=payload)  # 新增代码: 返回模型输出区块
        if event == "tool_call":  # 新增代码: 工具调用事件表示模型选择了具体工具
            return self._format_readable_tool_call(turn=turn, payload=payload)  # 新增代码: 返回工具名和参数区块
        if event == "tool_result":  # 新增代码: 工具结果事件表示 Python 工具层执行完成
            return self._format_readable_tool_result(payload=payload)  # 新增代码: 返回工具结果区块
        if event == "final_answer":  # 新增代码: 最终回答事件表示本轮 agent 已经结束
            return self._format_readable_final_answer(payload=payload)  # 新增代码: 返回最终回答区块
        if event == "safety_stop":  # 新增代码: 安全停止事件表示达到最大循环次数
            return self._format_readable_safety_stop(payload=payload)  # 新增代码: 返回安全停止区块
        return ""  # 新增代码: 未知事件暂时不写入 Markdown，避免干扰阅读

    def _format_readable_user_input(self, time_text: str, run_id: str, payload: dict[str, Any]) -> str:  # 新增代码: 格式化一轮运行开头和用户输入
        return (  # 新增代码: 返回 Markdown 标题、运行信息和用户输入代码块
            f"# Learning Agent 调试记录\n\n"  # 新增代码: 一级标题，记事本里也容易定位一轮开始
            f"运行时间：{time_text}\n\n"  # 新增代码: 显示本轮开始时间
            f"运行编号：`{run_id}`\n\n"  # 新增代码: 显示 run_id，便于回到 JSONL 精确排查
            "## 用户输入\n\n"  # 新增代码: 用户输入区块标题
            f"{self._markdown_code_block('text', str(payload.get('text', '')))}"  # 新增代码: 用代码块展示原始用户输入，避免长文本挤成一行
        )  # 新增代码: Markdown 片段结束

    def _format_readable_initial_messages(self, payload: dict[str, Any]) -> str:  # 新增代码: 格式化系统提示词、长期记忆上下文和工具列表
        messages = payload.get("messages", [])  # 新增代码: 取出初始 messages
        tool_names = payload.get("tool_names", [])  # 新增代码: 取出工具名列表
        system_content = ""  # 新增代码: 准备保存系统提示词内容
        user_content = ""  # 新增代码: 准备保存本轮用户消息内容
        if isinstance(messages, list):  # 新增代码: 确认 messages 是列表
            for message in messages:  # 新增代码: 遍历初始 messages
                if not isinstance(message, dict):  # 新增代码: 跳过非字典消息
                    continue  # 新增代码: 继续检查下一条
                if message.get("role") == "system":  # 新增代码: 找到 system 消息
                    system_content = str(message.get("content", ""))  # 新增代码: 保存系统提示词和 memory 内容
                if message.get("role") == "user":  # 新增代码: 找到 user 消息
                    user_content = str(message.get("content", ""))  # 新增代码: 保存本轮用户消息
        tools_text = self._format_tool_names(tool_names)  # 新增代码: 把工具名列表转成 Markdown 列表
        return (  # 新增代码: 返回可读上下文区块
            "## 加载的系统提示词和记忆上下文\n\n"  # 新增代码: 标明这里是模型看到的系统规则和 memory
            f"{self._markdown_code_block('text', system_content)}"  # 新增代码: 展示系统提示词和长期记忆内容
            "## 本轮用户消息\n\n"  # 新增代码: 标明这里是模型看到的用户消息
            f"{self._markdown_code_block('text', user_content)}"  # 新增代码: 展示用户消息
            "## 可用工具\n\n"  # 新增代码: 标明这里是本轮模型可选择的工具
            f"{tools_text}\n"  # 新增代码: 展示工具名列表
        )  # 新增代码: Markdown 片段结束

    def _format_readable_model_request(self, turn: Any, payload: dict[str, Any]) -> str:  # 新增代码: 格式化模型调用前的摘要
        messages = payload.get("messages", [])  # 新增代码: 取出本轮发送给模型的 messages
        message_count = len(messages) if isinstance(messages, list) else 0  # 新增代码: 统计消息数量，帮助理解上下文随工具调用增加
        tool_names = payload.get("tool_names", [])  # 新增代码: 取出工具名列表
        return (  # 新增代码: 返回模型调用轮次摘要
            f"## 模型调用：第 {turn} 轮\n\n"  # 新增代码: 标明这是第几轮模型调用
            f"发送给模型的消息数量：{message_count}\n\n"  # 新增代码: 显示 messages 数量，工具调用后通常会增加
            f"本轮可用工具：{', '.join(str(name) for name in tool_names) if isinstance(tool_names, list) else ''}\n\n"  # 新增代码: 显示本轮可用工具名称
        )  # 新增代码: Markdown 片段结束

    def _format_readable_model_response(self, turn: Any, payload: dict[str, Any]) -> str:  # 新增代码: 格式化模型返回的文本和工具计划
        decision_note = str(payload.get("decision_note", ""))  # 新增代码: 取出模型给人看的决策说明，用来解释为什么回答或调用工具
        decision_section = self._format_readable_decision_note(decision_note)  # 新增代码: 把决策说明转成 Markdown 区块，空内容时返回空字符串
        text = str(payload.get("text", ""))  # 新增代码: 取出模型文本
        tool_calls = payload.get("tool_calls", [])  # 新增代码: 取出模型请求的工具调用列表
        if isinstance(tool_calls, list) and tool_calls:  # 新增代码: 如果模型请求了工具
            return (  # 新增代码: 返回包含工具计划的模型响应区块
                f"## 模型返回：第 {turn} 轮\n\n"  # 新增代码: 标明模型响应轮次
                f"{decision_section}"  # 新增代码: 展示模型决策说明，帮助用户理解为什么调用工具
                "模型文本：\n\n"  # 新增代码: 标明下面是模型文本
                f"{self._markdown_code_block('text', text or '(空，模型本轮主要是在请求工具)')}"  # 新增代码: 展示模型文本，空文本给出解释
                "模型请求工具：\n\n"  # 新增代码: 标明下面是工具调用计划
                f"{self._markdown_code_block('json', self._json_for_readable(tool_calls))}"  # 新增代码: 用格式化 JSON 展示工具调用数组
            )  # 新增代码: Markdown 片段结束
        return (  # 新增代码: 如果没有工具调用，返回直接回答区块
            f"## 模型返回：第 {turn} 轮\n\n"  # 新增代码: 标明模型响应轮次
            f"{decision_section}"  # 新增代码: 展示模型决策说明，帮助用户理解为什么直接回答
            "模型文本：\n\n"  # 新增代码: 标明下面是模型文本
            f"{self._markdown_code_block('text', text)}"  # 新增代码: 展示模型文本
            "是否请求工具：没有请求工具。\n\n"  # 新增代码: 明确告诉用户本轮没有工具调用
        )  # 新增代码: Markdown 片段结束

    def _format_readable_decision_note(self, decision_note: str) -> str:  # 新增代码: 把模型决策说明格式化为 Markdown 区块
        if not decision_note.strip():  # 新增代码: 如果模型没有提供决策说明
            return ""  # 新增代码: 不显示空区块，避免日志噪音
        return (  # 新增代码: 返回决策说明区块
            "## 模型决策说明\n\n"  # 新增代码: 标明这是模型给人看的行动原因，不是隐藏思维链
            f"{self._markdown_code_block('text', decision_note)}"  # 新增代码: 用代码块展示说明，避免长句挤成一行
        )  # 新增代码: Markdown 片段结束

    def _format_readable_tool_call(self, turn: Any, payload: dict[str, Any]) -> str:  # 新增代码: 格式化工具调用请求
        tool_name = str(payload.get("tool_name", ""))  # 新增代码: 读取工具名
        call_id = str(payload.get("call_id", ""))  # 新增代码: 读取工具调用 id
        arguments = payload.get("arguments", {})  # 新增代码: 读取工具参数
        return (  # 新增代码: 返回工具调用区块
            f"## 工具调用：第 {turn} 轮\n\n"  # 新增代码: 标明工具调用发生在哪轮模型调用之后
            f"工具名：`{tool_name}`\n\n"  # 新增代码: 显示模型选择的工具
            f"调用编号：`{call_id}`\n\n"  # 新增代码: 显示 call_id，便于和工具结果对应
            "参数：\n\n"  # 新增代码: 标明下面是工具参数
            f"{self._markdown_code_block('json', self._json_for_readable(arguments))}"  # 新增代码: 用格式化 JSON 展示参数
        )  # 新增代码: Markdown 片段结束

    def _format_readable_tool_result(self, payload: dict[str, Any]) -> str:  # 新增代码: 格式化工具执行结果
        tool_name = str(payload.get("tool_name", ""))  # 新增代码: 读取工具名
        call_id = str(payload.get("call_id", ""))  # 新增代码: 读取工具调用 id
        output = str(payload.get("output", ""))  # 新增代码: 读取工具执行结果
        return (  # 新增代码: 返回工具结果区块
            "## 工具执行结果\n\n"  # 新增代码: 标明工具层已经执行完成
            f"工具名：`{tool_name}`\n\n"  # 新增代码: 显示工具名
            f"调用编号：`{call_id}`\n\n"  # 新增代码: 显示 call_id，便于对应前面的工具调用
            "结果：\n\n"  # 新增代码: 标明下面是工具返回给模型看的文本
            f"{self._markdown_code_block('text', output)}"  # 新增代码: 用代码块展示工具结果
        )  # 新增代码: Markdown 片段结束

    def _format_readable_final_answer(self, payload: dict[str, Any]) -> str:  # 新增代码: 格式化最终回答
        return (  # 新增代码: 返回最终回答区块
            "## 最终回答\n\n"  # 新增代码: 标明本轮 agent 已经完成
            f"{self._markdown_code_block('text', str(payload.get('text', '')))}"  # 新增代码: 展示最终返回给用户的文本
            "---\n\n"  # 新增代码: 用分隔线把不同运行隔开，方便长期日志阅读
        )  # 新增代码: Markdown 片段结束

    def _format_readable_safety_stop(self, payload: dict[str, Any]) -> str:  # 新增代码: 格式化安全停止结果
        return (  # 新增代码: 返回安全停止区块
            "## 安全停止\n\n"  # 新增代码: 标明 agent 因循环上限停止
            f"{self._markdown_code_block('text', str(payload.get('text', '')))}"  # 新增代码: 展示安全停止提示
            "---\n\n"  # 新增代码: 用分隔线结束本轮日志
        )  # 新增代码: Markdown 片段结束

    def _format_tool_names(self, tool_names: Any) -> str:  # 新增代码: 把工具名列表格式化为 Markdown 列表
        if not isinstance(tool_names, list) or not tool_names:  # 新增代码: 如果工具名不是列表或为空
            return "- 暂无工具\n"  # 新增代码: 返回空工具提示
        return "".join(f"- `{name}`\n" for name in tool_names)  # 新增代码: 每个工具名一行，方便记事本阅读

    def _json_for_readable(self, value: Any) -> str:  # 新增代码: 把任意值格式化为缩进 JSON 字符串
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)  # 新增代码: 使用中文不转义和缩进，提高可读性

    def _markdown_code_block(self, language: str, text: str) -> str:  # 新增代码: 生成 Markdown 代码块，避免长文本挤在一行
        return f"````{language}\n{text}\n````\n\n"  # 新增代码: 使用四反引号，降低内容里出现三反引号时破坏格式的概率

    def _build_initial_messages(self, user_input: str) -> list[dict[str, Any]]:  # 作用: 构造发给模型的初始 messages
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
        real_browser_task_harness = self._build_real_browser_task_harness_message(user_input)  # 新增代码+通用真实浏览器Harness: 根据用户短 prompt 生成可选真实浏览器查询约束；若没有这行代码，自然需求不会自动获得 Google 拟人搜索路线
        if real_browser_task_harness:  # 新增代码+通用真实浏览器Harness: 只有检测到真实浏览器查询任务时才拼接；若没有这行代码，所有任务都会被浏览器 harness 污染
            system_prompt = f"{system_prompt}\n\n{real_browser_task_harness}"  # 新增代码+通用真实浏览器Harness: 把 harness 拼进首条 system 消息以保持两条 messages 结构稳定；若没有这行代码，模型看不到新增约束
        visible_browser_task_harness = self._build_visible_browser_task_harness_message(user_input)  # 新增代码+自然可见浏览器路由: 根据普通实时查询生成可见浏览器约束；若没有这行代码，武汉天气攻略 prompt 看不到可见窗口要求。
        if visible_browser_task_harness:  # 新增代码+自然可见浏览器路由: 只有目标查询才拼接；若没有这行代码，稳定知识和代码任务也会被浏览器规则污染。
            system_prompt = f"{system_prompt}\n\n{visible_browser_task_harness}"  # 新增代码+自然可见浏览器路由: 把可见浏览器 harness 加入系统提示；若没有这行代码，模型仍可能选择后台搜索。
        computer_use_full_harness = self._build_computer_use_full_model_loop_harness_message(user_input)  # 新增代码+ModelLoopSemanticPlanner：根据 full 模式和桌面任务上下文生成模型循环约束；如果没有这一行，模型看不到“自己用 observe/action 规划”的明确规则。
        if computer_use_full_harness:  # 新增代码+ModelLoopSemanticPlanner：只有 full 工具包和桌面任务都满足时才拼接；如果没有这一行，普通任务会被桌面控制规则污染。
            system_prompt = f"{system_prompt}\n\n{computer_use_full_harness}"  # 新增代码+ModelLoopSemanticPlanner：把 Computer Use full harness 加入系统提示；如果没有这一行，语义规划仍可能漂回 Python 兼容入口。
        return [  # 作用: 返回 OpenAI-compatible messages
            {"role": "system", "content": system_prompt},  # 作用: 第一条是系统消息
            {"role": "user", "content": user_input},  # 作用: 第二条是用户本轮输入
        ]  # 作用: messages 列表结束

    def _read_static_prompt(self) -> str:  # 新增代码+PromptFiles: 读取 staticprompt.md 并渲染工作区占位符；若没有这行代码，静态提示词文件不会真正接管系统提示词
        return read_static_prompt(self.static_prompt_path, workspace=self.workspace, current_date=get_local_iso_date())  # 修改代码+PromptsSplit: 委托 prompts.static_prompt 统一读取、兜底和占位符渲染；若没有这行代码，主文件会继续重复保存 staticprompt 细节。

    def _fallback_static_prompt(self, reason: str) -> str:  # 新增代码+PromptFiles: 构造静态提示词缺失时的最小兜底；若没有这行代码，坏文件会直接打断 agent
        return fallback_static_prompt(reason, workspace=self.workspace, current_date=get_local_iso_date())  # 修改代码+PromptsSplit: 委托 prompts.static_prompt 生成最小安全兜底；若没有这行代码，兜底提示词会继续复制在主类里。

    def _resolve_static_prompt_path(self) -> Path:  # 新增代码+PromptFiles: 统一解析 staticprompt.md 的加载路径；若没有这行代码，工作区覆盖和包内默认路径会散落在多个地方
        return resolve_static_prompt_path(self.workspace)  # 修改代码+PromptsSplit: 委托 prompts.static_prompt 统一解析工作区覆盖和包内默认路径；若没有这行代码，路径规则会继续分散。

    def _resolve_dynamic_prompt_path(self) -> Path:  # 新增代码+PromptFiles: 统一解析 dynamicprompt.md 的按需加载路径；若没有这行代码，动态规则迁移后没有可审计入口
        return resolve_dynamic_prompt_path(self.workspace)  # 修改代码+PromptsSplit: 委托 prompts.dynamic_prompt 统一解析 dynamicprompt 路径；若没有这行代码，动态规则路径仍留在主文件。

    def _read_prompt_context_file(self, file_path: Path, max_chars: int) -> str:  # 新增代码+PromptSurfaceV2: 读取单个上下文文件并控制长度；若没有这行代码，三件套读取会重复且容易撑爆上下文
        if not file_path.exists():  # 新增代码+PromptSurfaceV2: 检查文件是否存在；若没有这行代码，缺少某个上下文文件会抛异常
            return f"{file_path.name} 不存在。"  # 新增代码+PromptSurfaceV2: 返回可读缺失说明；若没有这行代码，模型不知道具体少了哪个文件
        if file_path.is_dir():  # 新增代码+PromptSurfaceV2: 防御同名路径是目录；若没有这行代码，read_text 读取目录会崩溃
            return f"{file_path.name} 是目录，无法读取。"  # 新增代码+PromptSurfaceV2: 返回可读目录错误；若没有这行代码，用户难以理解加载失败原因
        text = file_path.read_text(encoding="utf-8", errors="replace")  # 新增代码+PromptSurfaceV2: 用 UTF-8 读取上下文文件；若没有这行代码，中文项目记忆无法进入 system prompt
        if len(text) <= max_chars:  # 新增代码+PromptSurfaceV2: 短文件可以完整加载；若没有这行代码，小上下文也会被不必要截断
            return text if text.strip() else f"{file_path.name} 当前为空。"  # 新增代码+PromptSurfaceV2: 返回原文或空文件说明；若没有这行代码，空文件会变成难以察觉的空区块
        head_chars = max_chars // 2  # 新增代码+PromptSurfaceV2: 计算首部保留长度；若没有这行代码，长文件压缩无法保留开头背景
        tail_chars = max_chars - head_chars  # 新增代码+PromptSurfaceV2: 计算尾部保留长度；若没有这行代码，长文件压缩无法保留最新记录
        return text[:head_chars] + "\n...[项目上下文过长，已保留开头和末尾]...\n" + text[-tail_chars:]  # 新增代码+PromptSurfaceV2: 返回首尾摘要；若没有这行代码，长上下文要么撑爆 prompt 要么完全丢失最新进度

    def _assistant_message_to_dict(self, model_message: ModelMessage) -> dict[str, Any]:  # 作用: 把内部模型消息转成 OpenAI 消息字典
        message: dict[str, Any] = {"role": "assistant", "content": model_message.text or None}  # 作用: 先放入 assistant 文本
        if model_message.tool_calls:  # 作用: 如果模型请求了工具
            message["tool_calls"] = [self._tool_call_to_openai_dict(call) for call in model_message.tool_calls]  # 作用: 转成 OpenAI tool_calls 格式
        return message  # 作用: 返回消息字典

    def _tool_call_to_openai_dict(self, tool_call: ToolCall) -> dict[str, Any]:  # 作用: 把 ToolCall 转成 OpenAI 工具调用格式
        return {  # 作用: 返回工具调用字典
            "id": tool_call.call_id,  # 作用: 保存工具调用 id
            "type": "function",  # 作用: 工具调用类型固定为 function
            "function": {  # 作用: function 内保存工具名和参数
                "name": tool_call.name,  # 作用: 工具名称
                "arguments": json.dumps(tool_call.arguments, ensure_ascii=False),  # 作用: 参数转成 JSON 字符串
            },  # 作用: function 字段结束
        }  # 作用: 工具调用字典结束

    def _tool_result_to_dict(self, tool_call: ToolCall, output: str) -> dict[str, Any]:  # 作用: 把工具执行结果转成 OpenAI tool 消息
        return {  # 作用: 返回 tool 消息字典
            "role": "tool",  # 作用: role=tool 表示这是工具结果
            "tool_call_id": tool_call.call_id,  # 作用: 对应前面的工具调用 id
            "name": tool_call.name,  # 作用: 保存工具名称，方便调试
            "content": output,  # 作用: 保存工具结果文本
        }  # 作用: tool 消息字典结束

    # 新增代码+ComputerUseVisionLoop: 函数段开始，_tool_result_messages_to_dicts 把普通工具结果扩展为“文本结果 + 可选视觉图片消息”；如果没有这段函数，Computer Use 的截图只能作为路径文本回灌，模型主循环无法像 ClaudeCode 一样真正看屏幕。
    def _tool_result_messages_to_dicts(self, tool_call: ToolCall, output: str) -> list[dict[str, Any]]:  # 新增代码+ComputerUseVisionLoop: 定义工具结果回灌消息构造入口；如果没有这行代码，主循环无法统一处理截图和普通工具结果。
        result_messages = [self._tool_result_to_dict(tool_call, output)]  # 新增代码+ComputerUseVisionLoop: 先保留标准 tool 文本结果以维持 tool_call_id 配对；如果没有这行代码，模型工具协议会断链。
        image_message = self._computer_use_image_message_from_tool_output(tool_call, output)  # 新增代码+ComputerUseVisionLoop: 尝试从 Computer Use 文本结果中提取截图并构造多模态消息；如果没有这行代码，截图像素不会进入下一轮模型输入。
        if image_message is not None:  # 新增代码+ComputerUseVisionLoop: 只有真实构造出图片消息才追加；如果没有这行代码，普通工具结果会出现空图片消息噪音。
            result_messages.append(image_message)  # 新增代码+ComputerUseVisionLoop: 把图片消息追加到 tool 结果后面；如果没有这行代码，模型仍只能看到文字。
        return result_messages  # 新增代码+ComputerUseVisionLoop: 返回一组可直接 extend 到 messages 的消息；如果没有这行代码，主循环拿不到构造结果。
    # 新增代码+ComputerUseVisionLoop: 函数段结束，_tool_result_messages_to_dicts 到此结束；如果没有这个边界说明，代码小白不容易看出工具结果回灌范围。

    # 新增代码+ComputerUseVisionLoop: 函数段开始，_computer_use_image_message_from_tool_output 把 Computer Use 截图 artifact 转成模型可见 image_url 消息；如果没有这段函数，观察层虽然落盘截图但模型不会接收像素。
    def _computer_use_image_message_from_tool_output(self, tool_call: ToolCall, output: str) -> dict[str, Any] | None:  # 新增代码+ComputerUseVisionLoop: 定义从工具输出构造图片消息的私有函数；如果没有这行代码，普通工具和 Computer Use 工具无法分开处理。
        if tool_call.name not in {"computer_observe", "computer_action", "computer_use", "computer-use"}:  # 新增代码+ComputerUseVisionLoop: 只处理 Computer Use 相关工具；如果没有这行代码，read/bash 等普通工具可能被误解析成本地图片。
            return None  # 新增代码+ComputerUseVisionLoop: 非 Computer Use 工具不追加图片消息；如果没有这行代码，普通工具结果会污染多模态上下文。
        image_blocks = self._computer_use_image_blocks_from_tool_output(output)  # 新增代码+ComputerUseVisionLoop: 从文本结果中读取 artifact 路径并转成 image_url 块；如果没有这行代码，函数无法生成图片内容。
        if not image_blocks:  # 新增代码+ComputerUseVisionLoop: 没有可读取截图时不返回图片消息；如果没有这行代码，无截图观察会追加空 user 消息。
            return None  # 新增代码+ComputerUseVisionLoop: 返回 None 表示保持普通文本工具结果；如果没有这行代码，调用方无法区分无图和有图。
        content_blocks: list[dict[str, Any]] = [{"type": "text", "text": f"Computer Use screenshot pixels from {tool_call.name}; use this image together with the preceding tool result to plan the next desktop action."}]  # 新增代码+ComputerUseVisionLoop: 放入一段简短说明，告诉模型这些像素对应刚才工具结果；如果没有这行代码，图片和工具调用来源容易脱节。
        content_blocks.extend(image_blocks)  # 新增代码+ComputerUseVisionLoop: 把所有截图 image_url 块追加到说明后；如果没有这行代码，消息只有说明没有像素。
        return {"role": "user", "content": content_blocks}  # 新增代码+ComputerUseVisionLoop: 用 user 多模态消息承载图片，兼容 OpenAI Chat Completions 的图片输入形态；如果没有这行代码，模型 API 不能接收图片块。
    # 新增代码+ComputerUseVisionLoop: 函数段结束，_computer_use_image_message_from_tool_output 到此结束；如果没有这个边界说明，学习者不容易看出图片消息生成范围。

    # 新增代码+ComputerUseVisionLoop: 函数段开始，_computer_use_image_blocks_from_tool_output 解析工具文本里的 image_result 行并读取图片字节；如果没有这段函数，只有 artifact_path 字符串，模型不能直接视觉观察。
    def _computer_use_image_blocks_from_tool_output(self, output: str) -> list[dict[str, Any]]:  # 新增代码+ComputerUseVisionLoop: 定义图片块提取函数；如果没有这行代码，调用方无法把工具输出转换为多模态块。
        image_specs = self._computer_use_image_specs_from_tool_output(output)  # 新增代码+ComputerUseVisionLoop: 先解析 artifact_path 和 mime_type 元数据；如果没有这行代码，后续不知道要读取哪些图片。
        image_blocks: list[dict[str, Any]] = []  # 新增代码+ComputerUseVisionLoop: 准备保存最终 image_url 块；如果没有这行代码，无法累积多张截图。
        max_image_bytes = 8 * 1024 * 1024  # 新增代码+ComputerUseVisionLoop: 限制单张图片最大 8MB，避免异常 artifact 撑爆模型上下文；如果没有这行代码，坏截图可能让请求体过大。
        for spec in image_specs:  # 新增代码+ComputerUseVisionLoop: 遍历每个图片引用；如果没有这行代码，多张截图无法处理。
            artifact_path = Path(str(spec.get("artifact_path", "") or ""))  # 新增代码+ComputerUseVisionLoop: 把 artifact 路径转为 Path；如果没有这行代码，无法稳定检查文件是否存在。
            if not artifact_path.is_file():  # 新增代码+ComputerUseVisionLoop: 跳过不存在或非文件路径；如果没有这行代码，读取坏路径会中断整个工具循环。
                continue  # 新增代码+ComputerUseVisionLoop: 继续处理下一张图片；如果没有这行代码，一个坏 artifact 会阻断所有有效截图。
            image_payload = self._computer_use_model_image_payload(artifact_path, spec.get("mime_type"), max_image_bytes)  # 新增代码+ComputerUseBmpPng: 读取截图并在必要时把 BMP 转成模型支持的 PNG；如果没有这行代码，真实 Windows BMP 截图会继续触发 Responses API 400。
            if image_payload is None:  # 新增代码+ComputerUseBmpPng: 遇到读取失败、转码失败、空图或过大图时跳过当前截图；如果没有这行代码，后续解包会因为 None 崩溃。
                continue  # 新增代码+ComputerUseBmpPng: 保留其它截图继续进入模型的机会；如果没有这行代码，一张坏图会阻断整轮 observe-plan-act。
            image_bytes, mime_type = image_payload  # 新增代码+ComputerUseBmpPng: 取得已经模型兼容的图片字节和 MIME；如果没有这行代码，base64 编码不知道应该处理哪份字节。
            encoded_image = base64.b64encode(image_bytes).decode("ascii")  # 新增代码+ComputerUseVisionLoop: 把图片字节转成 base64 文本；如果没有这行代码，JSON 消息无法携带二进制图片。
            image_blocks.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_image}", "detail": "high"}})  # 新增代码+ComputerUseVisionLoop: 生成 OpenAI 兼容 image_url 块；如果没有这行代码，模型不会收到实际图片像素。
        return image_blocks  # 新增代码+ComputerUseVisionLoop: 返回所有可用图片块；如果没有这行代码，调用方拿不到结果。
    # 新增代码+ComputerUseVisionLoop: 函数段结束，_computer_use_image_blocks_from_tool_output 到此结束；如果没有这个边界说明，学习者不容易看出图片字节读取范围。

    # 新增代码+ComputerUseBmpPng: 函数段开始，_computer_use_model_image_payload 统一把截图 artifact 变成模型 API 支持的图片字节；如果没有这段函数，BMP 转 PNG、读取失败和大小限制会散落在主循环里，后续容易再次误接。
    def _computer_use_model_image_payload(self, artifact_path: Path, raw_mime_type: Any, max_image_bytes: int) -> tuple[bytes, str] | None:  # 新增代码+ComputerUseBmpPng: 定义模型图片载荷构造函数；如果没有这行代码，调用方无法得到“字节+MIME”的稳定结果。
        mime_type = self._computer_use_model_image_mime_type(raw_mime_type, artifact_path)  # 新增代码+ComputerUseBmpPng: 先按工具输出和文件后缀判断源图片类型；如果没有这行代码，代码不知道什么时候需要 BMP 转码。
        if mime_type == "image/bmp":  # 新增代码+ComputerUseBmpPng: 识别 Windows observe 真实返回的 BMP 截图；如果没有这行代码，BMP 会被原样发给 Responses API 并失败。
            return self._computer_use_png_payload_from_bmp_artifact(artifact_path, max_image_bytes)  # 新增代码+ComputerUseBmpPng: 把 BMP 真实转码为 PNG 后返回；如果没有这行代码，只改 MIME 会造成模型按 PNG 解码 BMP 的新错误。
        try:  # 新增代码+ComputerUseBmpPng: 捕获普通图片读取异常；如果没有这行代码，权限或并发写入问题会让 agent 主循环崩溃。
            image_bytes = artifact_path.read_bytes()  # 新增代码+ComputerUseBmpPng: 读取 PNG/JPEG/WebP/GIF 等模型支持格式的原始字节；如果没有这行代码，无法生成 base64 data URL。
        except OSError as error:  # 新增代码+ComputerUseBmpPng: 处理文件读取失败；如果没有这行代码，底层 OSError 会直接冒泡。
            self._record_observation("computer_use_image_read_failed", {"artifact_path": str(artifact_path), "error": str(error)})  # 新增代码+ComputerUseBmpPng: 记录读取失败证据；如果没有这行代码，排查时不知道哪张图没读到。
            return None  # 新增代码+ComputerUseBmpPng: 告诉调用方当前图片不可用；如果没有这行代码，失败路径会继续尝试编码不存在的字节。
        if not image_bytes or len(image_bytes) > max_image_bytes:  # 新增代码+ComputerUseBmpPng: 拒绝空图或过大图；如果没有这行代码，模型可能收到无效或过大的图片块。
            self._record_observation("computer_use_image_skipped_for_model", {"artifact_path": str(artifact_path), "byte_count": len(image_bytes), "max_image_bytes": max_image_bytes})  # 新增代码+ComputerUseBmpPng: 记录跳过原因；如果没有这行代码，用户不知道为什么某张截图没进模型。
            return None  # 新增代码+ComputerUseBmpPng: 跳过当前图片；如果没有这行代码，后续仍会把异常图片编码进上下文。
        return image_bytes, mime_type  # 新增代码+ComputerUseBmpPng: 返回可直接发给模型的图片字节和 MIME；如果没有这行代码，调用方拿不到转码后的统一载荷。
    # 新增代码+ComputerUseBmpPng: 函数段结束，_computer_use_model_image_payload 到此结束；如果没有这个边界说明，用户不容易看出模型图片载荷处理范围。

    # 新增代码+ComputerUseBmpPng: 函数段开始，_computer_use_png_payload_from_bmp_artifact 只负责把 BMP artifact 转成 PNG；如果没有这段函数，真实 Windows 截图会因为模型 API 不支持 BMP 而中断任务。
    def _computer_use_png_payload_from_bmp_artifact(self, artifact_path: Path, max_image_bytes: int) -> tuple[bytes, str] | None:  # 新增代码+ComputerUseBmpPng: 定义 BMP 转 PNG 的专用函数；如果没有这行代码，转码逻辑会和普通读取逻辑混在一起难以审计。
        try:  # 新增代码+ComputerUseBmpPng: 延迟导入图片库，避免没有 Computer Use 截图时增加启动成本；如果没有这行代码，导入失败会在模块加载阶段直接影响普通 agent。
            from io import BytesIO  # 新增代码+ComputerUseBmpPng: 导入内存缓冲区保存 PNG 字节；如果没有这行代码，只能落盘临时 PNG，增加清理风险。
            from PIL import Image  # 新增代码+ComputerUseBmpPng: 导入 Pillow 读取 BMP 并写出 PNG；如果没有这行代码，不能真实转码，只能错误地改 MIME。
        except Exception as error:  # 新增代码+ComputerUseBmpPng: 捕获 Pillow 不可用等环境问题；如果没有这行代码，缺依赖会让整个模型主循环崩溃。
            self._record_observation("computer_use_bmp_conversion_unavailable", {"artifact_path": str(artifact_path), "error": str(error)})  # 新增代码+ComputerUseBmpPng: 记录转码能力缺失；如果没有这行代码，真实终端失败时无法定位为依赖问题。
            return None  # 新增代码+ComputerUseBmpPng: 没有可靠转码能力就不发送坏图；如果没有这行代码，后续可能继续把 BMP 发给模型。
        try:  # 新增代码+ComputerUseBmpPng: 捕获 BMP 读取或 PNG 写出异常；如果没有这行代码，坏截图会中断整个任务。
            with Image.open(artifact_path) as image:  # 新增代码+ComputerUseBmpPng: 用 Pillow 打开 BMP artifact；如果没有这行代码，无法把 Windows BMP 解码成像素。
                buffer = BytesIO()  # 新增代码+ComputerUseBmpPng: 创建内存 PNG 输出缓冲区；如果没有这行代码，PNG 字节没有保存位置。
                image.save(buffer, format="PNG")  # 新增代码+ComputerUseBmpPng: 把 BMP 像素重新编码为 PNG；如果没有这行代码，Responses API 仍然收不到支持格式。
                image_bytes = buffer.getvalue()  # 新增代码+ComputerUseBmpPng: 取出转码后的 PNG 字节；如果没有这行代码，调用方拿不到真实 PNG 内容。
        except Exception as error:  # 新增代码+ComputerUseBmpPng: 处理坏 BMP、文件被占用或 Pillow 解码失败；如果没有这行代码，异常会冒泡到用户任务。
            self._record_observation("computer_use_bmp_conversion_failed", {"artifact_path": str(artifact_path), "error": str(error)})  # 新增代码+ComputerUseBmpPng: 记录具体转码失败原因；如果没有这行代码，排查时只能看到图片没有进入模型。
            return None  # 新增代码+ComputerUseBmpPng: 转码失败时跳过该图；如果没有这行代码，后续会使用未定义字节。
        if not image_bytes or len(image_bytes) > max_image_bytes:  # 新增代码+ComputerUseBmpPng: 转码后仍检查空图和大小上限；如果没有这行代码，异常 BMP 可能变成过大的 PNG 请求体。
            self._record_observation("computer_use_image_skipped_for_model", {"artifact_path": str(artifact_path), "byte_count": len(image_bytes), "max_image_bytes": max_image_bytes, "converted_from": "image/bmp"})  # 新增代码+ComputerUseBmpPng: 记录 BMP 转 PNG 后被跳过的原因；如果没有这行代码，用户不知道是转码后大小不合格。
            return None  # 新增代码+ComputerUseBmpPng: 不把空图或过大图发给模型；如果没有这行代码，模型请求可能再次失败。
        return image_bytes, "image/png"  # 新增代码+ComputerUseBmpPng: 返回真实 PNG 字节和 PNG MIME；如果没有这行代码，模型仍会收到不支持的 BMP 或无效 MIME。
    # 新增代码+ComputerUseBmpPng: 函数段结束，_computer_use_png_payload_from_bmp_artifact 到此结束；如果没有这个边界说明，用户不容易看出 BMP 转 PNG 的完整范围。

    # 新增代码+ComputerUseVisionLoop: 函数段开始，_computer_use_image_specs_from_tool_output 从稳定文本区块解析图片路径和 MIME；如果没有这段函数，主循环需要理解完整 data dict，耦合会更重。
    def _computer_use_image_specs_from_tool_output(self, output: str) -> list[dict[str, str]]:  # 新增代码+ComputerUseVisionLoop: 定义 image_result 文本解析函数；如果没有这行代码，图片路径提取会散落到多个地方。
        specs_by_index: dict[str, dict[str, str]] = {}  # 新增代码+ComputerUseVisionLoop: 按 image_0/image_1 聚合字段；如果没有这行代码，路径和 MIME 无法稳定配对。
        for raw_line in str(output or "").splitlines():  # 新增代码+ComputerUseVisionLoop: 逐行读取工具输出；如果没有这行代码，无法解析格式化图片区。
            line = raw_line.strip()  # 新增代码+ComputerUseVisionLoop: 去掉每行首尾空白；如果没有这行代码，前导 "- " 会影响字段匹配。
            if not line.startswith("- image_") or "=" not in line:  # 新增代码+ComputerUseVisionLoop: 只处理图片区字段行；如果没有这行代码，普通文本可能被误解析。
                continue  # 新增代码+ComputerUseVisionLoop: 跳过非图片字段；如果没有这行代码，后续字符串切分会碰到无关行。
            key, value = line[2:].split("=", 1)  # 新增代码+ComputerUseVisionLoop: 拆分字段名和值；如果没有这行代码，无法取出 artifact_path 或 mime_type。
            key_parts = key.split("_")  # 新增代码+ComputerUseVisionLoop: 把 image_0_artifact_path 拆成片段；如果没有这行代码，无法识别图片序号。
            if len(key_parts) < 3 or key_parts[0] != "image":  # 新增代码+ComputerUseVisionLoop: 校验字段名结构；如果没有这行代码，异常字段可能污染 specs。
                continue  # 新增代码+ComputerUseVisionLoop: 跳过不合规字段；如果没有这行代码，后续 index 读取可能错误。
            image_index = key_parts[1]  # 新增代码+ComputerUseVisionLoop: 读取图片序号；如果没有这行代码，多个图片字段无法聚合。
            field_name = "_".join(key_parts[2:])  # 新增代码+ComputerUseVisionLoop: 还原字段名后缀；如果没有这行代码，artifact_path 这类字段会被拆散。
            spec = specs_by_index.setdefault(image_index, {})  # 新增代码+ComputerUseVisionLoop: 获取当前图片的聚合字典；如果没有这行代码，字段无法保存。
            if field_name in {"artifact_path", "mime_type"}:  # 新增代码+ComputerUseVisionLoop: 只保留读取图片所需字段；如果没有这行代码，尺寸和 marker 等无关字段会进入读取逻辑。
                spec[field_name] = value.strip()  # 新增代码+ComputerUseVisionLoop: 保存清理后的字段值；如果没有这行代码，路径可能带多余空白。
        return [spec for _, spec in sorted(specs_by_index.items()) if spec.get("artifact_path")]  # 新增代码+ComputerUseVisionLoop: 返回带 artifact_path 的图片引用；如果没有这行代码，调用方会收到空路径项。
    # 新增代码+ComputerUseVisionLoop: 函数段结束，_computer_use_image_specs_from_tool_output 到此结束；如果没有这个边界说明，用户不容易看出文本解析边界。

    # 新增代码+ComputerUseVisionLoop: 函数段开始，_computer_use_model_image_mime_type 为模型图片块选择保守 MIME；如果没有这段函数，data URL 类型可能为空或不稳定。
    def _computer_use_model_image_mime_type(self, raw_mime_type: Any, artifact_path: Path) -> str:  # 新增代码+ComputerUseVisionLoop: 定义 MIME 规范化函数；如果没有这行代码，图片块可能携带非法 MIME。
        mime_type = str(raw_mime_type or "").strip().lower()  # 新增代码+ComputerUseVisionLoop: 清理工具输出中的 MIME；如果没有这行代码，大小写和空白会影响 API 识别。
        if mime_type in {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/bmp"}:  # 新增代码+ComputerUseVisionLoop: 接受常见截图 MIME；如果没有这行代码，合法图片类型会被误改。
            return "image/jpeg" if mime_type == "image/jpg" else mime_type  # 新增代码+ComputerUseVisionLoop: 把 image/jpg 规范成 image/jpeg；如果没有这行代码，部分模型 API 可能不认别名。
        suffix = artifact_path.suffix.lower().lstrip(".")  # 新增代码+ComputerUseVisionLoop: 从文件后缀推断兜底类型；如果没有这行代码，缺 MIME 的旧证据无法传图。
        if suffix == "png":  # 新增代码+ComputerUseVisionLoop: 识别 PNG 后缀；如果没有这行代码，PNG 证据会落到默认 JPEG。
            return "image/png"  # 新增代码+ComputerUseVisionLoop: 返回 PNG MIME；如果没有这行代码，模型可能按错格式解码。
        if suffix in {"jpg", "jpeg"}:  # 新增代码+ComputerUseVisionLoop: 识别 JPEG 后缀；如果没有这行代码，JPEG 证据会落到默认类型。
            return "image/jpeg"  # 新增代码+ComputerUseVisionLoop: 返回 JPEG MIME；如果没有这行代码，模型可能按错格式解码。
        if suffix == "webp":  # 新增代码+ComputerUseVisionLoop: 识别 WebP 后缀；如果没有这行代码，WebP 证据会落到默认类型。
            return "image/webp"  # 新增代码+ComputerUseVisionLoop: 返回 WebP MIME；如果没有这行代码，模型可能按错格式解码。
        if suffix == "bmp":  # 新增代码+ComputerUseVisionLoop: 识别 Windows BMP 后缀；如果没有这行代码，BMP 证据会被错误标成 JPEG。
            return "image/bmp"  # 新增代码+ComputerUseVisionLoop: 返回 BMP MIME；如果没有这行代码，Windows 截图类型会丢失。
        return "image/jpeg"  # 新增代码+ComputerUseVisionLoop: 未知类型使用最保守常见图片 MIME；如果没有这行代码，data URL 会缺少稳定类型。
    # 新增代码+ComputerUseVisionLoop: 函数段结束，_computer_use_model_image_mime_type 到此结束；如果没有这个边界说明，用户不容易看出 MIME 兜底范围。

    def _execute_tool(self, tool_call: ToolCall) -> str:  # 修改代码+ToolsExecutorSplit: 根据工具名称委托 tools.executor 分发到具体工具函数；若没有这行代码，旧调用方会找不到执行入口
        return execute_tool_from_registry(self, tool_call)  # 修改代码+ToolsExecutorSplit: 把 allowed_tools、policy、plan mode、deferred 和工具名分发交给独立执行器；若没有这行代码，执行层仍会堆在 learning_agent.py 里

    def _mcp_tool_risk_summary(self, tool_call: ToolCall) -> tuple[str, str]:  # 新增代码+权限分级: 根据 MCP 工具名生成授权风险摘要；若省略: 用户只能看到模糊外部调用而无法区分搜索、写入、删除或命令风险
        tool_name = tool_call.name.lower()  # 新增代码+权限分级: 统一转小写方便匹配工具类别；若省略: 大小写变化可能导致风险分类漏判
        if tool_name.endswith("__authenticate") or tool_name.endswith("authenticate"):  # 新增代码+MCPAuthMetadata: 识别 MCP 鉴权说明伪工具；若省略: 登录入口会被归类成普通外部调用
            return ("鉴权说明/低风险", "只展示 WWW-Authenticate、resource_metadata 和 Authorization: Bearer 配置提示；不要在参数里填写 access token。")  # 新增代码+MCPAuthMetadata: 返回保守且明确的鉴权风险说明；若省略: 用户可能误以为工具会自动登录或收集令牌
        if tool_name.endswith("__delete_file") or tool_name.endswith("delete_file"):  # 新增代码+权限分级: 优先识别删除文件工具；若省略: 删除操作可能被误归为普通写入或外部调用
            return ("删除/破坏性操作", "会删除工作区文件；确认前请重点核对 path 和 confirm_delete。")  # 新增代码+权限分级: 返回删除风险说明；若省略: 用户看不到删除操作最需要核对的参数
        if tool_name.endswith("__run_powershell") or "powershell" in tool_name or "shell" in tool_name or "command" in tool_name:  # 新增代码+权限分级: 识别命令执行类工具；若省略: 运行命令可能只显示普通外部工具提示
            return ("命令执行", "会在本机或工作区执行命令；确认前请重点核对 command、cwd 和命令副作用。")  # 新增代码+权限分级: 返回命令执行风险说明；若省略: 用户缺少判断命令副作用的提醒
        if tool_name.endswith("__write_file") or tool_name.endswith("__create_file") or tool_name.endswith("__edit_file") or tool_name.endswith("__copy_file") or tool_name.endswith("__move_file"):  # 新增代码+权限分级: 识别写入、创建、编辑、复制和移动文件工具；若省略: 文件变更可能被当成只读操作
            return ("写入/文件变更", "会修改工作区文件；确认前请重点核对路径、覆盖参数和内容差异。")  # 新增代码+权限分级: 返回文件变更风险说明；若省略: 用户缺少检查文件副作用的提示
        if "browser_automation" in tool_name and tool_name.endswith("__browser_connect_real_chrome"):  # 新增代码+RealChrome风险: 在通用浏览器自动化分类前识别真实 Chrome 连接工具；若省略: 日常 profile 连接会被误标成低风险浏览器状态
            return ("真实 Chrome 高风险", "会连接日常 Chrome profile 并接触真实登录态；确认前请重点核对 confirm_real_profile、chrome_path、user_data_dir、profile_directory、debug_port。")  # 新增代码+RealChrome风险: 明确真实 profile 和登录态风险以及关键确认参数；若省略: 用户可能不知道该工具不同于独立 Chromium
        if "browser_automation" in tool_name and tool_name.endswith("__browser_disconnect_real_chrome"):  # 新增代码+RealChrome风险: 在通用浏览器自动化分类前识别真实 Chrome 断开工具；若省略: 断开 CDP 连接会被误归为只读状态
            return ("真实 Chrome 中风险", "会断开真实 Chrome CDP 连接；默认不关闭用户 Chrome，确认前请重点核对 close_browser。")  # 新增代码+RealChrome风险: 说明默认不关闭日常 Chrome 并提示核对 close_browser；若省略: 用户可能误以为断开一定会关闭浏览器或不会改变连接状态
        if "browser_automation" in tool_name and tool_name.endswith("__browser_profile_status"):  # 新增代码+RealChrome风险: 在通用浏览器自动化分类前识别 profile 状态工具；若省略: 只读隐私边界会被普通状态说明稀释
            return ("只读/低风险浏览器状态", "只读当前浏览器会话模式、页面数量和最近安全拒绝；不读取 cookies、storage、token 或密码。")  # 新增代码+RealChrome风险: 明确 status 只读范围和敏感数据不读取边界；若省略: 用户可能担心状态工具读取登录态明细
        if "browser_automation" in tool_name and tool_name.endswith("__browser_evaluate"):  # 新增代码+BrowserAutomation风险: 优先识别页面 JavaScript 执行工具；若省略: browser_evaluate 会被误归类为普通外部工具或联网工具
            return ("浏览器自动化高风险", "会在网页里执行 JavaScript；确认前请重点核对 script，避免读取 cookie、localStorage、sessionStorage、token、密码框等敏感信息。")  # 新增代码+BrowserAutomation风险: 明确脚本执行和敏感信息边界；若省略: 用户可能不知道 evaluate 能读取页面内敏感状态
        if "browser_automation" in tool_name and tool_name.endswith("__browser_downloads"):  # 新增代码+BrowserAutomation风险: 单独识别下载记录读取工具；若省略: browser_downloads 会被误描述成主动下载文件
            return ("浏览器自动化高风险", "会查看浏览器下载记录，本工具本身不主动触发下载；触发下载通常由 browser_click 等页面操作导致，确认前请重点核对 max_results、文件路径和 URL 记录范围。")  # 新增代码+BrowserAutomation风险: 区分查看下载记录和触发下载动作；若省略: 用户会误解 browser_downloads 的真实副作用
        if "browser_automation" in tool_name and (tool_name.endswith("__browser_click") or tool_name.endswith("__browser_type") or tool_name.endswith("__browser_press_key") or tool_name.endswith("__browser_upload_file") or tool_name.endswith("__browser_close")):  # 修改代码+BrowserAutomation风险: 识别会点击、输入、按键、上传或关闭浏览器的工具；若省略: 这些高副作用操作会缺少醒目提醒
            return ("浏览器自动化高风险", "会操作网页、输入文本、按键、上传文件、关闭页面或浏览器；确认前请重点核对 selector、文本、文件路径、URL。")  # 修改代码+BrowserAutomation风险: 返回高风险浏览器操作说明且不把 downloads 说成主动下载；若省略: 用户可能没核对目标元素、文本、路径或网址就授权
        if "browser_automation" in tool_name and (tool_name.endswith("__browser_open") or tool_name.endswith("__browser_wait") or tool_name.endswith("__browser_screenshot") or tool_name.endswith("__browser_launch_visible")):  # 修改代码+VisibleBrowser风险: 把弹出可见浏览器窗口识别为中等风险浏览器工具；若没有这行代码，权限提示不会说明本地窗口副作用
            return ("浏览器自动化中风险", "会打开网页、等待页面变化或保存截图；确认前请重点核对 url、page_id、filename。")  # 新增代码+BrowserAutomation风险: 返回中风险浏览器操作说明；若省略: 用户可能忽略网址、页面 id 或截图文件名
        if "browser_automation" in tool_name:  # 新增代码+BrowserAutomation风险: 捕获 snapshot、tabs、console、network 等其他浏览器自动化工具；若省略: 这些只读状态读取会落到普通外部工具分类
            return ("只读/低风险浏览器状态", "主要读取浏览器页面状态、标签页、console 或 network 摘要；确认前请重点核对 page_id 和读取范围。")  # 新增代码+BrowserAutomation风险: 返回低风险浏览器状态说明；若省略: 用户看不到 page_id 和读取范围这两个核对点
        if "browser_search" in tool_name or tool_name.endswith("__web_search") or tool_name.endswith("__fetch_url") or tool_name.endswith("__open_url"):  # 新增代码+权限分级: 识别搜索、浏览器和 URL 抓取类工具；若省略: 联网访问可能被误认为本地只读
            return ("外部网络访问", "会访问网络、搜索引擎或网页；确认前请重点核对 query、url 和是否需要实时信息。")  # 新增代码+权限分级: 返回联网风险说明；若省略: 用户看不到外部网络访问边界
        if tool_name.endswith("__read_file") or tool_name.endswith("__list_dir") or tool_name.endswith("__glob") or tool_name.endswith("__grep"):  # 新增代码+权限分级: 识别本地只读工作区工具；若省略: 低风险读取无法和高风险操作区分
            return ("只读/低风险", "只读取工作区信息；确认前仍需核对路径、模式或搜索关键词。")  # 新增代码+权限分级: 返回只读风险说明；若省略: 用户不知道虽然低风险也要检查参数
        return ("外部工具调用", "来自 MCP server 的外部能力；确认前请核对工具名和全部参数。")  # 新增代码+权限分级: 为未知 MCP 工具提供保守默认分类；若省略: 新增 MCP 工具可能没有任何风险提示

    def _format_mcp_permission_action(self, tool_call: ToolCall) -> str:  # 新增代码+权限分级: 统一格式化 MCP 工具授权文本；若省略: 风险等级、说明和参数可能在不同调用处格式不一致
        arguments_json = json.dumps(tool_call.arguments, ensure_ascii=False, indent=2)  # 新增代码+权限分级: 把参数格式化成用户可读 JSON；若省略: 用户难以核对本次工具调用的真实参数
        risk_level, risk_note = self._mcp_tool_risk_summary(tool_call)  # 新增代码+权限分级: 计算风险等级和风险说明；若省略: 授权文本无法显示分级信息
        return f"调用 MCP 工具：{tool_call.name}\n风险等级：{risk_level}\n风险说明：{risk_note}\n参数：{arguments_json}"  # 新增代码+权限分级: 返回包含工具名、风险和参数的完整授权说明；若省略: ask_permission 无法给用户足够决策信息

    def _record_mcp_call_progress(self, tool_call: ToolCall, state: str, arguments: dict[str, Any], detail: str) -> None:  # 新增代码+MCPProgress: 记录单次 MCP 调用进度；若没有这行代码，call progress 会分散在执行分支里
        event = {  # 新增代码+MCPProgress: 构造结构化进度事件；若没有这行代码，进度字段没有统一格式
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),  # 新增代码+MCPProgress: 保存事件时间；若没有这行代码，用户无法判断进度新旧
            "tool_name": tool_call.name,  # 新增代码+MCPProgress: 保存 MCP 前缀工具名；若没有这行代码，进度无法对应具体工具
            "call_id": tool_call.call_id,  # 新增代码+MCPProgress: 保存模型工具调用 id；若没有这行代码，多个并发/连续调用难以区分
            "state": state,  # 新增代码+MCPProgress: 保存 permission_requested/started/completed/failed 等状态；若没有这行代码，进度没有机器可读阶段
            "arguments": copy.deepcopy(arguments),  # 新增代码+MCPProgress: 保存清洗后参数快照；若没有这行代码，审计无法核对用户确认和实际调用是否一致
            "detail": detail,  # 新增代码+MCPProgress: 保存补充说明或错误摘要；若没有这行代码，失败和输出长度细节会丢失
        }  # 新增代码+MCPProgress: 进度事件字典结束；若没有这行代码，Python 语法不完整
        self.mcp_call_progress_events.append(event)  # 新增代码+MCPProgress: 把事件加入 MCP 调用进度列表；若没有这行代码，调用方无法回看进度
        self.mcp_call_progress_events = self.mcp_call_progress_events[-200:]  # 新增代码+MCPProgress: 限制最多保留最近 200 条；若没有这行代码，长期运行可能无限增长内存
        self._record_observation("mcp_call_progress", event)  # 新增代码+ObservationV1: 同步写入通用观察流；若没有这行代码，Phase 6 审计需要查多个列表

    def _load_visible_browser_tools_after_launch(self) -> None:  # 新增代码+VisibleBrowser验收: 可见浏览器启动成功后补加载普通浏览器能力包；若没有这行代码，agent 只能启动窗口但看不到 browser_open。
        loaded_names: list[str] = []  # 新增代码+VisibleBrowser验收: 保存本次恢复可见的工具名；若没有这行代码，审计日志无法解释工具池变化。
        for tool in self._capability_pack_tools("browser_automation"):  # 新增代码+VisibleBrowser验收: 遍历普通浏览器自动化能力包；若没有这行代码，browser_open、snapshot 等后续工具不会批量恢复。
            decision = self._tool_policy_decision(tool)  # 新增代码+VisibleBrowser验收: 复用统一工具策略避免绕过 deny 规则；若没有这行代码，启动可见浏览器可能意外解锁被禁工具。
            if decision.state == "blocked":  # 新增代码+VisibleBrowser验收: 明确被安全策略禁止的工具仍不能加载；若没有这行代码，deny 规则会被 visible workflow 绕开。
                continue  # 新增代码+VisibleBrowser验收: 跳过被禁止的工具并继续处理同包其他工具；若没有这行代码，一个禁用工具会影响整个包。
            self.loaded_tool_names.add(tool.name)  # 新增代码+VisibleBrowser验收: 把允许的浏览器工具加入当前工具池；若没有这行代码，下一轮模型仍看不到 browser_open。
            loaded_names.append(tool.name)  # 新增代码+VisibleBrowser验收: 记录成功加入的工具名；若没有这行代码，观察事件没有详细清单。
        if loaded_names:  # 新增代码+VisibleBrowser验收: 只有确实加载到工具时才写观察事件；若没有这行代码，日志会出现空事件噪声。
            self._record_observation("visible_browser_loaded_tools", {"tools": loaded_names})  # 新增代码+VisibleBrowser验收: 记录可见浏览器 workflow 解锁了哪些工具；若没有这行代码，验收失败时难以追溯工具池状态。

    def _load_visible_browser_tools_for_information_task(self) -> None:  # 新增代码+自然可见浏览器路由: 为普通实时查询首轮预加载可见浏览器工具；若没有这行代码，模型第一轮只能看到后台搜索或 profile_status。
        if not self.visible_browser_information_task_requested:  # 新增代码+自然可见浏览器路由: 只处理被识别为自然实时查询的任务；若没有这行代码，所有任务都会提前暴露浏览器工具。
            return  # 新增代码+自然可见浏览器路由: 非目标任务直接退出；若没有这行代码，代码分析任务可能被浏览器工具污染。
        self.tool_policy_context.loaded_skills.add("browser_automation")  # 新增代码+自然可见浏览器路由: 标记普通浏览器 skill 已准备；若没有这行代码，后续策略或审计无法解释工具为何可见。
        visible_query_tool_names = {  # 新增代码+自然可见浏览器路由: 限定普通查询首轮可见的浏览器工具白名单；若没有这行代码，browser_evaluate 等高风险工具可能被不必要暴露。
            "browser_launch_visible",  # 新增代码+自然可见浏览器路由: 启动可见独立 Chromium；若没有这项，用户看不到真实浏览器窗口。
            "browser_open",  # 新增代码+自然可见浏览器路由: 打开公开搜索页或天气资料页；若没有这项，启动窗口后无法访问网页。
            "browser_wait",  # 新增代码+自然可见浏览器路由: 等待页面加载；若没有这项，动态页面可能读取过早。
            "browser_snapshot",  # 新增代码+自然可见浏览器路由: 读取可见页面文本；若没有这项，最终回答缺少网页证据。
            "browser_screenshot",  # 新增代码+自然可见浏览器路由: 保存视觉证据；若没有这项，肉眼可见验收证据不足。
            "browser_visual_locate",  # 新增代码+自然可见浏览器路由: 定位页面文字或搜索框；若没有这项，复杂页面流程容易失败。
            "browser_click",  # 新增代码+自然可见浏览器路由: 点击搜索框或同意按钮；若没有这项，模型无法完成拟人操作。
            "browser_type",  # 新增代码+自然可见浏览器路由: 输入搜索词；若没有这项，用户看不到真实输入过程。
            "browser_press_key",  # 新增代码+自然可见浏览器路由: 按 Enter 提交搜索；若没有这项，拟人搜索流程不完整。
            "browser_flow_run",  # 新增代码+自然可见浏览器路由: 执行短流程并保留步骤证据；若没有这项，复杂网站流程需要多次零散工具调用。
            "browser_recover_page",  # 新增代码+自然可见浏览器路由: 页面空白或失败时恢复；若没有这项，异常会退回后台搜索。
            "browser_replay",  # 新增代码+自然可见浏览器路由: 生成安全 dry-run 回放计划；若没有这项，任务回放证据不足。
            "browser_plugin_status",  # 新增代码+自然可见浏览器路由: 查看插件兼容和可见浏览器状态；若没有这项，验收难以确认能力状态。
        }  # 新增代码+自然可见浏览器路由: 结束白名单集合；若没有这行代码，Python 语法不完整。
        loaded_names: list[str] = []  # 新增代码+自然可见浏览器路由: 保存本次预加载的工具名；若没有这行代码，观察日志无法说明工具池变化。
        for tool in self._capability_pack_tools("browser_automation"):  # 新增代码+自然可见浏览器路由: 遍历普通浏览器自动化能力包；若没有这行代码，无法把白名单原始名转成 MCP 前缀工具名。
            if tool.original_name not in visible_query_tool_names:  # 新增代码+自然可见浏览器路由: 跳过不在自然查询白名单内的浏览器工具；若没有这行代码，高风险 evaluate/downloads 可能首轮可见。
                continue  # 新增代码+自然可见浏览器路由: 继续检查同包其它工具；若没有这行代码，一个不需要的工具会中断循环。
            decision = self._tool_policy_decision(tool)  # 新增代码+自然可见浏览器路由: 复用统一策略避免绕过 deny rule；若没有这行代码，预加载会无视安全策略。
            if decision.state == "blocked":  # 新增代码+自然可见浏览器路由: 被策略明确禁止的工具不能暴露；若没有这行代码，deny rule 会被本次修复绕开。
                continue  # 新增代码+自然可见浏览器路由: 跳过被阻断工具；若没有这行代码，一个禁用工具会影响其它安全工具。
            self.loaded_tool_names.add(tool.name)  # 新增代码+自然可见浏览器路由: 将允许的 MCP 工具加入当前工具池；若没有这行代码，模型第一轮看不到 browser_launch_visible。
            loaded_names.append(tool.name)  # 新增代码+自然可见浏览器路由: 记录预加载成功的工具名；若没有这行代码，调试日志缺少具体列表。
        if loaded_names:  # 新增代码+自然可见浏览器路由: 只有确实预加载到工具时记录观察事件；若没有这行代码，日志会出现空事件噪声。
            self._record_observation("visible_browser_information_tools_preloaded", {"tools": loaded_names})  # 新增代码+自然可见浏览器路由: 写入工具池预加载证据；若没有这行代码，验收失败时难以确认首轮工具状态。

    def _update_workflows_after_mcp_tool(self, tool_call: ToolCall, result_text: str) -> None:  # 新增代码+RealChromeWorkflow: 根据 MCP 结果推进真实 Chrome workflow 状态；若没有这行代码，status 和 connect 只是文本不会影响 ToolPolicy
        catalog_tool = self._find_catalog_tool(tool_call.name)  # 新增代码+RealChromeWorkflow: 读取 AgentTool 元数据判断原始 MCP 工具名；若没有这行代码，无法区分 profile_status 和其他浏览器工具
        if catalog_tool is None:  # 新增代码+RealChromeWorkflow: 找不到目录工具时不更新 workflow；若没有这行代码，后续访问 original_name 会报错
            return  # 新增代码+RealChromeWorkflow: 无元数据直接退出；若没有这行代码，异常 catalog 会中断 MCP 调用结果返回
        if catalog_tool.server_name == "browser_automation" and catalog_tool.original_name == "browser_profile_status":  # 新增代码+RealChromeWorkflow: profile status 是真实 Chrome workflow 的前置检查；若没有这行代码，状态工具不会解锁连接准备
            self.tool_policy_context.loaded_skills.add("real_chrome")  # 新增代码+RealChromeWorkflow: 标记真实 Chrome skill 已准备；若没有这行代码，connect 工具会一直卡在 needs_skill
            self.tool_policy_context.completed_workflows.add("real_chrome_profile_ready")  # 新增代码+RealChromeWorkflow: 标记 profile 状态检查已完成；若没有这行代码，connect 工具会一直卡在 needs_workflow
            self._record_observation("real_chrome_profile_ready", {"tool_name": tool_call.name})  # 新增代码+ObservationV1: 记录真实 Chrome 前置 workflow 完成；若没有这行代码，审计看不到为何 connect 被解锁
        if catalog_tool.server_name == "browser_automation" and catalog_tool.original_name == "browser_connect_real_chrome" and "real_chrome_connected=true" in result_text:  # 新增代码+RealChromeWorkflow: 连接结果明确成功时推进 connected workflow；若没有这行代码，后续 browser_open 仍会被真实 Chrome 需求拦截
            self.tool_policy_context.completed_workflows.add("real_chrome_connected")  # 新增代码+RealChromeWorkflow: 标记真实 Chrome 会话已连接；若没有这行代码，后续页面操作无法被策略放行
            self._record_observation("real_chrome_connected", {"tool_name": tool_call.name})  # 新增代码+ObservationV1: 记录真实 Chrome 连接完成；若没有这行代码，审计缺少高风险 workflow 证据
        if catalog_tool.server_name == "browser_automation" and catalog_tool.original_name == "browser_launch_visible" and "visible_browser=true" in result_text and "headless=false" in result_text:  # 新增代码+VisibleBrowser验收: 可见独立浏览器启动成功时推进 visible workflow；若没有这行代码，后续 browser_open 仍会被真实 Chrome 关键词拦截。
            self.tool_policy_context.completed_workflows.add("visible_browser_launched")  # 新增代码+VisibleBrowser验收: 标记可见浏览器会话已启动；若没有这行代码，策略层不知道可以放行普通页面工具。
            self._load_visible_browser_tools_after_launch()  # 新增代码+VisibleBrowser验收: 启动成功后补加载 browser_automation 能力包；若没有这行代码，下一轮模型工具池仍缺 browser_open。
            self._record_observation("visible_browser_launched", {"tool_name": tool_call.name})  # 新增代码+VisibleBrowser验收: 记录可见浏览器 workflow 完成；若没有这行代码，真实验收日志缺少为什么放行的证据。
        if catalog_tool.server_name == "browser_automation" and catalog_tool.original_name == "browser_disconnect_real_chrome":  # 新增代码+RealChromeWorkflow: 断开工具执行后需要清连接状态；若没有这行代码，策略会误以为仍连接真实 Chrome
            self.tool_policy_context.completed_workflows.discard("real_chrome_connected")  # 新增代码+RealChromeWorkflow: 移除真实 Chrome 已连接状态；若没有这行代码，断开后仍可能放行页面操作
            self._record_observation("real_chrome_disconnected", {"tool_name": tool_call.name})  # 新增代码+ObservationV1: 记录真实 Chrome 断开事件；若没有这行代码，审计无法还原连接生命周期

    def _real_browser_customer_mode_active(self) -> bool:  # 新增代码+真实浏览器客户模式: 判断本轮是否可以启用公开查询自动授权；若没有这行代码，权限分支会重复拼条件且容易放宽边界
        return real_browser_customer_mode_active(self.real_chrome_requested, self.real_browser_information_task_requested)  # 修改代码+BrowserSplit: 委托 browser.permissions 判断客户模式是否激活；若没有这行代码，终端和 MCP 的客户模式条件会继续重复。

    def _real_browser_customer_auto_approve_reason(self, tool_call: ToolCall) -> str:  # 新增代码+真实浏览器客户模式: 给白名单真实浏览器工具返回自动授权原因；若没有这行代码，_execute_mcp_tool 无法区分客户模式和普通高风险权限
        real_reason = real_browser_customer_auto_approve_reason(tool_call.name, tool_call.arguments, customer_mode_active=self._real_browser_customer_mode_active())  # 修改代码+自然可见浏览器路由: 先保留真实 Chrome 客户模式白名单；若没有这行代码，显式真实浏览器查询会回归多次授权。
        if real_reason:  # 新增代码+自然可见浏览器路由: 如果真实 Chrome 白名单已命中就直接使用；若没有这行代码，后续普通浏览器规则可能覆盖真实 profile 审计原因。
            return real_reason  # 新增代码+自然可见浏览器路由: 返回真实 Chrome 授权原因；若没有这行代码，调用方拿不到既有客户模式结果。
        return visible_browser_customer_auto_approve_reason(tool_call.name, tool_call.arguments, customer_mode_active=self.visible_browser_information_task_requested)  # 新增代码+自然可见浏览器路由: 普通实时查询走独立 Chromium 白名单；若没有这行代码，精准 prompt 会被大量 y/N 打断。

    def _real_browser_customer_progress_message(self, tool_call: ToolCall) -> str:  # 修改代码+Stage14硬清理: 恢复真实浏览器客户模式进度提示的新模块委托函数；若没有这行代码，_execute_mcp_tool 会调用不存在的方法而中断真实浏览器任务
        return real_browser_customer_progress_message(tool_call.name, tool_call.arguments)  # 修改代码+Stage14硬清理: 委托 browser.permissions 生成进度文案；若没有这行代码，进度提示逻辑会重新散落在巨型 agent 文件里

    def _print_real_browser_customer_progress(self, message: str) -> None:  # 新增代码+真实浏览器客户模式: 统一打印客户可见进度行；若没有这行代码，多个工具分支会重复 print 格式
        if message:  # 新增代码+真实浏览器客户模式: 只有非空消息才打印；若没有这行代码，空消息可能产生无意义空行
            print(f"Agent > {message}", flush=True)  # 新增代码+真实浏览器客户模式: 立即把进度显示到真实终端；若没有这行代码，用户看不到 agent 正在做什么

    def _execute_mcp_tool(self, tool_call: ToolCall) -> str:  # 新增代码+MCP接入LearningAgent: 执行 MCP registry 工具并统一处理权限与异常；若省略: _execute_tool 无法安全调用外部 MCP 工具
        sanitizer = getattr(self.mcp_tool_registry, "sanitize_tool_arguments", None)  # 新增代码+MCP参数清洗: 读取 registry 的参数清洗能力；若省略: 授权提示会展示模型混入的无关字段
        safe_arguments = sanitizer(tool_call.name, tool_call.arguments) if callable(sanitizer) else dict(tool_call.arguments)  # 新增代码+MCP参数清洗: 先按工具 schema 清洗参数；若省略: 用户会继续看到 status/action/confirm_real_profile 这类串味字段
        safe_tool_call = ToolCall(name=tool_call.name, arguments=safe_arguments, call_id=tool_call.call_id)  # 新增代码+MCP参数清洗: 构造用于提示和调用的安全 ToolCall；若省略: 权限文本和实际调用可能用的不是同一份参数
        denial_key = self._tool_denial_key(safe_tool_call)  # 新增代码+ToolPolicyV2: 基于清洗后的 ToolCall 计算拒绝记忆指纹；若没有这行代码，多余参数会污染去重或导致同一请求重复弹窗
        if denial_key in self.permission_denials:  # 新增代码+ToolPolicyV2: 检查同一工具和参数是否已经被用户拒绝；若没有这行代码，agent 会反复请求相同权限
            self._record_mcp_call_progress(safe_tool_call, "permission_denied_cached", safe_arguments, "same sanitized arguments were denied before")  # 新增代码+MCPProgress: 记录命中拒绝记忆的进度；若没有这行代码，审计只能看到最终失败文本
            return f"{tool_call.name} 失败：之前已被用户拒绝，同一工具和参数不会重复请求权限。"  # 新增代码+ToolPolicyV2: 直接返回拒绝记忆结果；若没有这行代码，用户会被同一被拒操作反复打断
        auto_approve_reason = self._real_browser_customer_auto_approve_reason(safe_tool_call)  # 新增代码+真实浏览器客户模式: 判断本工具是否命中真实浏览器公开查询自动授权白名单；若没有这行代码，客户模式仍会每步弹 y/N
        if auto_approve_reason:  # 新增代码+真实浏览器客户模式: 命中自动授权时跳过人工 input；若没有这行代码，白名单判断结果不会生效
            self._record_mcp_call_progress(safe_tool_call, "permission_auto_approved", safe_arguments, auto_approve_reason)  # 新增代码+真实浏览器客户模式: 记录自动授权进度；若没有这行代码，审计无法解释为什么没有 permission_required
            self._print_real_browser_customer_progress(self._real_browser_customer_progress_message(safe_tool_call))  # 新增代码+真实浏览器客户模式: 向真实终端打印下一步操作；若没有这行代码，用户看不到 agent 正在思考和操作
        else:  # 新增代码+真实浏览器客户模式: 未命中白名单时保持原人工权限流程；若没有这行代码，敏感工具可能绕过用户确认
            action = self._format_mcp_permission_action(safe_tool_call)  # 修改代码+MCP参数清洗: 用清洗后的参数生成授权说明；若省略: 截图里的多余字段会继续误导用户
            self._record_mcp_call_progress(safe_tool_call, "permission_requested", safe_arguments, "")  # 新增代码+MCPProgress: 记录即将请求 MCP 工具权限；若没有这行代码，权限流缺少结构化进度
            if not self.ask_permission(action):  # 新增代码+MCP接入LearningAgent: 调用外部 MCP 工具前请求用户确认；若省略: agent 会绕过权限边界执行外部工具
                self.permission_denials.add(denial_key)  # 新增代码+ToolPolicyV2: 保存本次用户拒绝的稳定指纹；若没有这行代码，下次相同请求仍会再次弹权限确认
                self._record_mcp_call_progress(safe_tool_call, "permission_denied", safe_arguments, "user denied MCP tool call")  # 新增代码+MCPProgress: 记录用户拒绝本次权限；若没有这行代码，审计看不到拒绝发生在哪一步
                return f"用户拒绝了操作：{action}"  # 新增代码+MCP接入LearningAgent: 权限拒绝时返回可读结果给模型；若省略: 模型不知道工具调用被用户拒绝而可能继续误判
        try:  # 新增代码+MCP接入LearningAgent: 捕获 MCP registry 或外部工具调用异常；若省略: 单个 MCP 工具失败会中断整个 agent.run
            self._record_mcp_call_progress(safe_tool_call, "started", safe_arguments, "")  # 新增代码+MCPProgress: 记录外部 MCP 工具正式开始执行；若没有这行代码，进度只停留在权限阶段
            result_text = self.mcp_tool_registry.call_tool(safe_tool_call.name, safe_tool_call.arguments)  # 修改代码+MCPProgress: 调用 registry 时保存结果以便记录完成事件；若没有这行代码，无法在返回前更新 workflow 和 progress
            self._record_mcp_call_progress(safe_tool_call, "completed", safe_arguments, f"chars={len(result_text)}")  # 新增代码+MCPProgress: 记录 MCP 工具完成和输出长度；若没有这行代码，大输出审计缺少完成状态
            self._update_workflows_after_mcp_tool(safe_tool_call, result_text)  # 新增代码+RealChromeWorkflow: 根据 profile status/connect 结果更新 workflow 状态；若没有这行代码，真实 Chrome 前置检查不会解锁后续连接
            self._record_browser_runtime_status_after_mcp_tool(safe_tool_call, "completed")  # 新增代码+BrowserRuntimeStatus: 浏览器 MCP 工具完成后把最新 browser run 镜像到统一状态事件；若没有这行代码，BrowserRuntimeStore 会成为旁路系统。
            return result_text  # 修改代码+MCPProgress: 返回真实 MCP 工具结果；若没有这行代码，调用方拿不到外部工具输出
        except Exception as error:  # 新增代码+MCP接入LearningAgent: 把外部异常转换成可读文本；若省略: 用户和模型会看到 Python 堆栈或直接崩溃
            self._record_mcp_call_progress(safe_tool_call, "failed", safe_arguments, str(error))  # 新增代码+MCPProgress: 记录 MCP 工具失败和错误摘要；若没有这行代码，结构化审计无法追踪外部失败
            self._record_browser_runtime_status_after_mcp_tool(safe_tool_call, "failed")  # 新增代码+BrowserRuntimeStatus: 浏览器 MCP 工具失败后也尝试镜像 browser run；若没有这行代码，失败浏览器任务可能从状态生态消失。
            return f"MCP 工具调用失败：{error}"  # 新增代码+MCP接入LearningAgent: 返回清晰失败原因给模型；若省略: MCP 异常缺少可恢复反馈

    def _record_browser_runtime_status_after_mcp_tool(self, tool_call: ToolCall, state: str) -> None:  # 新增代码+BrowserRuntimeStatus: 将 browser runtime store 最新 run 镜像进 observation 和 status event；若没有这行代码，主循环看不见浏览器 durable run。
        catalog_tool = self._find_catalog_tool(tool_call.name)  # 新增代码+BrowserRuntimeStatus: 读取工具目录元数据以判断是否 browser_automation；若没有这行代码，所有 MCP 工具都会被误扫描 browser runtime。
        if catalog_tool is None or catalog_tool.server_name != "browser_automation":  # 新增代码+BrowserRuntimeStatus: 只处理浏览器自动化 MCP server；若没有这行代码，搜索、文件、命令工具会产生无意义扫描。
            return  # 新增代码+BrowserRuntimeStatus: 非浏览器工具直接退出；若没有这行代码，函数会继续访问不存在的 browser run。
        try:  # 新增代码+BrowserRuntimeStatus: status 镜像不能破坏真实工具结果返回；若没有这行代码，状态写入异常会拖垮浏览器任务。
            from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+BrowserRuntimeStatus: 延迟导入 browser runtime store；若没有这行代码，agent 无法读取 browser run 文件。
            from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+BrowserRuntimeStatus: 延迟导入统一状态事件 store；若没有这行代码，UI/SDK 仍看不到 browser runtime。
            browser_runtime_root = self.workspace / "learning_agent" / "memory" / "browser_runtime"  # 新增代码+BrowserRuntimeStatus: 使用 browser MCP server 约定的生产路径；若没有这行代码，agent 会扫描错误目录。
            browser_store = BrowserRuntimeStore(browser_runtime_root)  # 新增代码+BrowserRuntimeStatus: 创建读取端 store；若没有这行代码，无法结构化读取 run 和 event。
            run_ids = browser_store.list_run_ids()  # 新增代码+BrowserRuntimeStatus: 列出当前 workspace 下的 browser run；若没有这行代码，无法找到最新任务。
            if not run_ids:  # 新增代码+BrowserRuntimeStatus: 没有 browser run 时直接退出；若没有这行代码，空列表 max 会抛错。
                return  # 新增代码+BrowserRuntimeStatus: 无 run 可镜像时保持工具结果不受影响；若没有这行代码，非落盘工具会失败。
            latest_run_id = max(run_ids, key=lambda run_id: browser_store.run_path(run_id).stat().st_mtime)  # 新增代码+BrowserRuntimeStatus: 按文件修改时间选择刚刚写入的 run；若没有这行代码，多次浏览器调用会镜像旧 run。
            browser_run = browser_store.load_run(latest_run_id)  # 新增代码+BrowserRuntimeStatus: 读取最新 browser run 对象；若没有这行代码，状态事件只能写文件名不能写状态。
            browser_events = browser_store.tail_events(browser_run.run_id, limit=10)  # 新增代码+BrowserRuntimeStatus: 读取最近 browser runtime 事件；若没有这行代码，状态事件缺少 started/completed 证据。
            event_types = [str(event.get("event_type", "")) for event in browser_events]  # 新增代码+BrowserRuntimeStatus: 提取事件名列表；若没有这行代码，UI/SDK 无法快速显示浏览器时间线。
            payload = {"browser_run_id": browser_run.run_id, "browser_run_status": browser_run.status, "browser_current_stage_id": browser_run.current_stage_id, "browser_action_ids": list(browser_run.action_ids), "browser_observation_ids": list(browser_run.observation_ids), "browser_event_types": event_types, "mcp_tool_name": tool_call.name, "mirror_state": state}  # 新增代码+BrowserRuntimeStatus: 构造状态事件正文；若没有这行代码，状态生态拿不到 browser run 关键字段。
            self._record_observation("browser_runtime_run_detected", payload)  # 新增代码+BrowserRuntimeStatus: 同步写 observation，方便 debug/latest_run_readable 看到 browser run；若没有这行代码，旧调试入口看不到镜像结果。
            StatusEventStore(self.workspace / "memory" / "status").append("browser_runtime_event", payload, run_id=browser_run.run_id)  # 新增代码+BrowserRuntimeStatus: 写入统一状态事件流；若没有这行代码，CLI/API/SDK 无法订阅 browser runtime。
        except Exception as error:  # 新增代码+BrowserRuntimeStatus: 镜像失败只记录 observation，不影响工具输出；若没有这行代码，状态写入问题会破坏真实浏览器操作。
            self._record_observation("browser_runtime_status_mirror_failed", {"tool_name": tool_call.name, "state": state, "error": str(error)})  # 新增代码+BrowserRuntimeStatus: 留下镜像失败原因；若没有这行代码，状态缺失会无迹可查。

    def _listen_mcp_stream(self, arguments: dict[str, Any]) -> str:  # 修改代码+Stage14硬清理: 恢复独立 MCP stream 监听函数边界；若没有这行代码，listen_mcp_stream 会被误塞进 MCP 工具执行函数导致语法和运行都失败
        server_name = str(arguments.get("server", "") or "").strip()  # 新增代码+MCPStream: 读取并清理必填 server 参数；若省略: 无法确定要监听哪个 MCP server
        if not server_name:  # 新增代码+MCPStream: 检查 server 是否为空；若省略: 空 server 会进入 registry 并产生较难懂错误
            return "listen_mcp_stream 失败：缺少 server 参数。"  # 新增代码+MCPStream: 返回清楚缺参错误；若省略: 模型难以修正工具调用参数
        if not self.mcp_tools_enabled:  # 新增代码+MCPStream: 检查 MCP 是否已启动或可用；若省略: 拒绝启动后仍可能尝试访问外部 stream
            detail = self.mcp_start_error or "MCP 工具尚未启用。"  # 新增代码+MCPStream: 选择最清楚的不可用原因；若省略: 返回信息会缺少排查线索
            return f"MCP stream 不可用：{detail}"  # 新增代码+MCPStream: 返回可读不可用结果；若省略: 模型会把 stream 不可用误解为未知工具
        max_events = 5  # 新增代码+MCPStream: 设置默认最多读取 5 条事件；若省略: 非法或缺省参数没有安全兜底
        try:  # 修改代码+MCPStream: 捕获 max_events 转换错误和无穷大溢出；若省略: 模型传入字符串、对象或 inf 会抛裸异常
            parsed_max_events = int(arguments.get("max_events", max_events))  # 新增代码+MCPStream: 把 max_events 转成整数；若省略: registry 可能收到非数字导致底层错误
            if 1 <= parsed_max_events <= 20:  # 新增代码+MCPStream: 检查事件数在 1 到 20 内；若省略: 过大事件数可能撑爆上下文或等待过久
                max_events = parsed_max_events  # 新增代码+MCPStream: 使用合法事件数；若省略: 用户传入的合法限制不会生效
        except (TypeError, ValueError, OverflowError):  # 修改代码+MCPStream: 处理无法转成整数或无穷大溢出的非法值；若省略: inf 会触发 OverflowError 中断整个工具调用
            max_events = 5  # 新增代码+MCPStream: 非法值回退默认 5；若省略: 后续变量可能不存在或保留危险值
        timeout_seconds = 2.0  # 新增代码+MCPStream: 设置默认监听等待 2 秒；若省略: 非法或缺省参数没有安全兜底
        try:  # 新增代码+MCPStream: 捕获 timeout_seconds 转换错误；若省略: 模型传入字符串或对象会抛裸异常
            parsed_timeout_seconds = float(arguments.get("timeout_seconds", timeout_seconds))  # 新增代码+MCPStream: 把 timeout_seconds 转成浮点数；若省略: registry 可能收到非数字导致底层错误
            if parsed_timeout_seconds != parsed_timeout_seconds or parsed_timeout_seconds in {float("inf"), float("-inf")}:  # 修改代码+MCPStream: 拒绝 nan 和正负无穷大；若省略: nan 可能绕过范围判断后留下不清楚的非法超时
                raise ValueError("timeout_seconds 必须是有限数字")  # 修改代码+MCPStream: 把非有限数字转入统一兜底分支；若省略: 后续无法稳定回退默认 2.0
            if 0.1 <= parsed_timeout_seconds <= 10.0:  # 新增代码+MCPStream: 检查等待时间在 0.1 到 10 秒内；若省略: 过长等待会卡住工具调用
                timeout_seconds = parsed_timeout_seconds  # 新增代码+MCPStream: 使用合法等待时间；若省略: 用户传入的合法限制不会生效
        except (TypeError, ValueError):  # 新增代码+MCPStream: 处理无法转成浮点数的非法值；若省略: 非法 timeout_seconds 会中断整个工具调用
            timeout_seconds = 2.0  # 新增代码+MCPStream: 非法值回退默认 2.0；若省略: 后续变量可能不存在或保留危险值
        raw_resume = arguments.get("resume", True)  # 新增代码+MCPStream: 读取 resume 参数并默认开启；若省略: 缺省调用无法按要求自动续传
        if isinstance(raw_resume, bool):  # 新增代码+MCPStream: 直接支持布尔 resume；若省略: true/false 会被字符串逻辑误处理
            resume = raw_resume  # 新增代码+MCPStream: 保留调用方给出的布尔值；若省略: 用户无法明确关闭或开启续传
        elif isinstance(raw_resume, str):  # 新增代码+MCPStream: 支持常见字符串开关；若省略: 模型传 "false" 时仍会被当成 True
            resume = raw_resume.strip().lower() not in {"false", "0", "no", "off"}  # 新增代码+MCPStream: false/0/no/off 视为 False，其余视为 True；若省略: 字符串兼容规则不会生效
        else:  # 新增代码+MCPStream: 处理数字、None 或其他类型；若省略: 非字符串非布尔值的语义不清楚
            resume = True  # 新增代码+MCPStream: 其他类型按默认 True 处理；若省略: 非法 resume 可能导致底层收到奇怪类型
        permission_payload = {"server": server_name, "max_events": max_events, "timeout_seconds": timeout_seconds, "resume": resume}  # 新增代码+MCPStream: 构造权限提示里的参数快照；若省略: 用户看不到本次监听的关键边界
        action = f"监听 MCP stream\n参数：{json.dumps(permission_payload, ensure_ascii=False, indent=2)}"  # 新增代码+MCPStream: 生成 stream 监听权限说明；若省略: ask_permission 缺少 server、事件数、超时和续传信息
        if not self.ask_permission(action):  # 新增代码+MCPStream: 监听外部 MCP stream 前请求用户确认；若省略: 外部 stream 读取会绕过权限边界
            return f"用户拒绝了操作：{action}"  # 新增代码+MCPStream: 权限拒绝时返回可读结果；若省略: 模型不知道 stream 监听被拒绝
        try:  # 新增代码+MCPStream: 捕获 registry 或外部 server 的 stream 监听异常；若省略: 单个 MCP stream 失败会中断整个 agent
            text = self.mcp_tool_registry.listen_stream(server_name, max_events=max_events, timeout_seconds=timeout_seconds, resume=resume)  # 新增代码+MCPStream: 调用 registry 监听目标 server；若省略: 权限确认后不会真正读取 stream
        except Exception as error:  # 新增代码+MCPStream: 把外部异常转换成可读文本；若省略: 用户和模型会看到 Python 堆栈或直接崩溃
            return f"listen_mcp_stream 失败：{error}"  # 新增代码+MCPStream: 返回清晰失败原因；若省略: 模型无法判断下一步怎么修复
        return f"listen_mcp_stream 成功：server={server_name}\n{text}"  # 新增代码+MCPStream: 返回带 server 和正文的成功结果；若省略: 工具结果缺少来源或 stream 内容

    def _list_mcp_resources(self, arguments: dict[str, Any]) -> str:  # 新增代码+MCPResource: 执行内置 list_mcp_resources 工具；若省略: 模型无法从内置工具列 MCP 资源
        if not self.mcp_tools_enabled:  # 新增代码+MCPResource: 检查 MCP 是否已启动或可用；若省略: 拒绝启动后仍可能尝试访问外部资源
            detail = self.mcp_start_error or "MCP 工具尚未启用。"  # 新增代码+MCPResource: 选择最清楚的不可用原因；若省略: 返回信息会缺少排查线索
            return f"MCP resources 不可用：{detail}"  # 新增代码+MCPResource: 返回可读不可用结果；若省略: 模型会把资源不可用误解为未知工具
        raw_server = arguments.get("server")  # 新增代码+MCPResource: 读取可选 server 参数；若省略: 无法支持只列某个 MCP server
        server_name = str(raw_server).strip() if raw_server is not None else ""  # 新增代码+MCPResource: 清理 server 参数并允许省略；若省略: None 或空白 server 可能被误当真实名称
        selected_server = server_name or None  # 新增代码+MCPResource: 空字符串转成 None 表示列所有 server；若省略: registry 会查找名为空的 server
        max_results = self._tool_search_max_results(arguments.get("max_results"))  # 新增代码+MCPResource: 复用 1 到 20 的结果数限制；若省略: resources 太多可能撑爆上下文
        permission_payload = {"server": selected_server, "max_results": max_results}  # 新增代码+MCPResource: 构造权限提示里的参数快照；若省略: 用户看不到本次要列哪些资源
        action = f"列出 MCP resources\n参数：{json.dumps(permission_payload, ensure_ascii=False, indent=2)}"  # 新增代码+MCPResource: 生成资源列表权限说明；若省略: ask_permission 缺少可读操作描述
        if not self.ask_permission(action):  # 新增代码+MCPResource: 列出外部 MCP 资源前请求用户确认；若省略: 外部资源枚举会绕过权限边界
            return f"用户拒绝了操作：{action}"  # 新增代码+MCPResource: 权限拒绝时返回可读结果；若省略: 模型不知道资源列表被拒绝
        try:  # 新增代码+MCPResource: 捕获 registry 或外部 server 的资源列表异常；若省略: 单个 MCP server 失败会中断整个 agent
            resources = self.mcp_tool_registry.list_resources(selected_server)  # 新增代码+MCPResource: 调用 registry 聚合 resources/list；若省略: 权限确认后不会真正读取资源列表
        except Exception as error:  # 新增代码+MCPResource: 把外部异常转换成可读文本；若省略: 用户和模型会看到 Python 堆栈或直接崩溃
            return f"list_mcp_resources 失败：{error}"  # 新增代码+MCPResource: 返回清晰失败原因；若省略: 模型无法判断下一步怎么修复
        visible_resources = resources[:max_results]  # 新增代码+MCPResource: 截取最多 max_results 条资源；若省略: 大量 resources 可能撑爆上下文
        if not visible_resources:  # 新增代码+MCPResource: 处理没有资源的情况；若省略: 空结果会返回只有标题的模糊文本
            return "list_mcp_resources 成功：没有找到 MCP resources。"  # 新增代码+MCPResource: 明确说明列表为空；若省略: 模型可能误以为工具失败
        lines = [f"list_mcp_resources 成功：找到 {len(resources)} 个 resource，显示前 {len(visible_resources)} 个。"]  # 新增代码+MCPResource: 构造资源列表标题；若省略: 模型不知道数量和截断情况
        for index, resource in enumerate(visible_resources, start=1):  # 新增代码+MCPResource: 逐条格式化资源信息；若省略: 资源对象无法变成人类和模型可读文本
            name = str(resource.get("name", "") or "(无名称)")  # 新增代码+MCPResource: 读取资源名称并兜底；若省略: 缺名称资源展示不友好
            uri = str(resource.get("uri", "") or "(无 uri)")  # 新增代码+MCPResource: 读取资源 uri 并兜底；若省略: 模型不知道 read_mcp_resource 要传什么 uri
            server = str(resource.get("server", "") or "(未知 server)")  # 新增代码+MCPResource: 读取来源 server 并兜底；若省略: 模型不知道 read_mcp_resource 要传什么 server
            mime_type = str(resource.get("mimeType", "") or resource.get("mime_type", "") or "(未知类型)")  # 新增代码+MCPResource: 读取资源 MIME 类型并兼容字段名；若省略: 模型缺少判断资源内容格式的信息
            description = str(resource.get("description", "") or "(无说明)")  # 新增代码+MCPResource: 读取资源说明并兜底；若省略: 模型缺少判断资源用途的信息
            lines.append(f"{index}. {name}")  # 新增代码+MCPResource: 输出资源序号和名称；若省略: 结果清单不易阅读
            lines.append(f"   server：{server}")  # 新增代码+MCPResource: 输出读取时必需的 server；若省略: 模型后续无法精确读取资源
            lines.append(f"   uri：{uri}")  # 新增代码+MCPResource: 输出读取时必需的 uri；若省略: 模型后续无法精确读取资源
            lines.append(f"   mimeType：{mime_type}")  # 新增代码+MCPResource: 输出资源类型；若省略: 模型不知道内容可能是 markdown、json 或其他格式
            lines.append(f"   说明：{description}")  # 新增代码+MCPResource: 输出资源说明；若省略: 模型缺少选择资源的语义依据
        return "\n".join(lines)  # 新增代码+MCPResource: 返回完整资源列表文本；若省略: 工具无法把结果交回模型

    def _read_mcp_resource(self, arguments: dict[str, Any]) -> str:  # 新增代码+MCPResource: 执行内置 read_mcp_resource 工具；若省略: 模型无法从内置工具读取 MCP 资源正文
        if not self.mcp_tools_enabled:  # 新增代码+MCPResource: 检查 MCP 是否已启动或可用；若省略: 拒绝启动后仍可能尝试读取外部资源
            detail = self.mcp_start_error or "MCP 工具尚未启用。"  # 新增代码+MCPResource: 选择最清楚的不可用原因；若省略: 返回信息会缺少排查线索
            return f"MCP resources 不可用：{detail}"  # 新增代码+MCPResource: 返回可读不可用结果；若省略: 模型会把资源不可用误解为未知工具
        server_name = str(arguments.get("server", "") or "").strip()  # 新增代码+MCPResource: 读取并清理必填 server 参数；若省略: 无法确定资源来自哪个 MCP server
        uri = str(arguments.get("uri", "") or "").strip()  # 新增代码+MCPResource: 读取并清理必填 uri 参数；若省略: 无法确定要读取哪个资源
        if not server_name:  # 新增代码+MCPResource: 检查 server 是否为空；若省略: 空 server 会进入 registry 并产生较难懂错误
            return "read_mcp_resource 失败：缺少 server 参数。"  # 新增代码+MCPResource: 返回清楚缺参错误；若省略: 模型难以修正工具调用参数
        if not uri:  # 新增代码+MCPResource: 检查 uri 是否为空；若省略: 空 uri 会进入外部 server 并产生较难懂错误
            return "read_mcp_resource 失败：缺少 uri 参数。"  # 新增代码+MCPResource: 返回清楚缺参错误；若省略: 模型难以修正工具调用参数
        max_chars = self._parse_max_chars(arguments.get("max_chars"))  # 新增代码+MCPResource: 解析最大返回字符数；若省略: 大资源可能撑爆上下文
        permission_payload = {"server": server_name, "uri": uri, "max_chars": max_chars}  # 新增代码+MCPResource: 构造权限提示里的参数快照；若省略: 用户看不到本次读取哪个资源
        action = f"读取 MCP resource\n参数：{json.dumps(permission_payload, ensure_ascii=False, indent=2)}"  # 新增代码+MCPResource: 生成资源读取权限说明；若省略: ask_permission 缺少可读操作描述
        if not self.ask_permission(action):  # 新增代码+MCPResource: 读取外部 MCP 资源前请求用户确认；若省略: 外部资源正文会绕过权限边界
            return f"用户拒绝了操作：{action}"  # 新增代码+MCPResource: 权限拒绝时返回可读结果；若省略: 模型不知道资源读取被拒绝
        try:  # 新增代码+MCPResource: 捕获 registry 或外部 server 的资源读取异常；若省略: 单个 MCP resource 失败会中断整个 agent
            text = self.mcp_tool_registry.read_resource(server_name, uri)  # 新增代码+MCPResource: 调用 registry 读取目标 resource；若省略: 权限确认后不会真正读取正文
        except Exception as error:  # 新增代码+MCPResource: 把外部异常转换成可读文本；若省略: 用户和模型会看到 Python 堆栈或直接崩溃
            return f"read_mcp_resource 失败：{error}"  # 新增代码+MCPResource: 返回清晰失败原因；若省略: 模型无法判断下一步怎么修复
        truncated_text = text[:max_chars]  # 新增代码+MCPResource: 按 max_chars 截断资源正文；若省略: 长资源可能撑爆上下文
        if len(text) > max_chars:  # 新增代码+MCPResource: 检查正文是否被截断；若省略: 用户和模型不知道返回内容是否完整
            truncated_text += "\n...[MCP resource 内容过长，已截断]..."  # 新增代码+MCPResource: 添加截断提示；若省略: 模型可能误以为读取了完整资源
        return f"read_mcp_resource 成功：server={server_name} uri={uri}\n{truncated_text}"  # 新增代码+MCPResource: 返回带来源和正文的结果；若省略: 工具结果缺少上下文或正文

    def _list_mcp_prompts(self, arguments: dict[str, Any]) -> str:  # 新增代码+MCPPrompt: 执行内置 list_mcp_prompts 工具；若省略: 模型无法从内置工具列 MCP prompts
        if not self.mcp_tools_enabled:  # 新增代码+MCPPrompt: 检查 MCP 是否已启动或可用；若省略: 拒绝启动后仍可能尝试访问外部 prompts
            detail = self.mcp_start_error or "MCP 工具尚未启用。"  # 新增代码+MCPPrompt: 选择最清楚的不可用原因；若省略: 返回信息会缺少排查线索
            return f"MCP prompts 不可用：{detail}"  # 新增代码+MCPPrompt: 返回可读不可用结果；若省略: 模型会把 prompt 不可用误解为未知工具
        raw_server = arguments.get("server")  # 新增代码+MCPPrompt: 读取可选 server 参数；若省略: 无法支持只列某个 MCP server
        server_name = str(raw_server).strip() if raw_server is not None else ""  # 新增代码+MCPPrompt: 清理 server 参数并允许省略；若省略: None 或空白 server 可能被误当真实名称
        selected_server = server_name or None  # 新增代码+MCPPrompt: 空字符串转成 None 表示列所有 server；若省略: registry 会查找名为空的 server
        max_results = self._tool_search_max_results(arguments.get("max_results"))  # 新增代码+MCPPrompt: 复用 1 到 20 的结果数限制；若省略: prompts 太多可能撑爆上下文
        permission_payload = {"server": selected_server, "max_results": max_results}  # 新增代码+MCPPrompt: 构造权限提示里的参数快照；若省略: 用户看不到本次要列哪些 prompts
        action = f"列出 MCP prompts\n参数：{json.dumps(permission_payload, ensure_ascii=False, indent=2)}"  # 新增代码+MCPPrompt: 生成 prompt 列表权限说明；若省略: ask_permission 缺少可读操作描述
        if not self.ask_permission(action):  # 新增代码+MCPPrompt: 列出外部 MCP prompts 前请求用户确认；若省略: 外部 prompt 枚举会绕过权限边界
            return f"用户拒绝了操作：{action}"  # 新增代码+MCPPrompt: 权限拒绝时返回可读结果；若省略: 模型不知道 prompt 列表被拒绝
        try:  # 新增代码+MCPPrompt: 捕获 registry 或外部 server 的 prompt 列表异常；若省略: 单个 MCP server 失败会中断整个 agent
            prompts = self.mcp_tool_registry.list_prompts(selected_server)  # 新增代码+MCPPrompt: 调用 registry 聚合 prompts/list；若省略: 权限确认后不会真正读取 prompt 列表
        except Exception as error:  # 新增代码+MCPPrompt: 把外部异常转换成可读文本；若省略: 用户和模型会看到 Python 堆栈或直接崩溃
            return f"list_mcp_prompts 失败：{error}"  # 新增代码+MCPPrompt: 返回清晰失败原因；若省略: 模型无法判断下一步怎么修复
        visible_prompts = prompts[:max_results]  # 新增代码+MCPPrompt: 截取最多 max_results 条 prompt；若省略: 大量 prompts 可能撑爆上下文
        if not visible_prompts:  # 新增代码+MCPPrompt: 处理没有 prompts 的情况；若省略: 空结果会返回只有标题的模糊文本
            return "list_mcp_prompts 成功：没有找到 MCP prompts。"  # 新增代码+MCPPrompt: 明确说明列表为空；若省略: 模型可能误以为工具失败
        lines = [f"list_mcp_prompts 成功：找到 {len(prompts)} 个 prompt，显示前 {len(visible_prompts)} 个。"]  # 新增代码+MCPPrompt: 构造 prompt 列表标题；若省略: 模型不知道数量和截断情况
        for index, prompt in enumerate(visible_prompts, start=1):  # 新增代码+MCPPrompt: 逐条格式化 prompt 信息；若省略: prompt 对象无法变成人类和模型可读文本
            name = str(prompt.get("name", "") or "(无名称)")  # 新增代码+MCPPrompt: 读取 prompt 名称并兜底；若省略: 模型不知道 read_mcp_prompt 要传什么 name
            server = str(prompt.get("server", "") or "(未知 server)")  # 新增代码+MCPPrompt: 读取来源 server 并兜底；若省略: 模型不知道 read_mcp_prompt 要传什么 server
            description = str(prompt.get("description", "") or "(无说明)")  # 新增代码+MCPPrompt: 读取 prompt 说明并兜底；若省略: 模型缺少判断 prompt 用途的信息
            argument_names = self._mcp_prompt_argument_names(prompt)  # 新增代码+MCPPrompt: 格式化 prompt 参数名和必填性；若省略: 模型不知道如何构造 prompt_arguments
            lines.append(f"{index}. {name}")  # 新增代码+MCPPrompt: 输出 prompt 序号和名称；若省略: 结果清单不易阅读
            lines.append(f"   server：{server}")  # 新增代码+MCPPrompt: 输出读取时必需的 server；若省略: 模型后续无法精确读取 prompt
            lines.append(f"   arguments：{', '.join(argument_names) if argument_names else '(无参数)'}")  # 新增代码+MCPPrompt: 输出 prompt 参数列表；若省略: 带参数 prompt 无法被正确填充
            lines.append(f"   说明：{description}")  # 新增代码+MCPPrompt: 输出 prompt 说明；若省略: 模型缺少选择 prompt 的语义依据
        return "\n".join(lines)  # 新增代码+MCPPrompt: 返回完整 prompt 列表文本；若省略: 工具无法把结果交回模型

    def _read_mcp_prompt(self, arguments: dict[str, Any]) -> str:  # 新增代码+MCPPrompt: 执行内置 read_mcp_prompt 工具；若省略: 模型无法从内置工具读取 MCP prompt 正文
        if not self.mcp_tools_enabled:  # 新增代码+MCPPrompt: 检查 MCP 是否已启动或可用；若省略: 拒绝启动后仍可能尝试读取外部 prompt
            detail = self.mcp_start_error or "MCP 工具尚未启用。"  # 新增代码+MCPPrompt: 选择最清楚的不可用原因；若省略: 返回信息会缺少排查线索
            return f"MCP prompts 不可用：{detail}"  # 新增代码+MCPPrompt: 返回可读不可用结果；若省略: 模型会把 prompt 不可用误解为未知工具
        server_name = str(arguments.get("server", "") or "").strip()  # 新增代码+MCPPrompt: 读取并清理必填 server 参数；若省略: 无法确定 prompt 来自哪个 MCP server
        prompt_name = str(arguments.get("name", "") or "").strip()  # 新增代码+MCPPrompt: 读取并清理必填 name 参数；若省略: 无法确定要读取哪个 prompt
        if not server_name:  # 新增代码+MCPPrompt: 检查 server 是否为空；若省略: 空 server 会进入 registry 并产生较难懂错误
            return "read_mcp_prompt 失败：缺少 server 参数。"  # 新增代码+MCPPrompt: 返回清楚缺参错误；若省略: 模型难以修正工具调用参数
        if not prompt_name:  # 新增代码+MCPPrompt: 检查 prompt 名称是否为空；若省略: 空名称会进入外部 server 并产生较难懂错误
            return "read_mcp_prompt 失败：缺少 name 参数。"  # 新增代码+MCPPrompt: 返回清楚缺参错误；若省略: 模型难以修正工具调用参数
        raw_prompt_arguments = arguments.get("prompt_arguments")  # 新增代码+MCPPrompt: 读取可选 prompt_arguments 参数；若省略: 带参数 prompt 无法接收模板参数
        if raw_prompt_arguments is None:  # 新增代码+MCPPrompt: 允许模型省略 prompt_arguments；若省略: 无参 prompt 可能被误判失败
            prompt_arguments: dict[str, Any] = {}  # 新增代码+MCPPrompt: 省略时使用空字典；若省略: prompts/get 参数结构不稳定
        elif isinstance(raw_prompt_arguments, dict):  # 新增代码+MCPPrompt: 只有对象类型才可作为 MCP prompt arguments；若省略: 字符串或数组会传入外部 server 造成歧义
            prompt_arguments = raw_prompt_arguments  # 新增代码+MCPPrompt: 使用模型传入的 prompt 参数对象；若省略: 用户提供的 prompt 参数会丢失
        else:  # 新增代码+MCPPrompt: 处理 prompt_arguments 类型不正确的情况；若省略: 错误类型会进入外部 server
            return "read_mcp_prompt 失败：prompt_arguments 必须是对象。"  # 新增代码+MCPPrompt: 返回清楚类型错误；若省略: 模型难以修正参数
        max_chars = self._parse_max_chars(arguments.get("max_chars"))  # 新增代码+MCPPrompt: 解析最大返回字符数；若省略: 大 prompt 可能撑爆上下文
        permission_payload = {"server": server_name, "name": prompt_name, "prompt_arguments": prompt_arguments, "max_chars": max_chars}  # 新增代码+MCPPrompt: 构造权限提示里的参数快照；若省略: 用户看不到本次读取哪个 prompt
        action = f"读取 MCP prompt\n参数：{json.dumps(permission_payload, ensure_ascii=False, indent=2)}"  # 新增代码+MCPPrompt: 生成 prompt 读取权限说明；若省略: ask_permission 缺少可读操作描述
        if not self.ask_permission(action):  # 新增代码+MCPPrompt: 读取外部 MCP prompt 前请求用户确认；若省略: 外部 prompt 正文会绕过权限边界
            return f"用户拒绝了操作：{action}"  # 新增代码+MCPPrompt: 权限拒绝时返回可读结果；若省略: 模型不知道 prompt 读取被拒绝
        try:  # 新增代码+MCPPrompt: 捕获 registry 或外部 server 的 prompt 读取异常；若省略: 单个 MCP prompt 失败会中断整个 agent
            text = self.mcp_tool_registry.read_prompt(server_name, prompt_name, prompt_arguments)  # 新增代码+MCPPrompt: 调用 registry 读取目标 prompt；若省略: 权限确认后不会真正读取正文
        except Exception as error:  # 新增代码+MCPPrompt: 把外部异常转换成可读文本；若省略: 用户和模型会看到 Python 堆栈或直接崩溃
            return f"read_mcp_prompt 失败：{error}"  # 新增代码+MCPPrompt: 返回清晰失败原因；若省略: 模型无法判断下一步怎么修复
        truncated_text = text[:max_chars]  # 新增代码+MCPPrompt: 按 max_chars 截断 prompt 正文；若省略: 长 prompt 可能撑爆上下文
        if len(text) > max_chars:  # 新增代码+MCPPrompt: 检查正文是否被截断；若省略: 用户和模型不知道返回内容是否完整
            truncated_text += "\n...[MCP prompt 内容过长，已截断]..."  # 新增代码+MCPPrompt: 添加截断提示；若省略: 模型可能误以为读取了完整 prompt
        return f"read_mcp_prompt 成功：server={server_name} name={prompt_name}\n{truncated_text}"  # 新增代码+MCPPrompt: 返回带来源和正文的结果；若省略: 工具结果缺少上下文或正文

    def _mcp_prompt_argument_names(self, prompt: dict[str, Any]) -> list[str]:  # 新增代码+MCPPrompt: 把 prompt arguments 元数据格式化成可读参数名；若省略: list_mcp_prompts 会重复复杂解析逻辑
        raw_arguments = prompt.get("arguments")  # 新增代码+MCPPrompt: 读取 MCP prompt 的 arguments 字段；若省略: 无法展示 prompt 参数要求
        if not isinstance(raw_arguments, list):  # 新增代码+MCPPrompt: 只处理标准数组形式参数；若省略: 非数组 arguments 可能导致遍历异常
            return []  # 新增代码+MCPPrompt: 非数组参数按无参数展示；若省略: 调用方需要额外判断 None 或坏类型
        argument_names: list[str] = []  # 新增代码+MCPPrompt: 准备保存参数名和必填性；若省略: 无处累积格式化结果
        for raw_argument in raw_arguments:  # 新增代码+MCPPrompt: 遍历每个 prompt 参数元数据；若省略: 参数列表永远为空
            if not isinstance(raw_argument, dict):  # 新增代码+MCPPrompt: 跳过非对象参数项；若省略: 异常 server 返回会导致 .get 崩溃
                continue  # 新增代码+MCPPrompt: 保持单个坏参数不影响其他参数；若省略: 容错路径无法继续
            argument_name = str(raw_argument.get("name", "") or "").strip()  # 新增代码+MCPPrompt: 读取并清理参数名；若省略: 输出可能包含空白或空名称
            if not argument_name:  # 新增代码+MCPPrompt: 跳过空参数名；若省略: 输出会出现无法传入的参数提示
                continue  # 新增代码+MCPPrompt: 继续处理其他参数；若省略: 单个空参数会污染结果
            required_label = "必填" if bool(raw_argument.get("required")) else "可选"  # 新增代码+MCPPrompt: 标出参数是否必填；若省略: 模型不知道哪些 prompt_arguments 必须提供
            argument_names.append(f"{argument_name}({required_label})")  # 新增代码+MCPPrompt: 保存格式化参数名；若省略: 有效参数不会出现在列表输出
        return argument_names  # 新增代码+MCPPrompt: 返回格式化参数列表；若省略: list_mcp_prompts 无法展示参数

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

    def _task(self, arguments: dict[str, Any]) -> str:  # 新增代码+TaskAgent: 执行内置 task 工具并启动同进程子 agent；若省略: 主 agent 无法委派子任务
        prompt = str(arguments.get("prompt", "") or "").strip()  # 新增代码+TaskAgent: 读取并清理子任务 prompt；若省略: 子 agent 不知道要执行什么任务
        if not prompt:  # 新增代码+TaskAgent: 检查 prompt 是否为空；若省略: 空子任务会浪费模型调用并产生模糊结果
            return "task 失败：缺少非空 prompt 参数。"  # 新增代码+TaskAgent: 返回清楚缺参错误；若省略: 模型难以修正 task 调用
        allowed_tool_names = self._task_allowed_tool_names(arguments.get("allowed_tools"))  # 新增代码+TaskAgent: 解析子 agent 工具白名单；若省略: 子 agent 无法被限制工具范围
        if isinstance(allowed_tool_names, str):  # 新增代码+TaskAgent: 字符串返回值表示白名单解析失败；若省略: 错误字符串会被当作工具集合使用
            return allowed_tool_names  # 新增代码+TaskAgent: 直接返回可读失败信息；若省略: 模型看不到 allowed_tools 的具体错误
        max_turns = self._task_max_turns(arguments.get("max_turns"))  # 新增代码+TaskAgent: 解析子 agent 最大轮次；若省略: 子任务可能无界运行或无法控制执行长度
        if isinstance(max_turns, str):  # 新增代码+TaskAgent: 字符串返回值表示 max_turns 解析失败；若省略: 错误字符串会被当作轮次数值使用
            return max_turns  # 新增代码+TaskAgent: 直接返回可读失败信息；若省略: 模型看不到 max_turns 的具体错误
        background = self._task_background_enabled(arguments.get("background"))  # 新增代码+AsyncTask: 解析 background 开关；若省略: task 无法区分同步执行和后台执行
        stop_event = threading.Event() if background else None  # 新增代码+AsyncTask: 后台任务创建取消信号，同步任务保持 None；若省略: task_stop 无法通知后台子 agent
        task_id = f"task_{secrets.token_hex(6)}"  # 新增代码+TaskLifecycle: 生成短且唯一的子任务 id；若省略: task_output/task_stop 无法引用这次子任务
        task_record = TaskRun(task_id=task_id, prompt=prompt, allowed_tool_names=allowed_tool_names, max_turns=max_turns, status="running", created_at=time.strftime("%Y-%m-%d %H:%M:%S"), background=background, stop_event=stop_event)  # 修改代码+AsyncTask: 创建运行中任务记录并保存后台/取消信息；若省略 background/stop_event: task_output/task_stop 无法管理后台子任务
        self.task_runs[task_id] = task_record  # 新增代码+TaskLifecycle: 把任务记录放入 agent 内存表；若省略: task_id 返回后也无法被 task_output/task_stop 找到
        self.task_registry.create_task(task_id=task_id, prompt=prompt, kind="agent", status="running", allowed_tool_names=sorted(allowed_tool_names), max_turns=max_turns, background=background)  # 新增代码+DurableTaskRegistry: 同步创建持久 task 记录；若没有这行代码，新 agent 实例无法恢复或审计这个子任务。
        child_prompt = self._task_child_prompt(prompt)  # 新增代码+TaskAgent: 构造给子 agent 的专用提示；若省略: 子 agent 缺少“返回摘要给主 agent”的执行边界
        child_agent = LearningAgent(  # 新增代码+TaskAgent: 创建同进程子 agent；若省略: task 只能返回文本而不能真正执行子任务
            model=self.model,  # 新增代码+TaskAgent: 子 agent 复用当前模型客户端；若省略: 子任务无法调用同一个后端模型
            workspace=self.workspace,  # 新增代码+TaskAgent: 子 agent 使用同一工作区；若省略: 子任务无法读取主项目文件
            ask_permission=self.ask_permission,  # 新增代码+TaskAgent: 子 agent 复用同一权限确认函数；若省略: 子任务写入或外部调用会绕过用户确认
            debug_log_path=self.debug_log_path,  # 新增代码+TaskAgent: 子 agent 写入同一调试日志；若省略: 子任务执行过程不易追踪
            debug_enabled=self.debug_enabled,  # 新增代码+TaskAgent: 子 agent 继承调试开关；若省略: 用户关闭日志后子任务仍可能写日志
            mcp_tool_registry=self.mcp_tool_registry,  # 修改代码+TaskAgent: 子 agent 复用父 agent 已有 MCP registry；若省略: 子 agent 无法继承已启动的外部工具
            allowed_tool_names=allowed_tool_names,  # 新增代码+TaskAgent: 把工具白名单交给子 agent；若省略: allowed_tools 参数不会生效
            inherited_mcp_tools_enabled=self.mcp_tools_enabled,  # 新增代码+TaskAgent: 继承父 agent 的 MCP 启用状态且不重复启动 server；若省略: 子 agent 可能重复请求启动 MCP
            inherited_mcp_start_error=self.mcp_start_error,  # 新增代码+TaskAgent: 继承父 agent 的 MCP 启动错误；若省略: 子 agent 无法解释 MCP 不可用原因
            stop_event=stop_event,  # 新增代码+AsyncTask: 把取消信号传给子 agent；若省略: task_stop 只能改状态而不能让子 agent 协作停止
        )  # 新增代码+TaskAgent: 子 agent 构造结束；若省略: Python 调用语法不完整
        child_agent.tool_policy_context.allow_rules = list(self.tool_policy_context.allow_rules)  # 新增代码+ToolPolicyV2: 子 agent 继承父 agent 的 allow rules；若没有这行代码，父任务显式允许的工具策略不会传给子任务
        child_agent.tool_policy_context.deny_rules = list(self.tool_policy_context.deny_rules)  # 新增代码+ToolPolicyV2: 子 agent 继承父 agent 的 deny rules；若没有这行代码，子任务可能绕过父 agent 已禁止的工具
        child_agent.tool_policy_context.loaded_skills = set(self.tool_policy_context.loaded_skills)  # 新增代码+ToolPolicyV2: 子 agent 继承父 agent 已加载的 skills；若没有这行代码，子任务可能误以为 skill 未加载并错误隐藏可用工具
        child_agent.tool_policy_context.completed_workflows = set(self.tool_policy_context.completed_workflows)  # 新增代码+ToolPolicyV2: 子 agent 继承父 agent 已完成的 workflows；若没有这行代码，子任务可能重复要求已经完成的前置流程
        child_agent.loaded_tool_names.update(self.loaded_tool_names & allowed_tool_names)  # 新增代码+ToolArchitectureV2: 只把父 agent 已经 select 且被 allowed_tools 允许的 deferred 工具继承给子 agent；若没有这行代码，子 agent 会拿不到父 agent 已加载的 MCP 工具池
        if background:  # 新增代码+AsyncTask: 后台模式走线程启动并立即返回；若省略: background=true 仍会阻塞主 agent
            task_thread = threading.Thread(target=self._run_task_record, args=(task_record, child_agent, child_prompt), daemon=True)  # 新增代码+AsyncTask: 创建后台子 agent 线程；若省略: 子任务无法异步运行
            task_record.thread = task_thread  # 新增代码+AsyncTask: 把线程对象写回任务记录；若省略: task_output/test 无法观察后台线程
            task_thread.start()  # 新增代码+AsyncTask: 真正启动后台子 agent；若省略: task 只会返回 task_id 但任务不会执行
            return f"task 成功：子 agent 已后台启动。\ntask_id={task_id}\nstatus=running\nbackground=true\n允许工具：{', '.join(sorted(allowed_tool_names)) or '(无工具)'}"  # 新增代码+AsyncTask: 立即返回后台任务 id 和状态；若省略: 主 agent 无法继续用 task_output/task_stop 管理任务
        self._run_task_record(task_record, child_agent, child_prompt)  # 新增代码+AsyncTask: 同步模式复用统一执行记录逻辑；若省略: 同步 task 和后台 task 的状态写回会分叉
        if task_record.status == "failed":  # 新增代码+AsyncTask: 如果统一执行逻辑记录失败；若省略: 同步子任务异常会被包装成成功输出
            return f"task 失败：task_id={task_id}\n子 agent 执行失败：{task_record.error}"  # 新增代码+AsyncTask: 返回带 task_id 的失败信息；若省略: 主 agent 无法继续查询失败记录
        if task_record.status == "stopped":  # 新增代码+AsyncTask: 如果同步执行期间收到取消；若省略: stopped 状态可能继续按 completed 输出
            return f"task 成功：子 agent 已停止。\ntask_id={task_id}\n原因：{task_record.error or '(未提供)'}"  # 新增代码+AsyncTask: 返回停止结果给模型；若省略: 主 agent 看不到子任务取消原因
        child_answer = task_record.output  # 新增代码+AsyncTask: 从任务记录读取统一保存的输出；若省略: 同步返回逻辑拿不到子 agent 结果
        return f"task 成功：子 agent 已完成。\ntask_id={task_id}\n允许工具：{', '.join(sorted(allowed_tool_names)) or '(无工具)'}\n子任务结果：\n{child_answer}"  # 修改代码+TaskLifecycle: 返回子 agent 摘要和 task_id 给主 agent；若省略 task_id: 主 agent 无法用 task_output/task_stop 引用任务

    def _run_task_record(self, task_record: TaskRun, child_agent: "LearningAgent", child_prompt: str) -> None:  # 新增代码+AsyncTask: 统一执行子 agent 并写回任务记录；若省略: 同步/后台两条路径会重复且容易状态不一致
        try:  # 新增代码+AsyncTask: 捕获子 agent 执行异常并写回任务记录；若省略: 后台线程异常会静默丢失且 task_output 看不到失败原因
            child_answer = child_agent.run(child_prompt, max_turns=task_record.max_turns)  # 新增代码+AsyncTask: 执行子 agent 并获得最终回答；若省略: 子任务不会真正运行
        except Exception as error:  # 新增代码+AsyncTask: 处理子 agent 运行时异常；若省略: 失败任务不会被记录为 failed
            if task_record.status != "stopped":  # 新增代码+AsyncTask: 如果任务尚未被 stop 标记；若省略: stop 后的异常可能覆盖用户取消状态
                task_record.status = "failed"  # 新增代码+AsyncTask: 标记子任务失败；若省略: task_output 会误以为任务仍在 running
                task_record.error = str(error)  # 新增代码+AsyncTask: 保存失败原因；若省略: 用户无法知道子任务为什么失败
                task_record.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+AsyncTask: 保存失败结束时间；若省略: 查询结果缺少任务结束时间
                self.task_registry.fail_task(task_record.task_id, task_record.error)  # 新增代码+DurableTaskRegistry: 把失败状态写入持久任务登记表并通知主循环；若没有这行代码，后台子任务失败只会留在内存。
            return  # 新增代码+AsyncTask: 异常处理结束后退出执行函数；若省略: 后续会继续按成功路径写状态
        if task_record.stop_event is not None and task_record.stop_event.is_set():  # 新增代码+AsyncTask: 如果子任务结束时已经收到取消信号；若省略: 后台 stop 后可能被完成结果覆盖
            task_record.stop_requested = True  # 新增代码+AsyncTask: 记录取消意图；若省略: task_output 无法反映任务确实收到了停止请求
            task_record.status = "stopped"  # 新增代码+AsyncTask: 保持停止状态；若省略: task_stop 的 stopped 状态可能被 completed 覆盖
            task_record.error = task_record.error or "任务已停止：收到取消请求。"  # 新增代码+AsyncTask: 保存默认停止说明；若省略: task_output 可能只显示空输出
            task_record.completed_at = task_record.completed_at or time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+AsyncTask: 如果 stop 尚未写结束时间则补齐；若省略: 停止任务可能显示未完成
            self.task_registry.stop_task(task_record.task_id, task_record.error)  # 新增代码+DurableTaskRegistry: 把停止状态写入持久任务登记表并通知主循环；若没有这行代码，新 agent 实例看不到停止结果。
            return  # 新增代码+AsyncTask: 停止路径不再保存成功输出；若省略: 被取消任务会误显示为完成
        task_record.status = "completed"  # 新增代码+AsyncTask: 标记子任务完成；若省略: task_output 会误以为任务仍在 running
        task_record.output = child_answer  # 新增代码+AsyncTask: 保存子 agent 最终回答；若省略: task_output 无法读回任务结果
        task_record.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+AsyncTask: 保存完成时间；若省略: 查询结果缺少任务结束时间
        self.task_registry.complete_task(task_record.task_id, output=child_answer, usage={})  # 新增代码+DurableTaskRegistry: 把完成结果写入持久任务登记表并生成 task notification；若没有这行代码，主 agent 必须手动 task_output 才能知道子任务完成。

    def _task_output(self, arguments: dict[str, Any]) -> str:  # 新增代码+TaskLifecycle: 执行 task_output 工具并读取任务记录；若省略: 模型无法二次查询子任务结果
        task_id = str(arguments.get("task_id", "") or "").strip()  # 新增代码+TaskLifecycle: 读取并清理 task_id 参数；若省略: 工具不知道要查询哪个子任务
        if not task_id:  # 新增代码+TaskLifecycle: 检查 task_id 是否为空；若省略: 空查询会产生模糊未知任务错误
            return "task_output 失败：缺少 task_id 参数。"  # 新增代码+TaskLifecycle: 返回清楚缺参错误；若省略: 模型难以修正 task_output 调用
        task_record = self.task_runs.get(task_id)  # 新增代码+TaskLifecycle: 从内存表查找任务记录；若省略: 工具无法定位任务状态和输出
        if task_record is None:  # 新增代码+TaskLifecycle: 处理未知 task_id；若省略: 访问 None 会抛异常
            try:  # 新增代码+DurableTaskRegistry: 内存表找不到时尝试读取持久登记表；若没有这行代码，重启后的 agent 无法查询旧 task。
                persisted_record = self.task_registry.get_task(task_id)  # 新增代码+DurableTaskRegistry: 从磁盘恢复任务记录；若没有这行代码，task_output 只能依赖当前进程。
            except KeyError:  # 新增代码+DurableTaskRegistry: 持久登记表也没有该任务时返回旧错误；若没有这行代码，未知 id 会抛异常。
                return f"task_output 失败：未知 task_id：{task_id}"  # 修改代码+DurableTaskRegistry: 返回清楚未知任务错误；若省略: 模型难以判断是否需要重新创建任务
            max_chars = self._parse_max_chars(arguments.get("max_chars"))  # 新增代码+DurableTaskRegistry: 解析最大返回字符数；若没有这行代码，持久任务输出可能撑爆上下文。
            output_text = persisted_record.output or persisted_record.error or self.task_registry.output_store.tail(task_id, max_chars=max_chars) or "(暂无输出)"  # 新增代码+DurableTaskRegistry: 优先读取登记表摘要并兜底输出文件；若没有这行代码，持久任务结果可能为空。
            truncated_output = output_text[:max_chars]  # 新增代码+DurableTaskRegistry: 按 max_chars 截断持久输出；若没有这行代码，长输出不可控。
            if len(output_text) > max_chars:  # 新增代码+DurableTaskRegistry: 判断持久输出是否被截断；若没有这行代码，模型不知道结果是否完整。
                truncated_output += "\n...[task 输出过长，已截断]..."  # 新增代码+DurableTaskRegistry: 添加截断提示；若没有这行代码，模型可能误以为拿到完整输出。
            return f"task_output 成功：task_id={task_id}\nstatus={persisted_record.status}\nbackground={'true' if persisted_record.background else 'false'}\ncreated_at={persisted_record.created_at}\ncompleted_at={persisted_record.completed_at or '(未完成)'}\nallowed_tools={', '.join(sorted(persisted_record.allowed_tool_names)) or '(无工具)'}\nmax_turns={persisted_record.max_turns}\noutput_path={persisted_record.output_path or '(无)'}\n输出：\n{truncated_output}"  # 新增代码+DurableTaskRegistry: 返回持久任务状态和输出；若没有这行代码，跨进程 task_output 不可用。
        max_chars = self._parse_max_chars(arguments.get("max_chars"))  # 新增代码+TaskLifecycle: 解析最大返回字符数；若省略: 长子任务输出可能撑爆上下文
        output_text = task_record.output or task_record.error or "(暂无输出)"  # 新增代码+TaskLifecycle: 选择任务输出、错误或空输出占位；若省略: 未完成任务会返回空白难以理解
        truncated_output = output_text[:max_chars]  # 新增代码+TaskLifecycle: 按 max_chars 截断输出；若省略: 长输出不可控
        if len(output_text) > max_chars:  # 新增代码+TaskLifecycle: 判断输出是否被截断；若省略: 模型不知道结果是否完整
            truncated_output += "\n...[task 输出过长，已截断]..."  # 新增代码+TaskLifecycle: 添加截断提示；若省略: 模型可能误以为拿到完整输出
        return f"task_output 成功：task_id={task_id}\nstatus={task_record.status}\nbackground={'true' if task_record.background else 'false'}\ncreated_at={task_record.created_at}\ncompleted_at={task_record.completed_at or '(未完成)'}\nallowed_tools={', '.join(sorted(task_record.allowed_tool_names)) or '(无工具)'}\nmax_turns={task_record.max_turns}\n输出：\n{truncated_output}"  # 修改代码+AsyncTask: 返回任务状态、后台标记、元信息和输出；若省略 background: 主 agent 难以判断任务是否还可能异步更新

    def _task_stop(self, arguments: dict[str, Any]) -> str:  # 新增代码+TaskLifecycle: 执行 task_stop 工具并更新任务状态；若省略: 模型无法表达停止子任务的请求
        task_id = str(arguments.get("task_id", "") or "").strip()  # 新增代码+TaskLifecycle: 读取并清理 task_id 参数；若省略: 工具不知道要停止哪个子任务
        if not task_id:  # 新增代码+TaskLifecycle: 检查 task_id 是否为空；若省略: 空停止请求会产生模糊未知任务错误
            return "task_stop 失败：缺少 task_id 参数。"  # 新增代码+TaskLifecycle: 返回清楚缺参错误；若省略: 模型难以修正 task_stop 调用
        task_record = self.task_runs.get(task_id)  # 新增代码+TaskLifecycle: 从内存表查找任务记录；若省略: 工具无法定位任务状态
        if task_record is None:  # 新增代码+TaskLifecycle: 处理未知 task_id；若省略: 访问 None 会抛异常
            try:  # 新增代码+DurableTaskRegistry: 内存表没有时尝试停止持久任务；若没有这行代码，重启后的 agent 无法收束旧任务。
                persisted_record = self.task_registry.stop_task(task_id, "任务已请求停止。原因：(持久任务恢复停止)")  # 新增代码+DurableTaskRegistry: 标记持久任务 stopped；若没有这行代码，旧 running 状态会一直存在。
            except KeyError:  # 新增代码+DurableTaskRegistry: 持久登记表也找不到时返回旧错误；若没有这行代码，未知 id 会抛异常。
                return f"task_stop 失败：未知 task_id：{task_id}"  # 修改代码+DurableTaskRegistry: 返回清楚未知任务错误；若省略: 模型难以判断是否需要重新创建任务
            return f"task_stop 成功：task_id={task_id} 已标记为 {persisted_record.status}。\n原因：{persisted_record.error or '(未提供)'}"  # 新增代码+DurableTaskRegistry: 返回持久任务停止结果；若没有这行代码，跨进程 stop 没有可读反馈。
        reason = str(arguments.get("reason", "") or "").strip()  # 新增代码+TaskLifecycle: 读取可选停止原因；若省略: 停止记录缺少用户或模型意图
        if task_record.status == "completed":  # 新增代码+TaskLifecycle: 已完成任务无需停止；若省略: 可能把完成任务错误改成 stopped
            return f"task_stop 成功：task_id={task_id} 已经完成，无需停止。\n输出可用 task_output 查看。"  # 新增代码+TaskLifecycle: 返回已完成边界说明；若省略: 用户不知道 stop 没有改变任务
        if task_record.status in {"failed", "stopped"}:  # 新增代码+TaskLifecycle: 已失败或已停止任务无需重复停止；若省略: 重复停止会让状态语义混乱
            return f"task_stop 成功：task_id={task_id} 当前状态为 {task_record.status}，无需重复停止。"  # 新增代码+TaskLifecycle: 返回幂等停止说明；若省略: 模型可能继续重复调用 stop
        if task_record.stop_event is not None:  # 新增代码+AsyncTask: 如果这是带取消信号的后台任务；若省略: task_stop 无法通知后台子 agent 协作停止
            task_record.stop_event.set()  # 新增代码+AsyncTask: 置位取消信号；若省略: 后台子 agent 只能等自然结束
        task_record.stop_requested = True  # 新增代码+TaskLifecycle: 记录停止请求；若省略: task_output 无法反映用户取消意图
        task_record.status = "stopped"  # 新增代码+TaskLifecycle: 把未完成任务标记为 stopped；若省略: 任务会继续显示 running/pending
        task_record.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+TaskLifecycle: 保存停止时间；若省略: 查询结果缺少停止发生时间
        task_record.error = f"任务已请求停止。原因：{reason or '(未提供)'}"  # 新增代码+TaskLifecycle: 保存停止原因到错误/状态文本；若省略: task_output 看不到为什么停止
        self.task_registry.stop_task(task_id, task_record.error)  # 新增代码+DurableTaskRegistry: 同步把停止状态写入持久登记表；若没有这行代码，新 agent 实例仍会看到旧 running 状态。
        return f"task_stop 成功：task_id={task_id} 已标记为 stopped。\n原因：{reason or '(未提供)'}"  # 新增代码+TaskLifecycle: 返回停止结果；若省略: 模型无法向用户说明取消是否生效

    def _task_list(self, arguments: dict[str, Any]) -> str:  # 新增代码+TaskManagement: 执行 task_list 工具并返回子任务总览；若省略: 模型无法查看多个子任务的统一列表
        raw_status = str(arguments.get("status", "") or "").strip().lower()  # 新增代码+TaskManagement: 读取并标准化可选状态筛选；若省略: running/completed 等筛选无法生效
        allowed_statuses = {"all", "pending", "running", "completed", "failed", "stopped"}  # 新增代码+TaskManagement: 定义允许筛选的任务状态；若省略: 模型传错状态时无法给出清楚边界
        if raw_status and raw_status not in allowed_statuses:  # 新增代码+TaskManagement: 检查状态筛选是否有效；若省略: 拼写错误会默默返回空列表
            return f"task_list 失败：未知 status：{raw_status}，可选值为 all/pending/running/completed/failed/stopped。"  # 新增代码+TaskManagement: 返回可恢复的状态错误；若省略: 模型难以修正筛选参数
        max_results = self._tool_search_max_results(arguments.get("max_results"))  # 新增代码+TaskManagement: 复用 1 到 20 的结果数限制；若省略: 大量任务可能撑爆上下文
        persisted_records = self.task_registry.list_tasks()  # 修改代码+DurableTaskTools: 优先从持久 task registry 读取任务；若没有这行代码，重启后的 agent 会看不到旧任务。
        persisted_ids = {record.task_id for record in persisted_records}  # 新增代码+DurableTaskTools: 记录已经从磁盘恢复的 task_id；若没有这行代码，内存和磁盘任务可能重复显示。
        memory_only_records = [record for record in self.task_runs.values() if record.task_id not in persisted_ids]  # 新增代码+DurableTaskTools: 只补充尚未落盘的内存任务；若没有这行代码，极端内存任务会从列表里消失。
        all_records = [*persisted_records, *memory_only_records]  # 修改代码+DurableTaskTools: 合并持久任务和内存兜底任务；若没有这行代码，task_list 无法同时兼容重启恢复和当前进程缓存。
        if not all_records:  # 新增代码+TaskManagement: 处理尚未创建任何 task 的情况；若省略: 空列表会返回不清楚的标题
            return "task_list 成功：当前没有子任务记录。"  # 新增代码+TaskManagement: 明确说明没有任务；若省略: 模型可能误以为工具失败
        selected_records = [record for record in all_records if not raw_status or raw_status == "all" or record.status == raw_status]  # 新增代码+TaskManagement: 按状态筛选任务；若省略: status 参数不会影响结果
        if not selected_records:  # 新增代码+TaskManagement: 处理筛选后没有匹配任务的情况；若省略: 空筛选结果难以和无任务区分
            return f"task_list 成功：共有 {len(all_records)} 个子任务，但没有 status={raw_status} 的记录。"  # 新增代码+TaskManagement: 返回筛选为空的可读说明；若省略: 模型不知道是筛选太窄还是任务不存在
        visible_records = selected_records[:max_results]  # 新增代码+TaskManagement: 截取允许返回的任务数量；若省略: 多任务列表可能过长
        filter_text = raw_status or "all"  # 新增代码+TaskManagement: 生成用于标题展示的筛选文本；若省略: 返回标题无法说明当前筛选条件
        lines = [f"task_list 成功：共有 {len(all_records)} 个子任务，status={filter_text} 匹配 {len(selected_records)} 个，显示前 {len(visible_records)} 个。"]  # 新增代码+TaskManagement: 构造列表标题；若省略: 模型不知道总数、筛选数和截断情况
        for index, task_record in enumerate(visible_records, start=1):  # 新增代码+TaskManagement: 逐条格式化任务摘要；若省略: 任务记录无法变成人类和模型可读文本
            prompt_preview = " ".join(task_record.prompt.split())  # 新增代码+TaskManagement: 把多行 prompt 压成单行摘要；若省略: 列表输出会被长 prompt 撑乱
            if len(prompt_preview) > 80:  # 新增代码+TaskManagement: 判断 prompt 摘要是否过长；若省略: 长任务目标会让列表难以扫描
                prompt_preview = prompt_preview[:80] + "..."  # 新增代码+TaskManagement: 截断过长 prompt 摘要；若省略: 列表可能占用过多上下文
            task_metadata = getattr(task_record, "metadata", {}) if isinstance(getattr(task_record, "metadata", {}), dict) else {}  # 新增代码+DurableTaskTools: 读取持久任务 metadata；若没有这行代码，重启后的 label/notes 没有来源。
            task_label = getattr(task_record, "label", "") or str(task_metadata.get("label", ""))  # 新增代码+DurableTaskTools: 同时兼容内存 TaskRun 和持久 TaskRecord 标签；若没有这行代码，task_list 会因对象字段不同而崩溃。
            lines.append(f"{index}. task_id={task_record.task_id} status={task_record.status} background={'true' if task_record.background else 'false'} label={task_label or '(无标签)'}")  # 修改代码+DurableTaskTools: 输出任务 id、状态、后台标记和持久标签；若没有这行代码，模型无法快速选择跨实例任务。
            lines.append(f"   prompt={prompt_preview or '(无 prompt)'}")  # 新增代码+TaskManagement: 输出任务目标摘要；若省略: 任务列表只能看到 id 而不知任务内容
            lines.append(f"   created_at={task_record.created_at} completed_at={task_record.completed_at or '(未完成)'}")  # 新增代码+TaskManagement: 输出创建和完成时间；若省略: 模型难以判断任务新旧和是否结束
        return "\n".join(lines)  # 新增代码+TaskManagement: 返回完整任务列表文本；若省略: 工具无法把总览交回模型

    def _task_get(self, arguments: dict[str, Any]) -> str:  # 新增代码+TaskManagement: 执行 task_get 工具并返回单个子任务详情；若省略: 模型无法读取任务管理元信息
        task_id = str(arguments.get("task_id", "") or "").strip()  # 新增代码+TaskManagement: 读取并清理 task_id 参数；若省略: 工具不知道要查询哪个任务
        if not task_id:  # 新增代码+TaskManagement: 检查 task_id 是否为空；若省略: 空查询会产生模糊未知任务错误
            return "task_get 失败：缺少 task_id 参数。"  # 新增代码+TaskManagement: 返回清楚缺参错误；若省略: 模型难以修正 task_get 调用
        task_record = self.task_runs.get(task_id)  # 新增代码+TaskManagement: 从内存表查找任务记录；若省略: 工具无法定位任务详情
        if task_record is None:  # 新增代码+TaskManagement: 处理未知 task_id；若省略: 访问 None 会抛异常
            try:  # 修改代码+DurableTaskTools: 内存没有时读取持久 task registry；若没有这行代码，重启后的 task_get 会误报未知任务。
                task_record = self.task_registry.get_task(task_id)  # 新增代码+DurableTaskTools: 从磁盘恢复目标任务；若没有这行代码，旧任务详情无法跨进程读取。
            except KeyError:  # 新增代码+DurableTaskTools: 持久 registry 也没有该任务时才返回未知；若没有这行代码，真实未知 id 会抛出底层异常。
                return f"task_get 失败：未知 task_id：{task_id}"  # 修改代码+DurableTaskTools: 返回清楚未知任务错误；若没有这行代码，模型难以判断是否需要先 task_list。
        max_chars = self._parse_max_chars(arguments.get("max_chars"))  # 新增代码+TaskManagement: 解析最大返回字符数；若省略: 长输出可能撑爆上下文
        task_metadata = getattr(task_record, "metadata", {}) if isinstance(getattr(task_record, "metadata", {}), dict) else {}  # 新增代码+DurableTaskTools: 读取持久任务 metadata；若没有这行代码，label/notes/stop_requested 跨实例不可见。
        task_label = getattr(task_record, "label", "") or str(task_metadata.get("label", ""))  # 新增代码+DurableTaskTools: 兼容内存 TaskRun 和持久 TaskRecord 标签；若没有这行代码，task_get 会因为字段差异失败。
        task_notes = getattr(task_record, "notes", "") or str(task_metadata.get("notes", ""))  # 新增代码+DurableTaskTools: 兼容内存 TaskRun 和持久 TaskRecord 备注；若没有这行代码，跨实例交接说明会丢失。
        stop_requested = bool(getattr(task_record, "stop_requested", False) or task_metadata.get("stop_requested", False))  # 新增代码+DurableTaskTools: 兼容两种任务对象的停止标记；若没有这行代码，持久任务详情会因缺字段崩溃。
        output_text = task_record.output or task_record.error or self.task_registry.output_store.tail(task_id, max_chars=max_chars) or "(暂无输出)"  # 修改代码+DurableTaskTools: 优先读摘要并兜底输出文件；若没有这行代码，持久任务的大输出可能显示为空。
        truncated_output = output_text[:max_chars]  # 新增代码+TaskManagement: 按 max_chars 截断输出；若省略: 长输出不可控
        if len(output_text) > max_chars:  # 新增代码+TaskManagement: 判断输出是否被截断；若省略: 模型不知道结果是否完整
            truncated_output += "\n...[task 输出过长，已截断]..."  # 新增代码+TaskManagement: 添加截断提示；若省略: 模型可能误以为拿到完整输出
        lines = [f"task_get 成功：task_id={task_id}"]  # 新增代码+TaskManagement: 构造详情标题；若省略: 返回文本缺少目标任务 id
        lines.append(f"status={task_record.status}")  # 新增代码+TaskManagement: 输出任务状态；若省略: 模型无法判断任务是否完成
        lines.append(f"background={'true' if task_record.background else 'false'}")  # 新增代码+TaskManagement: 输出后台标记；若省略: 模型无法判断任务是否可能异步更新
        lines.append(f"label={task_label or '(无标签)'}")  # 修改代码+DurableTaskTools: 输出内存或持久标签；若没有这行代码，重启后的 task_update 标签无法被读回。
        lines.append(f"notes={task_notes or '(无备注)'}")  # 修改代码+DurableTaskTools: 输出内存或持久备注；若没有这行代码，重启后的 task_update 备注无法被读回。
        lines.append(f"prompt={task_record.prompt}")  # 新增代码+TaskManagement: 输出原始任务 prompt；若省略: 主 agent 无法追溯子任务目标
        lines.append(f"created_at={task_record.created_at}")  # 新增代码+TaskManagement: 输出创建时间；若省略: 任务详情缺少时间线起点
        lines.append(f"completed_at={task_record.completed_at or '(未完成)'}")  # 新增代码+TaskManagement: 输出完成时间或未完成占位；若省略: 模型难以区分 running 和没有时间字段
        lines.append(f"allowed_tools={', '.join(sorted(task_record.allowed_tool_names)) or '(无工具)'}")  # 新增代码+TaskManagement: 输出子 agent 工具边界；若省略: 审查子任务权限范围会更困难
        lines.append(f"max_turns={task_record.max_turns}")  # 新增代码+TaskManagement: 输出子 agent 最大轮次；若省略: 模型无法知道子任务执行约束
        lines.append(f"stop_requested={'true' if stop_requested else 'false'}")  # 修改代码+DurableTaskTools: 输出兼容持久任务的停止标记；若没有这行代码，TaskRecord 没有 stop_requested 字段时会崩溃。
        lines.append(f"输出：\n{truncated_output}")  # 新增代码+TaskManagement: 输出任务结果或错误摘要；若省略: 详情读取仍要再调用 task_output 才有结果
        return "\n".join(lines)  # 新增代码+TaskManagement: 返回完整任务详情文本；若省略: 工具无法把详情交回模型

    def _task_update(self, arguments: dict[str, Any]) -> str:  # 新增代码+TaskManagement: 执行 task_update 工具并更新任务管理元信息；若省略: 模型无法为任务补标签或备注
        task_id = str(arguments.get("task_id", "") or "").strip()  # 新增代码+TaskManagement: 读取并清理 task_id 参数；若省略: 工具不知道要更新哪个任务
        if not task_id:  # 新增代码+TaskManagement: 检查 task_id 是否为空；若省略: 空更新会产生模糊未知任务错误
            return "task_update 失败：缺少 task_id 参数。"  # 新增代码+TaskManagement: 返回清楚缺参错误；若省略: 模型难以修正 task_update 调用
        task_record = self.task_runs.get(task_id)  # 新增代码+TaskManagement: 从内存表查找任务记录；若省略: 工具无法定位任务
        persisted_record = None  # 新增代码+DurableTaskTools: 准备保存持久任务记录引用；若没有这行代码，跨实例更新无法区分是否从磁盘恢复。
        if task_record is None:  # 新增代码+TaskManagement: 处理未知 task_id；若省略: 访问 None 会抛异常
            try:  # 修改代码+DurableTaskTools: 内存没有时尝试读取持久 task registry；若没有这行代码，重启后的 task_update 会误报未知任务。
                persisted_record = self.task_registry.get_task(task_id)  # 新增代码+DurableTaskTools: 从磁盘恢复目标任务；若没有这行代码，旧任务元信息不能跨实例修改。
            except KeyError:  # 新增代码+DurableTaskTools: 持久 registry 也没有该任务时才返回未知；若没有这行代码，真实未知 id 会抛底层异常。
                return f"task_update 失败：未知 task_id：{task_id}"  # 修改代码+DurableTaskTools: 返回清楚未知任务错误；若没有这行代码，模型难以判断是否需要先 task_list。
        has_label = "label" in arguments  # 新增代码+TaskManagement: 判断调用是否显式提供 label；若省略: 无法区分省略字段和清空标签
        has_notes = "notes" in arguments  # 新增代码+TaskManagement: 判断调用是否显式提供 notes；若省略: 无法区分省略字段和清空备注
        if not has_label and not has_notes:  # 新增代码+TaskManagement: 要求至少更新一个管理字段；若省略: 空更新会返回成功但什么也没做
            return "task_update 失败：请至少提供 label 或 notes。"  # 新增代码+TaskManagement: 返回清楚空更新错误；若省略: 模型难以知道必须补哪个字段
        if persisted_record is not None:  # 新增代码+DurableTaskTools: 处理重启后只存在于持久 registry 的任务；若没有这行代码，跨实例更新仍无法落盘。
            if has_label:  # 新增代码+DurableTaskTools: 调用方提供 label 时才更新持久标签；若没有这行代码，无法区分不改和清空标签。
                persisted_record.metadata["label"] = str(arguments.get("label", "") or "").strip()  # 新增代码+DurableTaskTools: 把 label 写入 metadata；若没有这行代码，TaskRecord 没有 label 字段会无法保存标签。
            if has_notes:  # 新增代码+DurableTaskTools: 调用方提供 notes 时才更新持久备注；若没有这行代码，无法区分不改和清空备注。
                persisted_record.metadata["notes"] = str(arguments.get("notes", "") or "").strip()  # 新增代码+DurableTaskTools: 把 notes 写入 metadata；若没有这行代码，TaskRecord 没有 notes 字段会无法保存备注。
            self.task_registry.save_task(persisted_record)  # 新增代码+DurableTaskTools: 保存持久任务元信息；若没有这行代码，更新只在本次调用对象里生效。
            return f"task_update 成功：task_id={task_id}\nlabel={persisted_record.metadata.get('label') or '(无标签)'}\nnotes={persisted_record.metadata.get('notes') or '(无备注)'}"  # 新增代码+DurableTaskTools: 返回持久更新结果；若没有这行代码，模型无法确认跨实例更新是否生效。
        if has_label:  # 新增代码+TaskManagement: 如果调用提供了 label 字段；若省略: 标签更新不会执行
            task_record.label = str(arguments.get("label", "") or "").strip()  # 新增代码+TaskManagement: 写入清理后的标签，空字符串表示清空；若省略: 任务列表无法显示新标签
        if has_notes:  # 新增代码+TaskManagement: 如果调用提供了 notes 字段；若省略: 备注更新不会执行
            task_record.notes = str(arguments.get("notes", "") or "").strip()  # 新增代码+TaskManagement: 写入清理后的备注，空字符串表示清空；若省略: 任务详情无法显示新备注
        try:  # 新增代码+DurableTaskTools: 同步更新内存任务对应的持久记录；若没有这行代码，同一实例更新后重启会丢失 label/notes。
            registry_record = self.task_registry.get_task(task_id)  # 新增代码+DurableTaskTools: 读取持久任务记录；若没有这行代码，无法把内存元信息写回磁盘。
            if has_label:  # 新增代码+DurableTaskTools: 只同步调用方显式提供的 label；若没有这行代码，可能误覆盖已有持久标签。
                registry_record.metadata["label"] = task_record.label  # 新增代码+DurableTaskTools: 把内存标签写入持久 metadata；若没有这行代码，task_list 重启后看不到标签。
            if has_notes:  # 新增代码+DurableTaskTools: 只同步调用方显式提供的 notes；若没有这行代码，可能误覆盖已有持久备注。
                registry_record.metadata["notes"] = task_record.notes  # 新增代码+DurableTaskTools: 把内存备注写入持久 metadata；若没有这行代码，task_get 重启后看不到备注。
            self.task_registry.save_task(registry_record)  # 新增代码+DurableTaskTools: 保存持久任务记录；若没有这行代码，更新不会跨进程保留。
        except KeyError:  # 新增代码+DurableTaskTools: 兼容极端内存任务尚未落盘的情况；若没有这行代码，老测试或手工记录会被打断。
            pass  # 新增代码+DurableTaskTools: 没有持久记录时只保留内存更新；若没有这行代码，except 分支语法不完整。
        return f"task_update 成功：task_id={task_id}\nlabel={task_record.label or '(无标签)'}\nnotes={task_record.notes or '(无备注)'}"  # 新增代码+TaskManagement: 返回更新后的管理元信息；若省略: 模型无法确认更新结果

    def _team_create(self, arguments: dict[str, Any]) -> str:  # 新增代码+TeamCommunication: 执行 team_create 工具并登记教学版 peer；若省略: 模型无法创建团队成员记录
        name = str(arguments.get("name", "") or "").strip()  # 新增代码+TeamCommunication: 读取并清理 peer 名称；若省略: peer 记录缺少可读名称
        if not name:  # 新增代码+TeamCommunication: 检查名称是否为空；若省略: 空名称 peer 会让 list_peers 难以阅读
            return "team_create 失败：缺少非空 name 参数。"  # 新增代码+TeamCommunication: 返回清楚缺参错误；若省略: 模型难以修正 team_create 调用
        role = str(arguments.get("role", "") or "peer").strip() or "peer"  # 新增代码+TeamCommunication: 读取角色并在省略时使用 peer；若省略: 成员职责字段可能为空
        notes = str(arguments.get("notes", "") or "").strip()  # 新增代码+TeamCommunication: 读取可选备注；若省略: team_create 无法保存职责边界说明
        peer_id = f"peer_{secrets.token_hex(6)}"  # 新增代码+TeamCommunication: 生成短且唯一的 peer id；若省略: send_message/list_peers 无法稳定引用成员
        peer_record = TeamPeer(peer_id=peer_id, name=name, role=role, status="idle", notes=notes, created_at=time.strftime("%Y-%m-%d %H:%M:%S"))  # 新增代码+TeamCommunication: 创建 peer 记录并标记为空闲；若省略: team_create 只会返回文本但不会留下状态
        self.team_peers[peer_id] = peer_record  # 新增代码+TeamCommunication: 把 peer 记录放入当前 agent 进程内登记表；若省略: 后续 send_message/list_peers 找不到这个 peer
        self.team_registry.save_peer(peer_record)  # 新增代码+DurableTeamRegistry: 把 peer 同步写入持久登记表；若没有这行代码，新 agent 实例无法列出这个 peer。
        return f"team_create 成功：已创建教学版 peer。\npeer_id={peer_id}\nname={peer_record.name}\nrole={peer_record.role}\nstatus={peer_record.status}\nnotes={peer_record.notes or '(无备注)'}"  # 新增代码+TeamCommunication: 返回 peer id 和元信息给模型；若省略: 模型无法继续向该 peer 发送消息

    def _send_message(self, arguments: dict[str, Any]) -> str:  # 新增代码+TeamCommunication: 执行 send_message 工具并把消息放入 peer inbox；若省略: peer 之间无法建立教学版通信记录
        peer_id = str(arguments.get("peer_id", "") or "").strip()  # 新增代码+TeamCommunication: 读取并清理目标 peer_id；若省略: 工具不知道要发给谁
        if not peer_id:  # 新增代码+TeamCommunication: 检查 peer_id 是否为空；若省略: 空目标会产生模糊未知 peer 错误
            return "send_message 失败：缺少 peer_id 参数。"  # 新增代码+TeamCommunication: 返回清楚缺参错误；若省略: 模型难以修正 send_message 调用
        peer_record = self.team_peers.get(peer_id)  # 新增代码+TeamCommunication: 从登记表查找目标 peer；若省略: 工具无法定位收件箱
        if peer_record is None:  # 新增代码+TeamCommunication: 处理未知 peer_id；若省略: 访问 None 会抛异常
            try:  # 修改代码+DurableTeamRegistry: 内存没有时尝试从持久 team registry 恢复；若没有这行代码，重启后的 send_message 会误报未知 peer。
                peer_record = self.team_registry.get_peer(peer_id)  # 新增代码+DurableTeamRegistry: 从磁盘恢复 peer；若没有这行代码，旧 peer 无法继续接收消息。
                self.team_peers[peer_id] = peer_record  # 新增代码+DurableTeamRegistry: 把恢复的 peer 放回内存缓存；若没有这行代码，本次后续操作还会反复读磁盘。
            except KeyError:  # 新增代码+DurableTeamRegistry: 持久 registry 也没有该 peer 时才返回未知；若没有这行代码，真实未知 id 会抛底层异常。
                return f"send_message 失败：未知 peer_id：{peer_id}，请先调用 team_create 或 list_peers。"  # 修改代码+DurableTeamRegistry: 返回可恢复建议；若没有这行代码，模型不知道该先创建或查看 peer。
        message = str(arguments.get("message", arguments.get("content", "")) or "").strip()  # 修改代码+DurableTeamRegistry: 同时兼容 message 和 content 参数；若没有这行代码，控制器或模型使用 content 会被误判缺参。
        if not message:  # 新增代码+TeamCommunication: 检查消息正文是否为空；若省略: 空消息会污染 peer inbox
            return "send_message 失败：缺少非空 message 参数。"  # 新增代码+TeamCommunication: 返回清楚缺参错误；若省略: 模型难以修正消息内容
        sender = str(arguments.get("sender", "") or "main").strip() or "main"  # 新增代码+TeamCommunication: 读取发送者并默认使用 main；若省略: 消息来源字段可能为空
        message_id = f"msg_{secrets.token_hex(6)}"  # 新增代码+TeamCommunication: 生成短且唯一的消息 id；若省略: 用户无法审计具体消息
        peer_record.inbox.append(TeamMessage(message_id=message_id, sender=sender, content=message, created_at=time.strftime("%Y-%m-%d %H:%M:%S")))  # 新增代码+TeamCommunication: 把消息追加到目标 peer inbox；若省略: send_message 不会留下任何可查询记录
        peer_record.status = "active"  # 新增代码+TeamCommunication: 收到消息后把 peer 标记为 active；若省略: list_peers 无法反映该 peer 已有待处理消息
        self.team_registry.save_peer(peer_record)  # 新增代码+DurableTeamRegistry: 保存新增消息和 active 状态；若没有这行代码，重启后 peer inbox 会丢失。
        return f"send_message 成功：消息已进入 peer inbox。\npeer_id={peer_id}\nmessage_id={message_id}\ninbox_count={len(peer_record.inbox)}"  # 新增代码+TeamCommunication: 返回消息 id 和 inbox 数量；若省略: 模型无法确认消息是否保存

    def _list_peers(self, arguments: dict[str, Any]) -> str:  # 新增代码+TeamCommunication: 执行 list_peers 工具并返回 peer 总览；若省略: 模型无法查看当前团队成员
        role_filter = str(arguments.get("role", "") or "").strip().lower()  # 新增代码+TeamCommunication: 读取并标准化可选角色筛选；若省略: role 参数不会影响列表
        status_filter = str(arguments.get("status", "") or "").strip().lower()  # 新增代码+TeamCommunication: 读取并标准化可选状态筛选；若省略: status 参数不会影响列表
        max_results = self._tool_search_max_results(arguments.get("max_results"))  # 新增代码+TeamCommunication: 复用 1 到 20 的结果数限制；若省略: peer 太多可能撑爆上下文
        persisted_peers = self.team_registry.list_peers()  # 修改代码+DurableTeamRegistry: 优先从持久 team registry 读取 peer；若没有这行代码，重启后的 list_peers 会看不到旧成员。
        persisted_peer_ids = {peer.peer_id for peer in persisted_peers}  # 新增代码+DurableTeamRegistry: 记录已经从磁盘恢复的 peer_id；若没有这行代码，内存和磁盘 peer 可能重复显示。
        memory_only_peers = [peer for peer in self.team_peers.values() if peer.peer_id not in persisted_peer_ids]  # 新增代码+DurableTeamRegistry: 只补充还没落盘的内存 peer；若没有这行代码，极端临时 peer 会从列表里消失。
        all_peers = [*persisted_peers, *memory_only_peers]  # 修改代码+DurableTeamRegistry: 合并持久 peer 和内存兜底 peer；若没有这行代码，team 视图无法兼容恢复和当前进程缓存。
        if not all_peers:  # 新增代码+TeamCommunication: 处理尚未创建 peer 的情况；若省略: 空列表会返回不清楚的标题
            return "list_peers 成功：当前没有 peer 记录。"  # 新增代码+TeamCommunication: 明确说明没有成员；若省略: 模型可能误以为工具失败
        selected_peers = [peer for peer in all_peers if (not role_filter or peer.role.lower() == role_filter) and (not status_filter or peer.status.lower() == status_filter)]  # 新增代码+TeamCommunication: 按角色和状态筛选 peer；若省略: 筛选参数不会生效
        if not selected_peers:  # 新增代码+TeamCommunication: 处理筛选后没有匹配 peer 的情况；若省略: 空筛选结果难以和无 peer 区分
            return f"list_peers 成功：共有 {len(all_peers)} 个 peer，但没有匹配 role={role_filter or 'all'} status={status_filter or 'all'} 的记录。"  # 新增代码+TeamCommunication: 返回筛选为空说明；若省略: 模型不知道是筛选太窄还是成员不存在
        visible_peers = selected_peers[:max_results]  # 新增代码+TeamCommunication: 截取允许返回的 peer 数量；若省略: 多成员列表可能过长
        lines = [f"list_peers 成功：共有 {len(all_peers)} 个 peer，匹配 {len(selected_peers)} 个，显示前 {len(visible_peers)} 个。"]  # 新增代码+TeamCommunication: 构造列表标题；若省略: 模型不知道总数、筛选数和截断情况
        for index, peer in enumerate(visible_peers, start=1):  # 新增代码+TeamCommunication: 逐条格式化 peer 摘要；若省略: peer 记录无法变成人类和模型可读文本
            pending_count = sum(1 for message in peer.inbox if not message.acknowledged_at)  # 新增代码+TeamCommunicationLifecycle: 统计未确认消息数量；若省略: 主 agent 无法判断 peer inbox 还有多少待处理消息
            bound_task_id = peer.bound_task_id or "(无)"  # 新增代码+TeamTaskBinding: 生成 peer 绑定 task id 的展示文本；若省略: list_peers 无法显示 peer 正在承接哪个后台任务
            bound_task_record = self.task_runs.get(peer.bound_task_id) if peer.bound_task_id else None  # 新增代码+TeamTaskBinding: 从内存任务表读取绑定 task 当前记录；若省略: team 视图无法动态反映当前进程 task 状态
            if bound_task_record is None and peer.bound_task_id:  # 新增代码+DurableTeamRegistry: 内存找不到绑定任务时尝试持久 task registry；若没有这行代码，重启后 team 绑定任务会显示 missing。
                try:  # 新增代码+DurableTeamRegistry: 持久任务查询可能找不到目标；若没有这行代码，旧 peer 绑定坏 task 会让列表失败。
                    bound_task_record = self.task_registry.get_task(peer.bound_task_id)  # 新增代码+DurableTeamRegistry: 从磁盘读取绑定 task 状态；若没有这行代码，team 视图无法跨实例反映 task 状态。
                except KeyError:  # 新增代码+DurableTeamRegistry: 绑定任务确实不存在时保持 missing；若没有这行代码，异常会打断 list_peers。
                    bound_task_record = None  # 新增代码+DurableTeamRegistry: 明确保持未找到状态；若没有这行代码，后续变量语义不清楚。
            task_status = bound_task_record.status if bound_task_record is not None else ("missing" if peer.bound_task_id else "(无)")  # 新增代码+TeamTaskBinding: 计算绑定 task 当前状态或缺失占位；若省略: 用户无法判断 peer 任务是否 running/stopped/completed
            latest_message = peer.inbox[-1].content if peer.inbox else "(无消息)"  # 新增代码+TeamCommunication: 读取最新消息摘要或空占位；若省略: list_peers 无法提示最近通信内容
            latest_preview = " ".join(latest_message.split())  # 新增代码+TeamCommunication: 把最新消息压成单行摘要；若省略: 多行消息会打乱列表格式
            if len(latest_preview) > 80:  # 新增代码+TeamCommunication: 判断消息摘要是否过长；若省略: 长消息会让列表难以扫描
                latest_preview = latest_preview[:80] + "..."  # 新增代码+TeamCommunication: 截断过长消息摘要；若省略: 列表可能占用过多上下文
            lines.append(f"{index}. peer_id={peer.peer_id} name={peer.name} role={peer.role} status={peer.status} inbox_count={len(peer.inbox)} pending_count={pending_count} bound_task_id={bound_task_id} task_status={task_status}")  # 修改代码+TeamTaskBinding: 输出 peer 核心元信息、消息数和绑定任务状态；若省略: 模型无法从 team 视图追踪 peer 的后台 task
            lines.append(f"   notes={peer.notes or '(无备注)'}")  # 新增代码+TeamCommunication: 输出 peer 职责备注；若省略: 主 agent 难以理解成员边界
            lines.append(f"   created_at={peer.created_at}")  # 新增代码+TeamCommunication: 输出 peer 创建时间；若省略: 多 peer 场景缺少时间线
            lines.append(f"   latest_message={latest_preview}")  # 新增代码+TeamCommunication: 输出最新消息摘要；若省略: 模型需要额外工具才能知道 inbox 大致内容
        return "\n".join(lines)  # 新增代码+TeamCommunication: 返回完整 peer 列表文本；若省略: 工具无法把总览交回模型

    def _read_peer_messages(self, arguments: dict[str, Any]) -> str:  # 新增代码+TeamCommunicationLifecycle: 执行 read_peer_messages 工具并读取 peer inbox；若省略: 模型无法查看 peer 收到的消息详情
        peer_id = str(arguments.get("peer_id", "") or "").strip()  # 新增代码+TeamCommunicationLifecycle: 读取并清理目标 peer_id；若省略: 工具不知道要读取哪个 peer
        if not peer_id:  # 新增代码+TeamCommunicationLifecycle: 检查 peer_id 是否为空；若省略: 空目标会产生模糊未知 peer 错误
            return "read_peer_messages 失败：缺少 peer_id 参数。"  # 新增代码+TeamCommunicationLifecycle: 返回清楚缺参错误；若省略: 模型难以修正 read_peer_messages 调用
        peer_record = self.team_peers.get(peer_id)  # 新增代码+TeamCommunicationLifecycle: 从登记表查找目标 peer；若省略: 工具无法定位 inbox
        if peer_record is None:  # 新增代码+TeamCommunicationLifecycle: 处理未知 peer_id；若省略: 访问 None 会抛异常
            try:  # 修改代码+DurableTeamRegistry: 内存没有时尝试从持久 registry 恢复；若没有这行代码，重启后的 read_peer_messages 会误报未知 peer。
                peer_record = self.team_registry.get_peer(peer_id)  # 新增代码+DurableTeamRegistry: 从磁盘恢复 peer 和 inbox；若没有这行代码，旧消息无法跨实例读取。
                self.team_peers[peer_id] = peer_record  # 新增代码+DurableTeamRegistry: 把恢复的 peer 放回内存缓存；若没有这行代码，本次后续操作会反复读磁盘。
            except KeyError:  # 新增代码+DurableTeamRegistry: 持久 registry 也没有该 peer 时才返回未知；若没有这行代码，真实未知 id 会抛底层异常。
                return f"read_peer_messages 失败：未知 peer_id：{peer_id}，请先调用 team_create 或 list_peers。"  # 修改代码+DurableTeamRegistry: 返回可恢复建议；若没有这行代码，模型不知道该先创建或查看 peer。
        include_acknowledged = arguments.get("include_acknowledged") is True  # 新增代码+TeamCommunicationLifecycle: 仅在显式 true 时包含已确认消息；若省略: 默认读取会混入已处理历史
        max_results = self._tool_search_max_results(arguments.get("max_results"))  # 新增代码+TeamCommunicationLifecycle: 复用 1 到 20 的返回数量限制；若省略: inbox 太长可能撑爆上下文
        pending_count = sum(1 for message in peer_record.inbox if not message.acknowledged_at)  # 新增代码+TeamCommunicationLifecycle: 统计当前待确认消息数；若省略: 读取结果缺少处理压力摘要
        selected_messages = [message for message in peer_record.inbox if include_acknowledged or not message.acknowledged_at]  # 新增代码+TeamCommunicationLifecycle: 按是否包含已确认历史筛选消息；若省略: include_acknowledged 参数不会生效
        visible_messages = selected_messages[:max_results]  # 新增代码+TeamCommunicationLifecycle: 截取允许返回的消息数量；若省略: 消息太多会让输出过长
        if not visible_messages:  # 新增代码+TeamCommunicationLifecycle: 处理筛选后没有消息的情况；若省略: 空结果难以和工具失败区分
            return f"read_peer_messages 成功：peer_id={peer_id} inbox_count={len(peer_record.inbox)} pending_count={pending_count}，没有匹配消息。"  # 新增代码+TeamCommunicationLifecycle: 返回空结果摘要；若省略: 模型不知道 inbox 是否为空或只是筛选为空
        lines = [f"read_peer_messages 成功：peer_id={peer_id} inbox_count={len(peer_record.inbox)} pending_count={pending_count} 显示前 {len(visible_messages)} 条。"]  # 新增代码+TeamCommunicationLifecycle: 构造读取结果标题；若省略: 模型不知道返回数量和待处理数量
        for index, message_record in enumerate(visible_messages, start=1):  # 新增代码+TeamCommunicationLifecycle: 逐条格式化消息；若省略: 消息记录无法变成人类和模型可读文本
            message_preview = " ".join(message_record.content.split())  # 新增代码+TeamCommunicationLifecycle: 把消息正文压成单行摘要；若省略: 多行消息会打乱列表格式
            if len(message_preview) > 200:  # 新增代码+TeamCommunicationLifecycle: 判断消息正文是否过长；若省略: 长消息会让读取结果难以扫描
                message_preview = message_preview[:200] + "..."  # 新增代码+TeamCommunicationLifecycle: 截断过长消息正文；若省略: 单条消息可能占用过多上下文
            acknowledged_text = "true" if message_record.acknowledged_at else "false"  # 新增代码+TeamCommunicationLifecycle: 把确认状态转成人类可读布尔文本；若省略: 模型难以判断消息是否已处理
            lines.append(f"{index}. message_id={message_record.message_id} sender={message_record.sender} created_at={message_record.created_at} acknowledged={acknowledged_text}")  # 新增代码+TeamCommunicationLifecycle: 输出消息元信息；若省略: 模型无法选择要确认的 message_id
            lines.append(f"   content={message_preview}")  # 新增代码+TeamCommunicationLifecycle: 输出消息正文摘要；若省略: 读取 inbox 看不到真正消息内容
            if message_record.acknowledged_at:  # 新增代码+TeamCommunicationLifecycle: 如果消息已经确认；若省略: 已确认消息缺少处理时间和备注
                lines.append(f"   acknowledged_at={message_record.acknowledged_at}")  # 新增代码+TeamCommunicationLifecycle: 输出确认时间；若省略: 用户无法审计消息何时处理
                lines.append(f"   ack_note={message_record.ack_note or '(无备注)'}")  # 新增代码+TeamCommunicationLifecycle: 输出确认备注；若省略: 用户无法看到处理说明
        return "\n".join(lines)  # 新增代码+TeamCommunicationLifecycle: 返回完整消息列表文本；若省略: 工具无法把 inbox 内容交回模型

    def _ack_peer_message(self, arguments: dict[str, Any]) -> str:  # 新增代码+TeamCommunicationLifecycle: 执行 ack_peer_message 工具并确认一条消息；若省略: peer 消息无法标记已处理
        peer_id = str(arguments.get("peer_id", "") or "").strip()  # 新增代码+TeamCommunicationLifecycle: 读取并清理目标 peer_id；若省略: 工具不知道要操作哪个 peer
        if not peer_id:  # 新增代码+TeamCommunicationLifecycle: 检查 peer_id 是否为空；若省略: 空目标会产生模糊未知 peer 错误
            return "ack_peer_message 失败：缺少 peer_id 参数。"  # 新增代码+TeamCommunicationLifecycle: 返回清楚缺参错误；若省略: 模型难以修正 ack_peer_message 调用
        peer_record = self.team_peers.get(peer_id)  # 新增代码+TeamCommunicationLifecycle: 从登记表查找目标 peer；若省略: 工具无法定位 inbox
        if peer_record is None:  # 新增代码+TeamCommunicationLifecycle: 处理未知 peer_id；若省略: 访问 None 会抛异常
            try:  # 修改代码+DurableTeamRegistry: 内存没有时尝试从持久 registry 恢复；若没有这行代码，重启后的 ack_peer_message 会误报未知 peer。
                peer_record = self.team_registry.get_peer(peer_id)  # 新增代码+DurableTeamRegistry: 从磁盘恢复 peer 和 inbox；若没有这行代码，旧消息无法跨实例确认。
                self.team_peers[peer_id] = peer_record  # 新增代码+DurableTeamRegistry: 把恢复的 peer 放回内存缓存；若没有这行代码，本次后续操作会反复读磁盘。
            except KeyError:  # 新增代码+DurableTeamRegistry: 持久 registry 也没有该 peer 时才返回未知；若没有这行代码，真实未知 id 会抛底层异常。
                return f"ack_peer_message 失败：未知 peer_id：{peer_id}，请先调用 team_create 或 list_peers。"  # 修改代码+DurableTeamRegistry: 返回可恢复建议；若没有这行代码，模型不知道该先创建或查看 peer。
        message_id = str(arguments.get("message_id", "") or "").strip()  # 新增代码+TeamCommunicationLifecycle: 读取并清理 message_id；若省略: 工具不知道要确认哪条消息
        if not message_id:  # 新增代码+TeamCommunicationLifecycle: 检查 message_id 是否为空；若省略: 空消息目标会导致确认语义模糊
            return "ack_peer_message 失败：缺少 message_id 参数。"  # 新增代码+TeamCommunicationLifecycle: 返回清楚缺参错误；若省略: 模型难以修正 message_id
        message_record = next((message for message in peer_record.inbox if message.message_id == message_id), None)  # 新增代码+TeamCommunicationLifecycle: 在 inbox 中查找目标消息；若省略: 工具无法定位具体消息
        if message_record is None:  # 新增代码+TeamCommunicationLifecycle: 处理未知 message_id；若省略: 访问 None 会抛异常
            return f"ack_peer_message 失败：peer_id={peer_id} 中没有 message_id={message_id}。"  # 新增代码+TeamCommunicationLifecycle: 返回清楚未知消息错误；若省略: 模型难以判断是否需要先 read_peer_messages
        note = str(arguments.get("note", "") or "").strip()  # 新增代码+TeamCommunicationLifecycle: 读取确认备注；若省略: 用户无法保存处理说明
        if not message_record.acknowledged_at:  # 新增代码+TeamCommunicationLifecycle: 只在尚未确认时写入确认时间；若省略: 重复确认会覆盖首次处理时间
            message_record.acknowledged_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+TeamCommunicationLifecycle: 保存首次确认时间；若省略: 审计时不知道消息何时处理
        if note:  # 新增代码+TeamCommunicationLifecycle: 如果调用提供了确认备注；若省略: 备注更新不会执行
            message_record.ack_note = note  # 新增代码+TeamCommunicationLifecycle: 保存确认备注；若省略: 用户提供的处理说明会丢失
        pending_count = sum(1 for message in peer_record.inbox if not message.acknowledged_at)  # 新增代码+TeamCommunicationLifecycle: 重新统计待确认消息数；若省略: 返回结果无法说明剩余处理量
        peer_record.status = peer_status_from_pending_count(pending_count)  # 修改代码+TasksSplit: 委托 tasks.team 根据待确认消息数计算 peer 状态；若没有这行代码，peer 状态规则仍会散在主文件。
        self.team_registry.save_peer(peer_record)  # 新增代码+DurableTeamRegistry: 保存 ack 状态和 peer 状态；若没有这行代码，消息确认在重启后会丢失。
        return f"ack_peer_message 成功：peer_id={peer_id}\nmessage_id={message_id}\nacknowledged_at={message_record.acknowledged_at}\npending_count={pending_count}"  # 新增代码+TeamCommunicationLifecycle: 返回确认时间和剩余待处理数；若省略: 模型无法确认 ack 是否生效

    def _team_delete(self, arguments: dict[str, Any]) -> str:  # 新增代码+TeamCommunicationLifecycle: 执行 team_delete 工具并删除教学版 peer；若省略: peer 记录无法回收
        peer_id = str(arguments.get("peer_id", "") or "").strip()  # 新增代码+TeamCommunicationLifecycle: 读取并清理目标 peer_id；若省略: 工具不知道要删除哪个 peer
        if not peer_id:  # 新增代码+TeamCommunicationLifecycle: 检查 peer_id 是否为空；若省略: 空目标会产生模糊未知 peer 错误
            return "team_delete 失败：缺少 peer_id 参数。"  # 新增代码+TeamCommunicationLifecycle: 返回清楚缺参错误；若省略: 模型难以修正 team_delete 调用
        if arguments.get("confirm_delete") is not True:  # 新增代码+TeamCommunicationLifecycle: 要求显式 true 才执行删除；若省略: 模型可能在没有明确确认时删除 peer
            return "team_delete 失败：删除 peer 会丢弃该 peer 的进程内 inbox，请显式传入 confirm_delete=true。"  # 新增代码+TeamCommunicationLifecycle: 返回确认要求；若省略: 模型不知道如何安全重试删除
        peer_record = self.team_peers.pop(peer_id, None)  # 新增代码+TeamCommunicationLifecycle: 从登记表删除目标 peer；若省略: team_delete 只会返回文本但不会真正移除 peer
        if peer_record is None:  # 新增代码+TeamCommunicationLifecycle: 处理未知 peer_id；若省略: 删除不存在目标会被误认为成功
            try:  # 修改代码+DurableTeamRegistry: 内存没有时尝试删除持久 registry 里的 peer；若没有这行代码，重启后的 team_delete 会误报未知 peer。
                peer_record = self.team_registry.delete_peer(peer_id)  # 新增代码+DurableTeamRegistry: 从磁盘删除并返回 peer；若没有这行代码，旧 peer 无法跨实例清理。
            except KeyError:  # 新增代码+DurableTeamRegistry: 持久 registry 也没有该 peer 时才返回未知；若没有这行代码，真实未知 id 会抛底层异常。
                return f"team_delete 失败：未知 peer_id：{peer_id}，请先调用 list_peers。"  # 修改代码+DurableTeamRegistry: 返回可恢复建议；若没有这行代码，模型难以判断目标是否已经被删。
        else:  # 新增代码+DurableTeamRegistry: 内存里存在 peer 时也要同步删除磁盘记录；若没有这行代码，team_delete 后重启会把 peer 又恢复出来。
            try:  # 新增代码+DurableTeamRegistry: 持久记录可能已不存在，需要容错；若没有这行代码，内存删除会被磁盘缺失异常打断。
                self.team_registry.delete_peer(peer_id)  # 新增代码+DurableTeamRegistry: 删除持久 peer 文件；若没有这行代码，team_delete 只会删除当前进程缓存。
            except KeyError:  # 新增代码+DurableTeamRegistry: 兼容只有内存没有磁盘的旧状态；若没有这行代码，迁移前的临时 peer 不能删除。
                pass  # 新增代码+DurableTeamRegistry: 磁盘无记录时忽略；若没有这行代码，except 分支语法不完整。
        return f"team_delete 成功：已删除教学版 peer。\npeer_id={peer_id}\nname={peer_record.name}\ndropped_message_count={len(peer_record.inbox)}"  # 新增代码+TeamCommunicationLifecycle: 返回删除对象和丢弃消息数量；若省略: 用户无法审计删除了谁以及丢弃多少消息

    def _team_start_task(self, arguments: dict[str, Any]) -> str:  # 新增代码+TeamTaskBinding: 执行 team_start_task 并把 peer 绑定到后台 task；若省略: team 成员无法承接真实可查询子任务
        peer_id = str(arguments.get("peer_id", "") or "").strip()  # 新增代码+TeamTaskBinding: 读取并清理目标 peer_id；若省略: 工具不知道要让哪个 peer 启动任务
        if not peer_id:  # 新增代码+TeamTaskBinding: 检查 peer_id 是否为空；若省略: 空目标会产生模糊未知 peer 错误
            return "team_start_task 失败：缺少 peer_id 参数。"  # 新增代码+TeamTaskBinding: 返回清楚缺参错误；若省略: 模型难以修正 team_start_task 调用
        peer_record = self.team_peers.get(peer_id)  # 新增代码+TeamTaskBinding: 从登记表查找目标 peer；若省略: 工具无法定位要绑定的团队成员
        if peer_record is None:  # 新增代码+TeamTaskBinding: 处理未知 peer_id；若省略: 访问 None 会抛异常
            try:  # 修改代码+DurableTeamRegistry: 内存没有时尝试从持久 registry 恢复；若没有这行代码，重启后的 team_start_task 会误报未知 peer。
                peer_record = self.team_registry.get_peer(peer_id)  # 新增代码+DurableTeamRegistry: 从磁盘恢复 peer；若没有这行代码，旧 peer 无法继续绑定后台任务。
                self.team_peers[peer_id] = peer_record  # 新增代码+DurableTeamRegistry: 把恢复的 peer 放回内存缓存；若没有这行代码，本次绑定后续逻辑不方便复用。
            except KeyError:  # 新增代码+DurableTeamRegistry: 持久 registry 也没有该 peer 时才返回未知；若没有这行代码，真实未知 id 会抛底层异常。
                return f"team_start_task 失败：未知 peer_id：{peer_id}，请先调用 team_create 或 list_peers。"  # 修改代码+DurableTeamRegistry: 返回可恢复建议；若没有这行代码，模型不知道该先创建或查看 peer。
        prompt = str(arguments.get("prompt", "") or "").strip()  # 新增代码+TeamTaskBinding: 读取并清理子任务目标；若省略: 后台 task 没有可执行目标
        if not prompt:  # 新增代码+TeamTaskBinding: 检查 prompt 是否为空；若省略: 空任务会浪费子 agent 运行并产生模糊结果
            return "team_start_task 失败：缺少非空 prompt 参数。"  # 新增代码+TeamTaskBinding: 返回清楚缺参错误；若省略: 模型难以修正子任务目标
        existing_task = self.task_runs.get(peer_record.bound_task_id) if peer_record.bound_task_id else None  # 新增代码+TeamTaskBinding: 查找该 peer 已绑定的旧内存 task；若省略: 可能给同一 peer 重复启动多个未完成任务
        if existing_task is None and peer_record.bound_task_id:  # 新增代码+DurableTeamRegistry: 内存找不到旧 task 时尝试持久 registry；若没有这行代码，重启后可能重复启动同一 peer 的任务。
            try:  # 新增代码+DurableTeamRegistry: 持久任务可能不存在，需要容错；若没有这行代码，坏绑定会打断新任务启动。
                existing_task = self.task_registry.get_task(peer_record.bound_task_id)  # 新增代码+DurableTeamRegistry: 从磁盘读取旧绑定任务；若没有这行代码，team_start_task 无法跨实例保护运行中任务。
            except KeyError:  # 新增代码+DurableTeamRegistry: 旧绑定任务丢失时允许继续；若没有这行代码，历史坏状态会阻塞新任务。
                existing_task = None  # 新增代码+DurableTeamRegistry: 明确旧任务不存在；若没有这行代码，后续判断语义不清楚。
        if existing_task is not None and existing_task.status in {"pending", "running"}:  # 新增代码+TeamTaskBinding: 阻止同一 peer 同时绑定多个未完成任务；若省略: ownership 会变混乱
            return f"team_start_task 失败：peer_id={peer_id} 已绑定运行中的 task_id={existing_task.task_id}，请先 task_output 或 task_stop。"  # 新增代码+TeamTaskBinding: 返回旧任务 id 方便用户接管；若省略: 模型不知道该如何恢复
        task_arguments: dict[str, Any] = {"prompt": prompt, "background": True}  # 新增代码+TeamTaskBinding: 构造底层 task 参数并强制后台运行；若省略: team_start_task 可能阻塞主 agent
        if "allowed_tools" in arguments:  # 新增代码+TeamTaskBinding: 只有调用方提供工具白名单时才向底层 task 透传；若省略: 无法按 peer 职责收窄工具权限
            task_arguments["allowed_tools"] = arguments.get("allowed_tools")  # 新增代码+TeamTaskBinding: 透传 allowed_tools 给底层 task 校验和执行；若省略: team_start_task 的白名单参数不会生效
        if "max_turns" in arguments:  # 新增代码+TeamTaskBinding: 只有调用方提供轮次上限时才向底层 task 透传；若省略: 无法针对绑定任务调整执行长度
            task_arguments["max_turns"] = arguments.get("max_turns")  # 新增代码+TeamTaskBinding: 透传 max_turns 给底层 task 校验和执行；若省略: team_start_task 的轮次参数不会生效
        task_output = self._task(task_arguments)  # 新增代码+TeamTaskBinding: 复用现有 task 生命周期实现启动后台子 agent；若省略: 会重复造任务系统且 task_output/task_stop 接不上
        if not task_output.startswith("task 成功"):  # 新增代码+TeamTaskBinding: 检查底层 task 是否启动成功；若省略: 失败 task 也可能被误绑定到 peer
            return f"team_start_task 失败：后台 task 启动失败。\n{task_output}"  # 新增代码+TeamTaskBinding: 把底层失败原因带回；若省略: 模型无法知道 allowed_tools/max_turns 等参数哪里错
        task_id_line = next((line for line in task_output.splitlines() if line.startswith("task_id=")), "")  # 新增代码+TeamTaskBinding: 从底层 task 输出提取 task_id 行；若省略: peer 记录无法保存可查询任务 id
        if not task_id_line:  # 新增代码+TeamTaskBinding: 防御底层 task 成功文本缺少 task_id 的异常情况；若省略: split 后可能得到空 id 并污染 peer 记录
            return f"team_start_task 失败：后台 task 已返回成功但缺少 task_id。\n{task_output}"  # 新增代码+TeamTaskBinding: 返回完整底层输出方便排查；若省略: 用户不知道失败发生在绑定阶段
        task_id = task_id_line.split("=", 1)[1].strip()  # 新增代码+TeamTaskBinding: 提取 task_id 字符串用于绑定 peer；若省略: 后续 task_output/task_stop 无法定位任务
        task_record = self.task_runs.get(task_id)  # 新增代码+TeamTaskBinding: 读取刚启动的任务记录以取得当前状态；若省略: 返回结果无法反映真实任务表状态
        task_status = task_record.status if task_record is not None else "running"  # 新增代码+TeamTaskBinding: 选择任务当前状态并用 running 兜底；若省略: 绑定成功文本缺少可读状态
        peer_record.bound_task_id = task_id  # 新增代码+TeamTaskBinding: 把后台 task id 写入 peer 记录；若省略: list_peers 无法展示 peer 与 task 的连接
        peer_record.bound_task_started_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+TeamTaskBinding: 记录绑定任务启动时间；若省略: 用户无法审计 peer 何时开始工作
        peer_record.status = "active"  # 新增代码+TeamTaskBinding: 把承接任务的 peer 标记为 active；若省略: list_peers 可能显示正在执行任务的 peer 仍然 idle
        self.team_registry.save_peer(peer_record)  # 新增代码+DurableTeamRegistry: 保存 peer 与后台 task 的绑定关系；若没有这行代码，重启后 team 视图会丢失绑定。
        return f"team_start_task 成功：peer 已绑定后台 task。\npeer_id={peer_id}\ntask_id={task_id}\nstatus={task_status}\nbackground=true\nbound_task_started_at={peer_record.bound_task_started_at}"  # 新增代码+TeamTaskBinding: 返回 peer/task 绑定结果和可查询 id；若省略: 模型无法继续用 task_output/task_stop 管理任务

    def _task_background_enabled(self, raw_background: Any) -> bool:  # 新增代码+AsyncTask: 统一解析 task.background 参数；若省略: 模型传入布尔或字符串时语义可能不一致
        return task_background_enabled(raw_background)  # 修改代码+TasksSplit: 委托 tasks.task_runs 解析后台开关；若没有这行代码，task 参数兼容逻辑仍会留在主文件里。

    def _task_allowed_tool_names(self, raw_allowed_tools: Any) -> set[str] | str:  # 修改代码+ToolPolicyV2: 解析 task allowed_tools 时区分默认继承和显式白名单；若没有这行代码，显式 MCP 工具可能被父 visible 过滤提前清空
        blocked_task_tool_names = set(BLOCKED_TASK_TOOL_NAMES)  # 修改代码+TasksSplit: 从 tasks.task_runs 读取禁止子 agent 继承的任务工具集合；若没有这行代码，递归 task 风险清单仍会散在主文件。
        default_tool_names = set(self._tool_schema_names())  # 修改代码+ToolPolicyV2: 默认省略 allowed_tools 时仍只从父当前可见工具池继承；若没有这行代码，默认子任务可能拿到被 deny 或 hidden 的工具
        default_tool_names.difference_update(blocked_task_tool_names)  # 修改代码+ToolPolicyV2: 默认继承时移除 task 管理工具；若没有这行代码，省略 allowed_tools 的子 agent 可能递归建 task 或操作父任务
        if raw_allowed_tools is None:  # 修改代码+ToolPolicyV2: 省略 allowed_tools 时走父当前 visible 工具池边界；若没有这行代码，默认场景会和显式白名单混在一起导致越权
            return default_tool_names  # 修改代码+ToolPolicyV2: 返回默认可继承工具集合；若没有这行代码，省略 allowed_tools 的子 agent 没有稳定权限边界
        if not isinstance(raw_allowed_tools, list):  # 新增代码+TaskAgent: allowed_tools 必须是列表；若省略: 字符串会被逐字符误解析
            return "task 失败：allowed_tools 必须是工具名字符串数组。"  # 新增代码+TaskAgent: 返回清楚类型错误；若省略: 模型难以修正 allowed_tools 参数
        cleaned_tool_names = {str(tool_name).strip() for tool_name in raw_allowed_tools if str(tool_name).strip()}  # 新增代码+TaskAgent: 清理白名单工具名并丢弃空字符串；若省略: 空白工具名会进入过滤集合
        cleaned_tool_names.difference_update(blocked_task_tool_names)  # 修改代码+ToolPolicyV2: 显式白名单中也移除 task 管理工具；若没有这行代码，模型传入 task 可能造成递归委派或父任务越权
        catalog_tool_names = {tool.name for tool in self._tool_catalog()}  # 新增代码+ToolPolicyV2: 显式 allowed_tools 用完整 catalog 判断工具是否存在；若没有这行代码，父侧 deny 后目标 MCP 工具会因不可见而被提前丢弃
        explicit_allowed_tool_names = catalog_tool_names | set(self.loaded_tool_names)  # 新增代码+ToolPolicyV2: 显式 allowed_tools 额外允许父 agent 已加载 deferred 工具名；若没有这行代码，已 select 的外部工具可能无法传入子 agent
        explicit_allowed_tool_names.difference_update(blocked_task_tool_names)  # 新增代码+ToolPolicyV2: 完整 catalog 合法集合也移除递归和任务管理工具；若没有这行代码，显式白名单可能绕过禁止 task 规则
        return cleaned_tool_names & explicit_allowed_tool_names  # 修改代码+ToolPolicyV2: 显式白名单只过滤不存在或禁止的工具，不再受父当前 visible 状态影响；若没有这行代码，child policy deny 过滤无法被真实验证

    def _task_max_turns(self, raw_max_turns: Any) -> int | str:  # 新增代码+TaskAgent: 解析 task max_turns 参数；若省略: 子 agent 轮次规则会重复且不清晰
        if raw_max_turns is None:  # 新增代码+TaskAgent: 省略 max_turns 时使用保守默认值；若省略: 子 agent 可能默认无固定上限
            return 3  # 新增代码+TaskAgent: 默认允许 3 轮模型-工具循环；若省略: 子任务可能太早停止或运行过久
        try:  # 新增代码+TaskAgent: 捕获 max_turns 非法值；若省略: parse_max_turns_value 的异常会中断 agent
            parsed_max_turns = parse_max_turns_value(raw_max_turns, "task.max_turns")  # 新增代码+TaskAgent: 复用已有轮次解析规则；若省略: task 和主 agent 的轮次语义会不一致
        except ValueError as error:  # 新增代码+TaskAgent: 处理非法 max_turns；若省略: 用户会看到底层异常
            return f"task 失败：{error}"  # 新增代码+TaskAgent: 返回可读失败信息；若省略: 模型难以修正轮次参数
        if parsed_max_turns is None:  # 新增代码+TaskAgent: task 不接受无限制子 agent；若省略: 子任务可能无界运行
            return "task 失败：max_turns 必须是大于等于 1 的整数，task 子 agent 暂不接受无限制轮次。"  # 新增代码+TaskAgent: 明确拒绝无限制轮次；若省略: 模型不知道为什么 none 不被接受
        return parsed_max_turns  # 新增代码+TaskAgent: 返回合法正整数轮次；若省略: 子 agent run 拿不到轮次上限

    def _task_child_prompt(self, prompt: str) -> str:  # 新增代码+TaskAgent: 构造子 agent 专用 prompt；若省略: 子 agent 缺少统一执行边界说明
        return task_child_prompt(prompt)  # 修改代码+TasksSplit: 委托 tasks.task_runs 构造子 agent prompt；若没有这行代码，子任务提示词边界仍会藏在主类。

    def _enter_worktree(self, arguments: dict[str, Any]) -> str:  # 新增代码+WorktreeIsolation: 执行进入轻量 worktree 隔离状态工具；若省略: agent 只有工具 schema 没有实际状态切换
        if self.worktree_state.get("active"):  # 新增代码+WorktreeIsolation: 检查是否已经处于隔离状态；若省略: 模型可能嵌套进入多个隔离上下文导致边界混乱
            return "enter_worktree 失败：当前已经处于工作区隔离状态，请先调用 exit_worktree 退出。"  # 新增代码+WorktreeIsolation: 返回清楚的重复进入错误；若省略: 模型难以修正调用顺序
        reason = str(arguments.get("reason", "") or "").strip()  # 新增代码+WorktreeIsolation: 读取并清理进入隔离状态原因；若省略: 用户看不到为什么需要隔离
        goal = str(arguments.get("goal", "") or "").strip()  # 新增代码+WorktreeIsolation: 读取并清理隔离工作目标；若省略: 后续退出时缺少核对方向
        raw_worktree_path = str(arguments.get("worktree_path", "") or "").strip()  # 新增代码+WorktreeIsolation: 读取并清理隔离目录路径；若省略: 工具无法知道隔离上下文指向哪里
        if not reason:  # 新增代码+WorktreeIsolation: 检查 reason 是否为空；若省略: 模型可能用空原因进入隔离状态
            return "enter_worktree 失败：缺少非空 reason 参数。"  # 新增代码+WorktreeIsolation: 返回清楚缺参错误；若省略: 模型难以修正进入隔离状态参数
        if not goal:  # 新增代码+WorktreeIsolation: 检查 goal 是否为空；若省略: 模型可能在没有目标时进入隔离状态
            return "enter_worktree 失败：缺少非空 goal 参数。"  # 新增代码+WorktreeIsolation: 返回清楚缺参错误；若省略: 模型难以修正进入隔离状态参数
        if not raw_worktree_path:  # 新增代码+WorktreeIsolation: 检查 worktree_path 是否为空；若省略: 隔离状态会缺少路径边界
            return "enter_worktree 失败：缺少非空 worktree_path 参数。"  # 新增代码+WorktreeIsolation: 返回清楚缺参错误；若省略: 模型难以补充隔离目录
        resolved_worktree_path = self._resolve_workspace_path(raw_worktree_path)  # 新增代码+WorktreeIsolation: 把隔离目录解析并限制在工作区内；若省略: 模型可能把隔离上下文指到工作区外
        if resolved_worktree_path is None:  # 修改代码+Stage14硬清理: 恢复 worktree 路径越界检查；若没有这行代码，越界路径会继续进入状态记录
            return "enter_worktree 失败：worktree_path 必须位于工作区内。"  # 修改代码+Stage14硬清理: 对越界路径返回可读失败；若没有这行代码，模型不知道如何修正 worktree_path
        relative_worktree_path = resolved_worktree_path.relative_to(self.workspace).as_posix()  # 修改代码+Stage14硬清理: 恢复工作区相对路径展示值；若没有这行代码，后续输出和状态会引用未定义变量
        fallback_reason = "当前 learning_agent 教学版只记录隔离上下文，未创建真实 git worktree。"  # 修改代码+Stage14硬清理: 恢复状态型 fallback 原因；若没有这行代码，用户看不到当前隔离强度边界
        self.worktree_state = {"active": True, "reason": reason, "goal": goal, "worktree_path": relative_worktree_path, "mode": "state_only_fallback", "fallback_reason": fallback_reason}  # 修改代码+Stage14硬清理: 恢复进入 worktree 时的状态写入；若没有这行代码，exit_worktree 无法知道当前隔离上下文
        lines = [  # 新增代码+WorktreeIsolation: 准备返回给模型和用户看的状态文本；若省略: 工具结果缺少关键上下文
            "enter_worktree 成功：已进入轻量工作区隔离状态。",  # 新增代码+WorktreeIsolation: 输出成功前缀；若省略: 调用方难以判断工具是否成功
            "mode=state_only_fallback",  # 新增代码+WorktreeFallback: 输出当前模式是状态记录 fallback；若没有这行代码，模型难以判断隔离强度
            f"fallback_reason={fallback_reason}",  # 新增代码+WorktreeFallback: 输出为什么没有创建真实 git worktree；若没有这行代码，用户看不到 Phase 5 的明确边界
            f"reason={reason}",  # 新增代码+WorktreeIsolation: 输出进入隔离状态原因；若省略: 用户看不到隔离动机
            f"goal={goal}",  # 新增代码+WorktreeIsolation: 输出隔离工作目标；若省略: 后续工作缺少目标锚点
            f"worktree_path={relative_worktree_path}",  # 新增代码+WorktreeIsolation: 输出隔离目录相对路径；若省略: 用户无法确认隔离上下文位置
            "边界：该工具只记录状态，不创建真实 git worktree，不创建目录，也不执行命令。",  # 新增代码+WorktreeIsolation: 明确工具没有真实副作用；若省略: 模型可能误以为目录已经创建
        ]  # 新增代码+WorktreeIsolation: 完成返回文本列表；若省略: 后续 join 没有内容来源
        return "\n".join(lines)  # 新增代码+WorktreeIsolation: 返回完整进入隔离状态结果；若省略: 工具无法把状态交回模型

    def _exit_worktree(self, arguments: dict[str, Any]) -> str:  # 新增代码+WorktreeIsolation: 执行退出轻量 worktree 隔离状态工具；若省略: agent 无法结构化结束隔离上下文
        if not self.worktree_state.get("active"):  # 新增代码+WorktreeIsolation: 确认已经先进入隔离状态；若省略: 模型可以绕过 enter_worktree 直接退出
            return "exit_worktree 失败：请先调用 enter_worktree 进入工作区隔离状态，再调用 exit_worktree 退出。"  # 新增代码+WorktreeIsolation: 返回清楚顺序错误；若省略: 模型难以修正调用顺序
        summary = str(arguments.get("summary", "") or "").strip()  # 新增代码+WorktreeIsolation: 读取并清理退出总结；若省略: 用户看不到隔离工作结果
        if not summary:  # 新增代码+WorktreeIsolation: 检查 summary 是否为空；若省略: 空交接可能被当作成功
            return "exit_worktree 失败：缺少非空 summary 参数。"  # 新增代码+WorktreeIsolation: 返回清楚缺参错误；若省略: 模型难以补充退出总结
        open_items = self._plan_verification_optional_items(arguments.get("open_items"))  # 新增代码+WorktreeIsolation: 复用数组清理逻辑解析未完成事项；若省略: 风险项输出会重复实现且易错
        result_text = str(arguments.get("result", "") or "").strip().lower()  # 新增代码+WorktreeIsolation: 读取模型自评结论并统一成小写；若省略: blocked/failed 等状态无法参与判断
        incomplete_markers = {"incomplete", "blocked", "failed", "missing", "partial"}  # 新增代码+WorktreeIsolation: 定义会强制判为未完成的状态词；若省略: 明确失败结果可能仍被误判为 finished
        status = "incomplete" if open_items or result_text in incomplete_markers else (result_text or "finished")  # 新增代码+WorktreeIsolation: 根据风险项和自评结论计算退出状态；若省略: 用户无法快速判断隔离工作是否收尾
        previous_reason = str(self.worktree_state.get("reason", "") or "")  # 新增代码+WorktreeIsolation: 读取进入隔离状态时保存的原因；若省略: 退出输出缺少前后衔接
        previous_goal = str(self.worktree_state.get("goal", "") or "")  # 新增代码+WorktreeIsolation: 读取进入隔离状态时保存的目标；若省略: 退出输出缺少目标上下文
        previous_path = str(self.worktree_state.get("worktree_path", "") or "")  # 新增代码+WorktreeIsolation: 读取进入隔离状态时保存的路径；若省略: 退出输出缺少隔离上下文位置
        previous_mode = str(self.worktree_state.get("mode", "") or "state_only_fallback")  # 新增代码+WorktreeFallback: 读取进入隔离状态时的隔离模式；若没有这行代码，退出摘要无法保留真实 worktree 与 fallback 的区别
        self.worktree_state = {"active": False, "last_reason": previous_reason, "last_goal": previous_goal, "last_worktree_path": previous_path, "last_mode": previous_mode, "summary": summary, "status": status, "open_items": open_items}  # 修改代码+WorktreeFallback: 退出时保存最后隔离模式；若没有这行代码，后续审计无法知道上次隔离只是状态型 fallback
        lines = [  # 新增代码+WorktreeIsolation: 准备结构化退出摘要行；若省略: 工具无法输出可审计结果
            "exit_worktree 成功：已退出轻量工作区隔离状态。",  # 新增代码+WorktreeIsolation: 输出成功前缀；若省略: 调用方难以判断工具是否成功
            f"status={status}",  # 新增代码+WorktreeIsolation: 输出最终状态；若省略: 用户无法快速判断隔离工作结论
            f"worktree_path={previous_path}",  # 新增代码+WorktreeIsolation: 输出隔离目录相对路径；若省略: 用户无法知道退出的是哪个上下文
            f"reason={previous_reason}",  # 新增代码+WorktreeIsolation: 输出进入原因；若省略: 退出结果缺少背景
            f"goal={previous_goal}",  # 新增代码+WorktreeIsolation: 输出进入目标；若省略: 退出结果缺少目标核对
            "总结：",  # 新增代码+WorktreeIsolation: 添加总结标题；若省略: summary 和字段行容易混在一起
            summary,  # 新增代码+WorktreeIsolation: 输出隔离工作总结；若省略: 用户不知道隔离上下文做了什么
        ]  # 新增代码+WorktreeIsolation: 完成基础退出摘要列表；若省略: 后续追加内容没有容器
        if open_items:  # 新增代码+WorktreeIsolation: 如果存在未完成或风险项；若省略: 无法决定是否输出风险详情
            lines.append("未完成/风险项：")  # 新增代码+WorktreeIsolation: 添加风险项标题；若省略: 风险内容语义不清楚
            lines.extend(f"{index}. {item}" for index, item in enumerate(open_items, start=1))  # 新增代码+WorktreeIsolation: 编号输出每个遗漏或风险项；若省略: 用户不知道具体还缺什么
        else:  # 新增代码+WorktreeIsolation: 如果没有遗漏或风险项；若省略: 用户可能不确定 open_items 为空是否代表没有风险
            lines.append("未完成/风险项：(无)")  # 新增代码+WorktreeIsolation: 明确说明没有遗漏项；若省略: 退出摘要缺少关闭语义
        return "\n".join(lines)  # 新增代码+WorktreeIsolation: 返回完整退出隔离状态结果；若省略: 工具无法把交接结果交回模型

    def _lsp_symbols(self, arguments: dict[str, Any]) -> str:  # 新增代码+LSP工具: 执行 Python 文件符号读取工具；若省略: schema 暴露后仍没有实际符号读取能力
        loaded_file = self._lsp_python_file(arguments, "lsp_symbols")  # 新增代码+LSP工具: 解析并读取工作区内 Python 文件；若省略: 符号工具会重复路径和文件校验逻辑
        if isinstance(loaded_file, str):  # 新增代码+LSP工具: 判断读取前置校验是否失败；若省略: 错误文本会被当成文件元组继续解析
            return loaded_file  # 新增代码+LSP工具: 把清楚的失败原因返回给模型；若省略: 模型不知道如何修正 path 参数
        source_path, source_text = loaded_file  # 新增代码+LSP工具: 拆出源码路径和文本；若省略: 后续 AST 解析拿不到输入
        symbols = self._lsp_python_symbols(source_text, str(source_path), "lsp_symbols")  # 新增代码+LSP工具: 从源码中提取类、方法和函数符号；若省略: lsp_symbols 只能读文件不能理解结构
        if isinstance(symbols, str):  # 新增代码+LSP工具: 判断源码解析是否失败；若省略: 语法错误文本会被当成符号列表处理
            return symbols  # 新增代码+LSP工具: 返回语法解析失败原因；若省略: 模型看不到符号读取失败的行列信息
        max_results = self._tool_search_max_results(arguments.get("max_results"))  # 新增代码+LSP工具: 复用工具搜索的 1 到 20 结果数限制；若省略: 大文件符号列表可能过长
        visible_symbols = symbols[:max_results]  # 新增代码+LSP工具: 截取本次返回的符号数量；若省略: max_results 参数不会生效
        relative_path = source_path.relative_to(self.workspace).as_posix()  # 新增代码+LSP工具: 把绝对路径转成工作区相对路径；若省略: 输出会暴露更长本机绝对路径且不便阅读
        lines = [  # 新增代码+LSP工具: 准备结构化符号输出；若省略: 工具结果无法稳定被模型读取
            "lsp_symbols 成功：已读取 Python 文件符号。",  # 新增代码+LSP工具: 输出成功前缀；若省略: 调用方难以判断工具是否成功
            f"path={relative_path}",  # 新增代码+LSP工具: 输出被分析文件路径；若省略: 多文件排查时无法知道结果来自哪里
            f"symbol_count={len(symbols)}",  # 新增代码+LSP工具: 输出总符号数；若省略: 模型不知道是否发生截断
            f"returned_count={len(visible_symbols)}",  # 新增代码+LSP工具: 输出实际返回符号数；若省略: max_results 截断不透明
        ]  # 新增代码+LSP工具: 基础输出列表结束；若省略: 后续追加符号没有容器
        if visible_symbols:  # 新增代码+LSP工具: 如果存在可展示符号；若省略: 空列表和非空列表无法分支
            lines.append("符号：")  # 新增代码+LSP工具: 添加符号标题；若省略: 字段行和符号行语义不清楚
            lines.extend(self._lsp_symbol_line(symbol) for symbol in visible_symbols)  # 新增代码+LSP工具: 格式化每个符号；若省略: 模型拿不到符号名称和行号
        else:  # 新增代码+LSP工具: 如果没有任何符号；若省略: 空文件会返回没有结尾说明的结果
            lines.append("符号：(无)")  # 新增代码+LSP工具: 明确说明没有符号；若省略: 模型可能误以为工具输出被截断
        return "\n".join(lines)  # 新增代码+LSP工具: 返回完整符号列表；若省略: 工具结果无法交回模型

    def _lsp_definition(self, arguments: dict[str, Any]) -> str:  # 新增代码+LSP工具: 执行 Python 符号定义定位工具；若省略: schema 暴露后仍没有实际跳转定义能力
        symbol_name = str(arguments.get("symbol", "") or "").strip()  # 新增代码+LSP工具: 读取并清理目标符号名；若省略: 工具不知道要定位哪个定义
        if not symbol_name:  # 新增代码+LSP工具: 检查 symbol 是否为空；若省略: 空符号名会被当作合法搜索
            return "lsp_definition 失败：缺少非空 symbol 参数。"  # 新增代码+LSP工具: 返回清楚缺参错误；若省略: 模型难以补齐 symbol 参数
        loaded_file = self._lsp_python_file(arguments, "lsp_definition")  # 新增代码+LSP工具: 解析并读取工作区内 Python 文件；若省略: 定义工具会重复路径和文件校验逻辑
        if isinstance(loaded_file, str):  # 新增代码+LSP工具: 判断读取前置校验是否失败；若省略: 错误文本会被当成文件元组继续解析
            return loaded_file  # 新增代码+LSP工具: 把清楚的失败原因返回给模型；若省略: 模型不知道如何修正 path 参数
        source_path, source_text = loaded_file  # 新增代码+LSP工具: 拆出源码路径和文本；若省略: 后续 AST 解析拿不到输入
        symbols = self._lsp_python_symbols(source_text, str(source_path), "lsp_definition")  # 新增代码+LSP工具: 读取当前文件中的符号索引；若省略: 无法按名称查找定义
        if isinstance(symbols, str):  # 新增代码+LSP工具: 判断源码解析是否失败；若省略: 语法错误文本会被当成符号列表处理
            return symbols  # 新增代码+LSP工具: 返回语法解析失败原因；若省略: 模型看不到定义定位失败的行列信息
        matches = [symbol for symbol in symbols if str(symbol.get("name", "")) == symbol_name]  # 新增代码+LSP工具: 按符号名精确匹配定义；若省略: 工具无法筛出目标符号
        relative_path = source_path.relative_to(self.workspace).as_posix()  # 新增代码+LSP工具: 把绝对路径转成工作区相对路径；若省略: 输出会暴露更长本机绝对路径且不便阅读
        lines = [  # 新增代码+LSP工具: 准备结构化定义输出；若省略: 工具结果无法稳定被模型读取
            "lsp_definition 成功：已定位 Python 符号定义。",  # 新增代码+LSP工具: 输出成功前缀；若省略: 调用方难以判断工具是否成功
            f"path={relative_path}",  # 新增代码+LSP工具: 输出被分析文件路径；若省略: 多文件排查时无法知道结果来自哪里
            f"symbol={symbol_name}",  # 新增代码+LSP工具: 输出目标符号名；若省略: 用户无法核对查找对象
            f"match_count={len(matches)}",  # 新增代码+LSP工具: 输出匹配数量；若省略: 模型不知道是否未找到或有多个定义
        ]  # 新增代码+LSP工具: 基础输出列表结束；若省略: 后续追加定义没有容器
        if matches:  # 新增代码+LSP工具: 如果找到了匹配定义；若省略: 找到和未找到无法分支
            lines.append("定义：")  # 新增代码+LSP工具: 添加定义标题；若省略: 字段行和定义行语义不清楚
            lines.extend(self._lsp_symbol_line(symbol) for symbol in matches)  # 新增代码+LSP工具: 格式化每个匹配定义；若省略: 模型拿不到定义行号
        else:  # 新增代码+LSP工具: 如果没有找到匹配定义；若省略: 空结果会缺少明确说明
            lines.append("定义：(未找到)")  # 新增代码+LSP工具: 明确说明没有匹配；若省略: 模型可能误以为工具失败或输出截断
        return "\n".join(lines)  # 新增代码+LSP工具: 返回完整定义定位结果；若省略: 工具结果无法交回模型

    def _lsp_diagnostics(self, arguments: dict[str, Any]) -> str:  # 新增代码+LSP工具: 执行 Python 语法诊断工具；若省略: schema 暴露后仍没有实际诊断能力
        loaded_file = self._lsp_python_file(arguments, "lsp_diagnostics")  # 新增代码+LSP工具: 解析并读取工作区内 Python 文件；若省略: 诊断工具会重复路径和文件校验逻辑
        if isinstance(loaded_file, str):  # 新增代码+LSP工具: 判断读取前置校验是否失败；若省略: 错误文本会被当成文件元组继续解析
            return loaded_file  # 新增代码+LSP工具: 把清楚的失败原因返回给模型；若省略: 模型不知道如何修正 path 参数
        source_path, source_text = loaded_file  # 新增代码+LSP工具: 拆出源码路径和文本；若省略: 后续语法解析拿不到输入
        relative_path = source_path.relative_to(self.workspace).as_posix()  # 新增代码+LSP工具: 把绝对路径转成工作区相对路径；若省略: 输出会暴露更长本机绝对路径且不便阅读
        try:  # 新增代码+LSP工具: 使用 AST 解析触发 Python 语法检查；若省略: 诊断工具无法发现 SyntaxError
            ast.parse(source_text, filename=str(source_path))  # 新增代码+LSP工具: 解析源码但不执行源码；若省略: 诊断没有实际检查动作
        except SyntaxError as error:  # 新增代码+LSP工具: 捕获语法错误并转成 LSP 风格诊断；若省略: 语法错误会中断工具调用
            lines = [  # 新增代码+LSP工具: 准备语法错误诊断输出；若省略: 诊断结果无法稳定展示
                "lsp_diagnostics 成功：已读取 Python 语法诊断。",  # 新增代码+LSP工具: 输出成功前缀；若省略: 诊断工具语义会和工具失败混淆
                f"path={relative_path}",  # 新增代码+LSP工具: 输出被诊断文件路径；若省略: 多文件排查时无法知道结果来自哪里
                "diagnostic_count=1",  # 新增代码+LSP工具: 输出诊断数量；若省略: 模型不知道是否存在错误
                "诊断：",  # 新增代码+LSP工具: 添加诊断标题；若省略: 字段行和诊断行语义不清楚
                self._lsp_diagnostic_line(error),  # 新增代码+LSP工具: 输出错误级别、行列和消息；若省略: 模型无法定位语法错误
            ]  # 新增代码+LSP工具: 语法错误诊断输出列表结束；若省略: 返回内容没有容器
            return "\n".join(lines)  # 新增代码+LSP工具: 返回语法错误诊断；若省略: 工具无法把诊断交回模型
        return "\n".join([  # 新增代码+LSP工具: 返回无诊断时的结构化结果；若省略: 语法正常文件没有明确成功输出
            "lsp_diagnostics 成功：已读取 Python 语法诊断。",  # 新增代码+LSP工具: 输出成功前缀；若省略: 调用方难以判断工具是否成功
            f"path={relative_path}",  # 新增代码+LSP工具: 输出被诊断文件路径；若省略: 多文件排查时无法知道结果来自哪里
            "diagnostic_count=0",  # 新增代码+LSP工具: 明确说明没有诊断；若省略: 模型可能以为空结果是工具失败
            "诊断：(无)",  # 新增代码+LSP工具: 用中文说明语法层面未发现错误；若省略: 用户看不到关闭语义
        ])  # 新增代码+LSP工具: 合并并返回无诊断文本；若省略: 工具结果无法交回模型

    def _lsp_python_file(self, arguments: dict[str, Any], tool_name: str) -> tuple[Path, str] | str:  # 新增代码+LSP工具: 统一解析和读取 LSP Python 文件输入；若省略: 三个 LSP 工具会重复安全校验
        raw_path = str(arguments.get("path", "") or "").strip()  # 新增代码+LSP工具: 读取并清理 path 参数；若省略: 空白路径会进入文件系统解析
        if not raw_path:  # 新增代码+LSP工具: 检查 path 是否为空；若省略: 空路径可能误指向工作区根目录
            return f"{tool_name} 失败：缺少非空 path 参数。"  # 新增代码+LSP工具: 返回清楚缺参错误；若省略: 模型难以补齐 path 参数
        source_path = self._resolve_workspace_path(raw_path)  # 新增代码+LSP工具: 使用现有路径安全函数限制在工作区内；若省略: LSP 工具可能越界读取本机文件
        if source_path is None:  # 新增代码+LSP工具: 判断路径是否越出工作区；若省略: None 会被当成 Path 使用并报底层错误
            return f"{tool_name} 失败：path 必须指向工作区内文件。"  # 新增代码+LSP工具: 返回工作区边界错误；若省略: 模型不知道要改成相对工作区路径
        if not source_path.exists():  # 新增代码+LSP工具: 检查目标文件是否存在；若省略: 读取不存在文件会抛异常
            return f"{tool_name} 失败：文件不存在：{raw_path}"  # 新增代码+LSP工具: 返回不存在文件错误；若省略: 模型难以修正路径拼写
        if not source_path.is_file():  # 新增代码+LSP工具: 检查目标是否为普通文件；若省略: 目录路径会被当作文件读取
            return f"{tool_name} 失败：path 必须指向文件而不是目录：{raw_path}"  # 新增代码+LSP工具: 返回目录误用错误；若省略: 模型不知道路径类型不对
        if source_path.suffix != ".py":  # 新增代码+LSP工具: 当前最小版只支持 Python 文件；若省略: 其他语言会进入 AST 解析并产生误导错误
            return f"{tool_name} 失败：当前 LSP 最小版只支持 .py 文件。"  # 新增代码+LSP工具: 明确语言范围；若省略: 模型可能误以为完整 LSP 已经支持所有语言
        try:  # 新增代码+LSP工具: 捕获读取文件时的系统错误；若省略: 权限或编码问题会中断工具调用
            source_text = source_path.read_text(encoding="utf-8", errors="replace")  # 新增代码+LSP工具: 读取 UTF-8 源码并替换坏字符；若省略: 文件内容无法进入 AST 解析
        except OSError as error:  # 新增代码+LSP工具: 捕获文件读取失败；若省略: 用户会看到底层 traceback
            return f"{tool_name} 失败：读取文件失败：{error}"  # 新增代码+LSP工具: 返回清楚读取错误；若省略: 模型不知道失败来自文件读取
        return source_path, source_text  # 新增代码+LSP工具: 返回安全路径和源码文本；若省略: 调用方拿不到 LSP 分析输入

    def _lsp_python_symbols(self, source_text: str, source_name: str, tool_name: str) -> list[dict[str, Any]] | str:  # 新增代码+LSP工具: 用 AST 提取 Python 顶层类、方法和函数符号；若省略: 符号和定义工具没有共同索引
        try:  # 新增代码+LSP工具: 捕获源码语法错误；若省略: SyntaxError 会中断符号提取
            tree = ast.parse(source_text, filename=source_name)  # 新增代码+LSP工具: 解析源码为 AST 但不执行代码；若省略: 无法安全读取符号结构
        except SyntaxError as error:  # 新增代码+LSP工具: 捕获语法错误并返回可读失败；若省略: 模型看不到行列和错误消息
            return self._lsp_syntax_error_failure(tool_name, error)  # 新增代码+LSP工具: 转成统一失败文本；若省略: 三个工具的语法错误格式会不一致
        symbols: list[dict[str, Any]] = []  # 新增代码+LSP工具: 准备保存提取到的符号；若省略: 后续无法累积结果
        for node in tree.body:  # 新增代码+LSP工具: 遍历模块顶层语句；若省略: 顶层类和函数不会被发现
            if isinstance(node, ast.ClassDef):  # 新增代码+LSP工具: 识别顶层类定义；若省略: 类符号不会出现在结果里
                symbols.append(self._lsp_symbol_dict("class", node.name, node, ""))  # 新增代码+LSP工具: 记录类名和行号；若省略: 模型无法定位类定义
                for child in node.body:  # 新增代码+LSP工具: 遍历类内部成员；若省略: 类方法不会被发现
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):  # 新增代码+LSP工具: 识别同步和异步方法；若省略: 方法符号不会出现在结果里
                        method_kind = "async_method" if isinstance(child, ast.AsyncFunctionDef) else "method"  # 新增代码+LSP工具: 区分异步方法和普通方法；若省略: async def 的语义会丢失
                        symbols.append(self._lsp_symbol_dict(method_kind, child.name, child, node.name))  # 新增代码+LSP工具: 记录方法并附带所属类名；若省略: 模型难以区分方法归属
                continue  # 新增代码+LSP工具: 类节点处理完成后跳过函数分支；若省略: 类节点还会继续参与后续顶层函数判断
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):  # 新增代码+LSP工具: 识别顶层同步和异步函数；若省略: 函数符号不会出现在结果里
                function_kind = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"  # 新增代码+LSP工具: 区分异步函数和普通函数；若省略: async def 的语义会丢失
                symbols.append(self._lsp_symbol_dict(function_kind, node.name, node, ""))  # 新增代码+LSP工具: 记录顶层函数名和行号；若省略: 模型无法定位函数定义
        return symbols  # 新增代码+LSP工具: 返回完整符号列表；若省略: 调用方拿不到 AST 分析结果

    def _lsp_symbol_dict(self, kind: str, name: str, node: ast.AST, container: str) -> dict[str, Any]:  # 新增代码+LSP工具: 统一把 AST 节点转成符号字典；若省略: 类、方法和函数的字段格式容易不一致
        line_number = int(getattr(node, "lineno", 0) or 0)  # 新增代码+LSP工具: 读取符号起始行号；若省略: 模型无法跳到定义行
        end_line_number = int(getattr(node, "end_lineno", line_number) or line_number)  # 新增代码+LSP工具: 读取符号结束行号；若省略: 长函数范围不清楚
        return {  # 新增代码+LSP工具: 返回标准符号结构；若省略: 调用方无法稳定格式化符号
            "kind": kind,  # 新增代码+LSP工具: 保存符号类型；若省略: 模型无法区分类、方法和函数
            "name": name,  # 新增代码+LSP工具: 保存符号名称；若省略: 定义定位无法按名称匹配
            "line": line_number,  # 新增代码+LSP工具: 保存起始行号；若省略: 输出没有可跳转位置
            "end_line": end_line_number,  # 新增代码+LSP工具: 保存结束行号；若省略: 输出无法描述定义范围
            "container": container,  # 新增代码+LSP工具: 保存所属类名；若省略: 方法会和顶层函数混在一起
        }  # 新增代码+LSP工具: 符号字典结束；若省略: Python 语法结构不完整

    def _lsp_symbol_line(self, symbol: dict[str, Any]) -> str:  # 新增代码+LSP工具: 把符号字典格式化成稳定单行文本；若省略: 输出格式会散落在多个工具里
        kind = str(symbol.get("kind", ""))  # 新增代码+LSP工具: 读取符号类型；若省略: 输出可能缺少 kind 字段
        name = str(symbol.get("name", ""))  # 新增代码+LSP工具: 读取符号名称；若省略: 输出可能缺少 name 字段
        line_number = int(symbol.get("line", 0) or 0)  # 新增代码+LSP工具: 读取符号起始行；若省略: 输出没有可跳转行号
        end_line_number = int(symbol.get("end_line", line_number) or line_number)  # 新增代码+LSP工具: 读取符号结束行；若省略: 输出无法展示定义范围
        container = str(symbol.get("container", "") or "")  # 新增代码+LSP工具: 读取符号容器类名；若省略: 方法归属无法显示
        base_line = f"kind={kind} name={name} line={line_number}"  # 新增代码+LSP工具: 生成符号基础字段；若省略: 模型无法稳定解析符号输出
        if container:  # 新增代码+LSP工具: 如果符号有所属类；若省略: 方法输出会缺少类名
            base_line = f"{base_line} container={container}"  # 新增代码+LSP工具: 追加容器类名且保持 line 后紧跟 container；若省略: 测试和模型难以识别方法归属
        if end_line_number and end_line_number != line_number:  # 新增代码+LSP工具: 只有多行定义才展示结束行；若省略: 单行符号也会产生噪音字段
            base_line = f"{base_line} end_line={end_line_number}"  # 新增代码+LSP工具: 追加结束行号；若省略: 多行定义范围不清楚
        return base_line  # 新增代码+LSP工具: 返回单行符号文本；若省略: 调用方无法输出符号

    def _lsp_syntax_error_failure(self, tool_name: str, error: SyntaxError) -> str:  # 新增代码+LSP工具: 把符号/定义解析失败转成统一错误文本；若省略: 语法错误失败格式会重复且不一致
        line_number = int(error.lineno or 0)  # 新增代码+LSP工具: 读取语法错误行号；若省略: 模型无法定位错误行
        column_number = int(error.offset or 0)  # 新增代码+LSP工具: 读取语法错误列号；若省略: 模型无法定位错误列
        message = str(error.msg or "语法错误")  # 新增代码+LSP工具: 读取语法错误消息；若省略: 用户看不到 Python 解析器原因
        return f"{tool_name} 失败：Python 语法解析失败。line={line_number} column={column_number} message={message}"  # 新增代码+LSP工具: 返回带行列和消息的失败文本；若省略: 模型难以先修语法再重试

    def _lsp_diagnostic_line(self, error: SyntaxError) -> str:  # 新增代码+LSP工具: 把 SyntaxError 转成稳定诊断行；若省略: diagnostics 输出格式会和失败输出混杂
        line_number = int(error.lineno or 0)  # 新增代码+LSP工具: 读取诊断行号；若省略: 模型无法定位错误行
        column_number = int(error.offset or 0)  # 新增代码+LSP工具: 读取诊断列号；若省略: 模型无法定位错误列
        message = str(error.msg or "语法错误")  # 新增代码+LSP工具: 读取诊断消息；若省略: 用户看不到 Python 解析器原因
        return f"severity=error line={line_number} column={column_number} message={message}"  # 新增代码+LSP工具: 返回 LSP 风格诊断字段；若省略: 模型难以判断严重程度和位置

    def _repl(self, arguments: dict[str, Any]) -> str:  # 新增代码+REPL工具: 执行安全白名单内的批量工具编排；若省略: repl schema 暴露后仍没有实际行为
        raw_calls = arguments.get("calls")  # 新增代码+REPL工具: 读取批量子调用数组；若省略: 工具无法知道要执行哪些步骤
        if not isinstance(raw_calls, list) or not raw_calls:  # 新增代码+REPL工具: 校验 calls 必须是非空数组；若省略: 空批次或错误类型会进入执行逻辑
            return "repl 失败：calls 必须是 1 到 5 个子调用对象。"  # 新增代码+REPL工具: 返回清楚的 calls 类型错误；若省略: 模型难以修正参数结构
        if len(raw_calls) > 5:  # 新增代码+REPL工具: 限制单次最多五个子调用；若省略: 批量输出可能撑爆上下文
            return "repl 失败：calls 最多 5 个子调用。"  # 新增代码+REPL工具: 返回数量上限错误；若省略: 模型不知道应该缩小批次
        allowed_tool_names = self._repl_allowed_tool_names()  # 新增代码+REPL工具: 获取安全白名单工具集合；若省略: 无法拦截写入、命令和外部工具
        validated_calls: list[tuple[str, dict[str, Any]]] = []  # 新增代码+REPL工具: 准备保存校验后的子调用；若省略: 后续执行会重复解析原始结构
        for index, raw_call in enumerate(raw_calls, start=1):  # 新增代码+REPL工具: 逐个校验子调用并保留原始顺序；若省略: 无法定位哪一项参数错误
            if not isinstance(raw_call, dict):  # 新增代码+REPL工具: 每个子调用必须是对象；若省略: 字符串或数组会导致 .get 报错
                return f"repl 失败：第 {index} 个调用必须是对象。"  # 新增代码+REPL工具: 返回具体子调用类型错误；若省略: 模型不知道哪一项需要修正
            tool_name = str(raw_call.get("tool_name", "") or "").strip()  # 新增代码+REPL工具: 读取并清理子工具名；若省略: 空白工具名可能进入路由
            if not tool_name:  # 新增代码+REPL工具: 检查子工具名是否为空；若省略: 空工具名会变成未知工具
                return f"repl 失败：第 {index} 个调用缺少非空 tool_name。"  # 新增代码+REPL工具: 返回缺少工具名错误；若省略: 模型难以补齐子调用
            if tool_name not in allowed_tool_names:  # 新增代码+REPL工具: 拦截不在安全白名单内的工具；若省略: repl 可能执行写入、命令、MCP 或递归自身
                return f"repl 失败：第 {index} 个调用的 tool_name 不在安全白名单：{tool_name}"  # 新增代码+REPL工具: 返回白名单错误和具体工具名；若省略: 模型不知道哪个子工具被拒绝
            raw_arguments = raw_call.get("arguments", {})  # 新增代码+REPL工具: 读取子调用参数对象；若省略: 子工具无法收到 path/query 等入参
            if raw_arguments is None:  # 新增代码+REPL工具: 允许模型用 null 表示空参数；若省略: null 会被当成错误对象
                raw_arguments = {}  # 新增代码+REPL工具: 把 null 转成空字典；若省略: 后续 isinstance 校验会失败
            if not isinstance(raw_arguments, dict):  # 新增代码+REPL工具: 子调用参数必须是对象；若省略: 字符串参数会导致工具层混乱
                return f"repl 失败：第 {index} 个调用的 arguments 必须是对象。"  # 新增代码+REPL工具: 返回具体参数类型错误；若省略: 模型难以修正子调用参数
            validated_calls.append((tool_name, raw_arguments))  # 新增代码+REPL工具: 保存安全且结构正确的子调用；若省略: 后续没有可执行批次
        stop_on_error = self._repl_stop_on_error(arguments.get("stop_on_error"))  # 新增代码+REPL工具: 解析失败即停策略；若省略: 子调用失败后的行为不明确
        max_output_chars = self._repl_max_output_chars(arguments.get("max_output_chars"))  # 新增代码+REPL工具: 解析每个子调用输出长度上限；若省略: 长输出可能撑爆上下文
        lines = [  # 新增代码+REPL工具: 准备结构化 REPL 输出；若省略: 批量结果无法稳定阅读
            "repl 成功：已按顺序执行安全白名单内工具批次。",  # 新增代码+REPL工具: 输出成功前缀；若省略: 调用方难以判断 REPL 工具本身是否成功
            f"call_count={len(validated_calls)}",  # 新增代码+REPL工具: 输出子调用数量；若省略: 用户需要手动数结果段
            f"stop_on_error={str(stop_on_error).lower()}",  # 新增代码+REPL工具: 输出失败即停策略；若省略: 后续是否继续执行不透明
            f"max_output_chars={max_output_chars}",  # 新增代码+REPL工具: 输出每段截断上限；若省略: 长输出截断原因不清楚
            "调用结果：",  # 新增代码+REPL工具: 添加结果标题；若省略: 元信息和子调用输出容易混在一起
        ]  # 新增代码+REPL工具: 基础输出列表结束；若省略: 后续追加没有容器
        for index, (tool_name, child_arguments) in enumerate(validated_calls, start=1):  # 新增代码+REPL工具: 按原顺序执行每个子调用；若省略: REPL 不会实际批量执行
            child_output = self._execute_tool(ToolCall(name=tool_name, arguments=child_arguments))  # 新增代码+REPL工具: 复用现有工具路由执行安全子工具；若省略: 会重复实现各工具逻辑
            child_failed = self._repl_child_failed(child_output)  # 新增代码+REPL工具: 判断子调用输出是否表示失败；若省略: stop_on_error 无法生效
            lines.append(f"[{index}] tool_name={tool_name}")  # 新增代码+REPL工具: 输出子调用序号和工具名；若省略: 用户无法按顺序审计结果
            lines.append(f"status={'failed' if child_failed else 'ok'}")  # 新增代码+REPL工具: 输出子调用状态；若省略: 用户需要从正文猜是否失败
            lines.append(self._repl_truncate_output(child_output, max_output_chars))  # 新增代码+REPL工具: 输出并按上限截断子调用结果；若省略: 模型拿不到证据或可能输出过长
            if child_failed and stop_on_error:  # 新增代码+REPL工具: 如果子调用失败且策略要求停止；若省略: 失败后仍会继续执行后续调用
                lines.append(f"repl 已停止：第 {index} 个子调用失败，stop_on_error=true。")  # 新增代码+REPL工具: 明确说明提前停止原因；若省略: 后续结果缺失会显得像输出截断
                break  # 新增代码+REPL工具: 停止执行剩余子调用；若省略: stop_on_error 参数不会生效
        return "\n".join(lines)  # 新增代码+REPL工具: 返回完整批量执行结果；若省略: 工具无法把结果交回模型

    def _repl_allowed_tool_names(self) -> set[str]:  # 新增代码+REPL工具: 定义 REPL 可批量调用的安全工具白名单；若省略: REPL 无法保守限制副作用范围
        return {  # 新增代码+REPL工具: 返回只读、状态和符号类内置工具集合；若省略: 白名单没有实际内容
            "read_file",  # 新增代码+REPL工具: 允许读取工作区文本文件；若省略: REPL 无法批量做基础文件查看
            "todo_read",  # 新增代码+REPL工具: 允许读取任务清单状态；若省略: REPL 无法批量核对任务进度
            "read_background_command",  # 新增代码+REPL工具: 允许读取已启动后台命令状态和增量输出；若省略: REPL 无法批量收集运行状态
            "notebook_read",  # 新增代码+REPL工具: 允许读取 Notebook 摘要；若省略: REPL 无法批量查看 notebook cell
            "tool_search",  # 新增代码+REPL工具: 允许搜索当前可见工具；若省略: REPL 无法批量做工具发现
            "skill_list",  # 新增代码+REPL工具: 允许列出本地 skills；若省略: REPL 无法批量发现说明书
            "skill_load",  # 新增代码+REPL工具: 允许读取本地 skill 说明；若省略: REPL 无法批量加载安全本地规程
            "task_output",  # 新增代码+REPL工具: 允许读取子任务输出；若省略: REPL 无法批量查看子任务状态
            "task_list",  # 新增代码+REPL工具: 允许列出子任务状态；若省略: REPL 无法批量收集任务总览
            "task_get",  # 新增代码+REPL工具: 允许读取单个子任务详情；若省略: REPL 无法批量核对任务元信息
            "list_peers",  # 新增代码+REPL工具: 允许读取教学版 peer 总览；若省略: REPL 无法批量查看 team 状态
            "read_peer_messages",  # 新增代码+REPL工具: 允许读取 peer inbox；若省略: REPL 无法批量收集协作消息
            "lsp_symbols",  # 新增代码+REPL工具: 允许读取 Python 文件符号；若省略: REPL 无法批量做代码结构理解
            "lsp_definition",  # 新增代码+REPL工具: 允许定位 Python 符号定义；若省略: REPL 无法批量做定义跳转
            "lsp_diagnostics",  # 新增代码+REPL工具: 允许读取 Python 语法诊断；若省略: REPL 无法批量收集语法问题
            "cron_list",  # 新增代码+CronMonitor: 允许 REPL 批量读取定时任务记录列表；若省略: 模型无法把 Cron 状态查询纳入安全批量审计
        }  # 新增代码+REPL工具: 白名单集合结束；若省略: Python 语法结构不完整

    def _repl_stop_on_error(self, raw_value: Any) -> bool:  # 新增代码+REPL工具: 解析 REPL 子调用失败后是否停止；若省略: stop_on_error 容错逻辑会散落在主方法里
        if isinstance(raw_value, bool):  # 新增代码+REPL工具: 只有布尔值才尊重模型输入；若省略: 字符串 "false" 会被 bool() 误判为 True
            return raw_value  # 新增代码+REPL工具: 返回明确布尔输入；若省略: 模型无法关闭失败即停
        return True  # 新增代码+REPL工具: 非布尔或省略时默认失败即停；若省略: 默认策略不明确

    def _repl_max_output_chars(self, raw_value: Any) -> int:  # 新增代码+REPL工具: 解析每个子调用最大输出字符数；若省略: 输出截断策略会重复且不稳定
        parsed_value = self._parse_max_chars(raw_value)  # 新增代码+REPL工具: 复用已有字符数解析逻辑；若省略: 字符串和非法值处理会不一致
        return min(parsed_value, 8000)  # 新增代码+REPL工具: REPL 每段最多返回 8000 字符；若省略: 一个批次可能输出过长

    def _repl_truncate_output(self, output: str, max_output_chars: int) -> str:  # 新增代码+REPL工具: 截断单个子调用输出；若省略: 长结果可能撑爆上下文
        if len(output) <= max_output_chars:  # 新增代码+REPL工具: 如果输出没有超过上限；若省略: 所有输出都会被无意义处理
            return output  # 新增代码+REPL工具: 原样返回短输出；若省略: 短输出可能被误截断
        return output[:max_output_chars] + "\n...[repl 子调用输出过长，已截断]..."  # 新增代码+REPL工具: 返回截断结果并标明原因；若省略: 用户可能误以为输出完整

    def _repl_child_failed(self, output: str) -> bool:  # 新增代码+REPL工具: 判断子调用文本是否表示失败；若省略: stop_on_error 无法根据工具结果停下
        first_line = output.splitlines()[0] if output.splitlines() else output  # 新增代码+REPL工具: 取第一行状态文本；若省略: 长输出中间的“失败”可能被误判
        return "失败" in first_line or first_line.startswith("未知工具") or first_line.startswith("用户拒绝")  # 新增代码+REPL工具: 识别常见失败前缀；若省略: 子调用失败后仍可能继续执行后续步骤

    def _cron_create(self, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 创建教学版进程内定时任务记录；若省略: cron_create schema 暴露后仍没有实际行为
        name = str(arguments.get("name", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理定时任务名称；若省略: 列表中无法显示可读名称
        schedule = str(arguments.get("schedule", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理定时说明；若省略: 记录不知道何时复查
        prompt = str(arguments.get("prompt", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理到点任务说明；若省略: 记录没有实际检查内容
        stop_condition = str(arguments.get("stop_condition", "") or "").strip()  # 新增代码+CronMonitor: 读取可选停止条件；若省略: 长期任务缺少收束边界
        if not name:  # 新增代码+CronMonitor: 校验名称不能为空；若省略: 用户难以区分多个无名定时任务
            return "cron_create 失败：缺少非空 name 参数。"  # 新增代码+CronMonitor: 返回清楚的名称缺失错误；若省略: 模型难以修正参数
        if not schedule:  # 新增代码+CronMonitor: 校验定时说明不能为空；若省略: 可能登记没有触发时间的定时记录
            return "cron_create 失败：缺少非空 schedule 参数。"  # 新增代码+CronMonitor: 返回清楚的 schedule 缺失错误；若省略: 模型难以修正参数
        if not prompt:  # 新增代码+CronMonitor: 校验任务说明不能为空；若省略: 可能登记没有工作内容的定时记录
            return "cron_create 失败：缺少非空 prompt 参数。"  # 新增代码+CronMonitor: 返回清楚的 prompt 缺失错误；若省略: 模型难以修正参数
        cron_id = f"cron_{secrets.token_hex(6)}"  # 新增代码+CronMonitor: 生成短且唯一的定时任务 id；若省略: cron_list/delete 无法引用具体记录
        created_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+CronMonitor: 记录创建时间；若省略: 用户无法判断记录登记顺序
        record = CronRecord(cron_id=cron_id, name=name, schedule=schedule, prompt=prompt, stop_condition=stop_condition, state="active", created_at=created_at)  # 新增代码+CronMonitor: 构造进程内定时任务记录；若省略: 后续列表和删除没有数据源
        self.cron_records[cron_id] = record  # 新增代码+CronMonitor: 把记录保存到当前 agent 实例；若省略: 创建后无法被 cron_list 找回
        return "\n".join([  # 新增代码+CronMonitor: 返回结构化创建结果；若省略: 模型拿不到 cron_id 和边界说明
            "cron_create 成功：已登记教学版进程内定时任务记录。",  # 新增代码+CronMonitor: 输出成功前缀；若省略: 调用方难以判断工具是否成功
            f"cron_id={cron_id}",  # 新增代码+CronMonitor: 输出定时任务 id；若省略: 后续 cron_list/delete 难以引用
            "state=active",  # 新增代码+CronMonitor: 输出当前记录状态；若省略: 用户不知道记录是否有效
            f"name={name}",  # 新增代码+CronMonitor: 输出任务名称；若省略: 用户需要从 prompt 猜记录含义
            f"schedule={schedule}",  # 新增代码+CronMonitor: 输出触发时间说明；若省略: 用户无法审计计划何时复查
            f"prompt={prompt}",  # 新增代码+CronMonitor: 输出任务内容；若省略: 用户不知道到点要做什么
            f"stop_condition={stop_condition or '(未设置)'}",  # 新增代码+CronMonitor: 输出停止条件或占位；若省略: 收束边界不透明
            "边界：不执行真实定时任务，不创建系统定时器，不跨进程常驻，不发送通知。",  # 新增代码+CronMonitor: 明确教学版边界；若省略: 模型可能误以为真实调度已经启动
        ])  # 新增代码+CronMonitor: 创建结果拼接结束；若省略: Python 语法结构不完整

    def _cron_list(self, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 列出教学版进程内定时任务记录；若省略: 模型无法查看已登记 Cron 记录
        state = self._cron_monitor_state(arguments.get("state"))  # 新增代码+CronMonitor: 解析 active/deleted/all 筛选状态；若省略: 列表筛选逻辑会散落在方法里
        max_results = self._cron_monitor_max_results(arguments.get("max_results"))  # 新增代码+CronMonitor: 解析最大返回记录数；若省略: 大量记录可能撑爆上下文
        records = [record for record in self.cron_records.values() if state == "all" or record.state == state]  # 新增代码+CronMonitor: 按状态筛选定时记录；若省略: 删除记录和有效记录会混在一起
        limited_records = records[:max_results]  # 新增代码+CronMonitor: 按 max_results 截断输出记录；若省略: 长列表可能占用过多上下文
        lines = [  # 新增代码+CronMonitor: 准备结构化列表输出；若省略: 列表结果无法稳定阅读
            "cron_list 成功：已读取教学版进程内定时任务记录。",  # 新增代码+CronMonitor: 输出成功前缀；若省略: 调用方难以判断工具是否成功
            f"state_filter={state}",  # 新增代码+CronMonitor: 输出筛选状态；若省略: 用户不知道列表是否过滤过
            f"record_count={len(limited_records)}",  # 新增代码+CronMonitor: 输出本次返回数量；若省略: 用户需要手动数记录
            f"total_matching={len(records)}",  # 新增代码+CronMonitor: 输出匹配总数；若省略: 用户不知道是否被 max_results 截断
            "记录：",  # 新增代码+CronMonitor: 添加记录标题；若省略: 元信息和列表项容易混在一起
        ]  # 新增代码+CronMonitor: 列表输出基础行结束；若省略: 后续追加没有容器
        if not limited_records:  # 新增代码+CronMonitor: 如果没有匹配记录；若省略: 空列表会只显示标题而不清楚
            lines.append("(无记录)")  # 新增代码+CronMonitor: 明确说明没有记录；若省略: 用户可能误以为输出被截断
        for record in limited_records:  # 新增代码+CronMonitor: 逐条格式化定时任务记录；若省略: 列表不会显示具体内容
            lines.append(self._format_cron_record(record))  # 新增代码+CronMonitor: 使用统一格式输出记录；若省略: 多处输出格式容易不一致
        return "\n".join(lines)  # 新增代码+CronMonitor: 返回完整列表文本；若省略: 工具无法把结果交回模型

    def _cron_delete(self, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 删除教学版进程内定时任务记录；若省略: cron_delete schema 暴露后仍没有实际行为
        cron_id = str(arguments.get("cron_id", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理目标 cron_id；若省略: 工具不知道要删除哪条记录
        if not cron_id:  # 新增代码+CronMonitor: 校验 cron_id 是否为空；若省略: 空删除请求会进入记录查询
            return "cron_delete 失败：缺少非空 cron_id 参数。"  # 新增代码+CronMonitor: 返回清楚的缺参错误；若省略: 模型难以修正删除调用
        if arguments.get("confirm_delete") is not True:  # 新增代码+CronMonitor: 要求显式确认删除；若省略: 模型可能误删定时记录
            return "cron_delete 失败：删除定时任务记录需要 confirm_delete=true。"  # 新增代码+CronMonitor: 返回确认要求；若省略: 模型不知道如何安全重试
        record = self.cron_records.get(cron_id)  # 新增代码+CronMonitor: 查找目标定时记录；若省略: 无法判断 id 是否存在
        if record is None:  # 新增代码+CronMonitor: 如果没有找到记录；若省略: 后续访问 None 会崩溃
            return f"cron_delete 失败：没有找到 cron_id={cron_id} 的定时任务记录。"  # 新增代码+CronMonitor: 返回清楚的不存在错误；若省略: 用户不知道删除失败原因
        record.state = "deleted"  # 新增代码+CronMonitor: 标记记录已删除而不是创建系统副作用；若省略: cron_list active 仍会显示该记录
        record.deleted_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+CronMonitor: 保存删除时间用于审计；若省略: 用户无法知道记录何时被回收
        return "\n".join([  # 新增代码+CronMonitor: 返回结构化删除结果；若省略: 模型拿不到删除确认
            "cron_delete 成功：已删除教学版进程内定时任务记录。",  # 新增代码+CronMonitor: 输出成功前缀；若省略: 调用方难以判断删除是否成功
            f"cron_id={cron_id}",  # 新增代码+CronMonitor: 输出被删除记录 id；若省略: 用户无法核对目标
            "state=deleted",  # 新增代码+CronMonitor: 输出删除后状态；若省略: 用户不知道记录是否仍 active
            "边界：本工具只删除进程内记录；此前也没有创建过系统定时器。",  # 新增代码+CronMonitor: 明确删除边界；若省略: 用户可能误以为系统任务也被处理
        ])  # 新增代码+CronMonitor: 删除结果拼接结束；若省略: Python 语法结构不完整

    def _monitor(self, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 管理教学版进程内监控记录；若省略: monitor schema 暴露后仍没有实际行为
        action = str(arguments.get("action", "") or "").strip().lower()  # 新增代码+CronMonitor: 读取并清理 monitor 动作；若省略: 多动作工具无法判断执行分支
        if action == "create":  # 新增代码+CronMonitor: 如果请求创建监控记录；若省略: create 动作无法执行
            return self._monitor_create(arguments)  # 新增代码+CronMonitor: 调用监控创建分支；若省略: 创建逻辑会混在主分发里
        if action == "list":  # 新增代码+CronMonitor: 如果请求列出监控记录；若省略: list 动作无法执行
            return self._monitor_list(arguments)  # 新增代码+CronMonitor: 调用监控列表分支；若省略: 列表逻辑会混在主分发里
        if action == "delete":  # 新增代码+CronMonitor: 如果请求删除监控记录；若省略: delete 动作无法执行
            return self._monitor_delete(arguments)  # 新增代码+CronMonitor: 调用监控删除分支；若省略: 删除逻辑会混在主分发里
        if action == "record_result":  # 新增代码+CronMonitor: 如果请求记录最近观察结果；若省略: 监控无法保存检查证据
            return self._monitor_record_result(arguments)  # 新增代码+CronMonitor: 调用结果记录分支；若省略: 结果更新逻辑会混在主分发里
        return "monitor 失败：action 必须是 create、list、delete 或 record_result。"  # 新增代码+CronMonitor: 返回动作非法错误；若省略: 模型难以修正 action 参数

    def _monitor_create(self, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 创建教学版进程内监控记录；若省略: monitor create 动作没有实际行为
        name = str(arguments.get("name", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理监控名称；若省略: 多个监控记录难以区分
        target = str(arguments.get("target", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理监控目标；若省略: 记录不知道观察什么
        condition = str(arguments.get("condition", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理触发条件；若省略: 记录不知道什么情况算命中
        check_interval = str(arguments.get("check_interval", "") or "").strip() or "manual"  # 新增代码+CronMonitor: 读取检查频率并默认 manual；若省略: 监控节奏不清楚
        stop_condition = str(arguments.get("stop_condition", "") or "").strip()  # 新增代码+CronMonitor: 读取可选停止条件；若省略: 监控缺少收束边界
        if not name:  # 新增代码+CronMonitor: 校验名称不能为空；若省略: 用户难以区分无名监控记录
            return "monitor 失败：action=create 时缺少非空 name 参数。"  # 新增代码+CronMonitor: 返回名称缺失错误；若省略: 模型难以修正参数
        if not target:  # 新增代码+CronMonitor: 校验监控目标不能为空；若省略: 可能创建不知道观察对象的记录
            return "monitor 失败：action=create 时缺少非空 target 参数。"  # 新增代码+CronMonitor: 返回目标缺失错误；若省略: 模型难以修正参数
        if not condition:  # 新增代码+CronMonitor: 校验触发条件不能为空；若省略: 可能创建没有判断标准的监控记录
            return "monitor 失败：action=create 时缺少非空 condition 参数。"  # 新增代码+CronMonitor: 返回条件缺失错误；若省略: 模型难以修正参数
        monitor_id = f"mon_{secrets.token_hex(6)}"  # 新增代码+CronMonitor: 生成短且唯一的监控 id；若省略: 后续动作无法引用具体记录
        created_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+CronMonitor: 记录创建时间；若省略: 用户无法判断监控登记顺序
        record = MonitorRecord(monitor_id=monitor_id, name=name, target=target, condition=condition, check_interval=check_interval, stop_condition=stop_condition, state="active", created_at=created_at)  # 新增代码+CronMonitor: 构造进程内监控记录；若省略: 后续列表和结果记录没有数据源
        self.monitor_records[monitor_id] = record  # 新增代码+CronMonitor: 保存监控记录到当前 agent 实例；若省略: 创建后无法被 monitor list 找回
        return "\n".join([  # 新增代码+CronMonitor: 返回结构化创建结果；若省略: 模型拿不到 monitor_id 和边界说明
            "monitor 成功：action=create",  # 新增代码+CronMonitor: 输出成功前缀和动作；若省略: 调用方难以判断动作是否成功
            f"monitor_id={monitor_id}",  # 新增代码+CronMonitor: 输出监控 id；若省略: 后续 record_result/delete 难以引用
            "state=active",  # 新增代码+CronMonitor: 输出当前状态；若省略: 用户不知道记录是否有效
            f"name={name}",  # 新增代码+CronMonitor: 输出监控名称；若省略: 用户需要从目标猜含义
            f"target={target}",  # 新增代码+CronMonitor: 输出观察目标；若省略: 用户无法审计监控对象
            f"condition={condition}",  # 新增代码+CronMonitor: 输出触发条件；若省略: 用户无法审计命中标准
            f"check_interval={check_interval}",  # 新增代码+CronMonitor: 输出检查频率说明；若省略: 用户不知道复查节奏
            f"stop_condition={stop_condition or '(未设置)'}",  # 新增代码+CronMonitor: 输出停止条件或占位；若省略: 收束边界不透明
            "边界：不启动真实监控，不自动检查，不常驻后台，不发送通知。",  # 新增代码+CronMonitor: 明确教学版边界；若省略: 模型可能误以为真实监控已经运行
        ])  # 新增代码+CronMonitor: 创建结果拼接结束；若省略: Python 语法结构不完整

    def _monitor_list(self, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 列出教学版进程内监控记录；若省略: monitor list 动作没有实际行为
        state = self._cron_monitor_state(arguments.get("state"))  # 新增代码+CronMonitor: 解析 active/deleted/all 筛选状态；若省略: 列表筛选逻辑会重复
        max_results = self._cron_monitor_max_results(arguments.get("max_results"))  # 新增代码+CronMonitor: 解析最大返回记录数；若省略: 大量记录可能撑爆上下文
        records = [record for record in self.monitor_records.values() if state == "all" or record.state == state]  # 新增代码+CronMonitor: 按状态筛选监控记录；若省略: 删除记录和有效记录会混在一起
        limited_records = records[:max_results]  # 新增代码+CronMonitor: 按 max_results 截断输出记录；若省略: 长列表可能占用过多上下文
        lines = [  # 新增代码+CronMonitor: 准备结构化列表输出；若省略: monitor list 结果无法稳定阅读
            "monitor 成功：action=list",  # 新增代码+CronMonitor: 输出成功前缀和动作；若省略: 调用方难以判断动作是否成功
            f"state_filter={state}",  # 新增代码+CronMonitor: 输出筛选状态；若省略: 用户不知道列表是否过滤过
            f"record_count={len(limited_records)}",  # 新增代码+CronMonitor: 输出本次返回数量；若省略: 用户需要手动数记录
            f"total_matching={len(records)}",  # 新增代码+CronMonitor: 输出匹配总数；若省略: 用户不知道是否被 max_results 截断
            "记录：",  # 新增代码+CronMonitor: 添加记录标题；若省略: 元信息和列表项容易混在一起
        ]  # 新增代码+CronMonitor: 列表输出基础行结束；若省略: 后续追加没有容器
        if not limited_records:  # 新增代码+CronMonitor: 如果没有匹配记录；若省略: 空列表会只显示标题而不清楚
            lines.append("(无记录)")  # 新增代码+CronMonitor: 明确说明没有记录；若省略: 用户可能误以为输出被截断
        for record in limited_records:  # 新增代码+CronMonitor: 逐条格式化监控记录；若省略: 列表不会显示具体内容
            lines.append(self._format_monitor_record(record))  # 新增代码+CronMonitor: 使用统一格式输出记录；若省略: 多处输出格式容易不一致
        return "\n".join(lines)  # 新增代码+CronMonitor: 返回完整列表文本；若省略: 工具无法把结果交回模型

    def _monitor_delete(self, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 删除教学版进程内监控记录；若省略: monitor delete 动作没有实际行为
        monitor_id = str(arguments.get("monitor_id", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理目标 monitor_id；若省略: 工具不知道要删除哪条记录
        if not monitor_id:  # 新增代码+CronMonitor: 校验 monitor_id 是否为空；若省略: 空删除请求会进入记录查询
            return "monitor 失败：action=delete 时缺少非空 monitor_id 参数。"  # 新增代码+CronMonitor: 返回清楚的缺参错误；若省略: 模型难以修正删除调用
        if arguments.get("confirm_delete") is not True:  # 新增代码+CronMonitor: 要求显式确认删除；若省略: 模型可能误删监控记录
            return "monitor 失败：删除监控记录需要 confirm_delete=true。"  # 新增代码+CronMonitor: 返回确认要求；若省略: 模型不知道如何安全重试
        record = self.monitor_records.get(monitor_id)  # 新增代码+CronMonitor: 查找目标监控记录；若省略: 无法判断 id 是否存在
        if record is None:  # 新增代码+CronMonitor: 如果没有找到记录；若省略: 后续访问 None 会崩溃
            return f"monitor 失败：没有找到 monitor_id={monitor_id} 的监控记录。"  # 新增代码+CronMonitor: 返回清楚的不存在错误；若省略: 用户不知道删除失败原因
        record.state = "deleted"  # 新增代码+CronMonitor: 标记记录已删除而不触发外部副作用；若省略: monitor list active 仍会显示该记录
        record.deleted_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+CronMonitor: 保存删除时间用于审计；若省略: 用户无法知道记录何时被回收
        return "\n".join([  # 新增代码+CronMonitor: 返回结构化删除结果；若省略: 模型拿不到删除确认
            "monitor 成功：action=delete",  # 新增代码+CronMonitor: 输出成功前缀和动作；若省略: 调用方难以判断删除是否成功
            f"monitor_id={monitor_id}",  # 新增代码+CronMonitor: 输出被删除监控 id；若省略: 用户无法核对目标
            "state=deleted",  # 新增代码+CronMonitor: 输出删除后状态；若省略: 用户不知道记录是否仍 active
            "边界：本工具只删除进程内记录；此前也没有启动过真实监控服务。",  # 新增代码+CronMonitor: 明确删除边界；若省略: 用户可能误以为系统监控也被处理
        ])  # 新增代码+CronMonitor: 删除结果拼接结束；若省略: Python 语法结构不完整

    def _monitor_record_result(self, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 给监控记录写入最近一次观察结果；若省略: monitor 无法保存检查证据
        monitor_id = str(arguments.get("monitor_id", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理目标 monitor_id；若省略: 工具不知道更新哪条记录
        result = str(arguments.get("result", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理观察结果文本；若省略: 监控记录没有证据内容
        result_status = self._monitor_result_status(arguments.get("result_status"))  # 新增代码+CronMonitor: 解析最近观察状态；若省略: 状态标准化逻辑会散落在方法里
        if not monitor_id:  # 新增代码+CronMonitor: 校验 monitor_id 是否为空；若省略: 空更新请求会进入记录查询
            return "monitor 失败：action=record_result 时缺少非空 monitor_id 参数。"  # 新增代码+CronMonitor: 返回清楚的缺参错误；若省略: 模型难以修正调用
        if not result:  # 新增代码+CronMonitor: 校验观察结果不能为空；若省略: 可能写入没有证据的监控结果
            return "monitor 失败：action=record_result 时缺少非空 result 参数。"  # 新增代码+CronMonitor: 返回清楚的 result 缺失错误；若省略: 模型难以补充证据
        record = self.monitor_records.get(monitor_id)  # 新增代码+CronMonitor: 查找目标监控记录；若省略: 无法判断 id 是否存在
        if record is None:  # 新增代码+CronMonitor: 如果没有找到记录；若省略: 后续访问 None 会崩溃
            return f"monitor 失败：没有找到 monitor_id={monitor_id} 的监控记录。"  # 新增代码+CronMonitor: 返回清楚的不存在错误；若省略: 用户不知道更新失败原因
        if record.state != "active":  # 新增代码+CronMonitor: 已删除记录不能继续更新结果；若省略: 删除后的监控仍会被误用
            return f"monitor 失败：monitor_id={monitor_id} 当前 state={record.state}，不能记录新结果。"  # 新增代码+CronMonitor: 返回状态不允许错误；若省略: 模型不知道为什么更新被拒绝
        record.last_result = result  # 新增代码+CronMonitor: 保存最近观察结果正文；若省略: monitor list 无法展示最新证据
        record.last_status = result_status  # 新增代码+CronMonitor: 保存最近观察状态；若省略: 用户无法快速判断是否触发条件
        record.last_checked_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+CronMonitor: 保存最近检查时间；若省略: 用户无法判断结果是否新鲜
        return "\n".join([  # 新增代码+CronMonitor: 返回结构化结果记录输出；若省略: 模型拿不到更新后的状态
            "monitor 成功：action=record_result",  # 新增代码+CronMonitor: 输出成功前缀和动作；若省略: 调用方难以判断更新是否成功
            f"monitor_id={monitor_id}",  # 新增代码+CronMonitor: 输出被更新监控 id；若省略: 用户无法核对目标
            f"last_status={record.last_status}",  # 新增代码+CronMonitor: 输出最近状态；若省略: 用户无法快速判断监控是否命中
            f"last_checked_at={record.last_checked_at}",  # 新增代码+CronMonitor: 输出检查时间；若省略: 结果新鲜度不透明
            f"last_result={record.last_result}",  # 新增代码+CronMonitor: 输出最近结果正文；若省略: 监控结果缺少证据
        ])  # 新增代码+CronMonitor: 结果记录输出拼接结束；若省略: Python 语法结构不完整

    def _cron_monitor_state(self, raw_value: Any) -> str:  # 新增代码+CronMonitor: 解析 Cron/Monitor 列表筛选状态；若省略: active/deleted/all 处理会重复
        return cron_monitor_state(raw_value)  # 修改代码+TasksSplit: 委托 tasks.cron_monitor 解析筛选状态；若没有这行代码，Cron/Monitor 状态规则仍会留在主文件。

    def _cron_monitor_max_results(self, raw_value: Any) -> int:  # 新增代码+CronMonitor: 解析 Cron/Monitor 列表最大返回数；若省略: 输出长度控制会重复
        return cron_monitor_max_results(raw_value)  # 修改代码+TasksSplit: 委托 tasks.cron_monitor 解析最大返回数；若没有这行代码，列表长度规则无法复用。

    def _monitor_result_status(self, raw_value: Any) -> str:  # 新增代码+CronMonitor: 解析 monitor 最近观察状态；若省略: 状态标准化会散落在结果记录逻辑里
        return monitor_result_status(raw_value)  # 修改代码+TasksSplit: 委托 tasks.cron_monitor 解析 monitor 结果状态；若没有这行代码，监控状态标准化无法独立测试。

    def _format_cron_record(self, record: CronRecord) -> str:  # 新增代码+CronMonitor: 把定时任务记录格式化成稳定多字段文本；若省略: 创建和列表输出格式容易不一致
        return format_cron_record(record)  # 修改代码+TasksSplit: 委托 tasks.cron_monitor 格式化定时记录；若没有这行代码，cron 输出格式仍只能从主文件复用。

    def _format_monitor_record(self, record: MonitorRecord) -> str:  # 新增代码+CronMonitor: 把监控记录格式化成稳定多字段文本；若省略: 列表输出格式容易不一致
        return format_monitor_record(record)  # 修改代码+TasksSplit: 委托 tasks.cron_monitor 格式化监控记录；若没有这行代码，monitor 输出格式仍只能从主文件复用。

    def _enter_plan_mode(self, arguments: dict[str, Any]) -> str:  # 新增代码+PlanMode: 执行进入计划模式工具并保存上下文；若省略: agent 只有工具 schema 没有实际状态切换
        reason = str(arguments.get("reason", "") or "").strip()  # 新增代码+PlanMode: 读取并清理进入计划模式原因；若省略: 用户看不到模型为什么需要先计划
        goal = str(arguments.get("goal", "") or "").strip()  # 新增代码+PlanMode: 读取并清理计划目标；若省略: 后续计划缺少明确目标
        if not reason:  # 新增代码+PlanMode: 检查 reason 是否为空；若省略: 模型可能用空原因进入计划模式
            return "enter_plan_mode 失败：缺少非空 reason 参数。"  # 新增代码+PlanMode: 返回清楚缺参错误；若省略: 模型难以修正进入计划模式参数
        if not goal:  # 新增代码+PlanMode: 检查 goal 是否为空；若省略: 模型可能在没有目标时进入计划模式
            return "enter_plan_mode 失败：缺少非空 goal 参数。"  # 新增代码+PlanMode: 返回清楚缺参错误；若省略: 模型难以修正进入计划模式参数
        steps = self._plan_mode_steps(arguments.get("steps"))  # 修改代码+Stage14硬清理: 恢复进入计划模式时的初步步骤解析；若没有这行代码，后续状态写入会引用未定义变量
        self.plan_mode_state = {"active": True, "reason": reason, "goal": goal, "steps": steps}  # 新增代码+PlanMode: 保存当前计划模式状态；若省略: exit_plan_mode 无法确认已进入计划模式
        lines = ["enter_plan_mode 成功：已进入计划模式。", f"原因：{reason}", f"目标：{goal}"]  # 新增代码+PlanMode: 准备返回给模型和用户看的状态文本；若省略: 工具结果缺少关键上下文
        if steps:  # 新增代码+PlanMode: 如果模型提供了初步步骤；若省略: 初步步骤无法显示
            lines.append("初步步骤：")  # 新增代码+PlanMode: 添加步骤标题；若省略: 步骤列表语义不清楚
            lines.extend(f"{index}. {step}" for index, step in enumerate(steps, start=1))  # 修改代码+Stage14硬清理: 恢复初步步骤编号输出；若没有这行代码，进入计划模式的步骤会被静默丢掉
        lines.append("请继续分析并形成计划；在调用 exit_plan_mode 输出计划并等待用户确认前，不要执行写入、删除、命令执行或外部副作用工具。")  # 新增代码+PlanMode: 明确计划模式边界；若省略: 模型可能进入计划模式后仍继续执行副作用工具
        return "\n".join(lines)  # 新增代码+PlanMode: 返回完整进入计划模式结果；若省略: 工具无法把状态交回模型

    def _exit_plan_mode(self, arguments: dict[str, Any]) -> str:  # 新增代码+PlanMode: 执行退出计划模式工具并输出待确认计划；若省略: agent 无法结束计划阶段
        if not self.plan_mode_state.get("active"):  # 新增代码+PlanMode: 确认已经先进入计划模式；若省略: 模型可以绕过 enter_plan_mode 直接输出计划
            return "exit_plan_mode 失败：请先调用 enter_plan_mode 进入计划模式，再调用 exit_plan_mode 输出计划。"  # 新增代码+PlanMode: 返回清楚顺序错误；若省略: 模型难以修正调用顺序
        plan = str(arguments.get("plan", "") or "").strip()  # 新增代码+PlanMode: 读取并清理最终计划正文；若省略: 用户看不到要确认的计划
        if not plan:  # 新增代码+PlanMode: 检查 plan 是否为空；若省略: 空计划可能被当作成功
            return "exit_plan_mode 失败：缺少非空 plan 参数。"  # 新增代码+PlanMode: 返回清楚缺参错误；若省略: 模型难以修正退出计划模式参数
        steps = self._plan_mode_steps(arguments.get("steps"))  # 新增代码+PlanMode: 解析可选最终步骤列表；若省略: steps 参数会被忽略
        previous_reason = str(self.plan_mode_state.get("reason", "") or "")  # 新增代码+PlanMode: 读取进入计划模式时保存的原因；若省略: 最终输出缺少前后衔接
        previous_goal = str(self.plan_mode_state.get("goal", "") or "")  # 新增代码+PlanMode: 读取进入计划模式时保存的目标；若省略: 最终输出缺少计划目标
        self.plan_mode_state = {"active": False, "awaiting_confirmation": True, "reason": previous_reason, "goal": previous_goal, "plan": plan, "steps": steps}  # 新增代码+PlanMode: 标记计划模式结束并等待用户确认；若省略: agent 无法记录确认前状态
        lines = ["exit_plan_mode 成功：已输出计划，等待用户确认。", f"原始原因：{previous_reason}", f"计划目标：{previous_goal}", "最终计划：", plan]  # 新增代码+PlanMode: 准备返回最终计划文本；若省略: 用户无法看到计划内容
        if steps:  # 新增代码+PlanMode: 如果模型提供了最终步骤；若省略: 最终步骤无法显示
            lines.append("最终步骤：")  # 新增代码+PlanMode: 添加最终步骤标题；若省略: 步骤列表语义不清楚
            lines.extend(f"{index}. {step}" for index, step in enumerate(steps, start=1))  # 新增代码+PlanMode: 把最终步骤编号输出；若省略: 多步骤计划不易阅读
        lines.append("等待用户确认：用户确认前不要执行写入、删除、命令执行或外部副作用工具。")  # 新增代码+PlanMode: 明确下一步必须等待确认；若省略: 模型可能计划后立刻执行
        return "\n".join(lines)  # 新增代码+PlanMode: 返回完整退出计划模式结果；若省略: 工具无法把待确认计划交回模型

    def _verify_plan_execution(self, arguments: dict[str, Any]) -> str:  # 新增代码+PlanVerification: 执行计划验证工具并生成审计摘要；若省略: 工具 schema 存在但没有实际行为
        plan = str(arguments.get("plan", "") or "").strip()  # 新增代码+PlanVerification: 读取并清理显式传入的计划正文；若省略: 用户传入的验证对象会被忽略
        if not plan:  # 新增代码+PlanVerification: 如果调用方没有显式传 plan；若省略: 无法回退到最近 exit_plan_mode 保存的计划
            plan = str(self.plan_mode_state.get("plan", "") or "").strip()  # 新增代码+PlanVerification: 使用最近保存的计划作为验证对象；若省略: exit_plan_mode 后调用验证仍会缺少计划
        if not plan:  # 新增代码+PlanVerification: 检查是否仍然没有可验证计划；若省略: 空计划可能被当成成功验证
            return "verify_plan_execution 失败：缺少非空 plan 参数，且当前没有 exit_plan_mode 保存的计划。"  # 新增代码+PlanVerification: 返回清楚缺参错误；若省略: 模型难以修正验证参数
        executed_steps = self._plan_verification_items(arguments.get("executed_steps"), "executed_steps")  # 新增代码+PlanVerification: 解析已执行步骤列表；若省略: 工具无法统计实际完成步骤
        if isinstance(executed_steps, str):  # 新增代码+PlanVerification: 检查已执行步骤解析是否失败；若省略: 错误文本会被当作列表继续处理
            return executed_steps  # 新增代码+PlanVerification: 直接返回解析错误给模型；若省略: 模型不知道 executed_steps 参数有问题
        evidence_items = self._plan_verification_items(arguments.get("evidence"), "evidence")  # 新增代码+PlanVerification: 解析验证证据列表；若省略: 工具无法统计验证依据
        if isinstance(evidence_items, str):  # 新增代码+PlanVerification: 检查证据解析是否失败；若省略: 错误文本会被当作列表继续处理
            return evidence_items  # 新增代码+PlanVerification: 直接返回解析错误给模型；若省略: 模型不知道 evidence 参数有问题
        open_items = self._plan_verification_optional_items(arguments.get("open_items"))  # 新增代码+PlanVerification: 解析可选遗漏和风险项；若省略: 未完成事项无法进入验证状态判断
        result_text = str(arguments.get("result", "") or "").strip().lower()  # 新增代码+PlanVerification: 读取模型自评结论并统一成小写；若省略: blocked/failed 等状态无法参与判断
        incomplete_markers = {"incomplete", "blocked", "failed", "missing", "partial"}  # 新增代码+PlanVerification: 定义会强制判为未完成的状态词；若省略: 明确失败结果可能仍被误判为 verified
        status = "incomplete" if open_items or result_text in incomplete_markers else "verified"  # 新增代码+PlanVerification: 根据遗漏项和自评结论计算最终状态；若省略: 用户无法快速区分完成和未完成
        lines = [  # 新增代码+PlanVerification: 准备结构化验证摘要行；若省略: 工具无法输出可审计结果
            "verify_plan_execution 成功：已生成计划执行验证摘要。",  # 新增代码+PlanVerification: 输出成功前缀；若省略: 调用方难以判断工具是否成功执行
            f"status={status}",  # 新增代码+PlanVerification: 输出最终状态；若省略: 用户无法快速判断验证结论
            f"executed_step_count={len(executed_steps)}",  # 新增代码+PlanVerification: 输出已执行步骤数量；若省略: 用户需要逐行数步骤
            f"evidence_count={len(evidence_items)}",  # 新增代码+PlanVerification: 输出证据数量；若省略: 用户无法快速评估证据充分性
            f"open_item_count={len(open_items)}",  # 新增代码+PlanVerification: 输出遗漏项数量；若省略: 用户无法快速判断剩余风险
            "计划：",  # 新增代码+PlanVerification: 添加计划标题；若省略: 计划正文和后续列表容易混在一起
            plan,  # 新增代码+PlanVerification: 输出被验证的计划正文；若省略: 验证摘要缺少对象
            "已执行步骤：",  # 新增代码+PlanVerification: 添加已执行步骤标题；若省略: 步骤列表语义不清楚
        ]  # 新增代码+PlanVerification: 完成基础摘要列表；若省略: 后续追加内容没有容器
        lines.extend(f"{index}. {step}" for index, step in enumerate(executed_steps, start=1))  # 新增代码+PlanVerification: 编号输出每个已执行步骤；若省略: 多步骤审计不易阅读
        lines.append("验证证据：")  # 新增代码+PlanVerification: 添加证据标题；若省略: 证据列表语义不清楚
        lines.extend(f"{index}. {item}" for index, item in enumerate(evidence_items, start=1))  # 新增代码+PlanVerification: 编号输出每条证据；若省略: 用户无法逐条核验证据
        if open_items:  # 新增代码+PlanVerification: 如果存在未完成或风险项；若省略: 无法决定是否输出遗漏详情
            lines.append("未完成/风险项：")  # 新增代码+PlanVerification: 添加遗漏项标题；若省略: 遗漏内容语义不清楚
            lines.extend(f"{index}. {item}" for index, item in enumerate(open_items, start=1))  # 新增代码+PlanVerification: 编号输出每个遗漏或风险项；若省略: 用户不知道具体还缺什么
        else:  # 新增代码+PlanVerification: 如果没有遗漏或风险项；若省略: 用户可能不确定 open_item_count=0 是否代表没有风险
            lines.append("未完成/风险项：(无)")  # 新增代码+PlanVerification: 明确说明没有遗漏项；若省略: 验证摘要缺少关闭语义
        return "\n".join(lines)  # 新增代码+PlanVerification: 返回完整验证摘要；若省略: 工具无法把审计结果交回模型

    def _plan_verification_items(self, raw_items: Any, field_name: str) -> list[str] | str:  # 新增代码+PlanVerification: 解析必填验证数组字段；若省略: executed_steps/evidence 校验逻辑会重复且易错
        if not isinstance(raw_items, list):  # 新增代码+PlanVerification: 必填字段必须是数组；若省略: 字符串可能被误当成多个字符步骤
            return f"verify_plan_execution 失败：{field_name} 必须是非空字符串数组。"  # 新增代码+PlanVerification: 返回字段类型错误；若省略: 模型不知道该字段需要数组
        items = [str(item).strip() for item in raw_items if item is not None and str(item).strip()]  # 新增代码+PlanVerification: 清理数组项并丢弃空项；若省略: 空白证据或步骤会污染审计结果
        if not items:  # 新增代码+PlanVerification: 检查清理后是否还有有效项；若省略: 空数组也可能通过验证
            return f"verify_plan_execution 失败：{field_name} 必须至少包含一项。"  # 新增代码+PlanVerification: 返回字段为空错误；若省略: 模型难以补足必填验证内容
        return items  # 新增代码+PlanVerification: 返回清理后的有效数组；若省略: 调用方拿不到可输出的步骤或证据

    def _plan_verification_optional_items(self, raw_items: Any) -> list[str]:  # 新增代码+PlanVerification: 解析可选遗漏项数组；若省略: open_items 容错逻辑会散落在主方法里
        if not isinstance(raw_items, list):  # 新增代码+PlanVerification: 非数组遗漏项按未提供处理；若省略: None 或字符串会导致后续遍历语义混乱
            return []  # 新增代码+PlanVerification: 可选字段缺失时返回空列表；若省略: 调用方需要额外处理 None
        return [str(item).strip() for item in raw_items if item is not None and str(item).strip()]  # 新增代码+PlanVerification: 清理遗漏项并丢弃空项；若省略: 空白风险会污染输出

    def _plan_mode_steps(self, raw_steps: Any) -> list[str]:  # 新增代码+PlanMode: 把模型传入的 steps 统一清理成字符串列表；若省略: enter/exit 两个工具会重复解析逻辑
        if raw_steps is None:  # 新增代码+PlanMode: 允许模型省略 steps；若省略: None 会被当成不可迭代对象
            return []  # 新增代码+PlanMode: 省略 steps 时返回空列表；若省略: 调用方需要额外判断 None
        if not isinstance(raw_steps, list):  # 新增代码+PlanMode: 只接受数组形式的步骤；若省略: 字符串会被逐字符拆开
            return []  # 新增代码+PlanMode: 非数组步骤按空列表处理；若省略: 错误类型可能污染计划输出
        return [str(step).strip() for step in raw_steps if str(step).strip()]  # 新增代码+PlanMode: 清理每个步骤并丢弃空步骤；若省略: 输出里可能出现空白或非字符串步骤

    def _skill_list(self, arguments: dict[str, Any]) -> str:  # 新增代码+SkillLoad: 执行内置 skill_list 工具；若省略: 模型无法发现本地 skills
        query = str(arguments.get("query", "") or "").strip()  # 新增代码+SkillLoad: 读取可选搜索关键词；若省略: 模型无法按能力筛选 skills
        max_results = self._tool_search_max_results(arguments.get("max_results"))  # 新增代码+SkillLoad: 解析最大结果数并限制范围；若省略: skill 很多时可能撑爆上下文
        skills = self._discover_skills()  # 新增代码+SkillLoad: 扫描工作区本地 skills；若省略: 列表工具没有数据来源
        if query:  # 新增代码+SkillLoad: 如果模型提供了搜索关键词；若省略: 搜索和全量列表无法区分
            terms = self._tool_search_terms(query)  # 新增代码+SkillLoad: 复用工具搜索拆词逻辑；若省略: 多词和大小写匹配会不稳定
            scored_skills: list[tuple[int, dict[str, Any]]] = []  # 新增代码+SkillLoad: 准备保存匹配分数和 skill；若省略: 无法排序筛选结果
            for skill in skills:  # 新增代码+SkillLoad: 遍历每个本地 skill；若省略: query 不会匹配任何 skill
                score = self._tool_search_score(terms, str(skill["name"]), str(skill["description"]), [str(skill["relative_path"])])  # 新增代码+SkillLoad: 按名称、说明和路径计算相关度；若省略: 搜索结果无法排序或过滤
                if score > 0:  # 新增代码+SkillLoad: 只保留有命中的 skill；若省略: 搜索会返回无关说明书
                    scored_skills.append((score, skill))  # 新增代码+SkillLoad: 保存命中的 skill；若省略: 命中结果不会进入输出
            scored_skills.sort(key=lambda item: (-item[0], str(item[1]["name"])))  # 新增代码+SkillLoad: 按分数降序和名称升序排序；若省略: 结果顺序不稳定且不够相关
            visible_skills = [skill for _, skill in scored_skills[:max_results]]  # 新增代码+SkillLoad: 截取最多 max_results 条搜索结果；若省略: 大量结果可能撑爆上下文
            total_count = len(scored_skills)  # 新增代码+SkillLoad: 记录命中总数用于标题展示；若省略: 模型不知道是否发生截断
        else:  # 新增代码+SkillLoad: 如果没有 query 就列出全部 skills；若省略: 空 query 可能得到空结果
            visible_skills = skills[:max_results]  # 新增代码+SkillLoad: 截取最多 max_results 条全量结果；若省略: skill 很多时可能撑爆上下文
            total_count = len(skills)  # 新增代码+SkillLoad: 记录 skill 总数用于标题展示；若省略: 模型不知道本地共有多少 skill
        if not visible_skills:  # 新增代码+SkillLoad: 处理没有 skill 或没有命中的情况；若省略: 空结果会返回只有标题的模糊文本
            return "skill_list 成功：没有找到匹配的本地 skills。"  # 新增代码+SkillLoad: 明确告诉模型列表为空；若省略: 模型可能误以为工具失败
        lines = [f"skill_list 成功：找到 {total_count} 个 skill，显示前 {len(visible_skills)} 个。"]  # 新增代码+SkillLoad: 构造结果标题；若省略: 模型不知道结果数量和截断情况
        for index, skill in enumerate(visible_skills, start=1):  # 新增代码+SkillLoad: 逐条格式化 skill 信息；若省略: skill 元信息无法变成人类和模型可读文本
            lines.append(f"{index}. {skill['name']}")  # 新增代码+SkillLoad: 输出 skill 名称；若省略: 模型不知道 skill_load 要传什么 name
            lines.append(f"   说明：{skill['description'] or '(无说明)'}")  # 新增代码+SkillLoad: 输出 skill 说明；若省略: 模型缺少选择 skill 的语义依据
            lines.append(f"   路径：{skill['relative_path']}")  # 新增代码+SkillLoad: 输出 skill 文件相对路径；若省略: 用户无法定位说明书文件
        return "\n".join(lines)  # 新增代码+SkillLoad: 返回完整 skill 列表文本；若省略: 工具无法把结果交回模型

    def _skill_load(self, arguments: dict[str, Any]) -> str:  # 新增代码+SkillLoad: 执行内置 skill_load 工具；若省略: 模型无法读取本地 skill 说明书
        skill_name = str(arguments.get("name", "") or "").strip()  # 新增代码+SkillLoad: 读取并清理必填 skill 名称；若省略: 工具不知道加载哪个 skill
        if not skill_name:  # 新增代码+SkillLoad: 检查名称是否为空；若省略: 空名称会进入搜索并产生模糊错误
            return "skill_load 失败：缺少 name 参数。"  # 新增代码+SkillLoad: 返回清楚缺参错误；若省略: 模型难以修正工具调用参数
        max_chars = self._parse_max_chars(arguments.get("max_chars"))  # 新增代码+SkillLoad: 解析最大返回字符数；若省略: 大 skill 可能撑爆上下文
        skills = self._discover_skills()  # 新增代码+SkillLoad: 扫描当前本地 skills；若省略: 加载工具没有安全索引
        selected_skill = next((skill for skill in skills if str(skill["name"]).lower() == skill_name.lower()), None)  # 新增代码+SkillLoad: 按 name 大小写不敏感匹配 skill；若省略: 用户大小写差异会导致加载失败
        if selected_skill is None:  # 新增代码+SkillLoad: 如果没有找到指定名称；若省略: 后续会访问 None 并崩溃
            return f"skill_load 失败：没有找到名为 {skill_name!r} 的本地 skill，请先调用 skill_list 查看可用名称。"  # 新增代码+SkillLoad: 返回可恢复建议；若省略: 模型不知道下一步应该列 skills
        skill_path = selected_skill["path"]  # 新增代码+SkillLoad: 取出已经发现的安全 SKILL.md 路径；若省略: 无法读取目标说明书
        try:  # 新增代码+SkillLoad: 捕获读取 SKILL.md 的磁盘异常；若省略: 文件损坏或权限问题会中断整个 agent
            skill_text = skill_path.read_text(encoding="utf-8", errors="replace")  # 新增代码+SkillLoad: 用 UTF-8 读取 skill 内容；若省略: 模型拿不到说明书正文
        except OSError as error:  # 新增代码+SkillLoad: 处理文件读取失败；若省略: 用户会看到底层异常
            return f"skill_load 失败：无法读取 {selected_skill['relative_path']}：{error}"  # 新增代码+SkillLoad: 返回清楚失败原因；若省略: 模型无法解释为什么加载失败
        truncated_text = skill_text[:max_chars]  # 新增代码+SkillLoad: 按 max_chars 截断 skill 正文；若省略: 大 skill 可能撑爆上下文
        if len(skill_text) > max_chars:  # 新增代码+SkillLoad: 检查正文是否被截断；若省略: 模型不知道返回内容是否完整
            truncated_text += "\n...[skill 内容过长，已截断]..."  # 新增代码+SkillLoad: 添加截断提示；若省略: 模型可能误以为加载了完整 skill
        loaded_skill_name = str(selected_skill["name"])  # 新增代码+SkillGateState: 保存已加载 skill 的规范名称；若没有这行代码，后续策略上下文无法知道哪个 skill 已满足
        self.tool_policy_context.loaded_skills.add(loaded_skill_name)  # 新增代码+SkillGateState: 把原始 skill 名加入 ToolPolicy 上下文；若没有这行代码，needs_skill 工具不会因 skill_load 而解锁
        self.tool_policy_context.loaded_skills.add(loaded_skill_name.replace("-", "_"))  # 新增代码+SkillGateState: 同时加入下划线别名以匹配 workflow gate 常用命名；若没有这行代码，real-chrome 与 real_chrome 这类名字可能对不上
        self._record_observation("skill_loaded", {"name": loaded_skill_name, "relative_path": selected_skill["relative_path"]})  # 新增代码+ObservationV1: 记录 skill 已加载事件；若没有这行代码，Phase 6 审计看不到 skill gate 是如何满足的
        return f"skill_load 成功：name={selected_skill['name']}\n路径：{selected_skill['relative_path']}\n说明：{selected_skill['description'] or '(无说明)'}\n内容：\n{truncated_text}"  # 新增代码+SkillLoad: 返回元信息和正文；若省略: 模型无法按 skill 说明继续工作

    def _discover_skills(self) -> list[dict[str, Any]]:  # 新增代码+SkillLoad: 扫描工作区本地 skills 并返回元信息；若省略: skill_list 和 skill_load 会重复扫描逻辑
        skills: list[dict[str, Any]] = []  # 新增代码+SkillLoad: 准备保存扫描到的 skill 元信息；若省略: 无法累积结果
        seen_skill_names: set[str] = set()  # 新增代码+DynamicRuntimeRules: 记录已发现 skill 名称，优先保留工作区自定义 skill；若没有这行代码，包内和工作区同名 skill 会重复出现并让加载目标不稳定
        for skills_root in self._skill_roots():  # 修改代码+DynamicRuntimeRules: 同时扫描工作区 skills 和包内默认 skills；若没有这行代码，runtime 动态化后模型无法发现内置规则包
            if not skills_root.exists():  # 修改代码+DynamicRuntimeRules: 跳过不存在的 skill 根目录；若没有这行代码，空工作区会让 skill_list 失败
                continue  # 修改代码+DynamicRuntimeRules: 继续检查其它根目录；若没有这行代码，包内默认 skills 可能因工作区缺目录而无法扫描
            if not skills_root.is_dir():  # 修改代码+DynamicRuntimeRules: 跳过不是目录的 skill 根路径；若没有这行代码，异常文件路径会进入 glob 并产生误导
                continue  # 修改代码+DynamicRuntimeRules: 忽略坏根路径继续扫描其它来源；若没有这行代码，单个坏路径会阻断所有 skills
            for skill_file in sorted(skills_root.glob("*/SKILL.md")):  # 修改代码+DynamicRuntimeRules: 扫描当前根目录的一层 skill 文件；若没有这行代码，工作区和包内规则都不会被发现
                if not skill_file.is_file():  # 新增代码+SkillLoad: 跳过非文件路径；若省略: 特殊文件系统项可能让读取失败
                    continue  # 新增代码+SkillLoad: 忽略异常项并继续扫描其他 skills；若省略: 单个坏项会阻断列表
                try:  # 新增代码+SkillLoad: 捕获单个 skill 文件读取异常；若省略: 一个坏 skill 会让全部列表失败
                    skill_text = skill_file.read_text(encoding="utf-8", errors="replace")  # 新增代码+SkillLoad: 读取 SKILL.md 内容用于解析 frontmatter；若省略: 无法得到 name/description
                except OSError:  # 新增代码+SkillLoad: 处理读取失败的 skill 文件；若省略: 坏文件会中断扫描
                    continue  # 新增代码+SkillLoad: 跳过坏 skill 并继续其他文件；若省略: 用户一个损坏 skill 会影响所有 skill
                metadata = self._parse_skill_metadata(skill_text)  # 新增代码+SkillLoad: 从 frontmatter 提取 name/description；若省略: 只能使用目录名且缺少说明
                default_name = skill_file.parent.name  # 新增代码+SkillLoad: 用目录名作为默认 skill 名；若省略: 缺 name 的 skill 无法被加载
                skill_name = str(metadata.get("name", "") or default_name).strip()  # 新增代码+SkillLoad: 优先使用 metadata.name 并清理空白；若省略: 名称可能为空或包含多余空格
                if not skill_name:  # 新增代码+SkillLoad: 跳过仍然没有名称的异常 skill；若省略: 空名称会让 skill_load 匹配混乱
                    continue  # 新增代码+SkillLoad: 忽略坏 skill 并继续扫描；若省略: 空名称会进入结果列表
                skill_key = skill_name.lower()  # 新增代码+DynamicRuntimeRules: 用小写名称做去重键；若没有这行代码，大小写不同的同名 skill 会重复出现
                if skill_key in seen_skill_names:  # 新增代码+DynamicRuntimeRules: 如果工作区或更早根目录已经提供同名 skill；若没有这行代码，包内默认 skill 可能覆盖用户自定义 skill
                    continue  # 新增代码+DynamicRuntimeRules: 保留先发现的 skill 并跳过重复项；若没有这行代码，skill_load 的匹配结果会不稳定
                seen_skill_names.add(skill_key)  # 新增代码+DynamicRuntimeRules: 记录该 skill 已被收录；若没有这行代码，后续重复项无法过滤
                description = str(metadata.get("description", "") or "").strip()  # 新增代码+SkillLoad: 读取并清理描述；若省略: 列表缺少说明或显示 None
                skills.append({"name": skill_name, "description": description, "path": skill_file, "relative_path": self._skill_relative_path(skill_file)})  # 新增代码+SkillLoad: 保存完整元信息；若省略: 列表和加载工具拿不到目标数据
        dynamic_prompt_skill = self._dynamic_prompt_skill_metadata()  # 新增代码+PromptFiles: 把 dynamicprompt.md 暴露成可按需加载的伪 skill；若没有这行代码，动态规则文件虽然存在但模型很难用 skill_load 找到
        if dynamic_prompt_skill is not None:  # 新增代码+PromptFiles: 只有动态提示词文件可读时才加入列表；若没有这行代码，缺失文件会在 skill_list 里显示成不可加载入口
            dynamic_prompt_key = str(dynamic_prompt_skill["name"]).lower()  # 新增代码+PromptFiles: 计算伪 skill 的去重键；若没有这行代码，用户自定义同名 skill 无法优先覆盖
            if dynamic_prompt_key not in seen_skill_names:  # 新增代码+PromptFiles: 避免和真实 dynamicprompt skill 重复；若没有这行代码，skill_load 可能命中不稳定
                skills.append(dynamic_prompt_skill)  # 新增代码+PromptFiles: 加入动态提示词伪 skill；若没有这行代码，skill_list 看不到按需运行规则索引
        return skills  # 修改代码+PromptFiles: 返回真实 skills 加 dynamicprompt 入口；若没有这行代码，调用方无法使用本地 skills

    def _dynamic_prompt_skill_metadata(self) -> dict[str, Any] | None:  # 新增代码+PromptFiles: 生成 dynamicprompt.md 的 skill 元信息；若没有这行代码，动态提示词不能复用 skill_load 读取通道
        return dynamic_prompt_skill_metadata(self.dynamic_prompt_path, relative_path=self._skill_relative_path(self.dynamic_prompt_path))  # 修改代码+PromptsSplit: 委托 prompts.dynamic_prompt 生成伪 skill 元信息；若没有这行代码，dynamicprompt 的存在性和目录判断仍留在主文件。

    def _skill_roots(self) -> list[Path]:  # 新增代码+DynamicRuntimeRules: 返回按优先级扫描的 skill 根目录；若没有这行代码，skill_list 只能看工作区而无法加载包内动态规则
        roots: list[Path] = []  # 新增代码+DynamicRuntimeRules: 准备保存去重后的根目录；若没有这行代码，后续无法累积工作区和包内路径
        seen_roots: set[Path] = set()  # 新增代码+DynamicRuntimeRules: 记录已加入的解析路径；若没有这行代码，workspace 正好是 learning_agent 目录时会重复扫描同一 skills
        for candidate in [self.skills_path, Path(__file__).resolve().parents[1] / "skills"]:  # 修改代码+CoreAgentSplit: 工作区 skills 优先，再回退到 learning_agent/skills；若没有这行代码，迁移到 core/agent.py 后会错误查找 core/skills。
            try:  # 新增代码+DynamicRuntimeRules: 规范化路径用于去重；若没有这行代码，符号链接或相对路径可能导致重复扫描
                resolved_candidate = candidate.resolve()  # 新增代码+DynamicRuntimeRules: 解析绝对路径；若没有这行代码，seen_roots 可能无法识别同一目录
            except OSError:  # 新增代码+DynamicRuntimeRules: 防御路径解析失败；若没有这行代码，异常路径会打断 skill 发现
                resolved_candidate = candidate  # 新增代码+DynamicRuntimeRules: 解析失败时使用原路径继续；若没有这行代码，坏路径没有可去重标识
            if resolved_candidate in seen_roots:  # 新增代码+DynamicRuntimeRules: 跳过已经加入的根目录；若没有这行代码，同一路径会重复列出 skills
                continue  # 新增代码+DynamicRuntimeRules: 继续检查下一个候选根；若没有这行代码，重复目录仍会被加入结果
            seen_roots.add(resolved_candidate)  # 新增代码+DynamicRuntimeRules: 标记该根目录已加入；若没有这行代码，后续重复候选无法识别
            roots.append(candidate)  # 新增代码+DynamicRuntimeRules: 保留原始 Path 供 glob 使用；若没有这行代码，调用方拿不到可扫描路径
        return roots  # 新增代码+DynamicRuntimeRules: 返回有序根目录列表；若没有这行代码，_discover_skills 无法遍历 skill 来源

    def _parse_skill_metadata(self, skill_text: str) -> dict[str, str]:  # 新增代码+SkillLoad: 解析 SKILL.md 顶部简单 frontmatter；若省略: skill_list 无法显示 name/description
        lines = skill_text.splitlines()  # 新增代码+SkillLoad: 按行拆分 skill 文本；若省略: 无法定位 frontmatter 边界
        if not lines or lines[0].strip() != "---":  # 新增代码+SkillLoad: 只有第一行是 --- 才按 frontmatter 解析；若省略: 普通 Markdown 可能被误解析
            return {}  # 新增代码+SkillLoad: 没有 frontmatter 时返回空元信息；若省略: 调用方无法使用默认目录名
        metadata: dict[str, str] = {}  # 新增代码+SkillLoad: 准备保存 key/value 元信息；若省略: 无处累积解析结果
        for line in lines[1:]:  # 新增代码+SkillLoad: 从第二行开始读取 frontmatter 内容；若省略: 会把起始 --- 当作字段
            if line.strip() == "---":  # 新增代码+SkillLoad: 遇到结束分隔符停止解析；若省略: 正文里的冒号可能被误当元信息
                break  # 新增代码+SkillLoad: 结束 frontmatter 扫描；若省略: 后续 Markdown 正文会污染 metadata
            if ":" not in line:  # 新增代码+SkillLoad: 跳过没有冒号的行；若省略: 非 key/value 行会解析失败
                continue  # 新增代码+SkillLoad: 继续处理下一行；若省略: 单个非标准行会影响后续字段
            key, value = line.split(":", 1)  # 新增代码+SkillLoad: 按第一个冒号拆分 key 和 value；若省略: description 中的冒号会被错误拆多段
            clean_key = key.strip()  # 新增代码+SkillLoad: 清理字段名空白；若省略: " name" 这类字段无法识别
            clean_value = value.strip().strip("\"'")  # 新增代码+SkillLoad: 清理字段值空白和常见引号；若省略: 输出会包含多余引号
            if clean_key:  # 新增代码+SkillLoad: 只保存非空字段名；若省略: 空 key 会污染 metadata
                metadata[clean_key] = clean_value  # 新增代码+SkillLoad: 保存解析出的元信息；若省略: name/description 不会返回
        return metadata  # 新增代码+SkillLoad: 返回解析结果；若省略: 调用方拿不到 skill 元信息

    def _skill_relative_path(self, skill_file: Path) -> str:  # 新增代码+SkillLoad: 把 skill 文件路径转成工作区相对文本；若省略: 输出会暴露冗长绝对路径
        try:  # 新增代码+SkillLoad: 尝试计算相对路径；若省略: Windows 路径边界异常会直接抛出
            relative_path = skill_file.resolve().relative_to(self.workspace)  # 新增代码+SkillLoad: 计算相对于工作区的路径；若省略: 用户难以定位 skill 文件在项目中的位置
        except ValueError:  # 新增代码+SkillLoad: 防御路径不在工作区内的极端情况；若省略: 异常路径会中断 skill 列表
            return str(skill_file)  # 新增代码+SkillLoad: 兜底返回原始路径文本；若省略: 异常路径没有可展示内容
        return relative_path.as_posix()  # 新增代码+SkillLoad: 使用正斜杠输出相对路径；若省略: Windows 反斜杠会让测试和模型阅读不统一

    def _evidence_event_category(self, event_type: str) -> str:  # 新增代码+PromptArchitectureV1: 把 observation event 映射为 Evidence Ledger 分类；若没有这行代码，证据账本只能显示原始事件而缺少类别帮助理解
        if "tool_result" in event_type or event_type == "mcp_call_progress":  # 新增代码+PromptArchitectureV1: 识别工具结果和 MCP 进度事件；若没有这行代码，工具证据无法归入 tool_result
            return "tool_result"  # 新增代码+PromptArchitectureV1: 返回工具结果分类；若没有这行代码，落盘输出等事件不会有清晰 label
        if "policy" in event_type or "blocked_tool" in event_type:  # 新增代码+PromptArchitectureV1: 识别策略阻断相关事件；若没有这行代码，policy block 证据会混入普通观察
            return "policy_block"  # 新增代码+PromptArchitectureV1: 返回策略阻断分类；若没有这行代码，用户难以区分这是规则阻断而非工具失败
        if "plan" in event_type:  # 新增代码+PromptArchitectureV1: 识别计划模式确认或阻断事件；若没有这行代码，plan mode 证据无法被单独标记
            return "plan_confirmation"  # 新增代码+PromptArchitectureV1: 返回计划确认分类；若没有这行代码，计划解锁依据不够醒目
        if "skill" in event_type:  # 新增代码+PromptArchitectureV1: 识别 skill 加载事件；若没有这行代码，skill gate 证据无法被标记
            return "skill_loaded"  # 新增代码+PromptArchitectureV1: 返回技能加载分类；若没有这行代码，报告看不出 skill_loaded 类事件
        if "model" in event_type:  # 新增代码+PromptArchitectureV1: 识别模型推理或请求事件；若没有这行代码，模型相关证据无法被归类
            return "model_inference"  # 新增代码+PromptArchitectureV1: 返回模型推理分类；若没有这行代码，模型事件只能当普通 observation
        return "observation"  # 新增代码+PromptArchitectureV1: 兜底归类为普通观察；若没有这行代码，未知事件会没有分类

    def _format_evidence_ledger(self, max_events: int = 12) -> list[str]:  # 新增代码+PromptArchitectureV1: 把最近 observation_events 格式化为 Evidence Ledger；若没有这行代码，prompt_surface_report 无法桥接观察事件
        lines: list[str] = ["Evidence Ledger"]  # 新增代码+PromptArchitectureV1: 创建证据账本标题；若没有这行代码，报告里没有明确证据分组
        recent_events = self.observation_events[-max_events:]  # 新增代码+PromptArchitectureV1: 只取最新若干事件避免报告过长；若没有这行代码，长会话可能输出过多历史观察
        if not recent_events:  # 新增代码+PromptArchitectureV1: 处理没有观察事件的情况；若没有这行代码，空证据账本会显得像工具失败
            lines.append("- no observation events recorded yet")  # 新增代码+PromptArchitectureV1: 输出清楚的空状态；若没有这行代码，用户不知道是没有事件还是报告坏了
            return lines  # 新增代码+PromptArchitectureV1: 返回空账本；若没有这行代码，后续循环仍会执行但没有内容
        for event in recent_events:  # 新增代码+PromptArchitectureV1: 遍历最新事件生成账本行；若没有这行代码，观察流无法进入报告
            event_type = str(event.get("kind", event.get("type", event.get("event_type", "observation"))))  # 修改代码+PromptArchitectureV1: 优先读取 _record_observation 写入的 kind 字段；若没有这行代码，tool_result_offloaded 会被误显示成 observation
            category = self._evidence_event_category(event_type)  # 新增代码+PromptArchitectureV1: 计算事件分类；若没有这行代码，证据账本缺少 tool_result/policy_block 等 label
            payload = event.get("payload", {})  # 新增代码+PromptArchitectureV1: 读取事件 payload；若没有这行代码，artifact_path 和 raw_output_chars 等关键证据无法展示
            payload_items = []  # 新增代码+PromptArchitectureV1: 准备保存关键 payload 字段；若没有这行代码，无法控制报告只展示重点
            if isinstance(payload, dict):  # 新增代码+PromptArchitectureV1: 只在 payload 是字典时提取字段；若没有这行代码，异常 payload 形状可能导致报告崩溃
                for key in ("tool_name", "artifact_path", "raw_output_chars", "state", "reason", "name", "relative_path", "call_id"):  # 新增代码+PromptArchitectureV1: 按重要性挑选关键字段；若没有这行代码，证据账本可能漏掉 artifact 路径或输出长度
                    if key in payload:  # 新增代码+PromptArchitectureV1: 只展示实际存在的字段；若没有这行代码，报告会塞入大量空值
                        payload_items.append(f"{key}={payload[key]}")  # 新增代码+PromptArchitectureV1: 格式化单个关键字段；若没有这行代码，payload 细节无法进入账本
            payload_text = "; ".join(payload_items) if payload_items else "payload_keys=" + ",".join(sorted(payload.keys())) if isinstance(payload, dict) else f"payload={payload}"  # 新增代码+PromptArchitectureV1: 生成 payload 摘要兜底；若没有这行代码，未知事件会缺少任何 payload 线索
            lines.append(f"- category={category}; event_type={event_type}; {payload_text}")  # 新增代码+PromptArchitectureV1: 写入证据账本行；若没有这行代码，用户看不到事件类型和关键 payload
        return lines  # 新增代码+PromptArchitectureV1: 返回格式化后的证据账本行；若没有这行代码，调用方无法追加到报告

    def _status_snapshot(self, arguments: dict[str, Any]) -> str:  # 新增代码+StatusTools: 生成统一状态快照工具输出；若没有这行代码，模型无法主动查看 run/task/queue/session 状态。
        from learning_agent.app.status_renderer import render_status_snapshot  # 新增代码+StatusTools: 延迟导入状态渲染器避免启动阶段循环依赖；若没有这行代码，text 格式无法输出。
        from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+StatusTools: 延迟导入统一状态聚合器；若没有这行代码，工具会和 CLI/SDK 状态分叉。
        output_format = str(arguments.get("format", "text")).strip().lower()  # 新增代码+StatusTools: 读取输出格式参数；若没有这行代码，模型无法选择 text 或 json。
        snapshot = build_status_snapshot(self.workspace)  # 新增代码+StatusTools: 从当前工作区读取统一快照；若没有这行代码，工具不知道查看哪个项目。
        if output_format == "json":  # 新增代码+StatusTools: 支持机器可读 JSON；若没有这行代码，外部 agent 难以结构化解析状态。
            return json.dumps(snapshot, ensure_ascii=False, indent=2)  # 新增代码+StatusTools: 返回格式化 JSON；若没有这行代码，json 格式参数不会生效。
        return render_status_snapshot(snapshot)  # 新增代码+StatusTools: 默认返回人类可读状态页；若没有这行代码，用户看不到友好文本。

    def _task_status(self, arguments: dict[str, Any]) -> str:  # 新增代码+StatusTools: 查询持久任务状态；若没有这行代码，模型只能手动调用多个 task 工具。
        from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+StatusTools: 使用统一快照读取任务；若没有这行代码，task_status 会和状态页分叉。
        task_id = str(arguments.get("task_id", "")).strip()  # 新增代码+StatusTools: 读取可选 task_id；若没有这行代码，工具无法过滤单个任务。
        max_results = max(1, min(50, int(arguments.get("max_results", 20))))  # 新增代码+StatusTools: 限制返回任务数量；若没有这行代码，大量任务会撑爆上下文。
        tasks = build_status_snapshot(self.workspace).get("tasks", [])  # 新增代码+StatusTools: 从快照读取任务列表；若没有这行代码，任务状态无数据源。
        filtered_tasks = [task for task in tasks if not task_id or str(task.get("task_id", "")) == task_id]  # 新增代码+StatusTools: 按 task_id 过滤；若没有这行代码，单任务查询仍会返回全部任务。
        visible_tasks = filtered_tasks[:max_results]  # 新增代码+StatusTools: 应用最大数量限制；若没有这行代码，max_results 参数无效。
        if not visible_tasks:  # 新增代码+StatusTools: 处理无匹配任务；若没有这行代码，模型会看到空标题不知原因。
            return "task_status：没有找到匹配任务。"  # 新增代码+StatusTools: 返回清楚空结果；若没有这行代码，调用方难以恢复。
        lines = ["Task Status"]  # 新增代码+StatusTools: 创建任务状态标题；若没有这行代码，输出缺少明确用途。
        for task in visible_tasks:  # 新增代码+StatusTools: 遍历可见任务；若没有这行代码，任务不会输出。
            lines.append(f"- task_id={task.get('task_id', '')} status={task.get('status', '')} kind={task.get('kind', '')} output_path={task.get('output_path', '')} output={(task.get('output', '') or task.get('error', ''))}")  # 新增代码+StatusTools: 输出任务关键字段；若没有这行代码，模型无法判断任务完成或失败。
        return "\n".join(lines)  # 新增代码+StatusTools: 返回任务状态文本；若没有这行代码，工具没有输出。

    def _session_list(self, arguments: dict[str, Any]) -> str:  # 新增代码+StatusTools: 列出最近可恢复 session；若没有这行代码，模型不知道有哪些 session 可 resume。
        limit = max(1, min(50, int(arguments.get("limit", 20))))  # 新增代码+StatusTools: 读取并限制 session 数量；若没有这行代码，大量历史会刷屏。
        sessions = SessionStore(self.workspace / "memory" / "sessions").list_recent_sessions(limit=limit)  # 新增代码+StatusTools: 从 session store 读取最近会话；若没有这行代码，工具没有数据源。
        if not sessions:  # 新增代码+StatusTools: 处理无 session；若没有这行代码，空列表不易理解。
            return "session_list：暂无可恢复 session。"  # 新增代码+StatusTools: 返回空结果说明；若没有这行代码，调用方不知道是没数据还是失败。
        return "Session List\n" + "\n".join(f"- session_id={session_id}" for session_id in sessions)  # 新增代码+StatusTools: 返回 session 列表；若没有这行代码，模型无法复制 session_id。

    def _session_resume(self, arguments: dict[str, Any]) -> str:  # 新增代码+StatusTools: 加载指定 session 的恢复上下文；若没有这行代码，模型无法审计 resume 内容。
        from learning_agent.core.resume_loader import ResumeLoader  # 新增代码+StatusTools: 延迟导入恢复器避免启动阶段循环依赖；若没有这行代码，工具无法读取 resume context。
        session_id = str(arguments.get("session_id", "")).strip()  # 新增代码+StatusTools: 读取 session_id 参数；若没有这行代码，恢复目标不明确。
        if not session_id:  # 新增代码+StatusTools: 校验必填参数；若没有这行代码，空 session 会变成难懂文件错误。
            return "session_resume 失败：缺少 session_id。"  # 新增代码+StatusTools: 返回清楚缺参错误；若没有这行代码，模型不知道如何修正。
        context = ResumeLoader(self.workspace / "memory" / "sessions").load(session_id)  # 新增代码+StatusTools: 读取恢复上下文；若没有这行代码，工具无法返回恢复信息。
        return json.dumps(context.to_dict(), ensure_ascii=False, indent=2)  # 新增代码+StatusTools: 返回结构化恢复上下文；若没有这行代码，边界和一致性信息会丢失。

    def _compact_status(self, arguments: dict[str, Any]) -> str:  # 新增代码+StatusTools: 查看 compact/resume 状态；若没有这行代码，模型无法知道是否发生 compact。
        from learning_agent.core.resume_loader import ResumeLoader  # 新增代码+StatusTools: 延迟导入恢复器；若没有这行代码，compact_status 无法读取边界。
        session_id = str(arguments.get("session_id", "")).strip()  # 新增代码+StatusTools: 读取可选 session_id；若没有这行代码，工具不能查看单个 session。
        store = SessionStore(self.workspace / "memory" / "sessions")  # 新增代码+StatusTools: 打开 session store；若没有这行代码，工具无法列 session。
        session_ids = [session_id] if session_id else store.list_recent_sessions(limit=10)  # 新增代码+StatusTools: 决定要检查哪些 session；若没有这行代码，空参数时没有默认行为。
        loader = ResumeLoader(self.workspace / "memory" / "sessions")  # 新增代码+StatusTools: 创建恢复器；若没有这行代码，边界读取逻辑会重复。
        lines = ["Compact Status"]  # 新增代码+StatusTools: 创建输出标题；若没有这行代码，输出用途不清楚。
        for current_session_id in session_ids:  # 新增代码+StatusTools: 遍历目标 session；若没有这行代码，状态不会输出。
            context = loader.load(current_session_id)  # 新增代码+StatusTools: 加载恢复上下文；若没有这行代码，无法读取 last_boundary。
            boundary = context.last_boundary  # 新增代码+StatusTools: 读取最后 compact 边界；若没有这行代码，后续字段会重复访问。
            if boundary is None:  # 新增代码+StatusTools: 处理未 compact 的 session；若没有这行代码，None 会导致属性错误。
                lines.append(f"- session_id={current_session_id} compacted=false message_count={context.consistency.get('message_count', 0)}")  # 新增代码+StatusTools: 输出未压缩状态；若没有这行代码，用户不知道该 session 没 compact。
            else:  # 新增代码+StatusTools: 处理已经 compact 的 session；若没有这行代码，边界信息不会展示。
                lines.append(f"- session_id={current_session_id} compacted=true boundary_uuid={boundary.boundary_uuid} removed={boundary.removed_message_count} retained={boundary.retained_message_count} reason={boundary.reason}")  # 新增代码+StatusTools: 输出 compact 边界摘要；若没有这行代码，用户无法审计压缩范围。
        return "\n".join(lines)  # 新增代码+StatusTools: 返回 compact 状态文本；若没有这行代码，工具没有输出。

    def _event_tail(self, arguments: dict[str, Any]) -> str:  # 新增代码+StatusTools: 读取状态事件尾巴；若没有这行代码，模型无法增量观察状态生态。
        from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+StatusTools: 延迟导入状态事件 store；若没有这行代码，工具无法读取事件。
        limit = max(1, min(100, int(arguments.get("limit", 20))))  # 新增代码+StatusTools: 限制事件数量；若没有这行代码，长事件流会刷屏。
        since_sequence_raw = arguments.get("since_sequence")  # 新增代码+StatusTools: 读取可选增量起点；若没有这行代码，工具无法做增量查询。
        since_sequence = int(since_sequence_raw) if since_sequence_raw is not None else None  # 新增代码+StatusTools: 规范化增量起点；若没有这行代码，字符串参数会导致比较失败。
        events = StatusEventStore(self.workspace / "memory" / "status").list_events(since_sequence=since_sequence, limit=limit)  # 新增代码+StatusTools: 读取状态事件；若没有这行代码，工具无数据源。
        return json.dumps([event.to_dict() for event in events], ensure_ascii=False, indent=2)  # 新增代码+StatusTools: 返回 JSON 事件列表；若没有这行代码，调用方难以结构化解析。

    def _resume_report(self, arguments: dict[str, Any]) -> str:  # 新增代码+StatusToolsV2: 返回精简恢复审计报告；若没有这行代码，模型只能读取很大的 session_resume 全量上下文。
        from learning_agent.core.resume_loader import ResumeLoader  # 新增代码+StatusToolsV2: 复用真实恢复加载器；若没有这行代码，resume_report 会和主恢复逻辑分裂。
        session_id = str(arguments.get("session_id", "")).strip()  # 新增代码+StatusToolsV2: 读取目标 session_id；若没有这行代码，工具不知道审计哪个会话。
        if not session_id:  # 新增代码+StatusToolsV2: 校验 session_id 是否缺失；若没有这行代码，空查询会产生难懂文件错误。
            return "resume_report 失败：缺少 session_id。"  # 新增代码+StatusToolsV2: 返回可修正的缺参提示；若没有这行代码，模型不知道下一步该传什么。
        context = ResumeLoader(self.workspace / "memory" / "sessions").load(session_id)  # 新增代码+StatusToolsV2: 加载真实恢复上下文；若没有这行代码，报告没有 repair/tombstone 证据。
        report = {"session_id": session_id, "consistency": context.consistency, "repair_report": context.repair_report.to_dict(), "last_boundary": context.last_boundary.to_dict() if context.last_boundary is not None else None}  # 新增代码+StatusToolsV2: 只返回恢复决策所需字段；若没有这行代码，模型会被全量消息淹没。
        return json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+StatusToolsV2: 返回结构化 JSON；若没有这行代码，模型无法稳定判断 resume_safe/needs_review。

    def _run_status(self, arguments: dict[str, Any]) -> str:  # 新增代码+StatusToolsV2: 查询当前或指定 run 状态；若没有这行代码，模型无法直接判断长任务阶段位置。
        from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+StatusToolsV2: 读取统一快照作为 run 事实源；若没有这行代码，run_status 会和 /status 分裂。
        run_id = str(arguments.get("run_id", "")).strip()  # 新增代码+StatusToolsV2: 读取可选 run_id；若没有这行代码，工具不能过滤指定 run。
        snapshot = build_status_snapshot(self.workspace)  # 新增代码+StatusToolsV2: 构建当前状态快照；若没有这行代码，run_status 没有数据源。
        runs = snapshot.get("runs", []) if isinstance(snapshot.get("runs", []), list) else []  # 新增代码+StatusToolsV2: 安全读取 run 列表；若没有这行代码，坏快照会导致工具崩溃。
        selected_runs = [run for run in runs if not run_id or str(run.get("run_id", "")) == run_id]  # 新增代码+StatusToolsV2: 按 run_id 过滤；若没有这行代码，指定 run 查询仍返回全量。
        payload = {"current_run": snapshot.get("current_run", {}), "current_turn": snapshot.get("current_turn", {}), "runs": selected_runs[:10]}  # 新增代码+StatusToolsV2: 组合 run 和 turn 状态；若没有这行代码，模型需要再调用 status_snapshot 拼信息。
        return json.dumps(payload, ensure_ascii=False, indent=2)  # 新增代码+StatusToolsV2: 返回 JSON 状态；若没有这行代码，调用方无法结构化读取。

    def _health_status(self, arguments: dict[str, Any]) -> str:  # 新增代码+StatusToolsV2: 查询 health/resume/verifier 风险状态；若没有这行代码，模型无法自查是否应该继续或暂停。
        from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+StatusToolsV2: 使用统一快照读取健康状态；若没有这行代码，health_status 会形成旁路。
        snapshot = build_status_snapshot(self.workspace)  # 新增代码+StatusToolsV2: 构建当前状态快照；若没有这行代码，工具没有健康输入。
        payload = {"health": snapshot.get("health", {}), "resume": snapshot.get("resume", {}), "verifiers": snapshot.get("verifiers", {}), "current_run": snapshot.get("current_run", {})}  # 新增代码+StatusToolsV2: 返回判断继续任务所需状态；若没有这行代码，模型要自己解析完整快照。
        return json.dumps(payload, ensure_ascii=False, indent=2)  # 新增代码+StatusToolsV2: 返回结构化健康报告；若没有这行代码，模型无法稳定读取 warnings。

    def _prompt_surface_report(self, arguments: dict[str, Any]) -> str:  # 新增代码+PromptArchitectureV1: 生成提示词表面报告工具输出；若没有这行代码，prompt_surface_report 无法返回真实加载清单
        include_block_text = bool(arguments.get("include_block_text", False))  # 新增代码+PromptArchitectureV1: 读取是否包含提示词正文的开关且默认关闭；若没有这行代码，报告可能默认泄露完整提示词正文
        include_evidence = bool(arguments.get("include_evidence", False))  # 新增代码+PromptArchitectureV1: 读取预留证据开关供 Task 5 扩展；若没有这行代码，下阶段参数会被接收但没有可解释行为
        report = self.last_prompt_surface_report  # 新增代码+PromptArchitectureV1: 读取最近一次 _build_initial_messages 保存的报告；若没有这行代码，工具无法知道本轮加载了哪些 block
        lines: list[str] = ["Prompt Surface Report"]  # 新增代码+PromptArchitectureV1: 创建报告标题；若没有这行代码，输出缺少明确用途说明
        lines.append("说明：历史设计文档/历史计划不会自动加载，除非本轮通过 read_file、read_mcp_resource、read_mcp_prompt 或其它显式读取入口读取。")  # 新增代码+PromptArchitectureV1: 明确历史文档不自动影响模型；若没有这行代码，用户可能误以为旧计划一直在上下文里
        lines.append(f"estimated_total_tokens={report.estimated_total_tokens}")  # 新增代码+PromptArchitectureV1: 输出本轮 prompt 总 token 粗估；若没有这行代码，报告缺少整体预算视角
        lines.append(f"compacted={report.compacted}")  # 新增代码+PromptArchitectureV1: 输出本轮是否发生压缩；若没有这行代码，用户无法知道 prompt 是否被 compact
        lines.append("Loaded Prompt Blocks:")  # 新增代码+PromptArchitectureV1: 创建加载块明细标题；若没有这行代码，后续 block 行缺少分组
        if not report.loaded_blocks:  # 新增代码+PromptArchitectureV1: 处理尚未构造初始消息的空报告；若没有这行代码，空列表会输出成误导性的空明细
            lines.append("- no loaded blocks yet; call _build_initial_messages/run first")  # 新增代码+PromptArchitectureV1: 提示需要先构造消息；若没有这行代码，用户不知道为什么报告为空
        for block in report.loaded_blocks:  # 新增代码+PromptArchitectureV1: 遍历本轮已加载的提示词块；若没有这行代码，报告不会列出任何具体 block
            loaded_text = "loaded" if block.loaded else "not_loaded"  # 新增代码+PromptArchitectureV1: 把布尔加载状态转成可读文本；若没有这行代码，用户需要猜 True/False 的含义
            note_text = f", note={block.note}" if block.note else ""  # 新增代码+PromptArchitectureV1: 只在有 note 时追加来源/截断说明；若没有这行代码，记忆索引元数据会丢失或输出噪声
            lines.append(f"- id={block.block_id}; title={block.title}; source={block.source}; load_policy={block.load_policy}; priority={block.priority}; loaded={loaded_text}; status={block.status}; estimated_tokens={block.estimated_tokens}{note_text}")  # 新增代码+PromptArchitectureV1: 输出每个 block 的审计字段；若没有这行代码，用户无法复核来源、策略、状态和预算
            if include_block_text:  # 新增代码+PromptArchitectureV1: 只有显式开启时才说明正文输出状态；若没有这行代码，include_block_text 参数没有任何可见效果
                lines.append("  block_text=未缓存完整正文；请显式读取对应来源文件或代码入口查看正文。")  # 新增代码+PromptArchitectureV1: 避免假装拥有完整正文缓存；若没有这行代码，报告可能误导用户以为正文可审计
        if include_evidence:  # 修改代码+PromptArchitectureV1: include_evidence 为 true 时输出 Evidence Ledger；若没有这行代码，观察事件不会桥接到提示词表面报告
            lines.extend(self._format_evidence_ledger())  # 修改代码+PromptArchitectureV1: 追加最近 observation_events 的证据账本；若没有这行代码，tool_result_offloaded 和 artifact_path 不会出现在报告里
        return "\n".join(lines)  # 新增代码+PromptArchitectureV1: 合并报告行并返回工具结果；若没有这行代码，调用方拿不到可读报告

    def _token_budget_report(self, arguments: dict[str, Any]) -> str:  # 新增代码+PromptArchitectureV1: 生成 token 预算报告工具输出；若没有这行代码，token_budget_report 无法工作
        include_tools = bool(arguments.get("include_tools", True))  # 新增代码+PromptArchitectureV1: 读取是否包含工具池预算且默认开启；若没有这行代码，默认工具池列表无法按需求出现
        report = self.last_prompt_surface_report  # 新增代码+PromptArchitectureV1: 读取最近 prompt 装配报告作为 prompt 预算来源；若没有这行代码，预算工具没有 prompt blocks 数据
        lines: list[str] = ["Token Budget Report"]  # 新增代码+PromptArchitectureV1: 创建报告标题；若没有这行代码，输出缺少明确用途说明
        lines.append("Prompt blocks:")  # 新增代码+PromptArchitectureV1: 创建 prompt blocks 预算区；若没有这行代码，测试和用户找不到提示词预算分组
        if not report.loaded_blocks:  # 新增代码+PromptArchitectureV1: 处理尚未构造初始消息的空报告；若没有这行代码，空预算会显得像正常零成本
            lines.append("- no prompt blocks recorded yet")  # 新增代码+PromptArchitectureV1: 输出空报告提示；若没有这行代码，用户不知道需要先运行装配流程
        for block in report.loaded_blocks:  # 新增代码+PromptArchitectureV1: 遍历已加载 block 生成预算明细；若没有这行代码，单块 token 成本不可见
            lines.append(f"- {block.block_id}: estimated_tokens={block.estimated_tokens}; status={block.status}")  # 新增代码+PromptArchitectureV1: 输出单块 token 粗估和状态；若没有这行代码，用户只能看到总量
        lines.append(f"estimated_total_tokens={report.estimated_total_tokens}")  # 新增代码+PromptArchitectureV1: 输出 prompt 总 token 粗估；若没有这行代码，报告不满足总预算需求
        if include_tools:  # 新增代码+PromptArchitectureV1: 只有默认或显式要求时列出工具池；若没有这行代码，include_tools 参数无法控制输出
            tool_schemas = self._available_tool_schemas()  # 新增代码+PromptArchitectureV1: 读取当前真实可见工具池 schema；若没有这行代码，报告无法反映 deferred 工具加载状态
            tool_names = self._tool_schema_names(tool_schemas)  # 新增代码+PromptArchitectureV1: 提取当前工具池名称；若没有这行代码，用户看不到当前模型可见工具
            schema_text = json.dumps(tool_schemas, ensure_ascii=False, sort_keys=True)  # 新增代码+PromptArchitectureV1: 把工具 schema 转成稳定 JSON 文本用于粗略估算；若没有这行代码，schema token 预算无法计算
            schema_tokens = max(1, len(schema_text) // 4)  # 新增代码+PromptArchitectureV1: 用字符数除以四粗估工具 schema token；若没有这行代码，报告缺少工具池预算数值
            lines.append("Current Tool Pool:")  # 新增代码+PromptArchitectureV1: 创建当前工具池分组标题；若没有这行代码，工具列表和 prompt 预算混在一起
            lines.append(f"- tool_count={len(tool_names)}")  # 新增代码+PromptArchitectureV1: 输出当前工具数量；若没有这行代码，用户无法快速判断工具池体积
            lines.append(f"- estimated_schema_tokens={schema_tokens}")  # 新增代码+PromptArchitectureV1: 输出工具 schema token 粗估；若没有这行代码，工具池预算不可见
            lines.append("- tools=" + ", ".join(tool_names))  # 新增代码+PromptArchitectureV1: 输出当前工具池名称；若没有这行代码，用户无法确认哪些工具当前可见
        return "\n".join(lines)  # 新增代码+PromptArchitectureV1: 合并预算报告行并返回；若没有这行代码，工具调用没有可读输出

    def _capability_pack_tools(self, pack_name: str) -> list[AgentTool]:  # 新增代码+CapabilityPacks: 按能力包名称查找 catalog 工具；若没有这行代码，select_pack 需要重复遍历和过滤逻辑
        normalized_pack_name = pack_name.strip().lower().replace("-", "_")  # 新增代码+CapabilityPacks: 规范化用户传入的包名；若没有这行代码，real-chrome 和 real_chrome 这类写法无法兼容
        if not normalized_pack_name:  # 新增代码+CapabilityPacks: 防御空包名请求；若没有这行代码，空 select_pack 可能返回所有无包工具或模糊失败
            return []  # 新增代码+CapabilityPacks: 空包名直接返回空列表；若没有这行代码，调用方还要额外处理 None
        return [tool for tool in self._tool_catalog() if tool.capability_pack.lower().replace("-", "_") == normalized_pack_name]  # 新增代码+CapabilityPacks: 返回匹配能力包的工具列表；若没有这行代码，无法把包名转换成具体工具

    def _tool_search_select_pack(self, requested_pack: str) -> str:  # 新增代码+CapabilityPacks: 处理 tool_search 的 select_pack:<pack> 请求；若没有这行代码，模型只能逐个 select 工具
        pack_tools = self._capability_pack_tools(requested_pack)  # 新增代码+CapabilityPacks: 查找请求能力包下的所有工具；若没有这行代码，无法知道要加载哪些工具
        if not pack_tools:  # 新增代码+CapabilityPacks: 处理未知或空能力包；若没有这行代码，未知 pack 可能被误报成功
            return f"tool_search 失败：没有找到能力包 {requested_pack!r}，请先用 tool_search 搜索相关能力。"  # 新增代码+CapabilityPacks: 返回可恢复的失败说明；若没有这行代码，模型不知道应重新搜索能力名
        loaded_names: list[str] = []  # 新增代码+CapabilityPacks: 保存本次成功加入工具池的工具名；若没有这行代码，输出无法说明加载了哪些工具
        blocked_lines: list[str] = []  # 新增代码+CapabilityPacks: 保存因策略未加载的工具说明；若没有这行代码，部分失败会被静默吞掉
        for tool in pack_tools:  # 新增代码+CapabilityPacks: 遍历能力包内每个工具；若没有这行代码，无法批量加载整包工具
            decision = self._tool_policy_decision(tool)  # 新增代码+CapabilityPacks: 使用统一工具策略判断工具是否可选择；若没有这行代码，select_pack 会绕过 deny/skill/workflow gate
            if not decision.selectable:  # 新增代码+CapabilityPacks: 跳过当前不可选择的工具；若没有这行代码，blocked 或 needs_skill 工具可能被错误加载
                blocked_lines.append(f"- {tool.name}: state={decision.state}; reason={decision.reason or '(无)'}")  # 新增代码+CapabilityPacks: 记录未加载原因；若没有这行代码，模型无法知道下一步该补 skill 还是 workflow
                continue  # 新增代码+CapabilityPacks: 继续处理同包其他工具；若没有这行代码，一个 gated 工具会阻断整个能力包
            if self.defer_tool_select_until_next_turn:  # 新增代码+CapabilityPacks: run 同一批 tool_calls 中延迟加载生效；若没有这行代码，select_pack 会破坏既有下一轮才可见语义
                self.pending_loaded_tool_names.add(tool.name)  # 新增代码+CapabilityPacks: 把工具名放入 pending 集合；若没有这行代码，下一轮工具池看不到刚选择的整包工具
            else:  # 新增代码+CapabilityPacks: 非 run 批处理场景允许立即加载；若没有这行代码，单元测试和手动调试需要额外提交 pending 状态
                self.loaded_tool_names.add(tool.name)  # 新增代码+CapabilityPacks: 把工具名加入已加载集合；若没有这行代码，select_pack 返回成功但工具池不会变化
            loaded_names.append(tool.name)  # 新增代码+CapabilityPacks: 记录成功加载的工具名；若没有这行代码，输出无法展示加载结果
        if not loaded_names:  # 新增代码+CapabilityPacks: 处理整包都被策略阻断的情况；若没有这行代码，空加载也可能返回成功
            return "tool_search 失败：能力包 " + requested_pack + " 没有可加载工具。\n" + "\n".join(blocked_lines)  # 新增代码+CapabilityPacks: 返回所有阻断原因；若没有这行代码，模型不知道为什么整包加载失败
        timing_text = "将在下一轮工具池加载" if self.defer_tool_select_until_next_turn else "已加载到当前工具池"  # 新增代码+CapabilityPacks: 根据运行状态说明生效时机；若没有这行代码，模型可能误以为同一批调用已经能用
        lines = [f"tool_search 成功：能力包 {requested_pack} {timing_text}。"]  # 新增代码+CapabilityPacks: 构造成功标题；若没有这行代码，输出缺少明确状态
        lines.append("已加载工具：" + ", ".join(loaded_names))  # 新增代码+CapabilityPacks: 列出成功加载的工具；若没有这行代码，用户无法确认包内实际加载范围
        lines.append(f"建议：如需详细流程，请调用 skill_load，name={requested_pack!r}。")  # 新增代码+CapabilityPacks: 引导模型读取对应 skill；若没有这行代码，模型可能只加载 schema 而不读取操作规程
        if blocked_lines:  # 新增代码+CapabilityPacks: 如果同包有部分工具没加载；若没有这行代码，部分阻断信息会丢失
            lines.append("未加载工具：")  # 新增代码+CapabilityPacks: 添加未加载分组标题；若没有这行代码，成功和失败条目会混在一起
            lines.extend(blocked_lines)  # 新增代码+CapabilityPacks: 追加阻断明细；若没有这行代码，gate 状态无法反馈给模型
        return "\n".join(lines)  # 新增代码+CapabilityPacks: 返回完整 select_pack 结果；若没有这行代码，工具调用没有输出

    def _tool_search_select(self, requested_name: str) -> str:  # 新增代码+ToolArchitectureV2: 处理 tool_search 的 select:<tool_name> 加载请求；若没有这行代码，模型发现 deferred 工具后仍无法把它加入后续工具池
        tool = self._find_catalog_tool(requested_name)  # 新增代码+ToolArchitectureV2: 从完整 catalog 查找用户请求加载的工具；若没有这行代码，select 无法识别 deferred MCP 工具
        if tool is None:  # 新增代码+ToolArchitectureV2: 判断请求的工具名是否存在；若没有这行代码，未知工具名会继续进入加载集合造成假成功
            return f"tool_search 失败：没有找到工具 {requested_name!r}，请先用 tool_search 搜索完整工具名。"  # 新增代码+ToolArchitectureV2: 返回清晰失败原因和修正方向；若没有这行代码，模型不知道应该重新搜索还是换名称
        decision = self._tool_policy_decision(tool)  # 新增代码+ToolPolicyV2: select 前先读取统一策略决策；若没有这行代码，blocked 或缺 skill 的工具会被错误加入 loaded_tool_names
        if not decision.selectable:  # 新增代码+ToolPolicyV2: 判断当前策略是否允许通过 select 加载；若没有这行代码，needs_skill/needs_workflow/blocked 工具无法被拦在加载前
            reason_text = f"；阻断原因：{decision.reason}" if decision.reason else ""  # 新增代码+ToolPolicyV2: 把策略原因转换成人类可读后缀；若没有这行代码，失败输出只有状态但缺少解释
            skill_hint = "；需要先加载 skill" if decision.state == "needs_skill" else ""  # 新增代码+ToolPolicyV2: 给缺 skill 的场景补一句直接提示；若没有这行代码，用户可能不知道 needs_skill 应该怎么处理
            return f"tool_search 失败：工具 {tool.name} 当前不可选择，state={decision.state}{reason_text}{skill_hint}。"  # 新增代码+ToolPolicyV2: 返回包含 state 和 reason 的 select 失败；若没有这行代码，模型会误以为 select 失败只是工具不存在
        if self.defer_tool_select_until_next_turn:  # 新增代码+ToolPolicyV2: run 正在处理同一批 tool_calls 时先延迟 select 生效；若没有这行代码，同批后续 MCP 调用会绕过下一轮工具池边界
            self.pending_loaded_tool_names.add(tool.name)  # 新增代码+ToolPolicyV2: 把工具名放入 pending 集合等待批次结束合并；若没有这行代码，select 结果会丢失或立刻生效
            return f"tool_search 成功：已选择 {tool.name}，将在下一轮工具池加载。"  # 新增代码+ToolPolicyV2: 返回下一轮才加载的清楚提示；若没有这行代码，模型会误以为同一批后续调用已经可用
        self.loaded_tool_names.add(tool.name)  # 修改代码+ToolPolicyV2: 普通直接调用 select 时继续立即加入已加载集合；若没有这行代码，现有单元测试和手动调试会失去便利
        return f"tool_search 成功：已加载 {tool.name}，后续工具池可以使用该工具。"  # 修改代码+ToolPolicyV2: 返回包含“已加载”的成功文本；若没有这行代码，调用方无法确认策略允许后的 select 是否生效

    def _tool_search(self, arguments: dict[str, Any]) -> str:  # 修改代码+ToolArchitectureV2: 搜索完整工具 catalog 并支持 select 加载 deferred 工具；若没有这行代码，模型无法发现或启用延迟工具
        query = str(arguments.get("query", "")).strip()  # 修改代码+ToolArchitectureV2: 读取并清理搜索关键词或 select 指令；若没有这行代码，空白或缺参会导致搜索意图不明确
        if not query:  # 修改代码+ToolArchitectureV2: 检查 query 是否为空；若没有这行代码，空搜索可能返回大量无意义工具
            return "tool_search 失败：缺少 query 参数。"  # 修改代码+ToolArchitectureV2: 返回清楚缺参错误；若没有这行代码，模型难以修正工具调用参数
        if query.startswith("select:"):  # 新增代码+ToolArchitectureV2: 识别 select:<tool_name> 加载指令；若没有这行代码，select 会被当成普通关键词搜索而不会加载工具
            return self._tool_search_select(query.removeprefix("select:").strip())  # 新增代码+ToolArchitectureV2: 把 select 后面的工具名交给加载函数；若没有这行代码，deferred 工具无法进入后续工具池
        if query.startswith("select_pack:"):  # 新增代码+CapabilityPacks: 识别 select_pack:<pack> 加载指令；若没有这行代码，模型无法批量加载能力包工具
            return self._tool_search_select_pack(query.removeprefix("select_pack:").strip())  # 新增代码+CapabilityPacks: 把包名交给能力包加载函数；若没有这行代码，select_pack 只会被当成普通搜索
        max_results = self._tool_search_max_results(arguments.get("max_results"))  # 修改代码+ToolArchitectureV2: 解析最大结果数并限制范围；若没有这行代码，搜索结果可能撑爆上下文
        terms = self._tool_search_terms(query)  # 修改代码+ToolArchitectureV2: 把搜索词拆成可匹配的小写关键词；若没有这行代码，多词搜索和大小写匹配会不稳定
        scored_results: list[tuple[int, AgentTool, str, ToolPolicyDecision, str]] = []  # 修改代码+ToolPolicyV2: 保存分数、AgentTool、source、策略决策和参数文本；若没有这行代码，搜索结果无法展示 blocked/needs_skill 等统一状态
        for tool in self._tool_catalog():  # 修改代码+ToolArchitectureV2: 遍历完整工具 catalog 而不是当前工具池；若没有这行代码，deferred MCP 工具不会被 tool_search 发现
            if not tool.name:  # 新增代码+ToolArchitectureV2: 跳过没有名称的异常工具条目；若没有这行代码，坏 catalog 数据可能污染搜索结果
                continue  # 新增代码+ToolArchitectureV2: 继续处理其他工具；若没有这行代码，单个坏工具会阻断搜索
            properties = tool.input_schema.get("properties", {}) if isinstance(tool.input_schema, dict) else {}  # 新增代码+ToolArchitectureV2: 从 AgentTool.input_schema 读取参数字段定义；若没有这行代码，搜索无法按参数名匹配也无法展示参数
            parameter_names = [str(name) for name in properties.keys()] if isinstance(properties, dict) else []  # 新增代码+ToolArchitectureV2: 把参数字段名转成字符串列表；若没有这行代码，模型找到工具后仍不知道主要入参
            pack_aliases = tool.aliases + ([tool.capability_pack] if tool.capability_pack else [])  # 新增代码+CapabilityPacks: 把能力包名也作为搜索别名；若没有这行代码，用户搜 file_operations 可能找不到包内工具
            pack_search_hint = " ".join(part for part in [tool.search_hint, tool.capability_pack] if part)  # 新增代码+CapabilityPacks: 把能力包名加入搜索提示；若没有这行代码，自然语言搜能力包的召回会变弱
            score = self._tool_search_score(terms, tool.name, tool.description, parameter_names, pack_search_hint, pack_aliases)  # 修改代码+CapabilityPacks: 把 pack 名纳入相关度计算；若没有这行代码，工具搜索无法按能力包名召回
            if score <= 0:  # 修改代码+ToolArchitectureV2: 过滤没有任何命中的工具；若没有这行代码，搜索会返回大量无关工具
                continue  # 修改代码+ToolArchitectureV2: 跳过不相关工具；若没有这行代码，无关工具会污染结果
            source_parts = [tool.source]  # 新增代码+ToolArchitectureV2: 准备展示工具来源字段；若没有这行代码，输出缺少 source 信息
            if tool.server_name:  # 新增代码+ToolArchitectureV2: MCP 工具通常带有 server 名；若没有这行代码，外部工具来源会缺少具体 server
                source_parts.append(f"server={tool.server_name}")  # 新增代码+ToolArchitectureV2: 把 server 名追加到来源文本；若没有这行代码，用户和模型难以区分不同 MCP server
            source_text = ", ".join(source_parts)  # 新增代码+ToolArchitectureV2: 合并来源片段成可读文本；若没有这行代码，输出 source 字段无法直接展示
            decision = self._tool_policy_decision(tool)  # 修改代码+ToolPolicyV2: 用统一 ToolPolicy 决策生成搜索状态；若没有这行代码，tool_search 会继续手写 loaded/deferred 而漏掉 blocked 和 gate 状态
            parameter_text = ", ".join(parameter_names) if parameter_names else "(无参数)"  # 修改代码+ToolArchitectureV2: 把参数名合并成可读文本；若没有这行代码，输出里参数展示不清楚
            scored_results.append((score, tool, source_text, decision, parameter_text))  # 修改代码+ToolPolicyV2: 保存包含策略决策的 catalog 命中结果；若没有这行代码，格式化阶段拿不到 state 和 reason
        scored_results.sort(key=lambda item: (-item[0], item[1].name))  # 修改代码+ToolArchitectureV2: 按分数降序和工具名升序排序；若没有这行代码，搜索结果顺序不稳定且不够相关
        visible_results = scored_results[:max_results]  # 修改代码+ToolArchitectureV2: 截取最多 max_results 条结果；若没有这行代码，大量 MCP 工具会撑爆上下文
        if not visible_results:  # 修改代码+ToolArchitectureV2: 处理没有命中的情况；若没有这行代码，空结果会返回只有标题的模糊文本
            return f"tool_search 成功：没有找到匹配 query={query!r} 的工具。"  # 修改代码+ToolArchitectureV2: 明确告诉模型没有结果；若没有这行代码，模型可能误以为工具搜索失败
        lines = [f"tool_search 成功：query={query!r}，找到 {len(scored_results)} 个相关工具，显示前 {len(visible_results)} 个。"]  # 修改代码+ToolArchitectureV2: 构造结果标题；若没有这行代码，模型不知道结果数量和截断情况
        for index, (_, tool, source_text, decision, parameter_text) in enumerate(visible_results, start=1):  # 修改代码+ToolPolicyV2: 逐条格式化带策略决策的 catalog 命中结果；若没有这行代码，命中结果无法展示 state/reason
            lines.append(f"{index}. {tool.name}")  # 修改代码+ToolArchitectureV2: 输出工具名；若没有这行代码，模型不知道后续应调用或 select 哪个工具
            lines.append(f"   source/来源：{source_text}")  # 修改代码+ToolArchitectureV2: 输出 source 字段并保留中文来源提示；若没有这行代码，模型无法区分内置工具和外部 MCP 工具
            lines.append(f"   state：{decision.state}")  # 修改代码+ToolPolicyV2: 输出 ToolPolicyDecision.state；若没有这行代码，模型不知道工具是 loaded、deferred、blocked 还是缺少 gate
            lines.append(f"   参数：{parameter_text}")  # 修改代码+ToolArchitectureV2: 输出参数名；若没有这行代码，模型找到工具后还可能传错参数
            if tool.aliases:  # 新增代码+ToolPolicyV2: 只有工具声明了 aliases 时才展示别名；若没有这行代码，模型看不到可用于搜索和理解的替代名称
                lines.append(f"   aliases：{', '.join(tool.aliases)}")  # 新增代码+ToolPolicyV2: 输出工具别名列表；若没有这行代码，别名命中后仍缺少可解释的结果依据
            if tool.search_hint:  # 新增代码+ToolPolicyV2: 只有工具声明了 search_hint 时才展示搜索提示；若没有这行代码，MCP 提供的语义线索不会出现在搜索结果里
                lines.append(f"   search_hint：{tool.search_hint}")  # 新增代码+ToolPolicyV2: 输出搜索提示文本；若没有这行代码，模型不知道该工具为什么被召回
            if tool.capability_pack:  # 新增代码+CapabilityPacks: 只有工具声明了能力包时才展示包名；若没有这行代码，模型不知道可以用哪个 select_pack 批量加载
                lines.append(f"   capability_pack：{tool.capability_pack}")  # 新增代码+CapabilityPacks: 输出能力包名称；若没有这行代码，搜索结果缺少批量加载入口
            lines.append(f"   说明：{tool.description or '(无说明)'}")  # 修改代码+ToolArchitectureV2: 输出工具说明；若没有这行代码，模型缺少选择工具的语义依据
            if decision.reason:  # 新增代码+ToolPolicyV2: 只有策略提供原因时才展示阻断说明；若没有这行代码，blocked 或 gate 工具只显示状态而缺少人话解释
                lines.append(f"   阻断原因：{decision.reason}")  # 新增代码+ToolPolicyV2: 输出清楚的策略原因；若没有这行代码，用户不知道工具为什么不可见或不可选
            if decision.state == "deferred":  # 修改代码+ToolPolicyV2: 只给 deferred 工具显示加载提示；若没有这行代码，blocked/needs_skill 工具可能出现误导性的 select 提示
                lines.append(f"   加载提示：select:{tool.name}")  # 修改代码+CapabilityPacks: 保留单工具加载提示兼容旧流程；若没有这行代码，已有测试和模型习惯可能找不到精确 select 语法
                if tool.capability_pack:  # 新增代码+CapabilityPacks: 只有存在能力包时才追加整包加载提示；若没有这行代码，无包工具会出现空 pack 指令
                    lines.append(f"   能力包加载提示：select_pack:{tool.capability_pack}")  # 新增代码+CapabilityPacks: 输出批量加载指令；若没有这行代码，模型不知道可以一次加载整组工具
        return "\n".join(lines)  # 修改代码+ToolArchitectureV2: 返回完整搜索结果文本；若没有这行代码，工具搜索无法把结果交回模型

    @staticmethod  # 新增代码+ToolSearch: 解析最大结果数不依赖实例状态；若省略: 测试和调用都需要额外对象状态
    def _tool_search_max_results(raw_value: Any) -> int:  # 新增代码+ToolSearch: 把 max_results 转成 1 到 20 的整数；若省略: 模型可能传入字符串、空值或过大数字
        try:  # 新增代码+ToolSearch: 捕获模型传入非数字值的情况；若省略: int() 异常会中断工具调用
            value = int(raw_value) if raw_value is not None else 10  # 新增代码+ToolSearch: None 使用默认 10，否则尝试转整数；若省略: 省略 max_results 时没有默认值
        except (TypeError, ValueError):  # 新增代码+ToolSearch: 处理无法转成整数的参数；若省略: 坏参数会让工具崩溃
            value = 10  # 新增代码+ToolSearch: 非法 max_results 回退默认值；若省略: 模型一次传错参数就无法继续搜索
        return max(1, min(value, 20))  # 新增代码+ToolSearch: 把结果数限制在 1 到 20；若省略: 0 或超大值会导致结果为空或撑爆上下文

    @staticmethod  # 新增代码+ToolSearch: 搜索词拆分不依赖实例状态；若省略: 逻辑会散落在主搜索函数里
    def _tool_search_terms(query: str) -> list[str]:  # 新增代码+ToolSearch: 把用户查询拆成小写关键词；若省略: 多词查询和下划线工具名匹配会变差
        normalized = query.replace("_", " ").replace("-", " ").lower()  # 新增代码+ToolSearch: 把下划线和连字符转为空格并统一小写；若省略: mcp 工具名片段不容易被匹配
        terms = [term for term in normalized.split() if term]  # 新增代码+ToolSearch: 按空白拆词并去掉空项；若省略: 多余空格会产生无意义关键词
        return terms or [query.lower()]  # 新增代码+ToolSearch: 没有拆出词时保留原始小写查询；若省略: 中文或特殊查询可能变成空搜索

    @staticmethod  # 新增代码+ToolSearch: 工具名提取不依赖实例状态；若省略: 每个调用处都要重复 schema 防御逻辑
    def _tool_schema_name(schema: dict[str, Any]) -> str:  # 新增代码+ToolSearch: 从 OpenAI-compatible schema 中取 function.name；若省略: 搜索无法识别工具名称
        function = schema.get("function", {}) if isinstance(schema, dict) else {}  # 新增代码+ToolSearch: 安全读取 function 字段；若省略: 畸形 schema 可能触发异常
        if not isinstance(function, dict):  # 新增代码+ToolSearch: 检查 function 是否为字典；若省略: 非对象 function 会让 get 调用失败
            return ""  # 新增代码+ToolSearch: 坏 schema 返回空名并交给上层跳过；若省略: 搜索会被单个坏 schema 打断
        return str(function.get("name", "")).strip()  # 新增代码+ToolSearch: 返回清理后的工具名；若省略: 工具名前后空白会影响匹配和展示

    @staticmethod  # 新增代码+ToolSearch: 工具说明提取不依赖实例状态；若省略: 搜索和展示会重复读取逻辑
    def _tool_schema_description(schema: dict[str, Any]) -> str:  # 新增代码+ToolSearch: 从 schema 中取工具说明；若省略: 搜索无法利用自然语言说明
        function = schema.get("function", {}) if isinstance(schema, dict) else {}  # 新增代码+ToolSearch: 安全读取 function 字段；若省略: 畸形 schema 可能触发异常
        if not isinstance(function, dict):  # 新增代码+ToolSearch: 检查 function 是否为字典；若省略: 非对象 function 会让 get 调用失败
            return ""  # 新增代码+ToolSearch: 坏 schema 返回空说明；若省略: 搜索会因为坏 schema 中断
        return str(function.get("description", "")).strip()  # 新增代码+ToolSearch: 返回清理后的说明文本；若省略: 说明里的空白会污染输出

    @staticmethod  # 新增代码+ToolSearch: 参数名提取不依赖实例状态；若省略: 模型找到工具后缺少参数提示
    def _tool_schema_parameter_names(schema: dict[str, Any]) -> list[str]:  # 新增代码+ToolSearch: 从工具参数 schema 中提取参数名；若省略: 搜索无法按参数名匹配
        function = schema.get("function", {}) if isinstance(schema, dict) else {}  # 新增代码+ToolSearch: 安全读取 function 字段；若省略: 畸形 schema 可能触发异常
        if not isinstance(function, dict):  # 新增代码+ToolSearch: 检查 function 是否为字典；若省略: 非对象 function 会让 get 调用失败
            return []  # 新增代码+ToolSearch: 坏 schema 返回空参数；若省略: 搜索会被异常中断
        parameters = function.get("parameters", {})  # 新增代码+ToolSearch: 读取 JSON Schema 参数对象；若省略: 无法进入 properties
        if not isinstance(parameters, dict):  # 新增代码+ToolSearch: 检查 parameters 是否为字典；若省略: 畸形参数 schema 会导致异常
            return []  # 新增代码+ToolSearch: 坏参数 schema 返回空列表；若省略: 单个坏工具会破坏搜索
        properties = parameters.get("properties", {})  # 新增代码+ToolSearch: 读取参数字段定义；若省略: 无法枚举参数名
        if not isinstance(properties, dict):  # 新增代码+ToolSearch: 检查 properties 是否为字典；若省略: 非对象 properties 会导致 items 调用失败
            return []  # 新增代码+ToolSearch: 坏 properties 返回空列表；若省略: 搜索健壮性降低
        return [str(name) for name in properties.keys()]  # 新增代码+ToolSearch: 返回所有参数名字符串；若省略: 输出和搜索都看不到参数字段

    @staticmethod  # 新增代码+ToolSearch: 来源判断不依赖实例状态；若省略: 搜索结果无法解释工具来自哪里
    def _tool_schema_source(tool_name: str) -> str:  # 新增代码+ToolSearch: 根据工具名判断内置或 MCP 来源；若省略: 用户和模型难以区分工具边界
        parts = tool_name.split("__")  # 新增代码+ToolSearch: 按 MCP 命名约定拆分工具名；若省略: 无法提取 server 名
        if len(parts) >= 3 and parts[0] == "mcp":  # 新增代码+ToolSearch: 识别 mcp__server__tool 格式；若省略: MCP 工具会被误标为内置
            return f"MCP server：{parts[1]}"  # 新增代码+ToolSearch: 返回 MCP server 来源；若省略: 搜索结果缺少外部来源信息
        return "内置工具"  # 新增代码+ToolSearch: 非 MCP 前缀默认视为内置工具；若省略: 内置工具没有来源说明

    @staticmethod  # 新增代码+ToolSearch: 相关度计算不依赖实例状态；若省略: 主搜索函数会变得难读且难测
    def _tool_search_score(terms: list[str], tool_name: str, description: str, parameter_names: list[str], search_hint: str = "", aliases: list[str] | None = None) -> int:  # 修改代码+ToolPolicyV2: 根据名称、说明、参数名、搜索提示和别名计算匹配分数；若没有这行代码，searchHint/aliases 元数据只保存但不参与发现
        name_text = tool_name.lower()  # 新增代码+ToolSearch: 工具名转小写便于大小写无关匹配；若省略: Notebook/notebook 这类大小写差异会漏匹配
        description_text = description.lower()  # 新增代码+ToolSearch: 说明转小写便于匹配；若省略: 英文说明大小写可能影响结果
        parameter_text = " ".join(parameter_names).lower()  # 新增代码+ToolSearch: 参数名合并并转小写；若省略: 无法按 query/url/path 这类参数名搜索
        search_hint_text = search_hint.lower()  # 新增代码+ToolPolicyV2: 把 MCP searchHint 转小写后参与匹配；若没有这行代码，服务端提供的搜索语义不会影响召回
        alias_text = " ".join(aliases or []).lower()  # 新增代码+ToolPolicyV2: 把 aliases 合并转小写后参与匹配；若没有这行代码，别名不会真正帮助模型发现工具
        score = 0  # 新增代码+ToolSearch: 初始化相关度分数；若省略: 后续无法累加命中权重
        for term in terms:  # 新增代码+ToolSearch: 遍历每个查询关键词；若省略: 多词查询只会处理整体字符串
            if term in name_text:  # 新增代码+ToolSearch: 工具名命中权重最高；若省略: 精确工具名搜索排序会变差
                score += 6  # 新增代码+ToolSearch: 给工具名命中较高分；若省略: 名称相关工具可能排在说明偶然命中的工具后面
            if term in alias_text:  # 新增代码+ToolPolicyV2: 别名命中说明用户或模型使用了替代称呼；若没有这行代码，aliases 只能展示不能搜索
                score += 5  # 新增代码+ToolPolicyV2: 给别名命中接近工具名的高分；若没有这行代码，别名匹配可能排在不相关说明命中之后
            if term in search_hint_text:  # 新增代码+ToolPolicyV2: searchHint 命中说明 MCP server 主动给了语义线索；若没有这行代码，外部工具发现能力不如 ClaudeCode 风格 catalog
                score += 4  # 新增代码+ToolPolicyV2: 给 searchHint 命中较高分；若没有这行代码，服务端提示无法有效提升排序
            if term in parameter_text:  # 新增代码+ToolSearch: 参数名命中说明模型可能正在找某类入参；若省略: query/url/path 这类搜索效果变差
                score += 3  # 新增代码+ToolSearch: 给参数名命中中等分；若省略: 参数相关性无法影响排序
            if term in description_text:  # 新增代码+ToolSearch: 说明命中用于自然语言能力发现；若省略: “天气/Notebook”等描述词无法召回工具
                score += 2  # 新增代码+ToolSearch: 给说明命中基础分；若省略: 自然语言搜索结果排序不稳定
        return score  # 新增代码+ToolSearch: 返回最终相关度；若省略: 调用方无法判断是否命中

    @staticmethod  # 新增代码+极简工具面: 解析四原子工具里的整数参数；若没有这行代码，read/bash 的 offset、limit、timeout 解析会重复且容易不一致
    def _clamped_int_argument(raw_value: Any, default: int, minimum: int, maximum: int) -> int:  # 新增代码+极简工具面: 把模型传入值夹到安全范围；若没有这行代码，过大或非法数字可能导致长时间等待或超长输出
        try:  # 新增代码+极简工具面: 捕获模型传入字符串、None 或错误类型的情况；若没有这行代码，坏参数会让工具直接抛异常
            value = int(raw_value) if raw_value is not None else default  # 新增代码+极简工具面: 有值就尝试转整数，没有值就用默认值；若没有这行代码，可选参数缺省时没有稳定行为
        except (TypeError, ValueError):  # 新增代码+极简工具面: 处理无法转成整数的参数；若没有这行代码，模型一次传错数字就会中断工具调用
            value = default  # 新增代码+极简工具面: 非法值回退默认值；若没有这行代码，工具缺少容错能力
        return max(minimum, min(value, maximum))  # 新增代码+极简工具面: 把整数限制在最小和最大值之间；若没有这行代码，负偏移或超大超时会造成不稳定行为

    def _dynamic_prompt_read_key(self, path: Path) -> str | None:  # 新增代码+动态提示词分层: 把工作区内提示词路径转成稳定 key；若没有这行代码，read 门控无法知道哪些父层已经读取
        try:  # 新增代码+动态提示词分层: 捕获 path 不在工作区内的情况；若没有这行代码，relative_to 失败会打断普通 read
            relative_path = path.resolve().relative_to(self.workspace)  # 新增代码+动态提示词分层: 计算相对工作区路径；若没有这行代码，绝对路径无法和提示词层级规则匹配
        except ValueError:  # 新增代码+动态提示词分层: 处理不属于当前 workspace 的路径；若没有这行代码，外部路径会产生异常
            return None  # 新增代码+动态提示词分层: 非工作区路径不参与动态提示词门控；若没有这行代码，普通安全错误可能被误判为提示词层级问题
        return relative_path.as_posix().lower()  # 新增代码+动态提示词分层: 用小写 POSIX 路径做 key；若没有这行代码，Windows 大小写和反斜杠会导致同一文件匹配不上

    @staticmethod  # 新增代码+动态提示词分层: 技能根路径判断不依赖实例状态；若没有这行代码，门控逻辑会和其它实例数据耦合
    def _dynamic_prompt_skill_base(read_key: str) -> str | None:  # 新增代码+动态提示词分层: 判断路径是否属于 skills 动态提示词树；若没有这行代码，read 无法区分普通文件和分层提示词
        if read_key.startswith("learning_agent/skills/"):  # 新增代码+动态提示词分层: 支持项目根工作区下的 learning_agent/skills 路径；若没有这行代码，当前项目默认路径不会被门控
            return "learning_agent/skills"  # 新增代码+动态提示词分层: 返回项目根模式的技能根；若没有这行代码，后续无法拼出父层 key
        if read_key.startswith("skills/"):  # 新增代码+动态提示词分层: 支持工作区本身就是 learning_agent 包目录的路径；若没有这行代码，包目录作为工作区时分层会失效
            return "skills"  # 新增代码+动态提示词分层: 返回包目录模式的技能根；若没有这行代码，后续无法拼出父层 key
        return None  # 新增代码+动态提示词分层: 普通文件不属于动态提示词树；若没有这行代码，read 可能错误拦截代码文件

    def _dynamic_prompt_read_gate(self, path: Path) -> str | None:  # 新增代码+动态提示词分层: 检查 read 是否跳过了 tool_list 或父 SKILL；若没有这行代码，三级动态提示词树只能靠模型自觉遵守
        read_key = self._dynamic_prompt_read_key(path)  # 新增代码+动态提示词分层: 取得当前读取文件的稳定 key；若没有这行代码，门控没有判断对象
        if read_key is None:  # 新增代码+动态提示词分层: 如果路径不在 workspace 内；若没有这行代码，后续字符串判断可能拿到 None
            return None  # 新增代码+动态提示词分层: 非 workspace 路径交给原有边界处理；若没有这行代码，提示词门控会越权处理普通错误
        skill_base = self._dynamic_prompt_skill_base(read_key)  # 新增代码+动态提示词分层: 判断当前路径是否在 skills 动态树内；若没有这行代码，无法只门控提示词文件
        if skill_base is None:  # 新增代码+动态提示词分层: 普通代码、README、配置不属于动态提示词树；若没有这行代码，read 可能误拦截项目文件
            return None  # 新增代码+动态提示词分层: 普通文件允许按原流程读取；若没有这行代码，agent 会无法正常读代码
        tool_list_key = f"{skill_base}/tool_list.md"  # 新增代码+动态提示词分层: 计算第一层总索引 key；若没有这行代码，后续无法判断 tool_list 是否已读
        if read_key == tool_list_key:  # 新增代码+动态提示词分层: 总索引本身必须可直接读取；若没有这行代码，模型永远无法进入动态规则树
            return None  # 新增代码+动态提示词分层: 允许读取第一层索引；若没有这行代码，分层门控会变成死锁
        relative_under_skills = read_key.removeprefix(f"{skill_base}/")  # 新增代码+动态提示词分层: 取出 skills 根目录下的相对路径；若没有这行代码，无法解析 skill 名和 rules 层
        parts = relative_under_skills.split("/")  # 新增代码+动态提示词分层: 按路径段拆分；若没有这行代码，无法判断是否为 <skill>/SKILL.md 或 <skill>/rules/*.md
        if len(parts) >= 2 and parts[1] == "skill.md" and tool_list_key not in self.loaded_dynamic_prompt_paths:  # 新增代码+动态提示词分层: 读取第二层 SKILL 前必须读第一层索引；若没有这行代码，模型可以绕过总目录直接猜 skill 路径
            return f"read 失败：动态提示词分层要求先读取 {tool_list_key}，再读取目标 SKILL.md。"  # 新增代码+动态提示词分层: 返回可恢复的父层提示；若没有这行代码，模型不知道下一步该读哪个文件
        if len(parts) >= 3 and parts[1] == "rules":  # 新增代码+动态提示词分层: 识别第三层子规则文件；若没有这行代码，rules 文件不会受父层保护
            parent_skill_key = f"{skill_base}/{parts[0]}/skill.md"  # 新增代码+动态提示词分层: 计算该子规则对应的父 SKILL key；若没有这行代码，无法检查第二层是否已读
            parent_skill_path = f"{skill_base}/{parts[0]}/SKILL.md"  # 新增代码+动态提示词分层: 准备给模型看的父 SKILL 路径；若没有这行代码，错误提示会显示小写 skill.md 不利于用户定位
            if tool_list_key not in self.loaded_dynamic_prompt_paths:  # 新增代码+动态提示词分层: 子规则读取前先要求第一层索引；若没有这行代码，模型仍可直接跳进 rules 目录
                return f"read 失败：动态提示词子规则需要先读取 {tool_list_key}，再读取 {parent_skill_path}。"  # 新增代码+动态提示词分层: 返回第一层缺失提示；若没有这行代码，模型不知道要从总目录开始
            if parent_skill_key not in self.loaded_dynamic_prompt_paths:  # 新增代码+动态提示词分层: 子规则读取前再要求第二层父 skill；若没有这行代码，模型会跳过能力边界说明
                return f"read 失败：动态提示词子规则需要先读取 {parent_skill_path}。"  # 新增代码+动态提示词分层: 返回第二层缺失提示；若没有这行代码，模型不知道要先读哪个父文件
        return None  # 新增代码+动态提示词分层: 没有违反层级时允许 read 继续；若没有这行代码，合法提示词读取会被错误拒绝

    def _dynamic_skill_name_from_read_key(self, read_key: str) -> str:  # 新增代码+浏览器自动化: 从已读取的动态提示词路径解析 skill 名；若没有这行代码，read 无法知道应该激活哪个能力包
        skill_base = self._dynamic_prompt_skill_base(read_key)  # 新增代码+浏览器自动化: 先判断路径是否属于 skills 动态提示词树；若没有这行代码，普通代码读取也可能被误当成 skill
        if skill_base is None:  # 新增代码+浏览器自动化: 非 skill 路径不应该触发工具解锁；若没有这行代码，读取任意文件都可能污染工具池
            return ""  # 新增代码+浏览器自动化: 返回空字符串表达没有 skill 名；若没有这行代码，调用方需要处理 None 分支
        relative_under_skills = read_key.removeprefix(f"{skill_base}/")  # 新增代码+浏览器自动化: 取得 skills 根目录下的相对路径；若没有这行代码，无法从 learning_agent/skills/browser_automation/SKILL.md 中提取 browser_automation
        parts = relative_under_skills.split("/")  # 新增代码+浏览器自动化: 按路径段拆分 skill 名、SKILL.md 和 rules 层；若没有这行代码，后续判断只能做脆弱字符串匹配
        if len(parts) < 2:  # 新增代码+浏览器自动化: tool_list.md 这类第一层索引没有第二段；若没有这行代码，读取总索引也会被误识别成 skill
            return ""  # 新增代码+浏览器自动化: 第一层索引不解锁具体工具包；若没有这行代码，读 tool_list 会一次性打开太多能力
        if parts[1] not in {"skill.md", "rules"}:  # 新增代码+浏览器自动化: 只有第二层 SKILL 或第三层 rules 才代表进入某个具体 skill；若没有这行代码，skill 目录里的杂项文件也会触发工具加载
            return ""  # 新增代码+浏览器自动化: 非标准动态提示词文件不触发解锁；若没有这行代码，工具池状态会难以审计
        return parts[0].strip().lower().replace("-", "_")  # 新增代码+浏览器自动化: 规范化 skill 名用于映射能力包；若没有这行代码，real-chrome 和 real_chrome 这类写法无法统一匹配

    def _load_tools_for_dynamic_skill_read(self, read_key: str) -> None:  # 新增代码+浏览器自动化: 根据已读取的动态 skill 激活对应工具包；若没有这行代码，极简 read-based 路由无法真正调用浏览器 MCP 工具
        skill_name = self._dynamic_skill_name_from_read_key(read_key)  # 新增代码+浏览器自动化: 解析当前 read 事件对应的 skill 名；若没有这行代码，后续不知道查哪个能力包映射
        if not skill_name:  # 新增代码+浏览器自动化: 没有具体 skill 时不做任何工具池变更；若没有这行代码，读取 tool_list 或普通文件可能误触发加载
            return  # 新增代码+浏览器自动化: 提前结束无关读取；若没有这行代码，空 skill 名会继续查映射造成噪声
        pack_names = DYNAMIC_SKILL_CAPABILITY_PACKS.get(skill_name, ())  # 新增代码+浏览器自动化: 查找该 skill 可解锁的能力包列表；若没有这行代码，浏览器 skill 和真实工具包无法建立关系
        if not pack_names:  # 新增代码+浏览器自动化: 没有映射的 skill 仍只作为提示词加载；若没有这行代码，普通 skill 可能因为没有工具包而报错
            return  # 新增代码+浏览器自动化: 对无工具包 skill 保持安静返回；若没有这行代码，动态提示词读取会产生无意义失败
        self.tool_policy_context.loaded_skills.add(skill_name)  # 新增代码+浏览器自动化: 把已读 skill 记录进 ToolPolicy 上下文；若没有这行代码，real_chrome 这类 skill gate 永远不会满足
        if skill_name == "real_chrome":  # 新增代码+真实浏览器自动化: 读取 real_chrome skill 等价于用户/模型正在进入真实 Chrome 路线；若没有这行代码，普通 browser_open 可能在连接前过早可见
            self.real_chrome_requested = True  # 新增代码+真实浏览器自动化: 启用真实 Chrome workflow 拦截普通独立浏览器动作；若没有这行代码，真实登录态需求可能误走独立 Chromium
        loaded_names: list[str] = []  # 新增代码+浏览器自动化: 保存本次真正加入 loaded_tool_names 的工具名；若没有这行代码，观察事件无法说明解锁了哪些工具
        for pack_name in pack_names:  # 新增代码+浏览器自动化: 遍历一个 skill 对应的一个或多个能力包；若没有这行代码，real_chrome 无法同时准备连接和页面操作能力
            self.tool_policy_context.loaded_skills.add(pack_name)  # 新增代码+浏览器自动化: 也把能力包名记为已加载 skill 语义；若没有这行代码，skill_gate 使用包名时无法匹配
            for tool in self._capability_pack_tools(pack_name):  # 新增代码+浏览器自动化: 遍历能力包下的全部 catalog 工具；若没有这行代码，无法把包名转换成具体 MCP 工具
                decision = self._tool_policy_decision(tool)  # 新增代码+浏览器自动化: 读取当前策略状态避免加载被 deny 的工具；若没有这行代码，read skill 会绕过统一 ToolPolicy
                if decision.state == "blocked":  # 新增代码+浏览器自动化: 被安全策略明确阻断的工具不能仅因读了 skill 就加入；若没有这行代码，deny 规则会被动态提示词绕开
                    continue  # 新增代码+浏览器自动化: 跳过阻断工具并继续同包其他工具；若没有这行代码，一个 blocked 工具会影响整个包加载
                self.loaded_tool_names.add(tool.name)  # 新增代码+浏览器自动化: 把允许准备的 deferred 工具加入当前工具池状态；若没有这行代码，后续模型 schema 仍看不到浏览器工具
                loaded_names.append(tool.name)  # 新增代码+浏览器自动化: 记录成功准备的工具名用于审计；若没有这行代码，无法回看 read skill 带来了哪些工具
        if loaded_names:  # 新增代码+浏览器自动化: 只有确实加载到工具时才记录观察事件；若没有这行代码，无工具包 skill 会产生噪声事件
            self._record_observation("dynamic_skill_loaded_tools", {"skill": skill_name, "packs": list(pack_names), "tools": loaded_names})  # 新增代码+浏览器自动化: 记录 skill 到工具包的解锁证据；若没有这行代码，真实调试时难以解释工具池为何变大

    def _remember_dynamic_prompt_read(self, path: Path) -> None:  # 新增代码+动态提示词分层: 在成功读取后记录动态提示词层级状态；若没有这行代码，读过父层后仍无法进入子层
        read_key = self._dynamic_prompt_read_key(path)  # 新增代码+动态提示词分层: 获取成功读取文件的稳定 key；若没有这行代码，记录集合不知道该保存什么
        if read_key is None:  # 新增代码+动态提示词分层: 非工作区路径不记录；若没有这行代码，None 可能进入集合并污染状态
            return  # 新增代码+动态提示词分层: 直接结束记录流程；若没有这行代码，后续 add 会收到无意义值
        if self._dynamic_prompt_skill_base(read_key) is None:  # 新增代码+动态提示词分层: 只有 skills 动态提示词树需要记录层级；若没有这行代码，普通代码文件会污染门控状态
            return  # 新增代码+动态提示词分层: 普通文件不记录；若没有这行代码，集合会逐渐膨胀且难以审计
        self.loaded_dynamic_prompt_paths.add(read_key)  # 新增代码+动态提示词分层: 保存已读层级 key；若没有这行代码，后续子规则无法确认父层已经加载
        self._load_tools_for_dynamic_skill_read(read_key)  # 新增代码+浏览器自动化: 成功读取具体 skill 后同步准备对应工具包；若没有这行代码，浏览器自动化仍只能停留在提示词层

    def _read_atom(self, arguments: dict[str, Any]) -> str:  # 新增代码+极简工具面: 实现 read 原子工具；若没有这行代码，首轮 read schema 只能被看见但无法执行
        raw_path = str(arguments.get("path", "")).strip()  # 新增代码+极简工具面: 从参数读取并清理 path；若没有这行代码，工具不知道要读哪个文件
        if not raw_path:  # 新增代码+极简工具面: 检查模型是否提供了路径；若没有这行代码，空路径会进入路径解析产生模糊错误
            return "read 失败：缺少 path 参数。"  # 新增代码+极简工具面: 返回清楚缺参错误；若没有这行代码，模型难以修正下一次调用
        path = self._resolve_workspace_path(raw_path)  # 新增代码+极简工具面: 把相对路径安全解析到工作区内；若没有这行代码，read 可能越界读取任意文件
        if path is None:  # 新增代码+极简工具面: 检查路径是否越过工作区边界；若没有这行代码，用户项目外文件可能被读取
            return "read 失败：只能读取 learning_agent 工作区内的文件。"  # 新增代码+极简工具面: 返回安全边界错误；若没有这行代码，模型不知道失败原因
        if not path.exists():  # 新增代码+极简工具面: 检查文件是否存在；若没有这行代码，后续读取会抛出 FileNotFoundError
            return f"read 失败：文件不存在：{path}"  # 新增代码+极简工具面: 返回包含路径的不存在提示；若没有这行代码，模型无法定位错路径
        if path.is_dir():  # 新增代码+极简工具面: 检查路径是否是目录；若没有这行代码，目录读取会抛出不清晰异常
            return f"read 失败：不能把目录当文件读取：{path}"  # 新增代码+极简工具面: 返回目录错误；若没有这行代码，模型可能继续用 read 读取目录
        gate_message = self._dynamic_prompt_read_gate(path)  # 新增代码+动态提示词分层: 检查是否跳过了动态提示词父层；若没有这行代码，模型仍能直接读取第三层子规则
        if gate_message is not None:  # 新增代码+动态提示词分层: 如果门控发现缺少父层；若没有这行代码，失败提示不会返回给模型
            return gate_message  # 新增代码+动态提示词分层: 返回清楚的按层读取建议；若没有这行代码，read 会继续把子规则塞进上下文
        text = path.read_text(encoding="utf-8", errors="replace")  # 新增代码+极简工具面: 用 UTF-8 读取文本并替换坏字符；若没有这行代码，read 拿不到文件正文
        self._remember_dynamic_prompt_read(path)  # 新增代码+动态提示词分层: 成功读取后记录当前层级；若没有这行代码，读过 tool_list 或 SKILL 后仍无法继续读下一层
        offset = self._clamped_int_argument(arguments.get("offset"), 0, 0, max(len(text), 0))  # 新增代码+极简工具面: 解析读取起点并限制在文件长度内；若没有这行代码，大文件局部读取不可控
        limit = self._clamped_int_argument(arguments.get("limit"), 8000, 1, 20000)  # 新增代码+极简工具面: 解析最多返回字符数；若没有这行代码，read 可能返回过长内容
        selected_text = text[offset : offset + limit]  # 新增代码+极简工具面: 截取本次要返回的文本片段；若没有这行代码，offset/limit 参数不会生效
        if offset + limit < len(text):  # 新增代码+极简工具面: 判断文件后面是否还有未返回内容；若没有这行代码，模型不知道读取结果被截断
            return selected_text + f"\n...[read 截断：offset={offset} limit={limit} total_chars={len(text)}]..."  # 新增代码+极简工具面: 返回片段和截断提示；若没有这行代码，模型可能误把片段当全文
        return selected_text  # 新增代码+极简工具面: 返回完整或尾段文本；若没有这行代码，read 工具没有成功输出

    def _write_atom(self, arguments: dict[str, Any]) -> str:  # 新增代码+极简工具面: 实现 write 原子工具；若没有这行代码，首轮 write schema 只能被看见但无法执行
        output = self._write_file(arguments)  # 新增代码+极简工具面: 复用既有安全写文件逻辑和权限确认；若没有这行代码，write 会绕过已有路径检查和确认流程
        return rewrite_tool_result_prefix(output, old_prefix="write_file", new_prefix="write")  # 修改代码+AtomToolsSplit: 委托 atom_tools 把旧工具名前缀改成原子工具名；若没有这行代码，模型会看到与调用名不一致的结果

    def _edit_atom(self, arguments: dict[str, Any]) -> str:  # 新增代码+极简工具面: 实现 edit 原子工具；若没有这行代码，首轮 edit schema 只能被看见但无法执行
        raw_path = str(arguments.get("path", "")).strip()  # 新增代码+极简工具面: 从参数读取并清理 path；若没有这行代码，edit 不知道要改哪个文件
        old_text = str(arguments.get("old_text", ""))  # 新增代码+极简工具面: 读取要匹配的旧文本；若没有这行代码，edit 无法定位修改位置
        new_text = str(arguments.get("new_text", ""))  # 新增代码+极简工具面: 读取替换后的新文本；若没有这行代码，edit 无法写入目标内容
        replace_all = bool(arguments.get("replace_all", False))  # 新增代码+极简工具面: 读取是否替换所有匹配；若没有这行代码，多处匹配无法由模型明确表达
        if not raw_path:  # 新增代码+极简工具面: 检查路径是否为空；若没有这行代码，空路径会进入路径解析产生模糊错误
            return "edit 失败：缺少 path 参数。"  # 新增代码+极简工具面: 返回清楚缺参错误；若没有这行代码，模型难以修正调用
        if old_text == "":  # 新增代码+极简工具面: 检查旧文本是否为空；若没有这行代码，空字符串替换会在每个字符间插入新内容
            return "edit 失败：old_text 不能为空。"  # 新增代码+极简工具面: 返回空旧文本错误；若没有这行代码，可能造成灾难性全文修改
        path = self._resolve_workspace_path(raw_path)  # 新增代码+极简工具面: 把相对路径安全解析到工作区内；若没有这行代码，edit 可能越界修改文件
        if path is None:  # 新增代码+极简工具面: 检查路径是否越过工作区边界；若没有这行代码，用户项目外文件可能被修改
            return "edit 失败：只能编辑 learning_agent 工作区内的文件。"  # 新增代码+极简工具面: 返回安全边界错误；若没有这行代码，模型不知道失败原因
        if not path.exists():  # 新增代码+极简工具面: 检查文件是否存在；若没有这行代码，后续读取会抛出 FileNotFoundError
            return f"edit 失败：文件不存在：{path}"  # 新增代码+极简工具面: 返回包含路径的不存在提示；若没有这行代码，模型无法定位错路径
        if path.is_dir():  # 新增代码+极简工具面: 检查路径是否是目录；若没有这行代码，目录读取会抛出不清晰异常
            return f"edit 失败：不能把目录当文件编辑：{path}"  # 新增代码+极简工具面: 返回目录错误；若没有这行代码，模型可能继续用 edit 编辑目录
        text = path.read_text(encoding="utf-8", errors="replace")  # 新增代码+极简工具面: 读取当前文件正文；若没有这行代码，edit 无法判断旧文本是否存在
        match_count = text.count(old_text)  # 新增代码+极简工具面: 统计旧文本匹配次数；若没有这行代码，无法保护默认唯一替换语义
        if match_count == 0:  # 新增代码+极简工具面: 检查旧文本是否存在；若没有这行代码，替换失败会被误报成功
            return "edit 失败：没有找到 old_text。"  # 新增代码+极简工具面: 返回未找到提示；若没有这行代码，模型不知道应重新读取文件确认原文
        if match_count > 1 and not replace_all:  # 新增代码+极简工具面: 默认拒绝多处匹配；若没有这行代码，定点编辑可能误改多个位置
            return f"edit 失败：old_text 出现 {match_count} 次；请提供更精确片段或设置 replace_all=true。"  # 新增代码+极简工具面: 返回多匹配修正建议；若没有这行代码，模型难以安全继续
        action = f"编辑文件：{path}，替换次数：{match_count if replace_all else 1}"  # 新增代码+极简工具面: 准备权限确认说明；若没有这行代码，用户无法核对 edit 的副作用范围
        if not self.ask_permission(action):  # 新增代码+极简工具面: 请求用户确认编辑操作；若没有这行代码，edit 会绕过写入权限边界
            return f"用户拒绝了操作：{action}"  # 新增代码+极简工具面: 返回用户拒绝结果；若没有这行代码，模型可能误以为编辑已经完成
        updated_text = text.replace(old_text, new_text) if replace_all else text.replace(old_text, new_text, 1)  # 新增代码+极简工具面: 根据 replace_all 执行替换；若没有这行代码，edit 不会产生新文件内容
        path.write_text(updated_text, encoding="utf-8")  # 新增代码+极简工具面: 把替换后的文本写回文件；若没有这行代码，修改只存在内存里
        return f"edit 成功：已更新 {path}，替换次数：{match_count if replace_all else 1}"  # 新增代码+极简工具面: 返回成功摘要；若没有这行代码，模型无法确认编辑结果

    def _bash_atom(self, arguments: dict[str, Any]) -> str:  # 修改代码+DesktopTaskPolicy：函数段开始，实现 bash 原子工具并在桌面任务 active 时先检查脚本制品策略；如果没有这段函数，首轮 bash schema 只能被看见但无法执行，作者意图是让命令执行前先经过 Task 3 GUI 路线门禁，本函数与 desktop_task_policy 配合到 return 结束。
        command = str(arguments.get("command", "")).strip()  # 新增代码+极简工具面: 从参数读取并清理命令文本；若没有这行代码，bash 不知道要执行什么命令
        if not command:  # 新增代码+极简工具面: 检查命令是否为空；若没有这行代码，空命令会产生模糊 shell 行为
            return "bash 失败：缺少 command 参数。"  # 新增代码+极简工具面: 返回清楚缺参错误；若没有这行代码，模型难以修正调用
        desktop_task_context = getattr(self, "desktop_task_context", {})  # 新增代码+DesktopTaskPolicy：读取当前 agent 的桌面任务上下文；如果没有这一行，轻量测试对象或旧实例无法被安全识别为 active/inactive。
        desktop_task_active = bool(desktop_task_context.get("active", False)) if isinstance(desktop_task_context, dict) else False  # 新增代码+DesktopTaskPolicy：只从字典上下文读取 active 布尔值；如果没有这一行，异常上下文形状可能让 bash 工具崩溃。
        if desktop_task_active:  # 新增代码+DesktopTaskPolicy：只在桌面任务激活时启用命令策略；如果没有这一行，普通开发命令也会承担额外拦截逻辑。
            try:  # 新增代码+DesktopTaskPolicy：优先按包运行模式导入策略函数；如果没有这一行，start_oauth_agent.bat 和 unittest 的导入环境无法兼容处理。
                from learning_agent.computer_use.desktop_task_policy import evaluate_desktop_bash_command  # 新增代码+DesktopTaskPolicy：导入桌面任务 bash 策略函数；如果没有这一行，_bash_atom 无法在权限请求前识别脚本最终制品路线。
            except ModuleNotFoundError as error:  # 新增代码+DesktopTaskPolicy：兼容直接脚本运行时 learning_agent 包路径不可用的情况；如果没有这一行，脚本模式可能因为包名前缀失败。
                if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.desktop_task_policy"}:  # 新增代码+DesktopTaskPolicy：只对目标包路径缺失做 fallback；如果没有这一行，策略模块内部真实导入错误会被误吞。
                    raise  # 新增代码+DesktopTaskPolicy：重新抛出非目标导入错误；如果没有这一行，排查策略模块内部 bug 会很困难。
                from computer_use.desktop_task_policy import evaluate_desktop_bash_command  # 新增代码+DesktopTaskPolicy：脚本模式下从本地 computer_use 包导入策略函数；如果没有这一行，bat 入口可能无法加载 Task 3 策略。
            desktop_policy_result = evaluate_desktop_bash_command(command=command, desktop_task_active=desktop_task_active)  # 新增代码+DesktopTaskPolicy：在 cwd 解析、权限请求和执行命令前评估策略；如果没有这一行，危险命令会继续走到真实 shell 流程。
            if not bool(desktop_policy_result.get("allowed", False)):  # 新增代码+DesktopTaskPolicy：检查策略是否拒绝当前命令；如果没有这一行，命中禁止脚本制品路线也不会被拦住。
                desktop_policy_text = json.dumps(desktop_policy_result, ensure_ascii=False, indent=2)  # 新增代码+DesktopTaskPolicy：把结构化策略结果转成中文友好的 JSON；如果没有这一行，拒绝文本缺少可复盘细节。
                return f"bash 拒绝：{desktop_policy_result.get('decision', 'desktop_task_requires_gui_route')}\n原因：{desktop_policy_result.get('reason', '')}\n策略详情：{desktop_policy_text}"  # 新增代码+DesktopTaskPolicy：直接返回清晰拒绝，不请求权限也不执行命令；如果没有这一行，脚本生成最终图片制品路线仍可能进入真实终端。
        raw_cwd = str(arguments.get("cwd", "") or "").strip()  # 新增代码+极简工具面: 读取可选工作目录；若没有这行代码，模型无法指定子目录执行命令
        cwd_path = self._resolve_workspace_path(raw_cwd) if raw_cwd else self.workspace  # 新增代码+极简工具面: 将 cwd 限制在工作区内或默认根目录；若没有这行代码，命令可能在未知目录执行
        if cwd_path is None:  # 新增代码+极简工具面: 检查 cwd 是否越界；若没有这行代码，bash 可能在工作区外执行命令
            return "bash 失败：cwd 必须位于 learning_agent 工作区内。"  # 新增代码+极简工具面: 返回安全边界错误；若没有这行代码，模型不知道为什么命令没执行
        if not cwd_path.exists() or not cwd_path.is_dir():  # 新增代码+极简工具面: 检查执行目录是否存在且为目录；若没有这行代码，subprocess 会抛出不清晰异常
            return f"bash 失败：cwd 不存在或不是目录：{cwd_path}"  # 新增代码+极简工具面: 返回清楚 cwd 错误；若没有这行代码，模型无法修正路径
        timeout_seconds = self._clamped_int_argument(arguments.get("timeout_seconds"), 60, 1, 300)  # 新增代码+极简工具面: 解析命令超时秒数；若没有这行代码，长命令可能无限等待
        max_output_chars = self._clamped_int_argument(arguments.get("max_output_chars"), 8000, 1000, 20000)  # 新增代码+极简工具面: 解析最大输出字符数；若没有这行代码，命令输出可能撑爆上下文
        action = f"执行命令：{command}\n工作目录：{cwd_path}"  # 新增代码+极简工具面: 准备权限确认说明；若没有这行代码，用户无法核对命令和执行目录
        if not self.ask_permission(action):  # 新增代码+极简工具面: 请求用户确认命令执行；若没有这行代码，bash 会绕过命令权限边界
            return f"用户拒绝了操作：{action}"  # 新增代码+极简工具面: 返回用户拒绝结果；若没有这行代码，模型可能误以为命令已经执行
        command_args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command] if os.name == "nt" else ["bash", "-lc", command]  # 新增代码+极简工具面: 根据系统选择命令承载程序；若没有这行代码，Windows 和类 Unix 环境无法统一执行 bash 原子工具
        try:  # 新增代码+极简工具面: 捕获命令超时、shell 缺失或执行异常；若没有这行代码，bash 工具失败会冒出 Python traceback
            result = subprocess.run(command_args, cwd=cwd_path, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_seconds)  # 新增代码+极简工具面: 执行命令并捕获 stdout/stderr；若没有这行代码，bash 不会真正运行命令
        except subprocess.TimeoutExpired as error:  # 新增代码+极简工具面: 处理命令超过 timeout 的情况；若没有这行代码，超时命令会中断工具循环
            stdout_text = (error.stdout or "") if isinstance(error.stdout, str) else ""  # 新增代码+极简工具面: 提取超时前 stdout 文本；若没有这行代码，用户看不到命令已产生的部分输出
            stderr_text = (error.stderr or "") if isinstance(error.stderr, str) else ""  # 新增代码+极简工具面: 提取超时前 stderr 文本；若没有这行代码，用户看不到命令已产生的错误输出
            combined_text = f"bash 失败：命令超过 {timeout_seconds} 秒已停止。\nstdout:\n{stdout_text}\nstderr:\n{stderr_text}"  # 新增代码+极简工具面: 构造超时结果；若没有这行代码，模型不知道命令为何没有完成
            return combined_text[:max_output_chars]  # 新增代码+极简工具面: 截断超时输出；若没有这行代码，部分输出仍可能过长
        except OSError as error:  # 新增代码+极简工具面: 处理 shell 程序缺失或启动失败；若没有这行代码，环境问题会变成 traceback
            return f"bash 失败：无法启动命令执行器：{error}"  # 新增代码+极简工具面: 返回清楚环境错误；若没有这行代码，用户不知道是 shell 不可用
        combined_text = f"bash 成功：exit_code={result.returncode}\nstdout:\n{result.stdout or ''}\nstderr:\n{result.stderr or ''}"  # 新增代码+极简工具面: 合并退出码和输出；若没有这行代码，模型无法根据命令结果继续推理
        if len(combined_text) > max_output_chars:  # 新增代码+极简工具面: 判断命令输出是否超过返回上限；若没有这行代码，长输出会撑爆上下文
            return combined_text[:max_output_chars] + f"\n...[bash 输出过长，已截断，原始字符数={len(combined_text)}]..."  # 新增代码+极简工具面: 返回截断输出和原始长度；若没有这行代码，模型会误以为看到了完整输出
        return combined_text  # 新增代码+极简工具面: 返回完整命令结果；若没有这行代码，bash 工具没有成功输出

    def _computer_status(self, arguments: dict[str, Any]) -> str:  # 新增代码+OSComputerUse: 实现 computer_status 只读工具；若没有这段代码，模型无法查看 OS 桌面控制后端状态。
        status = self.computer_use_controller.status()  # 新增代码+OSComputerUse: 从控制器读取状态；若没有这行代码，状态工具无法反映后端可用性。
        self._record_observation("computer_use_status", status)  # 新增代码+OSComputerUse: 把状态查询写入观察流；若没有这行代码，Phase 7 排查无法看到模型是否检查过桌面能力。
        return json.dumps(status, ensure_ascii=False, indent=2)  # 新增代码+OSComputerUse: 返回中文友好的 JSON；若没有这行代码，模型和用户难以读取结构化状态。

    def _computer_observe(self, arguments: dict[str, Any]) -> str:  # 新增代码+Phase27ComputerUse: 实现 computer_observe 只读工具；如果没有这段代码，模型无法在动作前列出窗口或读取窗口状态。
        action_name = str(arguments.get("action", "")).strip()  # 新增代码+Phase27ComputerUse: 读取观察动作名用于审计；如果没有这行代码，observation 里看不到模型观察了什么。
        result = self.computer_use_controller.observe(arguments)  # 新增代码+Phase27ComputerUse: 通过控制器执行只读观察；如果没有这行代码，observe 不会经过统一动作枚举和审计。
        self._record_observation("computer_use_observe", {"action": action_name, "ok": result.ok, "message": result.message, "data": result.data})  # 新增代码+Phase27ComputerUse: 记录观察结果；如果没有这行代码，窗口发现和状态读取无法在运行日志里复盘。
        self._record_computer_use_image_artifacts(result.data, "computer_observe")  # 新增代码+Phase41WindowsImageResults: 登记 observe 结果中的截图 artifact；如果没有这行代码，模型看到图片块但会话产物列表会丢失截图。
        return result.to_text("computer_observe")  # 新增代码+Phase27ComputerUse: 返回带正确工具名的可读文本；如果没有这行代码，模型无法读取只读观察结果。

    def _computer_use_full_mode_requires_model_visible_observation(self, action_name: str) -> bool:  # 新增代码+ObserveBeforeActionGate: 函数段开始，判断 full GUI 任务的鼠标键盘动作是否必须先有模型可见截图；如果没有这段函数，提示词约束无法变成硬门禁。
        desktop_task_context = getattr(self, "desktop_task_context", {})  # 新增代码+ObserveBeforeActionGate: 读取当前桌面任务上下文；如果没有这行代码，普通工具调用和 full GUI 任务无法区分。
        if not isinstance(desktop_task_context, dict):  # 新增代码+ObserveBeforeActionGate: 防御异常上下文形状；如果没有这行代码，外部状态污染可能导致门禁崩溃。
            return False  # 新增代码+ObserveBeforeActionGate: 上下文异常时不启用本门禁；如果没有这行代码，普通任务可能被错误拦截。
        if not bool(desktop_task_context.get("active", False)):  # 新增代码+ObserveBeforeActionGate: 只在 /computer use --full 激活的桌面任务中启用；如果没有这行代码，兼容工具测试和普通调用会被过度限制。
            return False  # 新增代码+ObserveBeforeActionGate: 非 full 桌面任务不强制截图观察；如果没有这行代码，旧接口兼容性会被破坏。
        if not bool(desktop_task_context.get("requires_gui_actions", False)):  # 新增代码+ObserveBeforeActionGate: 只对确实需要 GUI 动作的任务启用；如果没有这行代码，状态查询类任务也可能被误拦。
            return False  # 新增代码+ObserveBeforeActionGate: 非 GUI 动作任务不拦截；如果没有这行代码，解释类任务可能无法继续。
        return action_name in {"move_mouse", "click", "double_click", "drag_path", "type_text", "press_key", "scroll"}  # 新增代码+ObserveBeforeActionGate: 鼠标键盘类动作必须先看屏幕，截图类动作不拦；如果没有这行代码，盲点、盲打和盲拖仍可能发生。
    # 新增代码+ObserveBeforeActionGate: 函数段结束，_computer_use_full_mode_requires_model_visible_observation 到此结束；如果没有这个边界说明，用户不容易看出门禁适用范围。

    def _computer_use_data_has_model_visible_image(self, data: Any) -> bool:  # 新增代码+ComputerUseActionVisualEvidence：函数段开始，统一判断 Computer Use data 是否含有模型可见截图；如果没有这段函数，observe 和 action 的截图证据会继续用两套标准导致真实终端误判。
        if not isinstance(data, dict):  # 新增代码+ComputerUseActionVisualEvidence：先确认 data 是字典；如果没有这行代码，字符串或 None 会触发属性错误。
            return False  # 新增代码+ComputerUseActionVisualEvidence：异常 data 不能当作视觉证据；如果没有这行代码，坏工具结果可能误放行真实动作。
        state = data.get("state", {}) if isinstance(data.get("state", {}), dict) else {}  # 修改代码+ComputerUseActionVisualEvidence：读取顶层窗口状态；如果没有这行代码，只在 state 内暴露截图字段的观察会被误判无图。
        image_result_count = int(data.get("image_result_count", 0) or state.get("image_result_count", 0) or 0)  # 修改代码+ComputerUseActionVisualEvidence：统计顶层模型可见图片块数量；如果没有这行代码，只有截图路径没有图片块的结果会被误当成模型已看见。
        screenshot_captured = bool(data.get("screenshot_captured", False) or state.get("screenshot_captured", False))  # 修改代码+ComputerUseActionVisualEvidence：检查顶层真实截图是否捕获；如果没有这行代码，空图片计数异常可能误放行。
        if image_result_count > 0 and screenshot_captured:  # 修改代码+ComputerUseActionVisualEvidence：顶层同时有截图和图片块时算模型可见；如果没有这行代码，普通 computer_observe 成功结果会失效。
            return True  # 修改代码+ComputerUseActionVisualEvidence：找到顶层有效视觉证据后返回成功；如果没有这行代码，已经看过屏幕的动作会被一直拦住。
        for evidence_key in ("before_evidence", "after_evidence"):  # 新增代码+ComputerUseActionVisualEvidence：继续检查真实动作自带的前后截图证据；如果没有这行代码，真实 SendInput 动作回灌的截图会被完成门忽略。
            evidence = data.get(evidence_key, {})  # 新增代码+ComputerUseActionVisualEvidence：读取某个动作证据块；如果没有这行代码，无法检查 before_evidence 或 after_evidence。
            if not isinstance(evidence, dict):  # 新增代码+ComputerUseActionVisualEvidence：防御异常证据形状；如果没有这行代码，字符串证据会导致属性错误。
                continue  # 新增代码+ComputerUseActionVisualEvidence：跳过异常证据块；如果没有这行代码，坏证据会中断整个主循环。
            evidence_state = evidence.get("state", {}) if isinstance(evidence.get("state", {}), dict) else {}  # 新增代码+ComputerUseActionVisualEvidence：读取证据内嵌窗口状态；如果没有这行代码，真实截图字段藏在 state 内时会被漏掉。
            evidence_image_count = int(evidence.get("image_result_count", 0) or evidence_state.get("image_result_count", 0) or 0)  # 新增代码+ComputerUseActionVisualEvidence：统计证据块里可回灌模型的图片数量；如果没有这行代码，动作截图只会成为文件路径而不是可见证据。
            evidence_captured = bool(evidence.get("captured", False) or evidence.get("screenshot_captured", False) or evidence_state.get("screenshot_captured", False))  # 新增代码+ComputerUseActionVisualEvidence：确认动作证据确实捕获截图；如果没有这行代码，只有结构壳子的证据会误放行。
            if evidence_image_count > 0 and evidence_captured:  # 新增代码+ComputerUseActionVisualEvidence：证据块同时有截图和图片块才算模型可见；如果没有这行代码，真实终端 action.before_evidence 不能推进 observe-plan-act loop。
                return True  # 新增代码+ComputerUseActionVisualEvidence：找到动作内嵌视觉证据后返回成功；如果没有这行代码，完成门会继续等一个已经不必要的 observe。
        return False  # 新增代码+ComputerUseActionVisualEvidence：没有任何有效截图证据时返回失败；如果没有这行代码，函数缺少明确否定结果。
    # 新增代码+ComputerUseActionVisualEvidence：函数段结束，_computer_use_data_has_model_visible_image 到此结束；如果没有这个边界说明，用户不容易看出截图证据统一判断范围。

    def _computer_use_has_recent_model_visible_observation(self) -> bool:  # 修改代码+ComputerUseActionVisualEvidence：函数段开始，检查主循环最近是否得到可回灌模型的真实截图证据；如果没有这段函数，动作层无法知道模型是否真正看过屏幕。
        for event in reversed(self.observation_events[-80:]):  # 修改代码+ComputerUseActionVisualEvidence：从最近事件倒序查找并扩到 80 条；如果没有这行代码，多轮真实绘图会把最近截图证据挤出窗口。
            if event.get("kind") not in {"computer_use_observe", "computer_use_action"}:  # 修改代码+ComputerUseActionVisualEvidence：同时接受观察事件和带截图的动作事件；如果没有这行代码，动作自带截图不会被主循环承认。
                continue  # 修改代码+ComputerUseActionVisualEvidence：跳过非桌面视觉相关事件；如果没有这行代码，后续字段读取会混入无关结构。
            payload = event.get("payload", {})  # 修改代码+ComputerUseActionVisualEvidence：读取事件载荷；如果没有这行代码，无法判断工具是否成功和是否有图。
            if not isinstance(payload, dict) or not bool(payload.get("ok", False)):  # 修改代码+ComputerUseActionVisualEvidence：只接受成功工具结果；如果没有这行代码，失败 observe/action 也可能放行动作。
                continue  # 修改代码+ComputerUseActionVisualEvidence：跳过失败或异常载荷；如果没有这行代码，坏事件会污染门禁判断。
            if self._computer_use_data_has_model_visible_image(payload.get("data", {})):  # 新增代码+ComputerUseActionVisualEvidence：用统一 helper 判断 data 或动作证据是否有模型可见截图；如果没有这行代码，真实 before_evidence 无法解锁完成门。
                return True  # 修改代码+ComputerUseActionVisualEvidence：找到有效视觉证据后放行动作或完成门；如果没有这行代码，已经看过屏幕的正常动作会被一直拦住。
        return False  # 修改代码+ComputerUseActionVisualEvidence：最近没有有效截图证据时拒绝动作；如果没有这行代码，函数缺少明确失败结果。
    # 修改代码+ComputerUseActionVisualEvidence：函数段结束，_computer_use_has_recent_model_visible_observation 到此结束；如果没有这个边界说明，用户不容易看出“看过屏幕”的判定标准。

    def _computer_use_observe_before_action_rejection(self, action_name: str, arguments: dict[str, Any]) -> str | None:  # 新增代码+ObserveBeforeActionGate: 函数段开始，在 full 模式动作前生成先观察拒绝结果；如果没有这段函数，盲动拦截会散落在 _computer_action 主流程里。
        if not self._computer_use_full_mode_requires_model_visible_observation(action_name):  # 新增代码+ObserveBeforeActionGate: 先判断当前动作是否需要观察门禁；如果没有这行代码，所有动作都会被不必要检查。
            return None  # 新增代码+ObserveBeforeActionGate: 不需要门禁时返回 None；如果没有这行代码，调用方无法区分放行和拒绝。
        if self._computer_use_has_recent_model_visible_observation():  # 新增代码+ObserveBeforeActionGate: 已经有模型可见截图观察时放行；如果没有这行代码，正常 observe-plan-act 会被卡死。
            return None  # 新增代码+ObserveBeforeActionGate: 返回 None 表示不拦截；如果没有这行代码，调用方无法继续权限和 controller 路径。
        report = {"ok": False, "decision": "observe_before_action_required", "action": action_name, "reason": "full 模式下鼠标键盘动作前必须先让模型看到真实截图观察。", "next_tools": ["computer_observe"], "required_observe_action": "get_window_state", "argument_preview": {"has_window": isinstance(arguments.get("window"), dict), "has_coordinates": "x" in arguments or "y" in arguments, "has_points": bool(arguments.get("points"))}}  # 新增代码+ObserveBeforeActionGate: 构造模型可读纠偏报告；如果没有这行代码，模型不知道该先调用哪个观察工具。
        self._record_observation("computer_use_observe_before_action_required", report)  # 新增代码+ObserveBeforeActionGate: 把盲动拦截写入观察日志；如果没有这行代码，真实终端排查不知道为何没有执行鼠标键盘。
        return "Computer Use full 模式已拒绝盲目桌面动作：请先观察屏幕和目标窗口，再执行鼠标键盘动作。\n请先调用 computer_observe，action=get_window_state，并使用返回的截图继续规划。\n" + json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+ObserveBeforeActionGate: 返回中文说明和结构化 JSON 给模型自我纠正；如果没有这行代码，模型可能继续重复盲动。
    # 新增代码+ObserveBeforeActionGate: 函数段结束，_computer_use_observe_before_action_rejection 到此结束；如果没有这个边界说明，用户不容易看出拒绝结果的范围。

    def _computer_use_full_mode_requires_agent_owned_launch(self, action_name: str) -> bool:  # 新增代码+AgentOwnedLaunchGate: 函数段开始，判断 full 本机应用任务的鼠标键盘动作是否必须先由 launch_app 取得 agent-owned 窗口；如果没有这段函数，模型看过旧窗口截图后仍可能直接操作用户旧软件。
        desktop_task_context = getattr(self, "desktop_task_context", {})  # 新增代码+AgentOwnedLaunchGate: 读取当前桌面任务上下文；如果没有这行代码，门禁无法知道本轮是不是 /computer use --full 任务。
        if not isinstance(desktop_task_context, dict):  # 新增代码+AgentOwnedLaunchGate: 防御异常上下文类型；如果没有这行代码，外部状态污染可能让门禁抛异常。
            return False  # 新增代码+AgentOwnedLaunchGate: 上下文异常时不启用本门禁；如果没有这行代码，普通工具调用可能被误拦。
        if not bool(desktop_task_context.get("active", False)):  # 新增代码+AgentOwnedLaunchGate: 只在 full 桌面任务激活时启用；如果没有这行代码，普通 computer_action 单测和兼容旧调用会被过度限制。
            return False  # 新增代码+AgentOwnedLaunchGate: 非 full 桌面任务不要求先 launch_app；如果没有这行代码，旧协议无法继续兼容。
        if not bool(desktop_task_context.get("requires_gui_actions", False)):  # 新增代码+AgentOwnedLaunchGate: 只对需要真实 GUI 动作的任务启用；如果没有这行代码，状态查询类桌面任务也可能被误拦。
            return False  # 新增代码+AgentOwnedLaunchGate: 非 GUI 动作任务不要求启动软件；如果没有这行代码，解释类任务会被卡住。
        if not str(desktop_task_context.get("target_app_hint", "") or "").strip():  # 新增代码+AgentOwnedLaunchGate: 只在自然语言识别到目标本机应用时启用；如果没有这行代码，纯鼠标坐标实验可能被错误要求启动应用。
            return False  # 新增代码+AgentOwnedLaunchGate: 没有目标应用线索时保持旧路径兼容；如果没有这行代码，开放式桌面任务会被过早收窄。
        return action_name in {"move_mouse", "click", "double_click", "drag_path", "type_text", "press_key", "scroll"}  # 新增代码+AgentOwnedLaunchGate: 鼠标键盘动作必须等 launch_app 成功，截图和 launch_app 本身不拦；如果没有这行代码，未启动软件前仍可能真实点击旧窗口。
    # 新增代码+AgentOwnedLaunchGate: 函数段结束，_computer_use_full_mode_requires_agent_owned_launch 到此结束；如果没有这个边界说明，用户不容易看出先启动门禁适用范围。

    def _computer_use_has_agent_owned_launch_target(self) -> bool:  # 新增代码+AgentOwnedLaunchGate: 函数段开始，检查 controller 是否已经保存 launch_app 返回的 agent-owned 目标窗口；如果没有这段函数，动作层无法知道是否真正打开并绑定了软件。
        controller = getattr(self, "computer_use_controller", None)  # 新增代码+AgentOwnedLaunchGate: 读取当前 Computer Use controller；如果没有这行代码，门禁会强依赖固定属性导致测试注入困难。
        active_window = getattr(controller, "active_agent_owned_target_window", {}) if controller is not None else {}  # 新增代码+AgentOwnedLaunchGate: 读取 controller 中 launch_app 成功后保存的窗口；如果没有这行代码，无法区分用户旧窗口和 agent 自己打开的窗口。
        return isinstance(active_window, dict) and bool(active_window.get("app_id")) and bool(active_window.get("window_id"))  # 新增代码+AgentOwnedLaunchGate: 只有同时有 app_id 和 window_id 才算可操作目标；如果没有这行代码，空字典或半截窗口可能误放行。
    # 新增代码+AgentOwnedLaunchGate: 函数段结束，_computer_use_has_agent_owned_launch_target 到此结束；如果没有这个边界说明，用户不容易看出 agent-owned 判断标准。

    def _computer_use_agent_owned_launch_rejection(self, action_name: str, arguments: dict[str, Any]) -> str | None:  # 新增代码+AgentOwnedLaunchGate: 函数段开始，在 full 本机应用任务的鼠标键盘动作前强制先 launch_app；如果没有这段函数，模型可能在未打开软件前操作旧窗口。
        if not self._computer_use_full_mode_requires_agent_owned_launch(action_name):  # 新增代码+AgentOwnedLaunchGate: 先判断本动作是否需要 agent-owned 启动门禁；如果没有这行代码，所有 Computer Use 动作都会被不必要检查。
            return None  # 新增代码+AgentOwnedLaunchGate: 不需要门禁时返回 None；如果没有这行代码，调用方无法继续正常路径。
        if self._computer_use_has_agent_owned_launch_target():  # 新增代码+AgentOwnedLaunchGate: 已经有 launch_app 绑定窗口时放行；如果没有这行代码，成功打开软件后仍无法操作。
            return None  # 新增代码+AgentOwnedLaunchGate: 返回 None 表示继续权限和 controller 路径；如果没有这行代码，正常动作会被误拒绝。
        desktop_task_context = getattr(self, "desktop_task_context", {}) if isinstance(getattr(self, "desktop_task_context", {}), dict) else {}  # 新增代码+AgentOwnedLaunchGate: 读取脱敏任务上下文用于提示目标应用；如果没有这行代码，拒绝信息缺少该启动哪个软件。
        target_app_hint = str(desktop_task_context.get("target_app_hint", "") or "").strip()  # 新增代码+AgentOwnedLaunchGate: 提取目标应用提示；如果没有这行代码，模型不知道 launch_app 应传什么 app_name。
        report = {"ok": False, "decision": "agent_owned_launch_required", "action": action_name, "reason": "full 本机应用任务必须先用 launch_app 打开并绑定 agent-owned 目标窗口，不能直接操作旧窗口。", "next_tools": ["computer_action"], "required_action": "launch_app", "target_app_hint": target_app_hint, "argument_preview": {"has_window": isinstance(arguments.get("window"), dict), "has_coordinates": "x" in arguments or "y" in arguments, "has_points": bool(arguments.get("points"))}}  # 新增代码+AgentOwnedLaunchGate: 构造模型可读纠偏报告；如果没有这行代码，模型不知道应先打开软件而不是继续点击。
        self._record_observation("computer_use_agent_owned_launch_required", report)  # 新增代码+AgentOwnedLaunchGate: 把先启动门禁写入观察日志；如果没有这行代码，真实终端排查不知道为什么没有执行鼠标键盘。
        return "Computer Use full 模式已拒绝操作非 agent-owned 目标窗口：请先调用 computer_action，action=launch_app，传入 app_name/target_app 打开并绑定目标软件。\n" + json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+AgentOwnedLaunchGate: 返回中文说明和 JSON 给模型纠偏；如果没有这行代码，模型可能继续对旧窗口做动作。
    # 新增代码+AgentOwnedLaunchGate: 函数段结束，_computer_use_agent_owned_launch_rejection 到此结束；如果没有这个边界说明，用户不容易看出启动门禁拒绝范围。

    def _computer_use_full_recent_events_after_mode_open(self) -> list[dict[str, Any]]:  # 新增代码+ComputerUseCompletionGate: 函数段开始，取出最近一次 full mode 打开后的观察事件；如果没有这段函数，完成门可能把旧任务的绘图动作算进本轮。
        start_index = 0  # 新增代码+ComputerUseCompletionGate: 默认从全部观察事件开始统计；如果没有这行代码，没有 mode 事件的单元测试会拿不到数据。
        for index, event in enumerate(self.observation_events):  # 新增代码+ComputerUseCompletionGate: 遍历观察事件寻找最近的 mode 事件；如果没有这行代码，无法切分当前 full 会话。
            if event.get("kind") == "computer_use_mode":  # 新增代码+ComputerUseCompletionGate: 只把 full mode 状态事件当作会话边界；如果没有这行代码，普通工具事件会误重置统计窗口。
                start_index = index + 1  # 新增代码+ComputerUseCompletionGate: 从 mode 事件之后开始统计动作；如果没有这行代码，本轮之前的动作可能污染完成判断。
        return list(self.observation_events[start_index:])  # 新增代码+ComputerUseCompletionGate: 返回当前 full 会话内的观察事件副本；如果没有这行代码，调用方无法安全遍历。
    # 新增代码+ComputerUseCompletionGate: 函数段结束，_computer_use_full_recent_events_after_mode_open 到此结束；如果没有这个边界说明，读者不容易看出事件窗口范围。

    def _computer_use_full_successful_real_action_count(self) -> int:  # 新增代码+ComputerUseCompletionGate: 函数段开始，统计当前 full 会话里已经成功执行的真实桌面动作数量；如果没有这段函数，模型可能无限重复 drag_path。
        count = 0  # 新增代码+ComputerUseCompletionGate: 初始化成功动作计数；如果没有这行代码，函数无法累加结果。
        for event in self._computer_use_full_recent_events_after_mode_open()[-80:]:  # 新增代码+ComputerUseCompletionGate: 只看最近 80 条事件避免长期会话过慢；如果没有这行代码，长任务日志越积越慢。
            if event.get("kind") != "computer_use_action":  # 新增代码+ComputerUseCompletionGate: 只统计桌面动作事件；如果没有这行代码，observe 或 status 会被误算成动作。
                continue  # 新增代码+ComputerUseCompletionGate: 跳过非动作事件；如果没有这行代码，后续读取 payload 可能混入无关字段。
            payload = event.get("payload", {})  # 新增代码+ComputerUseCompletionGate: 读取动作事件载荷；如果没有这行代码，无法判断动作是否成功。
            if not isinstance(payload, dict) or not bool(payload.get("ok", False)):  # 新增代码+ComputerUseCompletionGate: 只统计成功动作；如果没有这行代码，失败或拒绝也会推进完成门。
                continue  # 新增代码+ComputerUseCompletionGate: 跳过失败动作；如果没有这行代码，模型可能在没画出东西时被要求结束。
            data = payload.get("data", {})  # 新增代码+ComputerUseCompletionGate: 读取 controller 返回数据；如果没有这行代码，无法读取底层输入数量。
            if not isinstance(data, dict):  # 新增代码+ComputerUseCompletionGate: 防御异常 data 类型；如果没有这行代码，字符串结果会导致 get 调用异常。
                continue  # 新增代码+ComputerUseCompletionGate: 跳过异常数据；如果没有这行代码，完成门可能崩溃。
            dispatch = data.get("dispatch", {}) if isinstance(data.get("dispatch", {}), dict) else {}  # 新增代码+ComputerUseCompletionGate: 读取 SendInput 调度摘要；如果没有这行代码，无法区分真实输入和空动作。
            low_level_count = int(dispatch.get("low_level_event_count", data.get("low_level_event_count", 0)) or 0)  # 新增代码+ComputerUseCompletionGate: 读取底层输入事件数量；如果没有这行代码，只有表面成功但没有输入的动作也会被算入。
            if low_level_count > 0 or bool(data.get("real_input_enabled", False)):  # 新增代码+ComputerUseCompletionGate: 真实动作至少要有底层事件或真实输入标记；如果没有这行代码，纯状态报告可能被误算。
                count += 1  # 新增代码+ComputerUseCompletionGate: 成功真实动作计数加一；如果没有这行代码，完成门永远不会触发。
        return count  # 新增代码+ComputerUseCompletionGate: 返回成功动作数量；如果没有这行代码，调用方拿不到判断依据。
    # 新增代码+ComputerUseCompletionGate: 函数段结束，_computer_use_full_successful_real_action_count 到此结束；如果没有这个边界说明，读者不容易看出动作计数范围。

    def _computer_use_full_completion_signal_for_action(self, action_name: str, arguments: dict[str, Any]) -> str | None:  # 新增代码+ComputerUseCompletionGate: 函数段开始，在重复真实绘图前给模型最终回答信号；如果没有这段函数，真实 Paint 已经画出图后模型仍可能一直加笔。
        desktop_task_context = getattr(self, "desktop_task_context", {}) if isinstance(getattr(self, "desktop_task_context", {}), dict) else {}  # 新增代码+ComputerUseCompletionGate: 读取当前桌面任务上下文；如果没有这行代码，完成门无法区分 full 桌面任务和普通动作测试。
        if not bool(desktop_task_context.get("active", False)) or not bool(desktop_task_context.get("requires_gui_actions", False)):  # 新增代码+ComputerUseCompletionGate: 只在 full GUI 任务中启用；如果没有这行代码，普通 Computer Use 工具调用可能被错误截断。
            return None  # 新增代码+ComputerUseCompletionGate: 非 full GUI 任务不触发完成门；如果没有这行代码，调用方无法继续正常动作。
        if action_name not in {"drag_path", "click", "double_click", "type_text", "press_key", "scroll"}:  # 新增代码+ComputerUseCompletionGate: 只拦截会继续改变桌面的动作；如果没有这行代码，observe 和 launch_app 也可能被错误拦住。
            return None  # 新增代码+ComputerUseCompletionGate: 非改变类动作继续放行；如果没有这行代码，模型无法继续观察结果。
        if not self._computer_use_has_recent_model_visible_observation():  # 新增代码+ComputerUseCompletionGate: 必须已经有模型可见截图后才允许收敛；如果没有这行代码，模型可能没看过结果就被迫结束。
            return None  # 新增代码+ComputerUseCompletionGate: 没有截图证据时继续让模型观察或动作；如果没有这行代码，真实完成缺少视觉依据。
        action_count = self._computer_use_full_successful_real_action_count()  # 新增代码+ComputerUseCompletionGate: 统计本轮已经成功执行的真实动作；如果没有这行代码，完成门没有量化依据。
        threshold = 12  # 新增代码+ComputerUseCompletionGate: 设置较宽松的动作阈值避免过早停止复杂绘图；如果没有这行代码，完成门无法判断何时从执行转为最终回答。
        if action_count < threshold:  # 新增代码+ComputerUseCompletionGate: 未达到阈值时继续允许模型执行；如果没有这行代码，模型会被过早收敛。
            return None  # 新增代码+ComputerUseCompletionGate: 动作数量不足时不拦截；如果没有这行代码，普通三四笔绘图无法继续完善。
        report = {"ok": True, "decision": "computer_use_full_completion_ready", "action": action_name, "successful_real_action_count": action_count, "threshold": threshold, "reason": "已经有模型可见截图，并且真实桌面动作数量足够，继续加笔风险大于收益。", "next_step": "final_answer", "argument_preview": {"has_window": isinstance(arguments.get("window"), dict), "has_points": bool(arguments.get("points"))}}  # 新增代码+ComputerUseCompletionGate: 构造模型可读收敛报告；如果没有这行代码，模型不知道为什么不应继续动作。
        self._record_observation("computer_use_full_completion_ready", report)  # 新增代码+ComputerUseCompletionGate: 把完成信号写入观察日志；如果没有这行代码，真实终端失败时无法复盘为什么停止动作。
        return "Computer Use full completion gate: computer_use_full_completion_ready\n请直接输出最终回答，说明已经使用 computer_use 在真实本机应用中完成任务，并引用 screenshot、real_desktop_touched、low_level_event_count 等已有证据；不要继续调用鼠标键盘动作。\n" + json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+ComputerUseCompletionGate: 返回强收敛文本给模型；如果没有这行代码，模型可能继续请求 drag_path。
    # 新增代码+ComputerUseCompletionGate: 函数段结束，_computer_use_full_completion_signal_for_action 到此结束；如果没有这个边界说明，读者不容易看出完成门范围。

    def _computer_action(self, arguments: dict[str, Any]) -> str:  # 新增代码+OSComputerUse: 实现 computer_action 高风险动作工具；若没有这段代码，schema 中的桌面动作无法真正分发。
        action_name = str(arguments.get("action", "")).strip()  # 新增代码+OSComputerUse: 读取动作名用于权限说明；若没有这行代码，用户看不到要执行哪种桌面动作。
        observe_gate_rejection = self._computer_use_observe_before_action_rejection(action_name, arguments)  # 新增代码+ObserveBeforeActionGate: 在权限和后端前执行“先观察再动作”硬门禁；如果没有这行代码，模型看不到截图时仍可能盲目操作鼠标键盘。
        if observe_gate_rejection is not None:  # 新增代码+ObserveBeforeActionGate: 判断本次动作是否被观察门禁拒绝；如果没有这行代码，拒绝文本会被忽略继续执行。
            return observe_gate_rejection  # 新增代码+ObserveBeforeActionGate: 直接把纠偏结果返回模型且不弹权限不碰后端；如果没有这行代码，盲动仍会进入真实控制链。
        launch_gate_rejection = self._computer_use_agent_owned_launch_rejection(action_name, arguments)  # 新增代码+AgentOwnedLaunchGate: 在权限和后端前执行“先启动并绑定目标软件”硬门禁；如果没有这行代码，模型看过旧窗口截图后仍可能直接操作旧软件。
        if launch_gate_rejection is not None:  # 新增代码+AgentOwnedLaunchGate: 判断本次动作是否因为缺少 agent-owned launch target 被拒绝；如果没有这行代码，拒绝文本会被忽略继续执行。
            return launch_gate_rejection  # 新增代码+AgentOwnedLaunchGate: 直接返回纠偏结果且不弹权限不碰后端；如果没有这行代码，未启动软件前仍可能进入真实鼠标键盘链路。
        completion_signal = self._computer_use_full_completion_signal_for_action(action_name, arguments)  # 新增代码+ComputerUseCompletionGate: 在权限和后端前检查是否应收敛最终回答；如果没有这行代码，模型会在已经画出结果后继续真实移动鼠标。
        if completion_signal is not None:  # 新增代码+ComputerUseCompletionGate: 判断完成门是否触发；如果没有这行代码，收敛文本会被忽略继续执行。
            return completion_signal  # 新增代码+ComputerUseCompletionGate: 返回完成信号且不触碰真实桌面；如果没有这行代码，重复动作仍会打到 Paint。
        try:  # 新增代码+Phase30ComputerUseActionGate: 优先导入动作参数脱敏 helper；若没有这行代码，权限提示和拒绝观察可能保存原始 type_text 文本。
            from learning_agent.computer_use.action_policy import redact_action_arguments  # 新增代码+Phase30ComputerUseActionGate: 包运行模式下导入脱敏函数；若没有这行代码，敏感文本无法统一隐藏。
        except ModuleNotFoundError as error:  # 新增代码+Phase30ComputerUseActionGate: 兼容直接脚本运行时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因导入路径崩溃。
            if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.action_policy"}:  # 新增代码+Phase30ComputerUseActionGate: 只对目标包路径缺失做 fallback；若没有这行代码，真实内部错误会被误吞。
                raise  # 新增代码+Phase30ComputerUseActionGate: 重新抛出非目标导入错误；若没有这行代码，排查脱敏 helper 问题会很困难。
            from computer_use.action_policy import redact_action_arguments  # 新增代码+Phase30ComputerUseActionGate: 脚本模式下导入脱敏函数；若没有这行代码，bat 入口无法隐藏敏感文本。
        permission_payload = redact_action_arguments(action_name, arguments)  # 修改代码+Phase30ComputerUseActionGate: 复制并脱敏参数用于权限展示和审计；若没有这行代码，原始 type_text 可能进入终端日志或观察记录。
        permission_text = json.dumps(permission_payload, ensure_ascii=False, indent=2)  # 新增代码+OSComputerUse: 把参数格式化成用户可读 JSON；若没有这行代码，权限弹窗不便核对坐标和文本。
        permission_action = f"执行 OS Computer Use 桌面动作：{action_name}\n参数：{permission_text}"  # 新增代码+OSComputerUse: 构造清晰权限说明；若没有这行代码，用户无法知道 agent 准备控制桌面做什么。
        if not self.ask_permission(permission_action):  # 新增代码+OSComputerUse: 高风险桌面动作必须再次请求用户确认；若没有这行代码，computer_action 会绕过既有权限边界。
            self._record_observation("computer_use_denied", {"action": action_name, "arguments": permission_payload})  # 新增代码+OSComputerUse: 记录用户拒绝桌面动作；若没有这行代码，审计无法解释动作为什么没执行。
            return f"用户拒绝了操作：{permission_action}"  # 新增代码+OSComputerUse: 返回拒绝信息给模型；若没有这行代码，模型可能误以为动作已经完成。
        result = self.computer_use_controller.execute(arguments)  # 新增代码+OSComputerUse: 通过控制器执行安全检查和后端调用；若没有这行代码，动作不会真正到达 Computer Use 后端。
        self._record_observation("computer_use_action", {"action": action_name, "ok": result.ok, "message": result.message, "data": result.data})  # 新增代码+OSComputerUse: 记录桌面动作结果；若没有这行代码，Phase 7 无法复盘 Computer Use 行为。
        self._record_computer_use_image_artifacts(result.data, "computer_action")  # 新增代码+Phase41WindowsImageResults: 登记 action 结果中的截图 artifact；如果没有这行代码，动作前后证据截图不会进入 active_artifacts。
        return result.to_text()  # 新增代码+OSComputerUse: 把结构化结果转成工具返回文本；若没有这行代码，模型无法读取动作执行结果。

    # 新增代码+Phase92UniversalComputerUse：这一整段函数是通用 Windows Computer Use mode 的开始；如果没有这段函数，computer_use(operation=mode) 只能在兼容层归一化，无法真正进入通用运行时。
    def _computer_use_mode(self, arguments: dict[str, Any]) -> str:  # 新增代码+Phase92UniversalComputerUse：定义通用 mode 私有工具处理器；如果没有这行代码，Phase92 target_tool 没有 agent 侧执行入口。
        try:  # 新增代码+Phase92UniversalComputerUse：优先按包模式导入 Phase92 runtime；如果没有这行代码，正常包运行时无法加载通用 Computer Use mode。
            from learning_agent.computer_use.universal_mode import UniversalWindowsComputerUseRuntime  # 新增代码+Phase92UniversalComputerUse：导入通用运行时；如果没有这行代码，agent 无法调用观察-规划-动作-验证闭环。
        except ModuleNotFoundError as error:  # 新增代码+Phase92UniversalComputerUse：兼容 start_oauth_agent.bat 脚本模式；如果没有这段代码，真实可见终端可能因为包名前缀失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.universal_mode"}:  # 新增代码+Phase92UniversalComputerUse：只对目标包路径缺失做 fallback；如果没有这行代码，runtime 内部真实 bug 会被误吞。
                raise  # 新增代码+Phase92UniversalComputerUse：重新抛出非路径类导入错误；如果没有这行代码，排查 runtime 依赖问题会很困难。
            from computer_use.universal_mode import UniversalWindowsComputerUseRuntime  # 新增代码+Phase92UniversalComputerUse：脚本模式导入通用运行时；如果没有这行代码，bat 入口无法执行 mode。
        prompt_text = str(arguments.get("prompt", ""))  # 新增代码+Phase92UniversalComputerUse：读取用户 prompt 只传给 runtime 内存处理；如果没有这行代码，新模式不知道用户要做什么。
        real_actions = bool(arguments.get("real_actions", False))  # 新增代码+Phase92UniversalComputerUse：读取真实动作开关且默认关闭；如果没有这行代码，普通 mode 调用可能误触真实桌面。
        if real_actions:  # 修改代码+ModelLoopSemanticPlanner：真实动作 prompt 入口不再黑盒执行整段任务；如果没有这一行，模型可能继续把 run_prompt 当成语义规划器。
            report = {  # 新增代码+ModelLoopSemanticPlanner：构造结构化降级报告；如果没有这一行，模型拿不到可读的自我纠正依据。
                "ok": False,  # 新增代码+ModelLoopSemanticPlanner：明确本次没有执行桌面动作；如果没有这一项，模型可能误以为任务已经完成。
                "decision": "model_loop_observe_action_required",  # 新增代码+ModelLoopSemanticPlanner：给测试和模型稳定原因码；如果没有这一项，后续难以区分权限拒绝和架构降级。
                "reason": "semantic planning must happen in the model loop",  # 新增代码+ModelLoopSemanticPlanner：说明拒绝黑盒执行的原因；如果没有这一项，维护者可能重新接回旧 runtime。
                "next_tools": ["computer_observe", "computer_action", "computer_use"],  # 新增代码+ModelLoopSemanticPlanner：提示模型下一步该用的稳定工具；如果没有这一项，模型不容易从错误入口恢复。
                "prompt_text_included": False,  # 新增代码+ModelLoopSemanticPlanner：声明报告不泄露原始 prompt；如果没有这一项，审计无法确认隐私边界。
                "real_actions_requested": True,  # 新增代码+ModelLoopSemanticPlanner：保留用户请求真实动作的事实；如果没有这一项，排查时不知道为什么触发降级。
            }  # 新增代码+ModelLoopSemanticPlanner：降级报告字典结束；如果没有这一行，Python 字典语法不完整。
            self._record_observation("computer_use_model_loop_required", report)  # 新增代码+ModelLoopSemanticPlanner：把降级事件写入审计流；如果没有这一行，真实终端排查无法看到 run_prompt 被安全拦回主循环。
            return json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+ModelLoopSemanticPlanner：返回 JSON 给模型读取并自我修正；如果没有这一行，工具调用无法给下一轮模型提供稳定反馈。
        runtime = UniversalWindowsComputerUseRuntime()  # 新增代码+Phase92UniversalComputerUse：创建通用运行时实例；如果没有这行代码，agent 无法执行 Phase92 契约逻辑。
        report = runtime.run_prompt(prompt_text, real_actions=real_actions)  # 新增代码+Phase92UniversalComputerUse：运行 prompt 到通用闭环；如果没有这行代码，mode 工具不会产生结构化结果。
        self._record_observation("computer_use_mode", {"ok": bool(report.get("ok")), "prompt_sha256_16": report.get("prompt_sha256_16", ""), "prompt_text_included": False, "real_actions_requested": bool(report.get("real_actions_requested")), "single_universal_runtime": bool(report.get("single_universal_runtime")), "per_app_controller_required": bool(report.get("per_app_controller_required"))})  # 新增代码+Phase92UniversalComputerUse：记录脱敏 mode 结果；如果没有这行代码，审计无法看到 mode 是否进入通用运行时。
        return json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+Phase92UniversalComputerUse：返回中文友好的 JSON 报告；如果没有这行代码，模型无法读取 Phase92 mode 结果。
    # 新增代码+Phase92UniversalComputerUse：这一整段函数是通用 Windows Computer Use mode 的结束；如果没有这个结束标记，用户学习代码时不容易看出新模式处理器边界。

    # 新增代码+Phase49ComputerUseToolSurface: 这一整段函数是 computer_use / computer-use 兼容工具的开始；如果没有这段函数，ClaudeCode 风格工具名只能出现在 schema 里但无法真正调用现有 Windows Computer Use 能力。
    def _computer_use_compat(self, arguments: dict[str, Any]) -> str:  # 新增代码+Phase49ComputerUseToolSurface: 定义兼容工具入口；如果没有这行代码，executor 映射到 agent._computer_use_compat 时会直接报错。
        try:  # 新增代码+Phase49ComputerUseToolSurface: 优先按包模式导入参数归一化 helper；如果没有这行代码，learning_agent 包运行时无法使用统一兼容逻辑。
            from learning_agent.computer_use.tool_surface import normalize_computer_use_compat_arguments  # 新增代码+Phase49ComputerUseToolSurface: 导入兼容参数归一化函数；如果没有这行代码，兼容工具不知道该转发到 status、observe 还是 action。
        except ModuleNotFoundError as error:  # 新增代码+Phase49ComputerUseToolSurface: 兼容 bat 入口脚本模式下包名前缀不可用；如果没有这行代码，真实终端入口可能因为导入路径不同而失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.tool_surface"}:  # 新增代码+Phase49ComputerUseToolSurface: 只处理目标模块路径缺失；如果没有这行代码，模块内部真实错误会被误当成路径问题吞掉。
                raise  # 新增代码+Phase49ComputerUseToolSurface: 重新抛出非预期导入错误；如果没有这行代码，排查工具面内部 bug 会缺少真实 traceback。
            from computer_use.tool_surface import normalize_computer_use_compat_arguments  # 新增代码+Phase49ComputerUseToolSurface: 脚本模式下导入同一个 helper；如果没有这行代码，start_oauth_agent.bat 场景无法调用兼容工具。
        dispatch = normalize_computer_use_compat_arguments(arguments)  # 新增代码+Phase49ComputerUseToolSurface: 把 ClaudeCode 风格参数转换为旧工具参数；如果没有这行代码，兼容工具会绕开既有 controller 和安全策略。
        audit_dispatch = dict(dispatch)  # 修改代码+Phase92UniversalComputerUse：复制 dispatch 用于脱敏审计；如果没有这行代码，后续替换 arguments 会污染真实分发参数。
        if "audit_arguments" in audit_dispatch:  # 新增代码+Phase92UniversalComputerUse：检查兼容层是否提供脱敏审计字段；如果没有这行代码，mode prompt 原文可能进入观察日志。
            audit_dispatch["arguments"] = dict(audit_dispatch.get("audit_arguments", {}) or {})  # 新增代码+Phase92UniversalComputerUse：用脱敏参数替换日志里的真实参数；如果没有这行代码，dispatch 日志会记录用户 prompt 原文。
            audit_dispatch.pop("audit_arguments", None)  # 新增代码+Phase92UniversalComputerUse：删除辅助审计字段避免重复；如果没有这行代码，日志结构会同时出现两套参数字段。
        self._record_observation("computer_use_compat_dispatch", audit_dispatch)  # 修改代码+Phase92UniversalComputerUse：记录脱敏后的兼容分发结果；如果没有这行代码，mode 隐私边界会被旧日志破坏。
        if not bool(dispatch.get("ok", False)):  # 新增代码+Phase49ComputerUseToolSurface: 检查归一化是否成功；如果没有这行代码，错误参数可能继续进入底层工具造成混乱结果。
            return str(dispatch.get("error", "computer_use 兼容工具参数无效。"))  # 新增代码+Phase49ComputerUseToolSurface: 返回清晰参数错误；如果没有这行代码，模型不知道该如何修正 operation 或 action。
        target_tool = str(dispatch.get("target_tool", ""))  # 新增代码+Phase49ComputerUseToolSurface: 读取目标旧工具名；如果没有这行代码，兼容入口不知道该调用哪个已有函数。
        target_arguments = dict(dispatch.get("arguments", {}))  # 新增代码+Phase49ComputerUseToolSurface: 复制目标参数避免修改原始 dispatch；如果没有这行代码，后续审计数据可能被底层工具意外改动。
        if target_tool == "computer_use_mode":  # 新增代码+Phase92UniversalComputerUse：分发 mode 到通用 Computer Use 运行时；如果没有这行代码，operation=mode 会落到未知目标工具。
            if bool(target_arguments.get("real_actions", False)):  # 新增代码+Phase92UniversalComputerUse：只有请求真实动作时才弹权限说明；如果没有这行代码，普通预演 mode 会被不必要地阻塞。
                permission_payload = dict(dispatch.get("audit_arguments", {}) or {})  # 新增代码+Phase92UniversalComputerUse：使用脱敏审计参数构造权限提示；如果没有这行代码，用户 prompt 原文可能显示在权限文本中。
                permission_text = json.dumps(permission_payload, ensure_ascii=False, indent=2)  # 新增代码+Phase92UniversalComputerUse：格式化脱敏权限信息；如果没有这行代码，用户不容易确认本次真实动作请求。
                if not self.ask_permission(f"执行通用 OS Computer Use mode 真实桌面动作。\n参数：{permission_text}"):  # 新增代码+Phase92UniversalComputerUse：真实动作必须经过用户确认；如果没有这行代码，mode 可能绕开桌面动作权限边界。
                    self._record_observation("computer_use_mode_denied", permission_payload)  # 新增代码+Phase92UniversalComputerUse：记录用户拒绝 mode 真实动作；如果没有这行代码，审计无法解释为什么没有继续。
                    return "用户拒绝了通用 OS Computer Use mode 真实桌面动作。"  # 新增代码+Phase92UniversalComputerUse：返回拒绝说明；如果没有这行代码，模型可能误以为动作已经执行。
            return self._computer_use_mode(target_arguments)  # 新增代码+Phase92UniversalComputerUse：调用通用 mode 处理器；如果没有这行代码，Phase92 runtime 不会执行。
        if target_tool == "computer_status":  # 新增代码+Phase49ComputerUseToolSurface: 分发 status 到只读状态工具；如果没有这行代码，compat status 无法复用现有状态实现。
            return self._computer_status(target_arguments)  # 新增代码+Phase49ComputerUseToolSurface: 调用现有 status 工具；如果没有这行代码，状态查询不会进入统一 controller 状态读取。
        if target_tool == "computer_observe":  # 新增代码+Phase49ComputerUseToolSurface: 分发 observe 到只读观察工具；如果没有这行代码，compat observe 会绕开现有观察审计和截图 artifact 登记。
            return self._computer_observe(target_arguments)  # 新增代码+Phase49ComputerUseToolSurface: 调用现有 observe 工具；如果没有这行代码，窗口枚举和截图观察不会走统一安全边界。
        if target_tool == "computer_action":  # 新增代码+Phase49ComputerUseToolSurface: 分发 action 到高风险动作工具；如果没有这行代码，compat action 无法复用现有审批、锁和 controller 执行链。
            return self._computer_action(target_arguments)  # 新增代码+Phase49ComputerUseToolSurface: 调用现有 action 工具；如果没有这行代码，真实桌面动作可能出现两套不一致实现。
        return f"computer_use 兼容工具失败：未知目标工具 {target_tool}"  # 新增代码+Phase49ComputerUseToolSurface: 兜底返回未知分发目标；如果没有这行代码，异常 dispatch 会沉默失败或抛出难懂错误。
    # 新增代码+Phase49ComputerUseToolSurface: 这一整段函数是 computer_use / computer-use 兼容工具的结束；如果没有这个结束标记，用户后续学习代码时不容易看出兼容层边界。

    def _read_file(self, arguments: dict[str, Any]) -> str:  # 作用: 读取工作区内文本文件
        raw_path = str(arguments.get("path", "")).strip()  # 作用: 从参数取 path 并清理空白
        if not raw_path:  # 作用: 如果模型没有提供 path
            return "read_file 失败：缺少 path 参数。"  # 作用: 返回缺参错误
        path = self._resolve_workspace_path(raw_path)  # 作用: 把路径安全解析到工作区内
        if path is None:  # 作用: 如果路径不在工作区内
            return "read_file 失败：只能读取 learning_agent 工作区内的文件。"  # 作用: 返回安全错误
        if not path.exists():  # 作用: 如果文件不存在
            return f"read_file 失败：文件不存在：{path}"  # 作用: 返回不存在提示
        if path.is_dir():  # 作用: 如果路径是目录
            return f"read_file 失败：不能把目录当文件读取：{path}"  # 作用: 返回目录错误
        text = path.read_text(encoding="utf-8", errors="replace")  # 作用: 读取 UTF-8 文本，坏字符替换
        if len(text) > 8000:  # 作用: 如果内容太长
            return text[:8000] + "\n...[内容过长，已截断]..."  # 作用: 截断返回，避免撑爆上下文
        return text  # 作用: 返回完整文件内容

    def _write_file(self, arguments: dict[str, Any]) -> str:  # 作用: 写入工作区内文本文件
        raw_path = str(arguments.get("path", "")).strip()  # 作用: 从参数取 path 并清理空白
        content = str(arguments.get("content", ""))  # 作用: 从参数取 content 并转为字符串
        if not raw_path:  # 作用: 如果模型没有提供 path
            return "write_file 失败：缺少 path 参数。"  # 作用: 返回缺参错误
        path = self._resolve_workspace_path(raw_path)  # 作用: 把路径安全解析到工作区内
        if path is None:  # 作用: 如果路径不在工作区内
            return "write_file 失败：只能写入 learning_agent 工作区内的文件。"  # 作用: 返回安全错误
        action = f"写入文件：{path}"  # 作用: 准备权限确认说明
        if not self.ask_permission(action):  # 作用: 请求用户确认，如果不同意
            return f"用户拒绝了操作：{action}"  # 作用: 返回拒绝结果给模型
        path.parent.mkdir(parents=True, exist_ok=True)  # 作用: 确保目标目录存在
        path.write_text(content, encoding="utf-8")  # 作用: 写入 UTF-8 文本
        return f"write_file 成功：已写入 {path}"  # 作用: 返回成功结果给模型

    def _append_memory(self, arguments: dict[str, Any]) -> str:  # 作用: 追加一条长期记忆
        text = str(arguments.get("text", "")).strip()  # 作用: 从参数取 text 并清理空白
        if not text:  # 作用: 如果模型没有提供记忆内容
            return "append_memory 失败：缺少 text 参数。"  # 作用: 返回缺参错误
        action = f"追加长期记忆：{text}"  # 作用: 准备权限确认说明
        if not self.ask_permission(action):  # 作用: 请求用户确认，如果不同意
            return f"用户拒绝了操作：{action}"  # 作用: 返回拒绝结果给模型
        with self.memory_path.open("a", encoding="utf-8") as file:  # 作用: 用追加模式打开 memory.md
            file.write(f"- {text}\n")  # 作用: 以 Markdown 列表形式追加记忆
        return "append_memory 成功：已写入 memory.md"  # 作用: 返回成功结果给模型

    def _todo_read(self, arguments: dict[str, Any]) -> str:  # 新增代码+TodoWrite: 读取内部任务清单并返回给模型；若省略: 模型无法查看之前维护的任务状态
        del arguments  # 新增代码+TodoWrite: todo_read 当前不需要参数但保留统一工具签名；若省略: 未使用参数会让静态阅读者误以为遗漏处理
        if not self.todo_path.exists():  # 新增代码+TodoWrite: 如果任务清单文件尚未创建；若省略: 第一次读取会因文件不存在报错
            return "todo_read 成功：当前任务清单为空。"  # 新增代码+TodoWrite: 返回空清单的可读结果；若省略: 模型不知道可以从空计划开始
        try:  # 新增代码+TodoWrite: 捕获任务清单文件读取和 JSON 解析错误；若省略: 损坏的 todo_state.json 会中断整个 agent.run
            payload = json.loads(self.todo_path.read_text(encoding="utf-8"))  # 新增代码+TodoWrite: 读取并解析结构化任务清单；若省略: todo_read 无法恢复持久任务状态
        except (OSError, json.JSONDecodeError) as error:  # 新增代码+TodoWrite: 处理磁盘读取或 JSON 格式错误；若省略: 用户会看到底层异常而不是可恢复提示
            return f"todo_read 失败：无法读取 todo_state.json：{error}"  # 新增代码+TodoWrite: 返回清楚失败原因给模型；若省略: 模型无法解释为什么任务清单不可用
        todos = payload.get("todos", []) if isinstance(payload, dict) else []  # 新增代码+TodoWrite: 从顶层对象中取 todos 数组；若省略: 工具无法兼容约定的保存格式
        if not isinstance(todos, list):  # 新增代码+TodoWrite: 校验 todos 必须是数组；若省略: 坏文件结构会进入后续输出
            return "todo_read 失败：todo_state.json 中的 todos 必须是数组。"  # 新增代码+TodoWrite: 返回结构错误提示；若省略: 模型难以知道该如何修复任务清单
        if not todos:  # 新增代码+TodoWrite: 如果数组存在但没有任务；若省略: 空数组会显示成冗长 JSON
            return "todo_read 成功：当前任务清单为空。"  # 新增代码+TodoWrite: 返回简洁空状态；若省略: 模型可能误以为读取失败
        return "todo_read 成功：当前任务清单如下：\n" + json.dumps({"todos": todos}, ensure_ascii=False, indent=2)  # 新增代码+TodoWrite: 返回结构化任务清单文本；若省略: 模型无法基于当前计划继续更新

    def _todo_write(self, arguments: dict[str, Any]) -> str:  # 新增代码+TodoWrite: 校验并写入完整内部任务清单；若省略: 模型无法维护长任务状态
        raw_todos = arguments.get("todos")  # 新增代码+TodoWrite: 从参数中取出 todos 数组；若省略: 工具不知道模型提交了哪些任务
        if not isinstance(raw_todos, list):  # 新增代码+TodoWrite: 校验 todos 必须是数组；若省略: 字符串或对象会污染任务清单格式
            return "todo_write 失败：缺少 todos 数组参数。"  # 新增代码+TodoWrite: 返回缺参或类型错误；若省略: 模型无法根据错误修正参数
        valid_statuses = {"pending", "in_progress", "completed"}  # 新增代码+TodoWrite: 定义允许的任务状态；若省略: doing/done 等不统一状态会进入任务清单
        valid_priorities = {"high", "medium", "low"}  # 新增代码+TodoWrite: 定义允许的优先级；若省略: 任务优先级会变得不一致
        normalized_todos: list[dict[str, str]] = []  # 新增代码+TodoWrite: 准备保存校验后的任务列表；若省略: 无法统一补全 id 和 priority
        for index, raw_todo in enumerate(raw_todos, start=1):  # 新增代码+TodoWrite: 逐条校验任务并生成默认 id；若省略: 无法定位哪一条任务参数错误
            if not isinstance(raw_todo, dict):  # 新增代码+TodoWrite: 每条任务必须是对象；若省略: 纯字符串任务会导致后续 .get 报错
                return f"todo_write 失败：第 {index} 条任务必须是对象。"  # 新增代码+TodoWrite: 返回具体任务编号错误；若省略: 模型不知道该修哪一条
            content = str(raw_todo.get("content", "")).strip()  # 新增代码+TodoWrite: 读取并清理任务内容；若省略: 空白任务会进入任务清单
            if not content:  # 新增代码+TodoWrite: 任务内容不能为空；若省略: 清单里会出现不可执行的空任务
                return f"todo_write 失败：第 {index} 条任务缺少 content。"  # 新增代码+TodoWrite: 返回具体缺失字段；若省略: 模型难以自我修正
            status = str(raw_todo.get("status", "")).strip()  # 新增代码+TodoWrite: 读取并清理任务状态；若省略: 无法判断任务进度
            if status not in valid_statuses:  # 新增代码+TodoWrite: 校验状态必须来自白名单；若省略: 非法状态会污染任务进度
                return f"todo_write 失败：第 {index} 条任务 status 必须是 pending/in_progress/completed。"  # 新增代码+TodoWrite: 告诉模型合法状态值；若省略: 模型不知道应该改成什么
            priority = str(raw_todo.get("priority", "medium")).strip() or "medium"  # 新增代码+TodoWrite: 读取优先级并默认为 medium；若省略: 未传 priority 的任务会缺字段
            if priority not in valid_priorities:  # 新增代码+TodoWrite: 校验优先级必须来自白名单；若省略: 紧急/普通等自由文本会让排序不稳定
                return f"todo_write 失败：第 {index} 条任务 priority 必须是 high/medium/low。"  # 新增代码+TodoWrite: 告诉模型合法优先级值；若省略: 模型难以修正错误参数
            todo_id = str(raw_todo.get("id", "")).strip() or f"todo-{index}"  # 新增代码+TodoWrite: 使用模型提供的 id 或自动生成稳定 id；若省略: 后续多轮更新难以引用同一任务
            normalized_todos.append({"id": todo_id, "content": content, "status": status, "priority": priority})  # 新增代码+TodoWrite: 保存规范化任务对象；若省略: 校验后的任务不会进入落盘结果
        payload = {"todos": normalized_todos}  # 新增代码+TodoWrite: 构造统一落盘 JSON 对象；若省略: todo_read 不知道从哪里读取任务数组
        self.todo_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # 新增代码+TodoWrite: 写入 UTF-8 JSON 任务清单；若省略: 任务状态只存在内存里，下一轮无法读取
        return f"todo_write 成功：已保存 {len(normalized_todos)} 条任务到 todo_state.json"  # 新增代码+TodoWrite: 返回保存数量给模型；若省略: 模型无法确认任务清单是否更新成功

    def _notebook_read(self, arguments: dict[str, Any]) -> str:  # 新增代码+Notebook工具: 读取 .ipynb cell 摘要或指定 cell；若省略: agent 无法像 Claude Code 一样查看 Notebook
        notebook_result = self._load_notebook(arguments.get("path"), "notebook_read")  # 新增代码+Notebook工具: 统一加载并校验 notebook 文件；若省略: 路径、扩展名和 JSON 校验会重复且容易不一致
        if isinstance(notebook_result, str):  # 新增代码+Notebook工具: 如果加载函数返回错误文本；若省略: 后续会把错误字符串当作 notebook 元组使用
            return notebook_result  # 新增代码+Notebook工具: 直接把可读错误返回给模型；若省略: 模型无法知道读取失败原因
        path, payload = notebook_result  # 新增代码+Notebook工具: 拆出安全路径和 notebook JSON；若省略: 后续无法访问文件位置和内容
        cells = payload.get("cells")  # 新增代码+Notebook工具: 读取 notebook 的 cells 字段；若省略: 工具不知道有哪些 cell 可展示
        if not isinstance(cells, list):  # 新增代码+Notebook工具: 校验 cells 必须是数组；若省略: 畸形 notebook 会导致遍历或索引异常
            return "notebook_read 失败：notebook JSON 中的 cells 必须是数组。"  # 新增代码+Notebook工具: 返回结构错误；若省略: 模型无法理解文件格式问题
        max_chars = self._parse_max_chars(arguments.get("max_chars"))  # 新增代码+Notebook工具: 解析最大返回字符数；若省略: 大 notebook 输出可能撑爆上下文
        selected_cells_result = self._select_notebook_cells(cells, arguments.get("cell_index"), "notebook_read")  # 新增代码+Notebook工具: 根据可选 cell_index 选择要展示的 cell；若省略: 指定单 cell 的读取需求无法处理
        if isinstance(selected_cells_result, str):  # 新增代码+Notebook工具: 如果 cell_index 校验失败；若省略: 错误文本会被当作列表遍历
            return selected_cells_result  # 新增代码+Notebook工具: 返回 cell_index 错误给模型；若省略: 模型无法修正索引
        lines = [f"notebook_read 成功：{path}", f"nbformat: {payload.get('nbformat', '?')}.{payload.get('nbformat_minor', '?')}", f"cells: {len(cells)}"]  # 新增代码+Notebook工具: 准备输出文件、版本和 cell 数量；若省略: 模型缺少 notebook 总览信息
        for cell_index, cell in selected_cells_result:  # 新增代码+Notebook工具: 遍历要展示的 cell；若省略: 工具不会输出任何 cell 内容
            if not isinstance(cell, dict):  # 新增代码+Notebook工具: 防御畸形 cell 不是对象的情况；若省略: 后续 .get 会在非字典上报错
                lines.append(f"cell {cell_index}: 非对象 cell，无法解析。")  # 新增代码+Notebook工具: 把畸形 cell 也报告给模型；若省略: 模型不知道哪个 cell 有问题
                continue  # 新增代码+Notebook工具: 跳过坏 cell 并继续其他 cell；若省略: 单个坏 cell 会阻断整个 notebook 读取
            cell_type = str(cell.get("cell_type", "unknown"))  # 新增代码+Notebook工具: 读取 cell 类型；若省略: 模型不知道这是 code 还是 markdown
            source_text = self._notebook_source_to_text(cell.get("source", ""))  # 新增代码+Notebook工具: 把 source 字符串或行数组统一成文本；若省略: list source 会显示成 Python/JSON 结构而不利于阅读
            preview = source_text.strip() or "(空 cell)"  # 新增代码+Notebook工具: 生成可读预览并处理空 cell；若省略: 空 cell 会显示成空白难以判断
            lines.append(f"cell {cell_index}: type={cell_type}, source_chars={len(source_text)}")  # 新增代码+Notebook工具: 输出 cell 索引、类型和长度；若省略: 模型无法精确引用要编辑的 cell
            lines.append(preview)  # 新增代码+Notebook工具: 输出 cell 内容预览；若省略: 读取工具只能看到结构看不到实际内容
        output = "\n".join(lines)  # 新增代码+Notebook工具: 合并多行输出；若省略: 返回值无法一次交给模型
        if len(output) > max_chars:  # 新增代码+Notebook工具: 如果输出超过长度限制；若省略: 大 notebook 可能挤爆模型上下文
            return output[:max_chars] + "\n...[notebook 内容过长，已截断]..."  # 新增代码+Notebook工具: 返回截断输出并提示；若省略: 模型会误以为看到完整内容
        return output  # 新增代码+Notebook工具: 返回完整 notebook 读取结果；若省略: 工具调用没有结果

    def _notebook_edit(self, arguments: dict[str, Any]) -> str:  # 新增代码+Notebook工具: 替换指定 .ipynb cell 的 source；若省略: agent 无法安全编辑 Notebook
        if arguments.get("source") is None:  # 新增代码+Notebook工具: 检查是否提供新 source；若省略: None 会被写成字符串 "None" 污染 notebook
            return "notebook_edit 失败：缺少 source 参数。"  # 新增代码+Notebook工具: 返回缺参提示；若省略: 模型难以修正编辑调用
        notebook_result = self._load_notebook(arguments.get("path"), "notebook_edit")  # 新增代码+Notebook工具: 统一加载并校验 notebook 文件；若省略: 编辑路径安全和格式校验容易遗漏
        if isinstance(notebook_result, str):  # 新增代码+Notebook工具: 如果加载函数返回错误文本；若省略: 后续会把错误字符串当作 notebook 元组使用
            return notebook_result  # 新增代码+Notebook工具: 直接返回加载错误；若省略: 模型无法知道编辑失败原因
        path, payload = notebook_result  # 新增代码+Notebook工具: 拆出安全路径和 notebook JSON；若省略: 后续无法定位文件和内容
        cells = payload.get("cells")  # 新增代码+Notebook工具: 读取 notebook cells；若省略: 工具不知道能编辑哪些 cell
        if not isinstance(cells, list):  # 新增代码+Notebook工具: 校验 cells 必须是数组；若省略: 畸形 notebook 会导致索引异常
            return "notebook_edit 失败：notebook JSON 中的 cells 必须是数组。"  # 新增代码+Notebook工具: 返回结构错误；若省略: 模型无法理解文件格式问题
        cell_index_result = self._parse_notebook_cell_index(arguments.get("cell_index"), len(cells), "notebook_edit")  # 新增代码+Notebook工具: 校验目标 cell 索引；若省略: 无效索引可能导致崩溃或误改
        if isinstance(cell_index_result, str):  # 新增代码+Notebook工具: 如果索引解析失败；若省略: 错误文本会被当作整数使用
            return cell_index_result  # 新增代码+Notebook工具: 返回索引错误给模型；若省略: 模型无法修正 cell_index
        cell = cells[cell_index_result]  # 新增代码+Notebook工具: 取出目标 cell；若省略: 后续无法修改 source
        if not isinstance(cell, dict):  # 新增代码+Notebook工具: 校验目标 cell 必须是对象；若省略: 非对象 cell 写 source 会报错
            return f"notebook_edit 失败：cell {cell_index_result} 不是对象，无法编辑。"  # 新增代码+Notebook工具: 返回畸形 cell 错误；若省略: 模型不知道为什么不能编辑
        source_text = str(arguments.get("source", ""))  # 新增代码+Notebook工具: 把新 source 转成字符串；若省略: 数字或布尔 source 会让写入格式不稳定
        action = f"编辑 Notebook cell：{path}\ncell_index：{cell_index_result}\n新内容字符数：{len(source_text)}"  # 新增代码+Notebook工具: 构造权限确认说明；若省略: 用户无法核对要修改哪个 notebook 和 cell
        if not self.ask_permission(action):  # 新增代码+Notebook工具: 写入 notebook 前请求用户确认；若省略: agent 会绕过权限边界修改文件
            return f"用户拒绝了操作：{action}"  # 新增代码+Notebook工具: 权限拒绝时返回可读结果；若省略: 模型不知道文件未被修改
        cell["source"] = self._notebook_text_to_source_lines(source_text)  # 新增代码+Notebook工具: 把新文本按 notebook 常用行数组格式写回 source；若省略: cell 内容不会被替换
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # 新增代码+Notebook工具: 以 UTF-8 JSON 写回 notebook；若省略: 修改只存在内存不会落盘
        return f"notebook_edit 成功：已更新 {path} 的 cell {cell_index_result}"  # 新增代码+Notebook工具: 返回成功结果给模型；若省略: 模型无法确认编辑是否完成

    def _load_notebook(self, raw_path: Any, tool_name: str) -> tuple[Path, dict[str, Any]] | str:  # 新增代码+Notebook工具: 统一读取和校验 notebook 文件；若省略: read/edit 会重复路径和 JSON 校验逻辑
        raw_path_text = str(raw_path or "").strip()  # 新增代码+Notebook工具: 把 path 参数转成清理后的字符串；若省略: None 或空白路径处理不稳定
        if not raw_path_text:  # 新增代码+Notebook工具: 检查 path 是否为空；若省略: 空路径会被解析成工作区目录
            return f"{tool_name} 失败：缺少 path 参数。"  # 新增代码+Notebook工具: 返回缺参错误；若省略: 模型难以修正调用
        path = self._resolve_workspace_path(raw_path_text)  # 新增代码+Notebook工具: 使用已有安全路径解析器限制工作区边界；若省略: ../ 可能逃出 workspace
        if path is None:  # 新增代码+Notebook工具: 如果路径越界；若省略: 工具可能读取或修改工作区外文件
            return f"{tool_name} 失败：只能操作 learning_agent 工作区内的 .ipynb 文件。"  # 新增代码+Notebook工具: 返回安全边界错误；若省略: 模型不知道为什么被拒绝
        if path.suffix.lower() != ".ipynb":  # 新增代码+Notebook工具: 只允许 notebook 文件扩展名；若省略: 工具可能被误用于普通 JSON 或文本文件
            return f"{tool_name} 失败：只能操作 .ipynb 文件：{path}"  # 新增代码+Notebook工具: 返回扩展名错误；若省略: 模型难以选择正确工具
        if not path.exists():  # 新增代码+Notebook工具: 检查文件是否存在；若省略: 读取会抛底层 FileNotFoundError
            return f"{tool_name} 失败：文件不存在：{path}"  # 新增代码+Notebook工具: 返回不存在错误；若省略: 用户会看到不友好的底层异常
        if path.is_dir():  # 新增代码+Notebook工具: 防止把目录当 notebook 文件；若省略: 读取目录会抛底层异常
            return f"{tool_name} 失败：不能把目录当 notebook 读取：{path}"  # 新增代码+Notebook工具: 返回目录错误；若省略: 模型难以修正 path
        try:  # 新增代码+Notebook工具: 捕获文件读取和 JSON 解析异常；若省略: 坏 notebook 会中断整个 agent.run
            payload = json.loads(path.read_text(encoding="utf-8"))  # 新增代码+Notebook工具: 读取 UTF-8 notebook JSON；若省略: 工具拿不到 notebook 内容
        except (OSError, json.JSONDecodeError) as error:  # 新增代码+Notebook工具: 处理磁盘错误和 JSON 格式错误；若省略: 用户会看到 Python 堆栈
            return f"{tool_name} 失败：无法读取 notebook JSON：{error}"  # 新增代码+Notebook工具: 返回可读失败原因；若省略: 模型无法解释为什么读取失败
        if not isinstance(payload, dict):  # 新增代码+Notebook工具: notebook 顶层必须是对象；若省略: list/null JSON 会让后续 .get 报错
            return f"{tool_name} 失败：notebook JSON 顶层必须是对象。"  # 新增代码+Notebook工具: 返回结构错误；若省略: 模型不知道文件格式不对
        return path, payload  # 新增代码+Notebook工具: 返回安全路径和 notebook 数据；若省略: read/edit 无法继续处理

    def _select_notebook_cells(self, cells: list[Any], raw_cell_index: Any, tool_name: str) -> list[tuple[int, Any]] | str:  # 新增代码+Notebook工具: 根据可选索引选择 cell；若省略: notebook_read 不能复用索引校验
        if raw_cell_index is None:  # 新增代码+Notebook工具: 如果模型没有指定 cell_index；若省略: 全量摘要场景无法区分
            return list(enumerate(cells))  # 新增代码+Notebook工具: 返回所有 cell 供摘要展示；若省略: notebook_read 默认会没有输出
        cell_index = self._parse_notebook_cell_index(raw_cell_index, len(cells), tool_name)  # 新增代码+Notebook工具: 解析并校验单个 cell 索引；若省略: 可能访问越界索引
        if isinstance(cell_index, str):  # 新增代码+Notebook工具: 如果索引解析失败；若省略: 错误文本会被当作整数使用
            return cell_index  # 新增代码+Notebook工具: 返回索引错误；若省略: 模型无法修正参数
        return [(cell_index, cells[cell_index])]  # 新增代码+Notebook工具: 返回指定 cell 的二元组列表；若省略: 指定单 cell 时不会输出内容

    def _parse_notebook_cell_index(self, raw_cell_index: Any, cell_count: int, tool_name: str) -> int | str:  # 新增代码+Notebook工具: 把 cell_index 解析成安全整数；若省略: read/edit 索引校验会重复且易错
        try:  # 新增代码+Notebook工具: 捕获模型传入非整数索引的情况；若省略: int 转换失败会中断 agent.run
            cell_index = int(raw_cell_index)  # 新增代码+Notebook工具: 把 JSON 数字或数字字符串转成 int；若省略: 字符串索引无法兼容
        except (TypeError, ValueError):  # 新增代码+Notebook工具: 处理 None、对象或非数字字符串；若省略: 错误输入会抛异常
            return f"{tool_name} 失败：cell_index 必须是整数。"  # 新增代码+Notebook工具: 返回索引类型错误；若省略: 模型不知道如何修正
        if cell_index < 0 or cell_index >= cell_count:  # 新增代码+Notebook工具: 检查索引是否在 cell 数组范围内；若省略: 负数或越界可能误读误改
            return f"{tool_name} 失败：cell_index 超出范围，当前 notebook 有 {cell_count} 个 cell。"  # 新增代码+Notebook工具: 返回范围错误和总数；若省略: 模型不知道可用索引范围
        return cell_index  # 新增代码+Notebook工具: 返回安全 cell 索引；若省略: 调用方无法定位目标 cell

    def _notebook_source_to_text(self, source: Any) -> str:  # 新增代码+Notebook工具: 把 notebook source 统一转成文本；若省略: list/string 两种 notebook 表示会导致输出不一致
        if isinstance(source, list):  # 新增代码+Notebook工具: notebook source 常见形式是字符串数组；若省略: 多行 source 会显示成列表结构
            return "".join(str(part) for part in source)  # 新增代码+Notebook工具: 拼接每一行 source；若省略: 模型看不到正常连续文本
        if isinstance(source, str):  # 新增代码+Notebook工具: notebook source 也可能是单个字符串；若省略: 字符串 source 会被走到 JSON 兜底
            return source  # 新增代码+Notebook工具: 原样返回字符串 source；若省略: 代码内容可能被额外加引号
        if source is None:  # 新增代码+Notebook工具: 处理缺失或 null source；若省略: None 会显示成字符串 "None"
            return ""  # 新增代码+Notebook工具: 空 source 返回空文本；若省略: 空 cell 可读性变差
        return json.dumps(source, ensure_ascii=False)  # 新增代码+Notebook工具: 兜底显示异常 source 结构；若省略: 非标准 source 会完全丢失

    def _notebook_text_to_source_lines(self, source_text: str) -> list[str]:  # 新增代码+Notebook工具: 把编辑文本转成 notebook 常用 source 行数组；若省略: 写回格式容易不稳定
        if source_text == "":  # 新增代码+Notebook工具: 如果用户明确写入空内容；若省略: splitlines 会返回空列表但语义不够清楚
            return []  # 新增代码+Notebook工具: 空 cell 用空数组表示；若省略: 空字符串可能和多行格式不一致
        return source_text.splitlines(keepends=True)  # 新增代码+Notebook工具: 按行保留换行符写回 source；若省略: notebook 中的多行代码会丢失换行结构

    def _start_background_command(self, arguments: dict[str, Any]) -> str:  # 新增代码+后台命令: 启动后台 shell 命令并登记进程；若省略: agent 无法执行长时间运行的命令
        command = str(arguments.get("command", "")).strip()  # 新增代码+后台命令: 读取并清理 command 参数；若省略: 工具不知道要执行什么命令
        if not command:  # 新增代码+后台命令: 检查 command 是否为空；若省略: 可能启动空 shell 或产生难懂错误
            return "start_background_command 失败：缺少 command 参数。"  # 新增代码+后台命令: 返回清楚缺参错误；若省略: 模型难以修正调用
        cwd_result = self._resolve_background_cwd(arguments.get("cwd"))  # 新增代码+后台命令: 解析可选 cwd 并限制在工作区内；若省略: 命令可能在不受控目录运行
        if isinstance(cwd_result, str):  # 新增代码+后台命令: 如果 cwd 解析返回错误文本；若省略: 后续会把错误当路径使用
            return cwd_result  # 新增代码+后台命令: 在权限确认前返回 cwd 错误；若省略: 用户会被无效操作打扰
        label = str(arguments.get("label", "")).strip()  # 新增代码+后台命令: 读取可选标签；若省略: 多后台命令难以区分
        action = f"启动后台命令：{command}\n工作目录：{cwd_result}\n标签：{label or '(无)'}"  # 新增代码+后台命令: 构造启动权限说明；若省略: 用户无法核对命令、目录和标签
        if not self.ask_permission(action):  # 新增代码+后台命令: 启动命令前请求用户确认；若省略: agent 会绕过权限边界执行本机命令
            return f"用户拒绝了操作：{action}"  # 新增代码+后台命令: 权限拒绝时返回可读结果；若省略: 模型不知道命令没有启动
        command_id = f"bg_{secrets.token_hex(6)}"  # 新增代码+后台命令: 生成短且唯一的后台命令 id；若省略: read/stop 无法引用此进程
        stdout_lines: queue.Queue[str] = queue.Queue()  # 新增代码+后台命令: 创建 stdout 增量队列；若省略: 标准输出无法非阻塞读取
        stderr_lines: queue.Queue[str] = queue.Queue()  # 新增代码+后台命令: 创建 stderr 增量队列；若省略: 错误输出会丢失或阻塞管道
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0  # 修改代码+后台命令: Windows 下让后台命令拥有独立进程组；若没有这行代码，CTRL_BREAK_EVENT 无法一起停止 shell 子进程
        try:  # 新增代码+后台命令: 捕获 Popen 启动异常；若省略: 命令启动失败会中断整个 agent.run
            process = subprocess.Popen(command, shell=True, cwd=str(cwd_result), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", creationflags=creation_flags)  # 修改代码+后台命令: 用系统 shell 启动后台进程并在 Windows 创建独立进程组；若省略 creationflags，sandbox 下停止命令可能只能杀 shell 而留下子进程
        except Exception as error:  # 新增代码+后台命令: 处理命令不可启动、cwd 不可用等异常；若省略: 用户会看到底层堆栈或 agent 崩溃
            return f"start_background_command 失败：{error}"  # 新增代码+后台命令: 返回可读启动失败原因；若省略: 模型无法解释失败
        stdout_thread = threading.Thread(target=self._background_stream_reader, args=(process.stdout, stdout_lines), daemon=True)  # 修改代码+后台命令: 先创建 stdout reader 线程并保存对象；若没有这行代码，stop 时无法等待 stdout 管道释放
        stderr_thread = threading.Thread(target=self._background_stream_reader, args=(process.stderr, stderr_lines), daemon=True)  # 修改代码+后台命令: 先创建 stderr reader 线程并保存对象；若没有这行代码，stop 时无法等待 stderr 管道释放
        record = BackgroundCommand(command_id=command_id, command=command, cwd=cwd_result, label=label, process=process, stdout_lines=stdout_lines, stderr_lines=stderr_lines, started_at=time.strftime("%Y-%m-%d %H:%M:%S"), stdout_thread=stdout_thread, stderr_thread=stderr_thread)  # 修改代码+后台命令: 保存后台命令完整状态和 reader 线程；若省略线程字段，停止命令后 Windows 仍可能延迟占用临时目录
        monitor_thread = threading.Thread(target=self._background_completion_monitor, args=(record,), daemon=True)  # 新增代码+BackgroundAutoNotify: 创建后台完成监控线程；若没有这行代码，命令退出后不会自动写入 task_registry 和 runtime queue。
        record.monitor_thread = monitor_thread  # 新增代码+BackgroundAutoNotify: 把监控线程挂到记录上便于后续审计和调试；若没有这行代码，状态对象看不到谁负责自动收尾。
        self.background_commands[command_id] = record  # 新增代码+后台命令: 把记录加入 agent 内存表；若省略: command_id 返回后也无法被读取或停止
        self.task_registry.create_task(task_id=command_id, prompt=command, kind="background_shell", status="running", background=True, metadata={"cwd": str(cwd_result), "label": label})  # 新增代码+DurableTaskRegistry: 把后台命令登记成持久任务；若没有这行代码，后台 shell 无法被 task poller 和状态 CLI 审计。
        stdout_thread.start()  # 修改代码+后台命令: 启动 stdout reader 线程；若没有这行代码，后台命令标准输出不会进入 read 工具
        stderr_thread.start()  # 修改代码+后台命令: 启动 stderr reader 线程；若没有这行代码，后台命令错误输出不会进入 read 工具
        monitor_thread.start()  # 新增代码+BackgroundAutoNotify: 启动自动收尾监控线程；若没有这行代码，后台命令完成后仍需要模型手动 read 才能发现结果。
        return f"start_background_command 成功：command_id={command_id}\n状态：{self._background_command_status(record)}\n工作目录：{cwd_result}"  # 新增代码+后台命令: 返回 command_id 和状态给模型；若省略: 模型无法继续 read/stop

    def _resolve_background_cwd(self, raw_cwd: Any) -> Path | str:  # 新增代码+后台命令: 解析后台命令工作目录并限制在 workspace；若省略: cwd 校验逻辑会散落在启动工具中
        cwd_text = str(raw_cwd or "").strip()  # 新增代码+后台命令: 把可选 cwd 转成清理后的字符串；若省略: None 或空白 cwd 处理不稳定
        if not cwd_text:  # 新增代码+后台命令: 如果模型没有提供 cwd；若省略: 默认工作目录不明确
            return self.workspace  # 新增代码+后台命令: 默认使用 agent 工作区根目录；若省略: Popen 可能继承不可预期 cwd
        cwd_path = self._resolve_workspace_path(cwd_text)  # 新增代码+后台命令: 使用已有安全路径解析器限制工作区边界；若省略: .. 可能逃出 workspace
        if cwd_path is None:  # 新增代码+后台命令: 如果 cwd 不在工作区内；若省略: 越界目录会继续执行
            return "start_background_command 失败：cwd 必须位于 learning_agent 工作区内。"  # 新增代码+后台命令: 返回边界错误；若省略: 模型不知道 cwd 为什么被拒绝
        if not cwd_path.exists():  # 新增代码+后台命令: 如果 cwd 不存在；若省略: Popen 会抛底层找不到目录异常
            return f"start_background_command 失败：cwd 不存在：{cwd_path}"  # 新增代码+后台命令: 返回不存在路径；若省略: 错误信息不够友好
        if not cwd_path.is_dir():  # 新增代码+后台命令: 如果 cwd 指向文件而不是目录；若省略: Popen 会抛难懂异常
            return f"start_background_command 失败：cwd 不是目录：{cwd_path}"  # 新增代码+后台命令: 返回类型错误；若省略: 模型难以修正 cwd
        return cwd_path  # 新增代码+后台命令: 返回安全目录路径；若省略: 启动工具拿不到 cwd

    def _background_stream_reader(self, stream: Any, output_queue: queue.Queue[str]) -> None:  # 新增代码+后台命令: 在线程中读取进程输出并放入队列；若省略: 主线程读取会阻塞 tool loop
        if stream is None:  # 新增代码+后台命令: 防御性处理没有管道的情况；若省略: None.readline 会报错
            return  # 新增代码+后台命令: 没有流时直接结束线程；若省略: 后续代码无法安全执行
        try:  # 新增代码+后台命令: 捕获读取过程中流关闭或编码异常；若省略: reader 线程异常会污染测试输出
            for line in iter(stream.readline, ""):  # 新增代码+后台命令: 持续读取直到 EOF；若省略: 只能拿到一行或阻塞主流程
                output_queue.put(line)  # 新增代码+后台命令: 把每行输出放入线程安全队列；若省略: read 工具拿不到输出
        except Exception as error:  # 新增代码+后台命令: 处理读取异常；若省略: 输出读取失败不会留下任何线索
            output_queue.put(f"[后台输出读取失败：{error}]\n")  # 新增代码+后台命令: 把读取错误也作为输出返回；若省略: 模型无法知道输出为何中断
        finally:  # 新增代码+后台命令: 读取结束后尝试关闭流；若省略: 管道句柄可能延迟释放
            try:  # 新增代码+后台命令: 捕获关闭流异常；若省略: close 失败会在线程里抛出
                stream.close()  # 新增代码+后台命令: 关闭已读完的输出流；若省略: 子进程结束后句柄可能残留
            except Exception:  # 新增代码+后台命令: 忽略关闭异常；若省略: 清理失败会制造无意义报错
                pass  # 新增代码+后台命令: 保持 reader 线程静默结束；若省略: except 块语法不完整

    def _background_completion_monitor(self, record: BackgroundCommand) -> None:  # 新增代码+BackgroundAutoNotify: 等待后台命令结束并自动写入持久任务状态；若没有这行代码，长任务完成不会主动回灌给主 agent
        try:  # 新增代码+BackgroundAutoNotify: 捕获监控线程里的所有异常避免后台线程静默崩溃；若没有这行代码，失败时任务会永远卡在 running
            record.process.wait()  # 新增代码+BackgroundAutoNotify: 等待真实后台进程退出；若没有这行代码，监控线程无法知道什么时候该收尾
            self._join_background_reader_threads(record, 1.0)  # 新增代码+BackgroundAutoNotify: 给 stdout/stderr reader 时间读完 EOF；若没有这行代码，最后几行输出可能还没进入队列
            self._close_background_process_streams(record.process)  # 新增代码+BackgroundAutoNotify: 关闭已结束进程的管道句柄；若没有这行代码，Windows 上句柄可能延迟释放
            self._join_background_reader_threads(record, 0.5)  # 新增代码+BackgroundAutoNotify: 关闭管道后再等一次 reader 收尾；若没有这行代码，输出队列可能还缺尾部内容
            self._finalize_background_command_record(record)  # 新增代码+BackgroundAutoNotify: 把退出码、输出和通知统一写入持久层；若没有这行代码，等待结束不会产生可审计结果
        except Exception as error:  # 新增代码+BackgroundAutoNotify: 处理自动监控自身失败；若没有这行代码，监控异常会导致任务状态无人收束
            try:  # 新增代码+BackgroundAutoNotify: 尝试读取当前持久任务状态；若没有这行代码，未知任务会让异常处理再次崩溃
                current_record = self.task_registry.get_task(record.command_id)  # 新增代码+BackgroundAutoNotify: 获取任务当前状态以避免覆盖已收束结果；若没有这行代码，可能把 stopped/completed 覆盖成 failed
            except KeyError:  # 新增代码+BackgroundAutoNotify: 任务记录不存在时放弃监控失败写入；若没有这行代码，删除或创建失败的记录会导致线程报错
                return  # 新增代码+BackgroundAutoNotify: 没有持久记录就安全退出；若没有这行代码，异常处理会继续访问不存在的任务
            if current_record.status == "running" and not record.stop_requested:  # 新增代码+BackgroundAutoNotify: 只在任务仍运行且不是用户主动停止时写失败；若没有这行代码，正常 stop 可能被误报失败
                self.task_registry.fail_task(record.command_id, f"后台命令自动监控失败：{error}")  # 新增代码+BackgroundAutoNotify: 把监控异常变成可见失败通知；若没有这行代码，状态 CLI/API 看不到卡住原因

    def _finalize_background_command_record(self, record: BackgroundCommand) -> None:  # 新增代码+BackgroundAutoNotify: 根据后台命令最终状态更新 task_registry；若没有这行代码，read 和监控会各自写一套收尾逻辑
        if record.stop_requested:  # 新增代码+BackgroundAutoNotify: 如果 stop_background_command 已经接管收尾；若没有这行代码，自动监控会和用户停止流程抢写状态
            return  # 新增代码+BackgroundAutoNotify: 主动停止的任务交给 stop 工具写 stopped；若没有这行代码，用户停止可能被覆盖成 failed/completed
        try:  # 新增代码+BackgroundAutoNotify: 尝试读取持久任务记录；若没有这行代码，任务不存在时会抛异常中断监控线程
            current_record = self.task_registry.get_task(record.command_id)  # 新增代码+BackgroundAutoNotify: 读取当前状态用于幂等判断；若没有这行代码，已完成任务可能重复通知
        except KeyError:  # 新增代码+BackgroundAutoNotify: 持久任务不存在时安全退出；若没有这行代码，异常会让后台监控失败
            return  # 新增代码+BackgroundAutoNotify: 没有记录时不做任何写入；若没有这行代码，后续状态更新没有目标
        if current_record.status != "running":  # 新增代码+BackgroundAutoNotify: 只有 running 任务才允许自动收尾；若没有这行代码，stop/read 已收束的任务会被重复覆盖
            return  # 新增代码+BackgroundAutoNotify: 已经是终态或等待输入时保持原状态；若没有这行代码，状态历史可能被改坏
        return_code = record.process.poll()  # 新增代码+BackgroundAutoNotify: 读取进程退出码；若没有这行代码，无法区分成功完成和失败退出
        if return_code is None:  # 新增代码+BackgroundAutoNotify: 如果进程其实还没退出；若没有这行代码，可能把运行中的命令提前完成
            return  # 新增代码+BackgroundAutoNotify: 运行中的命令不收尾；若没有这行代码，后台任务状态会被提前写错
        stdout_text = self._drain_text_queue(record.stdout_lines, 20000)  # 新增代码+BackgroundAutoNotify: 自动收集剩余 stdout 输出；若没有这行代码，完成通知缺少命令结果
        stderr_text = self._drain_text_queue(record.stderr_lines, 20000)  # 新增代码+BackgroundAutoNotify: 自动收集剩余 stderr 输出；若没有这行代码，失败命令缺少错误上下文
        combined_output = "\n".join(part for part in [stdout_text, stderr_text] if part)  # 新增代码+BackgroundAutoNotify: 合并两路输出准备落盘；若没有这行代码，任务摘要无法统一展示结果
        if combined_output:  # 新增代码+BackgroundAutoNotify: 只有有新输出时才追加到输出文件；若没有这行代码，空命令会产生噪声记录
            self.task_registry.append_output(record.command_id, combined_output + "\n")  # 新增代码+BackgroundAutoNotify: 把最后输出写入 durable task output；若没有这行代码，重启后无法复查后台命令结果
        if return_code == 0:  # 新增代码+BackgroundAutoNotify: 退出码 0 表示后台命令成功；若没有这行代码，成功命令无法和失败命令区分
            self.task_registry.complete_task(record.command_id, output="", usage={})  # 新增代码+BackgroundAutoNotify: 标记任务完成并生成 task_notification；若没有这行代码，下一轮模型不会自动收到完成结果
        else:  # 新增代码+BackgroundAutoNotify: 非 0 退出码进入失败路径；若没有这行代码，失败命令可能被误报成功
            self.task_registry.fail_task(record.command_id, f"后台命令退出码：{return_code}")  # 新增代码+BackgroundAutoNotify: 标记任务失败并生成通知；若没有这行代码，失败状态不会自动回灌模型

    def _read_background_command(self, arguments: dict[str, Any]) -> str:  # 新增代码+后台命令: 读取后台命令增量输出；若省略: 模型无法观察后台任务状态
        command_id = str(arguments.get("command_id", "")).strip()  # 新增代码+后台命令: 读取要观察的 command_id；若省略: 工具不知道读取哪个后台命令
        if not command_id:  # 新增代码+后台命令: 检查 command_id 是否为空；若省略: 空 id 会变成未知命令错误
            return "read_background_command 失败：缺少 command_id 参数。"  # 新增代码+后台命令: 返回缺参提示；若省略: 模型难以修正调用
        record = self.background_commands.get(command_id)  # 新增代码+后台命令: 从内存表中查找后台命令；若省略: 无法定位进程和输出队列
        if record is None:  # 新增代码+后台命令: 如果 id 不存在；若省略: 后续访问 None 会报错
            return f"read_background_command 失败：未知 command_id：{command_id}"  # 新增代码+后台命令: 返回未知 id 错误；若省略: 模型不知道需要重新启动或改 id
        max_chars = self._parse_max_chars(arguments.get("max_chars"))  # 新增代码+后台命令: 解析可选最大输出字符数；若省略: 长输出可能不受控
        stdout_text = self._drain_text_queue(record.stdout_lines, max_chars)  # 新增代码+后台命令: 读取 stdout 队列里的增量文本；若省略: 标准输出不会返回给模型
        stderr_text = self._drain_text_queue(record.stderr_lines, max_chars)  # 新增代码+后台命令: 读取 stderr 队列里的增量文本；若省略: 错误输出不会返回给模型
        combined_output = "\n".join(part for part in [stdout_text, stderr_text] if part)  # 新增代码+DurableTaskRegistry: 合并本次读取到的 stdout/stderr；若没有这行代码，后台输出无法写入统一 task output 文件。
        if combined_output:  # 新增代码+DurableTaskRegistry: 只有有新增输出时才追加文件；若没有这行代码，空读取会制造无意义输出记录。
            self.task_registry.append_output(command_id, combined_output + "\n")  # 新增代码+DurableTaskRegistry: 把后台命令增量输出写入 task output；若没有这行代码，poller/status 看不到后台输出。
        if record.process.poll() is not None:  # 新增代码+DurableTaskRegistry: 如果后台命令已经退出；若没有这行代码，持久任务会一直显示 running。
            final_tail = self.task_registry.output_store.tail(command_id, max_chars=4000)  # 新增代码+DurableTaskRegistry: 读取最终输出尾部摘要；若没有这行代码，完成通知缺少结果上下文。
            if record.process.returncode == 0:  # 新增代码+DurableTaskRegistry: 退出码 0 视为完成；若没有这行代码，成功命令也会被误判失败。
                self.task_registry.complete_task(command_id, output=final_tail, usage={})  # 新增代码+DurableTaskRegistry: 持久标记后台命令完成并通知；若没有这行代码，后台命令结束不会自动回灌。
            else:  # 新增代码+DurableTaskRegistry: 非 0 退出码视为失败；若没有这行代码，失败命令会误显示完成。
                self.task_registry.fail_task(command_id, f"后台命令退出码：{record.process.returncode}")  # 新增代码+DurableTaskRegistry: 持久标记后台命令失败并通知；若没有这行代码，失败状态无法审计。
        return f"read_background_command 成功：command_id={command_id}\n状态：{self._background_command_status(record)}\nstdout:\n{stdout_text or '(无新增输出)'}\nstderr:\n{stderr_text or '(无新增输出)'}"  # 新增代码+后台命令: 返回状态和增量输出；若省略: 模型无法根据命令结果继续推理

    def _stop_background_command(self, arguments: dict[str, Any]) -> str:  # 新增代码+后台命令: 停止后台命令并返回最终增量输出；若省略: 长任务无法由 agent 收束
        command_id = str(arguments.get("command_id", "")).strip()  # 新增代码+后台命令: 读取要停止的 command_id；若省略: 工具不知道停止哪个进程
        if not command_id:  # 新增代码+后台命令: 检查 command_id 是否为空；若省略: 空 id 会变成未知命令错误
            return "stop_background_command 失败：缺少 command_id 参数。"  # 新增代码+后台命令: 返回缺参提示；若省略: 模型难以修正调用
        record = self.background_commands.get(command_id)  # 新增代码+后台命令: 查找目标后台命令记录；若省略: 无法访问进程对象
        if record is None:  # 新增代码+后台命令: 如果 id 不存在；若省略: 后续访问 None 会报错
            return f"stop_background_command 失败：未知 command_id：{command_id}"  # 新增代码+后台命令: 返回未知 id 错误；若省略: 模型不知道该检查 id
        action = f"停止后台命令：{command_id}\n命令：{record.command}\n工作目录：{record.cwd}"  # 新增代码+后台命令: 构造停止权限说明；若省略: 用户无法确认要停止哪个命令
        if not self.ask_permission(action):  # 新增代码+后台命令: 停止进程前请求用户确认；若省略: agent 可能擅自停止用户关心的进程
            return f"用户拒绝了操作：{action}"  # 新增代码+后台命令: 权限拒绝时返回可读结果；若省略: 模型不知道进程仍在运行
        record.stop_requested = True  # 新增代码+BackgroundAutoNotify: 标记用户停止流程已经接管该命令；若没有这行代码，监控线程可能把 stop 误判成异常失败
        if record.process.poll() is None:  # 新增代码+后台命令: 如果进程仍在运行；若省略: 已退出进程也会重复 terminate
            self._terminate_background_process(record.process)  # 修改代码+后台命令: 停止整个后台进程树；若省略: Windows shell 子进程可能继续占用工作目录
        self._join_background_reader_threads(record, 0.5)  # 修改代码+后台命令: 先给 reader 线程短暂时间自然读到 EOF；若没有这行代码，刚结束的进程输出可能还没进入队列
        self._close_background_process_streams(record.process)  # 修改代码+后台命令: 主动关闭后台进程管道句柄；若没有这行代码，Windows 可能延迟释放和临时目录相关的子进程资源
        self._join_background_reader_threads(record, 1.0)  # 修改代码+后台命令: 关闭管道后再次等待 reader 线程退出；若没有这行代码，测试清理临时目录时仍可能遇到句柄占用
        stdout_text = self._drain_text_queue(record.stdout_lines, 4000)  # 新增代码+后台命令: 停止后读取剩余 stdout；若省略: 最后一段输出会丢失
        stderr_text = self._drain_text_queue(record.stderr_lines, 4000)  # 新增代码+后台命令: 停止后读取剩余 stderr；若省略: 最后一段错误输出会丢失
        combined_output = "\n".join(part for part in [stdout_text, stderr_text] if part)  # 新增代码+DurableTaskRegistry: 合并停止时剩余输出；若没有这行代码，后台命令最后一段输出无法落盘。
        if combined_output:  # 新增代码+DurableTaskRegistry: 有剩余输出时才追加；若没有这行代码，空停止会生成噪音记录。
            self.task_registry.append_output(command_id, combined_output + "\n")  # 新增代码+DurableTaskRegistry: 保存停止前最后输出；若没有这行代码，task output 会缺尾部证据。
        self.task_registry.stop_task(command_id, "后台命令已被 stop_background_command 停止。")  # 新增代码+DurableTaskRegistry: 把后台命令停止状态写入持久任务表；若没有这行代码，状态 CLI 仍会显示 running。
        return f"stop_background_command 成功：command_id={command_id}\n状态：{self._background_command_status(record)}\nstdout:\n{stdout_text or '(无新增输出)'}\nstderr:\n{stderr_text or '(无新增输出)'}"  # 新增代码+后台命令: 返回停止结果和最终输出；若省略: 模型无法确认进程已收束

    def _terminate_background_process(self, process: subprocess.Popen[str]) -> None:  # 新增代码+后台命令: 终止后台进程及其子进程；若省略: shell 启动的子进程可能残留
        if os.name == "nt":  # 新增代码+后台命令: Windows 需要按进程树终止 shell 子进程；若省略: cmd/powershell 子进程可能继续运行
            try:  # 修改代码+后台命令: 先向独立进程组发送 Ctrl+Break；若没有这行代码，taskkill 被拒绝时只能杀外层 shell
                process.send_signal(signal.CTRL_BREAK_EVENT)  # 修改代码+后台命令: 请求 shell 和子进程一起退出；若没有这行代码，Python 子进程可能继续占用临时工作目录
                process.wait(timeout=3)  # 修改代码+后台命令: 等待 Ctrl+Break 生效；若没有这行代码，stop 可能在子进程退出前过早继续
                return  # 修改代码+后台命令: Ctrl+Break 成功后直接返回；若没有这行代码，还会继续走更强制的 taskkill 分支
            except (OSError, ValueError, subprocess.TimeoutExpired):  # 修改代码+后台命令: 处理进程已退出、信号不可用或等待超时；若没有这行代码，温和终止失败会让 stop 工具报错
                pass  # 修改代码+后台命令: 温和终止失败后继续使用后备强制路径；若没有这行代码，except 分支语法不完整
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")  # 新增代码+后台命令: 调用 taskkill 强制结束进程树；若省略: Windows 临时目录可能被子进程长期占用
            try:  # 新增代码+后台命令: 等待 Popen 记录的外层进程退出；若省略: 进程句柄可能未回收
                process.wait(timeout=3)  # 新增代码+后台命令: 给系统最多 3 秒回收进程；若省略: stop 工具可能过早返回
            except subprocess.TimeoutExpired:  # 新增代码+后台命令: 如果 taskkill 后外层进程仍未退出；若省略: 极端情况下会抛异常中断 stop
                process.kill()  # 新增代码+后台命令: 对外层进程再执行一次 kill；若省略: 进程句柄可能继续存在
                process.wait(timeout=3)  # 新增代码+后台命令: 回收被 kill 的外层进程；若省略: 可能留下句柄
            return  # 新增代码+后台命令: Windows 分支处理完成后返回；若省略: 还会继续执行通用 terminate 分支
        process.terminate()  # 新增代码+后台命令: 非 Windows 平台先温和请求进程退出；若省略: 长任务可能继续运行
        try:  # 新增代码+后台命令: 等待进程正常退出；若省略: terminate 后可能没有回收进程
            process.wait(timeout=3)  # 新增代码+后台命令: 给进程最多 3 秒退出；若省略: stop 工具可能无限等待
        except subprocess.TimeoutExpired:  # 新增代码+后台命令: 如果进程没有及时响应 terminate；若省略: 不响应进程会卡住工具
            process.kill()  # 新增代码+后台命令: 强制结束不响应的后台进程；若省略: 进程可能残留
            process.wait(timeout=3)  # 新增代码+后台命令: 回收被 kill 的进程；若省略: 可能留下僵尸或句柄

    def _close_background_process_streams(self, process: subprocess.Popen[str]) -> None:  # 修改代码+后台命令: 关闭后台进程 stdio 管道；若没有这行代码，停止命令后 reader 线程和系统句柄可能延迟释放
        for stream in (process.stdin, process.stdout, process.stderr):  # 修改代码+后台命令: 遍历标准输入、输出和错误三个可能存在的管道；若没有这行代码，清理逻辑会遗漏某类管道
            if stream is None or stream.closed:  # 修改代码+后台命令: 跳过不存在或已经关闭的管道；若没有这行代码，重复关闭会增加无意义异常
                continue  # 修改代码+后台命令: 当前管道无需处理时进入下一个；若没有这行代码，后续 close 会作用在空对象上
            try:  # 修改代码+后台命令: 捕获关闭管道时的系统异常；若没有这行代码，单个管道关闭失败会中断 stop 工具
                stream.close()  # 修改代码+后台命令: 释放管道句柄；若没有这行代码，Windows 可能认为后台命令资源仍被占用
            except Exception:  # 修改代码+后台命令: 忽略关闭期间的低层异常；若没有这行代码，已结束进程的管道清理可能把 stop 变成失败
                pass  # 修改代码+后台命令: 保持清理过程尽力而为；若没有这行代码，except 分支语法不完整

    def _join_background_reader_threads(self, record: BackgroundCommand, timeout_seconds: float) -> None:  # 修改代码+后台命令: 等待后台输出 reader 线程收尾；若没有这行代码，stop 返回时线程可能仍在读取管道
        for reader_thread in (record.stdout_thread, record.stderr_thread):  # 修改代码+后台命令: 同时处理 stdout 和 stderr reader；若没有这行代码，只清理一个方向的输出仍可能泄漏
            if reader_thread is None:  # 修改代码+后台命令: 兼容旧记录或启动失败时没有线程对象的情况；若没有这行代码，None 会触发属性错误
                continue  # 修改代码+后台命令: 没有线程就进入下一个；若没有这行代码，清理逻辑无法兼容空线程
            if not reader_thread.is_alive():  # 修改代码+后台命令: 已退出线程不需要等待；若没有这行代码，stop 会做多余 join
                continue  # 修改代码+后台命令: 跳过已结束线程；若没有这行代码，清理等待会增加不必要耗时
            reader_thread.join(timeout=timeout_seconds)  # 修改代码+后台命令: 等待线程在限定时间内退出；若没有这行代码，stop 工具可能在 Windows 上过早返回导致临时目录无法删除

    def _parse_max_chars(self, raw_value: Any) -> int:  # 新增代码+后台命令: 解析 read_background_command 的 max_chars；若省略: 输出长度控制会散落在读取逻辑中
        try:  # 新增代码+后台命令: 捕获无法转成整数的输入；若省略: 模型传错 max_chars 会让工具崩溃
            value = int(raw_value) if raw_value is not None else 4000  # 新增代码+后台命令: None 时使用默认 4000；若省略: 未传 max_chars 时无法确定截断长度
        except (TypeError, ValueError):  # 新增代码+后台命令: 处理非数字输入；若省略: ValueError 会中断 agent.run
            value = 4000  # 新增代码+后台命令: 错误输入回退默认值；若省略: 模型一次小错会导致工具失败
        return max(200, min(value, 20000))  # 新增代码+后台命令: 限制输出长度范围；若省略: 过小或过大值会影响可读性或上下文安全

    def _drain_text_queue(self, output_queue: queue.Queue[str], max_chars: int) -> str:  # 新增代码+后台命令: 非阻塞读取队列中的增量文本；若省略: read/stop 无法复用输出读取逻辑
        return drain_text_queue(output_queue, max_chars)  # 修改代码+TasksSplit: 委托 tasks.background 读取后台输出队列；若没有这行代码，后台输出截断规则仍留在主文件。

    def _background_command_status(self, record: BackgroundCommand) -> str:  # 修改代码+Stage14硬清理: 恢复后台命令状态 helper 的独立函数边界；若没有这行代码，read/stop/start 的状态格式会在主流程里散落
        return background_command_status(record)  # 修改代码+Stage14硬清理: 委托 tasks.background 统一格式化后台进程状态；若没有这行代码，后台命令状态规则会重新堆回 core.agent

    def _resolve_workspace_path(self, raw_path: str) -> Path | None:  # 修改代码+Stage14硬清理: 恢复工作区路径解析函数入口；若没有这行代码，read/write/edit 会缺少安全路径边界
        normalized_raw_path = raw_path.strip().replace("\\", "/")  # 新增代码+路径兼容: 统一清理空白和 Windows 反斜杠；若没有这行代码，learning_agent\skills 写法无法触发兼容分支
        path = Path(normalized_raw_path).expanduser()  # 修改代码+路径兼容: 用规范化后的文本构造路径并展开 ~；若没有这行代码，后续绝对路径和相对路径判断没有对象
        if not path.is_absolute():  # 修改代码+路径兼容: 如果模型给的是相对路径；若没有这行代码，相对路径不会落到当前工作区下
            if self.workspace.name.lower() == "learning_agent" and normalized_raw_path.lower().startswith("learning_agent/"):  # 新增代码+路径兼容: 工作区已是包目录时接受项目根风格路径；若没有这行代码，静态提示词里的 learning_agent/skills/tool_list.md 在 CLI 下会失败
                path = self.workspace / normalized_raw_path[len("learning_agent/") :]  # 新增代码+路径兼容: 去掉多余的 learning_agent 前缀再拼到包目录；若没有这行代码，路径会错误变成 learning_agent/learning_agent/skills
            else:  # 新增代码+路径兼容: 其他相对路径仍按原有工作区相对路径处理；若没有这行代码，普通文件读取路径会丢失默认分支
                path = self.workspace / path  # 修改代码+路径兼容: 视为相对于工作区的路径；若没有这行代码，read/write/edit 会找不到相对文件
        resolved = path.resolve()  # 修改代码+路径兼容: 解析成绝对路径并消除 ..；若没有这行代码，路径越界检查可能被绕过
        try:  # 修改代码+路径兼容: 检查 resolved 是否位于 workspace 内；若没有这行代码，模型可能读取或写入工作区外文件
            resolved.relative_to(self.workspace)  # 修改代码+路径兼容: 不在工作区内会抛 ValueError；若没有这行代码，安全边界没有实际判断
        except ValueError:  # 修改代码+路径兼容: 捕获越界路径；若没有这行代码，越界会抛异常而不是返回可读失败
            return None  # 修改代码+路径兼容: 返回 None 表示路径不安全；若没有这行代码，调用方无法统一处理越界
        return resolved  # 修改代码+路径兼容: 返回安全绝对路径；若没有这行代码，工具无法继续读写目标文件


def build_permission_event_payload(action: str) -> dict[str, Any]:  # 新增代码+StructuredPermissionLedger: 将人类可读权限文本转成可审计 payload；若没有这行代码，外部 controller 只能靠字符串 contains 判断权限
    return build_permission_event_payload_from_observability(action)  # 修改代码+ObservabilitySplit: 委托观测层生成权限事件 payload；若没有这行代码，权限解析仍会堆在主入口文件里。


def _customer_mode_can_auto_approve_terminal_permission(permission_payload: dict[str, Any]) -> bool:  # 新增代码+真实浏览器客户模式: 判断终端客户模式是否能自动允许本次权限；若没有这行代码，启动 MCP 仍会要求用户输入 y
    return customer_mode_can_auto_approve_terminal_permission(permission_payload)  # 修改代码+BrowserSplit: 委托 browser.permissions 判断终端客户模式启动授权；若没有这行代码，MCP 启动白名单仍会留在主文件里。


def _emit_permission_auto_approved(action: str, permission_payload: dict[str, Any], reason: str) -> None:  # 新增代码+真实浏览器客户模式: 统一发送自动授权审计事件；若没有这行代码，默认放行会缺少可追踪记录
    auto_payload = dict(permission_payload)  # 新增代码+真实浏览器客户模式: 复制权限 payload，避免修改调用方持有的对象；若没有这行代码，后续复用 payload 可能被意外污染
    auto_payload["action"] = action  # 新增代码+真实浏览器客户模式: 明确保留原始动作文本；若没有这行代码，审计事件可能缺少用户可读上下文
    auto_payload["allowed"] = True  # 新增代码+真实浏览器客户模式: 标记本次自动授权结果为允许；若没有这行代码，controller 无法判断自动授权方向
    auto_payload["auto_approved"] = True  # 新增代码+真实浏览器客户模式: 标记这不是用户手工输入 y；若没有这行代码，复盘时会误以为用户回答过
    auto_payload["reason"] = reason  # 新增代码+真实浏览器客户模式: 写入自动授权原因；若没有这行代码，审计无法解释为什么放行
    emit_acceptance_event("permission_auto_approved", auto_payload)  # 新增代码+真实浏览器客户模式: 写入验收事件但不触发 permission_required；若没有这行代码，控制器无法证明无 y 模式生效


def ask_permission_from_terminal(action: str) -> bool:  # 作用: 命令行版本的权限确认函数
    permission_payload = build_permission_event_payload(action)  # 新增代码+StructuredPermissionLedger: 生成结构化权限 payload；若没有这行代码，permission_required 事件只有 action 文本
    if dangerously_skip_permissions_enabled():  # 新增代码+危险调试权限: 危险调试模式下不再等待用户输入 y/N；若没有这行代码，真实浏览器调试会被权限焦点反复打断
        target = str(permission_payload.get("tool_name") or permission_payload.get("permission_kind") or "terminal_permission")  # 新增代码+危险调试权限: 生成本次自动允许的对象名称；若没有这行代码，审计原因无法指出放行了哪类权限
        _emit_permission_auto_approved(action, permission_payload, dangerously_skip_permission_reason(target))  # 新增代码+危险调试权限: 写入自动授权事件而不是 permission_required；若没有这行代码，控制器无法证明危险模式没有人工输入
        return True  # 新增代码+危险调试权限: 直接允许本次操作继续执行；若没有这行代码，危险模式开关不会真正跳过权限
    emit_acceptance_event("permission_required", permission_payload)  # 修改代码+StructuredPermissionLedger: 在等待用户授权前写结构化状态事件；若没有这行代码，外部 agent 无法按工具名和 URL 参数精确授权
    answer = input(f"允许 agent 执行这个操作吗？\n{action}\n[y/N] ").strip().lower()  # 修改代码+权限分级: 把多行风险提示放在独立行显示；若省略: 工具名、风险等级和参数会挤在同一行不利于用户核对
    allowed = answer in {"y", "yes"}  # 新增代码+AcceptanceHarness: 把是否允许保存成变量；若没有这行代码，后续事件和返回值容易写出不一致判断
    answered_payload = dict(permission_payload)  # 新增代码+StructuredPermissionLedger: 复制待授权 payload 作为回答事件基础；若没有这行代码，permission_answered 会丢失 tool_name 和 arguments
    answered_payload["allowed"] = allowed  # 新增代码+StructuredPermissionLedger: 把用户是否允许写入回答事件；若没有这行代码，controller 无法确认 y/n 结果
    emit_acceptance_event("permission_answered", answered_payload)  # 修改代码+StructuredPermissionLedger: 在用户回答后写结构化结果事件；若没有这行代码，外部 agent 无法把 y/n 对应到具体工具和参数
    return allowed  # 修改代码+AcceptanceHarness: 返回统一计算出的授权结果；若没有这行代码，权限函数无法保持原有布尔语义


def ask_permission_from_terminal_customer_mode(action: str, show_progress: bool = True) -> bool:  # 修改代码+真实浏览器客户模式: 客户可见终端默认权限入口，允许 JSON 模式关闭进度输出；若没有这行代码，main() 只能继续使用原人工确认函数或污染 JSON 输出
    permission_payload = build_permission_event_payload(action)  # 新增代码+真实浏览器客户模式: 解析权限动作供白名单判断；若没有这行代码，无法知道本次是不是项目 MCP 启动
    if dangerously_skip_permissions_enabled():  # 新增代码+危险调试权限: 危险模式优先于客户白名单，所有权限都自动允许；若没有这行代码，非 MCP 启动权限仍可能弹出 y/N
        target = str(permission_payload.get("tool_name") or permission_payload.get("permission_kind") or "terminal_permission")  # 新增代码+危险调试权限: 读取工具名或权限类型供审计；若没有这行代码，自动授权原因会太模糊
        _emit_permission_auto_approved(action, permission_payload, dangerously_skip_permission_reason(target))  # 新增代码+危险调试权限: 写入危险模式自动授权事件；若没有这行代码，真实验收无法确认权限是自动放开的
        if show_progress:  # 新增代码+危险调试权限: 只在真实人类终端展示危险模式提示；若没有这行代码，--output-json 可能被进度文本污染
            print("Agent > 危险调试模式已开启，本次权限请求已自动允许。", flush=True)  # 新增代码+危险调试权限: 明确告诉用户当前是全放开调试模式；若没有这行代码，用户可能误以为仍在普通安全模式
        return True  # 新增代码+危险调试权限: 直接允许本次权限请求；若没有这行代码，危险模式不会覆盖客户模式以外的权限
    if _customer_mode_can_auto_approve_terminal_permission(permission_payload):  # 新增代码+真实浏览器客户模式: 判断是否命中客户模式启动白名单；若没有这行代码，启动 MCP 仍会弹 y/N
        _emit_permission_auto_approved(action, permission_payload, "客户模式默认启动项目内置 MCP server")  # 新增代码+真实浏览器客户模式: 记录自动启动审计事件；若没有这行代码，默认放行缺少证据
        if show_progress:  # 新增代码+真实浏览器客户模式: 只有人类可见终端才打印进度；若没有这行代码，--output-json 会混入普通文本导致机器解析失败
            print("Agent > 正在启动 MCP 工具...", flush=True)  # 新增代码+真实浏览器客户模式: 用进度提示替代 y/N 提示；若没有这行代码，用户不知道 agent 正在启动工具
        return True  # 新增代码+真实浏览器客户模式: 返回允许启动；若没有这行代码，LearningAgent 会认为用户拒绝 MCP
    return ask_permission_from_terminal(action)  # 新增代码+真实浏览器客户模式: 未命中白名单时保留原人工授权流程；若没有这行代码，敏感或未知权限没有安全兜底


def format_cli_run_response(answer: str, output_json: bool, workspace: Path, visible_tools: list[str], max_turns: int | None = None) -> str:  # 新增代码+CLI接口: 统一格式化一次性 CLI 运行结果；若没有这行代码，Codex 和人类模式会各自拼输出导致不稳定
    return format_cli_run_response_from_app(answer=answer, output_json=output_json, workspace=workspace, visible_tools=visible_tools, max_turns=max_turns)  # 修改代码+AppSplit: 委托 app.cli 格式化 CLI 输出；若没有这行代码，JSON 输出结构仍会散在主文件。


def create_command_bridge_server(agent: LearningAgent, host: str = "127.0.0.1", port: int = 8765, token: str = "", max_turns: int | None = None) -> LearningAgentCommandBridgeServer:  # 新增代码+CommandBridge: 创建可测试和可启动的 HTTP bridge server；若没有这行代码，main 和单测都要重复 server 构造
    return create_command_bridge_server_from_app(agent=agent, host=host, port=port, token=token, max_turns=max_turns)  # 修改代码+AppSplit: 委托 app.http_bridge 创建 server；若没有这行代码，HTTP bridge 仍会使用主文件旧实现。


def main() -> None:  # 作用: 命令行入口函数
    app_cli_main(agent_cls=LearningAgent, permission_callback=ask_permission_from_terminal_customer_mode)  # 修改代码+AppSplit: 把 CLI/doctor/bridge/交互入口转发到 app.cli；若没有这行代码，启动逻辑会继续堆在 learning_agent.py。
    return  # 修改代码+AppSplit: app.cli 完成命令处理后直接返回；若没有这行代码，转发后还会继续执行旧入口逻辑造成重复启动。


if __name__ == "__main__":  # 作用: 只有直接运行本文件时才进入命令行模式
    main()  # 作用: 调用命令行入口函数

