"""Desktop GUI acceptance controller dashboard payload helpers."""  # 新增代码+DesktopGUIAcceptance：说明本模块只把现有验收控制器接到 GUI；如果没有这行，维护者容易误以为这里重写了验收系统。

from __future__ import annotations  # 新增代码+DesktopGUIAcceptance：启用延迟类型解析；如果没有这行，类型注解在导入顺序变化时更容易出错。

import json  # 新增代码+DesktopGUIAcceptance：读取场景 JSON 和 result.json；如果没有这行，GUI 无法知道验收场景和运行结果。
import re  # 新增代码+DesktopGUIAcceptance：清理场景 id 和文件名；如果没有这行，按钮请求可能带入危险字符。
import subprocess  # 新增代码+DesktopGUIAcceptance：启动现有 controller.ps1 的真实可见终端；如果没有这行，GUI 只能看不能跑验收。
import sys  # 新增代码+DesktopGUIAcceptance：判断当前平台是否支持 Windows 可见终端；如果没有这行，非 Windows 下可能误报可启动。
from datetime import UTC, datetime  # 新增代码+DesktopGUIAcceptance：生成统一 UTC 时间戳；如果没有这行，用户无法判断清单是否新鲜。
from pathlib import Path  # 新增代码+DesktopGUIAcceptance：安全拼接 workspace、scenarios 和 runs 路径；如果没有这行，Windows 路径处理会脆弱。
from typing import Any, Mapping  # 新增代码+DesktopGUIAcceptance：标注 JSON 风格 payload；如果没有这行，函数边界会退化成不清楚的动态对象。

from learning_agent.app.gui_protocol import GUI_V2_SCHEMA_VERSION  # 新增代码+DesktopGUIAcceptance：复用 GUI V2 协议版本；如果没有这行，验收端点会和其它 GUI payload 版本漂移。
from learning_agent.computer_use_mcp_v2.windows_runtime.controller_takeover import WindowsComputerUseControllerTakeoverDebugSurface  # 新增代码+DesktopGUIAcceptance：复用已有可见终端接管/证据读取薄封装；如果没有这行，GUI 会复制 controller_takeover 逻辑。


ACCEPTANCE_RELATIVE_ROOT = Path("learning_agent") / "acceptance_controller"  # 新增代码+DesktopGUIAcceptance：集中定义验收控制器目录；如果没有这行，多个 helper 会重复硬编码路径。
ACCEPTANCE_SCENARIO_LIMIT = 160  # 新增代码+DesktopGUIAcceptance：限制一次暴露的场景数量；如果没有这行，异常大目录可能拖慢右侧栏。
ACCEPTANCE_RUN_LIMIT = 80  # 新增代码+DesktopGUIAcceptance：限制最近运行记录数量；如果没有这行，长期证据目录可能让 payload 过大。
ACCEPTANCE_ID_PATTERN = re.compile(r"[^a-zA-Z0-9_.-]+")  # 新增代码+DesktopGUIAcceptance：定义场景 id 安全字符规则；如果没有这行，用户输入可能污染路径查找。


def _utc_now() -> str:  # 新增代码+DesktopGUIAcceptance：函数段开始，生成统一 UTC 时间；如果没有这段，每个 payload 会各自写时间逻辑。
    return datetime.now(UTC).isoformat()  # 新增代码+DesktopGUIAcceptance：返回 ISO 时间字符串；如果没有这行，前端无法显示稳定刷新时间。
# 新增代码+DesktopGUIAcceptance：函数段结束，_utc_now 到此结束；如果没有边界说明，用户不易看出时间生成范围。


def _safe_text(value: Any, fallback: str = "", limit: int = 260) -> str:  # 新增代码+DesktopGUIAcceptance：函数段开始，把未知值收敛成单行短文本；如果没有这段，坏 JSON 可能撑破 GUI。
    text = str(value if value is not None else fallback).replace("\r", " ").replace("\n", " ").strip()  # 新增代码+DesktopGUIAcceptance：把 None 和多行文本整理成单行；如果没有这行，卡片布局会被换行污染。
    if not text:  # 新增代码+DesktopGUIAcceptance：检查清理后是否为空；如果没有这行，空字符串不会使用兜底。
        text = fallback  # 新增代码+DesktopGUIAcceptance：使用兜底文本；如果没有这行，用户可能看到空标题或空状态。
    return text[:limit]  # 新增代码+DesktopGUIAcceptance：限制最大长度；如果没有这行，长 prompt 或路径会撑破右侧栏。
# 新增代码+DesktopGUIAcceptance：函数段结束，_safe_text 到此结束；如果没有边界说明，用户不易看出文本清洗范围。


def _safe_id(value: Any, fallback: str = "scenario") -> str:  # 新增代码+DesktopGUIAcceptance：函数段开始，生成适合 URL/body 的场景 id；如果没有这段，前端按钮目标可能不可控。
    candidate = _safe_text(value, fallback, 160).replace("\\", "/").split("/")[-1]  # 新增代码+DesktopGUIAcceptance：只保留最后一级名称；如果没有这行，用户提交相对路径可能绕过场景目录。
    candidate = candidate[:-5] if candidate.lower().endswith(".json") else candidate  # 新增代码+DesktopGUIAcceptance：去掉 JSON 后缀；如果没有这行，id 和文件名会混用。
    cleaned = ACCEPTANCE_ID_PATTERN.sub("_", candidate).strip("._-")  # 新增代码+DesktopGUIAcceptance：替换危险字符；如果没有这行，id 可能影响路径拼接。
    return cleaned or fallback  # 新增代码+DesktopGUIAcceptance：返回清理后 id 或兜底；如果没有这行，空 id 会进入查找逻辑。
# 新增代码+DesktopGUIAcceptance：函数段结束，_safe_id 到此结束；如果没有边界说明，用户不易看出 id 白名单范围。


def _read_json_file(path: Path) -> dict[str, Any]:  # 新增代码+DesktopGUIAcceptance：函数段开始，安全读取 JSON 文件；如果没有这段，坏场景或半写入 result 会导致 500。
    if not path.exists():  # 新增代码+DesktopGUIAcceptance：检查文件是否存在；如果没有这行，缺 result.json 会抛底层异常。
        return {}  # 新增代码+DesktopGUIAcceptance：缺文件返回空对象；如果没有这行，调用方要重复写存在性判断。
    try:  # 新增代码+DesktopGUIAcceptance：捕获读取和解析异常；如果没有这行，单个坏文件会拖垮整个面板。
        loaded = json.loads(path.read_text(encoding="utf-8"))  # 新增代码+DesktopGUIAcceptance：按 UTF-8 读取并解析 JSON；如果没有这行，验收事实源不可用。
    except Exception:  # 新增代码+DesktopGUIAcceptance：处理坏 JSON 或编码异常；如果没有这行，半写入文件会变成 HTTP 500。
        return {}  # 新增代码+DesktopGUIAcceptance：坏文件返回空对象；如果没有这行，调用方无法继续展示其它场景。
    return loaded if isinstance(loaded, dict) else {}  # 新增代码+DesktopGUIAcceptance：只接受 JSON 对象；如果没有这行，数组场景会让字段读取崩溃。
# 新增代码+DesktopGUIAcceptance：函数段结束，_read_json_file 到此结束；如果没有边界说明，用户不易看出 JSON 容错范围。


def _workspace_path(workspace: str | Path) -> Path:  # 新增代码+DesktopGUIAcceptance：函数段开始，规范化 workspace；如果没有这段，所有路径 helper 都要重复 resolve。
    return Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUIAcceptance：返回绝对工作区路径；如果没有这行，controller.ps1 和 runs 目录可能定位错误。
# 新增代码+DesktopGUIAcceptance：函数段结束，_workspace_path 到此结束；如果没有边界说明，用户不易看出路径规范化范围。


def _acceptance_root(workspace_path: Path) -> Path:  # 新增代码+DesktopGUIAcceptance：函数段开始，定位验收控制器根目录；如果没有这段，调用方会散落路径拼接。
    return workspace_path / ACCEPTANCE_RELATIVE_ROOT  # 新增代码+DesktopGUIAcceptance：返回 learning_agent/acceptance_controller；如果没有这行，场景和 runs 无法定位。
# 新增代码+DesktopGUIAcceptance：函数段结束，_acceptance_root 到此结束；如果没有边界说明，用户不易看出目录来源。


def _controller_surface(workspace_path: Path) -> WindowsComputerUseControllerTakeoverDebugSurface:  # 新增代码+DesktopGUIAcceptance：函数段开始，创建验收控制器复用对象；如果没有这段，默认 base_dir 可能污染模块目录。
    base_dir = workspace_path / "memory" / "gui_acceptance" / "controller_takeover"  # 新增代码+DesktopGUIAcceptance：把证据包目录放回当前 workspace；如果没有这行，测试和真实项目的临时包会混到默认目录。
    return WindowsComputerUseControllerTakeoverDebugSurface(repo_root=workspace_path, base_dir=base_dir)  # 新增代码+DesktopGUIAcceptance：返回带隔离目录的复用对象；如果没有这行，GUI 无法复用 controller_takeover 状态和计划。
# 新增代码+DesktopGUIAcceptance：函数段结束，_controller_surface 到此结束；如果没有边界说明，用户不易看出复用对象的隔离策略。


def _relative_display(workspace_path: Path, target: Path) -> str:  # 新增代码+DesktopGUIAcceptance：函数段开始，把路径转成 GUI 友好的相对路径；如果没有这段，payload 可能泄漏绝对本机目录。
    try:  # 新增代码+DesktopGUIAcceptance：保护 relative_to；如果没有这行，外部路径会导致异常。
        return target.resolve().relative_to(workspace_path).as_posix()  # 新增代码+DesktopGUIAcceptance：工作区内路径显示相对值；如果没有这行，用户看到的都是长绝对路径。
    except Exception:  # 新增代码+DesktopGUIAcceptance：处理路径不在工作区或不可解析；如果没有这行，坏路径会拖垮 payload。
        return target.name  # 新增代码+DesktopGUIAcceptance：外部路径只显示文件名；如果没有这行，本机目录可能暴露到 GUI。
# 新增代码+DesktopGUIAcceptance：函数段结束，_relative_display 到此结束；如果没有边界说明，用户不易看出路径脱敏范围。


def _scenario_paths(workspace_path: Path) -> list[Path]:  # 新增代码+DesktopGUIAcceptance：函数段开始，读取验收场景文件列表；如果没有这段，场景清单无法从真实目录生成。
    scenarios_dir = _acceptance_root(workspace_path) / "scenarios"  # 新增代码+DesktopGUIAcceptance：定位 scenarios 目录；如果没有这行，GUI 不知道从哪里枚举场景。
    if not scenarios_dir.exists():  # 新增代码+DesktopGUIAcceptance：检查目录是否存在；如果没有这行，新 workspace 会直接异常。
        return []  # 新增代码+DesktopGUIAcceptance：目录不存在返回空列表；如果没有这行，前端无法显示稳定空态。
    paths = [path for path in scenarios_dir.glob("*.json") if path.is_file()]  # 新增代码+DesktopGUIAcceptance：只读取一层 JSON 场景；如果没有这行，非场景文件会混入列表。
    return sorted(paths, key=lambda item: item.name.lower())[:ACCEPTANCE_SCENARIO_LIMIT]  # 新增代码+DesktopGUIAcceptance：按文件名排序并限量；如果没有这行，清单顺序和大小会不稳定。
# 新增代码+DesktopGUIAcceptance：函数段结束，_scenario_paths 到此结束；如果没有边界说明，用户不易看出场景扫描范围。


def _scenario_category(path: Path, data: Mapping[str, Any]) -> str:  # 新增代码+DesktopGUIAcceptance：函数段开始，从文件名和 JSON 推断场景分类；如果没有这段，用户只能看一长串文件。
    explicit = _safe_text(data.get("category"), "", 60)  # 新增代码+DesktopGUIAcceptance：优先读取显式 category；如果没有这行，未来场景配置无法覆盖分类。
    if explicit:  # 新增代码+DesktopGUIAcceptance：检查是否存在显式分类；如果没有这行，显式配置不会生效。
        return explicit  # 新增代码+DesktopGUIAcceptance：返回显式分类；如果没有这行，场景归组会被文件名规则覆盖。
    name = path.stem.lower()  # 新增代码+DesktopGUIAcceptance：读取小写文件名；如果没有这行，后续关键字匹配不稳定。
    if "smoke" in name:  # 新增代码+DesktopGUIAcceptance：识别 smoke 场景；如果没有这行，安全冒烟场景不好找到。
        return "smoke"  # 新增代码+DesktopGUIAcceptance：返回 smoke 分类；如果没有这行，验收面板缺少安全入口。
    if "browser" in name or "chrome" in name:  # 新增代码+DesktopGUIAcceptance：识别浏览器场景；如果没有这行，浏览器验收无法归组。
        return "browser"  # 新增代码+DesktopGUIAcceptance：返回 browser 分类；如果没有这行，浏览器能力混在通用场景里。
    if "computer" in name or "paint" in name or "notepad" in name or "windows" in name:  # 新增代码+DesktopGUIAcceptance：识别桌面自动化场景；如果没有这行，computer-use 验收不易扫描。
        return "computer_use"  # 新增代码+DesktopGUIAcceptance：返回 computer_use 分类；如果没有这行，桌面场景分类不清。
    if "harness" in name or "phase" in name:  # 新增代码+DesktopGUIAcceptance：识别 harness/阶段场景；如果没有这行，长任务门禁场景不易扫描。
        return "harness"  # 新增代码+DesktopGUIAcceptance：返回 harness 分类；如果没有这行，成熟 agent 门禁会混在普通场景里。
    return "general"  # 新增代码+DesktopGUIAcceptance：默认分类；如果没有这行，函数可能返回空值。
# 新增代码+DesktopGUIAcceptance：函数段结束，_scenario_category 到此结束；如果没有边界说明，用户不易看出分类规则范围。


def _assertion_passed(result: Mapping[str, Any]) -> bool:  # 新增代码+DesktopGUIAcceptance：函数段开始，读取 result.json 的断言结果；如果没有这段，运行状态要到处解析 assertion。
    assertion = result.get("assertion", {}) if isinstance(result.get("assertion", {}), dict) else {}  # 新增代码+DesktopGUIAcceptance：安全读取 assertion 对象；如果没有这行，坏 result 会导致 .get 崩溃。
    return bool(assertion.get("passed", False))  # 新增代码+DesktopGUIAcceptance：返回断言是否通过；如果没有这行，状态无法区分通过和失败。
# 新增代码+DesktopGUIAcceptance：函数段结束，_assertion_passed 到此结束；如果没有边界说明，用户不易看出断言读取范围。


def _run_status(result: Mapping[str, Any]) -> str:  # 新增代码+DesktopGUIAcceptance：函数段开始，把 result.json 转成 GUI 状态；如果没有这段，前端要重复推断 passed/failed。
    if bool(result.get("completed")) and _assertion_passed(result):  # 新增代码+DesktopGUIAcceptance：完成且断言通过视为 passed；如果没有这行，成功验收会显示不清楚。
        return "passed"  # 新增代码+DesktopGUIAcceptance：返回通过状态；如果没有这行，成功状态没有稳定 token。
    if result:  # 新增代码+DesktopGUIAcceptance：只要有 result 但未通过就视为 failed；如果没有这行，失败运行可能被当作 unknown。
        return "failed"  # 新增代码+DesktopGUIAcceptance：返回失败状态；如果没有这行，面板无法突出失败证据。
    return "unknown"  # 新增代码+DesktopGUIAcceptance：缺 result 时返回未知；如果没有这行，空运行目录会误显示失败或通过。
# 新增代码+DesktopGUIAcceptance：函数段结束，_run_status 到此结束；如果没有边界说明，用户不易看出状态归纳范围。


def _iter_run_dirs(workspace_path: Path) -> list[Path]:  # 新增代码+DesktopGUIAcceptance：函数段开始，枚举已有验收运行目录；如果没有这段，运行列表只能显示空壳。
    runs_dir = _acceptance_root(workspace_path) / "runs"  # 新增代码+DesktopGUIAcceptance：定位 runs 目录；如果没有这行，证据目录没有来源。
    if not runs_dir.exists():  # 新增代码+DesktopGUIAcceptance：检查 runs 目录是否存在；如果没有这行，首次项目会抛异常。
        return []  # 新增代码+DesktopGUIAcceptance：没有运行记录时返回空列表；如果没有这行，前端空态无法稳定。
    result_files = [path for path in runs_dir.rglob("result.json") if path.is_file()]  # 新增代码+DesktopGUIAcceptance：递归查找 result.json；如果没有这行，GUI 启动时指定 RunRoot 的嵌套结果会漏掉。
    run_dirs = [path.parent for path in result_files]  # 新增代码+DesktopGUIAcceptance：把 result.json 转成 run 目录；如果没有这行，后续 evidence helper 没有目录输入。
    return sorted(run_dirs, key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)[:ACCEPTANCE_RUN_LIMIT]  # 新增代码+DesktopGUIAcceptance：按更新时间倒序限量；如果没有这行，最新证据不在最前面。
# 新增代码+DesktopGUIAcceptance：函数段结束，_iter_run_dirs 到此结束；如果没有边界说明，用户不易看出运行扫描范围。


def _evidence_item(workspace_path: Path, kind: str, label: str, path: Path) -> dict[str, Any]:  # 新增代码+DesktopGUIAcceptance：函数段开始，构造单个证据链接摘要；如果没有这段，证据字段会不一致。
    return {  # 新增代码+DesktopGUIAcceptance：返回证据对象；如果没有这行，函数没有 JSON 输出。
        "kind": kind,  # 新增代码+DesktopGUIAcceptance：保存证据类型；如果没有这行，前端不知道是截图、日志还是报告。
        "label": label,  # 新增代码+DesktopGUIAcceptance：保存可读名称；如果没有这行，用户只能看路径。
        "relative_path": _relative_display(workspace_path, path),  # 新增代码+DesktopGUIAcceptance：保存相对路径；如果没有这行，用户无法定位证据且可能看到绝对目录。
        "exists": path.exists(),  # 新增代码+DesktopGUIAcceptance：保存文件是否存在；如果没有这行，前端无法区分缺证据和未运行。
    }  # 新增代码+DesktopGUIAcceptance：证据对象结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIAcceptance：函数段结束，_evidence_item 到此结束；如果没有边界说明，用户不易看出证据白名单范围。


def _run_payload(workspace_path: Path, run_dir: Path) -> dict[str, Any]:  # 新增代码+DesktopGUIAcceptance：函数段开始，把一个 run 目录转成 GUI 卡片；如果没有这段，前端要理解 controller 目录结构。
    result_path = run_dir / "result.json"  # 新增代码+DesktopGUIAcceptance：定位结果 JSON；如果没有这行，completed/assertion 没有读取入口。
    result = _read_json_file(result_path)  # 新增代码+DesktopGUIAcceptance：读取结果 JSON；如果没有这行，运行状态没有事实源。
    surface = _controller_surface(workspace_path)  # 新增代码+DesktopGUIAcceptance：复用已有 controller_takeover 证据读取对象并隔离输出；如果没有这行，GUI 会复制外部 agent 调试面逻辑。
    evidence_summary = surface.read_acceptance_run(run_dir)  # 新增代码+DesktopGUIAcceptance：读取 result/events/readable/final screenshot 摘要；如果没有这行，证据存在性规则会漂移。
    scenario_name = _safe_text(result.get("scenario"), run_dir.name.split("-")[0], 120)  # 新增代码+DesktopGUIAcceptance：读取场景名并兜底目录前缀；如果没有这行，运行无法归属场景。
    scenario_id = _safe_id(scenario_name, _safe_id(run_dir.name, "scenario"))  # 新增代码+DesktopGUIAcceptance：生成场景 id；如果没有这行，前端无法把运行和场景卡片关联。
    final_screenshot = Path(str(result.get("final_screenshot") or evidence_summary.get("final_screenshot") or (run_dir / "final.png")))  # 新增代码+DesktopGUIAcceptance：优先使用 controller 写出的最终截图字段；如果没有这行，截图证据可能漏掉。
    evidence = [  # 新增代码+DesktopGUIAcceptance：证据列表开始；如果没有这段，用户看不到 result/events/readable/screenshot 链接。
        _evidence_item(workspace_path, "result", "result.json", result_path),  # 新增代码+DesktopGUIAcceptance：加入结果 JSON；如果没有这行，用户无法复盘核心断言。
        _evidence_item(workspace_path, "events", "events.jsonl", run_dir / "events.jsonl"),  # 新增代码+DesktopGUIAcceptance：加入事件流；如果没有这行，用户无法复盘控制器状态。
        _evidence_item(workspace_path, "readable", "latest_run_readable.md", run_dir / "latest_run_readable.md"),  # 新增代码+DesktopGUIAcceptance：加入可读摘要；如果没有这行，小白用户只能读 JSON。
        _evidence_item(workspace_path, "screenshot", "final screenshot", final_screenshot),  # 新增代码+DesktopGUIAcceptance：加入最终截图；如果没有这行，真实可见 GUI 验收缺肉眼证据索引。
    ]  # 新增代码+DesktopGUIAcceptance：证据列表结束；如果没有这行，Python 列表语法不完整。
    return {  # 新增代码+DesktopGUIAcceptance：返回运行卡片 payload；如果没有这行，函数没有 JSON 输出。
        "id": _safe_id(run_dir.name, "run"),  # 新增代码+DesktopGUIAcceptance：保存运行 id；如果没有这行，前端列表 key 不稳定。
        "scenario_id": scenario_id,  # 新增代码+DesktopGUIAcceptance：保存关联场景 id；如果没有这行，场景卡片无法显示最近结果。
        "scenario_name": scenario_name,  # 新增代码+DesktopGUIAcceptance：保存场景名；如果没有这行，运行列表不可读。
        "status": _run_status(result),  # 新增代码+DesktopGUIAcceptance：保存 passed/failed/unknown；如果没有这行，用户要读 JSON 才知道成败。
        "completed": bool(result.get("completed", evidence_summary.get("completed", False))),  # 新增代码+DesktopGUIAcceptance：保存完成状态；如果没有这行，失败原因不易区分。
        "assertion_passed": _assertion_passed(result) or bool(evidence_summary.get("assertion_passed", False)),  # 新增代码+DesktopGUIAcceptance：保存断言结果；如果没有这行，GUI 无法显示是否真正通过。
        "permission_sent_count": int(result.get("permission_sent_count", evidence_summary.get("permission_sent_count", 0)) or 0),  # 新增代码+DesktopGUIAcceptance：保存权限响应次数；如果没有这行，验收安全链缺少可见审计数字。
        "updated_at": datetime.fromtimestamp(run_dir.stat().st_mtime, UTC).isoformat() if run_dir.exists() else "",  # 新增代码+DesktopGUIAcceptance：保存更新时间；如果没有这行，用户不知道证据新旧。
        "relative_path": _relative_display(workspace_path, run_dir),  # 新增代码+DesktopGUIAcceptance：保存运行目录相对路径；如果没有这行，用户难以定位证据。
        "evidence": evidence,  # 新增代码+DesktopGUIAcceptance：保存证据链接摘要；如果没有这行，面板无法展示验收产物。
    }  # 新增代码+DesktopGUIAcceptance：运行卡片 payload 结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIAcceptance：函数段结束，_run_payload 到此结束；如果没有边界说明，用户不易看出 run 卡片白名单范围。


def _latest_run_by_scenario(runs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:  # 新增代码+DesktopGUIAcceptance：函数段开始，按场景聚合最近运行；如果没有这段，场景卡片无法显示最新结果。
    latest: dict[str, dict[str, Any]] = {}  # 新增代码+DesktopGUIAcceptance：创建聚合字典；如果没有这行，后续无法保存每个场景的最新 run。
    for run in runs:  # 新增代码+DesktopGUIAcceptance：遍历按时间倒序的 run；如果没有这行，聚合不会执行。
        scenario_id = _safe_text(run.get("scenario_id"), "", 160)  # 新增代码+DesktopGUIAcceptance：读取 run 的场景 id；如果没有这行，无法匹配场景卡片。
        if scenario_id and scenario_id not in latest:  # 新增代码+DesktopGUIAcceptance：只保存第一个也就是最新的 run；如果没有这行，旧 run 可能覆盖新结果。
            latest[scenario_id] = run  # 新增代码+DesktopGUIAcceptance：记录最近 run；如果没有这行，场景卡片没有 last_result。
    return latest  # 新增代码+DesktopGUIAcceptance：返回聚合结果；如果没有这行，调用方拿不到数据。
# 新增代码+DesktopGUIAcceptance：函数段结束，_latest_run_by_scenario 到此结束；如果没有边界说明，用户不易看出最近结果聚合范围。


def _scenario_payload(workspace_path: Path, path: Path, last_runs: Mapping[str, dict[str, Any]]) -> dict[str, Any]:  # 新增代码+DesktopGUIAcceptance：函数段开始，把场景 JSON 转成 GUI 卡片；如果没有这段，前端要直接读场景文件。
    data = _read_json_file(path)  # 新增代码+DesktopGUIAcceptance：读取场景 JSON；如果没有这行，名称、prompt 和超时无法来自事实源。
    name = _safe_text(data.get("name"), path.stem, 120)  # 新增代码+DesktopGUIAcceptance：优先使用场景 name；如果没有这行，用户只能看文件名。
    scenario_id = _safe_id(name, _safe_id(path.stem, "scenario"))  # 新增代码+DesktopGUIAcceptance：生成稳定场景 id；如果没有这行，运行按钮没有目标。
    prompt_lines = data.get("prompt_lines") if isinstance(data.get("prompt_lines"), list) else []  # 新增代码+DesktopGUIAcceptance：读取 prompt_lines 数组；如果没有这行，多轮场景没有预览输入。
    prompt_preview = _safe_text(prompt_lines[0] if prompt_lines else data.get("prompt"), "", 180)  # 新增代码+DesktopGUIAcceptance：取第一条 prompt 作为预览；如果没有这行，场景用途不可见。
    last_run = last_runs.get(scenario_id, {})  # 新增代码+DesktopGUIAcceptance：查找最近运行；如果没有这行，场景卡片无法显示最新结果。
    return {  # 新增代码+DesktopGUIAcceptance：返回场景卡片 payload；如果没有这行，函数没有 JSON 输出。
        "id": scenario_id,  # 新增代码+DesktopGUIAcceptance：保存场景 id；如果没有这行，前端按钮和 key 不稳定。
        "name": name,  # 新增代码+DesktopGUIAcceptance：保存场景名称；如果没有这行，用户看不懂场景。
        "file_name": path.name,  # 新增代码+DesktopGUIAcceptance：保存文件名；如果没有这行，用户无法回到 scenarios 目录定位配置。
        "relative_path": _relative_display(workspace_path, path),  # 新增代码+DesktopGUIAcceptance：保存相对路径；如果没有这行，GUI 可能暴露绝对路径或无法定位。
        "category": _scenario_category(path, data),  # 新增代码+DesktopGUIAcceptance：保存分类；如果没有这行，场景列表难扫描。
        "max_seconds": int(data.get("max_seconds", 0) or 0),  # 新增代码+DesktopGUIAcceptance：保存最大运行秒数；如果没有这行，用户无法预估验收耗时。
        "prompt_preview": prompt_preview,  # 新增代码+DesktopGUIAcceptance：保存 prompt 预览；如果没有这行，用户不知道点击会测试什么。
        "success_marker": _safe_text(data.get("success_marker"), "", 120),  # 新增代码+DesktopGUIAcceptance：保存成功标记；如果没有这行，用户无法理解断言目标。
        "required_event_count": len(data.get("required_event_states") if isinstance(data.get("required_event_states"), list) else []),  # 新增代码+DesktopGUIAcceptance：保存必需事件数量；如果没有这行，安全门禁规模不可见。
        "last_result": last_run,  # 新增代码+DesktopGUIAcceptance：保存最近运行摘要；如果没有这行，场景列表无法显示最新成败。
        "run_supported": True,  # 新增代码+DesktopGUIAcceptance：声明可通过 controller.ps1 启动；如果没有这行，前端不知道是否启用按钮。
        "run_unavailable_reason": "",  # 新增代码+DesktopGUIAcceptance：当前可运行时留空原因；如果没有这行，前端禁用说明字段不稳定。
    }  # 新增代码+DesktopGUIAcceptance：场景卡片 payload 结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIAcceptance：函数段结束，_scenario_payload 到此结束；如果没有边界说明，用户不易看出场景卡片白名单范围。


def _scenario_lookup(workspace_path: Path) -> dict[str, Path]:  # 新增代码+DesktopGUIAcceptance：函数段开始，构建场景 id 到文件路径的映射；如果没有这段，POST run 无法安全查找场景。
    lookup: dict[str, Path] = {}  # 新增代码+DesktopGUIAcceptance：创建空映射；如果没有这行，后续无法存储场景索引。
    for path in _scenario_paths(workspace_path):  # 新增代码+DesktopGUIAcceptance：遍历真实场景文件；如果没有这行，映射永远为空。
        data = _read_json_file(path)  # 新增代码+DesktopGUIAcceptance：读取场景 JSON；如果没有这行，name 形式的 id 无法匹配。
        lookup[_safe_id(path.stem, "scenario")] = path  # 新增代码+DesktopGUIAcceptance：按文件名索引；如果没有这行，用户传 smoke 找不到 smoke.json。
        lookup[_safe_id(data.get("name"), _safe_id(path.stem, "scenario"))] = path  # 新增代码+DesktopGUIAcceptance：按场景 name 索引；如果没有这行，前端传 name 形式 id 可能失败。
    return lookup  # 新增代码+DesktopGUIAcceptance：返回映射；如果没有这行，调用方拿不到查找结果。
# 新增代码+DesktopGUIAcceptance：函数段结束，_scenario_lookup 到此结束；如果没有边界说明，用户不易看出场景查找范围。


def build_gui_acceptance_runs_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIAcceptance：函数段开始，构建验收运行列表 payload；如果没有这段，GUI 无法读取历史证据。
    workspace_path = _workspace_path(workspace)  # 新增代码+DesktopGUIAcceptance：规范化工作区；如果没有这行，runs 路径可能不稳定。
    try:  # 新增代码+DesktopGUIAcceptance：保护运行目录读取；如果没有这行，坏证据目录会让 HTTP 500。
        runs = [_run_payload(workspace_path, run_dir) for run_dir in _iter_run_dirs(workspace_path)]  # 新增代码+DesktopGUIAcceptance：读取并白名单化运行记录；如果没有这行，payload 没有主体列表。
        status_degraded = False  # 新增代码+DesktopGUIAcceptance：标记读取未降级；如果没有这行，payload 字段不稳定。
        safe_error = ""  # 新增代码+DesktopGUIAcceptance：清空安全错误；如果没有这行，前端可能显示旧错误。
    except Exception:  # 新增代码+DesktopGUIAcceptance：捕获任意读取异常；如果没有这行，半写入证据会拖垮面板。
        runs = []  # 新增代码+DesktopGUIAcceptance：异常时返回空列表；如果没有这行，变量未定义。
        status_degraded = True  # 新增代码+DesktopGUIAcceptance：标记降级；如果没有这行，用户会误信空列表正常。
        safe_error = "验收运行记录暂时不可读。"  # 新增代码+DesktopGUIAcceptance：暴露脱敏错误；如果没有这行，用户不知道为什么没有记录。
    return {  # 新增代码+DesktopGUIAcceptance：返回完整运行列表 payload；如果没有这行，HTTP route 没有响应体。
        "ok": True,  # 新增代码+DesktopGUIAcceptance：标记成功响应；如果没有这行，前端无法区分错误 payload。
        "schema_version": GUI_V2_SCHEMA_VERSION,  # 新增代码+DesktopGUIAcceptance：暴露协议版本；如果没有这行，前端合同无法兼容。
        "workspace": str(workspace_path),  # 新增代码+DesktopGUIAcceptance：保存 workspace；如果没有这行，用户无法确认证据来源。
        "generated_at": _utc_now(),  # 新增代码+DesktopGUIAcceptance：保存生成时间；如果没有这行，用户不知道状态是否新鲜。
        "reuse_module": "learning_agent.acceptance_controller;learning_agent.computer_use_mcp_v2.windows_runtime.controller_takeover",  # 新增代码+DesktopGUIAcceptance：声明复用模块；如果没有这行，用户无法验收 GUI 没有另造验收系统。
        "run_count": len(runs),  # 新增代码+DesktopGUIAcceptance：保存运行数量；如果没有这行，摘要区缺少规模。
        "runs": runs,  # 新增代码+DesktopGUIAcceptance：保存运行卡片列表；如果没有这行，前端无法渲染历史证据。
        "status_degraded": status_degraded,  # 新增代码+DesktopGUIAcceptance：保存降级状态；如果没有这行，读取失败会像正常空态。
        "safe_error": safe_error,  # 新增代码+DesktopGUIAcceptance：保存脱敏错误；如果没有这行，用户没有故障线索。
    }  # 新增代码+DesktopGUIAcceptance：运行列表 payload 结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIAcceptance：函数段结束，build_gui_acceptance_runs_payload 到此结束；如果没有边界说明，用户不易看出运行列表范围。


def build_gui_acceptance_scenarios_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIAcceptance：函数段开始，构建验收场景清单 payload；如果没有这段，GUI 没有验收控制中心数据源。
    workspace_path = _workspace_path(workspace)  # 新增代码+DesktopGUIAcceptance：规范化工作区；如果没有这行，场景目录定位可能漂移。
    run_payload = build_gui_acceptance_runs_payload(workspace_path)  # 新增代码+DesktopGUIAcceptance：复用运行列表读取；如果没有这行，场景卡片无法关联最近结果。
    runs = run_payload.get("runs", []) if isinstance(run_payload.get("runs", []), list) else []  # 新增代码+DesktopGUIAcceptance：安全取得运行列表；如果没有这行，坏 payload 会让聚合崩溃。
    last_runs = _latest_run_by_scenario([run for run in runs if isinstance(run, dict)])  # 新增代码+DesktopGUIAcceptance：按场景聚合最近结果；如果没有这行，场景列表没有 last result。
    try:  # 新增代码+DesktopGUIAcceptance：保护场景目录读取；如果没有这行，坏场景文件会导致 HTTP 500。
        scenarios = [_scenario_payload(workspace_path, path, last_runs) for path in _scenario_paths(workspace_path)]  # 新增代码+DesktopGUIAcceptance：读取并白名单化场景列表；如果没有这行，前端没有主体数据。
        status_degraded = bool(run_payload.get("status_degraded", False))  # 新增代码+DesktopGUIAcceptance：继承运行列表降级状态；如果没有这行，证据读取失败不会出现在总览。
        safe_error = _safe_text(run_payload.get("safe_error"), "", 220)  # 新增代码+DesktopGUIAcceptance：继承运行列表脱敏错误；如果没有这行，用户看不到 runs 读取失败。
    except Exception:  # 新增代码+DesktopGUIAcceptance：捕获场景读取异常；如果没有这行，单个坏场景会拖垮整个面板。
        scenarios = []  # 新增代码+DesktopGUIAcceptance：异常时返回空场景；如果没有这行，变量未定义。
        status_degraded = True  # 新增代码+DesktopGUIAcceptance：标记降级；如果没有这行，前端会误信空场景正常。
        safe_error = "验收场景目录暂时不可读。"  # 新增代码+DesktopGUIAcceptance：暴露脱敏错误；如果没有这行，用户不知道该查 scenarios 目录。
    safe_smoke = next((scenario.get("id", "") for scenario in scenarios if scenario.get("category") == "smoke"), "")  # 新增代码+DesktopGUIAcceptance：找出安全 smoke 场景；如果没有这行，真实 GUI 验收不易定位安全样例。
    controller = _controller_surface(workspace_path).status()  # 新增代码+DesktopGUIAcceptance：复用 controller_takeover 状态并隔离输出目录；如果没有这行，GUI 无法展示可见终端门禁边界。
    return {  # 新增代码+DesktopGUIAcceptance：返回完整场景 payload；如果没有这行，HTTP route 没有响应体。
        "ok": True,  # 新增代码+DesktopGUIAcceptance：标记成功响应；如果没有这行，前端无法区分错误 payload。
        "schema_version": GUI_V2_SCHEMA_VERSION,  # 新增代码+DesktopGUIAcceptance：保存协议版本；如果没有这行，前端合同无法演进。
        "workspace": str(workspace_path),  # 新增代码+DesktopGUIAcceptance：保存 workspace；如果没有这行，用户无法确认清单来源。
        "generated_at": _utc_now(),  # 新增代码+DesktopGUIAcceptance：保存生成时间；如果没有这行，清单新鲜度不可见。
        "reuse_module": "learning_agent.acceptance_controller;learning_agent.computer_use_mcp_v2.windows_runtime.controller_takeover",  # 新增代码+DesktopGUIAcceptance：声明复用原模块；如果没有这行，用户无法验收 GUI 没有重写验收逻辑。
        "controller": {"controller_ps1_exists": bool(controller.get("controller_ps1_exists")), "visible_terminal_required": bool(controller.get("visible_terminal_required")), "runs_dir": _relative_display(workspace_path, Path(str(controller.get("runs_dir", ""))))},  # 新增代码+DesktopGUIAcceptance：暴露控制器关键状态且脱敏路径；如果没有这行，用户看不到可见终端门禁是否存在。
        "scenario_count": len(scenarios),  # 新增代码+DesktopGUIAcceptance：保存场景数量；如果没有这行，摘要区缺少规模。
        "run_count": int(run_payload.get("run_count", len(runs)) or 0),  # 新增代码+DesktopGUIAcceptance：保存运行数量；如果没有这行，摘要区缺少证据规模。
        "safe_smoke_scenario_id": _safe_text(safe_smoke, "", 160),  # 新增代码+DesktopGUIAcceptance：保存安全 smoke id；如果没有这行，验收脚本不易找到安全样例。
        "scenarios": scenarios,  # 新增代码+DesktopGUIAcceptance：保存场景列表；如果没有这行，AcceptancePanel 没有主体数据。
        "recent_runs": runs[:12],  # 新增代码+DesktopGUIAcceptance：保存最近运行摘要；如果没有这行，用户要切换端点才看到证据。
        "status_degraded": status_degraded,  # 新增代码+DesktopGUIAcceptance：保存降级状态；如果没有这行，读取失败不明显。
        "safe_error": safe_error,  # 新增代码+DesktopGUIAcceptance：保存脱敏错误；如果没有这行，前端没有故障原因。
    }  # 新增代码+DesktopGUIAcceptance：场景 payload 结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIAcceptance：函数段结束，build_gui_acceptance_scenarios_payload 到此结束；如果没有边界说明，用户不易看出场景总览范围。


def build_gui_acceptance_run_payload(workspace: str | Path, request: Mapping[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+DesktopGUIAcceptance：函数段开始，构建并可启动一次真实可见终端验收；如果没有这段，运行按钮没有后端动作。
    workspace_path = _workspace_path(workspace)  # 新增代码+DesktopGUIAcceptance：规范化工作区；如果没有这行，controller.ps1 启动目录可能错误。
    body = request if isinstance(request, Mapping) else {}  # 新增代码+DesktopGUIAcceptance：收敛请求体；如果没有这行，None 或坏 body 会导致字段读取异常。
    scenario_id = _safe_id(body.get("scenario_id") or body.get("id") or body.get("scenario"), "scenario")  # 新增代码+DesktopGUIAcceptance：读取并清理场景 id；如果没有这行，POST 可能携带危险路径。
    dry_run = bool(body.get("dry_run", False))  # 新增代码+DesktopGUIAcceptance：读取测试模式；如果没有这行，自动测试会误打开真实终端。
    lookup = _scenario_lookup(workspace_path)  # 新增代码+DesktopGUIAcceptance：构建安全场景映射；如果没有这行，无法验证请求场景属于 scenarios 目录。
    scenario_path = lookup.get(scenario_id)  # 新增代码+DesktopGUIAcceptance：查找目标场景文件；如果没有这行，无法确认是否可运行。
    if scenario_path is None:  # 新增代码+DesktopGUIAcceptance：处理未找到场景；如果没有这行，后续会启动空路径。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": "run", "scenario_id": scenario_id, "status": "not_found", "supported": False, "launched": False, "message": "没有找到这个验收场景。", "safe_error": "", "run": {}}  # 新增代码+DesktopGUIAcceptance：返回结构化 not_found；如果没有这行，前端只能显示泛化错误。
    controller_dir = _acceptance_root(workspace_path)  # 新增代码+DesktopGUIAcceptance：定位控制器目录；如果没有这行，controller.ps1 路径无法生成。
    controller_ps1 = controller_dir / "controller.ps1"  # 新增代码+DesktopGUIAcceptance：定位 PowerShell 控制器；如果没有这行，启动命令没有脚本入口。
    if not controller_ps1.exists():  # 新增代码+DesktopGUIAcceptance：检查 controller.ps1 是否存在；如果没有这行，按钮会报底层文件不存在。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": "run", "scenario_id": scenario_id, "status": "unavailable", "supported": False, "launched": False, "message": "验收控制器 controller.ps1 不存在。", "safe_error": "", "run": {}}  # 新增代码+DesktopGUIAcceptance：返回控制器不可用；如果没有这行，前端无法解释按钮失败。
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")  # 新增代码+DesktopGUIAcceptance：生成 run root 时间戳；如果没有这行，多次 GUI 启动目录可能冲突。
    run_root = controller_dir / "runs" / f"gui_{scenario_id}_{timestamp}"  # 新增代码+DesktopGUIAcceptance：为本次 GUI 请求准备独立输出根目录；如果没有这行，GUI 难以定位本次证据。
    relative_scenario = f"scenarios/{scenario_path.name}"  # 新增代码+DesktopGUIAcceptance：生成 controller.ps1 期望的相对场景路径；如果没有这行，启动命令会依赖当前目录。
    plan = _controller_surface(workspace_path).build_takeover_plan(relative_scenario, run_root=run_root)  # 新增代码+DesktopGUIAcceptance：复用已有接管计划生成并隔离输出目录；如果没有这行，GUI 会复制 PowerShell 命令格式。
    command_args = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(controller_ps1), "-ScenarioPath", relative_scenario, "-RunRoot", str(run_root)]  # 新增代码+DesktopGUIAcceptance：构造 Popen 参数数组；如果没有这行，真实运行没有安全的参数化启动方式。
    if dry_run:  # 新增代码+DesktopGUIAcceptance：测试模式只返回计划；如果没有这行，单元测试和 GUI 列表验收会误启动真实终端。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": "run", "scenario_id": scenario_id, "status": "planned", "supported": True, "launched": False, "message": "已生成真实可见终端验收启动计划。", "safe_error": "", "command": plan.get("powershell_command", ""), "run": {"run_root": _relative_display(workspace_path, run_root), "scenario_path": _relative_display(workspace_path, scenario_path)}}  # 新增代码+DesktopGUIAcceptance：返回 dry-run 计划；如果没有这行，测试无法验证命令合同。
    if not sys.platform.startswith("win"):  # 新增代码+DesktopGUIAcceptance：非 Windows 不启动 Windows 终端；如果没有这行，Linux/macOS 测试机可能报不清楚的底层错误。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": "run", "scenario_id": scenario_id, "status": "unavailable", "supported": False, "launched": False, "message": "真实可见终端验收启动只支持 Windows。", "safe_error": "", "command": plan.get("powershell_command", ""), "run": {"run_root": _relative_display(workspace_path, run_root), "scenario_path": _relative_display(workspace_path, scenario_path)}}  # 新增代码+DesktopGUIAcceptance：返回平台不可用；如果没有这行，前端无法解释启动失败。
    run_root.mkdir(parents=True, exist_ok=True)  # 新增代码+DesktopGUIAcceptance：预创建 run root；如果没有这行，控制器可能因输出目录缺失而失败。
    creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)  # 新增代码+DesktopGUIAcceptance：请求新控制台窗口；如果没有这行，验收可能不满足肉眼可见终端门禁。
    process = subprocess.Popen(command_args, cwd=str(workspace_path), creationflags=creationflags)  # 新增代码+DesktopGUIAcceptance：启动现有 controller.ps1；如果没有这行，运行按钮不会真正执行验收。
    return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": "run", "scenario_id": scenario_id, "status": "launched", "supported": True, "launched": True, "pid": int(process.pid), "message": "已启动真实可见终端验收控制器。", "safe_error": "", "command": plan.get("powershell_command", ""), "run": {"run_root": _relative_display(workspace_path, run_root), "scenario_path": _relative_display(workspace_path, scenario_path)}}  # 新增代码+DesktopGUIAcceptance：返回启动结果；如果没有这行，前端拿不到 pid 和证据目录提示。
# 新增代码+DesktopGUIAcceptance：函数段结束，build_gui_acceptance_run_payload 到此结束；如果没有边界说明，用户不易看出启动动作范围。
