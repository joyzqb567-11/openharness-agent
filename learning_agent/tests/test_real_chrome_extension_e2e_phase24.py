import json  # 新增代码+Phase24RealExtensionE2E: 读取 native host manifest 和 bridge JSON；如果没有这行代码，测试无法确认 Chrome 将启动哪个 host、host 会写到哪里。
import os  # 新增代码+Phase24RealExtensionE2E: 临时设置 native host 工作区环境变量；如果没有这行代码，测试无法模拟 Chrome 启动 host 时的真实目录不确定场景。
import tempfile  # 新增代码+Phase24RealExtensionE2E: 创建隔离临时目录；如果没有这行代码，测试会污染真实 learning_agent memory。
import unittest  # 新增代码+Phase24RealExtensionE2E: 使用项目现有 unittest 测试框架；如果没有这行代码，Phase 24 没有自动化验收入口。
from pathlib import Path  # 新增代码+Phase24RealExtensionE2E: 用 Path 管理 Windows 路径；如果没有这行代码，manifest、launcher、memory 路径容易拼错。

from learning_agent.app.chrome_status_renderer import render_chrome_status  # 新增代码+Phase24RealExtensionE2E: 验证用户可见 /chrome 菜单；如果没有这行代码，新增命令可能存在但用户看不到。
from learning_agent.app.interactive import run_chrome_terminal_command  # 新增代码+Phase24RealExtensionE2E: 复用真实终端命令入口；如果没有这行代码，测试可能绕过用户实际会输入的路径。
from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+Phase24RealExtensionE2E: 直接写入真实 bridge 状态模型；如果没有这行代码，测试无法模拟扩展已经连接后的状态。
from learning_agent.browser_extension_host.manifest_installer import build_native_host_manifest  # 新增代码+Phase24RealExtensionE2E: 验证 manifest 和 launcher 生成结果；如果没有这行代码，native host 安装链路缺少 Phase 24 覆盖。
from learning_agent.browser_extension_host.native_host import resolve_native_host_workspace  # 新增代码+Phase24RealExtensionE2E: 验证 host 不再依赖 Chrome 当前工作目录；如果没有这行代码，真实扩展可能把状态写错目录。
from learning_agent.browser_extension_host.native_host import runtime_queue_dir_for_workspace  # 新增代码+Phase24RealExtensionE2E: 验证 runtime queue 目录和 bridge 目录同属一个项目；如果没有这行代码，浏览器 prompt 可能进错队列。


class RealChromeExtensionE2EPhase24Tests(unittest.TestCase):  # 新增代码+Phase24RealExtensionE2E: 定义 Phase 24 测试集；如果没有这段测试，真实扩展闭环缺口会退回人工排查。
    def test_launcher_sets_workspace_environment_for_chrome_started_native_host(self) -> None:  # 新增代码+Phase24RealExtensionE2E: 验证 launcher 写入项目根环境变量；如果没有这段测试，Chrome 启动 host 时仍可能依赖不可靠 cwd。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase24RealExtensionE2E: 创建临时目录承载 manifest；如果没有这行代码，测试会写入真实 native host 目录。
            target_dir = Path(raw_dir) / "native_host"  # 新增代码+Phase24RealExtensionE2E: 定位临时 native host 输出目录；如果没有这行代码，manifest 和 launcher 没有隔离位置。
            host_script = Path(raw_dir) / "repo" / "learning_agent" / "browser_extension_host" / "native_host.py"  # 新增代码+Phase24RealExtensionE2E: 构造真实项目形态的 host 脚本路径；如果没有这行代码，无法验证 workspace 推导。
            manifest_path = build_native_host_manifest(target_dir, "abc123", "python", host_script)  # 新增代码+Phase24RealExtensionE2E: 生成 manifest 和 launcher；如果没有这行代码，断言没有真实文件来源。
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))  # 新增代码+Phase24RealExtensionE2E: 读取 manifest 内容；如果没有这行代码，无法确认 Chrome 看到的 path。
            launcher_path = Path(manifest["path"])  # 新增代码+Phase24RealExtensionE2E: 从 manifest 获取 launcher 路径；如果没有这行代码，测试可能看错文件。
            launcher_text = launcher_path.read_text(encoding="utf-8")  # 新增代码+Phase24RealExtensionE2E: 读取 launcher 脚本；如果没有这行代码，无法验证环境变量是否写入。
        self.assertIn("OPENHARNESS_LEARNING_AGENT_WORKSPACE", launcher_text)  # 新增代码+Phase24RealExtensionE2E: launcher 必须写入工作区环境变量；如果没有这行断言，真实 Chrome cwd 风险不会暴露。
        self.assertIn(str(host_script.parents[1]), launcher_text)  # 新增代码+Phase24RealExtensionE2E: 环境变量必须指向 learning_agent 目录；如果没有这行断言，host 可能写到错误 memory。
        self.assertIn("PYTHONPATH", launcher_text)  # 新增代码+Phase25RealExtensionConnect: launcher 必须写入仓库根目录导入路径；如果没有这行断言，Chrome 启动 host 时会找不到 learning_agent 包。
        self.assertIn(str(host_script.parents[2]), launcher_text)  # 新增代码+Phase25RealExtensionConnect: PYTHONPATH 必须指向 OpenHarness 仓库根目录；如果没有这行断言，native host 会在真实 Chrome 场景导入失败。

    def test_native_host_workspace_resolution_prefers_environment_over_cwd(self) -> None:  # 新增代码+Phase24RealExtensionE2E: 验证 host 优先读取环境变量；如果没有这段测试，真实 Chrome 从任意 cwd 启动时仍可能失效。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase24RealExtensionE2E: 创建隔离目录；如果没有这行代码，环境变量测试会触碰真实项目。
            workspace = Path(raw_dir) / "learning_agent"  # 新增代码+Phase24RealExtensionE2E: 模拟真实 bat 使用的 learning_agent 工作区；如果没有这行代码，路径兼容性无法覆盖。
            workspace.mkdir()  # 新增代码+Phase24RealExtensionE2E: 创建工作区目录；如果没有这行代码，解析函数无法确认目录存在。
            old_value = os.environ.get("OPENHARNESS_LEARNING_AGENT_WORKSPACE")  # 新增代码+Phase24RealExtensionE2E: 保存旧环境变量；如果没有这行代码，测试结束可能污染用户环境。
            os.environ["OPENHARNESS_LEARNING_AGENT_WORKSPACE"] = str(workspace)  # 新增代码+Phase24RealExtensionE2E: 设置 host 应使用的稳定工作区；如果没有这行代码，测试无法模拟 launcher 行为。
            try:  # 新增代码+Phase24RealExtensionE2E: 确保环境变量会恢复；如果没有这行代码，失败时也可能留下测试变量。
                resolved = resolve_native_host_workspace(cwd=Path(raw_dir) / "random_chrome_cwd")  # 新增代码+Phase24RealExtensionE2E: 用错误 cwd 调用解析；如果没有这行代码，无法证明 env 优先级。
                queue_dir = runtime_queue_dir_for_workspace(resolved)  # 新增代码+Phase24RealExtensionE2E: 计算 runtime queue 目录；如果没有这行代码，prompt 入队路径无法验证。
            finally:  # 新增代码+Phase24RealExtensionE2E: 恢复环境变量；如果没有这行代码，测试会影响后续用例。
                if old_value is None:  # 新增代码+Phase24RealExtensionE2E: 旧值不存在时删除变量；如果没有这行代码，环境会被无中生有地留下。
                    os.environ.pop("OPENHARNESS_LEARNING_AGENT_WORKSPACE", None)  # 新增代码+Phase24RealExtensionE2E: 清理测试变量；如果没有这行代码，后续真实运行可能读到临时路径。
                else:  # 新增代码+Phase24RealExtensionE2E: 旧值存在时恢复；如果没有这行代码，用户原有配置会被覆盖。
                    os.environ["OPENHARNESS_LEARNING_AGENT_WORKSPACE"] = old_value  # 新增代码+Phase24RealExtensionE2E: 写回旧配置；如果没有这行代码，环境变量状态不可信。
        self.assertEqual(resolved, workspace)  # 新增代码+Phase24RealExtensionE2E: 解析结果必须等于环境变量工作区；如果没有这行断言，cwd 风险可能隐藏。
        self.assertEqual(queue_dir, workspace / "memory" / "runtime")  # 新增代码+Phase24RealExtensionE2E: runtime queue 必须写回同一 learning_agent memory；如果没有这行断言，Chrome prompt 可能进错目录。

    def test_real_extension_e2e_command_reports_true_when_bridge_has_real_connection_evidence(self) -> None:  # 新增代码+Phase24RealExtensionE2E: 验证真实连接证据会被终端命令识别；如果没有这段测试，Phase 24 命令可能永远只输出 false。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase24RealExtensionE2E: 创建临时 workspace；如果没有这行代码，测试会污染真实 bridge。
            workspace = Path(raw_dir) / "learning_agent"  # 新增代码+Phase24RealExtensionE2E: 模拟真实 learning_agent 工作区；如果没有这行代码，run_chrome_terminal_command 路径可能不一致。
            workspace.mkdir()  # 新增代码+Phase24RealExtensionE2E: 创建工作区目录；如果没有这行代码，bridge 保存会缺父目录。
            bridge = ChromeExtensionBridgeState(workspace / "memory" / "chrome_extension_bridge.json")  # 新增代码+Phase24RealExtensionE2E: 创建 bridge 状态对象；如果没有这行代码，无法模拟扩展真实连接。
            bridge.record_pairing({"extension_id": "ext-real", "device_id": "device-real", "session_id": "session-real", "allowed_origins": ["chrome-extension://ext-real/"]})  # 新增代码+Phase24RealExtensionE2E: 写入真实扩展配对证据；如果没有这行代码，命令不会进入 connected+paired 分支。
            text = run_chrome_terminal_command(workspace, "/chrome real-extension-e2e-check")  # 新增代码+Phase24RealExtensionE2E: 执行用户真实会输入的 Phase 24 命令；如果没有这行代码，新增命令没有终端覆盖。
        self.assertIn("phase24_real_extension_e2e_check", text)  # 新增代码+Phase24RealExtensionE2E: 输出必须包含 Phase 24 标识；如果没有这行断言，未知命令也可能误通过。
        self.assertIn("real_extension_connected=true", text)  # 新增代码+Phase24RealExtensionE2E: 有真实 bridge 连接证据时必须报告 true；如果没有这行断言，连接成功也不可见。
        self.assertIn("paired=true", text)  # 新增代码+Phase24RealExtensionE2E: 配对证据必须可见；如果没有这行断言，session sync 状态不透明。
        self.assertIn("workspace_lock_ok=true", text)  # 新增代码+Phase24RealExtensionE2E: bridge 和 runtime 必须在同一工作区；如果没有这行断言，错目录问题不会暴露。

    def test_chrome_menu_exposes_phase24_real_extension_check(self) -> None:  # 新增代码+Phase24RealExtensionE2E: 验证 /chrome 页面展示 Phase 24 命令；如果没有这段测试，用户可能不知道下一步如何验收真实扩展。
        text = render_chrome_status({"browser": {"provider_status": {"chrome_extension": {"paired": True, "connected": True}, "native_host": {"installer_state": "registry_registered"}}}})  # 新增代码+Phase24RealExtensionE2E: 构造已注册已连接状态；如果没有这行代码，菜单断言没有可渲染输入。
        self.assertIn("/chrome real-extension-e2e-check", text)  # 新增代码+Phase24RealExtensionE2E: 菜单必须露出真实扩展 E2E 检查；如果没有这行断言，入口可能被遗漏。

    def test_phase24_acceptance_scenario_requires_true_event_payload(self) -> None:  # 新增代码+Phase24AcceptancePayload: 验证真实终端场景不会只看 chrome_status_printed 事件；如果没有这段测试，real_extension_e2e=false 也可能误通过。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase24AcceptancePayload: 定位 OpenHarness-main 根目录；如果没有这行代码，测试无法稳定找到验收场景 JSON。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase24_real_chrome_extension_e2e.json"  # 新增代码+Phase24AcceptancePayload: 定位 Phase 24 真实终端场景；如果没有这行代码，测试可能检查错文件。
        interactive_path = project_root / "learning_agent" / "app" / "interactive.py"  # 新增代码+Phase24AcceptancePayload: 定位真实终端交互入口；如果没有这行代码，测试无法确认 chrome_status_printed 会携带输出文本。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase24AcceptancePayload: 读取场景 JSON；如果没有这行代码，测试无法确认 payload 门禁配置。
        interactive_text = interactive_path.read_text(encoding="utf-8")  # 新增代码+Phase24AcceptancePayload: 读取交互入口源码；如果没有这行代码，测试无法锁定 output_text 事件字段。
        required_payload_text = scenario.get("event_payload_contains", [])  # 新增代码+Phase24AcceptancePayload: 取出事件 payload 必含文本列表；如果没有这行代码，断言会散落在多个字段访问里。
        self.assertIn("output_text", interactive_text)  # 新增代码+Phase24AcceptancePayload: chrome_status_printed 必须写入终端输出；如果没有这行断言，场景 payload 门禁可能没有数据来源。
        self.assertIn("real_extension_connected=true", required_payload_text)  # 新增代码+Phase24AcceptancePayload: 必须确认真实扩展连接为 true；如果没有这行断言，连接 false 可能通过。
        self.assertIn("paired=true", required_payload_text)  # 新增代码+Phase24AcceptancePayload: 必须确认 extension/session 已配对；如果没有这行断言，未配对状态可能通过。
        self.assertIn("browser_prompt_queued=true", required_payload_text)  # 新增代码+Phase24AcceptancePayload: 必须确认浏览器 prompt 入队；如果没有这行断言，session sync 半通可能通过。
        self.assertIn("workspace_lock_ok=true", required_payload_text)  # 新增代码+Phase24AcceptancePayload: 必须确认 bridge 和 runtime queue 属于同一工作区；如果没有这行断言，写错目录可能通过。
        self.assertIn("real_extension_e2e=true", required_payload_text)  # 新增代码+Phase24AcceptancePayload: 必须确认最终 E2E 结论为 true；如果没有这行断言，部分成功会被误报完成。


if __name__ == "__main__":  # 新增代码+Phase24RealExtensionE2E: 允许单独运行本测试文件；如果没有这行代码，用户学习时不能直接执行 Phase 24 测试。
    unittest.main()  # 新增代码+Phase24RealExtensionE2E: 启动 unittest；如果没有这行代码，直接运行文件不会执行任何测试。
