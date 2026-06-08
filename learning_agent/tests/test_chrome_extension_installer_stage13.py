import json  # 新增代码+Phase1Installer: 用来读取 manifest JSON；如果没有这行代码，测试无法确认 manifest 内容是否正确。
import tempfile  # 新增代码+Phase1Installer: 用临时目录隔离测试文件；如果没有这行代码，测试会污染真实项目目录。
import unittest  # 新增代码+Phase1Installer: 使用项目现有 unittest 测试框架；如果没有这行代码，测试类无法运行。
from pathlib import Path  # 新增代码+Phase1Installer: 用 Path 管理 Windows/临时路径；如果没有这行代码，路径拼接会变得脆弱。


class ChromeExtensionInstallerStage13Tests(unittest.TestCase):  # 新增代码+Phase1Installer: 验证生产级 native host 安装器；如果没有这个测试类，Phase 1 的安装生命周期没有自动化证据。
    def test_installer_reports_manifest_and_registry_lifecycle_without_real_registry(self) -> None:  # 新增代码+Phase1Installer: 锁定 dry-run/fake registry 生命周期；如果没有这个测试，真实注册表写入风险会失控。
        from learning_agent.browser_extension_host.manifest_installer import ChromeNativeHostInstaller, MemoryNativeHostRegistryAdapter  # 新增代码+Phase1Installer: 导入待实现安装器和内存注册表；如果没有这行代码，测试无法驱动新 API。

        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase1Installer: 创建临时目录承载 manifest；如果没有这行代码，测试会写入真实工作区。
            workspace = Path(raw_dir)  # 新增代码+Phase1Installer: 把临时目录转成 Path；如果没有这行代码，后续路径操作不统一。
            registry = MemoryNativeHostRegistryAdapter()  # 新增代码+Phase1Installer: 使用内存注册表替代真实 Windows registry；如果没有这行代码，测试可能改动用户电脑。
            installer = ChromeNativeHostInstaller(workspace / "native_host", registry_adapter=registry)  # 新增代码+Phase1Installer: 创建安装器；如果没有这行代码，无法测试安装流程。
            status_before = installer.status()  # 新增代码+Phase1Installer: 查询初始状态；如果没有这行代码，无法证明未安装状态可见。
            install_result = installer.install(extension_id="abc123", python_executable="python", host_script=workspace / "native_host.py", dry_run=True)  # 新增代码+Phase1Installer: 执行 dry-run 安装；如果没有这行代码，无法证明默认安全不写真实注册表。
            status_after_dry_run = installer.status()  # 新增代码+Phase1Installer: 查询 dry-run 后状态；如果没有这行代码，无法确认 dry-run 不改变注册表。
            install_real = installer.install(extension_id="abc123", python_executable="python", host_script=workspace / "native_host.py", dry_run=False)  # 新增代码+Phase1Installer: 用内存注册表执行真实安装路径；如果没有这行代码，无法验证注册表适配器写入。
            status_after_install = installer.status()  # 新增代码+Phase1Installer: 查询安装后状态；如果没有这行代码，无法证明 registry_registered 状态。
            uninstall_result = installer.uninstall(dry_run=False)  # 新增代码+Phase1Installer: 执行卸载；如果没有这行代码，无法验证回滚路径。
            status_after_uninstall = installer.status()  # 新增代码+Phase1Installer: 查询卸载后状态；如果没有这行代码，无法证明 registry_missing 状态。

        self.assertEqual(status_before["state"], "not_installed")  # 新增代码+Phase1Installer: 初始应报告未安装；如果没有这行断言，初始状态错误也不会暴露。
        self.assertEqual(install_result["action"], "install")  # 新增代码+Phase1Installer: 安装结果要标明动作；如果没有这行断言，审计记录不稳定。
        self.assertTrue(install_result["dry_run"])  # 新增代码+Phase1Installer: dry-run 结果必须显式为 true；如果没有这行断言，用户可能误以为已写注册表。
        self.assertEqual(status_after_dry_run["state"], "manifest_created")  # 新增代码+Phase1Installer: dry-run 只生成 manifest；如果没有这行断言，dry-run 可能偷偷写 registry。
        self.assertEqual(install_real["registry_value"], str(install_real["manifest_path"]))  # 新增代码+Phase1Installer: 注册表值应指向 manifest；如果没有这行断言，Chrome 找不到 native host。
        self.assertEqual(status_after_install["state"], "registry_registered")  # 新增代码+Phase1Installer: 安装后应报告已注册；如果没有这行断言，状态工具无法给用户信心。
        self.assertEqual(uninstall_result["action"], "uninstall")  # 新增代码+Phase1Installer: 卸载结果要标明动作；如果没有这行断言，回滚审计不清楚。
        self.assertEqual(status_after_uninstall["state"], "registry_missing")  # 新增代码+Phase1Installer: 卸载后 manifest 还在但 registry 不在；如果没有这行断言，状态会误导用户。

    def test_repair_hint_explains_next_action_for_each_install_state(self) -> None:  # 新增代码+Phase1Installer: 验证修复建议可读；如果没有这个测试，用户遇到失败只能看生硬状态码。
        from learning_agent.browser_extension_host.manifest_installer import ChromeNativeHostInstaller, MemoryNativeHostRegistryAdapter  # 新增代码+Phase1Installer: 导入安装器和 fake registry；如果没有这行代码，测试无法隔离真实系统。

        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase1Installer: 创建临时 workspace；如果没有这行代码，测试会污染项目目录。
            installer = ChromeNativeHostInstaller(Path(raw_dir) / "native_host", registry_adapter=MemoryNativeHostRegistryAdapter())  # 新增代码+Phase1Installer: 创建未安装状态安装器；如果没有这行代码，无法获取 repair hint。
            hint = installer.repair_hint()  # 新增代码+Phase1Installer: 获取修复建议；如果没有这行代码，无法验证面向小白用户的提示。

        self.assertIn("native host manifest", hint)  # 新增代码+Phase1Installer: 提示必须说明 manifest；如果没有这行断言，用户可能不知道缺哪一步。
        self.assertIn("browser_extension_install", hint)  # 新增代码+Phase1Installer: 提示必须告诉用户下一步工具；如果没有这行断言，agent 不知道如何恢复。

    def test_manifest_keeps_compatible_schema(self) -> None:  # 新增代码+Phase1Installer: 保护旧 manifest 生成函数兼容；如果没有这个测试，Phase 1 可能破坏 Stage 5 路线。
        from learning_agent.browser_extension_host.manifest_installer import build_native_host_manifest  # 新增代码+Phase1Installer: 导入旧函数；如果没有这行代码，无法保护向后兼容。

        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase1Installer: 创建临时目录；如果没有这行代码，manifest 会写入真实目录。
            manifest_path = build_native_host_manifest(Path(raw_dir), "abc123", "python", Path(raw_dir) / "native_host.py")  # 新增代码+Phase1Installer: 生成 manifest；如果没有这行代码，无法读取 schema。
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))  # 新增代码+Phase1Installer: 读取 manifest JSON；如果没有这行代码，无法断言字段。

        self.assertEqual(manifest["name"], "com.openharness.learning_agent")  # 新增代码+Phase1Installer: host 名称必须稳定；如果没有这行断言，Chrome registry key 会失配。
        self.assertEqual(manifest["type"], "stdio")  # 新增代码+Phase1Installer: native messaging 类型必须是 stdio；如果没有这行断言，Chrome 无法通信。
        self.assertIn("chrome-extension://abc123/", manifest["allowed_origins"])  # 新增代码+Phase1Installer: allowed origin 必须包含扩展 id；如果没有这行断言，扩展无法连接 host。

    def test_browser_server_exposes_safe_extension_install_tools(self) -> None:  # 新增代码+Phase1Installer: 验证生产 MCP server 暴露安全安装工具；如果没有这个测试，安装器只能被 Python 代码调用，agent 无法使用。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer, TOOLS  # 新增代码+Phase1Installer: 导入真实 server 和工具 schema；如果没有这行代码，无法验证模型可见工具面。
        from learning_agent.browser_extension_host.manifest_installer import MemoryNativeHostRegistryAdapter  # 新增代码+Phase25RegistryTestIsolation: 导入内存 registry 适配器；如果没有这行代码，测试会受用户真实 HKCU registry 状态影响。

        tool_names = {tool["name"] for tool in TOOLS}  # 新增代码+Phase1Installer: 收集工具名；如果没有这行代码，断言会重复遍历 schema。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase1Installer: 创建临时 workspace；如果没有这行代码，server 会写入真实 memory。
            server = BrowserAutomationServer(Path(raw_dir), native_host_registry_adapter=MemoryNativeHostRegistryAdapter())  # 修改代码+Phase25RegistryTestIsolation: 创建带内存 registry 的浏览器 server；如果没有这行代码，真实已注册 native host 会让临时 workspace 状态变成 registry_mismatch。
            preview = server.call("browser_extension_install", {"extension_id": "abc123", "dry_run": True})  # 新增代码+Phase1Installer: 调用 dry-run 安装工具；如果没有这行代码，无法证明默认安全预览。
            status = server.call("browser_extension_status", {})  # 修改代码+Phase1Installer: 查询扩展状态；如果没有这行代码，无法证明 status 包含 installer 信息。
            hint = server.call("browser_extension_repair_hint", {})  # 新增代码+Phase1Installer: 调用修复建议工具；如果没有这行代码，无法验证小白可读恢复路径。

        self.assertIn("browser_extension_install", tool_names)  # 新增代码+Phase1Installer: schema 必须暴露安装工具；如果没有这行断言，模型可能看不到工具。
        self.assertIn("browser_extension_uninstall", tool_names)  # 新增代码+Phase1Installer: schema 必须暴露卸载工具；如果没有这行断言，用户无法回滚注册。
        self.assertIn("browser_extension_repair_hint", tool_names)  # 新增代码+Phase1Installer: schema 必须暴露修复建议；如果没有这行断言，排障体验不完整。
        self.assertIn("dry_run=true", preview)  # 新增代码+Phase1Installer: 安装预览必须显示 dry-run；如果没有这行断言，用户可能误解是否写 registry。
        self.assertIn("installer_state=manifest_created", status)  # 新增代码+Phase1Installer: 状态必须包含安装器状态；如果没有这行断言，/chrome UI 无法展示安装进度。
        self.assertIn("browser_extension_install", hint)  # 新增代码+Phase1Installer: 修复建议必须给出下一步工具；如果没有这行断言，agent 不知道怎么继续。


if __name__ == "__main__":  # 新增代码+Phase1Installer: 允许直接运行本测试文件；如果没有这行代码，手动排查不方便。
    unittest.main()  # 新增代码+Phase1Installer: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
