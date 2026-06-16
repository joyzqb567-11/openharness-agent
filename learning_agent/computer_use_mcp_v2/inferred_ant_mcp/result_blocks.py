"""Computer Use MCP v2 结果包装工具。"""  # 新增代码+ComputerUseMcpV2：说明本文件统一成功结果形状；如果没有这行代码，工具输出会不稳定。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，导入阶段类型求值可能产生噪音。

import json  # 新增代码+ComputerUseMcpV2：导入 JSON 用于生成 MCP 文本结果；如果没有这行代码，server 无法稳定返回 content 文本。
from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，结果 payload 边界不清楚。


def text_content_block(text: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeContentParity：函数段开始，生成 ClaudeCode 风格文本 content block；如果没有这段函数，观察结果只能退回整段 JSON 文本。
    return {"type": "text", "text": str(text)}  # 新增代码+ClaudeCodeContentParity：返回 MCP/ClaudeCode 都能读的文本块；如果没有这行代码，调用方无法稳定拼装 content 列表。
# 新增代码+ClaudeCodeContentParity：函数段结束，text_content_block 到此结束；如果没有这个边界说明，用户不容易看出文本块构造范围。


def image_content_block(data: str, media_type: str = "image/png") -> dict[str, Any]:  # 新增代码+ClaudeCodeContentParity：函数段开始，生成 ClaudeCode 风格 base64 图片 content block；如果没有这段函数，screenshot/zoom 无法直接把图片像素交给模型。
    safe_media_type = str(media_type or "image/png")  # 新增代码+ClaudeCodeContentParity：补齐图片 MIME 默认值；如果没有这行代码，空 MIME 会让多模态 content 难以识别图片格式。
    return {"type": "image", "source": {"type": "base64", "media_type": safe_media_type, "data": str(data)}}  # 新增代码+ClaudeCodeContentParity：返回 ClaudeCode-compatible 图片块；如果没有这行代码，截图只能通过文件路径二次回灌。
# 新增代码+ClaudeCodeContentParity：函数段结束，image_content_block 到此结束；如果没有这个边界说明，用户不容易看出图片块构造范围。


def success_result(tool_name: str, payload: dict[str, Any] | None = None, *, legacy_adapter_used: bool = False, content: list[dict[str, Any]] | None = None, debug: dict[str, Any] | None = None) -> dict[str, Any]:  # 修改代码+ClaudeCodeContentParity：函数段开始，生成统一成功结果并允许携带 ClaudeCode content/debug；如果没有这段函数，每个工具都会手写 ok/runtime/content 字段且容易不一致。
    result: dict[str, Any] = {"ok": True, "runtime": "computer_use_mcp_v2", "legacy_adapter_used": bool(legacy_adapter_used), "tool_name": str(tool_name), "tool": str(tool_name), "payload": dict(payload or {})}  # 修改代码+ClaudeCodeContentParity：保留旧 payload 同时补充 tool 别名；如果没有这行代码，旧审计和新协议调用方会分裂。
    if content is not None:  # 新增代码+ClaudeCodeContentParity：只有调用方明确传 content 时才覆盖 MCP 输出；如果没有这行代码，所有工具都会改变为非 JSON 文本输出。
        result["content"] = [dict(block) for block in content]  # 新增代码+ClaudeCodeContentParity：复制 content block 防止外部列表后续被改动；如果没有这行代码，运行时结果可能被调用方意外污染。
    if debug is not None:  # 新增代码+ClaudeCodeContentParity：只有存在调试信息时才输出 debug；如果没有这行代码，artifact_path 等证据无法随结果返回。
        result["debug"] = dict(debug)  # 新增代码+ClaudeCodeContentParity：复制 debug 字典作为稳定快照；如果没有这行代码，调试信息可能被后续代码改写。
    return result  # 修改代码+ClaudeCodeContentParity：返回兼容旧 payload 和新 content 的成功结果；如果没有这行代码，工具调用方拿不到执行结果。
# 修改代码+ClaudeCodeContentParity：函数段结束，success_result 到此结束；如果没有这个边界说明，用户不容易看出成功结果格式。


def mcp_content_from_result(result: dict[str, Any]) -> dict[str, Any]:  # 修改代码+ClaudeCodeContentParity：函数段开始，把 runtime 结果转成 MCP content；如果没有这段函数，stdio server 会重复写包装逻辑。
    explicit_content = result.get("content")  # 新增代码+ClaudeCodeContentParity：先读取显式 content blocks；如果没有这行代码，screenshot/zoom 即使生成图片块也不会被 MCP 返回。
    if isinstance(explicit_content, list) and explicit_content:  # 新增代码+ClaudeCodeContentParity：只在 content 是非空列表时使用新协议输出；如果没有这行代码，坏 content 类型会破坏 MCP 响应。
        return {"content": [dict(block) for block in explicit_content], "isError": not bool(result.get("ok", False))}  # 新增代码+ClaudeCodeContentParity：返回 ClaudeCode-compatible content blocks；如果没有这行代码，图片块会被重新包成不可见 JSON。
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, sort_keys=True)}], "isError": not bool(result.get("ok", False))}  # 修改代码+ClaudeCodeContentParity：无显式 content 时保留旧 JSON 文本回退；如果没有这行代码，非截图工具输出会被破坏。
# 修改代码+ClaudeCodeContentParity：函数段结束，mcp_content_from_result 到此结束；如果没有这个边界说明，用户不容易看出 MCP 包装范围。
