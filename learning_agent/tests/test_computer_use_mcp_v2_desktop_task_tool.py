from __future__ import annotations  # 新增代码+DesktopTaskMcpToolTest: 延迟类型注解解析；如果没有这一行，测试 fake 类型在旧解释器上更容易导入失败。

from pathlib import Path  # 新增代码+DesktopTaskModeStoreAlignmentTest: 导入 Path 用于 tmp_path 类型标注；如果没有这一行，路径型测试参数意图不清楚。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import COMPUTER_USE_MCP_TOOL_NAMES, computer_use_mcp_tools  # 新增代码+DesktopTaskMcpToolTest: 导入模型可见工具面；如果没有这一行，测试无法证明 desktop_task 被暴露。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import dispatch_computer_use_mcp_v2_tool  # 新增代码+DesktopTaskMcpToolTest: 导入统一 runtime 分发；如果没有这一行，测试无法证明工具真的可执行。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.types import ComputerUseMcpV2Context  # 新增代码+DesktopTaskMcpToolTest: 导入 MCP 上下文；如果没有这一行，测试无法注入 fake host 和验收事件。
from learning_agent.computer_use_mcp_v2.windows_runtime.desktop_task_runtime import ComputerUseDesktopTaskRuntime, build_default_desktop_task_runtime  # 修改代码+DesktopTaskModeStoreAlignmentTest: 导入 runtime 和默认工厂；如果没有这一行，测试无法覆盖 MCP 高层工具读取 full 状态的路径。
from learning_agent.computer_use_mcp_v2.windows_runtime.mode_session import ComputerUseModeSessionStore  # 新增代码+DesktopTaskModeStoreAlignmentTest: 导入真实 mode store；如果没有这一行，测试无法先写入 /computer use --full 同款状态。
from learning_agent.tool_policy import ToolPolicyDecision  # 新增代码+DesktopTaskMcpToolTest: 导入工具策略决策对象；如果没有这一行，scope 测试无法构造 deferred 基线。
from learning_agent.tools.tool_scope import computer_use_mcp_tool_name, tool_scope_policy_decision  # 新增代码+DesktopTaskMcpToolTest: 导入工具 scope 判断；如果没有这一行，测试无法证明 desktop_task 不再被隐藏。


class FakeDesktopTaskHost:  # 新增代码+DesktopTaskMcpToolTest: 类段开始，模拟真实 host adapter 的高层任务方法；如果没有这个 fake，单测会触碰真实桌面。
    def __init__(self) -> None:  # 新增代码+DesktopTaskMcpToolTest: 函数段开始，初始化调用记录；如果没有这一行，测试无法断言 prompt 传递。
        self.calls: list[tuple[str, dict[str, str]]] = []  # 新增代码+DesktopTaskMcpToolTest: 保存每次调用的 prompt 和参数；如果没有这一行，工具可能丢参数而测试发现不了。
    # 新增代码+DesktopTaskMcpToolTest: 函数段结束，FakeDesktopTaskHost.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def desktop_task(self, prompt: str, arguments: dict[str, str]) -> dict[str, object]:  # 新增代码+DesktopTaskMcpToolTest: 函数段开始，返回一个已完成 Stage Runtime 报告；如果没有这段函数，runtime 会认为 host 不支持 desktop_task。
        self.calls.append((prompt, dict(arguments)))  # 新增代码+DesktopTaskMcpToolTest: 记录调用参数；如果没有这一行，测试无法证明 runtime 把自然语言任务交给 host。
        return {  # 新增代码+DesktopTaskMcpToolTest: 返回低敏结构化阶段证据；如果没有这一行，验收事件无法验证字段透传。
            "passed": True,  # 新增代码+DesktopTaskMcpToolTest: 标记桌面任务 runtime 通过；如果没有这一行，顶层 ok 会被判为 false。
            "desktop_task_completed": True,  # 新增代码+DesktopTaskMcpToolTest: 标记任务完成；如果没有这一行，final gate 不会看到完成证据。
            "universal_stage_task_loop_used": True,  # 新增代码+DesktopTaskMcpToolTest: 标记已进入 Stage Loop；如果没有这一行，验收无法证明新主路径。
            "desktop_task_plan_created": True,  # 新增代码+DesktopTaskMcpToolTest: 标记已创建 DesktopTaskPlan；如果没有这一行，计划层证据缺失。
            "stage_boundary_observation_used": True,  # 新增代码+DesktopTaskMcpToolTest: 标记阶段边界观察；如果没有这一行，速度优化证据缺失。
            "batch_execution_used": True,  # 新增代码+DesktopTaskMcpToolTest: 标记批执行；如果没有这一行，批执行证据缺失。
            "low_level_event_count": 3,  # 新增代码+DesktopTaskMcpToolTest: 标记低层事件数；如果没有这一行，真实动作规模证据缺失。
        }  # 新增代码+DesktopTaskMcpToolTest: fake 报告结束；如果没有这一行，Python 字典语法不完整。
    # 新增代码+DesktopTaskMcpToolTest: 函数段结束，FakeDesktopTaskHost.desktop_task 到此结束；如果没有这个边界说明，用户不容易看出 fake 行为范围。
# 新增代码+DesktopTaskMcpToolTest: 类段结束，FakeDesktopTaskHost 到此结束；如果没有这个边界说明，用户不容易看出 fake host 范围。


class FakeIncompleteDesktopTaskHost:  # 新增代码+DesktopTaskIncompleteGateTest：类段开始，模拟 Stage Runtime 未完成报告；如果没有这个 fake，测试只能靠真实桌面复现失败。
    def desktop_task(self, prompt: str, arguments: dict[str, str]) -> dict[str, object]:  # 新增代码+DesktopTaskIncompleteGateTest：函数段开始，返回未完成阶段证据；如果没有这段函数，desktop_task 工具不会进入未完成路径。
        return {  # 新增代码+DesktopTaskIncompleteGateTest：返回低敏未完成报告；如果没有这行代码，测试无法验证 actionability marker 注入。
            "ok": False,  # 新增代码+DesktopTaskIncompleteGateTest：声明高层任务没有完成；如果没有这一行，run_desktop_task 会把工具误判成功。
            "decision": "desktop_task_incomplete",  # 新增代码+DesktopTaskIncompleteGateTest：写入稳定未完成决策；如果没有这一行，错误分类可能不稳定。
            "desktop_task_completed": False,  # 新增代码+DesktopTaskIncompleteGateTest：写入未完成事实的反面；如果没有这一行，final gate 可能读不到完成布尔值。
            "desktop_task_incomplete": True,  # 新增代码+DesktopTaskIncompleteGateTest：写入未完成事实；如果没有这一行，MCP 工具不知道要加收敛 marker。
            "stage_count": 5,  # 新增代码+DesktopTaskIncompleteGateTest：写入总阶段数；如果没有这一行，未完成状态缺阶段规模证据。
            "completed_stage_count": 2,  # 新增代码+DesktopTaskIncompleteGateTest：写入已完成阶段数；如果没有这一行，未完成状态缺进度证据。
            "run_state": {"active_target_ref": "target_1"},  # 新增代码+DesktopTaskIncompleteGateTest：写入当前目标引用；如果没有这一行，observe 恢复可能缺窗口绑定。
        }  # 新增代码+DesktopTaskIncompleteGateTest：未完成报告结束；如果没有这一行，Python 字典语法不完整。
    # 新增代码+DesktopTaskIncompleteGateTest：函数段结束，FakeIncompleteDesktopTaskHost.desktop_task 到此结束；如果没有这个边界说明，用户不容易看出 fake 输出范围。
# 新增代码+DesktopTaskIncompleteGateTest：类段结束，FakeIncompleteDesktopTaskHost 到此结束；如果没有这个边界说明，用户不容易看出 fake host 范围。


class FakeRealDesktopTaskLoop:  # 新增代码+DesktopTaskExplicitToolTest: 类段开始，模拟已接 Stage Runtime 的真实执行闭环；如果没有这个 fake，单测会启动真实桌面软件。
    def __init__(self) -> None:  # 新增代码+DesktopTaskExplicitToolTest: 函数段开始，初始化调用记录；如果没有这一行，测试无法证明 target_hint 被传入。
        self.calls: list[tuple[str, str]] = []  # 新增代码+DesktopTaskExplicitToolTest: 保存 target_app 和 prompt；如果没有这一行，runtime 可能仍用 desktop_app 而测试发现不了。
    # 新增代码+DesktopTaskExplicitToolTest: 函数段结束，FakeRealDesktopTaskLoop.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def run_desktop_task(self, target_app: str, prompt: str) -> dict[str, object]:  # 新增代码+DesktopTaskExplicitToolTest: 函数段开始，返回完整成功阶段证据；如果没有这段函数，runtime 无法模拟真实 Stage Loop。
        self.calls.append((target_app, prompt))  # 新增代码+DesktopTaskExplicitToolTest: 记录调用参数；如果没有这一行，测试无法断言授权目标没有丢失。
        return {  # 新增代码+DesktopTaskExplicitToolTest: 返回真实路径需要的低敏证据；如果没有这一行，_real_execution_report 会判为失败。
            "ok": True,  # 新增代码+DesktopTaskExplicitToolTest: 标记执行闭环成功；如果没有这一项，runtime 不会通过。
            "decision": "desktop_task_completed",  # 新增代码+DesktopTaskExplicitToolTest: 标记任务完成决策；如果没有这一项，报告无法解释结束原因。
            "computer_use_gui_route_used": True,  # 新增代码+DesktopTaskExplicitToolTest: 标记 GUI 路由已使用；如果没有这一项，验收器会认为不是 Computer Use。
            "owned_window_verified": True,  # 新增代码+DesktopTaskExplicitToolTest: 标记目标窗口已验证；如果没有这一项，真实动作可能缺目标身份。
            "low_level_event_count": 2,  # 新增代码+DesktopTaskExplicitToolTest: 标记低层事件大于 0；如果没有这一项，runtime 会拒绝口头成功。
            "real_desktop_touched": True,  # 新增代码+DesktopTaskExplicitToolTest: 标记真实桌面触达；如果没有这一项，报告会停在 recording。
            "desktop_task_completed": True,  # 新增代码+DesktopTaskExplicitToolTest: 标记阶段任务完成；如果没有这一项，final gate 缺主证据。
            "universal_stage_task_loop_used": True,  # 新增代码+DesktopTaskExplicitToolTest: 标记使用 Stage Loop；如果没有这一项，验收无法证明新架构生效。
            "desktop_task_plan_created": True,  # 新增代码+DesktopTaskExplicitToolTest: 标记计划已创建；如果没有这一项，Stage Planner 证据缺失。
            "stage_boundary_observation_used": True,  # 新增代码+DesktopTaskExplicitToolTest: 标记阶段边界观察；如果没有这一项，速度优化证据缺失。
            "batch_execution_used": True,  # 新增代码+DesktopTaskExplicitToolTest: 标记批执行；如果没有这一项，batch executor 证据缺失。
        }  # 新增代码+DesktopTaskExplicitToolTest: fake 报告结束；如果没有这一行，Python 字典语法不完整。
    # 新增代码+DesktopTaskExplicitToolTest: 函数段结束，FakeRealDesktopTaskLoop.run_desktop_task 到此结束；如果没有这个边界说明，用户不容易看出 fake 执行范围。
# 新增代码+DesktopTaskExplicitToolTest: 类段结束，FakeRealDesktopTaskLoop 到此结束；如果没有这个边界说明，用户不容易看出强制入口 fake 范围。


def test_desktop_task_tool_is_visible_before_atomic_tools() -> None:  # 新增代码+DesktopTaskMcpToolTest: 函数段开始，验证模型可见高层工具入口；如果没有这段测试，工具可能没暴露导致真实终端仍走原子链。
    names = [tool["name"] for tool in computer_use_mcp_tools()]  # 新增代码+DesktopTaskMcpToolTest: 读取 tools/list 中的名字；如果没有这一行，测试只能看内部常量。
    assert "desktop_task" in COMPUTER_USE_MCP_TOOL_NAMES  # 新增代码+DesktopTaskMcpToolTest: 断言内部清单包含新工具；如果没有这一行，runtime 会拒绝未知工具。
    assert names.index("desktop_task") < names.index("open_application")  # 新增代码+DesktopTaskMcpToolTest: 断言高层工具排在原子启动前；如果没有这一行，模型更容易继续优先选择 open_application。
    assert "阶段规划" in next(tool["description"] for tool in computer_use_mcp_tools() if tool["name"] == "desktop_task")  # 新增代码+DesktopTaskMcpToolTest: 断言描述明确提示 Stage Runtime；如果没有这一行，模型不知道何时使用它。
# 新增代码+DesktopTaskMcpToolTest: 函数段结束，test_desktop_task_tool_is_visible_before_atomic_tools 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_desktop_task_tool_scope_allows_operation_mode() -> None:  # 新增代码+DesktopTaskMcpToolTest: 函数段开始，验证 Computer Use 操作模式不会隐藏 desktop_task；如果没有这段测试，真实终端仍会提示 scope_blocked。
    class Agent:  # 新增代码+DesktopTaskMcpToolTest: 类段开始，构造最小 agent scope 对象；如果没有这个 fake，测试必须启动真实 agent。
        tool_scope_mode = "computer_use_operation"  # 新增代码+DesktopTaskMcpToolTest: 模拟 `/computer use --full` 后的操作模式；如果没有这一行，scope 判断会回到代码开发模式。
    # 新增代码+DesktopTaskMcpToolTest: 类段结束，Agent 到此结束；如果没有这个边界说明，用户不容易看出 fake agent 范围。
    class Tool:  # 新增代码+DesktopTaskMcpToolTest: 类段开始，构造最小 MCP 工具对象；如果没有这个 fake，测试需要依赖 catalog runtime。
        name = computer_use_mcp_tool_name("desktop_task")  # 新增代码+DesktopTaskMcpToolTest: 使用真实前缀工具名；如果没有这一行，scope 不会识别为 MCP 工具。
        server_name = "computer-use"  # 新增代码+DesktopTaskMcpToolTest: 保存 server 名；如果没有这一行，未来解析路径变化时测试覆盖不足。
        original_name = "desktop_task"  # 新增代码+DesktopTaskMcpToolTest: 保存原始工具名；如果没有这一行，scope 无法命中新白名单。
    # 新增代码+DesktopTaskMcpToolTest: 类段结束，Tool 到此结束；如果没有这个边界说明，用户不容易看出 fake tool 范围。
    base = ToolPolicyDecision(state="deferred", visible=False, selectable=True, executable=False, reason="test deferred")  # 新增代码+DesktopTaskMcpToolTest: 构造 deferred 基线；如果没有这一行，无法证明 scope 会自动加载工具。
    decision = tool_scope_policy_decision(Agent(), Tool(), base)  # 新增代码+DesktopTaskMcpToolTest: 执行真实 scope 判断；如果没有这一行，测试没有被测行为。
    assert decision.state == "loaded"  # 新增代码+DesktopTaskMcpToolTest: 断言操作模式自动加载 desktop_task；如果没有这一行，scope_blocked 回归不会被发现。
    assert decision.visible is True  # 新增代码+DesktopTaskMcpToolTest: 断言模型可见；如果没有这一行，tools/list 仍可能隐藏新入口。
    assert decision.executable is True  # 新增代码+DesktopTaskMcpToolTest: 断言执行层可调用；如果没有这一行，模型即使看到工具也可能执行失败。
# 新增代码+DesktopTaskMcpToolTest: 函数段结束，test_desktop_task_tool_scope_allows_operation_mode 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_desktop_task_dispatch_emits_stage_evidence_to_acceptance_event() -> None:  # 新增代码+DesktopTaskMcpToolTest: 函数段开始，验证 runtime 会把阶段证据写入验收事件；如果没有这段测试，可见终端无法断言新路径。
    host = FakeDesktopTaskHost()  # 新增代码+DesktopTaskMcpToolTest: 创建 fake host；如果没有这一行，工具没有执行对象。
    events: list[tuple[str, dict[str, object]]] = []  # 新增代码+DesktopTaskMcpToolTest: 准备收集验收事件；如果没有这一行，测试看不到事件 payload。
    context = ComputerUseMcpV2Context(host=host, emit_acceptance_event=lambda state, payload: events.append((state, payload)))  # 新增代码+DesktopTaskMcpToolTest: 构造带 fake host 和事件回调的上下文；如果没有这一行，runtime 会走无 host 错误。
    context.allowed_apps = [{"bundleId": "notepad", "displayName": "Notepad"}]  # 新增代码+DesktopTaskExplicitToolTest: 模拟 request_access 已授权一个普通本地应用；如果没有这一行，target_hint 自动补全路径没有测试覆盖。
    result = dispatch_computer_use_mcp_v2_tool("desktop_task", {"prompt": "请使用本机文本编辑软件输入 hello everyone。"}, context)  # 新增代码+DesktopTaskMcpToolTest: 执行新工具；如果没有这一行，测试无法证明 dispatch 接通。
    assert result["ok"] is True  # 新增代码+DesktopTaskMcpToolTest: 断言 fake 完成报告会让顶层 ok 为真；如果没有这一行，模型可能误以为工具失败。
    assert host.calls and host.calls[0][0].startswith("请使用本机文本编辑软件")  # 新增代码+DesktopTaskMcpToolTest: 断言自然语言任务传给 host；如果没有这一行，prompt 可能在 runtime 丢失。
    assert host.calls[0][1]["target_hint"] == "notepad"  # 新增代码+DesktopTaskExplicitToolTest: 断言 desktop_task 会复用最近授权应用作为目标提示；如果没有这一行，真实终端会丢失启动目标。
    assert events[-1][0] == "computer_use_mcp_v2_tool"  # 新增代码+DesktopTaskMcpToolTest: 断言 runtime 发出了标准验收事件；如果没有这一行，controller 无法观察工具调用。
    assert events[-1][1]["universal_stage_task_loop_used"] is True  # 新增代码+DesktopTaskMcpToolTest: 断言 Stage Loop 证据进入事件；如果没有这一行，真实验收仍只能看到 ok。
    assert events[-1][1]["desktop_task_plan_created"] is True  # 新增代码+DesktopTaskMcpToolTest: 断言计划创建证据进入事件；如果没有这一行，架构层证据缺失。
    assert events[-1][1]["stage_boundary_observation_used"] is True  # 新增代码+DesktopTaskMcpToolTest: 断言阶段观察证据进入事件；如果没有这一行，速度优化证据不可见。
    assert events[-1][1]["batch_execution_used"] is True  # 新增代码+DesktopTaskMcpToolTest: 断言批执行证据进入事件；如果没有这一行，批执行验收不可见。
    assert events[-1][1]["low_level_event_count"] == 3  # 新增代码+DesktopTaskMcpToolTest: 断言低层事件数进入事件；如果没有这一行，真实动作规模不可见。
# 新增代码+DesktopTaskMcpToolTest: 函数段结束，test_desktop_task_dispatch_emits_stage_evidence_to_acceptance_event 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_desktop_task_incomplete_result_contains_actionability_marker() -> None:  # 新增代码+DesktopTaskIncompleteGateTest：函数段开始，验证真实 desktop_task 工具未完成时会输出收敛 marker；如果没有这个测试，运行态门禁可能拿不到协议。
    context = ComputerUseMcpV2Context(host=FakeIncompleteDesktopTaskHost())  # 新增代码+DesktopTaskIncompleteGateTest：构造未完成 fake host 上下文；如果没有这行代码，工具没有执行对象。
    result = dispatch_computer_use_mcp_v2_tool("desktop_task", {"prompt": "请继续完成 GUI 阶段任务。"}, context)  # 新增代码+DesktopTaskIncompleteGateTest：执行真实 MCP 分发入口；如果没有这行代码，测试只会覆盖内部 helper。
    assert result["ok"] is False  # 新增代码+DesktopTaskIncompleteGateTest：确认未完成会让顶层 ok 为假；如果没有这行代码，模型可能把未完成当成功。
    assert result["error_class"] == "desktop_task_incomplete"  # 新增代码+DesktopTaskIncompleteGateTest：确认错误分类稳定；如果没有这行代码，controller 难以统计未完成。
    assert "OPENHARNESS_DESKTOP_TASK_INCOMPLETE" in result["payload"]["actionability"]  # 新增代码+DesktopTaskIncompleteGateTest：确认收敛 marker 被注入 payload；如果没有这行代码，后续轮次不能硬挡原子动作 fallback。
    assert "next_required_tool=mcp__computer-use__desktop_task" in result["payload"]["actionability"]  # 新增代码+DesktopTaskIncompleteGateTest：确认下一步要求回到高层工具；如果没有这行代码，模型仍可能继续 key/click/drag。
# 新增代码+DesktopTaskIncompleteGateTest：函数段结束，test_desktop_task_incomplete_result_contains_actionability_marker 到此结束；如果没有这个边界说明，初学者不容易看出 marker 断言范围。


def test_desktop_task_runtime_force_entry_bypasses_legacy_not_desktop_classifier() -> None:  # 新增代码+DesktopTaskExplicitToolTest: 函数段开始，验证显式 desktop_task 入口不会再被旧分类器误判挡住；如果没有这段测试，乱码中文 prompt 会回归 not_desktop_task。
    fake_loop = FakeRealDesktopTaskLoop()  # 新增代码+DesktopTaskExplicitToolTest: 创建 fake 真实执行闭环；如果没有这一行，测试会触碰本机桌面。
    runtime = ComputerUseDesktopTaskRuntime.for_test(full_mode=True)  # 新增代码+DesktopTaskExplicitToolTest: 创建已启用 full mode 的隔离 runtime；如果没有这一行，run_prompt 会被权限门禁挡住。
    runtime.real_execution_loop = fake_loop  # 新增代码+DesktopTaskExplicitToolTest: 注入 fake Stage Runtime；如果没有这一行，测试无法观察真实执行入口是否被调用。
    report = runtime.run_prompt("璇蜂娇鐢ㄦ湰鏈轰换鎰 hello everyone", real_actions=True, force_desktop_task=True, target_hint="notepad")  # 新增代码+DesktopTaskExplicitToolTest: 用类似终端乱码的 prompt 调用显式入口；如果没有这一行，旧 bug 没有回归样本。
    assert fake_loop.calls == [("notepad", "璇蜂娇鐢ㄦ湰鏈轰换鎰 hello everyone")]  # 新增代码+DesktopTaskExplicitToolTest: 断言运行时进入 Stage Loop 且保留授权目标；如果没有这一行，not_desktop_task 回归发现不了。
    assert report["passed"] is True  # 新增代码+DesktopTaskExplicitToolTest: 断言强制入口形成通过报告；如果没有这一行，runtime 可能调用了 loop 但仍判失败。
    assert report["decision"] == "desktop_task_completed"  # 新增代码+DesktopTaskExplicitToolTest: 断言结束原因不是 not_desktop_task；如果没有这一行，失败原因可能继续被掩盖。
# 新增代码+DesktopTaskExplicitToolTest: 函数段结束，test_desktop_task_runtime_force_entry_bypasses_legacy_not_desktop_classifier 到此结束；如果没有这个边界说明，用户不容易看出强制入口测试范围。


def test_default_desktop_task_runtime_reads_workspace_full_mode_store(tmp_path: Path) -> None:  # 新增代码+DesktopTaskModeStoreAlignmentTest: 函数段开始，验证默认工厂和真实终端使用同一个 mode_sessions 目录；如果没有这段测试，desktop_task 会再次误报 full_mode_required。
    workspace = tmp_path / "learning_agent"  # 新增代码+DesktopTaskModeStoreAlignmentTest: 模拟 start_oauth_agent.bat 传入的 learning_agent workspace；如果没有这一行，测试不能覆盖真实可见终端路径。
    mode_root = workspace / "memory" / "computer_use" / "mode_sessions"  # 新增代码+DesktopTaskModeStoreAlignmentTest: 计算真实终端 `/computer use --full` 的 mode store 目录；如果没有这一行，测试写入路径可能和交互层不一致。
    ComputerUseModeSessionStore(base_dir=mode_root).open_full_mode(reason="test full mode")  # 新增代码+DesktopTaskModeStoreAlignmentTest: 先写入 full_mode=true 状态；如果没有这一行，默认 runtime 没有可读取事实。
    runtime = build_default_desktop_task_runtime(workspace)  # 新增代码+DesktopTaskModeStoreAlignmentTest: 用默认 MCP 工厂构造 desktop_task runtime；如果没有这一行，测试没有被测对象。
    assert runtime.mode_store.base_dir == mode_root  # 新增代码+DesktopTaskModeStoreAlignmentTest: 断言工厂使用同一个 mode_sessions 目录；如果没有这一行，路径对齐回归发现不了。
    assert runtime._mode_status()["full_mode"] is True  # 新增代码+DesktopTaskModeStoreAlignmentTest: 断言 runtime 能读到 full 模式；如果没有这一行，computer_use_full_mode_required 会在真实终端复发。
# 新增代码+DesktopTaskModeStoreAlignmentTest: 函数段结束，test_default_desktop_task_runtime_reads_workspace_full_mode_store 到此结束；如果没有这个边界说明，用户不容易看出 mode store 对齐测试范围。
