"""Computer Use MCP v2 agent-side wrapper 桥接。"""  # 修改代码+ClaudeCodeWrapperParity：说明本文件对齐 ClaudeCode wrapper.tsx；如果没有这行代码，agent-side 绑定入口没有同构位置。
from __future__ import annotations  # 修改代码+ClaudeCodeWrapperParity：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生并放大循环导入风险。

import json  # 修改代码+ClaudeCodeWrapperParity：导入 JSON 用于返回当前字符串工具通道可承载的模型文本；如果没有这行代码，wrapper 无法稳定输出。
from typing import Any  # 修改代码+ClaudeCodeWrapperParity：导入通用类型；如果没有这行代码，agent 和 ToolCall duck typing 边界不清楚。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.bind_session_context import bind_session_context  # 修改代码+ClaudeCodeWrapperParity：导入 agent-side 上下文绑定；如果没有这行代码，wrapper 拿不到主循环回调、锁和 display state。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.result_blocks import mcp_content_from_result  # 新增代码+ClaudeCodeWrapperParity：复用 stdio server 的 MCP content block 包装；如果没有这行代码，agent-side 和 server-side 结果会分裂。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import cleanup_computer_use_mcp_v2_turn, dispatch_computer_use_mcp_v2_tool, normalize_tool_name  # 修改代码+ClaudeCodeWrapperParity：导入 runtime 分发、cleanup 和工具名归一化；如果没有这行代码，wrapper 无法执行工具或对齐 turn-end cleanup hook。

_current_tool_use_context: dict[str, Any] | None = None  # 新增代码+ClaudeCodeWrapperParity：保存最近一次 Computer Use 工具调用上下文；如果没有这行代码，就无法像 ClaudeCode 一样有 currentToolUseContext 可观测锚点。


def current_tool_use_context() -> dict[str, Any] | None:  # 新增代码+ClaudeCodeWrapperParity：函数段开始，暴露当前工具调用上下文快照；如果没有这段函数，测试和后续桥接层无法读取 wrapper 当前调用。
    return dict(_current_tool_use_context) if isinstance(_current_tool_use_context, dict) else None  # 新增代码+ClaudeCodeWrapperParity：返回副本避免外部修改模块状态；如果没有这行代码，调用方可能污染正在执行的工具上下文。
# 新增代码+ClaudeCodeWrapperParity：函数段结束，current_tool_use_context 到此结束；如果没有这个边界说明，用户不容易看出读取 current context 的范围。


def _tool_use_context_snapshot(tool_name: str, arguments: dict[str, Any], call_id: str = "") -> dict[str, Any]:  # 新增代码+ClaudeCodeWrapperParity：函数段开始，构造 ClaudeCode currentToolUseContext 的 Python 快照；如果没有这段函数，context 字段会散落在执行逻辑里。
    return {"tool_name": str(tool_name), "raw_tool_name": normalize_tool_name(tool_name), "call_id": str(call_id or ""), "arguments": dict(arguments), "bridge": "claudecode_wrapper", "runtime": "computer_use_mcp_v2"}  # 新增代码+ClaudeCodeWrapperParity：记录工具名、call_id、参数和桥接来源；如果没有这行代码，跨层排查无法确认本次调用是谁触发的。
# 新增代码+ClaudeCodeWrapperParity：函数段结束，_tool_use_context_snapshot 到此结束；如果没有这个边界说明，用户不容易看出 current context 字段来源。


def _write_current_tool_use_context(agent: Any, context: Any, snapshot: dict[str, Any]) -> None:  # 新增代码+ClaudeCodeWrapperParity：函数段开始，把当前工具上下文写入模块、agent 和 runtime context；如果没有这段函数，ClaudeCode 风格 current ref 无法被回调和审计读取。
    global _current_tool_use_context  # 新增代码+ClaudeCodeWrapperParity：声明要更新模块级 current ref；如果没有这行代码，赋值只会创建局部变量。
    _current_tool_use_context = dict(snapshot)  # 新增代码+ClaudeCodeWrapperParity：更新模块级快照；如果没有这行代码，current_tool_use_context 会继续返回旧调用或 None。
    setattr(agent, "computer_use_mcp_v2_current_tool_use_context", dict(snapshot))  # 新增代码+ClaudeCodeWrapperParity：把快照写到 agent 便于主循环和状态页读取；如果没有这行代码，agent 侧无法知道当前 Computer Use 工具。
    setattr(context, "current_tool_use_context", dict(snapshot))  # 新增代码+ClaudeCodeWrapperParity：把快照写到 runtime context 便于 host/回调读取；如果没有这行代码，context 回调无法对齐 ClaudeCode 的 per-call ref。
# 新增代码+ClaudeCodeWrapperParity：函数段结束，_write_current_tool_use_context 到此结束；如果没有这个边界说明，用户不容易看出写入 current context 的范围。


def _agent_block_from_mcp_block(block: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeWrapperParity：函数段开始，把单个 MCP content block 转成当前 agent 可记录的模型块；如果没有这段函数，text/image 映射会混在执行函数里。
    block_type = str(block.get("type", "") or "")  # 新增代码+ClaudeCodeWrapperParity：读取 MCP block 类型；如果没有这行代码，后续无法区分文本和图片。
    if block_type == "text":  # 新增代码+ClaudeCodeWrapperParity：处理 MCP text block；如果没有这行代码，普通工具说明会退回 JSON 兜底。
        return {"type": "text", "text": str(block.get("text", "") or "")}  # 新增代码+ClaudeCodeWrapperParity：返回模型可读文本块；如果没有这行代码，agent block 会丢掉文本内容。
    if block_type == "image":  # 新增代码+ClaudeCodeWrapperParity：处理 MCP image block；如果没有这行代码，screenshot/zoom 的图片语义不会进入 agent block。
        source = block.get("source", {})  # 新增代码+ClaudeCodeWrapperParity：读取 ClaudeCode-style image source；如果没有这行代码，图片 MIME 和 base64 数据无法保留。
        if isinstance(source, dict):  # 新增代码+ClaudeCodeWrapperParity：只复制合法 source 字典；如果没有这行代码，异常 source 类型会导致后续 .get 崩溃。
            return {"type": "image", "source": {"type": str(source.get("type", "base64") or "base64"), "media_type": str(source.get("media_type", source.get("mimeType", "image/jpeg")) or "image/jpeg"), "data": str(source.get("data", "") or "")}}  # 修改代码+ComputerUseAdaptiveImage：返回 Anthropic/ClaudeCode 风格 base64 图片块并用 JPEG 兜底；如果没有这行代码，未知 MIME 会默认 PNG 而偏离 ClaudeCode。
        return {"type": "text", "text": json.dumps(block, ensure_ascii=False, sort_keys=True)}  # 新增代码+ClaudeCodeWrapperParity：坏图片块使用 JSON 文本兜底；如果没有这行代码，异常 content block 会被静默丢弃。
    return {"type": "text", "text": json.dumps(block, ensure_ascii=False, sort_keys=True)}  # 新增代码+ClaudeCodeWrapperParity：未知 block 类型转成文本；如果没有这行代码，未来扩展 block 会完全不可见。
# 新增代码+ClaudeCodeWrapperParity：函数段结束，_agent_block_from_mcp_block 到此结束；如果没有这个边界说明，用户不容易看出单 block 映射范围。


def agent_blocks_from_mcp_content(content: Any) -> list[dict[str, Any]]:  # 新增代码+ClaudeCodeWrapperParity：函数段开始，把 MCP content 数组映射为 agent 可读 block；如果没有这段函数，wrapper 无法复用 ClaudeCode 的 result-to-block 语义。
    if not isinstance(content, list):  # 新增代码+ClaudeCodeWrapperParity：只处理标准 content 数组；如果没有这行代码，非列表 content 会导致遍历异常。
        return [{"type": "text", "text": json.dumps(content, ensure_ascii=False, sort_keys=True)}] if content is not None else []  # 新增代码+ClaudeCodeWrapperParity：非列表 content 用文本兜底或返回空；如果没有这行代码，异常结果无法交给模型。
    return [_agent_block_from_mcp_block(block) if isinstance(block, dict) else {"type": "text", "text": str(block)} for block in content]  # 新增代码+ClaudeCodeWrapperParity：逐块转换并容忍非字典项；如果没有这行代码，多块结果无法映射。
# 新增代码+ClaudeCodeWrapperParity：函数段结束，agent_blocks_from_mcp_content 到此结束；如果没有这个边界说明，用户不容易看出 content 数组映射范围。


def _agent_blocks_text_summary(blocks: list[dict[str, Any]]) -> str:  # 新增代码+ClaudeCodeWrapperParity：函数段开始，把 agent block 压成当前字符串工具通道能承载的摘要；如果没有这段函数，字符串通道会丢失图片块提示。
    lines: list[str] = []  # 新增代码+ClaudeCodeWrapperParity：准备累积文本摘要行；如果没有这行代码，多个 block 无法有序展示。
    for index, block in enumerate(blocks):  # 新增代码+ClaudeCodeWrapperParity：逐个处理 block；如果没有这行代码，只能处理单块或没有摘要。
        if block.get("type") == "text":  # 新增代码+ClaudeCodeWrapperParity：文本块直接输出正文；如果没有这行代码，文本内容会被统一 JSON 化降低可读性。
            lines.append(str(block.get("text", "") or ""))  # 新增代码+ClaudeCodeWrapperParity：保存文本正文；如果没有这行代码，模型看不到工具的自然语言摘要。
        elif block.get("type") == "image":  # 新增代码+ClaudeCodeWrapperParity：图片块输出轻量摘要；如果没有这行代码，字符串工具通道不会提示有图片。
            source = block.get("source", {}) if isinstance(block.get("source"), dict) else {}  # 新增代码+ClaudeCodeWrapperParity：读取图片 source；如果没有这行代码，MIME 和数据长度无法摘要。
            lines.append(f"[image_{index} media_type={source.get('media_type', 'image/jpeg')} base64_chars={len(str(source.get('data', '') or ''))}]")  # 修改代码+ComputerUseAdaptiveImage：写入图片块摘要并用 JPEG 兜底；如果没有这行代码，缺 MIME 图片摘要会偏向 PNG。
        else:  # 新增代码+ClaudeCodeWrapperParity：处理未知块类型；如果没有这行代码，未来 block 类型没有兜底。
            lines.append(json.dumps(block, ensure_ascii=False, sort_keys=True))  # 新增代码+ClaudeCodeWrapperParity：未知块以 JSON 展示；如果没有这行代码，调试信息会丢失。
    return "\n".join(line for line in lines if line)  # 新增代码+ClaudeCodeWrapperParity：返回非空摘要文本；如果没有这行代码，调用方拿不到模型可读摘要。
# 新增代码+ClaudeCodeWrapperParity：函数段结束，_agent_blocks_text_summary 到此结束；如果没有这个边界说明，用户不容易看出摘要生成范围。


def _public_agent_block_summary(block: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeWrapperParity：函数段开始，把完整 agent block 转成适合 JSON 文本返回的轻量摘要；如果没有这段函数，截图 base64 会在工具文本里重复膨胀。
    if block.get("type") != "image":  # 新增代码+ClaudeCodeWrapperParity：非图片块可以原样返回；如果没有这行代码，文本块也会被不必要改写。
        return dict(block)  # 新增代码+ClaudeCodeWrapperParity：复制文本或未知块；如果没有这行代码，调用方可能共享并污染原 block。
    source = block.get("source", {}) if isinstance(block.get("source"), dict) else {}  # 新增代码+ClaudeCodeWrapperParity：读取图片 source；如果没有这行代码，无法生成 MIME 和长度摘要。
    return {"type": "image", "source": {"type": str(source.get("type", "base64") or "base64"), "media_type": str(source.get("media_type", "image/jpeg") or "image/jpeg"), "base64_chars": len(str(source.get("data", "") or ""))}}  # 修改代码+ComputerUseAdaptiveImage：只返回图片元数据和数据长度并用 JPEG 兜底；如果没有这行代码，工具输出会重复携带整张截图且缺省 MIME 会偏离 ClaudeCode。
# 新增代码+ClaudeCodeWrapperParity：函数段结束，_public_agent_block_summary 到此结束；如果没有这个边界说明，用户不容易看出图片摘要范围。


def _public_mcp_result_summary(mcp_result: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeWrapperParity：函数段开始，把 MCP result 转成不会重复携带图片 base64 的公开摘要；如果没有这段函数，wrapper JSON 会复制大图片 content。
    public_result = dict(mcp_result)  # 新增代码+ClaudeCodeWrapperParity：复制 MCP result 外层字段；如果没有这行代码，后续替换 content 会污染原对象。
    content = mcp_result.get("content", [])  # 新增代码+ClaudeCodeWrapperParity：读取 MCP content 数组；如果没有这行代码，无法对图片块做摘要。
    public_result["content"] = [_public_agent_block_summary(block) if isinstance(block, dict) else {"type": "text", "text": str(block)} for block in content] if isinstance(content, list) else content  # 新增代码+ClaudeCodeWrapperParity：对列表里的图片块去掉 base64 数据；如果没有这行代码，mcp_result 会重复塞入截图。
    return public_result  # 新增代码+ClaudeCodeWrapperParity：返回轻量 MCP 摘要；如果没有这行代码，调用方拿不到处理后的结果。
# 新增代码+ClaudeCodeWrapperParity：函数段结束，_public_mcp_result_summary 到此结束；如果没有这个边界说明，用户不容易看出 MCP 摘要范围。


def _wrap_result_for_agent(tool_name: str, result: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:  # 新增代码+ClaudeCodeWrapperParity：函数段开始，把 runtime result 加上 MCP result 和 agent block 视图；如果没有这段函数，agent-side wrapper 和 stdio server 结果仍然不对齐。
    wrapped = dict(result)  # 新增代码+ClaudeCodeWrapperParity：复制 runtime 结果避免直接污染原对象；如果没有这行代码，后续字段可能影响 runtime 调试引用。
    mcp_result = mcp_content_from_result(result)  # 新增代码+ClaudeCodeWrapperParity：按 server-side 同一规则生成 MCP content；如果没有这行代码，wrapper 无法保证 content block 语义一致。
    agent_blocks = agent_blocks_from_mcp_content(mcp_result.get("content"))  # 新增代码+ClaudeCodeWrapperParity：把 MCP content 映射成 agent blocks；如果没有这行代码，ClaudeCode 的 content-to-model-block 语义缺失。
    wrapped["mcp_result"] = _public_mcp_result_summary(mcp_result)  # 修改代码+ClaudeCodeWrapperParity：保留轻量 MCP 视图供调试和测试；如果没有这行代码，agent-side 输出无法和 stdio 输出逐项对比。
    wrapped["agent_model_blocks"] = [_public_agent_block_summary(block) for block in agent_blocks]  # 修改代码+ClaudeCodeWrapperParity：返回轻量 block 摘要而不是重复 base64；如果没有这行代码，大截图会在工具文本里成倍膨胀。
    wrapped["agent_model_block_count"] = len(agent_blocks)  # 新增代码+ClaudeCodeWrapperParity：单独保留完整 block 数量；如果没有这行代码，adapter 不解析摘要列表也无法快速审计。
    wrapped["agent_model_text"] = _agent_blocks_text_summary(agent_blocks)  # 新增代码+ClaudeCodeWrapperParity：为当前字符串通道生成轻量文本摘要；如果没有这行代码，图片块和文本块的可读摘要缺失。
    wrapped["wrapper"] = {"tool_name": normalize_tool_name(tool_name), "bridge": "claudecode_wrapper", "content_block_count": len(agent_blocks)}  # 新增代码+ClaudeCodeWrapperParity：记录 wrapper 处理证据；如果没有这行代码，测试无法确认结果经过 bridge wrapper。
    return wrapped, agent_blocks  # 修改代码+ClaudeCodeWrapperParity：返回轻量 JSON 结果和完整内存 blocks；如果没有这行代码，execute_agent_side_tool 不能把完整 block 写回 agent。
# 新增代码+ClaudeCodeWrapperParity：函数段结束，_wrap_result_for_agent 到此结束；如果没有这个边界说明，用户不容易看出结果增强范围。


def cleanup_agent_side_turn(agent: Any, reason: str = "turn cleanup") -> dict[str, Any]:  # 新增代码+ClaudeCodeWrapperParity：函数段开始，暴露 ClaudeCode wrapper cleanup hook；如果没有这段函数，abort 或 turn end 只能绕过 wrapper 直接调用 runtime。
    context = bind_session_context(agent)  # 新增代码+ClaudeCodeWrapperParity：复用同一个 session context；如果没有这行代码，cleanup 可能释放不到本轮工具持有的锁。
    cleanup_result = cleanup_computer_use_mcp_v2_turn(context, reason=reason)  # 新增代码+ClaudeCodeWrapperParity：调用统一 cleanup runtime；如果没有这行代码，锁释放和 display pin 清理不会发生。
    setattr(agent, "computer_use_mcp_v2_last_cleanup", dict(cleanup_result))  # 新增代码+ClaudeCodeWrapperParity：把 cleanup 结果写回 agent；如果没有这行代码，终端状态和测试无法读取 cleanup 证据。
    return cleanup_result  # 新增代码+ClaudeCodeWrapperParity：返回 cleanup 报告；如果没有这行代码，调用方无法确认清理结果。
# 新增代码+ClaudeCodeWrapperParity：函数段结束，cleanup_agent_side_turn 到此结束；如果没有这个边界说明，用户不容易看出 cleanup hook 范围。


def execute_agent_side_tool(agent: Any, tool_name: str, arguments: dict[str, Any], call_id: str = "") -> str:  # 修改代码+ClaudeCodeWrapperParity：函数段开始，在 agent 主循环内执行 v2 工具并映射 content blocks；如果没有这段函数，mcp__computer-use__ 仍会缺少 ClaudeCode wrapper 语义。
    context = bind_session_context(agent)  # 修改代码+ClaudeCodeWrapperParity：绑定或复用 agent 回调上下文；如果没有这行代码，v2 工具拿不到权限、trace、锁、display state 和观察回调。
    snapshot = _tool_use_context_snapshot(tool_name, arguments, call_id=call_id)  # 新增代码+ClaudeCodeWrapperParity：构造本次工具调用快照；如果没有这行代码，current tool use context 没有稳定内容。
    _write_current_tool_use_context(agent, context, snapshot)  # 新增代码+ClaudeCodeWrapperParity：写入 current tool use context；如果没有这行代码，权限/trace/调试无法知道当前调用。
    try:  # 新增代码+ClaudeCodeWrapperParity：捕获 runtime 执行异常并触发 wrapper cleanup；如果没有这行代码，异常路径可能残留锁。
        result = dispatch_computer_use_mcp_v2_tool(tool_name, arguments, context)  # 修改代码+ClaudeCodeWrapperParity：执行 v2 runtime；如果没有这行代码，工具不会真正运行。
        wrapped_result, agent_blocks = _wrap_result_for_agent(tool_name, result)  # 修改代码+ClaudeCodeWrapperParity：把 runtime result 映射成轻量 JSON 和完整 agent blocks；如果没有这行代码，模型可读 block 语义缺失。
        setattr(agent, "computer_use_mcp_v2_last_agent_model_blocks", [dict(block) for block in agent_blocks])  # 新增代码+ClaudeCodeWrapperParity：把完整 blocks 写入 agent 内存而不是重复塞进工具文本；如果没有这行代码，未来多模态 tool result adapter 无法直接复用。
        return json.dumps(wrapped_result, ensure_ascii=False, sort_keys=True)  # 修改代码+ClaudeCodeWrapperParity：返回模型可读 JSON 文本；如果没有这行代码，agent executor 拿不到字符串结果。
    except BaseException:  # 新增代码+ClaudeCodeWrapperParity：异常或中断时进入 cleanup 兜底；如果没有这行代码，KeyboardInterrupt/abort 后可能留下锁或隐藏状态。
        cleanup_agent_side_turn(agent, reason=f"wrapper abort cleanup:{normalize_tool_name(tool_name)}")  # 新增代码+ClaudeCodeWrapperParity：异常路径执行 cleanup hook；如果没有这行代码，abort 与 turn-end cleanup 语义不闭合。
        raise  # 新增代码+ClaudeCodeWrapperParity：重新抛出原异常交给上层转换；如果没有这行代码，真实错误会被吞掉。
# 修改代码+ClaudeCodeWrapperParity：函数段结束，execute_agent_side_tool 到此结束；如果没有这个边界说明，用户不容易看出 wrapper 执行范围。
