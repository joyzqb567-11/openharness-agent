# Text Edits Rule

使用场景：
- 读取、创建、覆盖、复制、移动、删除或精确编辑工作区文本文件。

规则：
- 修改前先 `read` 相关文件，除非用户给出完整路径和完整内容。
- 小范围改动用 `edit`，要求 old_text 足够精确。
- 新文件或明确全量重写才用 `write`。
- 搜索优先用 `bash` 执行 `rg`，比手工遍历更省上下文。
- 删除、移动、覆盖和命令执行都要尊重权限确认。

关键词：read、write、edit、bash、list_dir、glob、grep、mcp__workspace_tools__read_file、mcp__workspace_tools__write_file、mcp__workspace_tools__create_file、mcp__workspace_tools__copy_file、mcp__workspace_tools__move_file、mcp__workspace_tools__delete_file、confirm_delete、run_powershell、edit_file、edits、dry_run、风险等级。
