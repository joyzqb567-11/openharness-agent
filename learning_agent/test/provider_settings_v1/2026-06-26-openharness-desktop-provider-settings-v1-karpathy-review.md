# OpenHarness Desktop Provider Settings V1 Karpathy-Style Review

评估对象：

```text
H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\docs\superpowers\plans\2026-06-26-openharness-desktop-provider-settings-v1.md
```

## 结论

这是一个方向正确的蓝图。它最好的地方是把“像 OpenCode 的设置界面”和“真实模型运行时切换”切开了。这个切分很重要。很多 AI 产品失败不是因为第一版不会画 UI，而是因为把 UI、密钥、安全、模型调用、错误恢复、验收全塞进同一个迭代，然后系统开始变得不可理解。

我会给它 **B+ / A-**。

不是因为它不够努力。它已经很完整。扣分点在于：它现在仍然更像一个漂亮的 deployment 前置壳，而不是一个成熟 provider substrate。真正成熟的系统要在“密钥存储、provider id 语义、custom provider 多实例、失败尾部场景、自动视觉验收”上更硬一点。

## 做得好的地方

1. **分层是对的**

V1 只做设置弹窗、provider catalog、auth contract、custom provider、model visibility，不碰 `GuiAgentAdapter` 和真实推理链路。这是正确的。真实模型连接是 Layer C，不应该混进视觉壳迭代。

2. **复用 OpenCode 的概念，而不是硬搬代码**

蓝图明确 OpenCode 是 SolidJS/serverSync/serverSDK，OpenHarness 是 React/Electron/bridge。这个判断对。复用数据模型和交互，不复用实现。

3. **TDD 和验收矩阵比较扎实**

后端 contract test、前端 client/store test、视觉 QA、release gate 都有。这比“先画出来再说”好很多。

4. **密钥不进 renderer 的方向是对的**

计划里反复强调 API key write-only、renderer 不拿原始 key、diagnostics 不暴露 key。这是成熟桌面壳的必要条件。

5. **保留了右侧 SettingsPanel 的定位**

左下角设置变成主设置入口，右侧 settings 保留为 diagnostics/local bridge 面板。这是好分工。

## 主要问题

### P0: 原始 API key 落盘到 JSON 文件，这不够成熟

当前计划里的持久化形状是：

```json
{
  "auth": {
    "openai": {
      "type": "api_key",
      "key": "raw secret saved only on disk"
    }
  }
}
```

这个是 demo 级做法，不是成熟桌面壳做法。真正成熟的桌面 provider 设置至少应该使用：

- Windows Credential Manager
- DPAPI
- keytar/electron safeStorage
- 或明确标注为 dev-only insecure store

建议升级：

- V1 改成 `GuiProviderSecretStore` 接口。
- 默认实现可以先是 `LocalEncryptedSecretStore` 或 `DevJsonSecretStore`。
- 如果继续用 JSON，必须命名成 `DevJsonSecretStore`，UI 和 diagnostics 都要显示“仅开发用途”。
- provider config 文件只保存 `secret_ref`，不保存 raw key。

这是一条红线。否则将来真实模型实验一接入，用户会把真 key 存进去。

### P0: `custom` 不应该既是 provider id，又是“新增自定义提供商”的入口

蓝图现在把 `custom` 放进 provider ids：

```text
github-copilot
openai
google
openrouter
vercel-ai-gateway
custom
```

这会产生语义混乱。`custom` 是一个 CTA row，不是一个真正 provider。真实 custom provider 应该有自己的 id，例如：

```text
local-openai-compatible
deepseek-compatible
my-company-gateway
```

建议升级：

- provider catalog 返回真实 providers。
- UI 额外渲染 `custom-provider-cta` 虚拟行。
- mutation endpoint 使用真实 custom id。
- model visibility key 只允许真实 provider id。

### P1: Provider id 和 OpenCode 对齐需要重新定一次

OpenCode 里 popular providers 包括 `vercel`，蓝图写的是 `vercel-ai-gateway`。这不是大错，但要早定。

建议：

- `id`: `vercel`
- `display_name`: `Vercel AI Gateway`
- `kind`: `built_in`

更一般地，id 应该短、稳定、用于配置；display name 才用于 UI。

### P1: GitHub Copilot 被放进 API key 连接流，可能误导

截图里 Copilot 是 provider，但实际连接方式通常不是简单 OpenAI API key 形态。蓝图把 V1 auth 都压成 API key，会导致 UI 看起来“支持连接”，实际体验很可能失败。

建议升级：

- 每个 provider 返回 `auth_methods` 的完整对象，而不是字符串数组。
- GitHub Copilot 在 V1 显示 `暂未支持` 或 `即将支持 OAuth/设备码`。
- OpenAI/OpenRouter/Vercel/custom 可以先支持 API key。
- Google 可以支持 API key，但要明确 Gemini key/base URL 模式。

### P1: 缺少“测试连接”这一层

用户想后续做真实大模型连接实验。那 provider 设置页需要一个中间层：

```text
保存 key != 模型可用
模型可用 != agent runtime 已切换
```

建议加 endpoint：

```text
POST /v2/gui/provider-settings/test-connection
```

V1 可以只做轻量测试：

- OpenAI-compatible: `GET /models` 或最小 metadata probe
- 不做真实 chat completion
- 返回 `ok / auth_failed / network_failed / unsupported`

这样将来 Layer C 不会盲接。

### P1: Release gate 的 secret scan 命令会误报

蓝图写：

```powershell
rg -n "sk-test-secret|Bearer test|api_key.*sk-|authorization.*Bearer" learning_agent apps/desktop
```

但是测试文件本来就会包含 `sk-test-secret`。命令本身会返回匹配，除非人工解释“这是 intentional test input”。这不是可自动化 gate。

建议：

- 测试 key 改成不符合真实 key 前缀的值，例如 `unit-test-secret-value`。
- 或把扫描拆成两步：
  - 源码扫描排除 tests/fixtures
  - 测试扫描只允许白名单文件
- release gate 必须有明确 exit code，不要靠人工读输出。

### P1: 视觉 QA 还是偏手工

Task 8 要求截图，但没有指定自动化工具和判断标准。对于 GUI shell，这会变成“看起来差不多”的主观验收。

建议：

- 加 Playwright 或复用现有浏览器 QA 工具。
- 固定 viewport：`1365x768`, `980x720`, `390x844`。
- 自动检查：
  - Settings dialog visible
  - Provider row count >= 6
  - no horizontal overflow
  - API key input type is password
  - no raw key text appears in DOM after submit

### P2: 文件写入需要 atomic write 和锁

provider settings 是会被 UI 快速点击写入的状态文件。计划里没有明确 atomic write。

建议：

- `save_provider_settings()` 写入临时文件，再 `replace()`。
- 后端 mutation 加 `threading.Lock`。
- JSON 读取失败时保留 `.corrupt-<timestamp>` 副本并返回安全错误。

### P2: 类型命名需要明确 snake_case 到 camelCase 的边界

后端 payload 是 `masked_key`，前端类型建议是 `maskedKey`。蓝图同时出现两种风格，但没有写转换边界。

建议：

- `guiProviderTypes.ts` 定义 backend raw type 和 view model type。
- `providerSettingsStore.ts` 负责从 snake_case 转 camelCase。
- React 组件只读 camelCase view model。

### P2: 没有把 AGENTS.md 的注释规则写入执行约束

这个项目有非常强的规则：新增/修改代码每行都要中文注释，并且复制到 `learning_agent/test`。蓝图虽然写了 evidence copy，但没有显式提醒每个任务必须遵守注释规则。

建议在蓝图顶部加：

```text
执行本计划时，所有新增/修改代码必须遵守 AGENTS.md 的逐行中文注释和 learning_agent/test 副本规则。
```

不然执行代理很容易只按普通工程习惯写代码。

## 建议升级版任务补丁

我建议在执行前把蓝图升级成下面这些结构：

1. **新增 Task 0: Provider Settings Invariants**

定义不可破坏的不变量：

- raw secret never leaves backend
- custom CTA is not a provider
- provider id is stable config key
- real runtime switching is Layer C
- every mutation returns redacted catalog

2. **替换 Task 2 的 secret persistence**

把 raw JSON key 改成 secret store abstraction：

```text
GuiProviderSecretStore
DevJsonSecretStore
WindowsCredentialSecretStore future
```

3. **新增 Task 2.5: Test Connection Contract**

先做连接探针，不接 agent runtime。

4. **修改 Task 5: Provider auth methods**

`auth_methods` 从字符串数组升级为对象数组：

```json
[
  {
    "id": "api_key",
    "label": "API 密钥",
    "enabled": true,
    "fields": ["api_key"]
  }
]
```

5. **修改 Task 8: Automated Visual QA**

明确自动截图工具、viewport 和 DOM assertions。

6. **修改 Task 9: Secret scan**

让 secret scan 变成可自动通过/失败的 gate。

## Go / No-Go

可以继续做，但我不会按现在这份原样执行。

最小升级项是：

- 修掉 raw key JSON 落盘设计。
- 把 `custom` 从 provider id 改成 CTA row。
- 加 provider auth method 对象。
- 加 test-connection contract。
- 把 secret scan 和 visual QA 变成可自动验收。

这些修完，这份蓝图就从“能做出来”变成“更可能不会在真实 provider 实验时塌掉”。
