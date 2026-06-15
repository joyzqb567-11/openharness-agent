"""prompt surface 和 token budget 报告工具实现。"""  # 新增代码+AgentPyPhaseDReportTools: 把提示词报告工具从 agent.py 拆到 prompts 层；若没有这个文件，主 agent 仍会承载报告格式化细节。

from __future__ import annotations  # 新增代码+AgentPyPhaseDReportTools: 延迟解析类型注解；若没有这行代码，脚本模式下导入顺序更容易影响注解解析。

import json  # 新增代码+AgentPyPhaseDReportTools: token 预算报告需要把工具 schema 转成 JSON 粗估长度；若没有这行代码，工具池预算无法计算。
from typing import Any  # 新增代码+AgentPyPhaseDReportTools: 用 Any 表示传入的 agent 对象；若没有这行代码，本模块会为了类型注解反向导入 agent.py。


try:  # 修改代码+AgentPyPhaseHMcpToolRuntime: 包运行模式下导入工具目录和工具池运行时；若没有这行代码，报告工具仍会通过 agent.py 薄包装读取工具池。
    import learning_agent.tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 读取 available_tool_schemas 和 tool_schema_names 的真实实现；若没有这行代码，报告和执行器的工具池来源会分裂。
except ModuleNotFoundError as error:  # 修改代码+AgentPyPhaseHMcpToolRuntime: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀缺失会导致报告工具导入失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.catalog_runtime"}:  # 修改代码+AgentPyPhaseHMcpToolRuntime: 只允许路径模式差异进入 fallback；若没有这行代码，catalog_runtime 内部真实错误会被误吞。
        raise  # 修改代码+AgentPyPhaseHMcpToolRuntime: 重新抛出真实导入错误；若没有这行代码，排查报告工具问题会看不到根因。
    import tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下读取同一个工具池运行时；若没有这行代码，bat 入口 token_budget_report 会断开。


def evidence_event_category(event_type: str) -> str:  # 新增代码+AgentPyPhaseDReportTools: 函数段开始，把 observation event 映射为 Evidence Ledger 分类；若没有这段函数，证据账本只能显示原始事件而缺少类别帮助理解。
    if "tool_result" in event_type or event_type == "mcp_call_progress":  # 新增代码+AgentPyPhaseDReportTools: 识别工具结果和 MCP 进度事件；若没有这行代码，工具证据无法归入 tool_result。
        return "tool_result"  # 新增代码+AgentPyPhaseDReportTools: 返回工具结果分类；若没有这行代码，落盘输出等事件不会有清晰 label。
    if "policy" in event_type or "blocked_tool" in event_type:  # 新增代码+AgentPyPhaseDReportTools: 识别策略阻断相关事件；若没有这行代码，policy block 证据会混入普通观察。
        return "policy_block"  # 新增代码+AgentPyPhaseDReportTools: 返回策略阻断分类；若没有这行代码，用户难以区分这是规则阻断而非工具失败。
    if "plan" in event_type:  # 新增代码+AgentPyPhaseDReportTools: 识别计划模式确认或阻断事件；若没有这行代码，plan mode 证据无法被单独标记。
        return "plan_confirmation"  # 新增代码+AgentPyPhaseDReportTools: 返回计划确认分类；若没有这行代码，计划解锁依据不够醒目。
    if "skill" in event_type:  # 新增代码+AgentPyPhaseDReportTools: 识别 skill 加载事件；若没有这行代码，skill gate 证据无法被标记。
        return "skill_loaded"  # 新增代码+AgentPyPhaseDReportTools: 返回技能加载分类；若没有这行代码，报告看不出 skill_loaded 类事件。
    if "model" in event_type:  # 新增代码+AgentPyPhaseDReportTools: 识别模型推理或请求事件；若没有这行代码，模型相关证据无法被归类。
        return "model_inference"  # 新增代码+AgentPyPhaseDReportTools: 返回模型推理分类；若没有这行代码，模型事件只能当普通 observation。
    return "observation"  # 新增代码+AgentPyPhaseDReportTools: 兜底归类为普通观察；若没有这行代码，未知事件会没有分类。
# 新增代码+AgentPyPhaseDReportTools: 函数段结束，evidence_event_category 到此结束；若没有这个边界说明，用户不容易看出证据分类逻辑已迁出 agent.py。


def format_evidence_ledger(agent: Any, max_events: int = 12) -> list[str]:  # 新增代码+AgentPyPhaseDReportTools: 函数段开始，把最近 observation_events 格式化为 Evidence Ledger；若没有这段函数，prompt_surface_report 无法桥接观察事件。
    lines: list[str] = ["Evidence Ledger"]  # 新增代码+AgentPyPhaseDReportTools: 创建证据账本标题；若没有这行代码，报告里没有明确证据分组。
    recent_events = agent.observation_events[-max_events:]  # 新增代码+AgentPyPhaseDReportTools: 只取最新若干事件避免报告过长；若没有这行代码，长会话可能输出过多历史观察。
    if not recent_events:  # 新增代码+AgentPyPhaseDReportTools: 处理没有观察事件的情况；若没有这行代码，空证据账本会显得像工具失败。
        lines.append("- no observation events recorded yet")  # 新增代码+AgentPyPhaseDReportTools: 输出清楚的空状态；若没有这行代码，用户不知道是没有事件还是报告坏了。
        return lines  # 新增代码+AgentPyPhaseDReportTools: 返回空账本；若没有这行代码，后续循环仍会执行但没有内容。
    for event in recent_events:  # 新增代码+AgentPyPhaseDReportTools: 遍历最新事件生成账本行；若没有这行代码，观察流无法进入报告。
        event_type = str(event.get("kind", event.get("type", event.get("event_type", "observation"))))  # 新增代码+AgentPyPhaseDReportTools: 优先读取 kind 字段；若没有这行代码，tool_result_offloaded 会被误显示成 observation。
        category = evidence_event_category(event_type)  # 新增代码+AgentPyPhaseDReportTools: 计算事件分类；若没有这行代码，证据账本缺少 tool_result/policy_block 等 label。
        payload = event.get("payload", {})  # 新增代码+AgentPyPhaseDReportTools: 读取事件 payload；若没有这行代码，artifact_path 和 raw_output_chars 等关键证据无法展示。
        payload_items = []  # 新增代码+AgentPyPhaseDReportTools: 准备保存关键 payload 字段；若没有这行代码，无法控制报告只展示重点。
        if isinstance(payload, dict):  # 新增代码+AgentPyPhaseDReportTools: 只在 payload 是字典时提取字段；若没有这行代码，异常 payload 形状可能导致报告崩溃。
            for key in ("tool_name", "artifact_path", "raw_output_chars", "state", "reason", "name", "relative_path", "call_id"):  # 新增代码+AgentPyPhaseDReportTools: 按重要性挑选关键字段；若没有这行代码，证据账本可能漏掉 artifact 路径或输出长度。
                if key in payload:  # 新增代码+AgentPyPhaseDReportTools: 只展示实际存在的字段；若没有这行代码，报告会塞入大量空值。
                    payload_items.append(f"{key}={payload[key]}")  # 新增代码+AgentPyPhaseDReportTools: 格式化单个关键字段；若没有这行代码，payload 细节无法进入账本。
        payload_text = "; ".join(payload_items) if payload_items else "payload_keys=" + ",".join(sorted(payload.keys())) if isinstance(payload, dict) else f"payload={payload}"  # 新增代码+AgentPyPhaseDReportTools: 生成 payload 摘要兜底；若没有这行代码，未知事件会缺少任何 payload 线索。
        lines.append(f"- category={category}; event_type={event_type}; {payload_text}")  # 新增代码+AgentPyPhaseDReportTools: 写入证据账本行；若没有这行代码，用户看不到事件类型和关键 payload。
    return lines  # 新增代码+AgentPyPhaseDReportTools: 返回格式化后的证据账本行；若没有这行代码，调用方无法追加到报告。
# 新增代码+AgentPyPhaseDReportTools: 函数段结束，format_evidence_ledger 到此结束；若没有这个边界说明，用户不容易看出证据账本逻辑已迁出 agent.py。


def prompt_surface_report(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseDReportTools: 函数段开始，生成提示词表面报告工具输出；若没有这段函数，prompt_surface_report 无法返回真实加载清单。
    include_block_text = bool(arguments.get("include_block_text", False))  # 新增代码+AgentPyPhaseDReportTools: 读取是否包含提示词正文的开关且默认关闭；若没有这行代码，报告可能默认泄露完整提示词正文。
    include_evidence = bool(arguments.get("include_evidence", False))  # 新增代码+AgentPyPhaseDReportTools: 读取证据开关；若没有这行代码，观察事件不会按需进入报告。
    report = agent.last_prompt_surface_report  # 新增代码+AgentPyPhaseDReportTools: 读取最近一次消息装配保存的报告；若没有这行代码，工具无法知道本轮加载了哪些 block。
    lines: list[str] = ["Prompt Surface Report"]  # 新增代码+AgentPyPhaseDReportTools: 创建报告标题；若没有这行代码，输出缺少明确用途说明。
    lines.append("说明：历史设计文档/历史计划不会自动加载，除非本轮通过 read_file、read_mcp_resource、read_mcp_prompt 或其它显式读取入口读取。")  # 新增代码+AgentPyPhaseDReportTools: 明确历史文档不自动影响模型；若没有这行代码，用户可能误以为旧计划一直在上下文里。
    lines.append(f"estimated_total_tokens={report.estimated_total_tokens}")  # 新增代码+AgentPyPhaseDReportTools: 输出本轮 prompt 总 token 粗估；若没有这行代码，报告缺少整体预算视角。
    lines.append(f"compacted={report.compacted}")  # 新增代码+AgentPyPhaseDReportTools: 输出本轮是否发生压缩；若没有这行代码，用户无法知道 prompt 是否被 compact。
    lines.append("Loaded Prompt Blocks:")  # 新增代码+AgentPyPhaseDReportTools: 创建加载块明细标题；若没有这行代码，后续 block 行缺少分组。
    if not report.loaded_blocks:  # 新增代码+AgentPyPhaseDReportTools: 处理尚未构造初始消息的空报告；若没有这行代码，空列表会输出成误导性的空明细。
        lines.append("- no loaded blocks yet; call _build_initial_messages/run first")  # 新增代码+AgentPyPhaseDReportTools: 提示需要先构造消息；若没有这行代码，用户不知道为什么报告为空。
    for block in report.loaded_blocks:  # 新增代码+AgentPyPhaseDReportTools: 遍历本轮已加载的提示词块；若没有这行代码，报告不会列出任何具体 block。
        loaded_text = "loaded" if block.loaded else "not_loaded"  # 新增代码+AgentPyPhaseDReportTools: 把布尔加载状态转成可读文本；若没有这行代码，用户需要猜 True/False 的含义。
        note_text = f", note={block.note}" if block.note else ""  # 新增代码+AgentPyPhaseDReportTools: 只在有 note 时追加来源/截断说明；若没有这行代码，记忆索引元数据会丢失或输出噪声。
        lines.append(f"- id={block.block_id}; title={block.title}; source={block.source}; load_policy={block.load_policy}; priority={block.priority}; loaded={loaded_text}; status={block.status}; estimated_tokens={block.estimated_tokens}{note_text}")  # 新增代码+AgentPyPhaseDReportTools: 输出每个 block 的审计字段；若没有这行代码，用户无法复核来源、策略、状态和预算。
        if include_block_text:  # 新增代码+AgentPyPhaseDReportTools: 只有显式开启时才说明正文输出状态；若没有这行代码，include_block_text 参数没有任何可见效果。
            lines.append("  block_text=未缓存完整正文；请显式读取对应来源文件或代码入口查看正文。")  # 新增代码+AgentPyPhaseDReportTools: 避免假装拥有完整正文缓存；若没有这行代码，报告可能误导用户以为正文可审计。
    if include_evidence:  # 新增代码+AgentPyPhaseDReportTools: include_evidence 为 true 时输出 Evidence Ledger；若没有这行代码，观察事件不会桥接到提示词表面报告。
        lines.extend(format_evidence_ledger(agent))  # 新增代码+AgentPyPhaseDReportTools: 追加最近 observation_events 的证据账本；若没有这行代码，tool_result_offloaded 和 artifact_path 不会出现在报告里。
    return "\n".join(lines)  # 新增代码+AgentPyPhaseDReportTools: 合并报告行并返回工具结果；若没有这行代码，调用方拿不到可读报告。
# 新增代码+AgentPyPhaseDReportTools: 函数段结束，prompt_surface_report 到此结束；若没有这个边界说明，用户不容易看出提示词报告逻辑已迁出 agent.py。


def token_budget_report(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseDReportTools: 函数段开始，生成 token 预算报告工具输出；若没有这段函数，token_budget_report 无法工作。
    include_tools = bool(arguments.get("include_tools", True))  # 新增代码+AgentPyPhaseDReportTools: 读取是否包含工具池预算且默认开启；若没有这行代码，默认工具池列表无法按需求出现。
    report = agent.last_prompt_surface_report  # 新增代码+AgentPyPhaseDReportTools: 读取最近 prompt 装配报告作为 prompt 预算来源；若没有这行代码，预算工具没有 prompt blocks 数据。
    lines: list[str] = ["Token Budget Report"]  # 新增代码+AgentPyPhaseDReportTools: 创建报告标题；若没有这行代码，输出缺少明确用途说明。
    lines.append("Prompt blocks:")  # 新增代码+AgentPyPhaseDReportTools: 创建 prompt blocks 预算区；若没有这行代码，测试和用户找不到提示词预算分组。
    if not report.loaded_blocks:  # 新增代码+AgentPyPhaseDReportTools: 处理尚未构造初始消息的空报告；若没有这行代码，空预算会显得像正常零成本。
        lines.append("- no prompt blocks recorded yet")  # 新增代码+AgentPyPhaseDReportTools: 输出空报告提示；若没有这行代码，用户不知道需要先运行装配流程。
    for block in report.loaded_blocks:  # 新增代码+AgentPyPhaseDReportTools: 遍历已加载 block 生成预算明细；若没有这行代码，单块 token 成本不可见。
        lines.append(f"- {block.block_id}: estimated_tokens={block.estimated_tokens}; status={block.status}")  # 新增代码+AgentPyPhaseDReportTools: 输出单块 token 粗估和状态；若没有这行代码，用户只能看到总量。
    lines.append(f"estimated_total_tokens={report.estimated_total_tokens}")  # 新增代码+AgentPyPhaseDReportTools: 输出 prompt 总 token 粗估；若没有这行代码，报告不满足总预算需求。
    if include_tools:  # 新增代码+AgentPyPhaseDReportTools: 只有默认或显式要求时列出工具池；若没有这行代码，include_tools 参数无法控制输出。
        tool_schemas = catalog_runtime_from_tools.available_tool_schemas(agent)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 直连 catalog_runtime 读取当前真实可见工具池 schema；若没有这行代码，报告仍会通过 agent.py 薄包装读取工具池。
        tool_names = catalog_runtime_from_tools.tool_schema_names(agent, tool_schemas)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 直连 catalog_runtime 提取当前工具池名称；若没有这行代码，报告工具名来源仍不在 tools 层。
        schema_text = json.dumps(tool_schemas, ensure_ascii=False, sort_keys=True)  # 新增代码+AgentPyPhaseDReportTools: 把工具 schema 转成稳定 JSON 文本用于粗略估算；若没有这行代码，schema token 预算无法计算。
        schema_tokens = max(1, len(schema_text) // 4)  # 新增代码+AgentPyPhaseDReportTools: 用字符数除以四粗估工具 schema token；若没有这行代码，报告缺少工具池预算数值。
        lines.append("Current Tool Pool:")  # 新增代码+AgentPyPhaseDReportTools: 创建当前工具池分组标题；若没有这行代码，工具列表和 prompt 预算混在一起。
        lines.append(f"- tool_count={len(tool_names)}")  # 新增代码+AgentPyPhaseDReportTools: 输出当前工具数量；若没有这行代码，用户无法快速判断工具池体积。
        lines.append(f"- estimated_schema_tokens={schema_tokens}")  # 新增代码+AgentPyPhaseDReportTools: 输出工具 schema token 粗估；若没有这行代码，工具池预算不可见。
        lines.append("- tools=" + ", ".join(tool_names))  # 新增代码+AgentPyPhaseDReportTools: 输出当前工具池名称；若没有这行代码，用户无法确认哪些工具当前可见。
    return "\n".join(lines)  # 新增代码+AgentPyPhaseDReportTools: 合并预算报告行并返回；若没有这行代码，工具调用没有可读输出。
# 新增代码+AgentPyPhaseDReportTools: 函数段结束，token_budget_report 到此结束；若没有这个边界说明，用户不容易看出预算报告逻辑已迁出 agent.py。
