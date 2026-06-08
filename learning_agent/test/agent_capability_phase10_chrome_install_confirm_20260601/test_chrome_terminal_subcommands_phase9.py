import tempfile  # 新增代码+Phase9ChromeTerminalActions: 创建临时工作区；如果没有这行代码，测试会污染真实项目目录。
import unittest  # 新增代码+Phase9ChromeTerminalActions: 使用 Python 标准测试框架；如果没有这行代码，本文件无法定义自动化验收用例。
from pathlib import Path  # 新增代码+Phase9ChromeTerminalActions: 用 Path 拼接临时目录；如果没有这行代码，Windows 路径处理容易出错。

from learning_agent.app.interactive import run_chrome_terminal_command  # 新增代码+Phase9ChromeTerminalActions: 导入即将实现的 /chrome 子命令入口；如果没有这行代码，测试无法锁定真实终端逻辑。
from learning_agent.browser_extension_host.manifest_installer import MemoryNativeHostRegistryAdapter  # 新增代码+Phase10ChromeInstallConfirm: 导入内存 registry；如果没有这行代码，确认安装测试可能误碰真实 Windows registry。


class ChromeTerminalSubcommandsPhase9Tests(unittest.TestCase):  # 新增代码+Phase9ChromeTerminalActions: 定义 Phase 9 的 /chrome 子命令测试集合；如果没有这段测试，终端动作可能只停留在文案提示。
    def test_install_preview_generates_manifest_launcher_without_registry_write(self) -> None:  # 新增代码+Phase9ChromeTerminalActions: 验证 install-preview 是安全预览；如果没有这段测试，命令可能误写真实 registry。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase9ChromeTerminalActions: 为本测试创建隔离目录；如果没有这行代码，manifest 会落到真实项目目录。
            workspace = Path(temp_dir)  # 新增代码+Phase9ChromeTerminalActions: 把临时目录转成 Path；如果没有这行代码，后续路径拼接不够稳定。
            text = run_chrome_terminal_command(workspace, "/chrome install-preview")  # 新增代码+Phase9ChromeTerminalActions: 执行终端预览命令；如果没有这行代码，测试无法证明命令可用。
            self.assertIn("Chrome Action", text)  # 新增代码+Phase9ChromeTerminalActions: 输出必须是动作结果页；如果没有这行断言，状态页误返回也可能通过。
            self.assertIn("browser_extension_install", text)  # 新增代码+Phase9ChromeTerminalActions: 输出必须说明调用的是安装预览；如果没有这行断言，用户看不懂发生了什么。
            self.assertIn("dry_run=true", text)  # 新增代码+Phase9ChromeTerminalActions: 输出必须明确没有写注册表；如果没有这行断言，安全边界不可见。
            self.assertIn(".cmd", text)  # 新增代码+Phase9ChromeTerminalActions: 输出必须体现 launcher；如果没有这行断言，可能退回裸 Python 脚本入口。
            manifest_path = workspace / "learning_agent" / "memory" / "chrome_native_host" / "com.openharness.learning_agent.json"  # 新增代码+Phase9ChromeTerminalActions: 定位预期 manifest 文件；如果没有这行代码，测试无法检查预览是否真的落盘。
            launcher_path = workspace / "learning_agent" / "memory" / "chrome_native_host" / "com.openharness.learning_agent.cmd"  # 新增代码+Phase9ChromeTerminalActions: 定位预期 launcher 文件；如果没有这行代码，测试无法检查生产化入口。
            self.assertTrue(manifest_path.exists())  # 新增代码+Phase9ChromeTerminalActions: manifest 必须生成；如果没有这行断言，命令可能只打印假成功。
            self.assertTrue(launcher_path.exists())  # 新增代码+Phase9ChromeTerminalActions: launcher 必须生成；如果没有这行断言，Chrome native messaging 入口仍不完整。

    def test_repair_and_uninstall_preview_return_readable_guidance(self) -> None:  # 新增代码+Phase9ChromeTerminalActions: 验证修复和卸载预览都有可读输出；如果没有这段测试，用户遇到问题会缺少下一步。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase9ChromeTerminalActions: 创建独立临时工作区；如果没有这行代码，不同测试之间会互相影响。
            workspace = Path(temp_dir)  # 新增代码+Phase9ChromeTerminalActions: 规范工作区路径；如果没有这行代码，命令入口收到的路径类型不稳定。
            repair_text = run_chrome_terminal_command(workspace, "/chrome repair")  # 新增代码+Phase9ChromeTerminalActions: 执行修复建议命令；如果没有这行代码，测试无法证明 repair 可从终端触发。
            uninstall_text = run_chrome_terminal_command(workspace, "/chrome uninstall-preview")  # 新增代码+Phase9ChromeTerminalActions: 执行卸载预览命令；如果没有这行代码，测试无法证明卸载预览可用。
            self.assertIn("Chrome Action", repair_text)  # 新增代码+Phase9ChromeTerminalActions: repair 输出必须是动作页；如果没有这行断言，用户可能看到混乱状态文本。
            self.assertIn("repair", repair_text)  # 新增代码+Phase9ChromeTerminalActions: repair 输出必须标明动作名称；如果没有这行断言，结果来源不清楚。
            self.assertIn("native host", repair_text)  # 新增代码+Phase9ChromeTerminalActions: repair 输出必须围绕 native host；如果没有这行断言，建议可能偏离 Chrome 安装问题。
            self.assertIn("browser_extension_uninstall", uninstall_text)  # 新增代码+Phase9ChromeTerminalActions: 卸载预览必须标明动作；如果没有这行断言，用户无法区分安装和卸载。
            self.assertIn("dry_run=true", uninstall_text)  # 新增代码+Phase9ChromeTerminalActions: 卸载预览必须明确不删 registry；如果没有这行断言，安全边界不可见。

    def test_unknown_chrome_subcommand_explains_supported_actions(self) -> None:  # 新增代码+Phase9ChromeTerminalActions: 验证未知子命令有友好提示；如果没有这段测试，小白用户输错会像程序坏了。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase9ChromeTerminalActions: 创建临时工作区；如果没有这行代码，测试没有隔离环境。
            text = run_chrome_terminal_command(Path(temp_dir), "/chrome nope")  # 新增代码+Phase9ChromeTerminalActions: 执行未知子命令；如果没有这行代码，无法覆盖错误提示路径。
            self.assertIn("不支持的 /chrome 子命令", text)  # 新增代码+Phase9ChromeTerminalActions: 输出必须明确说明命令不支持；如果没有这行断言，用户不知道哪里输错。
            self.assertIn("/chrome install-preview", text)  # 新增代码+Phase9ChromeTerminalActions: 输出必须给出正确命令；如果没有这行断言，用户不知道下一步怎么改。

    def test_install_preview_uses_existing_learning_agent_workspace_without_double_nesting(self) -> None:  # 新增代码+Phase9ChromeTerminalActions: 验证 bat 入口传 learning_agent 目录时不会重复拼 learning_agent；如果没有这段测试，真实终端会生成难懂的双层路径。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase9ChromeTerminalActions: 创建临时根目录；如果没有这行代码，测试会污染真实文件系统。
            workspace = Path(temp_dir) / "learning_agent"  # 新增代码+Phase9ChromeTerminalActions: 模拟 start_oauth_agent.bat 传入的工作区形态；如果没有这行代码，无法复现真实终端路径问题。
            workspace.mkdir()  # 新增代码+Phase9ChromeTerminalActions: 创建 learning_agent 工作区目录；如果没有这行代码，命令无法在该路径下落盘。
            text = run_chrome_terminal_command(workspace, "/chrome install-preview")  # 新增代码+Phase9ChromeTerminalActions: 执行安装预览；如果没有这行代码，测试无法观察 manifest 路径。
            self.assertIn(str(workspace / "memory" / "chrome_native_host"), text)  # 新增代码+Phase9ChromeTerminalActions: 输出路径必须使用已有 learning_agent 目录；如果没有这行断言，双层路径问题会回归。
            self.assertNotIn("learning_agent\\\\learning_agent", text)  # 新增代码+Phase9ChromeTerminalActions: 输出不能出现双层 learning_agent；如果没有这行断言，真实终端路径会变得混乱。

    def test_install_confirm_refuses_without_explicit_confirmation_token(self) -> None:  # 新增代码+Phase10ChromeInstallConfirm: 验证真实安装必须强确认；如果没有这段测试，用户可能误写 Windows registry。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase10ChromeInstallConfirm: 创建隔离目录；如果没有这行代码，测试会污染真实工作区。
            registry = MemoryNativeHostRegistryAdapter()  # 新增代码+Phase10ChromeInstallConfirm: 使用内存 registry 观察是否写入；如果没有这行代码，测试无法证明拒绝路径没有副作用。
            text = run_chrome_terminal_command(Path(temp_dir), "/chrome install-confirm abcdefghijklmnopabcdefghijklmnop", registry_adapter=registry)  # 新增代码+Phase10ChromeInstallConfirm: 少传确认 token 执行命令；如果没有这行代码，无法覆盖拒绝路径。
            self.assertIn("需要显式确认 token", text)  # 新增代码+Phase10ChromeInstallConfirm: 输出必须告诉用户缺确认 token；如果没有这行断言，小白用户不知道为什么没安装。
            self.assertIn("I_UNDERSTAND_WRITE_REGISTRY", text)  # 新增代码+Phase10ChromeInstallConfirm: 输出必须给出固定 token；如果没有这行断言，用户不知道如何明确授权。
            self.assertEqual(registry.values, {})  # 新增代码+Phase10ChromeInstallConfirm: 拒绝路径不得写 registry；如果没有这行断言，安全门可能只是文案。

    def test_install_confirm_writes_registry_only_after_confirmation_token(self) -> None:  # 新增代码+Phase10ChromeInstallConfirm: 验证带 token 时才执行真实安装路径；如果没有这段测试，install-confirm 可能永远无法真正注册 native host。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase10ChromeInstallConfirm: 创建临时工作区；如果没有这行代码，manifest 会落到真实目录。
            registry = MemoryNativeHostRegistryAdapter()  # 新增代码+Phase10ChromeInstallConfirm: 用 fake registry 替代真实系统；如果没有这行代码，测试会有系统副作用。
            text = run_chrome_terminal_command(Path(temp_dir), "/chrome install-confirm abcdefghijklmnopabcdefghijklmnop I_UNDERSTAND_WRITE_REGISTRY", registry_adapter=registry)  # 新增代码+Phase10ChromeInstallConfirm: 带 token 执行确认安装；如果没有这行代码，无法证明写入路径可用。
            self.assertIn("browser_extension_install_confirm", text)  # 新增代码+Phase10ChromeInstallConfirm: 输出必须标明是确认安装；如果没有这行断言，用户无法区分 preview 和 confirm。
            self.assertIn("dry_run=false", text)  # 新增代码+Phase10ChromeInstallConfirm: 输出必须明确这次不是预览；如果没有这行断言，真实写入边界不可见。
            self.assertEqual(len(registry.values), 4)  # 新增代码+Phase10ChromeInstallConfirm: 应写入 Chrome/Edge/Brave/Chromium 四个 HKCU 目标；如果没有这行断言，多浏览器注册可能退化。
            self.assertTrue(all(value.endswith("com.openharness.learning_agent.json") for value in registry.values.values()))  # 新增代码+Phase10ChromeInstallConfirm: registry 值必须指向 manifest；如果没有这行断言，浏览器会找不到 native host。


if __name__ == "__main__":  # 新增代码+Phase9ChromeTerminalActions: 允许初学者直接运行本测试文件；如果没有这行代码，双击或 python 文件方式不会执行测试。
    unittest.main()  # 新增代码+Phase9ChromeTerminalActions: 启动 unittest；如果没有这行代码，直接运行文件不会产生测试结果。
