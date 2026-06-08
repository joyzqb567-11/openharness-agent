import json  # 新增代码+Phase74RepresentativeE2E: 导入 JSON 用来读取画图交互证据文件；如果没有这行代码，测试无法确认画图不是直接生成图片作弊。
import tempfile  # 新增代码+Phase74RepresentativeE2E: 导入临时目录隔离 E2E 矩阵输出；如果没有这行代码，测试可能污染真实用户文件。
import unittest  # 新增代码+Phase74RepresentativeE2E: 导入 unittest 承载 Phase74 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase74RepresentativeE2E: 导入 Path 管理 Windows 路径；如果没有这行代码，证据目录和场景文件路径容易拼错。

from learning_agent.computer_use.representative_e2e_matrix import PHASE74_ACTIONS_EXPANDED, PHASE74_REPRESENTATIVE_E2E_MARKER, PHASE74_REPRESENTATIVE_E2E_OK_TOKEN, WindowsRepresentativeE2EMatrix, phase74_cli_line, run_phase74_representative_e2e_contract  # 新增代码+Phase74RepresentativeE2E: 导入计划要求的 Phase74 公开入口；如果没有这行代码，红灯无法证明生产模块是否已经实现。


class WindowsComputerUseRepresentativeE2EPhase74Tests(unittest.TestCase):  # 新增代码+Phase74RepresentativeE2E: 类段开始，集中验收代表性真实应用 E2E 矩阵；如果没有这个类，Phase74 没有自动化质量门禁。
    def test_representative_contract_reports_all_required_scenarios(self) -> None:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，验证五类代表性应用场景都进入合同报告；如果没有这个测试，矩阵可能只覆盖单个样例。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase74RepresentativeE2E: 使用临时目录隔离合同证据；如果没有这行代码，测试会写入真实 memory 目录。
            report = run_phase74_representative_e2e_contract(base_dir=Path(temp_dir), real_smoke=False)  # 新增代码+Phase74RepresentativeE2E: 运行安全合约模式；如果没有这行代码，测试没有结构化报告来源。
        self.assertTrue(report["notepad_scenario"])  # 新增代码+Phase74RepresentativeE2E: 断言记事本场景通过；如果没有这行代码，文本编辑类应用可能缺失。
        self.assertTrue(report["explorer_scenario"])  # 新增代码+Phase74RepresentativeE2E: 断言资源管理器场景通过；如果没有这行代码，文件浏览类应用可能缺失。
        self.assertTrue(report["browser_scenario"])  # 新增代码+Phase74RepresentativeE2E: 断言浏览器场景通过；如果没有这行代码，网页类应用可能缺失。
        self.assertTrue(report["window_style_scenario"])  # 新增代码+Phase74RepresentativeE2E: 断言窗口风格场景通过；如果没有这行代码，对话框/窗口类交互可能缺失。
        self.assertTrue(report["mspaint_pikachu_scenario"])  # 新增代码+Phase74RepresentativeE2E: 断言画图皮卡丘场景通过；如果没有这行代码，代表性绘图验收可能被遗漏。
        self.assertTrue(report["real_paint_app_control"])  # 新增代码+Phase74RepresentativeE2E: 断言画图场景使用真实 mspaint 目标合同；如果没有这行代码，画图可能退化成纯图片生成。
        self.assertTrue(report["humanlike_drawing_actions"])  # 新增代码+Phase74RepresentativeE2E: 断言存在拟人鼠标绘制动作；如果没有这行代码，画图可能不是用户可执行的动作序列。
        self.assertFalse(report["direct_image_file_cheat"])  # 新增代码+Phase74RepresentativeE2E: 断言没有直接写图片文件作弊；如果没有这行代码，验收可能被伪造图片绕过。
        self.assertTrue(report["paint_canvas_not_blank"])  # 新增代码+Phase74RepresentativeE2E: 断言画布非空证据成立；如果没有这行代码，空画布也可能误报通过。
        self.assertTrue(report["pikachu_visual_elements"])  # 新增代码+Phase74RepresentativeE2E: 断言皮卡丘关键视觉元素齐全；如果没有这行代码，随便画几笔也可能通过。
        self.assertTrue(report["representative_real_apps_passed"])  # 新增代码+Phase74RepresentativeE2E: 断言代表性应用矩阵总体通过；如果没有这行代码，单项结果不会汇总成最终门禁。
        self.assertFalse(report["actions_expanded"])  # 新增代码+Phase74RepresentativeE2E: 断言 Phase74 合约模式不扩大真实动作面；如果没有这行代码，安全模式边界可能漂移。
        self.assertFalse(PHASE74_ACTIONS_EXPANDED)  # 新增代码+Phase74RepresentativeE2E: 断言模块常量也不扩大动作面；如果没有这行代码，报告和模块声明可能不一致。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，test_representative_contract_reports_all_required_scenarios 到此结束；如果没有这个边界说明，初学者不容易看出总报告验收范围。

    def test_paint_pikachu_plan_uses_humanlike_actions_not_direct_image_cheat(self) -> None:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，验证画图皮卡丘靠鼠标轨迹而不是生成图片；如果没有这个测试，核心用户场景可能被偷换。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase74RepresentativeE2E: 使用临时目录保存画图证据；如果没有这行代码，测试证据可能污染项目默认目录。
            matrix = WindowsRepresentativeE2EMatrix(base_dir=Path(temp_dir))  # 新增代码+Phase74RepresentativeE2E: 创建代表性 E2E 矩阵；如果没有这行代码，无法单独检查画图场景细节。
            paint = matrix.build_paint_pikachu_scenario(real_smoke=False)  # 新增代码+Phase74RepresentativeE2E: 构建安全画图皮卡丘场景；如果没有这行代码，测试无法核对动作序列。
            artifact_path = Path(paint["artifact_path"])  # 新增代码+Phase74RepresentativeE2E: 读取交互证据路径；如果没有这行代码，无法检查证据是否真实落盘。
            evidence = json.loads(artifact_path.read_text(encoding="utf-8"))  # 新增代码+Phase74RepresentativeE2E: 解析画图证据 JSON；如果没有这行代码，测试只能相信内存报告。
            artifact_exists = artifact_path.exists()  # 修改代码+Phase74RepresentativeE2E: 在临时目录清理前记录证据文件存在性；如果没有这行代码，目录退出后再检查会误判失败。
        self.assertEqual(paint["process_name"], "mspaint.exe")  # 新增代码+Phase74RepresentativeE2E: 断言目标进程是 Windows 画图；如果没有这行代码，场景可能不是本机画图软件。
        self.assertTrue(paint["canvas_observed"])  # 新增代码+Phase74RepresentativeE2E: 断言先观察画布；如果没有这行代码，动作可能在未知窗口盲打。
        self.assertGreaterEqual(paint["draw_action_count"], 12)  # 新增代码+Phase74RepresentativeE2E: 断言至少十二个绘图动作；如果没有这行代码，皮卡丘元素可能不完整。
        self.assertTrue(paint["continuous_mouse_path"])  # 新增代码+Phase74RepresentativeE2E: 断言每个笔画是连续鼠标路径；如果没有这行代码，拟人绘制证据不足。
        self.assertTrue(paint["saved_visual_artifact"])  # 新增代码+Phase74RepresentativeE2E: 断言通过应用工作流保存证据；如果没有这行代码，画图结果可能不可审计。
        self.assertTrue(paint["paint_canvas_not_blank"])  # 新增代码+Phase74RepresentativeE2E: 断言画布有内容；如果没有这行代码，空白画布可能误通过。
        self.assertTrue(paint["pikachu_visual_elements"])  # 新增代码+Phase74RepresentativeE2E: 断言包含皮卡丘关键元素；如果没有这行代码，非皮卡丘涂鸦也可能通过。
        self.assertFalse(paint["direct_image_file_cheat"])  # 新增代码+Phase74RepresentativeE2E: 断言未直接生成图片；如果没有这行代码，真实应用控制目标会被绕开。
        self.assertFalse(paint["real_visible_app_invoked"])  # 新增代码+Phase74RepresentativeE2E: 断言安全合约模式没有打开真实窗口；如果没有这行代码，单元测试可能干扰用户桌面。
        self.assertEqual(paint["artifact_kind"], "interaction_evidence_json")  # 新增代码+Phase74RepresentativeE2E: 断言证据是交互 JSON 不是位图；如果没有这行代码，直接图片文件作弊不易发现。
        self.assertTrue(artifact_exists)  # 修改代码+Phase74RepresentativeE2E: 断言证据文件曾在安全临时目录中真实存在；如果没有这行代码，报告可能指向不存在路径。
        self.assertTrue(str(artifact_path).lower().endswith("paint_pikachu_interaction_evidence.json"))  # 新增代码+Phase74RepresentativeE2E: 断言证据文件名稳定；如果没有这行代码，备份和审计难以定位。
        self.assertEqual(evidence["target_process"], "mspaint.exe")  # 新增代码+Phase74RepresentativeE2E: 断言落盘证据同样指向画图；如果没有这行代码，内存报告和文件可能不一致。
        self.assertFalse(evidence["direct_image_file_cheat"])  # 新增代码+Phase74RepresentativeE2E: 断言落盘证据也没有图片作弊；如果没有这行代码，审计文件可能藏着错误。
        self.assertGreaterEqual(len(evidence["draw_actions"]), 12)  # 新增代码+Phase74RepresentativeE2E: 断言落盘笔画数量充足；如果没有这行代码，证据文件可能不完整。
        self.assertIn("yellow", {action["color"] for action in evidence["draw_actions"]})  # 新增代码+Phase74RepresentativeE2E: 断言有黄色身体笔画；如果没有这行代码，皮卡丘主体颜色可能缺失。
        self.assertIn("black", {action["color"] for action in evidence["draw_actions"]})  # 新增代码+Phase74RepresentativeE2E: 断言有黑色眼睛/耳尖笔画；如果没有这行代码，皮卡丘特征可能缺失。
        self.assertIn("red", {action["color"] for action in evidence["draw_actions"]})  # 新增代码+Phase74RepresentativeE2E: 断言有红色脸颊笔画；如果没有这行代码，皮卡丘脸颊可能缺失。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，test_paint_pikachu_plan_uses_humanlike_actions_not_direct_image_cheat 到此结束；如果没有这个边界说明，初学者不容易看出画图验收范围。

    def test_matrix_uses_controlled_artifact_dirs_and_no_private_data(self) -> None:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，验证矩阵只写受控目录且不读隐私数据；如果没有这个测试，真实应用场景可能越界。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase74RepresentativeE2E: 创建临时根目录；如果没有这行代码，目录边界测试没有根路径。
            root = Path(temp_dir).resolve()  # 新增代码+Phase74RepresentativeE2E: 解析根目录绝对路径；如果没有这行代码，is_relative_to 比较可能受相对路径影响。
            matrix = WindowsRepresentativeE2EMatrix(base_dir=root)  # 新增代码+Phase74RepresentativeE2E: 创建受控根目录矩阵；如果没有这行代码，场景输出路径不可控。
            report = matrix.run(real_smoke=False)  # 新增代码+Phase74RepresentativeE2E: 运行安全矩阵；如果没有这行代码，无法收集全部场景。
        for scenario in report["scenarios"].values():  # 新增代码+Phase74RepresentativeE2E: 遍历每个场景；如果没有这行代码，只会检查部分场景。
            artifact_path = Path(scenario["artifact_path"]).resolve()  # 新增代码+Phase74RepresentativeE2E: 解析场景证据路径；如果没有这行代码，路径穿越风险难以发现。
            self.assertTrue(artifact_path.is_relative_to(root))  # 新增代码+Phase74RepresentativeE2E: 断言证据路径在受控目录下；如果没有这行代码，场景可能写到用户真实文件夹。
            self.assertFalse(scenario.get("reads_private_profile", False))  # 新增代码+Phase74RepresentativeE2E: 断言不读私有浏览器资料；如果没有这行代码，cookies/token 风险可能漏过。
            self.assertFalse(scenario.get("cookies_read", False))  # 新增代码+Phase74RepresentativeE2E: 断言不读 cookies；如果没有这行代码，浏览器隐私边界可能被破坏。
            self.assertFalse(scenario.get("tokens_read", False))  # 新增代码+Phase74RepresentativeE2E: 断言不读 token；如果没有这行代码，账号凭据风险可能漏过。
            self.assertFalse(scenario.get("changes_registry", False))  # 新增代码+Phase74RepresentativeE2E: 断言不改注册表；如果没有这行代码，E2E 可能产生系统副作用。
            self.assertFalse(scenario.get("changes_system_settings", False))  # 新增代码+Phase74RepresentativeE2E: 断言不改系统设置；如果没有这行代码，窗口风格测试可能影响用户电脑。
            self.assertFalse(scenario.get("requires_admin", False))  # 新增代码+Phase74RepresentativeE2E: 断言不需要管理员权限；如果没有这行代码，场景可能越权。
            self.assertFalse(scenario.get("terminal_command_used", False))  # 新增代码+Phase74RepresentativeE2E: 断言不靠终端命令伪造应用操作；如果没有这行代码，真实应用控制可能被命令行替代。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，test_matrix_uses_controlled_artifact_dirs_and_no_private_data 到此结束；如果没有这个边界说明，初学者不容易看出目录和隐私边界验收范围。

    def test_phase74_cli_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，验证 CLI 和真实终端场景 token 稳定；如果没有这个测试，验收脚本可能漏检关键能力。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase74RepresentativeE2E: 使用临时目录运行合同；如果没有这行代码，CLI 报告会污染默认目录。
            report = run_phase74_representative_e2e_contract(base_dir=Path(temp_dir), real_smoke=False)  # 新增代码+Phase74RepresentativeE2E: 运行 Phase74 合同报告；如果没有这行代码，CLI 行没有事实来源。
        cli_line = phase74_cli_line(report)  # 新增代码+Phase74RepresentativeE2E: 生成稳定 CLI token 行；如果没有这行代码，测试无法和场景要求对齐。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase74_representative_e2e.json")  # 新增代码+Phase74RepresentativeE2E: 定位真实终端验收场景文件；如果没有这行代码，场景缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase74RepresentativeE2E: 读取场景文本；如果没有这行代码，debug/event token 漏配无法检测。
        expected_tokens = {PHASE74_REPRESENTATIVE_E2E_MARKER, PHASE74_REPRESENTATIVE_E2E_OK_TOKEN, "notepad_scenario=true", "explorer_scenario=true", "browser_scenario=true", "window_style_scenario=true", "mspaint_pikachu_scenario=true", "real_paint_app_control=true", "humanlike_drawing_actions=true", "direct_image_file_cheat=false", "paint_canvas_not_blank=true", "pikachu_visual_elements=true", "representative_real_apps_passed=true"}  # 新增代码+Phase74RepresentativeE2E: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase74RepresentativeE2E: 遍历关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase74RepresentativeE2E: 断言 CLI 行包含 token；如果没有这行代码，命令行输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase74RepresentativeE2E: 断言真实终端场景包含 token；如果没有这行代码，controller 可能漏验。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，test_phase74_cli_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 场景验收范围。
# 新增代码+Phase74RepresentativeE2E: 类段结束，WindowsComputerUseRepresentativeE2EPhase74Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase74RepresentativeE2E: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase74RepresentativeE2E: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
