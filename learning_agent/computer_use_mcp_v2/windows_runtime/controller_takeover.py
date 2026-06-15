"""Phase63 external agent controller takeover and debug surface."""  # 新增代码+Phase63ControllerTakeover: 标明本文件负责外部 agent 接管与调试面；如果没有这行代码，读者难以区分它不是底层桌面动作执行器。
from __future__ import annotations  # 新增代码+Phase63ControllerTakeover: 启用延迟类型解析；如果没有这行代码，复杂类型注解在脚本模式下更容易导入失败。

import json  # 新增代码+Phase63ControllerTakeover: 导入 JSON 读取 result.json 和写出证据包；如果没有这行代码，controller 证据无法结构化交接。
import time  # 新增代码+Phase63ControllerTakeover: 导入时间用于生成不冲突的合同目录；如果没有这行代码，多次自检可能互相覆盖。
from pathlib import Path  # 新增代码+Phase63ControllerTakeover: 导入 Path 管理 Windows 路径；如果没有这行代码，controller.ps1、runs 和证据包路径容易拼错。
from typing import Any  # 新增代码+Phase63ControllerTakeover: 导入 Any 描述 JSON 风格字典；如果没有这行代码，公开 API 的边界不清楚。

PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER = "PHASE63_WINDOWS_CONTROLLER_TAKEOVER_READY"  # 新增代码+Phase63ControllerTakeover: 定义 Phase63 ready marker；如果没有这行代码，真实终端验收没有稳定锚点。
PHASE63_WINDOWS_CONTROLLER_TAKEOVER_OK_TOKEN = "PHASE63_WINDOWS_CONTROLLER_TAKEOVER_OK"  # 新增代码+Phase63ControllerTakeover: 定义 Phase63 OK token；如果没有这行代码，debug log 无法区分自检通过和普通输出。
PHASE63_CONTROLLER_TAKEOVER_MODEL = "phase63_windows_controller_takeover_debug_surface"  # 新增代码+Phase63ControllerTakeover: 定义控制器调试面模型名；如果没有这行代码，status 和最终矩阵无法说明版本。
PHASE63_ACTIONS_EXPANDED = False  # 新增代码+Phase63ControllerTakeover: 明确 Phase63 不扩大真实桌面动作面；如果没有这行代码，用户可能误以为 controller 能新增越权动作。
DEFAULT_CONTROLLER_TAKEOVER_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "controller_takeover"  # 新增代码+Phase63ControllerTakeover: 定义默认证据包目录；如果没有这行代码，生产入口不知道把调试包写到哪里。


def _phase63_bool_token(value: Any) -> str:  # 新增代码+Phase63ControllerTakeover: 函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 可能输出 True/False 导致场景断言漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase63ControllerTakeover: 返回 true/false 文本；如果没有这行代码，真实终端 token 大小写不稳定。
# 新增代码+Phase63ControllerTakeover: 函数段结束，_phase63_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式范围。


def _phase63_safe_text(value: Any, limit: int = 220) -> str:  # 新增代码+Phase63ControllerTakeover: 函数段开始，把任意文本压成安全单行；如果没有这段函数，prompt 和 reason 可能刷乱终端或 JSON。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase63ControllerTakeover: 清理换行和空白；如果没有这行代码，外部 prompt 预览可能破坏日志格式。
    return text[:limit]  # 新增代码+Phase63ControllerTakeover: 限制最大长度；如果没有这行代码，长 prompt 可能让状态面板难以阅读。
# 新增代码+Phase63ControllerTakeover: 函数段结束，_phase63_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清理范围。


def _phase63_read_json(path: Path) -> dict[str, Any]:  # 新增代码+Phase63ControllerTakeover: 函数段开始，安全读取 JSON 文件；如果没有这段函数，坏 result.json 会让 controller 调试面直接崩溃。
    if not path.exists():  # 新增代码+Phase63ControllerTakeover: 检查文件是否存在；如果没有这行代码，缺失 result.json 会抛出底层异常。
        return {}  # 新增代码+Phase63ControllerTakeover: 缺文件时返回空字典；如果没有这行代码，调用方需要到处重复兜底。
    try:  # 新增代码+Phase63ControllerTakeover: 捕获 JSON 解析异常；如果没有这行代码，坏文件会中断外部 agent 排查。
        return json.loads(path.read_text(encoding="utf-8"))  # 新增代码+Phase63ControllerTakeover: 读取并解析 UTF-8 JSON；如果没有这行代码，证据摘要无法取得 completed/assertion 字段。
    except Exception:  # 新增代码+Phase63ControllerTakeover: 兜底任何读取或解析异常；如果没有这行代码，半写入文件会让状态查询不稳定。
        return {}  # 新增代码+Phase63ControllerTakeover: 返回空字典表示不可读；如果没有这行代码，调用方无法继续导出其它证据。
# 新增代码+Phase63ControllerTakeover: 函数段结束，_phase63_read_json 到此结束；如果没有这个边界说明，初学者不容易看出 JSON 读取范围。


def _phase63_write_min_png(path: Path) -> None:  # 新增代码+Phase63ControllerTakeover: 函数段开始，写入最小 PNG 占位文件；如果没有这段函数，合同自检无法证明截图路径存在。
    path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase63ControllerTakeover: 确保截图父目录存在；如果没有这行代码，首次运行写截图占位会失败。
    path.write_bytes(b"\x89PNG\r\n\x1a\n")  # 新增代码+Phase63ControllerTakeover: 写入 PNG 文件头；如果没有这行代码，证据读取只能看到不存在的截图路径。
# 新增代码+Phase63ControllerTakeover: 函数段结束，_phase63_write_min_png 到此结束；如果没有这个边界说明，初学者不容易看出占位截图范围。


def _phase63_repo_root_from_file() -> Path:  # 新增代码+Phase63ControllerTakeover: 函数段开始，从当前文件推断仓库根目录；如果没有这段函数，默认 controller.ps1 路径可能指到 learning_agent 内部。
    return Path(__file__).resolve().parents[3]  # 修改代码+ComputerUseMcpV2ResidualCleanup：从 v2 windows_runtime 文件夹返回 OpenHarness-main 根目录；如果没有这行代码，controller.ps1 和 start_oauth_agent.bat 会被拼到 learning_agent 下面。
# 新增代码+Phase63ControllerTakeover: 函数段结束，_phase63_repo_root_from_file 到此结束；如果没有这个边界说明，初学者不容易看出根目录推断范围。


class WindowsComputerUseControllerTakeoverDebugSurface:  # 新增代码+Phase63ControllerTakeover: 类段开始，封装外部 agent 接管计划、证据读取和调试命令；如果没有这个类，Phase63 能力会散落在测试和终端里。
    def __init__(self, repo_root: str | Path | None = None, acceptance_controller_dir: str | Path | None = None, base_dir: str | Path | None = None, token: str | None = None) -> None:  # 新增代码+Phase63ControllerTakeover: 函数段开始，初始化控制器调试面依赖；如果没有这段函数，测试和终端无法注入隔离目录。
        self.repo_root = Path(repo_root).resolve() if repo_root is not None else _phase63_repo_root_from_file()  # 新增代码+Phase63ControllerTakeover: 保存仓库根目录；如果没有这行代码，controller.ps1 相对路径无法稳定生成。
        self.acceptance_controller_dir = Path(acceptance_controller_dir).resolve() if acceptance_controller_dir is not None else self.repo_root / "learning_agent" / "acceptance_controller"  # 新增代码+Phase63ControllerTakeover: 保存验收控制器目录；如果没有这行代码，runs/scenarios 路径需要到处硬编码。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_CONTROLLER_TAKEOVER_ROOT  # 新增代码+Phase63ControllerTakeover: 保存证据包目录；如果没有这行代码，导出包没有稳定落点。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase63ControllerTakeover: 确保证据包目录存在；如果没有这行代码，首次导出 evidence package 会失败。
        self.token = str(token or "")  # 新增代码+Phase63ControllerTakeover: 保存可选调试 token 状态；如果没有这行代码，status 无法说明 token 是否已配置。
        self.controller_ps1 = self.acceptance_controller_dir / "controller.ps1"  # 新增代码+Phase63ControllerTakeover: 缓存 controller.ps1 路径；如果没有这行代码，启动计划无法明确复用现有可见终端控制器。
        self.start_bat = self.repo_root / "learning_agent" / "start_oauth_agent.bat"  # 新增代码+Phase63ControllerTakeover: 缓存 start_oauth_agent.bat 路径；如果没有这行代码，状态无法证明最终门禁仍是可见终端。
        self.scenarios_dir = self.acceptance_controller_dir / "scenarios"  # 新增代码+Phase63ControllerTakeover: 缓存场景目录；如果没有这行代码，外部 agent 不知道可执行场景放在哪里。
        self.runs_dir = self.acceptance_controller_dir / "runs"  # 新增代码+Phase63ControllerTakeover: 缓存 runs 目录；如果没有这行代码，读取历史验收证据需要猜路径。
    # 新增代码+Phase63ControllerTakeover: 函数段结束，__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase63ControllerTakeover: 函数段开始，返回外部 agent 控制器调试面的机器可读状态；如果没有这段函数，/computer status 无法展示 Phase63。
        return {"enabled": True, "marker": PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER, "model": PHASE63_CONTROLLER_TAKEOVER_MODEL, "controller_ps1": str(self.controller_ps1), "controller_ps1_exists": self.controller_ps1.exists(), "start_oauth_agent_bat": str(self.start_bat), "start_oauth_agent_bat_exists": self.start_bat.exists(), "scenarios_dir": str(self.scenarios_dir), "runs_dir": str(self.runs_dir), "evidence_package_dir": str(self.base_dir), "visible_terminal_required": True, "http_bridge_optional": True, "http_loopback_only": True, "stdio_surface_optional": True, "token_required": True, "token_configured": bool(self.token), "approval_bypass_allowed": False, "controller_can_abort": True, "controller_can_read_runs": True, "evidence_package_supported": True, "actions_expanded": PHASE63_ACTIONS_EXPANDED}  # 新增代码+Phase63ControllerTakeover: 返回完整状态字典；如果没有这行代码，终端 UI 和最终矩阵没有同一事实源。
    # 新增代码+Phase63ControllerTakeover: 函数段结束，status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def build_takeover_plan(self, scenario_path: str | Path, prompt: str = "", run_root: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase63ControllerTakeover: 函数段开始，生成外部 agent 可执行的可见终端接管计划；如果没有这段函数，Codex 只能靠口头记忆启动 controller。
        scenario_text = str(scenario_path).replace("\\", "/")  # 新增代码+Phase63ControllerTakeover: 统一场景路径斜杠；如果没有这行代码，PowerShell 命令在不同调用方里容易漂移。
        relative = scenario_text if scenario_text.startswith("scenarios/") else f"scenarios/{Path(scenario_text).name}"  # 新增代码+Phase63ControllerTakeover: 规范化为 controller.ps1 期望的 scenarios 相对路径；如果没有这行代码，外部 agent 传文件名时可能找不到场景。
        run_arg = f" -RunRoot {Path(run_root)}" if run_root is not None else ""  # 新增代码+Phase63ControllerTakeover: 可选追加 run 根目录；如果没有这行代码，测试和调试无法隔离输出目录。
        command = f"powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\learning_agent\\acceptance_controller\\controller.ps1 -ScenarioPath {relative}{run_arg}"  # 新增代码+Phase63ControllerTakeover: 生成复用现有 controller.ps1 的命令；如果没有这行代码，外部 agent 没有稳定启动入口。
        return {"powershell_command": command, "scenario_path": relative, "prompt_preview": _phase63_safe_text(prompt), "uses_start_oauth_agent_bat": True, "visible_terminal_required": True, "http_replaces_visible_terminal": False, "approval_bypass_allowed": False, "controller_ps1": str(self.controller_ps1), "start_oauth_agent_bat": str(self.start_bat), "marker": PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER}  # 新增代码+Phase63ControllerTakeover: 返回接管计划摘要；如果没有这行代码，控制器计划无法被测试和状态 UI 复用。
    # 新增代码+Phase63ControllerTakeover: 函数段结束，build_takeover_plan 到此结束；如果没有这个边界说明，初学者不容易看出启动计划范围。

    def controller_abort_command(self, reason: str = "controller abort") -> dict[str, Any]:  # 新增代码+Phase63ControllerTakeover: 函数段开始，生成外部 controller 可提示用户输入的急停命令；如果没有这段函数，外部接管缺少安全退出入口。
        safe_reason = _phase63_safe_text(reason, limit=160) or "controller abort"  # 新增代码+Phase63ControllerTakeover: 清理急停原因并兜底；如果没有这行代码，空原因或换行原因会破坏终端命令。
        return {"terminal_command": f"/computer abort {safe_reason}", "controller_can_abort": True, "approval_bypass_allowed": False, "direct_lock_write_allowed": False, "marker": PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER}  # 新增代码+Phase63ControllerTakeover: 返回终端急停命令预览；如果没有这行代码，controller 可能被误做成直接改锁文件。
    # 新增代码+Phase63ControllerTakeover: 函数段结束，controller_abort_command 到此结束；如果没有这个边界说明，初学者不容易看出急停预览范围。

    def read_acceptance_run(self, run_dir: str | Path) -> dict[str, Any]:  # 新增代码+Phase63ControllerTakeover: 函数段开始，读取现有验收 run 的核心证据；如果没有这段函数，外部 agent 排查失败时只能人工翻文件。
        root = Path(run_dir)  # 新增代码+Phase63ControllerTakeover: 转换 run 目录为 Path；如果没有这行代码，字符串路径后续无法稳定拼接。
        result_path = root / "result.json"  # 新增代码+Phase63ControllerTakeover: 定位 result.json；如果没有这行代码，completed/assertion 结果没有读取入口。
        events_path = root / "events.jsonl"  # 新增代码+Phase63ControllerTakeover: 定位 events.jsonl；如果没有这行代码，controller 过程事件无法被发现。
        readable_path = root / "latest_run_readable.md"  # 新增代码+Phase63ControllerTakeover: 定位人类可读摘要；如果没有这行代码，小白用户看证据会更困难。
        result = _phase63_read_json(result_path)  # 新增代码+Phase63ControllerTakeover: 读取结果 JSON；如果没有这行代码，后续字段都只能为空。
        assertion = result.get("assertion", {}) if isinstance(result.get("assertion", {}), dict) else {}  # 新增代码+Phase63ControllerTakeover: 安全读取 assertion 字典；如果没有这行代码，坏 assertion 类型会导致 .get 崩溃。
        screenshots = result.get("screenshots", {}) if isinstance(result.get("screenshots", {}), dict) else {}  # 新增代码+Phase63ControllerTakeover: 安全读取截图字典；如果没有这行代码，截图证据存在性无法判断。
        final_screenshot = Path(str(screenshots.get("final", ""))) if screenshots.get("final") else root / "final.png"  # 新增代码+Phase63ControllerTakeover: 推断最终截图路径；如果没有这行代码，result 缺 screenshot 字段时无法兜底检查。
        return {"run_dir": str(root), "result_json": str(result_path), "result_json_exists": result_path.exists(), "event_log": str(events_path), "event_log_exists": events_path.exists(), "readable_summary": str(readable_path), "readable_summary_exists": readable_path.exists(), "final_screenshot": str(final_screenshot), "final_screenshot_exists": final_screenshot.exists(), "completed": bool(result.get("completed", False)), "assertion_passed": bool(assertion.get("passed", False)), "permission_sent_count": int(result.get("permission_sent_count", 0) or 0), "evidence_package": True, "approval_bypass_allowed": False, "marker": PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER}  # 新增代码+Phase63ControllerTakeover: 返回证据摘要；如果没有这行代码，外部 agent 无法判断 run 成败和证据完整性。
    # 新增代码+Phase63ControllerTakeover: 函数段结束，read_acceptance_run 到此结束；如果没有这个边界说明，初学者不容易看出证据读取范围。

    def export_evidence_package(self, run_dir: str | Path) -> dict[str, Any]:  # 新增代码+Phase63ControllerTakeover: 函数段开始，导出外部 agent 可交接的证据包 JSON；如果没有这段函数，失败现场无法稳定留档。
        evidence = self.read_acceptance_run(run_dir)  # 新增代码+Phase63ControllerTakeover: 先读取 run 证据摘要；如果没有这行代码，证据包内容没有事实来源。
        package_path = self.base_dir / f"phase63_evidence_package_{int(time.time() * 1000)}.json"  # 新增代码+Phase63ControllerTakeover: 生成不冲突的证据包路径；如果没有这行代码，多次导出会互相覆盖。
        package = {"marker": PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER, "model": PHASE63_CONTROLLER_TAKEOVER_MODEL, "evidence_package": True, "visible_terminal_required": True, "approval_bypass_allowed": False, "evidence": evidence}  # 新增代码+Phase63ControllerTakeover: 组装证据包内容；如果没有这行代码，导出文件缺少安全边界和证据摘要。
        package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")  # 新增代码+Phase63ControllerTakeover: 写出 UTF-8 JSON 证据包；如果没有这行代码，外部 agent 无法从磁盘读取交接材料。
        return {"package_path": str(package_path), "evidence_package": True, "run_dir": str(run_dir), "marker": PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER, "approval_bypass_allowed": False}  # 新增代码+Phase63ControllerTakeover: 返回导出结果；如果没有这行代码，调用方不知道证据包写到了哪里。
    # 新增代码+Phase63ControllerTakeover: 函数段结束，export_evidence_package 到此结束；如果没有这个边界说明，初学者不容易看出证据包导出范围。

    def terminal_status_lines(self) -> list[str]:  # 新增代码+Phase63ControllerTakeover: 函数段开始，生成终端可读 controller 调试面板；如果没有这段函数，用户只能看机器字典。
        status = self.status()  # 新增代码+Phase63ControllerTakeover: 读取机器状态作为事实源；如果没有这行代码，终端文本容易和 status 字段不一致。
        abort_preview = self.controller_abort_command("controller requested stop")  # 新增代码+Phase63ControllerTakeover: 生成急停命令示例；如果没有这行代码，用户不知道外部 agent 接管时如何停手。
        return ["Computer Controller Takeover", f"- marker={status.get('marker', '')}", f"- model={status.get('model', '')}", f"- visible_terminal_required={_phase63_bool_token(status.get('visible_terminal_required'))}", f"- controller_ps1_exists={_phase63_bool_token(status.get('controller_ps1_exists'))} path={status.get('controller_ps1', '')}", f"- start_oauth_agent_bat_exists={_phase63_bool_token(status.get('start_oauth_agent_bat_exists'))} path={status.get('start_oauth_agent_bat', '')}", f"- http_bridge_optional={_phase63_bool_token(status.get('http_bridge_optional'))} loopback_only={_phase63_bool_token(status.get('http_loopback_only'))} token_required={_phase63_bool_token(status.get('token_required'))}", f"- controller_can_read_runs={_phase63_bool_token(status.get('controller_can_read_runs'))} runs_dir={status.get('runs_dir', '')}", f"- evidence_package_supported={_phase63_bool_token(status.get('evidence_package_supported'))} package_dir={status.get('evidence_package_dir', '')}", f"- controller_can_abort={_phase63_bool_token(status.get('controller_can_abort'))} abort_command={abort_preview.get('terminal_command', '')}", f"- approval_bypass_allowed={_phase63_bool_token(status.get('approval_bypass_allowed'))}", f"- actions_expanded={_phase63_bool_token(status.get('actions_expanded'))}"]  # 新增代码+Phase63ControllerTakeover: 返回完整终端面板；如果没有这行代码，/computer controller 无法展示 Phase63。
    # 新增代码+Phase63ControllerTakeover: 函数段结束，terminal_status_lines 到此结束；如果没有这个边界说明，初学者不容易看出终端面板范围。
# 新增代码+Phase63ControllerTakeover: 类段结束，WindowsComputerUseControllerTakeoverDebugSurface 到此结束；如果没有这个边界说明，初学者不容易看出调试面对象范围。


def _phase63_make_fake_run(root: Path) -> Path:  # 新增代码+Phase63ControllerTakeover: 函数段开始，为合同自检创建最小 acceptance run；如果没有这段函数，CLI 合同会依赖真实历史运行。
    run_dir = root / "agent_capability_phase63_controller_takeover_fake_run"  # 新增代码+Phase63ControllerTakeover: 定义 fake run 目录；如果没有这行代码，合同文件没有统一父目录。
    run_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase63ControllerTakeover: 创建 fake run 目录；如果没有这行代码，后续写文件会失败。
    final_png = run_dir / "final.png"  # 新增代码+Phase63ControllerTakeover: 定义最终截图占位路径；如果没有这行代码，截图证据无法落盘。
    _phase63_write_min_png(final_png)  # 新增代码+Phase63ControllerTakeover: 写入最小截图占位；如果没有这行代码，final_screenshot_exists 不能为真。
    (run_dir / "events.jsonl").write_text('{"event":"agent_ready_for_user_prompt"}\n{"event":"final_answer_printed"}\n', encoding="utf-8")  # 新增代码+Phase63ControllerTakeover: 写入最小事件流；如果没有这行代码，event_log_exists 没有真实文件。
    (run_dir / "latest_run_readable.md").write_text("# Phase63 fake run\ncompleted=true\n", encoding="utf-8")  # 新增代码+Phase63ControllerTakeover: 写入可读摘要；如果没有这行代码，readable_summary_exists 不能为真。
    (run_dir / "result.json").write_text(json.dumps({"completed": True, "assertion": {"passed": True}, "permission_sent_count": 0, "screenshots": {"final": str(final_png)}}, ensure_ascii=False, sort_keys=True), encoding="utf-8")  # 新增代码+Phase63ControllerTakeover: 写入最小 result.json；如果没有这行代码，证据读取无法证明 completed/assertion/permission。
    return run_dir  # 新增代码+Phase63ControllerTakeover: 返回 fake run 目录；如果没有这行代码，合同自检无法继续读取证据。
# 新增代码+Phase63ControllerTakeover: 函数段结束，_phase63_make_fake_run 到此结束；如果没有这个边界说明，初学者不容易看出 fake run 范围。


def run_phase63_controller_takeover_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase63ControllerTakeover: 函数段开始，运行 Phase63 控制器接管合同自检；如果没有这段函数，真实终端无法一条命令验证本阶段。
    root = Path(base_dir) if base_dir is not None else DEFAULT_CONTROLLER_TAKEOVER_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase63ControllerTakeover: 选择隔离合同目录；如果没有这行代码，多次自检可能互相污染。
    surface = WindowsComputerUseControllerTakeoverDebugSurface(base_dir=root / "packages")  # 新增代码+Phase63ControllerTakeover: 创建调试面板对象；如果没有这行代码，合同没有被测主体。
    status = surface.status()  # 新增代码+Phase63ControllerTakeover: 读取状态；如果没有这行代码，合同无法判断 loopback/token/visible terminal 边界。
    plan = surface.build_takeover_plan("scenarios/agent_capability_phase62_high_level_tools.json", prompt="请查看 /computer status")  # 新增代码+Phase63ControllerTakeover: 生成可见终端接管计划；如果没有这行代码，launches_visible_terminal 没有证据。
    run_dir = _phase63_make_fake_run(root)  # 新增代码+Phase63ControllerTakeover: 创建 fake acceptance run；如果没有这行代码，reads_acceptance_run 没有样本。
    evidence = surface.read_acceptance_run(run_dir)  # 新增代码+Phase63ControllerTakeover: 读取 fake run 证据；如果没有这行代码，合同无法证明证据读取能力。
    package = surface.export_evidence_package(run_dir)  # 新增代码+Phase63ControllerTakeover: 导出证据包；如果没有这行代码，evidence_package token 没有落盘证据。
    abort = surface.controller_abort_command("phase63 contract stop")  # 新增代码+Phase63ControllerTakeover: 生成急停命令预览；如果没有这行代码，can_abort token 没有证据。
    controller_surface = bool(status.get("enabled") and status.get("controller_ps1_exists") and status.get("start_oauth_agent_bat_exists"))  # 新增代码+Phase63ControllerTakeover: 汇总控制器表面是否存在；如果没有这行代码，CLI 无法表达基础文件是否齐全。
    launches_visible_terminal = bool(plan.get("uses_start_oauth_agent_bat") and plan.get("visible_terminal_required") and not plan.get("http_replaces_visible_terminal"))  # 新增代码+Phase63ControllerTakeover: 汇总可见终端启动要求；如果没有这行代码，HTTP 可能被误认为最终门禁。
    reads_acceptance_run = bool(evidence.get("result_json_exists") and evidence.get("event_log_exists") and evidence.get("completed") and evidence.get("assertion_passed"))  # 新增代码+Phase63ControllerTakeover: 汇总 run 读取能力；如果没有这行代码，证据读取 token 没有严格条件。
    evidence_package = bool(package.get("evidence_package") and Path(str(package.get("package_path", ""))).exists())  # 新增代码+Phase63ControllerTakeover: 汇总证据包落盘能力；如果没有这行代码，导出函数可能只返回假字段。
    can_abort = bool(abort.get("controller_can_abort") and str(abort.get("terminal_command", "")).startswith("/computer abort"))  # 新增代码+Phase63ControllerTakeover: 汇总急停命令能力；如果没有这行代码，can_abort 可能绕过终端链路。
    http_loopback_only = bool(status.get("http_loopback_only"))  # 新增代码+Phase63ControllerTakeover: 汇总 HTTP 本机限制；如果没有这行代码，CLI token 缺少网络边界。
    token_required = bool(status.get("token_required"))  # 新增代码+Phase63ControllerTakeover: 汇总 token 要求；如果没有这行代码，CLI token 缺少认证边界。
    approval_bypass_blocked = not bool(status.get("approval_bypass_allowed") or plan.get("approval_bypass_allowed") or abort.get("approval_bypass_allowed"))  # 新增代码+Phase63ControllerTakeover: 汇总审批绕过被阻断；如果没有这行代码，controller 可能越过 Phase60 安全链。
    visible_terminal_required = bool(status.get("visible_terminal_required") and plan.get("visible_terminal_required"))  # 新增代码+Phase63ControllerTakeover: 汇总可见终端强制门禁；如果没有这行代码，验收规则可能被弱化。
    passed = bool(controller_surface and launches_visible_terminal and reads_acceptance_run and evidence_package and can_abort and http_loopback_only and token_required and approval_bypass_blocked and visible_terminal_required and not PHASE63_ACTIONS_EXPANDED)  # 新增代码+Phase63ControllerTakeover: 汇总合同通过条件；如果没有这行代码，失败也可能返回成功码。
    return {"marker": PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER, "ok_token": PHASE63_WINDOWS_CONTROLLER_TAKEOVER_OK_TOKEN, "controller_surface": controller_surface, "launches_visible_terminal": launches_visible_terminal, "reads_acceptance_run": reads_acceptance_run, "evidence_package": evidence_package, "can_abort": can_abort, "http_loopback_only": http_loopback_only, "token_required": token_required, "approval_bypass_blocked": approval_bypass_blocked, "visible_terminal_required": visible_terminal_required, "actions_expanded": PHASE63_ACTIONS_EXPANDED, "passed": passed, "state_dir": str(root), "package_path": str(package.get("package_path", ""))}  # 新增代码+Phase63ControllerTakeover: 返回完整合同报告；如果没有这行代码，测试和真实终端拿不到统一结果。
# 新增代码+Phase63ControllerTakeover: 函数段结束，run_phase63_controller_takeover_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase63_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase63ControllerTakeover: 函数段开始，把 Phase63 报告转成稳定 CLI token 行；如果没有这段函数，验收场景需要解析复杂 JSON。
    return f"{PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER} {PHASE63_WINDOWS_CONTROLLER_TAKEOVER_OK_TOKEN} controller_surface={_phase63_bool_token(report.get('controller_surface'))} launches_visible_terminal={_phase63_bool_token(report.get('launches_visible_terminal'))} reads_acceptance_run={_phase63_bool_token(report.get('reads_acceptance_run'))} evidence_package={_phase63_bool_token(report.get('evidence_package'))} can_abort={_phase63_bool_token(report.get('can_abort'))} http_loopback_only={_phase63_bool_token(report.get('http_loopback_only'))} token_required={_phase63_bool_token(report.get('token_required'))} approval_bypass_blocked={_phase63_bool_token(report.get('approval_bypass_blocked'))} visible_terminal_required={_phase63_bool_token(report.get('visible_terminal_required'))} actions_expanded={_phase63_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase63ControllerTakeover: 返回固定顺序 token；如果没有这行代码，debug log 和场景断言容易漂移。
# 新增代码+Phase63ControllerTakeover: 函数段结束，phase63_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase63ControllerTakeover: 函数段开始，提供命令行自检入口；如果没有这段函数，真实终端无法直接运行 Phase63 合同。
    _ = argv  # 新增代码+Phase63ControllerTakeover: 保留 argv 供未来扩展；如果没有这行代码，参数存在但用途不清晰。
    report = run_phase63_controller_takeover_contract()  # 新增代码+Phase63ControllerTakeover: 运行默认隔离合同；如果没有这行代码，CLI 不会生成证据。
    print(phase63_cli_line(report))  # 新增代码+Phase63ControllerTakeover: 打印稳定 token 行；如果没有这行代码，debug log 无法匹配 Phase63 通过条件。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase63ControllerTakeover: 打印结构化报告；如果没有这行代码，失败时不容易复盘缺哪个条件。
    print(PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER)  # 新增代码+Phase63ControllerTakeover: 单独打印 ready marker；如果没有这行代码，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase63ControllerTakeover: 根据合同结果返回退出码；如果没有这行代码，失败也可能被 shell 当成成功。
# 新增代码+Phase63ControllerTakeover: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["DEFAULT_CONTROLLER_TAKEOVER_ROOT", "PHASE63_ACTIONS_EXPANDED", "PHASE63_CONTROLLER_TAKEOVER_MODEL", "PHASE63_WINDOWS_CONTROLLER_TAKEOVER_MARKER", "PHASE63_WINDOWS_CONTROLLER_TAKEOVER_OK_TOKEN", "WindowsComputerUseControllerTakeoverDebugSurface", "main", "phase63_cli_line", "run_phase63_controller_takeover_contract"]  # 新增代码+Phase63ControllerTakeover: 限定公开导出名称；如果没有这行代码，包导入容易暴露内部 helper 或漏掉合同入口。


if __name__ == "__main__":  # 新增代码+Phase63ControllerTakeover: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase63ControllerTakeover: 用 main 返回码退出；如果没有这行代码，命令行状态不明确。
