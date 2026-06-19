from types import SimpleNamespace  # 新增代码+ControlledResourceContextTest：导入轻量对象容器；如果没有这一行，测试需要额外定义样板 controller 类。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.legacy_ports import build_legacy_host_adapter  # 新增代码+ControlledResourceContextTest：导入 v2 到旧成熟 adapter 的桥接入口；如果没有这一行，测试无法证明 agent 上下文是否进入 session state。
from learning_agent.computer_use_mcp_v2.windows_runtime import mcp_session_adapter as adapter_module  # 新增代码+ControlledResourceContextTest：导入 adapter 模块本体用于替换真实桌面执行；如果没有这一行，单元测试可能真的启动本地应用。
from learning_agent.computer_use_mcp_v2.windows_runtime.desktop_task_router import classify_desktop_task  # 新增代码+ControlledResourceContextTest：导入自然语言分类器；如果没有这一行，测试无法从真实用户 prompt 开始验证脱敏资源提取。
from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter import ComputerUseMcpSessionAdapter  # 新增代码+ControlledResourceContextTest：导入真实 MCP session adapter；如果没有这一行，测试只能验证 helper 不能覆盖生产入口。
from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter import ComputerUseMcpSessionState  # 新增代码+ControlledResourceContextTest：导入真实 session 状态容器；如果没有这一行，测试无法模拟授权阶段和 agent 上下文共存。
from learning_agent.computer_use_mcp_v2.windows_runtime.target_registry import ComputerUseTargetRegistry  # 新增代码+ControlledResourceContextTest：导入真实目标注册表；如果没有这一行，adapter 的目标解析边界无法按生产形状初始化。


def test_desktop_task_router_extracts_controlled_desktop_txt_resource_without_raw_prompt() -> None:  # 新增代码+ControlledResourceContextTest：函数段开始，验证分类器只提取安全资源摘要而不是保存原始 prompt；如果没有这段测试，真实 prompt 里的 1.txt 会继续在后续链路丢失。
    prompt = "请打开本地真实记事本，并输入 hello everyone，最后保存文件名为1.txt到本地电脑桌面。"  # 新增代码+ControlledResourceContextTest：准备真实用户会输入的中文任务；如果没有这一行，测试不会覆盖这次反复失败的压力 prompt。
    intent = classify_desktop_task(prompt)  # 新增代码+ControlledResourceContextTest：调用真实分类器；如果没有这一行，测试无法验证源头是否产生脱敏资源提示。
    summary = intent.to_dict()  # 新增代码+ControlledResourceContextTest：读取公开脱敏字典；如果没有这一行，后续断言会直接依赖 dataclass 内部表示。

    assert summary["controlled_resource_name"] == "1.txt"  # 新增代码+ControlledResourceContextTest：确认文件名被提取；如果没有这一行，后续启动层仍不知道要打开哪个受控文本资源。
    assert summary["controlled_resource_location_hint"] == "desktop"  # 新增代码+ControlledResourceContextTest：确认桌面位置被脱敏保存；如果没有这一行，controller 不会自动拼桌面路径。
    assert summary["raw_prompt_included"] is False  # 新增代码+ControlledResourceContextTest：确认没有保存原始 prompt；如果没有这一行，修复可能用隐私风险换功能。
    assert "hello everyone" not in str(summary)  # 新增代码+ControlledResourceContextTest：确认输入正文没有被塞进上下文；如果没有这一行，受控资源提示会携带不必要用户内容。
# 新增代码+ControlledResourceContextTest：函数段结束，test_desktop_task_router_extracts_controlled_desktop_txt_resource_without_raw_prompt 到此结束；如果没有这个边界说明，用户不容易看出分类器资源测试范围。


def test_legacy_host_adapter_persists_agent_controlled_resource_context() -> None:  # 新增代码+ControlledResourceContextTest：函数段开始，验证 v2 host 创建时会把 agent 的脱敏资源上下文放进 session state；如果没有这段测试，adapter 无法看到分类器结果。
    controller = SimpleNamespace(target_registry=ComputerUseTargetRegistry("controlled-resource-host-test"))  # 新增代码+ControlledResourceContextTest：创建带真实 registry 的轻量 controller；如果没有这一行，host adapter 缺少生产形状的 controller。
    agent = SimpleNamespace(  # 新增代码+ControlledResourceContextTest：创建轻量 agent 替身；如果没有这一行，build_legacy_host_adapter 没有可读的 agent 状态。
        computer_use_controller=controller,  # 新增代码+ControlledResourceContextTest：提供 Computer Use controller；如果没有这一项，host adapter 会直接返回 None。
        desktop_task_context={"controlled_resource_name": "1.txt", "controlled_resource_location_hint": "desktop", "raw_prompt_included": False},  # 新增代码+ControlledResourceContextTest：模拟分类器写入的脱敏资源上下文；如果没有这一项，测试不能复现真实链路。
        ask_permission=lambda _action: True,  # 新增代码+ControlledResourceContextTest：提供权限回调；如果没有这一项，回调容器会使用默认拒绝并影响动作测试。
        observation_events=[],  # 新增代码+ControlledResourceContextTest：提供观察事件列表；如果没有这一项，回调闭包读取时会退到默认空值。
    )  # 新增代码+ControlledResourceContextTest：结束 agent 替身构造；如果没有这一行，Python 调用语法不完整。

    host = build_legacy_host_adapter(agent, lambda _kind, _payload: None)  # 新增代码+ControlledResourceContextTest：构造真实 v2 legacy host；如果没有这一行，session state 不会被创建。
    state = agent._computer_use_mcp_session_state  # 新增代码+ControlledResourceContextTest：读取 host 写回 agent 的 session state；如果没有这一行，断言拿不到实际状态。

    assert host is not None  # 新增代码+ControlledResourceContextTest：确认 host 正常创建；如果没有这一行，后续 state 断言可能掩盖 controller 缺失。
    assert state.grants["agent_desktop_task_context"]["controlled_resource_name"] == "1.txt"  # 新增代码+ControlledResourceContextTest：确认文件名进入 session state；如果没有这一行，open_application 仍只能依赖模型短 reason。
    assert state.grants["agent_desktop_task_context"]["controlled_resource_location_hint"] == "desktop"  # 新增代码+ControlledResourceContextTest：确认位置提示进入 session state；如果没有这一行，controller 仍无法知道该拼桌面路径。
# 新增代码+ControlledResourceContextTest：函数段结束，test_legacy_host_adapter_persists_agent_controlled_resource_context 到此结束；如果没有这个边界说明，用户不容易看出 host 上下文测试范围。


def test_open_application_uses_agent_resource_context_when_model_reason_loses_filename(monkeypatch) -> None:  # 新增代码+ControlledResourceContextTest：函数段开始，验证模型短 reason 丢文件名时 adapter 仍能从 session state 补受控资源；如果没有这段测试，真实终端会继续裸启动 Notepad。
    controller = SimpleNamespace(target_registry=ComputerUseTargetRegistry("controlled-resource-adapter-test"))  # 新增代码+ControlledResourceContextTest：创建带 registry 的轻量 controller；如果没有这一行，adapter 的目标解析 helper 可能缺对象。
    captured_arguments: dict = {}  # 新增代码+ControlledResourceContextTest：保存底层执行收到的最终参数；如果没有这一行，测试无法证明资源字段有没有传到底层。

    def _fake_internal_execute_desktop_action(arguments, *_args, **_kwargs):  # 新增代码+ControlledResourceContextTest：函数段开始，替换真实桌面启动避免碰用户本机窗口；如果没有这段函数，单元测试会真的打开应用。
        captured_arguments.update(dict(arguments))  # 新增代码+ControlledResourceContextTest：记录 adapter 输出给 controller 的参数；如果没有这一行，断言没有事实来源。
        return '{"ok": true, "message": "captured", "data": {}}'  # 新增代码+ControlledResourceContextTest：返回结构化成功文本；如果没有这一行，adapter 包装流程无法继续。
    # 新增代码+ControlledResourceContextTest：函数段结束，_fake_internal_execute_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出 fake 执行范围。

    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_execute_desktop_action", _fake_internal_execute_desktop_action)  # 新增代码+ControlledResourceContextTest：只替换最底层真实动作；如果没有这一行，测试会触发真实桌面。
    state = ComputerUseMcpSessionState()  # 新增代码+ControlledResourceContextTest：创建真实 session state；如果没有这一行，adapter 无法保存授权和 agent 上下文。
    state.grants["last_request_arguments"] = {"reason": "通过真实记事本窗口输入文本、拖动窗口、保存到桌面；先获取 Notepad 权限。"}  # 新增代码+ControlledResourceContextTest：模拟真实验收里 request_access.reason 已经被模型压缩且丢掉 1.txt；如果没有这一行，测试不会覆盖失败日志。
    state.grants["agent_desktop_task_context"] = {"controlled_resource_name": "1.txt", "controlled_resource_location_hint": "desktop"}  # 新增代码+ControlledResourceContextTest：模拟 host 从分类器保留下来的脱敏资源提示；如果没有这一行，adapter 没有可兜底的信息。
    adapter = ComputerUseMcpSessionAdapter(controller=controller, state=state)  # 新增代码+ControlledResourceContextTest：构造真实 adapter；如果没有这一行，测试不会覆盖生产 open_application 路径。

    result = adapter.call_atomic_tool("open_application", {"app_name": "notepad", "reason": "打开一个新的真实记事本窗口。"})  # 新增代码+ControlledResourceContextTest：模拟模型启动应用时再次没有写文件名；如果没有这一行，真实失败条件不会被触发。

    assert result["ok"] is True  # 新增代码+ControlledResourceContextTest：确认 fake 执行路径成功；如果没有这一行，后续参数断言可能掩盖包装失败。
    assert captured_arguments["controlled_resource_name"] == "1.txt"  # 新增代码+ControlledResourceContextTest：确认受控文件名传到底层动作参数；如果没有这一行，controller 无法从源头构造 Desktop\\1.txt。
    assert "1.txt" in captured_arguments["session_task_context"]  # 新增代码+ControlledResourceContextTest：确认 session_task_context 也包含文件名；如果没有这一行，旧 controller 文本解析路径仍可能失效。
    assert "desktop" in captured_arguments["session_task_context"].lower()  # 新增代码+ControlledResourceContextTest：确认 session_task_context 包含桌面语义；如果没有这一行，controller 不会自动把文件定位到桌面。
# 新增代码+ControlledResourceContextTest：函数段结束，test_open_application_uses_agent_resource_context_when_model_reason_loses_filename 到此结束；如果没有这个边界说明，用户不容易看出 adapter 兜底测试范围。


def test_legacy_host_syncs_latest_agent_resource_context_after_full_mode_context_reuse(monkeypatch) -> None:  # 新增代码+ControlledResourceContextTest：函数段开始，验证 `/computer use --full` 先建 context 后仍能同步下一条真实任务的资源提示；如果没有这段测试，真实终端会继续在复用 host 时丢 1.txt。
    controller = SimpleNamespace(target_registry=ComputerUseTargetRegistry("controlled-resource-reuse-test"))  # 新增代码+ControlledResourceContextTest：创建带 registry 的轻量 controller；如果没有这一行，legacy host 没有生产形状的控制器。
    captured_arguments: dict = {}  # 新增代码+ControlledResourceContextTest：保存底层启动参数；如果没有这一行，测试无法证明复用 host 是否补了资源。

    def _fake_internal_execute_desktop_action(arguments, *_args, **_kwargs):  # 新增代码+ControlledResourceContextTest：函数段开始，替换真实桌面动作；如果没有这段函数，测试会打开用户本地应用。
        captured_arguments.update(dict(arguments))  # 新增代码+ControlledResourceContextTest：记录最终传给 controller 的参数；如果没有这一行，断言没有事实来源。
        return '{"ok": true, "message": "captured", "data": {}}'  # 新增代码+ControlledResourceContextTest：返回 fake 成功文本；如果没有这一行，host 包装流程无法继续。
    # 新增代码+ControlledResourceContextTest：函数段结束，_fake_internal_execute_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出 fake 执行范围。

    monkeypatch.setattr(adapter_module.computer_use_internal_adapter_tools, "internal_execute_desktop_action", _fake_internal_execute_desktop_action)  # 新增代码+ControlledResourceContextTest：只替换最底层真实动作；如果没有这一行，测试会触碰真实桌面。
    agent = SimpleNamespace(  # 新增代码+ControlledResourceContextTest：创建模拟 `/computer use --full` 阶段的 agent；如果没有这一行，host 没有 agent 来源可复用。
        computer_use_controller=controller,  # 新增代码+ControlledResourceContextTest：提供 Computer Use controller；如果没有这一项，legacy host 不会创建。
        desktop_task_context={},  # 新增代码+ControlledResourceContextTest：模拟 full 模式刚打开时还没有真实任务资源；如果没有这一项，测试不能覆盖 context 复用缺口。
        ask_permission=lambda _action: True,  # 新增代码+ControlledResourceContextTest：提供权限回调；如果没有这一项，host 会使用默认拒绝路径。
        observation_events=[],  # 新增代码+ControlledResourceContextTest：提供观察事件容器；如果没有这一项，回调闭包读取时缺字段。
    )  # 新增代码+ControlledResourceContextTest：结束 agent 替身构造；如果没有这一行，Python 调用语法不完整。
    host = build_legacy_host_adapter(agent, lambda _kind, _payload: None)  # 新增代码+ControlledResourceContextTest：先创建会被复用的 legacy host；如果没有这一行，无法模拟 `/computer use --full` 先建 context。
    agent.desktop_task_context = {"controlled_resource_name": "1.txt", "controlled_resource_location_hint": "desktop", "raw_prompt_included": False}  # 新增代码+ControlledResourceContextTest：模拟下一条真实用户任务到来后 agent 更新了脱敏资源上下文；如果没有这一行，测试没有时序变化。

    result = host.open_application("notepad", {"app_name": "notepad", "reason": "打开一个新的真实记事本窗口。"})  # 新增代码+ControlledResourceContextTest：通过复用 host 启动应用；如果没有这一行，缺口不会被触发。

    assert result["ok"] is True  # 新增代码+ControlledResourceContextTest：确认 fake 启动路径成功；如果没有这一行，后续参数断言可能掩盖包装失败。
    assert captured_arguments["controlled_resource_name"] == "1.txt"  # 新增代码+ControlledResourceContextTest：确认复用 host 调用前同步了最新文件名；如果没有这一行，真实终端会继续裸启动旧 Notepad。
    assert "desktop" in captured_arguments["session_task_context"].lower()  # 新增代码+ControlledResourceContextTest：确认复用 host 调用前同步了桌面语义；如果没有这一行，controller 不会自动拼桌面文件路径。
# 新增代码+ControlledResourceContextTest：函数段结束，test_legacy_host_syncs_latest_agent_resource_context_after_full_mode_context_reuse 到此结束；如果没有这个边界说明，用户不容易看出 context 复用测试范围。
