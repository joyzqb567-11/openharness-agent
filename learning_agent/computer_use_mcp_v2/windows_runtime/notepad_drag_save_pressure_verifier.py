"""Notepad 拖动保存压力测试证据验证器。"""  # 新增代码+NotepadDragSavePressure：说明本模块只验证证据不控制桌面；如果没有这行，读者可能误以为这里会操作真实窗口。
from __future__ import annotations  # 新增代码+NotepadDragSavePressure：延迟解析类型注解；如果没有这行，部分运行路径可能因类型提前解析失败。

import argparse  # 新增代码+NotepadDragSavePressure：解析命令行参数；如果没有这行，真实验收后无法用 CLI 指定仓库路径。
import json  # 新增代码+NotepadDragSavePressure：写入结构化验证报告；如果没有这行，后续复盘只能看终端文本。
import os  # 新增代码+NotepadDragSavePressure：读取 USERPROFILE 来定位桌面；如果没有这行，默认桌面路径在 Windows 上不稳定。
import re  # 新增代码+NotepadDragSavePressure：用正则识别直接写文件命令；如果没有这行，反作弊只能做脆弱字符串判断。
import sys  # 新增代码+NotepadDragSavePressure：返回进程退出码；如果没有这行，自动化无法知道验证失败。
from pathlib import Path  # 新增代码+NotepadDragSavePressure：统一处理仓库、桌面和运行目录路径；如果没有这行，字符串拼接容易出错。
from typing import Any  # 新增代码+NotepadDragSavePressure：标注报告字典里的动态 JSON 值；如果没有这行，读者不清楚报告类型。


SCENARIO_NAME = "agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal"  # 新增代码+NotepadDragSavePressure：固定本压力测试场景名；如果没有这行，查找最新 run 会扫错目录。
TARGET_FILE_NAME = "1.txt"  # 新增代码+NotepadDragSavePressure：固定桌面保存文件名；如果没有这行，验证器和方案会出现两个目标名。
TARGET_TEXT = "hello everyone"  # 新增代码+NotepadDragSavePressure：固定要验证的文件内容；如果没有这行，文件内容检查没有标准。
SUCCESS_MARKER = "NOTEPAD_DRAG_SAVE_PRESSURE_OK"  # 新增代码+NotepadDragSavePressure：固定 agent 最终成功标记；如果没有这行，验证器无法确认本轮任务完成。
VERIFY_OK_TOKEN = "NOTEPAD_DRAG_SAVE_PRESSURE_VERIFY_OK"  # 新增代码+NotepadDragSavePressure：固定验证器成功标记；如果没有这行，外部脚本难以稳定匹配结果。
SCREENSHOT_NAMES = ("01_startup.png", "02_prompt_sent.png", "03_final.png")  # 新增代码+NotepadDragSavePressure：列出三张必需截图；如果没有这行，真实可见终端证据可能缺失。
DIRECT_FILE_WRITE_PATTERNS = (  # 新增代码+NotepadDragSavePressure：正则列表段开始，定义禁止的直接写文件痕迹；如果没有这段，agent 可绕过真实 Notepad。
    r"\bSet-Content\b[^\n\r]*\b1\.txt\b",  # 新增代码+NotepadDragSavePressure：拦截 PowerShell Set-Content 写 1.txt；如果没有这行，最常见直接写文件会漏掉。
    r"\bOut-File\b[^\n\r]*\b1\.txt\b",  # 新增代码+NotepadDragSavePressure：拦截 PowerShell Out-File 写 1.txt；如果没有这行，另一种直接写文件会漏掉。
    r"\[System\.IO\.File\]::WriteAllText[^\n\r]*\b1\.txt\b",  # 新增代码+NotepadDragSavePressure：拦截 .NET 写文件 API；如果没有这行，PowerShell 可绕过 cmdlet 名称。
    r"\bpython\b[^\n\r]*-c[^\n\r]*(write_text|open\()[^\n\r]*\b1\.txt\b",  # 新增代码+NotepadDragSavePressure：拦截 python -c 写 1.txt；如果没有这行，命令行 Python 可绕过真实记事本。
    r"\bcmd\b[^\n\r]*/c[^\n\r]*\becho\b[^\n\r]*>[^\n\r]*\b1\.txt\b",  # 新增代码+NotepadDragSavePressure：拦截 cmd echo 重定向写 1.txt；如果没有这行，cmd 重定向会漏掉。
)  # 新增代码+NotepadDragSavePressure：正则列表段结束；如果没有这个边界说明，初学者不容易看出反作弊范围。


def _default_desktop_path() -> Path:  # 新增代码+NotepadDragSavePressure：函数段开始，定位当前 Windows 桌面；如果没有这段函数，CLI 默认无法找到用户桌面。
    user_profile = os.environ.get("USERPROFILE")  # 新增代码+NotepadDragSavePressure：优先读取 Windows 用户目录；如果没有这行，Path.home 在某些嵌入环境可能不准。
    base_path = Path(user_profile) if user_profile else Path.home()  # 新增代码+NotepadDragSavePressure：没有 USERPROFILE 时用 home 兜底；如果没有这行，非标准环境会报错。
    return base_path / "Desktop"  # 新增代码+NotepadDragSavePressure：返回桌面目录；如果没有这行，验证器不知道去哪里找 1.txt。
# 新增代码+NotepadDragSavePressure：函数段结束，_default_desktop_path 到此结束；如果没有这个边界说明，初学者不容易看出桌面定位范围。


def _latest_run_dir(repo_root: Path) -> Path | None:  # 新增代码+NotepadDragSavePressure：函数段开始，查找最新 acceptance run；如果没有这段函数，CLI 必须手填 run 目录。
    runs_root = repo_root / "learning_agent" / "acceptance_controller" / "runs"  # 新增代码+NotepadDragSavePressure：定位 controller runs 根目录；如果没有这行，验证器会在错误目录扫描。
    if not runs_root.exists():  # 新增代码+NotepadDragSavePressure：检查 runs 目录是否存在；如果没有这行，首次运行前会抛异常。
        return None  # 新增代码+NotepadDragSavePressure：没有 runs 时返回空；如果没有这行，调用方无法报告 run_dir_missing。
    candidates = [path for path in runs_root.iterdir() if path.is_dir() and path.name.startswith(SCENARIO_NAME + "-")]  # 新增代码+NotepadDragSavePressure：筛选本场景运行目录；如果没有这行，可能误用别的验收结果。
    if not candidates:  # 新增代码+NotepadDragSavePressure：检查是否找到候选；如果没有这行，空列表取最大值会失败。
        return None  # 新增代码+NotepadDragSavePressure：没有候选时返回空；如果没有这行，调用方无法给出清晰失败原因。
    return max(candidates, key=lambda path: path.stat().st_mtime)  # 新增代码+NotepadDragSavePressure：返回最近修改的 run；如果没有这行，多轮测试会读到旧证据。
# 新增代码+NotepadDragSavePressure：函数段结束，_latest_run_dir 到此结束；如果没有这个边界说明，初学者不容易看出 run 选择逻辑。


def _read_text(path: Path) -> str:  # 新增代码+NotepadDragSavePressure：函数段开始，安全读取文本；如果没有这段函数，缺失日志会抛异常中断报告。
    if not path.exists():  # 新增代码+NotepadDragSavePressure：检查文件是否存在；如果没有这行，read_text 会抛出不友好的异常。
        return ""  # 新增代码+NotepadDragSavePressure：缺失文件返回空文本；如果没有这行，调用方不能统一处理缺日志。
    return path.read_text(encoding="utf-8", errors="replace")  # 新增代码+NotepadDragSavePressure：读取 UTF-8 并替换坏字符；如果没有这行，日志里的异常字符会打断验证。
# 新增代码+NotepadDragSavePressure：函数段结束，_read_text 到此结束；如果没有这个边界说明，初学者不容易看出容错读取范围。


def _screenshot_status(run_dir: Path | None) -> dict[str, Any]:  # 新增代码+NotepadDragSavePressure：函数段开始，检查三张截图；如果没有这段函数，真实可见终端证据没有机器门禁。
    if run_dir is None:  # 新增代码+NotepadDragSavePressure：没有 run 目录时截图必然失败；如果没有这行，后续 Path 拼接会报错。
        return {"ok": False, "missing": list(SCREENSHOT_NAMES)}  # 新增代码+NotepadDragSavePressure：返回全部截图缺失；如果没有这行，失败报告不清楚。
    missing = [name for name in SCREENSHOT_NAMES if not (run_dir / name).exists() or (run_dir / name).stat().st_size <= 0]  # 新增代码+NotepadDragSavePressure：检查截图存在且非空；如果没有这行，空文件也会被误判为证据。
    return {"ok": not missing, "missing": missing}  # 新增代码+NotepadDragSavePressure：返回截图检查结果；如果没有这行，调用方拿不到结构化状态。
# 新增代码+NotepadDragSavePressure：函数段结束，_screenshot_status 到此结束；如果没有这个边界说明，初学者不容易看出截图门禁范围。


def _direct_file_write_matches(log_text: str) -> list[str]:  # 新增代码+NotepadDragSavePressure：函数段开始，查找直接写文件命令；如果没有这段函数，反作弊逻辑无法复用。
    matches: list[str] = []  # 新增代码+NotepadDragSavePressure：初始化命中列表；如果没有这行，无法收集多个风险模式。
    for pattern in DIRECT_FILE_WRITE_PATTERNS:  # 新增代码+NotepadDragSavePressure：逐条检查禁止模式；如果没有这行，正则列表不会被使用。
        if re.search(pattern, log_text, flags=re.IGNORECASE):  # 新增代码+NotepadDragSavePressure：大小写不敏感匹配日志；如果没有这行，Set-Content 大小写变化可能绕过。
            matches.append(pattern)  # 新增代码+NotepadDragSavePressure：记录命中的模式；如果没有这行，失败报告不知道命中了什么。
    return matches  # 新增代码+NotepadDragSavePressure：返回命中列表；如果没有这行，调用方无法判定反作弊是否通过。
# 新增代码+NotepadDragSavePressure：函数段结束，_direct_file_write_matches 到此结束；如果没有这个边界说明，初学者不容易看出反作弊范围。


def _movement_evidence(log_text: str, run_dir: Path | None) -> dict[str, Any]:  # 新增代码+NotepadDragSavePressure：函数段开始，识别窗口移动证据；如果没有这段函数，拖动一圈只有人工口头判断。
    report_path = (run_dir / "notepad_drag_save_pressure_report.json") if run_dir is not None else None  # 新增代码+NotepadDragSavePressure：定位可选详细报告；如果没有这行，未来加入坐标采样后验证器找不到。
    if report_path is not None and report_path.exists():  # 新增代码+NotepadDragSavePressure：优先使用结构化移动报告；如果没有这行，验证器无法利用真实坐标采样。
        try:  # 新增代码+NotepadDragSavePressure：保护 JSON 解析；如果没有这行，坏报告会中断整个验证。
            payload = json.loads(report_path.read_text(encoding="utf-8"))  # 新增代码+NotepadDragSavePressure：读取结构化移动报告；如果没有这行，无法统计窗口坐标。
        except (OSError, json.JSONDecodeError):  # 新增代码+NotepadDragSavePressure：捕获文件或 JSON 错误；如果没有这行，坏报告会抛异常。
            payload = {}  # 新增代码+NotepadDragSavePressure：坏报告按空报告处理；如果没有这行，后续字段访问不安全。
        samples = payload.get("window_positions") or payload.get("window_rect_samples") or []  # 新增代码+NotepadDragSavePressure：兼容两种可能采样字段；如果没有这行，报告格式轻微变化会失效。
        distinct = {json.dumps(sample, sort_keys=True, ensure_ascii=False) for sample in samples if isinstance(sample, dict)}  # 新增代码+NotepadDragSavePressure：统计不同坐标样本；如果没有这行，无法判断是否移动至少四次。
        if len(distinct) >= 4:  # 新增代码+NotepadDragSavePressure：要求至少四个不同位置；如果没有这行，一个静止窗口也会误过。
            return {"ok": True, "source": "window_position_report", "sample_count": len(distinct)}  # 新增代码+NotepadDragSavePressure：返回强证据通过；如果没有这行，调用方无法知道证据来源。
    token_ok = "mouse_drag_loop=true" in log_text  # 新增代码+NotepadDragSavePressure：没有结构化采样时退回最终回答 token；如果没有这行，当前 controller 证据无法表达用户要求。
    return {"ok": token_ok, "source": "final_answer_token" if token_ok else "missing", "sample_count": 0}  # 新增代码+NotepadDragSavePressure：返回移动证据状态；如果没有这行，调用方无法生成报告。
# 新增代码+NotepadDragSavePressure：函数段结束，_movement_evidence 到此结束；如果没有这个边界说明，初学者不容易看出移动证据范围。


def verify_notepad_drag_save_pressure(repo_root: Path | str, *, desktop_path: Path | str | None = None, run_dir: Path | str | None = None) -> dict[str, Any]:  # 新增代码+NotepadDragSavePressure：函数段开始，执行完整证据验证；如果没有这段函数，CLI 和测试无法复用逻辑。
    repo = Path(repo_root)  # 新增代码+NotepadDragSavePressure：规范化仓库路径；如果没有这行，字符串路径无法统一拼接。
    desktop = Path(desktop_path) if desktop_path is not None else _default_desktop_path()  # 新增代码+NotepadDragSavePressure：使用传入桌面或默认桌面；如果没有这行，测试不能隔离真实桌面。
    selected_run_dir = Path(run_dir) if run_dir is not None else _latest_run_dir(repo)  # 新增代码+NotepadDragSavePressure：使用传入 run 或自动找最新 run；如果没有这行，CLI 使用不方便。
    target_file = desktop / TARGET_FILE_NAME  # 新增代码+NotepadDragSavePressure：定位桌面目标文件；如果没有这行，后续文件检查没有对象。
    file_exists = target_file.exists()  # 新增代码+NotepadDragSavePressure：检查 1.txt 是否存在；如果没有这行，报告不能区分缺文件和内容错误。
    file_text = _read_text(target_file) if file_exists else ""  # 新增代码+NotepadDragSavePressure：存在时读取内容；如果没有这行，内容校验无法进行。
    content_verified = TARGET_TEXT in file_text  # 新增代码+NotepadDragSavePressure：确认核心文本存在；如果没有这行，空文件也可能误过。
    log_path = (selected_run_dir / "latest_run_readable.md") if selected_run_dir is not None else None  # 新增代码+NotepadDragSavePressure：定位 debug 可读日志；如果没有这行，marker 和反作弊没有来源。
    log_text = _read_text(log_path) if log_path is not None else ""  # 新增代码+NotepadDragSavePressure：读取日志文本；如果没有这行，后续检查不能执行。
    screenshot_status = _screenshot_status(selected_run_dir)  # 新增代码+NotepadDragSavePressure：检查三张截图；如果没有这行，真实终端证据缺失不会被发现。
    direct_matches = _direct_file_write_matches(log_text)  # 新增代码+NotepadDragSavePressure：检查直接写文件痕迹；如果没有这行，反作弊门禁不会生效。
    movement_status = _movement_evidence(log_text, selected_run_dir)  # 新增代码+NotepadDragSavePressure：检查拖动一圈证据；如果没有这行，鼠标拖动要求无法验证。
    marker_present = SUCCESS_MARKER in log_text  # 新增代码+NotepadDragSavePressure：确认本压力测试成功标记出现；如果没有这行，可能误读其他 run。
    full_mode_present = "full_mode=true" in log_text  # 新增代码+NotepadDragSavePressure：确认 /computer use --full 已进入 full mode；如果没有这行，测试可能没走 Computer Use 模式。
    failures: list[str] = []  # 新增代码+NotepadDragSavePressure：初始化失败原因列表；如果没有这行，只能返回一个粗糙布尔值。
    if selected_run_dir is None:  # 新增代码+NotepadDragSavePressure：检查 run 目录是否缺失；如果没有这行，后续报告路径会不清楚。
        failures.append("run_dir_missing")  # 新增代码+NotepadDragSavePressure：记录 run 目录缺失；如果没有这行，用户不知道缺哪份证据。
    if not file_exists:  # 新增代码+NotepadDragSavePressure：检查桌面文件是否缺失；如果没有这行，缺文件不会导致失败。
        failures.append("desktop_file_missing")  # 新增代码+NotepadDragSavePressure：记录桌面文件缺失；如果没有这行，失败原因不明确。
    if file_exists and not content_verified:  # 新增代码+NotepadDragSavePressure：检查内容是否不符合；如果没有这行，错误内容文件会误过。
        failures.append("content_missing")  # 新增代码+NotepadDragSavePressure：记录内容缺失；如果没有这行，用户不知道是内容问题。
    if not screenshot_status["ok"]:  # 新增代码+NotepadDragSavePressure：检查截图门禁；如果没有这行，缺截图会误过。
        failures.append("screenshots_missing")  # 新增代码+NotepadDragSavePressure：记录截图缺失；如果没有这行，用户不知道真实终端证据不足。
    if not marker_present:  # 新增代码+NotepadDragSavePressure：检查成功 marker；如果没有这行，agent 没最终确认也会误过。
        failures.append("success_marker_missing")  # 新增代码+NotepadDragSavePressure：记录 marker 缺失；如果没有这行，失败原因不清楚。
    if not full_mode_present:  # 新增代码+NotepadDragSavePressure：检查 full mode token；如果没有这行，未开启 computer use 也可能误过。
        failures.append("full_mode_missing")  # 新增代码+NotepadDragSavePressure：记录 full mode 缺失；如果没有这行，无法追踪 /computer use --full 是否生效。
    if direct_matches:  # 新增代码+NotepadDragSavePressure：检查是否命中直接写文件；如果没有这行，反作弊命中不会变失败。
        failures.append("direct_file_write_detected")  # 新增代码+NotepadDragSavePressure：记录直接写文件风险；如果没有这行，用户看不出绕过 Notepad。
    if not movement_status["ok"]:  # 新增代码+NotepadDragSavePressure：检查拖动证据；如果没有这行，不拖窗口也会误过。
        failures.append("mouse_drag_loop_missing")  # 新增代码+NotepadDragSavePressure：记录拖动证据缺失；如果没有这行，压力测试核心动作不可追踪。
    result: dict[str, Any] = {  # 新增代码+NotepadDragSavePressure：报告对象段开始；如果没有这段，调用方拿不到结构化结果。
        "passed": not failures,  # 新增代码+NotepadDragSavePressure：只有无失败原因才通过；如果没有这行，报告没有核心结论。
        "failures": failures,  # 新增代码+NotepadDragSavePressure：保存失败原因列表；如果没有这行，排查只能猜。
        "repo_root": str(repo),  # 新增代码+NotepadDragSavePressure：记录仓库路径；如果没有这行，多仓库复盘会混淆。
        "desktop_file": str(target_file),  # 新增代码+NotepadDragSavePressure：记录桌面文件路径；如果没有这行，用户不知道验证了哪个文件。
        "run_dir": str(selected_run_dir) if selected_run_dir is not None else "",  # 新增代码+NotepadDragSavePressure：记录运行证据目录；如果没有这行，截图和日志不好找。
        "file_exists": file_exists,  # 新增代码+NotepadDragSavePressure：记录文件存在状态；如果没有这行，报告不透明。
        "content_verified": content_verified,  # 新增代码+NotepadDragSavePressure：记录内容校验状态；如果没有这行，报告无法证明 hello everyone。
        "screenshots_verified": bool(screenshot_status["ok"]),  # 新增代码+NotepadDragSavePressure：记录截图校验状态；如果没有这行，真实终端证据缺失不明显。
        "missing_screenshots": screenshot_status["missing"],  # 新增代码+NotepadDragSavePressure：记录缺失截图名；如果没有这行，修复者不知道缺哪张。
        "direct_file_write_not_detected": not bool(direct_matches),  # 新增代码+NotepadDragSavePressure：记录反作弊结果；如果没有这行，机器报告无法表达是否绕过。
        "direct_file_write_patterns": direct_matches,  # 新增代码+NotepadDragSavePressure：记录命中的风险模式；如果没有这行，失败证据不够具体。
        "movement_verified": bool(movement_status["ok"]),  # 新增代码+NotepadDragSavePressure：记录拖动证据状态；如果没有这行，核心压力动作没有报告字段。
        "movement_source": movement_status["source"],  # 新增代码+NotepadDragSavePressure：记录拖动证据来源；如果没有这行，无法区分强坐标证据和最终 token。
        "movement_sample_count": movement_status["sample_count"],  # 新增代码+NotepadDragSavePressure：记录坐标样本数；如果没有这行，未来强证据无法量化。
        "success_marker_present": marker_present,  # 新增代码+NotepadDragSavePressure：记录成功 marker 是否出现；如果没有这行，无法区分任务未答和文件问题。
        "full_mode_present": full_mode_present,  # 新增代码+NotepadDragSavePressure：记录 full mode 是否出现；如果没有这行，无法证明 /computer use --full 生效。
    }  # 新增代码+NotepadDragSavePressure：报告对象段结束；如果没有这个边界说明，初学者不容易看出报告字段范围。
    if selected_run_dir is not None and selected_run_dir.exists():  # 新增代码+NotepadDragSavePressure：有运行目录时写入报告；如果没有这行，缺 run 时会写到未知位置。
        report_path = selected_run_dir / "notepad_drag_save_pressure_report.json"  # 新增代码+NotepadDragSavePressure：定义验证报告路径；如果没有这行，后续证据文件不固定。
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")  # 新增代码+NotepadDragSavePressure：写入结构化报告；如果没有这行，验收后没有机器可读证据。
        result["report_path"] = str(report_path)  # 新增代码+NotepadDragSavePressure：把报告路径补进返回值；如果没有这行，CLI 输出无法告诉用户报告在哪。
    return result  # 新增代码+NotepadDragSavePressure：返回最终验证结果；如果没有这行，测试和 CLI 都拿不到结论。
# 新增代码+NotepadDragSavePressure：函数段结束，verify_notepad_drag_save_pressure 到此结束；如果没有这个边界说明，初学者不容易看出主验证范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+NotepadDragSavePressure：函数段开始，命令行入口；如果没有这段函数，真实验收后不能一条命令验证。
    parser = argparse.ArgumentParser(description="Verify Notepad drag-save pressure acceptance evidence.")  # 新增代码+NotepadDragSavePressure：创建参数解析器；如果没有这行，CLI 参数没有说明。
    parser.add_argument("--repo-root", default=".", help="OpenHarness repo root.")  # 新增代码+NotepadDragSavePressure：允许指定仓库根目录；如果没有这行，从其他目录运行会找错 runs。
    parser.add_argument("--desktop-path", default="", help="Optional desktop path override.")  # 新增代码+NotepadDragSavePressure：允许测试或特殊桌面覆盖路径；如果没有这行，非标准桌面无法验证。
    parser.add_argument("--run-dir", default="", help="Optional acceptance run directory override.")  # 新增代码+NotepadDragSavePressure：允许指定本轮 run；如果没有这行，多轮测试只能自动猜最新。
    args = parser.parse_args(argv)  # 新增代码+NotepadDragSavePressure：解析命令行参数；如果没有这行，下面拿不到用户输入。
    desktop_path = Path(args.desktop_path) if args.desktop_path else None  # 新增代码+NotepadDragSavePressure：把桌面参数转为可选 Path；如果没有这行，空字符串会被当成当前目录。
    run_dir = Path(args.run_dir) if args.run_dir else None  # 新增代码+NotepadDragSavePressure：把 run 参数转为可选 Path；如果没有这行，空字符串会被当成当前目录。
    result = verify_notepad_drag_save_pressure(Path(args.repo_root), desktop_path=desktop_path, run_dir=run_dir)  # 新增代码+NotepadDragSavePressure：执行主验证；如果没有这行，CLI 不会做任何检查。
    if result["passed"]:  # 新增代码+NotepadDragSavePressure：判断是否通过；如果没有这行，成功和失败输出无法分流。
        print(f"{VERIFY_OK_TOKEN} file_exists=true content_verified=true screenshots_verified=true direct_file_write_not_detected=true")  # 新增代码+NotepadDragSavePressure：输出稳定成功 token；如果没有这行，方案里的命令无法匹配通过。
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))  # 新增代码+NotepadDragSavePressure：输出完整 JSON 摘要；如果没有这行，终端没有结构化细节。
        return 0  # 新增代码+NotepadDragSavePressure：成功返回 0；如果没有这行，自动化会误判失败。
    print("NOTEPAD_DRAG_SAVE_PRESSURE_VERIFY_FAIL " + " ".join(str(item) for item in result["failures"]))  # 新增代码+NotepadDragSavePressure：输出稳定失败 token 和原因；如果没有这行，失败不可机器识别。
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))  # 新增代码+NotepadDragSavePressure：输出完整失败 JSON；如果没有这行，用户需要打开文件才知道详情。
    return 2  # 新增代码+NotepadDragSavePressure：失败返回非零；如果没有这行，自动化会把失败当成功。
# 新增代码+NotepadDragSavePressure：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 范围。


if __name__ == "__main__":  # 新增代码+NotepadDragSavePressure：脚本直接运行入口；如果没有这行，python 文件不会执行 main。
    raise SystemExit(main())  # 新增代码+NotepadDragSavePressure：把 main 返回值作为进程退出码；如果没有这行，失败也可能返回 0。
