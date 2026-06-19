"""Computer Use 原子鼠标事务回归测试。"""  # 新增代码+AtomicMouseTransaction：说明本文件专门防止连续拖拽被拆成多轮鼠标按下/移动/释放；如果没有这行代码，后续维护者不容易知道这些测试保护的是通用 Computer Use 动作层。
from __future__ import annotations  # 新增代码+AtomicMouseTransaction：延迟解析类型注解；如果没有这行代码，测试在不同 Python 启动方式下更容易受导入顺序影响。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import COMPUTER_USE_MCP_TOOL_NAMES  # 新增代码+AtomicMouseTransaction：导入生产工具名清单；如果没有这行代码，测试只能检查临时副本而不能守住真实工具面。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import FORBIDDEN_LEGACY_RAW_TOOL_NAMES  # 新增代码+AtomicMouseTransaction：导入生产禁止工具名集合；如果没有这行代码，测试无法确认 raw/batch 后门是否也被关上。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import computer_use_mcp_tools  # 新增代码+AtomicMouseTransaction：导入生产 schema 构造入口；如果没有这行代码，测试无法确认模型真正看见的 tools/list。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import dispatch_computer_use_mcp_v2_tool  # 新增代码+AtomicMouseTransaction：导入生产运行时分发入口；如果没有这行代码，测试无法证明直接调用和 batch 调用都被挡住。
from learning_agent.computer_use_mcp_v2.windows_runtime import mcp_session_adapter as session_adapter_module  # 新增代码+AtomicMouseTransaction：导入 session adapter 模块本体以替换内部执行函数；如果没有这行代码，测试无法证明拒绝发生在 controller 前。
from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter import ComputerUseMcpSessionAdapter  # 新增代码+AtomicMouseTransaction：导入生产 session adapter；如果没有这行代码，测试只能覆盖 stdio runtime 而漏掉 agent-side 旧桥接路径。
from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter import _controller_arguments_for_tool  # 新增代码+AtomicMouseTransaction：导入真实 adapter 映射函数；如果没有这行代码，测试无法证明保留的拖拽入口会走单次 drag_path。


SPLIT_MOUSE_TOOL_NAMES = {"left_mouse_down", "left_mouse_up"}  # 新增代码+AtomicMouseTransaction：集中保存不应再暴露给模型的拆分鼠标工具名；如果没有这行代码，多个断言会重复硬编码同一组风险入口。


def test_public_tool_surface_hides_split_left_mouse_transactions() -> None:  # 新增代码+AtomicMouseTransaction：函数段开始，验证模型可见工具面不再诱导拆分拖拽；如果没有这段测试，模型会继续学到 mouse_down/mouse_up 的不稳定路径。
    schema_tool_names = {str(tool.get("name", "")) for tool in computer_use_mcp_tools()}  # 新增代码+AtomicMouseTransaction：读取真实 tools/list 中的工具名；如果没有这一行，测试不知道模型实际会看到什么。
    constant_tool_names = set(COMPUTER_USE_MCP_TOOL_NAMES)  # 新增代码+AtomicMouseTransaction：读取公开常量里的工具名；如果没有这一行，只改 schema 不改常量会漏测。
    for split_tool_name in SPLIT_MOUSE_TOOL_NAMES:  # 新增代码+AtomicMouseTransaction：逐个检查拆分鼠标工具；如果没有这一行，新增风险工具可能只被部分覆盖。
        assert split_tool_name not in schema_tool_names  # 新增代码+AtomicMouseTransaction：要求 tools/list 不暴露拆分工具；如果没有这一行，模型仍可能选择中途会被门禁打断的动作。
        assert split_tool_name not in constant_tool_names  # 新增代码+AtomicMouseTransaction：要求工具常量不包含拆分工具；如果没有这一行，runtime 和工具清单可能漂移。
    assert "left_click_drag" in schema_tool_names  # 新增代码+AtomicMouseTransaction：确认仍保留原子拖拽入口；如果没有这一行，修复可能把通用拖拽能力一起删掉。
    assert "left_click_drag" in constant_tool_names  # 新增代码+AtomicMouseTransaction：确认常量里也保留原子拖拽入口；如果没有这一行，运行时可能把合法拖拽误判未知。
# 新增代码+AtomicMouseTransaction：函数段结束，test_public_tool_surface_hides_split_left_mouse_transactions 到此结束；如果没有这个边界说明，用户不容易看出工具面门禁范围。


def test_split_left_mouse_transactions_are_forbidden_for_direct_and_batch_calls() -> None:  # 新增代码+AtomicMouseTransaction：函数段开始，验证隐藏工具不能通过直接调用或 batch 后门复活；如果没有这段测试，旧模型记住工具名后仍可能绕过 tools/list。
    for split_tool_name in SPLIT_MOUSE_TOOL_NAMES:  # 新增代码+AtomicMouseTransaction：逐个覆盖左键按下和释放；如果没有这一行，只测一个工具会留下另一个半事务入口。
        assert split_tool_name in FORBIDDEN_LEGACY_RAW_TOOL_NAMES  # 新增代码+AtomicMouseTransaction：要求拆分工具进入禁止集合；如果没有这一行，runtime 或 batch 的黑名单不会挡住它。
        direct_result = dispatch_computer_use_mcp_v2_tool(split_tool_name, {"coordinate": [10, 20]})  # 新增代码+AtomicMouseTransaction：通过真实 runtime 直接调用拆分工具；如果没有这一行，测试无法证明 raw 入口被拒绝。
        assert direct_result["ok"] is False  # 新增代码+AtomicMouseTransaction：确认直接调用没有成功；如果没有这一行，拆分鼠标动作可能真实触碰桌面。
        assert direct_result["error_class"] == "legacy_tool_forbidden"  # 新增代码+AtomicMouseTransaction：确认拒绝分类稳定；如果没有这一行，收敛层无法按固定原因改用 left_click_drag。
        batch_result = dispatch_computer_use_mcp_v2_tool("computer_batch", {"actions": [{"tool": split_tool_name, "arguments": {"coordinate": [10, 20]}}]})  # 新增代码+AtomicMouseTransaction：通过真实 batch 尝试调用拆分工具；如果没有这一行，computer_batch 可能成为绕过公开工具面的后门。
        assert batch_result["ok"] is False  # 新增代码+AtomicMouseTransaction：确认 batch 调用没有成功；如果没有这一行，批量动作仍可能制造半按下状态。
        assert batch_result["error_class"] == "legacy_tool_forbidden"  # 新增代码+AtomicMouseTransaction：确认 batch 拒绝也使用同一分类；如果没有这一行，模型无法稳定理解应该换成原子拖拽。
# 新增代码+AtomicMouseTransaction：函数段结束，test_split_left_mouse_transactions_are_forbidden_for_direct_and_batch_calls 到此结束；如果没有这个边界说明，用户不容易看出后门拒绝范围。


def test_left_click_drag_maps_to_one_controller_drag_path_transaction() -> None:  # 新增代码+AtomicMouseTransaction：函数段开始，验证保留的公开拖拽工具会映射成一个 controller drag_path 事务；如果没有这段测试，修复可能只隐藏旧工具但没有证明替代路径存在。
    mapped_arguments = _controller_arguments_for_tool("left_click_drag", {"start_x": 10, "start_y": 20, "end_x": 110, "end_y": 120, "duration_seconds": 0.25})  # 新增代码+AtomicMouseTransaction：使用真实 adapter 映射一个拖拽请求；如果没有这一行，测试无法覆盖生产映射逻辑。
    assert mapped_arguments["action"] == "drag_path"  # 新增代码+AtomicMouseTransaction：确认 controller 收到的是单次拖拽事务；如果没有这一行，动作可能退化成拆分 mouse_down/move/mouse_up。
    assert mapped_arguments["points"] == [{"x": 10, "y": 20}, {"x": 110, "y": 120}]  # 新增代码+AtomicMouseTransaction：确认起点终点被完整保留；如果没有这一行，拖拽路径可能丢坐标或写错方向。
    assert mapped_arguments["button"] == "left"  # 新增代码+AtomicMouseTransaction：确认拖拽使用左键；如果没有这一行，底层可能无法知道按哪个按钮。
    assert mapped_arguments["duration_seconds"] == 0.25  # 新增代码+AtomicMouseTransaction：确认持续时间被保留；如果没有这一行，压力测试中的拖动轨迹可能变得不可控。
# 新增代码+AtomicMouseTransaction：函数段结束，test_left_click_drag_maps_to_one_controller_drag_path_transaction 到此结束；如果没有这个边界说明，用户不容易看出原子拖拽映射范围。


def test_session_adapter_rejects_split_left_mouse_transactions_before_controller(monkeypatch) -> None:  # 新增代码+AtomicMouseTransaction：函数段开始，验证 agent-side adapter 在触碰 controller 前拒绝拆分鼠标事务；如果没有这段测试，隐藏工具仍可能被旧桥接方法直接调用。
    controller_reached = {"value": False}  # 新增代码+AtomicMouseTransaction：记录内部执行函数是否被调用；如果没有这一行，测试无法证明零事件拒绝发生在源头。

    def _fake_execute_desktop_action(*_args, **_kwargs) -> str:  # 新增代码+AtomicMouseTransaction：函数段开始，模拟真实 controller 执行入口；如果没有这段函数，测试可能误触真实桌面或无法判断是否穿透。
        controller_reached["value"] = True  # 新增代码+AtomicMouseTransaction：标记 controller 已被触达；如果没有这一行，测试无法发现拆分工具已经穿透安全边界。
        return "{\"ok\": true}"  # 新增代码+AtomicMouseTransaction：返回可解析成功文本；如果没有这一行，未修复代码可能因 fake 返回形态异常而不是行为错误失败。
    # 新增代码+AtomicMouseTransaction：函数段结束，_fake_execute_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出 fake 执行入口范围。

    monkeypatch.setattr(session_adapter_module.computer_use_internal_adapter_tools, "internal_execute_desktop_action", _fake_execute_desktop_action)  # 新增代码+AtomicMouseTransaction：替换真实桌面执行入口；如果没有这一行，测试可能调用 Windows 真实动作链。
    adapter = ComputerUseMcpSessionAdapter(controller=object())  # 新增代码+AtomicMouseTransaction：创建生产 session adapter；如果没有这一行，测试无法覆盖 agent-side call_atomic_tool 路径。
    for split_tool_name in SPLIT_MOUSE_TOOL_NAMES:  # 新增代码+AtomicMouseTransaction：逐个覆盖左键按下和释放；如果没有这一行，半事务工具可能只挡住一半。
        controller_reached["value"] = False  # 新增代码+AtomicMouseTransaction：每个工具调用前重置穿透标记；如果没有这一行，前一次结果会污染后一次断言。
        result = adapter.call_atomic_tool(split_tool_name, {"x": 10, "y": 20})  # 新增代码+AtomicMouseTransaction：直接调用 agent-side 原子工具入口；如果没有这一行，测试无法证明旧桥接路径被兜底拦截。
        assert result["ok"] is False  # 新增代码+AtomicMouseTransaction：确认拆分工具被拒绝；如果没有这一行，半事务仍可能在真实桌面执行。
        assert result["error_class"] == "desktop_atomic_drag_required"  # 新增代码+AtomicMouseTransaction：确认拒绝原因指向应使用原子拖拽；如果没有这一行，模型不知道如何修正动作计划。
        assert controller_reached["value"] is False  # 新增代码+AtomicMouseTransaction：确认没有进入内部桌面执行；如果没有这一行，测试无法证明低层事件数为零。
# 新增代码+AtomicMouseTransaction：函数段结束，test_session_adapter_rejects_split_left_mouse_transactions_before_controller 到此结束；如果没有这个边界说明，用户不容易看出 adapter 兜底范围。
