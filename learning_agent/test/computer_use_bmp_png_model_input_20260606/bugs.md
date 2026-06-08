# 问题与风险记录

## 2026-06-06 Computer Use Full Paint Cat Route Risks

已处理风险：
- 现象：用户输入“请使用本机电脑画图软件画一只猫”时，旧设计不能证明真实打开 Paint 并画猫；更早的大象场景也暴露出旧对象特例可能误画皮卡丘。
- 根因：Paint 真实闭环只声明并实现了少数对象，且默认 full 路由先前没有把真实用户路径稳定接到受支持 Paint 绘图闭环。
- 修复：新增猫 primitive；Paint loop 识别猫 prompt、选择猫计划、返回猫专属视觉字段；LearningAgent 默认 full runtime 显式启用受支持 Paint 绘图桥。
- 验证：猫 primitive/loop focused tests 7 OK；full desktop task router regression 36 OK。

剩余风险：
- 这次修复只把“猫”加入已支持 Paint 绘图对象，并修正默认 full 路由；它仍不等于任意图像绘制能力成熟。
- 当前 Paint 绘图桥仍是有限对象计划，报告通过 `subject_specific_planning=true` 和 `natural_language_planner_ready=false` 明确边界。
- `start_oauth_agent.bat` 可见终端验收已完成并通过，证据在 `learning_agent/acceptance_controller/runs/computer_use_full_paint_cat_strict-20260606_111046/result.json`。
- 真正接近 Codex Computer Use 的设计还需要后续把自然语言视觉规划、屏幕观察、鼠标键盘动作和迭代校正接入通用 observe-plan-act loop。

---

## 2026-06-03 Phase 56 Windows Real Screenshot Pipeline Risks

已处理风险：
- 旧风险：Phase45 证明 provider/evidence 合同，但 fake bytes 可能让黑屏、空白图或坏尺寸 artifact 误过。已处理：Phase56 新增 `Phase56PixelGuard`，解析 BMP 头、尺寸、位深、像素采样、全黑/全白、颜色多样性和标题区域可见性。
- 旧风险：helper v2 的 `capture_window` 仍可能停留在 Phase55 占位摘要。已处理：`WindowsNativeHelperV2Worker` 支持注入或默认创建 `WindowsRealScreenshotPipeline`，并返回 `pixel_guard_passed`、artifact 路径和 provider 尝试链。
- 旧风险：真实 Windows 截图可能在 WGC 缺依赖时被误报失败或被 fake 代替。已处理：Phase56 继续 WGC-first，但本机缺 WGC 绑定时诚实记录失败并 fallback 到 `win32_gdi_printwindow`。
- 旧风险：截图 IPC 可能带出原始二进制内容。已处理：pipeline 和 helper v2 都设置 `screenshot_bytes_included=false`，并删除 `screenshot_bytes` / `raw_bytes` 字段。
- 旧风险：真实 smoke 可能误截图用户窗口。已处理：Phase56 只启动并匹配自己的临时 Notepad 文件窗口，结束后清理。

剩余风险：
- 当前 WGC 仍未真实可用，原因是本机缺 `winrt.windows.graphics.capture` / `winsdk.windows.graphics.capture` 绑定。
- GDI fallback 对某些 UWP、硬件加速、最小化、遮挡或权限特殊窗口可能失败或截图不完整。
- Phase56 还不提供 OCR、视觉定位或 UIA 控件语义；这些仍属于 Phase57 及后续。
- Phase56 不扩大 SendInput 或真实鼠标键盘动作；真实动作仍要等待 Phase58 的目标校验和安全门禁。

---

## 2026-06-05 Universal Computer Use Permission Mode Risks

Resolved design risks:
- Old risk: continuing to add per-app allowlists would make Computer Use non-universal.
- Handling: the new spec requires `/computer use` to open a universal mode governed by action risk and target risk, not an ordinary-app allowlist.
- Old risk: Notepad/Paint/Explorer live scenarios could be mistaken for the product architecture.
- Handling: the new spec treats representative apps as acceptance samples only and keeps Phase92/93 as the universal runtime foundation.
- Old risk: user-facing `/computer use` could be misunderstood as fully unrestricted desktop takeover.
- Handling: the new spec separates observe, normal, and full modes. Normal mode controls ordinary apps; full mode requires strong confirmation, short TTL, abort/stop, target recheck, and audit.
- Old risk: the project could keep relying on `/computer approve <app>` as the main path for ordinary desktop control.
- Handling: the new spec keeps approve/grants/revoke for special high-risk or longer-lived grants, but not as the normal ordinary-app control path.

Remaining risks:
- Implementation still needs to add `ComputerUseModeSession` and command handling for `/computer use`, `/computer use --observe`, `/computer use --full`, `/computer stop`, and `/computer permissions`.
- The action-risk and target-risk classifier must be strong enough to reject terminals, admin/security/system/auth/payment/private-data targets before low-level send.
- `/computer use --full` must not become a one-command bypass; it needs explicit confirmation, TTL, status visibility, audit, and stop.
- Real physical dispatch must still recheck target identity and abort state before every low-level event.
- Future acceptance must prove generic mode behavior through the visible terminal and must show the path does not call a per-app Notepad/Paint controller.
- The implementation plan now exists, but no production code has been changed yet; future agents must not describe Phase98-101 as completed until tests, compile checks, and `start_oauth_agent.bat` visible-terminal acceptance pass.

---

## 2026-06-05 Phase104 Controlled Notepad Launch Smoke Risks

已处理风险：
- 现象：直接真实 Phase104 smoke 首次失败，`process_ownership_verified=true`、`cleanup_completed=true`，但 `visible_window_verified=false`。
- 根因：Windows 11 Notepad 可能通过 wrapper/代理进程启动，`subprocess.Popen` 返回的 pid 与真实可见 Notepad 窗口 pid 不一致；旧逻辑要求窗口 pid 必须等于启动 pid，因此误失败。
- 额外风险：首次失败后仍可见一个 Phase104 受控 Notepad 窗口，说明只清理 wrapper 进程不足以证明窗口收尾。
- 修复：Phase104 改为每次生成唯一受控文件名，启动前记录窗口 baseline，允许启动后新出现的唯一标题 Notepad 窗口通过验证，并对 pid 不同的已验证窗口发送受控关闭。
- 验证：新增两个回归用例覆盖代理 pid 不一致和代理窗口关闭；Phase104 focused tests 5 OK；真实 CLI smoke 输出 `verified_window_cleanup_completed=true`；可见终端验收和独立 verifier 均通过。

剩余风险：
- Phase104 的真实关闭只针对已验证的唯一标题 Notepad 窗口，仍不应扩展成任意窗口关闭能力。
- 如果未来 Windows Notepad 的窗口标题、类名或关闭行为变化，Phase104 可能需要更新窗口身份规则，但不能放宽到按标题关闭用户窗口。
- Phase104 不代表 `/computer use --full` 可以随意打开所有应用；它只是受控 Notepad launch smoke。

---

## 2026-06-04 Phase97 Real Notepad Driver Quality Findings

已处理风险：
- 现象：Phase97 driver 成功路径在 fake sender 中发送 `key_down/key_up` 形式的 Ctrl+S，但默认真实 `WindowsSendInputLowLevelSender` 原先只处理 `set_foreground`、鼠标事件和 `unicode_text`。
- 根因：测试替身接受了按键事件形状，但真实 sender 没有对应分支，导致真实 Notepad 可能只收到文本而没有保存。
- 修复：真实 sender 只新增 `ctrl` 和 `s` 两个虚拟键白名单，Phase97 继续使用 `key_down/key_up` 表达 Ctrl+S，但没有开放任意键盘控制。
- 验证：新增 `Phase97InspectableLowLevelSender` 测试，确认真实 sender 分发 `ctrl down -> s down -> s up -> ctrl up`，同时 Phase97 focused tests 9 OK。

已处理风险：
- 现象：默认 launcher 返回空 `window_id` 时，旧复核逻辑可以通过标题线索匹配后续 Notepad 窗口。
- 根因：无 hwnd 场景缺少更硬的目标身份，多个 Notepad 或旧 Phase97 标题窗口可能被误当成本次启动目标。
- 修复：无 `window_id` 时必须匹配 `pid/process_id`，否则拒绝；同标题不同 pid 测试覆盖为零事件失败。
- 验证：新增 same-title/different-pid 拒绝测试，Phase97 focused tests 9 OK。

已处理风险：
- 现象：默认 launcher 启动 Notepad 后缺少 cleanup 路径。
- 根因：driver 早退和成功路径没有统一收尾点。
- 修复：默认 launcher 记录自己启动的进程，driver 使用 `finally` 调用可选 cleanup。
- 验证：正向 driver 测试断言 fake launcher cleanup 调用 1 次，Phase95+97 regression 14 OK。

剩余风险：
- Phase97 真实可见终端验收已通过，旧风险关闭。
- 仍不得把 Phase97 误读为通用桌面控制；它只证明受控 Notepad 固定文本 live edit。

后续新增处理：
- 现象：真实 Notepad 输入前复核失败，报告为 `target_recheck_before_input_failed`。
- 根因：Windows 11 Notepad 可能通过单实例进程承载窗口，`subprocess.Popen` 返回的 pid 与真实 Notepad 窗口 pid 不一致；旧 pid 强匹配过严。
- 修复：每次合同使用唯一目标文件名，启动前记录已有同名受控窗口 key，复核时接受启动后新出现的唯一文件名 Notepad 窗口。
- 验证：直接真实 CLI 和可见终端验收均通过。

后续新增处理：
- 现象：真实 Notepad 文件已出现 `*` 未保存标记或保存后内容丢字/重复字，`saved_file_verified=false`。
- 根因：对 Windows 11 Notepad 逐字符 Unicode SendInput 长文本不可靠，且 Ctrl+S 需要更稳定的真实输入路径。
- 修复：Phase97 改为复核目标后点击 Notepad 编辑区，再使用临时剪贴板粘贴固定受控文本，并尽力恢复原文本剪贴板；保存仍使用受控 Ctrl+S。
- 验证：直接真实 CLI 输出 `PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK`，可见终端 controller 和独立 verifier 均通过。

---

## 2026-06-03 Phase 55 Windows Native Helper V2 Risks

已处理风险：
- 旧风险：Phase44 仍是 in-process native host 合同，不能证明 helper 崩溃或卡死时主 agent 不被拖垮。已处理：Phase55 新增 `WindowsNativeHelperV2Client`，通过真实子进程 JSONL 协议覆盖启动、请求、cleanup、超时和崩溃路径。
- 旧风险：Windows 中文 stdout 可能按系统代码页写出，父进程按 UTF-8 读取时触发 `UnicodeDecodeError`。已处理：子进程启动时显式设置 `PYTHONIOENCODING=utf-8`，父进程也用 UTF-8 且 `errors="replace"` 读取。
- 旧风险：helper 崩溃后，后续请求可能返回不稳定的 transport error，让主 agent 不知道是否应该重启。已处理：client 在 EOF、坏管道或进程退出后标记 `_process_unavailable`，下一次请求稳定返回 `native_helper_v2_process_unavailable`。
- 旧风险：超时或崩溃测试可能残留 stdio 句柄和 worker 进程。已处理：`close()` 会终止/杀掉 worker、等待退出并关闭 stdin/stdout/stderr。
- 旧风险：Phase55 架构落地后可能被误解为已经允许真实桌面动作。已处理：`send_input` 默认拒绝，`actions_expanded=false`，截图和 UIA 只返回结构化占位摘要。

剩余风险：
- Phase55 尚未接入真实 Windows.Graphics.Capture/GDI 截图 pipeline，真实截图由 Phase56 处理。
- Phase55 尚未接入真实 UIAutomation 控件树和语义 locator，真实 UIA 由 Phase57 处理。
- Phase55 尚未开放真实 SendInput，动作执行必须继续等待 Phase58 的目标校验、安全门禁和真实验收。

---

## 2026-06-03 Phase 38 Windows ComputerUseApproval Risks

已处理风险：
- 旧风险：完成 SendInput executor 合同后，如果没有 session approval，真实动作可能只依赖锁和窗口校验，缺少 ClaudeCode 风格 app allowlist。已处理：新增 `WindowsComputerUseApprovalModel.grant_for_session()` 和 `evaluate()`，并可注入 controller。
- 旧风险：终端、PowerShell、认证弹窗、密码管理器等高风险窗口可能被当成普通 app 授权。已处理：approval 模型对 shell/codex_ui/system_settings/password_manager/auth 分类返回 `denied_forbidden_target`。
- 旧风险：系统级组合键如果只作为普通 `press_key` 处理，可能绕过危险权限确认。已处理：`ctrl+alt+delete`、`win+`、`alt+tab`、`ctrl+shift+esc` 等需要 `systemKeyCombos=true`。
- 旧风险：用户在真实终端只看到 lock/abort 状态，看不到 approval 边界。已处理：`/computer status` 追加 `Computer Use Approval` 摘要。
剩余风险：
- Phase38 不是图形化审批弹窗，后续如果需要接近 ClaudeCode 的交互体验，还要补 terminal/GUI approval UI。
- 当前 approval grant 存在于模型实例内；若未来要跨 turn/session 持久化授权，需要单独设计持久化、过期和撤销。
- Phase38 不证明真实底层 `ctypes.SendInput`、Windows.Graphics.Capture 或 UIA 已成熟；这些仍需后续阶段继续验证。
- 禁止目标分类基于摘要关键词，未来接入真实窗口 inventory 后还需要结合 process path、window class、签名或更可靠的安全分类。

---

## 2026-06-03 Phase 37 Windows SendInput Executor Risks

已处理风险：
- 旧风险：Windows 后端写动作仍可能停留在 `SetCursorPos + mouse_event` 的散落实现，难以统一审计和注入测试。
- 已处理：Phase37 新增 `WindowsSendInputExecutor` 合同，并让 `WindowsComputerUseBackend` 把鼠标/键盘写动作统一路由到 action executor。
- 旧风险：SendInput 成功路径如果只能靠真实鼠标键盘验证，会污染用户桌面。
- 已处理：执行器支持注入 fake implementation，自检和单元测试只记录规范事件，不触碰真实鼠标键盘。
- 旧风险：`type_text` 原文可能从底层 dispatch 返回值、事件或可见日志泄露。
- 已处理：执行器只生成文本长度、短哈希和 `text_redacted=true`；底层 dispatch 结果也会按键名递归脱敏。
- 旧风险：完成 SendInput 合同后，模型或后续开发者可能误以为可以绕过 Phase30/31 门禁直接执行 OS 写动作。
- 已处理：controller 仍保留确认、可信窗口、持锁、abort 和 evidence 门禁；执行器 status 也明确 `safe_gate_required=true`。
剩余风险：
- 当前阶段没有实现真实底层 `ctypes.SendInput`，只证明合同、注入点、路由和脱敏。
- 真实底层实现未来仍需单独处理虚拟键映射、Unicode 输入、滚轮单位、鼠标坐标、DPI、多显示器、前台窗口一致性和系统权限差异。
- Phase38 需要补 approval 模型，避免真实动作在“用户没明确确认目标和风险”的情况下继续扩展。

---

## 2026-06-03 Phase 36 Windows.Graphics.Capture Provider Risks

已处理风险：
- 旧风险：Phase33 diagnostics 只把 WGC 当作未来缺口文字列出，没有真正 provider 合同。
- 已处理：新增 `WindowsGraphicsCaptureProvider`，并让 diagnostics 的 WGC 项来自 provider.status，暴露 `contract=phase36_windows_graphics_capture_provider`。
- 旧风险：发现 WGC 依赖时可能被误当成真实截图已经可用。
- 已处理：Phase36 同时要求 dependency 和 capture_impl；当前未接真实实现时输出 `fallback_required=true`。
- 旧风险：为了证明 WGC 可能误造 fake screenshot artifact。
- 已处理：默认缺依赖/缺实现时 `capture_window()` 返回未捕获结果，不伪造截图 bytes。

剩余风险：
- 当前机器缺少 `winrt.windows.graphics.capture` / `winsdk.windows.graphics.capture`，所以 WGC 仍未在本机真实截图。
- 真实 WGC helper 未来可能涉及用户授权、窗口选择、高 DPI、遮挡、最小化窗口和权限差异，需要单独验收。
- Phase37 SendInput 不能因为 Phase36 provider 合同完成就直接放宽桌面动作范围。

---

## 2026-06-03 Phase 35 Windows Real UIA Smoke Risks

已处理风险：
- 旧风险：Phase34 主要通过 fake UIA module 验证 provider 合同，容易被误读成真实 Windows UIA 已经打通。
- 已处理：Phase35 新增 `real_uia_smoke.py`，默认先探测 `uiautomation` 依赖；依赖缺失时输出 `dependency_available=false`，不启动窗口、不声明真实 UIA 已验证。
- 旧风险：真实 smoke 如果扫描任意桌面窗口，可能读取用户敏感窗口。
- 已处理：Phase35 只查找自己创建的安全 Notepad 临时文件窗口，输出 `safe_window_only=true`，并保持 `actions_expanded=false`。
- 已确认工具经验：PowerShell controller 的 `-ScenarioPath` 相对路径会按 controller 目录拼接；从项目根调用时应传绝对路径或 `scenarios\xxx.json`。

剩余风险：
- 当前环境缺少 `uiautomation`，所以 `real_uia_verified=false` 是诚实诊断结果，不代表本机已完成真实 UIA 文本读取。
- Phase35 不包含 Windows.Graphics.Capture、SendInput、DPI、多显示器、approval UI 或全局 abort hook。
- 后续 Phase36/37 仍必须延续“不安装系统依赖、不写注册表、不自动操作敏感窗口”的边界。

---

## 2026-06-03 Phase 30 Windows Computer Use Safe Action Gate Risks

已处理风险：
- 旧风险：动作执行只有 confirm/window 校验，没有 durable desktop lock，两个会话可能同时控制同一桌面。
- 已处理：新增 `ComputerUseLockManager`，显式注入锁管理器时必须由当前 `owner_session_id` 持锁后才能执行动作。
- 旧风险：没有 abort flag，用户或 harness 无法在下一次动作前可靠阻断桌面控制。
- 已处理：新增 abort request/clear/status，controller 在调用后端前检查 abort 并拒绝动作。
- 旧风险：窗口相对坐标可能被当成屏幕坐标传给后端，导致点击落点错误。
- 已处理：`action_policy.prepare_action_arguments()` 会用 window rect 将相对 x/y 转成屏幕 x/y，并在 `action_evidence.coordinate_used` 记录转换来源。
- 旧风险：`type_text` 原始文本可能进入内存后端日志、controller audit、权限提示或 action evidence。
- 已处理：统一使用脱敏摘要，只保存 `text_length`、`text_sha256_16` 和 `text_redacted=true`。

剩余风险：
- Phase 30 仍使用内存后端和静态窗口样本验收，不代表真实 SendInput 已安全可用。
- 真实 Windows native helper、DPI、多显示器、窗口遮挡、前后台窗口一致性、动作前后真实截图 evidence chain 仍需后续 Phase 31+ 分阶段实现。
- 真实动作目标仍必须避开终端、Codex UI、安全/隐私设置、密码管理器、认证弹窗和 Windows Run。

---

## 2026-06-02 Phase 27 Windows Computer Use Protocol Risks

已处理风险：
- 旧风险：`computer_action` 只有松散参数，模型可以声明窗口相关意图但控制器无法验证目标窗口是否真实存在。
- 已处理：`computer_action` 增加可选 `window` 目标；如果提供窗口目标，控制器会先用只读 `get_window_state` 验证，不认识的窗口直接拒绝且不调用后端。
- 旧风险：观察和动作混在 `computer_action` 中，容易让只读状态查询也被当成高风险桌面动作。
- 已处理：新增 `computer_observe`，catalog 标记为低风险只读并发安全；`computer_action` 继续保持高风险串行。
- 已确认验收控制器 bug：场景缺省 `event_payload_contains` 时，PowerShell 的 `@($null)` 会让 foreach 产生一个 null 检查项，随后用 null 做字典 key 抛错。
- 已处理：`controller.ps1` 读取 `debug_log_contains`、`event_answer_contains`、`event_payload_contains` 时过滤空值和 null。

剩余风险：
- Phase 27 还没有真实 Windows 窗口枚举；`WindowsComputerUseBackend.observe()` 目前是明确占位。
- 真实 Windows 后端仍不能声明达到 Codex Computer Use 插件级别；截图、UI Automation、DPI、多显示器、窗口遮挡和前台窗口锁都需要 Phase 28+ 分阶段验证。
- 后续验收必须继续避免终端、Codex UI、安全/隐私设置、密码管理器、认证弹窗和 Windows Run。

---

## 2026-06-02 Phase 26 Windows OS Computer Use Blueprint Risks

已确认风险：
- Phase 25 编号已经被真实 extension/native-host 连接后续占用；如果继续把 Windows OS Computer Use 称为 Phase 25，会污染项目历史。处理：本轮改用 Phase 26。
- learning_agent 当前 Computer Use 仍主要是安全外壳和最小 Windows ctypes 占位能力，尚未达到 Codex Computer Use 的窗口截图、UI Automation 文本树和窗口相对动作成熟度。
- 直接实现真实鼠标键盘动作风险高，可能误控终端、Codex UI、安全设置、密码管理器或认证弹窗。处理：蓝图要求后续先做协议和只读观察，再做动作。
- Codex Computer Use 插件只能作为参考，不应成为 learning_agent 生产依赖；否则 learning_agent 离开 Codex 环境会失去独立能力。

剩余风险：
- Windows native helper 技术选型仍需在 Phase 27/28 前确认：推荐 C#/.NET helper，但实现工作量高。
- Windows.Graphics.Capture、UI Automation、DPI 缩放、多显示器、窗口遮挡和权限问题需要逐阶段验证，不能一次性假定可用。
- 未来真实端到端验收必须避免自动化终端本身，建议使用 Notepad 或专用安全测试应用。

---

## 2026-06-01 Stage 12 可见浏览器验收格式风险
已处理风险：
- 现象：旧 `browser_visible_runtime_acceptance.json` 场景中，真实浏览器工具全部执行成功，debug log 也包含 `browser_launch_visible`、`browser_open`、`browser_snapshot`、`browser_screenshot`、`browser_flow_run`、`browser_plugin_status`，但最终回答没有逐字复制长验收行，导致 controller 判定失败。
- 判断：这是验收输出格式问题，不是浏览器能力失败；但不能把该失败场景当作通过。
- 处理：新增 `browser_dual_track_stage12_acceptance.json`，把真实浏览器动作交给 debug log 断言，把最终回答收敛为短标记 `BROWSER_DUAL_TRACK_STAGE12_READY STAGE12_VISIBLE_BROWSER_OK`。
- 结果：新 Stage 12 场景 controller 完成且独立 verifier `assertion.passed=true`。
剩余风险：
- 长验收行容易被模型摘要化，后续验收场景应优先用 debug log 检查工具证据，用短 marker 检查最终回答。

## 2026-06-01 Browser Dual Track Stage 11 Harness 接入风险
已处理风险：
- 旧风险：browser runtime 已有 run/action/observation，但没有同 id harness run，导致浏览器任务仍像旁路系统，长任务状态、verifier 和 resume 无法统一观察。
- 已处理：新增 `BrowserHarnessMirror`，在 browser run 创建、provider decision、finish、flow report 同步四个生产节点写入 harness run/stage/event/verifier。
- 已确认并修复的 bug：`BrowserHarnessMirror` 初始化早于 `learning_agent/memory` 目录创建时，`browser_harness_store_for_workspace()` 可能误选项目根 `memory/harness`，而测试和状态快照随后读取 `learning_agent/memory/harness`，导致同 id harness run 查不到。
- 修复方式：项目根 workspace 固定写入 `learning_agent/memory/harness`，只有 workspace 本身就是 `learning_agent` 包目录时才写入直接 `memory/harness`。
剩余风险：
- Stage 11 已把浏览器 runtime 投影进 harness，但 ClaudeCode 级别的远程任务生态和更复杂 UI 状态生态仍属于 Stage 12 总验收后的后续增强范围。

## 2026-06-01 BrowserActionExecutor 执行层风险与处理

已处理风险：
- 旧风险：`BrowserActionExecutor` 只负责 begin/progress/complete/fail 记录，真实浏览器工具 handler 仍由 `BrowserAutomationServer.call()` 直接执行，导致执行器不是调度中心。
- 已处理：新增 `execute_action()`，让执行器统一接管 handler 调用、attempt progress、retry、成功完成、失败分类和 observation 回填。
- 旧风险：server 的 browser runtime event log、旧 action log、observation id 和 retry 摘要分散在 `call()` 的手写 wrapper 中，容易形成 executor 和 server 双轨。
- 已处理：server `call()` 现在通过回调把这些生产侧副作用挂到 `execute_action()`，生命周期最终由同一个 executor 收尾。
- 已确认并修复的 bug：`browser_flow_run` 外层工具持有普通写锁后递归调用内层浏览器工具，内层再次申请同一把锁会死锁；已把写锁改成 `threading.RLock()`，相关 flow_run 用例从超时恢复为通过。
- 已处理：旧 runtime store 测试只期待 started/completed；现在已更新为 started/progress/completed，避免 progress 事件丢失时测试仍误通过。

剩余风险：
- 当前执行器已经接管单个工具调用和嵌套流程，但还没有实现 ClaudeCode 级别的多工具并发批处理、真正的工具结果流式分块输出和远程任务 UI/SDK 生态。
- `browser_automation_mcp_server.py` 仍很大，后续新增浏览器能力时应优先拆到 `learning_agent/browser/` 下的独立模块，避免重新堆回 server。
- 真实可见终端验收已通过本轮执行层场景；后续每次修改浏览器执行链路仍必须继续跑 `start_oauth_agent.bat` 可见终端验收，不能只用单元测试替代。

## 2026-06-01 BrowserActionExecutor 批量并发与流式结果风险

已处理风险：
- 旧风险：执行器只能一次执行一个动作，上层即使有多个只读浏览器动作也无法表达批处理，后续 UI/SDK 或模型工具调度容易继续手写并发。
- 已处理：新增 `execute_batch()`，当批次全部是 `BrowserActionPolicy` 判定为并发安全的读工具时使用线程池并发执行，并按输入顺序返回结果。
- 旧风险：如果简单把所有动作都并发，点击、输入、导航这类写工具会和读取动作抢同一页面状态。
- 已处理：`execute_batch()` 只要发现任一写工具就整体串行执行，先保证真实浏览器页面不被并发污染。
- 旧风险：长工具或未来流式工具只能等最终字符串返回，状态页和外部 controller 无法看到中间输出。
- 已处理：`execute_action()` 支持 `on_result_chunk`；非字符串可迭代结果会逐片段写入 `browser_action_progress` 的 `result_chunk`，并回调给上层。

剩余风险：
- 当前批处理是执行器内部 API，尚未接入 `LearningAgent` 主工具调度器；也就是说模型一次给多个工具调用时，还不会自动合并成 executor batch。
- 当前流式结果支持 Python iterable handler；真实 MCP stdio 的逐 token/逐 event 流式协议还没有接入，需要后续在工具协议层继续扩展。
- 批处理当前采用“含写工具整体串行”的保守策略，安全但不够激进；未来可升级为按读写阶段分组，例如读读并发、写串行、写后读再并发。

## 2026-05-31 Long-Task Harness v1 风险与边界

已处理风险：
- 旧风险：`learning_agent` 的 `task_runs`、`cron_records`、`monitor_records`、`background_commands` 主要是内存结构，长任务遇到进程中断后缺少独立持久化恢复底座。
- 已处理：新增 `learning_agent/harness/`，把 run、stage、attempt、queue lease、event log、verification、recovery 和 status CLI 独立成可测试模块。
- 旧风险：阶段性验收如果只靠模型口头说“完成”，Codex 或其他 agent 很难做真实可审计验收。
- 已处理：`StageVerifier` 现在至少支持成功 marker 和 artifact 文件存在性两类确定性检查，并把通过/失败原因写入 `VerificationResult`。
- 旧风险：临时 endpoint timeout 后只能靠人工重新启动任务，容易重复跑已完成阶段。
- 已处理：`HarnessRunner` 会记录阶段 attempts 和 checkpoint，可恢复错误会按 `RecoveryPolicy` 重试，已完成阶段会跳过。

剩余风险：
- 当前 harness v1 仍是独立底座，尚未把真实交互式 `LearningAgent.run_events()` 强制改成 harness 驱动；后续接入时需要新增端到端测试。
- 当前 CLI 先提供 `status` 和 `list`，任务创建和 executor 接入仍以 Python API 为主；如果要给用户直接操作，需要继续补 `enqueue/run` CLI。
- 当前队列通过持久化 lease 状态防止顺序重复领取；如果未来多进程高并发 worker 同时抢占同一个 store，建议继续补文件锁或专用任务数据库。
- 本轮真实可见终端验收已完成：`long_task_harness_status-20260531_152707/result.json` 显示通过；后续新功能仍必须继续遵守同样门禁。

## 2026-05-31 Harness CLI Agent Execution 风险与边界

已处理风险：
- 旧风险：harness v1 只能通过 Python API 创建任务，外部 agent 不能用稳定命令行创建和推进任务。
- 已处理：新增 `python -m learning_agent.harness enqueue` 和 `python -m learning_agent.harness run`。
- 旧风险：runner 虽然能接 executor，但没有官方薄适配层连接真实 `LearningAgent.run()`。
- 已处理：新增 `AgentStageExecutor` 和 `build_default_learning_agent_executor()`，并保持真实 agent 依赖懒加载。

剩余风险：
- `--executor agent` 会启动真实模型和 MCP，适合真实任务，但不适合快速单元测试；测试和 smoke 应优先使用 `--executor echo`。
- 当前 `enqueue` 的阶段参数是轻量 `name::prompt` 文本格式；后续如果阶段配置复杂化，建议增加 JSON 计划文件输入。
- 多 worker 高并发抢同一 store 时仍建议补文件锁；当前实现适合顺序 worker 和可审计教学场景。
- 本轮真实可见终端验收已完成：`harness_cli_echo_run-20260531_154459/result.json` 显示目标 agent 在真实终端中通过 bash 执行了 `enqueue/run/status`，并得到 `status=completed` 与 `acceptance=passed`。

## 2026-05-31 smoke 场景旧权限事件断言误判

状态：已修复并通过真实可见终端 smoke 验收。

证据：
- 失败结果：`learning_agent/acceptance_controller/runs/smoke-20260531_135941/result.json` 显示 `completed=false`，但 `final_printed=true`、`prompt_received=true`、`marker_passed=true`。
- 事件日志显示实际事件链为 `permission_auto_approved -> agent_ready_for_user_prompt -> user_prompt_received -> final_answer_printed -> agent_ready_for_user_prompt`。
- 断言失败点只在 `permission_required=false` 和 `permission_answered=false`，说明真实终端输入和回答已经成功，失败来自场景仍等待旧人工权限事件。

处理：
- 已把 `learning_agent/acceptance_controller/scenarios/smoke.json` 的必需事件改为 `permission_auto_approved`、`agent_ready_for_user_prompt`、`user_prompt_received`、`final_answer_printed`。
- 修复后真实可见终端验收 `smoke-20260531_140112/result.json` 显示 `completed=true`。
- 后续如果客户模式继续默认自动允许内置 MCP server，smoke 场景不应再要求 `permission_required` 和 `permission_answered`。

## 2026-05-31 H 盘运行路径错位风险

状态：已修复当前路径错位；仍需另行处理浏览器测试环境中的 Playwright 依赖缺失。

已确认风险：
- 当前项目实际运行目录为 `H:\codexworkplace\sofeware\OpenHarness-main`，但 `learning_agent/mcp_servers.json` 曾经仍指向旧盘符下的 OpenHarness `learning_agent` 目录。
- 如果不修复，`mcp-doctor` 或真实 agent 启动 MCP server 时会尝试执行旧盘符路径，导致当前 H 盘项目的 browser/search/workspace tools 可能启动失败或启动到旧副本。
- `AGENTS.md` 和 `agent_memory/context.md` 中的旧盘符路径会误导后续 agent 把学习备份、真实终端验收或项目根定位到错误目录。

处理策略：
- 只改当前运行配置和协作上下文路径。
- 不批量改历史验收日志，因为旧日志中的历史盘符路径代表真实运行证据，改掉会污染证据。

验证结果：
- `mcp-doctor` 已确认当前工作区、配置文件和 MCP server 启动路径均来自 H 盘项目。
- 当前活跃配置范围内已搜不到旧 OpenHarness 盘符路径。

剩余环境风险：
- `learning_agent.tests.test_mcp_registry` 中 2 个浏览器自动化测试仍失败，失败原因是运行环境缺少 Playwright：`No module named 'playwright'`。
- 该风险会影响浏览器自动化单元测试，但本次 `mcp-doctor` 已证明 H 盘 MCP 配置本身能解析并启动。

## 2026-05-30 阶段 13B 旧脚本入口收紧风险记录

已处理风险：
- 旧风险：`tests_support/legacy_learning_agent_suite.py` 继续从旧脚本入口大导入，导致测试套件会倒逼 `learning_agent.py` 保留批量 re-export。
- 已处理：遗留测试套件已改为按 `app/core/models/mcp/tools` 分层导入，测试关注点不再绑定旧脚本入口。
- 旧风险：`fake_model_repl.py` 继续示范从旧脚本入口导入 `LearningAgent` 和消息对象，后续开发者容易照抄旧路径。
- 已处理：假模型 REPL 已改为从 `core.agent` 与 `core.messages` 导入。
- 旧风险：`learning_agent.py` 用 `vars(agent_module).items()` 和 `globals()[exported_name]` 批量导出 `core.agent`，让薄入口继续看起来像巨型公共 API。
- 已处理：`learning_agent.py` 已收紧为只启动 `app.cli.main()` 的脚本入口，`__all__` 只公开 `main`。

剩余风险：
- `core/agent.py` 仍然很大，下一阶段应继续拆 run loop、状态对象和工具调度委托，避免只是把巨型入口转移到核心文件。
- 历史学习备份目录 `learning_agent/test/**` 仍保留旧入口字符串，这是归档学习材料，不应作为活跃生产路径修改；扫描活跃代码时需要排除备份目录。
- 当前验收阻塞：真实可见终端验收 `real_chrome_natural_weather_travel-20260530_111154` 被 Codex OAuth/API HTTP 429 `usage_limit_reached` 阻塞，agent 没有机会调用真实浏览器工具；需要额度恢复后重跑验收。
- 备用链路风险：`LEARNING_AGENT_MODEL_PROVIDER=codex` 可找到本机 `codex.exe`，但一次性 run 在 `codex exec` 90 秒超时；当前不能依赖该 provider 绕过 OAuth/API 429 完成真实终端验收。

## 2026-05-30 阶段 13 旧入口回流风险记录

已处理风险：
- 旧风险：`tools/catalog.py`、`mcp/runtime.py`、`models/adapters.py`、`app/cli.py` 和包门面仍导入 `learning_agent.learning_agent`，导致“已经拆模块”但生产路径仍回到旧入口。
- 已确认根因：工具 schema 和工具包装 helper 的事实源仍在旧入口/核心文件附近，导致多个模块为了拿 `TOOL_SCHEMAS` 或 helper 只能回连旧入口。
- 已处理：把内置工具 schema 与能力包映射迁移到 `tools/schemas.py`，并让生产模块直接依赖新事实源。
- 已处理：新增 `tests/test_compat_cleanup.py`，静态扫描上述生产模块，防止它们再次出现 `learning_agent.learning_agent` 导入。

剩余风险更新：
- 阶段 13B 已处理 `learning_agent/learning_agent.py` 批量 re-export 和 `tests_support/legacy_learning_agent_suite.py` 旧入口导入问题。
- `core/agent.py` 仍很大，虽然 schema 和脚本入口已收紧，但 `LearningAgent` 主类仍承载大量 run loop、工具调度、观测和兼容方法；后续应继续拆 `core/run_loop.py`、`core/state.py`、`observability` 委托方法和剩余死代码。
## 2026-05-30 Stage12 Core Agent Split 风险与处理

已处理风险：
- 旧风险：阶段 12 只删除部分不可达代码时，`learning_agent.py` 仍会保留几十万字节核心实现，排查者仍然需要翻主入口，瘦身目标不成立。
- 已处理：`LearningAgent` 主实现整体迁入 `learning_agent/core/agent.py`，`learning_agent.py` 现在只做路径兜底、兼容 re-export 和 `main()` 转发。
- 旧风险：同目录 MCP server 以脚本方式运行时，Python 可能先加载 `learning_agent.py` 顶层模块，导致 `learning_agent.browser_real_chrome` 等子模块导入失败。
- 已处理：薄入口设置 `__path__`，`core/__init__.py` 也保留脚本模式 fallback；已用 `browser_automation_mcp_server.py` 和 `mcp-doctor` 链路验证。
- 旧风险：`core/agent.py` 从包根迁到 `core/` 后，原先按 `Path(__file__).with_name("skills")` 找 packaged skills 的逻辑会误找 `learning_agent/core/skills`。
- 已处理：packaged skill fallback 改为从包根 `learning_agent/skills` 查找，`test_prompts_context` 与完整回归已覆盖。
- 旧风险：真实可见终端验收中，Windows 受限环境让 `tasklist` 返回 Access denied，`ChromeProfileManager.chrome_is_running()` 把检测失败误判为 Chrome 正在运行，导致 `browser_connect_real_chrome` 被阻断。
- 已处理：`chrome_is_running()` 在 `tasklist` 非零退出时改用 PowerShell `Get-Process chrome` 复查；如果 fallback 明确没输出，则不再误报 Chrome 运行中；新增回归测试覆盖该场景。
- 旧风险：同一环境下 Python `Path.exists()` 读取 `C:\Users\joyzq\AppData\Local\Google\Chrome\User Data` 抛 `PermissionError`，导致 `mcp-doctor` 误报 User Data 缺失。
- 已处理：`_existing_path()` 在 Python 路径检查被拒绝时调用 PowerShell `Test-Path` 只读确认，且修复了 `powershell -Command` 下 `$args[0]` 不能稳定传递带空格路径的问题；新增回归测试覆盖带空格 User Data 路径。
- 已验证：`mcp-doctor` 恢复为真实 Chrome profile `available`，并且真实可见终端验收 `real_chrome_natural_weather_travel-20260530_025500` 通过，`permission_sent_count=0`。

剩余风险：
- `core/agent.py` 仍是核心大文件，虽然主入口已经瘦身，但下一轮若继续追求更细颗粒度，可按工具副作用编排、run loop、权限交互、task 编排继续从 `core/agent.py` 内部拆出更小模块。
- 真实 Chrome 环境诊断仍依赖本机 Windows 权限、Chrome 是否正在运行、User Data 是否被锁定和调试端口是否可用；后续如果换机器或换 Windows 权限策略，仍应先跑 `mcp-doctor` 和真实可见终端验收确认。


## 2026-05-29 Modular Tests Layer 风险与处理

已处理风险：
- 旧风险：`learning_agent/test_learning_agent.py` 超过 1MB，所有测试都在一个类里，排查模型层、MCP 层、浏览器层、权限层或提示词层问题时必须翻巨大文件。
- 已处理：阶段 11 新增八个领域测试入口，日常可以按 `learning_agent.tests.test_mcp_registry`、`learning_agent.tests.test_browser_harness` 等路径聚焦运行。
- 旧风险：直接把旧测试文件搬到 `tests_support` 后，大量 `Path(__file__)` 会指向错误目录，导致 staticprompt、skills、MCP server 脚本和 README 文档测试找不到文件。
- 已处理：阶段 11 在 legacy suite 中新增 `LEGACY_TEST_ROOT` 和 `LEGACY_PROJECT_ROOT`，并机械替换旧路径表达式。
- 旧风险：`python -m unittest discover learning_agent` 以目录作为 start_dir 时，会把 `learning_agent.py` 当成顶层模块，遮蔽 `learning_agent` 包名，导致 `learning_agent.tests` 和 `learning_agent.tests_support` 导入失败。
- 已处理：新测试模块使用相对导入；legacy suite 在目录 discovery 模式下强制把项目根放到 `sys.path` 最前，并清理非包的 `learning_agent` 遮蔽模块。

剩余风险：
- 阶段 11 是“低风险分组入口拆分”，遗留测试方法主体仍集中在 `tests_support/legacy_learning_agent_suite.py`；以后若要做到真正每个测试方法物理迁移到对应文件，还需要进一步分批搬迁。
- 当前分组依赖测试方法名关键字，新增测试如果命名不清楚会落入 `core_run_loop` 兜底组；后续新增测试时应使用明确领域关键词。
- 旧入口和 discovery 已通过自动化测试，但阶段 12 完成后仍需要重新跑全量测试，因为删除主文件重复实现可能影响导入兼容。

## 2026-05-29 Modular App Layer 风险与处理

已处理风险：
- 旧风险：CLI 参数解析、OAuth/API 模型构造、`mcp-doctor`、HTTP command bridge 和真实终端主循环全部堆在 `learning_agent.py` 里，启动类问题很难判断属于 app 入口层、模型层、MCP 层还是浏览器层。
- 已处理：阶段 10 新增 `learning_agent/app/cli.py`、`learning_agent/app/doctor.py`、`learning_agent/app/http_bridge.py` 和 `learning_agent/app/interactive.py`，把应用入口编排从主文件迁出。
- 旧风险：如果 app 层直接导入 `LearningAgent`，会和 `learning_agent.py` 的兼容导出形成循环导入。
- 已处理：`app.cli.main()` 使用 `agent_cls` 和 `permission_callback` 参数注入，主文件只负责传入真实类和真实权限回调。
- 已处理：`python learning_agent\learning_agent.py --help`、`mcp-doctor`、`run --prompt "ping" --json --max-turns 1`、`-k command_bridge` 和完整 `unittest` 均已通过，说明旧入口兼容仍可用。

剩余风险：
- `learning_agent.py` 里仍保留 app/main/bridge/model/format 的旧实现体；它们现在位于早返回之后，不再作为真实执行路径，但阶段 12 瘦身时需要删除这些不可达重复代码。
- `mcp-doctor` 的真实 Chrome 诊断仍会受本机 Chrome 是否运行、User Data 是否可访问、9222 端口是否被占用影响；这属于本机环境状态，不是阶段 10 app 拆分导致的失败。
- 阶段 10 已完成自动化验收，但最终整体任务仍必须在阶段 12 后重新完成 `start_oauth_agent.bat` 真实可见终端交互验收，才能声明整体改造完成。

## 2026-05-27 Acceptance Harness 风险与处理

已处理风险：
- 旧风险：外部 agent 只能靠固定等待、SendKeys 和截图猜测 `learning_agent` 真实终端处于哪个阶段，容易把 prompt 输进权限提示或启动阶段。
- 已处理：新增 JSONL 状态事件和终端标记，外部 agent 可以等待 `permission_required`、`agent_ready_for_user_prompt`、`final_answer_printed` 后再行动。
- 旧风险：权限提示无法被外部 agent 稳定识别，脚本只能循环发送 `y`，可能污染主 prompt。
- 已处理：权限函数现在发出 `permission_required` 和 `permission_answered`，可见终端 smoke 脚本只对新权限请求发送一次 `y`。
- 已处理：第一次可见终端 smoke 中裸 `SendKeys("y~")` 没有进入 Windows Terminal 输入行；脚本已改为优先聚焦真实 Windows Terminal 窗口，并用剪贴板粘贴 `y` 再回车。
- 已处理：最终版可见终端 smoke 曾出现 ready 后 prompt 偶发没有进入 agent 的情况；脚本已改为等待 `user_prompt_received`，若 12 秒内未确认则最多重发 3 次 prompt。
- 已处理：PowerShell 5.1 会把无 BOM 的 UTF-8 中文脚本读坏；本轮 smoke 脚本已转换为 UTF-8 BOM 后运行。

剩余风险：
- 可见终端截图在 Windows Terminal 滚动缓冲区中仍可能停留在启动日志附近，未必总能直接截到最终回答；本轮已用真实窗口输入、`final_answer_printed` 事件、`answer_preview`、调试日志和结果 JSON 交叉确认最终输出。
- `LEARNING_AGENT_ACCEPTANCE_EVENT_LOG` 开启后会记录 prompt 和 answer 的短预览；这是验收模式的有意设计，不应在含敏感内容的人工会话中随意开启。
- 浏览器上传/下载单测在一次完整回归中出现过空下载文件的偶发失败，随后单测连续复跑和完整回归均通过；后续若重复出现，应单独固化为浏览器下载时序问题排查。

## 2026-05-27 重庆天气真实可见终端验收风险记录

已确认的健康状态：
- `run_chongqing_weather_visible_terminal_acceptance.ps1` 已成功通过真实可见终端验收，不是 CLI run、HTTP bridge、stdin 管道或只看日志替代。
- 事件日志确认真实窗口中经历了启动 MCP 授权、ready、prompt received、`browser_open` 授权、`browser_snapshot` 授权和 final answer。
- 调试日志确认 `browser_open 成功` 和 `browser_snapshot 成功`，并读取到 Open-Meteo JSON。
- 结果 JSON 的 `log_checks` 全部为 `true`，包括 `browser_open`、`browser_snapshot`、目标日期、城市、来源和旅游攻略。

剩余风险：
- Open-Meteo 预报会随时间刷新，本轮 2026-05-27 22:50 左右读到的重庆 2026-05-30 数值以后可能变化。
- 可见终端截图受 Windows Terminal 滚动位置影响，可能不能完整展示长回答；本轮以事件日志、调试日志和结果 JSON 作为主要机器证据，截图作为可见窗口辅助证据。
- 脚本目前是验收脚本，不是长期产品化 UI 控制器；后续若要做多场景回归，应把窗口控制、事件等待、权限响应和结果断言继续抽成可复用测试库。

## 2026-05-27 Acceptance Controller 风险与处理

已处理风险：
- 旧风险：smoke 和重庆天气验收分别有独立 PowerShell 脚本，窗口控制、权限响应、截图和结果判断重复，后续场景越多维护越难。
- 已处理：新增 `acceptance_controller/controller.ps1`，把真实窗口控制和事件协议统一到一个控制器里。
- 已处理：新增场景 JSON，把任务 prompt、必需事件、调试日志断言和最终回答断言从脚本里抽出来。
- 已处理：新增测试锁定 controller 目录结构和场景 JSON 基本字段，防止后续又退回一堆专用脚本。
- 已处理：controller 版 smoke 和重庆天气场景均已通过真实可见终端验收，证明新控制器能替代旧专用脚本完成核心任务。

剩余风险：
- `controller.ps1` 仍是 PowerShell 实现，适合当前 Windows 可见终端验收；如果未来要跨平台或更复杂 UI 自动化，建议再抽一层 Python/Node 控制库或专用 MCP。
- 当前 controller 自动输入权限默认是对每个 `permission_required` 发送 `y`，适合受控验收场景；真实高风险场景需要给 scenario 增加允许/拒绝策略。
- 当前断言主要依赖事件日志和 debug log 的文本包含检查；后续可升级为结构化 tool-call ledger，让断言更精确。

## 2026-05-27 Real Chrome Profile Status 风险与处理

已处理风险：
- 旧风险：用户明确要求“桌面可见 Chrome、登录态、标签页和插件”后，如果直接让 agent 连接真实 Chrome，可能触碰 cookies、localStorage、sessionStorage、token、登录页面、隐私标签页或插件状态。
- 已处理：新增 `real_chrome_profile_status.json` 安全探针场景，本轮只允许读取真实 Chrome 规则和调用只读 `browser_profile_status`。
- 已处理：场景 prompt 明确禁止打开登录网站、读取 cookies/storage/token、访问隐私页面、读取标签页内容或插件内容。
- 已处理：结构测试要求 real Chrome 场景必须包含 `browser_profile_status` 和“不读取 cookies”等边界，避免后续场景被改成直接接管真实浏览器。
- 已处理：真实可见终端验收确认目标 agent 只调用了 `mcp__browser_automation__browser_profile_status`，最终回答也说明未连接真实 Chrome、未读取隐私内容。

剩余风险：
- 本轮证明的是 profile status 安全探针可用，不等于已经完成“使用用户登录态、已有标签页和插件”的端到端浏览器自动化。
- `mcp-doctor` 显示当前 Chrome 未运行；下一步若要真实连接日常 profile，需要用户明确确认高风险边界，并可能需要启动带本机 CDP 调试端口的 Chrome。
- 当前 controller 默认自动同意权限；真实 Chrome connect 属于高风险工具，后续场景应给权限策略增加“只自动同意 status，connect 必须人工确认或专门白名单”的保护。
- `browser_profile_status` 返回的是当前 MCP 会话状态摘要，不读取 Chrome profile 文件；它不能证明某个具体登录网站已可操作，只能证明安全前置流程和环境状态可用。

## 2026-05-28 Real Chrome Connect Public Page 风险与处理

已处理风险：
- 旧风险：controller 对每个 `permission_required` 都自动输入 `y`，一旦真实 Chrome 场景里模型请求 `browser_evaluate`、tabs、network、downloads 等权限，就可能越界读取敏感浏览器状态。
- 已处理：`controller.ps1` 已支持 `permission_policy`，connect 场景设置 `default_response=deny`，只对白名单权限自动输入 `y`。
- 已处理：`result.json` 现在记录 `permission_policy_decisions`，可复盘每个权限请求为什么被允许或拒绝。
- 已处理：`real_chrome_connect_public_page.json` 明确禁止 `browser_evaluate`，并在 deny list 中拒绝 `browser_evaluate`、tabs、console、network、downloads。
- 已处理：真实可见终端验收确认本轮只调用了 `browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`，未调用 `browser_evaluate`。
- 已处理：第一次 connect 场景失败不是权限策略或 Chrome 连接失败，而是目标 agent 在 status 后的第 4 轮模型调用长时间无返回；已收窄 prompt，第二次验收通过。
- 已处理：本轮测试启动的 Chrome 进程已在验收后清理，避免后续真实 Chrome connect 因 Chrome 正在运行而失败。

剩余风险：
- 真实 Chrome connect 已能打开公开页面，但这仍不等于已经安全操作用户已有登录网站、已有标签页或插件；下一步若要接管已有标签页，需要单独设计更细的用户确认和标签页选择机制。
- 当前 `permission_policy` 是基于权限 action 文本包含匹配；它比无脑同意安全很多，但仍不如结构化 tool-call ledger 精确，后续可把工具名和参数单独写入 acceptance event 便于严格匹配。
- `browser_connect_real_chrome` 需要 Chrome 运行前为空；如果用户手动打开了 Chrome，工具会按设计拒绝并提示先关闭当前 Chrome。
- `browser_snapshot` 会读取当前公开页面文本；本轮 URL 是 `https://example.com`，后续如果 URL 换成登录站点或私人页面，必须重新评估隐私边界。

## 2026-05-28 Real Chrome Chongqing Weather Travel 风险与处理

已处理风险：
- 旧风险：真实 Chrome connect 只在 `example.com` 公开页 smoke 级别跑通，还不能证明目标 agent 能在真实 Chrome 中完成有实际信息查询价值的任务。
- 已处理：新增 `real_chrome_chongqing_weather_travel.json`，在真实桌面 Chrome 中连接 profile 后打开公开 Open-Meteo URL，读取重庆 2026-05-31 天气 JSON 并生成旅游攻略。
- 已处理：场景继续使用 `permission_policy default_response=deny`，只对白名单工具自动输入 `y`，拒绝 `browser_evaluate`、tabs、console、network、downloads。
- 已处理：真实可见终端验收确认本轮只调用了 `browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`，没有读取 cookies、localStorage、sessionStorage、token、Authorization header、密码、已有标签页内容或插件内容。
- 已处理：验收前 `mcp-doctor` 确认 Chrome 未运行，验收后清理本轮测试启动的 Chrome 进程，并再次确认 Chrome 正在运行为 `false`。

剩余风险：
- Open-Meteo 预报会随时间刷新，本轮 2026-05-28 06:10 左右读到的重庆 2026-05-31 数值以后可能变化。
- 当前场景访问的是公开天气 API，不是用户登录网站；它证明真实 Chrome 可以执行受控公开查询任务，但仍不等于已经安全操作用户已有登录态页面、已有标签页或插件。
- 权限策略仍基于 action 文本包含匹配；对当前白名单场景足够可审计，但后续更复杂登录态任务仍建议升级为结构化 tool-call ledger 匹配工具名和参数。

## 2026-05-28 Structured Permission Ledger 风险与处理

已处理风险：
- 旧风险：`permission_policy` 主要基于 action 文本包含匹配，`browser_open` 一旦被 contains 放行，就难以精确限制 URL 参数。
- 已处理：`permission_required` / `permission_answered` 事件现在带结构化 `tool_name`、`arguments`、`risk_level`、`risk_summary`，controller 可以按工具名和参数做决策。
- 已处理：`real_chrome_chongqing_weather_travel.json` 已改为结构化工具白名单，`browser_open` 必须同时命中工具名白名单和 Open-Meteo URL 前缀。
- 已处理：真实可见终端验收确认 `browser_open` 决策原因为 `allow_tool_name_and_url_prefix`，不是旧的 `allow_contains`。
- 已处理：`permission_policy_decisions` 已记录结构化参数和风险摘要，后续可复盘每个 `y/n` 为什么发生。

剩余风险：
- 当前结构化 payload 是从人类可读权限文本解析出来的，而不是从 `_execute_mcp_tool()` 直接传对象到权限函数；它已经满足当前控制器精确匹配，但未来最好把权限回调升级为对象接口，避免依赖提示文本格式。
- `allow_url_prefixes` 目前只对 `mcp__browser_automation__browser_open` 做前缀校验；以后若其它工具也带 URL 或路径参数，需要扩展通用参数规则。
- 结构化策略已经适合公开网站查询验收，但进入真实登录网站、已有标签页或插件控制前，仍需要新增人工选择目标页和更严格的字段级白名单。

## 2026-05-27 重庆天气浏览器自动化测试风险记录

已确认的健康状态：
- 目标 agent 在 CLI 真实大模型路径中成功读取 `tool_list.md` 和 `browser_automation/SKILL.md`。
- 目标 agent 成功调用 `mcp__browser_automation__browser_open` 和 `mcp__browser_automation__browser_snapshot`。
- `mcp-doctor` 显示 `browser_automation` MCP server 启动成功，模型可见 MCP 工具 30 个。

剩余风险：
- 本轮通过 CLI `run --prompt --json` 驱动目标 agent，并通过日志确认浏览器 MCP 工具调用；这不能替代用户本地可见终端窗口中的 `start_oauth_agent.bat` 人工交互验收。
- CLI 输出文件 `learning_agent/test/chongqing_weather_browser_20260527/cli_run_output.txt` 可能因为 Windows 管道编码显示中文乱码；可信中文证据以 `learning_agent/debug_logs/latest_run_readable.md` 为准。
- Open-Meteo 预报会随时间刷新，2026-05-30 重庆天气数值代表本轮查询时返回结果，后续复测可能有小幅变化。

## 2026-05-27 learning_agent 当前剩余风险评估

已确认的健康状态：
- 当前完整单元测试通过：`Ran 332 tests in 28.030s OK (skipped=1)`。
- 当前 MCP doctor 通过：`browser_search`、`workspace_tools`、`browser_automation` 均可启动，真实 Chrome profile 诊断为 `available`。

剩余风险：
- 本轮是分析评估，不是新增功能开发；没有启动用户本地可见的 `start_oauth_agent.bat` 交互窗口做真实人工 prompt 验收，因此不能把本轮称为“开发完成验收”。
- `last_unittest_output.txt` 当前保存的是旧失败输出，和当前重新运行的测试结果不一致；后续若引用测试状态，应优先看新运行命令输出或重新生成该日志，不能把旧文件当当前事实。
- `learning_agent.py` 已超过 1MB，虽然有大量中文教学注释和测试保护，但长期维护成本较高；后续继续扩展时应优先拆模块或沉淀 skill/hook，不宜继续把新能力堆进主文件。
- `mcp-doctor` 证明真实 Chrome profile 环境可用，但不等于已在本轮实际连接用户真实 Chrome 登录态；涉及登录态时仍要走 profile status、明确授权和真实交互验收。

## 2026-05-26 Prompt Files v3 风险与处理

已处理风险：
- 旧风险：静态系统提示词仍散落在 `learning_agent.py` helper 中，用户后续编辑和审计都不方便。
- 已处理：静态系统提示词已迁移到 `learning_agent/staticprompt/staticprompt.md`，源码只负责读取和兜底。
- 旧风险：动态运行规则文件名仍叫 `runtime_instructions.md`，容易被误解为每轮 runtime 常驻提示词。
- 已处理：旧文件已迁移为 `learning_agent/dynamicprompt/dynamicprompt.md`，并通过测试锁定旧路径不再存在。
- 已处理：`dynamicprompt.md` 不进入首轮 system prompt，但可通过 `skill_load name=dynamicprompt` 按需加载，避免“动态规则不可见”的新风险。

剩余风险：
- 如果用户把 `staticprompt/staticprompt.md` 改得过长，仍可能重新增加每轮上下文；当前代码有 12000 字符兜底截断，但更好的做法是继续把流程规则下沉到 skill。
- 如果未来继续扩写 `dynamicprompt/dynamicprompt.md`，它虽然不常驻，但按需加载时仍可能过长；应优先拆分成更小的 skill 或 capability pack 说明。

## 2026-05-26 Lean System Prompt v2 风险与处理

已处理风险：
- 旧系统提示词过大，且 `Tool Boundary / 工具边界`、`Response Policy / 输出策略` 这类细节每轮固定加载，和用户希望精简 prompt surface 的方向冲突。
- 已处理：默认系统提示词只保留短核心身份、行为原则、上下文策略和 Prompt Surface Policy；细节规则迁移到 `dynamicprompt/dynamicprompt.md` 和 skill/capability pack。
- 已处理：旧测试依赖 `prompt.policy.response` 默认加载；当前已改为断言核心身份 block 加载，避免测试把旧大 prompt 形态固化。
- 已处理：完整回归发现 `知识与实时信息策略` 锚点丢失；当前把该锚点作为 runtime 小标题保留，不把实时信息细则重新塞回核心系统身份。
- 已处理：`agent_memory` 三件套过长；当前已复制旧全文到 `agent_memory/archive/2026-05-26-lean-system-prompt/`，活跃文件改为短摘要。

剩余风险：
- `prompt.policy.tool_boundary` 和 `prompt.policy.response` 的 helper 仍在源码中保留；这不影响默认每轮加载，但后续若注册表或测试误把它们重新加入 `block_contents`，提示词可能再次变大。
- `dynamicprompt/dynamicprompt.md` 仍承担很多工具关键词索引职责；如果继续往里堆长流程，应优先拆成独立 skill。
- `token_budget_report` 使用粗略 token 估算；最终预算判断仍应以真实模型 tokenizer 或运行时报告为准。
- 活跃 `agent_memory` 只保留摘要；需要旧细节时必须读取 `agent_memory/archive/2026-05-26-lean-system-prompt/` 下的归档文件。

## 2026-05-26 Dynamic Runtime Rules 风险与处理

已处理风险：
- 旧风险：`runtime_instructions.md` 虽然已缩短，但仍作为每轮 system prompt 正文加载，和用户希望“静态系统提示词 + 动态运行规则提示词”的结构不一致。
- 已处理：`_build_initial_messages()` 不再传入 `context.runtime_instructions`，运行时规则正文不再常驻。
- 已处理：必要底线已合并到静态系统提示词，避免 runtime 未加载时模型第一步走偏。
- 已处理：包内能力包 skills 以前不能被空工作区的 `skill_list` / `skill_load` 发现；当前已增加包内默认 skills fallback。

剩余风险：
- `dynamicprompt/dynamicprompt.md` 仍是单个动态索引文件；如果未来规则继续变长，应进一步把关键词索引拆到更小的 rule pack 或 skill metadata。
- 静态系统提示词仍需保留少量动态加载路由关键词；如果删得过狠，模型可能不知道何时调用 `skill_load` 或 `tool_search`。

## 2026-05-26 Prompt Files v3 最新风险

- 最新剩余风险：`staticprompt/staticprompt.md` 现在是每轮常驻入口，后续扩写它会直接增加每轮上下文。
- 最新剩余风险：`dynamicprompt/dynamicprompt.md` 虽然不常驻，但按需加载时仍可能过长，后续应优先拆成独立 skill。
- 最新已处理：旧 `runtime_instructions.md` 路径已删除，避免用户面对两个动态规则入口。

## 2026-05-26 Agent Memory Boundary 风险与处理

已处理风险：
- 旧风险：目标 `learning_agent` 会自动读取 Codex 开发用 `agent_memory/context.md`、`progress.md`、`bugs.md`，导致用户 agent 每轮 prompt 被开发会话记忆污染。
- 已处理：目标 agent 的 `_build_initial_messages()` 现在只默认加载 `staticprompt/staticprompt.md` 和 `memory.md` 索引，不再查找工作区或父目录的 `agent_memory`。
- 已处理：静态提示词已删除三件套路径说明，避免模型误以为这些文件属于目标 agent 的运行时上下文。

剩余风险：
- Codex 开发本项目仍会维护 `agent_memory` 三件套，但这只是开发协作记忆；后续不能再把它接回目标 agent 的默认 prompt surface。

## 2026-05-26 Four Atom Tool Surface 风险与处理

已处理风险：
- 旧风险：首轮仍暴露 `tool_search`、`skill_load` 等 kernel 工具，会让用户希望的极简 Tool Pool 继续膨胀。
- 已处理：`KERNEL_TOOL_NAMES` 已收敛为 `read`、`write`、`edit`、`bash`，完整测试锁定首轮 Tool Pool 只含四原子工具。
- 旧风险：`staticprompt.md`、`dynamicprompt.md`、README 和 fallback static prompt 仍可能把模型引回 `tool_search` / `select_pack` 旧路由。
- 已处理：静态提示词、动态提示词、README 和 fallback static prompt 都已改为通过 `learning_agent/skills/tool_list.md` 做 read-based skill discovery。
- 旧风险：README 与真实代码不一致，学习者会以为旧 select 流程仍是默认主路径。
- 已处理：README 已同步说明四原子首轮工具面，旧 skill/tool 入口只作为内部兼容能力保留。

剩余风险：
- `TOOL_SCHEMAS` 仍保存所有历史工具 schema，虽然默认不进首轮 Tool Pool，但后续维护者若误改 `KERNEL_TOOL_NAMES` 或 `build_builtin_tool_catalog()`，可能再次扩大模型首轮工具面。
- `dynamicprompt/dynamicprompt.md` 仍保留大量内部能力关键词索引；它不常驻，但按需读取时仍可能比较长，后续应继续拆成更小的 skill 文件。
- 四原子 `bash` 直接执行 shell 命令，虽然有权限确认、cwd 边界和超时限制，后续仍应持续强化命令风险提示和 Windows/类 Unix 兼容验证。

## 2026-05-26 CLI / HTTP Command Bridge 风险与处理

已处理风险：
- 旧风险：目标 agent 只有人工交互入口，Codex 难以稳定启动、下发任务和接收结果，真实调试场景无法闭环。
- 已处理：新增 CLI `run --prompt ... --json`，stdout 可返回结构化 JSON，方便 Codex 或脚本直接接收。
- 已处理：新增本机 HTTP command bridge，支持探活和运行命令，能复用同一个 agent 进程做连续调试。
- 已处理：bridge 默认建议绑定 `127.0.0.1`，并支持可选 token，避免一开始就把控制接口暴露成无保护远程入口。
- 已处理：HTTP `POST /run` 通过锁串行化 `agent.run()`，降低并发请求同时修改同一个 agent 状态的风险。

剩余风险：
- HTTP bridge 当前是标准库最小实现，不是生产级认证、TLS 或多用户权限系统；真实远程使用前必须加外层安全边界。
- bridge 使用同一个进程内 agent 状态，适合调试和连续控制，但不适合无隔离的多租户并发任务。
- CLI `--json` 运行仍会真实构造模型和 MCP registry；如果真实模型或 MCP 配置有问题，JSON 结果可能返回错误或启动阶段失败，后续可继续强化错误 JSON 包装。

## 2026-05-26 Dynamic Prompt Tree 风险与处理

已处理风险：
- 旧风险：动态提示词虽然不常驻，但所有细节都堆到 `SKILL.md` 后，按需读取某个 skill 时仍可能把大量无关流程塞进上下文。
- 已处理：每个顶层 `SKILL.md` 已改成轻入口，细节下沉到 `rules/*.md`，只在具体场景需要时继续读取第三层。
- 旧风险：包内 skills 仍包含 `tool_search` / `select_pack` 旧路由，会和四原子首轮工具面冲突。
- 已处理：包内 skills 已清理旧路由文案，并用测试锁定顶层 `SKILL.md` 不再出现这两个关键词。
- 旧风险：模型知道路径时可以直接 `read learning_agent/skills/<skill>/rules/*.md`，绕过父索引，导致分层只停留在提示词约定。
- 已处理：`read` 原子工具已新增层级门控，未先读 `tool_list.md` 和父 `SKILL.md` 时会返回可恢复提示。

剩余风险：
- `dynamicprompt/dynamicprompt.md` 仍保留内部能力关键词索引，虽然不常驻，但用户若主动读取它仍会看到较多关键词；后续可以继续拆成更小的规则索引。
- `skill_load` 作为内部兼容工具仍可直接加载 `SKILL.md`，但它不在首轮模型可见工具池中；后续若完全移除旧兼容入口，需要同步清理相关历史测试。
- 当前 read 层级门控只覆盖 workspace 内 `learning_agent/skills` 或 `skills` 路径；MCP prompt 或外部资源的层级加载仍依赖各自工具规则。

## 2026-05-26 Current Date Prompt 风险与处理

已处理风险：
- 旧风险：`learning_agent/staticprompt/staticprompt.md` 只能写稳定文本，无法让 agent 每天自动知道真实日期。
- 已处理：静态提示词新增 `{{CURRENT_DATE}}` 占位符，运行时每轮由 `get_local_iso_date()` 替换成本机当天日期。
- 旧风险：如果只在静态提示词里写死某一天日期，第二天以后 agent 会拿到过期日期。
- 已处理：具体日期不写进静态文件，单测和 CLI 验证都确认 system prompt 中出现运行时日期 `2026-05-26`。
- 旧风险：静态提示词文件缺失或损坏时 fallback prompt 可能没有日期上下文。
- 已处理：fallback static prompt 同步写入当前日期。

剩余风险：
- 当前实现满足“每轮看到今天日期”，但没有实现 ClaudeCode 的 `date_change` attachment；如果未来要在超长会话里专门通知跨午夜变化，可以再增加 last emitted date 状态和日期变化附件。
- 日期使用本机本地时区的 `date.today()`；如果未来需要固定用户时区或 UTC，需要增加显式时区配置。

## 2026-05-26 Browser Automation 风险与处理

已处理风险：
- 旧风险：四原子工具面移除 `tool_search` 后，browser MCP 工具虽然在 catalog 中，但模型读取 browser skill 后没有办法把 `browser_open` 等工具加入 Tool Pool。
- 已处理：新增 read-based dynamic skill unlock，读取 `browser_automation/SKILL.md` 后加载 `browser_automation` 能力包，且单测覆盖实际 MCP 调用。
- 旧风险：真实 Chrome connect 如果只靠读取 skill 直接暴露，会跳过 profile status 安全检查。
- 已处理：读取 `real_chrome/SKILL.md` 只准备工具并满足 skill gate，connect 仍要等 `browser_profile_status` 完成后才可见。
- 旧风险：真实 Chrome 路线如果未设置 `real_chrome_requested`，可能在连接前误把普通 browser_open 当成替代路径。
- 已处理：读取 `real_chrome/SKILL.md` 会设置 `real_chrome_requested=True`，普通浏览器动作在 `real_chrome_connected` 前继续被 workflow gate 拦住。
- 旧风险：CLI 默认 workspace 是 `learning_agent` 目录，而静态提示词推荐 `learning_agent/skills/tool_list.md`，模型按提示读取会形成 `learning_agent/learning_agent/skills` 错路。
- 已处理：`_resolve_workspace_path()` 已兼容包目录工作区下的项目根风格 `learning_agent/...` 路径，并新增回归测试。
- 旧风险：用户或测试说 `real browser automation` 时，`_detect_real_chrome_intent()` 会把普通真实浏览器自动化误判成真实 Chrome/profile 请求，导致 `browser_open` 被 workflow gate 隐藏。
- 已处理：真实 Chrome 触发词已收窄为真实 Chrome、桌面/可见/当前浏览器或登录态；普通 `real browser automation` 保持走独立 Playwright browser 工具。
- 旧风险：`run()` 调用了不存在的 `_final_answer_retry_message()`，HTTP command bridge 在模型给出最终回答时会返回 500。
- 已处理：已补齐 `_final_answer_retry_message()`，仅在用户明确列出 Markdown 标题且最终回答漏标题时自动重写一次，避免影响普通任务。
- 旧风险：之前只用脚本化假模型验证浏览器工具链，不能证明真实大模型能按 read-based skill 路由完成天气查询和攻略生成。
- 已处理：HTTP bridge 和 CLI run 都已使用真实 `CodexCliChatModel` 完成 Open-Meteo 北京 2026-05-29 查询，日志确认真实调用 `browser_open` 和 `browser_snapshot`。

剩余风险：
- `real_chrome` 路线已通过策略和 doctor 验证 profile status/connect 门控，但本轮没有实际连接用户真实 Chrome profile，避免触碰登录态风险。
- 读取 browser skill 后 Tool Pool 会从四原子扩展到浏览器工具组；这是按需扩展，不影响首轮极简工具面，但浏览器任务期间 schema 会明显增大。
- CLI `--json` 路径在自动喂权限输入并重定向到文件时，Windows 管道输出里的中文权限提示可能出现乱码；真实调试日志 `latest_run_readable.md` 仍是 UTF-8 可读证据，后续可改进 CLI 权限提示和 JSON 输出分流。

## 2026-05-28 Real Chrome Google Human Visible 风险与处理

已处理风险：
- 旧风险：用户希望肉眼看到真实 Chrome 打开 Google、点击输入和回车搜索；之前的真实 Chrome 天气场景直接打开 Open-Meteo URL，不会展示 Google 搜索框里的拟人输入过程。
- 已处理：新增 `real_chrome_google_human_search.json` 场景，强制打开 `https://www.google.com/`，再调用 `browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_snapshot`。
- 旧风险：controller 成功后立即关闭终端，用户可能错过桌面可见 Chrome 演示画面。
- 已处理：controller 新增 `post_success_wait_seconds`，Google 场景成功后停留 20 秒。
- 旧风险：第一次 Google 真实验收中 agent 实际完成了截图和最终回答，但 `final_answer_printed.answer_preview` 只有 500 字，截断在 `- br`，导致 `event_answer_checks.browser_screenshot=false` 并误判失败。
- 已处理：`final_answer_printed` 事件新增完整 `answer_text`；controller 的回答断言改为优先检查完整 `answer_text`，并保留 `answer_preview` 作为摘要。
- 已处理：新增回归测试锁定 `answer_text` 字段和 controller 完整回答断言，避免后续再退回截断预览。

剩余风险：
- Google 页面可能因地区、同意弹窗、异常流量或 CAPTCHA 改变 DOM；场景 prompt 已允许点击同意按钮，但不允许绕过 CAPTCHA，遇到 CAPTCHA 时必须截图并如实失败。
- 本场景只证明公开 Google 页面中的可见点击输入链路，不代表已经安全支持任意登录网站或读取用户私人标签页。
- 真实 Chrome 连接使用日常 profile，必须继续通过默认拒绝权限策略、URL 前缀白名单和禁止 cookies/storage/network/console/evaluate 的边界控制风险。

## 2026-05-28 Real Browser Task Harness 风险与处理

已处理风险：
- 旧风险：用户自然说“请使用真实浏览器，帮我查询3天后重庆的天气，并帮我做一下旅游攻略”时，旧 `_detect_real_chrome_intent()` 不包含“真实浏览器”短语，会漏判真实 Chrome/profile workflow。
- 已处理：新增 `真实浏览器`、`真实的浏览器`、`真实可见浏览器` 触发词，并用单测锁定自然短 prompt 会进入真实 Chrome 路线。
- 旧风险：只有长 prompt 明确写 `browser_click`、`browser_type`、`browser_press_key` 时，agent 才稳定执行可见 Google 搜索；这不能复用到会议、酒店、航班、资料等普通用户场景。
- 已处理：新增 `Real Browser Task Harness`，在真实浏览器信息查询任务里自动注入通用 Google 首页搜索流程，覆盖会议、酒店、航班、资料、天气、旅游攻略等任务。
- 旧风险：真实 Chrome skill 只有 profile 安全规则，没有把公开信息查询的可见搜索流程沉淀成子规则。
- 已处理：新增 `learning_agent/skills/real_chrome/rules/search_task_workflow.md`，并在 `real_chrome/SKILL.md` 中索引。
- 旧风险：自然短 prompt 验收如果仍把工具步骤写进 prompt，就不能证明 harness 本身能发挥作用。
- 已处理：新增 `real_chrome_natural_weather_travel.json`，第一行保留自然短 prompt，场景测试断言 prompt 不包含“必须使用 browser_click / browser_type”。
- 旧风险：第一次自然短 prompt 真实终端验收中，真实 Chrome 操作已经成功，但最终回答只写中文摘要，没写 `real_chrome_connected=true` 和工具名，导致机器验收误判失败。
- 已处理：harness 和 `search_task_workflow.md` 都要求最终回答包含 `real_chrome_connected=true` 与 `browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_snapshot`。
- 已处理：失败验收留下的 Chrome 调试进程已通过命令行识别，仅清理带 `--remote-debugging-port=9222` 的测试 Chrome 进程；最终 `mcp-doctor` 确认 Chrome 未运行且端口可用。

剩余风险：
- Google 页面、AI 概览、搜索结果排序和 DOM 会随地区、账号、时间和风控变化；当前场景通过快照、截图和宽松文本断言降低脆弱性，但遇到 CAPTCHA 时仍必须如实失败。
- 目前通用 harness 适合公开网页查询，不等于安全支持操作用户私人标签页、已登录后台、支付、预订或账号设置；这些场景需要更严格的目标页选择、字段级白名单和人工确认。
- 用户真实 Chrome profile 仍是高风险边界，必须继续默认拒绝未知权限，禁止 cookies/storage/token/password/network/console/evaluate，并优先只访问用户明确授权的公开 URL。

## 2026-05-28 Real Browser Customer Mode 风险与处理

已处理风险：
- 旧风险：真实浏览器自然查询任务会在启动 MCP、连接真实 Chrome、打开 Google、快照、点击、输入、回车、等待、截图等每一步都弹 `[y/N]`，真实客户体验很差。
- 已处理：交互式入口使用客户模式权限函数，项目内置 MCP 启动自动允许；真实浏览器公开查询白名单工具在任务级上下文中自动授权，不再调用 `input()`。
- 旧风险：取消所有 y/N 可能误放行 `browser_evaluate`、network、console、tabs、downloads、upload 或任意非授权 URL。
- 已处理：自动授权仅在“真实浏览器 + 公开信息查询”场景启用；只放行公开 Google 查询链路必需工具，敏感工具继续走权限层并可被拒绝。
- 旧风险：无 y 模式可能变成静默执行，用户看不到 agent 下一步在做什么。
- 已处理：自动授权时打印 `Agent > 正在...` 进度行，并记录 `permission_auto_approved` / `mcp_call_progress` 审计事件。

剩余风险：
- 自动授权当前默认允许项目内置 MCP server 启动；如果未来 `mcp_servers.json` 增加新的未知 server，客户模式不会自动允许，需要重新评估白名单。
- 当前 URL 自动授权仅覆盖 Google 公开入口；会议、酒店、航班等任务后续如果需要打开具体结果网站，应新增来源级白名单或短暂人工确认，而不是直接扩大到任意 URL。

## 2026-05-28 YouTube 自然查询仍弹 y/N 风险与处理

已处理风险：
- 旧风险：用户输入“请使用真实浏览器，youtube网站的视频关于ai agent介绍，评论最多的有哪些？”时，真实浏览器动作仍逐步弹 `[y/N]`，说明客户模式没有完全覆盖真实公开查询场景。
- 已确认根因：旧 `_detect_real_browser_information_task()` 未命中该 prompt，因为它没有“查询/搜索/天气/攻略/会议/酒店/航班/资料”等关键词，只包含“youtube网站/视频/评论最多/有哪些”。
- 已处理：将 `网站`、`视频`、`评论`、`最多`、`有哪些`、`哪些`、`哪个`、`排行`、`排名`、`榜单`、`介绍`、`youtube` 加入公开信息查询关键词。
- 已处理：新增 YouTube prompt 红灯测试，先观察到 `_detect_real_browser_information_task()` 返回 `False`，再修复到通过，避免把猜测当结论。
- 已处理：新增 YouTube 自然短 prompt 真实终端场景并完成验收，`permission_sent_count=0`，证明不会再让用户输入多次 `Y`。

剩余风险：
- 已经启动的旧 `start_oauth_agent.bat` 进程不会热加载新代码；用户必须关闭旧终端并重新启动，才能看到 YouTube 场景无 y 的新行为。
- 当前客户模式仍只自动打开 Google 公开入口；如果后续要直接打开 YouTube、酒店官网、航司官网等具体站点，需要按域名单独评估 URL 白名单，不能直接放开任意 URL。
- Google 结果页的评论数摘要可能随地区、账号、时间和搜索排序变化；真实浏览器功能已验收“能查且无 y”，但具体 YouTube 排名结果仍应以当次页面可见内容为准。

## 2026-05-29 模块化阶段 2 验证中发现的稳定性问题

已处理风险：
- 旧风险：`mcp-doctor` 会直接调用真实 Chrome profile 诊断；当 Windows 拒绝访问 `C:\Users\joyzq\AppData\Local\Google\Chrome\User Data` 时，`Path.exists()` 抛出 `PermissionError`，导致 doctor 退出码为 1。
- 已确认根因：`browser_real_chrome._existing_path()` 没有捕获路径候选检查期间的 `OSError/PermissionError`，一个不可访问候选会中断整个诊断。
- 已处理：`_existing_path()` 现在把不可访问候选视为不可用候选并继续检查，doctor 会返回结构化诊断而不是崩溃。
- 已新增回归测试：`test_real_chrome_profile_manager_skips_inaccessible_candidates`。
- 旧风险：后台命令测试停止长命令后，Windows 仍报告临时目录“另一个程序正在使用此文件”，导致 `TemporaryDirectory` 清理失败。
- 已确认根因：sandbox 环境下 `taskkill /F /T /PID` 对测试进程返回 `Access denied`；后备 `process.kill()` 只能杀外层 shell，Python 子进程继续持有工作目录和输出管道直到自然 sleep 结束。
- 已处理：后台命令在 Windows 下用 `CREATE_NEW_PROCESS_GROUP` 启动，并优先发送 `CTRL_BREAK_EVENT` 终止进程组；停止后主动关闭 stdio 管道并等待 reader 线程退出。
- 已验证：`test_agent_starts_reads_and_stops_background_command` 从约 30 秒自然结束降到 `Ran 1 test in 0.136s OK`。

剩余风险：
- Windows 受限环境下仍可能拒绝 `taskkill`、CIM 和其它进程枚举接口；后台命令停止逻辑应继续优先使用自身创建的进程组，不依赖全局进程枚举。
- Chrome profile 目录不可访问时，当前诊断会把该候选视为未找到；后续如需更精细用户提示，可以扩展诊断对象记录“存在但不可访问”的候选原因。

## 2026-05-29 模块化阶段 3 验证中观察到的浏览器下载时序风险

已观察风险：
- 完整单元测试第一次运行时，`test_browser_automation_mcp_server_uploads_and_downloads` 失败一次：`downloaded_files[0]` 已出现但文件内容暂时为空，断言未读到 `hello-download`。
- 该测试单独复现立即通过，随后完整 `python -m unittest learning_agent.test_learning_agent` 重跑也通过，说明当前不是阶段 3 模型拆分导致的稳定回归。

当前结论：
- 现有证据更符合 Playwright/Chromium 下载事件和 Windows 文件落盘之间的偶发时序差异：测试轮询条件只要求文件存在和下载记录出现，没有额外确认文件内容非空。
- 因阶段 3 的修改范围是模型代码迁移，且重跑完整测试已通过，本阶段未修改浏览器下载模块，避免把无关修复混入模型拆分。

剩余风险：
- 如果后续完整测试再次出现同类空文件失败，应在浏览器下载测试或 server 下载保存处增加“文件内容/大小稳定后再判定完成”的条件式等待，而不是固定 sleep。
- 该风险属于浏览器自动化层，后续阶段 7 拆 `browser/` 时更适合纳入专项处理和回归测试。

## 2026-05-29 模块化阶段 4 验证中发现并处理的问题

已处理风险：
- 旧风险：`run_mcp_doctor()` 拆到 `learning_agent/mcp/runtime.py` 后，测试仍 patch `learning_agent.learning_agent.diagnose_real_chrome_environment`，导致 doctor 读取真实本机 Chrome 状态并让测试不稳定。
- 已确认根因：阶段 4 迁移改变了诊断函数的读取位置，旧入口兼容导入存在，但 doctor 内部没有经过旧入口兼容层读取可替换诊断函数。
- 已处理：新增 `_diagnose_real_chrome_environment()` 兼容层，优先使用旧主入口上的诊断替身，再回退到真实 `browser_real_chrome` 诊断。
- 已验证：`test_mcp_doctor_reports_real_chrome_profile_diagnostic` 通过，`-k mcp` 通过，`mcp-doctor` 脚本入口通过。
- 旧风险：阶段 3 记录的浏览器下载空文件时序问题在阶段 4 `-k mcp` 中再次出现，说明它不是一次性偶发观察。
- 已确认根因：上传下载测试的轮询条件只要求下载记录出现且文件数量达到 2，没有确认文件内容已经写完整。
- 已处理：测试轮询现在每轮读取下载文本，只在两个文件都包含 `hello-download` 后停止等待。
- 已验证：上传下载聚焦测试通过，`-k mcp` 通过，完整单元测试通过。

剩余风险：
- `run_mcp_doctor()` 仍在阶段 4 临时依赖旧主入口的 `TOOL_SCHEMAS` 和工具包装 helper；阶段 5 拆 `tools/` 后应移除这类临时回连。
- 浏览器下载模块本身仍可能在真实机器上受浏览器、杀毒软件或文件锁影响；当前修复是让测试等待真实内容完整，而不是改变用户下载行为。

## 2026-05-29 模块化阶段 5 tools 拆分风险记录

已处理风险：
- 旧风险：阶段 4 的 MCP runtime 仍通过旧主入口读取 `agent_tool_from_schema`、`builtin_tool_capability_pack` 和 `TOOL_SCHEMAS`，阶段 5 如果只移动类型不保留旧入口兼容，会导致 MCP 工具包装断开。
- 已处理：`learning_agent.py` 从 `learning_agent/tools/catalog.py` 重导入 `agent_tool_from_schema`、`builtin_tool_capability_pack`、`build_builtin_tool_catalog`，旧入口名称继续存在；MCP runtime 的临时读取仍能工作。
- 旧风险：把 `_execute_tool` 长 if 链移出后，allowed_tools、ToolPolicy、plan mode、deferred MCP 的执行期守卫可能漏掉。
- 已处理：`learning_agent/tools/executor.py` 先执行统一守卫，再走内置分发表和 MCP 分发；`-k tool`、`-k permission`、`-k plan_mode` 均通过。
- 旧风险：长工具结果落盘摘要如果拆错，会导致模型下一轮拿不到 `Full output saved to` 或 artifact 观察事件。
- 已处理：只迁移文件名、inline limit 和摘要格式 helper，落盘写文件与 observation 仍由主 agent 保持原行为；`-k offload` 通过。

剩余风险：
- `TOOL_SCHEMAS` 和具体工具实现方法仍在 `learning_agent.py`，阶段 5 只是先拆出工具层边界、catalog、pool、executor 和 helper；后续如果继续细拆具体工具实现，应按能力域逐步迁移，避免一次性移动所有副作用工具。
- MCP runtime 仍通过旧主入口临时读取 `TOOL_SCHEMAS`；等内置 schema 常量完全迁入 `tools/catalog.py` 后，应移除这条临时回连。

## 2026-05-29 模块化阶段 6 prompts 拆分风险记录

已处理风险：
- 旧风险：`learning_agent.py` 同时承载 staticprompt 路径解析、读取、兜底、日期渲染和 dynamicprompt 伪 skill 元信息，导致 prompt 行为排查仍要翻主文件。
- 已处理：`static_prompt.py` 和 `dynamic_prompt.py` 已接管这些职责，主文件只保留委托调用。
- 旧风险：新目录 `learning_agent/prompts/` 在阶段 1 只有空骨架，无法作为真实 prompt 层入口使用。
- 已处理：阶段 6 新增 `registry.py`、`context_assembler.py`、`token_budget.py`、`surface_report.py` 和包入口 re-export，并用导入测试锁定。
- 旧风险：迁移 staticprompt 读取时可能丢失 `{{CURRENT_DATE}}` 或 `{{CURRENT_WORKSPACE}}` 渲染。
- 已处理：`read_static_prompt()` 显式接收 `workspace` 与 `current_date`，专项 prompt 测试和完整单测已通过。
- 旧风险：dynamicprompt 可能被误放进常驻 system prompt，重新撑大每轮上下文。
- 已处理：阶段 6 只迁移路径和伪 skill 元信息，`_build_initial_messages()` 仍只装配 staticprompt 与 memory index。

剩余风险：
- `prompt_registry.py` 和 `context_assembler.py` 的真实实现目前仍在根目录旧模块，新 `prompts/registry.py` 与 `prompts/context_assembler.py` 是兼容重导出；后续如果要完全移动实现，需要再做一轮更细的红绿测试，避免破坏旧 import。
- `token_budget.py` 目前只是预算入口和下限 helper，真实 token 估算仍复用 `ContextAssembler` 的粗略字符估算；如果后续接入真实 tokenizer，需要单独设计模型相关预算边界。
- `static_prompt.py`、`dynamic_prompt.py` 保留了大量逐行中文教学注释，适合用户学习，但文件本身偏长；后续稳定后可以把解释性材料同步到架构索引文档，代码注释保持必要密度。
- 本阶段额外运行 `mcp-doctor` 时，MCP server 均启动成功但真实 Chrome 诊断显示 `blocked`，原因是检测到 Chrome 正在运行且 User Data 路径未可用；这属于本机真实 Chrome 当前状态，不是阶段 6 prompts 拆分导致的回归。

## 2026-05-29 模块化阶段 7 browser 拆分风险记录

已处理风险：
- 旧风险：真实浏览器意图、公开查询识别、客户模式授权白名单和 Google URL 限制都堆在 `learning_agent.py`，排查“为什么还弹 y/N”或“为什么误用独立浏览器”时需要翻主文件大段逻辑。
- 已处理：阶段 7 新增 `browser/intent.py`、`browser/harness.py`、`browser/permissions.py`、`browser/search_workflow.py`，并让旧主入口优先委托这些模块。
- 旧风险：取消连续 `y/N` 的客户模式如果拆错，可能误放行非 Google URL 或敏感工具。
- 已处理：`browser.permissions` 保持原边界，只自动允许公开 Google 查询链路所需工具；`browser_evaluate`、network、console、tabs、downloads、upload 和非 Google URL 仍不自动放行。
- 旧风险：浏览器截图/下载产物路径清洗只存在于 MCP server 类内部，后续难以单独测试路径越界防护。
- 已处理：新增 `browser/artifacts.py` 并加模块测试，`browser_automation_mcp_server.safe_artifact_path()` 先委托新 helper。
- 旧风险：真实浏览器自然短 prompt 的无 y 客户模式可能在重构后退化。
- 已处理：真实可见终端验收 `real_chrome_natural_weather_travel-20260529_105333` 通过，`permission_sent_count=0`，动作链包含 `browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_snapshot`。

剩余风险：
- `learning_agent.py` 目前仍保留旧浏览器方法体作为过渡死代码，执行路径已经委托新模块，但文件体积和阅读噪音尚未完全下降；阶段 12 瘦身时应删除重复实现。
- `mcp-doctor` 仍可能显示真实 Chrome 诊断 `blocked`，如果本机 Chrome 正在运行或 User Data 路径不可用；这不阻断本阶段测试，但真实客户验收依赖 controller 能启动/连接本机可见 Chrome。
- 当前客户模式仍只自动打开 Google 公开入口；后续如果要直接打开会议官网、酒店官网、航司官网、YouTube 等站点，需要按域名和风险重新设计白名单，而不是扩大为任意 URL。

## 2026-05-29 模块化阶段 8 tasks 拆分风险记录

已处理风险：
- 旧风险：后台命令、task 子 agent、team、cron 和 monitor 的记录类全部堆在 `learning_agent.py` 顶部，长期任务排查时需要先穿过大量无关定义。
- 已处理：阶段 8 新增 `tasks/background.py`、`tasks/task_runs.py`、`tasks/team.py`、`tasks/cron_monitor.py`，并把记录类迁入这些模块。
- 旧风险：后台输出队列读取、后台命令状态、task background 解析、子 agent prompt、cron/monitor 状态和格式化规则都只能从主文件间接复用。
- 已处理：上述纯 helper 已迁移到 tasks 层，主文件旧方法优先委托新 helper。
- 旧风险：迁移 task 记录类时可能破坏后台 task、team_start_task、cron/monitor 的旧文本输出或生命周期状态。
- 已处理：`-k task`、`-k background`、`-k cron` 和完整单元测试均通过，说明旧工具输出与生命周期行为保持兼容。

剩余风险：
- `learning_agent.py` 仍保留 task/team/cron/monitor 的副作用编排方法，例如真正创建子 agent、启动后台进程、权限确认和 team 绑定 task；阶段 8 只迁移低风险记录类和纯 helper。
- `_task_background_enabled`、`_task_child_prompt`、`_cron_monitor_state` 等旧方法体中还存在委托后的不可达旧代码；阶段 12 瘦身时应删除这些重复实现。
- `mcp-doctor` 运行时观察到真实 Chrome 默认端口 9222 被占用，这是刚完成真实 Chrome 验收后的本机环境状态提示，不是 tasks 拆分导致的 MCP 启动失败。
## 2026-05-30 Stage 13C bug record: running Chrome was blocked even when CDP was available

Status: resolved in Stage 13C; automated tests and real visible terminal acceptance passed.

Symptom:
- Visible terminal acceptance run `real_chrome_natural_weather_travel-20260530_142210` stopped with a final answer telling the user to close Chrome.
- The run had `permission_sent_count=0`, so the old repeated `Y` issue was not the blocker.
- Required browser actions did not happen because `browser_connect_real_chrome` refused the already-running Chrome state.

Confirmed evidence:
- `Invoke-WebRequest http://127.0.0.1:9222/json/version` returned Chrome CDP metadata and a `webSocketDebuggerUrl`.
- Therefore the local visible Chrome was not merely “running”; it was already exposing a trusted local CDP endpoint that Playwright can attach to.
- Existing code in `browser_connect_real_chrome()` raised immediately on `manager.chrome_is_running()` and never checked the live CDP endpoint.

Root cause:
- The running-Chrome guard was too broad.
- It correctly protected profile locks when no CDP endpoint exists, but incorrectly blocked the valid case where the user has already launched Chrome with local remote debugging enabled.

Fix:
- When Chrome is running, check `wait_for_cdp_endpoint(preferred_port, timeout_seconds=1.0)`.
- If true, call `_connect_real_chrome_after_checks(..., attach_existing_cdp=True, existing_debug_port=preferred_port)`.
- If false, keep the old refusal path to protect the user’s daily profile.
- Attach mode never starts or owns a Chrome process, so cleanup must only disconnect CDP and must not terminate Chrome.
- Update `diagnose_real_chrome_environment()` with the same distinction, so “9222 is occupied by trusted Chrome CDP” is reported as `available` rather than `needs_user_action`.

Regression protection:
- `test_browser_connect_real_chrome_attaches_when_running_chrome_has_cdp`.
- `test_browser_connect_real_chrome_blocks_when_chrome_is_running_without_cdp`.
- `test_real_chrome_diagnostic_reports_available_when_running_chrome_has_cdp`.
- RealChrome focused suite: 40 tests OK, skipped=1.
- Full unittest discovery: 367 tests OK, skipped=1.

Acceptance closure:
- Visible terminal run: `learning_agent\acceptance_controller\runs\real_chrome_natural_weather_travel-20260530_144214\result.json`.
- Outcome: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Evidence checks passed for `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK`, `real_chrome_connected=true`, `browser_click`, `browser_type`, `browser_press_key`, and `browser_screenshot`.

Residual risk:
- If the endpoint disappears during a future run, the correct behavior is to fail with a clear “已有 Chrome CDP endpoint 未就绪” or fall back to the safe running-Chrome refusal, not to kill Chrome.

## 2026-05-30 Stage 14 cleanup risk record

Status: resolved for this pass.

Risk handled:
- Old user-visible entry points could confuse maintainers after the new layered architecture was built.
- `learning_agent/core/agent.py` still contained same-block unreachable old code after wrapper returns, making future debugging more expensive.
- Old artifact directories in the source tree made it look like historical debug output was still part of the active architecture.

Resolution:
- Removed the old test aggregator files, old acceptance forwarding file, and old `tests_support` directory.
- Replaced startup selftest commands with `python -m unittest discover learning_agent`.
- Rewrote the architecture index around unique new entry points, deleted old entry points, module ownership, and bug-routing guidance.
- Removed historical artifact directories after copying the fresh Stage 14 acceptance evidence into the run directory.

Regression guard:
- `learning_agent/tests/test_compat_cleanup.py` now checks that the deleted old files stay deleted and that active tests do not import the old routing names.

Maintenance caution:
- Avoid line-number bulk deletion in `core/agent.py`; use AST/function-boundary checks and small patches so wrapper cleanup does not damage neighboring method bodies.

## 2026-05-31 Stage 15A baseline test blockers

Status: resolved for this pass in worktree `stage15a-event-runtime`.

Symptoms:
- Initial `python -m unittest discover learning_agent` in the fresh worktree failed with 4 failures and 4 errors.
- Playwright was missing from the default Python 3.13 environment, causing browser automation tests to fail.
- Existing tests expected `.gitignore` to include `learning_agent/browser_profiles.json` and `learning_agent/browser_artifacts/real_chrome_audit.jsonl`, but the new baseline `.gitignore` did not include those exact sensitive local-file paths.
- Existing parity checklist test expected `docs/superpowers/specs/claudecode_parity_checklist.md`, but the file was absent from the first git baseline.

Confirmed evidence:
- `python -m pip show playwright` reported package not found.
- Focused tests reproduced the `.gitignore` and parity checklist failures.
- After installing Playwright/Chromium and restoring the missing fixture/document entries, `python -m unittest discover learning_agent` passed with 368 tests OK, skipped=1.

Resolution:
- Installed Playwright with `python -m pip install playwright`.
- Installed Chromium browser binaries with `python -m playwright install chromium`.
- Added the missing `.gitignore` entries.
- Added the missing parity checklist document.

Residual risk:
- The Playwright installation is an environment dependency, not a repository file. A different machine may still fail browser automation tests until Playwright and browser binaries are installed.
- Future setup docs should eventually explain the exact Python environment and Playwright install command used for local baseline tests.

## 2026-05-31 Stage 15 runtime residual risk record

Status: automated regressions passed through Stage 15G; final visible-terminal gate still required.

Handled risks:
- Unknown tools and side-effect tools remain serial by default because Stage 15F requires both `is_read_only=True` and `is_concurrency_safe=True` before parallel execution.
- Hook exceptions are converted into `tool_error` observation events instead of crashing the agent directly.
- Permission `deny` decisions stop execution before the tool handler runs.
- Session compact creates a summary and recent tail messages without deleting raw `events.jsonl` evidence.

Residual risks:
- `run()` still keeps the old plain-text return path and does not fully consume `run_events()` internally; compatibility is preserved, but there is still some duplicated loop logic.
- Stage 15G session resume is a minimal file-level foundation, not a full product command for “resume session id” in the CLI.
- Safe read parallelism can make observation event ordering less strictly linear for concurrent read-only tools; model message result order is preserved.
- Real visible terminal interaction acceptance must still be completed before claiming the whole Stage 15 agent runtime is fully done.

## 2026-05-31 Acceptance controller foreground focus bug

Status: resolved for smoke acceptance.

Symptom:
- Runs `smoke-20260531_142012` and `smoke-20260531_142703` opened the real terminal and reached `agent_ready_for_user_prompt`, but never produced `user_prompt_received`.
- Their `02_prompt_sent.png` screenshots showed Photoshop or another app in the foreground instead of the terminal.
- This proved the controller believed prompt input was sent, while the actual visible terminal stayed at `你 >`.

Root cause:
- `controller.ps1` trusted `WScript.Shell.AppActivate()` return values without independently verifying the current foreground window.
- On this desktop, Windows Terminal focus could fail or lag while another visible application remained active.

Fix:
- Added Win32 foreground-window checks using `GetForegroundWindow` and `GetWindowThreadProcessId`.
- Added stronger terminal activation through `ShowWindowAsync`, `SetForegroundWindow`, `SwitchToThisWindow`, temporary topmost toggling, and a click inside the terminal.
- `Send-TerminalTextLine` now only pastes after verified terminal focus.
- Increased paste-to-enter wait to 800ms so the input line is filled before Enter is sent.

Regression and acceptance evidence:
- Static guard test now requires the controller to include foreground-window verification.
- Successful visible-terminal run: `learning_agent/acceptance_controller/runs/smoke-20260531_143929/result.json`.
- Result: `completed=true`, `prompt_send_attempts=1`, `final_answer_preview=ACCEPTANCE_HARNESS_OK`.
- Independent verifier replay also passed for that run.

Residual risk:
- Foreground control still depends on Windows desktop focus rules. If the OS blocks all foreground changes, the controller should fail rather than paste into a non-terminal window.

## 2026-05-31 Missing independent durable long-task harness

Status: confirmed design gap, not a code defect introduced by the latest change.

Evidence:
- `learning_agent/core/agent.py` keeps `task_runs`, `cron_records`, `monitor_records`, and `background_commands` in process memory.
- `learning_agent/core/session.py` can save a session summary and minimal compact data, but this is not a durable task queue or checkpoint runner.
- `learning_agent/acceptance_controller` and `learning_agent/acceptance/verifier.py` provide real-terminal acceptance and replay verification, but they validate runs; they do not schedule, resume, or automatically continue long work.

Risk:
- Long tasks can be lost or become hard to resume after process exit, crash, OAuth/API failure, endpoint change, machine sleep, or manual interruption.
- There is no single visible task state source that another agent can inspect to know current stage, last checkpoint, next action, failure reason, and acceptance status.

Recommended fix:
- Add a dedicated `learning_agent/harness/` package with durable task/run/stage state, append-only event logs, queue leasing, checkpoint recovery, stage verifiers, retry/backoff policy, and status endpoints for controller/Codex observation.

## 2026-05-31 Harness session stage pending bug

Status: resolved and regression-tested.

Symptom:
- Real visible terminal acceptance created `learning_agent/memory/harness/runs/runtime_0b61bcfb0c2589c2.json` with top-level `status=completed`, but its `interactive_turn` stage still had `status=pending` and `acceptance.passed=false`.
- This meant the run looked finished while the stage-level audit record still looked unfinished.

Root cause:
- `HarnessRun.create()` deep-copies the input stages.
- `learning_agent/runtime/session_runtime.py` updated the original local `stage` object instead of `run.stages[0]`, so the object saved to disk never received the running/completed/acceptance fields.

Fix:
- Rebound `stage = run.stages[0]` immediately after `HarnessRun.create(...)`.
- Added `started_at` and `completed_at` timestamps to the persisted stage.
- Added regression assertions in `learning_agent/tests/test_harness_runtime_alignment.py` for `stage.status=completed`, `stage.acceptance.passed=true`, and checkpoint content.

Verification:
- Red test reproduced the bug: focused session-runtime test failed with `pending != completed`.
- Fixed focused test passed.
- Full regression passed: `python -m unittest discover learning_agent` ran 407 tests OK, skipped=1.
- Real visible terminal rerun passed: `learning_agent/acceptance_controller/runs/harness_runtime_alignment_status-20260531_165630/result.json`.
- Latest durable run evidence: `learning_agent/memory/harness/runs/runtime_275e3c33ad6ec332.json` has `status=completed`, `stages[0].status=completed`, and `stages[0].acceptance.passed=true`.

## 2026-05-31 Harness alignment false-completion risk

Status: confirmed residual risk; not resolved yet.

Symptom:
- The project had a real visible terminal acceptance proving that a normal prompt created a durable harness run and completed its stage.
- A later source-only comparison against ClaudeCode showed this does not prove core harness parity.
- The key missing behavior is that the real main loop does not yet drain the durable runtime queue into model-visible context for prompt, task-notification, and resume-interrupted commands.

Confirmed evidence:
- `learning_agent/runtime/session_runtime.py` enqueues the user prompt with `command_queue.enqueue_prompt(user_input)`.
- The same function then calls `agent.run_events(user_input, max_turns=max_turns)` directly.
- Source search shows `RuntimeCommandQueue.dequeue_next()` is used by CLI/tests, but not by the real `LearningAgent.run()` path as a durable command consumer.
- ClaudeCode source `query.ts` gets queued commands by priority, converts them to attachments, yields them into the model turn, and removes consumed prompt/task-notification commands from the queue.

Risk:
- Task notifications can be persisted but still not automatically reach the model on the next real turn.
- Interrupted resume commands can be persisted but still not automatically drive the next real turn.
- Passing unit tests and a single visible terminal status scenario can falsely suggest ClaudeCode harness alignment.

Required fix:
- Treat this as an unfinished alignment task.
- Add red tests for queue-drain-to-model behavior and resume command consumption.
- Implement a real runtime command drain in the main loop before claiming alignment again.
- Add visible terminal acceptance scenarios that prove the model sees queued task notification and resume context without manual intervention.

## 2026-05-31 Harness alignment false-completion risk resolved

Status: resolved and verified.

Root cause:
- The earlier implementation created durable files and single-run acceptance evidence, but did not prove queued task notifications and interrupted resumes entered the real model turn.
- Real visible terminal testing also exposed a second gap: `long_running_work/SKILL.md` loaded only prompt text, because `DYNAMIC_SKILL_CAPABILITY_PACKS` mapped browser skills but not long-running/execution skills.

Fix:
- `run_agent_with_harness_session()` now drains runtime commands and builds model-visible input before calling `run_events()`.
- Background command completion now updates durable task records and enqueues task notifications automatically.
- `DYNAMIC_SKILL_CAPABILITY_PACKS` now maps `long_running_work` to both `execution` and `long_running_work`, plus the other skill directories to their capability packs.
- Acceptance scenarios now use the real `permission_answered` event name instead of the stale `permission_sent` state.

Verification:
- Red test reproduced the skill-loading bug before the mapping fix.
- Full automated regression passed: 414 tests OK, skipped=1.
- Real visible terminal scenarios passed for seed, task-notification feedback, resume-interrupted, background-shell watchdog, and background-shell notification.
- Final queue audit reported `NO_QUEUED_COMMANDS`, proving acceptance notifications were consumed.

Residual risk:
- This resolves the planned core harness alignment gate, not every possible ClaudeCode feature. Future comparisons should still be source-based and should not use README claims as primary evidence.

## 2026-05-31 Compact/status API missing from HTTP bridge

Status: resolved in current compact/resume/status execution pass.

Symptom:
- A new regression test called GET `/status` on the real HTTP command bridge and received HTTP 404.

Confirmed root cause:
- `learning_agent/app/http_bridge.py` only routed GET `/health` and `/v1/health`; status snapshot and status event tail were available through SDK/CLI but not through HTTP.

Fix:
- Added GET `/status` and `/v1/status` backed by `build_status_snapshot()`.
- Added GET `/events` and `/v1/events` backed by `StatusEventStore.list_events()`.
- Added optional token protection for status endpoints when bridge token is configured.

Verification:
- The focused HTTP bridge test now passes and confirms `/events?since_sequence=0&limit=5` returns the same `status_probe` event written to the status event store.

## 2026-05-31 Harness CLI module entrypoint missing

Status: resolved in current compact/resume/status execution pass.

Symptom:
- Direct function test for harness CLI `snapshot` passed, but `python -m learning_agent.harness.cli snapshot --workspace ...` exited with no output.

Confirmed root cause:
- `learning_agent/harness/cli.py` defined `main()` but did not call it under `if __name__ == "__main__"`.

Fix:
- Added the module entrypoint and `SystemExit(main())` so real command-line use returns the correct exit code and prints the status snapshot.

Verification:
- Added regression test `test_harness_cli_module_entrypoint_prints_status_snapshot`.
- The new red test first failed because stdout was empty, then passed after the entrypoint fix.

## 2026-05-31 Compact summary regression expectation mismatch

Status: resolved during deep compact alignment.

Symptom:
- `test_compact_boundary_and_resume_loader_reconstruct_context_without_rerun` failed because `old-0` appeared inside the new compact summary text.

Confirmed root cause:
- The old test was written for a simpler compact behavior where archived messages should disappear from the rendered recovery text.
- The new ClaudeCode-like behavior intentionally preserves archived facts inside a single auditable summary while preventing archived messages from being replayed as standalone user/assistant turns.

Fix:
- Updated the assertion to require `old-0` to appear in the compact summary but not as an independent `{"role": "user", "content": "old-0"}` message.

Verification:
- `python -m unittest learning_agent.tests.test_compact_resume_status_ecosystem` passed.
- Full `python -m unittest discover learning_agent.tests` passed: 426 tests OK, skipped=1.

Residual risk:
- Human-readable summaries can still contain sensitive old text; future privacy work should add redaction policy before summary generation if needed.

## 2026-05-31 Real visible terminal gate for deep compact/status pass

Status: resolved.

Confirmed evidence:
- Automated tests and compile checks passed for the deep compact/resume/status implementation.
- Real visible terminal acceptance ran through `learning_agent/start_oauth_agent.bat` via the controller.
- Run directory: `learning_agent/acceptance_controller/runs/compact_resume_status_deep_alignment-20260531_200122`.
- Controller reported `ACCEPTANCE_CONTROLLER_COMPLETED=True`.
- Independent verifier reported `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.

Fix:
- Added and used `learning_agent/acceptance_controller/scenarios/compact_resume_status_deep_alignment.json`.
- The scenario checks visible terminal startup, prompt delivery, final answer observability, debug log evidence, screenshots, and key deep compact/status markers.

Risk:
- The visible terminal scenario verifies source visibility and final terminal output for this pass. It does not replace the separate unit tests that exercise reactive compact, resume repair, HTTP/SDK filters, and legacy migration behavior.
# 2026-05-31 风险记录：真实浏览器能力

1. 已补：浏览器 MCP 工具现在通过统一执行器记录动作并对临时错误做短重试。
2. 已补：`browser_snapshot` 和 `browser_visual_locate` 现在输出 bounding box、center_x、center_y，`browser_click` 支持 x/y 坐标。
3. 已补：新增 `browser_site_grant`，可开启真实 Chrome origin 严格边界；真实 Chrome 动作默认不自动回放。
4. 已补：新增 `browser_action_log.jsonl` 和 `browser_replay` dry-run 安全回放。
5. 仍需：真实可见终端验收依赖本地可见窗口控制，如果当前 Codex 环境无法观察或输入，最终不能声明完整验收通过。
6. 已修复：`browser_flow_run` 的 `stages` array schema 曾缺少 `items`，真实终端中 OpenAI response_format 拒绝请求；已补 `items` 并加入测试。
7. 已修复：浏览器运行层新增 `browser_launch_visible`，真实终端验收确认 `visible_browser=true`、`headless=false`，不再只有 headless 独立 Chromium。
8. 已修复：真实可见终端验收中 `atomic_write_text()` 曾因 Windows `os.replace` 短暂拒绝访问导致最终失败；现在对 `PermissionError` 做退避重试，并用 `test_runtime_files.py` 锁定。
9. 已修复：`browser_visual_locate` 曾只能定位可交互元素，找不到 `Example Domain` 这类标题文本；现在会额外收集标题、段落、表格等可见文本块。
10. 已修复：`browser_flow_run` 曾因空 `browser_wait` 参数失败；现在在 flow 内自动补 `milliseconds=250`，真实验收日志显示 `browser_flow_run 完成`。

## 2026-05-31 真实可见浏览器验收证据

Status: resolved.

Confirmed evidence:
- Real visible terminal acceptance ran through `learning_agent/start_oauth_agent.bat` via controller.
- Run directory: `learning_agent/acceptance_controller/runs/browser_visible_runtime_acceptance-20260531_211805`.
- Controller reported `ACCEPTANCE_CONTROLLER_COMPLETED=True`.
- `result.json` shows `completed=true`, `assertion.passed=true`, and all final-answer/debug-log checks true.
- Debug log confirms `browser_visual_locate 成功` located `<h1> Example Domain` with center coordinates, and `browser_flow_run 完成` executed `browser_wait` with a 250 ms default wait.

## 2026-05-31 自然实时查询未进入可见浏览器

Status: resolved and verified.

Symptom:
- 精准 prompt `帮我查询3天后武汉的天气，并帮我做一下旅游攻略。` 能得到最终回答，但真实验收没有打开可见浏览器。

Confirmed evidence:
- Run directory: `learning_agent/acceptance_controller/runs/wuhan_weather_travel_exact_prompt-20260531_212955`.
- `result.json` 显示 `completed=true`，但权限决策只有 `mcp__browser_search__web_search` 和 `mcp__browser_search__fetch_url`。
- 日志没有 `mcp__browser_automation__browser_launch_visible`、`browser_open` 或 `browser_snapshot`。

Root cause:
- `detect_real_browser_information_task()` 只有在用户显式说“真实浏览器/可见浏览器/登录态”等关键词后才返回 true。
- 普通天气和旅游攻略 prompt 没有触发 browser harness，也没有在首轮工具池里暴露 `browser_launch_visible`。

Risk:
- 用户以为 agent 在真实可见浏览器里查了天气，但实际只是后台搜索工具完成。
- 这会破坏“肉眼可见真实验收”的可信度。

Required fix:
- 普通实时公开查询也要进入可见独立 Chromium 工作流。
- 显式真实 Chrome 或登录态任务仍要保留原来的真实 Chrome profile 安全路径。

Resolution:
- 新增普通自然实时查询识别：`detect_visible_browser_information_task()`。
- 新增 `Visible Browser Task Harness`，普通天气/攻略查询要求先 `browser_launch_visible(confirm_visible_browser=true)`。
- `LearningAgent.run_events()` 在构造首轮工具池前预加载普通可见浏览器查询工具。
- 普通可见浏览器公开查询新增安全自动授权白名单，避免真实终端验收被多次 y/N 焦点问题打断；`browser_evaluate`、`file://`、缺少 `confirm_visible_browser` 的启动请求仍不自动放行。

Verification:
- Full automated suite passed: `python -m unittest discover learning_agent.tests` ran 444 tests OK, skipped=1.
- Real visible terminal acceptance passed: `learning_agent/acceptance_controller/runs/wuhan_weather_travel_exact_prompt-20260531_215353/result.json`.
- Independent verifier passed for the same run with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.
- Debug log confirms `Visible Browser Task Harness`, `browser_launch_visible 成功`, `visible_browser=true`, `headless=false`, `browser_open`, and `browser_snapshot`.
## 2026-05-31 危险调试权限风险记录

- 风险：`LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS=1` 会跳过 learning_agent 的人工权限确认层，适合用户明确要求的本地调试，不适合默认用于普通用户生产环境。
- 约束：该开关不能取消工具自身的必填确认参数，例如真实 Chrome 连接仍必须由模型传入 `confirm_real_profile=true`，否则验收不能算通过。
- 验收风险：如果真实 Chrome 已被普通方式打开且没有调试端口，普通模式仍应阻断日常 profile 抢占；危险调试模式可以改用隔离 debug profile 启动真实 Google Chrome 测试窗口，但必须清楚说明未读取登录态。
- 审计要求：危险模式下所有自动放行都必须留下 `permission_auto_approved` 事件，否则 controller 无法证明没有人工输入 y。
# 2026-05-31 千问真实 Chrome 拟人操作验收格式风险

现象：
- `real_chrome_qianwen_yinzhou_weather-20260531_225525` 已经实际完成真实 Chrome 打开千问、点击输入框、输入提示词、按 Enter 提交并获得页面回答。
- 但最终回答没有包含场景要求的固定标记和工具名清单，导致 controller 严格断言失败。
- 模型在已有 `browser_snapshot` 内容足够的情况下调用了 `browser_evaluate(document.body.innerText)`，偏离真实 Chrome 默认不读内部状态的隐私边界。

风险：
- 用户目标可能已经完成，但验收器会判失败，容易造成“能力可用”和“验收不合格”的判断混乱。
- 如果未来任务涉及登录态或敏感页面，额外 `browser_evaluate` 可能越过“只看页面可见内容”的边界。

建议：
- 后续需要在工具策略层对真实 Chrome 模式下的 `browser_evaluate` 增加更硬的门禁，而不是只靠 prompt 约束。
- 最终回答格式应由 harness 自动补充关键验收证据，避免模型完成任务后忘记输出 marker、工具链和截图路径。

## 2026-06-01 OAuth/API 结构化 JSON 损坏导致真实浏览器验收中断

Status: resolved and verified.

现象：
- 雷神 H5 真实 Chrome 登录场景中，真实浏览器工具链曾经已经跑通一次，但后续重试时模型在第 0 轮直接输出 `Codex CLI 返回格式错误...`，没有进入 `browser_connect_real_chrome`、`browser_open` 或后续输入步骤。
- 该错误不是浏览器工具失败，而是 OAuth/API 模型返回的结构化 JSON 偶发不完整，适配器把解析错误当作最终自然语言回答交给了 controller。

根因：
- `CodexCliChatModel.chat()` 和 `CodexOAuthChatModel.chat()` 之前只解析一次结构化输出。
- 一旦返回内容不是合法 JSON，agent 会停止工具执行；对长任务和真实浏览器验收来说，这会把偶发格式错误误判成任务失败。

修复：
- `CodexCliChatModel` 新增一次性 JSON 修复重试：第一次解析失败且错误像结构化输出损坏时，追加“只返回合法 JSON”的修复提示，再用同一 schema 请求一次。
- `CodexOAuthChatModel` 新增同样的一次性 JSON 修复重试，并保留原始失败作为兜底，避免修复请求也失败时吞掉真实错误。
- 新增单元测试 `test_codex_oauth_model_retries_once_when_json_output_is_invalid`，证明第一次坏 JSON 会触发第二次修复请求，并最终得到合法工具调用。

验证：
- `python -m unittest learning_agent.tests.test_models_codex_oauth`：47 tests OK。
- `python -m unittest learning_agent.tests.test_browser_runtime_alignment`：16 tests OK。
- 真实可见终端验收 `real_chrome_leishen_login_content-20260601_075721` 通过，`result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。

剩余风险：
- 如果第一次输出和一次修复输出都不是合法 JSON，agent 仍会明确失败；这是有意保留的边界，避免无限重试掩盖模型或接口问题。

## 2026-06-01 Browser Runtime Stage 1-2 剩余风险

Status: open.

风险：
- 当前新增的 `BrowserRuntimeStore` 已接入真实 `browser_automation_mcp_server.py` 工具调用路径，并已通过 `browser_runtime_event` 镜像到统一 status event；但 status snapshot/CLI/API 还没有专门 browser section，因此用户仍不容易用状态命令直接浏览 run/stage/action/event。
- 当前只完成自动化测试和语法检查，没有完成 `learning_agent/start_oauth_agent.bat` 真实可见终端交互验收，不能声明整套浏览器 runtime 对齐开发完成。

建议：
- 下一阶段优先做 Stage 3 session manager，随后在 Stage 11 将 browser runtime run/stage/action/event 纳入 status snapshot、CLI/API 和 verifier 入口，避免用户只能查 JSONL。

## 2026-06-01 Browser Runtime Stage 3 剩余风险

Status: Stage 3 resolved; later browser runtime stages still open.

已解决：
- Stage 3 已补上独立 `BrowserSessionManager` 和 `BrowserTabRegistry`，并接入真实 `BrowserAutomationServer` 页面生命周期，不再只靠 `self.pages` 和 `current_page_id` 旁路状态。
- `browser_plugin_status` 和 `browser_profile_status` 已能展示 session manager 的模式、连接、可见性、headless、tab_count 和 active_tab_id。
- 自动化验证已覆盖 tab id 跨 session 不复用、真实 Chrome profile 路径脱敏、状态报告字段和公开 plugin status 接入。
- 真实可见终端验收 `browser_visible_runtime_acceptance-20260601_105840` 已通过，debug log 确认 `session_mode=visible_chromium`、`connected=true`、`visible=true`、`tab_count=1`、`active_tab_id=browser_session_1_fa131c86-tab-1`。

仍有风险：
- Browser Runtime 仍缺 Observation Engine、Locator Engine、Action Executor、Recovery/Replay/Verifier 2.0、Status Browser Section 等后续阶段。
- 当前 session manager 状态已经接入 server，但还没有被 status snapshot/CLI/API 独立聚合成浏览器专栏；外部 agent 仍需要读 `browser_plugin_status` 或底层 event。

建议：
- 下一步进入 Stage 4 Observation Engine，把 DOM/截图/可访问性/网络/console 观察结果做成可落盘、可比较、可复现的统一 observation，而不是继续只扩展 `browser_snapshot` 文本。

## 2026-06-01 Browser Runtime Stage 4-12 剩余风险

Status: code and automated tests resolved; visible terminal gate still open.

已解决：
- Stage 4-11 已补上 Observation Engine、Locator Engine、Action Policy/Executor、Recovery Manager、Flow Runtime、Secret/Site Permission 模型、Replay/Assertions、Status Browser Section。
- `browser_snapshot` 和 `browser_screenshot` 不再只是返回一次性文本/图片路径，会保存 `BrowserObservation` 并关联到当前 action。
- `browser_flow_run` 已接入 checkpoint runtime，可在同一 `flow_id` 下跳过已完成阶段，降低失败后重跑风险。
- `acceptance.verifier` 已支持 `browser_assertions`，浏览器页面内容和截图证据可以成为真实验收门禁。
- SDK、HTTP bridge、harness CLI、终端状态渲染器都能看到 browser runtime 区块。
- 全量自动化测试已通过：483 tests OK，skipped=1。

仍有风险：
- 真实可见终端交互验收尚未执行；按 AGENTS.md 规则，不能声明开发完成或验收通过。
- `BrowserActionExecutor` 和 `BrowserSecretVault` 已是独立模块，但 server 里仍有部分旧手写逻辑；当前属于兼容接入，不是完全替换。
- `browser_flow_run` 的 checkpoint 依赖稳定 `flow_id`；如果调用方不传 `flow_id` 且不使用 `stages_file`，每次会生成新流程 id，不会自动 resume。

建议：
- Stage 12 必须运行 `learning_agent/start_oauth_agent.bat` 可见终端 controller 场景，检查 debug log 至少包含 `observation_id=`、`Browser Runtime`/browser status 字段或 browser runtime store 证据。
- 后续若继续对齐 ClaudeCode，应把 `BrowserActionExecutor` 进一步接管 server 的 `_start/_complete/_fail_browser_runtime_action`，减少双轨逻辑。

## 2026-06-01 Browser Runtime Stage 4-12 验收风险关闭

Status: resolved and verified.

已关闭：
- Stage 12 真实可见终端门禁已通过，不再停留在“只通过自动化测试”的状态。
- 验收 run：`learning_agent/acceptance_controller/runs/browser_visible_runtime_acceptance-20260601_114746`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 独立 verifier 输出 `schema_version=2`、`completed=true`，并且 artifact checks 全部为 true。
- debug log 已确认 `observation_id=`、`browser_runtime_store=`、`flow_checkpoint`、`status_browser_runtime` 和 `compatible=true`。

仍需关注：
- `BrowserActionExecutor` 是独立协议模块，但 `browser_automation_mcp_server.py` 内仍保留部分旧 action wrapper；当前属于兼容接入，不是完全替换。
- `browser_flow_run` 的断点恢复仍依赖稳定 `flow_id` 或 `stages_file`；调用方完全不传稳定标识时，只能生成新的 flow run。
- 本轮验收验证的是可见独立 Chromium 的 runtime 链路；真实 Chrome 登录态场景仍应继续使用单独的真实 Chrome 验收场景验证。

## 2026-06-01 BrowserActionExecutor 双轨风险收敛

Status: resolved and verified.

已解决：
- 之前的风险是 `BrowserActionExecutor` 已存在，但 `browser_automation_mcp_server.py` 的 `_start_browser_runtime_action()`、`_complete_browser_runtime_action()`、`_fail_browser_runtime_action()` 仍手写 action 生命周期，形成双轨逻辑。
- 本次已让 server 创建 `BrowserActionExecutor(store=self.browser_runtime_store)`，并把 started/completed/failed 三条 helper 路径委托给 executor。
- 红灯测试已证明旧代码不会调用 executor；修改后相关测试和全量测试都通过。

仍需关注：
- 当前只收敛了生命周期 helper，尚未把真实工具调用本身包进 `BrowserActionExecutor.write_lock`；未来如果要做真正并发调度，需要继续让 executor 接管串行/并发执行层。
- 旧的 `browser_visible_runtime_acceptance.json` 大场景在本轮重跑时连续两次失败，确认原因是模型提前最终回答，没有调用 `browser_plugin_status`，不是浏览器工具或 executor 生命周期失败。
- 本轮新增聚焦验收场景 `browser_action_executor_delegation_acceptance.json` 已通过真实可见终端和独立 verifier，适合后续专门验收 action executor 生命周期委托。

## 2026-06-01 BrowserProviderRouter 评审风险收敛

Status: code risk resolved by tests; visible terminal gate still open.

已解决：
- 代码质量审查指出 router 关键词和 `learning_agent/browser/intent.py` 不一致，可能漏判当前浏览器、真实浏览器、真实 Chrome、current browser、login state 等任务；本轮已复用 `REAL_CHROME_INTENT_KEYWORDS` 并新增覆盖测试。
- 审查指出 provider 不可用时 fallback 语义会误导后续 agent；本轮已让普通不可用分支保持 `fallback_provider=unavailable`，只在插件不可用且存在候选 CDP 时把 CDP 作为候选 fallback。
- 审查指出允许 CDP fallback 的分支语义不清；本轮已增加 `reason_code=extension_unavailable_cdp_fallback_allowed` 和 `metadata.fallback_from=chrome_extension`。
- 审查指出 event payload 缺少稳定版本和机器可读原因码；本轮已新增 `schema_version=1`、`reason_code` 和 JSON 安全 `metadata`。
- 审查指出 `provider_events` helper 与 registry 写入/快照路径缺测试；本轮已补充单元测试覆盖。

验证：
- `python -m unittest learning_agent.tests.test_browser_provider_router` 通过：12 tests OK。
- `python -m unittest discover -s learning_agent\tests` 通过：502 tests OK，skipped=1。

仍需关注：
- Stage 1 只建立 provider router 协议层，还没有接管真实 `browser_automation_mcp_server.py` 执行路径。
- `learning_agent/start_oauth_agent.bat` 真实可见终端交互验收仍未完成，按项目门禁不能声明 Stage 1 开发完成。

## 2026-06-01 BrowserProviderRouter 真实终端门禁关闭

Status: resolved and verified.

已关闭：
- Stage 1 真实可见终端交互验收已通过，run 为 `learning_agent/acceptance_controller/runs/browser_provider_router_stage1_acceptance-20260601_165755`。
- controller 的 `result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 真实终端里的 agent 使用 `bash` 成功验证 provider router 协议层，并输出 `PROVIDER_ROUTER_STAGE1_OK provider=real_chrome_cdp reason_code=extension_unavailable_cdp_fallback_allowed schema_version=1 fallback_from=chrome_extension`。
- 独立 verifier 已复验同一 run，输出 `schema_version=2`、`completed=true`、`assertion.passed=true`，并确认 result、event log、debug log 和三张截图 artifact 都存在。

仍需关注：
- Stage 1 的职责是协议层和防误选路由，不负责接管 `browser_automation_mcp_server.py` 的真实执行路径；这个接管应放到 Stage 2 之后的单独阶段计划里继续做。
## 2026-06-01 BrowserProviderAdapters Stage 2 风险关闭

Status: resolved and verified.

已关闭：
- Stage 2 已把 `VisibleChromiumProvider` 和 `RealChromeCdpProvider` 接入真实 `BrowserAutomationServer.call()` 顶层工具路径；如果没有这一步，provider router 只能停留在测试协议层，真实浏览器工具仍会绕过双轨架构。
- 顶层浏览器工具调用现在会写入 `browser_provider_decision` 事件；如果没有这条事件，其他 agent 和验收器无法复盘为什么走可见 Chromium 或真实 Chrome CDP。
- 自动化验证已通过：`python -m unittest learning_agent.tests.test_browser_provider_adapters`、相关浏览器测试组合、全量 `python -m unittest discover -s learning_agent\tests`。
- 真实可见终端验收已通过：`learning_agent/acceptance_controller/runs/browser_provider_adapters_stage2_acceptance-20260601_171446`，独立 verifier 显示 `completed=true` 且 `assertion.passed=true`。

仍需关注：
- Stage 2 只完成现有 Playwright/CDP provider 迁入；模型工具表面仍需要 Stage 3 明确禁止 provider-specific 重复工具，避免未来插件接入后把选择权重新暴露给模型。
- 当前 `browser_connect_real_chrome` 仍是高级控制入口，不是普通 open/click/type 的重复工具；Stage 3 需要用测试把它和统一动作工具的边界写清楚。
## 2026-06-01 Browser Tool Surface Stage 3 风险关闭

Status: resolved and verified.

已关闭：
- provider-specific 重复动作风险已收敛：`chrome_extension_open`、`real_chrome_cdp_click`、`visible_chromium_type` 这类工具不会进入模型 catalog。
- 真实 Chrome 控制入口风险已标记：`browser_connect_real_chrome`、`browser_disconnect_real_chrome`、`browser_profile_status` 会带 `advanced provider-control` 搜索提示，避免被模型当作普通页面动作。
- skill/harness 已明确：不要直接选择 provider；模型只调用统一 `browser_*` 工具，底层由 `BrowserProviderRouter` 选择并写入 event log。
- 自动化验证通过：Stage 3 单测 6 tests OK，相关回归 105 tests OK，全量 513 tests OK。
- 真实可见终端验收通过：`browser_tool_surface_stage3_acceptance-20260601_172518`，独立 verifier 显示 `completed=true` 和 `assertion.passed=true`。

仍需关注：
- Stage 3 没有实现 `browser_tabs_context`；当前 Chrome/登录态任务的强制首步 tab context 合同需要 Stage 4 单独补齐。
- Chrome 插件 provider 尚未实现；当前只是提前防止插件接入后模型工具表面分裂。
## 2026-06-01 Browser Tabs Context Stage 4 风险记录

Status: resolved and verified.

已发现风险：
- 真实 Chrome / 登录态任务如果没有先读取当前标签页上下文，模型可能在不知道 active tab、URL、标题和 page_id 的情况下直接点击或输入。
- 标签页切换、新建、关闭或导航后，如果旧 context 不失效，模型可能拿旧页面信息操作新页面。

本轮处理：
- 新增 `browser_tabs_context`，输出 session、provider、active tab、tab_id、page_id、URL 和 title。
- 真实 Chrome 模式下，`browser_click`、`browser_type`、`browser_type_secret`、`browser_press_key`、`browser_upload_file` 会先经过 context 门禁。
- active tab 改变、页面关闭、导航、真实 Chrome 重连/断开和 close_all 都会让旧 context 失效。

风险关闭证据：
- 全量 `python -m unittest discover -s learning_agent\tests` 已通过，518 tests OK，skipped=1。
- 真实可见终端验收 run 为 `learning_agent/acceptance_controller/runs/browser_tabs_context_stage4_acceptance-20260601_174203`。
- 独立 verifier 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。

## 2026-06-01 Chrome Extension Readonly Stage 5 风险记录

Status: resolved and verified.

已发现风险：
- Chrome 插件路线如果第一版就开放点击、输入、提交，会把登录态浏览器控制面扩大得太快，后续很难审计权限边界。
- 插件脚本如果读取 cookie、storage 或密码类内容，会把“看得见页面内容”和“读取浏览器内部状态”混在一起，破坏真实浏览器隐私边界。
- 插件 provider 如果默认可用，Router 可能在扩展未连接时误选插件路线，导致真实任务失败或误判。

本轮处理：
- Stage 5 只实现 Chrome extension、native host、bridge state、message protocol 和 provider 的只读 MVP。
- 协议只允许 `tabs_context`、`read_page`、`status`，明确拒绝 click/type/press_key/navigate/upload/submit 等写动作。
- 扩展脚本扫描测试禁止出现敏感浏览器 API 片段。
- `ChromeExtensionProvider` 默认 `connected=false` 时不可用；只有 bridge 记录连接后才返回 available。
- `BrowserAutomationServer` 只公开统一的 `browser_extension_status` 状态工具，不向模型暴露 provider-specific 重复动作。

风险关闭证据：
- `python -m unittest learning_agent.tests.test_chrome_extension_readonly_stage5` 已通过，5 tests OK。
- 相关浏览器回归已通过，33 tests OK。
- 全量 `python -m unittest discover -s learning_agent\tests` 已通过，523 tests OK，skipped=1。
- 真实可见终端验收 run 为 `learning_agent/acceptance_controller/runs/chrome_extension_readonly_stage5_acceptance-20260601_175710`。
- 独立 verifier 显示 `schema_version=2`、`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。

仍需关注：
- Stage 5 没有安装真实 Chrome 插件，也没有写 Windows 注册表；这是本阶段有意边界。
- Stage 6 若实现插件写动作，必须先补权限门禁、动作审计和真实终端验收，不能直接把写动作塞进只读 provider。

## 2026-06-01 Chrome Extension Write Actions Stage 6 风险记录

Status: resolved and verified.

已发现风险：
- 插件写动作如果直接从扩展发起，可能绕过 provider 决策、权限、action executor 和事件审计。
- 写动作如果只在 Python provider 里“假成功”，真实 Chrome 扩展脚本不会执行 click/type/key。
- 写动作结果如果不脱敏，页面反馈里的敏感字段可能进入 bridge state 或 debug log。

本轮处理：
- 写动作只能通过 provider 创建 pending command，再由扩展轮询 `poll_commands` 拉取执行。
- 扩展完成后必须通过 `action_result` 回传，bridge 使用协议层统一脱敏后保存。
- `ChromeExtensionProvider` 等待 command result，成功才返回工具结果，失败或超时会抛错。
- `BrowserAutomationServer` 仍通过 `BrowserActionExecutor.execute_action()` 包住插件 provider handler，保留 started/completed 事件。
- 扩展脚本新增命令轮询、页面动作执行和结果回传，同时继续禁止敏感浏览器 API 片段。

风险关闭证据：
- `python -m unittest learning_agent.tests.test_chrome_extension_write_actions_stage6` 已通过，5 tests OK。
- 相关回归已通过，38 tests OK。
- 全量 `python -m unittest discover -s learning_agent\tests` 已通过，528 tests OK，skipped=1。
- 真实可见终端验收 run 为 `learning_agent/acceptance_controller/runs/chrome_extension_write_actions_stage6_acceptance-20260601_181238`。
- 独立 verifier 显示 `schema_version=2`、`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。

仍需关注：
- Stage 6 尚未实现站点级权限，当前连接后的插件 provider 写动作可执行；Stage 7 必须补 origin 权限门禁。
- 本阶段仍未执行真实 Chrome 扩展安装流程；安装 UX 和真实插件全链路总验收应在后续总验收阶段单独确认。

## 2026-06-01 Chrome Extension Site Permissions Stage 7 风险记录

Status: resolved and verified.

已发现风险：
- Stage 6 后插件 provider 一旦连接，就可以排队执行 click/type/key 等写动作；如果没有 origin 权限，登录态页面风险过大。
- 旧 `BrowserSitePermissions` 只有 origin 级宽授权，无法表达“只允许 read，不允许 click/type/submit”。
- 旧 `browser_site_grant` 只维护 server 内存集合，没有同步 Chrome extension provider，容易形成两套权限系统。

本轮处理：
- `BrowserSitePermissions` 升级为 origin + action 级权限模型，并保留旧 `grant(origin)` 宽授权兼容。
- `ChromeExtensionProvider` 在 `browser_snapshot`、`browser_tabs_context`、`browser_visual_locate`、`browser_click`、`browser_type`、`browser_press_key`、`browser_open` 等工具前检查对应权限。
- `browser_press_key` 的 Enter 按 `submit` 权限处理。
- `browser_site_grant` 新增 `permissions` 参数，并同步到 `ChromeExtensionProvider.site_permissions`。
- 权限变化写入 `ChromeExtensionBridgeState.permission_events`，状态可查看事件数量。

风险关闭证据：
- `python -m unittest learning_agent.tests.test_chrome_extension_site_permissions_stage7` 已通过，4 tests OK。
- 相关回归已通过，44 tests OK。
- 全量 `python -m unittest discover -s learning_agent\tests` 已通过，532 tests OK，skipped=1。
- 真实可见终端验收 run 为 `learning_agent/acceptance_controller/runs/chrome_extension_site_permissions_stage7_acceptance-20260601_182242`。
- 独立 verifier 显示 `schema_version=2`、`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。

仍需关注：
- 当前权限 UI 仍是文本/工具方式，不是图形化授权弹窗。
- Stage 8 需要把 provider、native host、tab、permission、run、action、observation 做到状态 CLI/API 可见。

## 2026-06-01 Chrome Extension Status Ecosystem Stage 8 风险记录

Status: resolved and verified.

已发现风险：
- provider、Chrome 插件连接、native host、tab、权限和最近动作如果分散在不同文件里，其他 agent 很难判断真实浏览器当前是否可用。
- 如果终端渲染、SDK、HTTP API、CLI 和模型工具各自读取状态，会重新形成多套旁路系统。
- `browser_provider_status` 如果只支持包路径导入，在 `start_oauth_agent.bat` 这类脚本入口下可能因为导入路径不同而失败。

本轮处理：
- `status_snapshot.py` 新增 `browser.provider_status`，统一从 bridge state 和 BrowserRuntimeStore 聚合状态。
- `status_renderer.py`、`sdk/status.py`、`http_bridge.py`、`harness/cli.py` 和 `browser_automation_mcp_server.py` 全部复用统一快照。
- `browser_provider_status` 增加脚本模式导入 fallback，避免真实可见终端入口下包路径差异导致工具不可用。
- 新增 Stage 8 验收场景，要求真实终端里的 agent 自己执行 focused unittest 并输出固定成功标记。

风险关闭证据：
- `python -m unittest learning_agent.tests.test_chrome_extension_status_ecosystem_stage8` 已通过，3 tests OK。
- Stage 5/6/7/8 与状态生态相关回归已通过，47 tests OK。
- 全量 `python -m unittest discover -s learning_agent\tests` 已通过，535 tests OK，skipped=1。
- 真实可见终端验收 run 为 `learning_agent/acceptance_controller/runs/chrome_extension_status_ecosystem_stage8_acceptance-20260601_184110`。
- 独立 verifier 显示 `schema_version=2`、`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。

仍需关注：
- Stage 8 不包含 GIF/录屏/帧序列证据；这是 Stage 9 的范围。
- 当前 provider 状态是快照级状态，还需要 Stage 11 继续确认每个浏览器动作都进入长任务 harness run/stage/checkpoint。

## 2026-06-01 Browser Visual Evidence Stage 9 风险记录

Status: resolved and verified.

已发现风险：
- 只有单张截图和文本日志时，多步浏览器任务很难复盘“每一步到底看到了什么、点了哪里、页面怎么变化”。
- 如果录制只是工具手动调用，模型在长任务中很容易忘记每一步截图，导致证据链断裂。
- 如果 verifier 只看日志里的 GIF 路径，不检查真实文件，仍可能出现“假验收”。

本轮处理：
- 新增 `BrowserRecordingStore`，统一保存录制 manifest、PNG 帧序列和 GIF。
- 新增 `browser_record_start`、`browser_record_stop`、`browser_gif_export`，保持统一 browser 工具表面。
- 浏览器动作成功后自动捕帧，减少模型忘记截图造成的证据缺口。
- 状态快照和终端渲染新增 `Browser Recordings`。
- 独立 verifier 新增 `required_artifact_globs`，真实检查 manifest、frames 和 GIF 是否存在。

风险关闭证据：
- `python -m unittest learning_agent.tests.test_browser_recording_stage9 learning_agent.tests.test_acceptance_verifier` 已通过，7 tests OK。
- 全量 `python -m unittest discover -s learning_agent\tests` 已通过，539 tests OK，skipped=1。
- `python -m learning_agent.browser.recording --selftest --workspace H:\codexworkplace\sofeware\OpenHarness-main` 已生成真实帧和 GIF。
- 真实可见终端验收 run 为 `learning_agent/acceptance_controller/runs/browser_visual_evidence_stage9_acceptance-20260601_185914`。
- 独立 verifier 显示 `required_artifact_glob_checks` 中 manifest、frames、GIF 三项均为 true。

仍需关注：
- 当前 GIF 导出是基于动作后截图帧，不是视频级屏幕录制；对 agent 验收已足够，但不是高帧率录屏。
- Stage 10 需要继续处理失败恢复/fallback，避免录制证据存在但浏览器轨道选择错误或页面恢复策略错误。
## 2026-06-01 Stage 10 回归风险：状态工具不能被 fallback 门禁误伤

现象：
- Stage 10 初版把 `BrowserProviderKind.UNAVAILABLE` 全部阻断，导致 `browser_tabs_context` 也无法执行。

确认原因：
- `browser_tabs_context` 是恢复/确认状态的只读工具，不能和点击、输入、提交等写动作使用同一阻断策略。
- 旧 Stage 4 测试同时暴露出一个合同变化：读过 `browser_tabs_context` 只代表确认了标签页，不代表允许从插件降级到 CDP。

处理结果：
- `browser_tabs_context`、`browser_tabs`、`browser_provider_status`、`browser_extension_status`、`browser_plugin_status`、`browser_profile_status` 在 provider 不可用时仍允许执行旧只读 handler。
- 写动作仍然必须在插件可用或显式 `allow_cdp_fallback=true` 时才执行。
- 已把 `test_browser_tabs_context_stage4` 的允许写动作场景更新为“读 context + 显式 CDP fallback”。

验证：
- Stage 10 聚焦单测、Stage 4/Provider/Recovery/Recording/Status 回归和全量 544 tests 均通过。
## 2026-06-03 Phase 32 Windows Native Observation Helper Risks

已处理风险：
- 旧风险：Phase29/31 只有静态 helper 和 Null helper，缺少真实 Windows native helper 接入点。已处理：新增 `WindowsNativeWindowObservationHelper` 和 provider 注入合同。
- 旧风险：只读窗口 inventory 与真实屏幕读取边界容易混淆。已处理：新增独立环境变量 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE`，只开 inventory 不会自动截图或读取文本。
- 旧风险：native helper 如果直接写死真实 API，测试和验收会触碰用户桌面。已处理：helper 支持注入 fake capture/text provider，Phase32 验收使用 fake provider。
- 旧风险：native 文本可能把 password/token 等敏感内容写入响应或 metadata。已处理：继续复用 Phase29 evidence store 的敏感行过滤和长度限制。

剩余风险：
- `Win32GdiWindowCaptureProvider` 是 GDI `PrintWindow`/`BitBlt` fallback，不是完整 Windows.Graphics.Capture；部分 UWP、硬件加速、遮挡或权限场景可能截图失败或黑屏。
- `Win32WindowTextProvider` 只读取 Win32 标题和子控件文本，不是完整 UIAutomationClient 文本树。
- Phase32 尚未实现 DPI、多显示器、窗口遮挡、最小化窗口、焦点安全提示和 native helper 权限诊断。
- Phase32 不扩大真实鼠标键盘动作；真实动作仍必须依赖 Phase30/31 锁、abort、窗口目标和 evidence chain。

---

## 2026-06-03 Phase 31 Windows Computer Use Lock/Abort/Evidence Risks

已处理风险：
- 旧风险：崩溃遗留的 desktop control lock 可能永久阻塞后续会话。已处理：`ComputerUseLockManager` 增加 `stale_after_seconds` 和陈旧 owner 恢复证据。
- 旧风险：动作只有计划参数，没有动作前后现场证据。已处理：成功动作现在在执行前后各调用一次只读 `get_window_state`，并把 before/after evidence 绑定同一个 `audit_id`。
- 旧风险：审计只在内存里，真实问题复盘时缺少磁盘证据。已处理：新增 `ComputerUseAuditStore`，保存 events JSONL 和 chain JSON。
- 旧风险：`type_text` 原始文本可能泄露到审计文件。已处理：磁盘审计链使用递归脱敏，并保留 `text_sha256_16` 短哈希用于关联。
- 旧风险：真实终端用户没有直接急停入口。已处理：新增 `/computer abort <reason>` 和 `/computer clear-abort`。
- 本轮实测问题：`parse_lock_timestamp` 之前使用本地时区解析 UTC 字符串，东八区会把刚创建的锁误判为约 28800 秒前的陈旧锁。已处理：改为 `calendar.timegm(...)` 按 UTC 解析。

剩余风险：
- Phase31 的真实动作验证仍使用内存后端和静态窗口，不代表真实 SendInput 已成熟。
- before/after evidence 当前依赖已有 `get_window_state` 合同；真实 Windows.Graphics.Capture 和 UIAutomationClient helper 仍未接入。
- 真实窗口控制还需要 DPI、多显示器、窗口遮挡、焦点切换、动作回滚/重试策略和更严格 app allowlist。
- 终端、Codex UI、安全/隐私设置、密码管理器、认证弹窗和 Windows Run 仍必须保持禁止自动化。

---

## 2026-06-01 ClaudeCode 浏览器源码对比风险记录

Status: open observation.

已确认边界：
- ClaudeCode 本地仓库中 `claude-in-chrome` 的很多集成点可读，但核心浏览器工具实现来自外部包 `@ant/claude-for-chrome-mcp`。
- ClaudeCode `computer-use` 的 OS 级真实鼠标键盘/截图能力源码显示为 macOS 路线，Windows 下不能直接等同为已可用的同能力。
- learning_agent 已有 Chrome extension/native host scaffold，但 `manifest_installer.py` 源码只生成 manifest，不写 Windows 注册表；这说明生产安装体验仍弱于 ClaudeCode 的 `registerWindowsNativeHosts(...)` 路线。

后续处理建议：
- 若要声明“完全对齐 ClaudeCode 浏览器能力”，必须追加真实 Chrome 扩展安装、native host 注册、配对、站点权限、写动作、断线恢复和状态 UI 的完整端到端验收。

## 2026-06-02 Phase 18 Chrome Extension E2E 真实连接边界

Status: open observation.

已确认事实：
- Phase 18 新增 `/chrome extension-e2e-check` 后，真实可见终端验收截图显示 `manifest_ok=true`、`launcher_ok=true`、`pairing_completed=true`、`browser_prompt_queued=true`。
- 同一截图明确显示 `real_extension_connected=false`、`real_extension_e2e=false`。
- 这说明本机当前完成的是可审计 local protocol selftest，不是 Chrome extension UI 已实际连接 native host 的最终态。

处理原则：
- 后续报告不能把 `e2e_level=local_protocol_selftest` 说成真实扩展已连接。
- 只有用户在 Chrome 中实际加载 extension，并让 native host 产生真实连接后，再次运行 `/chrome extension-e2e-check` 显示 `real_extension_connected=true`，才可以把该机器状态称为真实 extension E2E 已闭合。
- Phase 23 最终矩阵必须保留这个字段，避免最终验收把 local selftest 和 real extension 连接混为一谈。
## 2026-06-03 Phase 29 Windows Computer Use Observe Evidence Risks

已处理风险：
- 旧风险：`get_window_state` 只有几何占位，没有可审计文件证据。已处理：新增 evidence store，保存 metadata JSON 和截图 artifact。
- 旧风险：UIA 文本如果直接返回，可能把 password/token/credential 等敏感内容送给模型。已处理：按行过滤敏感关键词，并限制响应摘要长度。
- 旧风险：只看工具响应无法证明证据落盘。已处理：真实可见终端验收和独立 verifier 均检查固定 marker，额外文件检查确认 evidence 文件存在。
- 旧风险：没有 native helper 时容易误报截图/UIA 已完成。已处理：`NullWindowObservationHelper` 和 status 都明确说明未配置真实 native helper。

剩余风险：
- Phase 29 尚未实现真实 Windows.Graphics.Capture 截图 helper，也未实现 UIAutomationClient 文本树读取。
- 当前真实终端验收使用静态安全 helper 证明证据合同，不能当作真实桌面窗口截图能力已成熟的证明。
- 真实截图接入后仍必须避免终端、Codex UI、安全设置、密码管理器、认证弹窗和 Windows Run。
- 后续动作阶段必须先补 durable lock、abort flag、动作前后 evidence 和窗口相对坐标验证，不能直接开放宽泛鼠标键盘动作。

---

## 2026-06-03 Phase 33 Windows Native Diagnostics Risks

已处理风险：
- 旧风险：Phase32 状态只说 GDI/Win32 fallback，不能结构化说明 WGC/UIA 是否是首选缺口。已处理：新增 `phase33_windows_native_diagnostics` 诊断对象。
- 旧风险：后端状态无法直接告诉 `/computer` 或其他 agent 当前 active provider 是谁。已处理：`WindowsComputerUseBackend.status()` 透传 `native_observation_diagnostics`。
- 旧风险：用户可能误以为 native helper opt-in 等于真实动作扩展。已处理：诊断对象明确包含 `safe_observe_only=true` 和 `real_input_actions_expanded=false`。

剩余风险：
- Phase33 仍未接入真正 Windows.Graphics.Capture provider。
- Phase33 仍未接入真正 UIAutomationClient 控件树 provider。
- 当前依赖探测只是诊断，不代表依赖可用时已经自动接管观察流程。
- 后续如果实现真实 WGC/UIA provider，仍必须做敏感文本过滤、窗口 allowlist、真实可见终端验收和独立 verifier。

---

## 2026-06-03 Phase 34 Windows UIAutomation Text Provider Risks

已处理风险：
- 旧风险：Phase33 只能诊断 UIA 缺口，默认文本读取仍停留在 Win32 标题/子控件 fallback。已处理：新增 UIA 优先文本 provider。
- 旧风险：直接使用 UIA provider 时，如果依赖缺失可能导致无文本或异常。已处理：新增 `FallbackNativeWindowTextProvider`，失败时降级到 Win32 文本。
- 旧风险：UIA 控件树可能输出过多文本。已处理：`WindowsUiautomationTextProvider` 包含 `max_depth` 和 `max_nodes` 上限。
- 旧风险：UIA 文本可能包含敏感内容。已处理：Phase34 测试确认 UIA 文本进入 evidence store 后仍会过滤 `password` 行。

剩余风险：
- Phase34 没有强制安装真实 `uiautomation` 依赖；没有依赖时仍会降级到 Win32 fallback。
- Phase34 验收使用 fake UIA module 证明 provider 合同和脱敏链路，不等同于已验证真实第三方应用完整 UIA 树。
- 真实 UIA 读取不同应用时可能遇到权限、空控件树、虚拟控件或性能问题，后续需要用真实安全窗口做专门验收。
- 终端、Codex UI、安全设置、密码管理器、认证弹窗和 Windows Run 仍必须禁止自动化。

---

## 2026-06-02 Phase 28 Windows Computer Use Read-Only Inventory Risks

已处理风险：
- 旧风险：Windows backend 只有协议占位，无法列出窗口和 app。已处理：新增 `windows_backend.py`，提供静态 inventory 和可选 Win32 只读枚举。
- 旧风险：只读观察和真实动作共用同一个启用开关，容易让安全边界不清楚。已处理：新增 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE`，与真实动作开关分离。
- 旧风险：真实桌面标题可能泄露到日志或被模型误选为自动化目标。已处理：Phase 28 测试和验收使用静态安全窗口；真实探针也会过滤空标题、终端、Codex、安全、密码和认证相关标题。
- 旧风险：只读模式下仍可能误执行动作。已处理：`WindowsComputerUseBackend(real_actions_enabled=False)` 会明确拒绝鼠标、键盘和窗口动作。

剩余风险：
- Phase 28 的 Win32 ctypes 探针只能做基础窗口枚举，不能证明窗口内容可见、未遮挡、DPI 坐标准确或多显示器坐标完整。
- `get_window_state` 还没有真实截图文件和 UI Automation 文本树，当前 evidence 仍是占位；Phase 29 必须补齐证据链后才能支持更可信的窗口状态判断。
- 即使能列出真实窗口，也不能自动化终端、Codex UI、安全/隐私设置、密码管理器、认证弹窗或 Windows Run。
- 后续若开启真实动作，必须先有窗口锁、目标确认、动作前后截图证据、撤销/中断策略和真实可见终端验收。

---
## 2026-06-03 Phase 35-42 Planning Tooling Notes

Status: open observation.

已确认事实：
- 当前 shell 是 PowerShell，不支持 Bash 风格 `python - <<'PY'` heredoc。
- 当前 PowerShell 的 `New-Item` 不接受 `-LiteralPath` 参数，创建目录时应使用 `-Path`。
- 当前 Python 环境缺少 `uiautomation`、`comtypes`、`winrt/winsdk Windows.Graphics.Capture` 依赖。

处理原则：
- 后续运行 inline Python 应使用 PowerShell here-string：`@' ... '@ | python -`。
- 后续创建目录使用 `New-Item -ItemType Directory -Force -Path ...`。
- Phase 35 不能把 fake UIA module 验收当作真实 UIA 验收；依赖缺失时必须输出诚实诊断。

---
---

## 2026-06-03 Phase 39 Windows Coordinates Risks

Resolved risks:
- Old risk: window-relative action coordinates could be treated as raw screen coordinates on high-DPI or multi-monitor desktops.
- Handling: Phase39 routes action coordinates through `build_coordinate_context(...)`, records DPI scale and display-relative coordinates, and sends physical screen coordinates to the backend.
- Old risk: negative monitor origins could be lost if code assumed every display starts at zero or above.
- Handling: Phase39 tests cover a display with `left=-800`, proving negative logical coordinates stay intact.

Remaining risks:
- The coordinate model depends on `display` or `displays` metadata being available from the window inventory/provider. If a future real provider omits that metadata, Phase39 falls back safely but cannot know the exact monitor.
- Phase39 does not expand real action permissions; the action surface still remains intentionally bounded by approval, lock, abort, forbidden target, and `actions_expanded=false` gates.
---

## 2026-06-03 Phase 40 Windows Abort Cleanup Risks

Resolved risks:
- Old risk: abort existed as a durable flag but lacked a user-visible runtime notification trail.
- Handling: Phase40 records `computer_use_abort_requested` notifications whenever `/computer abort` or runtime abort is used.
- Old risk: turn cleanup and lock release were available as low-level operations but not expressed as a session runtime lifecycle step.
- Handling: Phase40 adds `cleanup_turn(...)` and `/computer cleanup [session_id]`, which release the selected session lock and record a cleanup notification.
- Old risk: status UI could show lock/abort and approval, but not the runtime cleanup/notification layer.
- Handling: `/computer status` now includes a `Computer Runtime` section with model, marker, counts, last notification, and `actions_expanded=false`.

Remaining risks:
- Phase40 notifications are intentionally small runtime records, not OS-level toast notifications. A later phase can decide whether to add Windows toast integration.
- Cleanup does not clear abort automatically. This is intentional because clearing abort should remain an explicit recovery action.
- Phase40 does not expand real desktop actions; all approval, lock, abort, forbidden-target, and `actions_expanded=false` gates remain active.

---

## 2026-06-03 Phase 41 Windows Image Results Risks

Resolved risks:
- Old risk: screenshot artifacts existed as paths inside generic window state data, so the model could miss them during long tool result handling.
- Handling: Phase41 adds explicit `image_result` blocks and a `Computer Use Image Results` text section.
- Old risk: screenshot artifact paths could be lost from session context because they were not registered as active artifacts.
- Handling: `LearningAgent` now records Computer Use image artifact paths in `active_artifacts` and writes a `computer_use_image_result` observation.
- Old risk: the same image block can appear at both top-level `data.image_results` and nested `state.image_results`, causing duplicate model-visible image lines.
- Handling: `collect_image_result_blocks(...)` deduplicates by `artifact_path`.
- Old risk: making image results model-visible could accidentally carry sensitive UIA text.
- Handling: `image_result` blocks only include image metadata and paths, explicitly set `sensitive_text_included=false`, and tests check that `phase41-secret-must-not-leak` never appears in block/text/agent output.

Remaining risks:
- Phase41 makes screenshots easier for the model to reference, but it does not perform image OCR, visual reasoning, or UI element detection by itself.
- The actual screenshot quality still depends on the underlying observation helper or future WGC/native provider.
- Phase41 does not expand real desktop actions; approval, lock, abort, forbidden-target, and `actions_expanded=false` gates remain active.

---

## 2026-06-03 Phase 42 Windows Final Matrix Risks

Resolved risks:
- Old risk: Phase35-41 could each pass independently while the final Windows Computer Use acceptance story still missed a key capability.
- Handling: Phase42 adds a matrix JSON and `final_matrix.py` runner that requires Phase35-41 coverage plus observe, evidence, approval, gated refusal, safe action, abort cleanup, and artifact visibility.
- Old risk: a final aggregate run might accidentally trigger real UIA/WGC capture or real SendInput actions.
- Handling: Phase42 injects safe dependency-missing checks for Phase35/36, uses Phase37 fake implementation coverage, and keeps `actions_expanded=false`.
- Old risk: final acceptance could ignore Phase41 image artifact visibility.
- Handling: Phase42 requires `artifact_visibility=true` and checks Phase41 `agent_artifact` plus sensitive text hidden.

Remaining risks:
- Phase42 does not install or verify missing native dependencies such as `uiautomation`, `comtypes`, or Windows.Graphics.Capture Python bindings.
- Phase42 does not prove broad real Windows GUI automation is mature; it proves the current safety contracts are present, wired, and visible through real terminal acceptance.
- Future work can add real dependency installation/native helper validation only after explicit user approval because it may touch system state.

---

## 2026-06-03 Phase 52 Status UI Compatibility Regression

Resolved issue:
- Symptom: Phase43 regression failed because `/computer status` no longer contained `Computer Native Capability Matrix` after the compact Phase51 renderer.
- Root cause: Phase51 compressed the native section to `Computer Native` and displayed only the first four capabilities, so Phase43 marker and `windows_sendinput` were no longer visible.
- Fix: `learning_agent/app/computer_status_renderer.py` now restores the Phase43 title and marker while keeping the compact Phase51 panel, and explicitly includes `windows_sendinput` in the visible capability subset.
- Verification: Phase43 focused tests 4 OK; Phase51 focused tests 4 OK; Phase43-52 regression 39 OK.

Remaining risk:
- The status panel is still intentionally compact and does not show every capability line. For full detail, callers should use Phase43 matrix helpers or future detailed status commands.

---

## 2026-06-03 Phase 57 Real UIA Locator Risks

Resolved risks:
- Old risk: using Notepad as the safe UIA smoke target could expose existing user Notepad tab titles or unrelated document names.
- Handling: Phase57 now opens a dedicated temporary WinForms window with a unique exact title such as `LearningAgent-Phase57-RealUiaLocatorSmoke-*`, and the smoke lookup exact-matches that unique title.
- Old risk: PowerShell UIA could emit extremely large, NaN, or Infinity bounding values that fail JSON conversion.
- Handling: the provider script clamps UIA bounds through `Convert-ToSafeInt`, so bad provider coordinates do not crash the whole run.
- Old risk: helper v2 `read_uia_tree` could remain a placeholder while the standalone Phase57 module passed.
- Handling: `WindowsNativeHelperV2Worker` now delegates `read_uia_tree` to `WindowsRealUiaLocatorRuntime` and reports `uia_locator_available` in status.
- Old risk: UIA names and automation IDs could leak sensitive text.
- Handling: Phase57 sanitizes each UIA text field through the existing `filter_accessibility_text` path and tests that `phase57-secret` is absent from the whole response.

Remaining risks:
- Phase57 depends on PowerShell/.NET UIAutomationClient being available on Windows; missing or restricted UIA access must be reported honestly and not converted into fake success.
- Virtualized or owner-drawn controls can still produce incomplete trees; later high-level tools must treat locator confidence and candidate count as safety data, not decoration.
- Phase57 intentionally keeps `actions_expanded=false`; Phase58 must not reuse the locator to perform writes without a fresh target guard, lock, and before/after evidence.

---

## 2026-06-03 Phase 58 Real SendInput Guard Risks

Resolved risks:
- Old risk: a changed `title_preview` could be hidden by an older `title` field during static inventory normalization, allowing a same-hwnd title drift test to pass incorrectly.
- Handling: `windows_backend.normalize_window_record(...)` now prefers `title_preview` and falls back to `title`, matching the protocol model and Phase58 identity guard expectations.
- Old risk: real `SendInput` mouse events could succeed while Unicode keyboard events silently returned 0, making the action path look partially alive without changing the safe TextBox.
- Handling: the keyboard path now declares the full Win32 INPUT union shape, so `cbSize` matches the system expectation and Unicode text events are actually accepted.
- Old risk: type_text results could leak raw input text into logs or event payloads.
- Handling: Phase58 stores only `text_length`, `text_sha256_16`, and `text_redacted=true`; focused tests and real smoke verify the original text is absent from serialized output.
- Old risk: denied targets could still have low-level side effects.
- Handling: the target guard returns before event construction, and tests assert forbidden and changed targets keep `low_level_event_count=0` and an empty fake sender event list.

Remaining risks:
- Phase58 deliberately allows real input only in the dedicated `LearningAgent-Phase58-*` safe window; broad application control still requires later phases for lock/session policy, semantic high-level tools, and user-visible status integration.
- Windows foreground restrictions can still affect real input reliability on locked, secure, or elevated desktops; future phases must keep before/after evidence mandatory instead of trusting SendInput return counts alone.

---

## 2026-06-03 Phase 59 Session Context Risks

Resolved risks:
- Old risk: approval, display, screenshot, hidden-window, last-action, last-error, and cleanup state were scattered across runtime, approval, terminal grants, and status rendering.
- Handling: `ComputerUseSessionContextStore` now persists these fields under `learning_agent/memory/computer_use/session_state/` and `/computer status` reads the same source.
- Old risk: cleanup could leave stale allowlist, grant flags, hidden windows, or action/error summaries in the next turn.
- Handling: `cleanup_session(...)` clears these fields and marks `cleanup_completed=true`; focused tests assert the fields are reset.
- Old risk: multiple sessions could overwrite each other while sharing the same workspace.
- Handling: each sanitized session id maps to a separate JSON file, and tests assert cleaning `phase59-a` does not alter `phase59-b`.

Remaining risks:
- Phase59 is a state layer only; future phases must bind real tool calls to this context before broad production use.
- The default context currently records only fields explicitly provided by callers; later tool layers must consistently call `bind_context(...)` and `update_app_state(...)` so the store remains authoritative.

---

## 2026-06-03 Phase 60 Persistent Grants Risks

Resolved risks:
- Old risk: `/computer grant` looked like an approval UX but only stored a terminal UI draft and did not participate in real action evaluation.
- Handling: Phase60 adds `WindowsComputerUsePersistentGrantStore`; `/computer approve` now writes evaluable persistent grant records with app/window/display/action_scope/ttl/reason/grant_flags.
- Old risk: granted desktop access could remain valid forever.
- Handling: each grant stores `expires_at_epoch` and `evaluate(...)` returns `grant_expired` after TTL.
- Old risk: users could not reliably revoke a production grant from the terminal.
- Handling: `/computer revoke <app>` now revokes Phase60 persistent grants and also removes the old Phase51 terminal draft for compatibility.
- Old risk: high-risk actions such as system keys and clipboard access could be blurred into normal desktopAction grants.
- Handling: `approve(...)` refuses system key and clipboard scopes unless `systemKeyCombos`, `clipboardRead`, or `clipboardWrite` are explicitly present.
- Old risk: approval choices were not easy to inspect in `/computer status`.
- Handling: status now includes `Computer Persistent Grants` with active/revoked/expired counts and state/audit paths.

Remaining risks:
- Phase60 provides the grant lifecycle store and terminal UX, but high-level execution paths in later phases must consistently call `evaluate(...)` before using real action backends.
- `scope=*` is supported but intentionally requires explicit high-risk flags; future UI should keep it visibly scary and time-limited.
- Phase60 does not add global hotkey abort or streaming hooks; Phase61 owns that runtime safety layer.

---

## 2026-06-03 Phase 61 Abort Streaming Hooks Risks

Resolved risks:
- Old risk: an abort flag could be set while a real action was already close to low-level dispatch, leaving one final SendInput batch able to slip through.
- Handling: `Phase61AbortAwareLowLevelSender` checks `ComputerUseLockManager.is_abort_requested()` immediately before forwarding low-level events and returns `low_level_event_count=0` on abort.
- Old risk: exception, Ctrl+C, or model/tool interruption could bypass turn cleanup and leave locks or abort state behind.
- Handling: `WindowsComputerUseAbortStreamingHooks.run_with_cleanup(...)` catches interruption-like exits, invokes runtime cleanup, records audit flush intent, and writes a streaming cleanup event.
- Old risk: stale-lock recovery itself could become a new active lock owner.
- Handling: Phase61 `recover_stale_lock(...)` now releases the recovered owner after verifying recovery and records `lock_released_after_recovery`.
- Old risk: global hotkey work could be overstated as installed without an actually registered Windows hook.
- Handling: Phase61 status honestly reports `global_hotkey_registered=false` and exposes `/computer abort` plus controller abort as fallback.

Remaining risks:
- A real Windows global hotkey or low-level keyboard hook is still not registered by default. Adding one later must be opt-in, revocable, and separately verified on a visible desktop.
- High-level tools in Phase62 must consistently wrap write-capable senders with `Phase61AbortAwareLowLevelSender`; the hook exists now, but future callers must use it.
- Streaming hooks currently persist JSONL events locally; future UI can improve live rendering, but the evidence path is already stable.

---

## 2026-06-03 Phase 62 High-Level Computer Tool Risks

Resolved risks:
- Old risk: high-level desktop tasks could bypass the low-level safety chain by directly implementing click/type orchestration.
- Handling: `WindowsHighLevelComputerToolRuntime` routes write operations through Phase60 grant evaluation, the shared desktop lock, Phase58 target guard, and Phase61 abort-aware sender.
- Old risk: read-only observation could accidentally take over the write lock and block or perturb active desktop-control sessions.
- Handling: `run_read_only_batch(...)` accepts only read-only operations and focused tests assert an external write owner remains unchanged.
- Old risk: high-level tool execution could be invisible in streaming/progress surfaces.
- Handling: Phase62 mirrors `StreamingToolExecutor` lifecycle events and high-level operation progress into `phase62_progress_events.jsonl`.
- Old risk: `find_control` could return only a raw node without explaining confidence or candidates.
- Handling: Phase62 returns `uia_candidate_summary` with `matched`, `candidate_count`, `confidence`, `reason`, and a safe control summary.
- Old risk: terminal users would not know high-level tools exist or where artifact/progress evidence lives.
- Handling: `/computer high-level-tools` and `/computer status` now show the Phase62 marker, operation list, progress path, and artifact directory.

Remaining risks:
- Phase62 keeps `actions_expanded=false`; it proves high-level orchestration and safe chain integration, not broad real application control.
- The Phase62 image artifact is a deterministic contract artifact for result plumbing; real Windows screenshot capture and pixel validation remain owned by Phase56.
- Future model-facing schemas must expose high-level operations carefully so they cannot be used to bypass approval, lock, target guard, or abort hooks.
## 2026-06-03 Phase 63 Controller Takeover Risks

Resolved risks:
- Old risk: external agents such as Codex could control and debug `learning_agent` only by remembering ad hoc commands.
- Handling: `WindowsComputerUseControllerTakeoverDebugSurface.build_takeover_plan(...)` now returns a stable `controller.ps1` launch plan and explicitly preserves `start_oauth_agent.bat` as the visible terminal gate.
- Old risk: controller failures were hard to hand off because `result.json`, event logs, readable summaries, and screenshots were scattered.
- Handling: `read_acceptance_run(...)` summarizes those artifacts, and `export_evidence_package(...)` writes a compact package for external agent handoff.
- Old risk: external controller abort could be implemented by directly mutating lock state.
- Handling: Phase63 exposes `/computer abort <reason>` as the controller abort path and records `direct_lock_write_allowed=false`.
- Old risk: HTTP or stdio control could be mistaken for the final acceptance gate.
- Handling: Phase63 status and CLI token enforce `visible_terminal_required=true`, `http_loopback_only=true`, `token_required=true`, and `approval_bypass_allowed=false`.

Remaining risks:
- Phase63 is a debug/control surface, not a remote daemon. Any future HTTP/stdio expansion must keep loopback-only binding, token protection, and visible-terminal acceptance as the production gate.
- Evidence package export summarizes artifact paths and key booleans; if future acceptance artifacts become richer, the summary schema should be extended rather than scraping logs ad hoc.
- Phase64 must include Phase63 in the final parity-plus production matrix so controller takeover is verified alongside screenshot, UIA, SendInput, grants, abort hooks, and high-level tools.

---

## 2026-06-03 Phase 64 Final Parity Plus Matrix Risks

Resolved risks:
- Old risk: Phase53-63 could each pass in isolation while the overall Windows Computer Use capability still had no single final production gate.
- Handling: `run_phase64_parity_plus_matrix_contract(...)` now executes and rolls up all Phase53-63 contracts into one final matrix with `phase_count=11`.
- Old risk: Phase58's `actions_expanded=true` could be misread as unsafe global expansion.
- Handling: Phase64 distinguishes `controlled_actions_expansion=true` from `uncontrolled_actions_expanded=false`; Phase58 is accepted only when target guard, persistent grants, abort hooks, and zero-event refusal are all present.
- Old risk: final claims could rely on CLI/selftest instead of the user-mandated visible terminal gate.
- Handling: Phase64 requires the scenario file, Phase63 visible terminal launch boundary, and final visible-terminal acceptance evidence.
- Old risk: external controller takeover could silently bypass approval.
- Handling: Phase64 requires `approval_bypass_blocked=true` from Phase63 and `high_risk_default=true` from Phase60.

Remaining risks:
- If a future phase adds another `actions_expanded=true` report, Phase64 or its successor must explicitly classify whether it is controlled or unsafe instead of letting it pass by default.
- The final matrix proves the contracts and visible terminal scenario; deeper real-world app coverage still belongs to future targeted E2E scenarios.
- Scenario token lines are intentionally strict. Any future token rename must update the module, tests, scenario JSON, and visible terminal verifier together.

---
---

## 2026-06-03 Phase65-75 Humanlike Windows Operator Blueprint Risks

Resolved planning risks:
- Old risk: “控制所有应用” could be misunderstood as writing one fixed script per application.
- Handling: the new blueprint requires a universal observe-plan-act-verify-recover loop and explicitly sets `per_app_scripts_required=false`.
- Old risk: representative E2E could be too narrow and prove only text-entry tools.
- Handling: Phase74 now includes a real Paint drawing scenario that exercises launch, focus, canvas recognition, color/tool selection, drag/continuous mouse paths, save, and visual verification.
- Old risk: the Paint scenario could be cheated by directly generating an image file.
- Handling: the blueprint requires real `mspaint.exe`, real mouse/keyboard actions, saved visual evidence, and `direct_image_file_cheat=false`.

Remaining risks:
- OCR/vision dependencies may be required for robust Paint and arbitrary app control; installing those dependencies requires explicit user confirmation.
- Real Paint drawing introduces nondeterminism in UI layout, DPI scaling, and tool ribbon positions, so implementation must combine UIA, screenshot, and visual fallback rather than hard-coded coordinates.
- “All normal apps” must still exclude password, payment, admin, terminal-danger, security, login, captcha, and private-data flows unless the user explicitly confirms the exact high-risk action.
---

## 2026-06-03 Phase65-75 Implementation Plan Risks

Planning risks handled:
- The implementation plan explicitly keeps OCR/vision dependency installation as a stop condition rather than an automatic install.
- The plan separates generic action building from Phase72 real-app authorization, so new hotkey/drag/scroll primitives do not become uncontrolled desktop actions by themselves.
- The Phase74 Paint Pikachu scenario requires real `mspaint.exe`, action logs, visual evidence, and `direct_image_file_cheat=false`.

Remaining risks:
- Phase74 real E2E can still be affected by DPI scaling, Paint ribbon layout, Windows version, language, and focus timing.
- Phase72 must be implemented carefully; it is the point where authorized normal real app actions become possible.
- If a later phase cannot complete visible terminal acceptance, that phase must remain not complete even when unit tests pass.

---

## 2026-06-03 Phase65-75 Blueprint Backup Tooling Note

Resolved tooling issue:
- Attempt: create the learning backup directory with `New-Item -ItemType Directory -Force -LiteralPath ...`.
- Actual result: this Windows PowerShell environment reported `A parameter cannot be found that matches parameter name 'LiteralPath'`.
- Confirmed cause: `New-Item` in the current shell accepts `-Path` for this usage, while later `Copy-Item` and `Get-ChildItem` still support `-LiteralPath`.
- Resolution: recreated the directory with `New-Item -ItemType Directory -Force -Path ...` and copied all blueprint snapshots successfully.

---

## 2026-06-03 Phase65 Humanlike Operator Contract Risks

Resolved risks:
- Old risk: Phase65-75 could drift into per-application scripting rather than a universal humanlike operator architecture.
- Handling: Phase65 now exposes `per_app_scripts_required=false` and `prompt_to_normal_windows_app=true` in the runtime contract and visible terminal scenario.
- Old risk: future Paint Pikachu verification could be cheated by directly generating an image file.
- Handling: Phase65 now exposes `direct_file_cheat_blocked=true` and keeps this token in tests, CLI, and the real terminal scenario.
- Old risk: Phase65 could accidentally expand the real desktop action surface before observation, planning, authorization, and recovery layers are ready.
- Handling: Phase65 keeps `actions_expanded=false`, and tests assert this boundary.

Remaining risks:
- Phase65 is a contract stage only; it does not yet observe screenshots/UIA, plan tasks, launch apps, or send real input.
- Phase66 must carefully fuse screenshot, UIA, window state, and OCR/vision slot data without exposing sensitive raw text.
- Every later runtime phase still needs focused tests, compile checks, CLI self-check, real visible terminal acceptance, and learning backup before being marked complete.

---

## 2026-06-03 Phase66 Observation Fusion Risks

Resolved risks:
- Old risk: screenshot, UIA, OCR/vision, and window state could remain scattered across separate reports, forcing later planners to guess which source is authoritative.
- Handling: `WindowsObservationFusionRuntime.observe(...)` now returns one `FusedComputerObservation` with screenshot, UIA, OCR slot, and window state sections.
- Old risk: future OCR/vision support could require changing the observation protocol later.
- Handling: Phase66 adds `ocr_or_vision_slot=true` while honestly reporting `provider_available=false` and `install_attempted=false`.
- Old risk: UIA or OCR raw sensitive text could enter model-visible output.
- Handling: Phase66 filters UIA node fields, keeps `raw_text_included=false`, and tests that `phase66-secret` is not serialized.

Resolved tooling issue:
- First visible terminal controller run failed before prompt input because Windows would not focus the unique Phase66 terminal window.
- Handling: the failed `LearningAgent-Phase66-ObservationFusion-210058` window was closed, and the second real visible run completed successfully at `learning_agent/acceptance_controller/runs/agent_capability_phase66_observation_fusion-20260603_210148/result.json`.

Remaining risks:
- Phase66 uses contract fake inputs for acceptance; it proves protocol fusion and sensitive-boundary behavior, not real-world app observation coverage.
- OCR/vision dependencies remain uninstalled by design; installing or enabling them later requires explicit user confirmation.
- Phase67 must avoid turning prompt planning into per-app scripts; it should generate generic task steps with checkpoints, expected results, and risk levels.

---

## 2026-06-03 Phase67 Prompt Task Planner Risks

Resolved risks:
- Old risk: the agent could receive a prompt like “画一个皮卡丘” but have no structured plan for launch, observe, draw, save, and verify.
- Handling: `WindowsPromptTaskPlanner.plan(...)` now creates a Paint Pikachu representative plan with generic operation names and per-step expected results, risk levels, and checkpoints.
- Old risk: prompt planning could drift into per-app coordinate scripts.
- Handling: Phase67 explicitly returns `per_app_script=false`; Paint steps are semantic operations such as `identify_canvas`, `select_color`, `draw_body`, and `verify_visual_result`.
- Old risk: password/payment/admin prompts could be planned like normal app tasks.
- Handling: `classify_risk(...)` detects high-risk keywords and makes the first step `request_user_confirmation`.

Remaining risks:
- Phase67 is deterministic and rule-based for contract tests; future richer planning may need an LLM, but it must keep the same safety fields and visible-terminal acceptance.
- Phase67 does not execute or verify real applications; Phase68 must prove closed-loop execution with observation before action and verification after write actions.
- The Paint Pikachu plan is still a plan, not a drawing result. Real Paint control and visual verification remain Phase74 responsibilities.

---

## 2026-06-03 Phase68 Closed-Loop Executor Risks

Resolved risks:
- Old risk: the executor could perform actions without a fresh observation.
- Handling: `WindowsClosedLoopComputerExecutor.run(...)` records `observed` before each action or verification step.
- Old risk: write actions could succeed or fail silently.
- Handling: every write action produces a `verified` event after `acted`.
- Old risk: a failed verification could let the task continue blindly.
- Handling: failed verification triggers `recovered`, then a new `observed` event, then another `verified` event.
- Old risk: two write actions could form a blind coordinate chain without an intervening observation.
- Handling: `blind_write_chain_detected(...)` detects that pattern, and the Phase68 contract proves the dangerous chain is blocked while normal closed-loop events remain allowed.

Remaining risks:
- Phase68 still uses injected fake observer, actor, verifier, and recoverer components for contract acceptance.
- Phase68 does not launch, focus, click, type, drag, draw, or save artifacts in real Windows apps.
- Phase69 must introduce safe app launch and focus without changing Windows settings, registry, UAC, or default apps.
- Later real-action phases must keep target identity checks, user confirmation for high-risk actions, abort hooks, locks, evidence, and visible terminal acceptance.

---

## 2026-06-03 Phase69 App Window Control Risks

Resolved risks:
- Old risk: a prompt plan could say `launch_app` or `focus_window` without a safe, auditable launch contract.
- Handling: `build_launch_plan(...)` now emits a `Start-Process` style plan with `changes_registry=false`, `changes_system_settings=false`, `requires_admin=false`, and `uses_shell_string=false`.
- Old risk: app launch and focus tests could accidentally open or focus real user applications.
- Handling: `Phase69RecordingLauncher` and `Phase69RecordingFocuser` are used for contract acceptance and visible terminal self-checks.
- Old risk: after launching/focusing, the target window could drift to a terminal or another app and later actions would still continue.
- Handling: `WindowsAppWindowControlRuntime.verify_target_identity(...)` compares window identity before and after, and blocks changed targets with `reason=target_window_identity_changed`.

Remaining risks:
- Phase69 intentionally does not open real apps in acceptance; it proves the contract layer, not real app lifecycle reliability.
- Phase69 does not click, type, drag, draw, save files, or control Paint.
- Phase70 must add generic click/type/control actions without bypassing Phase68 closed-loop ordering or Phase69 target identity checks.
- Phase72 must still decide when normal real apps are authorized; high-risk apps and terminal/security/auth flows remain blocked unless explicitly confirmed by the user.

---

## 2026-06-03 Phase70 Generic Control Actions Risks

Resolved risks:
- Old risk: generic query click/type could bypass Phase57 locator and become blind coordinate clicking.
- Handling: Phase70 uses `SemanticControlLocator.find(...)` before query click/type and refuses missing targets with zero events.
- Old risk: typing could leak raw text into reports.
- Handling: Phase70 reports only text length and SHA256 short hash, with `raw_text_included=false`.
- Old risk: canvas-like targets without UIA controls had no generic action path.
- Handling: Phase70 wraps visual points as synthetic controls and delegates through the high-level click interface.
- Implementation bug found during verification: `_phase70_controls_from_observation(...)` recursed into default empty `{}` when `uia` was absent.
- Handling: fixed recursion by only descending into an actual independent nested `uia` dict.

Remaining risks:
- Phase70 uses a recording high-level tool for contract acceptance; production real input still depends on injecting the Phase62-compatible runtime and later Phase72 authorization.
- Phase70 does not cover hotkeys, menu navigation, scroll, drag, continuous mouse paths, drawing strokes, or Paint E2E.
- Phase71 must add generic input action builders while preserving zero-event refusal for forbidden system hotkeys.

---

## 2026-06-03 Phase71 Generic Input Actions Risks

Resolved risks:
- Old risk: hotkey, menu, scroll, and drag support might jump straight to real SendInput without a policy boundary.
- Handling: every Phase71 event is built with `real_dispatch_allowed=false`, and the default sender only records events.
- Old risk: system-level hotkeys could open OS or security surfaces.
- Handling: Phase71 blocks `ctrl+alt+delete`, `win+r`, `win+x`, `ctrl+shift+esc`, and all Windows-key combinations with zero events.
- Old risk: drag actions could be represented as a single blind jump.
- Handling: `build_drag_path(...)` preserves every path point and requires a start and end point before recording events.

Remaining risks:
- Phase71 is an event-construction layer only; it does not prove real hotkey/menu/scroll/drag behavior inside applications.
- Phase72 must add user-authorized real-app safety evaluation before any Phase71 event can reach a real dispatcher.
- Phase74 must still prove representative real app workflows, including Paint Pikachu, without direct image-file generation.

---

## 2026-06-03 Phase72 Real App Safety Boundary Risks

Resolved risks:
- Old risk: Phase70/71 generic actions could be interpreted as ready for arbitrary real-app dispatch without a final safety gate.
- Handling: `WindowsRealAppSafetyBoundary.evaluate(...)` now requires Phase60 persistent grants before ordinary real-app actions can proceed.
- Old risk: terminal, Codex UI, login/auth/captcha/payment/admin/security/private-data, Windows Run, or system management windows could be treated like normal app targets.
- Handling: Phase72 classifies those windows as high risk and refuses them by default with `low_level_event_count=0`.
- Old risk: stale approval fields or prompt-level hints could bypass durable authorization.
- Handling: Phase72 detects `approval_bypass`, `force_allowed`, and allowed `previous_approval` style hints and returns `approval_bypass_blocked` unless a real persistent grant exists.
- Old risk: an action authorized earlier could still fire after the user requested abort.
- Handling: Phase72 checks a Phase61-compatible abort gate after authorization and immediately before low-level send, returning `abort_before_low_level_send` and zero events.

Remaining risks:
- Phase72 is a policy boundary and does not itself prove real SendInput behavior in Notepad, Explorer, browser, or Paint.
- Phase72 depends on downstream dispatchers respecting `ready_for_low_level_send=true`.
- Phase73 must add non-secret app memory without storing secrets, prompt text, terminal commands, auth data, payment data, or private user content.
- Phase74 must still prove representative real app workflows, including Paint Pikachu, without direct image-file generation.

---

## 2026-06-03 Phase73 App Memory Risks

Resolved risks:
- Old risk: self-learning memory could store passwords, tokens, cookies, private text, payment data, authentication codes, or terminal commands.
- Handling: `WindowsComputerUseAppMemoryStore.remember_app_hint(...)` rejects those inputs before state write and records only a short hash with `redacted=true` in audit.
- Old risk: app memory could become a script recorder that replays hidden commands or coordinate macros.
- Handling: Phase73 allows only safe hint types and rejects `script` plus terminal-command-like values such as PowerShell/CMD/Remove-Item.
- Old risk: users could have no way to clear app-specific learning.
- Handling: `revoke_app_memory(app)` marks only the target app's active hints revoked and `list_app_hints(app)` hides revoked hints.
- Old risk: repeated safe hints could produce unbounded duplicates.
- Handling: Phase73 uses a stable hint hash id and updates existing active hints instead of appending duplicates.

Remaining risks:
- Phase73 is a memory store only and does not prove that hints improve real workflows.
- Downstream planners must treat app memory as advisory hints, not commands or hard-coded scripts.
- Phase74 must prove representative workflows on controlled files/artifacts and must keep Paint Pikachu from cheating by direct image-file generation.

---

## 2026-06-04 Phase74 Representative E2E Risks

Resolved risks:
- Old risk: representative E2E could become only one toy workflow and fail to prove cross-app generality.
- Handling: Phase74 matrix now covers Notepad, Explorer, Browser, standard window/dialog style, and Paint Pikachu.
- Old risk: Paint Pikachu could be cheated by directly writing a PNG/JPEG instead of controlling Paint.
- Handling: Phase74 stores `artifact_kind=interaction_evidence_json`, `direct_image_file_cheat=false`, and 13 drag-path drawing actions targeting `mspaint.exe`.
- Old risk: browser or Explorer scenarios could touch private profile data or user folders.
- Handling: Phase74 scenarios report `reads_private_profile=false`, `cookies_read=false`, `tokens_read=false`, and keep artifacts under a controlled matrix directory.
- Old risk: window-style testing could change registry, Windows settings, or require admin.
- Handling: Phase74 common safety fields force `changes_registry=false`, `changes_system_settings=false`, and `requires_admin=false` across scenarios.

Remaining risks:
- Phase74 safe contract does not open Paint live or dispatch real input; it proves the cross-app contract and interaction evidence shape.
- A later live smoke, if requested, must be separately guarded by Phase72 authorization, Phase60 grants, Phase61 abort checks, and controlled artifact paths.
- Phase75 must aggregate Phase65-74 honestly and avoid claiming arbitrary-app perfection beyond the current safety-gated contract coverage.

---

## 2026-06-04 Phase75 Humanlike Operator Matrix Risks

Resolved risks:
- Old risk: Phase65-74 could each pass while the overall Windows Computer Use story still had no single final gate.
- Handling: Phase75 now aggregates all ten phase reports, requires `phase_count=10`, and fails if any source phase summary does not pass.
- Old risk: final status could accidentally claim every app needs a custom script.
- Handling: Phase75 requires `per_app_scripts_required=false` from the universal contract and prompt planner path.
- Old risk: Paint Pikachu could be validated by direct image-file generation instead of humanlike drawing evidence.
- Handling: Phase75 inherits Phase74's `direct_image_file_cheat=false`, `real_paint_app_control=true`, and `humanlike_drawing_actions=true` checks.
- Old risk: an external controller could bypass approval or expand low-level actions without safety.
- Handling: Phase75 requires `approval_bypass_blocked=true` and `uncontrolled_actions_expanded=false`.

Remaining risks:
- Phase75 is a safe-contract matrix and visible terminal acceptance gate; it does not perform live arbitrary-app operation.
- Real Paint drawing, live Notepad/Explorer/browser dispatch, and broad production app control still require a separately authorized live-smoke or production dispatcher plan.
- Future live dispatch must keep Phase60 grants, Phase61 abort, Phase72 safety boundary, target drift checks, controlled artifact paths, and zero-event refusal for unsafe windows.

---

## 2026-06-04 Phase76-89 Windows Production Live-Control Risks

Resolved risks:
- Old risk: the remaining ClaudeCode gap could stay as scattered modules without one production Host Adapter.
- Handling: Phase76-89 adds `WindowsProductionComputerUseHostAdapter` as the unified coordination point for observation, input, permissions, clipboard, abort, cleanup, and tools.
- Old risk: broad desktop control could accidentally expand into unsafe terminal/login/security windows.
- Handling: `WindowsLiveControlPermissionGate` keeps representative allowlist checks and sentinel denial for terminal/auth/security-style targets.
- Old risk: long text input could overwrite the user's clipboard.
- Handling: `WindowsProductionClipboardGuard` saves, writes, verifies, uses, and restores clipboard content.
- Old risk: Paint Pikachu acceptance could be faked by writing an image file.
- Handling: Phase76-89 keeps `direct_image_file_cheat=false` and requires humanlike stroke evidence in the representative E2E matrix.
- Old risk: the real visible terminal gate could be skipped.
- Handling: `agent_capability_phase76_89_windows_live_control.json` passed through `start_oauth_agent.bat` via the acceptance controller.

Remaining risks:
- Phase76-89 acceptance runs in safe contract mode, not uncontrolled live arbitrary-app dispatch.
- Real live Paint drawing and broad native app operation still need explicit user authorization, real desktop smoke scope, target identity checks, abort gate, cleanup gate, and controlled artifacts.
- Future changes must avoid treating `claudecode_gap_closed=true` as permission to bypass Phase60 grants, Phase61 abort hooks, Phase72 safety boundaries, or visible terminal acceptance.

---

## 2026-06-04 Phase90 Live App Dispatcher Risks

Resolved risks:
- Old risk: Phase76-89 had production structure but no single dispatcher object that composed authorization, app launch, safety boundary, and input events.
- Handling: Phase90 adds `WindowsLiveAppDispatcher`, which composes Phase60, Phase69, Phase71, and Phase72.
- Old risk: authorization could be written for a different window identity than the launcher actually uses.
- Handling: Phase90 aligns grant window ids to Phase69 recording launcher ids such as `phase69-window:notepad.exe`.
- Old risk: dangerous apps such as PowerShell could enter the dispatcher path.
- Handling: Phase90 blocks unsafe launch plans and verifies `dangerous_window_zero_events=true`.
- Old risk: text input could leak raw text into reports.
- Handling: Phase90 records text length and digest only and verifies `raw_text_hidden=true`.

Remaining risks:
- Phase90 still defaults to recording dispatch and does not prove live control of every real Windows application.
- `LEARNING_AGENT_PHASE90_ENABLE_REAL_DISPATCH=1` must not be treated as enough by itself; real dispatch still needs target identity, permission grant, abort, cleanup, and visible terminal validation.
- A future live Paint/Notepad smoke should be scoped to controlled files/windows and should keep zero-event refusal for unsafe or drifting targets.

---

## 2026-06-04 Phase91 Controlled Notepad Live Smoke Risks

Resolved risks:
- Old risk: Phase90 had a generic dispatcher but no dedicated Notepad file/window identity plan.
- Handling: Phase91 adds a controlled file plan and dedicated Notepad identity with explicit `notepad.exe` binding.
- Old risk: Notepad positive path could bypass the existing Phase90 dispatcher.
- Handling: Phase91 positive path writes a Phase60-style grant through Phase90 and dispatches through the same controlled route.
- Old risk: unauthorized or dangerous targets could appear successful because the positive Notepad path passed.
- Handling: Phase91 verifies unauthorized Notepad and dangerous PowerShell remain zero-event refusals.
- Old risk: users could misread the phase as default live desktop control.
- Handling: Phase91 prints `real_notepad_smoke_executed=false` in the default token line and requires `LEARNING_AGENT_PHASE91_ENABLE_REAL_NOTEPAD_SMOKE=1` for the optional real path.

Remaining risks:
- Phase91 automated and visible-terminal default acceptance is safe-contract mode, not a proof that Notepad was physically opened and edited.
- The optional real Notepad path still needs a separately authorized visible desktop smoke before it can be used as live-control evidence.
- Future phases must keep target identity, explicit authorization, abort, cleanup, and raw-text hiding before expanding to more real apps.

---

## 2026-06-04 Phase92 Universal Windows Computer Use Mode Blueprint Risks

Resolved risks:
- Old risk: Phase90/91 could be misunderstood as a direction where every app needs a custom controller.
- Handling: Phase92 blueprint explicitly rejects per-app controller architecture and requires `per_app_controller_required=false`.
- Old risk: Notepad/Paint representative scenarios could become the product architecture.
- Handling: Phase92 defines `representative_apps_are_acceptance_only=true` as a required success token.
- Old risk: "Control all apps" could be interpreted as uncontrolled desktop input.
- Handling: Phase92 keeps `default_real_actions_enabled=false`, `uncontrolled_actions_expanded=false`, and mandatory safety boundary checks.
- Old risk: A generic mode could leak the user's raw prompt into reports or observation logs.
- Handling: Phase92 stores prompt hash and length only, and tests verify raw prompt text is absent from reports and agent observations.
- Old risk: High-risk Chinese prompts could bypass older English-heavy risk checks.
- Handling: Phase92 adds Chinese and English high-risk keyword checks and verifies `high_risk_requires_confirmation=true`.

Remaining risks:
- Phase92 implements `UniversalWindowsComputerUseRuntime`, but default acceptance remains safe-contract mode.
- Future implementation must keep avoiding hard-coded app workflows in the universal runtime.
- Future real-app smoke phases must prove they use the universal runtime, not app-specific shortcuts.
- Future live-control expansion must keep explicit authorization, target identity, abort, cleanup, and visible terminal acceptance before sending real input.

---

## 2026-06-04 Phase93 Universal Live Execution Gate Risks

Resolved risks:
- Old risk: the universal runtime could remain a static status report without an observe-plan-act-verify execution gate.
- Handling: Phase93 adds `UniversalWindowsLiveExecutionGate` and composes Phase92, Phase68 closed-loop execution, Phase70/71 generic actions, Phase72 safety boundary, Phase60 grants, and the production host adapter.
- Old risk: the architecture could slide back into one controller per local app.
- Handling: Phase93 prints `no_per_app_controller=true` and `representative_apps_are_acceptance_only=true`.
- Old risk: unsafe or drifting targets could look successful because only the positive path was tested.
- Handling: Phase93 verifies unauthorized, unsafe, and target-drift refusals with zero low-level events.
- Old risk: Phase93 was blocked by the `start_oauth_agent.bat` OAuth state mismatch, so Rule 17 acceptance could not pass.
- Handling: after the OAuth/model chain repair, `agent_capability_phase93_universal_live_execution_gate-20260604_203855/result.json` passed with `completed=true`, `assertion_passed=true`, and `permission_sent_count=0`.

Remaining risks:
- Sandboxed shell commands cannot be trusted for atomic-write behavior because the shell sandbox rejects rename/delete operations; escalated CLI is required for realistic default-path verification.
- Phase93's authorized positive path is recording-only; it does not physically click or scroll the user's desktop.
- Future phases must not treat Phase93's acceptance as blanket permission for uncontrolled physical desktop input; any real dispatch expansion still needs explicit authorization, target identity, abort, cleanup, and visible terminal proof.

---

## 2026-06-04 Phase94 Authorized Real Dispatch Candidate Risks

Resolved risks:
- Old risk: Phase93 could prove only a recording-only loop after authorization.
- Handling: Phase94 adds `WindowsAuthorizedRealDispatchCandidate`, which turns an authorized safe target into low-level mouse/keyboard/scroll event candidates and sends them to an injected low-level sender.
- Old risk: an authorized action could send to a stale or missing target.
- Handling: Phase94 runs an inventory target recheck before sender dispatch and verifies target drift produces zero low-level events.
- Old risk: the target recheck initially treated missing `display_id` from static inventory normalization as a hard target change.
- Handling: Phase94 now uses `app_id + window_id + title_sha256_16` as the hard identity and keeps `display_id` as audit context, so safe static snapshots do not false-refuse while real app/window/title drift still blocks.
- Old risk: text input could leak raw user text into reports.
- Handling: Phase94 stores text length and SHA256 digest only and verifies `raw_text_hidden=true`.
- Old risk: users could misread this phase as default physical desktop control.
- Handling: the default sender is recording-only, token output includes `real_dispatch_default_disabled=true` and `real_dispatch_performed=false`, and visible-terminal acceptance requires zero permission prompts.

Remaining risks:
- Phase94 does not physically control arbitrary Windows applications; it proves the authorized sender bridge in safe-contract mode.
- A future physical SendInput phase must still require explicit environment opt-in, persistent grant, target identity recheck, high-risk refusal, abort before low-level send, cleanup, evidence, and real visible terminal acceptance.
- The target identity rule should be revisited when a richer real inventory reliably preserves display metadata, but it must not become so strict that normalized snapshots false-refuse safe targets.

## 2026-06-04 Runtime WinError 5 Replace/Unlink Failure During Phase95

已处理风险：
- 现象：Phase95 CLI self-check 在写 `persistent_grants.json` / `phase95_controlled_physical_sendinput_report.json` 时触发 `PermissionError [WinError 5] 拒绝访问`，失败点位于 `learning_agent/runtime/files.py` 的 `os.replace`。
- 证据：最小 `atomic_write_json` 探针在 `learning_agent/memory/...` 和 `learning_agent/test/...` 下都复现 `os.replace` 拒绝，而普通 `write_text` 能成功。
- 证据：单独 `FileLock` 探针显示锁文件创建成功，但 `Path.unlink()` 释放锁时同样触发 `WinError 5`。
- 根因：当前 Windows/Codex workspace 允许普通写入，但拒绝 rename/replace/delete 这类文件系统操作；旧 runtime 同时依赖 `os.replace` 和“创建锁文件后删除锁文件”的模型。
- 修复：`atomic_write_text()` 保留 replace + 重试作为首选路径；只有 PermissionError 重试耗尽后才直接写入目标文件兜底，并尽力清理临时文件。
- 修复：Windows 下 `FileLock` 改用 `msvcrt.locking` 锁住固定字节区域，关闭句柄即可释放锁；mutex 文件可删除时清理，删不掉时保留为无害载体。
- 验证：新增 runtime 红灯转绿，Phase95 CLI 自检转绿，全量 unittest 845 OK skipped=1。

剩余风险：
- 在拒绝删除的 workspace 中，临时文件或 mutex 文件可能残留；当前修复保证它们不阻塞主流程，但目录卫生需要后续如有权限再清理。
- 直接写入兜底不是原子替换，只在 replace 被永久拒绝时启用；正常环境仍优先使用原子 replace。

---

## 2026-06-05 Phase101 Universal Computer Use Permission Mode Risks

Resolved risks:
- Old risk: the product design could drift back into per-application allowlists for every normal app.
- Handling: Phase98-101 require `/computer use` normal mode to print `per_app_allowlist_required=false` and `ordinary_apps_allowed_by_risk_policy=true`, with focused tests and visible-terminal acceptance proving the user-facing command path.
- Old risk: `/computer use --full` could look like a one-step privilege escalation.
- Handling: Phase100 requires `risk=high`, strong confirmation, a short-lived token, wrong-token refusal, expired-token refusal, and high-risk target blocking even after full mode.
- Old risk: visible-terminal acceptance plan originally described multiple `/computer` commands in one scenario, but the controller only sends one terminal input per scenario.
- Handling: Phase101 uses four direct terminal command scenarios so each real prompt is typed into a visible `start_oauth_agent.bat` window and independently verified.

Remaining risks:
- `learning_agent.computer_use.__init__` currently does not export the newer Phase99 `UniversalWindowsLiveExecutionGate`, so legacy import style `from learning_agent.computer_use import UniversalWindowsLiveExecutionGate` can fail even though direct module imports and focused Phase99 tests pass. A future cleanup should update package exports without changing runtime behavior.
- Phase101 validates permission mode behavior and policy gating, not unrestricted physical control of every Windows application. Any physical input expansion still needs explicit enablement, target identity recheck, high-risk refusal, abort/cleanup, and visible terminal acceptance.

---

## 2026-06-05 Phase102 Full Mode Execution Gate Risks

Resolved risks:
- Old risk: `UniversalWindowsLiveExecutionGate` always evaluated real actions as `"click"`, so `/computer use --full` could be confirmed but still have no execution-layer difference from normal mode.
- Handling: Phase102 maps explicit launch prompts to `launch_app`, passes that action class into `evaluate_with_mode_session()`, and reports `full_mode_session_used=true` plus `full_mode_action_ready=true` only when full mode actually unlocks that action.
- Old risk: observe steps went through the action path and could mask the real block/allow decision for the following write action.
- Handling: observe/read/wait steps now return `observe_step_no_dispatch` with zero events and are skipped when selecting the true blocked action decision.
- Old risk: package-level import `from learning_agent.computer_use import UniversalWindowsLiveExecutionGate` failed.
- Handling: `learning_agent/computer_use/__init__.py` now exports `UniversalWindowsLiveExecutionGate`; Phase93 package-level regression passes.

Remaining risks:
- Phase102 intentionally keeps `launch_app` as recording-only. It proves full-mode action-class authorization, not physical app launching.
- Future physical launch support must still add explicit target identity checks, abort/cleanup, high-risk refusal, rollback/user confirmation behavior, and a new visible terminal acceptance gate before claiming real desktop launch control.

---

## 2026-06-05 Phase103 Controlled App Launch Risks

Resolved risks:
- Old risk: Phase102 full-mode `launch_app` could only return a recording-only placeholder, so the execution gate still had no controlled app-launch backend path.
- Handling: Phase103 adds `WindowsControlledAppLaunchCandidate`, reuses Phase69 safe launch plans, and lets `UniversalWindowsLiveExecutionGate` inject the candidate for full-mode launch actions.
- Old risk: adding launch support could accidentally open local apps during tests or normal full-mode runs.
- Handling: the default path requires `enable_real_launch=False`, reports `real_app_launch_disabled_by_default=true`, keeps `backend_launch_reaches_launcher=false`, and verifies `real_desktop_touched=false`.
- Old risk: dangerous targets such as PowerShell could reach the launch backend.
- Handling: Phase103 refuses unsafe Phase69 plans before backend dispatch and verifies `unsafe_launch_zero_events=true`.

Remaining risks:
- Phase103 does not claim unrestricted physical launch control. Optional real launch still needs explicit enablement, safe target selection, cleanup, high-risk refusal, user-facing policy, and future visible-terminal proof before being treated as production behavior.
- Current prompt target extraction intentionally supports only safe representative ordinary apps (`notepad`, `mspaint`, `calc`) and defaults to `notepad`; broader app discovery should be a later phase with its own safety model.

---

## 2026-06-05 Phase105 Full Mode Controlled Real Launch Risks

Resolved risks:
- Old risk: Phase103 proved that full-mode `launch_app` could reach a controlled candidate, but the universal live execution path still always passed `enable_real_launch=false`.
- Handling: Phase105 adds `controlled_real_launch_enabled` and `controlled_launch_test_file` to `UniversalWindowsLiveExecutionGate` and `_Phase93ClosedLoopActor`, and only passes `enable_real_launch=true` when the Phase105 gate is explicitly enabled.
- Old risk: a future real launch could open an app without cleanup.
- Handling: Phase105 real path uses `Phase105ControlledNotepadSmokeLaunchCandidate`, which delegates to Phase104 controlled Notepad smoke for unique test file creation, visible-window verification, process cleanup, verified-window cleanup, and residual-process checks.
- Old risk: tests could accidentally open real apps.
- Handling: Phase105 focused tests use `Phase105SpyLaunchCandidate` and the default contract uses `Phase103RecordingLaunchBackend`; real Notepad launch only runs when the double environment gate is enabled.
- Old risk: a user could interpret `/computer use --full` as a blanket application launcher.
- Handling: Phase105 real gate is currently Notepad-only and reports `uncontrolled_actions_expanded=false`; the acceptance scenario explicitly says not to open other apps or interact with user windows.

Remaining risks:
- Phase105 still proves only one controlled Notepad launch path. It does not provide unrestricted application discovery, arbitrary app launching, arbitrary window input, or blanket local-computer takeover.
- Future broader launch support must add target identity, app classification, high-risk refusal, user-visible status, abort/cleanup, per-action evidence, and real visible terminal acceptance for each expanded surface.
- A failed direct smoke or visible acceptance can leave a Notepad window if Windows refuses cleanup; every future real-launch phase should keep the residual-window check as a final verification step.

---

## 2026-06-05 Phase106 Interactive Full Launch Risks

Resolved risks:
- Old risk: Phase105 proved the full-mode controlled launch path only through a contract/helper entry, not through the actual `/computer` user command path.
- Handling: Phase106 adds `/computer launch notepad`, which uses the active `ComputerUseModeSessionStore` and requires `/computer use --full-confirm` before reaching the Phase105 bridge.
- Old risk: adding a launch command could accidentally become arbitrary app launch.
- Handling: Phase106 is Notepad-only, returns `phase106_notepad_only_refused` for other targets, and reports `uncontrolled_actions_expanded=false`.
- Old risk: default full mode could open a real application unexpectedly.
- Handling: default Phase106 path keeps `controlled_real_launch_gate_passed=false`, `real_full_launch_attempted=false`, and `real_desktop_touched=false`; real Notepad launch requires both Phase106 environment gates.
- Old risk: real acceptance could leave a Notepad process behind.
- Handling: Phase106 real path reuses Phase104 visible-window verification and cleanup; post-acceptance process check reported `notepad_process_count=0`.

Remaining risks:
- Phase106 still proves only one controlled Notepad launch from the `/computer` command path. It does not provide arbitrary app discovery, arbitrary launch, arbitrary app input, or unrestricted desktop control.
- Future broader app support must add target identity, classification, high-risk refusal, abort/cleanup, per-action audit evidence, and a real visible terminal acceptance gate for every expanded surface.

---

## 2026-06-05 Phase107 Interactive Launch Target Resolver Risks

Resolved risks:
- Old risk: `/computer launch <target>` only accepted a hard-coded Notepad path, so broader user phrases would be rejected without a reusable safety classifier.
- Handling: Phase107 adds `resolve_interactive_launch_target()` with ordinary app aliases and stable target parsing fields.
- Old risk: expanding target handling could accidentally route terminal or system settings targets into the launch path.
- Handling: Phase107 refuses high-risk tokens such as PowerShell, CMD, terminal, registry, settings, admin, credential, and security-related targets before Universal gate routing.
- Old risk: recognizing Calculator or Paint could be misunderstood as real launch support.
- Handling: Phase107 marks Calculator and Paint as ordinary but `real_launch_supported=false`; command output keeps `real_full_launch_attempted=false` and `real_desktop_touched=false`.

Remaining risks:
- Phase107 still does not provide real launch support for Calculator or Paint.
- Future broader app support must add per-app identity, visible-window verification, cleanup, residual-process checks, and real visible terminal acceptance before enabling real launch for any new app family.
- High-risk token lists are conservative and string-based; later phases should evolve this into a stronger app identity and policy layer before supporting arbitrary installed applications.

---

## 2026-06-05 URG-4 Package Export Compression Issue

Status: resolved in current working tree.

Observation:
- `learning_agent/computer_use/__init__.py` was compressed into two very long lines where import and `__all__.extend(...)` statements appeared after `#` comments.

Impact:
- Python treated those import and export statements as comments, making package-level Computer Use exports unreliable even though direct submodule imports still worked.

Handling:
- Rewrote `__init__.py` into executable multiline imports and `__all__` entries.
- Preserved Phase98, `UniversalWindowsLiveExecutionGate`, URG-1, URG-2, and URG-3 exports.
- Added URG-4 exports for `UniversalObservePlanActVerifyLoop` and its marker/CLI/contract helpers.
## 2026-06-05 Task 3 Target Identity CLI Warning

Observation:
- Running `python -m learning_agent.computer_use.target_identity` emits a runpy warning because the `learning_agent.computer_use` package initialization imports modules that already load `target_identity`.

Impact:
- The warning does not affect the Task 3 API or script-mode CLI result, but it makes `python -m` output less clean for acceptance logs.

Current handling:
- Use `python learning_agent\computer_use\target_identity.py` for the Task 3 self-check until package-level eager imports are cleaned up in a broader package initialization refactor.

Status:
- Tracked as a low-risk packaging cleanliness issue, not a Task 3 functional blocker.
---

## 2026-06-05 URG-5 Canvas Change Observation Gap

Status: resolved in current working tree.

Observation:
- The first URG-5 implementation sent generic drag-path low-level events, but the verifier still reported `canvas_changed_after_real_actions=false`.

Root cause:
- The observe-plan-act-verify loop did not pass its internal `real_dispatch_performed` flag into the next observation frame in this representative contract, so the Paint observation runtime could not see that the injected sender had already dispatched drag events.

Handling:
- `Phase120PaintObservationRuntime` now accepts the same representative drag sender used by `UniversalActionDslRuntime`.
- The after-observation reads `drag_sender.real_desktop_touched` and marks the canvas state as changed only after the shared sender records low-level drag events.
- Focused URG-5 tests and the visible terminal scenario now require `canvas_changed_after_real_actions=true`.

Remaining risk:
- URG-5/URG-6 are blueprint maturity contracts with representative low-level sender evidence. Future work that replaces the representative sender with uncontrolled physical desktop input must keep explicit authorization, target identity recheck, abort/cleanup, high-risk refusal, and visible terminal acceptance.

## 2026-06-05 URG-6 Direct `python -m` Runpy Warning

Status: tracked as a packaging cleanliness issue, not an URG-6 functional blocker.

Observation:
- Running `python -m learning_agent.computer_use.universal_final_maturity_matrix` prints the final `UNIVERSAL_REAL_GUI_COMPUTER_USE_READY` token and exits with code 0, but stderr also prints a runpy warning that the module was already present in `sys.modules`.

Root cause:
- `learning_agent/computer_use/__init__.py` eagerly imports URG-6 symbols for package-level exports, so `python -m` sees the submodule already imported before executing it as a script.

Current handling:
- The visible-terminal acceptance scenarios call the stable `main()` function through `python -c`, which avoids the warning and passed with `assertion.passed=true`.
- A future package initialization cleanup can replace eager imports with lazy exports, but that refactor is outside the URG-5/URG-6 completion scope.

## 2026-06-05 Isolated Worktree Baseline Import Failure

Status: open environment risk.

Observation:
- Created isolated worktree `.worktrees/codex-computer-use-full-desktop-task-router` from commit `be71968`.
- Focused baseline tests failed before new implementation because the clean worktree could not import `learning_agent.app.chrome_status_renderer`.
- The main working directory contains many historical untracked files, including app/computer_use/test modules that current dirty-workspace tests depend on.

Impact:
- A clean git worktree from the current commit is not a faithful runnable baseline.
- Subagent-driven implementation should not blindly commit or delete the unrelated historical untracked files.
- Reviewers must distinguish this environment issue from new Task 1 implementation failures.

Decision:
- Proceed with subagent workflow on the current project state/forked worker context while preserving unrelated dirty files.
- Treat the clean-worktree baseline failure as a repository hygiene risk to fix separately, not as part of the Desktop Task Router Task 1 scope.

## 2026-06-06 `/computer maturity` Recording Evidence Overclaim

Status: mitigated in source; visible terminal recheck pending.

Observation:
- The user screenshot showed `/computer maturity` printing `COMPUTER_USE_FULL_MATURE_OK` while also showing `maturity_known_limit_real_desktop_execution=false`, `real_desktop_touched=false`, and `low_level_event_count=0`.
- The same screenshot showed a natural Paint/Pikachu prompt returning `computer_use_full_mode_required` before full-confirm and not opening real Paint.

Root cause:
- The terminal maturity command used the old `full_maturity_matrix.py` path, which could pass based on recording/representative evidence.
- The default `ComputerUseDesktopTaskRuntime` did not inject any real execution loop, so `real_actions=True` had no production target after full mode confirmation.

Handling:
- Added `WindowsPaintPikachuRealExecutionLoop` and injected it into the default desktop task runtime.
- Added `real_desktop_execution_loop_available` to the maturity matrix passed gate.
- Added automated tests around the new controlled Paint real loop.

Remaining risk:
- The new Paint loop estimates the Paint canvas from the window rectangle because a robust Paint canvas UIA locator is not yet implemented.
- True completion still requires controller-driven visible terminal validation that opens real Paint and confirms the drawing action in the user-visible session.

## 2026-06-06 Paint/Pikachu Fragmented Drawing False Positive

Status: resolved for the controlled Paint/Pikachu representative path.

Observation:
- A controller run could pass after opening real Paint, but the evidence screenshot showed only disconnected lines and did not look like Pikachu.
- The earlier visual gate accepted a tiny number of non-background pixels, so a partial or fragmented drawing could be reported as success.

Root cause:
- The first long body outline could be sent before Paint finished switching to the pencil tool.
- Long drag paths were not dense enough for reliable human-recognizable drawing.
- The visual gate checked "some canvas pixels changed" instead of checking a recognizable distribution across ears, face/body, and tail regions.

Handling:
- Added a bounded low-level `pause` event after selecting the Paint pencil tool.
- Densified drag paths and added a second-pass body outline.
- Tightened screenshot verification to require recognizable region coverage.
- Verified with real visible `start_oauth_agent.bat` controller run at `learning_agent/acceptance_controller/runs/computer_use_full_paint_pikachu_strict-20260606_074109/result.json`.

Residual risk:
- The drawing is a black-line simple sketch, not a colored artistic illustration.
- Paint canvas location is still estimated from the maximized window layout, so a future Windows Paint UI update could require replacing the heuristic with a real canvas locator.

## 2026-06-06 `/computer use --full` Token UX Mismatch

Status: resolved for the normal interactive path.

Observation:
- The user correctly pointed out that normal users will type `/computer use --full` and then the task prompt, not `/computer use --full-confirm <dynamic-token>`.

Root cause:
- The interactive full-mode command treated `/computer use --full` as a request generator and exposed a dynamic confirmation token as part of the ordinary UX.

Handling:
- `/computer use --full` now directly opens full mode for that explicit command.
- Tests and visible-terminal scenario now reject the token-style flow for the normal Paint/Pikachu acceptance path.

Verification:
- Final real visible terminal acceptance passed at `learning_agent/acceptance_controller/runs/computer_use_full_paint_pikachu_strict-20260606_081706/result.json` with `confirmation_token_count=0` and `full_confirm_count=0`.

## 2026-06-06 Paint Owned Process Cleanup False Positive

Status: resolved for the Paint/Pikachu real loop.

Observation:
- A prior visible-terminal validation could report cleanup success while the specific Paint PID from that run still existed.

Root cause:
- The global stop cleanup and the Paint launch registry were separate in-memory paths, so the launcher-owned `Popen` object was not being used to verify or terminate the actual Paint process.

Handling:
- Added `cleanup_owned_processes()` and `residual_owned_processes()` to `Phase110OwnedProcessRegistry`.
- The Paint/Pikachu real loop now cleans and checks the owned Paint process after screenshot evidence and fails with `paint_pikachu_cleanup_failed` if cleanup is not proven.

Verification:
- Unit test verifies a registered process object is terminated.
- Final real visible terminal acceptance at `learning_agent/acceptance_controller/runs/computer_use_full_paint_pikachu_strict-20260606_081706/result.json` reported `cleaned_process_count=1`, `residual_owned_process=false`, and PID 4536 was not running afterward.
# 2026-06-06 Bug: Elephant Prompt Drew Pikachu In Computer Use Full

- 修改代码+GenericPaintSubject：真实终端截图显示用户输入“请使用本机电脑画图软件画一个大象”后，报告仍为 `paint_pikachu_real_execution_finished`，画布也呈现皮卡丘特征；如果没有这条问题记录，后续容易把此类现象当成视觉误差。
- 修改代码+GenericPaintSubject：源码确认根因是 `paint_pikachu_real_loop.py` 固定调用 `build_pikachu_drag_plan(canvas)`，不是文档、maturity 输出或用户 prompt 格式导致；如果没有这条根因记录，后续会继续误修提示词层。
- 新增代码+GenericPaintSubject：修复方向是引入绘画对象识别和 subject-specific drag plan，目前明确支持 `pikachu` 与 `elephant`；如果没有这条修复记录，后续会误以为已经支持任意绘画对象。
- 新增代码+GenericPaintSubject：未知对象现在应明确拒绝而不是 fallback 到皮卡丘；如果没有这条风险记录，未来扩展时可能再次出现“用户要 A，系统画 B”的成熟度误报。
- 新增代码+GenericPaintSubject：后续若继续加入猫、狗、房子等对象，必须先加失败测试、独立 primitive、真实可见终端验收；如果没有这条经验约束，同类硬编码问题会重复发生。

## 2026-06-06 Computer Use Full Paint Loop Wrong Production Wiring

Resolved risk:
- Symptom: after `/computer use --full`, natural desktop drawing prompts were routed into a Paint/Pikachu-specific execution loop, so prompts such as drawing an elephant still produced Pikachu-style behavior or depended on hardcoded drawing subjects.
- Confirmed root cause: `LearningAgent._desktop_task_runtime_for_current_run()` default-created `WindowsPaintPikachuRealExecutionLoop` and injected it into `ComputerUseDesktopTaskRuntime`; `full_maturity_matrix.py` also treated Paint/Pikachu visible-terminal acceptance as production maturity evidence.
- Fix: the default production runtime no longer injects `WindowsPaintPikachuRealExecutionLoop`; maturity reporting now marks the Paint/Pikachu path as a legacy fixture and does not emit `COMPUTER_USE_FULL_MATURE_OK` while the universal real desktop loop is not connected.
- Regression guard: `test_default_agent_runtime_does_not_inject_paint_specific_loop` now fails if the Paint/Pikachu loop is reintroduced into the default agent runtime.
- Visible-terminal evidence: `computer_use_full_universal_loop_slimming_strict.json` passed through the real `start_oauth_agent.bat` terminal path and confirmed `gui_action_count=0`, `low_level_event_count=0`, and `real_desktop_touched=false` for a normal drawing prompt after full mode.

Remaining risk:
- `/computer use --full` is now honest but not yet mature: the universal observe -> plan -> act -> verify loop still needs to be connected to real desktop execution before arbitrary user drawing/control requests can be fulfilled.
- The old Paint/Pikachu files may remain in the tree as legacy fixtures or historical tests, but they must not be used as the default production path or as proof of universal Computer Use maturity.

---
## 2026-06-06 Computer Use Full Adapter Boundary Risk
- 新增代码+UniversalDesktopAdapter：已确认根因不是缺少更多 Paint/Pikachu/大象特例，而是默认生产路径没有接到通用 computer-use loop；本阶段已接入通用 adapter。
- 新增代码+UniversalDesktopAdapter：当前仍存在明确限制：adapter 使用 recording low-level sender，`real_desktop_touched=false`，所以不能把它宣传成成熟的真实桌面控制能力。
- 新增代码+UniversalDesktopAdapter：后续治本方向必须是把通用 observation、planner、verified target、physical sender、安全 abort、视觉验证闭环逐步接实，而不是继续新增“画某个对象”的固定控制器。

## 2026-06-06 Default Adapter Used Recording Observation
- 修改代码+RealObservationAdapter：红测确认默认 `UniversalDesktopExecutionLoopAdapter` 内部仍是 `Phase119RecordingObservationRuntime`，所以 `/computer use --full` 虽然走通用 adapter，但还没有真实只读屏幕/窗口观察；如果没有这条问题记录，后续可能把 adapter 外壳误判成真实 computer use。
- 修改代码+RealObservationAdapter：根因是 `UniversalDesktopExecutionLoopAdapter.__init__()` 只调用 `UniversalObservePlanActVerifyLoop(max_retries=0)`，没有显式注入 `UniversalRealObservationFrameRuntime`；如果没有这条根因记录，后续可能去错误修改 planner 或终端文案。
- 新增代码+RealObservationAdapter：修复方向是默认注入真实只读 observation runtime，并在报告中单独暴露 `real_observation_runtime_used` 与 `read_only_real_observation_used`；如果没有这条修复记录，后续容易再次把录制 observation 当成真实观察。
- 修改代码+RealObservationAdapter：剩余风险是该修复只补“眼睛”，物理 SendInput 派发仍未启用，不能声明 `/computer use --full` 成熟；如果没有这条风险记录，最终回答或 maturity 输出可能过度承诺。

## 2026-06-06 Controlled Physical Sender Missing Target Identity
- 修改代码+ControlledPhysicalAdapter：红测确认 `UniversalActionDslRuntime(low_level_sender=WindowsControlledPhysicalSendInputSender(...))` 原来会失败，因为 dispatcher 展开的低层事件没有 `target` 字段；如果没有这条问题记录，后续可能误以为 Phase95 本身坏了。
- 修改代码+ControlledPhysicalAdapter：根因是目标身份只在 URG-2/URG-3 动作前复核层存在，进入 `WindowsSendInputDispatcher._expand_event()` 后被丢弃；如果没有这条根因记录，未来真实 SendInput 接线会再次缺少最后一跳目标门禁。
- 新增代码+ControlledPhysicalAdapter：修复方向是 URG-3 在动作通过复核后给 dispatcher 事件附加脱敏 target，Phase47 展开所有低层事件时保留 target；如果没有这条修复记录，Phase95 会继续 `missing_target_identity`。
- 修改代码+ControlledPhysicalAdapter：剩余风险是当前只证明 fake 后端可被触达且默认不触桌面，尚未启用真实 `WindowsSendInputLowLevelSender` 的默认生产物理派发；如果没有这条风险记录，后续 maturity 可能把受控桥接误报成真实控制成熟。

---
## 2026-06-06 Default Full Runtime Reintroduced Paint Special Bridge

Status:
- Fixed in source; visible terminal re-acceptance is being rerun after this record.

Confirmed root cause:
- `learning_agent/core/agent.py` default runtime constructor passed `enable_supported_paint_drawing=True` into `UniversalDesktopExecutionLoopAdapter`, which re-enabled the Paint/Pikachu/animal-specific bridge on the normal `/computer use --full` user path.

Fix:
- Default runtime now constructs `UniversalDesktopExecutionLoopAdapter()` without the supported Paint bridge flag.
- Router regression tests now fail if the default path exposes `supported_paint_drawing_loop`, `supported_paint_drawing_enabled=true`, subject-specific planning, or bridge-used output.

Risk:
- Old direct Paint loop files may remain as legacy fixtures, but they must not be used as proof that `/computer use --full` is universal or mature.

Acceptance evidence:
- Real visible terminal re-acceptance passed at `learning_agent/acceptance_controller/runs/computer_use_full_universal_real_observation_strict-20260606_112108/result.json`.
- The parsed final answer confirmed the default route did not use the Paint/Pikachu special bridge and did not claim subject-specific planning.

---
## 2026-06-06 Computer Use Full Missing Physical Dispatch Connection

Status:
- Source fixed; real visible terminal acceptance pending.

Confirmed root cause:
- `LearningAgent._desktop_task_runtime_for_current_run()` default-created `UniversalDesktopExecutionLoopAdapter()` without a controlled physical sender, so `/computer use --full` could observe and record but not intentionally send real mouse/keyboard through the universal path.
- `UniversalObservePlanActVerifyLoop` did not propagate `real_dispatch_performed` from `UniversalActionDslRuntime.dispatch()`, so a true sender result could still be hidden at the top-level loop report.
- `UniversalActionDslRuntime` counted events only by comparing `low_level_sender.low_level_events`, which works for recording senders but returns zero for real/controlled senders that report event count in their result.

Fix:
- Default full-mode runtime now constructs `WindowsSendInputLowLevelSender`, wraps it in `WindowsControlledPhysicalSendInputSender(default_enable_physical_dispatch=True)`, and injects that sender into `UniversalDesktopExecutionLoopAdapter`.
- The loop now updates `self.real_dispatch_performed` from dispatch result fields and the action runtime state.
- The action DSL now uses sender-reported `low_level_event_count` when present.

Remaining risk:
- Real physical dispatch alone is not equivalent to mature arbitrary Computer Use.
- The universal route still needs robust real app launch/activation, natural-language visual planning, and observation-based correction before it can honestly satisfy requests like “draw any image with colors” in Paint.

Follow-up correction:
- User confirmed the Paint window in the real physical dispatch screenshot was opened by the user, not by the agent.
- Therefore `computer_use_full_universal_real_physical_dispatch_strict-20260606_114300` is not valid evidence for "agent opened Paint and drew a line"; it only proves physical dispatch against an already visible Paint window.
- Future acceptance must explicitly prove agent-owned launch/window ownership before physical drawing actions, otherwise the validation can repeat the same false positive.

---
## 2026-06-06 Universal Target Session Fabricated App Launch

Status:
- Fixed for the full-mode default path and verified by real visible terminal acceptance.

Confirmed root cause:
- `learning_agent/computer_use/universal_target_session.py` created fake `process_id`, fake `hwnd`, and a fake `Universal Target Session` window instead of calling the production generic launch backend.
- `UniversalDesktopExecutionLoopAdapter` consumed that fake session, so previous physical dispatch could target a user-opened Paint window and still look superficially successful.

Fix:
- The real-launch mode now calls Phase110 production generic launch, waits for a visible window with the launched pid, and only marks the session ready when process ownership and window identity both verify.
- The short desktop task token line now exposes `real_launch_performed`, `backend_launch_performed`, `process_started`, `owned_process_registered`, and `visible_window_verified`.
- New strict visible-terminal scenario requires all of those launch fields before it can pass.

Acceptance evidence:
- `learning_agent/acceptance_controller/runs/computer_use_full_agent_owned_paint_launch_line_strict-20260606_120309/result.json` passed with `process_id=23472`, `window_id=hwnd:397860`, `real_launch_performed=true`, and `visible_window_verified=true`.

Remaining risk:
- The current planner still emits a fixed generic stroke; this is not arbitrary drawing maturity.

---
## 2026-06-06 Agent-Owned Paint Cleanup Residual Mismatch

Status:
- Open follow-up risk.

Observed evidence:
- After the successful strict launch acceptance, `Get-Process -Id 23472` still showed `mspaint.exe`.
- The `/computer stop` output in the same run reported `owned_resource_cleanup_completed=true` and `residual_owned_process=false`.

Risk:
- Cleanup and residual reporting are not yet reliably tied to the Phase110 production launch registry used inside the universal target session.
- This does not invalidate the agent-owned launch proof, but it means `/computer stop` cleanup evidence is currently over-optimistic for launched GUI apps.

Suggested fix direction:
- Persist or pass the owned launch registry from the real target session into `/computer stop` cleanup.
- Add a visible-terminal cleanup scenario that verifies the launched pid is gone or explicitly reports a residual process.

---
## 2026-06-06 Visual Planner Semantic Drawing Gap

Status:
- Open product/architecture gap, not solved by this phase.

Confirmed evidence:
- Visible-terminal run `computer_use_full_visual_planner_paint_house_strict-20260606_123238` used the real full-mode route, launched Paint, connected the visual planner, and sent low-level mouse events.
- The final screenshot `learning_agent/memory/computer_use/evidence/computer-window-20260606T043252Z-8d291c7f.bmp` shows central canvas strokes, but the output is a generic geometric face rather than the requested house.

Risk:
- If maturity only checks `visual_planner_connected=true` and `real_desktop_touched=true`, the project may again overclaim arbitrary drawing maturity.
- The maturity matrix must continue reporting `visual_planner_mature=false` until the planner can derive task-specific visual plans and correct them from screenshots.

Suggested fix direction:
- Replace the current heuristic visual planner with a task-aware planner that converts user intent into editable drawing primitives, observes the screen after each batch, and replans until a verifier agrees the requested subject and requested operations are visible.
- Keep Paint/Pikachu/elephant/house special cases out of the default `/computer use --full` path; those hardcoded routes caused the original design failure.

---
## 2026-06-06 Visual Planner Semantic Drawing Gap Update

Status:
- Partially fixed for house; still open for arbitrary subjects and correction.

Fixed evidence:
- The prior failure mode “房子 prompt 画成通用几何脸” is fixed for the strict house scenario.
- Visible-terminal run `computer_use_full_visual_planner_paint_house_strict-20260606_124945` required and found `house_roof`、`house_body`、`house_door`、`house_window_left`、`house_window_right` in the real loop evidence.
- Screenshot `computer-window-20260606T044959Z-83e975e8.bmp` visually shows a house rather than a generic face.

Remaining risk:
- Unknown subjects still fall back to generic geometry.
- There is still no mature screenshot verifier that can say “this image semantically matches the prompt” and replan until it does.
- Color/tool selection and multi-step correction are not yet mature.
## 2026-06-06 修复：Computer Use full 语义规划被 run_prompt 黑盒 runtime 抢跑

- 问题：`computer_use(operation=run_prompt, real_actions=true)` 会把整段自然语言 prompt 交给 Python desktop runtime 执行，导致模型主循环没有真正承担语义理解、观察、纠偏和工具选择职责。
- 证据：新增红灯测试显示 system prompt 缺少 Computer Use full harness，且注入会爆炸的 `desktop_task_runtime.run_prompt()` 后，旧实现确实调用了该黑盒 runtime。
- 根因：兼容工具面把 `mode/run_prompt` 当成模型可见能力暴露，并在 `_computer_use_mode()` 的 `real_actions` 分支直接调用 full desktop runtime。
- 修复：模型可见 schema 收窄到 `status/observe/action`；`run_prompt` 真实动作分支改为返回 `model_loop_observe_action_required`；full 模式自然语言桌面任务加入模型主循环 harness。
- 剩余风险：这次修复的是“语义规划归位”的顶层结构，不代表真实可见 Paint 画树验收已经完成；后续仍需在真实终端里验证模型能通过观察、动作、纠偏完成完整桌面任务。

---
## 2026-06-06 Bug 状态：Computer Use 截图只作为文本路径进入模型

Root cause:
- `LearningAgent` 原先只把 Computer Use 工具输出作为普通 tool result 文本放回 messages，截图 artifact 只是路径文字。
- `CodexOAuthChatModel` 原先又把整个 messages JSON 压成一个 `input_text` prompt，因此即使上游出现图片块，也不会作为视觉输入发给模型。

Fix:
- 工具结果回灌层新增 Computer Use 图片 artifact -> `image_url` 消息。
- OAuth/Responses 适配层新增 `image_url` -> `input_image` 转换，并清洗文本 prompt 里的 base64。

Remaining risk:
- 真实可见终端验收尚未完成，因此还不能说 `/computer use --full` 端到端成熟。

---
## 2026-06-06 修复：Computer Use BMP 截图被 Responses API 拒绝

Root cause:
- 真实可见 controller 场景中，Windows observe 生成的截图 artifact 是 BMP。
- `LearningAgent` 之前把 BMP 原样转成 `data:image/bmp;base64,...`。
- OAuth/Responses 适配层会把该 data URL 作为 `input_image` 发给模型，而 Responses API 不支持 BMP。

Fix:
- `LearningAgent` 新增模型图片载荷入口，源图是 BMP 时先用 Pillow 转成 PNG。
- 新增回归测试确认 data URL 是 `image/png`，且解码后是真 PNG 文件头，不是简单改 MIME。

Verification:
- 新增测试先失败后通过。
- `python -m unittest learning_agent.tests.test_models_codex_oauth learning_agent.tests.test_windows_computer_use_image_results_phase41` 通过，54 tests OK。
- `python -m py_compile learning_agent\core\agent.py learning_agent\models\adapters.py learning_agent\tests\test_windows_computer_use_image_results_phase41.py learning_agent\tests\test_models_codex_oauth.py` 通过。

Remaining risk:
- 需要重新跑真实可见终端 controller 画树场景，确认模型不再因为 BMP 输入失败，并继续观察下一层真实桌面执行问题。

---
## 2026-06-06 修复：Codex OAuth SSE 心跳流导致真实终端卡住

Root cause:
- controller 真实画树场景停在“模型调用：第 0 轮”，没有进入工具调用，也没有最终回答。
- `CodexOAuthChatModel._read_sse_response_until_done()` 只在 `[DONE]`、`response.output_text.done` 或 `response.completed` 时退出。
- 如果后端持续发送心跳、空行或未知事件，socket read timeout 不一定触发，总循环没有全局 deadline。

Fix:
- `CodexOAuthChatModel` 新增 SSE 总读取超时，默认 240 秒。
- `from_env()` 新增 `CODEX_OAUTH_SSE_READ_TIMEOUT_SECONDS` 配置。
- SSE 读取循环在每次读取下一行前检查总 deadline，并抛出可被中文 OAuth timeout 文案识别的 `TimeoutError`。

Verification:
- 新增心跳流测试先失败后通过。
- `python -m unittest learning_agent.tests.test_models_codex_oauth learning_agent.tests.test_windows_computer_use_image_results_phase41` 通过，55 tests OK。
- `python -m py_compile learning_agent\core\agent.py learning_agent\models\adapters.py learning_agent\tests\test_windows_computer_use_image_results_phase41.py learning_agent\tests\test_models_codex_oauth.py` 通过。

Remaining risk:
- 需要重新跑真实可见终端 controller 场景，确认模型返回后是否会实际调用 `computer_observe`/`computer_action`。
