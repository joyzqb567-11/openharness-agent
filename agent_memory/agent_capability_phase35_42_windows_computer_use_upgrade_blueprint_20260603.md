# Phase 35-42 Windows OS Computer Use Upgrade Blueprint

时间：2026-06-03

## 目标

把 Phase 35-42 固化为 Windows 版 OS Computer Use 后续升级蓝图，用于继续对齐 ClaudeCode 的成熟 computer-use 设计，但不把 ClaudeCode 的 macOS-only 执行器误报为 Windows 已完成能力。

## 阶段列表

- Phase 35：真实安全窗口 UIA smoke harness，先证明真实依赖状态，不再用 fake provider 冒充真实 UIA。
- Phase 36：Windows.Graphics.Capture provider 合同和诊断接入，GDI fallback 继续保留。
- Phase 37：SendInput 动作执行器，补齐 `double_click/type_text/press_key/scroll` 等 schema 与后端错位。
- Phase 38：Windows ComputerUseApproval 模型，补 app allowlist、grant flags 和禁止目标提示。
- Phase 39：DPI、多显示器和坐标模型。
- Phase 40：全局 abort、turn cleanup、通知和锁释放。
- Phase 41：截图结果 artifact / image result 对模型可见。
- Phase 42：Phase 35-41 最终真实端到端验收矩阵。

## 当前依赖事实

本机探测结果：

- `uiautomation=False`
- `comtypes=False`
- `winrt.windows.graphics.capture` 不可用
- `winsdk.windows.graphics.capture` 不可用
- `sys.platform=win32`

因此 Phase 35 不能直接声明真实 UIA 已可用；正确目标是先做真实安全 smoke harness 和诚实诊断。

## 成功标准

- 每个阶段有 TDD 红灯、绿灯、自动化测试、真实可见终端验收和独立 verifier。
- 每个阶段有 agent_memory 记录和 learning_agent/test 学习备份。
- 每个阶段明确说明“已证明什么”和“未证明什么”。
- 未接入 WGC/SendInput/真实 UIA 依赖前，不得声称已达到 ClaudeCode computer-use 的 native 执行成熟度。

## 停止条件

- 需要安装系统依赖、改注册表、调整 Windows 安全设置时必须停止并请求用户确认。
- 目标窗口涉及终端、Codex UI、安全/隐私设置、密码管理器、认证弹窗、验证码/OTP 或 Windows Run 时必须停止。
- 真实可见终端验收未完成时，不能声明开发完成。

## 正式蓝图文件

- `docs/superpowers/plans/2026-06-03-phase35-42-windows-computer-use-claudecode-alignment.md`

