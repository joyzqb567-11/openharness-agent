import tempfile  # 新增代码+PaintVisualGuard：导入临时目录工具保存 fake 截图；如果没有这一行，像素门禁测试会污染项目真实证据目录。
import unittest  # 新增代码+PaintPikachuRealLoop：导入 unittest 测试框架；如果没有这一行，标准测试命令无法发现本文件。
from pathlib import Path  # 新增代码+PaintVisualGuard：导入 Path 管理 fake 截图路径；如果没有这一行，测试路径拼接会更难读。
from types import SimpleNamespace  # 新增代码+PaintPikachuRealLoop：导入简单对象用于模拟窗口快照；如果没有这一行，fake inventory 需要写更多样板类。
from typing import Any  # 新增代码+PaintPikachuRealLoop：导入 Any 标注 fake 报告；如果没有这一行，动态字典接口边界不清楚。

from PIL import Image  # 新增代码+PaintVisualGuard：导入 Pillow 生成白图和带线条的截图；如果没有这一行，测试无法验证像素变化门禁。
from learning_agent.computer_use.paint_pikachu_real_loop import WindowsPaintPikachuRealExecutionLoop, _paint_loop_canvas_rect  # 修改代码+PaintCanvasRectGuard：导入画布估算 helper；如果没有这一行，测试无法锁住真实 Paint 坐标偏移根因。


class FakePaintLaunchBackend:  # 新增代码+PaintPikachuRealLoop：类段开始，模拟 Phase110 真实启动后端但不打开应用；如果没有这个 fake，单元测试会触碰用户真实桌面。
    def __init__(self) -> None:  # 新增代码+PaintPikachuRealLoop：函数段开始，初始化启动记录；如果没有这段函数，测试无法断言启动后端被调用。
        self.launches: list[Any] = []  # 新增代码+PaintPikachuRealLoop：保存收到的启动请求；如果没有这一行，测试无法证明闭环尝试启动 mspaint。
    # 新增代码+PaintPikachuRealLoop：函数段结束，FakePaintLaunchBackend.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出 fake 初始化范围。

    def launch(self, request: Any) -> dict[str, Any]:  # 新增代码+PaintPikachuRealLoop：函数段开始，返回成功启动形状；如果没有这段函数，run_generic_launch_backend 无法调用 fake 后端。
        self.launches.append(request)  # 新增代码+PaintPikachuRealLoop：记录启动请求；如果没有这一行，测试无法检查启动链路是否经过后端。
        return {"ok": True, "decision": "fake_paint_started", "backend": "fake_paint_launch_backend", "backend_launch_reaches_launcher": True, "process_started": True, "process_id": 4242, "process_executable": "mspaint.exe", "real_desktop_touched": True, "cleanup_registered": True, "owned_process_registered": True}  # 新增代码+PaintPikachuRealLoop：返回真实启动报告形状但不触桌面；如果没有这一行，闭环会停在启动失败。
    # 新增代码+PaintPikachuRealLoop：函数段结束，FakePaintLaunchBackend.launch 到此结束；如果没有这个边界说明，初学者不容易看出 fake 启动范围。
# 新增代码+PaintPikachuRealLoop：类段结束，FakePaintLaunchBackend 到此结束；如果没有这个边界说明，初学者不容易看出 fake 启动器范围。


class FakePaintInventory:  # 新增代码+PaintPikachuRealLoop：类段开始，模拟窗口枚举结果；如果没有这个 fake，测试必须依赖真实 Windows 窗口。
    def snapshot(self) -> Any:  # 新增代码+PaintPikachuRealLoop：函数段开始，返回包含 Paint 窗口的快照；如果没有这段函数，真实闭环找不到窗口。
        window = {"app_id": "mspaint.exe", "window_id": "hwnd:42420", "hwnd": 42420, "pid": 4242, "title_preview": "Untitled - Paint", "rect": {"left": 100, "top": 100, "right": 1000, "bottom": 800}}  # 新增代码+PaintPikachuRealLoop：构造与 fake pid 匹配的 Paint 窗口；如果没有这一行，窗口身份无法验证。
        return SimpleNamespace(windows=[window])  # 新增代码+PaintPikachuRealLoop：返回带 windows 属性的快照对象；如果没有这一行，闭环无法遍历窗口列表。
    # 新增代码+PaintPikachuRealLoop：函数段结束，FakePaintInventory.snapshot 到此结束；如果没有这个边界说明，初学者不容易看出 fake 窗口范围。
# 新增代码+PaintPikachuRealLoop：类段结束，FakePaintInventory 到此结束；如果没有这个边界说明，初学者不容易看出 fake inventory 范围。


class FakeLowLevelSender:  # 新增代码+PaintPikachuRealLoop：类段开始，记录低层事件但不控制鼠标；如果没有这个 fake，单元测试会真实移动鼠标。
    def __init__(self) -> None:  # 新增代码+PaintPikachuRealLoop：函数段开始，初始化事件记录；如果没有这段函数，测试无法检查发送数量。
        self.events: list[dict[str, Any]] = []  # 新增代码+PaintPikachuRealLoop：保存低层事件副本；如果没有这一行，测试无法确认拖拽事件被生成。
    # 新增代码+PaintPikachuRealLoop：函数段结束，FakeLowLevelSender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出 fake sender 初始化范围。

    def send_low_level(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+PaintPikachuRealLoop：函数段开始，模拟真实 sender 返回成功；如果没有这段函数，闭环无法完成发送分支。
        self.events.extend(dict(event) for event in events)  # 新增代码+PaintPikachuRealLoop：复制所有事件用于断言；如果没有这一行，测试无法证明包含 mouse_down/mouse_up。
        return {"ok": True, "low_level_event_count": len(events), "sender": "fake_low_level_sender"}  # 新增代码+PaintPikachuRealLoop：返回成功发送摘要；如果没有这一行，闭环会认为 SendInput 失败。
    # 新增代码+PaintPikachuRealLoop：函数段结束，FakeLowLevelSender.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出 fake 发送范围。
# 新增代码+PaintPikachuRealLoop：类段结束，FakeLowLevelSender 到此结束；如果没有这个边界说明，初学者不容易看出 fake sender 范围。


class FakePaintScreenshotRuntime:  # 新增代码+PaintVisualGuard：类段开始，模拟动作后窗口截图；如果没有这个 fake，测试只能相信自报字段而不能验证像素门禁。
    def __init__(self, screenshot_path: Path, captured: bool = True) -> None:  # 新增代码+PaintVisualGuard：函数段开始，保存 fake 截图路径和捕获状态；如果没有这段函数，测试无法控制截图成功或失败。
        self.screenshot_path = screenshot_path  # 新增代码+PaintVisualGuard：记录要返回的截图路径；如果没有这一行，capture_window 不知道把证据指向哪里。
        self.captured = captured  # 新增代码+PaintVisualGuard：记录是否模拟截图成功；如果没有这一行，失败截图路径无法被测试。
        self.windows: list[dict[str, Any]] = []  # 新增代码+PaintVisualGuard：保存被截图的窗口；如果没有这一行，测试无法确认截图目标来自 Paint。
    # 新增代码+PaintVisualGuard：函数段结束，FakePaintScreenshotRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出 fake 截图初始化范围。

    def capture_window(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+PaintVisualGuard：函数段开始，返回与 Phase45 截图 runtime 兼容的结果；如果没有这段函数，闭环无法做动作后视觉验证。
        self.windows.append(dict(window))  # 新增代码+PaintVisualGuard：记录调用方传入的窗口；如果没有这一行，测试无法证明截图绑定的是 Paint 窗口。
        return {"captured": self.captured, "screenshot_captured": self.captured, "screenshot_path": str(self.screenshot_path), "screenshot_width": 900, "screenshot_height": 700, "provider": "fake_paint_screenshot_runtime"}  # 新增代码+PaintVisualGuard：返回截图摘要；如果没有这一行，生产逻辑拿不到可做像素检查的文件路径。
    # 新增代码+PaintVisualGuard：函数段结束，FakePaintScreenshotRuntime.capture_window 到此结束；如果没有这个边界说明，初学者不容易看出 fake 截图范围。
# 新增代码+PaintVisualGuard：类段结束，FakePaintScreenshotRuntime 到此结束；如果没有这个边界说明，初学者不容易看出视觉证据 fake 范围。


def write_fake_paint_screenshot(path: Path, *, changed: bool) -> None:  # 新增代码+PaintVisualGuard：函数段开始，生成白底或带线条的 Paint 截图；如果没有这个 helper，两个测试会重复写图片生成细节。
    image = Image.new("RGB", (900, 700), "white")  # 新增代码+PaintVisualGuard：创建白底截图模拟空白画布；如果没有这一行，测试没有稳定背景。
    if changed:  # 修改代码+PaintRecognizableVisualGuard：按参数决定是否加入分布式皮卡丘笔迹；如果没有这一行，无法分别覆盖空白和可识别两种场景。
        strokes = [(410, 220, 470, 330), (570, 220, 510, 330), (420, 380, 610, 380), (420, 430, 610, 430), (445, 460, 590, 500), (680, 430, 780, 520)]  # 新增代码+PaintRecognizableVisualGuard：准备耳朵、脸、身体和尾巴区域的模拟线段；如果没有这一行，成功 fake 图仍会被严格门禁拒绝。
        for start_x, start_y, end_x, end_y in strokes:  # 新增代码+PaintRecognizableVisualGuard：遍历每一条模拟笔迹；如果没有这一行，多个关键区域不会被写入。
            steps = max(abs(end_x - start_x), abs(end_y - start_y), 1)  # 新增代码+PaintRecognizableVisualGuard：计算线段需要多少像素步；如果没有这一行，斜线会断裂或除以零。
            for offset in range(steps + 1):  # 新增代码+PaintRecognizableVisualGuard：逐点画出线段；如果没有这一行，截图不会形成连续笔迹。
                x = int(round(start_x + (end_x - start_x) * offset / steps))  # 新增代码+PaintRecognizableVisualGuard：计算当前点 x；如果没有这一行，线段横向位置无法落到目标区域。
                y = int(round(start_y + (end_y - start_y) * offset / steps))  # 新增代码+PaintRecognizableVisualGuard：计算当前点 y；如果没有这一行，线段纵向位置无法落到目标区域。
                for thick in range(3):  # 新增代码+PaintRecognizableVisualGuard：给线条加一点厚度；如果没有这一行，像素数量可能不足以代表真实画笔。
                    image.putpixel((min(899, x + thick), min(699, y)), (0, 0, 0))  # 新增代码+PaintRecognizableVisualGuard：写入黑色笔迹像素；如果没有这一行，changed=True 的截图仍然是空白。
    image.save(path)  # 新增代码+PaintVisualGuard：把截图保存到磁盘；如果没有这一行，被测代码无法从路径读取像素。
# 新增代码+PaintVisualGuard：函数段结束，write_fake_paint_screenshot 到此结束；如果没有这个边界说明，初学者不容易看出截图生成范围。


class WindowsPaintPikachuRealExecutionLoopTests(unittest.TestCase):  # 新增代码+PaintPikachuRealLoop：类段开始，集中验证 Paint 皮卡丘真实闭环；如果没有这个类，测试用例无法组织运行。
    def test_maximized_paint_canvas_rect_avoids_toolbar_and_side_gutters(self) -> None:  # 新增代码+PaintCanvasRectGuard：函数段开始，验证最大化 Paint 的画布估算避开工具栏和左侧空白；如果没有这个测试，皮卡丘会被画到画布外。
        window = {"rect": {"left": 0, "top": 0, "right": 1928, "bottom": 1032}}  # 新增代码+PaintCanvasRectGuard：构造真实截图里类似的最大化 Paint 窗口；如果没有这一行，测试没有代表性输入。
        canvas = _paint_loop_canvas_rect(window)  # 新增代码+PaintCanvasRectGuard：计算画布估算结果；如果没有这一行，无法检查坐标是否安全。
        self.assertGreaterEqual(canvas["left"], 320)  # 新增代码+PaintCanvasRectGuard：断言画布左边界避开左侧面板；如果没有这一行，路径会从白纸外侧开始。
        self.assertGreaterEqual(canvas["top"], 240)  # 新增代码+PaintCanvasRectGuard：断言画布上边界避开顶部工具栏；如果没有这一行，耳朵和头部会画进工具栏区域。
        self.assertLessEqual(canvas["right"], 1620)  # 新增代码+PaintCanvasRectGuard：断言画布右边界避开右侧滚动/边缘区域；如果没有这一行，尾巴可能被画到白纸外。
        self.assertLessEqual(canvas["bottom"], 940)  # 新增代码+PaintCanvasRectGuard：断言画布下边界避开底部状态栏；如果没有这一行，身体下沿可能落到可绘区域外。
    # 新增代码+PaintCanvasRectGuard：函数段结束，test_maximized_paint_canvas_rect_avoids_toolbar_and_side_gutters 到此结束；如果没有这个边界说明，初学者不容易看出画布坐标测试范围。

    def test_loop_launches_paint_finds_window_and_sends_drag_events(self) -> None:  # 新增代码+PaintPikachuRealLoop：函数段开始，验证闭环主成功路径；如果没有这个测试，默认 full prompt 可能再次未接线。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PaintVisualGuard：创建隔离目录保存动作后截图；如果没有这一行，测试会把图片写进项目目录。
            screenshot_path = Path(raw_dir) / "paint_after.png"  # 新增代码+PaintVisualGuard：定义 fake 动作后截图路径；如果没有这一行，截图 runtime 没有返回目标。
            write_fake_paint_screenshot(screenshot_path, changed=True)  # 新增代码+PaintVisualGuard：生成带真实像素痕迹的截图；如果没有这一行，成功路径会被视觉门禁拒绝。
            launch_backend = FakePaintLaunchBackend()  # 新增代码+PaintPikachuRealLoop：创建 fake 启动后端；如果没有这一行，测试可能真实启动 Paint。
            sender = FakeLowLevelSender()  # 新增代码+PaintPikachuRealLoop：创建 fake 低层 sender；如果没有这一行，测试可能真实发送鼠标事件。
            screenshot_runtime = FakePaintScreenshotRuntime(screenshot_path)  # 新增代码+PaintVisualGuard：创建 fake 截图 runtime；如果没有这一行，闭环无法证明画布真的变化。
            loop = WindowsPaintPikachuRealExecutionLoop(inventory=FakePaintInventory(), low_level_sender=sender, launch_backend=launch_backend, screenshot_runtime=screenshot_runtime, platform="win32", poll_timeout_seconds=0.01)  # 修改代码+PaintVisualGuard：创建注入 fake 截图的闭环；如果没有截图 runtime，测试无法覆盖像素门禁。
            report = loop.run_desktop_task(target_app="mspaint", prompt="请使用本地电脑的画图软件画一个皮卡丘。")  # 新增代码+PaintPikachuRealLoop：运行真实用户风格 prompt；如果没有这一行，主路径不会被触发。
            event_types = {event.get("type") for event in sender.events}  # 新增代码+PaintPikachuRealLoop：收集事件类型；如果没有这一行，断言无法确认拖拽结构。
            self.assertTrue(report["ok"])  # 修改代码+PaintVisualGuard：断言有像素变化时闭环才成功；如果没有这一行，视觉门禁失效不会暴露。
            self.assertTrue(report["real_desktop_touched"])  # 新增代码+PaintPikachuRealLoop：断言报告表达真实桌面触达语义；如果没有这一行，runtime 无法区分 fake recording 和真实路径。
            self.assertTrue(report["computer_use_gui_route_used"])  # 新增代码+PaintPikachuRealLoop：断言 GUI 路由被使用；如果没有这一行，脚本路径可能混入成功。
            self.assertTrue(report["owned_window_verified"])  # 新增代码+PaintPikachuRealLoop：断言目标窗口已验证；如果没有这一行，拖拽可能落到未知窗口。
            self.assertTrue(report["post_action_screenshot_exists"])  # 新增代码+PaintVisualGuard：断言动作后截图存在；如果没有这一行，空证据也可能误判成功。
            self.assertTrue(report["canvas_changed_after_actions"])  # 新增代码+PaintVisualGuard：断言像素门禁确认画布变化；如果没有这一行，低层事件数可能再次冒充绘图结果。
            self.assertEqual(report["post_action_visual_evidence_path"], str(screenshot_path))  # 新增代码+PaintVisualGuard：断言报告暴露可复核截图路径；如果没有这一行，用户无法打开证据检查。
            self.assertGreater(report["gui_action_count"], 0)  # 新增代码+PaintPikachuRealLoop：断言有绘图动作；如果没有这一行，空计划可能冒充成功。
            self.assertGreater(report["low_level_event_count"], 0)  # 新增代码+PaintPikachuRealLoop：断言有低层事件；如果没有这一行，真实路径可能只有口头报告。
            self.assertGreater(len(launch_backend.launches), 0)  # 新增代码+PaintPikachuRealLoop：断言启动后端被调用；如果没有这一行，闭环可能没真正尝试打开 Paint。
            self.assertIn("set_foreground", event_types)  # 新增代码+PaintPikachuRealLoop：断言先聚焦 Paint 窗口；如果没有这一行，鼠标事件可能打到旧窗口。
            self.assertIn("mouse_down", event_types)  # 新增代码+PaintPikachuRealLoop：断言包含鼠标按下；如果没有这一行，拖拽不会开始绘制。
            self.assertIn("mouse_up", event_types)  # 新增代码+PaintPikachuRealLoop：断言包含鼠标抬起；如果没有这一行，拖拽不会闭合。
            self.assertIn("pause", event_types)  # 新增代码+PaintStablePause：断言选中铅笔后会等待 Paint 稳定；如果没有这一行，第一条主体轮廓可能被再次吞掉。
    # 新增代码+PaintPikachuRealLoop：函数段结束，test_loop_launches_paint_finds_window_and_sends_drag_events 到此结束；如果没有这个边界说明，初学者不容易看出成功路径测试范围。

    def test_loop_rejects_blank_post_action_screenshot(self) -> None:  # 新增代码+PaintVisualGuard：函数段开始，验证空白画布不能被低层事件数误判为成功；如果没有这个测试，当前 bug 会反复出现。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PaintVisualGuard：创建隔离目录保存空白截图；如果没有这一行，测试会污染真实 memory。
            screenshot_path = Path(raw_dir) / "paint_blank.png"  # 新增代码+PaintVisualGuard：定义空白截图路径；如果没有这一行，fake runtime 没有证据文件。
            write_fake_paint_screenshot(screenshot_path, changed=False)  # 新增代码+PaintVisualGuard：生成纯白截图模拟 Paint 没画上；如果没有这一行，测试无法复现用户截图里的空白画布。
            sender = FakeLowLevelSender()  # 新增代码+PaintVisualGuard：创建 fake sender 证明即使事件发送成功也不能直接成功；如果没有这一行，测试无法隔离误报根因。
            loop = WindowsPaintPikachuRealExecutionLoop(inventory=FakePaintInventory(), low_level_sender=sender, launch_backend=FakePaintLaunchBackend(), screenshot_runtime=FakePaintScreenshotRuntime(screenshot_path), platform="win32", poll_timeout_seconds=0.01)  # 新增代码+PaintVisualGuard：创建带空白截图的闭环；如果没有这一行，空白画布门禁不会被执行。
            report = loop.run_desktop_task(target_app="mspaint", prompt="请使用本地电脑的画图软件画一个皮卡丘。")  # 新增代码+PaintVisualGuard：运行用户真实 prompt；如果没有这一行，无法观察最终报告。
            self.assertFalse(report["ok"])  # 新增代码+PaintVisualGuard：断言空白画布不能成功；如果没有这一行，误报成功会漏过。
            self.assertFalse(report["canvas_changed_after_actions"])  # 新增代码+PaintVisualGuard：断言画布变化字段必须为 false；如果没有这一行，报告仍会欺骗 maturity。
            self.assertTrue(report["post_action_screenshot_exists"])  # 新增代码+PaintVisualGuard：断言截图存在但内容不合格；如果没有这一行，无法区分“无截图”和“截图空白”。
            self.assertGreater(report["low_level_event_count"], 0)  # 新增代码+PaintVisualGuard：断言低层事件已发送；如果没有这一行，测试不能证明根因是缺少视觉验证而不是没动作。
    # 新增代码+PaintVisualGuard：函数段结束，test_loop_rejects_blank_post_action_screenshot 到此结束；如果没有这个边界说明，初学者不容易看出误报回归测试范围。
# 新增代码+PaintPikachuRealLoop：类段结束，WindowsPaintPikachuRealExecutionLoopTests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+PaintPikachuRealLoop：文件入口段开始，允许直接运行本测试；如果没有这一行，用户必须记住 unittest 模块路径。
    unittest.main()  # 新增代码+PaintPikachuRealLoop：启动 unittest；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+PaintPikachuRealLoop：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出脚本入口范围。
