"""Cua Driver 借鉴的 Windows UIA 语义 Pattern 分发器。"""  # 新增代码+CuaDriverBorrowing：说明本模块把元素缓存命中的 raw_element 转成更稳的 UIA 语义动作；如果没有这一行，读者不知道该文件为何存在。
from __future__ import annotations  # 新增代码+CuaDriverBorrowing：启用延迟类型解析；如果没有这一行，部分类型标注在旧入口下可能提前求值失败。

from typing import Any, Callable, Mapping  # 新增代码+CuaDriverBorrowing：导入通用类型；如果没有这一行，分发器无法清楚表达输入对象和方法调用。

CUA_DRIVER_BORROWING_UIA_PATTERN_MODEL = "cua_driver_borrowing_uia_patterns_v1"  # 新增代码+CuaDriverBorrowing：标记当前 UIA Pattern 分发版本；如果没有这一行，日志和验收矩阵无法确认能力版本。
CLICK_TOOL_NAMES = {"left_click", "click", "double_click", "right_click"}  # 新增代码+CuaDriverBorrowing：定义按点击处理的工具名集合；如果没有这一行，按钮类控件无法走 Invoke/Toggle。
TYPE_TOOL_NAMES = {"type", "type_text", "input_text"}  # 新增代码+CuaDriverBorrowing：定义按文本输入处理的工具名集合；如果没有这一行，文本框无法走 ValuePattern。
SET_VALUE_TOOL_NAMES = {"set_value", "set_control_value", "set_slider_value"}  # 新增代码+CuaDriverBorrowing：定义按设置值处理的工具名集合；如果没有这一行，滑块和数值控件无法走 RangeValuePattern。


# 新增代码+CuaDriverBorrowing：函数段开始，_raw_element_from_snapshot 从缓存快照中取真实 UIA 元素；如果没有这段函数，分发器只能处理一种对象形态。
def _raw_element_from_snapshot(snapshot: Any) -> Any:  # 新增代码+CuaDriverBorrowing：定义 raw_element 提取入口；如果没有这一行，外部无法传入元素快照。
    if isinstance(snapshot, Mapping):  # 新增代码+CuaDriverBorrowing：判断快照是否是字典；如果没有这一行，字典缓存结构无法被识别。
        return snapshot.get("raw_element", snapshot)  # 新增代码+CuaDriverBorrowing：优先返回 raw_element，否则把字典本身当元素；如果没有这一行，兼容字典快照会失败。
    return getattr(snapshot, "raw_element", snapshot)  # 新增代码+CuaDriverBorrowing：优先读取对象属性 raw_element，否则把对象本身当元素；如果没有这一行，dataclass 和测试替身无法复用。
# 新增代码+CuaDriverBorrowing：函数段结束，_raw_element_from_snapshot 到此结束；如果没有这个边界说明，初学者不容易看出元素提取范围。


# 新增代码+CuaDriverBorrowing：函数段开始，_first_callable 找到元素上第一个可调用 Pattern 方法；如果没有这段函数，方法兼容分支会散落各处。
def _first_callable(raw_element: Any, *method_names: str) -> tuple[str, Callable[..., Any]] | None:  # 新增代码+CuaDriverBorrowing：定义方法查找入口；如果没有这一行，分发器无法兼容不同 UIA 包的方法名。
    for method_name in method_names:  # 新增代码+CuaDriverBorrowing：按优先级遍历候选方法名；如果没有这一行，只能支持一种命名。
        method = getattr(raw_element, method_name, None)  # 新增代码+CuaDriverBorrowing：从元素读取方法；如果没有这一行，无法发现 InvokePattern 或 ValuePattern。
        if callable(method):  # 新增代码+CuaDriverBorrowing：确认读取到的是可调用方法；如果没有这一行，普通属性会被误当成动作。
            return method_name, method  # 新增代码+CuaDriverBorrowing：返回命中的方法名和方法；如果没有这一行，调用方不知道该执行哪个 Pattern。
    return None  # 新增代码+CuaDriverBorrowing：没有可调用方法时返回 None；如果没有这一行，上层无法进入物理输入后备。
# 新增代码+CuaDriverBorrowing：函数段结束，_first_callable 到此结束；如果没有这个边界说明，初学者不容易看出方法查找范围。


# 新增代码+CuaDriverBorrowing：函数段开始，_success_result 统一包装语义动作成功结果；如果没有这段函数，动作层拿到的证据字段会不一致。
def _success_result(dispatch_path: str, method_name: str, value: Any | None = None) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：定义成功结果构造入口；如果没有这一行，多个 Pattern 成功分支会重复拼字典。
    return {  # 新增代码+CuaDriverBorrowing：返回成功结果字典开始；如果没有这一行，调用方拿不到结构化证据。
        "ok": True,  # 新增代码+CuaDriverBorrowing：标记语义动作成功；如果没有这一行，上层不知道是否可以跳过物理后备。
        "reason": "semantic_pattern_dispatched",  # 新增代码+CuaDriverBorrowing：说明成功原因；如果没有这一行，日志无法区分语义成功和普通成功。
        "dispatch_path": dispatch_path,  # 新增代码+CuaDriverBorrowing：记录使用的 UIA 路径；如果没有这一行，观察-动作-验证链路缺少关键证据。
        "method_name": method_name,  # 新增代码+CuaDriverBorrowing：记录实际调用的方法名；如果没有这一行，调试不同 UIA 包兼容性会很困难。
        "value": value,  # 新增代码+CuaDriverBorrowing：记录写入值或 None；如果没有这一行，set_value 类动作缺少审计线索。
        "semantic_action_performed": True,  # 新增代码+CuaDriverBorrowing：标记已经完成语义动作；如果没有这一行，上层可能重复执行物理输入。
    }  # 新增代码+CuaDriverBorrowing：返回成功结果字典结束；如果没有这一行，字典语法不完整。
# 新增代码+CuaDriverBorrowing：函数段结束，_success_result 到此结束；如果没有这个边界说明，初学者不容易看出成功结果范围。


# 新增代码+CuaDriverBorrowing：函数段开始，_unavailable_result 统一包装语义动作不可用结果；如果没有这段函数，物理后备原因会不稳定。
def _unavailable_result(tool_name: str) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：定义不可用结果构造入口；如果没有这一行，失败分支无法统一返回 reason。
    return {  # 新增代码+CuaDriverBorrowing：返回不可用结果字典开始；如果没有这一行，调用方拿不到结构化失败信息。
        "ok": False,  # 新增代码+CuaDriverBorrowing：标记语义动作失败；如果没有这一行，上层可能误以为已经执行。
        "reason": "semantic_pattern_unavailable",  # 新增代码+CuaDriverBorrowing：说明失败原因是没有可用 Pattern；如果没有这一行，上层无法安全退回物理输入。
        "dispatch_path": "semantic_pattern_unavailable",  # 新增代码+CuaDriverBorrowing：记录失败路径；如果没有这一行，日志无法看出为什么没有走 UIA。
        "tool_name": tool_name,  # 新增代码+CuaDriverBorrowing：记录请求的工具名；如果没有这一行，排查失败时不知道是哪类动作。
        "semantic_action_performed": False,  # 新增代码+CuaDriverBorrowing：标记没有执行语义动作；如果没有这一行，上层可能跳过必要的后备。
    }  # 新增代码+CuaDriverBorrowing：返回不可用结果字典结束；如果没有这一行，字典语法不完整。
# 新增代码+CuaDriverBorrowing：函数段结束，_unavailable_result 到此结束；如果没有这个边界说明，初学者不容易看出失败结果范围。


# 新增代码+CuaDriverBorrowing：函数段开始，_dispatch_click_pattern 处理点击类语义动作；如果没有这段函数，按钮和复选框只能依赖坐标点击。
def _dispatch_click_pattern(raw_element: Any, tool_name: str) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：定义点击分发入口；如果没有这一行，click 工具无法尝试 UIA Pattern。
    invoke = _first_callable(raw_element, "invoke", "Invoke")  # 新增代码+CuaDriverBorrowing：优先查找 InvokePattern；如果没有这一行，按钮点击不会走最稳路径。
    if invoke is not None:  # 新增代码+CuaDriverBorrowing：判断 InvokePattern 是否可用；如果没有这一行，None 会被误调用。
        method_name, method = invoke  # 新增代码+CuaDriverBorrowing：拆出方法名和方法；如果没有这一行，无法执行并记录证据。
        method()  # 新增代码+CuaDriverBorrowing：执行 InvokePattern；如果没有这一行，语义点击不会真正发生。
        return _success_result("uia_invoke", method_name)  # 新增代码+CuaDriverBorrowing：返回 invoke 成功证据；如果没有这一行，上层无法确认点击已完成。
    toggle = _first_callable(raw_element, "toggle", "Toggle")  # 新增代码+CuaDriverBorrowing：查找 TogglePattern 后备；如果没有这一行，复选框类控件无法稳定切换。
    if toggle is not None:  # 新增代码+CuaDriverBorrowing：判断 TogglePattern 是否可用；如果没有这一行，None 会被误调用。
        method_name, method = toggle  # 新增代码+CuaDriverBorrowing：拆出方法名和方法；如果没有这一行，无法执行并记录证据。
        method()  # 新增代码+CuaDriverBorrowing：执行 TogglePattern；如果没有这一行，勾选状态不会改变。
        return _success_result("uia_toggle", method_name)  # 新增代码+CuaDriverBorrowing：返回 toggle 成功证据；如果没有这一行，上层无法确认后备语义动作已完成。
    select = _first_callable(raw_element, "select", "Select")  # 新增代码+CuaDriverBorrowing：查找 SelectPattern 后备；如果没有这一行，列表项类控件无法稳定选择。
    if select is not None:  # 新增代码+CuaDriverBorrowing：判断 SelectPattern 是否可用；如果没有这一行，None 会被误调用。
        method_name, method = select  # 新增代码+CuaDriverBorrowing：拆出方法名和方法；如果没有这一行，无法执行并记录证据。
        method()  # 新增代码+CuaDriverBorrowing：执行 SelectPattern；如果没有这一行，列表项不会被选择。
        return _success_result("uia_select", method_name)  # 新增代码+CuaDriverBorrowing：返回 select 成功证据；如果没有这一行，上层无法确认选择已完成。
    return _unavailable_result(tool_name)  # 新增代码+CuaDriverBorrowing：没有点击语义 Pattern 时返回不可用；如果没有这一行，上层无法退回物理点击。
# 新增代码+CuaDriverBorrowing：函数段结束，_dispatch_click_pattern 到此结束；如果没有这个边界说明，初学者不容易看出点击语义范围。


# 新增代码+CuaDriverBorrowing：函数段开始，_dispatch_value_pattern 处理文本输入类语义动作；如果没有这段函数，文本框只能依赖键盘模拟。
def _dispatch_value_pattern(raw_element: Any, arguments: Mapping[str, Any], tool_name: str) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：定义文本值分发入口；如果没有这一行，type 工具无法尝试 ValuePattern。
    value = arguments.get("text", arguments.get("value", ""))  # 新增代码+CuaDriverBorrowing：读取要写入的文本；如果没有这一行，ValuePattern 不知道输入内容。
    method_match = _first_callable(raw_element, "set_value", "SetValue", "setValue")  # 新增代码+CuaDriverBorrowing：查找 ValuePattern 写入方法；如果没有这一行，文本语义路径无法执行。
    if method_match is None:  # 新增代码+CuaDriverBorrowing：判断 ValuePattern 是否缺失；如果没有这一行，None 会被误调用。
        return _unavailable_result(tool_name)  # 新增代码+CuaDriverBorrowing：返回不可用以便上层后备；如果没有这一行，文本输入会静默失败。
    method_name, method = method_match  # 新增代码+CuaDriverBorrowing：拆出方法名和方法；如果没有这一行，无法执行并记录证据。
    method(str(value))  # 新增代码+CuaDriverBorrowing：执行文本写入并统一转字符串；如果没有这一行，文本框不会被填入内容。
    return _success_result("uia_value_pattern", method_name, str(value))  # 新增代码+CuaDriverBorrowing：返回文本写入成功证据；如果没有这一行，上层无法确认文本已写入。
# 新增代码+CuaDriverBorrowing：函数段结束，_dispatch_value_pattern 到此结束；如果没有这个边界说明，初学者不容易看出文本语义范围。


# 新增代码+CuaDriverBorrowing：函数段开始，_dispatch_range_or_value_pattern 处理设置值类语义动作；如果没有这段函数，滑块和数值控件只能依赖粗糙拖拽。
def _dispatch_range_or_value_pattern(raw_element: Any, arguments: Mapping[str, Any], tool_name: str) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：定义设置值分发入口；如果没有这一行，set_value 工具无法尝试 RangeValuePattern。
    value = arguments.get("value", arguments.get("text", ""))  # 新增代码+CuaDriverBorrowing：读取要设置的值；如果没有这一行，数值或文本设置没有输入。
    range_match = _first_callable(raw_element, "set_current_value", "SetCurrentValue", "setCurrentValue")  # 新增代码+CuaDriverBorrowing：优先查找 RangeValuePattern；如果没有这一行，滑块数值无法稳定设置。
    if range_match is not None:  # 新增代码+CuaDriverBorrowing：判断 RangeValuePattern 是否可用；如果没有这一行，数值控件无法走首选路径。
        method_name, method = range_match  # 新增代码+CuaDriverBorrowing：拆出方法名和方法；如果没有这一行，无法执行并记录证据。
        numeric_value = float(value)  # 新增代码+CuaDriverBorrowing：把值转为浮点数；如果没有这一行，RangeValuePattern 可能收到错误类型。
        method(numeric_value)  # 新增代码+CuaDriverBorrowing：执行数值设置；如果没有这一行，滑块或数值控件不会变化。
        return _success_result("uia_range_value_pattern", method_name, numeric_value)  # 新增代码+CuaDriverBorrowing：返回数值写入成功证据；如果没有这一行，上层无法确认数值 Pattern 已执行。
    value_match = _first_callable(raw_element, "set_value", "SetValue", "setValue")  # 新增代码+CuaDriverBorrowing：没有 RangeValuePattern 时查找普通 ValuePattern；如果没有这一行，非数值控件无法设置值。
    if value_match is not None:  # 新增代码+CuaDriverBorrowing：判断 ValuePattern 是否可用；如果没有这一行，None 会被误调用。
        method_name, method = value_match  # 新增代码+CuaDriverBorrowing：拆出方法名和方法；如果没有这一行，无法执行并记录证据。
        method(str(value))  # 新增代码+CuaDriverBorrowing：执行普通值写入；如果没有这一行，文本值不会改变。
        return _success_result("uia_value_pattern", method_name, str(value))  # 新增代码+CuaDriverBorrowing：返回普通值写入成功证据；如果没有这一行，上层无法确认 set_value 已完成。
    return _unavailable_result(tool_name)  # 新增代码+CuaDriverBorrowing：没有可用 Pattern 时返回不可用；如果没有这一行，上层无法退回物理输入。
# 新增代码+CuaDriverBorrowing：函数段结束，_dispatch_range_or_value_pattern 到此结束；如果没有这个边界说明，初学者不容易看出设置值语义范围。


# 新增代码+CuaDriverBorrowing：函数段开始，dispatch_semantic_action 是对外唯一分发入口；如果没有这段函数，动作层无法统一调用 UIA 语义能力。
def dispatch_semantic_action(tool_name: str, snapshot: Any, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：定义语义动作分发入口；如果没有这一行，外部无法把 tool_name 映射到 Pattern。
    safe_arguments = arguments or {}  # 新增代码+CuaDriverBorrowing：把 None 参数转为空字典；如果没有这一行，无参点击会在读取参数时报错。
    raw_element = _raw_element_from_snapshot(snapshot)  # 新增代码+CuaDriverBorrowing：从快照提取真实元素；如果没有这一行，缓存命中的元素无法被操作。
    if tool_name in CLICK_TOOL_NAMES:  # 新增代码+CuaDriverBorrowing：识别点击类工具；如果没有这一行，left_click 不会走 Invoke/Toggle。
        return _dispatch_click_pattern(raw_element, tool_name)  # 新增代码+CuaDriverBorrowing：分发点击 Pattern；如果没有这一行，按钮语义动作不会执行。
    if tool_name in TYPE_TOOL_NAMES:  # 新增代码+CuaDriverBorrowing：识别文本输入类工具；如果没有这一行，type 不会走 ValuePattern。
        return _dispatch_value_pattern(raw_element, safe_arguments, tool_name)  # 新增代码+CuaDriverBorrowing：分发文本 Pattern；如果没有这一行，文本框语义输入不会执行。
    if tool_name in SET_VALUE_TOOL_NAMES:  # 新增代码+CuaDriverBorrowing：识别设置值类工具；如果没有这一行，set_value 不会走 RangeValuePattern。
        return _dispatch_range_or_value_pattern(raw_element, safe_arguments, tool_name)  # 新增代码+CuaDriverBorrowing：分发设置值 Pattern；如果没有这一行，滑块或数值控件无法语义设置。
    return _unavailable_result(tool_name)  # 新增代码+CuaDriverBorrowing：未知工具返回不可用；如果没有这一行，上层无法安全退回原动作路径。
# 新增代码+CuaDriverBorrowing：函数段结束，dispatch_semantic_action 到此结束；如果没有这个边界说明，初学者不容易看出公开分发范围。


__all__ = [  # 新增代码+CuaDriverBorrowing：声明公开 API 开始；如果没有这一行，外部不清楚哪些名字是稳定接口。
    "CUA_DRIVER_BORROWING_UIA_PATTERN_MODEL",  # 新增代码+CuaDriverBorrowing：公开分发器版本；如果没有这一行，验收矩阵无法读取能力标记。
    "dispatch_semantic_action",  # 新增代码+CuaDriverBorrowing：公开语义动作分发入口；如果没有这一行，动作层无法复用 UIA Pattern 分发。
]  # 新增代码+CuaDriverBorrowing：声明公开 API 结束；如果没有这一行，公开列表语法不完整。
