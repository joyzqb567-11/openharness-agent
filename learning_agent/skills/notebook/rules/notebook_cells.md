# Notebook Cells Rule

使用场景：
- 目标文件是 `.ipynb`，需要查看或修改 notebook cell。

规则：
- 先读取 notebook cell 索引、类型和 source 摘要。
- 修改时指定 cell index 和新 source。
- 不要用普通文本替换随意改 `.ipynb` JSON，除非用户明确要求 raw JSON。
- 修改后尽量做 JSON 解析或 notebook 专用检查。

关键词：notebook_read、notebook_edit、Notebook cell、cell index、source、.ipynb。
