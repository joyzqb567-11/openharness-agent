"""Computer Use MCP v2 旧成熟能力端口隔离边界。"""  # 修改代码+ComputerUseMcpV2HostAdapter：说明本文件只允许 v2 内部复用旧 controller/session 能力；如果没有这一行，读者容易误以为旧工具还能直接暴露给模型。
from __future__ import annotations  # 修改代码+ComputerUseMcpV2HostAdapter：延迟类型注解解析；如果没有这一行，跨模块类型引用更容易在导入阶段互相卡住。

from dataclasses import dataclass  # 新增代码+ComputerUseMcpV2HostAdapter：导入 dataclass 简化 host adapter 构造；如果没有这一行，就要手写初始化样板代码。
from typing import Any  # 新增代码+ComputerUseMcpV2HostAdapter：导入通用类型用于 agent 和 payload 边界；如果没有这一行，动态 agent 对象的接口意图不清楚。

from .build_tools import FORBIDDEN_LEGACY_RAW_TOOL_NAMES  # 修改代码+ComputerUseMcpV2HostAdapter：导入旧名黑名单；如果没有这一行，隔离边界会和 schema 清单漂移。

try:  # 新增代码+ComputerUseMcpV2HostAdapter：优先按包路径导入旧成熟 session adapter 和门禁；如果没有这一段，v2 内部无法复用旧状态、观察、执行链。
    from learning_agent.computer_use_mcp_v2.windows_runtime.action_gates import computer_use_agent_owned_launch_rejection as legacy_agent_owned_launch_rejection  # 修改代码+ComputerUseMcpV2HostAdapter：从 v2 windows_runtime 导入“必须先启动目标应用”门禁；如果没有这一行，v2 click/type 仍会依赖旧目录或可能操作用户旧窗口。
    from learning_agent.computer_use_mcp_v2.windows_runtime.action_gates import computer_use_full_completion_signal_for_action as legacy_completion_signal_for_action  # 修改代码+ComputerUseMcpV2HostAdapter：从 v2 windows_runtime 导入完成收束门禁；如果没有这一行，v2 动作可能在任务完成后继续改变桌面。
    from learning_agent.computer_use_mcp_v2.windows_runtime.action_gates import computer_use_observe_before_action_rejection as legacy_observe_before_action_rejection  # 修改代码+ComputerUseMcpV2HostAdapter：从 v2 windows_runtime 导入“先观察再动作”门禁；如果没有这一行，v2 鼠标键盘可能盲动。
    from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter import ComputerUseMcpSessionAdapter, ComputerUseMcpSessionCallbacks, ComputerUseMcpSessionState  # 修改代码+ComputerUseMcpV2HostAdapter：从 v2 windows_runtime 导入原子工具到 controller 的成熟 adapter；如果没有这一行，v2 只能调用空壳 no-op。
    from learning_agent.computer_use_mcp_v2.windows_runtime.runtime_trace import image_artifact_recorder as legacy_image_artifact_recorder  # 修改代码+ComputerUseMcpV2HostAdapter：从 v2 windows_runtime 导入截图 artifact 登记器；如果没有这一行，observe/action 的图片证据不会回到 agent。
    from learning_agent.computer_use_mcp_v2.windows_runtime.runtime_trace import runtime_trace_recorder as legacy_runtime_trace_recorder  # 修改代码+ComputerUseMcpV2HostAdapter：从 v2 windows_runtime 导入 runtime trace 记录器；如果没有这一行，执行链证据不会进入长任务审计。
    from learning_agent.core import run_helpers as run_helpers_from_core  # 新增代码+ComputerUseMcpV2HostAdapter：导入安全 observation 写入 helper；如果没有这一行，fake agent 缺字段时写日志可能崩溃。
except ModuleNotFoundError as error:  # 新增代码+ComputerUseMcpV2HostAdapter：兼容 start_oauth_agent.bat 直接脚本启动路径；如果没有这一行，脚本模式可能找不到 learning_agent 包前缀。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.action_gates", "learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter", "learning_agent.computer_use_mcp_v2.windows_runtime.runtime_trace", "learning_agent.core", "learning_agent.core.run_helpers"}:  # 修改代码+ComputerUseMcpV2HostAdapter：只吞 v2 windows_runtime 路径差异类导入错误；如果没有这一行，真实内部 bug 会被误当兼容问题。
        raise  # 新增代码+ComputerUseMcpV2HostAdapter：重新抛出真实导入错误；如果没有这一行，排查旧 adapter 内部 bug 会很困难。
    from computer_use_mcp_v2.windows_runtime.action_gates import computer_use_agent_owned_launch_rejection as legacy_agent_owned_launch_rejection  # type: ignore  # 修改代码+ComputerUseMcpV2HostAdapter：脚本模式从 v2 windows_runtime 导入启动门禁；如果没有这一行，bat 模式下 v2 动作缺少窗口归属约束。
    from computer_use_mcp_v2.windows_runtime.action_gates import computer_use_full_completion_signal_for_action as legacy_completion_signal_for_action  # type: ignore  # 修改代码+ComputerUseMcpV2HostAdapter：脚本模式从 v2 windows_runtime 导入完成门禁；如果没有这一行，bat 模式下 v2 任务可能过度操作。
    from computer_use_mcp_v2.windows_runtime.action_gates import computer_use_observe_before_action_rejection as legacy_observe_before_action_rejection  # type: ignore  # 修改代码+ComputerUseMcpV2HostAdapter：脚本模式从 v2 windows_runtime 导入观察门禁；如果没有这一行，bat 模式下 v2 鼠标键盘会缺少先观察保护。
    from computer_use_mcp_v2.windows_runtime.mcp_session_adapter import ComputerUseMcpSessionAdapter, ComputerUseMcpSessionCallbacks, ComputerUseMcpSessionState  # type: ignore  # 修改代码+ComputerUseMcpV2HostAdapter：脚本模式从 v2 windows_runtime 导入 session adapter；如果没有这一行，bat 模式下 v2 无法调用真实 controller。
    from computer_use_mcp_v2.windows_runtime.runtime_trace import image_artifact_recorder as legacy_image_artifact_recorder  # type: ignore  # 修改代码+ComputerUseMcpV2HostAdapter：脚本模式从 v2 windows_runtime 导入截图登记器；如果没有这一行，bat 模式下截图证据不会归档。
    from computer_use_mcp_v2.windows_runtime.runtime_trace import runtime_trace_recorder as legacy_runtime_trace_recorder  # type: ignore  # 修改代码+ComputerUseMcpV2HostAdapter：脚本模式从 v2 windows_runtime 导入 trace 记录器；如果没有这一行，bat 模式下执行证据会断链。
    from core import run_helpers as run_helpers_from_core  # type: ignore  # 新增代码+ComputerUseMcpV2HostAdapter：脚本模式导入安全 observation helper；如果没有这一行，bat 模式下日志写入可能崩溃。


def is_legacy_or_forbidden_tool(raw_name: str) -> bool:  # 修改代码+ComputerUseMcpV2HostAdapter：函数段开始，判断某个工具名是否旧接口或禁止名；如果没有这段函数，调用方会各自维护旧名判断。
    return str(raw_name or "").strip().removeprefix("mcp__computer-use__") in FORBIDDEN_LEGACY_RAW_TOOL_NAMES  # 修改代码+ComputerUseMcpV2HostAdapter：返回旧名命中状态；如果没有这一行，batch 和 runtime 的禁止规则可能不一致。
# 修改代码+ComputerUseMcpV2HostAdapter：函数段结束，is_legacy_or_forbidden_tool 到此结束；如果没有这个边界说明，用户不容易看出旧接口隔离范围。


def _computer_use_mcp_state(agent: Any) -> ComputerUseMcpSessionState:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，获取或创建旧 session adapter 的共享状态；如果没有这段函数，授权和剪贴板会在每次 v2 调用后丢失。
    state = getattr(agent, "_computer_use_mcp_session_state", None)  # 新增代码+ComputerUseMcpV2HostAdapter：读取 agent 上已有旧 MCP session 状态；如果没有这一行，无法复用 request_access/list_granted_applications 的闭环状态。
    if isinstance(state, ComputerUseMcpSessionState):  # 新增代码+ComputerUseMcpV2HostAdapter：确认已有状态类型正确；如果没有这一行，外部污染字段可能被错误当成可用状态。
        return state  # 新增代码+ComputerUseMcpV2HostAdapter：返回已有状态；如果没有这一行，每次调用都会重建状态。
    state = ComputerUseMcpSessionState()  # 新增代码+ComputerUseMcpV2HostAdapter：创建新的旧 session 状态容器；如果没有这一行，首次 v2 调用没有状态可用。
    setattr(agent, "_computer_use_mcp_session_state", state)  # 新增代码+ComputerUseMcpV2HostAdapter：把状态写回 agent 供后续复用；如果没有这一行，多轮工具无法共享授权和剪贴板。
    return state  # 新增代码+ComputerUseMcpV2HostAdapter：返回可用状态；如果没有这一行，调用方拿不到状态对象。
# 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，_computer_use_mcp_state 到此结束；如果没有这个边界说明，用户不容易看出旧 session 状态生命周期。


def _legacy_callbacks(agent: Any, controller: Any, emit_acceptance_event: Any) -> ComputerUseMcpSessionCallbacks:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，把 agent 主循环能力组装给旧 session adapter；如果没有这段函数，旧 adapter 无法拿到权限、门禁、trace 和截图回调。
    record_observation = lambda kind, payload: run_helpers_from_core.safe_record_observation(agent, kind, payload)  # 新增代码+ComputerUseMcpV2HostAdapter：创建安全 observation 回调；如果没有这一行，观察和动作证据不会写回 agent。
    record_runtime_trace = legacy_runtime_trace_recorder(agent, record_observation)  # 新增代码+ComputerUseMcpV2HostAdapter：创建旧成熟 trace 回调；如果没有这一行，controller 执行证据不会进入 runtime trace。
    record_image_artifacts = legacy_image_artifact_recorder(agent, record_observation)  # 新增代码+ComputerUseMcpV2HostAdapter：创建旧成熟截图 artifact 回调；如果没有这一行，observe/action 截图不会进入 active_artifacts。
    observe_before_action_rejection = lambda action_name, action_arguments: legacy_observe_before_action_rejection(action_name, action_arguments, getattr(agent, "desktop_task_context", {}), getattr(agent, "observation_events", []), record_observation)  # 新增代码+ComputerUseMcpV2HostAdapter：绑定旧“先观察再动作”硬门禁；如果没有这一行，v2 原子动作会绕开旧 full 模式保护。
    agent_owned_launch_rejection = lambda action_name, action_arguments: legacy_agent_owned_launch_rejection(action_name, action_arguments, getattr(agent, "desktop_task_context", {}), controller, record_observation)  # 新增代码+ComputerUseMcpV2HostAdapter：绑定旧“必须操作 agent 自己打开的窗口”门禁；如果没有这一行，v2 可能点到用户已有窗口。
    completion_signal_for_action = lambda action_name, action_arguments: legacy_completion_signal_for_action(action_name, action_arguments, getattr(agent, "desktop_task_context", {}), getattr(agent, "observation_events", []), record_observation)  # 新增代码+ComputerUseMcpV2HostAdapter：绑定旧完成收束门；如果没有这一行，v2 可能在任务已完成后继续鼠标键盘操作。
    return ComputerUseMcpSessionCallbacks(ask_permission=getattr(agent, "ask_permission", lambda _action: False), observe_before_action_rejection=observe_before_action_rejection, agent_owned_launch_rejection=agent_owned_launch_rejection, completion_signal_for_action=completion_signal_for_action, record_observation=record_observation, record_runtime_trace=record_runtime_trace, record_image_artifacts=record_image_artifacts, emit_acceptance_event=emit_acceptance_event)  # 新增代码+ComputerUseMcpV2HostAdapter：返回完整回调集合；如果没有这一行，旧 adapter 只能执行表面动作而缺少成熟 agent 约束。
# 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，_legacy_callbacks 到此结束；如果没有这个边界说明，用户不容易看出主循环能力注入范围。


@dataclass  # 新增代码+ComputerUseMcpV2HostAdapter：自动生成 adapter 初始化方法；如果没有这一行，下面的桥接类需要手写构造函数。
class ComputerUseMcpV2LegacyHostAdapter:  # 新增代码+ComputerUseMcpV2HostAdapter：类段开始，把 v2 原子方法转发到旧成熟 session adapter；如果没有这个类，v2 host 仍会直接错连 controller 或退回 no-op。
    session_adapter: ComputerUseMcpSessionAdapter  # 新增代码+ComputerUseMcpV2HostAdapter：保存旧成熟 session adapter；如果没有这一行，桥接方法无法执行旧 controller 链路。

    def _call(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，统一调用旧原子工具并标记来源；如果没有这段函数，每个鼠标键盘方法都要重复包装逻辑。
        legacy_result = self.session_adapter.call_atomic_tool(tool_name, dict(arguments or {}))  # 新增代码+ComputerUseMcpV2HostAdapter：调用旧 session adapter 的真实映射；如果没有这一行，left_click/type/observe 仍不会复用旧能力。
        return {"legacy_adapter_used": True, "backend": "computer_use_mcp_session_adapter", "legacy_tool_name": str(tool_name), "legacy_internal_tool": legacy_result.get("payload", {}).get("legacy_internal_tool", ""), "legacy_result": legacy_result, "ok": bool(legacy_result.get("ok", False))}  # 新增代码+ComputerUseMcpV2HostAdapter：返回带证据的桥接 payload；如果没有这一行，模型和测试无法确认到底是否走了旧成熟链路。
    # 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，_call 到此结束；如果没有这个边界说明，用户不容易看出旧 adapter 包装范围。

    def observe(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，把 v2 observe/screenshot 接到旧 observe；如果没有这段函数，观察会再次落到直接 controller 错配。
        return self._call("observe", arguments)  # 新增代码+ComputerUseMcpV2HostAdapter：执行旧观察链；如果没有这一行，observe 不能复用截图、窗口解析和 artifact 记录。
    # 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，observe 到此结束；如果没有这个边界说明，用户不容易看出观察桥接范围。

    def cursor_position(self) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，把光标读取接到旧 cursor_position；如果没有这段函数，v2 光标工具会绕开旧证据包装。
        return self._call("cursor_position", {})  # 新增代码+ComputerUseMcpV2HostAdapter：执行旧光标读取链；如果没有这一行，cursor_position 的来源无法被审计。
    # 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，cursor_position 到此结束；如果没有这个边界说明，用户不容易看出光标桥接范围。

    def mouse_move(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，把鼠标移动接到旧 action；如果没有这段函数，mouse_move 会退回 v2 no-op。
        return self._call("mouse_move", arguments)  # 新增代码+ComputerUseMcpV2HostAdapter：执行旧鼠标移动映射；如果没有这一行，真实低层移动链路不会被调用。
    # 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，mouse_move 到此结束；如果没有这个边界说明，用户不容易看出鼠标移动桥接范围。

    def left_click(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，把左键点击接到旧 action；如果没有这段函数，left_click 会继续走安全空壳。
        return self._call("left_click", arguments)  # 新增代码+ComputerUseMcpV2HostAdapter：执行旧左键点击映射；如果没有这一行，真实 click controller 后端不会被触发。
    # 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，left_click 到此结束；如果没有这个边界说明，用户不容易看出左键桥接范围。

    def double_click(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，把双击接到旧 action；如果没有这段函数，double_click 无法复用旧权限和 trace。
        return self._call("double_click", arguments)  # 新增代码+ComputerUseMcpV2HostAdapter：执行旧双击映射；如果没有这一行，真实双击不会进入 controller。
    # 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，double_click 到此结束；如果没有这个边界说明，用户不容易看出双击桥接范围。

    def right_click(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，把右键点击接到旧 action；如果没有这段函数，right_click 会退回 v2 no-op。
        return self._call("right_click", arguments)  # 新增代码+ComputerUseMcpV2HostAdapter：执行旧右键映射；如果没有这一行，旧 click+right 转换不会发生。
    # 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，right_click 到此结束；如果没有这个边界说明，用户不容易看出右键桥接范围。

    def type(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，把文本输入接到旧 type_text；如果没有这段函数，v2 type 只会返回长度不真正输入。
        return self._call("type", arguments)  # 新增代码+ComputerUseMcpV2HostAdapter：执行旧文本输入映射；如果没有这一行，键盘输入能力不会复用旧 controller。
    # 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，type 到此结束；如果没有这个边界说明，用户不容易看出文本输入桥接范围。

    def key(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，把按键接到旧 press_key；如果没有这段函数，v2 key 只会返回摘要。
        return self._call("key", arguments)  # 新增代码+ComputerUseMcpV2HostAdapter：执行旧按键映射；如果没有这一行，组合键不会进入真实键盘链。
    # 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，key 到此结束；如果没有这个边界说明，用户不容易看出按键桥接范围。

    def scroll(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，把滚动接到旧 action；如果没有这段函数，scroll 会退回 v2 空壳。
        return self._call("scroll", arguments)  # 新增代码+ComputerUseMcpV2HostAdapter：执行旧滚动映射；如果没有这一行，真实滚轮链路不会被调用。
    # 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，scroll 到此结束；如果没有这个边界说明，用户不容易看出滚动桥接范围。

    def zoom(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，把 zoom 接到旧 session adapter；如果没有这段函数，agent-side zoom 会停在 v2 host 缺方法失败。
        return self._call("zoom", arguments)  # 新增代码+ClaudeCodeParity：执行旧 zoom 映射；如果没有这一行，局部放大观察无法复用成熟 session adapter。
    # 新增代码+ClaudeCodeParity：函数段结束，zoom 到此结束；如果没有这个边界说明，用户不容易看出 zoom 桥接范围。

    def hold_key(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，把 hold_key 接到旧 session adapter；如果没有这段函数，按住键工具会在 agent-side 缺桥接。
        return self._call("hold_key", arguments)  # 新增代码+ClaudeCodeParity：执行旧 hold_key 映射；如果没有这一行，长按键动作不会进入 session adapter。
    # 新增代码+ClaudeCodeParity：函数段结束，hold_key 到此结束；如果没有这个边界说明，用户不容易看出 hold_key 桥接范围。

    def left_click_drag(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，把 left_click_drag 接到旧 session adapter；如果没有这段函数，拖拽工具会在 agent-side 缺桥接。
        return self._call("left_click_drag", arguments)  # 新增代码+ClaudeCodeParity：执行旧 left_click_drag 映射；如果没有这一行，拖拽动作不会进入 session adapter。
    # 新增代码+ClaudeCodeParity：函数段结束，left_click_drag 到此结束；如果没有这个边界说明，用户不容易看出拖拽桥接范围。

    def middle_click(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，把 middle_click 接到旧 session adapter；如果没有这段函数，中键点击会在 agent-side 缺桥接。
        return self._call("middle_click", arguments)  # 新增代码+ClaudeCodeParity：执行旧 middle_click 映射；如果没有这一行，中键动作不会进入 session adapter。
    # 新增代码+ClaudeCodeParity：函数段结束，middle_click 到此结束；如果没有这个边界说明，用户不容易看出中键桥接范围。

    def triple_click(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，把 triple_click 接到旧 session adapter；如果没有这段函数，三击工具会在 agent-side 缺桥接。
        return self._call("triple_click", arguments)  # 新增代码+ClaudeCodeParity：执行旧 triple_click 映射；如果没有这一行，三击动作不会进入 session adapter。
    # 新增代码+ClaudeCodeParity：函数段结束，triple_click 到此结束；如果没有这个边界说明，用户不容易看出三击桥接范围。

    def left_mouse_down(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，把 left_mouse_down 接到旧 session adapter；如果没有这段函数，左键按下会在 agent-side 缺桥接。
        return self._call("left_mouse_down", arguments)  # 新增代码+ClaudeCodeParity：执行旧 left_mouse_down 映射；如果没有这一行，按下动作不会进入 session adapter。
    # 新增代码+ClaudeCodeParity：函数段结束，left_mouse_down 到此结束；如果没有这个边界说明，用户不容易看出按下桥接范围。

    def left_mouse_up(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，把 left_mouse_up 接到旧 session adapter；如果没有这段函数，左键释放会在 agent-side 缺桥接。
        return self._call("left_mouse_up", arguments)  # 新增代码+ClaudeCodeParity：执行旧 left_mouse_up 映射；如果没有这一行，释放动作不会进入 session adapter。
    # 新增代码+ClaudeCodeParity：函数段结束，left_mouse_up 到此结束；如果没有这个边界说明，用户不容易看出释放桥接范围。

    def open_application(self, _app_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，把应用启动接到旧 launch_app；如果没有这段函数，open_application 会绕开旧窗口绑定。
        return self._call("open_application", arguments)  # 新增代码+ComputerUseMcpV2HostAdapter：执行旧应用启动映射；如果没有这一行，agent-owned 目标窗口不会被 controller 记录。
    # 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，open_application 到此结束；如果没有这个边界说明，用户不容易看出应用启动桥接范围。
# 新增代码+ComputerUseMcpV2HostAdapter：类段结束，ComputerUseMcpV2LegacyHostAdapter 到此结束；如果没有这个边界说明，用户不容易看出 v2 host adapter 的全部方法。


def build_legacy_host_adapter(agent: Any, emit_acceptance_event: Any) -> ComputerUseMcpV2LegacyHostAdapter | None:  # 新增代码+ComputerUseMcpV2HostAdapter：函数段开始，为 v2 context 构造旧成熟 host adapter；如果没有这段函数，bind_session_context 只能把 controller 直接塞给 v2 导致接口错配。
    controller = getattr(agent, "computer_use_controller", None)  # 新增代码+ComputerUseMcpV2HostAdapter：读取 agent 上的旧 Computer Use controller；如果没有这一行，桥接层没有真实桌面后端。
    if controller is None:  # 新增代码+ComputerUseMcpV2HostAdapter：检查 controller 是否存在；如果没有这一行，缺后端时会在更深处报 AttributeError。
        return None  # 新增代码+ComputerUseMcpV2HostAdapter：没有 controller 时返回 None 让 v2 保持独立 no-op/错误路径；如果没有这一行，普通 stdio selftest 会崩溃。
    callbacks = _legacy_callbacks(agent, controller, emit_acceptance_event)  # 新增代码+ComputerUseMcpV2HostAdapter：组装旧 adapter 所需回调；如果没有这一行，旧执行链拿不到主循环权限和证据记录能力。
    session_adapter = ComputerUseMcpSessionAdapter(controller=controller, callbacks=callbacks, state=_computer_use_mcp_state(agent))  # 新增代码+ComputerUseMcpV2HostAdapter：创建旧成熟 session adapter；如果没有这一行，原子工具名无法映射到旧 status/observe/action 能力。
    return ComputerUseMcpV2LegacyHostAdapter(session_adapter=session_adapter)  # 新增代码+ComputerUseMcpV2HostAdapter：返回 v2 可调用 host adapter；如果没有这一行，bind_session_context 拿不到可复用旧能力的 host。
# 新增代码+ComputerUseMcpV2HostAdapter：函数段结束，build_legacy_host_adapter 到此结束；如果没有这个边界说明，用户不容易看出旧能力只在 v2 内部绑定。
