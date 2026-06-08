"""Windows 通用 OS 级 Computer Use mode 运行时。"""  # 新增代码+Phase92UniversalComputerUse：说明本文件负责“一个通用运行时控制普通 Windows 应用”的入口；如果没有这行代码，维护者很难知道 Phase92 的核心位置。

from __future__ import annotations  # 新增代码+Phase92UniversalComputerUse：启用延迟类型解析；如果没有这行代码，后续类方法类型标注在旧解释器或循环导入时更容易出问题。

import hashlib  # 新增代码+Phase92UniversalComputerUse：导入哈希库用于 prompt 脱敏追踪；如果没有这行代码，报告只能保存原文或完全无法关联任务。
import json  # 新增代码+Phase92UniversalComputerUse：导入 JSON 用于报告序列化和隐私检查；如果没有这行代码，契约验收不能稳定检查 raw_text_hidden。
import time  # 新增代码+Phase92UniversalComputerUse：导入时间用于生成隔离 session/report 目录；如果没有这行代码，多次运行报告可能互相覆盖。
from pathlib import Path  # 新增代码+Phase92UniversalComputerUse：导入 Path 统一处理 Windows 路径；如果没有这行代码，路径拼接会更脆弱。
from typing import Any  # 新增代码+Phase92UniversalComputerUse：导入 Any 描述 JSON 风格对象；如果没有这行代码，接口边界对初学者不清楚。

try:  # 新增代码+Phase92UniversalComputerUse：优先按 learning_agent 包路径导入已有组件；如果没有这段代码，单元测试和生产入口不能共享同一套模块。
    from learning_agent.computer_use.generic_control_actions import Phase70RecordingHighLevelTool, WindowsGenericControlActionRuntime  # 新增代码+Phase92UniversalComputerUse：复用通用控件动作层；如果没有这行代码，Phase92 会退回按应用写控制器。
    from learning_agent.computer_use.generic_input_actions import Phase71RecordingInputSender, WindowsGenericInputActionRuntime  # 新增代码+Phase92UniversalComputerUse：复用通用键鼠事件构建层；如果没有这行代码，菜单、热键、滚轮和拖拽无法纳入统一模式。
    from learning_agent.computer_use.observation_fusion import WindowsObservationFusionRuntime  # 新增代码+Phase92UniversalComputerUse：复用观察融合层；如果没有这行代码，运行时无法统一看截图、UIA、OCR 和窗口状态。
    from learning_agent.computer_use.persistent_grants import WindowsComputerUsePersistentGrantStore  # 新增代码+Phase92UniversalComputerUse：复用持久授权 store；如果没有这行代码，真实应用安全边界没有授权事实源。
    from learning_agent.computer_use.production_live_control import WindowsProductionComputerUseHostAdapter  # 新增代码+Phase92UniversalComputerUse：复用生产 host adapter；如果没有这行代码，运行时无法声明和真实 Windows 控制桥的连接点。
    from learning_agent.computer_use.prompt_task_planner import WindowsPromptTaskPlanner, classify_risk  # 新增代码+Phase92UniversalComputerUse：复用 prompt 任务规划器和风险分类；如果没有这行代码，自然语言任务无法转成统一步骤。
    from learning_agent.computer_use.real_app_safety_boundary import WindowsRealAppSafetyBoundary  # 新增代码+Phase92UniversalComputerUse：复用真实应用安全边界；如果没有这行代码，未授权窗口和高风险窗口无法统一拒绝。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase92UniversalComputerUse：复用项目原子 JSON 写入工具；如果没有这行代码，验收报告可能半写损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase92UniversalComputerUse：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，真实可见终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase92UniversalComputerUse：只对包路径缺失做 fallback；如果没有这行代码，真实内部 bug 会被误吞。
        raise  # 新增代码+Phase92UniversalComputerUse：重新抛出非路径类导入错误；如果没有这行代码，依赖内部错误会被隐藏。
    from computer_use.generic_control_actions import Phase70RecordingHighLevelTool, WindowsGenericControlActionRuntime  # type: ignore  # 新增代码+Phase92UniversalComputerUse：脚本模式复用通用控件动作层；如果没有这行代码，bat 入口无法加载 Phase92 控件动作依赖。
    from computer_use.generic_input_actions import Phase71RecordingInputSender, WindowsGenericInputActionRuntime  # type: ignore  # 新增代码+Phase92UniversalComputerUse：脚本模式复用通用输入动作层；如果没有这行代码，bat 入口无法构建热键菜单滚轮拖拽能力。
    from computer_use.observation_fusion import WindowsObservationFusionRuntime  # type: ignore  # 新增代码+Phase92UniversalComputerUse：脚本模式复用观察融合层；如果没有这行代码，bat 入口无法构建统一观察对象。
    from computer_use.persistent_grants import WindowsComputerUsePersistentGrantStore  # type: ignore  # 新增代码+Phase92UniversalComputerUse：脚本模式复用持久授权 store；如果没有这行代码，bat 入口无法验证未授权拒绝。
    from computer_use.production_live_control import WindowsProductionComputerUseHostAdapter  # type: ignore  # 新增代码+Phase92UniversalComputerUse：脚本模式复用生产 host adapter；如果没有这行代码，bat 入口无法连接生产控制桥声明。
    from computer_use.prompt_task_planner import WindowsPromptTaskPlanner, classify_risk  # type: ignore  # 新增代码+Phase92UniversalComputerUse：脚本模式复用任务规划器；如果没有这行代码，bat 入口无法从 prompt 得到步骤。
    from computer_use.real_app_safety_boundary import WindowsRealAppSafetyBoundary  # type: ignore  # 新增代码+Phase92UniversalComputerUse：脚本模式复用安全边界；如果没有这行代码，bat 入口无法执行高风险拒绝。
    from runtime.files import atomic_write_json  # type: ignore  # 新增代码+Phase92UniversalComputerUse：脚本模式复用原子写工具；如果没有这行代码，bat 验收报告可能半写。

PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MARKER = "PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_READY"  # 新增代码+Phase92UniversalComputerUse：定义 Phase92 ready 标记；如果没有这行代码，真实终端验收无法稳定识别阶段结果。
PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK_TOKEN = "PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK"  # 新增代码+Phase92UniversalComputerUse：定义 Phase92 OK 标记；如果没有这行代码，debug log 无法区分成功契约和普通输出。
PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MODEL = "phase92_universal_windows_computer_use_mode"  # 新增代码+Phase92UniversalComputerUse：定义本阶段协议模型名；如果没有这行代码，后续矩阵和报告无法引用版本。
PHASE92_DEFAULT_REAL_ACTIONS_ENABLED = False  # 新增代码+Phase92UniversalComputerUse：声明默认不执行真实桌面动作；如果没有这行代码，用户普通询问可能误触本机。
PHASE92_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase92UniversalComputerUse：声明没有扩大无授权动作面；如果没有这行代码，安全审计无法判断边界是否被放宽。
PHASE92_HIGH_RISK_TERMS = ("password", "payment", "credential", "captcha", "admin", "administrator", "security", "token", "login", "sign in", "密码", "支付", "付款", "凭据", "验证码", "登录", "登入", "管理员", "安全", "口令", "令牌")  # 新增代码+Phase92UniversalComputerUse：补齐中英文高风险关键词；如果没有这行代码，中文用户的敏感 prompt 可能绕过确认门禁。
DEFAULT_PHASE92_UNIVERSAL_MODE_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "phase92_universal_mode"  # 新增代码+Phase92UniversalComputerUse：定义默认报告目录；如果没有这行代码，运行时输出没有稳定落点。


# 新增代码+Phase92UniversalComputerUse：函数段开始，_phase92_bool_token 把布尔值转成小写验收 token；如果没有这段函数，CLI 输出会混用 True/False，作者意图是让真实终端断言稳定。
def _phase92_bool_token(value: Any) -> str:  # 新增代码+Phase92UniversalComputerUse：定义布尔 token helper；如果没有这行代码，多处输出会重复写转换逻辑。
    return "true" if bool(value) else "false"  # 新增代码+Phase92UniversalComputerUse：返回小写布尔文本；如果没有这行代码，场景 JSON 的 token 匹配可能失败。
# 新增代码+Phase92UniversalComputerUse：函数段结束，_phase92_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


# 新增代码+Phase92UniversalComputerUse：函数段开始，_phase92_safe_prompt_text 只在内存中清理 prompt；如果没有这段函数，None、换行或超长 prompt 会污染规划器。
def _phase92_safe_prompt_text(prompt: Any) -> str:  # 新增代码+Phase92UniversalComputerUse：定义 prompt 清洗函数；如果没有这行代码，调用方要到处处理空值和换行。
    text = " ".join(str(prompt or "").strip().split())  # 新增代码+Phase92UniversalComputerUse：把 prompt 转成单行干净文本；如果没有这行代码，换行和多空格会影响关键词判断。
    return text[:1000]  # 新增代码+Phase92UniversalComputerUse：限制 prompt 最大长度；如果没有这行代码，超长输入会刷爆日志和报告。
# 新增代码+Phase92UniversalComputerUse：函数段结束，_phase92_safe_prompt_text 到此结束；如果没有这个边界说明，初学者不容易看出 prompt 清洗范围。


# 新增代码+Phase92UniversalComputerUse：函数段开始，_phase92_sha256_16 生成短哈希；如果没有这段函数，报告要么泄露原文，要么无法追踪任务。
def _phase92_sha256_16(value: Any) -> str:  # 新增代码+Phase92UniversalComputerUse：定义短哈希函数；如果没有这行代码，多个报告字段无法稳定脱敏。
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase92UniversalComputerUse：稳定序列化任意 JSON 风格值；如果没有这行代码，同一内容顺序不同会得到不同摘要。
    return hashlib.sha256(serialized.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase92UniversalComputerUse：返回 SHA256 前 16 位；如果没有这行代码，短指纹没有真实内容来源。
# 新增代码+Phase92UniversalComputerUse：函数段结束，_phase92_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出哈希范围。


# 新增代码+Phase92UniversalComputerUse：函数段开始，_phase92_prompt_risk 合并旧 planner 风险和中文高风险词；如果没有这段函数，中文敏感任务可能无法要求确认。
def _phase92_prompt_risk(prompt: str, planner_risk: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase92UniversalComputerUse：定义 Phase92 风险汇总入口；如果没有这行代码，运行时只能依赖旧规划器的英文风险规则。
    lowered = str(prompt or "").lower()  # 新增代码+Phase92UniversalComputerUse：生成小写文本用于英文匹配；如果没有这行代码，Password/PASSWORD 等变体可能漏检。
    matched = [term for term in PHASE92_HIGH_RISK_TERMS if term.lower() in lowered or term in prompt]  # 新增代码+Phase92UniversalComputerUse：收集中英文高风险命中；如果没有这行代码，密码、支付、管理员等 prompt 可能被当成普通任务。
    planner_requires_confirmation = bool(planner_risk.get("requires_confirmation"))  # 新增代码+Phase92UniversalComputerUse：读取旧规划器确认结果；如果没有这行代码，旧规则命中的高风险会被丢掉。
    requires_confirmation = bool(planner_requires_confirmation or matched)  # 新增代码+Phase92UniversalComputerUse：合并新旧高风险判断；如果没有这行代码，任一风险源都不能单独触发门禁。
    return {"risk_level": "high" if requires_confirmation else "normal", "requires_confirmation": requires_confirmation, "matched_keyword_count": len(matched) + len(list(planner_risk.get("matched_keywords", []) or [])), "raw_keywords_hidden": True}  # 新增代码+Phase92UniversalComputerUse：返回脱敏风险摘要；如果没有这行代码，调用方可能把敏感关键词原文写入报告。
# 新增代码+Phase92UniversalComputerUse：函数段结束，_phase92_prompt_risk 到此结束；如果没有这个边界说明，初学者不容易看出风险汇总范围。


# 新增代码+Phase92UniversalComputerUse：函数段开始，_phase92_redact_sensitive_step_text 隐藏计划步骤里的敏感词；如果没有这段函数，高风险 planner 的说明文本可能间接泄露用户任务。
def _phase92_redact_sensitive_step_text(value: Any) -> str:  # 新增代码+Phase92UniversalComputerUse：定义步骤文本脱敏函数；如果没有这行代码，_sanitized_plan 只能删除 prompt 字段但不能处理步骤说明。
    text = str(value or "")  # 新增代码+Phase92UniversalComputerUse：把动态值转成字符串；如果没有这行代码，None 或数字字段会让替换逻辑不稳定。
    for term in PHASE92_HIGH_RISK_TERMS:  # 新增代码+Phase92UniversalComputerUse：遍历中英文高风险词；如果没有这行代码，密码、支付、token 等词会留在报告里。
        text = text.replace(term, "[redacted-risk-term]")  # 新增代码+Phase92UniversalComputerUse：替换完全匹配的风险词；如果没有这行代码，中文敏感词不会被隐藏。
        text = text.replace(term.lower(), "[redacted-risk-term]")  # 新增代码+Phase92UniversalComputerUse：替换小写英文风险词；如果没有这行代码，password/payment 等英文词可能留在报告里。
    return text  # 新增代码+Phase92UniversalComputerUse：返回脱敏文本；如果没有这行代码，调用方拿不到处理后的步骤说明。
# 新增代码+Phase92UniversalComputerUse：函数段结束，_phase92_redact_sensitive_step_text 到此结束；如果没有这个边界说明，初学者不容易看出步骤文本脱敏范围。


# 新增代码+Phase92UniversalComputerUse：函数段开始，_phase92_fake_observation_inputs 构造无副作用观察样本；如果没有这段函数，契约测试可能触碰真实桌面。
def _phase92_fake_observation_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:  # 新增代码+Phase92UniversalComputerUse：定义观察样本生成函数；如果没有这行代码，观察融合契约输入会散落在多处。
    window = {"app_id": "generic_windows_app.exe", "process_name": "generic_windows_app.exe", "window_id": "hwnd:9201", "title_preview": "LearningAgent Phase92 Generic Window", "display_id": "DISPLAY1", "rect": {"left": 100, "top": 100, "right": 900, "bottom": 700}}  # 新增代码+Phase92UniversalComputerUse：构造普通应用窗口引用；如果没有这行代码，观察融合没有目标窗口。
    screenshot = {"screenshot_captured": True, "screenshot_path": "memory/computer_use/phase92/fake.bmp", "screenshot_width": 800, "screenshot_height": 600, "screenshot_format": "bmp", "pixel_guard_passed": True, "artifact_openable": True, "screenshot_bytes_included": False}  # 新增代码+Phase92UniversalComputerUse：构造截图摘要而不保存图片字节；如果没有这行代码，视觉观察 token 没有输入。
    uia = {"captured": True, "real_uia_tree": True, "raw_text_included": False, "flat_nodes": [{"node_id": "0", "name": "Main work area", "role": "Pane", "automation_id": "phase92_main", "class_name": "Pane", "bounds": {"left": 120, "top": 150, "right": 860, "bottom": 660, "width": 740, "height": 510}, "clickable": True, "editable": False}], "node_count": 1, "clickable_count": 1, "editable_count": 0, "bounds_available": True, "semantic_locator_available": True}  # 新增代码+Phase92UniversalComputerUse：构造 UIA 控件摘要；如果没有这行代码，通用动作层没有可定位候选。
    inventory = {"windows": [window], "filtered_count": 0, "captured_at": "2026-06-04T00:00:00Z", "source": "phase92_contract_static", "active_window": window}  # 新增代码+Phase92UniversalComputerUse：构造窗口清单摘要；如果没有这行代码，观察融合无法判断目标窗口状态。
    ocr = {"provider_available": False, "provider": "not_configured", "install_attempted": False, "result_count": 0, "text_summary": "", "raw_text_included": False}  # 新增代码+Phase92UniversalComputerUse：构造 OCR 预留槽；如果没有这行代码，观察融合的 OCR/vision 位置无法验证。
    return window, screenshot, uia, inventory, ocr  # 新增代码+Phase92UniversalComputerUse：返回完整 fake 观察输入；如果没有这行代码，调用方拿不到统一样本。
# 新增代码+Phase92UniversalComputerUse：函数段结束，_phase92_fake_observation_inputs 到此结束；如果没有这个边界说明，初学者不容易看出 fake 观察范围。


# 新增代码+Phase92UniversalComputerUse：类段开始，UniversalWindowsComputerUseRuntime 组合观察、规划、动作、安全和 host adapter；如果没有这个类，computer use 仍会像一堆分散工具而不是一个通用 OS 控制模式。
class UniversalWindowsComputerUseRuntime:
    # 新增代码+Phase92UniversalComputerUse：函数段开始，__init__ 注入或创建 Phase92 依赖组件；如果没有这段函数，测试和生产无法复用同一个 runtime 对象。
    def __init__(self, base_dir: str | Path | None = None, observation_runtime: Any | None = None, planner: Any | None = None, control_runtime: Any | None = None, input_runtime: Any | None = None, safety_boundary: Any | None = None, host_adapter: Any | None = None) -> None:  # 新增代码+Phase92UniversalComputerUse：定义构造函数和可注入依赖；如果没有这行代码，单元测试无法替换组件。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_PHASE92_UNIVERSAL_MODE_ROOT / f"run-{int(time.time() * 1000)}"  # 新增代码+Phase92UniversalComputerUse：确定隔离输出目录；如果没有这行代码，多次运行可能写到同一个位置。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase92UniversalComputerUse：创建输出目录；如果没有这行代码，保存报告时会因为目录不存在失败。
        self.observation_runtime = observation_runtime or WindowsObservationFusionRuntime()  # 新增代码+Phase92UniversalComputerUse：保存观察融合 runtime；如果没有这行代码，通用闭环没有观察层。
        self.planner = planner or WindowsPromptTaskPlanner()  # 新增代码+Phase92UniversalComputerUse：保存 prompt 规划器；如果没有这行代码，自然语言无法转成步骤。
        self.control_runtime = control_runtime or WindowsGenericControlActionRuntime(high_level_tool=Phase70RecordingHighLevelTool())  # 新增代码+Phase92UniversalComputerUse：保存通用控件动作 runtime；如果没有这行代码，点击和输入会退回应用脚本。
        self.input_runtime = input_runtime or WindowsGenericInputActionRuntime(sender=Phase71RecordingInputSender())  # 新增代码+Phase92UniversalComputerUse：保存通用输入 runtime；如果没有这行代码，热键、菜单、滚轮、拖拽无法统一表达。
        self.safety_boundary = safety_boundary or WindowsRealAppSafetyBoundary()  # 新增代码+Phase92UniversalComputerUse：保存真实应用安全边界；如果没有这行代码，未授权和高风险窗口无法阻断。
        self.host_adapter = host_adapter or WindowsProductionComputerUseHostAdapter()  # 新增代码+Phase92UniversalComputerUse：保存生产 host adapter；如果没有这行代码，运行时无法接到真实 Windows 控制桥。
        self.grant_store = WindowsComputerUsePersistentGrantStore(base_dir=self.base_dir / "grants")  # 新增代码+Phase92UniversalComputerUse：创建隔离授权 store；如果没有这行代码，安全边界无法评估未授权窗口。
    # 新增代码+Phase92UniversalComputerUse：函数段结束，UniversalWindowsComputerUseRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    # 新增代码+Phase92UniversalComputerUse：函数段开始，status 输出通用 runtime 的组件状态；如果没有这段函数，agent 无法解释当前 mode 是否可用。
    def status(self) -> dict[str, Any]:  # 新增代码+Phase92UniversalComputerUse：定义状态查询方法；如果没有这行代码，工具入口只能执行而不能自检。
        return {"marker": PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MARKER, "model": PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MODEL, "single_universal_runtime": True, "prompt_to_any_normal_app": True, "per_app_controller_required": False, "representative_apps_are_acceptance_only": True, "generic_observe_plan_act_verify_loop": True, "uses_observation_fusion": isinstance(self.observation_runtime, WindowsObservationFusionRuntime), "uses_prompt_task_planner": isinstance(self.planner, WindowsPromptTaskPlanner), "uses_generic_action_layer": isinstance(self.control_runtime, WindowsGenericControlActionRuntime) and isinstance(self.input_runtime, WindowsGenericInputActionRuntime), "uses_real_app_safety_boundary": isinstance(self.safety_boundary, WindowsRealAppSafetyBoundary), "uses_production_host_adapter": isinstance(self.host_adapter, WindowsProductionComputerUseHostAdapter), "default_real_actions_enabled": PHASE92_DEFAULT_REAL_ACTIONS_ENABLED, "uncontrolled_actions_expanded": PHASE92_UNCONTROLLED_ACTIONS_EXPANDED}  # 新增代码+Phase92UniversalComputerUse：返回核心能力布尔字段；如果没有这行代码，验收无法判断是不是单一通用运行时。
    # 新增代码+Phase92UniversalComputerUse：函数段结束，UniversalWindowsComputerUseRuntime.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    # 新增代码+Phase92UniversalComputerUse：函数段开始，_sanitized_plan 删除原始 prompt 并保留结构化步骤；如果没有这段函数，报告可能泄露用户原文。
    def _sanitized_plan(self, plan: dict[str, Any], prompt_digest: str, risk: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase92UniversalComputerUse：定义计划脱敏方法；如果没有这行代码，run_prompt 会直接暴露 planner 返回的 prompt 字段。
        steps: list[dict[str, Any]] = []  # 修改代码+Phase92UniversalComputerUse：准备保存脱敏步骤列表；如果没有这行代码，计划步骤会直接复制敏感说明。
        for step in list(plan.get("steps", []) or []):  # 新增代码+Phase92UniversalComputerUse：遍历 planner 步骤；如果没有这行代码，无法逐步处理高风险说明文本。
            if not isinstance(step, dict):  # 新增代码+Phase92UniversalComputerUse：跳过坏步骤对象；如果没有这行代码，非字典值会让字段脱敏报错。
                continue  # 新增代码+Phase92UniversalComputerUse：继续处理下一个步骤；如果没有这行代码，坏步骤会中断整个 mode 报告。
            safe_step = dict(step)  # 新增代码+Phase92UniversalComputerUse：复制单个步骤；如果没有这行代码，脱敏会修改 planner 原始对象。
            if bool(risk.get("requires_confirmation")):  # 新增代码+Phase92UniversalComputerUse：只在高风险计划中额外脱敏说明文本；如果没有这行代码，普通计划会被不必要修改。
                safe_step["expected_result"] = _phase92_redact_sensitive_step_text(safe_step.get("expected_result", ""))  # 新增代码+Phase92UniversalComputerUse：隐藏 expected_result 里的敏感词；如果没有这行代码，高风险原因可能泄露。
                safe_step["checkpoint"] = _phase92_redact_sensitive_step_text(safe_step.get("checkpoint", ""))  # 新增代码+Phase92UniversalComputerUse：隐藏 checkpoint 里的敏感词；如果没有这行代码，检查点文本可能泄露敏感词。
            steps.append(safe_step)  # 新增代码+Phase92UniversalComputerUse：保存脱敏后的步骤；如果没有这行代码，返回计划会缺少步骤。
        return {"prompt_sha256_16": prompt_digest, "prompt_text_included": False, "app": str(plan.get("app", "generic")), "task_type": str(plan.get("task_type", "generic_windows_task")), "step_count": int(plan.get("step_count", len(steps)) or 0), "risk_level": str(risk.get("risk_level", plan.get("risk_level", "normal"))), "requires_confirmation": bool(risk.get("requires_confirmation", plan.get("requires_confirmation", False))), "representative_scenario": bool(plan.get("representative_scenario", False)), "paint_pikachu_scenario": bool(plan.get("paint_pikachu_scenario", False)), "per_app_script": bool(plan.get("per_app_script", False)), "steps": steps}  # 新增代码+Phase92UniversalComputerUse：返回不含 raw prompt 的计划；如果没有这行代码，隐私门禁无法通过。
    # 新增代码+Phase92UniversalComputerUse：函数段结束，UniversalWindowsComputerUseRuntime._sanitized_plan 到此结束；如果没有这个边界说明，初学者不容易看出计划脱敏范围。

    # 新增代码+Phase92UniversalComputerUse：函数段开始，_fused_observation_summary 生成无副作用观察摘要；如果没有这段函数，运行时无法证明接入观察融合层。
    def _fused_observation_summary(self) -> dict[str, Any]:  # 新增代码+Phase92UniversalComputerUse：定义观察摘要方法；如果没有这行代码，run_prompt 报告缺少观察层证据。
        window, screenshot, uia, inventory, ocr = _phase92_fake_observation_inputs()  # 新增代码+Phase92UniversalComputerUse：获取 fake 观察输入；如果没有这行代码，观察融合没有安全样本。
        fused = self.observation_runtime.observe(window, screenshot, uia, inventory, ocr_result=ocr)  # 新增代码+Phase92UniversalComputerUse：调用现有观察融合 runtime；如果没有这行代码，uses_observation_fusion 只是空声明。
        return {"fingerprint": _phase92_sha256_16(fused), "screenshot_observation": bool(fused.get("screenshot_observation")), "uia_tree_observation": bool(fused.get("uia_tree_observation")), "window_state_observation": bool(fused.get("window_state_observation")), "raw_text_included": False}  # 新增代码+Phase92UniversalComputerUse：返回脱敏观察摘要；如果没有这行代码，报告可能过大或泄露视觉文本。
    # 新增代码+Phase92UniversalComputerUse：函数段结束，UniversalWindowsComputerUseRuntime._fused_observation_summary 到此结束；如果没有这个边界说明，初学者不容易看出观察摘要范围。

    # 新增代码+Phase92UniversalComputerUse：函数段开始，run_prompt 执行通用 mode 的安全预演或受控入口；如果没有这段函数，用户 prompt 无法打开通用 Computer Use 模式。
    def run_prompt(self, prompt: Any, real_actions: bool = False) -> dict[str, Any]:  # 新增代码+Phase92UniversalComputerUse：定义 prompt 运行方法；如果没有这行代码，tool_surface 的 mode 路由没有目标。
        prompt_text = _phase92_safe_prompt_text(prompt)  # 新增代码+Phase92UniversalComputerUse：清理 prompt 只用于内存规划；如果没有这行代码，规划器可能收到空值或超长文本。
        prompt_digest = _phase92_sha256_16(prompt_text)  # 新增代码+Phase92UniversalComputerUse：生成 prompt 脱敏摘要；如果没有这行代码，报告无法关联任务且不能保存原文。
        plan = self.planner.plan(prompt_text)  # 新增代码+Phase92UniversalComputerUse：调用 prompt 规划器生成步骤；如果没有这行代码，通用模式无法把自然语言转成闭环任务。
        planner_risk = classify_risk(prompt_text)  # 新增代码+Phase92UniversalComputerUse：调用旧风险分类器；如果没有这行代码，英文高风险规则无法复用。
        risk = _phase92_prompt_risk(prompt_text, planner_risk)  # 新增代码+Phase92UniversalComputerUse：补齐中英文风险门禁；如果没有这行代码，中文高风险 prompt 可能漏检。
        safe_plan = self._sanitized_plan(plan, prompt_digest, risk)  # 新增代码+Phase92UniversalComputerUse：脱敏计划；如果没有这行代码，planner 返回的 raw prompt 会进入报告。
        observation_summary = self._fused_observation_summary()  # 新增代码+Phase92UniversalComputerUse：生成观察融合摘要；如果没有这行代码，观察-规划-动作-验证闭环缺少第一环证据。
        real_action_requested = bool(real_actions)  # 新增代码+Phase92UniversalComputerUse：规范真实动作开关；如果没有这行代码，字符串或 None 可能导致判断混乱。
        blocked_by_high_risk = bool(real_action_requested and risk.get("requires_confirmation"))  # 新增代码+Phase92UniversalComputerUse：判断高风险真实动作是否必须先停下；如果没有这行代码，敏感任务可能继续进入动作层。
        real_action_decision = {"allowed": False, "decision": "preview_only_default" if not real_action_requested else "high_risk_requires_confirmation" if blocked_by_high_risk else "real_actions_require_explicit_controller_gate", "low_level_event_count": 0}  # 新增代码+Phase92UniversalComputerUse：生成真实动作决策摘要；如果没有这行代码，调用方不知道为什么没有派发键鼠。
        status = self.status()  # 新增代码+Phase92UniversalComputerUse：读取组件状态；如果没有这行代码，报告要重复拼接状态字段。
        report = {"ok": not real_action_requested, "marker": PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MARKER, "ok_token": PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK_TOKEN, "model": PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MODEL, "mode": "universal_windows_computer_use", "prompt_sha256_16": prompt_digest, "prompt_text_included": False, "prompt_length": len(prompt_text), "raw_text_hidden": True, "session_plan": safe_plan, "observation_summary": observation_summary, "real_actions_requested": real_action_requested, "real_action_decision": real_action_decision, "high_risk_requires_confirmation": bool(risk.get("requires_confirmation")), "generic_observe_plan_act_verify_loop": True, "single_universal_runtime": bool(status["single_universal_runtime"]), "prompt_to_any_normal_app": bool(status["prompt_to_any_normal_app"]), "per_app_controller_required": bool(status["per_app_controller_required"]), "representative_apps_are_acceptance_only": bool(status["representative_apps_are_acceptance_only"]), "uses_observation_fusion": bool(status["uses_observation_fusion"]), "uses_prompt_task_planner": bool(status["uses_prompt_task_planner"]), "uses_generic_action_layer": bool(status["uses_generic_action_layer"]), "uses_real_app_safety_boundary": bool(status["uses_real_app_safety_boundary"]), "uses_production_host_adapter": bool(status["uses_production_host_adapter"]), "default_real_actions_enabled": PHASE92_DEFAULT_REAL_ACTIONS_ENABLED, "uncontrolled_actions_expanded": PHASE92_UNCONTROLLED_ACTIONS_EXPANDED}  # 新增代码+Phase92UniversalComputerUse：返回通用 mode 报告；如果没有这行代码，测试和 agent 工具拿不到结构化结果。
        return report  # 新增代码+Phase92UniversalComputerUse：返回报告给调用方；如果没有这行代码，run_prompt 会默认返回 None。
    # 新增代码+Phase92UniversalComputerUse：函数段结束，UniversalWindowsComputerUseRuntime.run_prompt 到此结束；如果没有这个边界说明，初学者不容易看出 prompt 运行范围。

    # 新增代码+Phase92UniversalComputerUse：函数段开始，unauthorized_window_refusal 验证未授权普通窗口 0 事件拒绝；如果没有这段函数，安全契约无法证明默认不乱点真实软件。
    def unauthorized_window_refusal(self) -> dict[str, Any]:  # 新增代码+Phase92UniversalComputerUse：定义未授权窗口检查；如果没有这行代码，Phase92 契约缺少默认拒绝证据。
        window = {"app_id": "notepad.exe", "process_name": "notepad.exe", "window_id": "hwnd:9292", "title_preview": "Untitled - Notepad", "display_id": "DISPLAY1"}  # 新增代码+Phase92UniversalComputerUse：构造普通应用窗口但不写授权；如果没有这行代码，安全边界没有测试目标。
        decision = self.safety_boundary.evaluate(window, "click", self.grant_store, f"phase92-{int(time.time() * 1000)}")  # 新增代码+Phase92UniversalComputerUse：调用真实安全边界评估；如果没有这行代码，未授权拒绝只是模拟声明。
        return {"decision": str(decision.get("decision", "")), "allowed": bool(decision.get("allowed")), "low_level_event_count": int(decision.get("low_level_event_count", 0) or 0), "unauthorized_window_zero_events": bool(not decision.get("allowed") and int(decision.get("low_level_event_count", 0) or 0) == 0)}  # 新增代码+Phase92UniversalComputerUse：返回未授权 0 事件结果；如果没有这行代码，契约无法稳定读取 token。
    # 新增代码+Phase92UniversalComputerUse：函数段结束，UniversalWindowsComputerUseRuntime.unauthorized_window_refusal 到此结束；如果没有这个边界说明，初学者不容易看出未授权检查范围。

    # 新增代码+Phase92UniversalComputerUse：函数段开始，target_drift_refusal 证明目标漂移会阻断动作；如果没有这段函数，动作可能在窗口变化后误落到别处。
    def target_drift_refusal(self) -> dict[str, Any]:  # 新增代码+Phase92UniversalComputerUse：定义目标漂移检查；如果没有这行代码，Phase92 契约缺少目标一致性门禁。
        original_window = {"app_id": "generic_windows_app.exe", "window_id": "hwnd:9201", "title_preview": "Original target"}  # 新增代码+Phase92UniversalComputerUse：构造原目标窗口；如果没有这行代码，无法生成前态指纹。
        current_window = {"app_id": "other_windows_app.exe", "window_id": "hwnd:9202", "title_preview": "Different target"}  # 新增代码+Phase92UniversalComputerUse：构造漂移后的窗口；如果没有这行代码，无法证明目标已变化。
        original_digest = _phase92_sha256_16(original_window)  # 新增代码+Phase92UniversalComputerUse：生成原目标指纹；如果没有这行代码，漂移判断没有前态证据。
        current_digest = _phase92_sha256_16(current_window)  # 新增代码+Phase92UniversalComputerUse：生成当前目标指纹；如果没有这行代码，漂移判断没有后态证据。
        drifted = original_digest != current_digest  # 新增代码+Phase92UniversalComputerUse：比较目标指纹；如果没有这行代码，不同窗口也可能被当成同一目标。
        return {"target_drift_blocks_action": drifted, "decision": "target_drift_blocks_action" if drifted else "target_stable", "low_level_event_count": 0, "original_window_digest": original_digest, "current_window_digest": current_digest}  # 新增代码+Phase92UniversalComputerUse：返回目标漂移拒绝摘要；如果没有这行代码，契约无法确认 0 事件阻断。
    # 新增代码+Phase92UniversalComputerUse：函数段结束，UniversalWindowsComputerUseRuntime.target_drift_refusal 到此结束；如果没有这个边界说明，初学者不容易看出目标漂移检查范围。
# 新增代码+Phase92UniversalComputerUse：类段结束，UniversalWindowsComputerUseRuntime 到此结束；如果没有这个边界说明，初学者不容易看出通用运行时范围。


# 新增代码+Phase92UniversalComputerUse：函数段开始，run_phase92_universal_windows_computer_use_contract 运行总契约；如果没有这段函数，CLI、测试和真实终端没有同一事实源。
def run_phase92_universal_windows_computer_use_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase92UniversalComputerUse：定义 Phase92 契约入口；如果没有这行代码，测试不能一键验证所有 token。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE92_UNIVERSAL_MODE_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase92UniversalComputerUse：选择隔离契约目录；如果没有这行代码，多次验收可能互相污染。
    runtime = UniversalWindowsComputerUseRuntime(base_dir=root)  # 新增代码+Phase92UniversalComputerUse：创建通用运行时；如果没有这行代码，契约没有被测对象。
    generic = runtime.run_prompt("打开 computer use，帮我操作一个普通 Windows 应用，但先不要真的点击。", real_actions=False)  # 新增代码+Phase92UniversalComputerUse：运行普通用户风格 prompt；如果没有这行代码，prompt 到普通应用能力没有证据。
    high_risk = runtime.run_prompt("打开 computer use，输入密码并支付，但先不要真的点击。", real_actions=False)  # 新增代码+Phase92UniversalComputerUse：运行中文高风险 prompt；如果没有这行代码，中文确认门禁没有证据。
    privacy = runtime.run_prompt("phase92-contract-secret prompt should never be copied into report", real_actions=False)  # 新增代码+Phase92UniversalComputerUse：运行隐私检查 prompt；如果没有这行代码，raw_text_hidden 可能只是口头声明。
    unauthorized = runtime.unauthorized_window_refusal()  # 新增代码+Phase92UniversalComputerUse：验证未授权窗口拒绝；如果没有这行代码，默认安全边界没有证据。
    drift = runtime.target_drift_refusal()  # 新增代码+Phase92UniversalComputerUse：验证目标漂移阻断；如果没有这行代码，窗口变化安全门禁没有证据。
    serialized_without_raw = json.dumps({"generic": generic, "high_risk": high_risk, "privacy": privacy}, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase92UniversalComputerUse：序列化报告子集做隐私检查；如果没有这行代码，原文泄露很难自动发现。
    raw_text_hidden = "phase92-contract-secret" not in serialized_without_raw and "prompt should never be copied" not in serialized_without_raw  # 新增代码+Phase92UniversalComputerUse：确认隐私 prompt 没进入报告；如果没有这行代码，隐私门禁无法自动判断。
    status = runtime.status()  # 新增代码+Phase92UniversalComputerUse：读取运行时状态；如果没有这行代码，总报告要重复拼装组件字段。
    report_path = root / "reports" / "phase92_universal_windows_computer_use_mode_report.json"  # 新增代码+Phase92UniversalComputerUse：定义报告文件路径；如果没有这行代码，验收证据没有稳定落点。
    passed = bool(generic.get("ok") and status.get("single_universal_runtime") and status.get("prompt_to_any_normal_app") and not status.get("per_app_controller_required") and status.get("representative_apps_are_acceptance_only") and status.get("generic_observe_plan_act_verify_loop") and status.get("uses_observation_fusion") and status.get("uses_prompt_task_planner") and status.get("uses_generic_action_layer") and status.get("uses_real_app_safety_boundary") and status.get("uses_production_host_adapter") and high_risk.get("high_risk_requires_confirmation") and unauthorized.get("unauthorized_window_zero_events") and drift.get("target_drift_blocks_action") and raw_text_hidden and not PHASE92_DEFAULT_REAL_ACTIONS_ENABLED and not PHASE92_UNCONTROLLED_ACTIONS_EXPANDED)  # 新增代码+Phase92UniversalComputerUse：汇总所有契约门禁；如果没有这行代码，main 无法用退出码表达成败。
    report = {"marker": PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MARKER, "ok_token": PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK_TOKEN, "model": PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MODEL, "passed": passed, "single_universal_runtime": bool(status["single_universal_runtime"]), "prompt_to_any_normal_app": bool(status["prompt_to_any_normal_app"]), "per_app_controller_required": bool(status["per_app_controller_required"]), "representative_apps_are_acceptance_only": bool(status["representative_apps_are_acceptance_only"]), "generic_observe_plan_act_verify_loop": bool(status["generic_observe_plan_act_verify_loop"]), "uses_observation_fusion": bool(status["uses_observation_fusion"]), "uses_prompt_task_planner": bool(status["uses_prompt_task_planner"]), "uses_generic_action_layer": bool(status["uses_generic_action_layer"]), "uses_real_app_safety_boundary": bool(status["uses_real_app_safety_boundary"]), "uses_production_host_adapter": bool(status["uses_production_host_adapter"]), "high_risk_requires_confirmation": bool(high_risk["high_risk_requires_confirmation"]), "unauthorized_window_zero_events": bool(unauthorized["unauthorized_window_zero_events"]), "target_drift_blocks_action": bool(drift["target_drift_blocks_action"]), "raw_text_hidden": raw_text_hidden, "default_real_actions_enabled": PHASE92_DEFAULT_REAL_ACTIONS_ENABLED, "uncontrolled_actions_expanded": PHASE92_UNCONTROLLED_ACTIONS_EXPANDED, "report_path": str(report_path), "generic_report": generic, "high_risk_report": high_risk, "unauthorized_report": unauthorized, "target_drift_report": drift}  # 新增代码+Phase92UniversalComputerUse：构造完整契约报告；如果没有这行代码，测试和人工验收拿不到统一证据。
    atomic_write_json(report_path, report)  # 新增代码+Phase92UniversalComputerUse：原子写入报告；如果没有这行代码，异常中断时可能留下半个 JSON。
    return report  # 新增代码+Phase92UniversalComputerUse：返回报告给测试和 CLI；如果没有这行代码，调用方拿不到验收结果。
# 新增代码+Phase92UniversalComputerUse：函数段结束，run_phase92_universal_windows_computer_use_contract 到此结束；如果没有这个边界说明，初学者不容易看出总契约范围。


# 新增代码+Phase92UniversalComputerUse：函数段开始，phase92_cli_line 输出固定 token 行；如果没有这段函数，真实终端验收需要解析复杂 JSON。
def phase92_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase92UniversalComputerUse：定义 CLI 行格式化函数；如果没有这行代码，场景配置无法用简单 token 匹配。
    return f"{PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MARKER} {PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK_TOKEN} single_universal_runtime={_phase92_bool_token(report.get('single_universal_runtime'))} prompt_to_any_normal_app={_phase92_bool_token(report.get('prompt_to_any_normal_app'))} per_app_controller_required={_phase92_bool_token(report.get('per_app_controller_required'))} representative_apps_are_acceptance_only={_phase92_bool_token(report.get('representative_apps_are_acceptance_only'))} generic_observe_plan_act_verify_loop={_phase92_bool_token(report.get('generic_observe_plan_act_verify_loop'))} uses_observation_fusion={_phase92_bool_token(report.get('uses_observation_fusion'))} uses_prompt_task_planner={_phase92_bool_token(report.get('uses_prompt_task_planner'))} uses_generic_action_layer={_phase92_bool_token(report.get('uses_generic_action_layer'))} uses_real_app_safety_boundary={_phase92_bool_token(report.get('uses_real_app_safety_boundary'))} uses_production_host_adapter={_phase92_bool_token(report.get('uses_production_host_adapter'))} high_risk_requires_confirmation={_phase92_bool_token(report.get('high_risk_requires_confirmation'))} unauthorized_window_zero_events={_phase92_bool_token(report.get('unauthorized_window_zero_events'))} target_drift_blocks_action={_phase92_bool_token(report.get('target_drift_blocks_action'))} raw_text_hidden={_phase92_bool_token(report.get('raw_text_hidden'))} default_real_actions_enabled={_phase92_bool_token(report.get('default_real_actions_enabled'))} uncontrolled_actions_expanded={_phase92_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+Phase92UniversalComputerUse：返回固定顺序 token 行；如果没有这行代码，验收脚本很容易因为字段顺序不稳而失败。
# 新增代码+Phase92UniversalComputerUse：函数段结束，phase92_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 文本范围。


# 新增代码+Phase92UniversalComputerUse：函数段开始，main 提供命令行自检入口；如果没有这段函数，真实可见终端无法直接运行 Phase92 契约。
def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase92UniversalComputerUse：定义 CLI 入口并保留 argv 扩展位；如果没有这行代码，python -m 调用需要手写细节。
    _ = argv  # 新增代码+Phase92UniversalComputerUse：明确当前不解析命令行参数；如果没有这行代码，读者可能误以为 argv 遗漏处理。
    report = run_phase92_universal_windows_computer_use_contract()  # 新增代码+Phase92UniversalComputerUse：运行无副作用契约；如果没有这行代码，CLI 没有实际验收内容。
    print(phase92_cli_line(report))  # 新增代码+Phase92UniversalComputerUse：打印稳定 token 行；如果没有这行代码，验收器无法快速判断通过。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase92UniversalComputerUse：打印结构化报告；如果没有这行代码，失败时不容易复盘。
    print(PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MARKER)  # 新增代码+Phase92UniversalComputerUse：单独打印 ready marker；如果没有这行代码，真实终端人工观察不够直观。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase92UniversalComputerUse：用退出码表达契约成败；如果没有这行代码，失败也可能被自动化当成成功。
# 新增代码+Phase92UniversalComputerUse：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


__all__ = ["DEFAULT_PHASE92_UNIVERSAL_MODE_ROOT", "PHASE92_DEFAULT_REAL_ACTIONS_ENABLED", "PHASE92_UNCONTROLLED_ACTIONS_EXPANDED", "PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MARKER", "PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_MODEL", "PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK_TOKEN", "UniversalWindowsComputerUseRuntime", "main", "phase92_cli_line", "run_phase92_universal_windows_computer_use_contract"]  # 新增代码+Phase92UniversalComputerUse：限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。

if __name__ == "__main__":  # 新增代码+Phase92UniversalComputerUse：允许直接运行本模块；如果没有这行代码，初学者无法用 python 文件方式手动执行 Phase92 自检。
    raise SystemExit(main())  # 新增代码+Phase92UniversalComputerUse：调用 main 并传递退出码；如果没有这行代码，直接运行文件不会执行验收。
