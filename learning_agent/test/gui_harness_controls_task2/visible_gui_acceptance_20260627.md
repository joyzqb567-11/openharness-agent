# Task 2 Harness Real Controls 可见 GUI 验收记录

## 验收时间

- 2026-06-27 14:57:46Z

## 验收对象

- 桌面窗口标题：`OpenHarness Desktop`
- GUI 分支/worktree：`codex/gui-toolchain-control-center`
- 运行窗口：真实 Electron 桌面 GUI，不是截图模拟，不是单元测试替代。
- 后端 Bridge：`http://127.0.0.1:8776`
- Renderer：`http://127.0.0.1:5177`

## 验收步骤

1. 使用 `computer-use` 连接 Windows 桌面应用列表。
2. 定位并激活 `OpenHarness Desktop` 窗口。
3. 在右侧运行检查器点击 `任务` 页签。
4. 肉眼确认 `长任务 Harness` 面板显示当前目标、队列、Checkpoints。
5. 肉眼确认控制按钮可见：`暂停`、`恢复`、`停止`、`Checkpoint`。
6. 点击 `Checkpoint` 按钮。
7. 等待 GUI 刷新后重新读取窗口可访问文本和截图。

## 可见结果

- `任务` 页签可见。
- 当前目标可见：`Visible GUI acceptance for real Harness controls`。
- 当前阶段可见：`Harness real controls`。
- 队列状态可见：`running`。
- 控制按钮可见：`暂停`、`恢复`、`停止`、`Checkpoint`。
- 点击 `Checkpoint` 后，GUI 顶部绿色反馈条显示：`checkpointed · 手动 checkpoint 已写入。`
- 当前目标描述同步更新为：`Harness real controls · Desktop GUI checkpoint 2026-06-27T14:57:46Z`
- Checkpoints 列表新增记录：`Harness real controls` / `Desktop GUI checkpoint 2026-06-27T14:57:46Z`

## computer-use 文本证据摘录

```text
区域 长任务 Harness
文本 running
文本 Visible GUI acceptance for real Harness controls
文本 Harness real controls
按钮 暂停
按钮 恢复
按钮 停止
按钮 Checkpoint
文本 队列
文本 running
文本 Checkpoints
```

点击 `Checkpoint` 后：

```text
文本 checkpointed ·
文本 手动 checkpoint 已写入。
文本 Desktop GUI checkpoint 2026-06-27T14:57:46Z
按钮 Checkpoint
文本 Checkpoints
文本 Harness real controls
文本 Desktop GUI checkpoint 2026-06-27T14:57:46Z
```

## 验收结论

- Task 2 的真实 GUI 可见验收通过。
- 本轮未点击 `停止`，目的是保留演示 run，避免破坏后续面板观察状态。
- `stop` 行为已由后端 contract 测试覆盖，按钮也已在真实 GUI 中肉眼可见。
