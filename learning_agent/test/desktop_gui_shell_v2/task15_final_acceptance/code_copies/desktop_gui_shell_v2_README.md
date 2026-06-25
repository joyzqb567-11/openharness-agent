# Desktop GUI Shell V2 Evidence Archive

Branch: `codex/desktop-gui-shell-v1`

Commit range covered by this archive:

- `997e2811 docs: add desktop gui shell v2 blueprint`
- `ebf9bfa2 docs: upgrade desktop gui v2 blueprint stages`
- `d796a541 test: add desktop gui v2 golden traces`
- `a83de0d9 feat: add desktop gui v2 protocol contract`
- `98a19ef7 feat: stream desktop gui v2 events`
- `b6a4cb2f feat: add desktop gui fake streaming adapter`
- `90815572 feat: render streaming desktop gui messages`
- `ca63266b feat: polish desktop gui composer input`
- `6c3a206d feat: add desktop gui permission v2 flow`
- `335b826e feat: add desktop gui trace inspector`
- `1e073267 feat: surface browser and computer use panels`
- `4928a0b0 feat: add desktop gui settings and diagnostics`
- `310ae1ba feat: polish desktop gui visual shell`
- `73f45d40 feat: add desktop gui session search`
- `27fba3f2 feat: add desktop gui long task harness panel`
- `7c9493a0 feat: add desktop gui packaging flow`
- `9de10b27 feat: add desktop gui v2 release gate`

## Commands Run

Layer B:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\release-gate.ps1
```

Layer A visible Electron smoke:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\start-backend.ps1
npm run dev:renderer
electron . --remote-debugging-port=9223
```

The visible Electron window was then driven through CDP against the real renderer page and real local bridge.

## Layer B Result

- Python GUI tests: 58 tests OK.
- Frontend lint: passed.
- Frontend unit tests: 45 tests passed.
- Frontend production build: passed.
- Layer A visible GUI smoke instructions: generated.
- Layer C trigger decision: printed.

## Layer A Evidence

- `layer_a_visible_acceptance/electron_initial.png`
- `layer_a_visible_acceptance/electron_cdp_after_smoke.png`
- `layer_a_visible_acceptance/electron_final_fullscreen.png`
- `layer_a_visible_acceptance/layer_a_cdp_smoke_result.json`
- `layer_a_visible_acceptance/runtime_pids.json`

Visible Electron flows confirmed in `layer_a_cdp_smoke_result.json`:

- Chinese streaming prompt completed.
- Chinese multiline prompt completed with newline input.
- Tool trace prompt completed and produced 2 tool cards.
- Permission approve path completed.
- Slow turn cancelled.
- Cancelled turn retried and completed.
- Diagnostics tab opened and rendered safe backend status.

## Prompt Matrix Result

Checked V2 visible rows currently backed by Layer A evidence:

- Streaming Chinese answer.
- Multiline Chinese persistence.
- Tool trace row.
- Permission approve/deny. Approve is in JSON evidence; deny is visible in the initial screenshot from the same Electron session history.
- Diagnostics panel opens with safe status.
- Window restart restores latest V2 session.

Rows still intentionally unchecked pending dedicated visible evidence:

- Streaming English answer.
- Safety refusal as assistant message.
- Shift+Enter newline.
- Structured token rejection GUI error.
- Structured unknown route GUI error.
- Bridge offline banner.
- Browser panel degraded state.
- Computer Use panel safe unavailable state.
- Settings panel opens.

## Known Limitations

This archive proves the V2 automated gate and a core visible Electron smoke. It does not yet prove every negative/error visible GUI row.

The Windows package is a development artifact, not a signed installer.

The long-task Harness panel exposes pause/resume as structured unsupported until the backend runtime has a real pause/resume state machine.

## Layer C Decision

Layer C not triggered: this V2 change modified GUI shell, bridge display contracts, diagnostics, release gate, packaging, or visual acceptance only. It did not modify agent runtime behavior, MCP routing, model call path, browser automation execution, Computer Use execution, or backend permission enforcement.
