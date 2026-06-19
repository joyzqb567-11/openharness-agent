# Windows Computer Use 生产验收矩阵

这份文档用于说明如何在 OpenHarness 里运行 Windows Computer Use 的生产验收矩阵，以及如何判断结果是否真的通过。

## 一键运行

在项目根目录 `H:\codexworkplace\sofeware\OpenHarness-main` 运行：

```powershell
powershell -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\run_windows_computer_use_acceptance.ps1
```

这个命令会读取：

```text
learning_agent/acceptance_controller/windows_computer_use_production_matrix.json
```

然后逐条调用：

```text
learning_agent/acceptance_controller/controller.ps1
```

每条场景都会启动真实可见终端窗口，并通过 `learning_agent/start_oauth_agent.bat` 输入真实用户 prompt。

## 当前覆盖范围

矩阵覆盖 10 类 Windows Computer Use 生产场景：

1. Cua Driver 借鉴后的 Notepad 生产链路。
2. Computer Use 权限 UI 允许路径。
3. Computer Use 权限 UI 拒绝路径。
4. Notepad 单应用文本写入和保存。
5. Calculator 单应用计算。
6. Explorer 本地文件夹 roundtrip。
7. 本地浏览器页面点击验证。
8. 多应用传递。
9. 失败恢复。
10. 长任务恢复。

## 输出文件

每次运行会创建一个新目录：

```text
learning_agent/acceptance_controller/runs/windows_computer_use_production_matrix-<timestamp>/
```

关键文件：

```text
matrix_result.json
matrix_result.md
matrix_runner.log
<scenario-id>-controller.log
```

每条子场景还会创建自己的 controller 证据目录，包含：

```text
result.json
events.jsonl
latest_run_readable.md
01_startup.png
02_prompt_sent.png
03_final.png
```

## 通过标准

矩阵总结果必须满足：

```json
{
  "passed": true,
  "scenario_count": 10,
  "passed_count": 10,
  "failed_count": 0
}
```

每条场景必须满足：

```json
{
  "completed": true,
  "assertion_passed": true,
  "marker_passed": true,
  "token_passed": true,
  "screenshot_passed": true,
  "passed": true
}
```

如果某条场景缺少 `startup/prompt/final` 截图，不能算生产验收通过。

## 最新通过记录

本轮最新通过记录：

```text
learning_agent/acceptance_controller/runs/windows_computer_use_production_matrix-20260618_183954/matrix_result.json
```

关键事实：

```text
passed=true
scenario_count=10
passed_count=10
failed_count=0
```

## 常见失败解释

`result_json_missing` 通常表示 controller 没能成功输入或观察真实终端，常见原因是 Windows 焦点被其它窗口抢走。

`controller_exit_code_2` 表示 controller 正常写出了 `result.json`，但场景断言没有通过，需要打开该场景的 `result.json` 和 `latest_run_readable.md` 看具体缺哪个 token。

`required_tokens_missing` 表示 controller 可能通过了，但 manifest 要求的生产证据 token 没在 stdout、result、debug 或 readable log 里出现。

`required_screenshots_missing` 表示可见终端证据不完整，不能当成真实验收通过。

## 安全边界

矩阵只允许受控代表场景，不允许打开或操作：

```text
登录页、支付页、密码管理器、私人文档、注册表、安装器、系统设置、管理员窗口、UAC 弹窗
```

如果某个新场景必须依赖这些目标，不能加入当前生产矩阵。

## 维护规则

新增或修改 Computer Use 能力后，先跑单元测试，再跑这个矩阵。

如果 controlled CLI 不输出某个 token，不要把这个 token 写进 visible-terminal scenario 或 manifest。

如果真实场景偶发失败，先看失败证据，不要直接删除断言。只有确认是 Windows GUI 窗口沉淀问题，才可以在 runner 层增加保守等待。
