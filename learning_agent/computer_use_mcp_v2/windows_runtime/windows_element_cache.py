"""Windows Computer Use 元素索引缓存。"""  # 新增代码+CuaDriverBorrowing：说明本文件负责 Cua Driver 风格元素索引缓存；如果没有这一行，读者不知道本模块的职责。
from __future__ import annotations  # 新增代码+CuaDriverBorrowing：启用延迟类型解析；如果没有这一行，前向类型标注在旧入口下可能导入失败。

from dataclasses import dataclass, field  # 新增代码+CuaDriverBorrowing：导入 dataclass 和 field 简化数据对象；如果没有这一行，快照对象需要大量手写初始化代码。
from typing import Any  # 新增代码+CuaDriverBorrowing：导入 Any 描述 UIA/MSAA 动态节点；如果没有这一行，缓存输入边界不清楚。


CUA_DRIVER_BORROWING_ELEMENT_CACHE_MODEL = "cua_driver_borrowing_element_cache_v1"  # 新增代码+CuaDriverBorrowing：定义缓存模型版本；如果没有这一行，后续证据无法说明元素索引来自哪套合同。
SENSITIVE_ELEMENT_TEXT_TOKENS = ("password", "passwd", "secret", "token", "apikey", "api_key", "credential")  # 新增代码+CuaDriverBorrowing：列出元素缓存敏感词；如果没有这一行，密码和 token 控件文本可能原样进缓存。


def _safe_text(value: Any, max_length: int = 120) -> tuple[str, bool]:  # 新增代码+CuaDriverBorrowing：函数段开始，安全清洗元素文本；如果没有这段函数，name/role/id 等字段会各自处理且容易漏脱敏。
    text = str(value or "").strip()  # 新增代码+CuaDriverBorrowing：把动态值转成去空格字符串；如果没有这一行，None 或对象 repr 会污染缓存。
    lowered = text.lower()  # 新增代码+CuaDriverBorrowing：准备小写文本用于敏感词判断；如果没有这一行，Password 这类大小写变体可能漏掉。
    sensitive = any(token in lowered for token in SENSITIVE_ELEMENT_TEXT_TOKENS)  # 新增代码+CuaDriverBorrowing：判断文本是否包含敏感词；如果没有这一行，缓存无法触发脱敏。
    if sensitive:  # 新增代码+CuaDriverBorrowing：敏感文本进入占位分支；如果没有这一行，敏感字段仍会继续截断后返回。
        return "[redacted]", True  # 新增代码+CuaDriverBorrowing：返回脱敏占位和过滤标记；如果没有这一行，审计无法知道发生过脱敏。
    if len(text) > max_length:  # 新增代码+CuaDriverBorrowing：检查普通文本是否过长；如果没有这一行，大控件文本可能刷屏。
        return text[:max_length], False  # 新增代码+CuaDriverBorrowing：返回截断文本；如果没有这一行，摘要可能携带过长字符串。
    return text, False  # 新增代码+CuaDriverBorrowing：返回安全原文和未过滤标记；如果没有这一行，普通控件名称会丢失。
# 新增代码+CuaDriverBorrowing：函数段结束，_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清洗范围。


def _safe_int(value: Any, default: int = 0) -> int:  # 新增代码+CuaDriverBorrowing：函数段开始，安全读取整数；如果没有这段函数，坏坐标或索引会导致缓存更新崩溃。
    try:  # 新增代码+CuaDriverBorrowing：尝试把输入转成整数；如果没有这一行，字符串数字无法兼容。
        return int(value)  # 新增代码+CuaDriverBorrowing：返回整数值；如果没有这一行，调用方拿不到规范化数字。
    except (TypeError, ValueError):  # 新增代码+CuaDriverBorrowing：捕获空值和非数字文本；如果没有这一行，坏节点会中断整个快照。
        return int(default)  # 新增代码+CuaDriverBorrowing：返回默认整数；如果没有这一行，调用方需要自己兜底。
# 新增代码+CuaDriverBorrowing：函数段结束，_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出整数转换范围。


def _bounds_from_node(node: dict[str, Any]) -> dict[str, int]:  # 新增代码+CuaDriverBorrowing：函数段开始，规范化节点边界；如果没有这段函数，缓存中的 bounds 会有多种不兼容形状。
    raw_bounds = node.get("bounds") if isinstance(node.get("bounds"), dict) else {}  # 新增代码+CuaDriverBorrowing：只接受 dict 形 bounds；如果没有这一行，字符串或 None 会触发 get 错误。
    left = _safe_int(raw_bounds.get("left", raw_bounds.get("Left", 0)))  # 新增代码+CuaDriverBorrowing：读取左边界；如果没有这一行，元素中心无法计算。
    top = _safe_int(raw_bounds.get("top", raw_bounds.get("Top", 0)))  # 新增代码+CuaDriverBorrowing：读取上边界；如果没有这一行，元素中心无法计算。
    right = _safe_int(raw_bounds.get("right", raw_bounds.get("Right", left)))  # 新增代码+CuaDriverBorrowing：读取右边界并兜底左边界；如果没有这一行，宽度缺失时会变成异常。
    bottom = _safe_int(raw_bounds.get("bottom", raw_bounds.get("Bottom", top)))  # 新增代码+CuaDriverBorrowing：读取下边界并兜底上边界；如果没有这一行，高度缺失时会变成异常。
    width = max(0, right - left)  # 新增代码+CuaDriverBorrowing：计算非负宽度；如果没有这一行，坏矩形可能生成负尺寸。
    height = max(0, bottom - top)  # 新增代码+CuaDriverBorrowing：计算非负高度；如果没有这一行，坏矩形可能生成负尺寸。
    return {"left": left, "top": top, "right": right, "bottom": bottom, "width": width, "height": height}  # 新增代码+CuaDriverBorrowing：返回统一边界对象；如果没有这一行，动作层无法稳定读坐标。
# 新增代码+CuaDriverBorrowing：函数段结束，_bounds_from_node 到此结束；如果没有这个边界说明，初学者不容易看出边界规范化范围。


def _target_key(process_id: Any, window_id: Any) -> str:  # 新增代码+CuaDriverBorrowing：函数段开始，构造缓存键；如果没有这段函数，进程和窗口作用域可能在多处拼接不一致。
    return f"pid:{str(process_id or '').strip()}|window:{str(window_id or '').strip()}"  # 新增代码+CuaDriverBorrowing：返回同时包含进程和窗口的键；如果没有这一行，元素索引可能跨目标误用。
# 新增代码+CuaDriverBorrowing：函数段结束，_target_key 到此结束；如果没有这个边界说明，初学者不容易看出作用域键格式。


@dataclass(frozen=True)  # 新增代码+CuaDriverBorrowing：声明不可变快照数据类；如果没有这一行，动作执行中快照可能被外部意外改写。
class WindowsElementSnapshot:  # 新增代码+CuaDriverBorrowing：类段开始，描述一次观察中可操作元素；如果没有这个类，缓存只能返回无结构字典。
    process_id: str  # 新增代码+CuaDriverBorrowing：保存进程身份；如果没有这一行，后续无法确认元素来自哪个进程。
    window_id: str  # 新增代码+CuaDriverBorrowing：保存窗口身份；如果没有这一行，后续无法确认元素来自哪个窗口。
    element_index: int  # 新增代码+CuaDriverBorrowing：保存本窗口快照内的元素编号；如果没有这一行，动作层无法按编号定位元素。
    node_id: str = ""  # 新增代码+CuaDriverBorrowing：保存原 UIA 节点 id；如果没有这一行，调试时难以回到 UIA 树。
    name: str = ""  # 新增代码+CuaDriverBorrowing：保存脱敏后的元素名称；如果没有这一行，摘要难以让模型理解目标。
    role: str = ""  # 新增代码+CuaDriverBorrowing：保存脱敏后的控件角色；如果没有这一行，语义动作无法判断按钮或输入框。
    automation_id: str = ""  # 新增代码+CuaDriverBorrowing：保存脱敏后的 automation id；如果没有这一行，稳定定位线索会丢失。
    class_name: str = ""  # 新增代码+CuaDriverBorrowing：保存脱敏后的 class name；如果没有这一行，Win32/UIA 调试会缺少控件类信息。
    bounds: dict[str, int] = field(default_factory=dict)  # 新增代码+CuaDriverBorrowing：保存规范化边界框；如果没有这一行，后备坐标点击无法从元素中心计算。
    enabled: bool = True  # 新增代码+CuaDriverBorrowing：保存控件是否可用；如果没有这一行，动作层可能尝试点击禁用控件。
    clickable: bool = False  # 新增代码+CuaDriverBorrowing：保存观察层判断的可点击标记；如果没有这一行，动作层无法优先选择点击语义路径。
    editable: bool = False  # 新增代码+CuaDriverBorrowing：保存观察层判断的可输入标记；如果没有这一行，文本输入无法优先选择 ValuePattern。
    sensitive_text_filtered: bool = False  # 新增代码+CuaDriverBorrowing：保存是否发生脱敏；如果没有这一行，审计无法证明敏感文本已过滤。
    raw_element: Any | None = None  # 新增代码+CuaDriverBorrowing：保存可选测试/运行时原生元素引用；如果没有这一行，语义 UIA pattern 测试无法绑定 fake 控件。

    def center(self) -> dict[str, int]:  # 新增代码+CuaDriverBorrowing：函数段开始，计算元素中心点；如果没有这段函数，后备点击路径需要重复计算中心。
        left = _safe_int(self.bounds.get("left"))  # 新增代码+CuaDriverBorrowing：读取左边界；如果没有这一行，中心 x 无法计算。
        top = _safe_int(self.bounds.get("top"))  # 新增代码+CuaDriverBorrowing：读取上边界；如果没有这一行，中心 y 无法计算。
        width = _safe_int(self.bounds.get("width"))  # 新增代码+CuaDriverBorrowing：读取宽度；如果没有这一行，中心 x 会缺少尺寸。
        height = _safe_int(self.bounds.get("height"))  # 新增代码+CuaDriverBorrowing：读取高度；如果没有这一行，中心 y 会缺少尺寸。
        return {"x": left + max(0, width // 2), "y": top + max(0, height // 2)}  # 新增代码+CuaDriverBorrowing：返回中心坐标；如果没有这一行，调用方拿不到可点击点。
    # 新增代码+CuaDriverBorrowing：函数段结束，WindowsElementSnapshot.center 到此结束；如果没有这个边界说明，初学者不容易看出中心计算范围。

    def to_summary(self) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：函数段开始，生成安全摘要；如果没有这段函数，调用方可能直接输出 raw_element。
        return {"element_index": self.element_index, "node_id": self.node_id, "name": self.name, "role": self.role, "automation_id": self.automation_id, "class_name": self.class_name, "bounds": dict(self.bounds), "center": self.center(), "enabled": self.enabled, "clickable": self.clickable, "editable": self.editable, "sensitive_text_filtered": self.sensitive_text_filtered}  # 新增代码+CuaDriverBorrowing：返回不含 raw_element 的摘要；如果没有这一行，原生对象可能泄露到日志。
    # 新增代码+CuaDriverBorrowing：函数段结束，WindowsElementSnapshot.to_summary 到此结束；如果没有这个边界说明，初学者不容易看出摘要范围。
# 新增代码+CuaDriverBorrowing：类段结束，WindowsElementSnapshot 到此结束；如果没有这个边界说明，初学者不容易看出快照对象范围。


class WindowsElementSnapshotCache:  # 新增代码+CuaDriverBorrowing：类段开始，管理按窗口作用域隔离的元素索引；如果没有这个类，观察和动作之间无法共享元素编号。
    def __init__(self, summary_limit: int = 40) -> None:  # 新增代码+CuaDriverBorrowing：函数段开始，初始化缓存和摘要上限；如果没有这段函数，调用方无法创建独立测试缓存。
        self.summary_limit = max(1, int(summary_limit))  # 新增代码+CuaDriverBorrowing：保存至少为 1 的摘要上限；如果没有这一行，大窗口摘要可能无限增长。
        self._snapshots: dict[str, dict[int, WindowsElementSnapshot]] = {}  # 新增代码+CuaDriverBorrowing：保存目标键到元素索引表；如果没有这一行，缓存没有实际存储。
    # 新增代码+CuaDriverBorrowing：函数段结束，WindowsElementSnapshotCache.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def update_snapshot(self, process_id: Any, window_id: Any, nodes: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：函数段开始，用一次观察结果替换目标窗口快照；如果没有这段函数，旧元素索引无法刷新。
        key = _target_key(process_id, window_id)  # 新增代码+CuaDriverBorrowing：构造目标作用域键；如果没有这一行，进程和窗口无法绑定。
        snapshots: dict[int, WindowsElementSnapshot] = {}  # 新增代码+CuaDriverBorrowing：准备新的索引表；如果没有这一行，新旧快照会混在一起。
        sensitive_count = 0  # 新增代码+CuaDriverBorrowing：统计本次过滤的敏感节点数；如果没有这一行，摘要无法审计脱敏数量。
        for fallback_index, raw_node in enumerate(list(nodes or [])):  # 新增代码+CuaDriverBorrowing：遍历观察层节点并提供回退索引；如果没有这一行，节点不会进入缓存。
            node = dict(raw_node) if isinstance(raw_node, dict) else {}  # 新增代码+CuaDriverBorrowing：只接受字典节点并复制；如果没有这一行，坏节点可能污染缓存。
            snapshot = self._snapshot_from_node(process_id, window_id, fallback_index, node)  # 新增代码+CuaDriverBorrowing：把节点转换成不可变快照；如果没有这一行，缓存不会脱敏和规范化字段。
            snapshots[snapshot.element_index] = snapshot  # 新增代码+CuaDriverBorrowing：按 element_index 保存快照；如果没有这一行，lookup 无法按编号读取。
            sensitive_count += 1 if snapshot.sensitive_text_filtered else 0  # 新增代码+CuaDriverBorrowing：累计脱敏元素数；如果没有这一行，summary 缺少过滤统计。
        self._snapshots[key] = snapshots  # 新增代码+CuaDriverBorrowing：整体替换目标窗口旧快照；如果没有这一行，旧索引可能残留。
        return {"model": CUA_DRIVER_BORROWING_ELEMENT_CACHE_MODEL, "target_key": key, "process_id": str(process_id), "window_id": str(window_id), "element_count": len(snapshots), "sensitive_text_filtered": sensitive_count}  # 新增代码+CuaDriverBorrowing：返回更新摘要；如果没有这一行，观察层无法记录缓存更新证据。
    # 新增代码+CuaDriverBorrowing：函数段结束，WindowsElementSnapshotCache.update_snapshot 到此结束；如果没有这个边界说明，初学者不容易看出快照更新范围。

    def _snapshot_from_node(self, process_id: Any, window_id: Any, fallback_index: int, node: dict[str, Any]) -> WindowsElementSnapshot:  # 新增代码+CuaDriverBorrowing：函数段开始，把单个节点转成快照；如果没有这段函数，字段脱敏和索引规则会散落。
        element_index = _safe_int(node.get("element_index", node.get("index", fallback_index)), fallback_index)  # 新增代码+CuaDriverBorrowing：读取显式元素编号或使用顺序编号；如果没有这一行，观察层无法传入稳定编号。
        name, name_filtered = _safe_text(node.get("name"))  # 新增代码+CuaDriverBorrowing：脱敏元素名称；如果没有这一行，密码类名称可能进缓存。
        role, role_filtered = _safe_text(node.get("role"))  # 新增代码+CuaDriverBorrowing：脱敏元素角色；如果没有这一行，角色字段格式不统一。
        automation_id, automation_filtered = _safe_text(node.get("automation_id"))  # 新增代码+CuaDriverBorrowing：脱敏 automation id；如果没有这一行，token 字段可能从定位符泄露。
        class_name, class_filtered = _safe_text(node.get("class_name"))  # 新增代码+CuaDriverBorrowing：脱敏 class name；如果没有这一行，类名字段格式不统一。
        return WindowsElementSnapshot(process_id=str(process_id), window_id=str(window_id), element_index=element_index, node_id=str(node.get("node_id", "")), name=name, role=role, automation_id=automation_id, class_name=class_name, bounds=_bounds_from_node(node), enabled=bool(node.get("enabled", True)), clickable=bool(node.get("clickable", False)), editable=bool(node.get("editable", False)), sensitive_text_filtered=bool(name_filtered or role_filtered or automation_filtered or class_filtered), raw_element=node.get("raw_element"))  # 新增代码+CuaDriverBorrowing：返回规范化快照；如果没有这一行，缓存不会生成可操作元素对象。
    # 新增代码+CuaDriverBorrowing：函数段结束，WindowsElementSnapshotCache._snapshot_from_node 到此结束；如果没有这个边界说明，初学者不容易看出节点转换范围。

    def lookup(self, process_id: Any, window_id: Any, element_index: Any) -> WindowsElementSnapshot | None:  # 新增代码+CuaDriverBorrowing：函数段开始，按进程、窗口和编号查找元素；如果没有这段函数，动作层无法安全取回目标。
        key = _target_key(process_id, window_id)  # 新增代码+CuaDriverBorrowing：构造目标作用域键；如果没有这一行，lookup 可能查错窗口。
        return self._snapshots.get(key, {}).get(_safe_int(element_index, -1))  # 新增代码+CuaDriverBorrowing：返回元素或 None；如果没有这一行，调用方无法 fail closed。
    # 新增代码+CuaDriverBorrowing：函数段结束，WindowsElementSnapshotCache.lookup 到此结束；如果没有这个边界说明，初学者不容易看出查找范围。

    def element_count(self, process_id: Any, window_id: Any) -> int:  # 新增代码+CuaDriverBorrowing：函数段开始，读取目标窗口元素数量；如果没有这段函数，测试和审计需要直接访问私有字典。
        return len(self._snapshots.get(_target_key(process_id, window_id), {}))  # 新增代码+CuaDriverBorrowing：返回目标缓存元素数；如果没有这一行，调用方无法确认快照规模。
    # 新增代码+CuaDriverBorrowing：函数段结束，WindowsElementSnapshotCache.element_count 到此结束；如果没有这个边界说明，初学者不容易看出计数范围。

    def summary(self, process_id: Any, window_id: Any) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：函数段开始，生成目标窗口元素缓存摘要；如果没有这段函数，观察层无法输出有界审计信息。
        key = _target_key(process_id, window_id)  # 新增代码+CuaDriverBorrowing：构造目标作用域键；如果没有这一行，摘要可能混入其他窗口。
        snapshots = self._snapshots.get(key, {})  # 新增代码+CuaDriverBorrowing：读取该目标的索引表；如果没有这一行，后续无法构造元素摘要。
        ordered = [snapshots[index] for index in sorted(snapshots.keys())]  # 新增代码+CuaDriverBorrowing：按索引排序元素；如果没有这一行，摘要顺序会不稳定。
        visible = ordered[: self.summary_limit]  # 新增代码+CuaDriverBorrowing：按摘要上限裁剪；如果没有这一行，大窗口会输出过多元素。
        return {"model": CUA_DRIVER_BORROWING_ELEMENT_CACHE_MODEL, "target_key": key, "process_id": str(process_id), "window_id": str(window_id), "element_count": len(ordered), "elements": [item.to_summary() for item in visible], "truncated": len(ordered) > len(visible), "sensitive_text_filtered": sum(1 for item in ordered if item.sensitive_text_filtered)}  # 新增代码+CuaDriverBorrowing：返回安全有界摘要；如果没有这一行，调用方可能直接输出内部对象。
    # 新增代码+CuaDriverBorrowing：函数段结束，WindowsElementSnapshotCache.summary 到此结束；如果没有这个边界说明，初学者不容易看出摘要范围。

    def clear_target(self, process_id: Any, window_id: Any) -> None:  # 新增代码+CuaDriverBorrowing：函数段开始，清理单个目标快照；如果没有这段函数，窗口关闭后缓存可能长期残留。
        self._snapshots.pop(_target_key(process_id, window_id), None)  # 新增代码+CuaDriverBorrowing：删除目标缓存并容忍不存在；如果没有这一行，清理缺失目标会抛异常。
    # 新增代码+CuaDriverBorrowing：函数段结束，WindowsElementSnapshotCache.clear_target 到此结束；如果没有这个边界说明，初学者不容易看出单目标清理范围。

    def clear_all(self) -> None:  # 新增代码+CuaDriverBorrowing：函数段开始，清理全部快照；如果没有这段函数，turn cleanup 无法一次性释放缓存。
        self._snapshots.clear()  # 新增代码+CuaDriverBorrowing：清空全部目标缓存；如果没有这一行，长期运行可能保留过期元素。
    # 新增代码+CuaDriverBorrowing：函数段结束，WindowsElementSnapshotCache.clear_all 到此结束；如果没有这个边界说明，初学者不容易看出全量清理范围。
# 新增代码+CuaDriverBorrowing：类段结束，WindowsElementSnapshotCache 到此结束；如果没有这个边界说明，初学者不容易看出缓存类范围。


__all__ = ["CUA_DRIVER_BORROWING_ELEMENT_CACHE_MODEL", "WindowsElementSnapshot", "WindowsElementSnapshotCache"]  # 新增代码+CuaDriverBorrowing：限定公开 API；如果没有这一行，通配导入可能暴露内部 helper。
