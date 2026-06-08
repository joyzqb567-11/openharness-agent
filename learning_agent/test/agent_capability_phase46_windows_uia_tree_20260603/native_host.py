"""Windows Computer Use native host 协议层。"""  # 新增代码+Phase44WindowsNativeHost: 说明本文件负责 native host/client 消息合同；如果没有这个文件，Windows Computer Use 缺少类似 ClaudeCode host adapter 的独立边界。
from __future__ import annotations  # 新增代码+Phase44WindowsNativeHost: 启用延迟类型解析；如果没有这行代码，旧入口遇到前向类型标注时更容易导入失败。

import json  # 新增代码+Phase44WindowsNativeHost: 用于 CLI 输出结构化报告；如果没有这行代码，真实终端验收只能看散乱文本。
import sys  # 新增代码+Phase44WindowsNativeHost: 读取当前平台并限制 Windows native host 语义；如果没有这行代码，状态无法解释跨平台边界。
from typing import Any  # 新增代码+Phase44WindowsNativeHost: 标注 JSON 风格消息和响应；如果没有这行代码，协议输入输出边界不清楚。

try:  # 新增代码+Phase44WindowsNativeHost: 优先按包模式导入 helper 合同；如果没有这行代码，正常 unittest 和 agent 入口无法复用观察 helper。
    from learning_agent.computer_use.helper_client import NullWindowObservationHelper, StaticWindowObservationHelper, WindowObservationPayload  # 新增代码+Phase44WindowsNativeHost: 导入默认 helper、静态 helper 和 payload；如果没有这行代码，host 无法安全观察或自检。
except ModuleNotFoundError as error:  # 新增代码+Phase44WindowsNativeHost: 兼容 start_oauth_agent.bat 脚本模式；如果没有这行代码，真实终端可能因包名前缀不同而失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.helper_client"}:  # 新增代码+Phase44WindowsNativeHost: 只允许目标包路径缺失时 fallback；如果没有这行代码，真实内部 bug 会被误吞。
        raise  # 新增代码+Phase44WindowsNativeHost: 重新抛出非路径类导入错误；如果没有这行代码，排查 helper 内部问题会困难。
    from computer_use.helper_client import NullWindowObservationHelper, StaticWindowObservationHelper, WindowObservationPayload  # 新增代码+Phase44WindowsNativeHost: 脚本模式导入 helper 合同；如果没有这行代码，bat 入口无法运行 Phase44 自检。


PHASE44_WINDOWS_NATIVE_HOST_MARKER = "PHASE44_WINDOWS_NATIVE_HOST_READY"  # 新增代码+Phase44WindowsNativeHost: 定义 Phase44 ready marker；如果没有这行代码，真实终端验收没有稳定等待锚点。
PHASE44_WINDOWS_NATIVE_HOST_OK_TOKEN = "PHASE44_WINDOWS_NATIVE_HOST_OK"  # 新增代码+Phase44WindowsNativeHost: 定义 Phase44 OK token；如果没有这行代码，debug log 无法区分普通输出和自检通过。
PHASE44_NATIVE_HOST_PROTOCOL = "phase44_windows_native_host_protocol"  # 新增代码+Phase44WindowsNativeHost: 定义 native host 协议版本；如果没有这行代码，后续升级无法区分消息格式。
PHASE44_SUPPORTED_MESSAGES = ("status", "observe", "capture", "action", "cleanup")  # 新增代码+Phase44WindowsNativeHost: 固定 host 支持的消息白名单；如果没有这行代码，host 可能接收任意命令。
PHASE44_ACTIONS_EXPANDED = False  # 新增代码+Phase44WindowsNativeHost: 明确 Phase44 不扩大真实动作面；如果没有这行代码，架构阶段可能被误解为动作执行阶段。


def _phase44_bool_token(value: Any) -> str:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，把布尔值转成验收友好的小写文本；如果没有这段函数，CLI token 大小写会漂移。
    return str(bool(value)).lower()  # 新增代码+Phase44WindowsNativeHost: 返回 true/false；如果没有这行代码，场景断言容易因 True/False 失败。
# 新增代码+Phase44WindowsNativeHost: 函数段结束，_phase44_bool_token 到此结束；如果没有这个边界说明，读者不容易看出布尔格式范围。


def _safe_message_dict(message: Any) -> dict[str, Any]:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，把外部消息安全规整成 dict；如果没有这段函数，坏消息会让 host 崩溃。
    return dict(message) if isinstance(message, dict) else {}  # 新增代码+Phase44WindowsNativeHost: 只接受 dict 消息并复制；如果没有这行代码，列表或字符串消息会污染协议处理。
# 新增代码+Phase44WindowsNativeHost: 函数段结束，_safe_message_dict 到此结束；如果没有这个边界说明，读者不容易看出消息容错范围。


def _payload_summary(payload: WindowObservationPayload) -> dict[str, Any]:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，把观察 payload 转成 JSON 摘要；如果没有这段函数，host 可能直接返回二进制截图字节。
    screenshot_captured = bool(payload.screenshot_bytes)  # 新增代码+Phase44WindowsNativeHost: 判断是否有截图字节；如果没有这行代码，capture 无法说明是否捕获成功。
    return {"helper_name": payload.helper_name, "helper_available": bool(payload.helper_available), "helper_reason": payload.helper_reason, "screenshot_captured": screenshot_captured, "screenshot_format": payload.screenshot_format, "screenshot_width": int(payload.screenshot_width), "screenshot_height": int(payload.screenshot_height), "screenshot_byte_count": len(payload.screenshot_bytes), "screenshot_bytes_included": False, "accessibility_text_length": len(payload.accessibility_text), "focused_element": payload.focused_element, "selected_text_length": len(payload.selected_text), "document_text_length": len(payload.document_text)}  # 新增代码+Phase44WindowsNativeHost: 返回不含原始截图和正文的摘要；如果没有这行代码，IPC 响应可能过大或泄露内容。
# 新增代码+Phase44WindowsNativeHost: 函数段结束，_payload_summary 到此结束；如果没有这个边界说明，读者不容易看出 payload 脱敏范围。


def _runtime_capture_summary(capture_result: Any) -> dict[str, Any]:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，把 Phase45 截图运行时结果转成 host 可返回的安全摘要；如果没有这段函数，native host 可能把截图原始字节泄露到 IPC 响应里。
    summary = dict(capture_result) if isinstance(capture_result, dict) else {"captured": False, "reason": "截图运行时返回了非 dict 结果"}  # 新增代码+Phase45WindowsScreenshotRuntime: 只接受 dict 并给坏结果兜底；如果没有这行代码，异常 provider 可能让 host 崩溃。
    summary.pop("screenshot_bytes", None)  # 新增代码+Phase45WindowsScreenshotRuntime: 删除可能存在的原始截图 bytes；如果没有这行代码，大图可能被直接塞进 JSON 响应。
    summary.pop("raw_bytes", None)  # 新增代码+Phase45WindowsScreenshotRuntime: 删除兼容字段 raw_bytes；如果没有这行代码，未来 provider 换字段名时仍可能泄露二进制内容。
    summary["screenshot_bytes_included"] = False  # 新增代码+Phase45WindowsScreenshotRuntime: 明确告诉调用方没有返回原始 bytes；如果没有这行代码，验收和安全审计无法稳定判断脱敏结果。
    return summary  # 新增代码+Phase45WindowsScreenshotRuntime: 返回脱敏摘要；如果没有这行代码，host capture 分支拿不到可序列化结果。
# 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，_runtime_capture_summary 到此结束；如果没有这个边界说明，读者不容易看出运行时截图脱敏范围。


def _runtime_observe_summary(observe_result: Any) -> dict[str, Any]:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，把 UIA 树 observe 结果转成 host 可返回的安全摘要；如果没有这段函数，native host 可能把未来 raw_text 字段透出。
    summary = dict(observe_result) if isinstance(observe_result, dict) else {"captured": False, "reason": "UIA 树运行时返回了非 dict 结果"}  # 新增代码+Phase46WindowsUiaTree: 只接受 dict 并给坏结果兜底；如果没有这行代码，异常 provider 可能让 host 崩溃。
    summary.pop("raw_text", None)  # 新增代码+Phase46WindowsUiaTree: 删除可能存在的原始文本字段；如果没有这行代码，UIA 原文可能越过脱敏层。
    summary.pop("screenshot_bytes", None)  # 新增代码+Phase46WindowsUiaTree: 删除误放入 observe 的截图 bytes；如果没有这行代码，observe 响应可能变得巨大或泄露图像。
    summary["raw_text_included"] = False  # 新增代码+Phase46WindowsUiaTree: 明确声明 host observe 不返回原始 UIA 文本；如果没有这行代码，安全审计无法判断脱敏边界。
    return summary  # 新增代码+Phase46WindowsUiaTree: 返回脱敏 observe 摘要；如果没有这行代码，host observe 分支拿不到可序列化结果。
# 新增代码+Phase46WindowsUiaTree: 函数段结束，_runtime_observe_summary 到此结束；如果没有这个边界说明，读者不容易看出 UIA 树脱敏范围。


class WindowsComputerUseNativeHost:  # 新增代码+Phase44WindowsNativeHost: 类段开始，定义进程内 Windows native host；如果没有这个类，主 agent 没有独立 host 边界可调用。
    def __init__(self, helper: Any | None = None, platform: str | None = None, host_id: str = "windows-computer-use-native-host", real_actions_enabled: bool = False, screenshot_runtime: Any | None = None, uia_tree_runtime: Any | None = None) -> None:  # 修改代码+Phase46WindowsUiaTree: 函数段开始，初始化 helper、平台、动作开关、截图运行时和可选 UIA 树运行时；如果没有这段函数，host 无法接入 Phase46 结构化观察链路。
        self.helper = helper or NullWindowObservationHelper()  # 新增代码+Phase44WindowsNativeHost: 保存观察 helper，默认空 helper；如果没有这行代码，未配置 native helper 时 host 会崩溃。
        self.screenshot_runtime = screenshot_runtime  # 新增代码+Phase45WindowsScreenshotRuntime: 保存可选截图运行时；如果没有这行代码，capture 消息只能停留在旧 helper 摘要路径。
        self.uia_tree_runtime = uia_tree_runtime  # 新增代码+Phase46WindowsUiaTree: 保存可选 UIA 树运行时；如果没有这行代码，observe 消息无法返回结构化控件树。
        self.platform = platform or sys.platform  # 新增代码+Phase44WindowsNativeHost: 保存平台；如果没有这行代码，状态无法解释当前系统。
        self.host_id = str(host_id or "windows-computer-use-native-host")  # 新增代码+Phase44WindowsNativeHost: 保存 host 标识；如果没有这行代码，多 host 调试时无法区分来源。
        self.real_actions_enabled = bool(real_actions_enabled)  # 新增代码+Phase44WindowsNativeHost: 保存真实动作开关且默认关闭；如果没有这行代码，host 可能误以为 action 可执行。
        self.started = False  # 新增代码+Phase44WindowsNativeHost: 保存启动状态；如果没有这行代码，health_check 无法说明 host 是否已启动。
    # 修改代码+Phase46WindowsUiaTree: 函数段结束，WindowsComputerUseNativeHost.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def start(self) -> dict[str, Any]:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，启动 host 会话；如果没有这段函数，client 无法建立健康检查前置状态。
        self.started = True  # 新增代码+Phase44WindowsNativeHost: 标记 host 已启动；如果没有这行代码，status 会一直显示不健康。
        return {"started": True, "host_id": self.host_id, "protocol": PHASE44_NATIVE_HOST_PROTOCOL}  # 新增代码+Phase44WindowsNativeHost: 返回启动摘要；如果没有这行代码，调用方无法审计启动结果。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，WindowsComputerUseNativeHost.start 到此结束；如果没有这个边界说明，读者不容易看出启动范围。

    def stop(self) -> dict[str, Any]:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，停止 host 会话；如果没有这段函数，cleanup 没有具体动作。
        self.started = False  # 新增代码+Phase44WindowsNativeHost: 标记 host 已停止；如果没有这行代码，cleanup 后 health 状态会错误。
        return {"stopped": True, "host_id": self.host_id, "protocol": PHASE44_NATIVE_HOST_PROTOCOL}  # 新增代码+Phase44WindowsNativeHost: 返回停止摘要；如果没有这行代码，调用方无法确认 cleanup 已触发。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，WindowsComputerUseNativeHost.stop 到此结束；如果没有这个边界说明，读者不容易看出停止范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，返回 host 状态；如果没有这段函数，client 和 /computer 无法查看协议能力。
        helper_status = self.helper.status() if hasattr(self.helper, "status") else {}  # 新增代码+Phase44WindowsNativeHost: 读取 helper 状态；如果没有这行代码，status 无法展示观察来源。
        screenshot_runtime_status = self.screenshot_runtime.status() if hasattr(self.screenshot_runtime, "status") else {}  # 新增代码+Phase45WindowsScreenshotRuntime: 读取截图运行时状态；如果没有这行代码，/computer 和诊断看不到 Phase45 provider 链路。
        uia_tree_runtime_status = self.uia_tree_runtime.status() if hasattr(self.uia_tree_runtime, "status") else {}  # 新增代码+Phase46WindowsUiaTree: 读取 UIA 树运行时状态；如果没有这行代码，/computer 和诊断看不到 Phase46 控件树链路。
        return {"marker": PHASE44_WINDOWS_NATIVE_HOST_MARKER, "host_id": self.host_id, "protocol": PHASE44_NATIVE_HOST_PROTOCOL, "platform": self.platform, "started": bool(self.started), "healthy": bool(self.started), "supported_messages": list(PHASE44_SUPPORTED_MESSAGES), "helper": dict(helper_status) if isinstance(helper_status, dict) else {}, "screenshot_runtime_available": bool(self.screenshot_runtime is not None), "screenshot_runtime": dict(screenshot_runtime_status) if isinstance(screenshot_runtime_status, dict) else {}, "uia_tree_runtime_available": bool(self.uia_tree_runtime is not None), "uia_tree_runtime": dict(uia_tree_runtime_status) if isinstance(uia_tree_runtime_status, dict) else {}, "safe_observe_only": True, "real_actions_enabled": bool(self.real_actions_enabled), "actions_expanded": PHASE44_ACTIONS_EXPANDED}  # 修改代码+Phase46WindowsUiaTree: 返回包含截图和 UIA 树运行时的完整状态；如果没有这行代码，健康检查和能力展示没有统一事实源。
    # 修改代码+Phase46WindowsUiaTree: 函数段结束，WindowsComputerUseNativeHost.status 到此结束；如果没有这个边界说明，读者不容易看出状态范围。

    def _ok(self, op: str, result: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，构造成功响应；如果没有这段函数，每个分支会重复拼 envelope。
        return {"ok": True, "op": str(op), "host_id": self.host_id, "protocol": PHASE44_NATIVE_HOST_PROTOCOL, "result": dict(result), "actions_expanded": PHASE44_ACTIONS_EXPANDED}  # 新增代码+Phase44WindowsNativeHost: 返回统一成功 envelope；如果没有这行代码，client 难以稳定读取响应。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，WindowsComputerUseNativeHost._ok 到此结束；如果没有这个边界说明，读者不容易看出成功 envelope 范围。

    def _error(self, op: str, decision: str, message: str) -> dict[str, Any]:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，构造失败响应；如果没有这段函数，拒绝原因会格式不一致。
        return {"ok": False, "op": str(op), "host_id": self.host_id, "protocol": PHASE44_NATIVE_HOST_PROTOCOL, "error": {"decision": str(decision), "message": str(message)}, "actions_expanded": PHASE44_ACTIONS_EXPANDED}  # 新增代码+Phase44WindowsNativeHost: 返回统一失败 envelope；如果没有这行代码，调用方无法机器读取拒绝原因。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，WindowsComputerUseNativeHost._error 到此结束；如果没有这个边界说明，读者不容易看出失败 envelope 范围。

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，处理一条 native host 消息；如果没有这段函数，host 只有状态没有协议入口。
        payload = _safe_message_dict(message)  # 新增代码+Phase44WindowsNativeHost: 规整消息对象；如果没有这行代码，坏消息可能崩溃。
        op = str(payload.get("op", "status") or "status").strip()  # 新增代码+Phase44WindowsNativeHost: 读取消息操作名；如果没有这行代码，host 无法分发不同命令。
        if op == "status":  # 新增代码+Phase44WindowsNativeHost: 处理状态消息；如果没有这行代码，client 不能查询能力。
            return self._ok(op, self.status())  # 新增代码+Phase44WindowsNativeHost: 返回状态响应；如果没有这行代码，status 消息没有输出。
        if op == "observe":  # 新增代码+Phase44WindowsNativeHost: 处理只读观察消息；如果没有这行代码，host 无法调用 helper 观察窗口。
            if self.uia_tree_runtime is not None:  # 新增代码+Phase46WindowsUiaTree: 优先使用 Phase46 UIA 树运行时；如果没有这行代码，host observe 不会返回结构化控件树。
                uia_observed = self.uia_tree_runtime.observe_window(_safe_message_dict(payload.get("window")))  # 新增代码+Phase46WindowsUiaTree: 调用运行时观察目标窗口控件树；如果没有这行代码，native host 无法触发 UIA tree 链路。
                return self._ok(op, _runtime_observe_summary(uia_observed))  # 新增代码+Phase46WindowsUiaTree: 返回脱敏后的 UIA 树摘要；如果没有这行代码，调用方拿不到 Phase46 observe 结果。
            observed = self.helper.observe_window(_safe_message_dict(payload.get("window")))  # 新增代码+Phase44WindowsNativeHost: 调用 helper 获取 payload；如果没有这行代码，observe 只是空壳。
            return self._ok(op, _payload_summary(observed))  # 新增代码+Phase44WindowsNativeHost: 返回观察摘要；如果没有这行代码，client 拿不到 helper 结果。
        if op == "capture":  # 新增代码+Phase44WindowsNativeHost: 处理截图消息；如果没有这行代码，截图协议没有独立入口。
            if self.screenshot_runtime is not None:  # 新增代码+Phase45WindowsScreenshotRuntime: 优先使用 Phase45 截图运行时；如果没有这行代码，host capture 不会走 WGC/GDI/evidence 链路。
                runtime_capture = self.screenshot_runtime.capture_window(_safe_message_dict(payload.get("window")))  # 新增代码+Phase45WindowsScreenshotRuntime: 调用运行时捕获目标窗口；如果没有这行代码，native host 无法触发真实截图 provider 链。
                return self._ok(op, _runtime_capture_summary(runtime_capture))  # 新增代码+Phase45WindowsScreenshotRuntime: 返回脱敏后的 runtime 截图摘要；如果没有这行代码，调用方拿不到 Phase45 capture 结果。
            captured = self.helper.observe_window(_safe_message_dict(payload.get("window")))  # 新增代码+Phase44WindowsNativeHost: 复用 helper 观察窗口；如果没有这行代码，capture 无法得到截图摘要。
            summary = _payload_summary(captured)  # 新增代码+Phase44WindowsNativeHost: 转成不含原始字节的摘要；如果没有这行代码，二进制截图可能直接进入 JSON。
            return self._ok(op, summary)  # 新增代码+Phase44WindowsNativeHost: 返回截图摘要响应；如果没有这行代码，capture 消息无输出。
        if op == "cleanup":  # 新增代码+Phase44WindowsNativeHost: 处理 cleanup 消息；如果没有这行代码，turn 结束时无法清理 host 状态。
            stop_result = self.stop()  # 新增代码+Phase44WindowsNativeHost: 停止 host 会话；如果没有这行代码，cleanup 不会改变状态。
            return self._ok(op, {"cleanup_completed": True, **stop_result})  # 新增代码+Phase44WindowsNativeHost: 返回 cleanup 完成摘要；如果没有这行代码，调用方无法确认清理。
        if op == "action":  # 新增代码+Phase44WindowsNativeHost: 识别动作消息但默认拒绝；如果没有这行代码，未来动作协议没有安全占位。
            return self._error(op, "real_action_refused_by_native_host", "Phase44 native host 默认只读，未执行任何真实鼠标键盘动作。")  # 新增代码+Phase44WindowsNativeHost: 返回动作拒绝；如果没有这行代码，action 可能落到未知分支。
        return self._error(op, "unsupported_native_host_message", f"不支持的 native host 消息：{op}")  # 新增代码+Phase44WindowsNativeHost: 拒绝未知消息；如果没有这行代码，协议白名单不生效。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，WindowsComputerUseNativeHost.handle_message 到此结束；如果没有这个边界说明，读者不容易看出消息分发范围。
# 新增代码+Phase44WindowsNativeHost: 类段结束，WindowsComputerUseNativeHost 到此结束；如果没有这个边界说明，读者不容易看出 host 类范围。


class InProcessWindowsNativeHostClient:  # 新增代码+Phase44WindowsNativeHost: 类段开始，定义进程内 host client；如果没有这个类，主 agent 无法通过稳定 client API 调用 host。
    def __init__(self, host: WindowsComputerUseNativeHost | None = None) -> None:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，保存 host 实例；如果没有这段函数，client 没有目标。
        self.host = host or WindowsComputerUseNativeHost()  # 新增代码+Phase44WindowsNativeHost: 使用传入 host 或默认 host；如果没有这行代码，client 无法独立工作。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，InProcessWindowsNativeHostClient.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def health_check(self) -> dict[str, Any]:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，启动并检查 host 健康；如果没有这段函数，client 无法提供生产级健康检查入口。
        self.host.start()  # 新增代码+Phase44WindowsNativeHost: 先启动 host；如果没有这行代码，status.healthy 会保持 false。
        status = self.host.status()  # 新增代码+Phase44WindowsNativeHost: 读取启动后的状态；如果没有这行代码，健康检查没有证据。
        return {"healthy": bool(status.get("healthy")), "started": bool(status.get("started")), "status": status}  # 新增代码+Phase44WindowsNativeHost: 返回健康摘要；如果没有这行代码，调用方要自己解析完整 status。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，InProcessWindowsNativeHostClient.health_check 到此结束；如果没有这个边界说明，读者不容易看出健康检查范围。

    def request(self, message: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，发送一条 host 消息；如果没有这段函数，client 不能统一调用 status/observe/capture/action/cleanup。
        if not self.host.started:  # 新增代码+Phase44WindowsNativeHost: 检查 host 是否已启动；如果没有这行代码，直接 request 会拿到 unhealthy 状态。
            self.host.start()  # 新增代码+Phase44WindowsNativeHost: 自动启动进程内 host；如果没有这行代码，用户必须记住先 health_check。
        return self.host.handle_message(message)  # 新增代码+Phase44WindowsNativeHost: 分发消息给 host；如果没有这行代码，request 没有实际行为。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，InProcessWindowsNativeHostClient.request 到此结束；如果没有这个边界说明，读者不容易看出请求范围。
# 新增代码+Phase44WindowsNativeHost: 类段结束，InProcessWindowsNativeHostClient 到此结束；如果没有这个边界说明，读者不容易看出 client 类范围。


def run_phase44_native_host_contract() -> dict[str, Any]:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，运行 Phase44 host 协议自检；如果没有这段函数，真实终端场景没有稳定命令入口。
    payload = WindowObservationPayload(screenshot_bytes=b"phase44-contract-bmp", screenshot_format="bmp", screenshot_width=44, screenshot_height=22, accessibility_text="button: OK", focused_element="edit", selected_text="", document_text="document", helper_name="phase44_contract_helper", helper_available=True, helper_reason="contract static helper")  # 新增代码+Phase44WindowsNativeHost: 构造合同自检 payload；如果没有这行代码，observe/capture 成功路径没有数据。
    helper = StaticWindowObservationHelper(default_payload=payload)  # 新增代码+Phase44WindowsNativeHost: 使用静态 helper 保证无真实桌面副作用；如果没有这行代码，自检可能读取用户窗口。
    client = InProcessWindowsNativeHostClient(WindowsComputerUseNativeHost(helper=helper, platform="win32"))  # 新增代码+Phase44WindowsNativeHost: 创建进程内 host client；如果没有这行代码，自检没有协议主体。
    health = client.health_check()  # 新增代码+Phase44WindowsNativeHost: 执行健康检查；如果没有这行代码，health=true 没有证据。
    status = client.request({"op": "status"})  # 新增代码+Phase44WindowsNativeHost: 请求 status 消息；如果没有这行代码，messages=true 缺少状态分支。
    observe = client.request({"op": "observe", "window": {"window_id": "hwnd:4401"}})  # 新增代码+Phase44WindowsNativeHost: 请求 observe 消息；如果没有这行代码，messages=true 缺少观察分支。
    capture = client.request({"op": "capture", "window": {"window_id": "hwnd:4401"}})  # 新增代码+Phase44WindowsNativeHost: 请求 capture 消息；如果没有这行代码，messages=true 缺少截图分支。
    action = client.request({"op": "action", "action": "click", "x": 1, "y": 2})  # 新增代码+Phase44WindowsNativeHost: 请求 action 消息并期待拒绝；如果没有这行代码，safe_action_refused 没有证据。
    cleanup = client.request({"op": "cleanup"})  # 新增代码+Phase44WindowsNativeHost: 请求 cleanup 消息；如果没有这行代码，messages=true 缺少清理分支。
    messages = bool(status.get("ok") and observe.get("ok") and capture.get("ok") and cleanup.get("ok"))  # 新增代码+Phase44WindowsNativeHost: 汇总核心消息是否成功；如果没有这行代码，CLI 无法报告 messages=true。
    safe_action_refused = bool(not action.get("ok") and action.get("error", {}).get("decision") == "real_action_refused_by_native_host")  # 新增代码+Phase44WindowsNativeHost: 检查动作被安全拒绝；如果没有这行代码，默认拒绝边界不会进入报告。
    return {"marker": PHASE44_WINDOWS_NATIVE_HOST_MARKER, "ok_token": PHASE44_WINDOWS_NATIVE_HOST_OK_TOKEN, "health": bool(health.get("healthy")), "messages": messages, "safe_action_refused": safe_action_refused, "actions_expanded": PHASE44_ACTIONS_EXPANDED, "status": status, "observe": observe, "capture": capture, "cleanup": cleanup}  # 新增代码+Phase44WindowsNativeHost: 返回完整合同报告；如果没有这行代码，CLI 和测试拿不到统一结果。
# 新增代码+Phase44WindowsNativeHost: 函数段结束，run_phase44_native_host_contract 到此结束；如果没有这个边界说明，读者不容易看出合同自检范围。


def phase44_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，把合同报告转成稳定 token 行；如果没有这段函数，验收场景需要解析完整 JSON。
    return f"{PHASE44_WINDOWS_NATIVE_HOST_MARKER} {PHASE44_WINDOWS_NATIVE_HOST_OK_TOKEN} health={_phase44_bool_token(report.get('health'))} messages={_phase44_bool_token(report.get('messages'))} safe_action_refused={_phase44_bool_token(report.get('safe_action_refused'))} actions_expanded={_phase44_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase44WindowsNativeHost: 返回固定顺序验收行；如果没有这行代码，debug log token 容易漂移。
# 新增代码+Phase44WindowsNativeHost: 函数段结束，phase44_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 格式范围。


def main() -> int:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，提供命令行入口；如果没有这段函数，真实终端无法运行 Phase44 自检。
    report = run_phase44_native_host_contract()  # 新增代码+Phase44WindowsNativeHost: 运行合同自检；如果没有这行代码，CLI 没有真实报告。
    print(PHASE44_WINDOWS_NATIVE_HOST_MARKER)  # 新增代码+Phase44WindowsNativeHost: 打印 ready marker；如果没有这行代码，验收器可能等不到阶段标记。
    print(phase44_cli_line(report))  # 新增代码+Phase44WindowsNativeHost: 打印稳定 token 行；如果没有这行代码，debug log 无法确认通过。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase44WindowsNativeHost: 打印结构化报告；如果没有这行代码，失败时不易复盘。
    return 0 if bool(report.get("health") and report.get("messages") and report.get("safe_action_refused") and not report.get("actions_expanded")) else 1  # 新增代码+Phase44WindowsNativeHost: 根据合同结果返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase44WindowsNativeHost: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出命令入口范围。


if __name__ == "__main__":  # 新增代码+Phase44WindowsNativeHost: 允许直接运行模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase44WindowsNativeHost: 用 main 返回码退出；如果没有这行代码，命令行状态不稳定。
