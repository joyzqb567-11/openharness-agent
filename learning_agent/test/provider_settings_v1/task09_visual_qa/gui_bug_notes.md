# Task 9 可见 GUI Bug 记录

## Bug 1：备用 Vite 端口导致 Provider 设置加载失败

- 复现方式：运行 `learning_agent/test/provider_settings_v1/scripts/capture_provider_settings_visual_qa.ps1 -BridgePort 8876 -RendererPort 5277 -CdpPort 9323` 后，真实 Electron 窗口能打开设置弹窗，但 Provider 列表一直没有加载出来。
- 证据 1：`provider_settings_visual_qa_result.json` 记录 `Timed out waiting for provider rows`，说明 GUI 自动验收在等待 Provider 行时超时。
- 证据 2：通过 DevTools Protocol 检查 DOM，设置弹窗显示 `提供商加载失败`，主界面桥接状态显示 `GUI bridge 暂时离线，正在等待本地后端恢复。`
- 证据 3：直接用正确 token 请求 `http://127.0.0.1:8876/v2/gui/provider-settings/providers` 可以拿到 5 个 Provider，说明业务路由和 token 本身可用。
- 证据 4：用浏览器同款 `OPTIONS` 预检请求，带 `Origin: http://127.0.0.1:5277` 和 `Access-Control-Request-Headers: X-OpenHarness-Desktop-Token` 时返回 403，说明真实失败点是 CORS 来源门禁。
- 根因：`learning_agent/app/gui_bridge.py` 只把 `http://127.0.0.1:5177` 和 `http://localhost:5177` 写进 CORS 白名单；视觉验收脚本为了避开已占用端口使用了 `5277`，所以浏览器预检在到达 Provider 业务逻辑前就被拒绝。
- 修复：新增 `_origin_is_allowed()`，固定允许无来源、`null`、`file://`，并允许带显式端口的 `http://127.0.0.1:<port>` 和 `http://localhost:<port>` 本机 Vite 来源；`_send_cors_headers()` 与 `_origin_allowed()` 统一复用该判断。
- 回归：新增 `test_alternate_loopback_vite_origin_can_load_provider_settings`，覆盖 `http://127.0.0.1:5277` 对 `/v2/gui/provider-settings/providers` 的 OPTIONS 预检和 GET 读取。
- 已验证：`python -m pytest learning_agent/tests/test_gui_bridge_security_contract.py learning_agent/tests/test_gui_provider_settings_contract.py -q` 通过，结果为 `8 passed`。

## Bug 2：视觉验收 driver 返回 DOM 元素导致 CDP 克隆失败

- 复现方式：修复 CORS 后重新运行视觉验收脚本，Provider 默认页、OpenAI 连接弹窗、密钥不泄露断言均已通过，但进入自定义 Provider 弹窗阶段失败。
- 证据：`provider_settings_visual_qa_result.json` 记录 `Runtime.evaluate: Object reference chain is too long`，且截图已经生成到 `provider_connected_openai.png`，说明失败发生在后续自定义弹窗等待表达式。
- 根因：`provider_settings_visual_qa_driver.mjs` 中等待自定义弹窗的表达式是 `document.body.innerText.includes('自定义提供商') && document.querySelector('.custom-provider-dialog')`；当左侧为真时会返回 DOM 元素本身，`Runtime.evaluate` 又设置了 `returnByValue: true`，CDP 试图克隆元素对象链后失败。
- 修复：把等待表达式改为 `document.body.innerText.includes('自定义提供商') && Boolean(document.querySelector('.custom-provider-dialog'))`，让 CDP 只返回布尔值。
- 回归方式：重新运行完整 `capture_provider_settings_visual_qa.ps1`，确认自定义 Provider 弹窗截图、模型页截图和移动宽度断言全部继续执行。

## Bug 3：390px 截图使用移动缩放导致没有真正验收窄窗口

- 复现方式：视觉验收脚本通过后查看 `provider_settings_visual_qa_result.json`，移动阶段记录 `scrollWidth: 980`、`innerWidth: 980`，但截图文件名是 `provider_mobile_390x844.png`。
- 证据：CDP 设置 `mobile: true` 时，没有 viewport meta 的桌面页面会使用 980px layout viewport 再缩放到截图宽度；这样断言虽然通过，但没有真正证明 390px 窄窗口无横向溢出。
- 根因：OpenHarness Desktop 是 Electron 桌面壳，应该验收“窗口被缩窄”的布局，而不是手机浏览器的 viewport meta 缩放行为。
- 修复：把 `Emulation.setDeviceMetricsOverride` 的 `mobile` 固定为 `false`，让 `window.innerWidth` 等于脚本设置的实际宽度。
- 回归方式：重新运行完整视觉验收脚本，确认 `viewportResults` 仍包含 `390x844`，且移动断言用真实 `innerWidth: 390` 判断。

## Bug 4：真实 390px 窄窗口被全局 980px 最小宽度撑破

- 复现方式：修复移动缩放后重新运行视觉验收脚本，移动阶段失败，断言详情为 `scrollWidth: 980`、`innerWidth: 390`、`overflowOk: false`。
- 证据：`apps/desktop/src/styles/theme.css` 中 `body` 设置了 `min-width: 980px`，`apps/desktop/src/styles/layout.css` 在 1100px 以下仍保留 `216px + 1fr + 232px` 三栏布局。
- 根因：这些规则适合成熟桌面默认窗口，但在蓝图要求的 390px 视觉验收中会把整个 document 撑宽，导致设置弹窗即使自身有响应式规则也无法通过横向溢出门禁。
- 修复：在 `theme.css` 的 `max-width: 760px` 下把 `body` 的 `min-width/min-height` 归零；在 `layout.css` 的 `max-width: 760px` 下把主壳改成单栏，并隐藏背景左侧栏和右侧检查器。
- 回归方式：重新运行完整视觉验收脚本，确认移动断言变为 `scrollWidth <= innerWidth + 2`，并人工查看 390px 截图没有文字重叠。

## 验收门槛补强：每轮都必须真实打开 API Key 密码框

- 发现：多次运行视觉脚本后，OpenAI 已经处于已连接状态，最终结果里 `API key input has password type` 的详情可能是 `already-connected`。
- 风险：这会让最终验收没有真正证明连接弹窗里的 API Key 输入框仍是 `type=password`。
- 修复：driver 在默认 Provider 截图前先检查 OpenAI 主按钮；如果按钮是 `断开`，先断开并等待回到 `连接`；随后打开连接弹窗，密码框断言只接受 `password`。
- 回归方式：重新运行完整视觉验收脚本，确认结果 JSON 中 `API key input has password type` 的 `details.inputType` 等于 `password`。
