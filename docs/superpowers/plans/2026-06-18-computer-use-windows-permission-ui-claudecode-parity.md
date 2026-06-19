# Windows Computer Use 权限 UI 体验 ClaudeCode 对齐蓝图

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to execute this plan when implementation begins.

**Goal:** 把 OpenHarness 的 Windows Computer Use 权限 UI 体验对齐 ClaudeCode 的核心行为，让用户在真实终端里能清楚看到“谁要控制什么应用、要哪些危险权限、有什么风险、批准或拒绝后系统会怎样记录”，并且让后端执行链路只能在明确授权后继续。

**Architecture:** 保留 OpenHarness 现有 Windows Computer Use MCP v2 工具面、Windows 后端、锁和清理机制，只重做权限 UI 合同、权限决策模型、终端展示、审计状态和验收门禁。不要复制 ClaudeCode 的 macOS TCC 权限实现，也不要依赖外部 `@ant/computer-use-mcp` 包。

**Tech Stack:** Python 3, pytest, OpenHarness `learning_agent`, Windows terminal interaction, existing Computer Use MCP v2 inferred Anthropic tool surface.

---

## 1. 背景结论

本蓝图只覆盖“权限 UI 体验”这一项，它值得对齐，而且优先级最高。

原因很直接：Computer Use 是真实鼠标、键盘、窗口、剪贴板能力。用户是否敢让 agent 操作电脑，不主要取决于底层动作是否已经能点按钮，而取决于每一次授权前是否看得懂、可拒绝、可审计、可追溯。ClaudeCode 在这里的强项不是某个 macOS API，而是权限请求被做成了明确的用户交互合同。

OpenHarness 当前已经有很好的底座：

- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/permissions.py` 已支持 `request_access` 和 `list_granted_applications`。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/approval_prompt.py` 已集中构造授权提示。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/claudecode_protocol.py` 已有 `apps`、`grantFlags`、`sentinelWarnings`、Windows sentinel 分类。
- `learning_agent/computer_use/approval.py` 已有 Windows 会话授权模型、grant flags 和终端状态摘要。

主要差距是：现在更像“把结构化 JSON 打印给用户”，还不是一个成熟的权限 UI 体验。

---

## 2. 对齐原则

### 必须对齐的 ClaudeCode 行为

1. 用户能在授权前看懂目标应用。
2. 用户能在授权前看懂危险权限。
3. 用户能看到高风险应用提示，例如终端、资源管理器、系统设置、注册表。
4. 用户可以批准，也可以拒绝。
5. 拒绝必须阻断后续 Computer Use 动作。
6. 授权结果必须进入会话状态，后续工具调用能检查。
7. `list_granted_applications` 或状态面板必须能解释当前授权。
8. 权限提示必须适合真实终端，不要求 React/Ink 图形 UI。

### 不需要对齐的内容

1. 不对齐 macOS TCC 权限弹窗。
2. 不对齐 ClaudeCode 隐藏包内部私有实现。
3. 不引入外部 `@ant/computer-use-mcp` 包。
4. 不把 Windows 变成 macOS 式 bundle 权限，只保留 ClaudeCode 风格字段名和用户体验。
5. 不在本阶段重写截图、SendInput、锁、清理、浏览器能力。

---

## 3. 当前缺口矩阵

| 编号 | 当前状态 | 差距 | 对齐目标 | 优先级 |
|---|---|---|---|---|
| CU-PERM-001 | prompt 是中文标题加 JSON | 用户不容易一眼判断风险 | 改为终端权限面板 | P0 |
| CU-PERM-002 | `ask_permission` 主要是 bool | 无法表达批准但关闭部分 grant flag | 支持结构化权限决策，同时兼容 bool | P0 |
| CU-PERM-003 | 无 callback 时当前偏默认允许 | 生产安全边界不够强 | 无交互 callback 默认拒绝，诊断模式必须显式标注 | P0 |
| CU-PERM-004 | sentinel 有基础分类 | UI 提示还不够像用户可读风险说明 | 每类风险有中文解释和建议 | P0 |
| CU-PERM-005 | `list_granted` 有基础字段 | 缺少 prompt 版本、决策来源、拒绝原因、时间 | 输出完整授权审计摘要 | P1 |
| CU-PERM-006 | `approval.py` 和 MCP v2 权限层并存 | 两套权限状态容易漂移 | 明确桥接关系和字段映射 | P1 |
| CU-PERM-007 | 旧测试更偏接口和执行 | 缺少真实权限 UI 合同测试 | 增加 prompt、decision、terminal acceptance 测试 | P0 |

---

## 4. 目标用户体验

真实终端中，当 agent 想使用 Computer Use 控制 Windows 应用时，用户应看到类似以下信息结构。

```text
[Computer Use 权限请求]

Agent 想在本会话中控制以下 Windows 应用：
1. 记事本
   身份: notepad.exe
   风险: 普通桌面应用

本次请求的危险权限：
- 读取剪贴板: 否
- 写入剪贴板: 是
- 系统组合键: 否

申请原因：
需要在记事本中输入用户指定的文本。

请选择：
y = 允许本会话控制这些应用
n = 拒绝
```

当请求高风险目标时，用户应看到更强提示。

```text
[Computer Use 权限请求]

Agent 想在本会话中控制以下 Windows 应用：
1. PowerShell
   身份: powershell.exe
   风险: shell，可以运行命令、修改文件、启动程序

安全建议：
除非你明确知道 agent 要执行什么命令，否则建议拒绝。

请选择：
y = 允许本会话控制这些应用
n = 拒绝
```

注意：最终实现不要求逐字等于上面的文本，但必须满足信息结构和验收断言。

---

## 5. 新权限数据合同

### 输入合同

`request_access` 必须继续接受 ClaudeCode 风格字段。

| 字段 | 类型 | 说明 |
|---|---|---|
| `apps` | list[object] | 推荐输入，包含 `displayName` 和 `bundleId` |
| `applications` | list[string] | 旧兼容输入 |
| `grantFlags` | object | 包含 `clipboardRead`、`clipboardWrite`、`systemKeyCombos` |
| `reason` | string | 申请原因 |

### 决策合同

新增结构化决策对象，bool 仍保持兼容。

| 字段 | 类型 | 说明 |
|---|---|---|
| `approved` | bool | 是否允许 |
| `decision` | string | `allow_for_session`、`deny`、`allow_with_reduced_flags` |
| `grantedApps` | list[object] | 实际批准的应用 |
| `deniedApps` | list[object] | 被拒绝的应用 |
| `grantFlags` | object | 实际批准的危险权限 |
| `reason` | string | 用户拒绝或系统降级原因 |
| `source` | string | `terminal_prompt`、`legacy_bool_callback`、`noninteractive_default_deny` |
| `promptVersion` | string | 权限提示版本，例如 `windows-permission-ui-v1` |
| `timestampUtc` | string | ISO 时间 |

### 输出合同

批准时，`request_access` 返回 payload 至少包含：

| 字段 | 说明 |
|---|---|
| `grantedApps` | 本次授权应用 |
| `grantFlags` | 本次授权 flags |
| `sentinelWarnings` | 高风险提示 |
| `decision` | 决策类型 |
| `promptVersion` | 提示版本 |
| `source` | 决策来源 |

拒绝时，`request_access` 返回 `error_class="permission_denied"`，payload 至少包含：

| 字段 | 说明 |
|---|---|
| `deniedApps` | 被拒绝应用 |
| `sentinelWarnings` | 高风险提示 |
| `reason` | 拒绝原因 |
| `decision` | `deny` 或 `noninteractive_default_deny` |
| `promptVersion` | 提示版本 |
| `source` | 决策来源 |

---

## 6. 文件级设计

### 6.1 修改 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/approval_prompt.py`

目标：从 JSON prompt 升级为稳定的终端权限面板。

需要新增或调整的函数：

| 函数 | 责任 |
|---|---|
| `build_computer_use_approval_prompt(...)` | 保持现有入口，返回用户可读面板 |
| `_format_application_rows(...)` | 把应用列表转成编号行 |
| `_format_grant_flags(...)` | 把 grant flags 转成中文危险权限说明 |
| `_format_sentinel_warnings(...)` | 把 sentinel 分类转成中文风险说明 |
| `_safe_reason(...)` | 限制 reason 长度，避免 prompt 被过长文本污染 |

实现要求：

- 不删除现有入口函数，避免调用方断裂。
- 输出必须包含 `Computer Use 权限请求`。
- 输出必须包含应用展示名和身份。
- 输出必须包含 grant flags 中文名。
- 输出必须包含 sentinel warning 中文解释。
- 输出必须包含明确选择说明。
- 不再把完整 payload 作为主要 UI。

### 6.2 新增 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/approval_decision.py`

目标：集中处理 bool 回调、dict 回调、无交互默认拒绝，避免 `permissions.py` 继续变复杂。

建议公开函数：

| 函数 | 责任 |
|---|---|
| `normalize_permission_decision(raw_decision, requested_apps, requested_flags, sentinel_warnings)` | 把 bool 或 dict 变成统一结构 |
| `default_denied_decision(requested_apps, requested_flags, sentinel_warnings, reason)` | 无交互或异常时生成拒绝 |
| `approved_decision(...)` | 生成批准结构 |
| `denied_decision(...)` | 生成拒绝结构 |

接口草案：

```python
# 新增代码+PermissionUIDecision：定义提示版本常量；如果没有这行代码，审计记录无法知道用户看到的是哪一版权限 UI。
PROMPT_VERSION = "windows-permission-ui-v1"

# 新增代码+PermissionUIDecision：函数段开始，统一 bool 或 dict 权限决策；如果没有这段函数，permissions.py 会继续混合 UI、解析、授权写入三种职责。
def normalize_permission_decision(raw_decision, requested_apps, requested_flags, sentinel_warnings):
    # 新增代码+PermissionUIDecision：这里接收 ask_permission 的原始返回值；如果没有这行逻辑，旧 bool 回调和未来结构化回调无法兼容。
    ...
# 新增代码+PermissionUIDecision：函数段结束，normalize_permission_decision 到此结束；如果没有这个边界说明，用户不容易看出权限决策解析范围。
```

注意：真正实现时每一行新代码都必须按项目规则补中文注释，本草案只是说明函数边界。

### 6.3 修改 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/permissions.py`

目标：把 `request_access` 改成“构造请求 -> 展示 prompt -> 解析决策 -> 写入授权或拒绝”的清晰链路。

必须保持：

- `request_access(context, arguments)` 入口不变。
- 旧字段 `applications` 继续兼容。
- `apps` 和 `grantFlags` 继续使用 ClaudeCode 风格字段。
- 成功时仍写入 `context.allowed_apps`、`context.grant_flags`、`context.sentinel_warnings`、`context.grants`。

必须新增：

- `context.permission_decisions` 或等价审计列表。
- `context.permission_prompt_version` 或每条 grant 记录带 `promptVersion`。
- 无 `ask_permission` callback 时默认拒绝，并把 `source` 标为 `noninteractive_default_deny`。
- 对 `ask_permission` 抛异常的情况默认拒绝，并返回可读错误原因。

### 6.4 修改 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py`

目标：确保 runtime 透传新的授权 payload，不吞掉 `decision`、`source`、`promptVersion` 等字段。

检查点：

- `request_access` 调用路径不能被锁误阻塞。
- `list_granted_applications` 能返回新审计字段。
- 错误结果保留 `permission_denied`。

### 6.5 修改 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py`

目标：确保真实 agent 会话注入的 `ask_permission` 是终端可见交互，而不是隐藏默认允许。

检查点：

- 真实启动链路必须有用户可见提示。
- 测试模式可以注入假 `ask_permission`，但测试名称必须说明是 fake。
- 若存在非交互模式，必须显示 `noninteractive_default_deny`。

### 6.6 修改 `learning_agent/computer_use/approval.py`

目标：让旧 Windows approval model 和 MCP v2 权限 UI 语义不漂移。

处理方式：

- 不重写此文件的核心审批模型。
- 补充状态字段，让 `/computer status` 或等价状态输出能显示 prompt version、最近决策、拒绝次数。
- 确认 `grant_flags` 名称和 MCP v2 完全一致。

---

## 7. 测试蓝图

### 7.1 新增 prompt 合同测试

文件：`learning_agent/tests/test_computer_use_permission_ui_prompt.py`

必须覆盖：

- 普通应用请求显示应用名、身份、reason、grant flags。
- PowerShell 请求显示 shell 风险中文说明。
- Explorer 请求显示 filesystem 风险中文说明。
- Regedit 请求显示 system_settings 风险中文说明。
- reason 很长时被裁剪。
- prompt 不只是一段 JSON。

建议测试命令：

```powershell
python -m pytest learning_agent/tests/test_computer_use_permission_ui_prompt.py -q
```

### 7.2 新增决策归一化测试

文件：`learning_agent/tests/test_computer_use_permission_decision.py`

必须覆盖：

- bool `True` 转成 `allow_for_session`。
- bool `False` 转成 `deny`。
- dict 决策可以关闭 `clipboardRead` 等危险 flag。
- dict 决策不能注入未知 grant flag。
- 无 callback 场景生成 `noninteractive_default_deny`。
- callback 异常场景生成拒绝。

建议测试命令：

```powershell
python -m pytest learning_agent/tests/test_computer_use_permission_decision.py -q
```

### 7.3 修改 MCP v2 权限测试

可能涉及文件：

- `learning_agent/tests/test_computer_use_mcp_v2_permissions.py`
- `learning_agent/tests/test_computer_use_mcp_v2_runtime.py`

必须覆盖：

- `request_access` 成功 payload 包含 `decision`、`source`、`promptVersion`。
- `request_access` 拒绝 payload 包含 `deniedApps` 和 `permission_denied`。
- `list_granted_applications` 能展示最近授权和 flags。
- `applications` 旧字段仍兼容。
- `apps` 新字段优先保留 `displayName` 和 `bundleId`。

建议测试命令：

```powershell
python -m pytest learning_agent/tests/test_computer_use_mcp_v2_permissions.py learning_agent/tests/test_computer_use_mcp_v2_runtime.py -q
```

### 7.4 自动化回归命令

实现完成后至少运行：

```powershell
python -m pytest learning_agent/tests/test_computer_use_permission_ui_prompt.py learning_agent/tests/test_computer_use_permission_decision.py -q
python -m pytest learning_agent/tests/test_computer_use_mcp_v2_permissions.py learning_agent/tests/test_computer_use_mcp_v2_runtime.py -q
python -m py_compile learning_agent/computer_use_mcp_v2/inferred_ant_mcp/approval_prompt.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/approval_decision.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/permissions.py
```

### 7.5 真实可见终端验收

因为本仓库规则要求真实终端验收，后续只要实现代码，就必须执行：

```powershell
Start-Process -FilePath "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat"
```

真实终端里输入的验收 prompt 建议：

```text
请使用 computer use 打开记事本，并在获得我确认后输入一句：OpenHarness 权限 UI 验收通过。
```

必须观察到：

1. 终端出现 Computer Use 权限请求。
2. 提示中能看到目标应用、授权原因、grant flags。
3. 输入拒绝时，agent 不执行桌面动作。
4. 再次请求并输入允许时，agent 执行动作。
5. 后续状态能看到本会话授权。

高风险验收 prompt 建议：

```text
请使用 computer use 控制 PowerShell。
```

必须观察到：

1. 权限 UI 显示 shell 风险说明。
2. 用户拒绝后，agent 不得继续控制 PowerShell。
3. 输出要说明是权限拒绝，而不是工具崩溃。

如果当前环境无法打开、观察或输入真实可见终端，最终回答必须写：

```text
真实可见终端交互验收未完成，不能声明开发完成。
```

---

## 8. 执行任务清单

### 阶段 A：冻结现状和补合同

- [ ] 用 CodeGraph 读取 `permissions.py`、`approval_prompt.py`、`claudecode_protocol.py`、`runtime.py`、`bind_session_context.py`、`approval.py`。
- [ ] 记录当前 `request_access` 的成功和拒绝 payload。
- [ ] 确认旧测试名称和覆盖范围。
- [ ] 在 `agent_memory/progress.md` 记录本阶段开始。
- [ ] 如发现现有 bug，先写入 `agent_memory/bugs.md`，不要直接猜测式修改。

完成条件：能清楚说明当前权限请求从 MCP tool 到 `ask_permission` 再到 context grant 的全链路。

### 阶段 B：先写测试

- [ ] 新增 `test_computer_use_permission_ui_prompt.py`。
- [ ] 新增 `test_computer_use_permission_decision.py`。
- [ ] 扩展现有 MCP v2 permissions/runtime 测试。
- [ ] 确认新增测试在当前代码上至少有一部分失败，失败点对应本蓝图缺口。

完成条件：失败测试能证明权限 UI 缺口，而不是测试写错。

### 阶段 C：实现终端权限面板

- [ ] 修改 `approval_prompt.py`。
- [ ] 普通应用、shell、filesystem、system_settings 都有中文说明。
- [ ] reason 做长度限制。
- [ ] 保留 `build_computer_use_approval_prompt` 入口。
- [ ] 所有新写和修改代码按项目规则逐行中文注释。
- [ ] 把新写和修改代码另存到 `learning_agent/test` 下，供用户学习。

完成条件：prompt 合同测试通过。

### 阶段 D：实现结构化决策模型

- [ ] 新增 `approval_decision.py`。
- [ ] 支持 bool legacy callback。
- [ ] 支持 dict structured callback。
- [ ] 支持 unknown flag 过滤。
- [ ] 支持无 callback 默认拒绝。
- [ ] 支持 callback 异常默认拒绝。
- [ ] 所有新写代码按项目规则逐行中文注释。
- [ ] 把新写代码另存到 `learning_agent/test` 下。

完成条件：决策归一化测试通过。

### 阶段 E：接入 `request_access`

- [ ] 修改 `permissions.py` 使用新的 prompt 和 decision。
- [ ] 成功时写入 grant 状态和审计字段。
- [ ] 拒绝时返回 `permission_denied`。
- [ ] 无 callback 时不再静默允许。
- [ ] `list_granted_applications` 返回 prompt version、source、decision、timestamp。
- [ ] 所有新写和修改代码按项目规则逐行中文注释。
- [ ] 把新写和修改代码另存到 `learning_agent/test` 下。

完成条件：MCP v2 permissions/runtime 测试通过。

### 阶段 F：接入真实终端链路

- [ ] 检查 `bind_session_context.py` 的真实 `ask_permission` 注入。
- [ ] 检查 agent 启动链路是否能把 prompt 打到用户可见终端。
- [ ] 检查 `/computer status` 或等价状态输出是否显示权限摘要。
- [ ] 如果发现真实终端无法显示权限 UI，暂停并汇报治本方案。

完成条件：真实启动链路不是 hidden allow，也不是仅日志输出。

### 阶段 G：验收和收尾

- [ ] 运行全部指定 pytest。
- [ ] 运行 py_compile。
- [ ] 启动真实可见终端 `start_oauth_agent.bat`。
- [ ] 完成普通应用允许/拒绝验收。
- [ ] 完成 PowerShell 高风险拒绝验收。
- [ ] 更新 `agent_memory/progress.md`。
- [ ] 如发现重复经验，更新 `agent_memory/experience.md`。
- [ ] 最终回答明确列出已完成测试和未完成风险。

完成条件：代码修改完成、自动化测试通过、真实可见终端交互测试通过。三者缺一不可。

---

## 9. 停止条件

实现过程中遇到以下任一情况，必须停止并汇报，不继续堆补丁：

1. 真实终端链路没有可见 `ask_permission` 入口。
2. `request_access` 和旧 `approval.py` 状态出现互相覆盖或互相矛盾。
3. 无法确认拒绝后是否真正阻断桌面动作。
4. 高风险应用被 UI 提示为普通应用。
5. 为了对齐 ClaudeCode 需要引入外部 MCP 包或 macOS 专属逻辑。
6. 修改范围开始触及截图、SendInput、浏览器、OAuth 等无关模块。
7. 测试通过但真实终端无法验收。

---

## 10. 成功标准

最终实现完成后，应满足：

- 用户在 Windows 真实终端能看懂每次 Computer Use 权限请求。
- 用户拒绝后，Computer Use 不执行真实桌面动作。
- 用户允许后，只允许本会话、本应用、本次批准的 grant flags。
- 高风险应用有醒目风险说明。
- `list_granted_applications` 或状态面板能解释当前授权。
- 自动化测试覆盖普通授权、拒绝、高风险、旧字段兼容、无交互默认拒绝。
- 不依赖 ClaudeCode 隐藏包，不依赖 macOS TCC。

---

## 11. 推荐实施顺序

第一轮只做 P0：

1. prompt UI 面板。
2. 结构化 decision。
3. 无交互默认拒绝。
4. `request_access` 成功/拒绝 payload。
5. 真实终端验收。

第二轮再做 P1：

1. 状态面板美化。
2. 审计记录增强。
3. 与旧 `approval.py` 的深度统一。
4. 更多 sentinel 分类。

这样拆分可以最大限度防止长任务跑偏：第一轮只解决“用户授权体验是否可信”这个核心问题，先把安全门装牢，再扩展状态和审计细节。
