# OpenHarness Desktop ChatGPT OAuth Real Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 OpenHarness Desktop 在用户没有 API key、只有 ChatGPT/OpenAI OAuth 登录能力时，也能通过真实认证得到真实模型回答，并且不再把 provider 连接成功误装成 `fake streaming`。

**Architecture:** 先走官方支持边界：用 `codex login` / `codex login status` 作为 V1A 的 ChatGPT OAuth 登录桥，主聊天通过现有 `CodexCliChatModel` 跑通真实回答。再做 V1B，把 provider catalog、GUI bridge、real adapter、可见证据包打通。最后做 V1C，将 OpenCode-style PKCE + localhost callback + Codex backend route 作为显式 experimental direct OAuth，不把 OpenCode 内部实现当稳定产品契约。

**Tech Stack:** Python stdlib `subprocess` / `threading` / `pathlib` / `json` / `urllib`，现有 `learning_agent.models.adapters.CodexCliChatModel` 和 `CodexOAuthChatModel`，现有 `learning_agent.app.gui_bridge` HTTP bridge，React + TypeScript + Electron renderer，pytest + Vitest + Electron 可见 GUI 验收，Windows DPAPI 仅用于 V1C experimental direct OAuth token store。

---

## 0. 评估后升级结论

这份蓝图已按 `2026-06-26-openharness-desktop-chatgpt-oauth-real-model-v1-karpathy-review.md` 升级。

升级后的核心变化：

- 把路线拆成 `V1A / V1B / V1C` 三层，不再一口气把官方登录、OpenCode 直连、内部 backend route 混成一个主路径。
- V1A 优先使用官方 `codex login`。官方文档说明：`codex login` 可用 ChatGPT account、API key 或 access token 认证；无参数时会打开浏览器走 ChatGPT OAuth flow；`codex login status` 在已有凭据时退出码为 `0`。
- OpenCode 的 `app_EMoamEEZ73f0CkXaXp7hrann`、`localhost:1455/auth/callback`、`https://chatgpt.com/backend-api/codex/responses` 只作为源码研究依据，不能作为 OpenHarness 默认稳定契约。
- V1C direct OAuth 必须显式 experimental，并且需要 OpenHarness 自有 OAuth client id 或明确的本地实验配置。
- 增加 port 冲突、token 生命周期、真实 adapter cancel/streaming、证据包、secret leak gate 等 tail behavior。

---

## 1. 已读取的依据

### 1.1 OpenCode 源码依据

已读取 `D:\opencode` 的 CodeGraph 和源码，重点文件：

- `D:\opencode\packages\opencode\src\plugin\openai\codex.ts`
- `D:\opencode\packages\core\src\plugin\provider\openai.ts`
- `D:\opencode\packages\opencode\src\provider\auth.ts`
- `D:\opencode\packages\schema\src\credential.ts`
- `D:\opencode\packages\opencode\src\auth\index.ts`
- `D:\opencode\packages\app\src\components\dialog-connect-provider.tsx`

OpenCode 观察事实：

- browser OAuth 使用 PKCE：`code_verifier`、`code_challenge`、`state`。
- callback 使用 `http://localhost:1455/auth/callback`。
- 授权 URL 使用 `codex_cli_simplified_flow=true` 和 `originator=opencode`。
- token exchange 使用 `https://auth.openai.com/oauth/token`。
- 真实模型请求走 `https://chatgpt.com/backend-api/codex/responses`。
- renderer 不直接拿 token，UI 只显示授权状态。

产品原则：

- OpenCode 源码能说明“OpenCode 是这么做的”。
- OpenCode 源码不能证明“OpenHarness 可以长期依赖同一 client id 和 internal backend route”。

### 1.2 OpenAI 官方依据

已核对官方 Codex CLI 文档：

- `codex login` 支持 ChatGPT account、API key、access token。
- 无参数时会打开浏览器走 ChatGPT OAuth flow。
- `codex login status` 在 credentials 存在时退出码为 `0`。

官方路径结论：

- V1A 应优先桥接 `codex login`，不读取、不复制、不解析 Codex auth token。
- V1A 的目标是证明“用户通过 ChatGPT OAuth 登录后，OpenHarness Desktop GUI 能真实回答”。

### 1.3 OpenHarness 当前实现依据

已读取当前项目关键文件：

- `learning_agent/app/gui_provider_settings.py`
- `learning_agent/app/gui_provider_auth_attempts.py`
- `learning_agent/app/gui_provider_openai_auth_config.py`
- `learning_agent/app/gui_agent_adapter.py`
- `learning_agent/app/gui_bridge.py`
- `learning_agent/models/adapters.py`
- `apps/desktop/src/components/settings/ProviderConnectDialog.tsx`
- `apps/desktop/src/components/settings/SettingsDialog.tsx`
- `apps/desktop/src/api/guiClient.ts`

当前事实：

- Provider 设置页已有 OpenAI 三种入口：`chatgpt-browser`、`chatgpt-headless`、`api-key`。
- browser/headless 当前只是 mock auth-attempt，完成后保存 `oauth_mock`。
- 主聊天默认仍走 `FakeStreamingGuiAgentAdapter`。
- 已存在 `CodexCliChatModel`，可通过 Codex CLI 跑真实模型。
- 已存在 `CodexOAuthChatModel`，但直连 OAuth 尚未接入 Desktop provider auth 和 GUI adapter。

---

## 2. Release Split

### V1A: Official Codex Login Bridge

目标：

- 不自研 OAuth。
- 不碰 raw token。
- 使用官方 `codex login` 和 `codex login status`。
- provider 设置页能显示 ChatGPT/Codex 登录状态。
- GUI 主聊天能通过 `CodexCliChatModel` 得到真实回答。

完成标准：

- 用户点击 OpenAI browser 登录后，系统打开官方 Codex ChatGPT OAuth 登录流程。
- `codex login status` 成功后 provider 显示 connected。
- 用户在 OpenHarness Desktop 主聊天输入问题，回答不包含 `fake streaming`。
- 没有读取 `~/.codex/auth.json`，没有把 token 写入 OpenHarness workspace。

### V1B: Provider-Aware Real Adapter

目标：

- provider 状态和 GUI real adapter 联动。
- adapter 合同覆盖真实回答、远端失败、cancel、fake fallback forbidden。
- 可见 GUI 验收生成证据包。

完成标准：

- 已登录时自动走 real adapter。
- 未登录时显示 `real_model_not_connected`。
- 真实模型失败时不回退 fake。
- 证据包包含登录状态截图、provider connected 截图、真实回答截图、事件流截图、acceptance JSON。

### V1C: Experimental Direct OAuth

目标：

- 在 V1A/V1B 之后实现 OpenCode-style direct OAuth。
- 仅作为 experimental backend。
- 使用 OpenHarness 自有 OAuth client id 或明确的本地实验 client id。
- token store、redaction、port preflight、callback tail tests 先于 token exchange。

完成标准：

- 默认关闭。
- 没有安全 token store 时禁止启用。
- port 1455 冲突时给出可读错误。
- direct OAuth 成功后可通过 `CodexOAuthChatModel` 真实回答。

---

## 3. 安全和产品原则

- `OpenCode client id` 只作为源码研究依据，不能作为 OpenHarness 默认生产 client id。
- `chatgpt.com/backend-api/codex/responses` 只在 V1C experimental direct OAuth 中使用。
- V1A 不读取 Codex auth cache 文件内容，只调用 `codex login status` 和 `codex exec`。
- renderer 永远不能收到 raw token。
- 真实模型失败不能回退 fake。
- provider connected 必须表示真实可用状态，不能把 mock connected 当真实 connected。
- 每个真实 GUI 验收必须留下证据包。
- 验收需要使用肉眼可见的真实 GUI 界面进行验收，验收时出现 bug 或发现 bug 时，请使用 `superpowers:systematic-debugging` 技能，修复 bug，并重新测试，测试通过后继续执行下一个任务。

---

## 4. 文件结构地图

### V1A 新增文件

- `learning_agent/app/gui_codex_auth_bridge.py`
  - 只负责调用 Codex CLI 登录状态和启动登录。
  - 不读取、不解析、不保存 Codex token。

- `learning_agent/tests/test_gui_codex_auth_bridge.py`
  - 覆盖 `codex login status`、未安装 Codex、登录进程启动、命令超时、输出脱敏。

- `learning_agent/tests/test_gui_real_model_adapter.py`
  - 覆盖 real adapter 使用 `CodexCliChatModel` 的事件合同。

### V1A 修改文件

- `learning_agent/app/gui_provider_settings.py`
  - OpenAI browser 方法在 official mode 下显示为 Codex ChatGPT login。
  - catalog 支持 `source="codex_cli"`。

- `learning_agent/app/gui_provider_auth_attempts.py`
  - `chatgpt-browser` 在 official mode 下启动 `codex login`。
  - status 通过 `codex login status` 判断。

- `learning_agent/app/gui_agent_adapter.py`
  - 新增或导入 `RealModelGuiAgentAdapter`。

- `learning_agent/app/gui_bridge.py`
  - 根据 provider 状态和 `OPENHARNESS_GUI_MODEL_MODE` 选择 real adapter。

- `apps/desktop/src/api/guiProviderTypes.ts`
  - 支持 auth attempt mode：`codex_cli_login`。

- `apps/desktop/src/components/settings/ProviderConnectDialog.tsx`
  - 等待页显示“浏览器中完成 Codex/ChatGPT 登录”。

- `apps/desktop/src/components/settings/SettingsDialog.tsx`
  - 轮询 official login 状态。

### V1B 新增或修改文件

- `learning_agent/test/provider_settings_v2_openai_connect/scripts/capture_real_codex_login_visual_qa.ps1`
  - 生成真实 GUI 验收证据包。

- `learning_agent/test/provider_settings_v2_openai_connect/scripts/assert_real_model_acceptance.ps1`
  - 检查 evidence JSON 中 `fake_text_detected=false` 和 `secret_leak_detected=false`。

### V1C 新增文件

- `learning_agent/app/gui_provider_oauth_token_store.py`
  - V1C direct OAuth token store。
  - Windows 使用 DPAPI。

- `learning_agent/app/gui_provider_openai_oauth.py`
  - V1C direct OAuth PKCE、callback server、token exchange、refresh。

- `learning_agent/tests/test_gui_provider_oauth_token_store.py`
  - 覆盖 token 生命周期和 redaction。

- `learning_agent/tests/test_gui_provider_openai_oauth.py`
  - 覆盖 PKCE、callback server、port 1455、token exchange、tail behavior。

---

## 5. V1A Task List: Official Codex Login Bridge

### Task 1: Codex CLI auth bridge contract

**Files:**

- Create: `learning_agent/tests/test_gui_codex_auth_bridge.py`
- Create: `learning_agent/app/gui_codex_auth_bridge.py`

- [ ] **Step 1: Write failing tests**

Add tests:

```python
from learning_agent.app.gui_codex_auth_bridge import CodexAuthBridge, CodexAuthStatus

def test_login_status_connected_when_codex_status_exits_zero():
    calls = []
    def runner(command, timeout_seconds):
        calls.append(command)
        return 0, "Logged in with ChatGPT", ""
    bridge = CodexAuthBridge(command="codex", runner=runner)
    status = bridge.login_status()
    assert status == CodexAuthStatus(available=True, connected=True, message="Logged in with ChatGPT")
    assert calls == [["codex", "login", "status"]]

def test_login_status_not_connected_when_codex_status_exits_nonzero():
    def runner(command, timeout_seconds):
        return 1, "", "not logged in"
    bridge = CodexAuthBridge(command="codex", runner=runner)
    status = bridge.login_status()
    assert status.available is True
    assert status.connected is False
    assert status.message == "not logged in"

def test_login_status_unavailable_when_codex_missing():
    def runner(command, timeout_seconds):
        raise FileNotFoundError("codex")
    bridge = CodexAuthBridge(command="codex", runner=runner)
    status = bridge.login_status()
    assert status.available is False
    assert status.connected is False
    assert status.message == "codex_cli_not_found"

def test_start_login_runs_codex_login_without_token_access():
    calls = []
    def starter(command):
        calls.append(command)
        return "process-started"
    bridge = CodexAuthBridge(command="codex", starter=starter)
    result = bridge.start_login()
    assert result["ok"] is True
    assert result["mode"] == "codex_cli_login"
    assert calls == [["codex", "login"]]
```

- [ ] **Step 2: Run red tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_codex_auth_bridge.py -q
```

Expected:

- Fails because `learning_agent.app.gui_codex_auth_bridge` does not exist.

- [ ] **Step 3: Implement minimal bridge**

Create `learning_agent/app/gui_codex_auth_bridge.py` with:

```python
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Callable

CommandRunner = Callable[[list[str], float], tuple[int, str, str]]
CommandStarter = Callable[[list[str]], object]

@dataclass(frozen=True)
class CodexAuthStatus:
    available: bool
    connected: bool
    message: str

def _default_runner(command: list[str], timeout_seconds: float) -> tuple[int, str, str]:
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds)
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()

def _default_starter(command: list[str]) -> object:
    return subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

class CodexAuthBridge:
    def __init__(self, command: str = "codex", runner: CommandRunner | None = None, starter: CommandStarter | None = None, timeout_seconds: float = 15.0) -> None:
        self.command = command
        self.runner = runner or _default_runner
        self.starter = starter or _default_starter
        self.timeout_seconds = timeout_seconds

    def login_status(self) -> CodexAuthStatus:
        try:
            code, stdout, stderr = self.runner([self.command, "login", "status"], self.timeout_seconds)
        except FileNotFoundError:
            return CodexAuthStatus(available=False, connected=False, message="codex_cli_not_found")
        except subprocess.TimeoutExpired:
            return CodexAuthStatus(available=True, connected=False, message="codex_login_status_timeout")
        message = stdout or stderr
        return CodexAuthStatus(available=True, connected=(code == 0), message=message)

    def start_login(self) -> dict[str, object]:
        try:
            self.starter([self.command, "login"])
        except FileNotFoundError:
            return {"ok": False, "mode": "codex_cli_login", "error_code": "codex_cli_not_found", "message": "Codex CLI was not found."}
        return {"ok": True, "mode": "codex_cli_login", "message": "Codex login started."}
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_codex_auth_bridge.py -q
```

Expected:

- `4 passed`.

### Task 2: Provider catalog shows official Codex login status

**Files:**

- Modify: `learning_agent/app/gui_provider_settings.py`
- Test: `learning_agent/tests/test_gui_provider_settings_contract.py`

- [ ] **Step 1: Add provider status tests**

Add tests that inject a fake `CodexAuthBridge`:

```python
def test_openai_provider_uses_codex_cli_source_when_codex_login_connected(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENHARNESS_OPENAI_AUTH_MODE", "codex_cli")
    monkeypatch.setenv("OPENHARNESS_GUI_MODEL_MODE", "real")
    payload = build_provider_settings_payload(tmp_path)
    openai = next(provider for provider in payload["providers"] if provider["id"] == "openai")
    assert openai["connected"] in {True, False}
    assert any(method["id"] == "chatgpt-browser" for method in openai["auth_methods"])
```

The exact fake injection method should follow the existing test style in `test_gui_provider_settings_contract.py`.

- [ ] **Step 2: Run red test**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_settings_contract.py -q
```

Expected:

- Fails until `codex_cli` mode is represented in catalog.

- [ ] **Step 3: Update catalog behavior**

Modify `_openai_auth_methods()` so `chatgpt-browser` help text says:

```text
使用官方 Codex CLI 打开 ChatGPT OAuth 登录；OpenHarness 不读取 Codex token。
```

Modify built-in provider catalog so when `OPENHARNESS_OPENAI_AUTH_MODE=codex_cli`:

- `source="codex_cli"` when status connected.
- `masked_key="Codex ChatGPT login"` when connected.
- `connected=false` and `source="codex_cli_missing"` when Codex CLI is unavailable.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/tests/test_gui_codex_auth_bridge.py -q
```

Expected:

- All tests pass.

### Task 3: Auth attempt starts official Codex login

**Files:**

- Modify: `learning_agent/app/gui_provider_auth_attempts.py`
- Test: `learning_agent/tests/test_gui_provider_auth_attempts_contract.py`

- [ ] **Step 1: Add official login attempt tests**

Add tests:

```python
def test_start_chatgpt_browser_in_codex_cli_mode_returns_codex_login_attempt(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENHARNESS_OPENAI_AUTH_MODE", "codex_cli")
    payload = start_provider_auth_attempt(tmp_path, "openai", "chatgpt-browser")
    attempt = payload["attempt"]
    assert attempt["mode"] == "codex_cli_login"
    assert attempt["provider_id"] == "openai"
    assert attempt["auth_method_id"] == "chatgpt-browser"
    assert attempt["status"] in {"pending", "complete", "failed"}
    assert "access_token" not in str(payload)
    assert "refresh_token" not in str(payload)
```

- [ ] **Step 2: Run red test**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_auth_attempts_contract.py -q
```

Expected:

- Fails because `codex_cli_login` mode is not implemented.

- [ ] **Step 3: Implement official mode branch**

In `start_provider_auth_attempt()`:

- Read `build_openai_auth_config().auth_mode`.
- If auth mode is `codex_cli` and method is `chatgpt-browser`, call `CodexAuthBridge.start_login()`.
- Return attempt payload with:
  - `mode="codex_cli_login"`
  - `url=""`
  - `display_code="Complete authorization in your browser. This window will close automatically."`
  - `display_code_kind="browser_instruction"`
  - `display_code_copyable=False`
  - `status="pending"` unless `codex login status` already connected.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_auth_attempts_contract.py learning_agent/tests/test_gui_codex_auth_bridge.py -q
```

Expected:

- All tests pass.

### Task 4: Frontend renders official Codex login attempt

**Files:**

- Modify: `apps/desktop/src/api/guiProviderTypes.ts`
- Modify: `apps/desktop/src/components/settings/ProviderConnectDialog.tsx`
- Modify: `apps/desktop/src/components/settings/SettingsDialog.tsx`
- Test: `apps/desktop/tests/settingsProvidersPanel.test.tsx`
- Test: `apps/desktop/tests/settingsDialogViewModel.test.ts`

- [ ] **Step 1: Add frontend tests**

Add assertions:

```typescript
expect(screen.getByText(/连接 OpenAI/)).toBeTruthy();
expect(screen.getByText(/等待授权/)).toBeTruthy();
expect(screen.getByDisplayValue(/Complete authorization in your browser/)).toBeTruthy();
expect(container.textContent).not.toContain("access_token");
expect(container.textContent).not.toContain("refresh_token");
```

- [ ] **Step 2: Run red frontend tests**

Run:

```powershell
npm --prefix apps/desktop test -- --run tests/settingsProvidersPanel.test.tsx tests/settingsDialogViewModel.test.ts
```

Expected:

- Fails until `codex_cli_login` is handled.

- [ ] **Step 3: Update frontend types and copy**

Update `ProviderAuthAttemptInfo["mode"]` to include:

```typescript
"codex_cli_login"
```

When `mode === "codex_cli_login"`:

- Render the same OpenCode-style waiting page.
- Use the backend `display_code`.
- Do not require URL to be non-empty.
- Continue polling status.

- [ ] **Step 4: Run frontend tests**

Run:

```powershell
npm --prefix apps/desktop test -- --run tests/guiProviderClient.test.ts tests/settingsProvidersPanel.test.tsx tests/settingsDialogViewModel.test.ts
npm --prefix apps/desktop run lint
```

Expected:

- Tests pass.
- TypeScript lint passes.

### Task 5: Real adapter through CodexCliChatModel

**Files:**

- Modify: `learning_agent/app/gui_agent_adapter.py`
- Test: `learning_agent/tests/test_gui_real_model_adapter.py`

- [ ] **Step 1: Add adapter tests**

Add tests:

```python
def test_real_adapter_emits_completed_events_with_fake_model():
    emitted = []
    class FakeModel:
        def chat(self, messages, tools):
            return type("Message", (), {"text": "真实模型路径回答", "tool_calls": []})()
    adapter = RealModelGuiAgentAdapter(model_factory=lambda: FakeModel(), connected_provider_reader=lambda: True)
    result = adapter.run(make_request("你好"), emitted.append, lambda: False)
    assert result.status == "completed"
    assert [event["kind"] for event in emitted] == ["turn_started", "message_delta", "message_completed"]
    assert "fake streaming" not in result.final_text

def test_real_adapter_fails_when_not_connected():
    emitted = []
    adapter = RealModelGuiAgentAdapter(model_factory=lambda: object(), connected_provider_reader=lambda: False)
    result = adapter.run(make_request("你好"), emitted.append, lambda: False)
    assert result.status == "failed"
    assert result.error_code == "real_model_not_connected"
    assert emitted[-1]["kind"] == "turn_failed"
```

- [ ] **Step 2: Run red tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_real_model_adapter.py -q
```

Expected:

- Fails because `RealModelGuiAgentAdapter` is not implemented.

- [ ] **Step 3: Implement minimal real adapter**

Add `RealModelGuiAgentAdapter` with:

- constructor accepts `model_factory` and `connected_provider_reader`.
- `run()` emits `turn_started`.
- if not connected, emits `turn_failed` with `real_model_not_connected`.
- calls model `chat(messages=[{"role":"user","content": prompt}], tools=[])`.
- emits `message_delta` and `message_completed`.
- if model returns tool calls, fail with `real_model_tools_not_connected`.
- if `is_cancelled()` becomes true, emit `turn_cancelled`.

- [ ] **Step 4: Run adapter tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_real_model_adapter.py learning_agent/tests/test_gui_agent_adapter_contract.py -q
```

Expected:

- All tests pass.

### Task 6: GUI bridge selects real adapter without fake fallback

**Files:**

- Modify: `learning_agent/app/gui_bridge.py`
- Test: `learning_agent/tests/test_gui_bridge_lifecycle.py`

- [ ] **Step 1: Add bridge routing tests**

Add tests:

```python
def test_bridge_uses_real_adapter_when_gui_model_mode_real(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENHARNESS_GUI_MODEL_MODE", "real")
    manager = GuiRunManager(tmp_path, agent_adapter=FakeStreamingGuiAgentAdapter())
    adapter = manager._adapter_for_turn(make_turn(prompt="hello"))
    assert adapter.__class__.__name__ == "RealModelGuiAgentAdapter"

def test_bridge_does_not_fallback_to_fake_when_real_adapter_reports_not_connected(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENHARNESS_GUI_MODEL_MODE", "real")
    manager = GuiRunManager(tmp_path)
    result = manager._run_adapter_turn(make_turn(prompt="hello"))
    assert result.status in {"failed", "completed"}
    if result.status == "failed":
        assert "fake streaming" not in result.error_message
```

- [ ] **Step 2: Run red tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_bridge_lifecycle.py -q
```

Expected:

- Fails until bridge can construct real adapter.

- [ ] **Step 3: Implement routing**

Rules:

- If `OPENHARNESS_GUI_MODEL_MODE=fake`, use fake adapter.
- If `OPENHARNESS_GUI_MODEL_MODE=real`, use real adapter.
- If provider source is `codex_cli` connected and mode is unset, use real adapter.
- If real adapter fails, write failed turn; never switch to fake.

- [ ] **Step 4: Run bridge tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_bridge_lifecycle.py learning_agent/tests/test_gui_real_model_adapter.py -q
```

Expected:

- All tests pass.

### Task 7: V1A visible GUI acceptance

**Files:**

- Create: `learning_agent/test/provider_settings_v2_openai_connect/scripts/capture_real_codex_login_visual_qa.ps1`
- Create: `learning_agent/test/provider_settings_v2_openai_connect/real_codex_login_evidence/`

- [ ] **Step 1: Add evidence script**

The script must:

- Start backend and renderer on explicit ports.
- Open Electron window.
- Navigate to Settings -> Providers -> OpenAI.
- Capture screenshots:
  - `codex_login_method_picker.png`
  - `codex_login_waiting.png`
  - `codex_provider_connected.png`
  - `codex_real_model_answer.png`
  - `codex_real_event_stream.png`
- Write `real_codex_login_acceptance.json` with:

```json
{
  "ok": true,
  "provider_source": "codex_cli",
  "adapter_mode": "real",
  "event_kinds": ["turn_started", "message_delta", "message_completed"],
  "fake_text_detected": false,
  "secret_leak_detected": false
}
```

- [ ] **Step 2: Run manual V1A acceptance**

Run:

```powershell
npm --prefix apps/desktop run desktop:dev
```

Manual steps:

- Open Settings.
- Providers -> OpenAI -> Connect.
- Select `ChatGPT Pro/Plus (browser)`.
- Complete browser login through Codex CLI.
- Return to Desktop.
- Send prompt: `请用一句话说明你是真实模型连接还是模拟回复。`

Expected:

- Answer does not contain `fake streaming`.
- Event stream shows `turn_started`, `message_delta`, `message_completed`.
- Evidence JSON says `ok=true`.

---

## 6. V1B Task List: Provider-Aware Real Adapter Hardening

### Task 8: Adapter tail behavior tests

**Files:**

- Modify: `learning_agent/tests/test_gui_real_model_adapter.py`

- [ ] Add tests for:

```python
def test_real_adapter_cancel_before_model_call_emits_turn_cancelled():
    adapter = make_real_adapter(model=RecordingModel())
    events = adapter.run_turn(prompt="请取消这次真实模型请求", cancel_before_model=True)
    assert event_names(events) == ["gui_turn_started", "gui_turn_cancelled"]
    assert adapter.model.call_count == 0

def test_real_adapter_remote_error_emits_turn_failed_without_completed():
    adapter = make_real_adapter(model=FailingModel(RuntimeError("remote 500")))
    events = adapter.run_turn(prompt="触发远端错误")
    assert "gui_turn_failed" in event_names(events)
    assert "message_completed" not in event_names(events)

def test_real_adapter_tool_calls_fail_fast_with_clear_error():
    adapter = make_real_adapter(model=ToolCallModel(tool_name="write_file"))
    events = adapter.run_turn(prompt="请调用一个工具")
    failed = only_event(events, "gui_turn_failed")
    assert failed["error"]["code"] == "real_model_tools_not_connected"

def test_real_adapter_long_answer_chunks_delta_without_layout_shift():
    adapter = make_real_adapter(model=LongAnswerModel(chunk_count=12))
    events = adapter.run_turn(prompt="请输出长回答")
    deltas = [event for event in events if event["type"] == "message_delta"]
    assert len(deltas) >= 2
    assert "".join(delta["delta"] for delta in deltas).endswith("END")
```

- [ ] Run:

```powershell
python -m pytest learning_agent/tests/test_gui_real_model_adapter.py -q
```

Expected:

- Fails before adapter hardening.

### Task 9: Adapter hardening implementation

**Files:**

- Modify: `learning_agent/app/gui_agent_adapter.py`

- [ ] Implement:

  - cancel before model call.
  - cancel after model call before completion.
  - remote exception -> `turn_failed`.
  - tool calls -> `real_model_tools_not_connected`.
  - chunk long text into deterministic `message_delta` pieces.

- [ ] Run:

```powershell
python -m pytest learning_agent/tests/test_gui_real_model_adapter.py learning_agent/tests/test_gui_agent_adapter_contract.py -q
```

Expected:

- All tests pass.

### Task 10: Evidence package and secret scan

**Files:**

- Modify: `learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1`
- Create: `learning_agent/test/provider_settings_v2_openai_connect/scripts/assert_real_model_acceptance.ps1`

- [ ] Extend secret scan to inspect:

  - `learning_agent/test/provider_settings_v2_openai_connect/real_codex_login_evidence/`
  - `memory/gui_provider_settings/`
  - visual QA JSON files

- [ ] Reject runtime evidence containing:

  - `access_token`
  - `refresh_token`
  - `id_token`
  - `Bearer `
  - `secret_ref`
  - `api_key`

- [ ] Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1
```

Expected:

- `Provider secret leak scan passed.`

---

## 7. V1C Task List: Experimental Direct OAuth

### Task 11: Direct OAuth threat model and token store first

**Files:**

- Create: `learning_agent/app/gui_provider_oauth_token_store.py`
- Create: `learning_agent/tests/test_gui_provider_oauth_token_store.py`

- [ ] Write tests for:

```python
def test_token_store_writes_outside_workspace(tmp_path):
    store = make_fake_token_store(config_dir=tmp_path / "profile")
    store.set_tokens(provider="openai", tokens=sample_tokens())
    assert str(store.path_for("openai")).startswith(str(tmp_path / "profile"))

def test_token_store_never_returns_raw_tokens_in_info(tmp_path):
    store = make_fake_token_store(config_dir=tmp_path)
    store.set_tokens(provider="openai", tokens=sample_tokens())
    info = store.info(provider="openai")
    assert "access_token" not in json.dumps(info)
    assert info["connected"] is True

def test_token_store_delete_removes_login(tmp_path):
    store = make_fake_token_store(config_dir=tmp_path)
    store.set_tokens(provider="openai", tokens=sample_tokens())
    store.delete_tokens(provider="openai")
    assert store.info(provider="openai")["connected"] is False

def test_corrupt_token_record_is_reported_as_missing(tmp_path):
    store = make_fake_token_store(config_dir=tmp_path)
    store.write_raw(provider="openai", raw=b"not-json")
    assert store.info(provider="openai")["connected"] is False
```

- [ ] Run red tests:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_oauth_token_store.py -q
```

- [ ] Implement store:

  - Windows DPAPI storage.
  - In-memory fake store for tests.
  - `set_tokens()`, `get_tokens()`, `delete_tokens()`, `info()`.
  - no raw token in `info()`.

- [ ] Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_oauth_token_store.py -q
```

Expected:

- All tests pass.

### Task 12: Direct OAuth config and product gate

**Files:**

- Modify: `learning_agent/app/gui_provider_openai_auth_config.py`
- Test: `learning_agent/tests/test_gui_provider_openai_auth_config.py`

- [ ] Add tests:

```python
def test_direct_oauth_requires_experimental_flag_and_client_id(monkeypatch):
    monkeypatch.setenv("OPENHARNESS_OPENAI_AUTH_MODE", "direct_oauth")
    monkeypatch.delenv("OPENHARNESS_OPENAI_EXPERIMENTAL", raising=False)
    with pytest.raises(OpenAIAuthConfigError, match="experimental"):
        build_openai_auth_config()

def test_direct_oauth_does_not_default_to_opencode_client_id(monkeypatch):
    monkeypatch.setenv("OPENHARNESS_OPENAI_AUTH_MODE", "direct_oauth")
    monkeypatch.setenv("OPENHARNESS_OPENAI_EXPERIMENTAL", "1")
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "os_encrypted")
    monkeypatch.delenv("OPENHARNESS_OPENAI_CLIENT_ID", raising=False)
    with pytest.raises(OpenAIAuthConfigError, match="client_id"):
        build_openai_auth_config()

def test_direct_oauth_requires_os_encrypted_store(monkeypatch):
    monkeypatch.setenv("OPENHARNESS_OPENAI_AUTH_MODE", "direct_oauth")
    monkeypatch.setenv("OPENHARNESS_OPENAI_EXPERIMENTAL", "1")
    monkeypatch.setenv("OPENHARNESS_OPENAI_CLIENT_ID", "openharness-local-test")
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "plain_file")
    with pytest.raises(OpenAIAuthConfigError, match="os_encrypted"):
        build_openai_auth_config()
```

- [ ] Implement config:

  - `OPENHARNESS_OPENAI_AUTH_MODE=direct_oauth`.
  - `OPENHARNESS_OPENAI_EXPERIMENTAL=1`.
  - `OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted`.
  - `OPENHARNESS_OPENAI_CLIENT_ID` required.
  - No default OpenCode client id.

- [ ] Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_openai_auth_config.py -q
```

Expected:

- All tests pass.

### Task 13: PKCE and authorize URL

**Files:**

- Create: `learning_agent/app/gui_provider_openai_oauth.py`
- Create: `learning_agent/tests/test_gui_provider_openai_oauth.py`

- [ ] Add tests for:

  - PKCE verifier/challenge format.
  - state randomness.
  - authorize URL parameters.
  - originator is `openharness`.
  - OpenCode client id is not used unless explicitly configured.

- [ ] Run red tests:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_openai_oauth.py -q
```

- [ ] Implement minimal PKCE and URL helper.

- [ ] Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_openai_oauth.py -q
```

Expected:

- All tests pass.

### Task 14: Callback server with port preflight

**Files:**

- Modify: `learning_agent/app/gui_provider_openai_oauth.py`
- Modify: `learning_agent/tests/test_gui_provider_openai_oauth.py`

- [ ] Add tests for:

  - port 1455 available.
  - port 1455 occupied -> `oauth_port_in_use`.
  - state mismatch -> failed.
  - duplicate callback -> ignored after complete.
  - user closes dialog then callback arrives -> callback page says attempt expired.
  - token exchange 500 -> failed.

- [ ] Implement:

  - `preflight_oauth_port()`.
  - `OpenAIProviderOAuthAttempt`.
  - callback server bound to `127.0.0.1`.
  - timeout cleanup.

- [ ] Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_openai_oauth.py -q
```

Expected:

- All tests pass.

### Task 15: Direct OAuth provider integration

**Files:**

- Modify: `learning_agent/app/gui_provider_auth_attempts.py`
- Modify: `learning_agent/app/gui_provider_settings.py`
- Modify: `learning_agent/tests/test_gui_provider_auth_attempts_contract.py`
- Modify: `learning_agent/tests/test_gui_provider_settings_contract.py`

- [ ] Add tests:

  - direct OAuth attempt returns `mode="direct_oauth_browser"`.
  - direct OAuth complete writes only `token_ref`.
  - provider catalog source is `direct_oauth_experimental`.
  - raw token words never appear in payload.

- [ ] Implement integration.

- [ ] Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_auth_attempts_contract.py learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/tests/test_gui_provider_oauth_token_store.py -q
```

Expected:

- All tests pass.

### Task 16: Direct OAuth model adapter integration

**Files:**

- Modify: `learning_agent/models/adapters.py`
- Modify: `learning_agent/app/gui_agent_adapter.py`
- Test: `learning_agent/tests/test_gui_real_model_adapter.py`

- [ ] Add tests:

  - direct OAuth token store is injected into `CodexOAuthChatModel`.
  - refresh updates token store.
  - `ChatGPT-Account-Id` header is included when available.
  - remote endpoint is `https://chatgpt.com/backend-api/codex/responses`.

- [ ] Implement adapter factory selection:

  - `codex_cli` source -> `CodexCliChatModel`.
  - `direct_oauth_experimental` source -> `CodexOAuthChatModel`.

- [ ] Run:

```powershell
python -m pytest learning_agent/tests/test_gui_real_model_adapter.py learning_agent/tests/test_models_adapters.py -q
```

Expected:

- All tests pass.

### Task 17: Direct OAuth visible GUI acceptance

**Files:**

- Create: `learning_agent/test/provider_settings_v2_openai_connect/direct_oauth_evidence/`

- [ ] Set env:

```powershell
$env:OPENHARNESS_OPENAI_AUTH_MODE="direct_oauth"
$env:OPENHARNESS_OPENAI_EXPERIMENTAL="1"
$env:OPENHARNESS_PROVIDER_SECRET_STORE="os_encrypted"
$env:OPENHARNESS_OPENAI_CLIENT_ID="<OpenHarness-owned-or-explicit-test-client-id>"
$env:OPENHARNESS_GUI_MODEL_MODE="real"
```

- [ ] Start GUI:

```powershell
npm --prefix apps/desktop run desktop:dev
```

- [ ] Manual visible steps:

  - Settings -> Providers -> OpenAI -> Connect.
  - Select `ChatGPT Pro/Plus (browser)`.
  - Browser opens OpenAI auth.
  - Callback page shows `Authorization Successful`.
  - Provider row shows experimental direct OAuth connected.
  - Main chat returns real answer.

- [ ] Evidence files:

  - `direct_oauth_login_success.png`
  - `direct_oauth_provider_connected.png`
  - `direct_oauth_model_answer.png`
  - `direct_oauth_event_stream.png`
  - `direct_oauth_acceptance.json`

---

## 8. Release Gate

- [ ] Backend tests:

```powershell
python -m pytest learning_agent/tests/test_gui_codex_auth_bridge.py learning_agent/tests/test_gui_provider_openai_auth_config.py learning_agent/tests/test_gui_provider_auth_attempts_contract.py learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/tests/test_gui_bridge_security_contract.py learning_agent/tests/test_gui_real_model_adapter.py -q
```

- [ ] Direct OAuth tests:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_oauth_token_store.py learning_agent/tests/test_gui_provider_openai_oauth.py -q
```

- [ ] Frontend tests:

```powershell
npm --prefix apps/desktop test
```

- [ ] Frontend lint:

```powershell
npm --prefix apps/desktop run lint
```

- [ ] Frontend build:

```powershell
npm --prefix apps/desktop run build
```

- [ ] Secret scan:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1
```

- [ ] V1A visible GUI acceptance evidence exists:

```text
learning_agent/test/provider_settings_v2_openai_connect/real_codex_login_evidence/real_codex_login_acceptance.json
```

- [ ] V1C direct OAuth evidence exists only if V1C was enabled:

```text
learning_agent/test/provider_settings_v2_openai_connect/direct_oauth_evidence/direct_oauth_acceptance.json
```

Completion rule:

- V1A can be declared complete when official Codex login bridge produces a real GUI answer.
- V1B can be declared complete when real adapter tail behavior and evidence package pass.
- V1C can be declared complete only when direct OAuth is explicitly enabled, visible GUI acceptance passes, and no token leaks are detected.
- Every acceptance step must use a real, visible GUI window for human-visible verification. If a bug appears during acceptance or is discovered afterward, stop the task sequence, use `superpowers:systematic-debugging`, fix the bug, rerun the GUI acceptance, and continue only after the retest passes.
- If real visible GUI acceptance is not completed, the final report must say: `真实可见 GUI OAuth 验收未完成，不能声明真实模型连接开发完成。`

---

## 9. Success Criteria

The user-facing success path is:

1. 用户打开 OpenHarness Desktop。
2. 点击左下角设置。
3. 进入提供商。
4. OpenAI 选择 `ChatGPT Pro/Plus (browser)`。
5. V1A 默认打开官方 Codex ChatGPT OAuth 登录。
6. 登录完成后，OpenAI provider 显示 `Codex ChatGPT login` connected。
7. 用户回到主聊天输入问题。
8. OpenHarness Desktop 返回真实模型回答。
9. 回答和事件流都不包含 `fake streaming`。
10. 证据包可复盘，secret scan 通过。

到这里，OpenHarness Desktop 才算从“像 Codex 的外壳”走到“有真实 ChatGPT OAuth 模型连接能力的外壳”。
