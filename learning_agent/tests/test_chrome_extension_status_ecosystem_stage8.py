"""双轨浏览器 Stage 8 状态 UI/CLI/API 生态测试。"""  # 新增代码+ChromeExtensionStage8: 说明本文件锁定 provider 状态生态；若没有这行代码，维护者不知道测试保护的是状态入口。
from __future__ import annotations  # 新增代码+ChromeExtensionStage8: 延迟解析类型注解；若没有这行代码，局部 fake 类型在旧解释顺序下更脆弱。

from contextlib import redirect_stdout  # 新增代码+ChromeExtensionStage8: 捕获 CLI 输出用于断言；若没有这行代码，测试只能依赖肉眼查看终端。

from learning_agent.tests.support import *  # 新增代码+ChromeExtensionStage8: 复用 tempfile、Path、threading、http.client、json、io 等测试支撑；若没有这行代码，测试会重复大量基础导入。


class ChromeExtensionStatusEcosystemStage8Tests(LearningAgentTestBase):  # 新增代码+ChromeExtensionStage8: 定义 Stage 8 状态生态测试集合；若没有这个类，unittest 不会收集本阶段测试。
    def _seed_stage8_browser_state(self, workspace: Path) -> None:  # 新增代码+ChromeExtensionStage8: 写入一组可审计的插件和浏览器状态；若没有这行代码，每个测试会重复准备状态。
        from learning_agent.browser.runtime_models import BrowserAction, BrowserObservation  # 新增代码+ChromeExtensionStage8: 导入浏览器动作和观察模型；若没有这行代码，测试无法写入最近 action/observation 证据。
        from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+ChromeExtensionStage8: 导入浏览器 runtime store；若没有这行代码，状态快照没有真实 browser run 输入。
        from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+ChromeExtensionStage8: 导入插件 bridge 状态对象；若没有这行代码，测试无法模拟 native host/插件连接。
        bridge = ChromeExtensionBridgeState(workspace / "learning_agent" / "memory" / "chrome_extension_bridge.json")  # 新增代码+ChromeExtensionStage8: 创建与生产路径一致的 bridge 状态文件；若没有这行代码，快照聚合器读不到插件状态。
        bridge.record_connection(extension_id="stage8-extension")  # 新增代码+ChromeExtensionStage8: 模拟插件已经连接 native host；若没有这行代码，provider 健康应为不可用。
        bridge.update_tabs_context({"active_tab_id": "chrome-tab-7", "tabs": [{"id": 7, "url": "https://stage8.test/app", "title": "Stage 8 Tab", "active": True}]})  # 新增代码+ChromeExtensionStage8: 写入当前 tab context；若没有这行代码，状态页无法显示 active tab。
        bridge.update_page_snapshot({"tab": {"id": 7, "url": "https://stage8.test/app", "title": "Stage 8 Tab", "active": True}, "page": {"visibleText": "Stage 8 visible text", "elements": []}})  # 新增代码+ChromeExtensionStage8: 写入页面快照摘要；若没有这行代码，状态页无法关联最近页面内容。
        bridge.record_permission_event({"action": "grant", "origin": "https://stage8.test", "permissions": ["read", "click"]})  # 新增代码+ChromeExtensionStage8: 写入权限事件；若没有这行代码，状态页看不到站点授权变化。
        bridge.enqueue_command("browser_click", {"selector": "#ok", "page_id": "chrome-tab-7"})  # 新增代码+ChromeExtensionStage8: 写入待执行命令；若没有这行代码，pending command 计数无法被测试。
        store = BrowserRuntimeStore(workspace / "memory" / "browser_runtime")  # 新增代码+ChromeExtensionStage8: 创建默认 browser runtime store；若没有这行代码，最近 action/observation 没有事实源。
        store.create_run(run_id="browser-stage8-run", session_id="session-stage8", prompt="Stage 8 状态生态")  # 新增代码+ChromeExtensionStage8: 写入 browser run；若没有这行代码，状态快照没有浏览器任务可展示。
        action = BrowserAction.create("browser-stage8-run", "stage8", "browser_snapshot", {"provider": "chrome_extension"})  # 新增代码+ChromeExtensionStage8: 创建最近浏览器动作；若没有这行代码，recent_actions 无法证明工具动作进入状态。
        action.mark_completed("obs-stage8")  # 新增代码+ChromeExtensionStage8: 标记动作完成并关联 observation；若没有这行代码，action 状态不完整。
        observation = BrowserObservation(observation_id="obs-stage8", run_id="browser-stage8-run", stage_id="stage8", action_id=action.action_id, url="https://stage8.test/app", visible_text="Stage 8 visible text")  # 新增代码+ChromeExtensionStage8: 创建页面观察证据；若没有这行代码，状态页无法展示 observation 证据。
        store.save_action(action)  # 新增代码+ChromeExtensionStage8: 保存浏览器动作；若没有这行代码，快照聚合器读不到 recent action。
        store.save_observation(observation)  # 新增代码+ChromeExtensionStage8: 保存浏览器观察；若没有这行代码，快照聚合器读不到 recent observation。

    def test_snapshot_exposes_provider_extension_tabs_permissions_and_recent_actions(self) -> None:  # 新增代码+ChromeExtensionStage8: 验证状态快照包含 provider、插件、tab、权限和最近证据；若没有这行代码，Stage 8 可能只显示 browser run。
        from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+ChromeExtensionStage8: 导入统一状态快照聚合器；若没有这行代码，测试无法覆盖事实源。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ChromeExtensionStage8: 创建隔离工作区；若没有这行代码，测试会污染真实 memory。
            workspace = Path(raw_dir)  # 新增代码+ChromeExtensionStage8: 规范化临时工作区路径；若没有这行代码，后续路径拼接不稳定。
            self._seed_stage8_browser_state(workspace)  # 新增代码+ChromeExtensionStage8: 写入测试用状态；若没有这行代码，快照缺少输入。
            snapshot = build_status_snapshot(workspace)  # 新增代码+ChromeExtensionStage8: 构建统一状态快照；若没有这行代码，断言没有目标对象。
            provider_status = snapshot["browser"]["provider_status"]  # 新增代码+ChromeExtensionStage8: 读取 provider 状态区块；若没有这行代码，后续断言需要重复索引。
            self.assertTrue(provider_status["providers"]["chrome_extension"]["available"])  # 新增代码+ChromeExtensionStage8: 断言插件 provider 可用；若没有这行代码，连接状态可能未进入 provider 健康。
            self.assertEqual(provider_status["chrome_extension"]["pending_command_count"], 1)  # 新增代码+ChromeExtensionStage8: 断言 pending command 可见；若没有这行代码，写动作卡住时状态页看不到。
            self.assertEqual(provider_status["tabs"]["active_tab"]["url"], "https://stage8.test/app")  # 新增代码+ChromeExtensionStage8: 断言 active tab URL 可见；若没有这行代码，其他 agent 无法判断当前页面。
            self.assertEqual(provider_status["permissions"]["permission_event_count"], 1)  # 新增代码+ChromeExtensionStage8: 断言权限事件数量可见；若没有这行代码，授权变化不可审计。
            self.assertEqual(provider_status["native_host"]["connected"], True)  # 新增代码+ChromeExtensionStage8: 断言 native host 连接摘要可见；若没有这行代码，插件连接和 provider 健康会割裂。
            self.assertEqual(provider_status["recent_actions"][0]["tool_name"], "browser_snapshot")  # 新增代码+ChromeExtensionStage8: 断言最近动作进入 provider 状态；若没有这行代码，状态只显示连接不显示工作证据。

    def test_renderer_and_sdk_expose_same_provider_status(self) -> None:  # 新增代码+ChromeExtensionStage8: 验证终端渲染和 SDK 使用同一 provider 状态事实源；若没有这行代码，UI 和 SDK 可能再次分裂。
        from learning_agent.app.status_renderer import render_status_snapshot  # 新增代码+ChromeExtensionStage8: 导入终端状态渲染器；若没有这行代码，状态 UI 无法被测试。
        from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+ChromeExtensionStage8: 导入快照聚合器；若没有这行代码，渲染没有输入。
        from learning_agent.sdk.status import get_browser_provider_status  # 新增代码+ChromeExtensionStage8: 导入 SDK provider 状态入口；若没有这行代码，外部 agent 只能解析完整快照。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ChromeExtensionStage8: 创建隔离工作区；若没有这行代码，测试会读取真实 memory。
            workspace = Path(raw_dir)  # 新增代码+ChromeExtensionStage8: 保存工作区路径；若没有这行代码，多个入口可能读不同目录。
            self._seed_stage8_browser_state(workspace)  # 新增代码+ChromeExtensionStage8: 写入测试状态；若没有这行代码，渲染没有 provider 内容。
            snapshot = build_status_snapshot(workspace)  # 新增代码+ChromeExtensionStage8: 构建统一快照；若没有这行代码，renderer 无法测试。
            rendered = render_status_snapshot(snapshot)  # 新增代码+ChromeExtensionStage8: 渲染终端状态文本；若没有这行代码，断言没有文本。
            sdk_status = get_browser_provider_status(workspace)  # 新增代码+ChromeExtensionStage8: 通过 SDK 读取 provider 状态；若没有这行代码，无法证明 SDK 入口存在。
            self.assertIn("Browser Providers", rendered)  # 新增代码+ChromeExtensionStage8: 断言终端状态有 provider 区块；若没有这行代码，用户只看到 runtime 区块。
            self.assertIn("chrome_extension", rendered)  # 新增代码+ChromeExtensionStage8: 断言插件 provider 名可见；若没有这行代码，用户不知道当前轨道。
            self.assertIn("pending_command_count=1", rendered)  # 新增代码+ChromeExtensionStage8: 断言 pending 命令计数可见；若没有这行代码，卡住命令不可见。
            self.assertIn("permission_event_count=1", rendered)  # 新增代码+ChromeExtensionStage8: 断言权限事件计数可见；若没有这行代码，授权变化不可见。
            self.assertIn("https://stage8.test/app", rendered)  # 新增代码+ChromeExtensionStage8: 断言 active tab URL 可见；若没有这行代码，终端状态无法肉眼确认页面。
            self.assertEqual(sdk_status["tabs"]["active_tab"]["url"], "https://stage8.test/app")  # 新增代码+ChromeExtensionStage8: 断言 SDK 读到同一 active tab；若没有这行代码，SDK 可能读到不同事实源。

    def test_tool_http_and_cli_expose_provider_status(self) -> None:  # 新增代码+ChromeExtensionStage8: 验证模型工具、HTTP API 和 CLI 都能读取 provider 状态；若没有这行代码，Stage 8 可能漏外部入口。
        from learning_agent.app.http_bridge import create_command_bridge_server  # 新增代码+ChromeExtensionStage8: 导入真实 HTTP bridge 工厂；若没有这行代码，API 端点无法被测试。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+ChromeExtensionStage8: 导入真实浏览器 MCP server；若没有这行代码，browser_provider_status 工具无法被测试。
        from learning_agent.harness.cli import main as harness_cli_main  # 新增代码+ChromeExtensionStage8: 导入 harness CLI 入口；若没有这行代码，provider-status 命令无法被测试。
        class FakeAgent:  # 新增代码+ChromeExtensionStage8: 定义最小 HTTP bridge agent；若没有这个类，HTTP server 没有 workspace 和工具列表。
            def __init__(self, workspace: Path) -> None:  # 新增代码+ChromeExtensionStage8: 初始化 fake agent 工作区；若没有这行代码，bridge 无法读取状态快照。
                self.workspace = workspace  # 新增代码+ChromeExtensionStage8: 保存工作区供 HTTP bridge 使用；若没有这行代码，/browser/providers 会读不到状态。
            def _tool_schema_names(self) -> list[str]:  # 新增代码+ChromeExtensionStage8: 模拟 agent 暴露工具名；若没有这行代码，/health 分支可能调用失败。
                return ["browser_provider_status"]  # 新增代码+ChromeExtensionStage8: 返回最小工具名列表；若没有这行代码，HTTP health 缺少 visible_tools。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ChromeExtensionStage8: 创建隔离工作区；若没有这行代码，测试会污染真实状态。
            workspace = Path(raw_dir)  # 新增代码+ChromeExtensionStage8: 保存工作区路径；若没有这行代码，各入口无法共用状态。
            self._seed_stage8_browser_state(workspace)  # 新增代码+ChromeExtensionStage8: 写入状态输入；若没有这行代码，工具/API/CLI 都无内容。
            browser_server = BrowserAutomationServer(workspace)  # 新增代码+ChromeExtensionStage8: 创建真实浏览器 MCP server；若没有这行代码，无法调用 provider 状态工具。
            tool_output = browser_server.call("browser_provider_status", {})  # 新增代码+ChromeExtensionStage8: 调用模型可见 provider 状态工具；若没有这行代码，schema 和实现可能脱节。
            self.assertIn("browser_provider_status", tool_output)  # 新增代码+ChromeExtensionStage8: 断言工具输出标题存在；若没有这行代码，工具可能返回错误 handler。
            self.assertIn("provider=chrome_extension", tool_output)  # 新增代码+ChromeExtensionStage8: 断言工具显示插件 provider；若没有这行代码，模型无法理解当前轨道。
            cli_output = io.StringIO()  # 新增代码+ChromeExtensionStage8: 准备捕获 CLI 输出；若没有这行代码，CLI 文本无法断言。
            with redirect_stdout(cli_output):  # 新增代码+ChromeExtensionStage8: 捕获 stdout；若没有这行代码，测试输出会污染终端。
                cli_code = harness_cli_main(["provider-status", "--workspace", str(workspace)])  # 新增代码+ChromeExtensionStage8: 调用 provider 状态 CLI；若没有这行代码，命令行入口不会被验证。
            self.assertEqual(cli_code, 0)  # 新增代码+ChromeExtensionStage8: 断言 CLI 成功退出；若没有这行代码，文本断言可能掩盖失败码。
            self.assertIn("chrome_extension", cli_output.getvalue())  # 新增代码+ChromeExtensionStage8: 断言 CLI 输出 provider；若没有这行代码，外部 agent 不能用 CLI 判断状态。
            http_server = create_command_bridge_server(agent=FakeAgent(workspace), host="127.0.0.1", port=0)  # 新增代码+ChromeExtensionStage8: 创建随机端口 HTTP bridge；若没有这行代码，API 端点没有真实协议测试。
            thread = threading.Thread(target=http_server.serve_forever, daemon=True)  # 新增代码+ChromeExtensionStage8: 准备后台 HTTP 服务线程；若没有这行代码，测试会阻塞在 serve_forever。
            thread.start()  # 新增代码+ChromeExtensionStage8: 启动 HTTP 服务；若没有这行代码，请求会连接失败。
            self.addCleanup(http_server.server_close)  # 新增代码+ChromeExtensionStage8: 测试结束释放监听 socket；若没有这行代码，资源检查会看到未关闭端口。
            self.addCleanup(http_server.shutdown)  # 新增代码+ChromeExtensionStage8: 测试结束先停止 HTTP 服务；若没有这行代码，后台线程可能残留。
            host, port = http_server.server_address  # 新增代码+ChromeExtensionStage8: 读取实际监听地址；若没有这行代码，端口 0 场景不知道请求哪里。
            connection = http.client.HTTPConnection(host, port, timeout=5)  # 新增代码+ChromeExtensionStage8: 创建 HTTP 客户端；若没有这行代码，无法请求 API。
            connection.request("GET", "/browser/providers")  # 新增代码+ChromeExtensionStage8: 请求 provider 状态端点；若没有这行代码，HTTP 路由不会被覆盖。
            response = connection.getresponse()  # 新增代码+ChromeExtensionStage8: 读取 HTTP 响应；若没有这行代码，无法断言状态码。
            payload = json.loads(response.read().decode("utf-8"))  # 新增代码+ChromeExtensionStage8: 解析 JSON 响应；若没有这行代码，只能比较脆弱字符串。
            connection.close()  # 新增代码+ChromeExtensionStage8: 主动关闭 HTTP 客户端连接；若没有这行代码，单测会留下未关闭 socket 警告。
            self.assertEqual(response.status, 200)  # 新增代码+ChromeExtensionStage8: 断言 HTTP 端点成功；若没有这行代码，404/500 可能被正文掩盖。
            self.assertEqual(payload["provider_status"]["tabs"]["active_tab"]["url"], "https://stage8.test/app")  # 新增代码+ChromeExtensionStage8: 断言 HTTP 返回 active tab；若没有这行代码，API 可能只返回空壳。


if __name__ == "__main__":  # 新增代码+ChromeExtensionStage8: 支持直接运行本测试文件；若没有这行代码，单文件排查不方便。
    unittest.main()  # 新增代码+ChromeExtensionStage8: 直接运行时启动 unittest；若没有这行代码，python 文件本身不会执行测试。
