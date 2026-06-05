"""Phase70 generic click/type/control actions for Windows Computer Use."""  # 新增代码+Phase70GenericControlActions: 标明本文件负责通用点击、输入和控件动作；如果没有这行代码，读者不容易区分 Phase70 与底层 SendInput 模块。
from __future__ import annotations  # 新增代码+Phase70GenericControlActions: 启用延迟类型注解，避免运行时因为类型提示互相引用而导入失败；如果没有这行代码，后续扩展 runtime 类型时更容易遇到循环导入。

import hashlib  # 新增代码+Phase70GenericControlActions: 导入 hashlib 生成动作前后短指纹；如果没有这行代码，动作证据只能暴露原始窗口或控件内容。
import json  # 新增代码+Phase70GenericControlActions: 导入 JSON 用于稳定序列化报告和指纹输入；如果没有这行代码，CLI 和证据格式会更容易漂移。
from typing import Any  # 新增代码+Phase70GenericControlActions: 导入 Any 描述 JSON 风格窗口、观察和动作参数；如果没有这行代码，接口边界不容易读懂。

try:  # 新增代码+Phase70GenericControlActions: 优先按包路径导入 Phase57 语义控件定位器；如果没有这段代码，unittest 和生产入口无法复用真实 locator。
    from learning_agent.computer_use.real_uia_locator import SemanticControlLocator  # 新增代码+Phase70GenericControlActions: 复用 Phase57 控件定位器；如果没有这行代码，Phase70 会重复造定位逻辑。
except ModuleNotFoundError as error:  # 新增代码+Phase70GenericControlActions: 兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，脚本模式导入可能失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.real_uia_locator"}:  # 新增代码+Phase70GenericControlActions: 只允许包路径缺失时 fallback；如果没有这行代码，内部真实 bug 会被误吞。
        raise  # 新增代码+Phase70GenericControlActions: 重新抛出非路径类导入错误；如果没有这行代码，底层 locator 问题会被隐藏。
    from computer_use.real_uia_locator import SemanticControlLocator  # type: ignore  # 新增代码+Phase70GenericControlActions: 脚本模式导入 Phase57 locator；如果没有这行代码，bat 入口无法运行 Phase70 合同。
try:  # 新增代码+VerifiedWindowActionsMaturity: 优先按包路径导入 Phase114 已验证窗口动作门禁；如果没有这段代码，Phase70 点击/输入无法复用统一身份门禁。
    from learning_agent.computer_use.closed_loop_executor import phase114_verified_action_gate  # 新增代码+VerifiedWindowActionsMaturity: 导入统一动作身份门禁函数；如果没有这行代码，点击和输入会各自手写身份判断。
except ModuleNotFoundError as error:  # 新增代码+VerifiedWindowActionsMaturity: 兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行的脚本模式；如果没有这段代码，真实终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.closed_loop_executor"}:  # 新增代码+VerifiedWindowActionsMaturity: 只允许包路径缺失时 fallback；如果没有这行代码，closed_loop_executor 内部真实错误会被吞掉。
        raise  # 新增代码+VerifiedWindowActionsMaturity: 重新抛出非路径类导入错误；如果没有这行代码，隐藏 bug 会变成难查的动作异常。
    from computer_use.closed_loop_executor import phase114_verified_action_gate  # type: ignore  # 新增代码+VerifiedWindowActionsMaturity: 脚本模式导入统一身份门禁；如果没有这行代码，bat 入口无法执行 Task6 动作门禁。


PHASE70_GENERIC_CONTROL_ACTIONS_MARKER = "PHASE70_GENERIC_CONTROL_ACTIONS_READY"  # 新增代码+Phase70GenericControlActions: 定义真实终端验收 ready 标记；如果没有这行代码，controller 无法稳定识别 Phase70 输出。
PHASE70_GENERIC_CONTROL_ACTIONS_OK_TOKEN = "PHASE70_GENERIC_CONTROL_ACTIONS_OK"  # 新增代码+Phase70GenericControlActions: 定义真实终端验收 OK 标记；如果没有这行代码，用户无法一眼确认本阶段合同通过。
PHASE70_GENERIC_CONTROL_ACTIONS_MODEL = "phase70_windows_generic_control_actions"  # 新增代码+Phase70GenericControlActions: 定义本阶段能力模型名称；如果没有这行代码，后续矩阵无法统一引用 Phase70 能力。
PHASE70_ACTIONS_EXPANDED = False  # 新增代码+Phase70GenericControlActions: 明确 Phase70 不新增底层桌面动作面；如果没有这行代码，用户可能误以为绕过了既有安全链。
PHASE70_VISUAL_POINT_AUTOMATION_ID = "phase70_visual_point"  # 新增代码+Phase70GenericControlActions: 定义视觉点合成控件 id；如果没有这行代码，视觉兜底无法复用 Phase62 控件点击接口。


def _phase70_bool_token(value: Any) -> str:  # 新增代码+Phase70GenericControlActions: 函数段开始，把布尔值转换成验收 token 需要的小写 true/false；如果没有这个函数，CLI 输出容易出现 True/False 漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase70GenericControlActions: 返回稳定小写布尔字符串；如果没有这行代码，真实终端场景 token 无法稳定匹配。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出 token 转换范围。


def _phase70_safe_text(value: Any, limit: int = 220) -> str:  # 新增代码+Phase70GenericControlActions: 函数段开始，把任意文本压成安全单行；如果没有这个函数，日志和指纹可能被换行打乱。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase70GenericControlActions: 清理换行和首尾空白；如果没有这行代码，用户输入可能破坏终端 token 格式。
    return text[: max(0, int(limit))]  # 新增代码+Phase70GenericControlActions: 限制最大长度；如果没有这行代码，异常或长 query 可能刷爆终端。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清理范围。


def _phase70_sha256_16(value: Any) -> str:  # 新增代码+Phase70GenericControlActions: 函数段开始，生成 16 位短哈希；如果没有这个函数，证据只能保存原始文本或无法稳定比对。
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase70GenericControlActions: 稳定序列化任意 JSON 风格值；如果没有这行代码，同一证据在不同运行中可能顺序不同。
    return hashlib.sha256(serialized.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase70GenericControlActions: 返回 SHA256 前 16 位；如果没有这行代码，短指纹没有实际内容来源。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出哈希范围。


def _phase70_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase70GenericControlActions: 函数段开始，把坐标安全转换成整数；如果没有这个函数，坏视觉点或 bounds 会让动作构造崩溃。
    try:  # 新增代码+Phase70GenericControlActions: 捕获无法转换的动态值；如果没有这行代码，None 或字符串坐标会直接抛异常。
        return int(value)  # 新增代码+Phase70GenericControlActions: 返回整数；如果没有这行代码，高层工具拿不到标准坐标。
    except Exception:  # 新增代码+Phase70GenericControlActions: 兜底处理任意转换异常；如果没有这行代码，模型坏参数会中断 agent。
        return int(default)  # 新增代码+Phase70GenericControlActions: 返回默认整数；如果没有这行代码，调用方需要到处重复兜底。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出整数转换范围。


def _phase70_controls_from_observation(observation: Any) -> list[dict[str, Any]]:  # 新增代码+Phase70GenericControlActions: 函数段开始，从融合观察中提取 UIA 控件列表；如果没有这个函数，click/type 无法复用 Phase57 locator。
    controls: list[dict[str, Any]] = []  # 新增代码+Phase70GenericControlActions: 初始化控件列表；如果没有这行代码，后续无法累积多个来源的候选。
    if not isinstance(observation, dict):  # 新增代码+Phase70GenericControlActions: 检查观察是否为字典；如果没有这行代码，坏输入会在 get 调用时报错。
        return controls  # 新增代码+Phase70GenericControlActions: 非法观察返回空控件；如果没有这行代码，调用方无法安全得到零候选。
    for key in ("flat_nodes", "uia_controls", "controls"):  # 新增代码+Phase70GenericControlActions: 兼容 Phase57、融合观察和测试样本的控件字段；如果没有这行代码，不同观察格式不能共用。
        raw_items = observation.get(key, [])  # 新增代码+Phase70GenericControlActions: 读取当前候选字段；如果没有这行代码，循环不知道要处理哪个列表。
        if isinstance(raw_items, list):  # 新增代码+Phase70GenericControlActions: 只处理列表字段；如果没有这行代码，字符串等坏字段可能被逐字符遍历。
            for item in raw_items:  # 新增代码+Phase70GenericControlActions: 遍历候选控件；如果没有这行代码，无法复制单个控件。
                if isinstance(item, dict):  # 新增代码+Phase70GenericControlActions: 只接受字典控件；如果没有这行代码，坏候选会污染 locator。
                    controls.append(dict(item))  # 新增代码+Phase70GenericControlActions: 复制控件避免污染观察对象；如果没有这行代码，后续修改可能影响原始观察。
    nested_uia = observation.get("uia")  # 修改代码+Phase70GenericControlActions: 只在真实存在 uia 字段时读取嵌套观察；如果没有这行代码，缺省空字典会导致无限递归。
    if isinstance(nested_uia, dict) and nested_uia is not observation:  # 修改代码+Phase70GenericControlActions: 确认嵌套 UIA 是独立字典；如果没有这行代码，自引用观察会导致递归爆栈。
        for item in _phase70_controls_from_observation(nested_uia):  # 新增代码+Phase70GenericControlActions: 递归提取嵌套控件；如果没有这行代码，Phase66 风格嵌套观察不能使用。
            controls.append(item)  # 新增代码+Phase70GenericControlActions: 合并嵌套控件；如果没有这行代码，locator 候选会不完整。
    return controls  # 新增代码+Phase70GenericControlActions: 返回提取到的控件列表；如果没有这行代码，调用方拿不到定位输入。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_controls_from_observation 到此结束；如果没有这个边界说明，初学者不容易看出控件提取范围。


def _phase70_query_to_locator(query: Any, preferred_role: str | None = None) -> dict[str, Any]:  # 新增代码+Phase70GenericControlActions: 函数段开始，把自然语言 query 转为 Phase57 locator 查询；如果没有这个函数，调用方要手写 locator 字段。
    if isinstance(query, dict):  # 新增代码+Phase70GenericControlActions: 支持上层直接传结构化 locator；如果没有这行代码，精确 automation_id 查询无法复用。
        locator_query = dict(query)  # 新增代码+Phase70GenericControlActions: 复制结构化查询避免污染调用方对象；如果没有这行代码，补 role 时可能改到外部状态。
    else:  # 新增代码+Phase70GenericControlActions: 处理普通自然语言文本；如果没有这行代码，字符串 query 无法变成 locator。
        locator_query = {"text": _phase70_safe_text(query, 160)}  # 新增代码+Phase70GenericControlActions: 把文本作为可见文字查询；如果没有这行代码，Phase57 locator 不知道要找什么。
    if preferred_role and "role" not in locator_query:  # 新增代码+Phase70GenericControlActions: 在需要输入框时补充角色偏好；如果没有这行代码，type 可能匹配到同名按钮或标签。
        locator_query["role"] = preferred_role  # 新增代码+Phase70GenericControlActions: 写入角色偏好；如果没有这行代码，定位置信度和目标准确性会下降。
    return locator_query  # 新增代码+Phase70GenericControlActions: 返回 Phase57 可用查询；如果没有这行代码，调用方拿不到 locator 参数。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_query_to_locator 到此结束；如果没有这个边界说明，初学者不容易看出 query 转换范围。


def _phase70_point(point: Any) -> dict[str, int]:  # 新增代码+Phase70GenericControlActions: 函数段开始，把视觉点规范成 x/y 整数；如果没有这个函数，画布点击坐标可能格式混乱。
    raw_point = point if isinstance(point, dict) else {}  # 新增代码+Phase70GenericControlActions: 只接受字典点位；如果没有这行代码，列表或字符串坐标会造成难懂异常。
    return {"x": _phase70_safe_int(raw_point.get("x", 0)), "y": _phase70_safe_int(raw_point.get("y", 0))}  # 新增代码+Phase70GenericControlActions: 返回标准点位；如果没有这行代码，高层工具无法计算视觉落点。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_point 到此结束；如果没有这个边界说明，初学者不容易看出视觉点规范范围。


def _phase70_visual_control(point: dict[str, int], reason: str) -> dict[str, Any]:  # 新增代码+Phase70GenericControlActions: 函数段开始，把视觉点包装成合成控件；如果没有这个函数，视觉兜底无法复用 Phase62 click_control。
    x = int(point.get("x", 0))  # 新增代码+Phase70GenericControlActions: 读取视觉点 x 坐标；如果没有这行代码，合成 bounds 缺少横向中心。
    y = int(point.get("y", 0))  # 新增代码+Phase70GenericControlActions: 读取视觉点 y 坐标；如果没有这行代码，合成 bounds 缺少纵向中心。
    return {"node_id": "phase70.visual.0", "name": _phase70_safe_text(reason or "visual point", 120), "role": "VisualPoint", "automation_id": PHASE70_VISUAL_POINT_AUTOMATION_ID, "class_name": "Phase70VisualFallback", "bounds": {"left": x - 1, "top": y - 1, "right": x + 1, "bottom": y + 1, "width": 2, "height": 2}, "enabled": True, "clickable": True, "editable": False}  # 新增代码+Phase70GenericControlActions: 返回中心就是视觉点的合成控件；如果没有这行代码，高层点击无法使用视觉兜底坐标。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_visual_control 到此结束；如果没有这个边界说明，初学者不容易看出视觉控件构造范围。


def _phase70_control_center(control: dict[str, Any]) -> dict[str, int]:  # 新增代码+Phase70GenericControlActions: 函数段开始，从控件 bounds 计算中心点；如果没有这个函数，记录型高层工具无法展示目标点。
    bounds = dict(control.get("bounds", {}) or {})  # 新增代码+Phase70GenericControlActions: 读取控件边界并复制；如果没有这行代码，坏控件对象可能污染后续逻辑。
    left = _phase70_safe_int(bounds.get("left"))  # 新增代码+Phase70GenericControlActions: 读取左边界；如果没有这行代码，中心点缺少 x 起点。
    top = _phase70_safe_int(bounds.get("top"))  # 新增代码+Phase70GenericControlActions: 读取上边界；如果没有这行代码，中心点缺少 y 起点。
    right = _phase70_safe_int(bounds.get("right"), left + _phase70_safe_int(bounds.get("width"), 1))  # 新增代码+Phase70GenericControlActions: 读取右边界并用 width 兜底；如果没有这行代码，只有 width 的控件无法点击。
    bottom = _phase70_safe_int(bounds.get("bottom"), top + _phase70_safe_int(bounds.get("height"), 1))  # 新增代码+Phase70GenericControlActions: 读取下边界并用 height 兜底；如果没有这行代码，只有 height 的控件无法点击。
    return {"x": left + max(1, right - left) // 2, "y": top + max(1, bottom - top) // 2}  # 新增代码+Phase70GenericControlActions: 返回控件中心点；如果没有这行代码，记录事件缺少目标坐标。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_control_center 到此结束；如果没有这个边界说明，初学者不容易看出中心点计算范围。


def _phase70_text_summary(text: Any) -> dict[str, Any]:  # 新增代码+Phase70GenericControlActions: 函数段开始，生成输入文本脱敏摘要；如果没有这个函数，输入内容可能进入日志或验收报告。
    safe_text = str(text or "")  # 新增代码+Phase70GenericControlActions: 把输入规范成字符串；如果没有这行代码，None 或数字输入无法稳定统计。
    return {"length": len(safe_text), "sha256_16": _phase70_sha256_16({"text": safe_text}), "raw_text_included": False}  # 新增代码+Phase70GenericControlActions: 返回长度和短哈希但不返回原文；如果没有这行代码，敏感输入缺少可审计但安全的摘要。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_text_summary 到此结束；如果没有这个边界说明，初学者不容易看出文本脱敏范围。


def _phase70_fingerprint(window: dict[str, Any], observation: dict[str, Any] | None, label: str, extra: Any | None = None) -> str:  # 新增代码+Phase70GenericControlActions: 函数段开始，构造动作前后证据指纹；如果没有这个函数，闭环执行器无法比较动作影响。
    safe_observation = observation if isinstance(observation, dict) else {}  # 新增代码+Phase70GenericControlActions: 只接受字典观察；如果没有这行代码，坏观察会让指纹生成异常。
    payload = {"label": _phase70_safe_text(label, 80), "window_id": _phase70_safe_text(window.get("window_id", ""), 120), "app_id": _phase70_safe_text(window.get("app_id", ""), 120), "input_fingerprint": _phase70_safe_text(safe_observation.get("fingerprint", ""), 120), "control_count": len(_phase70_controls_from_observation(safe_observation)), "extra_hash": _phase70_sha256_16(extra or {})}  # 新增代码+Phase70GenericControlActions: 汇总脱敏状态字段；如果没有这行代码，前后证据没有统一输入。
    return f"phase70:{_phase70_sha256_16(payload)}"  # 新增代码+Phase70GenericControlActions: 返回稳定短指纹；如果没有这行代码，报告无法比较前后状态。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_fingerprint 到此结束；如果没有这个边界说明，初学者不容易看出指纹范围。


def _phase70_redact_payload(value: Any) -> Any:  # 新增代码+Phase70GenericControlActions: 函数段开始，递归脱敏高层工具结果；如果没有这个函数，type 参数可能泄露到 Phase70 报告。
    if isinstance(value, dict):  # 新增代码+Phase70GenericControlActions: 优先处理字典结构；如果没有这行代码，常见 JSON 结果无法递归脱敏。
        redacted: dict[str, Any] = {}  # 新增代码+Phase70GenericControlActions: 创建脱敏字典；如果没有这行代码，无法逐项保存安全字段。
        for key, item in value.items():  # 新增代码+Phase70GenericControlActions: 遍历原始字典字段；如果没有这行代码，无法检查敏感键。
            lowered = str(key).lower()  # 新增代码+Phase70GenericControlActions: 把键名转小写；如果没有这行代码，Text/TEXT 等大小写差异会漏过。
            if lowered in {"text", "password", "secret", "input"}:  # 新增代码+Phase70GenericControlActions: 判断是否为敏感文本键；如果没有这行代码，输入原文可能进入报告。
                redacted[str(key)] = {"redacted": True, "summary": _phase70_text_summary(item)}  # 新增代码+Phase70GenericControlActions: 用摘要替代敏感原文；如果没有这行代码，审计既不安全也不可比对。
            else:  # 新增代码+Phase70GenericControlActions: 处理非敏感字段；如果没有这行代码，普通字段会被误删。
                redacted[str(key)] = _phase70_redact_payload(item)  # 新增代码+Phase70GenericControlActions: 递归脱敏子结构；如果没有这行代码，嵌套结果可能漏敏。
        return redacted  # 新增代码+Phase70GenericControlActions: 返回脱敏字典；如果没有这行代码，调用方拿不到安全结果。
    if isinstance(value, list):  # 新增代码+Phase70GenericControlActions: 处理列表结构；如果没有这行代码，事件列表里的敏感字段无法递归处理。
        return [_phase70_redact_payload(item) for item in value]  # 新增代码+Phase70GenericControlActions: 返回逐项脱敏列表；如果没有这行代码，列表结果会原样泄露。
    return value  # 新增代码+Phase70GenericControlActions: 原样返回非容器值；如果没有这行代码，数字和布尔值会丢失。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_redact_payload 到此结束；如果没有这个边界说明，初学者不容易看出脱敏范围。


class Phase70RecordingHighLevelTool:  # 新增代码+Phase70GenericControlActions: 类段开始，提供记录型高层工具适配器；如果没有这个类，合同测试可能触碰真实鼠标键盘。
    def __init__(self) -> None:  # 新增代码+Phase70GenericControlActions: 函数段开始，初始化动作记录；如果没有这个函数，测试无法统计委托事件。
        self.events: list[dict[str, Any]] = []  # 新增代码+Phase70GenericControlActions: 保存高层工具调用记录；如果没有这行代码，无法证明 Phase70 没有绕过高层工具。
    # 新增代码+Phase70GenericControlActions: 函数段结束，Phase70RecordingHighLevelTool.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def run(self, operation: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase70GenericControlActions: 函数段开始，模拟 Phase62 runtime.run 接口；如果没有这个函数，Phase70 无法在合同里安全委托高层动作。
        args = dict(arguments or {})  # 新增代码+Phase70GenericControlActions: 复制参数避免污染调用方对象；如果没有这行代码，记录过程可能修改原参数。
        controls = [dict(item) for item in list(args.get("controls", []) or []) if isinstance(item, dict)]  # 新增代码+Phase70GenericControlActions: 复制控件候选；如果没有这行代码，记录事件无法展示目标摘要。
        control = controls[0] if controls else {}  # 新增代码+Phase70GenericControlActions: 选择第一个候选作为记录目标；如果没有这行代码，记录结果缺少目标控件。
        target = {"query": dict(args.get("query", {}) or {}), "control": control, "center": _phase70_control_center(control) if control else {}, "point": dict(args.get("visual_point", {}) or {}), "reason": _phase70_safe_text(args.get("visual_reason", ""), 160)}  # 新增代码+Phase70GenericControlActions: 构造脱敏目标摘要；如果没有这行代码，测试和审计不知道动作委托到哪里。
        event = {"operation": _phase70_safe_text(operation, 120), "target": target, "text_summary": _phase70_text_summary(args.get("text", "")) if operation == "type_into_control" else {}, "direct_low_level_bypass": False}  # 新增代码+Phase70GenericControlActions: 记录高层事件且不暴露输入原文；如果没有这行代码，委托链路缺少证据。
        self.events.append(event)  # 新增代码+Phase70GenericControlActions: 保存事件；如果没有这行代码，测试无法证明动作被调用。
        return {"ok": operation in {"click_control", "type_into_control"}, "operation": operation, "high_level_event_count": 1, "low_level_event_count": 0, "low_level_events_sent": False, "target": target, "text_summary": event["text_summary"], "tool": "phase70_recording_high_level_tool", "direct_low_level_bypass": False, "actions_expanded": PHASE70_ACTIONS_EXPANDED}  # 新增代码+Phase70GenericControlActions: 返回记录型高层工具结果；如果没有这行代码，Phase70 runtime 拿不到委托摘要。
    # 新增代码+Phase70GenericControlActions: 函数段结束，Phase70RecordingHighLevelTool.run 到此结束；如果没有这个边界说明，初学者不容易看出记录运行范围。
# 新增代码+Phase70GenericControlActions: 类段结束，Phase70RecordingHighLevelTool 到此结束；如果没有这个边界说明，初学者不容易看出记录型工具范围。


class WindowsGenericControlActionRuntime:  # 新增代码+Phase70GenericControlActions: 类段开始，提供通用 query 点击、query 输入和视觉点点击 runtime；如果没有这个类，Phase68 闭环执行器不能把用户意图落到控件动作。
    def __init__(self, high_level_tool: Any | None = None, locator: SemanticControlLocator | None = None) -> None:  # 新增代码+Phase70GenericControlActions: 函数段开始，注入高层工具和 Phase57 locator；如果没有这个函数，测试和生产无法替换执行后端。
        self.high_level_tool = high_level_tool if high_level_tool is not None else Phase70RecordingHighLevelTool()  # 新增代码+Phase70GenericControlActions: 默认使用记录型工具；如果没有这行代码，默认构造可能触碰真实桌面。
        self.locator = locator if locator is not None else SemanticControlLocator()  # 新增代码+Phase70GenericControlActions: 默认复用 Phase57 语义定位器；如果没有这行代码，query 动作无法找控件。
    # 新增代码+Phase70GenericControlActions: 函数段结束，WindowsGenericControlActionRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _run_high_level(self, operation: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase70GenericControlActions: 函数段开始，调用可注入的高层工具接口；如果没有这个函数，Phase70 会和具体工具实现强耦合。
        run_method = getattr(self.high_level_tool, "run", None)  # 新增代码+Phase70GenericControlActions: 读取 runtime.run 方法；如果没有这行代码，Phase62 风格工具无法被调用。
        if not callable(run_method):  # 新增代码+Phase70GenericControlActions: 检查高层工具接口是否存在；如果没有这行代码，错误适配器会产生难懂异常。
            return {"ok": False, "decision": "high_level_tool_missing_run", "high_level_event_count": 0, "low_level_event_count": 0, "direct_low_level_bypass": False, "actions_expanded": PHASE70_ACTIONS_EXPANDED}  # 新增代码+Phase70GenericControlActions: 返回零事件接口失败；如果没有这行代码，Phase70 可能误报动作已执行。
        result = run_method(operation, arguments)  # 新增代码+Phase70GenericControlActions: 调用高层工具；如果没有这行代码，点击和输入不会真正委托给 Phase62 风格接口。
        return dict(result or {}) if isinstance(result, dict) else {"ok": bool(result), "high_level_event_count": 1, "direct_low_level_bypass": False, "actions_expanded": PHASE70_ACTIONS_EXPANDED}  # 新增代码+Phase70GenericControlActions: 规范化高层工具返回；如果没有这行代码，非字典返回会让后续字段访问失败。
    # 新增代码+Phase70GenericControlActions: 函数段结束，WindowsGenericControlActionRuntime._run_high_level 到此结束；如果没有这个边界说明，初学者不容易看出高层委托范围。

    def _locate_control(self, observation: dict[str, Any], query: Any, preferred_role: str | None = None) -> dict[str, Any]:  # 新增代码+Phase70GenericControlActions: 函数段开始，使用 Phase57 locator 查找控件；如果没有这个函数，click/type 会重复定位逻辑。
        controls = _phase70_controls_from_observation(observation)  # 新增代码+Phase70GenericControlActions: 提取观察里的控件候选；如果没有这行代码，locator 没有输入。
        locator_query = _phase70_query_to_locator(query, preferred_role=preferred_role)  # 新增代码+Phase70GenericControlActions: 转换自然语言 query；如果没有这行代码，Phase57 不知道查询条件。
        located = self.locator.find(controls, locator_query)  # 新增代码+Phase70GenericControlActions: 调用 Phase57 语义控件定位器；如果没有这行代码，query 动作只能靠猜测。
        return {"controls": controls, "query": locator_query, "located": located, "control": dict(located.get("control", {}) or {})}  # 新增代码+Phase70GenericControlActions: 返回定位上下文；如果没有这行代码，动作构造拿不到控件和 query。
    # 新增代码+Phase70GenericControlActions: 函数段结束，WindowsGenericControlActionRuntime._locate_control 到此结束；如果没有这个边界说明，初学者不容易看出控件定位范围。

    def _refusal(self, window: dict[str, Any], observation: dict[str, Any], operation: str, decision: str, locator_result: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase70GenericControlActions: 函数段开始，构造零事件拒绝结果；如果没有这个函数，不同失败路径字段会漂移。
        before = _phase70_fingerprint(window, observation, "before-refusal", extra=operation)  # 新增代码+Phase70GenericControlActions: 生成拒绝前指纹；如果没有这行代码，拒绝报告缺少状态证据。
        return {"ok": False, "refused": True, "decision": decision, "operation": operation, "used_control_locator": bool(locator_result), "used_high_level_tool": False, "visual_fallback": False, "before_fingerprint": before, "after_fingerprint": before, "before_after_evidence": False, "zero_event_refusal": True, "high_level_event_count": 0, "low_level_event_count": 0, "low_level_events_sent": False, "locator": _phase70_redact_payload(locator_result or {}), "marker": PHASE70_GENERIC_CONTROL_ACTIONS_MARKER, "model": PHASE70_GENERIC_CONTROL_ACTIONS_MODEL, "actions_expanded": PHASE70_ACTIONS_EXPANDED}  # 新增代码+Phase70GenericControlActions: 返回零事件拒绝摘要；如果没有这行代码，找不到控件时可能继续执行默认动作。
    # 新增代码+Phase70GenericControlActions: 函数段结束，WindowsGenericControlActionRuntime._refusal 到此结束；如果没有这个边界说明，初学者不容易看出拒绝结构范围。

    def _phase114_gate_report(self, session_id: Any = "", window_identity: dict[str, Any] | None = None, target_identity_verification: dict[str, Any] | None = None, after_target_identity_verification: dict[str, Any] | None = None, require_verified_identity: bool = False, abort_requested: bool = False) -> dict[str, Any]:  # 新增代码+VerifiedWindowActionsMaturity: 函数段开始，为 Phase70 动作生成统一身份门禁报告；如果没有这个函数，每个动作方法都要重复传参并容易漏字段。
        return phase114_verified_action_gate(session_id=session_id, window_identity=window_identity, target_identity_verification=target_identity_verification, after_target_identity_verification=after_target_identity_verification, require_verified_identity=require_verified_identity, abort_requested=abort_requested)  # 新增代码+VerifiedWindowActionsMaturity: 调用闭环层统一门禁函数；如果没有这行代码，Phase70 会和 Phase114 门禁规则漂移。
    # 新增代码+VerifiedWindowActionsMaturity: 函数段结束，WindowsGenericControlActionRuntime._phase114_gate_report 到此结束；如果没有这个边界说明，初学者不容易看出身份门禁报告范围。

    def _phase114_blocked_refusal(self, window: dict[str, Any], observation: dict[str, Any], operation: str, identity_gate: dict[str, Any]) -> dict[str, Any]:  # 新增代码+VerifiedWindowActionsMaturity: 函数段开始，把身份门禁阻断转换为 Phase70 零事件拒绝；如果没有这个函数，阻断结果和普通拒绝字段会不一致。
        result = self._refusal(window, observation, operation, str(identity_gate.get("decision", "missing_verified_target_identity")))  # 新增代码+VerifiedWindowActionsMaturity: 复用现有零事件拒绝结构；如果没有这行代码，身份拒绝可能缺少前后指纹和零事件字段。
        result.update(identity_gate)  # 新增代码+VerifiedWindowActionsMaturity: 合并 before_identity/after_identity/same_target 等成熟字段；如果没有这行代码，测试和矩阵看不到身份门禁证据。
        return result  # 新增代码+VerifiedWindowActionsMaturity: 返回完整身份阻断结果；如果没有这行代码，调用方拿不到拒绝报告。
    # 新增代码+VerifiedWindowActionsMaturity: 函数段结束，WindowsGenericControlActionRuntime._phase114_blocked_refusal 到此结束；如果没有这个边界说明，初学者不容易看出身份拒绝范围。

    def click_by_query(self, window: dict[str, Any], observation: dict[str, Any], query: Any, session_id: Any = "", window_identity: dict[str, Any] | None = None, target_identity_verification: dict[str, Any] | None = None, after_target_identity_verification: dict[str, Any] | None = None, require_verified_identity: bool = False, abort_requested: bool = False) -> dict[str, Any]:  # 修改代码+VerifiedWindowActionsMaturity: 函数段开始，按 query 点击前先接收已验证窗口身份；如果没有这些参数，点击无法证明只落在 agent 自有窗口。
        identity_gate = self._phase114_gate_report(session_id=session_id, window_identity=window_identity, target_identity_verification=target_identity_verification, after_target_identity_verification=after_target_identity_verification, require_verified_identity=require_verified_identity, abort_requested=abort_requested)  # 新增代码+VerifiedWindowActionsMaturity: 生成点击前身份门禁报告；如果没有这行代码，缺身份或漂移窗口不会被前置阻断。
        if bool(identity_gate.get("blocked")):  # 新增代码+VerifiedWindowActionsMaturity: 身份门禁要求阻断时不再定位和委托动作；如果没有这行代码，阻断只会停留在报告里。
            return self._phase114_blocked_refusal(window, observation, "click_by_query", identity_gate)  # 新增代码+VerifiedWindowActionsMaturity: 返回零事件身份拒绝；如果没有这行代码，缺身份点击可能继续向下执行。
        located_context = self._locate_control(observation, query)  # 修改代码+VerifiedWindowActionsMaturity: 身份门禁放行后才用 Phase57 locator 查找控件；如果没有这行代码，点击可能落到错误目标。
        located = dict(located_context.get("located", {}) or {})  # 新增代码+Phase70GenericControlActions: 取出定位结果；如果没有这行代码，后续判断无法读取 matched。
        if not bool(located.get("matched")):  # 新增代码+Phase70GenericControlActions: 检查是否找到控件；如果没有这行代码，未命中时仍可能点击默认坐标。
            result = self._refusal(window, observation, "click_by_query", "control_not_found", located_context)  # 修改代码+VerifiedWindowActionsMaturity: 构造零事件控件未命中拒绝；如果没有这行代码，找不到控件会产生真实副作用风险。
            result.update(identity_gate)  # 新增代码+VerifiedWindowActionsMaturity: 把已放行的身份上下文也写入未命中报告；如果没有这行代码，拒绝路径缺少 before_identity/after_identity。
            return result  # 新增代码+VerifiedWindowActionsMaturity: 返回带身份字段的控件未命中拒绝；如果没有这行代码，调用方拿不到审计完整的拒绝结果。
        arguments = {"window": dict(window), "controls": [dict(located_context.get("control", {}) or {})], "query": dict(located_context.get("query", {}) or {}), "button": "left"}  # 新增代码+Phase70GenericControlActions: 构造 Phase62 click_control 参数；如果没有这行代码，高层工具拿不到窗口、控件和查询。
        before = _phase70_fingerprint(window, observation, "before-click", extra=arguments)  # 新增代码+Phase70GenericControlActions: 生成点击前指纹；如果没有这行代码，动作没有前态证据。
        high_level = self._run_high_level("click_control", arguments)  # 新增代码+Phase70GenericControlActions: 委托高层工具执行点击；如果没有这行代码，Phase70 会绕过 Phase62 风格安全链。
        after = _phase70_fingerprint(window, observation, "after-click", extra=high_level)  # 新增代码+Phase70GenericControlActions: 生成点击后指纹；如果没有这行代码，动作没有后态证据。
        result = {"ok": bool(high_level.get("ok")), "operation": "click_by_query", "generic_click": bool(high_level.get("ok")), "generic_type": False, "used_control_locator": True, "control_locator": True, "visual_fallback": False, "used_high_level_tool": True, "before_fingerprint": before, "after_fingerprint": after, "before_after_evidence": before != after, "zero_event_refusal": False, "high_level_event_count": int(high_level.get("high_level_event_count", 1) or 0), "low_level_event_count": int(high_level.get("low_level_event_count", 0) or 0), "locator": _phase70_redact_payload(located), "high_level_result": _phase70_redact_payload(high_level), "marker": PHASE70_GENERIC_CONTROL_ACTIONS_MARKER, "model": PHASE70_GENERIC_CONTROL_ACTIONS_MODEL, "actions_expanded": PHASE70_ACTIONS_EXPANDED}  # 修改代码+VerifiedWindowActionsMaturity: 构造通用点击报告准备合并身份字段；如果没有这行代码，闭环执行器拿不到统一结果。
        result.update(identity_gate)  # 新增代码+VerifiedWindowActionsMaturity: 把 before_identity/after_identity/same_target 写入点击报告；如果没有这行代码，点击审计看不到目标身份证据。
        return result  # 新增代码+VerifiedWindowActionsMaturity: 返回带身份门禁字段的点击报告；如果没有这行代码，调用方拿不到成熟动作结果。
    # 新增代码+Phase70GenericControlActions: 函数段结束，WindowsGenericControlActionRuntime.click_by_query 到此结束；如果没有这个边界说明，初学者不容易看出 query 点击范围。

    def type_by_query(self, window: dict[str, Any], observation: dict[str, Any], query: Any, text: str, session_id: Any = "", window_identity: dict[str, Any] | None = None, target_identity_verification: dict[str, Any] | None = None, after_target_identity_verification: dict[str, Any] | None = None, require_verified_identity: bool = False, abort_requested: bool = False) -> dict[str, Any]:  # 修改代码+VerifiedWindowActionsMaturity: 函数段开始，按 query 输入前先接收已验证窗口身份；如果没有这些参数，文本可能被输入到漂移窗口。
        identity_gate = self._phase114_gate_report(session_id=session_id, window_identity=window_identity, target_identity_verification=target_identity_verification, after_target_identity_verification=after_target_identity_verification, require_verified_identity=require_verified_identity, abort_requested=abort_requested)  # 新增代码+VerifiedWindowActionsMaturity: 生成输入前身份门禁报告；如果没有这行代码，缺身份或漂移窗口不会被前置阻断。
        if bool(identity_gate.get("blocked")):  # 新增代码+VerifiedWindowActionsMaturity: 身份门禁要求阻断时不再定位和输入；如果没有这行代码，阻断只会停留在报告里。
            return self._phase114_blocked_refusal(window, observation, "type_by_query", identity_gate)  # 新增代码+VerifiedWindowActionsMaturity: 返回零事件身份拒绝；如果没有这行代码，缺身份输入可能继续向下执行。
        located_context = self._locate_control(observation, query, preferred_role="Edit")  # 修改代码+VerifiedWindowActionsMaturity: 身份门禁放行后才用 Phase57 locator 查找输入控件；如果没有这行代码，文本可能输入到按钮或标签。
        located = dict(located_context.get("located", {}) or {})  # 新增代码+Phase70GenericControlActions: 取出定位结果；如果没有这行代码，后续判断无法读取 matched。
        if not bool(located.get("matched")):  # 新增代码+Phase70GenericControlActions: 检查是否找到输入控件；如果没有这行代码，未命中时仍可能输入到当前焦点。
            result = self._refusal(window, observation, "type_by_query", "control_not_found", located_context)  # 修改代码+VerifiedWindowActionsMaturity: 构造零事件输入控件未命中拒绝；如果没有这行代码，找不到输入框会产生真实副作用风险。
            result.update(identity_gate)  # 新增代码+VerifiedWindowActionsMaturity: 把已放行的身份上下文也写入未命中报告；如果没有这行代码，拒绝路径缺少 before_identity/after_identity。
            return result  # 新增代码+VerifiedWindowActionsMaturity: 返回带身份字段的输入控件未命中拒绝；如果没有这行代码，调用方拿不到审计完整的拒绝结果。
        arguments = {"window": dict(window), "controls": [dict(located_context.get("control", {}) or {})], "query": dict(located_context.get("query", {}) or {}), "text": str(text or "")}  # 新增代码+Phase70GenericControlActions: 构造 Phase62 type_into_control 参数；如果没有这行代码，高层工具没有文本和目标控件。
        text_summary = _phase70_text_summary(text)  # 新增代码+Phase70GenericControlActions: 生成输入文本脱敏摘要；如果没有这行代码，报告可能暴露原文或缺少可比对证据。
        before = _phase70_fingerprint(window, observation, "before-type", extra={"query": arguments["query"], "text_summary": text_summary})  # 新增代码+Phase70GenericControlActions: 生成输入前指纹；如果没有这行代码，输入动作没有前态证据。
        high_level = self._run_high_level("type_into_control", arguments)  # 新增代码+Phase70GenericControlActions: 委托高层工具执行输入；如果没有这行代码，Phase70 会绕过授权、锁和急停链。
        after = _phase70_fingerprint(window, observation, "after-type", extra={"high_level": _phase70_redact_payload(high_level), "text_summary": text_summary})  # 新增代码+Phase70GenericControlActions: 生成输入后指纹；如果没有这行代码，输入动作没有后态证据。
        result = {"ok": bool(high_level.get("ok")), "operation": "type_by_query", "generic_click": False, "generic_type": bool(high_level.get("ok")), "used_control_locator": True, "control_locator": True, "visual_fallback": False, "used_high_level_tool": True, "before_fingerprint": before, "after_fingerprint": after, "before_after_evidence": before != after, "zero_event_refusal": False, "high_level_event_count": int(high_level.get("high_level_event_count", 1) or 0), "low_level_event_count": int(high_level.get("low_level_event_count", 0) or 0), "text_summary": text_summary, "locator": _phase70_redact_payload(located), "high_level_result": _phase70_redact_payload(high_level), "marker": PHASE70_GENERIC_CONTROL_ACTIONS_MARKER, "model": PHASE70_GENERIC_CONTROL_ACTIONS_MODEL, "actions_expanded": PHASE70_ACTIONS_EXPANDED}  # 修改代码+VerifiedWindowActionsMaturity: 构造通用输入报告准备合并身份字段；如果没有这行代码，闭环执行器拿不到统一输入结果。
        result.update(identity_gate)  # 新增代码+VerifiedWindowActionsMaturity: 把 before_identity/after_identity/same_target 写入输入报告；如果没有这行代码，输入审计看不到目标身份证据。
        return result  # 新增代码+VerifiedWindowActionsMaturity: 返回带身份门禁字段的输入报告；如果没有这行代码，调用方拿不到成熟动作结果。
    # 新增代码+Phase70GenericControlActions: 函数段结束，WindowsGenericControlActionRuntime.type_by_query 到此结束；如果没有这个边界说明，初学者不容易看出 query 输入范围。

    def click_by_visual_point(self, window: dict[str, Any], point: dict[str, Any], reason: str, session_id: Any = "", window_identity: dict[str, Any] | None = None, target_identity_verification: dict[str, Any] | None = None, after_target_identity_verification: dict[str, Any] | None = None, require_verified_identity: bool = False, abort_requested: bool = False) -> dict[str, Any]:  # 修改代码+VerifiedWindowActionsMaturity: 函数段开始，按视觉点点击前先接收已验证窗口身份；如果没有这些参数，画布兜底点击可能落到漂移窗口。
        safe_point = _phase70_point(point)  # 新增代码+Phase70GenericControlActions: 规范化视觉点坐标；如果没有这行代码，坏坐标可能进入高层工具。
        visual_control = _phase70_visual_control(safe_point, reason)  # 新增代码+Phase70GenericControlActions: 把视觉点包装成合成控件；如果没有这行代码，Phase62 click_control 无法复用视觉点。
        observation = {"fingerprint": "phase70-visual-before", "flat_nodes": [visual_control]}  # 新增代码+Phase70GenericControlActions: 构造最小观察证据；如果没有这行代码，前后指纹和高层控件参数缺少输入。
        identity_gate = self._phase114_gate_report(session_id=session_id, window_identity=window_identity, target_identity_verification=target_identity_verification, after_target_identity_verification=after_target_identity_verification, require_verified_identity=require_verified_identity, abort_requested=abort_requested)  # 新增代码+VerifiedWindowActionsMaturity: 生成视觉点击前身份门禁报告；如果没有这行代码，缺身份或漂移窗口不会被前置阻断。
        if bool(identity_gate.get("blocked")):  # 新增代码+VerifiedWindowActionsMaturity: 身份门禁要求阻断时不再委托视觉点击；如果没有这行代码，阻断只会停留在报告里。
            return self._phase114_blocked_refusal(window, observation, "click_by_visual_point", identity_gate)  # 新增代码+VerifiedWindowActionsMaturity: 返回零事件身份拒绝；如果没有这行代码，缺身份视觉点击可能继续向下执行。
        arguments = {"window": dict(window), "controls": [visual_control], "query": {"automation_id": PHASE70_VISUAL_POINT_AUTOMATION_ID}, "button": "left", "visual_point": safe_point, "visual_reason": _phase70_safe_text(reason, 160)}  # 新增代码+Phase70GenericControlActions: 构造高层点击参数；如果没有这行代码，视觉点无法委托给高层工具。
        before = _phase70_fingerprint(window, observation, "before-visual-click", extra=arguments)  # 新增代码+Phase70GenericControlActions: 生成视觉点击前指纹；如果没有这行代码，视觉动作没有前态证据。
        high_level = self._run_high_level("click_control", arguments)  # 新增代码+Phase70GenericControlActions: 委托高层工具执行视觉点击；如果没有这行代码，视觉兜底会绕过安全接口。
        after = _phase70_fingerprint(window, observation, "after-visual-click", extra=high_level)  # 新增代码+Phase70GenericControlActions: 生成视觉点击后指纹；如果没有这行代码，视觉动作没有后态证据。
        result = {"ok": bool(high_level.get("ok")), "operation": "click_by_visual_point", "generic_click": bool(high_level.get("ok")), "generic_type": False, "used_control_locator": False, "control_locator": False, "visual_fallback": True, "used_high_level_tool": True, "before_fingerprint": before, "after_fingerprint": after, "before_after_evidence": before != after, "zero_event_refusal": False, "high_level_event_count": int(high_level.get("high_level_event_count", 1) or 0), "low_level_event_count": int(high_level.get("low_level_event_count", 0) or 0), "point": safe_point, "reason": _phase70_safe_text(reason, 160), "high_level_result": _phase70_redact_payload(high_level), "marker": PHASE70_GENERIC_CONTROL_ACTIONS_MARKER, "model": PHASE70_GENERIC_CONTROL_ACTIONS_MODEL, "actions_expanded": PHASE70_ACTIONS_EXPANDED}  # 修改代码+VerifiedWindowActionsMaturity: 构造视觉点击报告准备合并身份字段；如果没有这行代码，闭环执行器无法处理画布兜底动作。
        result.update(identity_gate)  # 新增代码+VerifiedWindowActionsMaturity: 把 before_identity/after_identity/same_target 写入视觉点击报告；如果没有这行代码，视觉点击审计看不到目标身份证据。
        return result  # 新增代码+VerifiedWindowActionsMaturity: 返回带身份门禁字段的视觉点击报告；如果没有这行代码，调用方拿不到成熟动作结果。
    # 新增代码+Phase70GenericControlActions: 函数段结束，WindowsGenericControlActionRuntime.click_by_visual_point 到此结束；如果没有这个边界说明，初学者不容易看出视觉点击范围。
# 新增代码+Phase70GenericControlActions: 类段结束，WindowsGenericControlActionRuntime 到此结束；如果没有这个边界说明，初学者不容易看出通用动作 runtime 范围。


def _phase70_contract_window() -> dict[str, Any]:  # 新增代码+Phase70GenericControlActions: 函数段开始，构造合同自检窗口；如果没有这个函数，合同样本会散落在多处。
    return {"app_id": "phase58_safe_app", "process_name": "phase58_safe_app", "window_id": "hwnd:7001", "hwnd": 7001, "title_preview": "LearningAgent-Phase70-GenericControlActions", "safe_to_target": True}  # 新增代码+Phase70GenericControlActions: 返回安全记录型窗口；如果没有这行代码，合同动作没有目标上下文。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_contract_window 到此结束；如果没有这个边界说明，初学者不容易看出合同窗口范围。


def _phase70_contract_observation() -> dict[str, Any]:  # 新增代码+Phase70GenericControlActions: 函数段开始，构造合同自检观察；如果没有这个函数，合同无法稳定验证 query 定位。
    return {"fingerprint": "phase70-before", "flat_nodes": [{"node_id": "0", "name": "Phase70 root", "role": "Window", "automation_id": "Phase70Root", "class_name": "Window", "bounds": {"left": 80, "top": 90, "right": 680, "bottom": 430, "width": 600, "height": 340}, "enabled": True, "clickable": False, "editable": False}, {"node_id": "0.1", "name": "Message box", "role": "Edit", "automation_id": "Phase70MessageBox", "class_name": "TextBox", "bounds": {"left": 110, "top": 130, "right": 430, "bottom": 170, "width": 320, "height": 40}, "enabled": True, "clickable": True, "editable": True}, {"node_id": "0.2", "name": "Send message", "role": "Button", "automation_id": "Phase70SendButton", "class_name": "Button", "bounds": {"left": 450, "top": 130, "right": 580, "bottom": 170, "width": 130, "height": 40}, "enabled": True, "clickable": True, "editable": False}]}  # 新增代码+Phase70GenericControlActions: 返回按钮和输入框候选；如果没有这行代码，合同无法验证点击和输入。
# 新增代码+Phase70GenericControlActions: 函数段结束，_phase70_contract_observation 到此结束；如果没有这个边界说明，初学者不容易看出合同观察范围。


def run_phase70_generic_control_actions_contract() -> dict[str, Any]:  # 新增代码+Phase70GenericControlActions: 函数段开始，运行 Phase70 通用动作合同自检；如果没有这个函数，CLI 和真实终端没有统一验收入口。
    tool = Phase70RecordingHighLevelTool()  # 新增代码+Phase70GenericControlActions: 创建记录型高层工具；如果没有这行代码，合同可能触碰真实桌面。
    runtime = WindowsGenericControlActionRuntime(high_level_tool=tool)  # 新增代码+Phase70GenericControlActions: 创建通用动作 runtime；如果没有这行代码，合同没有被测对象。
    window = _phase70_contract_window()  # 新增代码+Phase70GenericControlActions: 获取合同窗口；如果没有这行代码，动作缺少目标上下文。
    observation = _phase70_contract_observation()  # 新增代码+Phase70GenericControlActions: 获取合同观察；如果没有这行代码，query 定位没有控件输入。
    click = runtime.click_by_query(window, observation, "Send")  # 新增代码+Phase70GenericControlActions: 执行通用点击正例；如果没有这行代码，generic_click token 没证据。
    typed = runtime.type_by_query(window, observation, "Message", "hello phase70")  # 新增代码+Phase70GenericControlActions: 执行通用输入正例；如果没有这行代码，generic_type token 没证据。
    visual = runtime.click_by_visual_point(window, {"x": 260, "y": 220}, "canvas center")  # 新增代码+Phase70GenericControlActions: 执行视觉点兜底正例；如果没有这行代码，visual_fallback token 没证据。
    event_count_before_missing = len(tool.events)  # 新增代码+Phase70GenericControlActions: 记录拒绝前高层事件数；如果没有这行代码，无法证明拒绝路径没有新增事件。
    missing = runtime.click_by_query(window, observation, "DoesNotExist")  # 新增代码+Phase70GenericControlActions: 执行找不到控件的反例；如果没有这行代码，zero_event_refusal token 没证据。
    generic_click = bool(click.get("ok") and visual.get("ok") and click.get("generic_click") and visual.get("generic_click"))  # 新增代码+Phase70GenericControlActions: 汇总点击能力；如果没有这行代码，CLI 无法表达点击是否完整。
    generic_type = bool(typed.get("ok") and typed.get("generic_type") and not typed.get("text_summary", {}).get("raw_text_included", True))  # 新增代码+Phase70GenericControlActions: 汇总输入能力和脱敏；如果没有这行代码，输入原文泄露可能漏过。
    control_locator = bool(click.get("used_control_locator") and typed.get("used_control_locator"))  # 新增代码+Phase70GenericControlActions: 汇总控件定位能力；如果没有这行代码，query 可能只是硬编码坐标。
    visual_fallback = bool(visual.get("visual_fallback") and not visual.get("used_control_locator"))  # 新增代码+Phase70GenericControlActions: 汇总视觉兜底能力；如果没有这行代码，画布路径可能假冒 UIA 控件。
    before_after_evidence = bool(click.get("before_after_evidence") and typed.get("before_after_evidence") and visual.get("before_after_evidence"))  # 新增代码+Phase70GenericControlActions: 汇总动作前后证据；如果没有这行代码，闭环执行缺少验证基础。
    zero_event_refusal = bool(missing.get("zero_event_refusal") and missing.get("high_level_event_count") == 0 and len(tool.events) == event_count_before_missing)  # 新增代码+Phase70GenericControlActions: 汇总零事件拒绝；如果没有这行代码，找不到目标仍可能有副作用。
    high_level_tool_bridge = bool(all(not event.get("direct_low_level_bypass", True) for event in tool.events))  # 新增代码+Phase70GenericControlActions: 汇总高层工具桥接；如果没有这行代码，绕过 Phase62 风格接口不会暴露。
    passed = bool(generic_click and generic_type and control_locator and visual_fallback and before_after_evidence and zero_event_refusal and high_level_tool_bridge and not PHASE70_ACTIONS_EXPANDED)  # 新增代码+Phase70GenericControlActions: 汇总合同通过条件；如果没有这行代码，main 无法用退出码表达失败。
    return {"marker": PHASE70_GENERIC_CONTROL_ACTIONS_MARKER, "ok_token": PHASE70_GENERIC_CONTROL_ACTIONS_OK_TOKEN, "model": PHASE70_GENERIC_CONTROL_ACTIONS_MODEL, "generic_click": generic_click, "generic_type": generic_type, "control_locator": control_locator, "visual_fallback": visual_fallback, "before_after_evidence": before_after_evidence, "zero_event_refusal": zero_event_refusal, "high_level_tool_bridge": high_level_tool_bridge, "actions_expanded": PHASE70_ACTIONS_EXPANDED, "passed": passed, "results": {"click": click, "type": typed, "visual": visual, "missing": missing}, "events": _phase70_redact_payload(tool.events)}  # 新增代码+Phase70GenericControlActions: 返回完整合同报告；如果没有这行代码，测试和 CLI 拿不到统一结果。
# 新增代码+Phase70GenericControlActions: 函数段结束，run_phase70_generic_control_actions_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase70_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase70GenericControlActions: 函数段开始，把报告转成稳定 token 行；如果没有这个函数，真实终端场景要解析复杂 JSON。
    return f"{PHASE70_GENERIC_CONTROL_ACTIONS_MARKER} {PHASE70_GENERIC_CONTROL_ACTIONS_OK_TOKEN} generic_click={_phase70_bool_token(report.get('generic_click'))} generic_type={_phase70_bool_token(report.get('generic_type'))} control_locator={_phase70_bool_token(report.get('control_locator'))} visual_fallback={_phase70_bool_token(report.get('visual_fallback'))} before_after_evidence={_phase70_bool_token(report.get('before_after_evidence'))} zero_event_refusal={_phase70_bool_token(report.get('zero_event_refusal'))} actions_expanded={_phase70_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase70GenericControlActions: 返回固定顺序 token；如果没有这行代码，验收输出容易漂移。
# 新增代码+Phase70GenericControlActions: 函数段结束，phase70_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase70GenericControlActions: 函数段开始，提供命令行入口；如果没有这个函数，真实终端无法执行 Phase70 验收。
    _ = argv  # 新增代码+Phase70GenericControlActions: 保留 argv 以便未来扩展；如果没有这行代码，静态检查可能提示未使用参数。
    report = run_phase70_generic_control_actions_contract()  # 新增代码+Phase70GenericControlActions: 执行合同自检；如果没有这行代码，CLI 不会验证 Phase70 能力。
    print(phase70_cli_line(report))  # 新增代码+Phase70GenericControlActions: 打印稳定 token 行；如果没有这行代码，debug log 无法确认验收结果。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase70GenericControlActions: 打印结构化报告便于失败复盘；如果没有这行代码，失败时不易定位原因。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase70GenericControlActions: 根据合同结果返回退出码；如果没有这行代码，失败也可能被当成功。
# 新增代码+Phase70GenericControlActions: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["PHASE70_ACTIONS_EXPANDED", "PHASE70_GENERIC_CONTROL_ACTIONS_MARKER", "PHASE70_GENERIC_CONTROL_ACTIONS_MODEL", "PHASE70_GENERIC_CONTROL_ACTIONS_OK_TOKEN", "Phase70RecordingHighLevelTool", "WindowsGenericControlActionRuntime", "main", "phase70_cli_line", "run_phase70_generic_control_actions_contract"]  # 新增代码+Phase70GenericControlActions: 限定公开导出名称；如果没有这行代码，包导入容易暴露内部 helper 或漏掉合同入口。


if __name__ == "__main__":  # 新增代码+Phase70GenericControlActions: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase70GenericControlActions: 调用 main 并传递退出码；如果没有这行代码，命令行状态不明确。
