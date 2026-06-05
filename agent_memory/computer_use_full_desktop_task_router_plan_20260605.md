# Computer Use Full Desktop Task Router Implementation Plan Summary

Date: 2026-06-05

Status: implementation plan written.

Plan file:
- `docs/superpowers/plans/2026-06-05-computer-use-full-desktop-task-router.md`

Root-cause scope:
- Route ordinary natural-language desktop prompts into Computer Use before the normal model tool loop.
- Block script-generated final artifacts for desktop GUI tasks.
- Use Paint Pikachu only as strict representative visible-terminal acceptance, not as a Paint-specific controller.

Implementation tasks:
- Task 1: Freeze previous script bypass as a negative regression.
- Task 2: Add Desktop Task Intent Router.
- Task 3: Add Desktop Task Tool Policy.
- Task 4: Build Desktop Task Runtime.
- Task 5: Route ordinary prompts before the normal tool loop.
- Task 6: Add generic drawing primitive evidence.
- Task 7: Add strict visible-terminal Paint Pikachu acceptance.
- Task 8: Update final maturity matrix.

Completion rule:
- The feature cannot be called mature until the strict visible terminal scenario proves GUI route usage, forbidden script route blocking, owned Paint window identity, GUI action count, low-level event count, canvas change evidence, post-action screenshot evidence, and `/computer stop`.
