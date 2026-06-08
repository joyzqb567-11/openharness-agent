import json  # 新增代码+Phase54WindowsNativeRealityGate: 导入 JSON 工具读取报告和场景；如果没有这行代码，测试无法验证落盘文件内容。
import tempfile  # 新增代码+Phase54WindowsNativeRealityGate: 导入临时目录隔离 native_dependency_report.json；如果没有这行代码，测试可能污染真实运行报告。
import unittest  # 新增代码+Phase54WindowsNativeRealityGate: 导入 unittest 框架；如果没有这行代码，自动化命令无法发现 Phase54 测试。
from pathlib import Path  # 新增代码+Phase54WindowsNativeRealityGate: 导入 Path 处理临时目录和场景路径；如果没有这行代码，路径拼接会更脆弱。

from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase54WindowsNativeRealityGate: 导入真实终端 /computer 命令入口；如果没有这行代码，测试无法证明用户可见命令已接入。
from learning_agent.computer_use.native_reality_gate import PHASE54_WINDOWS_NATIVE_REALITY_GATE_MARKER, PHASE54_WINDOWS_NATIVE_REALITY_GATE_OK_TOKEN, phase54_cli_line, run_phase54_native_reality_gate_contract  # 新增代码+Phase54WindowsNativeRealityGate: 导入预期新增的 Windows 原生现实门禁；如果没有这行代码，红灯会证明 Phase54 尚未实现。


class WindowsComputerUseNativeRealityGatePhase54Tests(unittest.TestCase):  # 新增代码+Phase54WindowsNativeRealityGate: 类段开始，组织 Phase54 依赖门禁测试；如果没有这个类，unittest 不会执行本阶段门禁。
    def test_phase54_reports_missing_dependencies_without_fake_success(self) -> None:  # 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，验证缺依赖时诚实输出 missing/blocked；如果没有这个测试，真实能力可能被 fallback 伪装成通过。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase54WindowsNativeRealityGate: 创建临时目录保存报告；如果没有这行代码，测试会写入真实 memory 目录。
            report = run_phase54_native_reality_gate_contract(platform="win32", module_available=lambda name: name == "uiautomation", command_available=lambda name: name in {"powershell.exe", "dotnet"}, api_available=lambda name: name != "windows_graphics_capture_runtime", output_root=Path(temp_dir))  # 新增代码+Phase54WindowsNativeRealityGate: 用注入探针模拟部分依赖缺失；如果没有这行代码，测试会依赖当前机器安装状态。
            report_path = Path(report["report_path"])  # 新增代码+Phase54WindowsNativeRealityGate: 读取报告路径；如果没有这行代码，无法确认文件真实落盘。
            stored = json.loads(report_path.read_text(encoding="utf-8"))  # 新增代码+Phase54WindowsNativeRealityGate: 读取落盘 JSON；如果没有这行代码，测试只验证内存对象而不是交付物。
        dependency_names = {item["name"] for item in report["dependencies"]}  # 新增代码+Phase54WindowsNativeRealityGate: 收集依赖名称；如果没有这行代码，覆盖项检查会重复复杂表达式。
        self.assertEqual(report["dependency_count"], 9)  # 新增代码+Phase54WindowsNativeRealityGate: 断言九类 Windows 原生依赖都被检查；如果没有这行代码，漏检也可能误过。
        self.assertEqual(stored["dependency_count"], 9)  # 新增代码+Phase54WindowsNativeRealityGate: 断言落盘报告和内存报告一致；如果没有这行代码，文件内容可能缺项。
        self.assertTrue(report["report_written"])  # 新增代码+Phase54WindowsNativeRealityGate: 断言报告已经落盘；如果没有这行代码，native_dependency_report.json 可能缺失。
        self.assertFalse(report["install_attempted"])  # 新增代码+Phase54WindowsNativeRealityGate: 断言本阶段没有自动安装依赖；如果没有这行代码，门禁可能偷偷改系统环境。
        self.assertFalse(report["system_settings_changed"])  # 新增代码+Phase54WindowsNativeRealityGate: 断言本阶段没有修改 Windows 设置；如果没有这行代码，安全边界不明确。
        self.assertFalse(report["actions_expanded"])  # 新增代码+Phase54WindowsNativeRealityGate: 断言本阶段不扩大真实桌面动作面；如果没有这行代码，依赖检查可能被误解为放开控制。
        self.assertIn("uiautomation", dependency_names)  # 新增代码+Phase54WindowsNativeRealityGate: 确认 UIA 依赖进入报告；如果没有这行代码，真实控件树前置条件会漏检。
        self.assertIn("comtypes", dependency_names)  # 新增代码+Phase54WindowsNativeRealityGate: 确认 comtypes 依赖进入报告；如果没有这行代码，UIAutomation COM 路径会漏检。
        self.assertIn("windows_graphics_capture_binding", dependency_names)  # 新增代码+Phase54WindowsNativeRealityGate: 确认 WGC 绑定进入报告；如果没有这行代码，真实截图前置条件会漏检。
        self.assertIn("windows_sendinput_api", dependency_names)  # 新增代码+Phase54WindowsNativeRealityGate: 确认 SendInput API 进入报告；如果没有这行代码，真实输入前置条件会漏检。
        missing_items = [item for item in report["dependencies"] if item["status"] == "missing"]  # 新增代码+Phase54WindowsNativeRealityGate: 收集缺失项；如果没有这行代码，无法确认 blocked/missing 被诚实表达。
        self.assertTrue(missing_items)  # 新增代码+Phase54WindowsNativeRealityGate: 断言模拟环境下确实有缺失项；如果没有这行代码，测试可能没有覆盖缺依赖路径。
        self.assertTrue(all(item["next_step"] for item in missing_items))  # 新增代码+Phase54WindowsNativeRealityGate: 断言每个缺失项都有下一步；如果没有这行代码，用户只会看到失败但不知道怎么补。
        self.assertTrue(all(not item["install_attempted"] for item in report["dependencies"]))  # 新增代码+Phase54WindowsNativeRealityGate: 断言每项都没有执行安装；如果没有这行代码，单项偷偷安装不会被发现。
        self.assertTrue(report["passed"])  # 新增代码+Phase54WindowsNativeRealityGate: 断言诚实报告本身通过；如果没有这行代码，缺依赖会被误当作合同失败。
    # 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，test_phase54_reports_missing_dependencies_without_fake_success 到此结束；如果没有这个边界说明，初学者不容易看出依赖门禁测试范围。

    def test_phase54_cli_terminal_and_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，验证 CLI、/computer native-gate 和真实终端场景 token；如果没有这个测试，用户可见入口可能缺失。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase54WindowsNativeRealityGate: 创建临时目录保存报告；如果没有这行代码，测试会写入真实 memory 目录。
            report = run_phase54_native_reality_gate_contract(platform="win32", module_available=lambda name: False, command_available=lambda name: False, api_available=lambda name: name in {"win32_gdi_capture_api", "windows_sendinput_api"}, output_root=Path(temp_dir))  # 新增代码+Phase54WindowsNativeRealityGate: 注入稳定依赖状态；如果没有这行代码，token 测试会受当前机器影响。
        line = phase54_cli_line(report)  # 新增代码+Phase54WindowsNativeRealityGate: 生成稳定单行 token；如果没有这行代码，场景断言需要解析复杂 JSON。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase54_native_reality_gate.json")  # 新增代码+Phase54WindowsNativeRealityGate: 定位 Phase54 真实终端场景；如果没有这行代码，测试无法确认场景已创建。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase54WindowsNativeRealityGate: 读取场景 JSON；如果没有这行代码，场景漏 token 不会被发现。
        expected_tokens = {PHASE54_WINDOWS_NATIVE_REALITY_GATE_MARKER, PHASE54_WINDOWS_NATIVE_REALITY_GATE_OK_TOKEN, "dependency_count=9", "report_written=true", "install_attempted=false", "system_settings_changed=false", "actions_expanded=false"}  # 新增代码+Phase54WindowsNativeRealityGate: 列出必须稳定出现的 token；如果没有这行代码，验收标准会散落在多个断言里。
        for token in expected_tokens:  # 新增代码+Phase54WindowsNativeRealityGate: 遍历每个固定 token；如果没有这行代码，只能重复写多行断言。
            self.assertIn(token, line)  # 新增代码+Phase54WindowsNativeRealityGate: 断言 CLI 行包含 token；如果没有这行代码，命令行输出漂移不会被发现。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase54WindowsNativeRealityGate: 断言 debug log 检查包含 token；如果没有这行代码，真实终端验收可能漏查命令输出。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase54WindowsNativeRealityGate: 断言最终回答检查包含 token；如果没有这行代码，用户可见答案可能缺少验收锚点。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase54WindowsNativeRealityGate: 创建临时工作区运行 /computer native-gate；如果没有这行代码，测试可能写入真实项目状态目录。
            output = run_computer_terminal_command(Path(temp_dir), "/computer native-gate")  # 新增代码+Phase54WindowsNativeRealityGate: 调用真实终端命令处理函数；如果没有这行代码，无法证明 /computer native-gate 已对用户可见。
        self.assertIn("Computer Native Reality Gate", output)  # 新增代码+Phase54WindowsNativeRealityGate: 断言终端输出有现实门禁标题；如果没有这行代码，命令可能只是返回普通状态。
        self.assertIn(PHASE54_WINDOWS_NATIVE_REALITY_GATE_MARKER, output)  # 新增代码+Phase54WindowsNativeRealityGate: 断言终端输出包含 marker；如果没有这行代码，controller 难以稳定匹配。
        self.assertIn("next_step=", output)  # 新增代码+Phase54WindowsNativeRealityGate: 断言终端输出包含下一步；如果没有这行代码，用户看不到缺依赖怎么处理。
    # 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，test_phase54_cli_terminal_and_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI/终端测试范围。


if __name__ == "__main__":  # 新增代码+Phase54WindowsNativeRealityGate: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式单独验证 Phase54。
    unittest.main()  # 新增代码+Phase54WindowsNativeRealityGate: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行断言。
