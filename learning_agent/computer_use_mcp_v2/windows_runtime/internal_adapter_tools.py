"""Computer Use v2 内部 adapter facade。"""  # 新增代码+ComputerUseMcpV2InternalAdapterFence：说明本文件只把旧成熟能力改名为内部能力；如果没有这行代码，读者容易误以为这些旧函数仍是模型可见工具。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2InternalAdapterFence：延迟解析类型注解，避免运行时导入顺序影响；如果没有这行代码，复杂回调类型可能提前求值。

from typing import Any, Callable  # 新增代码+ComputerUseMcpV2InternalAdapterFence：导入动态参数和回调类型；如果没有这行代码，内部 facade 的边界不清楚。

from . import agent_tools as _legacy_agent_tools  # 新增代码+ComputerUseMcpV2InternalAdapterFence：只在 facade 内部导入旧成熟实现；如果没有这行代码，v2 adapter 就无法复用已验证的状态、观察、发现、执行能力。


RecordObservation = Callable[[str, dict[str, Any]], None]  # 新增代码+ComputerUseMcpV2InternalAdapterFence：定义 observation 回调签名；如果没有这行代码，内部状态/观察能力如何写回 agent 不清楚。
RecordRuntimeTrace = Callable[[str, dict[str, Any]], None]  # 新增代码+ComputerUseMcpV2InternalAdapterFence：定义 runtime trace 回调签名；如果没有这行代码，内部执行证据链的注入点不清楚。
RecordImageArtifacts = Callable[[dict[str, Any], str], None]  # 新增代码+ComputerUseMcpV2InternalAdapterFence：定义截图 artifact 回调签名；如果没有这行代码，内部观察图片如何登记不清楚。
AskPermission = Callable[[str], bool]  # 新增代码+ComputerUseMcpV2InternalAdapterFence：定义权限确认回调签名；如果没有这行代码，内部高风险动作权限边界不清楚。
ActionGate = Callable[[str, dict[str, Any]], str | None]  # 新增代码+ComputerUseMcpV2InternalAdapterFence：定义动作门禁回调签名；如果没有这行代码，内部执行如何复用旧安全门禁不清楚。
AcceptanceEmitter = Callable[[str, dict[str, Any]], None]  # 新增代码+ComputerUseMcpV2InternalAdapterFence：定义验收事件回调签名；如果没有这行代码，真实终端验收事件出口不清楚。


def internal_request_access(arguments: dict[str, Any], record_observation: RecordObservation, record_runtime_trace: RecordRuntimeTrace) -> str:  # 新增代码+ComputerUseMcpV2InternalAdapterFence：函数段开始，用内部名称复用旧授权申请能力；如果没有这段函数，session adapter 只能继续直接引用公开感很强的 request_access 名称。
    return _legacy_agent_tools.request_access(arguments, record_observation, record_runtime_trace)  # 新增代码+ComputerUseMcpV2InternalAdapterFence：委托旧成熟授权实现；如果没有这行代码，v2 request_access 会失去已有的观察记录和 trace 逻辑。
# 新增代码+ComputerUseMcpV2InternalAdapterFence：函数段结束，internal_request_access 到此结束；如果没有这个边界说明，用户不容易看出授权内部 facade 范围。


def internal_status_snapshot(arguments: dict[str, Any], controller: Any, record_observation: RecordObservation, record_runtime_trace: RecordRuntimeTrace) -> str:  # 新增代码+ComputerUseMcpV2InternalAdapterFence：函数段开始，用内部名称复用旧状态读取能力；如果没有这段函数，旧 computer_status 名称会继续出现在接线层。
    return _legacy_agent_tools.computer_status(arguments, controller, record_observation, record_runtime_trace)  # 新增代码+ComputerUseMcpV2InternalAdapterFence：委托旧成熟状态实现；如果没有这行代码，v2 内部状态快照会丢掉 controller 状态和审计记录。
# 新增代码+ComputerUseMcpV2InternalAdapterFence：函数段结束，internal_status_snapshot 到此结束；如果没有这个边界说明，用户不容易看出状态内部 facade 范围。


def internal_discover_applications(arguments: dict[str, Any], record_observation: RecordObservation, record_runtime_trace: RecordRuntimeTrace) -> str:  # 新增代码+ComputerUseMcpV2InternalAdapterFence：函数段开始，用内部名称复用旧应用发现能力；如果没有这段函数，旧 computer_discover 名称会继续出现在接线层。
    return _legacy_agent_tools.computer_discover(arguments, record_observation, record_runtime_trace)  # 新增代码+ComputerUseMcpV2InternalAdapterFence：委托旧成熟发现实现；如果没有这行代码，v2 授权/打开应用链路会丢掉 Windows 应用清单能力。
# 新增代码+ComputerUseMcpV2InternalAdapterFence：函数段结束，internal_discover_applications 到此结束；如果没有这个边界说明，用户不容易看出发现内部 facade 范围。


def internal_observe_desktop(arguments: dict[str, Any], controller: Any, record_observation: RecordObservation, record_runtime_trace: RecordRuntimeTrace, record_image_artifacts: RecordImageArtifacts) -> str:  # 新增代码+ComputerUseMcpV2InternalAdapterFence：函数段开始，用内部名称复用旧观察截图能力；如果没有这段函数，旧 computer_observe 名称会继续出现在接线层。
    return _legacy_agent_tools.computer_observe(arguments, controller, record_observation, record_runtime_trace, record_image_artifacts)  # 新增代码+ComputerUseMcpV2InternalAdapterFence：委托旧成熟观察实现；如果没有这行代码，v2 observe/screenshot 会失去窗口解析、截图和 artifact 记录。
# 新增代码+ComputerUseMcpV2InternalAdapterFence：函数段结束，internal_observe_desktop 到此结束；如果没有这个边界说明，用户不容易看出观察内部 facade 范围。


def internal_execute_desktop_action(arguments: dict[str, Any], controller: Any, ask_permission: AskPermission, observe_before_action_rejection: ActionGate, agent_owned_launch_rejection: ActionGate, completion_signal_for_action: ActionGate, record_observation: RecordObservation, record_runtime_trace: RecordRuntimeTrace, record_image_artifacts: RecordImageArtifacts, emit_acceptance_event: AcceptanceEmitter) -> str:  # 新增代码+ComputerUseMcpV2InternalAdapterFence：函数段开始，用内部名称复用旧桌面执行能力；如果没有这段函数，旧 computer_action 名称会继续出现在接线层并造成公开接口误判。
    return _legacy_agent_tools.computer_action(arguments, controller, ask_permission, observe_before_action_rejection, agent_owned_launch_rejection, completion_signal_for_action, record_observation, record_runtime_trace, record_image_artifacts, emit_acceptance_event)  # 新增代码+ComputerUseMcpV2InternalAdapterFence：委托旧成熟动作实现；如果没有这行代码，v2 原子动作会丢掉权限、门禁、trace、截图和验收事件。
# 新增代码+ComputerUseMcpV2InternalAdapterFence：函数段结束，internal_execute_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出执行内部 facade 范围。
