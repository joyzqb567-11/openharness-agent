"""运行结果事件 helper，用于保存最终回答等验收关键字段。"""  # 新增代码+ObservabilitySplit: 说明本模块负责运行结果事件；若没有这行代码，最终回答验收字段会继续散在入口函数里。
from __future__ import annotations  # 新增代码+ObservabilitySplit: 允许类型注解延迟解析；若没有这行代码，类型提示在部分运行顺序下可能提前求值。

from typing import Any  # 新增代码+ObservabilitySplit: 标注事件 payload 类型；若没有这行代码，返回值结构不容易被维护者理解。


def build_final_answer_event_payload(answer: str) -> dict[str, Any]:  # 新增代码+ObservabilitySplit: 生成 final_answer_printed 事件 payload；若没有这行代码，入口函数仍要手写最终回答验收结构。
    return {  # 新增代码+ObservabilitySplit: 返回包含完整回答和预览的 payload；若没有这行代码，控制器无法稳定读取最终答案。
        "answer_length": len(answer),  # 新增代码+ObservabilitySplit: 记录完整回答长度；若没有这行代码，外部 agent 无法判断预览是否被截断。
        "answer_preview": answer[:500],  # 新增代码+ObservabilitySplit: 保留短预览方便快速查看 result.json；若没有这行代码，排查时必须打开完整回答。
        "answer_text": answer,  # 新增代码+ObservabilitySplit: 保存完整最终回答给验收断言使用；若没有这行代码，长回答后半段的关键字段会被截断误判。
    }  # 新增代码+ObservabilitySplit: 结束最终回答 payload；若没有这行代码，Python 字典语法不完整。
