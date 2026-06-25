# Desktop GUI Shell V2 Task 10 学习副本

本目录保存 Task 10 “长任务 Harness GUI 面板”涉及的新写和修改代码副本，方便后续逐行学习和对照。

- `code_copies/gui_bridge.py`：后端 GUI bridge，包含 `/v2/gui/harness/status`、`/pause`、`/resume` 和 Harness payload 构建逻辑。
- `code_copies/test_gui_harness_panel_contract.py`：后端合同测试，验证 active goal、queue、checkpoint 顺序、blocked reason 和结构化 pause/resume 响应。
- `code_copies/guiClient.ts`：前端 GUI client，包含 Harness status 和控制请求方法。
- `code_copies/guiClient.test.ts`：前端 client 测试，验证 Harness endpoint URL、token 和响应解析。
- `code_copies/AppShell.tsx`：桌面 GUI 主壳，负责首屏加载、轮询 Harness 状态和接线控制回调。
- `code_copies/StatusInspector.tsx`：右侧检查器，新增“任务”页签并渲染 HarnessPanel。
- `code_copies/HarnessPanel.tsx`：长任务面板组件，显示当前目标、队列、checkpoint、阻塞原因和后端支持的控制按钮。
- `code_copies/runtime-panels.css`：Harness 面板视觉样式，保证右侧栏内长文本可换行且布局不溢出。

本轮验证命令：

```powershell
python -m unittest learning_agent.tests.test_gui_harness_panel_contract
cd apps/desktop
npm test -- --run
npm run lint
```
