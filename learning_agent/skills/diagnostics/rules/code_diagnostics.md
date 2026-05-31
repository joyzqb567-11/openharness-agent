# Code Diagnostics Rule

使用场景：
- 需要理解 Python 文件结构、定位定义、查看语法诊断或批量做只读检查。

规则：
- 先用 `read` 或 `bash` 搜索确认代码事实，再判断原因。
- 符号列表适合了解文件结构；定义查找适合追踪类、函数或方法来源。
- 诊断输出只能证明当前检查发现的问题，不要把没有检查到的问题说成不存在。
- REPL 类批处理只用于安全白名单中的只读/status/symbol 工具，不用于任意代码执行。

关键词：lsp_symbols、lsp_definition、lsp_diagnostics、符号、definition、diagnostics、repl、安全白名单。
