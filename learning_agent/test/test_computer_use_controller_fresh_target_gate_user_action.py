"""测试 Computer Use controller 的 FreshTarget 通用门禁。"""  # 新增代码+FreshTargetControllerTest：说明本文件验证 controller 层的新目标硬门禁；如果没有这一行，读者不容易知道这些测试覆盖真实动作前入口。
from __future__ import annotations  # 新增代码+FreshTargetControllerTest：启用延迟类型注解；如果没有这一行，测试在旧解释路径中可能受导入顺序影响。

from typing import Any  # 新增代码+FreshTargetControllerTest：导入 Any 描述 fake 后端动态数据；如果没有这一行，测试 helper 的接口边界不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.controller import ComputerUseActionResult, ComputerUseController  # 新增代码+FreshTargetControllerTest：导入被测 controller 和结果类型；如果没有这一行，测试无法走真实安全链路。


class FreshTargetBackend:  # 新增代码+FreshTargetControllerTest：类段开始，提供可控窗口列表和零真实动作后端；如果没有这个类，测试会依赖用户真实桌面。
    def __init__(self, windows: list[dict[str, Any]] | None = None) -> None:  # 新增代码+FreshTargetControllerTest：函数段开始，保存预检窗口列表；如果没有这段函数，fake 后端没有状态。
        self.windows = [dict(window) for window in list(windows or [])]  # 新增代码+FreshTargetControllerTest：复制窗口列表；如果没有这一行，外部修改会污染测试。
        self.executions: list[dict[str, Any]] = []  # 新增代码+FreshTargetControllerTest：记录写动作执行；如果没有这一行，拒绝零事件无法断言。
        self.observations: list[dict[str, Any]] = []  # 新增代码+FreshTargetControllerTest：记录只读观察调用；如果没有这一行，预检是否运行不可见。
    # 新增代码+FreshTargetControllerTest：函数段结束，FreshTargetBackend.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+FreshTargetControllerTest：函数段开始，返回后端状态；如果没有这段函数，controller 审计会读取失败。
        return {"backend": "fresh_target_test_backend", "real_actions_enabled": False}  # 新增代码+FreshTargetControllerTest：声明测试后端不触碰真实桌面；如果没有这一行，审计无法证明零真实动作。
    # 新增代码+FreshTargetControllerTest：函数段结束，FreshTargetBackend.status 到此结束；如果没有这个边界说明，用户不容易看出状态范围。

    def observe(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+FreshTargetControllerTest：函数段开始，模拟 list_windows 和窗口校验；如果没有这段函数，预检和未知窗口门禁无法运行。
        self.observations.append({"action": action, "arguments": dict(arguments)})  # 新增代码+FreshTargetControllerTest：记录观察调用；如果没有这一行，测试无法确认预检读取了窗口列表。
        if action == "list_windows":  # 新增代码+FreshTargetControllerTest：处理启动前窗口列表；如果没有这一行，preflight 看不到已有窗口。
            return ComputerUseActionResult(True, "fresh target windows returned", {"windows": [dict(window) for window in self.windows]})  # 新增代码+FreshTargetControllerTest：返回可控窗口列表；如果没有这一行，已有窗口阻断无法测试。
        if action == "get_window_state":  # 新增代码+FreshTargetControllerTest：处理动作前窗口存在性验证；如果没有这一行，合法写动作会被未知窗口门禁误拒。
            return ComputerUseActionResult(True, "fresh target window alive", {"state": {"alive": True}})  # 新增代码+FreshTargetControllerTest：返回窗口存在；如果没有这一行，成功路径无法到达后端。
        return ComputerUseActionResult(False, "unsupported observe", {"action": action})  # 新增代码+FreshTargetControllerTest：拒绝未实现观察动作；如果没有这一行，坏动作可能静默通过。
    # 新增代码+FreshTargetControllerTest：函数段结束，FreshTargetBackend.observe 到此结束；如果没有这个边界说明，用户不容易看出观察范围。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+FreshTargetControllerTest：函数段开始，记录写动作但不触碰桌面；如果没有这段函数，测试不能安全验证后端是否被调用。
        self.executions.append({"action": action, "arguments": dict(arguments)})  # 新增代码+FreshTargetControllerTest：保存执行记录；如果没有这一行，拒绝路径无法证明后端未执行。
        return ComputerUseActionResult(True, "fresh target execute recorded", {"backend": "fresh_target_test_backend", "low_level_event_count": 1})  # 新增代码+FreshTargetControllerTest：返回模拟低层事件；如果没有这一行，成功路径无法证明动作到达后端。
    # 新增代码+FreshTargetControllerTest：函数段结束，FreshTargetBackend.execute 到此结束；如果没有这个边界说明，用户不容易看出执行范围。
# 新增代码+FreshTargetControllerTest：类段结束，FreshTargetBackend 到此结束；如果没有这个边界说明，用户不容易看出 fake 后端范围。


class SequenceTargetRuntime:  # 新增代码+FreshTargetControllerTest：类段开始，按顺序返回目标窗口；如果没有这个类，多目标测试无法稳定产生两个 target_ref。
    def __init__(self, windows: list[dict[str, Any]]) -> None:  # 新增代码+FreshTargetControllerTest：函数段开始，保存待返回窗口；如果没有这段函数，runtime 没有目标样本。
        self.windows = [dict(window) for window in windows]  # 新增代码+FreshTargetControllerTest：复制窗口列表；如果没有这一行，外部修改会污染启动报告。
        self.open_count = 0  # 新增代码+FreshTargetControllerTest：统计 open 调用次数；如果没有这一行，预检阻断是否跳过 runtime 不可见。
    # 新增代码+FreshTargetControllerTest：函数段结束，SequenceTargetRuntime.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def open_target_session(self, target_app: str, user_authorized_window: bool = False) -> dict[str, Any]:  # 新增代码+FreshTargetControllerTest：函数段开始，模拟通用目标 session；如果没有这段函数，controller launch_app 无法生成租约。
        window = dict(self.windows[min(self.open_count, len(self.windows) - 1)])  # 新增代码+FreshTargetControllerTest：按调用次数选择窗口；如果没有这一行，多目标测试不能得到不同窗口。
        self.open_count += 1  # 新增代码+FreshTargetControllerTest：增加启动计数；如果没有这一行，第二次启动仍会返回第一个窗口。
        return {  # 新增代码+FreshTargetControllerTest：返回 controller 需要的 session 报告；如果没有这一行，launch_app 没有结构化输入。
            "session_ready": True,  # 新增代码+FreshTargetControllerTest：声明 session 已就绪；如果没有这一行，controller 不会注册 target。
            "target_window": window,  # 新增代码+FreshTargetControllerTest：返回目标窗口；如果没有这一行，TargetLease 无法建立。
            "process_started": True,  # 新增代码+FreshTargetControllerTest：声明进程已启动；如果没有这一行，身份报告不完整。
            "process_id": int(window["pid"]),  # 新增代码+FreshTargetControllerTest：返回进程 pid；如果没有这一行，agent-owned 身份无法验证。
            "process_executable": str(window["process_name"]),  # 新增代码+FreshTargetControllerTest：返回进程名；如果没有这一行，身份校验会缺进程名称。
            "owned_process_registered": not user_authorized_window,  # 新增代码+FreshTargetControllerTest：授权旧窗口时不伪装成自有进程；如果没有这一行，旧窗口授权和自启动会混淆。
            "fresh_target_decision": "user_granted_existing_window_ready" if user_authorized_window else "fresh_target_ready",  # 新增代码+FreshTargetControllerTest：返回 FreshTarget 决策；如果没有这一行，租约会缺启动来源。
            "fresh_target_class": "user_granted_existing_window" if user_authorized_window else "fresh_agent_owned_window",  # 新增代码+FreshTargetControllerTest：返回目标分类；如果没有这一行，审计看不出目标类型。
            "fresh_target_identity_verified": True,  # 新增代码+FreshTargetControllerTest：声明新鲜度已验证；如果没有这一行，租约字段会是弱证据。
            "target_window_existed_before_launch": bool(user_authorized_window),  # 新增代码+FreshTargetControllerTest：授权旧窗口时标记启动前已存在；如果没有这一行，授权路径缺少旧窗口事实。
            "real_desktop_touched": False,  # 新增代码+FreshTargetControllerTest：声明测试不触碰真实桌面；如果没有这一行，验收会误解自动测试。
            "low_level_event_count": 0,  # 新增代码+FreshTargetControllerTest：声明启动模拟零输入事件；如果没有这一行，门禁副作用不可审计。
        }  # 新增代码+FreshTargetControllerTest：结束 session 报告；如果没有这一行，Python 语法不完整。
    # 新增代码+FreshTargetControllerTest：函数段结束，SequenceTargetRuntime.open_target_session 到此结束；如果没有这个边界说明，用户不容易看出 fake runtime 范围。
# 新增代码+FreshTargetControllerTest：类段结束，SequenceTargetRuntime 到此结束；如果没有这个边界说明，用户不容易看出 runtime 范围。


def _window(app_id: str = "notepad.exe", pid: int = 301, hwnd: int = 401, title: str = "Untitled - Notepad") -> dict[str, Any]:  # 新增代码+FreshTargetControllerTest：函数段开始，生成标准窗口字典；如果没有这段函数，测试会重复写窗口字段。
    return {  # 新增代码+FreshTargetControllerTest：返回窗口事实；如果没有这一行，测试没有 target_window。
        "app_id": app_id,  # 新增代码+FreshTargetControllerTest：保存应用身份；如果没有这一行，预检无法匹配目标软件。
        "process_name": app_id,  # 新增代码+FreshTargetControllerTest：保存进程名；如果没有这一行，TargetLease 无法验证进程。
        "pid": pid,  # 新增代码+FreshTargetControllerTest：保存进程 id；如果没有这一行，漂移判断没有 pid 基准。
        "window_process_id": pid,  # 新增代码+FreshTargetControllerTest：保存窗口进程 id；如果没有这一行，不同模块字段读取可能不一致。
        "hwnd": hwnd,  # 新增代码+FreshTargetControllerTest：保存窗口句柄；如果没有这一行，窗口身份无法稳定比较。
        "window_id": f"hwnd:{hwnd}",  # 新增代码+FreshTargetControllerTest：保存协议窗口 id；如果没有这一行，target_ref 无法还原窗口。
        "title_preview": title,  # 新增代码+FreshTargetControllerTest：保存标题摘要；如果没有这一行，用户看不懂报告目标。
        "title": title,  # 新增代码+FreshTargetControllerTest：保存完整标题；如果没有这一行，标题哈希无法生成。
    }  # 新增代码+FreshTargetControllerTest：结束窗口字典；如果没有这一行，Python 语法不完整。
# 新增代码+FreshTargetControllerTest：函数段结束，_window 到此结束；如果没有这个边界说明，用户不容易看出窗口夹具范围。


def test_launch_app_preflight_blocks_existing_window_before_runtime() -> None:  # 新增代码+FreshTargetControllerTest：函数段开始，验证已有窗口在 runtime 前被阻断；如果没有这段测试，旧窗口可能被默认接管。
    existing = _window(title="Old user note - Notepad")  # 新增代码+FreshTargetControllerTest：构造已打开 Notepad；如果没有这一行，预检阻断场景不存在。
    backend = FreshTargetBackend([existing])  # 新增代码+FreshTargetControllerTest：让预检看到已有窗口；如果没有这一行，controller 会认为桌面为空。
    runtime = SequenceTargetRuntime([_window(pid=999, hwnd=1000)])  # 新增代码+FreshTargetControllerTest：准备不应被调用的 runtime；如果没有这一行，无法断言预检阻断位置。
    controller = ComputerUseController(backend=backend, owner_session_id="fresh-preflight-test", target_session_runtime=runtime)  # 新增代码+FreshTargetControllerTest：装配被测 controller；如果没有这一行，测试没有执行主体。
    result = controller.execute({"action": "launch_app", "app_name": "notepad", "confirm_desktop_control": True})  # 新增代码+FreshTargetControllerTest：尝试启动已有应用；如果没有这一行，预检不会运行。
    assert result.ok is False  # 新增代码+FreshTargetControllerTest：确认已有窗口默认拒绝；如果没有这一行，危险放行不会被发现。
    assert runtime.open_count == 0  # 新增代码+FreshTargetControllerTest：确认拒绝发生在打开应用前；如果没有这一行，预检可能太晚。
    assert result.data["fresh_target_decision"] == "existing_target_window_requires_user_close_or_authorize"  # 新增代码+FreshTargetControllerTest：确认拒绝原因稳定；如果没有这一行，用户不知道要关闭或授权。
    assert result.data["low_level_event_count"] == 0  # 新增代码+FreshTargetControllerTest：确认拒绝路径零事件；如果没有这一行，阻断可能已经触碰桌面。
    assert result.data["actionability_marker"] == "OPENHARNESS_DESKTOP_USER_ACTION_REQUIRED"  # 新增代码+FreshTargetUserAction：确认 controller 输出用户动作 marker；如果没有这一行，旧窗口拒绝不会触发上层终止收敛。
    assert result.data["retry_launch_allowed"] is False  # 新增代码+FreshTargetUserAction：确认拒绝后不允许继续默认重试启动；如果没有这一行，模型会重复 open_application。
    assert result.data["recovery_next_allowed_actions"] == ["ask_user_to_close_or_authorize"]  # 新增代码+FreshTargetUserAction：确认恢复路径是问用户关闭或授权；如果没有这一行，工具层会继续建议 observe 或 launch。
    assert "OPENHARNESS_DESKTOP_USER_ACTION_REQUIRED" in result.message  # 新增代码+FreshTargetUserAction：确认 marker 出现在 legacy 文本里；如果没有这一行，mcp_session_adapter 只传文本时上层无法解析。
# 新增代码+FreshTargetControllerTest：函数段结束，test_launch_app_preflight_blocks_existing_window_before_runtime 到此结束；如果没有这个边界说明，用户不容易看出预检拒绝范围。


def test_launch_app_allows_user_granted_existing_window() -> None:  # 新增代码+FreshTargetControllerTest：函数段开始，验证明确授权已有窗口可用；如果没有这段测试，微信类单窗口应用会被永久卡住。
    existing = _window(app_id="Weixin.exe", pid=501, hwnd=601, title="微信")  # 新增代码+FreshTargetControllerTest：构造已有微信窗口；如果没有这一行，授权旧窗口场景不存在。
    backend = FreshTargetBackend([existing])  # 新增代码+FreshTargetControllerTest：让预检看到已有窗口；如果没有这一行，授权路径没有旧窗口事实。
    runtime = SequenceTargetRuntime([existing])  # 新增代码+FreshTargetControllerTest：让 runtime 绑定同一已有窗口；如果没有这一行，租约没有目标。
    controller = ComputerUseController(backend=backend, owner_session_id="fresh-grant-test", target_session_runtime=runtime)  # 新增代码+FreshTargetControllerTest：装配 controller；如果没有这一行，测试无法运行。
    result = controller.execute({"action": "launch_app", "app_name": "wechat", "explicit_existing_window_request": True, "user_authorized_window": True, "confirm_desktop_control": True})  # 新增代码+FreshTargetControllerTest：显式授权已有窗口；如果没有这一行，策略应该继续拒绝。
    assert result.ok is True  # 新增代码+FreshTargetControllerTest：确认授权旧窗口可进入控制；如果没有这一行，合法用户授权路径不可用。
    assert result.data["target_lease"]["origin"] == "user_granted_existing_window"  # 新增代码+FreshTargetControllerTest：确认租约来源记录为用户授权；如果没有这一行，审计会混淆旧窗口和自启动。
    assert result.data["target_window_existed_before_launch"] is True  # 新增代码+FreshTargetControllerTest：确认报告保留旧窗口事实；如果没有这一行，用户看不到这是授权旧窗口。
# 新增代码+FreshTargetControllerTest：函数段结束，test_launch_app_allows_user_granted_existing_window 到此结束；如果没有这个边界说明，用户不容易看出授权范围。


def test_multiple_registered_targets_require_explicit_target_ref() -> None:  # 新增代码+FreshTargetControllerTest：函数段开始，验证多目标时不能隐式操作；如果没有这段测试，复杂任务会误用最近窗口。
    backend = FreshTargetBackend([])  # 新增代码+FreshTargetControllerTest：使用空桌面预检避免阻断启动；如果没有这一行，launch_app 可能被旧窗口预检影响。
    runtime = SequenceTargetRuntime([_window(pid=701, hwnd=801, title="One - App"), _window(app_id="mspaint.exe", pid=702, hwnd=802, title="Two - Paint")])  # 新增代码+FreshTargetControllerTest：准备两个不同目标窗口；如果没有这一行，多目标歧义不存在。
    controller = ComputerUseController(backend=backend, owner_session_id="fresh-multi-test", target_session_runtime=runtime)  # 新增代码+FreshTargetControllerTest：装配 controller；如果没有这一行，测试没有执行主体。
    controller.execute({"action": "launch_app", "app_name": "notepad", "confirm_desktop_control": True})  # 新增代码+FreshTargetControllerTest：注册第一个目标；如果没有这一行，registry 只有一个目标。
    controller.execute({"action": "launch_app", "app_name": "mspaint", "confirm_desktop_control": True})  # 新增代码+FreshTargetControllerTest：注册第二个目标；如果没有这一行，多目标门禁不会触发。
    result = controller.execute({"action": "type_text", "text": "hello", "confirm_desktop_control": True})  # 新增代码+FreshTargetControllerTest：故意不传 target_ref；如果没有这一行，歧义拒绝路径没有覆盖。
    assert result.ok is False  # 新增代码+FreshTargetControllerTest：确认多目标漏 target_ref 被拒绝；如果没有这一行，动作可能打到错误窗口。
    assert result.data["target_resolution_error"] == "multiple_active_targets_require_target_ref"  # 新增代码+FreshTargetControllerTest：确认拒绝原因稳定；如果没有这一行，模型不知道要补 target_ref。
    assert backend.executions == []  # 新增代码+FreshTargetControllerTest：确认后端没有收到写动作；如果没有这一行，拒绝可能发生太晚。
# 新增代码+FreshTargetControllerTest：函数段结束，test_multiple_registered_targets_require_explicit_target_ref 到此结束；如果没有这个边界说明，用户不容易看出多目标范围。


def test_drift_rejection_invalidates_target_ref_and_active_lease() -> None:  # 新增代码+FreshTargetControllerTest：函数段开始，验证漂移拒绝后 target_ref 失效；如果没有这段测试，坏引用可能被反复重试。
    backend = FreshTargetBackend([])  # 新增代码+FreshTargetControllerTest：使用空桌面预检；如果没有这一行，launch_app 可能被已有窗口阻断。
    controlled = _window(pid=901, hwnd=902, title="1.txt - Notepad")  # 新增代码+FreshTargetControllerTest：构造本轮受控窗口；如果没有这一行，租约没有正确基准。
    drifted = _window(pid=999, hwnd=998, title="Old unrelated Notepad")  # 新增代码+FreshTargetControllerTest：构造同应用不同窗口；如果没有这一行，漂移拒绝没有样本。
    controller = ComputerUseController(backend=backend, owner_session_id="fresh-drift-test", target_session_runtime=SequenceTargetRuntime([controlled]))  # 新增代码+FreshTargetControllerTest：装配带受控窗口的 controller；如果没有这一行，测试无法建立 target_ref。
    launch = controller.execute({"action": "launch_app", "app_name": "notepad", "confirm_desktop_control": True})  # 新增代码+FreshTargetControllerTest：先建立 target_ref 和租约；如果没有这一行，漂移没有目标基准。
    result = controller.execute({"action": "type_text", "target_ref": launch.data["target_ref"], "window": drifted, "text": "hello", "confirm_desktop_control": True})  # 新增代码+FreshTargetControllerTest：用正确 target_ref 搭配错误窗口；如果没有这一行，冲突窗口风险不被覆盖。
    resolved_after = controller.target_registry.resolve_target_ref(launch.data["target_ref"])  # 新增代码+FreshTargetControllerTest：漂移拒绝后再次解析 target_ref；如果没有这一行，失效状态无法断言。
    assert result.ok is False  # 新增代码+FreshTargetControllerTest：确认漂移动作被拒绝；如果没有这一行，错窗口会进入后端。
    assert result.data["target_invalidated"]["invalidated"] is True  # 新增代码+FreshTargetControllerTest：确认拒绝后 target 已失效；如果没有这一行，坏 ref 可能继续可用。
    assert resolved_after["decision"] == "target_ref_invalidated"  # 新增代码+FreshTargetControllerTest：确认 registry 之后拒绝该 ref；如果没有这一行，下一步仍可能复用旧目标。
    assert controller.active_target_lease == {}  # 新增代码+FreshTargetControllerTest：确认 active lease 被清空；如果没有这一行，显式 window 路径仍可能借旧租约。
    assert backend.executions == []  # 新增代码+FreshTargetControllerTest：确认后端没有执行写动作；如果没有这一行，零事件拒绝不可证明。
# 新增代码+FreshTargetControllerTest：函数段结束，test_drift_rejection_invalidates_target_ref_and_active_lease 到此结束；如果没有这个边界说明，用户不容易看出漂移失效范围。
