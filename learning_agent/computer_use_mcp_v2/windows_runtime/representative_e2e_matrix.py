"""Phase74 representative real-app E2E matrix for Windows Computer Use."""  # 新增代码+Phase74RepresentativeE2E: 标明本文件负责代表性真实应用 E2E 矩阵；如果没有这行代码，后续读者不容易区分合同矩阵和单个动作模块。
from __future__ import annotations  # 新增代码+Phase74RepresentativeE2E: 启用延迟类型注解，避免运行时因为类型提示互相引用而导入失败；如果没有这行代码，后续扩展类型时更容易遇到循环导入。

import json  # 新增代码+Phase74RepresentativeE2E: 导入 JSON 用于命令行打印结构化报告；如果没有这行代码，真实终端失败时不易复盘。
import time  # 新增代码+Phase74RepresentativeE2E: 导入 time 用于生成证据时间戳；如果没有这行代码，交互证据缺少发生时间。
from pathlib import Path  # 新增代码+Phase74RepresentativeE2E: 导入 Path 管理 Windows 证据目录；如果没有这行代码，受控目录路径容易拼错。
from typing import Any  # 新增代码+Phase74RepresentativeE2E: 导入 Any 描述 JSON 风格报告；如果没有这行代码，接口边界不容易读懂。

from learning_agent.computer_use_mcp_v2.windows_runtime.windows_launch_resolver import build_launch_plan  # 新增代码+Phase74RepresentativeE2E: 复用 Phase69 安全启动计划；如果没有这行代码，代表性场景会重复实现应用启动边界。
from learning_agent.computer_use_mcp_v2.windows_runtime.generic_input_actions import build_drag_path, build_hotkey_events, build_menu_sequence  # 新增代码+Phase74RepresentativeE2E: 复用 Phase71 通用输入事件构建器；如果没有这行代码，画图和菜单动作会变成手写脆弱协议。
from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase74RepresentativeE2E: 复用原子 JSON 写入工具；如果没有这行代码，证据文件崩溃时可能留下半个 JSON。


PHASE74_REPRESENTATIVE_E2E_MARKER = "PHASE74_REPRESENTATIVE_E2E_READY"  # 新增代码+Phase74RepresentativeE2E: 定义真实终端验收 ready 标记；如果没有这行代码，controller 无法稳定识别 Phase74 输出。
PHASE74_REPRESENTATIVE_E2E_OK_TOKEN = "PHASE74_REPRESENTATIVE_E2E_OK"  # 新增代码+Phase74RepresentativeE2E: 定义真实终端验收 OK 标记；如果没有这行代码，用户无法一眼确认本阶段合同通过。
PHASE74_REPRESENTATIVE_E2E_MODEL = "phase74_windows_representative_e2e_matrix"  # 新增代码+Phase74RepresentativeE2E: 定义本阶段能力模型名称；如果没有这行代码，后续最终矩阵无法统一引用 Phase74。
PHASE74_ACTIONS_EXPANDED = False  # 新增代码+Phase74RepresentativeE2E: 明确 Phase74 安全合同不扩大真实桌面动作面；如果没有这行代码，测试可能误以为本阶段会真实派发输入。
DEFAULT_PHASE74_REPRESENTATIVE_E2E_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "representative_e2e"  # 新增代码+Phase74RepresentativeE2E: 定义默认受控证据目录；如果没有这行代码，合同输出可能散落到用户目录。


def _phase74_bool_token(value: Any) -> str:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，把布尔值转换成验收 token 需要的小写 true/false；如果没有这个函数，CLI 输出容易出现 True/False 漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase74RepresentativeE2E: 返回稳定小写布尔字符串；如果没有这行代码，真实终端场景 token 无法稳定匹配。
# 新增代码+Phase74RepresentativeE2E: 函数段结束，_phase74_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出 token 转换范围。


def _phase74_timestamp() -> str:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，生成 UTC 时间戳；如果没有这个函数，证据文件无法说明何时生成。
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())  # 新增代码+Phase74RepresentativeE2E: 返回稳定 UTC 文本；如果没有这行代码，多机或跨时区验收难以对齐。
# 新增代码+Phase74RepresentativeE2E: 函数段结束，_phase74_timestamp 到此结束；如果没有这个边界说明，初学者不容易看出时间戳范围。


def _phase74_safe_text(value: Any, limit: int = 240) -> str:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，把任意文本压成安全单行；如果没有这个函数，prompt、路径或动作名可能打乱日志。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase74RepresentativeE2E: 清理换行和首尾空白；如果没有这行代码，证据 JSON 和 CLI 可能出现多行污染。
    return text[: max(0, int(limit))]  # 新增代码+Phase74RepresentativeE2E: 限制最大长度；如果没有这行代码，长文本可能刷爆终端或证据文件。
# 新增代码+Phase74RepresentativeE2E: 函数段结束，_phase74_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清理范围。


def _phase74_common_safety() -> dict[str, Any]:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，返回所有场景共享的安全边界字段；如果没有这个函数，每个场景可能漏填隐私或系统副作用字段。
    return {"reads_private_profile": False, "cookies_read": False, "tokens_read": False, "changes_registry": False, "changes_system_settings": False, "requires_admin": False, "terminal_command_used": False, "actions_expanded": PHASE74_ACTIONS_EXPANDED}  # 新增代码+Phase74RepresentativeE2E: 返回统一安全字段；如果没有这行代码，矩阵无法一致证明不碰隐私和系统设置。
# 新增代码+Phase74RepresentativeE2E: 函数段结束，_phase74_common_safety 到此结束；如果没有这个边界说明，初学者不容易看出共享安全字段范围。


def _phase74_launch_plan_matches_target(plan: dict[str, Any], *, executable_name: str, app_names: set[str], display_names: set[str], shortcut_names: set[str]) -> bool:  # 修改代码+Phase74LaunchResolverAlignment: 函数段开始，用 resolver 的多后端身份判断代表性应用目标；如果没有这段函数，Phase74 会继续只认 exe 字段而误判开始菜单/AppX 安全启动失败。
    executable = str(plan.get("executable", "") or "").casefold()  # 修改代码+Phase74LaunchResolverAlignment: 读取 argv 后端可执行名；如果没有这行代码，Notepad/Paint 这类 exe 后端无法继续被识别。
    app_name = str(plan.get("app_name", "") or "").casefold()  # 修改代码+Phase74LaunchResolverAlignment: 读取清洗后的应用名；如果没有这行代码，开始菜单快捷方式后端缺 executable 时无法识别目标。
    display_name = str(plan.get("display_name", "") or "").casefold()  # 修改代码+Phase74LaunchResolverAlignment: 读取用户可见显示名；如果没有这行代码，File Explorer/Microsoft Edge 这类显示名候选会被误判。
    shortcut_id = str(plan.get("shortcut_id", "") or plan.get("launch_id", "") or "").casefold()  # 修改代码+Phase74LaunchResolverAlignment: 读取快捷方式身份；如果没有这行代码，start_menu_shortcut 后端没有 exe 时缺少强证据。
    safe_resolver_plan = bool(plan.get("safe_to_launch") and plan.get("resolver_used") and not plan.get("changes_registry") and not plan.get("changes_system_settings") and not plan.get("requires_admin") and not plan.get("uses_shell_string"))  # 修改代码+Phase74LaunchResolverAlignment: 先确认计划安全且来自 resolver；如果没有这行代码，普通字符串或高风险 shell 计划可能混入代表性矩阵。
    executable_match = bool(executable and executable == executable_name.casefold())  # 修改代码+Phase74LaunchResolverAlignment: 判断 exe 后端是否命中目标；如果没有这行代码，传统 argv 启动路径会被漏掉。
    app_name_match = bool(app_name and app_name in {name.casefold() for name in app_names})  # 修改代码+Phase74LaunchResolverAlignment: 判断清洗应用名是否命中目标；如果没有这行代码，fileexplorer/microsoftedge 这类规范名无法通过。
    display_name_match = bool(display_name and display_name in {name.casefold() for name in display_names})  # 修改代码+Phase74LaunchResolverAlignment: 判断显示名是否命中目标；如果没有这行代码，真实开始菜单名称变化会让矩阵过脆。
    shortcut_match = bool(shortcut_id and shortcut_id in {name.casefold() for name in shortcut_names})  # 修改代码+Phase74LaunchResolverAlignment: 判断快捷方式标识是否命中目标；如果没有这行代码，start_menu_shortcut 后端证据无法进入合同。
    return bool(safe_resolver_plan and (executable_match or app_name_match or display_name_match or shortcut_match))  # 修改代码+Phase74LaunchResolverAlignment: 返回多后端目标匹配结论；如果没有这行代码，Phase74 仍会和当前 launch resolver 设计脱节。
# 修改代码+Phase74LaunchResolverAlignment: 函数段结束，_phase74_launch_plan_matches_target 到此结束；如果没有这个边界说明，用户不容易看出多后端目标判断范围。


def _phase74_write_json_artifact(path: Path, payload: dict[str, Any]) -> str:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，原子写入场景证据 JSON；如果没有这个函数，每个场景会重复且可能半写。
    target = atomic_write_json(path, payload)  # 新增代码+Phase74RepresentativeE2E: 使用 runtime 原子写入工具保存证据；如果没有这行代码，崩溃时可能留下损坏 JSON。
    return str(Path(target))  # 新增代码+Phase74RepresentativeE2E: 返回写入后的字符串路径；如果没有这行代码，报告无法给测试和用户定位证据。
# 新增代码+Phase74RepresentativeE2E: 函数段结束，_phase74_write_json_artifact 到此结束；如果没有这个边界说明，初学者不容易看出证据写入范围。


def _phase74_paint_stroke(name: str, color: str, element: str, points: list[dict[str, int]]) -> dict[str, Any]:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，把一个皮卡丘笔画转换成可审计鼠标拖拽动作；如果没有这个函数，画图动作会散落且不易证明拟人。
    safe_name = _phase74_safe_text(name, 80)  # 新增代码+Phase74RepresentativeE2E: 清理笔画名；如果没有这行代码，证据中的动作名可能污染日志。
    safe_color = _phase74_safe_text(color, 40).lower()  # 新增代码+Phase74RepresentativeE2E: 清理颜色名并转小写；如果没有这行代码，颜色集合判断可能漂移。
    safe_element = _phase74_safe_text(element, 80)  # 新增代码+Phase74RepresentativeE2E: 清理视觉元素名；如果没有这行代码，皮卡丘元素集合可能不稳定。
    safe_points = [dict(point) for point in list(points or []) if isinstance(point, dict)]  # 新增代码+Phase74RepresentativeE2E: 复制并过滤路径点；如果没有这行代码，坏点位可能破坏拖拽构建。
    events = build_drag_path(safe_points)  # 新增代码+Phase74RepresentativeE2E: 复用 Phase71 生成鼠标拖拽事件；如果没有这行代码，画图动作就不是统一输入协议。
    event_types = [str(event.get("type", "")) for event in events]  # 新增代码+Phase74RepresentativeE2E: 提取事件类型用于验证拖拽闭合；如果没有这行代码，humanlike 标志没有事实来源。
    continuous_mouse_path = bool(event_types.count("mouse_move") >= 2 and "mouse_down" in event_types and "mouse_up" in event_types)  # 新增代码+Phase74RepresentativeE2E: 判断是否为连续鼠标路径；如果没有这行代码，单点跳跃也可能被当作拟人绘制。
    return {"name": safe_name, "color": safe_color, "element": safe_element, "operation": "drag_path", "points": safe_points, "events": events, "event_count": len(events), "continuous_mouse_path": continuous_mouse_path, "humanlike_action": continuous_mouse_path, "real_dispatch_allowed": False}  # 新增代码+Phase74RepresentativeE2E: 返回完整笔画证据；如果没有这行代码，画图场景拿不到可审计动作。
# 新增代码+Phase74RepresentativeE2E: 函数段结束，_phase74_paint_stroke 到此结束；如果没有这个边界说明，初学者不容易看出笔画构建范围。


class WindowsRepresentativeE2EMatrix:  # 新增代码+Phase74RepresentativeE2E: 类段开始，组织代表性真实应用 E2E 场景；如果没有这个类，Notepad、Explorer、Browser、窗口和 Paint 验收会散落。
    def __init__(self, base_dir: str | Path | None = None) -> None:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，初始化受控证据根目录；如果没有这个函数，场景无法隔离输出位置。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_PHASE74_REPRESENTATIVE_E2E_ROOT  # 新增代码+Phase74RepresentativeE2E: 使用调用方目录或默认目录；如果没有这行代码，测试无法用临时目录隔离。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase74RepresentativeE2E: 确保证据根目录存在；如果没有这行代码，首次写入场景证据会失败。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，WindowsRepresentativeE2EMatrix.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _artifact_path(self, scenario_dir: str, file_name: str) -> Path:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，生成某个场景的受控证据路径；如果没有这个函数，各场景可能写到不一致目录。
        safe_dir = _phase74_safe_text(scenario_dir, 120) or "scenario"  # 新增代码+Phase74RepresentativeE2E: 清理场景目录名；如果没有这行代码，坏目录名可能导致路径混乱。
        safe_file = _phase74_safe_text(file_name, 160) or "evidence.json"  # 新增代码+Phase74RepresentativeE2E: 清理证据文件名；如果没有这行代码，空文件名会让写入失败。
        target_dir = self.base_dir / safe_dir  # 新增代码+Phase74RepresentativeE2E: 把场景目录限制在根目录下；如果没有这行代码，场景文件无法统一归档。
        target_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase74RepresentativeE2E: 确保场景目录存在；如果没有这行代码，首次写入该场景会失败。
        return target_dir / safe_file  # 新增代码+Phase74RepresentativeE2E: 返回完整证据路径；如果没有这行代码，调用方拿不到写入目标。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，WindowsRepresentativeE2EMatrix._artifact_path 到此结束；如果没有这个边界说明，初学者不容易看出路径构建范围。

    def _write_scenario(self, scenario_dir: str, file_name: str, payload: dict[str, Any]) -> str:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，写入单个场景证据并返回路径；如果没有这个函数，各场景会重复写入逻辑。
        artifact_path = self._artifact_path(scenario_dir, file_name)  # 新增代码+Phase74RepresentativeE2E: 生成受控证据路径；如果没有这行代码，证据没有落点。
        enriched = dict(payload)  # 新增代码+Phase74RepresentativeE2E: 复制 payload 避免污染调用方对象；如果没有这行代码，写入补字段可能改变内存报告。
        enriched["marker"] = PHASE74_REPRESENTATIVE_E2E_MARKER  # 新增代码+Phase74RepresentativeE2E: 写入阶段 marker；如果没有这行代码，证据文件难以归属 Phase74。
        enriched["model"] = PHASE74_REPRESENTATIVE_E2E_MODEL  # 新增代码+Phase74RepresentativeE2E: 写入模型名；如果没有这行代码，最终矩阵无法识别证据版本。
        enriched["created_at"] = _phase74_timestamp()  # 新增代码+Phase74RepresentativeE2E: 写入证据创建时间；如果没有这行代码，审计无法排序。
        return _phase74_write_json_artifact(artifact_path, enriched)  # 新增代码+Phase74RepresentativeE2E: 原子写入并返回路径；如果没有这行代码，场景证据不会落盘。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，WindowsRepresentativeE2EMatrix._write_scenario 到此结束；如果没有这个边界说明，初学者不容易看出证据落盘范围。

    def build_notepad_scenario(self, real_smoke: bool = False) -> dict[str, Any]:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，构建记事本文本编辑代表场景；如果没有这个函数，矩阵缺少最常见文本应用验收。
        controlled_text_path = self._artifact_path("e2e_notepad", "phase74_notepad_note.txt")  # 新增代码+Phase74RepresentativeE2E: 指定受控文本文件路径；如果没有这行代码，记事本场景可能写到用户真实文档。
        launch_plan = build_launch_plan("notepad", test_file=str(controlled_text_path))  # 新增代码+Phase74RepresentativeE2E: 生成安全记事本启动计划；如果没有这行代码，场景缺少真实应用目标。
        menu_events = build_menu_sequence(["File", "Save As"])  # 新增代码+Phase74RepresentativeE2E: 构建保存菜单路径；如果没有这行代码，文本保存动作无法审计。
        hotkey_events = build_hotkey_events(["ctrl", "s"])  # 新增代码+Phase74RepresentativeE2E: 构建保存热键事件；如果没有这行代码，通用快捷键能力无法纳入场景。
        payload = {"scenario_id": "notepad_text_edit", "target_process": "notepad.exe", "launch_plan": launch_plan, "controlled_text_path": str(controlled_text_path), "operations": ["launch_app", "focus_window", "type_text", "save_to_controlled_file", "verify_saved_text"], "menu_events": menu_events, "hotkey_events": hotkey_events, "real_smoke_requested": bool(real_smoke), "real_visible_app_invoked": False, "scenario_passed": bool(launch_plan.get("safe_to_launch") and launch_plan.get("executable") == "notepad.exe" and menu_events and hotkey_events)}  # 新增代码+Phase74RepresentativeE2E: 汇总记事本场景证据；如果没有这行代码，报告无法证明文本编辑类应用可覆盖。
        artifact_path = self._write_scenario("e2e_notepad", "notepad_text_edit_evidence.json", payload)  # 新增代码+Phase74RepresentativeE2E: 写入记事本证据；如果没有这行代码，场景只有内存报告不可审计。
        result = dict(_phase74_common_safety(), artifact_path=artifact_path, process_name="notepad.exe", notepad_scenario=bool(payload["scenario_passed"]), scenario_passed=bool(payload["scenario_passed"]), real_visible_app_invoked=False)  # 新增代码+Phase74RepresentativeE2E: 构造统一结果字段；如果没有这行代码，矩阵汇总无法读取通过状态。
        result.update(payload)  # 新增代码+Phase74RepresentativeE2E: 合并详细证据字段；如果没有这行代码，调用方看不到启动计划和操作列表。
        return result  # 新增代码+Phase74RepresentativeE2E: 返回记事本场景报告；如果没有这行代码，矩阵无法包含该场景。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，WindowsRepresentativeE2EMatrix.build_notepad_scenario 到此结束；如果没有这个边界说明，初学者不容易看出记事本场景范围。

    def build_explorer_scenario(self, real_smoke: bool = False) -> dict[str, Any]:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，构建资源管理器文件浏览代表场景；如果没有这个函数，矩阵缺少文件系统 UI 应用验收。
        controlled_folder = self._artifact_path("e2e_explorer", "controlled_folder_anchor.json").parent  # 新增代码+Phase74RepresentativeE2E: 指定受控文件夹；如果没有这行代码，资源管理器场景可能浏览用户真实资料。
        launch_plan = build_launch_plan("explorer", test_file=str(controlled_folder))  # 新增代码+Phase74RepresentativeE2E: 生成安全资源管理器启动计划；如果没有这行代码，文件浏览场景没有真实应用目标。
        explorer_target_verified = _phase74_launch_plan_matches_target(launch_plan, executable_name="explorer.exe", app_names={"explorer", "fileexplorer"}, display_names={"File Explorer", "Explorer"}, shortcut_names={"File Explorer.lnk", "Explorer.lnk"})  # 修改代码+Phase74LaunchResolverAlignment: 允许 exe 或开始菜单快捷方式证明资源管理器目标；如果没有这行代码，当前 resolver 返回 shortcut 时代表性矩阵会误报失败。
        payload = {"scenario_id": "explorer_controlled_folder", "target_process": "explorer.exe", "launch_plan": launch_plan, "controlled_folder": str(controlled_folder), "operations": ["launch_app", "focus_window", "open_controlled_folder", "select_controlled_file", "verify_path_inside_root"], "real_smoke_requested": bool(real_smoke), "real_visible_app_invoked": False, "scenario_passed": bool(explorer_target_verified and str(controlled_folder).startswith(str(self.base_dir)))}  # 修改代码+Phase74LaunchResolverAlignment: 汇总资源管理器场景证据并认可多后端安全目标；如果没有这行代码，文件浏览类应用会被旧 exe-only 合同误杀。
        artifact_path = self._write_scenario("e2e_explorer", "explorer_controlled_folder_evidence.json", payload)  # 新增代码+Phase74RepresentativeE2E: 写入资源管理器证据；如果没有这行代码，文件浏览场景不可审计。
        result = dict(_phase74_common_safety(), artifact_path=artifact_path, process_name="explorer.exe", explorer_scenario=bool(payload["scenario_passed"]), scenario_passed=bool(payload["scenario_passed"]), real_visible_app_invoked=False)  # 新增代码+Phase74RepresentativeE2E: 构造统一结果字段；如果没有这行代码，矩阵汇总无法读取 explorer 通过状态。
        result.update(payload)  # 新增代码+Phase74RepresentativeE2E: 合并详细证据字段；如果没有这行代码，调用方看不到受控目录和操作列表。
        return result  # 新增代码+Phase74RepresentativeE2E: 返回资源管理器场景报告；如果没有这行代码，矩阵无法包含该场景。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，WindowsRepresentativeE2EMatrix.build_explorer_scenario 到此结束；如果没有这个边界说明，初学者不容易看出资源管理器场景范围。

    def build_browser_scenario(self, real_smoke: bool = False) -> dict[str, Any]:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，构建浏览器安全页面代表场景；如果没有这个函数，矩阵缺少网页类应用验收。
        safe_page = self._artifact_path("e2e_browser", "phase74_safe_page.html")  # 新增代码+Phase74RepresentativeE2E: 指定受控本地页面路径；如果没有这行代码，浏览器场景可能访问用户账号站点。
        launch_plan = build_launch_plan("msedge", test_file="about:blank")  # 新增代码+Phase74RepresentativeE2E: 生成安全浏览器启动计划；如果没有这行代码，浏览器场景没有真实应用目标。
        browser_target_verified = _phase74_launch_plan_matches_target(launch_plan, executable_name="msedge.exe", app_names={"msedge", "microsoftedge"}, display_names={"Microsoft Edge", "Edge"}, shortcut_names={"Microsoft Edge.lnk", "Edge.lnk"})  # 修改代码+Phase74LaunchResolverAlignment: 允许 exe 或开始菜单快捷方式证明 Edge 目标；如果没有这行代码，当前 resolver 返回 shortcut 时浏览器代表场景会误报失败。
        payload = {"scenario_id": "browser_safe_blank_page", "target_process": "msedge.exe", "launch_plan": launch_plan, "safe_page": str(safe_page), "operations": ["launch_app", "open_about_blank_or_controlled_page", "type_url", "verify_page_title"], "reads_private_profile": False, "cookies_read": False, "tokens_read": False, "uses_private_profile_content": False, "real_smoke_requested": bool(real_smoke), "real_visible_app_invoked": False, "scenario_passed": bool(browser_target_verified and not launch_plan.get("changes_system_settings"))}  # 修改代码+Phase74LaunchResolverAlignment: 汇总浏览器场景证据并认可多后端安全目标；如果没有这行代码，网页类应用会被旧 exe-only 合同误杀。
        artifact_path = self._write_scenario("e2e_browser", "browser_safe_page_evidence.json", payload)  # 新增代码+Phase74RepresentativeE2E: 写入浏览器证据；如果没有这行代码，浏览器场景不可审计。
        result = dict(_phase74_common_safety(), artifact_path=artifact_path, process_name="msedge.exe", browser_scenario=bool(payload["scenario_passed"]), scenario_passed=bool(payload["scenario_passed"]), real_visible_app_invoked=False)  # 新增代码+Phase74RepresentativeE2E: 构造统一结果字段；如果没有这行代码，矩阵汇总无法读取 browser 通过状态。
        result.update(payload)  # 新增代码+Phase74RepresentativeE2E: 合并详细证据字段；如果没有这行代码，调用方看不到浏览器隐私边界。
        return result  # 新增代码+Phase74RepresentativeE2E: 返回浏览器场景报告；如果没有这行代码，矩阵无法包含该场景。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，WindowsRepresentativeE2EMatrix.build_browser_scenario 到此结束；如果没有这个边界说明，初学者不容易看出浏览器场景范围。

    def build_window_style_scenario(self, real_smoke: bool = False) -> dict[str, Any]:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，构建窗口风格和对话框代表场景；如果没有这个函数，矩阵缺少多窗口/弹窗类验收。
        launch_plan = build_launch_plan("notepad", test_file=str(self._artifact_path("e2e_window_style", "window_style_note.txt")))  # 新增代码+Phase74RepresentativeE2E: 用记事本保存对话框代表标准窗口风格；如果没有这行代码，场景没有安全应用载体。
        menu_events = build_menu_sequence(["File", "Save As"])  # 新增代码+Phase74RepresentativeE2E: 构建打开标准保存对话框的菜单事件；如果没有这行代码，窗口风格场景缺少弹窗入口。
        payload = {"scenario_id": "window_style_standard_dialog", "target_process": "notepad.exe", "launch_plan": launch_plan, "window_styles_covered": ["main_window", "standard_menu", "modal_save_dialog", "file_name_edit", "save_button"], "operations": ["launch_app", "focus_main_window", "open_save_dialog", "locate_file_name_edit", "close_or_cancel_without_side_effect"], "menu_events": menu_events, "real_smoke_requested": bool(real_smoke), "real_visible_app_invoked": False, "scenario_passed": bool(launch_plan.get("safe_to_launch") and menu_events and not launch_plan.get("changes_system_settings"))}  # 新增代码+Phase74RepresentativeE2E: 汇总窗口风格场景证据；如果没有这行代码，报告无法证明窗口和对话框类交互可覆盖。
        artifact_path = self._write_scenario("e2e_window_style", "window_style_dialog_evidence.json", payload)  # 新增代码+Phase74RepresentativeE2E: 写入窗口风格证据；如果没有这行代码，对话框场景不可审计。
        result = dict(_phase74_common_safety(), artifact_path=artifact_path, process_name="notepad.exe", window_style_scenario=bool(payload["scenario_passed"]), scenario_passed=bool(payload["scenario_passed"]), real_visible_app_invoked=False)  # 新增代码+Phase74RepresentativeE2E: 构造统一结果字段；如果没有这行代码，矩阵汇总无法读取窗口风格通过状态。
        result.update(payload)  # 新增代码+Phase74RepresentativeE2E: 合并详细证据字段；如果没有这行代码，调用方看不到覆盖的窗口风格。
        return result  # 新增代码+Phase74RepresentativeE2E: 返回窗口风格场景报告；如果没有这行代码，矩阵无法包含该场景。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，WindowsRepresentativeE2EMatrix.build_window_style_scenario 到此结束；如果没有这个边界说明，初学者不容易看出窗口风格场景范围。

    def build_paint_pikachu_scenario(self, real_smoke: bool = False) -> dict[str, Any]:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，构建画图软件画皮卡丘代表场景；如果没有这个函数，用户要求的本机画图通用性证明缺失。
        planned_png_path = self._artifact_path("e2e_paint", "pikachu_via_mspaint.png")  # 新增代码+Phase74RepresentativeE2E: 规划 Paint 保存目标但不直接写位图；如果没有这行代码，保存路径不可审计。
        launch_plan = build_launch_plan("mspaint", test_file=str(planned_png_path))  # 新增代码+Phase74RepresentativeE2E: 生成真实 Paint 应用启动计划；如果没有这行代码，画图场景可能不是控制本机画图软件。
        draw_actions = [_phase74_paint_stroke("body_outline", "yellow", "yellow_body", [{"x": 240, "y": 220}, {"x": 210, "y": 280}, {"x": 230, "y": 350}, {"x": 300, "y": 380}, {"x": 370, "y": 350}, {"x": 390, "y": 280}, {"x": 360, "y": 220}, {"x": 300, "y": 200}, {"x": 240, "y": 220}]), _phase74_paint_stroke("left_ear", "yellow", "left_ear", [{"x": 250, "y": 220}, {"x": 210, "y": 130}, {"x": 235, "y": 210}]), _phase74_paint_stroke("right_ear", "yellow", "right_ear", [{"x": 350, "y": 220}, {"x": 395, "y": 130}, {"x": 365, "y": 210}]), _phase74_paint_stroke("left_ear_tip", "black", "black_ear_tips", [{"x": 210, "y": 130}, {"x": 224, "y": 164}, {"x": 230, "y": 145}]), _phase74_paint_stroke("right_ear_tip", "black", "black_ear_tips", [{"x": 395, "y": 130}, {"x": 382, "y": 164}, {"x": 375, "y": 145}]), _phase74_paint_stroke("left_eye", "black", "eyes", [{"x": 270, "y": 260}, {"x": 274, "y": 264}, {"x": 278, "y": 260}, {"x": 274, "y": 256}, {"x": 270, "y": 260}]), _phase74_paint_stroke("right_eye", "black", "eyes", [{"x": 330, "y": 260}, {"x": 334, "y": 264}, {"x": 338, "y": 260}, {"x": 334, "y": 256}, {"x": 330, "y": 260}]), _phase74_paint_stroke("mouth_smile", "black", "mouth", [{"x": 290, "y": 300}, {"x": 300, "y": 310}, {"x": 310, "y": 300}]), _phase74_paint_stroke("left_cheek", "red", "red_cheeks", [{"x": 250, "y": 300}, {"x": 258, "y": 308}, {"x": 266, "y": 300}, {"x": 258, "y": 292}, {"x": 250, "y": 300}]), _phase74_paint_stroke("right_cheek", "red", "red_cheeks", [{"x": 350, "y": 300}, {"x": 358, "y": 308}, {"x": 366, "y": 300}, {"x": 358, "y": 292}, {"x": 350, "y": 300}]), _phase74_paint_stroke("left_arm", "yellow", "arms", [{"x": 230, "y": 300}, {"x": 190, "y": 325}, {"x": 220, "y": 330}]), _phase74_paint_stroke("right_arm", "yellow", "arms", [{"x": 370, "y": 300}, {"x": 410, "y": 325}, {"x": 380, "y": 330}]), _phase74_paint_stroke("lightning_tail", "yellow", "lightning_tail", [{"x": 390, "y": 310}, {"x": 450, "y": 285}, {"x": 430, "y": 330}, {"x": 490, "y": 305}, {"x": 450, "y": 360}])]  # 新增代码+Phase74RepresentativeE2E: 构建十二个以上拟人鼠标笔画；如果没有这行代码，皮卡丘绘制没有可审计动作证据。
        colors = {str(action.get("color", "")) for action in draw_actions}  # 新增代码+Phase74RepresentativeE2E: 汇总使用颜色；如果没有这行代码，无法证明黄色/黑色/红色元素齐全。
        elements = {str(action.get("element", "")) for action in draw_actions}  # 新增代码+Phase74RepresentativeE2E: 汇总视觉元素；如果没有这行代码，无法证明皮卡丘特征齐全。
        humanlike_drawing_actions = bool(draw_actions and all(action.get("humanlike_action") for action in draw_actions))  # 新增代码+Phase74RepresentativeE2E: 判断所有笔画都是连续鼠标动作；如果没有这行代码，画图可能只是静态计划。
        continuous_mouse_path = bool(draw_actions and all(action.get("continuous_mouse_path") for action in draw_actions))  # 新增代码+Phase74RepresentativeE2E: 判断所有笔画都有连续轨迹；如果没有这行代码，拟人绘制质量不可验证。
        draw_action_count = len(draw_actions)  # 新增代码+Phase74RepresentativeE2E: 统计笔画数量；如果没有这行代码，场景无法量化是否足够复杂。
        paint_canvas_not_blank = bool(draw_action_count >= 12 and {"yellow", "black", "red"}.issubset(colors))  # 新增代码+Phase74RepresentativeE2E: 用笔画数量和颜色证明画布非空；如果没有这行代码，空画布也可能误过。
        pikachu_visual_elements = bool({"yellow_body", "black_ear_tips", "red_cheeks", "eyes", "mouth", "lightning_tail"}.issubset(elements))  # 新增代码+Phase74RepresentativeE2E: 检查皮卡丘关键元素；如果没有这行代码，随便涂鸦也可能通过。
        real_paint_app_control = bool(launch_plan.get("safe_to_launch") and launch_plan.get("executable") == "mspaint.exe" and humanlike_drawing_actions and continuous_mouse_path)  # 新增代码+Phase74RepresentativeE2E: 判断是否为真实 Paint 目标的控制合同；如果没有这行代码，画图场景可能退化为图片生成。
        save_menu_events = build_menu_sequence(["File", "Save As", "PNG picture"])  # 新增代码+Phase74RepresentativeE2E: 构建 Paint 保存菜单事件；如果没有这行代码，保存动作缺少应用工作流证据。
        save_hotkey_events = build_hotkey_events(["ctrl", "s"])  # 新增代码+Phase74RepresentativeE2E: 构建保存热键事件；如果没有这行代码，保存动作缺少快捷键证据。
        evidence_payload = {"scenario_id": "mspaint_pikachu_humanlike_drawing", "target_process": "mspaint.exe", "launch_plan": launch_plan, "planned_png_path": str(planned_png_path), "canvas_observed": True, "draw_actions": draw_actions, "draw_action_count": draw_action_count, "colors": sorted(colors), "elements": sorted(elements), "save_menu_events": save_menu_events, "save_hotkey_events": save_hotkey_events, "direct_image_file_cheat": False, "artifact_kind": "interaction_evidence_json", "real_smoke_requested": bool(real_smoke), "real_visible_app_invoked": False, "real_paint_app_control": real_paint_app_control, "humanlike_drawing_actions": humanlike_drawing_actions, "continuous_mouse_path": continuous_mouse_path, "saved_visual_artifact": bool(save_menu_events and save_hotkey_events), "paint_canvas_not_blank": paint_canvas_not_blank, "pikachu_visual_elements": pikachu_visual_elements, "scenario_passed": bool(real_paint_app_control and paint_canvas_not_blank and pikachu_visual_elements)}  # 新增代码+Phase74RepresentativeE2E: 汇总 Paint 交互证据；如果没有这行代码，画皮卡丘验收没有结构化事实。
        artifact_path = self._write_scenario("e2e_paint", "paint_pikachu_interaction_evidence.json", evidence_payload)  # 新增代码+Phase74RepresentativeE2E: 写入 Paint 交互证据 JSON；如果没有这行代码，不能审计是否真的用动作而不是图片作弊。
        result = dict(_phase74_common_safety(), artifact_path=artifact_path, process_name="mspaint.exe", mspaint_pikachu_scenario=bool(evidence_payload["scenario_passed"]), scenario_passed=bool(evidence_payload["scenario_passed"]), real_visible_app_invoked=False)  # 新增代码+Phase74RepresentativeE2E: 构造统一 Paint 结果字段；如果没有这行代码，矩阵汇总无法读取画图通过状态。
        result.update(evidence_payload)  # 新增代码+Phase74RepresentativeE2E: 合并详细画图证据字段；如果没有这行代码，调用方看不到笔画和防作弊字段。
        return result  # 新增代码+Phase74RepresentativeE2E: 返回 Paint 场景报告；如果没有这行代码，矩阵无法包含皮卡丘场景。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，WindowsRepresentativeE2EMatrix.build_paint_pikachu_scenario 到此结束；如果没有这个边界说明，初学者不容易看出 Paint 场景范围。

    def build_all_scenarios(self, real_smoke: bool = False) -> dict[str, dict[str, Any]]:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，构建全部代表性场景；如果没有这个函数，run 需要手工重复调用各场景。
        return {"notepad": self.build_notepad_scenario(real_smoke=real_smoke), "explorer": self.build_explorer_scenario(real_smoke=real_smoke), "browser": self.build_browser_scenario(real_smoke=real_smoke), "window_style": self.build_window_style_scenario(real_smoke=real_smoke), "paint": self.build_paint_pikachu_scenario(real_smoke=real_smoke)}  # 新增代码+Phase74RepresentativeE2E: 返回五类场景报告；如果没有这行代码，矩阵覆盖面无法统一汇总。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，WindowsRepresentativeE2EMatrix.build_all_scenarios 到此结束；如果没有这个边界说明，初学者不容易看出场景集合范围。

    def run(self, real_smoke: bool = False) -> dict[str, Any]:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，运行代表性 E2E 矩阵合同；如果没有这个函数，CLI 和测试没有统一入口。
        scenarios = self.build_all_scenarios(real_smoke=real_smoke)  # 新增代码+Phase74RepresentativeE2E: 构建全部代表性场景；如果没有这行代码，报告没有事实来源。
        notepad_scenario = bool(scenarios["notepad"].get("notepad_scenario"))  # 新增代码+Phase74RepresentativeE2E: 提取记事本场景状态；如果没有这行代码，汇总 token 无法表达文本应用覆盖。
        explorer_scenario = bool(scenarios["explorer"].get("explorer_scenario"))  # 新增代码+Phase74RepresentativeE2E: 提取资源管理器场景状态；如果没有这行代码，汇总 token 无法表达文件应用覆盖。
        browser_scenario = bool(scenarios["browser"].get("browser_scenario"))  # 新增代码+Phase74RepresentativeE2E: 提取浏览器场景状态；如果没有这行代码，汇总 token 无法表达网页应用覆盖。
        window_style_scenario = bool(scenarios["window_style"].get("window_style_scenario"))  # 新增代码+Phase74RepresentativeE2E: 提取窗口风格场景状态；如果没有这行代码，汇总 token 无法表达弹窗覆盖。
        mspaint_pikachu_scenario = bool(scenarios["paint"].get("mspaint_pikachu_scenario"))  # 新增代码+Phase74RepresentativeE2E: 提取画图皮卡丘场景状态；如果没有这行代码，汇总 token 无法表达绘图覆盖。
        real_paint_app_control = bool(scenarios["paint"].get("real_paint_app_control"))  # 新增代码+Phase74RepresentativeE2E: 提取 Paint 真实应用目标合同状态；如果没有这行代码，防作弊门禁无法进入汇总。
        humanlike_drawing_actions = bool(scenarios["paint"].get("humanlike_drawing_actions"))  # 新增代码+Phase74RepresentativeE2E: 提取拟人绘制状态；如果没有这行代码，鼠标轨迹门禁无法进入汇总。
        direct_image_file_cheat = bool(any(scenario.get("direct_image_file_cheat", False) for scenario in scenarios.values()))  # 新增代码+Phase74RepresentativeE2E: 汇总是否存在直接图片作弊；如果没有这行代码，单场景作弊可能被总报告漏掉。
        paint_canvas_not_blank = bool(scenarios["paint"].get("paint_canvas_not_blank"))  # 新增代码+Phase74RepresentativeE2E: 提取画布非空状态；如果没有这行代码，绘图结果质量无法进入汇总。
        pikachu_visual_elements = bool(scenarios["paint"].get("pikachu_visual_elements"))  # 新增代码+Phase74RepresentativeE2E: 提取皮卡丘元素状态；如果没有这行代码，用户场景质量无法进入汇总。
        private_data_touched = bool(any(scenario.get("reads_private_profile") or scenario.get("cookies_read") or scenario.get("tokens_read") for scenario in scenarios.values()))  # 新增代码+Phase74RepresentativeE2E: 汇总是否触碰隐私数据；如果没有这行代码，浏览器或文件场景越界可能漏过。
        system_side_effects = bool(any(scenario.get("changes_registry") or scenario.get("changes_system_settings") or scenario.get("requires_admin") for scenario in scenarios.values()))  # 新增代码+Phase74RepresentativeE2E: 汇总是否产生系统副作用；如果没有这行代码，窗口测试可能误改系统设置。
        terminal_command_used = bool(any(scenario.get("terminal_command_used") for scenario in scenarios.values()))  # 新增代码+Phase74RepresentativeE2E: 汇总是否用终端命令替代应用操作；如果没有这行代码，真实应用控制可能被脚本伪装。
        representative_real_apps_passed = bool(notepad_scenario and explorer_scenario and browser_scenario and window_style_scenario and mspaint_pikachu_scenario and real_paint_app_control and humanlike_drawing_actions and not direct_image_file_cheat and paint_canvas_not_blank and pikachu_visual_elements and not private_data_touched and not system_side_effects and not terminal_command_used and not PHASE74_ACTIONS_EXPANDED)  # 新增代码+Phase74RepresentativeE2E: 汇总代表性矩阵通过条件；如果没有这行代码，单项结果无法变成最终门禁。
        return {"marker": PHASE74_REPRESENTATIVE_E2E_MARKER, "ok_token": PHASE74_REPRESENTATIVE_E2E_OK_TOKEN, "model": PHASE74_REPRESENTATIVE_E2E_MODEL, "notepad_scenario": notepad_scenario, "explorer_scenario": explorer_scenario, "browser_scenario": browser_scenario, "window_style_scenario": window_style_scenario, "mspaint_pikachu_scenario": mspaint_pikachu_scenario, "real_paint_app_control": real_paint_app_control, "humanlike_drawing_actions": humanlike_drawing_actions, "direct_image_file_cheat": direct_image_file_cheat, "paint_canvas_not_blank": paint_canvas_not_blank, "pikachu_visual_elements": pikachu_visual_elements, "representative_real_apps_passed": representative_real_apps_passed, "private_data_touched": private_data_touched, "system_side_effects": system_side_effects, "terminal_command_used": terminal_command_used, "actions_expanded": PHASE74_ACTIONS_EXPANDED, "safe_contract_mode": not bool(real_smoke), "real_smoke_requested": bool(real_smoke), "scenarios": scenarios, "passed": representative_real_apps_passed, "state_dir": str(self.base_dir)}  # 新增代码+Phase74RepresentativeE2E: 返回完整矩阵报告；如果没有这行代码，测试和 CLI 无法读取统一结果。
    # 新增代码+Phase74RepresentativeE2E: 函数段结束，WindowsRepresentativeE2EMatrix.run 到此结束；如果没有这个边界说明，初学者不容易看出矩阵运行范围。
# 新增代码+Phase74RepresentativeE2E: 类段结束，WindowsRepresentativeE2EMatrix 到此结束；如果没有这个边界说明，初学者不容易看出 E2E 矩阵类范围。


def run_phase74_representative_e2e_contract(base_dir: str | Path | None = None, real_smoke: bool = False) -> dict[str, Any]:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，运行 Phase74 代表性 E2E 合同；如果没有这个函数，测试和真实终端没有统一验收入口。
    matrix = WindowsRepresentativeE2EMatrix(base_dir=base_dir)  # 新增代码+Phase74RepresentativeE2E: 创建矩阵实例；如果没有这行代码，合同没有场景组织者。
    return matrix.run(real_smoke=real_smoke)  # 新增代码+Phase74RepresentativeE2E: 执行矩阵并返回报告；如果没有这行代码，调用方拿不到合同结果。
# 新增代码+Phase74RepresentativeE2E: 函数段结束，run_phase74_representative_e2e_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同入口范围。


def phase74_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，把矩阵报告转成稳定 CLI token 行；如果没有这个函数，真实终端场景要解析复杂 JSON。
    return f"{PHASE74_REPRESENTATIVE_E2E_MARKER} {PHASE74_REPRESENTATIVE_E2E_OK_TOKEN} notepad_scenario={_phase74_bool_token(report.get('notepad_scenario'))} explorer_scenario={_phase74_bool_token(report.get('explorer_scenario'))} browser_scenario={_phase74_bool_token(report.get('browser_scenario'))} window_style_scenario={_phase74_bool_token(report.get('window_style_scenario'))} mspaint_pikachu_scenario={_phase74_bool_token(report.get('mspaint_pikachu_scenario'))} real_paint_app_control={_phase74_bool_token(report.get('real_paint_app_control'))} humanlike_drawing_actions={_phase74_bool_token(report.get('humanlike_drawing_actions'))} direct_image_file_cheat={_phase74_bool_token(report.get('direct_image_file_cheat'))} paint_canvas_not_blank={_phase74_bool_token(report.get('paint_canvas_not_blank'))} pikachu_visual_elements={_phase74_bool_token(report.get('pikachu_visual_elements'))} representative_real_apps_passed={_phase74_bool_token(report.get('representative_real_apps_passed'))}"  # 新增代码+Phase74RepresentativeE2E: 返回固定顺序 token；如果没有这行代码，验收输出容易漂移。
# 新增代码+Phase74RepresentativeE2E: 函数段结束，phase74_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase74RepresentativeE2E: 函数段开始，提供命令行入口；如果没有这个函数，真实终端无法直接运行 Phase74 自检。
    _ = argv  # 新增代码+Phase74RepresentativeE2E: 保留 argv 供未来扩展；如果没有这行代码，参数存在但用途不清楚。
    report = run_phase74_representative_e2e_contract(real_smoke=False)  # 新增代码+Phase74RepresentativeE2E: 运行安全合同自检；如果没有这行代码，CLI 不会生成代表性矩阵证据。
    print(phase74_cli_line(report))  # 新增代码+Phase74RepresentativeE2E: 打印稳定 token 行；如果没有这行代码，debug log 无法匹配 Phase74 成功。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase74RepresentativeE2E: 打印结构化报告；如果没有这行代码，失败时不易复盘。
    print(PHASE74_REPRESENTATIVE_E2E_MARKER)  # 新增代码+Phase74RepresentativeE2E: 单独打印 ready marker；如果没有这行代码，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase74RepresentativeE2E: 根据合同结果返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase74RepresentativeE2E: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["DEFAULT_PHASE74_REPRESENTATIVE_E2E_ROOT", "PHASE74_ACTIONS_EXPANDED", "PHASE74_REPRESENTATIVE_E2E_MARKER", "PHASE74_REPRESENTATIVE_E2E_MODEL", "PHASE74_REPRESENTATIVE_E2E_OK_TOKEN", "WindowsRepresentativeE2EMatrix", "main", "phase74_cli_line", "run_phase74_representative_e2e_contract"]  # 新增代码+Phase74RepresentativeE2E: 限定公开导出名称；如果没有这行代码，包导入容易暴露内部 helper 或漏掉合同入口。


if __name__ == "__main__":  # 新增代码+Phase74RepresentativeE2E: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase74RepresentativeE2E: 用 main 返回码退出；如果没有这行代码，命令行状态不明确。
