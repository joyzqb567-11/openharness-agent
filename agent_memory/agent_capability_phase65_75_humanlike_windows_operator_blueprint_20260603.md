# 2026-06-03 Phase65-75 Humanlike Windows Operator Blueprint Record

本记录把用户新增的最终标准正式纳入 Phase65-75 蓝图：`learning_agent` 的 Computer Use 最终要做到拟人操作，也就是用户能在 Windows 上手动操作的普通应用程序，agent 也能通过 prompt 观察、理解、动作、校验和恢复。

核心结论：
- 后续实现不能退化成每个应用一个脚本。
- 正确方向是通用观察、规划、动作、校验、恢复闭环。
- 代表性真实应用 E2E 用来证明通用性，不要求给每个应用单独做 E2E。
- Paint 画图软件绘制简化皮卡丘/黄色卡通电气鼠已加入 Phase74 代表性场景。

新增 Paint 场景边界：
- 必须启动真实 `mspaint.exe`。
- 必须通过真实鼠标键盘动作操作画图软件。
- 必须识别画布区域、选择颜色并绘制图形。
- 必须包含黄色主体、黑色耳尖、红色脸颊、眼睛、嘴巴、闪电尾巴。
- 必须保存到受控测试目录并保存视觉证据。
- 不允许直接生成图片文件冒充画图结果。

Phase75 最终矩阵必须包含：

```text
PHASE75_HUMANLIKE_WINDOWS_OPERATOR_READY
prompt_to_any_normal_app=true
humanlike_observe_act_verify_loop=true
generic_windows_app_control=true
per_app_scripts_required=false
uia_ocr_vision_fusion=true
mouse_keyboard_window_control=true
failure_recovery=true
representative_real_apps_passed=true
mspaint_pikachu_scenario=true
real_paint_app_control=true
humanlike_drawing_actions=true
direct_image_file_cheat=false
abort_safety=true
high_risk_confirmation=true
```

正式蓝图文件：
- `docs/superpowers/specs/2026-06-03-humanlike-windows-operator-blueprint.md`

当前状态：
- 本步骤只写蓝图和记忆锚点，不修改运行代码。
- 因未新增 agent 功能代码，本步骤不声明功能开发完成。
- Phase65-75 开始实现后仍必须逐阶段执行自动化测试、编译检查和真实可见终端验收。
