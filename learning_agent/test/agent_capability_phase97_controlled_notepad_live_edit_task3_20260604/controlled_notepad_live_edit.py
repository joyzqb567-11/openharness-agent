"""Phase97 受控 Notepad 现场编辑合同。"""  # 新增代码+Phase97ControlledNotepadLiveEdit：说明本模块只负责 Phase97 的受控 Notepad 编辑合同；如果没有这一行，读者很难快速区分它和旧的 smoke/SendInput 模块。
from __future__ import annotations  # 新增代码+Phase97ControlledNotepadLiveEdit：启用延迟类型解析，避免类型标注在导入顺序变化时出错；如果没有这一行，后续前向类型写法更容易在旧解释器行为下失败。

import json  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 JSON 用来写合同报告和检查敏感文本是否泄露；如果没有这一行，报告无法稳定落盘也无法做脱敏扫描。
import os  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 os 用来读取真实 Notepad 执行的双环境门；如果没有这一行，CLI 入口不能按环境变量显式启用真实路径。
import time  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 time 用来生成默认隔离运行目录；如果没有这一行，多次 CLI 运行可能互相覆盖报告。
from pathlib import Path  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 Path 统一处理 Windows 路径；如果没有这一行，目标文件和报告路径会变成脆弱的字符串拼接。
from typing import Any  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 Any 描述动态报告字段；如果没有这一行，公开函数的 JSON 风格返回值边界不清楚。

try:  # 新增代码+Phase97ControlledNotepadLiveEdit：优先按包路径导入项目内原子写文件工具；如果没有这段代码，单元测试和真实终端入口不能共享同一套写报告方式。
    from learning_agent.computer_use.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # 新增代码+Phase97ControlledNotepadLiveEdit：复用现有 Computer Use 运行根目录；如果没有这一行，Phase97 报告落点会和前序阶段割裂。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase97ControlledNotepadLiveEdit：复用原子 JSON 写入，避免半写报告；如果没有这一行，异常中断时可能留下损坏 JSON。
except ModuleNotFoundError as error:  # 新增代码+Phase97ControlledNotepadLiveEdit：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行的导入方式；如果没有这一段，真实终端验收可能因包前缀缺失失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase97ControlledNotepadLiveEdit：只对包路径缺失做 fallback；如果没有这一行，内部真实 bug 可能被误吞。
        raise  # 新增代码+Phase97ControlledNotepadLiveEdit：重新抛出非路径类导入错误；如果没有这一行，底层模块问题会被隐藏成难排查的假兼容。
    from computer_use.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # type: ignore  # 新增代码+Phase97ControlledNotepadLiveEdit：脚本模式下复用现有运行根目录；如果没有这一行，bat 入口无法定位默认报告目录。
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


def _phase97_is_forbidden_window(window: Any) -> bool:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，识别终端和安全敏感窗口；如果没有这段函数，文本可能被发到命令行或安全窗口。
    blob = _phase97_window_text_blob(window)  # 新增代码+Phase97ControlledNotepadLiveEdit：读取统一窗口文本；如果没有这一行，危险关键字没有检查对象。
    forbidden_tokens = ("powershell", "cmd.exe", "command prompt", "windows terminal", "terminal", "consolewindowclass", "security", "credential", "password", "uac", "defender", "login", "captcha")  # 新增代码+Phase97ControlledNotepadLiveEdit：定义本 driver 必须零事件拒绝的目标线索；如果没有这一行，终端和安全窗口可能漏过。
    return any(token in blob for token in forbidden_tokens)  # 新增代码+Phase97ControlledNotepadLiveEdit：命中任一危险线索就拒绝；如果没有这一行，危险窗口不会被统一拦截。


def _phase97_is_controlled_notepad_window(window: Any, target_file: Path) -> bool:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，验证窗口必须是 Notepad 且带 Phase97 目标文件线索；如果没有这段函数，driver 可能把文本发给错误应用。
    blob = _phase97_window_text_blob(window)  # 新增代码+Phase97ControlledNotepadLiveEdit：读取统一窗口文本；如果没有这一行，Notepad 和标题线索无法判断。
    if _phase97_is_forbidden_window(window):  # 新增代码+Phase97ControlledNotepadLiveEdit：先拒绝终端和安全敏感窗口；如果没有这一行，危险窗口可能因为标题碰巧含 notepad 被放行。
        return False  # 新增代码+Phase97ControlledNotepadLiveEdit：危险窗口必须零事件拒绝；如果没有这一行，拒绝判断不会生效。
    notepad_like = bool("notepad.exe" in blob or "notepad" in blob or "notepad" in str(_phase97_get_window_field(window, "class_name") or "").lower())  # 新增代码+Phase97ControlledNotepadLiveEdit：要求进程或类名像 Notepad；如果没有这一行，任意窗口只要标题含文件名就可能被写入。
    target_hint = bool(target_file.name.lower() in blob or "phase97_controlled_notepad_live_edit" in blob)  # 新增代码+Phase97ControlledNotepadLiveEdit：要求标题或身份包含受控 Phase97 文件线索；如果没有这一行，已有其它 Notepad 文档可能被误写。
    return bool(notepad_like and target_hint)  # 新增代码+Phase97ControlledNotepadLiveEdit：只有 Notepad 身份和目标文件线索都满足才放行；如果没有这一行，双条件安全门无法汇总。


def _phase97_snapshot_windows(snapshot: Any) -> list[Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，从不同快照形态取窗口列表；如果没有这段函数，真实 probe 和 fake probe 可能不兼容。
    if isinstance(snapshot, dict):  # 新增代码+Phase97ControlledNotepadLiveEdit：支持字典快照；如果没有这一行，测试或未来 JSON 快照无法读取。
        return list(snapshot.get("windows") or [])  # 新增代码+Phase97ControlledNotepadLiveEdit：返回字典里的 windows 列表；如果没有这一行，字典快照会被当成空。
    return list(getattr(snapshot, "windows", []) or [])  # 新增代码+Phase97ControlledNotepadLiveEdit：返回对象快照里的 windows 列表；如果没有这一行，WindowsWindowInventorySnapshot 无法使用。


def _phase97_same_window_identity(left: Any, right: Any) -> bool:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，比较两次复核是否还是同一个窗口；如果没有这段函数，焦点漂移无法被识别。
    left_id = str(_phase97_get_window_field(left, "window_id") or "")  # 新增代码+Phase97ControlledNotepadLiveEdit：读取第一次窗口 id；如果没有这一行，窗口匹配没有稳定键。
    right_id = str(_phase97_get_window_field(right, "window_id") or "")  # 新增代码+Phase97ControlledNotepadLiveEdit：读取复核窗口 id；如果没有这一行，窗口匹配没有比较对象。
    if left_id and right_id:  # 新增代码+Phase97ControlledNotepadLiveEdit：优先使用 hwnd/window_id 比较；如果没有这一行，标题相似窗口可能被误当成同一窗口。
        return left_id == right_id  # 新增代码+Phase97ControlledNotepadLiveEdit：同一窗口 id 才算匹配；如果没有这一行，复核无法阻断窗口替换。
    left_pid = _phase97_window_pid(left)  # 修改代码+Phase97ControlledNotepadLiveEdit：读取启动窗口进程 id；如果没有这一行，无 hwnd 时只能靠标题猜测目标。
    right_pid = _phase97_window_pid(right)  # 修改代码+Phase97ControlledNotepadLiveEdit：读取复核窗口进程 id；如果没有这一行，无法确认当前窗口是不是刚启动的 Notepad。
    if left_pid and right_pid:  # 修改代码+Phase97ControlledNotepadLiveEdit：只有双方都有 pid 时才走无 hwnd 兼容；如果没有这一行，旧 Notepad 窗口可能凭标题误匹配。
        return left_pid == right_pid  # 修改代码+Phase97ControlledNotepadLiveEdit：同一进程才算同一目标；如果没有这一行，多 Notepad 场景会有漂移风险。
    return False  # 修改代码+Phase97ControlledNotepadLiveEdit：既没有共同 window_id 又没有共同 pid 时拒绝；如果没有这一行，标题相似的窗口可能被误当作安全目标。


def _phase97_recheck_controlled_target(window_probe: Any, expected_window: Any, target_file: Path) -> Any | None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，输入前和保存前重新确认目标窗口；如果没有这段函数，窗口切换后仍可能继续发送。
    snapshot = window_probe.snapshot()  # 新增代码+Phase97ControlledNotepadLiveEdit：读取当前窗口快照；如果没有这一行，复查只会相信启动时的旧信息。
    for candidate in _phase97_snapshot_windows(snapshot):  # 新增代码+Phase97ControlledNotepadLiveEdit：遍历当前可见窗口；如果没有这一行，无法寻找仍存在的目标窗口。
        if _phase97_same_window_identity(expected_window, candidate) and _phase97_is_controlled_notepad_window(candidate, target_file):  # 新增代码+Phase97ControlledNotepadLiveEdit：同时要求同一窗口和仍然安全；如果没有这一行，窗口漂移或标题变更不会被阻断。
            return candidate  # 新增代码+Phase97ControlledNotepadLiveEdit：返回复核通过的当前窗口；如果没有这一行，后续发送拿不到最新窗口身份。
    return None  # 新增代码+Phase97ControlledNotepadLiveEdit：没有安全匹配时返回 None；如果没有这一行，失败路径无法明确零事件退出。


class _Phase97DefaultNotepadLauncher:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，默认生产 launcher 只负责打开受控目标文件；如果没有这个类，真实 driver 无法启动 Notepad。
    def __init__(self) -> None:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，保存本 launcher 启动的进程句柄；如果没有这段函数，清理时不知道哪个 Notepad 是自己开的。
        self.process: Any | None = None  # 修改代码+Phase97ControlledNotepadLiveEdit：记录 subprocess.Popen 返回的进程对象；如果没有这一行，成功或失败后可能留下测试 Notepad 窗口。
    # 修改代码+Phase97ControlledNotepadLiveEdit：函数段结束，_Phase97DefaultNotepadLauncher.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出进程记录范围。

    def launch(self, target_file: Path) -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，用 subprocess 打开 notepad.exe；如果没有这段函数，生产 driver 没有默认启动动作。
        import subprocess  # 新增代码+Phase97ControlledNotepadLiveEdit：局部导入 subprocess 避免测试导入时提前绑定系统启动器；如果没有这一行，默认启动 Notepad 无法实现。
        self.process = subprocess.Popen(["notepad.exe", str(target_file)])  # 修改代码+Phase97ControlledNotepadLiveEdit：启动 Notepad 并保存进程对象；如果没有这一行，真实 live edit 没有目标窗口来源且无法后续清理。
        return {"app_id": "notepad.exe", "process_name": "notepad.exe", "class_name": "Notepad", "window_id": "", "title_preview": target_file.name, "process_id": getattr(self.process, "pid", 0)}  # 修改代码+Phase97ControlledNotepadLiveEdit：返回最小启动身份供后续快照复核并带进程 id；如果没有这一行，driver 无法继续进行目标验证。

    def cleanup(self) -> None:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，关闭本 launcher 创建的 Notepad；如果没有这段函数，真实验收失败或成功后可能留下窗口。
        process = self.process  # 修改代码+Phase97ControlledNotepadLiveEdit：取出记录的进程对象；如果没有这一行，后续清理不知道目标是谁。
        if process is None:  # 修改代码+Phase97ControlledNotepadLiveEdit：没有启动过进程时直接返回；如果没有这一行，清理空对象会报错。
            return  # 修改代码+Phase97ControlledNotepadLiveEdit：无进程无需清理；如果没有这一行，默认关闭路径可能异常。
        if getattr(process, "poll", lambda: None)() is None:  # 修改代码+Phase97ControlledNotepadLiveEdit：只在进程仍运行时尝试关闭；如果没有这一行，已退出进程可能被重复操作。
            process.terminate()  # 修改代码+Phase97ControlledNotepadLiveEdit：请求关闭自己启动的 Notepad；如果没有这一行，窗口会残留并影响下一次目标复核。
        self.process = None  # 修改代码+Phase97ControlledNotepadLiveEdit：清空进程记录避免重复清理；如果没有这一行，后续 cleanup 可能重复操作旧进程。
    # 修改代码+Phase97ControlledNotepadLiveEdit：函数段结束，_Phase97DefaultNotepadLauncher.cleanup 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。


class _Phase97DefaultVerifier:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，默认验证器读取目标文件内容；如果没有这个类，生产 driver 无法确认 Notepad 是否真的保存。
    def verify(self, target_file: Path, expected_text: str) -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，验证文件存在且内容等于受控文本；如果没有这段函数，保存成功只能相信按键已发送。
        saved_text = target_file.read_text(encoding="utf-8") if target_file.exists() else ""  # 新增代码+Phase97ControlledNotepadLiveEdit：读取保存文件内容；如果没有这一行，无法比较磁盘事实。
        return {"ok": bool(target_file.exists() and saved_text == expected_text), "saved_file_exists": target_file.exists(), "target_file_sha256_16": _phase97_sha256_16(saved_text) if saved_text else "", "expected_text_length": len(expected_text), "expected_text_sha256_16": _phase97_sha256_16(expected_text)}  # 新增代码+Phase97ControlledNotepadLiveEdit：返回脱敏验证摘要；如果没有这一行，报告会缺少文件证据或泄露正文。


class Phase97WindowsNotepadLiveEditDriver:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，实现 Task3 可注入 Windows Notepad live edit driver；如果没有这个类，Phase97 真实编辑路径仍停留在占位失败。
    def __init__(self, launcher: Any | None = None, window_probe: Any | None = None, focuser: Any | None = None, sender: Any | None = None, verifier: Any | None = None) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，允许测试注入所有桌面依赖；如果没有这段函数，单测会被迫启动真实进程或 SendInput。
        self.launcher = launcher if launcher is not None else _Phase97DefaultNotepadLauncher()  # 新增代码+Phase97ControlledNotepadLiveEdit：保存 launcher 或默认 Notepad 启动器；如果没有这一行，driver 无法启动受控文件。
        if window_probe is None:  # 新增代码+Phase97ControlledNotepadLiveEdit：没有注入 probe 时准备真实只读窗口枚举；如果没有这一行，生产 driver 没有复核来源。
            from learning_agent.computer_use.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase97ControlledNotepadLiveEdit：局部导入真实窗口 probe；如果没有这一行，默认生产复核无法枚举窗口。
            window_probe = WindowsWindowInventoryProbe()  # 新增代码+Phase97ControlledNotepadLiveEdit：创建真实窗口 probe；如果没有这一行，默认 driver 无法看到 Notepad 窗口。
        self.window_probe = window_probe  # 新增代码+Phase97ControlledNotepadLiveEdit：保存窗口 probe；如果没有这一行，输入前和保存前无法复查目标。
        self.focuser = focuser  # 新增代码+Phase97ControlledNotepadLiveEdit：保存可选 focuser；如果没有这一行，测试无法注入安全聚焦替身。
        if sender is None:  # 新增代码+Phase97ControlledNotepadLiveEdit：没有注入 sender 时准备真实低层发送器；如果没有这一行，生产 driver 没有默认输入通道。
            from learning_agent.computer_use.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+Phase97ControlledNotepadLiveEdit：局部导入真实 SendInput sender；如果没有这一行，默认生产路径无法触发受控 SendInput。
            sender = WindowsSendInputLowLevelSender()  # 新增代码+Phase97ControlledNotepadLiveEdit：创建真实低层 sender；如果没有这一行，受控文本和保存快捷键没有发送入口。
        self.sender = sender  # 新增代码+Phase97ControlledNotepadLiveEdit：保存 sender；如果没有这一行，driver 无法把事件交给注入或默认发送器。
        self.verifier = verifier if verifier is not None else _Phase97DefaultVerifier()  # 新增代码+Phase97ControlledNotepadLiveEdit：保存 verifier 或默认磁盘验证器；如果没有这一行，保存是否成功无法验证。

    def _fail_report(self, reason: str, expected_text: str, target_file: Path, *, notepad_verified: bool = False, input_rechecked: bool = False, save_rechecked: bool = False, low_level_event_count: int = 0, window: Any | None = None) -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，统一返回脱敏失败报告；如果没有这段函数，失败路径容易漏字段或泄露文本。
        return {"ok": False, "driver": "phase97_windows_notepad_live_edit_driver", "reason": reason, "notepad_process_verified": bool(notepad_verified), "target_rechecked_before_input": bool(input_rechecked), "target_rechecked_before_save": bool(save_rechecked), "saved_file_exists": target_file.exists(), "real_desktop_touched": bool(low_level_event_count), "low_level_event_count": int(low_level_event_count), "raw_text_included": False, "expected_text_length": len(expected_text), "expected_text_sha256_16": _phase97_sha256_16(expected_text), "target_file": str(target_file), "target_window": _phase97_window_identity(window) if window is not None else {}}  # 新增代码+Phase97ControlledNotepadLiveEdit：返回不含 expected_text 明文的失败摘要；如果没有这一行，报告无法审计失败点或可能泄露正文。

    def _send_events(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，统一调用低层 sender；如果没有这段函数，发送结果解析会散落在 run 里。
        result = self.sender.send_low_level(events)  # 新增代码+Phase97ControlledNotepadLiveEdit：把事件交给注入或默认 sender；如果没有这一行，文本和保存动作不会发生。
        return dict(result or {})  # 新增代码+Phase97ControlledNotepadLiveEdit：把 sender 结果规整成字典；如果没有这一行，None 结果会让后续字段读取崩溃。

    def _cleanup_launcher(self) -> None:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，统一清理 launcher 可能启动的外部进程；如果没有这段函数，真实 Notepad 可能残留影响下一轮验收。
        cleanup = getattr(self.launcher, "cleanup", None)  # 修改代码+Phase97ControlledNotepadLiveEdit：读取可选 cleanup 方法；如果没有这一行，fake launcher 和默认 launcher 无法用同一入口处理。
        if callable(cleanup):  # 修改代码+Phase97ControlledNotepadLiveEdit：只有 launcher 提供 cleanup 时才调用；如果没有这一行，没有 cleanup 的测试替身会报错。
            cleanup()  # 修改代码+Phase97ControlledNotepadLiveEdit：执行 launcher 自己的清理逻辑；如果没有这一行，默认 Notepad 进程不会被收尾。
    # 修改代码+Phase97ControlledNotepadLiveEdit：函数段结束，Phase97WindowsNotepadLiveEditDriver._cleanup_launcher 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。

    def run(self, *, run_root: Path, expected_text: str, target_file: Path) -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，按兼容签名执行受控 Notepad 编辑；如果没有这段函数，合同和测试无法调用真实 driver。
        run_root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase97ControlledNotepadLiveEdit：确保运行根目录存在；如果没有这一行，报告或目标文件目录可能缺失。
        target_file.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase97ControlledNotepadLiveEdit：确保受控目标文件目录存在；如果没有这一行，Notepad 启动受控文件可能失败。
        target_file.write_text("", encoding="utf-8") if not target_file.exists() else None  # 新增代码+Phase97ControlledNotepadLiveEdit：预创建受控文件让标题包含目标文件名；如果没有这一行，Notepad 可能打开未保存文档导致标题线索缺失。
        launched_window = self.launcher.launch(target_file)  # 新增代码+Phase97ControlledNotepadLiveEdit：启动或模拟启动 Notepad；如果没有这一行，driver 没有初始目标窗口。
        try:  # 修改代码+Phase97ControlledNotepadLiveEdit：包住目标验证、输入、保存和验证全过程；如果没有这一行，异常或早退时 cleanup 可能不会执行。
            if not _phase97_is_controlled_notepad_window(launched_window, target_file):  # 新增代码+Phase97ControlledNotepadLiveEdit：先验证启动目标必须是受控 Notepad；如果没有这一行，非 Notepad 窗口可能收到输入。
                return self._fail_report("unsafe_or_wrong_notepad_target", expected_text, target_file, window=launched_window)  # 新增代码+Phase97ControlledNotepadLiveEdit：非安全目标零事件拒绝；如果没有这一行，危险窗口可能继续执行。
            if self.focuser is not None:  # 新增代码+Phase97ControlledNotepadLiveEdit：如注入 focuser 则先请求聚焦；如果没有这一行，测试无法验证聚焦依赖被安全替换。
                self.focuser.focus(launched_window)  # 新增代码+Phase97ControlledNotepadLiveEdit：调用安全聚焦替身或生产聚焦器；如果没有这一行，目标窗口可能不是前台。
            input_window = _phase97_recheck_controlled_target(self.window_probe, launched_window, target_file)  # 新增代码+Phase97ControlledNotepadLiveEdit：输入前立即复查目标身份；如果没有这一行，焦点漂移后仍会发送文本。
            if input_window is None:  # 新增代码+Phase97ControlledNotepadLiveEdit：输入前复查失败时停止；如果没有这一行，错误窗口可能收到文本。
                return self._fail_report("target_recheck_before_input_failed", expected_text, target_file, notepad_verified=True, input_rechecked=False, window=launched_window)  # 新增代码+Phase97ControlledNotepadLiveEdit：返回零事件失败报告；如果没有这一行，失败点不可审计。
            text_events = [{"type": "set_foreground", "hwnd": _phase97_hwnd_from_window(input_window)}, {"type": "unicode_text", "text": expected_text, "text_length": len(expected_text), "text_sha256_16": _phase97_sha256_16(expected_text)}]  # 新增代码+Phase97ControlledNotepadLiveEdit：构造聚焦和受控 Unicode 文本事件；如果没有这一行，Notepad 不会收到固定验收文本。
            text_result = self._send_events(text_events)  # 新增代码+Phase97ControlledNotepadLiveEdit：发送受控文本事件；如果没有这一行，保存文件不会包含 expected_text。
            text_count = int(text_result.get("low_level_event_count", len(text_events)) or 0)  # 新增代码+Phase97ControlledNotepadLiveEdit：记录文本阶段低层事件数；如果没有这一行，失败报告无法说明副作用范围。
            save_window = _phase97_recheck_controlled_target(self.window_probe, input_window, target_file)  # 新增代码+Phase97ControlledNotepadLiveEdit：保存前立即复查目标身份；如果没有这一行，Ctrl+S 可能发到漂移后的错误窗口。
            if save_window is None:  # 新增代码+Phase97ControlledNotepadLiveEdit：保存前复查失败时停止；如果没有这一行，错误窗口可能收到保存快捷键。
                return self._fail_report("target_recheck_before_save_failed", expected_text, target_file, notepad_verified=True, input_rechecked=True, save_rechecked=False, low_level_event_count=text_count, window=input_window)  # 新增代码+Phase97ControlledNotepadLiveEdit：返回已输入但未保存的失败报告；如果没有这一行，停止点不可审计。
            save_events = [{"type": "set_foreground", "hwnd": _phase97_hwnd_from_window(save_window)}, {"type": "key_down", "key": "ctrl"}, {"type": "key_down", "key": "s"}, {"type": "key_up", "key": "s"}, {"type": "key_up", "key": "ctrl"}]  # 修改代码+Phase97ControlledNotepadLiveEdit：使用真实 sender 已支持的 key_down/key_up 事件表达 Ctrl+S；如果没有这一行，保存快捷键不会被真实后端执行。
            save_result = self._send_events(save_events)  # 新增代码+Phase97ControlledNotepadLiveEdit：发送保存快捷键事件；如果没有这一行，保存动作不会发生。
            save_count = int(save_result.get("low_level_event_count", len(save_events)) or 0)  # 新增代码+Phase97ControlledNotepadLiveEdit：记录保存阶段低层事件数；如果没有这一行，报告无法说明保存副作用范围。
            verification = dict(self.verifier.verify(target_file, expected_text))  # 新增代码+Phase97ControlledNotepadLiveEdit：验证目标文件是否保存为受控文本；如果没有这一行，发送快捷键和磁盘事实会脱节。
            ok = bool(verification.get("ok"))  # 新增代码+Phase97ControlledNotepadLiveEdit：读取验证是否成功；如果没有这一行，driver 无法决定最终结果。
            return {"ok": ok, "driver": "phase97_windows_notepad_live_edit_driver", "reason": "" if ok else "saved_file_verification_failed", "notepad_process_verified": True, "target_rechecked_before_input": True, "target_rechecked_before_save": True, "saved_file_exists": bool(verification.get("saved_file_exists", target_file.exists())), "real_desktop_touched": bool(text_count + save_count), "low_level_event_count": int(text_count + save_count), "raw_text_included": False, "expected_text_length": len(expected_text), "expected_text_sha256_16": _phase97_sha256_16(expected_text), "target_file": str(target_file), "target_file_sha256_16": str(verification.get("target_file_sha256_16", "")), "target_window": _phase97_window_identity(save_window)}  # 新增代码+Phase97ControlledNotepadLiveEdit：返回脱敏成功或验证失败报告；如果没有这一行，调用方拿不到 Task3 driver 结果。
        finally:  # 修改代码+Phase97ControlledNotepadLiveEdit：无论成功、失败或异常都清理 launcher；如果没有这一行，真实 Notepad 进程可能残留。
            self._cleanup_launcher()  # 修改代码+Phase97ControlledNotepadLiveEdit：调用统一清理入口；如果没有这一行，默认 launcher 的 cleanup 不会被执行。


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

def run_phase97_controlled_notepad_live_edit_contract(base_dir: str | Path | None = None, real_edit: bool | None = None, allow_real_gate: bool | None = None, notepad_driver: Any | None = None, require_injected_driver: bool = False, raw_prompt_text: str | None = None) -> dict[str, Any]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，运行 Phase97 总合同入口；如果没有这段函数，测试和真实终端没有统一事实来源。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase97ControlledNotepadLiveEdit：选择隔离运行目录；如果没有这一行，多次运行可能互相污染。
    root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase97ControlledNotepadLiveEdit：创建运行目录；如果没有这一行，目标文件或报告写入会失败。
    raw_prompt_for_scan = str(raw_prompt_text or "")  # 修改代码+Phase97ControlledNotepadLiveEdit：把可选 raw_prompt_text 规整成字符串再参与 in 检查；如果没有这一行，main 默认不传 prompt 时会因为 None in 字符串直接崩溃。
    target_file = root / "phase97_controlled_notepad_live_edit.txt"  # 新增代码+Phase97ControlledNotepadLiveEdit：固定受控目标文件在 base_dir 内；如果没有这一行，驱动可能写到不可控路径。
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

if __name__ == "__main__":  # 新增代码+Phase97ControlledNotepadLiveEdit：允许直接运行模块自检；如果没有这一行，python 文件方式不会启动合同。
    raise SystemExit(main())  # 新增代码+Phase97ControlledNotepadLiveEdit：使用 main 返回码退出；如果没有这一行，命令行状态不明确。
