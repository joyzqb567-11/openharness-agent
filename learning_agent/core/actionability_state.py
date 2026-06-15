"""Computer Use 下一步可行动作状态协议。"""  # 新增代码+ObservePlanActVerify：说明本模块负责保存“看见可操作目标后下一步必须做什么”；如果没有这行代码，维护者不知道该协议放在这里的原因。

from __future__ import annotations  # 新增代码+ObservePlanActVerify：延迟解析类型注解；如果没有这行代码，旧运行方式下部分类型写法更容易受定义顺序影响。

import json  # 新增代码+ObservePlanActVerify：把 pending 状态格式化成模型可读文本；如果没有这行代码，纠偏提示只能手写脆弱字符串。
from typing import Any  # 新增代码+ObservePlanActVerify：标注运行时状态和工具输出的宽松结构；如果没有这行代码，接口边界不清楚。


BROWSER_ACTION_REQUIRED_MARKER = "OPENHARNESS_BROWSER_ACTION_REQUIRED"  # 新增代码+ObservePlanActVerify：浏览器观察后要求真实动作的稳定标记；如果没有这行代码，收束器无法识别 snapshot 已经给出可操作目标。
BROWSER_ACTION_FULFILLED_MARKER = "OPENHARNESS_BROWSER_ACTION_FULFILLED"  # 新增代码+ObservePlanActVerify：浏览器动作完成并要求下一步的稳定标记；如果没有这行代码，输入完成后无法切换到发送或验证。
BROWSER_VERIFY_REQUIRED_MARKER = "OPENHARNESS_BROWSER_VERIFY_REQUIRED"  # 新增代码+ObservePlanActVerify：浏览器提交后要求等待和复查的稳定标记；如果没有这行代码，点击发送后模型可能直接总结而不验证。
DESKTOP_ACTION_REQUIRED_MARKER = "OPENHARNESS_DESKTOP_ACTION_REQUIRED"  # 新增代码+ObservePlanActVerify：桌面观察或启动后要求真实动作的稳定标记；如果没有这行代码，launch 到 observe/action 的链路无法机器解析。
DESKTOP_OBSERVATION_BLOCKED_MARKER = "OPENHARNESS_DESKTOP_OBSERVATION_BLOCKED"  # 新增代码+ObservePlanActVerify：桌面观察无法继续时的稳定阻塞标记；如果没有这行代码，工具失败和外部环境阻塞会混在一起。
ACTIONABILITY_PENDING_KEY = "actionability_pending"  # 新增代码+ObservePlanActVerify：runtime_state 中保存下一步动作的统一键；如果没有这行代码，各模块会用散落字符串导致状态不互通。
ACTIONABILITY_LAST_BLOCK_KEY = "actionability_last_block"  # 新增代码+ObservePlanActVerify：runtime_state 中保存最近阻塞原因的统一键；如果没有这行代码，最终报告无法解释为什么没有继续动作。
ACTIONABILITY_LAST_CLEARED_KEY = "actionability_last_cleared"  # 新增代码+ObservePlanActVerify：runtime_state 中保存最近清理原因的统一键；如果没有这行代码，pending 消失时缺少审计线索。
ACTIONABILITY_MARKERS = {BROWSER_ACTION_REQUIRED_MARKER, BROWSER_ACTION_FULFILLED_MARKER, BROWSER_VERIFY_REQUIRED_MARKER, DESKTOP_ACTION_REQUIRED_MARKER, DESKTOP_OBSERVATION_BLOCKED_MARKER}  # 新增代码+ObservePlanActVerify：集中列出所有 marker；如果没有这行代码，解析函数要到处重复硬编码。
ACTIONABILITY_ALLOWED_FIELDS = {  # 新增代码+ObservePlanActVerify：字段白名单段开始，只保存动作必需的低敏字段；如果没有这段代码，网页标签或用户输入可能被放进长期状态。
    "actionability_kind",  # 新增代码+ObservePlanActVerify：允许保存动作分类；如果没有这行代码，后续报告不知道 pending 属于浏览器还是桌面。
    "next_required_tool",  # 新增代码+ObservePlanActVerify：允许保存下一步工具名；如果没有这行代码，收束器无法告诉模型该调用哪个工具。
    "next_allowed_tools",  # 修改代码+ComputerUseMcpV2ResidualCleanup：允许保存一组 v2 MCP 原子工具；如果没有这行代码，桌面观察后只能继续要求已隐藏的旧 computer_action。
    "next_required_action",  # 新增代码+ObservePlanActVerify：允许保存下一步工具里的 action 参数；如果没有这行代码，computer_observe 这类多动作工具缺少具体指令。
    "next_required_reason",  # 新增代码+ObservePlanActVerify：允许保存低敏原因码；如果没有这行代码，纠偏提示只能说“继续动作”而不解释为什么。
    "next_required_after_wait",  # 新增代码+ObservePlanActVerify：允许保存等待后的复查工具；如果没有这行代码，点击发送后的 wait->snapshot 链路会断。
    "page_id",  # 新增代码+ObservePlanActVerify：允许保存浏览器页面 id；如果没有这行代码，下一步浏览器动作可能打到错误标签页。
    "element_id",  # 新增代码+ObservePlanActVerify：允许保存浏览器元素 id；如果没有这行代码，模型仍要重新查找输入框或按钮。
    "submit_candidate_tool",  # 新增代码+ObservePlanActVerify：允许保存输入后的提交工具；如果没有这行代码，browser_type 后不知道该 click 还是 press_key。
    "submit_candidate_element_id",  # 新增代码+ObservePlanActVerify：允许保存提交按钮 id；如果没有这行代码，发送动作仍需重新定位。
    "fulfilled_tool",  # 新增代码+ObservePlanActVerify：允许保存刚完成的工具；如果没有这行代码，审计无法知道 pending 是由哪一步推进的。
    "input_verified",  # 新增代码+ObservePlanActVerify：允许保存输入验证状态；如果没有这行代码，输入假成功和真成功难以区分。
    "target_ref",  # 新增代码+ObservePlanActVerify：允许保存桌面目标引用；如果没有这行代码，下一步 observe/action 可能失去绑定窗口。
    "external_app_window_bound",  # 新增代码+ObservePlanActVerify：允许保存真实外部窗口绑定布尔值；如果没有这行代码，桌面链路无法证明不是模拟窗口。
    "proxy_window_bound",  # 新增代码+ObservePlanActVerify：允许保存代理窗口绑定布尔值；如果没有这行代码，窗口代理链路无法被验收。
    "screenshot_captured",  # 新增代码+ObservePlanActVerify：允许保存截图证据是否存在；如果没有这行代码，桌面观察是否可见无法判断。
    "uia_tree_observation",  # 新增代码+ObservePlanActVerify：允许保存 UIA 树是否可读；如果没有这行代码，桌面观察能力缺少结构化证据。
    "key",  # 新增代码+ObservePlanActVerify：允许保存低敏按键名；如果没有这行代码，无发送按钮时无法要求 Enter 提交。
    "block_class",  # 新增代码+ObservePlanActVerify：允许保存阻塞分类；如果没有这行代码，工具失败和外部限制无法区分。
    "block_reason",  # 新增代码+ObservePlanActVerify：允许保存低敏阻塞原因码；如果没有这行代码，失败报告不可诊断。
}  # 新增代码+ObservePlanActVerify：字段白名单段结束；如果没有这行代码，Python 集合语法不完整。
BYPASSABLE_TOOL_NAMES = {"bash", "read", "read_file", "write", "edit", "write_file"}  # 新增代码+ObservePlanActVerify：定义可能绕过真实动作的工具集合；如果没有这行代码，模型会从可操作状态漂移到读日志或写 fallback。


def normalize_actionability_tool_name(tool_name: str) -> str:  # 新增代码+ObservePlanActVerify：函数段开始，统一 MCP 和本地工具名；如果没有这段函数，mcp__browser_automation__browser_type 无法匹配 browser_type。
    raw_name = str(tool_name or "").strip()  # 新增代码+ObservePlanActVerify：把输入转成干净字符串；如果没有这行代码，None 或空白会导致匹配混乱。
    if raw_name.startswith("mcp__browser_automation__"):  # 新增代码+ObservePlanActVerify：识别浏览器 MCP 工具前缀；如果没有这行代码，浏览器工具无法按短名进入 pending 规则。
        return raw_name.removeprefix("mcp__browser_automation__")  # 新增代码+ObservePlanActVerify：返回 browser_snapshot/browser_type 这类短名；如果没有这行代码，下一步工具名会和 marker 不一致。
    if raw_name.startswith("mcp__"):  # 新增代码+ObservePlanActVerify：兼容其他 MCP 工具名前缀；如果没有这行代码，未来 MCP 工具会带着整段前缀参与比较。
        return raw_name.split("__")[-1]  # 新增代码+ObservePlanActVerify：取最后一段作为短名；如果没有这行代码，通用 MCP 工具比较会过于脆弱。
    return raw_name  # 新增代码+ObservePlanActVerify：普通工具名原样返回；如果没有这行代码，本地 bash/computer_action 无法匹配。
    # 新增代码+ObservePlanActVerify：函数段结束，normalize_actionability_tool_name 到此结束；如果没有这个边界说明，用户不容易看出工具名归一范围。

def _actionability_tool_name_choices(raw_tools: Any) -> set[str]:  # 修改代码+ComputerUseMcpV2ResidualCleanup：函数段开始，把单个或多个工具名统一成可匹配短名集合；如果没有这段函数，完整 MCP 名会被 pending gate 当成不同工具。
    if isinstance(raw_tools, (list, tuple, set)):  # 修改代码+ComputerUseMcpV2ResidualCleanup：兼容结构化列表形式的工具名；如果没有这行代码，未来 adapter 写入列表时会被当成普通字符串。
        items = [str(item or "").strip() for item in raw_tools]  # 修改代码+ComputerUseMcpV2ResidualCleanup：清理列表中的空白工具名；如果没有这行代码，空值会污染允许集合。
    else:  # 修改代码+ComputerUseMcpV2ResidualCleanup：兼容当前 key=value 协议里的逗号分隔字符串；如果没有这行代码，旧文本协议无法表达多个 v2 工具。
        items = [part.strip() for part in str(raw_tools or "").replace(";", ",").split(",")]  # 修改代码+ComputerUseMcpV2ResidualCleanup：支持逗号和分号分隔；如果没有这行代码，left_click/type/key 等集合无法稳定解析。
    return {normalize_actionability_tool_name(item) for item in items if item}  # 修改代码+ComputerUseMcpV2ResidualCleanup：输出归一后的短名集合；如果没有这行代码，mcp__computer-use__left_click 不能匹配实际调用。
    # 修改代码+ComputerUseMcpV2ResidualCleanup：函数段结束，_actionability_tool_name_choices 到此结束；如果没有这个边界说明，用户不容易看出多工具白名单范围。


def _runtime_dict(runtime_state: dict[str, Any] | None) -> dict[str, Any]:  # 新增代码+ObservePlanActVerify：函数段开始，确保运行态是可写 dict；如果没有这段函数，None 状态会让记录函数崩溃。
    return runtime_state if isinstance(runtime_state, dict) else {}  # 新增代码+ObservePlanActVerify：非 dict 时返回空 dict；如果没有这行代码，调用方需要到处防御 None。
    # 新增代码+ObservePlanActVerify：函数段结束，_runtime_dict 到此结束；如果没有这个边界说明，读者不容易看出它只做安全适配。


def _parse_actionability_fields(output_text: str) -> tuple[str, dict[str, str]]:  # 新增代码+ObservePlanActVerify：函数段开始，从工具文本里解析 marker 和 key=value；如果没有这段函数，协议解析会散落在多个模块。
    marker = ""  # 新增代码+ObservePlanActVerify：默认没有发现 marker；如果没有这行代码，后续返回值可能未定义。
    fields: dict[str, str] = {}  # 新增代码+ObservePlanActVerify：准备保存解析出的低敏字段；如果没有这行代码，字段没有容器。
    for raw_line in str(output_text or "").splitlines():  # 新增代码+ObservePlanActVerify：逐行扫描工具输出；如果没有这行代码，多行协议无法解析。
        line = raw_line.strip()  # 新增代码+ObservePlanActVerify：去掉行首尾空白；如果没有这行代码，缩进或空格会导致 marker 匹配失败。
        if not line:  # 新增代码+ObservePlanActVerify：跳过空行；如果没有这行代码，空行会进入后续判断浪费处理。
            continue  # 新增代码+ObservePlanActVerify：继续扫描下一行；如果没有这行代码，空行会造成无意义解析。
        if line in ACTIONABILITY_MARKERS:  # 新增代码+ObservePlanActVerify：识别稳定 marker 行；如果没有这行代码，解析器不知道当前输出是哪类协议。
            marker = line  # 新增代码+ObservePlanActVerify：记录最后一个 marker；如果没有这行代码，调用方无法知道应该更新还是清理 pending。
            continue  # 新增代码+ObservePlanActVerify：marker 行不再当 key=value 解析；如果没有这行代码，marker 会被错误处理。
        if "=" not in line:  # 新增代码+ObservePlanActVerify：只解析 key=value 行；如果没有这行代码，普通工具文本会污染字段。
            continue  # 新增代码+ObservePlanActVerify：跳过普通描述行；如果没有这行代码，解析器可能误读自然语言。
        key, value = line.split("=", 1)  # 新增代码+ObservePlanActVerify：按第一个等号拆分字段；如果没有这行代码，value 中带等号会被截断。
        clean_key = key.strip()  # 新增代码+ObservePlanActVerify：清洗字段名；如果没有这行代码，空格会导致白名单匹配失败。
        clean_value = value.strip()  # 新增代码+ObservePlanActVerify：清洗字段值；如果没有这行代码，提示里会出现多余空白。
        if clean_key in ACTIONABILITY_ALLOWED_FIELDS and clean_value:  # 新增代码+ObservePlanActVerify：只保存白名单且非空字段；如果没有这行代码，网页标签和用户文本可能进入 runtime_state。
            fields[clean_key] = clean_value  # 新增代码+ObservePlanActVerify：写入安全字段；如果没有这行代码，pending 缺少可执行参数。
    return marker, fields  # 新增代码+ObservePlanActVerify：返回 marker 和字段；如果没有这行代码，调用方拿不到解析结果。
    # 新增代码+ObservePlanActVerify：函数段结束，_parse_actionability_fields 到此结束；如果没有这个边界说明，用户不容易看出解析边界。


def _bool_text(value: Any) -> str:  # 新增代码+ObservePlanActVerify：函数段开始，把布尔值转成协议 token；如果没有这段函数，True/False 大小写会不稳定。
    return "true" if bool(value) else "false"  # 新增代码+ObservePlanActVerify：返回小写布尔字符串；如果没有这行代码，验收器需要兼容多种写法。
    # 新增代码+ObservePlanActVerify：函数段结束，_bool_text 到此结束；如果没有这个边界说明，读者不容易看出它只做格式化。


def clear_pending_actionability(runtime_state: dict[str, Any] | None, reason: str = "") -> None:  # 新增代码+ObservePlanActVerify：函数段开始，清理已完成或阻塞的 pending；如果没有这段函数，旧下一步动作会误挡后续正常工具。
    state = _runtime_dict(runtime_state)  # 新增代码+ObservePlanActVerify：取得可写运行态；如果没有这行代码，None 状态会导致 pop 崩溃。
    state.pop(ACTIONABILITY_PENDING_KEY, None)  # 新增代码+ObservePlanActVerify：删除当前 pending；如果没有这行代码，已完成动作仍会被当成未完成。
    state[ACTIONABILITY_LAST_CLEARED_KEY] = str(reason or "cleared")  # 新增代码+ObservePlanActVerify：记录清理原因；如果没有这行代码，状态变化缺少审计解释。
    # 新增代码+ObservePlanActVerify：函数段结束，clear_pending_actionability 到此结束；如果没有这个边界说明，用户不容易看出清理范围。


def get_pending_actionability(runtime_state: dict[str, Any] | None) -> dict[str, str]:  # 新增代码+ObservePlanActVerify：函数段开始，读取当前下一步动作；如果没有这段函数，各模块会直接读写内部键。
    state = _runtime_dict(runtime_state)  # 新增代码+ObservePlanActVerify：取得运行态；如果没有这行代码，None 状态读取会失败。
    pending = state.get(ACTIONABILITY_PENDING_KEY)  # 新增代码+ObservePlanActVerify：读取 pending 原始对象；如果没有这行代码，无法判断是否已有下一步动作。
    return dict(pending) if isinstance(pending, dict) else {}  # 新增代码+ObservePlanActVerify：返回副本避免外部误改内部状态；如果没有这行代码，调用方可能直接污染 runtime_state。
    # 新增代码+ObservePlanActVerify：函数段结束，get_pending_actionability 到此结束；如果没有这个边界说明，读者不容易看出它是只读副本。


def _store_pending_actionability(runtime_state: dict[str, Any] | None, marker: str, fields: dict[str, str], source_tool_name: str) -> None:  # 新增代码+ObservePlanActVerify：函数段开始，保存解析后的下一步动作；如果没有这段函数，状态写入规则会散落。
    state = _runtime_dict(runtime_state)  # 新增代码+ObservePlanActVerify：取得可写运行态；如果没有这行代码，保存 pending 时可能因 None 崩溃。
    pending = dict(fields)  # 新增代码+ObservePlanActVerify：复制字段避免修改解析器返回对象；如果没有这行代码，后续补字段会产生隐式副作用。
    pending["marker"] = marker  # 新增代码+ObservePlanActVerify：保存来源 marker；如果没有这行代码，后续审计不知道 pending 来自哪类工具输出。
    pending["source_tool_name"] = normalize_actionability_tool_name(source_tool_name)  # 新增代码+ObservePlanActVerify：保存短工具名；如果没有这行代码，审计和匹配会受 MCP 前缀影响。
    if pending.get("next_required_tool") == "browser_click" and pending.get("submit_candidate_element_id") and not pending.get("element_id"):  # 新增代码+ObservePlanActVerify：输入完成后把提交候选提升为点击目标；如果没有这行代码，模型还要自己转换字段。
        pending["element_id"] = pending["submit_candidate_element_id"]  # 新增代码+ObservePlanActVerify：补齐 browser_click 可直接使用的 element_id；如果没有这行代码，收束提示不够可执行。
    if marker == BROWSER_VERIFY_REQUIRED_MARKER:  # 新增代码+ObservePlanActVerify：点击或回车提交后进入验证阶段；如果没有这行代码，提交后无法自动要求等待。
        pending.setdefault("actionability_kind", "browser_post_submit_verify")  # 新增代码+ObservePlanActVerify：补齐浏览器提交验证分类；如果没有这行代码，pending 类型可能为空。
        pending.setdefault("next_required_tool", "browser_wait")  # 新增代码+ObservePlanActVerify：默认下一步先等待页面生成结果；如果没有这行代码，提交后可能立刻 snapshot 导致页面还没更新。
        pending.setdefault("next_required_after_wait", "browser_snapshot")  # 新增代码+ObservePlanActVerify：默认等待后复查快照；如果没有这行代码，等待完成后不知道如何验证结果。
    state[ACTIONABILITY_PENDING_KEY] = pending  # 新增代码+ObservePlanActVerify：写入 runtime_state 供收束器使用；如果没有这行代码，marker 只会停留在工具文本里。
    # 新增代码+ObservePlanActVerify：函数段结束，_store_pending_actionability 到此结束；如果没有这个边界说明，用户不容易看出保存逻辑边界。


def _advance_pending_after_matching_tool(tool_name: str, runtime_state: dict[str, Any] | None) -> None:  # 新增代码+ObservePlanActVerify：函数段开始，处理无 marker 但工具名匹配的完成推进；如果没有这段函数，browser_wait 后不会自动切到 snapshot。
    state = _runtime_dict(runtime_state)  # 新增代码+ObservePlanActVerify：取得可写运行态；如果没有这行代码，状态推进无法保存。
    pending = get_pending_actionability(state)  # 新增代码+ObservePlanActVerify：读取当前 pending 副本；如果没有这行代码，无法知道是否有待完成动作。
    normalized_tool = normalize_actionability_tool_name(tool_name)  # 新增代码+ObservePlanActVerify：归一化本次工具名；如果没有这行代码，MCP 前缀会导致匹配失败。
    if not pending or normalized_tool not in _actionability_tool_name_choices(pending.get("next_required_tool", "")):  # 修改代码+ComputerUseMcpV2ResidualCleanup：用归一化后的必需工具集合判断完成；如果没有这行代码，mcp__computer-use__observe 完成后 pending 不会推进。
        return  # 新增代码+ObservePlanActVerify：不匹配则不做任何修改；如果没有这行代码，后续逻辑会错误推进。
    after_wait_tool = str(pending.get("next_required_after_wait", "") or "").strip()  # 新增代码+ObservePlanActVerify：读取等待后目标工具；如果没有这行代码，browser_wait 完成后无法知道下一步。
    if normalized_tool == "browser_wait" and after_wait_tool:  # 新增代码+ObservePlanActVerify：等待工具完成且存在后续复查时推进到复查；如果没有这行代码，验证链会停在 wait。
        pending["next_required_tool"] = after_wait_tool  # 新增代码+ObservePlanActVerify：把下一步改成 browser_snapshot；如果没有这行代码，模型不会收到复查要求。
        pending["actionability_kind"] = "browser_post_wait_verify"  # 新增代码+ObservePlanActVerify：更新分类为等待后验证；如果没有这行代码，审计看不出阶段变化。
        pending.pop("next_required_after_wait", None)  # 新增代码+ObservePlanActVerify：删除已消费的后续工具字段；如果没有这行代码，状态会反复推进同一字段。
        state[ACTIONABILITY_PENDING_KEY] = pending  # 新增代码+ObservePlanActVerify：写回推进后的 pending；如果没有这行代码，运行态不会更新。
        return  # 新增代码+ObservePlanActVerify：推进完成后退出；如果没有这行代码，后面会把刚推进的 pending 清掉。
    clear_pending_actionability(state, f"fulfilled_by_{normalized_tool}")  # 新增代码+ObservePlanActVerify：普通匹配工具完成后清理 pending；如果没有这行代码，已执行的下一步还会继续阻挡其他工具。
    # 新增代码+ObservePlanActVerify：函数段结束，_advance_pending_after_matching_tool 到此结束；如果没有这个边界说明，用户不容易看出推进规则。


def _tool_output_indicates_required_action_failure(output_text: str) -> bool:  # 新增代码+PendingFailureRetention：函数段开始，判断工具输出是否代表必需动作没有完成；如果没有这段函数，失败输出会被误当成功。
    lowered = str(output_text or "").lower()  # 新增代码+PendingFailureRetention：转小写便于匹配英文错误片段；如果没有这行代码，大小写变化会漏判。
    if "工具调用失败" in str(output_text or ""):  # 新增代码+PendingFailureRetention：识别 OpenHarness 包装的工具失败中文前缀；如果没有这行代码，真实 MCP 失败会清空 pending。
        return True  # 新增代码+PendingFailureRetention：确认这是失败输出；如果没有这行代码，调用方不会保留 pending。
    if "mcp request tools/call failed" in lowered:  # 新增代码+PendingFailureRetention：识别 MCP 协议层失败；如果没有这行代码，外部工具报错仍可能被当完成。
        return True  # 新增代码+PendingFailureRetention：确认这是失败输出；如果没有这行代码，状态不会记录 tool_failure。
    if "traceback" in lowered:  # 新增代码+PendingFailureRetention：识别 Python 异常堆栈；如果没有这行代码，脚本工具失败可能误推进。
        return True  # 新增代码+PendingFailureRetention：确认异常输出不是完成证据；如果没有这行代码，pending 会被错误清理。
    if "input_verified=false" in lowered:  # 新增代码+PendingFailureRetention：识别输入读回验证失败；如果没有这行代码，网页聊天框没填上也可能进入发送阶段。
        return True  # 新增代码+PendingFailureRetention：确认输入未完成；如果没有这行代码，后续 Enter 可能误提交空消息。
    return False  # 新增代码+PendingFailureRetention：没有失败特征则认为可走原推进逻辑；如果没有这行代码，函数缺少成功出口。
    # 新增代码+PendingFailureRetention：函数段结束，_tool_output_indicates_required_action_failure 到此结束；如果没有这个边界说明，用户不容易看出失败识别范围。


def _retain_pending_after_required_tool_failure(tool_name: str, output_text: str, runtime_state: dict[str, Any] | None) -> bool:  # 新增代码+PendingFailureRetention：函数段开始，必需工具失败时保留 pending；如果没有这段函数，失败会被当成完成。
    state = _runtime_dict(runtime_state)  # 新增代码+PendingFailureRetention：取得可写运行态；如果没有这行代码，无法保存失败审计。
    pending = get_pending_actionability(state)  # 新增代码+PendingFailureRetention：读取当前 pending；如果没有这行代码，不知道是否存在必需动作。
    normalized_tool = normalize_actionability_tool_name(tool_name)  # 新增代码+PendingFailureRetention：归一化工具名；如果没有这行代码，MCP 前缀会导致匹配失败。
    if not pending or normalized_tool not in _actionability_tool_name_choices(pending.get("next_required_tool", "")):  # 修改代码+ComputerUseMcpV2ResidualCleanup：用归一化后的必需工具集合判断失败保留；如果没有这行代码，完整 MCP 名失败会被当成无关失败。
        return False  # 新增代码+PendingFailureRetention：返回未处理；如果没有这行代码，调用方无法继续普通流程。
    if not _tool_output_indicates_required_action_failure(output_text):  # 新增代码+PendingFailureRetention：没有失败特征时不拦截推进；如果没有这行代码，成功工具也会被困在 pending。
        return False  # 新增代码+PendingFailureRetention：返回未处理；如果没有这行代码，成功路径会被误挡。
    block = dict(pending)  # 新增代码+PendingFailureRetention：复制 pending 作为失败审计基础；如果没有这行代码，直接改 pending 副本会不清晰。
    block["block_class"] = "tool_failure"  # 新增代码+PendingFailureRetention：记录失败分类；如果没有这行代码，最终报告无法区分外部阻塞和工具失败。
    block["block_reason"] = "required_tool_failed"  # 新增代码+PendingFailureRetention：记录稳定原因码；如果没有这行代码，验收矩阵难以统计。
    block["failed_tool"] = normalized_tool  # 新增代码+PendingFailureRetention：记录失败工具名；如果没有这行代码，排查时不知道是哪一步没完成。
    block["failure_preview"] = str(output_text or "")[:240]  # 新增代码+PendingFailureRetention：保存短失败预览；如果没有这行代码，后续日志要重新翻大段输出。
    state[ACTIONABILITY_LAST_BLOCK_KEY] = block  # 新增代码+PendingFailureRetention：写入最近阻塞状态；如果没有这行代码，最终回答缺少失败解释来源。
    state[ACTIONABILITY_PENDING_KEY] = pending  # 新增代码+PendingFailureRetention：显式保留原 pending；如果没有这行代码，失败后下一轮没有纠偏目标。
    return True  # 新增代码+PendingFailureRetention：告诉调用方失败已处理且不能推进；如果没有这行代码，后面仍会清理 pending。
    # 新增代码+PendingFailureRetention：函数段结束，_retain_pending_after_required_tool_failure 到此结束；如果没有这个边界说明，用户不容易看出它只负责失败保留。


def record_actionability_from_tool_result(tool_name: str, output_text: str, runtime_state: dict[str, Any] | None) -> None:  # 新增代码+ObservePlanActVerify：函数段开始，从工具结果沉淀下一步动作状态；如果没有这段函数，工具 marker 无法控制后续模型行为。
    marker, fields = _parse_actionability_fields(output_text)  # 新增代码+ObservePlanActVerify：解析工具输出里的 marker 和字段；如果没有这行代码，后续无法判断该保存还是清理。
    if not marker:  # 新增代码+ObservePlanActVerify：没有 marker 时走普通完成推进；如果没有这行代码，无 marker 工具会被误当 actionability 输出。
        if _retain_pending_after_required_tool_failure(tool_name, output_text, runtime_state):  # 新增代码+PendingFailureRetention：必需工具失败时保留 pending；如果没有这行代码，browser_type 失败会被误当完成。
            return  # 新增代码+PendingFailureRetention：失败保留后结束处理；如果没有这行代码，后续推进会清空 pending。
        _advance_pending_after_matching_tool(tool_name, runtime_state)  # 新增代码+ObservePlanActVerify：如果刚好完成 pending，就清理或推进；如果没有这行代码，browser_wait 后续验证链会卡住。
        return  # 新增代码+ObservePlanActVerify：无 marker 情况处理完毕；如果没有这行代码，下面会错误保存空 marker。
    if marker == DESKTOP_OBSERVATION_BLOCKED_MARKER:  # 新增代码+ObservePlanActVerify：桌面观察明确阻塞时不再要求盲动；如果没有这行代码，工具无法观察时模型仍可能硬操作。
        state = _runtime_dict(runtime_state)  # 新增代码+ObservePlanActVerify：取得可写状态；如果没有这行代码，阻塞原因没有保存位置。
        state[ACTIONABILITY_LAST_BLOCK_KEY] = dict(fields, marker=marker, source_tool_name=normalize_actionability_tool_name(tool_name))  # 新增代码+ObservePlanActVerify：保存阻塞摘要；如果没有这行代码，最终结果无法解释为什么停下。
        clear_pending_actionability(state, "desktop_observation_blocked")  # 新增代码+ObservePlanActVerify：清理旧 pending；如果没有这行代码，阻塞后仍会要求继续动作。
        return  # 新增代码+ObservePlanActVerify：阻塞处理完毕；如果没有这行代码，下面会把阻塞也当成 pending。
    _store_pending_actionability(runtime_state, marker, fields, tool_name)  # 新增代码+ObservePlanActVerify：保存下一步动作；如果没有这行代码，收束控制看不到工具提供的行动要求。
    # 新增代码+ObservePlanActVerify：函数段结束，record_actionability_from_tool_result 到此结束；如果没有这个边界说明，用户不容易看出状态入口。


def actionability_allowed_tool_names(pending: dict[str, Any]) -> set[str]:  # 新增代码+ObservePlanActVerify：函数段开始，列出 pending 状态下允许的工具；如果没有这段函数，阻断规则会写死且难扩展。
    required_tool = str(pending.get("next_required_tool", "") or "").strip()  # 新增代码+ObservePlanActVerify：读取下一步工具；如果没有这行代码，无法构造允许列表。
    allowed = _actionability_tool_name_choices(required_tool) if required_tool else set()  # 修改代码+ComputerUseMcpV2ResidualCleanup：默认允许必需工具并统一 MCP 前缀；如果没有这行代码，v2 observe/left_click 会被错误阻断。
    allowed.update(_actionability_tool_name_choices(pending.get("next_allowed_tools", "")))  # 修改代码+ComputerUseMcpV2ResidualCleanup：合并 v2 原子动作允许集合；如果没有这行代码，模型仍会被诱导调用隐藏旧 computer_action。
    after_wait_tool = str(pending.get("next_required_after_wait", "") or "").strip()  # 新增代码+ObservePlanActVerify：读取等待后工具；如果没有这行代码，等待阶段不能温和允许复查。
    if after_wait_tool:  # 新增代码+ObservePlanActVerify：存在等待后工具时加入允许集合；如果没有这行代码，直接复查的模型会被过度阻断。
        allowed.update(_actionability_tool_name_choices(after_wait_tool))  # 修改代码+ComputerUseMcpV2ResidualCleanup：等待后的工具也统一归一；如果没有这行代码，完整 MCP 名无法完成 wait->observe 链。
    if str(pending.get("actionability_kind", "")).startswith("browser_"):  # 新增代码+ObservePlanActVerify：浏览器 pending 允许查看标签上下文；如果没有这行代码，标签页切换必要信息会被误挡。
        allowed.add("browser_tabs_context")  # 新增代码+ObservePlanActVerify：加入浏览器标签上下文工具；如果没有这行代码，多标签任务可能不能确认当前页。
    return {tool for tool in allowed if tool}  # 新增代码+ObservePlanActVerify：过滤空工具名并返回集合；如果没有这行代码，空字符串会污染匹配。
    # 新增代码+ObservePlanActVerify：函数段结束，actionability_allowed_tool_names 到此结束；如果没有这个边界说明，用户不容易看出允许规则。


def actionability_tool_matches_required(tool_name: str, pending: dict[str, Any]) -> bool:  # 新增代码+ObservePlanActVerify：函数段开始，判断本次工具是否满足 pending；如果没有这段函数，收束器要重复比较逻辑。
    normalized_tool = normalize_actionability_tool_name(tool_name)  # 新增代码+ObservePlanActVerify：归一化工具名；如果没有这行代码，MCP 前缀会导致正确工具被误挡。
    return normalized_tool in actionability_allowed_tool_names(pending)  # 新增代码+ObservePlanActVerify：检查工具是否在允许集合；如果没有这行代码，调用方无法获得布尔结果。
    # 新增代码+ObservePlanActVerify：函数段结束，actionability_tool_matches_required 到此结束；如果没有这个边界说明，读者不容易看出匹配范围。


def pending_actionability_argument_mismatch(tool_name: str, tool_arguments: Any, pending: dict[str, Any]) -> str:  # 新增代码+PendingArgumentGate：函数段开始，检查正确工具是否用了错误的 pending 参数；如果没有这段函数，模型会把旧 element_id 填到错误按钮。
    if not pending:  # 新增代码+PendingArgumentGate：没有 pending 时不检查参数；如果没有这行代码，普通工具调用会被误判。
        return ""  # 新增代码+PendingArgumentGate：返回空字符串表示没有不匹配；如果没有这行代码，调用方无法区分通过和失败。
    if not actionability_tool_matches_required(tool_name, pending):  # 新增代码+PendingArgumentGate：只有工具本身符合 pending 时才检查参数；如果没有这行代码，错误工具会重复得到参数错误而不是工具错误。
        return ""  # 新增代码+PendingArgumentGate：工具不匹配时交给原有工具门禁处理；如果没有这行代码，职责会混乱。
    if not isinstance(tool_arguments, dict):  # 新增代码+PendingArgumentGate：参数不是字典时暂不做字段比对；如果没有这行代码，字符串参数会导致 get 属性错误。
        return ""  # 新增代码+PendingArgumentGate：无法结构化比对时放行给底层工具处理；如果没有这行代码，兼容性会下降。
    normalized_tool = normalize_actionability_tool_name(tool_name)  # 新增代码+PendingArgumentGate：拿到短工具名用于分支判断；如果没有这行代码，MCP 前缀会让 browser_type 分支失效。
    expected_page_id = str(pending.get("page_id", "") or "").strip()  # 新增代码+PendingArgumentGate：读取观察阶段给出的页面 id；如果没有这行代码，多标签任务无法防止打错页。
    actual_page_id = str(tool_arguments.get("page_id", "") or "").strip()  # 新增代码+PendingArgumentGate：读取本次工具调用传入的页面 id；如果没有这行代码，无法发现 page_id 漂移。
    if expected_page_id and actual_page_id and actual_page_id != expected_page_id:  # 新增代码+PendingArgumentGate：当两边都有 page_id 且不一致时判定错误；如果没有这行代码，真实 Chrome 可能在错误标签页输入。
        return f"page_id 参数不匹配，必须使用 page_id={expected_page_id}，当前传入 page_id={actual_page_id}。"  # 新增代码+PendingArgumentGate：返回人能看懂的纠偏原因；如果没有这行代码，模型不知道如何修复参数。
    expected_element_id = str(pending.get("element_id", "") or "").strip()  # 新增代码+PendingArgumentGate：读取观察阶段给出的元素 id；如果没有这行代码，无法防止 e32 这类旧 id 被误用。
    actual_element_id = str(tool_arguments.get("element_id", "") or "").strip()  # 新增代码+PendingArgumentGate：读取本次工具调用传入的元素 id；如果没有这行代码，元素比对没有输入。
    if normalized_tool in {"browser_type", "browser_click"} and expected_element_id and actual_element_id and actual_element_id != expected_element_id:  # 新增代码+PendingArgumentGate：浏览器输入/点击必须尊重 pending 元素 id；如果没有这行代码，千问输入框会再次被错误按钮替代。
        return f"element_id 参数不匹配，必须使用 element_id={expected_element_id}，当前传入 element_id={actual_element_id}。"  # 新增代码+PendingArgumentGate：返回正确元素 id；如果没有这行代码，纠偏提示不够可执行。
    expected_action = str(pending.get("next_required_action", "") or "").strip()  # 新增代码+PendingArgumentGate：读取桌面工具所需 action；如果没有这行代码，computer_observe/action 可能执行错动作。
    actual_action = str(tool_arguments.get("action", "") or "").strip()  # 新增代码+PendingArgumentGate：读取本次桌面工具 action；如果没有这行代码，无法比对桌面动作。
    if expected_action and actual_action and actual_action != expected_action:  # 新增代码+PendingArgumentGate：当桌面 action 不一致时判定错误；如果没有这行代码，网易云任务可能观察/动作阶段错位。
        return f"action 参数不匹配，必须使用 action={expected_action}，当前传入 action={actual_action}。"  # 新增代码+PendingArgumentGate：返回正确 action；如果没有这行代码，模型不知道该换哪个参数。
    expected_target_ref = str(pending.get("target_ref", "") or "").strip()  # 新增代码+PendingArgumentGate：读取桌面窗口引用；如果没有这行代码，真实外部软件可能被操作到错误窗口。
    actual_target_ref = str(tool_arguments.get("target_ref", "") or "").strip()  # 新增代码+PendingArgumentGate：读取本次工具调用窗口引用；如果没有这行代码，无法发现窗口漂移。
    if expected_target_ref and actual_target_ref and actual_target_ref != expected_target_ref:  # 新增代码+PendingArgumentGate：当窗口引用不一致时阻断；如果没有这行代码，多窗口桌面任务容易打错应用。
        return f"target_ref 参数不匹配，必须使用 target_ref={expected_target_ref}，当前传入 target_ref={actual_target_ref}。"  # 新增代码+PendingArgumentGate：返回正确窗口引用；如果没有这行代码，纠偏不可执行。
    return ""  # 新增代码+PendingArgumentGate：所有已提供关键参数都匹配则返回空；如果没有这行代码，函数缺少成功出口。
    # 新增代码+PendingArgumentGate：函数段结束，pending_actionability_argument_mismatch 到此结束；如果没有这个边界说明，用户不容易看出它只做参数门禁。


def pending_actionability_message(pending: dict[str, Any]) -> str:  # 新增代码+ObservePlanActVerify：函数段开始，把 pending 转成模型可执行提示；如果没有这段函数，阻断输出无法稳定提示下一步。
    safe_pending = {key: value for key, value in dict(pending).items() if key in ACTIONABILITY_ALLOWED_FIELDS or key in {"marker", "source_tool_name"}}  # 新增代码+ObservePlanActVerify：只输出低敏字段；如果没有这行代码，提示可能泄露网页标签或用户输入。
    pending_json = json.dumps(safe_pending, ensure_ascii=False, sort_keys=True)  # 新增代码+ObservePlanActVerify：把 pending 排序成稳定 JSON；如果没有这行代码，测试和日志难以稳定比对。
    key_value_lines = "\n".join(f"{key}={value}" for key, value in safe_pending.items())  # 新增代码+ObservePlanActVerify：额外输出可直接复制的 key=value 参数行；如果没有这一行，模型可能需要从 JSON 里二次改写 element_id。
    return f"actionability_controller: 已存在必须优先完成的真实动作，请先调用 next_required_tool，不要改去读日志或写本地替代文件。pending={pending_json}\n{key_value_lines}"  # 修改代码+ObservePlanActVerify：同时返回 JSON 和 key=value 纠偏；如果没有这行代码，模型不知道为什么被拦和下一步怎么做。
    # 新增代码+ObservePlanActVerify：函数段结束，pending_actionability_message 到此结束；如果没有这个边界说明，读者不容易看出提示构造范围。


def should_block_tool_for_pending_actionability(tool_name: str, tool_call_text: str, pending: dict[str, Any], user_debug_intent: bool) -> bool:  # 新增代码+ObservePlanActVerify：函数段开始，判断 pending 下是否阻断绕行工具；如果没有这段函数，读日志跑偏 bug 会复发。
    if not pending:  # 新增代码+ObservePlanActVerify：没有 pending 时不阻断；如果没有这行代码，普通任务也可能被误挡。
        return False  # 新增代码+ObservePlanActVerify：返回不阻断；如果没有这行代码，空 pending 会继续进入错误逻辑。
    if user_debug_intent:  # 新增代码+ObservePlanActVerify：用户明确要求源码或日志排查时放行；如果没有这行代码，合法调试会被误伤。
        return False  # 新增代码+ObservePlanActVerify：返回不阻断；如果没有这行代码，用户要求看源码也会被卡住。
    if actionability_tool_matches_required(tool_name, pending):  # 新增代码+ObservePlanActVerify：正确下一步工具必须放行；如果没有这行代码，协议会把自己要求的动作也拦住。
        return False  # 新增代码+ObservePlanActVerify：返回不阻断；如果没有这行代码，模型无法完成 pending。
    normalized_tool = normalize_actionability_tool_name(tool_name).lower()  # 新增代码+ObservePlanActVerify：归一化并小写本次工具；如果没有这行代码，大小写或 MCP 前缀会影响阻断。
    lower_text = str(tool_call_text or "").lower()  # 新增代码+ObservePlanActVerify：准备参数文本用于识别 debug/snapshot 读法；如果没有这行代码，bash 读日志命令无法判断。
    if normalized_tool in BYPASSABLE_TOOL_NAMES:  # 新增代码+ObservePlanActVerify：读写和 shell 工具属于可能绕行动作的工具；如果没有这行代码，模型会继续 Select-String snapshot 日志。
        return True  # 新增代码+ObservePlanActVerify：阻断绕行工具；如果没有这行代码，observe-plan-act-verify 链路没有硬门禁。
    if "debug_logs" in lower_text or "tool_results" in lower_text or "snapshot" in lower_text:  # 新增代码+ObservePlanActVerify：即使工具名变化，只要参数像读日志也阻断；如果没有这行代码，模型会用别名工具绕过。
        return True  # 新增代码+ObservePlanActVerify：阻断读日志参数；如果没有这行代码，复杂提示压力测试仍会漂移。
    return False  # 新增代码+ObservePlanActVerify：其他工具暂不阻断以避免过度收束；如果没有这行代码，函数缺少默认返回。
    # 新增代码+ObservePlanActVerify：函数段结束，should_block_tool_for_pending_actionability 到此结束；如果没有这个边界说明，用户不容易看出阻断规则。


__all__ = [  # 新增代码+ObservePlanActVerify：公开接口清单段开始；如果没有这段代码，其他模块导入边界不清楚。
    "ACTIONABILITY_PENDING_KEY",  # 新增代码+ObservePlanActVerify：导出 pending 键；如果没有这行代码，测试和控制器无法统一状态名。
    "BROWSER_ACTION_FULFILLED_MARKER",  # 新增代码+ObservePlanActVerify：导出浏览器完成 marker；如果没有这行代码，浏览器工具无法复用常量。
    "BROWSER_ACTION_REQUIRED_MARKER",  # 新增代码+ObservePlanActVerify：导出浏览器动作 marker；如果没有这行代码，浏览器 snapshot 无法复用常量。
    "BROWSER_VERIFY_REQUIRED_MARKER",  # 新增代码+ObservePlanActVerify：导出浏览器验证 marker；如果没有这行代码，点击和按键工具无法复用常量。
    "DESKTOP_ACTION_REQUIRED_MARKER",  # 新增代码+ObservePlanActVerify：导出桌面动作 marker；如果没有这行代码，桌面工具无法复用常量。
    "DESKTOP_OBSERVATION_BLOCKED_MARKER",  # 新增代码+ObservePlanActVerify：导出桌面阻塞 marker；如果没有这行代码，桌面工具无法复用常量。
    "actionability_allowed_tool_names",  # 新增代码+ObservePlanActVerify：导出允许工具函数；如果没有这行代码，控制器无法复用匹配规则。
    "actionability_tool_matches_required",  # 新增代码+ObservePlanActVerify：导出工具匹配函数；如果没有这行代码，外部测试无法验证规则。
    "clear_pending_actionability",  # 新增代码+ObservePlanActVerify：导出清理函数；如果没有这行代码，测试和后续模块无法显式清理状态。
    "get_pending_actionability",  # 新增代码+ObservePlanActVerify：导出读取函数；如果没有这行代码，控制器和测试无法读取 pending。
    "normalize_actionability_tool_name",  # 新增代码+ObservePlanActVerify：导出工具名归一函数；如果没有这行代码，未来模块会重复实现。
    "pending_actionability_argument_mismatch",  # 新增代码+PendingArgumentGate：导出 pending 参数门禁函数；如果没有这行代码，外部控制器无法复用同一套 element_id 校验。
    "pending_actionability_message",  # 新增代码+ObservePlanActVerify：导出纠偏提示函数；如果没有这行代码，控制器会重复拼提示。
    "record_actionability_from_tool_result",  # 新增代码+ObservePlanActVerify：导出工具结果记录函数；如果没有这行代码，主循环无法接入 marker。
    "should_block_tool_for_pending_actionability",  # 新增代码+ObservePlanActVerify：导出阻断判断函数；如果没有这行代码，控制器无法拦截读日志跑偏。
]  # 新增代码+ObservePlanActVerify：公开接口清单段结束；如果没有这行代码，Python 列表语法不完整。
