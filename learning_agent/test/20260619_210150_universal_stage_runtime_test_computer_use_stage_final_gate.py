import json  # 新增代码+DesktopStageFinalGateTest：导入 JSON 构造工具输出；如果没有这行代码，record_tool_result 解析路径无法测试。

from learning_agent.core.convergence_controller import assess_final_answer_for_desktop_task, record_tool_result  # 新增代码+DesktopStageFinalGateTest：导入最终回答门禁和工具结果记录；如果没有这行代码，测试无法覆盖第 8 项。
from learning_agent.core.task_state import TaskState  # 新增代码+DesktopStageFinalGateTest：导入任务状态；如果没有这行代码，record_tool_result 需要的上下文无法构造。


def _state(evidence: dict) -> dict:  # 新增代码+DesktopStageFinalGateTest：函数段开始，构造带阶段证据的 runtime_state；如果没有这段函数，多个测试会重复样板。
    return {"computer_use_stage_evidence": dict(evidence)}  # 新增代码+DesktopStageFinalGateTest：返回运行时状态；如果没有这行代码，final gate 读不到结构化证据。
# 新增代码+DesktopStageFinalGateTest：函数段结束，_state 到此结束；如果没有这个边界说明，初学者不容易看出状态构造范围。


def test_blocks_next_desktop_action_when_stage_task_is_incomplete() -> None:  # 新增代码+DesktopStageFinalGateTest：函数段开始，验证 next desktop action 不能 final；如果没有这个测试，Paint 类复杂任务会再次早停。
    decision = assess_final_answer_for_desktop_task("Next desktop action: draw the missing line.", _state({"desktop_task_incomplete": True, "stage_count": 5, "completed_stage_count": 2}))  # 新增代码+DesktopStageFinalGateTest：执行未完成门禁；如果没有这行代码，无法得到判断结果。
    assert decision.allow_final_answer is False  # 新增代码+DesktopStageFinalGateTest：确认不允许最终回答；如果没有这行代码，未完成动作可能被误放行。
    assert decision.reason == "desktop_task_incomplete"  # 新增代码+DesktopStageFinalGateTest：确认原因清晰；如果没有这行代码，失败时不容易定位门禁分支。


def test_blocks_success_marker_when_completed_stage_count_is_short() -> None:  # 新增代码+DesktopStageFinalGateTest：函数段开始，验证虚假成功 marker 被挡；如果没有这个测试，模型可能输出 OK 掩盖阶段未完成。
    decision = assess_final_answer_for_desktop_task("UNIVERSAL_DRAWING_STAGE_BATCH_OK desktop_task_completed=true", _state({"desktop_task_completed": False, "desktop_task_incomplete": True, "stage_count": 6, "completed_stage_count": 3}))  # 新增代码+DesktopStageFinalGateTest：执行虚假成功门禁；如果没有这行代码，无法触发成功话术场景。
    assert decision.allow_final_answer is False  # 新增代码+DesktopStageFinalGateTest：确认虚假成功不放行；如果没有这行代码，acceptance marker 可能被滥用。
    assert decision.reason == "desktop_task_incomplete"  # 新增代码+DesktopStageFinalGateTest：确认仍归因为桌面任务未完成；如果没有这行代码，用户看不到根因。


def test_allows_final_answer_when_desktop_stage_task_completed() -> None:  # 新增代码+DesktopStageFinalGateTest：函数段开始，验证完成任务可以 final；如果没有这个测试，门禁可能过度阻断。
    decision = assess_final_answer_for_desktop_task("任务已完成。", _state({"desktop_task_completed": True, "desktop_task_incomplete": False, "stage_count": 4, "completed_stage_count": 4}))  # 新增代码+DesktopStageFinalGateTest：执行完成放行判断；如果没有这行代码，无法验证正向路径。
    assert decision.allow_final_answer is True  # 新增代码+DesktopStageFinalGateTest：确认允许最终回答；如果没有这行代码，完成任务可能无法收束。
    assert decision.reason == "desktop_task_completed"  # 新增代码+DesktopStageFinalGateTest：确认完成原因；如果没有这行代码，审计看不到放行依据。


def test_needs_user_allows_only_user_action_answer() -> None:  # 新增代码+DesktopStageFinalGateTest：函数段开始，验证 needs_user 必须请求用户动作；如果没有这个测试，授权/关闭窗口场景可能被伪装成完成。
    evidence = {"needs_user": True, "desktop_task_completed": False, "desktop_task_incomplete": True, "stage_count": 3, "completed_stage_count": 2}  # 新增代码+DesktopStageFinalGateTest：构造用户介入证据；如果没有这行代码，测试无法覆盖 needs_user。
    blocked = assess_final_answer_for_desktop_task("已经成功完成。", _state(evidence))  # 新增代码+DesktopStageFinalGateTest：执行错误成功话术判断；如果没有这行代码，无法确认 needs_user 不被误放行。
    allowed = assess_final_answer_for_desktop_task("需要你手动关闭旧窗口或明确授权已有窗口。", _state(evidence))  # 新增代码+DesktopStageFinalGateTest：执行请求用户动作判断；如果没有这行代码，无法确认安全说明可 final。
    assert blocked.allow_final_answer is False  # 新增代码+DesktopStageFinalGateTest：确认 needs_user 成功话术被挡；如果没有这行代码，旧窗口问题会再次反复操作。
    assert allowed.allow_final_answer is True  # 新增代码+DesktopStageFinalGateTest：确认明确请求用户动作可放行；如果没有这行代码，agent 无法向用户解释阻断。


def test_record_tool_result_extracts_stage_evidence_from_json_output() -> None:  # 新增代码+DesktopStageFinalGateTest：函数段开始，验证工具结果能沉淀阶段证据；如果没有这个测试，agent 最终出口读不到 tool result 事实。
    runtime_state: dict = {}  # 新增代码+DesktopStageFinalGateTest：初始化空运行时状态；如果没有这行代码，record_tool_result 没地方写证据。
    task_state = TaskState.from_user_input("请执行 computer use 任务", session_id="s", run_id="r")  # 新增代码+DesktopStageFinalGateTest：构造任务状态；如果没有这行代码，record_tool_result 接口无法调用。
    output = json.dumps({"loop_report": {"desktop_task_completed": True, "stage_count": 2, "completed_stage_count": 2}}, ensure_ascii=False)  # 新增代码+DesktopStageFinalGateTest：构造嵌套 JSON 工具输出；如果没有这行代码，无法测试递归提取。
    record_tool_result({"name": "mcp__computer-use__computer_batch", "arguments": {}}, output, task_state, runtime_state)  # 新增代码+DesktopStageFinalGateTest：记录工具结果；如果没有这行代码，阶段证据不会写入状态。
    assert runtime_state["computer_use_stage_evidence"]["desktop_task_completed"] is True  # 新增代码+DesktopStageFinalGateTest：确认结构化证据被保存；如果没有这行代码，final gate 接线可能只是纯函数。
