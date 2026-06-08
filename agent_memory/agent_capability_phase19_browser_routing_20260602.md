# 2026-06-02 Agent Capability Phase 19 Browser Tool Routing

## 目标

- 强化浏览器 provider 路由：当前 Chrome/登录态任务优先使用已配对且支持目标工具的 Chrome extension。
- 当 Chrome extension 已配对但不支持目标工具时，优先切换到真实 Chrome CDP。
- 当 extension 不支持且 CDP 不可用时，退到隔离可见 Chromium，并在 decision metadata 中保留降级证据。
- 保持旧的安全门禁：extension 不可用时，不静默降级到 CDP，除非调用方显式允许。

## 修改文件

- `learning_agent/browser/providers/protocol.py`：`BrowserProviderHealth` 新增 `metadata`，构造函数支持携带审计字段。
- `learning_agent/browser/providers/chrome_extension.py`：`health()` 从“连接即可用”升级为“连接 + 完整配对才可用”，并暴露支持工具清单。
- `learning_agent/browser/providers/router.py`：新增当前 Chrome 专用路由策略，支持 extension / CDP / visible Chromium 三段选择。
- `learning_agent/tests/test_browser_routing_phase19.py`：新增 Phase 19 TDD 测试。
- `learning_agent/tests/test_chrome_extension_readonly_stage5.py`：旧测试同步为配对门禁语义。
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase19_browser_routing.json`：新增真实可见终端验收场景。

## 验证

- 红灯验证：`python -m unittest learning_agent.tests.test_browser_routing_phase19` 初次失败，失败点包括 metadata 构造参数缺失和 extension health 未按配对门禁判断。
- 聚焦测试：`python -m unittest learning_agent.tests.test_browser_routing_phase19`，3 tests OK。
- 相关回归：provider / extension / fallback 共 50 tests OK。
- 语法验证：`python -m py_compile ...`，退出码 0。
- JSON 验证：`python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_phase19_browser_routing.json`，退出码 0。
- 全量测试：`python -m unittest discover -s learning_agent\tests`，600 tests OK，skipped=1。

## 真实可见终端验收

- controller 启动 `learning_agent/start_oauth_agent.bat`，场景文件为 `learning_agent/acceptance_controller/scenarios/agent_capability_phase19_browser_routing.json`。
- run 目录：`learning_agent/acceptance_controller/runs/agent_capability_phase19_browser_routing-20260602_204739`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 独立 verifier 复验通过。
- 最终终端截图 `03_final.png` 显示 `PHASE19_ROUTING_OK`、`extension=chrome_extension`、`cdp=real_chrome_cdp`、`visible=visible_chromium`。

## 当前状态

- Phase 19 已完成自动化测试、全量回归、真实可见终端验收和独立 verifier 复验。
- 下一阶段进入 Phase 20：OS 级 Computer Use 生产化。
