# Acceptance Controller

这个目录把真实可见终端验收从“一次性脚本”升级为“场景驱动控制器”。

## 运行方式

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath .\learning_agent\acceptance_controller\scenarios\smoke.json
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath .\learning_agent\acceptance_controller\scenarios\chongqing_weather_browser.json
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath .\learning_agent\acceptance_controller\scenarios\real_chrome_profile_status.json
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath .\learning_agent\acceptance_controller\scenarios\real_chrome_connect_public_page.json
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath .\learning_agent\acceptance_controller\scenarios\real_chrome_chongqing_weather_travel.json
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath .\learning_agent\acceptance_controller\scenarios\real_chrome_google_human_search.json
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath .\learning_agent\acceptance_controller\scenarios\real_chrome_natural_weather_travel.json
```

## 场景职责

场景 JSON 只描述任务内容和断言：

- `prompt_lines`：要输入到真实终端 agent 的任务。
- `required_event_states`：必须出现的 acceptance harness 状态。
- `debug_log_contains`：调试日志必须包含的证据。
- `event_answer_contains`：最终回答事件预览必须包含的文本。
- `permission_policy`：可选权限策略；未配置时保持旧行为默认同意，配置后可用 `default_response`、`allow_contains`、`deny_contains`、`allow_tool_names`、`deny_tool_names`、`allow_url_prefixes` 控制自动输入 `y` 或 `n`。
- `allow_tool_names` / `deny_tool_names`：基于 `permission_required` 事件里的结构化 `payload.tool_name` 精确放行或拒绝工具，适合真实 Chrome 等高风险场景。
- `allow_url_prefixes`：基于 `permission_required` 事件里的结构化 `payload.arguments.url` 限制 `browser_open` 只能访问指定公开来源。
- `post_success_wait_seconds`：可选成功后停留秒数，适合 Google 拟人演示这类希望用户肉眼观察真实窗口的场景。

窗口启动、权限输入、prompt 重试、截图、事件日志、调试日志归档和 `result.json` 输出都由 `controller.ps1` 统一处理。
