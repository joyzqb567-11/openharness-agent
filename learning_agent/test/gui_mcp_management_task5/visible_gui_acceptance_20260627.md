# Desktop GUI Toolchain Control Center Task 5 Visible GUI Acceptance

## Scope

- Task: MCP Management Panel.
- Worktree: `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\gui-toolchain-control-center`.
- Branch: `codex/gui-toolchain-control-center`.
- Backend: `http://127.0.0.1:8776`.
- Renderer: `http://127.0.0.1:5177`.
- Date: 2026-06-27.

## Backend Endpoint Evidence

- `GET /v2/gui/mcp/servers` returned `ok=true`, `kind=servers`, `server_count=0`, `resource_count=0`, `prompt_count=0`, `reuse_module=learning_agent.mcp.runtime`.
- `GET /v2/gui/mcp/resources` returned `ok=true`, `kind=resources`, `data=[]`.
- `GET /v2/gui/mcp/prompts` returned `ok=true`, `kind=prompts`, `data=[]`.
- Current worktree has no `mcp_servers.json`, so the expected safe GUI state is an empty MCP inventory.

## Computer Use Visible GUI Evidence

- Real visible window title: `OpenHarness Desktop`.
- The right inspector contained an `MCP` tab.
- After selecting the `MCP` tab, the visible panel showed:
  - `MCP`
  - `0 servers`
  - `0 resources`
  - `0 prompts`
  - `schema 2`
  - `暂无 MCP server 配置。`
  - `Resources` with `暂无数据`
  - `Prompts` with `暂无数据`
- Computer Use accessibility excerpt confirmed:
  - `44 区域 MCP 管理中心`
  - `46 文本 0`
  - `47 文本 servers`
  - `48 文本 0`
  - `49 文本 resources`
  - `50 文本 0`
  - `51 文本 prompts`
  - `54 文本 暂无 MCP server 配置。`

## Result

- Visible GUI acceptance passed.
- No bug was found in Task 5 implementation.
- No secret, token, header, or unsafe raw config value was visible in the GUI.
