import unittest  # 新增代码+Phase20ComputerUse: 引入 unittest 测试框架；如果没有这行代码，本文件无法定义和运行测试用例。

from learning_agent.computer_use.controller import ComputerUseController, MemoryComputerUseBackend, build_default_computer_use_backend  # 新增代码+Phase20ComputerUse: 导入 Computer Use 控制器、内存后端和默认后端工厂；如果没有这行代码，测试无法覆盖生产安全边界。


class OsComputerUsePhase20Tests(unittest.TestCase):  # 新增代码+Phase20ComputerUse: 定义 Phase 20 的 Computer Use 生产化测试集合；如果没有这个类，unittest 不会发现本阶段测试。
    def test_default_backend_status_explains_opt_in_gate(self) -> None:  # 新增代码+Phase20ComputerUse: 验证默认后端会解释为什么真实 OS 控制不可用；如果没有这个测试，状态输出可能只说失败但不给用户下一步。
        backend = build_default_computer_use_backend(environ={})  # 新增代码+Phase20ComputerUse: 用空环境变量构造默认后端；如果没有这行代码，测试可能受到真实机器环境变量污染。
        status = backend.status()  # 新增代码+Phase20ComputerUse: 读取默认后端状态；如果没有这行代码，无法断言状态字段。

        self.assertFalse(status["available"])  # 新增代码+Phase20ComputerUse: 断言默认真实 OS 控制不可用；如果没有这行代码，默认安全关闭可能被误改。
        self.assertFalse(status["real_actions_enabled"])  # 新增代码+Phase20ComputerUse: 断言真实鼠标键盘动作默认未启用；如果没有这行代码，用户无法确认不会误动桌面。
        self.assertEqual(status["opt_in_env_var"], "LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE")  # 新增代码+Phase20ComputerUse: 断言状态里明确写出启用环境变量；如果没有这行代码，用户不知道怎样安全开启。
        self.assertIn("未设置", status["reason"])  # 新增代码+Phase20ComputerUse: 断言原因解释环境变量未设置；如果没有这行代码，状态提示不够可操作。

    def test_controller_records_denied_action_in_audit_log(self) -> None:  # 新增代码+Phase20ComputerUse: 验证被拒绝的桌面动作也会进入审计记录；如果没有这个测试，安全拒绝发生后无法复盘。
        controller = ComputerUseController(backend=MemoryComputerUseBackend())  # 新增代码+Phase20ComputerUse: 使用内存后端避免真实桌面副作用；如果没有这行代码，测试可能触碰真实鼠标键盘。
        result = controller.execute({"action": "click"})  # 新增代码+Phase20ComputerUse: 故意缺少 confirm_desktop_control 触发拒绝；如果没有这行代码，无法验证拒绝审计。
        status = controller.status()  # 新增代码+Phase20ComputerUse: 读取控制器状态以检查审计摘要；如果没有这行代码，无法确认拒绝事件被记录。

        self.assertFalse(result.ok)  # 新增代码+Phase20ComputerUse: 断言未确认动作被拒绝；如果没有这行代码，危险动作可能绕过确认。
        self.assertEqual(result.data["audit_id"], "computer-audit-1")  # 新增代码+Phase20ComputerUse: 断言拒绝结果也携带审计 id；如果没有这行代码，工具返回和审计日志无法关联。
        self.assertEqual(status["audit"]["event_count"], 1)  # 新增代码+Phase20ComputerUse: 断言审计计数增加；如果没有这行代码，状态页看不到最近发生过拒绝。
        self.assertFalse(status["audit"]["last_event"]["allowed"])  # 新增代码+Phase20ComputerUse: 断言最后事件标记为未允许；如果没有这行代码，用户可能误以为动作已执行。
        self.assertIn("confirm_desktop_control", status["audit"]["last_event"]["reason"])  # 新增代码+Phase20ComputerUse: 断言审计原因包含缺少确认；如果没有这行代码，排查时不知道为何被拒绝。

    def test_confirmed_memory_screenshot_returns_audit_and_evidence(self) -> None:  # 新增代码+Phase20ComputerUse: 验证确认后的安全截图动作带审计和证据字段；如果没有这个测试，Phase 20 的可观测证据链不完整。
        controller = ComputerUseController(backend=MemoryComputerUseBackend())  # 新增代码+Phase20ComputerUse: 使用不会触碰真实桌面的内存后端；如果没有这行代码，测试无法安全执行 screenshot。
        result = controller.execute({"action": "screenshot", "confirm_desktop_control": True})  # 新增代码+Phase20ComputerUse: 执行已确认的 screenshot 动作；如果没有这行代码，无法验证成功路径证据。

        self.assertTrue(result.ok)  # 新增代码+Phase20ComputerUse: 断言内存后端确认动作成功；如果没有这行代码，成功路径坏掉不会被发现。
        self.assertEqual(result.data["audit_id"], "computer-audit-1")  # 新增代码+Phase20ComputerUse: 断言成功结果带审计 id；如果没有这行代码，模型无法把动作结果关联到审计事件。
        self.assertEqual(result.data["evidence"]["kind"], "screenshot")  # 新增代码+Phase20ComputerUse: 断言结果包含截图证据类型；如果没有这行代码，用户看不到这是一次屏幕观察证据。
        self.assertEqual(result.data["evidence"]["backend"], "memory")  # 新增代码+Phase20ComputerUse: 断言证据说明来自内存后端而非真实桌面；如果没有这行代码，测试证据可能被误解成真实截图。
        self.assertTrue(controller.status()["audit"]["last_event"]["allowed"])  # 新增代码+Phase20ComputerUse: 断言状态里的最后事件为允许执行；如果没有这行代码，状态摘要可能和执行结果不一致。


if __name__ == "__main__":  # 新增代码+Phase20ComputerUse: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase20ComputerUse: 启动 unittest 主函数；如果没有这行代码，直接运行文件不会执行任何测试。
