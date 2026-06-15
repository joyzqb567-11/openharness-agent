"""HTTP command bridge 应用层，让外部控制器通过本机 HTTP 调用 agent。"""  # 新增代码+AppSplit: 说明本模块承载 HTTP bridge；若没有这行代码，bridge 排查仍要翻主入口文件。
from __future__ import annotations  # 新增代码+AppSplit: 允许类型注解延迟解析；若没有这行代码，前向引用 server 类型时更容易出错。

import http.server  # 新增代码+AppSplit: 使用标准库 HTTP server 暴露本机 bridge；若没有这行代码，Codex 无法通过 HTTP 控制 agent。
import json  # 新增代码+AppSplit: 解析请求和返回 JSON 响应；若没有这行代码，bridge 无法稳定传输中文 prompt 和 answer。
import threading  # 新增代码+AppSplit: 串行化 agent.run 并支持后台 serve_forever；若没有这行代码，并发请求可能同时修改同一个 agent。
import urllib.parse  # 新增代码+AppSplit: 解析 URL path 并忽略 query；若没有这行代码，/health?x=1 这类路径会误判。
from typing import Any  # 新增代码+AppSplit: 标注 agent 和 JSON payload 的通用类型；若没有这行代码，模块接口不容易理解。

try:  # 新增代码+AppSplit: 优先按包路径导入轮次解析和状态格式化；若没有这行代码，bridge 无法复用 core 配置规则。
    from learning_agent.core.config import format_max_turns_status, parse_max_turns_value  # 新增代码+AppSplit: 导入 max_turns helper；若没有这行代码，HTTP /run 无法解析临时轮次上限。
    from learning_agent.core.resume_loader import ResumeLoader  # 新增代码+StatusAPIV2: 导入恢复加载器供 /resume 端点使用；若没有这行代码，HTTP API 无法返回可审计恢复报告。
    from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+StatusAPI: 导入统一状态事件 store；若没有这行代码，HTTP /events 无法读取真实事件流。
    from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+StatusAPI: 导入统一状态快照聚合器；若没有这行代码，HTTP /status 会和 CLI/SDK 状态分裂。
    import learning_agent.tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 导入工具池名称运行时；若没有这行代码，HTTP bridge 仍会通过 agent.py 薄包装展示工具池。
except ModuleNotFoundError as error:  # 新增代码+AppSplit: 捕获脚本模式下包路径不可用；若没有这行代码，双击 bat 时 bridge 可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.config", "learning_agent.core.resume_loader", "learning_agent.runtime", "learning_agent.runtime.status_events", "learning_agent.runtime.status_snapshot", "learning_agent.tools", "learning_agent.tools.catalog_runtime"}:  # 修改代码+AgentPyPhaseHMcpToolRuntime: 允许 catalog_runtime 路径差异进入 fallback；若没有这行代码，runtime 内部错误会被误吞或脚本模式会失败。
        raise  # 新增代码+AppSplit: 重新抛出真实导入错误；若没有这行代码，配置层问题会被隐藏。
    from core.config import format_max_turns_status, parse_max_turns_value  # 新增代码+AppSplit: 脚本模式从同目录 core 包导入；若没有这行代码，直接运行时 bridge 轮次解析会断开。
    from core.resume_loader import ResumeLoader  # 新增代码+StatusAPIV2: 脚本模式导入恢复加载器；若没有这行代码，bat 入口下 /resume 会失败。
    from runtime.status_events import StatusEventStore  # 新增代码+StatusAPI: 脚本模式导入状态事件 store；若没有这行代码，bat 入口下 /events 会失败。
    from runtime.status_snapshot import build_status_snapshot  # 新增代码+StatusAPI: 脚本模式导入状态快照聚合器；若没有这行代码，bat 入口下 /status 会失败。
    import tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入工具池名称运行时；若没有这行代码，bat 入口 HTTP bridge visible_tools 会断开。


class LearningAgentCommandBridgeServer(http.server.ThreadingHTTPServer):  # 新增代码+AppSplit: 保存 HTTP bridge 的 agent、token 和运行配置；若没有这行代码，handler 无法访问被控制的 agent。
    def __init__(self, server_address: tuple[str, int], agent: Any, token: str = "", max_turns: int | None = None) -> None:  # 新增代码+AppSplit: 初始化 bridge server；若没有这行代码，无法把 agent 注入 HTTP 服务。
        super().__init__(server_address, LearningAgentCommandBridgeHandler)  # 新增代码+AppSplit: 用标准库 ThreadingHTTPServer 启动 handler；若没有这行代码，bridge 不能接收请求。
        self.agent = agent  # 新增代码+AppSplit: 保存可被 HTTP 控制的 agent 实例；若没有这行代码，POST /run 无法调用 agent.run。
        self.token = token  # 新增代码+AppSplit: 保存可选认证 token；若没有这行代码，handler 无法判断请求是否被授权。
        self.max_turns = max_turns  # 新增代码+AppSplit: 保存 bridge 默认模型-工具循环上限；若没有这行代码，HTTP run 不能继承 CLI 配置。
        self.agent_lock = threading.Lock()  # 新增代码+AppSplit: 串行化 agent.run 调用；若没有这行代码，并发 HTTP 请求可能同时修改同一个 agent 状态。


class LearningAgentCommandBridgeHandler(http.server.BaseHTTPRequestHandler):  # 新增代码+AppSplit: 处理 HTTP command bridge 请求；若没有这行代码，Codex 无法通过 HTTP 控制 agent。
    server: LearningAgentCommandBridgeServer  # 新增代码+AppSplit: 给类型检查器说明 self.server 的真实类型；若没有这行代码，后续访问 agent/token 字段不清楚。

    def log_message(self, format: str, *args: Any) -> None:  # 新增代码+AppSplit: 关闭默认 HTTP 访问日志；若没有这行代码，JSON 输出会混入噪声。
        return  # 新增代码+AppSplit: 静默处理标准库日志；若没有这行代码，自动化测试和 Codex 接收可能被日志污染。

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:  # 新增代码+AppSplit: 统一返回 JSON 响应；若没有这行代码，每个端点会重复 header 逻辑。
        raw_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")  # 新增代码+AppSplit: 把响应对象编码成 UTF-8 JSON；若没有这行代码，中文回答无法稳定返回。
        self.send_response(status)  # 新增代码+AppSplit: 写入 HTTP 状态码；若没有这行代码，客户端不知道请求成功还是失败。
        self.send_header("Content-Type", "application/json; charset=utf-8")  # 新增代码+AppSplit: 声明 JSON 响应类型；若没有这行代码，客户端可能按普通文本解析。
        self.send_header("Content-Length", str(len(raw_body)))  # 新增代码+AppSplit: 声明响应长度；若没有这行代码，HTTP 客户端可能等待连接关闭。
        self.send_header("Cache-Control", "no-store")  # 新增代码+AppSplit: 禁止缓存控制结果；若没有这行代码，调试客户端可能复用旧响应。
        self.end_headers()  # 新增代码+AppSplit: 结束 header 区；若没有这行代码，响应体不会被客户端正确读取。
        self.wfile.write(raw_body)  # 新增代码+AppSplit: 写出 JSON 响应体；若没有这行代码，客户端收不到正文。

    def _visible_tools(self) -> list[str]:  # 新增代码+AppSplit: 读取当前模型可见工具名；若没有这行代码，health/run 响应无法展示 Tool Pool。
        return catalog_runtime_from_tools.tool_schema_names(self.server.agent)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 直连 catalog_runtime 读取当前模型可见工具名；若没有这行代码，bridge 仍会通过 agent.py 薄包装展示工具池。

    def _is_authorized(self) -> bool:  # 新增代码+AppSplit: 判断当前请求是否通过可选 token 校验；若没有这行代码，POST /run 无法启用简单保护。
        if not self.server.token:  # 新增代码+AppSplit: 未配置 token 时允许本机调试请求；若没有这行代码，默认 bridge 会难以快速试用。
            return True  # 新增代码+AppSplit: 返回允许；若没有这行代码，未配置 token 仍会被拒绝。
        auth_header = self.headers.get("Authorization", "")  # 新增代码+AppSplit: 读取标准 Authorization header；若没有这行代码，Bearer token 无法使用。
        x_token = self.headers.get("X-Learning-Agent-Token", "")  # 新增代码+AppSplit: 读取简化 token header；若没有这行代码，脚本客户端需要拼 Bearer 格式。
        return auth_header == f"Bearer {self.server.token}" or x_token == self.server.token  # 新增代码+AppSplit: 接受两种 token 写法；若没有这行代码，认证判断不会生效。

    def _read_json_body(self) -> dict[str, Any] | str:  # 新增代码+AppSplit: 读取并解析 JSON 请求体；若没有这行代码，POST /run 无法获得 prompt。
        raw_length = self.headers.get("Content-Length", "0")  # 新增代码+AppSplit: 读取请求体长度；若没有这行代码，handler 不知道该读多少字节。
        try:  # 新增代码+AppSplit: 捕获非法 Content-Length；若没有这行代码，错误 header 会触发 traceback。
            length = int(raw_length)  # 新增代码+AppSplit: 把长度转成整数；若没有这行代码，rfile.read 无法使用字符串长度。
        except ValueError:  # 新增代码+AppSplit: 处理非数字长度；若没有这行代码，错误请求无法返回 400。
            return "Content-Length 必须是整数。"  # 新增代码+AppSplit: 返回可读错误；若没有这行代码，客户端不知道请求坏在哪里。
        if length <= 0:  # 新增代码+AppSplit: 检查请求体是否为空；若没有这行代码，空 body 会被当成 JSON 解析错误。
            return "请求体不能为空。"  # 新增代码+AppSplit: 返回缺正文错误；若没有这行代码，客户端难以修正请求。
        if length > 1_000_000:  # 新增代码+AppSplit: 限制桥接请求体大小；若没有这行代码，大请求可能占用过多内存。
            return "请求体过大，最大 1000000 字节。"  # 新增代码+AppSplit: 返回大小限制错误；若没有这行代码，客户端不知道上限。
        raw_body = self.rfile.read(length)  # 新增代码+AppSplit: 读取请求体字节；若没有这行代码，JSON 无法解析。
        try:  # 新增代码+AppSplit: 捕获 JSON 解析失败；若没有这行代码，坏 JSON 会抛出 traceback。
            payload = json.loads(raw_body.decode("utf-8"))  # 新增代码+AppSplit: 用 UTF-8 解码并解析 JSON；若没有这行代码，中文 prompt 无法稳定传入。
        except (UnicodeDecodeError, json.JSONDecodeError) as error:  # 新增代码+AppSplit: 处理编码或 JSON 格式错误；若没有这行代码，客户端看不到具体格式问题。
            return f"请求体必须是 UTF-8 JSON：{error}"  # 新增代码+AppSplit: 返回可读解析错误；若没有这行代码，调试 HTTP 客户端更困难。
        if not isinstance(payload, dict):  # 新增代码+AppSplit: 顶层 JSON 必须是对象；若没有这行代码，数组或字符串会让字段读取语义不清。
            return "请求 JSON 顶层必须是对象。"  # 新增代码+AppSplit: 返回结构错误；若没有这行代码，客户端不知道该传 {"prompt": "..."}。
        return payload  # 新增代码+AppSplit: 返回解析后的请求对象；若没有这行代码，POST /run 无法继续。

    def do_GET(self) -> None:  # 新增代码+AppSplit: 处理 HTTP GET 请求；若没有这行代码，Codex 无法探活 bridge。
        parsed_url = urllib.parse.urlparse(self.path)  # 修改代码+StatusAPI: 同时解析 path 和 query；若没有这行代码，/events?since_sequence=... 无法读取参数。
        path = parsed_url.path  # 修改代码+StatusAPI: 提取 URL path；若没有这行代码，GET 路由无法判断端点。
        query = urllib.parse.parse_qs(parsed_url.query)  # 新增代码+StatusAPI: 解析 query 参数；若没有这行代码，事件流无法支持增量读取和 limit。
        if path in {"/status", "/v1/status"}:  # 新增代码+StatusAPI: 支持状态快照端点；若没有这行代码，外部 agent 只能读本地文件。
            if not self._is_authorized():  # 新增代码+StatusAPI: token 配置后也保护状态数据；若没有这行代码，任务路径和输出可能被未授权读取。
                self._send_json(401, {"ok": False, "error": "未授权：请提供 Bearer token 或 X-Learning-Agent-Token。"})  # 新增代码+StatusAPI: 返回 JSON 认证错误；若没有这行代码，客户端不知道如何修正请求。
                return  # 新增代码+StatusAPI: 未授权时停止处理；若没有这行代码，仍可能继续返回状态。
            snapshot = build_status_snapshot(self.server.agent.workspace)  # 新增代码+StatusAPI: 从同一工作区读取统一状态快照；若没有这行代码，HTTP /status 会和 CLI/SDK 事实源不同。
            self._send_json(200, {"ok": True, "snapshot": snapshot})  # 新增代码+StatusAPI: 返回结构化状态快照；若没有这行代码，外部 agent 无法机器解析 run/task/session 状态。
            return  # 新增代码+StatusAPI: 状态端点响应完成后停止；若没有这行代码，后续 health 逻辑会二次发送响应。
        if path in {"/runs", "/v1/runs"}:  # 新增代码+StatusAPIV2: 支持单独读取 run 列表；若没有这行代码，外部 agent 只能下载完整 snapshot 再自己拆。
            if not self._is_authorized():  # 新增代码+StatusAPIV2: token 配置后保护 run 状态；若没有这行代码，任务 prompt 和阶段状态可能被未授权读取。
                self._send_json(401, {"ok": False, "error": "未授权：请提供 Bearer token 或 X-Learning-Agent-Token。"})  # 新增代码+StatusAPIV2: 返回 JSON 认证错误；若没有这行代码，客户端不知道如何修正请求。
                return  # 新增代码+StatusAPIV2: 未授权时停止处理；若没有这行代码，仍可能继续返回 run 数据。
            snapshot = build_status_snapshot(self.server.agent.workspace)  # 新增代码+StatusAPIV2: 复用统一状态快照获取 runs；若没有这行代码，/runs 会和 /status 使用不同事实源。
            self._send_json(200, {"ok": True, "runs": snapshot.get("runs", []), "current_run": snapshot.get("current_run", {})})  # 新增代码+StatusAPIV2: 返回 run 列表和当前 run；若没有这行代码，外部 agent 无法快速定位当前任务。
            return  # 新增代码+StatusAPIV2: run 端点响应完成后停止；若没有这行代码，后续路由会二次发送响应。
        if path in {"/browser/runs", "/v1/browser/runs"}:  # 新增代码+BrowserStatusStage11: 支持单独读取 browser runtime run；若没有这行代码，外部 UI/SDK 只能解析完整 snapshot。
            if not self._is_authorized():  # 新增代码+BrowserStatusStage11: token 配置后保护浏览器状态；若没有这行代码，页面 URL 和动作摘要可能被未授权读取。
                self._send_json(401, {"ok": False, "error": "未授权：请提供 Bearer token 或 X-Learning-Agent-Token。"})  # 新增代码+BrowserStatusStage11: 返回 JSON 认证错误；若没有这行代码，客户端不知道如何修正请求。
                return  # 新增代码+BrowserStatusStage11: 未授权时停止处理；若没有这行代码，仍可能继续返回浏览器状态。
            snapshot = build_status_snapshot(self.server.agent.workspace)  # 新增代码+BrowserStatusStage11: 使用统一快照读取 browser 区块；若没有这行代码，HTTP API 会和 CLI/SDK 分裂。
            browser = snapshot.get("browser", {})  # 新增代码+BrowserStatusStage11: 提取浏览器状态区块；若没有这行代码，响应需要暴露完整快照。
            self._send_json(200, {"ok": True, "browser": browser, "runs": browser.get("runs", []) if isinstance(browser, dict) else []})  # 新增代码+BrowserStatusStage11: 返回浏览器 run 和摘要；若没有这行代码，外部 agent 无法快速定位浏览器任务。
            return  # 新增代码+BrowserStatusStage11: browser runs 端点响应完成后停止；若没有这行代码，后续路由会二次发送响应。
        if path in {"/browser/events", "/v1/browser/events"}:  # 新增代码+BrowserStatusStage11: 支持单独读取 browser runtime events；若没有这行代码，UI watcher 不能轻量观察浏览器动作。
            if not self._is_authorized():  # 新增代码+BrowserStatusStage11: token 配置后保护浏览器事件；若没有这行代码，页面动作事件可能被未授权读取。
                self._send_json(401, {"ok": False, "error": "未授权：请提供 Bearer token 或 X-Learning-Agent-Token。"})  # 新增代码+BrowserStatusStage11: 返回 JSON 认证错误；若没有这行代码，客户端不知道如何修正请求。
                return  # 新增代码+BrowserStatusStage11: 未授权时停止处理；若没有这行代码，仍可能继续返回事件。
            snapshot = build_status_snapshot(self.server.agent.workspace)  # 新增代码+BrowserStatusStage11: 使用统一快照读取 browser 事件尾巴；若没有这行代码，HTTP API 会形成第二套读取逻辑。
            browser = snapshot.get("browser", {})  # 新增代码+BrowserStatusStage11: 提取 browser 区块；若没有这行代码，响应需要暴露完整快照。
            self._send_json(200, {"ok": True, "events": browser.get("events", []) if isinstance(browser, dict) else []})  # 新增代码+BrowserStatusStage11: 返回浏览器事件列表；若没有这行代码，外部 watcher 拿不到动作流。
            return  # 新增代码+BrowserStatusStage11: browser events 端点响应完成后停止；若没有这行代码，后续路由会二次发送响应。
        if path in {"/browser/providers", "/v1/browser/providers"}:  # 新增代码+ChromeExtensionStage8: 支持单独读取浏览器 provider 状态；若没有这行代码，外部 UI/SDK 只能解析完整 snapshot。
            if not self._is_authorized():  # 新增代码+ChromeExtensionStage8: token 配置后保护 provider 状态；若没有这行代码，页面 URL 和插件状态可能被未授权读取。
                self._send_json(401, {"ok": False, "error": "未授权：请提供 Bearer token 或 X-Learning-Agent-Token。"})  # 新增代码+ChromeExtensionStage8: 返回 JSON 认证错误；若没有这行代码，客户端不知道如何修正请求。
                return  # 新增代码+ChromeExtensionStage8: 未授权时停止处理；若没有这行代码，仍可能继续返回 provider 状态。
            snapshot = build_status_snapshot(self.server.agent.workspace)  # 新增代码+ChromeExtensionStage8: 使用统一快照读取 provider 状态；若没有这行代码，HTTP API 会和 CLI/SDK 分裂。
            browser = snapshot.get("browser", {}) if isinstance(snapshot.get("browser", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 提取 browser 区块；若没有这行代码，坏快照会触发异常。
            provider_status = browser.get("provider_status", {}) if isinstance(browser.get("provider_status", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 提取 provider_status；若没有这行代码，响应需要暴露完整快照。
            self._send_json(200, {"ok": True, "provider_status": provider_status, "browser": browser})  # 新增代码+ChromeExtensionStage8: 返回 provider 状态和 browser 摘要；若没有这行代码，外部 agent 无法轻量判断插件是否可用。
            return  # 新增代码+ChromeExtensionStage8: provider 端点响应完成后停止；若没有这行代码，后续路由会二次发送响应。
        if path in {"/sessions", "/v1/sessions"}:  # 新增代码+StatusAPIV2: 支持单独读取 session 列表；若没有这行代码，外部 agent 不容易发现可 resume 的会话。
            if not self._is_authorized():  # 新增代码+StatusAPIV2: token 配置后保护 session 列表；若没有这行代码，会话 id 和历史任务信息可能泄露。
                self._send_json(401, {"ok": False, "error": "未授权：请提供 Bearer token 或 X-Learning-Agent-Token。"})  # 新增代码+StatusAPIV2: 返回 JSON 认证错误；若没有这行代码，客户端不知道如何修正请求。
                return  # 新增代码+StatusAPIV2: 未授权时停止处理；若没有这行代码，仍可能继续返回 session 数据。
            snapshot = build_status_snapshot(self.server.agent.workspace)  # 新增代码+StatusAPIV2: 复用统一状态快照获取 sessions；若没有这行代码，/sessions 会和 /status 分裂。
            self._send_json(200, {"ok": True, "sessions": snapshot.get("sessions", []), "resume": snapshot.get("resume", {})})  # 新增代码+StatusAPIV2: 返回 session 列表和最新恢复状态；若没有这行代码，外部 agent 无法判断恢复风险。
            return  # 新增代码+StatusAPIV2: session 端点响应完成后停止；若没有这行代码，后续路由会二次发送响应。
        if path in {"/resume", "/v1/resume"}:  # 新增代码+StatusAPIV2: 支持按 session_id 读取恢复上下文和 repair report；若没有这行代码，外部 agent 只能调用模型工具或直接读文件。
            if not self._is_authorized():  # 新增代码+StatusAPIV2: token 配置后保护恢复上下文；若没有这行代码，历史 prompt 和工具输出摘要可能泄露。
                self._send_json(401, {"ok": False, "error": "未授权：请提供 Bearer token 或 X-Learning-Agent-Token。"})  # 新增代码+StatusAPIV2: 返回 JSON 认证错误；若没有这行代码，客户端不知道如何修正请求。
                return  # 新增代码+StatusAPIV2: 未授权时停止处理；若没有这行代码，仍可能继续读取恢复上下文。
            session_id = query.get("session_id", [""])[0].strip()  # 新增代码+StatusAPIV2: 从 query 读取目标 session_id；若没有这行代码，/resume 不知道恢复哪个会话。
            if not session_id:  # 新增代码+StatusAPIV2: 检查 session_id 是否为空；若没有这行代码，空请求会读到无意义路径。
                self._send_json(400, {"ok": False, "error": "缺少 session_id query 参数。"})  # 新增代码+StatusAPIV2: 返回缺参错误；若没有这行代码，客户端难以修正请求。
                return  # 新增代码+StatusAPIV2: 缺参后停止处理；若没有这行代码，后续会继续读取空 session。
            resume_context = ResumeLoader(self.server.agent.workspace / "memory" / "sessions").load(session_id)  # 新增代码+StatusAPIV2: 使用 ResumeLoader v2 加载恢复上下文；若没有这行代码，HTTP API 不会包含 repair report。
            self._send_json(200, {"ok": True, "resume": resume_context.to_dict()})  # 新增代码+StatusAPIV2: 返回结构化恢复上下文；若没有这行代码，外部 agent 无法机器解析恢复风险。
            return  # 新增代码+StatusAPIV2: resume 端点响应完成后停止；若没有这行代码，后续路由会二次发送响应。
        if path in {"/events", "/v1/events"}:  # 新增代码+StatusAPI: 支持状态事件尾部端点；若没有这行代码，外部 watcher 无法增量观察 agent。
            if not self._is_authorized():  # 新增代码+StatusAPI: token 配置后保护事件流；若没有这行代码，运行事件可能被未授权读取。
                self._send_json(401, {"ok": False, "error": "未授权：请提供 Bearer token 或 X-Learning-Agent-Token。"})  # 新增代码+StatusAPI: 返回 JSON 认证错误；若没有这行代码，客户端不知道如何修正请求。
                return  # 新增代码+StatusAPI: 未授权时停止处理；若没有这行代码，仍可能继续返回事件。
            since_raw = query.get("since_sequence", [""])[0]  # 新增代码+StatusAPI: 读取增量起点参数；若没有这行代码，外部 SDK 只能每次拉全量事件。
            limit_raw = query.get("limit", ["50"])[0]  # 新增代码+StatusAPI: 读取事件数量限制；若没有这行代码，长事件流可能一次返回过多。
            try:  # 新增代码+StatusAPI: 捕获非法 query 数字；若没有这行代码，坏参数会变成 500。
                since_sequence = int(since_raw) if since_raw else None  # 新增代码+StatusAPI: 把 since_sequence 转成整数或 None；若没有这行代码，事件 store 无法按序过滤。
                limit = int(limit_raw) if limit_raw else 50  # 新增代码+StatusAPI: 把 limit 转成整数并默认 50；若没有这行代码，事件端点缺少稳定默认值。
            except ValueError as error:  # 新增代码+StatusAPI: 处理非整数 query；若没有这行代码，客户端拿不到清楚参数错误。
                self._send_json(400, {"ok": False, "error": f"events query 参数必须是整数：{error}"})  # 新增代码+StatusAPI: 返回 JSON 参数错误；若没有这行代码，坏请求不可机器解析。
                return  # 新增代码+StatusAPI: 参数错误后停止；若没有这行代码，后续会用坏参数读取事件。
            event_store = StatusEventStore(self.server.agent.workspace / "memory" / "status")  # 新增代码+StatusAPI: 打开统一状态事件 store；若没有这行代码，/events 没有真实数据源。
            events = [event.to_dict() for event in event_store.list_events(since_sequence=since_sequence, limit=limit)]  # 新增代码+StatusAPI: 读取并序列化事件列表；若没有这行代码，HTTP 响应无法返回 JSON 事件。
            requested_event_types = {item.strip() for item in query.get("event_types", [""])[0].split(",") if item.strip()}  # 新增代码+StatusAPIV2: 支持逗号分隔的事件类型过滤；若没有这行代码，watcher 只能拉全量事件再本地筛选。
            single_event_type = query.get("event_type", [""])[0].strip()  # 新增代码+StatusAPIV2: 支持单个 event_type query；若没有这行代码，简单过滤请求写法不方便。
            if single_event_type:  # 新增代码+StatusAPIV2: 如果传了单个事件类型；若没有这行代码，event_type 参数不会生效。
                requested_event_types.add(single_event_type)  # 新增代码+StatusAPIV2: 合并单个事件类型到过滤集合；若没有这行代码，单类型过滤会被忽略。
            if requested_event_types:  # 新增代码+StatusAPIV2: 只有传过滤条件时才过滤；若没有这行代码，默认 /events 会错误返回空列表。
                events = [event for event in events if str(event.get("event_type", "")) in requested_event_types]  # 新增代码+StatusAPIV2: 过滤目标事件类型；若没有这行代码，HTTP watcher 会收到大量噪声。
            self._send_json(200, {"ok": True, "events": events, "since_sequence": since_sequence, "limit": limit, "event_types": sorted(requested_event_types)})  # 修改代码+StatusAPIV2: 返回增量事件和过滤条件；若没有这行代码，外部 watcher 无法确认服务端过滤是否生效。
            return  # 新增代码+StatusAPI: 事件端点响应完成后停止；若没有这行代码，后续 health 逻辑会二次发送响应。
        if path not in {"/health", "/v1/health"}:  # 新增代码+AppSplit: 只支持健康检查路径；若没有这行代码，未知 GET 可能被误当成功。
            self._send_json(404, {"ok": False, "error": "未知 GET 路径。"})  # 新增代码+AppSplit: 返回 JSON 404；若没有这行代码，客户端会收到默认 HTML 错误页。
            return  # 新增代码+AppSplit: 停止处理未知路径；若没有这行代码，后续仍会发送第二个响应。
        snapshot = build_status_snapshot(self.server.agent.workspace)  # 新增代码+StatusAPIV2: health 也读取统一快照的健康区块；若没有这行代码，/health 只能说明进程活着但不知道状态风险。
        payload = {"ok": True, "agent": "learning_agent", "workspace": str(self.server.agent.workspace), "visible_tools": self._visible_tools(), "health": snapshot.get("health", {}), "current_run": snapshot.get("current_run", {})}  # 修改代码+StatusAPIV2: 构造带健康状态的探活信息；若没有这行代码，外部 agent 无法快速判断运行是否有警告。
        self._send_json(200, payload)  # 新增代码+AppSplit: 返回探活 JSON；若没有这行代码，HTTP 探活没有正文。

    def do_POST(self) -> None:  # 新增代码+AppSplit: 处理 HTTP POST 请求；若没有这行代码，Codex 无法下发运行命令。
        path = urllib.parse.urlparse(self.path).path  # 新增代码+AppSplit: 提取 URL path；若没有这行代码，带 query 的路径无法识别。
        if path not in {"/run", "/command", "/v1/run", "/v1/command"}:  # 新增代码+AppSplit: 支持 run/command 两组路径；若没有这行代码，外部控制器路径兼容性较差。
            self._send_json(404, {"ok": False, "error": "未知 POST 路径。"})  # 新增代码+AppSplit: 返回 JSON 404；若没有这行代码，客户端会收到 HTML 错误页。
            return  # 新增代码+AppSplit: 停止未知路径处理；若没有这行代码，后续会继续解析 body。
        if not self._is_authorized():  # 新增代码+AppSplit: 检查可选 token；若没有这行代码，配置 token 后仍无法保护 POST /run。
            self._send_json(401, {"ok": False, "error": "未授权：请提供 Bearer token 或 X-Learning-Agent-Token。"})  # 新增代码+AppSplit: 返回 JSON 认证错误；若没有这行代码，客户端不知道如何修正请求。
            return  # 新增代码+AppSplit: 认证失败立即停止；若没有这行代码，未授权请求仍可能执行 agent。
        payload_or_error = self._read_json_body()  # 新增代码+AppSplit: 读取 JSON 请求体；若没有这行代码，run 端点拿不到 prompt。
        if isinstance(payload_or_error, str):  # 新增代码+AppSplit: 判断读取结果是否为错误文本；若没有这行代码，错误字符串会被当成 dict。
            self._send_json(400, {"ok": False, "error": payload_or_error})  # 新增代码+AppSplit: 返回 JSON 400；若没有这行代码，坏请求无法被机器解析。
            return  # 新增代码+AppSplit: 停止坏请求处理；若没有这行代码，后续会访问字符串字段。
        prompt = str(payload_or_error.get("prompt", "")).strip()  # 新增代码+AppSplit: 读取并清理 prompt 字段；若没有这行代码，agent.run 不知道用户任务。
        if not prompt:  # 新增代码+AppSplit: 检查 prompt 是否为空；若没有这行代码，空任务会进入模型造成无意义调用。
            self._send_json(400, {"ok": False, "error": "缺少 prompt 字段。"})  # 新增代码+AppSplit: 返回缺参错误；若没有这行代码，客户端难以修正请求。
            return  # 新增代码+AppSplit: 停止空 prompt 请求；若没有这行代码，仍会调用 agent.run。
        try:  # 新增代码+AppSplit: 捕获 max_turns 配置错误和 agent 运行异常；若没有这行代码，bridge 会用 traceback 断开连接。
            max_turns = parse_max_turns_value(payload_or_error["max_turns"], "HTTP command bridge max_turns") if "max_turns" in payload_or_error else self.server.max_turns  # 新增代码+AppSplit: 请求可覆盖默认轮次；若没有这行代码，外部调试无法临时限制单次调用。
            with self.server.agent_lock:  # 新增代码+AppSplit: 串行执行 agent.run；若没有这行代码，并发请求可能同时修改 messages/logs/工具状态。
                answer = self.server.agent.run(prompt, max_turns=max_turns)  # 新增代码+AppSplit: 调用真实 agent 主循环；若没有这行代码，bridge 只会探活不能控制 agent。
        except ValueError as error:  # 新增代码+AppSplit: 处理 max_turns 解析错误；若没有这行代码，错误参数会变成 500。
            self._send_json(400, {"ok": False, "error": str(error)})  # 新增代码+AppSplit: 返回可读参数错误；若没有这行代码，客户端不知道哪里填错。
            return  # 新增代码+AppSplit: 参数错误后停止；若没有这行代码，可能继续发送成功响应。
        except Exception as error:  # 新增代码+AppSplit: 兜底处理 agent 运行异常；若没有这行代码，HTTP 连接可能中断且没有 JSON 错误。
            self._send_json(500, {"ok": False, "error": f"agent 运行失败：{error}"})  # 新增代码+AppSplit: 返回 JSON 500；若没有这行代码，Codex 无法稳定接收失败原因。
            return  # 新增代码+AppSplit: 运行失败后停止；若没有这行代码，可能继续发送成功响应。
        result_payload = {"ok": True, "answer": answer, "workspace": str(self.server.agent.workspace), "visible_tools": self._visible_tools(), "max_turns": max_turns}  # 新增代码+AppSplit: 构造 run 成功结果；若没有这行代码，Codex 收不到 answer 和调试元数据。
        self._send_json(200, result_payload)  # 新增代码+AppSplit: 返回 run JSON；若没有这行代码，POST /run 没有成功响应。


def create_command_bridge_server(agent: Any, host: str = "127.0.0.1", port: int = 8765, token: str = "", max_turns: int | None = None) -> LearningAgentCommandBridgeServer:  # 新增代码+AppSplit: 创建可测试和可启动的 HTTP bridge server；若没有这行代码，CLI 和单测都要重复 server 构造。
    return LearningAgentCommandBridgeServer((host, port), agent=agent, token=token, max_turns=max_turns)  # 新增代码+AppSplit: 返回绑定后的 bridge server；若没有这行代码，调用方拿不到可 serve_forever 的对象。


def serve_command_bridge(bridge_server: LearningAgentCommandBridgeServer, visible_tools: list[str], max_turns: int | None, prompt_soft_token_limit: int) -> None:  # 新增代码+AppSplit: 运行 HTTP bridge 并打印人类可读启动信息；若没有这行代码，CLI 会继续手写 bridge 生命周期。
    bridge_host, bridge_port = bridge_server.server_address  # 新增代码+AppSplit: 读取实际绑定地址和端口；若没有这行代码，端口 0 场景无法告诉用户真实端口。
    print("模型-工具循环轮次策略：" + format_max_turns_status(max_turns))  # 新增代码+AppSplit: bridge 启动时显示轮次策略；若没有这行代码，调试者不知道 HTTP run 默认上限。
    print(f"提示词软预算：约 {prompt_soft_token_limit} tokens")  # 新增代码+AppSplit: bridge 启动时显示 prompt 预算；若没有这行代码，长上下文调试缺少关键参数。
    print("模型当前可见工具：" + ", ".join(visible_tools))  # 新增代码+AppSplit: bridge 启动时显示 Tool Pool；若没有这行代码，用户无法确认四原子工具面。
    print(f"HTTP command bridge 已启动：http://{bridge_host}:{bridge_port}")  # 新增代码+AppSplit: 打印 bridge URL；若没有这行代码，Codex 或用户不知道连接地址。
    print("HTTP command bridge 接口：GET /health，GET /status，GET /events，GET /browser/runs，GET /browser/events，GET /browser/providers，POST /run。按 Ctrl+C 退出。")  # 修改代码+ChromeExtensionStage8: 打印 provider 状态端点；若没有这行代码，用户和外部 agent 不知道插件/provider 可观察状态。
    try:  # 新增代码+AppSplit: 捕获 Ctrl+C 退出；若没有这行代码，用户停止 bridge 时可能看到 traceback。
        bridge_server.serve_forever()  # 新增代码+AppSplit: 开始处理 HTTP 请求；若没有这行代码，bridge 命令启动后立即退出。
    except KeyboardInterrupt:  # 新增代码+AppSplit: 处理用户中断；若没有这行代码，Ctrl+C 会显示异常堆栈。
        print("\nHTTP command bridge 已停止。")  # 新增代码+AppSplit: 给出停止提示；若没有这行代码，用户不知道是否正常退出。
    finally:  # 新增代码+AppSplit: 无论如何都释放 server socket；若没有这行代码，端口可能短时间占用。
        bridge_server.server_close()  # 新增代码+AppSplit: 关闭监听 socket；若没有这行代码，端口资源可能泄露。
