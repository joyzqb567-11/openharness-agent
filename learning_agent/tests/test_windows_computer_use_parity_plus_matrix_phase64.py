import json  # 新增代码+Phase64ParityPlusMatrix: 导入 JSON 用来读取真实终端验收场景；如果没有这行代码，测试无法确认场景 token 是否和 CLI 输出一致。
import tempfile  # 新增代码+Phase64ParityPlusMatrix: 导入临时目录用来隔离 Phase64 合同证据；如果没有这行代码，测试可能污染真实 memory 目录。
import unittest  # 新增代码+Phase64ParityPlusMatrix: 导入 unittest 承载 Phase64 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase64ParityPlusMatrix: 导入 Path 处理 Windows 路径；如果没有这行代码，场景文件和临时目录路径容易拼错。

from learning_agent.computer_use.parity_plus_matrix import PHASE64_EXPECTED_PHASE_COUNT, PHASE64_WINDOWS_PARITY_PLUS_MATRIX_MARKER, PHASE64_WINDOWS_PARITY_PLUS_MATRIX_OK_TOKEN, phase64_cli_line, run_phase64_parity_plus_matrix_contract  # 新增代码+Phase64ParityPlusMatrix: 导入预期 Phase64 最终矩阵 API；如果没有这行代码，红灯无法证明生产模块尚未实现。


class WindowsComputerUseParityPlusMatrixPhase64Tests(unittest.TestCase):  # 新增代码+Phase64ParityPlusMatrix: 类段开始，集中验证 Phase53-63 最终生产矩阵；如果没有这个类，Phase64 没有自动化门禁。
    def test_phase64_contract_rolls_up_phase53_to_phase63_without_uncontrolled_actions(self) -> None:  # 新增代码+Phase64ParityPlusMatrix: 函数段开始，验证 Phase64 汇总所有前置阶段且不新增无保护动作面；如果没有这个测试，总矩阵可能漏阶段或误放宽安全边界。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase64ParityPlusMatrix: 使用临时目录隔离合同运行；如果没有这行代码，合同会把测试证据写入真实运行目录。
            report = run_phase64_parity_plus_matrix_contract(base_dir=Path(temp_dir) / "phase64")  # 新增代码+Phase64ParityPlusMatrix: 运行 Phase64 最终矩阵合同；如果没有这行代码，测试没有真实报告来源。
        self.assertEqual(report["marker"], PHASE64_WINDOWS_PARITY_PLUS_MATRIX_MARKER)  # 新增代码+Phase64ParityPlusMatrix: 断言 marker 稳定；如果没有这行代码，真实终端验收无法稳定匹配 Phase64。
        self.assertEqual(report["ok_token"], PHASE64_WINDOWS_PARITY_PLUS_MATRIX_OK_TOKEN)  # 新增代码+Phase64ParityPlusMatrix: 断言 OK token 稳定；如果没有这行代码，用户看不到最终矩阵是否通过。
        self.assertEqual(report["phase_count"], PHASE64_EXPECTED_PHASE_COUNT)  # 新增代码+Phase64ParityPlusMatrix: 断言覆盖 11 个阶段；如果没有这行代码，矩阵可能漏掉某个 Phase 仍然通过。
        self.assertTrue(report["all_phase_contracts_passed"])  # 新增代码+Phase64ParityPlusMatrix: 断言所有阶段合同都通过；如果没有这行代码，单个阶段失败也可能被总矩阵掩盖。
        self.assertTrue(report["non_fake_acceptance"])  # 新增代码+Phase64ParityPlusMatrix: 断言非 fake 验收门禁仍然存在；如果没有这行代码，HTTP 或模拟路径可能被误当最终验收。
        self.assertTrue(report["visible_terminal_gate"])  # 新增代码+Phase64ParityPlusMatrix: 断言可见终端门禁仍然存在；如果没有这行代码，start_oauth_agent.bat 真实窗口验收可能被绕过。
        self.assertTrue(report["approval_bypass_blocked"])  # 新增代码+Phase64ParityPlusMatrix: 断言总矩阵没有审批绕过；如果没有这行代码，外部 controller 可能越过 Phase60 授权链。
        self.assertTrue(report["controlled_actions_expansion"])  # 新增代码+Phase64ParityPlusMatrix: 断言 Phase58 的真实动作扩展被安全门禁包住；如果没有这行代码，总矩阵可能错误否定真实 SendInput 能力。
        self.assertFalse(report["uncontrolled_actions_expanded"])  # 新增代码+Phase64ParityPlusMatrix: 断言没有无保护动作面扩张；如果没有这行代码，最终矩阵无法区分受控能力和危险扩张。
        for phase_id in ["53", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63"]:  # 新增代码+Phase64ParityPlusMatrix: 遍历所有必须覆盖的阶段；如果没有这行代码，阶段断言会重复且容易漏项。
            self.assertTrue(report["phase_results"][phase_id]["passed"])  # 新增代码+Phase64ParityPlusMatrix: 断言每个阶段报告 passed=true；如果没有这行代码，某个阶段失败不会被精准定位。
            self.assertIn(report["phase_results"][phase_id]["marker"], report["phase_cli_lines"][phase_id])  # 新增代码+Phase64ParityPlusMatrix: 断言每个阶段 CLI 行包含自己的 marker；如果没有这行代码，最终矩阵可能收集到错误输出。
    # 新增代码+Phase64ParityPlusMatrix: 函数段结束，test_phase64_contract_rolls_up_phase53_to_phase63_without_uncontrolled_actions 到此结束；如果没有这个边界说明，初学者不容易看出总矩阵合同测试范围。

    def test_phase64_cli_line_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase64ParityPlusMatrix: 函数段开始，验证 CLI 行和可见终端场景 token 稳定；如果没有这个测试，controller 可能漏检最终矩阵关键字段。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase64ParityPlusMatrix: 使用临时目录隔离合同状态；如果没有这行代码，测试会读写真实 memory。
            report = run_phase64_parity_plus_matrix_contract(base_dir=Path(temp_dir) / "phase64")  # 新增代码+Phase64ParityPlusMatrix: 运行 Phase64 合同自检；如果没有这行代码，CLI 行没有结构化来源。
        cli_line = phase64_cli_line(report)  # 新增代码+Phase64ParityPlusMatrix: 生成稳定 CLI token 行；如果没有这行代码，场景验收需要解析复杂 JSON。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase64_parity_plus_matrix.json")  # 新增代码+Phase64ParityPlusMatrix: 定位 Phase64 真实终端场景；如果没有这行代码，场景缺失不会被测试发现。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase64ParityPlusMatrix: 读取场景文本；如果没有这行代码，场景 token 漏配无法被发现。
        json.loads(scenario_text)  # 新增代码+Phase64ParityPlusMatrix: 校验场景是合法 JSON；如果没有这行代码，controller 运行时才会暴露格式错误。
        expected_tokens = {PHASE64_WINDOWS_PARITY_PLUS_MATRIX_MARKER, PHASE64_WINDOWS_PARITY_PLUS_MATRIX_OK_TOKEN, "phase_count=11", "phase53_parity_gap=true", "phase54_native_reality_gate=true", "phase55_native_helper_v2=true", "phase56_real_screenshot_pipeline=true", "phase57_real_uia_locator=true", "phase58_real_sendinput_guard=true", "phase59_session_context=true", "phase60_persistent_grants=true", "phase61_abort_streaming_hooks=true", "phase62_high_level_tools=true", "phase63_controller_takeover=true", "all_phase_contracts_passed=true", "non_fake_acceptance=true", "visible_terminal_gate=true", "approval_bypass_blocked=true", "controlled_actions_expansion=true", "uncontrolled_actions_expanded=false"}  # 新增代码+Phase64ParityPlusMatrix: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase64ParityPlusMatrix: 遍历每个关键 token；如果没有这行代码，重复断言容易遗漏。
            self.assertIn(token, cli_line)  # 新增代码+Phase64ParityPlusMatrix: 断言 CLI 输出包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase64ParityPlusMatrix: 断言真实终端场景也包含 token；如果没有这行代码，自动测试和真实验收可能不一致。
    # 新增代码+Phase64ParityPlusMatrix: 函数段结束，test_phase64_cli_line_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 token 测试范围。
# 新增代码+Phase64ParityPlusMatrix: 类段结束，WindowsComputerUseParityPlusMatrixPhase64Tests 到此结束；如果没有这个边界说明，初学者不容易看出 Phase64 测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase64ParityPlusMatrix: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase64ParityPlusMatrix: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
