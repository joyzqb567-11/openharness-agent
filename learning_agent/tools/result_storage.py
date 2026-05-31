"""长工具结果落盘辅助函数。"""  # 新增代码+ResultStorageSplit: 把结果文件名、inline limit 和摘要格式从主入口拆出；若没有这个文件，长输出策略仍埋在 LearningAgent 大类。

from __future__ import annotations  # 新增代码+ResultStorageSplit: 延迟解析类型注解；若没有这行代码，后续扩展路径类型时更容易受导入顺序影响。


def safe_tool_artifact_name(tool_name: str) -> str:  # 新增代码+ResultStorageSplit: 把工具名转换成安全文件名片段；若没有这行代码，MCP 工具名里的特殊字符可能生成非法路径。
    cleaned_chars = [char if char.isalnum() or char in {"_", "-", "."} else "_" for char in tool_name]  # 新增代码+ResultStorageSplit: 只保留字母数字和少量安全符号；若没有这行代码，冒号、斜杠等字符可能破坏文件路径。
    cleaned_name = "".join(cleaned_chars).strip("._-")  # 新增代码+ResultStorageSplit: 合并字符并去掉首尾容易混淆的分隔符；若没有这行代码，文件名可能变成隐藏文件或空壳分隔符。
    return (cleaned_name or "tool_result")[:80]  # 新增代码+ResultStorageSplit: 空名回退并限制长度；若没有这行代码，极长工具名可能生成难读或超长文件名。


def clamp_tool_result_inline_limit(configured_limit: int | str | None, *, default_limit: int = 8000) -> int:  # 新增代码+ResultStorageSplit: 把工具结果 inline 上限夹到安全范围；若没有这行代码，单个工具可能把巨量结果塞回模型上下文。
    try:  # 新增代码+ResultStorageSplit: 尝试把目录元数据里的限制转成整数；若没有这行代码，字符串配置会直接导致比较异常。
        raw_limit = int(configured_limit or default_limit)  # 新增代码+ResultStorageSplit: 空值使用默认限制；若没有这行代码，None 或 0 会让策略含义不清。
    except (TypeError, ValueError):  # 新增代码+ResultStorageSplit: 捕获无法转整数的异常；若没有这行代码，坏元数据会中断工具执行。
        raw_limit = default_limit  # 新增代码+ResultStorageSplit: 坏配置回退默认值；若没有这行代码，模型一次遇到坏工具元数据就会失败。
    return max(2000, min(raw_limit, 8000))  # 新增代码+ResultStorageSplit: 限制 inline 范围在 2000 到 8000；若没有这行代码，上下文体积会失控或摘要太短。


def summarize_offloaded_output(output: str, *, inline_limit: int, artifact_text: str) -> str:  # 新增代码+ResultStorageSplit: 构造长结果落盘后的上下文摘要；若没有这行代码，主类会继续手写摘要格式。
    head_limit = max(1000, inline_limit // 2)  # 新增代码+ResultStorageSplit: 为摘要保留前半段内容；若没有这行代码，模型可能看不到结果开头的关键信息。
    tail_limit = max(500, inline_limit // 4)  # 新增代码+ResultStorageSplit: 为摘要保留尾部内容；若没有这行代码，模型可能看不到日志末尾的错误或结论。
    summary = output[:head_limit] + "\n\n...[中间内容已保存到文件，未塞入模型上下文]...\n\n" + output[-tail_limit:]  # 新增代码+ResultStorageSplit: 构造头尾摘要；若没有这行代码，长结果落盘后模型完全没有上下文线索。
    return "\n".join([  # 新增代码+ResultStorageSplit: 返回机器和人都能读懂的压缩工具结果；若没有这行代码，模型不知道完整输出在哪里。
        "工具结果过长，已保存完整输出。",  # 新增代码+ResultStorageSplit: 明确说明发生了长结果持久化；若没有这行代码，用户和模型会误以为这是完整结果。
        f"Full output saved to: {artifact_text}",  # 新增代码+ResultStorageSplit: 给出完整结果文件路径；若没有这行代码，后续无法打开完整输出。
        f"原始字符数={len(output)}，上下文内摘要字符数约={len(summary)}。",  # 新增代码+ResultStorageSplit: 给出压缩前后规模；若没有这行代码，审计无法判断丢入上下文的比例。
        "上下文摘要：",  # 新增代码+ResultStorageSplit: 标记下面是摘要而不是完整结果；若没有这行代码，模型可能误把摘要当全文。
        summary,  # 新增代码+ResultStorageSplit: 放入头尾摘要帮助模型继续推理；若没有这行代码，落盘后模型没有可用内容。
    ])  # 新增代码+ResultStorageSplit: 压缩结果文本结束；若没有这行代码，Python 调用语法不完整。
