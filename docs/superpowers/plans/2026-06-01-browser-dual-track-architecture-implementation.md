# Browser Dual Track Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 learning_agent 的真实浏览器能力改造成“底层双轨、模型表面单轨”的 Browser Provider 架构，先完成 Provider Protocol 和 Router 代码级防误选基础。

**Architecture:** 本计划以 `docs/superpowers/specs/2026-06-01-browser-dual-track-architecture-blueprint.md` 为唯一设计依据。第一轮只做 Stage 1：新增 provider 协议、registry、router、provider decision 事件和单元测试，不改变现有浏览器工具行为；Chrome 插件、native host、tabs context、权限 UI 和 GIF 证据在后续阶段独立实施。

**Tech Stack:** Python、unittest、learning_agent browser runtime、JSON/JSONL event store、PowerShell acceptance controller、`learning_agent/start_oauth_agent.bat` 真实可见终端验收。

---

## 0. 执行边界

这份计划是双轨浏览器改造的主实施计划。为了防止长任务跑偏，本计划把工作分为两层：

1. **Stage 1 详细执行计划**：可直接开始编码，目标是建立 Provider Protocol 和 Router 空实现，不改变现有工具行为。
2. **Stage 2 到 Stage 12 阶段门禁**：每个阶段开始前必须单独生成更细的阶段计划，不能直接跳到插件或 native host 大改。

当前工作区已有大量未提交和未跟踪文件。执行本计划时不得回滚用户或其他 agent 的既有改动。除非用户明确要求提交，否则每个阶段只更新文件、测试、进度记录，不自动 `git commit`。

所有真实功能改动完成后，必须满足项目 AGENTS 规则：代码修改完成、自动化测试通过、独立 verifier 通过、`H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat` 真实可见终端交互验收通过，才允许声明开发完成。

## 1. 文件结构锁定

Stage 1 需要创建和修改这些文件：

- Create: `learning_agent/browser/providers/__init__.py`
- Create: `learning_agent/browser/providers/protocol.py`
- Create: `learning_agent/browser/providers/registry.py`
- Create: `learning_agent/browser/providers/router.py`
- Create: `learning_agent/browser/providers/provider_events.py`
- Create: `learning_agent/tests/test_browser_provider_router.py`
- Modify: `learning_agent/browser/runtime_events.py`
- Modify: `learning_agent/browser/__init__.py`
- Modify: `agent_memory/progress.md`
- Create: `learning_agent/test/browser_dual_track_stage1_20260601/modified_snippets.md`

Stage 1 不修改这些高风险文件，除非测试证明必须：

- `learning_agent/browser_automation_mcp_server.py`
- `learning_agent/core/agent.py`
- `learning_agent/browser_real_chrome.py`

这样可以保证 Stage 1 是低风险架构地基，不会误伤现有真实浏览器执行路径。

## 2. Stage 1 成功标准

Stage 1 完成后必须满足：

1. `BrowserProviderKind` 能表达 `visible_chromium`、`real_chrome_cdp`、`chrome_extension`、`unavailable`。
2. `BrowserProviderRouter.decide_provider(...)` 能根据公开网页、当前 Chrome、CDP 调试、本地开发、插件不可用降级等场景返回稳定 provider。
3. 路由结果包含 `provider`、`reason`、`fallback_provider`、`requires_user_confirmation`、`event_payload`。
4. 新增 `BROWSER_PROVIDER_DECISION` 事件常量，且纳入 `BROWSER_RUNTIME_EVENT_TYPES`。
5. 现有浏览器工具行为不改变。
6. 自动化测试通过。
7. 因 Stage 1 是运行时代码修改，最终必须通过真实可见终端验收后才能说 Stage 1 完成。

## 3. Stage 1 详细任务

### Task 1: 写 Provider Router 红灯测试

**Files:**
- Create: `learning_agent/tests/test_browser_provider_router.py`

- [ ] **Step 1: 创建测试文件**

写入以下测试。注意：实际写入代码时每一行都要保留中文注释，符合 AGENTS 规则。

```python
"""浏览器 provider router 测试。"""  # 新增代码+BrowserProviderRouter: 说明本文件锁定双轨浏览器路由规则；若没有这行代码，维护者不知道测试保护哪条架构原则。

from __future__ import annotations  # 新增代码+BrowserProviderRouter: 延迟解析类型注解；若没有这行代码，后续类型引用在旧解释顺序下更脆弱。

from learning_agent.tests.support import *  # 新增代码+BrowserProviderRouter: 复用项目测试基类和临时目录 helper；若没有这行代码，测试会重复公共准备逻辑。


class BrowserProviderRouterTests(LearningAgentTestBase):  # 新增代码+BrowserProviderRouter: 定义 provider router 测试集合；若没有这个类，unittest 不会发现本组路由规则测试。
    def test_public_web_query_defaults_to_visible_chromium(self) -> None:  # 新增代码+BrowserProviderRouter: 验证公开网页查询默认走隔离可见浏览器；若没有这行代码，模型可能误碰用户真实 Chrome。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型和健康状态；若没有这行代码，测试无法构造 provider 输入。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+BrowserProviderRouter: 导入被测路由器；若没有这行代码，测试无法锁定公开 API。
        router = BrowserProviderRouter()  # 新增代码+BrowserProviderRouter: 创建默认路由器；若没有这行代码，无法执行 provider 决策。
        health = {BrowserProviderKind.VISIBLE_CHROMIUM: BrowserProviderHealth.available(BrowserProviderKind.VISIBLE_CHROMIUM)}  # 新增代码+BrowserProviderRouter: 声明可见 Chromium 可用；若没有这行代码，路由器没有健康输入。
        decision = router.decide_provider(user_input="帮我查询明天武汉天气", tool_name="browser_open", arguments={"url": "https://www.baidu.com"}, provider_health=health)  # 新增代码+BrowserProviderRouter: 模拟公开网页查询；若没有这行代码，无法验证默认路线。
        self.assertEqual(decision.provider, BrowserProviderKind.VISIBLE_CHROMIUM)  # 新增代码+BrowserProviderRouter: 断言公开查询走可见 Chromium；若没有这行代码，默认路线错误不会报红。
        self.assertFalse(decision.requires_user_confirmation)  # 新增代码+BrowserProviderRouter: 断言低风险公开查询不需要额外确认；若没有这行代码，普通查询可能被不必要打断。

    def test_current_chrome_login_state_prefers_extension(self) -> None:  # 新增代码+BrowserProviderRouter: 验证当前 Chrome 登录态任务优先插件 provider；若没有这行代码，登录态任务可能误走 CDP 或独立浏览器。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型和健康状态；若没有这行代码，测试无法表示插件可用。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+BrowserProviderRouter: 导入被测路由器；若没有这行代码，测试无法执行路由。
        router = BrowserProviderRouter()  # 新增代码+BrowserProviderRouter: 创建默认路由器；若没有这行代码，无法得到 provider 决策。
        health = {BrowserProviderKind.CHROME_EXTENSION: BrowserProviderHealth.available(BrowserProviderKind.CHROME_EXTENSION), BrowserProviderKind.REAL_CHROME_CDP: BrowserProviderHealth.available(BrowserProviderKind.REAL_CHROME_CDP)}  # 新增代码+BrowserProviderRouter: 同时声明插件和 CDP 可用；若没有这行代码，无法证明插件优先级高于 CDP。
        decision = router.decide_provider(user_input="使用我当前 Chrome 已登录账号查看订单", tool_name="browser_snapshot", arguments={}, provider_health=health)  # 新增代码+BrowserProviderRouter: 模拟当前 Chrome 登录态任务；若没有这行代码，插件优先规则没有输入。
        self.assertEqual(decision.provider, BrowserProviderKind.CHROME_EXTENSION)  # 新增代码+BrowserProviderRouter: 断言插件优先；若没有这行代码，核心双轨策略可能失效。
        self.assertIn("登录态", decision.reason)  # 新增代码+BrowserProviderRouter: 断言原因文本可审计；若没有这行代码，event log 难以解释决策。

    def test_extension_unavailable_does_not_silently_fallback_without_permission(self) -> None:  # 新增代码+BrowserProviderRouter: 验证插件不可用时不能静默降级；若没有这行代码，真实 Chrome 登录态任务可能误走 CDP。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型和健康状态；若没有这行代码，测试无法表达插件不可用。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+BrowserProviderRouter: 导入被测路由器；若没有这行代码，无法测试 fallback。
        router = BrowserProviderRouter()  # 新增代码+BrowserProviderRouter: 创建默认路由器；若没有这行代码，无法执行路由。
        health = {BrowserProviderKind.CHROME_EXTENSION: BrowserProviderHealth.unavailable(BrowserProviderKind.CHROME_EXTENSION, "extension_not_connected"), BrowserProviderKind.REAL_CHROME_CDP: BrowserProviderHealth.available(BrowserProviderKind.REAL_CHROME_CDP)}  # 新增代码+BrowserProviderRouter: 插件不可用但 CDP 可用；若没有这行代码，无法验证不静默降级。
        decision = router.decide_provider(user_input="使用我当前 Chrome 登录态打开网页", tool_name="browser_open", arguments={"url": "https://example.com"}, provider_health=health)  # 新增代码+BrowserProviderRouter: 模拟登录态任务；若没有这行代码，fallback 规则没有触发条件。
        self.assertEqual(decision.provider, BrowserProviderKind.UNAVAILABLE)  # 新增代码+BrowserProviderRouter: 断言没有用户许可时返回不可用；若没有这行代码，静默降级风险不会被捕获。
        self.assertEqual(decision.fallback_provider, BrowserProviderKind.REAL_CHROME_CDP)  # 新增代码+BrowserProviderRouter: 断言 CDP 只是候选 fallback；若没有这行代码，用户无法知道可选路线。
        self.assertTrue(decision.requires_user_confirmation)  # 新增代码+BrowserProviderRouter: 断言需要用户确认；若没有这行代码，高风险降级可能直接执行。

    def test_explicit_cdp_debug_request_uses_real_chrome_cdp(self) -> None:  # 新增代码+BrowserProviderRouter: 验证明确 CDP 调试请求走 CDP provider；若没有这行代码，调试任务可能被插件拦截。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型和健康状态；若没有这行代码，测试无法声明 CDP 可用。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+BrowserProviderRouter: 导入路由器；若没有这行代码，无法执行 CDP 规则。
        router = BrowserProviderRouter()  # 新增代码+BrowserProviderRouter: 创建默认路由器；若没有这行代码，无法得到决策。
        health = {BrowserProviderKind.REAL_CHROME_CDP: BrowserProviderHealth.available(BrowserProviderKind.REAL_CHROME_CDP)}  # 新增代码+BrowserProviderRouter: 声明 CDP 可用；若没有这行代码，路由器会缺健康输入。
        decision = router.decide_provider(user_input="使用 CDP 调试端口连接真实 Chrome", tool_name="browser_connect_real_chrome", arguments={"confirm_real_profile": True}, provider_health=health)  # 新增代码+BrowserProviderRouter: 模拟显式 CDP 请求；若没有这行代码，CDP 规则无法验证。
        self.assertEqual(decision.provider, BrowserProviderKind.REAL_CHROME_CDP)  # 新增代码+BrowserProviderRouter: 断言显式 CDP 走 CDP provider；若没有这行代码，调试入口可能走错。

    def test_decision_payload_is_event_log_ready(self) -> None:  # 新增代码+BrowserProviderRouter: 验证决策能直接写 event log；若没有这行代码，状态生态无法复盘 provider 选择。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型和健康状态；若没有这行代码，测试无法构造路由输入。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+BrowserProviderRouter: 导入被测路由器；若没有这行代码，无法生成事件 payload。
        router = BrowserProviderRouter()  # 新增代码+BrowserProviderRouter: 创建默认路由器；若没有这行代码，无法得到决策。
        health = {BrowserProviderKind.VISIBLE_CHROMIUM: BrowserProviderHealth.available(BrowserProviderKind.VISIBLE_CHROMIUM)}  # 新增代码+BrowserProviderRouter: 声明可见 Chromium 可用；若没有这行代码，路由器没有健康输入。
        decision = router.decide_provider(user_input="打开本地 localhost 页面", tool_name="browser_open", arguments={"url": "http://localhost:3000"}, provider_health=health)  # 新增代码+BrowserProviderRouter: 模拟本地开发任务；若没有这行代码，事件 payload 没有具体样本。
        payload = decision.to_event_payload()  # 新增代码+BrowserProviderRouter: 转换为事件 payload；若没有这行代码，无法验证 event log 格式。
        self.assertEqual(payload["provider"], "visible_chromium")  # 新增代码+BrowserProviderRouter: 断言 provider 使用稳定字符串；若没有这行代码，外部 agent 难以解析。
        self.assertEqual(payload["tool_name"], "browser_open")  # 新增代码+BrowserProviderRouter: 断言工具名进入事件；若没有这行代码，审计不知道哪个工具触发决策。
        self.assertIn("reason", payload)  # 新增代码+BrowserProviderRouter: 断言原因字段存在；若没有这行代码，用户无法理解 provider 选择。
```

- [ ] **Step 2: 运行红灯测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_browser_provider_router
```

Expected:

```text
ModuleNotFoundError: No module named 'learning_agent.browser.providers'
```

### Task 2: 创建 Provider Protocol

**Files:**
- Create: `learning_agent/browser/providers/__init__.py`
- Create: `learning_agent/browser/providers/protocol.py`

- [ ] **Step 1: 创建 provider 包入口**

`learning_agent/browser/providers/__init__.py` 应导出稳定类型。实际实现时每一行都加中文注释。

```python
"""浏览器 provider 包公开入口。"""  # 新增代码+BrowserProviderRouter: 说明本包承载双轨浏览器 provider 抽象；若没有这行代码，维护者不知道 provider 边界。

from .protocol import BrowserProviderDecision, BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导出路由决策、健康状态和 provider 类型；若没有这行代码，外部测试要深入子模块导入。

__all__ = ["BrowserProviderDecision", "BrowserProviderHealth", "BrowserProviderKind"]  # 新增代码+BrowserProviderRouter: 固定公开 API；若没有这行代码，外部 agent 难以判断哪些名字稳定。
```

- [ ] **Step 2: 创建协议模型**

`learning_agent/browser/providers/protocol.py` 应包含以下数据结构。

```python
"""浏览器 provider 协议模型。"""  # 新增代码+BrowserProviderRouter: 说明本文件只定义 provider 类型和路由结果；若没有这行代码，执行逻辑容易混入协议层。

from __future__ import annotations  # 新增代码+BrowserProviderRouter: 延迟解析类型注解；若没有这行代码，类之间互相引用时更脆弱。

from dataclasses import dataclass  # 新增代码+BrowserProviderRouter: 使用 dataclass 表示小型不可变决策对象；若没有这行代码，需要手写初始化样板代码。
from enum import Enum  # 新增代码+BrowserProviderRouter: 使用枚举固定 provider 名称；若没有这行代码，字符串拼写错误难以及早发现。
from typing import Any  # 新增代码+BrowserProviderRouter: event payload 是 JSON 风格字典；若没有这行代码，类型标注无法表达通用字段。


class BrowserProviderKind(str, Enum):  # 新增代码+BrowserProviderRouter: 定义浏览器 provider 类型；若没有这个类，路由器只能使用容易拼错的裸字符串。
    VISIBLE_CHROMIUM = "visible_chromium"  # 新增代码+BrowserProviderRouter: 表示隔离可见 Chromium；若没有这项，公开网页和本地调试没有默认 provider。
    REAL_CHROME_CDP = "real_chrome_cdp"  # 新增代码+BrowserProviderRouter: 表示真实 Chrome CDP 调试路线；若没有这项，显式 CDP 请求无法表达。
    CHROME_EXTENSION = "chrome_extension"  # 新增代码+BrowserProviderRouter: 表示 Chrome 插件 provider；若没有这项，登录态和当前 Chrome 路线无法表达。
    UNAVAILABLE = "unavailable"  # 新增代码+BrowserProviderRouter: 表示没有可安全执行的 provider；若没有这项，插件不可用时容易静默降级。


@dataclass(frozen=True)  # 新增代码+BrowserProviderRouter: 冻结健康状态对象避免路由中被意外修改；若没有这行代码，测试和事件可能看到被污染的状态。
class BrowserProviderHealth:  # 新增代码+BrowserProviderRouter: 表示某个 provider 当前是否可用；若没有这个类，路由器无法区分插件未安装和可用。
    kind: BrowserProviderKind  # 新增代码+BrowserProviderRouter: 保存 provider 类型；若没有这行代码，健康状态无法对应具体 provider。
    available: bool  # 新增代码+BrowserProviderRouter: 保存是否可用；若没有这行代码，路由器无法判断能否选择。
    reason: str = ""  # 新增代码+BrowserProviderRouter: 保存不可用或可用原因；若没有这行代码，状态输出不可审计。

    @classmethod  # 新增代码+BrowserProviderRouter: 提供可读构造入口；若没有这行代码，测试会重复传 available=True。
    def available(cls, kind: BrowserProviderKind, reason: str = "available") -> "BrowserProviderHealth":  # 新增代码+BrowserProviderRouter: 构造可用健康状态；若没有这行代码，调用方需要手写布尔值。
        return cls(kind=kind, available=True, reason=reason)  # 新增代码+BrowserProviderRouter: 返回可用状态；若没有这行代码，classmethod 没有实际结果。

    @classmethod  # 新增代码+BrowserProviderRouter: 提供不可用构造入口；若没有这行代码，测试会重复传 available=False。
    def unavailable(cls, kind: BrowserProviderKind, reason: str) -> "BrowserProviderHealth":  # 新增代码+BrowserProviderRouter: 构造不可用健康状态；若没有这行代码，不可用原因容易缺失。
        return cls(kind=kind, available=False, reason=str(reason))  # 新增代码+BrowserProviderRouter: 返回不可用状态并规范化原因；若没有这行代码，原因可能不是字符串。


@dataclass(frozen=True)  # 新增代码+BrowserProviderRouter: 冻结决策对象避免执行层改写审计事实；若没有这行代码，event payload 可能和真实选择不一致。
class BrowserProviderDecision:  # 新增代码+BrowserProviderRouter: 表示一次 provider 路由决策；若没有这个类，路由器返回松散 dict 难以维护。
    provider: BrowserProviderKind  # 新增代码+BrowserProviderRouter: 保存最终选择的 provider；若没有这行代码，调用方不知道走哪条路。
    reason: str  # 新增代码+BrowserProviderRouter: 保存选择原因；若没有这行代码，用户无法理解为什么选择这条路线。
    tool_name: str  # 新增代码+BrowserProviderRouter: 保存触发决策的工具名；若没有这行代码，事件日志无法关联工具。
    fallback_provider: BrowserProviderKind = BrowserProviderKind.UNAVAILABLE  # 新增代码+BrowserProviderRouter: 保存可选 fallback；若没有这行代码，插件不可用时无法提示 CDP 可选。
    requires_user_confirmation: bool = False  # 新增代码+BrowserProviderRouter: 标记是否需要用户确认；若没有这行代码，高风险降级可能直接执行。
    metadata: dict[str, Any] | None = None  # 新增代码+BrowserProviderRouter: 保存额外审计字段；若没有这行代码，未来扩展会破坏构造签名。

    def to_event_payload(self) -> dict[str, Any]:  # 新增代码+BrowserProviderRouter: 把决策转成可写入 JSONL 的 payload；若没有这行代码，事件写入会在各处重复。
        return {  # 新增代码+BrowserProviderRouter: 返回稳定字典结构；若没有这行代码，函数没有可用输出。
            "provider": self.provider.value,  # 新增代码+BrowserProviderRouter: 写入最终 provider 字符串；若没有这行代码，状态 API 无法显示选择结果。
            "reason": self.reason,  # 新增代码+BrowserProviderRouter: 写入选择原因；若没有这行代码，审计无法解释路由。
            "tool_name": self.tool_name,  # 新增代码+BrowserProviderRouter: 写入工具名；若没有这行代码，无法知道哪个动作触发选择。
            "fallback_provider": self.fallback_provider.value,  # 新增代码+BrowserProviderRouter: 写入 fallback provider；若没有这行代码，用户不知道可选降级路线。
            "requires_user_confirmation": self.requires_user_confirmation,  # 新增代码+BrowserProviderRouter: 写入确认需求；若没有这行代码，高风险门禁不可见。
            "metadata": dict(self.metadata or {}),  # 新增代码+BrowserProviderRouter: 写入扩展字段副本；若没有这行代码，调用方可能污染内部状态。
        }  # 新增代码+BrowserProviderRouter: 结束 payload；若没有这行代码，Python 字典语法不完整。
```

- [ ] **Step 3: 运行测试确认仍然红灯但错误变窄**

Run:

```powershell
python -m unittest learning_agent.tests.test_browser_provider_router
```

Expected:

```text
ModuleNotFoundError: No module named 'learning_agent.browser.providers.router'
```

### Task 3: 实现 Router 选择规则

**Files:**
- Create: `learning_agent/browser/providers/router.py`

- [ ] **Step 1: 创建 Router**

`learning_agent/browser/providers/router.py` 应实现蓝图 Stage 1 的规则。

```python
"""浏览器 provider 路由器。"""  # 新增代码+BrowserProviderRouter: 说明本文件负责选择底层浏览器轨道；若没有这行代码，provider 选择逻辑容易散落到工具层。

from __future__ import annotations  # 新增代码+BrowserProviderRouter: 延迟解析类型注解；若没有这行代码，类型引用顺序更脆弱。

from .protocol import BrowserProviderDecision, BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入路由输入输出模型；若没有这行代码，路由器无法返回稳定对象。


class BrowserProviderRouter:  # 新增代码+BrowserProviderRouter: 定义代码级 provider 选择器；若没有这个类，模型可能直接面对多套浏览器工具。
    current_chrome_markers = ("当前 chrome", "当前Chrome", "我的浏览器", "已登录", "登录态", "oauth", "OAuth", "现有标签页", "当前标签页")  # 新增代码+BrowserProviderRouter: 定义当前 Chrome/登录态关键词；若没有这行代码，插件优先规则无法触发。
    cdp_markers = ("cdp", "CDP", "remote debugging", "调试端口", "browser_connect_real_chrome", "隔离 debug profile", "危险调试")  # 新增代码+BrowserProviderRouter: 定义显式 CDP 调试关键词；若没有这行代码，CDP 请求可能误走插件。
    local_markers = ("localhost", "127.0.0.1", "file://", "本地前端", "开发服务器")  # 新增代码+BrowserProviderRouter: 定义本地开发关键词；若没有这行代码，本地调试可能误触真实 Chrome。

    def decide_provider(self, user_input: str, tool_name: str, arguments: dict[str, object] | None = None, provider_health: dict[BrowserProviderKind, BrowserProviderHealth] | None = None, allow_cdp_fallback: bool = False) -> BrowserProviderDecision:  # 新增代码+BrowserProviderRouter: 根据意图和健康状态选择 provider；若没有这行代码，工具层无法统一防误选。
        text = f"{user_input} {tool_name} {arguments or {}}"  # 新增代码+BrowserProviderRouter: 合并用户输入、工具名和参数用于轻量意图判断；若没有这行代码，显式工具名和 URL 无法参与路由。
        health = dict(provider_health or {})  # 新增代码+BrowserProviderRouter: 复制健康状态避免修改调用方对象；若没有这行代码，路由过程可能污染外部状态。
        if self._has_marker(text, self.cdp_markers):  # 新增代码+BrowserProviderRouter: 显式 CDP 请求优先；若没有这行代码，调试端口任务可能被插件路线吞掉。
            return self._available_or_unavailable(BrowserProviderKind.REAL_CHROME_CDP, health, tool_name, "用户明确要求 CDP 或真实 Chrome 调试端口。")  # 新增代码+BrowserProviderRouter: 返回 CDP 决策；若没有这行代码，显式调试无法稳定执行。
        if self._has_marker(text, self.current_chrome_markers):  # 新增代码+BrowserProviderRouter: 当前 Chrome/登录态优先检查插件；若没有这行代码，登录态任务可能误走独立 Chromium。
            extension_health = health.get(BrowserProviderKind.CHROME_EXTENSION, BrowserProviderHealth.unavailable(BrowserProviderKind.CHROME_EXTENSION, "extension_health_missing"))  # 新增代码+BrowserProviderRouter: 读取插件健康状态并给缺省不可用；若没有这行代码，缺状态时可能误判可用。
            if extension_health.available:  # 新增代码+BrowserProviderRouter: 插件可用时优先选择插件；若没有这行代码，Chrome 插件架构不会被使用。
                return BrowserProviderDecision(provider=BrowserProviderKind.CHROME_EXTENSION, reason="用户要求当前 Chrome、登录态或现有标签页，插件 provider 可用。", tool_name=tool_name)  # 新增代码+BrowserProviderRouter: 返回插件决策；若没有这行代码，登录态任务没有首选路线。
            fallback = BrowserProviderKind.REAL_CHROME_CDP if health.get(BrowserProviderKind.REAL_CHROME_CDP, BrowserProviderHealth.unavailable(BrowserProviderKind.REAL_CHROME_CDP, "cdp_missing")).available else BrowserProviderKind.UNAVAILABLE  # 新增代码+BrowserProviderRouter: 计算 CDP 是否可作为候选降级；若没有这行代码，用户无法知道是否可降级。
            if allow_cdp_fallback and fallback == BrowserProviderKind.REAL_CHROME_CDP:  # 新增代码+BrowserProviderRouter: 只有明确允许时才降级 CDP；若没有这行代码，插件不可用会静默改走 CDP。
                return BrowserProviderDecision(provider=BrowserProviderKind.REAL_CHROME_CDP, reason="插件 provider 不可用，且调用方明确允许降级到 CDP。", tool_name=tool_name, fallback_provider=BrowserProviderKind.REAL_CHROME_CDP)  # 新增代码+BrowserProviderRouter: 返回已确认降级决策；若没有这行代码，授权降级无法执行。
            return BrowserProviderDecision(provider=BrowserProviderKind.UNAVAILABLE, reason=f"用户要求当前 Chrome 或登录态，但插件 provider 不可用：{extension_health.reason}", tool_name=tool_name, fallback_provider=fallback, requires_user_confirmation=True)  # 新增代码+BrowserProviderRouter: 返回不可用并要求确认；若没有这行代码，高风险降级会失控。
        if self._has_marker(text, self.local_markers):  # 新增代码+BrowserProviderRouter: 本地开发优先隔离可见 Chromium；若没有这行代码，本地调试可能污染用户 Chrome。
            return self._available_or_unavailable(BrowserProviderKind.VISIBLE_CHROMIUM, health, tool_name, "本地开发或 localhost 任务默认使用隔离可见 Chromium。")  # 新增代码+BrowserProviderRouter: 返回本地开发默认 provider；若没有这行代码，本地任务路线不稳定。
        return self._available_or_unavailable(BrowserProviderKind.VISIBLE_CHROMIUM, health, tool_name, "公开网页或普通浏览器任务默认使用隔离可见 Chromium。")  # 新增代码+BrowserProviderRouter: 返回默认公开网页 provider；若没有这行代码，普通查询没有安全默认路线。

    def _available_or_unavailable(self, kind: BrowserProviderKind, health: dict[BrowserProviderKind, BrowserProviderHealth], tool_name: str, reason: str) -> BrowserProviderDecision:  # 新增代码+BrowserProviderRouter: 复用可用性判断；若没有这行代码，多个分支会重复构造不可用结果。
        provider_health = health.get(kind, BrowserProviderHealth.unavailable(kind, "provider_health_missing"))  # 新增代码+BrowserProviderRouter: 读取 provider 健康状态；若没有这行代码，缺状态可能误判可用。
        if provider_health.available:  # 新增代码+BrowserProviderRouter: provider 可用时返回目标 provider；若没有这行代码，正常路线无法执行。
            return BrowserProviderDecision(provider=kind, reason=reason, tool_name=tool_name)  # 新增代码+BrowserProviderRouter: 返回成功决策；若没有这行代码，调用方拿不到 provider。
        return BrowserProviderDecision(provider=BrowserProviderKind.UNAVAILABLE, reason=f"{reason} 但 provider 不可用：{provider_health.reason}", tool_name=tool_name, fallback_provider=kind, requires_user_confirmation=True)  # 新增代码+BrowserProviderRouter: 返回不可用决策；若没有这行代码，失败原因不可审计。

    def _has_marker(self, text: str, markers: tuple[str, ...]) -> bool:  # 新增代码+BrowserProviderRouter: 统一关键词匹配；若没有这行代码，大小写和中英文规则会散落。
        lowered = text.lower()  # 新增代码+BrowserProviderRouter: 转小写支持英文大小写匹配；若没有这行代码，CDP/oauth 大小写变化可能漏判。
        return any(marker.lower() in lowered for marker in markers)  # 新增代码+BrowserProviderRouter: 判断任一关键词命中；若没有这行代码，意图识别永远为 false。
```

- [ ] **Step 2: 运行 Router 测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_browser_provider_router
```

Expected:

```text
OK
```

### Task 4: 增加 Provider Decision 事件常量

**Files:**
- Modify: `learning_agent/browser/runtime_events.py`
- Create: `learning_agent/browser/providers/provider_events.py`

- [ ] **Step 1: 修改 runtime_events**

在 `BROWSER_OBSERVATION_RECORDED` 后新增：

```python
BROWSER_PROVIDER_DECISION = "browser_provider_decision"  # 新增代码+BrowserProviderRouter: 表示浏览器 provider 路由决策已记录；若没有这行代码，状态生态无法稳定订阅 provider 选择。
```

同时把 `BROWSER_PROVIDER_DECISION` 加入 `BROWSER_RUNTIME_EVENT_TYPES`。

- [ ] **Step 2: 新增 provider_events helper**

`learning_agent/browser/providers/provider_events.py` 应提供稳定 payload 构造。

```python
"""浏览器 provider 事件 helper。"""  # 新增代码+BrowserProviderRouter: 说明本文件负责 provider 事件格式；若没有这行代码，事件 payload 会散落在多个模块。

from __future__ import annotations  # 新增代码+BrowserProviderRouter: 延迟解析类型注解；若没有这行代码，类型引用顺序更脆弱。

from .protocol import BrowserProviderDecision  # 新增代码+BrowserProviderRouter: 导入路由决策对象；若没有这行代码，helper 无法读取决策字段。


def build_provider_decision_event(decision: BrowserProviderDecision) -> dict[str, object]:  # 新增代码+BrowserProviderRouter: 把路由决策转换为事件 payload；若没有这行代码，调用方会重复拼字段。
    return decision.to_event_payload()  # 新增代码+BrowserProviderRouter: 复用决策对象的稳定序列化；若没有这行代码，事件 helper 没有实际输出。
```

- [ ] **Step 3: 增加事件测试**

在 `learning_agent/tests/test_browser_provider_router.py` 中新增测试：

```python
    def test_provider_decision_event_type_is_registered(self) -> None:  # 新增代码+BrowserProviderRouter: 验证 provider 决策事件进入 runtime 事件集合；若没有这行代码，状态生态可能订阅不到该事件。
        from learning_agent.browser.runtime_events import BROWSER_PROVIDER_DECISION, BROWSER_RUNTIME_EVENT_TYPES  # 新增代码+BrowserProviderRouter: 导入事件常量和事件集合；若没有这行代码，测试无法覆盖协议注册。
        self.assertEqual(BROWSER_PROVIDER_DECISION, "browser_provider_decision")  # 新增代码+BrowserProviderRouter: 断言事件名稳定；若没有这行代码，外部 agent 解析会被改名破坏。
        self.assertIn(BROWSER_PROVIDER_DECISION, BROWSER_RUNTIME_EVENT_TYPES)  # 新增代码+BrowserProviderRouter: 断言事件集合包含 provider 决策；若没有这行代码，状态校验可能漏掉新事件。
```

- [ ] **Step 4: 运行事件测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_browser_provider_router
```

Expected:

```text
OK
```

### Task 5: 新增 Registry 空实现

**Files:**
- Create: `learning_agent/browser/providers/registry.py`
- Modify: `learning_agent/tests/test_browser_provider_router.py`

- [ ] **Step 1: 写 registry 测试**

新增测试：

```python
    def test_registry_returns_unavailable_for_missing_provider(self) -> None:  # 新增代码+BrowserProviderRouter: 验证 registry 对未注册 provider 返回不可用；若没有这行代码，缺插件时可能被误判可用。
        from learning_agent.browser.providers.protocol import BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型；若没有这行代码，测试无法指定插件 provider。
        from learning_agent.browser.providers.registry import BrowserProviderRegistry  # 新增代码+BrowserProviderRouter: 导入 registry；若没有这行代码，测试无法覆盖健康查询。
        registry = BrowserProviderRegistry()  # 新增代码+BrowserProviderRouter: 创建空 registry；若没有这行代码，无法模拟 provider 尚未接入状态。
        health = registry.health(BrowserProviderKind.CHROME_EXTENSION)  # 新增代码+BrowserProviderRouter: 查询未注册插件 provider；若没有这行代码，无法验证缺省不可用。
        self.assertFalse(health.available)  # 新增代码+BrowserProviderRouter: 断言未注册 provider 不可用；若没有这行代码，路由器可能误选插件。
        self.assertIn("not_registered", health.reason)  # 新增代码+BrowserProviderRouter: 断言原因可审计；若没有这行代码，状态输出不可解释。
```

- [ ] **Step 2: 创建 registry**

```python
"""浏览器 provider 注册表。"""  # 新增代码+BrowserProviderRouter: 说明本文件负责 provider 健康状态查询；若没有这行代码，provider 生命周期边界不清楚。

from __future__ import annotations  # 新增代码+BrowserProviderRouter: 延迟解析类型注解；若没有这行代码，类型引用顺序更脆弱。

from .protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型和健康状态；若没有这行代码，registry 无法返回稳定对象。


class BrowserProviderRegistry:  # 新增代码+BrowserProviderRouter: 定义 provider 注册表；若没有这个类，router 只能接收散落的健康 dict。
    def __init__(self) -> None:  # 新增代码+BrowserProviderRouter: 初始化空 provider 映射；若没有这行代码，实例没有存储空间。
        self._health: dict[BrowserProviderKind, BrowserProviderHealth] = {}  # 新增代码+BrowserProviderRouter: 保存 provider 健康状态；若没有这行代码，health 查询无法工作。

    def set_health(self, health: BrowserProviderHealth) -> None:  # 新增代码+BrowserProviderRouter: 允许测试和未来 provider 更新健康状态；若没有这行代码，registry 无法记录可用 provider。
        self._health[health.kind] = health  # 新增代码+BrowserProviderRouter: 按 provider 类型保存状态；若没有这行代码，set_health 没有效果。

    def health(self, kind: BrowserProviderKind) -> BrowserProviderHealth:  # 新增代码+BrowserProviderRouter: 查询单个 provider 健康状态；若没有这行代码，router 无法统一读取状态。
        return self._health.get(kind, BrowserProviderHealth.unavailable(kind, "not_registered"))  # 新增代码+BrowserProviderRouter: 未注册 provider 返回不可用；若没有这行代码，缺插件可能被误判成功。

    def all_health(self) -> dict[BrowserProviderKind, BrowserProviderHealth]:  # 新增代码+BrowserProviderRouter: 返回健康状态副本；若没有这行代码，router 无法一次读取全部 provider。
        return dict(self._health)  # 新增代码+BrowserProviderRouter: 返回副本避免外部污染内部映射；若没有这行代码，调用方可能修改 registry 状态。
```

- [ ] **Step 3: 运行 registry 测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_browser_provider_router
```

Expected:

```text
OK
```

### Task 6: 更新 browser 包导出

**Files:**
- Modify: `learning_agent/browser/__init__.py`

- [ ] **Step 1: 增加 provider 导出**

在 `learning_agent/browser/__init__.py` 中导入：

```python
from .providers import BrowserProviderDecision, BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 从 browser 包入口导出 provider 路由协议；若没有这行代码，外部测试和 agent 难以统一导入。
```

在 `__all__` 中加入：

```python
    "BrowserProviderDecision",  # 新增代码+BrowserProviderRouter: 公开 provider 决策对象；若没有这行代码，外部 agent 难以读取路由结果类型。
    "BrowserProviderHealth",  # 新增代码+BrowserProviderRouter: 公开 provider 健康状态；若没有这行代码，外部状态 API 难以复用。
    "BrowserProviderKind",  # 新增代码+BrowserProviderRouter: 公开 provider 类型枚举；若没有这行代码，外部代码只能使用易错字符串。
```

- [ ] **Step 2: 运行导入验证**

Run:

```powershell
python - <<'PY'
from learning_agent.browser import BrowserProviderKind
print(BrowserProviderKind.VISIBLE_CHROMIUM.value)
PY
```

Expected:

```text
visible_chromium
```

### Task 7: Stage 1 自动化验证

**Files:**
- Test only

- [ ] **Step 1: 运行 provider router 单测**

Run:

```powershell
python -m unittest learning_agent.tests.test_browser_provider_router
```

Expected:

```text
OK
```

- [ ] **Step 2: 运行现有浏览器相关单测**

Run:

```powershell
python -m unittest learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_action_executor learning_agent.tests.test_browser_session_manager learning_agent.tests.test_browser_provider_router
```

Expected:

```text
OK
```

- [ ] **Step 3: 运行全量测试**

Run:

```powershell
python -m unittest discover -s learning_agent\tests
```

Expected:

```text
OK
```

### Task 8: Stage 1 文档备份和进度记录

**Files:**
- Modify: `agent_memory/progress.md`
- Create: `learning_agent/test/browser_dual_track_stage1_20260601/modified_snippets.md`

- [ ] **Step 1: 创建备份目录**

Run:

```powershell
New-Item -ItemType Directory -Force -Path H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\test\browser_dual_track_stage1_20260601
```

Expected:

```text
目录存在或创建成功
```

- [ ] **Step 2: 备份新增和修改代码片段**

`modified_snippets.md` 必须包含：

1. 新增文件列表。
2. 修改文件列表。
3. 每个新增类和函数的中文说明。
4. 测试命令和结果。
5. 真实终端验收 run id。

- [ ] **Step 3: 更新 agent_memory/progress.md**

记录：

1. Stage 1 开始时间。
2. 完成的 task。
3. 自动化测试结果。
4. 真实终端验收结果。
5. 未完成或风险。

### Task 9: Stage 1 真实可见终端验收

**Files:**
- May create: `learning_agent/acceptance_controller/scenarios/browser_provider_router_stage1.json`

- [ ] **Step 1: 创建最小验收场景**

场景要求：

1. 通过真实终端启动 `learning_agent/start_oauth_agent.bat`。
2. 输入 prompt：`请检查浏览器 provider router 状态，不要打开真实登录态页面。`
3. agent 至少能输出 provider router 的可用状态或说明当前 Stage 1 只是路由协议层。

- [ ] **Step 2: 启动真实终端**

Run:

```powershell
Start-Process -FilePath H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat -WorkingDirectory H:\codexworkplace\sofeware\OpenHarness-main\learning_agent
```

Expected:

```text
用户本地电脑出现真实可见终端窗口
```

- [ ] **Step 3: 在真实终端输入测试 prompt**

输入：

```text
请检查浏览器 provider router 状态，不要打开真实登录态页面。
```

Expected:

```text
agent 正常响应，未崩溃，未误打开用户真实 Chrome 登录态页面。
```

- [ ] **Step 4: 验收记录**

如果当前 Codex 环境无法观察或输入真实可见终端，必须明确记录：

```text
真实可见终端交互验收未完成，不能声明开发完成。
```

## 4. Stage 2 到 Stage 12 阶段门禁

这些阶段不能直接跳做。每个阶段开始前，必须先创建独立计划文件，路径格式：

```text
docs/superpowers/plans/YYYY-MM-DD-browser-dual-track-stageN-<name>.md
```

### Stage 2: 现有 Playwright/CDP 能力迁入 Provider

入口条件：

1. Stage 1 所有测试通过。
2. Stage 1 真实终端验收通过或明确由用户补充截图/输出。

必须产物：

1. `VisibleChromiumProvider`。
2. `RealChromeCdpProvider`。
3. 旧 `browser_automation_mcp_server.py` 通过 provider adapter 调用，但工具名不变。

验收重点：

1. 现有 browser 单测不退化。
2. 公开网页查询仍走可见 Chromium。
3. 显式 CDP 调试仍走真实 Chrome CDP。

### Stage 3: 统一工具表面和模型防误选

入口条件：

1. Stage 2 provider adapter 已稳定。

必须产物：

1. 模型首轮只看到统一 `browser_*` 工具。
2. provider-specific 工具只作为 internal 或 advanced 能力存在。
3. prompt/harness 明确“模型不选择 provider”。

验收重点：

1. 工具池中不存在重复 open/click/type 工具。
2. event log 能看到 provider 决策。

### Stage 4: `browser_tabs_context` 合同

入口条件：

1. Router 已接管真实 Chrome 登录态任务。

必须产物：

1. `browser_tabs_context`。
2. 真实 Chrome/插件任务必须先读取 tabs context。
3. tab id 不能跨 session 复用。

验收重点：

1. 未读 tabs context 时不能 click/type 当前 Chrome。
2. tab closed 或 navigation error 后自动刷新 context。

### Stage 5: Chrome 插件 MVP，只读能力

入口条件：

1. Stage 4 tabs context 合同通过。

必须产物：

1. Chrome extension manifest。
2. native host 安装器。
3. 插件连接状态。
4. 当前 tab 列表和页面文本读取。

验收重点：

1. 不读取 cookie、localStorage、sessionStorage、token、password。
2. learning_agent 能读取当前 Chrome 页面标题和可见文本。

### Stage 6: Chrome 插件写动作

入口条件：

1. 插件只读闭环稳定。

必须产物：

1. click。
2. type。
3. press_key。
4. navigate。
5. scroll。
6. form_input。

验收重点：

1. 每个写动作进入 `BrowserActionExecutor`。
2. 每个写动作有 action/event/observation 证据。

### Stage 7: 插件站点权限

入口条件：

1. 插件写动作稳定。

必须产物：

1. read/click/type/submit/upload/console/network 权限。
2. origin 授权状态。
3. 权限变更事件。

验收重点：

1. 未授权 origin 不允许 click/type/submit。
2. 授权后只允许对应动作。

### Stage 8: 状态 UI / CLI / API 生态

入口条件：

1. 插件 provider 和权限事件已稳定。

必须产物：

1. `browser_provider_status`。
2. `browser_extension_status`。
3. CLI/API 状态输出。

验收重点：

1. 能看到 provider、native host、tab、permission、run、action、observation。
2. 其他 agent 能通过状态 API 判断浏览器是否可用。

### Stage 9: GIF/录屏/视觉证据

入口条件：

1. 写动作和状态生态稳定。

必须产物：

1. `browser_record_start`。
2. `browser_record_stop`。
3. `browser_gif_export`。
4. action 关联截图帧。

验收重点：

1. 多步骤流程能生成可查看 GIF 或帧序列。
2. verifier 能确认 artifact 存在。

### Stage 10: 失败恢复和 fallback 策略

入口条件：

1. 三类 provider 均可被 Router 识别。

必须产物：

1. 插件不可用不静默降级。
2. 用户允许时才降级 CDP。
3. 普通公开网页可降级可见 Chromium。
4. 连续 2-3 次失败停止并汇报。

验收重点：

1. 单测覆盖插件断开、tab 丢失、权限不足。
2. 真实终端覆盖插件不可用场景。

### Stage 11: 长任务 harness 接入

入口条件：

1. provider 决策、动作、权限、状态均有事件。

必须产物：

1. harness run。
2. stage。
3. event log。
4. checkpoint。
5. resume。
6. replay。
7. verifier。

验收重点：

1. 中断后已完成浏览器 stage 不重跑。
2. 状态 CLI/API 能看到 provider 决策和 verifier 结果。

### Stage 12: 真实可见终端总验收

入口条件：

1. Stage 1 到 Stage 11 均完成。

必须场景：

1. 公开网页查询走可见 Chromium。
2. 当前 Chrome 登录态走插件 provider。
3. 显式 CDP 调试走 RealChromeCdpProvider。
4. 插件不可用且未允许降级时停止并说明。
5. 复杂表单在站点授权后 click/type/submit。
6. 中断恢复不重跑已完成阶段。
7. 状态 CLI/API 能看到 run、stage、task、event、output、verifier、provider、tab、permission。

完成标准：

1. 自动化测试通过。
2. 独立 verifier 通过。
3. `start_oauth_agent.bat` 真实可见终端交互验收通过。
4. 用户能肉眼看到真实浏览器被操作。

## 5. 自检清单

执行者在每个阶段结束前必须确认：

1. 是否只做当前阶段范围内的文件。
2. 是否没有让模型看到重复 provider 工具。
3. 是否每个新增代码行都有中文注释。
4. 是否把新增/修改代码片段备份到 `learning_agent/test/<stage>/`。
5. 是否更新 `agent_memory/progress.md`。
6. 是否运行阶段单测。
7. 是否运行相关全量测试。
8. 是否完成真实可见终端验收。
9. 是否明确记录未完成验收时不能声明开发完成。
