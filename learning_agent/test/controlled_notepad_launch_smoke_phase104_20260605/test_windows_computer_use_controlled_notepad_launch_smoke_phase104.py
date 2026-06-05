import tempfile  # 新增代码+Phase104ControlledNotepadLaunchSmoke：导入临时目录工具隔离 Phase104 报告；如果没有这行代码，测试会污染真实 memory。
import unittest  # 新增代码+Phase104ControlledNotepadLaunchSmoke：导入 unittest 沿用项目现有测试框架；如果没有这行代码，标准测试发现器找不到这些用例。
from pathlib import Path  # 新增代码+Phase104ControlledNotepadLaunchSmoke：导入 Path 统一处理 Windows 路径；如果没有这行代码，临时文件路径拼接会更脆弱。

from learning_agent.computer_use.controlled_notepad_launch_smoke import PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_MARKER, PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_OK_TOKEN, Phase104VisibleWindowProbe, WindowsControlledNotepadLaunchSmoke, phase104_cli_line, run_phase104_controlled_notepad_launch_smoke_contract  # 修改代码+Phase104ControlledNotepadLaunchSmoke：额外导入真实窗口探测器以覆盖 Windows 11 Notepad 代理 pid 场景；如果没有这行代码，回归测试无法直接验证窗口匹配根因。


class Phase104FakeProcess:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：类段开始，提供测试进程替身；如果没有这个类，单元测试可能需要真的打开 Notepad。
    def __init__(self, pid: int = 10401) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，初始化 fake 进程；如果没有这段函数，测试无法稳定设置进程号。
        self.pid = int(pid)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：保存进程号；如果没有这行代码，进程归属验证没有对象。
        self.terminated = False  # 新增代码+Phase104ControlledNotepadLaunchSmoke：记录是否被清理；如果没有这行代码，测试无法证明 cleanup 调用发生。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeProcess.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def poll(self) -> int | None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，模拟 subprocess.poll；如果没有这段函数，运行时无法判断 fake 进程是否仍活着。
        return 0 if self.terminated else None  # 新增代码+Phase104ControlledNotepadLaunchSmoke：已终止返回退出码，未终止返回 None；如果没有这行代码，清理前后状态不可测。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeProcess.poll 到此结束；如果没有这个边界说明，初学者不容易看出存活判断范围。

    def terminate(self) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，模拟终止进程；如果没有这段函数，cleanup 无法关闭 fake 进程。
        self.terminated = True  # 新增代码+Phase104ControlledNotepadLaunchSmoke：标记进程已终止；如果没有这行代码，残留进程检测会一直失败。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeProcess.terminate 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：类段结束，Phase104FakeProcess 到此结束；如果没有这个边界说明，初学者不容易看出 fake 进程范围。


class Phase104FakeLaunchBackend:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：类段开始，提供测试启动后端；如果没有这个类，单元测试无法安全证明后端桥接。
    def __init__(self) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，初始化 fake 后端；如果没有这段函数，测试无法记录调用和清理状态。
        self.process = Phase104FakeProcess()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建 fake 进程；如果没有这行代码，后端没有可归属的进程。
        self.processes = [self.process]  # 新增代码+Phase104ControlledNotepadLaunchSmoke：模拟 Phase103 后端的 processes 列表；如果没有这行代码，运行时无法用通用方式检查进程。
        self.launches: list[dict[str, object]] = []  # 新增代码+Phase104ControlledNotepadLaunchSmoke：保存启动计划；如果没有这行代码，测试无法确认只启动 Notepad。
        self.cleanup_called = False  # 新增代码+Phase104ControlledNotepadLaunchSmoke：记录 cleanup 是否被调用；如果没有这行代码，清理合同无法验证。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeLaunchBackend.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def launch(self, plan: dict[str, object]) -> dict[str, object]:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，模拟真实启动后端收到安全计划；如果没有这段函数，正向 smoke 没有后端证据。
        self.launches.append(dict(plan))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：记录计划副本；如果没有这行代码，测试无法检查 executable 和参数。
        return {"ok": True, "backend": "phase104_fake_launch_backend", "backend_launch_performed": True, "process_started": True, "process_id": self.process.pid, "real_desktop_touched": True, "cleanup_registered": True, "low_level_event_count": 0}  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回模拟真实启动结果；如果没有这行代码，运行时无法进入窗口和清理验证。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeLaunchBackend.launch 到此结束；如果没有这个边界说明，初学者不容易看出后端启动范围。

    def cleanup(self) -> dict[str, object]:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，模拟只清理本后端启动的进程；如果没有这段函数，运行时无法验证进程归属清理。
        self.cleanup_called = True  # 新增代码+Phase104ControlledNotepadLaunchSmoke：标记清理被调用；如果没有这行代码，测试无法发现漏清理。
        self.process.terminate()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：终止 fake 进程；如果没有这行代码，残留检测不会变为 false。
        return {"cleanup_attempted": True, "processes_cleaned": 1, "owned_process_only": True}  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回清理摘要；如果没有这行代码，报告无法证明只清理自有进程。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeLaunchBackend.cleanup 到此结束；如果没有这个边界说明，初学者不容易看出清理后端范围。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：类段结束，Phase104FakeLaunchBackend 到此结束；如果没有这个边界说明，初学者不容易看出 fake 后端范围。


class Phase104FakeInventorySnapshot:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：类段开始，提供最小窗口快照替身；如果没有这个类，窗口探测器测试需要真实 Win32 枚举结果。
    def __init__(self, windows: list[dict[str, object]]) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，保存 fake 窗口列表；如果没有这段函数，测试无法构造带 windows 字段的快照。
        self.windows = list(windows)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：复制窗口列表避免调用方后续修改污染快照；如果没有这行代码，测试证据可能被外部对象改动。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeInventorySnapshot.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出快照构造范围。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：类段结束，Phase104FakeInventorySnapshot 到此结束；如果没有这个边界说明，初学者不容易看出 fake 快照范围。


class Phase104FakeInventoryProbe:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：类段开始，按顺序返回 fake 快照；如果没有这个类，无法复现启动前后窗口变化。
    def __init__(self, snapshots: list[list[dict[str, object]]]) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，保存多帧窗口快照；如果没有这段函数，测试无法模拟窗口稍后出现。
        self.snapshots = [list(snapshot) for snapshot in snapshots]  # 新增代码+Phase104ControlledNotepadLaunchSmoke：复制每一帧窗口数据；如果没有这行代码，外部修改会让测试不稳定。
        self.calls = 0  # 新增代码+Phase104ControlledNotepadLaunchSmoke：记录 snapshot 调用次数；如果没有这行代码，测试无法确认探测器确实轮询过。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeInventoryProbe.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出 fake 枚举器初始化范围。
    def snapshot(self) -> Phase104FakeInventorySnapshot:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，返回当前 fake 快照；如果没有这段函数，真实探测器无法读取窗口列表。
        index = min(self.calls, max(0, len(self.snapshots) - 1))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：超过帧数后停在最后一帧；如果没有这行代码，轮询次数多时会越界。
        self.calls = self.calls + 1  # 新增代码+Phase104ControlledNotepadLaunchSmoke：递增调用次数模拟时间推进；如果没有这行代码，第二帧新窗口永远不会出现。
        return Phase104FakeInventorySnapshot(self.snapshots[index] if self.snapshots else [])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回 fake 快照对象；如果没有这行代码，窗口探测测试没有事实来源。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeInventoryProbe.snapshot 到此结束；如果没有这个边界说明，初学者不容易看出轮询范围。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：类段结束，Phase104FakeInventoryProbe 到此结束；如果没有这个边界说明，初学者不容易看出 fake 枚举器范围。


class Phase104FakeWindowProbe:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：类段开始，提供测试窗口探测器；如果没有这个类，单元测试会依赖真实桌面窗口。
    def __init__(self) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，初始化窗口探测记录；如果没有这段函数，测试无法确认探测参数。
        self.calls: list[dict[str, object]] = []  # 新增代码+Phase104ControlledNotepadLaunchSmoke：保存窗口探测调用；如果没有这行代码，进程号和标题提示无法断言。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeWindowProbe.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def wait_for_visible_window(self, process_id: int, title_hint: str, timeout_seconds: float = 8.0, baseline_window_keys: set[str] | None = None) -> dict[str, object]:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：兼容启动前窗口基线参数；如果没有这段函数，新增的真实窗口去重逻辑会让既有 fake 测试失效。
        self.calls.append({"process_id": int(process_id), "title_hint": str(title_hint), "timeout_seconds": float(timeout_seconds)})  # 新增代码+Phase104ControlledNotepadLaunchSmoke：记录调用参数；如果没有这行代码，测试无法确认按进程归属查窗口。
        return {"visible_window_verified": True, "window_identity": {"app_id": "notepad.exe", "process_id": int(process_id), "title_hint": str(title_hint), "visible": True}}  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回脱敏可见窗口身份；如果没有这行代码，正向 smoke 无法通过窗口验证。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeWindowProbe.wait_for_visible_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口探测范围。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：类段结束，Phase104FakeWindowProbe 到此结束；如果没有这个边界说明，初学者不容易看出 fake 探测器范围。


class Phase104FakeProxyWindowProbe:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：类段开始，模拟 Windows 11 Notepad 代理进程窗口；如果没有这个类，真实机器上的 pid 分离问题没有回归保护。
    def __init__(self) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，初始化代理窗口探测记录；如果没有这段函数，测试无法记录 close 是否发生。
        self.wait_calls: list[dict[str, object]] = []  # 新增代码+Phase104ControlledNotepadLaunchSmoke：保存等待窗口调用；如果没有这行代码，测试无法验证基线参数被传入。
        self.close_calls: list[dict[str, object]] = []  # 新增代码+Phase104ControlledNotepadLaunchSmoke：保存关闭窗口调用；如果没有这行代码，测试无法发现代理窗口残留。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeProxyWindowProbe.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。
    def wait_for_visible_window(self, process_id: int, title_hint: str, timeout_seconds: float = 8.0, baseline_window_keys: set[str] | None = None) -> dict[str, object]:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，返回与启动 pid 不同的可见 Notepad 窗口；如果没有这段函数，测试无法复现 Windows 11 代理行为。
        self.wait_calls.append({"process_id": int(process_id), "title_hint": str(title_hint), "baseline_window_keys": sorted(baseline_window_keys or set())})  # 新增代码+Phase104ControlledNotepadLaunchSmoke：记录等待参数；如果没有这行代码，测试无法确认启动前基线参与判断。
        return {"visible_window_verified": True, "window_identity": {"app_id": "notepad:pid:32000", "process_id": 32000, "window_id": "hwnd:10402", "title_preview": f"{title_hint} - Notepad", "visible": True, "new_window_after_launch": True, "window_pid_matches_launch_process": False}}  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回代理窗口身份；如果没有这行代码，清理逻辑无法识别需要关闭真实窗口。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeProxyWindowProbe.wait_for_visible_window 到此结束；如果没有这个边界说明，初学者不容易看出代理窗口等待范围。
    def close_verified_window(self, window_identity: dict[str, object], title_hint: str, baseline_window_keys: set[str] | None = None, timeout_seconds: float = 4.0) -> dict[str, object]:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，模拟关闭已验证代理窗口；如果没有这段函数，测试无法证明残留窗口被收尾。
        self.close_calls.append({"window_identity": dict(window_identity), "title_hint": str(title_hint), "baseline_window_keys": sorted(baseline_window_keys or set()), "timeout_seconds": float(timeout_seconds)})  # 新增代码+Phase104ControlledNotepadLaunchSmoke：记录关闭请求；如果没有这行代码，测试无法审计关闭范围。
        return {"window_cleanup_attempted": True, "window_cleanup_completed": True, "owned_window_only": True}  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回关闭成功摘要；如果没有这行代码，运行时无法把窗口清理纳入 cleanup_completed。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104FakeProxyWindowProbe.close_verified_window 到此结束；如果没有这个边界说明，初学者不容易看出关闭范围。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：类段结束，Phase104FakeProxyWindowProbe 到此结束；如果没有这个边界说明，初学者不容易看出代理窗口 fake 范围。


class WindowsComputerUseControlledNotepadLaunchSmokePhase104Tests(unittest.TestCase):  # 新增代码+Phase104ControlledNotepadLaunchSmoke：类段开始，集中验证 Phase104 受控 Notepad 启动 smoke；如果没有这个类，真实启动清理合同没有回归保护。
    def test_window_probe_accepts_new_controlled_notepad_window_when_pid_differs(self) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，验证 Windows 11 Notepad 代理 pid 不等于窗口 pid 时仍按新窗口证据通过；如果没有这段测试，本机真实失败会再次回归。
        title_hint = "phase104_controlled_notepad_launch_proxy_case.txt"  # 新增代码+Phase104ControlledNotepadLaunchSmoke：使用唯一受控文件名模拟真实标题；如果没有这行代码，测试可能与历史窗口混淆。
        baseline_window = {"window_id": "hwnd:old", "app_id": "notepad:pid:100", "class_name": "Notepad", "title_preview": "old.txt - Notepad", "pid": 100}  # 新增代码+Phase104ControlledNotepadLaunchSmoke：构造启动前已有 Notepad；如果没有这行代码，测试无法证明 baseline 过滤存在。
        proxy_window = {"window_id": "hwnd:new", "app_id": "notepad:pid:32000", "class_name": "Notepad", "title_preview": f"{title_hint} - Notepad", "pid": 32000}  # 新增代码+Phase104ControlledNotepadLaunchSmoke：构造启动后真实可见窗口但 pid 不同；如果没有这行代码，测试无法覆盖代理进程根因。
        probe = Phase104VisibleWindowProbe(inventory_probe=Phase104FakeInventoryProbe([[baseline_window], [baseline_window, proxy_window]]))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：注入两帧 fake 快照；如果没有这行代码，测试会依赖真实桌面。
        result = probe.wait_for_visible_window(10401, title_hint, timeout_seconds=0.3, baseline_window_keys={"hwnd:old"})  # 新增代码+Phase104ControlledNotepadLaunchSmoke：按启动 pid 和 baseline 查找窗口；如果没有这行代码，代理 pid 行为没有被执行。
        self.assertTrue(result["visible_window_verified"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言新窗口被验证；如果没有这行代码，过严 pid 匹配可能无人发现。
        self.assertFalse(result["window_identity"]["window_pid_matches_launch_process"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言窗口 pid 的确不同；如果没有这行代码，测试可能只覆盖普通同 pid 路径。
        self.assertTrue(result["window_identity"]["new_window_after_launch"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言通过的是启动后新窗口证据；如果没有这行代码，可能误认用户已有窗口。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，test_window_probe_accepts_new_controlled_notepad_window_when_pid_differs 到此结束；如果没有这个边界说明，初学者不容易看出代理窗口匹配测试范围。

    def test_proxy_notepad_window_is_closed_after_backend_wrapper_cleanup(self) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，验证代理窗口在后端 wrapper 清理后也要关闭；如果没有这段测试，真实桌面可能残留受控 Notepad 窗口。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建临时目录隔离报告；如果没有这行代码，测试会污染真实 memory。
            backend = Phase104FakeLaunchBackend()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建 fake 启动后端；如果没有这行代码，测试可能真实打开 Notepad。
            probe = Phase104FakeProxyWindowProbe()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建代理窗口 fake；如果没有这行代码，测试无法观察关闭调用。
            report = run_phase104_controlled_notepad_launch_smoke_contract(base_dir=Path(temp_dir), real_smoke=True, allow_real_gate=True, launch_backend=backend, window_probe=probe, platform="win32")  # 新增代码+Phase104ControlledNotepadLaunchSmoke：运行真实分支 fake 合同；如果没有这行代码，清理行为没有事实来源。
        self.assertTrue(report["passed"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言代理窗口合同通过；如果没有这行代码，新增清理字段可能没有进入总通过条件。
        self.assertTrue(report["cleanup_completed"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言总体清理完成；如果没有这行代码，残留窗口风险可能被掩盖。
        self.assertTrue(report["real_smoke_report"]["verified_window_cleanup_completed"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言已验证窗口被关闭；如果没有这行代码，只清理 wrapper 进程也会误过。
        self.assertEqual(probe.close_calls[0]["window_identity"]["process_id"], 32000)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言关闭的是代理窗口 pid；如果没有这行代码，可能误关启动 wrapper 或用户窗口。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，test_proxy_notepad_window_is_closed_after_backend_wrapper_cleanup 到此结束；如果没有这个边界说明，初学者不容易看出代理窗口清理测试范围。

    def test_default_off_does_not_call_launch_backend(self) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，验证默认关闭不启动 Notepad；如果没有这段测试，普通测试可能误触真实应用。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建临时目录隔离报告；如果没有这行代码，测试会污染项目 memory。
            backend = Phase104FakeLaunchBackend()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建 fake 后端；如果没有这行代码，无法证明默认关闭未调用后端。
            probe = Phase104FakeWindowProbe()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建 fake 窗口探测器；如果没有这行代码，无法证明默认关闭未探测窗口。
            smoke = WindowsControlledNotepadLaunchSmoke(base_dir=Path(temp_dir), launch_backend=backend, window_probe=probe, platform="win32")  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建受控 smoke runtime；如果没有这行代码，测试没有被测对象。
            report = smoke.run(real_smoke=False, allow_real_gate=False)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：运行默认关闭合同；如果没有这行代码，默认安全没有事实证据。
        self.assertTrue(report["passed"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言默认关闭合同通过；如果没有这行代码，安全预览可能失败但无人发现。
        self.assertTrue(report["default_off_zero_events"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言默认关闭零事件；如果没有这行代码，默认路径可能偷偷启动应用。
        self.assertFalse(report["real_notepad_launch_attempted"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言没有尝试真实启动；如果没有这行代码，默认关闭边界不可见。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言未触碰真实桌面；如果没有这行代码，测试可能误开本机应用。
        self.assertEqual(backend.launches, [])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言后端未被调用；如果没有这行代码，默认关闭可能已经越过最后一跳。
        self.assertEqual(probe.calls, [])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言窗口探测未发生；如果没有这行代码，默认关闭可能仍然执行真实流程。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，test_default_off_does_not_call_launch_backend 到此结束；如果没有这个边界说明，初学者不容易看出默认关闭测试范围。

    def test_enabled_fake_backend_verifies_process_window_and_cleanup(self) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，验证显式启用后的启动、窗口和清理合同；如果没有这段测试，Phase104 可能只证明启动不证明收尾。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建临时目录隔离目标文件；如果没有这行代码，受控文件会污染项目目录。
            backend = Phase104FakeLaunchBackend()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建 fake 启动后端；如果没有这行代码，测试可能真的打开 Notepad。
            probe = Phase104FakeWindowProbe()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建 fake 窗口探测器；如果没有这行代码，测试依赖真实桌面。
            report = run_phase104_controlled_notepad_launch_smoke_contract(base_dir=Path(temp_dir), real_smoke=True, allow_real_gate=True, launch_backend=backend, window_probe=probe, platform="win32")  # 新增代码+Phase104ControlledNotepadLaunchSmoke：运行显式启用合同；如果没有这行代码，正向路径没有统一事实源。
        self.assertTrue(report["passed"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言 fake 正向合同通过；如果没有这行代码，失败可能被后续字段掩盖。
        self.assertTrue(report["real_notepad_launch_attempted"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言已经尝试启动 Notepad；如果没有这行代码，后端桥接可能空跑。
        self.assertTrue(report["process_ownership_verified"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言进程归属已验证；如果没有这行代码，cleanup 可能误清理用户进程。
        self.assertTrue(report["visible_window_verified"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言可见窗口已验证；如果没有这行代码，进程存在但窗口未出现也会误过。
        self.assertTrue(report["cleanup_completed"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言清理完成；如果没有这行代码，真实 smoke 可能残留窗口。
        self.assertFalse(report["residual_owned_process"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言自有进程没有残留；如果没有这行代码，清理失败不可见。
        self.assertTrue(report["real_desktop_touched"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言正向 smoke 明确标记触碰桌面；如果没有这行代码，真实行为会被误说成无副作用。
        self.assertTrue(report["unsafe_launch_zero_events"])  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言危险启动零事件；如果没有这行代码，PowerShell 类目标可能进入后端。
        self.assertEqual(backend.launches[0]["executable"], "notepad.exe")  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言只启动安全 Notepad exe；如果没有这行代码，后端目标可能漂移。
        self.assertTrue(backend.cleanup_called)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言清理后端被调用；如果没有这行代码，cleanup_completed 可能只是报告自称。
        self.assertEqual(probe.calls[0]["process_id"], 10401)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言按自有进程号查找窗口；如果没有这行代码，可能误匹配用户已有 Notepad。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，test_enabled_fake_backend_verifies_process_window_and_cleanup 到此结束；如果没有这个边界说明，初学者不容易看出正向 smoke 测试范围。

    def test_phase104_cli_line_tokens_are_stable(self) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，验证 CLI token 稳定；如果没有这段测试，真实终端验收容易因输出漂移失败。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建临时目录隔离报告；如果没有这行代码，合同报告会污染真实 memory。
            report = run_phase104_controlled_notepad_launch_smoke_contract(base_dir=Path(temp_dir), real_smoke=True, allow_real_gate=True, launch_backend=Phase104FakeLaunchBackend(), window_probe=Phase104FakeWindowProbe(), platform="win32")  # 新增代码+Phase104ControlledNotepadLaunchSmoke：运行 fake 正向合同；如果没有这行代码，token 没有事实来源。
        line = phase104_cli_line(report)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：生成终端 token 行；如果没有这行代码，场景无法复用统一格式。
        self.assertIn(PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_MARKER, line)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言 ready marker 存在；如果没有这行代码，可见终端没有等待锚点。
        self.assertIn(PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_OK_TOKEN, line)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言 OK token 存在；如果没有这行代码，验收器无法区分成功输出。
        self.assertIn("real_notepad_launch_attempted=true", line)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言真实启动尝试 token 存在；如果没有这行代码，Phase104 正向目标不可验收。
        self.assertIn("process_ownership_verified=true", line)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言进程归属 token 存在；如果没有这行代码，清理边界不可验收。
        self.assertIn("visible_window_verified=true", line)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言可见窗口 token 存在；如果没有这行代码，真实窗口出现不可验收。
        self.assertIn("cleanup_completed=true", line)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言清理完成 token 存在；如果没有这行代码，窗口残留风险不可验收。
        self.assertIn("residual_owned_process=false", line)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言无残留 token 存在；如果没有这行代码，清理失败可能被忽略。
        self.assertIn("unsafe_launch_zero_events=true", line)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言危险启动零事件 token 存在；如果没有这行代码，高风险拒绝不可验收。
        self.assertIn("real_desktop_touched=true", line)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言正向 smoke 明确触碰桌面；如果没有这行代码，用户会误读副作用边界。
        self.assertIn("uncontrolled_actions_expanded=false", line)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：断言未扩张无边界动作面；如果没有这行代码，full 模式可能被误读成无限制。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，test_phase104_cli_line_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 token 测试范围。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：类段结束，WindowsComputerUseControlledNotepadLaunchSmokePhase104Tests 到此结束；如果没有这个边界说明，初学者不容易看出 Phase104 测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase104ControlledNotepadLaunchSmoke：文件入口段开始，允许直接运行测试文件；如果没有这行代码，小白用户必须记完整 unittest 命令。
    unittest.main()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出脚本入口范围。
