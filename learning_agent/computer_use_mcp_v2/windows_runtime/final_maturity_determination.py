"""Phase148E Computer Use 最终成熟度判定器。"""  # 新增代码+Phase148EFinalMaturity：说明本文件负责汇总 Phase148A-D 证据并给出最终成熟度等级；如果没有这一行，读者无法快速知道模块用途。
from __future__ import annotations  # 新增代码+Phase148EFinalMaturity：启用稳定的延迟类型注解；如果没有这一行，复杂类型在旧解释环境中更容易提前求值出错。

import argparse  # 新增代码+Phase148EFinalMaturity：导入命令行参数工具；如果没有这一行，真实终端无法传入 evidence root 和 final gate 状态。
import json  # 新增代码+Phase148EFinalMaturity：导入 JSON 工具；如果没有这一行，模块无法读取和写入结构化证据文件。
from pathlib import Path  # 新增代码+Phase148EFinalMaturity：导入路径对象；如果没有这一行，跨目录证据读取和报告写入会更容易写错。
from typing import Any  # 新增代码+Phase148EFinalMaturity：导入动态 JSON 类型；如果没有这一行，公开接口无法清楚表达字典输入输出。

from learning_agent.computer_use_mcp_v2.windows_runtime.post_parity_benchmark_matrix import evaluate_post_parity_benchmark_matrix  # 新增代码+Phase148EFinalMaturity：复用 Phase148B benchmark 矩阵；如果没有这一行，最终判定会重复实现并可能和既有 gate 漂移。

COMPUTER_USE_FINAL_MATURITY_MARKER = "COMPUTER_USE_FINAL_MATURITY_READY"  # 新增代码+Phase148EFinalMaturity：定义最终验收稳定 marker；如果没有这一行，acceptance controller 无法可靠匹配最终判定输出。
MATURITY_NOT_MATURE = "NOT_MATURE"  # 新增代码+Phase148EFinalMaturity：定义未成熟等级；如果没有这一行，治理或安全证据缺失时没有明确低等级。
MATURITY_GOVERNED_ONLY = "MATURE_GOVERNED_ONLY"  # 修改代码+Phase149ExplorerFileRoundtrip：定义治理成熟等级；如果没有这一行，当前未满 7/7 的实战证据无法被诚实归类。
MATURITY_PRACTICAL = "MATURE_PRACTICAL"  # 新增代码+Phase148EFinalMaturity：定义实战成熟等级；如果没有这一行，未来 7/7 真实 GUI 后没有中间目标。
MATURITY_CLAUDECODE_PARITY = "CLAUDECODE_PARITY_OR_BETTER"  # 新增代码+Phase148EFinalMaturity：定义 ClaudeCode 对齐或超过等级；如果没有这一行，最高成熟度没有稳定名称。
PHASE148B_EVIDENCE = Path("learning_agent/memory/computer_use/post_parity/phase148b_benchmark_evidence_20260613.json")  # 新增代码+Phase148EFinalMaturity：固定 Phase148B 原始 benchmark evidence 路径；如果没有这一行，最终判定找不到已通过的基准扩展证据。
PHASE148C_EVIDENCE = Path("learning_agent/memory/computer_use/post_parity/phase148c_fresh_benchmark_evidence_20260613.json")  # 修改代码+Phase149ExplorerFileRoundtrip：固定 Phase148C fresh evidence 路径；如果没有这一行，最终判定无法统计最新真实 GUI 覆盖比例。
PHASE148D_INVENTORY = Path("learning_agent/memory/computer_use/post_parity/phase148d_failure_inventory_20260613.json")  # 新增代码+Phase148EFinalMaturity：固定 Phase148D failure inventory 路径；如果没有这一行，最终判定无法列出剩余缺口。
FINAL_MANIFEST = Path("learning_agent/memory/computer_use/post_parity/final_maturity_evidence_manifest_20260613.json")  # 新增代码+Phase148EFinalMaturity：固定最终机器可读 manifest 路径；如果没有这一行，后续 agent 无法复用判定证据。
FINAL_REPORT = Path("agent_memory/computer_use_final_maturity_determination_20260613.md")  # 新增代码+Phase148EFinalMaturity：固定最终人类可读报告路径；如果没有这一行，用户难以查看成熟度结论。
PHASE148A_REPORT = Path("agent_memory/computer_use_current_maturity_audit_phase148a_20260613.md")  # 新增代码+Phase148EFinalMaturity：固定 Phase148A 治理审计报告路径；如果没有这一行，最终判定无法确认治理底座存在。
CLAUDECODE_ALIGNMENT_MANIFEST = Path("learning_agent/memory/computer_use/claudecode_alignment/claudecode_alignment_evidence_20260613.json")  # 新增代码+ClaudeCodeAlignmentMatrix：固定 ClaudeCode 对齐矩阵 manifest 路径；如果没有这一行，最终成熟度判定器无法读取新矩阵结果。


# 新增代码+Phase148EFinalMaturity：函数段开始，_bool_token 把布尔值转成小写 token；如果没有这个函数，summary line 的 true/false 大小写可能不稳定。
def _bool_token(value: Any) -> str:  # 新增代码+Phase148EFinalMaturity：声明布尔 token helper；如果没有这一行，调用方需要重复写格式化逻辑。
    return "true" if bool(value) else "false"  # 新增代码+Phase148EFinalMaturity：返回 acceptance 场景容易匹配的小写布尔值；如果没有这一行，终端断言可能因为大小写失败。
# 新增代码+Phase148EFinalMaturity：函数段结束，_bool_token 到此结束；如果没有这段边界说明，初学者不容易看出格式化 helper 范围。


# 新增代码+Phase148EFinalMaturity：函数段开始，_load_json_file 安全读取证据 JSON；如果没有这个函数，缺文件或坏 JSON 会让最终判定直接崩溃。
def _load_json_file(path: Path) -> dict[str, Any]:  # 新增代码+Phase148EFinalMaturity：声明 JSON 读取 helper；如果没有这一行，证据读取没有统一入口。
    if not path.exists():  # 新增代码+Phase148EFinalMaturity：检查文件是否存在；如果没有这一行，缺失证据会变成底层异常而不是可读状态。
        return {"load_ok": False, "load_error": f"missing:{path}"}  # 新增代码+Phase148EFinalMaturity：返回缺文件结构化错误；如果没有这一行，报告无法告诉用户缺哪份证据。
    try:  # 新增代码+Phase148EFinalMaturity：开始保护 JSON 解析；如果没有这一行，坏 JSON 会中断整个最终判定。
        payload = json.loads(path.read_text(encoding="utf-8-sig"))  # 新增代码+Phase148EFinalMaturity：读取 UTF-8 或带 BOM 的 JSON；如果没有这一行，证据内容无法进入评分器。
    except json.JSONDecodeError as error:  # 新增代码+Phase148EFinalMaturity：捕获 JSON 格式错误；如果没有这一行，用户看不到明确解析失败原因。
        return {"load_ok": False, "load_error": f"invalid_json:{error}"}  # 新增代码+Phase148EFinalMaturity：返回坏 JSON 结构化错误；如果没有这一行，报告无法定位证据损坏。
    if not isinstance(payload, dict):  # 新增代码+Phase148EFinalMaturity：确认顶层是对象；如果没有这一行，数组或字符串会污染后续 .get 调用。
        return {"load_ok": False, "load_error": f"not_object:{path}"}  # 新增代码+Phase148EFinalMaturity：返回类型错误；如果没有这一行，坏结构会造成不清楚的评分异常。
    payload["load_ok"] = True  # 新增代码+Phase148EFinalMaturity：标记读取成功；如果没有这一行，调用方无法区分真实 false 和未加载。
    return payload  # 新增代码+Phase148EFinalMaturity：返回证据对象；如果没有这一行，调用方拿不到 JSON 内容。
# 新增代码+Phase148EFinalMaturity：函数段结束，_load_json_file 到此结束；如果没有这段边界说明，初学者不容易看出读取逻辑范围。


# 新增代码+Phase148EFinalMaturity：函数段开始，_safe_benchmark_evidence 取出 benchmark_evidence 列表；如果没有这个函数，坏证据结构可能被误传给矩阵。
def _safe_benchmark_evidence(payload: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+Phase148EFinalMaturity：声明 evidence 列表 helper；如果没有这一行，评分器会重复做类型保护。
    evidence = payload.get("benchmark_evidence")  # 新增代码+Phase148EFinalMaturity：读取 benchmark_evidence 字段；如果没有这一行，矩阵没有输入来源。
    if not isinstance(evidence, list):  # 新增代码+Phase148EFinalMaturity：确认字段是列表；如果没有这一行，坏字段会导致迭代异常。
        return []  # 新增代码+Phase148EFinalMaturity：坏结构按空证据处理；如果没有这一行，最终判定无法降级为 NOT_MATURE 或治理成熟。
    return [item for item in evidence if isinstance(item, dict)]  # 新增代码+Phase148EFinalMaturity：只保留字典证据项；如果没有这一行，非字典项可能污染矩阵统计。
# 新增代码+Phase148EFinalMaturity：函数段结束，_safe_benchmark_evidence 到此结束；如果没有这段边界说明，初学者不容易看出证据清洗范围。


# 新增代码+Phase148EFinalMaturity：函数段开始，collect_maturity_evidence 汇总 Phase148A-D 证据；如果没有这个函数，最终评分没有统一事实来源。
def collect_maturity_evidence(repo_root: str | Path) -> dict[str, Any]:  # 新增代码+Phase148EFinalMaturity：声明成熟度证据收集入口；如果没有这一行，测试和 CLI 无法复用收集逻辑。
    root = Path(repo_root)  # 新增代码+Phase148EFinalMaturity：把输入仓库根目录规范成 Path；如果没有这一行，后续路径拼接不稳定。
    phase148a_report_path = root / PHASE148A_REPORT  # 新增代码+Phase148EFinalMaturity：定位 Phase148A 报告；如果没有这一行，治理底座无法被检查。
    phase148b_path = root / PHASE148B_EVIDENCE  # 新增代码+Phase148EFinalMaturity：定位 Phase148B evidence；如果没有这一行，原始 benchmark gate 无法被检查。
    phase148c_path = root / PHASE148C_EVIDENCE  # 新增代码+Phase148EFinalMaturity：定位 Phase148C evidence；如果没有这一行，fresh 真实 GUI 数量无法统计。
    phase148d_path = root / PHASE148D_INVENTORY  # 新增代码+Phase148EFinalMaturity：定位 Phase148D inventory；如果没有这一行，缺口和失败归因无法进入最终报告。
    claudecode_alignment_path = root / CLAUDECODE_ALIGNMENT_MANIFEST  # 新增代码+ClaudeCodeAlignmentMatrix：定位 ClaudeCode 对齐矩阵 manifest；如果没有这一行，最终评分无法知道是否已对齐 ClaudeCode。
    phase148b_payload = _load_json_file(phase148b_path)  # 新增代码+Phase148EFinalMaturity：读取 Phase148B evidence；如果没有这一行，无法验证 benchmark 扩展 gate。
    phase148c_payload = _load_json_file(phase148c_path)  # 新增代码+Phase148EFinalMaturity：读取 Phase148C evidence；如果没有这一行，无法知道当前 fresh 实战覆盖数。
    phase148d_payload = _load_json_file(phase148d_path)  # 新增代码+Phase148EFinalMaturity：读取 Phase148D inventory；如果没有这一行，无法区分 bug 和已知覆盖缺口。
    claudecode_alignment_payload = _load_json_file(claudecode_alignment_path)  # 新增代码+ClaudeCodeAlignmentMatrix：读取 ClaudeCode 对齐矩阵 evidence；如果没有这一行，矩阵通过也不会进入最终判定。
    phase148b_matrix = evaluate_post_parity_benchmark_matrix(_safe_benchmark_evidence(phase148b_payload))  # 新增代码+Phase148EFinalMaturity：用 Phase148B 原始 evidence 复算矩阵；如果没有这一行，benchmark gate 可能只靠旧报告文本。
    phase148c_matrix = evaluate_post_parity_benchmark_matrix(_safe_benchmark_evidence(phase148c_payload))  # 新增代码+Phase148EFinalMaturity：用 Phase148C fresh evidence 复算矩阵；如果没有这一行，缺少 4 类真实 GUI 的事实不会被机器确认。
    phase148c_entries = _safe_benchmark_evidence(phase148c_payload)  # 新增代码+Phase148EFinalMaturity：缓存 Phase148C 条目；如果没有这一行，后续统计会重复清洗证据。
    real_gui_entries = [item for item in phase148c_entries if item.get("real_gui_backing") is True and item.get("physical_dispatch") is True]  # 新增代码+Phase148EFinalMaturity：统计真实 GUI 且物理派发的条目；如果没有这一行，contract-only 证据会被误当实战能力。
    visible_terminal_entries = [item for item in phase148c_entries if item.get("visible_terminal_verified") is True]  # 新增代码+Phase148EFinalMaturity：统计真实可见终端验收通过条目；如果没有这一行，规则十七覆盖度不可见。
    known_gaps = phase148d_payload.get("known_gaps") if isinstance(phase148d_payload.get("known_gaps"), list) else []  # 新增代码+Phase148EFinalMaturity：读取已确认缺口列表；如果没有这一行，最终报告无法列出下一步要补什么。
    safety_gap_count = int(phase148d_payload.get("safety_boundary_failure_count", 0) or 0) if phase148d_payload.get("load_ok") is True else 0  # 新增代码+Phase148EFinalMaturity：读取安全边界失败数；如果没有这一行，安全问题无法压低成熟度等级。
    return {  # 新增代码+Phase148EFinalMaturity：开始返回统一证据字典；如果没有这一行，调用方拿不到汇总结果。
        "marker": COMPUTER_USE_FINAL_MATURITY_MARKER,  # 新增代码+Phase148EFinalMaturity：写入最终 marker；如果没有这一行，manifest 难以被后续工具识别。
        "repo_root": str(root),  # 新增代码+Phase148EFinalMaturity：记录仓库根目录；如果没有这一行，后续复盘不知道证据基于哪个项目。
        "phase148a_governance": phase148a_report_path.exists(),  # 新增代码+Phase148EFinalMaturity：记录 Phase148A 治理报告是否存在；如果没有这一行，治理成熟底座无法进入评分。
        "phase148a_report_path": str(phase148a_report_path),  # 新增代码+Phase148EFinalMaturity：记录 Phase148A 报告路径；如果没有这一行，用户无法追溯治理证据。
        "phase148b_evidence_path": str(phase148b_path),  # 新增代码+Phase148EFinalMaturity：记录 Phase148B evidence 路径；如果没有这一行，benchmark gate 来源不透明。
        "phase148b_payload_loaded": phase148b_payload.get("load_ok") is True,  # 新增代码+Phase148EFinalMaturity：记录 Phase148B 是否加载成功；如果没有这一行，缺证据时原因不清楚。
        "phase148b_matrix": phase148b_matrix,  # 新增代码+Phase148EFinalMaturity：记录 Phase148B 复算矩阵；如果没有这一行，最终结论缺少机器判定细节。
        "phase148c_evidence_path": str(phase148c_path),  # 新增代码+Phase148EFinalMaturity：记录 Phase148C evidence 路径；如果没有这一行，fresh benchmark 来源不透明。
        "phase148c_payload_loaded": phase148c_payload.get("load_ok") is True,  # 修改代码+Phase149ExplorerFileRoundtrip：记录 Phase148C 是否加载成功；如果没有这一行，最新覆盖比例来源无法审计。
        "phase148c_matrix": phase148c_matrix,  # 新增代码+Phase148EFinalMaturity：记录 Phase148C 复算矩阵；如果没有这一行，缺失 families 不会进入最终 manifest。
        "phase148c_required_count": int(phase148c_payload.get("required_family_count", 7) or 7),  # 修改代码+Phase149ExplorerFileRoundtrip：记录 Phase148C 分母；如果没有这一行，4/7 中的 7 不可追溯。
        "phase148c_fresh_visible_terminal_count": len(visible_terminal_entries),  # 新增代码+Phase148EFinalMaturity：记录可见终端 fresh 数量；如果没有这一行，规则十七执行情况不清楚。
        "phase148c_fresh_real_gui_count": len(real_gui_entries),  # 新增代码+Phase148EFinalMaturity：记录真实 GUI fresh 数量；如果没有这一行，成熟度可能被虚高。
        "phase148d_inventory_path": str(phase148d_path),  # 新增代码+Phase148EFinalMaturity：记录 Phase148D inventory 路径；如果没有这一行，缺口登记来源不透明。
        "phase148d_payload_loaded": phase148d_payload.get("load_ok") is True,  # 新增代码+Phase148EFinalMaturity：记录 Phase148D 是否加载成功；如果没有这一行，失败归因可信度不可见。
        "phase148d_failures_fixed": phase148d_payload.get("phase148d_failures_fixed") is True,  # 新增代码+Phase148EFinalMaturity：记录缺口是否已修复；如果没有这一行，等级无法区分已补齐和未补齐。
        "claudecode_alignment_path": str(claudecode_alignment_path),  # 新增代码+ClaudeCodeAlignmentMatrix：记录 ClaudeCode 对齐矩阵路径；如果没有这一行，用户无法追溯 parity 输入来源。
        "claudecode_alignment_loaded": claudecode_alignment_payload.get("load_ok") is True,  # 新增代码+ClaudeCodeAlignmentMatrix：记录矩阵 manifest 是否加载成功；如果没有这一行，缺矩阵和矩阵未通过会混在一起。
        "claudecode_alignment": claudecode_alignment_payload,  # 新增代码+ClaudeCodeAlignmentMatrix：把矩阵原文挂到 evidence；如果没有这一行，评分器拿不到 level、partial_count 和 visible gate。
        "known_gap_count": len([gap for gap in known_gaps if isinstance(gap, dict)]),  # 新增代码+Phase148EFinalMaturity：记录已知缺口数量；如果没有这一行，下一步工程量不可见。
        "known_gaps": [gap for gap in known_gaps if isinstance(gap, dict)],  # 新增代码+Phase148EFinalMaturity：记录已知缺口详情；如果没有这一行，报告无法列出 local_file 等具体 family。
        "safety_boundary_failure_count": safety_gap_count,  # 新增代码+Phase148EFinalMaturity：记录安全边界失败数；如果没有这一行，安全问题无法影响最终等级。
    }  # 新增代码+Phase148EFinalMaturity：结束统一证据字典；如果没有这一行，Python 字典语法不完整。
# 新增代码+Phase148EFinalMaturity：函数段结束，collect_maturity_evidence 到此结束；如果没有这段边界说明，初学者不容易看出证据收集范围。


# 新增代码+Phase148EFinalMaturity：函数段开始，score_computer_use_maturity 根据证据打分；如果没有这个函数，项目没有稳定成熟度判定规则。
def score_computer_use_maturity(evidence: dict[str, Any], *, visible_terminal_final_gate: bool = False, final_visible_run_dir: str = "") -> dict[str, Any]:  # 新增代码+Phase148EFinalMaturity：声明最终评分入口；如果没有这一行，测试和 CLI 无法得到成熟度等级。
    phase148a_governance = evidence.get("phase148a_governance") is True  # 新增代码+Phase148EFinalMaturity：读取治理底座是否存在；如果没有这一行，缺治理也可能被误判成熟。
    phase148b_benchmark_gate = evidence.get("phase148b_matrix", {}).get("passed") is True  # 新增代码+Phase148EFinalMaturity：读取 Phase148B 原始矩阵是否通过；如果没有这一行，benchmark catalog 成熟度不进入评分。
    phase148c_real_gui_count = int(evidence.get("phase148c_fresh_real_gui_count", 0) or 0)  # 新增代码+Phase148EFinalMaturity：读取真实 GUI 通过数量；如果没有这一行，实战成熟度没有核心分子。
    phase148c_required_count = int(evidence.get("phase148c_required_count", 7) or 7)  # 新增代码+Phase148EFinalMaturity：读取必须覆盖数量；如果没有这一行，实战成熟度没有核心分母。
    phase148d_failures_fixed = evidence.get("phase148d_failures_fixed") is True  # 新增代码+Phase148EFinalMaturity：读取 Phase148D 是否修复缺口；如果没有这一行，未修复缺口可能被忽略。
    safety_clean = int(evidence.get("safety_boundary_failure_count", 0) or 0) == 0  # 新增代码+Phase148EFinalMaturity：确认安全边界没有失败；如果没有这一行，安全问题不会阻止成熟结论。
    all_fresh_real_gui = phase148c_real_gui_count >= phase148c_required_count and phase148c_required_count > 0  # 新增代码+Phase148EFinalMaturity：判断 7/7 是否都有真实 GUI；如果没有这一行，实战成熟门槛不清楚。
    practical_ready = phase148a_governance and phase148b_benchmark_gate and safety_clean and all_fresh_real_gui and phase148d_failures_fixed  # 新增代码+Phase148EFinalMaturity：计算实战成熟候选条件；如果没有这一行，等级晋升规则会分散且容易虚高。
    alignment = evidence.get("claudecode_alignment", {}) if isinstance(evidence.get("claudecode_alignment", {}), dict) else {}  # 新增代码+ClaudeCodeAlignmentMatrix：读取 ClaudeCode 对齐矩阵证据；如果没有这一行，评分器无法消费新矩阵。
    alignment_level = str(alignment.get("level", ""))  # 新增代码+ClaudeCodeAlignmentMatrix：读取矩阵等级；如果没有这一行，报告无法说明是 partial 还是 parity。
    alignment_loaded = alignment.get("load_ok") is True  # 新增代码+ClaudeCodeAlignmentMatrix：确认矩阵 manifest 已成功加载；如果没有这一行，缺文件也可能被当成通过。
    alignment_visible_terminal_gate = alignment.get("visible_terminal_gate") is True  # 新增代码+ClaudeCodeAlignmentMatrix：确认矩阵自己的真实可见终端 gate 通过；如果没有这一行，静态矩阵会误升 parity。
    alignment_zero_gaps = int(alignment.get("partial_count", 0) or 0) == 0 and int(alignment.get("missing_count", 0) or 0) == 0  # 新增代码+ClaudeCodeAlignmentMatrix：确认矩阵没有 partial 或 missing；如果没有这一行，带缺口也可能进入最终 parity。
    alignment_parity_ready = bool(alignment_loaded and alignment_visible_terminal_gate and alignment_zero_gaps and alignment.get("claudecode_parity") is True and alignment_level in {"CLAUDECODE_PARITY", MATURITY_CLAUDECODE_PARITY})  # 新增代码+ClaudeCodeAlignmentMatrix：汇总矩阵是否足以支撑 ClaudeCode parity；如果没有这一行，最终等级升级条件会分散且容易误判。
    alignment_better_ready = bool(alignment_parity_ready and (alignment.get("claudecode_parity_or_better") is True or alignment_level == MATURITY_CLAUDECODE_PARITY))  # 新增代码+ClaudeCodeAlignmentMatrix：判断是否有超过 ClaudeCode 的证据；如果没有这一行，parity 和 better 无法区分。
    claudecode_parity = bool(practical_ready and visible_terminal_final_gate and alignment_parity_ready)  # 修改代码+ClaudeCodeAlignmentMatrix：只有实战成熟、最终可见终端 gate 和矩阵 parity 同时满足才给 true；如果没有这一行，报告可能继续保守 false 或过度 true。
    exceeds_claudecode = "true" if claudecode_parity and alignment_better_ready else ("false" if claudecode_parity else "insufficient_evidence")  # 修改代码+ClaudeCodeAlignmentMatrix：对齐但未超过时明确写 false；如果没有这一行，用户分不清无证据和已确认未超过。
    if not phase148a_governance or not phase148b_benchmark_gate or not safety_clean:  # 新增代码+Phase148EFinalMaturity：先处理未成熟或安全失败；如果没有这一行，缺基础 gate 也可能进入成熟等级。
        level = MATURITY_NOT_MATURE  # 新增代码+Phase148EFinalMaturity：基础 gate 不足时给未成熟；如果没有这一行，低等级没有明确返回值。
    elif claudecode_parity and practical_ready:  # 新增代码+Phase148EFinalMaturity：只有已对齐且实战成熟才给最高等级；如果没有这一行，ClaudeCode 对齐条件不受约束。
        level = MATURITY_CLAUDECODE_PARITY  # 新增代码+Phase148EFinalMaturity：给 ClaudeCode 对齐或超过等级；如果没有这一行，最高等级无法返回。
    elif practical_ready:  # 新增代码+Phase148EFinalMaturity：实战条件满足但无 ClaudeCode 证据时给 practical；如果没有这一行，未来 7/7 后只能停在治理成熟。
        level = MATURITY_PRACTICAL  # 新增代码+Phase148EFinalMaturity：给实战成熟等级；如果没有这一行，中间成熟等级无法返回。
    else:  # 修改代码+Phase149ExplorerFileRoundtrip：基础治理通过但实战证据不足时进入治理成熟；如果没有这一行，当前 4/7 状态无法诚实落级。
        level = MATURITY_GOVERNED_ONLY  # 新增代码+Phase148EFinalMaturity：给治理成熟等级；如果没有这一行，当前结果可能被误报成 practical。
    return {  # 新增代码+Phase148EFinalMaturity：开始返回评分字典；如果没有这一行，调用方拿不到机器可读结果。
        "marker": COMPUTER_USE_FINAL_MATURITY_MARKER,  # 新增代码+Phase148EFinalMaturity：写入最终 marker；如果没有这一行，summary line 和 manifest 无法稳定识别。
        "level": level,  # 新增代码+Phase148EFinalMaturity：写入成熟度等级；如果没有这一行，最终判定没有核心结论。
        "phase148a_governance": phase148a_governance,  # 新增代码+Phase148EFinalMaturity：写入治理 gate；如果没有这一行，用户看不到 Level1 是否满足。
        "phase148b_benchmark_gate": phase148b_benchmark_gate,  # 新增代码+Phase148EFinalMaturity：写入 benchmark gate；如果没有这一行，用户看不到 Phase148B 是否支撑结论。
        "phase148c_fresh_real_gui_count": phase148c_real_gui_count,  # 修改代码+Phase149ExplorerFileRoundtrip：写入真实 GUI 分子；如果没有这一行，4/7 结论不可见。
        "phase148c_required_count": phase148c_required_count,  # 修改代码+Phase149ExplorerFileRoundtrip：写入 required 分母；如果没有这一行，4/7 结论不完整。
        "phase148d_failures_fixed": phase148d_failures_fixed,  # 新增代码+Phase148EFinalMaturity：写入缺口修复状态；如果没有这一行，未修复缺口不会被最终输出暴露。
        "safety_boundary_clean": safety_clean,  # 新增代码+Phase148EFinalMaturity：写入安全状态；如果没有这一行，安全边界是否干净不透明。
        "visible_terminal_final_gate": bool(visible_terminal_final_gate),  # 新增代码+Phase148EFinalMaturity：写入最终可见终端 gate；如果没有这一行，最终报告可能自称已通过却无证据。
        "final_visible_run_dir": final_visible_run_dir,  # 新增代码+Phase148EFinalMaturity：写入最终验收 run 目录；如果没有这一行，用户无法追溯最终真实终端证据。
        "claudecode_alignment_loaded": alignment_loaded,  # 新增代码+ClaudeCodeAlignmentMatrix：写入 ClaudeCode 对齐矩阵是否加载成功；如果没有这一行，最终报告无法解释 parity=false 是缺证据还是未通过。
        "claudecode_alignment_level": alignment_level,  # 新增代码+ClaudeCodeAlignmentMatrix：写入 ClaudeCode 对齐矩阵原始等级；如果没有这一行，用户看不到矩阵的真实判定。
        "claudecode_alignment_visible_terminal_gate": alignment_visible_terminal_gate,  # 新增代码+ClaudeCodeAlignmentMatrix：写入矩阵自己的可见终端 gate；如果没有这一行，静态对齐和真实终端对齐无法区分。
        "claudecode_alignment_zero_gaps": alignment_zero_gaps,  # 新增代码+ClaudeCodeAlignmentMatrix：写入矩阵是否无 partial/missing；如果没有这一行，带缺口升级会不透明。
        "claudecode_parity": claudecode_parity,  # 新增代码+Phase148EFinalMaturity：写入 ClaudeCode parity 状态；如果没有这一行，对齐结论会变得含糊。
        "exceeds_claudecode": exceeds_claudecode,  # 新增代码+Phase148EFinalMaturity：写入是否超过 ClaudeCode 的证据状态；如果没有这一行，最高目标缺少诚实说明。
    }  # 新增代码+Phase148EFinalMaturity：结束评分字典；如果没有这一行，Python 字典语法不完整。
# 新增代码+Phase148EFinalMaturity：函数段结束，score_computer_use_maturity 到此结束；如果没有这段边界说明，初学者不容易看出评分规则范围。


# 新增代码+Phase148EFinalMaturity：函数段开始，format_computer_use_maturity_summary_line 生成终端稳定摘要；如果没有这个函数，真实终端验收缺少可匹配输出。
def format_computer_use_maturity_summary_line(score: dict[str, Any]) -> str:  # 新增代码+Phase148EFinalMaturity：声明 summary line 格式化入口；如果没有这一行，CLI 和测试无法共享输出格式。
    return (  # 新增代码+Phase148EFinalMaturity：开始拼接固定顺序 token；如果没有这一行，返回表达式不完整。
        f"{COMPUTER_USE_FINAL_MATURITY_MARKER} "  # 新增代码+Phase148EFinalMaturity：输出最终 marker；如果没有这一段，acceptance controller 找不到成功锚点。
        f"level={score.get('level', MATURITY_NOT_MATURE)} "  # 新增代码+Phase148EFinalMaturity：输出等级；如果没有这一段，用户不能从单行看到结论。
        f"phase148a_governance={_bool_token(score.get('phase148a_governance'))} "  # 新增代码+Phase148EFinalMaturity：输出治理 gate；如果没有这一段，单行结论缺少基础证据。
        f"phase148b_benchmark_gate={_bool_token(score.get('phase148b_benchmark_gate'))} "  # 新增代码+Phase148EFinalMaturity：输出 benchmark gate；如果没有这一段，单行结论缺少矩阵证据。
        f"phase148c_fresh_benchmarks={score.get('phase148c_fresh_real_gui_count', 0)}/{score.get('phase148c_required_count', 0)} "  # 新增代码+Phase148EFinalMaturity：输出真实 GUI 覆盖比例；如果没有这一段，用户看不到为什么不是 practical。
        f"phase148d_failures_fixed={_bool_token(score.get('phase148d_failures_fixed'))} "  # 新增代码+Phase148EFinalMaturity：输出缺口修复状态；如果没有这一段，剩余差距会被隐藏。
        f"visible_terminal_final_gate={_bool_token(score.get('visible_terminal_final_gate'))} "  # 新增代码+Phase148EFinalMaturity：输出最终可见终端 gate；如果没有这一段，规则十七最终门禁不可见。
        f"claudecode_parity={_bool_token(score.get('claudecode_parity'))} "  # 新增代码+Phase148EFinalMaturity：输出 ClaudeCode parity；如果没有这一段，用户可能误以为已对齐。
        f"exceeds_claudecode={score.get('exceeds_claudecode', 'insufficient_evidence')}"  # 新增代码+Phase148EFinalMaturity：输出是否超过 ClaudeCode 的证据状态；如果没有这一段，最高目标状态不清楚。
    )  # 新增代码+Phase148EFinalMaturity：结束 summary line 拼接；如果没有这一行，Python 表达式语法不完整。
# 新增代码+Phase148EFinalMaturity：函数段结束，format_computer_use_maturity_summary_line 到此结束；如果没有这段边界说明，初学者不容易看出终端输出范围。


# 新增代码+Phase148EFinalMaturity：函数段开始，render_computer_use_maturity_report 生成 Markdown 报告；如果没有这个函数，用户只能读机器 JSON。
def render_computer_use_maturity_report(evidence: dict[str, Any], score: dict[str, Any]) -> str:  # 新增代码+Phase148EFinalMaturity：声明报告渲染入口；如果没有这一行，测试和 CLI 无法生成可读报告。
    gaps = evidence.get("known_gaps") if isinstance(evidence.get("known_gaps"), list) else []  # 新增代码+Phase148EFinalMaturity：读取已知缺口列表；如果没有这一行，报告无法列出剩余任务。
    gap_lines = [f"- `{gap.get('family', '')}`: {gap.get('root_cause', '')}" for gap in gaps if isinstance(gap, dict)]  # 新增代码+Phase148EFinalMaturity：把缺口转成 Markdown 行；如果没有这一行，local_file 等缺口不会出现在报告里。
    if not gap_lines:  # 新增代码+Phase148EFinalMaturity：处理无缺口情况；如果没有这一行，报告可能留下空段落。
        gap_lines = ["- 无已知 Phase148D 缺口。"]  # 新增代码+Phase148EFinalMaturity：写入无缺口提示；如果没有这一行，用户看不出是不是漏写。
    return "\n".join(  # 新增代码+Phase148EFinalMaturity：开始拼接 Markdown 报告；如果没有这一行，函数不会返回完整文本。
        [  # 新增代码+Phase148EFinalMaturity：开始报告行列表；如果没有这一行，join 没有可拼接内容。
            "# Computer Use Maturity Determination",  # 新增代码+Phase148EFinalMaturity：写入报告标题；如果没有这一行，用户难以识别报告主题。
            "",  # 新增代码+Phase148EFinalMaturity：写入空行改善阅读；如果没有这一行，标题和正文会挤在一起。
            f"- level={score.get('level', MATURITY_NOT_MATURE)}",  # 新增代码+Phase148EFinalMaturity：写入最终等级；如果没有这一行，报告缺少核心结论。
            f"- phase148a_governance={_bool_token(score.get('phase148a_governance'))}",  # 新增代码+Phase148EFinalMaturity：写入治理 gate；如果没有这一行，用户看不到治理基础是否通过。
            f"- phase148b_benchmark_gate={_bool_token(score.get('phase148b_benchmark_gate'))}",  # 新增代码+Phase148EFinalMaturity：写入 benchmark gate；如果没有这一行，用户看不到矩阵基础是否通过。
            f"- phase148c_fresh_benchmarks={score.get('phase148c_fresh_real_gui_count', 0)}/{score.get('phase148c_required_count', 0)}",  # 新增代码+Phase148EFinalMaturity：写入真实 GUI 覆盖比例；如果没有这一行，用户看不出等级被压低的原因。
            f"- phase148d_failures_fixed={_bool_token(score.get('phase148d_failures_fixed'))}",  # 新增代码+Phase148EFinalMaturity：写入缺口修复状态；如果没有这一行，未修复缺口不透明。
            f"- visible_terminal_final_gate={_bool_token(score.get('visible_terminal_final_gate'))}",  # 新增代码+Phase148EFinalMaturity：写入最终真实终端 gate；如果没有这一行，规则十七最终状态不清楚。
            f"- claudecode_alignment_level={score.get('claudecode_alignment_level', '')}",  # 新增代码+ClaudeCodeAlignmentMatrix：写入 ClaudeCode 对齐矩阵等级；如果没有这一行，用户看不出最终 parity 来源于矩阵。
            f"- claudecode_alignment_visible_terminal_gate={_bool_token(score.get('claudecode_alignment_visible_terminal_gate'))}",  # 新增代码+ClaudeCodeAlignmentMatrix：写入矩阵自己的真实终端 gate；如果没有这一行，静态对齐和真实验收对齐会混淆。
            f"- claudecode_parity={_bool_token(score.get('claudecode_parity'))}",  # 新增代码+Phase148EFinalMaturity：写入 ClaudeCode parity；如果没有这一行，用户可能误解为已对齐。
            f"- exceeds_claudecode={score.get('exceeds_claudecode', 'insufficient_evidence')}",  # 新增代码+Phase148EFinalMaturity：写入超过 ClaudeCode 证据状态；如果没有这一行，最高目标状态缺少说明。
            "",  # 新增代码+Phase148EFinalMaturity：写入空行分隔概览和缺口；如果没有这一行，报告阅读性下降。
            "## Remaining Gaps",  # 新增代码+Phase148EFinalMaturity：写入剩余缺口标题；如果没有这一行，后续任务清单不明显。
            *gap_lines,  # 新增代码+Phase148EFinalMaturity：写入每条缺口；如果没有这一行，报告不会列出具体 family。
            "",  # 新增代码+Phase148EFinalMaturity：写入空行分隔缺口和证据；如果没有这一行，证据路径会和缺口混在一起。
            "## Evidence",  # 新增代码+Phase148EFinalMaturity：写入证据标题；如果没有这一行，用户无法快速定位证据来源。
            f"- phase148a_report={evidence.get('phase148a_report_path', '')}",  # 新增代码+Phase148EFinalMaturity：写入 Phase148A 报告路径；如果没有这一行，治理证据不可追溯。
            f"- phase148b_evidence={evidence.get('phase148b_evidence_path', '')}",  # 新增代码+Phase148EFinalMaturity：写入 Phase148B evidence 路径；如果没有这一行，benchmark gate 不可追溯。
            f"- phase148c_evidence={evidence.get('phase148c_evidence_path', '')}",  # 新增代码+Phase148EFinalMaturity：写入 Phase148C evidence 路径；如果没有这一行，fresh 统计不可追溯。
            f"- phase148d_inventory={evidence.get('phase148d_inventory_path', '')}",  # 新增代码+Phase148EFinalMaturity：写入 Phase148D inventory 路径；如果没有这一行，缺口登记不可追溯。
            f"- claudecode_alignment={evidence.get('claudecode_alignment_path', '')}",  # 新增代码+ClaudeCodeAlignmentMatrix：写入 ClaudeCode 对齐矩阵 manifest 路径；如果没有这一行，parity 证据不可追溯。
            f"- final_visible_run_dir={score.get('final_visible_run_dir', '')}",  # 新增代码+Phase148EFinalMaturity：写入最终验收 run 目录；如果没有这一行，最终可见终端证据不可追溯。
            "",  # 新增代码+Phase148EFinalMaturity：写入末尾空行；如果没有这一行，文本工具显示可能不够整洁。
        ]  # 新增代码+Phase148EFinalMaturity：结束报告行列表；如果没有这一行，Python 列表语法不完整。
    ) + "\n"  # 新增代码+Phase148EFinalMaturity：补充文件末尾换行；如果没有这一行，报告在 git diff 中不够规范。
# 新增代码+Phase148EFinalMaturity：函数段结束，render_computer_use_maturity_report 到此结束；如果没有这段边界说明，初学者不容易看出报告渲染范围。


# 新增代码+Phase148EFinalMaturity：函数段开始，write_final_maturity_outputs 写入最终 manifest 和报告；如果没有这个函数，Phase148E 结果无法落盘复查。
def write_final_maturity_outputs(repo_root: str | Path, *, visible_terminal_final_gate: bool = False, final_visible_run_dir: str = "") -> dict[str, str]:  # 新增代码+Phase148EFinalMaturity：声明最终输出写入入口；如果没有这一行，测试和 CLI 无法统一生成文件。
    root = Path(repo_root)  # 新增代码+Phase148EFinalMaturity：规范仓库根目录；如果没有这一行，输出路径拼接不稳定。
    evidence = collect_maturity_evidence(root)  # 新增代码+Phase148EFinalMaturity：收集当前证据；如果没有这一行，manifest 没有事实输入。
    score = score_computer_use_maturity(evidence, visible_terminal_final_gate=visible_terminal_final_gate, final_visible_run_dir=final_visible_run_dir)  # 新增代码+Phase148EFinalMaturity：计算最终评分；如果没有这一行，输出文件没有等级结论。
    manifest_path = root / FINAL_MANIFEST  # 新增代码+Phase148EFinalMaturity：定位 manifest 输出路径；如果没有这一行，机器可读结果没有落点。
    report_path = root / FINAL_REPORT  # 新增代码+Phase148EFinalMaturity：定位报告输出路径；如果没有这一行，人类可读结果没有落点。
    manifest_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase148EFinalMaturity：确保 manifest 目录存在；如果没有这一行，首次写入会因为目录缺失失败。
    report_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase148EFinalMaturity：确保报告目录存在；如果没有这一行，首次写入会因为目录缺失失败。
    manifest_path.write_text(json.dumps({"evidence": evidence, "score": score}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")  # 新增代码+Phase148EFinalMaturity：写入最终 JSON manifest；如果没有这一行，后续 agent 无法机器读取成熟度证据。
    report_path.write_text(render_computer_use_maturity_report(evidence, score), encoding="utf-8")  # 新增代码+Phase148EFinalMaturity：写入最终 Markdown 报告；如果没有这一行，用户没有可读成熟度结论。
    return {"manifest_path": str(manifest_path), "report_path": str(report_path)}  # 新增代码+Phase148EFinalMaturity：返回输出路径；如果没有这一行，测试和 CLI 无法知道文件写到哪里。
# 新增代码+Phase148EFinalMaturity：函数段结束，write_final_maturity_outputs 到此结束；如果没有这段边界说明，初学者不容易看出落盘范围。


# 新增代码+Phase148EFinalMaturity：函数段开始，main 提供真实终端可运行 CLI；如果没有这个函数，最终可见终端场景无法调用判定器。
def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase148EFinalMaturity：声明 CLI 主入口；如果没有这一行，python -m 无法稳定执行本模块。
    parser = argparse.ArgumentParser(description="Determine final Computer Use maturity level from Phase148 evidence.")  # 新增代码+Phase148EFinalMaturity：创建参数解析器；如果没有这一行，命令行参数错误时提示不清楚。
    parser.add_argument("--evidence-root", default=".")  # 新增代码+Phase148EFinalMaturity：支持传入仓库根目录；如果没有这一行，start_oauth_agent.bat 的工作目录差异会导致找不到证据。
    parser.add_argument("--visible-terminal-final-gate", action="store_true")  # 新增代码+Phase148EFinalMaturity：允许最终验收后回填 final gate；如果没有这一行，最终报告无法记录真实终端已验收。
    parser.add_argument("--final-visible-run-dir", default="")  # 新增代码+Phase148EFinalMaturity：允许记录最终 run 目录；如果没有这一行，最终报告无法追溯验收目录。
    args = parser.parse_args(argv)  # 新增代码+Phase148EFinalMaturity：解析命令行参数；如果没有这一行，CLI 不知道用户传入了什么。
    outputs = write_final_maturity_outputs(args.evidence_root, visible_terminal_final_gate=args.visible_terminal_final_gate, final_visible_run_dir=args.final_visible_run_dir)  # 新增代码+Phase148EFinalMaturity：写入 manifest 和报告；如果没有这一行，终端运行不会留下证据文件。
    manifest = _load_json_file(Path(outputs["manifest_path"]))  # 新增代码+Phase148EFinalMaturity：重新读取 manifest 供终端输出；如果没有这一行，CLI 无法用同一份落盘结果打印摘要。
    score = manifest.get("score", {}) if isinstance(manifest.get("score"), dict) else {}  # 新增代码+Phase148EFinalMaturity：安全读取 score；如果没有这一行，坏 manifest 会导致终端崩溃。
    print(format_computer_use_maturity_summary_line(score))  # 新增代码+Phase148EFinalMaturity：打印稳定 summary line；如果没有这一行，acceptance controller 无法匹配最终判定。
    print(f"manifest_path={outputs['manifest_path']}")  # 新增代码+Phase148EFinalMaturity：打印 manifest 路径；如果没有这一行，用户不容易找到机器证据。
    print(f"report_path={outputs['report_path']}")  # 新增代码+Phase148EFinalMaturity：打印报告路径；如果没有这一行，用户不容易找到可读报告。
    return 0  # 新增代码+Phase148EFinalMaturity：判定器成功生成结论就返回 0；如果没有这一行，治理成熟但非 practical 会被误当命令失败。
# 新增代码+Phase148EFinalMaturity：函数段结束，main 到此结束；如果没有这段边界说明，初学者不容易看出 CLI 范围。


__all__ = [  # 新增代码+Phase148EFinalMaturity：开始声明公开 API；如果没有这一行，通配导入可能暴露内部 helper。
    "COMPUTER_USE_FINAL_MATURITY_MARKER",  # 新增代码+Phase148EFinalMaturity：公开最终 marker；如果没有这一行，测试无法稳定导入 marker。
    "collect_maturity_evidence",  # 新增代码+Phase148EFinalMaturity：公开证据收集函数；如果没有这一行，其他模块无法复用证据链。
    "format_computer_use_maturity_summary_line",  # 新增代码+Phase148EFinalMaturity：公开 summary line 函数；如果没有这一行，验收场景输出格式无法复用。
    "render_computer_use_maturity_report",  # 新增代码+Phase148EFinalMaturity：公开报告渲染函数；如果没有这一行，测试无法验证可读报告。
    "score_computer_use_maturity",  # 新增代码+Phase148EFinalMaturity：公开评分函数；如果没有这一行，自动化无法独立调用成熟度规则。
    "write_final_maturity_outputs",  # 新增代码+Phase148EFinalMaturity：公开输出写入函数；如果没有这一行，测试无法确认 manifest 和报告落盘。
]  # 新增代码+Phase148EFinalMaturity：结束公开 API 列表；如果没有这一行，Python 列表语法不完整。


if __name__ == "__main__":  # 新增代码+Phase148EFinalMaturity：模块入口段开始，允许 python -m 直接运行；如果没有这一行，真实终端无法直接启动判定器。
    raise SystemExit(main())  # 新增代码+Phase148EFinalMaturity：执行 CLI 并返回退出码；如果没有这一行，直接运行模块不会产生最终判定。
# 新增代码+Phase148EFinalMaturity：模块入口段结束，本文件到此结束；如果没有这段说明，初学者不容易看出直接运行范围。
