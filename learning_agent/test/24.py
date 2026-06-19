"""测试 Computer Use controller 的通用目标租约门禁。"""  # 新增代码+ControllerTargetLease：说明本文件验证 controller 的通用 TargetLease 门禁；如果没有这一行，读者不容易知道这些测试不是 Notepad 专用补丁。

from __future__ import annotations  # 新增代码+ControllerTargetLease：启用延迟类型解析；如果没有这一行，测试里的类型注解在旧解释顺序下更容易导入失败。

from typing import Any  # 新增代码+ControllerTargetLease：导入 Any 描述假后端的 JSON 风格数据；如果没有这一行，测试 helper 的边界不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.controller import ComputerUseActionResult, ComputerUseController  # 新增代码+ControllerTargetLease：导入被测 controller 和统一结果对象；如果没有这一行，测试无法走真实 controller 门禁链路。


class RecordingBackend:  # 新增代码+ControllerTargetLease：类段开始，提供不碰真实桌面的记录型后端；如果没有这个类，测试可能误触发真实鼠标键盘。
    def __init__(self) -> None:  # 新增代码+ControllerTargetLease：函数段开始，初始化记录列表；如果没有这段函数，测试无法确认后端是否被调用。
        self.executions: list[dict[str, Any]] = []  # 新增代码+ControllerTargetLease：保存后端执行记录；如果没有这一行，零事件拒绝无法被断言。
        self.observations: list[dict[str, Any]] = []  # 新增代码+ControllerTargetLease：保存只读观察记录；如果没有这一行，测试无法证明窗口校验只读发生。
    # 新增代码+ControllerTargetLease：函数段结束，RecordingBackend.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+ControllerTargetLease：函数段开始，提供 controller 需要的后端状态；如果没有这段函数，审计记录会因缺少 status 崩溃。
        return {"backend": "recording_backend", "real_actions_enabled": False}  # 新增代码+ControllerTargetLease：返回假后端身份和零真实动作状态；如果没有这一行，审计无法说明测试没有触碰桌面。
    # 新增代码+ControllerTargetLease：函数段结束，RecordingBackend.status 到此结束；如果没有这个边界说明，读者不容易看出状态范围。

    def observe(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+ControllerTargetLease：函数段开始，模拟窗口存在性校验；如果没有这段函数，controller 的未知窗口门禁无法通过。
        self.observations.append({"action": action, "arguments": dict(arguments)})  # 新增代码+ControllerTargetLease：记录只读观察调用；如果没有这一行，测试无法排查是否越过了校验。
        return ComputerUseActionResult(True, "recording observe ok", {"backend": "recording_backend", "state": {"alive": True}})  # 新增代码+ControllerTargetLease：返回窗口仍存在；如果没有这一行，正常写动作会被窗口不存在门禁误拦。
    # 新增代码+ControllerTargetLease：函数段结束，RecordingBackend.observe 到此结束；如果没有这个边界说明，读者不容易看出观察范围。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+ControllerTargetLease：函数段开始，记录写动作而不执行真实输入；如果没有这段函数，测试不能安全覆盖写动作路径。
        self.executions.append({"action": action, "arguments": dict(arguments)})  # 新增代码+ControllerTargetLease：保存写动作调用；如果没有这一行，测试无法证明拒绝路径没有低层事件。
        return ComputerUseActionResult(True, "recording execute ok", {"backend": "recording_backend", "low_level_event_count": 1})  # 新增代码+ControllerTargetLease：返回一条模拟低层事件；如果没有这一行，成功路径无法证明动作真的到达后端。
    # 新增代码+ControllerTargetLease：函数段结束，RecordingBackend.execute 到此结束；如果没有这个边界说明，读者不容易看出执行范围。
# 新增代码+ControllerTargetLease：类段结束，RecordingBackend 到此结束；如果没有这个边界说明，读者不容易看出假后端范围。


class FakeTargetSessionRuntime:  # 新增代码+ControllerTargetLease：类段开始，提供不启动真实应用的 launch_app runtime；如果没有这个类，测试无法稳定生成 agent-owned 窗口。
    def __init__(self, target_window: dict[str, Any]) -> None:  # 新增代码+ControllerTargetLease：函数段开始，保存要返回的目标窗口；如果没有这段函数，测试无法控制窗口身份。
        self.target_window = dict(target_window)  # 新增代码+ControllerTargetLease：复制窗口避免外部修改污染 runtime；如果没有这一行，后续断言可能被共享对象影响。
        self.opened_targets: list[str] = []  # 新增代码+ControllerTargetLease：记录 launch_app 目标名；如果没有这一行，测试无法确认 controller 调用了 runtime。
    # 新增代码+ControllerTargetLease：函数段结束，FakeTargetSessionRuntime.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def open_target_session(self, target_app: str, user_authorized_window: bool = False) -> dict[str, Any]:  # 新增代码+ControllerTargetLease：函数段开始，模拟通用目标 session 绑定；如果没有这段函数，launch_app 无法产生 target_window。
        self.opened_targets.append(str(target_app))  # 新增代码+ControllerTargetLease：记录被请求的应用名；如果没有这一行，测试无法证明 app_name 解析正确。
        return {  # 新增代码+ControllerTargetLease：返回 controller 真实读取的 session 报告；如果没有这一行，launch_app 没有结构化输入。
            "session_ready": True,  # 新增代码+ControllerTargetLease：声明 session 已就绪；如果没有这一行，controller 会把启动当成失败。
            "target_window": dict(self.target_window),  # 新增代码+ControllerTargetLease：返回可控目标窗口；如果没有这一行，registry 和 lease 无法绑定窗口。
            "process_started": True,  # 新增代码+ControllerTargetLease：声明进程已启动；如果没有这一行，身份报告语义不完整。
            "process_id": int(self.target_window["pid"]),  # 新增代码+ControllerTargetLease：返回 agent 启动进程 pid；如果没有这一行，agent-owned 身份无法验证。
            "process_executable": str(self.target_window["process_name"]),  # 新增代码+ControllerTargetLease：返回进程名；如果没有这一行，进程和窗口无法交叉核对。
            "process_path_sha256_16": "notepadpathhash",  # 新增代码+ControllerTargetLease：返回脱敏路径指纹；如果没有这一行，租约报告缺少路径身份证据。
            "owned_process_registered": True,  # 新增代码+ControllerTargetLease：声明进程由 agent 登记拥有；如果没有这一行，existing window 会被误当成 agent-owned。
            "proxy_window_bound": True,  # 新增代码+ControllerTargetLease：声明代理窗口绑定成功；如果没有这一行，launch 结果里的绑定证据不完整。
            "proxy_window_binding": {"same_process": True},  # 新增代码+ControllerTargetLease：提供绑定细节；如果没有这一行，调试时看不到绑定依据。
            "window_binding_reason": "test_agent_owned_window",  # 新增代码+ControllerTargetLease：提供绑定原因；如果没有这一行，失败时不容易解释为什么选择这个窗口。
            "window_binding_confidence": "high",  # 新增代码+ControllerTargetLease：提供绑定置信度；如果没有这一行，报告缺少人工判断线索。
            "real_desktop_touched": False,  # 新增代码+ControllerTargetLease：声明测试不碰真实桌面；如果没有这一行，验收可能误判自动测试触碰用户桌面。
            "low_level_event_count": 0,  # 新增代码+ControllerTargetLease：声明启动模拟没有低层事件；如果没有这一行，门禁副作用不可审计。
            "user_authorized_window": bool(user_authorized_window),  # 新增代码+ControllerTargetLease：回显是否是用户授权旧窗口；如果没有这一行，测试无法验证授权分支。
        }  # 新增代码+ControllerTargetLease：结束 session 报告；如果没有这一行，Python 字典语法不完整。
    # 新增代码+ControllerTargetLease：函数段结束，FakeTargetSessionRuntime.open_target_session 到此结束；如果没有这个边界说明，读者不容易看出启动模拟范围。
# 新增代码+ControllerTargetLease：类段结束，FakeTargetSessionRuntime 到此结束；如果没有这个边界说明，读者不容易看出 fake runtime 范围。


def _window(pid: int = 401, hwnd: int = 402, title: str = "Untitled - Notepad") -> dict[str, Any]:  # 新增代码+ControllerTargetLease：函数段开始，生成可验证的通用窗口身份；如果没有这段函数，多个测试会重复手写易错字典。
    return {  # 新增代码+ControllerTargetLease：返回窗口字典；如果没有这一行，测试没有标准窗口输入。
        "app_id": "notepad.exe",  # 新增代码+ControllerTargetLease：声明应用身份；如果没有这一行，窗口引用不能区分不同应用。
        "process_name": "notepad.exe",  # 新增代码+ControllerTargetLease：声明窗口进程名；如果没有这一行，agent-owned 进程名验证会缺失。
        "window_id": f"hwnd:{hwnd}",  # 新增代码+ControllerTargetLease：声明稳定窗口 id；如果没有这一行，target_ref 解析后没有窗口身份。
        "hwnd": hwnd,  # 新增代码+ControllerTargetLease：声明窗口句柄；如果没有这一行，租约无法做 hwnd 级验证。
        "pid": pid,  # 新增代码+ControllerTargetLease：声明窗口所属进程；如果没有这一行，pid 漂移无法被检测。
        "title_preview": title,  # 新增代码+ControllerTargetLease：声明可读标题摘要；如果没有这一行，报告缺少人能看懂的窗口线索。
        "title": title,  # 新增代码+ControllerTargetLease：声明原始标题；如果没有这一行，标题哈希无法从完整标题生成。
        "bounds": {"left": 10, "top": 20, "width": 500, "height": 300},  # 新增代码+ControllerTargetLease：声明窗口区域；如果没有这一行，未来鼠标相对坐标测试缺少基准。
    }  # 新增代码+ControllerTargetLease：结束窗口字典；如果没有这一行，Python 字典语法不完整。
# 新增代码+ControllerTargetLease：函数段结束，_window 到此结束；如果没有这个边界说明，读者不容易看出窗口样本范围。


def _controller_with_runtime() -> tuple[ComputerUseController, RecordingBackend]:  # 新增代码+ControllerTargetLease：函数段开始，创建带假后端和假 runtime 的 controller；如果没有这段函数，每个测试都要重复复杂装配。
    backend = RecordingBackend()  # 新增代码+ControllerTargetLease：创建零真实动作后端；如果没有这一行，测试无法确认是否触达后端。
    runtime = FakeTargetSessionRuntime(_window())  # 新增代码+ControllerTargetLease：创建固定 agent-owned runtime；如果没有这一行，launch_app 没有目标窗口。
    controller = ComputerUseController(backend=backend, owner_session_id="lease-controller-test", target_session_runtime=runtime)  # 新增代码+ControllerTargetLease：注入假依赖并禁用生产锁默认落盘；如果没有这一行，测试会受真实系统状态影响。
    return controller, backend  # 新增代码+ControllerTargetLease：返回 controller 和后端记录器；如果没有这一行，测试拿不到被测对象和断言对象。
# 新增代码+ControllerTargetLease：函数段结束，_controller_with_runtime 到此结束；如果没有这个边界说明，读者不容易看出测试装配范围。


def test_launch_app_returns_verified_target_lease() -> None:  # 新增代码+ControllerTargetLease：函数段开始，验证 launch_app 会返回可审计 lease；如果没有这个测试，controller 可能只返回 target_ref 而没有权限来源。
    controller, _backend = _controller_with_runtime()  # 新增代码+ControllerTargetLease：创建被测 controller；如果没有这一行，测试没有执行主体。
    result = controller.execute({"action": "launch_app", "app_name": "notepad", "confirm_desktop_control": True})  # 新增代码+ControllerTargetLease：执行真实 controller 的 launch_app 路径；如果没有这一行，lease 创建路径没有被覆盖。
    assert result.ok is True  # 新增代码+ControllerTargetLease：确认启动模拟成功；如果没有这一行，后续 lease 断言可能基于失败结果误判。
    lease = result.data["target_lease"]  # 新增代码+ControllerTargetLease：读取 controller 应返回的租约；如果没有这一行，测试无法发现缺少 lease 的根因。
    assert lease["origin"] == "agent_owned_launch"  # 新增代码+ControllerTargetLease：确认租约来源是 agent 自启动；如果没有这一行，已有用户窗口可能被误归类。
    assert lease["lease_identity_verified"] is True  # 新增代码+ControllerTargetLease：确认首次绑定身份可信；如果没有这一行，坏租约也可能被后续动作使用。
    assert lease["low_level_event_count"] == 0  # 新增代码+ControllerTargetLease：确认创建租约不发送低层事件；如果没有这一行，门禁本身可能产生桌面副作用。
    active_target = controller.target_registry.get_active_target()  # 新增代码+ControllerTargetLease：读取 registry 中的 active target；如果没有这一行，测试无法确认 lease 被托管。
    assert active_target["lease"]["target_ref"] == result.data["target_ref"]  # 新增代码+ControllerTargetLease：确认 registry lease 和公开 target_ref 对齐；如果没有这一行，后续 target_ref 可能找不到正确租约。
# 新增代码+ControllerTargetLease：函数段结束，test_launch_app_returns_verified_target_lease 到此结束；如果没有这个边界说明，读者不容易看出本测试范围。


def test_write_action_with_target_ref_verifies_lease_and_reaches_backend() -> None:  # 新增代码+ControllerTargetLease：函数段开始，验证同一租约目标的写动作可以到达后端；如果没有这个测试，修复可能把所有写动作都误拒绝。
    controller, backend = _controller_with_runtime()  # 新增代码+ControllerTargetLease：创建被测 controller 和记录后端；如果没有这一行，测试没有断言对象。
    launch = controller.execute({"action": "launch_app", "app_name": "notepad", "confirm_desktop_control": True})  # 新增代码+ControllerTargetLease：先建立 target_ref 和 lease；如果没有这一行，写动作没有安全目标。
    result = controller.execute({"action": "type_text", "target_ref": launch.data["target_ref"], "text": "hello everyone", "confirm_desktop_control": True})  # 新增代码+ControllerTargetLease：通过 target_ref 发起写动作；如果没有这一行，controller 的 ref 解析和 lease 验证没有被覆盖。
    assert result.ok is True  # 新增代码+ControllerTargetLease：确认合法目标被允许；如果没有这一行，过严门禁会悄悄破坏正常 computer use。
    assert len(backend.executions) == 1  # 新增代码+ControllerTargetLease：确认后端正好收到一次写动作；如果没有这一行，成功结果可能只是表面成功。
    assert result.data["target_lease_verification"]["decision"] == "target_lease_verified"  # 新增代码+ControllerTargetLease：确认成功来自 lease 校验；如果没有这一行，旧漂移门禁可能假装覆盖了租约逻辑。
    assert result.data["target_lease_verification"]["low_level_event_count"] == 0  # 新增代码+ControllerTargetLease：确认租约验证本身零事件；如果没有这一行，安全校验可能触发真实输入。
# 新增代码+ControllerTargetLease：函数段结束，test_write_action_with_target_ref_verifies_lease_and_reaches_backend 到此结束；如果没有这个边界说明，读者不容易看出成功路径范围。


def test_write_action_rejects_registered_target_without_lease_before_backend() -> None:  # 新增代码+ControllerTargetLease：函数段开始，验证没有 lease 的 target_ref 不能写入；如果没有这个测试，旧 registry 记录可能绕过权限来源。
    backend = RecordingBackend()  # 新增代码+ControllerTargetLease：创建记录后端；如果没有这一行，测试无法证明拒绝时没有后端执行。
    controller = ComputerUseController(backend=backend, owner_session_id="lease-missing-test")  # 新增代码+ControllerTargetLease：创建不带 runtime 的 controller；如果没有这一行，测试无法模拟 legacy registry 记录。
    target_ref = controller.target_registry.register_target(_window(), source_action="legacy_test_without_lease")  # 新增代码+ControllerTargetLease：手动登记没有 lease 的目标；如果没有这一行，缺租约分支无法触发。
    result = controller.execute({"action": "type_text", "target_ref": target_ref, "text": "hello everyone", "confirm_desktop_control": True})  # 新增代码+ControllerTargetLease：尝试对无租约目标写入；如果没有这一行，controller 不会暴露缺租约风险。
    assert result.ok is False  # 新增代码+ControllerTargetLease：确认无租约目标被拒绝；如果没有这一行，危险放行不会被测试发现。
    assert backend.executions == []  # 新增代码+ControllerTargetLease：确认后端没有收到低层动作；如果没有这一行，拒绝结果可能仍然产生副作用。
    assert result.data["target_lease_verification"]["decision"] == "target_lease_missing"  # 新增代码+ControllerTargetLease：确认拒绝原因稳定可读；如果没有这一行，模型不知道该重新 launch_app 还是继续尝试。
    assert result.data["low_level_event_count"] == 0  # 新增代码+ControllerTargetLease：确认拒绝路径零底层事件；如果没有这一行，安全门禁可能已经晚于真实输入。
# 新增代码+ControllerTargetLease：函数段结束，test_write_action_rejects_registered_target_without_lease_before_backend 到此结束；如果没有这个边界说明，读者不容易看出缺租约范围。


def test_write_action_rejects_explicit_window_drift_with_lease_report() -> None:  # 新增代码+ControllerTargetLease：函数段开始，验证显式错误窗口会被 lease 报告拒绝；如果没有这个测试，模型可能把动作漂移到用户旧窗口。
    controller, backend = _controller_with_runtime()  # 新增代码+ControllerTargetLease：创建被测 controller 和记录后端；如果没有这一行，测试没有执行主体。
    controller.execute({"action": "launch_app", "app_name": "notepad", "confirm_desktop_control": True})  # 新增代码+ControllerTargetLease：先建立 agent-owned lease；如果没有这一行，漂移比较没有基准。
    drift_window = _window(pid=999, hwnd=998, title="User Old Notepad")  # 新增代码+ControllerTargetLease：构造同应用但不同进程窗口；如果没有这一行，漂移风险样本不真实。
    result = controller.execute({"action": "type_text", "window": drift_window, "text": "hello everyone", "confirm_desktop_control": True})  # 新增代码+ControllerTargetLease：尝试显式操作漂移窗口；如果没有这一行，错误窗口拒绝路径没有被覆盖。
    assert result.ok is False  # 新增代码+ControllerTargetLease：确认漂移窗口被拒绝；如果没有这一行，错窗口输入风险不会暴露。
    assert backend.executions == []  # 新增代码+ControllerTargetLease：确认拒绝发生在后端执行前；如果没有这一行，用户窗口可能已经被输入。
    assert result.data["target_lease_verification"]["decision"] == "target_lease_drift_rejected"  # 新增代码+ControllerTargetLease：确认拒绝由租约漂移判断产生；如果没有这一行，旧门禁可能无法给出通用 lease 证据。
    assert result.data["target_drift_blocks_action"] is True  # 新增代码+ControllerTargetLease：确认动作被漂移门禁阻断；如果没有这一行，报告缺少压力测试需要的硬指标。
    assert result.data["low_level_event_count"] == 0  # 新增代码+ControllerTargetLease：确认漂移拒绝零低层事件；如果没有这一行，压力测试无法证明错窗口零动作。
# 新增代码+ControllerTargetLease：函数段结束，test_write_action_rejects_explicit_window_drift_with_lease_report 到此结束；如果没有这个边界说明，读者不容易看出漂移拒绝范围。
def test_restored_unrelated_notepad_window_is_rejected_by_generic_lease_gate() -> None:  # 新增代码+NotepadRegressionLease：函数段开始，验证 restored 旧 Notepad 会被通用 lease 拒绝；如果没有这个测试，修复可能退化成 Notepad 专用补丁或忽略冲突 window。
    backend = RecordingBackend()  # 新增代码+NotepadRegressionLease：创建记录后端；如果没有这一行，测试无法证明拒绝时后端零执行。
    controlled_window = _window(pid=111, hwnd=222, title="1.txt - Notepad")  # 新增代码+NotepadRegressionLease：构造 agent 本轮应控制的 Notepad；如果没有这一行，租约没有正确目标基准。
    restored_window = _window(pid=999, hwnd=333, title="Restored unrelated task note - Notepad")  # 新增代码+NotepadRegressionLease：构造用户旧 Notepad 窗口；如果没有这一行，漂移风险样本不存在。
    controlled_window["app_id"] = "notepad.exe"  # 新增代码+NotepadRegressionLease：把受控窗口标记为 Notepad；如果没有这一行，测试不能模拟用户压力提示的应用。
    controlled_window["process_name"] = "notepad.exe"  # 新增代码+NotepadRegressionLease：设置受控窗口进程名；如果没有这一行，agent-owned 身份无法匹配启动进程。
    restored_window["app_id"] = "notepad.exe"  # 新增代码+NotepadRegressionLease：把漂移窗口也标记为 Notepad；如果没有这一行，测试不是同应用错窗口场景。
    restored_window["process_name"] = "notepad.exe"  # 新增代码+NotepadRegressionLease：设置漂移窗口进程名；如果没有这一行，测试无法证明同应用不同进程也会被拒绝。
    controller = ComputerUseController(backend=backend, target_session_runtime=FakeTargetSessionRuntime(controlled_window))  # 新增代码+NotepadRegressionLease：用通用 fake runtime 绑定受控窗口；如果没有这一行，测试会依赖真实 Notepad。
    launch = controller.execute({"action": "launch_app", "app_name": "notepad", "confirm_desktop_control": True})  # 新增代码+NotepadRegressionLease：建立本轮 target_ref 和 TargetLease；如果没有这一行，漂移比较没有租约基准。
    result = controller.execute({"action": "type_text", "text": "hello everyone", "confirm_desktop_control": True, "target_ref": launch.data["target_ref"], "window": restored_window})  # 新增代码+NotepadRegressionLease：同时传 target_ref 和错误旧窗口；如果没有这一行，无法覆盖模型混合参数导致的真实风险。
    assert result.ok is False  # 新增代码+NotepadRegressionLease：确认错误旧 Notepad 被拒绝；如果没有这一行，错窗口写入风险不会暴露。
    assert result.data["low_level_event_count"] == 0  # 新增代码+NotepadRegressionLease：确认拒绝路径零低层事件；如果没有这一行，可能已经触发真实输入后才报告失败。
    assert backend.executions == []  # 新增代码+NotepadRegressionLease：确认后端没有收到写动作；如果没有这一行，拒绝可能只是结果层包装。
    assert result.data["target_lease_verification"]["decision"] == "target_lease_drift_rejected"  # 新增代码+NotepadRegressionLease：确认拒绝来自通用 lease 漂移门禁；如果没有这一行，Notepad 专用逻辑可能混进核心路径。
# 新增代码+NotepadRegressionLease：函数段结束，test_restored_unrelated_notepad_window_is_rejected_by_generic_lease_gate 到此结束；如果没有这个边界说明，读者不容易看出 Notepad 只是回归样本。
def test_controller_clear_target_leases_removes_active_lease() -> None:  # 新增代码+TargetLeaseCleanup：函数段开始，验证 controller cleanup 会清空 active lease；如果没有这个测试，回合结束后旧租约可能影响下一轮任务。
    backend = RecordingBackend()  # 新增代码+TargetLeaseCleanup：创建记录后端；如果没有这一行，controller 无法初始化测试依赖。
    controller = ComputerUseController(backend=backend, target_session_runtime=FakeTargetSessionRuntime(_window()))  # 新增代码+TargetLeaseCleanup：创建带假 runtime 的 controller；如果没有这一行，测试无法建立 active lease。
    launch = controller.execute({"action": "launch_app", "app_name": "notepad", "confirm_desktop_control": True})  # 新增代码+TargetLeaseCleanup：建立 target_ref 和 active lease；如果没有这一行，清理前没有状态可验证。
    clear = controller.clear_target_leases()  # 新增代码+TargetLeaseCleanup：调用 controller 级清理入口；如果没有这一行，active lease 不会被测试覆盖。
    assert launch.ok is True  # 新增代码+TargetLeaseCleanup：确认清理前启动成功；如果没有这一行，后续清理断言可能基于空状态误判。
    assert clear["cleared"] is True  # 新增代码+TargetLeaseCleanup：确认 registry 报告已清理；如果没有这一行，清理结果可能无声失败。
    assert controller.target_registry.get_active_target() is None  # 新增代码+TargetLeaseCleanup：确认 active target 已清空；如果没有这一行，旧 target_ref 可能继续可解析。
    assert controller.active_target_lease == {}  # 新增代码+TargetLeaseCleanup：确认 active lease 已清空；如果没有这一行，显式 window 路径可能继续使用旧租约。
    assert controller.active_agent_owned_target_window == {}  # 新增代码+TargetLeaseCleanup：确认旧 agent-owned 窗口基准已清空；如果没有这一行，旧漂移门禁会影响新任务。
# 新增代码+TargetLeaseCleanup：函数段结束，test_controller_clear_target_leases_removes_active_lease 到此结束；如果没有这个边界说明，读者不容易看出 cleanup 覆盖范围。
