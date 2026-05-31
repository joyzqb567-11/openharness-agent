# Stable Memory Rule

使用场景：
- 用户给出长期偏好、稳定项目事实、反复约束或以后运行也应该记住的信息。

规则：
- 写入前确认信息是稳定事实，不是临时步骤。
- 不保存 API key、密码、token、cookie、身份证件、隐私内容或未确认猜测。
- 目标 agent 的长期记忆默认是 `memory.md`。
- Codex 开发本项目时维护的 `agent_memory/context.md`、`progress.md`、`bugs.md` 不属于目标 agent 默认提示词。

关键词：append_memory、memory.md、长期记忆、稳定事实、用户偏好、不要保存秘密。
