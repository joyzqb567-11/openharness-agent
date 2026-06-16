# 当前任务进度摘要（2026-06-16）

历史全文归档：`agent_memory/archive/2026-06-16-computer-use-mcp-v2-parity/`。

## 成功标准

- `inferred_ant_mcp` 明确作为 ClaudeCode Computer Use 外部 MCP 包反推层存在。
- 公开工具面、运行时分发、host adapter、Windows 执行链和返回结构尽量对齐 ClaudeCode 可观察行为。
- 自动化测试覆盖工具面、禁止旧入口、Windows adapter、SendInput parity、截图 artifact、坐标缩放和 zoom 图片结果。
- 真实可见终端交互验收通过后，才允许声明“开发完成”或“验收通过”。

## 已完成

- Task 1：锁定 Computer Use MCP v2 工具面和禁止旧入口，提交 `fd267a8`、`efb40c7`。
- Task 2：写动作无 host 时改为失败，避免假成功，提交 `7c8be81`。
- Task 3：把 ClaudeCode parity 工具映射到 Windows session action，提交 `eb0affc`、`d71c41b`、`edbaa3c`。
- Task 4：通过 Windows SendInput parity 执行链接通新增鼠标键盘动作，提交 `874eb66`、`2ab6095`。
- Task 5：把 Phase41 图片结果测试迁移到 v2 MCP wrapper，提交 `488146b`。
- Task 6：修正 `zoom` 观察语义，并返回模型可见的局部裁剪截图，提交 `659b7c0`。
- Task 7：补充 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/README.md`，并按规则把超长 `agent_memory/context.md`、`progress.md`、`bugs.md` 归档压缩。
- Task 8 自动化补强：补齐 `docs/computer_use_mcp_v2_architecture.md`、`computer-use` MCP 配置注册、独立 selftest probe 和可见终端场景；原失败的 3 个接入资产测试已修复。

## Task 6 关键细节

- 红测 1：`test_zoom_returns_cropped_model_visible_image_result` 证明原先 zoom 没有 `zoom_image_result_count`，也没有局部图片结果。
- 红测 2：`test_zoom_runtime_uses_observation_semantics` 证明原先 runtime 没有把 `zoom` 写入观察记录。
- 绿码：`runtime.py` 把 `zoom` 放入观察分支；`observation.py` 调用 `host.zoom`；`windows_runtime/mcp_session_adapter.py` 从源截图裁剪局部 PNG，并追加模型可见 `image_result`。
- 验证：47 个相关测试通过。

## 当前状态

Task 7 文档与项目记忆更新已完成。Task 8 自动化验证已通过：77 个相关测试通过，独立 probe 输出 `COMPUTER_USE_MCP_V2_READY`，新/改 Python 文件 py_compile 通过。下一步是尝试真实可见终端验收。

## 停止条件

若无法打开、观察或向用户本地可见终端窗口输入内容，必须明确说明：真实可见终端交互验收未完成，不能声明开发完成。然后请求用户手动运行 `start_oauth_agent.bat` 并反馈输出或截图。
