"""Desktop GUI MCP management payload helpers."""  # 新增代码+DesktopGUIMcpControl：说明本模块只负责 GUI 的 MCP 只读管理数据；如果没有这行，维护者容易把它和真正执行 MCP 工具的逻辑混在一起。
from __future__ import annotations  # 新增代码+DesktopGUIMcpControl：启用延迟类型解析；如果没有这行，较老运行时在读取类型标注时更容易遇到前向引用问题。
import re  # 新增代码+DesktopGUIMcpControl：用于把错误文案里的 token、secret、authorization 等敏感片段脱敏；如果没有这行，GUI 可能显示配置里的密钥。
import urllib.parse  # 新增代码+DesktopGUIMcpControl：用于安全解析 MCP HTTP/SSE 地址；如果没有这行，URL 脱敏只能靠字符串猜测。
from datetime import UTC, datetime  # 新增代码+DesktopGUIMcpControl：用于生成稳定的 UTC payload 时间戳；如果没有这行，前端无法判断 MCP 清单的新鲜度。
from pathlib import Path  # 新增代码+DesktopGUIMcpControl：用于规范化 workspace 和配置文件路径；如果没有这行，Windows 路径在 payload 里容易不一致。
from typing import Any  # 新增代码+DesktopGUIMcpControl：用于标注 JSON 结构中的通用字段；如果没有这行，helper 的输入输出边界不清楚。
from learning_agent.app.gui_protocol import GUI_V2_SCHEMA_VERSION  # 新增代码+DesktopGUIMcpControl：复用 GUI V2 协议版本；如果没有这行，MCP 面板会和其它 GUI endpoint 版本漂移。
from learning_agent.mcp.runtime import McpServerConfig, McpToolRegistry, load_mcp_server_configs  # 新增代码+DesktopGUIMcpControl：复用终端 agent 已有 MCP 配置和 registry；如果没有这行，GUI 会被迫重写 MCP 发现逻辑。

MCP_CONTROL_REUSE_MODULE = "learning_agent.mcp.runtime"  # 新增代码+DesktopGUIMcpControl：集中标注复用模块名称；如果没有这行，payload 里会到处硬编码来源字符串。
MCP_CONTROL_SUPPORTED_COLLECTIONS = {"servers", "resources", "prompts"}  # 新增代码+DesktopGUIMcpControl：限定 GUI 只读集合名称；如果没有这行，未知路径可能被误当成可读集合。
MCP_SECRET_PATTERN = re.compile(r"(?i)(authorization|bearer|token|secret|api[_-]?key|password)(\s*[:=]\s*)?([^\s,;]+)?")  # 新增代码+DesktopGUIMcpControl：匹配常见敏感字段；如果没有这行，错误字符串里的密钥可能泄漏到界面。
MCP_TEXT_LIMIT = 240  # 新增代码+DesktopGUIMcpControl：限制单段展示文本长度；如果没有这行，异常堆栈可能撑爆右侧面板。


def _safe_text(value: object, fallback: str = "") -> str:  # 新增代码+DesktopGUIMcpControl：函数段开始，把未知值转成短且脱敏的 GUI 文本；如果没有这段，异常和配置值会原样进入界面。
    text = str(value).replace("\r", " ").replace("\n", " ").strip() if value is not None else fallback  # 新增代码+DesktopGUIMcpControl：先转字符串并去掉换行；如果没有这行，多行错误会破坏卡片布局。
    if not text:  # 新增代码+DesktopGUIMcpControl：处理空字符串；如果没有这行，后续脱敏会返回空白导致用户看不懂状态。
        text = fallback  # 新增代码+DesktopGUIMcpControl：为空时使用兜底文案；如果没有这行，空错误会让 GUI 看起来像正常状态。
    redacted = MCP_SECRET_PATTERN.sub("<redacted>", text)  # 修改代码+DesktopGUIMcpControl：把命中的敏感片段整体替换成占位符；如果没有这行，token/secret 原词可能残留在 GUI payload。
    return redacted[:MCP_TEXT_LIMIT]  # 新增代码+DesktopGUIMcpControl：裁剪过长文本；如果没有这行，长异常会撑开状态检查器。
# 新增代码+DesktopGUIMcpControl：函数段结束，_safe_text 到此结束；如果没有边界说明，初学者不容易看出它只负责安全文本。


def _safe_url_summary(url: str) -> dict[str, Any]:  # 新增代码+DesktopGUIMcpControl：函数段开始，把 MCP URL 压缩成不含 query/path secret 的摘要；如果没有这段，HTTP MCP 配置可能泄漏密钥。
    parsed = urllib.parse.urlparse(url)  # 新增代码+DesktopGUIMcpControl：解析 URL 的协议和主机；如果没有这行，就无法可靠去掉 query 和 path。
    if not parsed.scheme or not parsed.netloc:  # 新增代码+DesktopGUIMcpControl：识别缺少协议或主机的坏 URL；如果没有这行，坏配置会生成误导性的摘要。
        return {"kind": "url", "origin": "", "host": "", "scheme": "", "valid": False}  # 新增代码+DesktopGUIMcpControl：返回安全空摘要；如果没有这行，前端需要猜测坏 URL 状态。
    return {"kind": "url", "origin": f"{parsed.scheme}://{parsed.netloc}", "host": parsed.hostname or "", "scheme": parsed.scheme, "valid": True}  # 新增代码+DesktopGUIMcpControl：只返回 origin 级别信息；如果没有这行，用户看不到 MCP 服务大致来源。
# 新增代码+DesktopGUIMcpControl：函数段结束，_safe_url_summary 到此结束；如果没有边界说明，初学者不容易看出 URL query 永不返回。


def _safe_config_summary(config: McpServerConfig) -> dict[str, Any]:  # 新增代码+DesktopGUIMcpControl：函数段开始，把 MCP server 配置转成脱敏摘要；如果没有这段，GUI 无法展示配置来源又不能安全隐藏密钥。
    if config.transport in {"http", "sse"}:  # 新增代码+DesktopGUIMcpControl：HTTP/SSE server 使用 URL 摘要；如果没有这行，远程 MCP 会被误按 stdio 展示。
        connection = _safe_url_summary(config.url)  # 新增代码+DesktopGUIMcpControl：脱敏 URL；如果没有这行，URL query 里的 token 可能暴露。
    else:  # 新增代码+DesktopGUIMcpControl：stdio server 使用命令摘要；如果没有这行，本地 MCP server 没有展示路径。
        connection = {"kind": "stdio", "command": Path(config.command).name if config.command else "", "arg_count": len(config.args)}  # 新增代码+DesktopGUIMcpControl：只展示命令名和参数数量；如果没有这行，参数中的 secret 可能进入 GUI。
    return {"name": config.name, "transport": config.transport, "connection": connection, "header_count": len(config.headers), "reuse_module": MCP_CONTROL_REUSE_MODULE}  # 新增代码+DesktopGUIMcpControl：返回白名单配置字段；如果没有这行，前端拿不到 server 的安全配置摘要。
# 新增代码+DesktopGUIMcpControl：函数段结束，_safe_config_summary 到此结束；如果没有边界说明，用户不易理解这里不返回 headers/args。


def _safe_record(value: object) -> dict[str, Any]:  # 新增代码+DesktopGUIMcpControl：函数段开始，把未知对象安全收敛成字典；如果没有这段，registry 返回坏数据时会拖垮 endpoint。
    return value.copy() if isinstance(value, dict) else {}  # 新增代码+DesktopGUIMcpControl：只复制 dict，其他类型返回空对象；如果没有这行，列表或字符串会被误当资源字段。
# 新增代码+DesktopGUIMcpControl：函数段结束，_safe_record 到此结束；如果没有边界说明，类型兜底范围不清楚。


def _safe_stream_state(value: object) -> dict[str, Any]:  # 新增代码+DesktopGUIMcpControl：函数段开始，脱敏 MCP stream 状态；如果没有这段，stream 诊断字段可能携带敏感 header。
    record = _safe_record(value)  # 新增代码+DesktopGUIMcpControl：先收敛成普通字典；如果没有这行，后续遍历可能在坏类型上失败。
    safe_state: dict[str, Any] = {}  # 新增代码+DesktopGUIMcpControl：准备只读白名单输出容器；如果没有这行，安全字段没有保存位置。
    for key, item in record.items():  # 新增代码+DesktopGUIMcpControl：遍历 registry 返回的 stream 字段；如果没有这行，连接状态无法进入 GUI。
        key_text = _safe_text(key, "field")  # 新增代码+DesktopGUIMcpControl：脱敏字段名；如果没有这行，敏感字段名可能被原样显示。
        if isinstance(item, bool) or isinstance(item, int) or item is None:  # 新增代码+DesktopGUIMcpControl：允许安全的标量值；如果没有这行，connected/count 等状态无法展示。
            safe_state[key_text] = item  # 新增代码+DesktopGUIMcpControl：保存安全标量；如果没有这行，前端缺少 stream 状态。
        elif isinstance(item, str):  # 新增代码+DesktopGUIMcpControl：字符串需要脱敏；如果没有这行，字符串状态可能泄漏 secret。
            safe_state[key_text] = _safe_text(item)  # 新增代码+DesktopGUIMcpControl：保存脱敏字符串；如果没有这行，字符串状态无法安全展示。
    return safe_state  # 新增代码+DesktopGUIMcpControl：返回脱敏 stream 状态；如果没有这行，调用方拿不到结果。
# 新增代码+DesktopGUIMcpControl：函数段结束，_safe_stream_state 到此结束；如果没有边界说明，stream 字段白名单不清楚。


def _resource_payload(server_name: str, resource: object) -> dict[str, Any]:  # 新增代码+DesktopGUIMcpControl：函数段开始，把 MCP resource 转成 GUI 白名单字段；如果没有这段，resource 列表会暴露未知字段。
    record = _safe_record(resource)  # 新增代码+DesktopGUIMcpControl：收敛 registry resource；如果没有这行，坏 resource 会导致字段读取异常。
    return {"server": server_name, "name": _safe_text(record.get("name"), "resource"), "uri": _safe_text(record.get("uri"), ""), "mime_type": _safe_text(record.get("mimeType") or record.get("mime_type"), ""), "description": _safe_text(record.get("description"), ""), "reuse_module": MCP_CONTROL_REUSE_MODULE}  # 新增代码+DesktopGUIMcpControl：返回 resource 安全字段；如果没有这行，前端无法显示资源名称和归属。
# 新增代码+DesktopGUIMcpControl：函数段结束，_resource_payload 到此结束；如果没有边界说明，resource 白名单范围不清楚。


def _prompt_payload(server_name: str, prompt: object) -> dict[str, Any]:  # 新增代码+DesktopGUIMcpControl：函数段开始，把 MCP prompt 转成 GUI 白名单字段；如果没有这段，prompt 列表会暴露未知字段。
    record = _safe_record(prompt)  # 新增代码+DesktopGUIMcpControl：收敛 registry prompt；如果没有这行，坏 prompt 会导致字段读取异常。
    arguments = record.get("arguments") if isinstance(record.get("arguments"), list) else []  # 新增代码+DesktopGUIMcpControl：只接受参数数组；如果没有这行，坏 arguments 会污染计数。
    return {"server": server_name, "name": _safe_text(record.get("name"), "prompt"), "description": _safe_text(record.get("description"), ""), "argument_count": len(arguments), "reuse_module": MCP_CONTROL_REUSE_MODULE}  # 新增代码+DesktopGUIMcpControl：返回 prompt 安全字段；如果没有这行，前端无法显示提示词名称和参数数量。
# 新增代码+DesktopGUIMcpControl：函数段结束，_prompt_payload 到此结束；如果没有边界说明，prompt 白名单范围不清楚。


def _server_status(server_name: str, start_errors: dict[str, Any], resource_errors: dict[str, str], prompt_errors: dict[str, str], available: bool) -> tuple[str, str]:  # 新增代码+DesktopGUIMcpControl：函数段开始，计算单个 MCP server 的状态和安全错误；如果没有这段，前端只能自己猜失败原因。
    if server_name in start_errors:  # 新增代码+DesktopGUIMcpControl：优先展示启动错误；如果没有这行，启动失败可能被误显示为 available。
        return "failed", _safe_text(start_errors.get(server_name), "MCP server 启动失败")  # 新增代码+DesktopGUIMcpControl：返回失败和脱敏错误；如果没有这行，用户看不到启动失败摘要。
    if server_name in resource_errors:  # 新增代码+DesktopGUIMcpControl：检查资源枚举错误；如果没有这行，资源失败会被吞掉。
        return "degraded", resource_errors[server_name]  # 新增代码+DesktopGUIMcpControl：返回降级和资源错误；如果没有这行，前端无法解释 resource count 为 0。
    if server_name in prompt_errors:  # 新增代码+DesktopGUIMcpControl：检查 prompt 枚举错误；如果没有这行，提示词失败会被吞掉。
        return "degraded", prompt_errors[server_name]  # 新增代码+DesktopGUIMcpControl：返回降级和 prompt 错误；如果没有这行，前端无法解释 prompt count 为 0。
    return ("available" if available else "configured"), ""  # 新增代码+DesktopGUIMcpControl：没有错误时按 registry 是否启动区分状态；如果没有这行，所有 server 状态会变成空。
# 新增代码+DesktopGUIMcpControl：函数段结束，_server_status 到此结束；如果没有边界说明，状态优先级不清楚。


def build_gui_mcp_inventory_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIMcpControl：函数段开始，构建 GUI MCP 管理总览；如果没有这段，GUI 无法看到 MCP server/resource/prompt 状态。
    workspace_path = Path(workspace).resolve()  # 新增代码+DesktopGUIMcpControl：规范化 workspace 路径；如果没有这行，payload 无法说明配置来自哪个项目。
    configs = load_mcp_server_configs(workspace_path)  # 新增代码+DesktopGUIMcpControl：复用原 MCP 配置加载器；如果没有这行，GUI 会漏掉 mcp_servers.json。
    config_by_name = {config.name: config for config in configs}  # 新增代码+DesktopGUIMcpControl：按 server 名建立查找表；如果没有这行，后续无法合并 registry 和配置状态。
    registry = McpToolRegistry.from_configs(configs)  # 新增代码+DesktopGUIMcpControl：复用原 MCP registry；如果没有这行，GUI 无法按真实 runtime 枚举资源和 prompt。
    resources: list[dict[str, Any]] = []  # 新增代码+DesktopGUIMcpControl：准备 resource 输出列表；如果没有这行，资源集合没有容器。
    prompts: list[dict[str, Any]] = []  # 新增代码+DesktopGUIMcpControl：准备 prompt 输出列表；如果没有这行，提示词集合没有容器。
    resource_errors: dict[str, str] = {}  # 新增代码+DesktopGUIMcpControl：记录每个 server 的资源错误；如果没有这行，单 server 降级原因会丢失。
    prompt_errors: dict[str, str] = {}  # 新增代码+DesktopGUIMcpControl：记录每个 server 的 prompt 错误；如果没有这行，单 server 降级原因会丢失。
    safe_error = ""  # 新增代码+DesktopGUIMcpControl：准备顶层安全错误字段；如果没有这行，顶层异常没有稳定合同。
    try:  # 新增代码+DesktopGUIMcpControl：保护 registry 启动和枚举过程；如果没有这行，一个 MCP server 坏掉会让整个 endpoint 500。
        registry.start()  # 新增代码+DesktopGUIMcpControl：启动 MCP registry 以读取真实资源和 prompt；如果没有这行，GUI 只能看到静态配置。
        started_names = set(registry.server_names())  # 新增代码+DesktopGUIMcpControl：读取 registry 实际管理的 server 名；如果没有这行，配置外 runtime server 无法合并。
        start_errors = registry.start_errors()  # 新增代码+DesktopGUIMcpControl：读取启动错误；如果没有这行，前端看不到 server 为什么失败。
        for server_name in sorted(set(config_by_name) | started_names | set(start_errors)):  # 新增代码+DesktopGUIMcpControl：遍历配置、启动和错误三类 server；如果没有这行，部分失败 server 可能消失。
            try:  # 新增代码+DesktopGUIMcpControl：单独保护资源枚举；如果没有这行，一个 server 的资源错误会阻断其他 server。
                resources.extend(_resource_payload(server_name, item) for item in registry.list_resources(server_name))  # 新增代码+DesktopGUIMcpControl：读取并脱敏资源列表；如果没有这行，资源管理页没有主体数据。
            except Exception as error:  # 新增代码+DesktopGUIMcpControl：捕获资源枚举异常；如果没有这行，异常会冒泡成 500。
                resource_errors[server_name] = _safe_text(error, "MCP resource 读取失败")  # 新增代码+DesktopGUIMcpControl：记录脱敏资源错误；如果没有这行，用户无法知道降级点。
            try:  # 新增代码+DesktopGUIMcpControl：单独保护 prompt 枚举；如果没有这行，一个 server 的 prompt 错误会阻断其他 server。
                prompts.extend(_prompt_payload(server_name, item) for item in registry.list_prompts(server_name))  # 新增代码+DesktopGUIMcpControl：读取并脱敏 prompt 列表；如果没有这行，prompt 管理页没有主体数据。
            except Exception as error:  # 新增代码+DesktopGUIMcpControl：捕获 prompt 枚举异常；如果没有这行，异常会冒泡成 500。
                prompt_errors[server_name] = _safe_text(error, "MCP prompt 读取失败")  # 新增代码+DesktopGUIMcpControl：记录脱敏 prompt 错误；如果没有这行，用户无法知道降级点。
        servers = []  # 新增代码+DesktopGUIMcpControl：准备 server 输出列表；如果没有这行，server 卡片没有容器。
        for server_name in sorted(set(config_by_name) | started_names | set(start_errors)):  # 新增代码+DesktopGUIMcpControl：再次按 server 汇总状态；如果没有这行，GUI 只有集合没有 server 概览。
            server_resources = [item for item in resources if item["server"] == server_name]  # 新增代码+DesktopGUIMcpControl：筛选当前 server 的资源；如果没有这行，resource_count 无法计算。
            server_prompts = [item for item in prompts if item["server"] == server_name]  # 新增代码+DesktopGUIMcpControl：筛选当前 server 的 prompt；如果没有这行，prompt_count 无法计算。
            status, last_error = _server_status(server_name, start_errors, resource_errors, prompt_errors, server_name in started_names)  # 新增代码+DesktopGUIMcpControl：计算当前 server 状态；如果没有这行，前端只能看到裸计数。
            config = config_by_name.get(server_name)  # 新增代码+DesktopGUIMcpControl：读取对应配置；如果没有这行，无法输出 transport 和安全连接摘要。
            servers.append({"name": server_name, "transport": config.transport if config else "runtime", "status": status, "resource_count": len(server_resources), "prompt_count": len(server_prompts), "last_error": last_error, "stream_state": _safe_stream_state(registry.stream_state(server_name)), "config_summary": _safe_config_summary(config) if config else {}, "reuse_module": MCP_CONTROL_REUSE_MODULE})  # 新增代码+DesktopGUIMcpControl：追加 server 汇总卡片数据；如果没有这行，MCP 面板无法渲染 server 行。
    except Exception as error:  # 新增代码+DesktopGUIMcpControl：捕获 registry 总体异常；如果没有这行，桥接端点会直接 500。
        start_errors = {}  # 新增代码+DesktopGUIMcpControl：总体失败时提供空启动错误；如果没有这行，后续 payload 构造会引用未定义变量。
        servers = [{"name": config.name, "transport": config.transport, "status": "failed", "resource_count": 0, "prompt_count": 0, "last_error": _safe_text(error, "MCP registry 读取失败"), "stream_state": {}, "config_summary": _safe_config_summary(config), "reuse_module": MCP_CONTROL_REUSE_MODULE} for config in configs]  # 新增代码+DesktopGUIMcpControl：总体失败时仍返回配置级 server；如果没有这行，用户会以为没有 MCP 配置。
        safe_error = _safe_text(error, "MCP registry 读取失败")  # 新增代码+DesktopGUIMcpControl：保存顶层安全错误；如果没有这行，前端无法展示降级原因。
    finally:  # 新增代码+DesktopGUIMcpControl：确保 registry 关闭；如果没有这行，stdio MCP 子进程可能泄漏。
        registry.close()  # 新增代码+DesktopGUIMcpControl：关闭 MCP registry 和底层连接；如果没有这行，刷新面板会残留进程或连接。
    degraded = bool(safe_error or start_errors or resource_errors or prompt_errors)  # 新增代码+DesktopGUIMcpControl：计算总降级状态；如果没有这行，前端无法显示整体健康灯。
    return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "workspace": str(workspace_path), "config_path": str(workspace_path / "mcp_servers.json"), "generated_at": datetime.now(UTC).isoformat(), "server_count": len(servers), "resource_count": len(resources), "prompt_count": len(prompts), "servers": servers, "resources": resources, "prompts": prompts, "status_degraded": degraded, "safe_error": safe_error, "reuse_module": MCP_CONTROL_REUSE_MODULE}  # 新增代码+DesktopGUIMcpControl：返回完整 MCP 管理 payload；如果没有这行，HTTP route 没有 JSON 响应。
# 新增代码+DesktopGUIMcpControl：函数段结束，build_gui_mcp_inventory_payload 到此结束；如果没有边界说明，初学者不容易看出它只读不执行工具。


def build_gui_mcp_collection_payload(kind: str, workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIMcpControl：函数段开始，按集合名返回 MCP servers/resources/prompts；如果没有这段，三个 endpoint 会重复拼 payload。
    inventory = build_gui_mcp_inventory_payload(workspace)  # 新增代码+DesktopGUIMcpControl：先构建统一 MCP 总览；如果没有这行，集合 endpoint 会和总览数据不一致。
    if kind not in MCP_CONTROL_SUPPORTED_COLLECTIONS:  # 新增代码+DesktopGUIMcpControl：拒绝未知集合名；如果没有这行，拼错路径可能返回误导性空数据。
        return {**inventory, "kind": kind, "status": "unsupported", "data": [], "status_degraded": True, "safe_error": "unsupported MCP collection"}  # 新增代码+DesktopGUIMcpControl：返回结构化 unsupported；如果没有这行，前端拿不到可机读错误。
    return {**inventory, "kind": kind, "status": "ready", "data": inventory[kind]}  # 新增代码+DesktopGUIMcpControl：返回完整总览和当前集合数据；如果没有这行，调用方需要额外请求总览。
# 新增代码+DesktopGUIMcpControl：函数段结束，build_gui_mcp_collection_payload 到此结束；如果没有边界说明，集合 endpoint 逻辑范围不清楚。
