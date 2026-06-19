"""测试通用 Computer Use FreshTarget 策略。"""  # 新增代码+FreshTargetPolicyTest：说明本文件验证通用新目标策略；如果没有这一行，读者不容易知道这些测试不是 Notepad 专用。
from __future__ import annotations  # 新增代码+FreshTargetPolicyTest：启用延迟类型注解；如果没有这一行，测试在旧解释路径下更容易遇到类型导入问题。

from typing import Any  # 新增代码+FreshTargetPolicyTest：导入 Any 表示窗口字典的动态字段；如果没有这一行，测试 helper 的输入类型不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.fresh_target_policy import (  # 新增代码+FreshTargetPolicyTest：导入被测 FreshTarget 策略；如果没有这一行，测试无法覆盖新硬门禁。
    classify_post_launch_target,  # 新增代码+FreshTargetPolicyTest：导入启动后分类函数；如果没有这一行，测试不能证明旧窗口绑定会被拒绝。
    decide_fresh_target_preflight,  # 新增代码+FreshTargetPolicyTest：导入启动前预检函数；如果没有这一行，测试不能证明已有窗口会先拦截。
    detect_existing_target_windows,  # 新增代码+FreshTargetPolicyTest：导入旧窗口检测函数；如果没有这一行，匹配逻辑可能无测试保护。
    window_fresh_identity_key,  # 新增代码+FreshTargetPolicyTest：导入窗口身份键函数；如果没有这一行，启动前后同窗判断无法被测试。
)  # 新增代码+FreshTargetPolicyTest：结束多行导入；如果没有这一行，Python 语法不完整。


def _window(app_id: str = "notepad.exe", pid: int = 501, hwnd: int = 601, title: str = "Untitled - Notepad") -> dict[str, Any]:  # 新增代码+FreshTargetPolicyTest：函数段开始，生成通用窗口样本；如果没有这段函数，每个测试会重复写易错窗口字典。
    return {  # 新增代码+FreshTargetPolicyTest：返回窗口事实字典；如果没有这一行，测试没有目标窗口输入。
        "app_id": app_id,  # 新增代码+FreshTargetPolicyTest：保存应用身份；如果没有这一行，策略无法匹配目标软件。
        "process_name": app_id,  # 新增代码+FreshTargetPolicyTest：保存进程名；如果没有这一行，真实 Win32 风格匹配无法覆盖。
        "pid": pid,  # 新增代码+FreshTargetPolicyTest：保存进程 id；如果没有这一行，旧窗口和新窗口无法区分。
        "hwnd": hwnd,  # 新增代码+FreshTargetPolicyTest：保存窗口句柄；如果没有这一行，身份键缺少窗口维度。
        "window_id": f"hwnd:{hwnd}",  # 新增代码+FreshTargetPolicyTest：保存协议窗口 id；如果没有这一行，target_ref 无法回指窗口。
        "title_preview": title,  # 新增代码+FreshTargetPolicyTest：保存可读标题摘要；如果没有这一行，标题类匹配和审计无法覆盖。
        "title": title,  # 新增代码+FreshTargetPolicyTest：保存完整标题；如果没有这一行，标题哈希无法生成。
    }  # 新增代码+FreshTargetPolicyTest：结束窗口字典；如果没有这一行，Python 语法不完整。
# 新增代码+FreshTargetPolicyTest：函数段结束，_window 到此结束；如果没有这个边界说明，用户不容易看出窗口夹具范围。


def test_preflight_blocks_existing_target_window_without_user_grant() -> None:  # 新增代码+FreshTargetPolicyTest：函数段开始，验证已有窗口默认阻断；如果没有这段测试，旧窗口可能再次被默认接管。
    decision = decide_fresh_target_preflight(  # 新增代码+FreshTargetPolicyTest：执行启动前预检；如果没有这一行，测试无法触发旧窗口门禁。
        "notepad",  # 新增代码+FreshTargetPolicyTest：请求打开 Notepad；如果没有这一行，预检没有目标应用。
        [_window()],  # 新增代码+FreshTargetPolicyTest：模拟 Notepad 已经打开；如果没有这一行，阻断场景不存在。
    )  # 新增代码+FreshTargetPolicyTest：结束预检调用；如果没有这一行，Python 语法不完整。
    assert decision["allowed"] is False  # 新增代码+FreshTargetPolicyTest：确认未授权旧窗口被阻断；如果没有这一行，危险放行不会被发现。
    assert decision["decision"] == "existing_target_window_requires_user_close_or_authorize"  # 新增代码+FreshTargetPolicyTest：确认拒绝 token 稳定；如果没有这一行，controller 无法可靠解释给用户。
    assert decision["requires_user_to_close_existing_app"] is True  # 新增代码+FreshTargetPolicyTest：确认提示用户关闭或授权；如果没有这一行，恢复路径会不明确。
    assert decision["low_level_event_count"] == 0  # 新增代码+FreshTargetPolicyTest：确认预检零桌面动作；如果没有这一行，安全预检可能自己触发副作用。
# 新增代码+FreshTargetPolicyTest：函数段结束，test_preflight_blocks_existing_target_window_without_user_grant 到此结束；如果没有这个边界说明，用户不容易看出拒绝范围。


def test_preflight_allows_explicit_user_granted_existing_window() -> None:  # 新增代码+FreshTargetPolicyTest：函数段开始，验证用户明确授权旧窗口可用；如果没有这段测试，合法单窗口应用流程可能被误拒。
    decision = decide_fresh_target_preflight(  # 新增代码+FreshTargetPolicyTest：执行启动前预检；如果没有这一行，授权路径没有事实来源。
        "wechat",  # 新增代码+FreshTargetPolicyTest：请求微信这类可能单实例应用；如果没有这一行，测试无法表达用户担心的应用类型。
        [_window(app_id="Weixin.exe", title="微信")],  # 新增代码+FreshTargetPolicyTest：模拟已有微信窗口；如果没有这一行，授权旧窗口场景不存在。
        explicit_existing_window_request=True,  # 新增代码+FreshTargetPolicyTest：声明用户明确要求已有窗口；如果没有这一行，策略应继续拒绝。
        user_authorized_window=True,  # 新增代码+FreshTargetPolicyTest：声明用户已经授权；如果没有这一行，旧窗口不能被合法接管。
    )  # 新增代码+FreshTargetPolicyTest：结束预检调用；如果没有这一行，Python 语法不完整。
    assert decision["allowed"] is True  # 新增代码+FreshTargetPolicyTest：确认明确授权旧窗口允许；如果没有这一行，用户授权能力不可用。
    assert decision["origin"] == "user_granted_existing_window"  # 新增代码+FreshTargetPolicyTest：确认来源记录为用户授权；如果没有这一行，审计会混淆自启动和授权旧窗口。
    assert decision["low_level_event_count"] == 0  # 新增代码+FreshTargetPolicyTest：确认授权判断本身零事件；如果没有这一行，预检可能触碰桌面。
# 新增代码+FreshTargetPolicyTest：函数段结束，test_preflight_allows_explicit_user_granted_existing_window 到此结束；如果没有这个边界说明，用户不容易看出授权范围。


def test_post_launch_rejects_target_window_that_existed_before_launch() -> None:  # 新增代码+FreshTargetPolicyTest：函数段开始，验证启动后旧窗口绑定会被拒绝；如果没有这段测试，预检漏网时仍会接管旧窗口。
    old_window = _window(pid=701, hwnd=801, title="Old user note - Notepad")  # 新增代码+FreshTargetPolicyTest：构造启动前已存在的 Notepad；如果没有这一行，旧窗口比较没有基准。
    decision = classify_post_launch_target(  # 新增代码+FreshTargetPolicyTest：执行启动后分类；如果没有这一行，测试不能覆盖绑定阶段。
        "notepad",  # 新增代码+FreshTargetPolicyTest：请求目标应用；如果没有这一行，分类无法按应用匹配。
        old_window,  # 新增代码+FreshTargetPolicyTest：模拟启动后绑定到同一个旧窗口；如果没有这一行，拒绝条件不会触发。
        [old_window],  # 新增代码+FreshTargetPolicyTest：传入启动前快照；如果没有这一行，策略无法知道窗口早已存在。
        {"process_started": False, "owned_process_registered": False},  # 新增代码+FreshTargetPolicyTest：声明没有新进程证据；如果没有这一行，策略可能误以为自启动成功。
    )  # 新增代码+FreshTargetPolicyTest：结束分类调用；如果没有这一行，Python 语法不完整。
    assert decision["allowed"] is False  # 新增代码+FreshTargetPolicyTest：确认旧窗口绑定被拒绝；如果没有这一行，错窗口风险不会被测试发现。
    assert decision["target_window_existed_before_launch"] is True  # 新增代码+FreshTargetPolicyTest：确认报告指出窗口启动前已存在；如果没有这一行，用户看不懂拒绝原因。
    assert decision["low_level_event_count"] == 0  # 新增代码+FreshTargetPolicyTest：确认启动后分类零输入事件；如果没有这一行，拒绝可能已经晚了。
# 新增代码+FreshTargetPolicyTest：函数段结束，test_post_launch_rejects_target_window_that_existed_before_launch 到此结束；如果没有这个边界说明，用户不容易看出启动后拒绝范围。


def test_post_launch_allows_unknown_app_when_no_preexisting_window_matches() -> None:  # 新增代码+FreshTargetPolicyTest：函数段开始，验证未知应用无旧窗口时不被卡死；如果没有这段测试，通用 Computer Use 会退化成白名单。
    target_window = _window(app_id="unknown-tool.exe", pid=901, hwnd=902, title="Unknown Tool")  # 新增代码+FreshTargetPolicyTest：构造未知应用新窗口；如果没有这一行，未知应用路径无法被覆盖。
    decision = classify_post_launch_target(  # 新增代码+FreshTargetPolicyTest：执行启动后分类；如果没有这一行，未知应用策略无测试。
        "unknown-tool",  # 新增代码+FreshTargetPolicyTest：请求未知应用；如果没有这一行，策略不会走未知分类。
        target_window,  # 新增代码+FreshTargetPolicyTest：传入启动后窗口；如果没有这一行，分类没有目标。
        [],  # 新增代码+FreshTargetPolicyTest：声明启动前没有旧窗口；如果没有这一行，测试不符合新窗口场景。
        {"process_started": True, "process_id": 901, "owned_process_registered": True},  # 新增代码+FreshTargetPolicyTest：提供 agent 自有进程证据；如果没有这一行，租约身份会缺少正向证明。
    )  # 新增代码+FreshTargetPolicyTest：结束分类调用；如果没有这一行，Python 语法不完整。
    assert decision["allowed"] is True  # 新增代码+FreshTargetPolicyTest：确认未知应用无旧窗口时允许进入通用租约；如果没有这一行，通用控制会被过度限制。
    assert decision["fresh_target_class"] == "fresh_agent_owned_window"  # 新增代码+FreshTargetPolicyTest：确认分类为 agent 自有新窗口；如果没有这一行，审计无法看懂为什么放行。
    assert decision["target_window_existed_before_launch"] is False  # 新增代码+FreshTargetPolicyTest：确认不是启动前旧窗口；如果没有这一行，压力测试缺少关键事实。
# 新增代码+FreshTargetPolicyTest：函数段结束，test_post_launch_allows_unknown_app_when_no_preexisting_window_matches 到此结束；如果没有这个边界说明，用户不容易看出未知应用范围。


def test_existing_target_detection_uses_stable_window_identity_key() -> None:  # 新增代码+FreshTargetPolicyTest：函数段开始，验证旧窗口检测和身份键稳定；如果没有这段测试，启动前后比较可能因字段变化失效。
    window = _window(app_id="Notepad.EXE", pid=111, hwnd=222, title="1.txt - Notepad")  # 新增代码+FreshTargetPolicyTest：构造大小写混合窗口；如果没有这一行，归一化能力无法覆盖。
    matches = detect_existing_target_windows("notepad.exe", [window])  # 新增代码+FreshTargetPolicyTest：按 exe 写法检测已有窗口；如果没有这一行，测试无法证明 exe 后缀兼容。
    key = window_fresh_identity_key(window)  # 新增代码+FreshTargetPolicyTest：生成窗口身份键；如果没有这一行，测试无法证明身份键非空。
    assert len(matches) == 1  # 新增代码+FreshTargetPolicyTest：确认目标旧窗口能被发现；如果没有这一行，预检可能漏掉大小写不同的应用。
    assert "notepad" in key  # 新增代码+FreshTargetPolicyTest：确认身份键包含归一化应用 token；如果没有这一行，调试身份键会很困难。
    assert "hwnd:222" in key  # 新增代码+FreshTargetPolicyTest：确认身份键包含窗口 id；如果没有这一行，同应用多窗口可能混淆。
# 新增代码+FreshTargetPolicyTest：函数段结束，test_existing_target_detection_uses_stable_window_identity_key 到此结束；如果没有这个边界说明，用户不容易看出身份键范围。
