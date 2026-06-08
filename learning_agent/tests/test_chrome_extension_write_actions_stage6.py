"""双轨浏览器 Stage 6 Chrome 插件写动作测试。"""  # 新增代码+ChromeExtensionStage6: 说明本文件锁定插件写动作接入；若没有这行代码，维护者不知道测试保护的架构边界。
from __future__ import annotations  # 新增代码+ChromeExtensionStage6: 延迟解析类型注解；若没有这行代码，局部 fake 类型在旧解释顺序下更脆弱。

from learning_agent.tests.support import *  # 新增代码+ChromeExtensionStage6: 复用项目测试基类、Path、tempfile、threading、time、json 等公共支撑；若没有这行代码，测试会重复大量基础导入。


class ChromeExtensionWriteActionsStage6Tests(LearningAgentTestBase):  # 新增代码+ChromeExtensionStage6: 定义 Stage 6 测试集合；若没有这个类，unittest 不会收集插件写动作测试。
    def test_extension_scripts_poll_commands_and_expose_page_actions(self) -> None:  # 新增代码+ChromeExtensionStage6: 验证扩展脚本具备命令轮询和页面动作入口；若没有这行代码，Python provider 可能绿但真实插件不会执行。
        extension_dir = TEST_ROOT / "chrome_extension"  # 新增代码+ChromeExtensionStage6: 定位扩展目录；若没有这行代码，测试无法读取交付脚本。
        background_text = (extension_dir / "background.js").read_text(encoding="utf-8")  # 新增代码+ChromeExtensionStage6: 读取后台脚本；若没有这行代码，无法检查 host 命令轮询。
        content_text = (extension_dir / "content_script.js").read_text(encoding="utf-8")  # 新增代码+ChromeExtensionStage6: 读取页面脚本；若没有这行代码，无法检查拟人动作入口。
        self.assertIn("poll_commands", background_text)  # 新增代码+ChromeExtensionStage6: 断言后台会拉取 pending commands；若没有这行代码，provider 入队动作不会被真实扩展发现。
        self.assertIn("action_result", background_text)  # 新增代码+ChromeExtensionStage6: 断言后台会回传动作结果；若没有这行代码，provider 会等到超时。
        self.assertIn("perform_browser_action", content_text)  # 新增代码+ChromeExtensionStage6: 断言页面脚本能执行 background 下发的动作；若没有这行代码，命令不会进入页面 DOM。
        for fragment in ["click", "type", "press_key", "visual_locate", "scroll"]:  # 新增代码+ChromeExtensionStage6: 遍历 Stage 6 需要的页面动作关键词；若没有这行代码，只会检查单个动作。
            self.assertIn(fragment, content_text + background_text)  # 新增代码+ChromeExtensionStage6: 断言扩展脚本包含该动作能力；若没有这行代码，缺某个动作不会失败。
        for forbidden in ["chrome.cookies", "document.cookie", "localStorage", "sessionStorage"]:  # 新增代码+ChromeExtensionStage6: 继续复用敏感 API 禁止清单；若没有这行代码，写动作升级可能顺手越界读取隐私。
            self.assertNotIn(forbidden, background_text + content_text)  # 新增代码+ChromeExtensionStage6: 断言扩展脚本仍不触碰敏感浏览器 API；若没有这行代码，隐私边界会倒退。

    def test_message_protocol_builds_write_command_and_sanitizes_action_result(self) -> None:  # 新增代码+ChromeExtensionStage6: 验证协议能构造写动作命令并清理结果；若没有这行代码，插件写动作会缺少安全协议门禁。
        from learning_agent.browser_extension_host.message_protocol import build_host_response, build_write_command  # 新增代码+ChromeExtensionStage6: 导入待实现的写命令构造和 host 响应入口；若没有这行代码，测试无法驱动协议层。
        command = build_write_command("browser_click", {"selector": "#submit", "page_id": "chrome-tab-7"}, command_id="cmd-stage6-1")  # 新增代码+ChromeExtensionStage6: 构造一次点击命令；若没有这行代码，无法验证统一工具名映射成插件动作。
        self.assertEqual(command["action"], "click")  # 新增代码+ChromeExtensionStage6: 断言 browser_click 会映射成插件 click；若没有这行代码，插件可能收到错误动作名。
        self.assertEqual(command["command_id"], "cmd-stage6-1")  # 新增代码+ChromeExtensionStage6: 断言命令 id 稳定；若没有这行代码，结果无法和命令关联。
        self.assertEqual(command["target"]["selector"], "#submit")  # 新增代码+ChromeExtensionStage6: 断言定位目标被保留；若没有这行代码，点击命令会丢失元素目标。
        result = build_host_response({"action": "action_result", "command_id": "cmd-stage6-1", "tool_name": "browser_click", "ok": True, "result": {"visibleText": "提交完成", "cookie": "secret", "tab": {"id": 7, "url": "https://example.com/form", "title": "Form", "active": True}}})  # 新增代码+ChromeExtensionStage6: 模拟扩展执行后的结果消息；若没有这行代码，脱敏和结果 schema 没有输入。
        encoded = json.dumps(result, ensure_ascii=False)  # 新增代码+ChromeExtensionStage6: 转成 JSON 文本便于扫描敏感字段；若没有这行代码，只能检查局部对象。
        self.assertTrue(result["ok"])  # 新增代码+ChromeExtensionStage6: 断言成功结果会被接受；若没有这行代码，插件写动作无法返回成功。
        self.assertEqual(result["action"], "action_result")  # 新增代码+ChromeExtensionStage6: 断言结果动作类型稳定；若没有这行代码，bridge 无法区分只读消息和写动作结果。
        self.assertIn("提交完成", encoded)  # 新增代码+ChromeExtensionStage6: 断言可见结果摘要保留；若没有这行代码，用户看不到动作后的页面反馈。
        self.assertNotIn("secret", encoded)  # 新增代码+ChromeExtensionStage6: 断言敏感值被过滤；若没有这行代码，插件结果可能泄露 cookie/token。
        self.assertNotIn("cookie", encoded.lower())  # 新增代码+ChromeExtensionStage6: 断言敏感字段名也被过滤；若没有这行代码，响应结构会暴露隐私线索。

    def test_bridge_state_queues_write_command_and_records_result(self) -> None:  # 新增代码+ChromeExtensionStage6: 验证 bridge 能保存待执行命令和执行结果；若没有这行代码，provider 和扩展无法异步协作。
        from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+ChromeExtensionStage6: 导入 bridge 状态对象；若没有这行代码，测试无法覆盖命令队列。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ChromeExtensionStage6: 使用临时目录隔离 bridge 状态文件；若没有这行代码，测试会污染真实 memory。
            bridge = ChromeExtensionBridgeState(Path(raw_dir) / "bridge_state.json")  # 新增代码+ChromeExtensionStage6: 创建文件支持的 bridge state；若没有这行代码，命令无法落盘。
            bridge.record_connection(extension_id="stage6-extension")  # 新增代码+ChromeExtensionStage6: 模拟插件已连接；若没有这行代码，命令队列状态无法体现可用连接。
            command = bridge.enqueue_command("browser_click", {"selector": "#ok", "page_id": "chrome-tab-7"})  # 新增代码+ChromeExtensionStage6: 入队一次点击命令；若没有这行代码，pending command 没有样本。
            pending = bridge.pending_commands()  # 新增代码+ChromeExtensionStage6: 读取待执行命令列表；若没有这行代码，无法验证扩展能拉取命令。
            bridge.record_command_result({"action": "action_result", "command_id": command["command_id"], "tool_name": "browser_click", "ok": True, "result": {"visibleText": "按钮已点击", "tab": {"id": 7, "url": "https://example.com", "title": "Example", "active": True}}})  # 新增代码+ChromeExtensionStage6: 记录扩展返回的执行结果；若没有这行代码，provider 没有结果可消费。
            result = bridge.consume_command_result(command["command_id"])  # 新增代码+ChromeExtensionStage6: 按 command id 消费结果；若没有这行代码，调用方无法同步拿到执行完成状态。
            status = bridge.command_status_text()  # 新增代码+ChromeExtensionStage6: 读取人类可读命令状态；若没有这行代码，调试时看不到最近命令。
        self.assertEqual(len(pending), 1)  # 新增代码+ChromeExtensionStage6: 断言命令进入 pending 队列；若没有这行代码，扩展可能永远拉不到动作。
        self.assertEqual(pending[0]["command_id"], command["command_id"])  # 新增代码+ChromeExtensionStage6: 断言 pending 命令 id 可追踪；若没有这行代码，结果关联会断开。
        self.assertTrue(result["ok"])  # 新增代码+ChromeExtensionStage6: 断言结果成功；若没有这行代码，bridge 可能把成功结果当失败。
        self.assertIn("按钮已点击", json.dumps(result, ensure_ascii=False))  # 新增代码+ChromeExtensionStage6: 断言动作结果摘要可见；若没有这行代码，用户无法审计页面反馈。
        self.assertIn("browser_click", status)  # 新增代码+ChromeExtensionStage6: 断言状态文本包含工具名；若没有这行代码，状态页无法知道最近执行了什么。

    def test_provider_supports_write_tools_and_waits_for_extension_result(self) -> None:  # 新增代码+ChromeExtensionStage6: 验证 provider 能执行写工具并等待扩展结果；若没有这行代码，provider 只会声明支持但不能闭环。
        from learning_agent.browser.providers.chrome_extension import ChromeExtensionProvider  # 新增代码+ChromeExtensionStage6: 导入待实现插件 provider；若没有这行代码，测试无法覆盖 adapter。
        from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+ChromeExtensionStage6: 导入 bridge 状态对象；若没有这行代码，provider 没有命令来源。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ChromeExtensionStage6: 使用临时目录隔离 provider 状态；若没有这行代码，测试会污染真实 memory。
            bridge = ChromeExtensionBridgeState(Path(raw_dir) / "bridge_state.json")  # 新增代码+ChromeExtensionStage6: 创建 bridge；若没有这行代码，provider 无法入队命令。
            bridge.record_connection(extension_id="stage6-extension")  # 新增代码+ChromeExtensionStage6: 模拟插件已连接；若没有这行代码，provider health 不会可用。
            provider = ChromeExtensionProvider(bridge, command_timeout_seconds=2.0)  # 新增代码+ChromeExtensionStage6: 创建带短超时的 provider；若没有这行代码，测试无法等待结果。
            def responder() -> None:  # 新增代码+ChromeExtensionStage6: 定义后台扩展模拟器；若没有这行代码，provider 会一直等不到执行结果。
                deadline = time.time() + 1.0  # 新增代码+ChromeExtensionStage6: 设置最多等待 1 秒；若没有这行代码，测试失败时可能卡住。
                while time.time() < deadline:  # 新增代码+ChromeExtensionStage6: 轮询 pending 命令；若没有这行代码，线程无法等待 provider 入队。
                    pending_commands = bridge.pending_commands()  # 新增代码+ChromeExtensionStage6: 读取待执行命令；若没有这行代码，模拟器不知道何时回填结果。
                    if pending_commands:  # 新增代码+ChromeExtensionStage6: 命令出现后回填结果；若没有这行代码，空列表也会被误处理。
                        command = pending_commands[0]  # 新增代码+ChromeExtensionStage6: 取第一条命令；若没有这行代码，无法取得 command_id。
                        bridge.record_command_result({"action": "action_result", "command_id": command["command_id"], "tool_name": command["tool_name"], "ok": True, "result": {"visibleText": "输入完成", "tab": {"id": 7, "url": "https://example.com/form", "title": "Form", "active": True}}})  # 新增代码+ChromeExtensionStage6: 模拟扩展成功执行并回传页面摘要；若没有这行代码，provider 不能完成。
                        return  # 新增代码+ChromeExtensionStage6: 回填后结束线程；若没有这行代码，线程会重复记录结果。
                    time.sleep(0.02)  # 新增代码+ChromeExtensionStage6: 短暂等待避免忙等；若没有这行代码，测试会浪费 CPU。
            thread = threading.Thread(target=responder)  # 新增代码+ChromeExtensionStage6: 创建模拟扩展线程；若没有这行代码，provider execute_tool 会阻塞到超时。
            thread.start()  # 新增代码+ChromeExtensionStage6: 启动模拟扩展；若没有这行代码，结果永远不会出现。
            result = provider.execute_tool("browser_type", {"selector": "#name", "text": "Alice", "page_id": "chrome-tab-7"})  # 新增代码+ChromeExtensionStage6: 通过统一 browser_type 执行插件输入；若没有这行代码，provider 写动作路径没有被触发。
            thread.join(timeout=2.0)  # 新增代码+ChromeExtensionStage6: 等待模拟扩展结束；若没有这行代码，后台线程可能拖到下个测试。
        self.assertTrue(provider.supports_tool("browser_click"))  # 新增代码+ChromeExtensionStage6: 断言插件 provider 支持点击；若没有这行代码，写工具可能仍回退旧 handler。
        self.assertTrue(provider.supports_tool("browser_type"))  # 新增代码+ChromeExtensionStage6: 断言插件 provider 支持输入；若没有这行代码，表单任务无法走插件路线。
        self.assertIn("browser_type 成功", result)  # 新增代码+ChromeExtensionStage6: 断言输出显示输入成功；若没有这行代码，用户无法确认动作结果。
        self.assertIn("provider=chrome_extension", result)  # 新增代码+ChromeExtensionStage6: 断言结果来自插件 provider；若没有这行代码，底层轨道不可审计。
        self.assertIn("command_id=", result)  # 新增代码+ChromeExtensionStage6: 断言结果带命令 id；若没有这行代码，后续 replay 和状态无法关联。

    def test_server_routes_extension_write_action_through_browser_action_executor(self) -> None:  # 新增代码+ChromeExtensionStage6: 验证生产 server 的插件写动作仍进入统一执行器；若没有这行代码，provider 写动作可能成为旁路系统。
        from learning_agent.browser.providers.protocol import BrowserProviderDecision, BrowserProviderKind  # 新增代码+ChromeExtensionStage6: 导入 provider 决策模型；若没有这行代码，测试无法强制选择插件 provider。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+ChromeExtensionStage6: 导入真实浏览器 MCP server；若没有这行代码，无法覆盖生产入口。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ChromeExtensionStage6: 使用临时 workspace 隔离 runtime store；若没有这行代码，测试会污染真实 memory。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+ChromeExtensionStage6: 创建真实 server；若没有这行代码，无法验证 call() 链路。
            server.chrome_extension_bridge.record_connection(extension_id="stage6-extension")  # 新增代码+ChromeExtensionStage6: 模拟插件已连接；若没有这行代码，provider 健康状态不可用。
            server._enforce_tabs_context_contract = lambda tool_name: None  # type: ignore[method-assign]  # 新增代码+ChromeExtensionStage6: 测试聚焦插件 provider，不让 Stage 4 真实 Chrome context 门禁干扰；若没有这行代码，click 会先被 context 合同拦截。
            server._decide_browser_provider_for_tool = lambda tool_name, arguments: BrowserProviderDecision(provider=BrowserProviderKind.CHROME_EXTENSION, reason="stage6 test", tool_name=tool_name, reason_code="stage6_test")  # type: ignore[method-assign]  # 新增代码+ChromeExtensionStage6: 强制路由到插件 provider；若没有这行代码，默认公开网页会走可见 Chromium。
            server.chrome_extension_provider.execute_tool = lambda tool_name, arguments: "browser_click 成功\nprovider=chrome_extension\ncommand_id=cmd-stage6-server\nobservation_id=obs-stage6-server"  # type: ignore[method-assign]  # 新增代码+ChromeExtensionStage6: 用轻量 fake 替代真实扩展等待；若没有这行代码，测试需要安装真实 Chrome 插件。
            result = server.call("browser_click", {"selector": "#ok"})  # 新增代码+ChromeExtensionStage6: 从生产统一工具入口执行点击；若没有这行代码，server 分发路径没有被验证。
            event_types = [event["event_type"] for event in server.browser_action_executor.events]  # 新增代码+ChromeExtensionStage6: 读取执行器内存事件；若没有这行代码，无法确认是否进入 action executor。
        self.assertIn("provider=chrome_extension", result)  # 新增代码+ChromeExtensionStage6: 断言结果来自插件 provider；若没有这行代码，测试无法证明走了插件轨道。
        self.assertIn("browser_action_started", event_types)  # 新增代码+ChromeExtensionStage6: 断言执行器记录 started；若没有这行代码，动作生命周期可能缺入口。
        self.assertIn("browser_action_completed", event_types)  # 新增代码+ChromeExtensionStage6: 断言执行器记录 completed；若没有这行代码，动作生命周期可能缺收尾。
