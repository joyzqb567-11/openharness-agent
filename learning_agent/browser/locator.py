"""浏览器定位引擎，把文字、角色、标签、坐标和视觉查询转换成候选元素。"""  # 新增代码+BrowserLocatorStage5: 说明本模块负责稳定定位；若没有这行代码，定位能力边界不清楚。

from __future__ import annotations  # 新增代码+BrowserLocatorStage5: 延迟解析类型注解；若没有这行代码，复杂类型更容易受定义顺序影响。

import math  # 新增代码+BrowserLocatorStage5: 计算坐标距离需要数学函数；若没有这行代码，坐标定位只能粗略比较。
from typing import Any  # 新增代码+BrowserLocatorStage5: 查询和元素都是通用 JSON；若没有这行代码，类型边界不清楚。

from learning_agent.browser.runtime_models import BrowserLocator, BrowserObservation  # 新增代码+BrowserLocatorStage5: 复用稳定协议模型；若没有这行代码，候选结果无法落盘或审计。


def _text(value: Any) -> str:  # 新增代码+BrowserLocatorStage5: 把未知字段转成文本；若没有这行代码，匹配逻辑会重复处理 None。
    return "" if value is None else str(value)  # 新增代码+BrowserLocatorStage5: None 转空串，其余转字符串；若没有这行代码，lower 调用可能失败。


def _norm(value: Any) -> str:  # 新增代码+BrowserLocatorStage5: 归一化匹配文本；若没有这行代码，大小写和空白会降低命中率。
    return " ".join(_text(value).lower().split())  # 新增代码+BrowserLocatorStage5: 小写并压缩空白；若没有这行代码，复杂页面文本匹配不稳定。


def _contains_score(haystack: Any, needle: Any, exact: bool = False) -> float:  # 新增代码+BrowserLocatorStage5: 计算文本匹配分数；若没有这行代码，每个字段会重复评分逻辑。
    left = _norm(haystack)  # 新增代码+BrowserLocatorStage5: 规范化候选文本；若没有这行代码，比较会受格式影响。
    right = _norm(needle)  # 新增代码+BrowserLocatorStage5: 规范化查询文本；若没有这行代码，比较会受格式影响。
    if not left or not right:  # 新增代码+BrowserLocatorStage5: 空字符串不能匹配；若没有这行代码，空查询可能命中所有元素。
        return 0.0  # 新增代码+BrowserLocatorStage5: 返回零分；若没有这行代码，空字段可能被误判。
    if exact and left == right:  # 新增代码+BrowserLocatorStage5: 精确匹配获得最高分；若没有这行代码，exact 参数没有意义。
        return 1.0  # 新增代码+BrowserLocatorStage5: 返回满分；若没有这行代码，强匹配无法体现。
    if not exact and right in left:  # 新增代码+BrowserLocatorStage5: 包含匹配获得高分；若没有这行代码，按钮文本片段无法命中。
        return min(0.95, 0.65 + len(right) / max(len(left), 1) * 0.3)  # 新增代码+BrowserLocatorStage5: 越接近完整文本分越高；若没有这行代码，短片段和完整匹配没有差异。
    return 0.0  # 新增代码+BrowserLocatorStage5: 不匹配返回零分；若没有这行代码，候选排序会错误。


class BrowserLocatorEngine:  # 新增代码+BrowserLocatorStage5: 定位候选评分器；若没有这个类，动作执行器只能直接靠 Playwright 猜。
    def __init__(self, min_confidence: float = 0.5) -> None:  # 新增代码+BrowserLocatorStage5: 初始化最低置信度；若没有这行代码，低质量候选无法统一拦截。
        self.min_confidence = float(min_confidence)  # 新增代码+BrowserLocatorStage5: 保存置信度阈值；若没有这行代码，阈值参数不会生效。

    def find_candidates(self, observation: BrowserObservation, query: dict[str, Any]) -> list[BrowserLocator]:  # 新增代码+BrowserLocatorStage5: 从 observation 中寻找候选元素；若没有这行代码，定位引擎没有主入口。
        scored: list[BrowserLocator] = []  # 新增代码+BrowserLocatorStage5: 准备保存候选结果；若没有这行代码，函数没有返回容器。
        for element in observation.elements:  # 新增代码+BrowserLocatorStage5: 遍历页面观察里的元素；若没有这行代码，定位没有候选来源。
            if not isinstance(element, dict):  # 新增代码+BrowserLocatorStage5: 跳过坏元素；若没有这行代码，坏 JSON 会导致失败。
                continue  # 新增代码+BrowserLocatorStage5: 继续后续元素；若没有这行代码，单个坏元素会中断定位。
            locator = self._score_element(element, query)  # 新增代码+BrowserLocatorStage5: 计算单个元素得分；若没有这行代码，候选无法排序。
            if locator.confidence >= self.min_confidence:  # 新增代码+BrowserLocatorStage5: 只保留可靠候选；若没有这行代码，低置信度元素可能被误点。
                scored.append(locator)  # 新增代码+BrowserLocatorStage5: 加入候选列表；若没有这行代码，结果会丢失。
        scored.sort(key=lambda item: item.confidence, reverse=True)  # 新增代码+BrowserLocatorStage5: 按置信度降序；若没有这行代码，动作执行器可能选到次优元素。
        return scored  # 新增代码+BrowserLocatorStage5: 返回候选列表；若没有这行代码，调用方拿不到结果。

    def choose_best(self, observation: BrowserObservation, query: dict[str, Any]) -> BrowserLocator | None:  # 新增代码+BrowserLocatorStage5: 选择最佳候选；若没有这行代码，调用方需要重复取第一个。
        candidates = self.find_candidates(observation, query)  # 新增代码+BrowserLocatorStage5: 复用候选查找；若没有这行代码，best 和 list 逻辑可能分裂。
        return candidates[0] if candidates else None  # 新增代码+BrowserLocatorStage5: 有候选返回第一项，否则返回 None；若没有这行代码，空列表会越界。

    def _score_element(self, element: dict[str, Any], query: dict[str, Any]) -> BrowserLocator:  # 新增代码+BrowserLocatorStage5: 给单个元素计算定位候选；若没有这行代码，find_candidates 会变得过长。
        score = 0.0  # 新增代码+BrowserLocatorStage5: 初始化分数；若没有这行代码，后续 max 无基础值。
        reasons: list[str] = []  # 新增代码+BrowserLocatorStage5: 保存命中原因；若没有这行代码，定位不可解释。
        exact = bool(query.get("exact", False))  # 新增代码+BrowserLocatorStage5: 读取是否精确匹配；若没有这行代码，exact 参数不会生效。
        field_map = {"selector": "selector", "element_id": "element_id", "text": "text", "label": "label", "placeholder": "placeholder", "role": "role", "visual_query": "text", "near_text": "text"}  # 新增代码+BrowserLocatorStage5: 定义查询字段到元素字段映射；若没有这行代码，各字段会重复写分支。
        for query_key, element_key in field_map.items():  # 新增代码+BrowserLocatorStage5: 遍历所有文本定位字段；若没有这行代码，多策略定位不会执行。
            if query_key not in query or _text(query.get(query_key)) == "":  # 新增代码+BrowserLocatorStage5: 跳过未传字段；若没有这行代码，空查询会影响得分。
                continue  # 新增代码+BrowserLocatorStage5: 继续下一个字段；若没有这行代码，空字段会误匹配。
            if query_key in {"selector", "element_id"} and _text(element.get(element_key)) == _text(query.get(query_key)):  # 新增代码+BrowserLocatorStage5: selector/id 要精确相等；若没有这行代码，CSS 片段可能误命中。
                score = max(score, 1.0)  # 新增代码+BrowserLocatorStage5: 精确结构字段给满分；若没有这行代码，直接引用不会优先。
                reasons.append(query_key)  # 新增代码+BrowserLocatorStage5: 记录命中来源；若没有这行代码，解释缺少字段名。
                continue  # 新增代码+BrowserLocatorStage5: 结构字段匹配已完成；若没有这行代码，会继续做无意义文本评分。
            field_score = _contains_score(element.get(element_key), query.get(query_key), exact=exact)  # 新增代码+BrowserLocatorStage5: 对文本字段评分；若没有这行代码，label/text/role 查询无法命中。
            if field_score > 0:  # 新增代码+BrowserLocatorStage5: 命中时保存原因；若没有这行代码，原因列表会为空。
                score = max(score, field_score)  # 新增代码+BrowserLocatorStage5: 使用最高分作为候选置信度；若没有这行代码，多字段匹配可能被低分覆盖。
                reasons.append(query_key)  # 新增代码+BrowserLocatorStage5: 记录命中字段；若没有这行代码，定位不可解释。
        if isinstance(query.get("coordinate"), dict):  # 新增代码+BrowserLocatorStage5: 坐标定位分支；若没有这行代码，视觉坐标无法映射候选。
            coordinate_score = self._coordinate_score(element, query["coordinate"])  # 新增代码+BrowserLocatorStage5: 计算坐标距离得分；若没有这行代码，坐标定位没有量化标准。
            if coordinate_score > score:  # 新增代码+BrowserLocatorStage5: 坐标得分更高时更新；若没有这行代码，坐标点击可能被弱文本匹配压过。
                score = coordinate_score  # 新增代码+BrowserLocatorStage5: 保存坐标置信度；若没有这行代码，候选排序错误。
                reasons.append("coordinate")  # 新增代码+BrowserLocatorStage5: 记录坐标命中；若没有这行代码，原因不可解释。
        return BrowserLocator(locator_type="browser_observation", value=str(query), confidence=round(score, 4), reason=",".join(reasons), selector=_text(element.get("selector")), element_id=_text(element.get("element_id")), box=dict(element.get("box") or {"x": element.get("x", 0), "y": element.get("y", 0), "width": element.get("width", 0), "height": element.get("height", 0)}))  # 新增代码+BrowserLocatorStage5: 返回协议化候选；若没有这行代码，定位结果无法审计。

    def _coordinate_score(self, element: dict[str, Any], coordinate: dict[str, Any]) -> float:  # 新增代码+BrowserLocatorStage5: 根据鼠标坐标计算候选分；若没有这行代码，坐标定位没有复用逻辑。
        try:  # 新增代码+BrowserLocatorStage5: 捕获坏坐标；若没有这行代码，错误输入会拖垮定位。
            target_x = float(coordinate.get("x"))  # 新增代码+BrowserLocatorStage5: 读取目标 x；若没有这行代码，无法计算距离。
            target_y = float(coordinate.get("y"))  # 新增代码+BrowserLocatorStage5: 读取目标 y；若没有这行代码，无法计算距离。
            center_x = float(element.get("center_x", 0))  # 新增代码+BrowserLocatorStage5: 读取元素中心 x；若没有这行代码，距离计算没有元素坐标。
            center_y = float(element.get("center_y", 0))  # 新增代码+BrowserLocatorStage5: 读取元素中心 y；若没有这行代码，距离计算没有元素坐标。
        except (TypeError, ValueError):  # 新增代码+BrowserLocatorStage5: 坏坐标返回零分；若没有这行代码，异常会冒泡。
            return 0.0  # 新增代码+BrowserLocatorStage5: 返回零分；若没有这行代码，定位结果不稳定。
        distance = math.hypot(target_x - center_x, target_y - center_y)  # 新增代码+BrowserLocatorStage5: 计算鼠标点到元素中心距离；若没有这行代码，坐标评分无依据。
        width = max(float(element.get("width", 1) or 1), 1.0)  # 新增代码+BrowserLocatorStage5: 读取宽度并避免 0；若没有这行代码，除法可能失败。
        height = max(float(element.get("height", 1) or 1), 1.0)  # 新增代码+BrowserLocatorStage5: 读取高度并避免 0；若没有这行代码，除法可能失败。
        radius = max(width, height, 20.0)  # 新增代码+BrowserLocatorStage5: 定义容忍半径；若没有这行代码，小元素坐标会过度严格。
        return max(0.0, 1.0 - distance / (radius * 2.0))  # 新增代码+BrowserLocatorStage5: 距离越近分越高；若没有这行代码，坐标定位无法排序。
