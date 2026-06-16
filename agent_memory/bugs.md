# 问题与风险摘要（2026-06-16）

历史全文归档：`agent_memory/archive/2026-06-16-computer-use-mcp-v2-parity/`。

## 已关闭问题

- 旧聚合 Computer Use 工具曾可能绕过新 v2 工具面；现在 `build_tools.py` 和 `batch.py` 都有禁止名单。
- shell、PowerShell、文件 read/write/edit 曾可能被误混入桌面 MCP；现在工具名和 batch 参数都有防线。
- 写动作无 host 时曾可能 no-op 假成功；现在 mutating action 缺 host 会返回明确失败。
- `left_mouse_up` 曾缺少坐标合同；现在 schema 要求 x/y，执行证据保留释放点。
- `hold_key` 曾存在 keys 参数和执行层不一致风险；现在对齐 keys 数组，并有异常清理和 batch 失败传播测试。
- Phase41 图片结果测试曾走旧 wrapper；现在迁移到 v2 MCP wrapper。
- `zoom` 曾被当成普通动作或整图 observe；现在是只读观察语义，并尝试返回局部裁剪 `image_result`。

## 仍需关注风险

- 真实可见终端交互验收尚未完成；不能只凭单元测试声明开发完成。
- `zoom` 裁剪依赖源截图和窗口 rect；如果真实观察结果缺少 rect，会返回明确失败并保留原观察文本。后续可从 session 状态或 controller active window 增加兜底 rect。
- `inferred_ant_mcp/actions.py` 仍保留直接调用 `zoom` 的无 host 错误兜底；正常 runtime 已把 zoom 分发到 `observation.py`，这个分支只是防止未来直接调用动作层时误报 unknown tool。
- 真实 Windows 桌面行为还需要更多端到端用例覆盖，例如打开记事本、输入文字、局部 zoom 观察文字、再执行清理。

## 验证备注

最近一次聚焦测试 47 个通过。最终仍需执行 AGENTS 规则十七定义的真实可见终端交互验收。
