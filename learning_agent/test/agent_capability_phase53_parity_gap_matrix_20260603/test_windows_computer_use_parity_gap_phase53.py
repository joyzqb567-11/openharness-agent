import json  # 新增代码+Phase53ParityGapMatrix: 导入 JSON 工具读取验收场景；如果没有这行代码，测试无法确认真实终端场景 token 是否和代码一致。
import tempfile  # 新增代码+Phase53ParityGapMatrix: 导入临时目录隔离 /computer parity 状态；如果没有这行代码，测试可能污染真实项目锁目录。
import unittest  # 新增代码+Phase53ParityGapMatrix: 导入 unittest 框架；如果没有这行代码，自动化命令无法发现 Phase53 测试。
from pathlib import Path  # 新增代码+Phase53ParityGapMatrix: 导入 Path 处理场景路径和临时工作区；如果没有这行代码，路径拼接会更脆弱。

from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase53ParityGapMatrix: 导入真实终端 /computer 命令入口；如果没有这行代码，测试无法证明用户可见命令已接入。
from learning_agent.computer_use.parity_gap_matrix import PHASE53_PARITY_GAP_MATRIX_MARKER, PHASE53_PARITY_GAP_MATRIX_OK_TOKEN, phase53_cli_line, run_phase53_parity_gap_matrix_contract  # 新增代码+Phase53ParityGapMatrix: 导入预期新增的差距矩阵合同；如果没有这行代码，红灯会证明 Phase53 尚未实现。


class WindowsComputerUseParityGapPhase53Tests(unittest.TestCase):  # 新增代码+Phase53ParityGapMatrix: 类段开始，组织 Phase53 差距矩阵测试；如果没有这个类，unittest 不会执行本阶段门禁。
    def test_phase53_contract_locks_claudecode_gap_items_and_boundaries(self) -> None:  # 新增代码+Phase53ParityGapMatrix: 函数段开始，验证 ClaudeCode 差距项和安全边界被固化；如果没有这个测试，后续阶段可能跑偏或假装完成。
        report = run_phase53_parity_gap_matrix_contract()  # 新增代码+Phase53ParityGapMatrix: 运行 Phase53 只读合同；如果没有这行代码，测试没有真实报告来源。
        self.assertEqual(report["gap_count"], 12)  # 新增代码+Phase53ParityGapMatrix: 断言 Phase53-64 共十二个阶段都在矩阵里；如果没有这行代码，遗漏阶段也可能误通过。
        self.assertTrue(report["owner_phases_complete"])  # 新增代码+Phase53ParityGapMatrix: 断言每个差距项都有责任阶段；如果没有这行代码，后续实现无法追踪归属。
        self.assertTrue(report["real_provider_required"])  # 新增代码+Phase53ParityGapMatrix: 断言矩阵明确区分真实 provider 要求；如果没有这行代码，fake 自测可能被误认为生产能力。
        self.assertTrue(report["non_fake_acceptance_contract"])  # 新增代码+Phase53ParityGapMatrix: 断言非伪验收边界存在；如果没有这行代码，真实终端验收要求可能被稀释。
        self.assertTrue(report["claudecode_source_reviewed"])  # 新增代码+Phase53ParityGapMatrix: 断言矩阵基于 ClaudeCode 源码审阅；如果没有这行代码，差距可能退化成主观猜测。
        self.assertFalse(report["actions_expanded"])  # 新增代码+Phase53ParityGapMatrix: 断言 Phase53 不扩大真实桌面动作面；如果没有这行代码，只读计划阶段可能误开放动作。
        self.assertTrue(report["passed"])  # 新增代码+Phase53ParityGapMatrix: 断言合同整体通过；如果没有这行代码，部分字段通过也会被误当成完成。
        for item in report["items"]:  # 新增代码+Phase53ParityGapMatrix: 遍历每个差距项做字段级门禁；如果没有这行代码，只检查摘要会漏掉坏项。
            self.assertIn("id", item)  # 新增代码+Phase53ParityGapMatrix: 断言差距项有稳定 id；如果没有这行代码，验收和后续阶段无法引用具体任务。
            self.assertIn("claudecode_source", item)  # 新增代码+Phase53ParityGapMatrix: 断言差距项记录源码证据；如果没有这行代码，比较结果容易变成无来源结论。
            self.assertIn("owner_phase", item)  # 新增代码+Phase53ParityGapMatrix: 断言差距项记录责任 phase；如果没有这行代码，阶段边界会模糊。
            self.assertIn("acceptance_type", item)  # 新增代码+Phase53ParityGapMatrix: 断言差距项记录验收类型；如果没有这行代码，无法知道该用真实终端还是自动化验证。
            self.assertIn(item["owner_phase"], list(range(53, 65)))  # 新增代码+Phase53ParityGapMatrix: 断言责任 phase 落在 Phase53-64；如果没有这行代码，旧 phase 或错号 phase 会混进蓝图。
            if item.get("real_provider_required"):  # 新增代码+Phase53ParityGapMatrix: 只对真实 provider 项检查 fake 边界；如果没有这行代码，所有项都会用同一规则导致误判。
                self.assertNotEqual(item["acceptance_type"], "fake_only")  # 新增代码+Phase53ParityGapMatrix: 禁止真实 provider 项只靠 fake 验收；如果没有这行代码，最关键的 20% 差距可能被伪通过。
    # 新增代码+Phase53ParityGapMatrix: 函数段结束，test_phase53_contract_locks_claudecode_gap_items_and_boundaries 到此结束；如果没有这个边界说明，初学者不容易看出合同测试范围。

    def test_phase53_cli_terminal_and_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase53ParityGapMatrix: 函数段开始，验证 CLI、/computer parity 和真实终端场景 token；如果没有这个测试，用户可见验收入口可能缺失。
        report = run_phase53_parity_gap_matrix_contract()  # 新增代码+Phase53ParityGapMatrix: 运行 Phase53 合同生成报告；如果没有这行代码，CLI token 没有真实依据。
        line = phase53_cli_line(report)  # 新增代码+Phase53ParityGapMatrix: 生成稳定单行 token；如果没有这行代码，场景断言需要解析复杂 JSON。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase53_parity_gap_matrix.json")  # 新增代码+Phase53ParityGapMatrix: 定位 Phase53 真实终端场景；如果没有这行代码，测试无法确认场景已创建。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase53ParityGapMatrix: 读取场景 JSON；如果没有这行代码，场景漏 token 不会被发现。
        expected_tokens = {PHASE53_PARITY_GAP_MATRIX_MARKER, PHASE53_PARITY_GAP_MATRIX_OK_TOKEN, "gap_count=12", "owner_phases_complete=true", "real_provider_required=true", "non_fake_acceptance=true", "claudecode_source_reviewed=true", "actions_expanded=false"}  # 新增代码+Phase53ParityGapMatrix: 列出必须稳定出现的 token；如果没有这行代码，验收标准会散落在多个断言里。
        for token in expected_tokens:  # 新增代码+Phase53ParityGapMatrix: 遍历每个固定 token；如果没有这行代码，只能重复写多行断言。
            self.assertIn(token, line)  # 新增代码+Phase53ParityGapMatrix: 断言 CLI 行包含 token；如果没有这行代码，命令行输出漂移不会被发现。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase53ParityGapMatrix: 断言 debug log 检查包含 token；如果没有这行代码，真实终端验收可能漏查命令输出。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase53ParityGapMatrix: 断言最终回答检查包含 token；如果没有这行代码，用户可见答案可能缺少验收锚点。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase53ParityGapMatrix: 创建临时工作区运行 /computer parity；如果没有这行代码，测试可能写入真实项目状态目录。
            output = run_computer_terminal_command(Path(temp_dir), "/computer parity")  # 新增代码+Phase53ParityGapMatrix: 调用真实终端命令处理函数；如果没有这行代码，无法证明 /computer parity 已对用户可见。
        self.assertIn("Computer Parity Matrix", output)  # 新增代码+Phase53ParityGapMatrix: 断言终端输出有差距矩阵标题；如果没有这行代码，命令可能只是返回普通状态。
        self.assertIn(PHASE53_PARITY_GAP_MATRIX_MARKER, output)  # 新增代码+Phase53ParityGapMatrix: 断言终端输出包含 marker；如果没有这行代码，controller 难以稳定匹配。
        self.assertIn(PHASE53_PARITY_GAP_MATRIX_OK_TOKEN, output)  # 新增代码+Phase53ParityGapMatrix: 断言终端输出包含 OK token；如果没有这行代码，用户看不到合同是否通过。
    # 新增代码+Phase53ParityGapMatrix: 函数段结束，test_phase53_cli_terminal_and_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI/场景测试范围。


if __name__ == "__main__":  # 新增代码+Phase53ParityGapMatrix: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式单独验证 Phase53。
    unittest.main()  # 新增代码+Phase53ParityGapMatrix: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行断言。
