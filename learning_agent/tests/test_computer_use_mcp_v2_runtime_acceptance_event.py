from learning_agent.computer_use_mcp_v2.inferred_ant_mcp import runtime as runtime_module  # 新增代码+AcceptanceEventEvidenceTest：导入 runtime 模块本体，方便替换动作分发函数；如果没有这一行，测试无法模拟资源拒绝结果。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import ComputerUseMcpV2Context  # 新增代码+AcceptanceEventEvidenceTest：导入真实上下文类型；如果没有这一行，测试会绕开生产事件回调入口。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import dispatch_computer_use_mcp_v2_tool  # 新增代码+AcceptanceEventEvidenceTest：导入真实分发入口；如果没有这一行，测试只能测 helper 而不能覆盖事件发射路径。


def test_acceptance_event_includes_resource_user_action_summary(monkeypatch) -> None:  # 新增代码+AcceptanceEventEvidenceTest：函数段开始，验证资源拒绝会进入验收事件摘要；如果没有这段测试，真实终端场景只能靠 debug log 证明零事件阻断。
    events: list[tuple[str, dict]] = []  # 新增代码+AcceptanceEventEvidenceTest：保存 runtime 发出的验收事件；如果没有这一行，测试无法断言 event payload 内容。

    def _fake_emit_acceptance_event(event_name: str, payload: dict) -> None:  # 新增代码+AcceptanceEventEvidenceTest：函数段开始，模拟真实终端事件写入回调；如果没有这段函数，事件会丢到空回调里。
        events.append((event_name, dict(payload)))  # 新增代码+AcceptanceEventEvidenceTest：复制保存事件名和 payload；如果没有这一行，后续断言没有数据来源。
    # 新增代码+AcceptanceEventEvidenceTest：函数段结束，_fake_emit_acceptance_event 到此结束；如果没有这个边界说明，用户不容易看出 fake 事件范围。

    def _fake_perform_action(_context, tool_name: str, _arguments: dict) -> dict:  # 新增代码+AcceptanceEventEvidenceTest：函数段开始，替换真实键鼠动作为资源门禁拒绝；如果没有这段函数，单元测试可能触碰真实桌面。
        return {  # 新增代码+AcceptanceEventEvidenceTest：返回生产工具结果形态的失败对象；如果没有这一行，runtime 无法继续包装和发事件。
            "tool_name": tool_name,  # 新增代码+AcceptanceEventEvidenceTest：保留被测工具名；如果没有这一行，失败时看不出哪个动作触发拒绝。
            "ok": False,  # 新增代码+AcceptanceEventEvidenceTest：声明动作未执行成功；如果没有这一行，runtime 会把事件当成功工具。
            "error_class": "desktop_resource_user_action_required",  # 新增代码+AcceptanceEventEvidenceTest：声明资源用户动作阻断分类；如果没有这一行，验收事件无法筛选拒绝类型。
            "reason": "OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED\nresource_freshness_decision=restored_existing_resource_requires_new_blank_or_authorization\nlow_level_event_count=0",  # 新增代码+AcceptanceEventEvidenceTest：模拟真实工具结果里的低敏 marker 文本；如果没有这一行，测试无法覆盖 acceptance controller 需要的证据。
        }  # 新增代码+AcceptanceEventEvidenceTest：失败对象结束；如果没有这一行，Python 字典语法不完整。
    # 新增代码+AcceptanceEventEvidenceTest：函数段结束，_fake_perform_action 到此结束；如果没有这个边界说明，用户不容易看出 fake 动作范围。

    monkeypatch.setattr(runtime_module, "perform_action", _fake_perform_action)  # 新增代码+AcceptanceEventEvidenceTest：替换 runtime 动作分发函数；如果没有这一行，测试会调用真实 Computer Use 动作。
    context = ComputerUseMcpV2Context(emit_acceptance_event=_fake_emit_acceptance_event)  # 新增代码+AcceptanceEventEvidenceTest：构造带事件捕获的真实上下文；如果没有这一行，runtime 不会输出验收事件。
    result = dispatch_computer_use_mcp_v2_tool("key", {"keys": ["CTRL", "N"]}, context)  # 新增代码+AcceptanceEventEvidenceTest：通过真实 runtime 分发 key 动作；如果没有这一行，事件发射路径不会被触发。

    assert result["ok"] is False  # 新增代码+AcceptanceEventEvidenceTest：确认 fake 资源拒绝结果确实返回失败；如果没有这一行，后续事件断言可能掩盖分发问题。
    assert events[-1][0] == "computer_use_mcp_v2_tool"  # 新增代码+AcceptanceEventEvidenceTest：确认最后一条事件是工具完成事件；如果没有这一行，测试可能误读其它事件。
    event_payload = events[-1][1]  # 新增代码+AcceptanceEventEvidenceTest：取出工具完成事件 payload；如果没有这一行，后续字段断言重复索引可读性差。
    assert event_payload["tool_name"] == "key"  # 新增代码+AcceptanceEventEvidenceTest：确认事件保留工具名；如果没有这一行，验收日志难以定位哪个工具被拒绝。
    assert event_payload["ok"] is False  # 新增代码+AcceptanceEventEvidenceTest：确认事件保留失败状态；如果没有这一行，controller 不能判断工具失败。
    assert event_payload["error_class"] == "desktop_resource_user_action_required"  # 新增代码+AcceptanceEventEvidenceTest：确认事件携带稳定错误分类；如果没有这一行，controller 无法区分资源拒绝和普通失败。
    assert event_payload["resource_freshness_decision"] == "restored_existing_resource_requires_new_blank_or_authorization"  # 新增代码+AcceptanceEventEvidenceTest：确认事件携带资源门禁决策；如果没有这一行，真实验收无法证明拒绝原因。
    assert event_payload["low_level_event_count"] == 0  # 新增代码+AcceptanceEventEvidenceTest：确认事件证明没有底层键鼠动作；如果没有这一行，真实验收无法证明没有误操作旧文档。
    assert "OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED" in event_payload["reason"]  # 新增代码+AcceptanceEventEvidenceTest：确认事件保留可搜索 marker；如果没有这一行，scenario 的 event_payload_contains 会继续失败。
# 新增代码+AcceptanceEventEvidenceTest：函数段结束，test_acceptance_event_includes_resource_user_action_summary 到此结束；如果没有这个边界说明，用户不容易看出验收事件证据回归范围。
