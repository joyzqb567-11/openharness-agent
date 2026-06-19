from types import SimpleNamespace  # 新增代码+ObserveTargetRefTest：导入简单对象模拟 controller 返回值；如果没有这一行，测试需要写额外样板类。

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
