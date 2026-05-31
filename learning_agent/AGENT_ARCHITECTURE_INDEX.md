# learning_agent Stage 14 纯新架构索引

更新时间：2026-05-30

这份文档是 `learning_agent` 的修 bug 索引和维护地图。它只描述 Stage 14 之后的当前新架构，帮助用户和后续 agent 快速判断“问题应该去哪个层、哪个模块查”，避免重新回到翻巨型入口文件的模式。

## 1. 当前结论

`learning_agent` 已经从“一个大文件堆所有能力”改造成分层 agent 工程。当前可见架构目标是：入口清晰、模型适配独立、工具目录独立、MCP 生命周期独立、真实浏览器能力独立、观测验收独立、测试按模块拆分。

Stage 14 的硬清理目标是让用户和维护者看到的都是纯新架构：

- 业务代码不再从旧脚本入口导入。
- 测试不再依赖旧的大测试聚合文件。
- 验收事件不再通过根目录兼容转发入口。
- 历史运行产物目录不再留在源码树里误导维护者。
- 文档和启动脚本统一指向新入口。

Stage 14 本次验收结果：

- `python -m compileall learning_agent` 通过。
- `core/agent.py` 同级不可达代码 AST 检查通过，结果为 `NO_UNREACHABLE_SAME_BLOCK_CODE`。
- `python -m unittest learning_agent.tests.test_compat_cleanup` 通过，结果为 5 tests OK。
- `python -m unittest discover learning_agent` 通过，结果为 368 tests OK，skipped=1。
- 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_210431/result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 真实浏览器截图和运行证据已归档到 `learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_210431/`，源码根下的 `test/`、`debug_logs/`、`browser_artifacts/`、`tests_support/` 均已删除。

## 2. 唯一新入口

用户双击入口：

```text
learning_agent/start_oauth_agent.bat
  -> learning_agent/start_oauth_agent.ps1
  -> learning_agent/learning_agent.py
  -> learning_agent/app/cli.py
  -> learning_agent/core/agent.py
```

Codex 模式入口：

```text
learning_agent/start_codex_agent.bat
  -> learning_agent/start_codex_agent.ps1
  -> learning_agent/learning_agent.py
  -> learning_agent/app/cli.py
```

Python 包公开入口：

```text
learning_agent/__init__.py
```

完整自动化测试入口：

```powershell
python -m unittest discover learning_agent
```

聚焦测试入口：

```powershell
python -m unittest learning_agent.tests.test_core_run_loop
python -m unittest learning_agent.tests.test_tools_policy
python -m unittest learning_agent.tests.test_browser_harness
```

真实可见终端验收入口：

```powershell
learning_agent/acceptance_controller/controller.ps1
```

## 3. 已删除或废弃的旧入口

以下入口不再作为当前架构的一部分：

- `learning_agent/test_learning_agent.py`
- `learning_agent/tests/_legacy_groups.py`
- `learning_agent/tests_support/legacy_learning_agent_suite.py`
- `learning_agent/tests_support/`
- `learning_agent/acceptance_harness.py`
- `learning_agent/test/`
- `learning_agent/debug_logs/`
- `learning_agent/browser_artifacts/`

如果未来代码、文档或脚本重新要求使用这些入口，应该先判定为架构回流风险，而不是顺手恢复兼容。

## 4. 目录分层

```text
learning_agent/
  app/                    命令行入口、交互终端、doctor、自检和 HTTP command bridge。
  browser/                真实浏览器意图识别、自然查询 harness、客户模式授权和截图路径策略。
  core/                   Agent 主循环、消息类型、运行配置和工具调度。
  mcp/                    MCP 配置加载、server 生命周期、工具发现和运行时适配。
  models/                 OpenAI、Codex CLI、Codex OAuth/API、FakeModel 等模型适配器。
  observability/          调试日志、权限事件、验收事件、最终回答事件和 JSONL 记录。
  prompts/                静态提示词、动态提示词、上下文组装和 token 预算。
  tasks/                  长任务、后台任务、cron monitor 和任务状态格式化。
  tools/                  内置工具 schema、工具目录、工具策略、文件和 shell 工具实现。
  tests/                  当前唯一模块化测试套件。
  acceptance_controller/  真实可见终端验收控制器、场景和运行记录。
```

## 5. 关键模块导航

启动命令或参数异常：

- 先看 `learning_agent/app/cli.py`
- 再看 `learning_agent/app/interactive.py`
- 双击脚本问题看 `start_oauth_agent.ps1` 或 `start_codex_agent.ps1`

Agent 思考循环或工具调用异常：

- 先看 `learning_agent/core/agent.py`
- 消息结构看 `learning_agent/core/messages.py`
- 配置对象看 `learning_agent/core/config.py`

模型返回异常、OAuth 失败、额度错误：

- 先看 `learning_agent/models/adapters.py`
- OAuth token 和 Responses API 看 `learning_agent/models/codex_oauth.py`

工具 schema、工具能力包、工具策略异常：

- schema 唯一事实源是 `learning_agent/tools/schemas.py`
- 工具目录和描述看 `learning_agent/tools/catalog.py`
- 权限策略看 `learning_agent/tools/policy.py`

MCP server 启动、发现、调用异常：

- 配置加载看 `learning_agent/mcp/config.py`
- 生命周期看 `learning_agent/mcp/lifecycle.py`
- 运行时注册和调用看 `learning_agent/mcp/runtime.py`

真实 Chrome 或浏览器自动化异常：

- 意图识别看 `learning_agent/browser/intent.py`
- 真实浏览器自然查询 harness 看 `learning_agent/browser/harness.py`
- 客户模式自动授权看 `learning_agent/browser/customer_mode.py`
- Chrome 环境诊断看 `learning_agent/browser_real_chrome.py`
- MCP 浏览器 server 看 `learning_agent/browser_automation_mcp_server.py`

权限提示、自动授权、真实终端验收异常：

- 权限事件看 `learning_agent/observability/permissions.py`
- 验收事件看 `learning_agent/observability/acceptance_events.py`
- 真实终端控制器看 `learning_agent/acceptance_controller/`

测试失败定位：

- 主循环失败看 `learning_agent/tests/test_core_run_loop.py`
- 模型失败看 `learning_agent/tests/test_models_codex_oauth.py`
- MCP 失败看 `learning_agent/tests/test_mcp_registry.py`
- 工具策略失败看 `learning_agent/tests/test_tools_policy.py`
- 浏览器意图失败看 `learning_agent/tests/test_browser_intent.py`
- 浏览器 harness 失败看 `learning_agent/tests/test_browser_harness.py`
- Prompt/context 失败看 `learning_agent/tests/test_prompts_context.py`
- 观测验收失败看 `learning_agent/tests/test_observability_acceptance.py`
- 架构回流失败看 `learning_agent/tests/test_compat_cleanup.py`

## 6. 为什么 `core/agent.py` 仍然较大

`core/agent.py` 仍然是主编排层，所以它会保留 agent run loop、工具调用路由、权限入口、模型调用前后处理和终端输出控制。它的“大”不应该来自旧入口兼容或重复实现，而应该来自主流程编排本身。

后续继续瘦身时，优先遵循这个边界：

- 纯工具 schema 放到 `tools/schemas.py`。
- 工具策略放到 `tools/policy.py`。
- MCP 生命周期放到 `mcp/`。
- 浏览器客户模式放到 `browser/`。
- 任务后台状态放到 `tasks/`。
- 观测和验收事件放到 `observability/`。

不要把新功能直接堆回 `core/agent.py`，除非它确实是主循环编排逻辑。

## 7. 回归测试清单

轻量语法检查：

```powershell
python -m compileall learning_agent
```

完整自动化回归：

```powershell
python -m unittest discover learning_agent
```

架构防回流测试：

```powershell
python -m unittest learning_agent.tests.test_compat_cleanup
```

真实可见终端验收：

```powershell
powershell -ExecutionPolicy Bypass -File learning_agent/acceptance_controller/controller.ps1 -Scenario real_chrome_natural_weather_travel
```

只有“代码修改完成 + 自动化测试通过 + 真实可见终端交互验收通过”，才能宣称本项目 agent 功能开发完成。

## 8. 维护规则

- 新代码不要从 `learning_agent.learning_agent` 导入业务对象。
- 新测试不要恢复旧聚合测试入口。
- 新验收逻辑直接使用 `observability/acceptance_events.py`。
- 新运行产物应写入专门运行目录或临时目录，不要留在源码根目录作为长期文件。
- 修改公开入口、工具策略、模型适配、MCP 或真实浏览器逻辑后，必须跑对应模块测试和完整回归。
- 修改真实浏览器功能后，必须跑真实可见终端验收；单元测试不能替代这个门禁。
