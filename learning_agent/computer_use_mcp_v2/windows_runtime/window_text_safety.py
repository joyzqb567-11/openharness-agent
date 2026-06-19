"""Windows Computer Use 可见文本清洗工具。"""  # 新增代码+WindowTextSafety：说明本模块负责清洗窗口标题等模型可见文本；如果没有这一行，读者不容易区分它和窗口身份校验模块。

from __future__ import annotations  # 新增代码+WindowTextSafety：启用延迟类型解析；如果没有这一行，未来类型注解更容易受导入顺序影响。

from typing import Any  # 新增代码+WindowTextSafety：导入 Any 表示外部窗口字段可能是任意值；如果没有这一行，函数输入边界不清楚。


BLOCKED_CHARS = {"<", ">", "`", "|", '"', "\r", "\n", "\t"}  # 新增代码+WindowTextSafety：定义会改变提示词结构或伪装代码的危险字符；如果没有这一行，标题里的换行和代码符号可能直接进入模型上下文。


def sanitize_window_text(value: Any, max_len: int = 120) -> str:  # 新增代码+WindowTextSafety：函数段开始，清洗窗口标题和应用文本；如果没有这段函数，registry/status 可能暴露未处理的 prompt 注入文本。
    text = str(value or "")  # 新增代码+WindowTextSafety：把 None、数字等外部值统一成字符串；如果没有这一行，坏字段可能让清洗流程抛异常。
    cleaned = "".join(" " if character in BLOCKED_CHARS else character for character in text)  # 新增代码+WindowTextSafety：把危险字符替换成空格；如果没有这一行，换行、反引号和尖括号可能改变模型看到的结构。
    compact = " ".join(cleaned.split())  # 新增代码+WindowTextSafety：压缩连续空白；如果没有这一行，替换后的空格噪音会污染窗口摘要。
    return compact[: max(0, int(max_len))]  # 新增代码+WindowTextSafety：按上限截断后返回；如果没有这一行，超长窗口标题可能撑大上下文并带来额外注入面。
# 新增代码+WindowTextSafety：函数段结束，sanitize_window_text 到此结束；如果没有这个边界说明，读者不容易看出文本清洗范围。


__all__ = ["sanitize_window_text"]  # 新增代码+WindowTextSafety：声明稳定导出函数；如果没有这一行，其他模块不知道哪个 helper 是公开入口。
