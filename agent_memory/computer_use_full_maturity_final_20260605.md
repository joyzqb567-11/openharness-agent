# Computer Use Full Maturity Final Acceptance

Date: 2026-06-05

Scope:
- Added final visible-terminal acceptance scenario `computer_use_full_maturity_final.json`.
- Added `phase115_main()` as the deterministic command sequence used by the visible terminal scenario.
- The final sequence runs `/computer maturity`, `/computer use --full`, `/computer use --full-confirm`, `/computer launch obsidian`, `/computer launch powershell`, and `/computer stop`.

Required final token:
`COMPUTER_USE_FULL_MATURE_READY COMPUTER_USE_FULL_MATURE_OK product_contract=true generic_discovery=true generic_real_launch=true verified_window_actions=true cleanup_recovery=true high_risk_refused=true visible_terminal_acceptance=true hardcoded_app_whitelist_required=false per_app_patch_required=false uncontrolled_actions_expanded=false real_desktop_touched=false low_level_event_count=0`

Acceptance boundary:
- Unit tests and controller automation are not enough by themselves.
- The controller must launch `learning_agent/start_oauth_agent.bat` in a real visible local terminal window.
- Completion can only be claimed if the controller result JSON says the scenario completed and all assertions passed.

Final visible terminal result:
- Controller completed: true.
- Verifier completed: true.
- Result JSON: `learning_agent/acceptance_controller/runs/computer_use_full_maturity_final-20260605_162905/result.json`.
- Run directory: `learning_agent/acceptance_controller/runs/computer_use_full_maturity_final-20260605_162905`.
- Final assertion: all maturity tokens present, permission_sent_count=0, startup/prompt/final screenshots present.
