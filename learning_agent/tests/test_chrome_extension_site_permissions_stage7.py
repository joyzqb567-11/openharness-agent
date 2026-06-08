"""双轨浏览器 Stage 7 Chrome 插件站点权限测试。"""  # 新增代码+ChromeExtensionStage7: 说明本文件锁定插件 origin 权限边界；若没有这行代码，维护者不知道测试保护什么安全目标。
from __future__ import annotations  # 新增代码+ChromeExtensionStage7: 延迟解析类型注解；若没有这行代码，局部 fake 类型在旧解释顺序下更脆弱。

from learning_agent.tests.support import *  # 新增代码+ChromeExtensionStage7: 复用项目测试基类、Path、tempfile、threading、time、json 等公共支撑；若没有这行代码，测试会重复基础导入。


class ChromeExtensionSitePermissionsStage7Tests(LearningAgentTestBase):  # 新增代码+ChromeExtensionStage7: 定义 Stage 7 测试集合；若没有这个类，unittest 不会收集插件权限测试。
    def test_site_permissions_are_origin_and_action_scoped(self) -> None:  # 新增代码+ChromeExtensionStage7: 验证权限按 origin 和动作类型分开；若没有这行代码，read 授权可能误放行 click/type。
        from learning_agent.browser.site_permissions import BrowserSitePermissions  # 新增代码+ChromeExtensionStage7: 导入站点权限模型；若没有这行代码，测试无法驱动权限层。
        permissions = BrowserSitePermissions(strict=True)  # 新增代码+ChromeExtensionStage7: 创建严格权限管理器；若没有这行代码，未授权默认会被放行。
        permissions.grant("https://example.test/path", permissions=["read"])  # 新增代码+ChromeExtensionStage7: 只授权 read；若没有这行代码，无法验证动作级隔离。
        self.assertTrue(permissions.is_allowed("https://example.test/next", "read"))  # 新增代码+ChromeExtensionStage7: 同 origin 的 read 应允许；若没有这行代码，正常读取会被误拒。
        self.assertFalse(permissions.is_allowed("https://example.test/next", "click"))  # 新增代码+ChromeExtensionStage7: read 不应自动允许 click；若没有这行代码，权限会过度放宽。
        permissions.grant("https://example.test", permissions=["click"])  # 新增代码+ChromeExtensionStage7: 单独授权 click；若没有这行代码，无法验证追加权限。
        self.assertTrue(permissions.is_allowed("https://example.test/next", "click"))  # 新增代码+ChromeExtensionStage7: click 授权后应允许；若没有这行代码，授权不会生效。
        self.assertFalse(permissions.is_allowed("https://evil.test/", "read"))  # 新增代码+ChromeExtensionStage7: 其他 origin 仍拒绝；若没有这行代码，授权可能跨站泄漏。
        self.assertEqual(permissions.events[-1]["permissions"], ["click"])  # 新增代码+ChromeExtensionStage7: 权限变更应留事件；若没有这行代码，审计无法知道谁放行了动作。

    def test_provider_blocks_read_and_write_without_origin_permission(self) -> None:  # 新增代码+ChromeExtensionStage7: 验证未授权 origin 不能读页面或写页面；若没有这行代码，插件连接后权限会默认全放开。
        from learning_agent.browser.providers.chrome_extension import ChromeExtensionProvider  # 新增代码+ChromeExtensionStage7: 导入插件 provider；若没有这行代码，测试无法覆盖 adapter 权限门禁。
        from learning_agent.browser.site_permissions import BrowserSitePermissions  # 新增代码+ChromeExtensionStage7: 导入权限模型；若没有这行代码，provider 没有严格权限对象。
        from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+ChromeExtensionStage7: 导入 bridge 状态；若没有这行代码，provider 无法读取当前 tab URL。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ChromeExtensionStage7: 使用临时目录隔离状态文件；若没有这行代码，测试会污染真实 memory。
            bridge = ChromeExtensionBridgeState(Path(raw_dir) / "bridge_state.json")  # 新增代码+ChromeExtensionStage7: 创建 bridge；若没有这行代码，provider 没有 tab context。
            bridge.record_connection(extension_id="stage7-extension")  # 新增代码+ChromeExtensionStage7: 模拟插件已连接；若没有这行代码，health 不会可用。
            bridge.update_tabs_context({"tabs": [{"id": 7, "url": "https://locked.test/app", "title": "Locked", "active": True}]})  # 新增代码+ChromeExtensionStage7: 写入当前 tab URL；若没有这行代码，权限检查不知道当前 origin。
            bridge.update_page_snapshot({"tab": {"id": 7, "url": "https://locked.test/app", "title": "Locked", "active": True}, "page": {"visibleText": "secret page", "elements": []}})  # 新增代码+ChromeExtensionStage7: 写入页面快照；若没有这行代码，snapshot 成功路径没有数据。
            provider = ChromeExtensionProvider(bridge, command_timeout_seconds=0.2, site_permissions=BrowserSitePermissions(strict=True))  # 新增代码+ChromeExtensionStage7: 创建严格权限 provider；若没有这行代码，未授权操作不会被拦截。
            status = provider.execute_tool("browser_extension_status", {})  # 新增代码+ChromeExtensionStage7: 状态工具应始终可用；若没有这行代码，无法证明未授权 origin 至少可看状态。
            with self.assertRaises(PermissionError):  # 新增代码+ChromeExtensionStage7: 未授权读取应失败；若没有这行代码，页面内容可能被直接读出。
                provider.execute_tool("browser_snapshot", {})  # 新增代码+ChromeExtensionStage7: 尝试读取页面快照；若没有这行代码，read 门禁没有输入。
            with self.assertRaises(PermissionError):  # 新增代码+ChromeExtensionStage7: 未授权点击应失败；若没有这行代码，写动作可能默认放行。
                provider.execute_tool("browser_click", {"selector": "#ok", "page_id": "chrome-tab-7"})  # 新增代码+ChromeExtensionStage7: 尝试点击当前 origin；若没有这行代码，click 门禁没有输入。
        self.assertIn("browser_extension_status", status)  # 新增代码+ChromeExtensionStage7: 断言状态仍能读取；若没有这行代码，未授权状态边界不可见。

    def test_provider_allows_only_granted_action_for_current_origin(self) -> None:  # 新增代码+ChromeExtensionStage7: 验证授权 read 不会自动授权 click，授权 click 后才执行；若没有这行代码，动作级授权可能失效。
        from learning_agent.browser.providers.chrome_extension import ChromeExtensionProvider  # 新增代码+ChromeExtensionStage7: 导入插件 provider；若没有这行代码，测试无法覆盖真实 adapter。
        from learning_agent.browser.site_permissions import BrowserSitePermissions  # 新增代码+ChromeExtensionStage7: 导入权限模型；若没有这行代码，测试无法配置授权。
        from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+ChromeExtensionStage7: 导入 bridge；若没有这行代码，provider 无法排队命令。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ChromeExtensionStage7: 使用临时目录隔离状态；若没有这行代码，测试会污染真实 memory。
            bridge = ChromeExtensionBridgeState(Path(raw_dir) / "bridge_state.json")  # 新增代码+ChromeExtensionStage7: 创建 bridge；若没有这行代码，provider 无法读取 context。
            bridge.record_connection(extension_id="stage7-extension")  # 新增代码+ChromeExtensionStage7: 模拟插件连接；若没有这行代码，provider 不可用。
            bridge.update_tabs_context({"tabs": [{"id": 7, "url": "https://allowed.test/form", "title": "Form", "active": True}]})  # 新增代码+ChromeExtensionStage7: 写入 active tab；若没有这行代码，权限检查缺 origin。
            bridge.update_page_snapshot({"tab": {"id": 7, "url": "https://allowed.test/form", "title": "Form", "active": True}, "page": {"visibleText": "form page", "elements": []}})  # 新增代码+ChromeExtensionStage7: 写入快照；若没有这行代码，read 成功路径没有内容。
            permissions = BrowserSitePermissions(strict=True)  # 新增代码+ChromeExtensionStage7: 创建严格权限对象；若没有这行代码，授权隔离无法验证。
            permissions.grant("https://allowed.test", permissions=["read"])  # 新增代码+ChromeExtensionStage7: 只授权读取；若没有这行代码，snapshot 应该失败。
            provider = ChromeExtensionProvider(bridge, command_timeout_seconds=1.0, site_permissions=permissions)  # 新增代码+ChromeExtensionStage7: 创建带权限的 provider；若没有这行代码，执行路径无法检查授权。
            snapshot = provider.execute_tool("browser_snapshot", {})  # 新增代码+ChromeExtensionStage7: read 授权后读取页面；若没有这行代码，无法证明 read 放行。
            with self.assertRaises(PermissionError):  # 新增代码+ChromeExtensionStage7: click 未授权时必须拒绝；若没有这行代码，read 会误放行 click。
                provider.execute_tool("browser_click", {"selector": "#ok", "page_id": "chrome-tab-7"})  # 新增代码+ChromeExtensionStage7: 尝试点击；若没有这行代码，click 拦截没有输入。
            permissions.grant("https://allowed.test", permissions=["click"])  # 新增代码+ChromeExtensionStage7: 单独授权点击；若没有这行代码，click 应继续失败。
            def responder() -> None:  # 新增代码+ChromeExtensionStage7: 定义扩展结果模拟器；若没有这行代码，provider 会等待到超时。
                deadline = time.time() + 1.0  # 新增代码+ChromeExtensionStage7: 设置最多等待 1 秒；若没有这行代码，测试失败时可能卡住。
                while time.time() < deadline:  # 新增代码+ChromeExtensionStage7: 轮询 pending 命令；若没有这行代码，模拟器无法发现 provider 入队。
                    pending = bridge.pending_commands()  # 新增代码+ChromeExtensionStage7: 读取 pending 队列；若没有这行代码，无法取得 command_id。
                    if pending:  # 新增代码+ChromeExtensionStage7: 出现命令后回填结果；若没有这行代码，空列表也会被误处理。
                        command = pending[0]  # 新增代码+ChromeExtensionStage7: 取第一条命令；若没有这行代码，回填结果缺 command_id。
                        bridge.record_command_result({"action": "action_result", "command_id": command["command_id"], "tool_name": command["tool_name"], "ok": True, "result": {"visibleText": "clicked", "tab": {"id": 7, "url": "https://allowed.test/form", "title": "Form", "active": True}}})  # 新增代码+ChromeExtensionStage7: 模拟 click 成功结果；若没有这行代码，provider 无法完成。
                        return  # 新增代码+ChromeExtensionStage7: 回填后退出线程；若没有这行代码，可能重复记录结果。
                    time.sleep(0.02)  # 新增代码+ChromeExtensionStage7: 避免忙等；若没有这行代码，测试会浪费 CPU。
            thread = threading.Thread(target=responder)  # 新增代码+ChromeExtensionStage7: 创建模拟扩展线程；若没有这行代码，provider execute_tool 会超时。
            thread.start()  # 新增代码+ChromeExtensionStage7: 启动模拟扩展；若没有这行代码，结果不会出现。
            result = provider.execute_tool("browser_click", {"selector": "#ok", "page_id": "chrome-tab-7"})  # 新增代码+ChromeExtensionStage7: click 授权后执行；若没有这行代码，放行路径没有被验证。
            thread.join(timeout=2.0)  # 新增代码+ChromeExtensionStage7: 等待模拟线程结束；若没有这行代码，后台线程可能拖到下个测试。
        self.assertIn("browser_snapshot 成功", snapshot)  # 新增代码+ChromeExtensionStage7: 断言 read 授权生效；若没有这行代码，snapshot 可能是假成功。
        self.assertIn("browser_click 成功", result)  # 新增代码+ChromeExtensionStage7: 断言 click 授权后成功；若没有这行代码，授权放行没有证据。

    def test_server_site_grant_syncs_extension_provider_permissions(self) -> None:  # 新增代码+ChromeExtensionStage7: 验证统一 browser_site_grant 会同步插件 provider；若没有这行代码，权限工具和插件轨道会分裂。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+ChromeExtensionStage7: 导入真实 server；若没有这行代码，无法覆盖生产授权工具。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ChromeExtensionStage7: 使用临时 workspace 隔离状态；若没有这行代码，测试会污染真实 memory。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+ChromeExtensionStage7: 创建真实 server；若没有这行代码，browser_site_grant 没有执行主体。
            server.chrome_extension_bridge.record_connection(extension_id="stage7-extension")  # 新增代码+ChromeExtensionStage7: 模拟插件连接；若没有这行代码，provider 状态不可用。
            server.chrome_extension_bridge.update_tabs_context({"tabs": [{"id": 7, "url": "https://sync.test/form", "title": "Sync", "active": True}]})  # 新增代码+ChromeExtensionStage7: 写入当前 tab；若没有这行代码，provider 权限检查缺 origin。
            server.browser_site_grant({"action": "enable_strict", "confirm_site_grant": True})  # 新增代码+ChromeExtensionStage7: 开启严格权限；若没有这行代码，未授权默认放行。
            with self.assertRaises(PermissionError):  # 新增代码+ChromeExtensionStage7: 未授权点击必须拒绝；若没有这行代码，同步前门禁没有验证。
                server.chrome_extension_provider.execute_tool("browser_click", {"selector": "#ok", "page_id": "chrome-tab-7"})  # 新增代码+ChromeExtensionStage7: 直接通过 provider 尝试点击；若没有这行代码，插件权限未授权路径没有输入。
            grant_result = server.browser_site_grant({"action": "grant", "origin": "https://sync.test/form", "permissions": ["click"], "confirm_site_grant": True})  # 新增代码+ChromeExtensionStage7: 通过统一工具授权 click；若没有这行代码，server 同步路径没有输入。
            allowed = server.chrome_extension_provider.site_permissions.is_allowed("https://sync.test/next", "click")  # 新增代码+ChromeExtensionStage7: 检查 provider 权限对象是否已同步；若没有这行代码，只能看返回文本。
        self.assertIn("permissions=click", grant_result)  # 新增代码+ChromeExtensionStage7: 断言返回文本说明授权的权限类型；若没有这行代码，用户不知道 grant 了什么。
        self.assertTrue(allowed)  # 新增代码+ChromeExtensionStage7: 断言插件 provider 确实获得 click 权限；若没有这行代码，server 和 provider 可能仍分裂。
