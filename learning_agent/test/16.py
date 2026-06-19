from learning_agent.computer_use_mcp_v2.windows_runtime.target_lease import (  # 新增代码+TargetLeaseTest：导入待实现的通用目标租约模块；如果没有这一行，测试无法证明新架构入口是否存在。
    TargetLease,  # 新增代码+TargetLeaseTest：导入目标租约类型；如果没有这一行，测试无法检查公开类型是否稳定。
    build_target_lease,  # 新增代码+TargetLeaseTest：导入租约构建函数；如果没有这一行，测试无法覆盖 launch_app 后如何生成租约。
    verify_target_lease_before_action,  # 新增代码+TargetLeaseTest：导入动作前验证函数；如果没有这一行，测试无法覆盖 SendInput 前的安全门禁。
)  # 新增代码+TargetLeaseTest：结束多行导入；如果没有这一行，Python 语法不完整。
from learning_agent.computer_use_mcp_v2.windows_runtime.target_registry import ComputerUseTargetRegistry  # 新增代码+TargetLeaseTest：导入目标注册表；如果没有这一行，测试无法验证 target_ref 是否能保存租约。


def _launch_result(pid: int = 101) -> dict:  # 新增代码+TargetLeaseTest：函数段开始，构造 agent 自己启动应用的进程事实；如果没有这段函数，每个测试都要重复写启动报告。
    return {  # 新增代码+TargetLeaseTest：返回模拟启动报告；如果没有这一行，租约构建没有输入事实。
        "ok": True,  # 新增代码+TargetLeaseTest：声明启动成功；如果没有这一行，租约可能被误判为未启动。
        "process_started": True,  # 新增代码+TargetLeaseTest：声明进程已启动；如果没有这一行，进程身份无法被验证。
        "process_id": pid,  # 新增代码+TargetLeaseTest：保存启动进程 pid；如果没有这一行，漂移测试无法比较进程。
        "process_executable": "paint.exe",  # 新增代码+TargetLeaseTest：保存启动程序名；如果没有这一行，目标身份缺少应用侧事实。
        "owned_process_registered": True,  # 新增代码+TargetLeaseTest：声明进程属于当前 agent；如果没有这一行，自有目标不能被确认为安全。
        "real_desktop_touched": True,  # 新增代码+TargetLeaseTest：声明真实启动路径发生；如果没有这一行，报告无法区分录制和真实路径。
    }  # 新增代码+TargetLeaseTest：结束启动报告字典；如果没有这一行，Python 语法不完整。
# 新增代码+TargetLeaseTest：函数段结束，_launch_result 到此结束；如果没有这个边界说明，后续维护者不容易看出测试夹具范围。


def _window(pid: int = 101, hwnd: int = 202, title: str = "Untitled - Paint") -> dict:  # 新增代码+TargetLeaseTest：函数段开始，构造可验证窗口事实；如果没有这段函数，测试无法稳定模拟窗口身份。
    return {  # 新增代码+TargetLeaseTest：返回模拟窗口字典；如果没有这一行，租约验证没有窗口输入。
        "app_id": "paint.exe",  # 新增代码+TargetLeaseTest：保存应用身份；如果没有这一行，窗口无法和应用绑定。
        "process_name": "paint.exe",  # 新增代码+TargetLeaseTest：保存进程名；如果没有这一行，窗口身份缺少进程线索。
        "pid": pid,  # 新增代码+TargetLeaseTest：保存窗口 pid；如果没有这一行，动作前无法发现 pid 漂移。
        "hwnd": hwnd,  # 新增代码+TargetLeaseTest：保存窗口句柄；如果没有这一行，动作前无法发现句柄漂移。
        "window_id": f"hwnd:{hwnd}",  # 新增代码+TargetLeaseTest：保存协议窗口 id；如果没有这一行，target_ref 无法还原稳定窗口。
        "title_preview": title,  # 新增代码+TargetLeaseTest：保存窗口标题摘要；如果没有这一行，标题漂移无法被审计。
        "rect": {"left": 0, "top": 0, "right": 800, "bottom": 600},  # 新增代码+TargetLeaseTest：保存窗口矩形；如果没有这一行，后续坐标转换测试会缺少窗口边界。
    }  # 新增代码+TargetLeaseTest：结束窗口字典；如果没有这一行，Python 语法不完整。
# 新增代码+TargetLeaseTest：函数段结束，_window 到此结束；如果没有这个边界说明，后续维护者不容易看出窗口夹具范围。


def test_agent_owned_launch_lease_allows_same_window() -> None:  # 新增代码+TargetLeaseTest：函数段开始，验证自有启动窗口可被允许；如果没有这段测试，正常路径可能被新门禁误杀。
    lease = build_target_lease(  # 新增代码+TargetLeaseTest：构建自有启动租约；如果没有这一行，后续无法验证同窗口动作。
        session_id="session-1",  # 新增代码+TargetLeaseTest：绑定会话 id；如果没有这一行，租约不能证明属于当前 session。
        target_ref="target-1",  # 新增代码+TargetLeaseTest：绑定 target_ref；如果没有这一行，模型后续动作没有稳定引用。
        origin="agent_owned_launch",  # 新增代码+TargetLeaseTest：声明来源是 agent 自己启动；如果没有这一行，安全策略不知道该按自有进程验证。
        launch_result=_launch_result(),  # 新增代码+TargetLeaseTest：提供启动事实；如果没有这一行，租约缺少进程侧证据。
        target_window=_window(),  # 新增代码+TargetLeaseTest：提供窗口事实；如果没有这一行，租约缺少窗口侧证据。
        user_granted_existing_window=False,  # 新增代码+TargetLeaseTest：声明不是用户授权旧窗口；如果没有这一行，测试无法区分两类目标。
    )  # 新增代码+TargetLeaseTest：结束租约构建；如果没有这一行，Python 语法不完整。

    result = verify_target_lease_before_action(  # 新增代码+TargetLeaseTest：执行动作前租约验证；如果没有这一行，无法证明 SendInput 前会检查目标。
        lease=lease,  # 新增代码+TargetLeaseTest：传入期望租约；如果没有这一行，验证函数没有基准。
        current_window=_window(),  # 新增代码+TargetLeaseTest：传入未漂移窗口；如果没有这一行，正常路径无法被验证。
        action="type_text",  # 新增代码+TargetLeaseTest：选择写文本动作；如果没有这一行，测试可能绕过写动作门禁。
    )  # 新增代码+TargetLeaseTest：结束验证调用；如果没有这一行，Python 语法不完整。

    assert isinstance(lease, TargetLease)  # 新增代码+TargetLeaseTest：确认公开类型稳定；如果没有这一行，返回散乱字典也可能误过测试。
    assert result.allowed is True  # 新增代码+TargetLeaseTest：确认同一自有窗口允许动作；如果没有这一行，正常应用控制可能被误拒绝。
    assert result.low_level_event_count == 0  # 新增代码+TargetLeaseTest：确认验证阶段不发送真实输入；如果没有这一行，安全门禁可能自己触发桌面事件。
    assert result.decision == "target_lease_verified"  # 新增代码+TargetLeaseTest：确认成功决策 token 稳定；如果没有这一行，controller 无法可靠解释结果。
# 新增代码+TargetLeaseTest：函数段结束，test_agent_owned_launch_lease_allows_same_window 到此结束；如果没有这个边界说明，用户不容易看出正例范围。


def test_agent_owned_launch_lease_rejects_pid_drift() -> None:  # 新增代码+TargetLeaseTest：函数段开始，验证 pid 漂移会被拒绝；如果没有这段测试，旧用户窗口可能被误控。
    lease = build_target_lease(  # 新增代码+TargetLeaseTest：构建原始自有窗口租约；如果没有这一行，漂移比较没有基准。
        session_id="session-1",  # 新增代码+TargetLeaseTest：绑定会话 id；如果没有这一行，租约不能证明属于当前 session。
        target_ref="target-1",  # 新增代码+TargetLeaseTest：绑定 target_ref；如果没有这一行，漂移报告缺少引用。
        origin="agent_owned_launch",  # 新增代码+TargetLeaseTest：声明来源是 agent 自己启动；如果没有这一行，验证策略无法使用自有进程规则。
        launch_result=_launch_result(pid=101),  # 新增代码+TargetLeaseTest：提供原始 pid；如果没有这一行，pid 漂移不可验证。
        target_window=_window(pid=101),  # 新增代码+TargetLeaseTest：提供原始窗口；如果没有这一行，窗口基准缺失。
        user_granted_existing_window=False,  # 新增代码+TargetLeaseTest：声明不是用户授权旧窗口；如果没有这一行，漂移规则可能走错分支。
    )  # 新增代码+TargetLeaseTest：结束租约构建；如果没有这一行，Python 语法不完整。

    result = verify_target_lease_before_action(  # 新增代码+TargetLeaseTest：执行动作前验证；如果没有这一行，漂移不会被检测。
        lease=lease,  # 新增代码+TargetLeaseTest：传入原始租约；如果没有这一行，验证没有期望目标。
        current_window=_window(pid=999),  # 新增代码+TargetLeaseTest：传入漂移后的窗口；如果没有这一行，测试无法模拟误控旧窗口。
        action="type_text",  # 新增代码+TargetLeaseTest：选择写文本动作；如果没有这一行，漂移门禁可能不生效。
    )  # 新增代码+TargetLeaseTest：结束验证调用；如果没有这一行，Python 语法不完整。

    assert result.allowed is False  # 新增代码+TargetLeaseTest：确认漂移窗口被拒绝；如果没有这一行，真实输入可能打到错误窗口。
    assert result.low_level_event_count == 0  # 新增代码+TargetLeaseTest：确认拒绝路径零事件；如果没有这一行，拒绝也可能已经触碰桌面。
    assert result.decision == "target_lease_drift_rejected"  # 新增代码+TargetLeaseTest：确认漂移拒绝 token 稳定；如果没有这一行，模型无法可靠恢复。
    assert result.target_drift_blocks_action is True  # 新增代码+TargetLeaseTest：确认漂移会阻断动作；如果没有这一行，报告无法证明门禁有效。
# 新增代码+TargetLeaseTest：函数段结束，test_agent_owned_launch_lease_rejects_pid_drift 到此结束；如果没有这个边界说明，用户不容易看出漂移测试范围。


def test_existing_window_requires_explicit_user_grant() -> None:  # 新增代码+TargetLeaseTest：函数段开始，验证已有用户窗口必须显式授权；如果没有这段测试，full mode 可能误控用户旧窗口。
    lease = build_target_lease(  # 新增代码+TargetLeaseTest：构建已有窗口租约；如果没有这一行，授权门禁没有输入。
        session_id="session-1",  # 新增代码+TargetLeaseTest：绑定会话 id；如果没有这一行，租约不能归属当前 session。
        target_ref="target-2",  # 新增代码+TargetLeaseTest：绑定 target_ref；如果没有这一行，授权失败报告缺少目标。
        origin="user_granted_existing_window",  # 新增代码+TargetLeaseTest：声明来源是用户已有窗口；如果没有这一行，策略无法要求用户授权。
        launch_result={},  # 新增代码+TargetLeaseTest：已有窗口没有 agent 启动事实；如果没有这一行，构建函数无法覆盖空启动报告。
        target_window=_window(pid=303, hwnd=404, title="Budget.xlsx - Excel"),  # 新增代码+TargetLeaseTest：提供已有窗口身份；如果没有这一行，授权测试没有目标。
        user_granted_existing_window=False,  # 新增代码+TargetLeaseTest：声明用户没有授权；如果没有这一行，拒绝路径无法被验证。
    )  # 新增代码+TargetLeaseTest：结束租约构建；如果没有这一行，Python 语法不完整。

    result = verify_target_lease_before_action(  # 新增代码+TargetLeaseTest：执行动作前验证；如果没有这一行，授权缺失不会被发现。
        lease=lease,  # 新增代码+TargetLeaseTest：传入已有窗口租约；如果没有这一行，验证没有授权状态。
        current_window=_window(pid=303, hwnd=404, title="Budget.xlsx - Excel"),  # 新增代码+TargetLeaseTest：传入同一已有窗口；如果没有这一行，测试不能证明即便同窗口也需要授权。
        action="type_text",  # 新增代码+TargetLeaseTest：选择写文本动作；如果没有这一行，授权门禁可能绕过写动作。
    )  # 新增代码+TargetLeaseTest：结束验证调用；如果没有这一行，Python 语法不完整。

    assert result.allowed is False  # 新增代码+TargetLeaseTest：确认未授权已有窗口被拒绝；如果没有这一行，full mode 可能误控用户资料。
    assert result.decision == "existing_window_missing_user_grant"  # 新增代码+TargetLeaseTest：确认拒绝原因稳定；如果没有这一行，用户不知道需要授权。
    assert result.low_level_event_count == 0  # 新增代码+TargetLeaseTest：确认拒绝路径零事件；如果没有这一行，未授权拒绝仍可能已触发输入。
# 新增代码+TargetLeaseTest：函数段结束，test_existing_window_requires_explicit_user_grant 到此结束；如果没有这个边界说明，用户不容易看出授权拒绝范围。


def test_existing_window_with_user_grant_allows_same_window() -> None:  # 新增代码+TargetLeaseTest：函数段开始，验证用户授权已有窗口可被控制；如果没有这段测试，合法用户授权路径可能被误拒绝。
    lease = build_target_lease(  # 新增代码+TargetLeaseTest：构建已授权已有窗口租约；如果没有这一行，正例没有验证对象。
        session_id="session-1",  # 新增代码+TargetLeaseTest：绑定会话 id；如果没有这一行，租约不能归属当前 session。
        target_ref="target-3",  # 新增代码+TargetLeaseTest：绑定 target_ref；如果没有这一行，后续动作没有稳定引用。
        origin="user_granted_existing_window",  # 新增代码+TargetLeaseTest：声明来源是用户已有窗口；如果没有这一行，策略不能进入用户授权分支。
        launch_result={},  # 新增代码+TargetLeaseTest：已有窗口没有启动报告；如果没有这一行，构建函数无法覆盖授权旧窗口。
        target_window=_window(pid=303, hwnd=404, title="Budget.xlsx - Excel"),  # 新增代码+TargetLeaseTest：提供窗口身份；如果没有这一行，验证没有目标。
        user_granted_existing_window=True,  # 新增代码+TargetLeaseTest：声明用户已经授权；如果没有这一行，已有窗口会被安全拒绝。
    )  # 新增代码+TargetLeaseTest：结束租约构建；如果没有这一行，Python 语法不完整。

    result = verify_target_lease_before_action(  # 新增代码+TargetLeaseTest：执行动作前验证；如果没有这一行，无法证明授权路径可用。
        lease=lease,  # 新增代码+TargetLeaseTest：传入已授权租约；如果没有这一行，验证没有授权事实。
        current_window=_window(pid=303, hwnd=404, title="Budget.xlsx - Excel"),  # 新增代码+TargetLeaseTest：传入同一窗口；如果没有这一行，正例无法通过身份匹配。
        action="type_text",  # 新增代码+TargetLeaseTest：选择写文本动作；如果没有这一行，无法覆盖真实高风险动作。
    )  # 新增代码+TargetLeaseTest：结束验证调用；如果没有这一行，Python 语法不完整。

    assert result.allowed is True  # 新增代码+TargetLeaseTest：确认用户授权同窗口允许动作；如果没有这一行，用户授权功能不可用。
    assert result.decision == "target_lease_verified"  # 新增代码+TargetLeaseTest：确认成功 token 稳定；如果没有这一行，controller 难以统一处理成功路径。
# 新增代码+TargetLeaseTest：函数段结束，test_existing_window_with_user_grant_allows_same_window 到此结束；如果没有这个边界说明，用户不容易看出授权正例范围。


def test_target_registry_stores_and_resolves_lease() -> None:  # 新增代码+TargetLeaseTest：函数段开始，验证 target_ref 可以解析出租约；如果没有这段测试，registry 仍可能只保存裸窗口。
    registry = ComputerUseTargetRegistry(session_id="session-lease")  # 新增代码+TargetLeaseTest：创建隔离注册表；如果没有这一行，测试无法保存 target_ref。
    lease = build_target_lease(  # 新增代码+TargetLeaseTest：构建待保存的自有目标租约；如果没有这一行，registry 没有租约输入。
        session_id="session-lease",  # 新增代码+TargetLeaseTest：绑定会话 id；如果没有这一行，租约和 registry 会话无法对应。
        target_ref="",  # 新增代码+TargetLeaseTest：先传空 ref，由 registry 生成真实 ref；如果没有这一行，测试无法覆盖注册时补 ref 的路径。
        origin="agent_owned_launch",  # 新增代码+TargetLeaseTest：声明来源为 agent 启动；如果没有这一行，租约身份验证规则不明确。
        launch_result=_launch_result(),  # 新增代码+TargetLeaseTest：提供启动事实；如果没有这一行，租约不会被验证为自有目标。
        target_window=_window(),  # 新增代码+TargetLeaseTest：提供窗口事实；如果没有这一行，租约没有目标窗口。
        user_granted_existing_window=False,  # 新增代码+TargetLeaseTest：声明不是用户已有窗口授权；如果没有这一行，测试不能覆盖 agent-owned 分支。
    )  # 新增代码+TargetLeaseTest：结束租约构建；如果没有这一行，Python 语法不完整。

    target_ref = registry.register_target(_window(), source_action="launch_app", lease=lease)  # 新增代码+TargetLeaseTest：注册窗口和租约；如果没有这一行，target_ref 不会持有 lease。
    resolved = registry.resolve_target_ref(target_ref)  # 新增代码+TargetLeaseTest：按 ref 解析目标；如果没有这一行，测试无法验证 registry 输出。

    assert resolved["ok"] is True  # 新增代码+TargetLeaseTest：确认 ref 能解析成功；如果没有这一行，坏 ref 也可能被误当通过。
    assert resolved["target"]["lease"]["origin"] == "agent_owned_launch"  # 新增代码+TargetLeaseTest：确认租约来源被保存；如果没有这一行，权限来源会丢失。
    assert resolved["target"]["lease"]["lease_identity_verified"] is True  # 新增代码+TargetLeaseTest：确认租约验证状态被保存；如果没有这一行，动作前门禁无法复用注册事实。
# 新增代码+TargetLeaseTest：函数段结束，test_target_registry_stores_and_resolves_lease 到此结束；如果没有这个边界说明，用户不容易看出 registry 测试范围。
def test_resource_identity_is_optional_for_unknown_apps() -> None:  # 新增代码+ResourceIdentityTest：函数段开始，验证未知应用没有资源身份也不阻断通用控制；如果没有这个测试，resource identity 可能被误设计成硬门禁。
    from learning_agent.computer_use_mcp_v2.windows_runtime.resource_identity import build_resource_identity  # 新增代码+ResourceIdentityTest：局部导入待实现 helper；如果没有这一行，测试无法触发资源身份模块。
    identity = build_resource_identity(  # 新增代码+ResourceIdentityTest：构建未知应用资源身份；如果没有这一行，测试没有被测输出。
        target_window={  # 新增代码+ResourceIdentityTest：准备未知应用窗口；如果没有这一行，helper 没有窗口输入。
            "app_id": "unknown.exe",  # 新增代码+ResourceIdentityTest：声明未知应用；如果没有这一行，测试无法证明 unknown 不被强制识别。
            "title_preview": "Some App",  # 新增代码+ResourceIdentityTest：提供普通标题；如果没有这一行，helper 无法读取标题摘要。
        },  # 新增代码+ResourceIdentityTest：结束窗口输入字典；如果没有这一行，Python 语法不完整。
        requested_resource_hint="",  # 新增代码+ResourceIdentityTest：不提供资源提示；如果没有这一行，测试无法验证缺 hint 时的可选行为。
    )  # 新增代码+ResourceIdentityTest：结束资源身份构建调用；如果没有这一行，Python 语法不完整。
    assert identity["available"] is False  # 新增代码+ResourceIdentityTest：确认未知应用资源身份不可用；如果没有这一行，helper 可能误报支持。
    assert identity["required_for_generic_control"] is False  # 新增代码+ResourceIdentityTest：确认资源身份不是通用控制硬要求；如果没有这一行，agent 可能被迫为每个应用写专用识别器。
# 新增代码+ResourceIdentityTest：函数段结束，test_resource_identity_is_optional_for_unknown_apps 到此结束；如果没有这个边界说明，读者不容易看出可选身份测试范围。


def test_document_title_resource_identity_matches_hint() -> None:  # 新增代码+ResourceIdentityTest：函数段开始，验证文档类标题能匹配用户资源提示；如果没有这个测试，Notepad 文件名证据无法被通用报告表达。
    from learning_agent.computer_use_mcp_v2.windows_runtime.resource_identity import build_resource_identity  # 新增代码+ResourceIdentityTest：局部导入待实现 helper；如果没有这一行，测试无法调用资源身份模块。
    identity = build_resource_identity(  # 新增代码+ResourceIdentityTest：构建文档类资源身份；如果没有这一行，测试没有被测输出。
        target_window={  # 新增代码+ResourceIdentityTest：准备 Notepad 窗口输入；如果没有这一行，helper 没有窗口标题可读。
            "app_id": "notepad.exe",  # 新增代码+ResourceIdentityTest：声明文档类应用；如果没有这一行，helper 无法识别文档类窗口。
            "title_preview": "1.txt - Notepad",  # 新增代码+ResourceIdentityTest：提供含文件名标题；如果没有这一行，资源 hint 无法匹配。
        },  # 新增代码+ResourceIdentityTest：结束窗口输入字典；如果没有这一行，Python 语法不完整。
        requested_resource_hint="1.txt",  # 新增代码+ResourceIdentityTest：提供用户请求的文件名；如果没有这一行，resource_matches_hint 无法验证。
    )  # 新增代码+ResourceIdentityTest：结束资源身份构建调用；如果没有这一行，Python 语法不完整。
    assert identity["available"] is True  # 新增代码+ResourceIdentityTest：确认文档类资源身份可用；如果没有这一行，Notepad 文件名证据可能缺失。
    assert identity["resource_matches_hint"] is True  # 新增代码+ResourceIdentityTest：确认标题匹配用户资源提示；如果没有这一行，文件名漂移无法被报告。
# 新增代码+ResourceIdentityTest：函数段结束，test_document_title_resource_identity_matches_hint 到此结束；如果没有这个边界说明，读者不容易看出资源匹配测试范围。
