# Learning Agent Skill Tool List

先用 read 读取本文件，再按任务需要读取对应 `SKILL.md`。
`SKILL.md` 是第二层入口，只做能力判断和子规则索引；更细流程必须继续读取该 skill 的 `rules/*.md`。

## 原子工具

- read：读取文件、提示词、skill、配置、测试和日志。
- write：创建或完整覆盖文本文件。
- edit：对已有文件做 old_text 到 new_text 的定点替换。
- bash：首轮常驻工具，用于执行命令、运行测试、搜索文件或调用脚本；如果没有这条说明，模型可能误以为 bash 仍要先加载 execution 才能使用。

## Skills

- file_operations：`learning_agent/skills/file_operations/SKILL.md`
- memory：`learning_agent/skills/memory/SKILL.md`
- execution：`learning_agent/skills/execution/SKILL.md`
- notebook：`learning_agent/skills/notebook/SKILL.md`
- mcp：`learning_agent/skills/mcp/SKILL.md`
- computer_use：`learning_agent/skills/computer_use/SKILL.md`
- browser_automation：`learning_agent/skills/browser_automation/SKILL.md`
- real_chrome：`learning_agent/skills/real_chrome/SKILL.md`
- delegation：`learning_agent/skills/delegation/SKILL.md`
- planning：`learning_agent/skills/planning/SKILL.md`
- diagnostics：`learning_agent/skills/diagnostics/SKILL.md`
- long_running_work：`learning_agent/skills/long_running_work/SKILL.md`
- prompt_architecture：`learning_agent/skills/prompt_architecture/SKILL.md`
- dynamicprompt：`learning_agent/dynamicprompt/dynamicprompt.md`

原则：skill 是说明书，不是额外模型工具；读取说明书后默认通过 read / write / edit / bash / tool_search 完成实际操作，后台命令生命周期等更高级执行能力再按需进入 execution 能力。
分层顺序：`tool_list.md` -> `SKILL.md` -> `rules/*.md`。不要跳过父层直接读取大量子规则。
