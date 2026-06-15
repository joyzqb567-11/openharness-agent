# OpenHarness Computer Use ClaudeCode 完全对齐设计

日期：2026-06-15

## 背景

OpenHarness 已经具备 `computer-use` MCP server、`mcp__computer-use__*` 工具前缀、Windows runtime、权限门禁、锁、审计、截图证据和 agent-side 执行接管。与 ClaudeCode 的总体链路相比，OpenHarness 的底层平台是 Windows in-tree runtime，而 ClaudeCode 是 macOS native package 接口；这部分天然不同，本设计不追求代码级一致。

本设计只覆盖除底层 OS native 接口差异以外的对齐目标：工具表面、真实执行能力、clipboard、动态 app 信息、无 host 失败语义、测试和真实可见终端验收。

## 范围

本期选择 B：完全对齐版。固定范围如下：

- 保留现有 17 个公开工具。
- 新增并公开 7 个 ClaudeCode 观察到的工具：`zoom`、`hold_key`、`left_click_drag`、`middle_click`、`triple_click`、`left_mouse_down`、`left_mouse_up`。
- `read_clipboard` 和 `write_clipboard` 改为真实 Windows 系统剪贴板能力。
- `tools/list` 动态加入 Windows 可用应用、已授权应用、最近安全窗口等提示信息。
- 无 host 或无真实执行后端时，所有会改变桌面的 mutating action 必须明确失败，不能返回 no-op 成功。
- 每个新增工具必须接入权限、窗口目标、锁、审计、截图证据、runtime trace、测试和真实可见终端验收。

不在本期范围内：

- 不把 Windows runtime 改成 ClaudeCode 的 macOS native package 结构。
- 不改变 OpenHarness 现有安全策略：危险窗口、终端、凭据、验证码、系统安全界面仍必须拒绝控制。
- 不把 browser use、file tools、shell tools 混入 computer use MCP 表面。

## 成功标准

- `mcp__computer-use__*` 公开工具包含现有 17 个工具和新增 7 个工具。
- 新增 7 个工具都能通过 MCP schema、tool scope、dispatch、Windows adapter、controller、安全门禁和 trace。
- `zoom` 能返回局部观察结果或裁剪截图，并明确坐标映射关系。
- `hold_key`、`left_mouse_down` 等会保持输入状态的工具必须在 cleanup 中兜底释放。
- `left_click_drag` 必须使用真实 Windows mouse down、路径移动、mouse up 序列，不允许只返回模拟成功。
- `middle_click` 和 `triple_click` 必须在真实 Windows 桌面动作层可执行。
- `read_clipboard` 和 `write_clipboard` 必须读取/写入系统剪贴板，并保留失败降级和审计信息。
- 无真实 host 时，点击、输入、拖拽、按键、剪贴板写入等工具必须返回明确失败。
- 自动化测试通过后，还必须在真实可见终端 `learning_agent\start_oauth_agent.bat` 中输入真实用户 prompt 并观察 agent 输出，才能声明验收通过。

## 架构设计

### 1. 工具契约层

主文件：`learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py`

这里继续作为公开 MCP 工具 schema 的唯一事实源。新增 7 个工具需要加入 `COMPUTER_USE_MCP_TOOL_NAMES` 和 `computer_use_mcp_tools()` 返回结果。当前 forbidden/legacy/raw 阻止清单中与这 7 个工具同名的条目，需要改成正式受控工具，不再按 legacy 禁止。

工具 schema 原则：

- 参数名尽量贴近 ClaudeCode 观察到的语义。
- 坐标参数统一使用当前 OpenHarness 的窗口相对像素模型。
- 会改变桌面的工具都必须带清晰描述，说明需要先 observe 或 request access。
- `_meta` 继续标记 `openharness/runtime=computer_use_mcp_v2` 和 `openharness/capability_pack=computer_use`。

### 2. 工具可见性层

主文件：`learning_agent/tools/tool_scope.py`

新增 7 个工具只允许在 `computer_use_operation` 和 `computer_use_debug` 模式中出现。普通代码模式、源码修改模式和非 computer-use 模式继续隐藏这些桌面控制工具。

这个层的目标是保持 ClaudeCode-like 工具表面，同时不破坏 OpenHarness 的模式隔离。

### 3. Agent-side dispatch 层

主文件：

- `learning_agent/mcp/agent_adapter.py`
- `learning_agent/computer_use_mcp_v2/claudecode_bridge/wrapper.py`
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py`
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/actions.py`

`agent_adapter.py` 继续拦截 `mcp__computer-use__*`，不让真实执行依赖普通外部 MCP server call。`runtime.py` 负责把新增工具分发给 actions/host。`actions.py` 需要改掉 no-host mutating action 的假成功行为：如果没有 host 或后端不支持真实执行，必须返回结构化失败。

失败结果必须包含：

- `ok: false`
- `reason`
- `tool_name`
- `requires_host: true`
- `desktop_action_performed: false`

### 4. Windows runtime 执行层

主文件：

- `learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py`
- `learning_agent/computer_use_mcp_v2/windows_runtime/controller.py`
- `learning_agent/computer_use_mcp_v2/windows_runtime/windows_backend.py`
- 现有 SendInput、coordinate、screenshot、cleanup、permission 相关模块

新增工具映射：

- `zoom`：读取最近 observe 的窗口或传入 region，走截图裁剪/区域观察，返回局部图像、原始坐标区域、缩放后的坐标映射。
- `hold_key`：执行 key down，等待指定持续时间或包装内部动作，再 key up；所有异常路径必须 finally 释放。
- `left_click_drag`：将点列表转换成 mouse move、left down、连续 move、left up。
- `middle_click`：发送 middle button down/up。
- `triple_click`：发送三次 left click，间隔受控，保留低层事件数。
- `left_mouse_down`：发送 left button down，记录当前按下状态，交给 cleanup 兜底释放。
- `left_mouse_up`：发送 left button up，清理当前按下状态。

所有 mutating action 都必须复用 controller 的目标窗口、权限、锁、漂移检查、审计、证据和 abort gate，不允许绕开 controller 裸发 SendInput。

### 5. Clipboard 真实化

主文件：

- `learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py`
- 需要新增或复用 Windows clipboard helper

`read_clipboard` 必须从系统剪贴板读取文本。`write_clipboard` 必须写入系统剪贴板。失败时要返回明确错误，例如权限不足、剪贴板被占用、非文本格式不可读。

安全要求：

- 默认只处理文本。
- 不把剪贴板全文写入普通日志；日志记录长度和摘要。
- 如某些动作临时覆盖剪贴板，需要在 cleanup 中尽量恢复。

### 6. 动态 tools/list 信息

主文件：

- `learning_agent/computer_use_mcp_v2/claudecode_bridge/mcpServer.py`
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py`
- Windows app inventory / grant store 相关模块

`tools/list` 仍返回稳定 schema，但可以在工具 description 或 `_meta` 中加入动态提示：

- 当前可发现的安全应用名称。
- 当前已授权应用摘要。
- 最近 observe 到的安全窗口摘要。

如果动态信息不可用，不能阻塞 tools/list；应返回静态 schema，并在 `_meta` 标记动态信息不可用。

### 7. 图片与观察结果

主文件：

- `learning_agent/computer_use_mcp_v2/windows_runtime/image_messages.py`
- `learning_agent/core/agent.py`

OpenHarness 当前通过工具输出 JSON 与 artifact path 再重建 image message。这个机制可以保留，但新增 `zoom` 必须保证局部截图能被 `image_messages.py` 识别并回灌给模型。

中期可以进一步贴近 ClaudeCode 的“工具结果直接包含文本和图片内容块”模式，但本期验收以 OpenHarness 现有回灌链路稳定为准。

## 数据流

1. 用户进入 `/computer use` 或模型判断需要桌面控制。
2. tool scope 暴露 `mcp__computer-use__*` 工具。
3. 模型选择工具，例如 `mcp__computer-use__left_click_drag`。
4. `agent_adapter.py` 拦截该工具，调用 agent-side wrapper。
5. wrapper 绑定 session context、permission callback、trace callback、observation callback。
6. `runtime.py` 分发到 host/action。
7. `mcp_session_adapter.py` 把 MCP 工具转换成 controller action。
8. `controller.py` 做目标窗口、权限、锁、abort、漂移、证据和审计。
9. Windows backend 执行真实动作或返回明确失败。
10. 观察/截图类结果经 artifact 和 `image_messages.py` 回灌给模型。
11. 本轮结束时 cleanup 释放锁、鼠标、按键、临时剪贴板状态。

## 错误处理

- 缺少 host：mutating action 失败，不允许 no-op 成功。
- 缺少 observe：需要目标窗口的 action 返回要求先 observe 的错误。
- 未授权：返回 request_access 提示，不执行真实输入。
- 窗口漂移：返回 drift 错误，要求重新 observe。
- 剪贴板被占用：短暂重试后失败，并保留可读错误。
- key/mouse down 后异常：cleanup 必须释放所有按键和鼠标按钮。
- zoom 区域越界：裁剪到安全窗口范围，或返回参数错误。

## 测试设计

自动化测试至少覆盖：

- 24 个公开工具 schema 列表。
- forbidden list 不再误拦截新增 7 个工具。
- 新增工具在 operation/debug 模式可见，在 code/source 模式隐藏。
- no-host mutating action 返回失败。
- `mcp_session_adapter` 对 7 个工具的 action 映射。
- controller 仍执行权限、锁、target、audit。
- clipboard helper 的真实/降级路径。
- `zoom` 产生可被 image builder 识别的图像结果。
- `computer_batch` 中嵌套新增工具时仍阻断 shell/file surface。

真实可见终端验收至少覆盖：

- 打开 Notepad，输入文本，使用真实 clipboard 读写。
- 打开 Paint 或安全画布，使用 `left_click_drag` 绘制简单线条。
- 使用 `middle_click` 或等价安全场景验证中键事件。
- 使用 `triple_click` 验证多击动作。
- 使用 `hold_key` 搭配输入或选择动作，并确认 cleanup 后没有卡键。
- 使用 `zoom` 局部观察并让模型基于局部截图继续操作。

## 风险与缓解

- 风险：新增 mouse down/up 和 hold_key 可能导致卡键或卡鼠标。
  缓解：所有路径都接 cleanup，异常也释放。

- 风险：真实 clipboard 修改用户数据。
  缓解：只处理文本，记录摘要，必要时保存原 clipboard 并恢复。

- 风险：动态 tools/list 访问 app inventory 太慢。
  缓解：加超时和缓存，失败时回退静态 schema。

- 风险：新增工具绕过旧安全边界。
  缓解：所有 mutating action 必须通过 controller，不允许裸发 SendInput。

- 风险：工具数量对齐后模型更容易误用。
  缓解：schema 描述强调 observe、request_access 和安全窗口要求，scope 继续严格隔离。

## 实施顺序

1. 对齐工具 schema、tool names、forbidden/reserved 清单。
2. 对齐 tool scope 和 MCP registry 可见性。
3. 对齐 dispatch，并移除 no-host 假成功。
4. 实现 7 个新增工具的 Windows runtime 映射。
5. 实现真实 Windows clipboard。
6. 实现动态 tools/list app/grant/window 提示。
7. 补齐自动化测试。
8. 执行真实可见终端验收。

## 自审结果

- 未保留待定项。
- 范围已固定为 7 个新增工具和 3 个配套对齐项。
- 设计没有要求改变 Windows 与 macOS 底层接口差异。
- 所有 mutating action 都要求走 controller 安全链路。
- 已明确自动化测试不能替代真实可见终端验收。
