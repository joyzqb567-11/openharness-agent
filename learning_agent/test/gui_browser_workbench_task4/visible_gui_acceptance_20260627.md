# Desktop GUI Browser Workbench Task 4 Visible Acceptance

## 验收结论

- 验收时间：2026-06-27。
- 验收方式：使用 `computer-use` 操作真实可见的 `OpenHarness Desktop` Electron 窗口。
- 验收结果：通过。
- 真实窗口：`OpenHarness Desktop`。
- Bridge：`http://127.0.0.1:8776`，重启后监听 PID 为 `39380`。
- Renderer：`http://127.0.0.1:5177`。

## 可见 GUI 证据

- 右侧检查器打开 `浏览器` 页签后，可见 `visible chromium`、`real chrome cdp`、`chrome extension` 三个 provider 状态。
- `chrome extension` 当前显示 `未连接`，原因显示为 `chrome_extension_bridge_not_connected`，GUI 没有崩溃。
- 可见活跃目标卡片、`刷新` 按钮、URL 输入框、`记录打开` 按钮。
- 可见 `Console`、`Network`、`Downloads`、`Replay` 四个调试区块。
- `Replay` 显示 `dry_run_only`，并说明复用 `browser_replay` 默认只生成安全回放计划。

## 操作验收

- 点击 `刷新` 后，主消息区新增 `completed` 状态消息：`Browser 刷新状态：已刷新浏览器状态，未绕过 agent 权限策略执行网页动作。`
- 点击 `刷新` 后，右侧浏览器面板显示 `refresh-status · refreshed`。
- 点击 `记录打开` 后，主消息区新增 `completed` 状态消息：`Browser 记录打开：已记录打开 https://example.com 的请求；GUI 不绕过现有 Browser/agent 权限策略直接控制网页。`
- 点击 `记录打开` 后，右侧浏览器面板显示 `open · recorded`。
- 本轮 GUI 操作只记录请求与刷新状态，没有绕过 agent/browser 权限策略直接控制网页。

## Bug 与复验

- 首轮真实 GUI 验收时，点击 `刷新` 返回 `GuiClientError: 未知 GUI bridge POST 路径。`
- 根因：端口 `8776` 上运行的是旧 Python bridge 进程，进程启动时间早于 Task 4 新增 `/v2/gui/browser/*` 路由，内存中的路由表没有新接口。
- 修复：停止旧 bridge PID `21488`，从当前 worktree 重新启动 `apps/desktop/scripts/start-backend.ps1`。
- 复验：直接 POST `/v2/gui/browser/refresh-status` 返回 `ok=true`、`status=refreshed`；随后使用 `computer-use` 点击真实 GUI 中的 `刷新` 和 `记录打开`，均通过。

## 自动化门禁

- `python -m py_compile learning_agent/app/gui_browser_control.py learning_agent/tests/test_gui_browser_workbench_contract.py learning_agent/app/gui_bridge.py`：通过。
- `python -m unittest learning_agent.tests.test_gui_browser_workbench_contract learning_agent.tests.test_gui_browser_computer_panel_contract -v`：通过，6 tests。
- `npm --prefix apps/desktop run test -- browserPanel guiClient`：通过，2 files / 17 tests。
- `npm --prefix apps/desktop run lint`：通过。
- `npm --prefix apps/desktop run build`：通过。
- `git diff --check`：通过，只有 CRLF 警告。
