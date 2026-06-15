"""Windows Computer Use Phase55 out-of-process native helper v2。"""  # 新增代码+Phase55WindowsNativeHelperV2: 标明本文件负责 helper v2 子进程协议；如果没有这行代码，读者不知道 out-of-process 边界在哪里。
from __future__ import annotations  # 新增代码+Phase55WindowsNativeHelperV2: 启用延迟类型解析；如果没有这行代码，旧运行路径遇到前向类型标注时更容易导入失败。

import json  # 新增代码+Phase55WindowsNativeHelperV2: 导入 JSON 工具实现 JSONL 协议；如果没有这行代码，client 和 worker 无法交换结构化消息。
import os  # 新增代码+Phase55WindowsNativeHelperV2: 导入 os 读取 worker pid；如果没有这行代码，health 状态无法证明 helper 是子进程。
import queue  # 新增代码+Phase55WindowsNativeHelperV2: 导入队列实现 stdout 读取超时；如果没有这行代码，Windows 上 readline 超时很难处理。
import subprocess  # 新增代码+Phase55WindowsNativeHelperV2: 导入子进程能力启动 helper worker；如果没有这行代码，Phase55 仍只能进程内模拟。
import sys  # 新增代码+Phase55WindowsNativeHelperV2: 导入当前 Python 解释器和 argv；如果没有这行代码，client 不知道如何启动同版本 worker。
import threading  # 新增代码+Phase55WindowsNativeHelperV2: 导入线程用于非阻塞读取 worker 响应；如果没有这行代码，超时场景会卡住主 agent。
import time  # 新增代码+Phase55WindowsNativeHelperV2: 导入时间工具记录 started_at 和 debug_sleep；如果没有这行代码，helper 生命周期缺少时间证据。
from typing import Any  # 新增代码+Phase55WindowsNativeHelperV2: 导入通用 JSON 类型；如果没有这行代码，协议函数边界不清楚。

PHASE55_WINDOWS_NATIVE_HELPER_V2_MARKER = "PHASE55_WINDOWS_NATIVE_HELPER_V2_READY"  # 新增代码+Phase55WindowsNativeHelperV2: 定义 Phase55 ready marker；如果没有这行代码，真实终端验收无法稳定等待本阶段输出。
PHASE55_WINDOWS_NATIVE_HELPER_V2_OK_TOKEN = "PHASE55_WINDOWS_NATIVE_HELPER_V2_OK"  # 新增代码+Phase55WindowsNativeHelperV2: 定义 Phase55 OK token；如果没有这行代码，日志无法区分 helper v2 通过和普通文本。
PHASE55_NATIVE_HELPER_V2_PROTOCOL = "windows_native_helper_v2"  # 新增代码+Phase55WindowsNativeHelperV2: 定义 helper v2 协议名；如果没有这行代码，调用方无法区分 Phase44 in-process host 和 Phase55 子进程 helper。
PHASE55_NATIVE_HELPER_V2_VERSION = "phase55.1"  # 新增代码+Phase55WindowsNativeHelperV2: 定义 helper v2 版本；如果没有这行代码，后续协议升级无法审计。
PHASE55_SUPPORTED_OPERATIONS = ("status", "list_windows", "capture_window", "read_uia_tree", "send_input", "hotkey", "cleanup")  # 新增代码+Phase55WindowsNativeHelperV2: 固定生产协议操作白名单；如果没有这行代码，worker 能力表会漂移。
PHASE55_ACTIONS_EXPANDED = False  # 新增代码+Phase55WindowsNativeHelperV2: 明确 Phase55 不扩大真实桌面动作面；如果没有这行代码，helper 架构可能被误解为已放开动作。


# 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，_bool_token 把布尔值转成稳定小写 token；如果没有这段函数，CLI 可能混用 True/False 和 true/false，作者意图是让真实终端断言稳定。
def _bool_token(value: Any) -> str:  # 新增代码+Phase55WindowsNativeHelperV2: 定义布尔 token helper；如果没有这行代码，多处输出会重复写转换逻辑。
    return "true" if bool(value) else "false"  # 新增代码+Phase55WindowsNativeHelperV2: 返回小写布尔文本；如果没有这行代码，场景 JSON 的 token 匹配可能失败。
# 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


# 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，_utc_timestamp 生成 helper 启动时间；如果没有这段函数，health 状态缺少可审计生命周期时间，作者意图是让崩溃恢复有时间线。
def _utc_timestamp() -> str:  # 新增代码+Phase55WindowsNativeHelperV2: 定义 UTC 时间戳 helper；如果没有这行代码，各处会重复拼接时间格式。
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())  # 新增代码+Phase55WindowsNativeHelperV2: 返回稳定 UTC 字符串；如果没有这行代码，started_at 格式会漂移。
# 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，_utc_timestamp 到此结束；如果没有这个边界说明，初学者不容易看出时间 helper 范围。


# 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，_error_response 构造统一错误 envelope；如果没有这段函数，超时、崩溃和拒绝动作会有不同格式，作者意图是主 agent 永远拿到结构化错误。
def _error_response(op: str, decision: str, message: str, request_id: Any = None) -> dict[str, Any]:  # 新增代码+Phase55WindowsNativeHelperV2: 定义错误响应 helper；如果没有这行代码，错误分支会重复拼装字段。
    return {"ok": False, "op": str(op or ""), "request_id": request_id, "protocol": PHASE55_NATIVE_HELPER_V2_PROTOCOL, "error": {"decision": str(decision), "message": str(message)}, "actions_expanded": PHASE55_ACTIONS_EXPANDED}  # 新增代码+Phase55WindowsNativeHelperV2: 返回统一错误 envelope；如果没有这行代码，调用方无法稳定读取 error.decision。
# 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，_error_response 到此结束；如果没有这个边界说明，初学者不容易看出错误 envelope 范围。


# 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，_ok_response 构造统一成功 envelope；如果没有这段函数，各个 op 响应字段会漂移，作者意图是让 worker 协议像 JSON-RPC 一样可预测。
def _ok_response(op: str, result: dict[str, Any], request_id: Any = None) -> dict[str, Any]:  # 新增代码+Phase55WindowsNativeHelperV2: 定义成功响应 helper；如果没有这行代码，成功分支会重复拼装字段。
    return {"ok": True, "op": str(op or ""), "request_id": request_id, "protocol": PHASE55_NATIVE_HELPER_V2_PROTOCOL, "result": dict(result), "actions_expanded": PHASE55_ACTIONS_EXPANDED}  # 新增代码+Phase55WindowsNativeHelperV2: 返回统一成功 envelope；如果没有这行代码，调用方无法稳定读取 result。
# 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，_ok_response 到此结束；如果没有这个边界说明，初学者不容易看出成功 envelope 范围。


class WindowsNativeHelperV2Worker:  # 新增代码+Phase55WindowsNativeHelperV2: 类段开始，定义运行在子进程里的 worker；如果没有这个类，helper v2 没有真正执行协议的一端。
    def __init__(self, real_actions_enabled: bool = False, screenshot_pipeline: Any | None = None, uia_locator_runtime: Any | None = None) -> None:  # 修改代码+Phase57RealUiaLocator: 函数段开始，初始化 worker 状态并允许注入截图 pipeline 和 UIA locator runtime；如果没有这段函数，worker 不知道自己 pid、启动时间、安全开关、截图链路和真实 UIA 链路。
        self.pid = os.getpid()  # 新增代码+Phase55WindowsNativeHelperV2: 保存当前子进程 pid；如果没有这行代码，health 无法证明 out-of-process。
        self.started_at = _utc_timestamp()  # 新增代码+Phase55WindowsNativeHelperV2: 保存启动时间；如果没有这行代码，生命周期审计缺少时间。
        self.real_actions_enabled = bool(real_actions_enabled)  # 新增代码+Phase55WindowsNativeHelperV2: 保存真实动作开关且默认关闭；如果没有这行代码，send_input 安全边界不明确。
        self.screenshot_pipeline = screenshot_pipeline  # 新增代码+Phase56RealScreenshotPipeline: 保存可选真实截图 pipeline；如果没有这行代码，capture_window 只能返回 Phase55 占位摘要。
        self.uia_locator_runtime = uia_locator_runtime  # 新增代码+Phase57RealUiaLocator: 保存可选真实 UIA locator runtime；如果没有这行代码，read_uia_tree 无法从 Phase55 占位升级到 Phase57 真实树。
        self.should_exit = False  # 新增代码+Phase55WindowsNativeHelperV2: 保存 cleanup 后退出标志；如果没有这行代码，cleanup 不能优雅结束 worker loop。
    # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，WindowsNativeHelperV2Worker.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，返回 worker health 状态；如果没有这段函数，client 无法验收 helper health。
        return {"marker": PHASE55_WINDOWS_NATIVE_HELPER_V2_MARKER, "protocol": PHASE55_NATIVE_HELPER_V2_PROTOCOL, "version": PHASE55_NATIVE_HELPER_V2_VERSION, "pid": self.pid, "started_at": self.started_at, "health": "healthy", "healthy": True, "capabilities": list(PHASE55_SUPPORTED_OPERATIONS), "real_actions_enabled": self.real_actions_enabled, "screenshot_pipeline_available": self.screenshot_pipeline is not None, "uia_locator_available": self.uia_locator_runtime is not None, "actions_expanded": PHASE55_ACTIONS_EXPANDED}  # 修改代码+Phase57RealUiaLocator: 返回完整 health 字段并暴露截图 pipeline 与 UIA locator 是否已注入；如果没有这行代码，真实终端看不到 helper 是否接入 Phase57。
    # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，WindowsNativeHelperV2Worker.status 到此结束；如果没有这个边界说明，初学者不容易看出 health 范围。

    def handle(self, message: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，处理单条 JSON 请求；如果没有这段函数，worker 无法响应 client。
        payload = dict(message) if isinstance(message, dict) else {}  # 新增代码+Phase55WindowsNativeHelperV2: 容错复制请求；如果没有这行代码，坏 JSON 类型可能让 worker 崩溃。
        op = str(payload.get("op", "status") or "status").strip()  # 新增代码+Phase55WindowsNativeHelperV2: 读取操作名；如果没有这行代码，worker 无法分发协议。
        request_id = payload.get("id")  # 新增代码+Phase55WindowsNativeHelperV2: 读取请求 id 用于响应关联；如果没有这行代码，client 难以匹配日志。
        if op == "status":  # 新增代码+Phase55WindowsNativeHelperV2: 处理 status 请求；如果没有这行代码，health_check 没有协议入口。
            return _ok_response(op, self.status(), request_id=request_id)  # 新增代码+Phase55WindowsNativeHelperV2: 返回 health 状态；如果没有这行代码，client.start 无法判断健康。
        if op == "list_windows":  # 新增代码+Phase55WindowsNativeHelperV2: 处理 list_windows 请求；如果没有这行代码，窗口枚举协议缺项。
            return _ok_response(op, {"windows": [], "source": "phase55_helper_v2_no_inventory_yet", "real_provider_used": False}, request_id=request_id)  # 新增代码+Phase55WindowsNativeHelperV2: 返回空但结构化窗口列表；如果没有这行代码，未接真实 inventory 时会被误认为失败。
        if op == "capture_window":  # 修改代码+Phase56RealScreenshotPipeline: 处理 capture_window 请求并优先走 Phase56 pipeline；如果没有这行代码，截图协议缺项。
            return _ok_response(op, self._capture_window_summary(dict(payload.get("window", {}) if isinstance(payload.get("window", {}), dict) else {})), request_id=request_id)  # 修改代码+Phase56RealScreenshotPipeline: 返回不含原始 bytes 的截图摘要；如果没有这行代码，JSON 响应可能泄露大二进制或停留占位。
        if op == "read_uia_tree":  # 新增代码+Phase55WindowsNativeHelperV2: 处理 read_uia_tree 请求；如果没有这行代码，UIA 树协议缺项。
            return _ok_response(op, self._read_uia_tree_summary(dict(payload.get("window", {}) if isinstance(payload.get("window", {}), dict) else {}), dict(payload.get("locator", {}) if isinstance(payload.get("locator", {}), dict) else {})), request_id=request_id)  # 修改代码+Phase57RealUiaLocator: 返回 Phase57 真实 UIA 树摘要和可选定位结果；如果没有这行代码，read_uia_tree 会继续停在 Phase55 占位树。
        if op == "send_input":  # 新增代码+Phase55WindowsNativeHelperV2: 处理 send_input 请求但默认拒绝；如果没有这行代码，真实动作安全默认值没有覆盖。
            return _error_response(op, "real_action_refused_by_helper_v2", "Phase55 helper v2 默认拒绝 send_input，未触碰真实鼠标键盘。", request_id=request_id)  # 新增代码+Phase55WindowsNativeHelperV2: 返回稳定拒绝错误且不回显文本；如果没有这行代码，send_input 可能误触真实系统或泄露原文。
        if op == "hotkey":  # 新增代码+Phase55WindowsNativeHelperV2: 处理 hotkey 状态请求；如果没有这行代码，Phase61 热键协议没有占位。
            return _ok_response(op, {"registered": False, "available": False, "reason": "Phase55 只提供 hotkey 协议占位，Phase61 才注册全局 abort 热键。"}, request_id=request_id)  # 新增代码+Phase55WindowsNativeHelperV2: 返回热键占位状态；如果没有这行代码，用户会误以为热键已注册。
        if op == "cleanup":  # 新增代码+Phase55WindowsNativeHelperV2: 处理 cleanup 请求；如果没有这行代码，client 无法优雅关闭 worker。
            self.should_exit = True  # 新增代码+Phase55WindowsNativeHelperV2: 标记响应后退出 loop；如果没有这行代码，cleanup 不会结束子进程。
            return _ok_response(op, {"cleanup_completed": True, "pid": self.pid}, request_id=request_id)  # 新增代码+Phase55WindowsNativeHelperV2: 返回 cleanup 完成摘要；如果没有这行代码，调用方无法确认 worker 已收到清理。
        if op == "debug_sleep":  # 新增代码+Phase55WindowsNativeHelperV2: 处理测试用 sleep 请求；如果没有这行代码，超时路径无法稳定验收。
            time.sleep(float(payload.get("seconds", 0) or 0))  # 新增代码+Phase55WindowsNativeHelperV2: 睡眠指定秒数；如果没有这行代码，client timeout 无法触发。
            return _ok_response(op, {"slept": True}, request_id=request_id)  # 新增代码+Phase55WindowsNativeHelperV2: 睡眠结束后返回成功；如果没有这行代码，非超时调试无法完成。
        if op == "debug_crash":  # 新增代码+Phase55WindowsNativeHelperV2: 处理测试用崩溃请求；如果没有这行代码，崩溃恢复路径无法稳定验收。
            raise SystemExit(55)  # 新增代码+Phase55WindowsNativeHelperV2: 立即退出 worker 模拟崩溃；如果没有这行代码，client 无法验证进程退出错误。
        return _error_response(op, "unsupported_native_helper_v2_message", f"不支持的 helper v2 消息：{op}", request_id=request_id)  # 新增代码+Phase55WindowsNativeHelperV2: 拒绝未知消息；如果没有这行代码，协议白名单不生效。
    # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，WindowsNativeHelperV2Worker.handle 到此结束；如果没有这个边界说明，初学者不容易看出消息分发范围。

    def run_stdio_loop(self) -> int:  # 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，运行 JSONL stdio worker loop；如果没有这段函数，子进程无法持续接收 client 请求。
        for line in sys.stdin:  # 新增代码+Phase55WindowsNativeHelperV2: 逐行读取 client JSON 请求；如果没有这行代码，worker 没有输入循环。
            if not line.strip():  # 新增代码+Phase55WindowsNativeHelperV2: 跳过空行；如果没有这行代码，空输入会触发 JSON 解析失败。
                continue  # 新增代码+Phase55WindowsNativeHelperV2: 继续等待下一行；如果没有这行代码，空行会继续向下处理。
            try:  # 新增代码+Phase55WindowsNativeHelperV2: 捕获单条请求解析或处理异常；如果没有这行代码，普通坏请求会杀死 worker。
                message = json.loads(line)  # 新增代码+Phase55WindowsNativeHelperV2: 解析 JSON 请求；如果没有这行代码，worker 无法读取 op。
                response = self.handle(message)  # 新增代码+Phase55WindowsNativeHelperV2: 处理请求；如果没有这行代码，请求没有响应。
            except SystemExit:  # 新增代码+Phase55WindowsNativeHelperV2: 允许 debug_crash 模拟进程退出；如果没有这行代码，崩溃会被包装成普通错误。
                raise  # 新增代码+Phase55WindowsNativeHelperV2: 重新抛出 SystemExit；如果没有这行代码，client 无法看到进程崩溃。
            except Exception as error:  # 新增代码+Phase55WindowsNativeHelperV2: 捕获未知异常并转结构化错误；如果没有这行代码，worker 会因单条坏请求退出。
                response = _error_response("unknown", "native_helper_v2_worker_error", type(error).__name__)  # 新增代码+Phase55WindowsNativeHelperV2: 返回异常类型但不泄露本地细节；如果没有这行代码，调用方只能看到管道断开。
            sys.stdout.write(json.dumps(response, ensure_ascii=False, sort_keys=True) + "\n")  # 新增代码+Phase55WindowsNativeHelperV2: 写出 JSONL 响应；如果没有这行代码，client 会一直等待。
            sys.stdout.flush()  # 新增代码+Phase55WindowsNativeHelperV2: 立即刷新响应；如果没有这行代码，client 可能超时。
            if self.should_exit:  # 新增代码+Phase55WindowsNativeHelperV2: 检查 cleanup 是否要求退出；如果没有这行代码，cleanup 响应后 worker 仍会常驻。
                return 0  # 新增代码+Phase55WindowsNativeHelperV2: 优雅退出 worker；如果没有这行代码，cleanup 生命周期不完整。
        return 0  # 新增代码+Phase55WindowsNativeHelperV2: stdin 关闭时正常退出；如果没有这行代码，进程退出码不明确。
    # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，WindowsNativeHelperV2Worker.run_stdio_loop 到此结束；如果没有这个边界说明，初学者不容易看出 worker loop 范围。

    def _read_uia_tree_summary(self, window: dict[str, Any], locator_query: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，执行或创建 Phase57 UIA locator runtime 并返回脱敏摘要；如果没有这段函数，helper v2 的 read_uia_tree 只能返回占位树。
        runtime = self.uia_locator_runtime  # 新增代码+Phase57RealUiaLocator: 读取已注入 runtime；如果没有这行代码，后续会重复访问可变属性。
        if runtime is None:  # 新增代码+Phase57RealUiaLocator: 检查是否还没有 runtime；如果没有这行代码，默认子进程无法自动接入 Phase57。
            try:  # 新增代码+Phase57RealUiaLocator: 捕获 Phase57 runtime 导入或初始化异常；如果没有这行代码，UIA 依赖问题会拖垮 worker。
                from learning_agent.computer_use_mcp_v2.windows_runtime.real_uia_locator import WindowsRealUiaLocatorRuntime  # 新增代码+Phase57RealUiaLocator: 延迟导入避免模块循环；如果没有这行代码，worker 默认无法读取真实 UIA。
                runtime = WindowsRealUiaLocatorRuntime()  # 新增代码+Phase57RealUiaLocator: 创建默认 PowerShell/.NET UIA runtime；如果没有这行代码，真实子进程 read_uia_tree 没有 provider 链。
                self.uia_locator_runtime = runtime  # 新增代码+Phase57RealUiaLocator: 缓存 runtime 供后续请求复用；如果没有这行代码，每次 read_uia_tree 都会重新建 provider。
            except Exception as error:  # 新增代码+Phase57RealUiaLocator: 处理 runtime 创建失败；如果没有这行代码，导入问题会变成堆栈。
                return {"captured": False, "real_uia_tree": False, "tree": {}, "flat_nodes": [], "node_count": 0, "semantic_locator_available": False, "raw_text_included": False, "reason": f"Phase57 UIA locator unavailable: {type(error).__name__}", "actions_expanded": PHASE55_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回结构化不可用摘要；如果没有这行代码，调用方无法恢复。
        try:  # 新增代码+Phase57RealUiaLocator: 捕获 runtime 读取或定位异常；如果没有这行代码，UIA provider 异常会杀死 worker。
            result = runtime.find_control(window, locator_query) if locator_query else runtime.observe_window(window)  # 新增代码+Phase57RealUiaLocator: 根据是否传 locator 查询选择观察或定位；如果没有这行代码，helper 无法同时支持树和语义定位。
        except Exception as error:  # 新增代码+Phase57RealUiaLocator: 处理 runtime 执行失败；如果没有这行代码，目标窗口变化会拖垮 helper。
            return {"captured": False, "real_uia_tree": False, "tree": {}, "flat_nodes": [], "node_count": 0, "semantic_locator_available": True, "raw_text_included": False, "reason": f"Phase57 UIA locator failed: {type(error).__name__}", "actions_expanded": PHASE55_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回结构化执行失败摘要；如果没有这行代码，调用方只能看到崩溃。
        summary = dict(result) if isinstance(result, dict) else {"captured": False, "reason": "Phase57 runtime returned non-dict result."}  # 新增代码+Phase57RealUiaLocator: 只接受 dict 结果并兜底；如果没有这行代码，坏返回会污染协议。
        summary["raw_text_included"] = False  # 新增代码+Phase57RealUiaLocator: 明确响应不含 UIA 原始敏感文本；如果没有这行代码，安全审计无法稳定判断。
        summary["actions_expanded"] = PHASE55_ACTIONS_EXPANDED  # 新增代码+Phase57RealUiaLocator: 保持 helper v2 动作面未扩大；如果没有这行代码，UIA 接入可能被误解为动作放开。
        return summary  # 新增代码+Phase57RealUiaLocator: 返回脱敏 UIA 树摘要；如果没有这行代码，read_uia_tree 没有结果。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，WindowsNativeHelperV2Worker._read_uia_tree_summary 到此结束；如果没有这个边界说明，初学者不容易看出 helper v2 UIA 摘要范围。

    def _capture_window_summary(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，执行或创建 Phase56 截图 pipeline 并脱敏摘要；如果没有这段函数，helper v2 capture 会继续只是占位。
        pipeline = self.screenshot_pipeline  # 新增代码+Phase56RealScreenshotPipeline: 读取已注入 pipeline；如果没有这行代码，后续会重复访问可变属性。
        if pipeline is None:  # 新增代码+Phase56RealScreenshotPipeline: 检查是否还没有 pipeline；如果没有这行代码，默认子进程无法自动接入 Phase56。
            try:  # 新增代码+Phase56RealScreenshotPipeline: 捕获 Phase56 pipeline 导入或初始化异常；如果没有这行代码，截图依赖问题会拖垮 worker。
                from learning_agent.computer_use_mcp_v2.windows_runtime.real_screenshot_pipeline import WindowsRealScreenshotPipeline  # 新增代码+Phase56RealScreenshotPipeline: 延迟导入避免模块循环；如果没有这行代码，worker 默认无法截图。
                pipeline = WindowsRealScreenshotPipeline()  # 新增代码+Phase56RealScreenshotPipeline: 创建默认 WGC→GDI 截图 pipeline；如果没有这行代码，真实子进程 capture 没有 provider 链。
                self.screenshot_pipeline = pipeline  # 新增代码+Phase56RealScreenshotPipeline: 缓存 pipeline 供后续请求复用；如果没有这行代码，每次 capture 都会重新建 provider 和 evidence store。
            except Exception as error:  # 新增代码+Phase56RealScreenshotPipeline: 处理 pipeline 创建失败；如果没有这行代码，导入问题会变成堆栈。
                return {"captured": False, "screenshot_bytes_included": False, "pixel_guard_passed": False, "artifact_openable": False, "reason": f"Phase56 pipeline unavailable: {type(error).__name__}", "actions_expanded": PHASE55_ACTIONS_EXPANDED}  # 新增代码+Phase56RealScreenshotPipeline: 返回结构化不可用摘要；如果没有这行代码，调用方无法恢复。
        try:  # 新增代码+Phase56RealScreenshotPipeline: 捕获 pipeline 截图异常；如果没有这行代码，Win32 权限或坏窗口会杀死 worker。
            result = pipeline.capture_window(window)  # 新增代码+Phase56RealScreenshotPipeline: 执行真实截图 pipeline；如果没有这行代码，helper v2 不会生成 artifact。
        except Exception as error:  # 新增代码+Phase56RealScreenshotPipeline: 处理截图异常；如果没有这行代码，provider 异常会拖垮 helper。
            return {"captured": False, "screenshot_bytes_included": False, "pixel_guard_passed": False, "artifact_openable": False, "reason": f"Phase56 pipeline capture failed: {type(error).__name__}", "actions_expanded": PHASE55_ACTIONS_EXPANDED}  # 新增代码+Phase56RealScreenshotPipeline: 返回结构化截图失败摘要；如果没有这行代码，调用方只能看到崩溃。
        summary = dict(result) if isinstance(result, dict) else {"captured": False, "reason": "Phase56 pipeline returned non-dict result."}  # 新增代码+Phase56RealScreenshotPipeline: 只接受 dict 结果并兜底；如果没有这行代码，坏返回会污染协议。
        summary.pop("screenshot_bytes", None)  # 新增代码+Phase56RealScreenshotPipeline: 删除可能存在的原始截图 bytes；如果没有这行代码，大图可能进入 JSONL。
        summary.pop("raw_bytes", None)  # 新增代码+Phase56RealScreenshotPipeline: 删除兼容字段 raw_bytes；如果没有这行代码，未来 provider 换字段名仍可能泄露。
        summary["screenshot_bytes_included"] = False  # 新增代码+Phase56RealScreenshotPipeline: 明确响应不含原始 bytes；如果没有这行代码，安全审计无法稳定判断。
        summary["actions_expanded"] = PHASE55_ACTIONS_EXPANDED  # 新增代码+Phase56RealScreenshotPipeline: 保持 helper v2 动作面未扩大；如果没有这行代码，截图接入可能被误解为动作放开。
        return summary  # 新增代码+Phase56RealScreenshotPipeline: 返回脱敏截图摘要；如果没有这行代码，capture_window 没有结果。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，WindowsNativeHelperV2Worker._capture_window_summary 到此结束；如果没有这个边界说明，初学者不容易看出 helper v2 截图摘要范围。
# 新增代码+Phase55WindowsNativeHelperV2: 类段结束，WindowsNativeHelperV2Worker 到此结束；如果没有这个边界说明，初学者不容易看出 worker 类范围。


class WindowsNativeHelperV2Client:  # 新增代码+Phase55WindowsNativeHelperV2: 类段开始，定义主进程侧 helper client；如果没有这个类，agent 无法安全启动和调用子进程 helper。
    def __init__(self, default_timeout_seconds: float = 3.0) -> None:  # 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，初始化 client；如果没有这段函数，client 没有超时配置和进程序列。
        self.default_timeout_seconds = float(default_timeout_seconds)  # 新增代码+Phase55WindowsNativeHelperV2: 保存默认请求超时；如果没有这行代码，worker 卡住时主 agent 也会卡住。
        self.process: subprocess.Popen[str] | None = None  # 新增代码+Phase55WindowsNativeHelperV2: 保存子进程对象；如果没有这行代码，client 无法复用 worker。
        self._request_id = 0  # 新增代码+Phase55WindowsNativeHelperV2: 保存请求序号；如果没有这行代码，日志无法关联请求响应。
        self._process_unavailable = False  # 新增代码+Phase55WindowsNativeHelperV2: 记录 worker 是否已经被判定不可用；如果没有这行代码，崩溃后的下一次请求可能仍误写坏管道。
    # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，WindowsNativeHelperV2Client.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _command(self) -> list[str]:  # 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，生成 worker 启动命令；如果没有这段函数，启动路径会散落在 start 里。
        return [sys.executable, "-m", "learning_agent.computer_use_mcp_v2.windows_runtime.native_helper_v2", "--worker"]  # 新增代码+Phase55WindowsNativeHelperV2: 使用当前解释器启动包模块 worker；如果没有这行代码，子进程可能用错 Python 环境。
    # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，WindowsNativeHelperV2Client._command 到此结束；如果没有这个边界说明，初学者不容易看出启动命令范围。

    def start(self) -> dict[str, Any]:  # 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，启动 helper 子进程并读取健康状态；如果没有这段函数，client 没有 out-of-process 生命周期入口。
        if self._process_unavailable:  # 新增代码+Phase55WindowsNativeHelperV2: 检查旧 worker 是否已经不可用；如果没有这行代码，重启时可能复用坏状态。
            self.close(kill=True)  # 新增代码+Phase55WindowsNativeHelperV2: 清理坏 worker 句柄；如果没有这行代码，新的 start 可能被旧管道影响。
            self._process_unavailable = False  # 新增代码+Phase55WindowsNativeHelperV2: 重置不可用标志；如果没有这行代码，新 worker 也会被误判为不可用。
        if self.process is not None and self.process.poll() is None:  # 新增代码+Phase55WindowsNativeHelperV2: 检查已有进程是否还活着；如果没有这行代码，重复 start 会启动多个 worker。
            return {"healthy": True, "pid": int(self.process.pid), "already_started": True}  # 新增代码+Phase55WindowsNativeHelperV2: 返回已有进程摘要；如果没有这行代码，调用方无法知道复用了 worker。
        worker_env = dict(os.environ)  # 新增代码+Phase55WindowsNativeHelperV2: 复制当前环境给子进程；如果没有这行代码，worker 会丢失 PYTHONPATH 等运行上下文。
        worker_env["PYTHONIOENCODING"] = "utf-8"  # 新增代码+Phase55WindowsNativeHelperV2: 强制 worker stdin/stdout 使用 UTF-8；如果没有这行代码，Windows 中文输出会按系统代码页写出导致父进程解码失败。
        self.process = subprocess.Popen(self._command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", bufsize=1, env=worker_env)  # 新增代码+Phase55WindowsNativeHelperV2: 启动真实 UTF-8 子进程 worker；如果没有这行代码，helper v2 仍只是进程内对象且中文协议可能乱码。
        status = self.request({"op": "status"}, timeout_seconds=5.0)  # 新增代码+Phase55WindowsNativeHelperV2: 启动后立即请求 status；如果没有这行代码，health 没有协议证据。
        result = dict(status.get("result", {})) if status.get("ok") else {}  # 新增代码+Phase55WindowsNativeHelperV2: 提取 status.result；如果没有这行代码，health 字段不稳定。
        return {"healthy": bool(status.get("ok") and result.get("healthy")), "pid": int(result.get("pid", self.process.pid if self.process else 0) or 0), "status": status}  # 新增代码+Phase55WindowsNativeHelperV2: 返回 health 摘要；如果没有这行代码，测试和终端看不到 pid/healthy。
    # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，WindowsNativeHelperV2Client.start 到此结束；如果没有这个边界说明，初学者不容易看出启动范围。

    def _readline_with_timeout(self, timeout_seconds: float) -> str | None:  # 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，用后台线程读取 stdout 并支持超时；如果没有这段函数，Windows 上阻塞 readline 无法限时。
        process = self.process  # 新增代码+Phase55WindowsNativeHelperV2: 保存进程引用；如果没有这行代码，线程闭包会反复访问可变属性。
        if process is None or process.stdout is None:  # 新增代码+Phase55WindowsNativeHelperV2: 检查 stdout 是否可读；如果没有这行代码，坏进程会触发 AttributeError。
            return None  # 新增代码+Phase55WindowsNativeHelperV2: 无 stdout 时返回 None；如果没有这行代码，调用方无法形成结构化错误。
        output_queue: queue.Queue[str] = queue.Queue(maxsize=1)  # 新增代码+Phase55WindowsNativeHelperV2: 创建结果队列；如果没有这行代码，后台线程无法把读取结果交回主线程。
        def reader() -> None:  # 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，后台读取一行 stdout；如果没有这段函数，主线程会阻塞在 readline。
            try:  # 新增代码+Phase55WindowsNativeHelperV2: 捕获 stdout 读取异常；如果没有这行代码，解码或管道错误会停在线程里导致主线程误判超时。
                output_queue.put(process.stdout.readline())  # 新增代码+Phase55WindowsNativeHelperV2: 读取响应行并放入队列；如果没有这行代码，主线程拿不到响应。
            except Exception:  # 新增代码+Phase55WindowsNativeHelperV2: 处理读取失败；如果没有这行代码，坏管道会留下未汇报的线程异常。
                output_queue.put("")  # 新增代码+Phase55WindowsNativeHelperV2: 用 EOF 语义通知主线程；如果没有这行代码，主线程不能把读取失败转成结构化错误。
        # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，reader 到此结束；如果没有这个边界说明，初学者不容易看出读取线程范围。
        thread = threading.Thread(target=reader, daemon=True)  # 新增代码+Phase55WindowsNativeHelperV2: 创建守护线程避免超时后阻塞退出；如果没有这行代码，超时线程可能阻止进程结束。
        thread.start()  # 新增代码+Phase55WindowsNativeHelperV2: 启动读取线程；如果没有这行代码，队列不会收到响应。
        try:  # 新增代码+Phase55WindowsNativeHelperV2: 捕获队列超时；如果没有这行代码，超时会变成异常堆栈。
            return output_queue.get(timeout=timeout_seconds)  # 新增代码+Phase55WindowsNativeHelperV2: 在限定时间内等待响应；如果没有这行代码，helper 卡住会拖住主 agent。
        except queue.Empty:  # 新增代码+Phase55WindowsNativeHelperV2: 处理超时未读到响应；如果没有这行代码，超时无法结构化返回。
            return None  # 新增代码+Phase55WindowsNativeHelperV2: 返回 None 表示超时；如果没有这行代码，调用方无法区分空响应和超时。
    # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，WindowsNativeHelperV2Client._readline_with_timeout 到此结束；如果没有这个边界说明，初学者不容易看出超时读取范围。

    def request(self, message: dict[str, Any], timeout_seconds: float | None = None) -> dict[str, Any]:  # 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，发送一条 JSONL 请求；如果没有这段函数，client 不能调用 helper 协议。
        process = self.process  # 新增代码+Phase55WindowsNativeHelperV2: 保存进程引用；如果没有这行代码，后续会反复访问可变属性。
        op = str((message or {}).get("op", "status"))  # 新增代码+Phase55WindowsNativeHelperV2: 读取 op 便于错误响应；如果没有这行代码，错误里不知道哪个请求失败。
        if self._process_unavailable:  # 新增代码+Phase55WindowsNativeHelperV2: 检查此前是否已经发现 worker 不可用；如果没有这行代码，崩溃后的后续请求还会继续打坏管道。
            return _error_response(op, "native_helper_v2_process_unavailable", "helper v2 子进程此前已不可用，需要重新 start。")  # 新增代码+Phase55WindowsNativeHelperV2: 稳定返回不可用错误；如果没有这行代码，上层无法决定重启 helper。
        if process is None or process.poll() is not None:  # 新增代码+Phase55WindowsNativeHelperV2: 检查进程是否不存在或已退出；如果没有这行代码，写管道会抛异常。
            self._process_unavailable = True  # 新增代码+Phase55WindowsNativeHelperV2: 标记进程不可用；如果没有这行代码，下一次请求可能继续尝试坏进程。
            return _error_response(op, "native_helper_v2_process_unavailable", "helper v2 子进程不可用，需要重新 start。")  # 新增代码+Phase55WindowsNativeHelperV2: 返回结构化不可用错误；如果没有这行代码，主 agent 会看到崩溃堆栈。
        if process.stdin is None or process.stdout is None:  # 新增代码+Phase55WindowsNativeHelperV2: 检查 stdio 管道是否存在；如果没有这行代码，坏 Popen 状态会触发 AttributeError。
            self._process_unavailable = True  # 新增代码+Phase55WindowsNativeHelperV2: 标记进程不可用；如果没有这行代码，后续会继续访问坏管道。
            return _error_response(op, "native_helper_v2_transport_error", "helper v2 stdio 管道不可用。")  # 新增代码+Phase55WindowsNativeHelperV2: 返回结构化传输错误；如果没有这行代码，调用方无法恢复。
        self._request_id += 1  # 新增代码+Phase55WindowsNativeHelperV2: 增加请求序号；如果没有这行代码，请求响应缺少关联 id。
        payload = dict(message or {})  # 新增代码+Phase55WindowsNativeHelperV2: 复制请求避免修改调用方对象；如果没有这行代码，外部 dict 会被污染。
        payload["id"] = self._request_id  # 新增代码+Phase55WindowsNativeHelperV2: 写入请求 id；如果没有这行代码，日志无法关联。
        try:  # 新增代码+Phase55WindowsNativeHelperV2: 捕获写入管道异常；如果没有这行代码，worker 崩溃会拖垮主 agent。
            process.stdin.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")  # 新增代码+Phase55WindowsNativeHelperV2: 写入 JSONL 请求；如果没有这行代码，worker 收不到命令。
            process.stdin.flush()  # 新增代码+Phase55WindowsNativeHelperV2: 立即刷新请求；如果没有这行代码，worker 可能迟迟不处理。
        except Exception:  # 新增代码+Phase55WindowsNativeHelperV2: 处理 BrokenPipe 等写入异常；如果没有这行代码，崩溃 worker 会抛到主 agent。
            self._process_unavailable = True  # 新增代码+Phase55WindowsNativeHelperV2: 标记 worker 不可用；如果没有这行代码，崩溃后的下一次请求不会稳定返回 process_unavailable。
            return _error_response(op, "native_helper_v2_transport_error", "helper v2 请求写入失败。")  # 新增代码+Phase55WindowsNativeHelperV2: 返回结构化写入错误；如果没有这行代码，调用方无法恢复。
        line = self._readline_with_timeout(float(timeout_seconds if timeout_seconds is not None else self.default_timeout_seconds))  # 新增代码+Phase55WindowsNativeHelperV2: 在超时内读取响应；如果没有这行代码，worker 卡住会卡住主 agent。
        if line is None:  # 新增代码+Phase55WindowsNativeHelperV2: 检查是否超时；如果没有这行代码，None 会进入 JSON 解析。
            return _error_response(op, "native_helper_v2_timeout", "helper v2 响应超时，主 agent 未崩溃。")  # 新增代码+Phase55WindowsNativeHelperV2: 返回结构化超时错误；如果没有这行代码，调用方无法触发恢复。
        if not line:  # 新增代码+Phase55WindowsNativeHelperV2: 检查 stdout 是否 EOF；如果没有这行代码，进程退出会被 JSON 解析成错误。
            self._process_unavailable = True  # 新增代码+Phase55WindowsNativeHelperV2: 标记 worker 已退出；如果没有这行代码，后续请求会继续尝试 EOF 管道。
            return _error_response(op, "native_helper_v2_process_exited", "helper v2 子进程已退出。")  # 新增代码+Phase55WindowsNativeHelperV2: 返回结构化进程退出错误；如果没有这行代码，崩溃恢复不可见。
        try:  # 新增代码+Phase55WindowsNativeHelperV2: 捕获响应 JSON 解析异常；如果没有这行代码，坏响应会拖垮主 agent。
            response = json.loads(line)  # 新增代码+Phase55WindowsNativeHelperV2: 解析 worker 响应；如果没有这行代码，client 无法读取结果。
            return dict(response) if isinstance(response, dict) else _error_response(op, "native_helper_v2_bad_response", "helper v2 返回了非对象 JSON。")  # 新增代码+Phase55WindowsNativeHelperV2: 返回响应或坏响应错误；如果没有这行代码，非 dict 响应会污染调用方。
        except Exception:  # 新增代码+Phase55WindowsNativeHelperV2: 处理 JSON 解析失败；如果没有这行代码，坏响应会抛异常。
            return _error_response(op, "native_helper_v2_bad_response", "helper v2 返回了不可解析 JSON。")  # 新增代码+Phase55WindowsNativeHelperV2: 返回结构化坏响应错误；如果没有这行代码，调用方无法恢复。
    # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，WindowsNativeHelperV2Client.request 到此结束；如果没有这个边界说明，初学者不容易看出请求范围。

    def close(self, kill: bool = False) -> None:  # 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，关闭 helper 子进程；如果没有这段函数，测试和生产 cleanup 可能残留 worker。
        process = self.process  # 新增代码+Phase55WindowsNativeHelperV2: 保存进程引用；如果没有这行代码，后续会反复访问可变属性。
        if process is None:  # 新增代码+Phase55WindowsNativeHelperV2: 没有进程时直接返回；如果没有这行代码，空 close 会触发异常。
            return  # 新增代码+Phase55WindowsNativeHelperV2: 结束空 close；如果没有这行代码，后续会访问 None。
        if process.poll() is None and not kill:  # 新增代码+Phase55WindowsNativeHelperV2: 若进程还活着且不强杀，先尝试 cleanup；如果没有这行代码，正常 close 会直接杀掉 worker。
            self.request({"op": "cleanup"}, timeout_seconds=1.0)  # 新增代码+Phase55WindowsNativeHelperV2: 发送 cleanup 请求；如果没有这行代码，worker 没有机会优雅退出。
        if process.poll() is None:  # 新增代码+Phase55WindowsNativeHelperV2: 检查 cleanup 后是否仍然存活；如果没有这行代码，残留进程不会被处理。
            process.kill() if kill else process.terminate()  # 新增代码+Phase55WindowsNativeHelperV2: 根据参数杀掉或终止进程；如果没有这行代码，worker 可能常驻后台。
        try:  # 新增代码+Phase55WindowsNativeHelperV2: 捕获等待退出异常；如果没有这行代码，清理慢会导致测试失败。
            process.wait(timeout=3)  # 新增代码+Phase55WindowsNativeHelperV2: 等待进程退出；如果没有这行代码，资源释放状态不确定。
        except Exception:  # 新增代码+Phase55WindowsNativeHelperV2: 处理等待超时或其他异常；如果没有这行代码，清理失败会抛出。
            pass  # 新增代码+Phase55WindowsNativeHelperV2: 忽略 close 阶段异常；如果没有这行代码，主流程可能被清理异常覆盖。
        self.process = None  # 新增代码+Phase55WindowsNativeHelperV2: 清空进程引用；如果没有这行代码，后续 request 会误用旧进程。
        self._process_unavailable = False  # 新增代码+Phase55WindowsNativeHelperV2: 清空不可用标志；如果没有这行代码，下一次 start 后仍可能被旧状态拦截。
        for stream in (process.stdin, process.stdout, process.stderr):  # 新增代码+Phase55WindowsNativeHelperV2: 遍历 stdio 句柄做资源回收；如果没有这行代码，Windows 测试会出现未关闭文件警告。
            if stream is None:  # 新增代码+Phase55WindowsNativeHelperV2: 跳过不存在的管道；如果没有这行代码，None.close 会触发异常。
                continue  # 新增代码+Phase55WindowsNativeHelperV2: 继续处理下一个管道；如果没有这行代码，空管道会中断清理。
            try:  # 新增代码+Phase55WindowsNativeHelperV2: 捕获关闭句柄异常；如果没有这行代码，清理错误会覆盖主流程结果。
                stream.close()  # 新增代码+Phase55WindowsNativeHelperV2: 关闭单个 stdio 句柄；如果没有这行代码，文件描述符可能残留。
            except Exception:  # 新增代码+Phase55WindowsNativeHelperV2: 忽略已经失效的句柄错误；如果没有这行代码，崩溃 worker 的关闭动作可能抛异常。
                pass  # 新增代码+Phase55WindowsNativeHelperV2: close 阶段保持兜底安静；如果没有这行代码，资源清理会影响验收输出。
    # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，WindowsNativeHelperV2Client.close 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。
# 新增代码+Phase55WindowsNativeHelperV2: 类段结束，WindowsNativeHelperV2Client 到此结束；如果没有这个边界说明，初学者不容易看出 client 类范围。


# 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，run_phase55_native_helper_v2_contract 执行 helper v2 合同自检；如果没有这段函数，CLI 和真实终端没有统一验收入口，作者意图是一次覆盖启动、消息、超时、崩溃和默认拒绝。
def run_phase55_native_helper_v2_contract() -> dict[str, Any]:  # 新增代码+Phase55WindowsNativeHelperV2: 定义 Phase55 合同入口；如果没有这行代码，自动化和终端场景无法调用本阶段自检。
    secret_text = "phase55-contract-hidden-secret"  # 新增代码+Phase55WindowsNativeHelperV2: 准备泄露检查文本；如果没有这行代码，raw_text_hidden 没有验证对象。
    client = WindowsNativeHelperV2Client()  # 新增代码+Phase55WindowsNativeHelperV2: 创建主 helper client；如果没有这行代码，合同无法启动子进程。
    try:  # 新增代码+Phase55WindowsNativeHelperV2: 确保主 helper 被清理；如果没有这行代码，自检失败时可能残留 worker。
        health = client.start()  # 新增代码+Phase55WindowsNativeHelperV2: 启动子进程并读取 health；如果没有这行代码，process_started 没有证据。
        status = client.request({"op": "status"})  # 新增代码+Phase55WindowsNativeHelperV2: 覆盖 status 消息；如果没有这行代码，messages 缺少健康分支。
        windows = client.request({"op": "list_windows"})  # 新增代码+Phase55WindowsNativeHelperV2: 覆盖 list_windows 消息；如果没有这行代码，messages 缺少窗口分支。
        capture = client.request({"op": "capture_window", "window": {"window_id": "hwnd:5501"}})  # 新增代码+Phase55WindowsNativeHelperV2: 覆盖 capture_window 消息；如果没有这行代码，messages 缺少截图分支。
        uia = client.request({"op": "read_uia_tree", "window": {"window_id": "hwnd:5501"}})  # 新增代码+Phase55WindowsNativeHelperV2: 覆盖 read_uia_tree 消息；如果没有这行代码，messages 缺少 UIA 分支。
        action = client.request({"op": "send_input", "action": "type_text", "text": secret_text})  # 新增代码+Phase55WindowsNativeHelperV2: 覆盖 send_input 默认拒绝；如果没有这行代码，send_input_refused 没有证据。
        hotkey = client.request({"op": "hotkey", "action": "status"})  # 新增代码+Phase55WindowsNativeHelperV2: 覆盖 hotkey 占位；如果没有这行代码，messages 缺少热键分支。
        cleanup = client.request({"op": "cleanup"})  # 新增代码+Phase55WindowsNativeHelperV2: 覆盖 cleanup 并优雅结束 worker；如果没有这行代码，生命周期清理没有证据。
    finally:  # 新增代码+Phase55WindowsNativeHelperV2: 无论主流程是否失败都清理 client；如果没有这行代码，worker 可能残留。
        client.close(kill=True)  # 新增代码+Phase55WindowsNativeHelperV2: 强制兜底关闭 worker；如果没有这行代码，失败路径可能留进程。
    timeout_client = WindowsNativeHelperV2Client(default_timeout_seconds=0.05)  # 新增代码+Phase55WindowsNativeHelperV2: 创建短超时 client；如果没有这行代码，timeout_handled 没有稳定输入。
    try:  # 新增代码+Phase55WindowsNativeHelperV2: 确保超时 worker 被杀；如果没有这行代码，睡眠 worker 可能残留。
        timeout_client.start()  # 新增代码+Phase55WindowsNativeHelperV2: 启动超时 worker；如果没有这行代码，debug_sleep 没有目标。
        timeout_result = timeout_client.request({"op": "debug_sleep", "seconds": 1})  # 新增代码+Phase55WindowsNativeHelperV2: 触发响应超时；如果没有这行代码，timeout_handled 无法验证。
    finally:  # 新增代码+Phase55WindowsNativeHelperV2: 无论超时结果如何都清理 worker；如果没有这行代码，后台进程会残留。
        timeout_client.close(kill=True)  # 新增代码+Phase55WindowsNativeHelperV2: 强制杀掉超时 worker；如果没有这行代码，自检会等到 sleep 结束。
    crash_client = WindowsNativeHelperV2Client()  # 新增代码+Phase55WindowsNativeHelperV2: 创建崩溃 client；如果没有这行代码，crash_handled 没有稳定输入。
    try:  # 新增代码+Phase55WindowsNativeHelperV2: 确保崩溃后清理句柄；如果没有这行代码，资源可能残留。
        crash_client.start()  # 新增代码+Phase55WindowsNativeHelperV2: 启动崩溃 worker；如果没有这行代码，debug_crash 没有目标。
        crash_result = crash_client.request({"op": "debug_crash"})  # 新增代码+Phase55WindowsNativeHelperV2: 触发 worker 退出；如果没有这行代码，crash_handled 无法验证。
        after_crash = crash_client.request({"op": "status"})  # 新增代码+Phase55WindowsNativeHelperV2: 崩溃后再次请求；如果没有这行代码，process_unavailable 无法验证。
    finally:  # 新增代码+Phase55WindowsNativeHelperV2: 无论崩溃断言如何都关闭 client；如果没有这行代码，句柄可能残留。
        crash_client.close(kill=True)  # 新增代码+Phase55WindowsNativeHelperV2: 强制兜底关闭崩溃 worker；如果没有这行代码，资源可能残留。
    serialized = json.dumps({"action": action, "capture": capture, "uia": uia}, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase55WindowsNativeHelperV2: 序列化主响应做泄露检查；如果没有这行代码，raw_text_hidden 无法机器验证。
    process_started = bool(health.get("healthy") and int(health.get("pid", 0) or 0) > 0)  # 新增代码+Phase55WindowsNativeHelperV2: 判断子进程是否启动；如果没有这行代码，进程内假对象可能误过。
    messages = bool(status.get("ok") and windows.get("ok") and capture.get("ok") and uia.get("ok") and hotkey.get("ok") and cleanup.get("ok"))  # 新增代码+Phase55WindowsNativeHelperV2: 汇总核心消息是否成功；如果没有这行代码，漏掉某个协议也可能误过。
    send_input_refused = bool(not action.get("ok") and action.get("error", {}).get("decision") == "real_action_refused_by_helper_v2")  # 新增代码+Phase55WindowsNativeHelperV2: 检查 send_input 默认拒绝；如果没有这行代码，真实动作安全门可能漏验。
    timeout_handled = bool(not timeout_result.get("ok") and timeout_result.get("error", {}).get("decision") == "native_helper_v2_timeout")  # 新增代码+Phase55WindowsNativeHelperV2: 检查超时结构化错误；如果没有这行代码，卡死恢复能力不可见。
    crash_handled = bool(not crash_result.get("ok") and not after_crash.get("ok") and after_crash.get("error", {}).get("decision") == "native_helper_v2_process_unavailable")  # 新增代码+Phase55WindowsNativeHelperV2: 检查崩溃后主 agent 仍拿到结构化错误；如果没有这行代码，崩溃恢复不可见。
    raw_text_hidden = secret_text not in serialized  # 新增代码+Phase55WindowsNativeHelperV2: 检查原始输入文本未泄露；如果没有这行代码，send_input 脱敏边界不可见。
    passed = bool(process_started and messages and send_input_refused and timeout_handled and crash_handled and raw_text_hidden and not PHASE55_ACTIONS_EXPANDED)  # 新增代码+Phase55WindowsNativeHelperV2: 汇总合同通过条件；如果没有这行代码，CLI 无法表达失败。
    return {"marker": PHASE55_WINDOWS_NATIVE_HELPER_V2_MARKER, "ok_token": PHASE55_WINDOWS_NATIVE_HELPER_V2_OK_TOKEN, "protocol": PHASE55_NATIVE_HELPER_V2_PROTOCOL, "version": PHASE55_NATIVE_HELPER_V2_VERSION, "process_started": process_started, "health": bool(health.get("healthy")), "messages": messages, "timeout_handled": timeout_handled, "crash_handled": crash_handled, "send_input_refused": send_input_refused, "raw_text_hidden": raw_text_hidden, "actions_expanded": PHASE55_ACTIONS_EXPANDED, "passed": passed, "health_report": health, "status": status, "timeout_result": timeout_result, "crash_result": crash_result, "after_crash": after_crash}  # 新增代码+Phase55WindowsNativeHelperV2: 返回完整合同报告；如果没有这行代码，测试和 CLI 拿不到结构化结果。
# 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，run_phase55_native_helper_v2_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


# 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，phase55_cli_line 把报告转成一行稳定 token；如果没有这段函数，真实终端场景需要解析复杂 JSON，作者意图是让最终回答可复制可验收。
def phase55_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase55WindowsNativeHelperV2: 定义 Phase55 CLI 行格式化函数；如果没有这行代码，main 无法打印固定顺序 token。
    return f"{PHASE55_WINDOWS_NATIVE_HELPER_V2_OK_TOKEN} process_started={_bool_token(report.get('process_started'))} health={_bool_token(report.get('health'))} messages={_bool_token(report.get('messages'))} timeout_handled={_bool_token(report.get('timeout_handled'))} crash_handled={_bool_token(report.get('crash_handled'))} send_input_refused={_bool_token(report.get('send_input_refused'))} raw_text_hidden={_bool_token(report.get('raw_text_hidden'))} actions_expanded={_bool_token(report.get('actions_expanded'))} marker={PHASE55_WINDOWS_NATIVE_HELPER_V2_MARKER}"  # 新增代码+Phase55WindowsNativeHelperV2: 返回固定顺序 token 行；如果没有这行代码，场景断言容易因为输出漂移失败。
# 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，phase55_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 文本范围。


# 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，main 负责 worker 模式和 CLI 自检模式分流；如果没有这段函数，子进程和终端验收无法共用同一模块。
def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase55WindowsNativeHelperV2: 定义命令行入口；如果没有这行代码，python -m 不能启动 worker 或自检。
    args = list(argv if argv is not None else sys.argv[1:])  # 新增代码+Phase55WindowsNativeHelperV2: 读取参数列表；如果没有这行代码，worker 模式无法识别 --worker。
    if "--worker" in args:  # 新增代码+Phase55WindowsNativeHelperV2: 判断是否作为子进程 worker 运行；如果没有这行代码，client 启动的进程会递归跑自检。
        return WindowsNativeHelperV2Worker().run_stdio_loop()  # 新增代码+Phase55WindowsNativeHelperV2: 运行 stdio JSONL loop；如果没有这行代码，worker 不会处理请求。
    report = run_phase55_native_helper_v2_contract()  # 新增代码+Phase55WindowsNativeHelperV2: 运行 Phase55 合同自检；如果没有这行代码，CLI 输出没有真实依据。
    print(phase55_cli_line(report))  # 新增代码+Phase55WindowsNativeHelperV2: 打印稳定单行 token；如果没有这行代码，验收器无法快速匹配结果。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase55WindowsNativeHelperV2: 打印结构化报告便于人工复盘；如果没有这行代码，失败时不容易定位哪项不合格。
    print(PHASE55_WINDOWS_NATIVE_HELPER_V2_MARKER)  # 新增代码+Phase55WindowsNativeHelperV2: 单独打印 ready marker；如果没有这行代码，真实终端验收可能看不到明确阶段标记。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase55WindowsNativeHelperV2: 根据合同结果返回退出码；如果没有这行代码，失败也可能被终端当成成功。
# 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


__all__ = ["PHASE55_NATIVE_HELPER_V2_PROTOCOL", "PHASE55_NATIVE_HELPER_V2_VERSION", "PHASE55_WINDOWS_NATIVE_HELPER_V2_MARKER", "PHASE55_WINDOWS_NATIVE_HELPER_V2_OK_TOKEN", "WindowsNativeHelperV2Client", "WindowsNativeHelperV2Worker", "main", "phase55_cli_line", "run_phase55_native_helper_v2_contract"]  # 新增代码+Phase55WindowsNativeHelperV2: 限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase55WindowsNativeHelperV2: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动 worker 或自检。
    raise SystemExit(main())  # 新增代码+Phase55WindowsNativeHelperV2: 调用 main 并传递退出码；如果没有这行代码，命令行退出状态不明确。
