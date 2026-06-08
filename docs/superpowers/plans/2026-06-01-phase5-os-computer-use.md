# Phase 5：OS 级 Computer Use 书面计划

## 目标
- 在项目内补齐 OS 级 Computer Use 的工具面、执行入口和安全边界。
- 默认不偷偷控制用户桌面；真实桌面动作必须显式确认并经过权限询问。
- 为后续接入真实 Windows/桌面自动化后端预留稳定接口。

## 范围
- 新增 `computer_status`：只读查看 OS Computer Use 后端是否可用。
- 新增 `computer_action`：统一承载 screenshot、move_mouse、click、double_click、type_text、press_key、scroll。
- 新增控制器和 backend 协议：默认后端为不可用，测试后端可验证动作编排。
- 接入工具 schema、catalog 元数据、executor 分发表和 `LearningAgent` 方法。

## 不做
- 本阶段不默认调用真实系统鼠标键盘 API，避免未验收前产生不可控桌面副作用。
- 本阶段不绕过现有 `ask_permission` 权限模型。

## 成功标准
- `computer_status` 能返回结构化、可读的可用性状态。
- `computer_action` 在没有 `confirm_desktop_control=true` 时拒绝执行。
- 默认不可用后端会明确告诉用户需要配置真实后端。
- 测试后端能记录动作并返回可验证结果。
- 工具目录把 `computer_action` 标记为高风险、需要用户交互、禁止并发。

## 验证
- 先写失败测试：`python -m unittest learning_agent.tests.test_os_computer_use_stage17`
- 实现后运行该测试和相关工具回归。
- 最终 Phase 7 再进入真实可见终端验收。
