"""ClaudeCode Computer Use 参数归一化。"""  # 新增代码+ClaudeCodeProtocolParity：说明本文件把 ClaudeCode 字段转成 Windows runtime 字段；如果没有这行代码，协议转换职责会散落在各工具里。
from __future__ import annotations  # 新增代码+ClaudeCodeProtocolParity：延迟类型注解解析；如果没有这行代码，后续类型扩展更容易导入出错。

from typing import Any  # 新增代码+ClaudeCodeProtocolParity：导入通用 JSON 类型；如果没有这行代码，normalizer 输入输出边界不清楚。

from .claudecode_protocol import CLAUDECODE_ACTIONS_FIELD, CLAUDECODE_AMOUNT_FIELD, CLAUDECODE_APPS_FIELD, CLAUDECODE_BUNDLE_ID_FIELD, CLAUDECODE_COORDINATE_FIELD, CLAUDECODE_DIRECTION_FIELD, CLAUDECODE_DURATION_FIELD, CLAUDECODE_REGION_FIELD, CLAUDECODE_START_COORDINATE_FIELD, CLAUDECODE_TEXT_FIELD, normalize_app_identity  # 新增代码+ClaudeCodeProtocolParity：导入 ClaudeCode 字段常量和 app helper；如果没有这行代码，normalizer 会重复硬编码字段名。


def _coordinate_pair(value: Any) -> tuple[int, int] | None:  # 新增代码+ClaudeCodeProtocolParity：函数段开始，解析 ClaudeCode `[x, y]` 坐标；如果没有这段函数，各工具会重复写脆弱列表解析。
    if isinstance(value, (list, tuple)) and len(value) >= 2:  # 新增代码+ClaudeCodeProtocolParity：只接受至少两个元素的列表或元组；如果没有这行代码，字符串坐标可能被错误拆开。
        try:  # 新增代码+ClaudeCodeProtocolParity：保护整数转换；如果没有这行代码，坏坐标会让整个工具调用崩溃。
            return (int(value[0]), int(value[1]))  # 新增代码+ClaudeCodeProtocolParity：返回整数坐标二元组；如果没有这行代码，Windows runtime 拿不到 x/y。
        except (TypeError, ValueError):  # 新增代码+ClaudeCodeProtocolParity：捕获无法转整数的坐标；如果没有这行代码，模型偶发坏参会导致异常外泄。
            return None  # 新增代码+ClaudeCodeProtocolParity：坏坐标返回 None 交给后续校验；如果没有这行代码，调用方无法温和失败。
    return None  # 新增代码+ClaudeCodeProtocolParity：非坐标数组返回 None；如果没有这行代码，函数可能隐式返回导致读者困惑。
# 新增代码+ClaudeCodeProtocolParity：函数段结束，_coordinate_pair 到此结束；如果没有这个边界说明，用户不容易看出坐标解析范围。


def _region_quad(value: Any) -> tuple[int, int, int, int] | None:  # 新增代码+ClaudeCodeProtocolParity：函数段开始，解析 ClaudeCode `[x, y, width, height]` 区域；如果没有这段函数，zoom 区域解析会散落。
    if isinstance(value, (list, tuple)) and len(value) >= 4:  # 新增代码+ClaudeCodeProtocolParity：只接受至少四个元素的区域数组；如果没有这行代码，短数组会被误当有效区域。
        try:  # 新增代码+ClaudeCodeProtocolParity：保护整数转换；如果没有这行代码，坏区域参数会让 runtime 崩溃。
            return (int(value[0]), int(value[1]), int(value[2]), int(value[3]))  # 新增代码+ClaudeCodeProtocolParity：返回整数区域四元组；如果没有这行代码，Windows zoom 拿不到裁剪范围。
        except (TypeError, ValueError):  # 新增代码+ClaudeCodeProtocolParity：捕获无法转整数的区域；如果没有这行代码，错误参数会外泄异常。
            return None  # 新增代码+ClaudeCodeProtocolParity：坏区域返回 None 交给后续校验；如果没有这行代码，调用方无法自行决定恢复。
    return None  # 新增代码+ClaudeCodeProtocolParity：非区域数组返回 None；如果没有这行代码，函数可能隐式返回。
# 新增代码+ClaudeCodeProtocolParity：函数段结束，_region_quad 到此结束；如果没有这个边界说明，用户不容易看出区域解析范围。


def _scroll_delta(direction: Any, amount: Any) -> int | None:  # 新增代码+ClaudeCodeProtocolParity：函数段开始，把 ClaudeCode direction/amount 转成 Windows delta_y；如果没有这段函数，scroll 会继续只懂 delta_y。
    if direction is None and amount is None:  # 新增代码+ClaudeCodeProtocolParity：没有 ClaudeCode 滚动字段时不处理；如果没有这行代码，旧 delta_y 可能被错误覆盖。
        return None  # 新增代码+ClaudeCodeProtocolParity：返回 None 表示保持旧参数；如果没有这行代码，调用方无法区分无输入和零滚动。
    direction_text = str(direction or "down").lower().strip()  # 新增代码+ClaudeCodeProtocolParity：读取滚动方向并默认向下；如果没有这行代码，只有 amount 的调用无法生成方向。
    try:  # 新增代码+ClaudeCodeProtocolParity：保护滚动数量转换；如果没有这行代码，坏 amount 会让工具调用崩溃。
        amount_value = int(amount if amount is not None else 1)  # 新增代码+ClaudeCodeProtocolParity：把数量转成整数并默认 1；如果没有这行代码，滚动距离没有稳定数值。
    except (TypeError, ValueError):  # 新增代码+ClaudeCodeProtocolParity：捕获无法转整数的数量；如果没有这行代码，模型坏参会外泄异常。
        amount_value = 1  # 新增代码+ClaudeCodeProtocolParity：坏数量回退到 1；如果没有这行代码，滚动工具难以容错。
    sign = -1 if direction_text in {"up", "left"} else 1  # 新增代码+ClaudeCodeProtocolParity：把方向转成 delta 符号；如果没有这行代码，向上/向下滚动无法区分。
    return sign * abs(amount_value)  # 新增代码+ClaudeCodeProtocolParity：返回带方向的滚动 delta；如果没有这行代码，Windows runtime 拿不到 delta_y。
# 新增代码+ClaudeCodeProtocolParity：函数段结束，_scroll_delta 到此结束；如果没有这个边界说明，用户不容易看出滚动转换范围。


def normalize_computer_use_arguments(tool_name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:  # 新增代码+ClaudeCodeProtocolParity：函数段开始，统一把 ClaudeCode 参数兼容到 Windows runtime；如果没有这段函数，每个工具会重复做别名转换。
    normalized = dict(arguments or {})  # 新增代码+ClaudeCodeProtocolParity：复制输入参数避免污染调用方对象；如果没有这行代码，batch 中的原始步骤可能被改写。
    raw_name = str(tool_name or "").strip().removeprefix("mcp__computer-use__")  # 新增代码+ClaudeCodeProtocolParity：规范工具名用于判断特殊分支；如果没有这行代码，前缀工具无法进入正确转换逻辑。
    coordinate = _coordinate_pair(normalized.get(CLAUDECODE_COORDINATE_FIELD))  # 新增代码+ClaudeCodeProtocolParity：读取 ClaudeCode 主坐标字段；如果没有这行代码，coordinate 不会映射到 x/y。
    if coordinate is not None:  # 新增代码+ClaudeCodeProtocolParity：确认 coordinate 可用；如果没有这行代码，坏坐标可能覆盖旧 x/y。
        normalized.setdefault("x", coordinate[0])  # 新增代码+ClaudeCodeProtocolParity：为 Windows runtime 补 x；如果没有这行代码，旧执行层无法读取横坐标。
        normalized.setdefault("y", coordinate[1])  # 新增代码+ClaudeCodeProtocolParity：为 Windows runtime 补 y；如果没有这行代码，旧执行层无法读取纵坐标。
    start_coordinate = _coordinate_pair(normalized.get(CLAUDECODE_START_COORDINATE_FIELD))  # 新增代码+ClaudeCodeProtocolParity：读取拖拽起点字段；如果没有这行代码，start_coordinate 不会映射到 start_x/start_y。
    if start_coordinate is not None:  # 新增代码+ClaudeCodeProtocolParity：确认起点坐标可用；如果没有这行代码，坏起点可能覆盖旧字段。
        normalized.setdefault("start_x", start_coordinate[0])  # 新增代码+ClaudeCodeProtocolParity：补 Windows 拖拽起点 x；如果没有这行代码，drag_path 会缺起点横坐标。
        normalized.setdefault("start_y", start_coordinate[1])  # 新增代码+ClaudeCodeProtocolParity：补 Windows 拖拽起点 y；如果没有这行代码，drag_path 会缺起点纵坐标。
    if raw_name == "left_click_drag" and coordinate is not None:  # 新增代码+ClaudeCodeProtocolParity：拖拽工具里 coordinate 表示终点；如果没有这行代码，拖拽终点无法按 ClaudeCode 字段表达。
        normalized.setdefault("end_x", coordinate[0])  # 新增代码+ClaudeCodeProtocolParity：补 Windows 拖拽终点 x；如果没有这行代码，drag_path 会缺终点横坐标。
        normalized.setdefault("end_y", coordinate[1])  # 新增代码+ClaudeCodeProtocolParity：补 Windows 拖拽终点 y；如果没有这行代码，drag_path 会缺终点纵坐标。
    region = _region_quad(normalized.get(CLAUDECODE_REGION_FIELD))  # 新增代码+ClaudeCodeProtocolParity：读取 ClaudeCode zoom 区域；如果没有这行代码，region 不会映射到 x/y/width/height。
    if region is not None:  # 新增代码+ClaudeCodeProtocolParity：确认区域可用；如果没有这行代码，坏区域可能覆盖旧字段。
        normalized.setdefault("x", region[0])  # 新增代码+ClaudeCodeProtocolParity：补区域左上角 x；如果没有这行代码，Windows zoom 无法定位区域。
        normalized.setdefault("y", region[1])  # 新增代码+ClaudeCodeProtocolParity：补区域左上角 y；如果没有这行代码，Windows zoom 无法定位区域。
        normalized.setdefault("width", region[2])  # 新增代码+ClaudeCodeProtocolParity：补区域宽度；如果没有这行代码，Windows zoom 无法裁剪宽度。
        normalized.setdefault("height", region[3])  # 新增代码+ClaudeCodeProtocolParity：补区域高度；如果没有这行代码，Windows zoom 无法裁剪高度。
    if CLAUDECODE_DURATION_FIELD in normalized:  # 新增代码+ClaudeCodeProtocolParity：检查 ClaudeCode duration 字段；如果没有这行代码，hold_key 时长别名不会生效。
        normalized.setdefault("duration_seconds", normalized.get(CLAUDECODE_DURATION_FIELD))  # 新增代码+ClaudeCodeProtocolParity：把 duration 映射到 duration_seconds；如果没有这行代码，Windows runtime 不知道长按多久。
    if CLAUDECODE_TEXT_FIELD in normalized and raw_name in {"key", "hold_key"}:  # 新增代码+ClaudeCodeProtocolParity：检查按键文本字段；如果没有这行代码，ClaudeCode 的 text 按键表示无法兼容 keys 数组。
        text_value = str(normalized.get(CLAUDECODE_TEXT_FIELD) or "").strip()  # 新增代码+ClaudeCodeProtocolParity：清理按键文本；如果没有这行代码，空白按键会进入 keys。
        if text_value:  # 新增代码+ClaudeCodeProtocolParity：只在文本非空时补 keys；如果没有这行代码，空 text 会覆盖已有 keys。
            normalized.setdefault("keys", [text_value])  # 新增代码+ClaudeCodeProtocolParity：补 Windows runtime keys 数组；如果没有这行代码，按键工具无法执行 text 字段。
            normalized.setdefault("key", text_value)  # 新增代码+ClaudeCodeProtocolParity：补旧 controller 兼容 key 字符串；如果没有这行代码，部分底层只读 key 时会失效。
    if "keys" in normalized and "key" not in normalized:  # 新增代码+ClaudeCodeProtocolParity：检查是否只有 keys 数组；如果没有这行代码，旧 controller 的 key 字符串兼容可能缺失。
        key_values = normalized.get("keys")  # 新增代码+ClaudeCodeProtocolParity：读取 keys 数组；如果没有这行代码，无法生成兼容 key。
        if isinstance(key_values, list) and key_values:  # 新增代码+ClaudeCodeProtocolParity：确认 keys 是非空列表；如果没有这行代码，坏 keys 可能触发索引错误。
            normalized["key"] = str(key_values[0])  # 新增代码+ClaudeCodeProtocolParity：用第一个 key 作为旧字段；如果没有这行代码，旧执行层可能读不到按键。
    delta_y = _scroll_delta(normalized.get(CLAUDECODE_DIRECTION_FIELD), normalized.get(CLAUDECODE_AMOUNT_FIELD))  # 新增代码+ClaudeCodeProtocolParity：从 direction/amount 计算滚动 delta；如果没有这行代码，ClaudeCode 风格 scroll 无法执行。
    if delta_y is not None:  # 新增代码+ClaudeCodeProtocolParity：确认需要补 delta_y；如果没有这行代码，旧 delta_y 可能被无输入覆盖。
        normalized.setdefault("delta_y", delta_y)  # 新增代码+ClaudeCodeProtocolParity：为 Windows runtime 补滚轮数值；如果没有这行代码，scroll 后端不知道滚动距离。
    if CLAUDECODE_BUNDLE_ID_FIELD in normalized:  # 新增代码+ClaudeCodeProtocolParity：检查 open_application bundle_id；如果没有这行代码，ClaudeCode 应用字段不会映射到 app_name。
        normalized.setdefault("app_name", str(normalized.get(CLAUDECODE_BUNDLE_ID_FIELD) or ""))  # 新增代码+ClaudeCodeProtocolParity：补旧 app_name 字段；如果没有这行代码，Windows 应用启动层读不到目标。
    if CLAUDECODE_APPS_FIELD in normalized:  # 新增代码+ClaudeCodeProtocolParity：检查 request_access apps 字段；如果没有这行代码，ClaudeCode 授权应用列表不会映射。
        apps = [normalize_app_identity(app) for app in list(normalized.get(CLAUDECODE_APPS_FIELD) or [])]  # 新增代码+ClaudeCodeProtocolParity：规范化每个 app 对象；如果没有这行代码，授权层会收到混合字符串和对象。
        normalized[CLAUDECODE_APPS_FIELD] = apps  # 新增代码+ClaudeCodeProtocolParity：写回规范化 apps；如果没有这行代码，后续权限结果无法保持 ClaudeCode 结构。
        normalized.setdefault("applications", [app.get("displayName", "") for app in apps])  # 新增代码+ClaudeCodeProtocolParity：补旧 applications 字符串列表；如果没有这行代码，旧 request_access 回调会丢应用名。
    elif "applications" in normalized:  # 新增代码+ClaudeCodeProtocolParity：兼容旧 applications 字段；如果没有这行代码，历史 prompt 的授权应用不会生成 apps 对象。
        apps = [normalize_app_identity(app) for app in list(normalized.get("applications") or [])]  # 新增代码+ClaudeCodeProtocolParity：把旧字符串列表规范为 app 对象；如果没有这行代码，权限模型无法统一输出。
        normalized.setdefault(CLAUDECODE_APPS_FIELD, apps)  # 新增代码+ClaudeCodeProtocolParity：补 ClaudeCode apps 字段；如果没有这行代码，list_granted_applications 无法返回统一结构。
    if CLAUDECODE_ACTIONS_FIELD in normalized:  # 新增代码+ClaudeCodeProtocolParity：检查 computer_batch actions 字段；如果没有这行代码，ClaudeCode batch 字段无法兼容旧 steps。
        normalized.setdefault("steps", normalized.get(CLAUDECODE_ACTIONS_FIELD))  # 新增代码+ClaudeCodeProtocolParity：补旧 steps 字段；如果没有这行代码，旧 session adapter 的 batch 路径可能读不到步骤。
    elif "steps" in normalized:  # 新增代码+ClaudeCodeProtocolParity：兼容旧 steps 字段；如果没有这行代码，历史 batch 调用不会生成 actions。
        normalized.setdefault(CLAUDECODE_ACTIONS_FIELD, normalized.get("steps"))  # 新增代码+ClaudeCodeProtocolParity：补 ClaudeCode actions 字段；如果没有这行代码，v2 batch 只看 actions 时会空执行。
    return normalized  # 新增代码+ClaudeCodeProtocolParity：返回归一化参数副本；如果没有这行代码，runtime 拿不到转换结果。
# 新增代码+ClaudeCodeProtocolParity：函数段结束，normalize_computer_use_arguments 到此结束；如果没有这个边界说明，用户不容易看出协议转换边界。
