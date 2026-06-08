# Stage 7：插件站点权限执行计划

日期：2026-06-01

项目根目录：`H:\codexworkplace\sofeware\OpenHarness-main`

## 阶段目标

在 Stage 6 插件写动作已经可执行的基础上，给 Chrome 插件 provider 加上 origin 级权限边界。

未授权 origin 只能看连接状态，不能读取页面、定位元素、点击、输入、按键、上传、提交或读取高风险日志。

## 成功标准

1. `BrowserSitePermissions` 支持按 origin 授权具体权限：`read`、`click`、`type`、`submit`、`upload`、`console`、`network`。
2. `ChromeExtensionProvider` 在执行 `browser_snapshot`、`browser_tabs_context`、`browser_visual_locate`、`browser_click`、`browser_type`、`browser_press_key`、`browser_open` 前检查对应 origin 权限。
3. 未授权 origin 调用读/写工具会失败，并提示需要使用 `browser_site_grant` 授权。
4. 授权 origin 后，只允许已授权的动作类型，不能因为授权了 `read` 就自动允许 `click/type/submit`。
5. `browser_site_grant` 支持 `permissions` 参数，并把权限变化同步到 Chrome extension provider。
6. 权限变化可以被状态和事件审计看到，至少包含 origin、permissions、action。
7. 单元测试、相关回归、全量回归、真实可见终端验收和独立 verifier 都通过。

## 范围边界

本阶段不做图形化授权 UI，不做真实扩展安装流程。

本阶段不新增模型可见 provider-specific 工具；仍通过统一 `browser_site_grant` 配置权限，通过统一 `browser_*` 工具执行动作。

本阶段只实现 Chrome extension provider 的站点权限边界；CDP 和可见 Chromium 的既有站点授权兼容逻辑不作为主改造目标。

## 执行步骤

1. 写红灯测试 `learning_agent/tests/test_chrome_extension_site_permissions_stage7.py`，覆盖权限模型、provider 拦截、授权后放行、server 工具同步。
2. 扩展 `BrowserSitePermissions`，让它支持按 origin 的 action-level 权限集合和 permission event。
3. 扩展 `ChromeExtensionBridgeState`，提供 active tab URL/origin 查询和 permission event 摘要。
4. 扩展 `ChromeExtensionProvider`，在读写工具执行前检查所需权限。
5. 扩展 `browser_site_grant` schema 和实现，支持 `permissions` 列表并同步插件 provider 权限。
6. 新增 Stage 7 acceptance scenario，并把计划和修改备份到 `learning_agent/test/browser_dual_track_stage7_20260601/`。
7. 运行聚焦单测、相关回归、`py_compile`、全量 `unittest discover`、真实可见终端验收和独立 verifier。

## 停止条件

如果未授权 origin 能执行 `browser_click`、`browser_type` 或 `browser_press_key`，必须停止并修复。

如果授权 `read` 后自动放行 `click/type/submit`，必须停止并修复。

如果真实可见终端验收未通过，不能声明 Stage 7 完成。
