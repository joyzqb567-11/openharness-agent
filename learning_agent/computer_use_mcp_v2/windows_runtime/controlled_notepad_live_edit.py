"""Phase97 受控 Notepad 现场编辑合同。"""  # 新增代码+Phase97ControlledNotepadLiveEdit：说明本模块只负责 Phase97 的受控 Notepad 编辑合同；如果没有这一行，读者很难快速区分它和旧的 smoke/SendInput 模块。
from __future__ import annotations  # 新增代码+Phase97ControlledNotepadLiveEdit：启用延迟类型解析，避免类型标注在导入顺序变化时出错；如果没有这一行，后续前向类型写法更容易在旧解释器行为下失败。

import json  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 JSON 用来写合同报告和检查敏感文本是否泄露；如果没有这一行，报告无法稳定落盘也无法做脱敏扫描。
import os  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 os 用来读取真实 Notepad 执行的双环境门；如果没有这一行，CLI 入口不能按环境变量显式启用真实路径。
import time  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 time 用来生成默认隔离运行目录；如果没有这一行，多次 CLI 运行可能互相覆盖报告。
from pathlib import Path  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 Path 统一处理 Windows 路径；如果没有这一行，目标文件和报告路径会变成脆弱的字符串拼接。
from typing import Any  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 Any 描述动态报告字段；如果没有这一行，公开函数的 JSON 风格返回值边界不清楚。

try:  # 新增代码+Phase97ControlledNotepadLiveEdit：优先按包路径导入项目内原子写文件工具；如果没有这段代码，单元测试和真实终端入口不能共享同一套写报告方式。
    from learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # 新增代码+Phase97ControlledNotepadLiveEdit：复用现有 Computer Use 运行根目录；如果没有这一行，Phase97 报告落点会和前序阶段割裂。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase97ControlledNotepadLiveEdit：复用原子 JSON 写入，避免半写报告；如果没有这一行，异常中断时可能留下损坏 JSON。
except ModuleNotFoundError as error:  # 新增代码+Phase97ControlledNotepadLiveEdit：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行的导入方式；如果没有这一段，真实终端验收可能因包前缀缺失失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase97ControlledNotepadLiveEdit：只对包路径缺失做 fallback；如果没有这一行，内部真实 bug 可能被误吞。
        raise  # 新增代码+Phase97ControlledNotepadLiveEdit：重新抛出非路径类导入错误；如果没有这一行，底层模块问题会被隐藏成难排查的假兼容。
    from computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # type: ignore  # 新增代码+Phase97ControlledNotepadLiveEdit：脚本模式下复用现有运行根目录；如果没有这一行，bat 入口无法定位默认报告目录。
    from runtime.files import atomic_write_json  # type: ignore  # 新增代码+Phase97ControlledNotepadLiveEdit：脚本模式下复用原子 JSON 写入；如果没有这一行，bat 入口可能写出半截报告。

PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_MARKER = "PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_READY"  # 新增代码+Phase97ControlledNotepadLiveEdit：定义真实终端验收等待的 ready marker；如果没有这一行，验收脚本没有稳定锚点。
PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK_TOKEN = "PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK"  # 新增代码+Phase97ControlledNotepadLiveEdit：定义成功 token；如果没有这一行，日志无法区分成功合同输出和普通文本。
PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_MODEL = "phase97_controlled_notepad_live_edit"  # 新增代码+Phase97ControlledNotepadLiveEdit：定义报告模型名；如果没有这一行，状态矩阵无法识别当前合同版本。
PHASE97_REAL_NOTEPAD_LIVE_EDIT_ENV = "LEARNING_AGENT_PHASE97_ENABLE_REAL_NOTEPAD_EDIT"  # 新增代码+Phase97ControlledNotepadLiveEdit：定义允许真实 Notepad 编辑的环境门；如果没有这一行，真实桌面动作缺少第二道显式确认。
PHASE97_REAL_NOTEPAD_LIVE_EDIT_REQUEST_ENV = "LEARNING_AGENT_PHASE97_RUN_REAL_NOTEPAD_EDIT"  # 新增代码+Phase97ControlledNotepadLiveEdit：定义请求真实 Notepad 编辑的环境门；如果没有这一行，CLI 无法表达本次确实要跑真实路径。
PHASE97_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase97ControlledNotepadLiveEdit：声明本阶段没有开放无边界桌面动作；如果没有这一行，能力范围容易被误读成已扩大。
DEFAULT_PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_ROOT = DEFAULT_PERSISTENT_GRANTS_ROOT.parent / "phase97_controlled_notepad_live_edit"  # 新增代码+Phase97ControlledNotepadLiveEdit：定义默认报告根目录；如果没有这一行，CLI 运行证据没有固定落点。

def _phase97_bool_token(value: Any) -> str:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会混用 True/False 而影响匹配。
    return "true" if bool(value) else "false"  # 新增代码+Phase97ControlledNotepadLiveEdit：返回 true 或 false 文本；如果没有这一行，验收脚本的精确字符串断言会不稳定。
# 新增代码+Phase97ControlledNotepadLiveEdit：函数段结束，_phase97_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。

def _phase97_env_enabled(name: str) -> bool:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，统一判断环境变量是否为显式真值；如果没有这段函数，门禁解析会散落在代码里。
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase97ControlledNotepadLiveEdit：只接受明确真值字符串；如果没有这一行，模糊环境值可能误开真实桌面动作。
# 新增代码+Phase97ControlledNotepadLiveEdit：函数段结束，_phase97_env_enabled 到此结束；如果没有这个边界说明，初学者不容易看出环境门解析范围。

def _phase97_request_real_edit(explicit_value: bool | None = None) -> bool:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，判断本次是否请求真实 Notepad 编辑；如果没有这段函数，测试参数和环境变量入口会漂移。
    if explicit_value is not None:  # 新增代码+Phase97ControlledNotepadLiveEdit：调用方传入显式值时优先使用；如果没有这一行，单元测试无法稳定覆盖真实请求分支。
        return bool(explicit_value)  # 新增代码+Phase97ControlledNotepadLiveEdit：返回显式请求布尔值；如果没有这一行，测试传参不会生效。
    return _phase97_env_enabled(PHASE97_REAL_NOTEPAD_LIVE_EDIT_REQUEST_ENV)  # 新增代码+Phase97ControlledNotepadLiveEdit：没有显式值时读取请求环境门；如果没有这一行，CLI 无法请求真实编辑路径。
# 新增代码+Phase97ControlledNotepadLiveEdit：函数段结束，_phase97_request_real_edit 到此结束；如果没有这个边界说明，初学者不容易看出请求门范围。

def _phase97_real_gate_enabled(explicit_value: bool | None = None) -> bool:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，判断真实 Notepad 编辑是否被允许；如果没有这段函数，第二道安全门会分散且难审计。
    if explicit_value is not None:  # 新增代码+Phase97ControlledNotepadLiveEdit：调用方传入显式允许值时优先使用；如果没有这一行，单元测试无法安全打开 gated 分支。
        return bool(explicit_value)  # 新增代码+Phase97ControlledNotepadLiveEdit：返回显式允许布尔值；如果没有这一行，测试传参不会生效。
    return _phase97_env_enabled(PHASE97_REAL_NOTEPAD_LIVE_EDIT_ENV)  # 新增代码+Phase97ControlledNotepadLiveEdit：没有显式值时读取允许环境门；如果没有这一行，CLI 真实路径缺少环境开关。
# 新增代码+Phase97ControlledNotepadLiveEdit：函数段结束，_phase97_real_gate_enabled 到此结束；如果没有这个边界说明，初学者不容易看出允许门范围。

def _phase97_expected_text() -> str:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，构造写入 Notepad 的固定受控文本；如果没有这段函数，用户原始 prompt 可能被误当成输入内容。
    return "PHASE97 controlled Notepad live edit\nThis file was written with controlled acceptance text only.\nRaw user prompt text is intentionally not included.\n"  # 新增代码+Phase97ControlledNotepadLiveEdit：返回不含用户原文的验收文本；如果没有这一行，显式编辑路径没有可验证的受控内容。
# 新增代码+Phase97ControlledNotepadLiveEdit：函数段结束，_phase97_expected_text 到此结束；如果没有这个边界说明，初学者不容易看出受控文本范围。

def _phase97_sha256_16(text: str) -> str:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，生成短哈希用于脱敏审计；如果没有这段函数，报告要么泄露文本要么缺少内容指纹。
    import hashlib  # 新增代码+Phase97ControlledNotepadLiveEdit：局部导入 hashlib 只为计算短哈希；如果没有这一行，保存验证报告无法生成脱敏指纹。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase97ControlledNotepadLiveEdit：返回前 16 位哈希；如果没有这一行，报告无法证明保存内容被读取过。
# 新增代码+Phase97ControlledNotepadLiveEdit：函数段结束，_phase97_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出哈希范围。

def _phase97_default_off_report() -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，生成默认关闭零物理事件证据；如果没有这段函数，安全默认只能靠口头承诺。
    return {"decision": "real_notepad_edit_disabled_by_default", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase97ControlledNotepadLiveEdit：返回默认关闭证据；如果没有这一行，报告无法证明普通运行没有触碰桌面。
# 新增代码+Phase97ControlledNotepadLiveEdit：函数段结束，_phase97_default_off_report 到此结束；如果没有这个边界说明，初学者不容易看出默认安全检查范围。

def _phase97_unsafe_target_report() -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，生成危险目标零物理事件证据；如果没有这段函数，终端等危险目标拦截没有审计样本。
    return {"decision": "unsafe_target_rejected", "target": "terminal_like_window", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase97ControlledNotepadLiveEdit：返回危险目标被拒绝证据；如果没有这一行，报告无法证明不安全目标不会收到事件。
# 新增代码+Phase97ControlledNotepadLiveEdit：函数段结束，_phase97_unsafe_target_report 到此结束；如果没有这个边界说明，初学者不容易看出危险目标检查范围。

def _phase97_get_window_field(window: Any, name: str) -> Any:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，统一读取 dict 或对象窗口字段；如果没有这段函数，fake 快照和真实快照字段读取会分裂。
    if isinstance(window, dict):  # 新增代码+Phase97ControlledNotepadLiveEdit：先处理测试和真实快照常见的 dict 窗口；如果没有这一行，注入测试窗口无法被 driver 识别。
        return window.get(name)  # 新增代码+Phase97ControlledNotepadLiveEdit：从字典里读取字段值；如果没有这一行，dict 窗口会被当成空对象导致误拒绝。
    return getattr(window, name, None)  # 新增代码+Phase97ControlledNotepadLiveEdit：从对象属性读取字段值；如果没有这一行，未来真实对象快照无法复用同一 driver。


def _phase97_window_text_blob(window: Any) -> str:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，拼出用于安全判断的窗口身份文本；如果没有这段函数，Notepad/终端判断会散落重复。
    fields = ["app_id", "process_name", "class_name", "title_preview", "title", "window_id"]  # 新增代码+Phase97ControlledNotepadLiveEdit：列出安全判断需要查看的字段；如果没有这一行，某些窗口身份线索可能漏检。
    return " ".join(str(_phase97_get_window_field(window, field) or "") for field in fields).lower()  # 新增代码+Phase97ControlledNotepadLiveEdit：合并并小写窗口字段；如果没有这一行，大小写差异会导致安全窗口被误拒绝或危险窗口漏过。


def _phase97_window_identity(window: Any) -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，生成不含正文的窗口身份摘要；如果没有这段函数，报告可能泄露完整窗口标题或难以审计。
    title = str(_phase97_get_window_field(window, "title_preview") or _phase97_get_window_field(window, "title") or "")  # 新增代码+Phase97ControlledNotepadLiveEdit：读取标题但只用于长度和哈希；如果没有这一行，目标窗口证据缺少标题线索。
    return {"app_id": str(_phase97_get_window_field(window, "app_id") or ""), "process_name": str(_phase97_get_window_field(window, "process_name") or ""), "class_name": str(_phase97_get_window_field(window, "class_name") or ""), "window_id": str(_phase97_get_window_field(window, "window_id") or ""), "pid": _phase97_window_pid(window), "title_length": len(title), "title_sha256_16": _phase97_sha256_16(title)}  # 修改代码+Phase97ControlledNotepadLiveEdit：返回脱敏身份摘要并加入 pid 线索；如果没有这一行，报告无法解释为什么选择或拒绝窗口，也无法审计无 hwnd 场景的进程匹配。


def _phase97_window_pid(window: Any) -> int:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，统一读取 pid/process_id；如果没有这段函数，默认 launcher 和真实 inventory 的进程字段会各读各的。
    value = _phase97_get_window_field(window, "pid") or _phase97_get_window_field(window, "process_id")  # 修改代码+Phase97ControlledNotepadLiveEdit：兼容真实窗口快照的 pid 和 launcher 的 process_id；如果没有这一行，无 hwnd 匹配缺少可靠进程证据。
    try:  # 修改代码+Phase97ControlledNotepadLiveEdit：尝试把动态字段转成整数；如果没有这一行，字符串 pid 会导致比较不稳定。
        return int(value or 0)  # 修改代码+Phase97ControlledNotepadLiveEdit：返回整数 pid；如果没有这一行，进程匹配无法做等值比较。
    except (TypeError, ValueError):  # 修改代码+Phase97ControlledNotepadLiveEdit：捕获缺失或非数字 pid；如果没有这一行，坏快照会让 driver 崩溃。
        return 0  # 修改代码+Phase97ControlledNotepadLiveEdit：无效 pid 按 0 处理；如果没有这一行，调用方没有安全兜底。
# 修改代码+Phase97ControlledNotepadLiveEdit：函数段结束，_phase97_window_pid 到此结束；如果没有这个边界说明，初学者不容易看出进程身份范围。


def _phase97_hwnd_from_window(window: Any) -> int:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，从 window_id 提取 hwnd；如果没有这段函数，SendInput 聚焦事件不知道目标句柄。
    value = str(_phase97_get_window_field(window, "window_id") or "")  # 新增代码+Phase97ControlledNotepadLiveEdit：读取窗口 id 文本；如果没有这一行，句柄解析没有输入来源。
    if value.lower().startswith("hwnd:"):  # 新增代码+Phase97ControlledNotepadLiveEdit：识别项目标准 hwnd:123 格式；如果没有这一行，真实窗口句柄无法转换。
        value = value.split(":", 1)[1]  # 新增代码+Phase97ControlledNotepadLiveEdit：去掉 hwnd 前缀只保留数字；如果没有这一行，int 转换会失败。
    try:  # 新增代码+Phase97ControlledNotepadLiveEdit：尝试把句柄文本转为整数；如果没有这一行，异常会让安全拒绝路径崩溃。
        return int(value)  # 新增代码+Phase97ControlledNotepadLiveEdit：返回整数 hwnd；如果没有这一行，前台切换事件无法定位窗口。
    except (TypeError, ValueError):  # 新增代码+Phase97ControlledNotepadLiveEdit：捕获缺失或非数字句柄；如果没有这一行，伪造窗口 id 会抛异常。
        return 0  # 新增代码+Phase97ControlledNotepadLiveEdit：无法解析时返回 0 让真实 sender 失败安全；如果没有这一行，driver 可能带着无效句柄继续。


def _phase97_window_center(window: Any) -> dict[str, int]:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，计算目标窗口中心点；如果没有这段函数，真实输入可能只有前台窗口但没有编辑区焦点。
    rect = _phase97_get_window_field(window, "rect") or {}  # 修改代码+Phase97ControlledNotepadLiveEdit：读取窗口矩形；如果没有这一行，无法从真实 inventory 计算点击位置。
    left = int(rect.get("left", 0) or 0) if isinstance(rect, dict) else 0  # 修改代码+Phase97ControlledNotepadLiveEdit：读取左边界；如果没有这一行，中心点 x 没有基准。
    top = int(rect.get("top", 0) or 0) if isinstance(rect, dict) else 0  # 修改代码+Phase97ControlledNotepadLiveEdit：读取上边界；如果没有这一行，中心点 y 没有基准。
    right = int(rect.get("right", left + 640) or left + 640) if isinstance(rect, dict) else left + 640  # 修改代码+Phase97ControlledNotepadLiveEdit：读取右边界并提供兜底宽度；如果没有这一行，缺 rect 时无法给出安全点击点。
    bottom = int(rect.get("bottom", top + 480) or top + 480) if isinstance(rect, dict) else top + 480  # 修改代码+Phase97ControlledNotepadLiveEdit：读取下边界并提供兜底高度；如果没有这一行，缺 rect 时无法给出安全点击点。
    return {"x": left + max(10, (right - left) // 2), "y": top + max(40, (bottom - top) // 2)}  # 修改代码+Phase97ControlledNotepadLiveEdit：返回窗口内部偏中心点；如果没有这一行，SendInput 文本可能发不到 Notepad 编辑区。
# 修改代码+Phase97ControlledNotepadLiveEdit：函数段结束，_phase97_window_center 到此结束；如果没有这个边界说明，初学者不容易看出点击点范围。


def _phase97_is_forbidden_window(window: Any) -> bool:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，识别终端和安全敏感窗口；如果没有这段函数，文本可能被发到命令行或安全窗口。
    blob = _phase97_window_text_blob(window)  # 新增代码+Phase97ControlledNotepadLiveEdit：读取统一窗口文本；如果没有这一行，危险关键字没有检查对象。
    forbidden_tokens = ("powershell", "cmd.exe", "command prompt", "windows terminal", "terminal", "consolewindowclass", "security", "credential", "password", "uac", "defender", "login", "captcha")  # 新增代码+Phase97ControlledNotepadLiveEdit：定义本 driver 必须零事件拒绝的目标线索；如果没有这一行，终端和安全窗口可能漏过。
    return any(token in blob for token in forbidden_tokens)  # 新增代码+Phase97ControlledNotepadLiveEdit：命中任一危险线索就拒绝；如果没有这一行，危险窗口不会被统一拦截。


def _phase97_is_controlled_notepad_window(window: Any, target_file: Path) -> bool:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，验证窗口必须是 Notepad 且带 Phase97 目标文件线索；如果没有这段函数，driver 可能把文本发给错误应用。
    blob = _phase97_window_text_blob(window)  # 新增代码+Phase97ControlledNotepadLiveEdit：读取统一窗口文本；如果没有这一行，Notepad 和标题线索无法判断。
    if _phase97_is_forbidden_window(window):  # 新增代码+Phase97ControlledNotepadLiveEdit：先拒绝终端和安全敏感窗口；如果没有这一行，危险窗口可能因为标题碰巧含 notepad 被放行。
        return False  # 新增代码+Phase97ControlledNotepadLiveEdit：危险窗口必须零事件拒绝；如果没有这一行，拒绝判断不会生效。
    notepad_like = bool("notepad.exe" in blob or "notepad" in blob or "notepad" in str(_phase97_get_window_field(window, "class_name") or "").lower())  # 新增代码+Phase97ControlledNotepadLiveEdit：要求进程或类名像 Notepad；如果没有这一行，任意窗口只要标题含文件名就可能被写入。
    target_hint = bool(target_file.name.lower() in blob)  # 修改代码+Phase97ControlledNotepadLiveEdit：必须命中本次唯一目标文件名；如果没有这一行，旧 Phase97 Notepad 窗口会被误当成当前目标。
    return bool(notepad_like and target_hint)  # 新增代码+Phase97ControlledNotepadLiveEdit：只有 Notepad 身份和目标文件线索都满足才放行；如果没有这一行，双条件安全门无法汇总。


def _phase97_snapshot_windows(snapshot: Any) -> list[Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，从不同快照形态取窗口列表；如果没有这段函数，真实 probe 和 fake probe 可能不兼容。
    if isinstance(snapshot, dict):  # 新增代码+Phase97ControlledNotepadLiveEdit：支持字典快照；如果没有这一行，测试或未来 JSON 快照无法读取。
        return list(snapshot.get("windows") or [])  # 新增代码+Phase97ControlledNotepadLiveEdit：返回字典里的 windows 列表；如果没有这一行，字典快照会被当成空。
    return list(getattr(snapshot, "windows", []) or [])  # 新增代码+Phase97ControlledNotepadLiveEdit：返回对象快照里的 windows 列表；如果没有这一行，WindowsWindowInventorySnapshot 无法使用。


def _phase97_window_key(window: Any) -> str:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，提取窗口硬身份键；如果没有这段函数，启动前后窗口去重会散落重复。
    window_id = str(_phase97_get_window_field(window, "window_id") or "")  # 修改代码+Phase97ControlledNotepadLiveEdit：优先读取 window_id；如果没有这一行，hwnd 场景缺少最稳身份。
    if window_id:  # 修改代码+Phase97ControlledNotepadLiveEdit：有 window_id 时直接使用；如果没有这一行，真实窗口会退到较弱 pid。
        return f"window_id:{window_id}"  # 修改代码+Phase97ControlledNotepadLiveEdit：返回 window_id 键；如果没有这一行，baseline 无法识别同一个窗口。
    pid = _phase97_window_pid(window)  # 修改代码+Phase97ControlledNotepadLiveEdit：缺 window_id 时读取 pid；如果没有这一行，部分 fake/未来快照无法形成身份。
    return f"pid:{pid}" if pid else ""  # 修改代码+Phase97ControlledNotepadLiveEdit：返回 pid 键或空键；如果没有这一行，调用方无法区分无身份窗口。
# 修改代码+Phase97ControlledNotepadLiveEdit：函数段结束，_phase97_window_key 到此结束；如果没有这个边界说明，初学者不容易看出窗口键范围。


def _phase97_controlled_window_keys(window_probe: Any, target_file: Path) -> set[str]:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，记录启动前已有的同名受控 Notepad 窗口；如果没有这段函数，真实 Notepad 单实例会让标题匹配和旧窗口混淆。
    snapshot = window_probe.snapshot()  # 修改代码+Phase97ControlledNotepadLiveEdit：读取当前窗口快照；如果没有这一行，baseline 没有事实来源。
    keys: set[str] = set()  # 修改代码+Phase97ControlledNotepadLiveEdit：准备保存窗口身份键；如果没有这一行，无法累计已有窗口。
    for candidate in _phase97_snapshot_windows(snapshot):  # 修改代码+Phase97ControlledNotepadLiveEdit：遍历当前窗口；如果没有这一行，baseline 永远为空。
        if _phase97_is_controlled_notepad_window(candidate, target_file):  # 修改代码+Phase97ControlledNotepadLiveEdit：只记录同目标名的受控 Notepad；如果没有这一行，不相关窗口会误挡新目标。
            key = _phase97_window_key(candidate)  # 修改代码+Phase97ControlledNotepadLiveEdit：提取窗口键；如果没有这一行，baseline 无法用于比较。
            if key:  # 修改代码+Phase97ControlledNotepadLiveEdit：只保存非空键；如果没有这一行，空键会让所有未知窗口互相误伤。
                keys.add(key)  # 修改代码+Phase97ControlledNotepadLiveEdit：加入 baseline 集合；如果没有这一行，启动前窗口不会被排除。
    return keys  # 修改代码+Phase97ControlledNotepadLiveEdit：返回已有目标窗口键；如果没有这一行，driver 拿不到 baseline。
# 修改代码+Phase97ControlledNotepadLiveEdit：函数段结束，_phase97_controlled_window_keys 到此结束；如果没有这个边界说明，初学者不容易看出 baseline 范围。


def _phase97_same_window_identity(left: Any, right: Any) -> bool:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，比较两次复核是否还是同一个窗口；如果没有这段函数，焦点漂移无法被识别。
    left_id = str(_phase97_get_window_field(left, "window_id") or "")  # 新增代码+Phase97ControlledNotepadLiveEdit：读取第一次窗口 id；如果没有这一行，窗口匹配没有稳定键。
    right_id = str(_phase97_get_window_field(right, "window_id") or "")  # 新增代码+Phase97ControlledNotepadLiveEdit：读取复核窗口 id；如果没有这一行，窗口匹配没有比较对象。
    if left_id and right_id:  # 新增代码+Phase97ControlledNotepadLiveEdit：优先使用 hwnd/window_id 比较；如果没有这一行，标题相似窗口可能被误当成同一窗口。
        return left_id == right_id  # 新增代码+Phase97ControlledNotepadLiveEdit：同一窗口 id 才算匹配；如果没有这一行，复核无法阻断窗口替换。
    left_pid = _phase97_window_pid(left)  # 修改代码+Phase97ControlledNotepadLiveEdit：读取启动窗口进程 id；如果没有这一行，无 hwnd 时只能靠标题猜测目标。
    right_pid = _phase97_window_pid(right)  # 修改代码+Phase97ControlledNotepadLiveEdit：读取复核窗口进程 id；如果没有这一行，无法确认当前窗口是不是刚启动的 Notepad。
    baseline_keys = set(_phase97_get_window_field(left, "baseline_window_keys") or [])  # 修改代码+Phase97ControlledNotepadLiveEdit：读取启动前已有窗口键；如果没有这一行，Windows 11 Notepad 单实例 pid 不一致时无法安全兼容。
    right_key = _phase97_window_key(right)  # 修改代码+Phase97ControlledNotepadLiveEdit：读取复核候选窗口键；如果没有这一行，无法判断候选是否是启动后新窗口。
    if not baseline_keys and right_key:  # 修改代码+Phase97ControlledNotepadLiveEdit：启动前没有同名窗口时接受首个带硬身份的唯一文件名候选；如果没有这一行，Windows 11 Notepad 单实例 pid 不一致会误失败。
        return True  # 修改代码+Phase97ControlledNotepadLiveEdit：把唯一文件名候选交给外层安全 Notepad 校验；如果没有这一行，真实 live edit 无法兼容 Notepad 转发启动。
    if baseline_keys and right_key and right_key not in baseline_keys:  # 修改代码+Phase97ControlledNotepadLiveEdit：只接受启动后新出现的受控窗口；如果没有这一行，旧同名窗口可能被误匹配。
        return True  # 修改代码+Phase97ControlledNotepadLiveEdit：新窗口可作为默认 launcher 的真实目标；如果没有这一行，Notepad 单实例场景会被过严 pid 规则拒绝。
    if left_pid and right_pid:  # 修改代码+Phase97ControlledNotepadLiveEdit：没有 baseline 新窗口证据时再比较 pid；如果没有这一行，fake 和非单实例场景缺少硬身份兜底。
        return left_pid == right_pid  # 修改代码+Phase97ControlledNotepadLiveEdit：同一进程才算同一目标；如果没有这一行，多 Notepad 场景会有漂移风险。
    return False  # 修改代码+Phase97ControlledNotepadLiveEdit：既没有共同 window_id 又没有共同 pid 时拒绝；如果没有这一行，标题相似的窗口可能被误当作安全目标。


def _phase97_recheck_controlled_target(window_probe: Any, expected_window: Any, target_file: Path) -> Any | None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，输入前和保存前重新确认目标窗口；如果没有这段函数，窗口切换后仍可能继续发送。
    snapshot = window_probe.snapshot()  # 新增代码+Phase97ControlledNotepadLiveEdit：读取当前窗口快照；如果没有这一行，复查只会相信启动时的旧信息。
    for candidate in _phase97_snapshot_windows(snapshot):  # 新增代码+Phase97ControlledNotepadLiveEdit：遍历当前可见窗口；如果没有这一行，无法寻找仍存在的目标窗口。
        if _phase97_same_window_identity(expected_window, candidate) and _phase97_is_controlled_notepad_window(candidate, target_file):  # 新增代码+Phase97ControlledNotepadLiveEdit：同时要求同一窗口和仍然安全；如果没有这一行，窗口漂移或标题变更不会被阻断。
            return candidate  # 新增代码+Phase97ControlledNotepadLiveEdit：返回复核通过的当前窗口；如果没有这一行，后续发送拿不到最新窗口身份。
    return None  # 新增代码+Phase97ControlledNotepadLiveEdit：没有安全匹配时返回 None；如果没有这一行，失败路径无法明确零事件退出。


def _phase97_uia_bounds(value: Any) -> dict[str, int]:  # 新增代码+Phase97DriverClosureEvidence：函数段开始，清洗 UIA bounds 为整数矩形；如果没有这段函数，真实 UIA provider 的动态坐标会让观察摘要不稳定。
    source = dict(value) if isinstance(value, dict) else {}  # 新增代码+Phase97DriverClosureEvidence：只接受 dict bounds；如果没有这一行，坏 provider 输出可能打断真实观察。
    left = _phase97_safe_int(source.get("left"))  # 新增代码+Phase97DriverClosureEvidence：读取左边界；如果没有这一行，控件位置缺少 x 起点。
    top = _phase97_safe_int(source.get("top"))  # 新增代码+Phase97DriverClosureEvidence：读取上边界；如果没有这一行，控件位置缺少 y 起点。
    right = _phase97_safe_int(source.get("right")) if source.get("right") is not None else left + _phase97_safe_int(source.get("width"))  # 修改代码+Phase97DriverClosureEvidence：读取或计算右边界；如果没有这一行，bounds 可能只有宽度却没有右边界。
    bottom = _phase97_safe_int(source.get("bottom")) if source.get("bottom") is not None else top + _phase97_safe_int(source.get("height"))  # 修改代码+Phase97DriverClosureEvidence：读取或计算下边界；如果没有这一行，bounds 可能只有高度却没有下边界。
    width = max(0, _phase97_safe_int(source.get("width"), right - left))  # 新增代码+Phase97DriverClosureEvidence：读取或计算宽度并防负数；如果没有这一行，融合层无法判断控件是否有尺寸。
    height = max(0, _phase97_safe_int(source.get("height"), bottom - top))  # 新增代码+Phase97DriverClosureEvidence：读取或计算高度并防负数；如果没有这一行，融合层无法判断控件是否可定位。
    return {"left": left, "top": top, "right": max(right, left + width), "bottom": max(bottom, top + height), "width": width, "height": height}  # 新增代码+Phase97DriverClosureEvidence：返回标准矩形；如果没有这一行，后续 UIA 观察字段会漂移。
# 新增代码+Phase97DriverClosureEvidence：函数段结束，_phase97_uia_bounds 到此结束；如果没有这个边界说明，初学者不容易看出坐标清洗范围。


def _phase97_collect_uia_nodes(tree: Any, limit: int = 120) -> list[dict[str, Any]]:  # 新增代码+Phase97DriverClosureEvidence：函数段开始，把真实 UIA 树压成脱敏扁平节点；如果没有这段函数，Phase97 要么没有 UIA 证据，要么可能泄露编辑区文本。
    nodes: list[dict[str, Any]] = []  # 新增代码+Phase97DriverClosureEvidence：准备扁平节点容器；如果没有这一行，递归读取没有存放结果的位置。
    def visit(node: Any) -> None:  # 新增代码+Phase97DriverClosureEvidence：内部函数段开始，递归读取单个 UIA 节点；如果没有这段函数，嵌套控件树无法转换成列表。
        if len(nodes) >= int(limit):  # 新增代码+Phase97DriverClosureEvidence：达到节点上限就停止；如果没有这一行，大窗口 UIA 树可能让报告过长。
            return  # 新增代码+Phase97DriverClosureEvidence：超过上限直接返回；如果没有这一行，递归仍会继续消耗时间和 token。
        source = dict(node) if isinstance(node, dict) else {}  # 新增代码+Phase97DriverClosureEvidence：清洗节点对象；如果没有这一行，坏节点会让字段读取异常。
        role = str(source.get("role", "") or "")  # 新增代码+Phase97DriverClosureEvidence：读取控件角色；如果没有这一行，后续无法判断是否有可编辑控件。
        class_name = str(source.get("class_name", "") or "")  # 新增代码+Phase97DriverClosureEvidence：读取控件类名；如果没有这一行，Edit 类控件无法作为定位线索。
        nodes.append({"node_id": str(source.get("node_id", len(nodes))), "name": "", "role": role, "automation_id": "", "class_name": class_name, "bounds": _phase97_uia_bounds(source.get("bounds")), "enabled": bool(source.get("enabled", True)), "clickable": bool(source.get("clickable", False)), "editable": bool(source.get("editable", False) or "edit" in role.lower() or "edit" in class_name.lower())})  # 新增代码+Phase97DriverClosureEvidence：追加脱敏节点且不保留 name 文本；如果没有这一行，UIA 证据可能把 Notepad 正文写进报告。
        for child in list(source.get("children", []) or []):  # 新增代码+Phase97DriverClosureEvidence：遍历子节点；如果没有这一行，深层编辑控件不会进入观察证据。
            visit(child)  # 新增代码+Phase97DriverClosureEvidence：递归处理子节点；如果没有这一行，UIA 树只能看到根节点。
    visit(tree)  # 新增代码+Phase97DriverClosureEvidence：从根节点开始收集；如果没有这一行，nodes 会一直为空。
    return nodes  # 新增代码+Phase97DriverClosureEvidence：返回脱敏扁平节点；如果没有这一行，观察适配器拿不到 UIA 摘要。
# 新增代码+Phase97DriverClosureEvidence：函数段结束，_phase97_collect_uia_nodes 到此结束；如果没有这个边界说明，初学者不容易看出 UIA 脱敏范围。


class _Phase97ControlledNotepadUiaRuntime:  # 新增代码+Phase97DriverClosureEvidence：类段开始，为 Phase97 受控 Notepad 提供专用 UIA 观察；如果没有这个类，默认 Phase57 UIA runtime 会拒绝普通 Notepad 而导致真实报告缺 UIA 证据。
    def __init__(self, target_file: Path, provider: Any | None = None) -> None:  # 新增代码+Phase97DriverClosureEvidence：函数段开始，保存目标文件和可注入 provider；如果没有这段函数，UIA 安全判断不知道本次 Notepad 文件名。
        self.target_file = Path(target_file)  # 新增代码+Phase97DriverClosureEvidence：保存受控目标文件路径；如果没有这一行，普通 Notepad 和本次受控 Notepad 无法区分。
        self.provider = provider  # 新增代码+Phase97DriverClosureEvidence：保存可选 UIA provider；如果没有这一行，单测或未来依赖注入无法替换真实 PowerShell provider。
    # 新增代码+Phase97DriverClosureEvidence：函数段结束，_Phase97ControlledNotepadUiaRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _provider(self) -> Any:  # 新增代码+Phase97DriverClosureEvidence：函数段开始，懒加载真实 PowerShell UIA provider；如果没有这段函数，导入模块时会过早绑定 Windows 依赖。
        if self.provider is None:  # 新增代码+Phase97DriverClosureEvidence：只在未注入 provider 时创建默认 provider；如果没有这一行，测试注入会被覆盖。
            try:  # 修改代码+Phase97DriverClosureEvidence：优先按仓库根包路径导入 UIA provider；如果没有这一行，start_oauth_agent 在不同工作目录下可能导入失败。
                from learning_agent.computer_use_mcp_v2.windows_runtime.real_uia_locator import PowerShellUiaTreeProvider  # 修改代码+Phase97DriverClosureEvidence：导入真实 UIA provider；如果没有这一行，Phase97 无法读取真实控件树。
            except ModuleNotFoundError as error:  # 修改代码+Phase97DriverClosureEvidence：捕获包根路径不存在的情况；如果没有这一行，真实终端从 learning_agent 目录启动时可能直接失败。
                if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.real_uia_locator"}:  # 修改代码+Phase97DriverClosureEvidence：只兜底包路径问题；如果没有这一行，provider 内部真实依赖缺失会被错误掩盖。
                    raise  # 修改代码+Phase97DriverClosureEvidence：重新抛出真实内部依赖错误；如果没有这一行，排查时会把内部 bug 误认为路径兜底成功。
                from computer_use_mcp_v2.windows_runtime.real_uia_locator import PowerShellUiaTreeProvider  # 修改代码+Phase97DriverClosureEvidence：按 learning_agent 内部包路径兜底导入；如果没有这一行，可见终端验收可能拿不到 UIA provider。
            self.provider = PowerShellUiaTreeProvider()  # 新增代码+Phase97DriverClosureEvidence：创建 provider 实例；如果没有这一行，observe_window 没有真实 UIA 来源。
        return self.provider  # 新增代码+Phase97DriverClosureEvidence：返回 provider；如果没有这一行，调用方拿不到读取入口。
    # 新增代码+Phase97DriverClosureEvidence：函数段结束，_Phase97ControlledNotepadUiaRuntime._provider 到此结束；如果没有这个边界说明，初学者不容易看出懒加载范围。

    def _failure(self, reason: str) -> dict[str, Any]:  # 新增代码+Phase97DriverClosureEvidence：函数段开始，构造 UIA 失败摘要；如果没有这段函数，失败路径字段会漂移。
        return {"captured": False, "real_uia_tree": False, "safe_window_only": True, "safe_window_reason": str(reason), "flat_nodes": [], "node_count": 0, "bounds_available": False, "clickable_count": 0, "editable_count": 0, "sensitive_text_filtered": 0, "semantic_locator_available": True, "raw_text_included": False, "backend": "phase97_controlled_notepad_uia", "reason": str(reason)}  # 新增代码+Phase97DriverClosureEvidence：返回统一失败结构；如果没有这一行，融合层无法稳定判断 UIA 不可用。
    # 新增代码+Phase97DriverClosureEvidence：函数段结束，_Phase97ControlledNotepadUiaRuntime._failure 到此结束；如果没有这个边界说明，初学者不容易看出失败结构范围。

    def observe_window(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase97DriverClosureEvidence：函数段开始，只读取本次受控 Notepad 的 UIA 树；如果没有这段函数，Phase97 无法证明动作前后有语义观察。
        safe_window = dict(window or {})  # 新增代码+Phase97DriverClosureEvidence：复制窗口输入避免污染调用方；如果没有这一行，后续补字段可能改到外部快照。
        if not _phase97_is_controlled_notepad_window(safe_window, self.target_file):  # 新增代码+Phase97DriverClosureEvidence：先确认窗口仍是本次受控 Notepad；如果没有这一行，UIA 读取可能越界到用户其它窗口。
            return self._failure("Phase97 只允许读取本次受控 Notepad 目标窗口。")  # 新增代码+Phase97DriverClosureEvidence：拒绝非受控窗口；如果没有这一行，安全边界不可审计。
        provider_result = self._provider().read_window_tree(safe_window)  # 新增代码+Phase97DriverClosureEvidence：调用真实 provider 读取控件树；如果没有这一行，UIA 证据不会发生。
        if not bool(provider_result.get("captured")):  # 新增代码+Phase97DriverClosureEvidence：检查 provider 是否成功；如果没有这一行，空树也可能误报 UIA 可用。
            return self._failure(str(provider_result.get("reason", "Phase97 UIA provider 未读取到控件树。")))  # 新增代码+Phase97DriverClosureEvidence：返回 provider 失败原因；如果没有这一行，排查不知道为什么没有 UIA。
        flat_nodes = _phase97_collect_uia_nodes(provider_result.get("tree", {}))  # 新增代码+Phase97DriverClosureEvidence：把真实树压成脱敏节点；如果没有这一行，融合层没有 UIA 节点输入。
        bounds_available = any(bool(node.get("bounds", {}).get("width") or node.get("bounds", {}).get("height")) for node in flat_nodes)  # 新增代码+Phase97DriverClosureEvidence：确认至少一个节点带坐标；如果没有这一行，UIA 是否可定位没有证据。
        return {"captured": bool(flat_nodes), "real_uia_tree": bool(provider_result.get("real_provider_used", False) and flat_nodes), "safe_window_only": True, "safe_window_reason": "目标是 Phase97 本次受控 Notepad 窗口。", "flat_nodes": flat_nodes, "node_count": len(flat_nodes), "bounds_available": bounds_available, "clickable_count": sum(1 for node in flat_nodes if node.get("clickable")), "editable_count": sum(1 for node in flat_nodes if node.get("editable")), "sensitive_text_filtered": 0, "semantic_locator_available": True, "raw_text_included": False, "backend": str(provider_result.get("backend", "powershell_dotnet_uia")), "reason": "Phase97 受控 Notepad UIA 控件树读取成功。"}  # 新增代码+Phase97DriverClosureEvidence：返回脱敏 UIA 摘要；如果没有这一行，Phase8 无法看到 UIA/vision targeting 证据。
    # 新增代码+Phase97DriverClosureEvidence：函数段结束，_Phase97ControlledNotepadUiaRuntime.observe_window 到此结束；如果没有这个边界说明，初学者不容易看出 UIA 读取范围。
# 新增代码+Phase97DriverClosureEvidence：类段结束，_Phase97ControlledNotepadUiaRuntime 到此结束；如果没有这个边界说明，初学者不容易看出它是 Phase97 专用 UIA 适配器。


def _phase97_observation_from_frame(frame: dict[str, Any], *, state_changed_after_action: bool) -> dict[str, Any]:  # 新增代码+Phase97DriverClosureEvidence：函数段开始，把 ObservationFrame 压成 Phase8 需要的观察字段；如果没有这段函数，driver 报告会夹带过大的原始观察对象。
    safe_frame = _phase97_safe_dict(frame)  # 新增代码+Phase97DriverClosureEvidence：清洗观察帧；如果没有这一行，坏观察 provider 输出会让 driver 崩溃。
    observation = {"screenshot_captured": bool(safe_frame.get("screenshot_observation") or safe_frame.get("screenshot_artifact_openable")), "uia_tree_observation": bool(safe_frame.get("uia_tree_observation") or safe_frame.get("uia_or_vision_targeting")), "window_state_observation": bool(safe_frame.get("window_state_observation")), "state_changed_after_action": bool(state_changed_after_action), "raw_text_included": bool(safe_frame.get("raw_text_included")), "observation_frame_model": str(safe_frame.get("model", "")), "screenshot_artifact_openable": bool(safe_frame.get("screenshot_artifact_openable")), "pixel_guard_passed": bool(safe_frame.get("pixel_guard_passed"))}  # 新增代码+Phase97DriverClosureEvidence：只保留脱敏布尔和模型摘要；如果没有这一行，报告可能过大或泄露 UIA 文本。
    return observation  # 新增代码+Phase97DriverClosureEvidence：返回压缩观察摘要；如果没有这一行，调用方拿不到 Phase8 可用字段。
# 新增代码+Phase97DriverClosureEvidence：函数段结束，_phase97_observation_from_frame 到此结束；如果没有这个边界说明，初学者不容易看出观察压缩范围。


class _Phase97DefaultObservationProbe:  # 新增代码+Phase97DriverClosureEvidence：类段开始，默认组合真实截图、受控 UIA 和窗口状态观察；如果没有这个类，生产 driver 成功后仍没有 Phase8 可验的 before/after evidence。
    def __init__(self, window_probe: Any) -> None:  # 新增代码+Phase97DriverClosureEvidence：函数段开始，保存窗口 probe 供 ObservationFrame 复用；如果没有这段函数，观察帧会重新创建独立窗口来源而难以绑定同一目标。
        self.window_probe = window_probe  # 新增代码+Phase97DriverClosureEvidence：保存窗口枚举器；如果没有这一行，观察帧无法复用 driver 的窗口事实来源。
    # 新增代码+Phase97DriverClosureEvidence：函数段结束，_Phase97DefaultObservationProbe.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def observe(self, *, target_window: dict[str, Any], target_file: Path, phase: str, state_changed_after_action: bool = False, real_desktop_touched: bool = False) -> dict[str, Any]:  # 新增代码+Phase97DriverClosureEvidence：函数段开始，执行一次真实只读观察并返回脱敏摘要；如果没有这段函数，driver 无法自动产出前后观察证据。
        _ = phase  # 新增代码+Phase97DriverClosureEvidence：保留阶段参数供调试和未来扩展；如果没有这一行，读者会以为 phase 被遗漏。
        try:  # 新增代码+Phase97DriverClosureEvidence：捕获真实 provider 失败并诚实返回 false；如果没有这一行，截图或 UIA 异常会中断 Notepad 清理。
            try:  # 修改代码+Phase97DriverClosureEvidence：优先按仓库根包路径导入观察帧 runtime；如果没有这一行，不同启动目录会影响真实验收。
                from learning_agent.computer_use_mcp_v2.windows_runtime.universal_real_observation import UniversalRealObservationFrameRuntime  # 修改代码+Phase97DriverClosureEvidence：导入统一观察帧 runtime；如果没有这一行，Phase97 会重复造截图/UIA 融合逻辑。
            except ModuleNotFoundError as error:  # 修改代码+Phase97DriverClosureEvidence：捕获仓库根包路径不存在的情况；如果没有这一行，start_oauth_agent 从子目录启动时可能无法观察。
                if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_real_observation"}:  # 修改代码+Phase97DriverClosureEvidence：只兜底包路径问题；如果没有这一行，观察模块内部真实依赖错误会被吞掉。
                    raise  # 修改代码+Phase97DriverClosureEvidence：保留内部依赖错误的真实堆栈；如果没有这一行，bug 会被错误伪装成兜底成功。
                from computer_use_mcp_v2.windows_runtime.universal_real_observation import UniversalRealObservationFrameRuntime  # 修改代码+Phase97DriverClosureEvidence：按 learning_agent 内部包路径兜底导入；如果没有这一行，可见终端验收可能缺 before/after 观察。
            runtime = UniversalRealObservationFrameRuntime(inventory_probe=self.window_probe, uia_runtime=_Phase97ControlledNotepadUiaRuntime(target_file))  # 新增代码+Phase97DriverClosureEvidence：用 Phase97 专用 UIA runtime 组合真实观察帧；如果没有这一行，默认 UIA 安全门会拒绝普通 Notepad。
            frame = runtime.observe(target_hint=target_file.name, real_desktop_touched=real_desktop_touched, target_window=dict(target_window or {}))  # 新增代码+Phase97DriverClosureEvidence：观察绑定到当前受控窗口；如果没有这一行，同名旧窗口可能污染观察证据。
            return _phase97_observation_from_frame(frame, state_changed_after_action=state_changed_after_action)  # 新增代码+Phase97DriverClosureEvidence：返回 Phase8 可读摘要；如果没有这一行，driver 报告会缺少观察字段。
        except Exception as error:  # 新增代码+Phase97DriverClosureEvidence：真实观察异常时转成失败字段；如果没有这一行，清理和报告落盘可能被 provider 异常阻断。
            return {"screenshot_captured": False, "uia_tree_observation": False, "window_state_observation": False, "state_changed_after_action": bool(state_changed_after_action), "raw_text_included": False, "reason": f"phase97_observation_failed:{type(error).__name__}"}  # 新增代码+Phase97DriverClosureEvidence：诚实返回观察失败类型；如果没有这一行，调用方无法知道证据缺口来自观察 provider。
    # 新增代码+Phase97DriverClosureEvidence：函数段结束，_Phase97DefaultObservationProbe.observe 到此结束；如果没有这个边界说明，初学者不容易看出默认观察范围。
# 新增代码+Phase97DriverClosureEvidence：类段结束，_Phase97DefaultObservationProbe 到此结束；如果没有这个边界说明，初学者不容易看出默认观察适配器范围。


def _phase97_sender_kind_from_results(sender: Any, *results: dict[str, Any]) -> str:  # 新增代码+Phase97DriverClosureEvidence：函数段开始，从 sender 结果提取物理派发身份；如果没有这段函数，报告只能看到事件数量而不知道是不是 recording/fake。
    for result in results:  # 新增代码+Phase97DriverClosureEvidence：按发送阶段依次检查返回值；如果没有这一行，文本或保存任一阶段的 sender 身份可能被漏掉。
        kind = str(result.get("sender_kind") or result.get("sender") or "")  # 新增代码+Phase97DriverClosureEvidence：优先读取 sender 明确上报字段；如果没有这一行，生产 WindowsSendInputLowLevelSender 的身份不会进入报告。
        if kind:  # 新增代码+Phase97DriverClosureEvidence：只接受非空身份；如果没有这一行，空字符串会提前返回。
            return kind  # 新增代码+Phase97DriverClosureEvidence：返回 sender 身份；如果没有这一行，调用方无法区分真实和记录器。
    return type(sender).__name__  # 新增代码+Phase97DriverClosureEvidence：没有返回字段时退回类名；如果没有这一行，报告完全缺 sender_kind。
# 新增代码+Phase97DriverClosureEvidence：函数段结束，_phase97_sender_kind_from_results 到此结束；如果没有这个边界说明，初学者不容易看出 sender 身份来源。


def _phase97_sender_is_physical(sender_kind: str, low_level_event_count: int, *results: dict[str, Any]) -> bool:  # 新增代码+Phase97DriverClosureEvidence：函数段开始，判断 sender 是否像真实物理桌面派发；如果没有这段函数，fake/recording sender 可能被事件数误判为真实。
    lowered = str(sender_kind or "").lower()  # 新增代码+Phase97DriverClosureEvidence：统一小写 sender 名称；如果没有这一行，大小写差异会影响判断。
    forbidden = ("fake", "recording", "representative", "dry", "noop", "mock")  # 新增代码+Phase97DriverClosureEvidence：列出不能算真实派发的 sender 线索；如果没有这一行，测试替身可能误过最终矩阵。
    result_ok = all(bool(result.get("ok")) for result in results if result)  # 新增代码+Phase97DriverClosureEvidence：要求每个发送阶段都成功；如果没有这一行，半失败派发也可能被算成真实闭环。
    return bool(low_level_event_count > 0 and result_ok and "sendinput" in lowered and not any(token in lowered for token in forbidden))  # 新增代码+Phase97DriverClosureEvidence：同时要求事件数、成功、SendInput 名称和非 fake；如果没有这一行，真实派发字段会失去可信边界。
# 新增代码+Phase97DriverClosureEvidence：函数段结束，_phase97_sender_is_physical 到此结束；如果没有这个边界说明，初学者不容易看出物理 sender 判断范围。


class _Phase97DefaultNotepadLauncher:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，默认生产 launcher 只负责打开受控目标文件；如果没有这个类，真实 driver 无法启动 Notepad。
    def __init__(self) -> None:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，保存本 launcher 启动的进程句柄；如果没有这段函数，清理时不知道哪个 Notepad 是自己开的。
        self.process: Any | None = None  # 修改代码+Phase97ControlledNotepadLiveEdit：记录 subprocess.Popen 返回的进程对象；如果没有这一行，成功或失败后可能留下测试 Notepad 窗口。
    # 修改代码+Phase97ControlledNotepadLiveEdit：函数段结束，_Phase97DefaultNotepadLauncher.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出进程记录范围。

    def launch(self, target_file: Path) -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，用 subprocess 打开 notepad.exe；如果没有这段函数，生产 driver 没有默认启动动作。
        import subprocess  # 新增代码+Phase97ControlledNotepadLiveEdit：局部导入 subprocess 避免测试导入时提前绑定系统启动器；如果没有这一行，默认启动 Notepad 无法实现。
        self.process = subprocess.Popen(["notepad.exe", str(target_file)])  # 修改代码+Phase97ControlledNotepadLiveEdit：启动 Notepad 并保存进程对象；如果没有这一行，真实 live edit 没有目标窗口来源且无法后续清理。
        return {"app_id": "notepad.exe", "process_name": "notepad.exe", "class_name": "Notepad", "window_id": "", "title_preview": target_file.name, "process_id": getattr(self.process, "pid", 0)}  # 修改代码+Phase97ControlledNotepadLiveEdit：返回最小启动身份供后续快照复核并带进程 id；如果没有这一行，driver 无法继续进行目标验证。

    def cleanup(self) -> dict[str, Any]:  # 修改代码+Phase97DriverClosureEvidence：函数段开始，关闭本 launcher 创建的 Notepad 并返回清理证据；如果没有这段函数，真实验收失败或成功后可能留下窗口且报告缺 cleanup evidence。
        process = self.process  # 修改代码+Phase97ControlledNotepadLiveEdit：取出记录的进程对象；如果没有这一行，后续清理不知道目标是谁。
        if process is None:  # 修改代码+Phase97ControlledNotepadLiveEdit：没有启动过进程时直接返回；如果没有这一行，清理空对象会报错。
            return {"cleanup_completed": True, "host_hidden_or_restored": True, "lock_released": True, "process_was_running": False, "cleanup_mode": "no_process"}  # 修改代码+Phase97DriverClosureEvidence：无进程时仍返回闭环清理事实；如果没有这一行，未启动场景会被误判 cleanup 缺失。
        process_was_running = bool(getattr(process, "poll", lambda: None)() is None)  # 新增代码+Phase97DriverClosureEvidence：记录清理前进程是否仍运行；如果没有这一行，报告无法区分已退出和被关闭。
        cleanup_mode = "already_exited_owned_notepad"  # 修改代码+Phase97DriverClosureEvidence：默认记录进程已自行退出；如果没有这一行，已退出场景会被误写成我们终止了它。
        if getattr(process, "poll", lambda: None)() is None:  # 修改代码+Phase97ControlledNotepadLiveEdit：只在进程仍运行时尝试关闭；如果没有这一行，已退出进程可能被重复操作。
            try:  # 修改代码+Phase97DriverClosureEvidence：先尝试温和终止并等待退出；如果没有这一行，wait 超时会直接丢失后续强制收尾机会。
                process.terminate()  # 修改代码+Phase97ControlledNotepadLiveEdit：请求关闭自己启动的 Notepad；如果没有这一行，窗口会残留并影响下一次目标复核。
                getattr(process, "wait", lambda timeout=None: None)(timeout=3)  # 新增代码+Phase97DriverClosureEvidence：短等进程退出；如果没有这一行，报告可能过早声明 cleanup 完成。
                cleanup_mode = "terminated_owned_notepad"  # 修改代码+Phase97DriverClosureEvidence：记录温和终止成功；如果没有这一行，报告无法区分正常收尾和强制收尾。
            except Exception as first_error:  # 修改代码+Phase97DriverClosureEvidence：捕获 terminate/wait 失败以便继续尝试 kill；如果没有这一行，Notepad 卡住会让验收留下残留窗口。
                kill = getattr(process, "kill", None)  # 修改代码+Phase97DriverClosureEvidence：读取可选 kill 方法；如果没有这一行，无法在温和终止失败后强制收尾。
                if not callable(kill):  # 修改代码+Phase97DriverClosureEvidence：没有 kill 能力时诚实返回失败；如果没有这一行，清理失败可能被误报成功。
                    self.process = None  # 修改代码+Phase97DriverClosureEvidence：清空本地句柄避免重复报同一对象；如果没有这一行，下一次 cleanup 会重复处理旧进程。
                    return {"cleanup_completed": False, "host_hidden_or_restored": True, "lock_released": True, "process_was_running": process_was_running, "cleanup_mode": "terminate_failed_no_kill", "reason": f"terminate_failed:{type(first_error).__name__}"}  # 修改代码+Phase97DriverClosureEvidence：返回无法强制收尾的失败证据；如果没有这一行，Phase8 不知道真实残留风险。
                try:  # 修改代码+Phase97DriverClosureEvidence：温和终止失败后强制关闭本 launcher 拥有的 Notepad；如果没有这一行，真实验收可能被一个残留窗口拖垮。
                    kill()  # 修改代码+Phase97DriverClosureEvidence：强制关闭自己启动的 Notepad 进程；如果没有这一行，卡住的 Notepad 可能继续留在桌面。
                    getattr(process, "wait", lambda timeout=None: None)(timeout=3)  # 修改代码+Phase97DriverClosureEvidence：等待强制关闭完成；如果没有这一行，报告可能早于系统真正释放进程。
                    cleanup_mode = "killed_owned_notepad_after_terminate_failed"  # 修改代码+Phase97DriverClosureEvidence：记录强制收尾路径；如果没有这一行，后续审计无法知道发生过超时兜底。
                except Exception as second_error:  # 修改代码+Phase97DriverClosureEvidence：捕获强制关闭仍失败的情况；如果没有这一行，cleanup 异常会打断报告返回。
                    self.process = None  # 修改代码+Phase97DriverClosureEvidence：清空本地句柄避免重复处理旧对象；如果没有这一行，下一轮 cleanup 可能重复失败。
                    return {"cleanup_completed": False, "host_hidden_or_restored": True, "lock_released": True, "process_was_running": process_was_running, "cleanup_mode": "kill_failed_after_terminate_failed", "reason": f"terminate_failed:{type(first_error).__name__};kill_failed:{type(second_error).__name__}"}  # 修改代码+Phase97DriverClosureEvidence：返回强制收尾失败证据；如果没有这一行，最终矩阵会误以为桌面已干净。
        self.process = None  # 修改代码+Phase97ControlledNotepadLiveEdit：清空进程记录避免重复清理；如果没有这一行，后续 cleanup 可能重复操作旧进程。
        return {"cleanup_completed": True, "host_hidden_or_restored": True, "lock_released": True, "process_was_running": process_was_running, "cleanup_mode": cleanup_mode}  # 新增代码+Phase97DriverClosureEvidence：返回默认 launcher 的清理证据；如果没有这一行，Phase8 无法确认真实 Notepad 已收尾且没有锁残留。
    # 修改代码+Phase97DriverClosureEvidence：函数段结束，_Phase97DefaultNotepadLauncher.cleanup 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。


class _Phase97DefaultVerifier:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，默认验证器读取目标文件内容；如果没有这个类，生产 driver 无法确认 Notepad 是否真的保存。
    def verify(self, target_file: Path, expected_text: str) -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，验证文件存在且内容等于受控文本；如果没有这段函数，保存成功只能相信按键已发送。
        saved_text = target_file.read_text(encoding="utf-8") if target_file.exists() else ""  # 新增代码+Phase97ControlledNotepadLiveEdit：读取保存文件内容；如果没有这一行，无法比较磁盘事实。
        return {"ok": bool(target_file.exists() and saved_text == expected_text), "saved_file_exists": target_file.exists(), "target_file_sha256_16": _phase97_sha256_16(saved_text) if saved_text else "", "expected_text_length": len(expected_text), "expected_text_sha256_16": _phase97_sha256_16(expected_text)}  # 新增代码+Phase97ControlledNotepadLiveEdit：返回脱敏验证摘要；如果没有这一行，报告会缺少文件证据或泄露正文。


class Phase97WindowsNotepadLiveEditDriver:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，实现 Task3 可注入 Windows Notepad live edit driver；如果没有这个类，Phase97 真实编辑路径仍停留在占位失败。
    def __init__(self, launcher: Any | None = None, window_probe: Any | None = None, focuser: Any | None = None, sender: Any | None = None, verifier: Any | None = None, observation_probe: Any | None = None, recheck_attempts: int = 20, recheck_interval_seconds: float = 0.25) -> None:  # 修改代码+Phase97DriverClosureEvidence：函数段开始，允许测试注入桌面依赖、观察依赖并配置窗口复核轮询；如果没有这段函数，单测会被迫启动真实进程或真实 Notepad 启动稍慢就失败。
        self.launcher = launcher if launcher is not None else _Phase97DefaultNotepadLauncher()  # 新增代码+Phase97ControlledNotepadLiveEdit：保存 launcher 或默认 Notepad 启动器；如果没有这一行，driver 无法启动受控文件。
        if window_probe is None:  # 新增代码+Phase97ControlledNotepadLiveEdit：没有注入 probe 时准备真实只读窗口枚举；如果没有这一行，生产 driver 没有复核来源。
            from learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase97ControlledNotepadLiveEdit：局部导入真实窗口 probe；如果没有这一行，默认生产复核无法枚举窗口。
            window_probe = WindowsWindowInventoryProbe()  # 新增代码+Phase97ControlledNotepadLiveEdit：创建真实窗口 probe；如果没有这一行，默认 driver 无法看到 Notepad 窗口。
        self.window_probe = window_probe  # 新增代码+Phase97ControlledNotepadLiveEdit：保存窗口 probe；如果没有这一行，输入前和保存前无法复查目标。
        self.focuser = focuser  # 新增代码+Phase97ControlledNotepadLiveEdit：保存可选 focuser；如果没有这一行，测试无法注入安全聚焦替身。
        if sender is None:  # 新增代码+Phase97ControlledNotepadLiveEdit：没有注入 sender 时准备真实低层发送器；如果没有这一行，生产 driver 没有默认输入通道。
            from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+Phase97ControlledNotepadLiveEdit：局部导入真实 SendInput sender；如果没有这一行，默认生产路径无法触发受控 SendInput。
            sender = WindowsSendInputLowLevelSender()  # 新增代码+Phase97ControlledNotepadLiveEdit：创建真实低层 sender；如果没有这一行，受控文本和保存快捷键没有发送入口。
        self.sender = sender  # 新增代码+Phase97ControlledNotepadLiveEdit：保存 sender；如果没有这一行，driver 无法把事件交给注入或默认发送器。
        self.verifier = verifier if verifier is not None else _Phase97DefaultVerifier()  # 新增代码+Phase97ControlledNotepadLiveEdit：保存 verifier 或默认磁盘验证器；如果没有这一行，保存是否成功无法验证。
        self.observation_probe = observation_probe if observation_probe is not None else _Phase97DefaultObservationProbe(self.window_probe)  # 新增代码+Phase97DriverClosureEvidence：保存动作前后观察探针；如果没有这一行，真实成功报告仍缺 screenshot/UIA/window_state 证据。
        self.recheck_attempts = max(1, int(recheck_attempts or 1))  # 修改代码+Phase97ControlledNotepadLiveEdit：保存复核尝试次数并至少为 1；如果没有这一行，真实窗口启动延迟或坏参数会让复核行为不稳定。
        self.recheck_interval_seconds = max(0.0, float(recheck_interval_seconds or 0.0))  # 修改代码+Phase97ControlledNotepadLiveEdit：保存复核间隔且不允许负数；如果没有这一行，轮询可能忙等或因负数 sleep 崩溃。

    def _fail_report(self, reason: str, expected_text: str, target_file: Path, *, notepad_verified: bool = False, input_rechecked: bool = False, save_rechecked: bool = False, low_level_event_count: int = 0, window: Any | None = None, before_observation: dict[str, Any] | None = None) -> dict[str, Any]:  # 修改代码+Phase97DriverClosureEvidence：函数段开始，统一返回脱敏失败报告并可保留已完成观察；如果没有这段函数，失败路径容易漏字段或泄露文本。
        return {"ok": False, "driver": "phase97_windows_notepad_live_edit_driver", "reason": reason, "notepad_process_verified": bool(notepad_verified), "target_rechecked_before_input": bool(input_rechecked), "target_rechecked_before_save": bool(save_rechecked), "saved_file_exists": target_file.exists(), "real_desktop_touched": bool(low_level_event_count), "low_level_event_count": int(low_level_event_count), "raw_text_included": bool(_phase97_safe_dict(before_observation).get("raw_text_included")), "expected_text_length": len(expected_text), "expected_text_sha256_16": _phase97_sha256_16(expected_text), "target_file": str(target_file), "target_window": _phase97_window_identity(window) if window is not None else {}, "before_observation": _phase97_safe_dict(before_observation), "after_observation": {}, "physical_desktop_dispatch_performed": False, "real_sendinput_dispatch": False, "sender_kind": ""}  # 修改代码+Phase97DriverClosureEvidence：返回不含 expected_text 明文且带闭环字段占位的失败摘要；如果没有这一行，报告无法审计失败点或可能泄露正文。

    def _send_events(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，统一调用低层 sender；如果没有这段函数，发送结果解析会散落在 run 里。
        result = self.sender.send_low_level(events)  # 新增代码+Phase97ControlledNotepadLiveEdit：把事件交给注入或默认 sender；如果没有这一行，文本和保存动作不会发生。
        return dict(result or {})  # 新增代码+Phase97ControlledNotepadLiveEdit：把 sender 结果规整成字典；如果没有这一行，None 结果会让后续字段读取崩溃。

    def _cleanup_launcher(self) -> dict[str, Any]:  # 修改代码+Phase97DriverClosureEvidence：函数段开始，统一清理 launcher 可能启动的外部进程并返回证据；如果没有这段函数，真实 Notepad 可能残留影响下一轮验收。
        cleanup = getattr(self.launcher, "cleanup", None)  # 修改代码+Phase97ControlledNotepadLiveEdit：读取可选 cleanup 方法；如果没有这一行，fake launcher 和默认 launcher 无法用同一入口处理。
        if callable(cleanup):  # 修改代码+Phase97ControlledNotepadLiveEdit：只有 launcher 提供 cleanup 时才调用；如果没有这一行，没有 cleanup 的测试替身会报错。
            try:  # 新增代码+Phase97DriverClosureEvidence：捕获清理异常并写入报告；如果没有这一行，cleanup 失败会让调用方拿不到失败证据。
                result = cleanup()  # 修改代码+Phase97DriverClosureEvidence：执行 launcher 自己的清理逻辑并接收返回证据；如果没有这一行，默认 Notepad 进程不会被收尾。
                evidence = _phase97_safe_dict(result)  # 新增代码+Phase97DriverClosureEvidence：清洗 launcher 返回值；如果没有这一行，None 或坏类型会污染报告。
                evidence.setdefault("cleanup_completed", True)  # 新增代码+Phase97DriverClosureEvidence：无异常时默认清理完成；如果没有这一行，旧 fake launcher 返回 None 会让 cleanup 被误判失败。
                evidence.setdefault("host_hidden_or_restored", True)  # 新增代码+Phase97DriverClosureEvidence：Phase97 当前没有隐藏宿主，报告为无隐藏残留；如果没有这一行，Phase8 会担心宿主状态未恢复。
                evidence.setdefault("lock_released", True)  # 新增代码+Phase97DriverClosureEvidence：Phase97 当前没有持有独立 computer-use lock，报告为无锁残留；如果没有这一行，Phase8 会担心下一轮被锁阻塞。
                return evidence  # 新增代码+Phase97DriverClosureEvidence：返回清理证据；如果没有这一行，报告无法携带 cleanup 字段。
            except Exception as error:  # 新增代码+Phase97DriverClosureEvidence：捕获 launcher cleanup 异常；如果没有这一行，清理失败会变成未结构化异常。
                return {"cleanup_completed": False, "host_hidden_or_restored": False, "lock_released": False, "reason": f"launcher_cleanup_failed:{type(error).__name__}"}  # 新增代码+Phase97DriverClosureEvidence：返回失败证据；如果没有这一行，最终矩阵不知道 cleanup 为什么失败。
        return {"cleanup_completed": True, "host_hidden_or_restored": True, "lock_released": True, "cleanup_mode": "no_launcher_cleanup"}  # 新增代码+Phase97DriverClosureEvidence：无 cleanup 方法时声明无外部进程可清理；如果没有这一行，简单测试替身会缺 cleanup evidence。
    # 修改代码+Phase97DriverClosureEvidence：函数段结束，Phase97WindowsNotepadLiveEditDriver._cleanup_launcher 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。

    def _observe_target(self, target_window: Any, target_file: Path, *, phase: str, state_changed_after_action: bool = False, real_desktop_touched: bool = False) -> dict[str, Any]:  # 新增代码+Phase97DriverClosureEvidence：函数段开始，统一调用动作前后观察探针；如果没有这段函数，run 里会重复处理观察异常和脱敏字段。
        probe = getattr(self, "observation_probe", None)  # 新增代码+Phase97DriverClosureEvidence：读取可注入观察探针；如果没有这一行，测试或生产默认观察来源无法统一。
        if probe is None or not hasattr(probe, "observe"):  # 新增代码+Phase97DriverClosureEvidence：检查观察探针是否可用；如果没有这一行，缺依赖会触发 AttributeError。
            return {"screenshot_captured": False, "uia_tree_observation": False, "window_state_observation": False, "state_changed_after_action": bool(state_changed_after_action), "raw_text_included": False, "reason": "phase97_observation_probe_missing"}  # 新增代码+Phase97DriverClosureEvidence：缺观察探针时诚实返回失败；如果没有这一行，driver 会假装有观察证据。
        observation = probe.observe(target_window=dict(target_window or {}), target_file=target_file, phase=phase, state_changed_after_action=state_changed_after_action, real_desktop_touched=real_desktop_touched)  # 新增代码+Phase97DriverClosureEvidence：调用观察探针并传入绑定目标；如果没有这一行，before/after evidence 不会产生。
        return _phase97_safe_dict(observation)  # 新增代码+Phase97DriverClosureEvidence：清洗观察结果；如果没有这一行，坏观察 provider 输出会打断报告。
    # 新增代码+Phase97DriverClosureEvidence：函数段结束，Phase97WindowsNotepadLiveEditDriver._observe_target 到此结束；如果没有这个边界说明，初学者不容易看出观察调用范围。

    def _wait_for_controlled_target(self, expected_window: Any, target_file: Path) -> Any | None:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，短轮询等待受控 Notepad 窗口稳定出现；如果没有这段函数，真实 Notepad 启动稍慢会被误判成目标漂移。
        for attempt in range(self.recheck_attempts):  # 修改代码+Phase97ControlledNotepadLiveEdit：按配置尝试多次复核；如果没有这一行，真实窗口枚举只有一次机会。
            candidate = _phase97_recheck_controlled_target(self.window_probe, expected_window, target_file)  # 修改代码+Phase97ControlledNotepadLiveEdit：执行一次目标身份复核；如果没有这一行，轮询没有事实来源。
            if candidate is not None:  # 修改代码+Phase97ControlledNotepadLiveEdit：找到安全目标就立即返回；如果没有这一行，成功也会继续等待浪费时间。
                return candidate  # 修改代码+Phase97ControlledNotepadLiveEdit：返回复核通过窗口；如果没有这一行，后续无法发送输入或保存。
            if attempt + 1 < self.recheck_attempts and self.recheck_interval_seconds > 0:  # 修改代码+Phase97ControlledNotepadLiveEdit：失败且还有机会时才等待；如果没有这一行，测试会无意义 sleep 或最后一次也等待。
                time.sleep(self.recheck_interval_seconds)  # 修改代码+Phase97ControlledNotepadLiveEdit：短暂等待窗口 inventory 更新；如果没有这一行，真实 Notepad 窗口可能还没出现就被拒绝。
        return None  # 修改代码+Phase97ControlledNotepadLiveEdit：多次复核仍失败则返回 None；如果没有这一行，失败路径没有明确结果。
    # 修改代码+Phase97ControlledNotepadLiveEdit：函数段结束，Phase97WindowsNotepadLiveEditDriver._wait_for_controlled_target 到此结束；如果没有这个边界说明，初学者不容易看出等待范围。

    def run(self, *, run_root: Path, expected_text: str, target_file: Path) -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，按兼容签名执行受控 Notepad 编辑；如果没有这段函数，合同和测试无法调用真实 driver。
        report: dict[str, Any] = {}  # 新增代码+Phase97DriverClosureEvidence：先准备可被 finally 补充的报告对象；如果没有这一行，早退路径无法注入 cleanup evidence。
        run_root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase97ControlledNotepadLiveEdit：确保运行根目录存在；如果没有这一行，报告或目标文件目录可能缺失。
        target_file.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase97ControlledNotepadLiveEdit：确保受控目标文件目录存在；如果没有这一行，Notepad 启动受控文件可能失败。
        target_file.write_text("", encoding="utf-8") if not target_file.exists() else None  # 新增代码+Phase97ControlledNotepadLiveEdit：预创建受控文件让标题包含目标文件名；如果没有这一行，Notepad 可能打开未保存文档导致标题线索缺失。
        baseline_keys = _phase97_controlled_window_keys(self.window_probe, target_file)  # 修改代码+Phase97ControlledNotepadLiveEdit：启动前记录已有同名受控窗口；如果没有这一行，真实 Notepad 单实例和旧窗口残留会混淆。
        launched_window = self.launcher.launch(target_file)  # 新增代码+Phase97ControlledNotepadLiveEdit：启动或模拟启动 Notepad；如果没有这一行，driver 没有初始目标窗口。
        launched_window = dict(launched_window) if isinstance(launched_window, dict) else {"raw_launched_window": launched_window}  # 修改代码+Phase97ControlledNotepadLiveEdit：把启动身份规整成字典；如果没有这一行，非字典 launcher 返回值无法附加 baseline。
        launched_window["baseline_window_keys"] = sorted(baseline_keys)  # 修改代码+Phase97ControlledNotepadLiveEdit：把 baseline 附到启动身份供后续复核；如果没有这一行，无 hwnd/pid 不一致场景无法安全识别新窗口。
        try:  # 修改代码+Phase97ControlledNotepadLiveEdit：包住目标验证、输入、保存和验证全过程；如果没有这一行，异常或早退时 cleanup 可能不会执行。
            if not _phase97_is_controlled_notepad_window(launched_window, target_file):  # 新增代码+Phase97ControlledNotepadLiveEdit：先验证启动目标必须是受控 Notepad；如果没有这一行，非 Notepad 窗口可能收到输入。
                report = self._fail_report("unsafe_or_wrong_notepad_target", expected_text, target_file, window=launched_window)  # 修改代码+Phase97DriverClosureEvidence：非安全目标零事件拒绝并保留 report 引用；如果没有这一行，危险窗口可能继续执行且 cleanup 字段无法注入。
                return report  # 新增代码+Phase97DriverClosureEvidence：返回同一个可被 finally 补充的报告对象；如果没有这一行，调用方拿不到拒绝结果。
            if self.focuser is not None:  # 新增代码+Phase97ControlledNotepadLiveEdit：如注入 focuser 则先请求聚焦；如果没有这一行，测试无法验证聚焦依赖被安全替换。
                self.focuser.focus(launched_window)  # 新增代码+Phase97ControlledNotepadLiveEdit：调用安全聚焦替身或生产聚焦器；如果没有这一行，目标窗口可能不是前台。
            input_window = self._wait_for_controlled_target(launched_window, target_file)  # 修改代码+Phase97ControlledNotepadLiveEdit：输入前短轮询复查目标身份；如果没有这一行，焦点漂移或启动延迟后仍可能误判。
            if input_window is None:  # 新增代码+Phase97ControlledNotepadLiveEdit：输入前复查失败时停止；如果没有这一行，错误窗口可能收到文本。
                report = self._fail_report("target_recheck_before_input_failed", expected_text, target_file, notepad_verified=True, input_rechecked=False, window=launched_window)  # 修改代码+Phase97DriverClosureEvidence：返回零事件失败报告并保留 report 引用；如果没有这一行，失败点不可审计且 cleanup 字段无法注入。
                return report  # 新增代码+Phase97DriverClosureEvidence：返回同一个可被 finally 补充的报告对象；如果没有这一行，调用方拿不到复查失败结果。
            before_observation = self._observe_target(input_window, target_file, phase="before_action", state_changed_after_action=False, real_desktop_touched=False)  # 新增代码+Phase97DriverClosureEvidence：动作前读取截图/UIA/窗口状态；如果没有这一行，报告无法证明先观察再输入。
            center = _phase97_window_center(input_window)  # 修改代码+Phase97ControlledNotepadLiveEdit：计算 Notepad 窗口中心点击点；如果没有这一行，真实输入可能没有编辑区焦点。
            text_events = [{"type": "set_foreground", "hwnd": _phase97_hwnd_from_window(input_window)}, {"type": "mouse_move", "x": center["x"], "y": center["y"]}, {"type": "mouse_down", "button": "left"}, {"type": "mouse_up", "button": "left"}, {"type": "clipboard_text", "text": expected_text, "text_length": len(expected_text), "text_sha256_16": _phase97_sha256_16(expected_text)}]  # 修改代码+Phase97ControlledNotepadLiveEdit：构造聚焦、点击编辑区和受控剪贴板粘贴事件；如果没有这一行，Notepad 不会稳定收到完整固定验收文本。
            text_result = self._send_events(text_events)  # 新增代码+Phase97ControlledNotepadLiveEdit：发送受控文本事件；如果没有这一行，保存文件不会包含 expected_text。
            text_count = int(text_result.get("low_level_event_count", len(text_events)) or 0)  # 新增代码+Phase97ControlledNotepadLiveEdit：记录文本阶段低层事件数；如果没有这一行，失败报告无法说明副作用范围。
            save_window = self._wait_for_controlled_target(input_window, target_file)  # 修改代码+Phase97ControlledNotepadLiveEdit：保存前短轮询复查目标身份；如果没有这一行，Ctrl+S 可能发到漂移后的错误窗口或因瞬时枚举缺口误失败。
            if save_window is None:  # 新增代码+Phase97ControlledNotepadLiveEdit：保存前复查失败时停止；如果没有这一行，错误窗口可能收到保存快捷键。
                report = self._fail_report("target_recheck_before_save_failed", expected_text, target_file, notepad_verified=True, input_rechecked=True, save_rechecked=False, low_level_event_count=text_count, window=input_window, before_observation=before_observation)  # 修改代码+Phase97DriverClosureEvidence：返回已输入但未保存的失败报告且保留动作前观察；如果没有这一行，停止点不可审计。
                return report  # 新增代码+Phase97DriverClosureEvidence：返回同一个可被 finally 补充的报告对象；如果没有这一行，调用方拿不到保存前复查失败结果。
            save_events = [{"type": "set_foreground", "hwnd": _phase97_hwnd_from_window(save_window)}, {"type": "key_down", "key": "ctrl"}, {"type": "key_down", "key": "s"}, {"type": "key_up", "key": "s"}, {"type": "key_up", "key": "ctrl"}]  # 修改代码+Phase97ControlledNotepadLiveEdit：使用真实 sender 已支持的 key_down/key_up 事件表达 Ctrl+S；如果没有这一行，保存快捷键不会被真实后端执行。
            save_result = self._send_events(save_events)  # 新增代码+Phase97ControlledNotepadLiveEdit：发送保存快捷键事件；如果没有这一行，保存动作不会发生。
            save_count = int(save_result.get("low_level_event_count", len(save_events)) or 0)  # 新增代码+Phase97ControlledNotepadLiveEdit：记录保存阶段低层事件数；如果没有这一行，报告无法说明保存副作用范围。
            verification = dict(self.verifier.verify(target_file, expected_text))  # 新增代码+Phase97ControlledNotepadLiveEdit：验证目标文件是否保存为受控文本；如果没有这一行，发送快捷键和磁盘事实会脱节。
            ok = bool(verification.get("ok"))  # 新增代码+Phase97ControlledNotepadLiveEdit：读取验证是否成功；如果没有这一行，driver 无法决定最终结果。
            total_event_count = int(text_count + save_count)  # 新增代码+Phase97DriverClosureEvidence：汇总文本和保存阶段的低层事件数；如果没有这一行，物理派发判断没有统一计数。
            sender_kind = _phase97_sender_kind_from_results(self.sender, text_result, save_result)  # 新增代码+Phase97DriverClosureEvidence：读取 sender 明确身份；如果没有这一行，最终矩阵无法区分真实 SendInput 和记录器。
            physical_dispatch = _phase97_sender_is_physical(sender_kind, total_event_count, text_result, save_result)  # 新增代码+Phase97DriverClosureEvidence：判断是否真实物理桌面派发；如果没有这一行，事件数量可能把 fake sender 误判为真实。
            after_observation = self._observe_target(save_window, target_file, phase="after_action", state_changed_after_action=ok, real_desktop_touched=bool(total_event_count))  # 新增代码+Phase97DriverClosureEvidence：动作后再次观察并标记验证到的状态变化；如果没有这一行，报告无法证明执行后有复查。
            raw_text_included = bool(before_observation.get("raw_text_included") or after_observation.get("raw_text_included"))  # 新增代码+Phase97DriverClosureEvidence：汇总观察字段是否泄露原文；如果没有这一行，新增观察可能绕过脱敏门禁。
            report = {"ok": ok, "driver": "phase97_windows_notepad_live_edit_driver", "reason": "" if ok else "saved_file_verification_failed", "notepad_process_verified": True, "target_rechecked_before_input": True, "target_rechecked_before_save": True, "saved_file_exists": bool(verification.get("saved_file_exists", target_file.exists())), "real_desktop_touched": bool(total_event_count), "low_level_event_count": total_event_count, "raw_text_included": raw_text_included, "expected_text_length": len(expected_text), "expected_text_sha256_16": _phase97_sha256_16(expected_text), "target_file": str(target_file), "target_file_sha256_16": str(verification.get("target_file_sha256_16", "")), "target_window": _phase97_window_identity(save_window), "before_observation": before_observation, "after_observation": after_observation, "physical_desktop_dispatch_performed": physical_dispatch, "real_sendinput_dispatch": physical_dispatch, "sender_kind": sender_kind}  # 修改代码+Phase97DriverClosureEvidence：返回脱敏成功或验证失败报告并带 Phase8 闭环字段；如果没有这一行，调用方拿不到 Task3 driver 结果。
            return report  # 新增代码+Phase97DriverClosureEvidence：返回同一个可被 finally 补充 cleanup 的报告；如果没有这一行，最终结果不会交给调用方。
        finally:  # 修改代码+Phase97ControlledNotepadLiveEdit：无论成功、失败或异常都清理 launcher；如果没有这一行，真实 Notepad 进程可能残留。
            cleanup_evidence = self._cleanup_launcher()  # 修改代码+Phase97DriverClosureEvidence：调用统一清理入口并接收证据；如果没有这一行，默认 launcher 的 cleanup 不会被执行且报告缺清理事实。
            if isinstance(report, dict):  # 新增代码+Phase97DriverClosureEvidence：只在已有报告对象时补字段；如果没有这一行，异常路径可能因为 report 类型问题二次失败。
                report["cleanup_evidence"] = cleanup_evidence  # 新增代码+Phase97DriverClosureEvidence：把 cleanup evidence 写回返回对象；如果没有这一行，Phase8 会正确拒绝缺清理证据的真实报告。


class Phase97RealNotepadLiveEditDriverPlaceholder:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，放置真实 Notepad 驱动占位符；如果没有这个类，未实现真实路径时可能误用不受控默认动作。
    def run(self, *, run_root: Path, expected_text: str, target_file: Path) -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，提供与未来真实驱动一致的入口；如果没有这一行，合同无法在 Task3 平滑替换真实驱动。
        _ = (run_root, expected_text, target_file)  # 新增代码+Phase97ControlledNotepadLiveEdit：明确占位符不使用这些参数；如果没有这一行，读者可能误以为这里已经执行真实编辑。
        return {"ok": False, "driver": "phase97_real_notepad_driver_placeholder", "reason": "phase97_real_driver_not_implemented_in_task2", "notepad_process_verified": False, "target_rechecked_before_input": False, "target_rechecked_before_save": False, "saved_file_exists": False, "real_desktop_touched": False, "raw_text_included": False}  # 新增代码+Phase97ControlledNotepadLiveEdit：安全失败且不触碰桌面；如果没有这一行，真实路径未实现时可能误报成功。
    # 新增代码+Phase97ControlledNotepadLiveEdit：函数段结束，Phase97RealNotepadLiveEditDriverPlaceholder.run 到此结束；如果没有这个边界说明，初学者不容易看出占位执行范围。
# 新增代码+Phase97ControlledNotepadLiveEdit：类段结束，Phase97RealNotepadLiveEditDriverPlaceholder 到此结束；如果没有这个边界说明，初学者不容易看出真实驱动还只是占位。

def _phase97_report_raw_hidden(report_without_path: dict[str, Any], raw_prompt_text: str | None) -> bool:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，检查报告里没有用户原始 prompt；如果没有这段函数，隐私门禁没有统一事实检查。
    if not raw_prompt_text:  # 新增代码+Phase97ControlledNotepadLiveEdit：没有原始文本时按无泄露处理；如果没有这一行，默认调用会被空值误伤。
        return True  # 新增代码+Phase97ControlledNotepadLiveEdit：返回无泄露；如果没有这一行，未传 prompt 的正常路径可能被误判失败。
    serialized = json.dumps(report_without_path, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase97ControlledNotepadLiveEdit：序列化报告用于扫描；如果没有这一行，嵌套字段里的泄露可能漏检。
    return raw_prompt_text not in serialized  # 新增代码+Phase97ControlledNotepadLiveEdit：确认精确原文不在报告中；如果没有这一行，用户敏感 prompt 可能被长期写入 artifact。
# 新增代码+Phase97ControlledNotepadLiveEdit：函数段结束，_phase97_report_raw_hidden 到此结束；如果没有这个边界说明，初学者不容易看出脱敏检查范围。

def _phase97_safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase97NotepadClosureEvidence：函数段开始，把外部驱动证据安全整理成字典；如果没有这段函数，坏类型报告会让 evidence builder 直接崩溃。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+Phase97NotepadClosureEvidence：只复制字典，其他类型按空证据处理；如果没有这一行，字符串或 None 可能被误当成真实闭环证据。
# 新增代码+Phase97NotepadClosureEvidence：函数段结束，_phase97_safe_dict 到此结束；如果没有这个边界说明，初学者不容易看出输入清洗范围。

def _phase97_safe_int(value: Any, default: int = 0) -> int:  # 修改代码+Phase97DriverClosureEvidence：函数段开始，把低层事件数量或坐标整理成整数；如果没有这段函数，JSON 字符串数字或坏值会打断最终矩阵接入。
    try:  # 新增代码+Phase97NotepadClosureEvidence：尝试按整数解释驱动上报值；如果没有这一行，合法的字符串数字不能被兼容。
        return int(value if value is not None else default)  # 修改代码+Phase97DriverClosureEvidence：空值按调用方默认值处理；如果没有这一行，缺少事件数或坐标会被异常而不是失败原因表达。
    except (TypeError, ValueError):  # 新增代码+Phase97NotepadClosureEvidence：捕获非数字或坏类型；如果没有这一行，损坏证据会让测试中断而不是被拒绝。
        return int(default)  # 修改代码+Phase97DriverClosureEvidence：坏事件数或坐标按默认值处理；如果没有这一行，错误报告可能绕过低层事件门禁或坐标清洗会崩溃。
# 修改代码+Phase97DriverClosureEvidence：函数段结束，_phase97_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出数字清洗范围。

def _phase97_phase8_observation(source: dict[str, Any], include_state_change: bool = False) -> dict[str, Any]:  # 新增代码+Phase97NotepadClosureEvidence：函数段开始，把 Phase97 观察字段转换成 Phase8 观察字段；如果没有这段函数，前后截图/UIA/窗口状态无法进入最终矩阵。
    observation = {"screenshot_captured": bool(source.get("screenshot_captured")), "uia_tree_observation": bool(source.get("uia_tree_observation") or source.get("uia_or_vision_targeting") or source.get("vision_targeting")), "window_state_observation": bool(source.get("window_state_observation"))}  # 新增代码+Phase97NotepadClosureEvidence：只转明确上报的观察证据；如果没有这一行，builder 可能凭空制造“已观察”的假阳性。
    if include_state_change:  # 新增代码+Phase97NotepadClosureEvidence：只给动作后观察补状态变化字段；如果没有这一行，动作前观察会带上没有意义的变化判断。
        observation["state_changed_after_action"] = bool(source.get("state_changed_after_action"))  # 新增代码+Phase97NotepadClosureEvidence：保留动作后状态确实变化的证据；如果没有这一行，空动作也可能被误认为闭环完成。
    return observation  # 新增代码+Phase97NotepadClosureEvidence：返回 Phase8 可读的观察结构；如果没有这一行，最终矩阵拿不到转换后的观察证据。
# 新增代码+Phase97NotepadClosureEvidence：函数段结束，_phase97_phase8_observation 到此结束；如果没有这个边界说明，初学者不容易看出观察转换范围。

def _phase97_phase8_target_identity(target_window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase97NotepadClosureEvidence：函数段开始，把 Phase97 目标窗口摘要转换成 Phase8 目标身份；如果没有这段函数，最终矩阵无法确认动作绑定到哪个窗口。
    return {"window_id": str(target_window.get("window_id") or target_window.get("hwnd") or ""), "hwnd": str(target_window.get("hwnd") or ""), "process_name": str(target_window.get("process_name") or ""), "app_id": str(target_window.get("app_id") or ""), "title_preview": str(target_window.get("title_preview") or target_window.get("title") or "")}  # 新增代码+Phase97NotepadClosureEvidence：保留窗口 ID、进程和标题线索但不写正文；如果没有这一行，Phase8 目标身份会缺少可复核锚点。
# 新增代码+Phase97NotepadClosureEvidence：函数段结束，_phase97_phase8_target_identity 到此结束；如果没有这个边界说明，初学者不容易看出目标身份转换范围。

def build_phase97_notepad_real_desktop_closure_evidence(report: dict[str, Any] | None, representative_acceptance: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase97NotepadClosureEvidence：函数段开始，把 Phase97 Notepad 成功报告接成 Phase8 最终矩阵闭环证据；如果没有这段函数，真实 Notepad 结果会停在局部合同里。
    safe_report = _phase97_safe_dict(report)  # 新增代码+Phase97NotepadClosureEvidence：先复制并清洗 Phase97 报告；如果没有这一行，None 或坏类型会导致 builder 崩溃。
    target_window = _phase97_safe_dict(safe_report.get("target_window"))  # 新增代码+Phase97NotepadClosureEvidence：读取驱动明确上报的目标窗口；如果没有这一行，动作目标身份无法进入 Phase8。
    before_observation = _phase97_safe_dict(safe_report.get("before_observation"))  # 新增代码+Phase97NotepadClosureEvidence：读取动作前观察证据；如果没有这一行，builder 无法证明先观察再输入。
    after_observation = _phase97_safe_dict(safe_report.get("after_observation"))  # 新增代码+Phase97NotepadClosureEvidence：读取动作后观察证据；如果没有这一行，builder 无法证明执行后状态被复查。
    cleanup_evidence = _phase97_safe_dict(safe_report.get("cleanup_evidence"))  # 新增代码+Phase97NotepadClosureEvidence：读取清理证据；如果没有这一行，真实桌面可能被污染却仍被误过。
    report_success = bool(safe_report.get("passed") and safe_report.get("real_notepad_edit_executed") and safe_report.get("notepad_process_verified") and safe_report.get("target_rechecked_before_input") and safe_report.get("target_rechecked_before_save") and safe_report.get("saved_file_verified") and safe_report.get("raw_text_hidden"))  # 新增代码+Phase97NotepadClosureEvidence：把 Phase97 局部合同成功条件收束成一个事实；如果没有这一行，失败报告也可能被拼成 Phase8 通过证据。
    representatives = _phase97_safe_dict(representative_acceptance)  # 新增代码+Phase97NotepadClosureEvidence：复制外部代表应用验收汇总；如果没有这一行，Paint/Calculator/Browser 的上游验收无法一起进入最终矩阵。
    representatives["notepad"] = report_success  # 新增代码+Phase97NotepadClosureEvidence：用 Phase97 真实 Notepad 成功覆盖 Notepad 代表结果；如果没有这一行，Notepad 场景仍会停留在旧代表样本。
    return {"target_identity": _phase97_phase8_target_identity(target_window), "before_observation": _phase97_phase8_observation(before_observation), "action": {"physical_desktop_dispatch_performed": bool(report_success and safe_report.get("physical_desktop_dispatch_performed")), "real_sendinput_dispatch": bool(report_success and safe_report.get("real_sendinput_dispatch")), "sender_kind": str(safe_report.get("sender_kind") or ""), "low_level_event_count": _phase97_safe_int(safe_report.get("low_level_event_count"))}, "after_observation": _phase97_phase8_observation(after_observation, include_state_change=True), "verification": {"verified": report_success, "decision": "accepted" if report_success else "rejected", "reason": str(safe_report.get("driver_reason") or "phase97_notepad_contract")}, "cleanup": {"cleanup_completed": bool(cleanup_evidence.get("cleanup_completed")), "host_hidden_or_restored": bool(cleanup_evidence.get("host_hidden_or_restored")), "lock_released": bool(cleanup_evidence.get("lock_released"))}, "representative_acceptance": representatives, "target_identity_rechecked_before_each_action": bool(safe_report.get("target_rechecked_before_input") and safe_report.get("target_rechecked_before_save")), "script_artifact_route_blocked": bool(not safe_report.get("uncontrolled_actions_expanded")), "uncontrolled_high_risk_actions_allowed": bool(safe_report.get("uncontrolled_actions_expanded"))}  # 新增代码+Phase97NotepadClosureEvidence：返回 Phase8 校验器需要的完整闭环形状；如果没有这一行，最终矩阵无法判断 Notepad 是否真的成熟。
# 新增代码+Phase97NotepadClosureEvidence：函数段结束，build_phase97_notepad_real_desktop_closure_evidence 到此结束；如果没有这个边界说明，初学者不容易看出 Phase97 接入最终矩阵的范围。

def run_phase97_controlled_notepad_live_edit_contract(base_dir: str | Path | None = None, real_edit: bool | None = None, allow_real_gate: bool | None = None, notepad_driver: Any | None = None, require_injected_driver: bool = False, raw_prompt_text: str | None = None) -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，运行 Phase97 总合同入口；如果没有这段函数，测试和真实终端没有统一事实来源。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase97ControlledNotepadLiveEdit：选择隔离运行目录；如果没有这一行，多次运行可能互相污染。
    root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase97ControlledNotepadLiveEdit：创建运行目录；如果没有这一行，目标文件或报告写入会失败。
    raw_prompt_for_scan = str(raw_prompt_text or "")  # 修改代码+Phase97ControlledNotepadLiveEdit：把可选 raw_prompt_text 规整成字符串再参与 in 检查；如果没有这一行，main 默认不传 prompt 时会因为 None in 字符串直接崩溃。
    target_file = root / f"phase97_controlled_notepad_live_edit_{int(time.time() * 1000)}.txt"  # 修改代码+Phase97ControlledNotepadLiveEdit：每次使用唯一受控目标文件名；如果没有这一行，旧 Notepad 同名标题可能干扰真实窗口复核。
    expected_text = _phase97_expected_text()  # 新增代码+Phase97ControlledNotepadLiveEdit：生成不含 raw prompt 的受控文本；如果没有这一行，编辑内容没有统一安全来源。
    requested = _phase97_request_real_edit(real_edit)  # 新增代码+Phase97ControlledNotepadLiveEdit：判断本次是否请求真实编辑；如果没有这一行，默认路径和显式路径会混淆。
    gate_enabled = _phase97_real_gate_enabled(allow_real_gate)  # 新增代码+Phase97ControlledNotepadLiveEdit：判断真实编辑允许门是否开启；如果没有这一行，真实桌面动作缺少第二道确认。
    default_report = _phase97_default_off_report()  # 新增代码+Phase97ControlledNotepadLiveEdit：收集默认关闭零事件证据；如果没有这一行，默认安全字段没有事实来源。
    unsafe_report = _phase97_unsafe_target_report()  # 新增代码+Phase97ControlledNotepadLiveEdit：收集危险目标零事件证据；如果没有这一行，危险目标字段没有事实来源。
    default_zero = bool(default_report.get("low_level_event_count") == 0 and not default_report.get("real_desktop_touched"))  # 新增代码+Phase97ControlledNotepadLiveEdit：确认默认关闭没有物理事件；如果没有这一行，默认安全值无法量化。
    unsafe_zero = bool(unsafe_report.get("low_level_event_count") == 0 and not unsafe_report.get("real_desktop_touched"))  # 新增代码+Phase97ControlledNotepadLiveEdit：确认危险目标没有物理事件；如果没有这一行，危险拦截值无法量化。
    driver_report: dict[str, Any] = {"ok": False, "driver": "not_requested", "reason": "real_notepad_edit_not_requested", "real_desktop_touched": False, "raw_text_included": False}  # 新增代码+Phase97ControlledNotepadLiveEdit：准备默认不执行驱动报告；如果没有这一行，默认关闭路径可能缺少统一字段。
    if requested and gate_enabled and notepad_driver is not None:  # 新增代码+Phase97ControlledNotepadLiveEdit：只有请求门、允许门、注入驱动同时存在才执行编辑；如果没有这一行，单元测试可能误触真实桌面。
        driver_report = dict(notepad_driver.run(run_root=root, expected_text=expected_text, target_file=target_file))  # 新增代码+Phase97ControlledNotepadLiveEdit：调用注入驱动写受控文本；如果没有这一行，显式 fake 路径不会保存文件。
    elif requested and gate_enabled and require_injected_driver:  # 新增代码+Phase97ControlledNotepadLiveEdit：要求注入驱动但没有提供时安全失败；如果没有这一行，fake-only 硬门可能被绕过并走默认真实驱动。
        driver_report = {"ok": False, "driver": "missing_injected_driver", "reason": "require_injected_driver_without_driver", "real_desktop_touched": False, "raw_text_included": False}  # 新增代码+Phase97ControlledNotepadLiveEdit：记录缺少注入驱动且不触桌面；如果没有这一行，失败原因不清楚。
    elif requested and gate_enabled:  # 新增代码+Phase97ControlledNotepadLiveEdit：真实请求且允许但没有注入驱动时走占位真实驱动；如果没有这一行，Task3 前的 CLI 真实路径边界不明确。
        driver_report = Phase97WindowsNotepadLiveEditDriver().run(run_root=root, expected_text=expected_text, target_file=target_file)  # 修改代码+Phase97ControlledNotepadLiveEdit：双门打开且无注入 driver 时使用 Task3 真实 driver；如果没有这一行，生产默认路径会继续停在旧占位失败而无法 live edit。
    elif requested and not gate_enabled:  # 新增代码+Phase97ControlledNotepadLiveEdit：请求真实编辑但允许门关闭时拒绝；如果没有这一行，用户可能误以为单门即可触发真实桌面。
        driver_report = {"ok": False, "driver": "gate_rejected", "reason": "phase97_real_gate_disabled", "real_desktop_touched": False, "raw_text_included": False}  # 新增代码+Phase97ControlledNotepadLiveEdit：记录 gate 拒绝且不触桌面；如果没有这一行，拒绝原因不清楚。
    saved_text = target_file.read_text(encoding="utf-8") if target_file.exists() else ""  # 新增代码+Phase97ControlledNotepadLiveEdit：读取保存文件用于验证；如果没有这一行，saved_file_verified 可能只相信驱动自报。
    saved_file_verified = bool(target_file.exists() and saved_text == expected_text and driver_report.get("ok"))  # 新增代码+Phase97ControlledNotepadLiveEdit：确认文件存在且内容等于受控文本；如果没有这一行，保存成功可能脱离磁盘证据。
    real_executed = bool(requested and gate_enabled and driver_report.get("ok") and saved_file_verified)  # 修改代码+Phase97ControlledNotepadLiveEdit：任意成功 driver 加文件验证都算真实编辑执行；如果没有这一行，默认 Phase97WindowsNotepadLiveEditDriver 路径即使成功也永远不能通过。
    real_desktop_touched = bool(driver_report.get("real_desktop_touched"))  # 修改代码+Phase97ControlledNotepadLiveEdit：保留驱动上报的任何真实桌面触达，即使保存失败或合同不通过；如果没有这一行，失败/半执行副作用会被 real_executed 掩盖。
    report_path = root / "reports" / "phase97_controlled_notepad_live_edit_report.json"  # 新增代码+Phase97ControlledNotepadLiveEdit：定义合同报告路径；如果没有这一行，验收失败时很难找到证据。
    report_without_raw_check: dict[str, Any] = {"marker": PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_MARKER, "ok_token": PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK_TOKEN, "model": PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_MODEL, "real_notepad_live_edit_env": PHASE97_REAL_NOTEPAD_LIVE_EDIT_ENV, "real_notepad_live_edit_request_env": PHASE97_REAL_NOTEPAD_LIVE_EDIT_REQUEST_ENV, "real_edit_requested": requested, "real_enable_gate_required": True, "real_enable_gate_passed": gate_enabled, "require_injected_driver": bool(require_injected_driver), "target_file": str(target_file), "target_file_sha256_16": _phase97_sha256_16(saved_text) if saved_text else "", "default_off_zero_physical_events": default_zero, "unsafe_target_zero_physical_events": unsafe_zero, "real_notepad_edit_executed": real_executed, "notepad_process_verified": bool(driver_report.get("notepad_process_verified")), "target_rechecked_before_input": bool(driver_report.get("target_rechecked_before_input")), "target_rechecked_before_save": bool(driver_report.get("target_rechecked_before_save")), "saved_file_verified": saved_file_verified, "real_desktop_touched": real_desktop_touched, "uncontrolled_actions_expanded": PHASE97_UNCONTROLLED_ACTIONS_EXPANDED, "driver": str(driver_report.get("driver", "")), "driver_ok": bool(driver_report.get("ok")), "driver_reason": str(driver_report.get("reason", "")), "default_off_report": default_report, "unsafe_report": unsafe_report}  # 修改代码+Phase97ControlledNotepadLiveEdit：构造报告主体并保留失败驱动的桌面触达事实；如果没有这一行，测试和 CLI 会丢失半执行副作用证据。
    report_without_raw_check.update({"target_window": _phase97_safe_dict(driver_report.get("target_window")), "before_observation": _phase97_safe_dict(driver_report.get("before_observation")), "after_observation": _phase97_safe_dict(driver_report.get("after_observation")), "cleanup_evidence": _phase97_safe_dict(driver_report.get("cleanup_evidence")), "physical_desktop_dispatch_performed": bool(driver_report.get("physical_desktop_dispatch_performed")), "real_sendinput_dispatch": bool(driver_report.get("real_sendinput_dispatch")), "sender_kind": str(driver_report.get("sender_kind") or ""), "low_level_event_count": _phase97_safe_int(driver_report.get("low_level_event_count"))})  # 新增代码+Phase97NotepadClosureEvidence：把驱动明确上报的 Phase8 关键证据并入脱敏报告；如果没有这一行，builder 无法从合同报告恢复真实闭环字段。
    raw_text_hidden = bool(_phase97_report_raw_hidden(report_without_raw_check, raw_prompt_for_scan) and not driver_report.get("raw_text_included") and (not raw_prompt_for_scan or raw_prompt_for_scan not in expected_text))  # 修改代码+Phase97ControlledNotepadLiveEdit：用已规整字符串做脱敏检查且允许空 prompt；如果没有这一行，默认 main 会崩溃或把空 prompt 误判成泄露。
    passed = bool(default_zero and unsafe_zero and raw_text_hidden and not PHASE97_UNCONTROLLED_ACTIONS_EXPANDED and ((not requested and not report_without_raw_check["real_desktop_touched"]) or (requested and gate_enabled and real_executed and report_without_raw_check["notepad_process_verified"] and report_without_raw_check["target_rechecked_before_input"] and report_without_raw_check["target_rechecked_before_save"] and saved_file_verified)))  # 新增代码+Phase97ControlledNotepadLiveEdit：汇总合同通过条件；如果没有这一行，main 无法用退出码表达成功或失败。
    report = dict(report_without_raw_check, raw_text_hidden=raw_text_hidden, passed=passed, report_path=str(report_path))  # 新增代码+Phase97ControlledNotepadLiveEdit：补齐最终报告字段；如果没有这一行，调用方拿不到 passed、脱敏和报告路径。
    atomic_write_json(report_path, report)  # 新增代码+Phase97ControlledNotepadLiveEdit：原子写入报告文件；如果没有这一行，验收和排查没有落盘证据。
    return report  # 新增代码+Phase97ControlledNotepadLiveEdit：返回合同报告；如果没有这一行，测试和 CLI 无法读取结果。
# 新增代码+Phase97ControlledNotepadLiveEdit：函数段结束，run_phase97_controlled_notepad_live_edit_contract 到此结束；如果没有这个边界说明，初学者不容易看出总合同范围。

def phase97_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，把报告转成真实终端稳定 token 行；如果没有这段函数，验收器必须解析复杂 JSON。
    ok_token = f" {PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK_TOKEN}" if bool(report.get("passed")) else ""  # 修改代码+Phase97ControlledNotepadLiveEdit：仅在合同通过时输出 OK token；如果没有这一行，失败报告会误带成功锚点。
    return f"{PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_MARKER}{ok_token} default_off_zero_physical_events={_phase97_bool_token(report.get('default_off_zero_physical_events'))} unsafe_target_zero_physical_events={_phase97_bool_token(report.get('unsafe_target_zero_physical_events'))} real_enable_gate_required={_phase97_bool_token(report.get('real_enable_gate_required'))} real_notepad_edit_executed={_phase97_bool_token(report.get('real_notepad_edit_executed'))} notepad_process_verified={_phase97_bool_token(report.get('notepad_process_verified'))} target_rechecked_before_input={_phase97_bool_token(report.get('target_rechecked_before_input'))} target_rechecked_before_save={_phase97_bool_token(report.get('target_rechecked_before_save'))} saved_file_verified={_phase97_bool_token(report.get('saved_file_verified'))} raw_text_hidden={_phase97_bool_token(report.get('raw_text_hidden'))} real_desktop_touched={_phase97_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase97_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 修改代码+Phase97ControlledNotepadLiveEdit：返回失败无 OK、成功有 OK 的固定 token 行；如果没有这一行，CLI 会把失败和成功混在同一个锚点里。
# 新增代码+Phase97ControlledNotepadLiveEdit：函数段结束，phase97_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。

def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，提供命令行入口；如果没有这段函数，真实终端无法直接运行 Phase97 合同。
    _ = argv  # 新增代码+Phase97ControlledNotepadLiveEdit：保留 argv 扩展位；如果没有这一行，读者可能误以为命令参数被遗漏。
    report = run_phase97_controlled_notepad_live_edit_contract()  # 新增代码+Phase97ControlledNotepadLiveEdit：按环境门运行合同；如果没有这一行，CLI 不会产生验收事实。
    print(phase97_cli_line(report))  # 新增代码+Phase97ControlledNotepadLiveEdit：打印稳定 token 行；如果没有这一行，验收脚本无法快速匹配成功条件。
    print(json.dumps({"report_path": report.get("report_path"), "passed": report.get("passed"), "real_notepad_edit_executed": report.get("real_notepad_edit_executed")}, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase97ControlledNotepadLiveEdit：打印短 JSON 方便定位报告；如果没有这一行，失败时不容易找到证据文件。
    print(PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_MARKER)  # 新增代码+Phase97ControlledNotepadLiveEdit：单独打印 marker 方便人工观察；如果没有这一行，可见终端里阶段标识不够醒目。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase97ControlledNotepadLiveEdit：按 passed 返回退出码；如果没有这一行，失败合同可能被自动化误判为成功。
# 新增代码+Phase97ControlledNotepadLiveEdit：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。

__all__ = ["DEFAULT_PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_ROOT", "PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_MARKER", "PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_MODEL", "PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK_TOKEN", "PHASE97_REAL_NOTEPAD_LIVE_EDIT_ENV", "PHASE97_REAL_NOTEPAD_LIVE_EDIT_REQUEST_ENV", "PHASE97_UNCONTROLLED_ACTIONS_EXPANDED", "Phase97RealNotepadLiveEditDriverPlaceholder", "main", "phase97_cli_line", "run_phase97_controlled_notepad_live_edit_contract"]  # 新增代码+Phase97ControlledNotepadLiveEdit：限定公开导出名称；如果没有这一行，from module import * 会暴露内部 helper。
__all__.append("Phase97WindowsNotepadLiveEditDriver")  # 新增代码+Phase97ControlledNotepadLiveEdit：把 Task3 driver 加入模块公开导出；如果没有这一行，from module import * 会漏掉新真实驱动。
__all__.append("build_phase97_notepad_real_desktop_closure_evidence")  # 新增代码+Phase97NotepadClosureEvidence：公开 Phase97 到 Phase8 的证据 builder；如果没有这一行，后续矩阵和验收控制器无法稳定导入它。

if __name__ == "__main__":  # 新增代码+Phase97ControlledNotepadLiveEdit：允许直接运行模块自检；如果没有这一行，python 文件方式不会启动合同。
    raise SystemExit(main())  # 新增代码+Phase97ControlledNotepadLiveEdit：使用 main 返回码退出；如果没有这一行，命令行状态不明确。
