# zqb-superagent1
zqb-superagent1

## OpenHarness Desktop GUI Shell

Codex 风格桌面 GUI 外壳位于 `apps/desktop`。它是 Electron + React + Vite 前端，默认连接本机 `learning_agent.app.gui_bridge`。

### 开发启动

先启动后端 GUI bridge：

```powershell
cd apps\desktop
npm run backend
```

再打开另一个终端启动桌面窗口：

```powershell
cd apps\desktop
npm run desktop:dev
```

`npm run backend` 会在仓库根目录启动 `python -m learning_agent.app.cli desktop-bridge`。`npm run desktop:dev` 会启动 Vite renderer 并打开 Electron 窗口。

### 验证

```powershell
cd apps\desktop
npm run lint
npm run build
```
