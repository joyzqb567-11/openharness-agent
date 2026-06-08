"""长任务 harness 的阶段验收验证器。"""  # 新增代码+LongTaskHarness: 说明本文件负责确定性验收；若没有这行代码，验收逻辑边界不清楚。

from __future__ import annotations  # 新增代码+LongTaskHarness: 延迟解析类型注解；若没有这行代码，后续类型引用更容易出问题。

import json  # 新增代码+VerifierUpgrade: 解析 JSON artifact 和 acceptance result；若没有这行代码，结构化验收只能停留在文本层。
from pathlib import Path  # 新增代码+LongTaskHarness: artifact 检查需要路径操作；若没有这行代码，文件验收只能手写字符串拼接。
from typing import Any  # 新增代码+VerifierUpgrade: command_results 和 events 使用通用 JSON 类型；若没有这行代码，增强 verifier 类型边界不清楚。

from learning_agent.harness.models import HarnessStage, VerificationResult  # 新增代码+LongTaskHarness: 导入阶段和验收结果模型；若没有这行代码，verifier 无法返回统一结果。


class StageVerifier:  # 新增代码+LongTaskHarness: 执行阶段成功标记和 artifact 断言；若没有这个类，阶段验收无法复用。
    def __init__(self, base_dir: str | Path) -> None:  # 新增代码+LongTaskHarness: 初始化 artifact 根目录；若没有这行代码，verifier 不知道从哪里查文件。
        self.base_dir = Path(base_dir)  # 新增代码+LongTaskHarness: 规范化根目录；若没有这行代码，相对路径检查不稳定。

    def verify(self, stage: HarnessStage, output: str, command_results: dict[str, int] | None = None, events: list[dict[str, Any]] | None = None) -> VerificationResult:  # 修改代码+VerifierUpgrade: 验证阶段输出、文件、命令退出码和事件顺序；若没有这行代码，harness 无法做真实可复现验收。
        checks: list[str] = []  # 新增代码+LongTaskHarness: 收集通过的检查项；若没有这行代码，审计报告没有细节。
        failures: list[str] = []  # 新增代码+LongTaskHarness: 收集失败原因；若没有这行代码，用户只能看到失败布尔值。
        safe_command_results = command_results or {}  # 新增代码+VerifierUpgrade: 未传命令结果时使用空字典；若没有这行代码，后续访问 None 会崩溃。
        safe_events = events or []  # 新增代码+VerifierUpgrade: 未传事件列表时使用空列表；若没有这行代码，事件顺序检查会崩溃。
        for marker in stage.success_markers:  # 新增代码+LongTaskHarness: 遍历文本成功标记；若没有这行代码，模型输出无法被确定性检查。
            label = f"marker:{marker}"  # 新增代码+LongTaskHarness: 构造审计标签；若没有这行代码，报告中不知道检查哪条 marker。
            if marker in output:  # 新增代码+LongTaskHarness: 检查输出是否包含 marker；若没有这行代码，文本验收不会执行。
                checks.append(label)  # 新增代码+LongTaskHarness: 记录通过标记；若没有这行代码，成功报告缺少证据。
            else:  # 新增代码+LongTaskHarness: marker 缺失时进入失败分支；若没有这行代码，失败不会被记录。
                failures.append(label)  # 新增代码+LongTaskHarness: 记录缺失标记；若没有这行代码，用户不知道缺什么。
        for artifact in stage.required_artifacts:  # 新增代码+LongTaskHarness: 遍历必需 artifact；若没有这行代码，文件成果无法验收。
            label = f"artifact:{artifact}"  # 新增代码+LongTaskHarness: 构造 artifact 审计标签；若没有这行代码，报告无法说明检查哪个文件。
            if (self.base_dir / artifact).exists():  # 新增代码+LongTaskHarness: 检查文件是否存在；若没有这行代码，artifact 门禁没有实际作用。
                checks.append(label)  # 新增代码+LongTaskHarness: 记录 artifact 通过；若没有这行代码，成功报告缺少文件证据。
            else:  # 新增代码+LongTaskHarness: 文件不存在时进入失败分支；若没有这行代码，缺文件不会影响结果。
                failures.append(label)  # 新增代码+LongTaskHarness: 记录缺失文件；若没有这行代码，用户不知道缺哪个 artifact。
        for artifact, expected_text in stage.artifact_contains.items():  # 新增代码+VerifierUpgrade: 遍历文件内容断言；若没有这行代码，文件内容错误不会被检查。
            label = f"artifact_contains:{artifact}"  # 新增代码+VerifierUpgrade: 构造内容检查标签；若没有这行代码，审计报告不知道检查哪个文件。
            path = self.base_dir / artifact  # 新增代码+VerifierUpgrade: 计算 artifact 路径；若没有这行代码，无法读取文件内容。
            if path.exists() and expected_text in path.read_text(encoding="utf-8", errors="replace"):  # 新增代码+VerifierUpgrade: 检查文件存在且包含期望文本；若没有这行代码，内容门禁没有实际作用。
                checks.append(label)  # 新增代码+VerifierUpgrade: 记录内容检查通过；若没有这行代码，成功报告缺少内容证据。
            else:  # 新增代码+VerifierUpgrade: 文件不存在或内容缺失时失败；若没有这行代码，缺内容不会影响验收。
                failures.append(label)  # 新增代码+VerifierUpgrade: 记录内容检查失败；若没有这行代码，用户不知道哪项内容缺失。
        for artifact, schema in stage.json_schema_artifacts.items():  # 新增代码+VerifierUpgrade: 遍历 JSON schema artifact 断言；若没有这行代码，结构化结果不会被检查。
            label = f"json_schema:{artifact}"  # 新增代码+VerifierUpgrade: 构造 schema 检查标签；若没有这行代码，审计报告不知道检查哪个 JSON。
            if self._json_artifact_matches_schema(self.base_dir / artifact, schema):  # 新增代码+VerifierUpgrade: 执行轻量 schema 检查；若没有这行代码，required 字段缺失无法发现。
                checks.append(label)  # 新增代码+VerifierUpgrade: 记录 schema 检查通过；若没有这行代码，成功报告缺少结构证据。
            else:  # 新增代码+VerifierUpgrade: schema 不匹配时失败；若没有这行代码，坏 JSON 会误通过。
                failures.append(label)  # 新增代码+VerifierUpgrade: 记录 schema 检查失败；若没有这行代码，用户不知道哪个 JSON 结构不合格。
        for command_name, expected_code in stage.expected_command_exit_codes.items():  # 新增代码+VerifierUpgrade: 遍历命令退出码断言；若没有这行代码，自动化命令结果不会进入门禁。
            actual_code = safe_command_results.get(command_name)  # 新增代码+VerifierUpgrade: 读取实际退出码；若没有这行代码，无法比较期望和实际。
            label = f"command_exit_code:{command_name}={expected_code}"  # 新增代码+VerifierUpgrade: 构造退出码检查标签；若没有这行代码，审计报告缺少命令结果。
            if actual_code == expected_code:  # 新增代码+VerifierUpgrade: 检查退出码是否符合期望；若没有这行代码，失败命令可能被忽略。
                checks.append(label)  # 新增代码+VerifierUpgrade: 记录退出码检查通过；若没有这行代码，成功报告缺少命令证据。
            else:  # 新增代码+VerifierUpgrade: 退出码不符合期望时失败；若没有这行代码，自动化失败不会阻断阶段。
                failures.append(label)  # 新增代码+VerifierUpgrade: 记录退出码失败；若没有这行代码，用户不知道哪个命令失败。
        if stage.expected_event_sequence:  # 新增代码+VerifierUpgrade: 如果阶段配置了事件顺序；若没有这行代码，无事件配置时会无意义检查。
            label = "event_sequence:" + ">".join(stage.expected_event_sequence)  # 新增代码+VerifierUpgrade: 构造事件顺序标签；若没有这行代码，审计报告看不出期望顺序。
            if self._events_contain_sequence(safe_events, stage.expected_event_sequence):  # 新增代码+VerifierUpgrade: 检查事件序列是否按顺序出现；若没有这行代码，事件流断裂不会被发现。
                checks.append(label)  # 新增代码+VerifierUpgrade: 记录事件顺序通过；若没有这行代码，成功报告缺少事件证据。
            else:  # 新增代码+VerifierUpgrade: 顺序缺失或乱序时失败；若没有这行代码，事件门禁没有实际作用。
                failures.append(label)  # 新增代码+VerifierUpgrade: 记录事件顺序失败；若没有这行代码，用户不知道事件流哪里不满足。
        for artifact in stage.acceptance_result_artifacts:  # 新增代码+VerifierUpgrade: 遍历真实验收 result.json；若没有这行代码，acceptance_controller 结果无法纳入门禁。
            label = f"acceptance_result:{artifact}"  # 新增代码+VerifierUpgrade: 构造真实验收标签；若没有这行代码，审计报告不知道检查哪个 result。
            if self._acceptance_result_passed(self.base_dir / artifact):  # 新增代码+VerifierUpgrade: 判断 result.json 是否 completed 且 assertion passed；若没有这行代码，真实验收失败也可能误通过。
                checks.append(label)  # 新增代码+VerifierUpgrade: 记录真实验收通过；若没有这行代码，成功报告缺少验真证据。
            else:  # 新增代码+VerifierUpgrade: 验收结果失败或缺字段时失败；若没有这行代码，验真结果不影响阶段。
                failures.append(label)  # 新增代码+VerifierUpgrade: 记录真实验收失败；若没有这行代码，用户不知道哪个场景未通过。
        passed = not failures  # 新增代码+LongTaskHarness: 没有失败项才算通过；若没有这行代码，验收结论无法汇总。
        message = "passed" if passed else "missing " + ", ".join(failures)  # 新增代码+LongTaskHarness: 生成可读结论；若没有这行代码，状态页缺少失败说明。
        return VerificationResult(passed=passed, checks=checks, message=message)  # 新增代码+LongTaskHarness: 返回统一验收结果；若没有这行代码，runner 无法保存 acceptance。

    def _json_artifact_matches_schema(self, path: Path, schema: dict[str, Any]) -> bool:  # 新增代码+VerifierUpgrade: 执行轻量 JSON required 字段检查；若没有这行代码，verify 会堆满解析细节。
        if not path.exists():  # 新增代码+VerifierUpgrade: 文件不存在直接失败；若没有这行代码，read_text 会抛异常。
            return False  # 新增代码+VerifierUpgrade: 返回 schema 不匹配；若没有这行代码，缺文件可能误通过。
        try:  # 新增代码+VerifierUpgrade: 捕获 JSON 解析错误；若没有这行代码，坏 JSON 会中断整个 verifier。
            payload = json.loads(path.read_text(encoding="utf-8"))  # 新增代码+VerifierUpgrade: 读取并解析 JSON；若没有这行代码，无法检查字段。
        except json.JSONDecodeError:  # 新增代码+VerifierUpgrade: 处理 JSON 格式错误；若没有这行代码，坏文件会抛异常。
            return False  # 新增代码+VerifierUpgrade: 坏 JSON 视为不匹配；若没有这行代码，错误无法转成验收失败。
        if not isinstance(payload, dict):  # 新增代码+VerifierUpgrade: schema 只支持对象根；若没有这行代码，数组根可能误通过 required。
            return False  # 新增代码+VerifierUpgrade: 非对象根返回失败；若没有这行代码，结构检查不安全。
        required = schema.get("required", []) if isinstance(schema, dict) else []  # 新增代码+VerifierUpgrade: 读取 required 字段；若没有这行代码，schema 缺省会报错。
        if not isinstance(required, list):  # 新增代码+VerifierUpgrade: required 必须是数组；若没有这行代码，坏 schema 会导致遍历异常。
            return False  # 新增代码+VerifierUpgrade: schema 不合法时失败；若没有这行代码，坏配置可能误通过。
        return all(str(key) in payload for key in required)  # 新增代码+VerifierUpgrade: 检查所有 required key 存在；若没有这行代码，缺字段无法被发现。

    def _events_contain_sequence(self, events: list[dict[str, Any]], expected_sequence: list[str]) -> bool:  # 新增代码+VerifierUpgrade: 检查事件类型是否按顺序出现；若没有这行代码，事件门禁逻辑会散落在 verify。
        event_types = [str(event.get("event_type", "")) for event in events if isinstance(event, dict)]  # 新增代码+VerifierUpgrade: 提取事件类型列表；若没有这行代码，无法按顺序匹配。
        cursor = 0  # 新增代码+VerifierUpgrade: 保存当前期望事件索引；若没有这行代码，无法做子序列匹配。
        for event_type in event_types:  # 新增代码+VerifierUpgrade: 遍历实际事件类型；若没有这行代码，无法推进匹配。
            if cursor < len(expected_sequence) and event_type == expected_sequence[cursor]:  # 新增代码+VerifierUpgrade: 当前事件命中期望顺序；若没有这行代码，无法判断进度。
                cursor += 1  # 新增代码+VerifierUpgrade: 推进到下一个期望事件；若没有这行代码，永远只匹配第一项。
        return cursor == len(expected_sequence)  # 新增代码+VerifierUpgrade: 全部期望事件命中才通过；若没有这行代码，部分匹配也可能误通过。

    def _acceptance_result_passed(self, path: Path) -> bool:  # 新增代码+VerifierUpgrade: 检查 acceptance_controller result.json 是否通过；若没有这行代码，真实终端验收无法纳入阶段门禁。
        if not path.exists():  # 新增代码+VerifierUpgrade: result 文件不存在直接失败；若没有这行代码，缺证据会被忽略。
            return False  # 新增代码+VerifierUpgrade: 返回失败；若没有这行代码，后续读取会抛异常。
        try:  # 新增代码+VerifierUpgrade: 捕获 JSON 解析失败；若没有这行代码，坏 result 会中断 verifier。
            payload = json.loads(path.read_text(encoding="utf-8"))  # 新增代码+VerifierUpgrade: 读取 result JSON；若没有这行代码，无法判断 completed/assertion。
        except json.JSONDecodeError:  # 新增代码+VerifierUpgrade: 处理坏 JSON；若没有这行代码，格式错误会抛异常。
            return False  # 新增代码+VerifierUpgrade: 坏 result 视为失败；若没有这行代码，错误无法变成验收结论。
        assertion = payload.get("assertion", {}) if isinstance(payload, dict) else {}  # 新增代码+VerifierUpgrade: 读取 assertion 对象；若没有这行代码，断言结果无法判断。
        return bool(isinstance(payload, dict) and payload.get("completed") is True and isinstance(assertion, dict) and assertion.get("passed") is True)  # 新增代码+VerifierUpgrade: 同时要求 completed 和 assertion.passed；若没有这行代码，半完成场景会误通过。
