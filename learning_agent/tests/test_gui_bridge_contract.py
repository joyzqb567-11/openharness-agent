import tempfile  # 新增代码+DesktopGUIBridgeTest: 使用标准库创建临时工作区；如果没有这行代码，unittest 无法获得 pytest 的 tmp_path fixture。
import unittest  # 新增代码+DesktopGUIBridgeTest: 使用 unittest.TestCase 让计划中的 unittest 命令能发现测试；如果没有这行代码，测试函数不会被 unittest 收集。
from pathlib import Path  # 新增代码+DesktopGUIBridgeTest: 使用 Path 构造临时工作区；如果没有这行代码，测试无法用统一路径对象。


class GuiBridgeContractTests(unittest.TestCase):  # 新增代码+DesktopGUIBridgeTest: 测试类段开始，承载 GUI bridge 合同；如果没有这个类，unittest 不会执行合同检查。
    def test_gui_bootstrap_payload_contains_snapshot_and_flags(self) -> None:  # 新增代码+DesktopGUIBridgeTest: 验证 GUI 启动所需字段；如果没有这段测试，桌面壳可能拿不到状态和功能开关。
        from learning_agent.app.gui_bridge import build_gui_bootstrap_payload  # 新增代码+DesktopGUIBridgeTest: 导入计划新增的 bridge helper；如果没有这行代码，测试无法锁定后端合同。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIBridgeTest: 创建自动清理的临时目录；如果没有这行代码，测试会污染真实项目目录。
            workspace = Path(directory)  # 新增代码+DesktopGUIBridgeTest: 把临时目录转换成 Path；如果没有这行代码，合同无法验证路径规范化。
            payload = build_gui_bootstrap_payload(workspace)  # 新增代码+DesktopGUIBridgeTest: 生成 GUI bootstrap 响应；如果没有这行代码，无法验证结构。

        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUIBridgeTest: 确认 bridge 返回成功；如果没有这行断言，失败 payload 可能误过。
        self.assertEqual(payload["workspace"], str(workspace.resolve()))  # 新增代码+DesktopGUIBridgeTest: 确认工作区路径可展示；如果没有这行断言，GUI 可能显示错误项目。
        self.assertEqual(payload["app"]["schema_version"], 1)  # 新增代码+DesktopGUIBridgeTest: 锁定响应协议版本；如果没有这行断言，前端无法安全兼容。
        self.assertIn("snapshot", payload)  # 新增代码+DesktopGUIBridgeTest: 确认包含统一状态快照；如果没有这行断言，GUI 需要旁路读状态。
        self.assertIs(payload["feature_flags"]["event_polling"], True)  # 新增代码+DesktopGUIBridgeTest: 确认事件轮询可用；如果没有这行断言，前端无法知道刷新方式。
    # 新增代码+DesktopGUIBridgeTest: 测试方法结束；如果没有这个边界说明，初学者不容易看出 bootstrap 合同测试范围。
# 新增代码+DesktopGUIBridgeTest: 测试类段结束，GuiBridgeContractTests 到此结束；如果没有这个边界说明，用户不容易看出本文件只测 GUI bridge 合同。


if __name__ == "__main__":  # 新增代码+DesktopGUIBridgeTest: 允许直接运行本测试文件；如果没有这行代码，手动调试时只能通过模块方式启动。
    unittest.main()  # 新增代码+DesktopGUIBridgeTest: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
