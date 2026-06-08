import tempfile  # 新增代码+RealPhysicalFullMode：导入临时目录工具隔离测试 workspace；如果没有这一行，测试会把运行证据写进用户真实项目目录。
import unittest  # 新增代码+RealPhysicalFullMode：导入标准测试框架；如果没有这一行，本文件不会被 unittest 正常组织和执行。
from pathlib import Path  # 新增代码+RealPhysicalFullMode：导入路径对象用于构造 agent workspace；如果没有这一行，路径只能用脆弱字符串传递。
from typing import Any  # 新增代码+RealPhysicalFullMode：导入动态类型标注；如果没有这一行，fake runtime 的输入输出边界不清楚。

from learning_agent.computer_use.universal_observe_plan_act_verify import UniversalObservePlanActVerifyLoop  # 新增代码+RealPhysicalFullMode：导入通用观察-规划-动作-验证 loop；如果没有这一行，测试无法证明真实派发状态是否会向上冒泡。
from learning_agent.core.agent import LearningAgent, ToolCallingFakeModel  # 新增代码+RealPhysicalFullMode：导入真实 agent 构造入口和离线假模型；如果没有这一行，测试无法覆盖默认 /computer use --full 生产接线。


class RealDispatchingActionRuntimeForTest:  # 新增代码+RealPhysicalFullMode：类段开始，模拟已经真实派发的动作 runtime；如果没有这个类，单元测试只能真的移动鼠标键盘才知道状态是否冒泡。
    def __init__(self) -> None:  # 新增代码+RealPhysicalFullMode：函数段开始，初始化 fake runtime 的真实派发状态；如果没有这段函数，loop 读取不到 runtime 级状态。
        self.real_dispatch_performed = False  # 新增代码+RealPhysicalFullMode：默认先声明尚未真实派发；如果没有这一行，测试无法验证 dispatch 后状态变化。
    # 新增代码+RealPhysicalFullMode：函数段结束，RealDispatchingActionRuntimeForTest.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def open_target_session(self, raw_target: Any, candidates: list[dict[str, Any]] | None = None) -> dict[str, Any]:  # 新增代码+RealPhysicalFullMode：函数段开始，提供 loop 需要的最小目标 session 接口；如果没有这段函数，测试会停在接口错误而不是验证真实派发冒泡。
        del candidates  # 新增代码+RealPhysicalFullMode：声明本 fake 不使用候选列表；如果没有这一行，读者会误以为测试依赖真实应用发现。
        return {"session_id": "real-dispatch-test-session", "target": str(raw_target), "target_window": {"app_id": f"{raw_target}.exe", "window_id": "test-window", "title_preview": "Test Window"}, "target_identity_verification": {"target_identity_verified": True}}  # 新增代码+RealPhysicalFullMode：返回已复核目标身份的脱敏 session；如果没有这一行，loop 无法进入动作分发阶段。
    # 新增代码+RealPhysicalFullMode：函数段结束，RealDispatchingActionRuntimeForTest.open_target_session 到此结束；如果没有这个边界说明，初学者不容易看出 fake session 范围。

    def dispatch(self, session: dict[str, Any], action: dict[str, Any], current_window: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+RealPhysicalFullMode：函数段开始，模拟一次底层动作分发；如果没有这段函数，UniversalObservePlanActVerifyLoop 无法执行 action。
        del session, action, current_window  # 新增代码+RealPhysicalFullMode：声明本 fake 不依赖这些输入；如果没有这一行，读者会误以为这些参数参与了判断。
        self.real_dispatch_performed = True  # 新增代码+RealPhysicalFullMode：模拟真实 sender 已触达物理桌面；如果没有这一行，loop 没有状态可以向上汇总。
        return {"ok": True, "low_level_event_count": 3, "real_dispatch_performed": True, "real_desktop_touched": True}  # 新增代码+RealPhysicalFullMode：返回真实派发形状的脱敏报告；如果没有这一行，loop 只能看到普通成功而看不到物理派发事实。
    # 新增代码+RealPhysicalFullMode：函数段结束，RealDispatchingActionRuntimeForTest.dispatch 到此结束；如果没有这个边界说明，初学者不容易看出 fake 派发范围。
# 新增代码+RealPhysicalFullMode：类段结束，RealDispatchingActionRuntimeForTest 到此结束；如果没有这个边界说明，初学者不容易看出 fake runtime 的边界。


class WindowsComputerUseFullRealPhysicalSenderTests(unittest.TestCase):  # 新增代码+RealPhysicalFullMode：类段开始，集中验证 full 模式默认真实物理 sender 接线；如果没有这个类，本轮“打开真实物理鼠标键盘”的升级没有自动化护栏。
    def test_loop_propagates_real_dispatch_from_action_runtime(self) -> None:  # 新增代码+RealPhysicalFullMode：函数段开始，验证 loop 会把 action runtime 的真实派发结果向上报告；如果没有这个测试，底层真实 SendInput 可能已经发生但顶层仍显示 false。
        action_runtime = RealDispatchingActionRuntimeForTest()  # 新增代码+RealPhysicalFullMode：创建安全 fake action runtime；如果没有这一行，测试可能触碰真实桌面。
        loop = UniversalObservePlanActVerifyLoop(action_runtime=action_runtime, max_retries=0)  # 新增代码+RealPhysicalFullMode：把 fake runtime 注入通用 loop；如果没有这一行，测试只会覆盖默认录制 sender。
        result = loop.run_task({"target": "mspaint", "actions": [{"type": "drag_path", "points": [{"x": 1, "y": 1}, {"x": 2, "y": 2}]}]})  # 新增代码+RealPhysicalFullMode：执行一条代表性拖拽任务；如果没有这一行，断言没有真实 loop 结果可检查。
        self.assertTrue(result["ok"])  # 新增代码+RealPhysicalFullMode：断言 fake 成功任务仍保持成功；如果没有这一行，状态冒泡测试可能掩盖执行失败。
        self.assertTrue(result["real_dispatch_performed"])  # 新增代码+RealPhysicalFullMode：断言 loop 顶层看到真实派发；如果没有这一行，用户终端仍可能误显示 real_dispatch_performed=false。
        self.assertTrue(result["real_desktop_touched"])  # 新增代码+RealPhysicalFullMode：断言 loop 顶层看到桌面触达；如果没有这一行，成熟度矩阵会继续漏掉真实触桌事实。
    # 新增代码+RealPhysicalFullMode：函数段结束，test_loop_propagates_real_dispatch_from_action_runtime 到此结束；如果没有这个边界说明，初学者不容易看出状态冒泡测试范围。

    def test_default_agent_runtime_wires_controlled_physical_sender_to_windows_sendinput_backend(self) -> None:  # 新增代码+RealPhysicalFullMode：函数段开始，验证默认 agent runtime 接入 Phase95 受控物理 sender 和 Windows SendInput 后端；如果没有这个测试，生产路径可能继续停在只观察不动作。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RealPhysicalFullMode：创建一次性 workspace；如果没有这一行，测试会污染用户真实 memory。
            agent = LearningAgent(model=ToolCallingFakeModel([]), workspace=Path(raw_dir), ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+RealPhysicalFullMode：创建未手动注入 runtime 的真实 agent；如果没有这一行，测试不能覆盖默认生产构造路径。
            runtime = agent._desktop_task_runtime_for_current_run()  # 新增代码+RealPhysicalFullMode：调用默认 runtime 工厂；如果没有这一行，断言只是在猜源码结构。
            adapter = getattr(runtime, "real_execution_loop", None)  # 新增代码+RealPhysicalFullMode：取得 full 模式真实执行 adapter；如果没有这一行，测试无法检查最后一跳接线。
            self.assertTrue(getattr(adapter, "controlled_physical_sender_configured", False))  # 新增代码+RealPhysicalFullMode：断言 adapter 已配置受控物理 sender；如果没有这一行，默认 full 模式仍不会尝试真实鼠标键盘。
            inner_loop = getattr(adapter, "loop", None)  # 新增代码+RealPhysicalFullMode：取得 adapter 内部通用 loop；如果没有这一行，无法继续检查动作 runtime。
            action_runtime = getattr(inner_loop, "action_runtime", None)  # 新增代码+RealPhysicalFullMode：取得通用动作 runtime；如果没有这一行，最后一跳 sender 无法被定位。
            controlled_sender = getattr(action_runtime, "low_level_sender", None)  # 新增代码+RealPhysicalFullMode：读取动作 runtime 的低层 sender；如果没有这一行，测试无法确认是否真接 Phase95。
            backend = getattr(controlled_sender, "low_level_backend", None)  # 新增代码+RealPhysicalFullMode：读取 Phase95 背后的真实底层后端；如果没有这一行，Phase95 可能只是空壳不会发鼠标键盘。
            self.assertIn("WindowsControlledPhysicalSendInputSender", type(controlled_sender).__name__)  # 新增代码+RealPhysicalFullMode：断言最后一跳先经过受控 sender；如果没有这一行，代码可能绕过安全门直接发输入。
            self.assertIn("WindowsSendInputLowLevelSender", type(backend).__name__)  # 新增代码+RealPhysicalFullMode：断言受控 sender 背后是真实 Windows SendInput 后端；如果没有这一行，默认 full 模式仍可能只是 fake 后端。
    # 新增代码+RealPhysicalFullMode：函数段结束，test_default_agent_runtime_wires_controlled_physical_sender_to_windows_sendinput_backend 到此结束；如果没有这个边界说明，初学者不容易看出默认接线测试范围。
# 新增代码+RealPhysicalFullMode：类段结束，WindowsComputerUseFullRealPhysicalSenderTests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合边界。


if __name__ == "__main__":  # 新增代码+RealPhysicalFullMode：文件入口段开始，允许直接运行本测试文件；如果没有这一行，初学者需要记完整 unittest 命令。
    unittest.main()  # 新增代码+RealPhysicalFullMode：启动 unittest；如果没有这一行，直接运行文件不会执行测试。
# 新增代码+RealPhysicalFullMode：文件入口段结束，本测试文件到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
