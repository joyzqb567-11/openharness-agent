"""CLI 应用入口，统一处理 doctor、run、HTTP bridge 和交互式终端模式。"""  # 新增代码+AppSplit: 说明本模块承载命令行入口；若没有这行代码，启动逻辑仍会堆在 learning_agent.py。
from __future__ import annotations  # 新增代码+AppSplit: 允许类型注解延迟解析；若没有这行代码，类型提示在部分运行顺序下可能提前求值。

import json  # 新增代码+AppSplit: 输出 CLI JSON 响应和错误；若没有这行代码，Codex 无法稳定解析一次性运行结果。
import os  # 新增代码+AppSplit: 读取模型 provider 环境变量；若没有这行代码，用户无法通过环境切换 OpenAI/Codex 模型。
import sys  # 新增代码+AppSplit: 读取命令行 argv；若没有这行代码，CLI 无法解析用户传入的子命令。
from pathlib import Path  # 新增代码+AppSplit: 定位 learning_agent 工作区；若没有这行代码，mcp_servers.json 和 memory 路径会不稳定。
from typing import Any, Callable  # 新增代码+AppSplit: 标注 agent 类和权限回调；若没有这行代码，依赖注入接口不清楚。

try:  # 新增代码+AppSplit: 优先按包路径导入 app/core/models/mcp 依赖；若没有这行代码，包运行模式下 CLI 无法复用已拆分层。
    from learning_agent.app.doctor import run_mcp_doctor  # 新增代码+AppSplit: 导入 app 层 doctor 入口；若没有这行代码，doctor 命令仍会绑在主文件。
    from learning_agent.app.http_bridge import create_command_bridge_server, serve_command_bridge  # 新增代码+AppSplit: 导入 HTTP bridge 创建和运行 helper；若没有这行代码，bridge 生命周期仍散在 CLI 里。
    from learning_agent.app.interactive import run_interactive_session  # 新增代码+AppSplit: 导入交互式终端循环；若没有这行代码，CLI 无法进入人类可见交互模式。
    import learning_agent.app.terminal_permissions as terminal_permissions_from_app  # 修改代码+AgentPyPhaseJTerminalPermissions: 包运行模式下导入终端权限默认回调；若没有这行代码，app.cli 会继续从 core.agent 取权限函数。
    from learning_agent.core.config import load_agent_runtime_config, parse_main_args, resolve_run_max_turns  # 新增代码+AppSplit: 导入运行配置解析；若没有这行代码，CLI 无法读取 runtime_config 或 --max-turns。
    from learning_agent.models.codex_cli import CodexCliChatModel  # 新增代码+AppSplit: 导入 Codex CLI 模型适配器；若没有这行代码，LEARNING_AGENT_MODEL_PROVIDER=codex 会失效。
    from learning_agent.models.codex_oauth import CodexOAuthChatModel  # 新增代码+AppSplit: 导入 Codex OAuth 模型适配器；若没有这行代码，OAuth/API 模式会失效。
    from learning_agent.models.openai_chat import OpenAIChatModel  # 新增代码+AppSplit: 导入默认 OpenAI-compatible 模型；若没有这行代码，默认模型入口会失效。
    from learning_agent.mcp.config import format_mcp_startup_status, load_mcp_server_configs  # 新增代码+AppSplit: 导入 MCP 配置读取和启动提示；若没有这行代码，CLI 无法加载 mcp_servers.json。
    from learning_agent.mcp.registry import McpToolRegistry  # 新增代码+AppSplit: 导入 MCP 工具注册表；若没有这行代码，外部 MCP 工具无法进入 agent。
    import learning_agent.tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 导入工具池名称运行时；若没有这行代码，CLI 仍会通过 agent.py 薄包装展示 visible_tools。
except ModuleNotFoundError as error:  # 新增代码+AppSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 启动可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.app", "learning_agent.app.doctor", "learning_agent.app.http_bridge", "learning_agent.app.interactive", "learning_agent.app.terminal_permissions", "learning_agent.core", "learning_agent.core.config", "learning_agent.models", "learning_agent.models.codex_cli", "learning_agent.models.codex_oauth", "learning_agent.models.openai_chat", "learning_agent.mcp", "learning_agent.mcp.config", "learning_agent.mcp.registry", "learning_agent.tools", "learning_agent.tools.catalog_runtime"}:  # 修改代码+AgentPyPhaseJTerminalPermissions: 允许 terminal_permissions 路径差异进入 fallback；若没有这行代码，直接脚本模式可能找不到新权限模块。
        raise  # 新增代码+AppSplit: 重新抛出真实依赖错误；若没有这行代码，导入问题会被伪装成脚本模式。
    from app.doctor import run_mcp_doctor  # 新增代码+AppSplit: 脚本模式从同目录 app 包导入 doctor；若没有这行代码，直接运行时诊断命令会断开。
    from app.http_bridge import create_command_bridge_server, serve_command_bridge  # 新增代码+AppSplit: 脚本模式导入 HTTP bridge helper；若没有这行代码，直接运行时 bridge 会断开。
    from app.interactive import run_interactive_session  # 新增代码+AppSplit: 脚本模式导入交互式终端循环；若没有这行代码，直接运行时交互模式会断开。
    import app.terminal_permissions as terminal_permissions_from_app  # 修改代码+AgentPyPhaseJTerminalPermissions: 脚本模式下导入终端权限默认回调；若没有这行代码，start_oauth_agent.bat 无法使用拆出的权限模块。
    from core.config import load_agent_runtime_config, parse_main_args, resolve_run_max_turns  # 新增代码+AppSplit: 脚本模式导入运行配置解析；若没有这行代码，CLI 参数无法解析。
    from models.codex_cli import CodexCliChatModel  # 新增代码+AppSplit: 脚本模式导入 Codex CLI 模型适配器；若没有这行代码，codex provider 会失效。
    from models.codex_oauth import CodexOAuthChatModel  # 新增代码+AppSplit: 脚本模式导入 Codex OAuth 模型适配器；若没有这行代码，OAuth provider 会失效。
    from models.openai_chat import OpenAIChatModel  # 新增代码+AppSplit: 脚本模式导入默认 OpenAI-compatible 模型；若没有这行代码，默认模型入口会失效。
    from mcp.config import format_mcp_startup_status, load_mcp_server_configs  # 新增代码+AppSplit: 脚本模式导入 MCP 配置 helper；若没有这行代码，mcp_servers.json 不会被加载。
    from mcp.registry import McpToolRegistry  # 新增代码+AppSplit: 脚本模式导入 MCP 工具注册表；若没有这行代码，外部 MCP 工具无法进入 agent。
    import tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入工具池名称运行时；若没有这行代码，bat 入口 CLI visible_tools 会断开。


def build_model_from_env(workspace: str | Path) -> Any:  # 新增代码+AppSplit: 根据环境变量选择真实模型来源；若没有这行代码，CLI 无法统一构造 OpenAI/Codex 模型。
    provider = os.environ.get("LEARNING_AGENT_MODEL_PROVIDER", "openai").strip().lower()  # 新增代码+AppSplit: 读取模型提供方式；若没有这行代码，用户无法通过环境变量切换模型链路。
    if provider in {"codex-oauth", "codex_oauth", "oauth", "openai-oauth"}:  # 新增代码+AppSplit: 识别 OAuth/API 直连模式；若没有这行代码，网页 OAuth 登录模式不会被选中。
        return CodexOAuthChatModel.from_env()  # 新增代码+AppSplit: 返回 OAuth/API 模型适配器；若没有这行代码，OAuth 模式无法调用模型。
    if provider in {"codex", "codex-cli", "codex_cli"}:  # 新增代码+AppSplit: 识别 Codex CLI 桥接模式；若没有这行代码，用户无法复用本机 codex exec。
        return CodexCliChatModel.from_env(cwd=workspace)  # 新增代码+AppSplit: 返回 Codex CLI 模型适配器；若没有这行代码，CLI provider 没有工作目录。
    return OpenAIChatModel.from_env()  # 新增代码+AppSplit: 默认返回 OpenAI-compatible 模型适配器；若没有这行代码，普通 API key 模式无法启动。


def format_cli_run_response(answer: str, output_json: bool, workspace: Path, visible_tools: list[str], max_turns: int | None = None) -> str:  # 新增代码+AppSplit: 统一格式化一次性 CLI 运行结果；若没有这行代码，Codex 和人类模式会各自拼输出导致不稳定。
    if not output_json:  # 新增代码+AppSplit: 判断是否需要人类可读输出；若没有这行代码，普通 CLI 用户也会被迫读取 JSON。
        return answer  # 新增代码+AppSplit: 人类模式直接返回最终回答；若没有这行代码，交互体验会变差。
    payload = {  # 新增代码+AppSplit: 构造机器可读结果对象；若没有这行代码，Codex 无法稳定读取字段。
        "ok": True,  # 新增代码+AppSplit: 标记本次 CLI run 成功；若没有这行代码，外部控制器需要猜测命令状态。
        "answer": answer,  # 新增代码+AppSplit: 保存 agent 最终回答；若没有这行代码，Codex 收不到核心输出。
        "workspace": str(workspace),  # 新增代码+AppSplit: 保存工作区路径；若没有这行代码，外部控制器无法确认控制的是哪个 agent。
        "visible_tools": visible_tools,  # 新增代码+AppSplit: 保存模型当前可见工具；若没有这行代码，调试时无法确认四原子工具面。
        "max_turns": max_turns,  # 新增代码+AppSplit: 保存本次工具循环上限；若没有这行代码，外部控制器无法确认运行策略。
    }  # 新增代码+AppSplit: 结束结果对象；若没有这行代码，Python 字典语法不完整。
    return json.dumps(payload, ensure_ascii=False)  # 新增代码+AppSplit: 输出 UTF-8 友好的 JSON 字符串；若没有这行代码，中文回答会被不必要转义或不可解析。


def _resolve_agent_dependencies(agent_cls: type[Any] | None, permission_callback: Callable[..., bool] | None) -> tuple[type[Any], Callable[..., bool]]:  # 新增代码+AppSplit: 解析 CLI 所需的 agent 类和权限回调；若没有这行代码，app.cli 直接导入主文件会形成循环依赖。
    if agent_cls is not None and permission_callback is not None:  # 新增代码+AppSplit: 调用方已显式注入依赖时直接使用；若没有这行代码，learning_agent.py 转发入口会被迫再次导入自己。
        return agent_cls, permission_callback  # 新增代码+AppSplit: 返回注入依赖；若没有这行代码，脚本入口无法避免循环导入。
    try:  # 修改代码+AgentPyPhaseJTerminalPermissions: 独立调用 app.cli.main 时只从 core.agent 读取主类；若没有这行代码，CLI 会继续把权限回调绑回 agent.py。
        from learning_agent.core.agent import LearningAgent  # 修改代码+AgentPyPhaseJTerminalPermissions: 导入核心 agent 主类但不导入权限函数；若没有这行代码，直接调用 app.cli.main 没有可运行对象。
    except ModuleNotFoundError as error:  # 修改代码+ToolSchemaSplit: 捕获脚本模式下包名不可用；若没有这行代码，直接运行路径可能导入失败。
        if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.agent"}:  # 修改代码+ToolSchemaSplit: 只允许目标路径缺失时 fallback；若没有这行代码，core 内部 bug 会被误吞。
            raise  # 修改代码+ToolSchemaSplit: 重新抛出真实导入错误；若没有这行代码，真实问题会被隐藏。
        from core.agent import LearningAgent  # 修改代码+AgentPyPhaseJTerminalPermissions: 脚本模式兜底只导入核心 agent 主类；若没有这行代码，app.cli 直接运行时没有 agent 类。
    return LearningAgent, terminal_permissions_from_app.ask_permission_from_terminal_customer_mode  # 修改代码+AgentPyPhaseJTerminalPermissions: 返回 app 层权限回调而不是 agent.py 薄包装；若没有这行代码，CLI 会继续依赖主入口权限实现。


def main(agent_cls: type[Any] | None = None, permission_callback: Callable[..., bool] | None = None, argv: list[str] | None = None) -> None:  # 新增代码+AppSplit: CLI 主入口；若没有这行代码，app 包没有可调用的主命令入口。
    workspace = Path(__file__).resolve().parent.parent  # 新增代码+AppSplit: 默认把 learning_agent 文件夹作为工作区；若没有这行代码，MCP 配置和 memory 路径会跑偏。
    resolved_agent_cls, resolved_permission_callback = _resolve_agent_dependencies(agent_cls, permission_callback)  # 新增代码+AppSplit: 解析 agent 类和权限回调；若没有这行代码，CLI 无法创建真实 agent。
    main_args = parse_main_args(sys.argv[1:] if argv is None else argv)  # 新增代码+AppSplit: 统一解析 doctor、run、bridge 和交互参数；若没有这行代码，CLI 命令无法进入对应分支。
    if main_args.command in {"mcp-doctor", "doctor"}:  # 新增代码+AppSplit: 判断是否是诊断模式；若没有这行代码，doctor 后还会继续启动模型和交互循环。
        print(run_mcp_doctor(workspace))  # 新增代码+AppSplit: 打印 MCP 配置、启动和工具可见性报告；若没有这行代码，用户无法从命令行看到诊断结果。
        return  # 新增代码+AppSplit: 诊断完成后退出；若没有这行代码，doctor 会继续创建模型。
    try:  # 新增代码+AppSplit: 捕获 runtime_config.json 或环境变量配置错误；若没有这行代码，配置写错会显示不友好的 traceback。
        runtime_config = load_agent_runtime_config(workspace)  # 新增代码+AppSplit: 加载配置文件和环境变量里的轮次策略；若没有这行代码，max_turns 只能写在代码里。
        max_turns = resolve_run_max_turns(runtime_config, main_args)  # 新增代码+AppSplit: 计算最终传给 agent.run 的轮次策略；若没有这行代码，CLI 与配置文件优先级不明确。
    except ValueError as error:  # 新增代码+AppSplit: 处理配置解析失败；若没有这行代码，用户看到底层异常不利于学习。
        print(f"运行配置错误：{error}")  # 新增代码+AppSplit: 打印中文配置错误；若没有这行代码，用户不知道该修哪里。
        return  # 新增代码+AppSplit: 配置错误时停止启动；若没有这行代码，agent 可能带着错误策略继续运行。
    model = build_model_from_env(workspace)  # 新增代码+AppSplit: 根据环境变量选择模型适配器；若没有这行代码，CLI 没有模型可用。
    mcp_configs = load_mcp_server_configs(workspace)  # 新增代码+AppSplit: 从工作区读取 mcp_servers.json；若没有这行代码，CLI 启动时不会发现用户配置的 MCP server。
    quiet_json_run = main_args.command in {"run", "once", "command"} and main_args.output_json  # 新增代码+AppSplit: JSON 一次性运行时保持 stdout 干净；若没有这行代码，Codex 解析 JSON 会被启动提示污染。
    if not quiet_json_run:  # 新增代码+AppSplit: 人类交互和 bridge 模式仍显示启动状态；若没有这行代码，用户看不到 MCP 配置提示。
        print(format_mcp_startup_status(workspace, mcp_configs))  # 新增代码+AppSplit: 启动时显示 MCP 配置状态；若没有这行代码，用户不知道本轮是否会加载外部 MCP 工具。
    mcp_tool_registry = McpToolRegistry.from_configs(mcp_configs)  # 新增代码+AppSplit: 把配置对象转换成 MCP 工具注册表；若没有这行代码，配置无法变成 LearningAgent 可用的外部工具入口。
    terminal_permission = (lambda action: resolved_permission_callback(action, show_progress=False)) if quiet_json_run else resolved_permission_callback  # 新增代码+AppSplit: JSON 模式关闭启动进度文本，人类终端保留进度；若没有这行代码，--output-json 可能被进度文本污染。
    agent = resolved_agent_cls(model=model, workspace=workspace, ask_permission=terminal_permission, mcp_tool_registry=mcp_tool_registry, prompt_soft_token_limit=runtime_config.prompt_soft_token_limit)  # 新增代码+AppSplit: 创建 agent 并注入模型、工作区、权限和 MCP registry；若没有这行代码，CLI 没有可运行实例。
    visible_tools = catalog_runtime_from_tools.tool_schema_names(agent)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 缓存当前模型可见工具名并直连 catalog_runtime；若没有这行代码，run/bridge/交互模式仍会通过 agent.py 薄包装展示工具池。
    if main_args.command in {"run", "once", "command"}:  # 新增代码+AppSplit: 处理一次性非交互运行命令；若没有这行代码，Codex 只能通过人工交互控制 agent。
        prompt = main_args.prompt.strip()  # 新增代码+AppSplit: 清理一次性 prompt；若没有这行代码，空白输入可能被当成有效任务。
        if not prompt:  # 新增代码+AppSplit: 检查 run 命令是否带 prompt；若没有这行代码，空任务会进入模型造成困惑。
            error_text = "CLI run 失败：缺少 --prompt 参数。"  # 新增代码+AppSplit: 构造可读缺参错误；若没有这行代码，用户不知道怎么修正命令。
            if main_args.output_json:  # 新增代码+AppSplit: JSON 模式错误也要机器可读；若没有这行代码，Codex 无法解析失败。
                print(json.dumps({"ok": False, "error": error_text, "workspace": str(workspace)}, ensure_ascii=False))  # 新增代码+AppSplit: 输出 JSON 错误；若没有这行代码，自动化调用收不到结构化失败。
            else:  # 新增代码+AppSplit: 人类模式输出普通错误；若没有这行代码，终端用户会看到 JSON 噪音。
                print(error_text)  # 新增代码+AppSplit: 打印缺参错误；若没有这行代码，命令会静默退出。
            return  # 新增代码+AppSplit: 缺 prompt 时停止；若没有这行代码，后续会调用 agent.run("")。
        answer = agent.run(prompt, max_turns=max_turns)  # 新增代码+AppSplit: 执行一次 agent.run；若没有这行代码，run 命令不会真正控制 agent。
        print(format_cli_run_response(answer=answer, output_json=main_args.output_json, workspace=workspace, visible_tools=visible_tools, max_turns=max_turns))  # 新增代码+AppSplit: 输出人类文本或 JSON；若没有这行代码，调用方收不到 agent 结果。
        return  # 新增代码+AppSplit: 一次性运行结束后退出；若没有这行代码，CLI run 会继续进入交互循环。
    if main_args.command in {"bridge", "serve", "http-bridge"}:  # 新增代码+AppSplit: 处理 HTTP bridge 启动命令；若没有这行代码，Codex 无法通过 HTTP 控制 agent。
        bridge_server = create_command_bridge_server(agent=agent, host=main_args.bridge_host, port=main_args.bridge_port, token=main_args.bridge_token, max_turns=max_turns)  # 新增代码+AppSplit: 创建 bridge server；若没有这行代码，bridge 命令无法监听端口。
        serve_command_bridge(bridge_server=bridge_server, visible_tools=visible_tools, max_turns=max_turns, prompt_soft_token_limit=runtime_config.prompt_soft_token_limit)  # 新增代码+AppSplit: 运行 bridge 生命周期；若没有这行代码，HTTP bridge 启动后不会处理请求。
        return  # 新增代码+AppSplit: bridge 结束后退出；若没有这行代码，停止服务后会进入交互循环。
    run_interactive_session(agent=agent, workspace=workspace, visible_tools=visible_tools, max_turns=max_turns, prompt_soft_token_limit=runtime_config.prompt_soft_token_limit)  # 新增代码+AppSplit: 进入真实用户可见交互循环；若没有这行代码，默认启动不会等待用户输入。
