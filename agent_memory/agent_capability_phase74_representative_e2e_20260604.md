# Phase74 Representative Real App E2E Matrix

Date: 2026-06-04

Status: completed.

Implemented:
- Added `learning_agent/computer_use/representative_e2e_matrix.py`.
- Added `learning_agent/tests/test_windows_computer_use_representative_e2e_phase74.py`.
- Added `learning_agent/acceptance_controller/scenarios/agent_capability_phase74_representative_e2e.json`.
- Exported Phase74 APIs from `learning_agent/computer_use/__init__.py`.
- Marked Phase74 complete in `task_plan.md`.
- Marked Phase74 Step 1-4 complete in `docs/superpowers/plans/2026-06-03-phase65-75-humanlike-windows-operator.md`.

Capability:
- The representative matrix covers Notepad, Explorer, Browser, standard window/dialog style, and Paint Pikachu.
- The Paint Pikachu scenario targets `mspaint.exe`, observes a canvas contract, builds 13 humanlike drag strokes, includes yellow/black/red colors, includes body, ears, black ear tips, eyes, mouth, red cheeks, arms, and lightning tail, and writes interaction evidence JSON.
- The Paint scenario explicitly reports `direct_image_file_cheat=false`; it plans a controlled PNG save path but does not directly write bitmap pixels in the safe contract.
- The matrix keeps all artifacts under `learning_agent/memory/computer_use/representative_e2e/` by default.

Verification:
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.representative_e2e_matrix'`.
- Focused Phase74 tests passed: 4 OK.
- Phase67/68/69/70/71/72/73/74 regression passed: 38 OK.
- `py_compile` passed for the Phase74 module, package init, and focused test.
- CLI self-check passed and printed:
  `PHASE74_REPRESENTATIVE_E2E_READY PHASE74_REPRESENTATIVE_E2E_OK notepad_scenario=true explorer_scenario=true browser_scenario=true window_style_scenario=true mspaint_pikachu_scenario=true real_paint_app_control=true humanlike_drawing_actions=true direct_image_file_cheat=false paint_canvas_not_blank=true pikachu_visual_elements=true representative_real_apps_passed=true`
- Real visible `start_oauth_agent.bat` terminal acceptance passed through `learning_agent/acceptance_controller/controller.ps1`: `learning_agent/acceptance_controller/runs/agent_capability_phase74_representative_e2e-20260604_062842/result.json`.
- Independent result JSON assertion passed with `completed=true`, `assertion.passed=true`, `final_printed=true`, and `permission_sent_count=0`.

Boundary:
- Phase74 is a representative safe-contract E2E matrix. It proves the cross-app workflow contracts and Paint drawing action evidence without touching real user data.
- Phase74 safe contract mode does not open Paint live, does not dispatch real mouse/keyboard input, and does not directly generate an image file.
- The next phase is Phase75 Humanlike Windows Operator Final Matrix, which must aggregate Phase65-74 and keep the Paint Pikachu fields visible in the final token.
