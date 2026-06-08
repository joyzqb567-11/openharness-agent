import json  # 新增代码+Phase69AppWindowControl: 导入 JSON 用来校验真实终端验收场景；如果没有这行代码，场景格式错误只能等 controller 运行时才暴露。
import unittest  # 新增代码+Phase69AppWindowControl: 导入 unittest 承载 Phase69 自动化测试；如果没有这行代码，标准测试命令无法发现本阶段门禁。
from pathlib import Path  # 新增代码+Phase69AppWindowControl: 导入 Path 处理 Windows 场景文件路径；如果没有这行代码，路径拼接容易受当前目录影响。

from learning_agent.computer_use.app_window_control import PHASE69_ACTIONS_EXPANDED, PHASE69_APP_WINDOW_CONTROL_MARKER, PHASE69_APP_WINDOW_CONTROL_OK_TOKEN, Phase69RecordingFocuser, Phase69RecordingLauncher, WindowsAppWindowControlRuntime, build_launch_plan, phase69_cli_line, run_phase69_app_window_control_contract  # 新增代码+Phase69AppWindowControl: 导入 Phase69 应用窗口控制公开 API；如果没有这行代码，红灯测试无法证明生产模块尚未补齐。


class WindowsComputerUseAppWindowControlPhase69Tests(unittest.TestCase):  # 新增代码+Phase69AppWindowControl: 类段开始，集中验证 Phase69 应用启动、聚焦和目标身份合同；如果没有这个类，本阶段没有自动化质量门禁。
    def test_phase69_contract_reports_required_app_window_capabilities(self) -> None:  # 新增代码+Phase69AppWindowControl: 函数段开始，验证 Phase69 合同报告必须包含启动、聚焦、身份和漂移阻断能力；如果没有这个测试，CLI token 可能只是空口号。
        report = run_phase69_app_window_control_contract(real_smoke=False)  # 新增代码+Phase69AppWindowControl: 运行 Phase69 记录型合同自检；如果没有这行代码，测试没有真实报告来源。
        self.assertEqual(report["marker"], PHASE69_APP_WINDOW_CONTROL_MARKER)  # 新增代码+Phase69AppWindowControl: 断言 ready marker 稳定；如果没有这行代码，真实终端验收可能匹配不到 Phase69 输出。
        self.assertEqual(report["ok_token"], PHASE69_APP_WINDOW_CONTROL_OK_TOKEN)  # 新增代码+Phase69AppWindowControl: 断言 OK token 稳定；如果没有这行代码，用户无法一眼判断本阶段是否通过。
        self.assertTrue(report["app_launch"])  # 新增代码+Phase69AppWindowControl: 断言应用启动合同成立；如果没有这行代码，后续 Phase70 无法依赖目标应用已打开。
        self.assertTrue(report["window_focus"])  # 新增代码+Phase69AppWindowControl: 断言窗口聚焦合同成立；如果没有这行代码，后续点击和输入可能落到错误窗口。
        self.assertTrue(report["target_window_identity"])  # 新增代码+Phase69AppWindowControl: 断言动作前后目标身份一致；如果没有这行代码，窗口漂移风险不会被发现。
        self.assertTrue(report["target_drift_blocked"])  # 新增代码+Phase69AppWindowControl: 断言目标漂移会被阻断；如果没有这行代码，真实软件切窗后仍可能继续操作。
        self.assertTrue(report["safe_start_process_plan"])  # 新增代码+Phase69AppWindowControl: 断言启动计划只使用安全 Start-Process 语义；如果没有这行代码，启动层可能引入注册表或系统设置改动。
        self.assertTrue(report["recording_launcher"])  # 新增代码+Phase69AppWindowControl: 断言合同使用记录型 launcher；如果没有这行代码，单测可能误触真实本机应用。
        self.assertFalse(report["system_settings_changed"])  # 新增代码+Phase69AppWindowControl: 断言本阶段不改系统设置；如果没有这行代码，启动功能可能越界修改 Windows 环境。
        self.assertFalse(report["actions_expanded"])  # 新增代码+Phase69AppWindowControl: 断言 Phase69 不扩大真实桌面写动作范围；如果没有这行代码，本阶段可能被误当成真实通用控制已完成。
    # 新增代码+Phase69AppWindowControl: 函数段结束，test_phase69_contract_reports_required_app_window_capabilities 到此结束；如果没有这个边界说明，初学者不容易看出合同测试范围。

    def test_phase69_build_launch_plan_uses_safe_start_process_contract(self) -> None:  # 新增代码+Phase69AppWindowControl: 函数段开始，验证启动计划必须是安全、可审计、无系统设置副作用的计划；如果没有这个测试，app launch 可能被实现成危险 shell 字符串。
        plan = build_launch_plan("notepad", test_file="H:/tmp/phase69-safe.txt")  # 新增代码+Phase69AppWindowControl: 构建记事本启动计划；如果没有这行代码，测试无法检查启动计划结构。
        self.assertEqual(plan["app_name"], "notepad")  # 新增代码+Phase69AppWindowControl: 断言应用名被规范化；如果没有这行代码，大小写和空格可能导致启动器行为漂移。
        self.assertEqual(plan["executable"], "notepad.exe")  # 新增代码+Phase69AppWindowControl: 断言 notepad 映射到安全可执行名；如果没有这行代码，启动计划可能依赖用户输入的任意命令。
        self.assertEqual(plan["launch_verb"], "Start-Process")  # 新增代码+Phase69AppWindowControl: 断言计划使用 Start-Process 语义；如果没有这行代码，后续实现可能改成不受控 shell 执行。
        self.assertIn("H:/tmp/phase69-safe.txt", plan["arguments"])  # 新增代码+Phase69AppWindowControl: 断言测试文件作为参数保存；如果没有这行代码，打开文件类任务无法被计划。
        self.assertFalse(plan["changes_registry"])  # 新增代码+Phase69AppWindowControl: 断言不会修改注册表；如果没有这行代码，启动阶段可能越界触碰系统配置。
        self.assertFalse(plan["changes_system_settings"])  # 新增代码+Phase69AppWindowControl: 断言不会修改系统设置；如果没有这行代码，用户环境可能被启动功能改变。
        self.assertFalse(plan["requires_admin"])  # 新增代码+Phase69AppWindowControl: 断言不需要管理员权限；如果没有这行代码，启动阶段可能触发 UAC 或高风险流程。
    # 新增代码+Phase69AppWindowControl: 函数段结束，test_phase69_build_launch_plan_uses_safe_start_process_contract 到此结束；如果没有这个边界说明，初学者不容易看出启动计划测试范围。

    def test_phase69_runtime_launches_and_focuses_with_recording_adapters(self) -> None:  # 新增代码+Phase69AppWindowControl: 函数段开始，验证 runtime 通过注入的记录型启动器和聚焦器工作；如果没有这个测试，单测可能无法证明没有真实桌面副作用。
        launcher = Phase69RecordingLauncher()  # 新增代码+Phase69AppWindowControl: 创建记录型启动器；如果没有这行代码，测试可能触发真实应用启动。
        focuser = Phase69RecordingFocuser()  # 新增代码+Phase69AppWindowControl: 创建记录型聚焦器；如果没有这行代码，测试可能触发真实前台窗口切换。
        runtime = WindowsAppWindowControlRuntime(launcher=launcher, focuser=focuser)  # 新增代码+Phase69AppWindowControl: 创建注入记录器的 runtime；如果没有这行代码，启动和聚焦合同无法被安全执行。
        plan = build_launch_plan("mspaint")  # 新增代码+Phase69AppWindowControl: 构建画图启动计划；如果没有这行代码，测试无法覆盖 Paint 代表场景的前置应用启动。
        launch_result = runtime.launch_app(plan)  # 新增代码+Phase69AppWindowControl: 执行记录型启动；如果没有这行代码，app_launch 事实没有事件来源。
        focus_result = runtime.focus_window(launch_result["window"])  # 新增代码+Phase69AppWindowControl: 执行记录型聚焦；如果没有这行代码，window_focus 事实没有事件来源。
        self.assertTrue(launch_result["launched"])  # 新增代码+Phase69AppWindowControl: 断言启动结果成功；如果没有这行代码，runtime 可能只构造计划不调用 launcher。
        self.assertTrue(focus_result["focused"])  # 新增代码+Phase69AppWindowControl: 断言聚焦结果成功；如果没有这行代码，后续动作可能没有目标窗口。
        self.assertEqual(len(launcher.launches), 1)  # 新增代码+Phase69AppWindowControl: 断言只记录一次启动；如果没有这行代码，重复启动可能造成真实验收漂移。
        self.assertEqual(len(focuser.focuses), 1)  # 新增代码+Phase69AppWindowControl: 断言只记录一次聚焦；如果没有这行代码，聚焦器可能被重复调用。
        self.assertEqual(launch_result["window"]["app_id"], "mspaint.exe")  # 新增代码+Phase69AppWindowControl: 断言启动结果窗口身份来自可执行名；如果没有这行代码，窗口身份可能无法和计划关联。
        self.assertFalse(launch_result["actions_expanded"])  # 新增代码+Phase69AppWindowControl: 断言记录型启动不扩大真实动作面；如果没有这行代码，合同测试可能误触真实桌面。
    # 新增代码+Phase69AppWindowControl: 函数段结束，test_phase69_runtime_launches_and_focuses_with_recording_adapters 到此结束；如果没有这个边界说明，初学者不容易看出 runtime 测试范围。

    def test_phase69_target_identity_allows_same_window_and_blocks_drift(self) -> None:  # 新增代码+Phase69AppWindowControl: 函数段开始，验证目标窗口身份一致时允许、漂移时阻断；如果没有这个测试，切窗风险无法被自动发现。
        runtime = WindowsAppWindowControlRuntime(launcher=Phase69RecordingLauncher(), focuser=Phase69RecordingFocuser())  # 新增代码+Phase69AppWindowControl: 创建记录型 runtime；如果没有这行代码，身份校验方法没有实例入口。
        before = {"app_id": "notepad.exe", "window_id": "phase69-window:notepad.exe", "pid": 6900, "title_sha256_16": "same-title"}  # 新增代码+Phase69AppWindowControl: 构造动作前窗口身份；如果没有这行代码，测试没有基准目标。
        same_after = {"app_id": "notepad.exe", "window_id": "phase69-window:notepad.exe", "pid": 6900, "title_sha256_16": "same-title"}  # 新增代码+Phase69AppWindowControl: 构造未漂移窗口身份；如果没有这行代码，允许路径无法验证。
        drift_after = {"app_id": "powershell.exe", "window_id": "phase69-window:powershell.exe", "pid": 6901, "title_sha256_16": "other-title"}  # 新增代码+Phase69AppWindowControl: 构造漂移到终端的窗口身份；如果没有这行代码，阻断路径无法验证。
        same_result = runtime.verify_target_identity(before, same_after)  # 新增代码+Phase69AppWindowControl: 校验同一窗口；如果没有这行代码，允许路径没有结果。
        drift_result = runtime.verify_target_identity(before, drift_after)  # 新增代码+Phase69AppWindowControl: 校验漂移窗口；如果没有这行代码，阻断路径没有结果。
        self.assertTrue(same_result["same_target"])  # 新增代码+Phase69AppWindowControl: 断言同一窗口被允许；如果没有这行代码，正常流程可能被误杀。
        self.assertFalse(same_result["blocked"])  # 新增代码+Phase69AppWindowControl: 断言同一窗口不阻断；如果没有这行代码，后续动作无法继续。
        self.assertFalse(drift_result["same_target"])  # 新增代码+Phase69AppWindowControl: 断言漂移窗口不是同一目标；如果没有这行代码，身份比对可能过松。
        self.assertTrue(drift_result["blocked"])  # 新增代码+Phase69AppWindowControl: 断言漂移会被阻断；如果没有这行代码，真实切窗后可能继续误操作。
        self.assertEqual(drift_result["reason"], "target_window_identity_changed")  # 新增代码+Phase69AppWindowControl: 断言阻断原因稳定；如果没有这行代码，审计和恢复无法判断为何停止。
    # 新增代码+Phase69AppWindowControl: 函数段结束，test_phase69_target_identity_allows_same_window_and_blocks_drift 到此结束；如果没有这个边界说明，初学者不容易看出身份校验测试范围。

    def test_phase69_cli_line_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase69AppWindowControl: 函数段开始，验证 CLI 行和真实终端场景 token 稳定；如果没有这个测试，自动化验收和真实终端验收可能漂移。
        report = run_phase69_app_window_control_contract(real_smoke=False)  # 新增代码+Phase69AppWindowControl: 运行合同报告作为 CLI 输出来源；如果没有这行代码，token 测试没有结构化来源。
        cli_line = phase69_cli_line(report)  # 新增代码+Phase69AppWindowControl: 生成稳定 CLI token 行；如果没有这行代码，真实终端最终回答需要解析复杂 JSON。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase69_app_window_control.json")  # 新增代码+Phase69AppWindowControl: 定位 Phase69 真实终端验收场景；如果没有这行代码，场景缺失不会被测试发现。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase69AppWindowControl: 读取场景文本；如果没有这行代码，场景 token 漏配无法被发现。
        json.loads(scenario_text)  # 新增代码+Phase69AppWindowControl: 校验场景是合法 JSON；如果没有这行代码，controller 运行时才会暴露格式错误。
        expected_tokens = {PHASE69_APP_WINDOW_CONTROL_MARKER, PHASE69_APP_WINDOW_CONTROL_OK_TOKEN, "app_launch=true", "window_focus=true", "target_window_identity=true", "target_drift_blocked=true", "actions_expanded=false"}  # 新增代码+Phase69AppWindowControl: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase69AppWindowControl: 遍历每个关键 token；如果没有这行代码，重复断言容易遗漏。
            self.assertIn(token, cli_line)  # 新增代码+Phase69AppWindowControl: 断言 CLI 输出包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase69AppWindowControl: 断言真实终端场景也包含 token；如果没有这行代码，自动化测试和真实验收可能不一致。
        self.assertFalse(PHASE69_ACTIONS_EXPANDED)  # 新增代码+Phase69AppWindowControl: 断言常量层也没有扩大真实动作面；如果没有这行代码，包级导出可能和报告字段脱节。
    # 新增代码+Phase69AppWindowControl: 函数段结束，test_phase69_cli_line_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 token 测试范围。
# 新增代码+Phase69AppWindowControl: 类段结束，WindowsComputerUseAppWindowControlPhase69Tests 到此结束；如果没有这个边界说明，初学者不容易看出 Phase69 测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase69AppWindowControl: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase69AppWindowControl: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
