"""MCP 配置、客户端、registry 和 doctor 运行时实现。"""  # 新增代码+McpSplit: 这个文件承载从主入口迁出的 MCP 业务逻辑；若没有这个文件，MCP 问题仍要翻 learning_agent.py。

from __future__ import annotations  # 新增代码+McpSplit: 延迟解析类型注解；若没有这行代码，MCP runtime 对后续工具层类型的临时引用会更容易形成导入顺序问题。

import copy  # 新增代码+McpSplit: MCP schema、通知和资源记录需要深拷贝防止外部污染；若没有这行代码，调用方可能改坏 registry 缓存。
import json  # 新增代码+McpSplit: MCP JSON-RPC、配置文件和 doctor 输出都需要 JSON 解析；若没有这行代码，MCP 协议无法工作。
import queue  # 新增代码+McpSplit: stdio client 用队列接收后台 stdout reader；若没有这行代码，请求超时无法绕开阻塞 readline。
import subprocess  # 新增代码+McpSplit: stdio client 需要启动本地 MCP server 进程；若没有这行代码，本地 MCP server 无法运行。
import threading  # 新增代码+McpSplit: stdio client 需要后台线程读取 stdout；若没有这行代码，主线程会被 readline 卡住。
import time  # 新增代码+McpSplit: 请求超时、SSE 状态和 doctor 计时需要当前时间；若没有这行代码，超时和状态记录无法工作。
import urllib.error  # 新增代码+McpSplit: HTTP MCP client 需要区分 HTTPError 和网络错误；若没有这行代码，远程 MCP 错误会变得不可诊断。
import urllib.parse  # 新增代码+McpSplit: HTTP/SSE URL 和鉴权 metadata 解析需要 URL 工具；若没有这行代码，远程 MCP 请求会拼接不稳。
import urllib.request  # 新增代码+McpSplit: HTTP MCP client 使用标准库发送请求；若没有这行代码，远程 MCP 无法通信。
from dataclasses import dataclass, field  # 新增代码+McpSplit: MCP 配置和流状态使用数据类；若没有这行代码，需要手写重复初始化逻辑。
from pathlib import Path  # 新增代码+McpSplit: mcp_servers.json 路径和工作区路径需要跨平台处理；若没有这行代码，路径解析会脆弱。
from typing import Any  # 新增代码+McpSplit: MCP JSON-RPC 消息和外部工具结果需要通用 JSON 类型；若没有这行代码，类型边界不清楚。

try:  # 新增代码+McpSplit: 包运行模式下导入真实 Chrome 诊断函数给 doctor 使用；若没有这行代码，doctor 无法继续输出真实 Chrome 状态。
    from learning_agent.browser_real_chrome import diagnose_real_chrome_environment  # 新增代码+McpSplit: 导入真实 Chrome profile 诊断入口；若没有这行代码，mcp-doctor 会失去 Chrome 环境检查。
except ModuleNotFoundError as error:  # 新增代码+McpSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.browser_real_chrome"}:  # 新增代码+McpSplit: 只允许目标路径缺失时 fallback；若没有这行代码，诊断模块内部真实 bug 会被误吞。
        raise  # 新增代码+McpSplit: 重新抛出真实导入错误；若没有这行代码，排查 doctor 问题会很困难。
    from browser_real_chrome import diagnose_real_chrome_environment  # 新增代码+McpSplit: 脚本运行模式下从同目录导入 Chrome 诊断入口；若没有这行代码，直接执行文件时 doctor 会失败。



try:  # 新增代码+ToolSchemaSplit: 包运行模式下从工具层读取 catalog helper 和 schema；若没有这行代码，MCP runtime 会继续绕回旧入口。
    from learning_agent.tools.catalog import agent_tool_from_schema, builtin_tool_capability_pack  # 新增代码+ToolSchemaSplit: 导入工具包装和能力包查询函数；若没有这行代码，MCP 工具无法进入统一 AgentTool catalog。
    from learning_agent.tools.schemas import TOOL_SCHEMAS  # 新增代码+ToolSchemaSplit: 导入内置工具 schema 供 doctor 汇总；若没有这行代码，doctor 无法显示内置工具数量。
except ModuleNotFoundError as error:  # 新增代码+ToolSchemaSplit: 捕获直接脚本运行时包路径不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.catalog", "learning_agent.tools.schemas"}:  # 新增代码+ToolSchemaSplit: 只允许目标路径缺失时 fallback；若没有这行代码，工具层真实 bug 会被误吞。
        raise  # 新增代码+ToolSchemaSplit: 重新抛出真实导入错误；若没有这行代码，MCP 工具目录问题会被隐藏。
    from tools.catalog import agent_tool_from_schema, builtin_tool_capability_pack  # 新增代码+ToolSchemaSplit: 脚本模式下从同目录 tools 包读取 helper；若没有这行代码，直接执行 learning_agent.py 时 MCP 工具包装会失败。
    from tools.schemas import TOOL_SCHEMAS  # 新增代码+ToolSchemaSplit: 脚本模式下读取内置工具 schema；若没有这行代码，doctor 在脚本模式下缺少内置工具清单。

try:  # 新增代码+BrowserToolSurfaceStage3: 包运行模式下导入浏览器工具表面 helper；若没有这行代码，MCP catalog 无法过滤 provider 专属重复动作。
    from learning_agent.browser.providers.tool_surface import browser_tool_surface_hint, is_provider_specific_tool_name  # 新增代码+BrowserToolSurfaceStage3: 导入提示和过滤函数；若没有这行代码，Stage 3 单轨工具表面无法落到 catalog。
except ModuleNotFoundError as error:  # 新增代码+BrowserToolSurfaceStage3: 捕获直接脚本运行时包路径不可用；若没有这行代码，start_oauth_agent.bat 可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.providers", "learning_agent.browser.providers.tool_surface"}:  # 新增代码+BrowserToolSurfaceStage3: 只允许目标路径缺失时 fallback；若没有这行代码，helper 内部 bug 会被误吞。
        raise  # 新增代码+BrowserToolSurfaceStage3: 重新抛出真实导入错误；若没有这行代码，工具表面问题会被隐藏。
    from browser.providers.tool_surface import browser_tool_surface_hint, is_provider_specific_tool_name  # 新增代码+BrowserToolSurfaceStage3: 脚本模式下导入 helper；若没有这行代码，直接执行时无法应用 Stage 3 过滤。


def _main_tool_schemas() -> list[dict[str, Any]]:  # 修改代码+ToolSchemaSplit: 从独立 schema 模块读取内置工具清单供 doctor 使用；若没有这行代码，doctor 会重新依赖旧入口。
    return TOOL_SCHEMAS if isinstance(TOOL_SCHEMAS, list) else []  # 修改代码+ToolSchemaSplit: 异常类型降级为空列表；若没有这行代码，坏 schema 状态会让 doctor 崩溃。


def _diagnose_real_chrome_environment(workspace_path: Path) -> Any:  # 修改代码+ToolSchemaSplit: 直接调用真实 Chrome 诊断函数；若没有这行代码，doctor 调用点会散落在各处。
    return diagnose_real_chrome_environment(workspace_path)  # 修改代码+ToolSchemaSplit: 返回 Chrome 环境诊断结果；若没有这行代码，mcp-doctor 无法报告真实浏览器状态。


@dataclass  # 修改代码+MCPTransport: 自动生成 MCP server 配置对象并扩展 transport 字段；若省略: HTTP/SSE 配置只能用松散字典传递且容易写错字段
class McpServerConfig:  # 修改代码+MCPTransport: 表示 stdio、Streamable HTTP 或旧 SSE MCP server 配置；若省略: registry 无法按连接方式选择 client
    name: str  # 修改代码+MCPTransport: 保存 server 名称，用于生成 mcp__服务器__工具 的前缀；若省略: MCP 工具无法稳定命名
    command: str  # 修改代码+MCPTransport: 保存 stdio 启动命令，HTTP/SSE 可为空；若省略: 本地 MCP server 无法启动且旧测试不兼容
    args: list[str] = field(default_factory=list)  # 修改代码+MCPTransport: 保存 stdio 启动参数；若省略: 无法传入 Playwright MCP 包名或脚本路径
    transport: str = "stdio"  # 新增代码+MCPTransport: 标记连接方式为 stdio/http/sse；若省略: 远程 MCP server 会被错误当成本地命令启动
    url: str = ""  # 新增代码+MCPTransport: 保存 HTTP/SSE MCP endpoint URL；若省略: 远程 MCP client 不知道 POST 或连接到哪里
    headers: dict[str, str] = field(default_factory=dict)  # 新增代码+MCPTransport: 保存远程 MCP 自定义请求头；若省略: 需要 Authorization 等鉴权头的 server 无法使用



@dataclass  # 新增代码+MCPAuthMetadata: 自动生成 MCP 鉴权挑战数据对象；若省略: 401、WWW-Authenticate 和 metadata URL 只能用松散字典传递且容易丢字段
class McpAuthChallenge:  # 新增代码+MCPAuthMetadata: 保存远程 MCP server 返回的 OAuth/auth 挑战信息；若省略: registry 无法把登录需求转成可审计 authenticate 工具
    server_name: str  # 新增代码+MCPAuthMetadata: 保存触发鉴权的 server 名称；若省略: 错误提示无法指出哪个 MCP server 需要登录
    status_code: int  # 新增代码+MCPAuthMetadata: 保存 HTTP 状态码；若省略: 用户无法确认这是 401 Unauthorized 还是其他网络错误
    www_authenticate: str = ""  # 新增代码+MCPAuthMetadata: 保存原始 WWW-Authenticate header；若省略: 用户和模型无法追溯服务端给出的鉴权挑战
    resource_metadata_url: str = ""  # 新增代码+MCPAuthMetadata: 保存 RFC9728 resource_metadata URL；若省略: 用户不知道授权服务器发现入口在哪里
    error_body: str = ""  # 新增代码+MCPAuthMetadata: 保存 401 错误正文；若省略: 服务端给出的登录说明或错误原因会丢失



@dataclass  # 新增代码+MCPStream: 自动生成 SSE event 数据对象；若省略: 流事件只能用松散字典传递且容易漏字段
class McpHttpStreamEvent:  # 新增代码+MCPStream: 表示一个解析后的 SSE 事件；若省略: GET/POST 流无法共享统一事件结构
    event_id: str = ""  # 新增代码+MCPStream: 保存 SSE id 字段；若省略: Last-Event-ID 恢复没有游标
    event_type: str = ""  # 新增代码+MCPStream: 保存 SSE event 字段；若省略: 无法区分 message、endpoint 或自定义事件
    retry_ms: int | None = None  # 新增代码+MCPStream: 保存 SSE retry 建议；若省略: 客户端无法尊重服务端重连节奏
    data: str = ""  # 新增代码+MCPStream: 保存合并后的 data 文本；若省略: JSON-RPC 消息正文会丢失
    message: dict[str, Any] | None = None  # 新增代码+MCPStream: 保存解析后的 JSON-RPC 消息；若省略: 调用方需要重复 json.loads
    raw: str = ""  # 新增代码+MCPStream: 保存原始事件文本；若省略: 非标准事件无法诊断



@dataclass  # 新增代码+MCPStream: 自动生成 stream 状态对象；若省略: last event id 和 retry 状态会散落在多个字段
class McpHttpStreamState:  # 新增代码+MCPStream: 保存单个 HTTP MCP client 的流状态；若省略: GET 恢复和 doctor 展示缺少统一来源
    last_event_id: str = ""  # 新增代码+MCPStream: 保存最近一次收到的 SSE id；若省略: 重连时无法发送 Last-Event-ID
    retry_ms: int | None = None  # 新增代码+MCPStream: 保存最近一次 retry 建议；若省略: 断线恢复无法参考服务端等待时间
    last_opened_at: str = ""  # 新增代码+MCPStream: 保存最近一次打开流的时间文本；若省略: 用户无法判断监听状态新旧
    last_error: str = ""  # 新增代码+MCPStream: 保存最近一次流错误；若省略: listen 失败后 doctor 无法解释原因
    received_count: int = 0  # 新增代码+MCPStream: 保存累计事件数；若省略: 用户无法判断监听是否真的收到过事件


class McpAuthenticationRequired(RuntimeError):  # 新增代码+MCPAuthMetadata: 用专门异常表达 MCP HTTP server 需要鉴权；若省略: registry 无法区分“需要登录”和“真实启动失败”
    def __init__(self, challenge: McpAuthChallenge) -> None:  # 新增代码+MCPAuthMetadata: 用鉴权挑战初始化异常；若省略: 异常无法携带 metadata URL 给上层
        self.challenge = challenge  # 新增代码+MCPAuthMetadata: 保存结构化挑战供 registry 暴露 authenticate 工具；若省略: 上层只能解析错误字符串
        detail = challenge.resource_metadata_url or challenge.www_authenticate or challenge.error_body or "未提供鉴权 metadata"  # 新增代码+MCPAuthMetadata: 选择最有用的错误细节；若省略: 异常消息会缺少恢复线索
        super().__init__(f"MCP HTTP server {challenge.server_name} 需要鉴权：HTTP {challenge.status_code}，{detail}")  # 新增代码+MCPAuthMetadata: 生成可读异常文本；若省略: 用户不知道失败是登录需求而不是普通连接错误


class McpSessionExpired(RuntimeError):  # 新增代码+MCPStream: 标记 HTTP session 已过期；若省略: 404 无法和普通远程错误区分
    pass  # 新增代码+MCPStream: 继承 RuntimeError 即可；若省略: Python 类体不能为空


def mcp_server_config_path(workspace: str | Path) -> Path:  # 新增代码+MCP诊断: 统一计算 mcp_servers.json 路径；若省略: 配置加载、启动提示和 doctor 可能各自拼错路径
    return Path(workspace).expanduser().resolve() / "mcp_servers.json"  # 新增代码+MCP诊断: 返回工作区内固定配置文件路径；若省略: agent 无法稳定告诉用户配置应该放在哪里


def load_mcp_server_configs(workspace: str | Path) -> list[McpServerConfig]:  # 新增代码: 从工作区读取 MCP server 配置；若省略: agent 无法从文件发现外部工具服务
    config_path = mcp_server_config_path(workspace)  # 修改代码+MCP诊断: 复用统一配置路径函数；若省略: doctor 和加载逻辑可能显示不同配置位置
    if not config_path.exists():  # 新增代码: 如果配置文件不存在；若省略: 默认启动会因为缺文件崩溃
        return []  # 新增代码: 缺少配置时返回空列表保持旧行为；若省略: 无 MCP 用户无法继续使用 agent
    try:  # 修改代码: 捕获读取和解析配置时的异常；若省略: 坏 JSON 或目录路径会让 agent 启动崩溃
        payload = json.loads(config_path.read_text(encoding="utf-8"))  # 修改代码: 用 UTF-8 读取并解析 JSON；若省略: 无法取得 server 配置
    except (OSError, json.JSONDecodeError):  # 新增代码: 处理文件读取失败和 JSON 格式错误；若省略: 用户写错配置时无法回退到无 MCP 模式
        return []  # 新增代码: 配置不可读或不可解析时返回空列表；若省略: 容错场景仍会中断 agent
    servers_value = payload.get("servers", []) if isinstance(payload, dict) else []  # 新增代码: 只从顶层对象读取 servers 值；若省略: 非对象 JSON 可能导致属性访问异常
    raw_servers = servers_value if isinstance(servers_value, list) else []  # 新增代码: 只接受 servers 数组；若省略: servers 为数字或 null 时遍历会崩溃
    configs: list[McpServerConfig] = []  # 新增代码: 准备保存解析后的配置对象；若省略: 无处累积结果
    for raw_server in raw_servers:  # 新增代码: 遍历每个 server 配置；若省略: 只能支持零个 server
        if not isinstance(raw_server, dict):  # 新增代码: 跳过非对象配置；若省略: 错误 JSON 会导致属性访问异常
            continue  # 新增代码: 保持配置加载尽量宽容；若省略: 单个坏项会破坏全部配置
        name = str(raw_server.get("name", "")).strip()  # 修改代码+MCPTransport: 读取并清理 server 名；若省略: 工具前缀可能为空或带空格
        command = str(raw_server.get("command", "")).strip()  # 修改代码+MCPTransport: 读取 stdio 启动命令，HTTP/SSE 可为空；若省略: 本地 server 无法启动
        transport = str(raw_server.get("transport", "stdio") or "stdio").strip().lower()  # 新增代码+MCPTransport: 读取连接方式并默认 stdio；若省略: 旧配置无法兼容且远程配置无法分流
        url = str(raw_server.get("url", "") or "").strip()  # 新增代码+MCPTransport: 读取远程 MCP endpoint URL；若省略: HTTP/SSE client 无法知道目标地址
        headers_value = raw_server.get("headers", {})  # 新增代码+MCPTransport: 读取远程 MCP 自定义请求头原始值；若省略: 鉴权或自定义网关 header 无法配置
        headers = {str(key): str(value) for key, value in headers_value.items()} if isinstance(headers_value, dict) else {}  # 新增代码+MCPTransport: 把 header 键值转成字符串字典；若省略: urllib 可能收到非法 header 类型
        args_value = raw_server.get("args", [])  # 修改代码+MCPTransport: 读取 stdio 启动参数原始值；若省略: 无法支持命令参数
        args = [str(item) for item in args_value] if isinstance(args_value, list) else []  # 修改代码+MCPTransport: 只接受数组参数并转成字符串；若省略: 参数类型不稳定
        if transport not in {"stdio", "http", "sse"}:  # 新增代码+MCPTransport: 只接受当前明确支持或明确设边界的 transport；若省略: 拼写错误会进入不可预测启动流程
            continue  # 新增代码+MCPTransport: 跳过未知 transport 配置项；若省略: 单个坏 transport 会破坏整体配置加载
        if transport == "stdio" and name and command:  # 修改代码+MCPTransport: stdio 必须有名称和命令；若省略: 空命令会进入子进程启动并报底层错误
            configs.append(McpServerConfig(name=name, command=command, args=args, transport=transport))  # 修改代码+MCPTransport: 保存 stdio 配置对象；若省略: 本地 MCP server 配置会丢失
        elif transport in {"http", "sse"} and name and url:  # 新增代码+MCPTransport: 远程 transport 必须有名称和 URL；若省略: HTTP/SSE 配置可能缺目标仍进入启动流程
            configs.append(McpServerConfig(name=name, command=command, args=args, transport=transport, url=url, headers=headers))  # 新增代码+MCPTransport: 保存远程 MCP 配置对象；若省略: HTTP/SSE server 不会进入 registry
    return configs  # 新增代码: 返回所有可用 MCP server 配置；若省略: 调用方拿不到配置


def format_mcp_startup_status(workspace: str | Path, configs: list[McpServerConfig]) -> str:  # 新增代码+MCP诊断: 生成启动时简短 MCP 状态提示；若省略: 用户启动后不知道有没有加载外部工具配置
    config_path = mcp_server_config_path(workspace)  # 新增代码+MCP诊断: 取得真实配置文件路径；若省略: 启动提示无法告诉用户应该检查哪个文件
    lines = ["MCP 启动状态：", f"- 配置文件：{config_path}"]  # 新增代码+MCP诊断: 初始化状态文本和配置路径；若省略: 输出缺少基本定位信息
    if not config_path.exists():  # 新增代码+MCP诊断: 判断配置文件是否缺失；若省略: 无法解释为什么没有外部 MCP 工具
        lines.append("- 配置状态：未找到 mcp_servers.json，当前不会加载外部 MCP 工具。")  # 新增代码+MCP诊断: 明确缺配置状态；若省略: 用户会误以为 MCP 已经启用
        lines.append("- 诊断命令：运行 learning_agent.py mcp-doctor 查看详细说明。")  # 新增代码+MCP诊断: 给出下一步排查入口；若省略: 用户不知道如何继续自检
        return "\n".join(lines)  # 新增代码+MCP诊断: 返回缺配置状态文本；若省略: 后续会继续输出误导性的 server 列表
    if not configs:  # 新增代码+MCP诊断: 处理配置文件存在但没有有效 server 的情况；若省略: 坏配置会被误判为正常
        lines.append("- 配置状态：已找到 mcp_servers.json，但没有解析到可用 MCP server。")  # 新增代码+MCP诊断: 明确配置内容不可用；若省略: 用户无法定位 JSON 内容问题
        lines.append("- 诊断命令：运行 learning_agent.py mcp-doctor 查看详细说明。")  # 新增代码+MCP诊断: 提示使用 doctor 深入检查；若省略: 用户缺少排查路径
        return "\n".join(lines)  # 新增代码+MCP诊断: 返回坏配置状态文本；若省略: 会输出空 server 名列表
    server_names = ", ".join(f"{config.name}({config.transport})" for config in configs)  # 修改代码+MCPTransport: 汇总配置里的 server 名和 transport；若省略: 用户不知道本轮准备启动本地还是远程 MCP server
    lines.append(f"- 配置状态：已找到 mcp_servers.json，解析到 {len(configs)} 个 MCP server：{server_names}")  # 修改代码+MCPTransport: 输出 server 数量、名称和 transport；若省略: 启动前可见性不足
    lines.append("- 后续会请求启动 MCP server；允许后模型才能看到对应 mcp__... 工具。")  # 新增代码+MCP诊断: 说明权限确认和工具可见性的关系；若省略: 用户可能以为只要有配置就自动可用
    return "\n".join(lines)  # 新增代码+MCP诊断: 返回完整启动状态文本；若省略: main 无法打印状态


class McpStdioClient:  # 新增代码+MCP stdio client: 定义最小 MCP stdio JSON-RPC 客户端；若省略: 项目无法启动和调用本地 MCP server
    def __init__(self, config: McpServerConfig, request_timeout_seconds: float | None = None) -> None:  # 修改代码+浏览器超时: 接收单个 server 配置和可选请求超时；若省略可选语义: browser_automation 直接构造仍会被 5 秒误杀
        self.config = config  # 新增代码+MCP stdio client: 保存 MCP server 配置供 start 使用；若省略: start 无法访问 command 和 args
        self.request_timeout_seconds = request_timeout_seconds if request_timeout_seconds is not None else self._default_request_timeout_seconds(config)  # 修改代码+浏览器超时: 未显式传参时按 server 类型选择默认超时；若省略: 直接构造 browser_automation client 仍可能在页面加载前超时
        self._process: subprocess.Popen[str] | None = None  # 新增代码+MCP stdio client: 保存子进程对象；若省略: 后续无法读写 stdio 或关闭进程
        self._next_id = 1  # 新增代码+MCP stdio client: 初始化 JSON-RPC 请求 id；若省略: 无法匹配请求和响应
        self._stdout_lines: queue.Queue[str] = queue.Queue()  # 新增代码+MCP stdio client 健壮性: 保存后台线程读取到的 stdout 行；若省略: 主线程无法用超时方式等待响应
        self._stdout_reader_thread: threading.Thread | None = None  # 新增代码+MCP stdio client 健壮性: 保存 stdout reader 线程引用；若省略: 无法确认读取线程已启动
        self._pending_notifications: list[dict[str, Any]] = []  # 新增代码+MCPLifecycleV2: 保存等待 registry 消费的 MCP server notifications；若没有这行代码，tools/list_changed 会在响应等待循环里被丢弃

    @staticmethod  # 新增代码+浏览器超时: 默认超时策略只依赖配置，不需要 client 实例状态；若省略: registry 和直接构造会各写一套容易不一致
    def _default_request_timeout_seconds(config: McpServerConfig) -> float:  # 新增代码+浏览器超时: 统一决定 stdio client 默认请求超时；若省略: 慢浏览器工具无法和普通工具区分
        if config.transport == "stdio" and config.name == "browser_automation":  # 新增代码+浏览器超时: browser_automation 页面加载可能等待到 30000ms；若省略: 真实浏览器操作仍可能被 5 秒外层截断
            return 90.0  # 修改代码+真实Chrome连接超时: 给真实 Chrome 启动、CDP 连接和慢页面更多外层余量；若没有这行代码，start_oauth_agent.bat 真实终端验收会偶发把 browser_automation 提前杀掉。
        return 5.0  # 新增代码+浏览器超时: 其他 stdio server 保持快速失败；若省略: 坏 server 会让 agent 等待过久

    def start(self) -> None:  # 新增代码+MCP stdio client: 启动子进程并完成 MCP 初始化握手；若省略: list_tools 和 call_tool 没有可用连接
        if self._process is not None:  # 新增代码+MCP stdio client: 避免重复启动同一个客户端；若省略: 可能产生多个难以关闭的 server 进程
            return  # 新增代码+MCP stdio client: 已启动时直接返回保持幂等；若省略: 重复 start 会额外启动进程
        self._process = subprocess.Popen(  # 新增代码+MCP stdio client: 按要求创建 stdio 子进程；若省略: 客户端无法和 MCP server 通信
            [self.config.command, *self.config.args],  # 新增代码+MCP stdio client: 组合命令和参数数组；若省略: server 脚本或参数不会被传入
            stdin=subprocess.PIPE,  # 新增代码+MCP stdio client: 打开标准输入管道发送 JSON-RPC；若省略: 无法写请求给 server
            stdout=subprocess.PIPE,  # 新增代码+MCP stdio client: 打开标准输出管道读取 JSON-RPC；若省略: 无法读取 server 响应
            stderr=subprocess.DEVNULL,  # 修改代码+MCP stdio client 健壮性: 丢弃 stderr 避免未 drain 管道导致死锁；若省略: server 大量写 stderr 可能阻塞
            text=True,  # 新增代码+MCP stdio client: 使用文本模式读写字符串；若省略: 需要手动处理 bytes 编码
            encoding="utf-8",  # 新增代码+MCP stdio client: 明确使用 UTF-8 支持中文参数；若省略: Windows 默认编码可能破坏中文
            bufsize=1,  # 新增代码+MCP stdio client: 使用行缓冲配合单行 JSON-RPC；若省略: 消息可能延迟刷新
        )  # 新增代码+MCP stdio client: 子进程启动完成；若省略: self._process 不会保存可通信进程
        self._start_stdout_reader()  # 新增代码+MCP stdio client 健壮性: 启动后台线程读取 stdout；若省略: _send_request 无法用队列超时等待响应
        self._send_request(  # 新增代码+MCP stdio client: 发送 initialize 请求完成 MCP 握手第一步；若省略: server 可能拒绝后续工具请求
            "initialize",  # 新增代码+MCP stdio client: 指定 MCP 初始化方法名；若省略: server 不知道这是初始化
            {  # 新增代码+MCP stdio client: 构造初始化参数对象；若省略: initialize 请求缺少协议元信息
                "protocolVersion": "2024-11-05",  # 新增代码+MCP stdio client: 声明客户端支持的 MCP 协议版本；若省略: server 可能无法协商协议
                "capabilities": {},  # 新增代码+MCP stdio client: 声明当前最小客户端没有额外能力；若省略: 初始化参数不完整
                "clientInfo": {"name": "OpenHarness", "version": "0.1"},  # 新增代码+MCP stdio client: 提供客户端标识；若省略: server 无法知道调用方来源
            },  # 新增代码+MCP stdio client: 初始化参数对象结束；若省略: Python 语法不完整
        )  # 新增代码+MCP stdio client: initialize 响应已收到；若省略: 后续通知可能过早发送
        self._send_notification("notifications/initialized", {})  # 新增代码+MCP stdio client: 通知 server 初始化完成；若省略: 部分 MCP server 不会进入就绪状态

    def list_tools(self) -> list[dict[str, Any]]:  # 新增代码+MCP stdio client: 请求 MCP server 暴露的工具列表；若省略: 调用方无法发现工具
        result = self._send_request("tools/list", {})  # 新增代码+MCP stdio client: 发送 tools/list 请求并读取结果；若省略: 无法获得 server 工具数组
        tools = result.get("tools", []) if isinstance(result, dict) else []  # 新增代码+MCP stdio client: 从结果中取 tools 数组；若省略: 非标准响应可能导致崩溃
        return tools if isinstance(tools, list) else []  # 新增代码+MCP stdio client: 只返回列表类型工具；若省略: 调用方可能收到错误类型

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:  # 新增代码+MCP stdio client: 调用指定 MCP 工具并返回文本；若省略: 客户端只能列工具不能执行工具
        result = self._send_request("tools/call", {"name": name, "arguments": arguments})  # 新增代码+MCP stdio client: 发送 tools/call 请求；若省略: server 不会执行目标工具
        return self._mcp_result_to_text(result)  # 新增代码+MCP stdio client: 将 MCP content 结果转成文本；若省略: 上层难以直接展示工具结果

    def list_resources(self) -> list[dict[str, Any]]:  # 新增代码+MCPResource: 请求 MCP server 暴露的资源列表；若省略: agent 无法发现 resources/list 提供的外部上下文
        result = self._send_request("resources/list", {})  # 新增代码+MCPResource: 发送 resources/list 请求并读取结果；若省略: 无法获得 server resources 数组
        resources = result.get("resources", []) if isinstance(result, dict) else []  # 新增代码+MCPResource: 从结果中取 resources 数组；若省略: 非标准响应可能导致崩溃
        return resources if isinstance(resources, list) else []  # 新增代码+MCPResource: 只返回列表类型资源；若省略: 调用方可能收到错误类型

    def read_resource(self, uri: str) -> str:  # 新增代码+MCPResource: 读取指定 MCP resource 并返回文本；若省略: 客户端只能列资源不能读取资源正文
        result = self._send_request("resources/read", {"uri": uri})  # 新增代码+MCPResource: 发送 resources/read 请求；若省略: server 不会返回目标资源内容
        return self._mcp_resource_result_to_text(result)  # 新增代码+MCPResource: 将 MCP contents 结果转成文本；若省略: 上层难以直接展示资源正文

    def list_prompts(self) -> list[dict[str, Any]]:  # 新增代码+MCPPrompt: 请求 MCP server 暴露的 prompt 列表；若省略: agent 无法发现 prompts/list 提供的远程操作规程
        result = self._send_request("prompts/list", {})  # 新增代码+MCPPrompt: 发送 prompts/list 请求并读取结果；若省略: 无法获得 server prompts 数组
        prompts = result.get("prompts", []) if isinstance(result, dict) else []  # 新增代码+MCPPrompt: 从结果中取 prompts 数组；若省略: 非标准响应可能导致崩溃
        return prompts if isinstance(prompts, list) else []  # 新增代码+MCPPrompt: 只返回列表类型 prompt；若省略: 调用方可能收到错误类型

    def get_prompt(self, name: str, arguments: dict[str, Any] | None = None) -> str:  # 新增代码+MCPPrompt: 读取指定 MCP prompt 并返回文本；若省略: 客户端只能列 prompts 不能读取 prompt 正文
        prompt_arguments = arguments or {}  # 新增代码+MCPPrompt: 把缺省参数转成空对象；若省略: prompts/get 可能收到 None 而不符合常见 MCP 参数形态
        result = self._send_request("prompts/get", {"name": name, "arguments": prompt_arguments})  # 新增代码+MCPPrompt: 发送 prompts/get 请求；若省略: server 不会返回目标 prompt 内容
        return self._mcp_prompt_result_to_text(result)  # 新增代码+MCPPrompt: 将 MCP prompt messages 结果转成文本；若省略: 上层难以直接展示 prompt 正文

    def close(self) -> None:  # 新增代码+MCP stdio client: 关闭 MCP server 子进程；若省略: 测试和运行时会泄漏进程
        process = self._process  # 新增代码+MCP stdio client: 取出当前进程引用；若省略: 后续清理逻辑无法访问进程
        self._process = None  # 新增代码+MCP stdio client: 先清空进程引用避免重复关闭；若省略: 多次 close 可能重复操作同一进程
        self._pending_notifications = []  # 新增代码+MCPLifecycleV2: 关闭 client 时丢弃旧会话未处理通知；若没有这行代码，下次启动可能误处理过期 list_changed
        if process is None:  # 新增代码+MCP stdio client: 处理尚未启动或已关闭的情况；若省略: close 在空状态会报错
            return  # 新增代码+MCP stdio client: 没有进程时无需清理；若省略: 后续会访问 None
        try:  # 修改代码+MCP stdio client 健壮性: 保护 terminate/kill/wait 清理流程；若省略: close 可能把底层异常暴露给调用方
            if process.poll() is None:  # 新增代码+MCP stdio client: 只终止仍在运行的进程；若省略: 已退出进程也会被多余 terminate
                process.terminate()  # 新增代码+MCP stdio client: 请求子进程退出；若省略: MCP server 可能继续占用资源
                try:  # 新增代码+MCP stdio client: 等待进程短时间退出；若省略: terminate 后可能留下未回收进程
                    process.wait(timeout=2)  # 新增代码+MCP stdio client: 回收已终止进程；若省略: 操作系统可能保留进程句柄
                except subprocess.TimeoutExpired:  # 新增代码+MCP stdio client: 处理进程没有及时退出；若省略: close 可能抛异常中断清理
                    process.kill()  # 新增代码+MCP stdio client: 强制结束不响应 terminate 的进程；若省略: 卡住的 server 可能残留
                    try:  # 新增代码+MCP stdio client 健壮性: 等待被 kill 的进程退出；若省略: kill 后 wait 失败会中断管道关闭
                        process.wait(timeout=2)  # 新增代码+MCP stdio client: 回收被 kill 的进程；若省略: 强制结束后仍可能留下句柄
                    except subprocess.TimeoutExpired:  # 新增代码+MCP stdio client 健壮性: 处理 kill 后仍未退出的极端情况；若省略: close 会抛出不可控异常
                        pass  # 新增代码+MCP stdio client 健壮性: 忽略极端等待失败并继续关闭管道；若省略: pipe 可能无法进入 finally 清理
        finally:  # 新增代码+MCP stdio client 健壮性: 确保无论 wait 是否失败都关闭管道；若省略: 异常路径会泄漏文件句柄
            for pipe in (process.stdin, process.stdout, process.stderr):  # 新增代码+MCP stdio client: 遍历子进程三个管道句柄；若省略: unittest 会提示未关闭文件资源
                if pipe is not None and not pipe.closed:  # 新增代码+MCP stdio client: 只关闭存在且尚未关闭的管道；若省略: 关闭空管道或重复关闭会增加异常风险
                    pipe.close()  # 新增代码+MCP stdio client: 释放 stdio 管道文件句柄；若省略: 测试和长期运行会泄漏文件资源

    def _send_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:  # 新增代码+MCP stdio client: 发送带 id 的 JSON-RPC 请求并等待匹配响应；若省略: start/list/call 会重复写等待逻辑
        self._require_process()  # 修改代码+MCP stdio client 健壮性: 确保子进程已启动且管道可用；若省略: 未启动调用会出现难懂的 None 错误
        request_id = self._next_id  # 新增代码+MCP stdio client: 取当前请求 id；若省略: 响应无法和请求对应
        self._next_id += 1  # 新增代码+MCP stdio client: 递增 id 避免后续请求重复；若省略: 多个请求响应可能混淆
        deadline = time.monotonic() + self.request_timeout_seconds  # 新增代码+MCP stdio client 健壮性: 计算本次请求截止时间；若省略: 无法判断等待是否超时
        self._write_message({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})  # 新增代码+MCP stdio client: 写出单行 JSON-RPC 请求；若省略: server 收不到请求
        while True:  # 新增代码+MCP stdio client: 持续读取直到找到匹配 id 的响应；若省略: 遇到通知或其他响应时无法跳过
            remaining = deadline - time.monotonic()  # 新增代码+MCP stdio client 健壮性: 计算当前剩余等待时间；若省略: 队列等待无法按请求超时收敛
            if remaining <= 0:  # 新增代码+MCP stdio client 健壮性: 检查请求是否已经超时；若省略: 超时后仍可能继续等待
                self.close()  # 新增代码+MCP stdio client 健壮性: 超时后清理子进程和管道；若省略: 卡住的 server 会残留
                raise RuntimeError(f"MCP server {self.config.name} 请求 {method} 超时。")  # 新增代码+MCP stdio client 健壮性: 抛出清晰超时异常；若省略: 调用方不知道卡在哪里
            try:  # 新增代码+MCP stdio client 健壮性: 用队列超时等待 stdout 行；若省略: queue.Empty 会泄漏为低层异常
                raw_line = self._stdout_lines.get(timeout=remaining)  # 新增代码+MCP stdio client 健壮性: 从后台 reader 队列取一行；若省略: 主线程仍会被 blocking readline 卡住
            except queue.Empty:  # 新增代码+MCP stdio client 健壮性: 处理等待期间没有任何 stdout 行；若省略: 超时无法转成可读 RuntimeError
                self.close()  # 新增代码+MCP stdio client 健壮性: 超时后关闭客户端；若省略: 不响应 server 仍会继续运行
                raise RuntimeError(f"MCP server {self.config.name} 请求 {method} 超时。")  # 新增代码+MCP stdio client 健壮性: 抛出中文超时错误；若省略: 测试和用户无法判断超时原因
            if raw_line == "":  # 新增代码+MCP stdio client: 检测 stdout 关闭或进程退出；若省略: 可能把空响应当 JSON 解析
                raise RuntimeError(f"MCP server {self.config.name} stdout closed before response to {method}")  # 新增代码+MCP stdio client: 抛出可读错误；若省略: 用户难以定位 server 已关闭
            message = json.loads(raw_line)  # 新增代码+MCP stdio client: 解析单行 JSON-RPC 响应；若省略: 无法读取 result 或 error
            if message.get("id") != request_id:  # 新增代码+MCP stdio client: 跳过不属于当前请求的消息；若省略: 乱序或通知会破坏请求响应匹配
                self._remember_notification(message)  # 新增代码+MCPLifecycleV2: 如果这条消息是 server notification 就先保存；若没有这行代码，list_changed 会在等待响应时直接消失
                continue  # 新增代码+MCP stdio client: 继续等待匹配 id；若省略: 不匹配消息会被错误返回
            if "error" in message:  # 新增代码+MCP stdio client: 检查 JSON-RPC 错误响应；若省略: 工具错误会被当成成功结果
                raise RuntimeError(f"MCP request {method} failed: {message['error']}")  # 新增代码+MCP stdio client: 抛出带方法名的可读错误；若省略: 调用方无法知道失败原因
            result = message.get("result", {})  # 新增代码+MCP stdio client: 取出 result 字段；若省略: 调用方拿不到 MCP 返回数据
            return result if isinstance(result, dict) else {"value": result}  # 新增代码+MCP stdio client: 保证返回字典；若省略: 后续 .get 调用可能崩溃

    def _start_stdout_reader(self) -> None:  # 新增代码+MCP stdio client 健壮性: 启动读取 stdout 的后台线程；若省略: _send_request 无法非阻塞等待响应
        process = self._require_process()  # 新增代码+MCP stdio client 健壮性: 获取已启动进程；若省略: 无法访问 stdout 管道
        stdout = process.stdout  # 新增代码+MCP stdio client 健壮性: 保存 stdout 引用给 reader 线程；若省略: 线程闭包会反复访问进程对象
        if stdout is None:  # 新增代码+MCP stdio client 健壮性: 检查 stdout 管道是否存在；若省略: 线程会在 None 上读取失败
            raise RuntimeError(f"MCP server {self.config.name} stdout is not available")  # 新增代码+MCP stdio client 健壮性: 抛出清晰 stdout 错误；若省略: 启动失败原因不清楚
        self._stdout_lines = queue.Queue()  # 新增代码+MCP stdio client 健壮性: 每次 start 使用新的响应队列；若省略: 旧消息可能污染新进程
        self._stdout_reader_thread = threading.Thread(target=self._read_stdout_lines, args=(stdout,), daemon=True)  # 新增代码+MCP stdio client 健壮性: 创建 daemon reader 线程；若省略: 后台读取无法启动且进程退出可能阻塞程序关闭
        self._stdout_reader_thread.start()  # 新增代码+MCP stdio client 健壮性: 启动 stdout reader；若省略: 队列永远收不到响应

    def _read_stdout_lines(self, stdout: Any) -> None:  # 新增代码+MCP stdio client 健壮性: 后台读取 stdout 并放入队列；若省略: 主线程无法带超时读取 server 输出
        try:  # 新增代码+MCP stdio client 健壮性: 保护 reader 线程不把异常打印到测试输出；若省略: 管道关闭时可能产生噪声
            for raw_line in stdout:  # 新增代码+MCP stdio client 健壮性: 持续读取 server 输出行；若省略: 客户端收不到 JSON-RPC 响应
                self._stdout_lines.put(raw_line)  # 新增代码+MCP stdio client 健壮性: 把响应行交给请求线程；若省略: _send_request 会一直等队列
        finally:  # 新增代码+MCP stdio client 健壮性: stdout 结束或异常时通知请求线程；若省略: 进程退出后请求会等到超时而不是立即报关闭
            self._stdout_lines.put("")  # 新增代码+MCP stdio client 健壮性: 用空字符串作为 stdout 关闭哨兵；若省略: _send_request 无法区分无消息和已关闭

    def _send_notification(self, method: str, params: dict[str, Any]) -> None:  # 新增代码+MCP stdio client: 发送不等待响应的 JSON-RPC notification；若省略: initialized 通知会误等响应
        self._require_process()  # 新增代码+MCP stdio client: 确保通知发送前进程已启动；若省略: 未启动时会静默丢消息
        self._write_message({"jsonrpc": "2.0", "method": method, "params": params})  # 新增代码+MCP stdio client: 写出无 id 的通知；若省略: server 收不到初始化完成通知

    def pop_notifications(self) -> list[dict[str, Any]]:  # 新增代码+MCPLifecycleV2: 让 registry 一次性拉取并清空 client 收到的 notifications；若没有这行代码，上层无法按 ClaudeCode 风格刷新 MCP catalog
        notifications = copy.deepcopy(self._pending_notifications)  # 新增代码+MCPLifecycleV2: 返回深拷贝，避免 registry 修改通知对象污染 client 内部队列；若没有这行代码，调试信息可能被调用方改坏
        self._pending_notifications = []  # 新增代码+MCPLifecycleV2: 消费后清空队列，避免同一 list_changed 重复触发刷新；若没有这行代码，每次 tool_search 都可能反复重建 registry
        return notifications  # 新增代码+MCPLifecycleV2: 返回待处理通知列表；若没有这行代码，调用方拿不到 server 生命周期事件

    def _remember_notification(self, message: Any) -> None:  # 新增代码+MCPLifecycleV2: 识别并缓存 MCP JSON-RPC notification；若没有这行代码，stdio 与 HTTP SSE 的通知保存逻辑会重复且容易不一致
        if not self._is_json_rpc_notification(message):  # 新增代码+MCPLifecycleV2: 只保存没有 id 且带 method 的 JSON-RPC notification；若没有这行代码，普通 response 或坏消息也会污染生命周期队列
            return  # 新增代码+MCPLifecycleV2: 非 notification 直接忽略；若没有这行代码，后续会把无关消息当刷新事件
        self._pending_notifications.append(copy.deepcopy(message))  # 新增代码+MCPLifecycleV2: 保存 notification 快照；若没有这行代码，registry 无法在下一次工具池计算时看到 list_changed
        self._pending_notifications = self._pending_notifications[-100:]  # 新增代码+MCPLifecycleV2: 最多保留最近 100 条通知防止长期运行无限增长；若没有这行代码，异常 server 可用通知刷爆内存

    @staticmethod  # 新增代码+MCPLifecycleV2: notification 判断不依赖 client 实例状态；若没有这行代码，测试和 HTTP 子类复用会更困难
    def _is_json_rpc_notification(message: Any) -> bool:  # 新增代码+MCPLifecycleV2: 判断消息是否是 JSON-RPC notification；若没有这行代码，list_changed 和普通 response 的边界会散落各处
        return isinstance(message, dict) and "id" not in message and isinstance(message.get("method"), str)  # 新增代码+MCPLifecycleV2: MCP notification 没有 id 且有 method；若没有这行代码，registry 可能误处理 response 或空对象

    def _write_message(self, message: dict[str, Any]) -> None:  # 新增代码+MCP stdio client: 将 JSON-RPC 消息写成单行 JSON；若省略: 请求和通知写法会重复且易错
        process = self._require_process()  # 新增代码+MCP stdio client: 获取已启动进程；若省略: 无法访问 stdin 管道
        if process.stdin is None:  # 新增代码+MCP stdio client: 检查 stdin 管道是否存在；若省略: 管道异常时会出现难懂错误
            raise RuntimeError(f"MCP server {self.config.name} stdin is not available")  # 新增代码+MCP stdio client: 抛出可读 stdin 错误；若省略: 调试管道问题更困难
        process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")  # 新增代码+MCP stdio client: 写入 UTF-8 单行 JSON 加换行；若省略: server readline 不会收到完整消息
        process.stdin.flush()  # 新增代码+MCP stdio client: 立即刷新请求；若省略: 请求可能停在缓冲区导致等待超时

    def _require_process(self) -> subprocess.Popen[str]:  # 新增代码+MCP stdio client: 返回已启动子进程或抛出清晰错误；若省略: 每个方法都要重复 None 检查
        if self._process is None:  # 新增代码+MCP stdio client: 检查客户端是否已经 start；若省略: 未启动时会访问空对象
            raise RuntimeError(f"MCP server {self.config.name} is not started")  # 新增代码+MCP stdio client: 抛出可读未启动错误；若省略: 使用者难以知道需先调用 start
        return self._process  # 新增代码+MCP stdio client: 返回可用进程；若省略: 调用方拿不到进程对象

    def _mcp_result_to_text(self, result: dict[str, Any]) -> str:  # 新增代码+MCP stdio client: 将 MCP 工具结果转换为文本；若省略: call_tool 无法返回易读内容
        content = result.get("content")  # 新增代码+MCP stdio client: 读取 MCP content 字段；若省略: 无法提取标准文本块
        if isinstance(content, list):  # 新增代码+MCP stdio client: 仅当 content 是数组时逐项处理；若省略: 非列表 content 可能导致遍历异常
            parts: list[str] = []  # 新增代码+MCP stdio client: 准备累积文本片段；若省略: 多个 content 块无法合并
            for item in content:  # 新增代码+MCP stdio client: 遍历 MCP content 块；若省略: 只能处理空结果
                if isinstance(item, dict) and item.get("type") == "text":  # 新增代码+MCP stdio client: 识别标准文本 content；若省略: 文本结果不会被优先提取
                    parts.append(str(item.get("text", "")))  # 新增代码+MCP stdio client: 保存文本字段；若省略: call_tool 返回会丢失工具输出
                elif isinstance(item, dict):  # 新增代码+MCP stdio client: 处理非文本字典 content；若省略: 图片或资源类结果会被丢弃
                    parts.append(json.dumps(item, ensure_ascii=False))  # 新增代码+MCP stdio client: 用 JSON 兜底表示非文本内容；若省略: 调用方看不到非文本结果
            if parts:  # 新增代码+MCP stdio client: 如果提取到了任何片段；若省略: 空片段也会返回空字符串掩盖原始结果
                return "\n".join(parts)  # 新增代码+MCP stdio client: 用换行合并多个内容块；若省略: 多块文本无法清晰展示
        return json.dumps(result, ensure_ascii=False)  # 新增代码+MCP stdio client: 没有 content 时返回完整 JSON；若省略: 非标准结果会丢失

    def _mcp_resource_result_to_text(self, result: dict[str, Any]) -> str:  # 新增代码+MCPResource: 将 MCP resources/read 结果转换为文本；若省略: read_resource 无法返回易读正文
        contents = result.get("contents")  # 新增代码+MCPResource: 读取 MCP resources/read 的 contents 字段；若省略: 无法提取标准资源内容
        if isinstance(contents, list):  # 新增代码+MCPResource: 仅当 contents 是数组时逐项处理；若省略: 非列表 contents 可能导致遍历异常
            parts: list[str] = []  # 新增代码+MCPResource: 准备累积多个资源片段；若省略: 多个 contents 块无法合并
            for item in contents:  # 新增代码+MCPResource: 遍历 resources/read 返回的每个内容块；若省略: 资源正文不会被提取
                if isinstance(item, dict) and "text" in item:  # 新增代码+MCPResource: 优先识别文本资源块；若省略: 最常见的 text 内容不会被直接返回
                    parts.append(str(item.get("text", "")))  # 新增代码+MCPResource: 保存文本字段；若省略: read_resource 返回会丢失正文
                elif isinstance(item, dict) and "blob" in item:  # 新增代码+MCPResource: 识别二进制资源块；若省略: blob 资源会被静默丢弃
                    parts.append(json.dumps(item, ensure_ascii=False))  # 新增代码+MCPResource: 用 JSON 兜底展示 blob 元数据；若省略: 调用方看不到非文本资源
                elif isinstance(item, dict):  # 新增代码+MCPResource: 处理其他字典内容块；若省略: 非标准资源内容会被丢弃
                    parts.append(json.dumps(item, ensure_ascii=False))  # 新增代码+MCPResource: 用 JSON 表示未知资源块；若省略: 调试非标准 MCP server 更困难
            if parts:  # 新增代码+MCPResource: 如果提取到任何片段；若省略: 空片段也会返回空字符串掩盖原始结果
                return "\n".join(parts)  # 新增代码+MCPResource: 用换行合并多个资源片段；若省略: 多块资源无法清晰展示
        return json.dumps(result, ensure_ascii=False)  # 新增代码+MCPResource: 没有标准 contents 时返回完整 JSON；若省略: 非标准资源结果会丢失

    def _mcp_prompt_result_to_text(self, result: dict[str, Any]) -> str:  # 新增代码+MCPPrompt: 将 MCP prompts/get 结果转换为文本；若省略: get_prompt 无法返回易读正文
        description = str(result.get("description", "") or "").strip()  # 新增代码+MCPPrompt: 读取 prompt 说明并清理空白；若省略: 返回内容会丢失 prompt 用途信息
        messages = result.get("messages")  # 新增代码+MCPPrompt: 读取 MCP prompts/get 的 messages 字段；若省略: 无法提取标准 prompt 消息
        parts: list[str] = []  # 新增代码+MCPPrompt: 准备累积说明和多条消息；若省略: 多消息 prompt 无法合并展示
        if description:  # 新增代码+MCPPrompt: 只有说明非空时才输出说明行；若省略: 空说明会产生噪声
            parts.append(f"description: {description}")  # 新增代码+MCPPrompt: 保存 prompt 说明；若省略: 模型缺少选择和遵循 prompt 的语义依据
        if isinstance(messages, list):  # 新增代码+MCPPrompt: 仅当 messages 是数组时逐项处理；若省略: 非列表 messages 可能导致遍历异常
            for index, message in enumerate(messages, start=1):  # 新增代码+MCPPrompt: 遍历 prompts/get 返回的每条消息；若省略: prompt 正文不会被提取
                if not isinstance(message, dict):  # 新增代码+MCPPrompt: 跳过非对象消息；若省略: 异常 server 返回会让格式化崩溃
                    continue  # 新增代码+MCPPrompt: 保持单个坏消息不影响其他消息；若省略: 容错路径无法继续
                role = str(message.get("role", "") or "unknown")  # 新增代码+MCPPrompt: 读取消息角色并兜底；若省略: 用户和模型不知道文本应作为哪类消息理解
                content_text = self._mcp_prompt_content_to_text(message.get("content"))  # 新增代码+MCPPrompt: 把消息 content 转成文本；若省略: 文本、图片或资源内容不会被统一展示
                parts.append(f"[{index}] role={role}\n{content_text}")  # 新增代码+MCPPrompt: 保存带序号和角色的消息正文；若省略: 多条 prompt 消息会混在一起难以审计
        if parts:  # 新增代码+MCPPrompt: 如果提取到说明或消息；若省略: 有效 prompt 内容可能继续走 JSON 兜底
            return "\n".join(parts)  # 新增代码+MCPPrompt: 用换行合并 prompt 片段；若省略: 多消息 prompt 无法清晰展示
        return json.dumps(result, ensure_ascii=False)  # 新增代码+MCPPrompt: 没有标准 messages 时返回完整 JSON；若省略: 非标准 prompt 结果会丢失

    def _mcp_prompt_content_to_text(self, content: Any) -> str:  # 新增代码+MCPPrompt: 将单条 prompt message 的 content 转为文本；若省略: _mcp_prompt_result_to_text 会混入复杂分支
        if isinstance(content, dict) and content.get("type") == "text":  # 新增代码+MCPPrompt: 识别标准文本 content；若省略: 最常见 prompt 文本不会被优先提取
            return str(content.get("text", ""))  # 新增代码+MCPPrompt: 返回文本字段；若省略: prompt 正文会丢失
        if isinstance(content, dict):  # 新增代码+MCPPrompt: 处理非文本字典 content；若省略: 图片、资源或其他内容块会被丢弃
            return json.dumps(content, ensure_ascii=False)  # 新增代码+MCPPrompt: 用 JSON 兜底展示非文本内容；若省略: 调试非标准 MCP server 更困难
        if isinstance(content, list):  # 新增代码+MCPPrompt: 兼容少数 server 把 content 做成数组的情况；若省略: 多块 content 会被整体 JSON 化且可读性差
            return "\n".join(self._mcp_prompt_content_to_text(item) for item in content)  # 新增代码+MCPPrompt: 递归格式化并合并多个 content 块；若省略: 多块 prompt 内容无法清晰阅读
        return str(content)  # 新增代码+MCPPrompt: 对其他类型做字符串兜底；若省略: None 或简单值 content 会导致返回缺失


class McpHttpClient(McpStdioClient):  # 新增代码+MCPTransport: 定义最小 Streamable HTTP MCP client；若省略: 远程 HTTP MCP server 无法被 learning_agent 调用
    def __init__(self, config: McpServerConfig, request_timeout_seconds: float = 5.0) -> None:  # 新增代码+MCPTransport: 接收远程 server 配置和请求超时；若省略: HTTP 连接参数无法保存
        super().__init__(config, request_timeout_seconds)  # 新增代码+MCPTransport: 复用 stdio client 的结果格式化和公共字段；若省略: tools/resources/prompts 文本转换需要重复实现
        self._started = False  # 新增代码+MCPTransport: 记录 HTTP client 是否完成 initialize；若省略: 未初始化也可能发送业务请求
        self._session_id = ""  # 新增代码+MCPTransport: 保存服务器返回的 Mcp-Session-Id；若省略: 有状态 Streamable HTTP server 后续请求会被拒绝
        self._protocol_version = "2025-11-25"  # 新增代码+MCPStream: 保存 HTTP 请求使用的新版 MCP 协议版本；若省略: 后续请求会退回旧协议版本导致流状态能力协商不准确
        self._auth_challenge: McpAuthChallenge | None = None  # 新增代码+MCPAuthMetadata: 保存最近一次 401 鉴权挑战；若省略: authenticate 伪工具无法解释登录入口
        self._stream_state = McpHttpStreamState()  # 新增代码+MCPStream: 保存当前 HTTP SSE 流状态；若省略: POST SSE 解析后 registry 无法暴露 last_event_id 和 retry_ms
        self._recent_stream_events: list[McpHttpStreamEvent] = []  # 新增代码+MCPStream: 保存最近解析到的 SSE 事件；若省略: 后续排查流消息时没有最近事件缓存

    def start(self) -> None:  # 新增代码+MCPTransport: 执行 HTTP MCP 初始化握手；若省略: list_tools 和 call_tool 没有协议前置步骤
        if self._started:  # 新增代码+MCPTransport: 避免重复初始化同一个 HTTP client；若省略: 重复 start 会多次发送 initialize
            return  # 新增代码+MCPTransport: 已初始化时直接返回保持幂等；若省略: registry 重复启动可能污染会话
        result = self._send_request(  # 新增代码+MCPTransport: 发送 initialize 请求并读取协商结果；若省略: HTTP server 可能拒绝后续请求
            "initialize",  # 新增代码+MCPTransport: 指定 MCP 初始化方法；若省略: server 不知道这是生命周期第一步
            {  # 新增代码+MCPTransport: 构造初始化参数对象；若省略: initialize 缺少协议元数据
                "protocolVersion": "2025-11-25",  # 新增代码+MCPStream: 使用支持流状态的 MCP HTTP 规范版本；若省略: server 可能按旧版本返回或忽略新流语义
                "capabilities": {},  # 新增代码+MCPTransport: 声明最小客户端没有额外能力；若省略: 初始化参数不完整
                "clientInfo": {"name": "OpenHarness", "version": "0.1"},  # 新增代码+MCPTransport: 提供客户端标识；若省略: server 无法记录调用方来源
            },  # 新增代码+MCPTransport: 初始化参数结束；若省略: Python 语法不完整
        )  # 新增代码+MCPTransport: initialize 响应读取完成；若省略: 后续无法保存协议版本
        self._protocol_version = str(result.get("protocolVersion", "") or "2025-11-25")  # 新增代码+MCPStream: 保存 server 协商后的协议版本并用新版默认值兜底；若省略: 后续请求可能使用旧版本头
        self._started = True  # 新增代码+MCPTransport: 标记 HTTP client 已完成初始化；若省略: list_tools 会被误判为未启动
        self._send_notification("notifications/initialized", {})  # 新增代码+MCPTransport: 通知 server 客户端已就绪；若省略: 部分 MCP server 不会进入正常操作阶段

    def close(self) -> None:  # 新增代码+MCPTransport: 关闭 HTTP client 的本地状态；若省略: registry.close 后状态仍显示已启动
        if self._session_id:  # 新增代码+MCPStream: 只有已有 HTTP session 时才请求服务端关闭；若省略: 无会话 close 会发送无意义 DELETE
            self._delete_session()  # 新增代码+MCPStream: 尽力发送 DELETE 关闭远端 session；若省略: 有状态 server 可能残留旧会话
        self._started = False  # 新增代码+MCPTransport: 清理启动标记；若省略: 复用 client 时可能跳过 initialize
        self._session_id = ""  # 新增代码+MCPTransport: 清理 session id；若省略: 下次启动可能误带旧会话
        self._stream_state = McpHttpStreamState()  # 新增代码+MCPStream: close 后清空流状态；若省略: registry.close 后仍会看到旧 SSE 游标和错误
        self._recent_stream_events = []  # 新增代码+MCPStream: close 后清空最近事件缓存；若省略: 下次会话可能混入旧事件记录
        self._pending_notifications = []  # 新增代码+MCPLifecycleV2: close 后清空 HTTP SSE 捕获的 lifecycle notifications；若没有这行代码，下个 HTTP 会话可能误刷新旧工具目录

    def authenticate(self, arguments: dict[str, Any] | None = None) -> str:  # 新增代码+MCPAuthMetadata: 返回当前 HTTP MCP server 的鉴权说明；若省略: mcp__server__authenticate 工具没有可执行目标
        challenge = self._auth_challenge  # 新增代码+MCPAuthMetadata: 读取最近保存的鉴权挑战；若省略: 后续无法判断 server 是否真的返回过 401
        if challenge is None:  # 新增代码+MCPAuthMetadata: 处理用户提前调用 authenticate 的情况；若省略: 无挑战时会访问 None 字段崩溃
            return f"mcp__{self.config.name}__authenticate：当前还没有收到该 server 的 401 WWW-Authenticate 鉴权挑战。"  # 新增代码+MCPAuthMetadata: 返回可恢复说明；若省略: 用户不知道需要先启动或调用 server
        lines = [f"mcp__{self.config.name}__authenticate：MCP server `{challenge.server_name}` 需要鉴权。"]  # 新增代码+MCPAuthMetadata: 输出工具标题和目标 server；若省略: 模型无法把说明对应到具体 server
        lines.append(f"HTTP 状态：{challenge.status_code}")  # 新增代码+MCPAuthMetadata: 输出 401 状态码；若省略: 用户无法确认这是认证需求
        if challenge.resource_metadata_url:  # 新增代码+MCPAuthMetadata: 如果服务端提供了 resource_metadata；若省略: metadata URL 不会展示
            lines.append(f"resource_metadata：{challenge.resource_metadata_url}")  # 新增代码+MCPAuthMetadata: 展示受保护资源 metadata URL；若省略: 用户无法按 OAuth 发现入口继续排查
        else:  # 新增代码+MCPAuthMetadata: 处理没有 metadata URL 的 401；若省略: 输出会让用户以为信息完整
            lines.append("resource_metadata：服务端未在 WWW-Authenticate 中提供。")  # 新增代码+MCPAuthMetadata: 明确缺失字段；若省略: 用户不知道是不是解析失败
        if challenge.www_authenticate:  # 新增代码+MCPAuthMetadata: 如果有原始 header；若省略: 原始鉴权挑战无法审计
            lines.append(f"WWW-Authenticate：{challenge.www_authenticate}")  # 新增代码+MCPAuthMetadata: 展示原始 header；若省略: 用户无法核对服务端返回细节
        if challenge.error_body:  # 新增代码+MCPAuthMetadata: 如果服务端返回错误正文；若省略: server 额外提示会丢失
            lines.append(f"错误正文：{challenge.error_body}")  # 新增代码+MCPAuthMetadata: 展示错误正文；若省略: 用户看不到服务端可能给出的登录提示
        lines.append("当前最小版不会自动打开浏览器、不会自动请求 metadata URL、不会自动交换 OAuth token。")  # 新增代码+MCPAuthMetadata: 明确 SSRF 和 OAuth UI 边界；若省略: 模型可能误以为已经自动登录
        lines.append("如果你已经从可信流程拿到访问令牌，请把它写入 mcp_servers.json 的 headers.Authorization。")  # 新增代码+MCPAuthMetadata: 指向当前已支持的 token 配置入口；若省略: 用户不知道怎样让下一次请求带 token
        lines.append('示例：{"headers": {"Authorization": "Bearer <access-token>"}}')  # 新增代码+MCPAuthMetadata: 给出 Bearer header 写法；若省略: 初学者可能把 token 放错字段
        lines.append("不要把 access token 放进 url 查询参数，也不要把不可信 metadata URL 当作自动可访问目标。")  # 新增代码+MCPAuthMetadata: 强调 token 和 SSRF 安全边界；若省略: 用户可能采用不安全配置
        return "\n".join(lines)  # 新增代码+MCPAuthMetadata: 返回完整鉴权说明文本；若省略: 工具无法把指导交回模型

    def _send_request(self, method: str, params: dict[str, Any], allow_session_rebuild: bool = True) -> dict[str, Any]:  # 修改代码+MCPStream: 支持 session 404 后最多重建一次再重试；若省略: session 过期会直接导致 tools/list 或 tools/call 失败
        if method != "initialize" and not self._started:  # 新增代码+MCPTransport: 禁止初始化前发送业务请求；若省略: server 生命周期顺序可能被破坏
            raise RuntimeError(f"MCP HTTP server {self.config.name} is not started")  # 新增代码+MCPTransport: 抛出清晰未启动错误；若省略: 用户只会看到底层 HTTP 错误
        request_id = self._next_id  # 新增代码+MCPTransport: 读取当前 JSON-RPC 请求 id；若省略: 响应无法匹配请求
        self._next_id += 1  # 新增代码+MCPTransport: 递增请求 id 避免后续重复；若省略: 多请求响应可能混淆
        message = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}  # 新增代码+MCPTransport: 构造 JSON-RPC 请求对象；若省略: server 收不到标准 MCP 消息
        try:  # 新增代码+MCPStream: 捕获 session 过期并做一次受控重建；若省略: 404 恢复逻辑没有入口
            body, content_type = self._post_json(message, include_session=method != "initialize")  # 新增代码+MCPTransport: POST 请求并读取响应正文和类型；若省略: 无法解析 HTTP 响应
        except McpSessionExpired:  # 新增代码+MCPStream: 单独处理旧 session 被服务端判定不存在；若省略: 无法把 404 转成重建会话流程
            if method == "initialize" or not allow_session_rebuild:  # 新增代码+MCPStream: initialize 或已重试过时禁止再次递归；若省略: 可能陷入无限初始化循环
                raise  # 新增代码+MCPStream: 保留不能恢复的过期错误；若省略: 真正失败会被误吞
            self._session_id = ""  # 新增代码+MCPStream: 清掉旧 session 让下一次 initialize 不携带过期 id；若省略: start 可能继续复用坏会话
            self._started = False  # 新增代码+MCPStream: 标记需要重新初始化；若省略: start 会因为已启动而直接返回
            self.start()  # 新增代码+MCPStream: 重新执行 initialize 获取新 session；若省略: 原请求重试时仍没有有效会话
            return self._send_request(method, params, allow_session_rebuild=False)  # 新增代码+MCPStream: 原请求只重试一次；若省略: 用户操作不会在新 session 上继续执行
        response_message = self._parse_http_response_message(body, content_type, request_id, method)  # 新增代码+MCPTransport: 解析 JSON 或 SSE 格式响应；若省略: Streamable HTTP 两种响应形态无法兼容
        if "error" in response_message:  # 新增代码+MCPTransport: 检查 JSON-RPC error；若省略: server 错误会被当成成功
            raise RuntimeError(f"MCP HTTP request {method} failed: {response_message['error']}")  # 新增代码+MCPTransport: 抛出带方法名的可读错误；若省略: 调试远程失败更困难
        result = response_message.get("result", {})  # 新增代码+MCPTransport: 取出 JSON-RPC result；若省略: 调用方拿不到 MCP 返回数据
        return result if isinstance(result, dict) else {"value": result}  # 新增代码+MCPTransport: 保证返回字典；若省略: inherited list_tools 的 .get 可能崩溃

    def _send_notification(self, method: str, params: dict[str, Any]) -> None:  # 新增代码+MCPTransport: 通过 HTTP POST 发送 JSON-RPC notification；若省略: initialized 通知会误等 JSON-RPC 响应
        message = {"jsonrpc": "2.0", "method": method, "params": params}  # 新增代码+MCPTransport: 构造无 id 的 notification；若省略: server 会把通知误当请求
        self._post_json(message, include_session=True)  # 新增代码+MCPTransport: 发送通知并忽略 202/200 响应体；若省略: server 收不到 initialized 信号

    def _post_json(self, message: dict[str, Any], include_session: bool) -> tuple[str, str]:  # 新增代码+MCPTransport: 统一发送 HTTP JSON-RPC 消息；若省略: 请求和通知会重复 header/body 逻辑
        if not self.config.url:  # 新增代码+MCPTransport: 检查 HTTP endpoint 是否存在；若省略: urllib 会报难懂的空 URL 错误
            raise RuntimeError(f"MCP HTTP server {self.config.name} 缺少 url 配置。")  # 新增代码+MCPTransport: 抛出可读配置错误；若省略: 用户不知道应补 mcp_servers.json 的 url
        request_body = json.dumps(message, ensure_ascii=False).encode("utf-8")  # 新增代码+MCPTransport: 把 JSON-RPC 消息编码为 UTF-8；若省略: HTTP 请求没有 body
        request = urllib.request.Request(self.config.url, data=request_body, method="POST")  # 新增代码+MCPTransport: 创建 POST 请求到 MCP endpoint；若省略: 无法向远程 server 发送消息
        for key, value in self._http_headers(include_session).items():  # 新增代码+MCPTransport: 遍历标准和自定义请求头；若省略: Accept、Content-Type、鉴权和 session 无法写入
            request.add_header(key, value)  # 新增代码+MCPTransport: 写入单个 HTTP header；若省略: 远程 server 可能拒绝请求
        try:  # 新增代码+MCPTransport: 捕获 HTTP 和网络错误并转成可读 RuntimeError；若省略: urllib 异常会直接泄漏给上层
            with urllib.request.urlopen(request, timeout=self.request_timeout_seconds) as response:  # 新增代码+MCPTransport: 发送请求并设置超时；若省略: 网络卡住可能无限等待
                session_id = response.headers.get("Mcp-Session-Id", "")  # 新增代码+MCPTransport: 读取 server 返回的 session id；若省略: 有状态 server 后续请求缺少会话
                if session_id:  # 新增代码+MCPTransport: 只有响应实际返回 session 时才更新；若省略: 空 header 可能覆盖已有 session
                    self._session_id = session_id  # 新增代码+MCPTransport: 保存 session id 给后续请求；若省略: tools/list 等会缺少 Mcp-Session-Id
                content_type = response.headers.get("Content-Type", "")  # 新增代码+MCPTransport: 读取响应类型用于区分 JSON 和 SSE；若省略: Streamable HTTP 响应解析不可靠
                response_body = response.read().decode("utf-8")  # 新增代码+MCPTransport: 读取 UTF-8 响应正文；若省略: 无法解析 JSON-RPC 响应
                return response_body, content_type  # 新增代码+MCPTransport: 返回正文和内容类型；若省略: 调用方无法继续解析
        except urllib.error.HTTPError as error:  # 新增代码+MCPTransport: 捕获 HTTP 4xx/5xx；若省略: 错误体和状态码不易读
            error_body = error.read().decode("utf-8", errors="replace")  # 新增代码+MCPTransport: 读取错误响应体；若省略: 用户不知道远程 server 返回了什么
            if error.code == 401:  # 新增代码+MCPAuthMetadata: 识别 MCP HTTP 鉴权挑战；若省略: 需要登录的 server 会被当成普通启动失败
                www_authenticate = error.headers.get("WWW-Authenticate", "")  # 新增代码+MCPAuthMetadata: 读取服务端返回的鉴权 header；若省略: resource_metadata URL 无法解析
                self._auth_challenge = self._build_auth_challenge(error.code, www_authenticate, error_body)  # 新增代码+MCPAuthMetadata: 保存结构化鉴权挑战；若省略: authenticate 工具无法生成说明
                raise McpAuthenticationRequired(self._auth_challenge) from error  # 新增代码+MCPAuthMetadata: 用专门异常交给 registry 注册伪工具；若省略: 上层无法区分登录需求和真实错误
            if error.code == 404 and include_session and self._session_id:  # 新增代码+MCPStream: 只有带旧 session 的 404 才视为会话过期；若省略: 普通 404 会被错误重建
                raise McpSessionExpired(f"MCP HTTP server {self.config.name} session 已过期：HTTP 404，{error_body}") from error  # 新增代码+MCPStream: 抛出专用异常触发一次重建；若省略: _send_request 无法区分过期 session
            raise RuntimeError(f"MCP HTTP server {self.config.name} HTTP {error.code}: {error_body}") from error  # 新增代码+MCPTransport: 抛出带状态码和正文的错误；若省略: 排查远程失败更困难
        except urllib.error.URLError as error:  # 新增代码+MCPTransport: 捕获连接失败、DNS 或超时类错误；若省略: 网络错误会以底层类型冒出
            raise RuntimeError(f"MCP HTTP server {self.config.name} 连接失败：{error}") from error  # 新增代码+MCPTransport: 抛出带 server 名的连接错误；若省略: 用户不知道哪个 server 失败

    def _delete_session(self) -> None:  # 新增代码+MCPStream: 关闭远端 HTTP session 的尽力方法；若省略: close 只能清本地状态不能通知 server
        if not self.config.url:  # 新增代码+MCPStream: 缺少 URL 时无法发送 DELETE；若省略: urllib 会抛出难懂的空 URL 错误
            self._stream_state.last_error = f"MCP HTTP server {self.config.name} 缺少 url 配置。"  # 新增代码+MCPStream: 记录关闭失败原因但不中断本地清理；若省略: close 失败原因无法排查
            return  # 新增代码+MCPStream: 放弃远端关闭并继续本地清理；若省略: close 会因为配置错误阻断 registry.close
        request = urllib.request.Request(self.config.url, method="DELETE")  # 新增代码+MCPStream: 创建无请求体的 DELETE 请求；若省略: server 不会收到 session 关闭信号
        for key, value in self._http_headers(include_session=True, accept="application/json, text/event-stream", include_content_type=False).items():  # 新增代码+MCPStream: 发送协议版本、session 和自定义 headers 且不带 Content-Type；若省略: DELETE 可能缺少会话或被误判有 JSON body
            request.add_header(key, value)  # 新增代码+MCPStream: 写入单个 DELETE header；若省略: Authorization、Mcp-Session-Id 等不会发送
        try:  # 新增代码+MCPStream: 捕获 DELETE 关闭中的 HTTP 和网络错误；若省略: registry.close 可能被远端错误打断
            with urllib.request.urlopen(request, timeout=self.request_timeout_seconds) as response:  # 新增代码+MCPStream: 发出 DELETE 并等待服务端确认；若省略: 远端 session 不会被主动释放
                response.read()  # 新增代码+MCPStream: 读取并丢弃响应体以完整结束连接；若省略: 底层连接可能未被消费干净
        except urllib.error.HTTPError as error:  # 新增代码+MCPStream: 捕获 DELETE 的 HTTP 错误；若省略: 405/401 等边界会冒泡
            error_body = error.read().decode("utf-8", errors="replace")  # 新增代码+MCPStream: 读取错误正文用于记录和鉴权挑战；若省略: last_error 和 auth 说明缺少服务端细节
            if error.code == 405:  # 新增代码+MCPStream: 识别 server 不允许客户端 DELETE session；若省略: 合法非致命边界会污染 close
                return  # 新增代码+MCPStream: 忽略 405 并继续本地清理；若省略: registry.close 会被不支持 DELETE 的 server 阻断
            if error.code == 401:  # 新增代码+MCPStream: 识别关闭时遇到鉴权挑战；若省略: authenticate 工具拿不到最新挑战信息
                www_authenticate = error.headers.get("WWW-Authenticate", "")  # 新增代码+MCPStream: 读取 WWW-Authenticate header；若省略: resource_metadata URL 无法解析
                self._auth_challenge = self._build_auth_challenge(error.code, www_authenticate, error_body)  # 新增代码+MCPStream: 保存鉴权挑战但不抛出；若省略: close 遇到 401 后用户缺少恢复线索
                return  # 新增代码+MCPStream: 401 不阻断本地关闭；若省略: 鉴权失败会让 registry.close 无法完成
            self._stream_state.last_error = f"DELETE session HTTP {error.code}: {error_body}"  # 新增代码+MCPStream: 记录其他 DELETE HTTP 错误；若省略: close 失败原因会丢失
        except urllib.error.URLError as error:  # 新增代码+MCPStream: 捕获 DELETE 连接失败、DNS 或超时；若省略: 网络错误会阻断本地清理
            self._stream_state.last_error = f"DELETE session 连接失败：{error}"  # 新增代码+MCPStream: 记录网络错误但继续关闭；若省略: 用户无法知道远端关闭没有成功

    def listen_stream(self, max_events: int = 5, timeout_seconds: float = 2.0, resume: bool = True) -> str:  # 新增代码+MCPStream: 有界读取 GET SSE 事件；若省略: agent 无法主动监听远程 server 通知
        if not self._started:  # 新增代码+MCPStream: 未初始化时先完成 initialize；若省略: GET 监听可能缺少协议版本和 session
            self.start()  # 新增代码+MCPStream: 启动 HTTP MCP client；若省略: 有状态 server 可能拒绝 GET
        safe_max_events = self._safe_stream_max_events(max_events)  # 修改代码+MCPStream: 用 helper 解析并限制事件数；若省略: 非法 max_events 会抛裸 ValueError 或让输出过长
        safe_timeout = self._safe_stream_timeout(timeout_seconds)  # 修改代码+MCPStream: 用 helper 解析并限制等待时间；若省略: 非法 timeout_seconds 会抛裸 ValueError 或让监听卡太久
        self._stream_state.last_opened_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+MCPStream: 记录打开时间；若省略: 状态无法判断新旧
        try:  # 新增代码+MCPStream: 捕获 GET 监听中的 HTTP 和网络错误；若省略: 405/连接失败会直接打断 agent
            body, content_type = self._get_stream_body(safe_timeout, resume, safe_max_events)  # 修改代码+MCPStream: 执行 GET 并按事件数有界读取响应；若省略: 长连接 SSE 可能一直等 EOF
        except urllib.error.HTTPError as error:  # 新增代码+MCPStream: 捕获 HTTP 错误；若省略: 405 边界会变成异常
            if error.code == 405:  # 新增代码+MCPStream: 识别 server 不提供 GET stream；若省略: 不支持监听会误报失败
                self._stream_state.last_error = "HTTP 405 Method Not Allowed"  # 新增代码+MCPStream: 保存最近错误；若省略: stream_state 无法展示边界
                return f"MCP HTTP stream：server {self.config.name} 不提供 GET 监听流（HTTP 405）。"  # 新增代码+MCPStream: 返回可读边界；若省略: 用户不知道这是允许的非致命情况
            error_body = error.read().decode("utf-8", errors="replace")  # 新增代码+MCPStream: 读取错误正文；若省略: 诊断信息会丢失
            self._stream_state.last_error = f"HTTP {error.code}: {error_body}"  # 新增代码+MCPStream: 保存错误状态；若省略: 后续无法查看失败原因
            raise RuntimeError(f"MCP HTTP stream {self.config.name} HTTP {error.code}: {error_body}") from error  # 新增代码+MCPStream: 抛出清晰错误；若省略: 调试远程失败更困难
        except (urllib.error.URLError, TimeoutError) as error:  # 修改代码+MCPStream: 捕获连接失败或底层读取超时；若省略: 长连接超时会以底层异常泄漏
            self._stream_state.last_error = str(error)  # 新增代码+MCPStream: 保存网络错误；若省略: stream_state 缺少失败原因
            raise RuntimeError(f"MCP HTTP stream {self.config.name} 连接失败：{error}") from error  # 新增代码+MCPStream: 返回带 server 名的错误；若省略: 用户不知道哪个 server 失败
        if "text/event-stream" not in content_type.lower():  # 修改代码+MCPStream: 即使非 SSE 响应体为空也返回清晰边界；若省略: 空 HTML/JSON 响应会被误报成没有事件
            self._stream_state.last_error = f"unexpected content-type: {content_type}"  # 新增代码+MCPStream: 保存类型错误；若省略: 诊断缺少响应类型
            return f"MCP HTTP stream：server {self.config.name} 返回非 SSE 内容类型：{content_type or '(空)'}"  # 修改代码+MCPStream: 返回可读类型边界并处理空类型；若省略: 用户不知道 server 返回了什么
        events = self._parse_sse_events(body)[:safe_max_events]  # 新增代码+MCPStream: 解析并截断事件；若省略: 输出可能过长
        return self._format_stream_events(events)  # 新增代码+MCPStream: 返回可读事件摘要；若省略: 工具结果难以理解

    def _safe_stream_max_events(self, raw_max_events: Any) -> int:  # 新增代码+MCPStream: 安全解析 GET 监听事件数上限；若省略: 坏参数会抛裸异常或绕过上限
        try:  # 新增代码+MCPStream: 捕获无法转整数的输入；若省略: 字符串错误值会抛出不友好的 ValueError
            parsed_max_events = int(raw_max_events or 5)  # 新增代码+MCPStream: 把输入转成整数并给空值默认 5；若省略: 后续无法统一限制范围
        except (TypeError, ValueError):  # 新增代码+MCPStream: 处理 None 以外的坏类型或坏文本；若省略: 非数字输入会打断 agent
            parsed_max_events = 5  # 新增代码+MCPStream: 非法事件数回退默认值；若省略: 用户一次传错参数会导致监听失败
        return max(1, min(parsed_max_events, 20))  # 新增代码+MCPStream: 限制事件数到 1 到 20；若省略: 0 会无输出、过大值会撑爆上下文

    def _safe_stream_timeout(self, raw_timeout_seconds: Any) -> float:  # 新增代码+MCPStream: 安全解析 GET 监听超时时间；若省略: 坏参数会抛裸异常或等待过久
        try:  # 新增代码+MCPStream: 捕获无法转浮点数的输入；若省略: 字符串错误值会抛出不友好的 ValueError
            parsed_timeout = float(raw_timeout_seconds or 2.0)  # 新增代码+MCPStream: 把输入转成秒数并给空值默认 2 秒；若省略: 后续无法统一限制范围
        except (TypeError, ValueError):  # 新增代码+MCPStream: 处理 None 以外的坏类型或坏文本；若省略: 非数字输入会打断 agent
            parsed_timeout = 2.0  # 新增代码+MCPStream: 非法超时回退默认值；若省略: 用户一次传错参数会导致监听失败
        return max(0.1, min(parsed_timeout, 10.0))  # 新增代码+MCPStream: 限制超时到 0.1 到 10 秒；若省略: 太小会误超时、太大会卡住

    def _get_stream_body(self, timeout_seconds: float, resume: bool, max_events: int) -> tuple[str, str]:  # 修改代码+MCPStream: 执行 GET 请求并返回有界 SSE 正文和类型；若省略: listen_stream 会混入底层 HTTP 细节
        if not self.config.url:  # 新增代码+MCPStream: 检查 HTTP endpoint 是否存在；若省略: urllib 会报难懂的空 URL 错误
            raise RuntimeError(f"MCP HTTP server {self.config.name} 缺少 url 配置。")  # 新增代码+MCPStream: 抛出可读配置错误；若省略: 用户不知道应补 mcp_servers.json 的 url
        request = urllib.request.Request(self.config.url, method="GET")  # 新增代码+MCPStream: 创建指向 MCP endpoint 的 GET 请求；若省略: 无法打开远程监听流
        headers = self._http_headers(include_session=True, accept="text/event-stream", include_content_type=False)  # 修改代码+MCPStream: 复用会话但不发送 GET Content-Type；若省略: server 可能把无 body 的 GET 当 JSON 请求
        if resume and self._stream_state.last_event_id:  # 新增代码+MCPStream: 有游标且允许续传时才发送 Last-Event-ID；若省略: 每次监听都可能从头开始
            headers["Last-Event-ID"] = self._stream_state.last_event_id  # 新增代码+MCPStream: 写入 SSE 续传游标；若省略: 断线恢复无法从上次事件继续
        for key, value in headers.items():  # 新增代码+MCPStream: 遍历要发送的 HTTP header；若省略: header 字典不会进入真实请求
            request.add_header(key, value)  # 新增代码+MCPStream: 写入单个 GET 请求头；若省略: server 收不到 Accept/session/protocol
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # 新增代码+MCPStream: 打开 GET 流并设置超时；若省略: 监听可能永久卡住
            session_id = response.headers.get("Mcp-Session-Id", "")  # 新增代码+MCPStream: 读取 GET 响应可能更新的 session；若省略: server 轮换 session 时客户端会落后
            if session_id:  # 新增代码+MCPStream: 只有响应实际返回 session 时才更新；若省略: 空 header 可能覆盖已有 session
                self._session_id = session_id  # 新增代码+MCPStream: 保存新 session 给后续请求；若省略: 后续监听或调用可能带旧会话
            content_type = response.headers.get("Content-Type", "")  # 新增代码+MCPStream: 读取响应类型用于确认 SSE；若省略: listen_stream 无法判断返回内容是否正确
            response_body = self._read_stream_body(response, timeout_seconds, max_events)  # 修改代码+MCPStream: 按行读取到事件上限或超时；若省略: 长连接无 EOF 时会挂住
            return response_body, content_type  # 新增代码+MCPStream: 返回正文和类型给 listen_stream；若省略: 调用方拿不到 GET 结果

    def _read_stream_body(self, response: Any, timeout_seconds: float, max_events: int) -> str:  # 新增代码+MCPStream: 从 HTTPResponse 按行读取有界 SSE 文本；若省略: 无 Content-Length 长连接会卡住
        deadline = time.monotonic() + timeout_seconds  # 新增代码+MCPStream: 计算本次监听截止时间；若省略: 循环只能依赖底层 socket timeout
        chunks: list[str] = []  # 新增代码+MCPStream: 保存已读取的 SSE 文本片段；若省略: 后续无法解析事件
        event_count = 0  # 新增代码+MCPStream: 记录已经读到的完整事件块数量；若省略: 无法在 max_events 达到时停止
        current_event_lines: list[str] = []  # 新增代码+MCPStream: 记录当前事件块是否已有内容；若省略: 连续空行会被误算成事件
        try:  # 新增代码+MCPStream: 捕获长连接读取超时；若省略: socket timeout 无法转成可读边界
            while event_count < max_events:  # 新增代码+MCPStream: 按事件上限循环读取；若省略: 远程流可能无限输出
                if time.monotonic() >= deadline:  # 新增代码+MCPStream: 检查是否超过本次等待时间；若省略: server 不发 EOF 时可能等待过久
                    break  # 新增代码+MCPStream: 到期后返回已收集内容；若省略: deadline 不会真正生效
                line_bytes = response.readline()  # 新增代码+MCPStream: 读取一行 SSE 数据；若省略: 无法按事件边界增量处理
                if not line_bytes:  # 新增代码+MCPStream: EOF 时停止读取；若省略: 空字节可能形成死循环
                    break  # 新增代码+MCPStream: 服务端关闭连接后返回已有内容；若省略: 已完成事件无法交给解析器
                line_text = line_bytes.decode("utf-8", errors="replace")  # 新增代码+MCPStream: 把字节行转成文本；若省略: SSE 解析器无法处理 bytes
                chunks.append(line_text)  # 新增代码+MCPStream: 保存原始行文本；若省略: 事件正文会丢失
                normalized_line = line_text.rstrip("\r\n")  # 新增代码+MCPStream: 去掉行尾判断空行；若省略: Windows 换行下事件边界识别不稳定
                if normalized_line.startswith(":"):  # 修改代码+MCPStream: 识别 SSE 注释心跳且不计入业务事件；若省略: keepalive 会误消耗 max_events
                    continue  # 修改代码+MCPStream: 注释仍保留在原始文本但不增加当前事件内容；若省略: 真实事件可能被心跳挤掉
                if normalized_line == "":  # 新增代码+MCPStream: SSE 空行代表一个事件块结束；若省略: 无法按事件计数停止
                    if current_event_lines:  # 新增代码+MCPStream: 只有当前块有内容才计作事件；若省略: 心跳空行会污染计数
                        event_count += 1  # 新增代码+MCPStream: 累加完整事件数量；若省略: max_events 永远不会触发
                        current_event_lines = []  # 新增代码+MCPStream: 清空当前事件缓存准备下一条；若省略: 后续事件会被合并计数
                    continue  # 新增代码+MCPStream: 空行处理完后继续读取下一行；若省略: 会把空行也加入当前事件内容
                current_event_lines.append(normalized_line)  # 新增代码+MCPStream: 记录当前事件已有内容；若省略: 事件结束时无法判断是否为空块
        except TimeoutError as error:  # 新增代码+MCPStream: 处理 socket 层读取超时；若省略: 长连接等待会泄漏底层异常
            if event_count > 0:  # 新增代码+MCPStream: 已收到完整事件时允许返回部分结果；若省略: 有用事件会因后续超时被丢弃
                return "".join(chunks)  # 新增代码+MCPStream: 返回已收集的完整和可能部分文本；若省略: 调用方拿不到已到达事件
            raise urllib.error.URLError("GET stream timeout before a complete SSE event") from error  # 新增代码+MCPStream: 没有完整事件时抛出清晰超时；若省略: 用户不知道是等待事件超时
        return "".join(chunks)  # 新增代码+MCPStream: 返回读取到的 SSE 文本；若省略: listen_stream 没有正文可解析

    def _format_stream_events(self, events: list[McpHttpStreamEvent]) -> str:  # 新增代码+MCPStream: 把 SSE 事件格式化成可读文本；若省略: 工具结果难以被用户和测试检查
        if not events:  # 新增代码+MCPStream: 处理本次没有事件的合法情况；若省略: 空列表会输出不清晰
            return f"MCP HTTP stream：server {self.config.name} 本次没有收到 SSE 事件。"  # 新增代码+MCPStream: 返回空结果说明；若省略: 用户不知道是失败还是暂时无事件
        lines = [f"MCP HTTP stream：server {self.config.name} 收到 {len(events)} 条 SSE 事件。"]  # 新增代码+MCPStream: 构造摘要标题；若省略: 输出缺少 server 和事件数量
        for index, event in enumerate(events, start=1):  # 新增代码+MCPStream: 逐条格式化事件；若省略: 只能看到汇总看不到内容
            data_text = self._truncate_stream_data(event.data)  # 新增代码+MCPStream: 截断单条事件正文；若省略: 超长 data 会撑爆上下文
            lines.append(f"{index}. id={event.event_id or '(无)'} event={event.event_type or '(默认)'} retry_ms={event.retry_ms if event.retry_ms is not None else '(无)'} data={data_text}")  # 修改代码+MCPStream: 输出事件核心字段和截断正文；若省略: listen-1/listen-2 等事件内容不可见
        return "\n".join(lines)  # 新增代码+MCPStream: 合并多行文本返回；若省略: 调用方拿不到可读摘要

    def _truncate_stream_data(self, data: str, max_chars: int = 1200) -> str:  # 新增代码+MCPStream: 限制单条 SSE data 输出长度；若省略: 大事件会撑爆上下文
        if len(data) <= max_chars:  # 新增代码+MCPStream: 短正文无需截断；若省略: 正常事件也会被添加噪声提示
            return data  # 新增代码+MCPStream: 原样返回短正文；若省略: 调用方看不到完整短事件
        return data[:max_chars] + f"...[SSE data 已截断，原始长度 {len(data)} 字符]"  # 新增代码+MCPStream: 返回截断正文并标注原始长度；若省略: 用户不知道输出不完整

    def _build_auth_challenge(self, status_code: int, www_authenticate: str, error_body: str) -> McpAuthChallenge:  # 新增代码+MCPAuthMetadata: 把 401 响应转换成结构化挑战；若省略: 解析逻辑会散落在异常处理和 authenticate 工具里
        resource_metadata_url = self._parse_www_authenticate_parameter(www_authenticate, "resource_metadata")  # 新增代码+MCPAuthMetadata: 提取 RFC9728 resource_metadata 参数；若省略: 用户看不到授权发现入口
        return McpAuthChallenge(  # 新增代码+MCPAuthMetadata: 返回结构化鉴权挑战；若省略: 上层无法携带 server、状态码和 header
            server_name=self.config.name,  # 新增代码+MCPAuthMetadata: 写入当前 server 名；若省略: 多 server 场景无法定位挑战来源
            status_code=status_code,  # 新增代码+MCPAuthMetadata: 写入 HTTP 状态码；若省略: authenticate 输出缺少 401 证据
            www_authenticate=www_authenticate,  # 新增代码+MCPAuthMetadata: 写入原始 WWW-Authenticate；若省略: 鉴权挑战不可审计
            resource_metadata_url=resource_metadata_url,  # 新增代码+MCPAuthMetadata: 写入解析出的 metadata URL；若省略: 用户需要手动从 header 里找
            error_body=error_body,  # 新增代码+MCPAuthMetadata: 写入错误正文；若省略: 服务端补充说明会丢失
        )  # 新增代码+MCPAuthMetadata: McpAuthChallenge 构造结束；若省略: Python 语法不完整

    def _parse_www_authenticate_parameter(self, header_value: str, parameter_name: str) -> str:  # 新增代码+MCPAuthMetadata: 从 WWW-Authenticate 中解析指定参数；若省略: 无法提取 resource_metadata
        marker = f"{parameter_name.lower()}="  # 新增代码+MCPAuthMetadata: 构造小写查找标记；若省略: 无法定位目标参数
        search_text = header_value.lower()  # 新增代码+MCPAuthMetadata: 转小写做大小写不敏感搜索；若省略: Resource_Metadata 大小写变化会漏掉
        marker_index = search_text.find(marker)  # 新增代码+MCPAuthMetadata: 查找参数起始位置；若省略: 后续不知道从哪里截取值
        if marker_index < 0:  # 新增代码+MCPAuthMetadata: 处理 header 不含目标参数；若省略: 截取会从错误位置开始
            return ""  # 新增代码+MCPAuthMetadata: 返回空字符串表示没有 metadata URL；若省略: 调用方无法判断缺失
        value_start = marker_index + len(marker)  # 新增代码+MCPAuthMetadata: 计算参数值开始位置；若省略: 结果会包含参数名
        if value_start >= len(header_value):  # 新增代码+MCPAuthMetadata: 处理参数后没有值的异常 header；若省略: 下标访问可能越界
            return ""  # 新增代码+MCPAuthMetadata: 空值返回空字符串；若省略: 异常 header 会导致解析崩溃
        if header_value[value_start] == '"':  # 新增代码+MCPAuthMetadata: 识别 quoted-string 参数值；若省略: 标准 resource_metadata="..." 会包含引号或截断错误
            value_chars: list[str] = []  # 新增代码+MCPAuthMetadata: 准备累积引号内字符；若省略: 无法处理转义字符
            escaped = False  # 新增代码+MCPAuthMetadata: 记录前一个字符是否是反斜杠；若省略: 带转义引号的 header 解析不正确
            for char in header_value[value_start + 1:]:  # 新增代码+MCPAuthMetadata: 遍历引号后的每个字符；若省略: 无法找到结束引号
                if escaped:  # 新增代码+MCPAuthMetadata: 如果上一字符是转义符；若省略: 被转义字符会被错误解释
                    value_chars.append(char)  # 新增代码+MCPAuthMetadata: 保留被转义字符；若省略: URL 中被转义字符会丢失
                    escaped = False  # 新增代码+MCPAuthMetadata: 结束转义状态；若省略: 后续所有字符都会被当成转义
                    continue  # 新增代码+MCPAuthMetadata: 继续解析下一个字符；若省略: 当前字符还会进入后续分支
                if char == "\\":  # 新增代码+MCPAuthMetadata: 识别转义符；若省略: quoted-string 转义不兼容
                    escaped = True  # 新增代码+MCPAuthMetadata: 标记下一字符被转义；若省略: 下一字符无法按字面值保留
                    continue  # 新增代码+MCPAuthMetadata: 转义符本身不加入结果；若省略: 返回值会多一个反斜杠
                if char == '"':  # 新增代码+MCPAuthMetadata: 找到结束引号；若省略: 会把后续 error/scope 参数也吞进去
                    return "".join(value_chars).strip()  # 新增代码+MCPAuthMetadata: 返回去空白后的参数值；若省略: 调用方拿不到解析结果
                value_chars.append(char)  # 新增代码+MCPAuthMetadata: 保存普通字符；若省略: URL 内容会丢失
            return "".join(value_chars).strip()  # 新增代码+MCPAuthMetadata: 容忍缺少结束引号的 header 并返回已解析内容；若省略: 异常服务端响应无法给出部分线索
        value_end = len(header_value)  # 新增代码+MCPAuthMetadata: 默认非引号参数读到字符串结尾；若省略: 无法截取裸值
        comma_index = header_value.find(",", value_start)  # 新增代码+MCPAuthMetadata: 查找参数分隔逗号；若省略: 裸值会包含后续参数
        if comma_index >= 0:  # 新增代码+MCPAuthMetadata: 如果存在逗号分隔；若省略: 后续参数会混入当前值
            value_end = comma_index  # 新增代码+MCPAuthMetadata: 把结束位置设为逗号；若省略: 截取范围不正确
        return header_value[value_start:value_end].strip()  # 新增代码+MCPAuthMetadata: 返回裸参数值；若省略: 非引号写法无法支持

    def _http_headers(self, include_session: bool, accept: str = "application/json, text/event-stream", include_content_type: bool = True) -> dict[str, str]:  # 修改代码+MCPStream: 构造可配置的 Streamable HTTP 请求头；若省略: GET 和 POST 不能安全复用 header 逻辑
        headers: dict[str, str] = {}  # 修改代码+MCPStream: 准备标准 MCP HTTP headers 容器；若省略: 后续无法按 GET/POST 条件填充
        if include_content_type:  # 新增代码+MCPStream: 只有带请求体的 POST 需要 Content-Type；若省略: GET listen 会误带 application/json
            headers["Content-Type"] = "application/json"  # 修改代码+MCPStream: 声明请求体是 JSON；若省略: POST server 可能无法解析请求
        headers["Accept"] = accept  # 修改代码+MCPStream: 按调用场景声明可接受响应类型；若省略: GET 无法只声明 text/event-stream
        headers.update(self.config.headers)  # 新增代码+MCPTransport: 合并用户配置的自定义 headers；若省略: Authorization 等鉴权配置不会生效
        if not include_content_type:  # 新增代码+MCPStream: GET listen 明确不允许 Content-Type；若省略: 用户配置的 Content-Type 仍可能污染 GET
            for header_key in list(headers.keys()):  # 新增代码+MCPStream: 遍历副本以便安全删除 header；若省略: 删除时会修改正在迭代的字典
                if header_key.lower() == "content-type":  # 新增代码+MCPStream: 大小写不敏感识别 Content-Type；若省略: content-type 小写配置无法移除
                    headers.pop(header_key, None)  # 新增代码+MCPStream: 删除 GET 不应发送的 Content-Type；若省略: server 可能误判 GET 有 JSON body
        if include_session and self._protocol_version:  # 新增代码+MCPTransport: 初始化后的请求需要带协议版本；若省略: HTTP server 无法按协商版本处理
            headers["MCP-Protocol-Version"] = self._protocol_version  # 新增代码+MCPTransport: 写入 MCP 协议版本 header；若省略: 远程 server 可能按错误版本兼容
        if include_session and self._session_id:  # 新增代码+MCPTransport: 如果 server 下发 session，则后续请求必须携带；若省略: 有状态 server 可能返回 400
            headers["Mcp-Session-Id"] = self._session_id  # 新增代码+MCPTransport: 写入 session header；若省略: HTTP session 不能延续
        return headers  # 新增代码+MCPTransport: 返回完整请求头；若省略: POST 方法无法发送 header

    def _parse_http_response_message(self, body: str, content_type: str, request_id: int, method: str) -> dict[str, Any]:  # 新增代码+MCPTransport: 解析 Streamable HTTP 的 JSON 或 SSE 响应；若省略: HTTP client 只能处理一种响应类型
        if not body.strip():  # 新增代码+MCPTransport: 检查响应体是否为空；若省略: json.loads 空字符串会产生不友好的错误
            raise RuntimeError(f"MCP HTTP server {self.config.name} 请求 {method} 返回空响应。")  # 新增代码+MCPTransport: 抛出可读空响应错误；若省略: 用户不知道远程 server 没有返回 JSON-RPC
        if "text/event-stream" in content_type or any(line.startswith("data:") for line in body.splitlines()):  # 新增代码+MCPTransport: 识别 SSE 响应；若省略: 流式响应会被当普通 JSON 解析失败
            return self._parse_sse_response_message(body, request_id, method)  # 新增代码+MCPTransport: 转交 SSE 数据行解析；若省略: SSE 兼容路径无法复用
        parsed = json.loads(body)  # 新增代码+MCPTransport: 解析普通 JSON-RPC 响应；若省略: 无法读取 result/error
        if not isinstance(parsed, dict):  # 新增代码+MCPTransport: 确认响应是 JSON 对象；若省略: 数组或字符串会让后续 .get 崩溃
            raise RuntimeError(f"MCP HTTP server {self.config.name} 请求 {method} 返回非对象 JSON。")  # 新增代码+MCPTransport: 抛出可读格式错误；若省略: 调试非标准 server 更困难
        if parsed.get("id") != request_id:  # 新增代码+MCPTransport: 检查响应 id 是否匹配；若省略: 错配响应可能被误用
            raise RuntimeError(f"MCP HTTP server {self.config.name} 请求 {method} 响应 id 不匹配。")  # 新增代码+MCPTransport: 抛出响应关联错误；若省略: 多请求场景难以排查
        return parsed  # 新增代码+MCPTransport: 返回已验证 JSON-RPC 响应；若省略: 调用方拿不到解析结果

    def _parse_sse_events(self, body: str) -> list[McpHttpStreamEvent]:  # 新增代码+MCPStream: 把 SSE 文本解析成结构化事件列表；若省略: POST 和未来 GET 流只能重复手写解析逻辑
        self._stream_state.last_opened_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+MCPStream: 记录最近一次解析流响应的时间；若省略: 用户无法判断流状态是不是刚更新
        normalized_body = body.replace("\r\n", "\n").replace("\r", "\n")  # 新增代码+MCPStream: 统一 Windows、旧 Mac 和 Unix 换行；若省略: 空行分隔在不同服务端换行下会失效
        raw_blocks = normalized_body.split("\n\n")  # 新增代码+MCPStream: 按 SSE 空行规则切分事件；若省略: 多个事件会粘在一起无法逐条更新状态
        events: list[McpHttpStreamEvent] = []  # 新增代码+MCPStream: 准备保存解析后的事件；若省略: 调用方拿不到结构化解析结果
        for raw_block in raw_blocks:  # 新增代码+MCPStream: 逐个处理 SSE 事件块；若省略: 只能解析第一条或整段原文
            if raw_block == "":  # 新增代码+MCPStream: 跳过纯空块；若省略: 连续空行会制造没有意义的空事件
                continue  # 新增代码+MCPStream: 继续解析后续事件块；若省略: 空块会污染 received_count
            event_id = ""  # 新增代码+MCPStream: 初始化当前事件 id；若省略: 没有 id 的事件会继承上一条 id
            event_type = ""  # 新增代码+MCPStream: 初始化当前事件类型；若省略: 没有 event 字段的消息会继承上一条类型
            retry_ms: int | None = None  # 新增代码+MCPStream: 初始化当前事件 retry 建议；若省略: 没有 retry 的事件会误用旧值
            data_lines: list[str] = []  # 新增代码+MCPStream: 准备收集多行 data 字段；若省略: 多行 JSON 或文本正文会丢行
            has_event_field = False  # 修改代码+MCPStream: 记录事件块是否包含有效 SSE 字段；若省略: 纯注释心跳会被当成空事件
            for line in raw_block.split("\n"):  # 新增代码+MCPStream: 逐行读取当前事件字段；若省略: 无法识别 id、event、retry 和 data
                if line.startswith(":"):  # 新增代码+MCPStream: 识别 SSE 注释行；若省略: 心跳注释可能被当成字段解析
                    continue  # 新增代码+MCPStream: 忽略注释行继续解析；若省略: 注释会干扰事件内容
                field_name, field_value = self._split_sse_field(line)  # 新增代码+MCPStream: 拆分字段名和值；若省略: data: 前缀和正文无法可靠分开
                if field_name == "id":  # 新增代码+MCPStream: 处理 SSE id 字段；若省略: last_event_id 无法更新
                    has_event_field = True  # 修改代码+MCPStream: 标记该块包含有效字段；若省略: id-only 事件可能被错误跳过
                    event_id = field_value  # 新增代码+MCPStream: 保存当前事件游标；若省略: 重连恢复会丢失当前位置
                elif field_name == "event":  # 新增代码+MCPStream: 处理 SSE event 字段；若省略: 自定义事件类型会丢失
                    has_event_field = True  # 修改代码+MCPStream: 标记该块包含有效字段；若省略: event-only 事件可能被错误跳过
                    event_type = field_value  # 新增代码+MCPStream: 保存当前事件类型；若省略: 调用方无法区分 endpoint、message 等事件
                elif field_name == "retry":  # 新增代码+MCPStream: 处理 SSE retry 字段；若省略: 服务端重连建议不会进入状态
                    has_event_field = True  # 修改代码+MCPStream: 标记该块包含有效字段；若省略: retry-only 事件可能被错误跳过
                    retry_ms = self._parse_sse_retry(field_value)  # 新增代码+MCPStream: 把 retry 文本转成毫秒整数；若省略: retry 只能作为难用字符串保存
                elif field_name == "data":  # 新增代码+MCPStream: 处理 SSE data 字段；若省略: JSON-RPC 消息正文会丢失
                    has_event_field = True  # 修改代码+MCPStream: 标记该块包含有效字段；若省略: 空 data 事件会被错误跳过
                    data_lines.append(field_value)  # 新增代码+MCPStream: 追加 data 行并保留多行顺序；若省略: 多行 data 无法按规范合并
            if not has_event_field:  # 修改代码+MCPStream: 跳过只包含注释或未知字段的块；若省略: keepalive 会变成空事件输出
                continue  # 修改代码+MCPStream: 不记录无有效字段的心跳块；若省略: received_count 和 max_events 会被心跳污染
            data_text = "\n".join(data_lines)  # 新增代码+MCPStream: 按 SSE 规范用换行合并多行 data；若省略: 多行消息会拼接错误
            event = McpHttpStreamEvent(event_id=event_id, event_type=event_type, retry_ms=retry_ms, data=data_text, message=self._try_parse_json_rpc_message(data_text), raw=raw_block)  # 新增代码+MCPStream: 构造结构化事件并尝试解析 JSON-RPC；若省略: 状态记录和响应匹配都缺少统一对象
            self._remember_stream_event(event)  # 新增代码+MCPStream: 更新 last_event_id、retry_ms 和最近事件缓存；若省略: registry.stream_state 看不到 POST SSE 结果
            events.append(event)  # 新增代码+MCPStream: 把事件加入返回列表；若省略: 响应解析器无法遍历查找 request_id
        return events  # 新增代码+MCPStream: 返回所有解析到的事件；若省略: 调用方无法继续处理 SSE 消息

    def _split_sse_field(self, line: str) -> tuple[str, str]:  # 新增代码+MCPStream: 拆分一行 SSE 字段名和值；若省略: id/event/retry/data 解析会重复且容易出错
        if ":" not in line:  # 新增代码+MCPStream: 兼容没有冒号的 SSE 字段行；若省略: 非标准但允许的字段会解析失败
            return line, ""  # 新增代码+MCPStream: 没有冒号时值为空字符串；若省略: 调用方无法按统一二元组处理
        field_name, field_value = line.split(":", 1)  # 新增代码+MCPStream: 只按第一个冒号切分；若省略: data JSON 里的冒号会被误切
        if field_value.startswith(" "):  # 新增代码+MCPStream: 识别 SSE 允许的单个前导空格；若省略: data: {...} 会多出一个空格
            field_value = field_value[1:]  # 新增代码+MCPStream: 去掉字段值前的一个规范空格；若省略: JSON data 可能因前导空格以外场景不一致
        return field_name, field_value  # 新增代码+MCPStream: 返回字段名和值；若省略: 解析循环拿不到拆分结果

    def _parse_sse_retry(self, value: str) -> int | None:  # 新增代码+MCPStream: 把 SSE retry 字段解析成毫秒整数；若省略: 重连间隔无法用于后续恢复
        try:  # 新增代码+MCPStream: 捕获非数字 retry；若省略: 单个坏 retry 会让整个 SSE 响应失败
            retry_ms = int(value.strip())  # 新增代码+MCPStream: 去空白后转整数；若省略: " 25 " 这类值无法兼容
        except ValueError:  # 新增代码+MCPStream: 处理 retry 不是整数的情况；若省略: 异常会冒泡中断工具列表解析
            return None  # 新增代码+MCPStream: 非法 retry 视为没有建议；若省略: 客户端无法容忍非标准服务端
        if retry_ms < 0:  # 新增代码+MCPStream: 拒绝负数重连间隔；若省略: 后续等待逻辑可能收到无意义负值
            return None  # 新增代码+MCPStream: 负数 retry 不保存；若省略: 状态里会记录错误重连建议
        return retry_ms  # 新增代码+MCPStream: 返回合法毫秒值；若省略: retry 字段不会进入状态

    def _try_parse_json_rpc_message(self, data: str) -> dict[str, Any] | None:  # 新增代码+MCPStream: 尝试把 data 解析成 JSON-RPC 字典；若省略: 调用方需要重复 json.loads 并处理异常
        if not data.strip():  # 新增代码+MCPStream: 空 data 是合法 SSE 事件；若省略: 空事件会触发 JSON 解析错误
            return None  # 新增代码+MCPStream: 空 data 不产生消息；若省略: 状态更新和消息匹配语义会混在一起
        try:  # 新增代码+MCPStream: 捕获非 JSON data；若省略: 普通文本事件会中断 HTTP 响应解析
            message = json.loads(data)  # 新增代码+MCPStream: 解析 data 中的 JSON 文本；若省略: 无法识别 JSON-RPC response
        except json.JSONDecodeError:  # 新增代码+MCPStream: 处理 data 不是 JSON 的合法情况；若省略: 非 JSON 事件会变成错误
            return None  # 新增代码+MCPStream: 非 JSON data 保留原文但不设置 message；若省略: 调用方无法区分文本和解析失败
        return message if isinstance(message, dict) else None  # 新增代码+MCPStream: 只接受对象消息；若省略: 数组或字符串会让后续 .get 崩溃

    def _remember_stream_event(self, event: McpHttpStreamEvent) -> None:  # 新增代码+MCPStream: 把解析到的事件写入流状态；若省略: 解析成功也不会留下 last_event_id/retry 记录
        if event.event_id:  # 新增代码+MCPStream: 只有事件提供非空 id 时才更新游标；若省略: 无 id 事件可能清空可恢复位置
            self._stream_state.last_event_id = event.event_id  # 新增代码+MCPStream: 保存最新事件 id；若省略: registry.stream_state 无法告诉用户断线从哪里恢复
        if event.retry_ms is not None:  # 新增代码+MCPStream: 只有 retry 合法存在时才更新重连建议；若省略: 空 retry 会覆盖已有建议
            self._stream_state.retry_ms = event.retry_ms  # 新增代码+MCPStream: 保存最新 retry 毫秒值；若省略: 客户端无法尊重服务端节流提示
        self._stream_state.received_count += 1  # 新增代码+MCPStream: 累加已解析事件数量；若省略: 用户无法判断流是否真的收到事件
        self._stream_state.last_error = ""  # 新增代码+MCPStream: 成功解析事件后清空旧错误；若省略: 旧错误会误导当前健康状态
        self._recent_stream_events.append(event)  # 新增代码+MCPStream: 把事件加入最近缓存；若省略: 后续诊断无法看到最近流内容
        self._recent_stream_events = self._recent_stream_events[-20:]  # 新增代码+MCPStream: 最近事件最多保留 20 条；若省略: 长时间运行会无限增长内存
        self._remember_notification(event.message)  # 新增代码+MCPLifecycleV2: 如果 SSE data 是 JSON-RPC notification 就放入待刷新队列；若没有这行代码，HTTP tools/list_changed 会只出现在 recent_events 里而不会驱动刷新

    def stream_state(self) -> dict[str, Any]:  # 新增代码+MCPStream: 返回当前 HTTP 流状态给 registry；若省略: 上层无法读取 last_event_id 和 retry_ms
        return {  # 新增代码+MCPStream: 构造稳定的状态字典；若省略: 调用方会依赖 dataclass 内部结构
            "last_event_id": self._stream_state.last_event_id,  # 新增代码+MCPStream: 暴露最近 SSE id；若省略: 测试和未来重连无法读取游标
            "retry_ms": self._stream_state.retry_ms,  # 新增代码+MCPStream: 暴露最近 retry 建议；若省略: 测试和未来重连无法读取等待时间
            "last_opened_at": self._stream_state.last_opened_at,  # 新增代码+MCPStream: 暴露最近流解析时间；若省略: 用户无法判断状态新旧
            "last_error": self._stream_state.last_error,  # 新增代码+MCPStream: 暴露最近流错误；若省略: doctor 类输出无法解释监听失败原因
            "received_count": self._stream_state.received_count,  # 新增代码+MCPStream: 暴露累计事件数；若省略: 用户无法判断是否收到过事件
            "recent_events": [copy.deepcopy(event.__dict__) for event in self._recent_stream_events],  # 修改代码+MCPStream: 深拷贝最近事件快照避免外部修改污染内部缓存；若省略: 调用方改 message 字典会影响 client 内部状态
        }  # 新增代码+MCPStream: 状态字典结束；若省略: Python 语法不完整

    def _parse_sse_response_message(self, body: str, request_id: int, method: str) -> dict[str, Any]:  # 修改代码+MCPStream: 从结构化 SSE 事件里找匹配请求的 JSON-RPC 响应；若省略: text/event-stream 响应无法记录流状态
        candidate: dict[str, Any] | None = None  # 修改代码+MCPStream: 保存最后一个可用 JSON-RPC 响应候选；若省略: 没有 id 匹配时无法保留兼容兜底
        for event in self._parse_sse_events(body):  # 修改代码+MCPStream: 遍历结构化事件并顺便更新流状态；若省略: POST SSE 的 id/retry 不会被记录
            message = event.message  # 修改代码+MCPStream: 读取事件中已解析的 JSON-RPC 消息；若省略: 需要重复解析 data 且空 data 会更难处理
            if message is None:  # 修改代码+MCPStream: 跳过空 data 或非 JSON data 事件；若省略: notification 前的空事件会导致属性访问错误
                continue  # 修改代码+MCPStream: 继续寻找真正的 JSON-RPC response；若省略: 空事件会中断响应匹配
            if message.get("id") == request_id:  # 修改代码+MCPStream: 优先返回 id 匹配的响应；若省略: 多条 SSE 消息可能错取 notification 或旧响应
                return message  # 修改代码+MCPStream: 返回当前请求的响应；若省略: 调用方拿不到正确 result/error
            if "result" in message or "error" in message:  # 修改代码+MCPStream: 保存可用响应候选；若省略: 缺 id 的兼容 server 无法兜底
                candidate = message  # 修改代码+MCPStream: 更新候选响应；若省略: 最后无法回退到可用响应
        if candidate is not None:  # 修改代码+MCPStream: 如果没有 id 匹配但有候选响应；若省略: 兼容返回会被误判失败
            return candidate  # 修改代码+MCPStream: 返回候选响应；若省略: SSE 兼容性更差
        self._stream_state.last_error = f"请求 {method} 的 SSE 响应缺少 JSON-RPC result"  # 修改代码+MCPStream: 保存最近解析失败原因；若省略: stream_state 无法解释为什么没拿到响应
        raise RuntimeError(f"MCP HTTP server {self.config.name} 请求 {method} 的 SSE 响应缺少 JSON-RPC result。")  # 修改代码+MCPStream: 抛出可读 SSE 解析错误；若省略: 用户不知道流里缺少响应


class McpSseClient:  # 新增代码+MCPTransport: 定义旧 HTTP+SSE transport 的明确边界 client；若省略: 旧协议配置会被错误交给 stdio 或 HTTP client
    def __init__(self, config: McpServerConfig, request_timeout_seconds: float = 5.0) -> None:  # 新增代码+MCPTransport: 保存 SSE 配置和超时参数；若省略: registry 无法实例化 legacy client
        self.config = config  # 新增代码+MCPTransport: 保存 server 配置供错误信息使用；若省略: 报错无法指出哪个 server 配错
        self.request_timeout_seconds = request_timeout_seconds  # 新增代码+MCPTransport: 保存超时参数以保持 client 构造签名一致；若省略: 工厂扩展时参数不兼容

    def start(self) -> None:  # 新增代码+MCPTransport: 启动旧 SSE transport 时给出明确未实现边界；若省略: 用户会看到模糊连接失败
        raise RuntimeError(f"MCP server {self.config.name} 使用旧 HTTP+SSE transport，当前最小版暂未实现；请优先改用 transport=http 的 Streamable HTTP endpoint。")  # 新增代码+MCPTransport: 抛出带替代方案的错误；若省略: 用户不知道下一步应改成 http

    def close(self) -> None:  # 新增代码+MCPTransport: 提供 close 兼容 registry 清理流程；若省略: registry.close 会因缺少方法失败
        return None  # 新增代码+MCPTransport: SSE 未启动任何资源所以无需清理；若省略: close 语义不完整


class McpToolRegistry:  # 新增代码+MCP 工具注册表: 统一管理多个 MCP client 暴露的工具；若省略: 项目无法把 MCP tools/list 转成模型可用工具列表
    AUTHENTICATE_TOOL_NAME = "__authenticate__"  # 新增代码+MCPAuthMetadata: 标记 registry 内部的鉴权伪工具路由名；若省略: call_tool 无法区分真实 MCP 工具和本地登录说明工具

    def __init__(self, clients: dict[str, Any] | None = None) -> None:  # 新增代码+MCP 工具注册表: 接收 server 名到 client 的映射；若省略: 测试和运行时无法注入 MCP client
        self._clients = clients or {}  # 新增代码+MCP 工具注册表: 保存 client 映射并允许空配置；若省略: 空 MCP 配置会导致初始化失败
        self._tool_schemas: list[dict[str, Any]] = []  # 新增代码+MCP 工具注册表: 缓存转换后的 OpenAI-compatible schema；若省略: 模型层无法读取工具定义
        self._tool_routes: dict[str, tuple[Any, str]] = {}  # 新增代码+MCP 工具注册表: 记录前缀工具名到 client 和原始工具名的路由；若省略: call_tool 无法剥离前缀并转发
        self._tool_server_names: dict[str, str] = {}  # 新增代码+ToolArchitectureV2: 记录前缀工具名来自哪个 MCP server；若没有这行代码，AgentTool 目录无法保留 server_name
        self._tool_annotations: dict[str, dict[str, Any]] = {}  # 新增代码+ToolPolicyV2: 记录每个 MCP 工具的原始 annotations；若没有这行代码，agent_tools 无法把 readOnlyHint 等标记映射进 AgentTool
        self._tool_meta: dict[str, dict[str, Any]] = {}  # 新增代码+ToolPolicyV2: 记录每个 MCP 工具的原始 _meta；若没有这行代码，searchHint 和 alwaysLoad 等扩展字段会丢失
        self._tool_input_json_schemas: dict[str, dict[str, Any]] = {}  # 新增代码+ToolPolicyV2: 记录每个 MCP 工具原始 inputSchema 的深拷贝；若没有这行代码，AgentTool 无法保留 MCP 原始输入 schema
        self._tool_output_schemas: dict[str, dict[str, Any]] = {}  # 新增代码+ToolPolicyV2: 记录每个 MCP 工具原始 outputSchema 的深拷贝；若没有这行代码，AgentTool 无法保留 MCP 输出结构
        self._tool_strict_flags: dict[str, bool] = {}  # 新增代码+ToolPolicyV2: 记录每个 MCP 工具合理 strict 标记；若没有这行代码，strict 只能永远使用默认 False
        self._tool_parameter_schemas: dict[str, dict[str, Any]] = {}  # 新增代码+MCP参数清洗: 缓存每个前缀工具的参数 schema；若省略: 执行前无法按工具声明过滤串味参数
        self._auth_challenges: dict[str, McpAuthChallenge] = {}  # 新增代码+MCPAuthMetadata: 保存需要鉴权的 server 挑战信息；若省略: doctor 无法报告哪些 server 只暴露 authenticate 工具
        self._start_errors: dict[str, str] = {}  # 新增代码+MCP启动隔离: 记录每个启动失败 server 的错误文本；若省略: LearningAgent 无法区分部分失败和全部失败
        self._started_servers: set[str] = set()  # 新增代码+MCP启动隔离: 记录本轮已经成功 start 且 list_tools 成功的 server；若省略: 上层不知道是否仍有可用 MCP server
        self._lifecycle_events: list[dict[str, Any]] = []  # 新增代码+MCPLifecycleV2: 保存最近处理过的 MCP list_changed 生命周期事件；若没有这行代码，doctor/测试无法审计 server 何时触发刷新
        self._mcp_skill_refresh_version = 0  # 新增代码+MCPLifecycleV2: 记录 prompts/resources 变化导致的 MCP skills/search 索引刷新版本；若没有这行代码，后续技能搜索层没有失效挂点

    @classmethod  # 新增代码+MCP 工具注册表: 提供从配置对象创建注册表的类方法；若省略: 调用方需要重复把配置转成 McpStdioClient
    def from_configs(cls, configs: list[McpServerConfig]) -> "McpToolRegistry":  # 新增代码+MCP 工具注册表: 从 MCP server 配置列表构造注册表；若省略: 配置加载结果无法直接变成可用注册表
        clients: dict[str, Any] = {}  # 新增代码+MCP 工具注册表: 准备保存由配置创建的 client；若省略: 无处累积多个 server 的客户端
        for config in configs:  # 新增代码+MCP 工具注册表: 遍历每个 MCP server 配置；若省略: 只能支持零个配置
            request_timeout_seconds = cls._request_timeout_seconds_for_config(config)  # 新增代码+浏览器超时: 按 server 类型选择外层请求超时；若省略: browser_automation 会继续沿用 5 秒导致页面未超时而外层先失败
            if config.transport == "http":  # 新增代码+MCPTransport: HTTP 配置使用 Streamable HTTP client；若省略: 远程 MCP server 会被错误当作本地命令启动
                clients[config.name] = McpHttpClient(config, request_timeout_seconds=request_timeout_seconds)  # 修改代码+浏览器超时: 创建 HTTP client 并传入统一超时；若省略: 工厂策略无法覆盖不同 transport
            elif config.transport == "sse":  # 新增代码+MCPTransport: SSE 配置使用明确边界 client；若省略: legacy 配置会给出误导性 stdio/HTTP 错误
                clients[config.name] = McpSseClient(config, request_timeout_seconds=request_timeout_seconds)  # 修改代码+浏览器超时: 创建 SSE 边界 client 并保留超时策略；若省略: 工厂行为不一致
            else:  # 新增代码+MCPTransport: 默认保留 stdio client；若省略: 旧配置无法继续工作
                clients[config.name] = McpStdioClient(config, request_timeout_seconds=request_timeout_seconds)  # 修改代码+浏览器超时: 为 stdio 配置创建本地 client 并传入 server 专属超时；若省略: browser_open 的 10000/30000ms 页面等待会被 5 秒外层截断
        return cls(clients)  # 新增代码+MCP 工具注册表: 返回带 client 映射的注册表；若省略: 调用方拿不到构造结果

    @staticmethod  # 新增代码+浏览器超时: 超时策略只依赖配置，不需要 registry 实例状态；若省略: from_configs 会混入硬编码判断
    def _request_timeout_seconds_for_config(config: McpServerConfig) -> float:  # 新增代码+浏览器超时: 为不同 MCP server 选择外层请求等待时间；若省略: 慢页面场景无法和普通工具区分
        return McpStdioClient._default_request_timeout_seconds(config)  # 修改代码+浏览器超时: 复用 stdio client 默认超时策略；若省略: registry 和直接构造的 browser_automation 超时可能再次不一致

    def has_servers(self) -> bool:  # 新增代码+MCP 工具注册表: 判断当前是否配置了任何 MCP server；若省略: 上层无法快速跳过空 MCP 流程
        return bool(self._clients)  # 新增代码+MCP 工具注册表: 用 client 映射是否为空作为判断依据；若省略: 空配置状态无法表达

    def server_names(self) -> list[str]:  # 新增代码+MCP 工具注册表: 返回当前注册的 server 名称列表；若省略: 调试和展示无法知道有哪些 MCP server
        return list(self._clients.keys())  # 新增代码+MCP 工具注册表: 保留插入顺序返回名称；若省略: 调用方无法枚举 server

    def start(self) -> None:  # 新增代码+MCP 工具注册表: 启动所有 client 并读取 tools/list；若省略: tool_schemas 没有 MCP 工具可提供给模型
        self._tool_schemas = []  # 新增代码+MCP 工具注册表: 每次启动前清空旧 schema；若省略: 重复 start 会累积重复工具
        self._tool_routes = {}  # 新增代码+MCP 工具注册表: 每次启动前清空旧路由；若省略: 旧工具可能错误指向已过期 client
        self._tool_server_names = {}  # 新增代码+ToolArchitectureV2: 每次启动前清空旧工具到 server 的映射；若没有这行代码，上一轮 MCP server_name 可能污染新 catalog
        self._tool_annotations = {}  # 新增代码+ToolPolicyV2: 每次启动前清空旧 annotations；若没有这行代码，上一轮 MCP 工具标记可能污染新工具
        self._tool_meta = {}  # 新增代码+ToolPolicyV2: 每次启动前清空旧 _meta；若没有这行代码，旧 searchHint 或 alwaysLoad 可能错误套到新工具
        self._tool_input_json_schemas = {}  # 新增代码+ToolPolicyV2: 每次启动前清空旧原始 inputSchema；若没有这行代码，旧输入结构可能污染新 catalog
        self._tool_output_schemas = {}  # 新增代码+ToolPolicyV2: 每次启动前清空旧 outputSchema；若没有这行代码，旧输出结构可能污染新 catalog
        self._tool_strict_flags = {}  # 新增代码+ToolPolicyV2: 每次启动前清空旧 strict 标记；若没有这行代码，旧严格模式可能错误影响新工具
        self._tool_parameter_schemas = {}  # 新增代码+MCP参数清洗: 每次启动前清空旧参数 schema；若省略: 旧工具参数规则可能污染新 server
        self._auth_challenges = {}  # 新增代码+MCPAuthMetadata: 每次启动前清空旧鉴权挑战；若省略: 上一轮 401 状态可能污染本轮成功连接
        self._start_errors = {}  # 新增代码+MCP启动隔离: 每次启动前清空旧失败记录；若省略: 上一轮坏 server 会污染本轮状态判断
        self._started_servers = set()  # 新增代码+MCP启动隔离: 每次启动前清空成功 server 集合；若省略: 已关闭或失败 server 可能仍被当成可用
        used_tool_names: set[str] = set()  # 新增代码+MCP 工具注册表健壮性: 记录本次启动已分配的前缀工具名；若省略: sanitize 后同名工具会互相覆盖路由
        for server_name, client in self._clients.items():  # 新增代码+MCP 工具注册表: 逐个处理 server 和对应 client；若省略: 多 server 无法被发现
            try:  # 修改代码+MCPAuthMetadata: 捕获 HTTP 401 鉴权挑战并继续处理其他 server；若省略: 一个需要登录的远程 server 会阻断全部 MCP 工具
                client.start()  # 新增代码+MCP 工具注册表: 启动当前 MCP client；若省略: list_tools 可能在未连接状态失败
                tools = client.list_tools()  # 修改代码+MCP启动隔离: 把 tools/list 放进单 server 容错区；若省略: 单个 server 列工具失败会拖垮全部 MCP
            except McpAuthenticationRequired as error:  # 新增代码+MCPAuthMetadata: 单独处理需要鉴权的 HTTP MCP server；若省略: auth-required 会被当作普通失败抛出
                self._auth_challenges[server_name] = error.challenge  # 新增代码+MCPAuthMetadata: 保存挑战供 doctor 和测试读取；若省略: 无法解释哪个 server 需要登录
                self._register_authenticate_tool(server_name, client, error.challenge, used_tool_names)  # 新增代码+MCPAuthMetadata: 为该 server 暴露 mcp__server__authenticate 伪工具；若省略: 模型没有恢复/解释入口
                continue  # 新增代码+MCPAuthMetadata: 跳过该 server 的 tools/list 并继续启动其他 server；若省略: 未初始化 client 会继续 list_tools 导致二次错误
            except Exception as error:  # 新增代码+MCP启动隔离: 捕获单个 server 的普通启动或列工具失败；若省略: Playwright/Chromium 故障会禁用 browser_search 和 workspace_tools
                self._start_errors[server_name] = str(error)  # 新增代码+MCP启动隔离: 保存失败 server 的可读原因；若省略: 用户无法定位哪个 server 坏了
                try:  # 新增代码+MCP启动隔离: 尝试关闭失败 client 释放子进程或连接；若省略: 启动到一半的坏 server 可能残留
                    client.close()  # 新增代码+MCP启动隔离: 只关闭当前失败 client；若省略: 坏 server 的资源不会被清理
                except Exception:  # 新增代码+MCP启动隔离: 忽略失败 client 清理异常继续启动其他 server；若省略: close 失败仍会拖垮后续 server
                    pass  # 新增代码+MCP启动隔离: 保持单 server 清理容错分支语法完整；若省略: except 分支无法成立
                continue  # 新增代码+MCP启动隔离: 跳过失败 server 并继续处理其他 server；若省略: 一个坏 server 仍会中断整个启动流程
            for tool in tools:  # 新增代码+MCP 工具注册表: 遍历 MCP 返回的每个工具；若省略: 工具列表不会被转换
                if not isinstance(tool, dict):  # 新增代码+MCP 工具注册表: 跳过非对象工具项；若省略: 异常 server 返回会让注册表崩溃
                    continue  # 新增代码+MCP 工具注册表: 保持单个坏工具不影响其他工具；若省略: 容错路径无法继续
                raw_tool_name = str(tool.get("name", "")).strip()  # 新增代码+MCP 工具注册表: 读取并清理 MCP 原始工具名；若省略: 前缀名可能包含空白或为空
                if not raw_tool_name:  # 新增代码+MCP 工具注册表: 跳过缺少名称的工具；若省略: 无名工具会生成不可调用 schema
                    continue  # 新增代码+MCP 工具注册表: 忽略坏工具并继续处理后续工具；若省略: 一个坏项会阻断整个 server
                base_prefixed_name = self._prefix_tool_name(server_name, raw_tool_name)  # 修改代码+MCP 工具注册表健壮性: 先生成未去重的 mcp__server__tool 名称；若省略: 后续无法基于标准名称处理冲突
                prefixed_name = self._unique_tool_name(base_prefixed_name, used_tool_names)  # 新增代码+MCP 工具注册表健壮性: 为 sanitize 后冲突的工具生成唯一名称；若省略: 第二个同名工具会覆盖第一个路由
                used_tool_names.add(prefixed_name)  # 新增代码+MCP 工具注册表健壮性: 标记名称已被占用；若省略: 后续工具仍可能分配重复名称
                input_schema = tool.get("inputSchema", {})  # 新增代码+MCP 工具注册表: 读取 MCP inputSchema；若省略: 参数 schema 会丢失
                parameters = copy.deepcopy(input_schema) if isinstance(input_schema, dict) else {"type": "object"}  # 修改代码+MCP 工具注册表健壮性: 深拷贝 MCP inputSchema 或兜底 object；若省略: 原始 schema 后续变化会污染注册表缓存
                output_schema = tool.get("outputSchema", {})  # 新增代码+ToolPolicyV2: 读取 MCP outputSchema；若没有这行代码，返回值结构无法保存进 AgentTool
                annotations = tool.get("annotations", {})  # 新增代码+ToolPolicyV2: 读取 MCP annotations；若没有这行代码，readOnlyHint/destructiveHint/openWorldHint 无法映射
                meta = tool.get("_meta", {})  # 新增代码+ToolPolicyV2: 读取 MCP _meta；若没有这行代码，anthropic/searchHint 和 anthropic/alwaysLoad 无法映射
                safe_output_schema = copy.deepcopy(output_schema) if isinstance(output_schema, dict) else {}  # 新增代码+ToolPolicyV2: 只保存合法字典 outputSchema；若没有这行代码，坏 MCP 输出结构可能污染 AgentTool
                safe_annotations = copy.deepcopy(annotations) if isinstance(annotations, dict) else {}  # 新增代码+ToolPolicyV2: 只保存合法字典 annotations；若没有这行代码，异常 annotations 会让 agent_tools 读取时报错
                safe_meta = copy.deepcopy(meta) if isinstance(meta, dict) else {}  # 新增代码+ToolPolicyV2: 只保存合法字典 _meta；若没有这行代码，异常 _meta 会让扩展字段映射崩溃
                strict_raw_value = safe_meta["strict"] if "strict" in safe_meta else safe_meta["anthropic/strict"] if "anthropic/strict" in safe_meta else tool.get("strict", False)  # 修改代码+ToolPolicyV2: 按 strict、anthropic/strict、顶层 strict 的顺序取原始值；若没有这行代码，严格布尔解析无法保持现有优先级
                strict_flag = self._metadata_bool(strict_raw_value)  # 修改代码+ToolPolicyV2: 用严格布尔解析 strict 标记；若没有这行代码，字符串 "false" 会被 bool() 误判为 True
                description = str(tool.get("description", ""))  # 新增代码+MCP 工具注册表: 读取工具说明文本；若省略: 模型缺少判断何时调用工具的提示
                schema = {  # 新增代码+MCP 工具注册表: 构造 OpenAI-compatible tool schema；若省略: 模型 API 无法识别 MCP 工具
                    "type": "function",  # 新增代码+MCP 工具注册表: 声明工具类型为 function；若省略: OpenAI-compatible 工具格式不完整
                    "function": {  # 新增代码+MCP 工具注册表: 放置 function 具体定义；若省略: name/description/parameters 没有标准位置
                        "name": prefixed_name,  # 新增代码+MCP 工具注册表: 使用带 server 前缀的工具名；若省略: 多 server 同名工具会冲突
                        "description": description,  # 新增代码+MCP 工具注册表: 透传 MCP 工具说明；若省略: 模型选择工具时信息不足
                        "parameters": parameters,  # 新增代码+MCP 工具注册表: 透传 MCP inputSchema 作为参数 schema；若省略: required 等约束会丢失
                    },  # 新增代码+MCP 工具注册表: function 定义结束；若省略: schema 字典语法不完整
                }  # 新增代码+MCP 工具注册表: tool schema 构造结束；若省略: 无法追加到 schema 列表
                self._tool_schemas.append(schema)  # 新增代码+MCP 工具注册表: 保存转换后的 schema；若省略: tool_schemas 返回空列表
                self._tool_routes[prefixed_name] = (client, raw_tool_name)  # 新增代码+MCP 工具注册表: 保存调用路由；若省略: call_tool 找不到对应原始工具
                self._tool_server_names[prefixed_name] = server_name  # 新增代码+ToolArchitectureV2: 保存该 MCP 工具的 server_name 元数据；若没有这行代码，agent_tools 无法告诉 catalog 工具来自 weather 还是其他 server
                self._tool_annotations[prefixed_name] = safe_annotations  # 新增代码+ToolPolicyV2: 缓存该 MCP 工具 annotations；若没有这行代码，agent_tools 无法还原只读、破坏性和开放世界标记
                self._tool_meta[prefixed_name] = safe_meta  # 新增代码+ToolPolicyV2: 缓存该 MCP 工具 _meta；若没有这行代码，agent_tools 无法还原 searchHint 和 alwaysLoad
                self._tool_input_json_schemas[prefixed_name] = copy.deepcopy(parameters)  # 新增代码+ToolPolicyV2: 缓存原始 inputSchema 深拷贝；若没有这行代码，AgentTool.input_json_schema 会丢失 MCP 原始输入结构
                self._tool_output_schemas[prefixed_name] = safe_output_schema  # 新增代码+ToolPolicyV2: 缓存 outputSchema 深拷贝；若没有这行代码，AgentTool.output_schema 只能是空字典
                self._tool_strict_flags[prefixed_name] = strict_flag  # 新增代码+ToolPolicyV2: 缓存 strict 标记；若没有这行代码，agent_tools 无法把 strict 传给 AgentTool
                self._tool_parameter_schemas[prefixed_name] = copy.deepcopy(parameters)  # 新增代码+MCP参数清洗: 保存该工具自己的参数 schema；若省略: call_tool 无法清除其他工具混进来的字段
            self._started_servers.add(server_name)  # 新增代码+MCP启动隔离: 标记当前 server 已经成功启动并完成工具发现；若省略: 上层会把可用 server 误判为全部失败

    def _register_authenticate_tool(self, server_name: str, client: Any, challenge: McpAuthChallenge, used_tool_names: set[str]) -> None:  # 新增代码+MCPAuthMetadata: 注册单个鉴权伪工具；若省略: 401 server 无法在模型工具列表中留下恢复入口
        base_prefixed_name = self._prefix_tool_name(server_name, "authenticate")  # 新增代码+MCPAuthMetadata: 生成 mcp__server__authenticate 基础名；若省略: 工具命名会和真实 MCP 前缀规则不一致
        prefixed_name = self._unique_tool_name(base_prefixed_name, used_tool_names)  # 新增代码+MCPAuthMetadata: 避免和真实工具或其他 server 冲突；若省略: 同名 authenticate 可能覆盖路由
        used_tool_names.add(prefixed_name)  # 新增代码+MCPAuthMetadata: 标记该工具名已占用；若省略: 后续工具仍可能拿到同一名称
        metadata_hint = challenge.resource_metadata_url or "未提供 resource_metadata"  # 新增代码+MCPAuthMetadata: 生成工具描述里的 metadata 提示；若省略: 模型看 schema 时缺少登录线索
        schema = {  # 新增代码+MCPAuthMetadata: 构造 OpenAI-compatible authenticate 工具 schema；若省略: 模型无法看到鉴权入口
            "type": "function",  # 新增代码+MCPAuthMetadata: 声明工具类型为 function；若省略: OpenAI-compatible 工具格式不完整
            "function": {  # 新增代码+MCPAuthMetadata: 放置 function 工具定义；若省略: name/description/parameters 没有标准位置
                "name": prefixed_name,  # 新增代码+MCPAuthMetadata: 使用 mcp__server__authenticate 工具名；若省略: 模型无法调用该伪工具
                "description": f"MCP server `{server_name}` 返回 401，需要鉴权；调用后会说明 WWW-Authenticate/resource_metadata 与 Authorization: Bearer 配置方式，不会自动登录。metadata={metadata_hint}",  # 新增代码+MCPAuthMetadata: 告诉模型这是解释型登录入口；若省略: 模型可能误以为这是完整 OAuth 执行工具
                "parameters": {  # 新增代码+MCPAuthMetadata: 定义伪工具参数 schema；若省略: 模型可能传入 token 等敏感字段
                    "type": "object",  # 新增代码+MCPAuthMetadata: 参数必须是对象；若省略: function schema 不完整
                    "properties": {  # 新增代码+MCPAuthMetadata: 列出允许字段；若省略: additionalProperties 无上下文
                        "note": {"type": "string", "description": "可选备注；不要在这里填写 access token。"},  # 新增代码+MCPAuthMetadata: 允许非敏感备注并提醒不要传 token；若省略: 模型可能把令牌写进工具参数和日志
                    },  # 新增代码+MCPAuthMetadata: properties 定义结束；若省略: Python 字典语法不完整
                    "additionalProperties": False,  # 新增代码+MCPAuthMetadata: 禁止未声明参数；若省略: 模型可能传入 credential/token 等敏感字段
                },  # 新增代码+MCPAuthMetadata: parameters 定义结束；若省略: schema 不完整
            },  # 新增代码+MCPAuthMetadata: function 定义结束；若省略: schema 字典不完整
        }  # 新增代码+MCPAuthMetadata: authenticate schema 构造结束；若省略: 无法追加工具
        self._tool_schemas.append(schema)  # 新增代码+MCPAuthMetadata: 保存 authenticate 工具 schema；若省略: 模型可见工具列表不会包含它
        self._tool_routes[prefixed_name] = (client, self.AUTHENTICATE_TOOL_NAME)  # 新增代码+MCPAuthMetadata: 把伪工具路由到 client.authenticate；若省略: 工具可见但无法调用
        self._tool_server_names[prefixed_name] = server_name  # 新增代码+ToolArchitectureV2: 保存 authenticate 伪工具所属 server；若没有这行代码，鉴权目录条目也无法追踪 server_name
        self._tool_annotations[prefixed_name] = {}  # 新增代码+ToolPolicyV2: 给鉴权伪工具保存空 annotations；若没有这行代码，agent_tools 读取元数据时需要额外分支
        self._tool_meta[prefixed_name] = {"anthropic/alwaysLoad": True, "anthropic/searchHint": "mcp authentication oauth login resource metadata"}  # 修改代码+MCPAuthBoundary: 鉴权入口强制首轮可见并加入搜索提示；若没有这行代码，需要登录的 MCP server 会把恢复入口藏进 deferred 工具
        self._tool_input_json_schemas[prefixed_name] = copy.deepcopy(schema["function"]["parameters"])  # 新增代码+ToolPolicyV2: 给鉴权伪工具保存原始输入 schema；若没有这行代码，AgentTool.input_json_schema 会缺少兜底结构
        self._tool_output_schemas[prefixed_name] = {}  # 新增代码+ToolPolicyV2: 给鉴权伪工具保存空 outputSchema；若没有这行代码，AgentTool.output_schema 需要特殊处理 None
        self._tool_strict_flags[prefixed_name] = False  # 新增代码+ToolPolicyV2: 给鉴权伪工具保存默认非 strict；若没有这行代码，strict 读取需要额外兜底
        self._tool_parameter_schemas[prefixed_name] = copy.deepcopy(schema["function"]["parameters"])  # 新增代码+MCP参数清洗: 保存 authenticate 伪工具允许的参数；若省略: 鉴权说明工具也可能收到多余敏感字段

    def tool_schemas(self) -> list[dict[str, Any]]:  # 新增代码+MCP 工具注册表: 返回转换后的模型工具 schema；若省略: 模型层无法获取 MCP 工具定义
        return copy.deepcopy(self._tool_schemas)  # 修改代码+MCP 工具注册表健壮性: 返回深拷贝避免调用方修改嵌套 schema；若省略: 外部修改 properties/required 会污染注册表状态

    @staticmethod  # 新增代码+ToolPolicyV2: 元数据布尔解析不依赖 registry 实例状态；若没有这行代码，调用 helper 时需要无意义的 self 状态
    def _metadata_bool(value: Any) -> bool:  # 新增代码+ToolPolicyV2: 严格解析 MCP annotations/_meta 布尔值；若没有这行代码，字符串 "false"、"0"、"no" 会被 bool() 误判为 True
        return value is True  # 新增代码+ToolPolicyV2: 只有真正的布尔 True 才返回 True；若没有这行代码，非布尔真值会错误开启工具策略标记

    @staticmethod  # 新增代码+RealChromeWorkflow: MCP gate 推断不依赖 registry 实例状态；若没有这行代码，测试复用该规则会需要构造 registry
    def _mcp_tool_skill_gate(server_name: str, original_name: str) -> str:  # 新增代码+RealChromeWorkflow: 按 MCP server 和原始工具名决定 skill gate；若没有这行代码，真实 Chrome 工具无法自动进入 ToolPolicy 门控
        if server_name == "browser_automation" and original_name in {"browser_connect_real_chrome", "browser_disconnect_real_chrome"}:  # 新增代码+RealChromeWorkflow: 真实 Chrome 连接/断开属于高风险 profile 工具；若没有这行代码，连接真实登录态前不会要求 real_chrome skill
            return "real_chrome"  # 新增代码+RealChromeWorkflow: 返回真实 Chrome skill 名；若没有这行代码，ToolPolicyContext.loaded_skills 无法匹配门槛
        return ""  # 新增代码+RealChromeWorkflow: 其他 MCP 工具暂不需要该 skill gate；若没有这行代码，普通工具会被误锁

    @staticmethod  # 新增代码+RealChromeWorkflow: workflow gate 推断不依赖 registry 实例状态；若没有这行代码，规则无法独立测试
    def _mcp_tool_workflow_gate(server_name: str, original_name: str) -> str:  # 新增代码+RealChromeWorkflow: 按 MCP 工具决定 workflow gate；若没有这行代码，真实 Chrome 工具不会强制先执行 profile status
        if server_name == "browser_automation" and original_name in {"browser_connect_real_chrome", "browser_disconnect_real_chrome"}:  # 新增代码+RealChromeWorkflow: 连接/断开真实 Chrome 前必须先完成 profile 状态检查；若没有这行代码，用户仍可能直接授权高风险连接
            return "real_chrome_profile_ready"  # 新增代码+RealChromeWorkflow: 返回 profile ready workflow 名；若没有这行代码，ToolPolicyContext.completed_workflows 无法匹配门槛
        return ""  # 新增代码+RealChromeWorkflow: 其他 MCP 工具暂不需要该 workflow gate；若没有这行代码，普通工具会被误锁

    @staticmethod  # 新增代码+RealChromeWorkflow: always-load 推断不依赖 registry 实例状态；若没有这行代码，前置工具可见性规则难以复用
    def _mcp_tool_force_always_load(server_name: str, original_name: str) -> bool:  # 新增代码+RealChromeWorkflow: 判断某些 MCP 工具是否必须首轮可见；若没有这行代码，profile status/auth 前置入口仍可能藏在 deferred 工具里
        if original_name == McpToolRegistry.AUTHENTICATE_TOOL_NAME:  # 新增代码+MCPAuthBoundary: authenticate 是恢复登录的入口；若没有这行代码，需要鉴权的 server 会把恢复入口隐藏起来
            return True  # 新增代码+MCPAuthBoundary: 鉴权伪工具强制可见；若没有这行代码，用户不知道该如何处理 401
        if server_name == "browser_automation" and original_name == "browser_profile_status":  # 新增代码+RealChromeWorkflow: profile status 是真实 Chrome workflow 的前置只读检查；若没有这行代码，模型可能先搜到 browser_open 而不是状态入口
            return True  # 新增代码+RealChromeWorkflow: 强制首轮可见 profile status；若没有这行代码，真实浏览器请求仍容易走错入口
        return False  # 新增代码+RealChromeWorkflow: 其他 MCP 工具保留默认 deferred；若没有这行代码，大量外部工具会重新挤进首轮上下文

    @staticmethod  # 新增代码+CapabilityPacks: MCP 能力包推断不依赖 registry 实例状态；若没有这行代码，MCP 工具分包规则无法复用和测试
    def _mcp_tool_capability_pack(server_name: str, original_name: str) -> str:  # 新增代码+CapabilityPacks: 根据 MCP server 和原始工具名推断能力包；若没有这行代码，外部工具无法参与 select_pack
        if server_name == "computer-use":  # 新增代码+ComputerUseMCP：把独立 computer-use MCP server 归入桌面能力包；如果没有这一行，/computer use --full 只会加载旧内置兼容工具而找不到 mcp__computer-use__ 原子工具。
            return "computer_use"  # 新增代码+ComputerUseMCP：返回现有 Computer Use 能力包名；如果没有这一行，tool_search select_pack:computer_use 无法批量启用新 MCP 工具。
        if server_name == "browser_automation" and "real_chrome" in original_name:  # 新增代码+CapabilityPacks: 真实 Chrome 工具归入专门高风险能力包；若没有这行代码，真实登录态流程会和普通浏览器混在一起
            return "real_chrome"  # 新增代码+CapabilityPacks: 返回真实 Chrome 能力包名；若没有这行代码，模型无法按真实浏览器需求加载正确工具组
        if server_name == "browser_automation":  # 新增代码+CapabilityPacks: 普通浏览器自动化工具归入浏览器能力包；若没有这行代码，browser_open/click 等工具缺少批量加载入口
            return "browser_automation"  # 新增代码+CapabilityPacks: 返回浏览器自动化能力包名；若没有这行代码，普通浏览器工具只能逐个 select
        if original_name == McpToolRegistry.AUTHENTICATE_TOOL_NAME:  # 新增代码+CapabilityPacks: 鉴权伪工具归入 MCP 能力包；若没有这行代码，认证恢复入口的分组不清楚
            return "mcp"  # 新增代码+CapabilityPacks: 返回 MCP 能力包名；若没有这行代码，auth 工具不会随 MCP 说明一起出现
        return "mcp"  # 新增代码+CapabilityPacks: 其他 MCP 工具默认归入 MCP 包；若没有这行代码，外部工具可能没有任何能力包元数据

    def agent_tools(self) -> list[AgentTool]:  # 新增代码+ToolArchitectureV2: 把已缓存的 MCP schema 包装成 AgentTool 目录条目；若没有这行代码，MCP 工具无法进入 v2 catalog
        catalog: list[AgentTool] = []  # 新增代码+ToolArchitectureV2: 准备累积 MCP AgentTool 条目；若没有这行代码，函数没有地方保存包装结果
        for schema in self._tool_schemas:  # 新增代码+ToolArchitectureV2: 遍历 start 已经发现并缓存的 MCP 工具 schema；若没有这行代码，catalog 会一直为空
            function_schema = schema.get("function", {}) if isinstance(schema, dict) else {}  # 新增代码+ToolArchitectureV2: 安全读取 function 定义；若没有这行代码，异常 schema 可能在目录包装时崩溃
            if not isinstance(function_schema, dict):  # 新增代码+ToolArchitectureV2: 防御 function 不是字典的坏 schema；若没有这行代码，后续读取 name 会触发错误
                continue  # 新增代码+ToolArchitectureV2: 跳过坏 schema 并保留其他工具；若没有这行代码，一个坏 MCP 工具会阻断整个 catalog
            tool_name = str(function_schema.get("name", "")).strip()  # 新增代码+ToolArchitectureV2: 读取前缀后的工具名；若没有这行代码，无法从路由元数据查回 original_name
            if not tool_name:  # 新增代码+ToolArchitectureV2: 跳过没有名称的坏 schema；若没有这行代码，目录会出现不可调用的空名工具
                continue  # 新增代码+ToolArchitectureV2: 忽略空名工具继续处理后续项；若没有这行代码，空名会污染 catalog
            route = self._tool_routes.get(tool_name)  # 新增代码+ToolArchitectureV2: 从路由表读取 client 和 MCP 原始工具名；若没有这行代码，AgentTool 无法保留 original_name
            original_name = route[1] if route is not None else tool_name  # 新增代码+ToolArchitectureV2: 优先使用路由里的原始名并兜底为当前名；若没有这行代码，元数据缺失时会直接报错
            if is_provider_specific_tool_name(original_name):  # 新增代码+BrowserToolSurfaceStage3: provider 专属重复动作不进入模型 catalog；若没有这行代码，模型会重新面对插件/CDP/Chromium 多轨选择。
                continue  # 新增代码+BrowserToolSurfaceStage3: 过滤内部 provider 工具并保留统一 browser_* 动作；若没有这行代码，错误工具仍会暴露给模型。
            annotations = self._tool_annotations.get(tool_name, {})  # 新增代码+ToolPolicyV2: 读取当前 MCP 工具 annotations；若没有这行代码，readOnlyHint/destructiveHint/openWorldHint 无法进入 AgentTool
            meta = self._tool_meta.get(tool_name, {})  # 新增代码+ToolPolicyV2: 读取当前 MCP 工具 _meta；若没有这行代码，searchHint 和 alwaysLoad 无法进入 AgentTool
            always_load_meta = meta.get("anthropic/alwaysLoad", meta.get("alwaysLoad", False))  # 新增代码+ToolPolicyV2: 同时兼容 anthropic/alwaysLoad 和普通 alwaysLoad；若没有这行代码，兼容 MCP server 的强制加载声明会被忽略
            search_hint_meta = meta.get("anthropic/searchHint", meta.get("searchHint", ""))  # 新增代码+ToolPolicyV2: 同时兼容 anthropic/searchHint 和普通 searchHint；若没有这行代码，部分 MCP server 提供的搜索提示会丢失
            surface_hint = browser_tool_surface_hint(original_name)  # 新增代码+BrowserToolSurfaceStage3: 读取 Stage 3 工具表面提示；若没有这行代码，provider-control 工具不会带 advanced 说明。
            search_hint_parts = [str(search_hint_meta or "").strip(), surface_hint]  # 新增代码+BrowserToolSurfaceStage3: 合并 MCP 原始 searchHint 和工具表面提示；若没有这行代码，两类提示会互相覆盖。
            combined_search_hint = " ".join(part for part in search_hint_parts if part)  # 新增代码+BrowserToolSurfaceStage3: 去掉空提示并拼成稳定字符串；若没有这行代码，search_hint 可能出现多余空格或丢失信息。
            server_name = self._tool_server_names.get(tool_name, "")  # 新增代码+RealChromeWorkflow: 先取出 MCP server 名供 gate 和元数据复用；若没有这行代码，真实 Chrome helper 会重复查映射
            skill_gate = self._mcp_tool_skill_gate(server_name, original_name)  # 新增代码+RealChromeWorkflow: 按 server 和原始工具名决定 skill gate；若没有这行代码，真实 Chrome 连接工具不会被 skill 前置流程保护
            workflow_gate = self._mcp_tool_workflow_gate(server_name, original_name)  # 新增代码+RealChromeWorkflow: 按 server 和原始工具名决定 workflow gate；若没有这行代码，真实 Chrome 工具不会要求先查 profile 状态
            force_always_load = self._mcp_tool_force_always_load(server_name, original_name)  # 新增代码+RealChromeWorkflow: 标记 profile status/auth 等前置工具默认可见；若没有这行代码，模型可能连准备 workflow 的入口都看不到
            capability_pack = self._mcp_tool_capability_pack(server_name, original_name)  # 新增代码+CapabilityPacks: 为 MCP 工具推断能力包；若没有这行代码，select_pack 无法批量加载外部工具
            catalog.append(  # 新增代码+ToolArchitectureV2: 把当前 MCP 工具加入返回目录；若没有这行代码，包装好的 AgentTool 会被丢弃
                agent_tool_from_schema(  # 新增代码+ToolArchitectureV2: 复用 schema 包装函数获得深拷贝保护；若没有这行代码，可变 input_schema 可能污染 registry 缓存
                    schema,  # 新增代码+ToolArchitectureV2: 传入已缓存的 OpenAI-compatible schema；若没有这行代码，包装函数拿不到工具名和参数
                    source="mcp",  # 新增代码+ToolArchitectureV2: 标记工具来自 MCP；若没有这行代码，权限和展示层会把外部工具误判为内置
                    should_defer=True,  # 新增代码+ToolArchitectureV2: 默认延迟加载 MCP 工具；若没有这行代码，大量外部工具可能默认进入首轮上下文
                    always_load=self._metadata_bool(always_load_meta) or force_always_load,  # 修改代码+RealChromeWorkflow: 兼容 MCP alwaysLoad 并强制暴露真实 Chrome 前置状态工具；若没有这行代码，profile status/auth 仍可能被隐藏
                    is_read_only=self._metadata_bool(annotations.get("readOnlyHint", False)),  # 修改代码+ToolPolicyV2: 用严格布尔解析 readOnlyHint；若没有这行代码，字符串 "false" 会错误标成只读
                    is_destructive=self._metadata_bool(annotations.get("destructiveHint", False)),  # 修改代码+ToolPolicyV2: 用严格布尔解析 destructiveHint；若没有这行代码，字符串 "false" 会错误标成破坏性工具
                    skill_gate=skill_gate,  # 新增代码+RealChromeWorkflow: 把真实 Chrome skill gate 写入 AgentTool；若没有这行代码，ToolPolicy 无法在 select 和执行前阻断
                    workflow_gate=workflow_gate,  # 新增代码+RealChromeWorkflow: 把真实 Chrome workflow gate 写入 AgentTool；若没有这行代码，connect 前置状态检查不会被强制执行
                    original_name=original_name,  # 新增代码+ToolArchitectureV2: 保留 MCP 原始工具名；若没有这行代码，审计和调试无法对应外部 server 的真实工具
                    server_name=server_name,  # 修改代码+RealChromeWorkflow: 复用前面读取的 server 名；若没有这行代码，后续 gate 和 catalog 可能来源不一致
                    search_hint=combined_search_hint,  # 修改代码+BrowserToolSurfaceStage3: 把 MCP searchHint 与 provider-control 提示一起保存；若没有这行代码，真实 Chrome 控制工具缺少高级标记。
                    input_json_schema=self._tool_input_json_schemas.get(tool_name, {}),  # 新增代码+ToolPolicyV2: 传入 MCP 原始 inputSchema 深拷贝；若没有这行代码，AgentTool.input_json_schema 会退化为包装 schema
                    output_schema=self._tool_output_schemas.get(tool_name, {}),  # 新增代码+ToolPolicyV2: 传入 MCP outputSchema 深拷贝；若没有这行代码，AgentTool.output_schema 会一直为空
                    is_open_world=self._metadata_bool(annotations.get("openWorldHint", False)),  # 修改代码+ToolPolicyV2: 用严格布尔解析 openWorldHint；若没有这行代码，字符串 "false" 会错误标成开放世界工具
                    strict=self._tool_strict_flags.get(tool_name, False),  # 新增代码+ToolPolicyV2: 传入合理 strict 标记；若没有这行代码，strict 元数据不会随 AgentTool 流转
                    capability_pack=capability_pack,  # 新增代码+CapabilityPacks: 把 MCP 能力包写入 AgentTool；若没有这行代码，外部工具无法通过 select_pack 加入工具池
                )  # 修改代码+ToolPolicyV2: 结束带 MCP annotations/_meta 映射参数的 AgentTool 包装调用；若没有这行代码，Python 调用语法不完整且 MCP 元数据无法完整传入
            )  # 新增代码+ToolArchitectureV2: 结束目录追加调用；若没有这行代码，catalog.append 语法不完整
        return catalog  # 新增代码+ToolArchitectureV2: 返回 MCP AgentTool 列表；若没有这行代码，调用方拿不到任何 catalog 条目

    def auth_challenges(self) -> dict[str, McpAuthChallenge]:  # 新增代码+MCPAuthMetadata: 返回当前需要鉴权的 server 挑战表；若省略: doctor 无法展示 auth-required 状态
        return dict(self._auth_challenges)  # 新增代码+MCPAuthMetadata: 返回浅拷贝避免外部替换内部字典；若省略: 调用方可能污染 registry 状态

    def start_errors(self) -> dict[str, str]:  # 新增代码+MCP启动隔离: 返回本轮启动失败的 server 错误表；若省略: LearningAgent 无法生成部分失败提示
        return dict(self._start_errors)  # 新增代码+MCP启动隔离: 返回浅拷贝避免调用方污染内部状态；若省略: 外部代码可能修改 registry 的失败记录

    def has_available_servers(self) -> bool:  # 新增代码+MCP启动隔离: 判断本轮是否还有可用 server 或鉴权伪工具；若省略: 单个 server 失败会被上层误判为全局状态
        return bool(self._started_servers or self._auth_challenges)  # 新增代码+MCP启动隔离: 成功启动或存在 authenticate 入口都算 MCP 可用；若省略: 需要登录的 server 可能无法暴露恢复说明

    def stream_state(self, server_name: str) -> dict[str, Any]:  # 新增代码+MCPStream: 返回指定 MCP server 的 HTTP SSE 流状态；若省略: 测试和 doctor 无法读取 last_event_id/retry_ms
        if server_name not in self._clients:  # 新增代码+MCPStream: 检查 server 名是否存在；若省略: 输错名字会得到模糊 AttributeError 或空结果
            raise RuntimeError(f"未知 MCP server：{server_name}")  # 新增代码+MCPStream: 抛出清晰未知 server 错误；若省略: 用户不知道是 server 名写错
        client = self._clients[server_name]  # 新增代码+MCPStream: 取出对应 client；若省略: 无法调用该 server 的 stream_state 方法
        stream_state = getattr(client, "stream_state", None)  # 新增代码+MCPStream: 读取 client 可选的 stream_state 方法；若省略: stdio client 会因没有该方法而崩溃
        if not callable(stream_state):  # 新增代码+MCPStream: 兼容不支持 HTTP 流状态的 client；若省略: 老 client 或测试假 client 会触发 TypeError
            return {}  # 新增代码+MCPStream: 不支持时返回空字典；若省略: 调用方无法用统一方式读取状态
        return stream_state()  # 新增代码+MCPStream: 返回 client 提供的流状态；若省略: registry.stream_state 没有实际数据

    def refresh_from_notifications(self) -> dict[str, Any]:  # 新增代码+MCPLifecycleV2: 消费 MCP notifications 并按 list_changed 刷新 registry；若没有这行代码，工具目录只能在启动时读取一次
        events = self._drain_lifecycle_notifications()  # 新增代码+MCPLifecycleV2: 从所有 client 拉取待处理 lifecycle notifications；若没有这行代码，registry 不知道哪些 server 发了变化通知
        changed_kinds = sorted({str(event.get("kind", "")) for event in events if event.get("kind")})  # 新增代码+MCPLifecycleV2: 汇总本批 notifications 影响的资源类型；若没有这行代码，后续无法判断是否需要刷新 tools/prompts/resources
        summary: dict[str, Any] = {  # 新增代码+MCPLifecycleV2: 构造给上层和测试读取的刷新摘要；若没有这行代码，LearningAgent 无法判断是否要清 catalog cache
            "event_count": len(events),  # 新增代码+MCPLifecycleV2: 记录本批有效生命周期事件数量；若没有这行代码，调用方无法区分没通知和有通知
            "changed_kinds": changed_kinds,  # 新增代码+MCPLifecycleV2: 暴露 tools/prompts/resources 变化类型；若没有这行代码，测试无法确认方法名映射正确
            "refreshed_tools": False,  # 新增代码+MCPLifecycleV2: 默认尚未刷新工具目录；若没有这行代码，上层可能误以为每次调用都刷新了 catalog
            "refreshed_prompts": "prompts" in changed_kinds,  # 新增代码+MCPLifecycleV2: prompts 目前按即时读取边界记录刷新；若没有这行代码，后续 prompt cache 层没有可对接标志
            "refreshed_resources": "resources" in changed_kinds,  # 新增代码+MCPLifecycleV2: resources 目前按即时读取边界记录刷新；若没有这行代码，后续 resource cache 层没有可对接标志
            "mcp_skill_refresh_version": self._mcp_skill_refresh_version,  # 新增代码+MCPLifecycleV2: 返回刷新前技能索引版本；若没有这行代码，调用方无法观察 prompts/resources 是否让技能索引失效
            "events": copy.deepcopy(events),  # 新增代码+MCPLifecycleV2: 返回事件快照供调试；若没有这行代码，用户无法审计是哪台 server 触发刷新
        }  # 新增代码+MCPLifecycleV2: 刷新摘要字典结束；若没有这行代码，Python 语法不完整
        if not events:  # 新增代码+MCPLifecycleV2: 没有生命周期通知时不做任何刷新；若没有这行代码，每轮工具池计算都会重新 tools/list 造成性能和副作用问题
            return summary  # 新增代码+MCPLifecycleV2: 直接返回空刷新摘要；若没有这行代码，空事件也会进入后续刷新逻辑
        self._lifecycle_events.extend(copy.deepcopy(events))  # 新增代码+MCPLifecycleV2: 把本批事件追加进审计缓存；若没有这行代码，刷新后无法回看最近通知历史
        self._lifecycle_events = self._lifecycle_events[-100:]  # 新增代码+MCPLifecycleV2: 生命周期事件最多保留最近 100 条；若没有这行代码，长期运行可能无限增长内存
        if "tools" in changed_kinds:  # 新增代码+MCPLifecycleV2: tools/list_changed 必须重新拉 tools/list；若没有这行代码，外部 server 新增或删除工具后 ToolSearch 仍看到旧目录
            self.start()  # 新增代码+MCPLifecycleV2: 复用现有启动读取逻辑重建 schema/routes/metadata；若没有这行代码，刷新逻辑会重复大量注册表转换代码且容易不一致
            summary["refreshed_tools"] = True  # 新增代码+MCPLifecycleV2: 标记工具目录已经重建；若没有这行代码，LearningAgent 不会知道需要清自己的 catalog cache
        if "prompts" in changed_kinds or "resources" in changed_kinds:  # 新增代码+MCPLifecycleV2: prompts/resources 变化会影响 ClaudeCode 风格 MCP skills/search index；若没有这行代码，后续技能发现可能继续用旧索引
            self._mcp_skill_refresh_version += 1  # 新增代码+MCPLifecycleV2: 递增技能刷新版本作为当前最小版的索引失效挂点；若没有这行代码，MCP skills refresh 没有可验证状态
            summary["mcp_skill_refresh_version"] = self._mcp_skill_refresh_version  # 新增代码+MCPLifecycleV2: 把更新后的版本写回摘要；若没有这行代码，调用方看到的版本会停在刷新前
        return summary  # 新增代码+MCPLifecycleV2: 返回完整刷新摘要；若没有这行代码，上层无法决定是否清理 Tool Catalog cache

    def lifecycle_events(self) -> list[dict[str, Any]]:  # 新增代码+MCPLifecycleV2: 返回最近 MCP 生命周期事件审计快照；若没有这行代码，doctor 或测试只能访问私有字段
        return copy.deepcopy(self._lifecycle_events)  # 新增代码+MCPLifecycleV2: 深拷贝返回避免外部修改内部审计缓存；若没有这行代码，调用方可能污染事件历史

    def _drain_lifecycle_notifications(self) -> list[dict[str, Any]]:  # 新增代码+MCPLifecycleV2: 从所有 client 消费并标准化 list_changed notifications；若没有这行代码，refresh_from_notifications 会混入 client 细节
        events: list[dict[str, Any]] = []  # 新增代码+MCPLifecycleV2: 准备累积标准化 lifecycle 事件；若没有这行代码，循环没有返回容器
        for server_name, client in self._clients.items():  # 新增代码+MCPLifecycleV2: 遍历每个 MCP server client；若没有这行代码，多 server 通知无法统一刷新
            pop_notifications = getattr(client, "pop_notifications", None)  # 新增代码+MCPLifecycleV2: 读取 client 可选的通知拉取方法；若没有这行代码，不支持通知的旧 client 会崩溃
            if not callable(pop_notifications):  # 新增代码+MCPLifecycleV2: 兼容没有 lifecycle notification 支持的 client；若没有这行代码，测试替身或旧 transport 会触发 TypeError
                continue  # 新增代码+MCPLifecycleV2: 跳过不支持通知的 client；若没有这行代码，一个旧 client 会阻断全部刷新
            raw_notifications = pop_notifications()  # 新增代码+MCPLifecycleV2: 拉取并清空该 client 的 pending notifications；若没有这行代码，registry 永远看不到 server 推送的变化
            if not isinstance(raw_notifications, list):  # 新增代码+MCPLifecycleV2: 防御异常 client 返回非列表；若没有这行代码，坏返回值会让遍历抛错
                continue  # 新增代码+MCPLifecycleV2: 跳过坏 client 返回并继续其他 server；若没有这行代码，单个异常 server 会拖垮刷新流程
            for notification in raw_notifications:  # 新增代码+MCPLifecycleV2: 遍历该 server 本批所有通知；若没有这行代码，只能处理零条或一条硬编码通知
                if not isinstance(notification, dict):  # 新增代码+MCPLifecycleV2: 跳过非对象通知；若没有这行代码，异常消息会让 get 调用崩溃
                    continue  # 新增代码+MCPLifecycleV2: 单条坏通知不影响其他通知；若没有这行代码，容错性差
                method = str(notification.get("method", "") or "")  # 新增代码+MCPLifecycleV2: 提取 JSON-RPC notification method；若没有这行代码，无法判断是否为 list_changed
                kind = self._lifecycle_changed_kind(method)  # 新增代码+MCPLifecycleV2: 把 method 映射成 tools/prompts/resources；若没有这行代码，刷新逻辑会依赖字符串散落判断
                if not kind:  # 新增代码+MCPLifecycleV2: 只处理 Phase 3 关心的 list_changed 通知；若没有这行代码，channel 或自定义通知会误触发 catalog 刷新
                    continue  # 新增代码+MCPLifecycleV2: 忽略非 list_changed 通知；若没有这行代码，未知通知会污染生命周期审计
                params = notification.get("params", {})  # 新增代码+MCPLifecycleV2: 读取通知参数用于审计；若没有这行代码，事件历史缺少 server 附带上下文
                event = {  # 新增代码+MCPLifecycleV2: 构造标准化生命周期事件；若没有这行代码，后续摘要需要重复解析原始通知
                    "server": server_name,  # 新增代码+MCPLifecycleV2: 记录触发通知的 MCP server；若没有这行代码，多 server 刷新难以定位来源
                    "method": method,  # 新增代码+MCPLifecycleV2: 保留原始 notification method；若没有这行代码，审计无法核对协议事件
                    "kind": kind,  # 新增代码+MCPLifecycleV2: 保存归类后的变化类型；若没有这行代码，摘要无法聚合 changed_kinds
                    "params": copy.deepcopy(params) if isinstance(params, dict) else {},  # 新增代码+MCPLifecycleV2: 保存参数快照且只接受对象；若没有这行代码，异常 params 可能污染事件历史
                    "received_at": time.strftime("%Y-%m-%d %H:%M:%S"),  # 新增代码+MCPLifecycleV2: 记录本地处理时间；若没有这行代码，用户无法判断刷新事件新旧
                }  # 新增代码+MCPLifecycleV2: lifecycle 事件字典结束；若没有这行代码，Python 语法不完整
                events.append(event)  # 新增代码+MCPLifecycleV2: 保存标准化事件；若没有这行代码，刷新摘要永远为空
        return events  # 新增代码+MCPLifecycleV2: 返回本批有效生命周期事件；若没有这行代码，refresh_from_notifications 拿不到任何输入

    @staticmethod  # 新增代码+MCPLifecycleV2: method 映射不依赖 registry 实例状态；若没有这行代码，测试和未来 helper 复用会更困难
    def _lifecycle_changed_kind(method: str) -> str:  # 新增代码+MCPLifecycleV2: 将 MCP list_changed notification method 映射成资源类型；若没有这行代码，协议字符串会分散在多个分支
        if method in {"notifications/tools/list_changed", "tools/list_changed"}:  # 新增代码+MCPLifecycleV2: 兼容标准 notification 名和简写 method；若没有这行代码，部分 server 的 tools 变化可能不被识别
            return "tools"  # 新增代码+MCPLifecycleV2: 返回工具目录变化类型；若没有这行代码，tools/list_changed 不会触发 tools/list 刷新
        if method in {"notifications/prompts/list_changed", "prompts/list_changed"}:  # 新增代码+MCPLifecycleV2: 兼容 prompts list_changed 标准和简写；若没有这行代码，远程 prompt 变化不会被记录
            return "prompts"  # 新增代码+MCPLifecycleV2: 返回 prompts 变化类型；若没有这行代码，prompt/skill 刷新挂点无法触发
        if method in {"notifications/resources/list_changed", "resources/list_changed"}:  # 新增代码+MCPLifecycleV2: 兼容 resources list_changed 标准和简写；若没有这行代码，资源变化不会被记录
            return "resources"  # 新增代码+MCPLifecycleV2: 返回 resources 变化类型；若没有这行代码，resource/skill 刷新挂点无法触发
        return ""  # 新增代码+MCPLifecycleV2: 未知 method 不属于 Phase 3 生命周期刷新；若没有这行代码，调用方无法用空字符串判断不处理

    def listen_stream(self, server_name: str, max_events: int = 5, timeout_seconds: float = 2.0, resume: bool = True) -> str:  # 新增代码+MCPStream: 转发 GET listen 到指定 MCP client；若省略: LearningAgent 无法通过 registry 使用监听能力
        if server_name not in self._clients:  # 新增代码+MCPStream: 检查 server 是否存在；若省略: 输错 server 会触发 KeyError
            raise RuntimeError(f"未知 MCP server：{server_name}")  # 新增代码+MCPStream: 返回清晰错误；若省略: 用户不知道哪个参数错了
        client = self._clients[server_name]  # 新增代码+MCPStream: 取出目标 client；若省略: 无法调用具体 transport
        listen_stream = getattr(client, "listen_stream", None)  # 新增代码+MCPStream: 检查 client 是否支持监听；若省略: stdio client 会出现属性错误
        if not callable(listen_stream):  # 新增代码+MCPStream: 非 HTTP client 不支持 GET listen；若省略: stdio 或 legacy client 会崩溃
            raise RuntimeError(f"MCP server {server_name} 不支持 HTTP GET stream listen。")  # 新增代码+MCPStream: 返回清晰边界；若省略: 用户不知道该 server 不是 HTTP stream
        return str(listen_stream(max_events=max_events, timeout_seconds=timeout_seconds, resume=resume))  # 新增代码+MCPStream: 返回 client 监听结果；若省略: registry 方法没有输出

    def has_tool(self, name: str) -> bool:  # 新增代码+MCP 工具注册表: 判断指定前缀工具名是否存在；若省略: 上层无法在调用前做快速检查
        return name in self._tool_routes  # 新增代码+MCP 工具注册表: 通过路由表确认工具可调用；若省略: has_tool 无法反映实际可转发工具

    def sanitize_tool_arguments(self, prefixed_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+MCP参数清洗: 按目标工具 schema 删除未声明参数；若省略: browser_open 会继续收到 status/action 等串味字段
        if not isinstance(arguments, dict):  # 新增代码+MCP参数清洗: 防御异常模型输出非对象参数；若省略: 后续 items 遍历会抛出难懂错误
            return {}  # 新增代码+MCP参数清洗: 非对象参数降级为空对象；若省略: 外部 MCP server 可能收到非法参数类型
        schema = self._tool_parameter_schemas.get(prefixed_name, {})  # 新增代码+MCP参数清洗: 读取该工具启动时缓存的参数 schema；若省略: 无法知道允许哪些字段
        raw_properties = schema.get("properties") if isinstance(schema, dict) else None  # 新增代码+MCP参数清洗: 取出 schema 声明的字段表；若省略: 无法判断哪些键是合法的
        if not isinstance(raw_properties, dict):  # 新增代码+MCP参数清洗: 没有 properties 的开放 schema 不做过滤；若省略: 可能误删真正需要的动态参数
            return dict(arguments)  # 新增代码+MCP参数清洗: 返回浅拷贝避免调用方后续修改原字典影响记录；若省略: 参数对象可能被外部共享污染
        if schema.get("additionalProperties") is True:  # 新增代码+MCP参数清洗: 明确允许额外字段的工具保留原参数；若省略: 开放工具会被过度过滤
            return dict(arguments)  # 新增代码+MCP参数清洗: 保留开放 schema 的参数但返回副本；若省略: 动态参数工具可能失效
        allowed_names = set(raw_properties.keys())  # 新增代码+MCP参数清洗: 将合法字段名做成集合便于过滤；若省略: 每个参数都要重复遍历 properties
        return {key: value for key, value in arguments.items() if key in allowed_names}  # 新增代码+MCP参数清洗: 只保留目标工具声明过的字段；若省略: 无关字段会继续进入授权提示和真实 MCP 调用

    def call_tool(self, prefixed_name: str, arguments: dict[str, Any]) -> str:  # 新增代码+MCP 工具注册表: 用前缀工具名调用对应 MCP client；若省略: 模型选择 MCP 工具后无法执行
        if prefixed_name not in self._tool_routes:  # 新增代码+MCP 工具注册表: 检查工具是否已注册；若省略: 未知工具会触发难懂 KeyError
            raise RuntimeError(f"未知 MCP 工具：{prefixed_name}")  # 新增代码+MCP 工具注册表: 抛出清晰未知工具错误；若省略: 调试工具名错误会更困难
        client, raw_tool_name = self._tool_routes[prefixed_name]  # 新增代码+MCP 工具注册表: 取出目标 client 和原始工具名；若省略: 无法剥离 mcp__server__ 前缀
        safe_arguments = self.sanitize_tool_arguments(prefixed_name, arguments)  # 新增代码+MCP参数清洗: 调用前再次清洗参数作为安全兜底；若省略: 直接调用 registry 的路径仍可能发送串味字段
        if raw_tool_name == self.AUTHENTICATE_TOOL_NAME:  # 新增代码+MCPAuthMetadata: 如果这是鉴权伪工具；若省略: registry 会把 __authenticate__ 当真实 MCP 工具发给 server
            authenticate = getattr(client, "authenticate", None)  # 新增代码+MCPAuthMetadata: 读取 client 的 authenticate 方法；若省略: 无法生成本地鉴权说明
            if not callable(authenticate):  # 新增代码+MCPAuthMetadata: 防御 client 缺少 authenticate 方法；若省略: AttributeError 会变成难懂错误
                raise RuntimeError(f"MCP server {prefixed_name} 没有可用 authenticate 处理器。")  # 新增代码+MCPAuthMetadata: 抛出清晰路由错误；若省略: 调试伪工具失败更困难
            return str(authenticate(safe_arguments))  # 修改代码+MCP参数清洗: 用清洗后的参数调用本地鉴权说明；若省略: authenticate 工具可能接收 token 等多余字段
        return client.call_tool(raw_tool_name, safe_arguments)  # 修改代码+MCP参数清洗: 转发到 client 时只传目标工具声明的字段；若省略: 真实浏览器工具会继续收到无关参数

    def list_resources(self, server_name: str | None = None) -> list[dict[str, Any]]:  # 新增代码+MCPResource: 聚合已启动 MCP server 暴露的 resources；若省略: agent 无法列出 MCP 外部资源
        if server_name is not None and server_name not in self._clients:  # 新增代码+MCPResource: 检查指定 server 是否存在；若省略: 用户输错 server 会得到空列表而难以排查
            raise RuntimeError(f"未知 MCP server：{server_name}")  # 新增代码+MCPResource: 抛出清晰未知 server 错误；若省略: 调试资源来源错误会更困难
        resources: list[dict[str, Any]] = []  # 新增代码+MCPResource: 准备保存带 server 字段的资源条目；若省略: 无法累积多个 server 的 resources
        for current_server_name, client in self._clients.items():  # 新增代码+MCPResource: 遍历每个 MCP server 和 client；若省略: 只能读取零个或一个 server
            if server_name is not None and current_server_name != server_name:  # 新增代码+MCPResource: 如果调用方指定了 server 就跳过其他 server；若省略: 筛选参数不会生效
                continue  # 新增代码+MCPResource: 跳过非目标 server；若省略: 多 server 结果会混入无关资源
            list_resources = getattr(client, "list_resources", None)  # 新增代码+MCPResource: 读取 client 的 list_resources 方法；若省略: 不支持资源的 client 会直接属性错误
            if not callable(list_resources):  # 新增代码+MCPResource: 检查当前 client 是否支持资源列表；若省略: 工具型 MCP server 可能让列表操作崩溃
                continue  # 新增代码+MCPResource: 跳过不支持 resources/list 的 server；若省略: 一个 server 缺能力会影响所有 server
            raw_resources = list_resources()  # 新增代码+MCPResource: 调用 server 的 resources/list；若省略: registry 拿不到实际资源数据
            if not isinstance(raw_resources, list):  # 新增代码+MCPResource: 防御异常 client 返回非列表；若省略: 后续遍历可能出错
                continue  # 新增代码+MCPResource: 跳过坏返回值并处理其他 server；若省略: 单个坏 server 会中断资源发现
            for raw_resource in raw_resources:  # 新增代码+MCPResource: 遍历当前 server 的每个资源条目；若省略: resources/list 结果无法转换
                if not isinstance(raw_resource, dict):  # 新增代码+MCPResource: 跳过非对象资源项；若省略: 异常 MCP server 返回会让 registry 崩溃
                    continue  # 新增代码+MCPResource: 保持单个坏资源不影响其他资源；若省略: 容错路径无法继续
                resource = copy.deepcopy(raw_resource)  # 新增代码+MCPResource: 深拷贝资源条目避免调用方污染 client 返回对象；若省略: 外部修改可能影响测试 fake 或缓存
                resource["server"] = current_server_name  # 新增代码+MCPResource: 给资源补充来源 server；若省略: read_mcp_resource 无法知道该向哪个 server 读取
                resources.append(resource)  # 新增代码+MCPResource: 保存转换后的资源条目；若省略: 有效资源不会返回给上层
        return resources  # 新增代码+MCPResource: 返回聚合后的资源列表；若省略: 上层拿不到资源发现结果

    def read_resource(self, server_name: str, uri: str) -> str:  # 新增代码+MCPResource: 按 server 和 uri 读取 MCP resource；若省略: agent 无法把资源发现结果转成正文
        if server_name not in self._clients:  # 新增代码+MCPResource: 检查目标 server 是否存在；若省略: 未知 server 会触发难懂 KeyError
            raise RuntimeError(f"未知 MCP server：{server_name}")  # 新增代码+MCPResource: 抛出清晰未知 server 错误；若省略: 用户不知道 server 名写错
        client = self._clients[server_name]  # 新增代码+MCPResource: 取出目标 server 对应 client；若省略: 无法把 read 请求路由到正确连接
        read_resource = getattr(client, "read_resource", None)  # 新增代码+MCPResource: 读取 client 的 read_resource 方法；若省略: 不支持资源读取的 server 会属性错误
        if not callable(read_resource):  # 新增代码+MCPResource: 检查当前 client 是否支持资源读取；若省略: 工具型 MCP server 可能让读取操作崩溃
            raise RuntimeError(f"MCP server {server_name} 不支持 resources/read。")  # 新增代码+MCPResource: 抛出清晰能力缺失错误；若省略: 用户难以区分 server 不存在和不支持资源
        return str(read_resource(uri))  # 新增代码+MCPResource: 调用目标 client 读取 uri 并转成文本；若省略: 上层拿不到资源正文

    def list_prompts(self, server_name: str | None = None) -> list[dict[str, Any]]:  # 新增代码+MCPPrompt: 聚合已启动 MCP server 暴露的 prompts；若省略: agent 无法列出 MCP 远程提示词
        if server_name is not None and server_name not in self._clients:  # 新增代码+MCPPrompt: 检查指定 server 是否存在；若省略: 用户输错 server 会得到空列表而难以排查
            raise RuntimeError(f"未知 MCP server：{server_name}")  # 新增代码+MCPPrompt: 抛出清晰未知 server 错误；若省略: 调试 prompt 来源错误会更困难
        prompts: list[dict[str, Any]] = []  # 新增代码+MCPPrompt: 准备保存带 server 字段的 prompt 条目；若省略: 无法累积多个 server 的 prompts
        for current_server_name, client in self._clients.items():  # 新增代码+MCPPrompt: 遍历每个 MCP server 和 client；若省略: 只能读取零个或一个 server
            if server_name is not None and current_server_name != server_name:  # 新增代码+MCPPrompt: 如果调用方指定了 server 就跳过其他 server；若省略: 筛选参数不会生效
                continue  # 新增代码+MCPPrompt: 跳过非目标 server；若省略: 多 server 结果会混入无关 prompts
            list_prompts = getattr(client, "list_prompts", None)  # 新增代码+MCPPrompt: 读取 client 的 list_prompts 方法；若省略: 不支持 prompts 的 client 会直接属性错误
            if not callable(list_prompts):  # 新增代码+MCPPrompt: 检查当前 client 是否支持 prompt 列表；若省略: 纯工具型 MCP server 可能让列表操作崩溃
                continue  # 新增代码+MCPPrompt: 跳过不支持 prompts/list 的 server；若省略: 一个 server 缺能力会影响所有 server
            raw_prompts = list_prompts()  # 新增代码+MCPPrompt: 调用 server 的 prompts/list；若省略: registry 拿不到实际 prompt 数据
            if not isinstance(raw_prompts, list):  # 新增代码+MCPPrompt: 防御异常 client 返回非列表；若省略: 后续遍历可能出错
                continue  # 新增代码+MCPPrompt: 跳过坏返回值并处理其他 server；若省略: 单个坏 server 会中断 prompt 发现
            for raw_prompt in raw_prompts:  # 新增代码+MCPPrompt: 遍历当前 server 的每个 prompt 条目；若省略: prompts/list 结果无法转换
                if not isinstance(raw_prompt, dict):  # 新增代码+MCPPrompt: 跳过非对象 prompt 项；若省略: 异常 MCP server 返回会让 registry 崩溃
                    continue  # 新增代码+MCPPrompt: 保持单个坏 prompt 不影响其他 prompt；若省略: 容错路径无法继续
                prompt = copy.deepcopy(raw_prompt)  # 新增代码+MCPPrompt: 深拷贝 prompt 条目避免调用方污染 client 返回对象；若省略: 外部修改可能影响测试 fake 或缓存
                prompt["server"] = current_server_name  # 新增代码+MCPPrompt: 给 prompt 补充来源 server；若省略: read_mcp_prompt 无法知道该向哪个 server 读取
                prompts.append(prompt)  # 新增代码+MCPPrompt: 保存转换后的 prompt 条目；若省略: 有效 prompt 不会返回给上层
        return prompts  # 新增代码+MCPPrompt: 返回聚合后的 prompt 列表；若省略: 上层拿不到 prompt 发现结果

    def read_prompt(self, server_name: str, name: str, arguments: dict[str, Any] | None = None) -> str:  # 新增代码+MCPPrompt: 按 server 和 name 读取 MCP prompt；若省略: agent 无法把 prompt 发现结果转成正文
        if server_name not in self._clients:  # 新增代码+MCPPrompt: 检查目标 server 是否存在；若省略: 未知 server 会触发难懂 KeyError
            raise RuntimeError(f"未知 MCP server：{server_name}")  # 新增代码+MCPPrompt: 抛出清晰未知 server 错误；若省略: 用户不知道 server 名写错
        client = self._clients[server_name]  # 新增代码+MCPPrompt: 取出目标 server 对应 client；若省略: 无法把 prompts/get 请求路由到正确连接
        get_prompt = getattr(client, "get_prompt", None)  # 新增代码+MCPPrompt: 读取 client 的 get_prompt 方法；若省略: 不支持 prompt 读取的 server 会属性错误
        if not callable(get_prompt):  # 新增代码+MCPPrompt: 检查当前 client 是否支持 prompt 读取；若省略: 纯工具型 MCP server 可能让读取操作崩溃
            raise RuntimeError(f"MCP server {server_name} 不支持 prompts/get。")  # 新增代码+MCPPrompt: 抛出清晰能力缺失错误；若省略: 用户难以区分 server 不存在和不支持 prompts
        return str(get_prompt(name, arguments or {}))  # 新增代码+MCPPrompt: 调用目标 client 读取 prompt 并转成文本；若省略: 上层拿不到 prompt 正文

    def close(self) -> None:  # 新增代码+MCP 工具注册表: 关闭所有 MCP client；若省略: server 子进程和连接可能泄漏
        for client in self._clients.values():  # 新增代码+MCP 工具注册表: 遍历所有已配置 client；若省略: 只能关闭零个或一个 client
            client.close()  # 新增代码+MCP 工具注册表: 调用 client 自身关闭逻辑；若省略: 真实 McpStdioClient 的子进程不会退出

    @classmethod  # 新增代码+MCP 工具注册表: 让命名逻辑可被类级调用；若省略: 构造前缀名必须依赖实例
    def _prefix_tool_name(cls, server_name: str, tool_name: str) -> str:  # 新增代码+MCP 工具注册表: 生成 OpenAI-compatible MCP 工具名；若省略: 命名格式会散落在调用处
        safe_server_name = cls._sanitize_tool_segment(server_name)  # 新增代码+MCP 工具注册表: 清理 server 名片段；若省略: server 名里的非法字符可能让工具名无效
        safe_tool_name = cls._sanitize_tool_segment(tool_name)  # 新增代码+MCP 工具注册表: 清理工具名片段；若省略: MCP 工具名里的非法字符可能让模型 schema 无效
        return f"mcp__{safe_server_name}__{safe_tool_name}"  # 新增代码+MCP 工具注册表: 返回规定的 mcp__服务器__工具 格式；若省略: Task 4 要求的名称格式无法满足

    @staticmethod  # 新增代码+MCP 工具注册表健壮性: 唯一名生成不依赖实例状态；若省略: 测试和内部调用必须创建额外状态对象
    def _unique_tool_name(base_name: str, used_tool_names: set[str]) -> str:  # 新增代码+MCP 工具注册表健壮性: 为已占用工具名追加递增后缀；若省略: sanitize 后冲突工具会共享同一个名称
        if base_name not in used_tool_names:  # 新增代码+MCP 工具注册表健壮性: 如果基础名称尚未使用；若省略: 第一个工具也会被错误追加后缀
            return base_name  # 新增代码+MCP 工具注册表健壮性: 直接返回未冲突名称；若省略: 无冲突工具名称会变得不稳定
        index = 2  # 新增代码+MCP 工具注册表健壮性: 冲突后缀从 _2 开始；若省略: 无法满足第二个同名工具变成 _2 的约定
        while f"{base_name}_{index}" in used_tool_names:  # 新增代码+MCP 工具注册表健壮性: 跳过已经占用的递增名称；若省略: 第三次以上冲突可能再次重复
            index += 1  # 新增代码+MCP 工具注册表健壮性: 继续尝试下一个序号；若省略: while 会无限循环或停在已占用名称
        return f"{base_name}_{index}"  # 新增代码+MCP 工具注册表健壮性: 返回第一个可用的递增名称；若省略: 冲突工具无法获得可调用名称

    @staticmethod  # 新增代码+MCP 工具注册表: 清理函数不依赖实例状态；若省略: 调用方必须创建对象才能清理名称片段
    def _sanitize_tool_segment(value: str) -> str:  # 新增代码+MCP 工具注册表: 把任意 server/tool 名转成 function name 可用片段；若省略: 非法字符可能导致模型拒绝 schema
        text = str(value).strip()  # 新增代码+MCP 工具注册表: 转字符串并去掉首尾空白；若省略: 空格会进入工具名
        safe_chars: list[str] = []  # 新增代码+MCP 工具注册表: 准备收集合法字符；若省略: 无法逐字符替换非法内容
        allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"  # 新增代码+MCP 工具注册表健壮性: 明确 ASCII 白名单；若省略: char.isalnum 会保留中文等非 ASCII 字符
        for char in text:  # 新增代码+MCP 工具注册表: 遍历名称片段里的每个字符；若省略: 无法保留合法字符并替换非法字符
            if char in allowed:  # 修改代码+MCP 工具注册表健壮性: 只保留显式 ASCII 白名单字符；若省略: 非 ASCII 字符可能进入 OpenAI function name
                safe_chars.append(char)  # 新增代码+MCP 工具注册表: 保留合法字符；若省略: 合法名称也会被清空
            else:  # 新增代码+MCP 工具注册表: 处理空格、斜杠、点号等非法字符；若省略: 非法字符不会被替换
                safe_chars.append("_")  # 新增代码+MCP 工具注册表: 用下划线替换非法字符；若省略: schema 名称兼容性降低
        safe_text = "".join(safe_chars).strip("_")  # 新增代码+MCP 工具注册表: 合并字符并去掉边缘下划线；若省略: 名称可能出现多余边界符号
        return safe_text or "unnamed"  # 新增代码+MCP 工具注册表: 空名称兜底为 unnamed；若省略: 可能生成 mcp____tool 这类不可读名称


def run_mcp_doctor(workspace: str | Path) -> str:  # 新增代码+MCP诊断: 执行 MCP 配置、启动和工具可见性诊断；若省略: 用户无法自查 MCP 为什么没有出现在模型工具列表里
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+MCP诊断: 规范化工作区路径；若省略: 报告里的相对路径可能让用户找错目录
    config_path = mcp_server_config_path(workspace_path)  # 新增代码+MCP诊断: 取得 mcp_servers.json 真实路径；若省略: 诊断无法指出配置文件位置
    lines = ["MCP Doctor", f"工作区：{workspace_path}", f"配置文件：{config_path}"]  # 新增代码+MCP诊断: 初始化报告标题、工作区和配置路径；若省略: 报告缺少定位信息
    builtin_tool_names = [schema["function"]["name"] for schema in _main_tool_schemas()]
    lines.append("内置工具：" + ", ".join(builtin_tool_names))  # 新增代码+MCP诊断: 展示 read_file/write_file/append_memory 始终可见；若省略: 用户可能误以为无 MCP 就没有任何工具
    real_chrome_diagnostic = _diagnose_real_chrome_environment(workspace_path)  # 修改代码+McpSplit: 通过兼容层诊断真实 Chrome profile 自动化环境；若省略: 阶段 4 拆分会绕过旧入口 patch 并让 doctor 测试依赖真实机器
    lines.append(f"真实 Chrome profile 诊断：{real_chrome_diagnostic.status}")  # 新增代码+RealChromeDoctor: 输出 available/needs_user_action/blocked 三态；若省略: 用户无法快速判断真实 Chrome 自动化是否可尝试
    lines.append(f"真实 Chrome 路径：{real_chrome_diagnostic.chrome_path}")  # 新增代码+RealChromeDoctor: 输出检测到的 Chrome 可执行文件路径；若省略: 用户不知道 doctor 找到的是哪个 Chrome
    lines.append(f"真实 Chrome User Data：{real_chrome_diagnostic.user_data_dir}")  # 新增代码+RealChromeDoctor: 输出检测到的 User Data 根目录；若省略: 用户不知道真实 profile 目录是否被识别
    lines.append(f"真实 Chrome 正在运行：{str(real_chrome_diagnostic.chrome_running).lower()}")  # 新增代码+RealChromeDoctor: 输出 Chrome 是否正在运行并使用 true/false；若省略: 用户不知道是否需要先关闭 Chrome
    lines.append(f"真实 Chrome 默认端口可用：{str(real_chrome_diagnostic.port_available).lower()}")  # 新增代码+RealChromeDoctor: 输出默认 CDP 端口是否可用并使用 true/false；若省略: 端口冲突不会提前暴露
    real_chrome_messages = real_chrome_diagnostic.messages or ["环境暂未发现阻塞问题。"]  # 新增代码+RealChromeDoctor: 保证至少有一条提示说明；若省略: messages 为空时“真实 Chrome 提示”字段会消失
    for message in real_chrome_messages:  # 新增代码+RealChromeDoctor: 逐条输出真实 Chrome 诊断提示；若省略: 多个环境问题只能显示一个或完全丢失
        lines.append(f"真实 Chrome 提示：{message}")  # 新增代码+RealChromeDoctor: 把诊断提示写入 doctor 报告；若省略: 用户看不到需要关闭 Chrome、换端口等行动建议
    if not config_path.exists():  # 新增代码+MCP诊断: 检查配置文件是否存在；若省略: 缺配置场景会继续尝试启动空 registry
        lines.append("配置状态：未找到 mcp_servers.json")  # 新增代码+MCP诊断: 明确说明未找到配置文件；若省略: 用户不知道为什么没有外部工具
        lines.append("模型可见 MCP 工具：0 个")  # 新增代码+MCP诊断: 明确外部工具数量为零；若省略: 用户无法判断模型是否能搜索网页
        lines.append("建议：在 learning_agent 目录创建 mcp_servers.json，或先配置 browser_search MCP server。")  # 新增代码+MCP诊断: 给出直接修复方向；若省略: 诊断只报错不指导下一步
        return "\n".join(lines)  # 新增代码+MCP诊断: 返回缺配置报告；若省略: 后续配置解析没有输入
    lines.append("配置状态：已找到 mcp_servers.json")  # 新增代码+MCP诊断: 说明配置文件存在；若省略: 用户不知道 doctor 已经读到文件
    configs = load_mcp_server_configs(workspace_path)  # 新增代码+MCP诊断: 解析 MCP server 配置；若省略: doctor 无法知道要启动哪些 server
    if not configs:  # 新增代码+MCP诊断: 检查配置文件里是否有有效 server；若省略: 空配置会被误判为启动成功
        lines.append("配置内容：没有解析到可用 MCP server")  # 新增代码+MCP诊断: 明确配置内容不可用；若省略: 用户很难区分文件存在和配置有效
        lines.append("模型可见 MCP 工具：0 个")  # 新增代码+MCP诊断: 明确没有可见 MCP 工具；若省略: 输出不完整
        lines.append("建议：stdio 检查 name、command、args；HTTP/SSE 检查 name、transport、url、headers 字段。")  # 修改代码+MCPTransport: 提示不同 transport 的必填字段；若省略: 初学者不知道远程 MCP 应该改哪里
        return "\n".join(lines)  # 新增代码+MCP诊断: 返回无有效 server 报告；若省略: from_configs 会创建空 registry
    lines.append("配置内容：解析到 " + ", ".join(f"{config.name}({config.transport})" for config in configs))  # 修改代码+MCPTransport: 展示解析出的 server 名和 transport；若省略: 用户不知道配置是否按本地或远程读取
    registry = McpToolRegistry.from_configs(configs)  # 新增代码+MCP诊断: 根据配置创建 MCP 注册表；若省略: doctor 无法执行真实启动和 tools/list
    try:  # 新增代码+MCP诊断: 保护启动过程并把异常变成可读报告；若省略: 单个 server 失败会让 doctor 直接抛栈
        registry.start()  # 新增代码+MCP诊断: 启动所有配置的 MCP server 并读取 tools/list；若省略: doctor 只能检查配置，不能验证工具真的可见
        auth_challenges = registry.auth_challenges()  # 新增代码+MCPAuthMetadata: 读取哪些 server 只完成到 401 鉴权挑战；若省略: doctor 会把需要登录误报成普通启动成功
        start_errors = registry.start_errors()  # 新增代码+MCP诊断部分失败: 读取单个 MCP server 启动或 tools/list 失败记录；若省略: doctor 会把失败 server 误报为启动成功
        for server_name in registry.server_names():  # 修改代码+MCPTransport: 遍历已配置 server 名；若省略: 报告无法逐个展示启动成功
            matching_config = next((config for config in configs if config.name == server_name), None)  # 新增代码+MCPTransport: 查找 server 对应配置以显示 transport；若省略: doctor 成功行缺少连接方式
            transport_text = matching_config.transport if matching_config is not None else "unknown"  # 新增代码+MCPTransport: 生成 transport 展示文本并兜底；若省略: 异常配置会导致 AttributeError
            if server_name in auth_challenges:  # 新增代码+MCPAuthMetadata: 判断当前 server 是否需要鉴权；若省略: 401 server 会被展示成完全可用
                challenge = auth_challenges[server_name]  # 新增代码+MCPAuthMetadata: 取出该 server 的鉴权挑战；若省略: 无法展示 metadata URL
                metadata_text = challenge.resource_metadata_url or "未提供 resource_metadata"  # 新增代码+MCPAuthMetadata: 生成 metadata 展示文本；若省略: 缺失 metadata 时输出不清楚
                lines.append(f"需要鉴权：{server_name}({transport_text}) resource_metadata={metadata_text}")  # 新增代码+MCPAuthMetadata: 报告 auth-required 状态；若省略: 用户不知道应调用 authenticate 工具
                continue  # 新增代码+MCPAuthMetadata: 鉴权 server 不再输出启动成功；若省略: 同一 server 状态会自相矛盾
            if server_name in start_errors:  # 新增代码+MCP诊断部分失败: 判断当前 server 是否在部分失败表中；若省略: 已失败 server 会继续进入启动成功分支
                lines.append(f"启动失败：{server_name}({transport_text}) 错误：{start_errors[server_name]}")  # 新增代码+MCP诊断部分失败: 把失败 server 和错误文本写进报告；若省略: 用户无法定位坏 server 的原因
                continue  # 新增代码+MCP诊断部分失败: 失败 server 不再输出启动成功；若省略: 同一 server 会同时显示失败和成功
            lines.append(f"启动成功：{server_name}({transport_text})")  # 修改代码+MCPTransport: 标记 server 启动成功并显示 transport；若省略: 用户无法确认是本地还是远程启动阶段通过
        tool_names = [schema["function"]["name"] for schema in registry.tool_schemas()]  # 新增代码+MCP诊断: 收集模型最终可见的 MCP 工具名；若省略: doctor 不能回答“模型看到哪些工具”
        lines.append(f"模型可见 MCP 工具：{len(tool_names)} 个")  # 新增代码+MCP诊断: 输出 MCP 工具数量；若省略: 用户无法快速判断是否为空
        if tool_names:  # 新增代码+MCP诊断: 如果存在 MCP 工具；若省略: 会输出空工具列表标题
            lines.extend(f"- {tool_name}" for tool_name in tool_names)  # 新增代码+MCP诊断: 逐行展示 mcp__... 工具名；若省略: 用户不知道提示词里该期待哪个工具名
        else:  # 新增代码+MCP诊断: 处理 server 启动但没有工具的情况；若省略: 0 工具场景缺少解释
            lines.append("建议：MCP server 已启动，但 tools/list 没有返回工具，请检查 server 实现。")  # 新增代码+MCP诊断: 给出无工具时的排查方向；若省略: 用户不知道问题在 server 工具暴露层
    except Exception as error:  # 新增代码+MCP诊断: 捕获启动、initialize、tools/list 中的异常；若省略: doctor 会把内部异常直接暴露为堆栈
        lines.append(f"启动失败：{error}")  # 新增代码+MCP诊断: 把失败原因写进报告；若省略: 用户只能看到命令失败而不知道原因
        lines.append("模型可见 MCP 工具：0 个")  # 新增代码+MCP诊断: 启动失败时明确没有可见 MCP 工具；若省略: 工具可见性结论不清楚
        lines.append("建议：stdio 检查 command/args；HTTP 检查 url/headers 和 initialize/tools/list；SSE 当前请改用 transport=http。")  # 修改代码+MCPTransport: 给出按 transport 区分的排查方向；若省略: 远程 MCP 失败时用户仍只会检查本地命令
    finally:  # 新增代码+MCP诊断: 无论启动成功失败都尝试清理 MCP 进程；若省略: doctor 可能遗留 server 子进程
        registry.close()  # 新增代码+MCP诊断: 关闭所有 doctor 启动的 MCP client；若省略: 诊断结束后外部进程可能残留
    return "\n".join(lines)  # 新增代码+MCP诊断: 返回完整诊断报告；若省略: 调用方拿不到文本输出

