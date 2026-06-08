import json  # 新增代码+Phase51ComputerStatusUI: 导入 JSON 工具用于读取场景文件；如果没有这行代码，测试无法确认验收 token 是否写入场景。
import tempfile  # 新增代码+Phase51ComputerStatusUI: 导入临时目录隔离 `/computer` 终端状态文件；如果没有这行代码，测试会污染真实 workspace。
import unittest  # 新增代码+Phase51ComputerStatusUI: 导入 unittest 框架承载 Phase51 测试；如果没有这行代码，自动化命令无法发现这些断言。
from pathlib import Path  # 新增代码+Phase51ComputerStatusUI: 导入 Path 管理临时 workspace 路径；如果没有这行代码，路径拼接会变脆弱。

from learning_agent.app.computer_status_renderer import PHASE51_COMPUTER_STATUS_UI_MARKER, PHASE51_COMPUTER_STATUS_UI_OK_TOKEN, phase51_cli_line, render_computer_status, run_phase51_computer_status_ui_contract  # 新增代码+Phase51ComputerStatusUI: 导入预期新增的 Computer 状态 renderer；如果没有这行代码，红灯会证明 Phase51 UI 尚未实现。
from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase51ComputerStatusUI: 导入真实 `/computer` 命令入口；如果没有这行代码，测试无法覆盖用户终端路径。


class WindowsComputerUseTerminalUiPhase51Tests(unittest.TestCase):  # 新增代码+Phase51ComputerStatusUI: 类段开始，集中验证 `/computer` 紧凑状态 UI 和命令入口；如果没有这个类，unittest 不会组织 Phase51 验收。
    def _sample_snapshot(self) -> dict[str, object]:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，构造 renderer 最小快照；如果没有这段函数，各测试会重复大段状态字典。
        return {  # 新增代码+Phase51ComputerStatusUI: 返回完整快照字典；如果没有这行代码，renderer 测试没有输入事实源。
            "lock": {"locked": True, "stale": False, "owner_session_id": "phase51-session", "abort_requested": False},  # 新增代码+Phase51ComputerStatusUI: 提供锁状态；如果没有这行代码，summary 无法显示 lock/abort。
            "approval": {"approval_granted_app_count": 1, "grant_flags": {"observe": True, "desktopAction": True, "systemKeyCombos": False, "clipboardRead": False, "clipboardWrite": False}},  # 新增代码+Phase51ComputerStatusUI: 提供授权状态；如果没有这行代码，summary 无法显示 grant flags。
            "runtime": {"notification_count": 2, "cleanup_count": 1, "last_notification": {"event": "computer_use_turn_cleanup_completed"}},  # 新增代码+Phase51ComputerStatusUI: 提供 runtime 状态；如果没有这行代码，summary 无法显示 cleanup/通知。
            "recovery": {"recent_action_count": 1, "recent_actions": [{"audit_id": "phase51-audit", "action": "click", "chain_available": True, "allowed": True}]},  # 新增代码+Phase51ComputerStatusUI: 提供最近动作 journal；如果没有这行代码，summary 无法显示 recent action。
            "terminal_grants": {"grant_scope": "terminal_ui_only", "granted_app_count": 1, "grant_flags": {"desktopAction": True}},  # 新增代码+Phase51ComputerStatusUI: 提供终端授权草案状态；如果没有这行代码，grant/revoke UI 无法显示。
            "capability_matrix": {"summary": {"available_count": 4, "enabled_count": 2, "blocked_count": 7}, "capabilities": [{"name": "windows_graphics_capture", "available": False, "enabled": False, "reason": "fallback required"}]},  # 新增代码+Phase51ComputerStatusUI: 提供 native 能力矩阵摘要；如果没有这行代码，summary 无法显示能力差距。
        }  # 新增代码+Phase51ComputerStatusUI: 结束快照字典；如果没有这行代码，Python 语法不完整。
    # 新增代码+Phase51ComputerStatusUI: 函数段结束，_sample_snapshot 到此结束；如果没有这个边界说明，读者不容易看出测试快照范围。

    def test_renderer_adds_compact_summary_next_command_and_recent_action(self) -> None:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，验证 renderer 像 `/chrome` 一样有摘要、下一步和最近动作；如果没有这个测试，/computer status 可能继续冗长难扫。
        rendered = render_computer_status(self._sample_snapshot())  # 新增代码+Phase51ComputerStatusUI: 渲染 Computer 状态；如果没有这行代码，后续断言没有输出对象。
        self.assertIn("Computer Summary", rendered)  # 新增代码+Phase51ComputerStatusUI: 断言紧凑摘要区存在；如果没有这行代码，用户仍要在长状态里找重点。
        self.assertIn("next=/computer observe", rendered)  # 新增代码+Phase51ComputerStatusUI: 断言下一步命令可见；如果没有这行代码，小白用户看完状态不知道下一步。
        self.assertIn("recent_action=click audit_id=phase51-audit", rendered)  # 新增代码+Phase51ComputerStatusUI: 断言最近动作进入摘要；如果没有这行代码，用户看不到最近桌面动作链路。
        self.assertIn(PHASE51_COMPUTER_STATUS_UI_MARKER, rendered)  # 新增代码+Phase51ComputerStatusUI: 断言 Phase51 marker 可见；如果没有这行代码，真实终端验收无法稳定识别 UI 阶段。
        self.assertTrue(all(len(line) <= 220 for line in rendered.splitlines()))  # 新增代码+Phase51ComputerStatusUI: 限制单行长度适合真实终端截图；如果没有这行代码，状态 UI 可能被长行撑坏。
    # 新增代码+Phase51ComputerStatusUI: 函数段结束，test_renderer_adds_compact_summary_next_command_and_recent_action 到此结束；如果没有这个边界说明，读者不容易看出 renderer 验收范围。

    def test_computer_terminal_status_uses_compact_renderer(self) -> None:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，验证真实 `/computer status` 使用新 renderer；如果没有这个测试，底层 renderer 可能没有接到用户入口。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase51ComputerStatusUI: 创建临时 workspace；如果没有这行代码，状态命令会写真实项目目录。
            output = run_computer_terminal_command(Path(temp_dir), "/computer status")  # 新增代码+Phase51ComputerStatusUI: 执行真实终端状态命令；如果没有这行代码，无法覆盖用户输入路径。
        self.assertIn("Computer Summary", output)  # 新增代码+Phase51ComputerStatusUI: 断言状态输出包含新摘要区；如果没有这行代码，/computer status 可能仍走旧拼接逻辑。
        self.assertIn("Computer Commands", output)  # 新增代码+Phase51ComputerStatusUI: 断言命令区可见；如果没有这行代码，用户不知道 grant/revoke/observe 等入口。
        self.assertIn("next=/computer observe", output)  # 新增代码+Phase51ComputerStatusUI: 断言下一步建议是 observe；如果没有这行代码，状态面板不够可操作。
        self.assertIn(PHASE51_COMPUTER_STATUS_UI_MARKER, output)  # 新增代码+Phase51ComputerStatusUI: 断言 marker 出现在真实终端状态；如果没有这行代码，验收器无法定位 Phase51。
    # 新增代码+Phase51ComputerStatusUI: 函数段结束，test_computer_terminal_status_uses_compact_renderer 到此结束；如果没有这个边界说明，读者不容易看出终端状态接线范围。

    def test_grant_revoke_and_observe_terminal_commands_are_available(self) -> None:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，验证 grant/revoke/observe 命令可用；如果没有这个测试，Phase51 命令入口可能只停留在文案。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase51ComputerStatusUI: 创建临时 workspace；如果没有这行代码，grant 状态会污染真实项目。
            workspace = Path(temp_dir)  # 新增代码+Phase51ComputerStatusUI: 保存 workspace Path；如果没有这行代码，后续命令路径会重复转换。
            grant_output = run_computer_terminal_command(workspace, "/computer grant notepad.exe desktopAction")  # 新增代码+Phase51ComputerStatusUI: 执行终端授权草案命令；如果没有这行代码，无法证明 grant 入口存在。
            status_output = run_computer_terminal_command(workspace, "/computer status")  # 新增代码+Phase51ComputerStatusUI: 再读取状态；如果没有这行代码，无法证明 grant 被状态面板展示。
            observe_output = run_computer_terminal_command(workspace, "/computer observe")  # 新增代码+Phase51ComputerStatusUI: 执行只读 observe 命令；如果没有这行代码，无法证明 observe 入口存在。
            revoke_output = run_computer_terminal_command(workspace, "/computer revoke notepad.exe")  # 新增代码+Phase51ComputerStatusUI: 执行终端撤销授权命令；如果没有这行代码，无法证明 revoke 入口存在。
        self.assertIn("grant_recorded=true", grant_output)  # 新增代码+Phase51ComputerStatusUI: 断言 grant 命令记录成功；如果没有这行代码，grant 可能只是空输出。
        self.assertIn("grant_scope=terminal_ui_only", grant_output)  # 新增代码+Phase51ComputerStatusUI: 断言授权边界明确；如果没有这行代码，用户可能误以为它绕过 controller 审批。
        self.assertIn("terminal_granted_app_count=1", status_output)  # 新增代码+Phase51ComputerStatusUI: 断言 status 展示终端授权数量；如果没有这行代码，grant 状态不可见。
        self.assertIn("computer_observe", observe_output)  # 新增代码+Phase51ComputerStatusUI: 断言 observe 命令调用只读入口；如果没有这行代码，observe 可能只是文案。
        self.assertIn("revoked=true", revoke_output)  # 新增代码+Phase51ComputerStatusUI: 断言 revoke 命令成功；如果没有这行代码，授权草案无法收回。
    # 新增代码+Phase51ComputerStatusUI: 函数段结束，test_grant_revoke_and_observe_terminal_commands_are_available 到此结束；如果没有这个边界说明，读者不容易看出命令入口范围。

    def test_phase51_cli_contract_and_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，验证 CLI 合同和场景 token；如果没有这个测试，真实验收可能漏掉状态 UI 证据。
        report = run_phase51_computer_status_ui_contract()  # 新增代码+Phase51ComputerStatusUI: 运行 Phase51 合同自检；如果没有这行代码，CLI token 没有结构化报告来源。
        line = phase51_cli_line(report)  # 新增代码+Phase51ComputerStatusUI: 生成稳定单行 token；如果没有这行代码，场景断言要解析复杂 JSON。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase51ComputerStatusUI: 定位项目根目录；如果没有这行代码，场景文件路径会依赖当前工作目录。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase51_computer_status_ui.json"  # 新增代码+Phase51ComputerStatusUI: 定位 Phase51 场景；如果没有这行代码，测试无法确认验收配置存在。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase51ComputerStatusUI: 读取场景 JSON；如果没有这行代码，场景 token 漏写不会被发现。
        expected_tokens = {PHASE51_COMPUTER_STATUS_UI_MARKER, PHASE51_COMPUTER_STATUS_UI_OK_TOKEN, "summary=true", "next_command=true", "commands=true", "grant_revoke=true", "actions_expanded=false"}  # 新增代码+Phase51ComputerStatusUI: 列出 Phase51 必须稳定输出的 token；如果没有这行代码，成功标准会散落多个断言。
        for token in expected_tokens:  # 新增代码+Phase51ComputerStatusUI: 遍历所有关键 token；如果没有这行代码，只能重复写多个断言。
            self.assertIn(token, line)  # 新增代码+Phase51ComputerStatusUI: 断言 CLI 行包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase51ComputerStatusUI: 断言 debug log 检查包含 token；如果没有这行代码，真实验收可能不查 UI。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase51ComputerStatusUI: 断言最终回答检查包含 token；如果没有这行代码，用户可见输出可能漏证据。
    # 新增代码+Phase51ComputerStatusUI: 函数段结束，test_phase51_cli_contract_and_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，读者不容易看出 CLI/场景范围。


if __name__ == "__main__":  # 新增代码+Phase51ComputerStatusUI: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式单独验证 Phase51。
    unittest.main()  # 新增代码+Phase51ComputerStatusUI: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行断言。
