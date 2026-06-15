"""把真实 agent 主循环接入 durable harness runtime。"""  # 新增代码+HarnessSessionRuntime: 说明本文件负责桥接 agent.run 和 harness；若没有这行代码，真实入口仍容易绕过 harness。

from __future__ import annotations  # 新增代码+HarnessSessionRuntime: 延迟解析类型注解；若没有这行代码，agent duck type 标注更容易出错。

import secrets  # 新增代码+HarnessSessionRuntime: 生成 harness runtime run_id 需要随机后缀；若没有这行代码，多轮运行可能 id 冲突。
from typing import Any, Callable  # 修改代码+ProcessSummaryUX: 增加 Callable 用来标注可选事件回调；若没有这行代码，终端摘要接线只能使用不清晰的动态类型。

from learning_agent.harness.models import HarnessRun, HarnessStage, VerificationResult, utc_timestamp  # 修改代码+HarnessSessionRuntime: 同时导入统一时间戳；若没有这行代码，阶段 started/completed 时间无法落盘。
from learning_agent.harness.store import HarnessStore  # 新增代码+HarnessSessionRuntime: 需要写入 harness 状态和事件；若没有这行代码，主循环仍只写 transcript。
from learning_agent.runtime.command_queue import RuntimeCommand, RuntimeCommandQueue  # 修改代码+HarnessQueueDrain: 同时导入命令对象和队列；若没有 RuntimeCommand，drain helper 无法清楚标注命令列表类型。


def _format_task_notification(payload: dict[str, Any]) -> str:  # 新增代码+HarnessQueueDrain: 把 task notification 转成模型可见文本；若没有这行代码，后台任务结果只会停在队列里。
    task_id = str(payload.get("task_id", ""))  # 新增代码+HarnessQueueDrain: 提取任务 id；若没有这行代码，模型无法知道通知对应哪个任务。
    status = str(payload.get("status", ""))  # 新增代码+HarnessQueueDrain: 提取任务状态；若没有这行代码，模型无法判断任务完成、失败还是卡住。
    summary = str(payload.get("summary", ""))  # 新增代码+HarnessQueueDrain: 提取任务摘要；若没有这行代码，模型看不到后台任务的实际结果。
    output_file = str(payload.get("output_file", ""))  # 新增代码+HarnessQueueDrain: 提取完整输出文件路径；若没有这行代码，长输出无法被后续工具定位。
    usage = payload.get("usage", {})  # 新增代码+HarnessQueueDrain: 提取用量信息；若没有这行代码，任务通知会缺少成本和执行摘要线索。
    return "\n".join([f"<task-notification task_id=\"{task_id}\">", f"status: {status}", f"summary: {summary}", f"output_file: {output_file}", f"usage: {usage}", "</task-notification>"])  # 新增代码+HarnessQueueDrain: 返回清楚边界的通知块；若没有这行代码，模型可能把通知和用户普通输入混在一起。


def _format_resume_interrupted(payload: dict[str, Any]) -> str:  # 新增代码+HarnessQueueDrain: 把 interrupted resume 命令转成模型可见文本；若没有这行代码，恢复命令只会写入队列但不会驱动继续。
    run_id = str(payload.get("run_id", ""))  # 新增代码+HarnessQueueDrain: 提取要恢复的 harness run id；若没有这行代码，模型不知道继续哪个任务。
    prompt = str(payload.get("prompt", ""))  # 新增代码+HarnessQueueDrain: 提取续跑提示；若没有这行代码，模型不知道当前动作是继续执行。
    original_prompt = str(payload.get("original_prompt", ""))  # 新增代码+HarnessQueueDrain: 提取原始任务目标；若没有这行代码，模型无法恢复任务意图。
    return "\n".join([f"<resume-interrupted run_id=\"{run_id}\">", f"prompt: {prompt}", f"original_prompt: {original_prompt}", "</resume-interrupted>"])  # 新增代码+HarnessQueueDrain: 返回清楚边界的恢复块；若没有这行代码，恢复上下文会不可审计。


def _format_runtime_command(command: RuntimeCommand) -> str:  # 新增代码+HarnessQueueDrain: 按命令类型转成模型可见文本；若没有这行代码，主循环 drain 后不知道如何喂给模型。
    if command.mode == "prompt":  # 新增代码+HarnessQueueDrain: 处理用户 prompt 命令；若没有这行代码，真实用户输入不会进入模型。
        return str(command.payload.get("text", ""))  # 新增代码+HarnessQueueDrain: 返回 prompt 文本；若没有这行代码，用户输入会被空内容替代。
    if command.mode == "task_notification":  # 新增代码+HarnessQueueDrain: 处理任务通知命令；若没有这行代码，后台任务结果无法自动回灌。
        return _format_task_notification(command.payload)  # 新增代码+HarnessQueueDrain: 转成通知块；若没有这行代码，模型无法读懂 task notification。
    if command.mode == "resume_interrupted":  # 新增代码+HarnessQueueDrain: 处理中断恢复命令；若没有这行代码，resume 命令不会驱动模型继续。
        return _format_resume_interrupted(command.payload)  # 新增代码+HarnessQueueDrain: 转成恢复块；若没有这行代码，恢复信息不会进入上下文。
    return f"<runtime-command mode=\"{command.mode}\">{command.payload}</runtime-command>"  # 新增代码+HarnessQueueDrain: 给未知命令保留可见兜底；若没有这行代码，新命令类型可能被静默丢弃。


def _drain_runtime_commands_for_turn(command_queue: RuntimeCommandQueue) -> list[RuntimeCommand]:  # 新增代码+HarnessQueueDrain: 领取本轮要喂给模型的 durable 命令；若没有这行代码，真实主循环不会消费 runtime queue。
    drained: list[RuntimeCommand] = []  # 新增代码+HarnessQueueDrain: 准备保存本轮已 started 的命令；若没有这行代码，后续无法统一完成或审计。
    while True:  # 新增代码+HarnessQueueDrain: 持续取命令直到队列为空；若没有这行代码，later task notification 可能仍留在队列里。
        command = command_queue.dequeue_next()  # 新增代码+HarnessQueueDrain: 按队列优先级取下一条命令并标记 started；若没有这行代码，多个 worker 可能重复消费。
        if command is None:  # 新增代码+HarnessQueueDrain: 如果没有更多 queued 命令；若没有这行代码，循环不会停。
            break  # 新增代码+HarnessQueueDrain: 结束本轮 drain；若没有这行代码，空队列会造成死循环。
        drained.append(command)  # 新增代码+HarnessQueueDrain: 记录本轮已领取命令；若没有这行代码，命令无法被转成模型输入或标记完成。
    return drained  # 新增代码+HarnessQueueDrain: 返回本轮命令列表；若没有这行代码，调用方拿不到 drain 结果。


def _build_model_visible_input(drained_commands: list[RuntimeCommand], fallback_user_input: str) -> str:  # 新增代码+HarnessQueueDrain: 把已领取命令组装成本轮模型输入；若没有这行代码，队列命令和用户输入仍会分裂。
    command_blocks = [_format_runtime_command(command) for command in drained_commands]  # 新增代码+HarnessQueueDrain: 逐条命令转成可见文本块；若没有这行代码，模型看不到命令内容。
    safe_blocks = [block for block in command_blocks if block.strip()]  # 新增代码+HarnessQueueDrain: 去掉空命令块；若没有这行代码，空 prompt 可能污染上下文。
    if safe_blocks:  # 新增代码+HarnessQueueDrain: 如果本轮确实取到了命令；若没有这行代码，fallback 分支无法区分空队列。
        return "\n\n".join(safe_blocks)  # 新增代码+HarnessQueueDrain: 用空行分隔命令块；若没有这行代码，多个命令会挤在一起难以审计。
    return fallback_user_input  # 新增代码+HarnessQueueDrain: 队列为空时使用调用方输入兜底；若没有这行代码，异常空队列会导致模型输入为空。


def run_agent_with_harness_session(agent: Any, user_input: str, max_turns: int | None = None, event_callback: Callable[[Any], None] | None = None, conversation_history: Any | None = None) -> str:  # 修改代码+交互上下文: 增加可选 conversation_history 透传参数；若没有这行代码，interactive.py 保存的多轮历史会断在 harness runtime 入口。
    harness_store = HarnessStore(agent.workspace / "memory" / "harness")  # 新增代码+HarnessSessionRuntime: 使用 workspace 默认 harness 目录；若没有这行代码，真实运行状态没有固定位置。
    command_queue = RuntimeCommandQueue(agent.workspace / "memory" / "runtime")  # 新增代码+HarnessSessionRuntime: 使用 workspace 默认 runtime 队列目录；若没有这行代码，prompt 和通知无法统一排队。
    command = command_queue.enqueue_prompt(user_input)  # 新增代码+HarnessSessionRuntime: 先把用户输入持久化入队；若没有这行代码，模型请求前崩溃会丢 prompt。
    drained_commands = _drain_runtime_commands_for_turn(command_queue)  # 新增代码+HarnessQueueDrain: 真实主循环消费本轮 runtime 命令；若没有这行代码，prompt/task/resume 仍只在队列里。
    model_visible_input = _build_model_visible_input(drained_commands, user_input)  # 新增代码+HarnessQueueDrain: 构造实际传给模型的输入；若没有这行代码，task notification 和 resume 无法进上下文。
    run_id = f"runtime_{secrets.token_hex(8)}"  # 新增代码+HarnessSessionRuntime: 生成 harness run id；若没有这行代码，状态文件无法区分多轮运行。
    stage = HarnessStage(name="interactive_turn", prompt=user_input, max_attempts=1)  # 新增代码+HarnessSessionRuntime: 把一次真实交互视为一个可审计阶段；若没有这行代码，harness 状态看不到当前 turn。
    run = HarnessRun.create(run_id=run_id, prompt=user_input, stages=[stage])  # 新增代码+HarnessSessionRuntime: 创建 durable run；若没有这行代码，真实主循环不会出现在 harness status。
    stage = run.stages[0]  # 修改代码+HarnessSessionRuntime: 改用 run 内部深拷贝后的阶段对象；若没有这行代码，真实落盘 stage 会一直停在 pending。
    run.status = "running"  # 新增代码+HarnessSessionRuntime: 标记 run 已开始；若没有这行代码，中断恢复无法发现未完成 turn。
    stage.status = "running"  # 新增代码+HarnessSessionRuntime: 标记交互阶段运行中；若没有这行代码，状态页无法显示当前阶段。
    stage.started_at = utc_timestamp()  # 修改代码+HarnessSessionRuntime: 保存阶段开始时间；若没有这行代码，审计时不知道真实 turn 何时开始。
    harness_store.save_run(run)  # 新增代码+HarnessSessionRuntime: 在模型请求前保存 running 状态；若没有这行代码，崩溃后无法恢复。
    harness_store.append_event(run.run_id, "runtime_command_queued", {"command_id": command.command_id, "mode": command.mode})  # 新增代码+HarnessSessionRuntime: 记录 prompt 已进入 runtime queue；若没有这行代码，队列和 run 无法关联。
    harness_store.append_event(run.run_id, "runtime_commands_attached", {"commands": [{"command_id": item.command_id, "mode": item.mode, "priority": item.priority} for item in drained_commands]})  # 新增代码+HarnessQueueDrain: 记录哪些命令已进入模型上下文；若没有这行代码，command_completed 不能证明模型真的看见了命令。
    final_answer = ""  # 新增代码+HarnessSessionRuntime: 保存最终回答文本；若没有这行代码，run_completed 后没有返回值。
    failed_text = ""  # 新增代码+HarnessSessionRuntime: 保存失败文本；若没有这行代码，异常路径无法写 failure_reason。
    try:  # 新增代码+HarnessSessionRuntime: 捕获事件流消费过程异常；若没有这行代码，状态可能卡在 running。
        for event in agent.run_events(model_visible_input, max_turns=max_turns, conversation_history=conversation_history):  # 修改代码+交互上下文: 用已 drain 的模型可见输入和交互历史驱动事件流；若没有这行代码，第二轮短句仍只会看到当前输入。
            event_payload = event.to_json_dict() if hasattr(event, "to_json_dict") else {"event_type": getattr(event, "event_type", ""), "payload": getattr(event, "payload", {})}  # 新增代码+HarnessSessionRuntime: 把 AgentEvent 转成 JSON；若没有这行代码，harness event 无法保存结构化事件。
            harness_store.append_event(run.run_id, "agent_event", event_payload)  # 新增代码+HarnessSessionRuntime: 镜像 AgentEvent 到 harness 事件流；若没有这行代码，transcript 和 harness 仍是两套证据。
            if event_callback is not None:  # 新增代码+ProcessSummaryUX: 只在交互终端传入回调时转发事件；若没有这行代码，普通 API 调用会被迫承担终端 UI 行为。
                try:  # 新增代码+ProcessSummaryUX: 隔离摘要渲染器异常；若没有这行代码，UI 显示错误可能拖垮真实 agent 主循环。
                    event_callback(event)  # 新增代码+ProcessSummaryUX: 把真实 AgentEvent 传给终端摘要渲染器；若没有这行代码，用户看不到 Codex 风格过程摘要。
                except Exception as callback_error:  # 新增代码+ProcessSummaryUX: 捕获回调异常并继续执行；若没有这行代码，摘要插件的小错误会变成任务失败。
                    harness_store.append_event(run.run_id, "event_callback_failed", {"error": str(callback_error)})  # 新增代码+ProcessSummaryUX: 把 UI 回调失败写入 harness 便于排查；若没有这行代码，过程摘要坏了会没有证据。
            if getattr(event, "event_type", "") == "run_completed":  # 新增代码+HarnessSessionRuntime: 识别事件流完成事件；若没有这行代码，最终回答无法提取。
                payload = getattr(event, "payload", {})  # 新增代码+HarnessSessionRuntime: 读取完成事件 payload；若没有这行代码，无法拿到 text 字段。
                final_answer = str(payload.get("text", "")) if isinstance(payload, dict) else ""  # 新增代码+HarnessSessionRuntime: 保存最终回答；若没有这行代码，兼容 run 返回会变空。
            if getattr(event, "event_type", "") == "run_failed":  # 新增代码+HarnessSessionRuntime: 识别事件流失败事件；若没有这行代码，失败会被误当完成。
                payload = getattr(event, "payload", {})  # 新增代码+HarnessSessionRuntime: 读取失败 payload；若没有这行代码，无法提取错误文本。
                failed_text = str(payload.get("text", "")) if isinstance(payload, dict) else "任务失败。"  # 新增代码+HarnessSessionRuntime: 保存失败说明；若没有这行代码，failure_reason 会为空。
    except Exception as error:  # 新增代码+HarnessSessionRuntime: 处理 run_events 自身抛错；若没有这行代码，harness run 会永久 running。
        failed_text = f"任务失败：{error}"  # 新增代码+HarnessSessionRuntime: 构造可读失败文本；若没有这行代码，用户看不到异常原因。
    if failed_text:  # 新增代码+HarnessSessionRuntime: 如果事件流失败；若没有这行代码，失败路径会继续按完成保存。
        run.status = "failed"  # 新增代码+HarnessSessionRuntime: 标记 run 失败；若没有这行代码，状态页会误报 completed。
        run.failure_reason = failed_text  # 新增代码+HarnessSessionRuntime: 保存失败原因；若没有这行代码，排查要翻底层日志。
        stage.status = "failed"  # 新增代码+HarnessSessionRuntime: 标记阶段失败；若没有这行代码，失败阶段无法定位。
        stage.completed_at = utc_timestamp()  # 修改代码+HarnessSessionRuntime: 保存失败收束时间；若没有这行代码，失败阶段缺少结束时间证据。
        stage.acceptance = VerificationResult(passed=False, checks=["run_failed"], message=failed_text)  # 新增代码+HarnessSessionRuntime: 保存失败验收结果；若没有这行代码，acceptance 状态缺证据。
        for drained_command in drained_commands:  # 修改代码+HarnessQueueDrain: 收束本轮已经附加到模型上下文的所有命令；若没有这行代码，task/resume 命令会残留 started。
            command_queue.mark_completed(drained_command.command_id)  # 修改代码+HarnessQueueDrain: 标记命令完成；若没有这行代码，已经进入模型的命令可能被重复消费。
        harness_store.save_run(run)  # 新增代码+HarnessSessionRuntime: 保存失败状态；若没有这行代码，重启后仍是 running。
        harness_store.append_event(run.run_id, "run_failed", {"text": failed_text})  # 新增代码+HarnessSessionRuntime: 记录 harness 失败事件；若没有这行代码，harness 事件流没有终点。
        return failed_text  # 新增代码+HarnessSessionRuntime: 兼容旧 run 返回失败文本；若没有这行代码，调用方拿不到错误。
    stage.status = "completed"  # 新增代码+HarnessSessionRuntime: 标记交互阶段完成；若没有这行代码，恢复时会误以为阶段未完成。
    stage.checkpoint = final_answer[:500]  # 新增代码+HarnessSessionRuntime: 保存最终回答摘要作为 checkpoint；若没有这行代码，状态页缺少阶段结果。
    stage.completed_at = utc_timestamp()  # 修改代码+HarnessSessionRuntime: 保存阶段完成时间；若没有这行代码，验收报告无法判断 turn 是否真正收束。
    stage.acceptance = VerificationResult(passed=True, checks=["run_completed"], message="passed")  # 新增代码+HarnessSessionRuntime: 保存完成验收；若没有这行代码，stage 完成缺少证据。
    run.status = "completed"  # 新增代码+HarnessSessionRuntime: 标记 run 完成；若没有这行代码，队列会认为任务仍可恢复。
    run.current_stage_index = len(run.stages)  # 新增代码+HarnessSessionRuntime: 推进 checkpoint 到末尾；若没有这行代码，恢复可能重跑已完成阶段。
    for drained_command in drained_commands:  # 修改代码+HarnessQueueDrain: 收束本轮已经进入模型上下文的所有命令；若没有这行代码，通知和恢复命令不会完成。
        command_queue.mark_completed(drained_command.command_id)  # 修改代码+HarnessQueueDrain: 标记单条命令完成；若没有这行代码，队列生命周期无法闭环。
    harness_store.save_run(run)  # 新增代码+HarnessSessionRuntime: 保存完成状态；若没有这行代码，重启后看不到完成。
    harness_store.append_event(run.run_id, "run_completed", {"command_id": command.command_id, "text": final_answer})  # 新增代码+HarnessSessionRuntime: 记录 harness 完成事件；若没有这行代码，事件流缺终点。
    return final_answer  # 新增代码+HarnessSessionRuntime: 返回最终回答保持旧 run API；若没有这行代码，CLI/HTTP bridge 会拿不到 answer。
