"""Windows Computer Use Phase53 ClaudeCode 对齐差距矩阵。"""  # 新增代码+Phase53ParityGapMatrix: 标明本文件负责把 ClaudeCode 源码差距固化成可验收矩阵；如果没有这行代码，读者不知道 Phase53 的总入口在哪里。
from __future__ import annotations  # 新增代码+Phase53ParityGapMatrix: 启用延迟类型解析；如果没有这行代码，旧运行路径遇到前向类型标注时更容易导入失败。

import json  # 新增代码+Phase53ParityGapMatrix: 导入 JSON 工具用于 CLI 打印结构化报告；如果没有这行代码，失败时不容易复盘具体差距项。
from typing import Any  # 新增代码+Phase53ParityGapMatrix: 导入 Any 描述矩阵中的通用字段；如果没有这行代码，函数边界缺少清楚的类型提示。

PHASE53_PARITY_GAP_MATRIX_MARKER = "PHASE53_PARITY_GAP_MATRIX_READY"  # 新增代码+Phase53ParityGapMatrix: 定义 Phase53 ready marker；如果没有这行代码，真实终端验收无法稳定等待本阶段输出。
PHASE53_PARITY_GAP_MATRIX_OK_TOKEN = "PHASE53_PARITY_GAP_MATRIX_OK"  # 新增代码+Phase53ParityGapMatrix: 定义 Phase53 OK token；如果没有这行代码，日志无法区分差距矩阵通过和普通文本。
PHASE53_PARITY_GAP_MATRIX_MODEL = "phase53_parity_gap_matrix"  # 新增代码+Phase53ParityGapMatrix: 定义矩阵模型名；如果没有这行代码，报告无法说明当前使用哪套差距合同。
PHASE53_ACTIONS_EXPANDED = False  # 新增代码+Phase53ParityGapMatrix: 明确 Phase53 不扩大真实桌面动作面；如果没有这行代码，用户可能误以为差距矩阵会直接控制电脑。
PHASE53_EXPECTED_GAP_COUNT = 12  # 新增代码+Phase53ParityGapMatrix: 固定 Phase53-64 十二个差距项；如果没有这行代码，漏掉阶段也可能被误判为完整。
PHASE53_REQUIRED_ITEM_FIELDS = {"id", "claudecode_capability", "learning_agent_current", "owner_phase", "claudecode_source", "real_provider_required", "acceptance_type", "status", "exceeds_claudecode_when_done"}  # 新增代码+Phase53ParityGapMatrix: 定义每个差距项必须具备的字段；如果没有这行代码，矩阵字段可能漂移且难以验收。

PHASE53_GAP_ITEMS: tuple[dict[str, Any], ...] = (  # 新增代码+Phase53ParityGapMatrix: 函数外常量段开始，列出 Phase53-64 每个差距项；如果没有这段数据，后续阶段没有稳定蓝图来源。
    {  # 新增代码+Phase53ParityGapMatrix: Phase53 差距项开始；如果没有这行代码，本阶段无法锁定非伪验收合同。
        "id": "phase53_non_fake_acceptance_contract",  # 新增代码+Phase53ParityGapMatrix: 给 Phase53 差距项一个稳定 id；如果没有这行代码，验收和文档无法引用本项。
        "claudecode_capability": "源码级差距矩阵、真实能力边界和验收合同。",  # 新增代码+Phase53ParityGapMatrix: 记录 ClaudeCode 成熟点；如果没有这行代码，用户看不到本阶段对齐对象。
        "learning_agent_current": "已有 Phase43-52 矩阵，但还需要把剩余 20% 差距逐项锁死。",  # 新增代码+Phase53ParityGapMatrix: 记录 learning_agent 当前状态；如果没有这行代码，差距来源不清楚。
        "owner_phase": 53,  # 新增代码+Phase53ParityGapMatrix: 指定本项由 Phase53 负责；如果没有这行代码，阶段归属会模糊。
        "claudecode_source": "D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse/executor.ts and hooks in utils/computerUse",  # 新增代码+Phase53ParityGapMatrix: 记录源码证据范围；如果没有这行代码，矩阵会像主观判断。
        "real_provider_required": False,  # 新增代码+Phase53ParityGapMatrix: 表示本项是合同锁定而不是原生 provider；如果没有这行代码，测试无法区分文档门禁和真实能力。
        "acceptance_type": "contract_plus_visible_terminal",  # 新增代码+Phase53ParityGapMatrix: 说明本项要靠合同和可见终端验收；如果没有这行代码，验收方式不明确。
        "status": "implemented_by_phase53",  # 新增代码+Phase53ParityGapMatrix: 标记本项由当前阶段实现；如果没有这行代码，报告无法显示进度。
        "exceeds_claudecode_when_done": True,  # 新增代码+Phase53ParityGapMatrix: 标记完成后会因 Windows 对齐和外部 controller 超越 ClaudeCode；如果没有这行代码，超越目标不可见。
    },  # 新增代码+Phase53ParityGapMatrix: Phase53 差距项结束；如果没有这行代码，Python 数据结构无法闭合。
    {  # 新增代码+Phase53ParityGapMatrix: Phase54 差距项开始；如果没有这行代码，依赖门禁不会进入蓝图。
        "id": "phase54_windows_dependency_reality_gate",  # 新增代码+Phase53ParityGapMatrix: 给 Phase54 差距项一个稳定 id；如果没有这行代码，依赖门禁无法被跟踪。
        "claudecode_capability": "启动前检查系统依赖、权限和运行环境，失败时给出真实原因。",  # 新增代码+Phase53ParityGapMatrix: 记录 ClaudeCode 的环境门禁能力；如果没有这行代码，对齐目标不清楚。
        "learning_agent_current": "已有 Phase43 native capability matrix，但缺少更细的 Windows 依赖和权限现实门禁。",  # 新增代码+Phase53ParityGapMatrix: 记录当前差距；如果没有这行代码，后续补强点会模糊。
        "owner_phase": 54,  # 新增代码+Phase53ParityGapMatrix: 指定本项由 Phase54 负责；如果没有这行代码，阶段分配会丢失。
        "claudecode_source": "D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse/executor.ts platform checks",  # 新增代码+Phase53ParityGapMatrix: 记录源码证据；如果没有这行代码，依赖门禁比较没有来源。
        "real_provider_required": True,  # 新增代码+Phase53ParityGapMatrix: 表示本项必须检查真实 Windows 依赖；如果没有这行代码，fake 环境可能误过。
        "acceptance_type": "real_diagnostics_or_blocked_with_reason",  # 新增代码+Phase53ParityGapMatrix: 说明缺依赖时要诚实阻断并给原因；如果没有这行代码，失败可能被伪装成成功。
        "status": "planned_phase54",  # 新增代码+Phase53ParityGapMatrix: 标记本项等待 Phase54 实现；如果没有这行代码，进度不可见。
        "exceeds_claudecode_when_done": True,  # 新增代码+Phase53ParityGapMatrix: 标记 Windows 依赖门禁完成后会覆盖 ClaudeCode 的 macOS 单平台边界；如果没有这行代码，超越目标不明确。
    },  # 新增代码+Phase53ParityGapMatrix: Phase54 差距项结束；如果没有这行代码，Python 数据结构无法闭合。
    {  # 新增代码+Phase53ParityGapMatrix: Phase55 差距项开始；如果没有这行代码，native helper v2 不会进入蓝图。
        "id": "phase55_out_of_process_native_helper_v2",  # 新增代码+Phase53ParityGapMatrix: 给 Phase55 差距项一个稳定 id；如果没有这行代码，helper v2 无法被跟踪。
        "claudecode_capability": "MCP 侧 out-of-process worker 隔离桌面控制、会话上下文和清理生命周期。",  # 新增代码+Phase53ParityGapMatrix: 记录 ClaudeCode native helper 成熟点；如果没有这行代码，helper 对齐对象不清楚。
        "learning_agent_current": "已有 native_host 合同，但需要更强的进程边界、心跳、协议版本和崩溃恢复。",  # 新增代码+Phase53ParityGapMatrix: 记录当前 helper 差距；如果没有这行代码，Phase55 容易只补文档。
        "owner_phase": 55,  # 新增代码+Phase53ParityGapMatrix: 指定本项由 Phase55 负责；如果没有这行代码，阶段分配会丢失。
        "claudecode_source": "D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse/executor.ts bindSessionContext/native MCP lifecycle",  # 新增代码+Phase53ParityGapMatrix: 记录源码证据；如果没有这行代码，helper 生命周期对齐没有依据。
        "real_provider_required": True,  # 新增代码+Phase53ParityGapMatrix: 表示本项必须能驱动真实 helper 进程或诚实说明不可用；如果没有这行代码，内存 mock 可能误过。
        "acceptance_type": "out_of_process_helper_smoke_or_blocked_with_reason",  # 新增代码+Phase53ParityGapMatrix: 说明验收方式；如果没有这行代码，helper 是否真的跨进程不可验证。
        "status": "planned_phase55",  # 新增代码+Phase53ParityGapMatrix: 标记本项等待 Phase55 实现；如果没有这行代码，进度不可见。
        "exceeds_claudecode_when_done": True,  # 新增代码+Phase53ParityGapMatrix: 标记完成后会成为 Windows 版可接管 helper；如果没有这行代码，超越目标不明确。
    },  # 新增代码+Phase53ParityGapMatrix: Phase55 差距项结束；如果没有这行代码，Python 数据结构无法闭合。
    {  # 新增代码+Phase53ParityGapMatrix: Phase56 差距项开始；如果没有这行代码，真实截图流水线不会进入蓝图。
        "id": "phase56_real_screenshot_pixel_guard",  # 新增代码+Phase53ParityGapMatrix: 给 Phase56 差距项一个稳定 id；如果没有这行代码，截图守卫无法被跟踪。
        "claudecode_capability": "截图不是假字节，而是带像素检查、窗口目标和 artifact 的真实观察。",  # 新增代码+Phase53ParityGapMatrix: 记录 ClaudeCode 截图成熟点；如果没有这行代码，截图质量要求不清楚。
        "learning_agent_current": "已有 screenshot_runtime 合同和 artifact，但仍需要更硬的非空像素守卫与真实 provider 选择。",  # 新增代码+Phase53ParityGapMatrix: 记录当前截图差距；如果没有这行代码，Phase56 容易只判断文件存在。
        "owner_phase": 56,  # 新增代码+Phase53ParityGapMatrix: 指定本项由 Phase56 负责；如果没有这行代码，阶段分配会丢失。
        "claudecode_source": "D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse/executor.ts screenshot/getWindowState flow",  # 新增代码+Phase53ParityGapMatrix: 记录源码证据；如果没有这行代码，截图对齐没有来源。
        "real_provider_required": True,  # 新增代码+Phase53ParityGapMatrix: 表示本项必须验证真实截图 provider 或明确阻断；如果没有这行代码，空 PNG 可能误过。
        "acceptance_type": "real_screenshot_pixel_smoke_or_blocked_with_reason",  # 新增代码+Phase53ParityGapMatrix: 说明验收方式；如果没有这行代码，真实截图和占位图无法区分。
        "status": "planned_phase56",  # 新增代码+Phase53ParityGapMatrix: 标记本项等待 Phase56 实现；如果没有这行代码，进度不可见。
        "exceeds_claudecode_when_done": True,  # 新增代码+Phase53ParityGapMatrix: 标记完成后会增加 Windows 像素守卫；如果没有这行代码，超越点不可见。
    },  # 新增代码+Phase53ParityGapMatrix: Phase56 差距项结束；如果没有这行代码，Python 数据结构无法闭合。
    {  # 新增代码+Phase53ParityGapMatrix: Phase57 差距项开始；如果没有这行代码，UIA 语义定位不会进入蓝图。
        "id": "phase57_real_uia_semantic_locator",  # 新增代码+Phase53ParityGapMatrix: 给 Phase57 差距项一个稳定 id；如果没有这行代码，UIA 定位能力无法被跟踪。
        "claudecode_capability": "通过 accessibility tree 找到控件、焦点、文本和可操作区域。",  # 新增代码+Phase53ParityGapMatrix: 记录 ClaudeCode 控件树成熟点；如果没有这行代码，UIA 对齐目标不清楚。
        "learning_agent_current": "已有 UIA tree 合同和文本脱敏，但需要真实 UIA 控件树、语义 locator 和坐标映射。",  # 新增代码+Phase53ParityGapMatrix: 记录当前 UIA 差距；如果没有这行代码，Phase57 容易停留在静态树。
        "owner_phase": 57,  # 新增代码+Phase53ParityGapMatrix: 指定本项由 Phase57 负责；如果没有这行代码，阶段分配会丢失。
        "claudecode_source": "D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse executor observation/accessibility callbacks",  # 新增代码+Phase53ParityGapMatrix: 记录源码证据；如果没有这行代码，控件树对齐没有来源。
        "real_provider_required": True,  # 新增代码+Phase53ParityGapMatrix: 表示本项必须验证真实 UIA provider 或明确阻断；如果没有这行代码，静态控件树可能误过。
        "acceptance_type": "real_uia_locator_smoke_or_blocked_with_reason",  # 新增代码+Phase53ParityGapMatrix: 说明验收方式；如果没有这行代码，语义定位是否真实不可验证。
        "status": "planned_phase57",  # 新增代码+Phase53ParityGapMatrix: 标记本项等待 Phase57 实现；如果没有这行代码，进度不可见。
        "exceeds_claudecode_when_done": True,  # 新增代码+Phase53ParityGapMatrix: 标记完成后会具备 Windows UIA 专项语义定位；如果没有这行代码，超越点不可见。
    },  # 新增代码+Phase53ParityGapMatrix: Phase57 差距项结束；如果没有这行代码，Python 数据结构无法闭合。
    {  # 新增代码+Phase53ParityGapMatrix: Phase58 差距项开始；如果没有这行代码，真实输入守卫不会进入蓝图。
        "id": "phase58_real_sendinput_target_guard",  # 新增代码+Phase53ParityGapMatrix: 给 Phase58 差距项一个稳定 id；如果没有这行代码，SendInput 守卫无法被跟踪。
        "claudecode_capability": "动作前确认目标窗口、审批、锁和 abort 状态，避免把输入打到错误应用。",  # 新增代码+Phase53ParityGapMatrix: 记录 ClaudeCode 动作守卫成熟点；如果没有这行代码，动作安全目标不清楚。
        "learning_agent_current": "已有 SendInput dispatcher 和 target_check 合同，但需要更接近真实 Windows 前台目标守卫。",  # 新增代码+Phase53ParityGapMatrix: 记录当前动作差距；如果没有这行代码，Phase58 容易只验证 recording sender。
        "owner_phase": 58,  # 新增代码+Phase53ParityGapMatrix: 指定本项由 Phase58 负责；如果没有这行代码，阶段分配会丢失。
        "claudecode_source": "D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse/executor.ts approval/action execution path",  # 新增代码+Phase53ParityGapMatrix: 记录源码证据；如果没有这行代码，动作门禁对齐没有来源。
        "real_provider_required": True,  # 新增代码+Phase53ParityGapMatrix: 表示本项必须在安全窗口验证真实输入或明确阻断；如果没有这行代码，recording sender 可能误过。
        "acceptance_type": "safe_window_sendinput_smoke_or_blocked_with_reason",  # 新增代码+Phase53ParityGapMatrix: 说明验收方式；如果没有这行代码，动作是否真实不可验证。
        "status": "planned_phase58",  # 新增代码+Phase53ParityGapMatrix: 标记本项等待 Phase58 实现；如果没有这行代码，进度不可见。
        "exceeds_claudecode_when_done": True,  # 新增代码+Phase53ParityGapMatrix: 标记完成后会具备 Windows 前台目标守卫；如果没有这行代码，超越点不可见。
    },  # 新增代码+Phase53ParityGapMatrix: Phase58 差距项结束；如果没有这行代码，Python 数据结构无法闭合。
    {  # 新增代码+Phase53ParityGapMatrix: Phase59 差距项开始；如果没有这行代码，会话上下文不会进入蓝图。
        "id": "phase59_session_context_appstate",  # 新增代码+Phase53ParityGapMatrix: 给 Phase59 差距项一个稳定 id；如果没有这行代码，session context 无法被跟踪。
        "claudecode_capability": "bindSessionContext、AppState 回调、当前 app 和窗口状态同步。",  # 新增代码+Phase53ParityGapMatrix: 记录 ClaudeCode 会话能力；如果没有这行代码，AppState 对齐目标不清楚。
        "learning_agent_current": "已有 session_runtime、journal 和 status UI，但缺少 ClaudeCode 风格 AppState 事件合同。",  # 新增代码+Phase53ParityGapMatrix: 记录当前会话差距；如果没有这行代码，Phase59 容易只扩展日志。
        "owner_phase": 59,  # 新增代码+Phase53ParityGapMatrix: 指定本项由 Phase59 负责；如果没有这行代码，阶段分配会丢失。
        "claudecode_source": "D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse/executor.ts bindSessionContext callbacks",  # 新增代码+Phase53ParityGapMatrix: 记录源码证据；如果没有这行代码，会话上下文对齐没有来源。
        "real_provider_required": False,  # 新增代码+Phase53ParityGapMatrix: 表示本项主要是状态合同和事件模型；如果没有这行代码，验收会误要求真实点击。
        "acceptance_type": "session_state_contract_plus_visible_terminal",  # 新增代码+Phase53ParityGapMatrix: 说明验收方式；如果没有这行代码，AppState 是否进入终端不可验证。
        "status": "planned_phase59",  # 新增代码+Phase53ParityGapMatrix: 标记本项等待 Phase59 实现；如果没有这行代码，进度不可见。
        "exceeds_claudecode_when_done": True,  # 新增代码+Phase53ParityGapMatrix: 标记完成后会保留 Windows 外部 controller 友好状态；如果没有这行代码，超越点不可见。
    },  # 新增代码+Phase53ParityGapMatrix: Phase59 差距项结束；如果没有这行代码，Python 数据结构无法闭合。
    {  # 新增代码+Phase53ParityGapMatrix: Phase60 差距项开始；如果没有这行代码，审批持久授权不会进入蓝图。
        "id": "phase60_approval_ux_persistent_grants",  # 新增代码+Phase53ParityGapMatrix: 给 Phase60 差距项一个稳定 id；如果没有这行代码，审批 UX 无法被跟踪。
        "claudecode_capability": "用户审批、allowlist、动作风险分类和会话级授权。",  # 新增代码+Phase53ParityGapMatrix: 记录 ClaudeCode 审批能力；如果没有这行代码，授权对齐目标不清楚。
        "learning_agent_current": "已有 approval model、安全策略和 terminal grants 草案，但需要持久授权、撤销和过期合同。",  # 新增代码+Phase53ParityGapMatrix: 记录当前审批差距；如果没有这行代码，Phase60 容易只改显示文本。
        "owner_phase": 60,  # 新增代码+Phase53ParityGapMatrix: 指定本项由 Phase60 负责；如果没有这行代码，阶段分配会丢失。
        "claudecode_source": "D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse approval/request flow",  # 新增代码+Phase53ParityGapMatrix: 记录源码证据；如果没有这行代码，审批比较没有来源。
        "real_provider_required": False,  # 新增代码+Phase53ParityGapMatrix: 表示本项主要是授权数据和 UX 合同；如果没有这行代码，验收会误要求真实输入。
        "acceptance_type": "approval_contract_plus_visible_terminal",  # 新增代码+Phase53ParityGapMatrix: 说明验收方式；如果没有这行代码，授权是否可见不可验证。
        "status": "planned_phase60",  # 新增代码+Phase53ParityGapMatrix: 标记本项等待 Phase60 实现；如果没有这行代码，进度不可见。
        "exceeds_claudecode_when_done": True,  # 新增代码+Phase53ParityGapMatrix: 标记完成后会有 Windows 持久授权与撤销；如果没有这行代码，超越点不可见。
    },  # 新增代码+Phase53ParityGapMatrix: Phase60 差距项结束；如果没有这行代码，Python 数据结构无法闭合。
    {  # 新增代码+Phase53ParityGapMatrix: Phase61 差距项开始；如果没有这行代码，急停清理 streaming hooks 不会进入蓝图。
        "id": "phase61_abort_hotkey_cleanup_streaming_hooks",  # 新增代码+Phase53ParityGapMatrix: 给 Phase61 差距项一个稳定 id；如果没有这行代码，急停清理能力无法被跟踪。
        "claudecode_capability": "Escape 热键、abort、清理、通知和 streaming 状态钩子。",  # 新增代码+Phase53ParityGapMatrix: 记录 ClaudeCode 生命周期能力；如果没有这行代码，急停对齐目标不清楚。
        "learning_agent_current": "已有 abort/cleanup/journal，但需要热键式全局中断、清理闭环和 streaming hook。",  # 新增代码+Phase53ParityGapMatrix: 记录当前生命周期差距；如果没有这行代码，Phase61 容易只复用旧 abort。
        "owner_phase": 61,  # 新增代码+Phase53ParityGapMatrix: 指定本项由 Phase61 负责；如果没有这行代码，阶段分配会丢失。
        "claudecode_source": "D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse/executor.ts escape hotkey cleanup notification hooks",  # 新增代码+Phase53ParityGapMatrix: 记录源码证据；如果没有这行代码，热键清理对齐没有来源。
        "real_provider_required": True,  # 新增代码+Phase53ParityGapMatrix: 表示本项至少要验证真实可见终端和 OS 钩子诊断；如果没有这行代码，纯内存 abort 可能误过。
        "acceptance_type": "visible_abort_cleanup_smoke_or_blocked_with_reason",  # 新增代码+Phase53ParityGapMatrix: 说明验收方式；如果没有这行代码，全局中断是否真实不可验证。
        "status": "planned_phase61",  # 新增代码+Phase53ParityGapMatrix: 标记本项等待 Phase61 实现；如果没有这行代码，进度不可见。
        "exceeds_claudecode_when_done": True,  # 新增代码+Phase53ParityGapMatrix: 标记完成后会保留 controller 可观测 streaming hooks；如果没有这行代码，超越点不可见。
    },  # 新增代码+Phase53ParityGapMatrix: Phase61 差距项结束；如果没有这行代码，Python 数据结构无法闭合。
    {  # 新增代码+Phase53ParityGapMatrix: Phase62 差距项开始；如果没有这行代码，高层 API 不会进入蓝图。
        "id": "phase62_high_level_computer_tool_api_streaming",  # 新增代码+Phase53ParityGapMatrix: 给 Phase62 差距项一个稳定 id；如果没有这行代码，高层工具 API 无法被跟踪。
        "claudecode_capability": "模型可调用的高层 browser/computer 工具、工具执行状态和结果汇流。",  # 新增代码+Phase53ParityGapMatrix: 记录 ClaudeCode 高层工具能力；如果没有这行代码，工具面目标不清楚。
        "learning_agent_current": "已有 tool_surface 兼容入口，但需要更统一的高层 Computer Tool API 和 streaming executor 集成。",  # 新增代码+Phase53ParityGapMatrix: 记录当前工具面差距；如果没有这行代码，Phase62 容易只加别名。
        "owner_phase": 62,  # 新增代码+Phase53ParityGapMatrix: 指定本项由 Phase62 负责；如果没有这行代码，阶段分配会丢失。
        "claudecode_source": "D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse tool executor integration",  # 新增代码+Phase53ParityGapMatrix: 记录源码证据；如果没有这行代码，高层 API 对齐没有来源。
        "real_provider_required": False,  # 新增代码+Phase53ParityGapMatrix: 表示本项主要是 API 和 streaming 合同；如果没有这行代码，验收会误要求真实点击。
        "acceptance_type": "tool_api_contract_plus_streaming_trace",  # 新增代码+Phase53ParityGapMatrix: 说明验收方式；如果没有这行代码，API 是否汇流不可验证。
        "status": "planned_phase62",  # 新增代码+Phase53ParityGapMatrix: 标记本项等待 Phase62 实现；如果没有这行代码，进度不可见。
        "exceeds_claudecode_when_done": True,  # 新增代码+Phase53ParityGapMatrix: 标记完成后会为 Windows 和外部 agent 同时提供接口；如果没有这行代码，超越点不可见。
    },  # 新增代码+Phase53ParityGapMatrix: Phase62 差距项结束；如果没有这行代码，Python 数据结构无法闭合。
    {  # 新增代码+Phase53ParityGapMatrix: Phase63 差距项开始；如果没有这行代码，外部 controller 接管不会进入蓝图。
        "id": "phase63_external_agent_controller_takeover_debug_surface",  # 新增代码+Phase53ParityGapMatrix: 给 Phase63 差距项一个稳定 id；如果没有这行代码，controller 接管能力无法被跟踪。
        "claudecode_capability": "会话可被外部调试、观察和接管，便于真实 prompt 端到端验证。",  # 新增代码+Phase53ParityGapMatrix: 记录 ClaudeCode 可调试性成熟点；如果没有这行代码，接管目标不清楚。
        "learning_agent_current": "已有 acceptance_controller 和命令桥雏形，但需要 computer-use 专属 takeover/debug surface。",  # 新增代码+Phase53ParityGapMatrix: 记录当前接管差距；如果没有这行代码，Phase63 容易只依赖旧验收器。
        "owner_phase": 63,  # 新增代码+Phase53ParityGapMatrix: 指定本项由 Phase63 负责；如果没有这行代码，阶段分配会丢失。
        "claudecode_source": "D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse session/controller integration",  # 新增代码+Phase53ParityGapMatrix: 记录源码证据；如果没有这行代码，外部接管对齐没有来源。
        "real_provider_required": False,  # 新增代码+Phase53ParityGapMatrix: 表示本项主要是调试接口和验收控制面；如果没有这行代码，验收会误要求真实输入动作。
        "acceptance_type": "controller_takeover_contract_plus_visible_terminal",  # 新增代码+Phase53ParityGapMatrix: 说明验收方式；如果没有这行代码，外部 agent 是否能接管不可验证。
        "status": "planned_phase63",  # 新增代码+Phase53ParityGapMatrix: 标记本项等待 Phase63 实现；如果没有这行代码，进度不可见。
        "exceeds_claudecode_when_done": True,  # 新增代码+Phase53ParityGapMatrix: 标记完成后会更适合 Codex 等 agent 控制调试；如果没有这行代码，超越点不可见。
    },  # 新增代码+Phase53ParityGapMatrix: Phase63 差距项结束；如果没有这行代码，Python 数据结构无法闭合。
    {  # 新增代码+Phase53ParityGapMatrix: Phase64 差距项开始；如果没有这行代码，最终总矩阵不会进入蓝图。
        "id": "phase64_final_parity_plus_production_matrix",  # 新增代码+Phase53ParityGapMatrix: 给 Phase64 差距项一个稳定 id；如果没有这行代码，最终矩阵无法被跟踪。
        "claudecode_capability": "最终生产矩阵汇总所有能力、失败原因和真实终端证据。",  # 新增代码+Phase53ParityGapMatrix: 记录 ClaudeCode 最终门禁能力；如果没有这行代码，收尾标准不清楚。
        "learning_agent_current": "已有 Phase52 总矩阵，但需要覆盖 Phase53-63，并明确是否达到或超越 ClaudeCode。",  # 新增代码+Phase53ParityGapMatrix: 记录当前总矩阵差距；如果没有这行代码，Phase64 容易只重复 Phase52。
        "owner_phase": 64,  # 新增代码+Phase53ParityGapMatrix: 指定本项由 Phase64 负责；如果没有这行代码，阶段分配会丢失。
        "claudecode_source": "D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse full source review",  # 新增代码+Phase53ParityGapMatrix: 记录源码证据；如果没有这行代码，最终对齐结论没有来源。
        "real_provider_required": True,  # 新增代码+Phase53ParityGapMatrix: 表示最终矩阵必须汇总真实 provider 状态或明确阻断；如果没有这行代码，最终报告可能假装 100%。
        "acceptance_type": "phase53_to_63_matrix_plus_visible_terminal_and_real_provider_summary",  # 新增代码+Phase53ParityGapMatrix: 说明验收方式；如果没有这行代码，最终生产矩阵边界不清楚。
        "status": "planned_phase64",  # 新增代码+Phase53ParityGapMatrix: 标记本项等待 Phase64 实现；如果没有这行代码，进度不可见。
        "exceeds_claudecode_when_done": True,  # 新增代码+Phase53ParityGapMatrix: 标记完成后目标是 Windows 版 parity-plus；如果没有这行代码，最终目标不明确。
    },  # 新增代码+Phase53ParityGapMatrix: Phase64 差距项结束；如果没有这行代码，Python 数据结构无法闭合。
)  # 新增代码+Phase53ParityGapMatrix: 函数外常量段结束，PHASE53_GAP_ITEMS 到此结束；如果没有这行代码，Python 元组无法闭合。


# 新增代码+Phase53ParityGapMatrix: 函数段开始，_bool_token 把布尔值转成验收器稳定匹配的小写 token；如果没有这段函数，CLI 可能混用 True/False 和 true/false，作者意图是让真实终端断言稳定。
def _bool_token(value: Any) -> str:  # 新增代码+Phase53ParityGapMatrix: 定义布尔 token helper；如果没有这行代码，多处输出会重复写转换逻辑。
    return "true" if bool(value) else "false"  # 新增代码+Phase53ParityGapMatrix: 返回小写布尔文本；如果没有这行代码，场景 JSON 的 token 匹配可能失败。
# 新增代码+Phase53ParityGapMatrix: 函数段结束，_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


# 新增代码+Phase53ParityGapMatrix: 函数段开始，_copy_items 复制矩阵项避免调用方改坏全局常量；如果没有这段函数，外部测试或 UI 可能污染后续报告，作者意图是保持合同数据不可变。
def _copy_items() -> list[dict[str, Any]]:  # 新增代码+Phase53ParityGapMatrix: 定义差距项复制 helper；如果没有这行代码，run 函数会暴露原始常量。
    return [dict(item) for item in PHASE53_GAP_ITEMS]  # 新增代码+Phase53ParityGapMatrix: 返回每个差距项的浅拷贝；如果没有这行代码，调用方修改 item 会影响全局矩阵。
# 新增代码+Phase53ParityGapMatrix: 函数段结束，_copy_items 到此结束；如果没有这个边界说明，初学者不容易看出复制保护范围。


# 新增代码+Phase53ParityGapMatrix: 函数段开始，run_phase53_parity_gap_matrix_contract 生成 Phase53 差距矩阵报告；如果没有这段函数，测试、CLI 和真实终端没有统一事实源，作者意图是把“还差 20%”变成可执行清单。
def run_phase53_parity_gap_matrix_contract() -> dict[str, Any]:  # 新增代码+Phase53ParityGapMatrix: 定义 Phase53 合同入口；如果没有这行代码，自动化和终端场景无法调用本阶段自检。
    items = _copy_items()  # 新增代码+Phase53ParityGapMatrix: 复制差距项；如果没有这行代码，报告可能直接暴露全局常量。
    owner_phases = sorted({int(item.get("owner_phase", 0) or 0) for item in items})  # 新增代码+Phase53ParityGapMatrix: 收集责任 phase；如果没有这行代码，无法判断 Phase53-64 是否全覆盖。
    required_fields_ok = all(PHASE53_REQUIRED_ITEM_FIELDS.issubset(set(item.keys())) for item in items)  # 新增代码+Phase53ParityGapMatrix: 检查每个差距项字段完整；如果没有这行代码，坏字段可能进入最终报告。
    owner_phases_complete = owner_phases == list(range(53, 65)) and len(items) == PHASE53_EXPECTED_GAP_COUNT  # 新增代码+Phase53ParityGapMatrix: 确认十二个阶段完整覆盖；如果没有这行代码，漏阶段也会被误认为完成。
    real_provider_required = any(bool(item.get("real_provider_required")) for item in items)  # 新增代码+Phase53ParityGapMatrix: 汇总是否存在真实 provider 要求；如果没有这行代码，报告无法显示后续不能只靠 fake。
    non_fake_acceptance_contract = all(str(item.get("acceptance_type")) != "fake_only" for item in items if item.get("real_provider_required"))  # 新增代码+Phase53ParityGapMatrix: 禁止真实 provider 项只靠 fake 验收；如果没有这行代码，关键差距可能被伪验收掩盖。
    claudecode_source_reviewed = all(bool(str(item.get("claudecode_source", "")).strip()) for item in items)  # 新增代码+Phase53ParityGapMatrix: 确认每项都有 ClaudeCode 源码证据；如果没有这行代码，差距矩阵可能变成猜测。
    actions_expanded = bool(PHASE53_ACTIONS_EXPANDED)  # 新增代码+Phase53ParityGapMatrix: 读取本阶段动作边界；如果没有这行代码，CLI token 的安全语义不稳定。
    gap_count = len(items)  # 新增代码+Phase53ParityGapMatrix: 计算实际差距项数量；如果没有这行代码，报告不能发现少项或多项。
    passed = bool(gap_count == PHASE53_EXPECTED_GAP_COUNT and required_fields_ok and owner_phases_complete and real_provider_required and non_fake_acceptance_contract and claudecode_source_reviewed and not actions_expanded)  # 新增代码+Phase53ParityGapMatrix: 汇总最终通过条件；如果没有这行代码，main 无法用退出码表达成功或失败。
    return {"marker": PHASE53_PARITY_GAP_MATRIX_MARKER, "ok_token": PHASE53_PARITY_GAP_MATRIX_OK_TOKEN, "model": PHASE53_PARITY_GAP_MATRIX_MODEL, "gap_count": gap_count, "owner_phases": owner_phases, "owner_phases_complete": owner_phases_complete, "required_fields_ok": required_fields_ok, "real_provider_required": real_provider_required, "non_fake_acceptance_contract": non_fake_acceptance_contract, "claudecode_source_reviewed": claudecode_source_reviewed, "actions_expanded": actions_expanded, "passed": passed, "items": items}  # 新增代码+Phase53ParityGapMatrix: 返回完整结构化报告；如果没有这行代码，CLI、测试和 UI 拿不到矩阵事实。
# 新增代码+Phase53ParityGapMatrix: 函数段结束，run_phase53_parity_gap_matrix_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同报告范围。


# 新增代码+Phase53ParityGapMatrix: 函数段开始，phase53_cli_line 把报告转成一行稳定 token；如果没有这段函数，真实终端场景需要解析复杂 JSON，作者意图是让最终回答可复制可验收。
def phase53_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase53ParityGapMatrix: 定义 Phase53 CLI 行格式化函数；如果没有这行代码，main 无法打印固定顺序 token。
    return f"{PHASE53_PARITY_GAP_MATRIX_OK_TOKEN} gap_count={int(report.get('gap_count', 0) or 0)} owner_phases_complete={_bool_token(report.get('owner_phases_complete'))} real_provider_required={_bool_token(report.get('real_provider_required'))} non_fake_acceptance={_bool_token(report.get('non_fake_acceptance_contract'))} claudecode_source_reviewed={_bool_token(report.get('claudecode_source_reviewed'))} actions_expanded={_bool_token(report.get('actions_expanded'))} marker={PHASE53_PARITY_GAP_MATRIX_MARKER}"  # 新增代码+Phase53ParityGapMatrix: 返回固定顺序 token 行；如果没有这行代码，场景断言容易因为输出漂移失败。
# 新增代码+Phase53ParityGapMatrix: 函数段结束，phase53_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 文本范围。


# 新增代码+Phase53ParityGapMatrix: 函数段开始，format_phase53_parity_gap_lines 渲染 /computer parity 可读面板；如果没有这段函数，用户只能看 JSON，作者意图是让代码小白也能看懂差距和阶段归属。
def format_phase53_parity_gap_lines(report: dict[str, Any]) -> list[str]:  # 新增代码+Phase53ParityGapMatrix: 定义终端面板渲染函数；如果没有这行代码，/computer parity 会缺少人类可读输出。
    lines = ["Computer Parity Matrix"]  # 新增代码+Phase53ParityGapMatrix: 输出固定标题；如果没有这行代码，用户分不清这是普通状态还是对齐矩阵。
    lines.append(f"- marker={report.get('marker', PHASE53_PARITY_GAP_MATRIX_MARKER)}")  # 新增代码+Phase53ParityGapMatrix: 显示 ready marker；如果没有这行代码，验收器无法稳定匹配本面板。
    lines.append(f"- model={report.get('model', PHASE53_PARITY_GAP_MATRIX_MODEL)}")  # 新增代码+Phase53ParityGapMatrix: 显示矩阵模型名；如果没有这行代码，用户不知道当前对齐规则版本。
    lines.append(f"- {phase53_cli_line(report)}")  # 新增代码+Phase53ParityGapMatrix: 直接嵌入稳定 token 行；如果没有这行代码，真实终端输出和 CLI 输出可能不一致。
    lines.append("- boundary=read_only_no_mouse_no_click_no_new_real_action")  # 新增代码+Phase53ParityGapMatrix: 明确本命令只读安全边界；如果没有这行代码，用户可能误以为 parity 会控制桌面。
    for item in report.get("items", []):  # 新增代码+Phase53ParityGapMatrix: 遍历差距项渲染摘要；如果没有这行代码，用户只能看到总数看不到具体任务。
        item_data = dict(item) if isinstance(item, dict) else {}  # 新增代码+Phase53ParityGapMatrix: 容错复制单个差距项；如果没有这行代码，坏输入可能让状态 UI 崩溃。
        lines.append(f"- gap={item_data.get('id', '')} owner_phase={item_data.get('owner_phase', '')} real_provider_required={_bool_token(item_data.get('real_provider_required'))} acceptance_type={item_data.get('acceptance_type', '')} status={item_data.get('status', '')}")  # 新增代码+Phase53ParityGapMatrix: 输出单项关键字段；如果没有这行代码，用户看不到每项由哪个 phase 补齐。
    return lines  # 新增代码+Phase53ParityGapMatrix: 返回可打印行列表；如果没有这行代码，调用方拿不到终端文本。
# 新增代码+Phase53ParityGapMatrix: 函数段结束，format_phase53_parity_gap_lines 到此结束；如果没有这个边界说明，初学者不容易看出面板渲染范围。


# 新增代码+Phase53ParityGapMatrix: 函数段开始，main 提供命令行自检入口；如果没有这段函数，真实终端无法直接运行 Phase53 差距矩阵，作者意图是自动化和可见终端共用同一合同。
def main() -> int:  # 新增代码+Phase53ParityGapMatrix: 定义命令行入口；如果没有这行代码，python -c 只能手写调用细节。
    report = run_phase53_parity_gap_matrix_contract()  # 新增代码+Phase53ParityGapMatrix: 运行 Phase53 合同；如果没有这行代码，CLI 输出没有真实依据。
    print(phase53_cli_line(report))  # 新增代码+Phase53ParityGapMatrix: 打印稳定单行 token；如果没有这行代码，验收器无法快速匹配结果。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase53ParityGapMatrix: 打印结构化报告便于人工复盘；如果没有这行代码，失败时不容易定位哪项不合格。
    print(PHASE53_PARITY_GAP_MATRIX_MARKER)  # 新增代码+Phase53ParityGapMatrix: 单独打印 ready marker；如果没有这行代码，真实终端验收可能看不到明确阶段标记。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase53ParityGapMatrix: 根据合同结果返回退出码；如果没有这行代码，失败也可能被终端当成成功。
# 新增代码+Phase53ParityGapMatrix: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


__all__ = ["PHASE53_PARITY_GAP_MATRIX_MARKER", "PHASE53_PARITY_GAP_MATRIX_MODEL", "PHASE53_PARITY_GAP_MATRIX_OK_TOKEN", "format_phase53_parity_gap_lines", "main", "phase53_cli_line", "run_phase53_parity_gap_matrix_contract"]  # 新增代码+Phase53ParityGapMatrix: 限定公开导出名称；如果没有这行代码，from module import * 会暴露内部常量和 helper。


if __name__ == "__main__":  # 新增代码+Phase53ParityGapMatrix: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase53ParityGapMatrix: 调用 main 并传递退出码；如果没有这行代码，命令行退出状态不明确。
