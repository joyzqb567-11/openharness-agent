# Universal Computer Use Permission Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build command-driven universal Computer Use permission modes so `/computer use` controls ordinary Windows apps through action-risk and target-risk policy instead of per-app allowlists.

**Architecture:** Add a focused `ComputerUseModeSessionStore` that records observe, normal, and full modes under `learning_agent/memory/computer_use/mode_sessions`. Wire `/computer use`, `/computer stop`, `/computer permissions`, and `/computer use --full-confirm <token>` into the existing terminal command path, then let the universal live execution gate consult this mode session before low-level dispatch. Keep Phase92/93 as the universal runtime foundation, keep representative apps as acceptance samples only, and keep dangerous targets, sensitive input, target drift, expired mode, and abort as hard stops.

**Tech Stack:** Python 3, `unittest`, existing `learning_agent.computer_use` modules, PowerShell acceptance controller, `start_oauth_agent.bat` visible terminal acceptance.

---

## File Structure

- Create `learning_agent/computer_use/mode_session.py`
  - Owns Phase98 constants, mode-state storage, permission rendering, full-mode token generation, stop/abort integration helpers, and action-risk evaluation.
  - Has no app-specific controller logic and no per-app ordinary allowlist.
- Create `learning_agent/tests/test_windows_computer_use_mode_session_phase98.py`
  - Tests mode session state, permissions, stop, sensitive-text hiding, and full-mode confirmation.
- Create `learning_agent/tests/test_windows_computer_use_mode_commands_phase98.py`
  - Tests `/computer use`, `/computer use --observe`, `/computer use --full`, `/computer use --full-confirm`, `/computer stop`, `/computer permissions`, and `/computer status` terminal wiring.
- Modify `learning_agent/app/interactive.py`
  - Imports `ComputerUseModeSessionStore`.
  - Adds `/computer use`, `/computer stop`, `/computer permissions`, and `/computer use --full-confirm <token>`.
  - Keeps `/computer abort` as a compatible lower-level stop path.
- Modify `learning_agent/app/computer_status_renderer.py`
  - Displays current mode, full-mode flag, TTL, allowed action classes, and command hints.
- Modify `learning_agent/computer_use/real_app_safety_boundary.py`
  - Adds a mode-aware evaluation path that can allow ordinary-app normal-mode actions without app allowlists while still refusing dangerous targets.
- Modify `learning_agent/computer_use/universal_live_execution.py`
  - Reads mode session before action dispatch and reports `per_app_allowlist_required=false`.
- Modify `learning_agent/computer_use/__init__.py`
  - Exports Phase98 APIs.
- Create `learning_agent/tests/test_windows_computer_use_mode_gate_phase99.py`
  - Tests that normal mode permits ordinary targets by risk policy and rejects unsafe targets, expired modes, observe mode writes, and abort.
- Create `learning_agent/acceptance_controller/scenarios/agent_capability_phase101_universal_computer_use_permission_mode.json`
  - Visible-terminal scenario for `/computer use`, status, generic contract prompt, and `/computer stop`.
- Update memory and backups:
  - `agent_memory/context.md`
  - `agent_memory/progress.md`
  - `agent_memory/bugs.md`
  - `learning_agent/test/universal_computer_use_permission_mode_20260605/`

---

### Task 1: Phase98 Red Tests For Mode Session

**Files:**
- Create: `learning_agent/tests/test_windows_computer_use_mode_session_phase98.py`
- Create: `learning_agent/computer_use/mode_session.py`

- [ ] **Step 1: Write the failing mode-session tests**

Add this test file:

```python
import json  # 新增代码+Phase98UniversalComputerUseMode：导入 JSON 用来检查状态文件不会泄露敏感原文；如果没有这行代码，就无法验证隐私边界。
import tempfile  # 新增代码+Phase98UniversalComputerUseMode：导入临时目录用来隔离测试状态；如果没有这行代码，测试会污染真实 memory 目录。
import unittest  # 新增代码+Phase98UniversalComputerUseMode：导入 unittest 以符合项目现有测试风格；如果没有这行代码，标准测试发现机制找不到测试类。
from pathlib import Path  # 新增代码+Phase98UniversalComputerUseMode：导入 Path 统一处理 Windows 路径；如果没有这行代码，路径拼接会变脆弱。

from learning_agent.computer_use.mode_session import (  # 新增代码+Phase98UniversalComputerUseMode：导入待实现的模式 session API；如果没有这行代码，测试无法锁定公开接口。
    PHASE98_COMPUTER_USE_MODE_READY,  # 新增代码+Phase98UniversalComputerUseMode：导入 ready marker；如果没有这行代码，终端验收没有稳定锚点。
    PHASE98_COMPUTER_USE_MODE_OK,  # 新增代码+Phase98UniversalComputerUseMode：导入 OK token；如果没有这行代码，测试无法确认合同输出。
    ComputerUseModeSessionStore,  # 新增代码+Phase98UniversalComputerUseMode：导入模式 session store；如果没有这行代码，测试无法创建模式状态。
)


class ComputerUseModeSessionPhase98Tests(unittest.TestCase):  # 新增代码+Phase98UniversalComputerUseMode：类段开始，集中验证 /computer use 的权限模式状态；如果没有这个类，Phase98 的核心状态没有门禁。
    def test_normal_mode_does_not_require_per_app_allowlist(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证普通模式不依赖应用白名单；如果没有这段测试，架构可能滑回 per-app allowlist。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，不同测试会共享状态文件。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，测试没有状态操作对象。
            result = store.open_mode(mode="normal", reason="打开 computer use，控制普通 Windows 应用")  # 新增代码+Phase98UniversalComputerUseMode：打开普通模式；如果没有这行代码，无法验证 normal 语义。
            status = store.status()  # 新增代码+Phase98UniversalComputerUseMode：读取当前状态；如果没有这行代码，无法确认状态已落盘。
        self.assertTrue(result["opened"])  # 新增代码+Phase98UniversalComputerUseMode：断言模式已打开；如果没有这行代码，失败结果可能被忽略。
        self.assertEqual(status["mode"], "normal")  # 新增代码+Phase98UniversalComputerUseMode：断言当前模式是 normal；如果没有这行代码，observe/full 混淆不会被发现。
        self.assertFalse(status["per_app_allowlist_required"])  # 新增代码+Phase98UniversalComputerUseMode：断言不需要应用白名单；如果没有这行代码，用户纠偏点没有自动化保护。
        self.assertTrue(status["ordinary_apps_allowed_by_risk_policy"])  # 新增代码+Phase98UniversalComputerUseMode：断言普通应用由风险策略放行；如果没有这行代码，normal mode 的产品意义不明确。
        self.assertIn("click", status["allowed_action_classes"])  # 新增代码+Phase98UniversalComputerUseMode：断言普通点击被允许；如果没有这行代码，普通控制模式可能只剩观察。
        self.assertIn("type_text", status["allowed_action_classes"])  # 新增代码+Phase98UniversalComputerUseMode：断言普通输入被允许；如果没有这行代码，普通应用无法被真实操作。
        self.assertEqual(status["marker"], PHASE98_COMPUTER_USE_MODE_READY)  # 新增代码+Phase98UniversalComputerUseMode：断言 marker 稳定；如果没有这行代码，真实终端验收会漂移。
        self.assertEqual(status["ok_token"], PHASE98_COMPUTER_USE_MODE_OK)  # 新增代码+Phase98UniversalComputerUseMode：断言 OK token 稳定；如果没有这行代码，场景断言没有成功锚点。

    def test_observe_mode_blocks_write_actions(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证观察模式零写动作；如果没有这段测试，observe 可能误发送低层输入。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，状态会污染其它测试。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，无法打开 observe mode。
            store.open_mode(mode="observe", reason="只观察当前桌面")  # 新增代码+Phase98UniversalComputerUseMode：打开观察模式；如果没有这行代码，后续权限判断没有来源。
            decision = store.evaluate_action({"process_name": "notepad.exe"}, "type_text")  # 新增代码+Phase98UniversalComputerUseMode：评估写文本动作；如果没有这行代码，observe 拒绝没有证据。
        self.assertFalse(decision["allowed"])  # 新增代码+Phase98UniversalComputerUseMode：断言写动作被拒绝；如果没有这行代码，观察模式可能变成写模式。
        self.assertEqual(decision["decision"], "observe_mode_blocks_write_action")  # 新增代码+Phase98UniversalComputerUseMode：断言原因码稳定；如果没有这行代码，错误处理不可审计。
        self.assertEqual(decision["low_level_event_count"], 0)  # 新增代码+Phase98UniversalComputerUseMode：断言零低层事件；如果没有这行代码，拒绝后仍可能触发输入。

    def test_stop_sets_abort_and_blocks_later_actions(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 stop 会阻断后续动作；如果没有这段测试，急停可能只是显示文字。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，stop 状态会污染真实环境。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，无法打开和停止 session。
            store.open_mode(mode="normal", reason="准备控制普通应用")  # 新增代码+Phase98UniversalComputerUseMode：先打开普通模式；如果没有这行代码，stop 无法证明从活动态变为停止态。
            stop = store.stop(reason="用户输入 /computer stop")  # 新增代码+Phase98UniversalComputerUseMode：执行停止；如果没有这行代码，后续动作不会被阻断。
            decision = store.evaluate_action({"process_name": "notepad.exe"}, "click")  # 新增代码+Phase98UniversalComputerUseMode：停止后再评估点击；如果没有这行代码，无法证明停止生效。
        self.assertTrue(stop["stopped"])  # 新增代码+Phase98UniversalComputerUseMode：断言 stop 已记录；如果没有这行代码，停止失败可能被忽略。
        self.assertFalse(decision["allowed"])  # 新增代码+Phase98UniversalComputerUseMode：断言后续动作被拒绝；如果没有这行代码，stop 不能保护真实桌面。
        self.assertEqual(decision["decision"], "computer_use_stopped")  # 新增代码+Phase98UniversalComputerUseMode：断言稳定原因码；如果没有这行代码，用户不知道为什么被阻断。
        self.assertEqual(decision["low_level_event_count"], 0)  # 新增代码+Phase98UniversalComputerUseMode：断言没有低层事件；如果没有这行代码，急停可能只是事后报告。

    def test_full_mode_requires_confirmation_before_activation(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 full 不能单命令裸开；如果没有这段测试，最高风险模式会变成默认绕过。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，full token 会污染其它测试。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，无法请求 full mode。
            request = store.request_full_mode(reason="用户请求完全接管")  # 新增代码+Phase98UniversalComputerUseMode：请求 full 模式；如果没有这行代码，无法得到确认 token。
            before = store.status()  # 新增代码+Phase98UniversalComputerUseMode：确认请求后还未进入 full；如果没有这行代码，单命令裸开不会被发现。
            confirmed = store.confirm_full_mode(request["confirmation_token"], reason="用户二次确认 full mode")  # 新增代码+Phase98UniversalComputerUseMode：用 token 二次确认；如果没有这行代码，无法证明确认路径可用。
            after = store.status()  # 新增代码+Phase98UniversalComputerUseMode：读取确认后的状态；如果没有这行代码，full 激活结果不可见。
        self.assertFalse(before["full_mode"])  # 新增代码+Phase98UniversalComputerUseMode：断言请求阶段没有 full 权限；如果没有这行代码，风险说明可能被跳过。
        self.assertTrue(request["strong_confirmation_required"])  # 新增代码+Phase98UniversalComputerUseMode：断言需要强确认；如果没有这行代码，full 安全边界没有证据。
        self.assertTrue(confirmed["opened"])  # 新增代码+Phase98UniversalComputerUseMode：断言确认后打开；如果没有这行代码，full 确认路径可能坏掉。
        self.assertTrue(after["full_mode"])  # 新增代码+Phase98UniversalComputerUseMode：断言 full 标志为真；如果没有这行代码，状态页无法显示风险模式。
        self.assertLessEqual(after["ttl_seconds"], 300)  # 新增代码+Phase98UniversalComputerUseMode：断言 full TTL 不超过 5 分钟；如果没有这行代码，长期全权限风险不可控。

    def test_state_hides_sensitive_reason_text(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证状态文件不写敏感原文；如果没有这段测试，用户 prompt 可能泄露进磁盘。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，隐私测试会污染真实状态。
            root = Path(temp_dir)  # 新增代码+Phase98UniversalComputerUseMode：保存根路径；如果没有这行代码，后续读取文件需要重复构造路径。
            store = ComputerUseModeSessionStore(base_dir=root)  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，无法写入状态文件。
            store.open_mode(mode="normal", reason="secret-password-123 打开 computer use")  # 新增代码+Phase98UniversalComputerUseMode：写入包含敏感词的原因；如果没有这行代码，隐私扫描没有样本。
            serialized = json.dumps(json.loads((root / "current.json").read_text(encoding="utf-8")), ensure_ascii=False)  # 新增代码+Phase98UniversalComputerUseMode：读取并序列化状态文件；如果没有这行代码，无法扫描落盘内容。
        self.assertNotIn("secret-password-123", serialized)  # 新增代码+Phase98UniversalComputerUseMode：断言敏感原文没有落盘；如果没有这行代码，状态文件可能泄露用户内容。
        self.assertIn("reason_sha256_16", serialized)  # 新增代码+Phase98UniversalComputerUseMode：断言保留脱敏哈希；如果没有这行代码，排查时无法关联用户请求。


if __name__ == "__main__":  # 新增代码+Phase98UniversalComputerUseMode：文件入口段开始，允许直接运行测试；如果没有这行代码，小白用户必须记完整 unittest 命令。
    unittest.main()  # 新增代码+Phase98UniversalComputerUseMode：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_mode_session_phase98
```

Expected:

```text
ModuleNotFoundError: No module named 'learning_agent.computer_use.mode_session'
```

- [ ] **Step 3: Commit the red test**

Run:

```powershell
git add learning_agent/tests/test_windows_computer_use_mode_session_phase98.py
git commit -m "test: add computer use mode session contract"
```

---

### Task 2: Implement Phase98 Mode Session Store

**Files:**
- Create: `learning_agent/computer_use/mode_session.py`
- Modify: `learning_agent/computer_use/__init__.py`
- Test: `learning_agent/tests/test_windows_computer_use_mode_session_phase98.py`

- [ ] **Step 1: Create the mode-session module**

Implement `learning_agent/computer_use/mode_session.py` with these public APIs:

```python
from __future__ import annotations  # 新增代码+Phase98UniversalComputerUseMode：启用延迟类型解析；如果没有这行代码，后续类型标注更容易受导入顺序影响。
import hashlib  # 新增代码+Phase98UniversalComputerUseMode：导入哈希库用于脱敏 reason；如果没有这行代码，状态文件要么泄露原文要么无法追踪。
import json  # 新增代码+Phase98UniversalComputerUseMode：导入 JSON 用于稳定读写状态；如果没有这行代码，mode session 无法落盘。
import secrets  # 新增代码+Phase98UniversalComputerUseMode：导入安全随机库用于 full mode 确认 token；如果没有这行代码，强确认 token 容易可预测。
import time  # 新增代码+Phase98UniversalComputerUseMode：导入时间库用于 TTL 和过期判断；如果没有这行代码，模式不会自动过期。
from pathlib import Path  # 新增代码+Phase98UniversalComputerUseMode：导入 Path 统一处理 Windows 路径；如果没有这行代码，状态目录处理会变脆弱。
from typing import Any  # 新增代码+Phase98UniversalComputerUseMode：导入 Any 描述 JSON 风格数据；如果没有这行代码，公开接口边界不清楚。

try:  # 新增代码+Phase98UniversalComputerUseMode：优先按包路径导入原子写文件工具；如果没有这段代码，测试和 bat 入口不能共享同一写入方式。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase98UniversalComputerUseMode：复用项目原子 JSON 写入；如果没有这行代码，状态文件可能半写。
except ModuleNotFoundError as error:  # 新增代码+Phase98UniversalComputerUseMode：兼容 start_oauth_agent.bat 从 learning_agent 目录运行；如果没有这段代码，真实终端可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase98UniversalComputerUseMode：只对包路径缺失 fallback；如果没有这行代码，真实内部 bug 会被误吞。
        raise  # 新增代码+Phase98UniversalComputerUseMode：重新抛出非路径类导入错误；如果没有这行代码，排查依赖错误会困难。
    from runtime.files import atomic_write_json  # type: ignore  # 新增代码+Phase98UniversalComputerUseMode：脚本模式导入原子写入工具；如果没有这行代码，bat 入口不能写状态。

PHASE98_COMPUTER_USE_MODE_READY = "PHASE98_COMPUTER_USE_MODE_READY"  # 新增代码+Phase98UniversalComputerUseMode：定义 ready marker；如果没有这行代码，验收脚本没有稳定锚点。
PHASE98_COMPUTER_USE_MODE_OK = "PHASE98_COMPUTER_USE_MODE_OK"  # 新增代码+Phase98UniversalComputerUseMode：定义 OK token；如果没有这行代码，终端输出无法稳定表示成功。
PHASE98_COMPUTER_USE_MODE_MODEL = "phase98_universal_computer_use_permission_mode"  # 新增代码+Phase98UniversalComputerUseMode：定义模型名；如果没有这行代码，报告无法区分阶段版本。
DEFAULT_MODE_SESSION_ID = "learning-agent-default-session"  # 新增代码+Phase98UniversalComputerUseMode：定义默认 session；如果没有这行代码，终端命令无法共享同一状态。
DEFAULT_MODE_SESSION_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "mode_sessions"  # 新增代码+Phase98UniversalComputerUseMode：定义默认状态目录；如果没有这行代码，mode session 没有稳定落点。
OBSERVE_ACTIONS = ("observe_screen", "list_windows")  # 新增代码+Phase98UniversalComputerUseMode：定义观察模式动作；如果没有这行代码，observe 权限边界不清楚。
NORMAL_ACTIONS = ("observe_screen", "list_windows", "focus_window", "click", "double_click", "type_text", "hotkey_safe", "scroll", "drag", "clipboard_temporary_text", "save_current_document")  # 新增代码+Phase98UniversalComputerUseMode：定义普通模式动作；如果没有这行代码，/computer use 不知道允许什么。
FULL_ACTIONS = NORMAL_ACTIONS + ("hotkey_system_candidate", "file_delete_candidate", "install_candidate", "submit_form_candidate")  # 新增代码+Phase98UniversalComputerUseMode：定义 full 候选动作；如果没有这行代码，full 模式无法表达更宽动作面。
DANGEROUS_TARGET_TERMS = ("powershell", "cmd.exe", "command prompt", "windows terminal", "administrator", "uac", "windows security", "defender", "firewall", "registry", "services", "password", "credential", "captcha", "payment", "token", "api key", "private key", "验证码", "密码", "支付", "付款", "令牌", "私钥", "管理员", "安全")  # 新增代码+Phase98UniversalComputerUseMode：定义目标风险词；如果没有这行代码，普通模式可能误控危险目标。
SENSITIVE_REASON_TERMS = ("password", "token", "api key", "private key", "captcha", "验证码", "密码", "令牌", "私钥")  # 新增代码+Phase98UniversalComputerUseMode：定义敏感原因词；如果没有这行代码，状态文件可能泄露敏感输入。


def _phase98_now() -> float:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，统一读取当前时间；如果没有这段函数，测试注入时间会更困难。
    return time.time()  # 新增代码+Phase98UniversalComputerUseMode：返回 Unix 时间；如果没有这行代码，TTL 无法计算。


def _phase98_sha256_16(value: Any) -> str:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，生成短哈希；如果没有这段函数，隐私追踪会重复实现。
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase98UniversalComputerUseMode：稳定序列化输入；如果没有这行代码，同一数据顺序变化会得到不同哈希。
    return hashlib.sha256(serialized.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase98UniversalComputerUseMode：返回前 16 位哈希；如果没有这行代码，报告无法脱敏关联。


def _phase98_bool(value: Any) -> bool:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，统一布尔转换；如果没有这段函数，字符串布尔容易误判。
    return bool(value)  # 新增代码+Phase98UniversalComputerUseMode：返回 Python 布尔值；如果没有这行代码，调用方会散落转换逻辑。


def _phase98_target_blob(window: dict[str, Any]) -> str:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，拼接目标窗口风险文本；如果没有这段函数，危险目标扫描会漏字段。
    return " ".join(str(window.get(key, "")) for key in ("app_id", "process_name", "title_preview", "class_name")).lower()  # 新增代码+Phase98UniversalComputerUseMode：返回小写目标摘要；如果没有这行代码，大小写和字段差异会影响风险判断。


class ComputerUseModeSessionStore:  # 新增代码+Phase98UniversalComputerUseMode：类段开始，管理通用 Computer Use 模式；如果没有这个类，/computer use 状态会散落在多个模块。
    def __init__(self, base_dir: str | Path | None = None, now_func: Any = _phase98_now) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，初始化状态目录和时钟；如果没有这段函数，测试无法隔离状态。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_MODE_SESSION_ROOT  # 新增代码+Phase98UniversalComputerUseMode：保存状态目录；如果没有这行代码，store 不知道读写哪里。
        self.now_func = now_func  # 新增代码+Phase98UniversalComputerUseMode：保存时钟函数；如果没有这行代码，过期测试无法稳定。
        self.state_path = self.base_dir / "current.json"  # 新增代码+Phase98UniversalComputerUseMode：保存当前状态路径；如果没有这行代码，status 无法定位文件。
        self.pending_full_path = self.base_dir / "pending_full.json"  # 新增代码+Phase98UniversalComputerUseMode：保存 full 确认请求路径；如果没有这行代码，二次确认无法跨命令。

    def _write_state(self, payload: dict[str, Any]) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，写当前模式状态；如果没有这段函数，多个入口会重复落盘逻辑。
        atomic_write_json(self.state_path, payload)  # 新增代码+Phase98UniversalComputerUseMode：原子写入 JSON；如果没有这行代码，中断时可能留下半截状态。

    def _read_json(self, path: Path) -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，安全读取 JSON；如果没有这段函数，坏文件会让终端命令崩溃。
        if not path.exists():  # 新增代码+Phase98UniversalComputerUseMode：检查文件是否存在；如果没有这行代码，首次运行会报错。
            return {}  # 新增代码+Phase98UniversalComputerUseMode：缺文件返回空状态；如果没有这行代码，首次状态不可用。
        try:  # 新增代码+Phase98UniversalComputerUseMode：捕获 JSON 解析错误；如果没有这行代码，损坏文件会打断用户终端。
            data = json.loads(path.read_text(encoding="utf-8"))  # 新增代码+Phase98UniversalComputerUseMode：读取并解析 JSON；如果没有这行代码，无法获得落盘状态。
        except (OSError, json.JSONDecodeError):  # 新增代码+Phase98UniversalComputerUseMode：处理文件或格式错误；如果没有这行代码，坏状态不能自愈。
            return {}  # 新增代码+Phase98UniversalComputerUseMode：坏状态返回空字典；如果没有这行代码，用户需要手删文件。
        return data if isinstance(data, dict) else {}  # 新增代码+Phase98UniversalComputerUseMode：只接受字典状态；如果没有这行代码，数组或字符串会污染逻辑。

    def _build_state(self, mode: str, ttl_seconds: int, reason: str, full_mode: bool) -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，构造标准状态；如果没有这段函数，normal/observe/full 字段容易不一致。
        now = float(self.now_func())  # 新增代码+Phase98UniversalComputerUseMode：读取当前时间；如果没有这行代码，created/expires 无法计算。
        actions = FULL_ACTIONS if full_mode else OBSERVE_ACTIONS if mode == "observe" else NORMAL_ACTIONS  # 新增代码+Phase98UniversalComputerUseMode：按模式选择动作集合；如果没有这行代码，权限等级不会生效。
        return {"marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK, "model": PHASE98_COMPUTER_USE_MODE_MODEL, "session_id": DEFAULT_MODE_SESSION_ID, "mode": mode, "full_mode": full_mode, "opened": True, "stopped": False, "created_at_epoch": now, "expires_at_epoch": now + ttl_seconds, "ttl_seconds": ttl_seconds, "allowed_action_classes": list(actions), "high_risk_requires_confirmation": True, "per_app_allowlist_required": False, "ordinary_apps_allowed_by_risk_policy": mode == "normal" and not full_mode, "target_recheck_required": True, "abort_required": True, "audit_required": True, "reason_sha256_16": _phase98_sha256_16(reason), "reason_text_included": False}  # 新增代码+Phase98UniversalComputerUseMode：返回完整脱敏状态；如果没有这行代码，状态页和执行门拿不到统一事实。

    def open_mode(self, mode: str = "normal", reason: str = "", ttl_seconds: int | None = None) -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，打开 observe 或 normal 模式；如果没有这段函数，/computer use 没有状态入口。
        selected = "observe" if str(mode).strip().lower() == "observe" else "normal"  # 新增代码+Phase98UniversalComputerUseMode：只允许 observe/normal 直接打开；如果没有这行代码，full 可能被单命令绕开。
        ttl = int(ttl_seconds if ttl_seconds is not None else 900)  # 新增代码+Phase98UniversalComputerUseMode：普通模式默认 15 分钟；如果没有这行代码，授权时长不明确。
        state = self._build_state(selected, max(1, ttl), reason, full_mode=False)  # 新增代码+Phase98UniversalComputerUseMode：构造状态；如果没有这行代码，无法写入标准字段。
        self._write_state(state)  # 新增代码+Phase98UniversalComputerUseMode：写入当前状态；如果没有这行代码，命令结果不会跨轮保存。
        return dict(state, opened=True)  # 新增代码+Phase98UniversalComputerUseMode：返回结果副本；如果没有这行代码，调用方看不到打开状态。

    def request_full_mode(self, reason: str = "") -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，请求 full 模式确认 token；如果没有这段函数，full 会缺少强确认。
        token = "FULL-" + secrets.token_hex(4).upper()  # 新增代码+Phase98UniversalComputerUseMode：生成短确认 token；如果没有这行代码，用户无法二次确认。
        pending = {"marker": PHASE98_COMPUTER_USE_MODE_READY, "confirmation_token": token, "strong_confirmation_required": True, "created_at_epoch": float(self.now_func()), "expires_at_epoch": float(self.now_func()) + 120, "reason_sha256_16": _phase98_sha256_16(reason), "reason_text_included": False}  # 新增代码+Phase98UniversalComputerUseMode：构造 pending full 记录；如果没有这行代码，确认请求不能跨命令保存。
        atomic_write_json(self.pending_full_path, pending)  # 新增代码+Phase98UniversalComputerUseMode：写入 pending full 文件；如果没有这行代码，下一条确认命令无法验证 token。
        return dict(pending, opened=False, full_mode=False)  # 新增代码+Phase98UniversalComputerUseMode：返回风险提示所需字段；如果没有这行代码，终端无法显示 token。

    def confirm_full_mode(self, confirmation_token: str, reason: str = "") -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，确认并打开 full 模式；如果没有这段函数，full mode 无法安全激活。
        pending = self._read_json(self.pending_full_path)  # 新增代码+Phase98UniversalComputerUseMode：读取 pending full 请求；如果没有这行代码，无法验证二次确认。
        if not pending or pending.get("confirmation_token") != str(confirmation_token).strip():  # 新增代码+Phase98UniversalComputerUseMode：检查 token 是否匹配；如果没有这行代码，任意文本都能开 full。
            return {"opened": False, "full_mode": False, "decision": "full_mode_confirmation_token_mismatch", "low_level_event_count": 0}  # 新增代码+Phase98UniversalComputerUseMode：返回拒绝；如果没有这行代码，失败路径不稳定。
        if float(pending.get("expires_at_epoch", 0) or 0) < float(self.now_func()):  # 新增代码+Phase98UniversalComputerUseMode：检查 token 是否过期；如果没有这行代码，旧 token 可长期复用。
            return {"opened": False, "full_mode": False, "decision": "full_mode_confirmation_expired", "low_level_event_count": 0}  # 新增代码+Phase98UniversalComputerUseMode：返回过期拒绝；如果没有这行代码，用户看不懂失败原因。
        state = self._build_state("full", 300, reason, full_mode=True)  # 新增代码+Phase98UniversalComputerUseMode：构造 full 状态且 TTL 5 分钟；如果没有这行代码，full 权限可能过长。
        self._write_state(state)  # 新增代码+Phase98UniversalComputerUseMode：写入 full 状态；如果没有这行代码，确认不会生效。
        return dict(state, opened=True, decision="full_mode_confirmed")  # 新增代码+Phase98UniversalComputerUseMode：返回确认成功；如果没有这行代码，终端看不到结果。

    def stop(self, reason: str = "") -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，停止 Computer Use 模式；如果没有这段函数，/computer stop 不能阻断后续动作。
        state = self.status()  # 新增代码+Phase98UniversalComputerUseMode：读取当前状态；如果没有这行代码，stop 不知道之前模式。
        stopped = dict(state, stopped=True, mode="stopped", full_mode=False, allowed_action_classes=[], expires_at_epoch=float(self.now_func()), reason_sha256_16=_phase98_sha256_16(reason), reason_text_included=False)  # 新增代码+Phase98UniversalComputerUseMode：构造停止状态；如果没有这行代码，后续 evaluate_action 不知道已停止。
        self._write_state(stopped)  # 新增代码+Phase98UniversalComputerUseMode：写入停止状态；如果没有这行代码，stop 只在内存中生效。
        return {"stopped": True, "decision": "computer_use_stopped", "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK, "low_level_event_count": 0}  # 新增代码+Phase98UniversalComputerUseMode：返回停止结果；如果没有这行代码，终端输出没有稳定字段。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，读取当前模式状态；如果没有这段函数，状态页和执行门无法共享事实。
        state = self._read_json(self.state_path)  # 新增代码+Phase98UniversalComputerUseMode：读取落盘状态；如果没有这行代码，status 只能返回默认空态。
        if not state:  # 新增代码+Phase98UniversalComputerUseMode：检查是否没有状态；如果没有这行代码，首次状态字段会缺失。
            return {"marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK, "model": PHASE98_COMPUTER_USE_MODE_MODEL, "mode": "off", "opened": False, "stopped": False, "expired": False, "full_mode": False, "ttl_seconds": 0, "allowed_action_classes": [], "per_app_allowlist_required": False, "ordinary_apps_allowed_by_risk_policy": False, "state_path": str(self.state_path)}  # 新增代码+Phase98UniversalComputerUseMode：返回默认关闭状态；如果没有这行代码，/computer status 首次运行会崩。
        remaining = max(0, int(float(state.get("expires_at_epoch", 0) or 0) - float(self.now_func())))  # 新增代码+Phase98UniversalComputerUseMode：计算剩余 TTL；如果没有这行代码，状态页无法显示过期。
        expired = bool(state.get("opened")) and remaining <= 0 and not bool(state.get("stopped"))  # 新增代码+Phase98UniversalComputerUseMode：判断模式是否过期；如果没有这行代码，旧模式会一直有效。
        return dict(state, expired=expired, ttl_seconds=remaining, state_path=str(self.state_path))  # 新增代码+Phase98UniversalComputerUseMode：返回带派生字段的状态；如果没有这行代码，执行门要重复计算。

    def permissions(self) -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，返回当前权限摘要；如果没有这段函数，/computer permissions 只能重复 status。
        status = self.status()  # 新增代码+Phase98UniversalComputerUseMode：读取当前状态；如果没有这行代码，权限输出没有事实来源。
        return {"marker": PHASE98_COMPUTER_USE_MODE_READY, "mode": status.get("mode", "off"), "allowed_action_classes": list(status.get("allowed_action_classes", []) or []), "high_risk_requires_confirmation": True, "per_app_allowlist_required": False, "dangerous_target_terms_hidden": True, "full_mode": bool(status.get("full_mode"))}  # 新增代码+Phase98UniversalComputerUseMode：返回权限摘要；如果没有这行代码，用户看不到允许范围。

    def evaluate_action(self, window: dict[str, Any], action_class: str) -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，按当前模式评估动作；如果没有这段函数，执行门不能使用 mode session。
        status = self.status()  # 新增代码+Phase98UniversalComputerUseMode：读取当前模式；如果没有这行代码，评估没有依据。
        action = str(action_class or "").strip()  # 新增代码+Phase98UniversalComputerUseMode：规范化动作名；如果没有这行代码，空白会导致误判。
        if status.get("mode") in {"off", "stopped"} or bool(status.get("stopped")):  # 新增代码+Phase98UniversalComputerUseMode：检查是否关闭或停止；如果没有这行代码，stop 后仍可能放行动作。
            return {"allowed": False, "decision": "computer_use_stopped", "low_level_event_count": 0, "mode": status.get("mode", "off")}  # 新增代码+Phase98UniversalComputerUseMode：返回停止拒绝；如果没有这行代码，低层 sender 可能被触发。
        if bool(status.get("expired")):  # 新增代码+Phase98UniversalComputerUseMode：检查模式是否过期；如果没有这行代码，旧授权会长期有效。
            return {"allowed": False, "decision": "mode_expired", "low_level_event_count": 0, "mode": status.get("mode", "off")}  # 新增代码+Phase98UniversalComputerUseMode：返回过期拒绝；如果没有这行代码，用户不知道要重新开启。
        target_blob = _phase98_target_blob(window)  # 新增代码+Phase98UniversalComputerUseMode：生成目标风险文本；如果没有这行代码，危险窗口无法识别。
        if any(term in target_blob for term in DANGEROUS_TARGET_TERMS):  # 新增代码+Phase98UniversalComputerUseMode：检查危险目标；如果没有这行代码，普通模式可能操作终端或安全窗口。
            return {"allowed": False, "decision": "dangerous_target_blocked", "low_level_event_count": 0, "mode": status.get("mode", "off")}  # 新增代码+Phase98UniversalComputerUseMode：返回危险目标拒绝；如果没有这行代码，风险拦截不可审计。
        if action not in set(status.get("allowed_action_classes", []) or []):  # 新增代码+Phase98UniversalComputerUseMode：检查动作是否允许；如果没有这行代码，observe/full/normal 分级无效。
            decision = "observe_mode_blocks_write_action" if status.get("mode") == "observe" else "action_risk_exceeds_mode"  # 新增代码+Phase98UniversalComputerUseMode：生成稳定原因码；如果没有这行代码，拒绝原因不清楚。
            return {"allowed": False, "decision": decision, "low_level_event_count": 0, "mode": status.get("mode", "off")}  # 新增代码+Phase98UniversalComputerUseMode：返回动作拒绝；如果没有这行代码，未授权动作可能继续。
        return {"allowed": True, "decision": "allowed_by_computer_use_mode", "low_level_event_count": 0, "mode": status.get("mode", "off"), "per_app_allowlist_required": False, "target_recheck_required": True, "abort_required": True, "audit_required": True}  # 新增代码+Phase98UniversalComputerUseMode：返回允许决策；如果没有这行代码，普通模式无法替代应用白名单。


__all__ = ["DEFAULT_MODE_SESSION_ROOT", "DEFAULT_MODE_SESSION_ID", "PHASE98_COMPUTER_USE_MODE_MODEL", "PHASE98_COMPUTER_USE_MODE_OK", "PHASE98_COMPUTER_USE_MODE_READY", "ComputerUseModeSessionStore"]  # 新增代码+Phase98UniversalComputerUseMode：公开稳定 API；如果没有这行代码，其它模块只能依赖内部名称。
```

- [ ] **Step 2: Export Phase98 APIs**

Add to `learning_agent/computer_use/__init__.py`:

```python
from learning_agent.computer_use.mode_session import DEFAULT_MODE_SESSION_ID, DEFAULT_MODE_SESSION_ROOT, PHASE98_COMPUTER_USE_MODE_MODEL, PHASE98_COMPUTER_USE_MODE_OK, PHASE98_COMPUTER_USE_MODE_READY, ComputerUseModeSessionStore  # 新增代码+Phase98UniversalComputerUseMode：公开通用 Computer Use 模式 session；如果没有这行代码，其它模块只能硬编码内部路径。
__all__.extend(["DEFAULT_MODE_SESSION_ID", "DEFAULT_MODE_SESSION_ROOT", "PHASE98_COMPUTER_USE_MODE_MODEL", "PHASE98_COMPUTER_USE_MODE_OK", "PHASE98_COMPUTER_USE_MODE_READY", "ComputerUseModeSessionStore"])  # 新增代码+Phase98UniversalComputerUseMode：把 Phase98 名称加入包级导出；如果没有这行代码，from learning_agent.computer_use import * 会漏掉新模式 API。
```

- [ ] **Step 3: Run the focused mode-session tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_mode_session_phase98
```

Expected:

```text
Ran 5 tests
OK
```

- [ ] **Step 4: Commit Phase98 store**

Run:

```powershell
git add learning_agent/computer_use/mode_session.py learning_agent/computer_use/__init__.py learning_agent/tests/test_windows_computer_use_mode_session_phase98.py
git commit -m "feat: add universal computer use mode session"
```

---

### Task 3: Wire `/computer use`, Stop, Permissions, And Status

**Files:**
- Create: `learning_agent/tests/test_windows_computer_use_mode_commands_phase98.py`
- Modify: `learning_agent/app/interactive.py`
- Modify: `learning_agent/app/computer_status_renderer.py`
- Test: `learning_agent/tests/test_windows_computer_use_mode_commands_phase98.py`

- [ ] **Step 1: Write failing terminal command tests**

Add tests that use `run_computer_terminal_command(...)` with a temporary workspace:

```python
import tempfile  # 新增代码+Phase98UniversalComputerUseMode：导入临时目录隔离终端命令状态；如果没有这行代码，测试会污染真实 memory。
import unittest  # 新增代码+Phase98UniversalComputerUseMode：导入 unittest；如果没有这行代码，测试无法被标准命令发现。
from pathlib import Path  # 新增代码+Phase98UniversalComputerUseMode：导入 Path 处理 workspace；如果没有这行代码，Windows 路径容易拼错。

from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase98UniversalComputerUseMode：导入真实 /computer 命令入口；如果没有这行代码，只能测试底层 store 而不能覆盖终端 UX。


class ComputerUseModeCommandPhase98Tests(unittest.TestCase):  # 新增代码+Phase98UniversalComputerUseMode：类段开始，验证终端命令接入；如果没有这个类，真实用户入口没有门禁。
    def test_computer_use_opens_normal_mode(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 /computer use 开普通模式；如果没有这段测试，命令可能仍显示不支持。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建临时 workspace；如果没有这行代码，命令会写真实状态。
            output = run_computer_terminal_command(Path(temp_dir), "/computer use")  # 新增代码+Phase98UniversalComputerUseMode：执行真实命令入口；如果没有这行代码，无法验证输出。
        self.assertIn("Computer Use Mode", output)  # 新增代码+Phase98UniversalComputerUseMode：断言新面板标题；如果没有这行代码，旧输出可能误通过。
        self.assertIn("mode=normal", output)  # 新增代码+Phase98UniversalComputerUseMode：断言 normal 模式；如果没有这行代码，模式错误不会暴露。
        self.assertIn("per_app_allowlist_required=false", output)  # 新增代码+Phase98UniversalComputerUseMode：断言不需要应用白名单；如果没有这行代码，核心架构目标可能丢失。
        self.assertIn("ordinary_apps_allowed_by_risk_policy=true", output)  # 新增代码+Phase98UniversalComputerUseMode：断言普通应用由风险策略放行；如果没有这行代码，用户看不出新设计。

    def test_computer_use_observe_mode_blocks_real_actions(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 observe 命令输出；如果没有这段测试，observe 可能不显示零事件边界。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建临时 workspace；如果没有这行代码，状态会污染真实目录。
            output = run_computer_terminal_command(Path(temp_dir), "/computer use --observe")  # 新增代码+Phase98UniversalComputerUseMode：执行 observe 模式；如果没有这行代码，无法验证只读入口。
        self.assertIn("mode=observe", output)  # 新增代码+Phase98UniversalComputerUseMode：断言 observe 模式；如果没有这行代码，命令可能开成 normal。
        self.assertIn("real_desktop_touched=false", output)  # 新增代码+Phase98UniversalComputerUseMode：断言不会触桌面；如果没有这行代码，用户可能误解 observe。
        self.assertIn("low_level_event_count=0", output)  # 新增代码+Phase98UniversalComputerUseMode：断言零低层事件；如果没有这行代码，拒绝路径不透明。

    def test_computer_stop_blocks_mode(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 stop 命令；如果没有这段测试，stop 可能只保留旧 abort 文案。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建临时 workspace；如果没有这行代码，stop 会影响真实状态。
            workspace = Path(temp_dir)  # 新增代码+Phase98UniversalComputerUseMode：保存 workspace；如果没有这行代码，后续命令需要重复转换。
            run_computer_terminal_command(workspace, "/computer use")  # 新增代码+Phase98UniversalComputerUseMode：先打开 normal；如果没有这行代码，stop 不知道停止什么。
            output = run_computer_terminal_command(workspace, "/computer stop")  # 新增代码+Phase98UniversalComputerUseMode：执行 stop；如果没有这行代码，无法验证新命令。
            status = run_computer_terminal_command(workspace, "/computer status")  # 新增代码+Phase98UniversalComputerUseMode：读取状态；如果没有这行代码，无法验证 stop 持久化。
        self.assertIn("stopped=true", output)  # 新增代码+Phase98UniversalComputerUseMode：断言 stop 输出成功；如果没有这行代码，失败也可能被忽略。
        self.assertIn("mode=stopped", status)  # 新增代码+Phase98UniversalComputerUseMode：断言状态变为 stopped；如果没有这行代码，后续动作可能继续。

    def test_full_mode_requires_confirm_command(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 full 强确认 UX；如果没有这段测试，full 可能单命令裸开。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建临时 workspace；如果没有这行代码，pending token 会污染真实目录。
            output = run_computer_terminal_command(Path(temp_dir), "/computer use --full")  # 新增代码+Phase98UniversalComputerUseMode：请求 full；如果没有这行代码，无法验证确认提示。
        self.assertIn("strong_confirmation_required=true", output)  # 新增代码+Phase98UniversalComputerUseMode：断言需要强确认；如果没有这行代码，风险边界可能消失。
        self.assertIn("/computer use --full-confirm", output)  # 新增代码+Phase98UniversalComputerUseMode：断言给出确认命令；如果没有这行代码，用户不知道下一步。
        self.assertIn("full_mode=false", output)  # 新增代码+Phase98UniversalComputerUseMode：断言请求阶段未激活 full；如果没有这行代码，单命令可能裸开。


if __name__ == "__main__":  # 新增代码+Phase98UniversalComputerUseMode：文件入口段开始；如果没有这行代码，无法直接运行本测试文件。
    unittest.main()  # 新增代码+Phase98UniversalComputerUseMode：启动 unittest；如果没有这行代码，直接运行不会执行测试。
```

- [ ] **Step 2: Run the red command tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_mode_commands_phase98
```

Expected:

```text
FAIL
```

The failure should mention unsupported `/computer` subcommand or missing mode output.

- [ ] **Step 3: Modify `interactive.py` imports**

Add package-mode import:

```python
from learning_agent.computer_use.mode_session import ComputerUseModeSessionStore  # 新增代码+Phase98UniversalComputerUseMode：导入通用 Computer Use 模式 store；如果没有这行代码，/computer use 无法写入 mode session。
```

Add script-mode fallback import:

```python
from computer_use.mode_session import ComputerUseModeSessionStore  # 新增代码+Phase98UniversalComputerUseMode：脚本模式导入通用模式 store；如果没有这行代码，双击 start_oauth_agent.bat 后 /computer use 不可用。
```

Add `"learning_agent.computer_use.mode_session"` and `"computer_use.mode_session"` to the existing allowed `ModuleNotFoundError` name sets in the same import block.

- [ ] **Step 4: Instantiate the mode store in `run_computer_terminal_command`**

Add after `persistent_grants` is created:

```python
    mode_sessions = ComputerUseModeSessionStore(base_dir=_computer_lock_root(Path(workspace)).parent / "mode_sessions")  # 新增代码+Phase98UniversalComputerUseMode：打开同一 workspace 的 mode session store；如果没有这行代码，/computer use 状态会和其它 Computer Use 状态分裂。
```

- [ ] **Step 5: Add `/computer use` command branches**

Add before the existing `status` branch:

```python
    if subcommand == "use":  # 新增代码+Phase98UniversalComputerUseMode：识别 /computer use 模式命令；如果没有这行代码，用户无法开启通用 Computer Use 模式。
        raw_mode_args = command_parts[2].strip() if len(command_parts) >= 3 else ""  # 新增代码+Phase98UniversalComputerUseMode：读取 use 后面的参数；如果没有这行代码，--observe/--full 无法识别。
        if raw_mode_args.startswith("--full-confirm"):  # 新增代码+Phase98UniversalComputerUseMode：识别 full 二次确认命令；如果没有这行代码，full 只能请求不能激活。
            confirm_token = raw_mode_args.split(maxsplit=1)[1].strip() if len(raw_mode_args.split(maxsplit=1)) == 2 else ""  # 新增代码+Phase98UniversalComputerUseMode：读取确认 token；如果没有这行代码，无法验证用户二次确认。
            confirm_result = mode_sessions.confirm_full_mode(confirm_token, reason="terminal full mode confirmation")  # 新增代码+Phase98UniversalComputerUseMode：确认 full mode；如果没有这行代码，确认命令不会改变状态。
            return _format_computer_mode_result(confirm_result)  # 新增代码+Phase98UniversalComputerUseMode：返回模式结果面板；如果没有这行代码，终端看不到 full 是否打开。
        if "--full" in raw_mode_args:  # 新增代码+Phase98UniversalComputerUseMode：识别 full 请求；如果没有这行代码，用户无法进入高风险候选路径。
            full_request = mode_sessions.request_full_mode(reason="terminal full mode request")  # 新增代码+Phase98UniversalComputerUseMode：生成 full 确认 token；如果没有这行代码，强确认无法执行。
            return _format_computer_full_request(full_request)  # 新增代码+Phase98UniversalComputerUseMode：返回 full 风险提示；如果没有这行代码，用户看不到确认命令。
        selected_mode = "observe" if "--observe" in raw_mode_args else "normal"  # 新增代码+Phase98UniversalComputerUseMode：选择 observe 或 normal；如果没有这行代码，--observe 会被当成 normal。
        open_result = mode_sessions.open_mode(mode=selected_mode, reason=f"terminal /computer use {selected_mode}")  # 新增代码+Phase98UniversalComputerUseMode：打开模式 session；如果没有这行代码，/computer use 只是文字提示。
        return _format_computer_mode_result(open_result)  # 新增代码+Phase98UniversalComputerUseMode：返回稳定模式面板；如果没有这行代码，验收器无法匹配 token。
```

Add format helpers near existing `_format_phase60_*` helpers:

```python
def _format_computer_mode_result(result: dict[str, Any]) -> str:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，格式化 /computer use 结果；如果没有这段函数，终端输出会散落在分支里。
    return "\n".join(["Computer Use Mode", f"- marker={result.get('marker', '')}", f"- ok_token={result.get('ok_token', '')}", f"- opened={str(bool(result.get('opened', False))).lower()}", f"- mode={result.get('mode', '')}", f"- full_mode={str(bool(result.get('full_mode', False))).lower()}", f"- ttl_seconds={result.get('ttl_seconds', 0)}", f"- per_app_allowlist_required={str(bool(result.get('per_app_allowlist_required', False))).lower()}", f"- ordinary_apps_allowed_by_risk_policy={str(bool(result.get('ordinary_apps_allowed_by_risk_policy', False))).lower()}", f"- real_desktop_touched=false", f"- low_level_event_count=0", f"- allowed_action_classes={','.join(result.get('allowed_action_classes', [])) if isinstance(result.get('allowed_action_classes', []), list) else ''}"]) + "\n"  # 新增代码+Phase98UniversalComputerUseMode：返回稳定多行面板；如果没有这行代码，真实终端验收难以断言。


def _format_computer_full_request(result: dict[str, Any]) -> str:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，格式化 full 请求提示；如果没有这段函数，用户无法清楚看到风险确认。
    token = str(result.get("confirmation_token", ""))  # 新增代码+Phase98UniversalComputerUseMode：读取确认 token；如果没有这行代码，确认命令无法显示。
    return "\n".join(["Computer Use Full Request", f"- marker={result.get('marker', '')}", "- opened=false", "- full_mode=false", f"- strong_confirmation_required={str(bool(result.get('strong_confirmation_required', False))).lower()}", "- ttl_seconds=300", "- risk=high", f"- confirm_command=/computer use --full-confirm {token}", "- real_desktop_touched=false", "- low_level_event_count=0"]) + "\n"  # 新增代码+Phase98UniversalComputerUseMode：返回 full 风险面板；如果没有这行代码，full 可能被误解为已开启。
```

- [ ] **Step 6: Add `/computer stop` and `/computer permissions`**

Add before the existing `abort` branch:

```python
    if subcommand == "stop":  # 新增代码+Phase98UniversalComputerUseMode：识别 /computer stop；如果没有这行代码，用户没有直观急停入口。
        stop_result = mode_sessions.stop(reason="terminal /computer stop")  # 新增代码+Phase98UniversalComputerUseMode：停止 mode session；如果没有这行代码，后续动作不会被 mode 阻断。
        abort_result = runtime.request_global_abort("terminal /computer stop", source="terminal")  # 新增代码+Phase98UniversalComputerUseMode：同步写入现有 abort；如果没有这行代码，旧低层门禁可能不知道 stop。
        return _format_computer_lock_action("stop", {"status": abort_result.get("status", {})}) + _format_computer_mode_result(dict(stop_result, mode="stopped", opened=False, full_mode=False, ttl_seconds=0, per_app_allowlist_required=False, ordinary_apps_allowed_by_risk_policy=False, allowed_action_classes=[]))  # 新增代码+Phase98UniversalComputerUseMode：同时返回旧锁和新模式结果；如果没有这行代码，用户看不到两个门禁都已停止。
    if subcommand == "permissions":  # 新增代码+Phase98UniversalComputerUseMode：识别权限查看命令；如果没有这行代码，用户无法查看当前模式动作边界。
        permissions = mode_sessions.permissions()  # 新增代码+Phase98UniversalComputerUseMode：读取权限摘要；如果没有这行代码，命令没有事实来源。
        return "\n".join(["Computer Use Permissions", f"- marker={permissions.get('marker', '')}", f"- mode={permissions.get('mode', '')}", f"- full_mode={str(bool(permissions.get('full_mode', False))).lower()}", f"- per_app_allowlist_required={str(bool(permissions.get('per_app_allowlist_required', False))).lower()}", f"- high_risk_requires_confirmation={str(bool(permissions.get('high_risk_requires_confirmation', False))).lower()}", f"- dangerous_target_terms_hidden={str(bool(permissions.get('dangerous_target_terms_hidden', False))).lower()}", f"- allowed_action_classes={','.join(permissions.get('allowed_action_classes', [])) if isinstance(permissions.get('allowed_action_classes', []), list) else ''}"]) + "\n"  # 新增代码+Phase98UniversalComputerUseMode：返回稳定权限面板；如果没有这行代码，验收器无法证明权限范围。
```

- [ ] **Step 7: Include mode session in `/computer status` snapshot**

Modify the status snapshot:

```python
        status_snapshot = {"lock": lock_manager.status(), "computer_use_mode": mode_sessions.status(), "approval": approval_model.status(), "runtime": runtime.status(), "recovery": runtime.action_journal(limit=3), "terminal_grants": terminal_grants.status(), "persistent_grants": persistent_grants.status(DEFAULT_SESSION_CONTEXT_ID), "abort_streaming_hooks": abort_streaming_hooks.status(), "high_level_tools": high_level_tools.status(), "controller_takeover": controller_takeover.status(), "session_context": session_context_store.status(DEFAULT_SESSION_CONTEXT_ID), "capability_matrix": capability_report["matrix"]}  # 修改代码+Phase98UniversalComputerUseMode：把 mode session 加入 /computer status 快照；如果没有这行代码，状态页看不到 /computer use 是否开启。
```

- [ ] **Step 8: Render mode session in `computer_status_renderer.py`**

Inside `render_computer_status`, read and render the mode:

```python
    computer_use_mode = _as_dict(snapshot.get("computer_use_mode", {}))  # 新增代码+Phase98UniversalComputerUseMode：读取 Computer Use 模式状态；如果没有这行代码，状态页无法显示 /computer use。
    lines.append(f"- mode={computer_use_mode.get('mode', 'off')} full:{_bool_token(computer_use_mode.get('full_mode'))} ttl:{computer_use_mode.get('ttl_seconds', 0)} per_app_allowlist_required:{_bool_token(computer_use_mode.get('per_app_allowlist_required'))}")  # 新增代码+Phase98UniversalComputerUseMode：在摘要区显示模式和白名单边界；如果没有这行代码，用户看不出新架构生效。
    lines.append(f"- mode_actions={','.join(_as_list(computer_use_mode.get('allowed_action_classes', [])))}")  # 新增代码+Phase98UniversalComputerUseMode：显示允许动作类别；如果没有这行代码，用户不知道当前能做什么。
```

Add command hints:

```python
    lines.append("- risk=medium command=/computer use : open normal universal Computer Use mode")  # 新增代码+Phase98UniversalComputerUseMode：展示普通通用模式命令；如果没有这行代码，用户不知道新入口。
    lines.append("- risk=low command=/computer use --observe : open observe-only mode with zero low-level events")  # 新增代码+Phase98UniversalComputerUseMode：展示只观察命令；如果没有这行代码，用户不知道安全预览模式。
    lines.append("- risk=high command=/computer use --full : request full takeover confirmation token")  # 新增代码+Phase98UniversalComputerUseMode：展示 full 请求命令；如果没有这行代码，用户不知道高风险入口需要确认。
    lines.append("- risk=medium command=/computer stop : stop mode session and request abort")  # 新增代码+Phase98UniversalComputerUseMode：展示 stop 命令；如果没有这行代码，急停入口不够直观。
    lines.append("- risk=low command=/computer permissions : show allowed action classes")  # 新增代码+Phase98UniversalComputerUseMode：展示权限查看命令；如果没有这行代码，用户不知道如何查看边界。
```

- [ ] **Step 9: Run command and status tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_mode_session_phase98 learning_agent.tests.test_windows_computer_use_mode_commands_phase98
```

Expected:

```text
Ran 9 tests
OK
```

- [ ] **Step 10: Commit terminal wiring**

Run:

```powershell
git add learning_agent/app/interactive.py learning_agent/app/computer_status_renderer.py learning_agent/tests/test_windows_computer_use_mode_commands_phase98.py
git commit -m "feat: wire universal computer use mode commands"
```

---

### Task 4: Phase99 Mode-Aware Live Execution Gate

**Files:**
- Create: `learning_agent/tests/test_windows_computer_use_mode_gate_phase99.py`
- Modify: `learning_agent/computer_use/real_app_safety_boundary.py`
- Modify: `learning_agent/computer_use/universal_live_execution.py`
- Test: `learning_agent/tests/test_windows_computer_use_mode_gate_phase99.py`

- [ ] **Step 1: Write failing gate tests**

Create tests that prove normal mode replaces ordinary app allowlists:

```python
import tempfile  # 新增代码+Phase99UniversalComputerUseModeGate：导入临时目录隔离 mode 和 gate 状态；如果没有这行代码，测试会污染真实 memory。
import unittest  # 新增代码+Phase99UniversalComputerUseModeGate：导入 unittest；如果没有这行代码，标准测试命令无法发现本文件。
from pathlib import Path  # 新增代码+Phase99UniversalComputerUseModeGate：导入 Path 管理临时目录；如果没有这行代码，Windows 路径处理会脆弱。

from learning_agent.computer_use.mode_session import ComputerUseModeSessionStore  # 新增代码+Phase99UniversalComputerUseModeGate：导入 mode session；如果没有这行代码，gate 测试无法打开 normal mode。
from learning_agent.computer_use.real_app_safety_boundary import WindowsRealAppSafetyBoundary  # 修改代码+Phase99UniversalComputerUseModeGate：导入安全边界；如果没有这行代码，无法验证模式授权是否接入真实边界。


class ComputerUseModeGatePhase99Tests(unittest.TestCase):  # 新增代码+Phase99UniversalComputerUseModeGate：类段开始，验证 mode-aware gate；如果没有这个类，普通应用免白名单路径没有保护。
    def test_normal_mode_allows_ordinary_app_without_per_app_grant(self) -> None:  # 新增代码+Phase99UniversalComputerUseModeGate：函数段开始，验证普通应用无需 app grant；如果没有这段测试，系统可能继续依赖白名单。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase99UniversalComputerUseModeGate：创建隔离目录；如果没有这行代码，mode 状态会污染其它测试。
            mode_store = ComputerUseModeSessionStore(base_dir=Path(temp_dir) / "mode")  # 新增代码+Phase99UniversalComputerUseModeGate：创建 mode store；如果没有这行代码，无法打开 normal mode。
            mode_store.open_mode(mode="normal", reason="普通通用控制")  # 新增代码+Phase99UniversalComputerUseModeGate：打开 normal mode；如果没有这行代码，安全边界没有模式授权。
            boundary = WindowsRealAppSafetyBoundary()  # 新增代码+Phase99UniversalComputerUseModeGate：创建安全边界；如果没有这行代码，无法评估目标风险。
            window = {"app_id": "generic_editor.exe", "process_name": "generic_editor.exe", "window_id": "hwnd:9901", "title_preview": "Generic Editor"}  # 新增代码+Phase99UniversalComputerUseModeGate：构造普通应用窗口；如果没有这行代码，测试目标不明确。
            decision = boundary.evaluate_with_mode_session(window, "click", mode_store, "phase99-test")  # 新增代码+Phase99UniversalComputerUseModeGate：用 mode session 评估点击；如果没有这行代码，无法证明免 app grant 路径。
        self.assertTrue(decision["allowed"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言普通目标放行；如果没有这行代码，normal mode 没有实际意义。
        self.assertEqual(decision["decision"], "allowed_by_computer_use_mode")  # 新增代码+Phase99UniversalComputerUseModeGate：断言原因码；如果没有这行代码，路径可能仍是 app grant。
        self.assertFalse(decision["per_app_allowlist_required"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言不需要 app 白名单；如果没有这行代码，核心架构可能倒退。

    def test_normal_mode_blocks_terminal_target(self) -> None:  # 新增代码+Phase99UniversalComputerUseModeGate：函数段开始，验证危险目标仍拒绝；如果没有这段测试，normal mode 可能变成裸权限。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase99UniversalComputerUseModeGate：创建隔离目录；如果没有这行代码，测试状态会污染真实目录。
            mode_store = ComputerUseModeSessionStore(base_dir=Path(temp_dir) / "mode")  # 新增代码+Phase99UniversalComputerUseModeGate：创建 mode store；如果没有这行代码，无法打开 normal mode。
            mode_store.open_mode(mode="normal", reason="普通通用控制")  # 新增代码+Phase99UniversalComputerUseModeGate：打开 normal mode；如果没有这行代码，危险目标拒绝路径没有上下文。
            boundary = WindowsRealAppSafetyBoundary()  # 新增代码+Phase99UniversalComputerUseModeGate：创建安全边界；如果没有这行代码，无法评估危险目标。
            window = {"app_id": "powershell.exe", "process_name": "powershell.exe", "window_id": "hwnd:9902", "title_preview": "Windows PowerShell"}  # 新增代码+Phase99UniversalComputerUseModeGate：构造终端窗口；如果没有这行代码，危险样本不明确。
            decision = boundary.evaluate_with_mode_session(window, "click", mode_store, "phase99-test")  # 新增代码+Phase99UniversalComputerUseModeGate：评估危险目标；如果没有这行代码，拒绝路径没有证据。
        self.assertFalse(decision["allowed"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言拒绝；如果没有这行代码，危险窗口可能被放行。
        self.assertEqual(decision["decision"], "dangerous_target_blocked")  # 新增代码+Phase99UniversalComputerUseModeGate：断言原因码；如果没有这行代码，安全边界不可审计。
        self.assertEqual(decision["low_level_event_count"], 0)  # 新增代码+Phase99UniversalComputerUseModeGate：断言零事件；如果没有这行代码，拒绝后可能仍发送输入。

    def test_observe_mode_blocks_click(self) -> None:  # 新增代码+Phase99UniversalComputerUseModeGate：函数段开始，验证 observe 不允许点击；如果没有这段测试，observe 可能绕过写动作限制。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase99UniversalComputerUseModeGate：创建隔离目录；如果没有这行代码，状态不隔离。
            mode_store = ComputerUseModeSessionStore(base_dir=Path(temp_dir) / "mode")  # 新增代码+Phase99UniversalComputerUseModeGate：创建 mode store；如果没有这行代码，无法打开 observe。
            mode_store.open_mode(mode="observe", reason="只观察")  # 新增代码+Phase99UniversalComputerUseModeGate：打开 observe；如果没有这行代码，权限判断没有 observe 状态。
            boundary = WindowsRealAppSafetyBoundary()  # 新增代码+Phase99UniversalComputerUseModeGate：创建安全边界；如果没有这行代码，无法评估动作。
            decision = boundary.evaluate_with_mode_session({"process_name": "notepad.exe"}, "click", mode_store, "phase99-test")  # 新增代码+Phase99UniversalComputerUseModeGate：评估点击；如果没有这行代码，observe 拒绝没有证据。
        self.assertFalse(decision["allowed"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言点击被拒绝；如果没有这行代码，observe 会误控桌面。
        self.assertEqual(decision["decision"], "action_risk_exceeds_mode")  # 新增代码+Phase99UniversalComputerUseModeGate：断言原因码；如果没有这行代码，拒绝原因不稳定。


if __name__ == "__main__":  # 新增代码+Phase99UniversalComputerUseModeGate：文件入口段开始；如果没有这行代码，不能直接运行本测试。
    unittest.main()  # 新增代码+Phase99UniversalComputerUseModeGate：启动 unittest；如果没有这行代码，直接运行没有测试。
```

- [ ] **Step 2: Run the red gate tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_mode_gate_phase99
```

Expected:

```text
AttributeError: 'WindowsRealAppSafetyBoundary' object has no attribute 'evaluate_with_mode_session'
```

- [ ] **Step 3: Add mode-aware evaluation to `real_app_safety_boundary.py`**

Add import fallback for `ComputerUseModeSessionStore`, then add this method inside `WindowsRealAppSafetyBoundary`:

```python
    def evaluate_with_mode_session(self, window: dict[str, Any], action: str, mode_store: Any, session_id: str) -> dict[str, Any]:  # 新增代码+Phase99UniversalComputerUseModeGate：函数段开始，用通用模式评估动作；如果没有这段函数，normal mode 无法替代普通 app 白名单。
        mode_decision = mode_store.evaluate_action(window, action)  # 新增代码+Phase99UniversalComputerUseModeGate：先读取 mode session 决策；如果没有这行代码，执行门不知道 /computer use 是否开启。
        if not bool(mode_decision.get("allowed", False)):  # 新增代码+Phase99UniversalComputerUseModeGate：检查模式是否拒绝；如果没有这行代码，observe/stop/expired/危险目标可能被绕过。
            return dict(mode_decision, safety_boundary_model=PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL, session_id=session_id)  # 修改代码+Phase99UniversalComputerUseModeGate：返回零事件拒绝并保留安全边界标记；如果没有这行代码，调用方无法审计来源。
        return dict(mode_decision, allowed=True, decision="allowed_by_computer_use_mode", safety_boundary_model=PHASE72_REAL_APP_SAFETY_BOUNDARY_MODEL, session_id=session_id, ready_for_low_level_send=True)  # 新增代码+Phase99UniversalComputerUseModeGate：返回模式授权允许；如果没有这行代码，普通应用仍需要 per-app grant。
```

This method intentionally checks dangerous targets through `mode_store.evaluate_action(...)` before returning allowed. It must not call `persistent_grants.approve(...)` to fake a per-app allowlist.

- [ ] **Step 4: Wire mode session into `UniversalWindowsLiveExecutionGate`**

Modify `UniversalWindowsLiveExecutionGate.__init__` to accept `mode_store: Any | None = None` and default it to `ComputerUseModeSessionStore(...)`.

Modify `_Phase93ClosedLoopActor` to use `safety_boundary.evaluate_with_mode_session(...)` when `request_real_actions=True` and a mode store is present.

The action report must include:

```python
"mode_session_used": True  # 新增代码+Phase99UniversalComputerUseModeGate：标记本次通过 mode session 评估；如果没有这行代码，验收无法证明不是 app 白名单。
"per_app_allowlist_required": False  # 新增代码+Phase99UniversalComputerUseModeGate：标记不需要应用白名单；如果没有这行代码，用户纠偏点无法从报告看到。
"ordinary_apps_allowed_by_risk_policy": True  # 新增代码+Phase99UniversalComputerUseModeGate：标记普通应用走风险策略；如果没有这行代码，报告无法解释 normal mode 的放行原因。
```

- [ ] **Step 5: Run Phase98 and Phase99 tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_mode_session_phase98 learning_agent.tests.test_windows_computer_use_mode_commands_phase98 learning_agent.tests.test_windows_computer_use_mode_gate_phase99
```

Expected:

```text
OK
```

- [ ] **Step 6: Commit Phase99 gate**

Run:

```powershell
git add learning_agent/computer_use/real_app_safety_boundary.py learning_agent/computer_use/universal_live_execution.py learning_agent/tests/test_windows_computer_use_mode_gate_phase99.py
git commit -m "feat: connect universal computer use mode to live gate"
```

---

### Task 5: Phase100 Full Mode Confirmation And Safety Tests

**Files:**
- Modify: `learning_agent/tests/test_windows_computer_use_mode_session_phase98.py`
- Modify: `learning_agent/tests/test_windows_computer_use_mode_commands_phase98.py`
- Modify: `learning_agent/computer_use/mode_session.py`
- Modify: `learning_agent/app/interactive.py`

- [ ] **Step 1: Expand tests for invalid and expired full confirmations**

Add tests for:

- Wrong token returns `full_mode_confirmation_token_mismatch`.
- Expired token returns `full_mode_confirmation_expired`.
- Confirmed full mode has `ttl_seconds <= 300`.
- Full mode still blocks `password`, `token`, `private key`, and `captcha` target text through dangerous target checks.

Use the existing `ComputerUseModeSessionStore(now_func=...)` injection to simulate expiration.

- [ ] **Step 2: Ensure command output warns before full activation**

The `/computer use --full` output must include:

```text
Computer Use Full Request
- opened=false
- full_mode=false
- strong_confirmation_required=true
- risk=high
- confirm_command=/computer use --full-confirm FULL-...
- low_level_event_count=0
```

The `/computer use --full-confirm <token>` output must include:

```text
Computer Use Mode
- opened=true
- mode=full
- full_mode=true
- ttl_seconds=
- per_app_allowlist_required=false
```

- [ ] **Step 3: Run full mode tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_mode_session_phase98 learning_agent.tests.test_windows_computer_use_mode_commands_phase98
```

Expected:

```text
OK
```

- [ ] **Step 4: Commit Phase100**

Run:

```powershell
git add learning_agent/computer_use/mode_session.py learning_agent/app/interactive.py learning_agent/tests/test_windows_computer_use_mode_session_phase98.py learning_agent/tests/test_windows_computer_use_mode_commands_phase98.py
git commit -m "feat: require confirmation for full computer use mode"
```

---

### Task 6: Phase101 Visible-Terminal Acceptance Scenario

**Files:**
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase101_universal_computer_use_permission_mode.json`
- Test: `learning_agent/acceptance_controller/controller.ps1`
- Test: `learning_agent/acceptance/verifier.py`

- [ ] **Step 1: Add scenario JSON**

Create a scenario that sends these prompts to `start_oauth_agent.bat`:

```text
/computer use
/computer status
/computer permissions
请打开 computer use，确认当前是通用普通控制模式，不要调用 Notepad 专用控制器，只输出 Phase101 合同检查结果。
/computer stop
/computer status
```

The scenario must assert these text fragments:

```text
Computer Use Mode
mode=normal
per_app_allowlist_required=false
ordinary_apps_allowed_by_risk_policy=true
Computer Use Permissions
high_risk_requires_confirmation=true
mode=stopped
```

- [ ] **Step 2: Validate scenario JSON**

Run:

```powershell
python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_phase101_universal_computer_use_permission_mode.json > $null
```

Expected:

```text
exit code 0
```

- [ ] **Step 3: Run real visible terminal acceptance**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath 'H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\agent_capability_phase101_universal_computer_use_permission_mode.json'
```

Expected:

```text
ACCEPTANCE_CONTROLLER_COMPLETED=True
RESULT_JSON=H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_phase101_universal_computer_use_permission_mode-...\result.json
```

- [ ] **Step 4: Run independent verifier**

Run with the actual run directory from Step 3:

```powershell
python -m learning_agent.acceptance.verifier "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_phase101_universal_computer_use_permission_mode-YYYYMMDD_HHMMSS" "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\agent_capability_phase101_universal_computer_use_permission_mode.json"
```

Expected:

```text
completed: true
assertion.passed: true
permission_sent_count: 0
```

- [ ] **Step 5: Commit Phase101**

Run:

```powershell
git add learning_agent/acceptance_controller/scenarios/agent_capability_phase101_universal_computer_use_permission_mode.json
git commit -m "test: add universal computer use mode acceptance"
```

---

### Task 7: Regression, Memory, And Learning Backup

**Files:**
- Modify: `agent_memory/context.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`
- Create: `learning_agent/test/universal_computer_use_permission_mode_20260605/`

- [ ] **Step 1: Run focused regression**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_mode_session_phase98 learning_agent.tests.test_windows_computer_use_mode_commands_phase98 learning_agent.tests.test_windows_computer_use_mode_gate_phase99 learning_agent.tests.test_windows_computer_use_universal_mode_phase92 learning_agent.tests.test_windows_computer_use_universal_live_execution_phase93
```

Expected:

```text
OK
```

- [ ] **Step 2: Run Computer Use discovery regression**

Run:

```powershell
python -m unittest discover -s learning_agent\tests -p "test_windows_computer_use_*.py"
```

Expected:

```text
OK
```

The exact test count may grow. Record the final count in `agent_memory/progress.md`.

- [ ] **Step 3: Run compile check**

Run:

```powershell
python -m compileall -q learning_agent\computer_use learning_agent\app learning_agent\tests learning_agent\acceptance_controller
```

Expected:

```text
exit code 0
```

- [ ] **Step 4: Update memory files**

Append a concise Phase98-101 summary:

- `agent_memory/context.md`: record the new mode session architecture and command set.
- `agent_memory/progress.md`: record completed tests, compile checks, and visible terminal run directory.
- `agent_memory/bugs.md`: record resolved risks and remaining risks around full mode, dangerous targets, and real physical dispatch.

- [ ] **Step 5: Create learning backup**

Run:

```powershell
$backup = 'H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\test\universal_computer_use_permission_mode_20260605'
New-Item -ItemType Directory -Force -Path $backup | Out-Null
Copy-Item -LiteralPath 'H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use\mode_session.py' -Destination (Join-Path $backup 'mode_session.py') -Force
Copy-Item -LiteralPath 'H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\interactive.py' -Destination (Join-Path $backup 'interactive.py') -Force
Copy-Item -LiteralPath 'H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\computer_status_renderer.py' -Destination (Join-Path $backup 'computer_status_renderer.py') -Force
Copy-Item -LiteralPath 'H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use\real_app_safety_boundary.py' -Destination (Join-Path $backup 'real_app_safety_boundary.py') -Force
Copy-Item -LiteralPath 'H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use\universal_live_execution.py' -Destination (Join-Path $backup 'universal_live_execution.py') -Force
Copy-Item -LiteralPath 'H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_windows_computer_use_mode_session_phase98.py' -Destination (Join-Path $backup 'test_windows_computer_use_mode_session_phase98.py') -Force
Copy-Item -LiteralPath 'H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_windows_computer_use_mode_commands_phase98.py' -Destination (Join-Path $backup 'test_windows_computer_use_mode_commands_phase98.py') -Force
Copy-Item -LiteralPath 'H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_windows_computer_use_mode_gate_phase99.py' -Destination (Join-Path $backup 'test_windows_computer_use_mode_gate_phase99.py') -Force
Copy-Item -LiteralPath 'H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\agent_capability_phase101_universal_computer_use_permission_mode.json' -Destination (Join-Path $backup 'agent_capability_phase101_universal_computer_use_permission_mode.json') -Force
Copy-Item -LiteralPath 'H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\context.md' -Destination (Join-Path $backup 'agent_memory_context.md') -Force
Copy-Item -LiteralPath 'H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\progress.md' -Destination (Join-Path $backup 'agent_memory_progress.md') -Force
Copy-Item -LiteralPath 'H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\bugs.md' -Destination (Join-Path $backup 'agent_memory_bugs.md') -Force
```

- [ ] **Step 6: Commit memory and backup**

Run:

```powershell
git add agent_memory/context.md agent_memory/progress.md agent_memory/bugs.md learning_agent/test/universal_computer_use_permission_mode_20260605
git commit -m "docs: record universal computer use mode progress"
```

---

## Final Verification Gate

Before saying the implementation is complete, all of these must be true:

- Focused Phase98-101 tests pass.
- Phase92 and Phase93 regressions pass.
- Computer Use discovery regression passes.
- Compile check passes.
- Scenario JSON validates.
- `learning_agent/start_oauth_agent.bat` visible terminal acceptance passes through controller.
- Independent verifier reports `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.
- `learning_agent/test/universal_computer_use_permission_mode_20260605/` contains the modified code, tests, scenario, and memory files.

If the visible terminal cannot be opened, observed, and interacted with, the final answer must say:

```text
真实可见终端交互验收未完成，不能声明开发完成。
```

---

## Execution Recommendation

Use subagent-driven execution for this plan. Task 1-2, Task 3, Task 4-5, and Task 6-7 are separable enough to review between checkpoints, and the final visible-terminal gate should remain in the main session so the final claim is based on directly observed acceptance evidence.
