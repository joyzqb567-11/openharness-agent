"""双轨浏览器 Stage 9 视觉证据录制测试。"""  # 新增代码+BrowserRecordingStage9: 说明本文件保护帧序列和 GIF 证据能力；若没有这行代码，维护者不知道测试范围。
from __future__ import annotations  # 新增代码+BrowserRecordingStage9: 延迟解析类型注解；若没有这行代码，局部假对象类型在旧解释顺序下更脆弱。

from PIL import Image  # 新增代码+BrowserRecordingStage9: 使用 Pillow 生成测试 PNG 和验证 GIF；若没有这行代码，测试无法构造真实图片证据。

from learning_agent.tests.support import *  # 新增代码+BrowserRecordingStage9: 复用 tempfile、Path、json、unittest 等测试工具；若没有这行代码，测试会重复大量基础导入。


def _write_png(path: Path, color: tuple[int, int, int]) -> None:  # 新增代码+BrowserRecordingStage9: 写入一个小 PNG 帧；若没有这行代码，store 测试没有真实图片文件。
    path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+BrowserRecordingStage9: 确保帧目录存在；若没有这行代码，保存 PNG 会因为目录缺失失败。
    Image.new("RGB", (16, 16), color).save(path)  # 新增代码+BrowserRecordingStage9: 保存真实 PNG；若没有这行代码，GIF 导出不能证明图片格式可读。


class FakeRecordingPage:  # 新增代码+BrowserRecordingStage9: 提供最小 Playwright Page 替身；若没有这个类，server 录帧测试需要启动真实浏览器。
    url = "https://stage9.test/page"  # 新增代码+BrowserRecordingStage9: 模拟当前页面 URL；若没有这行代码，帧 manifest 无法保存页面来源。

    def __init__(self) -> None:  # 新增代码+BrowserRecordingStage9: 初始化假页面状态；若没有这行代码，截图颜色无法递增。
        self.screenshot_count = 0  # 新增代码+BrowserRecordingStage9: 记录截图次数；若没有这行代码，测试无法确认真的调用了 screenshot。

    def is_closed(self) -> bool:  # 新增代码+BrowserRecordingStage9: 模拟页面未关闭；若没有这行代码，server.current_page 会把假页面当坏页面。
        return False  # 新增代码+BrowserRecordingStage9: 返回可用状态；若没有这行代码，录帧 helper 无法取得页面。

    def title(self) -> str:  # 新增代码+BrowserRecordingStage9: 模拟页面标题；若没有这行代码，帧 manifest 缺少可读标题。
        return "Stage 9 Page"  # 新增代码+BrowserRecordingStage9: 返回稳定标题；若没有这行代码，断言无法稳定匹配。

    def screenshot(self, path: str, full_page: bool = False) -> None:  # 新增代码+BrowserRecordingStage9: 模拟 Playwright 截图 API；若没有这行代码，录帧 helper 无法保存图片。
        del full_page  # 新增代码+BrowserRecordingStage9: 假页面不区分整页截图；若没有这行代码，读者会误以为参数被使用。
        self.screenshot_count += 1  # 新增代码+BrowserRecordingStage9: 记录截图调用次数；若没有这行代码，测试无法判断是否自动捕获。
        _write_png(Path(path), (self.screenshot_count * 40 % 255, 80, 120))  # 新增代码+BrowserRecordingStage9: 写入不同颜色的真实 PNG；若没有这行代码，导出 GIF 没有帧输入。


class BrowserRecordingStage9Tests(LearningAgentTestBase):  # 新增代码+BrowserRecordingStage9: 定义 Stage 9 录制测试集合；若没有这个类，unittest 不会收集本阶段测试。
    def test_recording_store_exports_gif_and_manifest(self) -> None:  # 新增代码+BrowserRecordingStage9: 验证底层 store 能生成帧序列和 GIF；若没有这行代码，工具层可能只有空壳。
        from learning_agent.browser.recording import BrowserRecordingStore  # 新增代码+BrowserRecordingStage9: 导入待实现录制 store；若没有这行代码，测试无法驱动核心功能。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRecordingStage9: 创建隔离目录；若没有这行代码，测试会污染真实 browser_artifacts。
            root = Path(raw_dir)  # 新增代码+BrowserRecordingStage9: 规范化临时目录；若没有这行代码，路径拼接不稳定。
            store = BrowserRecordingStore(root / "browser_artifacts" / "browser_recordings")  # 新增代码+BrowserRecordingStage9: 创建录制 store；若没有这行代码，manifest 没有存储位置。
            manifest = store.start_recording(recording_id="rec-one", run_id="run-one", page_id="page-1")  # 新增代码+BrowserRecordingStage9: 开始录制；若没有这行代码，后续帧没有 recording 归属。
            frame_one = store.recording_dir("rec-one") / "frames" / "frame-0001.png"  # 新增代码+BrowserRecordingStage9: 定义第一帧路径；若没有这行代码，测试无法写帧。
            frame_two = store.recording_dir("rec-one") / "frames" / "frame-0002.png"  # 新增代码+BrowserRecordingStage9: 定义第二帧路径；若没有这行代码，GIF 只有单帧。
            _write_png(frame_one, (255, 0, 0))  # 新增代码+BrowserRecordingStage9: 写入第一帧；若没有这行代码，record_frame 会记录不存在文件。
            _write_png(frame_two, (0, 255, 0))  # 新增代码+BrowserRecordingStage9: 写入第二帧；若没有这行代码，GIF 动态证据不足。
            store.record_frame("rec-one", frame_one, tool_name="browser_open", action_id="a1", page_id="page-1", url="https://stage9.test/one", title="One")  # 新增代码+BrowserRecordingStage9: 记录第一帧元数据；若没有这行代码，manifest 帧列表为空。
            store.record_frame("rec-one", frame_two, tool_name="browser_click", action_id="a2", page_id="page-1", url="https://stage9.test/two", title="Two")  # 新增代码+BrowserRecordingStage9: 记录第二帧元数据；若没有这行代码，动作过程无法复盘。
            stopped = store.stop_recording("rec-one")  # 新增代码+BrowserRecordingStage9: 停止录制；若没有这行代码，manifest 状态不会收尾。
            exported = store.export_gif("rec-one", output_name="evidence.gif", duration_ms=120)  # 新增代码+BrowserRecordingStage9: 导出 GIF；若没有这行代码，Stage 9 没有可视化过程证据。
            self.assertEqual(manifest["recording_id"], "rec-one")  # 新增代码+BrowserRecordingStage9: 断言录制 id 稳定；若没有这行代码，manifest 可能写错对象。
            self.assertEqual(stopped["frame_count"], 2)  # 新增代码+BrowserRecordingStage9: 断言停止时能看到帧数；若没有这行代码，用户不知道录制是否有内容。
            self.assertTrue(Path(exported["gif_path"]).exists())  # 新增代码+BrowserRecordingStage9: 断言 GIF 文件真实存在；若没有这行代码，导出可能只返回假路径。
            self.assertEqual(exported["status"], "exported")  # 新增代码+BrowserRecordingStage9: 断言 manifest 状态更新为 exported；若没有这行代码，状态页无法识别 GIF 已生成。
            self.assertEqual(len(store.load_recording("rec-one")["frames"]), 2)  # 新增代码+BrowserRecordingStage9: 断言重读 manifest 仍有两帧；若没有这行代码，持久化可能丢帧。

    def test_browser_server_tools_capture_frames_and_export_gif(self) -> None:  # 新增代码+BrowserRecordingStage9: 验证 MCP server 暴露统一录制工具并能保存假页面帧；若没有这行代码，store 可能没有接入工具层。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer, TOOLS  # 新增代码+BrowserRecordingStage9: 导入真实 server 和工具清单；若没有这行代码，schema/dispatch 不会被覆盖。
        tool_names = {tool["name"] for tool in TOOLS}  # 新增代码+BrowserRecordingStage9: 收集工具名；若没有这行代码，断言会重复遍历。
        self.assertIn("browser_record_start", tool_names)  # 新增代码+BrowserRecordingStage9: 断言开始录制工具可见；若没有这行代码，模型无法启动证据录制。
        self.assertIn("browser_record_stop", tool_names)  # 新增代码+BrowserRecordingStage9: 断言停止录制工具可见；若没有这行代码，录制无法收尾。
        self.assertIn("browser_gif_export", tool_names)  # 新增代码+BrowserRecordingStage9: 断言 GIF 导出工具可见；若没有这行代码，模型无法生成可视化证据。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRecordingStage9: 创建隔离 workspace；若没有这行代码，测试会污染真实项目。
            workspace = Path(raw_dir)  # 新增代码+BrowserRecordingStage9: 规范化 workspace；若没有这行代码，server 路径不稳定。
            server = BrowserAutomationServer(workspace)  # 新增代码+BrowserRecordingStage9: 创建真实 server；若没有这行代码，工具 dispatch 不会被验证。
            fake_page = FakeRecordingPage()  # 新增代码+BrowserRecordingStage9: 创建假页面；若没有这行代码，录帧没有页面对象。
            server.pages["page-1"] = fake_page  # 新增代码+BrowserRecordingStage9: 注册假页面；若没有这行代码，current_page 找不到页面。
            server.current_page_id = "page-1"  # 新增代码+BrowserRecordingStage9: 设置当前页面；若没有这行代码，录制工具省略 page_id 时无法定位。
            start_output = server.call("browser_record_start", {"recording_id": "server-rec", "page_id": "page-1"})  # 新增代码+BrowserRecordingStage9: 调用统一开始录制工具；若没有这行代码，dispatch 可能只在 schema 存在。
            self.assertIn("recording_id=server-rec", start_output)  # 新增代码+BrowserRecordingStage9: 断言工具返回录制 id；若没有这行代码，模型不知道当前证据编号。
            frame = server._capture_recording_frame("browser_click", "action-1")  # 新增代码+BrowserRecordingStage9: 通过 server helper 捕获一帧；若没有这行代码，自动帧路径无法验证。
            self.assertTrue(Path(frame["frame_path"]).exists())  # 新增代码+BrowserRecordingStage9: 断言帧 PNG 真实存在；若没有这行代码，录制可能只是 manifest。
            stop_output = server.call("browser_record_stop", {"recording_id": "server-rec"})  # 新增代码+BrowserRecordingStage9: 调用统一停止录制工具；若没有这行代码，录制状态无法收尾。
            self.assertIn("frame_count=", stop_output)  # 新增代码+BrowserRecordingStage9: 断言停止输出帧数；若没有这行代码，用户不知道证据是否完整。
            gif_output = server.call("browser_gif_export", {"recording_id": "server-rec", "output_name": "server-rec.gif"})  # 新增代码+BrowserRecordingStage9: 调用统一 GIF 导出工具；若没有这行代码，导出入口不会被验证。
            self.assertIn("gif_path=", gif_output)  # 新增代码+BrowserRecordingStage9: 断言工具返回 GIF 路径；若没有这行代码，用户找不到产物。
            gif_path = Path(gif_output.split("gif_path=", 1)[1].splitlines()[0].strip())  # 新增代码+BrowserRecordingStage9: 从工具输出提取 GIF 路径；若没有这行代码，无法验证真实文件。
            self.assertTrue(gif_path.exists())  # 新增代码+BrowserRecordingStage9: 断言 GIF 真实存在；若没有这行代码，工具可能返回假成功。

    def test_status_snapshot_and_renderer_list_recordings(self) -> None:  # 新增代码+BrowserRecordingStage9: 验证状态生态能看到录制证据；若没有这行代码，录制会成为旁路产物。
        from learning_agent.app.status_renderer import render_status_snapshot  # 新增代码+BrowserRecordingStage9: 导入终端渲染器；若没有这行代码，UI 不会被测试。
        from learning_agent.browser.recording import BrowserRecordingStore  # 新增代码+BrowserRecordingStage9: 导入录制 store；若没有这行代码，测试无法准备状态。
        from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+BrowserRecordingStage9: 导入统一状态快照；若没有这行代码，状态生态无测试目标。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRecordingStage9: 创建隔离 workspace；若没有这行代码，测试会读取真实录制。
            workspace = Path(raw_dir)  # 新增代码+BrowserRecordingStage9: 保存 workspace；若没有这行代码，各入口可能读不同路径。
            store = BrowserRecordingStore(workspace / "browser_artifacts" / "browser_recordings")  # 新增代码+BrowserRecordingStage9: 创建录制 store；若没有这行代码，无法准备 manifest。
            store.start_recording(recording_id="status-rec", run_id="run-status", page_id="page-1")  # 新增代码+BrowserRecordingStage9: 创建录制 manifest；若没有这行代码，状态快照无录制输入。
            frame_path = store.recording_dir("status-rec") / "frames" / "frame-0001.png"  # 新增代码+BrowserRecordingStage9: 定义测试帧路径；若没有这行代码，record_frame 没有文件。
            _write_png(frame_path, (10, 20, 30))  # 新增代码+BrowserRecordingStage9: 写入帧文件；若没有这行代码，状态中的 frame_count 不能证明文件存在。
            store.record_frame("status-rec", frame_path, tool_name="browser_snapshot", action_id="a1")  # 新增代码+BrowserRecordingStage9: 记录帧元数据；若没有这行代码，manifest 帧数为空。
            store.stop_recording("status-rec")  # 新增代码+BrowserRecordingStage9: 停止录制；若没有这行代码，状态还是 recording。
            store.export_gif("status-rec", output_name="status-rec.gif")  # 新增代码+BrowserRecordingStage9: 导出 GIF；若没有这行代码，状态不会显示 gif_path。
            snapshot = build_status_snapshot(workspace)  # 新增代码+BrowserRecordingStage9: 构建统一快照；若没有这行代码，断言没有对象。
            rendered = render_status_snapshot(snapshot)  # 新增代码+BrowserRecordingStage9: 渲染状态文本；若没有这行代码，终端 UI 不会被覆盖。
            recordings = snapshot["browser"]["recordings"]  # 新增代码+BrowserRecordingStage9: 读取录制区块；若没有这行代码，后续断言路径冗长。
            self.assertEqual(recordings["recording_count"], 1)  # 新增代码+BrowserRecordingStage9: 断言状态发现录制；若没有这行代码，状态可能漏扫目录。
            self.assertEqual(recordings["latest"]["recording_id"], "status-rec")  # 新增代码+BrowserRecordingStage9: 断言最新录制 id；若没有这行代码，状态排序可能错误。
            self.assertIn("Browser Recordings", rendered)  # 新增代码+BrowserRecordingStage9: 断言终端有录制区块；若没有这行代码，用户肉眼看不到视觉证据。
            self.assertIn("recording_id=status-rec", rendered)  # 新增代码+BrowserRecordingStage9: 断言录制 id 可见；若没有这行代码，用户找不到对应 manifest。
            self.assertIn("frame_count=1", rendered)  # 新增代码+BrowserRecordingStage9: 断言帧数可见；若没有这行代码，用户不知道录制是否有内容。
            self.assertIn("status-rec.gif", rendered)  # 新增代码+BrowserRecordingStage9: 断言 GIF 路径可见；若没有这行代码，用户无法快速打开证据。


if __name__ == "__main__":  # 新增代码+BrowserRecordingStage9: 支持直接运行本测试文件；若没有这行代码，单文件排查不方便。
    unittest.main()  # 新增代码+BrowserRecordingStage9: 直接运行时启动 unittest；若没有这行代码，python 文件本身不会执行测试。
