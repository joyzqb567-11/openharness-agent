import json  # 新增代码+Phase75HumanlikeMatrix: 导入 JSON 用来校验真实终端场景文件格式；如果没有这行代码，场景 JSON 写坏要到验收时才暴露。
import tempfile  # 新增代码+Phase75HumanlikeMatrix: 导入临时目录隔离最终矩阵证据；如果没有这行代码，测试会污染真实 memory 目录。
import unittest  # 新增代码+Phase75HumanlikeMatrix: 导入 unittest 承载 Phase75 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase75HumanlikeMatrix: 导入 Path 管理 Windows 路径；如果没有这行代码，临时目录和场景文件路径容易拼错。

from learning_agent.computer_use.humanlike_operator_matrix import PHASE75_EXPECTED_PHASE_COUNT, PHASE75_HUMANLIKE_WINDOWS_OPERATOR_MARKER, PHASE75_HUMANLIKE_WINDOWS_OPERATOR_OK_TOKEN, phase75_cli_line, run_phase75_humanlike_operator_matrix_contract  # 新增代码+Phase75HumanlikeMatrix: 导入计划要求的 Phase75 最终矩阵入口；如果没有这行代码，红灯无法证明生产模块是否已经实现。


class WindowsComputerUseHumanlikeOperatorMatrixPhase75Tests(unittest.TestCase):  # 新增代码+Phase75HumanlikeMatrix: 类段开始，集中验证 Phase65-74 最终拟人 Windows Operator 矩阵；如果没有这个类，Phase75 没有自动化门禁。
    def test_phase75_contract_rolls_up_phase65_to_phase74(self) -> None:  # 新增代码+Phase75HumanlikeMatrix: 函数段开始，验证最终矩阵汇总十个前置阶段；如果没有这个测试，Phase75 可能漏阶段仍误报完成。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase75HumanlikeMatrix: 使用临时目录隔离合同证据；如果没有这行代码，测试会写入真实运行目录。
            report = run_phase75_humanlike_operator_matrix_contract(base_dir=Path(temp_dir))  # 新增代码+Phase75HumanlikeMatrix: 运行 Phase75 最终矩阵合同；如果没有这行代码，测试没有结构化报告来源。
        self.assertEqual(report["marker"], PHASE75_HUMANLIKE_WINDOWS_OPERATOR_MARKER)  # 新增代码+Phase75HumanlikeMatrix: 断言 ready marker 稳定；如果没有这行代码，真实终端验收无法稳定匹配 Phase75。
        self.assertEqual(report["ok_token"], PHASE75_HUMANLIKE_WINDOWS_OPERATOR_OK_TOKEN)  # 新增代码+Phase75HumanlikeMatrix: 断言 OK token 稳定；如果没有这行代码，用户无法一眼确认最终矩阵通过。
        self.assertEqual(report["phase_count"], PHASE75_EXPECTED_PHASE_COUNT)  # 新增代码+Phase75HumanlikeMatrix: 断言覆盖 Phase65-74 共十个阶段；如果没有这行代码，漏跑阶段也可能通过。
        self.assertTrue(report["all_phase_contracts_passed"])  # 新增代码+Phase75HumanlikeMatrix: 断言前置阶段合同全部通过；如果没有这行代码，单个阶段失败可能被总矩阵掩盖。
        self.assertTrue(report["prompt_to_any_normal_app"])  # 新增代码+Phase75HumanlikeMatrix: 断言支持从 prompt 到普通 Windows app 的通用路线；如果没有这行代码，最终矩阵可能退回固定应用。
        self.assertTrue(report["humanlike_observe_act_verify_loop"])  # 新增代码+Phase75HumanlikeMatrix: 断言观察-动作-验证闭环成立；如果没有这行代码，最终矩阵可能只有动作没有校验。
        self.assertTrue(report["generic_windows_app_control"])  # 新增代码+Phase75HumanlikeMatrix: 断言通用 Windows 应用控制能力成立；如果没有这行代码，最终矩阵可能缺点击/输入/窗口层。
        self.assertFalse(report["per_app_scripts_required"])  # 新增代码+Phase75HumanlikeMatrix: 断言不要求每个应用写专用脚本；如果没有这行代码，设计会偏离用户目标。
        self.assertTrue(report["uia_ocr_vision_fusion"])  # 新增代码+Phase75HumanlikeMatrix: 断言 UIA/OCR/vision 融合槽成立；如果没有这行代码，观察层可能缺多源融合。
        self.assertTrue(report["mouse_keyboard_window_control"])  # 新增代码+Phase75HumanlikeMatrix: 断言鼠标键盘窗口控制协议完整；如果没有这行代码，输入和窗口层可能漏验。
        self.assertTrue(report["failure_recovery"])  # 新增代码+Phase75HumanlikeMatrix: 断言失败恢复能力进入最终门禁；如果没有这行代码，闭环恢复可能被遗漏。
        self.assertTrue(report["representative_real_apps_passed"])  # 新增代码+Phase75HumanlikeMatrix: 断言代表性应用矩阵通过；如果没有这行代码，最终矩阵无法证明通用性样本。
        self.assertTrue(report["mspaint_pikachu_scenario"])  # 新增代码+Phase75HumanlikeMatrix: 断言 Paint 皮卡丘场景进入最终矩阵；如果没有这行代码，用户指定验收目标可能被漏掉。
        self.assertTrue(report["real_paint_app_control"])  # 新增代码+Phase75HumanlikeMatrix: 断言 Paint 场景指向真实 mspaint 控制合同；如果没有这行代码，图片作弊或伪场景可能混入。
        self.assertTrue(report["humanlike_drawing_actions"])  # 新增代码+Phase75HumanlikeMatrix: 断言画图使用拟人绘制动作证据；如果没有这行代码，画图可能不是鼠标轨迹式操作。
        self.assertFalse(report["direct_image_file_cheat"])  # 新增代码+Phase75HumanlikeMatrix: 断言最终矩阵禁止直接生成图片作弊；如果没有这行代码，Paint 验收可被伪造文件绕过。
        self.assertTrue(report["abort_safety"])  # 新增代码+Phase75HumanlikeMatrix: 断言急停安全进入最终门禁；如果没有这行代码，用户中断可能拦不住动作。
        self.assertTrue(report["high_risk_confirmation"])  # 新增代码+Phase75HumanlikeMatrix: 断言高风险确认进入最终门禁；如果没有这行代码，登录/支付/管理员窗口风险可能漏掉。
        self.assertTrue(report["visible_terminal_gate"])  # 新增代码+Phase75HumanlikeMatrix: 断言真实可见终端门禁存在；如果没有这行代码，CLI/HTTP 自测可能被误当完成。
        self.assertTrue(report["approval_bypass_blocked"])  # 新增代码+Phase75HumanlikeMatrix: 断言审批绕过被阻断；如果没有这行代码，外部 agent 可能伪造授权。
        self.assertFalse(report["uncontrolled_actions_expanded"])  # 新增代码+Phase75HumanlikeMatrix: 断言没有无保护动作面扩张；如果没有这行代码，最终矩阵无法区分受控能力和危险扩张。
    # 新增代码+Phase75HumanlikeMatrix: 函数段结束，test_phase75_contract_rolls_up_phase65_to_phase74 到此结束；如果没有这个边界说明，初学者不容易看出总矩阵合同范围。

    def test_phase75_phase_results_keep_each_source_contract_visible(self) -> None:  # 新增代码+Phase75HumanlikeMatrix: 函数段开始，验证最终矩阵保留每个阶段摘要和 CLI 行；如果没有这个测试，失败时难以定位哪个阶段掉链子。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase75HumanlikeMatrix: 使用临时目录隔离合同证据；如果没有这行代码，阶段报告会污染默认目录。
            report = run_phase75_humanlike_operator_matrix_contract(base_dir=Path(temp_dir))  # 新增代码+Phase75HumanlikeMatrix: 运行最终矩阵；如果没有这行代码，阶段摘要没有事实来源。
        expected_phase_ids = [str(phase_id) for phase_id in range(65, 75)]  # 新增代码+Phase75HumanlikeMatrix: 定义必须覆盖的 Phase65-74 阶段号；如果没有这行代码，阶段列表容易写散。
        self.assertEqual(sorted(report["phase_results"].keys()), expected_phase_ids)  # 新增代码+Phase75HumanlikeMatrix: 断言阶段摘要键完整；如果没有这行代码，漏阶段不会被精准发现。
        for phase_id in expected_phase_ids:  # 新增代码+Phase75HumanlikeMatrix: 遍历每个阶段；如果没有这行代码，断言会重复且容易漏项。
            self.assertTrue(report["phase_results"][phase_id]["passed"])  # 新增代码+Phase75HumanlikeMatrix: 断言每个阶段摘要通过；如果没有这行代码，总体通过可能掩盖单阶段失败。
            self.assertIn(report["phase_results"][phase_id]["marker"], report["phase_cli_lines"][phase_id])  # 新增代码+Phase75HumanlikeMatrix: 断言每个 CLI 行包含本阶段 marker；如果没有这行代码，矩阵可能收集错输出。
            self.assertFalse(report["phase_results"][phase_id]["uncontrolled_actions_expanded"])  # 新增代码+Phase75HumanlikeMatrix: 断言单阶段摘要没有无保护动作扩张；如果没有这行代码，危险扩张可能藏在子报告。
    # 新增代码+Phase75HumanlikeMatrix: 函数段结束，test_phase75_phase_results_keep_each_source_contract_visible 到此结束；如果没有这个边界说明，初学者不容易看出阶段摘要验收范围。

    def test_phase75_cli_line_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase75HumanlikeMatrix: 函数段开始，验证 CLI 行和真实终端场景 token 稳定；如果没有这个测试，controller 可能漏检最终关键字段。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase75HumanlikeMatrix: 使用临时目录隔离合同状态；如果没有这行代码，测试会写入真实 memory。
            report = run_phase75_humanlike_operator_matrix_contract(base_dir=Path(temp_dir))  # 新增代码+Phase75HumanlikeMatrix: 运行最终矩阵合同；如果没有这行代码，CLI 行没有结构化来源。
        cli_line = phase75_cli_line(report)  # 新增代码+Phase75HumanlikeMatrix: 生成稳定 CLI token 行；如果没有这行代码，场景验收需要解析复杂 JSON。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase75_humanlike_operator_matrix.json")  # 新增代码+Phase75HumanlikeMatrix: 定位 Phase75 真实终端场景文件；如果没有这行代码，场景缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase75HumanlikeMatrix: 读取场景文本；如果没有这行代码，场景 token 漏配无法被发现。
        json.loads(scenario_text)  # 新增代码+Phase75HumanlikeMatrix: 校验场景是合法 JSON；如果没有这行代码，controller 运行时才会暴露格式错误。
        expected_tokens = {PHASE75_HUMANLIKE_WINDOWS_OPERATOR_MARKER, PHASE75_HUMANLIKE_WINDOWS_OPERATOR_OK_TOKEN, "phase_count=10", "prompt_to_any_normal_app=true", "humanlike_observe_act_verify_loop=true", "generic_windows_app_control=true", "per_app_scripts_required=false", "uia_ocr_vision_fusion=true", "mouse_keyboard_window_control=true", "failure_recovery=true", "representative_real_apps_passed=true", "mspaint_pikachu_scenario=true", "real_paint_app_control=true", "humanlike_drawing_actions=true", "direct_image_file_cheat=false", "abort_safety=true", "high_risk_confirmation=true", "visible_terminal_gate=true", "approval_bypass_blocked=true", "uncontrolled_actions_expanded=false"}  # 新增代码+Phase75HumanlikeMatrix: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase75HumanlikeMatrix: 遍历每个关键 token；如果没有这行代码，重复断言容易遗漏。
            self.assertIn(token, cli_line)  # 新增代码+Phase75HumanlikeMatrix: 断言 CLI 输出包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase75HumanlikeMatrix: 断言真实终端场景也包含 token；如果没有这行代码，自动测试和真实验收可能不一致。
    # 新增代码+Phase75HumanlikeMatrix: 函数段结束，test_phase75_cli_line_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 场景验收范围。
# 新增代码+Phase75HumanlikeMatrix: 类段结束，WindowsComputerUseHumanlikeOperatorMatrixPhase75Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase75HumanlikeMatrix: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase75HumanlikeMatrix: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
