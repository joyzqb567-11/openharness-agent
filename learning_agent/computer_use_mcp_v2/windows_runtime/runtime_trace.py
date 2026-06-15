"""Computer Use 运行 trace 和截图 artifact 登记工具。"""  # 新增代码+AgentPySplitPhase3: 说明本文件负责桌面工具运行证据链；如果没有这行代码，代码小白不知道 trace 相关函数为什么放在这里。

from __future__ import annotations  # 新增代码+AgentPySplitPhase3: 允许类型注解延迟解析；如果没有这行代码，复杂类型在旧运行方式下更容易受定义顺序影响。

import copy  # 新增代码+AgentPySplitPhase3: 用于深拷贝 trace payload；如果没有这行代码，后续代码修改原字典会污染历史证据。
import time  # 新增代码+AgentPySplitPhase3: 用于给 trace 事件打时间戳；如果没有这行代码，排查时无法判断模型请求和工具结果先后。
from typing import Any, Callable  # 新增代码+AgentPySplitPhase3: 导入通用类型和回调类型；如果没有这行代码，模块接口不容易看出依赖边界。


RecordObservation = Callable[[str, dict[str, Any]], None]  # 新增代码+AgentPySplitPhase3: 定义观察事件记录回调类型；如果没有这行代码，新模块会被迫直接依赖 LearningAgent。


# 修改代码+AgentPySplitPhase15B6: 函数段开始，runtime_trace_recorder 把“更新 agent trace 列表”的状态写回动作封装成公开回调；如果没有这段函数，删除 agent.py 旧 trace 薄包装后各调用点会重复写 setattr 逻辑。
def runtime_trace_recorder(state_owner: Any, record_observation: RecordObservation) -> Callable[[str, dict[str, Any]], None]:  # 修改代码+AgentPySplitPhase15B6: 定义 trace 回调工厂入口；如果没有这行代码，Computer Use 工具适配层拿不到可复用的 trace 记录回调。
    def record(phase: str, payload: dict[str, Any]) -> None:  # 修改代码+AgentPySplitPhase15B6: 定义真正交给 agent_tools 或主循环调用的记录函数；如果没有这行代码，调用方无法用简单回调追加 trace。
        if not hasattr(state_owner, "computer_use_runtime_trace_events"):  # 修改代码+AgentPySplitPhase15B6: 兼容轻量 __new__ 测试对象没有初始化 trace 列表的情况；如果没有这行代码，旧兼容测试会因缺属性中断。
            state_owner.computer_use_runtime_trace_events = []  # 修改代码+AgentPySplitPhase15B6: 惰性创建 trace 事件列表；如果没有这行代码，后续 record_computer_use_runtime_trace 没有旧列表可追加。
        state_owner.computer_use_runtime_trace_events = record_computer_use_runtime_trace(state_owner.computer_use_runtime_trace_events, phase, payload, record_observation)  # 修改代码+AgentPySplitPhase15B6: 调用公开 trace 记录函数并写回 agent 状态；如果没有这行代码，trace 事件不会真正保存在本轮 agent 上。
    return record  # 修改代码+AgentPySplitPhase15B6: 返回可复用回调给主循环和工具入口；如果没有这行代码，外层无法拿到记录函数。
# 修改代码+AgentPySplitPhase15B6: 函数段结束，runtime_trace_recorder 到此结束；如果没有这个边界说明，用户不容易看出这是替代旧 agent trace 薄包装的公开入口。


# 修改代码+AgentPySplitPhase15B6: 函数段开始，image_artifact_recorder 把截图 active_artifacts 写回动作封装成公开回调；如果没有这段函数，删除 agent.py 旧截图登记薄包装后 observe/action 工具无法登记截图产物。
def image_artifact_recorder(state_owner: Any, record_observation: RecordObservation) -> Callable[[dict[str, Any], str], None]:  # 修改代码+AgentPySplitPhase15B6: 定义图片 artifact 回调工厂入口；如果没有这行代码，Computer Use observe/action 无法拿到截图登记回调。
    def record(result_data: dict[str, Any], tool_name: str) -> None:  # 修改代码+AgentPySplitPhase15B6: 定义真正处理工具结果的截图登记函数；如果没有这行代码，调用方不能用简单回调登记截图。
        state_owner.active_artifacts = record_computer_use_image_artifacts(result_data, tool_name, getattr(state_owner, "active_artifacts", []), record_observation)  # 修改代码+AgentPySplitPhase15B6: 调用公开图片登记函数并写回 active_artifacts；如果没有这行代码，截图虽然落盘但不会进入本轮活跃产物列表。
    return record  # 修改代码+AgentPySplitPhase15B6: 返回可复用回调给 observe/action 工具入口；如果没有这行代码，外层无法拿到截图登记函数。
# 修改代码+AgentPySplitPhase15B6: 函数段结束，image_artifact_recorder 到此结束；如果没有这个边界说明，用户不容易看出这是替代旧 agent 截图登记薄包装的公开入口。


# 新增代码+AgentPySplitPhase3: 函数段开始，is_computer_use_tool_name 判断工具名是否属于 Computer Use 工具面；如果没有这段函数，trace 过滤规则会散落在主循环多个位置。
def is_computer_use_tool_name(tool_name: str) -> bool:  # 新增代码+AgentPySplitPhase3: 定义 Computer Use 工具名判断入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    normalized_name = str(tool_name).strip()  # 新增代码+AgentPySplitPhase3: 清理工具名两端空白；如果没有这行代码，异常空白会导致 Computer Use 工具漏记。
    return normalized_name.startswith("mcp__computer-use__")  # 修改代码+ComputerUseMcpV2ResidualCleanup：主循环只把 v2 MCP 前缀工具名当作模型可见 Computer Use 工具；如果没有这行代码，旧 computer_action/computer_use 名称会继续污染 runtime trace 判断。
# 新增代码+AgentPySplitPhase3: 函数段结束，is_computer_use_tool_name 到此结束；如果没有这个边界说明，用户不容易看出工具名过滤范围。


# 新增代码+AgentPySplitPhase3: 函数段开始，record_computer_use_runtime_trace 追加 Computer Use 主循环运行证据；如果没有这段函数，模型请求、工具调用和工具结果无法形成同一条证据链。
def record_computer_use_runtime_trace(events: list[dict[str, Any]], phase: str, payload: dict[str, Any], record_observation: RecordObservation) -> list[dict[str, Any]]:  # 新增代码+AgentPySplitPhase3: 定义 trace 记录入口；如果没有这行代码，agent.py 不能把 trace 追加逻辑迁出。
    event = {  # 新增代码+AgentPySplitPhase3: 构造固定结构的 trace 事件；如果没有这行代码，不同记录点会输出不兼容字段。
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),  # 新增代码+AgentPySplitPhase3: 保存 trace 事件时间；如果没有这行代码，排查时无法判断模型请求和工具结果先后。
        "phase": str(phase),  # 新增代码+AgentPySplitPhase3: 保存阶段名，例如 model_request、tool_call、tool_result；如果没有这行代码，汇总函数无法分类。
        "payload": copy.deepcopy(payload),  # 新增代码+AgentPySplitPhase3: 深拷贝脱敏摘要载荷；如果没有这行代码，后续代码改动 payload 会污染历史证据。
    }  # 新增代码+AgentPySplitPhase3: trace 事件字典结束；如果没有这行代码，Python 语法不完整。
    updated_events = list(events or [])  # 新增代码+AgentPySplitPhase3: 复制旧事件列表，避免直接依赖外层列表对象状态；如果没有这行代码，调用方传 None 或旧对象时不稳定。
    updated_events.append(event)  # 新增代码+AgentPySplitPhase3: 把事件加入 Computer Use 专用 trace；如果没有这行代码，report 没有数据来源。
    updated_events = updated_events[-300:]  # 新增代码+AgentPySplitPhase3: 限制最多保留最近 300 条避免长任务内存无限增长；如果没有这行代码，真实桌面长循环会堆积过多事件。
    record_observation("computer_use_runtime_trace", event)  # 新增代码+AgentPySplitPhase3: 同步写入通用 observation 方便旧调试入口查看；如果没有这行代码，latest_run_readable 看不到 trace 入口。
    return updated_events  # 新增代码+AgentPySplitPhase3: 返回裁剪后的事件列表给 agent 保存；如果没有这行代码，外层状态不会更新。
# 新增代码+AgentPySplitPhase3: 函数段结束，record_computer_use_runtime_trace 到此结束；如果没有这个边界说明，用户不容易看出 trace 记录范围。


# 新增代码+AgentPySplitPhase3: 函数段开始，computer_use_runtime_trace_report 汇总 Computer Use 运行时证据；如果没有这段函数，用户无法查询主循环实际走过哪些工具。
def computer_use_runtime_trace_report(events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+AgentPySplitPhase3: 定义 trace 汇总入口；如果没有这行代码，agent.py 不能把 report 计算迁出。
    event_snapshot = list(events or [])  # 新增代码+AgentPySplitPhase3: 读取 trace 事件快照；如果没有这行代码，汇总过程可能被后续追加事件影响。
    computer_tool_names_seen: set[str] = set()  # 新增代码+AgentPySplitPhase3: 保存模型请求阶段看到过的 Computer Use 工具名；如果没有这行代码，schema 可见性无法汇总。
    tools_called: set[str] = set()  # 新增代码+AgentPySplitPhase3: 保存模型实际调用过的 Computer Use 工具名；如果没有这行代码，schema 暴露和真实调用会混在一起。
    direct_tool_phases: set[str] = set()  # 新增代码+AgentPySplitPhase3: 保存工具内部补充记录过的阶段；如果没有这行代码，observe/discover/action 内部路径无法单独查看。
    model_request_seen = False  # 新增代码+AgentPySplitPhase3: 默认尚未看到模型请求；如果没有这行代码，空 trace 可能被误判为真。
    tool_call_seen = False  # 新增代码+AgentPySplitPhase3: 默认尚未看到工具调用；如果没有这行代码，report 无法给出稳定布尔字段。
    tool_result_seen = False  # 新增代码+AgentPySplitPhase3: 默认尚未看到工具结果；如果没有这行代码，report 无法判断结果是否回流模型。
    screenshot_returned_to_model = False  # 新增代码+AgentPySplitPhase3: 默认未观察到截图回流标记；如果没有这行代码，视觉输入状态没有汇总字段。
    for event in event_snapshot:  # 新增代码+AgentPySplitPhase3: 逐条扫描 trace 事件；如果没有这行代码，汇总字段没有计算过程。
        phase = str(event.get("phase", ""))  # 新增代码+AgentPySplitPhase3: 读取当前事件阶段；如果没有这行代码，后续无法按阶段判断。
        payload = event.get("payload", {})  # 新增代码+AgentPySplitPhase3: 读取当前事件载荷；如果没有这行代码，工具名和截图标记无法提取。
        payload_dict = payload if isinstance(payload, dict) else {}  # 新增代码+AgentPySplitPhase3: 防御异常载荷类型；如果没有这行代码，坏事件会让 report 崩溃。
        if phase == "model_request":  # 新增代码+AgentPySplitPhase3: 识别模型请求阶段；如果没有这行代码，schema 可见性不会被记录。
            model_request_seen = True  # 新增代码+AgentPySplitPhase3: 标记模型请求已出现；如果没有这行代码，report 会错误显示模型没有请求。
            for tool_name in payload_dict.get("tool_names", []):  # 新增代码+AgentPySplitPhase3: 遍历模型可见工具名；如果没有这行代码，无法收集 Computer Use schema。
                tool_name_text = str(tool_name)  # 新增代码+AgentPySplitPhase3: 把工具名转成字符串；如果没有这行代码，异常类型会影响集合去重。
                if is_computer_use_tool_name(tool_name_text):  # 新增代码+AgentPySplitPhase3: 只保留 Computer Use 工具；如果没有这行代码，普通 read/bash 工具会污染 report。
                    computer_tool_names_seen.add(tool_name_text)  # 新增代码+AgentPySplitPhase3: 记录模型可见 Computer Use 工具；如果没有这行代码，tool_schema_visible 无法判断。
        if phase == "tool_call":  # 新增代码+AgentPySplitPhase3: 识别工具调用阶段；如果没有这行代码，模型实际调用过工具不会被汇总。
            tool_name_text = str(payload_dict.get("tool_name", ""))  # 新增代码+AgentPySplitPhase3: 读取被调用工具名；如果没有这行代码，工具调用集合没有元素来源。
            if is_computer_use_tool_name(tool_name_text):  # 新增代码+AgentPySplitPhase3: 只统计 Computer Use 工具调用；如果没有这行代码，普通工具会误算到桌面能力里。
                tool_call_seen = True  # 新增代码+AgentPySplitPhase3: 标记模型实际调用过 Computer Use 工具；如果没有这行代码，report 会漏掉调用事实。
                tools_called.add(tool_name_text)  # 新增代码+AgentPySplitPhase3: 记录工具名；如果没有这行代码，用户看不到具体调用了 discover 还是 action。
        if phase == "tool_result":  # 新增代码+AgentPySplitPhase3: 识别工具结果阶段；如果没有这行代码，结果回流不会被汇总。
            tool_name_text = str(payload_dict.get("tool_name", ""))  # 新增代码+AgentPySplitPhase3: 读取结果所属工具名；如果没有这行代码，工具结果集合没有归属。
            if is_computer_use_tool_name(tool_name_text):  # 新增代码+AgentPySplitPhase3: 只统计 Computer Use 工具结果；如果没有这行代码，普通工具结果会污染桌面 trace。
                tool_result_seen = True  # 新增代码+AgentPySplitPhase3: 标记 Computer Use 工具结果已回流；如果没有这行代码，report 无法证明模型拿到了工具结果。
                tools_called.add(tool_name_text)  # 新增代码+AgentPySplitPhase3: 把有结果的工具也纳入调用集合；如果没有这行代码，只记录调用时中断会漏算。
                screenshot_returned_to_model = screenshot_returned_to_model or bool(payload_dict.get("screenshot_returned_to_model", False))  # 新增代码+AgentPySplitPhase3: 累计截图回流标记；如果没有这行代码，视觉输入证据不会出现在 report。
        if phase.startswith("computer_"):  # 新增代码+AgentPySplitPhase3: 识别工具内部补充阶段；如果没有这行代码，discover/observe/action 内部 trace 无法汇总。
            direct_tool_phases.add(phase)  # 新增代码+AgentPySplitPhase3: 保存内部阶段名；如果没有这行代码，真实工具内部是否执行过不可见。
    return {  # 新增代码+AgentPySplitPhase3: 返回结构化汇总报告；如果没有这行代码，调用方拿不到可断言结果。
        "runtime_trace_available": True,  # 新增代码+AgentPySplitPhase3: 声明 runtime trace 能力存在；如果没有这行代码，外部无法区分旧 agent 和新 agent。
        "trace_event_count": len(event_snapshot),  # 新增代码+AgentPySplitPhase3: 返回事件数量；如果没有这行代码，空 trace 不容易被发现。
        "model_request_seen": model_request_seen,  # 新增代码+AgentPySplitPhase3: 返回模型请求是否被记录；如果没有这行代码，主循环入口不可验证。
        "tool_schema_visible": bool(computer_tool_names_seen),  # 新增代码+AgentPySplitPhase3: 返回 Computer Use schema 是否对模型可见；如果没有这行代码，工具暴露状态不可验证。
        "tool_call_seen": tool_call_seen,  # 新增代码+AgentPySplitPhase3: 返回模型是否调用 Computer Use 工具；如果没有这行代码，模型主动选择工具不可验证。
        "tool_result_seen": tool_result_seen,  # 新增代码+AgentPySplitPhase3: 返回工具结果是否回流；如果没有这行代码，observe-plan-act loop 是否闭合不可验证。
        "screenshot_returned_to_model": screenshot_returned_to_model,  # 新增代码+AgentPySplitPhase3: 返回是否观察到截图回流；如果没有这行代码，视觉输入路径没有统一字段。
        "computer_tool_names_seen": sorted(computer_tool_names_seen),  # 新增代码+AgentPySplitPhase3: 返回模型看见过的 Computer Use 工具名；如果没有这行代码，用户只能看到布尔值不能定位缺哪一个。
        "tools_called": sorted(tools_called),  # 新增代码+AgentPySplitPhase3: 返回模型实际调用过的 Computer Use 工具名；如果没有这行代码，瘦身时仍无法区分暴露和使用。
        "direct_tool_phases": sorted(direct_tool_phases),  # 新增代码+AgentPySplitPhase3: 返回工具内部记录阶段；如果没有这行代码，内部 discover/observe/action 路径不可见。
    }  # 新增代码+AgentPySplitPhase3: 报告字典结束；如果没有这行代码，Python 语法不完整。
# 新增代码+AgentPySplitPhase3: 函数段结束，computer_use_runtime_trace_report 到此结束；如果没有这个边界说明，用户不容易看出汇总函数范围。


# 新增代码+AgentPySplitPhase3: 函数段开始，record_computer_use_image_artifacts 把 Computer Use 图片结果登记为活跃产物；如果没有这段函数，截图虽然落盘但长任务恢复和会话摘要不知道它仍然重要。
def record_computer_use_image_artifacts(result_data: dict[str, Any], tool_name: str, active_artifacts: list[str], record_observation: RecordObservation) -> list[str]:  # 新增代码+AgentPySplitPhase3: 定义图片 artifact 登记入口；如果没有这行代码，agent.py 不能把截图登记逻辑迁出。
    from .evidence import collect_image_result_blocks  # 新增代码+AgentPySplitPhase3: 从同包导入 image_result block 收集器；如果没有这行代码，agent 无法从嵌套结果里找到截图路径。
    image_results = collect_image_result_blocks(result_data)  # 新增代码+AgentPySplitPhase3: 收集工具结果里的图片块；如果没有这行代码，agent 不知道本次结果包含截图。
    if not image_results:  # 新增代码+AgentPySplitPhase3: 无图片块时直接返回；如果没有这行代码，普通 Computer Use 结果会产生无意义审计事件。
        return list(active_artifacts or [])  # 新增代码+AgentPySplitPhase3: 无图时保持原活跃产物列表；如果没有这行代码，调用方可能丢失已有 artifact。
    updated_artifacts = list(active_artifacts or [])  # 新增代码+AgentPySplitPhase3: 复制外层活跃产物列表；如果没有这行代码，函数会直接依赖传入列表对象的可变状态。
    recorded_paths: list[str] = []  # 新增代码+AgentPySplitPhase3: 准备保存本次登记的路径；如果没有这行代码，observation 无法记录具体 artifact。
    for image_result in image_results:  # 新增代码+AgentPySplitPhase3: 遍历每个图片块；如果没有这行代码，多张截图无法全部登记。
        artifact_path = str(image_result.get("artifact_path", "")).strip()  # 新增代码+AgentPySplitPhase3: 读取并清理 artifact 路径；如果没有这行代码，空白或非字符串路径可能污染 active_artifacts。
        if not artifact_path:  # 新增代码+AgentPySplitPhase3: 跳过空路径；如果没有这行代码，active_artifacts 可能出现不可打开的空条目。
            continue  # 新增代码+AgentPySplitPhase3: 继续处理下一张图；如果没有这行代码，空路径会被错误登记。
        if artifact_path not in updated_artifacts:  # 新增代码+AgentPySplitPhase3: 避免重复登记同一截图；如果没有这行代码，长会话里相同 artifact 会挤占列表。
            updated_artifacts.append(artifact_path)  # 新增代码+AgentPySplitPhase3: 把截图路径加入活跃产物；如果没有这行代码，后续上下文控制找不到该截图。
        recorded_paths.append(artifact_path)  # 新增代码+AgentPySplitPhase3: 记录本次处理路径用于审计；如果没有这行代码，observation 事件缺少具体文件。
    updated_artifacts = updated_artifacts[-50:]  # 新增代码+AgentPySplitPhase3: 保持活跃产物列表上限；如果没有这行代码，长期 Computer Use 会无限累积截图路径。
    if recorded_paths:  # 新增代码+AgentPySplitPhase3: 只有确实登记路径才写 observation；如果没有这行代码，空路径结果会制造噪音事件。
        record_observation("computer_use_image_result", {"tool_name": tool_name, "image_result_count": len(image_results), "artifact_paths": recorded_paths, "marker": image_results[0].get("marker", "")})  # 新增代码+AgentPySplitPhase3: 记录图片 artifact 事件；如果没有这行代码，审计无法解释截图为何成为活跃产物。
    return updated_artifacts  # 新增代码+AgentPySplitPhase3: 返回裁剪后的活跃产物列表；如果没有这行代码，外层 agent 无法保存登记结果。
# 新增代码+AgentPySplitPhase3: 函数段结束，record_computer_use_image_artifacts 到此结束；如果没有这个结束标记，学习者不容易看出图片 artifact 登记边界。
