"""Phase137 受控 Windows Calculator 真实求和合同。"""  # 新增代码+Phase137CalculatorLiveSum: 说明本文件只负责 Calculator 代表应用验收；如果没有这行代码，读者难以区分它和通用 Computer Use 控制器。
from __future__ import annotations  # 新增代码+Phase137CalculatorLiveSum: 启用延迟类型解析，避免前向类型标注在旧导入顺序下出错；如果没有这行代码，部分类型提示可能在运行时过早求值。
import hashlib  # 新增代码+Phase137CalculatorLiveSum: 导入哈希库用于脱敏指纹；如果没有这行代码，报告要么泄露原始文本，要么缺少可审计指纹。
import json  # 新增代码+Phase137CalculatorLiveSum: 导入 JSON 用于报告写入和泄露扫描；如果没有这行代码，合同结果无法稳定落盘。
import os  # 新增代码+Phase137CalculatorLiveSum: 导入 os 用于读取双环境门；如果没有这行代码，真实 Calculator 路径无法被显式开关控制。
import subprocess  # 新增代码+Phase137CalculatorLiveSum: 导入 subprocess 用于启动 calc.exe；如果没有这行代码，验收无法自己打开受控 Calculator。
import sys  # 新增代码+Phase137CalculatorLiveSum: 导入 sys 用于平台判断；如果没有这行代码，非 Windows 环境可能误触发 Win32 行为。
import time  # 新增代码+Phase137CalculatorLiveSum: 导入 time 用于轮询窗口和生成隔离目录；如果没有这行代码，启动等待和报告目录会不稳定。
from pathlib import Path  # 新增代码+Phase137CalculatorLiveSum: 导入 Path 统一处理 Windows 路径；如果没有这行代码，报告路径拼接容易脆弱。
from typing import Any  # 新增代码+Phase137CalculatorLiveSum: 导入 Any 描述动态 JSON 报告；如果没有这行代码，公开接口类型边界不清楚。

try:  # 新增代码+Phase137CalculatorLiveSum: 优先按包路径导入项目内组件；如果没有这段代码，单测和真实终端不能共享同一套实现。
    from learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # 新增代码+Phase137CalculatorLiveSum: 复用现有 Computer Use 运行根目录；如果没有这行代码，Calculator 报告会散落到未知位置。
    from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+Phase137CalculatorLiveSum: 复用真实 SendInput sender；如果没有这行代码，Calculator 可能退回假 sender。
    from learning_agent.computer_use_mcp_v2.windows_runtime.real_uia_locator import PowerShellUiaTreeProvider  # 新增代码+Phase137CalculatorLiveSum: 复用 PowerShell/.NET UIA provider 读取结果；如果没有这行代码，结果验证只能靠盲猜。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_real_observation import UniversalRealObservationFrameRuntime  # 新增代码+Phase137CalculatorLiveSum: 复用真实观察帧生成截图/UIA/window 状态摘要；如果没有这行代码，Phase8 证据会缺观察链。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase137CalculatorLiveSum: 复用真实窗口枚举器；如果没有这行代码，驱动无法定位 Calculator 窗口。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase137CalculatorLiveSum: 复用原子 JSON 写入；如果没有这行代码，验收中断可能留下半截报告。
except ModuleNotFoundError as error:  # 新增代码+Phase137CalculatorLiveSum: 兼容 start_oauth_agent.bat 可能从 learning_agent 目录直接运行；如果没有这段代码，真实可见终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants", "learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard", "learning_agent.computer_use_mcp_v2.windows_runtime.real_uia_locator", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_real_observation", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase137CalculatorLiveSum: 只兜底包路径缺失，避免吞掉真实内部 bug；如果没有这行代码，依赖内部错误会被误判为脚本模式问题。
        raise  # 新增代码+Phase137CalculatorLiveSum: 重新抛出非路径类导入错误；如果没有这行代码，排查底层模块 bug 会很困难。
    from computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # type: ignore  # 新增代码+Phase137CalculatorLiveSum: 脚本模式下复用运行根目录；如果没有这行代码，bat 入口无法定位报告目录。
    from computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # type: ignore  # 新增代码+Phase137CalculatorLiveSum: 脚本模式下导入真实 sender；如果没有这行代码，bat 入口无法发送真实按键。
    from computer_use_mcp_v2.windows_runtime.real_uia_locator import PowerShellUiaTreeProvider  # type: ignore  # 新增代码+Phase137CalculatorLiveSum: 脚本模式下导入 UIA provider；如果没有这行代码，bat 入口无法验证结果。
    from computer_use_mcp_v2.windows_runtime.universal_real_observation import UniversalRealObservationFrameRuntime  # type: ignore  # 新增代码+Phase137CalculatorLiveSum: 脚本模式下导入观察帧 runtime；如果没有这行代码，bat 入口无法形成观察证据。
    from computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # type: ignore  # 新增代码+Phase137CalculatorLiveSum: 脚本模式下导入窗口枚举器；如果没有这行代码，bat 入口无法找到 Calculator。
    from runtime.files import atomic_write_json  # type: ignore  # 新增代码+Phase137CalculatorLiveSum: 脚本模式下导入原子写入；如果没有这行代码，报告可能写坏。

PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_MARKER = "PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_READY"  # 新增代码+Phase137CalculatorLiveSum: 定义真实终端验收等待的 ready marker；如果没有这行代码，controller 没有稳定锚点。
PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_OK_TOKEN = "PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_OK"  # 新增代码+Phase137CalculatorLiveSum: 定义成功 token；如果没有这行代码，失败和成功输出无法稳定区分。
PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_MODEL = "phase137_controlled_calculator_live_sum"  # 新增代码+Phase137CalculatorLiveSum: 定义报告模型名；如果没有这行代码，后续矩阵无法识别合同版本。
PHASE137_REAL_CALCULATOR_SUM_ENV = "LEARNING_AGENT_PHASE137_ENABLE_REAL_CALCULATOR_SUM"  # 新增代码+Phase137CalculatorLiveSum: 定义允许真实 Calculator 动作的第二道门；如果没有这行代码，真实桌面动作缺少显式授权。
PHASE137_REAL_CALCULATOR_SUM_REQUEST_ENV = "LEARNING_AGENT_PHASE137_RUN_REAL_CALCULATOR_SUM"  # 新增代码+Phase137CalculatorLiveSum: 定义请求真实 Calculator 动作的第一道门；如果没有这行代码，CLI 无法表达本次确实要跑真实路径。
PHASE137_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase137CalculatorLiveSum: 声明本合同没有开放无边界桌面动作；如果没有这行代码，能力范围容易被误读成泛化放权。
DEFAULT_PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_ROOT = DEFAULT_PERSISTENT_GRANTS_ROOT.parent / "phase137_controlled_calculator_live_sum"  # 新增代码+Phase137CalculatorLiveSum: 定义默认报告根目录；如果没有这行代码，真实验收证据没有固定落点。

def _phase137_bool_token(value: Any) -> str:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+Phase137CalculatorLiveSum: 返回 true 或 false 文本；如果没有这行代码，验收脚本的字符串匹配会不稳定。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。

def _phase137_env_enabled(name: str) -> bool:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，统一判断环境变量是否显式为真；如果没有这段函数，双门解析会散落重复。
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase137CalculatorLiveSum: 只接受明确真值；如果没有这行代码，模糊环境值可能误开真实桌面动作。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_env_enabled 到此结束；如果没有这个边界说明，初学者不容易看出环境门范围。

def _phase137_request_real_run(explicit_value: bool | None = None) -> bool:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，判断本次是否请求真实 Calculator；如果没有这段函数，测试参数和环境变量入口会漂移。
    if explicit_value is not None:  # 新增代码+Phase137CalculatorLiveSum: 调用方传入显式值时优先使用；如果没有这行代码，单测无法稳定覆盖真实请求分支。
        return bool(explicit_value)  # 新增代码+Phase137CalculatorLiveSum: 返回显式请求布尔值；如果没有这行代码，传参不会生效。
    return _phase137_env_enabled(PHASE137_REAL_CALCULATOR_SUM_REQUEST_ENV)  # 新增代码+Phase137CalculatorLiveSum: 没有显式值时读取请求环境门；如果没有这行代码，CLI 无法请求真实 Calculator 路径。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_request_real_run 到此结束；如果没有这个边界说明，初学者不容易看出请求门范围。

def _phase137_real_gate_enabled(explicit_value: bool | None = None) -> bool:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，判断真实 Calculator 是否被允许；如果没有这段函数，第二道安全门会分散且难审计。
    if explicit_value is not None:  # 新增代码+Phase137CalculatorLiveSum: 调用方传入显式允许值时优先使用；如果没有这行代码，单测无法安全打开 gated 分支。
        return bool(explicit_value)  # 新增代码+Phase137CalculatorLiveSum: 返回显式允许布尔值；如果没有这行代码，传参不会生效。
    return _phase137_env_enabled(PHASE137_REAL_CALCULATOR_SUM_ENV)  # 新增代码+Phase137CalculatorLiveSum: 没有显式值时读取允许环境门；如果没有这行代码，CLI 真实路径缺少第二道确认。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_real_gate_enabled 到此结束；如果没有这个边界说明，初学者不容易看出允许门范围。

def _phase137_sha256_16(value: Any) -> str:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，生成短哈希用于脱敏审计；如果没有这段函数，报告无法安全证明读到过某些内容。
    text = str(value or "")  # 新增代码+Phase137CalculatorLiveSum: 把动态输入规整成字符串；如果没有这行代码，None 或数字输入的哈希不稳定。
    if not text:  # 新增代码+Phase137CalculatorLiveSum: 空值不生成哈希；如果没有这行代码，空输入也会看起来像有内容。
        return ""  # 新增代码+Phase137CalculatorLiveSum: 返回空哈希；如果没有这行代码，调用方无法区分空值。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase137CalculatorLiveSum: 返回前 16 位 SHA256；如果没有这行代码，脱敏指纹不可用。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出哈希范围。

def _phase137_safe_int(value: Any) -> int:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，把动态值安全转成整数；如果没有这段函数，坏 JSON 字段可能让合同崩溃。
    try:  # 新增代码+Phase137CalculatorLiveSum: 捕获无法转换的输入；如果没有这行代码，坏窗口字段会抛异常。
        return int(value or 0)  # 新增代码+Phase137CalculatorLiveSum: 返回整数或 0；如果没有这行代码，低层事件计数和 hwnd 无法稳定使用。
    except (TypeError, ValueError):  # 新增代码+Phase137CalculatorLiveSum: 处理坏类型和值错误；如果没有这行代码，动态证据不能容错。
        return 0  # 新增代码+Phase137CalculatorLiveSum: 坏值按 0 处理；如果没有这行代码，调用方要重复兜底。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出整数清洗范围。

def _phase137_safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，把外部值安全整理成字典；如果没有这段函数，坏 driver 输出会让 builder 崩溃。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+Phase137CalculatorLiveSum: 只接受 dict 并复制；如果没有这行代码，外部可变对象可能污染内部报告。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_safe_dict 到此结束；如果没有这个边界说明，初学者不容易看出字典清洗范围。

def _phase137_get_window_field(window: Any, name: str) -> Any:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，统一读取 dict 或对象窗口字段；如果没有这段函数，fake 和真实窗口读取会分裂。
    if isinstance(window, dict):  # 新增代码+Phase137CalculatorLiveSum: 优先处理 dict 窗口；如果没有这行代码，注入测试窗口无法读取。
        return window.get(name)  # 新增代码+Phase137CalculatorLiveSum: 从字典读取字段；如果没有这行代码，dict 会被当成普通对象。
    return getattr(window, name, None)  # 新增代码+Phase137CalculatorLiveSum: 从对象属性读取字段；如果没有这行代码，未来对象窗口无法复用。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_get_window_field 到此结束；如果没有这个边界说明，初学者不容易看出字段读取范围。

def _phase137_hwnd_from_window(window: Any) -> int:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，从窗口摘要里取 hwnd；如果没有这段函数，SetForegroundWindow 没有目标。
    explicit_hwnd = _phase137_safe_int(_phase137_get_window_field(window, "hwnd"))  # 新增代码+Phase137CalculatorLiveSum: 优先读取 hwnd 字段；如果没有这行代码，真实 inventory 的句柄可能被忽略。
    if explicit_hwnd > 0:  # 新增代码+Phase137CalculatorLiveSum: 检查显式 hwnd 是否有效；如果没有这行代码，0 句柄会被误用。
        return explicit_hwnd  # 新增代码+Phase137CalculatorLiveSum: 返回真实 hwnd；如果没有这行代码，后续只能解析 window_id。
    window_id = str(_phase137_get_window_field(window, "window_id") or "")  # 新增代码+Phase137CalculatorLiveSum: 读取 window_id 作为兜底；如果没有这行代码，只有 hwnd:123 形式的窗口无法使用。
    return _phase137_safe_int(window_id.split(":", 1)[1]) if window_id.startswith("hwnd:") and ":" in window_id else 0  # 新增代码+Phase137CalculatorLiveSum: 从 hwnd:123 解析句柄；如果没有这行代码，协议窗口 id 无法转 Win32 句柄。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_hwnd_from_window 到此结束；如果没有这个边界说明，初学者不容易看出 hwnd 解析范围。

def _phase137_window_text_blob(window: Any) -> str:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，拼出用于识别 Calculator 的窗口文本；如果没有这段函数，目标识别逻辑会散落。
    fields = ["app_id", "process_name", "class_name", "title_preview", "title", "window_id"]  # 新增代码+Phase137CalculatorLiveSum: 列出身份判断需要的字段；如果没有这行代码，某些窗口线索可能漏检。
    return " ".join(str(_phase137_get_window_field(window, field) or "") for field in fields).lower()  # 新增代码+Phase137CalculatorLiveSum: 合并并小写窗口字段；如果没有这行代码，大小写差异会导致误判。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_window_text_blob 到此结束；如果没有这个边界说明，初学者不容易看出窗口识别文本范围。

def _phase137_is_calculator_window(window: Any) -> bool:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，判断窗口是否像 Windows Calculator；如果没有这段函数，按键可能发到错误窗口。
    blob = _phase137_window_text_blob(window)  # 新增代码+Phase137CalculatorLiveSum: 读取窗口身份文本；如果没有这行代码，判断没有输入。
    has_calculator_identity = bool("calculator" in blob or "calc.exe" in blob)  # 修改代码+Phase137CalculatorLiveSum: 只接受明确 Calculator/calc 线索；如果没有这行代码，空标题 ApplicationFrameWindow 会被误当成 Calculator。
    has_forbidden_identity = any(token in blob for token in ("codex", "powershell", "terminal", "cmd.exe"))  # 修改代码+Phase137CalculatorLiveSum: 集中排除终端和 Codex 等敏感窗口；如果没有这行代码，安全边界会被同名外壳窗口绕过。
    return bool(has_calculator_identity and not has_forbidden_identity)  # 修改代码+Phase137CalculatorLiveSum: 同时要求明确身份和非敏感目标；如果没有这行代码，driver 可能向错误窗口发送真实按键。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_is_calculator_window 到此结束；如果没有这个边界说明，初学者不容易看出 Calculator 目标边界。

def _phase137_window_identity(window: Any) -> dict[str, Any]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，生成不含完整标题正文的窗口身份摘要；如果没有这段函数，报告可能泄露窗口标题或缺可审计身份。
    title = str(_phase137_get_window_field(window, "title_preview") or _phase137_get_window_field(window, "title") or "")  # 新增代码+Phase137CalculatorLiveSum: 读取标题只用于长度和哈希；如果没有这行代码，目标身份缺少标题线索。
    return {"app_id": str(_phase137_get_window_field(window, "app_id") or ""), "process_name": str(_phase137_get_window_field(window, "process_name") or ""), "class_name": str(_phase137_get_window_field(window, "class_name") or ""), "window_id": str(_phase137_get_window_field(window, "window_id") or ""), "hwnd": _phase137_hwnd_from_window(window), "pid": _phase137_safe_int(_phase137_get_window_field(window, "pid") or _phase137_get_window_field(window, "process_id")), "title_preview": "Calculator" if "calculator" in title.lower() else "", "title_length": len(title), "title_sha256_16": _phase137_sha256_16(title)}  # 新增代码+Phase137CalculatorLiveSum: 返回脱敏身份摘要；如果没有这行代码，Phase8 无法确认动作绑定到具体窗口。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_window_identity 到此结束；如果没有这个边界说明，初学者不容易看出身份摘要范围。

def _phase137_default_off_report() -> dict[str, Any]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，生成默认关闭零事件证据；如果没有这段函数，安全默认值只能靠口头承诺。
    return {"decision": "real_calculator_sum_disabled_by_default", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase137CalculatorLiveSum: 返回默认关闭证据；如果没有这行代码，报告无法证明普通运行不会碰桌面。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_default_off_report 到此结束；如果没有这个边界说明，初学者不容易看出默认安全检查范围。

def _phase137_unsafe_target_report() -> dict[str, Any]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，生成危险目标零事件证据；如果没有这段函数，终端窗口拒绝没有审计样本。
    return {"decision": "unsafe_target_rejected", "target": "terminal_like_window", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase137CalculatorLiveSum: 返回危险目标拒绝证据；如果没有这行代码，报告无法证明不会向终端发键。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_unsafe_target_report 到此结束；如果没有这个边界说明，初学者不容易看出危险目标检查范围。

def _phase137_report_raw_hidden(report_without_raw_check: dict[str, Any], raw_prompt_text: str | None) -> bool:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，检查报告没有用户原始 prompt；如果没有这段函数，隐私门禁没有统一事实检查。
    raw_prompt = str(raw_prompt_text or "")  # 新增代码+Phase137CalculatorLiveSum: 规整可选 prompt 文本；如果没有这行代码，None 会导致 in 检查异常。
    serialized = json.dumps(report_without_raw_check, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase137CalculatorLiveSum: 序列化报告用于全文扫描；如果没有这行代码，嵌套字段泄露可能漏检。
    return bool(not raw_prompt or raw_prompt not in serialized)  # 新增代码+Phase137CalculatorLiveSum: 原始 prompt 不存在才通过；如果没有这行代码，用户敏感输入可能写入 artifact。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_report_raw_hidden 到此结束；如果没有这个边界说明，初学者不容易看出脱敏检查范围。

def _phase137_tree_names(node: Any) -> list[str]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，递归收集 UIA 节点名称用于内部结果验证；如果没有这段函数，Calculator 结果只能靠 driver 自报。
    if not isinstance(node, dict):  # 新增代码+Phase137CalculatorLiveSum: 只处理字典节点；如果没有这行代码，坏 UIA 树会抛异常。
        return []  # 新增代码+Phase137CalculatorLiveSum: 非字典节点返回空列表；如果没有这行代码，递归没有稳定兜底。
    names = [str(node.get("name") or "")]  # 新增代码+Phase137CalculatorLiveSum: 收集当前节点名称；如果没有这行代码，显示文本不会进入内部判断。
    for child in list(node.get("children", []) or []):  # 新增代码+Phase137CalculatorLiveSum: 遍历子节点；如果没有这行代码，只能看到根节点。
        names.extend(_phase137_tree_names(child))  # 新增代码+Phase137CalculatorLiveSum: 合并子节点名称；如果没有这行代码，Calculator 显示区域可能漏检。
    return names  # 新增代码+Phase137CalculatorLiveSum: 返回名称列表；如果没有这行代码，调用方拿不到扫描输入。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_tree_names 到此结束；如果没有这个边界说明，初学者不容易看出 UIA 扫描范围。

def _phase137_result_seen_in_tree(tree_result: dict[str, Any], expected_result: str) -> tuple[bool, dict[str, Any]]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，在 UIA 树里查找 Calculator 结果；如果没有这段函数，观察结果无法验证。
    names = _phase137_tree_names(_phase137_safe_dict(tree_result).get("tree", {}))  # 新增代码+Phase137CalculatorLiveSum: 提取 UIA 名称列表；如果没有这行代码，结果判断没有文本来源。
    lowered = [name.lower().strip() for name in names if name.strip()]  # 新增代码+Phase137CalculatorLiveSum: 清洗名称用于匹配；如果没有这行代码，大小写和空白会影响结果。
    expected = str(expected_result).strip().lower()  # 新增代码+Phase137CalculatorLiveSum: 清洗期望结果；如果没有这行代码，数字结果比较不稳定。
    exact_seen = expected in lowered  # 新增代码+Phase137CalculatorLiveSum: 检查是否有节点名称正好等于结果；如果没有这行代码，最可靠的匹配路径缺失。
    display_seen = any(("display" in name or "显示" in name) and expected in name for name in lowered)  # 新增代码+Phase137CalculatorLiveSum: 检查显示区域是否包含结果；如果没有这行代码，Windows Calculator 常见 “Display is 2” 会漏检。
    summary = {"captured": bool(tree_result.get("captured")), "node_count": _phase137_safe_int(tree_result.get("node_count")), "truncated": bool(tree_result.get("truncated")), "name_count": len(lowered), "names_sha256_16": _phase137_sha256_16("|".join(lowered)), "raw_text_included": False}  # 新增代码+Phase137CalculatorLiveSum: 返回脱敏扫描摘要；如果没有这行代码，报告无法说明验证来源且可能泄露原文。
    return bool(exact_seen or display_seen), summary  # 新增代码+Phase137CalculatorLiveSum: 返回是否看到结果和摘要；如果没有这行代码，调用方无法汇总验证结论。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_result_seen_in_tree 到此结束；如果没有这个边界说明，初学者不容易看出结果验证范围。

def _phase137_observation_summary(frame: dict[str, Any], state_changed_after_action: bool = False) -> dict[str, Any]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，把真实观察帧压成 Phase8 友好摘要；如果没有这段函数，报告会过大或泄露细节。
    safe_frame = _phase137_safe_dict(frame)  # 新增代码+Phase137CalculatorLiveSum: 清洗观察帧；如果没有这行代码，坏观察 provider 输出会导致异常。
    return {"screenshot_captured": bool(safe_frame.get("screenshot_observation") or safe_frame.get("screenshot_artifact_openable")), "uia_tree_observation": bool(safe_frame.get("uia_tree_observation") or safe_frame.get("uia_or_vision_targeting")), "window_state_observation": bool(safe_frame.get("window_state_observation") or safe_frame.get("real_window_inventory")), "state_changed_after_action": bool(state_changed_after_action), "raw_text_included": bool(safe_frame.get("raw_text_included")), "observation_frame_model": str(safe_frame.get("model", "")), "screenshot_artifact_openable": bool(safe_frame.get("screenshot_artifact_openable")), "pixel_guard_passed": bool(safe_frame.get("pixel_guard_passed"))}  # 新增代码+Phase137CalculatorLiveSum: 返回脱敏观察摘要；如果没有这行代码，最终矩阵拿不到前后观察字段。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_observation_summary 到此结束；如果没有这个边界说明，初学者不容易看出观察摘要范围。

def _phase137_phase8_observation(source: dict[str, Any], include_state_change: bool = False) -> dict[str, Any]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，把本合同观察字段转成 Phase8 字段；如果没有这段函数，builder 格式会漂移。
    observation = {"screenshot_captured": bool(source.get("screenshot_captured")), "uia_tree_observation": bool(source.get("uia_tree_observation") or source.get("uia_or_vision_targeting") or source.get("vision_targeting")), "window_state_observation": bool(source.get("window_state_observation"))}  # 新增代码+Phase137CalculatorLiveSum: 转换基础观察字段；如果没有这行代码，前后观察无法进入最终矩阵。
    if include_state_change:  # 新增代码+Phase137CalculatorLiveSum: 只有 after 观察需要状态变化字段；如果没有这行代码，before 也会出现无意义变化字段。
        observation["state_changed_after_action"] = bool(source.get("state_changed_after_action"))  # 新增代码+Phase137CalculatorLiveSum: 添加动作后状态变化；如果没有这行代码，Phase8 会拒绝缺少变化证据。
    return observation  # 新增代码+Phase137CalculatorLiveSum: 返回 Phase8 观察摘要；如果没有这行代码，builder 调用没有结果。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_phase8_observation 到此结束；如果没有这个边界说明，初学者不容易看出观察转换范围。

def _phase137_phase8_target_identity(target_window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，把目标窗口摘要转成 Phase8 身份；如果没有这段函数，最终矩阵无法确认目标。
    return {"window_id": str(target_window.get("window_id") or ""), "hwnd": _phase137_safe_int(target_window.get("hwnd")), "process_name": str(target_window.get("process_name") or target_window.get("app_id") or "calculator"), "title_preview": str(target_window.get("title_preview") or "Calculator")}  # 新增代码+Phase137CalculatorLiveSum: 返回 Phase8 需要的目标字段；如果没有这行代码，target_identity 会缺 id 或进程/标题线索。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_phase8_target_identity 到此结束；如果没有这个边界说明，初学者不容易看出目标转换范围。

def _phase137_sender_kind_from_result(sender: Any, result: dict[str, Any]) -> str:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，从发送结果提取 sender 身份；如果没有这段函数，fake 和真实 sender 难区分。
    kind = str(result.get("sender_kind") or result.get("sender") or "")  # 新增代码+Phase137CalculatorLiveSum: 优先读取 sender 上报字段；如果没有这行代码，真实 sender 身份不会进入报告。
    return kind or type(sender).__name__  # 新增代码+Phase137CalculatorLiveSum: 没有字段时回退类名；如果没有这行代码，报告可能缺 sender_kind。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_sender_kind_from_result 到此结束；如果没有这个边界说明，初学者不容易看出 sender 身份来源。

def _phase137_sender_is_physical(sender_kind: str, low_level_event_count: int, result: dict[str, Any]) -> bool:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，判断 sender 是否真实物理派发；如果没有这段函数，记录器可能冒充真实键盘。
    lowered = str(sender_kind or "").lower()  # 新增代码+Phase137CalculatorLiveSum: 标准化 sender 名称；如果没有这行代码，大小写会影响判断。
    return bool(low_level_event_count > 0 and "windows_sendinput" in lowered and "record" not in lowered and "fake" not in lowered and result.get("ok"))  # 新增代码+Phase137CalculatorLiveSum: 要求事件数、真实 sender 名称和发送成功；如果没有这行代码，空动作或 fake sender 可能误过。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，_phase137_sender_is_physical 到此结束；如果没有这个边界说明，初学者不容易看出真实 sender 判断范围。

class Phase137WindowsCalculatorLiveSumDriver:  # 新增代码+Phase137CalculatorLiveSum: 类段开始，执行受控真实 Calculator 1+1 验收；如果没有这个类，CLI 双门打开后没有真实 driver。
    def __init__(self, inventory: Any | None = None, sender: Any | None = None, observation_runtime: Any | None = None, uia_provider: Any | None = None, launch_command: list[str] | None = None, timeout_seconds: float = 10.0) -> None:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，注入或创建真实依赖；如果没有这段函数，单测无法替换依赖且生产路径无法启动。
        self.inventory = inventory if inventory is not None else WindowsWindowInventoryProbe()  # 新增代码+Phase137CalculatorLiveSum: 保存窗口枚举器；如果没有这行代码，driver 找不到 Calculator。
        self.sender = sender if sender is not None else WindowsSendInputLowLevelSender()  # 新增代码+Phase137CalculatorLiveSum: 保存真实 SendInput sender；如果没有这行代码，动作无法触达桌面。
        self.observation_runtime = observation_runtime if observation_runtime is not None else UniversalRealObservationFrameRuntime(inventory_probe=self.inventory)  # 新增代码+Phase137CalculatorLiveSum: 保存真实观察 runtime 并共享 inventory；如果没有这行代码，前后观察可能看不同事实源。
        self.uia_provider = uia_provider if uia_provider is not None else PowerShellUiaTreeProvider()  # 新增代码+Phase137CalculatorLiveSum: 保存 UIA provider 用于结果验证；如果没有这行代码，结果只能靠视觉外观猜测。
        self.launch_command = list(launch_command or ["calc.exe"])  # 新增代码+Phase137CalculatorLiveSum: 保存启动命令；如果没有这行代码，driver 不知道如何打开 Calculator。
        self.timeout_seconds = max(1.0, float(timeout_seconds))  # 新增代码+Phase137CalculatorLiveSum: 保存并限制最小超时；如果没有这行代码，窗口轮询可能立即失败。
    # 新增代码+Phase137CalculatorLiveSum: 函数段结束，Phase137WindowsCalculatorLiveSumDriver.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出依赖初始化范围。

    def _snapshot_windows(self) -> list[dict[str, Any]]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，读取当前窗口列表；如果没有这段函数，真实和 fake inventory 形态无法统一。
        snapshot = self.inventory.snapshot()  # 新增代码+Phase137CalculatorLiveSum: 调用 inventory 快照；如果没有这行代码，无法知道桌面窗口状态。
        return [dict(window) for window in list(getattr(snapshot, "windows", []) if not isinstance(snapshot, dict) else snapshot.get("windows", [])) if isinstance(window, dict)]  # 新增代码+Phase137CalculatorLiveSum: 统一返回窗口字典列表；如果没有这行代码，后续匹配要处理多种结构。
    # 新增代码+Phase137CalculatorLiveSum: 函数段结束，Phase137WindowsCalculatorLiveSumDriver._snapshot_windows 到此结束；如果没有这个边界说明，初学者不容易看出快照读取范围。

    def _find_calculator_window(self, baseline_ids: set[str]) -> tuple[dict[str, Any] | None, bool]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，查找 Calculator 窗口并判断是否本次新开；如果没有这段函数，driver 可能控制错误窗口。
        windows = self._snapshot_windows()  # 新增代码+Phase137CalculatorLiveSum: 获取当前窗口列表；如果没有这行代码，查找没有数据来源。
        calculator_windows = [window for window in windows if _phase137_is_calculator_window(window)]  # 新增代码+Phase137CalculatorLiveSum: 过滤 Calculator 候选；如果没有这行代码，终端等窗口可能被误控。
        for window in calculator_windows:  # 新增代码+Phase137CalculatorLiveSum: 优先遍历候选窗口；如果没有这行代码，无法选择新窗口。
            if str(window.get("window_id") or "") not in baseline_ids:  # 新增代码+Phase137CalculatorLiveSum: 优先使用本次启动后新出现的窗口；如果没有这行代码，可能复用用户原有 Calculator。
                return dict(window), True  # 新增代码+Phase137CalculatorLiveSum: 返回新窗口和 owned 标记；如果没有这行代码，清理阶段不知道能否关闭。
        return (dict(calculator_windows[0]), False) if calculator_windows else (None, False)  # 新增代码+Phase137CalculatorLiveSum: 找不到新窗口时可回退已有 Calculator；如果没有这行代码，单实例 Calculator 可能无法验收。
    # 新增代码+Phase137CalculatorLiveSum: 函数段结束，Phase137WindowsCalculatorLiveSumDriver._find_calculator_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口选择范围。

    def _poll_calculator_window(self, baseline_ids: set[str]) -> tuple[dict[str, Any] | None, bool]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，轮询等待 Calculator 窗口出现；如果没有这段函数，启动稍慢会被误判失败。
        deadline = time.time() + self.timeout_seconds  # 新增代码+Phase137CalculatorLiveSum: 计算等待截止时间；如果没有这行代码，轮询没有边界。
        while time.time() <= deadline:  # 新增代码+Phase137CalculatorLiveSum: 在超时前重复查找；如果没有这行代码，只会尝试一次。
            window, owned = self._find_calculator_window(baseline_ids)  # 新增代码+Phase137CalculatorLiveSum: 查找 Calculator 窗口；如果没有这行代码，轮询没有实际工作。
            if window is not None:  # 新增代码+Phase137CalculatorLiveSum: 检查是否找到目标；如果没有这行代码，None 会被误返回。
                return window, owned  # 新增代码+Phase137CalculatorLiveSum: 返回目标窗口；如果没有这行代码，调用方拿不到 hwnd。
            time.sleep(0.25)  # 新增代码+Phase137CalculatorLiveSum: 短暂等待再重试；如果没有这行代码，轮询会忙等占用 CPU。
        return None, False  # 新增代码+Phase137CalculatorLiveSum: 超时返回未找到；如果没有这行代码，调用方无法处理失败。
    # 新增代码+Phase137CalculatorLiveSum: 函数段结束，Phase137WindowsCalculatorLiveSumDriver._poll_calculator_window 到此结束；如果没有这个边界说明，初学者不容易看出等待范围。

    def _recheck_target(self, window: dict[str, Any]) -> dict[str, Any] | None:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，动作前重新确认同一 Calculator 仍存在；如果没有这段函数，焦点漂移风险无法拦截。
        current = self.inventory.snapshot()  # 新增代码+Phase137CalculatorLiveSum: 读取当前窗口快照；如果没有这行代码，无法发现窗口关闭或漂移。
        found = current.find_window(window) if hasattr(current, "find_window") else None  # 新增代码+Phase137CalculatorLiveSum: 按 app_id/window_id 查找目标；如果没有这行代码，无法绑定原窗口身份。
        return dict(found) if isinstance(found, dict) and _phase137_is_calculator_window(found) else None  # 新增代码+Phase137CalculatorLiveSum: 只返回仍是 Calculator 的窗口；如果没有这行代码，旧 hwnd 可能打到错误窗口。
    # 新增代码+Phase137CalculatorLiveSum: 函数段结束，Phase137WindowsCalculatorLiveSumDriver._recheck_target 到此结束；如果没有这个边界说明，初学者不容易看出复核范围。

    def _observe_window(self, window: dict[str, Any], state_changed_after_action: bool = False) -> dict[str, Any]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，执行真实只读观察并压缩摘要；如果没有这段函数，报告缺前后观察证据。
        try:  # 新增代码+Phase137CalculatorLiveSum: 保护真实观察 provider；如果没有这行代码，截图或 UIA 异常会让清理无法运行。
            frame = self.observation_runtime.observe(target_hint="calculator", real_desktop_touched=state_changed_after_action, target_window=window)  # 新增代码+Phase137CalculatorLiveSum: 观察绑定 Calculator 窗口；如果没有这行代码，观察可能选错同名窗口。
            return _phase137_observation_summary(frame, state_changed_after_action=state_changed_after_action)  # 新增代码+Phase137CalculatorLiveSum: 返回脱敏观察摘要；如果没有这行代码，报告会过大或格式不兼容。
        except Exception as error:  # 新增代码+Phase137CalculatorLiveSum: 捕获观察异常；如果没有这行代码，真实桌面权限问题会中断合同。
            return {"screenshot_captured": False, "uia_tree_observation": False, "window_state_observation": False, "state_changed_after_action": bool(state_changed_after_action), "raw_text_included": False, "reason": f"phase137_observation_failed:{type(error).__name__}"}  # 新增代码+Phase137CalculatorLiveSum: 诚实返回观察失败类型；如果没有这行代码，调用方无法知道证据缺口。
    # 新增代码+Phase137CalculatorLiveSum: 函数段结束，Phase137WindowsCalculatorLiveSumDriver._observe_window 到此结束；如果没有这个边界说明，初学者不容易看出观察范围。

    def _read_result_tree(self, window: dict[str, Any], expected_result: str) -> tuple[bool, dict[str, Any]]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，读取 UIA 树并验证结果；如果没有这段函数，Calculator 只发键不验算。
        try:  # 新增代码+Phase137CalculatorLiveSum: 保护真实 UIA provider；如果没有这行代码，UIA 异常会让整个验收崩溃。
            tree_result = self.uia_provider.read_window_tree(window)  # 新增代码+Phase137CalculatorLiveSum: 按 hwnd 读取 Calculator 控件树；如果没有这行代码，结果验证没有输入。
            return _phase137_result_seen_in_tree(tree_result, expected_result)  # 新增代码+Phase137CalculatorLiveSum: 在树中查找期望结果；如果没有这行代码，观察到结果无法转成布尔证据。
        except Exception as error:  # 新增代码+Phase137CalculatorLiveSum: 捕获 UIA 读取异常；如果没有这行代码，权限或平台差异会中断清理。
            return False, {"captured": False, "node_count": 0, "truncated": False, "name_count": 0, "names_sha256_16": "", "raw_text_included": False, "reason": f"phase137_uia_result_failed:{type(error).__name__}"}  # 新增代码+Phase137CalculatorLiveSum: 返回脱敏失败摘要；如果没有这行代码，失败原因不可审计。
    # 新增代码+Phase137CalculatorLiveSum: 函数段结束，Phase137WindowsCalculatorLiveSumDriver._read_result_tree 到此结束；如果没有这个边界说明，初学者不容易看出结果读取范围。

    def _dispatch_expression(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，发送受控 1+1 Enter 键序列；如果没有这段函数，Calculator 不会真实计算。
        hwnd = _phase137_hwnd_from_window(window)  # 新增代码+Phase137CalculatorLiveSum: 读取目标窗口 hwnd；如果没有这行代码，无法把 Calculator 置前。
        events = [{"type": "set_foreground", "hwnd": hwnd}, {"type": "key_down", "key": "1"}, {"type": "key_up", "key": "1"}, {"type": "key_down", "key": "ADD"}, {"type": "key_up", "key": "ADD"}, {"type": "key_down", "key": "1"}, {"type": "key_up", "key": "1"}, {"type": "key_down", "key": "ENTER"}, {"type": "key_up", "key": "ENTER"}]  # 新增代码+Phase137CalculatorLiveSum: 构造最小受控键序列；如果没有这行代码，sender 没有明确动作。
        return self.sender.send_low_level(events) if hasattr(self.sender, "send_low_level") else {"ok": False, "low_level_event_count": 0, "sender": type(self.sender).__name__, "raw_text_included": False, "reason": "sender_missing_send_low_level"}  # 新增代码+Phase137CalculatorLiveSum: 调用真实 sender 或返回失败；如果没有这行代码，动作派发结果不可审计。
    # 新增代码+Phase137CalculatorLiveSum: 函数段结束，Phase137WindowsCalculatorLiveSumDriver._dispatch_expression 到此结束；如果没有这个边界说明，初学者不容易看出键序列范围。

    def _cleanup_window(self, window: dict[str, Any], owned_window: bool) -> dict[str, Any]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，清理本次拥有的 Calculator 窗口；如果没有这段函数，验收可能污染用户桌面。
        hwnd = _phase137_hwnd_from_window(window)  # 新增代码+Phase137CalculatorLiveSum: 读取窗口句柄；如果没有这行代码，关闭窗口没有目标。
        if not owned_window or hwnd <= 0 or sys.platform != "win32":  # 新增代码+Phase137CalculatorLiveSum: 非本次窗口或无 hwnd 时不强行关闭；如果没有这行代码，可能关闭用户原有 Calculator。
            return {"cleanup_completed": True, "host_hidden_or_restored": True, "lock_released": True, "owned_window": bool(owned_window), "close_attempted": False}  # 新增代码+Phase137CalculatorLiveSum: 返回未关闭但已恢复边界的证据；如果没有这行代码，已有窗口场景会被误清理。
        try:  # 新增代码+Phase137CalculatorLiveSum: 保护 Win32 关闭调用；如果没有这行代码，清理异常会盖过验收结果。
            import ctypes  # 新增代码+Phase137CalculatorLiveSum: 延迟导入 ctypes 调用 PostMessageW；如果没有这行代码，无法请求窗口关闭。
            posted = bool(ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0))  # 新增代码+Phase137CalculatorLiveSum: 发送 WM_CLOSE 给 Calculator；如果没有这行代码，本次窗口会残留。
            time.sleep(0.5)  # 新增代码+Phase137CalculatorLiveSum: 等待窗口处理关闭消息；如果没有这行代码，马上复查可能误判未关闭。
            still_there = self._recheck_target(window) is not None  # 新增代码+Phase137CalculatorLiveSum: 检查窗口是否仍存在；如果没有这行代码，cleanup_completed 没有事实依据。
            return {"cleanup_completed": bool(posted and not still_there), "host_hidden_or_restored": bool(posted), "lock_released": True, "owned_window": True, "close_attempted": True}  # 新增代码+Phase137CalculatorLiveSum: 返回清理证据；如果没有这行代码，Phase8 无法判断是否污染桌面。
        except Exception as error:  # 新增代码+Phase137CalculatorLiveSum: 捕获清理异常；如果没有这行代码，失败清理会让 CLI 崩溃。
            return {"cleanup_completed": False, "host_hidden_or_restored": False, "lock_released": True, "owned_window": True, "close_attempted": True, "reason": f"phase137_cleanup_failed:{type(error).__name__}"}  # 新增代码+Phase137CalculatorLiveSum: 返回清理失败摘要；如果没有这行代码，用户不知道是否残留窗口。
    # 新增代码+Phase137CalculatorLiveSum: 函数段结束，Phase137WindowsCalculatorLiveSumDriver._cleanup_window 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。

    def run(self, *, run_root: Path, expression: str, expected_result: str) -> dict[str, Any]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，执行完整真实 Calculator 闭环；如果没有这段函数，合同无法触达真实代表应用。
        run_root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase137CalculatorLiveSum: 确保运行目录存在；如果没有这行代码，报告附属证据可能无法写入。
        baseline_ids = {str(window.get("window_id") or "") for window in self._snapshot_windows()}  # 新增代码+Phase137CalculatorLiveSum: 记录启动前窗口集合；如果没有这行代码，无法区分本次新开的 Calculator。
        process = None  # 新增代码+Phase137CalculatorLiveSum: 初始化进程对象；如果没有这行代码，启动失败路径无法安全引用变量。
        try:  # 新增代码+Phase137CalculatorLiveSum: 保护启动和动作全过程；如果没有这行代码，异常会绕过结构化失败报告。
            process = subprocess.Popen(self.launch_command, shell=False)  # 新增代码+Phase137CalculatorLiveSum: 启动 Windows Calculator；如果没有这行代码，真实窗口不会出现。
            window, owned_window = self._poll_calculator_window(baseline_ids)  # 新增代码+Phase137CalculatorLiveSum: 等待并定位 Calculator 窗口；如果没有这行代码，后续动作没有目标。
            if window is None:  # 新增代码+Phase137CalculatorLiveSum: 检查是否定位失败；如果没有这行代码，None 会进入 SendInput。
                return {"ok": False, "driver": "phase137_windows_calculator_live_sum_driver", "reason": "calculator_window_not_found", "calculator_process_verified": False, "target_rechecked_before_input": False, "target_rechecked_before_result": False, "expression_verified": False, "observed_result_matches_expected": False, "real_desktop_touched": False, "low_level_event_count": 0, "raw_text_included": False, "target_window": {}, "before_observation": {}, "after_observation": {}, "cleanup_evidence": {"cleanup_completed": True, "host_hidden_or_restored": True, "lock_released": True}, "physical_desktop_dispatch_performed": False, "real_sendinput_dispatch": False, "sender_kind": ""}  # 新增代码+Phase137CalculatorLiveSum: 返回定位失败摘要；如果没有这行代码，调用方无法审计失败点。
            calculator_verified = _phase137_is_calculator_window(window)  # 新增代码+Phase137CalculatorLiveSum: 确认目标像 Calculator；如果没有这行代码，可能向错误窗口发键。
            input_window = self._recheck_target(window) if calculator_verified else None  # 新增代码+Phase137CalculatorLiveSum: 输入前复核目标仍存在；如果没有这行代码，焦点漂移风险无法拦截。
            before_observation = self._observe_window(input_window or window, state_changed_after_action=False) if input_window else {}  # 新增代码+Phase137CalculatorLiveSum: 动作前观察 Calculator；如果没有这行代码，闭环缺少 before 证据。
            dispatch_result = self._dispatch_expression(input_window) if input_window else {"ok": False, "low_level_event_count": 0, "sender": type(self.sender).__name__, "raw_text_included": False}  # 新增代码+Phase137CalculatorLiveSum: 只有复核通过才发送按键；如果没有这行代码，错误目标也可能收到事件。
            time.sleep(0.8)  # 新增代码+Phase137CalculatorLiveSum: 等待 Calculator 更新显示；如果没有这行代码，结果读取可能太早。
            result_window = self._recheck_target(input_window) if input_window else None  # 新增代码+Phase137CalculatorLiveSum: 读取结果前再次复核目标；如果没有这行代码，结果可能来自错误窗口。
            result_seen, result_summary = self._read_result_tree(result_window, expected_result) if result_window else (False, {"captured": False, "node_count": 0, "raw_text_included": False})  # 新增代码+Phase137CalculatorLiveSum: 从 UIA 结果树验证期望结果；如果没有这行代码，表达式是否成功不可知。
            after_observation = self._observe_window(result_window or input_window or window, state_changed_after_action=bool(dispatch_result.get("ok") and result_seen)) if result_window else {}  # 新增代码+Phase137CalculatorLiveSum: 动作后重新观察 Calculator；如果没有这行代码，闭环缺少 after 证据。
            cleanup_evidence = self._cleanup_window(result_window or input_window or window, owned_window=owned_window)  # 新增代码+Phase137CalculatorLiveSum: 清理本次窗口；如果没有这行代码，Calculator 可能残留在桌面。
            sender_kind = _phase137_sender_kind_from_result(self.sender, _phase137_safe_dict(dispatch_result))  # 新增代码+Phase137CalculatorLiveSum: 提取 sender 身份；如果没有这行代码，报告无法证明是不是真实 SendInput。
            low_level_event_count = _phase137_safe_int(dispatch_result.get("low_level_event_count"))  # 新增代码+Phase137CalculatorLiveSum: 读取低层事件数量；如果没有这行代码，空动作可能被误过。
            physical_dispatch = _phase137_sender_is_physical(sender_kind, low_level_event_count, _phase137_safe_dict(dispatch_result))  # 新增代码+Phase137CalculatorLiveSum: 判断是否真实物理派发；如果没有这行代码，recording sender 可冒充真实。
            return {"ok": bool(calculator_verified and input_window and result_window and expression == "1+1" and result_seen and physical_dispatch), "driver": "phase137_windows_calculator_live_sum_driver", "reason": "" if result_seen else "calculator_result_not_observed", "calculator_process_verified": bool(calculator_verified), "target_rechecked_before_input": bool(input_window), "target_rechecked_before_result": bool(result_window), "expression_verified": bool(expression == "1+1"), "observed_result_matches_expected": bool(result_seen), "result_observation": result_summary, "target_window": _phase137_window_identity(result_window or input_window or window), "before_observation": before_observation, "after_observation": after_observation, "cleanup_evidence": cleanup_evidence, "real_desktop_touched": bool(low_level_event_count), "physical_desktop_dispatch_performed": physical_dispatch, "real_sendinput_dispatch": physical_dispatch, "sender_kind": sender_kind, "low_level_event_count": low_level_event_count, "raw_text_included": False}  # 新增代码+Phase137CalculatorLiveSum: 返回脱敏闭环报告；如果没有这行代码，合同层拿不到真实执行事实。
        except Exception as error:  # 新增代码+Phase137CalculatorLiveSum: 捕获真实路径异常；如果没有这行代码，CLI 会输出堆栈而不是结构化失败。
            return {"ok": False, "driver": "phase137_windows_calculator_live_sum_driver", "reason": f"phase137_driver_failed:{type(error).__name__}", "calculator_process_verified": False, "target_rechecked_before_input": False, "target_rechecked_before_result": False, "expression_verified": False, "observed_result_matches_expected": False, "real_desktop_touched": False, "low_level_event_count": 0, "raw_text_included": False, "target_window": {}, "before_observation": {}, "after_observation": {}, "cleanup_evidence": {"cleanup_completed": False, "host_hidden_or_restored": False, "lock_released": True}, "physical_desktop_dispatch_performed": False, "real_sendinput_dispatch": False, "sender_kind": ""}  # 新增代码+Phase137CalculatorLiveSum: 返回异常失败摘要；如果没有这行代码，验收失败难以定位。
        finally:  # 新增代码+Phase137CalculatorLiveSum: 最后兜底处理进程对象；如果没有这行代码，经典 calc.exe 进程可能残留。
            if process is not None and process.poll() is None:  # 新增代码+Phase137CalculatorLiveSum: 只有进程仍在运行时才尝试等待；如果没有这行代码，已退出进程会被误处理。
                try:  # 新增代码+Phase137CalculatorLiveSum: 保护短等待；如果没有这行代码，进程状态异常会盖过主报告。
                    process.wait(timeout=0.2)  # 新增代码+Phase137CalculatorLiveSum: 给进程自然退出机会；如果没有这行代码，可能过早 terminate。
                except Exception:  # 新增代码+Phase137CalculatorLiveSum: 忽略兜底等待异常；如果没有这行代码，清理分支可能抛出无关错误。
                    pass  # 新增代码+Phase137CalculatorLiveSum: 保持主报告为准；如果没有这行代码，except 语法不完整。
    # 新增代码+Phase137CalculatorLiveSum: 函数段结束，Phase137WindowsCalculatorLiveSumDriver.run 到此结束；如果没有这个边界说明，初学者不容易看出真实闭环范围。
# 新增代码+Phase137CalculatorLiveSum: 类段结束，Phase137WindowsCalculatorLiveSumDriver 到此结束；如果没有这个边界说明，初学者不容易看出真实 driver 范围。

def build_phase137_calculator_real_desktop_closure_evidence(report: dict[str, Any] | None, representative_acceptance: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，把 Calculator 成功报告接成 Phase8 最终矩阵证据；如果没有这段函数，局部验收无法进入 Layer A。
    safe_report = _phase137_safe_dict(report)  # 新增代码+Phase137CalculatorLiveSum: 清洗合同报告；如果没有这行代码，None 或坏类型会让 builder 崩溃。
    target_window = _phase137_safe_dict(safe_report.get("target_window"))  # 新增代码+Phase137CalculatorLiveSum: 读取目标窗口摘要；如果没有这行代码，target_identity 没有来源。
    before_observation = _phase137_safe_dict(safe_report.get("before_observation"))  # 新增代码+Phase137CalculatorLiveSum: 读取动作前观察；如果没有这行代码，Phase8 before 字段为空。
    after_observation = _phase137_safe_dict(safe_report.get("after_observation"))  # 新增代码+Phase137CalculatorLiveSum: 读取动作后观察；如果没有这行代码，Phase8 after 字段为空。
    cleanup_evidence = _phase137_safe_dict(safe_report.get("cleanup_evidence"))  # 新增代码+Phase137CalculatorLiveSum: 读取清理证据；如果没有这行代码，Phase8 cleanup 字段为空。
    report_success = bool(safe_report.get("passed") and safe_report.get("real_calculator_run_executed") and safe_report.get("calculator_process_verified") and safe_report.get("target_rechecked_before_input") and safe_report.get("target_rechecked_before_result") and safe_report.get("expression_verified") and safe_report.get("observed_result_matches_expected") and safe_report.get("raw_text_hidden"))  # 新增代码+Phase137CalculatorLiveSum: 汇总能进入最终矩阵的强条件；如果没有这行代码，部分成功会被误当完整闭环。
    representatives = _phase137_safe_dict(representative_acceptance)  # 新增代码+Phase137CalculatorLiveSum: 复制外部代表应用验收汇总；如果没有这行代码，Paint/Notepad/Browser 的上游验收无法保留。
    representatives["calculator"] = bool(report_success)  # 新增代码+Phase137CalculatorLiveSum: 用 Calculator 本合同成功覆盖 Calculator 代表位；如果没有这行代码，Calculator 缺口不会缩小。
    sender_kind = str(safe_report.get("sender_kind") or "").lower()  # 新增代码+Phase137CalculatorLiveSum: 读取 sender 类型；如果没有这行代码，action 字段无法归一。
    normalized_sender_kind = "windows_sendinput" if sender_kind == "windows_sendinput_low_level" else sender_kind  # 新增代码+Phase137CalculatorLiveSum: 把底层 sender 名称归一成矩阵稳定值；如果没有这行代码，最终矩阵和测试字段会漂移。
    return {"target_identity": _phase137_phase8_target_identity(target_window), "before_observation": _phase137_phase8_observation(before_observation), "action": {"physical_desktop_dispatch_performed": bool(report_success and safe_report.get("physical_desktop_dispatch_performed")), "real_sendinput_dispatch": bool(report_success and safe_report.get("real_sendinput_dispatch")), "sender_kind": normalized_sender_kind, "low_level_event_count": _phase137_safe_int(safe_report.get("low_level_event_count"))}, "after_observation": _phase137_phase8_observation(after_observation, include_state_change=True), "verification": {"verified": report_success, "decision": "accepted" if report_success else "rejected", "reason": str(safe_report.get("driver_reason") or safe_report.get("reason") or "phase137_calculator_contract")}, "cleanup": {"cleanup_completed": bool(cleanup_evidence.get("cleanup_completed")), "host_hidden_or_restored": bool(cleanup_evidence.get("host_hidden_or_restored")), "lock_released": bool(cleanup_evidence.get("lock_released"))}, "representative_acceptance": representatives, "target_identity_rechecked_before_each_action": bool(safe_report.get("target_rechecked_before_input") and safe_report.get("target_rechecked_before_result")), "script_artifact_route_blocked": bool(not safe_report.get("uncontrolled_actions_expanded")), "uncontrolled_high_risk_actions_allowed": bool(safe_report.get("uncontrolled_actions_expanded"))}  # 新增代码+Phase137CalculatorLiveSum: 返回 Phase8 校验器需要的完整闭环形状；如果没有这行代码，最终矩阵无法判断 Calculator 是否真的成熟。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，build_phase137_calculator_real_desktop_closure_evidence 到此结束；如果没有这个边界说明，初学者不容易看出 Phase8 接入范围。

def run_phase137_controlled_calculator_live_sum_contract(base_dir: str | Path | None = None, real_run: bool | None = None, allow_real_gate: bool | None = None, calculator_driver: Any | None = None, require_injected_driver: bool = False, raw_prompt_text: str | None = None) -> dict[str, Any]:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，运行 Phase137 总合同入口；如果没有这段函数，测试和 CLI 没有统一事实源。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase137CalculatorLiveSum: 选择隔离运行目录；如果没有这行代码，多次运行可能互相覆盖。
    root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase137CalculatorLiveSum: 创建运行目录；如果没有这行代码，报告写入会失败。
    expression = "1+1"  # 新增代码+Phase137CalculatorLiveSum: 固定受控表达式；如果没有这行代码，用户 prompt 可能被误当作 Calculator 输入。
    expected_result = "2"  # 新增代码+Phase137CalculatorLiveSum: 固定期望结果；如果没有这行代码，结果验证没有标准答案。
    requested = _phase137_request_real_run(real_run)  # 新增代码+Phase137CalculatorLiveSum: 判断本次是否请求真实路径；如果没有这行代码，默认和显式路径会混淆。
    gate_enabled = _phase137_real_gate_enabled(allow_real_gate)  # 新增代码+Phase137CalculatorLiveSum: 判断真实路径是否被第二道门允许；如果没有这行代码，真实桌面动作缺少双确认。
    default_report = _phase137_default_off_report()  # 新增代码+Phase137CalculatorLiveSum: 收集默认关闭证据；如果没有这行代码，默认安全字段没有事实来源。
    unsafe_report = _phase137_unsafe_target_report()  # 新增代码+Phase137CalculatorLiveSum: 收集危险目标拒绝证据；如果没有这行代码，unsafe 字段没有事实来源。
    default_zero = bool(default_report.get("low_level_event_count") == 0 and not default_report.get("real_desktop_touched"))  # 新增代码+Phase137CalculatorLiveSum: 确认默认关闭没有物理事件；如果没有这行代码，默认安全值无法量化。
    unsafe_zero = bool(unsafe_report.get("low_level_event_count") == 0 and not unsafe_report.get("real_desktop_touched"))  # 新增代码+Phase137CalculatorLiveSum: 确认危险目标没有物理事件；如果没有这行代码，危险拦截值无法量化。
    driver_report: dict[str, Any] = {"ok": False, "driver": "not_requested", "reason": "real_calculator_sum_not_requested", "real_desktop_touched": False, "raw_text_included": False}  # 新增代码+Phase137CalculatorLiveSum: 准备默认不执行 driver 报告；如果没有这行代码，默认关闭路径缺少统一字段。
    if requested and gate_enabled and calculator_driver is not None:  # 新增代码+Phase137CalculatorLiveSum: 只有请求门、允许门、注入 driver 同时存在才执行注入路径；如果没有这行代码，单测可能误触真实桌面。
        driver_report = dict(calculator_driver.run(run_root=root, expression=expression, expected_result=expected_result))  # 新增代码+Phase137CalculatorLiveSum: 调用注入 driver；如果没有这行代码，fake 合同不能提供成功事实。
    elif requested and gate_enabled and require_injected_driver:  # 新增代码+Phase137CalculatorLiveSum: 要求注入 driver 但没提供时安全失败；如果没有这行代码，fake-only 测试可能绕到真实桌面。
        driver_report = {"ok": False, "driver": "missing_injected_driver", "reason": "require_injected_driver_without_driver", "real_desktop_touched": False, "raw_text_included": False}  # 新增代码+Phase137CalculatorLiveSum: 记录缺少注入 driver 且不触桌面；如果没有这行代码，失败原因不清楚。
    elif requested and gate_enabled:  # 新增代码+Phase137CalculatorLiveSum: 双门打开且无注入时使用真实 driver；如果没有这行代码，真实可见终端验收无法跑 Calculator。
        driver_report = Phase137WindowsCalculatorLiveSumDriver().run(run_root=root, expression=expression, expected_result=expected_result)  # 新增代码+Phase137CalculatorLiveSum: 执行生产真实 Calculator 闭环；如果没有这行代码，CLI 只能停在占位失败。
    elif requested and not gate_enabled:  # 新增代码+Phase137CalculatorLiveSum: 请求真实但允许门关闭时拒绝；如果没有这行代码，用户可能误以为单门即可触发真实桌面。
        driver_report = {"ok": False, "driver": "gate_rejected", "reason": "phase137_real_gate_disabled", "real_desktop_touched": False, "raw_text_included": False}  # 新增代码+Phase137CalculatorLiveSum: 记录 gate 拒绝且不触桌面；如果没有这行代码，拒绝原因不清楚。
    real_executed = bool(requested and gate_enabled and driver_report.get("ok"))  # 新增代码+Phase137CalculatorLiveSum: 汇总真实 Calculator 是否成功执行；如果没有这行代码，CLI token 无法表达代表应用通过。
    real_desktop_touched = bool(driver_report.get("real_desktop_touched"))  # 新增代码+Phase137CalculatorLiveSum: 保留任何真实桌面触达事实；如果没有这行代码，失败/半执行副作用可能被隐藏。
    report_path = root / "reports" / "phase137_controlled_calculator_live_sum_report.json"  # 新增代码+Phase137CalculatorLiveSum: 定义合同报告路径；如果没有这行代码，验收失败时很难找证据。
    report_without_raw_check: dict[str, Any] = {"marker": PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_MARKER, "ok_token": PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_OK_TOKEN, "model": PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_MODEL, "real_calculator_sum_env": PHASE137_REAL_CALCULATOR_SUM_ENV, "real_calculator_sum_request_env": PHASE137_REAL_CALCULATOR_SUM_REQUEST_ENV, "real_run_requested": requested, "real_enable_gate_required": True, "real_enable_gate_passed": gate_enabled, "require_injected_driver": bool(require_injected_driver), "expression_length": len(expression), "expression_sha256_16": _phase137_sha256_16(expression), "expected_result_sha256_16": _phase137_sha256_16(expected_result), "default_off_zero_physical_events": default_zero, "unsafe_target_zero_physical_events": unsafe_zero, "real_calculator_run_executed": real_executed, "calculator_process_verified": bool(driver_report.get("calculator_process_verified")), "target_rechecked_before_input": bool(driver_report.get("target_rechecked_before_input")), "target_rechecked_before_result": bool(driver_report.get("target_rechecked_before_result")), "expression_verified": bool(driver_report.get("expression_verified")), "observed_result_matches_expected": bool(driver_report.get("observed_result_matches_expected")), "real_desktop_touched": real_desktop_touched, "uncontrolled_actions_expanded": PHASE137_UNCONTROLLED_ACTIONS_EXPANDED, "driver": str(driver_report.get("driver", "")), "driver_ok": bool(driver_report.get("ok")), "driver_reason": str(driver_report.get("reason", "")), "default_off_report": default_report, "unsafe_report": unsafe_report}  # 新增代码+Phase137CalculatorLiveSum: 构造脱敏报告主体；如果没有这行代码，测试和 CLI 会丢失关键事实。
    report_without_raw_check.update({"target_window": _phase137_safe_dict(driver_report.get("target_window")), "before_observation": _phase137_safe_dict(driver_report.get("before_observation")), "after_observation": _phase137_safe_dict(driver_report.get("after_observation")), "cleanup_evidence": _phase137_safe_dict(driver_report.get("cleanup_evidence")), "physical_desktop_dispatch_performed": bool(driver_report.get("physical_desktop_dispatch_performed")), "real_sendinput_dispatch": bool(driver_report.get("real_sendinput_dispatch")), "sender_kind": str(driver_report.get("sender_kind") or ""), "low_level_event_count": _phase137_safe_int(driver_report.get("low_level_event_count"))})  # 新增代码+Phase137CalculatorLiveSum: 合并 Phase8 关键证据字段；如果没有这行代码，builder 无法恢复真实闭环。
    raw_text_hidden = bool(_phase137_report_raw_hidden(report_without_raw_check, raw_prompt_text) and not driver_report.get("raw_text_included"))  # 新增代码+Phase137CalculatorLiveSum: 检查原始 prompt 没有进入报告；如果没有这行代码，隐私门禁无法落地。
    passed = bool(default_zero and unsafe_zero and raw_text_hidden and not PHASE137_UNCONTROLLED_ACTIONS_EXPANDED and ((not requested and not report_without_raw_check["real_desktop_touched"]) or (requested and gate_enabled and real_executed and report_without_raw_check["calculator_process_verified"] and report_without_raw_check["target_rechecked_before_input"] and report_without_raw_check["target_rechecked_before_result"] and report_without_raw_check["expression_verified"] and report_without_raw_check["observed_result_matches_expected"])))  # 新增代码+Phase137CalculatorLiveSum: 汇总合同通过条件；如果没有这行代码，main 无法用退出码表达成功或失败。
    report = dict(report_without_raw_check, raw_text_hidden=raw_text_hidden, passed=passed, report_path=str(report_path))  # 新增代码+Phase137CalculatorLiveSum: 补齐最终报告字段；如果没有这行代码，调用方拿不到 passed、脱敏和路径。
    atomic_write_json(report_path, report)  # 新增代码+Phase137CalculatorLiveSum: 原子写入报告文件；如果没有这行代码，验收和排查没有落盘证据。
    return report  # 新增代码+Phase137CalculatorLiveSum: 返回合同报告；如果没有这行代码，测试和 CLI 无法读取结果。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，run_phase137_controlled_calculator_live_sum_contract 到此结束；如果没有这个边界说明，初学者不容易看出总合同范围。

def phase137_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，把报告转成真实终端稳定 token 行；如果没有这段函数，验收器必须解析复杂 JSON。
    ok_token = f" {PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_OK_TOKEN}" if bool(report.get("passed")) else ""  # 新增代码+Phase137CalculatorLiveSum: 仅在合同通过时输出 OK token；如果没有这行代码，失败报告会误带成功锚点。
    return f"{PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_MARKER}{ok_token} default_off_zero_physical_events={_phase137_bool_token(report.get('default_off_zero_physical_events'))} unsafe_target_zero_physical_events={_phase137_bool_token(report.get('unsafe_target_zero_physical_events'))} real_enable_gate_required={_phase137_bool_token(report.get('real_enable_gate_required'))} real_calculator_run_executed={_phase137_bool_token(report.get('real_calculator_run_executed'))} calculator_process_verified={_phase137_bool_token(report.get('calculator_process_verified'))} target_rechecked_before_input={_phase137_bool_token(report.get('target_rechecked_before_input'))} target_rechecked_before_result={_phase137_bool_token(report.get('target_rechecked_before_result'))} expression_verified={_phase137_bool_token(report.get('expression_verified'))} observed_result_matches_expected={_phase137_bool_token(report.get('observed_result_matches_expected'))} raw_text_hidden={_phase137_bool_token(report.get('raw_text_hidden'))} real_desktop_touched={_phase137_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase137_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+Phase137CalculatorLiveSum: 返回固定顺序 token 行；如果没有这行代码，真实可见终端场景匹配会漂移。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，phase137_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。

def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase137CalculatorLiveSum: 函数段开始，提供命令行入口；如果没有这段函数，真实终端无法直接运行 Phase137 合同。
    _ = argv  # 新增代码+Phase137CalculatorLiveSum: 保留 argv 扩展位；如果没有这行代码，读者可能误以为命令参数被遗漏。
    report = run_phase137_controlled_calculator_live_sum_contract()  # 新增代码+Phase137CalculatorLiveSum: 按环境双门运行合同；如果没有这行代码，CLI 不会产生验收事实。
    print(phase137_cli_line(report))  # 新增代码+Phase137CalculatorLiveSum: 打印稳定 token 行；如果没有这行代码，验收脚本无法快速匹配成功条件。
    print(json.dumps({"report_path": report.get("report_path"), "passed": report.get("passed"), "real_calculator_run_executed": report.get("real_calculator_run_executed")}, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase137CalculatorLiveSum: 打印短 JSON 方便定位报告；如果没有这行代码，失败时不容易找到证据文件。
    print(PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_MARKER)  # 新增代码+Phase137CalculatorLiveSum: 单独打印 marker 方便人工观察；如果没有这行代码，可见终端里阶段标识不够醒目。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase137CalculatorLiveSum: 按 passed 返回退出码；如果没有这行代码，失败合同可能被自动化误判为成功。
# 新增代码+Phase137CalculatorLiveSum: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。

__all__ = ["DEFAULT_PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_ROOT", "PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_MARKER", "PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_MODEL", "PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_OK_TOKEN", "PHASE137_REAL_CALCULATOR_SUM_ENV", "PHASE137_REAL_CALCULATOR_SUM_REQUEST_ENV", "PHASE137_UNCONTROLLED_ACTIONS_EXPANDED", "Phase137WindowsCalculatorLiveSumDriver", "build_phase137_calculator_real_desktop_closure_evidence", "main", "phase137_cli_line", "run_phase137_controlled_calculator_live_sum_contract"]  # 新增代码+Phase137CalculatorLiveSum: 限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。

if __name__ == "__main__":  # 新增代码+Phase137CalculatorLiveSum: 允许直接运行模块；如果没有这行代码，python 文件方式不会启动合同。
    raise SystemExit(main())  # 新增代码+Phase137CalculatorLiveSum: 使用 main 返回码退出；如果没有这行代码，命令行状态不明确。
# 新增代码+Phase137CalculatorLiveSum: 文件入口段结束，本模块到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
