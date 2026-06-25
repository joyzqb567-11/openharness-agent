"""Desktop GUI bridge for the OpenHarness local desktop shell."""  # 新增代码+DesktopGUIBridge: 说明本模块只服务桌面 GUI；如果没有这行代码，维护者容易把它和通用 HTTP bridge 混淆。
from __future__ import annotations  # 新增代码+DesktopGUIBridge: 延迟解析类型注解；如果没有这行代码，后续类型引用更容易受导入顺序影响。

import http.server  # 新增代码+DesktopGUIBridge: 使用标准库 HTTP server；如果没有这行代码，GUI bridge 需要引入新依赖。
import json  # 新增代码+DesktopGUIBridge: 序列化 HTTP JSON 响应；如果没有这行代码，前端无法解析结构化数据。
import secrets  # 新增代码+DesktopGUIBridge: 生成本地 bridge 随机 token；如果没有这行代码，默认启动会缺少认证保护。
import urllib.parse  # 新增代码+DesktopGUIBridge: 解析 URL path 和 query；如果没有这行代码，事件轮询参数无法读取。
from pathlib import Path  # 新增代码+DesktopGUIBridge: 使用 Path 规范化工作区；如果没有这行代码，字符串路径处理容易分裂。
from typing import Any  # 新增代码+DesktopGUIBridge: 描述 JSON payload 的通用值；如果没有这行代码，接口类型边界不清楚。

from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+DesktopGUIBridge: 复用统一状态事实源；如果没有这行代码，GUI 会和 CLI/SDK 状态分裂。


GUI_SCHEMA_VERSION = 1  # 新增代码+DesktopGUIBridge: 固定 GUI bridge 协议版本；如果没有这行代码，前端无法判断响应兼容性。
GUI_TOKEN_HEADER = "X-OpenHarness-Desktop-Token"  # 新增代码+DesktopGUIBridge: 固定桌面 bridge token header；如果没有这行代码，前后端认证字段会分裂。
GUI_ALLOWED_ORIGINS = {"", "null", "file://", "http://127.0.0.1:5177"}  # 新增代码+DesktopGUIBridge: 固定第一版允许来源；如果没有这行代码，本机恶意网页可能跨源调用 bridge。


def build_gui_bootstrap_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIBridge: 函数段开始，生成 GUI 启动首屏数据；如果没有这段函数，桌面壳需要调用多个后端端点拼状态。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUIBridge: 规范化工作区路径；如果没有这行代码，相对路径会导致前端项目身份不稳定。
    snapshot = build_status_snapshot(workspace_path)  # 新增代码+DesktopGUIBridge: 读取统一状态快照；如果没有这行代码，GUI 没有 run/task/session/browser 数据。
    return {  # 新增代码+DesktopGUIBridge: 返回稳定 JSON 对象；如果没有这行代码，前端无法渲染启动页。
        "ok": True,  # 新增代码+DesktopGUIBridge: 标记请求成功；如果没有这行代码，前端要靠异常猜测状态。
        "workspace": str(workspace_path),  # 新增代码+DesktopGUIBridge: 返回当前项目路径；如果没有这行代码，侧栏无法显示项目身份。
        "app": {"name": "OpenHarness Desktop", "schema_version": GUI_SCHEMA_VERSION},  # 新增代码+DesktopGUIBridge: 返回应用名和协议版本；如果没有这行代码，前端无法做兼容判断。
        "snapshot": snapshot,  # 新增代码+DesktopGUIBridge: 返回统一状态快照；如果没有这行代码，首屏看不到任务和会话。
        "feature_flags": {  # 新增代码+DesktopGUIBridge: 返回能力开关；如果没有这行代码，前端无法按后端能力显示 UI。
            "chat_run": True,  # 新增代码+DesktopGUIBridge: 声明可发起聊天运行；如果没有这行代码，输入框无法判断是否可用。
            "event_polling": True,  # 新增代码+DesktopGUIBridge: 声明当前使用事件轮询；如果没有这行代码，前端无法启动 watcher。
            "browser_panel": True,  # 新增代码+DesktopGUIBridge: 声明可显示浏览器状态；如果没有这行代码，浏览器面板会误隐藏。
            "computer_use_panel": True,  # 新增代码+DesktopGUIBridge: 声明可显示 Computer Use 状态；如果没有这行代码，权限面板会误隐藏。
            "streaming": False,  # 新增代码+DesktopGUIBridge: 第一阶段不声明真实流式输出；如果没有这行代码，前端可能误等 SSE。
        },  # 新增代码+DesktopGUIBridge: feature_flags 对象结束；如果没有这行代码，Python 语法不完整。
    }  # 新增代码+DesktopGUIBridge: bootstrap payload 结束；如果没有这行代码，函数没有返回值。
# 新增代码+DesktopGUIBridge: 函数段结束，build_gui_bootstrap_payload 到此结束；如果没有这个边界说明，用户不容易看出它只负责首屏数据。


class DesktopGuiBridgeServer(http.server.ThreadingHTTPServer):  # 新增代码+DesktopGUIBridge: 类段开始，保存 GUI bridge 工作区和 token；如果没有这个类，handler 无法访问项目状态。
    def __init__(self, server_address: tuple[str, int], workspace: str | Path, token: str = "") -> None:  # 新增代码+DesktopGUIBridge: 初始化 server；如果没有这段函数，外部无法注入工作区。
        super().__init__(server_address, DesktopGuiBridgeHandler)  # 新增代码+DesktopGUIBridge: 绑定 handler；如果没有这行代码，server 不会处理 GUI 路由。
        self.workspace = Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUIBridge: 保存规范化工作区；如果没有这行代码，所有端点都不知道项目位置。
        self.token = str(token or secrets.token_hex(32))  # 新增代码+DesktopGUIBridge: 保存或生成启动 token；如果没有这行代码，本地 bridge 默认没有认证保护。
    # 新增代码+DesktopGUIBridge: 函数段结束，DesktopGuiBridgeServer.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 server 只保存共享状态。


class DesktopGuiBridgeHandler(http.server.BaseHTTPRequestHandler):  # 新增代码+DesktopGUIBridge: 类段开始，处理 GUI bridge HTTP 请求；如果没有这个类，Electron 前端没有后端入口。
    server: DesktopGuiBridgeServer  # 新增代码+DesktopGUIBridge: 标注 server 类型；如果没有这行代码，编辑器看不懂 workspace/token 字段。

    def log_message(self, format: str, *args: Any) -> None:  # 新增代码+DesktopGUIBridge: 关闭默认访问日志；如果没有这段函数，控制台会被轮询请求刷屏。
        return  # 新增代码+DesktopGUIBridge: 明确不输出标准库日志；如果没有这行代码，函数没有行为。
    # 新增代码+DesktopGUIBridge: 函数段结束，log_message 到此结束；如果没有这个边界说明，用户不容易看出它只负责降噪。

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:  # 新增代码+DesktopGUIBridge: 统一返回 JSON；如果没有这段函数，每个端点会重复 header 逻辑。
        raw_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")  # 新增代码+DesktopGUIBridge: 编码 UTF-8 JSON；如果没有这行代码，中文状态会乱码。
        self.send_response(status)  # 新增代码+DesktopGUIBridge: 写 HTTP 状态码；如果没有这行代码，前端无法判断成功失败。
        self.send_header("Content-Type", "application/json; charset=utf-8")  # 新增代码+DesktopGUIBridge: 声明 JSON 类型；如果没有这行代码，前端可能按文本处理。
        self.send_header("Content-Length", str(len(raw_body)))  # 新增代码+DesktopGUIBridge: 声明响应长度；如果没有这行代码，客户端可能等待连接关闭。
        self.send_header("Cache-Control", "no-store")  # 新增代码+DesktopGUIBridge: 禁止缓存状态响应；如果没有这行代码，GUI 可能显示旧状态。
        self.end_headers()  # 新增代码+DesktopGUIBridge: 结束响应头；如果没有这行代码，响应体不会正确发送。
        self.wfile.write(raw_body)  # 新增代码+DesktopGUIBridge: 写出响应体；如果没有这行代码，前端收不到数据。
    # 新增代码+DesktopGUIBridge: 函数段结束，_send_json 到此结束；如果没有这个边界说明，用户不容易看出它只负责响应包装。

    def _send_error(self, status: int, code: str, message: str) -> None:  # 新增代码+DesktopGUIBridge: 统一返回结构化错误；如果没有这段函数，前端要解析不同形状的失败。
        self._send_json(status, {"ok": False, "code": code, "error": message})  # 新增代码+DesktopGUIBridge: 返回不含本机路径的错误对象；如果没有这行代码，错误可能泄漏文件系统细节。
    # 新增代码+DesktopGUIBridge: 函数段结束，_send_error 到此结束；如果没有这个边界说明，用户不容易看出它只负责错误包装。

    def _origin_allowed(self) -> bool:  # 新增代码+DesktopGUIBridge: 检查浏览器来源；如果没有这段函数，本机恶意网页可能跨源访问 bridge。
        origin = self.headers.get("Origin", "")  # 新增代码+DesktopGUIBridge: 读取 Origin header；如果没有这行代码，无法判断请求来源。
        return origin in GUI_ALLOWED_ORIGINS  # 新增代码+DesktopGUIBridge: 只允许桌面 file/null 和 dev server；如果没有这行代码，任意来源都能调用。
    # 新增代码+DesktopGUIBridge: 函数段结束，_origin_allowed 到此结束；如果没有这个边界说明，用户不容易看出它只负责来源检查。

    def _authorized(self) -> bool:  # 新增代码+DesktopGUIBridge: 检查 GUI bridge token；如果没有这段函数，本机其它进程可直接读取状态。
        return self.headers.get(GUI_TOKEN_HEADER, "") == self.server.token  # 新增代码+DesktopGUIBridge: 比对启动 token；如果没有这行代码，认证字段不会生效。
    # 新增代码+DesktopGUIBridge: 函数段结束，_authorized 到此结束；如果没有这个边界说明，用户不容易看出它只负责 token 校验。

    def _guard_request(self, require_token: bool) -> bool:  # 新增代码+DesktopGUIBridge: 同时执行 Origin 和 token 门禁；如果没有这段函数，每个端点会重复安全判断。
        if not self._origin_allowed():  # 新增代码+DesktopGUIBridge: 先检查来源；如果没有这行代码，错误 token 前可能接受恶意来源。
            self._send_error(403, "origin_forbidden", "请求来源不允许访问 Desktop GUI bridge。")  # 新增代码+DesktopGUIBridge: 返回来源拒绝；如果没有这行代码，前端无法解释失败。
            return False  # 新增代码+DesktopGUIBridge: 阻止后续处理；如果没有这行代码，被拒来源仍可能继续执行。
        if require_token and not self._authorized():  # 新增代码+DesktopGUIBridge: 检查需要 token 的端点；如果没有这行代码，bootstrap 会被无授权读取。
            self._send_error(401, "unauthorized", f"未授权：请提供 {GUI_TOKEN_HEADER}。")  # 新增代码+DesktopGUIBridge: 返回认证拒绝；如果没有这行代码，客户端不知道要补哪个 header。
            return False  # 新增代码+DesktopGUIBridge: 阻止后续处理；如果没有这行代码，未授权请求仍可能继续执行。
        return True  # 新增代码+DesktopGUIBridge: 安全检查通过；如果没有这行代码，合法请求也无法继续。
    # 新增代码+DesktopGUIBridge: 函数段结束，_guard_request 到此结束；如果没有这个边界说明，用户不容易看出它只负责统一门禁。

    def do_GET(self) -> None:  # 新增代码+DesktopGUIBridge: 处理 GET 请求；如果没有这段函数，GUI 无法读取 bootstrap 和事件。
        path = urllib.parse.urlparse(self.path).path  # 新增代码+DesktopGUIBridge: 提取路径；如果没有这行代码，带 query 的请求无法路由。
        if path in {"/health", "/v1/gui/health"}:  # 新增代码+DesktopGUIBridge: 识别无 token 探活端点；如果没有这行代码，Electron 启动前无法轻量探测。
            if not self._guard_request(require_token=False):  # 新增代码+DesktopGUIBridge: health 仍检查 Origin；如果没有这行代码，恶意来源可探测 bridge。
                return  # 新增代码+DesktopGUIBridge: 门禁失败后退出；如果没有这行代码，会继续发送成功响应。
            self._send_json(200, {"ok": True, "app": "OpenHarness Desktop", "schema_version": GUI_SCHEMA_VERSION})  # 新增代码+DesktopGUIBridge: 返回轻量健康信息；如果没有这行代码，前端不知道 bridge 是否在线。
            return  # 新增代码+DesktopGUIBridge: 响应完成后退出；如果没有这行代码，handler 可能继续发送第二个响应。
        if path in {"/v1/gui/bootstrap", "/gui/bootstrap"}:  # 新增代码+DesktopGUIBridge: 识别 bootstrap 端点；如果没有这行代码，前端首屏请求会 404。
            if not self._guard_request(require_token=True):  # 新增代码+DesktopGUIBridge: bootstrap 必须通过 token；如果没有这行代码，项目状态可能被未授权读取。
                return  # 新增代码+DesktopGUIBridge: 门禁失败后退出；如果没有这行代码，会继续返回状态。
            self._send_json(200, build_gui_bootstrap_payload(self.server.workspace))  # 新增代码+DesktopGUIBridge: 返回首屏 payload；如果没有这行代码，GUI 不能启动。
            return  # 新增代码+DesktopGUIBridge: 响应完成后退出；如果没有这行代码，handler 可能继续发送第二个响应。
        self._send_error(404, "not_found", "未知 GUI bridge GET 路径。")  # 新增代码+DesktopGUIBridge: 返回结构化 404；如果没有这行代码，前端会收到 HTML 错误页。
    # 新增代码+DesktopGUIBridge: 函数段结束，do_GET 到此结束；如果没有这个边界说明，用户不容易看出当前只开放只读端点。
# 新增代码+DesktopGUIBridge: 类段结束，DesktopGuiBridgeHandler 到此结束；如果没有这个边界说明，用户不容易看出 HTTP handler 范围。


def create_gui_bridge_server(workspace: str | Path, host: str = "127.0.0.1", port: int = 8776, token: str = "") -> DesktopGuiBridgeServer:  # 新增代码+DesktopGUIBridge: 函数段开始，创建 GUI bridge server；如果没有这段函数，CLI 和测试会重复构造逻辑。
    return DesktopGuiBridgeServer((host, port), workspace=workspace, token=token)  # 新增代码+DesktopGUIBridge: 返回绑定 server；如果没有这行代码，调用方拿不到可启动对象。
# 新增代码+DesktopGUIBridge: 函数段结束，create_gui_bridge_server 到此结束；如果没有这个边界说明，用户不容易看出它只负责创建 server。
