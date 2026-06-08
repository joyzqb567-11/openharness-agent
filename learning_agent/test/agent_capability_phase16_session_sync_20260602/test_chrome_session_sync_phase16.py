import tempfile  # 新增代码+Phase16SessionSyncClosure: 创建隔离临时目录；如果没有这行代码，测试会污染真实 runtime queue。
import unittest  # 新增代码+Phase16SessionSyncClosure: 使用项目现有 unittest 框架；如果没有这行代码，本文件无法定义测试。
from pathlib import Path  # 新增代码+Phase16SessionSyncClosure: 管理 Windows/临时路径；如果没有这行代码，路径拼接会更脆弱。

from learning_agent.app.chrome_status_renderer import render_chrome_status  # 新增代码+Phase16SessionSyncClosure: 验证 /chrome 用户可见输出；如果没有这行代码，状态页可能缺少 browser prompt 证据。
from learning_agent.app.interactive import run_chrome_terminal_command  # 新增代码+Phase16SessionSyncClosure: 复用真实 /chrome 终端入口；如果没有这行代码，session sync 自检可能绕过用户路径。
from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+Phase16SessionSyncClosure: 复用真实 bridge 入队逻辑；如果没有这行代码，测试会绕过 native host 侧核心代码。
from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+Phase16SessionSyncClosure: 验证 durable runtime queue；如果没有这行代码，无法证明浏览器 prompt 已入队。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+Phase16SessionSyncClosure: 验证统一状态快照；如果没有这行代码，/chrome 和队列可能分裂。


class ChromeSessionSyncPhase16Tests(unittest.TestCase):  # 新增代码+Phase16SessionSyncClosure: 定义 Phase 16 session sync 测试集合；如果没有这段测试，浏览器 prompt 闭环没有红线。
    def test_browser_prompt_creates_structured_durable_runtime_command(self) -> None:  # 新增代码+Phase16SessionSyncClosure: 验证浏览器 prompt 进入 durable queue 且保留结构化来源；如果没有这段测试，URL/title/tab/selected 可能只混进文本。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase16SessionSyncClosure: 创建临时目录；如果没有这行代码，测试会复用真实 memory。
            workspace = Path(temp_dir) / "learning_agent"  # 新增代码+Phase16SessionSyncClosure: 模拟真实 learning_agent workspace；如果没有这行代码，路径兼容问题无法覆盖。
            bridge = ChromeExtensionBridgeState(workspace / "memory" / "chrome_extension_bridge.json")  # 新增代码+Phase16SessionSyncClosure: 创建 bridge 状态对象；如果没有这行代码，无法保存 browser prompt 摘要。
            queue = RuntimeCommandQueue(workspace / "memory" / "runtime")  # 新增代码+Phase16SessionSyncClosure: 创建 durable runtime queue；如果没有这行代码，prompt 无法入队。
            result = bridge.enqueue_browser_prompt(queue, {"prompt": "帮我总结当前网页", "url": "https://example.com/page", "title": "Example Title", "selected_text": "hello" * 1000, "tab_id": "chrome-tab-7"})  # 新增代码+Phase16SessionSyncClosure: 模拟扩展推送浏览器侧 prompt；如果没有这行代码，无法验证真实入队 payload。
            self.assertEqual(result["mode"], "browser_prompt")  # 新增代码+Phase16SessionSyncClosure: bridge 返回必须说明来源模式；如果没有这行断言，调用方无法区分普通 prompt。
            commands = queue.list_commands()  # 新增代码+Phase16SessionSyncClosure: 读取 durable commands；如果没有这行代码，无法证明入队成功。
            self.assertEqual(len(commands), 1)  # 新增代码+Phase16SessionSyncClosure: 必须只创建一条命令；如果没有这行断言，重复入队会漏掉。
            command = commands[0]  # 新增代码+Phase16SessionSyncClosure: 取唯一命令；如果没有这行代码，后续断言会重复索引。
            self.assertEqual(command.mode, "prompt")  # 新增代码+Phase16SessionSyncClosure: 仍保持 prompt 模式便于主循环消费；如果没有这行断言，session runtime 可能看不懂新模式。
            browser_prompt = command.payload.get("browser_prompt", {})  # 新增代码+Phase16SessionSyncClosure: 读取结构化浏览器来源；如果没有这行代码，断言会重复路径。
            self.assertEqual(browser_prompt.get("url"), "https://example.com/page")  # 新增代码+Phase16SessionSyncClosure: URL 必须机器可读保存；如果没有这行断言，verifier 只能解析文本。
            self.assertEqual(browser_prompt.get("title"), "Example Title")  # 新增代码+Phase16SessionSyncClosure: 标题必须机器可读保存；如果没有这行断言，状态审计缺上下文。
            self.assertEqual(browser_prompt.get("tab_id"), "chrome-tab-7")  # 新增代码+Phase16SessionSyncClosure: tab id 必须保存；如果没有这行断言，后续无法关联标签页。
            self.assertLessEqual(len(str(browser_prompt.get("selected_text", ""))), 2000)  # 新增代码+Phase16SessionSyncClosure: 选中文本必须限长；如果没有这行断言，大段页面内容可能撑爆队列。
            self.assertIn("帮我总结当前网页", command.payload.get("text", ""))  # 新增代码+Phase16SessionSyncClosure: 模型可见文本仍必须包含用户意图；如果没有这行断言，主循环会收到空任务。

    def test_chrome_status_shows_last_browser_prompt_evidence(self) -> None:  # 新增代码+Phase16SessionSyncClosure: 验证 /chrome 显示最近浏览器 prompt 证据；如果没有这段测试，用户看不到 session sync 是否入队。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase16SessionSyncClosure: 创建临时目录；如果没有这行代码，测试会污染真实状态。
            workspace = Path(temp_dir) / "learning_agent"  # 新增代码+Phase16SessionSyncClosure: 模拟真实 workspace；如果没有这行代码，状态快照路径可能不一致。
            bridge = ChromeExtensionBridgeState(workspace / "memory" / "chrome_extension_bridge.json")  # 新增代码+Phase16SessionSyncClosure: 创建 bridge 状态对象；如果没有这行代码，无法写入 last_browser_prompt。
            queue = RuntimeCommandQueue(workspace / "memory" / "runtime")  # 新增代码+Phase16SessionSyncClosure: 创建 runtime queue；如果没有这行代码，browser prompt 不会持久化。
            bridge.enqueue_browser_prompt(queue, {"prompt": "打开这个页面的信息", "url": "https://sync.example/page", "title": "Sync Page", "selected_text": "selected", "tab_id": "chrome-tab-8"})  # 新增代码+Phase16SessionSyncClosure: 写入一条浏览器 prompt；如果没有这行代码，状态页没有证据可显示。
            text = render_chrome_status(build_status_snapshot(workspace))  # 新增代码+Phase16SessionSyncClosure: 生成真实 /chrome 状态文本；如果没有这行代码，无法验证用户可见输出。
            self.assertIn("last_browser_prompt_id=", text)  # 新增代码+Phase16SessionSyncClosure: 状态页必须显示队列 command id；如果没有这行断言，用户无法定位 durable 命令。
            self.assertIn("last_browser_prompt_url=https://sync.example/page", text)  # 新增代码+Phase16SessionSyncClosure: 状态页必须显示来源 URL；如果没有这行断言，用户不知道 prompt 来自哪个页面。

    def test_chrome_session_sync_selftest_uses_terminal_command_path(self) -> None:  # 新增代码+Phase16SessionSyncClosure: 验证真实 /chrome 命令能模拟浏览器 prompt 入队；如果没有这段测试，真实终端验收缺少可操作入口。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase16SessionSyncClosure: 创建临时目录；如果没有这行代码，测试会污染真实 runtime queue。
            workspace = Path(temp_dir) / "learning_agent"  # 新增代码+Phase16SessionSyncClosure: 模拟真实 learning_agent workspace；如果没有这行代码，终端命令路径可能测错。
            workspace.mkdir()  # 新增代码+Phase16SessionSyncClosure: 创建 workspace；如果没有这行代码，状态目录没有根路径。
            text = run_chrome_terminal_command(workspace, "/chrome session-sync-selftest")  # 新增代码+Phase16SessionSyncClosure: 执行真实终端自检命令；如果没有这行代码，无法验证用户可触发路径。
            self.assertIn("chrome_session_sync_selftest", text)  # 新增代码+Phase16SessionSyncClosure: 输出必须标明 session sync 自检；如果没有这行断言，未知命令也可能误通过。
            self.assertIn("last_browser_prompt_url=https://session-sync.local/selftest", text)  # 新增代码+Phase16SessionSyncClosure: 输出必须显示模拟来源 URL；如果没有这行断言，用户看不到闭环证据。
            self.assertIn("queue_command_exists=true", text)  # 新增代码+Phase16SessionSyncClosure: 输出必须证明 durable command 存在；如果没有这行断言，自检可能只写 bridge 摘要。


if __name__ == "__main__":  # 新增代码+Phase16SessionSyncClosure: 允许直接运行本测试文件；如果没有这行代码，初学者不能单独执行本阶段测试。
    unittest.main()  # 新增代码+Phase16SessionSyncClosure: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
