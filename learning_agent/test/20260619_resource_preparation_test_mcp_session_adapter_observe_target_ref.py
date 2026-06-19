from types import SimpleNamespace  # 新增代码+ObserveTargetRefTest：导入简单对象模拟 controller 返回值；如果没有这一行，测试需要写额外样板类。

from learning_agent.computer_use_mcp_v2.windows_runtime import mcp_session_adapter as adapter_module  # 新增代码+TargetRefAutoInjectTest：导入 adapter 模块本体用于替换内部执行函数；如果没有这一行，测试无法抓到动作最终传给底层的参数。
from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter import ComputerUseMcpSessionCallbacks  # 新增代码+ExplicitTargetRefResourceFallbackTest：导入真实回调容器记录 adapter trace；如果没有这一行，测试无法证明显式 target_ref 是否在 adapter 层被解析。
from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter import ComputerUseMcpSessionAdapter  # 新增代码+TargetRefAutoInjectTest：导入真实 MCP 会话适配器；如果没有这一行，测试只能测 helper 而不能覆盖真实动作路径。
from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter import ComputerUseMcpSessionState  # 新增代码+TargetRefAutoInjectTest：导入真实会话状态对象；如果没有这一行，测试无法模拟 observe 后复用窗口的状态。
from learning_agent.computer_use_mcp_v2.windows_runtime.target_registry import ComputerUseTargetRegistry  # 新增代码+TargetRefAutoInjectTest：导入真实 target 注册表；如果没有这一行，测试会用假实现而不是验证现有单目标隐式解析合同。

from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter import _resolve_default_observation_window  # 新增代码+ObserveTargetRefTest：导入默认观察窗口解析函数；如果没有这一行，测试无法约束 observe 优先使用 active target_ref。


class _FakeTargetRegistry:  # 新增代码+ObserveTargetRefTest：类段开始，模拟已注册的一对一目标窗口；如果没有这个类，测试无法复现 launch_app 后 registry 已有 target_ref 的状态。
    def get_active_target(self) -> dict:  # 新增代码+ObserveTargetRefTest：函数段开始，返回当前 active target；如果没有这段函数，adapter 无法从 fake registry 读取目标。
        return {  # 新增代码+ObserveTargetRefTest：返回 registry 公开目标记录；如果没有这一行，测试没有 active target 输入。
            "target_ref": "cu-target-test-0001",  # 新增代码+ObserveTargetRefTest：保存一对一窗口 ID；如果没有这一行，观察结果无法携带后续动作所需 target_ref。
            "window": {  # 新增代码+ObserveTargetRefTest：保存已注册目标窗口；如果没有这一行，adapter 没有可注入的 window。
                "app_id": "notepad.exe",  # 新增代码+ObserveTargetRefTest：声明目标应用是 Notepad；如果没有这一行，测试无法区分目标窗口和前台终端窗口。
                "process_name": "notepad.exe",  # 新增代码+ObserveTargetRefTest：保存进程名；如果没有这一行，窗口身份不完整。
                "pid": 222,  # 新增代码+ObserveTargetRefTest：保存真实窗口 pid；如果没有这一行，动作前租约验证缺少进程证据。
                "hwnd": 333,  # 新增代码+ObserveTargetRefTest：保存真实窗口 hwnd；如果没有这一行，窗口一对一绑定缺少句柄证据。
                "window_id": "hwnd:333",  # 新增代码+ObserveTargetRefTest：保存协议窗口 id；如果没有这一行，target_ref 无法回指窗口。
                "title_preview": "Untitled - Notepad",  # 新增代码+ObserveTargetRefTest：保存用户可读标题；如果没有这一行，失败时看不出目标窗口。
            },  # 新增代码+ObserveTargetRefTest：结束窗口字典；如果没有这一行，Python 语法不完整。
            "lease": {"origin": "agent_owned_launch"},  # 新增代码+ObserveTargetRefTest：保存租约摘要；如果没有这一行，后续观察窗口不能携带权限来源证据。
        }  # 新增代码+ObserveTargetRefTest：结束 active target 字典；如果没有这一行，Python 语法不完整。
    # 新增代码+ObserveTargetRefTest：函数段结束，_FakeTargetRegistry.get_active_target 到此结束；如果没有这个边界说明，用户不容易看出 fake registry 范围。
# 新增代码+ObserveTargetRefTest：类段结束，_FakeTargetRegistry 到此结束；如果没有这个边界说明，用户不容易看出 fake registry 结构。


class _FakeController:  # 新增代码+ObserveTargetRefTest：类段开始，模拟桌面 controller；如果没有这个类，测试无法证明前台窗口不应覆盖 active target。
    def __init__(self) -> None:  # 新增代码+ObserveTargetRefTest：函数段开始，初始化 fake controller；如果没有这段函数，测试无法保存 observe 调用次数。
        self.target_registry = _FakeTargetRegistry()  # 新增代码+ObserveTargetRefTest：挂载 fake target registry；如果没有这一行，adapter 无法读取 active target。
        self.observe_calls: list[dict] = []  # 新增代码+ObserveTargetRefTest：记录 observe 是否被调用；如果没有这一行，测试无法断言 registry 优先级。
    # 新增代码+ObserveTargetRefTest：函数段结束，_FakeController.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def observe(self, arguments: dict) -> SimpleNamespace:  # 新增代码+ObserveTargetRefTest：函数段开始，模拟前台活动窗口观察；如果没有这段函数，旧实现无法运行到失败点。
        self.observe_calls.append(arguments)  # 新增代码+ObserveTargetRefTest：记录观察调用；如果没有这一行，测试无法证明是否错误读取前台窗口。
        return SimpleNamespace(data={"window": {"app_id": "cmd.exe", "pid": 999, "hwnd": 888, "window_id": "hwnd:888", "title_preview": "cmd"}})  # 新增代码+ObserveTargetRefTest：返回前台终端窗口；如果没有这一行，旧实现不会暴露“观察跑到终端”的问题。
    # 新增代码+ObserveTargetRefTest：函数段结束，_FakeController.observe 到此结束；如果没有这个边界说明，用户不容易看出 fake observe 范围。
# 新增代码+ObserveTargetRefTest：类段结束，_FakeController 到此结束；如果没有这个边界说明，用户不容易看出 fake controller 结构。


def test_observe_default_window_prefers_active_target_ref_over_foreground_terminal() -> None:  # 新增代码+ObserveTargetRefTest：函数段开始，验证 observe 默认窗口优先使用 registry active target；如果没有这段测试，真实终端验收会被前台 cmd 带偏。
    controller = _FakeController()  # 新增代码+ObserveTargetRefTest：创建 fake controller；如果没有这一行，测试没有被测 controller。
    window = _resolve_default_observation_window(controller, "after launch")  # 新增代码+ObserveTargetRefTest：解析默认观察窗口；如果没有这一行，测试不会触发 adapter 逻辑。
    assert window["target_ref"] == "cu-target-test-0001"  # 新增代码+ObserveTargetRefTest：确认观察窗口携带 target_ref；如果没有这一行，后续动作仍可能漏写目标 ID。
    assert window["app_id"] == "notepad.exe"  # 新增代码+ObserveTargetRefTest：确认返回已注册目标而不是前台终端；如果没有这一行，observe 可能继续看错窗口。
    assert controller.observe_calls == []  # 新增代码+ObserveTargetRefTest：确认 registry 命中时无需读取前台窗口；如果没有这一行，前台 cmd 仍可能污染观察上下文。
# 新增代码+ObserveTargetRefTest：函数段结束，test_observe_default_window_prefers_active_target_ref_over_foreground_terminal 到此结束；如果没有这个边界说明，用户不容易看出 observe target_ref 回归范围。


class _RegistryBackedController:  # 新增代码+TargetRefAutoInjectTest：类段开始，使用真实 registry 模拟已由 launch_app 绑定的新窗口；如果没有这个类，测试无法复现真实验收里的 active target 状态。
    def __init__(self) -> None:  # 新增代码+TargetRefAutoInjectTest：函数段开始，初始化 controller 测试替身；如果没有这段函数，registry 和窗口事实没有容器。
        self.target_registry = ComputerUseTargetRegistry("target-ref-auto-inject-test")  # 新增代码+TargetRefAutoInjectTest：创建真实目标注册表；如果没有这一行，单目标隐式解析能力不会被真实验证。
        self.window = {  # 新增代码+TargetRefAutoInjectTest：准备一个可被键鼠动作复用的目标窗口；如果没有这一行，adapter 没有 last_observed_window 可注入。
            "app_id": "notepad.exe",  # 新增代码+TargetRefAutoInjectTest：声明目标应用身份；如果没有这一行，registry 无法保存应用摘要。
            "process_name": "notepad.exe",  # 新增代码+TargetRefAutoInjectTest：声明目标进程名；如果没有这一行，窗口身份缺少真实进程线索。
            "pid": 34500,  # 新增代码+TargetRefAutoInjectTest：模拟真实窗口 pid；如果没有这一行，窗口事实与验收日志里的 pid 场景不一致。
            "hwnd": 4329584,  # 新增代码+TargetRefAutoInjectTest：模拟真实窗口句柄；如果没有这一行，一对一窗口身份缺少 hwnd。
            "window_id": "hwnd:4329584",  # 新增代码+TargetRefAutoInjectTest：提供协议化窗口 ID；如果没有这一行，registry 无法稳定回指窗口。
            "title_preview": "Untitled - Notepad",  # 新增代码+TargetRefAutoInjectTest：模拟新空白窗口标题；如果没有这一行，失败时看不出被测窗口。
        }  # 新增代码+TargetRefAutoInjectTest：窗口字典结束；如果没有这一行，Python 语法不完整。
        self.target_ref = self.target_registry.register_target(self.window, source_action="launch_app", lease={"origin": "agent_owned_launch"})  # 新增代码+TargetRefAutoInjectTest：注册目标并保存真实 target_ref；如果没有这一行，adapter 无法从 registry 解析单 active target。
    # 新增代码+TargetRefAutoInjectTest：函数段结束，_RegistryBackedController.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake controller 初始化范围。
# 新增代码+TargetRefAutoInjectTest：类段结束，_RegistryBackedController 到此结束；如果没有这个边界说明，用户不容易看出 fake controller 范围。


def test_action_reuses_single_active_target_ref_when_model_omits_it(monkeypatch) -> None:  # 新增代码+TargetRefAutoInjectTest：函数段开始，验证单 active target 时动作自动补 target_ref；如果没有这段测试，真实 agent 仍会在 key/click 时因漏传 target_ref 卡死。
    controller = _RegistryBackedController()  # 新增代码+TargetRefAutoInjectTest：创建带真实 registry 的 controller；如果没有这一行，测试没有单 active target 事实源。
    captured_arguments: dict = {}  # 新增代码+TargetRefAutoInjectTest：保存底层执行收到的参数；如果没有这一行，测试无法证明 target_ref 是否真的传到底层。

    def _fake_internal_execute_desktop_action(arguments, *_args, **_kwargs):  # 新增代码+TargetRefAutoInjectTest：函数段开始，替换真实桌面执行避免触碰本机窗口；如果没有这段函数，单元测试会变成真实键鼠动作。
        captured_arguments.update(dict(arguments))  # 新增代码+TargetRefAutoInjectTest：记录 adapter 最终生成的旧 controller 参数；如果没有这一行，断言没有对象可检查。
        return '{"ok": true, "message": "captured", "data": {}}'  # 新增代码+TargetRefAutoInjectTest：返回结构化成功文本给 adapter 包装；如果没有这一行，测试会因 fake 函数无返回而失败。
    # 新增代码+TargetRefAutoInjectTest：函数段结束，_fake_internal_execute_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出 fake 执行范围。

    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_execute_desktop_action", _fake_internal_execute_desktop_action)  # 新增代码+TargetRefAutoInjectTest：只替换最底层执行函数；如果没有这一行，测试会调用真实桌面动作。
    state = ComputerUseMcpSessionState(last_observed_window=dict(controller.window))  # 新增代码+TargetRefAutoInjectTest：模拟 observe 已经保存窗口但模型下一步漏写 target_ref；如果没有这一行，adapter 不会进入窗口复用路径。
    adapter = ComputerUseMcpSessionAdapter(controller=controller, state=state)  # 新增代码+TargetRefAutoInjectTest：构造真实会话适配器；如果没有这一行，测试不会覆盖生产调用路径。
    result = adapter.call_atomic_tool("key", {"key": "CTRL+S", "reason": "save active document"})  # 新增代码+TargetRefAutoInjectTest：模拟模型调用按键却没有传 target_ref；如果没有这一行，缺口不会被触发。

    assert result["ok"] is True  # 新增代码+TargetRefAutoInjectTest：确认 fake 执行路径本身成功；如果没有这一行，后续参数断言可能掩盖包装失败。
    assert captured_arguments["target_ref"] == controller.target_ref  # 新增代码+TargetRefAutoInjectTest：确认 adapter 自动补上唯一 active target_ref；如果没有这一行，真实验收会继续出现 target_ref_required_for_bound_window_action。
    assert captured_arguments["window"]["window_id"] == controller.window["window_id"]  # 新增代码+TargetRefAutoInjectTest：确认动作仍绑定同一个窗口；如果没有这一行，target_ref 可能和 window 漂移。
# 新增代码+TargetRefAutoInjectTest：函数段结束，test_action_reuses_single_active_target_ref_when_model_omits_it 到此结束；如果没有这个边界说明，用户不容易看出 target_ref 自动注入回归范围。


class _RestoredResourceController(_RegistryBackedController):  # 新增代码+ResourceFreshnessAdapterTest：类段开始，模拟 launch 后窗口恢复到旧文档；如果没有这个类，测试无法复现真实验收里的旧标题恢复场景。
    def __init__(self) -> None:  # 新增代码+ResourceFreshnessAdapterTest：函数段开始，初始化旧资源窗口控制器；如果没有这段函数，测试没有旧文档窗口事实。
        super().__init__()  # 新增代码+ResourceFreshnessAdapterTest：复用真实 registry 绑定逻辑；如果没有这一行，旧资源测试不会覆盖 active target。
        self.window["title_preview"] = "2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad"  # 新增代码+ResourceFreshnessAdapterTest：把窗口标题改成恢复旧文档；如果没有这一行，资源新鲜度风险不会触发。
        self.target_registry.clear()  # 新增代码+ResourceFreshnessAdapterTest：清掉父类注册的新空白窗口记录；如果没有这一行，registry 里仍保存旧标题修改前的记录。
        self.target_ref = self.target_registry.register_target(self.window, source_action="launch_app", lease={"origin": "agent_owned_launch"})  # 新增代码+ResourceFreshnessAdapterTest：重新注册旧标题窗口；如果没有这一行，adapter 从 registry 取不到恢复后的标题。
    # 新增代码+ResourceFreshnessAdapterTest：函数段结束，_RestoredResourceController.__init__ 到此结束；如果没有这个边界说明，用户不容易看出旧资源初始化范围。
# 新增代码+ResourceFreshnessAdapterTest：类段结束，_RestoredResourceController 到此结束；如果没有这个边界说明，用户不容易看出旧资源 fake 范围。


def test_action_is_blocked_after_observe_detects_restored_document_resource(monkeypatch) -> None:  # 新增代码+ResourceFreshnessAdapterTest：函数段开始，验证旧资源观察后后续写动作被零事件阻断；如果没有这段测试，agent 可能继续把用户内容写进旧文档。
    controller = _RestoredResourceController()  # 新增代码+ResourceFreshnessAdapterTest：创建恢复旧文档的 controller；如果没有这一行，测试没有旧资源事实源。
    executed_actions: list[dict] = []  # 新增代码+ResourceFreshnessAdapterTest：保存底层执行尝试；如果没有这一行，测试无法证明阻断是零低层事件。

    def _fake_internal_observe_desktop(arguments, *_args, **_kwargs):  # 新增代码+ResourceFreshnessAdapterTest：函数段开始，替换真实观察避免截图触碰本机窗口；如果没有这段函数，单元测试会依赖真实桌面状态。
        return '{"ok": true, "message": "observed", "data": {"state": {"window": {}}}}'  # 新增代码+ResourceFreshnessAdapterTest：返回结构化成功观察；如果没有这一行，adapter 不会保存 last_observed_window。
    # 新增代码+ResourceFreshnessAdapterTest：函数段结束，_fake_internal_observe_desktop 到此结束；如果没有这个边界说明，用户不容易看出 fake observe 范围。

    def _fake_internal_execute_desktop_action(arguments, *_args, **_kwargs):  # 新增代码+ResourceFreshnessAdapterTest：函数段开始，替换真实键鼠执行；如果没有这段函数，测试可能真的输入文字。
        executed_actions.append(dict(arguments))  # 新增代码+ResourceFreshnessAdapterTest：记录任何穿透阻断的动作；如果没有这一行，零事件断言没有数据来源。
        return '{"ok": true, "message": "executed", "data": {}}'  # 新增代码+ResourceFreshnessAdapterTest：返回成功文本；如果没有这一行，穿透时 adapter 包装会失败。
    # 新增代码+ResourceFreshnessAdapterTest：函数段结束，_fake_internal_execute_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出 fake action 范围。

    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_observe_desktop", _fake_internal_observe_desktop)  # 新增代码+ResourceFreshnessAdapterTest：只替换底层 observe；如果没有这一行，测试会读取真实屏幕。
    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_execute_desktop_action", _fake_internal_execute_desktop_action)  # 新增代码+ResourceFreshnessAdapterTest：只替换底层 action；如果没有这一行，测试会触发真实键鼠。
    adapter = ComputerUseMcpSessionAdapter(controller=controller)  # 新增代码+ResourceFreshnessAdapterTest：构造真实 adapter；如果没有这一行，测试不会覆盖生产路径。
    adapter.call_atomic_tool("observe", {"reason": "请打开本地真实记事本，输入 hello everyone，并保存到桌面 1.txt"})  # 新增代码+ResourceFreshnessAdapterTest：模拟观察阶段携带用户要保存的新文件名；如果没有这一行，adapter 没有资源新鲜度上下文。
    result = adapter.call_atomic_tool("type", {"text": "hello everyone", "reason": "输入用户要求的内容"})  # 新增代码+ResourceFreshnessAdapterTest：模拟后续写入动作；如果没有这一行，旧资源阻断不会被验证。

    assert result["ok"] is False  # 新增代码+ResourceFreshnessAdapterTest：确认旧资源写动作被拒绝；如果没有这一行，测试无法防止写进旧文档。
    assert executed_actions == []  # 新增代码+ResourceFreshnessAdapterTest：确认没有任何底层键鼠动作穿透；如果没有这一行，安全阻断可能只是事后失败。
    assert "OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED" in result["payload"]["legacy_text"]  # 新增代码+ResourceFreshnessAdapterTest：确认返回稳定资源阻断 marker；如果没有这一行，收敛层无法停止重复尝试。
# 新增代码+ResourceFreshnessAdapterTest：函数段结束，test_action_is_blocked_after_observe_detects_restored_document_resource 到此结束；如果没有这个边界说明，用户不容易看出资源阻断回归范围。


def test_action_blocks_restored_document_resource_when_observe_state_is_missing(monkeypatch) -> None:  # 新增代码+ResourceFreshnessActionFallbackTest：函数段开始，验证 observe 没留下资源状态时 action 入口也要拦旧资源；如果没有这段测试，真实验收里新进程恢复旧文档会直接穿透到键鼠动作。
    controller = _RestoredResourceController()  # 新增代码+ResourceFreshnessActionFallbackTest：创建一对一绑定但标题是旧文档的 controller；如果没有这一行，测试没有“新窗口恢复旧资源”的事实。
    executed_actions: list[dict] = []  # 新增代码+ResourceFreshnessActionFallbackTest：记录任何进入底层执行的动作；如果没有这一行，测试无法证明阻断发生在真实键鼠前。

    def _fake_internal_execute_desktop_action(arguments, *_args, **_kwargs):  # 新增代码+ResourceFreshnessActionFallbackTest：函数段开始，替换真实桌面动作；如果没有这段函数，单元测试可能真的按键到用户桌面。
        executed_actions.append(dict(arguments))  # 新增代码+ResourceFreshnessActionFallbackTest：保存穿透动作参数；如果没有这一行，失败时看不到 adapter 是否已经越过门禁。
        return '{"ok": true, "message": "executed", "data": {}}'  # 新增代码+ResourceFreshnessActionFallbackTest：返回成功文本模拟旧执行链；如果没有这一行，穿透路径不能被 adapter 正常包装。
    # 新增代码+ResourceFreshnessActionFallbackTest：函数段结束，_fake_internal_execute_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出 fake 执行范围。

    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_execute_desktop_action", _fake_internal_execute_desktop_action)  # 新增代码+ResourceFreshnessActionFallbackTest：只替换底层动作函数；如果没有这一行，测试会触碰真实窗口。
    state = ComputerUseMcpSessionState(last_observed_window=dict(controller.window))  # 新增代码+ResourceFreshnessActionFallbackTest：模拟 observe 只留下窗口但没有留下 resource_freshness；如果没有这一行，无法复现这次验收日志里的缺口。
    adapter = ComputerUseMcpSessionAdapter(controller=controller, state=state)  # 新增代码+ResourceFreshnessActionFallbackTest：构造真实 adapter 入口；如果没有这一行，测试不会覆盖生产 action gate。
    result = adapter.call_atomic_tool("key", {"key": "CTRL+A", "reason": "选择当前窗口内容，准备输入新内容"})  # 新增代码+ResourceFreshnessActionFallbackTest：模拟模型下一步按键但没有资源新鲜度状态；如果没有这一行，缺口不会被触发。

    assert result["ok"] is False  # 新增代码+ResourceFreshnessActionFallbackTest：确认旧资源窗口被 action 前置门禁拒绝；如果没有这一行，测试无法阻止继续写入旧文档。
    assert executed_actions == []  # 新增代码+ResourceFreshnessActionFallbackTest：确认没有任何底层键鼠动作；如果没有这一行，安全拒绝可能已经太晚。
    assert "OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED" in result["payload"]["legacy_text"]  # 新增代码+ResourceFreshnessActionFallbackTest：确认返回可收敛的资源用户动作 marker；如果没有这一行，模型可能继续反复尝试按键。
# 新增代码+ResourceFreshnessActionFallbackTest：函数段结束，test_action_blocks_restored_document_resource_when_observe_state_is_missing 到此结束；如果没有这个边界说明，用户不容易看出 action 兜底阻断范围。


def test_action_blocks_restored_document_resource_when_explicit_target_ref_has_no_window(monkeypatch) -> None:  # 新增代码+ExplicitTargetRefResourceFallbackTest：函数段开始，验证模型只传 target_ref 不传 window 时也要先解析窗口再拦旧资源；如果没有这段测试，真实验收会在底层解析窗口后才发现旧文档，已经太晚。
    controller = _RestoredResourceController()  # 新增代码+ExplicitTargetRefResourceFallbackTest：创建 registry 中已绑定旧文档窗口的 controller；如果没有这一行，测试没有显式 target_ref 对应窗口事实。
    executed_actions: list[dict] = []  # 新增代码+ExplicitTargetRefResourceFallbackTest：记录是否有动作穿透到底层；如果没有这一行，测试不能证明零事件阻断。

    def _fake_internal_execute_desktop_action(arguments, *_args, **_kwargs):  # 新增代码+ExplicitTargetRefResourceFallbackTest：函数段开始，替换真实桌面动作；如果没有这段函数，单测可能真的操作本机窗口。
        executed_actions.append(dict(arguments))  # 新增代码+ExplicitTargetRefResourceFallbackTest：保存穿透参数；如果没有这一行，失败时无法定位 adapter 是否提前阻断。
        return '{"ok": true, "message": "executed", "data": {}}'  # 新增代码+ExplicitTargetRefResourceFallbackTest：返回 fake 成功；如果没有这一行，穿透路径无法形成可断言结果。
    # 新增代码+ExplicitTargetRefResourceFallbackTest：函数段结束，_fake_internal_execute_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出 fake 执行范围。

    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_execute_desktop_action", _fake_internal_execute_desktop_action)  # 新增代码+ExplicitTargetRefResourceFallbackTest：替换底层执行函数；如果没有这一行，测试会触碰真实桌面。
    adapter = ComputerUseMcpSessionAdapter(controller=controller)  # 新增代码+ExplicitTargetRefResourceFallbackTest：构造真实 adapter；如果没有这一行，测试不会覆盖生产 action 入口。
    result = adapter.call_atomic_tool("key", {"key": "CTRL+A", "target_ref": controller.target_ref, "reason": "在已绑定的一对一真实记事本窗口中全选当前内容"})  # 新增代码+ExplicitTargetRefResourceFallbackTest：模拟真实失败里模型只传 target_ref 的按键动作；如果没有这一行，显式 ref 缺 window 缺口不会触发。

    assert result["ok"] is False  # 新增代码+ExplicitTargetRefResourceFallbackTest：确认旧资源窗口被 adapter 提前拒绝；如果没有这一行，测试无法防止底层真实按键。
    assert executed_actions == []  # 新增代码+ExplicitTargetRefResourceFallbackTest：确认没有穿透到底层执行；如果没有这一行，安全拒绝可能发生得太晚。
    assert "OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED" in result["payload"]["legacy_text"]  # 新增代码+ExplicitTargetRefResourceFallbackTest：确认收敛 marker 出现在工具结果里；如果没有这一行，模型可能继续重试。
# 新增代码+ExplicitTargetRefResourceFallbackTest：函数段结束，test_action_blocks_restored_document_resource_when_explicit_target_ref_has_no_window 到此结束；如果没有这个边界说明，用户不容易看出显式 target_ref 资源门禁范围。


def test_observe_actual_window_title_replaces_launch_snapshot_before_action_resource_gate(monkeypatch) -> None:  # 新增代码+ObservedWindowRefreshResourceGateTest：函数段开始，验证 observe 返回的真实窗口标题会替换启动时快照；如果没有这段测试，Notepad 启动后延迟恢复旧文档会绕过资源门禁。
    controller = _RegistryBackedController()  # 新增代码+ObservedWindowRefreshResourceGateTest：创建启动时标题为 Notepad 的单目标 controller；如果没有这一行，测试没有 registry 旧快照输入。
    restored_window = dict(controller.window)  # 新增代码+ObservedWindowRefreshResourceGateTest：复制启动窗口并模拟 observe 后的真实窗口；如果没有这一行，不能表达“同一 hwnd 标题变了”的场景。
    restored_window["title_preview"] = "*2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad"  # 新增代码+ObservedWindowRefreshResourceGateTest：把真实观察标题改成恢复旧文档；如果没有这一行，资源门禁没有旧资源证据。
    executed_actions: list[dict] = []  # 新增代码+ObservedWindowRefreshResourceGateTest：记录是否有动作穿透到底层；如果没有这一行，测试不能证明零事件阻断。

    def _fake_internal_observe_desktop(arguments, *_args, **_kwargs):  # 新增代码+ObservedWindowRefreshResourceGateTest：函数段开始，替换真实 observe 返回标题已变化的窗口；如果没有这段函数，单测会依赖真实桌面。
        observed_payload = {"action": "get_window_state", "state": {"window": restored_window}}  # 新增代码+ObservedWindowRefreshResourceGateTest：构造旧 observe 文本里的数据字典；如果没有这一行，adapter 没有可解析的真实窗口事实。
        return "mcp__computer-use__observe 成功：Windows 只读窗口状态已返回。\n数据：" + repr(observed_payload) + "\nComputer Use Image Results\n- image_result_count=0"  # 新增代码+ObservedWindowRefreshResourceGateTest：返回生产格式的 legacy 文本；如果没有这一行，测试无法覆盖真实日志里的“数据：{...}”解析路径。
    # 新增代码+ObservedWindowRefreshResourceGateTest：函数段结束，_fake_internal_observe_desktop 到此结束；如果没有这个边界说明，用户不容易看出 fake observe 范围。

    def _fake_internal_execute_desktop_action(arguments, *_args, **_kwargs):  # 新增代码+ObservedWindowRefreshResourceGateTest：函数段开始，替换真实键盘动作；如果没有这段函数，单测会真的按键。
        executed_actions.append(dict(arguments))  # 新增代码+ObservedWindowRefreshResourceGateTest：保存穿透动作；如果没有这一行，失败时无法判断门禁是否失效。
        return '{"ok": true, "message": "executed", "data": {}}'  # 新增代码+ObservedWindowRefreshResourceGateTest：返回 fake 成功；如果没有这一行，穿透路径不能被 adapter 包装。
    # 新增代码+ObservedWindowRefreshResourceGateTest：函数段结束，_fake_internal_execute_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出 fake action 范围。

    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_observe_desktop", _fake_internal_observe_desktop)  # 新增代码+ObservedWindowRefreshResourceGateTest：替换底层 observe；如果没有这一行，测试会读取真实屏幕。
    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_execute_desktop_action", _fake_internal_execute_desktop_action)  # 新增代码+ObservedWindowRefreshResourceGateTest：替换底层 action；如果没有这一行，测试会触碰真实窗口。
    adapter = ComputerUseMcpSessionAdapter(controller=controller)  # 新增代码+ObservedWindowRefreshResourceGateTest：构造真实 adapter；如果没有这一行，测试不会覆盖生产状态同步路径。
    adapter.call_atomic_tool("observe", {"reason": "确认当前桌面状态，看看 Notepad 是否已经可见"})  # 新增代码+ObservedWindowRefreshResourceGateTest：模拟模型观察但 reason 未携带 1.txt；如果没有这一行，无法复现真实验收里 observe 报告掩盖 action 兜底的问题。
    result = adapter.call_atomic_tool("key", {"key": "ALT+TAB", "reason": "切换窗口以确认 Notepad 是否在前台"})  # 新增代码+ObservedWindowRefreshResourceGateTest：模拟下一步系统键动作；如果没有这一行，旧资源 action 兜底不会被验证。

    assert adapter.state.last_observed_window["title_preview"].startswith("*2026-06-18")  # 新增代码+ObservedWindowRefreshResourceGateTest：确认 adapter 保存的是 observe 真实标题而不是启动快照；如果没有这一行，测试可能错过根因。
    assert result["ok"] is False  # 新增代码+ObservedWindowRefreshResourceGateTest：确认旧资源窗口的后续动作被拒绝；如果没有这一行，测试无法防止按键穿透。
    assert executed_actions == []  # 新增代码+ObservedWindowRefreshResourceGateTest：确认没有任何底层按键执行；如果没有这一行，安全拒绝可能太晚。
    assert "OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED" in result["payload"]["legacy_text"]  # 新增代码+ObservedWindowRefreshResourceGateTest：确认返回资源用户动作 marker；如果没有这一行，模型仍可能继续重试。
# 新增代码+ObservedWindowRefreshResourceGateTest：函数段结束，test_observe_actual_window_title_replaces_launch_snapshot_before_action_resource_gate 到此结束；如果没有这个边界说明，用户不容易看出 observe 刷新窗口回归范围。


def test_safe_new_blank_shortcut_runs_on_restored_resource_then_blocks_typing_until_observe(monkeypatch) -> None:  # 新增代码+ResourcePreparationTest：函数段开始，验证旧资源窗口里只允许明确新建空白资源动作，且新建后必须先观察；如果没有这段测试，修复可能放开直接输入旧文档的风险。
    controller = _RestoredResourceController()  # 新增代码+ResourcePreparationTest：创建恢复旧文档的目标窗口；如果没有这一行，测试没有旧资源恢复事实。
    executed_actions: list[dict] = []  # 新增代码+ResourcePreparationTest：记录底层动作调用；如果没有这一行，无法证明只有 Ctrl+N 通过、文本输入被挡住。

    def _fake_internal_execute_desktop_action(arguments, *_args, **_kwargs):  # 新增代码+ResourcePreparationTest：函数段开始，替换真实桌面动作避免碰用户电脑；如果没有这段函数，单测会真的按键。
        executed_actions.append(dict(arguments))  # 新增代码+ResourcePreparationTest：保存穿过 adapter 的动作参数；如果没有这一行，断言看不到真实门禁效果。
        return '{"ok": true, "message": "executed", "data": {}}'  # 新增代码+ResourcePreparationTest：返回 fake 成功文本；如果没有这一行，允许动作路径无法被包装为成功结果。
    # 新增代码+ResourcePreparationTest：函数段结束，_fake_internal_execute_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出 fake 执行范围。

    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_execute_desktop_action", _fake_internal_execute_desktop_action)  # 新增代码+ResourcePreparationTest：替换底层执行函数；如果没有这一行，测试会触发真实键鼠。
    blocked_resource_freshness = {  # 新增代码+ResourcePreparationTest：准备旧资源阻断状态；如果没有这一行，Ctrl+N 场景不会复现当前真实失败。
        "allowed": False,  # 新增代码+ResourcePreparationTest：声明当前资源不可直接编辑；如果没有这一行，adapter 会误以为可以继续输入。
        "decision": "restored_existing_resource_requires_new_blank_or_authorization",  # 新增代码+ResourcePreparationTest：声明旧资源恢复决策；如果没有这一行，测试不覆盖 ResourceFreshness 硬门禁。
        "document_like": True,  # 新增代码+ResourcePreparationTest：声明目标应用承载文档资源；如果没有这一行，通用资源准备逻辑不会启用。
        "title_preview": controller.window["title_preview"],  # 新增代码+ResourcePreparationTest：保存旧文档标题证据；如果没有这一行，失败结果缺少可读上下文。
        "app_id": "notepad.exe",  # 新增代码+ResourcePreparationTest：保存目标应用身份；如果没有这一行，报告缺少应用线索。
        "process_name": "notepad.exe",  # 新增代码+ResourcePreparationTest：保存目标进程身份；如果没有这一行，资源判断缺少进程线索。
        "low_level_event_count": 0,  # 新增代码+ResourcePreparationTest：声明阻断状态本身没有底层事件；如果没有这一行，验收无法证明安全边界。
    }  # 新增代码+ResourcePreparationTest：旧资源状态字典结束；如果没有这一行，Python 语法不完整。
    state = ComputerUseMcpSessionState(last_observed_window=dict(controller.window), last_resource_freshness=blocked_resource_freshness)  # 新增代码+ResourcePreparationTest：模拟 observe 已发现旧文档；如果没有这一行，动作入口不会处在真实失败状态。
    adapter = ComputerUseMcpSessionAdapter(controller=controller, state=state)  # 新增代码+ResourcePreparationTest：构造真实 adapter；如果没有这一行，测试不会覆盖生产动作路径。
    new_result = adapter.call_atomic_tool("key", {"key": "CTRL+N", "reason": "新建空白文档，避免写入旧资源"})  # 新增代码+ResourcePreparationTest：模拟模型执行通用新建空白资源快捷键；如果没有这一行，缺陷不会被触发。
    type_result = adapter.call_atomic_tool("type", {"text": "hello everyone", "reason": "输入用户要求的新内容"})  # 新增代码+ResourcePreparationTest：模拟模型没有重新观察就直接输入；如果没有这一行，观察确认门禁不会被验证。

    assert new_result["ok"] is True  # 新增代码+ResourcePreparationTest：确认明确新建空白资源动作可以通过；如果没有这一行，Ctrl+N 仍会被旧资源门禁误挡。
    assert len(executed_actions) == 1  # 新增代码+ResourcePreparationTest：确认只有 Ctrl+N 穿过底层执行；如果没有这一行，文本输入可能已经污染旧文档。
    assert executed_actions[0]["key"] == "CTRL+N"  # 新增代码+ResourcePreparationTest：确认通过的是新建空白快捷键；如果没有这一行，测试可能误放行其他危险按键。
    assert type_result["ok"] is False  # 新增代码+ResourcePreparationTest：确认未 observe 前输入仍被拒绝；如果没有这一行，准备动作后会形成直接写入风险。
    assert type_result["error_class"] == "desktop_resource_preparation_observe_required"  # 新增代码+ResourcePreparationTest：确认拒绝原因是等待空白资源观察确认；如果没有这一行，模型无法知道下一步应 observe。
# 新增代码+ResourcePreparationTest：函数段结束，test_safe_new_blank_shortcut_runs_on_restored_resource_then_blocks_typing_until_observe 到此结束；如果没有这个边界说明，用户不容易看出准备动作门禁范围。


def test_typing_after_safe_new_blank_shortcut_is_allowed_after_observe_confirms_blank_resource(monkeypatch) -> None:  # 新增代码+ResourcePreparationTest：函数段开始，验证新建空白资源并观察确认后才允许输入；如果没有这段测试，修复可能卡在永远不能继续编辑。
    controller = _RestoredResourceController()  # 新增代码+ResourcePreparationTest：创建旧资源窗口控制器；如果没有这一行，测试没有从旧资源切到新空白的起点。
    blank_window = dict(controller.window)  # 新增代码+ResourcePreparationTest：复制同一个目标窗口事实；如果没有这一行，无法模拟同一 hwnd 标题变成空白资源。
    blank_window["title_preview"] = "Untitled - Notepad"  # 新增代码+ResourcePreparationTest：把观察后的标题改成空白文档；如果没有这一行，ResourceFreshness 不会确认新资源就绪。
    executed_actions: list[dict] = []  # 新增代码+ResourcePreparationTest：记录底层动作；如果没有这一行，无法确认 Ctrl+N 和 type 都按顺序通过。

    def _fake_internal_observe_desktop(arguments, *_args, **_kwargs):  # 新增代码+ResourcePreparationTest：函数段开始，替换真实 observe 返回空白资源窗口；如果没有这段函数，单测会依赖真实桌面。
        observed_payload = {"action": "get_window_state", "state": {"window": blank_window}}  # 新增代码+ResourcePreparationTest：构造生产格式观察数据；如果没有这一行，adapter 解析不到空白窗口标题。
        return "mcp__computer-use__observe 成功：Windows 只读窗口状态已返回。\n数据：" + repr(observed_payload) + "\nComputer Use Image Results\n- image_result_count=0"  # 新增代码+ResourcePreparationTest：返回旧 observe 文本格式；如果没有这一行，测试不会覆盖真实解析路径。
    # 新增代码+ResourcePreparationTest：函数段结束，_fake_internal_observe_desktop 到此结束；如果没有这个边界说明，用户不容易看出 fake observe 范围。

    def _fake_internal_execute_desktop_action(arguments, *_args, **_kwargs):  # 新增代码+ResourcePreparationTest：函数段开始，替换真实键鼠执行；如果没有这段函数，测试可能真的输入文字。
        executed_actions.append(dict(arguments))  # 新增代码+ResourcePreparationTest：保存执行参数；如果没有这一行，无法确认输入动作是否真的在观察后通过。
        return '{"ok": true, "message": "executed", "data": {}}'  # 新增代码+ResourcePreparationTest：返回 fake 成功；如果没有这一行，adapter 无法包装成功路径。
    # 新增代码+ResourcePreparationTest：函数段结束，_fake_internal_execute_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出 fake action 范围。

    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_observe_desktop", _fake_internal_observe_desktop)  # 新增代码+ResourcePreparationTest：替换底层 observe；如果没有这一行，测试会读取真实屏幕。
    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_execute_desktop_action", _fake_internal_execute_desktop_action)  # 新增代码+ResourcePreparationTest：替换底层 action；如果没有这一行，测试会触碰真实窗口。
    blocked_resource_freshness = {"allowed": False, "decision": "restored_existing_resource_requires_new_blank_or_authorization", "document_like": True, "title_preview": controller.window["title_preview"], "app_id": "notepad.exe", "process_name": "notepad.exe", "low_level_event_count": 0}  # 新增代码+ResourcePreparationTest：准备旧资源阻断状态；如果没有这一行，Ctrl+N 不会处在真实恢复旧文档门禁下。
    state = ComputerUseMcpSessionState(last_observed_window=dict(controller.window), last_resource_freshness=blocked_resource_freshness)  # 新增代码+ResourcePreparationTest：模拟 observe 已发现旧资源；如果没有这一行，准备流程不会启动。
    adapter = ComputerUseMcpSessionAdapter(controller=controller, state=state)  # 新增代码+ResourcePreparationTest：构造真实 adapter；如果没有这一行，测试不会覆盖生产状态机。
    new_result = adapter.call_atomic_tool("key", {"key": "CTRL+N", "reason": "新建空白文档，避免写入旧资源"})  # 新增代码+ResourcePreparationTest：执行通用新建空白资源动作；如果没有这一行，准备状态不会建立。
    observe_result = adapter.call_atomic_tool("observe", {"reason": "观察确认新建空白资源是否已经出现"})  # 新增代码+ResourcePreparationTest：执行只读观察确认；如果没有这一行，输入动作不应被允许。
    type_result = adapter.call_atomic_tool("type", {"text": "hello everyone", "reason": "输入用户要求的新内容"})  # 新增代码+ResourcePreparationTest：观察确认后输入文本；如果没有这一行，不能证明流程可继续完成任务。

    assert new_result["ok"] is True  # 新增代码+ResourcePreparationTest：确认 Ctrl+N 被允许；如果没有这一行，根因修复仍未解决旧资源恢复后的新建入口。
    assert observe_result["ok"] is True  # 新增代码+ResourcePreparationTest：确认空白资源观察成功；如果没有这一行，后续输入断言没有可靠前提。
    assert type_result["ok"] is True  # 新增代码+ResourcePreparationTest：确认观察到空白资源后允许输入；如果没有这一行，agent 会被卡在不能继续编辑。
    assert [item["action"] for item in executed_actions] == ["press_key", "type_text"]  # 新增代码+ResourcePreparationTest：确认只有新建和输入两个动作触发；如果没有这一行，流程可能夹带多余危险动作。
    assert adapter.state.resource_preparation_pending == {}  # 新增代码+ResourcePreparationTest：确认空白观察后准备状态被清空；如果没有这一行，后续动作会被错误持续阻断。
# 新增代码+ResourcePreparationTest：函数段结束，test_typing_after_safe_new_blank_shortcut_is_allowed_after_observe_confirms_blank_resource 到此结束；如果没有这个边界说明，用户不容易看出确认后放行范围。


class _MultiTargetController:  # 新增代码+MultiTargetRefGateTest：类段开始，模拟同一会话内已有多个可用目标窗口；如果没有这个类，测试无法覆盖复杂多应用任务的歧义场景。
    def __init__(self) -> None:  # 新增代码+MultiTargetRefGateTest：函数段开始，初始化多目标 controller；如果没有这段函数，registry 没有两个 target。
        self.target_registry = ComputerUseTargetRegistry("multi-target-ref-gate-test")  # 新增代码+MultiTargetRefGateTest：创建真实 target registry；如果没有这一行，多目标隐式解析合同不会被真实验证。
        self.first_window = {"app_id": "notepad.exe", "process_name": "notepad.exe", "pid": 1001, "hwnd": 2001, "window_id": "hwnd:2001", "title_preview": "Untitled - Notepad"}  # 新增代码+MultiTargetRefGateTest：准备第一个目标窗口；如果没有这一行，registry 无法形成多目标状态。
        self.second_window = {"app_id": "word.exe", "process_name": "winword.exe", "pid": 1002, "hwnd": 2002, "window_id": "hwnd:2002", "title_preview": "Document1 - Word"}  # 新增代码+MultiTargetRefGateTest：准备第二个目标窗口；如果没有这一行，registry 仍是单目标状态。
        self.first_ref = self.target_registry.register_target(self.first_window, source_action="launch_app", lease={"origin": "agent_owned_launch"})  # 新增代码+MultiTargetRefGateTest：注册第一个目标；如果没有这一行，多目标列表缺少第一个引用。
        self.second_ref = self.target_registry.register_target(self.second_window, source_action="launch_app", lease={"origin": "agent_owned_launch"})  # 新增代码+MultiTargetRefGateTest：注册第二个目标；如果没有这一行，隐式解析不会返回多目标歧义。
    # 新增代码+MultiTargetRefGateTest：函数段结束，_MultiTargetController.__init__ 到此结束；如果没有这个边界说明，用户不容易看出多目标初始化范围。
# 新增代码+MultiTargetRefGateTest：类段结束，_MultiTargetController 到此结束；如果没有这个边界说明，用户不容易看出多目标 fake 范围。


class _MultiTargetRestoredResourceController:  # 新增代码+ExplicitTargetRefResourceFallbackTest：类段开始，模拟多目标里某个 target_ref 指向恢复旧文档的窗口；如果没有这个类，测试无法复现真实终端里“显式 ref + 旧资源标题”的组合缺口。
    def __init__(self) -> None:  # 新增代码+ExplicitTargetRefResourceFallbackTest：函数段开始，初始化多目标旧资源 controller；如果没有这段函数，registry 不会同时拥有旧文档窗口和另一个应用窗口。
        self.target_registry = ComputerUseTargetRegistry("multi-target-restored-resource-test")  # 新增代码+ExplicitTargetRefResourceFallbackTest：创建真实目标注册表；如果没有这一行，测试会用假状态而不是验证生产 registry 合同。
        self.restored_window = {"app_id": "notepad.exe", "process_name": "notepad.exe", "pid": 3001, "hwnd": 4001, "window_id": "hwnd:4001", "title_preview": "2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad"}  # 新增代码+ExplicitTargetRefResourceFallbackTest：准备恢复旧文档标题的 Notepad 窗口；如果没有这一行，资源新鲜度门禁没有旧资源事实。
        self.second_window = {"app_id": "word.exe", "process_name": "winword.exe", "pid": 3002, "hwnd": 4002, "window_id": "hwnd:4002", "title_preview": "Document1 - Word"}  # 新增代码+ExplicitTargetRefResourceFallbackTest：准备第二个目标窗口制造多目标场景；如果没有这一行，target_ref 被丢弃后仍可能被单目标注入掩盖问题。
        self.restored_ref = self.target_registry.register_target(self.restored_window, source_action="launch_app", lease={"origin": "agent_owned_launch"})  # 新增代码+ExplicitTargetRefResourceFallbackTest：注册旧资源 Notepad 并保存显式 target_ref；如果没有这一行，模型无法指定要操作的窗口。
        self.second_ref = self.target_registry.register_target(self.second_window, source_action="launch_app", lease={"origin": "agent_owned_launch"})  # 新增代码+ExplicitTargetRefResourceFallbackTest：注册第二个目标窗口；如果没有这一行，测试无法证明显式 target_ref 不应被多目标歧义拦住。
    # 新增代码+ExplicitTargetRefResourceFallbackTest：函数段结束，_MultiTargetRestoredResourceController.__init__ 到此结束；如果没有这个边界说明，用户不容易看出多目标旧资源初始化范围。
# 新增代码+ExplicitTargetRefResourceFallbackTest：类段结束，_MultiTargetRestoredResourceController 到此结束；如果没有这个边界说明，用户不容易看出 fake controller 范围。


def test_explicit_target_ref_resolves_window_before_resource_gate_when_multiple_targets_exist(monkeypatch) -> None:  # 新增代码+ExplicitTargetRefResourceFallbackTest：函数段开始，验证多目标下显式 target_ref 必须先解析窗口再做旧资源阻断；如果没有这段测试，adapter 丢失 target_ref 时真实键鼠动作或错误歧义拒绝会复发。
    controller = _MultiTargetRestoredResourceController()  # 新增代码+ExplicitTargetRefResourceFallbackTest：创建多目标且其中一个是旧文档窗口的 controller；如果没有这一行，测试没有真实失败路径输入。
    executed_actions: list[dict] = []  # 新增代码+ExplicitTargetRefResourceFallbackTest：记录任何穿透到底层执行的动作；如果没有这一行，无法证明阻断发生在低层事件前。
    traces: list[tuple[str, dict]] = []  # 新增代码+ExplicitTargetRefResourceFallbackTest：记录 adapter trace；如果没有这一行，测试无法检查显式 target_ref 解析证据。

    def _fake_internal_execute_desktop_action(arguments, *_args, **_kwargs):  # 新增代码+ExplicitTargetRefResourceFallbackTest：函数段开始，替换真实桌面动作；如果没有这段函数，单测可能真的对用户桌面按键。
        executed_actions.append(dict(arguments))  # 新增代码+ExplicitTargetRefResourceFallbackTest：保存穿透动作参数；如果没有这一行，失败时不知道是否已经越过门禁。
        return '{"ok": true, "message": "executed", "data": {}}'  # 新增代码+ExplicitTargetRefResourceFallbackTest：返回 fake 成功文本；如果没有这一行，穿透路径无法被 adapter 正常包装。
    # 新增代码+ExplicitTargetRefResourceFallbackTest：函数段结束，_fake_internal_execute_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出 fake 执行范围。

    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_execute_desktop_action", _fake_internal_execute_desktop_action)  # 新增代码+ExplicitTargetRefResourceFallbackTest：替换底层执行函数；如果没有这一行，测试会触碰真实桌面。
    callbacks = ComputerUseMcpSessionCallbacks(record_runtime_trace=lambda name, payload: traces.append((name, dict(payload))))  # 新增代码+ExplicitTargetRefResourceFallbackTest：注入 trace 收集回调；如果没有这一行，测试无法证明 adapter 已按显式 ref 注入窗口。
    adapter = ComputerUseMcpSessionAdapter(controller=controller, callbacks=callbacks)  # 新增代码+ExplicitTargetRefResourceFallbackTest：构造真实 adapter；如果没有这一行，测试不会覆盖生产 action 入口。
    result = adapter.call_atomic_tool("key", {"key": "CTRL+A", "target_ref": controller.restored_ref, "reason": "请打开本地真实记事本，并输入 hello everyone，最后保存文件名为 1.txt 到桌面"})  # 新增代码+ExplicitTargetRefResourceFallbackTest：模拟模型在多目标下明确选择旧文档 Notepad；如果没有这一行，target_ref 丢失缺口不会触发。

    assert result["ok"] is False  # 新增代码+ExplicitTargetRefResourceFallbackTest：确认动作被拒绝；如果没有这一行，测试无法防止继续写入旧文档。
    assert executed_actions == []  # 新增代码+ExplicitTargetRefResourceFallbackTest：确认没有底层键鼠动作穿透；如果没有这一行，安全拒绝可能已经太晚。
    assert "OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED" in result["payload"]["legacy_text"]  # 新增代码+ExplicitTargetRefResourceFallbackTest：确认返回资源用户动作 marker；如果没有这一行，模型可能把结果当普通多目标错误继续重试。
    assert result["payload"]["resource_freshness"]["decision"] == "restored_existing_resource_requires_new_blank_or_authorization"  # 新增代码+ExplicitTargetRefResourceFallbackTest：确认拒绝原因是旧资源而不是多目标歧义；如果没有这一行，修复可能跑偏到错误门禁。
    assert any(name == "computer_use_mcp_explicit_target_ref_window_injected" for name, _payload in traces)  # 新增代码+ExplicitTargetRefResourceFallbackTest：确认 adapter 记录显式 target_ref 注入证据；如果没有这一行，真实验收日志仍难追踪。
# 新增代码+ExplicitTargetRefResourceFallbackTest：函数段结束，test_explicit_target_ref_resolves_window_before_resource_gate_when_multiple_targets_exist 到此结束；如果没有这个边界说明，用户不容易看出新回归测试范围。


def test_action_without_target_ref_is_blocked_when_multiple_targets_are_active(monkeypatch) -> None:  # 新增代码+MultiTargetRefGateTest：函数段开始，验证多目标时漏写 target_ref 会被零事件拒绝；如果没有这段测试，复杂多应用任务可能误操作最近 active 窗口。
    controller = _MultiTargetController()  # 新增代码+MultiTargetRefGateTest：创建多目标 controller；如果没有这一行，测试没有歧义 target 状态。
    executed_actions: list[dict] = []  # 新增代码+MultiTargetRefGateTest：保存底层执行尝试；如果没有这一行，无法证明拒绝发生在低层事件之前。

    def _fake_internal_execute_desktop_action(arguments, *_args, **_kwargs):  # 新增代码+MultiTargetRefGateTest：函数段开始，替换真实键鼠执行；如果没有这段函数，单元测试可能触碰桌面。
        executed_actions.append(dict(arguments))  # 新增代码+MultiTargetRefGateTest：记录穿透动作；如果没有这一行，零事件断言没有数据来源。
        return '{"ok": true, "message": "executed", "data": {}}'  # 新增代码+MultiTargetRefGateTest：返回成功文本；如果没有这一行，穿透路径无法被 adapter 包装。
    # 新增代码+MultiTargetRefGateTest：函数段结束，_fake_internal_execute_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出 fake action 范围。

    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_execute_desktop_action", _fake_internal_execute_desktop_action)  # 新增代码+MultiTargetRefGateTest：替换底层执行函数；如果没有这一行，测试会进入真实动作链。
    state = ComputerUseMcpSessionState(last_observed_window=dict(controller.first_window))  # 新增代码+MultiTargetRefGateTest：模拟模型最近观察了一个窗口但没有显式 target_ref；如果没有这一行，测试不会覆盖复用窗口路径。
    adapter = ComputerUseMcpSessionAdapter(controller=controller, state=state)  # 新增代码+MultiTargetRefGateTest：构造真实 adapter；如果没有这一行，测试不会覆盖生产动作入口。
    result = adapter.call_atomic_tool("key", {"key": "CTRL+S", "reason": "save active document"})  # 新增代码+MultiTargetRefGateTest：模拟多目标下漏写 target_ref 的按键；如果没有这一行，多目标拒绝不会触发。

    assert result["ok"] is False  # 新增代码+MultiTargetRefGateTest：确认多目标漏 target_ref 被拒绝；如果没有这一行，测试无法防止隐式误操作。
    assert executed_actions == []  # 新增代码+MultiTargetRefGateTest：确认没有底层执行；如果没有这一行，多目标拒绝可能只是底层事后失败。
    assert result["payload"]["decision"] == "multiple_active_targets_require_target_ref"  # 新增代码+MultiTargetRefGateTest：确认稳定拒绝决策码；如果没有这一行，模型不知道要补显式 target_ref。
# 新增代码+MultiTargetRefGateTest：函数段结束，test_action_without_target_ref_is_blocked_when_multiple_targets_are_active 到此结束；如果没有这个边界说明，用户不容易看出多目标拒绝范围。
