"Browser runtime alignment tests for recovery, vision, replay, and safety."  # 新增代码+BrowserRuntime对齐测试: 说明本文件专门锁定真实浏览器运行层缺口；若没有这行代码，维护者不知道这些测试服务于 ClaudeCode 对齐任务。
from __future__ import annotations  # 新增代码+BrowserRuntime对齐测试: 延迟解析类型注解；若没有这行代码，测试里的前向注解在旧运行方式下可能更脆弱。
from learning_agent.tests.support import *  # 新增代码+BrowserRuntime对齐测试: 复用项目测试根目录、临时目录和断言工具；若没有这行代码，测试会重复大量公共准备逻辑。


class FakeRuntimeMouse:  # 新增代码+BrowserRuntime对齐测试: 定义假鼠标来观察坐标点击；若没有这行代码，测试只能启动真实浏览器才能知道是否点击坐标。
    def __init__(self) -> None:  # 新增代码+BrowserRuntime对齐测试: 初始化假鼠标状态；若没有这行代码，点击记录没有保存位置。
        self.clicks: list[tuple[int, int]] = []  # 新增代码+BrowserRuntime对齐测试: 保存所有坐标点击；若没有这行代码，断言无法确认点击位置。

    def click(self, x: int, y: int) -> None:  # 新增代码+BrowserRuntime对齐测试: 模拟 Playwright mouse.click 接口；若没有这行代码，browser_click 坐标分支会因为假对象缺方法失败。
        self.clicks.append((x, y))  # 新增代码+BrowserRuntime对齐测试: 记录点击坐标；若没有这行代码，测试无法判断实现是否真的使用坐标。


class FakeRuntimePage:  # 新增代码+BrowserRuntime对齐测试: 定义假页面来避免测试依赖真实浏览器；若没有这行代码，恢复和视觉测试会变成不稳定集成测试。
    def __init__(self, url: str = "https://example.com/") -> None:  # 新增代码+BrowserRuntime对齐测试: 初始化假页面 URL；若没有这行代码，返回摘要没有页面地址。
        self.url = url  # 新增代码+BrowserRuntime对齐测试: 保存当前 URL；若没有这行代码，browser_click 和 recover 返回值会缺少地址。
        self.mouse = FakeRuntimeMouse()  # 新增代码+BrowserRuntime对齐测试: 给页面挂假鼠标；若没有这行代码，坐标点击无法被记录。
        self.reload_count = 0  # 新增代码+BrowserRuntime对齐测试: 保存 reload 调用次数；若没有这行代码，恢复测试无法确认 reload 真执行。
        self.closed = False  # 新增代码+BrowserRuntime对齐测试: 保存页面关闭状态；若没有这行代码，current_page 无法判断页面是否可用。

    def is_closed(self) -> bool:  # 新增代码+BrowserRuntime对齐测试: 模拟 Playwright Page.is_closed；若没有这行代码，server.current_page 会把假页面当坏对象。
        return self.closed  # 新增代码+BrowserRuntime对齐测试: 返回当前关闭状态；若没有这行代码，关闭状态无法被测试控制。

    def reload(self, wait_until: str, timeout: int) -> None:  # 新增代码+BrowserRuntime对齐测试: 模拟页面 reload；若没有这行代码，browser_recover_page 的 reload 分支无法测试。
        del wait_until  # 新增代码+BrowserRuntime对齐测试: 明确假页面不关心等待状态；若没有这行代码，读者可能误以为测试验证了真实加载状态。
        del timeout  # 新增代码+BrowserRuntime对齐测试: 明确假页面不关心超时值；若没有这行代码，未使用参数意图不清楚。
        self.reload_count += 1  # 新增代码+BrowserRuntime对齐测试: 记录 reload 次数；若没有这行代码，恢复动作无法被断言。

    def title(self) -> str:  # 新增代码+BrowserRuntime对齐测试: 模拟页面标题读取；若没有这行代码，部分返回摘要会因为假页面缺 title 失败。
        return "Example"  # 新增代码+BrowserRuntime对齐测试: 返回固定标题；若没有这行代码，测试结果会依赖真实页面。


class BrowserRuntimeAlignmentTests(LearningAgentTestBase):  # 新增代码+BrowserRuntime对齐测试: 定义浏览器运行层对齐测试类；若没有这行代码，unittest 不会发现本组测试。
    def test_browser_tools_expose_recovery_visual_flow_replay_plugin_and_site_grant(self) -> None:  # 新增代码+BrowserRuntime对齐测试: 验证 MCP 工具清单暴露本轮核心能力；若没有这行代码，后续可能只实现内部函数却不给 agent 使用。
        from learning_agent.browser_automation_mcp_server import TOOLS  # 新增代码+BrowserRuntime对齐测试: 导入真实 MCP 工具清单；若没有这行代码，测试无法覆盖 tools/list 的事实来源。
        tool_names = {tool["name"] for tool in TOOLS}  # 新增代码+BrowserRuntime对齐测试: 提取所有工具名；若没有这行代码，逐个断言会重复遍历列表。
        expected_tools = {"browser_launch_visible", "browser_recover_page", "browser_visual_locate", "browser_flow_run", "browser_replay", "browser_plugin_status", "browser_site_grant", "browser_type_secret"}  # 修改代码+SecretInput: 固定可见浏览器、运行层和敏感输入工具；若没有这行代码，密码脱敏输入入口缺失不会被测试发现。
        for expected_tool in expected_tools:  # 新增代码+BrowserRuntime对齐测试: 遍历每个期望工具；若没有这行代码，只能写重复断言。
            self.assertIn(expected_tool, tool_names)  # 新增代码+BrowserRuntime对齐测试: 断言工具已公开给 agent；若没有这行代码，工具缺失不会报红。
        flow_tool = next(tool for tool in TOOLS if tool["name"] == "browser_flow_run")  # 新增代码+BrowserRuntime对齐测试: 找到复杂流程工具 schema；若没有这行代码，无法验证 OpenAI 严格 JSON schema。
        stages_schema = flow_tool["inputSchema"]["properties"]["stages"]  # 新增代码+BrowserRuntime对齐测试: 读取 stages 数组字段；若没有这行代码，断言会写成脆弱长表达式。
        self.assertIn("items", stages_schema)  # 新增代码+BrowserRuntime对齐测试: 断言 array schema 必须声明 items；若没有这行代码，真实终端会再次出现 invalid_json_schema。

    def test_browser_launch_visible_requires_explicit_confirmation(self) -> None:  # 新增代码+VisibleBrowser验收: 验证可见浏览器启动必须用户显式确认；若没有这行代码，agent 可能静默弹出本地浏览器窗口。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+VisibleBrowser验收: 导入被测 server；若没有这行代码，测试无法调用可见浏览器工具。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+VisibleBrowser验收: 使用临时工作区隔离动作日志；若没有这行代码，失败日志会污染真实项目。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+VisibleBrowser验收: 创建隔离 server；若没有这行代码，无法验证确认边界。
            with self.assertRaisesRegex(RuntimeError, "confirm_visible_browser"):  # 新增代码+VisibleBrowser验收: 断言缺少确认会被拒绝；若没有这行代码，确认门禁可能失效。
                server.call("browser_launch_visible", {})  # 新增代码+VisibleBrowser验收: 故意不传确认参数；若没有这行代码，测试不会触发安全拒绝路径。

    def test_browser_launch_visible_switches_independent_browser_to_headed_mode(self) -> None:  # 新增代码+VisibleBrowser验收: 验证确认后会切换到可见浏览器模式；若没有这行代码，工具可能只返回文本不改变启动方式。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+VisibleBrowser验收: 导入被测 server；若没有这行代码，测试没有运行时对象。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+VisibleBrowser验收: 使用临时工作区隔离状态；若没有这行代码，测试可能污染真实 browser_artifacts。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+VisibleBrowser验收: 创建隔离 server；若没有这行代码，无法替换启动函数。
            calls = {"ensure": 0}  # 新增代码+VisibleBrowser验收: 保存 ensure_browser 调用次数；若没有这行代码，无法证明工具尝试启动浏览器。
            def fake_ensure_browser() -> None:  # 新增代码+VisibleBrowser验收: 用假启动函数避免测试真的弹浏览器；若没有这行代码，单元测试会依赖桌面环境。
                calls["ensure"] += 1  # 新增代码+VisibleBrowser验收: 记录启动尝试；若没有这行代码，断言无法知道工具是否执行启动流程。
            server.ensure_browser = fake_ensure_browser  # 新增代码+VisibleBrowser验收: 替换真实启动函数；若没有这行代码，测试会打开真实浏览器。
            result = server.call("browser_launch_visible", {"confirm_visible_browser": True})  # 新增代码+VisibleBrowser验收: 显式确认启动可见浏览器；若没有这行代码，测试没有行为来源。
        self.assertFalse(server.launch_headless)  # 新增代码+VisibleBrowser验收: 断言后续 browser_open 会使用 headless=false；若没有这行代码，可见模式可能没有真正生效。
        self.assertEqual(calls["ensure"], 1)  # 新增代码+VisibleBrowser验收: 断言启动流程被调用一次；若没有这行代码，工具可能没有启动浏览器。
        self.assertIn("browser_launch_visible 成功", result)  # 新增代码+VisibleBrowser验收: 断言返回成功标题；若没有这行代码，调用方难以识别结果来源。
        self.assertIn("visible_browser=true", result)  # 新增代码+VisibleBrowser验收: 断言返回机器可读可见状态；若没有这行代码，真实终端验收无法稳定检查可见模式。
        self.assertIn("headless=false", result)  # 新增代码+VisibleBrowser验收: 断言返回机器可读 headless 状态；若没有这行代码，验收无法证明不是 headless。

    def test_browser_type_secret_reads_env_without_leaking_value(self) -> None:  # 新增代码+SecretInput: 验证敏感输入从环境变量读取且不会回显；若没有这行代码，登录密码可能重新进入日志。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+SecretInput: 导入被测 server；若没有这行代码，测试无法调用新增工具。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+SecretInput: 使用临时工作区隔离动作日志；若没有这行代码，测试会污染真实 browser_artifacts。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+SecretInput: 创建隔离 server；若没有这行代码，无法执行工具入口。
            captured_arguments: dict[str, object] = {}  # 新增代码+SecretInput: 保存底层 browser_type 收到的参数；若没有这行代码，无法证明真实值被输入。
            def fake_type(arguments: dict[str, object]) -> str:  # 新增代码+SecretInput: 替换底层输入以避免启动真实浏览器；若没有这行代码，单测会依赖桌面环境。
                captured_arguments.update(arguments)  # 新增代码+SecretInput: 记录底层输入参数；若没有这行代码，测试看不到环境变量值是否被传入。
                return "browser_type 成功\n输入完成\n字符数：9"  # 新增代码+SecretInput: 返回不含敏感值的成功文本；若没有这行代码，外层工具无法完成。
            server.browser_type = fake_type  # 新增代码+SecretInput: 用假输入替换真实输入；若没有这行代码，测试会打开浏览器并输入到真实页面。
            with mock.patch.dict(os.environ, {"LEARNING_AGENT_TEST_PASSWORD": "secret123"}, clear=False):  # 新增代码+SecretInput: 临时设置专用秘密环境变量；若没有这行代码，工具无法读取测试密码。
                result = server.call("browser_type_secret", {"secret_env_var": "LEARNING_AGENT_TEST_PASSWORD", "selector": "#password"})  # 新增代码+SecretInput: 通过公开 call 入口执行敏感输入；若没有这行代码，动作日志脱敏不会被覆盖。
            action_log = (Path(raw_dir) / "browser_artifacts" / "browser_action_log.jsonl").read_text(encoding="utf-8")  # 新增代码+SecretInput: 读取动作日志确认脱敏；若没有这行代码，无法证明日志没有保存密码。
        self.assertEqual(captured_arguments["text"], "secret123")  # 新增代码+SecretInput: 断言底层确实拿到了环境变量值；若没有这行代码，工具可能没有真实输入。
        self.assertIn("browser_type_secret 成功", result)  # 新增代码+SecretInput: 断言敏感输入工具返回成功；若没有这行代码，失败文本也可能被忽略。
        self.assertNotIn("secret123", result)  # 新增代码+SecretInput: 断言工具结果不回显秘密；若没有这行代码，密码泄露不会被发现。
        self.assertNotIn("secret123", action_log)  # 新增代码+SecretInput: 断言动作日志不保存秘密；若没有这行代码，回放审计日志可能泄露密码。
        self.assertIn("[已脱敏]", action_log)  # 新增代码+SecretInput: 断言敏感参数被统一占位；若没有这行代码，脱敏分支可能没有执行。

    def test_flow_run_allows_secret_type_stage_without_leaking_value(self) -> None:  # 新增代码+SecretFlow: 验证复杂流程能执行敏感输入阶段；若没有这行代码，真实网页登录会再次卡在 flow_run 不允许 browser_type_secret。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+SecretFlow: 导入真实 server 类；若没有这行代码，测试无法覆盖公开工具分发入口。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+SecretFlow: 使用临时工作区隔离动作日志；若没有这行代码，测试可能污染真实浏览器审计文件。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+SecretFlow: 创建隔离浏览器 server；若没有这行代码，无法模拟 flow_run 的执行环境。
            captured_arguments: dict[str, object] = {}  # 新增代码+SecretFlow: 保存底层输入收到的参数；若没有这行代码，无法证明环境变量值真的传进输入工具。
            def fake_type(arguments: dict[str, object]) -> str:  # 新增代码+SecretFlow: 用假输入替换真实页面输入；若没有这行代码，单测会打开浏览器并依赖外部网站。
                captured_arguments.update(arguments)  # 新增代码+SecretFlow: 记录 flow_run 传递后的真实输入参数；若没有这行代码，断言没有可观察证据。
                return "browser_type 成功\n输入完成\n字符数：9"  # 新增代码+SecretFlow: 返回不含敏感值的成功文本；若没有这行代码，外层流程无法继续完成。
            server.browser_type = fake_type  # 新增代码+SecretFlow: 把底层输入替换为可观察假实现；若没有这行代码，测试会触发真实键盘输入。
            with mock.patch.dict(os.environ, {"LEARNING_AGENT_TEST_FLOW_PASSWORD": "flowsecret"}, clear=False):  # 新增代码+SecretFlow: 临时设置专用敏感环境变量；若没有这行代码，secret 工具会因为缺值失败。
                result = server.call("browser_flow_run", {"stages": [{"name": "输入敏感字段", "tool": "browser_type_secret", "arguments": {"secret_env_var": "LEARNING_AGENT_TEST_FLOW_PASSWORD", "selector": "#password"}}]})  # 新增代码+SecretFlow: 通过复杂流程调用敏感输入工具；若没有这行代码，无法锁住真实登录需要的多步骤路径。
            action_log = (Path(raw_dir) / "browser_artifacts" / "browser_action_log.jsonl").read_text(encoding="utf-8")  # 新增代码+SecretFlow: 读取动作日志检查是否脱敏；若没有这行代码，日志泄露不会被测试发现。
        self.assertEqual(captured_arguments["text"], "flowsecret")  # 新增代码+SecretFlow: 断言底层输入拿到真实环境变量值；若没有这行代码，流程可能只是空跑成功。
        self.assertIn("browser_flow_run 完成", result)  # 新增代码+SecretFlow: 断言复杂流程整体完成；若没有这行代码，阶段失败可能被忽略。
        self.assertIn("browser_type_secret 成功", result)  # 新增代码+SecretFlow: 断言敏感输入阶段执行成功；若没有这行代码，flow_run 可能没有真正跑到登录输入。
        self.assertNotIn("flowsecret", result)  # 新增代码+SecretFlow: 断言流程结果不回显敏感值；若没有这行代码，密码可能出现在模型上下文。
        self.assertNotIn("flowsecret", action_log)  # 新增代码+SecretFlow: 断言审计日志不保存敏感值；若没有这行代码，任务回放文件可能泄露密码。
        self.assertIn("[已脱敏]", action_log)  # 新增代码+SecretFlow: 断言动作日志使用脱敏占位；若没有这行代码，安全边界无法被自动验证。

    def test_secret_values_are_redacted_from_later_tool_outputs_and_logs(self) -> None:  # 新增代码+SecretOutputRedaction: 验证秘密输入后页面快照也会脱敏；若没有这行代码，登录成功页可能把账号重新交给模型。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+SecretOutputRedaction: 导入被测 server；若没有这行代码，测试无法覆盖真实工具执行器。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+SecretOutputRedaction: 使用临时目录隔离动作日志；若没有这行代码，测试会污染真实项目日志。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+SecretOutputRedaction: 创建隔离 server；若没有这行代码，无法注册秘密脱敏状态。
            captured_arguments: dict[str, object] = {}  # 新增代码+SecretOutputRedaction: 保存底层输入参数；若没有这行代码，无法证明秘密确实输入过。
            def fake_type(arguments: dict[str, object]) -> str:  # 新增代码+SecretOutputRedaction: 用假输入替代真实页面输入；若没有这行代码，单测会依赖浏览器窗口。
                captured_arguments.update(arguments)  # 新增代码+SecretOutputRedaction: 记录输入参数；若没有这行代码，断言没有数据来源。
                return "browser_type 成功\n输入完成\n字符数：11"  # 新增代码+SecretOutputRedaction: 返回不含秘密的输入结果；若没有这行代码，secret 工具无法成功。
            def fake_snapshot(arguments: dict[str, object]) -> str:  # 新增代码+SecretOutputRedaction: 构造包含秘密的后续页面输出；若没有这行代码，无法复现登录后页面显示账号的风险。
                del arguments  # 新增代码+SecretOutputRedaction: 明确假快照不使用参数；若没有这行代码，读者会误以为参数参与了判断。
                return "browser_snapshot 成功\n正文摘要：欢迎回来 用户：18800001111 修改密码"  # 新增代码+SecretOutputRedaction: 模拟页面把账号显示给 agent；若没有这行代码，回归测试无法锁住泄露场景。
            server.browser_type = fake_type  # 新增代码+SecretOutputRedaction: 替换输入实现；若没有这行代码，测试会触发真实输入。
            with mock.patch.dict(os.environ, {"LEARNING_AGENT_TEST_ACCOUNT": "18800001111"}, clear=False):  # 新增代码+SecretOutputRedaction: 设置专用测试账号环境变量；若没有这行代码，secret 工具没有可读秘密。
                type_result = server.call("browser_type_secret", {"secret_env_var": "LEARNING_AGENT_TEST_ACCOUNT", "selector": "#username"})  # 新增代码+SecretOutputRedaction: 先通过公开入口输入秘密；若没有这行代码，后续脱敏列表不会被登记。
            server.browser_snapshot = fake_snapshot  # 新增代码+SecretOutputRedaction: 替换后续快照实现；若没有这行代码，测试无法稳定产出包含秘密的页面文本。
            snapshot_result = server.call("browser_snapshot", {})  # 新增代码+SecretOutputRedaction: 调用公开快照入口触发统一输出脱敏；若没有这行代码，无法证明模型看到的是安全结果。
            action_log = (Path(raw_dir) / "browser_artifacts" / "browser_action_log.jsonl").read_text(encoding="utf-8")  # 新增代码+SecretOutputRedaction: 读取动作日志验证落盘内容；若没有这行代码，日志泄露不会被发现。
        self.assertEqual(captured_arguments["text"], "18800001111")  # 新增代码+SecretOutputRedaction: 断言底层确实输入了秘密；若没有这行代码，测试可能只验证空流程。
        self.assertIn("browser_type_secret 成功", type_result)  # 新增代码+SecretOutputRedaction: 断言秘密输入阶段成功；若没有这行代码，失败也可能继续检查快照。
        self.assertNotIn("18800001111", snapshot_result)  # 新增代码+SecretOutputRedaction: 断言返回给模型的快照不含账号；若没有这行代码，最终回答仍可能泄露账号。
        self.assertNotIn("18800001111", action_log)  # 新增代码+SecretOutputRedaction: 断言动作日志不含账号；若没有这行代码，审计文件可能泄露账号。
        self.assertIn("[已脱敏]", snapshot_result)  # 新增代码+SecretOutputRedaction: 断言快照里使用占位符；若没有这行代码，无法证明替换真的发生。
        self.assertIn("[已脱敏]", action_log)  # 新增代码+SecretOutputRedaction: 断言日志里使用占位符；若没有这行代码，落盘脱敏可能没有执行。

    def test_visible_browser_launch_unlocks_open_after_real_browser_wording(self) -> None:  # 新增代码+VisibleBrowser验收: 验证用户说“真实浏览器”时，显式启动可见独立浏览器后可以继续打开网页；若没有这行代码，真实验收会卡在 browser_open 不可见。
        workspace = self._project_root()  # 新增代码+VisibleBrowser验收: 使用真实项目根目录读取动态 skill；若没有这行代码，测试不会覆盖交付路径。
        fake_client = FakeMcpClient(tools=[{"name": "browser_launch_visible", "description": "Launch visible browser", "inputSchema": {"type": "object", "properties": {"confirm_visible_browser": {"type": "boolean"}}, "required": ["confirm_visible_browser"]}}, {"name": "browser_open", "description": "Open visible page", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}], result_prefix="browser_launch_visible 成功\nvisible_browser=true\nheadless=false\ncalled")  # 新增代码+VisibleBrowser验收: 构造可见启动和打开页面两个 MCP 工具；若没有这行代码，无法复现真实工具池解锁路径。
        registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+VisibleBrowser验收: 使用 browser_automation server 名触发能力包映射；若没有这行代码，fake 工具不会按浏览器能力包加载。
        agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry, debug_enabled=False)  # 新增代码+VisibleBrowser验收: 创建自动授权测试 agent；若没有这行代码，无法执行真实工具策略。
        agent.real_chrome_requested = True  # 新增代码+VisibleBrowser验收: 模拟用户 prompt 命中了“真实浏览器”关键词；若没有这行代码，测试无法覆盖本次真实验收失败条件。
        agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/tool_list.md"}))  # 新增代码+VisibleBrowser验收: 先读动态提示词总索引；若没有这行代码，后续读取 browser skill 会被层级门控挡住。
        agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/browser_automation/SKILL.md"}))  # 新增代码+VisibleBrowser验收: 读取普通浏览器 skill 以加载可见启动工具；若没有这行代码，browser_launch_visible 不会进入工具池。
        before_launch_tools = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+VisibleBrowser验收: 读取启动前模型可见工具；若没有这行代码，无法证明 browser_open 起初确实被真实 Chrome workflow 拦截。
        self.assertIn("mcp__browser_automation__browser_launch_visible", before_launch_tools)  # 新增代码+VisibleBrowser验收: 断言可见浏览器启动入口必须可见；若没有这行代码，agent 无法开始可见验收。
        self.assertNotIn("mcp__browser_automation__browser_open", before_launch_tools)  # 新增代码+VisibleBrowser验收: 断言真实浏览器关键词下打开页面起初仍受保护；若没有这行代码，安全边界可能被过度放宽。
        launch_result = agent._execute_tool(ToolCall(name="mcp__browser_automation__browser_launch_visible", arguments={"confirm_visible_browser": True}))  # 新增代码+VisibleBrowser验收: 执行可见启动工具推进 workflow；若没有这行代码，后续工具池不会有状态变化。
        after_launch_tools = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+VisibleBrowser验收: 读取启动后的模型可见工具；若没有这行代码，无法验证 browser_open 是否恢复。
        self.assertIn("visible_browser=true", launch_result)  # 新增代码+VisibleBrowser验收: 断言启动结果包含可见状态；若没有这行代码，假启动结果无法推进可靠验收。
        self.assertIn("headless=false", launch_result)  # 新增代码+VisibleBrowser验收: 断言启动结果包含非 headless 状态；若没有这行代码，测试可能接受无窗口模式。
        self.assertIn("mcp__browser_automation__browser_open", after_launch_tools)  # 新增代码+VisibleBrowser验收: 断言可见浏览器启动成功后 browser_open 可见；若没有这行代码，真实浏览器窗口只能打开不能继续操作。

    def test_visual_locate_uses_snapshot_geometry_without_selector_guessing(self) -> None:  # 新增代码+BrowserRuntime对齐测试: 验证视觉定位可直接使用快照里的几何信息；若没有这行代码，视觉定位可能仍停留在纯文本 selector。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserRuntime对齐测试: 导入被测浏览器 server；若没有这行代码，测试没有运行时对象。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRuntime对齐测试: 使用临时工作区隔离动作日志；若没有这行代码，测试会污染真实 browser_artifacts。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserRuntime对齐测试: 创建隔离 server 实例；若没有这行代码，无法布置假页面状态。
            server.pages = {"page-1": FakeRuntimePage()}  # 新增代码+BrowserRuntime对齐测试: 注入一个可用假页面；若没有这行代码，visual_locate 找不到当前页面。
            server.current_page_id = "page-1"  # 新增代码+BrowserRuntime对齐测试: 指定当前页面；若没有这行代码，省略 page_id 的调用没有目标。
            server.element_refs = {"page-1": [{"id": 1, "label": "Submit order", "selector": "button#submit", "visible": True, "x": 10, "y": 20, "width": 100, "height": 30, "center_x": 60, "center_y": 35}]}  # 新增代码+BrowserRuntime对齐测试: 注入带边框和中心点的快照元素；若没有这行代码，视觉定位没有可匹配候选。
            result = server.call("browser_visual_locate", {"page_id": "page-1", "text": "Submit"})  # 新增代码+BrowserRuntime对齐测试: 调用公开视觉定位工具；若没有这行代码，测试无法证明工具入口可用。
        self.assertIn("browser_visual_locate 成功", result)  # 新增代码+BrowserRuntime对齐测试: 断言视觉定位成功；若没有这行代码，失败文本也可能被误当通过。
        self.assertIn("center_x=60", result)  # 新增代码+BrowserRuntime对齐测试: 断言返回中心点横坐标；若没有这行代码，视觉定位无法指导坐标点击。
        self.assertIn("center_y=35", result)  # 新增代码+BrowserRuntime对齐测试: 断言返回中心点纵坐标；若没有这行代码，视觉定位无法指导坐标点击。

    def test_visual_locate_can_find_non_interactive_text_blocks(self) -> None:  # 新增代码+BrowserRuntime文本定位: 验证视觉定位能找到标题和正文这类不可点击文本；若没有这行代码，Example Domain 标题会再次定位失败。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserRuntime文本定位: 导入被测浏览器 server；若没有这行代码，测试没有真实工具入口。
        class FakeTextPage(FakeRuntimePage):  # 新增代码+BrowserRuntime文本定位: 定义能返回页面文本候选的假页面；若没有这个类，测试需要启动真实浏览器才可复现。
            def evaluate(self, script: str) -> list[dict[str, object]]:  # 新增代码+BrowserRuntime文本定位: 模拟 Playwright page.evaluate；若没有这行代码，文本候选收集无法测试。
                del script  # 新增代码+BrowserRuntime文本定位: 明确测试不关心注入脚本内容；若没有这行代码，未使用参数意图不清楚。
                return [{"id": "text-1", "tag": "h1", "label": "Example Domain", "selector": "h1:nth-of-type(1)", "visible": True, "x": 10, "y": 20, "width": 300, "height": 40, "center_x": 160, "center_y": 40}]  # 新增代码+BrowserRuntime文本定位: 返回不可交互标题元素的视觉框；若没有这行代码，测试无法证明标题定位恢复。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRuntime文本定位: 使用临时目录隔离动作日志；若没有这行代码，测试会污染真实浏览器产物。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserRuntime文本定位: 创建隔离 server；若没有这行代码，无法布置假页面。
            server.pages = {"page-1": FakeTextPage()}  # 新增代码+BrowserRuntime文本定位: 注入可评估文本候选的假页面；若没有这行代码，visual_locate 找不到目标页。
            server.current_page_id = "page-1"  # 新增代码+BrowserRuntime文本定位: 设置当前页面；若没有这行代码，省略 page_id 的逻辑无法定位。
            result = server.call("browser_visual_locate", {"page_id": "page-1", "text": "Example Domain", "selector": "h1"})  # 新增代码+BrowserRuntime文本定位: 用真实验收失败参数调用视觉定位；若没有这行代码，回归测试不贴近现场。
        self.assertIn("browser_visual_locate 成功", result)  # 新增代码+BrowserRuntime文本定位: 断言文本标题定位成功；若没有这行代码，空结果不会被发现。
        self.assertIn("center_x=160", result)  # 新增代码+BrowserRuntime文本定位: 断言返回标题中心点横坐标；若没有这行代码，定位结果无法用于视觉点击或审计。
        self.assertIn("center_y=40", result)  # 新增代码+BrowserRuntime文本定位: 断言返回标题中心点纵坐标；若没有这行代码，定位结果缺少可复核几何信息。

    def test_flow_run_defaults_empty_wait_stage_to_short_delay(self) -> None:  # 新增代码+BrowserRuntime流程容错: 验证 flow_run 中空 browser_wait 阶段会自动变成短等待；若没有这行代码，模型少传等待参数会让复杂流程失败。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserRuntime流程容错: 导入被测 server；若没有这行代码，测试无法调用公开流程工具。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRuntime流程容错: 使用临时目录隔离动作日志；若没有这行代码，测试会污染真实产物。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserRuntime流程容错: 创建隔离 server；若没有这行代码，无法替换 wait 工具。
            captured_arguments: list[dict[str, object]] = []  # 新增代码+BrowserRuntime流程容错: 保存 flow_run 传给 browser_wait 的参数；若没有这行代码，无法证明默认值被补上。
            def fake_wait(arguments: dict[str, object]) -> str:  # 新增代码+BrowserRuntime流程容错: 定义假等待工具避免真实 sleep；若没有这行代码，单测会变慢且依赖页面。
                captured_arguments.append(dict(arguments))  # 新增代码+BrowserRuntime流程容错: 记录收到的等待参数；若没有这行代码，断言没有观察对象。
                return "browser_wait 成功\npage_id=page-1"  # 新增代码+BrowserRuntime流程容错: 返回成功文本让流程继续；若没有这行代码，flow_run 无法完成。
            server.browser_wait = fake_wait  # 新增代码+BrowserRuntime流程容错: 用假等待替换真实等待；若没有这行代码，测试会要求真实页面。
            result = server.call("browser_flow_run", {"stages": [{"name": "空等待阶段", "tool": "browser_wait", "arguments": {}}]})  # 新增代码+BrowserRuntime流程容错: 复现真实验收里的空 wait 参数；若没有这行代码，默认补参逻辑不会被触发。
        self.assertIn("browser_flow_run 完成", result)  # 新增代码+BrowserRuntime流程容错: 断言流程完成而不是失败；若没有这行代码，模型的小参数遗漏仍会拖垮验收。
        self.assertEqual(captured_arguments[0]["milliseconds"], 250)  # 新增代码+BrowserRuntime流程容错: 断言空 wait 自动补 250ms；若没有这行代码，默认等待值可能失效或过长。

    def test_flow_run_can_load_stages_from_workspace_file(self) -> None:  # 新增代码+FlowFile: 验证复杂流程可以从文件读取 stages；若没有这行代码，真实验收仍要模型复制长 JSON。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+FlowFile: 导入被测 server；若没有这行代码，测试无法覆盖真实工具入口。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+FlowFile: 使用临时工作区放流程文件；若没有这行代码，测试会污染项目目录。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+FlowFile: 创建以临时目录为 workspace 的 server；若没有这行代码，stages_file 相对路径无法解析。
            flow_file = Path(raw_dir) / "flow.md"  # 新增代码+FlowFile: 定义工作区内的 Markdown 流程文件；若没有这行代码，工具没有文件可读。
            flow_file.write_text("```json\n{\"stages\":[{\"name\":\"file wait\",\"tool\":\"browser_wait\",\"arguments\":{}}],\"continue_on_error\":false}\n```", encoding="utf-8")  # 新增代码+FlowFile: 写入包含 JSON 代码块的流程文件；若没有这行代码，无法验证 Markdown 提取逻辑。
            captured_arguments: list[dict[str, object]] = []  # 新增代码+FlowFile: 保存文件流程传给 wait 的参数；若没有这行代码，无法证明文件 stages 被执行。
            def fake_wait(arguments: dict[str, object]) -> str:  # 新增代码+FlowFile: 用假等待避免真实 sleep；若没有这行代码，单测会变慢且依赖页面。
                captured_arguments.append(dict(arguments))  # 新增代码+FlowFile: 记录实际等待参数；若没有这行代码，断言没有观察对象。
                return "browser_wait 成功\npage_id=page-1"  # 新增代码+FlowFile: 返回成功文本让流程完成；若没有这行代码，测试流程会失败。
            server.browser_wait = fake_wait  # 新增代码+FlowFile: 替换真实等待工具；若没有这行代码，测试无法稳定验证文件加载。
            result = server.call("browser_flow_run", {"stages_file": "flow.md"})  # 新增代码+FlowFile: 通过 stages_file 调用公开流程工具；若没有这行代码，新增参数不会被覆盖。
        self.assertIn("browser_flow_run 完成", result)  # 新增代码+FlowFile: 断言文件流程整体完成；若没有这行代码，文件未执行也可能被忽略。
        self.assertEqual(captured_arguments[0]["milliseconds"], 250)  # 新增代码+FlowFile: 断言文件里的空 wait 仍会自动补短等待；若没有这行代码，文件流程容错可能丢失。

    def test_coordinate_click_records_action_log_for_replay(self) -> None:  # 新增代码+BrowserRuntime对齐测试: 验证坐标点击会真实调用鼠标并写动作日志；若没有这行代码，回放无法审计实际动作。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserRuntime对齐测试: 导入被测 server 类；若没有这行代码，测试无法创建浏览器运行层。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRuntime对齐测试: 使用临时目录隔离日志文件；若没有这行代码，测试会写入真实项目产物目录。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserRuntime对齐测试: 创建隔离 server；若没有这行代码，无法验证动作日志路径。
            page = FakeRuntimePage()  # 新增代码+BrowserRuntime对齐测试: 创建可记录鼠标点击的假页面；若没有这行代码，坐标点击没有观察对象。
            server.pages = {"page-1": page}  # 新增代码+BrowserRuntime对齐测试: 把假页面登记到 server；若没有这行代码，current_page 找不到目标。
            server.current_page_id = "page-1"  # 新增代码+BrowserRuntime对齐测试: 设置当前页；若没有这行代码，browser_click 省略 page_id 时会失败。
            result = server.call("browser_click", {"page_id": "page-1", "x": 12, "y": 34})  # 新增代码+BrowserRuntime对齐测试: 通过公开 call 入口执行坐标点击；若没有这行代码，重试和记录包装不会被覆盖。
            action_log = (Path(raw_dir) / "browser_artifacts" / "browser_action_log.jsonl").read_text(encoding="utf-8")  # 新增代码+BrowserRuntime对齐测试: 读取动作日志；若没有这行代码，无法证明任务回放有数据来源。
        self.assertEqual(page.mouse.clicks, [(12, 34)])  # 新增代码+BrowserRuntime对齐测试: 断言鼠标坐标准确；若没有这行代码，实现可能仍走 selector 点击。
        self.assertIn("browser_click 成功", result)  # 新增代码+BrowserRuntime对齐测试: 断言点击工具返回成功；若没有这行代码，异常也可能因为日志断言被掩盖。
        self.assertIn('"tool": "browser_click"', action_log)  # 新增代码+BrowserRuntime对齐测试: 断言动作日志记录工具名；若没有这行代码，回放和审计无法知道执行了什么。

    def test_call_retries_transient_browser_errors(self) -> None:  # 新增代码+BrowserRuntime对齐测试: 验证统一工具执行器会重试临时浏览器错误；若没有这行代码，页面偶发超时仍会直接中断长任务。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserRuntime对齐测试: 导入被测 server；若没有这行代码，测试无法覆盖 call 包装器。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRuntime对齐测试: 使用临时工作区；若没有这行代码，失败日志会污染真实项目。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserRuntime对齐测试: 创建隔离 server；若没有这行代码，无法替换工具方法。
            attempts = {"count": 0}  # 新增代码+BrowserRuntime对齐测试: 保存假工具被调用次数；若没有这行代码，无法断言是否真的重试。
            def flaky_wait(arguments: dict[str, object]) -> str:  # 新增代码+BrowserRuntime对齐测试: 定义第一次失败第二次成功的假等待工具；若没有这行代码，测试无法稳定复现临时错误。
                del arguments  # 新增代码+BrowserRuntime对齐测试: 明确假工具不使用参数；若没有这行代码，参数未用意图不清楚。
                attempts["count"] += 1  # 新增代码+BrowserRuntime对齐测试: 记录调用次数；若没有这行代码，重试次数不可见。
                if attempts["count"] == 1:  # 新增代码+BrowserRuntime对齐测试: 第一次调用进入失败分支；若没有这行代码，测试不会覆盖重试。
                    raise RuntimeError("Timeout while waiting for page")  # 新增代码+BrowserRuntime对齐测试: 抛出可重试的超时错误；若没有这行代码，包装器没有错误可处理。
                return "flaky wait ok"  # 新增代码+BrowserRuntime对齐测试: 第二次返回成功；若没有这行代码，重试后仍无法完成。
            server.browser_wait = flaky_wait  # 新增代码+BrowserRuntime对齐测试: 用假工具替换实例方法；若没有这行代码，测试会调用真实等待逻辑。
            result = server.call("browser_wait", {"milliseconds": 1})  # 新增代码+BrowserRuntime对齐测试: 通过公开 call 入口触发统一重试；若没有这行代码，无法证明分发层已接管重试。
        self.assertEqual(result, "flaky wait ok")  # 新增代码+BrowserRuntime对齐测试: 断言重试后返回成功结果；若没有这行代码，包装器可能吞掉成功内容。
        self.assertEqual(attempts["count"], 2)  # 新增代码+BrowserRuntime对齐测试: 断言确实执行了两次；若没有这行代码，假成功无法证明重试发生。

    def test_recover_page_reload_updates_recovery_summary(self) -> None:  # 新增代码+BrowserRuntime对齐测试: 验证页面恢复工具能执行 reload 并留下状态摘要；若没有这行代码，页面失败恢复仍不可审计。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserRuntime对齐测试: 导入被测 server；若没有这行代码，测试无法调用恢复工具。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRuntime对齐测试: 使用临时工作区；若没有这行代码，恢复日志会污染项目产物。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserRuntime对齐测试: 创建隔离 server；若没有这行代码，无法布置假页面。
            page = FakeRuntimePage()  # 新增代码+BrowserRuntime对齐测试: 创建可记录 reload 的假页面；若没有这行代码，恢复动作无观察对象。
            server.pages = {"page-1": page}  # 新增代码+BrowserRuntime对齐测试: 登记假页面；若没有这行代码，恢复工具找不到页面。
            server.current_page_id = "page-1"  # 新增代码+BrowserRuntime对齐测试: 设置当前页；若没有这行代码，恢复工具省略 page_id 时会失败。
            result = server.call("browser_recover_page", {"page_id": "page-1", "action": "reload"})  # 新增代码+BrowserRuntime对齐测试: 调用页面恢复工具；若没有这行代码，测试只验证了内部状态没有验证公开入口。
        self.assertEqual(page.reload_count, 1)  # 新增代码+BrowserRuntime对齐测试: 断言 reload 执行一次；若没有这行代码，恢复工具可能只返回文本不操作页面。
        self.assertIn("browser_recover_page 成功", result)  # 新增代码+BrowserRuntime对齐测试: 断言恢复成功；若没有这行代码，错误文本可能被误判通过。
        self.assertIn("action=reload", result)  # 新增代码+BrowserRuntime对齐测试: 断言恢复结果包含动作名；若没有这行代码，审计时不知道做了哪种恢复。

    def test_site_grant_can_enable_strict_real_chrome_origin_boundary(self) -> None:  # 新增代码+BrowserRuntime对齐测试: 验证站点级授权状态可开启并出现在状态报告；若没有这行代码，登录态安全仍只是敏感脚本阻断。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserRuntime对齐测试: 导入被测 server；若没有这行代码，测试无法调用 site grant。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRuntime对齐测试: 使用临时工作区；若没有这行代码，状态文件会污染真实项目。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserRuntime对齐测试: 创建隔离 server；若没有这行代码，无法验证权限状态。
            grant_result = server.call("browser_site_grant", {"action": "grant", "origin": "https://example.com", "confirm_site_grant": True})  # 新增代码+BrowserRuntime对齐测试: 授权一个站点 origin；若没有这行代码，站点级权限没有可用数据。
            strict_result = server.call("browser_site_grant", {"action": "enable_strict", "confirm_site_grant": True})  # 新增代码+BrowserRuntime对齐测试: 开启严格站点边界；若没有这行代码，真实 profile 打开任意站点仍无法被限制。
            status_result = server.call("browser_profile_status", {})  # 新增代码+BrowserRuntime对齐测试: 读取状态报告；若没有这行代码，其他 agent 无法看见安全边界。
        self.assertIn("granted_origin=https://example.com", grant_result)  # 新增代码+BrowserRuntime对齐测试: 断言授权结果包含 origin；若没有这行代码，授权结果可能不可审计。
        self.assertIn("strict_site_permissions=true", strict_result)  # 新增代码+BrowserRuntime对齐测试: 断言严格模式开启；若没有这行代码，调用可能只是空操作。
        self.assertIn("site_grants=1", status_result)  # 新增代码+BrowserRuntime对齐测试: 断言状态能看见授权数量；若没有这行代码，UI/SDK 无法展示安全范围。

    def test_replay_dry_run_lists_recorded_safe_actions(self) -> None:  # 新增代码+BrowserRuntime对齐测试: 验证任务回放能以 dry-run 方式列出安全动作；若没有这行代码，复杂浏览器任务无法复现和审计。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserRuntime对齐测试: 导入被测 server；若没有这行代码，测试无法写入动作轨迹。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRuntime对齐测试: 使用临时工作区隔离 JSONL；若没有这行代码，回放测试会读取真实历史动作。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserRuntime对齐测试: 创建隔离 server；若没有这行代码，无法使用动作记录器。
            server._record_browser_action("browser_open", {"url": "https://example.com"}, "success", "ok", 1, "")  # 新增代码+BrowserRuntime对齐测试: 直接记录一条安全打开动作；若没有这行代码，回放工具没有输入数据。
            result = server.call("browser_replay", {"dry_run": True, "max_steps": 5})  # 新增代码+BrowserRuntime对齐测试: 以 dry-run 调用回放工具；若没有这行代码，测试可能真的重新打开网页。
        self.assertIn("browser_replay 计划", result)  # 新增代码+BrowserRuntime对齐测试: 断言回放返回计划而非执行；若没有这行代码，默认安全边界可能失效。
        self.assertIn("browser_open", result)  # 新增代码+BrowserRuntime对齐测试: 断言计划列出记录动作；若没有这行代码，回放没有复现价值。


if __name__ == "__main__":  # 新增代码+BrowserRuntime对齐测试: 允许直接运行本测试文件；若没有这行代码，单文件调试不方便。
    unittest.main()  # 新增代码+BrowserRuntime对齐测试: 启动 unittest；若没有这行代码，直接执行文件不会跑测试。
