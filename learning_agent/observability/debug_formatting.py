"""把调试事件转换成适合初学者阅读的 Markdown 日志。"""  # 新增代码+AgentPySplitPhase7: 说明本模块专门负责可读调试日志；若没有这行代码，用户不容易知道日志排版逻辑已经从 agent.py 拆出。
from __future__ import annotations  # 新增代码+AgentPySplitPhase7: 延迟解析类型注解；若没有这行代码，部分类型在运行早期可能提前求值导致兼容性变差。

import json  # 新增代码+AgentPySplitPhase7: 用于把工具参数和模型工具调用格式化成 JSON；若没有这行代码，可读日志里的结构数据会变成难读的 Python repr。
from pathlib import Path  # 新增代码+AgentPySplitPhase7: 用 Path 统一处理日志文件路径；若没有这行代码，Windows 路径处理会散落回 agent.py。
from typing import Any, Callable  # 修改代码+AgentPySplitPhase15B7: 用 Any 标注通用数据并用 Callable 标注 debug 写入回调；若没有 Callable，run_events 删除旧写日志薄包装后接口意图不清楚。

try:  # 修改代码+AgentPySplitPhase15B7: 包运行模式下导入 JSONL 调试日志 helper；若没有这段导入，debug_formatting.py 无法完整承接 agent.py 的写日志职责。
    from learning_agent.observability.debug_log import append_debug_event_record, build_debug_event_record  # 修改代码+AgentPySplitPhase15B7: 导入构造和追加 JSONL 调试事件的公开函数；若没有这行代码，debug_event_writer 只能写 Markdown 而丢掉 JSONL。
except ModuleNotFoundError as error:  # 修改代码+AgentPySplitPhase15B7: 捕获 start_oauth_agent.bat 直接脚本模式下包名不可用；若没有这行代码，真实可见终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.observability", "learning_agent.observability.debug_log"}:  # 修改代码+AgentPySplitPhase15B7: 只允许目标包路径缺失时 fallback；若没有这行代码，debug_log 内部真实 bug 会被误吞。
        raise  # 修改代码+AgentPySplitPhase15B7: 重新抛出非路径问题；若没有这行代码，真实导入错误会被伪装成脚本模式问题。
    from observability.debug_log import append_debug_event_record, build_debug_event_record  # 修改代码+AgentPySplitPhase15B7: 脚本模式下导入 JSONL 调试日志 helper；若没有这行代码，bat 入口删除 agent.py 写日志薄包装后会找不到实现。


def write_debug_event(debug_enabled: bool, debug_log_path: Path, debug_readable_log_path: Path, debug_latest_run_path: Path, *, run_id: str, event: str, payload: dict[str, Any], turn: int | None = None) -> None:  # 修改代码+AgentPySplitPhase15B7: 函数段开始，统一写 JSONL 调试事件和 Markdown 可读日志；若没有这段函数，agent.py 删除 `_write_debug_event` 后没有公开承接入口。
    if not debug_enabled:  # 修改代码+AgentPySplitPhase15B7: 如果用户关闭了调试日志就不写文件；若没有这行代码，关闭 debug 后仍会产生日志副作用。
        return  # 修改代码+AgentPySplitPhase15B7: 关闭 debug 时直接返回；若没有这行代码，下面仍会构造和写入日志。
    record = build_debug_event_record(run_id=run_id, event=event, payload=payload, turn=turn)  # 修改代码+AgentPySplitPhase15B7: 构造统一 JSONL 调试记录；若没有这行代码，JSONL 和 Markdown 日志会缺少同一份事件事实。
    try:  # 修改代码+AgentPySplitPhase15B7: 捕获 JSONL 写入失败，避免非核心日志影响主流程；若没有这行代码，磁盘或权限问题会打断 agent 回答。
        append_debug_event_record(Path(debug_log_path), record)  # 修改代码+AgentPySplitPhase15B7: 把结构化事件追加到 debug JSONL；若没有这行代码，旧调试回放文件不会更新。
    except OSError:  # 修改代码+AgentPySplitPhase15B7: 处理目录、权限、磁盘等写入异常；若没有这行代码，日志问题会冒泡到主循环。
        return  # 修改代码+AgentPySplitPhase15B7: JSONL 写入失败时跳过本条日志；若没有这行代码，agent 会因为日志失败停止工作。
    write_readable_debug_event(record, Path(debug_readable_log_path), Path(debug_latest_run_path))  # 修改代码+AgentPySplitPhase15B7: 同步写入 Markdown 可读日志；若没有这行代码，用户无法继续看 latest_run_readable.md。
# 修改代码+AgentPySplitPhase15B7: 函数段结束，write_debug_event 到此结束；若没有这个边界说明，用户不容易看出完整 debug 写入职责已迁到 observability。


def debug_event_writer(debug_enabled: bool, debug_log_path: Path, debug_readable_log_path: Path, debug_latest_run_path: Path) -> Callable[..., None]:  # 修改代码+AgentPySplitPhase15B7: 函数段开始，生成 run_events 可复用的 debug 写入回调；若没有这段函数，run_events 每次写日志都要重复传四个路径参数。
    def write(*, run_id: str, event: str, payload: dict[str, Any], turn: int | None = None) -> None:  # 修改代码+AgentPySplitPhase15B7: 定义真正被主循环调用的闭包；若没有这行代码，外层无法把路径状态封装起来。
        write_debug_event(debug_enabled, debug_log_path, debug_readable_log_path, debug_latest_run_path, run_id=run_id, event=event, payload=payload, turn=turn)  # 修改代码+AgentPySplitPhase15B7: 调用公开写入函数并传入固定路径；若没有这行代码，闭包不会真正写日志。
    return write  # 修改代码+AgentPySplitPhase15B7: 返回简洁回调给 run_events；若没有这行代码，主循环拿不到新的 debug 写入入口。
# 修改代码+AgentPySplitPhase15B7: 函数段结束，debug_event_writer 到此结束；若没有这个边界说明，用户不容易看出这是替代 agent.py 旧 debug 薄包装的入口。


def model_message_to_debug_dict(model_message: Any) -> dict[str, Any]:  # 新增代码+AgentPySplitPhase7: 函数段开始，把模型返回对象转成 JSONL 可记录的字典；若没有这段函数，agent.py 仍要保存模型调试字段转换细节。
    return {  # 新增代码+AgentPySplitPhase7: 返回结构化调试数据；若没有这行代码，调用方拿不到可写入 JSONL 的模型响应内容。
        "decision_note": model_message.decision_note,  # 新增代码+AgentPySplitPhase7: 记录模型给人看的决策说明；若没有这行代码，初学者看不懂模型为什么调用工具。
        "text": model_message.text,  # 新增代码+AgentPySplitPhase7: 记录模型文本回答；若没有这行代码，调试日志无法复盘模型说了什么。
        "tool_calls": [tool_call_to_debug_dict(call) for call in model_message.tool_calls],  # 新增代码+AgentPySplitPhase7: 记录模型请求的所有工具调用；若没有这行代码，工具循环在日志里会断链。
    }  # 新增代码+AgentPySplitPhase7: 调试字典结束；若没有这行代码，Python 字典语法不完整。
# 新增代码+AgentPySplitPhase7: 函数段结束，model_message_to_debug_dict 到此结束；若没有这行注释，用户不容易看出模型消息转换边界。


def tool_call_to_debug_dict(tool_call: Any) -> dict[str, Any]:  # 新增代码+AgentPySplitPhase7: 函数段开始，把工具调用对象转成 JSONL 可记录字典；若没有这段函数，agent.py 仍要保存工具调用字段转换细节。
    return {  # 新增代码+AgentPySplitPhase7: 返回工具调用调试数据；若没有这行代码，调用方拿不到工具名、参数和调用编号。
        "tool_name": tool_call.name,  # 新增代码+AgentPySplitPhase7: 记录工具名称；若没有这行代码，用户无法知道模型到底选了哪个工具。
        "arguments": tool_call.arguments,  # 新增代码+AgentPySplitPhase7: 记录模型传给工具的参数；若没有这行代码，排查工具行为时缺少输入证据。
        "call_id": tool_call.call_id,  # 新增代码+AgentPySplitPhase7: 记录工具调用编号；若没有这行代码，工具调用和工具结果不容易对应。
    }  # 新增代码+AgentPySplitPhase7: 工具调用字典结束；若没有这行代码，Python 字典语法不完整。
# 新增代码+AgentPySplitPhase7: 函数段结束，tool_call_to_debug_dict 到此结束；若没有这行注释，用户不容易看出工具调用转换边界。


def write_readable_debug_event(record: dict[str, Any], debug_readable_log_path: Path, debug_latest_run_path: Path) -> None:  # 新增代码+AgentPySplitPhase7: 函数段开始，把一条结构化事件写入两个 Markdown 可读日志；若没有这段函数，agent.py 仍要负责文件写入和排版。
    readable_text = format_readable_debug_event(record)  # 新增代码+AgentPySplitPhase7: 先把事件格式化成 Markdown 片段；若没有这行代码，后面只能写入机器 JSON 而不是人能读的内容。
    if not readable_text:  # 新增代码+AgentPySplitPhase7: 如果当前事件不需要展示到可读日志；若没有这行代码，空字符串也会触发无意义文件写入。
        return  # 新增代码+AgentPySplitPhase7: 直接跳过无内容事件；若没有这行代码，未知事件会污染日志文件。
    readable_path = Path(debug_readable_log_path)  # 新增代码+AgentPySplitPhase7: 统一转换为 Path 对象；若没有这行代码，调用方传字符串时路径操作会不稳定。
    latest_path = Path(debug_latest_run_path)  # 新增代码+AgentPySplitPhase7: 统一转换最新一轮日志路径；若没有这行代码，latest 文件写入规则会依赖调用方类型。
    try:  # 新增代码+AgentPySplitPhase7: 捕获 Markdown 日志写入失败；若没有这行代码，磁盘或权限问题会打断 agent 主流程。
        readable_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+AgentPySplitPhase7: 确保 debug_logs 文件夹存在；若没有这行代码，首次写日志会因目录不存在失败。
        if record.get("event") == "user_input":  # 新增代码+AgentPySplitPhase7: 用户输入表示新一轮开始；若没有这行代码，latest_run_readable.md 会混入历史轮次。
            latest_path.write_text("", encoding="utf-8")  # 新增代码+AgentPySplitPhase7: 清空 latest 日志只保留最新一轮；若没有这行代码，用户每次打开都会看到旧记录。
        with readable_path.open("a", encoding="utf-8") as file:  # 新增代码+AgentPySplitPhase7: 追加打开长期可读日志；若没有这行代码，历史运行记录无法持续保存。
            file.write(readable_text)  # 新增代码+AgentPySplitPhase7: 写入当前 Markdown 片段；若没有这行代码，本事件不会出现在长期日志里。
        with latest_path.open("a", encoding="utf-8") as file:  # 新增代码+AgentPySplitPhase7: 追加打开最新一轮日志；若没有这行代码，用户无法快速查看最近一次流程。
            file.write(readable_text)  # 新增代码+AgentPySplitPhase7: 写入当前 Markdown 片段；若没有这行代码，latest 日志会缺少当前事件。
    except OSError:  # 新增代码+AgentPySplitPhase7: 捕获路径、权限、磁盘等写入错误；若没有这行代码，调试日志问题会影响 agent 回答。
        return  # 新增代码+AgentPySplitPhase7: 静默跳过日志失败；若没有这行代码，非核心日志功能可能让主任务失败。
# 新增代码+AgentPySplitPhase7: 函数段结束，write_readable_debug_event 到此结束；若没有这行注释，用户不容易看出可读日志落盘边界。


def format_readable_debug_event(record: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase7: 函数段开始，把单个调试事件转成中文 Markdown 片段；若没有这段函数，用户只能看机器 JSONL。
    event = str(record.get("event", ""))  # 新增代码+AgentPySplitPhase7: 读取事件类型；若没有这行代码，无法决定用哪种 Markdown 模板。
    time_text = str(record.get("time", ""))  # 新增代码+AgentPySplitPhase7: 读取事件时间；若没有这行代码，可读日志缺少运行时间线索。
    run_id = str(record.get("run_id", ""))  # 新增代码+AgentPySplitPhase7: 读取运行编号；若没有这行代码，Markdown 记录不容易和 JSONL 对照。
    turn = record.get("turn")  # 新增代码+AgentPySplitPhase7: 读取模型调用轮次；若没有这行代码，多轮工具循环不容易定位。
    payload = record.get("payload", {})  # 新增代码+AgentPySplitPhase7: 读取事件主体内容；若没有这行代码，格式化函数没有输入数据。
    if not isinstance(payload, dict):  # 新增代码+AgentPySplitPhase7: 防御 payload 不是字典的异常情况；若没有这行代码，后续 get 调用可能崩溃。
        payload = {"value": payload}  # 新增代码+AgentPySplitPhase7: 把异常 payload 包成字典；若没有这行代码，日志格式化不够稳。
    if event == "user_input":  # 新增代码+AgentPySplitPhase7: 用户输入事件是一轮日志开头；若没有这行代码，用户输入不会显示在 Markdown 里。
        return format_readable_user_input(time_text=time_text, run_id=run_id, payload=payload)  # 新增代码+AgentPySplitPhase7: 返回运行标题和用户输入区块；若没有这行代码，一轮运行没有入口说明。
    if event == "initial_messages":  # 新增代码+AgentPySplitPhase7: 初始消息事件包含系统提示词、记忆和工具；若没有这行代码，用户看不到模型开局上下文。
        return format_readable_initial_messages(payload=payload)  # 新增代码+AgentPySplitPhase7: 返回系统/用户/工具区块；若没有这行代码，初始上下文不会进入可读日志。
    if event == "model_request":  # 新增代码+AgentPySplitPhase7: 模型请求事件表示一轮模型调用开始；若没有这行代码，用户看不到模型调用轮次。
        return format_readable_model_request(turn=turn, payload=payload)  # 新增代码+AgentPySplitPhase7: 返回模型调用摘要；若没有这行代码，messages 数量和工具面不会显示。
    if event == "model_response":  # 新增代码+AgentPySplitPhase7: 模型响应事件包含文本和工具计划；若没有这行代码，用户看不到模型选择。
        return format_readable_model_response(turn=turn, payload=payload)  # 新增代码+AgentPySplitPhase7: 返回模型输出区块；若没有这行代码，模型返回不会进入 Markdown。
    if event == "tool_call":  # 新增代码+AgentPySplitPhase7: 工具调用事件表示模型选择了具体工具；若没有这行代码，工具请求不会显示。
        return format_readable_tool_call(turn=turn, payload=payload)  # 新增代码+AgentPySplitPhase7: 返回工具名和参数区块；若没有这行代码，用户无法复盘工具输入。
    if event == "tool_result":  # 新增代码+AgentPySplitPhase7: 工具结果事件表示工具执行完成；若没有这行代码，工具返回内容不会显示。
        return format_readable_tool_result(payload=payload)  # 新增代码+AgentPySplitPhase7: 返回工具结果区块；若没有这行代码，模型看到的工具输出无法复盘。
    if event == "final_answer":  # 新增代码+AgentPySplitPhase7: 最终回答事件表示本轮结束；若没有这行代码，用户看不到最终答案区块。
        return format_readable_final_answer(payload=payload)  # 新增代码+AgentPySplitPhase7: 返回最终回答区块；若没有这行代码，可读日志没有收尾。
    if event == "safety_stop":  # 新增代码+AgentPySplitPhase7: 安全停止事件表示达到循环上限；若没有这行代码，停止原因不会显示。
        return format_readable_safety_stop(payload=payload)  # 新增代码+AgentPySplitPhase7: 返回安全停止区块；若没有这行代码，用户不容易知道 agent 为什么停。
    return ""  # 新增代码+AgentPySplitPhase7: 未知事件暂不写 Markdown；若没有这行代码，函数没有稳定返回值。
# 新增代码+AgentPySplitPhase7: 函数段结束，format_readable_debug_event 到此结束；若没有这行注释，用户不容易看出事件分发边界。


def format_readable_user_input(time_text: str, run_id: str, payload: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase7: 函数段开始，格式化一轮运行开头和用户输入；若没有这段函数，用户输入展示模板会散落在分发函数里。
    return (  # 新增代码+AgentPySplitPhase7: 返回 Markdown 标题、运行信息和用户输入代码块；若没有这行代码，函数无法输出文本。
        f"# Learning Agent 调试记录\n\n"  # 新增代码+AgentPySplitPhase7: 一级标题方便记事本定位；若没有这行代码，多轮日志开头不明显。
        f"运行时间：{time_text}\n\n"  # 新增代码+AgentPySplitPhase7: 显示本轮开始时间；若没有这行代码，用户不知道这次日志是什么时候生成的。
        f"运行编号：`{run_id}`\n\n"  # 新增代码+AgentPySplitPhase7: 显示 run_id；若没有这行代码，Markdown 和 JSONL 难以互相对照。
        "## 用户输入\n\n"  # 新增代码+AgentPySplitPhase7: 用户输入区块标题；若没有这行代码，用户原始 prompt 不容易被找到。
        f"{markdown_code_block('text', str(payload.get('text', '')))}"  # 新增代码+AgentPySplitPhase7: 用代码块展示原始用户输入；若没有这行代码，长文本会挤成一行。
    )  # 新增代码+AgentPySplitPhase7: Markdown 片段结束；若没有这行代码，Python 返回表达式无法闭合。
# 新增代码+AgentPySplitPhase7: 函数段结束，format_readable_user_input 到此结束；若没有这行注释，用户不容易看出用户输入模板边界。


def format_readable_initial_messages(payload: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase7: 函数段开始，格式化系统提示词、用户消息和工具列表；若没有这段函数，初始上下文展示逻辑会留在 agent.py。
    messages = payload.get("messages", [])  # 新增代码+AgentPySplitPhase7: 取出初始 messages；若没有这行代码，系统提示词和用户消息没有来源。
    tool_names = payload.get("tool_names", [])  # 新增代码+AgentPySplitPhase7: 取出工具名列表；若没有这行代码，可用工具区块没有来源。
    system_content = ""  # 新增代码+AgentPySplitPhase7: 准备保存系统提示词内容；若没有这行代码，后续拼接变量可能未定义。
    user_content = ""  # 新增代码+AgentPySplitPhase7: 准备保存本轮用户消息；若没有这行代码，后续拼接变量可能未定义。
    if isinstance(messages, list):  # 新增代码+AgentPySplitPhase7: 只在 messages 是列表时遍历；若没有这行代码，异常输入可能导致格式化崩溃。
        for message in messages:  # 新增代码+AgentPySplitPhase7: 遍历模型开局看到的消息；若没有这行代码，无法从列表里找 system/user。
            if not isinstance(message, dict):  # 新增代码+AgentPySplitPhase7: 跳过非字典消息；若没有这行代码，异常消息会让 get 调用失败。
                continue  # 新增代码+AgentPySplitPhase7: 继续检查下一条消息；若没有这行代码，坏消息会阻断整个日志格式化。
            if message.get("role") == "system":  # 新增代码+AgentPySplitPhase7: 找到 system 消息；若没有这行代码，系统提示词不会被抽取。
                system_content = str(message.get("content", ""))  # 新增代码+AgentPySplitPhase7: 保存系统提示词和记忆上下文；若没有这行代码，系统区块会为空。
            if message.get("role") == "user":  # 新增代码+AgentPySplitPhase7: 找到 user 消息；若没有这行代码，本轮用户消息不会被抽取。
                user_content = str(message.get("content", ""))  # 新增代码+AgentPySplitPhase7: 保存用户消息内容；若没有这行代码，用户消息区块会为空。
    tools_text = format_tool_names(tool_names)  # 新增代码+AgentPySplitPhase7: 把工具名列表转成 Markdown 列表；若没有这行代码，可用工具显示会难读。
    return (  # 新增代码+AgentPySplitPhase7: 返回可读上下文区块；若没有这行代码，函数没有输出。
        "## 加载的系统提示词和记忆上下文\n\n"  # 新增代码+AgentPySplitPhase7: 标明这里是模型看到的系统规则和 memory；若没有这行代码，用户难以理解下方长文本来源。
        f"{markdown_code_block('text', system_content)}"  # 新增代码+AgentPySplitPhase7: 展示系统提示词和长期记忆内容；若没有这行代码，初始上下文缺少关键证据。
        "## 本轮用户消息\n\n"  # 新增代码+AgentPySplitPhase7: 标明这里是模型看到的用户消息；若没有这行代码，用户消息和系统提示词会混在一起。
        f"{markdown_code_block('text', user_content)}"  # 新增代码+AgentPySplitPhase7: 展示用户消息；若没有这行代码，模型输入无法完整复盘。
        "## 可用工具\n\n"  # 新增代码+AgentPySplitPhase7: 标明这里是本轮模型可选择工具；若没有这行代码，工具列表没有标题。
        f"{tools_text}\n"  # 新增代码+AgentPySplitPhase7: 展示工具名列表；若没有这行代码，用户不知道模型有哪些工具可选。
    )  # 新增代码+AgentPySplitPhase7: Markdown 片段结束；若没有这行代码，Python 返回表达式无法闭合。
# 新增代码+AgentPySplitPhase7: 函数段结束，format_readable_initial_messages 到此结束；若没有这行注释，用户不容易看出初始上下文模板边界。


def format_readable_model_request(turn: Any, payload: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase7: 函数段开始，格式化模型调用前摘要；若没有这段函数，模型请求摘要会继续堆在 agent.py。
    messages = payload.get("messages", [])  # 新增代码+AgentPySplitPhase7: 取出本轮发送给模型的 messages；若没有这行代码，无法统计上下文消息数量。
    message_count = len(messages) if isinstance(messages, list) else 0  # 新增代码+AgentPySplitPhase7: 统计消息数量；若没有这行代码，用户看不到工具循环后上下文增长。
    tool_names = payload.get("tool_names", [])  # 新增代码+AgentPySplitPhase7: 取出本轮可用工具名；若没有这行代码，模型请求区块无法显示工具面。
    return (  # 新增代码+AgentPySplitPhase7: 返回模型调用轮次摘要；若没有这行代码，函数没有输出。
        f"## 模型调用：第 {turn} 轮\n\n"  # 新增代码+AgentPySplitPhase7: 标明第几轮模型调用；若没有这行代码，多轮 tool loop 不容易跟踪。
        f"发送给模型的消息数量：{message_count}\n\n"  # 新增代码+AgentPySplitPhase7: 显示 messages 数量；若没有这行代码，用户看不到上下文规模变化。
        f"本轮可用工具：{', '.join(str(name) for name in tool_names) if isinstance(tool_names, list) else ''}\n\n"  # 新增代码+AgentPySplitPhase7: 显示本轮可用工具名称；若没有这行代码，工具可见性无法复盘。
    )  # 新增代码+AgentPySplitPhase7: Markdown 片段结束；若没有这行代码，Python 返回表达式无法闭合。
# 新增代码+AgentPySplitPhase7: 函数段结束，format_readable_model_request 到此结束；若没有这行注释，用户不容易看出模型请求模板边界。


def format_readable_model_response(turn: Any, payload: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase7: 函数段开始，格式化模型返回文本和工具计划；若没有这段函数，模型响应排版会留在 agent.py。
    decision_note = str(payload.get("decision_note", ""))  # 新增代码+AgentPySplitPhase7: 取出模型给人看的决策说明；若没有这行代码，日志无法解释模型为什么调用工具或直接回答。
    decision_section = format_readable_decision_note(decision_note)  # 新增代码+AgentPySplitPhase7: 把决策说明转成 Markdown 区块；若没有这行代码，决策说明不能复用统一模板。
    text = str(payload.get("text", ""))  # 新增代码+AgentPySplitPhase7: 取出模型文本；若没有这行代码，模型回答没有来源。
    tool_calls = payload.get("tool_calls", [])  # 新增代码+AgentPySplitPhase7: 取出模型请求的工具调用列表；若没有这行代码，无法判断是否需要展示工具计划。
    if isinstance(tool_calls, list) and tool_calls:  # 新增代码+AgentPySplitPhase7: 如果模型请求了工具；若没有这行代码，工具调用和直接回答会使用同一种模板。
        return (  # 新增代码+AgentPySplitPhase7: 返回包含工具计划的模型响应区块；若没有这行代码，工具计划不会显示。
            f"## 模型返回：第 {turn} 轮\n\n"  # 新增代码+AgentPySplitPhase7: 标明模型响应轮次；若没有这行代码，多轮响应不容易区分。
            f"{decision_section}"  # 新增代码+AgentPySplitPhase7: 展示模型决策说明；若没有这行代码，工具选择原因不会显示。
            "模型文本：\n\n"  # 新增代码+AgentPySplitPhase7: 标明下面是模型文本；若没有这行代码，空文本提示缺少上下文。
            f"{markdown_code_block('text', text or '(空，模型本轮主要是在请求工具)')}"  # 新增代码+AgentPySplitPhase7: 展示模型文本或空文本说明；若没有这行代码，用户可能误以为模型没有响应。
            "模型请求工具：\n\n"  # 新增代码+AgentPySplitPhase7: 标明下面是工具调用计划；若没有这行代码，JSON 数组含义不清楚。
            f"{markdown_code_block('json', json_for_readable(tool_calls))}"  # 新增代码+AgentPySplitPhase7: 用格式化 JSON 展示工具调用数组；若没有这行代码，工具计划难读。
        )  # 新增代码+AgentPySplitPhase7: Markdown 片段结束；若没有这行代码，Python 返回表达式无法闭合。
    return (  # 新增代码+AgentPySplitPhase7: 如果没有工具调用，返回直接回答区块；若没有这行代码，直接回答场景没有输出。
        f"## 模型返回：第 {turn} 轮\n\n"  # 新增代码+AgentPySplitPhase7: 标明模型响应轮次；若没有这行代码，多轮响应不容易区分。
        f"{decision_section}"  # 新增代码+AgentPySplitPhase7: 展示模型决策说明；若没有这行代码，直接回答原因不会显示。
        "模型文本：\n\n"  # 新增代码+AgentPySplitPhase7: 标明下面是模型文本；若没有这行代码，文本区块不清楚。
        f"{markdown_code_block('text', text)}"  # 新增代码+AgentPySplitPhase7: 展示模型文本；若没有这行代码，模型回答不会写入 Markdown。
        "是否请求工具：没有请求工具。\n\n"  # 新增代码+AgentPySplitPhase7: 明确说明本轮没有工具调用；若没有这行代码，用户不确定模型是否跳过了工具。
    )  # 新增代码+AgentPySplitPhase7: Markdown 片段结束；若没有这行代码，Python 返回表达式无法闭合。
# 新增代码+AgentPySplitPhase7: 函数段结束，format_readable_model_response 到此结束；若没有这行注释，用户不容易看出模型响应模板边界。


def format_readable_decision_note(decision_note: str) -> str:  # 新增代码+AgentPySplitPhase7: 函数段开始，把模型决策说明格式化为 Markdown 区块；若没有这段函数，决策说明展示会重复在多个模板里。
    if not decision_note.strip():  # 新增代码+AgentPySplitPhase7: 如果模型没有提供决策说明；若没有这行代码，空内容也会生成噪音标题。
        return ""  # 新增代码+AgentPySplitPhase7: 不显示空区块；若没有这行代码，可读日志会出现无意义段落。
    return (  # 新增代码+AgentPySplitPhase7: 返回决策说明区块；若没有这行代码，函数无法输出文本。
        "## 模型决策说明\n\n"  # 新增代码+AgentPySplitPhase7: 标明这是模型给人看的行动原因；若没有这行代码，用户可能把它和最终回答混淆。
        f"{markdown_code_block('text', decision_note)}"  # 新增代码+AgentPySplitPhase7: 用代码块展示说明；若没有这行代码，长句会挤成一行。
    )  # 新增代码+AgentPySplitPhase7: Markdown 片段结束；若没有这行代码，Python 返回表达式无法闭合。
# 新增代码+AgentPySplitPhase7: 函数段结束，format_readable_decision_note 到此结束；若没有这行注释，用户不容易看出决策说明模板边界。


def format_readable_tool_call(turn: Any, payload: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase7: 函数段开始，格式化工具调用请求；若没有这段函数，工具调用排版会继续留在 agent.py。
    tool_name = str(payload.get("tool_name", ""))  # 新增代码+AgentPySplitPhase7: 读取工具名；若没有这行代码，工具调用区块不知道展示哪个工具。
    call_id = str(payload.get("call_id", ""))  # 新增代码+AgentPySplitPhase7: 读取工具调用 id；若没有这行代码，工具调用和结果不容易对应。
    arguments = payload.get("arguments", {})  # 新增代码+AgentPySplitPhase7: 读取工具参数；若没有这行代码，用户看不到模型给工具的输入。
    return (  # 新增代码+AgentPySplitPhase7: 返回工具调用区块；若没有这行代码，函数没有输出。
        f"## 工具调用：第 {turn} 轮\n\n"  # 新增代码+AgentPySplitPhase7: 标明工具调用发生在哪轮模型调用后；若没有这行代码，多轮工具调用不容易定位。
        f"工具名：`{tool_name}`\n\n"  # 新增代码+AgentPySplitPhase7: 显示模型选择的工具；若没有这行代码，用户不知道调用了什么。
        f"调用编号：`{call_id}`\n\n"  # 新增代码+AgentPySplitPhase7: 显示 call_id；若没有这行代码，后续工具结果难以配对。
        "参数：\n\n"  # 新增代码+AgentPySplitPhase7: 标明下面是工具参数；若没有这行代码，JSON 内容含义不清楚。
        f"{markdown_code_block('json', json_for_readable(arguments))}"  # 新增代码+AgentPySplitPhase7: 用格式化 JSON 展示参数；若没有这行代码，复杂参数难读。
    )  # 新增代码+AgentPySplitPhase7: Markdown 片段结束；若没有这行代码，Python 返回表达式无法闭合。
# 新增代码+AgentPySplitPhase7: 函数段结束，format_readable_tool_call 到此结束；若没有这行注释，用户不容易看出工具调用模板边界。


def format_readable_tool_result(payload: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase7: 函数段开始，格式化工具执行结果；若没有这段函数，工具结果排版会继续留在 agent.py。
    tool_name = str(payload.get("tool_name", ""))  # 新增代码+AgentPySplitPhase7: 读取工具名；若没有这行代码，结果区块不知道来自哪个工具。
    call_id = str(payload.get("call_id", ""))  # 新增代码+AgentPySplitPhase7: 读取工具调用 id；若没有这行代码，工具结果不容易对应前面的调用。
    output = str(payload.get("output", ""))  # 新增代码+AgentPySplitPhase7: 读取工具执行结果；若没有这行代码，模型看到的工具输出不会展示。
    return (  # 新增代码+AgentPySplitPhase7: 返回工具结果区块；若没有这行代码，函数没有输出。
        "## 工具执行结果\n\n"  # 新增代码+AgentPySplitPhase7: 标明工具层已经执行完成；若没有这行代码，用户不知道这是工具返回而非模型回答。
        f"工具名：`{tool_name}`\n\n"  # 新增代码+AgentPySplitPhase7: 显示工具名；若没有这行代码，结果来源不清楚。
        f"调用编号：`{call_id}`\n\n"  # 新增代码+AgentPySplitPhase7: 显示 call_id；若没有这行代码，工具结果无法和请求配对。
        "结果：\n\n"  # 新增代码+AgentPySplitPhase7: 标明下面是工具返回给模型看的文本；若没有这行代码，结果内容缺少说明。
        f"{markdown_code_block('text', output)}"  # 新增代码+AgentPySplitPhase7: 用代码块展示工具结果；若没有这行代码，长输出会难以阅读。
    )  # 新增代码+AgentPySplitPhase7: Markdown 片段结束；若没有这行代码，Python 返回表达式无法闭合。
# 新增代码+AgentPySplitPhase7: 函数段结束，format_readable_tool_result 到此结束；若没有这行注释，用户不容易看出工具结果模板边界。


def format_readable_final_answer(payload: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase7: 函数段开始，格式化最终回答；若没有这段函数，可读日志不会清楚标记本轮结束。
    return (  # 新增代码+AgentPySplitPhase7: 返回最终回答区块；若没有这行代码，函数没有输出。
        "## 最终回答\n\n"  # 新增代码+AgentPySplitPhase7: 标明本轮 agent 已经完成；若没有这行代码，用户不容易找到最终结果。
        f"{markdown_code_block('text', str(payload.get('text', '')))}"  # 新增代码+AgentPySplitPhase7: 展示最终返回给用户的文本；若没有这行代码，日志缺少最终答案。
        "---\n\n"  # 新增代码+AgentPySplitPhase7: 用分隔线隔开不同运行；若没有这行代码，追加日志多轮内容会粘在一起。
    )  # 新增代码+AgentPySplitPhase7: Markdown 片段结束；若没有这行代码，Python 返回表达式无法闭合。
# 新增代码+AgentPySplitPhase7: 函数段结束，format_readable_final_answer 到此结束；若没有这行注释，用户不容易看出最终回答模板边界。


def format_readable_safety_stop(payload: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase7: 函数段开始，格式化安全停止结果；若没有这段函数，循环上限停止不会有清晰日志。
    return (  # 新增代码+AgentPySplitPhase7: 返回安全停止区块；若没有这行代码，函数没有输出。
        "## 安全停止\n\n"  # 新增代码+AgentPySplitPhase7: 标明 agent 因循环上限停止；若没有这行代码，用户不知道这是保护性停止。
        f"{markdown_code_block('text', str(payload.get('text', '')))}"  # 新增代码+AgentPySplitPhase7: 展示安全停止提示；若没有这行代码，停止原因不会进入 Markdown。
        "---\n\n"  # 新增代码+AgentPySplitPhase7: 用分隔线结束本轮日志；若没有这行代码，后续追加内容会粘连。
    )  # 新增代码+AgentPySplitPhase7: Markdown 片段结束；若没有这行代码，Python 返回表达式无法闭合。
# 新增代码+AgentPySplitPhase7: 函数段结束，format_readable_safety_stop 到此结束；若没有这行注释，用户不容易看出安全停止模板边界。


def format_tool_names(tool_names: Any) -> str:  # 新增代码+AgentPySplitPhase7: 函数段开始，把工具名列表格式化为 Markdown 列表；若没有这段函数，工具列表展示会重复在多个位置。
    if not isinstance(tool_names, list) or not tool_names:  # 新增代码+AgentPySplitPhase7: 如果工具名不是列表或为空；若没有这行代码，空工具列表会输出奇怪内容。
        return "- 暂无工具\n"  # 新增代码+AgentPySplitPhase7: 返回空工具提示；若没有这行代码，用户不知道本轮没有工具可用。
    return "".join(f"- `{name}`\n" for name in tool_names)  # 新增代码+AgentPySplitPhase7: 每个工具名一行；若没有这行代码，工具列表不适合记事本阅读。
# 新增代码+AgentPySplitPhase7: 函数段结束，format_tool_names 到此结束；若没有这行注释，用户不容易看出工具名列表模板边界。


def json_for_readable(value: Any) -> str:  # 新增代码+AgentPySplitPhase7: 函数段开始，把任意值格式化为缩进 JSON 字符串；若没有这段函数，工具参数和调用计划会难读。
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)  # 新增代码+AgentPySplitPhase7: 使用中文不转义和缩进；若没有这行代码，中文会转义且结构不清楚。
# 新增代码+AgentPySplitPhase7: 函数段结束，json_for_readable 到此结束；若没有这行注释，用户不容易看出 JSON 格式化边界。


def markdown_code_block(language: str, text: str) -> str:  # 新增代码+AgentPySplitPhase7: 函数段开始，生成 Markdown 代码块；若没有这段函数，长文本会挤在一行且容易破坏排版。
    return f"````{language}\n{text}\n````\n\n"  # 新增代码+AgentPySplitPhase7: 使用四反引号包裹内容；若没有这行代码，内容里出现三反引号时可能破坏 Markdown。
# 新增代码+AgentPySplitPhase7: 函数段结束，markdown_code_block 到此结束；若没有这行注释，用户不容易看出代码块模板边界。
