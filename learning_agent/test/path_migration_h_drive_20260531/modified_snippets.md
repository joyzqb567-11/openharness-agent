# H 盘路径修复学习备份

本次修改原因：当前项目实际运行目录是 `H:\codexworkplace\sofeware\OpenHarness-main`，但部分运行配置和协作说明仍写着旧的 `D:\codexworkplace\software\OpenHarness-main`。

## 修改 1：MCP server 启动参数

文件：`learning_agent/mcp_servers.json`

旧路径：

```text
D:\codexworkplace\software\OpenHarness-main\learning_agent
```

新路径：

```text
H:\codexworkplace\sofeware\OpenHarness-main\learning_agent
```

原因：如果 MCP server 继续指向 D 盘，当前 H 盘项目启动 `browser_search`、`workspace_tools`、`browser_automation` 时可能会找不到文件，或者误启动旧项目副本。

## 修改 2：项目协作规则路径

文件：`AGENTS.md`

旧路径：

```text
D:\codexworkplace\software\OpenHarness-main
```

新路径：

```text
H:\codexworkplace\sofeware\OpenHarness-main
```

原因：如果规则文件继续写 D 盘，后续 agent 会把学习备份和真实终端验收脚本定位到错误目录。

## 修改 3：项目记忆中的根目录

文件：`agent_memory/context.md`

旧路径：

```text
D:\codexworkplace\software\OpenHarness-main
```

新路径：

```text
H:\codexworkplace\sofeware\OpenHarness-main
```

原因：如果项目记忆继续写旧根目录，后续任务恢复上下文时会误以为 D 盘才是当前项目。
