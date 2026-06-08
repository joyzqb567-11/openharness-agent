import json  # 新增代码+Phase66ObservationFusion: 导入 JSON 用来校验场景文件和检查融合结果是否泄露敏感文本；如果没有这行代码，测试无法覆盖结构化输出安全边界。
import unittest  # 新增代码+Phase66ObservationFusion: 导入 unittest 承载 Phase66 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase66ObservationFusion: 导入 Path 处理 Windows 场景文件路径；如果没有这行代码，路径拼接容易在不同工作目录下失败。

from learning_agent.computer_use.observation_fusion import PHASE66_OBSERVATION_FUSION_MARKER, PHASE66_OBSERVATION_FUSION_OK_TOKEN, WindowsObservationFusionRuntime, phase66_cli_line, run_phase66_observation_fusion_contract  # 新增代码+Phase66ObservationFusion: 导入 Phase66 观察融合 API；如果没有这行代码，红灯测试无法证明生产模块尚未实现。


class WindowsComputerUseObservationFusionPhase66Tests(unittest.TestCase):  # 新增代码+Phase66ObservationFusion: 类段开始，集中验证 Phase66 截图、UIA、OCR/vision 插槽和窗口状态融合；如果没有这个类，Phase66 没有自动化门禁。
    def test_phase66_contract_fuses_screenshot_uia_ocr_slot_and_window_state(self) -> None:  # 新增代码+Phase66ObservationFusion: 函数段开始，验证 Phase66 合同融合所有只读观察来源且不扩展动作；如果没有这个测试，后续闭环执行器会缺少统一观察事实源。
        report = run_phase66_observation_fusion_contract()  # 新增代码+Phase66ObservationFusion: 运行 Phase66 合同自检；如果没有这行代码，测试没有真实报告来源。
        self.assertEqual(report["marker"], PHASE66_OBSERVATION_FUSION_MARKER)  # 新增代码+Phase66ObservationFusion: 断言 ready marker 稳定；如果没有这行代码，真实终端验收可能匹配不到 Phase66 输出。
        self.assertEqual(report["ok_token"], PHASE66_OBSERVATION_FUSION_OK_TOKEN)  # 新增代码+Phase66ObservationFusion: 断言 OK token 稳定；如果没有这行代码，用户无法一眼判断合同是否通过。
        self.assertTrue(report["screenshot_observation"])  # 新增代码+Phase66ObservationFusion: 断言截图观察已进入融合对象；如果没有这行代码，后续视觉推理会缺失屏幕证据。
        self.assertTrue(report["uia_tree_observation"])  # 新增代码+Phase66ObservationFusion: 断言 UIA 控件树观察已进入融合对象；如果没有这行代码，后续语义定位会缺少控件事实。
        self.assertTrue(report["ocr_or_vision_slot"])  # 新增代码+Phase66ObservationFusion: 断言 OCR/vision 预留槽存在；如果没有这行代码，后续补视觉依赖时会破坏协议。
        self.assertTrue(report["window_state_observation"])  # 新增代码+Phase66ObservationFusion: 断言窗口状态观察已进入融合对象；如果没有这行代码，动作执行前无法确认目标窗口身份。
        self.assertTrue(report["sensitive_text_boundary"])  # 新增代码+Phase66ObservationFusion: 断言敏感文本边界生效；如果没有这行代码，UIA 或 OCR 原文可能泄露进模型上下文。
        self.assertTrue(report["uia_ocr_vision_fusion"])  # 新增代码+Phase66ObservationFusion: 断言 UIA/OCR/vision 融合 token 成立；如果没有这行代码，后续规划器无法判断观察层可用。
        self.assertFalse(report["actions_expanded"])  # 新增代码+Phase66ObservationFusion: 断言 Phase66 不扩展真实桌面动作；如果没有这行代码，本阶段可能提前打开没有授权保护的输入能力。
        observation = report["fused_observation"]  # 新增代码+Phase66ObservationFusion: 读取融合观察对象；如果没有这行代码，下面无法检查嵌套字段。
        self.assertFalse(observation["ocr"]["provider_available"])  # 新增代码+Phase66ObservationFusion: 断言默认不声称 OCR provider 已安装；如果没有这行代码，系统可能误导用户以为视觉依赖可用。
        self.assertFalse(observation["ocr"]["install_attempted"])  # 新增代码+Phase66ObservationFusion: 断言合同自检没有尝试安装 OCR；如果没有这行代码，验收可能悄悄改变本机环境。
        self.assertFalse(observation["raw_text_included"])  # 新增代码+Phase66ObservationFusion: 断言融合对象不包含原始敏感文本；如果没有这行代码，用户隐私边界不可靠。
    # 新增代码+Phase66ObservationFusion: 函数段结束，test_phase66_contract_fuses_screenshot_uia_ocr_slot_and_window_state 到此结束；如果没有这个边界说明，初学者不容易看出合同测试范围。

    def test_phase66_runtime_accepts_injected_results_and_hides_sensitive_uia_text(self) -> None:  # 新增代码+Phase66ObservationFusion: 函数段开始，验证 runtime 能用注入 fake 结果融合并隐藏敏感 UIA 文本；如果没有这个测试，真实 provider 之外的可测性和脱敏边界会漂移。
        runtime = WindowsObservationFusionRuntime()  # 新增代码+Phase66ObservationFusion: 创建观察融合 runtime；如果没有这行代码，测试无法直接验证注入式融合逻辑。
        window = {"app_id": "mspaint.exe", "window_id": "hwnd:6601", "title_preview": "LearningAgent Phase66 Paint", "rect": {"left": 10, "top": 20, "right": 810, "bottom": 620}}  # 新增代码+Phase66ObservationFusion: 构造代表普通 Windows 应用的窗口引用；如果没有这行代码，窗口状态融合没有输入。
        screenshot_result = {"screenshot_captured": True, "screenshot_path": "H:/tmp/phase66.bmp", "screenshot_width": 800, "screenshot_height": 600, "screenshot_format": "bmp", "pixel_guard_passed": True, "artifact_openable": True, "screenshot_bytes_included": False, "image_results": [{"type": "image_result", "artifact_path": "H:/tmp/phase66.bmp", "width": 800, "height": 600, "sensitive_text_included": False}]}  # 新增代码+Phase66ObservationFusion: 构造 fake 截图结果；如果没有这行代码，截图融合和图片块计数无法测试。
        uia_result = {"captured": True, "real_uia_tree": True, "raw_text_included": False, "flat_nodes": [{"node_id": "0", "name": "Paint canvas", "role": "Document", "automation_id": "canvas", "class_name": "Canvas", "bounds": {"left": 30, "top": 90, "right": 780, "bottom": 560, "width": 750, "height": 470}, "clickable": True, "editable": False}, {"node_id": "1", "name": "password: phase66-secret", "role": "Edit", "automation_id": "secret", "class_name": "Edit", "bounds": {"left": 30, "top": 570, "right": 780, "bottom": 600, "width": 750, "height": 30}, "clickable": True, "editable": True}], "node_count": 2, "clickable_count": 2, "editable_count": 1, "bounds_available": True, "sensitive_text_filtered": 0}  # 新增代码+Phase66ObservationFusion: 构造带敏感文本的 fake UIA 结果；如果没有这行代码，脱敏边界没有可验证输入。
        inventory_result = {"windows": [window], "filtered_count": 0, "captured_at": "2026-06-03T12:00:00Z", "source": "phase66-test", "active_window": window}  # 新增代码+Phase66ObservationFusion: 构造 fake 窗口 inventory；如果没有这行代码，窗口状态融合只能靠 window 参数猜测。
        fused = runtime.observe(window, screenshot_result, uia_result, inventory_result)  # 新增代码+Phase66ObservationFusion: 执行融合观察；如果没有这行代码，测试无法验证 runtime 行为。
        serialized = json.dumps(fused, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase66ObservationFusion: 序列化融合对象检查敏感值；如果没有这行代码，嵌套泄露难以发现。
        self.assertTrue(fused["screenshot"]["available"])  # 新增代码+Phase66ObservationFusion: 断言截图摘要可用；如果没有这行代码，fake 截图可能没有进入融合结果。
        self.assertTrue(fused["uia"]["available"])  # 新增代码+Phase66ObservationFusion: 断言 UIA 摘要可用；如果没有这行代码，fake 控件树可能被丢弃。
        self.assertTrue(fused["window_state"]["available"])  # 新增代码+Phase66ObservationFusion: 断言窗口状态摘要可用；如果没有这行代码，目标窗口身份可能丢失。
        self.assertGreaterEqual(fused["uia"]["sensitive_text_filtered"], 1)  # 修改代码+Phase66ObservationFusion: 断言至少过滤到一处敏感 UIA 文本；如果没有这行代码，脱敏行为可能失效，而不钉死次数是因为 automation_id 等字段也可能被安全过滤。
        self.assertNotIn("phase66-secret", serialized)  # 新增代码+Phase66ObservationFusion: 断言具体敏感值没有进入输出；如果没有这行代码，密码/token 类文本可能泄露。
        self.assertFalse(fused["ocr"]["install_attempted"])  # 新增代码+Phase66ObservationFusion: 断言 runtime 没有尝试安装 OCR；如果没有这行代码，测试无法保护本机环境边界。
        self.assertFalse(fused["actions_expanded"])  # 新增代码+Phase66ObservationFusion: 断言 runtime 不扩展真实动作；如果没有这行代码，融合层可能被误用成动作层。
    # 新增代码+Phase66ObservationFusion: 函数段结束，test_phase66_runtime_accepts_injected_results_and_hides_sensitive_uia_text 到此结束；如果没有这个边界说明，初学者不容易看出 runtime 测试范围。

    def test_phase66_cli_line_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase66ObservationFusion: 函数段开始，验证 CLI 行和真实终端场景 token 稳定；如果没有这个测试，controller 场景可能和模块输出脱节。
        report = run_phase66_observation_fusion_contract()  # 新增代码+Phase66ObservationFusion: 运行合同报告作为 CLI 输出来源；如果没有这行代码，token 测试没有结构化来源。
        cli_line = phase66_cli_line(report)  # 新增代码+Phase66ObservationFusion: 生成稳定 CLI token 行；如果没有这行代码，真实终端最终回答需要解析复杂 JSON。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase66_observation_fusion.json")  # 新增代码+Phase66ObservationFusion: 定位 Phase66 真实终端验收场景；如果没有这行代码，场景缺失不会被测试发现。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase66ObservationFusion: 读取场景文本；如果没有这行代码，场景 token 漏配无法被发现。
        json.loads(scenario_text)  # 新增代码+Phase66ObservationFusion: 校验场景是合法 JSON；如果没有这行代码，controller 运行时才会暴露格式错误。
        expected_tokens = {PHASE66_OBSERVATION_FUSION_MARKER, PHASE66_OBSERVATION_FUSION_OK_TOKEN, "screenshot_observation=true", "uia_tree_observation=true", "ocr_or_vision_slot=true", "window_state_observation=true", "sensitive_text_boundary=true", "uia_ocr_vision_fusion=true", "actions_expanded=false"}  # 新增代码+Phase66ObservationFusion: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase66ObservationFusion: 遍历每个关键 token；如果没有这行代码，重复断言容易遗漏。
            self.assertIn(token, cli_line)  # 新增代码+Phase66ObservationFusion: 断言 CLI 输出包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase66ObservationFusion: 断言真实终端场景也包含 token；如果没有这行代码，自动测试和真实验收可能不一致。
    # 新增代码+Phase66ObservationFusion: 函数段结束，test_phase66_cli_line_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 token 测试范围。
# 新增代码+Phase66ObservationFusion: 类段结束，WindowsComputerUseObservationFusionPhase66Tests 到此结束；如果没有这个边界说明，初学者不容易看出 Phase66 测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase66ObservationFusion: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase66ObservationFusion: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
