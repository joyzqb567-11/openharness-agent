from datetime import datetime, timezone  # 新增代码+真实模型延迟基线: 引入标准时间解析工具；如果没有这行，测试无法把 ISO 时间戳转成可计算的 UTC 时间。


def _parse_ts(value: str) -> datetime:  # 新增代码+真实模型延迟基线: 函数段开始，把事件时间字符串转成 UTC datetime；如果没有这段，耗时计算会依赖脆弱的字符串处理。
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)  # 新增代码+真实模型延迟基线: 兼容 Z 结尾并统一到 UTC；如果没有这行，Windows/Python 对 Z 的解析可能失败。


def _ms(start: datetime, end: datetime) -> int:  # 新增代码+真实模型延迟基线: 函数段开始，把两个时间点差值转成毫秒；如果没有这段，测试会重复写换算逻辑。
    return int((end - start).total_seconds() * 1000)  # 新增代码+真实模型延迟基线: 返回整数毫秒；如果没有这行，后续指标会混用秒和毫秒。


def summarize_latency_events(events: list[dict[str, object]]) -> dict[str, int]:  # 新增代码+真实模型延迟基线: 函数段开始，按事件类型生成延迟摘要；如果没有这段，后续无法自动比较优化前后差异。
    by_type = {str(event["type"]): event for event in events}  # 新增代码+真实模型延迟基线: 按事件类型建立索引；如果没有这行，每个指标都要手写遍历查找。
    started = _parse_ts(str(by_type["turn_started"]["ts"]))  # 新增代码+真实模型延迟基线: 读取后端开始处理时间；如果没有这行，模型阶段的起点不明确。
    queued = _parse_ts(str(by_type["gui_turn_queued"]["ts"]))  # 新增代码+真实模型延迟基线: 读取 GUI 入队时间；如果没有这行，无法证明排队不是瓶颈。
    status = _parse_ts(str(by_type["model_call_status"]["ts"]))  # 新增代码+真实模型延迟基线: 读取首个模型状态时间；如果没有这行，无法度量 2 秒内可见状态目标。
    delta = _parse_ts(str(by_type["message_delta"]["ts"]))  # 新增代码+真实模型延迟基线: 读取首个回答 delta 时间；如果没有这行，无法度量真实首文本延迟。
    completed = _parse_ts(str(by_type["gui_turn_completed"]["ts"]))  # 新增代码+真实模型延迟基线: 读取 turn 完成时间；如果没有这行，无法度量总耗时。
    return {  # 新增代码+真实模型延迟基线: 返回统一指标字典；如果没有这行，调用方拿不到结构化摘要。
        "queued_to_started_ms": _ms(queued, started),  # 新增代码+真实模型延迟基线: 保存入队到启动耗时；如果没有这行，排队阶段无法被单独观察。
        "started_to_first_status_ms": _ms(started, status),  # 新增代码+真实模型延迟基线: 保存启动到首状态耗时；如果没有这行，首状态指标会被遗漏。
        "started_to_first_delta_ms": _ms(started, delta),  # 新增代码+真实模型延迟基线: 保存启动到首 delta 耗时；如果没有这行，核心慢点无法被量化。
        "started_to_completed_ms": _ms(started, completed),  # 新增代码+真实模型延迟基线: 保存启动到完成耗时；如果没有这行，总调用耗时没有基线。
    }  # 新增代码+真实模型延迟基线: 指标字典结束；如果没有这行，Python 字典语法不完整。


def test_latency_summary_separates_queue_start_status_delta_and_completion():  # 新增代码+真实模型延迟基线: 测试基线摘要能分清排队、启动、首状态、首 delta 和完成耗时；如果没有这条测试，后续可能把首状态误当首 token。
    events = [  # 新增代码+真实模型延迟基线: 准备一组模拟 GUI 事件；如果没有这组数据，测试无法复现 123 秒首 delta 的慢点。
        {"type": "gui_turn_queued", "turn_id": "turn_a", "ts": "2026-06-26T13:30:31Z"},  # 新增代码+真实模型延迟基线: 表示 GUI turn 入队；如果没有这行，无法计算 queued_to_started_ms。
        {"type": "turn_started", "turn_id": "turn_a", "ts": "2026-06-26T13:30:31Z"},  # 新增代码+真实模型延迟基线: 表示后端已开始处理；如果没有这行，无法定位模型调用阶段的起点。
        {"type": "model_call_status", "turn_id": "turn_a", "phase": "connecting", "ts": "2026-06-26T13:30:32Z"},  # 新增代码+真实模型延迟基线: 表示首个可见模型状态；如果没有这行，无法验证 2 秒内可见状态指标。
        {"type": "message_delta", "turn_id": "turn_a", "ts": "2026-06-26T13:32:34Z"},  # 新增代码+真实模型延迟基线: 表示首个回答 delta；如果没有这行，无法独立测量真实首 token/首文本延迟。
        {"type": "gui_turn_completed", "turn_id": "turn_a", "ts": "2026-06-26T13:32:35Z"},  # 新增代码+真实模型延迟基线: 表示本轮完成；如果没有这行，无法计算整体完成耗时。
    ]  # 新增代码+真实模型延迟基线: 事件样本结束；如果没有这行，Python 列表语法不完整。

    summary = summarize_latency_events(events)  # 新增代码+真实模型延迟基线: 调用待实现的摘要函数；如果没有这行，测试不会驱动实现真实的耗时汇总。

    assert summary["queued_to_started_ms"] == 0  # 新增代码+真实模型延迟基线: 断言排队到启动没有慢点；如果没有这行，无法排除 bridge 排队问题。
    assert summary["started_to_first_status_ms"] == 1000  # 新增代码+真实模型延迟基线: 断言首状态耗时为 1 秒；如果没有这行，后续可能把状态可见性指标漏掉。
    assert summary["started_to_first_delta_ms"] == 123000  # 新增代码+真实模型延迟基线: 断言首 delta 慢点为 123 秒；如果没有这行，无法守住真实用户感知瓶颈。
    assert summary["started_to_completed_ms"] == 124000  # 新增代码+真实模型延迟基线: 断言完成耗时为 124 秒；如果没有这行，无法对比整体调用时间。
