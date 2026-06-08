import json  # 新增代码+Phase76-89WindowsLiveControl: 导入 JSON 用来校验真实终端场景文件格式；如果没有这行代码，场景文件写坏要到验收时才会暴露。
import tempfile  # 新增代码+Phase76-89WindowsLiveControl: 导入临时目录隔离验收报告；如果没有这行代码，测试会污染真实运行目录。
import unittest  # 新增代码+Phase76-89WindowsLiveControl: 导入 unittest 承载 Phase76-89 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase76-89WindowsLiveControl: 导入 Path 管理 Windows 路径；如果没有这行代码，临时目录和场景路径容易拼错。

from learning_agent.computer_use.production_live_control import PHASE76_89_WINDOWS_LIVE_CONTROL_MARKER, PHASE76_89_WINDOWS_LIVE_CONTROL_OK_TOKEN, WindowsLiveControlPermissionGate, WindowsProductionClipboardGuard, build_phase76_89_claudecode_parity_matrix, build_phase82_app_launch_plan, build_phase86_high_level_tool_surface, build_phase88_representative_e2e_matrix, phase76_89_cli_line, run_phase76_89_windows_live_control_contract  # 新增代码+Phase76-89WindowsLiveControl: 导入本轮生产级闭环入口；如果没有这行代码，测试无法验证新模块是否实现。


class WindowsComputerUseProductionLiveControlPhase76To89Tests(unittest.TestCase):  # 新增代码+Phase76-89WindowsLiveControl: 类段开始，集中验证 Phase76-89 Windows Computer Use 生产闭环；如果没有这个类，本轮 35% 差距补齐没有自动化门禁。
    def test_phase76_89_contract_covers_every_confirmed_phase(self) -> None:  # 新增代码+Phase76-89WindowsLiveControl: 函数段开始，验证蓝图 76-89 全部被合同覆盖；如果没有这个测试，漏阶段也可能误报完成。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase76-89WindowsLiveControl: 使用临时目录隔离报告证据；如果没有这行代码，测试会写入默认运行目录。
            report = run_phase76_89_windows_live_control_contract(base_dir=Path(temp_dir), real_smoke=False)  # 新增代码+Phase76-89WindowsLiveControl: 运行安全合同模式；如果没有这行代码，测试没有结构化事实来源。
        self.assertEqual(report["marker"], PHASE76_89_WINDOWS_LIVE_CONTROL_MARKER)  # 新增代码+Phase76-89WindowsLiveControl: 断言 READY marker 稳定；如果没有这行代码，真实终端无法稳定匹配新能力。
        self.assertEqual(report["ok_token"], PHASE76_89_WINDOWS_LIVE_CONTROL_OK_TOKEN)  # 新增代码+Phase76-89WindowsLiveControl: 断言 OK token 稳定；如果没有这行代码，用户无法一眼确认本阶段通过。
        self.assertTrue(report["passed"])  # 新增代码+Phase76-89WindowsLiveControl: 断言总合同通过；如果没有这行代码，单项失败可能被忽略。
        self.assertEqual(report["phase_count"], 14)  # 新增代码+Phase76-89WindowsLiveControl: 断言 Phase76-89 共十四个阶段；如果没有这行代码，阶段数量漂移不会被发现。
        self.assertEqual(report["baseline_gap_percent"], 35)  # 新增代码+Phase76-89WindowsLiveControl: 断言本轮补齐的差距基线是 35%；如果没有这行代码，用户关心的差距数字没有门禁。
        for phase_name, phase_passed in report["phase_results"].items():  # 新增代码+Phase76-89WindowsLiveControl: 遍历每个阶段结果；如果没有这行代码，逐阶段断言会重复且容易漏项。
            self.assertTrue(phase_passed, phase_name)  # 新增代码+Phase76-89WindowsLiveControl: 断言每个阶段都通过；如果没有这行代码，总体通过原因不够透明。
        self.assertIn("mspaint_draw_pikachu", {item["id"] for item in report["representative_e2e"]})  # 新增代码+Phase76-89WindowsLiveControl: 断言画图皮卡丘场景存在；如果没有这行代码，用户点名目标可能被漏掉。
        self.assertTrue(any(item.get("requires_strokes") for item in report["representative_e2e"]))  # 新增代码+Phase76-89WindowsLiveControl: 断言皮卡丘场景要求拟人笔画；如果没有这行代码，直接图片文件作弊可能混入。
        self.assertTrue(all(not item["direct_image_file_cheat"] for item in report["representative_e2e"]))  # 新增代码+Phase76-89WindowsLiveControl: 断言代表性场景禁止图片作弊；如果没有这行代码，Paint 场景可被伪造文件绕过。
    # 新增代码+Phase76-89WindowsLiveControl: 函数段结束，test_phase76_89_contract_covers_every_confirmed_phase 到此结束；如果没有这个边界说明，初学者不容易看出总合同范围。

    def test_phase76_89_components_keep_safety_and_genericity_visible(self) -> None:  # 新增代码+Phase76-89WindowsLiveControl: 函数段开始，验证关键组件单独可读可测；如果没有这个测试，安全门和通用能力可能只藏在总报告里。
        matrix = build_phase76_89_claudecode_parity_matrix()  # 新增代码+Phase76-89WindowsLiveControl: 生成 ClaudeCode 对齐矩阵；如果没有这行代码，Phase76 需求表没有测试来源。
        self.assertEqual(matrix["phase_ids"], list(range(76, 90)))  # 新增代码+Phase76-89WindowsLiveControl: 断言矩阵阶段号完整；如果没有这行代码，漏阶段不会被发现。
        self.assertGreaterEqual(len(build_phase86_high_level_tool_surface()), 12)  # 新增代码+Phase76-89WindowsLiveControl: 断言高层工具数量足够；如果没有这行代码，模型工具面可能退化成少量底层动作。
        self.assertTrue(build_phase82_app_launch_plan("paint")["safe_start_process_plan"])  # 新增代码+Phase76-89WindowsLiveControl: 断言自然说 paint 也能映射到 mspaint；如果没有这行代码，真实用户 prompt 容易失败。
        self.assertTrue(any(item["id"] == "security_window_denial" for item in build_phase88_representative_e2e_matrix()))  # 新增代码+Phase76-89WindowsLiveControl: 断言安全拒绝场景存在；如果没有这行代码，通用控制可能忽视高风险窗口。
        gate = WindowsLiveControlPermissionGate()  # 新增代码+Phase76-89WindowsLiveControl: 创建权限门；如果没有这行代码，安全拒绝无法单独验证。
        denied = gate.evaluate("click", {"app_id": "terminal", "title": "PowerShell Terminal"})  # 新增代码+Phase76-89WindowsLiveControl: 模拟终端窗口点击；如果没有这行代码，sentinel 拒绝没有事实样本。
        allowed = gate.evaluate("click", {"app_id": "mspaint.exe", "title": "Untitled - Paint"})  # 新增代码+Phase76-89WindowsLiveControl: 模拟画图窗口点击；如果没有这行代码，普通代表应用允许路径没有样本。
        self.assertFalse(denied["allowed"])  # 新增代码+Phase76-89WindowsLiveControl: 断言终端被拒绝；如果没有这行代码，敏感窗口可能被误操作。
        self.assertTrue(allowed["allowed"])  # 新增代码+Phase76-89WindowsLiveControl: 断言画图被允许；如果没有这行代码，安全门可能过度阻断普通应用。
    # 新增代码+Phase76-89WindowsLiveControl: 函数段结束，test_phase76_89_components_keep_safety_and_genericity_visible 到此结束；如果没有这个边界说明，初学者不容易看出组件门禁范围。

    def test_phase81_clipboard_guard_restores_user_clipboard(self) -> None:  # 新增代码+Phase76-89WindowsLiveControl: 函数段开始，验证剪贴板保存验证恢复；如果没有这个测试，用户剪贴板可能被功能污染。
        pasted_payloads: list[str] = []  # 新增代码+Phase76-89WindowsLiveControl: 准备记录粘贴回调收到的文本；如果没有这行代码，无法确认回调是否被调用。
        guard = WindowsProductionClipboardGuard(initial_text="original-user-copy")  # 新增代码+Phase76-89WindowsLiveControl: 创建带原始内容的剪贴板守卫；如果没有这行代码，恢复逻辑没有可验证原值。
        result = guard.paste_with_restore("new controlled text", pasted_payloads.append)  # 新增代码+Phase76-89WindowsLiveControl: 执行安全粘贴流程；如果没有这行代码，剪贴板生命周期没有事实样本。
        self.assertEqual(pasted_payloads, ["new controlled text"])  # 新增代码+Phase76-89WindowsLiveControl: 断言粘贴回调收到新文本；如果没有这行代码，写入成功不代表真的进入粘贴路径。
        self.assertEqual(guard.read(), "original-user-copy")  # 新增代码+Phase76-89WindowsLiveControl: 断言用户原剪贴板已恢复；如果没有这行代码，污染剪贴板不会被发现。
        self.assertTrue(result["saved"] and result["verified"] and result["pasted"] and result["restored"])  # 新增代码+Phase76-89WindowsLiveControl: 断言四段生命周期全通过；如果没有这行代码，某个关键环节失败可能被忽略。
        self.assertEqual(guard.restore_count, 1)  # 新增代码+Phase76-89WindowsLiveControl: 断言恢复执行一次；如果没有这行代码，finally 清理路径是否运行不明确。
    # 新增代码+Phase76-89WindowsLiveControl: 函数段结束，test_phase81_clipboard_guard_restores_user_clipboard 到此结束；如果没有这个边界说明，初学者不容易看出剪贴板门禁范围。

    def test_phase76_89_cli_line_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase76-89WindowsLiveControl: 函数段开始，验证 CLI 行和真实终端场景 token 稳定；如果没有这个测试，controller 可能漏检关键字段。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase76-89WindowsLiveControl: 使用临时目录隔离合同证据；如果没有这行代码，测试会污染默认目录。
            report = run_phase76_89_windows_live_control_contract(base_dir=Path(temp_dir), real_smoke=False)  # 新增代码+Phase76-89WindowsLiveControl: 运行 Phase76-89 合同；如果没有这行代码，CLI 行没有结构化来源。
        cli_line = phase76_89_cli_line(report)  # 新增代码+Phase76-89WindowsLiveControl: 生成稳定 CLI token 行；如果没有这行代码，场景验收需要解析复杂 JSON。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase76_89_windows_live_control.json")  # 新增代码+Phase76-89WindowsLiveControl: 定位真实终端场景文件；如果没有这行代码，场景缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase76-89WindowsLiveControl: 读取场景文本；如果没有这行代码，场景 token 漏配无法被发现。
        json.loads(scenario_text)  # 新增代码+Phase76-89WindowsLiveControl: 校验场景是合法 JSON；如果没有这行代码，controller 运行时才会暴露格式错误。
        expected_tokens = {PHASE76_89_WINDOWS_LIVE_CONTROL_MARKER, PHASE76_89_WINDOWS_LIVE_CONTROL_OK_TOKEN, "passed=true", "phase_count=14", "claudecode_gap_closed=true", "unified_host_adapter=true", "live_observation_fusion=true", "display_coordinate_model=true", "sendinput_production_gate=true", "clipboard_save_verify_restore=true", "app_launch_focus_plan=true", "allowlist_sentinel_permissions=true", "global_abort_cleanup_hooks=true", "high_level_tool_surface=true", "observe_act_verify_loop=true", "representative_e2e_matrix=true", "mspaint_pikachu_scenario=true", "humanlike_drawing_actions=true", "direct_image_file_cheat=false", "security_window_denial=true", "real_visible_terminal_gate=true", "uncontrolled_actions_expanded=false"}  # 新增代码+Phase76-89WindowsLiveControl: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase76-89WindowsLiveControl: 遍历每个关键 token；如果没有这行代码，重复断言容易遗漏。
            self.assertIn(token, cli_line)  # 新增代码+Phase76-89WindowsLiveControl: 断言 CLI 输出包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase76-89WindowsLiveControl: 断言真实终端场景也包含 token；如果没有这行代码，自动测试和真实验收可能不一致。
    # 新增代码+Phase76-89WindowsLiveControl: 函数段结束，test_phase76_89_cli_line_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 场景验收范围。
# 新增代码+Phase76-89WindowsLiveControl: 类段结束，WindowsComputerUseProductionLiveControlPhase76To89Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase76-89WindowsLiveControl: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase76-89WindowsLiveControl: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
