import json  # 新增代码+Phase7Acceptance: 引入 JSON 解析；若没有这行代码，测试无法读取验收矩阵和场景。
import unittest  # 新增代码+Phase7Acceptance: 引入 unittest 测试框架；若没有这行代码，本文件无法定义测试用例。
from pathlib import Path  # 新增代码+Phase7Acceptance: 使用 Path 定位项目文件；若没有这行代码，路径拼接会更脆弱。


PROJECT_ROOT = Path(__file__).resolve().parents[2]  # 新增代码+Phase7Acceptance: 定位 OpenHarness 项目根；若没有这行代码，测试在不同 cwd 下可能读错文件。
SCENARIO_DIR = PROJECT_ROOT / "learning_agent" / "acceptance_controller" / "scenarios"  # 新增代码+Phase7Acceptance: 定位验收场景目录；若没有这行代码，矩阵和场景路径会散落。


class AgentCapabilityAcceptanceMatrixStage19Tests(unittest.TestCase):  # 新增代码+Phase7Acceptance: 定义 Phase 7 验收矩阵测试集合；若没有这段代码，真实端到端门禁没有自动化保护。
    def test_matrix_covers_all_phases_and_visible_terminal_scenario(self) -> None:  # 新增代码+Phase7Acceptance: 验证矩阵覆盖 Phase 1-7；若没有这段测试，后续可能漏掉某个阶段验收。
        matrix_path = SCENARIO_DIR / "agent_capability_completion_phase7_matrix.json"  # 新增代码+Phase7Acceptance: 定位验收矩阵文件；若没有这行代码，测试不知道读取哪份矩阵。
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))  # 新增代码+Phase7Acceptance: 读取并解析矩阵 JSON；若没有这行代码，格式错误不会被发现。
        phases = [item["phase"] for item in matrix["phases"]]  # 新增代码+Phase7Acceptance: 收集矩阵声明的阶段号；若没有这行代码，无法判断阶段覆盖。
        self.assertEqual(phases, [1, 2, 3, 4, 5, 6, 7])  # 新增代码+Phase7Acceptance: 断言 Phase 1-7 全覆盖且顺序稳定；若没有这行代码，漏阶段不会失败。
        self.assertTrue(matrix["visible_terminal_required"])  # 新增代码+Phase7Acceptance: 断言真实可见终端仍是强制门禁；若没有这行代码，矩阵可能退化成纯单测。
        self.assertIn("agent_capability_completion_phase7_chrome_status.json", matrix["visible_terminal_scenarios"])  # 新增代码+Phase7Acceptance: 断言 /chrome 场景进入矩阵；若没有这行代码，新增终端 UI 可能没有真实验收。

    def test_chrome_status_scenario_is_event_only_and_permissionless(self) -> None:  # 新增代码+Phase7Acceptance: 验证 /chrome 场景适合事件型终端命令；若没有这段测试，controller 可能继续等待不存在的最终回答。
        scenario_path = SCENARIO_DIR / "agent_capability_completion_phase7_chrome_status.json"  # 新增代码+Phase7Acceptance: 定位 /chrome 场景文件；若没有这行代码，测试无法读取场景。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase7Acceptance: 读取并解析场景 JSON；若没有这行代码，格式错误不会被发现。
        self.assertEqual(scenario["prompt_lines"], ["/chrome"])  # 新增代码+Phase7Acceptance: 断言真实终端输入就是 /chrome；若没有这行代码，场景可能没有实际测试命令。
        self.assertIn("chrome_status_printed", scenario["required_event_states"])  # 新增代码+Phase7Acceptance: 断言场景等待 /chrome 验收事件；若没有这行代码，命令输出可能没有被证明。
        self.assertNotIn("final_answer_printed", scenario["required_event_states"])  # 新增代码+Phase7Acceptance: 断言事件型命令不要求模型最终回答；若没有这行代码，场景会无意义等待模型。
        self.assertEqual(scenario["max_permission_sent_count"], 0)  # 新增代码+Phase7Acceptance: 断言 /chrome 状态命令不需要权限输入；若没有这行代码，状态 UI 可能触发高风险授权。

    def test_controller_supports_event_only_completion(self) -> None:  # 新增代码+Phase7Acceptance: 验证 acceptance controller 支持没有 final_answer 的终端命令；若没有这段测试，/chrome 场景会等到超时。
        controller_path = PROJECT_ROOT / "learning_agent" / "acceptance_controller" / "controller.ps1"  # 新增代码+Phase7Acceptance: 定位 PowerShell 控制器；若没有这行代码，测试无法检查真实脚本。
        controller_text = controller_path.read_text(encoding="utf-8")  # 新增代码+Phase7Acceptance: 读取控制器脚本文本；若没有这行代码，无法验证事件型完成逻辑。
        self.assertIn("AllowsEventOnlyCompletion", controller_text)  # 新增代码+Phase7Acceptance: 断言脚本包含事件型完成开关；若没有这行代码，/chrome 场景可能必须等最终回答。
        self.assertIn("chrome_status_printed", controller_text)  # 新增代码+Phase7Acceptance: 断言脚本显式支持 /chrome 验收事件；若没有这行代码，未来重构可能删掉关键路径。


if __name__ == "__main__":  # 新增代码+Phase7Acceptance: 允许直接运行本测试文件；若没有这行代码，初学者无法用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase7Acceptance: 启动 unittest 主函数；若没有这行代码，直接运行文件不会执行测试。
