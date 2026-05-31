---
name: mcp
description: Use when MCP servers, external tools, resources, prompts, auth metadata, or stream lifecycle are relevant.
---

# MCP

入口顺序：先 read `learning_agent/skills/tool_list.md`，再 read 本文件。

本 skill 只判断是否进入 MCP 能力。需要细节时，再按场景读取：

- `learning_agent/skills/mcp/rules/resources_prompts.md`
- `learning_agent/skills/mcp/rules/auth_transport.md`

边界：
- MCP 是外部能力边界，不是模型直接拥有外部系统。
- 先确认配置、权限和工具结果，再声称已访问外部资源。
- 实际执行仍通过 `read / write / edit / bash` 以及运行时已接入的工具桥完成。
