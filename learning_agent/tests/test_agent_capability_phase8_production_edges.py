import tempfile  # 新增代码+Phase8ProductionEdges: 使用临时目录隔离测试文件；如果没有这行代码，测试会把 launcher 和 manifest 写进真实项目目录。
import unittest  # 新增代码+Phase8ProductionEdges: 使用项目现有 unittest 测试框架；如果没有这行代码，Phase 8 的回归用例无法运行。
from pathlib import Path  # 新增代码+Phase8ProductionEdges: 使用 Path 处理跨平台路径；如果没有这行代码，测试中的路径拼接会更脆弱。

from learning_agent.app.chrome_status_renderer import render_chrome_status  # 新增代码+Phase8ProductionEdges: 导入 /chrome 渲染器验证管理提示；如果没有这行代码，UI 差距无法被自动化测试锁住。
from learning_agent.browser_extension_host.manifest_installer import ChromeNativeHostInstaller, MemoryNativeHostRegistryAdapter, build_native_host_manifest  # 新增代码+Phase8ProductionEdges: 导入 native host 安装器；如果没有这行代码，生产级 launcher 和多浏览器注册差距无法被测试覆盖。
from learning_agent.computer_use.controller import build_default_computer_use_backend  # 新增代码+Phase8ProductionEdges: 导入 Computer Use 后端工厂；如果没有这行代码，Windows 后端默认安全关闭的行为无法被测试覆盖。


class AgentCapabilityPhase8ProductionEdgesTests(unittest.TestCase):  # 新增代码+Phase8ProductionEdges: 定义 Phase 8 生产边缘能力测试；如果没有这个测试类，后续补齐 ClaudeCode 差距时容易只写说明不写保护。
    def test_native_host_manifest_uses_launcher_file_and_reports_multi_browser_targets(self) -> None:  # 新增代码+Phase8ProductionEdges: 验证 manifest 指向 launcher 并暴露多浏览器注册目标；如果没有这个测试，Chrome 可能继续尝试直接执行裸 Python 脚本。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase8ProductionEdges: 创建临时工作目录；如果没有这行代码，测试文件会污染真实 memory 目录。
            workspace = Path(raw_dir)  # 新增代码+Phase8ProductionEdges: 把临时目录转成 Path；如果没有这行代码，后续路径操作不统一。
            registry = MemoryNativeHostRegistryAdapter()  # 新增代码+Phase8ProductionEdges: 使用内存注册表避免碰真实 Windows registry；如果没有这行代码，测试可能改用户电脑配置。
            installer = ChromeNativeHostInstaller(workspace / "native_host", registry_adapter=registry)  # 新增代码+Phase8ProductionEdges: 创建安装器实例；如果没有这行代码，无法验证安装生命周期。
            manifest_path = build_native_host_manifest(workspace / "native_host", "abc123", "python", workspace / "native_host.py")  # 新增代码+Phase8ProductionEdges: 生成 manifest 和 launcher；如果没有这行代码，测试没有实际文件可检查。
            manifest = manifest_path.read_text(encoding="utf-8")  # 新增代码+Phase8ProductionEdges: 读取 manifest 文本；如果没有这行代码，断言无法确认 path 字段。
            status = installer.status()  # 新增代码+Phase8ProductionEdges: 读取安装器状态；如果没有这行代码，多浏览器 registry 目标不会被验证。
        self.assertIn(".cmd", manifest)  # 新增代码+Phase8ProductionEdges: manifest 应指向 Windows 可执行 launcher；如果没有这个断言，裸 `.py` 路径回归不会被发现。
        self.assertIn("registry_targets", status)  # 新增代码+Phase8ProductionEdges: 状态应暴露所有浏览器注册目标；如果没有这个断言，/chrome 无法提示多浏览器覆盖范围。
        self.assertGreaterEqual(len(status["registry_targets"]), 3)  # 新增代码+Phase8ProductionEdges: 至少应覆盖 Chrome/Edge/Brave 等多个 Chromium 家族入口；如果没有这个断言，能力仍会停留在单 Chrome key。

    def test_chrome_status_renderer_includes_management_actions(self) -> None:  # 新增代码+Phase8ProductionEdges: 验证 /chrome 输出管理动作提示；如果没有这个测试，UI 可能仍只是只读状态页。
        text = render_chrome_status({"browser": {"provider_status": {"native_host": {"connected": False}}}})  # 新增代码+Phase8ProductionEdges: 用最小快照渲染 /chrome；如果没有这行代码，断言没有输出对象。
        self.assertIn("Chrome Actions", text)  # 新增代码+Phase8ProductionEdges: /chrome 必须有管理动作区；如果没有这个断言，用户仍不知道下一步怎么操作。
        self.assertIn("/chrome install-preview", text)  # 新增代码+Phase8ProductionEdges: /chrome 必须提示安全安装预览；如果没有这个断言，用户可能直接尝试危险注册。
        self.assertIn("/chrome repair", text)  # 新增代码+Phase8ProductionEdges: /chrome 必须提示修复入口；如果没有这个断言，排障仍要靠猜。

    def test_default_computer_use_backend_stays_safe_without_enable_env(self) -> None:  # 新增代码+Phase8ProductionEdges: 验证 Computer Use 默认不会启用真实桌面控制；如果没有这个测试，后端工厂可能在用户不知情时接管鼠标键盘。
        backend = build_default_computer_use_backend(environ={})  # 新增代码+Phase8ProductionEdges: 用空环境创建默认后端；如果没有这行代码，无法模拟安全默认值。
        status = backend.status()  # 新增代码+Phase8ProductionEdges: 读取后端状态；如果没有这行代码，断言无法判断是否安全关闭。
        self.assertFalse(status["available"])  # 新增代码+Phase8ProductionEdges: 默认后端必须不可用；如果没有这个断言，真实桌面控制可能默认打开。
        self.assertEqual(status["backend"], "unavailable")  # 新增代码+Phase8ProductionEdges: 默认后端必须明确是 unavailable；如果没有这个断言，用户可能误以为已经有真实 OS 控制。


if __name__ == "__main__":  # 新增代码+Phase8ProductionEdges: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式调试。
    unittest.main()  # 新增代码+Phase8ProductionEdges: 启动 unittest 主程序；如果没有这行代码，直接运行文件不会执行测试。
