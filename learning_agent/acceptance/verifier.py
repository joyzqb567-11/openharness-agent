"""离线复验真实可见终端验收结果。"""  # 新增代码+验收验证器: 说明本模块把 controller 断言抽成可复用 verifier；若没有这行代码，模块用途不清楚
from __future__ import annotations  # 新增代码+验收验证器: 允许类型注解延迟解析；若没有这行代码，复杂类型可能在导入时提前求值

import glob  # 新增代码+BrowserRecordingStage9: 支持按 glob 检查录制帧和 GIF artifact；若没有这行代码，verifier 只能检查固定文件名。
import json  # 新增代码+验收验证器: 读取场景、事件和结果 JSON；若没有这行代码，verifier 无法解析验收证据
import re  # 新增代码+DesktopTaskVisibleAcceptance: 支持 payload 正则门禁；若没有这行代码，gui_action_count>0 这类条件无法离线复验
import sys  # 新增代码+验收验证器: 提供命令行输出和退出码；若没有这行代码，`python -m` 入口无法返回状态
from collections import Counter  # 新增代码+验收验证器: 统计事件状态出现次数；若没有这行代码，required_event_states 检查会重复手写循环
from pathlib import Path  # 新增代码+验收验证器: 统一处理 Windows 和相对路径；若没有这行代码，证据文件路径处理会脆弱
from typing import Any  # 新增代码+验收验证器: 标注 JSON 对象中的任意值；若没有这行代码，类型提示无法表达真实 JSON 结构

from learning_agent.browser.assertions import BrowserAssertionEngine  # 新增代码+BrowserVerifierV2: 导入浏览器断言引擎；若没有这行代码，真实浏览器 observation 无法进入验收门禁。
from learning_agent.browser.runtime_models import BrowserObservation  # 新增代码+BrowserVerifierV2: 导入浏览器观察协议；若没有这行代码，verifier 无法从 JSON 证据恢复页面状态。


def _load_json_object(path: Path) -> dict[str, Any]:  # 新增代码+验收验证器: 读取 JSON 对象文件；若没有这行代码，场景和 result 解析逻辑会重复
    if not path.exists():  # 新增代码+验收验证器: 检查文件是否存在；若没有这行代码，缺文件会变成不清楚的打开异常
        return {}  # 新增代码+验收验证器: 缺文件返回空对象；若没有这行代码，离线复验无法给出结构化失败报告
    payload = json.loads(path.read_text(encoding="utf-8-sig"))  # 修改代码+验收验证器: 兼容 PowerShell 写出的 UTF-8 BOM JSON；若没有这行代码，真实 controller 的 result.json 会复验崩溃
    if isinstance(payload, dict):  # 新增代码+验收验证器: 确认顶层是对象；若没有这行代码，列表或字符串 JSON 会污染后续字段读取
        return payload  # 新增代码+验收验证器: 返回合法 JSON 对象；若没有这行代码，调用方拿不到结构化数据
    return {}  # 新增代码+验收验证器: 非对象 JSON 视为无效输入；若没有这行代码，后续 `.get` 调用可能崩溃


def _read_jsonl_events(path: Path) -> tuple[list[dict[str, Any]], int]:  # 新增代码+验收验证器: 读取事件 JSONL 并统计坏行；若没有这行代码，events.jsonl 无法被独立复验
    events: list[dict[str, Any]] = []  # 新增代码+验收验证器: 保存成功解析的事件；若没有这行代码，状态断言没有输入
    invalid_line_count = 0  # 新增代码+验收验证器: 统计无法解析的事件行；若没有这行代码，坏证据可能被悄悄忽略
    if not path.exists():  # 新增代码+验收验证器: 检查事件日志是否存在；若没有这行代码，缺日志会抛出不可控异常
        return events, 1  # 新增代码+验收验证器: 缺日志按一个坏输入处理；若没有这行代码，缺事件可能被误认为空但合法
    for raw_line in path.read_text(encoding="utf-8").splitlines():  # 新增代码+验收验证器: 逐行读取 JSONL；若没有这行代码，无法保留事件顺序和坏行定位
        if not raw_line.strip():  # 新增代码+验收验证器: 跳过空行；若没有这行代码，末尾空行会被当成坏证据
            continue  # 新增代码+验收验证器: 空行进入下一轮；若没有这行代码，空行会触发 JSON 解析错误
        try:  # 新增代码+验收验证器: 捕获单行 JSON 错误；若没有这行代码，一行坏证据会中断整个复验报告
            event = json.loads(raw_line)  # 新增代码+验收验证器: 解析单条事件；若没有这行代码，状态和 payload 无法读取
        except json.JSONDecodeError:  # 新增代码+验收验证器: 捕获 JSON 格式错误；若没有这行代码，坏行无法形成审计计数
            invalid_line_count += 1  # 新增代码+验收验证器: 记录坏行数量；若没有这行代码，审计报告不知道证据被污染
            continue  # 新增代码+验收验证器: 继续读取后续事件；若没有这行代码，一个坏行会丢失后续可用证据
        if isinstance(event, dict):  # 新增代码+验收验证器: 只接受对象事件；若没有这行代码，数组或字符串事件会污染状态统计
            events.append(event)  # 新增代码+验收验证器: 保存合法事件；若没有这行代码，后续检查没有事件输入
        else:  # 新增代码+验收验证器: 处理非对象事件；若没有这行代码，非法事件类型不会被计入风险
            invalid_line_count += 1  # 新增代码+验收验证器: 非对象事件也计为坏证据；若没有这行代码，审计会漏掉异常行
    return events, invalid_line_count  # 新增代码+验收验证器: 返回事件和坏行数量；若没有这行代码，调用方无法判断证据质量


def _as_text_list(value: Any) -> list[str]:  # 新增代码+验收验证器: 把场景字段安全转换成字符串列表；若没有这行代码，场景字段类型错误会导致遍历异常
    if not isinstance(value, list):  # 新增代码+验收验证器: 检查字段是否为列表；若没有这行代码，字符串会被当成字符逐个检查
        return []  # 新增代码+验收验证器: 非列表按空列表处理；若没有这行代码，错误场景会让 verifier 崩溃
    return [str(item) for item in value]  # 新增代码+验收验证器: 把每个值转为文本；若没有这行代码，数字等 JSON 值无法用于 contains 检查


def _coerce_int_or_none(value: Any) -> int | None:  # 新增代码+验收验证器: 把权限次数上限转成整数；若没有这行代码，字符串或空值会让比较逻辑不稳定
    if value is None:  # 新增代码+验收验证器: 允许场景不配置权限次数上限；若没有这行代码，旧场景会被误判
        return None  # 新增代码+验收验证器: None 表示不启用次数门禁；若没有这行代码，调用方无法区分未配置和 0
    try:  # 新增代码+验收验证器: 尝试兼容可转整数的 JSON 值；若没有这行代码，配置为字符串数字会直接崩溃
        return int(value)  # 新增代码+验收验证器: 返回整数上限；若没有这行代码，权限次数无法比较
    except (TypeError, ValueError):  # 新增代码+验收验证器: 捕获非法数字；若没有这行代码，坏配置无法形成结构化失败
        return None  # 新增代码+验收验证器: 非法上限按未配置处理；若没有这行代码，复验会因配置小错中断


def _resolve_path(raw_path: Any, run_dir: Path, fallback_name: str) -> Path:  # 新增代码+验收验证器: 把 result 中的路径解析为实际文件路径；若没有这行代码，相对路径和缺省文件名处理会散落
    candidate_text = str(raw_path).strip() if raw_path else ""  # 新增代码+验收验证器: 清理输入路径文本；若没有这行代码，空白路径可能被当成有效路径
    candidate = Path(candidate_text) if candidate_text else run_dir / fallback_name  # 新增代码+验收验证器: 有显式路径用显式路径，否则用默认文件名；若没有这行代码，旧 result 缺字段时无法复验
    if candidate.is_absolute():  # 新增代码+验收验证器: 检查是否已经是绝对路径；若没有这行代码，绝对路径会被错误拼到 run_dir 下
        return candidate  # 新增代码+验收验证器: 绝对路径直接返回；若没有这行代码，Windows 绝对路径会被破坏
    return run_dir / candidate  # 新增代码+验收验证器: 相对路径按 run_dir 解析；若没有这行代码，离线复验会依赖当前工作目录


def _latest_final_answer(events: list[dict[str, Any]]) -> tuple[str, str]:  # 新增代码+验收验证器: 提取最后一次最终回答文本和预览；若没有这行代码，回答断言会重复遍历事件
    answer_text = ""  # 新增代码+验收验证器: 初始化完整回答；若没有这行代码，无最终回答时变量未定义
    answer_preview = ""  # 新增代码+验收验证器: 初始化回答预览；若没有这行代码，报告缺少快速查看摘要
    for event in events:  # 新增代码+验收验证器: 按事件顺序寻找最终回答；若没有这行代码，无法处理多轮交互日志
        if event.get("state") != "final_answer_printed":  # 新增代码+验收验证器: 只处理最终回答事件；若没有这行代码，其他事件 payload 可能被误当答案
            continue  # 新增代码+验收验证器: 非最终回答事件跳过；若没有这行代码，循环会执行错误字段读取
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}  # 新增代码+验收验证器: 安全读取 payload；若没有这行代码，坏事件结构会导致崩溃
        answer_preview = str(payload.get("answer_preview", ""))  # 新增代码+验收验证器: 保存短预览；若没有这行代码，报告不方便快速查看答案
        answer_text = str(payload.get("answer_text") or answer_preview)  # 新增代码+验收验证器: 优先使用完整回答并兼容旧预览字段；若没有这行代码，长回答后半段无法被复验
    return answer_text, answer_preview  # 新增代码+验收验证器: 返回答案文本和预览；若没有这行代码，调用方拿不到回答证据


def _contains_checks(expected_texts: list[str], source_text: str) -> dict[str, bool]:  # 新增代码+验收验证器: 统一执行文本包含断言；若没有这行代码，回答和日志检查会重复实现
    return {text: text in source_text for text in expected_texts}  # 新增代码+验收验证器: 返回每个目标文本是否命中；若没有这行代码，失败报告无法显示缺哪一项


def _regex_checks(expected_patterns: list[str], source_text: str) -> dict[str, bool]:  # 新增代码+DesktopTaskVisibleAcceptance: 函数段开始，统一执行正则断言；若没有这段函数，数值门禁无法进入离线 verifier
    checks: dict[str, bool] = {}  # 新增代码+DesktopTaskVisibleAcceptance: 准备保存每个正则的命中结果；若没有这行代码，调用方拿不到逐项失败原因
    for pattern in expected_patterns:  # 新增代码+DesktopTaskVisibleAcceptance: 遍历场景声明的每个正则；若没有这行代码，只能检查一个写死条件
        try:  # 新增代码+DesktopTaskVisibleAcceptance: 捕获坏正则，避免 verifier 崩溃；若没有这行代码，场景里一个拼写错误会中断整份报告
            checks[pattern] = re.search(pattern, source_text) is not None  # 新增代码+DesktopTaskVisibleAcceptance: 执行正则匹配并保存布尔结果；若没有这行代码，动作数量大于 0 无法被复验
        except re.error:  # 新增代码+DesktopTaskVisibleAcceptance: 捕获非法正则表达式；若没有这行代码，坏配置不会以结构化失败呈现
            checks[pattern] = False  # 新增代码+DesktopTaskVisibleAcceptance: 坏正则按未通过处理；若没有这行代码，错误配置可能被误当成功
    return checks  # 新增代码+DesktopTaskVisibleAcceptance: 返回逐项正则断言结果；若没有这行代码，主 verifier 无法汇总门禁
# 新增代码+DesktopTaskVisibleAcceptance: 函数段结束，_regex_checks 到此结束；若没有这个边界说明，代码小白不容易看出正则复验范围


def _load_browser_observation_evidence(scenario: dict[str, Any], run_path: Path) -> BrowserObservation | None:  # 新增代码+BrowserVerifierV2: 从场景配置加载浏览器 observation 证据；若没有这行代码，浏览器断言只能靠调用方手写 Python。
    observation_path_text = str(scenario.get("browser_observation_path") or "").strip()  # 新增代码+BrowserVerifierV2: 读取可选 observation JSON 路径；若没有这行代码，verifier 不知道证据文件在哪。
    if not observation_path_text:  # 新增代码+BrowserVerifierV2: 未配置 observation 时返回空；若没有这行代码，旧场景会被强制要求浏览器证据。
        return None  # 新增代码+BrowserVerifierV2: 返回 None 表示无浏览器证据；若没有这行代码，调用方无法兼容旧场景。
    observation_path = Path(observation_path_text)  # 新增代码+BrowserVerifierV2: 把路径文本转成 Path；若没有这行代码，后续无法判断绝对路径。
    if not observation_path.is_absolute():  # 新增代码+BrowserVerifierV2: 相对路径按 run_dir 解析；若没有这行代码，离线复验会依赖当前工作目录。
        observation_path = run_path / observation_path  # 新增代码+BrowserVerifierV2: 拼成 run_dir 下路径；若没有这行代码，相对证据路径找不到。
    payload = _load_json_object(observation_path)  # 新增代码+BrowserVerifierV2: 读取 observation JSON；若没有这行代码，断言引擎没有页面状态输入。
    if not payload:  # 新增代码+BrowserVerifierV2: 空或缺文件时返回空；若没有这行代码，旧场景或坏路径会直接崩溃。
        return None  # 新增代码+BrowserVerifierV2: 返回 None 表示证据不可用；若没有这行代码，调用方无法生成结构化失败。
    return BrowserObservation.from_dict(payload)  # 新增代码+BrowserVerifierV2: 恢复 observation 协议对象；若没有这行代码，浏览器断言字段访问不稳定。


def _verify_browser_assertions(scenario: dict[str, Any], run_path: Path) -> dict[str, Any]:  # 新增代码+BrowserVerifierV2: 执行场景里的浏览器断言；若没有这行代码，真实浏览器测试无法成为门禁。
    browser_assertions = scenario.get("browser_assertions", [])  # 新增代码+BrowserVerifierV2: 读取浏览器断言列表；若没有这行代码，verifier 不知道要检查什么。
    if not isinstance(browser_assertions, list) or not browser_assertions:  # 新增代码+BrowserVerifierV2: 无断言时视为未启用浏览器门禁；若没有这行代码，旧场景会错误失败。
        return {"enabled": False, "completed": True, "assertions": []}  # 新增代码+BrowserVerifierV2: 返回兼容成功；若没有这行代码，主结果难以汇总。
    observation = _load_browser_observation_evidence(scenario, run_path)  # 新增代码+BrowserVerifierV2: 加载页面观察证据；若没有这行代码，断言没有输入。
    if observation is None:  # 新增代码+BrowserVerifierV2: 配了断言但缺证据时失败；若没有这行代码，浏览器断言可能被静默跳过。
        return {"enabled": True, "completed": False, "assertions": [], "error": "缺少 browser_observation_path 或 observation 文件不可读。"}  # 新增代码+BrowserVerifierV2: 返回结构化缺证据错误；若没有这行代码，调用方不知道为什么失败。
    report = BrowserAssertionEngine().evaluate_many([item for item in browser_assertions if isinstance(item, dict)], {"observation": observation})  # 新增代码+BrowserVerifierV2: 执行浏览器断言；若没有这行代码，URL/文本/截图门禁不会生效。
    report["enabled"] = True  # 新增代码+BrowserVerifierV2: 标记浏览器断言已启用；若没有这行代码，报告读者不知道该区块是否参与门禁。
    return report  # 新增代码+BrowserVerifierV2: 返回浏览器断言报告；若没有这行代码，主 verifier 拿不到结果。

def _project_root_from_scenario(scenario_file: Path) -> Path:  # 新增代码+BrowserRecordingStage9: 从场景路径推导项目根；若没有这行代码，{project_root} glob 无法定位录制产物。
    if len(scenario_file.parents) >= 4 and scenario_file.parent.name == "scenarios":  # 新增代码+BrowserRecordingStage9: 识别 learning_agent/acceptance_controller/scenarios 结构；若没有这行代码，真实场景会退回错误根。
        return scenario_file.parents[3]  # 新增代码+BrowserRecordingStage9: 返回仓库根目录；若没有这行代码，browser_artifacts glob 会从 learning_agent 下找错。
    return scenario_file.parent  # 新增代码+BrowserRecordingStage9: 非标准测试路径退回场景所在目录；若没有这行代码，临时测试场景无法工作。


def _verify_required_artifact_globs(scenario: dict[str, Any], run_path: Path, scenario_file: Path) -> dict[str, bool]:  # 新增代码+BrowserRecordingStage9: 检查场景要求的 artifact glob；若没有这行代码，GIF/帧文件存在性不能成为独立门禁。
    project_root = _project_root_from_scenario(scenario_file)  # 新增代码+BrowserRecordingStage9: 推导 project_root 占位符；若没有这行代码，glob 模板无法替换。
    checks: dict[str, bool] = {}  # 新增代码+BrowserRecordingStage9: 准备返回每个 glob 的结果；若没有这行代码，报告没有容器。
    for raw_pattern in _as_text_list(scenario.get("required_artifact_globs")):  # 新增代码+BrowserRecordingStage9: 遍历场景声明的 glob；若没有这行代码，配置不会生效。
        pattern = raw_pattern.replace("{project_root}", str(project_root)).replace("{run_dir}", str(run_path))  # 新增代码+BrowserRecordingStage9: 替换支持的占位符；若没有这行代码，场景只能写死绝对路径。
        if not Path(pattern).is_absolute():  # 新增代码+BrowserRecordingStage9: 相对 glob 按 run_dir 解析；若没有这行代码，相对配置会依赖当前工作目录。
            pattern = str(run_path / pattern)  # 新增代码+BrowserRecordingStage9: 拼成 run_dir 下的 glob；若没有这行代码，离线复验路径不稳定。
        checks[raw_pattern] = bool(glob.glob(pattern))  # 新增代码+BrowserRecordingStage9: 记录 glob 是否匹配至少一个文件；若没有这行代码，缺帧/GIF 不会失败。
    return checks  # 新增代码+BrowserRecordingStage9: 返回逐项 glob 检查结果；若没有这行代码，主 verifier 无法汇总。


def verify_acceptance_run(run_dir: str | Path, scenario_path: str | Path) -> dict[str, Any]:  # 新增代码+验收验证器: 对已有真实验收 run 执行离线复验；若没有这行代码，Codex 无法独立审计 result/events/log/screenshots
    run_path = Path(run_dir).resolve()  # 新增代码+验收验证器: 解析运行目录为绝对路径；若没有这行代码，报告里的路径不稳定
    scenario_file = Path(scenario_path).resolve()  # 新增代码+验收验证器: 解析场景文件为绝对路径；若没有这行代码，复验记录无法准确指向配置来源
    scenario = _load_json_object(scenario_file)  # 新增代码+验收验证器: 读取场景断言配置；若没有这行代码，verifier 不知道验收目标
    result_path = run_path / "result.json"  # 新增代码+验收验证器: 定位 controller 结果文件；若没有这行代码，权限次数和证据路径没有固定入口
    controller_result = _load_json_object(result_path)  # 新增代码+验收验证器: 读取已有 result.json；若没有这行代码，无法复核 controller 的证据索引
    event_log_path = _resolve_path(controller_result.get("event_log"), run_path, "events.jsonl")  # 新增代码+验收验证器: 定位事件日志；若没有这行代码，状态链无法复验
    debug_log_path = _resolve_path(controller_result.get("copied_debug_log"), run_path, "latest_run_readable.md")  # 新增代码+验收验证器: 定位归档 debug log；若没有这行代码，日志证据无法复验
    events, invalid_event_line_count = _read_jsonl_events(event_log_path)  # 新增代码+验收验证器: 读取事件并统计坏行；若没有这行代码，状态和回答检查没有输入
    states = [str(event.get("state", "")) for event in events]  # 新增代码+验收验证器: 提取事件状态序列；若没有这行代码，报告无法复盘运行时序
    state_counts = Counter(states)  # 新增代码+验收验证器: 统计每种状态出现次数；若没有这行代码，required_event_states 检查效率低且重复
    required_states = _as_text_list(scenario.get("required_event_states"))  # 新增代码+验收验证器: 读取场景要求的状态；若没有这行代码，状态断言没有目标
    state_checks = {state: state_counts[state] > 0 for state in required_states}  # 新增代码+验收验证器: 检查每个必需状态是否出现；若没有这行代码，缺 ready/final 也可能误通过
    answer_text, answer_preview = _latest_final_answer(events)  # 新增代码+验收验证器: 提取最终回答；若没有这行代码，回答断言没有输入
    event_answer_checks = _contains_checks(_as_text_list(scenario.get("event_answer_contains")), answer_text)  # 新增代码+验收验证器: 检查最终回答必须包含的证据；若没有这行代码，用户可见输出无法独立验证
    event_payload_text = json.dumps(events, ensure_ascii=False, default=str)  # 新增代码+Phase24AcceptancePayload: 把事件 payload 重新序列化成可搜索文本；若没有这行代码，离线 verifier 无法复验 /chrome 输出里的 true/false 字段。
    event_payload_checks = _contains_checks(_as_text_list(scenario.get("event_payload_contains")), event_payload_text)  # 新增代码+Phase24AcceptancePayload: 检查场景要求的事件 payload 文本；若没有这行代码，real_extension_e2e=false 也可能只靠事件名通过离线复验。
    event_payload_regex_checks = _regex_checks(_as_text_list(scenario.get("event_payload_regex")), event_payload_text)  # 新增代码+DesktopTaskVisibleAcceptance: 检查场景要求的事件 payload 正则；若没有这行代码，动作数量为 0 也可能离线通过
    debug_log_exists = debug_log_path.exists()  # 新增代码+验收验证器: 记录 debug log 是否存在；若没有这行代码，日志断言无法区分缺文件和缺文本
    debug_log_text = debug_log_path.read_text(encoding="utf-8") if debug_log_exists else ""  # 新增代码+验收验证器: 读取 debug log 文本；若没有这行代码，工具调用证据无法检查
    debug_log_checks = _contains_checks(_as_text_list(scenario.get("debug_log_contains")), debug_log_text)  # 新增代码+验收验证器: 检查 debug log 必含片段；若没有这行代码，工具调用证据可能缺失仍通过
    success_marker = str(scenario.get("success_marker", "")).strip()  # 新增代码+验收验证器: 读取固定成功标记；若没有这行代码，场景无法确认答案属于本轮
    marker_passed = (not success_marker) or (success_marker in answer_text) or (success_marker in debug_log_text)  # 新增代码+验收验证器: 检查成功标记是否出现；若没有这行代码，非本轮回答可能误通过
    permission_sent_count = int(controller_result.get("permission_sent_count", state_counts["permission_answered"]))  # 新增代码+验收验证器: 读取或推导权限响应次数；若没有这行代码，客户模式无 y 门禁无法复验
    max_permission_sent_count = _coerce_int_or_none(scenario.get("max_permission_sent_count"))  # 新增代码+验收验证器: 读取权限次数上限；若没有这行代码，场景无法表达 0 次 y/N 门禁
    permission_count_passed = max_permission_sent_count is None or permission_sent_count <= max_permission_sent_count  # 新增代码+验收验证器: 检查权限响应次数是否超标；若没有这行代码，多次 y/N 仍可能验收通过
    artifact_paths = {"result_json": result_path, "event_log": event_log_path, "debug_log": debug_log_path, "startup_screenshot": _resolve_path(controller_result.get("startup_screenshot"), run_path, "01_startup.png"), "prompt_screenshot": _resolve_path(controller_result.get("prompt_screenshot"), run_path, "02_prompt_sent.png"), "final_screenshot": _resolve_path(controller_result.get("final_screenshot"), run_path, "03_final.png")}  # 新增代码+验收验证器: 汇总审计证据文件；若没有这行代码，截图和日志缺失也可能被忽略
    debug_log_required = bool(_as_text_list(scenario.get("debug_log_contains")))  # 修改代码+DesktopTaskVisibleAcceptance: 只有场景显式声明日志断言时才强制 debug log；若没有这行代码，完整 answer_text 事件已足够的场景会被误判失败。
    artifact_checks = {name: (path.exists() or (name == "debug_log" and not debug_log_required)) for name, path in artifact_paths.items()}  # 修改代码+Phase7Acceptance: 事件型场景允许没有 debug log，但仍要求 result/events/screenshots；若没有这行代码，真实 /chrome 验收不能独立复验。
    required_artifact_glob_checks = _verify_required_artifact_globs(scenario, run_path, scenario_file)  # 新增代码+BrowserRecordingStage9: 检查额外帧/GIF artifact glob；若没有这行代码，Stage 9 产物无法被 verifier 独立确认。
    browser_assertion_report = _verify_browser_assertions(scenario, run_path)  # 新增代码+BrowserVerifierV2: 执行浏览器 observation 断言；若没有这行代码，真实浏览器内容无法作为验收门禁。
    states_passed = not (False in state_checks.values())  # 新增代码+验收验证器: 汇总状态断言；若没有这行代码，缺状态无法影响最终结论
    event_answer_passed = not (False in event_answer_checks.values())  # 新增代码+验收验证器: 汇总回答断言；若没有这行代码，缺最终回答证据无法影响最终结论
    event_payload_passed = not (False in event_payload_checks.values())  # 新增代码+Phase24AcceptancePayload: 汇总事件 payload 断言；若没有这行代码，/chrome 输出为 false 时离线 verifier 仍可能通过。
    event_payload_regex_passed = not (False in event_payload_regex_checks.values())  # 新增代码+DesktopTaskVisibleAcceptance: 汇总事件 payload 正则断言；若没有这行代码，数值门禁不会影响最终结论
    debug_log_passed = not (False in debug_log_checks.values())  # 新增代码+验收验证器: 汇总日志断言；若没有这行代码，缺工具证据无法影响最终结论
    artifacts_passed = not (False in artifact_checks.values())  # 新增代码+验收验证器: 汇总证据文件断言；若没有这行代码，缺截图或日志无法影响最终结论
    required_artifact_globs_passed = not (False in required_artifact_glob_checks.values())  # 新增代码+BrowserRecordingStage9: 汇总额外 artifact glob 断言；若没有这行代码，缺 GIF/帧不会影响最终结论。
    event_log_parse_passed = invalid_event_line_count == 0  # 新增代码+验收验证器: 检查事件日志是否无坏行；若没有这行代码，损坏 JSONL 仍可能验收通过
    browser_assertions_passed = bool(browser_assertion_report.get("completed", True))  # 新增代码+BrowserVerifierV2: 汇总浏览器断言结果；若没有这行代码，浏览器失败不会影响总门禁。
    passed = states_passed and event_answer_passed and event_payload_passed and event_payload_regex_passed and debug_log_passed and marker_passed and permission_count_passed and artifacts_passed and required_artifact_globs_passed and event_log_parse_passed and browser_assertions_passed  # 修改代码+DesktopTaskVisibleAcceptance: 汇总最终复验结论并纳入 payload 正则断言；若没有这行代码，动作数量为 0 仍可能离线误通过。
    return {"schema_version": 2, "verifier": "learning_agent.acceptance.verifier", "completed": passed, "scenario": str(scenario.get("name", "")), "scenario_path": str(scenario_file), "run_dir": str(run_path), "event_count": len(events), "states": states, "event_log": str(event_log_path), "result_json": str(result_path), "debug_log": str(debug_log_path), "permission_policy_decisions": controller_result.get("permission_policy_decisions", []), "browser_assertions": browser_assertion_report, "assertion": {"passed": passed, "marker_passed": marker_passed, "permission_count_passed": permission_count_passed, "permission_sent_count": permission_sent_count, "max_permission_sent_count": max_permission_sent_count, "event_log_parse_passed": event_log_parse_passed, "invalid_event_line_count": invalid_event_line_count, "state_checks": state_checks, "event_answer_checks": event_answer_checks, "event_payload_checks": event_payload_checks, "event_payload_regex_checks": event_payload_regex_checks, "event_payload_text_length": len(event_payload_text), "debug_log_checks": debug_log_checks, "artifact_checks": artifact_checks, "required_artifact_glob_checks": required_artifact_glob_checks, "required_artifact_globs_passed": required_artifact_globs_passed, "browser_assertions_passed": browser_assertions_passed, "final_answer_preview": answer_preview, "final_answer_text_length": len(answer_text)}}  # 修改代码+DesktopTaskVisibleAcceptance: 返回可审计 JSON 报告并包含 payload 正则检查；若没有这行代码，调用方无法复盘数值门禁。


def main(argv: list[str] | None = None) -> int:  # 新增代码+验收验证器: 提供 `python -m` 命令行入口；若没有这行代码，其他 agent 只能写 Python 代码调用 verifier
    args = sys.argv[1:] if argv is None else argv  # 新增代码+验收验证器: 获取命令行参数或测试参数；若没有这行代码，CLI 和单测不能共用入口
    if len(args) != 2:  # 新增代码+验收验证器: 要求 run_dir 和 scenario_path 两个参数；若没有这行代码，错误调用会产生不清楚的异常
        sys.stderr.write("用法: python -m learning_agent.acceptance.verifier <run_dir> <scenario.json>\n")  # 新增代码+验收验证器: 输出清晰用法；若没有这行代码，用户不知道如何调用
        return 2  # 新增代码+验收验证器: 参数错误返回非零退出码；若没有这行代码，自动化可能把错误调用当成功
    report = verify_acceptance_run(args[0], args[1])  # 新增代码+验收验证器: 执行离线复验；若没有这行代码，CLI 不会真正检查证据
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")  # 新增代码+验收验证器: 输出可读 JSON 报告；若没有这行代码，外部 agent 无法稳定解析复验结果
    return 0 if report["completed"] else 2  # 新增代码+验收验证器: 根据复验结果返回退出码；若没有这行代码，CI 或 Codex 无法用命令状态判断通过


if __name__ == "__main__":  # 新增代码+验收验证器: 只有直接以模块执行时才进入 CLI；若没有这行代码，导入模块会误跑命令行逻辑
    raise SystemExit(main())  # 新增代码+验收验证器: 把 main 返回值交给系统退出码；若没有这行代码，失败复验不会正确返回非零
