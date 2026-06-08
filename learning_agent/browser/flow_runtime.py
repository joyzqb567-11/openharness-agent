"""浏览器流程运行时，按阶段执行并保存 checkpoint 以支持恢复。"""  # 新增代码+BrowserFlowStage8: 说明本模块负责流程执行和恢复；若没有这行代码，运行时用途不清楚。

from __future__ import annotations  # 新增代码+BrowserFlowStage8: 延迟解析类型注解；若没有这行代码，回调类型更脆弱。

from collections.abc import Callable  # 新增代码+BrowserFlowStage8: 标注阶段 executor 回调；若没有这行代码，类型边界不清楚。
from pathlib import Path  # 新增代码+BrowserFlowStage8: 管理 checkpoint 文件路径；若没有这行代码，路径拼接不稳定。
from typing import Any  # 新增代码+BrowserFlowStage8: 报告和 checkpoint 是通用 JSON；若没有这行代码，类型边界不清楚。

from learning_agent.browser.flow_schema import BrowserFlowPlan, BrowserFlowStage  # 新增代码+BrowserFlowStage8: 导入流程协议对象；若没有这行代码，runtime 只能处理松散字典。
from learning_agent.runtime.files import atomic_write_json, read_json_or_default  # 新增代码+BrowserFlowStage8: 复用安全 JSON 写读；若没有这行代码，checkpoint 可能半写损坏。


class BrowserFlowRuntime:  # 新增代码+BrowserFlowStage8: 管理浏览器多阶段流程执行；若没有这个类，flow_run 无法恢复已完成阶段。
    def __init__(self, checkpoint_dir: str | Path) -> None:  # 新增代码+BrowserFlowStage8: 初始化 checkpoint 目录；若没有这行代码，调用方无法指定持久位置。
        self.checkpoint_dir = Path(checkpoint_dir)  # 新增代码+BrowserFlowStage8: 规范化目录路径；若没有这行代码，字符串路径后续操作不稳定。

    def checkpoint_path(self, flow_id: str) -> Path:  # 新增代码+BrowserFlowStage8: 计算流程 checkpoint 文件路径；若没有这行代码，读写路径可能不一致。
        return self.checkpoint_dir / f"{flow_id}.json"  # 新增代码+BrowserFlowStage8: 返回稳定 checkpoint 文件；若没有这行代码，resume 找不到旧进度。

    def load_checkpoint(self, flow_id: str) -> dict[str, Any]:  # 新增代码+BrowserFlowStage8: 读取流程 checkpoint；若没有这行代码，恢复无法知道已完成阶段。
        payload = read_json_or_default(self.checkpoint_path(flow_id), {})  # 新增代码+BrowserFlowStage8: 容错读取 JSON；若没有这行代码，缺文件会报错。
        return payload if isinstance(payload, dict) else {}  # 新增代码+BrowserFlowStage8: 坏根对象降级为空；若没有这行代码，坏 checkpoint 会拖垮运行。

    def save_checkpoint(self, flow_id: str, checkpoint: dict[str, Any]) -> Path:  # 新增代码+BrowserFlowStage8: 保存流程 checkpoint；若没有这行代码，中断后无法恢复。
        return atomic_write_json(self.checkpoint_path(flow_id), checkpoint)  # 新增代码+BrowserFlowStage8: 原子写 checkpoint；若没有这行代码，崩溃可能留下半截 JSON。

    def run(self, flow: BrowserFlowPlan, executor: Callable[[BrowserFlowStage], str]) -> dict[str, Any]:  # 新增代码+BrowserFlowStage8: 执行或恢复流程；若没有这行代码，复杂网站任务无法阶段化。
        checkpoint = self.load_checkpoint(flow.flow_id)  # 新增代码+BrowserFlowStage8: 读取旧 checkpoint；若没有这行代码，resume 会重跑所有阶段。
        completed_stage_names = list(checkpoint.get("completed_stage_names", [])) if isinstance(checkpoint.get("completed_stage_names", []), list) else []  # 新增代码+BrowserFlowStage8: 读取已完成阶段名；若没有这行代码，跳过逻辑没有依据。
        outputs = dict(checkpoint.get("outputs", {})) if isinstance(checkpoint.get("outputs", {}), dict) else {}  # 新增代码+BrowserFlowStage8: 读取历史阶段输出；若没有这行代码，resume 报告会丢旧结果。
        skipped_stage_names: list[str] = []  # 新增代码+BrowserFlowStage8: 保存本次跳过阶段；若没有这行代码，用户不知道恢复跳过了什么。
        failed_stage = ""  # 新增代码+BrowserFlowStage8: 保存失败阶段名；若没有这行代码，报告缺少卡点。
        error_message = ""  # 新增代码+BrowserFlowStage8: 保存失败原因；若没有这行代码，用户看不到错误。
        for stage in flow.stages:  # 新增代码+BrowserFlowStage8: 按顺序执行阶段；若没有这行代码，流程没有动作。
            if stage.name in completed_stage_names:  # 新增代码+BrowserFlowStage8: 已完成阶段直接跳过；若没有这行代码，恢复会重复提交或点击。
                skipped_stage_names.append(stage.name)  # 新增代码+BrowserFlowStage8: 记录跳过阶段；若没有这行代码，恢复报告不透明。
                continue  # 新增代码+BrowserFlowStage8: 跳到下一阶段；若没有这行代码，已完成阶段仍会执行。
            try:  # 新增代码+BrowserFlowStage8: 捕获阶段执行失败；若没有这行代码，失败报告无法结构化保存。
                output = executor(stage)  # 新增代码+BrowserFlowStage8: 调用阶段执行器；若没有这行代码，流程不会真正推进。
                outputs[stage.name] = str(output)  # 新增代码+BrowserFlowStage8: 保存阶段输出；若没有这行代码，后续验收无法查看结果。
                completed_stage_names.append(stage.name)  # 新增代码+BrowserFlowStage8: 标记阶段完成；若没有这行代码，resume 会重跑该阶段。
                self.save_checkpoint(flow.flow_id, {"flow_id": flow.flow_id, "completed_stage_names": completed_stage_names, "outputs": outputs, "status": "running"})  # 新增代码+BrowserFlowStage8: 每阶段后立即落盘；若没有这行代码，中断会丢进度。
            except Exception as error:  # 新增代码+BrowserFlowStage8: 捕获执行器错误；若没有这行代码，checkpoint 无法记录失败。
                failed_stage = stage.name  # 新增代码+BrowserFlowStage8: 保存失败阶段；若没有这行代码，报告不知道卡哪一步。
                error_message = str(error)  # 新增代码+BrowserFlowStage8: 保存失败信息；若没有这行代码，用户看不到异常原因。
                self.save_checkpoint(flow.flow_id, {"flow_id": flow.flow_id, "completed_stage_names": completed_stage_names, "outputs": outputs, "status": "failed", "failed_stage": failed_stage, "error": error_message})  # 新增代码+BrowserFlowStage8: 保存失败 checkpoint；若没有这行代码，恢复前无法审计失败。
                if not flow.continue_on_error:  # 新增代码+BrowserFlowStage8: 默认失败停止；若没有这行代码，流程可能在错误页面上继续误操作。
                    return {"completed": False, "flow_id": flow.flow_id, "failed_stage": failed_stage, "error": error_message, "outputs": outputs, "skipped_stage_names": skipped_stage_names}  # 新增代码+BrowserFlowStage8: 返回失败报告；若没有这行代码，调用方无法处理失败。
        self.save_checkpoint(flow.flow_id, {"flow_id": flow.flow_id, "completed_stage_names": completed_stage_names, "outputs": outputs, "status": "completed"})  # 新增代码+BrowserFlowStage8: 保存完成 checkpoint；若没有这行代码，后续 resume 不知道流程完成。
        return {"completed": failed_stage == "", "flow_id": flow.flow_id, "outputs": outputs, "skipped_stage_names": skipped_stage_names, "failed_stage": failed_stage, "error": error_message}  # 新增代码+BrowserFlowStage8: 返回结构化流程报告；若没有这行代码，调用方拿不到结果。
