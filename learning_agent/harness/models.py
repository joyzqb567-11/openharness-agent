"""长任务 harness 的持久化数据模型。"""  # 新增代码+LongTaskHarness: 说明本文件只放可落盘的数据结构；若没有这行代码，维护者不清楚模型层边界。

from __future__ import annotations  # 新增代码+LongTaskHarness: 延迟解析类型注解；若没有这行代码，类之间互相引用时更容易受定义顺序影响。

import copy  # 新增代码+LongTaskHarness: 序列化时复制可变列表和字典；若没有这行代码，外部修改可能污染已保存状态。
import time  # 新增代码+LongTaskHarness: 生成时间戳和租约时间；若没有这行代码，任务状态无法记录发生时间。
from dataclasses import dataclass, field  # 新增代码+LongTaskHarness: 用 dataclass 减少样板代码；若没有这行代码，模型类需要手写大量初始化逻辑。
from typing import Any  # 新增代码+LongTaskHarness: JSON 载荷需要通用类型；若没有这行代码，事件 payload 类型边界不清楚。


def utc_timestamp() -> str:  # 新增代码+LongTaskHarness: 生成统一 UTC 文本时间；若没有这行代码，审计事件会混用不同时间格式。
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())  # 新增代码+LongTaskHarness: 返回秒级 UTC 时间；若没有这行代码，状态文件缺少稳定可读时间。


@dataclass  # 新增代码+LongTaskHarness: 自动生成 VerificationResult 初始化方法；若没有这行代码，验收结果对象要手写构造器。
class VerificationResult:  # 新增代码+LongTaskHarness: 表示一个阶段验收结果；若没有这个类，验收只能散落成松散字典。
    passed: bool = False  # 新增代码+LongTaskHarness: 保存验收是否通过；若没有这行代码，runner 无法判断是否进入下一阶段。
    checks: list[str] = field(default_factory=list)  # 新增代码+LongTaskHarness: 保存已执行检查项；若没有这行代码，失败后无法审计检查了什么。
    message: str = ""  # 新增代码+LongTaskHarness: 保存可读结论；若没有这行代码，用户只能看到布尔值而不知道原因。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+LongTaskHarness: 把验收结果转成 JSON 字典；若没有这行代码，store 无法稳定保存结果。
        return {"passed": self.passed, "checks": list(self.checks), "message": self.message}  # 新增代码+LongTaskHarness: 返回复制后的字段；若没有这行代码，外部可变列表可能污染对象。

    @classmethod  # 新增代码+LongTaskHarness: 提供从 JSON 字典恢复对象的入口；若没有这行代码，resume 只能处理原始 dict。
    def from_dict(cls, payload: dict[str, Any] | None) -> "VerificationResult":  # 新增代码+LongTaskHarness: 从持久化数据恢复验收结果；若没有这行代码，坏数据会让恢复逻辑重复兜底。
        safe_payload = payload if isinstance(payload, dict) else {}  # 新增代码+LongTaskHarness: 非字典时回退空数据；若没有这行代码，损坏状态文件会直接崩溃。
        raw_checks = safe_payload.get("checks", [])  # 新增代码+LongTaskHarness: 读取检查项列表；若没有这行代码，验收细节会丢失。
        checks = [str(item) for item in raw_checks] if isinstance(raw_checks, list) else []  # 新增代码+LongTaskHarness: 规范化检查项为字符串列表；若没有这行代码，状态文件里的异常类型会污染输出。
        return cls(passed=bool(safe_payload.get("passed", False)), checks=checks, message=str(safe_payload.get("message", "")))  # 新增代码+LongTaskHarness: 返回稳定结果对象；若没有这行代码，调用方拿不到统一类型。


@dataclass  # 新增代码+LongTaskHarness: 自动生成 HarnessAttempt 初始化方法；若没有这行代码，尝试记录会有大量重复构造代码。
class HarnessAttempt:  # 新增代码+LongTaskHarness: 表示某阶段的一次执行尝试；若没有这个类，重试历史无法审计。
    attempt_number: int  # 新增代码+LongTaskHarness: 保存第几次尝试；若没有这行代码，用户不知道失败是否已经重试过。
    status: str  # 新增代码+LongTaskHarness: 保存 running/completed/failed 状态；若没有这行代码，尝试结果无法判断。
    endpoint: str = ""  # 新增代码+LongTaskHarness: 保存当次使用的 endpoint；若没有这行代码，端点恢复无法复盘。
    output: str = ""  # 新增代码+LongTaskHarness: 保存当次输出摘要；若没有这行代码，验收依据难以追踪。
    error: str = ""  # 新增代码+LongTaskHarness: 保存当次错误；若没有这行代码，失败原因会丢失。
    started_at: str = field(default_factory=utc_timestamp)  # 新增代码+LongTaskHarness: 保存尝试开始时间；若没有这行代码，耗时和顺序无法审计。
    completed_at: str = ""  # 新增代码+LongTaskHarness: 保存尝试结束时间；若没有这行代码，无法判断尝试是否收尾。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+LongTaskHarness: 把尝试记录转成 JSON 字典；若没有这行代码，store 无法保存重试历史。
        return {"attempt_number": self.attempt_number, "status": self.status, "endpoint": self.endpoint, "output": self.output, "error": self.error, "started_at": self.started_at, "completed_at": self.completed_at}  # 新增代码+LongTaskHarness: 返回完整尝试字段；若没有这行代码，恢复后会缺少审计信息。

    @classmethod  # 新增代码+LongTaskHarness: 提供从 JSON 恢复尝试记录的入口；若没有这行代码，stage 恢复需要手写解析。
    def from_dict(cls, payload: dict[str, Any]) -> "HarnessAttempt":  # 新增代码+LongTaskHarness: 从字典恢复一次尝试；若没有这行代码，重启后尝试历史只能以 dict 存在。
        return cls(attempt_number=int(payload.get("attempt_number", 0)), status=str(payload.get("status", "")), endpoint=str(payload.get("endpoint", "")), output=str(payload.get("output", "")), error=str(payload.get("error", "")), started_at=str(payload.get("started_at", "")), completed_at=str(payload.get("completed_at", "")))  # 新增代码+LongTaskHarness: 兜底恢复字段；若没有这行代码，旧状态文件字段缺失会导致崩溃。


@dataclass  # 新增代码+LongTaskHarness: 自动生成 HarnessStage 初始化方法；若没有这行代码，阶段定义会难以维护。
class HarnessStage:  # 新增代码+LongTaskHarness: 表示长任务中的一个可验收阶段；若没有这个类，任务无法拆成阶段恢复。
    name: str  # 新增代码+LongTaskHarness: 保存阶段名称；若没有这行代码，状态输出无法说明当前跑到哪一步。
    prompt: str  # 新增代码+LongTaskHarness: 保存阶段执行提示；若没有这行代码，runner 不知道阶段要做什么。
    success_markers: list[str] = field(default_factory=list)  # 新增代码+LongTaskHarness: 保存文本成功标记；若没有这行代码，阶段验收缺少确定性条件。
    required_artifacts: list[str] = field(default_factory=list)  # 新增代码+LongTaskHarness: 保存必需产物路径；若没有这行代码，文件型成果无法验收。
    artifact_contains: dict[str, str] = field(default_factory=dict)  # 新增代码+VerifierUpgrade: 保存 artifact 必须包含的文本；若没有这行代码，文件存在但内容错误也会误通过。
    json_schema_artifacts: dict[str, dict[str, Any]] = field(default_factory=dict)  # 新增代码+VerifierUpgrade: 保存 JSON artifact 的轻量 schema 要求；若没有这行代码，result.json 结构缺字段也可能误通过。
    expected_command_exit_codes: dict[str, int] = field(default_factory=dict)  # 新增代码+VerifierUpgrade: 保存命令名到期望退出码；若没有这行代码，自动化检查失败无法进入阶段门禁。
    expected_event_sequence: list[str] = field(default_factory=list)  # 新增代码+VerifierUpgrade: 保存期望事件顺序；若没有这行代码，事件流缺失或乱序无法被 verifier 发现。
    acceptance_result_artifacts: list[str] = field(default_factory=list)  # 新增代码+VerifierUpgrade: 保存真实验收 result.json 路径；若没有这行代码，acceptance_controller 证据无法成为阶段验收门禁。
    max_attempts: int = 1  # 新增代码+LongTaskHarness: 保存最大尝试次数；若没有这行代码，失败后可能无限重试或完全不重试。
    status: str = "pending"  # 新增代码+LongTaskHarness: 保存 pending/running/completed/failed；若没有这行代码，阶段状态不可见。
    attempts: list[HarnessAttempt] = field(default_factory=list)  # 新增代码+LongTaskHarness: 保存阶段尝试历史；若没有这行代码，重试过程不可审计。
    acceptance: VerificationResult = field(default_factory=VerificationResult)  # 新增代码+LongTaskHarness: 保存阶段验收结果；若没有这行代码，完成状态没有证据。
    checkpoint: str = ""  # 新增代码+LongTaskHarness: 保存阶段 checkpoint 摘要；若没有这行代码，恢复时不知道已产出什么。
    started_at: str = ""  # 新增代码+LongTaskHarness: 保存阶段开始时间；若没有这行代码，状态页无法显示阶段时间线。
    completed_at: str = ""  # 新增代码+LongTaskHarness: 保存阶段完成时间；若没有这行代码，审计时无法判断阶段何时结束。

    def safe_max_attempts(self) -> int:  # 新增代码+LongTaskHarness: 返回至少为 1 的尝试次数；若没有这行代码，max_attempts=0 会让阶段永远不执行。
        return max(1, int(self.max_attempts))  # 新增代码+LongTaskHarness: 对外部输入做安全兜底；若没有这行代码，坏配置会破坏 runner。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+LongTaskHarness: 把阶段转成 JSON 字典；若没有这行代码，store 无法保存阶段状态。
        return {"name": self.name, "prompt": self.prompt, "success_markers": list(self.success_markers), "required_artifacts": list(self.required_artifacts), "artifact_contains": dict(self.artifact_contains), "json_schema_artifacts": copy.deepcopy(self.json_schema_artifacts), "expected_command_exit_codes": dict(self.expected_command_exit_codes), "expected_event_sequence": list(self.expected_event_sequence), "acceptance_result_artifacts": list(self.acceptance_result_artifacts), "max_attempts": self.safe_max_attempts(), "status": self.status, "attempts": [attempt.to_dict() for attempt in self.attempts], "acceptance": self.acceptance.to_dict(), "checkpoint": self.checkpoint, "started_at": self.started_at, "completed_at": self.completed_at}  # 修改代码+VerifierUpgrade: 返回增强验收字段；若没有这行代码，重启后 artifact 内容、JSON schema、命令和事件门禁会丢失。

    @classmethod  # 新增代码+LongTaskHarness: 提供从 JSON 字典恢复阶段的入口；若没有这行代码，run 恢复需要重复解析阶段列表。
    def from_dict(cls, payload: dict[str, Any]) -> "HarnessStage":  # 新增代码+LongTaskHarness: 从持久化字段恢复阶段对象；若没有这行代码，阶段状态不能跨进程恢复。
        raw_attempts = payload.get("attempts", [])  # 新增代码+LongTaskHarness: 读取尝试记录；若没有这行代码，重试历史会丢失。
        attempts = [HarnessAttempt.from_dict(item) for item in raw_attempts] if isinstance(raw_attempts, list) else []  # 新增代码+LongTaskHarness: 安全恢复尝试列表；若没有这行代码，坏 attempts 字段会让恢复失败。
        artifact_contains = payload.get("artifact_contains", {}) if isinstance(payload.get("artifact_contains", {}), dict) else {}  # 新增代码+VerifierUpgrade: 安全读取 artifact 内容断言；若没有这行代码，坏字段会污染 verifier。
        json_schema_artifacts = payload.get("json_schema_artifacts", {}) if isinstance(payload.get("json_schema_artifacts", {}), dict) else {}  # 新增代码+VerifierUpgrade: 安全读取 JSON schema 断言；若没有这行代码，重启后 schema 门禁会丢失。
        expected_command_exit_codes = payload.get("expected_command_exit_codes", {}) if isinstance(payload.get("expected_command_exit_codes", {}), dict) else {}  # 新增代码+VerifierUpgrade: 安全读取退出码断言；若没有这行代码，命令门禁恢复不稳定。
        return cls(name=str(payload.get("name", "")), prompt=str(payload.get("prompt", "")), success_markers=[str(item) for item in payload.get("success_markers", [])] if isinstance(payload.get("success_markers", []), list) else [], required_artifacts=[str(item) for item in payload.get("required_artifacts", [])] if isinstance(payload.get("required_artifacts", []), list) else [], artifact_contains={str(key): str(value) for key, value in artifact_contains.items()}, json_schema_artifacts={str(key): value if isinstance(value, dict) else {} for key, value in json_schema_artifacts.items()}, expected_command_exit_codes={str(key): int(value) for key, value in expected_command_exit_codes.items()}, expected_event_sequence=[str(item) for item in payload.get("expected_event_sequence", [])] if isinstance(payload.get("expected_event_sequence", []), list) else [], acceptance_result_artifacts=[str(item) for item in payload.get("acceptance_result_artifacts", [])] if isinstance(payload.get("acceptance_result_artifacts", []), list) else [], max_attempts=max(1, int(payload.get("max_attempts", 1))), status=str(payload.get("status", "pending")), attempts=attempts, acceptance=VerificationResult.from_dict(payload.get("acceptance")), checkpoint=str(payload.get("checkpoint", "")), started_at=str(payload.get("started_at", "")), completed_at=str(payload.get("completed_at", "")))  # 修改代码+VerifierUpgrade: 返回包含增强验收字段的阶段对象；若没有这行代码，runner 恢复后会丢失真实验收门禁。


@dataclass  # 新增代码+LongTaskHarness: 自动生成 HarnessRun 初始化方法；若没有这行代码，任务 run 对象构造会重复。
class HarnessRun:  # 新增代码+LongTaskHarness: 表示一个可恢复的长任务运行；若没有这个类，harness 没有统一状态根对象。
    run_id: str  # 新增代码+LongTaskHarness: 保存运行编号；若没有这行代码，队列和事件无法定位同一个任务。
    prompt: str  # 新增代码+LongTaskHarness: 保存用户原始任务；若没有这行代码，恢复后不知道任务目标。
    stages: list[HarnessStage]  # 新增代码+LongTaskHarness: 保存阶段列表；若没有这行代码，任务不能分阶段执行。
    endpoints: list[str] = field(default_factory=lambda: ["default"])  # 新增代码+LongTaskHarness: 保存可用 endpoint 列表；若没有这行代码，端点恢复无法轮换。
    status: str = "queued"  # 新增代码+LongTaskHarness: 保存 queued/running/completed/failed；若没有这行代码，队列无法判断任务状态。
    current_stage_index: int = 0  # 新增代码+LongTaskHarness: 保存当前阶段索引；若没有这行代码，恢复时可能从头重跑。
    endpoint_index: int = 0  # 新增代码+LongTaskHarness: 保存当前 endpoint 索引；若没有这行代码，失败后无法切换 endpoint。
    failure_reason: str = ""  # 新增代码+LongTaskHarness: 保存最终失败原因；若没有这行代码，用户看不到为什么停下。
    lease_worker: str = ""  # 新增代码+LongTaskHarness: 保存当前领取任务的 worker；若没有这行代码，多个 agent 可能重复执行同一任务。
    lease_until: float = 0.0  # 新增代码+LongTaskHarness: 保存租约过期时间；若没有这行代码，崩溃 worker 占住任务后无法释放。
    created_at: str = field(default_factory=utc_timestamp)  # 新增代码+LongTaskHarness: 保存创建时间；若没有这行代码，用户无法判断任务何时开始。
    updated_at: str = field(default_factory=utc_timestamp)  # 新增代码+LongTaskHarness: 保存更新时间；若没有这行代码，状态页无法判断信息新旧。

    @classmethod  # 新增代码+LongTaskHarness: 提供统一创建 run 的入口；若没有这行代码，调用方要重复设置默认值。
    def create(cls, run_id: str, prompt: str, stages: list[HarnessStage], endpoints: list[str] | None = None) -> "HarnessRun":  # 新增代码+LongTaskHarness: 创建新的长任务 run；若没有这行代码，测试和 CLI 构造会不一致。
        safe_endpoints = list(endpoints or ["default"])  # 新增代码+LongTaskHarness: 没传 endpoint 时使用 default；若没有这行代码，current_endpoint 可能访问空列表。
        return cls(run_id=run_id, prompt=prompt, stages=copy.deepcopy(stages), endpoints=safe_endpoints)  # 新增代码+LongTaskHarness: 返回带深拷贝阶段的 run；若没有这行代码，外部修改 stages 会污染 run。

    def current_endpoint(self) -> str:  # 新增代码+LongTaskHarness: 返回当前 endpoint 名称；若没有这行代码，executor 无法知道应使用哪个端点。
        if not self.endpoints:  # 新增代码+LongTaskHarness: 防御空 endpoint 列表；若没有这行代码，坏状态文件会触发索引错误。
            return "default"  # 新增代码+LongTaskHarness: 空列表时兜底 default；若没有这行代码，恢复流程会崩溃。
        return self.endpoints[self.endpoint_index % len(self.endpoints)]  # 新增代码+LongTaskHarness: 按索引取 endpoint 并防越界；若没有这行代码，轮换后可能访问越界。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+LongTaskHarness: 把 run 转成 JSON 字典；若没有这行代码，store 无法落盘任务状态。
        return {"run_id": self.run_id, "prompt": self.prompt, "stages": [stage.to_dict() for stage in self.stages], "endpoints": list(self.endpoints), "status": self.status, "current_stage_index": self.current_stage_index, "endpoint_index": self.endpoint_index, "failure_reason": self.failure_reason, "lease_worker": self.lease_worker, "lease_until": self.lease_until, "created_at": self.created_at, "updated_at": self.updated_at}  # 新增代码+LongTaskHarness: 返回完整 run 字段；若没有这行代码，恢复和可视化会缺数据。

    @classmethod  # 新增代码+LongTaskHarness: 提供从 JSON 字典恢复 run 的入口；若没有这行代码，store.load_run 会返回松散 dict。
    def from_dict(cls, payload: dict[str, Any]) -> "HarnessRun":  # 新增代码+LongTaskHarness: 从持久化字段恢复 run；若没有这行代码，重启恢复无法重建对象。
        raw_stages = payload.get("stages", [])  # 新增代码+LongTaskHarness: 读取阶段列表；若没有这行代码，run 会丢失阶段状态。
        stages = [HarnessStage.from_dict(item) for item in raw_stages] if isinstance(raw_stages, list) else []  # 新增代码+LongTaskHarness: 安全恢复阶段对象；若没有这行代码，坏 stages 字段会导致崩溃。
        endpoints = [str(item) for item in payload.get("endpoints", ["default"])] if isinstance(payload.get("endpoints", []), list) else ["default"]  # 新增代码+LongTaskHarness: 安全恢复 endpoint 列表；若没有这行代码，端点轮换可能拿到错误类型。
        return cls(run_id=str(payload.get("run_id", "")), prompt=str(payload.get("prompt", "")), stages=stages, endpoints=endpoints or ["default"], status=str(payload.get("status", "queued")), current_stage_index=int(payload.get("current_stage_index", 0)), endpoint_index=int(payload.get("endpoint_index", 0)), failure_reason=str(payload.get("failure_reason", "")), lease_worker=str(payload.get("lease_worker", "")), lease_until=float(payload.get("lease_until", 0.0)), created_at=str(payload.get("created_at", "")), updated_at=str(payload.get("updated_at", "")))  # 新增代码+LongTaskHarness: 返回完整 run 对象；若没有这行代码，runner 无法继续历史任务。
