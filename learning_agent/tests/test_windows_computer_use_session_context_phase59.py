import tempfile  # 新增代码+Phase59SessionContextAppState: 导入临时目录用于隔离持久化状态；如果没有这行代码，测试会污染真实用户 session_state。
import unittest  # 新增代码+Phase59SessionContextAppState: 导入 unittest 承载 Phase59 自动化测试；如果没有这行代码，标准测试命令无法发现本阶段门禁。
from pathlib import Path  # 新增代码+Phase59SessionContextAppState: 导入 Path 读取验收场景文件；如果没有这行代码，Windows 路径拼接更容易出错。

from learning_agent.computer_use.session_context import PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER, PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_OK_TOKEN, ComputerUseSessionContextStore, phase59_cli_line, run_phase59_session_context_contract  # 新增代码+Phase59SessionContextAppState: 导入预期 Phase59 session context 入口；如果没有这行代码，红灯会证明生产模块尚未实现。


class WindowsComputerUseSessionContextPhase59Tests(unittest.TestCase):  # 新增代码+Phase59SessionContextAppState: 类段开始，集中验证 ClaudeCode 风格 session context/AppState；如果没有这个类，Phase59 没有自动化门禁。
    def test_context_persists_allowed_apps_grants_display_and_screenshot_dims(self) -> None:  # 新增代码+Phase59SessionContextAppState: 函数段开始，验证会话事实源能落盘并被新 store 读取；如果没有这个测试，多轮终端状态可能只停在内存。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase59SessionContextAppState: 使用临时目录隔离状态文件；如果没有这行代码，测试会改真实 memory。
            store = ComputerUseSessionContextStore(base_dir=Path(temp_dir))  # 新增代码+Phase59SessionContextAppState: 创建第一份 store；如果没有这行代码，无法写入 session context。
            context = store.bind_context("phase59-a", allowed_apps=["notepad.exe"], grant_flags={"desktopAction": True}, selected_display={"display_id": "DISPLAY1"}, last_screenshot_dims={"width": 1280, "height": 720})  # 新增代码+Phase59SessionContextAppState: 写入允许 app、grant、显示器和截图尺寸；如果没有这行代码，持久化字段没有输入。
            reloaded = ComputerUseSessionContextStore(base_dir=Path(temp_dir)).snapshot("phase59-a")  # 新增代码+Phase59SessionContextAppState: 用新 store 重新读取同一会话；如果没有这行代码，无法证明状态真的落盘。
            self.assertEqual(context["session_id"], "phase59-a")  # 新增代码+Phase59SessionContextAppState: 断言 session_id 保留；如果没有这行代码，会话身份漂移不被发现。
            self.assertIn("notepad.exe", reloaded["allowed_apps"])  # 新增代码+Phase59SessionContextAppState: 断言 allowed_apps 持久化；如果没有这行代码，授权事实可能丢失。
            self.assertTrue(reloaded["grant_flags"]["desktopAction"])  # 新增代码+Phase59SessionContextAppState: 断言 grant_flags 持久化；如果没有这行代码，动作权限可能跨轮丢失。
            self.assertEqual(reloaded["selected_display"]["display_id"], "DISPLAY1")  # 新增代码+Phase59SessionContextAppState: 断言显示器选择持久化；如果没有这行代码，多屏上下文可能丢失。
            self.assertEqual(reloaded["last_screenshot_dims"]["width"], 1280)  # 新增代码+Phase59SessionContextAppState: 断言截图宽度持久化；如果没有这行代码，工具无法复用截图尺寸事实。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，test_context_persists_allowed_apps_grants_display_and_screenshot_dims 到此结束；如果没有这个边界说明，初学者不容易看出持久化测试范围。

    def test_context_cleanup_and_multi_session_isolation(self) -> None:  # 新增代码+Phase59SessionContextAppState: 函数段开始，验证 cleanup 不污染其他 session；如果没有这个测试，并发 session 可能互相覆盖。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase59SessionContextAppState: 使用临时目录隔离状态文件；如果没有这行代码，测试会改真实 memory。
            store = ComputerUseSessionContextStore(base_dir=Path(temp_dir))  # 新增代码+Phase59SessionContextAppState: 创建 session context store；如果没有这行代码，无法写入两个 session。
            store.bind_context("phase59-a", allowed_apps=["app-a"], grant_flags={"desktopAction": True})  # 新增代码+Phase59SessionContextAppState: 写入 A 会话授权；如果没有这行代码，cleanup 没有被清理对象。
            store.bind_context("phase59-b", allowed_apps=["app-b"], grant_flags={"observe": True})  # 新增代码+Phase59SessionContextAppState: 写入 B 会话授权；如果没有这行代码，无法验证隔离。
            store.update_app_state("phase59-a", hidden_windows=[{"window_id": "hwnd:1"}], last_action={"action": "type_text"}, last_error={"code": "phase59-test"})  # 新增代码+Phase59SessionContextAppState: 写入 A 会话 AppState；如果没有这行代码，cleanup 字段没有变化输入。
            cleanup = store.cleanup_session("phase59-a", reason="phase59 cleanup")  # 新增代码+Phase59SessionContextAppState: 清理 A 会话；如果没有这行代码，cleanup_state 无法验证。
            session_a = store.snapshot("phase59-a")  # 新增代码+Phase59SessionContextAppState: 读取清理后的 A；如果没有这行代码，无法断言归零结果。
            session_b = store.snapshot("phase59-b")  # 新增代码+Phase59SessionContextAppState: 读取未清理的 B；如果没有这行代码，无法断言隔离。
            self.assertTrue(cleanup["cleanup_completed"])  # 新增代码+Phase59SessionContextAppState: 断言 cleanup 标记完成；如果没有这行代码，清理可能无声失败。
            self.assertEqual(session_a["allowed_apps"], [])  # 新增代码+Phase59SessionContextAppState: 断言 A 的 allowlist 已归零；如果没有这行代码，清理后权限可能残留。
            self.assertEqual(session_a["hidden_windows"], [])  # 新增代码+Phase59SessionContextAppState: 断言 A 的 hidden windows 已归零；如果没有这行代码，隐藏窗口状态可能残留。
            self.assertEqual(session_a["last_action"], {})  # 新增代码+Phase59SessionContextAppState: 断言 A 的 last_action 已清空；如果没有这行代码，旧动作可能误导状态 UI。
            self.assertIn("app-b", session_b["allowed_apps"])  # 新增代码+Phase59SessionContextAppState: 断言 B 会话不受 A cleanup 影响；如果没有这行代码，跨 session 污染不会暴露。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，test_context_cleanup_and_multi_session_isolation 到此结束；如果没有这个边界说明，初学者不容易看出隔离测试范围。

    def test_phase59_cli_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase59SessionContextAppState: 函数段开始，验证 CLI token 和真实终端场景保持一致；如果没有这个测试，controller 可能漏检关键状态。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase59SessionContextAppState: 使用临时目录避免合同污染真实状态；如果没有这行代码，单测会写默认 memory。
            report = run_phase59_session_context_contract(base_dir=Path(temp_dir))  # 新增代码+Phase59SessionContextAppState: 运行 Phase59 合同自检；如果没有这行代码，CLI 行没有报告来源。
        cli_line = phase59_cli_line(report)  # 新增代码+Phase59SessionContextAppState: 生成稳定 token 行；如果没有这行代码，无法比对场景断言。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase59_session_context_appstate.json")  # 新增代码+Phase59SessionContextAppState: 定位 Phase59 真实终端场景；如果没有这行代码，场景缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase59SessionContextAppState: 读取场景文本；如果没有这行代码，token 漏配无法检测。
        expected_tokens = {PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_MARKER, PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_OK_TOKEN, "context_persisted=true", "multi_session_isolated=true", "cleanup_state=true", "status_readable=true", "actions_expanded=false"}  # 新增代码+Phase59SessionContextAppState: 定义 CLI 和场景都必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase59SessionContextAppState: 遍历每个稳定 token；如果没有这行代码，断言会重复且易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase59SessionContextAppState: 断言 CLI 包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase59SessionContextAppState: 断言场景包含 token；如果没有这行代码，真实终端验收可能漏检。
    # 新增代码+Phase59SessionContextAppState: 函数段结束，test_phase59_cli_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 场景测试范围。
# 新增代码+Phase59SessionContextAppState: 类段结束，WindowsComputerUseSessionContextPhase59Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase59SessionContextAppState: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase59SessionContextAppState: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
