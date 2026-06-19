from learning_agent.computer_use_mcp_v2.windows_runtime import controlled_browser_live_local_page as browser_page  # 新增代码+Phase139BrowserLiveLocalPage：导入被测浏览器本地页合同模块；如果没有这一行，测试无法覆盖真实矩阵失败点。


def _browser_window(title: str) -> dict[str, object]:  # 新增代码+Phase139BrowserLiveLocalPage：函数段开始，构造 fake 浏览器窗口；如果没有这段函数，测试要重复写窗口字段。
    return {  # 新增代码+Phase139BrowserLiveLocalPage：返回符合真实 inventory 字段的窗口字典；如果没有这一行，driver 无法识别目标窗口。
        "app_id": "msedge.exe",  # 新增代码+Phase139BrowserLiveLocalPage：模拟 Edge 进程身份；如果没有这一行，浏览器窗口识别会失败。
        "process_name": "msedge.exe",  # 新增代码+Phase139BrowserLiveLocalPage：模拟真实进程名；如果没有这一行，目标身份摘要不完整。
        "class_name": "Chrome_WidgetWin_1",  # 新增代码+Phase139BrowserLiveLocalPage：模拟 Chromium 顶层窗口类；如果没有这一行，浏览器判断缺少类名证据。
        "window_id": "hwnd:139001",  # 新增代码+Phase139BrowserLiveLocalPage：提供稳定窗口 ID；如果没有这一行，复核目标无法匹配。
        "hwnd": 139001,  # 新增代码+Phase139BrowserLiveLocalPage：提供 Win32 句柄；如果没有这一行，点击事件无法附带目标句柄。
        "pid": 139002,  # 新增代码+Phase139BrowserLiveLocalPage：提供进程 ID；如果没有这一行，清理和身份报告缺少 pid。
        "title_preview": title,  # 新增代码+Phase139BrowserLiveLocalPage：设置可变窗口标题；如果没有这一行，无法模拟标题延迟加载。
        "rect": {"left": 0, "top": 0, "right": 1200, "bottom": 900},  # 新增代码+Phase139BrowserLiveLocalPage：提供窗口矩形；如果没有这一行，点击坐标会走不稳定兜底。
    }  # 新增代码+Phase139BrowserLiveLocalPage：fake 窗口字典结束；如果没有这一行，Python 字典语法不完整。
    # 新增代码+Phase139BrowserLiveLocalPage：函数段结束，_browser_window 到此结束；如果没有这个边界说明，用户不容易看出 fake 窗口范围。


class _FakeSnapshot:  # 新增代码+Phase139BrowserLiveLocalPage：类段开始，模拟真实 inventory 快照；如果没有这个类，driver._recheck_target 无法按 window_id 查找。
    def __init__(self, windows: list[dict[str, object]]) -> None:  # 新增代码+Phase139BrowserLiveLocalPage：函数段开始，保存本次快照窗口列表；如果没有这段函数，fake 快照没有数据。
        self.windows = [dict(window) for window in windows]  # 新增代码+Phase139BrowserLiveLocalPage：复制窗口列表避免测试外部修改；如果没有这一行，快照事实可能被污染。
        # 新增代码+Phase139BrowserLiveLocalPage：函数段结束，_FakeSnapshot.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def find_window(self, raw_window: object) -> dict[str, object] | None:  # 新增代码+Phase139BrowserLiveLocalPage：函数段开始，按 window_id 复核同一个窗口；如果没有这段函数，driver 会认为目标漂移。
        target_id = str(raw_window.get("window_id") if isinstance(raw_window, dict) else "")  # 新增代码+Phase139BrowserLiveLocalPage：读取待复核窗口 ID；如果没有这一行，无法匹配同一个 fake 窗口。
        for window in self.windows:  # 新增代码+Phase139BrowserLiveLocalPage：遍历当前快照窗口；如果没有这一行，查找永远失败。
            if str(window.get("window_id") or "") == target_id:  # 新增代码+Phase139BrowserLiveLocalPage：比较窗口 ID 是否一致；如果没有这一行，不同窗口可能混淆。
                return dict(window)  # 新增代码+Phase139BrowserLiveLocalPage：返回匹配窗口副本；如果没有这一行，driver 拿不到最新标题。
        return None  # 新增代码+Phase139BrowserLiveLocalPage：没有找到时返回 None；如果没有这一行，调用方无法识别漂移。
        # 新增代码+Phase139BrowserLiveLocalPage：函数段结束，_FakeSnapshot.find_window 到此结束；如果没有这个边界说明，用户不容易看出复核范围。


class _FakeInventory:  # 新增代码+Phase139BrowserLiveLocalPage：类段开始，按顺序返回窗口快照；如果没有这个类，无法模拟标题从新标签页变成本地页。
    def __init__(self) -> None:  # 新增代码+Phase139BrowserLiveLocalPage：函数段开始，准备快照序列；如果没有这段函数，fake inventory 没有状态。
        self.snapshots = [  # 新增代码+Phase139BrowserLiveLocalPage：定义每次 snapshot 返回的窗口状态；如果没有这一行，测试不能控制时序。
            [],  # 新增代码+Phase139BrowserLiveLocalPage：启动前没有目标窗口；如果没有这一项，driver 无法把后续窗口视为新窗口。
            [_browser_window("New tab")],  # 新增代码+Phase139BrowserLiveLocalPage：窗口先以新标签页出现；如果没有这一项，无法复现矩阵里的过早判断。
            [_browser_window("New tab")],  # 新增代码+Phase139BrowserLiveLocalPage：准备窗口时标题仍未更新；如果没有这一项，等待逻辑不会被覆盖。
            [_browser_window("New tab")],  # 新增代码+Phase139BrowserLiveLocalPage：第一次短轮询仍未加载；如果没有这一项，测试无法证明会继续等待。
            [_browser_window(browser_page.PHASE139_LOCAL_PAGE_LABEL)],  # 新增代码+Phase139BrowserLiveLocalPage：后续标题变成本地测试页；如果没有这一项，driver 应该拒绝点击。
            [_browser_window(browser_page.PHASE139_LOCAL_PAGE_LABEL)],  # 新增代码+Phase139BrowserLiveLocalPage：动作后复核仍是同一页面；如果没有这一项，结果验证会失败。
        ]  # 新增代码+Phase139BrowserLiveLocalPage：快照序列结束；如果没有这一行，Python 列表语法不完整。
        self.index = 0  # 新增代码+Phase139BrowserLiveLocalPage：初始化快照读取位置；如果没有这一行，每次 snapshot 无法前进。
        # 新增代码+Phase139BrowserLiveLocalPage：函数段结束，_FakeInventory.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake 时序。

    def snapshot(self) -> _FakeSnapshot:  # 新增代码+Phase139BrowserLiveLocalPage：函数段开始，返回下一个 fake 快照；如果没有这段函数，driver 没有窗口事实来源。
        position = min(self.index, len(self.snapshots) - 1)  # 新增代码+Phase139BrowserLiveLocalPage：超过序列后停在最后一个快照；如果没有这一行，多次复核会越界。
        self.index += 1  # 新增代码+Phase139BrowserLiveLocalPage：推进快照序列；如果没有这一行，标题永远不会从新标签页变化。
        return _FakeSnapshot(self.snapshots[position])  # 新增代码+Phase139BrowserLiveLocalPage：返回当前 fake 快照；如果没有这一行，driver 拿不到窗口列表。
        # 新增代码+Phase139BrowserLiveLocalPage：函数段结束，_FakeInventory.snapshot 到此结束；如果没有这个边界说明，用户不容易看出快照读取范围。


class _FakeSender:  # 新增代码+Phase139BrowserLiveLocalPage：类段开始，模拟真实 SendInput sender；如果没有这个类，测试无法证明等待后会派发点击。
    def send_low_level(self, events: list[dict[str, object]]) -> dict[str, object]:  # 新增代码+Phase139BrowserLiveLocalPage：函数段开始，记录低层事件派发成功；如果没有这段函数，driver 会认为没有真实动作。
        return {"ok": True, "low_level_event_count": len(events), "sender_kind": "windows_sendinput_low_level", "raw_text_included": False}  # 新增代码+Phase139BrowserLiveLocalPage：返回真实 sender 风格成功结果；如果没有这一行，page_changed_after_real_click 不能成立。
        # 新增代码+Phase139BrowserLiveLocalPage：函数段结束，_FakeSender.send_low_level 到此结束；如果没有这个边界说明，用户不容易看出 sender 范围。


class _FakeObservationRuntime:  # 新增代码+Phase139BrowserLiveLocalPage：类段开始，模拟前后截图观察；如果没有这个类，截图差异条件无法通过。
    def __init__(self, before_path: object, after_path: object) -> None:  # 新增代码+Phase139BrowserLiveLocalPage：函数段开始，保存前后截图路径；如果没有这段函数，observe 无法产生不同 artifact。
        self.paths = [before_path, after_path]  # 新增代码+Phase139BrowserLiveLocalPage：记录两次观察对应的文件路径；如果没有这一行，截图哈希不会变化。
        self.index = 0  # 新增代码+Phase139BrowserLiveLocalPage：初始化观察次数；如果没有这一行，无法区分 before 和 after。
        # 新增代码+Phase139BrowserLiveLocalPage：函数段结束，_FakeObservationRuntime.__init__ 到此结束；如果没有这个边界说明，用户不容易看出观察初始化。

    def observe(self, **_: object) -> dict[str, object]:  # 新增代码+Phase139BrowserLiveLocalPage：函数段开始，返回一帧 fake 观察；如果没有这段函数，driver 不能生成 before/after 摘要。
        position = min(self.index, len(self.paths) - 1)  # 新增代码+Phase139BrowserLiveLocalPage：超过次数后使用最后一个截图；如果没有这一行，多次观察会越界。
        self.index += 1  # 新增代码+Phase139BrowserLiveLocalPage：推进观察序号；如果没有这一行，前后截图会相同。
        path = self.paths[position]  # 新增代码+Phase139BrowserLiveLocalPage：选择本次截图路径；如果没有这一行，后续无法写文件。
        path.write_bytes(f"phase139-screenshot-{position}".encode("utf-8"))  # 新增代码+Phase139BrowserLiveLocalPage：写入不同截图内容；如果没有这一行，截图哈希无法证明变化。
        return {  # 新增代码+Phase139BrowserLiveLocalPage：返回观察帧字段；如果没有这一行，_phase139_observation_summary 不能解析证据。
            "model": "fake_observation",  # 新增代码+Phase139BrowserLiveLocalPage：标记 fake 观察来源；如果没有这一行，报告缺模型名。
            "screenshot_observation": True,  # 新增代码+Phase139BrowserLiveLocalPage：声明截图已捕获；如果没有这一行，截图证据会被判空。
            "screenshot_artifact_openable": True,  # 新增代码+Phase139BrowserLiveLocalPage：声明截图文件可打开；如果没有这一行，像素证据不完整。
            "pixel_guard_passed": True,  # 新增代码+Phase139BrowserLiveLocalPage：声明像素保护通过；如果没有这一行，观察质量不足。
            "uia_tree_observation": True,  # 新增代码+Phase139BrowserLiveLocalPage：声明 UIA 观察可用；如果没有这一行，结构化观察缺失。
            "window_state_observation": True,  # 新增代码+Phase139BrowserLiveLocalPage：声明窗口状态观察可用；如果没有这一行，窗口证据缺失。
            "raw_text_included": False,  # 新增代码+Phase139BrowserLiveLocalPage：声明没有泄露原始文本；如果没有这一行，隐私条件不清楚。
            "screenshot": {"artifact_path": str(path), "artifact_openable": True, "pixel_guard_passed": True},  # 新增代码+Phase139BrowserLiveLocalPage：提供截图 artifact 路径；如果没有这一行，截图哈希为空。
        }  # 新增代码+Phase139BrowserLiveLocalPage：观察帧返回结束；如果没有这一行，Python 字典语法不完整。
        # 新增代码+Phase139BrowserLiveLocalPage：函数段结束，_FakeObservationRuntime.observe 到此结束；如果没有这个边界说明，用户不容易看出观察范围。


class _FakeProcess:  # 新增代码+Phase139BrowserLiveLocalPage：类段开始，模拟 subprocess.Popen 返回对象；如果没有这个类，测试会尝试启动真实浏览器。
    def poll(self) -> int | None:  # 新增代码+Phase139BrowserLiveLocalPage：函数段开始，模拟进程仍在运行；如果没有这段函数，finally 分支无法查询状态。
        return None  # 新增代码+Phase139BrowserLiveLocalPage：返回 None 表示进程未退出；如果没有这一行，driver 可能跳过等待路径。
        # 新增代码+Phase139BrowserLiveLocalPage：函数段结束，_FakeProcess.poll 到此结束；如果没有这个边界说明，用户不容易看出进程状态。

    def wait(self, timeout: float | None = None) -> int:  # 新增代码+Phase139BrowserLiveLocalPage：函数段开始，模拟短等待成功；如果没有这段函数，finally 会报缺方法。
        _ = timeout  # 新增代码+Phase139BrowserLiveLocalPage：显式接收 timeout 参数；如果没有这一行，读者会疑惑参数为何未用。
        return 0  # 新增代码+Phase139BrowserLiveLocalPage：返回成功退出码；如果没有这一行，等待结果不稳定。
        # 新增代码+Phase139BrowserLiveLocalPage：函数段结束，_FakeProcess.wait 到此结束；如果没有这个边界说明，用户不容易看出等待范围。


def test_phase139_driver_waits_for_delayed_local_page_title(monkeypatch, tmp_path) -> None:  # 新增代码+Phase139BrowserLiveLocalPage：函数段开始，验证浏览器标题延迟加载时仍会等待后点击；如果没有这段测试，矩阵里的 local_page_loaded=false 会复发。
    monkeypatch.setattr(browser_page.subprocess, "Popen", lambda *_args, **_kwargs: _FakeProcess())  # 新增代码+Phase139BrowserLiveLocalPage：阻止测试启动真实浏览器；如果没有这一行，单测会污染用户桌面。
    driver = browser_page.Phase139WindowsBrowserLiveLocalPageDriver(  # 新增代码+Phase139BrowserLiveLocalPage：创建注入 fake 依赖的 driver；如果没有这一行，测试无法控制窗口和 sender。
        inventory=_FakeInventory(),  # 新增代码+Phase139BrowserLiveLocalPage：注入标题延迟变化的 fake inventory；如果没有这一行，无法复现失败时序。
        sender=_FakeSender(),  # 新增代码+Phase139BrowserLiveLocalPage：注入 fake 真实 sender；如果没有这一行，点击派发结果无法通过。
        observation_runtime=_FakeObservationRuntime(tmp_path / "before.bmp", tmp_path / "after.bmp"),  # 新增代码+Phase139BrowserLiveLocalPage：注入前后截图不同的 fake 观察器；如果没有这一行，页面变化证据无法成立。
        launch_command=["fake-browser"],  # 新增代码+Phase139BrowserLiveLocalPage：提供非空启动命令让 driver 进入真实路径；如果没有这一行，driver 会报 browser_executable_not_found。
        timeout_seconds=1.0,  # 新增代码+Phase139BrowserLiveLocalPage：缩短 poll 超时让测试快速完成；如果没有这一行，失败时测试等待过久。
    )  # 新增代码+Phase139BrowserLiveLocalPage：driver 构造结束；如果没有这一行，Python 调用语法不完整。
    driver._cleanup_window = lambda *_args, **_kwargs: {"cleanup_completed": True, "host_hidden_or_restored": True, "lock_released": True, "owned_window": True, "close_attempted": False}  # 新增代码+Phase139BrowserLiveLocalPage：避免单测调用真实 Win32 进程清理；如果没有这一行，fake pid 可能触发系统 API。
    report = driver.run(run_root=tmp_path, page_label=browser_page.PHASE139_LOCAL_PAGE_LABEL)  # 新增代码+Phase139BrowserLiveLocalPage：执行完整 driver 流程；如果没有这一行，测试没有实际验证修复。
    assert report["local_page_loaded"] is True  # 新增代码+Phase139BrowserLiveLocalPage：确认等待后识别到本地页面；如果没有这一行，修复目标没有被断言。
    assert report["real_desktop_touched"] is True  # 新增代码+Phase139BrowserLiveLocalPage：确认等待后确实派发了低层事件；如果没有这一行，driver 可能仍然只观察不动作。
    assert report["page_changed_after_real_click"] is True  # 新增代码+Phase139BrowserLiveLocalPage：确认 fake 前后截图差异让页面变化成立；如果没有这一行，点击闭环可能不完整。
    assert report["ok"] is True  # 新增代码+Phase139BrowserLiveLocalPage：确认 driver 总体通过；如果没有这一行，矩阵入口仍可能失败。
    # 新增代码+Phase139BrowserLiveLocalPage：函数段结束，test_phase139_driver_waits_for_delayed_local_page_title 到此结束；如果没有这个边界说明，用户不容易看出回归范围。
