# Computer Use ClaudeCode Alignment Matrix

- level=CLAUDECODE_ALIGNMENT_PARTIAL
- aligned=11/14
- partial=3
- missing=0
- visible_terminal_gate=false
- claudecode_parity=false
- claudecode_parity_or_better=false

## Dimensions
- CA01 `aligned` MCP request_access tool surface
- CA02 `aligned` request_access session grants
- CA03 `aligned` installed app inventory hardening
- CA04 `aligned` native permission diagnostics
- CA05 `aligned` display and coordinate state
- CA06 `aligned` model visible screenshots
- CA07 `partial` real desktop input dispatch
- CA08 `aligned` target identity and drift guard
- CA09 `aligned` computer use lock and stale recovery
- CA10 `aligned` global abort hotkey
- CA11 `aligned` turn cleanup and unhide
- CA12 `aligned` tool rendering and status
- CA13 `partial` 7 of 7 real GUI benchmark support
- CA14 `partial` final visible terminal proof

## Excluded Platform Differences
- `macos_tcc`: ClaudeCode macOS TCC 权限不适用于 Windows。
- `swift_helper`: ClaudeCode Swift helper 是 macOS 原生实现，Windows 使用 Win32/UIA/SendInput 等等价能力。
- `external_mcp_package_internals`: 外部 MCP 包内部代码不属于 OpenHarness 仓库可控范围。

## Evidence
- manifest=learning_agent\memory\computer_use\claudecode_alignment\claudecode_alignment_evidence_20260613.json
- final_visible_run_dir=
