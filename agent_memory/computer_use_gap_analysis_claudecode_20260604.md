# 2026-06-04 ClaudeCode Computer Use vs learning_agent 差距分析记录

## 本次范围

- 已阅读 ClaudeCode 本地源码中的 Computer Use 相关目录：`D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\`。
- 已阅读 ClaudeCode 权限 UI：`D:\ClaudeCode-main\ClaudeCode-main\components\permissions\ComputerUseApproval\ComputerUseApproval.tsx`。
- 已确认 ClaudeCode 引用的 `@ant/computer-use-mcp`、`@ant/computer-use-input`、`@ant/computer-use-swift` 不在当前 `node_modules` 中，因此只能比较 ClaudeCode 本地可见源码和这些包暴露出来的接口使用方式。
- 已阅读 learning_agent 的 Windows Computer Use 关键源码：`learning_agent/computer_use/`、`learning_agent/core/agent.py`、`learning_agent/tools/catalog.py`、`learning_agent/tools/executor.py`。

## 结论

- 源码级综合估算：learning_agent 当前已有 ClaudeCode Computer Use 的约 84%。
- 若按“默认真实生产可用 + 产品级交互 polish”严格估算：约 78%。
- 主要原因：learning_agent 架构、权限、安全、闭环、Windows 观察和通用 prompt 路由已经很完整；但真实输入默认仍大量处于安全记录/受控 smoke 路线，还没有达到 ClaudeCode 那种成熟 native executor + UI 审批 + 会话渲染一体化程度。

## 关键差距

- ClaudeCode 的本地 executor 是 macOS-only，且接入 Swift 截图、Rust/enigo 输入、TCC 权限、剪贴板保存验证恢复、全局 Escape、文件锁和 React 权限 UI。
- learning_agent 是 Windows 路线，已经有 WGC/GDI 截图、UIA、SendInput guard、持久授权、安全边界、闭环执行器、通用 mode、Phase93 live execution gate。
- learning_agent 的最大短板不是“没有能力”，而是“默认真实动作还没完全产品化放开”：Phase92/93 明确 `real_actions_default_disabled=true/false equivalent safe default`，未授权和危险窗口走零事件拒绝。

## 建议百分比

- 对外单数建议：84%。
- 对内严苛生产口径：78%。
