import json  # 新增代码+Phase68ClosedLoopExecutor: 导入 JSON 用来校验真实终端验收场景文件；如果没有这行代码，场景格式错误只能等 controller 运行时才暴露。
import unittest  # 新增代码+Phase68ClosedLoopExecutor: 导入 unittest 承载 Phase68 自动化测试；如果没有这行代码，标准测试命令无法发现本阶段门禁。
from pathlib import Path  # 新增代码+Phase68ClosedLoopExecutor: 导入 Path 处理 Windows 项目路径；如果没有这行代码，测试会依赖脆弱的字符串路径拼接。

from learning_agent.computer_use.closed_loop_executor import PHASE68_CLOSED_LOOP_EXECUTOR_MARKER, PHASE68_CLOSED_LOOP_EXECUTOR_OK_TOKEN, WindowsClosedLoopComputerExecutor, phase68_cli_line, run_phase68_closed_loop_executor_contract  # 新增代码+Phase68ClosedLoopExecutor: 导入 Phase68 闭环执行器公开 API；如果没有这行代码，红灯测试无法证明生产模块尚未补齐。


class Phase68FakeObserver:  # 新增代码+Phase68ClosedLoopExecutor: 类段开始，提供可计数的假观察器来模拟屏幕观察；如果没有这个类，测试无法确认执行器是否真的每步先观察。
    def __init__(self) -> None:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，初始化观察记录；如果没有这个函数，测试无法统计观察次数和观察顺序。
        self.calls = []  # 新增代码+Phase68ClosedLoopExecutor: 保存每次 observe 的步骤；如果没有这行代码，测试无法证明动作前发生过观察。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，Phase68FakeObserver.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def observe(self, step: dict) -> dict:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，模拟一次真实桌面观察；如果没有这个函数，闭环执行器无法拿到行动前证据。
        self.calls.append(step)  # 新增代码+Phase68ClosedLoopExecutor: 记录当前步骤已经被观察；如果没有这行代码，测试无法核对观察次数。
        return {"observation_id": f"obs-{len(self.calls)}", "step_operation": step.get("operation", "")}  # 新增代码+Phase68ClosedLoopExecutor: 返回稳定观察结果；如果没有这行代码，执行器后续决策和动作没有观察输入。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，Phase68FakeObserver.observe 到此结束；如果没有这个边界说明，初学者不容易看出观察逻辑范围。
# 新增代码+Phase68ClosedLoopExecutor: 类段结束，Phase68FakeObserver 到此结束；如果没有这个边界说明，初学者不容易看出假观察器范围。


class Phase68FakeActor:  # 新增代码+Phase68ClosedLoopExecutor: 类段开始，提供假动作执行器来模拟键盘鼠标动作；如果没有这个类，测试无法确认执行器是否真的调用行动层。
    def __init__(self) -> None:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，初始化动作记录；如果没有这个函数，测试无法统计动作调用顺序。
        self.actions = []  # 新增代码+Phase68ClosedLoopExecutor: 保存每次 act 的输入；如果没有这行代码，测试无法证明行动层被有序调用。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，Phase68FakeActor.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def act(self, step: dict, observation: dict) -> dict:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，模拟一次动作执行；如果没有这个函数，闭环测试无法覆盖 acted 事件。
        self.actions.append({"step": step, "observation": observation})  # 新增代码+Phase68ClosedLoopExecutor: 记录动作拿到的步骤和观察；如果没有这行代码，测试无法确认动作不是盲打。
        return {"acted": True, "operation": step.get("operation", ""), "write_action": step.get("action_kind") == "write"}  # 新增代码+Phase68ClosedLoopExecutor: 返回稳定动作结果；如果没有这行代码，执行器无法进行动作后验证。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，Phase68FakeActor.act 到此结束；如果没有这个边界说明，初学者不容易看出动作逻辑范围。
# 新增代码+Phase68ClosedLoopExecutor: 类段结束，Phase68FakeActor 到此结束；如果没有这个边界说明，初学者不容易看出假执行器范围。


class Phase68FailThenPassVerifier:  # 新增代码+Phase68ClosedLoopExecutor: 类段开始，提供先失败后成功的假验证器；如果没有这个类，测试无法覆盖失败恢复路径。
    def __init__(self) -> None:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，初始化验证次数；如果没有这个函数，验证器无法模拟第一次失败。
        self.calls = 0  # 新增代码+Phase68ClosedLoopExecutor: 记录验证调用次数；如果没有这行代码，测试无法制造可重复的失败后恢复。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，Phase68FailThenPassVerifier.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def verify(self, step: dict, observation: dict, action_result: dict) -> dict:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，模拟动作后的结果校验；如果没有这个函数，写动作后是否成功无法被判断。
        self.calls += 1  # 新增代码+Phase68ClosedLoopExecutor: 增加验证次数；如果没有这行代码，第一次失败和后续成功无法区分。
        passed = self.calls > 1  # 新增代码+Phase68ClosedLoopExecutor: 第一次验证故意失败，后面通过；如果没有这行代码，恢复路径不会被触发。
        return {"passed": passed, "checked_operation": step.get("operation", ""), "observation_id": observation.get("observation_id", "")}  # 新增代码+Phase68ClosedLoopExecutor: 返回稳定验证报告；如果没有这行代码，执行器无法决定是否恢复。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，Phase68FailThenPassVerifier.verify 到此结束；如果没有这个边界说明，初学者不容易看出验证逻辑范围。
# 新增代码+Phase68ClosedLoopExecutor: 类段结束，Phase68FailThenPassVerifier 到此结束；如果没有这个边界说明，初学者不容易看出假验证器范围。


class Phase68FakeRecoverer:  # 新增代码+Phase68ClosedLoopExecutor: 类段开始，提供假恢复器来模拟失败后的重新观察策略；如果没有这个类，测试无法确认 recovered 事件。
    def __init__(self) -> None:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，初始化恢复记录；如果没有这个函数，测试无法统计恢复调用次数。
        self.recoveries = []  # 新增代码+Phase68ClosedLoopExecutor: 保存每次恢复输入；如果没有这行代码，测试无法确认失败后真的进入恢复路径。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，Phase68FakeRecoverer.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def recover(self, step: dict, observation: dict, action_result: dict, verification: dict) -> dict:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，模拟失败恢复动作；如果没有这个函数，执行器失败后只能停住。
        self.recoveries.append({"step": step, "verification": verification})  # 新增代码+Phase68ClosedLoopExecutor: 记录恢复请求；如果没有这行代码，测试无法核对恢复是否发生。
        return {"recovered": True, "strategy": "observe_again", "operation": step.get("operation", "")}  # 新增代码+Phase68ClosedLoopExecutor: 返回稳定恢复结果；如果没有这行代码，执行器无法继续闭环。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，Phase68FakeRecoverer.recover 到此结束；如果没有这个边界说明，初学者不容易看出恢复逻辑范围。
# 新增代码+Phase68ClosedLoopExecutor: 类段结束，Phase68FakeRecoverer 到此结束；如果没有这个边界说明，初学者不容易看出假恢复器范围。


class WindowsComputerUseClosedLoopExecutorPhase68Tests(unittest.TestCase):  # 新增代码+Phase68ClosedLoopExecutor: 类段开始，集中验证 Phase68 闭环执行器；如果没有这个类，本阶段没有自动化质量门禁。
    def test_phase68_contract_reports_closed_loop_recovery_and_guard(self) -> None:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，验证 Phase68 合同报告必须包含闭环、验证、恢复和防盲打能力；如果没有这个测试，CLI token 可能只是假口号。
        report = run_phase68_closed_loop_executor_contract()  # 新增代码+Phase68ClosedLoopExecutor: 运行 Phase68 合同自检；如果没有这行代码，测试没有真实报告来源。
        self.assertEqual(report["marker"], PHASE68_CLOSED_LOOP_EXECUTOR_MARKER)  # 新增代码+Phase68ClosedLoopExecutor: 断言 ready marker 稳定；如果没有这行代码，真实终端验收可能匹配不到本阶段输出。
        self.assertEqual(report["ok_token"], PHASE68_CLOSED_LOOP_EXECUTOR_OK_TOKEN)  # 新增代码+Phase68ClosedLoopExecutor: 断言 OK token 稳定；如果没有这行代码，用户无法一眼判断本阶段是否通过。
        self.assertTrue(report["closed_loop_execution"])  # 新增代码+Phase68ClosedLoopExecutor: 断言执行器形成观察到停止的闭环；如果没有这行代码，执行器可能只跑单步动作。
        self.assertTrue(report["post_action_verification"])  # 新增代码+Phase68ClosedLoopExecutor: 断言写动作之后一定验证；如果没有这行代码，打字点击失败可能无人发现。
        self.assertTrue(report["failure_recovery"])  # 新增代码+Phase68ClosedLoopExecutor: 断言验证失败会进入恢复；如果没有这行代码，真实软件轻微漂移会导致任务直接失控。
        self.assertTrue(report["blind_coordinate_chain_blocked"])  # 新增代码+Phase68ClosedLoopExecutor: 断言连续盲写动作会被阻断；如果没有这行代码，坐标连点可能绕过观察证据。
        self.assertFalse(report["actions_expanded"])  # 新增代码+Phase68ClosedLoopExecutor: 断言 Phase68 仍不扩大真实桌面动作范围；如果没有这行代码，本阶段可能越界执行真实输入。
        self.assertTrue({"observed", "decided", "acted", "verified", "recovered", "stopped"}.issubset(set(report["event_states"])))  # 新增代码+Phase68ClosedLoopExecutor: 断言关键事件状态齐全；如果没有这行代码，闭环轨迹可能缺少恢复或停止边界。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，test_phase68_contract_reports_closed_loop_recovery_and_guard 到此结束；如果没有这个边界说明，初学者不容易看出合同测试范围。

    def test_phase68_executor_observes_before_each_action_and_verifies_after_write(self) -> None:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，验证执行顺序必须先观察再行动再验证；如果没有这个测试，执行器可能退化成盲目坐标动作链。
        observer = Phase68FakeObserver()  # 新增代码+Phase68ClosedLoopExecutor: 创建假观察器；如果没有这行代码，测试无法统计观察调用。
        actor = Phase68FakeActor()  # 新增代码+Phase68ClosedLoopExecutor: 创建假动作执行器；如果没有这行代码，测试无法统计行动调用。
        verifier = Phase68FailThenPassVerifier()  # 新增代码+Phase68ClosedLoopExecutor: 创建先失败后成功的验证器；如果没有这行代码，测试无法触发恢复路径。
        recoverer = Phase68FakeRecoverer()  # 新增代码+Phase68ClosedLoopExecutor: 创建假恢复器；如果没有这行代码，测试无法证明失败后会恢复。
        task_plan = {"steps": [{"operation": "type_text", "action_kind": "write", "expected_result": "text appears"}, {"operation": "verify_result", "action_kind": "verify", "expected_result": "text exists"}]}  # 新增代码+Phase68ClosedLoopExecutor: 定义包含写动作和验证动作的最小计划；如果没有这行代码，执行器没有可运行任务。
        result = WindowsClosedLoopComputerExecutor().run(task_plan, observer, actor, verifier, recoverer)  # 新增代码+Phase68ClosedLoopExecutor: 执行闭环计划；如果没有这行代码，顺序规则无法被真实验证。
        event_states = [event["state"] for event in result["events"]]  # 新增代码+Phase68ClosedLoopExecutor: 提取事件状态列表；如果没有这行代码，后续断言要重复解析事件。
        acted_index = event_states.index("acted")  # 新增代码+Phase68ClosedLoopExecutor: 找到第一次行动位置；如果没有这行代码，测试无法核对行动前是否观察。
        verified_index = event_states.index("verified")  # 新增代码+Phase68ClosedLoopExecutor: 找到第一次验证位置；如果没有这行代码，测试无法核对写动作后是否验证。
        self.assertEqual(event_states[acted_index - 1], "decided")  # 新增代码+Phase68ClosedLoopExecutor: 断言行动前先决策；如果没有这行代码，动作可能没有计划依据。
        self.assertIn("observed", event_states[:acted_index])  # 新增代码+Phase68ClosedLoopExecutor: 断言行动前已经观察；如果没有这行代码，动作可能直接盲打。
        self.assertGreater(verified_index, acted_index)  # 新增代码+Phase68ClosedLoopExecutor: 断言验证发生在写动作之后；如果没有这行代码，后置校验顺序可能倒置。
        self.assertIn("recovered", event_states)  # 新增代码+Phase68ClosedLoopExecutor: 断言失败后触发恢复；如果没有这行代码，恢复机制可能没有接入。
        self.assertGreaterEqual(len(observer.calls), len(actor.actions))  # 新增代码+Phase68ClosedLoopExecutor: 断言观察次数不少于动作次数；如果没有这行代码，执行器可能存在未观察就行动的步骤。
        self.assertTrue(result["post_action_verification"])  # 新增代码+Phase68ClosedLoopExecutor: 断言结果报告认可写后验证；如果没有这行代码，汇总报告可能和事件轨迹脱节。
        self.assertTrue(result["failure_recovery"])  # 新增代码+Phase68ClosedLoopExecutor: 断言结果报告认可失败恢复；如果没有这行代码，汇总报告可能漏掉恢复事实。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，test_phase68_executor_observes_before_each_action_and_verifies_after_write 到此结束；如果没有这个边界说明，初学者不容易看出顺序测试范围。

    def test_phase68_rejects_blind_write_chain_without_intervening_observation(self) -> None:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，验证两个写动作之间必须重新观察；如果没有这个测试，执行器可能连续盲点盲打。
        executor = WindowsClosedLoopComputerExecutor()  # 新增代码+Phase68ClosedLoopExecutor: 创建闭环执行器实例；如果没有这行代码，无法调用盲写链检测方法。
        blind_events = [{"state": "observed"}, {"state": "acted", "write_action": True}, {"state": "acted", "write_action": True}]  # 新增代码+Phase68ClosedLoopExecutor: 构造缺少中间观察的危险事件链；如果没有这行代码，防盲打规则没有负例。
        safe_events = [{"state": "observed"}, {"state": "acted", "write_action": True}, {"state": "observed"}, {"state": "acted", "write_action": True}]  # 新增代码+Phase68ClosedLoopExecutor: 构造写动作之间重新观察的安全事件链；如果没有这行代码，检测器可能把安全闭环误杀。
        self.assertTrue(executor.blind_write_chain_detected(blind_events))  # 新增代码+Phase68ClosedLoopExecutor: 断言危险链会被识别；如果没有这行代码，连续盲写风险不会被测试发现。
        self.assertFalse(executor.blind_write_chain_detected(safe_events))  # 新增代码+Phase68ClosedLoopExecutor: 断言带观察的链不会被误报；如果没有这行代码，执行器可能过度阻断正常任务。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，test_phase68_rejects_blind_write_chain_without_intervening_observation 到此结束；如果没有这个边界说明，初学者不容易看出安全检测测试范围。

    def test_phase68_cli_line_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，验证 CLI 行和真实终端场景 token 稳定；如果没有这个测试，自动化验收和真实终端验收可能漂移。
        report = run_phase68_closed_loop_executor_contract()  # 新增代码+Phase68ClosedLoopExecutor: 运行合同报告作为 CLI 输出来源；如果没有这行代码，token 测试没有结构化来源。
        cli_line = phase68_cli_line(report)  # 新增代码+Phase68ClosedLoopExecutor: 生成稳定 CLI token 行；如果没有这行代码，真实终端最终回答需要解析复杂 JSON。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase68_closed_loop_executor.json")  # 新增代码+Phase68ClosedLoopExecutor: 定位 Phase68 真实终端验收场景；如果没有这行代码，场景缺失不会被测试发现。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase68ClosedLoopExecutor: 读取场景文本；如果没有这行代码，场景 token 漏配无法被发现。
        json.loads(scenario_text)  # 新增代码+Phase68ClosedLoopExecutor: 校验场景是合法 JSON；如果没有这行代码，controller 运行时才会暴露格式错误。
        expected_tokens = {PHASE68_CLOSED_LOOP_EXECUTOR_MARKER, PHASE68_CLOSED_LOOP_EXECUTOR_OK_TOKEN, "closed_loop_execution=true", "post_action_verification=true", "failure_recovery=true", "blind_coordinate_chain_blocked=true", "actions_expanded=false"}  # 新增代码+Phase68ClosedLoopExecutor: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase68ClosedLoopExecutor: 遍历每个关键 token；如果没有这行代码，重复断言容易遗漏。
            self.assertIn(token, cli_line)  # 新增代码+Phase68ClosedLoopExecutor: 断言 CLI 输出包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase68ClosedLoopExecutor: 断言真实终端场景也包含 token；如果没有这行代码，自动化测试和真实验收可能不一致。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，test_phase68_cli_line_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 token 测试范围。
# 新增代码+Phase68ClosedLoopExecutor: 类段结束，WindowsComputerUseClosedLoopExecutorPhase68Tests 到此结束；如果没有这个边界说明，初学者不容易看出 Phase68 测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase68ClosedLoopExecutor: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase68ClosedLoopExecutor: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
