# Phase 3 高层浏览器工具计划

## 目标

把现有低层浏览器动作补成更接近真实 agent 使用习惯的高层入口：批量填表、快捷键发现、快捷键执行。高层工具必须复用既有底层工具，不绕开真实 Chrome 的审计、脱敏、标签页上下文门禁。

## 成功标准

1. `browser_form_input` 可以按字段列表顺序调用 `browser_type` 或 `browser_type_secret`，并可选提交表单。
2. `browser_shortcuts_list` 输出稳定、可读、机器可检查的快捷键清单。
3. `browser_shortcuts_execute` 使用快捷键别名执行真实 `browser_press_key`。
4. 敏感字段只允许走 `secret_env_var`，普通返回不回显明文。
5. 新工具进入 MCP `TOOLS`、分发器、重试/真实 Chrome 写动作门禁。
6. 单元测试先红后绿，旧浏览器测试回归通过。

## 实施步骤

1. 新增 `learning_agent/tests/test_browser_high_level_tools_stage15.py` 作为红灯测试。
2. 新增 `learning_agent/browser/high_level_tools.py`，集中保存字段规划和快捷键映射。
3. 修改 `learning_agent/browser_automation_mcp_server.py` 暴露三个高层工具并复用底层动作。
4. 复制 Phase 3 新增/修改文件到 `learning_agent/test/agent_capability_completion_20260601/phase3/`。
5. 运行 Phase 3 测试、浏览器相关回归测试和 `py_compile`。

## 停止条件

如果发现现有底层工具无法安全复用，先停止并记录到 `agent_memory/bugs.md`，不直接绕过安全层。
