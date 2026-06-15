"""Post-parity Computer Use 结构化证据账本。"""  # 新增代码+PostParityEvidenceLedger：说明本文件负责保存 accepted/rejected 的 Computer Use 证据记录；如果没有这一行，读者不知道该模块的职责。
from __future__ import annotations  # 新增代码+PostParityEvidenceLedger：启用稳定的注解解析；如果没有这一行，后续类型注解在部分环境下可能更容易出兼容问题。

import json  # 新增代码+PostParityEvidenceLedger：导入 JSON 工具读写 JSONL；如果没有这一行，ledger 无法保存结构化证据。
from pathlib import Path  # 新增代码+PostParityEvidenceLedger：导入路径对象处理 ledger 文件；如果没有这一行，路径创建和读取会更脆弱。
from typing import Any  # 新增代码+PostParityEvidenceLedger：导入动态字段类型；如果没有这一行，entry/report 字典类型无法清楚表达。


ALLOWED_EVIDENCE_PREFIXES = (  # 新增代码+PostParityEvidenceLedger：定义允许进入账本的 evidence 路径前缀；如果没有这一段，用户私有路径可能被保存到 ledger。
    "learning_agent/memory/computer_use/",  # 新增代码+PostParityEvidenceLedger：允许项目内 Computer Use memory 证据；如果没有这一行，真实工作流报告无法被 ledger 引用。
    "learning_agent/acceptance_controller/runs/",  # 新增代码+PostParityEvidenceLedger：允许 acceptance controller run 证据；如果没有这一行，真实可见终端证据无法被 ledger 引用。
)  # 新增代码+PostParityEvidenceLedger：结束允许前缀元组；如果没有这一行，Python 元组语法不完整。


# 新增代码+PostParityEvidenceLedger：函数段开始，_normalize_evidence_path 把路径统一成正斜杠相对表达；如果没有这段函数，Windows 反斜杠路径会导致白名单判断不稳定。
def _normalize_evidence_path(path: str | Path) -> str:  # 新增代码+PostParityEvidenceLedger：声明路径标准化函数；如果没有这一行，调用方无法复用路径清洗逻辑。
    return str(path).replace("\\", "/").strip()  # 新增代码+PostParityEvidenceLedger：把反斜杠转成正斜杠并去空白；如果没有这一行，同一项目路径可能因为斜杠不同被误拒绝。
# 新增代码+PostParityEvidenceLedger：函数段结束，_normalize_evidence_path 到此结束；如果没有这个边界说明，初学者不容易看出路径标准化范围。


# 新增代码+PostParityEvidenceLedger：函数段开始，_is_allowed_evidence_path 判断 evidence 路径是否在受控范围；如果没有这段函数，ledger 可能保存用户隐私路径。
def _is_allowed_evidence_path(path: str | Path) -> bool:  # 新增代码+PostParityEvidenceLedger：声明 evidence 路径白名单函数；如果没有这一行，调用方无法统一判断路径是否安全。
    normalized = _normalize_evidence_path(path)  # 新增代码+PostParityEvidenceLedger：先标准化路径；如果没有这一行，Windows 路径和 Unix 风格路径会判断不一致。
    return any(normalized.startswith(prefix) for prefix in ALLOWED_EVIDENCE_PREFIXES)  # 新增代码+PostParityEvidenceLedger：只有受控项目前缀才允许；如果没有这一行，C:/Users 私有路径可能进入账本。
# 新增代码+PostParityEvidenceLedger：函数段结束，_is_allowed_evidence_path 到此结束；如果没有这个边界说明，初学者不容易看出路径白名单范围。


# 新增代码+PostParityEvidenceLedger：函数段开始，build_post_parity_ledger_entry 构造单条 ledger 记录；如果没有这段函数，各处会手写 entry 且容易漏掉脱敏规则。
def build_post_parity_ledger_entry(  # 新增代码+PostParityEvidenceLedger：声明 ledger entry 构造函数；如果没有这一行，外部无法创建标准账本记录。
    *,  # 新增代码+PostParityEvidenceLedger：强制使用关键字参数；如果没有这一行，调用者容易把 run_id 和 scenario_id 顺序写错。
    scenario_id: str,  # 新增代码+PostParityEvidenceLedger：接收场景 ID；如果没有这一行，记录无法追溯到具体工作流。
    run_id: str,  # 新增代码+PostParityEvidenceLedger：接收运行 ID；如果没有这一行，多次运行无法区分。
    accepted: bool,  # 新增代码+PostParityEvidenceLedger：接收是否通过；如果没有这一行，账本无法区分 accepted/rejected。
    evidence_paths: list[str],  # 新增代码+PostParityEvidenceLedger：接收证据路径列表；如果没有这一行，记录无法指向可审计 artifacts。
    verifier_decision: str,  # 新增代码+PostParityEvidenceLedger：接收 verifier 决策；如果没有这一行，用户看不出为什么通过或失败。
    cleanup_completed: bool,  # 新增代码+PostParityEvidenceLedger：接收 cleanup 状态；如果没有这一行，环境清理无法进入证据账本。
    failure_category: str = "",  # 新增代码+PostParityEvidenceLedger：接收失败分类，成功记录可为空；如果没有这一行，triage 结果无法写入失败记录。
) -> dict[str, Any]:  # 新增代码+PostParityEvidenceLedger：声明返回标准 entry 字典；如果没有这一行，调用方不知道返回结构。
    redaction_reasons: list[str] = []  # 新增代码+PostParityEvidenceLedger：初始化脱敏/拒绝原因列表；如果没有这一行，私有路径被拒绝时没有可解释原因。
    safe_paths: list[str] = []  # 新增代码+PostParityEvidenceLedger：初始化安全路径列表；如果没有这一行，受控路径没有地方保存。
    for raw_path in evidence_paths:  # 新增代码+PostParityEvidenceLedger：逐条检查证据路径；如果没有这一行，只能处理一个路径或漏掉多 artifact 记录。
        normalized = _normalize_evidence_path(raw_path)  # 新增代码+PostParityEvidenceLedger：标准化当前路径；如果没有这一行，白名单判断会受斜杠影响。
        if _is_allowed_evidence_path(normalized):  # 新增代码+PostParityEvidenceLedger：判断路径是否在受控 evidence 范围；如果没有这一行，私有路径会直接保存。
            safe_paths.append(normalized)  # 新增代码+PostParityEvidenceLedger：保存受控路径；如果没有这一行，合法 evidence 也会丢失。
        else:  # 新增代码+PostParityEvidenceLedger：处理不受控路径；如果没有这一行，违规路径没有拒绝分支。
            redaction_reasons.append("uncontrolled_evidence_path")  # 新增代码+PostParityEvidenceLedger：记录不受控路径原因；如果没有这一行，用户不知道为什么 entry 不 sanitized。
    sanitized = not redaction_reasons  # 新增代码+PostParityEvidenceLedger：只有没有脱敏原因才算安全；如果没有这一行，后续矩阵无法判断 ledger 是否干净。
    return {  # 新增代码+PostParityEvidenceLedger：开始返回 entry 字典；如果没有这一行，函数没有标准输出。
        "scenario_id": scenario_id,  # 新增代码+PostParityEvidenceLedger：写入场景 ID；如果没有这一行，记录来源不可追溯。
        "run_id": run_id,  # 新增代码+PostParityEvidenceLedger：写入运行 ID；如果没有这一行，多 run 难以区分。
        "accepted": bool(accepted),  # 新增代码+PostParityEvidenceLedger：写入布尔 accepted；如果没有这一行，统计 accepted/rejected 会不稳定。
        "evidence_paths": safe_paths,  # 新增代码+PostParityEvidenceLedger：写入受控证据路径；如果没有这一行，账本无法追溯 artifacts。
        "verifier_decision": verifier_decision,  # 新增代码+PostParityEvidenceLedger：写入 verifier 决策；如果没有这一行，记录缺少验收结论。
        "cleanup_completed": bool(cleanup_completed),  # 新增代码+PostParityEvidenceLedger：写入 cleanup 布尔状态；如果没有这一行，环境清理能力不可审计。
        "failure_category": failure_category,  # 新增代码+PostParityEvidenceLedger：写入失败分类；如果没有这一行，失败复盘信息会丢失。
        "sanitized": sanitized,  # 新增代码+PostParityEvidenceLedger：写入是否安全脱敏；如果没有这一行，矩阵无法阻止隐私路径进入通过状态。
        "redaction_reasons": redaction_reasons,  # 新增代码+PostParityEvidenceLedger：写入脱敏原因；如果没有这一行，用户无法理解路径被拒绝原因。
    }  # 新增代码+PostParityEvidenceLedger：结束 entry 字典；如果没有这一行，Python 语法不完整。
# 新增代码+PostParityEvidenceLedger：函数段结束，build_post_parity_ledger_entry 到此结束；如果没有这个边界说明，初学者不容易看出 entry 构造范围。


# 新增代码+PostParityEvidenceLedger：函数段开始，write_post_parity_ledger_entry 把单条 entry 追加写入 JSONL；如果没有这段函数，ledger 不能持久保存多次运行记录。
def write_post_parity_ledger_entry(path: str | Path, entry: dict[str, Any]) -> None:  # 新增代码+PostParityEvidenceLedger：声明 ledger 写入函数；如果没有这一行，外部无法保存账本记录。
    ledger_path = Path(path)  # 新增代码+PostParityEvidenceLedger：把输入路径转成 Path；如果没有这一行，后续 parent/open 操作不稳定。
    ledger_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+PostParityEvidenceLedger：确保父目录存在；如果没有这一行，写入新目录下的 ledger 会失败。
    with ledger_path.open("a", encoding="utf-8") as handle:  # 新增代码+PostParityEvidenceLedger：以追加模式打开 JSONL 文件；如果没有这一行，记录无法持久化。
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")  # 新增代码+PostParityEvidenceLedger：写入一行 JSON 并保留中文；如果没有这一行，账本不会产生实际记录。
# 新增代码+PostParityEvidenceLedger：函数段结束，write_post_parity_ledger_entry 到此结束；如果没有这个边界说明，初学者不容易看出 JSONL 写入范围。


# 新增代码+PostParityEvidenceLedger：函数段开始，read_post_parity_ledger_entries 读取 JSONL ledger；如果没有这段函数，评估函数无法复用读取逻辑。
def read_post_parity_ledger_entries(path: str | Path) -> list[dict[str, Any]]:  # 新增代码+PostParityEvidenceLedger：声明 ledger 读取函数；如果没有这一行，外部无法读取账本记录。
    ledger_path = Path(path)  # 新增代码+PostParityEvidenceLedger：把输入路径转成 Path；如果没有这一行，exists/open 操作不稳定。
    if not ledger_path.exists():  # 新增代码+PostParityEvidenceLedger：检查 ledger 是否存在；如果没有这一行，不存在的文件会抛异常而不是返回空账本。
        return []  # 新增代码+PostParityEvidenceLedger：不存在时返回空列表；如果没有这一行，调用方需要额外捕获文件异常。
    entries: list[dict[str, Any]] = []  # 新增代码+PostParityEvidenceLedger：初始化 entry 列表；如果没有这一行，读取结果没有收集容器。
    with ledger_path.open("r", encoding="utf-8") as handle:  # 新增代码+PostParityEvidenceLedger：以 UTF-8 打开 JSONL 文件；如果没有这一行，无法读取已有账本。
        for line in handle:  # 新增代码+PostParityEvidenceLedger：逐行读取 JSONL；如果没有这一行，只能读取整文件且不好跳过空行。
            raw_line = line.strip()  # 新增代码+PostParityEvidenceLedger：清理行首尾空白；如果没有这一行，空行判断和 JSON 解析会不稳定。
            if raw_line:  # 新增代码+PostParityEvidenceLedger：跳过空行；如果没有这一行，空行会触发 JSON 解析失败。
                entries.append(json.loads(raw_line))  # 新增代码+PostParityEvidenceLedger：解析 JSON 行并加入列表；如果没有这一行，读取函数不会返回实际记录。
    return entries  # 新增代码+PostParityEvidenceLedger：返回所有记录；如果没有这一行，调用方拿不到账本内容。
# 新增代码+PostParityEvidenceLedger：函数段结束，read_post_parity_ledger_entries 到此结束；如果没有这个边界说明，初学者不容易看出 JSONL 读取范围。


# 新增代码+PostParityEvidenceLedger：函数段开始，evaluate_post_parity_ledger 评估 ledger 是否满足 post-parity 门禁；如果没有这段函数，矩阵无法判断账本能力是否成熟。
def evaluate_post_parity_ledger(path: str | Path) -> dict[str, Any]:  # 新增代码+PostParityEvidenceLedger：声明 ledger 评估函数；如果没有这一行，外部无法得到账本门禁报告。
    entries = read_post_parity_ledger_entries(path)  # 新增代码+PostParityEvidenceLedger：读取账本所有记录；如果没有这一行，评估没有输入数据。
    accepted_count = sum(1 for item in entries if item.get("accepted") is True)  # 新增代码+PostParityEvidenceLedger：统计 accepted 记录；如果没有这一行，账本无法证明成功样本存在。
    rejected_count = sum(1 for item in entries if item.get("accepted") is False)  # 新增代码+PostParityEvidenceLedger：统计 rejected 记录；如果没有这一行，账本无法证明失败样本存在。
    sanitized = all(item.get("sanitized") is True for item in entries) if entries else False  # 新增代码+PostParityEvidenceLedger：要求所有记录都已脱敏；如果没有这一行，隐私路径可能仍让 ledger gate 通过。
    passed = accepted_count > 0 and rejected_count > 0 and sanitized  # 新增代码+PostParityEvidenceLedger：只有成功/失败记录都有且全部安全才通过；如果没有这一行，账本门禁缺少总判断。
    return {  # 新增代码+PostParityEvidenceLedger：开始返回评估报告；如果没有这一行，调用方拿不到结构化结论。
        "passed": passed,  # 新增代码+PostParityEvidenceLedger：写入总通过状态；如果没有这一行，post-parity 矩阵无法消费 ledger 结果。
        "accepted_count": accepted_count,  # 新增代码+PostParityEvidenceLedger：写入成功记录数量；如果没有这一行，用户无法看到账本覆盖情况。
        "rejected_count": rejected_count,  # 新增代码+PostParityEvidenceLedger：写入失败记录数量；如果没有这一行，用户无法看到账本是否支持失败复盘。
        "entry_count": len(entries),  # 新增代码+PostParityEvidenceLedger：写入总记录数；如果没有这一行，账本规模不可见。
        "sanitized": sanitized,  # 新增代码+PostParityEvidenceLedger：写入脱敏状态；如果没有这一行，隐私安全状态不可见。
    }  # 新增代码+PostParityEvidenceLedger：结束评估报告；如果没有这一行，Python 字典语法不完整。
# 新增代码+PostParityEvidenceLedger：函数段结束，evaluate_post_parity_ledger 到此结束；如果没有这个边界说明，初学者不容易看出账本门禁范围。
