"""Stage 15 高层浏览器工具测试。"""  # 新增代码+Phase3HighLevelTools: 说明本文件锁定批量填表和快捷键入口；若没有这行代码，维护者不知道这些测试保护什么能力。
from __future__ import annotations  # 新增代码+Phase3HighLevelTools: 让类型注解延迟解析；若没有这行代码，未来前向类型引用可能在导入时失败。
from learning_agent.tests.support import *  # 新增代码+Phase3HighLevelTools: 复用项目测试基类和临时目录工具；若没有这行代码，测试需要重复写公共导入。

class BrowserHighLevelToolsStage15Tests(LearningAgentTestBase):  # 新增代码+Phase3HighLevelTools: 定义 Stage 15 测试集合；若没有这个类，unittest 不会发现本阶段门禁。
    def test_high_level_tools_are_exposed_by_browser_server(self) -> None:  # 新增代码+Phase3HighLevelTools: 验证 MCP server 暴露高层工具；若没有这行代码，schema 缺口不会被发现。
        from learning_agent.browser_automation_mcp_server import TOOLS  # 新增代码+Phase3HighLevelTools: 读取真实工具清单；若没有这行代码，测试只会检查假数据。
        tool_names = {str(tool.get("name", "")) for tool in TOOLS}  # 新增代码+Phase3HighLevelTools: 收集所有工具名便于断言；若没有这行代码，后续无法快速检查目标工具。
        self.assertIn("browser_form_input", tool_names)  # 新增代码+Phase3HighLevelTools: 断言批量填表工具存在；若没有这行代码，模型仍需手动拼多个 type 调用。
        self.assertIn("browser_shortcuts_list", tool_names)  # 新增代码+Phase3HighLevelTools: 断言快捷键清单工具存在；若没有这行代码，模型不知道支持哪些常用快捷键。
        self.assertIn("browser_shortcuts_execute", tool_names)  # 新增代码+Phase3HighLevelTools: 断言快捷键执行工具存在；若没有这行代码，快捷键别名无法被用户自然调用。
    def test_form_input_plan_redacts_secret_and_preserves_order(self) -> None:  # 新增代码+Phase3HighLevelTools: 验证填表计划按顺序且不泄露秘密；若没有这行代码，批量输入可能乱序或回显敏感值。
        from learning_agent.browser.high_level_tools import build_form_input_plan  # 新增代码+Phase3HighLevelTools: 导入生产规划函数；若没有这行代码，测试无法驱动真实实现。
        plan = build_form_input_plan({"fields": [{"label": "邮箱", "text": "alice@example.com"}, {"label": "密码", "secret_env_var": "LEARNING_AGENT_SECRET_PASSWORD"}], "submit": True})  # 新增代码+Phase3HighLevelTools: 构造含普通字段、敏感字段和提交的表单任务；若没有这行代码，测试没有真实样本。
        self.assertEqual([step["tool_name"] for step in plan], ["browser_type", "browser_type_secret", "browser_press_key"])  # 新增代码+Phase3HighLevelTools: 断言底层动作顺序稳定；若没有这行代码，填表可能先提交再输入。
        self.assertEqual(plan[0]["arguments"]["label"], "邮箱")  # 新增代码+Phase3HighLevelTools: 断言普通字段保留定位标签；若没有这行代码，底层输入找不到目标框。
        self.assertEqual(plan[0]["arguments"]["text"], "alice@example.com")  # 新增代码+Phase3HighLevelTools: 断言普通文本传给 browser_type；若没有这行代码，非敏感字段不会输入。
        self.assertNotIn("text", plan[1]["arguments"])  # 新增代码+Phase3HighLevelTools: 断言敏感字段不生成明文 text；若没有这行代码，密码可能进入动作参数。
        self.assertEqual(plan[1]["arguments"]["secret_env_var"], "LEARNING_AGENT_SECRET_PASSWORD")  # 新增代码+Phase3HighLevelTools: 断言敏感字段只引用环境变量名；若没有这行代码，底层 secret 工具无法取值。
        self.assertEqual(plan[2]["arguments"]["key"], "Enter")  # 新增代码+Phase3HighLevelTools: 断言 submit 转成 Enter；若没有这行代码，表单不会提交。
    def test_shortcut_mapping_is_stable_and_rejects_unknown_names(self) -> None:  # 新增代码+Phase3HighLevelTools: 验证快捷键别名稳定且坏输入有边界；若没有这行代码，用户自然语言快捷键可能漂移。
        from learning_agent.browser.high_level_tools import browser_shortcut_key, format_shortcuts_list  # 新增代码+Phase3HighLevelTools: 导入快捷键 helper；若没有这行代码，测试无法覆盖真实映射。
        self.assertEqual(browser_shortcut_key("submit"), "Enter")  # 新增代码+Phase3HighLevelTools: 断言提交别名对应 Enter；若没有这行代码，表单提交快捷键可能改错。
        self.assertEqual(browser_shortcut_key("select_all"), "Control+A")  # 新增代码+Phase3HighLevelTools: 断言全选别名对应 Control+A；若没有这行代码，常用编辑动作不稳定。
        self.assertIn("submit=Enter", format_shortcuts_list())  # 新增代码+Phase3HighLevelTools: 断言清单包含机器可读映射；若没有这行代码，模型无法从列表结果解析快捷键。
        with self.assertRaises(ValueError):  # 新增代码+Phase3HighLevelTools: 进入未知快捷键错误断言；若没有这行代码，坏别名可能被静默忽略。
            browser_shortcut_key("unknown_shortcut")  # 新增代码+Phase3HighLevelTools: 传入不存在的快捷键；若没有这行代码，错误分支没有输入样本。
    def test_browser_server_form_input_reuses_low_level_methods(self) -> None:  # 新增代码+Phase3HighLevelTools: 验证 server 高层工具复用底层方法；若没有这行代码，高层入口可能绕过审计和脱敏。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+Phase3HighLevelTools: 导入真实 server；若没有这行代码，测试无法覆盖分发入口。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase3HighLevelTools: 使用临时目录隔离运行产物；若没有这行代码，测试会污染真实 workspace。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+Phase3HighLevelTools: 创建浏览器 server 实例；若没有这行代码，无法调用真实高层方法。
            calls: list[tuple[str, dict[str, Any]]] = []  # 新增代码+Phase3HighLevelTools: 准备记录底层方法调用；若没有这行代码，无法断言复用路径。
            server.browser_type = lambda arguments: calls.append(("browser_type", dict(arguments))) or "typed"  # 新增代码+Phase3HighLevelTools: 替换普通输入以避免启动浏览器；若没有这行代码，测试会依赖真实页面。
            server.browser_type_secret = lambda arguments: calls.append(("browser_type_secret", dict(arguments))) or "secret_typed"  # 新增代码+Phase3HighLevelTools: 替换敏感输入以避免读取真实环境变量；若没有这行代码，测试需要真实密码变量。
            server.browser_press_key = lambda arguments: calls.append(("browser_press_key", dict(arguments))) or "pressed"  # 新增代码+Phase3HighLevelTools: 替换按键方法以记录提交动作；若没有这行代码，测试会向真实页面发按键。
            result = server.call("browser_form_input", {"fields": [{"selector": "#q", "text": "hello"}, {"label": "密码", "secret_env_var": "LEARNING_AGENT_SECRET_PASSWORD"}], "submit": True})  # 新增代码+Phase3HighLevelTools: 通过真实 call 分发调用高层工具；若没有这行代码，分发器是否接线不可见。
        self.assertIn("browser_form_input 成功", result)  # 新增代码+Phase3HighLevelTools: 断言高层工具返回成功标题；若没有这行代码，调用方无法识别结果。
        self.assertEqual([name for name, _arguments in calls], ["browser_type", "browser_type_secret", "browser_press_key"])  # 新增代码+Phase3HighLevelTools: 断言底层调用顺序；若没有这行代码，高层复用可能错乱。
        self.assertEqual(calls[0][1]["selector"], "#q")  # 新增代码+Phase3HighLevelTools: 断言 selector 被透传到底层输入；若没有这行代码，批量填表无法定位输入框。
        self.assertEqual(calls[1][1]["secret_env_var"], "LEARNING_AGENT_SECRET_PASSWORD")  # 新增代码+Phase3HighLevelTools: 断言 secret_env_var 被透传；若没有这行代码，敏感输入无法执行。
