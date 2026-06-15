"""compact 专用提示词合同。"""  # 新增代码+CompactPrompt: 说明本文件只保存压缩摘要提示词；如果没有这行代码，compact prompt 可能继续散落在主循环里。

from __future__ import annotations  # 新增代码+CompactPrompt: 延迟解析类型注解；如果没有这行代码，跨模块类型引用更容易受导入顺序影响。

from learning_agent.core.task_state import TaskState  # 新增代码+CompactPrompt: 引入任务状态事实源；如果没有这行代码，compact prompt 无法固定携带用户原始目标。


COMPACT_NO_TOOLS_RULE = "压缩阶段只能回复文字摘要，绝对不要调用任何工具。"  # 新增代码+CompactPrompt: 固定 no-tools 规则；如果没有这行代码，压缩摘要器可能又去读日志或调浏览器。
COMPACT_SECTION_HEADINGS = [  # 新增代码+CompactPrompt: 固定九段摘要标题列表；如果没有这行代码，质量检查器无法稳定识别摘要结构。
    "Primary Request and Intent",  # 新增代码+CompactPrompt: 第一段保存用户主请求和意图；如果没有这行代码，摘要可能丢掉用户到底要什么。
    "Key Technical Concepts",  # 新增代码+CompactPrompt: 第二段保存关键技术概念；如果没有这行代码，开发任务压缩后会丢背景概念。
    "Files and Code Sections",  # 新增代码+CompactPrompt: 第三段保存文件和代码段；如果没有这行代码，代码任务压缩后会丢改动位置。
    "Errors and fixes",  # 新增代码+CompactPrompt: 第四段保存错误和修复；如果没有这行代码，调试任务会重复踩坑。
    "Problem Solving",  # 新增代码+CompactPrompt: 第五段保存解决过程；如果没有这行代码，模型不知道哪些路径试过。
    "All user messages",  # 新增代码+CompactPrompt: 第六段保存全部用户消息；如果没有这行代码，多轮短句容易丢上下文。
    "Pending Tasks",  # 新增代码+CompactPrompt: 第七段保存待办任务；如果没有这行代码，模型可能漏掉未完成事项。
    "Current Work",  # 新增代码+CompactPrompt: 第八段保存当前工作；如果没有这行代码，compact 后不知道做到哪一步。
    "Optional Next Step",  # 新增代码+CompactPrompt: 第九段保存下一步；如果没有这行代码，模型不知道继续查证还是最终回答。
]  # 新增代码+CompactPrompt: 结束九段标题列表；如果没有这行代码，Python 列表语法不完整。


def build_compact_prompt(task_state: TaskState, compact_reason: str) -> str:  # 新增代码+CompactPrompt: 函数段开始，生成压缩摘要专用提示词；如果没有这段函数，compact.py 会继续临时拼提示词。
    section_contract = "\n".join(f"{index}. {heading}" for index, heading in enumerate(COMPACT_SECTION_HEADINGS, start=1))  # 新增代码+CompactPrompt: 生成九段标题文本；如果没有这行代码，提示词不会稳定要求九段结构。
    return "\n\n".join([  # 新增代码+CompactPrompt: 拼接完整提示词；如果没有这行代码，调用方拿不到 compact summarizer 的合同文本。
        COMPACT_NO_TOOLS_RULE,  # 新增代码+CompactPrompt: 把 no-tools 规则放在最前；如果没有这行代码，模型容易把压缩当成继续执行任务。
        "你是 OpenHarness 的专用上下文压缩摘要器，只能总结已经给你的消息和 TaskState。",  # 新增代码+CompactPrompt: 明确摘要器身份；如果没有这行代码，模型可能尝试继续完成主任务。
        "不要读取日志，不要打开浏览器，不要运行 shell，不要调用 MCP，不要补做主任务。",  # 新增代码+CompactPrompt: 明确禁止外部动作；如果没有这行代码，压缩阶段可能造成真实副作用。
        f"compact_reason: {compact_reason}",  # 新增代码+CompactPrompt: 写入触发原因；如果没有这行代码，摘要无法解释为什么压缩。
        task_state.to_model_summary(),  # 新增代码+CompactPrompt: 写入稳定任务状态；如果没有这行代码，原始目标和待办仍可能丢失。
        "请严格输出以下九段标题，标题文本不要翻译、不要改名、不要省略：\n" + section_contract,  # 新增代码+CompactPrompt: 写入固定九段合同；如果没有这行代码，质量检查无法稳定验收。
    ])  # 新增代码+CompactPrompt: 结束提示词拼接；如果没有这行代码，Python 调用语法不完整。


def build_compact_user_summary_message(summary_text: str) -> dict[str, str]:  # 新增代码+CompactPrompt: 函数段开始，构造压缩后继续会话的 summary message；如果没有这段函数，compact.py 会重复构造消息格式。
    return {"role": "system", "content": "<summary>\n" + str(summary_text).strip() + "\n</summary>"}  # 新增代码+CompactPrompt: 用 system summary 包裹摘要；如果没有这行代码，模型可能把摘要误当成用户新要求。


__all__ = ["COMPACT_NO_TOOLS_RULE", "COMPACT_SECTION_HEADINGS", "build_compact_prompt", "build_compact_user_summary_message"]  # 新增代码+CompactPrompt: 明确公开接口；如果没有这行代码，其他模块导入边界不清。
