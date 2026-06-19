---
name: notebook
description: Use when .ipynb notebooks must be inspected or edited without breaking notebook structure.
---

# Notebook

入口顺序：先 read `learning_agent/skills/tool_list.md`，再 read 本文件。

本 skill 只判断是否进入 Notebook 能力。需要细节时，再读取：

- `learning_agent/skills/notebook/rules/notebook_cells.md`

边界：
- `.ipynb` 是结构化 JSON，不要把它当普通文本随意替换。
- 先定位 cell，再改具体 cell 内容。
- 实际执行默认通过 `read / write / edit / bash / tool_search` 完成；后台命令生命周期等更高级执行能力需要按需加载 execution 能力或运行时已接入的工具桥完成。
