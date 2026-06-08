import json  # 新增代码+Phase63ControllerTakeover: 导入 JSON 用来写入假的验收结果；如果没有这行代码，测试无法模拟 controller 产出的 result.json。
import tempfile  # 新增代码+Phase63ControllerTakeover: 导入临时目录隔离测试证据；如果没有这行代码，测试可能污染真实 acceptance runs。
import unittest  # 新增代码+Phase63ControllerTakeover: 导入 unittest 承载 Phase63 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase63ControllerTakeover: 导入 Path 处理 Windows 路径；如果没有这行代码，controller.ps1、run_dir、scenario 路径容易拼错。

from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase63ControllerTakeover: 导入真实 `/computer` 终端命令入口；如果没有这行代码，测试无法证明控制器调试面板可见。
from learning_agent.computer_use.controller_takeover import PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER, PHASE63_WINDOWS_CONTROLLER_TAKEOVER_OK_TOKEN, WindowsComputerUseControllerTakeoverDebugSurface, phase63_cli_line, run_phase63_controller_takeover_contract  # 新增代码+Phase63ControllerTakeover: 导入预期 Phase63 API；如果没有这行代码，红灯无法证明生产模块尚未实现。


class WindowsComputerUseControllerTakeoverPhase63Tests(unittest.TestCase):  # 新增代码+Phase63ControllerTakeover: 类段开始，集中验证外部 agent 接管、证据读取和安全边界；如果没有这个类，Phase63 没有自动化门禁。
    def _write_fake_run(self, root: Path) -> Path:  # 新增代码+Phase63ControllerTakeover: 函数段开始，构造一个最小 acceptance run 目录；如果没有这段函数，证据读取测试会依赖真实历史运行。
        run_dir = root / "agent_capability_phase63_fake_run"  # 新增代码+Phase63ControllerTakeover: 定义假的 run 目录；如果没有这行代码，后续 result/events/screenshot 没有统一父目录。
        run_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase63ControllerTakeover: 创建 run 目录；如果没有这行代码，写入证据文件会失败。
        screenshot_path = run_dir / "final.png"  # 新增代码+Phase63ControllerTakeover: 定义假的最终截图路径；如果没有这行代码，证据包无法说明截图是否存在。
        screenshot_path.write_bytes(b"\x89PNG\r\n\x1a\n")  # 新增代码+Phase63ControllerTakeover: 写入最小 PNG 头作为占位截图；如果没有这行代码，截图存在性检查没有样本。
        events_path = run_dir / "events.jsonl"  # 新增代码+Phase63ControllerTakeover: 定义事件日志路径；如果没有这行代码，controller 事件证据无法被读取。
        events_path.write_text('{"event":"agent_ready"}\n{"event":"assertion_passed"}\n', encoding="utf-8")  # 新增代码+Phase63ControllerTakeover: 写入最小事件流；如果没有这行代码，证据读取只会看到 result 而看不到过程。
        readable_path = run_dir / "latest_run_readable.md"  # 新增代码+Phase63ControllerTakeover: 定义可读摘要路径；如果没有这行代码，失败时给人看的摘要证据缺失。
        readable_path.write_text("# fake run\ncompleted=true\n", encoding="utf-8")  # 新增代码+Phase63ControllerTakeover: 写入可读摘要；如果没有这行代码，证据包无法证明 controller 会保留人类可读材料。
        result_path = run_dir / "result.json"  # 新增代码+Phase63ControllerTakeover: 定义 result.json 路径；如果没有这行代码，Phase63 无法复用现有验收结果格式。
        result_path.write_text(json.dumps({"completed": True, "assertion": {"passed": True}, "permission_sent_count": 0, "screenshots": {"final": str(screenshot_path)}}, ensure_ascii=False), encoding="utf-8")  # 新增代码+Phase63ControllerTakeover: 写入最小成功结果；如果没有这行代码，证据读取无法断言 completed/assertion/permission。
        return run_dir  # 新增代码+Phase63ControllerTakeover: 返回 run 目录给测试使用；如果没有这行代码，调用方不知道证据写到哪里。
    # 新增代码+Phase63ControllerTakeover: 函数段结束，_write_fake_run 到此结束；如果没有这个边界说明，读者不容易看出 fake run 构造范围。

    def test_takeover_status_and_plan_require_visible_terminal_without_approval_bypass(self) -> None:  # 新增代码+Phase63ControllerTakeover: 函数段开始，验证 controller 接管计划必须走可见终端且不能绕过审批；如果没有这个测试，外部 agent 可能被误设计成静默越权入口。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase63ControllerTakeover: 使用临时目录隔离证据包；如果没有这行代码，测试会写入真实 memory。
            surface = WindowsComputerUseControllerTakeoverDebugSurface(repo_root=Path.cwd(), base_dir=Path(temp_dir) / "controller_takeover")  # 新增代码+Phase63ControllerTakeover: 创建调试面板对象；如果没有这行代码，测试没有被测对象。
            status = surface.status()  # 新增代码+Phase63ControllerTakeover: 读取 Phase63 状态；如果没有这行代码，无法断言安全边界。
            plan = surface.build_takeover_plan("scenarios/agent_capability_phase62_high_level_tools.json", prompt="请查看 /computer status")  # 新增代码+Phase63ControllerTakeover: 生成外部 agent 可执行的 controller 启动计划；如果没有这行代码，无法证明 Codex 可按同一入口输入真实 prompt。
        self.assertEqual(status["marker"], PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER)  # 新增代码+Phase63ControllerTakeover: 断言 marker 稳定；如果没有这行代码，真实终端验收无法稳定匹配 Phase63。
        self.assertTrue(status["visible_terminal_required"])  # 新增代码+Phase63ControllerTakeover: 断言必须保留可见终端门禁；如果没有这行代码，HTTP/stdio 可能被误当最终验收。
        self.assertTrue(status["http_loopback_only"])  # 新增代码+Phase63ControllerTakeover: 断言 HTTP 调试面仅限本机；如果没有这行代码，控制面可能暴露到网络。
        self.assertTrue(status["token_required"])  # 新增代码+Phase63ControllerTakeover: 断言控制面设计要求 token；如果没有这行代码，外部 agent 接管缺少最小认证边界。
        self.assertFalse(status["approval_bypass_allowed"])  # 新增代码+Phase63ControllerTakeover: 断言不允许绕过审批；如果没有这行代码，controller 可能越过 Phase60 授权链。
        self.assertTrue(plan["uses_start_oauth_agent_bat"])  # 新增代码+Phase63ControllerTakeover: 断言计划最终启动 start_oauth_agent.bat；如果没有这行代码，真实可见终端规则可能被绕开。
        self.assertIn("controller.ps1", plan["powershell_command"])  # 新增代码+Phase63ControllerTakeover: 断言计划复用现有 controller.ps1；如果没有这行代码，可能出现未审计的新启动脚本。
        self.assertFalse(plan["http_replaces_visible_terminal"])  # 新增代码+Phase63ControllerTakeover: 断言 HTTP 不替代可见终端验收；如果没有这行代码，Phase63 会违反用户的强制门禁。
    # 新增代码+Phase63ControllerTakeover: 函数段结束，test_takeover_status_and_plan_require_visible_terminal_without_approval_bypass 到此结束；如果没有这个边界说明，读者不容易看出安全计划测试范围。

    def test_read_acceptance_run_and_export_evidence_package(self) -> None:  # 新增代码+Phase63ControllerTakeover: 函数段开始，验证外部 agent 能读取验收 run 并导出证据包；如果没有这个测试，失败排查仍然需要人工到处翻文件。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase63ControllerTakeover: 使用临时目录隔离 fake run 和证据包；如果没有这行代码，测试会污染真实 runs。
            root = Path(temp_dir)  # 新增代码+Phase63ControllerTakeover: 保存临时根目录；如果没有这行代码，路径转换会重复且容易写错。
            run_dir = self._write_fake_run(root)  # 新增代码+Phase63ControllerTakeover: 构造假的验收 run；如果没有这行代码，证据读取没有样本。
            surface = WindowsComputerUseControllerTakeoverDebugSurface(repo_root=Path.cwd(), base_dir=root / "controller_takeover")  # 新增代码+Phase63ControllerTakeover: 创建调试面板对象；如果没有这行代码，无法读取 run。
            evidence = surface.read_acceptance_run(run_dir)  # 新增代码+Phase63ControllerTakeover: 读取 run 证据摘要；如果没有这行代码，无法断言 completed/assertion/screenshot。
            package = surface.export_evidence_package(run_dir)  # 新增代码+Phase63ControllerTakeover: 导出外部 agent 可带走的证据包；如果没有这行代码，失败现场无法稳定交接。
            package_exists = Path(package["package_path"]).exists()  # 修改代码+Phase63ControllerTakeover: 在临时目录销毁前记录证据包是否存在；如果没有这行代码，with 结束后目录被删会误判生产代码失败。
        self.assertTrue(evidence["result_json_exists"])  # 新增代码+Phase63ControllerTakeover: 断言 result.json 被发现；如果没有这行代码，证据读取可能只是假状态。
        self.assertTrue(evidence["event_log_exists"])  # 新增代码+Phase63ControllerTakeover: 断言事件日志被发现；如果没有这行代码，controller 过程证据可能缺失。
        self.assertTrue(evidence["readable_summary_exists"])  # 新增代码+Phase63ControllerTakeover: 断言人类可读摘要被发现；如果没有这行代码，小白用户难以复盘。
        self.assertTrue(evidence["completed"])  # 新增代码+Phase63ControllerTakeover: 断言 completed 字段被读取；如果没有这行代码，证据读取无法判断 run 是否结束。
        self.assertTrue(evidence["assertion_passed"])  # 新增代码+Phase63ControllerTakeover: 断言 assertion.passed 被读取；如果没有这行代码，run 成败会被模糊处理。
        self.assertEqual(evidence["permission_sent_count"], 0)  # 新增代码+Phase63ControllerTakeover: 断言 controller 没有自动发送危险确认；如果没有这行代码，外部接管可能绕过用户授权。
        self.assertTrue(package_exists)  # 修改代码+Phase63ControllerTakeover: 断言证据包曾经落盘；如果没有这行代码，导出函数可能只返回空文案。
        self.assertTrue(package["evidence_package"])  # 新增代码+Phase63ControllerTakeover: 断言证据包标记为真；如果没有这行代码，外部 agent 不知道该结果是否可交接。
    # 新增代码+Phase63ControllerTakeover: 函数段结束，test_read_acceptance_run_and_export_evidence_package 到此结束；如果没有这个边界说明，读者不容易看出证据读取测试范围。

    def test_abort_preview_terminal_command_does_not_bypass_policy(self) -> None:  # 新增代码+Phase63ControllerTakeover: 函数段开始，验证外部 controller 的急停入口只是终端命令预览；如果没有这个测试，controller 可能直接修改锁文件绕过链路。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase63ControllerTakeover: 使用临时目录隔离对象状态；如果没有这行代码，测试可能读写真实 memory。
            surface = WindowsComputerUseControllerTakeoverDebugSurface(repo_root=Path.cwd(), base_dir=Path(temp_dir) / "controller_takeover")  # 新增代码+Phase63ControllerTakeover: 创建调试面板对象；如果没有这行代码，无法生成 abort 命令。
            preview = surface.controller_abort_command("phase63 user stop")  # 新增代码+Phase63ControllerTakeover: 生成急停命令预览；如果没有这行代码，无法证明外部 agent 能请求 abort。
        self.assertEqual(preview["terminal_command"], "/computer abort phase63 user stop")  # 新增代码+Phase63ControllerTakeover: 断言急停走真实终端命令；如果没有这行代码，controller 可能直接篡改内部状态。
        self.assertTrue(preview["controller_can_abort"])  # 新增代码+Phase63ControllerTakeover: 断言 controller 能触发急停路径；如果没有这行代码，外部接管缺少安全退出按钮。
        self.assertFalse(preview["approval_bypass_allowed"])  # 新增代码+Phase63ControllerTakeover: 断言急停预览也不能绕过审批；如果没有这行代码，安全边界会在异常路径松动。
    # 新增代码+Phase63ControllerTakeover: 函数段结束，test_abort_preview_terminal_command_does_not_bypass_policy 到此结束；如果没有这个边界说明，读者不容易看出 abort 测试范围。

    def test_phase63_cli_terminal_status_and_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase63ControllerTakeover: 函数段开始，验证 CLI、终端面板和真实验收场景 token 稳定；如果没有这个测试，Phase63 可见入口可能漏接。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase63ControllerTakeover: 使用临时目录隔离合同状态；如果没有这行代码，自检会污染真实 memory。
            report = run_phase63_controller_takeover_contract(base_dir=Path(temp_dir) / "contract")  # 新增代码+Phase63ControllerTakeover: 运行 Phase63 合同自检；如果没有这行代码，CLI token 没有结构化来源。
            output = run_computer_terminal_command(Path(temp_dir), "/computer controller")  # 新增代码+Phase63ControllerTakeover: 通过真实 `/computer` 入口查看 controller 状态；如果没有这行代码，用户侧可见性无证据。
        cli_line = phase63_cli_line(report)  # 新增代码+Phase63ControllerTakeover: 生成稳定 CLI token 行；如果没有这行代码，场景验收需要解析复杂 JSON。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase63_controller_takeover.json")  # 新增代码+Phase63ControllerTakeover: 定位 Phase63 真实终端场景；如果没有这行代码，场景缺失不会被测试发现。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase63ControllerTakeover: 读取场景文本；如果没有这行代码，token 漏配无法被发现。
        expected_tokens = {PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER, PHASE63_WINDOWS_CONTROLLER_TAKEOVER_OK_TOKEN, "controller_surface=true", "launches_visible_terminal=true", "reads_acceptance_run=true", "evidence_package=true", "can_abort=true", "http_loopback_only=true", "token_required=true", "approval_bypass_blocked=true", "visible_terminal_required=true", "actions_expanded=false"}  # 新增代码+Phase63ControllerTakeover: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        self.assertIn("Computer Controller Takeover", output)  # 新增代码+Phase63ControllerTakeover: 断言终端状态标题可见；如果没有这行代码，用户找不到外部控制器调试面板。
        self.assertIn(PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER, output)  # 新增代码+Phase63ControllerTakeover: 断言终端输出 marker；如果没有这行代码，验收器无法稳定匹配 Phase63。
        for token in expected_tokens:  # 新增代码+Phase63ControllerTakeover: 遍历关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase63ControllerTakeover: 断言 CLI 包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase63ControllerTakeover: 断言场景包含 token；如果没有这行代码，真实终端验收可能漏检。
    # 新增代码+Phase63ControllerTakeover: 函数段结束，test_phase63_cli_terminal_status_and_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，读者不容易看出 CLI 场景测试范围。
# 新增代码+Phase63ControllerTakeover: 类段结束，WindowsComputerUseControllerTakeoverPhase63Tests 到此结束；如果没有这个边界说明，读者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase63ControllerTakeover: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase63ControllerTakeover: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
