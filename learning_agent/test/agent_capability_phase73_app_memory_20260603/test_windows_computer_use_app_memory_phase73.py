import json  # 新增代码+Phase73AppMemory: 导入 JSON 用于检查状态文件没有落入秘密；如果没有这行代码，测试无法可靠扫描持久化内容。
import tempfile  # 新增代码+Phase73AppMemory: 导入临时目录隔离 app memory 状态；如果没有这行代码，测试会污染真实用户记忆。
import unittest  # 新增代码+Phase73AppMemory: 导入 unittest 承载 Phase73 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase73AppMemory: 导入 Path 管理 Windows 路径；如果没有这行代码，临时状态和场景路径更容易拼错。

from learning_agent.computer_use.app_memory import PHASE73_ACTIONS_EXPANDED, PHASE73_APP_MEMORY_MARKER, PHASE73_APP_MEMORY_OK_TOKEN, WindowsComputerUseAppMemoryStore, phase73_cli_line, run_phase73_app_memory_contract  # 新增代码+Phase73AppMemory: 导入预期 Phase73 app memory 入口；如果没有这行代码，红灯会证明生产模块尚未实现。


class WindowsComputerUseAppMemoryPhase73Tests(unittest.TestCase):  # 新增代码+Phase73AppMemory: 类段开始，集中验证非敏感 app memory、拒绝秘密、拒绝脚本和撤销；如果没有这个类，Phase73 没有自动化门禁。
    def test_safe_app_hints_are_persisted_and_reloaded(self) -> None:  # 新增代码+Phase73AppMemory: 函数段开始，验证安全应用提示会落盘并可重载；如果没有这个测试，memory 可能只存在内存里。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase73AppMemory: 使用临时目录隔离状态；如果没有这行代码，测试会修改真实 app memory。
            store = WindowsComputerUseAppMemoryStore(base_dir=Path(temp_dir))  # 新增代码+Phase73AppMemory: 创建隔离 app memory store；如果没有这行代码，无法记录提示。
            window_class = store.remember_app_hint("notepad.exe", "window_class", "Notepad", source="phase73 unit", confidence=0.9)  # 新增代码+Phase73AppMemory: 写入安全窗口类提示；如果没有这行代码，window_class 持久化没有正例。
            role_hint = store.remember_app_hint("notepad.exe", "role_hint", "main editor role is Edit", source="phase73 unit", confidence=0.8)  # 新增代码+Phase73AppMemory: 写入安全角色提示；如果没有这行代码，role_hint 持久化没有正例。
            control_name = store.remember_app_hint("notepad.exe", "safe_control_name", "File name", source="phase73 unit", confidence=0.85)  # 新增代码+Phase73AppMemory: 写入安全控件名；如果没有这行代码，控件提示持久化没有正例。
            menu_label = store.remember_app_hint("notepad.exe", "menu_label", "File", source="phase73 unit", confidence=0.95)  # 新增代码+Phase73AppMemory: 写入安全菜单标签；如果没有这行代码，菜单提示持久化没有正例。
            strategy = store.remember_app_hint("notepad.exe", "last_successful_strategy", "Open File menu, choose Save As, then use standard dialog controls.", source="phase73 unit", confidence=0.7)  # 新增代码+Phase73AppMemory: 写入非敏感成功策略；如果没有这行代码，自学习提示没有正例。
            reloaded = WindowsComputerUseAppMemoryStore(base_dir=Path(temp_dir))  # 新增代码+Phase73AppMemory: 用新 store 重新读取磁盘状态；如果没有这行代码，无法证明已经落盘。
            hints = reloaded.list_app_hints("notepad.exe")  # 新增代码+Phase73AppMemory: 列出 notepad 安全提示；如果没有这行代码，测试无法检查状态内容。
            self.assertTrue(window_class["remembered"])  # 新增代码+Phase73AppMemory: 断言窗口类提示已记录；如果没有这行代码，失败写入不会暴露。
            self.assertTrue(role_hint["remembered"])  # 新增代码+Phase73AppMemory: 断言角色提示已记录；如果没有这行代码，role_hint 可能没有被支持。
            self.assertTrue(control_name["remembered"])  # 新增代码+Phase73AppMemory: 断言控件名已记录；如果没有这行代码，控制提示可能没有被支持。
            self.assertTrue(menu_label["remembered"])  # 新增代码+Phase73AppMemory: 断言菜单标签已记录；如果没有这行代码，菜单提示可能丢失。
            self.assertTrue(strategy["remembered"])  # 新增代码+Phase73AppMemory: 断言非敏感策略已记录；如果没有这行代码，自学习提示可能不可用。
            self.assertEqual(len(hints["hints"]), 5)  # 新增代码+Phase73AppMemory: 断言重载后仍有五条提示；如果没有这行代码，落盘或读取可能遗漏。
            self.assertEqual({hint["hint_type"] for hint in hints["hints"]}, {"window_class", "role_hint", "safe_control_name", "menu_label", "last_successful_strategy"})  # 新增代码+Phase73AppMemory: 断言提示类型集合准确；如果没有这行代码，错误类型可能污染记忆。
            self.assertFalse(hints["actions_expanded"])  # 新增代码+Phase73AppMemory: 断言 memory 不扩大动作能力；如果没有这行代码，学习层可能被误读为执行层。
    # 新增代码+Phase73AppMemory: 函数段结束，test_safe_app_hints_are_persisted_and_reloaded 到此结束；如果没有这个边界说明，初学者不容易看出安全提示持久化范围。

    def test_secret_and_private_content_is_rejected_without_persisting_raw_text(self) -> None:  # 新增代码+Phase73AppMemory: 函数段开始，验证秘密和隐私文本不落盘；如果没有这个测试，memory 可能泄露密码、token 或支付信息。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase73AppMemory: 使用临时目录隔离状态；如果没有这行代码，测试会修改真实 app memory。
            store = WindowsComputerUseAppMemoryStore(base_dir=Path(temp_dir))  # 新增代码+Phase73AppMemory: 创建隔离 app memory store；如果没有这行代码，无法检查持久化文件。
            secret = store.remember_app_hint("chrome.exe", "safe_control_name", "password field value hunter2 api token sk-test-secret credit card 4111111111111111", source="phase73 unit", confidence=1.0)  # 新增代码+Phase73AppMemory: 尝试写入明显敏感内容；如果没有这行代码，秘密拒绝路径没有输入。
            state_text = store.state_path.read_text(encoding="utf-8") if store.state_path.exists() else ""  # 新增代码+Phase73AppMemory: 读取状态文件文本；如果没有这行代码，无法确认秘密没有落盘。
            audit_text = store.audit_path.read_text(encoding="utf-8") if store.audit_path.exists() else ""  # 新增代码+Phase73AppMemory: 读取审计文件文本；如果没有这行代码，无法确认审计也没有泄露秘密。
            persisted_text = state_text + audit_text  # 新增代码+Phase73AppMemory: 合并所有持久化文本；如果没有这行代码，检查状态和审计会重复。
            self.assertFalse(secret["remembered"])  # 新增代码+Phase73AppMemory: 断言敏感提示未记录；如果没有这行代码，秘密泄露不会被发现。
            self.assertEqual(secret["decision"], "secret_or_private_content_rejected")  # 新增代码+Phase73AppMemory: 断言拒绝原因稳定；如果没有这行代码，用户不知道为什么不能记。
            self.assertEqual(store.list_app_hints("chrome.exe")["hints"], [])  # 新增代码+Phase73AppMemory: 断言 chrome 没有任何提示；如果没有这行代码，秘密可能部分落盘。
            self.assertNotIn("hunter2", persisted_text)  # 新增代码+Phase73AppMemory: 断言密码样本未落盘；如果没有这行代码，最危险泄露可能漏检。
            self.assertNotIn("sk-test-secret", persisted_text)  # 新增代码+Phase73AppMemory: 断言 token 样本未落盘；如果没有这行代码，API token 泄露可能漏检。
            self.assertNotIn("4111111111111111", persisted_text)  # 新增代码+Phase73AppMemory: 断言支付卡号样本未落盘；如果没有这行代码，支付信息泄露可能漏检。
    # 新增代码+Phase73AppMemory: 函数段结束，test_secret_and_private_content_is_rejected_without_persisting_raw_text 到此结束；如果没有这个边界说明，初学者不容易看出隐私拒绝范围。

    def test_memory_assists_but_does_not_store_scripts_or_terminal_commands(self) -> None:  # 新增代码+Phase73AppMemory: 函数段开始，验证 app memory 不是脚本仓库或终端命令历史；如果没有这个测试，学习层可能变成危险自动执行脚本。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase73AppMemory: 使用临时目录隔离状态；如果没有这行代码，测试会污染真实 memory。
            store = WindowsComputerUseAppMemoryStore(base_dir=Path(temp_dir))  # 新增代码+Phase73AppMemory: 创建隔离 app memory store；如果没有这行代码，脚本拒绝没有持久化对象。
            script_type = store.remember_app_hint("notepad.exe", "script", "click 10 10; type secret; save file", source="phase73 unit", confidence=0.5)  # 新增代码+Phase73AppMemory: 尝试用 script 类型写入脚本；如果没有这行代码，unsupported 类型拒绝没有输入。
            command_value = store.remember_app_hint("notepad.exe", "last_successful_strategy", "powershell.exe -NoProfile -Command Remove-Item C:\\important -Recurse", source="phase73 unit", confidence=0.5)  # 新增代码+Phase73AppMemory: 尝试把终端命令伪装成策略；如果没有这行代码，命令内容拒绝没有输入。
            safe_strategy = store.remember_app_hint("notepad.exe", "last_successful_strategy", "Use menu labels and visible dialog roles; never replay terminal commands.", source="phase73 unit", confidence=0.6)  # 新增代码+Phase73AppMemory: 写入安全辅助策略；如果没有这行代码，测试无法区分辅助提示和脚本。
            persisted = json.dumps(store.status(), ensure_ascii=False)  # 新增代码+Phase73AppMemory: 序列化状态用于扫描脚本内容；如果没有这行代码，脚本落盘风险无法检查。
            self.assertFalse(script_type["remembered"])  # 新增代码+Phase73AppMemory: 断言 script 类型被拒绝；如果没有这行代码，脚本仓库风险不会暴露。
            self.assertEqual(script_type["decision"], "unsupported_hint_type")  # 新增代码+Phase73AppMemory: 断言不支持脚本类型；如果没有这行代码，错误原因可能漂移。
            self.assertFalse(command_value["remembered"])  # 新增代码+Phase73AppMemory: 断言终端命令值被拒绝；如果没有这行代码，危险命令可能被记住。
            self.assertEqual(command_value["decision"], "terminal_command_rejected")  # 新增代码+Phase73AppMemory: 断言命令拒绝原因稳定；如果没有这行代码，审计无法区分命令和秘密。
            self.assertTrue(safe_strategy["remembered"])  # 新增代码+Phase73AppMemory: 断言安全辅助策略仍能记录；如果没有这行代码，memory 可能过度拒绝而失去用途。
            self.assertNotIn("Remove-Item", persisted)  # 新增代码+Phase73AppMemory: 断言危险命令未进入状态；如果没有这行代码，命令文本可能在状态里泄露。
            self.assertNotIn("click 10 10", persisted)  # 新增代码+Phase73AppMemory: 断言脚本动作未进入状态；如果没有这行代码，脚本录制风险可能漏检。
    # 新增代码+Phase73AppMemory: 函数段结束，test_memory_assists_but_does_not_store_scripts_or_terminal_commands 到此结束；如果没有这个边界说明，初学者不容易看出非脚本边界。

    def test_revoke_app_memory_removes_only_target_app(self) -> None:  # 新增代码+Phase73AppMemory: 函数段开始，验证按 app 撤销 memory；如果没有这个测试，用户无法清除某个应用的学习痕迹。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase73AppMemory: 使用临时目录隔离状态；如果没有这行代码，撤销测试会影响真实 memory。
            store = WindowsComputerUseAppMemoryStore(base_dir=Path(temp_dir))  # 新增代码+Phase73AppMemory: 创建隔离 app memory store；如果没有这行代码，无法写入和撤销提示。
            store.remember_app_hint("notepad.exe", "menu_label", "File", source="phase73 unit", confidence=0.9)  # 新增代码+Phase73AppMemory: 写入 notepad 提示；如果没有这行代码，撤销目标没有数据。
            store.remember_app_hint("mspaint.exe", "menu_label", "Brushes", source="phase73 unit", confidence=0.9)  # 新增代码+Phase73AppMemory: 写入 paint 提示作为隔离反例；如果没有这行代码，无法证明撤销不误伤其他 app。
            revoke = store.revoke_app_memory("notepad.exe")  # 新增代码+Phase73AppMemory: 撤销 notepad 的 memory；如果没有这行代码，memory_can_be_revoked 没有动作。
            notepad_hints = store.list_app_hints("notepad.exe")  # 新增代码+Phase73AppMemory: 读取撤销后的 notepad；如果没有这行代码，无法确认撤销效果。
            paint_hints = store.list_app_hints("mspaint.exe")  # 新增代码+Phase73AppMemory: 读取 paint 作为未撤销 app；如果没有这行代码，无法确认隔离。
            self.assertTrue(revoke["revoked"])  # 新增代码+Phase73AppMemory: 断言撤销成功；如果没有这行代码，失败撤销也可能被忽略。
            self.assertEqual(revoke["revoked_count"], 1)  # 新增代码+Phase73AppMemory: 断言只撤销一条 notepad 记忆；如果没有这行代码，撤销数量可能不准确。
            self.assertEqual(notepad_hints["hints"], [])  # 新增代码+Phase73AppMemory: 断言目标 app 已无有效提示；如果没有这行代码，撤销可能只写审计不改状态。
            self.assertEqual(len(paint_hints["hints"]), 1)  # 新增代码+Phase73AppMemory: 断言其他 app 未被误删；如果没有这行代码，撤销可能破坏全局 memory。
    # 新增代码+Phase73AppMemory: 函数段结束，test_revoke_app_memory_removes_only_target_app 到此结束；如果没有这个边界说明，初学者不容易看出撤销范围。

    def test_phase73_cli_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase73AppMemory: 函数段开始，验证 CLI 和真实终端场景 token 稳定；如果没有这个测试，验收器可能漏检 memory 边界。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase73AppMemory: 使用临时目录隔离合同状态；如果没有这行代码，合同会读写真实 memory。
            report = run_phase73_app_memory_contract(base_dir=Path(temp_dir))  # 新增代码+Phase73AppMemory: 运行 Phase73 合同自检；如果没有这行代码，CLI token 没有结构化来源。
        cli_line = phase73_cli_line(report)  # 新增代码+Phase73AppMemory: 生成稳定 CLI 行；如果没有这行代码，场景匹配无法验证。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase73_app_memory.json")  # 新增代码+Phase73AppMemory: 定位 Phase73 真实终端场景；如果没有这行代码，场景缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase73AppMemory: 读取场景文本；如果没有这行代码，token 漏配无法检测。
        expected_tokens = {PHASE73_APP_MEMORY_MARKER, PHASE73_APP_MEMORY_OK_TOKEN, "app_memory=true", "non_secret_memory=true", "memory_assists_not_scripts=true", "memory_can_be_revoked=true", "actions_expanded=false"}  # 新增代码+Phase73AppMemory: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        self.assertTrue(report["app_memory"])  # 新增代码+Phase73AppMemory: 断言 app memory 正常工作；如果没有这行代码，核心功能失败可能只靠字符串掩盖。
        self.assertTrue(report["non_secret_memory"])  # 新增代码+Phase73AppMemory: 断言只记非敏感信息；如果没有这行代码，隐私边界无法验收。
        self.assertTrue(report["memory_assists_not_scripts"])  # 新增代码+Phase73AppMemory: 断言记忆不是脚本仓库；如果没有这行代码，脚本录制风险无法验收。
        self.assertTrue(report["memory_can_be_revoked"])  # 新增代码+Phase73AppMemory: 断言 memory 可撤销；如果没有这行代码，用户无法清理学习痕迹。
        self.assertFalse(report["actions_expanded"])  # 新增代码+Phase73AppMemory: 断言 Phase73 不扩大动作能力；如果没有这行代码，学习层可能被误读成执行层。
        self.assertFalse(PHASE73_ACTIONS_EXPANDED)  # 新增代码+Phase73AppMemory: 断言模块常量同样不扩大动作；如果没有这行代码，报告和模块声明可能不一致。
        for token in expected_tokens:  # 新增代码+Phase73AppMemory: 遍历关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase73AppMemory: 断言 CLI 包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase73AppMemory: 断言场景包含 token；如果没有这行代码，真实终端验收可能漏检。
    # 新增代码+Phase73AppMemory: 函数段结束，test_phase73_cli_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 场景测试范围。
# 新增代码+Phase73AppMemory: 类段结束，WindowsComputerUseAppMemoryPhase73Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase73AppMemory: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase73AppMemory: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
