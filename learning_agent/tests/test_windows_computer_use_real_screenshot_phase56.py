import json  # 新增代码+Phase56RealScreenshotPipeline: 导入 JSON 用来检查协议响应是否泄露原始 bytes；如果没有这行代码，测试无法稳定审计结构化结果。
import tempfile  # 新增代码+Phase56RealScreenshotPipeline: 导入临时目录隔离截图 artifact；如果没有这行代码，测试会污染真实 evidence 目录。
import unittest  # 新增代码+Phase56RealScreenshotPipeline: 导入 unittest 框架承载 Phase56 测试；如果没有这行代码，自动化回归不会执行本文件。
from pathlib import Path  # 新增代码+Phase56RealScreenshotPipeline: 导入 Path 检查 artifact 是否真实落盘；如果没有这行代码，路径判断会变成脆弱字符串。

from learning_agent.computer_use.native_helper import NativeWindowCaptureResult  # 新增代码+Phase56RealScreenshotPipeline: 复用既有截图结果合同；如果没有这行代码，测试会和 Phase45/55 截图协议割裂。
from learning_agent.computer_use.native_helper_v2 import WindowsNativeHelperV2Worker  # 新增代码+Phase56RealScreenshotPipeline: 导入 helper v2 worker 验证 capture_window 接入；如果没有这行代码，Phase56 可能只实现孤立 pipeline。
from learning_agent.computer_use.real_screenshot_pipeline import PHASE56_WINDOWS_REAL_SCREENSHOT_MARKER, PHASE56_WINDOWS_REAL_SCREENSHOT_OK_TOKEN, Phase56PixelGuard, WindowsRealScreenshotPipeline, build_phase56_test_bmp, phase56_cli_line, run_phase56_real_screenshot_pipeline_contract  # 新增代码+Phase56RealScreenshotPipeline: 导入 Phase56 预期新增模块；如果没有这行代码，红灯会证明真实截图 pipeline 尚未实现。


class FakePhase56CaptureProvider:  # 新增代码+Phase56RealScreenshotPipeline: 定义可控截图 provider；如果没有这个类，单元测试只能触碰真实桌面。
    def __init__(self, backend: str, screenshot_bytes: bytes, width: int, height: int) -> None:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，初始化 fake provider；如果没有这段函数，测试无法注入不同像素内容。
        self.backend = backend  # 新增代码+Phase56RealScreenshotPipeline: 保存 provider 名称；如果没有这行代码，pipeline 结果无法说明截图来源。
        self.screenshot_bytes = screenshot_bytes  # 新增代码+Phase56RealScreenshotPipeline: 保存截图 bytes；如果没有这行代码，fake provider 没有可返回图片。
        self.width = int(width)  # 新增代码+Phase56RealScreenshotPipeline: 保存宽度；如果没有这行代码，pixel guard 无法做尺寸校验。
        self.height = int(height)  # 新增代码+Phase56RealScreenshotPipeline: 保存高度；如果没有这行代码，pixel guard 无法做尺寸校验。
        self.calls: list[int] = []  # 新增代码+Phase56RealScreenshotPipeline: 记录被调用 hwnd；如果没有这行代码，测试无法确认 provider 真被执行。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，FakePhase56CaptureProvider.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def status(self) -> dict[str, object]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，返回 provider 状态；如果没有这段函数，pipeline status 会缺 provider 摘要。
        return {"backend": self.backend, "available": True, "reason": "phase56 fake provider", "contract_ready": True}  # 新增代码+Phase56RealScreenshotPipeline: 返回稳定 provider 状态；如果没有这行代码，状态测试和审计字段会漂移。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，FakePhase56CaptureProvider.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def capture_window(self, hwnd: int) -> NativeWindowCaptureResult:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，返回可控截图结果；如果没有这段函数，pipeline 无法执行截图路径。
        self.calls.append(int(hwnd))  # 新增代码+Phase56RealScreenshotPipeline: 记录 hwnd；如果没有这行代码，测试无法证明 pipeline 调用了 provider。
        return NativeWindowCaptureResult(captured=True, screenshot_bytes=self.screenshot_bytes, screenshot_format="bmp", screenshot_width=self.width, screenshot_height=self.height, backend=self.backend, reason=f"{self.backend} captured {hwnd}")  # 新增代码+Phase56RealScreenshotPipeline: 返回统一截图结果；如果没有这行代码，pipeline 没有可分析像素。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，FakePhase56CaptureProvider.capture_window 到此结束；如果没有这个边界说明，初学者不容易看出 fake 截图范围。


class WindowsComputerUseRealScreenshotPhase56Tests(unittest.TestCase):  # 新增代码+Phase56RealScreenshotPipeline: 类段开始，组织 Phase56 测试；如果没有这个类，unittest 不会发现本阶段门禁。
    def _window(self) -> dict[str, object]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，提供稳定安全窗口引用；如果没有这段函数，各测试会重复拼窗口 dict。
        return {"window_id": "hwnd:5601", "hwnd": 5601, "title": "Phase56 Safe Window", "rect": {"left": 20, "top": 30, "right": 220, "bottom": 150}}  # 新增代码+Phase56RealScreenshotPipeline: 返回含 hwnd/rect 的窗口；如果没有这行代码，pipeline 无法解析截图目标和尺寸。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口样本范围。

    def test_pixel_guard_accepts_diverse_bmp_and_rejects_blank_bmp(self) -> None:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，验证 pixel guard 能区分有效截图和空白截图；如果没有这个测试，黑屏/白屏可能误过。
        guard = Phase56PixelGuard()  # 新增代码+Phase56RealScreenshotPipeline: 创建像素检测器；如果没有这行代码，被测对象不存在。
        valid_bmp = build_phase56_test_bmp(120, 80, title_color=(30, 60, 120), body_color=(240, 240, 240), accent_color=(10, 10, 10))  # 新增代码+Phase56RealScreenshotPipeline: 构造有标题栏和正文差异的 BMP；如果没有这行代码，有效截图路径没有输入。
        black_bmp = build_phase56_test_bmp(120, 80, title_color=(0, 0, 0), body_color=(0, 0, 0), accent_color=(0, 0, 0))  # 新增代码+Phase56RealScreenshotPipeline: 构造全黑 BMP；如果没有这行代码，全黑拒绝路径没有输入。
        white_bmp = build_phase56_test_bmp(120, 80, title_color=(255, 255, 255), body_color=(255, 255, 255), accent_color=(255, 255, 255))  # 新增代码+Phase56RealScreenshotPipeline: 构造全白 BMP；如果没有这行代码，空白拒绝路径没有输入。

        valid_report = guard.inspect_bytes(valid_bmp, "bmp", expected_width=120, expected_height=80)  # 新增代码+Phase56RealScreenshotPipeline: 分析有效 BMP；如果没有这行代码，断言没有实际报告。
        black_report = guard.inspect_bytes(black_bmp, "bmp", expected_width=120, expected_height=80)  # 新增代码+Phase56RealScreenshotPipeline: 分析全黑 BMP；如果没有这行代码，全黑分支不被覆盖。
        white_report = guard.inspect_bytes(white_bmp, "bmp", expected_width=120, expected_height=80)  # 新增代码+Phase56RealScreenshotPipeline: 分析全白 BMP；如果没有这行代码，全白分支不被覆盖。

        self.assertTrue(valid_report["passed"])  # 新增代码+Phase56RealScreenshotPipeline: 断言有效截图通过；如果没有这行代码，pixel guard 可能过严导致真实截图无法用。
        self.assertTrue(valid_report["title_region_visible"])  # 新增代码+Phase56RealScreenshotPipeline: 断言标题区域可见；如果没有这行代码，窗口标题区校验可能缺失。
        self.assertGreater(valid_report["unique_color_count"], 2)  # 新增代码+Phase56RealScreenshotPipeline: 断言像素不是单色；如果没有这行代码，全色块截图可能误过。
        self.assertFalse(black_report["passed"])  # 新增代码+Phase56RealScreenshotPipeline: 断言全黑截图失败；如果没有这行代码，黑屏可能被当成成功。
        self.assertTrue(black_report["all_black"])  # 新增代码+Phase56RealScreenshotPipeline: 断言报告说明全黑；如果没有这行代码，失败原因不可解释。
        self.assertFalse(white_report["passed"])  # 新增代码+Phase56RealScreenshotPipeline: 断言全白截图失败；如果没有这行代码，空白窗口可能误过。
        self.assertTrue(white_report["all_white"])  # 新增代码+Phase56RealScreenshotPipeline: 断言报告说明全白；如果没有这行代码，失败原因不可解释。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，test_pixel_guard_accepts_diverse_bmp_and_rejects_blank_bmp 到此结束；如果没有这个边界说明，初学者不容易看出 pixel guard 测试范围。

    def test_pipeline_writes_guarded_artifact_and_image_result_without_raw_bytes(self) -> None:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，验证 pipeline 写入经过 pixel guard 的 artifact；如果没有这个测试，截图可能落盘但没有像素验真。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase56RealScreenshotPipeline: 创建临时 evidence 目录；如果没有这行代码，测试会污染真实 memory。
            bmp = build_phase56_test_bmp(200, 120, title_color=(20, 80, 160), body_color=(245, 245, 245), accent_color=(5, 5, 5))  # 新增代码+Phase56RealScreenshotPipeline: 构造有效 BMP；如果没有这行代码，pipeline 没有可通过的截图。
            provider = FakePhase56CaptureProvider("win32_gdi_printwindow", bmp, 200, 120)  # 新增代码+Phase56RealScreenshotPipeline: 准备 fake GDI provider；如果没有这行代码，测试会触碰真实桌面。
            pipeline = WindowsRealScreenshotPipeline(providers=[provider], evidence_root=Path(raw_dir), platform="win32")  # 新增代码+Phase56RealScreenshotPipeline: 创建 Phase56 pipeline；如果没有这行代码，被测对象不存在。
            result = pipeline.capture_window(self._window())  # 新增代码+Phase56RealScreenshotPipeline: 执行截图 pipeline；如果没有这行代码，断言没有实际结果。
            serialized = json.dumps(result, ensure_ascii=False, default=str)  # 新增代码+Phase56RealScreenshotPipeline: 序列化响应用于泄露检查；如果没有这行代码，原始 bytes 泄露不易发现。

            self.assertTrue(result["captured"])  # 新增代码+Phase56RealScreenshotPipeline: 断言截图成功；如果没有这行代码，空响应也可能误过。
            self.assertTrue(result["pixel_guard_passed"])  # 新增代码+Phase56RealScreenshotPipeline: 断言 pixel guard 通过；如果没有这行代码，截图成功和截图可信会混淆。
            self.assertTrue(result["artifact_openable"])  # 新增代码+Phase56RealScreenshotPipeline: 断言 artifact 可打开解析；如果没有这行代码，坏文件可能误过。
            self.assertEqual(result["image_result_count"], 1)  # 新增代码+Phase56RealScreenshotPipeline: 断言 image_result 已生成；如果没有这行代码，模型可能看不到截图。
            self.assertTrue(Path(result["screenshot_path"]).exists())  # 新增代码+Phase56RealScreenshotPipeline: 断言截图文件真实存在；如果没有这行代码，路径可能是假的。
            self.assertFalse(result["screenshot_bytes_included"])  # 新增代码+Phase56RealScreenshotPipeline: 断言 JSON 不带原始 bytes；如果没有这行代码，大图可能泄露进 IPC。
            self.assertNotIn("BM" + "\x00", serialized)  # 新增代码+Phase56RealScreenshotPipeline: 粗略断言 BMP 原始内容没有被直接塞进 JSON；如果没有这行代码，脱敏边界可能漏验。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，test_pipeline_writes_guarded_artifact_and_image_result_without_raw_bytes 到此结束；如果没有这个边界说明，初学者不容易看出 pipeline 成功测试范围。

    def test_pipeline_rejects_blank_capture_before_artifact_is_accepted(self) -> None:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，验证空白截图不能变成通过 artifact；如果没有这个测试，fake/黑屏截图可能进入生产链。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase56RealScreenshotPipeline: 创建临时 evidence 目录；如果没有这行代码，失败路径可能污染真实 evidence。
            blank_bmp = build_phase56_test_bmp(160, 90, title_color=(0, 0, 0), body_color=(0, 0, 0), accent_color=(0, 0, 0))  # 新增代码+Phase56RealScreenshotPipeline: 构造全黑 BMP；如果没有这行代码，拒绝路径没有像素输入。
            provider = FakePhase56CaptureProvider("win32_gdi_printwindow", blank_bmp, 160, 90)  # 新增代码+Phase56RealScreenshotPipeline: 准备返回黑屏的 provider；如果没有这行代码，无法模拟真实黑屏。
            pipeline = WindowsRealScreenshotPipeline(providers=[provider], evidence_root=Path(raw_dir), platform="win32")  # 新增代码+Phase56RealScreenshotPipeline: 创建 pipeline；如果没有这行代码，被测失败路径不存在。
            result = pipeline.capture_window(self._window())  # 新增代码+Phase56RealScreenshotPipeline: 执行失败截图；如果没有这行代码，断言没有对象。

            self.assertFalse(result["captured"])  # 新增代码+Phase56RealScreenshotPipeline: 断言黑屏不算截图成功；如果没有这行代码，黑屏可能误过。
            self.assertFalse(result["pixel_guard_passed"])  # 新增代码+Phase56RealScreenshotPipeline: 断言 pixel guard 失败；如果没有这行代码，失败原因可能丢失。
            self.assertFalse(result["artifact_openable"])  # 新增代码+Phase56RealScreenshotPipeline: 断言失败截图不接受为可用 artifact；如果没有这行代码，坏图可能被模型引用。
            self.assertEqual(result["image_result_count"], 0)  # 新增代码+Phase56RealScreenshotPipeline: 断言没有 image_result；如果没有这行代码，模型可能看到不可用截图。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，test_pipeline_rejects_blank_capture_before_artifact_is_accepted 到此结束；如果没有这个边界说明，初学者不容易看出失败路径范围。

    def test_helper_v2_capture_uses_phase56_pipeline_summary(self) -> None:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，验证 helper v2 capture_window 接入 Phase56；如果没有这个测试，out-of-process helper 可能仍停留占位。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase56RealScreenshotPipeline: 创建临时 evidence 目录；如果没有这行代码，helper 测试会污染真实目录。
            bmp = build_phase56_test_bmp(180, 100, title_color=(50, 80, 130), body_color=(245, 245, 245), accent_color=(0, 0, 0))  # 新增代码+Phase56RealScreenshotPipeline: 构造有效 BMP；如果没有这行代码，helper capture 没有可通过截图。
            pipeline = WindowsRealScreenshotPipeline(providers=[FakePhase56CaptureProvider("win32_gdi_printwindow", bmp, 180, 100)], evidence_root=Path(raw_dir), platform="win32")  # 新增代码+Phase56RealScreenshotPipeline: 创建注入式 pipeline；如果没有这行代码，worker 会依赖真实桌面。
            worker = WindowsNativeHelperV2Worker(screenshot_pipeline=pipeline)  # 新增代码+Phase56RealScreenshotPipeline: 把 Phase56 pipeline 注入 helper v2 worker；如果没有这行代码，helper v2 无法被单元测试稳定覆盖。
            response = worker.handle({"op": "capture_window", "window": self._window()})  # 新增代码+Phase56RealScreenshotPipeline: 通过 helper v2 协议请求截图；如果没有这行代码，集成路径不会执行。

            self.assertTrue(response["ok"])  # 新增代码+Phase56RealScreenshotPipeline: 断言 helper v2 协议成功；如果没有这行代码，错误 envelope 可能误过。
            self.assertTrue(response["result"]["captured"])  # 新增代码+Phase56RealScreenshotPipeline: 断言 helper 返回真实截图摘要；如果没有这行代码，capture 可能仍是占位。
            self.assertTrue(response["result"]["pixel_guard_passed"])  # 新增代码+Phase56RealScreenshotPipeline: 断言 helper 摘要携带 pixel guard 结果；如果没有这行代码，主 agent 不知道截图是否可信。
            self.assertFalse(response["result"]["screenshot_bytes_included"])  # 新增代码+Phase56RealScreenshotPipeline: 断言 helper 不返回原始 bytes；如果没有这行代码，IPC 可能泄露截图内容。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，test_helper_v2_capture_uses_phase56_pipeline_summary 到此结束；如果没有这个边界说明，初学者不容易看出 helper v2 集成测试范围。

    def test_phase56_cli_contract_and_visible_terminal_scenario_tokens(self) -> None:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，验证 CLI 合同和真实终端场景 token；如果没有这个测试，Phase56 可能无法被真实终端验收。
        report = run_phase56_real_screenshot_pipeline_contract(real_smoke=False)  # 新增代码+Phase56RealScreenshotPipeline: 运行不触碰真实桌面的合同自检；如果没有这行代码，CLI 行没有稳定输入。
        cli_line = phase56_cli_line(report)  # 新增代码+Phase56RealScreenshotPipeline: 生成稳定 token 行；如果没有这行代码，场景无法复用同一格式。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase56_real_screenshot_pipeline.json")  # 新增代码+Phase56RealScreenshotPipeline: 定位 Phase56 场景；如果没有这行代码，真实终端配置缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase56RealScreenshotPipeline: 读取场景 JSON；如果没有这行代码，token 是否写入场景无法检查。
        cli_tokens = {PHASE56_WINDOWS_REAL_SCREENSHOT_MARKER, PHASE56_WINDOWS_REAL_SCREENSHOT_OK_TOKEN, "pixel_guard=true", "artifact=true", "helper_v2_capture=true", "raw_bytes_hidden=true", "actions_expanded=false"}  # 新增代码+Phase56RealScreenshotPipeline: 定义合同自检必须包含的 token；如果没有这行代码，验收输出标准会漂移。
        scenario_tokens = cli_tokens | {"real_smoke=true"}  # 新增代码+Phase56RealScreenshotPipeline: 定义真实终端额外必须包含真实 smoke token；如果没有这行代码，场景可能只检查 fake 合同。
        for token in cli_tokens:  # 新增代码+Phase56RealScreenshotPipeline: 遍历 CLI token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase56RealScreenshotPipeline: 断言 CLI 行包含 token；如果没有这行代码，自检输出可能不稳定。
        for token in scenario_tokens:  # 新增代码+Phase56RealScreenshotPipeline: 遍历场景 token；如果没有这行代码，真实终端门禁可能漏检。
            self.assertIn(token, scenario_text)  # 新增代码+Phase56RealScreenshotPipeline: 断言场景包含 token；如果没有这行代码，可见终端验收可能只证明假截图。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，test_phase56_cli_contract_and_visible_terminal_scenario_tokens 到此结束；如果没有这个边界说明，初学者不容易看出 CLI/场景测试范围。


if __name__ == "__main__":  # 新增代码+Phase56RealScreenshotPipeline: 允许直接运行测试文件；如果没有这行代码，初学者无法手动启动本阶段测试。
    unittest.main()  # 新增代码+Phase56RealScreenshotPipeline: 启动 unittest；如果没有这行代码，直接运行文件不会执行任何测试。
