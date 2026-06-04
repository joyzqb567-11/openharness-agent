# Phase97 Controlled Notepad Live Edit Design

## Purpose

Phase97 turns the current Windows Computer Use stack from a controlled physical input smoke into a visible, useful, low-risk local application workflow.

The goal is to prove that the agent can operate a normal Windows application under explicit authorization: launch a dedicated Notepad instance, focus only that target window, input controlled text through the approved SendInput path, save to a controlled project file, and verify the saved file contents.

This phase deliberately uses Phase97 instead of Phase96 because the current workspace already contains untracked Phase96 files for `controlled_physical_live_smoke`. Reusing Phase96 for Notepad would risk overwriting or confusing that existing candidate work.

## Scope

Phase97 covers one representative app: Windows Notepad.

The workflow is:

1. Create an isolated run directory under `learning_agent/memory/computer_use/phase97_controlled_notepad_live_edit/`.
2. Launch or attach to a dedicated Notepad test file created by the phase.
3. Verify the target process is `notepad.exe` and the target title/path matches the Phase97 run.
4. Send only the fixed Phase97 test content through the controlled physical SendInput chain.
5. Save the file to the controlled run directory.
6. Read the saved file and verify the expected content exists.
7. Write a sanitized JSON report and a stable CLI token line.
8. Pass the real visible `learning_agent/start_oauth_agent.bat` terminal acceptance scenario.

Out of scope:

- General control of every Windows application.
- Editing user documents outside the controlled Phase97 directory.
- Sending arbitrary raw user text to the desktop.
- Operating PowerShell, terminal windows, Codex UI, login windows, security prompts, installers, or system settings.
- Replacing Phase92-95 architecture.

## Architecture

Phase97 should compose the existing layers instead of creating a parallel controller:

- Phase95 `WindowsControlledPhysicalSendInputSender` for low-level input dispatch.
- Phase72 or existing safety boundary checks for unsafe process/window refusal.
- Existing runtime file helpers for JSON evidence writes.
- Existing acceptance controller scenario format for Rule 17 visible terminal validation.

The new runtime should live in a focused module, tentatively:

`learning_agent/computer_use/controlled_notepad_live_edit.py`

It should expose:

- `PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_MARKER`
- `PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK_TOKEN`
- `run_phase97_controlled_notepad_live_edit_contract(...)`
- `phase97_cli_line(report)`
- `main(argv=None)`

The default contract remains safe: it must not touch the real desktop unless both a request gate and an enable gate are explicitly true.

## Safety Rules

Phase97 must keep a strict target boundary:

- Only the Phase97-created Notepad file/window is eligible.
- The target process must be `notepad.exe`.
- The target title or file path must contain the Phase97 run identity.
- If the active window drifts away from the target, the runtime stops before sending input.
- If the candidate target is terminal-like, authentication-like, installer-like, system-settings-like, or unknown, the runtime sends zero events.
- The report must not include arbitrary raw prompt text.
- The runtime must record event counts, text length, and hashes instead of sensitive raw user text.
- Cleanup must avoid deleting user files and may leave evidence artifacts for review.

## Success Criteria

Automated success requires:

- Focused Phase97 unit tests pass.
- Adjacent Phase95/Phase97 regression tests pass.
- Windows Computer Use focused tests pass, or the plan records a narrow justified subset if the full suite is too slow.
- Compile check passes for touched source and test files.
- The scenario JSON validates with `python -m json.tool`.

Real acceptance requires:

- `learning_agent/start_oauth_agent.bat` is launched in a real visible terminal window.
- The terminal prompt receives a realistic Phase97 acceptance prompt.
- The agent invokes the terminal tool from inside that visible run.
- The final answer includes the Phase97 ready and OK tokens.
- The saved Notepad file exists under the controlled Phase97 directory.
- The saved file content matches the expected Phase97 test content.
- The visible-terminal result JSON records `completed=true`, `prompt_sent=true`, `prompt_received=true`, `final_printed=true`, and assertion passed.

## Evidence

Phase97 should write:

- A sanitized report JSON under `learning_agent/memory/computer_use/phase97_controlled_notepad_live_edit/`.
- The saved Notepad `.txt` file under the same controlled run root.
- A learning backup under `learning_agent/test/agent_capability_phase97_controlled_notepad_live_edit_20260604/`.
- A detailed memory record under `agent_memory/agent_capability_phase97_controlled_notepad_live_edit_20260604.md`.

## Open Risks

Windows Notepad behavior varies by Windows version. Newer Notepad can restore tabs, add confirmation prompts, or change title text after save. Phase97 should avoid relying on brittle title-only matching and should prefer a controlled file path plus process/window identity evidence.

Real SendInput can affect the wrong window if focus changes between observe and act. Phase97 must recheck the target immediately before input and before save.

Rule 17 acceptance may fail if the local OAuth/model chain is unavailable. In that case, code may be implemented and automated tests may pass, but the final answer must clearly say that real visible terminal acceptance is not complete.
