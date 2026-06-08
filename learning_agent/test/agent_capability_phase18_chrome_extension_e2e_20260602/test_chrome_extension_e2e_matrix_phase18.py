import tempfile  # 新增代码+Phase18ChromeExtensionE2E: 创建隔离临时目录；如果没有这行代码，测试会污染真实 learning_agent memory。
import unittest  # 新增代码+Phase18ChromeExtensionE2E: 使用项目现有 unittest 框架；如果没有这行代码，本测试文件无法定义和运行测试用例。
from pathlib import Path  # 新增代码+Phase18ChromeExtensionE2E: 用 Path 管理 Windows 路径；如果没有这行代码，manifest 和 bridge 路径拼接容易出错。

from learning_agent.app.chrome_status_renderer import render_chrome_status  # 新增代码+Phase18ChromeExtensionE2E: 导入 /chrome 渲染器；如果没有这行代码，测试无法确认用户菜单会显示 Phase 18 入口。
from learning_agent.app.interactive import run_chrome_terminal_command  # 新增代码+Phase18ChromeExtensionE2E: 复用真实 /chrome 终端入口；如果没有这行代码，测试可能绕过用户实际会执行的路径。
from learning_agent.browser_extension_host.manifest_installer import MemoryNativeHostRegistryAdapter  # 新增代码+Phase18ChromeExtensionE2E: 用内存 registry 隔离真实系统；如果没有这行代码，单测可能误碰 Windows registry。
from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+Phase18ChromeExtensionE2E: 读取 durable queue 证据；如果没有这行代码，测试无法确认 browser prompt 真的入队。


class ChromeExtensionE2EMatrixPhase18Tests(unittest.TestCase):  # 新增代码+Phase18ChromeExtensionE2E: 定义 Phase 18 端到端证据测试集合；如果没有这段测试，真实扩展验收链路缺少自动化红线。
    def test_terminal_e2e_check_reports_manifest_pairing_prompt_and_real_extension_boundary(self) -> None:  # 新增代码+Phase18ChromeExtensionE2E: 验证终端命令输出五类端到端证据；如果没有这段测试，Phase 18 可能把局部自检误说成真实 E2E。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase18ChromeExtensionE2E: 创建临时工作区；如果没有这行代码，测试会读写真实项目 memory。
            workspace = Path(temp_dir) / "learning_agent"  # 新增代码+Phase18ChromeExtensionE2E: 模拟真实 bat 传入的 learning_agent 目录；如果没有这行代码，路径兼容性无法覆盖。
            workspace.mkdir()  # 新增代码+Phase18ChromeExtensionE2E: 创建工作区目录；如果没有这行代码，manifest 和 queue 目录没有根路径。
            registry = MemoryNativeHostRegistryAdapter()  # 新增代码+Phase18ChromeExtensionE2E: 创建 fake registry；如果没有这行代码，测试无法安全验证 native host 状态。
            text = run_chrome_terminal_command(workspace, "/chrome extension-e2e-check", registry_adapter=registry)  # 新增代码+Phase18ChromeExtensionE2E: 执行真实终端子命令；如果没有这行代码，后续断言没有行为来源。
            self.assertIn("chrome_extension_e2e_check", text)  # 新增代码+Phase18ChromeExtensionE2E: 输出必须标明 Phase 18 检查；如果没有这行断言，未知命令也可能误通过。
            self.assertIn("manifest_ok=true", text)  # 新增代码+Phase18ChromeExtensionE2E: 必须证明 native host manifest 存在且可读；如果没有这行断言，Chrome 找不到 host 也可能漏检。
            self.assertIn("launcher_ok=true", text)  # 新增代码+Phase18ChromeExtensionE2E: 必须证明 launcher 存在；如果没有这行断言，manifest 可能指向不可执行入口。
            self.assertIn("pairing_completed=true", text)  # 新增代码+Phase18ChromeExtensionE2E: 必须证明 pairing 请求能闭合；如果没有这行断言，配对链路可能停在 pending。
            self.assertIn("browser_prompt_queued=true", text)  # 新增代码+Phase18ChromeExtensionE2E: 必须证明浏览器 prompt 进入 durable queue；如果没有这行断言，session sync 可能只写状态不入队。
            self.assertIn("real_extension_connected=false", text)  # 新增代码+Phase18ChromeExtensionE2E: 没有真实扩展连接时必须诚实标 false；如果没有这行断言，模拟会被误报成真实连接。
            queue = RuntimeCommandQueue(workspace / "memory" / "runtime")  # 新增代码+Phase18ChromeExtensionE2E: 打开自检写入的 runtime queue；如果没有这行代码，无法二次确认 durable 命令存在。
            self.assertTrue(any(command.payload.get("browser_prompt", {}).get("url") == "https://extension-e2e.local/selftest" for command in queue.list_commands()))  # 新增代码+Phase18ChromeExtensionE2E: 检查 queue 中确有 Phase 18 来源 URL；如果没有这行断言，输出可能只是文本假证据。

    def test_chrome_actions_list_includes_extension_e2e_check(self) -> None:  # 新增代码+Phase18ChromeExtensionE2E: 验证 /chrome 菜单暴露 Phase 18 命令；如果没有这段测试，用户需要猜测隐藏子命令。
        text = render_chrome_status({"browser": {"provider_status": {"chrome_extension": {"paired": False}, "native_host": {"installer_state": "manifest_created"}}}})  # 新增代码+Phase18ChromeExtensionE2E: 构造最小 Chrome 状态；如果没有这行代码，断言没有可见菜单文本。
        self.assertIn("risk=low confirm=no command=/chrome extension-e2e-check", text)  # 新增代码+Phase18ChromeExtensionE2E: E2E 检查应是低风险无确认命令；如果没有这行断言，用户不清楚它不会写 registry。


if __name__ == "__main__":  # 新增代码+Phase18ChromeExtensionE2E: 允许直接运行本测试文件；如果没有这行代码，小白用户不能单独执行 Phase 18 测试。
    unittest.main()  # 新增代码+Phase18ChromeExtensionE2E: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
