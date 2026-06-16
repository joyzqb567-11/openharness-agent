# Computer Use MCP v2 架构说明

本文档记录 OpenHarness 当前 `computer-use` MCP v2 的工具面、执行路径和边界。它和 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/README.md` 互补：README 说明反推包目录的职责，本文档说明整个 MCP v2 从模型工具到 Windows runtime 的架构。

## 工具面

当前 `computer-use` MCP v2 一共公开 24 个模型可见工具：

```text
request_access
observe
screenshot
cursor_position
mouse_move
left_click
double_click
right_click
middle_click
triple_click
left_mouse_down
left_mouse_up
type
key
hold_key
scroll
left_click_drag
zoom
wait
read_clipboard
write_clipboard
open_application
list_granted_applications
computer_batch
```

这些工具由 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py` 定义。`bash`、`powershell`、`shell`、`read`、`write`、`edit` 等命令或文件工具不能进入 Computer Use 工具面；旧的 `computer_observe`、`computer_action`、`computer_status` 也不能作为 v2 原始工具暴露给模型。

## 两条入口

### agent-side wrapper

正式 agent 运行时优先走 agent-side wrapper。`bind_session_context.py` 从当前 agent 取出 controller、权限回调、观察记录回调、runtime trace 回调和验收事件回调，构造 `ComputerUseMcpV2Context`，再交给 `runtime.py` 分发。

这条路径会保留 OpenHarness 原有主循环能力：权限询问、先观察再动作门禁、agent-owned 窗口约束、完成收口门禁、截图 artifact、runtime trace 和真实可见终端验收事件。

### standalone stdio diagnostic

`learning_agent/mcp/servers/computer_use_server.py` 是独立 stdio server 兼容入口。它当前转发到 `learning_agent/computer_use_mcp_v2/claudecode_bridge/mcpServer.py`，用于 MCP registry、tools/list、tools/call 和 `--selftest` 诊断。

`--selftest` 会输出 `standalone_stdio_diagnostic` 所需的固定 marker：`COMPUTER_USE_MCP_V2_READY`，同时报告工具数量、工具名和无 shell 面检查结果。这个入口用于证明独立 server 可以被发现和调用，但它不是有 agent controller 的完整桌面执行路径。

## 运行时分发

`runtime.py` 是唯一分发入口。所有模型传入参数都会先经过 `protocol_normalizer.py`，再进入权限、观察、动作或 batch 分支。这个 normalizer 是 ClaudeCode-facing 字段和 Windows runtime 字段之间的唯一转换边界：

- `coordinate` 会镜像为 `x`、`y`。
- `start_coordinate` 会镜像为 `start_x`、`start_y`。
- drag 工具里的 `coordinate` 会镜像为 `end_x`、`end_y`。
- `region` 会镜像为 `x`、`y`、`width`、`height`。
- `duration` 会镜像为 `duration_seconds`。
- `bundle_id` 会镜像为 `app_name`。
- `apps` 会镜像为 `applications`。
- `actions` 会镜像为 `steps`。

- `request_access` 和 `list_granted_applications` 进入 `permissions.py`。
- `observe`、`screenshot`、`zoom` 进入 `observation.py`。
- `wait` 进入等待分支。
- `read_clipboard` 和 `write_clipboard` 进入 `clipboard.py`。
- `open_application` 进入 `applications.py`。
- `computer_batch` 进入 `batch.py`。
- 鼠标、键盘、拖拽、长按等原子动作进入 `actions.py`。

`batch.py` 会再次检查旧工具名、shell 工具名和危险参数，避免模型把禁止工具包在 batch 里绕过白名单。

## ClaudeCode 协议状态

协议常量集中在 `claudecode_protocol.py`。当前 v2 facade 已经具备 ClaudeCode 可观察协议里的主要状态：

- 权限状态：`request_access` 支持 `apps`、`grantFlags`、sentinel 风险分类、拒绝记录；`list_granted_applications` 返回 `allowedApps`、`grantFlags`、`sentinelWarnings`、`deniedApps`，同时保留旧 `grants` 兼容。
- 锁状态：`request_access` 和 `list_granted_applications` 只检查 lock，不获取 lock；观察和写动作会先 acquire lock；turn cleanup 会释放本轮持有的 desktop control lock。
- display 状态：`selectedDisplayId`、`displayPinnedByModel`、`displayResolvedForApps`、`lastScreenshotDims` 用 Python snake_case 保存在 context，返回模型时使用 ClaudeCode camelCase。
- 结果状态：`result_blocks.py` 支持 MCP text/image content blocks；截图和 zoom 可以返回模型可见 image block，同时把 Windows artifact path 放到 `debug.artifact_path`，便于排查。

这些状态不改变 Windows backend 的截图、SendInput、UIA 或坐标核心实现；它们只让模型和 MCP 客户端看到更接近 ClaudeCode 的协议面。

## tools/list 动态注入

`claudecode_bridge/mcpServer.py` 在 `tools/list` 时会尝试读取 Windows 安全应用 inventory，并把候选应用追加到 `request_access.description`。读取最多等待 `1.0` 秒；超时或异常时返回静态 schema，并通过 runtime trace 记录 `computer_use_tools_list_app_inventory`。

这和 ClaudeCode 的思路一致：模型在申请 access 前能看到“可以申请哪些应用”的提示，但工具 schema 本身仍保持稳定，避免 app inventory 失败影响 MCP server 可用性。

## Bridge wrapper

正式 agent 侧调用 `learning_agent/computer_use_mcp_v2/claudecode_bridge/wrapper.py`。这个 wrapper 当前负责四件事：

- 绑定同一个 `ComputerUseMcpV2Context`，让权限、lock、display、截图 artifact 和 turn cleanup 都走 agent 主循环同一事实源。
- 每次工具调用记录 `current_tool_use_context`，包括工具名、参数、`call_id` 和 session id。
- 把 MCP `content` blocks 转成 agent model blocks；公开 JSON 里只放轻量摘要，完整 image block 保存在 agent 上，避免重复复制 base64。
- 在 abort 或异常路径调用 `cleanup_agent_side_turn`，和主循环 finally cleanup 使用同一套 cleanup runtime。

`toolRendering.py` 使用 ClaudeCode 可观察字段名渲染工具消息：`coordinate`、`start_coordinate`、`region`、`direction`、`amount`、`text`、`duration`、`bundle_id`、`apps`、`actions`。

## Windows 执行边界

`inferred_ant_mcp` 不直接执行 Win32、UIA、SendInput 或截图。真实 Windows 能力在 `learning_agent/computer_use_mcp_v2/windows_runtime/` 下：

- `mcp_session_adapter.py`：把 v2 原子工具映射到 OpenHarness 已有 controller 和截图 artifact 链。
- `internal_adapter_tools.py`：内部 facade，只允许 v2 内部复用旧成熟观察/动作能力，不把旧工具名重新暴露给模型。
- `mcp_executor.py`：独立 executor 和诊断路径使用的执行封装。

这层边界的设计目的很简单：模型看到的是 ClaudeCode 风格 MCP 工具；Windows 真实执行仍由 OpenHarness 自己的 runtime 管理。

## zoom 语义

`zoom` 是只读观察工具。它不会点击、移动鼠标或输入键盘。运行时把它和 `observe`、`screenshot` 放在同一个观察分支；host adapter 再交给 `windows_runtime/mcp_session_adapter.py`。如果源截图和窗口 rect 足够，adapter 会裁剪出局部 PNG，并把它作为模型可见 `image_result` 返回。

缺少 host 时，`zoom` 返回 `zoom_unavailable_without_host`；缺少截图、rect 或坐标映射时，结果会带明确失败原因，而不是假装放大成功。

## 对齐边界

已经对齐：

- ClaudeCode 风格 `mcp__computer-use__*` 工具名前缀。
- 原子化桌面工具面。
- 旧聚合工具和 shell/file 工具隔离。
- 只读观察和写动作语义区分。
- 无 host 写动作失败，不再 no-op 假成功。
- 图片 artifact 和模型可见 image_result 链路。
- ClaudeCode-compatible 主字段和旧 OpenHarness 字段双兼容。
- app allowlist、grant flags、sentinel warnings 和 denied apps。
- MCP text/image content blocks 与 Windows debug artifact 并存。
- request/list defers-lock、观察/动作 acquire-lock、turn cleanup release-lock。
- display state 的 camelCase 模型协议和 snake_case 内部状态。
- `tools/list` 动态 Windows app inventory 注入。
- agent-side wrapper 的 current tool use context、`call_id`、content block 映射和 abort cleanup hook。

不能代码级对齐：

- ClaudeCode 底层是 macOS native package。
- OpenHarness 底层是 Windows in-tree runtime。

因此，本项目追求接口、数据、行为和安全边界对齐，而不是复制 ClaudeCode 底层 native package 源码。
