import re  # 新增代码+Phase98UniversalComputerUseMode：导入正则用来从 full 请求输出提取确认 token；如果没有这行代码，测试无法验证二次确认命令链路。
import tempfile  # 新增代码+Phase98UniversalComputerUseMode：导入临时目录用来隔离 `/computer` 命令状态；如果没有这行代码，测试会污染真实 memory 目录。
import unittest  # 新增代码+Phase98UniversalComputerUseMode：导入 unittest 以符合项目现有测试风格；如果没有这行代码，标准测试运行器找不到测试类。
from pathlib import Path  # 新增代码+Phase98UniversalComputerUseMode：导入 Path 统一传递 Windows 工作区路径；如果没有这行代码，命令入口会收到脆弱的字符串路径。

from learning_agent.app.computer_status_renderer import render_computer_status  # 新增代码+Phase98UniversalComputerUseMode：导入 `/computer status` renderer 以覆盖坏 snapshot 容错；如果没有这行代码，TTL 崩溃只能在真实终端里暴露。
from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase98UniversalComputerUseMode：导入真实 `/computer` 终端命令入口；如果没有这行代码，测试只能测底层 store 而覆盖不到用户命令。


class ComputerUseModeCommandPhase98Tests(unittest.TestCase):  # 新增代码+Phase98UniversalComputerUseMode：类段开始，集中验证 Phase98 模式命令真实终端契约；如果没有这个类，Task3 的 `/computer` 接入没有红绿灯。
    def assert_contains_all(self, output: str, expected_parts: list[str]) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，复用多 token 断言；如果没有这段函数，测试会重复很多难读的 assertIn。
        for expected_part in expected_parts:  # 新增代码+Phase98UniversalComputerUseMode：逐个检查必须出现的输出片段；如果没有这行代码，测试只会验证一个字段而漏掉契约。
            self.assertIn(expected_part, output)  # 新增代码+Phase98UniversalComputerUseMode：断言当前片段存在；如果没有这行代码，输出缺字段也会误通过。
    # 新增代码+Phase98UniversalComputerUseMode：函数段结束，assert_contains_all 到此结束；如果没有这个边界说明，读者不容易看出断言 helper 的范围。

    def test_computer_use_opens_normal_mode_without_real_desktop_actions(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 `/computer use` 打开 normal 且不触碰真实桌面；如果没有这段测试，命令可能仍是 unsupported 或误发输入。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建临时 workspace；如果没有这行代码，mode session 会写入真实项目 memory。
            output = run_computer_terminal_command(Path(temp_dir), "/computer use")  # 新增代码+Phase98UniversalComputerUseMode：执行真实终端 normal mode 命令；如果没有这行代码，测试无法覆盖用户输入路径。
        self.assert_contains_all(output, ["Computer Use Mode", "mode=normal", "per_app_allowlist_required=false", "ordinary_apps_allowed_by_risk_policy=true", "real_desktop_touched=false", "low_level_event_count=0"])  # 新增代码+Phase98UniversalComputerUseMode：断言 normal 输出完整契约；如果没有这行代码，白名单纠偏和零低层事件可能悄悄丢失。
    # 新增代码+Phase98UniversalComputerUseMode：函数段结束，test_computer_use_opens_normal_mode_without_real_desktop_actions 到此结束；如果没有这个边界说明，读者不容易看出 normal 命令测试范围。

    def test_computer_use_observe_opens_observe_mode_without_real_desktop_actions(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 `/computer use --observe` 只打开观察模式；如果没有这段测试，observe 可能继续走旧 `/computer observe` 真实观察入口。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建临时 workspace；如果没有这行代码，observe mode 状态会污染真实目录。
            output = run_computer_terminal_command(Path(temp_dir), "/computer use --observe")  # 新增代码+Phase98UniversalComputerUseMode：执行真实终端 observe mode 命令；如果没有这行代码，测试无法证明新参数被识别。
        self.assert_contains_all(output, ["Computer Use Mode", "mode=observe", "real_desktop_touched=false", "low_level_event_count=0"])  # 新增代码+Phase98UniversalComputerUseMode：断言 observe 输出零真实动作；如果没有这行代码，观察模式安全边界可能退化。
    # 新增代码+Phase98UniversalComputerUseMode：函数段结束，test_computer_use_observe_opens_observe_mode_without_real_desktop_actions 到此结束；如果没有这个边界说明，读者不容易看出 observe 命令测试范围。

    def test_computer_stop_stops_mode_and_status_reports_stopped(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 `/computer stop` 停止模式并保留状态可见；如果没有这段测试，stop 可能只写旧 abort 而不停止模式 session。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建临时 workspace；如果没有这行代码，stop 测试会读写真实状态。
            workspace = Path(temp_dir)  # 新增代码+Phase98UniversalComputerUseMode：保存 workspace 路径供多条命令共用；如果没有这行代码，后续命令可能不在同一 session 中运行。
            run_computer_terminal_command(workspace, "/computer use")  # 新增代码+Phase98UniversalComputerUseMode：先打开 normal mode；如果没有这行代码，stop 无法证明从活动模式变成 stopped。
            stop_output = run_computer_terminal_command(workspace, "/computer stop")  # 新增代码+Phase98UniversalComputerUseMode：执行真实终端 stop 命令；如果没有这行代码，测试无法覆盖用户停止入口。
            status_output = run_computer_terminal_command(workspace, "/computer status")  # 新增代码+Phase98UniversalComputerUseMode：停止后读取 status；如果没有这行代码，无法证明 stopped 持久显示。
        self.assertIn("stopped=true", stop_output)  # 新增代码+Phase98UniversalComputerUseMode：断言 stop 输出显示成功；如果没有这行代码，用户看不到停止是否生效。
        self.assert_contains_all(status_output, ["Computer Use Mode", "mode=stopped", "full_mode=false"])  # 新增代码+Phase98UniversalComputerUseMode：断言 status 显示 stopped 模式；如果没有这行代码，状态面板可能仍显示 normal。
    # 新增代码+Phase98UniversalComputerUseMode：函数段结束，test_computer_stop_stops_mode_and_status_reports_stopped 到此结束；如果没有这个边界说明，读者不容易看出 stop/status 测试范围。

    def test_computer_status_renderer_bad_or_missing_ttl_defaults_to_zero(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证坏 TTL 或缺 TTL 不会拖垮 status 渲染；如果没有这段测试，旧坏状态可能让 `/computer status` 直接崩溃。
        bad_ttl_output = render_computer_status({"mode_session": {"mode": "normal", "full_mode": False, "ttl_seconds": "not-a-number", "per_app_allowlist_required": False, "ordinary_apps_allowed_by_risk_policy": True}})  # 新增代码+Phase98UniversalComputerUseMode：传入字符串坏 TTL 复现质量复审指出的崩溃场景；如果没有这行代码，ValueError 回归不会被测试抓到。
        missing_ttl_output = render_computer_status({"mode_session": {"mode": "normal", "full_mode": False, "per_app_allowlist_required": False, "ordinary_apps_allowed_by_risk_policy": True}})  # 新增代码+Phase98UniversalComputerUseMode：传入缺失 TTL 的旧状态；如果没有这行代码，缺字段默认值不会被明确覆盖。
        self.assert_contains_all(bad_ttl_output, ["Computer Use Mode", "mode=normal", "ttl_seconds=0"])  # 新增代码+Phase98UniversalComputerUseMode：断言坏 TTL 被降级为 0；如果没有这行代码，渲染器可能吞错字段或输出不稳定。
        self.assert_contains_all(missing_ttl_output, ["Computer Use Mode", "mode=normal", "ttl_seconds=0"])  # 新增代码+Phase98UniversalComputerUseMode：断言缺 TTL 也使用安全默认值；如果没有这行代码，旧状态兼容性没有回归保护。
    # 新增代码+Phase98UniversalComputerUseMode：函数段结束，test_computer_status_renderer_bad_or_missing_ttl_defaults_to_zero 到此结束；如果没有这个边界说明，读者不容易看出坏 TTL 容错测试范围。

    def test_computer_permissions_show_task3_permission_fields(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 `/computer permissions` 显示 Task3 权限字段；如果没有这段测试，权限摘要可能缺少安全说明。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建临时 workspace；如果没有这行代码，permissions 测试会污染真实 mode 状态。
            workspace = Path(temp_dir)  # 新增代码+Phase98UniversalComputerUseMode：保存 workspace 路径供打开和查询共用；如果没有这行代码，permissions 可能读不到刚打开的模式。
            run_computer_terminal_command(workspace, "/computer use")  # 新增代码+Phase98UniversalComputerUseMode：先打开 normal mode；如果没有这行代码，权限输出只能显示默认 off 状态。
            output = run_computer_terminal_command(workspace, "/computer permissions")  # 新增代码+Phase98UniversalComputerUseMode：执行真实终端权限命令；如果没有这行代码，测试无法覆盖用户权限入口。
        self.assert_contains_all(output, ["Computer Use Permissions", "mode=normal", "full_mode=false", "per_app_allowlist_required=false", "high_risk_requires_confirmation=true", "dangerous_target_terms_hidden=true", "allowed_action_classes="])  # 新增代码+Phase98UniversalComputerUseMode：断言权限输出完整字段；如果没有这行代码，安全边界缺字段也会误通过。
    # 新增代码+Phase98UniversalComputerUseMode：函数段结束，test_computer_permissions_show_task3_permission_fields 到此结束；如果没有这个边界说明，读者不容易看出 permissions 测试范围。

    def test_computer_full_user_command_opens_full_without_dynamic_confirm_token(self) -> None:  # 修改代码+FullNaturalUserFlow：函数段开始，验证普通用户输入 `/computer use --full` 就直接打开 full；如果没有这段测试，项目会继续要求用户输入反直觉的动态 token 命令。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建临时 workspace；如果没有这行代码，full token 会污染真实状态。
            workspace = Path(temp_dir)  # 新增代码+Phase98UniversalComputerUseMode：保存 workspace 路径以复用同一 pending token；如果没有这行代码，confirm 会读不到 request 写入的 token。
            request_output = run_computer_terminal_command(workspace, "/computer use --full")  # 修改代码+FullNaturalUserFlow：执行真实用户会输入的一行 full 命令；如果没有这行代码，测试无法覆盖用户指出的自然入口。
        self.assert_contains_all(request_output, ["Computer Use Mode", "mode=full", "full_mode=true", "opened=true", "ttl_seconds=", "per_app_allowlist_required=false", "low_level_event_count=0"])  # 修改代码+FullNaturalUserFlow：断言一行命令直接进入 full 且仍不触发低层桌面事件；如果没有这行代码，token 流程或误触桌面都可能漏测。
        self.assertNotIn("confirmation_token=", request_output)  # 新增代码+FullNaturalUserFlow：断言普通用户输出不再暴露动态确认 token；如果没有这行代码，旧反直觉体验可能悄悄回归。
        self.assertNotIn("/computer use --full-confirm", request_output)  # 新增代码+FullNaturalUserFlow：断言普通用户输出不再要求输入 full-confirm 命令；如果没有这行代码，验收脚本可能继续模拟非真实用户习惯。
    # 修改代码+FullNaturalUserFlow：函数段结束，test_computer_full_user_command_opens_full_without_dynamic_confirm_token 到此结束；如果没有这个边界说明，读者不容易看出自然 full 命令测试范围。

    def test_computer_full_confirm_failures_show_decision(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 full-confirm 缺 token 或错 token 时输出可排查原因；如果没有这段测试，终端只会显示空 mode 导致用户不知道哪里错。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建临时 workspace；如果没有这行代码，失败 token 测试会污染真实 pending 状态。
            workspace = Path(temp_dir)  # 新增代码+Phase98UniversalComputerUseMode：保存同一 workspace 以复用 mode session store；如果没有这行代码，两个失败场景可能读写不同目录。
            missing_token_output = run_computer_terminal_command(workspace, "/computer use --full-confirm")  # 新增代码+Phase98UniversalComputerUseMode：执行缺 token 确认命令；如果没有这行代码，缺参诊断不会被测试覆盖。
            wrong_token_output = run_computer_terminal_command(workspace, "/computer use --full-confirm WRONG-TOKEN")  # 新增代码+Phase98UniversalComputerUseMode：执行错误 token 确认命令；如果没有这行代码，token mismatch 诊断不会被测试覆盖。
        self.assert_contains_all(missing_token_output, ["decision=full_mode_confirmation_token_mismatch", "opened=false", "full_mode=false", "low_level_event_count=0"])  # 新增代码+Phase98UniversalComputerUseMode：断言缺 token 输出明确 mismatch；如果没有这行代码，P2 诊断字段可能再次丢失。
        self.assert_contains_all(wrong_token_output, ["decision=full_mode_confirmation_token_mismatch", "opened=false", "full_mode=false", "low_level_event_count=0"])  # 新增代码+Phase98UniversalComputerUseMode：断言错 token 输出明确 mismatch；如果没有这行代码，用户排查 full-confirm 失败会没有原因码。
    # 新增代码+Phase98UniversalComputerUseMode：函数段结束，test_computer_full_confirm_failures_show_decision 到此结束；如果没有这个边界说明，读者不容易看出 full-confirm 失败诊断测试范围。

    def test_unsupported_computer_help_lists_phase98_commands(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证未知 `/computer` 帮助列出 Phase98 命令；如果没有这段测试，用户输错后找不到新入口。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建临时 workspace；如果没有这行代码，帮助命令也会初始化真实状态目录。
            output = run_computer_terminal_command(Path(temp_dir), "/computer unknown-phase98-command")  # 新增代码+Phase98UniversalComputerUseMode：执行未知命令触发帮助；如果没有这行代码，测试无法覆盖 unsupported 分支。
        self.assert_contains_all(output, ["/computer use", "/computer use --observe", "/computer use --full", "/computer stop", "/computer permissions"])  # 新增代码+Phase98UniversalComputerUseMode：断言帮助包含 Task3 新命令；如果没有这行代码，帮助文本遗漏也会溜走。
    # 新增代码+Phase98UniversalComputerUseMode：函数段结束，test_unsupported_computer_help_lists_phase98_commands 到此结束；如果没有这个边界说明，读者不容易看出帮助文本测试范围。


if __name__ == "__main__":  # 新增代码+Phase98UniversalComputerUseMode：文件入口段开始，允许直接运行本测试文件；如果没有这行代码，新手只能记住完整 unittest 模块命令。
    unittest.main()  # 新增代码+Phase98UniversalComputerUseMode：启动 unittest；如果没有这行代码，直接运行文件不会执行任何测试。
