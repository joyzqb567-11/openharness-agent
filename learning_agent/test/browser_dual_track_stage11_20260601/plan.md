# Stage 11: 浏览器双轨运行时接入长任务 Harness 计划

## 目标

把 `browser_*` 工具产生的 browser runtime run 正式投影成 harness run/stage/verifier/event，让浏览器任务不再只是 `learning_agent/memory/browser_runtime` 里的旁路记录。

## 成功标准

1. 每一次顶层浏览器工具调用都会自动创建同名 durable harness run。
2. 浏览器 provider 决策会进入 browser event log，也会镜像进入 harness event log。
3. 浏览器 action/observation/replay/checkpoint/verifier 能被统一状态快照关联起来。
4. `browser_flow_run` 进程中断后，已完成 stage 继续由 checkpoint 跳过，并且 harness stage 也显示 completed。
5. `status` CLI/API/SDK 快照能看到 browser run 对应的 harness verifier 结果。
6. 单元测试、全量测试、controller 场景和真实可见终端验收都通过后，才允许进入 Stage 12。

## 实施阶段

### 1. 先写失败测试

新增 `learning_agent/tests/test_browser_harness_integration_stage11.py`，覆盖：

- 顶层 `browser_provider_status` 调用后，必须存在同 id 的 `HarnessRun`。
- harness 事件里必须有 provider decision 镜像事件。
- harness stage 必须有 `acceptance.passed=true` 和 verifier checks。
- 状态快照 `browser.runs[*].harness` 必须能看到 verifier 结果。
- `BrowserFlowRuntime` 恢复时不能重跑已完成阶段，并且镜像后的 harness stage 仍是 completed。

### 2. 新增 harness 投影模块

新增 `learning_agent/browser/harness_integration.py`：

- `browser_harness_store_for_workspace()`：兼容项目根目录和 `learning_agent` 包目录两种 workspace。
- `BrowserHarnessMirror.start_run()`：创建/领取/标记 browser 对应 harness run。
- `BrowserHarnessMirror.append_provider_decision()`：把 provider 决策镜像到 harness event log。
- `BrowserHarnessMirror.finish_run()`：把浏览器工具最终结果写成 stage acceptance/verifier。
- `BrowserHarnessMirror.sync_flow_report()`：把 `browser_flow_run` 的阶段 checkpoint 结果写进 harness stage。

### 3. 接入 MCP 浏览器 server

修改 `learning_agent/browser_automation_mcp_server.py`：

- 初始化 `BrowserHarnessMirror`。
- `_start_browser_runtime_run()` 创建 browser run 后同步创建 harness run。
- `_record_browser_provider_decision()` 同步镜像 provider decision。
- `_finish_browser_runtime_run()` 同步写入 stage/verifier 结果。
- `browser_flow_run()` 在 report 生成后同步 flow stage 到 harness。

### 4. 接入状态生态

修改 `learning_agent/runtime/status_snapshot.py`：

- `_load_runs()` 兼容 `workspace/memory/harness` 和 `workspace/learning_agent/memory/harness`。
- `_load_browser_runtime()` 给每个 browser run 加上 `harness` 链接摘要。
- `browser.harness.latest_verifier` 提供 CLI/API/SDK 可见的最近浏览器 verifier。

### 5. CLI/API/SDK 验收

复用已有：

- `python -m learning_agent.harness.cli snapshot --workspace ... --json`
- `/browser/runs`
- `/browser/events`

如测试发现缺少字段，只补字段，不再新增旁路端点。

### 6. 备份与验收

新增或修改的核心代码、测试、场景、文档都备份到：

`learning_agent/test/browser_dual_track_stage11_20260601/`

验收命令：

- `python -m unittest learning_agent.tests.test_browser_harness_integration_stage11`
- `python -m unittest discover -s learning_agent\tests`
- `python -m py_compile ...`
- acceptance controller 场景
- 最终 Stage 12 再执行 `start_oauth_agent.bat` 真实可见终端总验收
