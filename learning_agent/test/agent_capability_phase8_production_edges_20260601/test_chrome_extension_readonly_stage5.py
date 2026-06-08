"""双轨浏览器 Stage 5 Chrome 插件只读 MVP 测试。"""  # 新增代码+ChromeExtensionStage5: 说明本文件锁定 Chrome 插件只读接入；若没有这行代码，维护者不知道这些测试保护什么边界。
from __future__ import annotations  # 新增代码+ChromeExtensionStage5: 延迟解析类型注解；若没有这行代码，局部 fake 类型在旧解释顺序下更脆弱。

from learning_agent.tests.support import *  # 新增代码+ChromeExtensionStage5: 复用项目测试基类、Path、tempfile、json 等公共支撑；若没有这行代码，测试会重复基础导入。


class ChromeExtensionReadonlyStage5Tests(LearningAgentTestBase):  # 新增代码+ChromeExtensionStage5: 定义 Stage 5 测试集合；若没有这个类，unittest 不会收集插件只读测试。
    def test_extension_assets_exist_and_avoid_sensitive_browser_apis(self) -> None:  # 新增代码+ChromeExtensionStage5: 验证插件文件存在且不触碰敏感浏览器 API；若没有这行代码，扩展可能从第一版就越界。
        extension_dir = TEST_ROOT / "chrome_extension"  # 新增代码+ChromeExtensionStage5: 定位扩展目录；若没有这行代码，测试无法读取交付文件。
        expected_files = ["manifest.json", "background.js", "content_script.js", "page_bridge.js", "options.html", "options.js"]  # 新增代码+ChromeExtensionStage5: 固定最小插件文件清单；若没有这行代码，缺文件不会被发现。
        for file_name in expected_files:  # 新增代码+ChromeExtensionStage5: 遍历所有必须存在的扩展文件；若没有这行代码，只会检查单个文件。
            self.assertTrue((extension_dir / file_name).is_file(), file_name)  # 新增代码+ChromeExtensionStage5: 断言每个文件存在；若没有这行代码，插件资产缺失不会失败。
        manifest = json.loads((extension_dir / "manifest.json").read_text(encoding="utf-8"))  # 新增代码+ChromeExtensionStage5: 读取并解析 manifest；若没有这行代码，无法验证 Manifest V3 和权限。
        self.assertEqual(manifest.get("manifest_version"), 3)  # 新增代码+ChromeExtensionStage5: 断言使用 Manifest V3；若没有这行代码，旧 manifest 可能无法安装。
        self.assertIn("nativeMessaging", manifest.get("permissions", []))  # 新增代码+ChromeExtensionStage5: 断言插件具备 native messaging 权限；若没有这行代码，扩展无法连接本地 host。
        combined_script = "\n".join((extension_dir / name).read_text(encoding="utf-8") for name in ["background.js", "content_script.js", "page_bridge.js", "options.js"])  # 新增代码+ChromeExtensionStage5: 合并脚本文本便于敏感 API 扫描；若没有这行代码，检查会漏掉某个脚本。
        forbidden_fragments = ["chrome.cookies", "document.cookie", "localStorage", "sessionStorage"]  # 新增代码+ChromeExtensionStage5: 定义本阶段禁止触碰的浏览器敏感 API；若没有这行代码，隐私边界没有测试事实源。
        for fragment in forbidden_fragments:  # 新增代码+ChromeExtensionStage5: 遍历禁止片段；若没有这行代码，只会检查一个 API。
            self.assertNotIn(fragment, combined_script)  # 新增代码+ChromeExtensionStage5: 断言脚本没有读取敏感 API；若没有这行代码，插件可能读取 cookie 或 storage。

    def test_message_protocol_rejects_write_actions_and_sanitizes_tabs(self) -> None:  # 新增代码+ChromeExtensionStage5: 验证 native host 协议只允许只读动作；若没有这行代码，Stage 5 可能提前开放写动作。
        from learning_agent.browser_extension_host.message_protocol import build_host_response  # 新增代码+ChromeExtensionStage5: 导入 host 协议响应构建器；若没有这行代码，测试无法驱动协议层。
        write_message = {"action": "click", "selector": "#danger"}  # 新增代码+ChromeExtensionStage5: 构造应被拒绝的点击消息；若没有这行代码，写动作拒绝没有样本。
        rejected = build_host_response(write_message)  # 新增代码+ChromeExtensionStage5: 让协议处理写动作；若没有这行代码，无法检查拒绝结果。
        self.assertFalse(rejected["ok"])  # 新增代码+ChromeExtensionStage5: 断言写动作不会成功；若没有这行代码，协议可能误放行点击。
        self.assertIn("read-only", rejected["error"])  # 新增代码+ChromeExtensionStage5: 断言错误说明只读边界；若没有这行代码，调用方不知道为何拒绝。
        readonly_message = {"action": "tabs_context", "tabs": [{"id": 1, "url": "https://example.com", "title": "Example", "active": True, "cookie": "secret"}]}  # 新增代码+ChromeExtensionStage5: 构造含敏感字段的只读 tabs 消息；若没有这行代码，脱敏规则无输入。
        response = build_host_response(readonly_message)  # 新增代码+ChromeExtensionStage5: 让协议构造 tabs context 响应；若没有这行代码，无法验证只读成功。
        encoded = json.dumps(response, ensure_ascii=False)  # 新增代码+ChromeExtensionStage5: 转成 JSON 文本便于扫描敏感字段；若没有这行代码，断言只能检查局部对象。
        self.assertTrue(response["ok"])  # 新增代码+ChromeExtensionStage5: 断言 tabs_context 是允许的只读动作；若没有这行代码，协议可能过度拒绝。
        self.assertIn("https://example.com", encoded)  # 新增代码+ChromeExtensionStage5: 断言 URL 摘要保留；若没有这行代码，context 读到的信息不可用。
        self.assertNotIn("secret", encoded)  # 新增代码+ChromeExtensionStage5: 断言敏感字段值被丢弃；若没有这行代码，cookie 可能进入 host 响应。
        self.assertNotIn("cookie", encoded.lower())  # 新增代码+ChromeExtensionStage5: 断言敏感字段名也不进入响应；若没有这行代码，响应结构会暴露隐私线索。

    def test_bridge_state_and_provider_expose_readonly_context(self) -> None:  # 新增代码+ChromeExtensionStage5: 验证 bridge state 和 provider 只读输出；若没有这行代码，provider 可能只是文件存在没有运行时能力。
        from learning_agent.browser.providers.chrome_extension import ChromeExtensionProvider  # 新增代码+ChromeExtensionStage5: 导入待实现插件 provider；若没有这行代码，测试无法覆盖 provider。
        from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+ChromeExtensionStage5: 导入 bridge 状态对象；若没有这行代码，provider 没有可读状态。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ChromeExtensionStage5: 使用临时目录隔离 bridge 状态文件；若没有这行代码，测试会污染真实 memory。
            bridge = ChromeExtensionBridgeState(Path(raw_dir) / "bridge_state.json")  # 新增代码+ChromeExtensionStage5: 创建文件支持的 bridge state；若没有这行代码，状态无法落盘。
            provider = ChromeExtensionProvider(bridge)  # 新增代码+ChromeExtensionStage5: 用 bridge 创建插件 provider；若没有这行代码，测试没有被测 provider。
            self.assertFalse(provider.health().available)  # 新增代码+ChromeExtensionStage5: 断言默认未连接不可用；若没有这行代码，Router 可能误选插件。
            bridge.record_connection(extension_id="stage5-extension")  # 新增代码+ChromeExtensionStage5: 模拟扩展已连接；若没有这行代码，provider 健康状态不会变为可用。
            bridge.update_tabs_context({"tabs": [{"id": 7, "url": "https://example.com/app", "title": "App", "active": True}]})  # 新增代码+ChromeExtensionStage5: 写入只读标签页上下文；若没有这行代码，provider 无 context 可返回。
            result = provider.execute_tool("browser_tabs_context", {})  # 新增代码+ChromeExtensionStage5: 通过 provider 读取统一 tabs context；若没有这行代码，provider 执行路径未被触发。
        self.assertTrue(provider.health().available)  # 新增代码+ChromeExtensionStage5: 断言连接后 provider 可用；若没有这行代码，健康状态不会被锁定。
        self.assertIn("provider=chrome_extension", result)  # 新增代码+ChromeExtensionStage5: 断言输出来自插件 provider；若没有这行代码，状态难以区分插件和 CDP。
        self.assertIn("tab_id=chrome-tab-7", result)  # 新增代码+ChromeExtensionStage5: 断言 Chrome tab id 被稳定格式化；若没有这行代码，后续审计无法引用 tab。
        self.assertIn("URL=https://example.com/app", result)  # 新增代码+ChromeExtensionStage5: 断言 URL 可见；若没有这行代码，只读 context 没有实际内容。

    def test_server_registers_extension_provider_and_status_tool(self) -> None:  # 新增代码+ChromeExtensionStage5: 验证生产 server 注册插件 provider 和状态工具；若没有这行代码，插件能力无法进入统一运行时。
        from learning_agent.browser.providers.protocol import BrowserProviderKind  # 新增代码+ChromeExtensionStage5: 导入 provider 类型枚举；若没有这行代码，测试会写散落字符串。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer, TOOLS  # 新增代码+ChromeExtensionStage5: 导入真实 server 和工具清单；若没有这行代码，无法覆盖生产入口。
        tool_names = [str(tool.get("name", "")) for tool in TOOLS]  # 新增代码+ChromeExtensionStage5: 收集公开工具名；若没有这行代码，无法确认状态工具是否暴露。
        self.assertIn("browser_extension_status", tool_names)  # 新增代码+ChromeExtensionStage5: 断言插件状态工具公开；若没有这行代码，用户无法查看插件连接状态。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ChromeExtensionStage5: 使用临时 workspace 隔离 server 状态；若没有这行代码，测试会污染真实项目。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+ChromeExtensionStage5: 创建真实 browser server；若没有这行代码，无法检查 registry。
            health = server.browser_provider_registry.health(BrowserProviderKind.CHROME_EXTENSION)  # 新增代码+ChromeExtensionStage5: 查询插件 provider 健康状态；若没有这行代码，无法确认注册结果。
            status = server.call("browser_extension_status", {})  # 新增代码+ChromeExtensionStage5: 通过公开工具读取插件状态；若没有这行代码，状态工具分发未被测试。
        self.assertFalse(health.available)  # 新增代码+ChromeExtensionStage5: 断言默认未连接不可用；若没有这行代码，真实 Chrome 登录态任务可能误走未连接插件。
        self.assertIn("browser_extension_status", status)  # 新增代码+ChromeExtensionStage5: 断言状态输出标题；若没有这行代码，用户难以识别结果。
        self.assertIn("connected=false", status)  # 新增代码+ChromeExtensionStage5: 断言默认未连接；若没有这行代码，状态输出可能误导用户。

    def test_manifest_installer_writes_native_host_manifest_without_registry_side_effects(self) -> None:  # 新增代码+ChromeExtensionStage5: 验证 native host manifest 可生成但不写系统注册表；若没有这行代码，安装准备可能有不可控副作用。
        from learning_agent.browser_extension_host.manifest_installer import build_native_host_manifest  # 新增代码+ChromeExtensionStage5: 导入 manifest 构建函数；若没有这行代码，测试无法验证安装文件格式。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ChromeExtensionStage5: 使用临时目录隔离 manifest 输出；若没有这行代码，测试会写到真实系统路径。
            manifest_path = build_native_host_manifest(Path(raw_dir), extension_id="abcdefghijklmnopabcdefghijklmnop", python_executable="python.exe", host_script=Path(raw_dir) / "native_host.py")  # 新增代码+ChromeExtensionStage5: 生成 native host manifest；若没有这行代码，无法检查输出文件。
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))  # 新增代码+ChromeExtensionStage5: 读取生成的 manifest；若没有这行代码，断言没有数据。
        self.assertEqual(manifest["name"], "com.openharness.learning_agent")  # 新增代码+ChromeExtensionStage5: 断言 native host 名称稳定；若没有这行代码，Chrome 连接名称可能漂移。
        self.assertIn("chrome-extension://abcdefghijklmnopabcdefghijklmnop/", manifest["allowed_origins"])  # 新增代码+ChromeExtensionStage5: 断言只允许指定扩展来源；若没有这行代码，host 可能被任意扩展连接。
        self.assertTrue(str(manifest["path"]).endswith(".cmd"))  # 修改代码+Phase8ProductionEdges: 断言 manifest 指向可执行 launcher；如果没有这行断言，生产级 native host 可能退回裸 Python 脚本。
        self.assertEqual(manifest["metadata"]["python_executable"], "python.exe")  # 新增代码+ChromeExtensionStage5: 断言 Python 解释器只进入元数据不破坏 Chrome manifest path；若没有这行代码，安装器可能把命令行参数塞进 path。
        self.assertTrue(str(manifest["metadata"]["host_script"]).endswith("native_host.py"))  # 新增代码+Phase8ProductionEdges: 断言真实 host 脚本仍保留在元数据里；如果没有这行断言，排障时无法知道 launcher 最终运行哪个脚本。
