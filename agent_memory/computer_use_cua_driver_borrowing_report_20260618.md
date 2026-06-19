# Cua Driver Windows Computer Use Borrowing Matrix

- marker=CUA_DRIVER_WINDOWS_BORROWING_READY
- passed=true
- visible_terminal_gate=false

## Checks
- claudecode_tool_surface_unchanged=true
- cua_inspired_element_cache_present=true
- uia_semantic_dispatch_present=true
- coordinate_contract_present=true
- uipi_diagnostics_present=true
- mcp_observe_act_verify_present=true
- hidden_claudecode_package_internals_excluded=true

## Boundary
- ClaudeCode hidden external package internals remain excluded from line-by-line verification.
- Windows implementation differences are accepted when they are platform-equivalent.
