# Universal Windows Computer Use Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one generic Windows Computer Use mode so a prompt can enter a universal observe -> plan -> act -> verify -> recover loop, instead of requiring one controller per app.

**Architecture:** Add `UniversalWindowsComputerUseRuntime` as the single orchestration layer above existing Phase66-72 and Phase76-89 modules. Representative apps remain acceptance samples only; the runtime must expose generic capability tokens and keep real actions disabled by default.

**Tech Stack:** Python, unittest, existing `learning_agent.computer_use` modules, existing tool surface, PowerShell acceptance controller, `start_oauth_agent.bat` visible terminal acceptance.

---

## File Structure

- Create `learning_agent/computer_use/universal_mode.py`
  - Owns Phase92 constants, runtime class, contract runner, CLI line, and `main()`.
  - Composes existing observation, planner, action, safety, and production adapter modules.
  - Does not contain app-specific Notepad/Paint control logic.
- Create `learning_agent/tests/test_windows_computer_use_universal_mode_phase92.py`
  - Proves Phase92 contract, no per-app controllers, representative samples are acceptance-only, and real actions are off by default.
- Modify `learning_agent/computer_use/__init__.py`
  - Exports Phase92 runtime and contract APIs.
- Modify `learning_agent/computer_use/tool_surface.py`
  - Adds a compatibility route for `operation="mode"` or `operation="run_prompt"` without bypassing existing controller/safety semantics.
- Modify `learning_agent/core/agent.py`
  - Routes the compatible Computer Use mode request to Phase92 runtime while keeping explicit permission gates for action-like operations.
- Create `learning_agent/acceptance_controller/scenarios/agent_capability_phase92_universal_windows_computer_use_mode.json`
  - Real visible terminal scenario in safe contract mode.
- Modify memory/docs:
  - `agent_memory/context.md`
  - `agent_memory/progress.md`
  - `agent_memory/bugs.md`
  - `task_plan.md`
  - `progress.md`
  - `findings.md`
  - `learning_agent/test/agent_capability_phase92_universal_windows_computer_use_mode_20260604/`

---

### Task 1: Red Test For Universal Runtime

**Files:**
- Create: `learning_agent/tests/test_windows_computer_use_universal_mode_phase92.py`

- [ ] **Step 1: Write failing import and contract tests**

Use this test shape:

```python
import json  # 新增代码+Phase92UniversalComputerUse：导入 JSON 用来检查报告是否泄露原始 prompt；如果没有这行代码，raw_text_hidden 无法验证。
import tempfile  # 新增代码+Phase92UniversalComputerUse：导入临时目录隔离测试状态；如果没有这行代码，测试可能污染真实 memory。
import unittest  # 新增代码+Phase92UniversalComputerUse：导入 unittest 以符合现有测试风格；如果没有这行代码，标准测试命令无法发现本文件。
from pathlib import Path  # 新增代码+Phase92UniversalComputerUse：导入 Path 管理临时路径；如果没有这行代码，Windows 路径拼接容易出错。

from learning_agent.computer_use.universal_mode import (  # 新增代码+Phase92UniversalComputerUse：导入 Phase92 入口；如果没有这行代码，测试无法证明通用 runtime 存在。
    PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MARKER,
    PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK_TOKEN,
    PHASE92_UNCONTROLLED_ACTIONS_EXPANDED,
    UniversalWindowsComputerUseRuntime,
    phase92_cli_line,
    run_phase92_universal_windows_computer_use_contract,
)


class WindowsComputerUseUniversalModePhase92Tests(unittest.TestCase):  # 新增代码+Phase92UniversalComputerUse：类段开始，集中验证通用 Computer Use 模式；如果没有这个类，Phase92 架构纠偏没有自动化门禁。
    def test_phase92_contract_rejects_per_app_controller_architecture(self) -> None:  # 新增代码+Phase92UniversalComputerUse：函数段开始，验证不是每个软件一个控制器；如果没有这段测试，后续可能继续堆 app-specific 控制器。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase92UniversalComputerUse：使用临时目录隔离报告；如果没有这行代码，测试会污染真实运行目录。
            report = run_phase92_universal_windows_computer_use_contract(base_dir=Path(temp_dir))  # 新增代码+Phase92UniversalComputerUse：运行 Phase92 合同；如果没有这行代码，测试没有事实来源。
        self.assertTrue(report["passed"])  # 新增代码+Phase92UniversalComputerUse：断言合同通过；如果没有这行代码，失败字段可能被忽略。
        self.assertTrue(report["single_universal_runtime"])  # 新增代码+Phase92UniversalComputerUse：断言只有一个通用 runtime；如果没有这行代码，架构会退化成 app 控制器集合。
        self.assertFalse(report["per_app_controller_required"])  # 新增代码+Phase92UniversalComputerUse：断言不需要每 app 控制器；如果没有这行代码，用户纠偏点没有被锁住。
        self.assertTrue(report["representative_apps_are_acceptance_only"])  # 新增代码+Phase92UniversalComputerUse：断言代表应用只是验收样本；如果没有这行代码，Notepad/Paint 会被误当成主架构。
        self.assertTrue(report["prompt_to_any_normal_app"])  # 新增代码+Phase92UniversalComputerUse：断言目标是 prompt 到任意普通应用；如果没有这行代码，通用目标不清楚。
        self.assertFalse(report["default_real_actions_enabled"])  # 新增代码+Phase92UniversalComputerUse：断言默认不执行真实动作；如果没有这行代码，单测可能误控用户桌面。
        self.assertFalse(report["uncontrolled_actions_expanded"])  # 新增代码+Phase92UniversalComputerUse：断言不扩张无保护动作；如果没有这行代码，安全边界可能被绕过。
        self.assertFalse(PHASE92_UNCONTROLLED_ACTIONS_EXPANDED)  # 新增代码+Phase92UniversalComputerUse：断言模块常量也保持安全；如果没有这行代码，报告和代码可能不一致。

    def test_phase92_runtime_builds_generic_prompt_session(self) -> None:  # 新增代码+Phase92UniversalComputerUse：函数段开始，验证 prompt 会进入通用 session；如果没有这段测试，runtime 可能只是静态矩阵。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase92UniversalComputerUse：隔离 runtime 状态；如果没有这行代码，不同测试会共享报告。
            runtime = UniversalWindowsComputerUseRuntime(base_dir=Path(temp_dir))  # 新增代码+Phase92UniversalComputerUse：创建通用 runtime；如果没有这行代码，无法验证组件行为。
            result = runtime.run_prompt("打开 computer use，帮我操作一个普通 Windows 应用", real_actions=False)  # 新增代码+Phase92UniversalComputerUse：用自然 prompt 进入通用模式；如果没有这行代码，prompt 入口没有测试。
        self.assertTrue(result["ok"])  # 新增代码+Phase92UniversalComputerUse：断言通用 session 创建成功；如果没有这行代码，失败也可能被忽略。
        self.assertTrue(result["generic_observe_plan_act_verify_loop"])  # 新增代码+Phase92UniversalComputerUse：断言走通用闭环；如果没有这行代码，runtime 可能还是 app 特例。
        self.assertEqual(result["mode"], "universal_windows_computer_use")  # 新增代码+Phase92UniversalComputerUse：断言模式名稳定；如果没有这行代码，上层 agent 难以识别模式。
        self.assertFalse(result["real_actions_requested"])  # 新增代码+Phase92UniversalComputerUse：断言默认没有请求真实动作；如果没有这行代码，测试可能误触桌面。
        self.assertTrue(result["raw_text_hidden"])  # 新增代码+Phase92UniversalComputerUse：断言报告隐藏 prompt 原文；如果没有这行代码，用户 prompt 可能进日志。

    def test_phase92_cli_and_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase92UniversalComputerUse：函数段开始，验证终端 token 和场景同步；如果没有这段测试，真实终端验收可能漂移。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase92UniversalComputerUse：隔离合同报告；如果没有这行代码，CLI 行可能引用真实目录。
            report = run_phase92_universal_windows_computer_use_contract(base_dir=Path(temp_dir))  # 新增代码+Phase92UniversalComputerUse：运行合同获得报告；如果没有这行代码，CLI 行没有事实来源。
        line = phase92_cli_line(report)  # 新增代码+Phase92UniversalComputerUse：生成固定 token 行；如果没有这行代码，场景无法稳定匹配。
        scenario_text = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase92_universal_windows_computer_use_mode.json").read_text(encoding="utf-8")  # 新增代码+Phase92UniversalComputerUse：读取可见终端场景；如果没有这行代码，场景缺 token 不会在单测暴露。
        json.loads(scenario_text)  # 新增代码+Phase92UniversalComputerUse：校验场景 JSON 合法；如果没有这行代码，controller 运行时才发现格式错误。
        expected_tokens = {
            PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MARKER,
            PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK_TOKEN,
            "single_universal_runtime=true",
            "prompt_to_any_normal_app=true",
            "per_app_controller_required=false",
            "representative_apps_are_acceptance_only=true",
            "generic_observe_plan_act_verify_loop=true",
            "uses_observation_fusion=true",
            "uses_prompt_task_planner=true",
            "uses_generic_action_layer=true",
            "uses_real_app_safety_boundary=true",
            "uses_production_host_adapter=true",
            "high_risk_requires_confirmation=true",
            "unauthorized_window_zero_events=true",
            "target_drift_blocks_action=true",
            "raw_text_hidden=true",
            "default_real_actions_enabled=false",
            "uncontrolled_actions_expanded=false",
        }  # 新增代码+Phase92UniversalComputerUse：列出验收必须稳定出现的 token；如果没有这行代码，验收标准会漂移。
        for token in expected_tokens:  # 新增代码+Phase92UniversalComputerUse：逐项检查 token；如果没有这行代码，某个关键字段可能漏检。
            self.assertIn(token, line)  # 新增代码+Phase92UniversalComputerUse：断言 CLI 行包含 token；如果没有这行代码，终端输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase92UniversalComputerUse：断言场景也包含 token；如果没有这行代码，自动测试和真实终端验收会不一致。


if __name__ == "__main__":  # 新增代码+Phase92UniversalComputerUse：允许直接运行测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase92UniversalComputerUse：调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
```

- [ ] **Step 2: Run test to verify red**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_universal_mode_phase92
```

Expected:

```text
ModuleNotFoundError: No module named 'learning_agent.computer_use.universal_mode'
```

---

### Task 2: Implement Universal Runtime Contract

**Files:**
- Create: `learning_agent/computer_use/universal_mode.py`
- Modify: `learning_agent/computer_use/__init__.py`

- [ ] **Step 1: Create constants and runtime shell**

The module must define:

```python
PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MARKER = "PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_READY"  # 新增代码+Phase92UniversalComputerUse：定义真实终端 ready 标记；如果没有这行代码，controller 无法稳定识别 Phase92。
PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK_TOKEN = "PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK"  # 新增代码+Phase92UniversalComputerUse：定义成功 token；如果没有这行代码，用户无法一眼确认 Phase92 通过。
PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MODEL = "phase92_universal_windows_computer_use_mode"  # 新增代码+Phase92UniversalComputerUse：定义协议模型名；如果没有这行代码，报告无法说明版本。
PHASE92_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase92UniversalComputerUse：声明不扩张无保护动作；如果没有这行代码，通用模式可能被误解为裸控。
PHASE92_DEFAULT_REAL_ACTIONS_ENABLED = False  # 新增代码+Phase92UniversalComputerUse：声明默认不执行真实桌面动作；如果没有这行代码，测试和验收可能误控用户电脑。
```

- [ ] **Step 2: Compose existing modules**

`UniversalWindowsComputerUseRuntime.__init__` must instantiate or accept:

```python
WindowsObservationFusionRuntime  # 新增代码+Phase92UniversalComputerUse：用于统一观察事实；如果没有它，runtime 会回到分散截图/UIA。
WindowsPromptTaskPlanner  # 新增代码+Phase92UniversalComputerUse：用于把 prompt 转成步骤；如果没有它，runtime 不能处理自然语言目标。
WindowsGenericControlActionRuntime  # 新增代码+Phase92UniversalComputerUse：用于通用控件点击/输入；如果没有它，会退回 app 专用动作。
WindowsGenericInputActionRuntime  # 新增代码+Phase92UniversalComputerUse：用于热键/菜单/滚动/拖拽；如果没有它，普通应用常见操作不完整。
WindowsRealAppSafetyBoundary  # 新增代码+Phase92UniversalComputerUse：用于授权、风险和急停门禁；如果没有它，通用模式会危险。
WindowsProductionComputerUseHostAdapter  # 新增代码+Phase92UniversalComputerUse：用于生产 host adapter 汇总；如果没有它，Phase76-89 产物无法进入新总入口。
```

- [ ] **Step 3: Implement `run_prompt`**

`run_prompt(prompt, real_actions=False)` must return a generic session report:

```python
{
    "ok": True,
    "mode": "universal_windows_computer_use",
    "prompt_sha256_16": "...",
    "prompt_text_included": False,
    "single_universal_runtime": True,
    "per_app_controller_required": False,
    "representative_apps_are_acceptance_only": True,
    "generic_observe_plan_act_verify_loop": True,
    "real_actions_requested": False,
    "default_real_actions_enabled": False,
    "raw_text_hidden": True,
}
```

It must not call `notepad_live_smoke.py` or any app-specific smoke module.

- [ ] **Step 4: Implement `run_phase92_universal_windows_computer_use_contract`**

The contract must verify:

- One runtime exists.
- The runtime composes Phase66, Phase67, Phase70/71, Phase72, and Phase76-89 host adapter.
- Prompt mode works for a generic normal-app prompt.
- Representative apps are acceptance samples only.
- High-risk prompt requires confirmation.
- Unauthorized window and target drift produce zero-event refusal in contract evidence.
- Real actions are disabled by default.
- Raw prompt text is not visible in the serialized report.

- [ ] **Step 5: Export APIs**

Add to `learning_agent/computer_use/__init__.py`:

```python
from learning_agent.computer_use.universal_mode import PHASE92_UNCONTROLLED_ACTIONS_EXPANDED, PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MARKER, PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MODEL, PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK_TOKEN, UniversalWindowsComputerUseRuntime, phase92_cli_line, run_phase92_universal_windows_computer_use_contract  # 新增代码+Phase92UniversalComputerUse：公开 Phase92 通用 Computer Use 模式入口；如果没有这行代码，其它 agent 只能硬编码内部模块路径。
__all__.extend(["PHASE92_UNCONTROLLED_ACTIONS_EXPANDED", "PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MARKER", "PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MODEL", "PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK_TOKEN", "UniversalWindowsComputerUseRuntime", "phase92_cli_line", "run_phase92_universal_windows_computer_use_contract"])  # 新增代码+Phase92UniversalComputerUse：把 Phase92 名称加入包级公开导出；如果没有这行代码，from learning_agent.computer_use import * 会漏掉通用模式。
```

- [ ] **Step 6: Run focused tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_universal_mode_phase92
```

Expected:

```text
Ran 3 tests
OK
```

---

### Task 3: Add Computer Use Mode Tool Route

**Files:**
- Modify: `learning_agent/computer_use/tool_surface.py`
- Modify: `learning_agent/tools/schemas.py`
- Modify: `learning_agent/core/agent.py`

- [ ] **Step 1: Extend compatible operation normalization**

Allow:

```json
{"operation": "mode", "prompt": "打开 computer use，帮我操作一个普通 Windows 应用"}
```

and:

```json
{"operation": "run_prompt", "prompt": "打开 computer use，帮我操作一个普通 Windows 应用"}
```

Both must route to a new internal target:

```python
{"target_tool": "computer_use_mode", "target_arguments": {"prompt": "...", "real_actions": False}}
```

- [ ] **Step 2: Keep action-like requests gated**

If `real_actions=True`, the route must be treated as action-like and must not bypass `ask_permission`.

- [ ] **Step 3: Add agent handler**

Add `_computer_use_mode(self, arguments)` in `learning_agent/core/agent.py`.

The handler must:

- Instantiate `UniversalWindowsComputerUseRuntime`.
- Call `run_prompt(prompt, real_actions=False)` by default.
- Record `computer_use_mode` observation.
- Return a short JSON/text summary.
- Not invoke app-specific smoke modules.

- [ ] **Step 4: Update schema description**

Update `computer_use` / `computer-use` descriptions so users and models know `operation=mode` starts generic Computer Use mode.

- [ ] **Step 5: Add tests or extend Phase92 tests**

Test that `operation=mode` normalizes to `computer_use_mode` and does not dispatch to Notepad/Paint-specific modules.

---

### Task 4: Add Acceptance Scenario

**Files:**
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase92_universal_windows_computer_use_mode.json`

- [ ] **Step 1: Add visible terminal scenario**

The prompt must tell the agent:

```text
Please run one Phase 92 Universal Windows Computer Use mode acceptance.
Use only the project terminal self-check command in safe contract mode.
Do not open real applications.
Do not interact with user windows.
Do not install dependencies.
Do not change registry.
Do not change Windows settings.
```

- [ ] **Step 2: Require self-check command**

The scenario must require:

```powershell
$env:PYTHONPATH='..'; python -c "from learning_agent.computer_use.universal_mode import main; raise SystemExit(main())"
```

- [ ] **Step 3: Require stable final line**

The final copied line must be:

```text
PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_READY PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK single_universal_runtime=true prompt_to_any_normal_app=true per_app_controller_required=false representative_apps_are_acceptance_only=true generic_observe_plan_act_verify_loop=true uses_observation_fusion=true uses_prompt_task_planner=true uses_generic_action_layer=true uses_real_app_safety_boundary=true uses_production_host_adapter=true high_risk_requires_confirmation=true unauthorized_window_zero_events=true target_drift_blocks_action=true raw_text_hidden=true default_real_actions_enabled=false uncontrolled_actions_expanded=false
```

---

### Task 5: Verification

**Files:**
- No new source files beyond previous tasks.

- [ ] **Step 1: Run focused Phase92 tests**

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_universal_mode_phase92
```

Expected: OK.

- [ ] **Step 2: Run Phase90-92 regression**

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_live_app_dispatcher_phase90 learning_agent.tests.test_windows_computer_use_notepad_live_smoke_phase91 learning_agent.tests.test_windows_computer_use_universal_mode_phase92
```

Expected: OK.

- [ ] **Step 3: Run Windows Computer Use discovery**

```powershell
python -m unittest discover learning_agent\tests -p "test_windows_computer_use*.py"
```

Expected: OK.

- [ ] **Step 4: Run compileall**

```powershell
python -m compileall -q learning_agent
```

Expected: no output and exit code 0.

- [ ] **Step 5: Run real visible terminal acceptance**

```powershell
$scenario=(Resolve-Path learning_agent\acceptance_controller\scenarios\agent_capability_phase92_universal_windows_computer_use_mode.json).Path
powershell -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\controller.ps1 -ScenarioPath $scenario
```

Expected result JSON:

```text
completed=True
assertion_passed=True
final_printed=True
permission_sent_count=0
```

---

### Task 6: Records And Learning Backup

**Files:**
- Modify: `agent_memory/context.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`
- Modify: `task_plan.md`
- Modify: `progress.md`
- Create: `agent_memory/agent_capability_phase92_universal_windows_computer_use_mode_20260604.md`
- Create directory: `learning_agent/test/agent_capability_phase92_universal_windows_computer_use_mode_20260604/`

- [ ] **Step 1: Update project memory**

Record:

- Phase92 adds one universal runtime.
- App-specific controllers are explicitly rejected.
- Representative apps are acceptance samples only.
- Real actions remain disabled by default.
- Visible terminal acceptance evidence path.

- [ ] **Step 2: Copy learning backup**

Copy:

- `learning_agent/computer_use/universal_mode.py`
- `learning_agent/tests/test_windows_computer_use_universal_mode_phase92.py`
- `learning_agent/computer_use/__init__.py`
- `learning_agent/computer_use/tool_surface.py`
- `learning_agent/core/agent.py`
- `learning_agent/tools/schemas.py`
- Phase92 scenario JSON
- Phase92 memory record

to:

```text
learning_agent/test/agent_capability_phase92_universal_windows_computer_use_mode_20260604/
```

---

## Self-Review

Spec coverage:

- User correction is covered by `single_universal_runtime=true`, `per_app_controller_required=false`, and `representative_apps_are_acceptance_only=true`.
- Generic prompt-to-control session is covered by `run_prompt(...)` and `operation=mode`.
- Existing modules are reused instead of duplicated.
- Safety constraints remain explicit.
- Real visible terminal acceptance remains mandatory before claiming completion.

Placeholder scan:

- No `TBD`, `TODO`, or “implement later” placeholders are present.
- Every implementation task has exact file paths, expected commands, and expected outputs.

Type consistency:

- Public names are consistent: `UniversalWindowsComputerUseRuntime`, `run_phase92_universal_windows_computer_use_contract`, `phase92_cli_line`, `PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MARKER`, and `PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK_TOKEN`.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-04-phase92-universal-windows-computer-use-mode.md`.

Recommended execution approach: inline execution with checkpoints, because Phase92 modifies shared Computer Use routing and should be verified carefully after each task.
