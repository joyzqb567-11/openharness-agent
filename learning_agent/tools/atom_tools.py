"""四原子工具轻量辅助函数。"""  # 新增代码+AtomToolsSplit: 为 read/write/edit/bash 原子工具建立独立模块边界；若没有这个文件，原子工具细节只能继续散在主入口。

from __future__ import annotations  # 新增代码+AtomToolsSplit: 延迟解析类型注解；若没有这行代码，后续扩展辅助函数类型时更稳。


def rewrite_tool_result_prefix(output: str, *, old_prefix: str, new_prefix: str) -> str:  # 新增代码+AtomToolsSplit: 把复用旧工具实现得到的结果前缀改成原子工具名；若没有这行代码，write 调用会看到 write_file 成功这类不一致文本。
    return output.replace(old_prefix, new_prefix, 1)  # 新增代码+AtomToolsSplit: 只替换第一处工具名前缀；若没有这行代码，正文里出现的同名文本也可能被误改。
