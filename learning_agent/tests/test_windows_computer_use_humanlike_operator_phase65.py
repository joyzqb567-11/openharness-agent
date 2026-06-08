import json  # 新增代码+Phase65HumanlikeOperator: 导入 JSON 用来校验真实终端验收场景文件；如果没有这行代码，场景格式错误只能等 controller 运行时才暴露。
import unittest  # 新增代码+Phase65HumanlikeOperator: 导入 unittest 承载 Phase65 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase65HumanlikeOperator: 导入 Path 处理 Windows 和项目相对路径；如果没有这行代码，场景文件路径容易拼错。

from learning_agent.computer_use.humanlike_operator_contract import PHASE65_HUMANLIKE_OPERATOR_MARKER, PHASE65_HUMANLIKE_OPERATOR_OK_TOKEN, phase65_cli_line, run_phase65_humanlike_operator_contract  # 新增代码+Phase65HumanlikeOperator: 导入 Phase65 通用拟人操作合同 API；如果没有这行代码，红灯测试无法证明生产模块尚未实现。


class WindowsComputerUseHumanlikeOperatorPhase65Tests(unittest.TestCase):  # 新增代码+Phase65HumanlikeOperator: 类段开始，集中验证 Phase65 通用拟人 Windows Operator 契约；如果没有这个类，Phase65 没有自动化门禁。
    def test_phase65_contract_locks_humanlike_operator_boundaries(self) -> None:  # 新增代码+Phase65HumanlikeOperator: 函数段开始，验证 Phase65 只建立通用操作边界不偷跑扩展动作；如果没有这个测试，后续阶段可能绕过安全边界。
        report = run_phase65_humanlike_operator_contract()  # 新增代码+Phase65HumanlikeOperator: 运行 Phase65 合同生成结构化报告；如果没有这行代码，测试没有真实报告来源。
        self.assertEqual(report["marker"], PHASE65_HUMANLIKE_OPERATOR_MARKER)  # 新增代码+Phase65HumanlikeOperator: 断言 marker 稳定；如果没有这行代码，真实终端验收可能匹配不到 Phase65 输出。
        self.assertEqual(report["ok_token"], PHASE65_HUMANLIKE_OPERATOR_OK_TOKEN)  # 新增代码+Phase65HumanlikeOperator: 断言 OK token 稳定；如果没有这行代码，用户无法一眼判断本阶段是否通过。
        self.assertTrue(report["humanlike_operator_contract"])  # 新增代码+Phase65HumanlikeOperator: 断言通用拟人 Operator 契约已启用；如果没有这行代码，本阶段可能只输出 token 但没有表达真实能力边界。
        self.assertTrue(report["prompt_to_normal_windows_app"])  # 新增代码+Phase65HumanlikeOperator: 断言目标是从 prompt 操控普通 Windows 应用；如果没有这行代码，项目目标可能退回到单应用脚本。
        self.assertFalse(report["per_app_scripts_required"])  # 新增代码+Phase65HumanlikeOperator: 断言不要求每个应用写专用脚本；如果没有这行代码，设计会偏离“通用操控所有本机应用”的目标。
        self.assertTrue(report["high_risk_confirmation_required"])  # 新增代码+Phase65HumanlikeOperator: 断言高风险界面必须确认；如果没有这行代码，拟人控制可能误触支付、登录或安全窗口。
        self.assertTrue(report["direct_file_cheat_blocked"])  # 新增代码+Phase65HumanlikeOperator: 断言禁止用直接写文件伪装真实操作；如果没有这行代码，画图等 E2E 可能被文件生成作弊替代。
        self.assertFalse(report["actions_expanded"])  # 新增代码+Phase65HumanlikeOperator: 断言 Phase65 暂不扩展真实动作面；如果没有这行代码，本阶段可能提前打开没有配套验收的输入能力。
    # 新增代码+Phase65HumanlikeOperator: 函数段结束，test_phase65_contract_locks_humanlike_operator_boundaries 到此结束；如果没有这个边界说明，初学者不容易看出合同边界测试范围。

    def test_phase65_cli_line_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase65HumanlikeOperator: 函数段开始，验证 CLI 行和真实终端场景 token 保持一致；如果没有这个测试，controller 场景可能和模块输出脱节。
        report = run_phase65_humanlike_operator_contract()  # 新增代码+Phase65HumanlikeOperator: 运行合同报告作为 CLI 输出来源；如果没有这行代码，测试只能硬编码猜测输出。
        cli_line = phase65_cli_line(report)  # 新增代码+Phase65HumanlikeOperator: 生成稳定的一行验收 token；如果没有这行代码，真实终端最终回答需要解析复杂 JSON。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase65_humanlike_operator_contract.json")  # 新增代码+Phase65HumanlikeOperator: 定位 Phase65 真实终端验收场景；如果没有这行代码，场景缺失不会被自动发现。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase65HumanlikeOperator: 读取场景文本进行一致性检查；如果没有这行代码，场景 token 漏配无法被发现。
        json.loads(scenario_text)  # 新增代码+Phase65HumanlikeOperator: 校验场景是合法 JSON；如果没有这行代码，JSON 语法错误会拖到真实验收时才失败。
        expected_tokens = {PHASE65_HUMANLIKE_OPERATOR_MARKER, PHASE65_HUMANLIKE_OPERATOR_OK_TOKEN, "humanlike_operator_contract=true", "prompt_to_normal_windows_app=true", "per_app_scripts_required=false", "high_risk_confirmation_required=true", "direct_file_cheat_blocked=true", "actions_expanded=false"}  # 新增代码+Phase65HumanlikeOperator: 定义 CLI 和场景必须同时包含的关键 token；如果没有这行代码，验收标准容易在后续修改中漂移。
        for token in expected_tokens:  # 新增代码+Phase65HumanlikeOperator: 遍历每个关键 token；如果没有这行代码，重复断言容易漏掉字段。
            self.assertIn(token, cli_line)  # 新增代码+Phase65HumanlikeOperator: 断言 CLI 输出包含 token；如果没有这行代码，模块输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase65HumanlikeOperator: 断言真实终端场景也包含 token；如果没有这行代码，自动测试和可见终端验收可能不一致。
    # 新增代码+Phase65HumanlikeOperator: 函数段结束，test_phase65_cli_line_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 token 稳定性测试范围。
# 新增代码+Phase65HumanlikeOperator: 类段结束，WindowsComputerUseHumanlikeOperatorPhase65Tests 到此结束；如果没有这个边界说明，初学者不容易看出 Phase65 测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase65HumanlikeOperator: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase65HumanlikeOperator: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
