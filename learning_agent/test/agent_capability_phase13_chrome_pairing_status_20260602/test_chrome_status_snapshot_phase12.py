import tempfile  # 新增代码+Phase12ChromeStatusGuide: 创建临时工作区；如果没有这行代码，快照测试会污染真实项目状态。
import unittest  # 新增代码+Phase12ChromeStatusGuide: 使用 unittest 测试框架；如果没有这行代码，本文件无法定义测试用例。
import json  # 新增代码+Phase13ChromePairingGuide: 写入临时 bridge 状态 JSON；如果没有这行代码，测试无法模拟扩展配对状态。
from pathlib import Path  # 新增代码+Phase12ChromeStatusGuide: 用 Path 拼接临时路径；如果没有这行代码，Windows 路径处理容易出错。

from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+Phase12ChromeStatusGuide: 导入真实状态快照入口；如果没有这行代码，测试无法证明 /chrome 能读到 installer 状态。


class ChromeStatusSnapshotPhase12Tests(unittest.TestCase):  # 新增代码+Phase12ChromeStatusGuide: 定义 Phase 12 的状态快照测试；如果没有这段测试，真实 /chrome 可能只有假数据能显示向导。
    def test_status_snapshot_includes_native_host_installer_state(self) -> None:  # 新增代码+Phase12ChromeStatusGuide: 验证快照包含 native host 安装器状态；如果没有这段测试，渲染器拿不到下一步依据。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase12ChromeStatusGuide: 创建隔离目录；如果没有这行代码，测试会读写真实 memory。
            workspace = Path(temp_dir) / "learning_agent"  # 新增代码+Phase12ChromeStatusGuide: 模拟真实 bat 入口的 learning_agent 工作区；如果没有这行代码，无法覆盖生产路径形态。
            workspace.mkdir()  # 新增代码+Phase12ChromeStatusGuide: 创建工作区目录；如果没有这行代码，快照路径会不存在。
            snapshot = build_status_snapshot(workspace)  # 新增代码+Phase12ChromeStatusGuide: 构建真实状态快照；如果没有这行代码，测试没有观测对象。
            native_host = snapshot["browser"]["provider_status"]["native_host"]  # 新增代码+Phase12ChromeStatusGuide: 取 native host 区块；如果没有这行代码，断言会散落在深层字典里。
            self.assertEqual(native_host["installer_state"], "not_installed")  # 新增代码+Phase12ChromeStatusGuide: 新工作区应报告未安装；如果没有这行断言，/chrome 初始引导会失真。
            self.assertIn("manifest_path", native_host)  # 新增代码+Phase12ChromeStatusGuide: 快照必须包含 manifest 路径；如果没有这行断言，用户无法定位生成文件。
            self.assertIn("registry_targets", native_host)  # 新增代码+Phase12ChromeStatusGuide: 快照必须包含 registry 目标；如果没有这行断言，用户无法知道安装覆盖范围。

    def test_status_snapshot_includes_extension_pairing_and_session_sync(self) -> None:  # 新增代码+Phase13ChromePairingGuide: 验证快照包含 extension pairing/session sync；如果没有这段测试，/chrome 没有真实配对数据源。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase13ChromePairingGuide: 创建隔离目录；如果没有这行代码，测试会污染真实 bridge 状态。
            workspace = Path(temp_dir) / "learning_agent"  # 新增代码+Phase13ChromePairingGuide: 模拟 bat 入口传入的 learning_agent 工作区；如果没有这行代码，路径兼容问题无法覆盖。
            memory_dir = workspace / "memory"  # 新增代码+Phase13ChromePairingGuide: 定位 memory 目录；如果没有这行代码，bridge 文件路径会散落写死。
            memory_dir.mkdir(parents=True)  # 新增代码+Phase13ChromePairingGuide: 创建 memory 目录；如果没有这行代码，写 bridge 文件会失败。
            bridge_path = memory_dir / "chrome_extension_bridge.json"  # 新增代码+Phase13ChromePairingGuide: 定位扩展 bridge 状态文件；如果没有这行代码，测试无法模拟真实状态来源。
            bridge_path.write_text(json.dumps({"connected": True, "extension_id": "ext-1", "last_seen_at": 12345, "pairing": {"device_id": "device-1", "session_id": "session-1", "extension_id": "ext-1", "allowed_origins": ["chrome-extension://ext-1/"]}}, ensure_ascii=False), encoding="utf-8")  # 新增代码+Phase13ChromePairingGuide: 写入脱敏 pairing 状态；如果没有这行代码，快照无法读到配对数据。
            snapshot = build_status_snapshot(workspace)  # 新增代码+Phase13ChromePairingGuide: 构建真实状态快照；如果没有这行代码，测试没有观测对象。
            extension = snapshot["browser"]["provider_status"]["chrome_extension"]  # 新增代码+Phase13ChromePairingGuide: 取扩展状态区块；如果没有这行代码，断言路径重复且难读。
            self.assertTrue(extension["paired"])  # 新增代码+Phase13ChromePairingGuide: 快照必须显示已配对；如果没有这行断言，/chrome 无法判断 session sync。
            self.assertEqual(extension["device_id"], "device-1")  # 新增代码+Phase13ChromePairingGuide: 快照必须显示 device id；如果没有这行断言，用户无法定位配对设备。
            self.assertEqual(extension["session_id"], "session-1")  # 新增代码+Phase13ChromePairingGuide: 快照必须显示 session id；如果没有这行断言，session sync 不可审计。
            self.assertEqual(extension["allowed_origin_count"], 1)  # 新增代码+Phase13ChromePairingGuide: 快照必须显示 allowed origin 数量；如果没有这行断言，配对边界不可见。


if __name__ == "__main__":  # 新增代码+Phase12ChromeStatusGuide: 允许直接运行本测试文件；如果没有这行代码，初学者无法单独执行测试。
    unittest.main()  # 新增代码+Phase12ChromeStatusGuide: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
