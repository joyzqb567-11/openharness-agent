# Agent Capability Phase 24 Real Chrome Extension E2E

## 目标

- 把 Phase 18 的本地协议自检，推进到更接近真实 Chrome extension 的端到端闭环。
- 修复真实 Chrome 启动 native host 时工作目录不稳定的问题。
- 提供一个终端命令，明确报告真实扩展连接、配对、浏览器侧 prompt 入队和 bridge 文件是否在同一项目目录。

## 成功标准

- native host launcher 会把项目根目录写入环境变量，Chrome 启动 host 时不再依赖当前工作目录。
- native host 会优先读取环境变量里的项目根目录，并把 bridge state 和 runtime queue 写回同一个 learning_agent memory 目录。
- `/chrome real-extension-e2e-check` 能输出 `phase24_real_extension_e2e_check`。
- 命令能区分 `real_extension_connected`、`paired`、`browser_prompt_queued`、`workspace_lock_ok`。
- 自动化测试覆盖 launcher、native host 路径解析、终端命令和状态输出。
- 修改代码备份到 `learning_agent/test/agent_capability_phase24_real_chrome_extension_e2e_20260602/`。
- 最终必须运行 `learning_agent/start_oauth_agent.bat` 的真实可见终端验收；如果当前机器真实扩展未安装或未连接，则必须明确说明真实扩展连接仍未完成，不能把 `false` 说成 `true`。

## 范围边界

- 本阶段允许补强 native host 启动路径、诊断命令和验收证据。
- 本阶段不强行安装真实 Chrome 扩展，因为扩展 ID 需要用户 Chrome 加载 unpacked extension 后确认，不能伪造。
- 本阶段不会保存 cookie、token、密码或任何浏览器隐私数据。

## 执行步骤

1. 写 Phase 24 自动化红线测试。
2. 修改 native host launcher，写入稳定工作区环境变量。
3. 修改 native host，优先按环境变量定位项目根目录。
4. 新增 `/chrome real-extension-e2e-check` 诊断命令。
5. 更新 `/chrome` 状态菜单入口。
6. 备份代码和测试。
7. 运行 focused tests、相关回归、py_compile、node --check。
8. 运行真实可见终端验收。

## 停止条件

- 如果真实 Chrome 扩展未加载或 native host 未连接，只能声明代码和自动化验收完成，不能声明真实扩展连接成功。
- 如果真实可见终端无法打开、观察或输入，必须请求用户手动验收。
