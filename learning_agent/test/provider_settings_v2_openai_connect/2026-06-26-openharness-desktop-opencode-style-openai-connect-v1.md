# OpenHarness Desktop OpenCode-Style OpenAI Connect Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 OpenHarness Desktop 的 `设置 -> 提供商 -> OpenAI -> 连接` 升级为 OpenCode 风格连接向导，并先交付可执行、可验收、可回滚的稳定 V1：方法选择 + API Key 真实路径 + mock auth-attempt 状态机；真实 ChatGPT headless/browser OAuth 只在安全门禁满足后作为 gated experimental 能力开启。

**Architecture:** 采用 OpenCode 的 integration attempt 抽象，但不把真实 OAuth token 默认写进开发 JSON 存储。稳定 V1 用 `auth-attempt` 端到端打通 UI、bridge、状态轮询、取消、mock 完成和视觉验收；真实 headless/browser OAuth 被拆为后续 gated slices，必须满足加密密钥存储、显式 experimental flag 和 OAuth config 才能保存 refresh token。

**Tech Stack:** Python stdlib HTTP bridge + React 18 + TypeScript + Vite + Electron + Vitest + pytest + CDP visual QA scripts.

---

## Karpathy Review Changes Applied

本升级版已吸收 `2026-06-26-openharness-desktop-opencode-style-openai-connect-v1-karpathy-review.md` 的核心意见：

- V1 不再一次吞下真实 browser/headless OAuth；稳定交付范围收敛为 `Slice A + Slice B`。
- 旧会话式命名统一改为 `auth-attempt`，避免和聊天 session 混淆。
- 真实 OpenAI OAuth token 保存增加硬门禁：`OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted` 之前不能保存真实 `refresh_token`。
- 不直接照搬 OpenCode 的 OAuth `clientID`、`issuer`、`callbackPort`；新增 `OpenAIAuthConfig` 配置层。
- 旧确认码命名改为 `display_code`、`display_code_kind`，避免把 browser instruction 误称为 code。
- attempt status enum 收紧为 `pending | complete | failed | expired`；取消统一表现为 `expired + message=cancelled_by_user`。
- auto mode 前端只 `start/status/cancel`，不调用 `complete`；`complete` 只用于 code mode 或 mock/test mode。
- 增加 tail behavior tests：重复 start、重复 cancel、未知 attempt、renderer 关闭、secret leak、callback state 错误。

## Evidence From OpenCode

本蓝图已经读取 `D:\opencode` 的 CodeGraph 和源代码，关键证据如下：

- `D:\opencode\packages\core\src\plugin\provider\openai.ts:38` 注册 `ChatGPT Pro/Plus (browser)`，使用 PKCE、本地 callback server、`https://auth.openai.com/oauth/authorize`。
- `D:\opencode\packages\core\src\plugin\provider\openai.ts:91` 注册 `ChatGPT Pro/Plus (headless)`，使用 device flow，请求 user code 并轮询 token endpoint。
- `D:\opencode\packages\app\src\components\dialog-connect-provider.tsx:20` 是连接 UI 主入口：先选择 method，再进入 API Key、OAuth auto 或 OAuth code 分支。
- `D:\opencode\packages\protocol\src\groups\integration.ts:41` 定义 key connect，`:61` 定义 OAuth connect，`:72`、`:87`、`:102` 定义 attempt status、complete、cancel。
- `D:\opencode\packages\schema\src\integration.ts:114` 定义 attempt：`attemptID`、`url`、`instructions`、`mode`、`time`，状态为 `pending`、`complete`、`failed`、`expired`。

## Product Boundary

稳定 V1 必须完成：

- OpenAI 连接界面肉眼接近 OpenCode：返回箭头、关闭按钮、标题 `连接 OpenAI`、三种登录方式、API Key 表单、OAuth 等待页。
- API Key 路径真实写入后端 secret store，刷新 provider catalog，并能使用现有 OpenAI-compatible `/models` 探针。
- Browser/headless 方法在 V1 中可进入 mock auth-attempt flow：返回 mock 授权 URL、`display_code`、等待授权状态、完成后刷新连接状态。
- 所有 provider catalog、renderer state、日志、截图、visual QA JSON 不包含 raw key、`access_token`、`refresh_token`、`id_token`、`secret_ref`。
- 真实可见 GUI 验收必须通过；发现 bug 时用 `superpowers:systematic-debugging` 修复并重测。
- 用户强制验收要求：验收需要使用肉眼可见的真实GUI界面进行验收，验收时出现bug或发现bug时，请使用systematic debugging技能，修复bug，并重新测试，测试通过后继续执行下一个任务。

稳定 V1 不声明完成：

- 真实 ChatGPT browser OAuth 网络授权。
- 真实 ChatGPT headless device flow 网络授权。
- 完整模型 runtime 使用 ChatGPT OAuth token 发起推理。
- OS 加密密钥存储实现。

真实 OAuth 的开启条件：

```text
OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted
OPENHARNESS_OPENAI_AUTH_MODE=real_headless 或 real_browser
OPENHARNESS_OPENAI_CLIENT_ID 非空
OPENHARNESS_OPENAI_EXPERIMENTAL=1
```

如果以上条件不满足，真实 OAuth 入口必须显示安全门禁文案或使用 mock/test mode，不能保存真实 `refresh_token`。

## File Structure

新增文件：

```text
learning_agent/app/gui_provider_auth_attempts.py
learning_agent/app/gui_provider_openai_auth_config.py
learning_agent/tests/test_gui_provider_auth_attempts_contract.py
learning_agent/tests/test_gui_provider_openai_auth_config.py
apps/desktop/src/components/settings/ProviderConnectWizard.tsx
apps/desktop/src/components/settings/ProviderAuthMethodList.tsx
apps/desktop/src/components/settings/ProviderApiKeyStep.tsx
apps/desktop/src/components/settings/ProviderOAuthAutoStep.tsx
apps/desktop/src/components/settings/ProviderOAuthCodeStep.tsx
apps/desktop/tests/providerConnectWizard.test.tsx
learning_agent/test/provider_settings_v2_openai_connect/scripts/mock_openai_oauth_server.py
learning_agent/test/provider_settings_v2_openai_connect/scripts/capture_openai_connect_visual_qa.ps1
learning_agent/test/provider_settings_v2_openai_connect/scripts/openai_connect_visual_qa_driver.mjs
```

修改文件：

```text
learning_agent/app/gui_provider_settings.py
learning_agent/app/gui_provider_secret_store.py
learning_agent/app/gui_bridge.py
learning_agent/tests/test_gui_provider_settings_contract.py
learning_agent/tests/test_gui_bridge_security_contract.py
apps/desktop/src/api/guiProviderTypes.ts
apps/desktop/src/api/guiClient.ts
apps/desktop/src/state/providerSettingsStore.ts
apps/desktop/src/components/settings/SettingsDialog.tsx
apps/desktop/src/components/settings/SettingsProvidersPanel.tsx
apps/desktop/src/components/settings/ProviderConnectDialog.tsx
apps/desktop/src/styles/settings-dialog.css
apps/desktop/tests/guiProviderClient.test.ts
apps/desktop/tests/providerSettingsStore.test.ts
apps/desktop/tests/settingsProvidersPanel.test.tsx
learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1
agent_memory/context.md
agent_memory/progress.md
agent_memory/bugs.md
```

## Contract Design

### OpenAI Auth Config

新增 `OpenAIAuthConfig`，从环境变量和 secret store kind 计算 OAuth 能力：

```json
{
  "mode": "mock",
  "auth_base_url": "http://127.0.0.1:18991",
  "client_id": "",
  "callback_host": "localhost",
  "preferred_callback_port": 1455,
  "experimental_enabled": false,
  "allow_insecure_oauth_for_tests": false,
  "secret_store_kind": "dev_json",
  "real_oauth_allowed": false,
  "blocked_reason": "requires_os_encrypted_secret_store"
}
```

环境变量：

```text
OPENHARNESS_OPENAI_AUTH_MODE=disabled|mock|real_headless|real_browser
OPENHARNESS_OPENAI_AUTH_BASE=http://127.0.0.1:18991
OPENHARNESS_OPENAI_CLIENT_ID=
OPENHARNESS_OPENAI_CALLBACK_HOST=localhost
OPENHARNESS_OPENAI_CALLBACK_PORT=1455
OPENHARNESS_OPENAI_EXPERIMENTAL=0|1
OPENHARNESS_ALLOW_INSECURE_OAUTH_FOR_TESTS=0|1
OPENHARNESS_PROVIDER_SECRET_STORE=dev_json|os_encrypted
```

Truth table：

| Mode | Secret Store | Experimental | Result |
| --- | --- | --- | --- |
| `mock` | any | any | mock attempt allowed, no real token |
| `disabled` | any | any | OAuth methods visible but disabled |
| `real_headless` | `os_encrypted` | `1` | real headless allowed |
| `real_browser` | `os_encrypted` | `1` | real browser allowed |
| `real_headless` | `dev_json` | any | blocked |
| `real_browser` | `dev_json` | any | blocked |

### Provider Method Metadata

`GuiProviderAuthMethod` schema version 升级到 `3`，OpenAI methods 顺序固定：

```json
[
  {
    "id": "chatgpt-browser",
    "type": "oauth",
    "label": "ChatGPT Pro/Plus (browser)",
    "enabled": true,
    "status": "mock_available",
    "mode": "auto",
    "experimental": true,
    "fields": [],
    "help_text": "使用浏览器登录 ChatGPT Pro/Plus；稳定 V1 使用 mock auth-attempt 验证界面和状态机。"
  },
  {
    "id": "chatgpt-headless",
    "type": "oauth",
    "label": "ChatGPT Pro/Plus (headless)",
    "enabled": true,
    "status": "mock_available",
    "mode": "auto",
    "experimental": true,
    "fields": [],
    "help_text": "使用设备码登录 ChatGPT Pro/Plus；稳定 V1 使用 mock auth-attempt 验证界面和状态机。"
  },
  {
    "id": "api-key",
    "type": "api",
    "label": "API 密钥",
    "enabled": true,
    "status": "available",
    "mode": "form",
    "experimental": false,
    "fields": ["secret"],
    "help_text": "使用 OpenAI API Key 真实连接后端。"
  }
]
```

### Auth Attempt Endpoints

endpoint 统一使用 `auth-attempt`：

```text
POST /v2/gui/provider-settings/auth-attempt/start
GET  /v2/gui/provider-settings/auth-attempt/status?attempt_id=...
POST /v2/gui/provider-settings/auth-attempt/complete
POST /v2/gui/provider-settings/auth-attempt/cancel
```

`start` 请求：

```json
{
  "provider_id": "openai",
  "auth_method_id": "chatgpt-headless",
  "inputs": {}
}
```

`start` 响应：

```json
{
  "ok": true,
  "schema_version": 3,
  "attempt": {
    "attempt_id": "ohauth_20260626_000001",
    "provider_id": "openai",
    "auth_method_id": "chatgpt-headless",
    "url": "http://127.0.0.1:18991/codex/device",
    "instructions": "Enter code: MOCK-OPENAI",
    "mode": "auto",
    "display_code": "MOCK-OPENAI",
    "display_code_kind": "device_code",
    "display_code_copyable": true,
    "status": "pending",
    "message": "",
    "created_at": 1782440000.0,
    "expires_at": 1782440600.0
  }
}
```

browser mock attempt 使用：

```json
{
  "display_code": "Complete authorization in your browser. This window will close automatically.",
  "display_code_kind": "instruction",
  "display_code_copyable": true
}
```

status enum 只允许：

```text
pending
complete
failed
expired
```

取消语义：

```json
{
  "ok": true,
  "schema_version": 3,
  "attempt_id": "ohauth_20260626_000001",
  "status": "expired",
  "message": "cancelled_by_user",
  "expires_at": 1782440600.0
}
```

auto mode 前端职责：

```text
start -> poll status -> cancel on close
```

code mode 前端职责：

```text
start -> user enters code -> complete
```

mock/test mode 可以用 `complete` 或 mock server 触发 complete，但真实 auto mode 前端不能调用 complete。

## Implementation Slices

### Slice A: Method Picker + API Key Real Path

完成 OpenAI 三方法展示、OpenCode 风格连接向导、API Key 真实保存和 `/models` 探针。

### Slice B: Auth Attempt Contract + Mock Headless/Browser

完成 `auth-attempt` backend contract、mock OAuth server、status polling、cancel、mock complete、视觉验收。

### Slice C: Real Headless Device Flow Gate

稳定 V1 不执行真实 headless 网络授权。只有满足 `os_encrypted + experimental + client_id` 后，另起任务把 mock headless backend 替换为真实 device flow。

### Slice D: Real Browser PKCE Callback Gate

稳定 V1 不执行真实 browser PKCE callback。只有 Slice C 稳定且满足安全门禁后，另起任务实现 browser callback server、state 校验、token exchange。

## Implementation Tasks

### Task 0: Product And Safety Decisions

**Files:**
- Modify: `agent_memory/context.md`
- Modify: `agent_memory/progress.md`

- [ ] 记录 V1 stable path：API Key 真实路径 + mock auth-attempt。
- [ ] 记录 OAuth path：真实 OAuth 是 gated experimental，不属于稳定 V1 完成定义。
- [ ] 记录真实 OAuth token gate：没有 `os_encrypted` secret store 时不能保存真实 `refresh_token`。
- [ ] 记录 attempt status enum：`pending | complete | failed | expired`。
- [ ] 记录 auto/code mode 前端职责边界。
- [ ] 运行人工检查：确认蓝图没有旧会话式命名字样，只有 `auth-attempt`。

Expected:

```text
No deprecated auth attempt naming remains in the upgraded implementation plan.
```

### Task 1: Backend Catalog Contract For Three OpenAI Methods

**Files:**
- Modify: `learning_agent/app/gui_provider_settings.py`
- Test: `learning_agent/tests/test_gui_provider_settings_contract.py`

- [ ] 新增失败测试：OpenAI provider 返回三种 method，顺序为 browser、headless、API Key。
- [ ] 新增失败测试：OAuth methods 在 default dev mode 下 `status=mock_available`，真实 OAuth 不写入 `connected=true`。
- [ ] 新增失败测试：provider catalog 不包含 `access_token`、`refresh_token`、`id_token`、`secret_ref`。
- [ ] 修改 `GuiAuthMethodInfo`，增加 `type`、`mode`、`experimental` 字段。
- [ ] 修改 OpenAI method builder，按 Contract Design 返回三种 methods。
- [ ] 运行：

```powershell
python -m pytest learning_agent/tests/test_gui_provider_settings_contract.py -q
```

Expected:

```text
passed
```

### Task 2: Frontend Types And Store For Method Picker

**Files:**
- Modify: `apps/desktop/src/api/guiProviderTypes.ts`
- Modify: `apps/desktop/src/state/providerSettingsStore.ts`
- Test: `apps/desktop/tests/providerSettingsStore.test.ts`

- [ ] 新增类型：`GuiProviderAuthMethodType = "api" | "oauth" | string`。
- [ ] 新增类型：`GuiProviderAuthMethodMode = "form" | "auto" | "code" | string`。
- [ ] `ProviderAuthMethodView` 增加 `type`、`mode`、`experimental`。
- [ ] `redactedProviderPayload()` 禁止字段增加：`access_token`、`refresh_token`、`id_token`、`token`、`secret_ref`。
- [ ] 新增测试：OpenAI 三 methods 被转换成 camelCase view model。
- [ ] 新增测试：危险 token 字段被递归清理。
- [ ] 运行：

```powershell
npm --prefix apps/desktop test -- --run tests/providerSettingsStore.test.ts
```

Expected:

```text
Test Files  1 passed
```

### Task 3: OpenCode-Style Method Picker UI

**Files:**
- Create: `apps/desktop/src/components/settings/ProviderConnectWizard.tsx`
- Create: `apps/desktop/src/components/settings/ProviderAuthMethodList.tsx`
- Modify: `apps/desktop/src/components/settings/ProviderConnectDialog.tsx`
- Modify: `apps/desktop/src/components/settings/SettingsDialog.tsx`
- Modify: `apps/desktop/src/components/settings/SettingsProvidersPanel.tsx`
- Test: `apps/desktop/tests/providerConnectWizard.test.tsx`
- Test: `apps/desktop/tests/settingsProvidersPanel.test.tsx`

- [ ] 新增失败测试：点击 OpenAI `+ 连接` 后显示标题 `连接 OpenAI`。
- [ ] 新增失败测试：方法选择页显示 `ChatGPT Pro/Plus (browser)`、`ChatGPT Pro/Plus (headless)`、`API 密钥`。
- [ ] 新增失败测试：返回箭头从方法选择页关闭 wizard，从子步骤返回方法选择页。
- [ ] 实现 `ProviderConnectWizard`，先只渲染 method picker，不接入 API submit。
- [ ] 将旧 `ProviderConnectDialog.tsx` 改成兼容 re-export 或薄包装，避免两套连接 UI 分叉。
- [ ] 运行：

```powershell
npm --prefix apps/desktop test -- --run tests/providerConnectWizard.test.tsx tests/settingsProvidersPanel.test.tsx
```

Expected:

```text
Test Files  2 passed
```

### Task 4: API Key Step Real Path

**Files:**
- Create: `apps/desktop/src/components/settings/ProviderApiKeyStep.tsx`
- Modify: `apps/desktop/src/components/settings/ProviderConnectWizard.tsx`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Test: `apps/desktop/tests/providerConnectWizard.test.tsx`
- Test: `apps/desktop/tests/guiProviderClient.test.ts`

- [ ] 新增失败测试：点击 `API 密钥` 后显示 password input。
- [ ] 新增失败测试：空 API Key 提交显示 `API 密钥为必填项`。
- [ ] 新增失败测试：有效 API Key 调用现有 `/v2/gui/provider-settings/auth`，成功后刷新 provider catalog。
- [ ] 实现 `ProviderApiKeyStep`，输入框 `type=password`，`autoComplete=off`。
- [ ] 保持后端现有 `set_provider_auth()` 逻辑，不引入 OAuth attempt。
- [ ] 运行：

```powershell
python -m pytest learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/tests/test_gui_provider_secret_store.py -q
npm --prefix apps/desktop test -- --run tests/providerConnectWizard.test.tsx tests/guiProviderClient.test.ts
```

Expected:

```text
passed
Test Files  2 passed
```

### Task 5: OpenAI Auth Config Gate

**Files:**
- Create: `learning_agent/app/gui_provider_openai_auth_config.py`
- Test: `learning_agent/tests/test_gui_provider_openai_auth_config.py`

- [ ] 新增失败测试：default config 为 `mode=mock` 或 `mode=disabled`，`real_oauth_allowed=false`。
- [ ] 新增失败测试：`real_headless + dev_json + experimental=1` 返回 blocked reason `requires_os_encrypted_secret_store`。
- [ ] 新增失败测试：`real_headless + os_encrypted + experimental=1 + client_id` 返回 `real_oauth_allowed=true`。
- [ ] 实现 `build_openai_auth_config(env, secret_store_kind)`。
- [ ] 实现 `assert_real_oauth_allowed(config)`，失败时抛结构化错误。
- [ ] 运行：

```powershell
python -m pytest learning_agent/tests/test_gui_provider_openai_auth_config.py -q
```

Expected:

```text
passed
```

### Task 6: Auth Attempt Backend Contract In Mock Mode

**Files:**
- Create: `learning_agent/app/gui_provider_auth_attempts.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Test: `learning_agent/tests/test_gui_provider_auth_attempts_contract.py`
- Test: `learning_agent/tests/test_gui_bridge_security_contract.py`

- [ ] 新增失败测试：`start_auth_attempt(openai, chatgpt-headless)` 返回 `pending`、mock URL、`display_code_kind=device_code`。
- [ ] 新增失败测试：`start_auth_attempt(openai, chatgpt-browser)` 返回 `pending`、mock URL、`display_code_kind=instruction`。
- [ ] 新增失败测试：重复 start 同 provider 取消旧 attempt，旧 attempt status 为 `expired`。
- [ ] 新增失败测试：未知 attempt status 返回 `expired`，不返回 500。
- [ ] 新增失败测试：cancel 两次是 idempotent。
- [ ] 新增 bridge endpoints：`auth-attempt/start`、`status`、`complete`、`cancel`。
- [ ] 所有 endpoints 必须走 token guard。
- [ ] 运行：

```powershell
python -m pytest learning_agent/tests/test_gui_provider_auth_attempts_contract.py learning_agent/tests/test_gui_bridge_security_contract.py -q
```

Expected:

```text
passed
```

### Task 7: OAuth Auto UI With Polling And Cancel

**Files:**
- Create: `apps/desktop/src/components/settings/ProviderOAuthAutoStep.tsx`
- Create: `apps/desktop/src/components/settings/ProviderOAuthCodeStep.tsx`
- Modify: `apps/desktop/src/components/settings/ProviderConnectWizard.tsx`
- Modify: `apps/desktop/src/api/guiProviderTypes.ts`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Test: `apps/desktop/tests/providerConnectWizard.test.tsx`
- Test: `apps/desktop/tests/guiProviderClient.test.ts`

- [ ] 新增 client methods：`startProviderAuthAttempt()`、`getProviderAuthAttemptStatus()`、`completeProviderAuthAttempt()`、`cancelProviderAuthAttempt()`。
- [ ] 新增失败测试：点击 headless 调用 `auth-attempt/start` 并显示 `display_code`。
- [ ] 新增失败测试：auto mode poll 到 `complete` 后关闭 wizard 并刷新 catalog。
- [ ] 新增失败测试：关闭 wizard 调用 `auth-attempt/cancel` 并清理 poll timer。
- [ ] 新增失败测试：auto mode 前端不调用 `complete`。
- [ ] 实现 `ProviderOAuthAutoStep`，显示链接、display code、复制按钮、spinner、`等待授权...`。
- [ ] 实现 `ProviderOAuthCodeStep`，仅在 `mode=code` 时显示 code 输入。
- [ ] 运行：

```powershell
npm --prefix apps/desktop test -- --run tests/providerConnectWizard.test.tsx tests/guiProviderClient.test.ts
```

Expected:

```text
Test Files  2 passed
```

### Task 8: Mock OAuth Visual QA

**Files:**
- Create: `learning_agent/test/provider_settings_v2_openai_connect/scripts/mock_openai_oauth_server.py`
- Create: `learning_agent/test/provider_settings_v2_openai_connect/scripts/capture_openai_connect_visual_qa.ps1`
- Create: `learning_agent/test/provider_settings_v2_openai_connect/scripts/openai_connect_visual_qa_driver.mjs`
- Modify: `apps/desktop/src/styles/settings-dialog.css`

- [ ] mock server 提供 `/codex/device`、`/api/accounts/deviceauth/usercode`、`/api/accounts/deviceauth/token`，只返回测试 token，不返回真实 token。
- [ ] visual QA 启动 bridge、renderer、Electron、mock server。
- [ ] visual QA 点击 `设置 -> 提供商 -> OpenAI -> + 连接`。
- [ ] visual QA 截图 method picker。
- [ ] visual QA 点击 API Key，断言 `input.type=password`。
- [ ] visual QA 返回 method picker，点击 headless，断言等待授权页可见。
- [ ] visual QA 完成 mock attempt，断言 provider 状态刷新。
- [ ] visual QA JSON 必须包含：

```json
{
  "ok": true,
  "methodCount": 3,
  "inputType": "password",
  "waitingVisible": true,
  "rawSecretLeakFound": false
}
```

- [ ] 运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v2_openai_connect/scripts/capture_openai_connect_visual_qa.ps1
```

Expected:

```text
OpenAI connect visual QA passed.
```

### Task 9: Tail Behavior And Secret Leak Gate

**Files:**
- Modify: `learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1`
- Modify: `learning_agent/tests/test_gui_provider_auth_attempts_contract.py`
- Modify: `apps/desktop/tests/providerConnectWizard.test.tsx`

- [ ] secret scan 增加危险模式：`access_token`、`refresh_token`、`id_token`、`oauth-secret-test-value`、`secret_ref`。
- [ ] 允许蓝图文档和测试源码出现字段名，不允许运行产物出现 raw token 值。
- [ ] 后端 tail tests 覆盖：重复 start、重复 cancel、未知 attempt、过期 attempt、mock complete 后不能重复保存。
- [ ] 前端 tail tests 覆盖：renderer 关闭 wizard 时清理 poll timer；失败 status 显示错误并停止轮询。
- [ ] 运行：

```powershell
python -m pytest learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/tests/test_gui_provider_auth_attempts_contract.py learning_agent/tests/test_gui_provider_openai_auth_config.py learning_agent/tests/test_gui_bridge_security_contract.py -q
npm --prefix apps/desktop test
powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1
```

Expected:

```text
passed
Test Files passed
Provider secret leak scan passed.
```

### Task 10: Real Visible GUI Acceptance Gate

**Files:**
- Evidence: `learning_agent/test/provider_settings_v2_openai_connect/visual_evidence/`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md` when bugs are found

- [ ] 启动真实可见 OpenHarness Desktop Electron 窗口。
- [ ] 肉眼验收 provider list 与 OpenCode 参考截图一致。
- [ ] 肉眼验收 `连接 OpenAI` 方法选择页显示三种方式。
- [ ] 肉眼验收 API Key step 的输入框是 password，空值有错误。
- [ ] 肉眼验收 headless mock OAuth step 显示链接、display code、复制按钮、等待授权。
- [ ] 肉眼验收 mock complete 后 provider 状态刷新。
- [ ] 按用户强制验收要求执行：验收需要使用肉眼可见的真实GUI界面进行验收，验收时出现bug或发现bug时，请使用systematic debugging技能，修复bug，并重新测试，测试通过后继续执行下一个任务。
- [ ] 保存截图：

```text
openai-method-selection.png
openai-api-key-step.png
openai-oauth-auto-waiting.png
openai-connect-complete.png
openai_connect_visual_qa_result.json
```

- [ ] 如果验收发现 bug，使用 `superpowers:systematic-debugging` 定位根因，修复后重新跑 Task 8、Task 9、Task 10。
- [ ] 如果当前 Codex 环境无法观察或操作用户本地真实窗口，最终回答必须明确写出：`真实可见 GUI 交互验收未完成，不能声明开发完成。`

Expected:

```text
真实 GUI 截图齐全，visual QA ok=true，未发现 token 泄露。
```

### Task 11: Documentation, Learning Copies, And Release Gate

**Files:**
- Modify: `agent_memory/context.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`
- Copy to: `learning_agent/test/provider_settings_v2_openai_connect/source_copies/`
- Copy to: `learning_agent/test/provider_settings_v2_openai_connect/2026-06-26-openharness-desktop-opencode-style-openai-connect-v1.md`

- [ ] 更新 `agent_memory/context.md`，记录 stable V1、mock auth-attempt、real OAuth gate。
- [ ] 更新 `agent_memory/progress.md`，记录每个 task 的命令和结果。
- [ ] 若出现 OAuth config、attempt、visual QA、secret scan bug，更新 `agent_memory/bugs.md`。
- [ ] 将新增/修改代码学习副本保存到 `source_copies/`。
- [ ] 将本蓝图复制到 `learning_agent/test/provider_settings_v2_openai_connect/`。
- [ ] 运行最终 release gate：

```powershell
python -m pytest learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/tests/test_gui_provider_auth_attempts_contract.py learning_agent/tests/test_gui_provider_openai_auth_config.py learning_agent/tests/test_gui_bridge_security_contract.py -q
npm --prefix apps/desktop test
npm --prefix apps/desktop run lint
npm --prefix apps/desktop run build
powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v2_openai_connect/scripts/capture_openai_connect_visual_qa.ps1
```

Expected:

```text
All backend tests passed.
All frontend tests passed.
Frontend lint passed.
Frontend build passed.
Provider secret leak scan passed.
OpenAI connect visual QA passed.
```

## Post-V1 Gated Slices

### Slice C Gate: Real Headless Device Flow

开启条件：

```text
OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted
OPENHARNESS_OPENAI_AUTH_MODE=real_headless
OPENHARNESS_OPENAI_EXPERIMENTAL=1
OPENHARNESS_OPENAI_CLIENT_ID=<approved client id>
```

验收标准：

- real device flow 使用真实 OpenAI auth base。
- 保存 token 前确认 secret store 是加密存储。
- 失败时不保存半成品 token。
- visual QA 标明 real mode，不混淆 mock mode。

### Slice D Gate: Real Browser PKCE Callback

开启条件：

```text
Slice C 已完成并稳定
OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted
OPENHARNESS_OPENAI_AUTH_MODE=real_browser
OPENHARNESS_OPENAI_EXPERIMENTAL=1
OPENHARNESS_OPENAI_CLIENT_ID=<approved client id>
```

验收标准：

- callback server 只接受 `/auth/callback`。
- state mismatch 必须失败且不保存 token。
- callback port 冲突时有清晰错误或安全 fallback。
- Electron 关闭或 wizard cancel 时关闭 callback server。

## Final Verification Matrix

稳定 V1 完成前必须全部为 true：

| Gate | Command Or Action | Required Result |
| --- | --- | --- |
| Backend contracts | `python -m pytest learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/tests/test_gui_provider_auth_attempts_contract.py learning_agent/tests/test_gui_provider_openai_auth_config.py learning_agent/tests/test_gui_bridge_security_contract.py -q` | all passed |
| Frontend tests | `npm --prefix apps/desktop test` | all passed |
| Frontend lint | `npm --prefix apps/desktop run lint` | passed |
| Frontend build | `npm --prefix apps/desktop run build` | passed |
| Secret scan | `powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1` | `Provider secret leak scan passed.` |
| Visual QA | `powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v2_openai_connect/scripts/capture_openai_connect_visual_qa.ps1` | `OpenAI connect visual QA passed.` |
| Real GUI | Manual visible Electron acceptance | screenshots saved, no visual blocker |

## Self-Review Checklist

- [ ] 稳定 V1 没有默认保存真实 OAuth refresh token。
- [ ] `auth-attempt` 命名在 endpoints、types、tests、docs 中一致。
- [ ] `display_code` 没有被误命名为旧确认码字段。
- [ ] status enum 只使用 `pending | complete | failed | expired`。
- [ ] auto mode 前端没有调用 `complete`。
- [ ] API Key 是唯一稳定真实连接路径。
- [ ] mock auth-attempt 有真实 UI、真实状态轮询和真实视觉验收。
- [ ] Provider catalog、renderer state、日志、截图、visual QA JSON 没有 raw key/token/secret_ref。
- [ ] 真实 OAuth 只作为 Post-V1 gated slices 记录，不被稳定 V1 冒进声明完成。

## Execution Handoff

执行本计划时从 Task 0 开始，按 Slice A、Slice B 推进。每个 task 完成后更新 `agent_memory/progress.md`。若执行中发现 mock auth-attempt、secret scan 或 visual QA 的 bug，先用 `superpowers:systematic-debugging` 修复并重跑对应 gate。稳定 V1 完成后，才允许评估是否进入 Slice C；没有加密 secret store 时，不进入真实 OAuth token 保存路径。
