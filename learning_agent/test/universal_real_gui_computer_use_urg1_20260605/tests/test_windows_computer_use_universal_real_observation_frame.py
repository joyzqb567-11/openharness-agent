import io  # 新增代码+URG1RealObservationFrame：导入内存文本缓冲区来捕获 CLI 输出；如果没有这一行，测试无法检查真实终端会看到的固定 token。
import tempfile  # 新增代码+URG1RealObservationFrame：导入临时目录工具来隔离截图证据文件；如果没有这一行，测试可能污染项目真实 evidence 目录。
import unittest  # 新增代码+URG1RealObservationFrame：导入标准测试框架；如果没有这一行，自动化测试发现不了本文件。
from contextlib import redirect_stdout  # 新增代码+URG1RealObservationFrame：导入 stdout 重定向工具；如果没有这一行，main 输出无法被断言。
from pathlib import Path  # 新增代码+URG1RealObservationFrame：导入 Path 统一处理 Windows 路径；如果没有这一行，临时截图路径拼接会变脆弱。
from typing import Any  # 新增代码+URG1RealObservationFrame：导入 Any 描述 fake provider 的动态字典；如果没有这一行，测试里的接口形状不清楚。

from learning_agent.computer_use.universal_real_observation import PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MARKER, PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_OK_TOKEN, UniversalRealObservationFrameRuntime, main, run_universal_real_observation_frame_contract, universal_real_observation_frame_cli_line  # 新增代码+URG1RealObservationFrame：导入 URG-1 公开 API；如果没有这一行，红测无法证明模块缺失或 API 漂移。


class _Urg1FakeInventoryProbe:  # 新增代码+URG1RealObservationFrame：类段开始，提供只读窗口 inventory fake；如果没有这个类，单测会触碰用户真实桌面窗口。
    def snapshot(self) -> dict[str, Any]:  # 新增代码+URG1RealObservationFrame：函数段开始，返回稳定窗口快照；如果没有这段函数，runtime 拿不到目标窗口事实。
        window = {"app_id": "notepad.exe", "window_id": "hwnd:11601", "hwnd": 11601, "title_preview": "URG1 Contract Window", "title": "URG1 Contract Window", "rect": {"left": 10, "top": 20, "right": 610, "bottom": 420, "width": 600, "height": 400}}  # 新增代码+URG1RealObservationFrame：构造可截图可 UIA 的假窗口；如果没有这一行，观察帧没有目标身份。
        return {"windows": [window], "filtered_count": 0, "captured_at": "2026-06-05T00:00:00Z", "source": "urg1_fake_inventory", "active_window": window}  # 新增代码+URG1RealObservationFrame：返回标准 inventory 结构；如果没有这一行，窗口状态融合字段会缺失。
    # 新增代码+URG1RealObservationFrame：函数段结束，_Urg1FakeInventoryProbe.snapshot 到此结束；如果没有这个边界说明，初学者不容易看出 fake 快照范围。


class _Urg1FakeScreenshotPipeline:  # 新增代码+URG1RealObservationFrame：类段开始，提供只读截图 fake；如果没有这个类，单测会依赖真实屏幕截图权限。
    def __init__(self, artifact_path: Path) -> None:  # 新增代码+URG1RealObservationFrame：函数段开始，保存截图 artifact 路径；如果没有这段函数，fake 截图无法落到临时目录。
        self.artifact_path = artifact_path  # 新增代码+URG1RealObservationFrame：记录要返回的截图文件路径；如果没有这一行，capture_window 不知道写哪里。
    # 新增代码+URG1RealObservationFrame：函数段结束，_Urg1FakeScreenshotPipeline.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。
    def capture_window(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+URG1RealObservationFrame：函数段开始，模拟真实截图 pipeline 输出；如果没有这段函数，runtime 无法验证截图汇入 ObservationFrame。
        self.artifact_path.write_bytes(b"BM" + b"urg1-observation-frame")  # 新增代码+URG1RealObservationFrame：写入可存在的假 BMP 证据文件；如果没有这一行，artifact_openable 只能靠空字段冒充。
        return {"captured": True, "screenshot_captured": True, "screenshot_path": str(self.artifact_path), "screenshot_width": 600, "screenshot_height": 400, "screenshot_format": "bmp", "pixel_guard_passed": True, "artifact_openable": True, "screenshot_bytes_included": False, "provider": "urg1_fake_screenshot", "image_results": [{"artifact_path": str(self.artifact_path), "width": 600, "height": 400, "sensitive_text_included": False}], "actions_expanded": False}  # 新增代码+URG1RealObservationFrame：返回与真实 pipeline 兼容的截图摘要；如果没有这一行，观察融合无法证明截图证据可用。
    # 新增代码+URG1RealObservationFrame：函数段结束，_Urg1FakeScreenshotPipeline.capture_window 到此结束；如果没有这个边界说明，初学者不容易看出 fake 截图范围。


class _Urg1FakeUiaRuntime:  # 新增代码+URG1RealObservationFrame：类段开始，提供只读 UIA fake；如果没有这个类，单测会依赖 Windows UIAutomationClient。
    def observe_window(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+URG1RealObservationFrame：函数段开始，模拟 UIA 控件树读取；如果没有这段函数，runtime 无法证明 UIA 汇入 ObservationFrame。
        return {"captured": True, "real_uia_tree": True, "safe_window_only": True, "flat_nodes": [{"node_id": "0", "name": "Editor", "role": "Edit", "automation_id": "editor", "class_name": "Edit", "bounds": {"left": 30, "top": 80, "right": 580, "bottom": 380, "width": 550, "height": 300}, "clickable": True, "editable": True}], "node_count": 1, "bounds_available": True, "clickable_count": 1, "editable_count": 1, "sensitive_text_filtered": 0, "semantic_locator_available": True, "raw_text_included": False, "actions_expanded": False}  # 新增代码+URG1RealObservationFrame：返回可定位控件摘要；如果没有这一行，规划器后续拿不到控件候选。
    # 新增代码+URG1RealObservationFrame：函数段结束，_Urg1FakeUiaRuntime.observe_window 到此结束；如果没有这个边界说明，初学者不容易看出 fake UIA 范围。


class UniversalRealObservationFrameTests(unittest.TestCase):  # 新增代码+URG1RealObservationFrame：类段开始，集中验收 URG-1 真实观察帧；如果没有这个类，蓝图 URG-1 没有自动化护栏。
    def test_contract_reports_read_only_real_observation_frame(self) -> None:  # 新增代码+URG1RealObservationFrame：函数段开始，验收合同自检输出完整安全 token；如果没有这段测试，模块可能只输出文案不输出机器事实。
        report = run_universal_real_observation_frame_contract(real_smoke=False)  # 新增代码+URG1RealObservationFrame：运行无真实桌面副作用的合同自检；如果没有这一行，断言没有结构化报告来源。
        cli_line = universal_real_observation_frame_cli_line(report)  # 新增代码+URG1RealObservationFrame：把报告转成真实终端固定 token 行；如果没有这一行，场景验收无法复用同一格式。
        self.assertTrue(report["passed"])  # 新增代码+URG1RealObservationFrame：断言合同整体通过；如果没有这一行，局部字段成功但整体失败会被漏掉。
        self.assertTrue(report["real_observation_frame"])  # 新增代码+URG1RealObservationFrame：断言 ObservationFrame 已建立；如果没有这一行，URG-1 可能仍停留在分散截图/UIA 输出。
        self.assertTrue(report["real_window_inventory"])  # 新增代码+URG1RealObservationFrame：断言窗口 inventory 已进入帧；如果没有这一行，目标身份来源会缺失。
        self.assertTrue(report["real_screenshot_pipeline_used"])  # 新增代码+URG1RealObservationFrame：断言截图管线已接入；如果没有这一行，视觉证据可能只是占位。
        self.assertTrue(report["screenshot_artifact_openable"])  # 新增代码+URG1RealObservationFrame：断言截图证据可打开或至少可落盘；如果没有这一行，空路径也可能冒充成功。
        self.assertTrue(report["pixel_guard_passed"])  # 新增代码+URG1RealObservationFrame：断言像素验真通过；如果没有这一行，黑屏或空图可能被误判为成功。
        self.assertTrue(report["real_uia_provider_used"])  # 新增代码+URG1RealObservationFrame：断言 UIA 或真实控件树槽位已接入；如果没有这一行，后续目标定位缺少语义输入。
        self.assertTrue(report["target_window_identity_present"])  # 新增代码+URG1RealObservationFrame：断言目标窗口身份存在；如果没有这一行，后续动作前复核无法绑定目标。
        self.assertFalse(report["actions_expanded"])  # 新增代码+URG1RealObservationFrame：断言 URG-1 未扩大动作面；如果没有这一行，只读观察阶段可能误发输入。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+URG1RealObservationFrame：断言合同自检不触碰真实桌面；如果没有这一行，单测可能悄悄操作本机。
        self.assertEqual(0, report["low_level_event_count"])  # 新增代码+URG1RealObservationFrame：断言底层输入事件为 0；如果没有这一行，只读观察可能混入鼠标键盘动作。
        self.assertIn(PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MARKER, cli_line)  # 新增代码+URG1RealObservationFrame：断言 CLI 行包含 ready marker；如果没有这一行，真实终端无法稳定匹配阶段。
        self.assertIn(PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_OK_TOKEN, cli_line)  # 新增代码+URG1RealObservationFrame：断言 CLI 行包含 OK token；如果没有这一行，验收器无法区分成功和普通输出。
    # 新增代码+URG1RealObservationFrame：函数段结束，test_contract_reports_read_only_real_observation_frame 到此结束；如果没有这个边界说明，初学者不容易看出合同测试范围。

    def test_runtime_composes_injected_sources_without_desktop_actions(self) -> None:  # 新增代码+URG1RealObservationFrame：函数段开始，验收 runtime 能组合注入的窗口、截图和 UIA 来源；如果没有这段测试，代码可能只会跑固定自检。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+URG1RealObservationFrame：创建临时目录隔离截图 artifact；如果没有这一行，测试文件会散落到项目目录。
            artifact_path = Path(temp_dir) / "urg1_fake_screen.bmp"  # 新增代码+URG1RealObservationFrame：定义假截图路径；如果没有这一行，fake pipeline 没有落盘目标。
            runtime = UniversalRealObservationFrameRuntime(inventory_probe=_Urg1FakeInventoryProbe(), screenshot_pipeline=_Urg1FakeScreenshotPipeline(artifact_path), uia_runtime=_Urg1FakeUiaRuntime())  # 新增代码+URG1RealObservationFrame：创建注入式 runtime；如果没有这一行，测试无法证明生产依赖可以替换。
            frame = runtime.observe(target_hint="notepad")  # 新增代码+URG1RealObservationFrame：执行一次只读观察；如果没有这一行，断言没有 ObservationFrame 输入。
        self.assertTrue(frame["real_observation_frame"])  # 新增代码+URG1RealObservationFrame：断言帧标记为真；如果没有这一行，调用方不知道这是 URG-1 统一帧。
        self.assertTrue(frame["screenshot_observation"])  # 新增代码+URG1RealObservationFrame：断言截图观察进入帧；如果没有这一行，视觉目标定位会缺少证据。
        self.assertTrue(frame["uia_tree_observation"])  # 新增代码+URG1RealObservationFrame：断言 UIA 观察进入帧；如果没有这一行，控件目标定位会缺少证据。
        self.assertTrue(frame["window_state_observation"])  # 新增代码+URG1RealObservationFrame：断言窗口状态进入帧；如果没有这一行，目标身份复核缺少基础。
        self.assertEqual("hwnd:11601", frame["target_window"]["window_id"])  # 新增代码+URG1RealObservationFrame：断言目标窗口身份来自 inventory；如果没有这一行，runtime 可能随便选择空窗口。
        self.assertTrue(frame["screenshot"]["artifact_openable"])  # 新增代码+URG1RealObservationFrame：断言截图 artifact 可用；如果没有这一行，证据路径可能不可打开。
        self.assertEqual(1, frame["uia"]["node_count"])  # 新增代码+URG1RealObservationFrame：断言 UIA 节点数量被保留；如果没有这一行，规划器无法知道控件候选是否存在。
        self.assertFalse(frame["actions_expanded"])  # 新增代码+URG1RealObservationFrame：断言 runtime 未扩大动作面；如果没有这一行，观察帧可能混入真实输入。
        self.assertFalse(frame["real_desktop_touched"])  # 新增代码+URG1RealObservationFrame：断言注入式观察不触碰真实桌面；如果没有这一行，单测和生产边界会混淆。
        self.assertEqual(0, frame["low_level_event_count"])  # 新增代码+URG1RealObservationFrame：断言底层事件计数为 0；如果没有这一行，URG-1 只读边界不可验证。
    # 新增代码+URG1RealObservationFrame：函数段结束，test_runtime_composes_injected_sources_without_desktop_actions 到此结束；如果没有这个边界说明，初学者不容易看出 runtime 测试范围。

    def test_main_prints_fixed_visible_terminal_tokens(self) -> None:  # 新增代码+URG1RealObservationFrame：函数段开始，验收 main 输出可被真实终端场景复制；如果没有这段测试，controller 可能匹配不到最终回答。
        buffer = io.StringIO()  # 新增代码+URG1RealObservationFrame：创建输出缓冲区；如果没有这一行，main 的打印内容无法断言。
        with redirect_stdout(buffer):  # 新增代码+URG1RealObservationFrame：捕获 main 打印；如果没有这一行，测试只能看退出码。
            exit_code = main([])  # 新增代码+URG1RealObservationFrame：运行 URG-1 命令行入口；如果没有这一行，真实终端入口没有自动化覆盖。
        output = buffer.getvalue()  # 新增代码+URG1RealObservationFrame：读取捕获输出；如果没有这一行，后续 token 断言没有文本来源。
        self.assertEqual(0, exit_code)  # 新增代码+URG1RealObservationFrame：断言 main 成功退出；如果没有这一行，打印成功但退出失败会被漏掉。
        self.assertIn("real_observation_frame=true", output)  # 新增代码+URG1RealObservationFrame：断言输出包含观察帧 token；如果没有这一行，用户看不到 URG-1 核心能力。
        self.assertIn("real_window_inventory=true", output)  # 新增代码+URG1RealObservationFrame：断言输出包含窗口 inventory token；如果没有这一行，后续目标身份能力没有可见证据。
        self.assertIn("real_screenshot_pipeline_used=true", output)  # 新增代码+URG1RealObservationFrame：断言输出包含截图管线 token；如果没有这一行，视觉证据接入不可见。
        self.assertIn("real_uia_provider_used=true", output)  # 新增代码+URG1RealObservationFrame：断言输出包含 UIA token；如果没有这一行，语义定位接入不可见。
        self.assertIn("actions_expanded=false", output)  # 新增代码+URG1RealObservationFrame：断言输出明确未扩大动作；如果没有这一行，用户可能误解观察阶段已经能真实控制。
        self.assertIn("real_desktop_touched=false", output)  # 新增代码+URG1RealObservationFrame：断言合同入口不触碰真实桌面；如果没有这一行，安全边界不可见。
        self.assertIn("low_level_event_count=0", output)  # 新增代码+URG1RealObservationFrame：断言底层事件为 0；如果没有这一行，验收无法证明只读。
    # 新增代码+URG1RealObservationFrame：函数段结束，test_main_prints_fixed_visible_terminal_tokens 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 测试范围。
# 新增代码+URG1RealObservationFrame：类段结束，UniversalRealObservationFrameTests 到此结束；如果没有这个边界说明，初学者不容易看出 URG-1 测试集合范围。


if __name__ == "__main__":  # 新增代码+URG1RealObservationFrame：文件入口段开始，允许直接运行本测试文件；如果没有这一行，初学者需要记住完整 unittest 命令。
    unittest.main()  # 新增代码+URG1RealObservationFrame：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+URG1RealObservationFrame：文件入口段结束，本测试文件到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
