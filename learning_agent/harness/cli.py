"""长任务 harness 的命令行入口。"""  # 新增代码+LongTaskHarness: 说明本文件给外部 agent 提供命令入口；若没有这行代码，CLI 边界不清楚。

from __future__ import annotations  # 新增代码+LongTaskHarness: 延迟解析类型注解；若没有这行代码，main 参数注解更容易受版本影响。

import argparse  # 新增代码+LongTaskHarness: 解析 status/list 等命令参数；若没有这行代码，外部 agent 只能写 Python 调用。
from pathlib import Path  # 新增代码+LongTaskHarness: 处理 store 路径；若没有这行代码，CLI 路径拼接会更脆弱。

from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+BrowserStatusStage11: CLI 读取浏览器 runtime store；若没有这行代码，命令行看不到 browser run/action/event。
from learning_agent.harness.agent_executor import build_default_learning_agent_executor  # 新增代码+HarnessCliAgentExecution: 导入真实 agent executor 构建器；若没有这行代码，run --executor agent 无法接入 LearningAgent。
from learning_agent.harness.models import HarnessRun, HarnessStage  # 新增代码+HarnessCliAgentExecution: CLI enqueue 需要创建 run 和 stage；若没有这行代码，命令无法持久化新任务。
from learning_agent.harness.queue import HarnessQueue  # 新增代码+HarnessCliAgentExecution: CLI enqueue/run 需要持久队列；若没有这行代码，命令只能读不能写。
from learning_agent.harness.runner import HarnessRunner  # 新增代码+HarnessCliAgentExecution: CLI run 需要调用 runner 推进任务；若没有这行代码，命令无法执行阶段。
from learning_agent.harness.status import render_harness_status  # 新增代码+LongTaskHarness: 导入状态渲染函数；若没有这行代码，status 命令无法输出可读结果。
from learning_agent.harness.store import HarnessStore  # 新增代码+LongTaskHarness: CLI 通过 store 读取状态；若没有这行代码，命令无法访问持久化文件。
from learning_agent.harness.verifier import StageVerifier  # 新增代码+HarnessCliAgentExecution: CLI run 需要阶段验收；若没有这行代码，命令执行后无法判断阶段是否通过。
from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+HarnessCliUpgrade: CLI 需要展示 runtime command queue；若没有这行代码，外部 agent 看不到 prompt/notification 队列。
from learning_agent.runtime.poller import TaskPoller  # 新增代码+HarnessCliUpgrade: CLI poll 命令需要推进 watchdog；若没有这行代码，卡住任务不能从命令行检查。
from learning_agent.runtime.resume import InterruptedRunResumer  # 新增代码+HarnessCliUpgrade: CLI resume 命令需要恢复 interrupted run；若没有这行代码，崩溃恢复没有外部入口。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+StatusEcosystem: CLI snapshot 需要统一状态快照；若没有这行代码，状态 CLI 会继续只看 harness 局部。
from learning_agent.runtime.task_output import TaskOutputStore  # 新增代码+HarnessCliUpgrade: CLI poll 需要读取任务输出文件；若没有这行代码，watchdog 无法判断 Continue?。
from learning_agent.runtime.task_registry import TaskRegistry  # 新增代码+HarnessCliUpgrade: CLI tasks/poll 需要读取持久任务表；若没有这行代码，任务状态不可见。
from learning_agent.app.status_renderer import render_status_snapshot  # 新增代码+StatusEcosystem: CLI snapshot 需要渲染人类可读状态；若没有这行代码，用户只能看原始 JSON。


def _parse_stage_spec(raw_stage: str) -> HarnessStage:  # 新增代码+HarnessCliAgentExecution: 把 name::prompt 文本转成阶段对象；若没有这行代码，enqueue 参数解析会散在 main 里。
    name, separator, prompt = raw_stage.partition("::")  # 新增代码+HarnessCliAgentExecution: 拆分阶段名和阶段 prompt；若没有这行代码，CLI 无法用一项参数表达阶段。
    if not separator or not name.strip() or not prompt.strip():  # 新增代码+HarnessCliAgentExecution: 校验阶段格式完整；若没有这行代码，坏输入会生成空阶段。
        raise ValueError("--stage 必须使用 name::prompt 格式。")  # 新增代码+HarnessCliAgentExecution: 给用户明确格式错误；若没有这行代码，排查 CLI 输入会困难。
    return HarnessStage(name=name.strip(), prompt=prompt.strip())  # 新增代码+HarnessCliAgentExecution: 返回规范化阶段对象；若没有这行代码，enqueue 无法保存阶段。


def _apply_success_markers(stages: list[HarnessStage], marker_specs: list[str]) -> None:  # 新增代码+HarnessCliAgentExecution: 把 stage=marker 参数写入对应阶段；若没有这行代码，CLI 创建的任务缺少验收门禁。
    stage_by_name = {stage.name: stage for stage in stages}  # 新增代码+HarnessCliAgentExecution: 建立阶段名索引；若没有这行代码，每个 marker 都要重复遍历阶段。
    for marker_spec in marker_specs:  # 新增代码+HarnessCliAgentExecution: 遍历用户传入的 marker 规则；若没有这行代码，多阶段验收无法配置。
        stage_name, separator, marker = marker_spec.partition("=")  # 新增代码+HarnessCliAgentExecution: 拆分 stage=marker；若没有这行代码，无法知道 marker 属于哪个阶段。
        if not separator or not stage_name.strip() or not marker.strip():  # 新增代码+HarnessCliAgentExecution: 校验 marker 格式；若没有这行代码，空 marker 会悄悄进入验收规则。
            raise ValueError("--success-marker 必须使用 stage=marker 格式。")  # 新增代码+HarnessCliAgentExecution: 给用户明确格式错误；若没有这行代码，坏参数会导致后续验收难懂。
        if stage_name.strip() not in stage_by_name:  # 新增代码+HarnessCliAgentExecution: 检查 marker 指向的阶段是否存在；若没有这行代码，用户拼错阶段名也不会被发现。
            raise ValueError(f"未知阶段：{stage_name.strip()}。")  # 新增代码+HarnessCliAgentExecution: 报告具体未知阶段；若没有这行代码，用户不知道哪里写错。
        stage_by_name[stage_name.strip()].success_markers.append(marker.strip())  # 新增代码+HarnessCliAgentExecution: 把 marker 追加到阶段；若没有这行代码，StageVerifier 没有文本断言。


def _echo_executor(run: HarnessRun, stage: HarnessStage) -> str:  # 新增代码+HarnessCliAgentExecution: 提供 deterministic executor 给测试和 smoke；若没有这行代码，CLI run 只能调用真实模型。
    _ = run  # 新增代码+HarnessCliAgentExecution: 保留 run 参数以匹配 executor 协议；若没有这行代码，未来扩展 run 上下文不清楚。
    return "\n".join([stage.prompt, *stage.success_markers])  # 新增代码+HarnessCliAgentExecution: 返回阶段 prompt 和 marker，确保 echo 验收可通过；若没有这行代码，本地 smoke 无法稳定完成。


def _tail_file_for_status(path_text: str, max_chars: int = 200) -> str:  # 新增代码+HarnessStatusAudit: 读取 output_path 的尾部摘要给 CLI 直接展示；若没有这行代码，用户必须手动打开输出文件才能审计任务。
    if not path_text:  # 新增代码+HarnessStatusAudit: 如果任务没有输出文件路径；若没有这行代码，Path('') 可能误指向当前目录。
        return ""  # 新增代码+HarnessStatusAudit: 无路径时返回空摘要；若没有这行代码，调用方无法稳定拼接输出。
    path = Path(path_text)  # 新增代码+HarnessStatusAudit: 把持久记录里的路径文本转成 Path；若没有这行代码，后续无法检查文件。
    if not path.exists() or not path.is_file():  # 新增代码+HarnessStatusAudit: 输出文件不存在或不是文件时跳过；若没有这行代码，CLI 会因为旧路径报错。
        return ""  # 新增代码+HarnessStatusAudit: 文件不可读时返回空摘要；若没有这行代码，状态命令不够健壮。
    text = path.read_text(encoding="utf-8", errors="replace")  # 新增代码+HarnessStatusAudit: 读取输出文件内容并容忍坏字符；若没有这行代码，无法展示任务输出尾巴。
    return text[-max_chars:].replace("\r", "\\r").replace("\n", "\\n")  # 新增代码+HarnessStatusAudit: 返回单行尾部摘要；若没有这行代码，多行输出会打乱状态命令结构。


def _build_executor(executor_name: str, workspace: str | Path | None, max_turns: int | None):  # 新增代码+HarnessCliAgentExecution: 根据 CLI 参数选择执行器；若没有这行代码，run 分支会混入 executor 构造细节。
    if executor_name == "echo":  # 新增代码+HarnessCliAgentExecution: 处理无模型 echo 模式；若没有这行代码，自动化测试需要真实模型。
        return _echo_executor  # 新增代码+HarnessCliAgentExecution: 返回确定性 executor；若没有这行代码，echo 模式不会执行。
    if executor_name == "agent":  # 新增代码+HarnessCliAgentExecution: 处理真实 agent 模式；若没有这行代码，harness 不能接入 LearningAgent。
        return build_default_learning_agent_executor(workspace=workspace, max_turns=max_turns)  # 新增代码+HarnessCliAgentExecution: 构建真实 agent executor；若没有这行代码，run --executor agent 没有执行对象。
    raise ValueError(f"未知 executor：{executor_name}")  # 新增代码+HarnessCliAgentExecution: 拒绝未知 executor；若没有这行代码，错误输入会变成静默空行为。


def _browser_store_for_workspace(workspace: str | Path) -> BrowserRuntimeStore:  # 新增代码+BrowserStatusStage11: CLI 按 workspace 形态定位浏览器 store；若没有这行代码，项目根和 agent 根会读不同位置。
    root = Path(workspace)  # 新增代码+BrowserStatusStage11: 规范化工作区路径；若没有这行代码，字符串路径后续处理不稳定。
    direct_store = BrowserRuntimeStore(root / "memory" / "browser_runtime")  # 新增代码+BrowserStatusStage11: 优先使用 agent.workspace 风格目录；若没有这行代码，真实 agent 状态读不到。
    package_store = BrowserRuntimeStore(root / "learning_agent" / "memory" / "browser_runtime")  # 新增代码+BrowserStatusStage11: 兼容从仓库根调用 CLI；若没有这行代码，Codex 外部查询可能漏数据。
    if direct_store.runs_dir.exists() or not package_store.runs_dir.exists():  # 新增代码+BrowserStatusStage11: 根据实际存在目录选择；若没有这行代码，状态路径会误判。
        return direct_store  # 新增代码+BrowserStatusStage11: 返回直接 store；若没有这行代码，调用方拿不到数据源。
    return package_store  # 新增代码+BrowserStatusStage11: 返回包内 store；若没有这行代码，项目根查询无法看到浏览器状态。


def build_parser() -> argparse.ArgumentParser:  # 新增代码+LongTaskHarness: 构造 CLI 参数解析器；若没有这行代码，main 会混入重复解析逻辑。
    parser = argparse.ArgumentParser(prog="learning_agent.harness", description="Inspect learning_agent long-task harness state.")  # 新增代码+LongTaskHarness: 创建根解析器；若没有这行代码，用户看不到命令用法。
    subparsers = parser.add_subparsers(dest="command", required=True)  # 新增代码+LongTaskHarness: 创建子命令集合；若没有这行代码，status/list 无法区分。
    enqueue_parser = subparsers.add_parser("enqueue", help="Create and queue one harness run.")  # 新增代码+HarnessCliAgentExecution: 定义 enqueue 子命令；若没有这行代码，外部 agent 无法通过 CLI 创建任务。
    enqueue_parser.add_argument("--store", required=True, help="Harness store directory.")  # 新增代码+HarnessCliAgentExecution: enqueue 需要 store 目录；若没有这行代码，新任务不知道保存到哪里。
    enqueue_parser.add_argument("--run-id", required=True, help="Harness run id.")  # 新增代码+HarnessCliAgentExecution: 要求调用方提供 run id；若没有这行代码，后续 status 难以定位任务。
    enqueue_parser.add_argument("--prompt", required=True, help="Original long task prompt.")  # 新增代码+HarnessCliAgentExecution: 保存总任务 prompt；若没有这行代码，恢复后不知道任务目标。
    enqueue_parser.add_argument("--stage", action="append", required=True, help="Stage spec in name::prompt format.")  # 新增代码+HarnessCliAgentExecution: 支持重复传入阶段；若没有这行代码，任务无法分阶段。
    enqueue_parser.add_argument("--success-marker", action="append", default=[], help="Stage success marker in stage=marker format.")  # 新增代码+HarnessCliAgentExecution: 支持给阶段配置 marker；若没有这行代码，CLI 任务缺少确定性验收。
    run_parser = subparsers.add_parser("run", help="Run one queued harness task.")  # 新增代码+HarnessCliAgentExecution: 定义 run 子命令；若没有这行代码，外部 agent 无法通过 CLI 推进任务。
    run_parser.add_argument("--store", required=True, help="Harness store directory.")  # 新增代码+HarnessCliAgentExecution: run 需要 store 目录；若没有这行代码，runner 找不到队列。
    run_parser.add_argument("--run-id", default="", help="Optional run id to execute directly.")  # 新增代码+HarnessCliAgentExecution: 支持指定任务执行；若没有这行代码，只能按队列顺序领取。
    run_parser.add_argument("--executor", choices=["echo", "agent"], default="echo", help="Executor mode.")  # 新增代码+HarnessCliAgentExecution: 允许选择 echo 或真实 agent；若没有这行代码，测试和真实任务无法分开。
    run_parser.add_argument("--worker-id", default="harness-cli", help="Worker id for queue lease.")  # 新增代码+HarnessCliAgentExecution: 记录领取任务的 worker；若没有这行代码，审计日志不知道是谁执行。
    run_parser.add_argument("--lease-seconds", type=int, default=300, help="Queue lease seconds.")  # 新增代码+HarnessCliAgentExecution: 配置租约时长；若没有这行代码，长阶段只能用固定 300 秒。
    run_parser.add_argument("--workspace", default="", help="LearningAgent workspace for agent executor.")  # 新增代码+HarnessCliAgentExecution: 真实 agent 模式可指定工作区；若没有这行代码，跨目录调用可能找错 workspace。
    run_parser.add_argument("--max-turns", type=int, default=None, help="Max turns for agent executor.")  # 新增代码+HarnessCliAgentExecution: 真实 agent 模式可限制轮次；若没有这行代码，阶段执行无法单独限流。
    status_parser = subparsers.add_parser("status", help="Print one harness run status.")  # 新增代码+LongTaskHarness: 定义 status 子命令；若没有这行代码，外部 agent 无法查单个任务。
    status_parser.add_argument("--store", required=True, help="Harness store directory.")  # 新增代码+LongTaskHarness: 要求传入 store 目录；若没有这行代码，CLI 不知道读取哪里。
    status_parser.add_argument("--run-id", required=True, help="Harness run id.")  # 新增代码+LongTaskHarness: 要求传入 run id；若没有这行代码，CLI 不知道读取哪个任务。
    list_parser = subparsers.add_parser("list", help="List harness run ids.")  # 新增代码+LongTaskHarness: 定义 list 子命令；若没有这行代码，外部 agent 无法发现任务。
    list_parser.add_argument("--store", required=True, help="Harness store directory.")  # 新增代码+LongTaskHarness: list 也需要 store 目录；若没有这行代码，命令没有数据源。
    queue_parser = subparsers.add_parser("queue", help="Print harness runs and runtime commands.")  # 新增代码+HarnessCliUpgrade: 定义 queue 子命令；若没有这行代码，外部 agent 无法看主队列。
    queue_parser.add_argument("--store", required=True, help="Harness store directory.")  # 新增代码+HarnessCliUpgrade: queue 需要 harness store；若没有这行代码，命令不知道列哪些 run。
    queue_parser.add_argument("--runtime", required=True, help="Runtime command queue directory.")  # 新增代码+HarnessCliUpgrade: queue 需要 runtime queue 目录；若没有这行代码，命令看不到 prompt/notification。
    tasks_parser = subparsers.add_parser("tasks", help="Print durable task registry.")  # 新增代码+HarnessCliUpgrade: 定义 tasks 子命令；若没有这行代码，外部 agent 无法列后台任务。
    tasks_parser.add_argument("--tasks", required=True, help="Task registry directory.")  # 新增代码+HarnessCliUpgrade: tasks 需要任务登记表目录；若没有这行代码，命令没有数据源。
    events_parser = subparsers.add_parser("events", help="Print recent harness events.")  # 新增代码+HarnessCliUpgrade: 定义 events 子命令；若没有这行代码，外部 agent 无法审计事件流。
    events_parser.add_argument("--store", required=True, help="Harness store directory.")  # 新增代码+HarnessCliUpgrade: events 需要 harness store；若没有这行代码，命令找不到 JSONL。
    events_parser.add_argument("--run-id", required=True, help="Harness run id.")  # 新增代码+HarnessCliUpgrade: events 需要 run id；若没有这行代码，命令不知道读取哪个事件文件。
    events_parser.add_argument("--limit", type=int, default=20, help="Maximum events to print.")  # 新增代码+HarnessCliUpgrade: events 支持限制行数；若没有这行代码，大事件日志会刷屏。
    resume_parser = subparsers.add_parser("resume", help="Requeue interrupted harness runs.")  # 新增代码+HarnessCliUpgrade: 定义 resume 子命令；若没有这行代码，中断恢复没有 CLI 入口。
    resume_parser.add_argument("--store", required=True, help="Harness store directory.")  # 新增代码+HarnessCliUpgrade: resume 需要 harness store；若没有这行代码，恢复器无法扫描 run。
    resume_parser.add_argument("--runtime", required=True, help="Runtime command queue directory.")  # 新增代码+HarnessCliUpgrade: resume 需要 runtime queue；若没有这行代码，恢复命令无法入队。
    poll_parser = subparsers.add_parser("poll", help="Poll durable tasks and enqueue notifications.")  # 新增代码+HarnessCliUpgrade: 定义 poll 子命令；若没有这行代码，watchdog 没有命令入口。
    poll_parser.add_argument("--tasks", required=True, help="Task registry directory.")  # 新增代码+HarnessCliUpgrade: poll 需要任务登记表目录；若没有这行代码，无法扫描任务。
    poll_parser.add_argument("--runtime", required=True, help="Runtime command queue directory.")  # 新增代码+HarnessCliUpgrade: poll 需要 runtime queue；若没有这行代码，needs_input 无法回灌。
    poll_parser.add_argument("--outputs", required=True, help="Task output directory.")  # 新增代码+HarnessCliUpgrade: poll 需要输出目录；若没有这行代码，watchdog 无法读取 tail。
    snapshot_parser = subparsers.add_parser("snapshot", help="Print unified learning_agent status snapshot.")  # 新增代码+StatusEcosystem: 定义统一状态快照子命令；若没有这行代码，CLI 只能看局部 harness 状态。
    snapshot_parser.add_argument("--workspace", required=True, help="LearningAgent workspace directory.")  # 新增代码+StatusEcosystem: snapshot 需要工作区根目录；若没有这行代码，聚合器不知道读取哪个项目。
    snapshot_parser.add_argument("--json", action="store_true", help="Print raw JSON snapshot.")  # 新增代码+StatusEcosystem: 支持机器可读 JSON 输出；若没有这行代码，外部 agent 只能解析文本。
    browser_runs_parser = subparsers.add_parser("browser-runs", help="Print browser runtime runs.")  # 新增代码+BrowserStatusStage11: 定义浏览器 run 列表命令；若没有这行代码，CLI 无法单独查看浏览器任务。
    browser_runs_parser.add_argument("--workspace", required=True, help="LearningAgent workspace directory.")  # 新增代码+BrowserStatusStage11: browser-runs 需要工作区；若没有这行代码，命令不知道读取哪个 memory。
    browser_events_parser = subparsers.add_parser("browser-events", help="Print recent browser runtime events.")  # 新增代码+BrowserStatusStage11: 定义浏览器事件命令；若没有这行代码，CLI 无法单独查看浏览器动作流。
    browser_events_parser.add_argument("--workspace", required=True, help="LearningAgent workspace directory.")  # 新增代码+BrowserStatusStage11: browser-events 需要工作区；若没有这行代码，命令不知道读取哪个 memory。
    browser_events_parser.add_argument("--run-id", required=True, help="Browser runtime run id.")  # 新增代码+BrowserStatusStage11: browser-events 需要 run id；若没有这行代码，命令不知道读取哪个事件文件。
    browser_events_parser.add_argument("--limit", type=int, default=20, help="Maximum events to print.")  # 新增代码+BrowserStatusStage11: 支持限制事件数量；若没有这行代码，大事件日志会刷屏。
    provider_status_parser = subparsers.add_parser("provider-status", help="Print browser provider and Chrome extension status.")  # 新增代码+ChromeExtensionStage8: 定义 provider 状态命令；若没有这行代码，CLI 无法单独查看双轨 provider。
    provider_status_parser.add_argument("--workspace", required=True, help="LearningAgent workspace directory.")  # 新增代码+ChromeExtensionStage8: provider-status 需要工作区；若没有这行代码，命令不知道读取哪个 memory。
    return parser  # 新增代码+LongTaskHarness: 返回解析器；若没有这行代码，main 无法解析 argv。


def main(argv: list[str] | None = None) -> int:  # 新增代码+LongTaskHarness: CLI 主入口并返回退出码；若没有这行代码，python -m 调用无法复用。
    parser = build_parser()  # 新增代码+LongTaskHarness: 构造参数解析器；若没有这行代码，argv 无法解析。
    args = parser.parse_args(argv)  # 新增代码+LongTaskHarness: 解析参数；若没有这行代码，命令行输入不会生效。
    store = HarnessStore(Path(args.store)) if hasattr(args, "store") else None  # 修改代码+HarnessCliUpgrade: 只有带 --store 的命令才创建 harness store；若没有这行代码，tasks/poll 这类只读任务命令会因缺 args.store 崩溃。
    if args.command == "enqueue":  # 新增代码+HarnessCliAgentExecution: 处理 enqueue 子命令；若没有这行代码，新建任务请求不会执行。
        try:  # 新增代码+HarnessCliAgentExecution: 捕获用户参数格式错误；若没有这行代码，CLI 会给出不友好的 traceback。
            stages = [_parse_stage_spec(raw_stage) for raw_stage in args.stage]  # 新增代码+HarnessCliAgentExecution: 解析所有阶段参数；若没有这行代码，run 对象没有阶段。
            _apply_success_markers(stages, list(args.success_marker or []))  # 新增代码+HarnessCliAgentExecution: 应用 marker 规则；若没有这行代码，阶段验收缺少用户配置。
        except ValueError as error:  # 新增代码+HarnessCliAgentExecution: 处理参数解析失败；若没有这行代码，错误格式会冒泡成堆栈。
            parser.error(str(error))  # 新增代码+HarnessCliAgentExecution: 用 argparse 风格显示错误；若没有这行代码，用户不知道命令格式。
        run = HarnessRun.create(run_id=str(args.run_id), prompt=str(args.prompt), stages=stages)  # 新增代码+HarnessCliAgentExecution: 构建新 harness run；若没有这行代码，queue 没有可保存对象。
        HarnessQueue(store).enqueue(run)  # 新增代码+HarnessCliAgentExecution: 把任务写入持久队列；若没有这行代码，enqueue 只是内存动作。
        print(run.run_id)  # 新增代码+HarnessCliAgentExecution: 打印 run id 给外部 agent；若没有这行代码，后续自动化不知道查询哪个任务。
        return 0  # 新增代码+HarnessCliAgentExecution: 返回成功退出码；若没有这行代码，调用方无法确认 enqueue 成功。
    if args.command == "run":  # 新增代码+HarnessCliAgentExecution: 处理 run 子命令；若没有这行代码，队列任务无法从 CLI 推进。
        executor = _build_executor(str(args.executor), str(args.workspace) if args.workspace else None, args.max_turns)  # 新增代码+HarnessCliAgentExecution: 根据参数选择执行器；若没有这行代码，runner 没有阶段执行函数。
        runner = HarnessRunner(store=store, executor=executor, verifier=StageVerifier(store.base_dir))  # 新增代码+HarnessCliAgentExecution: 创建 runner；若没有这行代码，CLI 不能执行多阶段任务。
        run = runner.run_to_completion(store.load_run(str(args.run_id))) if args.run_id else runner.run_once(worker_id=str(args.worker_id), lease_seconds=int(args.lease_seconds))  # 新增代码+HarnessCliAgentExecution: 指定 run-id 时直跑，否则从队列领取；若没有这行代码，run 命令不会推进任务。
        if run is None:  # 新增代码+HarnessCliAgentExecution: 处理空队列；若没有这行代码，后续状态渲染会访问空对象。
            print("No queued harness run.")  # 新增代码+HarnessCliAgentExecution: 告诉用户没有任务；若没有这行代码，空队列会静默。
            return 1  # 新增代码+HarnessCliAgentExecution: 空队列返回失败码；若没有这行代码，自动化可能误以为执行成功。
        print(render_harness_status(run, store.read_events(run.run_id)))  # 新增代码+HarnessCliAgentExecution: 打印最终状态；若没有这行代码，用户执行后仍要手动 status。
        return 0 if run.status == "completed" else 1  # 新增代码+HarnessCliAgentExecution: 完成返回 0，失败返回 1；若没有这行代码，外部 agent 无法用退出码判断结果。
    if args.command == "status":  # 新增代码+LongTaskHarness: 处理 status 子命令；若没有这行代码，单任务查询不会执行。
        run = store.load_run(str(args.run_id))  # 新增代码+LongTaskHarness: 读取目标 run；若没有这行代码，状态渲染没有对象。
        print(render_harness_status(run, store.read_events(run.run_id)))  # 新增代码+LongTaskHarness: 打印可读状态；若没有这行代码，CLI 不会给用户结果。
        return 0  # 新增代码+LongTaskHarness: 返回成功退出码；若没有这行代码，调用方无法确认命令成功。
    if args.command == "list":  # 新增代码+LongTaskHarness: 处理 list 子命令；若没有这行代码，任务发现入口不可用。
        for run_id in store.list_run_ids():  # 新增代码+LongTaskHarness: 遍历 run id；若没有这行代码，list 不会输出任何任务。
            print(run_id)  # 新增代码+LongTaskHarness: 打印一个 run id；若没有这行代码，外部 agent 无法读取列表。
        return 0  # 新增代码+LongTaskHarness: 返回成功退出码；若没有这行代码，list 调用方无法确认成功。
    if args.command == "queue":  # 新增代码+HarnessCliUpgrade: 处理 queue 子命令；若没有这行代码，主队列状态无法打印。
        runtime_queue = RuntimeCommandQueue(Path(args.runtime))  # 新增代码+HarnessCliUpgrade: 打开 runtime command queue；若没有这行代码，命令无法读取 prompt/notification。
        run_ids = store.list_run_ids()  # 新增代码+HarnessCliUpgrade: 列出 harness run；若没有这行代码，queue 输出缺少 run 状态。
        print(f"harness_runs={len(run_ids)}")  # 新增代码+HarnessCliUpgrade: 打印 run 总数；若没有这行代码，用户不知道队列规模。
        for run_id in run_ids:  # 新增代码+HarnessCliUpgrade: 遍历 run id；若没有这行代码，具体任务不会显示。
            run = store.load_run(run_id)  # 新增代码+HarnessCliUpgrade: 读取 run 状态；若没有这行代码，输出无法显示 status。
            print(f"run_id={run.run_id} status={run.status} current_stage_index={run.current_stage_index}")  # 新增代码+HarnessCliUpgrade: 打印 run 摘要；若没有这行代码，用户无法判断是否 running/queued。
        commands = runtime_queue.list_commands()  # 新增代码+HarnessCliUpgrade: 读取 runtime 命令；若没有这行代码，prompt/notification 状态不可见。
        print(f"runtime_commands={len(commands)}")  # 新增代码+HarnessCliUpgrade: 打印命令总数；若没有这行代码，用户不知道队列是否为空。
        for command in commands:  # 新增代码+HarnessCliUpgrade: 遍历命令列表；若没有这行代码，具体 command 不会显示。
            print(f"command_id={command.command_id} mode={command.mode} priority={command.priority} status={command.status}")  # 新增代码+HarnessCliUpgrade: 打印命令摘要；若没有这行代码，外部 agent 无法决定下一步。
        return 0  # 新增代码+HarnessCliUpgrade: 返回成功退出码；若没有这行代码，自动化无法确认命令成功。
    if args.command == "tasks":  # 新增代码+HarnessCliUpgrade: 处理 tasks 子命令；若没有这行代码，持久任务状态无法打印。
        registry = TaskRegistry(Path(args.tasks))  # 新增代码+HarnessCliUpgrade: 打开持久任务登记表；若没有这行代码，命令没有任务数据源。
        tasks = registry.list_tasks()  # 新增代码+HarnessCliUpgrade: 读取任务列表；若没有这行代码，无法展示任务。
        print(f"tasks={len(tasks)}")  # 新增代码+HarnessCliUpgrade: 打印任务总数；若没有这行代码，用户不知道是否为空。
        for task in tasks:  # 新增代码+HarnessCliUpgrade: 遍历任务；若没有这行代码，具体任务不会显示。
            output_tail = _tail_file_for_status(task.output_path) or task.output[:200].replace("\r", "\\r").replace("\n", "\\n")  # 新增代码+HarnessStatusAudit: 优先读取 output_path 尾巴并回退记录摘要；若没有这行代码，任务输出不能在 CLI 直接审计。
            print(f"task_id={task.task_id} status={task.status} kind={task.kind} output_path={task.output_path} output_tail={output_tail or '(empty)'}")  # 修改代码+HarnessStatusAudit: 打印任务状态和输出尾巴；若没有这行代码，外部 agent 只能看到路径看不到真实输出。
        return 0  # 新增代码+HarnessCliUpgrade: 返回成功退出码；若没有这行代码，自动化无法确认 tasks 成功。
    if args.command == "events":  # 新增代码+HarnessCliUpgrade: 处理 events 子命令；若没有这行代码，事件审计入口不可用。
        events = store.read_events(str(args.run_id))  # 新增代码+HarnessCliUpgrade: 读取 run 事件；若没有这行代码，命令没有事件数据。
        limit = max(1, int(args.limit))  # 新增代码+HarnessCliUpgrade: 限制至少输出一条；若没有这行代码，limit=0 会让命令看似无结果。
        for event in events[-limit:]:  # 新增代码+HarnessCliUpgrade: 只打印最近 N 条事件；若没有这行代码，长日志会刷屏。
            print(f"{event.get('timestamp', '')} {event.get('event_type', '')} {event.get('payload', {})}")  # 新增代码+HarnessCliUpgrade: 打印事件摘要；若没有这行代码，外部 agent 无法看审计轨迹。
        return 0  # 新增代码+HarnessCliUpgrade: 返回成功退出码；若没有这行代码，自动化无法确认 events 成功。
    if args.command == "resume":  # 新增代码+HarnessCliUpgrade: 处理 resume 子命令；若没有这行代码，中断恢复无法执行。
        runtime_queue = RuntimeCommandQueue(Path(args.runtime))  # 新增代码+HarnessCliUpgrade: 打开 runtime queue；若没有这行代码，恢复命令无法写入。
        restored = InterruptedRunResumer(store=store, command_queue=runtime_queue).enqueue_interrupted_runs()  # 新增代码+HarnessCliUpgrade: 扫描并恢复 interrupted run；若没有这行代码，resume 命令不会做事。
        print(f"restored={restored}")  # 新增代码+HarnessCliUpgrade: 打印恢复数量；若没有这行代码，用户不知道是否恢复成功。
        return 0  # 新增代码+HarnessCliUpgrade: 返回成功退出码；若没有这行代码，自动化无法确认 resume 成功。
    if args.command == "poll":  # 新增代码+HarnessCliUpgrade: 处理 poll 子命令；若没有这行代码，watchdog 无法命令行触发。
        runtime_queue = RuntimeCommandQueue(Path(args.runtime))  # 新增代码+HarnessCliUpgrade: 打开 runtime queue；若没有这行代码，poller 无法写通知。
        output_store = TaskOutputStore(Path(args.outputs))  # 新增代码+HarnessCliUpgrade: 打开任务输出 store；若没有这行代码，poller 无法读取 tail。
        registry = TaskRegistry(Path(args.tasks), output_store=output_store, command_queue=runtime_queue)  # 新增代码+HarnessCliUpgrade: 打开任务登记表并接入输出和队列；若没有这行代码，poller 无法更新任务。
        changed = TaskPoller(task_registry=registry, command_queue=runtime_queue).poll_once()  # 新增代码+HarnessCliUpgrade: 执行一次 poll；若没有这行代码，needs_input 不会生成。
        print(f"changed={changed}")  # 新增代码+HarnessCliUpgrade: 打印变化数量；若没有这行代码，用户不知道 poll 是否发现问题。
        return 0  # 新增代码+HarnessCliUpgrade: 返回成功退出码；若没有这行代码，自动化无法确认 poll 成功。
    if args.command == "snapshot":  # 新增代码+StatusEcosystem: 处理统一状态快照命令；若没有这行代码，CLI 无法同屏显示 run/task/queue/session。
        snapshot = build_status_snapshot(Path(args.workspace))  # 新增代码+StatusEcosystem: 从工作区聚合状态；若没有这行代码，snapshot 命令没有数据。
        if bool(args.json):  # 新增代码+StatusEcosystem: 如果用户请求 JSON 输出；若没有这行代码，机器调用无法拿结构化结果。
            import json  # 新增代码+StatusEcosystem: 延迟导入 JSON 只服务该分支；若没有这行代码，无法序列化快照。
            print(json.dumps(snapshot, ensure_ascii=False, indent=2))  # 新增代码+StatusEcosystem: 打印结构化快照；若没有这行代码，外部 agent 只能解析文本。
        else:  # 新增代码+StatusEcosystem: 默认输出人类可读状态；若没有这行代码，普通用户会看到 JSON 而不易理解。
            print(render_status_snapshot(snapshot), end="")  # 新增代码+StatusEcosystem: 渲染统一状态文本；若没有这行代码，状态 CLI 不友好。
        return 0  # 新增代码+StatusEcosystem: 快照成功返回 0；若没有这行代码，自动化无法判断命令成功。
    if args.command == "browser-runs":  # 新增代码+BrowserStatusStage11: 处理浏览器 run 列表命令；若没有这行代码，CLI 无法查看 browser runtime。
        snapshot = build_status_snapshot(Path(args.workspace))  # 新增代码+BrowserStatusStage11: 使用统一快照读取 browser 区块；若没有这行代码，CLI 会和 SDK/API 分裂。
        browser = snapshot.get("browser", {})  # 新增代码+BrowserStatusStage11: 提取浏览器状态；若没有这行代码，后续字段读取不清楚。
        runs = browser.get("runs", []) if isinstance(browser, dict) else []  # 新增代码+BrowserStatusStage11: 安全读取 run 列表；若没有这行代码，坏快照可能导致异常。
        print(f"browser_runs={len(runs)}")  # 新增代码+BrowserStatusStage11: 打印 browser run 总数；若没有这行代码，用户不知道是否为空。
        for browser_run in runs:  # 新增代码+BrowserStatusStage11: 遍历浏览器 run；若没有这行代码，具体任务不会显示。
            print(f"run_id={browser_run.get('run_id', '')} status={browser_run.get('status', '')} actions={len(browser_run.get('action_ids', []))} observations={len(browser_run.get('observation_ids', []))}")  # 新增代码+BrowserStatusStage11: 打印 run 摘要；若没有这行代码，外部 agent 无法定位浏览器任务。
        return 0  # 新增代码+BrowserStatusStage11: browser-runs 成功返回 0；若没有这行代码，自动化无法判断命令成功。
    if args.command == "browser-events":  # 新增代码+BrowserStatusStage11: 处理浏览器事件命令；若没有这行代码，CLI 无法查看 browser event log。
        browser_store = _browser_store_for_workspace(Path(args.workspace))  # 新增代码+BrowserStatusStage11: 找到 browser runtime store；若没有这行代码，事件读取没有数据源。
        events = browser_store.tail_events(str(args.run_id), limit=max(1, int(args.limit)))  # 新增代码+BrowserStatusStage11: 读取指定 run 的事件尾巴；若没有这行代码，命令不会输出动作流。
        for event in events:  # 新增代码+BrowserStatusStage11: 遍历事件；若没有这行代码，具体事件不会显示。
            print(f"{event.get('timestamp_ms', '')} {event.get('event_type', '')} {event.get('payload', {})}")  # 新增代码+BrowserStatusStage11: 打印事件摘要；若没有这行代码，外部 agent 无法审计浏览器动作。
        return 0  # 新增代码+BrowserStatusStage11: browser-events 成功返回 0；若没有这行代码，自动化无法判断命令成功。
    if args.command == "provider-status":  # 新增代码+ChromeExtensionStage8: 处理浏览器 provider 状态命令；若没有这行代码，CLI 无法查看插件/provider 健康。
        snapshot = build_status_snapshot(Path(args.workspace))  # 新增代码+ChromeExtensionStage8: 使用统一快照读取 provider 状态；若没有这行代码，CLI 会和 SDK/API 分裂。
        browser = snapshot.get("browser", {}) if isinstance(snapshot.get("browser", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 安全读取 browser 区块；若没有这行代码，坏快照会导致异常。
        provider_status = browser.get("provider_status", {}) if isinstance(browser.get("provider_status", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取 provider_status 区块；若没有这行代码，命令没有主要数据。
        providers = provider_status.get("providers", {}) if isinstance(provider_status.get("providers", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取 provider 健康集合；若没有这行代码，三条轨道不会显示。
        extension = provider_status.get("chrome_extension", {}) if isinstance(provider_status.get("chrome_extension", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取插件摘要；若没有这行代码，pending 和权限计数不可见。
        tabs = provider_status.get("tabs", {}) if isinstance(provider_status.get("tabs", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取 tab 摘要；若没有这行代码，active tab 不可见。
        active_tab = tabs.get("active_tab", {}) if isinstance(tabs.get("active_tab", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取 active tab；若没有这行代码，URL 不会显示。
        print("browser_provider_status")  # 新增代码+ChromeExtensionStage8: 输出稳定标题；若没有这行代码，自动化验收难以匹配命令类型。
        for provider_name, provider_health in providers.items():  # 新增代码+ChromeExtensionStage8: 遍历 provider 状态；若没有这行代码，CLI 看不到三条轨道。
            if isinstance(provider_health, dict):  # 新增代码+ChromeExtensionStage8: 只处理结构化健康对象；若没有这行代码，坏状态会报错。
                print(f"provider={provider_name} available={str(bool(provider_health.get('available', False))).lower()} reason={provider_health.get('reason', '')}")  # 新增代码+ChromeExtensionStage8: 打印 provider 健康；若没有这行代码，外部 agent 不能用 CLI 判断可用性。
        print(f"chrome_extension_connected={str(bool(extension.get('connected', False))).lower()} pending_command_count={extension.get('pending_command_count', 0)} permission_event_count={extension.get('permission_event_count', 0)}")  # 新增代码+ChromeExtensionStage8: 打印插件核心计数；若没有这行代码，权限和队列状态不可见。
        print(f"active_tab_url={active_tab.get('url', '')}")  # 新增代码+ChromeExtensionStage8: 打印 active tab URL；若没有这行代码，CLI 不能确认当前页面。
        return 0  # 新增代码+ChromeExtensionStage8: provider-status 成功返回 0；若没有这行代码，自动化无法判断命令成功。
    parser.error("unknown command")  # 新增代码+LongTaskHarness: 未知命令时给出 argparse 错误；若没有这行代码，异常路径不清楚。
    return 2  # 新增代码+LongTaskHarness: 返回命令行错误码；若没有这行代码，静态分析会认为可能无返回。


if __name__ == "__main__":  # 新增代码+StatusEcosystem: 让 python -m learning_agent.harness.cli 真正执行 main；若没有这行代码，CLI 模块会静默退出且没有任何状态输出。
    raise SystemExit(main())  # 新增代码+StatusEcosystem: 把 main 的退出码交给系统；若没有这行代码，自动化无法根据命令退出码判断成功或失败。
