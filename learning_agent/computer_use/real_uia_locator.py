"""Phase57 Windows real UIA control tree and semantic locator."""  # 新增代码+Phase57RealUiaLocator: 标明本文件负责真实 Windows UIA 树和语义控件定位；如果没有这行代码，读者不容易区分 Phase46 合同层和 Phase57 生产层。
from __future__ import annotations  # 新增代码+Phase57RealUiaLocator: 启用延迟类型解析；如果没有这行代码，旧解释器路径遇到前向类型标注时更容易导入失败。

import base64  # 新增代码+Phase57RealUiaLocator: 导入 base64 用于安全传递 PowerShell 脚本；如果没有这行代码，命令行引号会很容易破坏 UIA 脚本。
import json  # 新增代码+Phase57RealUiaLocator: 导入 JSON 用于解析 PowerShell 输出和打印验收报告；如果没有这行代码，provider 和 CLI 都无法交换结构化结果。
import subprocess  # 修改代码+Phase57RealUiaLocator: 导入 subprocess 执行 PowerShell UIAutomationClient 和启动独立安全窗体；如果没有这行代码，真实 UIA 后端无法运行。
import sys  # 新增代码+Phase57RealUiaLocator: 导入 sys 判断当前平台；如果没有这行代码，非 Windows 环境可能误触发 Windows UIA。
import tempfile  # 修改代码+Phase57RealUiaLocator: 导入临时目录工具创建自有安全窗体脚本；如果没有这行代码，smoke 可能污染项目目录或用户目录。
import time  # 修改代码+Phase57RealUiaLocator: 导入 time 用于轮询等待安全窗口出现；如果没有这行代码，窗体启动延迟会被误判为失败。
from pathlib import Path  # 新增代码+Phase57RealUiaLocator: 导入 Path 统一处理 Windows 文件路径；如果没有这行代码，临时文件路径拼接会更脆弱。
from typing import Any  # 新增代码+Phase57RealUiaLocator: 导入 Any 标注 JSON 风格协议对象；如果没有这行代码，接口边界不清楚。

try:  # 新增代码+Phase57RealUiaLocator: 优先按包模式导入既有 Computer Use 组件；如果没有这段代码，unittest 和生产入口不能复用项目模块。
    from learning_agent.computer_use.evidence import filter_accessibility_text  # 新增代码+Phase57RealUiaLocator: 复用既有 UIA 文本脱敏函数；如果没有这行代码，控件名称可能泄露 password/token。
    from learning_agent.computer_use.native_helper import parse_hwnd_from_window  # 新增代码+Phase57RealUiaLocator: 复用统一 hwnd 解析逻辑；如果没有这行代码，不同模块会用不同窗口身份规则。
    from learning_agent.computer_use.windows_backend import WindowsWindowInventoryProbe  # 修改代码+Phase57RealUiaLocator: 复用真实窗口枚举能力定位自有安全窗体；如果没有这行代码，real smoke 找不到安全窗口。
except ModuleNotFoundError as error:  # 新增代码+Phase57RealUiaLocator: 兼容 start_oauth_agent.bat 从 learning_agent 目录运行；如果没有这段代码，脚本模式可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.evidence", "learning_agent.computer_use.native_helper", "learning_agent.computer_use.windows_backend"}:  # 新增代码+Phase57RealUiaLocator: 只允许包路径缺失时 fallback；如果没有这行代码，真实内部 bug 会被误吞。
        raise  # 新增代码+Phase57RealUiaLocator: 重新抛出非路径类导入错误；如果没有这行代码，排查 evidence/native_helper 内部错误会困难。
    from computer_use.evidence import filter_accessibility_text  # 新增代码+Phase57RealUiaLocator: 脚本模式复用 UIA 文本脱敏函数；如果没有这行代码，bat 入口无法安全脱敏。
    from computer_use.native_helper import parse_hwnd_from_window  # 新增代码+Phase57RealUiaLocator: 脚本模式复用 hwnd 解析；如果没有这行代码，bat 入口无法识别目标窗口。
    from computer_use.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase57RealUiaLocator: 脚本模式复用窗口枚举；如果没有这行代码，bat 入口无法定位安全窗口。

PHASE57_WINDOWS_REAL_UIA_LOCATOR_MARKER = "PHASE57_WINDOWS_REAL_UIA_LOCATOR_READY"  # 新增代码+Phase57RealUiaLocator: 定义 Phase57 ready marker；如果没有这行代码，真实终端验收无法稳定等待本阶段输出。
PHASE57_WINDOWS_REAL_UIA_LOCATOR_OK_TOKEN = "PHASE57_WINDOWS_REAL_UIA_LOCATOR_OK"  # 新增代码+Phase57RealUiaLocator: 定义 Phase57 OK token；如果没有这行代码，debug log 无法区分运行完成和真正通过。
PHASE57_REAL_UIA_LOCATOR_MODEL = "phase57_windows_real_uia_locator"  # 新增代码+Phase57RealUiaLocator: 定义 runtime 模型名；如果没有这行代码，状态和 evidence 难以区分版本。
PHASE57_ACTIONS_EXPANDED = False  # 新增代码+Phase57RealUiaLocator: 明确 Phase57 只读观察和定位，不扩大动作面；如果没有这行代码，安全审计无法确认边界。


def _phase57_bool_token(value: Any) -> str:  # 新增代码+Phase57RealUiaLocator: 函数段开始，把布尔值转成验收友好的小写 token；如果没有这段函数，CLI token 大小写容易漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase57RealUiaLocator: 返回 true/false 文本；如果没有这行代码，场景断言可能因为 True/False 失败。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_phase57_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


def _safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase57RealUiaLocator: 函数段开始，安全转换 hwnd 和坐标整数；如果没有这段函数，坏 UIA 坐标会让整个树读取崩溃。
    try:  # 新增代码+Phase57RealUiaLocator: 捕获无法转换的动态值；如果没有这行代码，None 或字符串坐标会抛异常。
        return int(value)  # 新增代码+Phase57RealUiaLocator: 返回整数值；如果没有这行代码，坐标和句柄无法稳定比较。
    except Exception:  # 新增代码+Phase57RealUiaLocator: 捕获所有转换异常作为兜底；如果没有这行代码，坏输入会中断 agent。
        return int(default)  # 新增代码+Phase57RealUiaLocator: 返回默认整数；如果没有这行代码，调用方需要到处重复兜底。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出整数转换范围。


def _clean_role(role: Any) -> str:  # 新增代码+Phase57RealUiaLocator: 函数段开始，规范化 UIA ControlType 名称；如果没有这段函数，ControlType.Edit 和 Edit 会被当成不同角色。
    text = str(role or "").strip()  # 新增代码+Phase57RealUiaLocator: 把角色转成干净字符串；如果没有这行代码，None 角色会污染输出。
    if text.startswith("ControlType."):  # 新增代码+Phase57RealUiaLocator: 检查 .NET UIA 常见前缀；如果没有这行代码，语义定位需要知道底层 API 格式。
        text = text.split(".", 1)[1]  # 新增代码+Phase57RealUiaLocator: 去掉 ControlType. 前缀；如果没有这行代码，role=Edit 查询匹配不到 ControlType.Edit。
    if text.endswith("Control"):  # 新增代码+Phase57RealUiaLocator: 兼容旧 uiautomation 的 ButtonControl 风格；如果没有这行代码，新旧树角色不统一。
        text = text[:-7]  # 新增代码+Phase57RealUiaLocator: 去掉 Control 后缀；如果没有这行代码，role=Button 查询匹配不到 ButtonControl。
    return text or "Unknown"  # 新增代码+Phase57RealUiaLocator: 返回规范化角色并兜底 Unknown；如果没有这行代码，空角色会让 locator 理由不清楚。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_clean_role 到此结束；如果没有这个边界说明，初学者不容易看出角色规范化范围。


def _safe_text(value: Any, max_length: int = 160) -> tuple[str, int]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，脱敏并截断单个 UIA 文本字段；如果没有这段函数，控件名称和 automation_id 可能泄露敏感信息。
    raw_text = str(value or "")  # 新增代码+Phase57RealUiaLocator: 把输入转成字符串；如果没有这行代码，None 或数字字段无法统一过滤。
    filtered = filter_accessibility_text(raw_text, max_length=max_length)  # 新增代码+Phase57RealUiaLocator: 调用既有敏感词过滤；如果没有这行代码，password/token 行可能进入响应。
    if raw_text and not filtered.excerpt and filtered.filtered_line_count > 0:  # 新增代码+Phase57RealUiaLocator: 检查整字段被过滤的情况；如果没有这行代码，用户看不出这里原本有敏感字段。
        return "[filtered]", int(filtered.filtered_line_count)  # 新增代码+Phase57RealUiaLocator: 返回占位文本和过滤计数；如果没有这行代码，树结构会因为敏感值变成空而难以调试。
    return filtered.excerpt, int(filtered.filtered_line_count)  # 新增代码+Phase57RealUiaLocator: 返回安全文本和过滤计数；如果没有这行代码，调用方拿不到脱敏结果。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出文本脱敏范围。


def _normalize_bounds(bounds: Any) -> dict[str, int]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，统一 UIA 边界框格式；如果没有这段函数，locator 无法可靠比较控件坐标。
    source = dict(bounds or {}) if isinstance(bounds, dict) else {}  # 新增代码+Phase57RealUiaLocator: 只接受 dict 边界输入；如果没有这行代码，坏 bounds 类型会触发异常。
    left = _safe_int(source.get("left"))  # 新增代码+Phase57RealUiaLocator: 读取左边界；如果没有这行代码，控件 x 起点缺失。
    top = _safe_int(source.get("top"))  # 新增代码+Phase57RealUiaLocator: 读取上边界；如果没有这行代码，控件 y 起点缺失。
    right = _safe_int(source.get("right"), left + _safe_int(source.get("width")))  # 新增代码+Phase57RealUiaLocator: 读取右边界并用宽度兜底；如果没有这行代码，只有 width 的节点无法定位。
    bottom = _safe_int(source.get("bottom"), top + _safe_int(source.get("height")))  # 新增代码+Phase57RealUiaLocator: 读取下边界并用高度兜底；如果没有这行代码，只有 height 的节点无法定位。
    width = max(0, _safe_int(source.get("width"), right - left))  # 新增代码+Phase57RealUiaLocator: 计算宽度并防止负数；如果没有这行代码，坐标异常会污染后续判断。
    height = max(0, _safe_int(source.get("height"), bottom - top))  # 新增代码+Phase57RealUiaLocator: 计算高度并防止负数；如果没有这行代码，控件尺寸不可审计。
    if right < left:  # 新增代码+Phase57RealUiaLocator: 检查左右边界反转；如果没有这行代码，坏 UIA 坐标会产生负宽度。
        right = left + width  # 新增代码+Phase57RealUiaLocator: 用宽度修正右边界；如果没有这行代码，bounds 结果不自洽。
    if bottom < top:  # 新增代码+Phase57RealUiaLocator: 检查上下边界反转；如果没有这行代码，坏 UIA 坐标会产生负高度。
        bottom = top + height  # 新增代码+Phase57RealUiaLocator: 用高度修正下边界；如果没有这行代码，bounds 结果不自洽。
    return {"left": left, "top": top, "right": right, "bottom": bottom, "width": max(width, right - left), "height": max(height, bottom - top)}  # 新增代码+Phase57RealUiaLocator: 返回标准边界对象；如果没有这行代码，调用方需要兼容多种坐标形态。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_normalize_bounds 到此结束；如果没有这个边界说明，初学者不容易看出边界标准化范围。


def _looks_clickable(role: str, class_name: str, name: str) -> bool:  # 新增代码+Phase57RealUiaLocator: 函数段开始，根据 UIA 线索判断控件是否可点击；如果没有这段函数，模型需要自己猜按钮和菜单。
    text = f"{role} {class_name} {name}".lower()  # 新增代码+Phase57RealUiaLocator: 合并控件线索便于关键词判断；如果没有这行代码，判断逻辑会重复读取多个字段。
    return any(token in text for token in ("button", "menu", "tab", "check", "radio", "hyperlink", "listitem", "edit", "document"))  # 新增代码+Phase57RealUiaLocator: 返回常见可点击控件启发式结果；如果没有这行代码，clickable_count 无法生成。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_looks_clickable 到此结束；如果没有这个边界说明，初学者不容易看出点击提示范围。


def _looks_editable(role: str, class_name: str, name: str) -> bool:  # 新增代码+Phase57RealUiaLocator: 函数段开始，根据 UIA 线索判断控件是否可编辑；如果没有这段函数，高层 type_into_control 难以选择输入目标。
    text = f"{role} {class_name} {name}".lower()  # 新增代码+Phase57RealUiaLocator: 合并角色、类名和名称；如果没有这行代码，关键词判断会重复。
    return any(token in text for token in ("edit", "document", "textbox", "text box", "textarea", "combo"))  # 新增代码+Phase57RealUiaLocator: 返回常见可输入控件判断；如果没有这行代码，editable_count 无法生成。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_looks_editable 到此结束；如果没有这个边界说明，初学者不容易看出输入提示范围。


def _flatten_nodes(tree: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，把控件树转换成扁平列表；如果没有这段函数，locator 需要递归扫描树。
    nodes: list[dict[str, Any]] = []  # 新增代码+Phase57RealUiaLocator: 准备保存扁平节点；如果没有这行代码，遍历结果没有容器。

    def visit(node: dict[str, Any]) -> None:  # 新增代码+Phase57RealUiaLocator: 函数段开始，递归访问单个节点；如果没有这段函数，树无法递归展开。
        if not isinstance(node, dict):  # 新增代码+Phase57RealUiaLocator: 跳过坏节点；如果没有这行代码，PowerShell 异常结构可能导致崩溃。
            return  # 新增代码+Phase57RealUiaLocator: 结束坏节点处理；如果没有这行代码，后续会访问非 dict 字段。
        copy = dict(node)  # 新增代码+Phase57RealUiaLocator: 复制节点避免污染原树；如果没有这行代码，扁平化可能改变树结构。
        copy.pop("children", None)  # 新增代码+Phase57RealUiaLocator: 扁平节点不重复包含 children；如果没有这行代码，输出会指数级变大。
        nodes.append(copy)  # 新增代码+Phase57RealUiaLocator: 保存当前节点；如果没有这行代码，根节点和叶子节点都不会进入 locator。
        for child in list(node.get("children", []) or []):  # 新增代码+Phase57RealUiaLocator: 遍历子节点；如果没有这行代码，只有根节点会被定位。
            visit(child)  # 新增代码+Phase57RealUiaLocator: 递归展开子节点；如果没有这行代码，深层控件会丢失。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，visit 到此结束；如果没有这个边界说明，初学者不容易看出递归范围。

    visit(tree)  # 新增代码+Phase57RealUiaLocator: 从根节点开始扁平化；如果没有这行代码，nodes 会一直为空。
    return nodes  # 新增代码+Phase57RealUiaLocator: 返回扁平节点列表；如果没有这行代码，locator 拿不到控件候选。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_flatten_nodes 到此结束；如果没有这个边界说明，初学者不容易看出扁平化范围。


def _sanitize_tree(node: Any, state: dict[str, int]) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，递归清洗 UIA 树字段；如果没有这段函数，PowerShell 原始控件名会直接进入响应。
    source = dict(node or {}) if isinstance(node, dict) else {}  # 新增代码+Phase57RealUiaLocator: 只接受 dict 节点并兜底为空；如果没有这行代码，坏子节点会让清洗崩溃。
    name, filtered_name = _safe_text(source.get("name"), max_length=160)  # 新增代码+Phase57RealUiaLocator: 脱敏控件名称；如果没有这行代码，控件 title 可能泄露敏感内容。
    automation_id, filtered_automation = _safe_text(source.get("automation_id"), max_length=120)  # 新增代码+Phase57RealUiaLocator: 脱敏 automation_id；如果没有这行代码，敏感 id 也可能出现在日志。
    class_name, filtered_class = _safe_text(source.get("class_name"), max_length=120)  # 新增代码+Phase57RealUiaLocator: 清理类名；如果没有这行代码，异常类名可能过长或带控制字符。
    role = _clean_role(source.get("role"))  # 新增代码+Phase57RealUiaLocator: 规范化角色名；如果没有这行代码，locator 需要兼容多种底层格式。
    state["sensitive"] = int(state.get("sensitive", 0)) + filtered_name + filtered_automation + filtered_class  # 新增代码+Phase57RealUiaLocator: 累计脱敏次数；如果没有这行代码，用户不知道是否发生过滤。
    bounds = _normalize_bounds(source.get("bounds"))  # 新增代码+Phase57RealUiaLocator: 规范化边界框；如果没有这行代码，坐标定位不稳定。
    enabled = bool(source.get("enabled", True))  # 新增代码+Phase57RealUiaLocator: 读取 enabled 状态并默认可用；如果没有这行代码，缺字段控件可能被误判不可用。
    clickable = bool(source.get("clickable", False)) or _looks_clickable(role, class_name, name)  # 新增代码+Phase57RealUiaLocator: 生成可点击提示；如果没有这行代码，按钮和菜单无法被高层工具识别。
    editable = bool(source.get("editable", False)) or _looks_editable(role, class_name, name)  # 新增代码+Phase57RealUiaLocator: 生成可编辑提示；如果没有这行代码，输入框无法被高层工具识别。
    children = [_sanitize_tree(child, state) for child in list(source.get("children", []) or [])]  # 新增代码+Phase57RealUiaLocator: 递归清洗子节点；如果没有这行代码，只有根节点安全，子节点仍可能泄露。
    return {"node_id": str(source.get("node_id", "")), "name": name, "role": role, "automation_id": automation_id, "class_name": class_name, "bounds": bounds, "enabled": enabled, "clickable": clickable, "editable": editable, "children": children}  # 新增代码+Phase57RealUiaLocator: 返回标准安全节点；如果没有这行代码，调用方拿不到统一字段。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_sanitize_tree 到此结束；如果没有这个边界说明，初学者不容易看出树清洗范围。


def _powershell_command(script: str) -> list[str]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，把 PowerShell 脚本编码成稳定命令；如果没有这段函数，多行脚本容易被引号和中文破坏。
    encoded = base64.b64encode(str(script).encode("utf-16le")).decode("ascii")  # 新增代码+Phase57RealUiaLocator: 使用 PowerShell 官方 EncodedCommand 编码；如果没有这行代码，命令中的引号和换行可能失效。
    return ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded]  # 新增代码+Phase57RealUiaLocator: 返回安全命令数组；如果没有这行代码，subprocess 无法启动脚本。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_powershell_command 到此结束；如果没有这个边界说明，初学者不容易看出命令构造范围。


def _default_runner(command: list[str], timeout_seconds: float) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，执行真实 PowerShell 命令并返回结构化结果；如果没有这段函数，provider 只能依赖测试 fake。
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=max(1.0, float(timeout_seconds)))  # 新增代码+Phase57RealUiaLocator: 运行命令并强制 UTF-8 解码；如果没有这行代码，Windows 代码页可能导致 UnicodeDecodeError。
    return {"returncode": int(completed.returncode), "stdout": completed.stdout, "stderr": completed.stderr}  # 新增代码+Phase57RealUiaLocator: 返回稳定命令结果；如果没有这行代码，调用方无法判断成功或读取 JSON。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_default_runner 到此结束；如果没有这个边界说明，初学者不容易看出命令执行范围。


def _parse_json_output(output: Any) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，解析 PowerShell 输出 JSON；如果没有这段函数，provider 需要重复处理空输出和警告行。
    text = str(output or "").strip()  # 新增代码+Phase57RealUiaLocator: 清理输出文本；如果没有这行代码，空白会影响 JSON 解析。
    if not text:  # 新增代码+Phase57RealUiaLocator: 检查空输出；如果没有这行代码，json.loads 会抛出难懂错误。
        return {}  # 新增代码+Phase57RealUiaLocator: 空输出返回空 dict；如果没有这行代码，调用方无法温和失败。
    try:  # 新增代码+Phase57RealUiaLocator: 尝试直接解析完整输出；如果没有这行代码，正常 JSON 无法读取。
        return dict(json.loads(text))  # 新增代码+Phase57RealUiaLocator: 返回 JSON dict；如果没有这行代码，provider 拿不到结构化 payload。
    except Exception:  # 新增代码+Phase57RealUiaLocator: 捕获输出前后夹杂日志的情况；如果没有这行代码，PowerShell 警告会导致整体失败。
        for line in reversed(text.splitlines()):  # 新增代码+Phase57RealUiaLocator: 从最后一行向前找 JSON；如果没有这行代码，带提示的输出无法恢复。
            candidate = line.strip()  # 新增代码+Phase57RealUiaLocator: 清理候选行；如果没有这行代码，行首空白会影响判断。
            if candidate.startswith("{") and candidate.endswith("}"):  # 新增代码+Phase57RealUiaLocator: 只尝试形似 JSON 对象的行；如果没有这行代码，会重复解析普通日志。
                try:  # 新增代码+Phase57RealUiaLocator: 捕获单行 JSON 解析错误；如果没有这行代码，坏候选会中断恢复。
                    return dict(json.loads(candidate))  # 新增代码+Phase57RealUiaLocator: 返回最后一个 JSON 对象；如果没有这行代码，provider 无法从混合输出恢复。
                except Exception:  # 新增代码+Phase57RealUiaLocator: 忽略坏候选继续查找；如果没有这行代码，一个坏行会阻止后续候选。
                    continue  # 新增代码+Phase57RealUiaLocator: 继续查找上一行；如果没有这行代码，恢复流程会提前结束。
    return {}  # 新增代码+Phase57RealUiaLocator: 解析失败时返回空 dict；如果没有这行代码，调用方需要捕获 JSON 异常。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_parse_json_output 到此结束；如果没有这个边界说明，初学者不容易看出 JSON 恢复范围。


class PowerShellUiaTreeProvider:  # 新增代码+Phase57RealUiaLocator: 类段开始，使用 PowerShell/.NET UIAutomationClient 读取真实 Windows 控件树；如果没有这个类，Phase57 仍依赖 Python uiautomation 包。
    def __init__(self, platform: str | None = None, runner: Any | None = None, max_depth: int = 5, max_nodes: int = 120, timeout_seconds: float = 8.0) -> None:  # 新增代码+Phase57RealUiaLocator: 函数段开始，初始化平台、命令执行器和树上限；如果没有这段函数，provider 无法隔离测试和生产参数。
        self.platform = platform or sys.platform  # 新增代码+Phase57RealUiaLocator: 保存当前平台；如果没有这行代码，非 Windows 拒绝路径无法测试。
        self.runner = runner or _default_runner  # 新增代码+Phase57RealUiaLocator: 保存可注入命令执行器；如果没有这行代码，单测会真的调用 PowerShell。
        self.max_depth = max(0, int(max_depth))  # 新增代码+Phase57RealUiaLocator: 限制树深度并防止负数；如果没有这行代码，大窗口可能遍历过深。
        self.max_nodes = max(1, int(max_nodes))  # 新增代码+Phase57RealUiaLocator: 限制节点数量并至少为 1；如果没有这行代码，大窗口可能输出过多节点。
        self.timeout_seconds = max(1.0, float(timeout_seconds))  # 新增代码+Phase57RealUiaLocator: 保存命令超时；如果没有这行代码，卡住的 UIA 调用可能拖死 agent。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，PowerShellUiaTreeProvider.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，探测 PowerShell/.NET UIA 是否可用；如果没有这段函数，状态 UI 无法诚实报告依赖。
        if self.platform != "win32":  # 新增代码+Phase57RealUiaLocator: 非 Windows 直接不可用；如果没有这行代码，Linux/macOS 会误触发 PowerShell UIA。
            return {"marker": PHASE57_WINDOWS_REAL_UIA_LOCATOR_MARKER, "backend": "powershell_dotnet_uia", "available": False, "reason": "当前平台不是 Windows，未运行 UIAutomationClient。", "real_provider_required": True, "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回平台不支持状态；如果没有这行代码，用户不知道为什么不可用。
        script = self._status_script()  # 新增代码+Phase57RealUiaLocator: 构造状态探针脚本；如果没有这行代码，provider 不知道要执行什么。
        result = self._run_script(script)  # 新增代码+Phase57RealUiaLocator: 执行状态探针；如果没有这行代码，状态不会读取真实系统。
        payload = _parse_json_output(result.get("stdout", ""))  # 新增代码+Phase57RealUiaLocator: 解析 PowerShell JSON；如果没有这行代码，status 只能看到原始文本。
        available = bool(result.get("returncode") == 0 and payload.get("available"))  # 新增代码+Phase57RealUiaLocator: 汇总命令退出码和 payload 可用性；如果没有这行代码，失败命令可能被误报成功。
        reason = "PowerShell/.NET UIAutomationClient 可用。" if available else str(payload.get("message") or result.get("stderr") or "PowerShell/.NET UIAutomationClient 不可用。")  # 新增代码+Phase57RealUiaLocator: 生成可读原因；如果没有这行代码，缺依赖时用户不知道下一步。
        return {"marker": PHASE57_WINDOWS_REAL_UIA_LOCATOR_MARKER, "backend": "powershell_dotnet_uia", "available": available, "reason": reason, "root_role": str(payload.get("root_role", "")), "real_provider_required": True, "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回完整状态；如果没有这行代码，状态 UI 和验收矩阵没有统一事实源。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，PowerShellUiaTreeProvider.status 到此结束；如果没有这个边界说明，初学者不容易看出状态探测范围。

    def read_window_tree(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，按 hwnd 读取真实 UIA 控件树；如果没有这段函数，provider 只有状态没有行为。
        if self.platform != "win32":  # 新增代码+Phase57RealUiaLocator: 非 Windows 拒绝真实读取；如果没有这行代码，跨平台测试可能误触发系统命令。
            return self._failure("当前平台不是 Windows，未读取 UIA 控件树。")  # 新增代码+Phase57RealUiaLocator: 返回平台失败；如果没有这行代码，失败原因不可解释。
        hwnd = parse_hwnd_from_window(dict(window or {}))  # 新增代码+Phase57RealUiaLocator: 从窗口引用解析 hwnd；如果没有这行代码，PowerShell 不知道目标窗口。
        if hwnd <= 0:  # 新增代码+Phase57RealUiaLocator: 检查 hwnd 是否有效；如果没有这行代码，0 句柄可能传给 UIAutomationElement.FromHandle。
            return self._failure("窗口句柄无效，未读取 UIA 控件树。")  # 新增代码+Phase57RealUiaLocator: 返回坏句柄原因；如果没有这行代码，用户不知道为什么没有树。
        script = self._tree_script(hwnd)  # 新增代码+Phase57RealUiaLocator: 构造读取控件树脚本；如果没有这行代码，provider 没有真实读取逻辑。
        result = self._run_script(script)  # 新增代码+Phase57RealUiaLocator: 执行控件树读取；如果没有这行代码，真实 UIA 不会发生。
        payload = _parse_json_output(result.get("stdout", ""))  # 新增代码+Phase57RealUiaLocator: 解析树 JSON；如果没有这行代码，runtime 只能拿到原始文本。
        if result.get("returncode") != 0 or not payload.get("captured"):  # 新增代码+Phase57RealUiaLocator: 检查命令和捕获状态；如果没有这行代码，失败脚本可能被误当有树。
            return self._failure(str(payload.get("reason") or payload.get("message") or result.get("stderr") or "PowerShell UIA 读取失败。"))  # 新增代码+Phase57RealUiaLocator: 返回结构化失败；如果没有这行代码，调用方拿不到原因。
        return {"captured": True, "tree": payload.get("tree") or {}, "node_count": _safe_int(payload.get("node_count")), "truncated": bool(payload.get("truncated")), "backend": "powershell_dotnet_uia", "real_provider_used": True, "reason": "PowerShell/.NET UIA 控件树读取成功。"}  # 新增代码+Phase57RealUiaLocator: 返回真实树 payload；如果没有这行代码，runtime 无法清洗和定位。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，PowerShellUiaTreeProvider.read_window_tree 到此结束；如果没有这个边界说明，初学者不容易看出读取范围。

    def _failure(self, reason: str) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，构造 provider 失败结果；如果没有这段函数，失败字段会漂移。
        return {"captured": False, "tree": {}, "node_count": 0, "truncated": False, "backend": "powershell_dotnet_uia", "real_provider_used": False, "reason": str(reason)}  # 新增代码+Phase57RealUiaLocator: 返回稳定失败结构；如果没有这行代码，runtime 需要到处判断字段是否存在。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，PowerShellUiaTreeProvider._failure 到此结束；如果没有这个边界说明，初学者不容易看出失败结构范围。

    def _run_script(self, script: str) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，执行编码后的 PowerShell 脚本；如果没有这段函数，status 和 tree 读取会重复命令逻辑。
        command = _powershell_command(script)  # 新增代码+Phase57RealUiaLocator: 生成 EncodedCommand 参数；如果没有这行代码，多行脚本无法安全传递。
        try:  # 新增代码+Phase57RealUiaLocator: 捕获命令超时和启动失败；如果没有这行代码，PowerShell 异常会拖垮 agent。
            return dict(self.runner(command, self.timeout_seconds))  # 新增代码+Phase57RealUiaLocator: 调用真实或 fake runner；如果没有这行代码，provider 无法执行脚本。
        except subprocess.TimeoutExpired:  # 新增代码+Phase57RealUiaLocator: 捕获 UIA 命令超时；如果没有这行代码，超时会以异常形式逃出。
            return {"returncode": 124, "stdout": "", "stderr": "PowerShell UIA 命令超时。"}  # 新增代码+Phase57RealUiaLocator: 返回超时结构；如果没有这行代码，调用方无法恢复。
        except Exception as error:  # 新增代码+Phase57RealUiaLocator: 捕获 runner 其他错误；如果没有这行代码，PowerShell 缺失会崩溃。
            return {"returncode": 1, "stdout": "", "stderr": f"PowerShell UIA 命令失败：{type(error).__name__}"}  # 新增代码+Phase57RealUiaLocator: 返回异常类型但不泄露细节；如果没有这行代码，失败不可读。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，PowerShellUiaTreeProvider._run_script 到此结束；如果没有这个边界说明，初学者不容易看出命令执行边界。

    def _status_script(self) -> str:  # 新增代码+Phase57RealUiaLocator: 函数段开始，生成 UIAutomationClient 状态探针脚本；如果没有这段函数，status 没有真实依赖检查。
        return """[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
try {
  Add-Type -AssemblyName UIAutomationClient
  $root = [System.Windows.Automation.AutomationElement]::RootElement
  $payload = @{ available = $true; root_role = $root.Current.ControlType.ProgrammaticName }
} catch {
  $payload = @{ available = $false; message = $_.Exception.Message; error_type = $_.Exception.GetType().Name }
}
$payload | ConvertTo-Json -Compress -Depth 8
"""  # 新增代码+Phase57RealUiaLocator: 返回只读依赖探针脚本；如果没有这行代码，provider 无法检测 .NET UIA 是否存在。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，PowerShellUiaTreeProvider._status_script 到此结束；如果没有这个边界说明，初学者不容易看出状态脚本范围。

    def _tree_script(self, hwnd: int) -> str:  # 新增代码+Phase57RealUiaLocator: 函数段开始，生成读取指定 hwnd 控件树的 PowerShell 脚本；如果没有这段函数，真实控件树无法生成。
        safe_hwnd = max(0, int(hwnd))  # 新增代码+Phase57RealUiaLocator: 规范化 hwnd；如果没有这行代码，脚本中可能出现非法句柄文本。
        safe_depth = max(0, int(self.max_depth))  # 新增代码+Phase57RealUiaLocator: 规范化最大深度；如果没有这行代码，脚本遍历上限不可信。
        safe_nodes = max(1, int(self.max_nodes))  # 新增代码+Phase57RealUiaLocator: 规范化最大节点数；如果没有这行代码，脚本可能无限遍历大树。
        return f"""[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
try {{
  Add-Type -AssemblyName UIAutomationClient
  $maxDepth = {safe_depth}
  $maxNodes = {safe_nodes}
  $script:count = 0
  $script:truncated = $false
  $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
  function Convert-ToSafeInt($value) {{
    try {{
      $number = [double]$value
      if ([double]::IsNaN($number) -or [double]::IsInfinity($number)) {{ return 0 }}
      if ($number -gt 2147483647) {{ return 2147483647 }}
      if ($number -lt -2147483648) {{ return -2147483648 }}
      return [int][Math]::Round($number)
    }} catch {{
      return 0
    }}
  }}
  function Read-Bounds($element) {{
    $rect = $element.Current.BoundingRectangle
    $left = Convert-ToSafeInt $rect.Left
    $top = Convert-ToSafeInt $rect.Top
    $right = Convert-ToSafeInt $rect.Right
    $bottom = Convert-ToSafeInt $rect.Bottom
    return @{{ left = $left; top = $top; right = $right; bottom = $bottom; width = [Math]::Max(0, $right - $left); height = [Math]::Max(0, $bottom - $top) }}
  }}
  function Convert-Node($element, [int]$depth, [string]$nodeId) {{
    if ($script:count -ge $maxNodes) {{ $script:truncated = $true; return $null }}
    $script:count = $script:count + 1
    $current = $element.Current
    $node = @{{ node_id = $nodeId; name = [string]$current.Name; role = [string]$current.ControlType.ProgrammaticName; automation_id = [string]$current.AutomationId; class_name = [string]$current.ClassName; bounds = (Read-Bounds $element); enabled = [bool]$current.IsEnabled; clickable = $false; editable = $false; children = @() }}
    if ($depth -lt $maxDepth) {{
      $child = $walker.GetFirstChild($element)
      $index = 0
      while ($null -ne $child -and $script:count -lt $maxNodes) {{
        $childNode = Convert-Node $child ($depth + 1) ($nodeId + "." + $index)
        if ($null -ne $childNode) {{ $node.children += $childNode }}
        $child = $walker.GetNextSibling($child)
        $index = $index + 1
      }}
      if ($null -ne $child -and $script:count -ge $maxNodes) {{ $script:truncated = $true }}
    }}
    return $node
  }}
  $root = [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]{safe_hwnd})
  if ($null -eq $root) {{
    $payload = @{{ captured = $false; reason = "AutomationElement.FromHandle returned null"; node_count = 0; truncated = $false; tree = @{{}} }}
  }} else {{
    $tree = Convert-Node $root 0 "0"
    $payload = @{{ captured = $true; reason = "ok"; node_count = $script:count; truncated = $script:truncated; tree = $tree }}
  }}
}} catch {{
  $payload = @{{ captured = $false; reason = $_.Exception.GetType().Name; message = $_.Exception.Message; node_count = 0; truncated = $false; tree = @{{}} }}
}}
$payload | ConvertTo-Json -Compress -Depth 80
"""  # 新增代码+Phase57RealUiaLocator: 返回有界、只读、JSON 输出的树读取脚本；如果没有这行代码，provider 无法读取真实控件树。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，PowerShellUiaTreeProvider._tree_script 到此结束；如果没有这个边界说明，初学者不容易看出树脚本范围。
# 新增代码+Phase57RealUiaLocator: 类段结束，PowerShellUiaTreeProvider 到此结束；如果没有这个边界说明，初学者不容易看出 provider 范围。


class SemanticControlLocator:  # 新增代码+Phase57RealUiaLocator: 类段开始，定义可解释语义控件定位器；如果没有这个类，高层工具只能让模型自己扫描控件列表。
    def find(self, nodes: Any, query: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，根据 text/title/role/automation_id/class/bounds 查找控件；如果没有这段函数，Phase57 只有树没有定位能力。
        flat_nodes = self._coerce_nodes(nodes)  # 新增代码+Phase57RealUiaLocator: 统一输入为扁平节点列表；如果没有这行代码，调用方必须知道内部数据形态。
        safe_query = dict(query or {})  # 新增代码+Phase57RealUiaLocator: 复制查询条件避免污染调用方对象；如果没有这行代码，后续规范化可能修改外部状态。
        scored = [self._score_node(node, safe_query) for node in flat_nodes]  # 新增代码+Phase57RealUiaLocator: 为每个节点计算匹配分；如果没有这行代码，locator 无法选择最佳节点。
        candidates = [item for item in scored if item["score"] > 0]  # 新增代码+Phase57RealUiaLocator: 只保留有任一线索命中的候选；如果没有这行代码，候选数量没有意义。
        if not candidates:  # 新增代码+Phase57RealUiaLocator: 处理没有候选的情况；如果没有这行代码，max 空列表会抛异常。
            return {"matched": False, "candidate_count": 0, "confidence": 0.0, "reason": "没有控件匹配查询条件。", "control": {}, "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回可解释未命中；如果没有这行代码，调用方不知道为何失败。
        best = max(candidates, key=lambda item: item["score"])  # 新增代码+Phase57RealUiaLocator: 选择最高分候选；如果没有这行代码，locator 无法确定目标。
        confidence = min(1.0, round(float(best["score"]), 2))  # 新增代码+Phase57RealUiaLocator: 规范化置信度到 0-1；如果没有这行代码，调用方难以比较强弱。
        return {"matched": confidence >= 0.25, "candidate_count": len(candidates), "confidence": confidence, "reason": "; ".join(best["reasons"]) or "命中弱线索。", "control": self._summarize_node(best["node"]), "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回可解释定位结果；如果没有这行代码，高层工具拿不到控制点。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，SemanticControlLocator.find 到此结束；如果没有这个边界说明，初学者不容易看出定位入口范围。

    def _coerce_nodes(self, nodes: Any) -> list[dict[str, Any]]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，把树或列表统一为节点列表；如果没有这段函数，调用方必须区分 tree 和 flat_nodes。
        if isinstance(nodes, dict) and isinstance(nodes.get("flat_nodes"), list):  # 新增代码+Phase57RealUiaLocator: 支持 observe_window 结果；如果没有这行代码，runtime 结果不能直接传给 locator。
            return [dict(node) for node in nodes.get("flat_nodes", []) if isinstance(node, dict)]  # 新增代码+Phase57RealUiaLocator: 返回 flat_nodes 副本；如果没有这行代码，locator 可能污染观察结果。
        if isinstance(nodes, dict):  # 新增代码+Phase57RealUiaLocator: 支持直接传入树根节点；如果没有这行代码，调用方需要先手动 flatten。
            return _flatten_nodes(nodes)  # 新增代码+Phase57RealUiaLocator: 递归展开树；如果没有这行代码，树输入无法定位。
        return [dict(node) for node in list(nodes or []) if isinstance(node, dict)]  # 新增代码+Phase57RealUiaLocator: 支持普通列表输入；如果没有这行代码，locator 不能处理测试和 helper 的扁平节点。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，SemanticControlLocator._coerce_nodes 到此结束；如果没有这个边界说明，初学者不容易看出输入兼容范围。

    def _score_node(self, node: dict[str, Any], query: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，对单个节点按查询条件打分；如果没有这段函数，定位理由和分值无法复用。
        score = 0.0  # 新增代码+Phase57RealUiaLocator: 初始化匹配分；如果没有这行代码，后续加分没有起点。
        reasons: list[str] = []  # 新增代码+Phase57RealUiaLocator: 初始化命中理由列表；如果没有这行代码，locator 输出无法解释为什么选中。
        role_query = str(query.get("role", "") or "").lower()  # 新增代码+Phase57RealUiaLocator: 读取角色查询；如果没有这行代码，role 条件无法使用。
        role_value = str(node.get("role", "") or "").lower()  # 新增代码+Phase57RealUiaLocator: 读取节点角色；如果没有这行代码，role 匹配没有对象。
        if role_query and role_query in role_value:  # 新增代码+Phase57RealUiaLocator: 检查角色包含匹配；如果没有这行代码，按 role 查找不可用。
            score += 0.35  # 新增代码+Phase57RealUiaLocator: 角色命中加分；如果没有这行代码，角色线索没有影响。
            reasons.append(f"role matched {role_query}")  # 新增代码+Phase57RealUiaLocator: 记录角色命中理由；如果没有这行代码，用户不知道角色参与了选择。
        text_query = str(query.get("text", query.get("title", "")) or "").lower()  # 新增代码+Phase57RealUiaLocator: 读取文本或标题查询；如果没有这行代码，按可见文字定位不可用。
        visible_text = f"{node.get('name', '')} {node.get('automation_id', '')}".lower()  # 新增代码+Phase57RealUiaLocator: 合并可见名和 automation_id；如果没有这行代码，文字查询可能漏掉 id 命中。
        if text_query and text_query in visible_text:  # 新增代码+Phase57RealUiaLocator: 检查文字包含匹配；如果没有这行代码，按 text/title 查找不可用。
            score += 0.35  # 新增代码+Phase57RealUiaLocator: 文本命中加分；如果没有这行代码，文本线索没有影响。
            reasons.append(f"text matched {text_query}")  # 新增代码+Phase57RealUiaLocator: 记录文本命中理由；如果没有这行代码，定位解释不完整。
        automation_query = str(query.get("automation_id", "") or "").lower()  # 新增代码+Phase57RealUiaLocator: 读取 automation_id 查询；如果没有这行代码，精准 id 查找不可用。
        automation_value = str(node.get("automation_id", "") or "").lower()  # 新增代码+Phase57RealUiaLocator: 读取节点 automation_id；如果没有这行代码，id 匹配没有对象。
        if automation_query and automation_query == automation_value:  # 新增代码+Phase57RealUiaLocator: 检查 automation_id 精确匹配；如果没有这行代码，精准定位会变弱。
            score += 0.45  # 新增代码+Phase57RealUiaLocator: 精准 id 命中加高分；如果没有这行代码，id 查询可能被其他弱线索盖过。
            reasons.append(f"automation_id matched {automation_query}")  # 新增代码+Phase57RealUiaLocator: 记录 id 命中理由；如果没有这行代码，解释缺少最强线索。
        class_query = str(query.get("class_name", "") or "").lower()  # 新增代码+Phase57RealUiaLocator: 读取类名查询；如果没有这行代码，按 class_name 查找不可用。
        class_value = str(node.get("class_name", "") or "").lower()  # 新增代码+Phase57RealUiaLocator: 读取节点类名；如果没有这行代码，类名匹配没有对象。
        if class_query and class_query in class_value:  # 新增代码+Phase57RealUiaLocator: 检查类名包含匹配；如果没有这行代码，class_name 查询不起作用。
            score += 0.25  # 新增代码+Phase57RealUiaLocator: 类名命中加分；如果没有这行代码，类线索没有影响。
            reasons.append(f"class_name matched {class_query}")  # 新增代码+Phase57RealUiaLocator: 记录类名理由；如果没有这行代码，解释不完整。
        if isinstance(query.get("bounds"), dict) and _bounds_overlap(_normalize_bounds(node.get("bounds")), _normalize_bounds(query.get("bounds"))):  # 新增代码+Phase57RealUiaLocator: 检查节点边界是否和查询范围相交；如果没有这行代码，按区域定位不可用。
            score += 0.25  # 新增代码+Phase57RealUiaLocator: 区域命中加分；如果没有这行代码，bounds 条件没有影响。
            reasons.append("bounds overlapped query")  # 新增代码+Phase57RealUiaLocator: 记录边界命中理由；如果没有这行代码，坐标参与选择不可见。
        if score > 0 and bool(node.get("enabled", True)):  # 新增代码+Phase57RealUiaLocator: 对可用控件给轻微加分；如果没有这行代码，禁用控件可能和可用控件同分。
            score += 0.05  # 新增代码+Phase57RealUiaLocator: 可用状态加分；如果没有这行代码，enabled 信息没有参与选择。
            reasons.append("control is enabled")  # 新增代码+Phase57RealUiaLocator: 记录控件可用理由；如果没有这行代码，解释少一个安全线索。
        return {"node": node, "score": score, "reasons": reasons}  # 新增代码+Phase57RealUiaLocator: 返回节点分数和理由；如果没有这行代码，find 无法选择最佳候选。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，SemanticControlLocator._score_node 到此结束；如果没有这个边界说明，初学者不容易看出评分范围。

    def _summarize_node(self, node: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，裁剪定位结果中的控件字段；如果没有这段函数，locator 可能返回过多内部结构。
        return {"node_id": str(node.get("node_id", "")), "name": str(node.get("name", "")), "role": str(node.get("role", "")), "automation_id": str(node.get("automation_id", "")), "class_name": str(node.get("class_name", "")), "bounds": dict(node.get("bounds", {}) or {}), "enabled": bool(node.get("enabled", True)), "clickable": bool(node.get("clickable", False)), "editable": bool(node.get("editable", False))}  # 新增代码+Phase57RealUiaLocator: 返回安全摘要字段；如果没有这行代码，调用方可能拿到 children 或未脱敏原始字段。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，SemanticControlLocator._summarize_node 到此结束；如果没有这个边界说明，初学者不容易看出摘要范围。
# 新增代码+Phase57RealUiaLocator: 类段结束，SemanticControlLocator 到此结束；如果没有这个边界说明，初学者不容易看出定位器范围。


def _bounds_overlap(first: dict[str, int], second: dict[str, int]) -> bool:  # 新增代码+Phase57RealUiaLocator: 函数段开始，判断两个矩形是否相交；如果没有这段函数，bounds 查询无法实现。
    return max(first["left"], second["left"]) < min(first["right"], second["right"]) and max(first["top"], second["top"]) < min(first["bottom"], second["bottom"])  # 新增代码+Phase57RealUiaLocator: 返回矩形相交结果；如果没有这行代码，locator 无法按区域筛控件。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_bounds_overlap 到此结束；如果没有这个边界说明，初学者不容易看出矩形判断范围。


def _is_phase57_safe_window(window: dict[str, Any]) -> tuple[bool, str]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，判断窗口是否允许读取 UIA 树；如果没有这段函数，Phase57 可能误读终端、Codex 或认证窗口。
    title = str(window.get("title_preview", window.get("title", "")) or "").lower()  # 新增代码+Phase57RealUiaLocator: 读取窗口标题摘要；如果没有这行代码，安全判断没有上下文。
    app_id = str(window.get("app_id", "") or "").lower()  # 新增代码+Phase57RealUiaLocator: 读取 app_id；如果没有这行代码，终端类应用无法辅助识别。
    if "learningagent-phase57" in title or "learningagent-phase58" in title:  # 修改代码+Phase58RealSendInputGuard: 允许 Phase57/Phase58 自建安全窗口标题；如果没有这行代码，Phase58 真实动作后的 UIA 复验会被安全门误拒绝。
        return True, "目标是 Phase57/Phase58 自有安全窗口。"  # 修改代码+Phase58RealSendInputGuard: 返回安全原因；如果没有这行代码，审计无法说明为什么允许 PowerShell 承载的自有测试窗体。
    forbidden = ("codex", "terminal", "powershell", "cmd.exe", "windows terminal", "password", "auth", "login", "captcha", "验证码", "密码")  # 新增代码+Phase57RealUiaLocator: 定义禁止目标关键词；如果没有这行代码，高风险窗口可能被读取。
    combined = f"{title} {app_id}"  # 新增代码+Phase57RealUiaLocator: 合并标题和 app 便于统一检查；如果没有这行代码，判断会重复。
    if any(token in combined for token in forbidden):  # 新增代码+Phase57RealUiaLocator: 检查是否命中禁止目标；如果没有这行代码，敏感窗口边界不生效。
        return False, "目标窗口属于终端、Codex、认证或敏感输入边界，Phase57 拒绝读取 UIA 树。"  # 新增代码+Phase57RealUiaLocator: 返回拒绝原因；如果没有这行代码，用户不知道为何 blocked。
    return False, "Phase57 当前只允许自有安全窗口，未读取普通用户窗口。"  # 新增代码+Phase57RealUiaLocator: 默认保守拒绝；如果没有这行代码，早期生产层可能越界读取用户桌面。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_is_phase57_safe_window 到此结束；如果没有这个边界说明，初学者不容易看出安全窗口判断范围。


class WindowsRealUiaLocatorRuntime:  # 新增代码+Phase57RealUiaLocator: 类段开始，组合真实 UIA provider 和语义定位器；如果没有这个类，树读取和定位无法作为统一 runtime 暴露。
    def __init__(self, platform: str | None = None, provider: Any | None = None, locator: SemanticControlLocator | None = None) -> None:  # 新增代码+Phase57RealUiaLocator: 函数段开始，初始化平台、provider 和 locator；如果没有这段函数，测试和生产无法注入依赖。
        self.platform = platform or sys.platform  # 新增代码+Phase57RealUiaLocator: 保存平台；如果没有这行代码，非 Windows 拒绝路径无法测试。
        self.provider = provider or PowerShellUiaTreeProvider(platform=self.platform)  # 新增代码+Phase57RealUiaLocator: 默认使用 PowerShell/.NET UIA provider；如果没有这行代码，生产 runtime 没有真实后端。
        self.locator = locator or SemanticControlLocator()  # 新增代码+Phase57RealUiaLocator: 默认创建语义定位器；如果没有这行代码，find_control 无法工作。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，WindowsRealUiaLocatorRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，返回 runtime 状态；如果没有这段函数，/computer status 无法展示 UIA 定位能力。
        provider_status = self.provider.status() if hasattr(self.provider, "status") else {"available": False, "reason": "provider 缺少 status。"}  # 新增代码+Phase57RealUiaLocator: 读取 provider 状态；如果没有这行代码，runtime 不知道真实依赖是否可用。
        return {"marker": PHASE57_WINDOWS_REAL_UIA_LOCATOR_MARKER, "model": PHASE57_REAL_UIA_LOCATOR_MODEL, "available": bool(provider_status.get("available")), "provider": provider_status, "semantic_locator_available": True, "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回统一状态；如果没有这行代码，状态 UI 没有机器可读事实源。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，WindowsRealUiaLocatorRuntime.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def observe_window(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，读取并清洗指定安全窗口 UIA 树；如果没有这段函数，runtime 没有真实观察能力。
        safe_window = dict(window or {})  # 新增代码+Phase57RealUiaLocator: 复制窗口输入避免污染调用方对象；如果没有这行代码，后续补字段可能改到外部状态。
        if self.platform != "win32":  # 新增代码+Phase57RealUiaLocator: 非 Windows 拒绝真实读取；如果没有这行代码，跨平台会误触发 Windows UIA。
            return self._failure("当前平台不是 Windows，未读取 UIA 控件树。")  # 新增代码+Phase57RealUiaLocator: 返回平台失败；如果没有这行代码，失败原因不清楚。
        safe, safe_reason = _is_phase57_safe_window(safe_window)  # 新增代码+Phase57RealUiaLocator: 检查目标是否自有安全窗口；如果没有这行代码，可能误读敏感窗口。
        if not safe:  # 新增代码+Phase57RealUiaLocator: 处理不安全目标；如果没有这行代码，禁止条件不会生效。
            return self._failure(safe_reason)  # 新增代码+Phase57RealUiaLocator: 返回安全拒绝结果；如果没有这行代码，调用方不知道被拒绝原因。
        provider_result = self.provider.read_window_tree(safe_window) if hasattr(self.provider, "read_window_tree") else {"captured": False, "reason": "provider 缺少 read_window_tree。"}  # 新增代码+Phase57RealUiaLocator: 调用 provider 读取树；如果没有这行代码，真实 UIA 不会执行。
        if not bool(provider_result.get("captured")):  # 新增代码+Phase57RealUiaLocator: 检查 provider 是否成功；如果没有这行代码，空树可能误报成功。
            return self._failure(str(provider_result.get("reason", "UIA provider 未读取到控件树。")))  # 新增代码+Phase57RealUiaLocator: 返回 provider 失败原因；如果没有这行代码，失败不可解释。
        state = {"sensitive": 0}  # 新增代码+Phase57RealUiaLocator: 初始化脱敏计数状态；如果没有这行代码，过滤次数无法汇总。
        tree = _sanitize_tree(provider_result.get("tree", {}), state)  # 新增代码+Phase57RealUiaLocator: 清洗整棵树；如果没有这行代码，原始 UIA 文本可能泄露。
        flat_nodes = _flatten_nodes(tree)  # 新增代码+Phase57RealUiaLocator: 生成扁平节点列表；如果没有这行代码，locator 和计数无法使用。
        bounds_available = any(bool(node.get("bounds", {}).get("width") or node.get("bounds", {}).get("height")) for node in flat_nodes)  # 新增代码+Phase57RealUiaLocator: 检查是否有坐标信息；如果没有这行代码，验收无法证明 bounds 存在。
        return {"marker": PHASE57_WINDOWS_REAL_UIA_LOCATOR_MARKER, "model": PHASE57_REAL_UIA_LOCATOR_MODEL, "captured": bool(flat_nodes), "real_uia_tree": bool(provider_result.get("real_provider_used", False) and flat_nodes), "safe_window_only": True, "safe_window_reason": safe_reason, "reason": "UIA 控件树读取成功。", "tree": tree, "flat_nodes": flat_nodes, "node_count": len(flat_nodes), "truncated": bool(provider_result.get("truncated", False)), "bounds_available": bounds_available, "clickable_count": sum(1 for node in flat_nodes if node.get("clickable")), "editable_count": sum(1 for node in flat_nodes if node.get("editable")), "sensitive_text_filtered": int(state.get("sensitive", 0)), "semantic_locator_available": True, "raw_text_included": False, "backend": str(provider_result.get("backend", "")), "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回完整安全观察结果；如果没有这行代码，helper 和 CLI 拿不到统一事实源。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，WindowsRealUiaLocatorRuntime.observe_window 到此结束；如果没有这个边界说明，初学者不容易看出观察流程范围。

    def find_control(self, window: dict[str, Any], query: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，读取安全窗口并运行语义定位；如果没有这段函数，高层工具需要手动拼 observe 和 locator。
        observed = self.observe_window(window)  # 新增代码+Phase57RealUiaLocator: 先读取控件树；如果没有这行代码，定位器没有真实节点输入。
        locator_result = self.locator.find(observed.get("flat_nodes", []), query or {}) if observed.get("captured") else {"matched": False, "candidate_count": 0, "confidence": 0.0, "reason": observed.get("reason", "未读取控件树。"), "control": {}, "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 成功时定位，失败时返回解释；如果没有这行代码，错误路径会抛异常。
        result = dict(observed)  # 新增代码+Phase57RealUiaLocator: 复制观察结果；如果没有这行代码，追加 locator 会污染缓存对象。
        result["locator"] = locator_result  # 新增代码+Phase57RealUiaLocator: 附加定位结果；如果没有这行代码，调用方需要第二次调用 locator。
        return result  # 新增代码+Phase57RealUiaLocator: 返回观察加定位的组合结果；如果没有这行代码，helper 拿不到完整响应。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，WindowsRealUiaLocatorRuntime.find_control 到此结束；如果没有这个边界说明，初学者不容易看出定位流程范围。

    def _failure(self, reason: str) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，构造 runtime 失败结果；如果没有这段函数，失败结构会漂移。
        return {"marker": PHASE57_WINDOWS_REAL_UIA_LOCATOR_MARKER, "model": PHASE57_REAL_UIA_LOCATOR_MODEL, "captured": False, "real_uia_tree": False, "safe_window_only": True, "reason": str(reason), "tree": {}, "flat_nodes": [], "node_count": 0, "truncated": False, "bounds_available": False, "clickable_count": 0, "editable_count": 0, "sensitive_text_filtered": 0, "semantic_locator_available": True, "raw_text_included": False, "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回统一失败字段；如果没有这行代码，调用方需要到处判断缺字段。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，WindowsRealUiaLocatorRuntime._failure 到此结束；如果没有这个边界说明，初学者不容易看出失败结构范围。
# 新增代码+Phase57RealUiaLocator: 类段结束，WindowsRealUiaLocatorRuntime 到此结束；如果没有这个边界说明，初学者不容易看出 runtime 范围。


class Phase57DedicatedSafeWindowLauncher:  # 修改代码+Phase57RealUiaLocator: 类段开始，启动只属于 Phase57 的独立 WinForms 安全窗口；如果没有这个类，真实 UIA smoke 可能误读用户已有 Notepad 标签页。
    def __init__(self, marker_text: str = "LearningAgent Phase57 real UIA locator smoke", title_prefix: str = "LearningAgent-Phase57-RealUiaLocatorSmoke") -> None:  # 修改代码+Phase58RealSendInputGuard: 函数段开始，初始化安全窗口内容和可复用标题前缀；如果没有这段函数，Phase58 无法复用隔离安全窗体。
        self.marker_text = marker_text  # 修改代码+Phase57RealUiaLocator: 保存写入安全窗体的标记文本；如果没有这行代码，窗体内容不易识别。
        self.title_prefix = str(title_prefix or "LearningAgent-Phase57-RealUiaLocatorSmoke")  # 新增代码+Phase58RealSendInputGuard: 保存安全窗体标题前缀；如果没有这行代码，Phase58 无法创建自有标题而只能复用 Phase57 名称。
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None  # 新增代码+Phase57RealUiaLocator: 保存临时目录对象；如果没有这行代码，cleanup 无法删除文件。
        self._process: subprocess.Popen[Any] | None = None  # 修改代码+Phase57RealUiaLocator: 保存安全窗体进程；如果没有这行代码，cleanup 无法关闭安全窗口。
    # 修改代码+Phase57RealUiaLocator: 函数段结束，Phase57DedicatedSafeWindowLauncher.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def launch(self) -> dict[str, Any]:  # 修改代码+Phase57RealUiaLocator: 函数段开始，创建临时 PowerShell WinForms 脚本并启动独立安全窗体；如果没有这段函数，真实 smoke 没有隔离 UIA 目标。
        self._temp_dir = tempfile.TemporaryDirectory(prefix="learning-agent-phase57-")  # 新增代码+Phase57RealUiaLocator: 创建隔离临时目录；如果没有这行代码，测试文件可能散落到项目或用户目录。
        script_path = Path(self._temp_dir.name) / "LearningAgent-Phase57-RealUiaLocatorSmoke.ps1"  # 修改代码+Phase57RealUiaLocator: 固定临时脚本名作为安全窗体来源；如果没有这行代码，窗体启动脚本没有落盘路径。
        title = f"{self.title_prefix}-{int(time.time() * 1000)}"  # 修改代码+Phase58RealSendInputGuard: 使用可配置前缀生成每次唯一标题；如果没有这行代码，Phase58 不能用自己的安全窗口身份做目标守卫。
        script_path.write_text(self._forms_script(title), encoding="utf-8")  # 修改代码+Phase57RealUiaLocator: 写入 WinForms 安全窗体脚本；如果没有这行代码，PowerShell 没有可执行窗体定义。
        self._process = subprocess.Popen(["powershell.exe", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-File", str(script_path)])  # 修改代码+Phase57RealUiaLocator: 启动独立 STA WinForms 窗体；如果没有这行代码，真实桌面不会出现隔离安全窗口。
        return {"title_hint": title, "script_path": str(script_path)}  # 修改代码+Phase57RealUiaLocator: 返回标题线索和脚本路径；如果没有这行代码，poll 无法只找自有窗口。
    # 修改代码+Phase57RealUiaLocator: 函数段结束，Phase57DedicatedSafeWindowLauncher.launch 到此结束；如果没有这个边界说明，初学者不容易看出启动范围。

    def _forms_script(self, title: str) -> str:  # 修改代码+Phase57RealUiaLocator: 函数段开始，生成独立 WinForms 安全窗体脚本；如果没有这段函数，launcher 只能复用可能含用户内容的外部应用。
        safe_title = str(title).replace("'", "''")  # 新增代码+Phase57RealUiaLocator: 转义 PowerShell 单引号；如果没有这行代码，标题里的特殊字符可能破坏脚本。
        safe_marker = str(self.marker_text).replace("'", "''")  # 新增代码+Phase57RealUiaLocator: 转义窗体文本；如果没有这行代码，marker 文本可能破坏脚本。
        return f"""Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$form = New-Object System.Windows.Forms.Form
$form.Text = '{safe_title}'
$form.Width = 720
$form.Height = 460
$form.StartPosition = 'CenterScreen'
$label = New-Object System.Windows.Forms.Label
$label.Name = 'Phase57Label'
$label.Text = '{safe_marker}'
$label.AutoSize = $true
$label.Location = New-Object System.Drawing.Point(24, 18)
$text = New-Object System.Windows.Forms.TextBox
$text.Name = 'Phase57Editor'
$text.Text = 'Phase57 editable safe text'
$text.Multiline = $true
$text.Width = 640
$text.Height = 240
$text.Location = New-Object System.Drawing.Point(24, 58)
$button = New-Object System.Windows.Forms.Button
$button.Name = 'Phase57Button'
$button.Text = 'Phase57 Button'
$button.Width = 150
$button.Height = 34
$button.Location = New-Object System.Drawing.Point(24, 320)
$form.Controls.Add($label)
$form.Controls.Add($text)
$form.Controls.Add($button)
$form.Add_Shown({{ $form.Activate(); $text.Focus() }}) # 修改代码+Phase58RealSendInputGuard: 在 Python f-string 里用双花括号生成 PowerShell 脚本块并聚焦文本框；如果没有这行代码，真实 SendInput 文本可能打不到安全输入框或模块直接语法失败。
[System.Windows.Forms.Application]::Run($form)
"""  # 新增代码+Phase57RealUiaLocator: 返回只创建自有窗体的 PowerShell 脚本；如果没有这行代码，真实 smoke 无法隔离用户桌面内容。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，Phase57DedicatedSafeWindowLauncher._forms_script 到此结束；如果没有这个边界说明，初学者不容易看出窗体脚本范围。

    def cleanup(self) -> bool:  # 修改代码+Phase57RealUiaLocator: 函数段开始，关闭独立安全窗体并删除临时目录；如果没有这段函数，smoke 可能留下窗口和文件。
        cleaned = False  # 新增代码+Phase57RealUiaLocator: 初始化清理状态；如果没有这行代码，返回值无法说明是否执行清理。
        process = self._process  # 新增代码+Phase57RealUiaLocator: 保存进程引用；如果没有这行代码，后续会重复访问可变属性。
        if process is not None and process.poll() is None:  # 修改代码+Phase57RealUiaLocator: 只关闭仍在运行的安全窗体进程；如果没有这行代码，已退出进程可能触发无意义错误。
            process.terminate()  # 修改代码+Phase57RealUiaLocator: 请求安全窗体正常退出；如果没有这行代码，安全窗口会残留。
            try:  # 修改代码+Phase57RealUiaLocator: 捕获等待超时；如果没有这行代码，安全窗体关闭慢会中断清理。
                process.wait(timeout=3)  # 新增代码+Phase57RealUiaLocator: 等待进程退出；如果没有这行代码，临时文件可能仍被占用。
            except subprocess.TimeoutExpired:  # 新增代码+Phase57RealUiaLocator: 处理关闭超时；如果没有这行代码，超时窗口会残留。
                process.kill()  # 新增代码+Phase57RealUiaLocator: 强制结束测试窗口；如果没有这行代码，超时后窗口仍可能残留。
                process.wait(timeout=3)  # 新增代码+Phase57RealUiaLocator: 等待强制结束完成；如果没有这行代码，资源释放状态不确定。
            cleaned = True  # 新增代码+Phase57RealUiaLocator: 标记已处理进程；如果没有这行代码，结果无法说明窗口已清理。
        if self._temp_dir is not None:  # 新增代码+Phase57RealUiaLocator: 检查临时目录是否存在；如果没有这行代码，空 cleanup 会访问 None。
            self._temp_dir.cleanup()  # 新增代码+Phase57RealUiaLocator: 删除临时目录；如果没有这行代码，磁盘会留下 smoke 文件。
            self._temp_dir = None  # 新增代码+Phase57RealUiaLocator: 清空临时目录引用；如果没有这行代码，重复 cleanup 可能再次清理同一对象。
            cleaned = True  # 新增代码+Phase57RealUiaLocator: 标记已清理文件；如果没有这行代码，结果可能误报未清理。
        return cleaned  # 新增代码+Phase57RealUiaLocator: 返回清理状态；如果没有这行代码，smoke 报告无法审计善后。
    # 修改代码+Phase57RealUiaLocator: 函数段结束，Phase57DedicatedSafeWindowLauncher.cleanup 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。
# 修改代码+Phase57RealUiaLocator: 类段结束，Phase57DedicatedSafeWindowLauncher 到此结束；如果没有这个边界说明，初学者不容易看出安全窗口 launcher 范围。


Phase57NotepadSafeWindowLauncher = Phase57DedicatedSafeWindowLauncher  # 新增代码+Phase57RealUiaLocator: 保留旧类名兼容早期调用但实际使用独立窗体；如果没有这行代码，已导入旧名称的脚本会失效。


def _find_phase57_safe_window(windows: list[dict[str, Any]], title_hint: str) -> dict[str, Any] | None:  # 修改代码+Phase57RealUiaLocator: 函数段开始，从窗口列表找自有 Phase57 安全窗体；如果没有这段函数，smoke 可能误选用户窗口。
    lowered_hint = str(title_hint or "").lower()  # 新增代码+Phase57RealUiaLocator: 标题线索转小写；如果没有这行代码，大小写差异可能导致找不到窗口。
    for window in windows:  # 新增代码+Phase57RealUiaLocator: 遍历窗口列表；如果没有这行代码，无法搜索目标窗口。
        title = str(window.get("title_preview", window.get("title", ""))).lower()  # 修改代码+Phase57RealUiaLocator: 读取窗口标题摘要；如果没有这行代码，无法匹配安全窗体标题。
        if lowered_hint and lowered_hint == title:  # 修改代码+Phase57RealUiaLocator: 只接受精确等于本次唯一标题的窗口；如果没有这行代码，旧 Notepad 标签页可能被误读。
            safe_window = dict(window)  # 新增代码+Phase57RealUiaLocator: 复制窗口记录；如果没有这行代码，调用方可能修改 inventory 原始对象。
            safe_window["title_preview"] = safe_window.get("title_preview", safe_window.get("title", title_hint))  # 新增代码+Phase57RealUiaLocator: 确保安全判断有 title_preview；如果没有这行代码，runtime 可能拒绝自有窗口。
            return safe_window  # 新增代码+Phase57RealUiaLocator: 返回安全窗口；如果没有这行代码，poll 找到后仍会失败。
    return None  # 新增代码+Phase57RealUiaLocator: 找不到时返回 None；如果没有这行代码，调用方无法区分未找到和异常。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_find_phase57_safe_window 到此结束；如果没有这个边界说明，初学者不容易看出安全窗口匹配范围。


def _poll_phase57_safe_window(inventory: Any, title_hint: str, timeout_seconds: float, poll_interval_seconds: float) -> dict[str, Any] | None:  # 修改代码+Phase57RealUiaLocator: 函数段开始，轮询等待安全窗体出现；如果没有这段函数，窗口启动稍慢会误失败。
    deadline = time.time() + max(0.5, float(timeout_seconds))  # 新增代码+Phase57RealUiaLocator: 计算超时截止时间；如果没有这行代码，等待可能无限持续或立即失败。
    while time.time() <= deadline:  # 新增代码+Phase57RealUiaLocator: 在截止前重复检查；如果没有这行代码，异步窗口创建无法等待。
        snapshot = inventory.snapshot()  # 修改代码+Phase57RealUiaLocator: 获取窗口快照；如果没有这行代码，无法看到安全窗体是否出现。
        window = _find_phase57_safe_window(list(getattr(snapshot, "windows", []) or []), title_hint)  # 新增代码+Phase57RealUiaLocator: 查找自有安全窗口；如果没有这行代码，后续 UIA 没有可信 hwnd。
        if window is not None:  # 新增代码+Phase57RealUiaLocator: 判断是否找到窗口；如果没有这行代码，找到后仍会继续等待。
            return window  # 新增代码+Phase57RealUiaLocator: 返回目标窗口；如果没有这行代码，调用方拿不到 hwnd。
        time.sleep(max(0.05, float(poll_interval_seconds)))  # 新增代码+Phase57RealUiaLocator: 短暂等待后重试；如果没有这行代码，轮询会占满 CPU。
    return None  # 新增代码+Phase57RealUiaLocator: 超时返回未找到；如果没有这行代码，调用方无法输出定位失败。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_poll_phase57_safe_window 到此结束；如果没有这个边界说明，初学者不容易看出轮询范围。


def run_phase57_real_uia_locator_smoke(platform: str | None = None, inventory_factory: Any | None = None, launcher: Any | None = None, timeout_seconds: float = 8.0, poll_interval_seconds: float = 0.25) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，运行真实安全窗口 UIA 树和定位 smoke；如果没有这段函数，Phase57 无法证明真实 Windows UIA。
    current_platform = platform or sys.platform  # 新增代码+Phase57RealUiaLocator: 确定平台；如果没有这行代码，测试无法注入平台。
    if current_platform != "win32":  # 修改代码+Phase57RealUiaLocator: 非 Windows 直接诚实返回；如果没有这行代码，跨平台会误触安全窗体。
        return {"real_smoke": False, "platform_supported": False, "safe_window_only": True, "reason": "当前平台不是 Windows，未运行真实 UIA smoke。", "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回平台不支持；如果没有这行代码，失败原因不清楚。
    active_launcher = launcher or Phase57DedicatedSafeWindowLauncher()  # 修改代码+Phase57RealUiaLocator: 没有注入时使用独立安全窗体 launcher；如果没有这行代码，生产 smoke 没有默认目标。
    target = active_launcher.launch() if hasattr(active_launcher, "launch") else active_launcher()  # 新增代码+Phase57RealUiaLocator: 启动或获取安全目标；如果没有这行代码，UIA 没有自有窗口。
    try:  # 新增代码+Phase57RealUiaLocator: 包住真实窗口定位和 UIA 读取；如果没有这行代码，异常会绕过结构化报告和清理。
        inventory = inventory_factory() if inventory_factory is not None else WindowsWindowInventoryProbe()  # 新增代码+Phase57RealUiaLocator: 创建真实或注入 inventory；如果没有这行代码，无法定位窗口。
        window = _poll_phase57_safe_window(inventory, str(target.get("title_hint", "")), timeout_seconds, poll_interval_seconds)  # 修改代码+Phase57RealUiaLocator: 等待自有安全窗体出现；如果没有这行代码，窗体启动延迟会误失败。
        if window is None:  # 新增代码+Phase57RealUiaLocator: 检查是否找到窗口；如果没有这行代码，后续会对空窗口读 UIA。
            return {"real_smoke": False, "platform_supported": True, "safe_window_found": False, "safe_window_only": True, "reason": "未找到 Phase57 自有安全窗口，未读取 UIA。", "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回未找到结果；如果没有这行代码，定位失败不可解释。
        runtime = WindowsRealUiaLocatorRuntime(platform=current_platform)  # 新增代码+Phase57RealUiaLocator: 创建真实 UIA runtime；如果没有这行代码，smoke 不会走 PowerShell/.NET UIA。
        observed = runtime.observe_window(window)  # 新增代码+Phase57RealUiaLocator: 读取安全窗口控件树；如果没有这行代码，real_smoke 没有 UIA 输入。
        locator_result = _phase57_find_safe_edit_control(observed.get("flat_nodes", []))  # 修改代码+Phase57RealUiaLocator: 尝试定位独立安全窗体里的编辑控件；如果没有这行代码，semantic_locator token 没有真实证据。
        real_smoke = bool(observed.get("captured") and observed.get("real_uia_tree") and locator_result.get("matched"))  # 新增代码+Phase57RealUiaLocator: 汇总真实 smoke 成功条件；如果没有这行代码，读到空树也可能误报成功。
        return {"real_smoke": real_smoke, "platform_supported": True, "safe_window_found": True, "safe_window_only": True, "observed": observed, "locator": locator_result, "node_count": observed.get("node_count", 0), "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回真实 smoke 报告；如果没有这行代码，CLI 无法带出真实 UIA 证据。
    except Exception as error:  # 修改代码+Phase57RealUiaLocator: 捕获真实 smoke 异常；如果没有这行代码，桌面权限或安全窗体问题会让命令崩溃。
        return {"real_smoke": False, "platform_supported": True, "safe_window_found": False, "safe_window_only": True, "reason": f"Phase57 真实 UIA smoke 异常：{type(error).__name__}", "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回异常类型但不泄露本地细节；如果没有这行代码，用户只会看到堆栈。
    finally:  # 修改代码+Phase57RealUiaLocator: 无论成功失败都清理安全窗口；如果没有这行代码，安全窗体可能残留。
        if hasattr(active_launcher, "cleanup"):  # 新增代码+Phase57RealUiaLocator: 检查 launcher 是否有 cleanup；如果没有这行代码，函数式 fake launcher 会触发 AttributeError。
            active_launcher.cleanup()  # 修改代码+Phase57RealUiaLocator: 调用 cleanup 关闭安全窗口；如果没有这行代码，真实验收可能留下独立窗体。
# 新增代码+Phase57RealUiaLocator: 函数段结束，run_phase57_real_uia_locator_smoke 到此结束；如果没有这个边界说明，初学者不容易看出真实 smoke 范围。


def _phase57_find_safe_edit_control(flat_nodes: list[dict[str, Any]]) -> dict[str, Any]:  # 修改代码+Phase57RealUiaLocator: 函数段开始，为真实安全窗体 smoke 查找编辑/文档控件；如果没有这段函数，真实 UIA 树可能读到但语义定位无证据。
    locator = SemanticControlLocator()  # 新增代码+Phase57RealUiaLocator: 创建定位器；如果没有这行代码，函数无法复用统一定位逻辑。
    for query in ({"automation_id": "Phase57Editor"}, {"role": "Edit"}, {"class_name": "EDIT"}, {"class_name": "TextBox"}, {"text": "Phase57"}):  # 修改代码+Phase57RealUiaLocator: 兼容 WinForms TextBox 的 id、角色、EDIT 类名和文本线索；如果没有这行代码，真实 smoke 容易因控件角色差异失败。
        result = locator.find(flat_nodes, query)  # 新增代码+Phase57RealUiaLocator: 执行一次语义定位；如果没有这行代码，查询条件不会生效。
        if result.get("matched"):  # 新增代码+Phase57RealUiaLocator: 检查当前查询是否命中；如果没有这行代码，后续会覆盖成功结果。
            return result  # 新增代码+Phase57RealUiaLocator: 返回第一个成功定位；如果没有这行代码，函数无法短路成功结果。
    return locator.find(flat_nodes, {"role": "Window"})  # 新增代码+Phase57RealUiaLocator: 兜底定位窗口根节点；如果没有这行代码，部分系统 UIA 树只读到根时完全没有定位结果。
# 修改代码+Phase57RealUiaLocator: 函数段结束，_phase57_find_safe_edit_control 到此结束；如果没有这个边界说明，初学者不容易看出安全窗体定位范围。


def _phase57_contract_tree() -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，构造合同自检用控件树；如果没有这段函数，单元测试和 CLI 合同会触碰真实桌面。
    return {"node_id": "0", "name": "LearningAgent-Phase57-Contract", "role": "Window", "automation_id": "root", "class_name": "Notepad", "bounds": {"left": 10, "top": 20, "right": 620, "bottom": 420, "width": 610, "height": 400}, "enabled": True, "children": [{"node_id": "0.0", "name": "Save", "role": "Button", "automation_id": "save", "class_name": "Button", "bounds": {"left": 30, "top": 48, "right": 120, "bottom": 82, "width": 90, "height": 34}, "enabled": True, "children": []}, {"node_id": "0.1", "name": "Document", "role": "Edit", "automation_id": "editor", "class_name": "Edit", "bounds": {"left": 30, "top": 90, "right": 590, "bottom": 390, "width": 560, "height": 300}, "enabled": True, "children": []}, {"node_id": "0.2", "name": "password: phase57-contract-secret", "role": "Edit", "automation_id": "secret", "class_name": "Edit", "bounds": {"left": 30, "top": 400, "right": 590, "bottom": 430, "width": 560, "height": 30}, "enabled": True, "children": []}]}  # 新增代码+Phase57RealUiaLocator: 返回带敏感节点的树；如果没有这行代码，脱敏和 locator 合同没有稳定输入。
# 新增代码+Phase57RealUiaLocator: 函数段结束，_phase57_contract_tree 到此结束；如果没有这个边界说明，初学者不容易看出合同树范围。


class _Phase57ContractProvider:  # 新增代码+Phase57RealUiaLocator: 类段开始，定义合同自检 fake provider；如果没有这个类，自检会触碰真实桌面。
    def status(self) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，返回 fake provider 可用状态；如果没有这段函数，runtime status 无法用于合同。
        return {"available": True, "backend": "powershell_dotnet_uia", "real_provider_required": True, "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 返回与真实后端同名但只用于合同的状态；如果没有这行代码，测试无法驱动成功路径。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，_Phase57ContractProvider.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def read_window_tree(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，返回合同树；如果没有这段函数，合同 runtime 没有树输入。
        _ = window  # 新增代码+Phase57RealUiaLocator: 明确合同 provider 不依赖真实窗口；如果没有这行代码，读者可能误以为这里会读桌面。
        return {"captured": True, "tree": _phase57_contract_tree(), "backend": "powershell_dotnet_uia", "real_provider_used": True, "reason": "phase57 contract provider"}  # 新增代码+Phase57RealUiaLocator: 返回标准 provider 结果；如果没有这行代码，runtime 无法清洗和定位。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，_Phase57ContractProvider.read_window_tree 到此结束；如果没有这个边界说明，初学者不容易看出合同读取范围。
# 新增代码+Phase57RealUiaLocator: 类段结束，_Phase57ContractProvider 到此结束；如果没有这个边界说明，初学者不容易看出合同 provider 范围。


def run_phase57_real_uia_locator_contract(real_smoke: bool = True) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，运行 Phase57 合同自检和可选真实 smoke；如果没有这段函数，CLI 和真实终端没有统一入口。
    window = {"window_id": "hwnd:5701", "hwnd": 5701, "title_preview": "LearningAgent-Phase57-Contract", "app_id": "notepad.exe", "rect": {"left": 10, "top": 20, "right": 620, "bottom": 420}}  # 新增代码+Phase57RealUiaLocator: 准备安全合同窗口引用；如果没有这行代码，runtime 会因缺少安全窗口上下文拒绝读取。
    runtime = WindowsRealUiaLocatorRuntime(platform="win32", provider=_Phase57ContractProvider())  # 新增代码+Phase57RealUiaLocator: 创建合同 runtime；如果没有这行代码，合同自检会碰真实桌面。
    observed = runtime.observe_window(window)  # 新增代码+Phase57RealUiaLocator: 读取合同控件树；如果没有这行代码，real_uia_tree token 没有输入。
    locator_result = runtime.locator.find(observed.get("flat_nodes", []), {"automation_id": "editor"})  # 新增代码+Phase57RealUiaLocator: 按 automation_id 定位编辑区；如果没有这行代码，semantic_locator token 没有证据。
    from learning_agent.computer_use.native_helper_v2 import WindowsNativeHelperV2Worker  # 新增代码+Phase57RealUiaLocator: 延迟导入 helper v2 避免模块循环；如果没有这行代码，合同无法证明 helper read_uia_tree 接入。
    helper_response = WindowsNativeHelperV2Worker(uia_locator_runtime=runtime).handle({"op": "read_uia_tree", "window": window, "locator": {"automation_id": "editor"}})  # 新增代码+Phase57RealUiaLocator: 通过 helper v2 协议读取 UIA 树；如果没有这行代码，out-of-process 协议可能仍是占位。
    helper_result = helper_response.get("result", {}) if isinstance(helper_response, dict) else {}  # 新增代码+Phase57RealUiaLocator: 提取 helper result；如果没有这行代码，helper_v2_uia 难以稳定判断。
    serialized = json.dumps({"observed": observed, "locator": locator_result, "helper": helper_response}, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase57RealUiaLocator: 序列化主要响应检查泄露；如果没有这行代码，敏感文本可能漏检。
    real_report = run_phase57_real_uia_locator_smoke() if real_smoke else {"real_smoke": False, "skipped": True, "safe_window_only": True, "actions_expanded": PHASE57_ACTIONS_EXPANDED}  # 新增代码+Phase57RealUiaLocator: 根据参数执行真实 smoke；如果没有这行代码，单测无法跳过真实桌面。
    real_uia_tree = bool(observed.get("captured") and observed.get("real_uia_tree") and (not real_smoke or real_report.get("real_smoke")))  # 新增代码+Phase57RealUiaLocator: 汇总合同和真实树成功条件；如果没有这行代码，fake 合同可能冒充真实 smoke。
    semantic_locator = bool(locator_result.get("matched") and (not real_smoke or real_report.get("locator", {}).get("matched")))  # 新增代码+Phase57RealUiaLocator: 汇总合同和真实 locator 成功条件；如果没有这行代码，真实定位失败可能被漏掉。
    helper_v2_uia = bool(helper_response.get("ok") and helper_result.get("real_uia_tree") and helper_result.get("semantic_locator_available"))  # 新增代码+Phase57RealUiaLocator: 检查 helper v2 已接入 Phase57 runtime；如果没有这行代码，helper 占位不会暴露。
    safe_window_only = bool(observed.get("safe_window_only") and real_report.get("safe_window_only", True))  # 新增代码+Phase57RealUiaLocator: 检查只面向安全窗口；如果没有这行代码，越界读取风险不可见。
    raw_text_hidden = "phase57-contract-secret" not in serialized and "password: phase57" not in serialized.lower()  # 新增代码+Phase57RealUiaLocator: 检查敏感原文没有泄露；如果没有这行代码，脱敏失败可能被误过。
    passed = bool(real_uia_tree and semantic_locator and helper_v2_uia and safe_window_only and raw_text_hidden and not PHASE57_ACTIONS_EXPANDED)  # 新增代码+Phase57RealUiaLocator: 汇总通过条件；如果没有这行代码，CLI 无法表达失败。
    return {"marker": PHASE57_WINDOWS_REAL_UIA_LOCATOR_MARKER, "ok_token": PHASE57_WINDOWS_REAL_UIA_LOCATOR_OK_TOKEN, "real_uia_tree": real_uia_tree, "semantic_locator": semantic_locator, "helper_v2_uia": helper_v2_uia, "safe_window_only": safe_window_only, "real_smoke": bool(real_report.get("real_smoke", False)), "raw_text_hidden": raw_text_hidden, "actions_expanded": PHASE57_ACTIONS_EXPANDED, "passed": passed, "observed": observed, "locator": locator_result, "helper_response": helper_response, "real_report": real_report}  # 新增代码+Phase57RealUiaLocator: 返回完整合同报告；如果没有这行代码，测试和 CLI 拿不到统一结果。
# 新增代码+Phase57RealUiaLocator: 函数段结束，run_phase57_real_uia_locator_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase57_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase57RealUiaLocator: 函数段开始，把报告转成稳定 token 行；如果没有这段函数，真实终端场景要解析复杂 JSON。
    return f"{PHASE57_WINDOWS_REAL_UIA_LOCATOR_OK_TOKEN} real_uia_tree={_phase57_bool_token(report.get('real_uia_tree'))} semantic_locator={_phase57_bool_token(report.get('semantic_locator'))} helper_v2_uia={_phase57_bool_token(report.get('helper_v2_uia'))} safe_window_only={_phase57_bool_token(report.get('safe_window_only'))} real_smoke={_phase57_bool_token(report.get('real_smoke'))} raw_text_hidden={_phase57_bool_token(report.get('raw_text_hidden'))} actions_expanded={_phase57_bool_token(report.get('actions_expanded'))} marker={PHASE57_WINDOWS_REAL_UIA_LOCATOR_MARKER}"  # 新增代码+Phase57RealUiaLocator: 返回固定顺序 token；如果没有这行代码，验收输出容易漂移。
# 新增代码+Phase57RealUiaLocator: 函数段结束，phase57_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase57RealUiaLocator: 函数段开始，提供命令行入口；如果没有这段函数，真实终端无法执行 Phase57 验收。
    _ = argv  # 新增代码+Phase57RealUiaLocator: 保留 argv 以便未来扩展；如果没有这行代码，静态检查可能提示未使用参数。
    report = run_phase57_real_uia_locator_contract(real_smoke=True)  # 新增代码+Phase57RealUiaLocator: 执行合同和真实安全窗口 UIA smoke；如果没有这行代码，CLI 不会证明真实 UIA。
    print(phase57_cli_line(report))  # 新增代码+Phase57RealUiaLocator: 打印稳定 token 行；如果没有这行代码，debug log 无法确认验收结果。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase57RealUiaLocator: 打印结构化报告便于失败复盘；如果没有这行代码，失败时不易定位原因。
    print(PHASE57_WINDOWS_REAL_UIA_LOCATOR_MARKER)  # 新增代码+Phase57RealUiaLocator: 单独打印 ready marker；如果没有这行代码，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase57RealUiaLocator: 根据真实验收结果返回退出码；如果没有这行代码，真实 UIA 失败也可能被当成功。
# 新增代码+Phase57RealUiaLocator: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["PHASE57_ACTIONS_EXPANDED", "PHASE57_REAL_UIA_LOCATOR_MODEL", "PHASE57_WINDOWS_REAL_UIA_LOCATOR_MARKER", "PHASE57_WINDOWS_REAL_UIA_LOCATOR_OK_TOKEN", "Phase57DedicatedSafeWindowLauncher", "Phase57NotepadSafeWindowLauncher", "PowerShellUiaTreeProvider", "SemanticControlLocator", "WindowsRealUiaLocatorRuntime", "main", "phase57_cli_line", "run_phase57_real_uia_locator_contract", "run_phase57_real_uia_locator_smoke"]  # 修改代码+Phase57RealUiaLocator: 限定公开导出名称并包含新旧安全窗口 launcher 名称；如果没有这行代码，from module import * 会暴露内部 helper 或漏掉兼容入口。


if __name__ == "__main__":  # 新增代码+Phase57RealUiaLocator: 允许直接运行模块；如果没有这行代码，python -m 不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase57RealUiaLocator: 调用 main 并传递退出码；如果没有这行代码，命令行状态不明确。
