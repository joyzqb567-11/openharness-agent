# Computer Use Full 源码复核门禁 2026-06-05

## 当前结论

源码复核后确认：`/computer use --full` 的终极 C 方向尚未成熟完成。当前已经完成的是第一阶段治本门禁：不再允许 recording/representative 证据冒充真实桌面成熟能力。

## 本轮源码改动

- `learning_agent/core/agent.py`
  - 自然语言桌面任务现在调用 `runtime.run_prompt(..., real_actions=True)`。
  - full 未确认时仍安全拒绝。
  - full 已确认但真实执行闭环未注入时，返回 `real_actions_not_enabled_in_desktop_task_runtime`。
  - 文案改为按 `decision` 分支输出，避免把真实闭环缺失说成录制模式成功。

- `learning_agent/computer_use/desktop_task_runtime.py`
  - `ComputerUseDesktopTaskRuntime.__init__` 新增 `real_execution_loop` 注入点。
  - 新增 `_real_execution_report(...)` 汇总真实闭环字段。
  - `real_actions=True` 不再硬编码旧的 recording runtime 拒绝，而是进入可注入真实闭环。
  - `ok_token` 改为只有 `passed=true` 时才写入，避免失败 JSON 也出现成功 token。

- `learning_agent/computer_use/universal_action_dsl.py`
  - 新增真实 sender 识别逻辑，能从 `windows_sendinput_low_level`、低层事件数、真实派发标记推断真实动作。

- `learning_agent/computer_use/universal_paint_pikachu_acceptance.py`
  - 代表性 drag sender 明确不是物理派发。
  - Paint/Pikachu 验收只有物理派发和真实画布变化都存在时才可能成熟。

- `learning_agent/computer_use/universal_final_maturity_matrix.py`
  - 最终成熟矩阵不再把代表性窗口、代表性定位、代表性拖拽当作真实成熟。
  - 当前矩阵应返回未成熟，直到真实 GUI 链路完整接通并通过可见终端验收。

## 自动化验证

已通过：

```text
python -m unittest learning_agent.tests.test_windows_computer_use_full_desktop_task_router
python -m unittest learning_agent.tests.test_windows_computer_use_universal_action_dsl learning_agent.tests.test_windows_computer_use_universal_paint_pikachu_acceptance learning_agent.tests.test_windows_computer_use_universal_final_maturity_matrix learning_agent.tests.test_windows_computer_use_full_desktop_task_router learning_agent.tests.test_windows_computer_use_universal_observe_plan_act_verify_loop
```

## 未完成门禁

真实可见终端交互验收尚未完成，不能声明开发完成。

必须后续启动：

```text
H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat
```

然后在真实可见终端中的 agent 提示符输入真实用户风格 prompt，并观察输出。单元测试、CLI、日志、自测都不能替代该验收。

## 后续建议

下一步应实现默认真实执行 loop：观察真实窗口、绑定 owned window、通过 UIA/vision 定位目标、经 `WindowsSendInputLowLevelSender` 物理派发、动作后截图或 UIA 复核，并把该 loop 注入 `ComputerUseDesktopTaskRuntime`。没有这一步，C 方向不能称为成熟。
