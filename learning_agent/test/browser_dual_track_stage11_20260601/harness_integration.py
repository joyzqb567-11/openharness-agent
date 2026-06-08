"""浏览器运行时到长任务 harness 的投影层。"""  # 新增代码+BrowserHarnessStage11: 说明本模块负责把 browser runtime 接入 harness；若没有这行代码，维护者会误以为这里又是一套新 runtime。
from __future__ import annotations  # 新增代码+BrowserHarnessStage11: 延迟解析类型注解；若没有这行代码，前向类型引用在旧 Python 下更容易出错。

import time  # 新增代码+BrowserHarnessStage11: 生成 harness lease 过期时间；若没有这行代码，browser run 无法进入可恢复的 running/lease 状态。
from pathlib import Path  # 新增代码+BrowserHarnessStage11: 统一处理 workspace 和 store 路径；若没有这行代码，路径拼接会散落成字符串。
from typing import Any  # 新增代码+BrowserHarnessStage11: 支持 browser run、provider decision、flow report 等通用对象；若没有这行代码，类型边界不清楚。

from learning_agent.harness.models import HarnessRun, HarnessStage, VerificationResult, utc_timestamp  # 新增代码+BrowserHarnessStage11: 复用长任务 harness 标准模型；若没有这行代码，browser 会继续落成旁路 dict。
from learning_agent.harness.queue import HarnessQueue  # 新增代码+BrowserHarnessStage11: 复用 harness 队列事件语义；若没有这行代码，browser run 不会留下 queued 审计入口。
from learning_agent.harness.store import HarnessStore  # 新增代码+BrowserHarnessStage11: 复用 harness 持久化 store；若没有这行代码，browser stage/verifier 无法跨进程恢复。


def _short_text(value: Any, limit: int = 800) -> str:  # 新增代码+BrowserHarnessStage11: 截断落盘摘要避免状态文件过大；若没有这行代码，大页面输出可能撑爆 harness JSON。
    text = "" if value is None else str(value)  # 新增代码+BrowserHarnessStage11: 把任意值转成文本摘要；若没有这行代码，None 或对象会让 checkpoint 写入不稳定。
    safe_limit = max(1, int(limit))  # 新增代码+BrowserHarnessStage11: 保证截断长度至少为 1；若没有这行代码，坏 limit 会导致空切片或异常。
    return text[:safe_limit]  # 新增代码+BrowserHarnessStage11: 返回安全长度文本；若没有这行代码，状态输出可能无限增长。


def browser_harness_store_for_workspace(workspace: str | Path) -> HarnessStore:  # 新增代码+BrowserHarnessStage11: 根据 workspace 形态定位 harness store；若没有这行代码，项目根和包目录会读写两套状态。
    root = Path(workspace)  # 新增代码+BrowserHarnessStage11: 规范化 workspace 路径；若没有这行代码，字符串和 Path 混用容易出错。
    direct_store = HarnessStore(root / "memory" / "harness")  # 新增代码+BrowserHarnessStage11: 支持 workspace 已经是 learning_agent 包目录的情况；若没有这行代码，真实 agent 启动方式会读不到 harness。
    package_store = HarnessStore(root / "learning_agent" / "memory" / "harness")  # 新增代码+BrowserHarnessStage11: 支持 workspace 是项目根目录的情况；若没有这行代码，MCP browser server 会把 harness 写到错误位置。
    if root.name.lower() == "learning_agent":  # 新增代码+BrowserHarnessStage11: 明确识别包目录 workspace；若没有这行代码，learning_agent/learning_agent 双重路径可能出现。
        return direct_store  # 新增代码+BrowserHarnessStage11: 包目录模式直接使用 memory/harness；若没有这行代码，真实终端主循环状态会分裂。
    return package_store  # 修改代码+BrowserHarnessStage11: 项目根模式固定写入 learning_agent/memory/harness；若没有这行代码，mirror 初始化早于目录创建时会写到错误 direct store。


class BrowserHarnessMirror:  # 新增代码+BrowserHarnessStage11: 把 browser runtime 生命周期镜像成 harness 生命周期；若没有这个类，接线会散落在 server 各处。
    def __init__(self, workspace: str | Path) -> None:  # 新增代码+BrowserHarnessStage11: 初始化投影器并绑定 workspace；若没有这行代码，调用方无法复用状态路径规则。
        self.workspace = Path(workspace)  # 新增代码+BrowserHarnessStage11: 保存规范化 workspace；若没有这行代码，后续事件 payload 无法说明来源。
        self.store = browser_harness_store_for_workspace(self.workspace)  # 新增代码+BrowserHarnessStage11: 选择和当前 workspace 匹配的 harness store；若没有这行代码，browser 和 harness 会继续分裂。
        self.queue = HarnessQueue(self.store)  # 新增代码+BrowserHarnessStage11: 创建队列 helper 以复用 queued 事件语义；若没有这行代码，task queue 接入缺少审计入口。

    def start_run(self, browser_run: Any, tool_name: str) -> HarnessRun:  # 新增代码+BrowserHarnessStage11: 为 browser run 创建同 id harness run；若没有这行代码，顶层浏览器工具没有 durable harness 根。
        run_id = str(getattr(browser_run, "run_id", "") or "")  # 新增代码+BrowserHarnessStage11: 读取 browser run id；若没有这行代码，harness 无法和 browser runtime 对齐。
        if not run_id:  # 新增代码+BrowserHarnessStage11: 防御缺失 run id 的异常输入；若没有这行代码，空文件名可能污染 store。
            raise ValueError("browser_run.run_id 不能为空")  # 新增代码+BrowserHarnessStage11: 明确拒绝坏输入；若没有这行代码，错误会变成难懂的文件路径异常。
        existing = self.store.try_load_run(run_id)  # 新增代码+BrowserHarnessStage11: 尝试读取已存在 harness run；若没有这行代码，恢复场景会覆盖旧阶段状态。
        if existing is None:  # 新增代码+BrowserHarnessStage11: 没有旧 run 时创建新投影；若没有这行代码，首次浏览器工具不会进入 harness。
            stage = HarnessStage(name=str(tool_name), prompt=f"Browser tool: {tool_name}", max_attempts=1)  # 新增代码+BrowserHarnessStage11: 创建顶层工具阶段；若没有这行代码，harness run 没有可验收 stage。
            run = HarnessRun.create(run_id=run_id, prompt=str(getattr(browser_run, "prompt", "") or f"Browser tool: {tool_name}"), stages=[stage], endpoints=["browser-runtime"])  # 新增代码+BrowserHarnessStage11: 创建同 id harness run；若没有这行代码，browser run 只能在 browser store 里可见。
            self.queue.enqueue(run)  # 新增代码+BrowserHarnessStage11: 写入 queued 事件并保存任务入口；若没有这行代码，task queue 审计链缺少起点。
            run = self.store.load_run(run_id)  # 新增代码+BrowserHarnessStage11: 重新读取 queue 更新后的 run；若没有这行代码，后续运行状态可能基于旧对象。
        else:  # 新增代码+BrowserHarnessStage11: 已存在 run 时进入恢复分支；若没有这行代码，重复同步会误创建状态。
            run = existing  # 新增代码+BrowserHarnessStage11: 使用旧 run 保留已完成 stage；若没有这行代码，checkpoint/resume 证据会丢失。
        if run.status not in {"completed", "failed"}:  # 新增代码+BrowserHarnessStage11: 只有非终态 run 才标记 running；若没有这行代码，已完成 run 可能被重新打开。
            run.status = "running"  # 新增代码+BrowserHarnessStage11: 标记 harness run 正在执行；若没有这行代码，状态 CLI 会以为任务仍在排队。
            run.lease_worker = "browser-runtime"  # 新增代码+BrowserHarnessStage11: 标记本 run 由浏览器 runtime 接管；若没有这行代码，多 worker 审计不知道执行者。
            run.lease_until = time.time() + 3600  # 新增代码+BrowserHarnessStage11: 设置一小时租约方便中断后恢复扫描；若没有这行代码，崩溃占用无法被识别。
            if run.stages:  # 新增代码+BrowserHarnessStage11: 只有存在 stage 时才更新 stage 状态；若没有这行代码，空 stages 会触发索引错误。
                run.stages[min(run.current_stage_index, len(run.stages) - 1)].status = "running"  # 新增代码+BrowserHarnessStage11: 当前阶段标记 running；若没有这行代码，stage 仍显示 pending。
                run.stages[min(run.current_stage_index, len(run.stages) - 1)].started_at = run.stages[min(run.current_stage_index, len(run.stages) - 1)].started_at or utc_timestamp()  # 新增代码+BrowserHarnessStage11: 记录阶段开始时间；若没有这行代码，状态时间线缺少起点。
            run.updated_at = utc_timestamp()  # 新增代码+BrowserHarnessStage11: 刷新 run 更新时间；若没有这行代码，状态页无法判断 run 是否新鲜。
            self.store.save_run(run)  # 新增代码+BrowserHarnessStage11: 保存 running 状态；若没有这行代码，进程中断后无法恢复当前阶段。
            self.store.append_event(run_id, "leased", {"worker_id": "browser-runtime", "lease_seconds": 3600})  # 新增代码+BrowserHarnessStage11: 写入浏览器运行时领取事件；若没有这行代码，task queue 接入没有审计证据。
        self.store.append_event(run_id, "browser_harness_run_started", {"tool_name": str(tool_name), "workspace": str(self.workspace)})  # 新增代码+BrowserHarnessStage11: 写入浏览器 harness 启动事件；若没有这行代码，外部 agent 无法知道 run 来源。
        return run  # 新增代码+BrowserHarnessStage11: 返回最新 harness run；若没有这行代码，调用方无法继续同步后续事件。

    def append_provider_decision(self, run_id: str, decision: Any) -> None:  # 新增代码+BrowserHarnessStage11: 把 provider 决策镜像到 harness event log；若没有这行代码，provider 选择仍只在 browser 旁路事件里。
        if not run_id:  # 新增代码+BrowserHarnessStage11: 没有 run id 时跳过；若没有这行代码，空事件文件名可能污染 store。
            return  # 新增代码+BrowserHarnessStage11: 直接返回表示无 active run；若没有这行代码，内部调用会抛路径异常。
        payload = decision.to_event_payload() if hasattr(decision, "to_event_payload") else {"decision": str(decision)}  # 新增代码+BrowserHarnessStage11: 使用 provider 决策标准 payload；若没有这行代码，harness 事件字段会和 browser 事件不一致。
        self.store.append_event(run_id, "browser_provider_decision", payload)  # 新增代码+BrowserHarnessStage11: 写入 harness provider decision 事件；若没有这行代码，状态 CLI/API 无法复盘 provider 决策。

    def finish_run(self, browser_run: Any, tool_name: str, success: bool, message: str) -> HarnessRun:  # 新增代码+BrowserHarnessStage11: 把 browser run 最终结果同步为 harness verifier；若没有这行代码，browser 完成没有可审计验收。
        run_id = str(getattr(browser_run, "run_id", "") or "")  # 新增代码+BrowserHarnessStage11: 读取 browser run id；若没有这行代码，无法定位 harness run。
        run = self.store.try_load_run(run_id) if run_id else None  # 新增代码+BrowserHarnessStage11: 读取现有 harness run；若没有这行代码，finish 会覆盖恢复状态。
        if run is None:  # 新增代码+BrowserHarnessStage11: 如果 start 阶段缺失则兜底创建；若没有这行代码，少见异常路径会丢最终结果。
            run = self.start_run(browser_run, tool_name)  # 新增代码+BrowserHarnessStage11: 兜底创建同 id run；若没有这行代码，finish 无处落盘。
        stage = self._stage_for_tool(run, tool_name)  # 新增代码+BrowserHarnessStage11: 找到或创建工具阶段；若没有这行代码，结果可能写错 stage。
        existing_failed = any(item.status == "failed" for item in run.stages)  # 新增代码+BrowserHarnessStage11: 检查 flow 同步是否已经标记失败；若没有这行代码，失败 flow 可能被顶层成功文本覆盖。
        final_success = bool(success) and not existing_failed  # 新增代码+BrowserHarnessStage11: 只有工具成功且没有失败阶段才算最终成功；若没有这行代码，部分失败流程会误报完成。
        stage.status = "completed" if final_success else "failed"  # 新增代码+BrowserHarnessStage11: 保存阶段最终状态；若没有这行代码，resume 无法判断是否重跑。
        stage.completed_at = utc_timestamp()  # 新增代码+BrowserHarnessStage11: 保存阶段完成时间；若没有这行代码，审计时间线缺少终点。
        stage.checkpoint = _short_text(message, 800)  # 新增代码+BrowserHarnessStage11: 保存短 checkpoint 摘要；若没有这行代码，恢复时看不到上次输出。
        stage.acceptance = VerificationResult(passed=final_success, checks=self._verifier_checks(browser_run), message="browser runtime verifier passed" if final_success else _short_text(message, 400))  # 新增代码+BrowserHarnessStage11: 写入 verifier 结果；若没有这行代码，完成状态没有验收依据。
        run.status = "completed" if final_success else "failed"  # 新增代码+BrowserHarnessStage11: 保存 run 终态；若没有这行代码，队列可能继续领取已完成浏览器任务。
        run.current_stage_index = len(run.stages) if final_success else max(0, run.stages.index(stage))  # 新增代码+BrowserHarnessStage11: 成功时推进到末尾，失败时停在失败阶段；若没有这行代码，resume 无法定位下一步。
        run.failure_reason = "" if final_success else _short_text(message, 400)  # 新增代码+BrowserHarnessStage11: 失败时保存原因；若没有这行代码，用户只看到 failed 不知道原因。
        run.lease_worker = ""  # 新增代码+BrowserHarnessStage11: 清理浏览器 worker 租约；若没有这行代码，完成任务仍像被占用。
        run.lease_until = 0.0  # 新增代码+BrowserHarnessStage11: 清理租约过期时间；若没有这行代码，状态页会显示无意义旧租约。
        run.updated_at = utc_timestamp()  # 新增代码+BrowserHarnessStage11: 刷新 run 更新时间；若没有这行代码，状态快照无法判断最新结果。
        self.store.save_run(run)  # 新增代码+BrowserHarnessStage11: 保存最终 harness run；若没有这行代码，完成/失败只存在内存。
        self.store.append_event(run.run_id, "browser_harness_stage_completed" if final_success else "browser_harness_stage_failed", {"tool_name": str(tool_name), "message": _short_text(message, 500)})  # 新增代码+BrowserHarnessStage11: 写入阶段收尾事件；若没有这行代码，event log 无法审计最终状态。
        self.store.append_event(run.run_id, "verifier_result", stage.acceptance.to_dict())  # 新增代码+BrowserHarnessStage11: 写入 verifier 事件；若没有这行代码，CLI/API/SDK 不能订阅验收结果。
        return run  # 新增代码+BrowserHarnessStage11: 返回最终 run；若没有这行代码，调用方无法追加诊断。

    def sync_flow_report(self, run_id: str, flow_plan: Any, report: dict[str, Any]) -> HarnessRun | None:  # 新增代码+BrowserHarnessStage11: 把 browser_flow_run 报告同步成 harness 多阶段状态；若没有这行代码，流程 checkpoint 仍和 harness 分裂。
        if not run_id:  # 新增代码+BrowserHarnessStage11: 没有 run id 时跳过同步；若没有这行代码，空 run 会污染 store。
            return None  # 新增代码+BrowserHarnessStage11: 返回 None 表示没有可同步对象；若没有这行代码，调用方无法区分跳过和完成。
        run = self.store.try_load_run(run_id)  # 新增代码+BrowserHarnessStage11: 读取已有 harness run；若没有这行代码，flow stage 无法保留旧状态。
        if run is None:  # 新增代码+BrowserHarnessStage11: 没有 harness run 时跳过；若没有这行代码，sync 会凭空构造不完整任务。
            return None  # 新增代码+BrowserHarnessStage11: 返回 None 让调用方继续原工具输出；若没有这行代码，异常会打断浏览器任务。
        outputs = report.get("outputs", {}) if isinstance(report.get("outputs", {}), dict) else {}  # 新增代码+BrowserHarnessStage11: 读取流程输出字典；若没有这行代码，stage checkpoint 无法同步。
        skipped = set(str(item) for item in report.get("skipped_stage_names", []) if item is not None) if isinstance(report.get("skipped_stage_names", []), list) else set()  # 新增代码+BrowserHarnessStage11: 读取恢复跳过阶段；若没有这行代码，状态页看不到哪些阶段未重跑。
        failed_stage = str(report.get("failed_stage", "") or "")  # 新增代码+BrowserHarnessStage11: 读取失败阶段名；若没有这行代码，失败无法定位到具体 stage。
        old_by_name = {stage.name: stage for stage in run.stages}  # 新增代码+BrowserHarnessStage11: 建立旧 stage 索引以保留时间和验收；若没有这行代码，重复同步会丢历史字段。
        new_stages: list[HarnessStage] = []  # 新增代码+BrowserHarnessStage11: 准备新的 flow stage 列表；若没有这行代码，run 无法替换成真实流程阶段。
        for index, flow_stage in enumerate(getattr(flow_plan, "stages", [])):  # 新增代码+BrowserHarnessStage11: 按流程计划顺序同步 stage；若没有这行代码，harness 阶段顺序会和浏览器流程不一致。
            stage_name = str(getattr(flow_stage, "name", "") or f"stage-{index + 1}")  # 新增代码+BrowserHarnessStage11: 读取稳定阶段名；若没有这行代码，匿名阶段无法进入状态页。
            stage_prompt = f"{getattr(flow_stage, 'tool', '')} {getattr(flow_stage, 'arguments', {})}"  # 新增代码+BrowserHarnessStage11: 保存阶段工具和参数摘要；若没有这行代码，恢复时不知道 stage 做什么。
            stage = old_by_name.get(stage_name) or HarnessStage(name=stage_name, prompt=stage_prompt, max_attempts=1)  # 新增代码+BrowserHarnessStage11: 复用旧阶段或创建新阶段；若没有这行代码，旧 checkpoint 会被重置。
            stage.prompt = stage.prompt or stage_prompt  # 新增代码+BrowserHarnessStage11: 确保阶段 prompt 不为空；若没有这行代码，状态页可能看不到阶段意图。
            if stage_name in outputs or stage_name in skipped:  # 新增代码+BrowserHarnessStage11: 已有输出或本轮跳过都表示阶段已完成；若没有这行代码，恢复跳过阶段会误显示 pending。
                stage.status = "completed"  # 新增代码+BrowserHarnessStage11: 标记阶段完成；若没有这行代码，resume 可能重跑已完成阶段。
                stage.completed_at = stage.completed_at or utc_timestamp()  # 新增代码+BrowserHarnessStage11: 保存完成时间并保留旧值；若没有这行代码，重复同步会刷新历史时间。
                stage.checkpoint = _short_text(outputs.get(stage_name, "skipped by checkpoint"), 800)  # 新增代码+BrowserHarnessStage11: 保存阶段输出或跳过说明；若没有这行代码，用户看不到 checkpoint 依据。
                stage.acceptance = VerificationResult(passed=True, checks=["browser_harness_projection", "browser_flow_checkpoint", "browser_resume_skip"], message="browser flow stage completed")  # 新增代码+BrowserHarnessStage11: 写入阶段 verifier；若没有这行代码，completed 阶段没有验收证据。
            elif stage_name == failed_stage:  # 新增代码+BrowserHarnessStage11: 当前阶段是失败点；若没有这行代码，失败会落不到具体 stage。
                stage.status = "failed"  # 新增代码+BrowserHarnessStage11: 标记阶段失败；若没有这行代码，状态页可能误报 pending。
                stage.completed_at = utc_timestamp()  # 新增代码+BrowserHarnessStage11: 保存失败完成时间；若没有这行代码，审计时间线缺失。
                stage.checkpoint = _short_text(report.get("error", ""), 800)  # 新增代码+BrowserHarnessStage11: 保存失败错误摘要；若没有这行代码，用户不知道卡点原因。
                stage.acceptance = VerificationResult(passed=False, checks=["browser_harness_projection", "browser_flow_checkpoint"], message=_short_text(report.get("error", ""), 400))  # 新增代码+BrowserHarnessStage11: 写入失败 verifier；若没有这行代码，失败状态没有可审计依据。
            else:  # 新增代码+BrowserHarnessStage11: 处理尚未执行到的后续阶段；若没有这行代码，未到达阶段会继承旧状态。
                stage.status = "pending"  # 新增代码+BrowserHarnessStage11: 标记阶段等待执行；若没有这行代码，恢复时下一阶段定位不清楚。
            new_stages.append(stage)  # 新增代码+BrowserHarnessStage11: 保存同步后的阶段；若没有这行代码，run.stages 不会更新。
        run.stages = new_stages or run.stages  # 新增代码+BrowserHarnessStage11: 用 flow 阶段替换顶层工具阶段；若没有这行代码，harness 仍只看到 browser_flow_run 一个粗阶段。
        completed = bool(report.get("completed", False))  # 新增代码+BrowserHarnessStage11: 读取流程是否完整完成；若没有这行代码，run 终态无法判断。
        run.status = "completed" if completed else ("failed" if failed_stage else "running")  # 新增代码+BrowserHarnessStage11: 根据 flow report 更新 run 状态；若没有这行代码，harness run 会和流程 checkpoint 不一致。
        run.current_stage_index = self._first_incomplete_stage_index(run.stages)  # 新增代码+BrowserHarnessStage11: 计算下一阶段索引；若没有这行代码，resume 无法跳过完成阶段。
        run.failure_reason = _short_text(report.get("error", ""), 400) if failed_stage else ""  # 新增代码+BrowserHarnessStage11: 失败时保存原因；若没有这行代码，状态页只有失败没有说明。
        run.updated_at = utc_timestamp()  # 新增代码+BrowserHarnessStage11: 刷新 run 更新时间；若没有这行代码，状态快照可能显示旧数据。
        self.store.save_run(run)  # 新增代码+BrowserHarnessStage11: 保存 flow 同步结果；若没有这行代码，阶段 checkpoint 仍只存在内存。
        self.store.append_event(run.run_id, "browser_flow_report_synced", {"flow_id": str(getattr(flow_plan, "flow_id", "")), "completed": completed, "skipped_stage_names": sorted(skipped), "failed_stage": failed_stage})  # 新增代码+BrowserHarnessStage11: 写入 flow 同步事件；若没有这行代码，恢复跳过行为不可审计。
        self.store.append_event(run.run_id, "verifier_result", {"passed": completed, "checks": ["browser_harness_projection", "browser_flow_checkpoint"], "message": "browser flow verifier passed" if completed else _short_text(report.get("error", ""), 400)})  # 新增代码+BrowserHarnessStage11: 写入流程级 verifier 事件；若没有这行代码，CLI/API 无法快速看到流程验收结果。
        return run  # 新增代码+BrowserHarnessStage11: 返回同步后的 run；若没有这行代码，调用方无法测试或追加处理。

    def _stage_for_tool(self, run: HarnessRun, tool_name: str) -> HarnessStage:  # 新增代码+BrowserHarnessStage11: 找到顶层工具 stage；若没有这行代码，finish_run 会重复创建阶段。
        for stage in run.stages:  # 新增代码+BrowserHarnessStage11: 遍历已有阶段；若没有这行代码，无法复用 start_run 创建的 stage。
            if stage.name == tool_name:  # 新增代码+BrowserHarnessStage11: 匹配同名工具阶段；若没有这行代码，工具结果可能写到错误阶段。
                return stage  # 新增代码+BrowserHarnessStage11: 返回匹配阶段；若没有这行代码，调用方拿不到目标对象。
        stage = HarnessStage(name=str(tool_name), prompt=f"Browser tool: {tool_name}", max_attempts=1)  # 新增代码+BrowserHarnessStage11: 缺失时创建兜底阶段；若没有这行代码，异常路径会丢结果。
        run.stages.append(stage)  # 新增代码+BrowserHarnessStage11: 把兜底阶段加入 run；若没有这行代码，保存 run 时不会包含该阶段。
        return stage  # 新增代码+BrowserHarnessStage11: 返回兜底阶段；若没有这行代码，finish_run 无法继续。

    def _verifier_checks(self, browser_run: Any) -> list[str]:  # 新增代码+BrowserHarnessStage11: 生成浏览器 stage 的验收检查项；若没有这行代码，verifier 只能保存空列表。
        checks = ["browser_harness_projection", "browser_runtime_run", "browser_event_log"]  # 新增代码+BrowserHarnessStage11: 基础检查表示 browser run 已进入 harness；若没有这行代码，验收来源不可见。
        if getattr(browser_run, "action_ids", []):  # 新增代码+BrowserHarnessStage11: 如果 browser run 有 action；若没有这行代码，动作执行器接入无法反映在 verifier。
            checks.append("browser_action_executor")  # 新增代码+BrowserHarnessStage11: 记录 action executor 检查；若没有这行代码，状态页不知道动作层已落盘。
        if getattr(browser_run, "observation_ids", []):  # 新增代码+BrowserHarnessStage11: 如果 browser run 有 observation；若没有这行代码，页面证据接入无法反映在 verifier。
            checks.append("browser_observation_store")  # 新增代码+BrowserHarnessStage11: 记录 observation store 检查；若没有这行代码，验收不会说明页面证据存在。
        return checks  # 新增代码+BrowserHarnessStage11: 返回检查项列表；若没有这行代码，VerificationResult 无法构造完整证据。

    def _first_incomplete_stage_index(self, stages: list[HarnessStage]) -> int:  # 新增代码+BrowserHarnessStage11: 计算第一个未完成阶段索引；若没有这行代码，resume 会从错误位置继续。
        for index, stage in enumerate(stages):  # 新增代码+BrowserHarnessStage11: 按顺序扫描阶段；若没有这行代码，无法保持流程顺序。
            if stage.status != "completed":  # 新增代码+BrowserHarnessStage11: 找到第一个未完成阶段；若没有这行代码，失败或 pending 阶段会被跳过。
                return index  # 新增代码+BrowserHarnessStage11: 返回可恢复索引；若没有这行代码，调用方不知道下一步。
        return len(stages)  # 新增代码+BrowserHarnessStage11: 全部完成时索引落在末尾；若没有这行代码，completed run 可能指向最后一个阶段重跑。
