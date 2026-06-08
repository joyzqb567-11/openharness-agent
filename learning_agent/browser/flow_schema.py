"""浏览器流程 schema，把多阶段网站任务解析成可 checkpoint 的计划。"""  # 新增代码+BrowserFlowStage8: 说明本模块负责流程输入协议；若没有这行代码，flow 边界不清楚。

from __future__ import annotations  # 新增代码+BrowserFlowStage8: 延迟解析类型注解；若没有这行代码，类型引用更脆弱。

from dataclasses import dataclass, field  # 新增代码+BrowserFlowStage8: 用 dataclass 定义流程计划；若没有这行代码，流程对象需要手写构造器。
from typing import Any  # 新增代码+BrowserFlowStage8: 流程参数来自 JSON；若没有这行代码，类型边界不清楚。


@dataclass  # 新增代码+BrowserFlowStage8: 自动生成阶段构造器；若没有这行代码，阶段对象初始化冗长。
class BrowserFlowStage:  # 新增代码+BrowserFlowStage8: 表示流程里的单个阶段；若没有这个类，checkpoint 无法按阶段命名。
    name: str  # 新增代码+BrowserFlowStage8: 阶段名称；若没有这行代码，失败和恢复报告不知道卡在哪一步。
    tool: str  # 新增代码+BrowserFlowStage8: 阶段要调用的浏览器工具；若没有这行代码，流程无法执行动作。
    arguments: dict[str, Any] = field(default_factory=dict)  # 新增代码+BrowserFlowStage8: 阶段工具参数；若没有这行代码，工具没有输入。
    expect: dict[str, Any] = field(default_factory=dict)  # 新增代码+BrowserFlowStage8: 阶段期望断言；若没有这行代码，复杂流程缺少阶段性验收。


@dataclass  # 新增代码+BrowserFlowStage8: 自动生成计划构造器；若没有这行代码，流程对象初始化冗长。
class BrowserFlowPlan:  # 新增代码+BrowserFlowStage8: 表示完整浏览器流程；若没有这个类，resume/checkpoint 没有统一对象。
    flow_id: str  # 新增代码+BrowserFlowStage8: 流程 id；若没有这行代码，checkpoint 文件无法稳定命名。
    stages: list[BrowserFlowStage]  # 新增代码+BrowserFlowStage8: 阶段列表；若没有这行代码，流程没有执行内容。
    continue_on_error: bool = False  # 新增代码+BrowserFlowStage8: 失败是否继续；若没有这行代码，运行时无法表达容错策略。


def parse_browser_flow(payload: dict[str, Any]) -> BrowserFlowPlan:  # 新增代码+BrowserFlowStage8: 把 JSON 输入解析成流程计划；若没有这行代码，browser_flow_run 会继续处理松散字典。
    if not isinstance(payload, dict):  # 新增代码+BrowserFlowStage8: 顶层必须是对象；若没有这行代码，坏输入会触发难懂异常。
        raise ValueError("browser flow payload 必须是对象。")  # 新增代码+BrowserFlowStage8: 抛出清楚错误；若没有这行代码，用户不知道格式要求。
    flow_id = str(payload.get("flow_id") or payload.get("name") or "browser_flow").strip()  # 新增代码+BrowserFlowStage8: 读取流程 id 并给默认值；若没有这行代码，checkpoint 没有文件名。
    raw_stages = payload.get("stages")  # 新增代码+BrowserFlowStage8: 读取阶段列表；若没有这行代码，流程没有输入。
    if not isinstance(raw_stages, list) or not raw_stages:  # 新增代码+BrowserFlowStage8: 阶段列表必须非空；若没有这行代码，空流程可能假装成功。
        raise ValueError("browser flow stages 必须是非空列表。")  # 新增代码+BrowserFlowStage8: 抛出清楚错误；若没有这行代码，用户不知道哪里错。
    stages: list[BrowserFlowStage] = []  # 新增代码+BrowserFlowStage8: 准备保存解析后的阶段；若没有这行代码，函数没有容器。
    for index, raw_stage in enumerate(raw_stages, 1):  # 新增代码+BrowserFlowStage8: 按顺序遍历阶段；若没有这行代码，流程顺序无法保持。
        if not isinstance(raw_stage, dict):  # 新增代码+BrowserFlowStage8: 每个阶段必须是对象；若没有这行代码，坏阶段会触发属性错误。
            raise ValueError(f"browser flow 第 {index} 个阶段必须是对象。")  # 新增代码+BrowserFlowStage8: 报告坏阶段位置；若没有这行代码，用户难以修复。
        name = str(raw_stage.get("name") or f"stage-{index}").strip()  # 新增代码+BrowserFlowStage8: 读取阶段名；若没有这行代码，checkpoint 不能按人类名称展示。
        tool = str(raw_stage.get("tool") or "").strip()  # 新增代码+BrowserFlowStage8: 读取工具名；若没有这行代码，阶段无法执行。
        if not tool:  # 新增代码+BrowserFlowStage8: 工具名不能为空；若没有这行代码，运行时会调用空工具。
            raise ValueError(f"browser flow 阶段 {name} 缺少 tool。")  # 新增代码+BrowserFlowStage8: 抛出清楚错误；若没有这行代码，用户不知道缺哪个字段。
        arguments = raw_stage.get("arguments", {})  # 新增代码+BrowserFlowStage8: 读取工具参数；若没有这行代码，阶段工具没有输入。
        expect = raw_stage.get("expect", {})  # 新增代码+BrowserFlowStage8: 读取阶段断言；若没有这行代码，阶段验收无法表达。
        stages.append(BrowserFlowStage(name=name, tool=tool, arguments=dict(arguments) if isinstance(arguments, dict) else {}, expect=dict(expect) if isinstance(expect, dict) else {}))  # 新增代码+BrowserFlowStage8: 添加规范阶段对象；若没有这行代码，计划阶段为空。
    return BrowserFlowPlan(flow_id=flow_id, stages=stages, continue_on_error=bool(payload.get("continue_on_error", False)))  # 新增代码+BrowserFlowStage8: 返回完整流程计划；若没有这行代码，调用方拿不到结果。
