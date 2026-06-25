# Desktop GUI Shell V2 Task 8 - Sessions And Search

- Scope: add V2 session list, rename, archive, and search backend contracts, then wire the Electron sidebar and search panel to those contracts.
- Backend files copied here: `gui_bridge.py`, `test_gui_sessions_search_contract.py`.
- Frontend files copied here: `guiClient.ts`, `guiClient.test.ts`, `AppShell.tsx`, `Sidebar.tsx`, `SearchPanel.tsx`, `layout.css`.
- Verified: `python -m unittest learning_agent.tests.test_gui_sessions_search_contract`.
- Verified: `cd apps/desktop && npm test -- --run`.
- Verified: `cd apps/desktop && npm run lint`.
- GUI note: this task adds visible sidebar/search behavior; final V2 visible Electron acceptance still runs at the release gate after Task 10, Task 13, and Task 14.
