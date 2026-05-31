"""安全并发工具编排器。"""  # 新增代码+Stage15F: 把批量工具调用的并发规则独立成模块；若没有这个文件，主循环只能继续逐个串行执行所有工具。

from __future__ import annotations  # 新增代码+Stage15F: 延迟解析类型注解；若没有这行代码，脚本模式导入顺序会更脆弱。

from concurrent.futures import ThreadPoolExecutor, as_completed  # 新增代码+Stage15F: 使用标准线程池执行安全只读工具；若没有这行代码，无法真正并发读取。
from typing import Any, Callable, Iterable  # 新增代码+Stage15F: 编排器需要通用 agent、回调和可迭代类型；若没有这行代码，接口边界不清楚。

try:  # 新增代码+Stage15F: 包运行模式下导入工具调用类型；若没有这行代码，编排器无法读取 tool_call.name 和 call_id。
    from learning_agent.core.messages import ToolCall  # 新增代码+Stage15F: 导入统一 ToolCall 类型；若没有这行代码，编排器会和主循环使用不同调用对象。
except ModuleNotFoundError as error:  # 新增代码+Stage15F: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.messages"}:  # 新增代码+Stage15F: 只允许目标包路径缺失时 fallback；若没有这行代码，core 内部真实 bug 会被误吞。
        raise  # 新增代码+Stage15F: 重新抛出真实导入错误；若没有这行代码，排查 orchestrator 问题会很困难。
    from core.messages import ToolCall  # 新增代码+Stage15F: 脚本模式下导入 ToolCall；若没有这行代码，直接执行时并发编排器无法工作。


ToolExecutorFunction = Callable[[ToolCall], str]  # 新增代码+Stage15F: 定义单个工具执行函数签名；若没有这行代码，execute_tool_calls 参数含义不清楚。


def _default_execute_one(agent: Any, tool_call: ToolCall) -> str:  # 新增代码+Stage15F: 默认复用 agent._execute_tool 执行单个工具；若没有这行代码，调用方每次都必须传 execute_one。
    return agent._execute_tool(tool_call)  # 新增代码+Stage15F: 委托真实 agent 工具执行入口；若没有这行代码，主循环无法直接使用编排器。


def _find_catalog_tool(agent: Any, tool_name: str) -> Any:  # 新增代码+Stage15F: 安全读取 agent catalog 工具元数据；若没有这行代码，fake agent 或旧对象缺方法时会崩溃。
    finder = getattr(agent, "_find_catalog_tool", None)  # 新增代码+Stage15F: 动态获取 catalog 查询函数；若没有这行代码，编排器会强依赖 LearningAgent。
    return finder(tool_name) if callable(finder) else None  # 新增代码+Stage15F: 有查询函数时返回工具元数据，否则返回 None；若没有这行代码，未知工具无法保守串行。


def is_tool_call_concurrency_safe(agent: Any, tool_call: ToolCall) -> bool:  # 新增代码+Stage15F: 判断单个工具调用是否允许并发；若没有这行代码，并发规则会散落在主循环里。
    catalog_tool = _find_catalog_tool(agent, tool_call.name)  # 新增代码+Stage15F: 读取工具元数据；若没有这行代码，无法知道工具是否只读。
    if catalog_tool is None:  # 新增代码+Stage15F: 未知工具一律保守处理；若没有这行代码，未知工具可能被错误并发。
        return False  # 新增代码+Stage15F: 未知工具不并发；若没有这行代码，副作用边界会变危险。
    is_read_only = bool(getattr(catalog_tool, "is_read_only", False))  # 新增代码+Stage15F: 读取只读标记；若没有这行代码，写入工具可能误入并发批次。
    is_concurrency_safe = bool(getattr(catalog_tool, "is_concurrency_safe", False))  # 新增代码+Stage15F: 读取并发安全标记；若没有这行代码，只读但不安全的工具会被并发。
    return is_read_only and is_concurrency_safe  # 新增代码+Stage15F: 只有两项同时为真才允许并发；若没有这行代码，安全规则不够保守。


def _execute_one_catching(tool_call: ToolCall, execute_one: ToolExecutorFunction) -> str:  # 新增代码+Stage15F: 执行单个工具并把异常转成结果文本；若没有这行代码，一个并发工具失败会中断整批。
    try:  # 新增代码+Stage15F: 捕获单工具异常；若没有这行代码，future.result 会把异常抛回编排器。
        return execute_one(tool_call)  # 新增代码+Stage15F: 调用真实单工具执行函数；若没有这行代码，编排器不会执行任何工具。
    except Exception as error:  # 新增代码+Stage15F: 把工具异常转换成可读结果；若没有这行代码，其他并发工具结果可能被丢弃。
        return f"{tool_call.name} 工具执行失败：{error}"  # 新增代码+Stage15F: 返回失败文本给模型；若没有这行代码，模型无法基于失败继续恢复。


def _execute_parallel_batch(batch: list[ToolCall], execute_one: ToolExecutorFunction, max_workers: int) -> list[str]:  # 新增代码+Stage15F: 并发执行一个安全只读批次；若没有这行代码，execute_tool_calls 会充满线程池细节。
    ordered_results: list[str] = [""] * len(batch)  # 新增代码+Stage15F: 预留按原顺序返回的结果数组；若没有这行代码，完成顺序会污染消息回填顺序。
    with ThreadPoolExecutor(max_workers=max_workers) as pool:  # 新增代码+Stage15F: 创建线程池并限制并发数；若没有这行代码，安全工具无法真正并发或可能无限开线程。
        future_to_index = {pool.submit(_execute_one_catching, tool_call, execute_one): index for index, tool_call in enumerate(batch)}  # 新增代码+Stage15F: 提交批次并记录每个 future 的原始位置；若没有这行代码，结果无法按 tool_call 顺序还原。
        for future in as_completed(future_to_index):  # 新增代码+Stage15F: 按完成顺序收集 future；若没有这行代码，慢工具会阻塞所有已完成结果的记录。
            result_index = future_to_index[future]  # 新增代码+Stage15F: 找回该 future 对应的原始位置；若没有这行代码，结果会乱序。
            ordered_results[result_index] = future.result()  # 新增代码+Stage15F: 写入对应位置的结果；若没有这行代码，成功或失败结果不会进入返回列表。
    return ordered_results  # 新增代码+Stage15F: 返回按原顺序排列的结果；若没有这行代码，主循环无法稳定回填 tool messages。


def execute_tool_calls(agent: Any, tool_calls: Iterable[ToolCall], execute_one: ToolExecutorFunction | None = None, max_concurrency: int = 3) -> list[str]:  # 新增代码+Stage15F: 批量执行工具调用并只并发安全只读工具；若没有这行代码，主循环无法利用 Stage 15D 元数据提速。
    calls = list(tool_calls)  # 新增代码+Stage15F: 固化输入顺序；若没有这行代码，生成器输入可能被多次消费或无法按索引写结果。
    if not calls:  # 新增代码+Stage15F: 空批次直接返回；若没有这行代码，空工具调用也会进入后续循环。
        return []  # 新增代码+Stage15F: 返回空结果列表；若没有这行代码，调用方需要额外处理 None。
    execute = execute_one or (lambda tool_call: _default_execute_one(agent, tool_call))  # 新增代码+Stage15F: 选择自定义执行函数或默认 agent 执行；若没有这行代码，测试和主循环无法复用同一个编排器。
    max_workers = max(1, int(max_concurrency or 1))  # 新增代码+Stage15F: 规范化并发上限且至少为 1；若没有这行代码，0 或 None 会让线程池参数非法。
    results: list[str] = [""] * len(calls)  # 新增代码+Stage15F: 预留总结果数组；若没有这行代码，后续无法按原始 tool_call 顺序填充。
    index = 0  # 新增代码+Stage15F: 当前扫描位置；若没有这行代码，while 循环无法推进。
    while index < len(calls):  # 新增代码+Stage15F: 按顺序扫描工具调用；若没有这行代码，批次不会执行。
        current_call = calls[index]  # 新增代码+Stage15F: 读取当前工具调用；若没有这行代码，无法判断是否安全并发。
        if not is_tool_call_concurrency_safe(agent, current_call):  # 新增代码+Stage15F: 非安全工具必须串行；若没有这行代码，写入、命令和未知工具可能被并发。
            results[index] = _execute_one_catching(current_call, execute)  # 新增代码+Stage15F: 串行执行当前工具并捕获异常；若没有这行代码，副作用工具不会执行或异常会中断循环。
            index += 1  # 新增代码+Stage15F: 推进到下一个工具；若没有这行代码，循环会卡住。
            continue  # 新增代码+Stage15F: 继续扫描后续工具；若没有这行代码，串行工具后会错误进入并发批次逻辑。
        batch_start = index  # 新增代码+Stage15F: 记录安全批次起点；若没有这行代码，无法把批次结果放回总结果数组。
        safe_batch: list[ToolCall] = []  # 新增代码+Stage15F: 保存连续安全只读工具；若没有这行代码，无法一次提交并发批次。
        while index < len(calls) and is_tool_call_concurrency_safe(agent, calls[index]):  # 新增代码+Stage15F: 收集连续的安全只读工具；若没有这行代码，安全工具仍会一个个串行执行。
            safe_batch.append(calls[index])  # 新增代码+Stage15F: 把当前安全工具加入批次；若没有这行代码，并发批次为空。
            index += 1  # 新增代码+Stage15F: 推进扫描位置；若没有这行代码，收集循环会卡住。
        if len(safe_batch) == 1 or max_workers == 1:  # 新增代码+Stage15F: 单个安全工具或并发上限 1 时直接串行执行；若没有这行代码，会为一个工具创建不必要线程池。
            batch_results = [_execute_one_catching(tool_call, execute) for tool_call in safe_batch]  # 新增代码+Stage15F: 串行执行小批次并捕获异常；若没有这行代码，单工具安全批次不会返回结果。
        else:  # 新增代码+Stage15F: 多个安全工具且允许并发时使用线程池；若没有这行代码，并发分支无法进入。
            batch_results = _execute_parallel_batch(safe_batch, execute, min(max_workers, len(safe_batch)))  # 新增代码+Stage15F: 并发执行安全批次并限制线程数；若没有这行代码，安全读取无法提速。
        for offset, result in enumerate(batch_results):  # 新增代码+Stage15F: 把批次结果写回总结果数组；若没有这行代码，调用方拿不到结果。
            results[batch_start + offset] = result  # 新增代码+Stage15F: 按原始位置保存结果；若没有这行代码，并发结果会乱序。
    return results  # 新增代码+Stage15F: 返回所有工具结果；若没有这行代码，主循环无法把结果回填给模型。
