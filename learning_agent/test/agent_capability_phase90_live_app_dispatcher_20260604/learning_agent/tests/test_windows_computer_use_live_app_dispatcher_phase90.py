import json  # 新增代码+Phase90LiveAppDispatcher: 导入 JSON 用来校验真实终端场景文件格式；如果没有这行代码，场景 JSON 写坏要到验收时才暴露。
import tempfile  # 新增代码+Phase90LiveAppDispatcher: 导入临时目录隔离 Phase90 验收报告；如果没有这行代码，测试会污染真实运行目录。
import unittest  # 新增代码+Phase90LiveAppDispatcher: 导入 unittest 承载 Phase90 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase90LiveAppDispatcher: 导入 Path 管理 Windows 路径；如果没有这行代码，临时目录和场景文件路径容易拼错。

from learning_agent.computer_use.live_app_dispatcher import PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MARKER, PHASE90_WINDOWS_LIVE_APP_DISPATCHER_OK_TOKEN, WindowsLiveAppDispatcher, phase90_cli_line, run_phase90_live_app_dispatcher_contract  # 新增代码+Phase90LiveAppDispatcher: 导入计划要求的 Phase90 live dispatcher 入口；如果没有这行代码，红灯无法证明生产模块是否已经实现。


class WindowsComputerUseLiveAppDispatcherPhase90Tests(unittest.TestCase):  # 新增代码+Phase90LiveAppDispatcher: 类段开始，集中验证 Phase90 受控真实应用 dispatcher；如果没有这个类，真实 live app dispatcher 没有自动化门禁。
    def test_phase90_contract_wires_safe_live_dispatcher_path(self) -> None:  # 新增代码+Phase90LiveAppDispatcher: 函数段开始，验证 Phase90 总合同覆盖 live dispatcher 主路径；如果没有这个测试，模块可能只返回空矩阵仍误报完成。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase90LiveAppDispatcher: 使用临时目录隔离合同证据；如果没有这行代码，测试会写入真实 memory 目录。
            report = run_phase90_live_app_dispatcher_contract(base_dir=Path(temp_dir), real_smoke=False)  # 新增代码+Phase90LiveAppDispatcher: 运行安全合同模式；如果没有这行代码，测试没有结构化报告来源。
        self.assertEqual(report["marker"], PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MARKER)  # 新增代码+Phase90LiveAppDispatcher: 断言 ready marker 稳定；如果没有这行代码，真实终端验收无法稳定匹配 Phase90。
        self.assertEqual(report["ok_token"], PHASE90_WINDOWS_LIVE_APP_DISPATCHER_OK_TOKEN)  # 新增代码+Phase90LiveAppDispatcher: 断言 OK token 稳定；如果没有这行代码，用户无法一眼确认 Phase90 通过。
        self.assertTrue(report["passed"])  # 新增代码+Phase90LiveAppDispatcher: 断言总合同通过；如果没有这行代码，单项失败可能被总报告掩盖。
        self.assertTrue(report["live_dispatcher_ready"])  # 新增代码+Phase90LiveAppDispatcher: 断言 dispatcher 已就绪；如果没有这行代码，Phase90 可能只有文档没有执行入口。
        self.assertTrue(report["real_app_dispatch_path"])  # 新增代码+Phase90LiveAppDispatcher: 断言存在真实应用派发路径；如果没有这行代码，功能仍停留在矩阵描述。
        self.assertFalse(report["default_real_dispatch_enabled"])  # 新增代码+Phase90LiveAppDispatcher: 断言默认不裸开真实输入；如果没有这行代码，测试可能误允许无保护控制本机。
        self.assertTrue(report["requires_explicit_live_env_gate"])  # 新增代码+Phase90LiveAppDispatcher: 断言真实派发需要显式环境门；如果没有这行代码，用户可能误触真实桌面动作。
        self.assertTrue(report["uses_phase72_safety_boundary"])  # 新增代码+Phase90LiveAppDispatcher: 断言复用 Phase72 安全边界；如果没有这行代码，真实动作可能绕过高风险拒绝。
        self.assertTrue(report["uses_phase60_persistent_grants"])  # 新增代码+Phase90LiveAppDispatcher: 断言复用 Phase60 持久授权；如果没有这行代码，普通应用动作没有可审计授权来源。
        self.assertTrue(report["uses_phase69_app_window_control"])  # 新增代码+Phase90LiveAppDispatcher: 断言复用 Phase69 应用启动聚焦；如果没有这行代码，dispatcher 会重复造脆弱启动逻辑。
        self.assertTrue(report["uses_phase71_input_events"])  # 新增代码+Phase90LiveAppDispatcher: 断言复用 Phase71 输入事件；如果没有这行代码，热键/拖拽/滚轮事件格式可能漂移。
        self.assertTrue(report["notepad_live_dispatch_contract"])  # 新增代码+Phase90LiveAppDispatcher: 断言记事本派发合同通过；如果没有这行代码，文本类应用没有主路径样本。
        self.assertTrue(report["mspaint_pikachu_live_plan"])  # 新增代码+Phase90LiveAppDispatcher: 断言 Paint 皮卡丘 live 计划通过；如果没有这行代码，用户点名场景可能被漏掉。
        self.assertTrue(report["dangerous_window_zero_events"])  # 新增代码+Phase90LiveAppDispatcher: 断言危险窗口零事件拒绝；如果没有这行代码，终端/系统窗口可能被误控。
        self.assertTrue(report["unauthorized_window_zero_events"])  # 新增代码+Phase90LiveAppDispatcher: 断言未授权普通窗口零事件拒绝；如果没有这行代码，授权门可能被绕过。
        self.assertTrue(report["raw_text_hidden"])  # 新增代码+Phase90LiveAppDispatcher: 断言文本输入不在日志泄露明文；如果没有这行代码，真实输入可能泄露用户文本。
        self.assertFalse(report["uncontrolled_actions_expanded"])  # 新增代码+Phase90LiveAppDispatcher: 断言没有扩张无保护动作面；如果没有这行代码，Phase90 可能变成危险裸控。
    # 新增代码+Phase90LiveAppDispatcher: 函数段结束，test_phase90_contract_wires_safe_live_dispatcher_path 到此结束；如果没有这个边界说明，初学者不容易看出总合同范围。

    def test_phase90_dispatcher_blocks_unauthorized_and_dangerous_targets(self) -> None:  # 新增代码+Phase90LiveAppDispatcher: 函数段开始，验证 dispatcher 的拒绝路径；如果没有这个测试，危险窗口可能被主路径成功掩盖。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase90LiveAppDispatcher: 使用临时目录隔离 grant store；如果没有这行代码，测试可能读到旧授权。
            dispatcher = WindowsLiveAppDispatcher(base_dir=Path(temp_dir), session_id="phase90-test")  # 新增代码+Phase90LiveAppDispatcher: 创建隔离 dispatcher；如果没有这行代码，无法直接验证组件行为。
            unauthorized = dispatcher.dispatch("notepad", "click", {"x": 12, "y": 34})  # 新增代码+Phase90LiveAppDispatcher: 未授权普通应用先请求点击；如果没有这行代码，默认拒绝路径没有样本。
            dangerous = dispatcher.dispatch("powershell", "click", {"x": 12, "y": 34})  # 新增代码+Phase90LiveAppDispatcher: 危险终端应用请求点击；如果没有这行代码，高风险拒绝路径没有样本。
        self.assertFalse(unauthorized["ok"])  # 新增代码+Phase90LiveAppDispatcher: 断言未授权普通应用不执行；如果没有这行代码，grant 门可能失效。
        self.assertEqual(unauthorized["low_level_event_count"], 0)  # 新增代码+Phase90LiveAppDispatcher: 断言未授权拒绝是零事件；如果没有这行代码，拒绝后仍可能发送输入。
        self.assertTrue(unauthorized["zero_event_refusal"])  # 新增代码+Phase90LiveAppDispatcher: 断言返回零事件拒绝标志；如果没有这行代码，审计无法区分拒绝和执行失败。
        self.assertFalse(dangerous["ok"])  # 新增代码+Phase90LiveAppDispatcher: 断言危险终端不执行；如果没有这行代码，系统/终端窗口可能被误控。
        self.assertEqual(dangerous["low_level_event_count"], 0)  # 新增代码+Phase90LiveAppDispatcher: 断言危险窗口拒绝是零事件；如果没有这行代码，安全拒绝仍可能产生副作用。
        self.assertTrue(dangerous["zero_event_refusal"])  # 新增代码+Phase90LiveAppDispatcher: 断言危险窗口有零事件拒绝标志；如果没有这行代码，安全审计不可读。
    # 新增代码+Phase90LiveAppDispatcher: 函数段结束，test_phase90_dispatcher_blocks_unauthorized_and_dangerous_targets 到此结束；如果没有这个边界说明，初学者不容易看出拒绝路径范围。

    def test_phase90_dispatcher_allows_granted_representative_app_without_real_dispatch(self) -> None:  # 新增代码+Phase90LiveAppDispatcher: 函数段开始，验证已授权代表应用能走到记录派发层；如果没有这个测试，dispatcher 可能永远只会拒绝。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase90LiveAppDispatcher: 使用临时目录隔离授权和证据；如果没有这行代码，测试可能污染真实 memory。
            dispatcher = WindowsLiveAppDispatcher(base_dir=Path(temp_dir), session_id="phase90-granted")  # 新增代码+Phase90LiveAppDispatcher: 创建隔离 dispatcher；如果没有这行代码，无法单独验证授权正例。
            dispatcher.grant_representative_app("notepad", action_scope=["click", "type_text"])  # 新增代码+Phase90LiveAppDispatcher: 给记事本写入受控授权；如果没有这行代码，Phase72 会正确拒绝但无法测试放行。
            result = dispatcher.dispatch("notepad", "type_text", {"text": "secret text must not leak"})  # 新增代码+Phase90LiveAppDispatcher: 执行已授权文本输入合同；如果没有这行代码，文本派发和脱敏没有样本。
        self.assertTrue(result["ok"])  # 新增代码+Phase90LiveAppDispatcher: 断言已授权动作成功进入记录派发层；如果没有这行代码，正例路径可能坏掉。
        self.assertGreater(result["low_level_event_count"], 0)  # 新增代码+Phase90LiveAppDispatcher: 断言生成了低层事件；如果没有这行代码，成功可能只是空报告。
        self.assertFalse(result["real_dispatch_performed"])  # 新增代码+Phase90LiveAppDispatcher: 断言默认没有真实派发；如果没有这行代码，单元测试可能误控本机。
        self.assertTrue(result["raw_text_hidden"])  # 新增代码+Phase90LiveAppDispatcher: 断言日志隐藏原文；如果没有这行代码，用户输入可能泄露到报告。
        self.assertNotIn("secret text must not leak", json.dumps(result, ensure_ascii=False))  # 新增代码+Phase90LiveAppDispatcher: 断言序列化结果不含明文；如果没有这行代码，脱敏可能只是字段名上的假象。
    # 新增代码+Phase90LiveAppDispatcher: 函数段结束，test_phase90_dispatcher_allows_granted_representative_app_without_real_dispatch 到此结束；如果没有这个边界说明，初学者不容易看出授权正例范围。

    def test_phase90_cli_line_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase90LiveAppDispatcher: 函数段开始，验证 CLI 行和真实终端场景 token 稳定；如果没有这个测试，controller 可能漏检最终关键字段。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase90LiveAppDispatcher: 使用临时目录隔离合同状态；如果没有这行代码，测试会写入真实 memory。
            report = run_phase90_live_app_dispatcher_contract(base_dir=Path(temp_dir), real_smoke=False)  # 新增代码+Phase90LiveAppDispatcher: 运行 Phase90 合同；如果没有这行代码，CLI 行没有结构化来源。
        cli_line = phase90_cli_line(report)  # 新增代码+Phase90LiveAppDispatcher: 生成稳定 CLI token 行；如果没有这行代码，场景验收需要解析复杂 JSON。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase90_live_app_dispatcher.json")  # 新增代码+Phase90LiveAppDispatcher: 定位 Phase90 真实终端场景文件；如果没有这行代码，场景缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase90LiveAppDispatcher: 读取场景文本；如果没有这行代码，场景 token 漏配无法被发现。
        json.loads(scenario_text)  # 新增代码+Phase90LiveAppDispatcher: 校验场景是合法 JSON；如果没有这行代码，controller 运行时才会暴露格式错误。
        expected_tokens = {PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MARKER, PHASE90_WINDOWS_LIVE_APP_DISPATCHER_OK_TOKEN, "live_dispatcher_ready=true", "real_app_dispatch_path=true", "default_real_dispatch_enabled=false", "requires_explicit_live_env_gate=true", "uses_phase72_safety_boundary=true", "uses_phase60_persistent_grants=true", "uses_phase69_app_window_control=true", "uses_phase71_input_events=true", "safe_window_real_smoke_path=true", "representative_live_apps_ready=true", "notepad_live_dispatch_contract=true", "mspaint_pikachu_live_plan=true", "dangerous_window_zero_events=true", "unauthorized_window_zero_events=true", "raw_text_hidden=true", "uncontrolled_actions_expanded=false"}  # 新增代码+Phase90LiveAppDispatcher: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase90LiveAppDispatcher: 遍历每个关键 token；如果没有这行代码，重复断言容易遗漏。
            self.assertIn(token, cli_line)  # 新增代码+Phase90LiveAppDispatcher: 断言 CLI 输出包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase90LiveAppDispatcher: 断言真实终端场景也包含 token；如果没有这行代码，自动测试和真实验收可能不一致。
    # 新增代码+Phase90LiveAppDispatcher: 函数段结束，test_phase90_cli_line_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 场景验收范围。
# 新增代码+Phase90LiveAppDispatcher: 类段结束，WindowsComputerUseLiveAppDispatcherPhase90Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase90LiveAppDispatcher: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase90LiveAppDispatcher: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
