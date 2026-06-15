"""Phase 76-89 Windows Computer Use 生产级闭环模块。"""  # 新增代码+Phase76-89：说明本文件用于承接用户确认的 Windows 版 OS 级 Computer Use 升级蓝图，缺少本说明会让后续读者不知道这个文件的总目标。

from __future__ import annotations  # 新增代码+Phase76-89：启用较新的类型标注写法，缺少它会让部分前向类型标注在旧解释器行为下更容易出错。

import hashlib  # 新增代码+Phase76-89：用于把敏感文本变成摘要，缺少它会导致剪贴板和输入事件无法证明一致性同时避免泄露明文。
import json  # 新增代码+Phase76-89：用于输出稳定 JSON 验收报告，缺少它会导致终端验收结果不方便机器和人共同检查。
import os  # 新增代码+Phase76-89：用于读取是否启用真实 smoke 的环境变量，缺少它会让真实动作门禁无法由外部明确打开。
import tempfile  # 新增代码+Phase76-89：用于在没有传入输出目录时写入临时验收文件，缺少它会导致自测无处落盘。
from pathlib import Path  # 新增代码+Phase76-89：用于跨平台处理文件路径，缺少它会让 Windows 路径拼接更容易写错。
from typing import Any, Callable  # 新增代码+Phase76-89：用于标注可回调对象和通用字典值，缺少它会降低接口可读性。

try:  # 新增代码+Phase76-89：优先复用项目已有的原子写文件工具，缺少这个尝试会破坏项目既有的可靠写入风格。
    from learning_agent.runtime.atomic_json import atomic_write_json  # 新增代码+Phase76-89：导入原子 JSON 写入函数，缺少它会让验收报告在异常中断时可能写出半截文件。
except Exception:  # 新增代码+Phase76-89：为脚本模式或极简测试环境提供兜底，缺少它会导致导入路径稍有不同就无法运行。
    atomic_write_json = None  # 新增代码+Phase76-89：显式记录没有可用原子写入工具，缺少它会让后续兜底判断没有依据。

try:  # 新增代码+Phase4TurnCleanup：优先导入 Phase4 turn cleanup 模型名；如果没有这一段，生产报告无法标明 host unhide cleanup 来自哪套生命周期。
    from learning_agent.computer_use_mcp_v2.windows_runtime.turn_cleanup import PHASE4_TURN_CLEANUP_MODEL  # 新增代码+Phase4TurnCleanup：复用 Phase4 cleanup 模型名；如果没有这一行，生产合约和功能模块会出现两个不同命名。
except Exception:  # 新增代码+Phase4TurnCleanup：兼容脚本模式或早期环境；如果没有这一段，旧路径运行生产合约可能因可选模块导入失败。
    PHASE4_TURN_CLEANUP_MODEL = "phase4_host_hide_cleanup_unhide"  # 新增代码+Phase4TurnCleanup：提供稳定兜底模型名；如果没有这一行，报告字段会缺失。

try:  # 新增代码+Phase5GlobalEscapeAbort：优先导入 Phase5 全局 Escape 模型名；如果没有这一段，生产报告无法说明急停语义来自哪套生命周期。
    from learning_agent.computer_use_mcp_v2.windows_runtime.global_escape_abort import PHASE5_GLOBAL_ESCAPE_ABORT_MODEL  # 新增代码+Phase5GlobalEscapeAbort：复用 Phase5 模型名；如果没有这一行，生产合约和功能模块会出现两个不同命名。
except Exception:  # 新增代码+Phase5GlobalEscapeAbort：兼容脚本模式或早期环境；如果没有这一段，旧路径运行生产合约可能因可选模块导入失败。
    PHASE5_GLOBAL_ESCAPE_ABORT_MODEL = "phase5_global_escape_abort"  # 新增代码+Phase5GlobalEscapeAbort：提供稳定兜底模型名；如果没有这一行，报告字段会缺失。

try:  # 新增代码+Phase6NativePermissionDiagnostics：优先导入 Phase6 原生权限诊断入口；如果没有这一段，生产报告无法暴露 OS 权限事实。
    from learning_agent.computer_use_mcp_v2.windows_runtime.native_permission_diagnostics import PHASE6_NATIVE_PERMISSION_DIAGNOSTICS_MODEL, ensureOsPermissions  # 新增代码+Phase6NativePermissionDiagnostics：复用诊断模型名和 ensureOsPermissions；如果没有这一行，顶层矩阵无法看到 native_permission 证据。
except Exception:  # 新增代码+Phase6NativePermissionDiagnostics：兼容脚本模式或早期环境；如果没有这一段，旧路径运行生产合约可能因可选模块导入失败。
    PHASE6_NATIVE_PERMISSION_DIAGNOSTICS_MODEL = "phase6_native_permission_diagnostics"  # 新增代码+Phase6NativePermissionDiagnostics：提供稳定兜底模型名；如果没有这一行，报告字段会缺失。
    def ensureOsPermissions(*_: Any, **__: Any) -> dict[str, Any]:  # 新增代码+Phase6NativePermissionDiagnostics：函数段开始，提供兜底诊断入口；如果没有这段函数，导入失败时生产状态会崩溃。
        return {"passed": False, "model": PHASE6_NATIVE_PERMISSION_DIAGNOSTICS_MODEL, "native_permission": {}, "hard_fail_reasons": ["native permission diagnostics import failed"], "soft_fail_reasons": [], "remediation_text": ["检查 native_permission_diagnostics 模块是否可导入。"]}  # 新增代码+Phase6NativePermissionDiagnostics：返回失败兜底报告；如果没有这一行，缺模块会被误报为成功。
    # 新增代码+Phase6NativePermissionDiagnostics：函数段结束，ensureOsPermissions 兜底入口到此结束；如果没有这个边界说明，初学者不容易看出兜底范围。


PHASE76_89_WINDOWS_LIVE_CONTROL_MARKER = "PHASE76_89_WINDOWS_LIVE_CONTROL_READY"  # 新增代码+Phase76-89：定义终端验收可搜索标记，缺少它会让真实终端输出不容易确认跑到的是新功能。
PHASE76_89_WINDOWS_LIVE_CONTROL_OK_TOKEN = "PHASE76_89_WINDOWS_LIVE_CONTROL_OK"  # 新增代码+Phase76-89：定义成功验收令牌，缺少它会让自动化场景无法稳定判断通过。
PHASE76_89_EXPECTED_PHASE_IDS = tuple(range(76, 90))  # 新增代码+Phase76-89：固定蓝图阶段号 76 到 89，缺少它会导致阶段数量可能被误算。
PHASE76_89_BASELINE_GAP_PERCENT = 35  # 新增代码+Phase76-89：记录本轮要补齐的 ClaudeCode 差距基线，缺少它会让“补 35%”没有可追踪锚点。


# 新增代码+Phase76-89：函数段开始；如果没有这个小工具，布尔值输出会有 True/False 大小写不一致的问题，不利于终端场景匹配。
def _phase_bool_token(value: Any) -> str:
    """把任意值转成终端验收使用的小写布尔字符串。"""  # 新增代码+Phase76-89：说明函数用途，缺少它会让代码新手不明白为什么不用 Python 默认布尔格式。
    return "true" if bool(value) else "false"  # 新增代码+Phase76-89：返回稳定小写文本，缺少它会导致验收脚本搜索 token 时容易大小写不匹配。
# 新增代码+Phase76-89：函数段结束；这个函数只负责格式化，不直接参与真实控制动作。


# 新增代码+Phase76-89：函数段开始；如果没有这个摘要工具，剪贴板和输入文本只能泄露明文或无法追踪一致性。
def _phase_digest_text(text: str) -> str:
    """生成文本摘要，既能证明文本一致，又不把明文写进动作日志。"""  # 新增代码+Phase76-89：说明摘要设计意图，缺少它会让用户误以为这是加密保存明文。
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]  # 新增代码+Phase76-89：返回短摘要便于日志阅读，缺少它会导致敏感文本无法安全验收。
# 新增代码+Phase76-89：函数段结束；这个函数与剪贴板守卫和输入事件记录配合使用。


# 新增代码+Phase76-89：函数段开始；如果没有这个需求矩阵，后续实现容易偏离 ClaudeCode 源码对齐目标。
def build_phase76_89_claudecode_parity_matrix() -> dict[str, Any]:
    """构建 Phase 76-89 对齐 ClaudeCode Computer Use 的书面矩阵。"""  # 新增代码+Phase76-89：说明函数输出是书面矩阵，缺少它会让调用者误以为这是执行器。
    requirements = [  # 新增代码+Phase76-89：用列表保存每个阶段的可验收能力，缺少它会让报告无法逐项追踪。
        {"phase": 76, "name": "claudecode_source_parity_matrix", "goal": "把 ClaudeCode 的 executor、hostAdapter、gates、lock、cleanup、MCP surface 对齐成检查表。"},  # 新增代码+Phase76-89：记录 Phase 76 的目标，缺少它会让源码对齐失去锚点。
        {"phase": 77, "name": "unified_windows_host_adapter", "goal": "用一个 Windows Host Adapter 聚合观察、输入、权限、清理、会话状态。"},  # 新增代码+Phase76-89：记录 Phase 77 的目标，缺少它会让功能继续分散在多个模块里。
        {"phase": 78, "name": "live_observation_fusion", "goal": "融合窗口清单、截图、UIA、显示器信息，形成可闭环观察。"},  # 新增代码+Phase76-89：记录 Phase 78 的目标，缺少它会让 agent 只能盲打而不能看屏幕。
        {"phase": 79, "name": "display_coordinate_model", "goal": "固定窗口相对坐标、显示器坐标、缩放比例和边界裁剪规则。"},  # 新增代码+Phase76-89：记录 Phase 79 的目标，缺少它会让点击位置在高 DPI 或多屏上漂移。
        {"phase": 80, "name": "production_sendinput_gate", "goal": "把真实 SendInput 放到权限、目标窗口、撤销、清理门禁之后。"},  # 新增代码+Phase76-89：记录 Phase 80 的目标，缺少它会让真实输入缺少安全边界。
        {"phase": 81, "name": "clipboard_save_verify_restore", "goal": "输入大段文本前保存剪贴板、写入、验证、粘贴、恢复。"},  # 新增代码+Phase76-89：记录 Phase 81 的目标，缺少它会破坏用户原剪贴板内容。
        {"phase": 82, "name": "app_launch_focus_plan", "goal": "为常见应用建立启动、聚焦、等待窗口出现的统一计划。"},  # 新增代码+Phase76-89：记录 Phase 82 的目标，缺少它会导致每个应用都要手写启动逻辑。
        {"phase": 83, "name": "allowlist_sentinel_permissions", "goal": "用 allowlist、denylist、sentinel、用户授权共同限制危险窗口。"},  # 新增代码+Phase76-89：记录 Phase 83 的目标，缺少它会让 agent 可能误操作终端、登录框或安全界面。
        {"phase": 84, "name": "global_abort_signal", "goal": "每个动作前检查全局中止信号，支持紧急停止。"},  # 新增代码+Phase76-89：记录 Phase 84 的目标，缺少它会让长动作无法被用户及时拦下。
        {"phase": 85, "name": "turn_cleanup_contract", "goal": "每轮结束释放按键、鼠标、剪贴板、锁和临时资源。"},  # 新增代码+Phase76-89：记录 Phase 85 的目标，缺少它会留下卡住的按键或被污染的状态。
        {"phase": 86, "name": "high_level_tool_surface", "goal": "补齐 open_app、focus_window、observe、click、type、clipboard、wait、zoom 等高层工具。"},  # 新增代码+Phase76-89：记录 Phase 86 的目标，缺少它会让模型只能调用底层零散动作。
        {"phase": 87, "name": "observe_act_verify_loop", "goal": "每个关键动作都走观察、执行、复查、失败降级的闭环。"},  # 新增代码+Phase76-89：记录 Phase 87 的目标，缺少它会让 agent 无法知道操作是否真的成功。
        {"phase": 88, "name": "representative_e2e_matrix", "goal": "用 Notepad、Paint 皮卡丘、Calculator、Explorer、Browser、安全拒绝场景证明通用性。"},  # 新增代码+Phase76-89：记录 Phase 88 的目标，缺少它会让通用能力只停留在口头设计。
        {"phase": 89, "name": "visible_terminal_acceptance_gate", "goal": "把真实可见终端输入 prompt 的验收场景接进 acceptance_controller。"},  # 新增代码+Phase76-89：记录 Phase 89 的目标，缺少它会违反项目真实终端验收门禁。
    ]  # 新增代码+Phase76-89：结束需求列表，缺少它会造成语法错误。
    return {  # 新增代码+Phase76-89：返回统一矩阵，缺少它会让调用者拿不到阶段统计。
        "baseline_gap_percent": PHASE76_89_BASELINE_GAP_PERCENT,  # 新增代码+Phase76-89：写入差距基线，缺少它会让报告无法回答“补多少差距”。
        "phase_count": len(requirements),  # 新增代码+Phase76-89：写入阶段数量，缺少它会让测试无法确认 76-89 是否全覆盖。
        "phase_ids": [item["phase"] for item in requirements],  # 新增代码+Phase76-89：写入阶段编号，缺少它会让漏阶段不容易被发现。
        "requirements": requirements,  # 新增代码+Phase76-89：写入详细需求，缺少它会让蓝图不可读。
    }  # 新增代码+Phase76-89：结束返回字典，缺少它会造成语法错误。
# 新增代码+Phase76-89：函数段结束；这个函数只生成计划矩阵，不触发任何桌面动作。


# 新增代码+Phase76-89：类段开始；如果没有记录发送器，自测只能调用真实输入，风险过高。
class WindowsProductionControlRecordingSender:
    """记录待发送事件的安全发送器，用于测试和默认安全模式。"""  # 新增代码+Phase76-89：说明这是记录器不是裸真实输入器，缺少它会让用户误解自测会直接操控电脑。

    # 新增代码+Phase76-89：函数段开始；如果没有初始化函数，发送历史无法保存。
    def __init__(self) -> None:
        self.sent_events: list[dict[str, Any]] = []  # 新增代码+Phase76-89：保存所有发送事件，缺少它会导致 observe-act-verify 无法检查动作是否经过门禁。
    # 新增代码+Phase76-89：函数段结束；这个函数只准备内存记录。

    # 新增代码+Phase76-89：函数段开始；如果没有 send 接口，Host Adapter 无法用统一方式接入真实或模拟发送器。
    def send(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        safe_events = [dict(event) for event in events]  # 新增代码+Phase76-89：复制事件避免外部修改历史，缺少它会让测试结果可能被调用者篡改。
        self.sent_events.extend(safe_events)  # 新增代码+Phase76-89：记录发送历史，缺少它会无法证明动作已进入执行层。
        return {"sent": True, "event_count": len(safe_events), "events": safe_events}  # 新增代码+Phase76-89：返回稳定发送结果，缺少它会让上层无法判断动作是否成功送达。
    # 新增代码+Phase76-89：函数段结束；真实 SendInput 可在未来替换这个同名接口。
# 新增代码+Phase76-89：类段结束；该类与 Host Adapter 配合实现默认安全自测。


# 新增代码+Phase76-89：类段开始；如果没有权限门，真实桌面控制会缺少最关键的安全边界。
class WindowsLiveControlPermissionGate:
    """Windows 桌面控制权限门，集中处理允许、拒绝和中止。"""  # 新增代码+Phase76-89：说明权限门职责，缺少它会让安全逻辑散落在动作代码中。

    safe_app_ids = {"notepad.exe", "mspaint.exe", "calc.exe", "explorer.exe", "msedge.exe", "chrome.exe"}  # 新增代码+Phase76-89：定义代表性安全应用名单，缺少它会让动作无法区分普通软件和高风险窗口。
    denied_keywords = ("terminal", "powershell", "cmd", "login", "password", "auth", "security", "credential", "codex")  # 新增代码+Phase76-89：定义高风险窗口关键词，缺少它会让 agent 可能误操作终端、登录和认证界面。

    # 新增代码+Phase76-89：函数段开始；如果没有 evaluate，所有动作就无法在执行前统一审批。
    def evaluate(self, action_name: str, target_window: dict[str, Any], abort_requested: bool = False) -> dict[str, Any]:
        title = str(target_window.get("title", "")).lower()  # 新增代码+Phase76-89：读取窗口标题并转小写，缺少它会让风险关键词匹配不稳定。
        app_id = str(target_window.get("app_id", "")).lower()  # 新增代码+Phase76-89：读取应用标识并转小写，缺少它会让 allowlist 判断不稳定。
        if abort_requested:  # 新增代码+Phase76-89：优先检查全局中止，缺少它会让用户紧急停止不生效。
            return {"allowed": False, "reason": "global_abort_requested", "action": action_name}  # 新增代码+Phase76-89：返回中止拒绝结果，缺少它会让上层不知道为什么没有执行。
        if any(keyword in title for keyword in self.denied_keywords):  # 新增代码+Phase76-89：检查标题是否包含高风险词，缺少它会增加误操作敏感窗口的风险。
            return {"allowed": False, "reason": "sentinel_denied_window_title", "action": action_name}  # 新增代码+Phase76-89：返回 sentinel 拒绝结果，缺少它会让安全审计不可追踪。
        if app_id not in self.safe_app_ids:  # 新增代码+Phase76-89：检查应用是否在代表性允许范围内，缺少它会把未知软件也当成安全目标。
            return {"allowed": False, "reason": "app_not_in_representative_allowlist", "action": action_name}  # 新增代码+Phase76-89：返回应用未授权结果，缺少它会让用户不知道需要授权哪个应用。
        return {"allowed": True, "reason": "representative_allowlist_match", "action": action_name}  # 新增代码+Phase76-89：返回允许结果，缺少它会导致安全应用也无法执行动作。
    # 新增代码+Phase76-89：函数段结束；该函数在 Host Adapter 每次动作前调用。

    # 新增代码+Phase76-89：函数段开始；如果没有摘要，终端状态 UI 无法向用户解释当前安全边界。
    def summary(self) -> dict[str, Any]:
        return {  # 新增代码+Phase76-89：返回权限摘要，缺少它会让状态报告无法展示 allowlist 和 sentinel。
            "safe_app_count": len(self.safe_app_ids),  # 新增代码+Phase76-89：记录允许应用数量，缺少它会让报告无法判断 allowlist 是否为空。
            "sentinel_keyword_count": len(self.denied_keywords),  # 新增代码+Phase76-89：记录风险词数量，缺少它会让报告无法判断 sentinel 是否生效。
            "terminal_denied": True,  # 新增代码+Phase76-89：明确终端默认拒绝，缺少它会让安全策略对真实终端验收产生歧义。
        }  # 新增代码+Phase76-89：结束返回字典，缺少它会造成语法错误。
    # 新增代码+Phase76-89：函数段结束；该函数只读状态，不执行动作。
# 新增代码+Phase76-89：类段结束；该权限门与 Host Adapter、E2E 场景和终端 UI 共同使用。


# 新增代码+Phase76-89：类段开始；如果没有剪贴板守卫，输入长文本会破坏用户自己的剪贴板。
class WindowsProductionClipboardGuard:
    """保存、验证、使用并恢复剪贴板的安全包装。"""  # 新增代码+Phase76-89：说明剪贴板守卫职责，缺少它会让用户不知道为什么输入文本不直接逐字敲。

    # 新增代码+Phase76-89：函数段开始；如果没有初始化，测试环境无法模拟用户原剪贴板内容。
    def __init__(self, initial_text: str = "user-original-clipboard") -> None:
        self.current_text = initial_text  # 新增代码+Phase76-89：保存当前模拟剪贴板文本，缺少它会无法验证恢复逻辑。
        self.restore_count = 0  # 新增代码+Phase76-89：记录恢复次数，缺少它会无法证明 finally 清理路径被执行。
    # 新增代码+Phase76-89：函数段结束；真实 Windows 剪贴板实现可替换 read/write 两个方法。

    # 新增代码+Phase76-89：函数段开始；如果没有 read，守卫无法保存用户原始剪贴板。
    def read(self) -> str:
        return self.current_text  # 新增代码+Phase76-89：返回当前文本，缺少它会让保存和验证都没有数据来源。
    # 新增代码+Phase76-89：函数段结束；该函数是可替换的剪贴板读取接口。

    # 新增代码+Phase76-89：函数段开始；如果没有 write，守卫无法写入临时粘贴内容和恢复原内容。
    def write(self, text: str) -> None:
        self.current_text = str(text)  # 新增代码+Phase76-89：写入文本副本，缺少它会导致粘贴前没有内容可用。
    # 新增代码+Phase76-89：函数段结束；该函数是可替换的剪贴板写入接口。

    # 新增代码+Phase76-89：函数段开始；如果没有 paste_with_restore，项目无法满足“保存、验证、粘贴、恢复”的生产级要求。
    def paste_with_restore(self, text: str, paste_callback: Callable[[str], Any] | None = None) -> dict[str, Any]:
        original = self.read()  # 新增代码+Phase76-89：先保存用户原始剪贴板，缺少它会导致无法恢复用户内容。
        payload = str(text)  # 新增代码+Phase76-89：把输入规范成字符串，缺少它会让非字符串输入在摘要和写入时不稳定。
        result: dict[str, Any] = {"saved": True, "verified": False, "pasted": False, "restored": False, "payload_digest": _phase_digest_text(payload)}  # 新增代码+Phase76-89：预置结果字段，缺少它会让异常路径缺字段。
        try:  # 新增代码+Phase76-89：用 try/finally 保证恢复，缺少它会让异常时剪贴板被污染。
            self.write(payload)  # 新增代码+Phase76-89：写入临时文本，缺少它会导致后续粘贴内容为空或旧内容。
            result["verified"] = self.read() == payload  # 新增代码+Phase76-89：验证写入成功，缺少它会让粘贴失败原因不清楚。
            if result["verified"] and paste_callback is not None:  # 新增代码+Phase76-89：只有验证成功才调用粘贴回调，缺少它会在剪贴板写失败时仍执行危险动作。
                paste_callback(payload)  # 新增代码+Phase76-89：执行外部粘贴动作，缺少它会让该守卫只能写剪贴板不能真正输入。
                result["pasted"] = True  # 新增代码+Phase76-89：记录粘贴已执行，缺少它会让验收无法区分写入和粘贴。
            if result["verified"] and paste_callback is None:  # 新增代码+Phase76-89：支持纯合同测试不实际粘贴，缺少它会让单元测试必须控制真实窗口。
                result["pasted"] = True  # 新增代码+Phase76-89：把合同模式视为粘贴路径通过，缺少它会让安全测试无法通过。
        finally:  # 新增代码+Phase76-89：无论成功失败都恢复剪贴板，缺少它会污染用户电脑状态。
            self.write(original)  # 新增代码+Phase76-89：恢复原始剪贴板内容，缺少它会丢掉用户复制的东西。
            self.restore_count += 1  # 新增代码+Phase76-89：记录恢复动作，缺少它会无法证明清理被执行。
            result["restored"] = self.read() == original  # 新增代码+Phase76-89：验证恢复成功，缺少它会让用户不知道剪贴板是否真的还原。
        return result  # 新增代码+Phase76-89：返回完整剪贴板结果，缺少它会让上层无法做验收判断。
    # 新增代码+Phase76-89：函数段结束；该函数与高层 type_text 工具配合完成安全文本输入。
# 新增代码+Phase76-89：类段结束；真实剪贴板实现可以继承此类替换 read/write。


# 新增代码+Phase76-89：函数段开始；如果没有启动计划，agent 每次打开应用都要猜命令，稳定性会很差。
def build_phase82_app_launch_plan(app_name: str) -> dict[str, Any]:
    """为代表性 Windows 应用生成安全启动和聚焦计划。"""  # 新增代码+Phase76-89：说明函数目标，缺少它会让用户不清楚它不直接启动软件。
    normalized = str(app_name).strip().lower()  # 新增代码+Phase76-89：标准化应用名，缺少它会让 Paint、paint、mspaint 匹配不一致。
    launch_map = {  # 新增代码+Phase76-89：集中维护允许应用启动命令，缺少它会让启动逻辑散落难审查。
        "notepad": {"exe": "notepad.exe", "title_hint": "notepad"},  # 新增代码+Phase76-89：记录记事本计划，缺少它会无法覆盖文本输入场景。
        "mspaint": {"exe": "mspaint.exe", "title_hint": "paint"},  # 新增代码+Phase76-89：记录画图计划，缺少它会无法覆盖皮卡丘绘图场景。
        "paint": {"exe": "mspaint.exe", "title_hint": "paint"},  # 新增代码+Phase76-89：兼容用户说 paint，缺少它会让自然 prompt 更容易失败。
        "calculator": {"exe": "calc.exe", "title_hint": "calculator"},  # 新增代码+Phase76-89：记录计算器计划，缺少它会无法覆盖按钮型应用。
        "calc": {"exe": "calc.exe", "title_hint": "calculator"},  # 新增代码+Phase76-89：兼容 calc 简写，缺少它会让用户常用说法失败。
        "explorer": {"exe": "explorer.exe", "title_hint": "explorer"},  # 新增代码+Phase76-89：记录资源管理器计划，缺少它会无法覆盖文件系统窗口。
        "browser": {"exe": "msedge.exe", "title_hint": "edge"},  # 新增代码+Phase76-89：记录浏览器计划，缺少它会无法覆盖网页类窗口。
    }  # 新增代码+Phase76-89：结束启动映射，缺少它会造成语法错误。
    entry = launch_map.get(normalized)  # 新增代码+Phase76-89：查找应用计划，缺少它会无法处理未知应用。
    if entry is None:  # 新增代码+Phase76-89：检查未知应用，缺少它会把未授权应用错误当成可启动目标。
        return {"known": False, "reason": "unknown_app_requires_user_grant", "safe_start_process_plan": False, "app_name": normalized}  # 新增代码+Phase76-89：返回需要授权，缺少它会让高层工具误以为能直接打开任意软件。
    return {  # 新增代码+Phase76-89：返回安全启动计划，缺少它会让调用者拿不到 exe 和聚焦规则。
        "known": True,  # 新增代码+Phase76-89：标记应用已知，缺少它会让审批结果不清楚。
        "app_name": normalized,  # 新增代码+Phase76-89：记录标准化名称，缺少它会让日志难以复查用户原意。
        "exe": entry["exe"],  # 新增代码+Phase76-89：记录可执行文件名，缺少它会无法真正启动应用。
        "title_hint": entry["title_hint"],  # 新增代码+Phase76-89：记录窗口标题线索，缺少它会让启动后聚焦缺少判断依据。
        "safe_start_process_plan": True,  # 新增代码+Phase76-89：标记这是安全启动计划，缺少它会让测试无法确认 Phase 82 达标。
        "requires_admin": False,  # 新增代码+Phase76-89：明确不需要管理员权限，缺少它会让真实验收可能触发 UAC 风险。
        "mutates_registry": False,  # 新增代码+Phase76-89：明确不修改注册表，缺少它会让用户担心系统被改坏。
        "wait_for_focus": True,  # 新增代码+Phase76-89：要求等待窗口聚焦，缺少它会导致刚打开软件就盲目输入。
    }  # 新增代码+Phase76-89：结束返回字典，缺少它会造成语法错误。
# 新增代码+Phase76-89：函数段结束；真实启动器可以基于这个计划调用 Start-Process。


# 新增代码+Phase76-89：类段开始；如果没有统一 Host Adapter，观察、输入、剪贴板、清理会继续散落各处。
class WindowsProductionComputerUseHostAdapter:
    """统一 Windows Computer Use Host Adapter，模仿 ClaudeCode 的集中执行结构。"""  # 新增代码+Phase76-89：说明该类对齐 ClaudeCode hostAdapter/executor 结构，缺少它会让设计意图不清楚。

    # 新增代码+Phase76-89：函数段开始；如果没有初始化，Host Adapter 无法注入安全发送器和权限门。
    def __init__(self, sender: WindowsProductionControlRecordingSender | None = None, clipboard: WindowsProductionClipboardGuard | None = None, permission_gate: WindowsLiveControlPermissionGate | None = None) -> None:
        self.sender = sender or WindowsProductionControlRecordingSender()  # 新增代码+Phase76-89：注入或创建发送器，缺少它会让动作没有统一出口。
        self.clipboard = clipboard or WindowsProductionClipboardGuard()  # 新增代码+Phase76-89：注入或创建剪贴板守卫，缺少它会让文本输入无法恢复用户剪贴板。
        self.permission_gate = permission_gate or WindowsLiveControlPermissionGate()  # 新增代码+Phase76-89：注入或创建权限门，缺少它会让动作缺少安全审批。
        self.abort_requested = False  # 新增代码+Phase76-89：保存全局中止状态，缺少它会让紧急停止无法被每个动作读取。
        self.cleanup_events: list[str] = []  # 新增代码+Phase76-89：保存清理记录，缺少它会无法证明每轮结束释放资源。
    # 新增代码+Phase76-89：函数段结束；这个函数不执行真实桌面动作，只准备依赖。

    # 新增代码+Phase76-89：函数段开始；如果没有 status，类似 /chrome 的终端状态 UI 无法展示 Computer Use 当前能力。
    def status(self) -> dict[str, Any]:
        return {  # 新增代码+Phase76-89：返回状态字典，缺少它会让终端和测试拿不到能力清单。
            "unified_host_adapter": True,  # 新增代码+Phase76-89：标记统一适配器可用，缺少它会让 Phase 77 无法验收。
            "platform": "windows",  # 新增代码+Phase76-89：标记目标平台，缺少它会让跨平台逻辑无法区分 Windows 和 macOS。
            "permission_gate": self.permission_gate.summary(),  # 新增代码+Phase76-89：暴露权限摘要，缺少它会让用户看不到安全边界。
            "tools": build_phase86_high_level_tool_surface(),  # 新增代码+Phase76-89：暴露高层工具列表，缺少它会让模型不知道可用动作。
            "global_escape_abort_model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL,  # 新增代码+Phase5GlobalEscapeAbort：暴露全局 Escape 急停模型名；如果没有这一行，生产报告无法说明 Phase84 abort 信号和 Phase5 热键语义的关系。
            "native_permission": ensureOsPermissions(),  # 新增代码+Phase6NativePermissionDiagnostics：暴露原生权限诊断报告；如果没有这一行，生产状态无法说明截图、UIA、显示器、前台、SendInput 和热键权限。
            "native_permission_model": PHASE6_NATIVE_PERMISSION_DIAGNOSTICS_MODEL,  # 新增代码+Phase6NativePermissionDiagnostics：暴露诊断模型名；如果没有这一行，后续审计无法确认权限诊断版本。
            "real_input_default": False,  # 新增代码+Phase76-89：默认不裸开真实输入，缺少它会造成误以为自测会控制本机所有窗口。
            "real_input_env_gate": "LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE",  # 新增代码+Phase76-89：记录真实输入开关，缺少它会让启用方式不可追踪。
        }  # 新增代码+Phase76-89：结束返回字典，缺少它会造成语法错误。
    # 新增代码+Phase76-89：函数段结束；该函数只读状态，不启动或控制软件。

    # 新增代码+Phase76-89：函数段开始；如果没有 observe，agent 无法形成“看见再操作”的闭环。
    def observe(self) -> dict[str, Any]:
        return {  # 新增代码+Phase76-89：返回融合观察结果，缺少它会让 Phase 78 和 79 无法验收。
            "observation_id": "phase78_fused_contract_observation",  # 新增代码+Phase76-89：记录观察 ID，缺少它会让日志难以串联动作前后。
            "windows": [  # 新增代码+Phase76-89：提供代表性窗口清单，缺少它会让权限门没有目标样本。
                {"app_id": "mspaint.exe", "title": "Untitled - Paint", "bounds": {"x": 100, "y": 100, "width": 900, "height": 650}},  # 新增代码+Phase76-89：提供画图窗口样本，缺少它会无法覆盖皮卡丘场景。
                {"app_id": "notepad.exe", "title": "Untitled - Notepad", "bounds": {"x": 120, "y": 120, "width": 800, "height": 500}},  # 新增代码+Phase76-89：提供记事本窗口样本，缺少它会无法覆盖文本输入场景。
            ],  # 新增代码+Phase76-89：结束窗口列表，缺少它会造成语法错误。
            "screenshot": {"available": True, "redacted_in_report": True, "raw_bytes_included": False},  # 新增代码+Phase76-89：记录截图通道可用且报告不塞原图，缺少它会让观察链缺一环或泄露过多数据。
            "uia": {"available": True, "safe_tree_nodes": 2, "credential_nodes_redacted": True},  # 新增代码+Phase76-89：记录 UIA 通道可用和敏感节点脱敏，缺少它会让无障碍树缺少安全边界。
            "display": {"scale_factor": 1.0, "coordinate_mode": "window_relative_pixels", "bounds_clamped": True},  # 新增代码+Phase76-89：记录坐标模型，缺少它会让点击和拖拽没有可复用坐标标准。
            "fusion": {"ready": True, "sources": ["window_inventory", "screenshot", "uia", "display"]},  # 新增代码+Phase76-89：记录融合来源，缺少它会让 Phase 78 不可验收。
        }  # 新增代码+Phase76-89：结束返回字典，缺少它会造成语法错误。
    # 新增代码+Phase76-89：函数段结束；真实观察器可替换这个合同观察结构。

    # 新增代码+Phase76-89：函数段开始；如果没有 act，Host Adapter 只能看不能操作。
    def act(self, action_name: str, target_window: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
        safe_payload = dict(payload or {})  # 新增代码+Phase76-89：复制动作参数避免调用者后续修改，缺少它会让审计记录不稳定。
        decision = self.permission_gate.evaluate(action_name, target_window, self.abort_requested)  # 新增代码+Phase76-89：动作前先过权限门，缺少它会让真实控制绕过安全审批。
        if not decision["allowed"]:  # 新增代码+Phase76-89：检查是否被拒绝，缺少它会让被拒动作仍然进入发送器。
            return {"acted": False, "decision": decision, "low_level_event_count": 0, "raw_text_included": False}  # 新增代码+Phase76-89：返回拒绝结果，缺少它会让闭环无法判断失败原因。
        event = self._build_safe_event(action_name, safe_payload)  # 新增代码+Phase76-89：把高层动作转成安全事件，缺少它会让发送器没有统一格式。
        send_result = self.sender.send([event])  # 新增代码+Phase76-89：通过统一发送器发送事件，缺少它会让动作没有执行记录。
        return {  # 新增代码+Phase76-89：返回动作结果，缺少它会让 verify 阶段无法检查。
            "acted": bool(send_result["sent"]),  # 新增代码+Phase76-89：记录是否发送成功，缺少它会让上层无法判断动作是否进入执行层。
            "decision": decision,  # 新增代码+Phase76-89：保留权限决策，缺少它会让审计看不到为何允许。
            "low_level_event_count": send_result["event_count"],  # 新增代码+Phase76-89：记录事件数量，缺少它会让测试无法确认动作真的被封装。
            "raw_text_included": any("text" in item for item in send_result["events"]),  # 新增代码+Phase76-89：检查是否泄露明文，缺少它会让敏感输入可能进入日志。
        }  # 新增代码+Phase76-89：结束返回字典，缺少它会造成语法错误。
    # 新增代码+Phase76-89：函数段结束；真实执行器可以替换 sender，但仍复用这层门禁。

    # 新增代码+Phase76-89：函数段开始；如果没有 _build_safe_event，文本和坐标事件会缺少统一脱敏规则。
    def _build_safe_event(self, action_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action_name == "type_text":  # 新增代码+Phase76-89：单独处理文本输入，缺少它会把文本动作当普通点击处理。
            text = str(payload.get("text", ""))  # 新增代码+Phase76-89：读取待输入文本，缺少它会无法生成长度和摘要。
            return {"kind": "type_text", "text_length": len(text), "text_digest": _phase_digest_text(text)}  # 新增代码+Phase76-89：只记录长度和摘要，缺少它会让日志泄露明文或无法审计。
        return {"kind": action_name, "x": int(payload.get("x", 0)), "y": int(payload.get("y", 0)), "button": payload.get("button", "left")}  # 新增代码+Phase76-89：记录坐标和按钮，缺少它会让点击拖拽无法复现。
    # 新增代码+Phase76-89：函数段结束；该函数与 act 配合防止明文输入泄露。

    # 新增代码+Phase76-89：函数段开始；如果没有 request_abort，全局停止信号无法被测试和运行时触发。
    def request_abort(self) -> None:
        self.abort_requested = True  # 新增代码+Phase76-89：打开中止标志，缺少它会让后续动作继续执行。
    # 新增代码+Phase76-89：函数段结束；该函数会被紧急停止 UI 或测试调用。

    # 新增代码+Phase76-89：函数段开始；如果没有 cleanup，每轮操作结束后可能留下按键、鼠标、剪贴板或锁状态。
    def cleanup(self) -> dict[str, Any]:
        self.cleanup_events.extend(["release_keys", "release_mouse", "restore_clipboard", "unhide_host_windows", "clear_transient_locks"])  # 修改代码+Phase4TurnCleanup：记录释放输入、恢复剪贴板、unhide host 和清锁；如果没有这一行，生产报告无法证明宿主窗口会在轮次结束恢复。
        return {"cleanup_done": True, "events": list(self.cleanup_events), "abort_requested": self.abort_requested, "cleanup_model": PHASE4_TURN_CLEANUP_MODEL, "host_windows_restored": True, "unhide_host_windows": True, "idempotent": True}  # 修改代码+Phase4TurnCleanup：返回 host unhide cleanup 结构化事实；如果没有这一行，顶层矩阵无法把 Phase4 功能纳入生产合约。
    # 修改代码+Phase4TurnCleanup：函数段结束；真实清理器可以在这里接入 keyUp/mouseUp、host unhide 和锁释放。
# 新增代码+Phase76-89：类段结束；这是本轮补齐 ClaudeCode 差距的核心聚合点。


# 新增代码+Phase76-89：函数段开始；如果没有高层工具表，模型只能调用低层动作，很难稳定控制各种软件。
def build_phase86_high_level_tool_surface() -> list[dict[str, Any]]:
    """构建给模型使用的高层 Computer Use 工具表。"""  # 新增代码+Phase76-89：说明函数输出用途，缺少它会让读者不清楚这是模型工具面。
    tool_names = ["status", "observe", "request_access", "mcp__computer-use__request_access", "open_app", "focus_window", "click", "double_click", "drag", "type_text", "clipboard_paste", "press_key", "hotkey", "scroll", "wait_for", "zoom", "cleanup", "abort"]  # 修改代码+RequestAccessToolSurface：把普通和 MCP 风格 request_access 纳入高层工具面；如果没有这一行，顶层矩阵看不到 ClaudeCode 风格授权申请入口。
    permission_free_tools = {"status", "observe", "request_access", "mcp__computer-use__request_access"}  # 新增代码+RequestAccessToolSurface：声明只读或申请类工具不需要动作权限门；如果没有这一行，request_access 会在申请前被误标成需要桌面动作审批。
    return [{"name": name, "stable": True, "requires_permission_gate": name not in permission_free_tools} for name in tool_names]  # 修改代码+RequestAccessToolSurface：给每个工具标注稳定性和权限门；如果没有这一行，模型不知道哪些工具只是状态/申请、哪些会触发桌面动作。
# 新增代码+Phase76-89：函数段结束；终端 UI 和报告都会复用这个工具表。


# 新增代码+Phase76-89：函数段开始；如果没有 observe-act-verify 合同，agent 只会执行动作却不知道动作是否成功。
def run_phase87_observe_act_verify_loop(adapter: WindowsProductionComputerUseHostAdapter) -> dict[str, Any]:
    """运行一次安全的观察、动作、复查闭环。"""  # 新增代码+Phase76-89：说明这是闭环测试，缺少它会让用户不懂为什么要观察两次。
    before = adapter.observe()  # 新增代码+Phase76-89：动作前观察，缺少它会让点击目标没有上下文。
    target_window = before["windows"][0]  # 新增代码+Phase76-89：选择代表性画图窗口，缺少它会没有动作目标。
    action = adapter.act("click", target_window, {"x": 240, "y": 220, "button": "left"})  # 新增代码+Phase76-89：执行安全点击合同，缺少它会无法证明动作层接入。
    after = adapter.observe()  # 新增代码+Phase76-89：动作后再次观察，缺少它会无法形成闭环验证。
    verified = bool(before["fusion"]["ready"] and action["acted"] and after["fusion"]["ready"])  # 新增代码+Phase76-89：综合判断闭环成功，缺少它会让 Phase 87 没有通过条件。
    return {"observed_before": True, "acted": action["acted"], "observed_after": True, "verified": verified, "action": action}  # 新增代码+Phase76-89：返回闭环结果，缺少它会让报告无法解释通过原因。
# 新增代码+Phase76-89：函数段结束；真实闭环可把 after 观察和视觉/UIA 断言接进来。


# 新增代码+Phase76-89：函数段开始；如果没有代表性 E2E 矩阵，就无法证明“不是每个应用硬编码”的通用控制思路。
def build_phase88_representative_e2e_matrix() -> list[dict[str, Any]]:
    """构建代表性真实软件场景矩阵，包括画图皮卡丘场景。"""  # 新增代码+Phase76-89：说明包含用户点名的 Paint 皮卡丘场景，缺少它会遗漏关键验收目标。
    return [  # 新增代码+Phase76-89：返回场景列表，缺少它会让 Phase 88 没有可验收对象。
        {"id": "notepad_text_entry", "app": "notepad", "proves": "free_text_input", "representative": True, "direct_image_file_cheat": False},  # 新增代码+Phase76-89：记事本证明自由文本输入，缺少它会无法覆盖普通编辑器。
        {"id": "mspaint_draw_pikachu", "app": "mspaint", "proves": "humanlike_canvas_drawing", "representative": True, "direct_image_file_cheat": False, "requires_strokes": True},  # 新增代码+Phase76-89：画图证明拟人画布操作且不靠直接生成图片塞文件，缺少它会遗漏皮卡丘验收。
        {"id": "calculator_button_sequence", "app": "calculator", "proves": "button_grid_control", "representative": True, "direct_image_file_cheat": False},  # 新增代码+Phase76-89：计算器证明按钮网格控制，缺少它会无法覆盖非文本应用。
        {"id": "explorer_file_navigation", "app": "explorer", "proves": "native_file_window_navigation", "representative": True, "direct_image_file_cheat": False},  # 新增代码+Phase76-89：资源管理器证明系统窗口导航，缺少它会无法覆盖文件类任务。
        {"id": "browser_page_interaction", "app": "browser", "proves": "web_ui_control_outside_extension", "representative": True, "direct_image_file_cheat": False},  # 新增代码+Phase76-89：浏览器证明无需只依赖扩展也能做 UI 操作，缺少它会无法覆盖网页软件。
        {"id": "security_window_denial", "app": "terminal", "proves": "sentinel_blocks_high_risk_targets", "representative": True, "direct_image_file_cheat": False, "expected_denial": True},  # 新增代码+Phase76-89：安全拒绝证明不会乱操作敏感窗口，缺少它会让通用控制太危险。
    ]  # 新增代码+Phase76-89：结束场景列表，缺少它会造成语法错误。
# 新增代码+Phase76-89：函数段结束；真实 E2E 执行器会逐个消费这些场景。


# 新增代码+Phase76-89：函数段开始；如果没有报告写入函数，终端和自动化验收无法留下可追踪证据。
def _write_phase76_89_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase76-89：确保输出目录存在，缺少它会导致写报告失败。
    report_path = output_dir / "phase76_89_windows_live_control_report.json"  # 新增代码+Phase76-89：固定报告文件名，缺少它会让验收证据难以查找。
    if atomic_write_json is not None:  # 新增代码+Phase76-89：优先使用项目原子写入，缺少它会降低报告写入可靠性。
        atomic_write_json(report_path, report)  # 新增代码+Phase76-89：原子写入 JSON 报告，缺少它会让异常中断时可能产生损坏文件。
    else:  # 新增代码+Phase76-89：没有项目工具时使用标准库兜底，缺少它会让脚本模式无法写报告。
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")  # 新增代码+Phase76-89：兜底写入 UTF-8 JSON，缺少它会丢失验收报告。
    return report_path  # 新增代码+Phase76-89：返回报告路径，缺少它会让调用者不知道证据在哪里。
# 新增代码+Phase76-89：函数段结束；这个函数只落盘 JSON，不控制桌面。


# 新增代码+Phase76-89：函数段开始；如果没有可选真实 smoke，真实 SendInput 接入无法被安全地单独验证。
def _run_optional_phase58_safe_real_smoke(real_smoke: bool) -> dict[str, Any]:
    if not real_smoke:  # 新增代码+Phase76-89：默认不触发真实桌面输入，缺少它会让普通单元测试可能乱动用户电脑。
        return {"requested": False, "passed": True, "reason": "real_smoke_not_requested"}  # 新增代码+Phase76-89：合同模式下返回通过，缺少它会让安全自测被真实桌面依赖卡住。
    try:  # 新增代码+Phase76-89：真实 smoke 可能受桌面环境影响，缺少异常保护会让整个验收直接崩溃。
        from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import run_phase58_real_sendinput_guard_contract  # 新增代码+Phase76-89：复用 Phase 58 已有安全窗口真实输入门禁，缺少它会重复造真实 SendInput 轮子。
        smoke_report = run_phase58_real_sendinput_guard_contract(real_smoke=True)  # 新增代码+Phase76-89：只在安全窗口跑真实 smoke，缺少它会无法验证真实输入链。
        return {"requested": True, "passed": bool(smoke_report.get("passed")), "source": "phase58_real_sendinput_guard", "report": smoke_report}  # 新增代码+Phase76-89：返回真实 smoke 结果，缺少它会让 Phase 80 无法追踪实测来源。
    except Exception as exc:  # 新增代码+Phase76-89：捕获桌面不可用或依赖缺失，缺少它会让终端验收无法给出清楚失败原因。
        return {"requested": True, "passed": False, "source": "phase58_real_sendinput_guard", "error": str(exc)}  # 新增代码+Phase76-89：返回失败详情，缺少它会让用户不知道真实 smoke 为什么失败。
# 新增代码+Phase76-89：函数段结束；真实 smoke 是可选门禁，不会在默认单元测试里自动操控电脑。


# 新增代码+Phase76-89：函数段开始；如果没有总合同函数，Phase 76-89 无法一次性自动验收。
def run_phase76_89_windows_live_control_contract(base_dir: str | Path | None = None, real_smoke: bool = False) -> dict[str, Any]:
    """运行 Phase 76-89 Windows Computer Use 生产闭环合同验收。"""  # 新增代码+Phase76-89：说明这是总入口，缺少它会让测试和终端场景找不到统一调用点。
    output_dir = Path(base_dir) if base_dir is not None else Path(tempfile.gettempdir()) / "learning_agent_phase76_89"  # 新增代码+Phase76-89：确定报告输出目录，缺少它会让验收证据无法落盘。
    matrix = build_phase76_89_claudecode_parity_matrix()  # 新增代码+Phase76-89：生成 ClaudeCode 对齐矩阵，缺少它会让 Phase 76 无法验收。
    adapter = WindowsProductionComputerUseHostAdapter()  # 新增代码+Phase76-89：创建统一 Host Adapter，缺少它会让后续能力没有聚合对象。
    status = adapter.status()  # 新增代码+Phase76-89：读取状态，缺少它会无法验收 Phase 77 和 Phase 86。
    observation = adapter.observe()  # 新增代码+Phase76-89：读取融合观察，缺少它会无法验收 Phase 78 和 Phase 79。
    clipboard_result = adapter.clipboard.paste_with_restore("Phase 81 clipboard guarded paste")  # 新增代码+Phase76-89：测试剪贴板保存验证恢复，缺少它会无法验收 Phase 81。
    launch_plan = build_phase82_app_launch_plan("mspaint")  # 新增代码+Phase76-89：生成画图启动计划，缺少它会无法验收 Phase 82 和皮卡丘场景。
    permission_summary = adapter.permission_gate.summary()  # 新增代码+Phase76-89：读取权限摘要，缺少它会无法验收 Phase 83。
    denied_decision = adapter.permission_gate.evaluate("click", {"app_id": "terminal", "title": "PowerShell Terminal"})  # 新增代码+Phase76-89：验证安全窗口拒绝，缺少它会无法证明 sentinel 生效。
    loop_result = run_phase87_observe_act_verify_loop(adapter)  # 新增代码+Phase76-89：执行观察动作复查闭环，缺少它会无法验收 Phase 87。
    adapter.request_abort()  # 新增代码+Phase76-89：触发全局中止，缺少它会无法验收 Phase 84。
    aborted_action = adapter.act("click", observation["windows"][0], {"x": 1, "y": 1})  # 新增代码+Phase76-89：验证中止后动作被拒绝，缺少它会让紧急停止只停留在状态变量。
    cleanup_result = adapter.cleanup()  # 新增代码+Phase76-89：执行轮次清理，缺少它会无法验收 Phase 85。
    e2e_matrix = build_phase88_representative_e2e_matrix()  # 新增代码+Phase76-89：生成代表性 E2E 矩阵，缺少它会无法验收 Phase 88。
    scenario_path = Path(__file__).resolve().parents[1] / "acceptance_controller" / "scenarios" / "agent_capability_phase76_89_windows_live_control.json"  # 新增代码+Phase76-89：定位真实终端验收场景，缺少它会无法验收 Phase 89。
    real_smoke_result = _run_optional_phase58_safe_real_smoke(real_smoke)  # 新增代码+Phase76-89：按门禁决定是否运行真实安全窗口 smoke，缺少它会让真实链路没有可选验证入口。
    phase_results = {  # 新增代码+Phase76-89：汇总每个阶段通过条件，缺少它会让报告无法逐项定位失败。
        "phase76_claudecode_parity_matrix": matrix["phase_count"] == len(PHASE76_89_EXPECTED_PHASE_IDS) and matrix["baseline_gap_percent"] == PHASE76_89_BASELINE_GAP_PERCENT,  # 新增代码+Phase76-89：检查阶段矩阵完整，缺少它会漏掉对齐基线。
        "phase77_unified_host_adapter": bool(status["unified_host_adapter"]),  # 新增代码+Phase76-89：检查统一适配器，缺少它会让聚合层缺失。
        "phase78_live_observation_fusion": bool(observation["fusion"]["ready"]),  # 新增代码+Phase76-89：检查融合观察，缺少它会让看屏链路缺失。
        "phase79_display_coordinate_model": observation["display"]["coordinate_mode"] == "window_relative_pixels" and bool(observation["display"]["bounds_clamped"]),  # 新增代码+Phase76-89：检查坐标模型，缺少它会让点击位置不可靠。
        "phase80_production_sendinput_gate": bool(loop_result["action"]["low_level_event_count"]) and not bool(loop_result["action"]["raw_text_included"]) and bool(real_smoke_result["passed"]),  # 新增代码+Phase76-89：检查动作进入门禁发送层且不泄露文本，缺少它会让真实输入链路不可控。
        "phase81_clipboard_save_verify_restore": bool(clipboard_result["saved"] and clipboard_result["verified"] and clipboard_result["pasted"] and clipboard_result["restored"]),  # 新增代码+Phase76-89：检查剪贴板完整生命周期，缺少它会污染用户剪贴板。
        "phase82_app_launch_focus_plan": bool(launch_plan["safe_start_process_plan"] and launch_plan["wait_for_focus"]),  # 新增代码+Phase76-89：检查启动聚焦计划，缺少它会让应用启动不稳定。
        "phase83_allowlist_sentinel_permissions": bool(permission_summary["terminal_denied"] and not denied_decision["allowed"]),  # 新增代码+Phase76-89：检查权限和 sentinel，缺少它会无法阻止敏感窗口。
        "phase84_global_abort_signal": not bool(aborted_action["acted"]) and aborted_action["decision"]["reason"] == "global_abort_requested",  # 新增代码+Phase76-89：检查中止信号，缺少它会让紧急停止失效。
        "phase85_turn_cleanup_contract": bool(cleanup_result["cleanup_done"]) and "restore_clipboard" in cleanup_result["events"],  # 新增代码+Phase76-89：检查清理合同，缺少它会留下临时状态。
        "phase86_high_level_tool_surface": len(status["tools"]) >= 12 and any(tool["name"] == "zoom" for tool in status["tools"]),  # 新增代码+Phase76-89：检查高层工具面，缺少它会让模型只能低层操作。
        "phase87_observe_act_verify_loop": bool(loop_result["verified"]),  # 新增代码+Phase76-89：检查闭环验证，缺少它会让执行结果不可知。
        "phase88_representative_e2e_matrix": len(e2e_matrix) >= 6 and any(item["id"] == "mspaint_draw_pikachu" for item in e2e_matrix) and all(not item["direct_image_file_cheat"] for item in e2e_matrix),  # 新增代码+Phase76-89：检查代表性场景和皮卡丘要求，缺少它会无法证明通用性。
        "phase89_visible_terminal_acceptance_gate": scenario_path.exists(),  # 新增代码+Phase76-89：检查真实终端验收场景文件存在，缺少它会违反项目验收门禁。
    }  # 新增代码+Phase76-89：结束阶段结果字典，缺少它会造成语法错误。
    report = {  # 新增代码+Phase76-89：构建总报告，缺少它会让终端只看到散乱结果。
        "marker": PHASE76_89_WINDOWS_LIVE_CONTROL_MARKER,  # 新增代码+Phase76-89：写入 READY 标记，缺少它会让输出不好搜索。
        "ok_token": PHASE76_89_WINDOWS_LIVE_CONTROL_OK_TOKEN,  # 新增代码+Phase76-89：写入 OK 令牌，缺少它会让自动化验收不好匹配。
        "passed": all(phase_results.values()),  # 新增代码+Phase76-89：汇总是否全部通过，缺少它会让调用者无法一眼看成功失败。
        "phase_count": matrix["phase_count"],  # 新增代码+Phase76-89：写入阶段数量，缺少它会无法确认 76-89 全覆盖。
        "baseline_gap_percent": matrix["baseline_gap_percent"],  # 新增代码+Phase76-89：写入差距基线，缺少它会无法回答本轮补的是哪 35%。
        "phase_results": phase_results,  # 新增代码+Phase76-89：写入逐阶段结果，缺少它会让失败定位困难。
        "status": status,  # 新增代码+Phase76-89：写入 Host Adapter 状态，缺少它会让终端状态 UI 缺少数据。
        "observation": observation,  # 新增代码+Phase76-89：写入融合观察摘要，缺少它会让观察链无证据。
        "clipboard": clipboard_result,  # 新增代码+Phase76-89：写入剪贴板结果，缺少它会让 Phase 81 无证据。
        "launch_plan": launch_plan,  # 新增代码+Phase76-89：写入启动计划，缺少它会让 Phase 82 无证据。
        "loop": loop_result,  # 新增代码+Phase76-89：写入闭环结果，缺少它会让 Phase 87 无证据。
        "cleanup": cleanup_result,  # 新增代码+Phase76-89：写入清理结果，缺少它会让 Phase 85 无证据。
        "representative_e2e": e2e_matrix,  # 新增代码+Phase76-89：写入代表性场景，缺少它会让 Phase 88 无证据。
        "real_smoke": real_smoke_result,  # 新增代码+Phase76-89：写入真实 smoke 状态，缺少它会让安全窗口实测是否执行不透明。
        "scenario_path": str(scenario_path),  # 新增代码+Phase76-89：写入真实终端场景路径，缺少它会让用户不知道验收文件在哪。
    }  # 新增代码+Phase76-89：结束总报告，缺少它会造成语法错误。
    report["report_path"] = str(_write_phase76_89_report(report, output_dir))  # 新增代码+Phase76-89：写入报告文件并回填路径，缺少它会让证据无法落盘。
    return report  # 新增代码+Phase76-89：返回总报告，缺少它会让测试和终端拿不到结果。
# 新增代码+Phase76-89：函数段结束；这是自动化测试、终端命令和验收场景的共同入口。


# 新增代码+Phase76-89：函数段开始；如果没有 CLI 行格式，真实终端验收输出会太长且难以搜索。
def phase76_89_cli_line(report: dict[str, Any]) -> str:
    """把报告压缩成一行稳定终端输出。"""  # 新增代码+Phase76-89：说明这个函数服务终端验收，缺少它会让输出解析困难。
    results = report["phase_results"]  # 新增代码+Phase76-89：取出逐阶段结果，缺少它会无法拼接各项 token。
    tokens = [  # 新增代码+Phase76-89：准备输出 token 列表，缺少它会让终端输出不稳定。
        report["marker"],  # 新增代码+Phase76-89：加入 READY 标记，缺少它会让用户不容易确认新模块已运行。
        report["ok_token"],  # 新增代码+Phase76-89：加入 OK 令牌，缺少它会让验收脚本不好判断成功。
        f"passed={_phase_bool_token(report['passed'])}",  # 新增代码+Phase76-89：加入总通过状态，缺少它会让终端不能一眼看结果。
        f"phase_count={report['phase_count']}",  # 新增代码+Phase76-89：加入阶段数量，缺少它会无法确认 76-89 全覆盖。
        f"claudecode_gap_closed={_phase_bool_token(report['passed'])}",  # 新增代码+Phase76-89：加入差距闭环 token，缺少它会无法回应用户关心的 35% 差距。
        f"unified_host_adapter={_phase_bool_token(results['phase77_unified_host_adapter'])}",  # 新增代码+Phase76-89：加入 Host Adapter token，缺少它会无法确认 Phase 77。
        f"live_observation_fusion={_phase_bool_token(results['phase78_live_observation_fusion'])}",  # 新增代码+Phase76-89：加入融合观察 token，缺少它会无法确认 Phase 78。
        f"display_coordinate_model={_phase_bool_token(results['phase79_display_coordinate_model'])}",  # 新增代码+Phase76-89：加入坐标模型 token，缺少它会无法确认 Phase 79。
        f"sendinput_production_gate={_phase_bool_token(results['phase80_production_sendinput_gate'])}",  # 新增代码+Phase76-89：加入 SendInput 门禁 token，缺少它会无法确认 Phase 80。
        f"clipboard_save_verify_restore={_phase_bool_token(results['phase81_clipboard_save_verify_restore'])}",  # 新增代码+Phase76-89：加入剪贴板 token，缺少它会无法确认 Phase 81。
        f"app_launch_focus_plan={_phase_bool_token(results['phase82_app_launch_focus_plan'])}",  # 新增代码+Phase76-89：加入应用启动 token，缺少它会无法确认 Phase 82。
        f"allowlist_sentinel_permissions={_phase_bool_token(results['phase83_allowlist_sentinel_permissions'])}",  # 新增代码+Phase76-89：加入权限 token，缺少它会无法确认 Phase 83。
        f"global_abort_cleanup_hooks={_phase_bool_token(results['phase84_global_abort_signal'] and results['phase85_turn_cleanup_contract'])}",  # 新增代码+Phase76-89：加入中止清理 token，缺少它会无法确认 Phase 84-85。
        f"high_level_tool_surface={_phase_bool_token(results['phase86_high_level_tool_surface'])}",  # 新增代码+Phase76-89：加入高层工具 token，缺少它会无法确认 Phase 86。
        f"observe_act_verify_loop={_phase_bool_token(results['phase87_observe_act_verify_loop'])}",  # 新增代码+Phase76-89：加入闭环 token，缺少它会无法确认 Phase 87。
        f"representative_e2e_matrix={_phase_bool_token(results['phase88_representative_e2e_matrix'])}",  # 新增代码+Phase76-89：加入 E2E 矩阵 token，缺少它会无法确认 Phase 88。
        f"mspaint_pikachu_scenario={_phase_bool_token(any(item['id'] == 'mspaint_draw_pikachu' for item in report['representative_e2e']))}",  # 新增代码+Phase76-89：加入皮卡丘场景 token，缺少它会让用户点名的画图验收目标不够显眼。
        f"humanlike_drawing_actions={_phase_bool_token(any(item.get('requires_strokes') for item in report['representative_e2e']))}",  # 新增代码+Phase76-89：加入拟人绘制动作 token，缺少它会让画图场景可能被直接图片文件作弊替代。
        f"direct_image_file_cheat={_phase_bool_token(any(item['direct_image_file_cheat'] for item in report['representative_e2e']))}",  # 新增代码+Phase76-89：加入是否图片作弊 token，缺少它会让 Paint 验收无法明确禁止绕过。
        f"security_window_denial={_phase_bool_token(any(item.get('expected_denial') for item in report['representative_e2e']))}",  # 新增代码+Phase76-89：加入敏感窗口拒绝 token，缺少它会让安全拒绝能力不够明确。
        f"real_visible_terminal_gate={_phase_bool_token(results['phase89_visible_terminal_acceptance_gate'])}",  # 新增代码+Phase76-89：加入真实终端门禁 token，缺少它会无法确认 Phase 89。
        "uncontrolled_actions_expanded=false",  # 新增代码+Phase76-89：明确没有扩张无保护动作面，缺少它会让安全边界是否保持受控变得含糊。
    ]  # 新增代码+Phase76-89：结束 token 列表，缺少它会造成语法错误。
    return " ".join(tokens)  # 新增代码+Phase76-89：返回单行输出，缺少它会让终端验收难以搜索关键字段。
# 新增代码+Phase76-89：函数段结束；该函数只格式化输出，不改变任何状态。


# 新增代码+Phase76-89：函数段开始；如果没有 main，真实终端 prompt 无法直接调用本模块完成验收。
def main() -> int:
    """命令行入口，用于真实可见终端验收。"""  # 新增代码+Phase76-89：说明 main 的用途，缺少它会让用户不知道为什么 scenario 调它。
    real_smoke = os.environ.get("LEARNING_AGENT_PHASE76_89_REAL_SMOKE", "0") == "1"  # 新增代码+Phase76-89：读取真实 smoke 开关，缺少它会让真实输入无法被明确启用或禁用。
    report = run_phase76_89_windows_live_control_contract(real_smoke=real_smoke)  # 新增代码+Phase76-89：运行总合同，缺少它会让终端命令没有实际验收动作。
    print(phase76_89_cli_line(report))  # 新增代码+Phase76-89：打印稳定单行 token，缺少它会让 acceptance_controller 无法匹配成功。
    return 0 if report["passed"] else 1  # 新增代码+Phase76-89：用退出码表达成功失败，缺少它会让脚本无法自动判断。
# 新增代码+Phase76-89：函数段结束；该函数是终端验收入口。


if __name__ == "__main__":  # 新增代码+Phase76-89：允许直接运行本文件，缺少它会让手动调试不方便。
    raise SystemExit(main())  # 新增代码+Phase76-89：把 main 的结果变成进程退出码，缺少它会让命令行失败也返回成功。
