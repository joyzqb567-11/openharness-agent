"""Computer Use 的 agent 工具入口适配层。"""  # 新增代码+AgentPySplitPhase6: 说明本文件承接 agent.py 中的 Computer Use 工具入口；如果没有这行代码，代码小白不知道这个模块为什么存在。

from __future__ import annotations  # 新增代码+AgentPySplitPhase6: 允许类型注解延迟解析；如果没有这行代码，回调类型在旧运行方式下更容易受定义顺序影响。

import json  # 新增代码+AgentPySplitPhase6: 用来把状态、发现、mode 和权限参数转成模型可读 JSON；如果没有这行代码，工具返回会缺少稳定结构化文本。
from typing import Any, Callable  # 新增代码+AgentPySplitPhase6: 导入通用数据类型和回调类型；如果没有这行代码，新模块接口不容易看出依赖边界。

from .action_policy import redact_action_arguments  # 新增代码+AgentPySplitPhase6: 复用 Computer Use 动作参数脱敏规则；如果没有这行代码，权限提示可能泄露 type_text 等敏感文本。
from .tool_surface import normalize_computer_use_compat_arguments  # 新增代码+AgentPySplitPhase6: 复用兼容工具参数归一化；如果没有这行代码，computer_use 统一入口会重新写一套分发逻辑。
from .universal_mode import UniversalWindowsComputerUseRuntime  # 新增代码+AgentPySplitPhase6: 保留旧 mode 兼容入口的通用运行时；如果没有这行代码，operation=mode 的历史兼容测试会断开。
from .windows_app_inventory import query_windows_app_inventory  # 新增代码+AgentPySplitPhase6: 复用统一 Windows 应用清单查询；如果没有这行代码，computer_discover 会绕开当前 inventory 主入口。
from .request_access_tool import request_computer_use_access  # 新增代码+RequestAccessToolSurface: 导入只读授权申请实现；如果没有这一行，agent 工具适配层无法把 request_access 路由到真实函数。
from .session_context import deny_action_without_request_access  # 新增代码+Phase2SessionGrants：导入 request_access 动作前授权门禁；如果没有这一行，computer_action 无法在触碰桌面前拒绝未授权目标。
from learning_agent.core.actionability_state import DESKTOP_ACTION_REQUIRED_MARKER, DESKTOP_OBSERVATION_BLOCKED_MARKER  # 新增代码+ObservePlanActVerify：导入桌面动作 marker；如果没有这一行，launch/observe 结果无法驱动下一步动作控制。


RecordObservation = Callable[[str, dict[str, Any]], None]  # 新增代码+AgentPySplitPhase6: 定义观察记录回调类型；如果没有这行代码，本模块会被迫直接依赖 LearningAgent。
RecordRuntimeTrace = Callable[[str, dict[str, Any]], None]  # 新增代码+AgentPySplitPhase6: 定义 runtime trace 回调类型；如果没有这行代码，工具内部证据记录会和 agent 主类耦合。
RecordImageArtifacts = Callable[[dict[str, Any], str], None]  # 新增代码+AgentPySplitPhase6: 定义截图 artifact 登记回调类型；如果没有这行代码，observe/action 结果里的截图不会回到 agent 活跃产物列表。
AskPermission = Callable[[str], bool]  # 新增代码+AgentPySplitPhase6: 定义权限确认回调类型；如果没有这行代码，真实桌面动作可能绕过用户确认边界。
ActionGate = Callable[[str, dict[str, Any]], str | None]  # 新增代码+AgentPySplitPhase6: 定义动作门禁回调类型；如果没有这行代码，观察门、启动门、完成门会和本模块硬绑定。
ComputerToolHandler = Callable[[dict[str, Any]], str]  # 新增代码+AgentPySplitPhase6: 定义兼容工具分发处理器类型；如果没有这行代码，compat 入口依赖关系不清晰。
AcceptanceEmitter = Callable[[str, dict[str, Any]], None]  # 新增代码+AgentPySplitPhase6: 定义验收事件写入回调类型；如果没有这行代码，本模块会直接绑定观测层实现。
UniversalRuntimeFactory = Callable[[], Any]  # 新增代码+AgentPySplitPhase6: 定义 mode runtime 工厂类型；如果没有这行代码，测试或后续替换 runtime 不方便。


# 新增代码+ObservePlanActVerify：函数段开始，把布尔值转换成稳定的小写协议文本；如果没有这段函数，验收器需要兼容 True/False/true/false 多种写法。
def _desktop_bool_text(value: Any) -> str:  # 新增代码+ObservePlanActVerify：定义桌面 actionability 布尔格式化入口；如果没有这一行，输出协议中的布尔字段不稳定。
    return "true" if bool(value) else "false"  # 新增代码+ObservePlanActVerify：返回小写布尔 token；如果没有这一行，debug_log_contains 断言更脆弱。
# 新增代码+ObservePlanActVerify：函数段结束，_desktop_bool_text 到此结束；如果没有这个边界说明，用户不容易看出它只做格式化。


# 新增代码+ObservePlanActVerify：函数段开始，从动作或观察结果里提取目标窗口引用；如果没有这段函数，target_ref 可能藏在 session/target_window 中被漏掉。
def _desktop_target_ref_from_data(data: dict[str, Any], arguments: dict[str, Any] | None = None) -> str:  # 新增代码+ObservePlanActVerify：定义 target_ref 抽取入口；如果没有这一行，launch 到 observe/action 的窗口绑定容易断。
    safe_arguments = arguments if isinstance(arguments, dict) else {}  # 新增代码+ObservePlanActVerify：把可选参数归一成字典；如果没有这一行，None 参数会导致 get 调用失败。
    session = data.get("session") if isinstance(data.get("session"), dict) else {}  # 新增代码+ObservePlanActVerify：读取嵌套 session 证据；如果没有这一行，controller 嵌套返回的 target_ref 会漏掉。
    target_window = data.get("target_window") if isinstance(data.get("target_window"), dict) else {}  # 新增代码+ObservePlanActVerify：读取顶层目标窗口；如果没有这一行，窗口对象里的 ref 无法被使用。
    if not target_window:  # 新增代码+ObservePlanActVerify：顶层没有窗口时尝试 session；如果没有这一行，嵌套窗口证据不会进入提取逻辑。
        target_window = session.get("target_window") if isinstance(session.get("target_window"), dict) else {}  # 新增代码+ObservePlanActVerify：读取 session 中的目标窗口；如果没有这一行，launch resolver 生成的窗口 ref 会丢失。
    return str(data.get("target_ref") or safe_arguments.get("target_ref") or session.get("target_ref") or target_window.get("target_ref") or target_window.get("ref") or target_window.get("window_ref") or "").strip()  # 新增代码+ObservePlanActVerify：按多个可信字段顺序返回目标引用；如果没有这一行，下一步 observe/action 可能不知道绑定哪个窗口。
# 新增代码+ObservePlanActVerify：函数段结束，_desktop_target_ref_from_data 到此结束；如果没有这个边界说明，用户不容易看出目标引用来源。


# 新增代码+ObservePlanActVerify：函数段开始，判断桌面观察结果是否有可继续动作的视觉或 UIA 线索；如果没有这段函数，观察成功和观察空白无法区分。
def _desktop_observation_has_action_candidate(data: dict[str, Any]) -> bool:  # 新增代码+ObservePlanActVerify：定义观察候选判断入口；如果没有这一行，网易云搜索框/按钮等线索无法驱动下一步动作。
    state = data.get("state") if isinstance(data.get("state"), dict) else {}  # 新增代码+ObservePlanActVerify：读取窗口状态子对象；如果没有这一行，get_window_state 返回结构无法分析。
    image_result_count = int(data.get("image_result_count", 0) or 0)  # 新增代码+ObservePlanActVerify：读取截图 artifact 数量；如果没有这一行，截图存在性无法作为可观察证据。
    screenshot_captured = bool(state.get("screenshot_captured") or data.get("screenshot_captured") or image_result_count > 0)  # 新增代码+ObservePlanActVerify：汇总截图证据；如果没有这一行，真实可见窗口截图不会触发继续动作。
    accessibility_excerpt = str(state.get("accessibility_excerpt") or data.get("accessibility_excerpt") or "").strip()  # 新增代码+ObservePlanActVerify：读取 UIA/可访问性摘要；如果没有这一行，搜索框等控件文字线索会被漏掉。
    controls = state.get("controls") if isinstance(state.get("controls"), list) else []  # 新增代码+ObservePlanActVerify：读取控件列表；如果没有这一行，结构化控件候选无法判断。
    return bool(screenshot_captured or accessibility_excerpt or controls)  # 新增代码+ObservePlanActVerify：任一视觉或 UIA 证据存在就允许继续动作；如果没有这一行，observe 后可能被误判为失败。
# 新增代码+ObservePlanActVerify：函数段结束，_desktop_observation_has_action_candidate 到此结束；如果没有这个边界说明，用户不容易看出可继续条件。


# 新增代码+ObservePlanActVerify：函数段开始，从 launch_app 动作结果生成下一步 observe 要求；如果没有这段函数，打开网易云等应用后模型可能不观察窗口直接 fallback。
def build_desktop_actionability_summary_from_action_result(action_name: str, result_data: Any) -> str:  # 新增代码+ObservePlanActVerify：定义桌面动作结果摘要入口；如果没有这一行，测试和工具返回无法复用同一协议。
    if str(action_name or "").strip() != "launch_app":  # 新增代码+ObservePlanActVerify：目前只在启动应用后强制观察；如果没有这一行，普通点击/输入动作会被错误要求 get_window_state。
        return ""  # 新增代码+ObservePlanActVerify：非 launch_app 返回空摘要；如果没有这一行，调用方无法区分不适用场景。
    data = result_data if isinstance(result_data, dict) else {}  # 新增代码+ObservePlanActVerify：只从字典结果抽取字段；如果没有这一行，异常 data 会导致 get 调用失败。
    target_ref = _desktop_target_ref_from_data(data)  # 新增代码+ObservePlanActVerify：抽取目标窗口引用；如果没有这一行，下一步 observe 缺少 target_ref。
    session = data.get("session") if isinstance(data.get("session"), dict) else {}  # 新增代码+ObservePlanActVerify：读取嵌套 session；如果没有这一行，绑定字段可能漏掉。
    target_window = data.get("target_window") if isinstance(data.get("target_window"), dict) else session.get("target_window") if isinstance(session.get("target_window"), dict) else {}  # 新增代码+ObservePlanActVerify：读取目标窗口对象；如果没有这一行，窗口绑定状态无法判断。
    if not target_ref and not target_window:  # 新增代码+ObservePlanActVerify：没有可绑定窗口时不创建动作要求；如果没有这一行，启动失败也会要求 observe。
        return ""  # 新增代码+ObservePlanActVerify：返回空摘要；如果没有这一行，模型会对不存在窗口执行观察。
    external_bound = bool(data.get("external_app_window_bound") or session.get("external_app_window_bound") or target_window)  # 新增代码+ObservePlanActVerify：判断是否绑定真实外部窗口；如果没有这一行，验收无法证明不是内存模拟。
    proxy_bound = bool(data.get("proxy_window_bound") or session.get("proxy_window_bound") or target_ref)  # 新增代码+ObservePlanActVerify：判断是否已有可复用代理引用；如果没有这一行，后续 target_ref 绑定证据不完整。
    fresh_target_decision = str(data.get("fresh_target_decision") or session.get("fresh_target_decision") or "").strip()  # 新增代码+FreshTargetActionability：抽取新目标策略决策；如果没有这一行，模型不知道 launch_app 是否走了旧窗口保护。
    fresh_target_class = str(data.get("fresh_target_class") or session.get("fresh_target_class") or "").strip()  # 新增代码+FreshTargetActionability：抽取新目标分类；如果没有这一行，验收无法区分新窗口和授权旧窗口。
    target_window_existed_before_launch = bool(data.get("target_window_existed_before_launch") or session.get("target_window_existed_before_launch"))  # 新增代码+FreshTargetActionability：记录目标窗口启动前是否已存在；如果没有这一行，旧窗口默认接管风险不可见。
    old_window_default_takeover = bool(data.get("old_window_default_takeover") or session.get("old_window_default_takeover"))  # 新增代码+FreshTargetActionability：记录是否发生旧窗口默认接管；如果没有这一行，压力测试无法断言 false。
    target_lease = data.get("target_lease") if isinstance(data.get("target_lease"), dict) else session.get("target_lease") if isinstance(session.get("target_lease"), dict) else {}  # 新增代码+FreshTargetActionability：读取 target_ref 对应租约；如果没有这一行，一对一绑定只能靠窗口对象猜。
    target_ref_one_to_one = bool(target_ref and target_lease)  # 新增代码+FreshTargetActionability：用 target_ref 加租约证明一对一绑定；如果没有这一行，多窗口任务缺少稳定验证 token。
    return "\n".join([  # 新增代码+ObservePlanActVerify：拼接桌面动作协议；如果没有这一行，工具输出不会被 actionability_state 解析。
        DESKTOP_ACTION_REQUIRED_MARKER,  # 新增代码+ObservePlanActVerify：声明桌面下一步必须真实观察/动作；如果没有这一行，收束器不会创建 pending。
        "actionability_kind=desktop_bound_window_observe",  # 新增代码+ObservePlanActVerify：声明启动后绑定窗口需要观察；如果没有这一行，阶段不可审计。
        "next_required_tool=mcp__computer-use__observe",  # 修改代码+ComputerUseMcpV2ResidualCleanup：要求下一步调用 v2 MCP observe；如果没有这一行，模型会被旧 computer_observe 名字带回隐藏接口。
        "next_required_action=get_window_state",  # 新增代码+ObservePlanActVerify：要求 observe 的具体动作；如果没有这一行，模型不知道参数 action 应该填什么。
        "next_required_reason=launch_app_window_bound",  # 新增代码+ObservePlanActVerify：输出低敏原因码；如果没有这一行，纠偏提示缺少解释。
        f"target_ref={target_ref}",  # 新增代码+ObservePlanActVerify：输出绑定窗口引用；如果没有这一行，下一步 observe 无法锁定窗口。
        f"external_app_window_bound={_desktop_bool_text(external_bound)}",  # 新增代码+ObservePlanActVerify：输出真实窗口绑定证据；如果没有这一行，验收无法区分真实桌面和模拟。
        f"proxy_window_bound={_desktop_bool_text(proxy_bound)}",  # 新增代码+ObservePlanActVerify：输出代理绑定证据；如果没有这一行，后续窗口操作链路不可审计。
        f"fresh_target_decision={fresh_target_decision}",  # 新增代码+FreshTargetActionability：输出 FreshTarget 决策；如果没有这一行，模型无法把旧窗口拒绝和正常启动区分开。
        f"fresh_target_class={fresh_target_class}",  # 新增代码+FreshTargetActionability：输出 FreshTarget 分类；如果没有这一行，验收器无法确认是否 fresh 或 user-granted。
        f"target_window_existed_before_launch={_desktop_bool_text(target_window_existed_before_launch)}",  # 新增代码+FreshTargetActionability：输出旧窗口事实；如果没有这一行，旧窗口复用无法被审计。
        f"target_ref_one_to_one={_desktop_bool_text(target_ref_one_to_one)}",  # 新增代码+FreshTargetActionability：输出一对一租约事实；如果没有这一行，复杂多应用任务无法被稳定验证。
        f"old_window_default_takeover={_desktop_bool_text(old_window_default_takeover)}",  # 新增代码+FreshTargetActionability：输出是否默认接管旧窗口；如果没有这一行，压力测试无法证明没有悄悄操作旧软件。
    ])  # 新增代码+ObservePlanActVerify：协议拼接结束；如果没有这一行，Python 语法不完整。
# 新增代码+ObservePlanActVerify：函数段结束，build_desktop_actionability_summary_from_action_result 到此结束；如果没有这个边界说明，用户不容易看出 launch_app 后续规则。


# 新增代码+ObservePlanActVerify：函数段开始，从 get_window_state 结果生成继续动作或阻塞摘要；如果没有这段函数，观察后不知道该继续控制还是明确失败。
def build_desktop_observation_actionability_summary(action_name: str, result_data: Any, arguments: dict[str, Any] | None = None) -> str:  # 新增代码+ObservePlanActVerify：定义桌面观察摘要入口；如果没有这一行，observe 工具和测试无法共用规则。
    if str(action_name or "").strip() != "get_window_state":  # 新增代码+ObservePlanActVerify：只有窗口状态观察需要生成下一步动作；如果没有这一行，list_windows/list_apps 会被误判。
        return ""  # 新增代码+ObservePlanActVerify：不适用时返回空摘要；如果没有这一行，调用方无法跳过普通观察。
    data = result_data if isinstance(result_data, dict) else {}  # 新增代码+ObservePlanActVerify：只从字典 data 抽取；如果没有这一行，异常结果会让摘要构造失败。
    state = data.get("state") if isinstance(data.get("state"), dict) else {}  # 新增代码+ObservePlanActVerify：读取窗口状态；如果没有这一行，截图/UIA 字段无法读取。
    target_ref = _desktop_target_ref_from_data(data, arguments)  # 新增代码+ObservePlanActVerify：抽取目标引用；如果没有这一行，下一步动作可能丢失窗口绑定。
    image_result_count = int(data.get("image_result_count", 0) or 0)  # 新增代码+ObservePlanActVerify：读取截图 artifact 数量；如果没有这一行，截图证据无法输出。
    screenshot_captured = bool(state.get("screenshot_captured") or data.get("screenshot_captured") or image_result_count > 0)  # 新增代码+ObservePlanActVerify：汇总截图是否存在；如果没有这一行，观察质量无法被验收。
    uia_tree_observation = bool(state.get("accessibility_excerpt") or state.get("controls") or data.get("accessibility_excerpt"))  # 新增代码+ObservePlanActVerify：汇总 UIA/控件树是否存在；如果没有这一行，搜索框等结构线索无法验收。
    if _desktop_observation_has_action_candidate(data):  # 新增代码+ObservePlanActVerify：有截图或 UIA 线索时要求继续真实动作；如果没有这一行，网易云搜索和播放链路会停在 observe。
        return "\n".join([  # 新增代码+ObservePlanActVerify：拼接可继续动作协议；如果没有这一行，收束器不会创建 computer_action pending。
            DESKTOP_ACTION_REQUIRED_MARKER,  # 新增代码+ObservePlanActVerify：声明桌面下一步必须动作；如果没有这一行，模型可能转写本地替代结果。
            "actionability_kind=desktop_bound_window_operable",  # 新增代码+ObservePlanActVerify：声明已观察到可操作窗口；如果没有这一行，阶段不可审计。
            "next_required_tool=mcp__computer-use__computer_batch",  # 修改代码+ComputerUseMcpV2ResidualCleanup：默认建议用 v2 batch 承载下一步原子动作；如果没有这一行，模型会继续看到旧 computer_action。
            "next_allowed_tools=mcp__computer-use__left_click,mcp__computer-use__double_click,mcp__computer-use__right_click,mcp__computer-use__type,mcp__computer-use__key,mcp__computer-use__scroll,mcp__computer-use__computer_batch",  # 修改代码+ComputerUseMcpV2ResidualCleanup：允许模型选择真实需要的 v2 原子动作；如果没有这一行，pending gate 会误挡 click/type/key 等正确工具。
            "next_required_reason=desktop_window_observed_with_candidates",  # 新增代码+ObservePlanActVerify：输出低敏原因码；如果没有这一行，纠偏提示缺少解释。
            f"target_ref={target_ref}",  # 新增代码+ObservePlanActVerify：输出窗口引用；如果没有这一行，下一步动作可能漂移到旧窗口。
            f"screenshot_captured={_desktop_bool_text(screenshot_captured)}",  # 新增代码+ObservePlanActVerify：输出截图证据；如果没有这一行，验收看不到视觉观察是否发生。
            f"uia_tree_observation={_desktop_bool_text(uia_tree_observation)}",  # 新增代码+ObservePlanActVerify：输出 UIA 证据；如果没有这一行，验收看不到结构化观察是否发生。
        ])  # 新增代码+ObservePlanActVerify：可继续协议拼接结束；如果没有这一行，Python 语法不完整。
    return "\n".join([  # 新增代码+ObservePlanActVerify：拼接阻塞协议；如果没有这一行，观察失败不会有稳定分类。
        DESKTOP_OBSERVATION_BLOCKED_MARKER,  # 新增代码+ObservePlanActVerify：声明桌面观察阻塞；如果没有这一行，收束器无法区分工具失败和外部限制。
        "block_class=tool_observation_failure",  # 新增代码+ObservePlanActVerify：输出阻塞分类；如果没有这一行，验收无法识别工具观察失败。
        "block_reason=missing_screenshot_and_uia",  # 新增代码+ObservePlanActVerify：输出低敏阻塞原因；如果没有这一行，失败报告不可诊断。
        f"target_ref={target_ref}",  # 新增代码+ObservePlanActVerify：保留目标引用；如果没有这一行，用户不知道哪个窗口观察失败。
        f"screenshot_captured={_desktop_bool_text(screenshot_captured)}",  # 新增代码+ObservePlanActVerify：输出截图缺失状态；如果没有这一行，无法判断是否视觉通道失败。
        f"uia_tree_observation={_desktop_bool_text(uia_tree_observation)}",  # 新增代码+ObservePlanActVerify：输出 UIA 缺失状态；如果没有这一行，无法判断是否结构通道失败。
    ])  # 新增代码+ObservePlanActVerify：阻塞协议拼接结束；如果没有这一行，Python 语法不完整。
# 新增代码+ObservePlanActVerify：函数段结束，build_desktop_observation_actionability_summary 到此结束；如果没有这个边界说明，用户不容易看出 observe 后续规则。


# 新增代码+AgentPySplitPhase6: 函数段开始，computer_status 实现 Computer Use 状态工具；如果没有这段函数，agent.py 无法把 _computer_status 逻辑迁到 Computer Use 模块。
def computer_status(arguments: dict[str, Any], controller: Any, record_observation: RecordObservation, record_runtime_trace: RecordRuntimeTrace) -> str:  # 新增代码+AgentPySplitPhase6: 定义状态工具适配入口；如果没有这行代码，agent.py 的薄包装没有可委托对象。
    del arguments  # 新增代码+AgentPySplitPhase6: status 当前不需要参数但保留统一工具签名；如果没有这行代码，读者可能误以为参数遗漏处理。
    status = controller.status()  # 新增代码+AgentPySplitPhase6: 从 Computer Use controller 读取当前桌面后端状态；如果没有这行代码，状态工具无法反映后端是否可用。
    record_observation("computer_use_status", status)  # 新增代码+AgentPySplitPhase6: 把状态查询写入观察流；如果没有这行代码，真实终端排查不知道模型是否检查过桌面能力。
    record_runtime_trace("computer_status", {"ok": bool(status.get("ok", False)), "backend": status.get("backend", ""), "real_desktop_touched": bool(status.get("real_desktop_touched", False))})  # 新增代码+AgentPySplitPhase6: 记录状态工具内部摘要；如果没有这行代码，runtime trace 无法证明状态入口实际执行。
    return json.dumps(status, ensure_ascii=False, indent=2)  # 新增代码+AgentPySplitPhase6: 返回中文友好的 JSON 文本；如果没有这行代码，模型和用户难以读取结构化状态。
# 新增代码+AgentPySplitPhase6: 函数段结束，computer_status 到此结束；如果没有这个边界说明，用户不容易看出状态工具范围。


# 新增代码+AgentPySplitPhase6: 函数段开始，computer_observe 实现 Computer Use 只读观察工具；如果没有这段函数，模型无法在动作前读取窗口和截图。
def computer_observe(arguments: dict[str, Any], controller: Any, record_observation: RecordObservation, record_runtime_trace: RecordRuntimeTrace, record_image_artifacts: RecordImageArtifacts) -> str:  # 新增代码+AgentPySplitPhase6: 定义观察工具适配入口；如果没有这行代码，agent.py 的薄包装无法委托 observe 逻辑。
    action_name = str(arguments.get("action", "")).strip()  # 新增代码+AgentPySplitPhase6: 读取观察动作名用于审计；如果没有这行代码，日志里看不到模型观察了什么。
    result = controller.observe(arguments)  # 新增代码+AgentPySplitPhase6: 通过 controller 执行只读观察；如果没有这行代码，observe 不会经过统一 Computer Use 后端。
    result_data = result.data if isinstance(result.data, dict) else {}  # 新增代码+AgentPySplitPhase6: 准备安全字典形态用于 trace 计数；如果没有这行代码，非字典 data 会导致 get 调用异常。
    record_observation("computer_use_observe", {"action": action_name, "ok": result.ok, "message": result.message, "data": result.data})  # 新增代码+AgentPySplitPhase6: 记录观察结果；如果没有这行代码，窗口发现和截图读取无法在运行日志里复盘。
    record_runtime_trace("computer_observe", {"action": action_name, "ok": bool(result.ok), "message": result.message, "image_result_count": result_data.get("image_result_count", 0)})  # 新增代码+AgentPySplitPhase6: 记录 observe 工具内部摘要；如果没有这行代码，截图观察是否发生只能从长文本里猜。
    record_image_artifacts(result_data, "computer_observe")  # 新增代码+AgentPySplitPhase6: 登记 observe 返回的截图 artifact；如果没有这行代码，模型看到图片块但会话产物列表会丢失截图。
    actionability_summary = build_desktop_observation_actionability_summary(action_name, result_data, arguments)  # 新增代码+ObservePlanActVerify：从观察结果生成继续动作或阻塞 marker；如果没有这一行，get_window_state 后模型不知道该继续控制还是停下。
    base_text = result.to_text("mcp__computer-use__observe")  # 修改代码+ComputerUseMcpV2ResidualCleanup：把模型可见观察结果标成 v2 MCP 工具名；如果没有这一行，返回文本会继续泄露旧 computer_observe。
    return f"{base_text}\n{actionability_summary}" if actionability_summary else base_text  # 修改代码+ObservePlanActVerify：有 actionability 时追加到工具结果；如果没有这一行，marker 无法进入主循环。
# 新增代码+AgentPySplitPhase6: 函数段结束，computer_observe 到此结束；如果没有这个边界说明，用户不容易看出观察工具范围。


# 新增代码+AgentPySplitPhase6: 函数段开始，computer_discover 实现 Computer Use 应用发现工具；如果没有这段函数，模型无法查询本机普通应用候选。
def computer_discover(arguments: dict[str, Any], record_observation: RecordObservation, record_runtime_trace: RecordRuntimeTrace) -> str:  # 新增代码+AgentPySplitPhase6: 定义应用发现工具适配入口；如果没有这行代码，agent.py 的薄包装没有可委托对象。
    query_text = str(arguments.get("query", "")).strip()  # 新增代码+AgentPySplitPhase6: 读取模型提供的应用查询词；如果没有这行代码，discover 不知道要查哪个应用。
    max_results = arguments.get("max_results", arguments.get("limit"))  # 新增代码+AgentPySplitPhase6: 只在模型显式传数量时限制结果；如果没有这行代码，普通应用清单可能再次被默认截断。
    include_common = bool(arguments.get("include_common", True))  # 新增代码+AgentPySplitPhase6: 读取是否包含公共兜底候选；如果没有这行代码，枚举失败时 Paint 等基础应用可能缺少入口。
    report = query_windows_app_inventory(query=query_text, include_common=include_common, max_count=max_results)  # 新增代码+AgentPySplitPhase6: 调用统一应用清单查询；如果没有这行代码，discover 不会返回真实清洗候选。
    record_observation("computer_use_discover", {"ok": bool(report.get("ok", False)), "query": report.get("query", ""), "result_count": report.get("result_count", 0), "candidates": report.get("candidates", [])})  # 新增代码+AgentPySplitPhase6: 把应用发现结果写入观察流；如果没有这行代码，真实终端调试无法复盘模型看到了哪些应用候选。
    record_runtime_trace("computer_discover", {"ok": bool(report.get("ok", False)), "query": report.get("query", ""), "result_count": report.get("result_count", 0)})  # 新增代码+AgentPySplitPhase6: 记录 discover 工具内部摘要；如果没有这行代码，运行时无法证明 discover 使用的是统一 inventory 路线。
    return json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+AgentPySplitPhase6: 返回中文友好的 JSON；如果没有这行代码，模型无法稳定读取候选 app_name 和 launch_kind。
# 新增代码+AgentPySplitPhase6: 函数段结束，computer_discover 到此结束；如果没有这个边界说明，用户不容易看出应用发现工具范围。


# 新增代码+RequestAccessToolSurface: 函数段开始，request_access 适配 Computer Use 授权申请工具；如果没有这段函数，executor 即使识别工具名也无法调用 request_access。
def request_access(arguments: dict[str, Any], record_observation: RecordObservation, record_runtime_trace: RecordRuntimeTrace) -> str:  # 新增代码+RequestAccessToolSurface: 声明 agent_tools 层 request_access 入口；如果没有这一行，工具执行器无法复用 observation 和 trace 证据链。
    report = request_computer_use_access(arguments)  # 新增代码+RequestAccessToolSurface: 调用纯函数生成授权申请报告；如果没有这一行，request_access 只会有路由没有结果。
    record_observation("computer_use_request_access", {"access_request_created": bool(report.get("access_request_created")), "grant_created": bool(report.get("grant_created")), "requested_apps": report.get("requested_apps", []), "denied_requested_apps": report.get("denied_requested_apps", [])})  # 新增代码+RequestAccessToolSurface: 写入脱敏观察事件；如果没有这一行，真实终端中无法复盘模型申请了哪些普通应用。
    record_runtime_trace("computer_request_access", {"access_request_created": bool(report.get("access_request_created")), "grant_created": bool(report.get("grant_created")), "safe_hint_count": len(report.get("safe_app_hints", [])) if isinstance(report.get("safe_app_hints", []), list) else 0})  # 新增代码+RequestAccessToolSurface: 写入运行证据摘要；如果没有这一行，验收时无法确认 request_access 没有创建授权。
    return json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+RequestAccessToolSurface: 返回中文友好的 JSON 报告；如果没有这一行，模型拿不到申请结果和安全应用提示。
# 新增代码+RequestAccessToolSurface: 函数段结束，request_access 到此结束；如果没有这个边界说明，用户不容易看出它只是申请入口。


# 新增代码+AgentPySplitPhase6: 函数段开始，computer_action_acceptance_payload_from_result_data 从动作结果抽取验收字段；如果没有这段函数，真实动作成功只能靠调试日志猜。
def computer_action_acceptance_payload_from_result_data(action_name: str, result_ok: bool, result_message: str, result_data: Any) -> dict[str, Any]:  # 新增代码+AgentPySplitPhase6: 定义 structured acceptance payload 生成入口；如果没有这行代码，agent.py 的静态薄包装没有可委托对象。
    data = result_data if isinstance(result_data, dict) else {}  # 新增代码+AgentPySplitPhase6: 只接受字典结果数据；如果没有这行代码，后端返回异常类型时会把验收抽取逻辑撞崩。
    session = data.get("session") if isinstance(data.get("session"), dict) else {}  # 新增代码+AgentPySplitPhase6: 读取通用 Computer Use session 子报告；如果没有这行代码，launch resolver 的嵌套证据会丢失。
    phase108_report = session.get("phase108_report") if isinstance(session.get("phase108_report"), dict) else {}  # 新增代码+AgentPySplitPhase6: 读取应用发现和启动 resolver 报告；如果没有这行代码，start_menu_shortcut 等后端证据拿不到。
    launch_plan = phase108_report.get("launch_plan") if isinstance(phase108_report.get("launch_plan"), dict) else {}  # 新增代码+AgentPySplitPhase6: 读取最终启动计划；如果没有这行代码，显示名和启动后端只能靠脆弱字符串搜索。
    target_window = data.get("target_window") if isinstance(data.get("target_window"), dict) else {}  # 新增代码+AgentPySplitPhase6: 优先读取顶层目标窗口；如果没有这行代码，动作结果里的直接窗口证据会被漏掉。
    if not target_window:  # 新增代码+AgentPySplitPhase6: 顶层没有窗口时继续查 session；如果没有这行代码，嵌套窗口证据不会被使用。
        target_window = session.get("target_window") if isinstance(session.get("target_window"), dict) else {}  # 新增代码+AgentPySplitPhase6: 读取 session 里的目标窗口；如果没有这行代码，验收无法判断是否找到可见窗口。
    launch_backend = str(launch_plan.get("launch_backend") or phase108_report.get("launch_backend") or data.get("launch_backend") or "")  # 新增代码+AgentPySplitPhase6: 抽取真实启动后端；如果没有这行代码，场景无法区分开始菜单、App Paths 或 shell fallback。
    display_name = str(launch_plan.get("display_name") or phase108_report.get("display_name") or phase108_report.get("best_candidate_name") or data.get("target_app") or "")  # 新增代码+AgentPySplitPhase6: 抽取用户可识别应用名；如果没有这行代码，微信这类中文应用会退回调试日志断言。
    target_app = str(data.get("target_app") or session.get("target_app") or display_name)  # 新增代码+AgentPySplitPhase6: 统一输出目标应用字段；如果没有这行代码，消费者需要自己猜 display_name 是否就是目标。
    real_launch_performed = bool(data.get("real_launch_performed") or session.get("real_launch_performed") or phase108_report.get("real_launch_performed") or phase108_report.get("backend_launch_performed"))  # 新增代码+AgentPySplitPhase6: 汇总真实启动完成信号；如果没有这行代码，发现候选但未打开应用也可能误过。
    visible_window_verified = bool(data.get("visible_window_verified") or session.get("visible_window_verified") or phase108_report.get("visible_window_verified") or bool(target_window))  # 新增代码+AgentPySplitPhase6: 汇总可见窗口验证信号；如果没有这行代码，启动进程但窗口不可见也可能被当成功。
    real_desktop_touched = bool(data.get("real_desktop_touched") or session.get("real_desktop_touched") or real_launch_performed or visible_window_verified)  # 新增代码+AgentPySplitPhase6: 汇总真实桌面触达信号；如果没有这行代码，验收无法区分真实桌面路径和纯模拟路径。
    low_level_event_count = int(data.get("low_level_event_count", 0) or 0)  # 新增代码+AgentPySplitPhase6: 输出低层鼠标键盘事件数量；如果没有这行代码，点击输入类动作缺少可量化证据。
    image_result_count = int(data.get("image_result_count", 0) or 0)  # 新增代码+AgentPySplitPhase6: 输出截图结果数量；如果没有这行代码，后续无法判断动作后是否带回视觉证据。
    target_ref = _desktop_target_ref_from_data(data)  # 新增代码+FreshTargetAcceptancePayload：抽取 target_ref；如果没有这一行，验收事件无法证明一对一窗口绑定。
    fresh_target_decision = str(data.get("fresh_target_decision") or session.get("fresh_target_decision") or "")  # 新增代码+FreshTargetAcceptancePayload：抽取 FreshTarget 决策；如果没有这一行，真实终端日志看不到旧窗口策略结果。
    fresh_target_class = str(data.get("fresh_target_class") or session.get("fresh_target_class") or "")  # 新增代码+FreshTargetAcceptancePayload：抽取 FreshTarget 分类；如果没有这一行，验收无法区分新窗口和授权旧窗口。
    target_window_existed_before_launch = bool(data.get("target_window_existed_before_launch") or session.get("target_window_existed_before_launch"))  # 新增代码+FreshTargetAcceptancePayload：抽取旧窗口存在事实；如果没有这一行，旧窗口复用风险无法被正式事件记录。
    old_window_default_takeover = bool(data.get("old_window_default_takeover") or session.get("old_window_default_takeover"))  # 新增代码+FreshTargetAcceptancePayload：抽取旧窗口默认接管标记；如果没有这一行，压力测试缺少核心反证字段。
    target_lease = data.get("target_lease") if isinstance(data.get("target_lease"), dict) else session.get("target_lease") if isinstance(session.get("target_lease"), dict) else {}  # 新增代码+FreshTargetAcceptancePayload：读取租约；如果没有这一行，target_ref_one_to_one 不能可靠计算。
    target_ref_one_to_one = bool(target_ref and target_lease)  # 新增代码+FreshTargetAcceptancePayload：计算 target_ref 是否有一对一租约；如果没有这一行，多窗口任务容易退回隐式目标。
    return {  # 修改代码+FreshTargetAcceptancePayload：返回正式 JSONL 可断言 payload；如果没有这行代码，controller 只能继续读取开发调试日志。
        "state_model": "computer_action_structured_evidence",  # 新增代码+FreshTargetAcceptancePayload：声明事件模型；如果没有这一行，验收消费方不知道如何解析。
        "tool_name": "computer_action",  # 新增代码+FreshTargetAcceptancePayload：声明工具名；如果没有这一行，事件来源不清楚。
        "action": action_name,  # 新增代码+FreshTargetAcceptancePayload：记录动作名；如果没有这一行，无法知道 launch_app/type_text 等阶段。
        "ok": bool(result_ok),  # 新增代码+FreshTargetAcceptancePayload：记录动作是否成功；如果没有这一行，成功和拒绝无法区分。
        "message": result_message,  # 新增代码+FreshTargetAcceptancePayload：保留动作消息；如果没有这一行，失败原因不便排查。
        "target_app": target_app,  # 新增代码+FreshTargetAcceptancePayload：记录目标应用；如果没有这一行，多应用验收无法分辨窗口归属。
        "target_ref": target_ref,  # 新增代码+FreshTargetAcceptancePayload：记录窗口绑定 ID；如果没有这一行，后续动作无法证明一对一引用。
        "target_ref_one_to_one": target_ref_one_to_one,  # 新增代码+FreshTargetAcceptancePayload：记录租约绑定事实；如果没有这一行，压力测试无法断言 target_ref_one_to_one=true。
        "fresh_target_decision": fresh_target_decision,  # 新增代码+FreshTargetAcceptancePayload：记录 FreshTarget 决策；如果没有这一行，旧窗口保护只能靠文本猜测。
        "fresh_target_class": fresh_target_class,  # 新增代码+FreshTargetAcceptancePayload：记录 FreshTarget 分类；如果没有这一行，授权旧窗口和新窗口审计会混淆。
        "target_window_existed_before_launch": target_window_existed_before_launch,  # 新增代码+FreshTargetAcceptancePayload：记录目标窗口是否旧窗；如果没有这一行，默认接管风险不可见。
        "old_window_default_takeover": old_window_default_takeover,  # 新增代码+FreshTargetAcceptancePayload：记录是否默认接管旧窗口；如果没有这一行，验收无法证明 false。
        "real_desktop_touched": real_desktop_touched,  # 新增代码+FreshTargetAcceptancePayload：记录真实桌面触达；如果没有这一行，无法区分模拟和真实窗口。
        "real_launch_performed": real_launch_performed,  # 新增代码+FreshTargetAcceptancePayload：记录真实启动；如果没有这一行，open_application 是否成功不可见。
        "visible_window_verified": visible_window_verified,  # 新增代码+FreshTargetAcceptancePayload：记录可见窗口验证；如果没有这一行，后台进程可能误当窗口成功。
        "launch_backend": launch_backend,  # 新增代码+FreshTargetAcceptancePayload：记录启动后端；如果没有这一行，开始菜单/App Paths/fallback 路径无法审计。
        "display_name": display_name,  # 新增代码+FreshTargetAcceptancePayload：记录应用显示名；如果没有这一行，用户难以确认控制的是哪个软件。
        "target_window_present": bool(target_window),  # 新增代码+FreshTargetAcceptancePayload：记录目标窗口是否存在；如果没有这一行，空窗口报告可能误过验收。
        "low_level_event_count": low_level_event_count,  # 新增代码+FreshTargetAcceptancePayload：记录低层输入数量；如果没有这一行，零事件拒绝无法被验收。
        "image_result_count": image_result_count,  # 新增代码+FreshTargetAcceptancePayload：记录截图数量；如果没有这一行，观察证据链不完整。
    }  # 新增代码+FreshTargetAcceptancePayload：结束 payload 字典；如果没有这一行，Python 语法不完整。
# 新增代码+AgentPySplitPhase6: 函数段结束，computer_action_acceptance_payload_from_result_data 到此结束；如果没有这个边界说明，用户不容易看出验收字段抽取范围。


# 新增代码+AgentPySplitPhase6: 函数段开始，emit_computer_action_acceptance_event 写入 computer_action 正式验收事件；如果没有这段函数，真实动作结果不会进入产品级 JSONL。
def emit_computer_action_acceptance_event(action_name: str, result: Any, emit_acceptance_event: AcceptanceEmitter) -> None:  # 新增代码+AgentPySplitPhase6: 定义动作验收事件发射入口；如果没有这行代码，agent.py 仍要自己拼 payload 和写事件。
    payload = computer_action_acceptance_payload_from_result_data(action_name, bool(getattr(result, "ok", False)), str(getattr(result, "message", "")), getattr(result, "data", {}))  # 新增代码+AgentPySplitPhase6: 从控制器结果抽取稳定字段；如果没有这行代码，事件只能包含难解析的原始文本。
    emit_acceptance_event("computer_action_result", payload)  # 新增代码+AgentPySplitPhase6: 写入正式动作结果事件；如果没有这行代码，controller 无法在无调试日志的产品模式验证真实启动。
# 新增代码+AgentPySplitPhase6: 函数段结束，emit_computer_action_acceptance_event 到此结束；如果没有这个边界说明，用户不容易看出验收事件写入范围。


# 新增代码+AgentPySplitPhase6: 函数段开始，computer_action 实现高风险桌面动作工具；如果没有这段函数，schema 中的 computer_action 无法真正分发。
def computer_action(arguments: dict[str, Any], controller: Any, ask_permission: AskPermission, observe_before_action_rejection: ActionGate, agent_owned_launch_rejection: ActionGate, completion_signal_for_action: ActionGate, record_observation: RecordObservation, record_runtime_trace: RecordRuntimeTrace, record_image_artifacts: RecordImageArtifacts, emit_acceptance_event: AcceptanceEmitter) -> str:  # 新增代码+AgentPySplitPhase6: 定义动作工具适配入口；如果没有这行代码，agent.py 的薄包装无法委托真实动作流程。
    action_name = str(arguments.get("action", "")).strip()  # 新增代码+AgentPySplitPhase6: 读取动作名用于权限说明；如果没有这行代码，用户看不到 agent 准备执行哪种桌面动作。
    observe_gate_rejection = observe_before_action_rejection(action_name, arguments)  # 新增代码+AgentPySplitPhase6: 先执行“先观察再动作”硬门禁；如果没有这行代码，模型看不到截图时仍可能盲目操作鼠标键盘。
    if observe_gate_rejection is not None:  # 新增代码+AgentPySplitPhase6: 判断本次动作是否被观察门禁拒绝；如果没有这行代码，拒绝文本会被忽略继续执行。
        return observe_gate_rejection  # 新增代码+AgentPySplitPhase6: 直接返回纠偏结果且不弹权限不碰后端；如果没有这行代码，盲动仍会进入真实控制链。
    launch_gate_rejection = agent_owned_launch_rejection(action_name, arguments)  # 新增代码+AgentPySplitPhase6: 再执行“先启动并绑定目标软件”硬门禁；如果没有这行代码，模型看过旧窗口后仍可能操作旧软件。
    if launch_gate_rejection is not None:  # 新增代码+AgentPySplitPhase6: 判断本次动作是否缺少 agent-owned 目标窗口；如果没有这行代码，拒绝文本会被忽略继续执行。
        return launch_gate_rejection  # 新增代码+AgentPySplitPhase6: 直接返回纠偏结果且不弹权限不碰后端；如果没有这行代码，未启动软件前仍可能进入鼠标键盘链路。
    completion_signal = completion_signal_for_action(action_name, arguments)  # 新增代码+AgentPySplitPhase6: 检查 full 模式动作是否已足够并应收敛；如果没有这行代码，模型会在已完成后继续真实移动鼠标。
    if completion_signal is not None:  # 新增代码+AgentPySplitPhase6: 判断完成门是否触发；如果没有这行代码，收敛文本会被忽略继续执行。
        return completion_signal  # 新增代码+AgentPySplitPhase6: 返回完成信号且不触碰真实桌面；如果没有这行代码，重复动作仍会打到真实窗口。
    request_access_grant = arguments.get("request_access_grant") if isinstance(arguments.get("request_access_grant"), dict) else {}  # 新增代码+Phase2SessionGrants：读取可选 request_access 授权对象；如果没有这一行，动作层无法使用 Phase 2 会话授权。
    request_access_required = bool(arguments.get("require_request_access_grant") or request_access_grant)  # 新增代码+Phase2SessionGrants：判断本次动作是否启用 request_access 门禁；如果没有这一行，旧调用和新授权路径无法兼容。
    if request_access_required:  # 新增代码+Phase2SessionGrants：仅在新授权路径启用时执行门禁；如果没有这一行，历史调用会被突然全部拒绝。
        raw_window = arguments.get("window") if isinstance(arguments.get("window"), dict) else {}  # 新增代码+Phase2SessionGrants：读取窗口目标对象；如果没有这一行，门禁无法知道动作要控制哪个 app。
        target = dict(raw_window or {})  # 新增代码+Phase2SessionGrants：复制目标窗口信息；如果没有这一行，后续补字段可能污染原始参数。
        target.setdefault("app_id", arguments.get("app_id") or arguments.get("app") or arguments.get("target_app") or arguments.get("app_name") or arguments.get("target"))  # 新增代码+Phase2SessionGrants：补齐动作目标 app_id；如果没有这一行，launch_app 这类无 window 动作无法匹配授权。
        grant_decision = deny_action_without_request_access(request_access_grant, target, action=action_name)  # 新增代码+Phase2SessionGrants：在权限弹窗和 controller 前评估授权；如果没有这一行，未授权动作可能先触碰桌面。
        if not bool(grant_decision.get("allowed")):  # 新增代码+Phase2SessionGrants：判断授权门禁是否拒绝；如果没有这一行，拒绝结果会被忽略继续执行。
            record_observation("computer_use_request_access_denied", {"action": action_name, "decision": grant_decision.get("decision"), "target_summary": grant_decision.get("target_summary", {})})  # 新增代码+Phase2SessionGrants：记录脱敏拒绝事件；如果没有这一行，审计无法解释动作为什么没执行。
            record_runtime_trace("computer_request_access_denial", {"action": action_name, "decision": grant_decision.get("decision"), "low_level_event_count": grant_decision.get("low_level_event_count", 0)})  # 新增代码+Phase2SessionGrants：记录拒绝路径低层事件计数；如果没有这一行，验收无法证明没有触碰桌面。
            return json.dumps(grant_decision, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase2SessionGrants：返回结构化拒绝给模型；如果没有这一行，模型无法知道要重新申请授权。
    permission_payload = redact_action_arguments(action_name, arguments)  # 新增代码+AgentPySplitPhase6: 复制并脱敏参数用于权限展示和审计；如果没有这行代码，原始 type_text 可能进入终端日志或观察记录。
    permission_text = json.dumps(permission_payload, ensure_ascii=False, indent=2)  # 新增代码+AgentPySplitPhase6: 把脱敏参数格式化成用户可读 JSON；如果没有这行代码，权限提示不便核对坐标和文本。
    permission_action = f"执行 OS Computer Use 桌面动作：{action_name}\n参数：{permission_text}"  # 新增代码+AgentPySplitPhase6: 构造清晰权限说明；如果没有这行代码，用户无法知道 agent 准备控制桌面做什么。
    if not ask_permission(permission_action):  # 新增代码+AgentPySplitPhase6: 高风险桌面动作必须再次请求用户确认；如果没有这行代码，computer_action 会绕过权限边界。
        record_observation("computer_use_denied", {"action": action_name, "arguments": permission_payload})  # 新增代码+AgentPySplitPhase6: 记录用户拒绝桌面动作；如果没有这行代码，审计无法解释动作为什么没执行。
        return f"用户拒绝了操作：{permission_action}"  # 新增代码+AgentPySplitPhase6: 返回拒绝信息给模型；如果没有这行代码，模型可能误以为动作已经完成。
    result = controller.execute(arguments)  # 新增代码+AgentPySplitPhase6: 通过 controller 执行安全检查和后端调用；如果没有这行代码，动作不会真正到达 Computer Use 后端。
    result_data = result.data if isinstance(result.data, dict) else {}  # 新增代码+AgentPySplitPhase6: 准备安全字典形态用于 trace 和 artifact 登记；如果没有这行代码，异常 data 会导致 get 调用失败。
    record_observation("computer_use_action", {"action": action_name, "ok": result.ok, "message": result.message, "data": result.data})  # 新增代码+AgentPySplitPhase6: 记录桌面动作结果；如果没有这行代码，真实终端无法复盘 Computer Use 行为。
    record_runtime_trace("computer_action", {"action": action_name, "ok": bool(result.ok), "message": result.message, "low_level_event_count": result_data.get("low_level_event_count", 0), "image_result_count": result_data.get("image_result_count", 0)})  # 新增代码+AgentPySplitPhase6: 记录 action 工具内部摘要；如果没有这行代码，鼠标键盘动作证据只能散落在 controller 文本里。
    emit_computer_action_acceptance_event(action_name, result, emit_acceptance_event)  # 新增代码+AgentPySplitPhase6: 把真实动作结果写入正式验收事件；如果没有这行代码，微信打开成功只能靠 debug log 证明。
    record_image_artifacts(result_data, "computer_action")  # 新增代码+AgentPySplitPhase6: 登记 action 结果中的截图 artifact；如果没有这行代码，动作前后证据截图不会进入 active_artifacts。
    actionability_summary = build_desktop_actionability_summary_from_action_result(action_name, result_data)  # 新增代码+ObservePlanActVerify：从 launch_app 结果生成下一步 observe marker；如果没有这一行，启动应用后模型可能不观察真实窗口。
    base_text = result.to_text()  # 修改代码+ObservePlanActVerify：先生成原始动作文本；如果没有这一行，旧兼容输出会丢失。
    return f"{base_text}\n{actionability_summary}" if actionability_summary else base_text  # 修改代码+ObservePlanActVerify：有 actionability 时追加到工具结果；如果没有这一行，marker 无法进入主循环。
# 新增代码+AgentPySplitPhase6: 函数段结束，computer_action 到此结束；如果没有这个边界说明，用户不容易看出高风险动作工具范围。


# 新增代码+AgentPySplitPhase6: 函数段开始，computer_use_mode 保留通用 Windows Computer Use mode 兼容入口；如果没有这段函数，旧 operation=mode 测试会断开。
def computer_use_mode(arguments: dict[str, Any], record_observation: RecordObservation, runtime_factory: UniversalRuntimeFactory = UniversalWindowsComputerUseRuntime) -> str:  # 新增代码+AgentPySplitPhase6: 定义 mode 工具适配入口；如果没有这行代码，agent.py 的薄包装无法委托旧 mode 逻辑。
    prompt_text = str(arguments.get("prompt", ""))  # 新增代码+AgentPySplitPhase6: 读取用户 prompt 只传给 runtime 内存处理；如果没有这行代码，新模式不知道用户要做什么。
    real_actions = bool(arguments.get("real_actions", False))  # 新增代码+AgentPySplitPhase6: 读取真实动作开关且默认关闭；如果没有这行代码，普通 mode 调用可能误触真实桌面。
    if real_actions:  # 新增代码+AgentPySplitPhase6: 真实动作 prompt 入口不再黑盒执行整段任务；如果没有这行代码，模型可能继续把 run_prompt 当成语义规划器。
        report = {"ok": False, "decision": "model_loop_observe_action_required", "reason": "semantic planning must happen in the model loop", "next_tools": ["mcp__computer-use__observe", "mcp__computer-use__left_click", "mcp__computer-use__type", "mcp__computer-use__key", "mcp__computer-use__scroll", "mcp__computer-use__computer_batch"], "prompt_text_included": False, "real_actions_requested": True}  # 修改代码+ComputerUseMcpV2ResidualCleanup：降级报告只提示 v2 MCP 原子工具；如果没有这行代码，模型会继续尝试隐藏旧 computer_observe/computer_action/computer_use。
        record_observation("computer_use_model_loop_required", report)  # 新增代码+AgentPySplitPhase6: 把降级事件写入审计流；如果没有这行代码，真实终端排查无法看到 run_prompt 被安全拦回主循环。
        return json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+AgentPySplitPhase6: 返回 JSON 给模型读取并自我修正；如果没有这行代码，工具调用无法给下一轮模型提供稳定反馈。
    runtime = runtime_factory()  # 新增代码+AgentPySplitPhase6: 创建通用运行时实例；如果没有这行代码，mode 工具不会产生结构化结果。
    report = runtime.run_prompt(prompt_text, real_actions=real_actions)  # 新增代码+AgentPySplitPhase6: 运行 prompt 到通用闭环；如果没有这行代码，旧 mode 兼容入口没有实际报告。
    record_observation("computer_use_mode", {"ok": bool(report.get("ok")), "prompt_sha256_16": report.get("prompt_sha256_16", ""), "prompt_text_included": False, "real_actions_requested": bool(report.get("real_actions_requested")), "single_universal_runtime": bool(report.get("single_universal_runtime")), "per_app_controller_required": bool(report.get("per_app_controller_required"))})  # 新增代码+AgentPySplitPhase6: 记录脱敏 mode 结果；如果没有这行代码，审计无法看到 mode 是否进入通用运行时。
    return json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+AgentPySplitPhase6: 返回中文友好的 JSON 报告；如果没有这行代码，模型无法读取 mode 结果。
# 新增代码+AgentPySplitPhase6: 函数段结束，computer_use_mode 到此结束；如果没有这个边界说明，用户不容易看出 mode 兼容入口范围。


# 新增代码+AgentPySplitPhase6: 函数段开始，computer_use_compat 实现 computer_use / computer-use 兼容工具分发；如果没有这段函数，统一工具名无法调用旧能力。
def computer_use_compat(arguments: dict[str, Any], ask_permission: AskPermission, record_observation: RecordObservation, record_runtime_trace: RecordRuntimeTrace, computer_use_mode_handler: ComputerToolHandler, computer_status_handler: ComputerToolHandler, computer_discover_handler: ComputerToolHandler, computer_observe_handler: ComputerToolHandler, computer_action_handler: ComputerToolHandler) -> str:  # 新增代码+AgentPySplitPhase6: 定义兼容工具适配入口；如果没有这行代码，agent.py 的薄包装无法委托 compat 分发。
    dispatch = normalize_computer_use_compat_arguments(arguments)  # 新增代码+AgentPySplitPhase6: 把 ClaudeCode 风格参数转换为旧工具参数；如果没有这行代码，兼容工具会绕开既有 controller 和安全策略。
    audit_dispatch = dict(dispatch)  # 新增代码+AgentPySplitPhase6: 复制 dispatch 用于脱敏审计；如果没有这行代码，后续替换 arguments 会污染真实分发参数。
    if "audit_arguments" in audit_dispatch:  # 新增代码+AgentPySplitPhase6: 检查兼容层是否提供脱敏审计字段；如果没有这行代码，mode prompt 原文可能进入观察日志。
        audit_dispatch["arguments"] = dict(audit_dispatch.get("audit_arguments", {}) or {})  # 新增代码+AgentPySplitPhase6: 用脱敏参数替换日志里的真实参数；如果没有这行代码，dispatch 日志会记录用户 prompt 原文。
        audit_dispatch.pop("audit_arguments", None)  # 新增代码+AgentPySplitPhase6: 删除辅助审计字段避免重复；如果没有这行代码，日志结构会同时出现两套参数字段。
    record_observation("computer_use_compat_dispatch", audit_dispatch)  # 新增代码+AgentPySplitPhase6: 记录脱敏后的兼容分发结果；如果没有这行代码，mode 隐私边界和工具路由不可复盘。
    record_runtime_trace("computer_use_compat_dispatch", {"ok": bool(dispatch.get("ok", False)), "target_tool": dispatch.get("target_tool", ""), "operation": dict(audit_dispatch.get("arguments", {}) or {}).get("operation", "") if isinstance(audit_dispatch.get("arguments", {}), dict) else ""})  # 新增代码+AgentPySplitPhase6: 记录兼容工具分发目标；如果没有这行代码，后续无法确认 computer_use 是否只是薄兼容层。
    if not bool(dispatch.get("ok", False)):  # 新增代码+AgentPySplitPhase6: 检查归一化是否成功；如果没有这行代码，错误参数可能继续进入底层工具造成混乱结果。
        return str(dispatch.get("error", "computer_use 兼容工具参数无效。"))  # 新增代码+AgentPySplitPhase6: 返回清晰参数错误；如果没有这行代码，模型不知道该如何修正 operation 或 action。
    target_tool = str(dispatch.get("target_tool", ""))  # 新增代码+AgentPySplitPhase6: 读取目标旧工具名；如果没有这行代码，兼容入口不知道该调用哪个已有函数。
    target_arguments = dict(dispatch.get("arguments", {}))  # 新增代码+AgentPySplitPhase6: 复制目标参数避免修改原始 dispatch；如果没有这行代码，后续审计数据可能被底层工具意外改动。
    if target_tool == "computer_use_mode":  # 新增代码+AgentPySplitPhase6: 分发 mode 到通用 Computer Use 运行时；如果没有这行代码，operation=mode 会落到未知目标工具。
        if bool(target_arguments.get("real_actions", False)):  # 新增代码+AgentPySplitPhase6: 只有请求真实动作时才弹权限说明；如果没有这行代码，普通预演 mode 会被不必要地阻塞。
            permission_payload = dict(dispatch.get("audit_arguments", {}) or {})  # 新增代码+AgentPySplitPhase6: 使用脱敏审计参数构造权限提示；如果没有这行代码，用户 prompt 原文可能显示在权限文本中。
            permission_text = json.dumps(permission_payload, ensure_ascii=False, indent=2)  # 新增代码+AgentPySplitPhase6: 格式化脱敏权限信息；如果没有这行代码，用户不容易确认本次真实动作请求。
            if not ask_permission(f"执行通用 OS Computer Use mode 真实桌面动作。\n参数：{permission_text}"):  # 新增代码+AgentPySplitPhase6: 真实动作必须经过用户确认；如果没有这行代码，mode 可能绕开桌面动作权限边界。
                record_observation("computer_use_mode_denied", permission_payload)  # 新增代码+AgentPySplitPhase6: 记录用户拒绝 mode 真实动作；如果没有这行代码，审计无法解释为什么没有继续。
                return "用户拒绝了通用 OS Computer Use mode 真实桌面动作。"  # 新增代码+AgentPySplitPhase6: 返回拒绝说明；如果没有这行代码，模型可能误以为动作已经执行。
        return computer_use_mode_handler(target_arguments)  # 新增代码+AgentPySplitPhase6: 调用通用 mode 处理器；如果没有这行代码，Phase92 runtime 不会执行。
    if target_tool == "computer_status":  # 新增代码+AgentPySplitPhase6: 分发 status 到只读状态工具；如果没有这行代码，compat status 无法复用现有状态实现。
        return computer_status_handler(target_arguments)  # 新增代码+AgentPySplitPhase6: 调用 status 工具处理器；如果没有这行代码，状态查询不会进入统一 controller 状态读取。
    if target_tool == "computer_discover":  # 新增代码+AgentPySplitPhase6: 分发 discover 到只读应用发现工具；如果没有这行代码，operation=discover 会落到未知目标。
        return computer_discover_handler(target_arguments)  # 新增代码+AgentPySplitPhase6: 调用 discover 工具处理器；如果没有这行代码，兼容入口会出现第二套应用发现逻辑。
    if target_tool == "computer_observe":  # 新增代码+AgentPySplitPhase6: 分发 observe 到只读观察工具；如果没有这行代码，compat observe 会绕开现有观察审计和截图登记。
        return computer_observe_handler(target_arguments)  # 新增代码+AgentPySplitPhase6: 调用 observe 工具处理器；如果没有这行代码，窗口枚举和截图观察不会走统一安全边界。
    if target_tool == "computer_action":  # 新增代码+AgentPySplitPhase6: 分发 action 到高风险动作工具；如果没有这行代码，compat action 无法复用现有审批、锁和 controller 执行链。
        return computer_action_handler(target_arguments)  # 新增代码+AgentPySplitPhase6: 调用 action 工具处理器；如果没有这行代码，真实桌面动作可能出现两套不一致实现。
    return f"computer_use 兼容工具失败：未知目标工具 {target_tool}"  # 新增代码+AgentPySplitPhase6: 兜底返回未知分发目标；如果没有这行代码，异常 dispatch 会沉默失败或抛出难懂错误。
# 新增代码+AgentPySplitPhase6: 函数段结束，computer_use_compat 到此结束；如果没有这个边界说明，用户不容易看出兼容工具分发范围。
