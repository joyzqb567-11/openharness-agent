"""调试日志 JSONL 写入 helper，把日志落盘细节从主 agent 中拆出来。"""  # 新增代码+ObservabilitySplit: 说明本模块负责调试日志；若没有这行代码，排查日志写入时还要回到巨型入口文件。
from __future__ import annotations  # 新增代码+ObservabilitySplit: 允许类型注解延迟解析；若没有这行代码，类型提示在部分运行顺序下可能提前求值。

import json  # 新增代码+ObservabilitySplit: 把调试记录序列化为 JSON；若没有这行代码，debug_logs 无法保持机器可读。
import time  # 新增代码+ObservabilitySplit: 给调试记录生成时间；若没有这行代码，调试事件缺少发生顺序线索。
from pathlib import Path  # 新增代码+ObservabilitySplit: 使用 Path 处理日志文件路径；若没有这行代码，Windows 路径处理会分散在主类里。
from typing import Any  # 新增代码+ObservabilitySplit: 标注通用 payload 类型；若没有这行代码，函数签名会失去结构说明。


def build_debug_event_record(run_id: str, event: str, payload: dict[str, Any], turn: int | None = None) -> dict[str, Any]:  # 新增代码+ObservabilitySplit: 构造统一调试事件记录；若没有这行代码，主类仍要手写日志字典。
    return {  # 新增代码+ObservabilitySplit: 返回可写入 JSONL 的记录；若没有这行代码，调用方拿不到结构化日志。
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),  # 新增代码+ObservabilitySplit: 记录人类可读时间；若没有这行代码，可读日志和 JSONL 都缺少时间字段。
        "run_id": run_id,  # 新增代码+ObservabilitySplit: 记录本轮请求编号；若没有这行代码，多轮对话日志无法分组。
        "event": event,  # 新增代码+ObservabilitySplit: 记录事件类型；若没有这行代码，排查时不知道这是请求、响应还是工具结果。
        "turn": turn,  # 新增代码+ObservabilitySplit: 记录模型调用轮次；若没有这行代码，多轮 tool loop 难以定位。
        "payload": payload,  # 新增代码+ObservabilitySplit: 保存事件具体内容；若没有这行代码，日志只剩空壳没有排查价值。
    }  # 新增代码+ObservabilitySplit: 结束记录字典；若没有这行代码，Python 字典语法不完整。


def append_debug_event_record(debug_log_path: Path, record: dict[str, Any]) -> None:  # 新增代码+ObservabilitySplit: 把调试记录追加到 JSONL 文件；若没有这行代码，主类仍要处理目录和文件写入。
    debug_log_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+ObservabilitySplit: 确保 debug_logs 目录存在；若没有这行代码，首次写日志会因目录缺失失败。
    with debug_log_path.open("a", encoding="utf-8") as file:  # 新增代码+ObservabilitySplit: 以追加模式打开 JSONL 文件；若没有这行代码，新事件无法保存。
        file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")  # 新增代码+ObservabilitySplit: 一行写入一个 JSON 事件；若没有这行代码，后续工具无法按行解析日志。
