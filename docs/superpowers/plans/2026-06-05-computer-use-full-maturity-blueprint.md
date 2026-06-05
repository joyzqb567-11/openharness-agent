# Computer Use Full Maturity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Learning Agent 的 `/computer use --full` 从“安全框架可用”推进到“可宣布成熟”的有限交付目标，避免无限 Phase。

**Architecture:** 继续沿用 Phase92/93 的单一通用 Computer Use runtime，不再为每个本机应用写专用 controller。成熟版本必须通过一个统一的 observe -> plan -> act -> verify -> recover 闭环，并且对任意普通应用走同一套发现、启动、身份绑定、操作、清理、审计和验收模型。

**Tech Stack:** Python `unittest`，Windows Computer Use 模块，`learning_agent/app/interactive.py` 终端入口，`learning_agent/acceptance_controller` 真实可见终端验收，Windows UIA/WGC/SendInput/进程窗口探针现有能力。

---

## 一句话结论

`/computer use --full` 成熟的定义不是“声称可以打开任何应用”，而是：

1. 普通应用不需要逐应用白名单或逐应用补丁。
2. 真实动作默认仍要经过用户强确认、风险分类、目标身份绑定和急停门禁。
3. 对普通应用的启动、观察、点击、输入、保存、关闭和清理走统一通用链路。
4. 高风险目标、凭据窗口、终端、系统设置、管理员工具默认拒绝，且拒绝路径零副作用。
5. 最终矩阵通过后停止新增 Phase，只保留 bugfix、兼容性修复和新代表性样本。

## 当前基线

已经完成并可复用：

- Phase92：单一通用 Computer Use mode，代表性 app 只作为验收样本。
- Phase93：统一 live execution gate，默认真实动作关闭。
- Phase103：受控 app launch candidate 和可注入后端。
- Phase104：受控 Notepad 真实启动、可见窗口验证、清理、残留检查。
- Phase105：`/computer use --full` 到受控 Notepad 真实启动 smoke。
- Phase106：真实用户命令 `/computer launch notepad` 接入 full 模式。
- Phase107：交互目标解析和高风险拒绝。
- Phase108：通用应用发现，不需要每 app 白名单。
- Phase109：通用真实启动候选、记录型进程身份、窗口身份、清理和残留模型。

仍未成熟：

- 通用普通应用真实启动后端还没有产品化默认接入。
- 任意普通应用启动后的真实窗口身份绑定还没有作为统一 production path。
- 通用点击、输入、保存、关闭还没有在 `/computer use --full` 的真实 app 端到端矩阵中完成。
- 真实失败恢复、残留清理、审计回放和用户可见状态还没有形成最终成熟门禁。

## 成熟定义

只有同时满足下面 8 个成熟门禁，才能说 `/computer use --full` 成熟。

### M0: 产品语义成熟

- `/computer use --full` 表示“用户强确认后的通用受控桌面模式”。
- 它不是无限权限。
- 它不是跳过所有安全策略。
- 它不是每个 app 白名单。
- 它必须显示当前模式、剩余 TTL、允许动作类别、急停状态和最后一次真实动作摘要。

通过标准：

- `/computer use --full`
- `/computer use --full-confirm <token>`
- `/computer status`
- `/computer stop`

都在真实可见终端里可用，并且状态一致。

### M1: 普通应用通用发现成熟

- 从 Start Menu、PATH、App Paths、Windows Apps、已安装应用索引中只读发现普通应用。
- 发现结果生成统一 `LaunchTargetIdentity`，不是专用 app 分支。
- 高风险目标在发现后仍拒绝。

必须输出：

`hardcoded_app_whitelist_required=false`

`per_app_patch_required=false`

### M2: 通用真实启动成熟

- `/computer launch <ordinary_app>` 对普通应用走统一后端。
- 默认仍安全关闭，真实启动必须满足 full confirmed、风险普通、目标可发现、显式真实动作 gate。
- 真实启动后必须拿到 owned process identity。
- 启动失败必须给出可读原因，不允许沉默失败。

必须输出：

`generic_real_launch_default_enabled=false`

`generic_real_launch_enabled_when_authorized=true`

### M3: 窗口身份绑定成熟

- 真实启动后必须绑定 pid、hwnd、进程名、窗口标题摘要、进程路径哈希。
- 后续动作必须只允许落在 verified owned window 上。
- 目标漂移必须阻断动作。
- 多窗口 app 必须选择正确 owned window 或要求用户确认。

必须输出：

`process_identity_verified=true`

`window_identity_verified=true`

`target_drift_blocks_action=true`

### M4: 通用操作闭环成熟

至少支持普通应用上的统一动作：

- observe screen
- list windows
- focus verified window
- click
- type text
- hotkey safe
- scroll
- temporary clipboard text
- save current document
- close owned window

每个动作都必须经过：

- before snapshot
- target identity check
- action dispatch
- after snapshot
- verification
- recovery decision

必须输出：

`generic_observe_plan_act_verify_loop=true`

`actions_require_verified_window=true`

### M5: 清理和恢复成熟

- 每次真实启动必须注册 owned process/window cleanup。
- stop/abort 必须清理本次 agent 拥有的窗口和进程。
- 不能关闭用户原本打开的同名应用窗口。
- 失败后必须残留检查。

必须输出：

`cleanup_completed=true`

`residual_owned_process=false`

`user_preexisting_windows_preserved=true`

### M6: 安全成熟

默认拒绝：

- PowerShell、CMD、Windows Terminal、registry、settings、services、task manager。
- Windows Security、credential、password、OTP、captcha、bank/payment/admin 类窗口。
- 未授权窗口。
- 目标漂移窗口。
- 用户取消或 stop 后的动作。

必须输出：

`high_risk_refused=true`

`credential_window_zero_events=true`

`abort_before_low_level_send=true`

`uncontrolled_actions_expanded=false`

### M7: 真实可见终端成熟验收

最终成熟不是靠单元测试宣布，必须通过真实可见终端：

- 启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`
- 在可见终端输入真实用户风格 prompt。
- 观察 agent 输出。
- 保存截图、events、debug log、result JSON。
- 最终回答包含固定成熟 token。

最终 token：

`COMPUTER_USE_FULL_MATURE_READY COMPUTER_USE_FULL_MATURE_OK generic_discovery=true generic_real_launch=true verified_window_actions=true cleanup_recovery=true high_risk_refused=true visible_terminal_acceptance=true hardcoded_app_whitelist_required=false per_app_patch_required=false uncontrolled_actions_expanded=false`

## 最终停止条件

当 M0-M7 全部通过，并且最终真实可见终端 scenario 通过后：

- 停止新增“成熟能力 Phase”。
- 后续只允许三类工作：
  - bugfix：修复已定义能力的失败。
  - compatibility：为 Windows 版本、应用窗口行为差异增加兼容。
  - representative sample：增加新 app 样本验证同一通用链路，不允许新增专用 app controller。

如果某个新需求要求绕过上面的安全边界，必须新开设计评审，不允许直接并入 `/computer use --full` 成熟范围。

## File Structure

### New Files

- `learning_agent/computer_use/generic_launch_backend.py`
  - 负责普通应用通用真实启动后端。
- `learning_agent/computer_use/target_identity.py`
  - 负责进程身份、窗口身份、路径哈希、目标漂移检测。
- `learning_agent/computer_use/owned_resource_registry.py`
  - 负责记录本次 agent 拥有的进程、窗口、临时文件和 cleanup handle。
- `learning_agent/computer_use/full_maturity_matrix.py`
  - 负责汇总 M0-M7 成熟门禁。
- `learning_agent/tests/test_windows_computer_use_generic_launch_backend_maturity.py`
  - 测通用真实启动后端。
- `learning_agent/tests/test_windows_computer_use_target_identity_maturity.py`
  - 测窗口身份和漂移阻断。
- `learning_agent/tests/test_windows_computer_use_cleanup_recovery_maturity.py`
  - 测清理、残留、保留用户原窗口。
- `learning_agent/tests/test_windows_computer_use_full_maturity_matrix.py`
  - 测最终成熟矩阵。
- `learning_agent/acceptance_controller/scenarios/computer_use_full_maturity_final.json`
  - 最终真实可见终端验收。

### Modified Files

- `learning_agent/app/interactive.py`
  - `/computer launch <app>` 接入通用真实启动后端。
  - `/computer status` 显示 full 成熟状态。
- `learning_agent/computer_use/generic_real_launch_candidate.py`
  - Phase109 recording-only 候选升级为 production candidate 输入模型。
- `learning_agent/computer_use/universal_live_execution.py`
  - 将通用后端接入 live execution gate。
- `learning_agent/computer_use/security_policy.py`
  - 增加成熟级高风险拒绝字段。
- `learning_agent/computer_use/session_runtime.py`
  - 接入 owned resource cleanup 和 abort 处理。

---

## Task 1: Freeze Product Contract

**Files:**
- Create: `agent_memory/computer_use_full_maturity_contract_20260605.md`
- Create: `learning_agent/tests/test_windows_computer_use_full_maturity_contract.py`

- [ ] **Step 1: Write the failing test**

Create `learning_agent/tests/test_windows_computer_use_full_maturity_contract.py` with assertions for:

- final maturity token name
- no per-app controller
- full mode is not unlimited permission
- high risk refusal remains mandatory
- final visible terminal acceptance is mandatory

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_full_maturity_contract`

Expected:

`ModuleNotFoundError` or missing contract constants.

- [ ] **Step 2: Write the contract module**

Create `learning_agent/computer_use/full_maturity_contract.py` with constants:

- `COMPUTER_USE_FULL_MATURE_MARKER`
- `COMPUTER_USE_FULL_MATURE_OK_TOKEN`
- `COMPUTER_USE_FULL_MATURITY_GATES`
- `COMPUTER_USE_FULL_OUT_OF_SCOPE`

- [ ] **Step 3: Run focused tests**

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_full_maturity_contract`

Expected:

All tests pass.

- [ ] **Step 4: Commit**

Run:

`git add learning_agent/computer_use/full_maturity_contract.py learning_agent/tests/test_windows_computer_use_full_maturity_contract.py agent_memory/computer_use_full_maturity_contract_20260605.md`

`git commit -m "docs: freeze computer use full maturity contract"`

## Task 2: Build Generic Launch Backend

**Files:**
- Create: `learning_agent/computer_use/generic_launch_backend.py`
- Test: `learning_agent/tests/test_windows_computer_use_generic_launch_backend_maturity.py`
- Modify: `learning_agent/computer_use/generic_real_launch_candidate.py`

- [ ] **Step 1: Write failing tests**

Test cases:

- default path does not launch
- authorized path calls backend with argv, not shell string
- unsafe plan refuses before backend call
- launched process is registered as owned
- launch failure returns structured reason

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_generic_launch_backend_maturity`

Expected:

Fails because `generic_launch_backend.py` does not exist.

- [ ] **Step 2: Implement recording backend first**

Create:

- `Phase110RecordingGenericLaunchBackend`
- `GenericLaunchRequest`
- `GenericLaunchResult`

Keep real desktop untouched.

- [ ] **Step 3: Implement production backend behind explicit gate**

Use existing safe plan fields:

- no shell string
- no admin
- no registry changes
- no system settings changes
- no high-risk target

The real backend must return:

- `process_started`
- `process_id`
- `process_executable`
- `real_desktop_touched`
- `cleanup_registered`

- [ ] **Step 4: Run focused tests**

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_generic_launch_backend_maturity`

Expected:

All tests pass.

- [ ] **Step 5: Commit**

Run:

`git add learning_agent/computer_use/generic_launch_backend.py learning_agent/computer_use/generic_real_launch_candidate.py learning_agent/tests/test_windows_computer_use_generic_launch_backend_maturity.py`

`git commit -m "feat: add generic launch backend"`

## Task 3: Build Target Identity Binding

**Files:**
- Create: `learning_agent/computer_use/target_identity.py`
- Test: `learning_agent/tests/test_windows_computer_use_target_identity_maturity.py`
- Modify: `learning_agent/computer_use/windows_backend.py`

- [ ] **Step 1: Write failing tests**

Test cases:

- binds pid to hwnd
- process path is hashed, not exposed raw
- window title is summarized
- target drift blocks action
- same title from different pid is not accepted
- user preexisting same-app window is not accepted as owned target

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_target_identity_maturity`

Expected:

Fails because `target_identity.py` does not exist.

- [ ] **Step 2: Implement identity records**

Create structured records:

- `ProcessIdentity`
- `WindowIdentity`
- `OwnedTargetIdentity`
- `TargetIdentityVerification`

- [ ] **Step 3: Wire into launch candidate**

`generic_real_launch_candidate.py` must emit:

- `process_identity_verified`
- `window_identity_verified`
- `target_identity_verified`
- `target_drift_blocks_action`

- [ ] **Step 4: Run focused tests**

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_target_identity_maturity`

Expected:

All tests pass.

- [ ] **Step 5: Commit**

Run:

`git add learning_agent/computer_use/target_identity.py learning_agent/computer_use/windows_backend.py learning_agent/computer_use/generic_real_launch_candidate.py learning_agent/tests/test_windows_computer_use_target_identity_maturity.py`

`git commit -m "feat: bind launched process to verified window"`

## Task 4: Add Owned Resource Registry

**Files:**
- Create: `learning_agent/computer_use/owned_resource_registry.py`
- Test: `learning_agent/tests/test_windows_computer_use_cleanup_recovery_maturity.py`
- Modify: `learning_agent/computer_use/session_runtime.py`

- [ ] **Step 1: Write failing tests**

Test cases:

- register owned process
- register owned window
- cleanup only owned resources
- preserve preexisting user windows
- abort cleans owned resources
- residual check fails if owned process remains

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_cleanup_recovery_maturity`

Expected:

Fails because `owned_resource_registry.py` does not exist.

- [ ] **Step 2: Implement registry**

Registry fields:

- `session_id`
- `process_id`
- `window_id`
- `created_at`
- `cleanup_state`
- `residual_check_state`

- [ ] **Step 3: Wire into stop and abort**

Modify `session_runtime.py` so `/computer stop` and abort hooks call cleanup for owned resources.

- [ ] **Step 4: Run focused tests**

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_cleanup_recovery_maturity`

Expected:

All tests pass.

- [ ] **Step 5: Commit**

Run:

`git add learning_agent/computer_use/owned_resource_registry.py learning_agent/computer_use/session_runtime.py learning_agent/tests/test_windows_computer_use_cleanup_recovery_maturity.py`

`git commit -m "feat: track and cleanup owned computer use resources"`

## Task 5: Wire Generic Launch Into `/computer launch <app>`

**Files:**
- Modify: `learning_agent/app/interactive.py`
- Modify: `learning_agent/computer_use/universal_live_execution.py`
- Test: `learning_agent/tests/test_windows_computer_use_interactive_generic_launch_maturity.py`

- [ ] **Step 1: Write failing tests**

Test cases:

- `/computer launch obsidian` in full mode reaches generic launch backend in default-off mode
- explicit real launch gate reaches production backend
- `/computer launch powershell` still refuses
- `/computer stop` clears owned resources

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_interactive_generic_launch_maturity`

Expected:

Fails because the interactive path still only prints Phase109 default-off evidence.

- [ ] **Step 2: Wire default-off production candidate**

Keep default path:

`real_full_launch_attempted=false`

Expose:

`generic_real_launch_candidate_ready=true`

- [ ] **Step 3: Wire explicit real gate**

Use a clearly named env gate for automated smoke only:

`LEARNING_AGENT_ENABLE_GENERIC_REAL_LAUNCH_SMOKE=1`

Without this env gate, tests must prove no real desktop touch.

- [ ] **Step 4: Run focused tests**

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_interactive_generic_launch_maturity`

Expected:

All tests pass.

- [ ] **Step 5: Commit**

Run:

`git add learning_agent/app/interactive.py learning_agent/computer_use/universal_live_execution.py learning_agent/tests/test_windows_computer_use_interactive_generic_launch_maturity.py`

`git commit -m "feat: route computer launch through generic backend"`

## Task 6: Mature Generic Action Loop

**Files:**
- Modify: `learning_agent/computer_use/closed_loop_executor.py`
- Modify: `learning_agent/computer_use/generic_control_actions.py`
- Modify: `learning_agent/computer_use/generic_input_actions.py`
- Test: `learning_agent/tests/test_windows_computer_use_verified_window_actions_maturity.py`

- [ ] **Step 1: Write failing tests**

Test cases:

- click requires verified owned window
- type text requires verified owned window
- safe hotkey requires verified owned window
- target drift blocks low-level dispatch
- abort before dispatch produces zero low-level events

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_verified_window_actions_maturity`

Expected:

Fails until action layers read `OwnedTargetIdentity`.

- [ ] **Step 2: Thread identity through actions**

Every action must receive:

- `session_id`
- `window_identity`
- `target_identity_verification`

- [ ] **Step 3: Enforce before and after verification**

Each action must produce:

- `before_identity`
- `after_identity`
- `same_target`
- `blocked`
- `low_level_event_count`

- [ ] **Step 4: Run focused tests**

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_verified_window_actions_maturity`

Expected:

All tests pass.

- [ ] **Step 5: Commit**

Run:

`git add learning_agent/computer_use/closed_loop_executor.py learning_agent/computer_use/generic_control_actions.py learning_agent/computer_use/generic_input_actions.py learning_agent/tests/test_windows_computer_use_verified_window_actions_maturity.py`

`git commit -m "feat: require verified target identity for desktop actions"`

## Task 7: Build Final Maturity Matrix

**Files:**
- Create: `learning_agent/computer_use/full_maturity_matrix.py`
- Test: `learning_agent/tests/test_windows_computer_use_full_maturity_matrix.py`
- Modify: `learning_agent/app/interactive.py`

- [ ] **Step 1: Write failing tests**

Test matrix fields:

- `product_contract=true`
- `generic_discovery=true`
- `generic_real_launch=true`
- `verified_window_actions=true`
- `cleanup_recovery=true`
- `high_risk_refused=true`
- `visible_terminal_acceptance=true`
- `hardcoded_app_whitelist_required=false`
- `per_app_patch_required=false`
- `uncontrolled_actions_expanded=false`

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_full_maturity_matrix`

Expected:

Fails because `full_maturity_matrix.py` does not exist.

- [ ] **Step 2: Implement matrix**

Create:

- `run_computer_use_full_maturity_matrix()`
- `computer_use_full_maturity_cli_line()`
- `computer_use_full_maturity_main()`

- [ ] **Step 3: Expose status command**

Add:

`/computer maturity`

It must print the final matrix without touching real desktop.

- [ ] **Step 4: Run focused tests**

Run:

`python -m unittest learning_agent.tests.test_windows_computer_use_full_maturity_matrix`

Expected:

All tests pass.

- [ ] **Step 5: Commit**

Run:

`git add learning_agent/computer_use/full_maturity_matrix.py learning_agent/app/interactive.py learning_agent/tests/test_windows_computer_use_full_maturity_matrix.py`

`git commit -m "feat: add computer use full maturity matrix"`

## Task 8: Final Visible Terminal Acceptance

**Files:**
- Create: `learning_agent/acceptance_controller/scenarios/computer_use_full_maturity_final.json`
- Create: `agent_memory/computer_use_full_maturity_final_20260605.md`
- Create backup directory: `learning_agent/test/computer_use_full_maturity_final_20260605/`

- [ ] **Step 1: Create scenario**

The scenario must require:

- launch visible `start_oauth_agent.bat`
- request `/computer use --full`
- confirm token
- run `/computer maturity`
- run one ordinary app default-off command
- run one high-risk refusal command
- run `/computer stop`
- final answer copies final token

- [ ] **Step 2: Run controller**

Run:

`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\computer_use_full_maturity_final.json"`

Expected:

`ACCEPTANCE_CONTROLLER_COMPLETED=True`

- [ ] **Step 3: Verify result JSON**

Open:

`learning_agent/acceptance_controller/runs/<computer_use_full_maturity_final-run>/result.json`

Required fields:

- `completed=true`
- `prompt_sent=true`
- `prompt_received=true`
- `final_printed=true`
- `assertion.passed=true`
- `permission_sent_count=0`

- [ ] **Step 4: Back up artifacts**

Copy into:

`learning_agent/test/computer_use_full_maturity_final_20260605/`

Required artifacts:

- final scenario JSON
- result JSON
- latest readable log
- screenshots
- final matrix report
- memory file

- [ ] **Step 5: Commit**

Run:

`git add learning_agent/acceptance_controller/scenarios/computer_use_full_maturity_final.json agent_memory/computer_use_full_maturity_final_20260605.md learning_agent/test/computer_use_full_maturity_final_20260605`

`git commit -m "test: add final computer use full maturity acceptance"`

## Final Verification Command Set

Run all commands before declaring maturity:

`python -m py_compile .\learning_agent\app\interactive.py .\learning_agent\computer_use\generic_real_launch_candidate.py .\learning_agent\computer_use\generic_launch_backend.py .\learning_agent\computer_use\target_identity.py .\learning_agent\computer_use\owned_resource_registry.py .\learning_agent\computer_use\full_maturity_matrix.py`

`python -m unittest learning_agent.tests.test_windows_computer_use_full_maturity_contract learning_agent.tests.test_windows_computer_use_generic_launch_backend_maturity learning_agent.tests.test_windows_computer_use_target_identity_maturity learning_agent.tests.test_windows_computer_use_cleanup_recovery_maturity learning_agent.tests.test_windows_computer_use_interactive_generic_launch_maturity learning_agent.tests.test_windows_computer_use_verified_window_actions_maturity learning_agent.tests.test_windows_computer_use_full_maturity_matrix`

`python -m unittest discover -s learning_agent\tests -p "test_windows_computer_use*.py"`

`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\computer_use_full_maturity_final.json"`

## Final Completion Rule

Only say `/computer use --full` is mature when the final visible terminal result JSON has:

- `completed=true`
- `assertion.passed=true`
- final answer contains `COMPUTER_USE_FULL_MATURE_OK`
- `hardcoded_app_whitelist_required=false`
- `per_app_patch_required=false`
- `uncontrolled_actions_expanded=false`

If any of those fail, the correct status is:

`/computer use --full` is usable but not mature.
