"""Windows Computer Use 动作策略和证据 envelope。"""  # 新增代码+Phase30ComputerUseActionGate: 说明本文件集中处理坐标转换、脱敏和动作证据；如果没有这个文件，controller 会继续堆高风险细节。

from __future__ import annotations  # 新增代码+Phase30ComputerUseActionGate: 延迟解析类型注解；如果没有这行代码，旧运行路径遇到前向类型时更容易导入失败。

import hashlib  # 新增代码+Phase30ComputerUseActionGate: 用 SHA256 生成文本短指纹；如果没有这行代码，审计只能在保存原文和完全不可追踪之间二选一。
from typing import Any  # 新增代码+Phase30ComputerUseActionGate: 引入通用 JSON 值类型；如果没有这行代码，策略函数参数边界不清楚。


try:  # 新增代码+Phase39WindowsCoordinates: 优先用包路径导入 Phase39 坐标模型；如果没有这行代码，动作策略无法接入 DPI 和多显示器换算。
    from learning_agent.computer_use.coordinates import PHASE39_COORDINATE_MODEL, build_coordinate_context  # 新增代码+Phase39WindowsCoordinates: 导入坐标模型版本和核心换算函数；如果没有这行代码，后端仍会收到旧逻辑屏幕坐标。
except ModuleNotFoundError as error:  # 新增代码+Phase39WindowsCoordinates: 捕获 start_oauth_agent 脚本模式下包名前缀不可用；如果没有这行代码，真实终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.coordinates"}:  # 新增代码+Phase39WindowsCoordinates: 只允许目标包路径缺失时 fallback；如果没有这行代码，coordinates 内部真实 bug 会被误吞。
        raise  # 新增代码+Phase39WindowsCoordinates: 重新抛出非路径类导入错误；如果没有这行代码，排查坐标模块问题会很困难。
    from computer_use.coordinates import PHASE39_COORDINATE_MODEL, build_coordinate_context  # 新增代码+Phase39WindowsCoordinates: 脚本模式下从本地包导入坐标模型；如果没有这行代码，bat 入口无法加载 Phase39 动作策略。

POLICY_VERSION = "phase30_window_relative_action_gate_v1"  # 新增代码+Phase30ComputerUseActionGate: 固定本阶段策略版本；如果没有这行代码，未来审计无法区分不同策略产生的证据。
COORDINATE_ACTIONS = {"move_mouse", "click", "double_click", "scroll"}  # 新增代码+Phase30ComputerUseActionGate: 声明需要坐标处理的动作集合；如果没有这行代码，文本动作可能被错误做坐标转换。
TEXT_FIELD_NAME = "text"  # 新增代码+Phase30ComputerUseActionGate: 集中声明敏感文本字段名；如果没有这行代码，脱敏逻辑容易写出不一致字段。


# 新增代码+Phase30ComputerUseActionGate: 函数段开始，safe_int 用于把模型参数安全转成整数；如果没有这段函数，坐标转换会在字符串或空值上崩溃，作者意图是让动作策略对模型输入更稳健。
def safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase30ComputerUseActionGate: 定义安全整数转换函数；如果没有这行代码，每个坐标读取点都要重复 try/except。
    try:  # 新增代码+Phase30ComputerUseActionGate: 捕获模型传入非整数的情况；如果没有这行代码，异常会直接中断工具调用。
        return int(value)  # 新增代码+Phase30ComputerUseActionGate: 返回整数形式的值；如果没有这行代码，坐标无法参与加法。
    except (TypeError, ValueError):  # 新增代码+Phase30ComputerUseActionGate: 处理空值和不可转换字符串；如果没有这行代码，坏参数无法安全兜底。
        return int(default)  # 新增代码+Phase30ComputerUseActionGate: 返回默认值；如果没有这行代码，调用方仍然拿不到稳定坐标。
# 新增代码+Phase30ComputerUseActionGate: 函数段结束，safe_int 到此结束；如果没有这个结束标记，初学者不容易看出转换 helper 的边界。


# 新增代码+Phase30ComputerUseActionGate: 函数段开始，text_sha256_16 用于生成不泄露原文的短指纹；如果没有这段函数，审计既难以关联文本动作又可能保存敏感文本。
def text_sha256_16(raw_text: Any) -> str:  # 新增代码+Phase30ComputerUseActionGate: 定义文本短哈希函数；如果没有这行代码，动作证据无法在不存原文的情况下追踪同一文本。
    text = str(raw_text or "")  # 新增代码+Phase30ComputerUseActionGate: 把任意文本参数规范成字符串；如果没有这行代码，None 或数字会让 encode 不稳定。
    if not text:  # 新增代码+Phase30ComputerUseActionGate: 空文本不需要生成哈希；如果没有这行代码，空输入也会产生看似有意义的指纹。
        return ""  # 新增代码+Phase30ComputerUseActionGate: 返回空指纹；如果没有这行代码，调用方无法区分无文本和空字符串。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase30ComputerUseActionGate: 返回前 16 位 SHA256；如果没有这行代码，审计缺少安全的文本关联字段。
# 新增代码+Phase30ComputerUseActionGate: 函数段结束，text_sha256_16 到此结束；如果没有这个结束标记，读者不容易看出哈希 helper 的边界。


# 新增代码+Phase30ComputerUseActionGate: 函数段开始，window_rect 用于提取窗口矩形；如果没有这段函数，窗口相对坐标无法转换成屏幕坐标，作者意图是只信任窗口对象中的 rect 字段。
def window_rect(raw_window: Any) -> dict[str, int]:  # 新增代码+Phase30ComputerUseActionGate: 定义窗口矩形读取函数；如果没有这行代码，坐标策略要直接触碰松散 dict。
    if not isinstance(raw_window, dict):  # 新增代码+Phase30ComputerUseActionGate: 只接受对象形式窗口；如果没有这行代码，字符串窗口会让 get 调用崩溃。
        return {}  # 新增代码+Phase30ComputerUseActionGate: 非对象返回空 rect；如果没有这行代码，调用方无法安全判断无 rect。
    raw_rect = raw_window.get("rect", {})  # 新增代码+Phase30ComputerUseActionGate: 读取窗口矩形字段；如果没有这行代码，策略无法找到窗口原点。
    if not isinstance(raw_rect, dict):  # 新增代码+Phase30ComputerUseActionGate: 检查 rect 是否是对象；如果没有这行代码，坏 rect 会导致坐标读取异常。
        return {}  # 新增代码+Phase30ComputerUseActionGate: 坏 rect 返回空对象；如果没有这行代码，后续 int 转换仍可能误用坏数据。
    return {"left": safe_int(raw_rect.get("left")), "top": safe_int(raw_rect.get("top")), "right": safe_int(raw_rect.get("right")), "bottom": safe_int(raw_rect.get("bottom"))}  # 新增代码+Phase30ComputerUseActionGate: 返回标准四边矩形；如果没有这行代码，转换函数拿不到窗口原点和尺寸。
# 新增代码+Phase30ComputerUseActionGate: 函数段结束，window_rect 到此结束；如果没有这个结束标记，读者不容易看出 rect helper 的边界。


# 新增代码+Phase30ComputerUseActionGate: 函数段开始，target_window_for_evidence 用于生成安全窗口摘要；如果没有这段函数，action evidence 可能携带过多窗口原始字段，作者意图是记录可追踪但不过量的窗口信息。
def target_window_for_evidence(raw_window: Any) -> dict[str, Any]:  # 新增代码+Phase30ComputerUseActionGate: 定义目标窗口证据摘要函数；如果没有这行代码，证据 envelope 无法稳定描述目标窗口。
    if not isinstance(raw_window, dict):  # 新增代码+Phase30ComputerUseActionGate: 只接受 dict 窗口；如果没有这行代码，非对象输入会污染证据结构。
        return {}  # 新增代码+Phase30ComputerUseActionGate: 非对象返回空摘要；如果没有这行代码，调用方无法安全处理无窗口动作。
    allowed_keys = ("app_id", "window_id", "title_preview", "process_path_hash", "captured_at")  # 新增代码+Phase30ComputerUseActionGate: 限定窗口证据字段；如果没有这行代码，未知窗口字段可能泄露到审计。
    summary = {key: raw_window.get(key, "") for key in allowed_keys if raw_window.get(key, "")}  # 新增代码+Phase30ComputerUseActionGate: 复制非空白名单字段；如果没有这行代码，证据会缺少目标窗口身份。
    rect = window_rect(raw_window)  # 新增代码+Phase30ComputerUseActionGate: 读取标准 rect；如果没有这行代码，证据缺少坐标转换依据。
    if rect:  # 新增代码+Phase30ComputerUseActionGate: 只有存在 rect 时才写入；如果没有这行代码，空 rect 也会污染证据。
        summary["rect"] = rect  # 新增代码+Phase30ComputerUseActionGate: 保存窗口几何；如果没有这行代码，审计无法解释相对坐标如何转换。
    return summary  # 新增代码+Phase30ComputerUseActionGate: 返回安全窗口摘要；如果没有这行代码，调用方拿不到证据对象。
# 新增代码+Phase30ComputerUseActionGate: 函数段结束，target_window_for_evidence 到此结束；如果没有这个结束标记，读者不容易看出窗口证据边界。


# 新增代码+Phase30ComputerUseActionGate: 函数段开始，redact_action_arguments 用于脱敏可见日志参数；如果没有这段函数，内存后端和审计日志可能保存用户输入的密码或 token。
def redact_action_arguments(action: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase30ComputerUseActionGate: 定义动作参数脱敏函数；如果没有这行代码，controller 和 backend 会各自手写不一致脱敏。
    redacted: dict[str, Any] = {}  # 新增代码+Phase30ComputerUseActionGate: 准备脱敏后的参数字典；如果没有这行代码，函数没有返回容器。
    for key, value in dict(arguments).items():  # 新增代码+Phase30ComputerUseActionGate: 遍历原始参数副本；如果没有这行代码，无法逐字段删除敏感文本。
        if key == TEXT_FIELD_NAME:  # 新增代码+Phase30ComputerUseActionGate: 识别敏感文本字段；如果没有这行代码，原始 text 会进入日志。
            redacted["text_length"] = len(str(value or ""))  # 新增代码+Phase30ComputerUseActionGate: 只记录文本长度；如果没有这行代码，审计无法知道是否发生文本输入。
            redacted["text_sha256_16"] = text_sha256_16(value)  # 新增代码+Phase30ComputerUseActionGate: 记录短哈希；如果没有这行代码，审计无法在不泄露原文时关联文本。
            redacted["text_redacted"] = True  # 新增代码+Phase30ComputerUseActionGate: 明确标记文本已脱敏；如果没有这行代码，读者可能误以为字段缺失是 bug。
            continue  # 新增代码+Phase30ComputerUseActionGate: 跳过原始 text 写入；如果没有这行代码，敏感文本会被继续保存。
        redacted[key] = value  # 新增代码+Phase30ComputerUseActionGate: 保存非敏感字段；如果没有这行代码，坐标、窗口和确认标记会丢失。
    redacted["action"] = action  # 新增代码+Phase30ComputerUseActionGate: 保证脱敏参数仍包含动作名；如果没有这行代码，日志不知道是哪类动作。
    return redacted  # 新增代码+Phase30ComputerUseActionGate: 返回脱敏后的参数；如果没有这行代码，调用方拿不到安全日志内容。
# 新增代码+Phase30ComputerUseActionGate: 函数段结束，redact_action_arguments 到此结束；如果没有这个结束标记，读者不容易看出脱敏边界。


# 新增代码+Phase30ComputerUseActionGate: 函数段开始，prepare_action_arguments 用于把窗口相对坐标转换成后端坐标；如果没有这段函数，真实鼠标点击会把窗口内坐标误当屏幕坐标。
def prepare_action_arguments(action: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase30ComputerUseActionGate: 定义动作参数准备函数；如果没有这行代码，controller 需要直接操作坐标细节。
    backend_arguments = dict(arguments)  # 新增代码+Phase30ComputerUseActionGate: 复制参数用于传给后端；如果没有这行代码，转换会修改调用方原始对象。
    coordinate_used: dict[str, Any] = {}  # 新增代码+Phase30ComputerUseActionGate: 准备坐标证据对象；如果没有这行代码，结果无法说明实际使用的坐标。
    raw_window = arguments.get("window")  # 新增代码+Phase30ComputerUseActionGate: 读取目标窗口；如果没有这行代码，无法判断是否能做窗口相对转换。
    rect = window_rect(raw_window)  # 新增代码+Phase30ComputerUseActionGate: 读取窗口矩形；如果没有这行代码，相对坐标没有窗口原点。
    if action in COORDINATE_ACTIONS and "x" in arguments and "y" in arguments and rect:  # 新增代码+Phase30ComputerUseActionGate: 有坐标动作、x/y 和 rect 时做转换；如果没有这行代码，窗口相对坐标不会转换。
        relative_x = safe_int(arguments.get("x"))  # 新增代码+Phase30ComputerUseActionGate: 读取窗口内 x；如果没有这行代码，横坐标无法和窗口 left 相加。
        relative_y = safe_int(arguments.get("y"))  # 新增代码+Phase30ComputerUseActionGate: 读取窗口内 y；如果没有这行代码，纵坐标无法和窗口 top 相加。
        coordinate_context = build_coordinate_context(raw_window, relative_x, relative_y)  # 新增代码+Phase39WindowsCoordinates: 使用统一坐标模型换算逻辑坐标、显示器相对坐标和物理坐标；如果没有这行代码，高 DPI 或副屏动作仍会落错位置。
        physical_screen = dict(coordinate_context.get("physical_screen", {}))  # 新增代码+Phase39WindowsCoordinates: 读取后端真正要使用的物理屏幕坐标；如果没有这行代码，后端参数无法和坐标模型结果对齐。
        screen_x = safe_int(physical_screen.get("x"))  # 修改代码+Phase39WindowsCoordinates: 把最终 x 升级为物理像素坐标；如果没有这行代码，真实 SendInput 后端会继续收到逻辑坐标。
        screen_y = safe_int(physical_screen.get("y"))  # 修改代码+Phase39WindowsCoordinates: 把最终 y 升级为物理像素坐标；如果没有这行代码，真实 SendInput 后端会继续收到逻辑坐标。
        backend_arguments["window_relative_x"] = relative_x  # 新增代码+Phase30ComputerUseActionGate: 记录原始相对 x 供后端或测试审计；如果没有这行代码，无法复盘转换来源。
        backend_arguments["window_relative_y"] = relative_y  # 新增代码+Phase30ComputerUseActionGate: 记录原始相对 y 供后端或测试审计；如果没有这行代码，无法复盘转换来源。
        backend_arguments["x"] = screen_x  # 新增代码+Phase30ComputerUseActionGate: 覆盖为后端需要的屏幕 x；如果没有这行代码，真实后端会收到错误坐标空间。
        backend_arguments["y"] = screen_y  # 新增代码+Phase30ComputerUseActionGate: 覆盖为后端需要的屏幕 y；如果没有这行代码，真实后端会收到错误坐标空间。
        coordinate_used = {"space": "screen", "source": "window_relative", "x": screen_x, "y": screen_y, "relative_x": relative_x, "relative_y": relative_y, "window_origin": {"x": safe_int(rect.get("left")), "y": safe_int(rect.get("top"))}, "model": coordinate_context.get("model", PHASE39_COORDINATE_MODEL), "logical_screen": dict(coordinate_context.get("logical_screen", {})), "display_relative_logical": dict(coordinate_context.get("display_relative_logical", {})), "physical_screen": dict(coordinate_context.get("physical_screen", {})), "dpi_scale": dict(coordinate_context.get("dpi_scale", {})), "display": dict(coordinate_context.get("display", {})), "window_logical_rect": dict(coordinate_context.get("window_logical_rect", {})), "window_physical_rect": dict(coordinate_context.get("window_physical_rect", {}))}  # 修改代码+Phase39WindowsCoordinates: 保留 Phase30 兼容字段并新增完整坐标上下文；如果没有这行代码，审计无法解释 DPI、多显示器和最终物理像素来源。
    elif action in COORDINATE_ACTIONS and "x" in arguments and "y" in arguments:  # 新增代码+Phase30ComputerUseActionGate: 无 rect 但有坐标时记录原样屏幕输入；如果没有这行代码，旧兼容坐标动作没有证据。
        coordinate_used = {"space": "screen", "source": "screen_input", "x": safe_int(arguments.get("x")), "y": safe_int(arguments.get("y"))}  # 新增代码+Phase30ComputerUseActionGate: 记录原样屏幕坐标；如果没有这行代码，审计不知道最终使用了什么位置。
    return {"backend_arguments": backend_arguments, "coordinate_used": coordinate_used, "target_window": target_window_for_evidence(raw_window)}  # 新增代码+Phase30ComputerUseActionGate: 返回后端参数和证据摘要；如果没有这行代码，controller 拿不到转换结果。
# 新增代码+Phase30ComputerUseActionGate: 函数段结束，prepare_action_arguments 到此结束；如果没有这个结束标记，读者不容易看出坐标转换边界。


# 新增代码+Phase30ComputerUseActionGate: 函数段开始，build_action_evidence 用于组装最终动作证据 envelope；如果没有这段函数，结果、锁、窗口和坐标难以被一个 audit_id 串起来。
def build_action_evidence(action: str, original_arguments: dict[str, Any], prepared_action: dict[str, Any], lock_status: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase30ComputerUseActionGate: 定义 evidence 构造函数；如果没有这行代码，controller 会重复拼接证据字段。
    backend_arguments = dict(prepared_action.get("backend_arguments", {}))  # 新增代码+Phase30ComputerUseActionGate: 读取后端参数副本；如果没有这行代码，脱敏摘要无法基于最终坐标生成。
    evidence = {"policy_version": POLICY_VERSION, "action": action, "lock_session_id": str(lock_status.get("owner_session_id", "")), "target_window": dict(prepared_action.get("target_window", {})), "coordinate_used": dict(prepared_action.get("coordinate_used", {})), "argument_summary": redact_action_arguments(action, backend_arguments)}  # 新增代码+Phase30ComputerUseActionGate: 构造基础证据 envelope；如果没有这行代码，动作结果缺少统一可审计字段。
    if TEXT_FIELD_NAME in original_arguments:  # 新增代码+Phase30ComputerUseActionGate: 文本动作需要额外记录脱敏摘要；如果没有这行代码，type_text 证据无法显示文本长度。
        evidence["text_length"] = len(str(original_arguments.get(TEXT_FIELD_NAME, "") or ""))  # 新增代码+Phase30ComputerUseActionGate: 写入原始文本长度；如果没有这行代码，审计无法确认输入规模。
        evidence["text_sha256_16"] = text_sha256_16(original_arguments.get(TEXT_FIELD_NAME, ""))  # 新增代码+Phase30ComputerUseActionGate: 写入原始文本短哈希；如果没有这行代码，审计无法安全关联同一文本。
        evidence["text_redacted"] = True  # 新增代码+Phase30ComputerUseActionGate: 标记文本已脱敏；如果没有这行代码，读者可能误以为没有文本。
    return evidence  # 新增代码+Phase30ComputerUseActionGate: 返回完整动作证据；如果没有这行代码，controller 无法把 envelope 附到结果。
# 新增代码+Phase30ComputerUseActionGate: 函数段结束，build_action_evidence 到此结束；如果没有这个结束标记，读者不容易看出证据组装边界。
