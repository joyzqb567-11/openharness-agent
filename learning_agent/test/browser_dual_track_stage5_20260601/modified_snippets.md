# Stage 5 学习备份：Chrome 插件 MVP 只读能力

日期：2026-06-01

本备份用于给后续 agent 和用户复盘：Stage 5 只补 Chrome 插件路线的“只读 MVP”，不开放点击、输入、按键、上传、提交等写动作。

## 本阶段新增与修改的关键文件

1. `learning_agent/chrome_extension/manifest.json`
2. `learning_agent/chrome_extension/background.js`
3. `learning_agent/chrome_extension/content_script.js`
4. `learning_agent/chrome_extension/page_bridge.js`
5. `learning_agent/chrome_extension/options.html`
6. `learning_agent/chrome_extension/options.js`
7. `learning_agent/browser_extension_host/__init__.py`
8. `learning_agent/browser_extension_host/message_protocol.py`
9. `learning_agent/browser_extension_host/pairing_store.py`
10. `learning_agent/browser_extension_host/bridge_server.py`
11. `learning_agent/browser_extension_host/manifest_installer.py`
12. `learning_agent/browser_extension_host/native_host.py`
13. `learning_agent/browser/providers/chrome_extension.py`
14. `learning_agent/browser/providers/__init__.py`
15. `learning_agent/browser_automation_mcp_server.py`
16. `learning_agent/skills/real_chrome/SKILL.md`
17. `learning_agent/tests/test_chrome_extension_readonly_stage5.py`
18. `learning_agent/acceptance_controller/scenarios/chrome_extension_readonly_stage5_acceptance.json`

## 红灯证据

首次运行：

```powershell
python -m unittest learning_agent.tests.test_chrome_extension_readonly_stage5
```

预期失败点：

- 缺少 `learning_agent/chrome_extension/manifest.json`。
- 缺少 `learning_agent.browser_extension_host`。
- 缺少 `learning_agent.browser.providers.chrome_extension`。
- `BrowserAutomationServer` 未公开 `browser_extension_status`。

这些失败证明测试先锁住了 Stage 5 的真实缺口，而不是事后补测试。

## 绿灯证据

聚焦测试：

```powershell
python -m unittest learning_agent.tests.test_chrome_extension_readonly_stage5
```

结果：5 tests OK。

相关回归：

```powershell
python -m unittest learning_agent.tests.test_chrome_extension_readonly_stage5 learning_agent.tests.test_browser_provider_router learning_agent.tests.test_browser_provider_adapters learning_agent.tests.test_browser_tabs_context_stage4 learning_agent.tests.test_browser_tool_surface_stage3
```

结果：33 tests OK。

语法检查：

```powershell
python -m py_compile .\learning_agent\browser_extension_host\__init__.py .\learning_agent\browser_extension_host\message_protocol.py .\learning_agent\browser_extension_host\pairing_store.py .\learning_agent\browser_extension_host\bridge_server.py .\learning_agent\browser_extension_host\manifest_installer.py .\learning_agent\browser_extension_host\native_host.py .\learning_agent\browser\providers\chrome_extension.py .\learning_agent\browser\providers\__init__.py .\learning_agent\browser_automation_mcp_server.py .\learning_agent\tests\test_chrome_extension_readonly_stage5.py
```

结果：退出码 0。

全量回归：

```powershell
python -m unittest discover -s learning_agent\tests
```

结果：523 tests OK，skipped=1。

## 关键边界

- Chrome 插件脚本不读取 cookie、storage 或密码类本地状态。
- Native host 协议只允许 `tabs_context`、`read_page`、`status` 这类只读动作。
- `ChromeExtensionProvider` 默认未连接时不可用，避免 Router 误选插件轨道。
- 模型仍只看到统一 `browser_*` 工具表面，不新增 `chrome_extension_open` 这类 provider-specific 重复动作。

## 真实终端验收

真实可见终端验收场景已新增：

```text
learning_agent/acceptance_controller/scenarios/chrome_extension_readonly_stage5_acceptance.json
```

本文件创建时真实终端验收仍在执行前；验收通过后，需要把 run 目录、`result.json` 和独立 verifier 结果继续写入 `agent_memory/progress.md` 与 `agent_memory/bugs.md`。

验收已通过：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\chrome_extension_readonly_stage5_acceptance.json
```

controller 结果：

```text
ACCEPTANCE_CONTROLLER_COMPLETED=True
RESULT_JSON=H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\chrome_extension_readonly_stage5_acceptance-20260601_175710\result.json
```

独立 verifier：

```powershell
python -m learning_agent.acceptance.verifier .\learning_agent\acceptance_controller\runs\chrome_extension_readonly_stage5_acceptance-20260601_175710 .\learning_agent\acceptance_controller\scenarios\chrome_extension_readonly_stage5_acceptance.json
```

verifier 结果：`schema_version=2`、`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。

最终回答包含：

```text
CHROME_EXTENSION_STAGE5_READY STAGE5_CHROME_EXTENSION_READONLY_OK
```
