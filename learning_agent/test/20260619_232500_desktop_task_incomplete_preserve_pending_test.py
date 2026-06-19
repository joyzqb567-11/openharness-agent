"""desktop_task 未完成后的通用动作收敛测试。"""  # 新增代码+DesktopTaskIncompleteGateTest：说明本测试验证高层桌面任务未完成时不能退回零散原子动作；如果没有这行代码，读者不知道测试目标。
from __future__ import annotations  # 新增代码+DesktopTaskIncompleteGateTest：延迟解析类型注解；如果没有这行代码，后续类型写法在旧运行方式下更容易受导入顺序影响。

import json  # 新增代码+DesktopTaskIncompleteGateTest：导入 JSON 构造工具输出；如果没有这行代码，测试无法模拟 MCP 文本结果。

from learning_agent.core.actionability_state import get_pending_actionability, record_actionability_from_tool_result, should_block_tool_for_pending_actionability  # 新增代码+DesktopTaskIncompleteGateTest：导入 actionability 状态入口；如果没有这行代码，测试无法验证 runtime 门禁。


def _desktop_task_incomplete_output() -> str:  # 新增代码+DesktopTaskIncompleteGateTest：函数段开始，构造包含未完成 marker 的工具输出；如果没有这段函数，多个断言会重复协议样板。
    return json.dumps(  # 新增代码+DesktopTaskIncompleteGateTest：返回 JSON 文本，模拟真实 MCP content 文本；如果没有这行代码，record_actionability 无法按生产路径解析。
        {  # 新增代码+DesktopTaskIncompleteGateTest：payload 字典开始；如果没有这行代码，JSON 没有结构化证据容器。
            "ok": False,  # 新增代码+DesktopTaskIncompleteGateTest：声明高层任务未完成；如果没有这行代码，测试缺少失败事实。
            "payload": {  # 新增代码+DesktopTaskIncompleteGateTest：payload 开始；如果没有这行代码，结构会偏离真实 desktop_task 工具结果。
                "desktop_task_incomplete": True,  # 新增代码+DesktopTaskIncompleteGateTest：写入结构化未完成证据；如果没有这行代码，final gate 无法识别桌面任务未完成。
                "stage_count": 5,  # 新增代码+DesktopTaskIncompleteGateTest：写入总阶段数；如果没有这行代码，阶段完整性无法审计。
                "completed_stage_count": 2,  # 新增代码+DesktopTaskIncompleteGateTest：写入已完成阶段数；如果没有这行代码，未完成比例无法审计。
                "actionability": "\nOPENHARNESS_DESKTOP_TASK_INCOMPLETE\nactionability_kind=desktop_task_incomplete\nnext_required_tool=mcp__computer-use__desktop_task\nnext_allowed_tools=mcp__computer-use__desktop_task,mcp__computer-use__observe,mcp__computer-use__request_access\nnext_required_reason=desktop_task_incomplete\nstage_count=5\ncompleted_stage_count=2\ndesktop_task_incomplete=true\ntarget_ref=target_1\n",  # 新增代码+DesktopTaskIncompleteGateTest：嵌入稳定 actionability marker；如果没有这行代码，模型可继续调用 key/click/drag 逃离 Stage Runtime。
            },  # 新增代码+DesktopTaskIncompleteGateTest：payload 字典结束；如果没有这行代码，Python 字典语法不完整。
        },  # 新增代码+DesktopTaskIncompleteGateTest：顶层字典结束；如果没有这行代码，JSON 输入不完整。
        ensure_ascii=False,  # 新增代码+DesktopTaskIncompleteGateTest：保留中文便于调试；如果没有这行代码，失败输出会变成难读转义。
        sort_keys=True,  # 新增代码+DesktopTaskIncompleteGateTest：排序输出让测试稳定；如果没有这行代码，日志比对会抖动。
    )  # 新增代码+DesktopTaskIncompleteGateTest：JSON 序列化调用结束；如果没有这行代码，函数没有返回文本。
# 新增代码+DesktopTaskIncompleteGateTest：函数段结束，_desktop_task_incomplete_output 到此结束；如果没有这个边界说明，初学者不容易看出工具输出样板。


def test_desktop_task_incomplete_records_pending_stage_tool() -> None:  # 新增代码+DesktopTaskIncompleteGateTest：函数段开始，验证 desktop_task 未完成会沉淀 pending；如果没有这个测试，模型会把未完成当普通失败。
    runtime_state: dict[str, object] = {}  # 新增代码+DesktopTaskIncompleteGateTest：准备空运行态；如果没有这行代码，record_actionability 没地方保存 pending。
    record_actionability_from_tool_result("mcp__computer-use__desktop_task", _desktop_task_incomplete_output(), runtime_state)  # 新增代码+DesktopTaskIncompleteGateTest：记录工具输出；如果没有这行代码，测试不会触发 marker 解析。
    pending = get_pending_actionability(runtime_state)  # 新增代码+DesktopTaskIncompleteGateTest：读取沉淀后的 pending；如果没有这行代码，无法断言运行态。
    assert pending["actionability_kind"] == "desktop_task_incomplete"  # 新增代码+DesktopTaskIncompleteGateTest：确认 pending 类型是桌面任务未完成；如果没有这行代码，错误 marker 也可能过关。
    assert pending["next_required_tool"] == "mcp__computer-use__desktop_task"  # 新增代码+DesktopTaskIncompleteGateTest：确认下一步回到高层任务工具；如果没有这行代码，模型可能继续拆成原子动作。
    assert "mcp__computer-use__observe" in pending["next_allowed_tools"]  # 新增代码+DesktopTaskIncompleteGateTest：确认允许阶段边界观察；如果没有这行代码，修复轮无法先观察当前窗口。
# 新增代码+DesktopTaskIncompleteGateTest：函数段结束，test_desktop_task_incomplete_records_pending_stage_tool 到此结束；如果没有这个边界说明，初学者不容易看出 pending 断言范围。


def test_desktop_task_incomplete_blocks_primitive_action_fallback() -> None:  # 新增代码+DesktopTaskIncompleteGateTest：函数段开始，验证未完成后原子动作会被阻断；如果没有这个测试，key/click/drag 仍可绕过 Stage Runtime。
    runtime_state: dict[str, object] = {}  # 新增代码+DesktopTaskIncompleteGateTest：准备空运行态；如果没有这行代码，pending 无处保存。
    record_actionability_from_tool_result("mcp__computer-use__desktop_task", _desktop_task_incomplete_output(), runtime_state)  # 新增代码+DesktopTaskIncompleteGateTest：写入 desktop_task 未完成状态；如果没有这行代码，后续门禁没有输入。
    pending = get_pending_actionability(runtime_state)  # 新增代码+DesktopTaskIncompleteGateTest：读取当前 pending；如果没有这行代码，阻断函数没有待执行约束。
    assert should_block_tool_for_pending_actionability("mcp__computer-use__key", '{"key":"CTRL+A"}', pending, False) is True  # 新增代码+DesktopTaskIncompleteGateTest：确认键盘原子动作被挡；如果没有这行代码，模型会继续污染真实应用。
    assert should_block_tool_for_pending_actionability("mcp__computer-use__left_click_drag", '{"x":1}', pending, False) is True  # 新增代码+DesktopTaskIncompleteGateTest：确认鼠标拖拽原子动作被挡；如果没有这行代码，绘图/窗口移动会绕过阶段验证。
    assert should_block_tool_for_pending_actionability("mcp__computer-use__desktop_task", '{"prompt":"继续完成"}', pending, False) is False  # 新增代码+DesktopTaskIncompleteGateTest：确认高层任务工具被放行；如果没有这行代码，正确恢复路径也会被误挡。
    assert should_block_tool_for_pending_actionability("mcp__computer-use__observe", '{"action":"get_window_state"}', pending, False) is False  # 新增代码+DesktopTaskIncompleteGateTest：确认观察工具被放行；如果没有这行代码，阶段边界观察无法执行。
# 新增代码+DesktopTaskIncompleteGateTest：函数段结束，test_desktop_task_incomplete_blocks_primitive_action_fallback 到此结束；如果没有这个边界说明，初学者不容易看出门禁断言范围。


def test_desktop_task_incomplete_survives_observe_action_marker() -> None:  # 新增代码+DesktopTaskIncompleteGateTest：函数段开始，验证 Stage 未完成 pending 不会被普通 observe marker 覆盖；如果没有这个测试，observe 后模型又能退回原子动作。
    runtime_state: dict[str, object] = {}  # 新增代码+DesktopTaskIncompleteGateTest：准备运行态；如果没有这行代码，测试没有状态容器。
    record_actionability_from_tool_result("mcp__computer-use__desktop_task", _desktop_task_incomplete_output(), runtime_state)  # 新增代码+DesktopTaskIncompleteGateTest：先写入高层任务未完成 pending；如果没有这行代码，无法复现真实绘图验收的前置状态。
    observe_output = "\nOPENHARNESS_DESKTOP_ACTION_REQUIRED\nactionability_kind=desktop_observe_before_action\nnext_required_tool=observe\nnext_allowed_tools=mcp__computer-use__observe,observe\nnext_required_action=get_window_state\n"  # 新增代码+DesktopTaskIncompleteGateTest：模拟 observe 返回旧动作协议 marker；如果没有这行代码，无法验证 pending 覆盖问题。
    record_actionability_from_tool_result("mcp__computer-use__observe", observe_output, runtime_state)  # 新增代码+DesktopTaskIncompleteGateTest：记录 observe 工具输出；如果没有这行代码，覆盖路径不会触发。
    pending = get_pending_actionability(runtime_state)  # 新增代码+DesktopTaskIncompleteGateTest：读取 observe 后的 pending；如果没有这行代码，无法判断是否被降级。
    assert pending["actionability_kind"] == "desktop_task_incomplete"  # 新增代码+DesktopTaskIncompleteGateTest：确认仍保持高层任务未完成；如果没有这行代码，observe 会把 Stage pending 覆盖掉。
    assert should_block_tool_for_pending_actionability("mcp__computer-use__left_click_drag", '{"points":[]}', pending, False) is True  # 新增代码+DesktopTaskIncompleteGateTest：确认 observe 后仍阻断原子拖拽；如果没有这行代码，复杂绘图任务会再次失控。
# 新增代码+DesktopTaskIncompleteGateTest：函数段结束，test_desktop_task_incomplete_survives_observe_action_marker 到此结束；如果没有这个边界说明，初学者不容易看出覆盖保护范围。
