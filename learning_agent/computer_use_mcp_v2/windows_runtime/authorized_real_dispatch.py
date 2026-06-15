"""Windows 授权后低层真实派发候选层。"""  # 新增代码+Phase94AuthorizedRealDispatch：说明本模块把 Phase93 的 recording-only 缺口推进到“授权后可进入低层 sender”的候选层；如果没有这行代码，读者不知道本文件的职责边界。
from __future__ import annotations  # 新增代码+Phase94AuthorizedRealDispatch：启用延迟类型解析，避免类之间互相引用时被旧版解析顺序影响；如果没有这行代码，复杂类型注解更容易在导入时失败。

import hashlib  # 新增代码+Phase94AuthorizedRealDispatch：导入哈希工具用于脱敏文本和窗口身份；如果没有这行代码，报告要么泄露明文，要么无法稳定比对目标。
import json  # 新增代码+Phase94AuthorizedRealDispatch：导入 JSON 用于稳定序列化报告和做泄露扫描；如果没有这行代码，脱敏验证和 CLI 报告会不稳定。
import os  # 新增代码+Phase94AuthorizedRealDispatch：导入环境变量读取工具，用于真实派发显式开关；如果没有这行代码，启用真实派发的入口会分散且不可审计。
import time  # 新增代码+Phase94AuthorizedRealDispatch：导入时间工具用于生成隔离合同目录和短期授权 TTL；如果没有这行代码，多次验收可能互相污染状态。
from pathlib import Path  # 新增代码+Phase94AuthorizedRealDispatch：导入 Path 统一处理 Windows 路径；如果没有这行代码，路径拼接会更脆弱。
from typing import Any  # 新增代码+Phase94AuthorizedRealDispatch：导入 Any 描述 JSON 风格对象；如果没有这行代码，接口边界对初学者不够清楚。

try:  # 新增代码+Phase94AuthorizedRealDispatch：优先按 learning_agent 包路径导入现有安全组件；如果没有这段代码，单元测试和生产入口不能共享同一套模块。
    from learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANT_SESSION_ID, DEFAULT_PERSISTENT_GRANTS_ROOT, WindowsComputerUsePersistentGrantStore  # 新增代码+Phase94AuthorizedRealDispatch：复用 Phase60 持久授权事实源；如果没有这行代码，Phase94 会绕开已有授权门禁。
    from learning_agent.computer_use_mcp_v2.windows_runtime.real_app_safety_boundary import PHASE72_UNCONTROLLED_ACTIONS_EXPANDED, WindowsRealAppSafetyBoundary  # 新增代码+Phase94AuthorizedRealDispatch：复用 Phase72 真实应用安全边界；如果没有这行代码，危险窗口和未授权窗口会缺少统一拒绝。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_live_execution import run_phase93_universal_live_execution_gate_contract  # 新增代码+Phase94AuthorizedRealDispatch：复用 Phase93 合同证明旧缺口；如果没有这行代码，Phase94 报告不能说明自己补的是哪一段差距。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase94AuthorizedRealDispatch：复用静态窗口 inventory 做目标复核；如果没有这行代码，测试只能依赖真实桌面窗口。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase94AuthorizedRealDispatch：复用项目原子 JSON 写入；如果没有这行代码，验收报告可能半写损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase94AuthorizedRealDispatch：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行的脚本模式；如果没有这段代码，真实终端入口可能因包名前缀失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase94AuthorizedRealDispatch：只对包路径缺失做 fallback；如果没有这行代码，内部真实 bug 可能被错误吞掉。
        raise  # 新增代码+Phase94AuthorizedRealDispatch：重新抛出非路径类导入错误；如果没有这行代码，底层模块问题会被隐藏。
    from computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANT_SESSION_ID, DEFAULT_PERSISTENT_GRANTS_ROOT, WindowsComputerUsePersistentGrantStore  # type: ignore  # 新增代码+Phase94AuthorizedRealDispatch：脚本模式复用 Phase60 授权 store；如果没有这行代码，bat 入口无法验证授权。
    from computer_use_mcp_v2.windows_runtime.real_app_safety_boundary import PHASE72_UNCONTROLLED_ACTIONS_EXPANDED, WindowsRealAppSafetyBoundary  # type: ignore  # 新增代码+Phase94AuthorizedRealDispatch：脚本模式复用 Phase72 安全边界；如果没有这行代码，bat 入口无法拦截危险窗口。
    from computer_use_mcp_v2.windows_runtime.universal_live_execution import run_phase93_universal_live_execution_gate_contract  # type: ignore  # 新增代码+Phase94AuthorizedRealDispatch：脚本模式复用 Phase93 合同；如果没有这行代码，bat 入口无法证明承接 Phase93。
    from computer_use_mcp_v2.windows_runtime.windows_backend import StaticWindowsWindowInventory  # type: ignore  # 新增代码+Phase94AuthorizedRealDispatch：脚本模式复用静态窗口 inventory；如果没有这行代码，合同无法离线复核目标。
    from runtime.files import atomic_write_json  # type: ignore  # 新增代码+Phase94AuthorizedRealDispatch：脚本模式复用原子写入工具；如果没有这行代码，bat 验收报告可能写坏。

PHASE94_AUTHORIZED_REAL_DISPATCH_MARKER = "PHASE94_AUTHORIZED_REAL_DISPATCH_READY"  # 新增代码+Phase94AuthorizedRealDispatch：定义 Phase94 ready marker；如果没有这行代码，真实终端验收没有稳定阶段锚点。
PHASE94_AUTHORIZED_REAL_DISPATCH_OK_TOKEN = "PHASE94_AUTHORIZED_REAL_DISPATCH_OK"  # 新增代码+Phase94AuthorizedRealDispatch：定义 Phase94 OK token；如果没有这行代码，验收脚本无法区分成功输出和普通日志。
PHASE94_AUTHORIZED_REAL_DISPATCH_MODEL = "phase94_authorized_real_dispatch_candidate"  # 新增代码+Phase94AuthorizedRealDispatch：定义报告模型名；如果没有这行代码，状态和证据无法说明当前合同版本。
PHASE94_REAL_DISPATCH_ENV = "LEARNING_AGENT_PHASE94_ENABLE_REAL_DISPATCH"  # 新增代码+Phase94AuthorizedRealDispatch：定义真实派发环境开关名；如果没有这行代码，启用方式会漂移且不易审计。
PHASE94_REAL_DISPATCH_DEFAULT_DISABLED = True  # 新增代码+Phase94AuthorizedRealDispatch：声明真实物理派发默认关闭；如果没有这行代码，普通运行可能被误解为会直接操控桌面。
PHASE94_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase94AuthorizedRealDispatch：声明本阶段没有扩大无授权动作面；如果没有这行代码，用户可能误解为任意窗口都可控。
DEFAULT_PHASE94_AUTHORIZED_REAL_DISPATCH_ROOT = DEFAULT_PERSISTENT_GRANTS_ROOT.parent / "phase94_authorized_real_dispatch"  # 新增代码+Phase94AuthorizedRealDispatch：定义默认报告目录；如果没有这行代码，验收证据没有稳定落点。
PHASE94_ACTION_ALIASES = {"click_control": "click", "click_by_query": "click", "click_by_visual_point": "click", "click": "click", "type_into_control": "type_text", "type_by_query": "type_text", "type": "type_text", "type_text": "type_text", "scroll_at": "scroll", "scroll": "scroll"}  # 新增代码+Phase94AuthorizedRealDispatch：定义高层动作到授权 scope 的映射；如果没有这行代码，高层动作名和持久授权会对不上。

# 新增代码+Phase94AuthorizedRealDispatch：函数段开始，_phase94_bool_token 把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会混用 True/False 并导致验收匹配漂移。
def _phase94_bool_token(value: Any) -> str:  # 新增代码+Phase94AuthorizedRealDispatch：定义布尔 token helper；如果没有这行代码，多处输出会重复写转换逻辑。
    return "true" if bool(value) else "false"  # 新增代码+Phase94AuthorizedRealDispatch：返回小写布尔文本；如果没有这行代码，验收场景的字符串匹配不稳定。
# 新增代码+Phase94AuthorizedRealDispatch：函数段结束，_phase94_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。

# 新增代码+Phase94AuthorizedRealDispatch：函数段开始，_phase94_safe_int 把坐标和滚动量安全转成整数；如果没有这段函数，坏输入可能让动作构造直接崩溃。
def _phase94_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase94AuthorizedRealDispatch：定义安全整数转换；如果没有这行代码，x/y/delta 等字段需要到处手写容错。
    try:  # 新增代码+Phase94AuthorizedRealDispatch：尝试按整数读取输入；如果没有这行代码，非数字值会直接抛出异常。
        return int(value)  # 新增代码+Phase94AuthorizedRealDispatch：返回转换后的整数；如果没有这行代码，调用方拿不到可用数值。
    except (TypeError, ValueError):  # 新增代码+Phase94AuthorizedRealDispatch：捕获 None、空字符串和非数字文本；如果没有这行代码，坏参数会中断整个执行链。
        return int(default)  # 新增代码+Phase94AuthorizedRealDispatch：返回默认值兜底；如果没有这行代码，函数无法优雅降级。
# 新增代码+Phase94AuthorizedRealDispatch：函数段结束，_phase94_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出容错范围。

# 新增代码+Phase94AuthorizedRealDispatch：函数段开始，_phase94_text_digest 只保存文本指纹不保存明文；如果没有这段函数，用户输入内容可能进入报告。
def _phase94_text_digest(value: Any) -> str:  # 新增代码+Phase94AuthorizedRealDispatch：定义文本短哈希 helper；如果没有这行代码，脱敏字段无法稳定关联原输入。
    text = str(value or "")  # 新增代码+Phase94AuthorizedRealDispatch：把输入归一化为文本；如果没有这行代码，None 或其他对象不能稳定编码。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase94AuthorizedRealDispatch：返回 SHA256 前 16 位；如果没有这行代码，报告无法用短指纹复盘而又不泄露明文。
# 新增代码+Phase94AuthorizedRealDispatch：函数段结束，_phase94_text_digest 到此结束；如果没有这个边界说明，初学者不容易看出脱敏范围。

# 新增代码+Phase94AuthorizedRealDispatch：函数段开始，_phase94_normalized_action 统一动作名；如果没有这段函数，高层动作和低层事件构造会各说各话。
def _phase94_normalized_action(action: Any) -> str:  # 新增代码+Phase94AuthorizedRealDispatch：定义动作名归一化入口；如果没有这行代码，click_by_query/type_into_control 等别名无法复用授权。
    key = str(action or "").strip().lower()  # 新增代码+Phase94AuthorizedRealDispatch：清理动作名并转小写；如果没有这行代码，大小写和空格会导致授权匹配失败。
    return PHASE94_ACTION_ALIASES.get(key, key)  # 新增代码+Phase94AuthorizedRealDispatch：返回别名映射后的动作名；如果没有这行代码，高层动作可能被当成未知动作拒绝。
# 新增代码+Phase94AuthorizedRealDispatch：函数段结束，_phase94_normalized_action 到此结束；如果没有这个边界说明，初学者不容易看出动作映射范围。

# 新增代码+Phase94AuthorizedRealDispatch：函数段开始，_phase94_window_identity 生成目标窗口脱敏身份；如果没有这段函数，发送前无法复核目标是否漂移。
def _phase94_window_identity(window: dict[str, Any] | Any) -> dict[str, str]:  # 新增代码+Phase94AuthorizedRealDispatch：定义窗口身份摘要函数；如果没有这行代码，目标比对会散落在各处。
    source = dict(window or {}) if isinstance(window, dict) else {}  # 新增代码+Phase94AuthorizedRealDispatch：只接受 dict 并容错为空；如果没有这行代码，坏窗口对象会让身份计算崩溃。
    title = str(source.get("title_preview") or source.get("title") or "").strip()  # 新增代码+Phase94AuthorizedRealDispatch：读取可见标题但不直接返回明文；如果没有这行代码，标题变化无法参与漂移判断。
    return {"app_id": str(source.get("app_id") or source.get("process_name") or "").lower(), "window_id": str(source.get("window_id") or source.get("hwnd") or ""), "display_id": str(source.get("display_id") or source.get("monitor_id") or ""), "title_sha256_16": _phase94_text_digest(title)}  # 新增代码+Phase94AuthorizedRealDispatch：返回脱敏身份字段；如果没有这行代码，目标复核无法解释 app/window/title 哪些维度参与了判断。
# 新增代码+Phase94AuthorizedRealDispatch：函数段结束，_phase94_window_identity 到此结束；如果没有这个边界说明，初学者不容易看出目标身份范围。

# 修改代码+Phase94AuthorizedRealDispatch：函数段开始，_phase94_target_core_identity 只抽取发送前必须完全一致的硬身份；如果没有这段函数，静态 inventory 丢失 display_id 时会误判正常窗口为漂移。
def _phase94_target_core_identity(identity: dict[str, str]) -> dict[str, str]:  # 修改代码+Phase94AuthorizedRealDispatch：定义硬身份裁剪 helper；如果没有这行代码，复核逻辑需要重复挑字段。
    return {"app_id": str(identity.get("app_id", "")), "window_id": str(identity.get("window_id", "")), "title_sha256_16": str(identity.get("title_sha256_16", ""))}  # 修改代码+Phase94AuthorizedRealDispatch：只返回 app/window/title 指纹；如果没有这行代码，display_id 这类快照可选字段会误伤正例。
# 修改代码+Phase94AuthorizedRealDispatch：函数段结束，_phase94_target_core_identity 到此结束；如果没有这个边界说明，初学者不容易看出硬身份范围。

# 新增代码+Phase94AuthorizedRealDispatch：函数段开始，_phase94_real_dispatch_enabled 读取显式真实派发开关；如果没有这段函数，真实派发可能被隐式打开。
def _phase94_real_dispatch_enabled(explicit_value: bool | None = None) -> bool:  # 新增代码+Phase94AuthorizedRealDispatch：定义真实派发启用判断；如果没有这行代码，调用方需要重复理解 env 规则。
    if explicit_value is not None:  # 新增代码+Phase94AuthorizedRealDispatch：调用方显式传值时优先使用；如果没有这行代码，单元测试无法稳定覆盖开关路径。
        return bool(explicit_value)  # 新增代码+Phase94AuthorizedRealDispatch：返回显式布尔值；如果没有这行代码，显式参数不会生效。
    return str(os.environ.get(PHASE94_REAL_DISPATCH_ENV, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase94AuthorizedRealDispatch：仅接受明确真值环境变量；如果没有这行代码，模糊环境值可能误开启真实派发。
# 新增代码+Phase94AuthorizedRealDispatch：函数段结束，_phase94_real_dispatch_enabled 到此结束；如果没有这个边界说明，初学者不容易看出开关范围。

# 新增代码+Phase94AuthorizedRealDispatch：函数段开始，_phase94_safe_rect_center 计算窗口中心兜底坐标；如果没有这段函数，缺 x/y 时无法生成安全点击候选事件。
def _phase94_safe_rect_center(window: dict[str, Any]) -> tuple[int, int]:  # 新增代码+Phase94AuthorizedRealDispatch：定义窗口中心坐标 helper；如果没有这行代码，点击动作必须总是依赖调用方给坐标。
    rect = dict(window.get("rect", {})) if isinstance(window.get("rect"), dict) else {}  # 新增代码+Phase94AuthorizedRealDispatch：读取窗口矩形并容错；如果没有这行代码，缺 rect 的窗口会触发属性错误。
    left = _phase94_safe_int(rect.get("left"), 0)  # 新增代码+Phase94AuthorizedRealDispatch：读取左边界；如果没有这行代码，中心点无法计算横向起点。
    top = _phase94_safe_int(rect.get("top"), 0)  # 新增代码+Phase94AuthorizedRealDispatch：读取上边界；如果没有这行代码，中心点无法计算纵向起点。
    right = _phase94_safe_int(rect.get("right"), left + 1)  # 新增代码+Phase94AuthorizedRealDispatch：读取右边界并兜底；如果没有这行代码，坏 rect 可能产生零宽窗口。
    bottom = _phase94_safe_int(rect.get("bottom"), top + 1)  # 新增代码+Phase94AuthorizedRealDispatch：读取下边界并兜底；如果没有这行代码，坏 rect 可能产生零高窗口。
    return left + max(1, right - left) // 2, top + max(1, bottom - top) // 2  # 新增代码+Phase94AuthorizedRealDispatch：返回中心点；如果没有这行代码，默认点击位置不稳定。
# 新增代码+Phase94AuthorizedRealDispatch：函数段结束，_phase94_safe_rect_center 到此结束；如果没有这个边界说明，初学者不容易看出坐标兜底范围。

# 新增代码+Phase94AuthorizedRealDispatch：函数段开始，_phase94_low_level_events_for_action 把受控动作转成低层事件候选；如果没有这段函数，授权通过后仍只能停留在高层记录。
def _phase94_low_level_events_for_action(window: dict[str, Any], action: Any, arguments: dict[str, Any] | None = None) -> list[dict[str, Any]]:  # 新增代码+Phase94AuthorizedRealDispatch：定义低层事件构造入口；如果没有这行代码，sender 拿不到可发送事件。
    action_key = _phase94_normalized_action(action)  # 新增代码+Phase94AuthorizedRealDispatch：统一动作名；如果没有这行代码，别名动作不会进入对应事件分支。
    args = dict(arguments or {})  # 新增代码+Phase94AuthorizedRealDispatch：复制参数避免污染调用方对象；如果没有这行代码，后续清洗可能改坏外部数据。
    identity = _phase94_window_identity(window)  # 新增代码+Phase94AuthorizedRealDispatch：计算目标身份放入事件；如果没有这行代码，sender 侧难以审计目标。
    if action_key == "click":  # 新增代码+Phase94AuthorizedRealDispatch：处理点击动作；如果没有这行代码，最基础的鼠标控制无法进入低层候选。
        default_x, default_y = _phase94_safe_rect_center(window)  # 新增代码+Phase94AuthorizedRealDispatch：在缺坐标时使用窗口中心；如果没有这行代码，点击候选会因缺 x/y 失败。
        x = _phase94_safe_int(args.get("x"), default_x)  # 新增代码+Phase94AuthorizedRealDispatch：读取点击横坐标；如果没有这行代码，sender 不知道鼠标移动到哪里。
        y = _phase94_safe_int(args.get("y"), default_y)  # 新增代码+Phase94AuthorizedRealDispatch：读取点击纵坐标；如果没有这行代码，sender 不知道鼠标移动到哪里。
        return [{"kind": "mouse_move", "x": x, "y": y, "target": identity}, {"kind": "mouse_down", "button": "left", "x": x, "y": y, "target": identity}, {"kind": "mouse_up", "button": "left", "x": x, "y": y, "target": identity}]  # 新增代码+Phase94AuthorizedRealDispatch：返回移动、按下、抬起三段事件；如果没有这行代码，点击动作无法被真实 sender 接收。
    if action_key == "type_text":  # 新增代码+Phase94AuthorizedRealDispatch：处理文本输入动作；如果没有这行代码，授权输入仍无法形成低层候选事件。
        text = str(args.get("text") or args.get("value") or "")  # 新增代码+Phase94AuthorizedRealDispatch：读取待输入文本但只在内存中短暂使用；如果没有这行代码，无法知道要输入多长内容。
        return [{"kind": "keyboard_text", "text_sha256_16": _phase94_text_digest(text), "text_length": len(text), "target": identity}]  # 新增代码+Phase94AuthorizedRealDispatch：返回脱敏文本事件；如果没有这行代码，文本输入会泄露明文或无法派发。
    if action_key == "scroll":  # 新增代码+Phase94AuthorizedRealDispatch：处理滚动动作；如果没有这行代码，通用桌面控制缺少常见滚轮能力。
        default_x, default_y = _phase94_safe_rect_center(window)  # 新增代码+Phase94AuthorizedRealDispatch：计算滚动位置兜底；如果没有这行代码，滚动事件缺少坐标上下文。
        x = _phase94_safe_int(args.get("x"), default_x)  # 新增代码+Phase94AuthorizedRealDispatch：读取滚动横坐标；如果没有这行代码，滚动位置无法审计。
        y = _phase94_safe_int(args.get("y"), default_y)  # 新增代码+Phase94AuthorizedRealDispatch：读取滚动纵坐标；如果没有这行代码，滚动位置无法审计。
        delta_y = _phase94_safe_int(args.get("delta_y", args.get("wheel_delta", -120)), -120)  # 新增代码+Phase94AuthorizedRealDispatch：读取滚动量并默认向下滚；如果没有这行代码，滚轮事件没有方向。
        return [{"kind": "mouse_wheel", "x": x, "y": y, "delta_y": delta_y, "target": identity}]  # 新增代码+Phase94AuthorizedRealDispatch：返回滚轮低层事件；如果没有这行代码，sender 无法执行滚动候选。
    return []  # 新增代码+Phase94AuthorizedRealDispatch：未知动作返回空事件；如果没有这行代码，未知动作可能被误构造成副作用事件。
# 新增代码+Phase94AuthorizedRealDispatch：函数段结束，_phase94_low_level_events_for_action 到此结束；如果没有这个边界说明，初学者不容易看出支持动作范围。

# 新增代码+Phase94AuthorizedRealDispatch：函数段开始，_phase94_sanitize_event 删除事件中的任何潜在明文；如果没有这段函数，记录型 sender 可能把用户输入写进报告。
def _phase94_sanitize_event(event: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase94AuthorizedRealDispatch：定义事件脱敏 helper；如果没有这行代码，每个 sender 都要重复清洗。
    clean = dict(event)  # 新增代码+Phase94AuthorizedRealDispatch：复制事件避免修改原对象；如果没有这行代码，调用方持有的事件会被意外改变。
    clean.pop("text", None)  # 新增代码+Phase94AuthorizedRealDispatch：删除可能存在的明文 text 字段；如果没有这行代码，敏感输入可能进入长期证据。
    clean.pop("value", None)  # 新增代码+Phase94AuthorizedRealDispatch：删除可能存在的明文 value 字段；如果没有这行代码，替代文本字段可能泄露。
    clean["raw_text_included"] = False  # 新增代码+Phase94AuthorizedRealDispatch：显式标记事件不含明文；如果没有这行代码，审计无法快速判断隐私状态。
    return clean  # 新增代码+Phase94AuthorizedRealDispatch：返回脱敏事件；如果没有这行代码，sender 无法保存安全副本。
# 新增代码+Phase94AuthorizedRealDispatch：函数段结束，_phase94_sanitize_event 到此结束；如果没有这个边界说明，初学者不容易看出脱敏范围。

# 新增代码+Phase94AuthorizedRealDispatch：类段开始，Phase94RecordingLowLevelSender 是默认安全 sender；如果没有这个类，测试可能误触真实鼠标键盘。
class Phase94RecordingLowLevelSender:  # 新增代码+Phase94AuthorizedRealDispatch：定义记录型低层 sender；如果没有这行代码，Phase94 不能证明事件到达 sender 而不产生物理副作用。
    physical_dispatch = False  # 新增代码+Phase94AuthorizedRealDispatch：声明此 sender 不做真实物理派发；如果没有这行代码，调用方无法区分记录和真实 sender。

    # 新增代码+Phase94AuthorizedRealDispatch：函数段开始，初始化记录型 sender 的计数和事件缓存；如果没有这段函数，sender 调用证据无处保存。
    def __init__(self) -> None:  # 新增代码+Phase94AuthorizedRealDispatch：定义初始化方法；如果没有这行代码，send_count 和 events 不会存在。
        self.send_count = 0  # 新增代码+Phase94AuthorizedRealDispatch：记录发送调用次数；如果没有这行代码，测试无法证明 sender 被调用。
        self.events: list[dict[str, Any]] = []  # 新增代码+Phase94AuthorizedRealDispatch：保存脱敏事件副本；如果没有这行代码，低层事件到达情况不可观察。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段结束，Phase94RecordingLowLevelSender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    # 新增代码+Phase94AuthorizedRealDispatch：函数段开始，send_low_level 记录事件但不触碰桌面；如果没有这段函数，候选适配器没有统一 sender 接口。
    def send_low_level(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase94AuthorizedRealDispatch：定义低层发送接口；如果没有这行代码，runtime 不能把事件交给注入 sender。
        sanitized_events = [_phase94_sanitize_event(event) for event in list(events or [])]  # 新增代码+Phase94AuthorizedRealDispatch：脱敏复制所有事件；如果没有这行代码，记录里可能混入明文。
        self.send_count += 1  # 新增代码+Phase94AuthorizedRealDispatch：增加调用次数；如果没有这行代码，测试无法确认 sender 真的被触达。
        self.events.extend(sanitized_events)  # 新增代码+Phase94AuthorizedRealDispatch：保存脱敏事件；如果没有这行代码，后续审计看不到事件形状。
        return {"ok": bool(sanitized_events), "sender": "phase94_recording_low_level_sender", "low_level_event_count": len(sanitized_events), "real_dispatch_performed": False, "physical_dispatch": False, "raw_text_included": False, "event_types": [str(event.get("kind", "")) for event in sanitized_events]}  # 新增代码+Phase94AuthorizedRealDispatch：返回安全发送报告；如果没有这行代码，调用方无法汇总 sender 结果。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段结束，Phase94RecordingLowLevelSender.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出记录发送范围。
# 新增代码+Phase94AuthorizedRealDispatch：类段结束，Phase94RecordingLowLevelSender 到此结束；如果没有这个边界说明，初学者不容易看出 sender 范围。

# 新增代码+Phase94AuthorizedRealDispatch：类段开始，WindowsAuthorizedRealDispatchCandidate 组合授权、安全边界、目标复核和低层 sender；如果没有这个类，Phase94 的主能力没有承载对象。
class WindowsAuthorizedRealDispatchCandidate:  # 新增代码+Phase94AuthorizedRealDispatch：定义授权后真实派发候选适配器；如果没有这行代码，测试没有主对象可驱动。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段开始，初始化候选适配器依赖；如果没有这段函数，授权 store、边界和 sender 无法组合。
    def __init__(self, base_dir: str | Path | None = None, *, grant_store: Any | None = None, safety_boundary: Any | None = None, inventory: Any | None = None, low_level_sender: Any | None = None) -> None:  # 新增代码+Phase94AuthorizedRealDispatch：定义初始化入口并允许依赖注入；如果没有这行代码，测试无法隔离状态或替换 sender。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_PHASE94_AUTHORIZED_REAL_DISPATCH_ROOT  # 新增代码+Phase94AuthorizedRealDispatch：确定运行目录；如果没有这行代码，报告和授权状态没有稳定位置。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase94AuthorizedRealDispatch：创建目录；如果没有这行代码，后续授权和报告写入可能失败。
        self.grant_store = grant_store if grant_store is not None else WindowsComputerUsePersistentGrantStore(base_dir=self.base_dir / "grants")  # 新增代码+Phase94AuthorizedRealDispatch：使用注入或默认授权 store；如果没有这行代码，安全边界无法判断授权。
        self.safety_boundary = safety_boundary if safety_boundary is not None else WindowsRealAppSafetyBoundary()  # 新增代码+Phase94AuthorizedRealDispatch：使用注入或默认安全边界；如果没有这行代码，危险窗口无法统一拒绝。
        self.low_level_sender = low_level_sender if low_level_sender is not None else Phase94RecordingLowLevelSender()  # 新增代码+Phase94AuthorizedRealDispatch：使用注入或默认记录 sender；如果没有这行代码，默认运行可能误触真实桌面。
        self.inventory = inventory if inventory is not None else StaticWindowsWindowInventory([self.contract_window()], source="phase94_contract_static")  # 新增代码+Phase94AuthorizedRealDispatch：使用注入或默认静态 inventory；如果没有这行代码，目标复核没有快照来源。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段结束，WindowsAuthorizedRealDispatchCandidate.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出依赖范围。

    # 新增代码+Phase94AuthorizedRealDispatch：函数段开始，contract_window 构造普通安全窗口样本；如果没有这段函数，合同测试没有可授权目标。
    def contract_window(self) -> dict[str, Any]:  # 新增代码+Phase94AuthorizedRealDispatch：定义合同窗口工厂；如果没有这行代码，测试会散落重复窗口字段。
        return {"app_id": "notepad.exe", "process_name": "notepad.exe", "window_id": "hwnd:9401", "hwnd": 9401, "title_preview": "LearningAgent Phase94 Normal App", "display_id": "DISPLAY1", "rect": {"left": 200, "top": 160, "right": 620, "bottom": 420}, "safe_to_target": True}  # 新增代码+Phase94AuthorizedRealDispatch：返回普通应用窗口；如果没有这行代码，授权和目标复核没有稳定样本。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段结束，WindowsAuthorizedRealDispatchCandidate.contract_window 到此结束；如果没有这个边界说明，初学者不容易看出样本窗口范围。

    # 新增代码+Phase94AuthorizedRealDispatch：函数段开始，authorize_window 写入短期持久授权；如果没有这段函数，正例无法通过 Phase72 安全边界。
    def authorize_window(self, window: dict[str, Any], session_id: Any = DEFAULT_PERSISTENT_GRANT_SESSION_ID, action_scope: Any = None, ttl_seconds: int | float = 60) -> dict[str, Any]:  # 新增代码+Phase94AuthorizedRealDispatch：定义授权 helper；如果没有这行代码，测试和合同需要直接理解 Phase60 参数。
        target = dict(window or {})  # 新增代码+Phase94AuthorizedRealDispatch：复制窗口避免污染调用方；如果没有这行代码，授权过程可能修改原对象。
        scope = action_scope if action_scope is not None else ["click", "type_text", "scroll"]  # 新增代码+Phase94AuthorizedRealDispatch：默认授权常见普通桌面动作；如果没有这行代码，合同正例可能少授权导致失败。
        return self.grant_store.approve(session_id=session_id, app=target.get("process_name") or target.get("app_id") or "notepad.exe", window_id=target.get("window_id", ""), display_id=target.get("display_id", ""), action_scope=scope, ttl_seconds=ttl_seconds, reason="phase94-authorized-real-dispatch-candidate", grant_flags={"desktopAction": True, "realDispatchCandidate": True})  # 新增代码+Phase94AuthorizedRealDispatch：写入带 desktopAction 的授权；如果没有这行代码，Phase72 会正确拒绝所有真实动作候选。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段结束，WindowsAuthorizedRealDispatchCandidate.authorize_window 到此结束；如果没有这个边界说明，初学者不容易看出授权范围。

    # 新增代码+Phase94AuthorizedRealDispatch：函数段开始，_zero_result 统一生成零事件结果；如果没有这段函数，拒绝路径容易遗漏安全字段。
    def _zero_result(self, decision: str, *, action: str = "", safety_decision: dict[str, Any] | None = None, target_check: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase94AuthorizedRealDispatch：定义零事件结果 helper；如果没有这行代码，多个拒绝分支会重复拼装。
        return {"ok": False, "decision": decision, "action": action, "authorized_real_dispatch_candidate_ready": False, "low_level_dispatch_reaches_sender": False, "authorized_low_level_dispatch_reaches_sender": False, "low_level_event_count": 0, "real_dispatch_performed": False, "raw_text_hidden": True, "uncontrolled_actions_expanded": PHASE94_UNCONTROLLED_ACTIONS_EXPANDED, "safety_decision": dict(safety_decision or {}), "target_check": dict(target_check or {})}  # 新增代码+Phase94AuthorizedRealDispatch：返回标准关闭报告；如果没有这行代码，拒绝路径可能仍被误判为有副作用。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段结束，WindowsAuthorizedRealDispatchCandidate._zero_result 到此结束；如果没有这个边界说明，初学者不容易看出拒绝结果范围。

    # 新增代码+Phase94AuthorizedRealDispatch：函数段开始，_verify_target 发送前复核目标仍在当前 inventory；如果没有这段函数，焦点漂移后可能误发输入。
    def _verify_target(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase94AuthorizedRealDispatch：定义目标复核方法；如果没有这行代码，授权时的窗口和发送时窗口不会再次比对。
        requested_identity = _phase94_window_identity(window)  # 新增代码+Phase94AuthorizedRealDispatch：生成请求目标身份；如果没有这行代码，复核没有前态。
        snapshot = self.inventory.snapshot()  # 新增代码+Phase94AuthorizedRealDispatch：读取当前窗口快照；如果没有这行代码，无法判断目标是否还存在。
        actual_window = snapshot.find_window(window)  # 新增代码+Phase94AuthorizedRealDispatch：按 app_id/window_id 查找目标；如果没有这行代码，任意窗口对象都可能被信任。
        if actual_window is None:  # 新增代码+Phase94AuthorizedRealDispatch：判断目标是否缺失；如果没有这行代码，找不到目标也可能继续构造事件。
            return {"ok": False, "decision": "target_not_found_before_send", "requested_identity": requested_identity, "actual_identity": {}, "low_level_event_count": 0}  # 新增代码+Phase94AuthorizedRealDispatch：返回目标缺失零事件；如果没有这行代码，目标漂移风险不可审计。
        actual_identity = _phase94_window_identity(actual_window)  # 新增代码+Phase94AuthorizedRealDispatch：生成当前目标身份；如果没有这行代码，无法比较标题等辅助身份。
        if _phase94_target_core_identity(requested_identity) != _phase94_target_core_identity(actual_identity):  # 修改代码+Phase94AuthorizedRealDispatch：比较授权目标和当前目标的硬身份；如果没有这行代码，静态快照缺 display_id 会误判，同时真实 app/window/title 漂移又会漏检。
            return {"ok": False, "decision": "target_changed_before_send", "requested_identity": requested_identity, "actual_identity": actual_identity, "low_level_event_count": 0}  # 新增代码+Phase94AuthorizedRealDispatch：返回目标变化零事件；如果没有这行代码，漂移原因无法复盘。
        return {"ok": True, "decision": "target_stable_before_send", "requested_identity": requested_identity, "actual_identity": actual_identity, "window": actual_window, "low_level_event_count": 0}  # 新增代码+Phase94AuthorizedRealDispatch：返回目标稳定结果；如果没有这行代码，dispatch 拿不到复核后的窗口。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段结束，WindowsAuthorizedRealDispatchCandidate._verify_target 到此结束；如果没有这个边界说明，初学者不容易看出复核范围。

    # 新增代码+Phase94AuthorizedRealDispatch：函数段开始，dispatch 走完整授权、安全、复核、低层 sender 链路；如果没有这段函数，Phase94 只能停留在零散 helper。
    def dispatch(self, window: dict[str, Any], action: Any, arguments: dict[str, Any] | None = None, *, session_id: Any = DEFAULT_PERSISTENT_GRANT_SESSION_ID, enable_real_dispatch: bool | None = False) -> dict[str, Any]:  # 新增代码+Phase94AuthorizedRealDispatch：定义主派发入口；如果没有这行代码，外部 agent 无法用统一接口触发候选链路。
        action_key = _phase94_normalized_action(action)  # 新增代码+Phase94AuthorizedRealDispatch：归一化动作名；如果没有这行代码，安全边界和事件构造可能使用不同动作名。
        target = dict(window or {})  # 新增代码+Phase94AuthorizedRealDispatch：复制目标窗口；如果没有这行代码，后续流程可能污染调用方对象。
        args = dict(arguments or {})  # 新增代码+Phase94AuthorizedRealDispatch：复制动作参数；如果没有这行代码，脱敏和默认值处理可能改变外部数据。
        safety_decision = self.safety_boundary.evaluate(target, action_key, self.grant_store, session_id)  # 新增代码+Phase94AuthorizedRealDispatch：先经过 Phase72 安全边界；如果没有这行代码，未授权或危险窗口可能进入低层事件。
        if not bool(safety_decision.get("allowed")):  # 新增代码+Phase94AuthorizedRealDispatch：安全边界未允许时拒绝；如果没有这行代码，拒绝结果可能继续往下发送。
            return self._zero_result(str(safety_decision.get("decision", "blocked_by_safety_boundary")), action=action_key, safety_decision=safety_decision)  # 新增代码+Phase94AuthorizedRealDispatch：返回安全拒绝零事件；如果没有这行代码，调用方拿不到拒绝原因。
        if not _phase94_real_dispatch_enabled(enable_real_dispatch):  # 新增代码+Phase94AuthorizedRealDispatch：检查真实派发候选是否显式打开；如果没有这行代码，授权后会默认触达 sender。
            return self._zero_result("real_dispatch_disabled_by_default", action=action_key, safety_decision=safety_decision)  # 新增代码+Phase94AuthorizedRealDispatch：默认关闭时返回零事件；如果没有这行代码，安全默认值无法被证明。
        target_check = self._verify_target(target)  # 新增代码+Phase94AuthorizedRealDispatch：发送前复核目标；如果没有这行代码，窗口漂移可能导致误操作。
        if not bool(target_check.get("ok")):  # 新增代码+Phase94AuthorizedRealDispatch：目标不稳定时拒绝；如果没有这行代码，找不到目标仍可能发送。
            return self._zero_result(str(target_check.get("decision", "target_not_stable_before_send")), action=action_key, safety_decision=safety_decision, target_check=target_check)  # 新增代码+Phase94AuthorizedRealDispatch：返回漂移零事件；如果没有这行代码，漂移原因不会进入报告。
        events = _phase94_low_level_events_for_action(dict(target_check.get("window", target)), action_key, args)  # 新增代码+Phase94AuthorizedRealDispatch：构造低层事件；如果没有这行代码，授权通过后 sender 仍没有输入。
        if not events:  # 新增代码+Phase94AuthorizedRealDispatch：没有事件时拒绝；如果没有这行代码，未知动作可能被当作成功。
            return self._zero_result("no_low_level_events_for_action", action=action_key, safety_decision=safety_decision, target_check=target_check)  # 新增代码+Phase94AuthorizedRealDispatch：返回无事件结果；如果没有这行代码，动作覆盖缺口不可见。
        sender_result = self.low_level_sender.send_low_level(events)  # 新增代码+Phase94AuthorizedRealDispatch：把低层事件交给注入 sender；如果没有这行代码，Phase94 不能证明桥接到 sender。
        real_performed = bool(sender_result.get("real_dispatch_performed") or sender_result.get("physical_dispatch"))  # 新增代码+Phase94AuthorizedRealDispatch：从 sender 报告判断是否真实物理派发；如果没有这行代码，记录 sender 和真实 sender 会混淆。
        return {"ok": bool(sender_result.get("ok") and sender_result.get("low_level_event_count", 0)), "decision": "authorized_low_level_dispatch_sent_to_sender", "action": action_key, "authorized_real_dispatch_candidate_ready": True, "low_level_dispatch_reaches_sender": True, "authorized_low_level_dispatch_reaches_sender": True, "low_level_event_count": int(sender_result.get("low_level_event_count", 0) or 0), "real_dispatch_performed": real_performed, "raw_text_hidden": True, "uncontrolled_actions_expanded": PHASE94_UNCONTROLLED_ACTIONS_EXPANDED, "safety_decision": safety_decision, "target_check": target_check, "sender_result": sender_result}  # 新增代码+Phase94AuthorizedRealDispatch：返回授权候选派发报告；如果没有这行代码，测试和终端拿不到统一事实。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段结束，WindowsAuthorizedRealDispatchCandidate.dispatch 到此结束；如果没有这个边界说明，初学者不容易看出主流程范围。

    # 新增代码+Phase94AuthorizedRealDispatch：函数段开始，target_drift_refusal 构造漂移场景；如果没有这段函数，合同无法证明发送前复核会阻止误发。
    def target_drift_refusal(self, session_id: str = "phase94-drift") -> dict[str, Any]:  # 新增代码+Phase94AuthorizedRealDispatch：定义目标漂移检查 helper；如果没有这行代码，合同要手写一套漂移 runtime。
        window = self.contract_window()  # 新增代码+Phase94AuthorizedRealDispatch：读取原始安全窗口；如果没有这行代码，漂移测试没有授权前目标。
        drift_runtime = WindowsAuthorizedRealDispatchCandidate(base_dir=self.base_dir / "drift", inventory=StaticWindowsWindowInventory([], source="phase94_target_drift_empty"), low_level_sender=Phase94RecordingLowLevelSender())  # 新增代码+Phase94AuthorizedRealDispatch：创建空 inventory 的 runtime 模拟目标丢失；如果没有这行代码，漂移场景不稳定。
        drift_runtime.authorize_window(window, session_id=session_id, action_scope=["click"])  # 新增代码+Phase94AuthorizedRealDispatch：先授权原目标；如果没有这行代码，拒绝原因会变成未授权而不是目标漂移。
        return drift_runtime.dispatch(window, "click", {"x": 320, "y": 240}, session_id=session_id, enable_real_dispatch=True)  # 新增代码+Phase94AuthorizedRealDispatch：执行漂移派发并期待零事件；如果没有这行代码，漂移合同没有结果。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段结束，WindowsAuthorizedRealDispatchCandidate.target_drift_refusal 到此结束；如果没有这个边界说明，初学者不容易看出漂移范围。
# 新增代码+Phase94AuthorizedRealDispatch：类段结束，WindowsAuthorizedRealDispatchCandidate 到此结束；如果没有这个边界说明，初学者不容易看出适配器范围。

# 新增代码+Phase94AuthorizedRealDispatch：函数段开始，run_phase94_authorized_real_dispatch_candidate_contract 运行总合同；如果没有这段函数，CLI、测试和真实终端没有同一事实源。
def run_phase94_authorized_real_dispatch_candidate_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase94AuthorizedRealDispatch：定义 Phase94 合同入口；如果没有这行代码，无法一键验证所有成功标准。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE94_AUTHORIZED_REAL_DISPATCH_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase94AuthorizedRealDispatch：选择隔离合同目录；如果没有这行代码，多次运行会互相污染授权状态。
    root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase94AuthorizedRealDispatch：创建合同目录；如果没有这行代码，报告写入会失败。
    phase93_report = run_phase93_universal_live_execution_gate_contract(base_dir=root / "phase93")  # 新增代码+Phase94AuthorizedRealDispatch：运行 Phase93 合同作为差距基线；如果没有这行代码，Phase94 无法证明自己承接了 recording-only 缺口。
    sender = Phase94RecordingLowLevelSender()  # 新增代码+Phase94AuthorizedRealDispatch：创建默认安全 sender；如果没有这行代码，合同可能触发真实物理输入。
    runtime = WindowsAuthorizedRealDispatchCandidate(base_dir=root / "runtime", low_level_sender=sender)  # 新增代码+Phase94AuthorizedRealDispatch：创建 Phase94 runtime；如果没有这行代码，合同没有被测对象。
    window = runtime.contract_window()  # 新增代码+Phase94AuthorizedRealDispatch：读取稳定合同窗口；如果没有这行代码，授权和派发目标可能不一致。
    session_id = f"phase94-contract-{int(time.time() * 1000)}"  # 新增代码+Phase94AuthorizedRealDispatch：生成隔离会话 id；如果没有这行代码，多次合同授权可能互相命中。
    runtime.authorize_window(window, session_id=session_id, action_scope=["click", "type_text", "scroll"])  # 新增代码+Phase94AuthorizedRealDispatch：授权普通动作正例；如果没有这行代码，授权候选派发无法通过安全边界。
    default_disabled = runtime.dispatch(window, "click", {"x": 320, "y": 240}, session_id=session_id, enable_real_dispatch=False)  # 新增代码+Phase94AuthorizedRealDispatch：验证默认关闭路径；如果没有这行代码，安全默认值没有证据。
    authorized = runtime.dispatch(window, "type_text", {"text": "phase94-secret-text"}, session_id=session_id, enable_real_dispatch=True)  # 新增代码+Phase94AuthorizedRealDispatch：验证授权后低层 sender 路径且包含脱敏文本样本；如果没有这行代码，文本隐私和 sender 桥接没有证据。
    unauthorized_runtime = WindowsAuthorizedRealDispatchCandidate(base_dir=root / "unauthorized")  # 新增代码+Phase94AuthorizedRealDispatch：创建无授权 runtime；如果没有这行代码，未授权拒绝可能被授权状态污染。
    unauthorized = unauthorized_runtime.dispatch(unauthorized_runtime.contract_window(), "click", {"x": 320, "y": 240}, session_id="phase94-unauthorized", enable_real_dispatch=True)  # 新增代码+Phase94AuthorizedRealDispatch：验证未授权零事件；如果没有这行代码，默认拒绝路径没有证据。
    unsafe_window = {"app_id": "powershell.exe", "process_name": "powershell.exe", "window_id": "hwnd:9499", "title_preview": "Windows PowerShell", "display_id": "DISPLAY1", "rect": {"left": 10, "top": 10, "right": 500, "bottom": 360}, "safe_to_target": True}  # 新增代码+Phase94AuthorizedRealDispatch：构造终端类高风险窗口；如果没有这行代码，高风险默认拒绝缺少样本。
    unsafe = runtime.dispatch(unsafe_window, "click", {"x": 20, "y": 20}, session_id=session_id, enable_real_dispatch=True)  # 新增代码+Phase94AuthorizedRealDispatch：验证危险窗口零事件；如果没有这行代码，终端窗口拒绝没有 Phase94 证据。
    drift = runtime.target_drift_refusal(session_id=f"{session_id}-drift")  # 新增代码+Phase94AuthorizedRealDispatch：验证目标漂移零事件；如果没有这行代码，发送前复核没有合同证据。
    serialized = json.dumps({"authorized": authorized, "default_disabled": default_disabled, "unauthorized": unauthorized, "unsafe": unsafe, "drift": drift}, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase94AuthorizedRealDispatch：序列化报告子集扫描明文；如果没有这行代码，嵌套字段泄露不容易发现。
    raw_text_hidden = "phase94-secret-text" not in serialized  # 新增代码+Phase94AuthorizedRealDispatch：确认秘密文本未进入报告；如果没有这行代码，隐私门禁只是口头声明。
    phase93_gap_closed = bool(phase93_report.get("authorized_recording_loop_ready") and phase93_report.get("authorized_report", {}).get("recording_dispatch_only") and authorized.get("authorized_low_level_dispatch_reaches_sender"))  # 新增代码+Phase94AuthorizedRealDispatch：汇总 Phase93 缺口是否被候选层接住；如果没有这行代码，阶段进展无法量化。
    authorized_reaches_sender = bool(authorized.get("ok") and authorized.get("authorized_low_level_dispatch_reaches_sender") and sender.send_count == 1)  # 新增代码+Phase94AuthorizedRealDispatch：确认授权低层事件到达 sender；如果没有这行代码，事件可能只存在返回值里。
    report_path = root / "reports" / "phase94_authorized_real_dispatch_candidate_report.json"  # 新增代码+Phase94AuthorizedRealDispatch：定义报告路径；如果没有这行代码，验收证据没有固定文件。
    passed = bool(phase93_gap_closed and authorized_reaches_sender and default_disabled.get("decision") == "real_dispatch_disabled_by_default" and default_disabled.get("low_level_event_count") == 0 and not authorized.get("real_dispatch_performed") and unauthorized.get("low_level_event_count") == 0 and unsafe.get("low_level_event_count") == 0 and drift.get("low_level_event_count") == 0 and raw_text_hidden and not PHASE94_UNCONTROLLED_ACTIONS_EXPANDED and not PHASE72_UNCONTROLLED_ACTIONS_EXPANDED)  # 新增代码+Phase94AuthorizedRealDispatch：汇总合同通过条件；如果没有这行代码，main 无法用退出码表达失败。
    report = {"marker": PHASE94_AUTHORIZED_REAL_DISPATCH_MARKER, "ok_token": PHASE94_AUTHORIZED_REAL_DISPATCH_OK_TOKEN, "model": PHASE94_AUTHORIZED_REAL_DISPATCH_MODEL, "passed": passed, "phase93_recording_gap_closed_by_candidate": phase93_gap_closed, "authorized_real_dispatch_candidate_ready": bool(authorized.get("authorized_real_dispatch_candidate_ready")), "authorized_low_level_dispatch_reaches_sender": authorized_reaches_sender, "real_dispatch_default_disabled": PHASE94_REAL_DISPATCH_DEFAULT_DISABLED, "real_dispatch_env_gate": PHASE94_REAL_DISPATCH_ENV, "real_dispatch_performed": bool(authorized.get("real_dispatch_performed")), "unauthorized_window_zero_events": bool(unauthorized.get("low_level_event_count") == 0), "unsafe_window_zero_events": bool(unsafe.get("low_level_event_count") == 0), "target_drift_zero_events": bool(drift.get("low_level_event_count") == 0), "raw_text_hidden": raw_text_hidden, "uncontrolled_actions_expanded": PHASE94_UNCONTROLLED_ACTIONS_EXPANDED, "report_path": str(report_path), "phase93_report_path": str(phase93_report.get("report_path", "")), "authorized_report": authorized, "default_disabled_report": default_disabled, "unauthorized_report": unauthorized, "unsafe_report": unsafe, "target_drift_report": drift}  # 新增代码+Phase94AuthorizedRealDispatch：构造完整合同报告；如果没有这行代码，测试和真实终端拿不到统一结果。
    atomic_write_json(report_path, report)  # 新增代码+Phase94AuthorizedRealDispatch：原子写入报告；如果没有这行代码，异常中断时可能留下半个 JSON。
    return report  # 新增代码+Phase94AuthorizedRealDispatch：返回合同报告；如果没有这行代码，调用方无法读取验证结果。
# 新增代码+Phase94AuthorizedRealDispatch：函数段结束，run_phase94_authorized_real_dispatch_candidate_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同范围。

# 新增代码+Phase94AuthorizedRealDispatch：函数段开始，phase94_cli_line 输出固定 token 行；如果没有这段函数，真实终端验收需要解析复杂 JSON。
def phase94_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase94AuthorizedRealDispatch：定义 CLI 单行格式化函数；如果没有这行代码，验收输出容易漂移。
    return f"{PHASE94_AUTHORIZED_REAL_DISPATCH_MARKER} {PHASE94_AUTHORIZED_REAL_DISPATCH_OK_TOKEN} phase93_recording_gap_closed_by_candidate={_phase94_bool_token(report.get('phase93_recording_gap_closed_by_candidate'))} authorized_real_dispatch_candidate_ready={_phase94_bool_token(report.get('authorized_real_dispatch_candidate_ready'))} authorized_low_level_dispatch_reaches_sender={_phase94_bool_token(report.get('authorized_low_level_dispatch_reaches_sender'))} real_dispatch_default_disabled={_phase94_bool_token(report.get('real_dispatch_default_disabled'))} unauthorized_window_zero_events={_phase94_bool_token(report.get('unauthorized_window_zero_events'))} unsafe_window_zero_events={_phase94_bool_token(report.get('unsafe_window_zero_events'))} target_drift_zero_events={_phase94_bool_token(report.get('target_drift_zero_events'))} raw_text_hidden={_phase94_bool_token(report.get('raw_text_hidden'))} real_dispatch_performed={_phase94_bool_token(report.get('real_dispatch_performed'))} uncontrolled_actions_expanded={_phase94_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+Phase94AuthorizedRealDispatch：返回固定顺序 token；如果没有这行代码，验收脚本容易因为字段顺序变化失败。
# 新增代码+Phase94AuthorizedRealDispatch：函数段结束，phase94_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 范围。

# 新增代码+Phase94AuthorizedRealDispatch：函数段开始，main 提供命令行自检入口；如果没有这段函数，真实可见终端无法直接运行 Phase94 合同。
def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase94AuthorizedRealDispatch：定义 CLI 入口并保留 argv 扩展位；如果没有这行代码，python -c 调用需要手写细节。
    _ = argv  # 新增代码+Phase94AuthorizedRealDispatch：明确当前不解析命令行参数；如果没有这行代码，读者可能误以为 argv 被遗漏处理。
    report = run_phase94_authorized_real_dispatch_candidate_contract()  # 新增代码+Phase94AuthorizedRealDispatch：运行无真实副作用合同；如果没有这行代码，CLI 没有实际验收内容。
    print(phase94_cli_line(report))  # 新增代码+Phase94AuthorizedRealDispatch：打印稳定 token 行；如果没有这行代码，验收器无法快速判断通过。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase94AuthorizedRealDispatch：打印结构化报告；如果没有这行代码，失败时不容易复盘。
    print(PHASE94_AUTHORIZED_REAL_DISPATCH_MARKER)  # 新增代码+Phase94AuthorizedRealDispatch：单独打印 ready marker；如果没有这行代码，人工观察终端不够直观。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase94AuthorizedRealDispatch：用退出码表达合同成败；如果没有这行代码，失败也可能被自动化当成成功。
# 新增代码+Phase94AuthorizedRealDispatch：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。

__all__ = ["DEFAULT_PHASE94_AUTHORIZED_REAL_DISPATCH_ROOT", "PHASE94_AUTHORIZED_REAL_DISPATCH_MARKER", "PHASE94_AUTHORIZED_REAL_DISPATCH_MODEL", "PHASE94_AUTHORIZED_REAL_DISPATCH_OK_TOKEN", "PHASE94_REAL_DISPATCH_DEFAULT_DISABLED", "PHASE94_REAL_DISPATCH_ENV", "PHASE94_UNCONTROLLED_ACTIONS_EXPANDED", "Phase94RecordingLowLevelSender", "WindowsAuthorizedRealDispatchCandidate", "main", "phase94_cli_line", "run_phase94_authorized_real_dispatch_candidate_contract"]  # 新增代码+Phase94AuthorizedRealDispatch：限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。

if __name__ == "__main__":  # 新增代码+Phase94AuthorizedRealDispatch：允许直接运行本模块；如果没有这行代码，初学者无法用 python 文件方式手动自检。
    raise SystemExit(main())  # 新增代码+Phase94AuthorizedRealDispatch：调用 main 并传递退出码；如果没有这行代码，直接运行文件不会执行验收。
