import json  # 新增代码+Phase14ChromePairingDiagnose: 写入临时 bridge 状态；如果没有这行代码，测试无法模拟已连接但未完整配对的 Chrome extension。
import tempfile  # 新增代码+Phase14ChromePairingDiagnose: 创建隔离工作区；如果没有这行代码，测试会污染真实 memory。
import unittest  # 新增代码+Phase14ChromePairingDiagnose: 使用项目现有 unittest 框架；如果没有这行代码，本文件无法定义自动化测试。
from pathlib import Path  # 新增代码+Phase14ChromePairingDiagnose: 管理 Windows/临时路径；如果没有这行代码，路径拼接会变得脆弱。

from learning_agent.app.interactive import run_chrome_terminal_command  # 新增代码+Phase14ChromePairingDiagnose: 复用真实 /chrome 终端命令入口；如果没有这行代码，测试可能绕过交互层。


class ChromePairingDiagnosePhase14Tests(unittest.TestCase):  # 新增代码+Phase14ChromePairingDiagnose: 定义 Phase 14 配对诊断测试集合；如果没有这段测试，/chrome pairing-diagnose 没有行为红线。
    def test_pairing_diagnose_reports_missing_bridge_and_pairing_reasons(self) -> None:  # 新增代码+Phase14ChromePairingDiagnose: 验证无 bridge 时能解释 paired=false；如果没有这段测试，用户只会看到空字段。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase14ChromePairingDiagnose: 创建临时目录；如果没有这行代码，诊断测试会读真实项目状态。
            workspace = Path(temp_dir) / "learning_agent"  # 新增代码+Phase14ChromePairingDiagnose: 模拟真实 bat 入口 workspace；如果没有这行代码，路径兼容问题无法覆盖。
            workspace.mkdir()  # 新增代码+Phase14ChromePairingDiagnose: 创建工作区目录；如果没有这行代码，状态快照目录不存在。
            text = run_chrome_terminal_command(workspace, "/chrome pairing-diagnose")  # 新增代码+Phase14ChromePairingDiagnose: 执行诊断命令；如果没有这行代码，无法证明终端命令可用。
            self.assertIn("pairing_diagnose", text)  # 新增代码+Phase14ChromePairingDiagnose: 输出必须标明诊断类型；如果没有这行断言，未知输出也可能误通过。
            self.assertIn("paired=false", text)  # 新增代码+Phase14ChromePairingDiagnose: 输出必须说明当前未配对；如果没有这行断言，用户不知道核心状态。
            self.assertIn("bridge_file_exists=false", text)  # 新增代码+Phase14ChromePairingDiagnose: 输出必须说明 bridge 文件缺失；如果没有这行断言，用户不知道 extension 是否写入状态。
            self.assertIn("reason=bridge_file_missing", text)  # 新增代码+Phase14ChromePairingDiagnose: 输出必须包含缺失原因分类；如果没有这行断言，诊断不可执行。
            self.assertIn("next=", text)  # 新增代码+Phase14ChromePairingDiagnose: 输出必须给下一步；如果没有这行断言，诊断后仍然无法行动。

    def test_pairing_diagnose_reports_partial_pairing_missing_session_fields(self) -> None:  # 新增代码+Phase14ChromePairingDiagnose: 验证部分配对状态会指出缺失字段；如果没有这段测试，session sync 半成功会难以排查。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase14ChromePairingDiagnose: 创建临时目录；如果没有这行代码，测试会污染真实 bridge 文件。
            workspace = Path(temp_dir) / "learning_agent"  # 新增代码+Phase14ChromePairingDiagnose: 模拟真实 learning_agent 工作区；如果没有这行代码，bridge 路径会不真实。
            memory_dir = workspace / "memory"  # 新增代码+Phase14ChromePairingDiagnose: 定位 memory 目录；如果没有这行代码，bridge 文件路径会散落。
            memory_dir.mkdir(parents=True)  # 新增代码+Phase14ChromePairingDiagnose: 创建 memory 目录；如果没有这行代码，写 bridge 状态会失败。
            (memory_dir / "chrome_extension_bridge.json").write_text(json.dumps({"connected": True, "extension_id": "ext-1", "last_seen_at": 12345, "pairing": {"device_id": "device-1", "allowed_origins": []}}, ensure_ascii=False), encoding="utf-8")  # 新增代码+Phase14ChromePairingDiagnose: 写入缺 session_id 的配对状态；如果没有这行代码，无法验证半配对诊断。
            text = run_chrome_terminal_command(workspace, "/chrome pairing-diagnose")  # 新增代码+Phase14ChromePairingDiagnose: 执行诊断命令；如果没有这行代码，无法获取诊断输出。
            self.assertIn("pairing_diagnose", text)  # 新增代码+Phase14ChromePairingDiagnose: 输出必须标明诊断类型；如果没有这行断言，命令可能返回普通状态页。
            self.assertIn("bridge_file_exists=true", text)  # 新增代码+Phase14ChromePairingDiagnose: 输出必须说明 bridge 文件存在；如果没有这行断言，诊断无法区分缺文件和缺字段。
            self.assertIn("connected=true", text)  # 新增代码+Phase14ChromePairingDiagnose: 输出必须说明扩展连接状态；如果没有这行断言，用户不知道 extension 是否在线。
            self.assertIn("device_id=device-1", text)  # 新增代码+Phase14ChromePairingDiagnose: 输出必须保留非敏感 device id；如果没有这行断言，用户无法识别设备。
            self.assertIn("reason=session_id_missing", text)  # 新增代码+Phase14ChromePairingDiagnose: 输出必须指出 session_id 缺失；如果没有这行断言，session sync 失败点不可见。
            self.assertIn("reason=allowed_origins_empty", text)  # 新增代码+Phase14ChromePairingDiagnose: 输出必须指出 allowed origins 为空；如果没有这行断言，扩展来源边界不可见。


if __name__ == "__main__":  # 新增代码+Phase14ChromePairingDiagnose: 允许直接运行本测试文件；如果没有这行代码，初学者无法单独执行测试。
    unittest.main()  # 新增代码+Phase14ChromePairingDiagnose: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
