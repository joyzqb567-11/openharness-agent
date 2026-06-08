"""长任务 harness 的状态渲染。"""  # 新增代码+LongTaskHarness: 说明本文件负责可视化文本；若没有这行代码，状态输出逻辑边界不清楚。

from __future__ import annotations  # 新增代码+LongTaskHarness: 延迟解析类型注解；若没有这行代码，类型引用更容易受定义顺序影响。

from typing import Any  # 新增代码+LongTaskHarness: 事件列表来自 JSON 字典；若没有这行代码，类型边界不清楚。

from learning_agent.harness.models import HarnessRun  # 新增代码+LongTaskHarness: 状态渲染需要读取 run 对象；若没有这行代码，函数无法访问阶段状态。


def _one_line_tail(text: str, max_chars: int = 200) -> str:  # 新增代码+HarnessStatusAudit: 把长输出压成单行尾部摘要；若没有这行代码，状态页容易被多行输出刷屏。
    tail = str(text)[-max_chars:]  # 新增代码+HarnessStatusAudit: 只取最后一段文本；若没有这行代码，长输出会让状态 CLI 过长。
    return tail.replace("\r", "\\r").replace("\n", "\\n")  # 新增代码+HarnessStatusAudit: 把换行转义成可读单行；若没有这行代码，状态表格结构会被输出内容打乱。


def render_harness_status(run: HarnessRun, events: list[dict[str, Any]] | None = None) -> str:  # 新增代码+LongTaskHarness: 把 run 状态渲染成可读文本；若没有这行代码，用户和外部 agent 只能看 JSON。
    safe_events = events or []  # 新增代码+LongTaskHarness: 空事件时使用空列表；若没有这行代码，新任务状态渲染会报错。
    last_event = safe_events[-1]["event_type"] if safe_events else "none"  # 新增代码+LongTaskHarness: 提取最近事件；若没有这行代码，用户不知道最后发生了什么。
    lines = [f"HarnessRun {run.run_id}: status={run.status} current_stage_index={run.current_stage_index} endpoint={run.current_endpoint()} last_event={last_event}", f"prompt={run.prompt}"]  # 新增代码+LongTaskHarness: 写入 run 总览；若没有这行代码，状态页缺少核心定位信息。
    if run.failure_reason:  # 新增代码+LongTaskHarness: 有失败原因时展示；若没有这行代码，失败状态不解释原因。
        lines.append(f"failure_reason={run.failure_reason}")  # 新增代码+LongTaskHarness: 加入失败原因行；若没有这行代码，用户要翻事件才能知道问题。
    for index, stage in enumerate(run.stages):  # 新增代码+LongTaskHarness: 遍历每个阶段；若没有这行代码，状态页无法显示阶段进度。
        acceptance = "passed" if stage.acceptance.passed else ("failed" if stage.acceptance.message else "pending")  # 新增代码+LongTaskHarness: 计算验收文本；若没有这行代码，acceptance 状态不可读。
        lines.append(f"- stage[{index}] {stage.name}: status={stage.status} attempts={len(stage.attempts)}/{stage.safe_max_attempts()} acceptance={acceptance} checkpoint={stage.checkpoint[:80]}")  # 新增代码+LongTaskHarness: 写入阶段状态行；若没有这行代码，用户不知道阶段尝试和验收情况。
        if stage.acceptance.checks:  # 新增代码+HarnessStatusAudit: 如果 verifier 有具体检查项；若没有这行代码，用户只能看到 passed 而不知道通过了哪些门禁。
            lines.append(f"  verifier_checks={', '.join(stage.acceptance.checks)}")  # 新增代码+HarnessStatusAudit: 展示 verifier 检查项；若没有这行代码，验收结果不可复核。
        if stage.acceptance.message:  # 新增代码+HarnessStatusAudit: 如果 verifier 有结论消息；若没有这行代码，失败或通过说明不会出现在状态页。
            lines.append(f"  verifier_message={stage.acceptance.message}")  # 新增代码+HarnessStatusAudit: 展示 verifier 可读结论；若没有这行代码，用户要打开 JSON 才能看原因。
        if stage.attempts:  # 新增代码+HarnessStatusAudit: 如果阶段已有尝试历史；若没有这行代码，状态页看不到阶段实际输出。
            latest_attempt = stage.attempts[-1]  # 新增代码+HarnessStatusAudit: 取最近一次尝试作为当前输出证据；若没有这行代码，用户不知道最新结果是哪次。
            output_tail = _one_line_tail(latest_attempt.output)  # 新增代码+HarnessStatusAudit: 生成输出尾部摘要；若没有这行代码，长输出会破坏状态页可读性。
            lines.append(f"  latest_attempt={latest_attempt.status} endpoint={latest_attempt.endpoint or '(default)'} output_tail={output_tail or '(empty)'}")  # 新增代码+HarnessStatusAudit: 展示尝试状态、endpoint 和输出尾巴；若没有这行代码，run/stage/output 证据不会同屏可见。
    return "\n".join(lines)  # 新增代码+LongTaskHarness: 合并多行状态文本；若没有这行代码，调用方拿不到可打印字符串。
