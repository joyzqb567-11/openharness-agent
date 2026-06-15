"""Computer Use 顶层治理矩阵。"""  # 新增代码+TopLevelComputerUseMatrix：说明本文件负责把真实桌面闭环和 ClaudeCode 生产化对齐统一成最高层门禁；如果没有这一行，读者一打开文件就不知道这个模块的总职责。
from __future__ import annotations  # 新增代码+TopLevelComputerUseMatrix：启用更稳定的类型注解解析；如果没有这一行，老版本解释器在读取部分注解时可能更容易出现兼容问题。

import json  # 新增代码+TopLevelComputerUseMatrix：导入 JSON 工具用于 CLI 输出完整报告；如果没有这一行，命令行无法打印机器可读的矩阵结果。
import os  # 新增代码+Phase9VisibleTerminalGovernance：导入系统环境工具读取 acceptance controller 注入的事件日志路径；如果没有这一行，顶层矩阵无法从真实可见终端继承验收证据。
import sys  # 新增代码+Phase9CliArgvFix：导入进程参数工具，让 python -m 真实命令行参数可以进入 main；如果没有这一行，--real-desktop-evidence 等参数会被忽略。
import time  # 新增代码+Phase9VisibleTerminalGovernance：导入时间工具判断事件日志是否新鲜；如果没有这一行，旧 run artifacts 可能冒充本轮真实验收。
from pathlib import Path  # 新增代码+TopLevelComputerUseMatrix：导入路径对象用于读取项目源码证据；如果没有这一行，矩阵只能靠脆弱字符串路径访问文件。
from typing import Any  # 新增代码+TopLevelComputerUseMatrix：导入通用类型用于描述动态报告结构；如果没有这一行，函数签名无法清楚表达报告字段可能来自多种来源。

try:  # 新增代码+TopLevelComputerUseMatrix：优先使用包路径导入已有矩阵；如果没有这一段，单元测试和模块运行时会重复写两套导入逻辑。
    from learning_agent.computer_use_mcp_v2.windows_runtime.production_live_control import run_phase76_89_windows_live_control_contract  # 新增代码+TopLevelComputerUseMatrix：导入 Phase76-89 生产化合约；如果没有这一行，顶层矩阵无法复用现有 ClaudeCode 对齐证据。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_final_maturity_matrix import run_phase121_universal_final_maturity_matrix  # 新增代码+TopLevelComputerUseMatrix：导入 Phase121 真实桌面最终矩阵；如果没有这一行，顶层矩阵无法判断真实桌面闭环是否成熟。
except ModuleNotFoundError as error:  # 新增代码+TopLevelComputerUseMatrix：兼容直接从 learning_agent 目录运行脚本的情况；如果没有这一行，开发者在不同工作目录运行会遇到导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime"}:  # 新增代码+TopLevelComputerUseMatrix：只兜底包根不存在的场景；如果没有这一行，真实依赖缺失会被错误吞掉。
        raise  # 新增代码+TopLevelComputerUseMatrix：保留真正缺依赖的异常；如果没有这一行，矩阵可能在依赖损坏时悄悄给出错误结论。
    from computer_use_mcp_v2.windows_runtime.production_live_control import run_phase76_89_windows_live_control_contract  # type: ignore  # 新增代码+TopLevelComputerUseMatrix：提供脚本模式下的生产化合约导入；如果没有这一行，直接运行脚本时无法复用生产化矩阵。
    from computer_use_mcp_v2.windows_runtime.universal_final_maturity_matrix import run_phase121_universal_final_maturity_matrix  # type: ignore  # 新增代码+TopLevelComputerUseMatrix：提供脚本模式下的真实桌面矩阵导入；如果没有这一行，直接运行脚本时无法复用最终成熟度矩阵。

COMPUTER_USE_TOP_LEVEL_GOVERNANCE_MARKER = "COMPUTER_USE_TOP_LEVEL_GOVERNANCE_READY"  # 新增代码+TopLevelComputerUseMatrix：定义顶层矩阵稳定 marker；如果没有这一行，终端验收和自动化脚本无法用固定锚点识别报告。
COMPUTER_USE_TOP_LEVEL_GOVERNANCE_MODEL = "computer_use_top_level_governance_matrix"  # 新增代码+TopLevelComputerUseMatrix：定义矩阵模型名称；如果没有这一行，后续多套矩阵并存时不容易区分当前报告来源。
PHASE9_FINAL_VISIBLE_TERMINAL_SCENARIO_ID = "agent_capability_computer_use_top_level_governance_final_visible_terminal"  # 新增代码+Phase9VisibleTerminalGovernance：定义最终真实可见终端场景 ID；如果没有这一行，代码和 scenario 可能各用一个名字导致验收路径漂移。
PHASE9_VISIBLE_TERMINAL_GOVERNANCE_MODEL = "phase9_visible_terminal_governance"  # 新增代码+Phase9VisibleTerminalGovernance：定义可见终端证据模型名；如果没有这一行，顶层报告无法区分真实终端证据和普通生产化证据。
PHASE9_VISIBLE_TERMINAL_EVENT_LOG_ENV = "LEARNING_AGENT_ACCEPTANCE_EVENT_LOG"  # 新增代码+Phase9VisibleTerminalGovernance：定义 acceptance controller 注入事件日志的环境变量名；如果没有这一行，矩阵无法稳定找到真实终端事件。
PHASE9_VISIBLE_TERMINAL_FRESH_SECONDS = 86400  # 新增代码+Phase9VisibleTerminalGovernance：限定最终验收事件日志必须在一天内生成；如果没有这一行，历史旧日志可能绕过规则十七。


# 新增代码+TopLevelComputerUseMatrix：函数段开始，_top_level_bool_token 把布尔值变成稳定小写 token；如果没有这段函数，CLI 输出可能混用 True/False 导致脚本匹配不稳定。
def _top_level_bool_token(value: Any) -> str:  # 新增代码+TopLevelComputerUseMatrix：声明布尔 token 转换函数；如果没有这一行，调用方无法统一格式化矩阵状态。
    return "true" if bool(value) else "false"  # 新增代码+TopLevelComputerUseMatrix：返回小写 true/false；如果没有这一行，真实终端里的人和脚本都更难快速判断门禁状态。
# 新增代码+TopLevelComputerUseMatrix：函数段结束，_top_level_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化逻辑范围。


# 新增代码+TopLevelComputerUseMatrix：函数段开始，_top_level_project_root 定位 OpenHarness 项目根目录；如果没有这段函数，源码证据检查会散落重复路径计算。
def _top_level_project_root() -> Path:  # 新增代码+TopLevelComputerUseMatrix：声明项目根目录定位函数；如果没有这一行，其他函数无法安全找到仓库文件。
    return Path(__file__).resolve().parents[3]  # 修改代码+ComputerUseMcpV2ResidualCleanup：从 learning_agent/computer_use_mcp_v2/windows_runtime 回退三级得到项目根；如果没有这一行，治理矩阵会少退一层并读取错误路径。
# 新增代码+TopLevelComputerUseMatrix：函数段结束，_top_level_project_root 到此结束；如果没有这个边界说明，初学者不容易看出路径根的来源。


# 新增代码+TopLevelComputerUseMatrix：函数段开始，_top_level_read_source 读取源码作为矩阵证据；如果没有这段函数，顶层矩阵无法检查 ClaudeCode 对齐能力是否真实存在于代码里。
def _top_level_read_source(relative_path: str) -> str:  # 新增代码+TopLevelComputerUseMatrix：声明按相对路径读取源码的函数；如果没有这一行，调用方需要重复处理路径和异常。
    source_path = _top_level_project_root() / relative_path  # 新增代码+TopLevelComputerUseMatrix：把相对路径拼成绝对路径；如果没有这一行，读取动作会依赖当前终端所在目录。
    try:  # 新增代码+TopLevelComputerUseMatrix：进入安全读取区；如果没有这一行，文件缺失会直接打断整个矩阵报告。
        return source_path.read_text(encoding="utf-8", errors="replace")  # 新增代码+TopLevelComputerUseMatrix：按 UTF-8 读取源码并容忍坏字符；如果没有这一行，少量编码问题可能让顶层矩阵无法运行。
    except OSError:  # 新增代码+TopLevelComputerUseMatrix：捕获文件不存在或无法读取；如果没有这一行，某个证据文件缺失会让所有门禁都无法输出。
        return ""  # 新增代码+TopLevelComputerUseMatrix：读取失败时返回空字符串让对应门禁自然失败；如果没有这一行，矩阵会把无法证明的能力误判成异常中断。
# 新增代码+TopLevelComputerUseMatrix：函数段结束，_top_level_read_source 到此结束；如果没有这个边界说明，初学者不容易看出源码读取兜底范围。


# 新增代码+TopLevelComputerUseMatrix：函数段开始，_top_level_source_contains_all 检查源码证据 token；如果没有这段函数，每个门禁都要重复 all 判断且容易写错。
def _top_level_source_contains_all(source_text: str, required_tokens: list[str]) -> bool:  # 新增代码+TopLevelComputerUseMatrix：声明源码 token 全量匹配函数；如果没有这一行，生产化门禁缺少统一判断入口。
    return all(token in source_text for token in required_tokens)  # 新增代码+TopLevelComputerUseMatrix：只有所有 token 都存在才返回真；如果没有这一行，矩阵可能因为一个孤立词就误报能力已完成。
# 新增代码+TopLevelComputerUseMatrix：函数段结束，_top_level_source_contains_all 到此结束；如果没有这个边界说明，初学者不容易看出证据匹配规则。


# 新增代码+Phase9VisibleTerminalGovernance：函数段开始，_top_level_safe_dict 把动态输入安全整理为字典；如果没有这段函数，坏 evidence 结构可能让顶层矩阵异常中断。
def _top_level_safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase9VisibleTerminalGovernance：声明字典清洗函数；如果没有这一行，调用方需要反复写 isinstance 判断。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+Phase9VisibleTerminalGovernance：只复制字典输入并拒绝其它类型；如果没有这一行，列表或字符串可能污染报告结构。
# 新增代码+Phase9VisibleTerminalGovernance：函数段结束，_top_level_safe_dict 到此结束；如果没有这个边界说明，初学者不容易看出动态字段清洗范围。


# 新增代码+Phase9VisibleTerminalGovernance：函数段开始，_top_level_event_states_from_log 从 JSONL 事件日志提取状态；如果没有这段函数，可见终端门禁无法知道真实终端是否 ready 和收到 prompt。
def _top_level_event_states_from_log(event_log: Path) -> list[str]:  # 新增代码+Phase9VisibleTerminalGovernance：声明事件状态读取函数；如果没有这一行，校验函数要混杂文件读取和业务判断。
    try:  # 新增代码+Phase9VisibleTerminalGovernance：进入安全读取事件日志区；如果没有这一行，损坏或被占用的日志会打断整个顶层矩阵。
        lines = event_log.read_text(encoding="utf-8", errors="replace").splitlines()  # 新增代码+Phase9VisibleTerminalGovernance：按 UTF-8 读取 JSONL 行；如果没有这一行，真实 controller 写出的中文 payload 可能无法解析。
    except OSError:  # 新增代码+Phase9VisibleTerminalGovernance：捕获日志不可读错误；如果没有这一行，缺失日志会变成异常而不是门禁失败。
        return []  # 新增代码+Phase9VisibleTerminalGovernance：不可读时返回空状态；如果没有这一行，调用方无法自然得到失败报告。
    states: list[str] = []  # 新增代码+Phase9VisibleTerminalGovernance：初始化状态列表；如果没有这一行，后续循环没有收集容器。
    for line in lines:  # 新增代码+Phase9VisibleTerminalGovernance：逐行扫描 JSONL；如果没有这一行，只能读取第一条事件。
        raw_line = str(line).strip()  # 新增代码+Phase9VisibleTerminalGovernance：清理行首尾空白；如果没有这一行，空行或换行会干扰解析。
        if not raw_line:  # 新增代码+Phase9VisibleTerminalGovernance：跳过空行；如果没有这一行，空行会产生无意义 JSON 错误。
            continue  # 新增代码+Phase9VisibleTerminalGovernance：继续处理下一行；如果没有这一行，空行会落入解析逻辑。
        try:  # 新增代码+Phase9VisibleTerminalGovernance：尝试解析单行 JSON；如果没有这一行，一条坏事件会破坏整份日志。
            event = json.loads(raw_line)  # 新增代码+Phase9VisibleTerminalGovernance：把事件行转成对象；如果没有这一行，门禁无法读取 state 字段。
        except json.JSONDecodeError:  # 新增代码+Phase9VisibleTerminalGovernance：捕获坏 JSON 行；如果没有这一行，截断日志会让矩阵崩溃。
            continue  # 新增代码+Phase9VisibleTerminalGovernance：忽略坏行并保留其它证据；如果没有这一行，局部日志损坏会造成过度失败。
        if isinstance(event, dict) and isinstance(event.get("state"), str):  # 新增代码+Phase9VisibleTerminalGovernance：只接受带字符串 state 的事件；如果没有这一行，异常 payload 可能污染状态列表。
            states.append(str(event["state"]))  # 新增代码+Phase9VisibleTerminalGovernance：记录状态名；如果没有这一行，后续无法判断 ready 和 prompt 是否出现。
    return states  # 新增代码+Phase9VisibleTerminalGovernance：返回状态序列；如果没有这一行，调用方拿不到事件事实。
# 新增代码+Phase9VisibleTerminalGovernance：函数段结束，_top_level_event_states_from_log 到此结束；如果没有这个边界说明，初学者不容易看出事件读取范围。


# 新增代码+Phase9VisibleTerminalGovernance：函数段开始，evaluate_visible_terminal_e2e_evidence 校验真实可见终端验收证据；如果没有这段函数，规则十七无法进入顶层矩阵。
def evaluate_visible_terminal_e2e_evidence(event_log_path: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase9VisibleTerminalGovernance：声明可见终端证据校验入口；如果没有这一行，测试和 CLI 无法复用同一门禁。
    raw_event_log = str(event_log_path or os.environ.get(PHASE9_VISIBLE_TERMINAL_EVENT_LOG_ENV, "")).strip()  # 新增代码+Phase9VisibleTerminalGovernance：优先使用显式路径，否则读取 controller 环境变量；如果没有这一行，真实 bat 启动链路无法自动接入。
    event_log = Path(raw_event_log) if raw_event_log else None  # 新增代码+Phase9VisibleTerminalGovernance：把日志路径转成 Path；如果没有这一行，后续不能稳定访问父目录和文件状态。
    event_log_exists = bool(event_log and event_log.exists() and event_log.is_file())  # 新增代码+Phase9VisibleTerminalGovernance：检查事件日志是否真实存在；如果没有这一行，随便写一个路径也可能被当成证据。
    run_dir = event_log.parent if event_log_exists and event_log else None  # 新增代码+Phase9VisibleTerminalGovernance：定位本次 controller run 目录；如果没有这一行，无法检查场景 ID 和截图证据。
    run_dir_name = run_dir.name if run_dir else ""  # 新增代码+Phase9VisibleTerminalGovernance：读取 run 目录名；如果没有这一行，报告无法说明是否匹配最终场景。
    run_dir_matches_final_scenario = bool(PHASE9_FINAL_VISIBLE_TERMINAL_SCENARIO_ID in run_dir_name)  # 新增代码+Phase9VisibleTerminalGovernance：要求日志来自最终可见终端场景；如果没有这一行，普通历史场景会冒充最终验收。
    states = _top_level_event_states_from_log(event_log) if event_log_exists and event_log else []  # 新增代码+Phase9VisibleTerminalGovernance：读取事件状态；如果没有这一行，ready/prompt 事实不会进入门禁。
    agent_ready_for_user_prompt = "agent_ready_for_user_prompt" in states  # 新增代码+Phase9VisibleTerminalGovernance：确认 agent 已在真实终端准备接收用户输入；如果没有这一行，仅有日志文件就可能通过。
    user_prompt_received = "user_prompt_received" in states  # 新增代码+Phase9VisibleTerminalGovernance：确认真实用户 prompt 已进入 agent；如果没有这一行，终端只启动不交互也会被误算通过。
    startup_screenshot = run_dir / "01_startup.png" if run_dir else None  # 新增代码+Phase9VisibleTerminalGovernance：定位启动截图；如果没有这一行，报告无法证明窗口启动画面被保存。
    prompt_screenshot = run_dir / "02_prompt_sent.png" if run_dir else None  # 新增代码+Phase9VisibleTerminalGovernance：定位 prompt 输入截图；如果没有这一行，报告无法证明 prompt 发进了可见窗口。
    startup_screenshot_present = bool(startup_screenshot and startup_screenshot.exists() and startup_screenshot.is_file())  # 新增代码+Phase9VisibleTerminalGovernance：检查启动截图存在；如果没有这一行，真实可见窗口证据不够硬。
    prompt_screenshot_present = bool(prompt_screenshot and prompt_screenshot.exists() and prompt_screenshot.is_file())  # 新增代码+Phase9VisibleTerminalGovernance：检查 prompt 截图存在；如果没有这一行，真实输入证据不够硬。
    age_seconds = -1  # 新增代码+Phase9VisibleTerminalGovernance：初始化日志年龄；如果没有这一行，缺失日志时报告无法提供稳定数值。
    if event_log_exists and event_log:  # 新增代码+Phase9VisibleTerminalGovernance：只有日志存在时才计算年龄；如果没有这一行，缺失路径会触发 stat 错误。
        age_seconds = max(0, int(time.time() - event_log.stat().st_mtime))  # 新增代码+Phase9VisibleTerminalGovernance：根据修改时间计算证据年龄；如果没有这一行，旧日志无法被识别。
    fresh_event_log = bool(event_log_exists and 0 <= age_seconds <= PHASE9_VISIBLE_TERMINAL_FRESH_SECONDS)  # 新增代码+Phase9VisibleTerminalGovernance：要求事件日志足够新鲜；如果没有这一行，旧 run artifacts 可能绕过最终验收。
    hard_fail_reasons: list[str] = []  # 新增代码+Phase9VisibleTerminalGovernance：初始化失败原因列表；如果没有这一行，用户看不懂门禁为什么失败。
    if not raw_event_log:  # 新增代码+Phase9VisibleTerminalGovernance：检查日志路径是否缺失；如果没有这一行，空路径失败原因不清楚。
        hard_fail_reasons.append("event_log_path_missing")  # 新增代码+Phase9VisibleTerminalGovernance：记录路径缺失原因；如果没有这一行，排查环境变量问题会更慢。
    if not event_log_exists:  # 新增代码+Phase9VisibleTerminalGovernance：检查日志文件存在性；如果没有这一行，坏路径失败原因不清楚。
        hard_fail_reasons.append("event_log_path_exists")  # 新增代码+Phase9VisibleTerminalGovernance：记录日志不存在原因；如果没有这一行，用户难以定位 controller 是否启动。
    if not run_dir_matches_final_scenario:  # 新增代码+Phase9VisibleTerminalGovernance：检查 run 目录是否属于最终场景；如果没有这一行，普通场景会绕过最终门禁。
        hard_fail_reasons.append("final_visible_terminal_scenario_id")  # 新增代码+Phase9VisibleTerminalGovernance：记录场景 ID 不匹配原因；如果没有这一行，旧场景误用时不易发现。
    if not agent_ready_for_user_prompt:  # 新增代码+Phase9VisibleTerminalGovernance：检查 ready 事件是否缺失；如果没有这一行，终端未准备也可能通过。
        hard_fail_reasons.append("agent_ready_for_user_prompt")  # 新增代码+Phase9VisibleTerminalGovernance：记录 ready 缺失原因；如果没有这一行，终端启动失败不够直观。
    if not user_prompt_received:  # 新增代码+Phase9VisibleTerminalGovernance：检查用户 prompt 事件是否缺失；如果没有这一行，未真实输入也可能通过。
        hard_fail_reasons.append("user_prompt_received")  # 新增代码+Phase9VisibleTerminalGovernance：记录 prompt 缺失原因；如果没有这一行，真实交互失败不够直观。
    if not startup_screenshot_present:  # 新增代码+Phase9VisibleTerminalGovernance：检查启动截图是否缺失；如果没有这一行，真实可见窗口证据会变弱。
        hard_fail_reasons.append("startup_screenshot_present")  # 新增代码+Phase9VisibleTerminalGovernance：记录启动截图缺失；如果没有这一行，用户不知道缺哪张图。
    if not prompt_screenshot_present:  # 新增代码+Phase9VisibleTerminalGovernance：检查 prompt 截图是否缺失；如果没有这一行，真实输入证据会变弱。
        hard_fail_reasons.append("prompt_screenshot_present")  # 新增代码+Phase9VisibleTerminalGovernance：记录 prompt 截图缺失；如果没有这一行，排查截图链路会更慢。
    if not fresh_event_log:  # 新增代码+Phase9VisibleTerminalGovernance：检查新鲜度是否失败；如果没有这一行，旧 artifact 风险不会进入失败原因。
        hard_fail_reasons.append("fresh_event_log")  # 新增代码+Phase9VisibleTerminalGovernance：记录新鲜度失败；如果没有这一行，用户难以知道需要重新跑可见终端。
    passed = not hard_fail_reasons  # 新增代码+Phase9VisibleTerminalGovernance：只有所有硬门禁都满足才通过；如果没有这一行，局部证据可能被误判为完整验收。
    return {"model": PHASE9_VISIBLE_TERMINAL_GOVERNANCE_MODEL, "passed": passed, "event_log_env": PHASE9_VISIBLE_TERMINAL_EVENT_LOG_ENV, "event_log_path": raw_event_log, "scenario_id_expected": PHASE9_FINAL_VISIBLE_TERMINAL_SCENARIO_ID, "scenario_run_dir": str(run_dir) if run_dir else "", "run_dir_matches_final_scenario": run_dir_matches_final_scenario, "event_states": states, "agent_ready_for_user_prompt": agent_ready_for_user_prompt, "user_prompt_received": user_prompt_received, "startup_screenshot_path": str(startup_screenshot) if startup_screenshot else "", "prompt_screenshot_path": str(prompt_screenshot) if prompt_screenshot else "", "startup_screenshot_present": startup_screenshot_present, "prompt_screenshot_present": prompt_screenshot_present, "fresh_event_log": fresh_event_log, "age_seconds": age_seconds, "fresh_seconds_limit": PHASE9_VISIBLE_TERMINAL_FRESH_SECONDS, "hard_fail_reasons": hard_fail_reasons}  # 新增代码+Phase9VisibleTerminalGovernance：返回结构化可见终端证据报告；如果没有这一行，顶层矩阵无法审计规则十七证据。
# 新增代码+Phase9VisibleTerminalGovernance：函数段结束，evaluate_visible_terminal_e2e_evidence 到此结束；如果没有这个边界说明，初学者不容易看出可见终端门禁范围。


# 新增代码+Phase9VisibleTerminalGovernance：函数段开始，_top_level_load_json_file 读取 CLI 提供的真实桌面证据文件；如果没有这段函数，真实终端里无法把本轮闭环证据交给顶层矩阵。
def _top_level_load_json_file(path_text: str | None) -> dict[str, Any] | None:  # 新增代码+Phase9VisibleTerminalGovernance：声明 JSON 文件读取函数；如果没有这一行，main 会混杂参数处理和文件解析。
    if not path_text:  # 新增代码+Phase9VisibleTerminalGovernance：没有路径时返回空证据；如果没有这一行，默认 CLI 会错误尝试读取空路径。
        return None  # 新增代码+Phase9VisibleTerminalGovernance：返回 None 让矩阵保持默认失败；如果没有这一行，缺省运行可能异常退出。
    evidence_path = Path(path_text)  # 新增代码+Phase9VisibleTerminalGovernance：把字符串路径转成 Path；如果没有这一行，后续不能统一读取。
    try:  # 新增代码+Phase9VisibleTerminalGovernance：进入安全读取 JSON 文件区；如果没有这一行，坏路径会打断 CLI 输出。
        loaded = json.loads(evidence_path.read_text(encoding="utf-8", errors="replace"))  # 新增代码+Phase9VisibleTerminalGovernance：读取并解析 JSON 证据；如果没有这一行，真实终端无法用文件形式传入 Layer A 证据。
    except (OSError, json.JSONDecodeError):  # 新增代码+Phase9VisibleTerminalGovernance：捕获读取和解析失败；如果没有这一行，坏证据文件会让顶层矩阵没有完整失败报告。
        return None  # 新增代码+Phase9VisibleTerminalGovernance：读取失败时返回 None 让 Layer A 诚实失败；如果没有这一行，错误证据可能造成异常中断。
    return _top_level_safe_dict(loaded)  # 新增代码+Phase9VisibleTerminalGovernance：只返回字典证据；如果没有这一行，数组或字符串 JSON 可能污染矩阵。
# 新增代码+Phase9VisibleTerminalGovernance：函数段结束，_top_level_load_json_file 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 证据读取范围。


# 新增代码+Phase9VisibleTerminalGovernance：函数段开始，_top_level_cli_arg_value 从 argv 提取简单 flag 参数；如果没有这段函数，main 只能忽略真实证据文件路径。
def _top_level_cli_arg_value(argv: list[str], flag_name: str) -> str | None:  # 新增代码+Phase9VisibleTerminalGovernance：声明 CLI 参数读取函数；如果没有这一行，后续无法复用同一解析规则。
    if flag_name not in argv:  # 新增代码+Phase9VisibleTerminalGovernance：检查 flag 是否存在；如果没有这一行，缺省运行会误读参数。
        return None  # 新增代码+Phase9VisibleTerminalGovernance：不存在时返回 None；如果没有这一行，main 无法区分未传参和空值。
    index = argv.index(flag_name)  # 新增代码+Phase9VisibleTerminalGovernance：定位 flag 下标；如果没有这一行，函数不知道该取哪个后续值。
    if index + 1 >= len(argv):  # 新增代码+Phase9VisibleTerminalGovernance：检查 flag 后是否有值；如果没有这一行，缺值参数会触发越界。
        return None  # 新增代码+Phase9VisibleTerminalGovernance：缺值时返回 None 让门禁保持失败；如果没有这一行，坏命令行会崩溃。
    return str(argv[index + 1])  # 新增代码+Phase9VisibleTerminalGovernance：返回 flag 后的值；如果没有这一行，main 拿不到证据路径。
# 新增代码+Phase9VisibleTerminalGovernance：函数段结束，_top_level_cli_arg_value 到此结束；如果没有这个边界说明，初学者不容易看出参数解析范围。


# 新增代码+TopLevelComputerUseMatrix：函数段开始，_top_level_tool_names 从生产化报告提取工具名；如果没有这段函数，MCP/request_access 门禁无法判断工具面是否真实暴露。
def _top_level_tool_names(production_report: dict[str, Any]) -> set[str]:  # 新增代码+TopLevelComputerUseMatrix：声明工具名提取函数；如果没有这一行，后续门禁无法复用工具列表。
    status = production_report.get("status", {})  # 新增代码+TopLevelComputerUseMatrix：取出生产化报告里的状态段；如果没有这一行，工具列表没有数据来源。
    tools = status.get("tools", []) if isinstance(status, dict) else []  # 新增代码+TopLevelComputerUseMatrix：只在 status 是字典时读取 tools；如果没有这一行，坏报告结构会导致类型错误。
    tool_names: set[str] = set()  # 新增代码+TopLevelComputerUseMatrix：创建去重工具名集合；如果没有这一行，重复工具会让后续判断更混乱。
    for tool in tools:  # 新增代码+TopLevelComputerUseMatrix：逐个扫描工具描述；如果没有这一行，矩阵无法从列表中提取每个工具名。
        if isinstance(tool, dict) and isinstance(tool.get("name"), str):  # 新增代码+TopLevelComputerUseMatrix：只接受带字符串 name 的工具项；如果没有这一行，异常结构可能污染工具名集合。
            tool_names.add(tool["name"])  # 新增代码+TopLevelComputerUseMatrix：把合法工具名加入集合；如果没有这一行，工具面门禁永远无法识别已有工具。
    return tool_names  # 新增代码+TopLevelComputerUseMatrix：返回工具名集合；如果没有这一行，调用方拿不到提取结果。
# 新增代码+TopLevelComputerUseMatrix：函数段结束，_top_level_tool_names 到此结束；如果没有这个边界说明，初学者不容易看出工具名提取范围。


# 新增代码+TopLevelComputerUseMatrix：函数段开始，_top_level_claudecode_production_gates 生成 ClaudeCode 生产化一等门禁；如果没有这段函数，顶层矩阵只会停留在旧的散点能力清单。
def _top_level_claudecode_production_gates(production_report: dict[str, Any], visible_terminal_report: dict[str, Any] | None = None) -> dict[str, bool]:  # 修改代码+Phase9VisibleTerminalGovernance：声明生产化门禁汇总函数并接收真实终端证据；如果没有这个参数，规则十七无法成为 Layer B 的一等门禁。
    phase_results = production_report.get("phase_results", {})  # 新增代码+TopLevelComputerUseMatrix：读取 Phase76-89 的阶段结果；如果没有这一行，已有生产合约无法参与顶层判断。
    phase_results = phase_results if isinstance(phase_results, dict) else {}  # 新增代码+TopLevelComputerUseMatrix：保证阶段结果是字典；如果没有这一行，异常报告结构会让 get 调用崩溃。
    tool_names = _top_level_tool_names(production_report)  # 新增代码+TopLevelComputerUseMatrix：提取当前高层工具名；如果没有这一行，工具面相关门禁没有事实来源。
    inventory_text = _top_level_read_source("learning_agent/computer_use_mcp_v2/windows_runtime/windows_app_inventory.py")  # 新增代码+TopLevelComputerUseMatrix：读取应用清单安全过滤源码；如果没有这一行，installed app hardening 只能靠猜。
    session_text = _top_level_read_source("learning_agent/computer_use_mcp_v2/windows_runtime/session_context.py")  # 新增代码+TopLevelComputerUseMatrix：读取会话上下文源码；如果没有这一行，显示器钉住和授权会话状态无法被矩阵检查。
    persistent_text = _top_level_read_source("learning_agent/computer_use_mcp_v2/windows_runtime/persistent_grants.py")  # 新增代码+TopLevelComputerUseMatrix：读取持久授权源码；如果没有这一行，request_access 授权生命周期无法被矩阵检查。
    abort_text = _top_level_read_source("learning_agent/computer_use_mcp_v2/windows_runtime/abort_streaming_hooks.py")  # 新增代码+TopLevelComputerUseMatrix：读取 abort/streaming 钩子源码；如果没有这一行，全局中止和 stale lock 恢复缺少证据。
    lock_text = _top_level_read_source("learning_agent/computer_use_mcp_v2/windows_runtime/lock.py")  # 新增代码+TopLevelComputerUseMatrix：读取锁文件实现源码；如果没有这一行，stale lock 门禁无法确认底层锁语义。
    production_text = _top_level_read_source("learning_agent/computer_use_mcp_v2/windows_runtime/production_live_control.py")  # 新增代码+TopLevelComputerUseMatrix：读取生产控制合约源码；如果没有这一行，host cleanup 和原生权限诊断无法被交叉检查。
    image_text = _top_level_read_source("learning_agent/computer_use_mcp_v2/windows_runtime/image_messages.py")  # 新增代码+TopLevelComputerUseMatrix：读取截图消息构造源码；如果没有这一行，模型可见截图门禁无法确认图片块存在。
    message_text = _top_level_read_source("learning_agent/core/message_builders.py")  # 新增代码+TopLevelComputerUseMatrix：读取消息构建器源码；如果没有这一行，截图是否真正进入模型消息链路无法确认。
    status_text = _top_level_read_source("learning_agent/app/computer_status_renderer.py")  # 新增代码+TopLevelComputerUseMatrix：读取状态渲染源码；如果没有这一行，工具渲染状态门禁无法判断 UI 反馈能力。
    mcp_request_access_tool_surface_gate = bool("mcp__computer-use__request_access" in tool_names and any(name.startswith("mcp__computer-use__") for name in tool_names))  # 修改代码+ComputerUseMcpV2ResidualCleanup：治理矩阵只承认 v2 MCP 授权入口；如果没有这行代码，普通 request_access 和 mcp__computer-use__request_access 的重复暴露会被误判为成功。
    request_access_session_grant_gate = bool(mcp_request_access_tool_surface_gate and _top_level_source_contains_all(session_text, ["allowed_apps", "grant_flags", "grant_scope_matches_target", "deny_action_without_request_access"]) and _top_level_source_contains_all(persistent_text, ["requires_approval", "grant_expired", "grant_revoked", "request_access_session_id"]))  # 修改代码+RequestAccessToolSurface：要求 Phase 2 级会话范围匹配、无授权拒绝动作和持久会话标识都存在；如果没有这一行，Phase 1 只加工具面就会被误报成完整授权生命周期成熟。
    installed_app_inventory_hardening_gate = bool(_top_level_source_contains_all(inventory_text, ["sanitize_inventory_display_name", "APP_INVENTORY_HIGH_RISK_TOKENS", "APP_INVENTORY_BLOCKED_EXACT_NAMES"]))  # 新增代码+TopLevelComputerUseMatrix：确认应用清单具备脱敏和高风险过滤；如果没有这一行，危险系统项可能被顶层矩阵漏检。
    display_pin_coordinate_gate = bool(phase_results.get("phase79_display_coordinate_model") and _top_level_source_contains_all(session_text, ["selected_display", "last_screenshot_dims", "display_pinned"]))  # 新增代码+TopLevelComputerUseMatrix：要求显示器坐标模型和会话固定显示器状态同时存在；如果没有这一行，多显示器场景可能被误判为稳定。
    host_hide_cleanup_gate = bool(phase_results.get("phase85_turn_cleanup_contract") and _top_level_source_contains_all(session_text, ["hidden_windows", "cleanup_completed"]) and "unhide" in production_text.lower() and "host" in production_text.lower())  # 新增代码+TopLevelComputerUseMatrix：要求 host 隐藏/恢复和 cleanup 合约都有证据；如果没有这一行，宿主窗口污染用户桌面的风险会被忽略。
    stale_lock_recovery_gate = bool(_top_level_source_contains_all(abort_text, ["recover_stale_lock", "lock_released_after_recovery"]) and "stale" in lock_text.lower())  # 新增代码+TopLevelComputerUseMatrix：确认 stale lock 恢复路径和底层锁语义同时存在；如果没有这一行，崩溃后的死锁风险不会进入顶层治理。
    global_escape_abort_gate = bool(phase_results.get("phase84_global_abort_signal") and "registerEscHotkey" in abort_text)  # 新增代码+TopLevelComputerUseMatrix：必须看到全局 Escape 热键注册证据才放行；如果没有这一行，普通 controller abort fallback 会被误当成 ClaudeCode 级急停。
    clipboard_guard_gate = bool(phase_results.get("phase81_clipboard_save_verify_restore"))  # 新增代码+TopLevelComputerUseMatrix：复用剪贴板保存、校验、恢复阶段结果；如果没有这一行，剪贴板被污染的风险不会阻塞顶层成熟度。
    native_permission_diagnostics_gate = bool(_top_level_source_contains_all(production_text, ["ensureOsPermissions", "native_permission"]))  # 新增代码+TopLevelComputerUseMatrix：要求存在原生 OS 权限诊断入口；如果没有这一行，Windows 权限缺口会被包装层状态掩盖。
    model_visible_screenshot_gate = bool(_top_level_source_contains_all(image_text, ["image_url", "data:", "build_computer_use_image_blocks_from_tool_output"]) and _top_level_source_contains_all(message_text, ["tool_result_messages_to_dicts", "image_message_builder"]))  # 新增代码+TopLevelComputerUseMatrix：要求截图能构造成图片块并进入消息构建链路；如果没有这一行，agent 可能看不到自己刚操作后的屏幕。
    tool_rendering_status_gate = bool(mcp_request_access_tool_surface_gate and "Computer Use Tool Rendering" in status_text)  # 新增代码+TopLevelComputerUseMatrix：要求 MCP 工具面和专门工具渲染状态同时具备；如果没有这一行，普通状态文本可能被误当成 ClaudeCode 级工具反馈。
    visible_terminal_report = _top_level_safe_dict(visible_terminal_report)  # 新增代码+Phase9VisibleTerminalGovernance：清洗可见终端证据报告；如果没有这一行，坏报告类型可能让门禁异常中断。
    visible_terminal_e2e_gate = bool(visible_terminal_report.get("passed"))  # 修改代码+Phase9VisibleTerminalGovernance：只有真实可见终端证据通过时才放行；如果没有这一行，规则十七会继续固定失败或被静态检查绕过。
    return {  # 新增代码+TopLevelComputerUseMatrix：返回 ClaudeCode 生产化门禁字典；如果没有这一行，顶层报告没有可对照的生产化矩阵。
        "mcp_request_access_tool_surface_gate": mcp_request_access_tool_surface_gate,  # 新增代码+TopLevelComputerUseMatrix：输出 MCP/request_access 工具面门禁；如果没有这一行，后续无法精准追踪授权工具缺口。
        "request_access_session_grant_gate": request_access_session_grant_gate,  # 新增代码+TopLevelComputerUseMatrix：输出 request_access 会话授权生命周期门禁；如果没有这一行，授权状态和工具面会混在一起看不清。
        "installed_app_inventory_hardening_gate": installed_app_inventory_hardening_gate,  # 新增代码+TopLevelComputerUseMatrix：输出应用清单安全门禁；如果没有这一行，已有安全基础不会被顶层矩阵记录。
        "display_pin_coordinate_gate": display_pin_coordinate_gate,  # 新增代码+TopLevelComputerUseMatrix：输出显示器钉住坐标门禁；如果没有这一行，多屏坐标稳定性缺口会被漏掉。
        "host_hide_cleanup_gate": host_hide_cleanup_gate,  # 新增代码+TopLevelComputerUseMatrix：输出宿主隐藏和清理门禁；如果没有这一行，桌面污染和清理遗漏风险不会阻塞成熟度。
        "stale_lock_recovery_gate": stale_lock_recovery_gate,  # 新增代码+TopLevelComputerUseMatrix：输出 stale lock 恢复门禁；如果没有这一行，长任务中断后的恢复能力无法被治理。
        "global_escape_abort_gate": global_escape_abort_gate,  # 新增代码+TopLevelComputerUseMatrix：输出全局 Escape 急停门禁；如果没有这一行，安全中止能力会被低估或误报。
        "clipboard_guard_gate": clipboard_guard_gate,  # 新增代码+TopLevelComputerUseMatrix：输出剪贴板保护门禁；如果没有这一行，复制粘贴副作用不会进入顶层检查。
        "native_permission_diagnostics_gate": native_permission_diagnostics_gate,  # 新增代码+TopLevelComputerUseMatrix：输出原生权限诊断门禁；如果没有这一行，平台级权限问题无法被矩阵明确暴露。
        "model_visible_screenshot_gate": model_visible_screenshot_gate,  # 新增代码+TopLevelComputerUseMatrix：输出模型可见截图门禁；如果没有这一行，观察-动作-再观察闭环可能只停留在本地工具层。
        "tool_rendering_status_gate": tool_rendering_status_gate,  # 新增代码+TopLevelComputerUseMatrix：输出工具渲染状态门禁；如果没有这一行，用户和模型看不到足够清晰的工具执行反馈。
        "visible_terminal_e2e_gate": visible_terminal_e2e_gate,  # 新增代码+TopLevelComputerUseMatrix：输出真实可见终端 E2E 门禁；如果没有这一行，项目规则十七无法成为顶层成熟度条件。
    }  # 新增代码+TopLevelComputerUseMatrix：结束生产化门禁字典；如果没有这一行，Python 无法正确结束返回结构。
# 新增代码+TopLevelComputerUseMatrix：函数段结束，_top_level_claudecode_production_gates 到此结束；如果没有这个边界说明，初学者不容易看出 ClaudeCode 生产化层的完整范围。


# 新增代码+TopLevelComputerUseMatrix：函数段开始，run_computer_use_top_level_governance_matrix 运行顶层治理矩阵；如果没有这段函数，测试、CLI、后续验收都没有统一入口。
def run_computer_use_top_level_governance_matrix(real_desktop_evidence: dict[str, Any] | None = None, visible_terminal_event_log: str | Path | None = None) -> dict[str, Any]:  # 修改代码+Phase9VisibleTerminalGovernance：声明顶层矩阵主函数并允许注入真实桌面与可见终端证据；如果没有这些参数，最终验收结果无法进入顶层治理。
    visible_terminal_report = evaluate_visible_terminal_e2e_evidence(visible_terminal_event_log)  # 新增代码+Phase9VisibleTerminalGovernance：先校验真实可见终端证据；如果没有这一行，Layer B 的最终门禁没有事实来源。
    real_desktop_report = run_phase121_universal_final_maturity_matrix(real_desktop_evidence=real_desktop_evidence)  # 修改代码+Phase9VisibleTerminalGovernance：运行真实桌面最终成熟度矩阵并传入 Phase 8 证据；如果没有这一行，Layer A 不能由真实闭环验收驱动通过。
    production_report = run_phase76_89_windows_live_control_contract(real_smoke=False)  # 新增代码+TopLevelComputerUseMatrix：运行 ClaudeCode 生产化合约但不伪造真实烟测；如果没有这一行，Layer B 缺少现有生产化证据。
    production_gates = _top_level_claudecode_production_gates(production_report, visible_terminal_report=visible_terminal_report)  # 修改代码+Phase9VisibleTerminalGovernance：生成一等生产化门禁并纳入可见终端报告；如果没有这一行，规则十七无法影响顶层 passed。
    layer_a_passed = bool(real_desktop_report.get("passed"))  # 新增代码+TopLevelComputerUseMatrix：读取真实桌面闭环层是否通过；如果没有这一行，顶层 passed 无法受到真实桌面约束。
    layer_b_passed = bool(all(production_gates.values()))  # 新增代码+TopLevelComputerUseMatrix：要求所有 ClaudeCode 生产化门禁都通过；如果没有这一行，某个关键门禁失败也可能被整体放行。
    paint_report = real_desktop_report.get("reports", {}).get("paint", {}) if isinstance(real_desktop_report.get("reports", {}), dict) else {}  # 新增代码+TopLevelComputerUseMatrix：取出 Paint 代表性场景报告；如果没有这一行，recording sender 是否真实派发无法被顶层说明。
    recording_sender_not_accepted_as_real = not bool(paint_report.get("physical_desktop_dispatch_performed", True)) if isinstance(paint_report, dict) else True  # 新增代码+TopLevelComputerUseMatrix：确认录制式 sender 不能冒充真实桌面动作；如果没有这一行，顶层报告不够明确地区分模拟记录和真实输入。
    passed = bool(layer_a_passed and layer_b_passed)  # 新增代码+TopLevelComputerUseMatrix：只有真实桌面层和生产化层同时通过才算顶层通过；如果没有这一行，矩阵可能被单层成功误导。
    return {  # 新增代码+TopLevelComputerUseMatrix：返回完整顶层治理报告；如果没有这一行，调用方拿不到结构化结果。
        "marker": COMPUTER_USE_TOP_LEVEL_GOVERNANCE_MARKER,  # 新增代码+TopLevelComputerUseMatrix：输出稳定 marker；如果没有这一行，真实终端验收不容易定位报告。
        "model": COMPUTER_USE_TOP_LEVEL_GOVERNANCE_MODEL,  # 新增代码+TopLevelComputerUseMatrix：输出矩阵模型名；如果没有这一行，多矩阵并存时无法区分来源。
        "passed": passed,  # 新增代码+TopLevelComputerUseMatrix：输出最终是否通过；如果没有这一行，CI 和人工验收无法判断顶层结果。
        "layer_a_real_desktop_gate_passed": layer_a_passed,  # 新增代码+TopLevelComputerUseMatrix：输出真实桌面层状态；如果没有这一行，用户看不出是否卡在真实桌面闭环。
        "layer_b_claudecode_production_gate_passed": layer_b_passed,  # 新增代码+TopLevelComputerUseMatrix：输出 ClaudeCode 生产化层状态；如果没有这一行，用户看不出是否卡在生产化生命周期。
        "real_desktop_closed_loop_ready": layer_a_passed,  # 新增代码+TopLevelComputerUseMatrix：给真实桌面闭环提供直观 ready 字段；如果没有这一行，后续矩阵消费者要重复理解 Layer A。
        "production_integration_lifecycle_ready": layer_b_passed,  # 新增代码+TopLevelComputerUseMatrix：给生产化生命周期提供直观 ready 字段；如果没有这一行，ClaudeCode 对齐状态不够醒目。
        "claudecode_production_gates": production_gates,  # 新增代码+TopLevelComputerUseMatrix：输出所有一等生产化门禁；如果没有这一行，后续开发无法逐项对照修复。
        "layers": {  # 新增代码+TopLevelComputerUseMatrix：输出两层治理摘要；如果没有这一行，报告缺少人类友好的层级结构。
            "real_desktop": {  # 新增代码+TopLevelComputerUseMatrix：开始真实桌面层摘要；如果没有这一行，Layer A 结果会散落在原始报告里。
                "passed": layer_a_passed,  # 新增代码+TopLevelComputerUseMatrix：记录真实桌面层通过状态；如果没有这一行，Layer A 摘要不完整。
                "source_matrix": "universal_final_maturity_matrix",  # 新增代码+TopLevelComputerUseMatrix：记录 Layer A 来源矩阵；如果没有这一行，后续定位真实桌面证据会更慢。
            },  # 新增代码+TopLevelComputerUseMatrix：结束真实桌面层摘要；如果没有这一行，Python 无法正确关闭该字典。
            "claudecode_production": {  # 新增代码+TopLevelComputerUseMatrix：开始 ClaudeCode 生产化层摘要；如果没有这一行，Layer B 结果会缺少独立入口。
                "passed": layer_b_passed,  # 新增代码+TopLevelComputerUseMatrix：记录生产化层通过状态；如果没有这一行，Layer B 摘要不完整。
                "source_matrix": "phase76_89_windows_live_control_contract",  # 新增代码+TopLevelComputerUseMatrix：记录 Layer B 来源矩阵；如果没有这一行，后续定位生产化证据会更慢。
                "gates": production_gates,  # 新增代码+TopLevelComputerUseMatrix：在层摘要里重复暴露门禁；如果没有这一行，消费者需要跳到顶层其他字段再找。
            },  # 新增代码+TopLevelComputerUseMatrix：结束 ClaudeCode 生产化层摘要；如果没有这一行，Python 无法正确关闭该字典。
        },  # 新增代码+TopLevelComputerUseMatrix：结束两层治理摘要；如果没有这一行，Python 无法正确关闭 layers。
        "reports": {  # 新增代码+TopLevelComputerUseMatrix：输出原始子报告；如果没有这一行，后续审计无法追溯顶层判断依据。
            "real_desktop": real_desktop_report,  # 新增代码+TopLevelComputerUseMatrix：挂载真实桌面原始报告；如果没有这一行，Layer A 失败原因难以追踪。
            "claudecode_production": production_report,  # 新增代码+TopLevelComputerUseMatrix：挂载生产化原始报告；如果没有这一行，Layer B 失败原因难以追踪。
            "visible_terminal_governance": visible_terminal_report,  # 新增代码+Phase9VisibleTerminalGovernance：挂载规则十七真实可见终端证据报告；如果没有这一行，最终验收失败原因无法追溯到具体事件或截图。
        },  # 新增代码+TopLevelComputerUseMatrix：结束原始子报告集合；如果没有这一行，Python 无法正确关闭 reports。
        "no_static_only_gate_can_pass_final": True,  # 新增代码+TopLevelComputerUseMatrix：声明静态检查不能单独让最终门禁通过；如果没有这一行，用户可能误以为源码 token 足够证明成熟。
        "representative_apps_are_acceptance_only": True,  # 新增代码+TopLevelComputerUseMatrix：声明代表应用只是验收样本不是全部能力；如果没有这一行，矩阵容易被误解成只支持少数应用。
        "recording_sender_not_accepted_as_real": recording_sender_not_accepted_as_real,  # 新增代码+TopLevelComputerUseMatrix：明确录制式 sender 不能算真实桌面输入；如果没有这一行，最关键的假阳性风险不够醒目。
    }  # 新增代码+TopLevelComputerUseMatrix：结束完整报告字典；如果没有这一行，Python 无法正确结束返回结构。
# 新增代码+TopLevelComputerUseMatrix：函数段结束，run_computer_use_top_level_governance_matrix 到此结束；如果没有这个边界说明，初学者不容易看出顶层矩阵主入口范围。


# 新增代码+TopLevelComputerUseMatrix：函数段开始，computer_use_top_level_governance_cli_line 生成单行终端摘要；如果没有这段函数，真实终端验收时需要翻很长 JSON 才能看结论。
def computer_use_top_level_governance_cli_line(report: dict[str, Any]) -> str:  # 新增代码+TopLevelComputerUseMatrix：声明 CLI 单行摘要函数；如果没有这一行，测试和命令行无法复用相同输出格式。
    production_gates = report.get("claudecode_production_gates", {})  # 新增代码+TopLevelComputerUseMatrix：取出生产化门禁；如果没有这一行，CLI 无法逐项输出 ClaudeCode 对齐状态。
    production_gates = production_gates if isinstance(production_gates, dict) else {}  # 新增代码+TopLevelComputerUseMatrix：保证门禁集合是字典；如果没有这一行，坏报告结构会让 CLI 崩溃。
    tokens = [  # 新增代码+TopLevelComputerUseMatrix：开始组装稳定 token 列表；如果没有这一行，CLI 输出会缺少固定顺序。
        str(report.get("marker", COMPUTER_USE_TOP_LEVEL_GOVERNANCE_MARKER)),  # 新增代码+TopLevelComputerUseMatrix：加入 marker token；如果没有这一行，终端验收无法快速确认报告类型。
        f"passed={_top_level_bool_token(report.get('passed'))}",  # 新增代码+TopLevelComputerUseMatrix：加入最终通过状态；如果没有这一行，用户需要读 JSON 才知道总结果。
        f"layer_a_real_desktop_gate_passed={_top_level_bool_token(report.get('layer_a_real_desktop_gate_passed'))}",  # 新增代码+TopLevelComputerUseMatrix：加入真实桌面层状态；如果没有这一行，Layer A 失败不够醒目。
        f"layer_b_claudecode_production_gate_passed={_top_level_bool_token(report.get('layer_b_claudecode_production_gate_passed'))}",  # 新增代码+TopLevelComputerUseMatrix：加入生产化层状态；如果没有这一行，Layer B 失败不够醒目。
        f"real_desktop_closed_loop_ready={_top_level_bool_token(report.get('real_desktop_closed_loop_ready'))}",  # 新增代码+TopLevelComputerUseMatrix：加入真实桌面 ready 状态；如果没有这一行，人类读者不容易快速理解 Layer A。
        f"production_integration_lifecycle_ready={_top_level_bool_token(report.get('production_integration_lifecycle_ready'))}",  # 新增代码+TopLevelComputerUseMatrix：加入生产化生命周期 ready 状态；如果没有这一行，ClaudeCode 对齐状态不够直观。
    ]  # 新增代码+TopLevelComputerUseMatrix：结束基础 token 列表；如果没有这一行，Python 无法继续追加门禁字段。
    for gate_name in sorted(production_gates):  # 新增代码+TopLevelComputerUseMatrix：按名称稳定输出所有生产化门禁；如果没有这一行，CLI 字段顺序会随字典变化而漂移。
        tokens.append(f"{gate_name}={_top_level_bool_token(production_gates.get(gate_name))}")  # 新增代码+TopLevelComputerUseMatrix：追加单个门禁状态；如果没有这一行，后续开发无法从终端逐项确认缺口。
    return " ".join(tokens)  # 新增代码+TopLevelComputerUseMatrix：返回空格分隔的单行摘要；如果没有这一行，调用方拿不到可打印字符串。
# 新增代码+TopLevelComputerUseMatrix：函数段结束，computer_use_top_level_governance_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 摘要逻辑范围。


# 新增代码+TopLevelComputerUseMatrix：函数段开始，main 提供命令行入口；如果没有这段函数，真实终端和 CI 不能直接运行顶层矩阵。
def main(argv: list[str] | None = None) -> int:  # 新增代码+TopLevelComputerUseMatrix：声明命令行入口函数；如果没有这一行，模块无法返回标准退出码。
    safe_argv = list(argv) if argv is not None else list(sys.argv[1:])  # 修改代码+Phase9CliArgvFix：显式测试参数优先，否则读取 python -m 的真实进程参数；如果没有这一行，真实终端传入的 evidence 和 event-log 参数会被全部忽略。
    real_desktop_evidence_path = _top_level_cli_arg_value(safe_argv, "--real-desktop-evidence")  # 新增代码+Phase9VisibleTerminalGovernance：读取真实桌面闭环证据文件参数；如果没有这一行，Layer A 只能保持默认失败。
    visible_terminal_event_log = _top_level_cli_arg_value(safe_argv, "--visible-terminal-event-log")  # 新增代码+Phase9VisibleTerminalGovernance：读取显式可见终端事件日志参数；如果没有这一行，CLI 只能依赖环境变量。
    real_desktop_evidence = _top_level_load_json_file(real_desktop_evidence_path)  # 新增代码+Phase9VisibleTerminalGovernance：把证据文件转成字典；如果没有这一行，真实终端无法通过文件把 Phase 8 闭环交给矩阵。
    report = run_computer_use_top_level_governance_matrix(real_desktop_evidence=real_desktop_evidence, visible_terminal_event_log=visible_terminal_event_log)  # 修改代码+Phase9VisibleTerminalGovernance：运行顶层治理矩阵并传入可选证据；如果没有这一行，CLI 证据参数不会生效。
    print(computer_use_top_level_governance_cli_line(report))  # 新增代码+TopLevelComputerUseMatrix：先打印人类和脚本都易读的单行摘要；如果没有这一行，真实终端验收不够醒目。
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))  # 新增代码+TopLevelComputerUseMatrix：再打印完整 JSON 报告；如果没有这一行，失败原因无法被完整审计。
    print(COMPUTER_USE_TOP_LEVEL_GOVERNANCE_MARKER)  # 新增代码+TopLevelComputerUseMatrix：最后再次打印 marker 作为终端锚点；如果没有这一行，长输出末尾不容易确认命令已运行到结束。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+TopLevelComputerUseMatrix：通过时返回 0，未成熟时返回 1；如果没有这一行，CI 可能把失败矩阵误当成功命令。
# 新增代码+TopLevelComputerUseMatrix：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


__all__ = [  # 新增代码+TopLevelComputerUseMatrix：声明对外稳定 API；如果没有这一行，后续导入方不清楚哪些名字是正式接口。
    "COMPUTER_USE_TOP_LEVEL_GOVERNANCE_MARKER",  # 新增代码+TopLevelComputerUseMatrix：导出顶层 marker；如果没有这一行，测试和验收脚本无法稳定引用 marker。
    "COMPUTER_USE_TOP_LEVEL_GOVERNANCE_MODEL",  # 新增代码+TopLevelComputerUseMatrix：导出矩阵模型名；如果没有这一行，外部无法识别报告模型。
    "PHASE9_FINAL_VISIBLE_TERMINAL_SCENARIO_ID",  # 新增代码+Phase9VisibleTerminalGovernance：导出最终可见终端场景 ID；如果没有这一行，测试和 scenario 可能无法复用同一个名字。
    "PHASE9_VISIBLE_TERMINAL_EVENT_LOG_ENV",  # 新增代码+Phase9VisibleTerminalGovernance：导出事件日志环境变量名；如果没有这一行，外部工具无法稳定知道 controller 注入点。
    "PHASE9_VISIBLE_TERMINAL_GOVERNANCE_MODEL",  # 新增代码+Phase9VisibleTerminalGovernance：导出可见终端证据模型名；如果没有这一行，外部报告消费者无法区分 Phase 9 子报告。
    "evaluate_visible_terminal_e2e_evidence",  # 新增代码+Phase9VisibleTerminalGovernance：导出可见终端证据校验函数；如果没有这一行，测试和验收脚本无法复用规则十七门禁。
    "computer_use_top_level_governance_cli_line",  # 新增代码+TopLevelComputerUseMatrix：导出 CLI 摘要函数；如果没有这一行，终端格式测试无法复用函数。
    "main",  # 新增代码+TopLevelComputerUseMatrix：导出命令行入口；如果没有这一行，外部无法直接调用入口测试。
    "run_computer_use_top_level_governance_matrix",  # 新增代码+TopLevelComputerUseMatrix：导出顶层矩阵主函数；如果没有这一行，后续开发无法复用报告生成器。
]  # 新增代码+TopLevelComputerUseMatrix：结束导出清单；如果没有这一行，Python 无法正确结束列表。


if __name__ == "__main__":  # 新增代码+TopLevelComputerUseMatrix：文件入口段开始，允许 python -m 直接执行；如果没有这一行，模块直接运行不会触发矩阵。
    raise SystemExit(main())  # 新增代码+TopLevelComputerUseMatrix：把 main 返回值转成进程退出码；如果没有这一行，未成熟矩阵不会用退出码提醒 CI 和用户。
# 新增代码+TopLevelComputerUseMatrix：文件入口段结束，本模块代码到此结束；如果没有这个边界说明，初学者不容易看出直接运行逻辑范围。
