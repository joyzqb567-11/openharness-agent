"""全局流式工具执行器。"""  # 新增代码+Phase4StreamingExecutor: 说明本模块统一包装所有工具执行事件；若没有这行代码，维护者不知道这里是全局工具生命周期入口。
from __future__ import annotations  # 新增代码+Phase4StreamingExecutor: 延迟解析类型注解；若没有这行代码，回调类型在脚本模式下更容易受导入顺序影响。
from collections.abc import Iterable  # 新增代码+Phase4StreamingExecutor: 判断工具结果是否为分段可迭代对象；若没有这行代码，流式 chunk 无法识别。
from dataclasses import dataclass, field  # 新增代码+Phase4StreamingExecutor: 用 dataclass 定义轻量事件对象；若没有这行代码，事件 payload 需要手写大量样板。
from typing import Any, Callable  # 新增代码+Phase4StreamingExecutor: 执行器需要通用工具调用、handler 和 event sink 类型；若没有这行代码，接口边界不清楚。

try:  # 新增代码+Phase4StreamingExecutor: 包运行模式下导入 ToolCall；若没有这行代码，执行器无法读取工具名和 call_id。
    from learning_agent.core.messages import ToolCall  # 新增代码+Phase4StreamingExecutor: 使用项目统一工具调用对象；若没有这行代码，执行器会和主循环类型割裂。
except ModuleNotFoundError as error:  # 新增代码+Phase4StreamingExecutor: 捕获直接运行脚本时包路径不可用；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.messages"}:  # 新增代码+Phase4StreamingExecutor: 只允许目标包路径缺失时 fallback；若没有这行代码，core 内部真实 bug 会被误吞。
        raise  # 新增代码+Phase4StreamingExecutor: 重新抛出真实导入错误；若没有这行代码，排查方向会被 fallback 误导。
    from core.messages import ToolCall  # 新增代码+Phase4StreamingExecutor: 脚本模式下导入 ToolCall；若没有这行代码，直接运行时执行器不可用。

ToolResultHandler = Callable[[ToolCall], Any]  # 新增代码+Phase4StreamingExecutor: 定义单工具 handler 签名；若没有这行代码，执行器参数含义不清楚。
ToolEventSink = Callable[[dict[str, Any]], None]  # 新增代码+Phase4StreamingExecutor: 定义事件接收函数签名；若没有这行代码，调用方不知道 sink 收到什么。

@dataclass  # 新增代码+Phase4StreamingExecutor: 自动生成事件初始化方法；若没有这行代码，每种事件都要手写构造器。
class ToolExecutionEvent:  # 新增代码+Phase4StreamingExecutor: 表示全局工具执行生命周期事件；若没有这个类，事件只能用松散字典传来传去。
    event_type: str  # 新增代码+Phase4StreamingExecutor: 保存事件类型 started/chunk/completed/failed；若没有这行代码，UI 无法判断事件阶段。
    tool_name: str  # 新增代码+Phase4StreamingExecutor: 保存工具名；若没有这行代码，事件无法按工具过滤。
    call_id: str  # 新增代码+Phase4StreamingExecutor: 保存模型 tool_call id；若没有这行代码，事件无法和本次调用对应。
    chunk_index: int = 0  # 新增代码+Phase4StreamingExecutor: 保存分段序号；若没有这行代码，chunk 事件无法稳定排序。
    chunk: str = ""  # 新增代码+Phase4StreamingExecutor: 保存本次分段文本；若没有这行代码，终端 UI 看不到增量内容。
    result_text: str = ""  # 新增代码+Phase4StreamingExecutor: 保存完成时的最终文本；若没有这行代码，completed 事件缺少完整结果摘要。
    error: str = ""  # 新增代码+Phase4StreamingExecutor: 保存失败原因；若没有这行代码，failed 事件无法解释问题。
    metadata: dict[str, Any] = field(default_factory=dict)  # 新增代码+Phase4StreamingExecutor: 保存扩展信息；若没有这行代码，后续无法无破坏扩展事件。
    def to_payload(self) -> dict[str, Any]:  # 新增代码+Phase4StreamingExecutor: 把事件对象转成可落盘字典；若没有这段函数，调用方需要重复拼 payload。
        return {  # 新增代码+Phase4StreamingExecutor: 返回新的 payload 字典；若没有这行代码，事件无法传给 observation 或测试 sink。
            "event_type": self.event_type,  # 新增代码+Phase4StreamingExecutor: 输出事件类型；若没有这行代码，接收方无法判断阶段。
            "tool_name": self.tool_name,  # 新增代码+Phase4StreamingExecutor: 输出工具名；若没有这行代码，事件身份不完整。
            "call_id": self.call_id,  # 新增代码+Phase4StreamingExecutor: 输出调用 id；若没有这行代码，事件无法关联模型请求。
            "chunk_index": self.chunk_index,  # 新增代码+Phase4StreamingExecutor: 输出 chunk 序号；若没有这行代码，分段排序不稳定。
            "chunk": self.chunk,  # 新增代码+Phase4StreamingExecutor: 输出 chunk 文本；若没有这行代码，流式显示没有内容。
            "result_text": self.result_text,  # 新增代码+Phase4StreamingExecutor: 输出最终文本；若没有这行代码，completed 事件缺少结果。
            "error": self.error,  # 新增代码+Phase4StreamingExecutor: 输出错误文本；若没有这行代码，failed 事件缺少原因。
            "metadata": dict(self.metadata),  # 新增代码+Phase4StreamingExecutor: 输出元数据副本；若没有这行代码，调用方可能污染事件内部状态。
        }  # 新增代码+Phase4StreamingExecutor: 结束 payload 字典；若没有这行代码，Python 语法不完整。

class StreamingToolExecutor:  # 新增代码+Phase4StreamingExecutor: 统一执行单个工具并发出生命周期事件；若没有这个类，全局工具层仍没有 ClaudeCode 式执行器。
    def __init__(self, event_sink: ToolEventSink | None = None) -> None:  # 新增代码+Phase4StreamingExecutor: 初始化可选事件接收器；若没有这行代码，执行器无法把事件交给 UI/日志。
        self.event_sink = event_sink  # 新增代码+Phase4StreamingExecutor: 保存事件 sink；若没有这行代码，后续 emit 不知道发到哪里。
    def execute(self, tool_call: ToolCall, handler: ToolResultHandler) -> str:  # 新增代码+Phase4StreamingExecutor: 执行单个工具并返回最终文本；若没有这段函数，调用方无法使用执行器。
        self._emit("tool_started", tool_call)  # 新增代码+Phase4StreamingExecutor: 执行前发 started；若没有这行代码，终端 UI 看不到工具开始。
        try:  # 新增代码+Phase4StreamingExecutor: 捕获 handler 成功或失败；若没有这行代码，异常会跳过 failed 事件。
            raw_result = handler(tool_call)  # 新增代码+Phase4StreamingExecutor: 调用真实工具 handler；若没有这行代码，执行器只会发事件不执行工具。
            result_text = self._consume_result(tool_call, raw_result)  # 新增代码+Phase4StreamingExecutor: 消费普通或分段结果；若没有这行代码，生成器会被原样返回。
        except Exception as error:  # 新增代码+Phase4StreamingExecutor: 捕获工具异常；若没有这行代码，单工具失败会中断整批编排。
            error_text = str(error)  # 新增代码+Phase4StreamingExecutor: 把异常转成文本；若没有这行代码，failed 事件缺少可读原因。
            self._emit("tool_failed", tool_call, error=error_text)  # 新增代码+Phase4StreamingExecutor: 发出失败事件；若没有这行代码，状态 UI 可能一直停在 running。
            return f"{tool_call.name} 工具执行失败：{error_text}"  # 新增代码+Phase4StreamingExecutor: 返回失败文本给模型；若没有这行代码，模型无法基于错误继续恢复。
        self._emit("tool_completed", tool_call, result_text=result_text)  # 新增代码+Phase4StreamingExecutor: 发出完成事件；若没有这行代码，状态 UI 不知道工具已结束。
        return result_text  # 新增代码+Phase4StreamingExecutor: 返回最终工具文本；若没有这行代码，主循环无法回填 tool message。
    def _consume_result(self, tool_call: ToolCall, raw_result: Any) -> str:  # 新增代码+Phase4StreamingExecutor: 把工具返回值统一转成文本；若没有这段函数，字符串、字节、dict 和生成器规则会混在 execute 里。
        if raw_result is None:  # 新增代码+Phase4StreamingExecutor: 兼容无返回值工具；若没有这行代码，None 会变成误导性的 "None"。
            return ""  # 新增代码+Phase4StreamingExecutor: 无结果时返回空文本；若没有这行代码，模型会收到多余文本。
        if isinstance(raw_result, bytes):  # 新增代码+Phase4StreamingExecutor: 字节结果需要解码；若没有这行代码，用户会看到 Python bytes 表示。
            return raw_result.decode("utf-8", errors="replace")  # 新增代码+Phase4StreamingExecutor: 用 UTF-8 容错解码；若没有这行代码，非 UTF-8 片段可能让执行器崩溃。
        if isinstance(raw_result, (str, dict)) or not isinstance(raw_result, Iterable):  # 新增代码+Phase4StreamingExecutor: 字符串、字典和非迭代对象按普通结果处理；若没有这行代码，字符串会被拆成单字 chunk。
            return str(raw_result)  # 新增代码+Phase4StreamingExecutor: 返回普通文本表示；若没有这行代码，普通工具结果无法回填。
        result_parts: list[str] = []  # 新增代码+Phase4StreamingExecutor: 保存所有 chunk 文本；若没有这行代码，最终结果无法拼接。
        chunk_index = 0  # 新增代码+Phase4StreamingExecutor: 初始化 chunk 序号；若没有这行代码，事件无法从 1 开始编号。
        for raw_chunk in raw_result:  # 新增代码+Phase4StreamingExecutor: 遍历流式分段；若没有这行代码，生成器不会被消费。
            chunk_index += 1  # 新增代码+Phase4StreamingExecutor: 增加当前分段序号；若没有这行代码，所有 chunk 序号会相同。
            chunk_text = "" if raw_chunk is None else str(raw_chunk)  # 新增代码+Phase4StreamingExecutor: 把分段转成文本；若没有这行代码，None 或对象 chunk 不稳定。
            result_parts.append(chunk_text)  # 新增代码+Phase4StreamingExecutor: 保存分段用于最终拼接；若没有这行代码，completed 结果会缺内容。
            self._emit("tool_result_chunk", tool_call, chunk_index=chunk_index, chunk=chunk_text)  # 新增代码+Phase4StreamingExecutor: 发出分段事件；若没有这行代码，终端 UI 看不到实时进度。
        return "".join(result_parts)  # 新增代码+Phase4StreamingExecutor: 返回拼接后的完整文本；若没有这行代码，模型只会看到空结果。
    def _emit(self, event_type: str, tool_call: ToolCall, chunk_index: int = 0, chunk: str = "", result_text: str = "", error: str = "") -> None:  # 新增代码+Phase4StreamingExecutor: 统一发事件；若没有这段函数，每个事件分支会重复构造 payload。
        if self.event_sink is None:  # 新增代码+Phase4StreamingExecutor: 没有事件接收器时静默跳过；若没有这行代码，默认使用会因 None 调用失败。
            return  # 新增代码+Phase4StreamingExecutor: 直接返回保持无 sink 模式可用；若没有这行代码，后续仍会尝试调用 None。
        event = ToolExecutionEvent(event_type=event_type, tool_name=tool_call.name, call_id=tool_call.call_id, chunk_index=chunk_index, chunk=chunk, result_text=result_text, error=error)  # 新增代码+Phase4StreamingExecutor: 构造标准事件对象；若没有这行代码，sink 收不到统一字段。
        self.event_sink(event.to_payload())  # 新增代码+Phase4StreamingExecutor: 把 payload 交给调用方；若没有这行代码，事件不会落盘或显示。

def execute_tool_call_with_streaming(tool_call: ToolCall, handler: ToolResultHandler, event_sink: ToolEventSink | None = None) -> str:  # 新增代码+Phase4StreamingExecutor: 提供函数式便捷入口；若没有这段函数，orchestrator 和测试都要手动创建执行器。
    executor = StreamingToolExecutor(event_sink=event_sink)  # 新增代码+Phase4StreamingExecutor: 创建带 sink 的执行器；若没有这行代码，函数入口无法复用类实现。
    return executor.execute(tool_call, handler)  # 新增代码+Phase4StreamingExecutor: 执行工具并返回文本；若没有这行代码，便捷入口没有实际行为。
