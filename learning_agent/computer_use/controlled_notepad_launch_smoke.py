"""Phase104 受控 Notepad 真实启动 smoke。"""  # 新增代码+Phase104ControlledNotepadLaunchSmoke：说明本模块只负责短暂真实启动并清理 Notepad；如果没有这行代码，读者容易把它误解成任意应用启动器。
from __future__ import annotations  # 新增代码+Phase104ControlledNotepadLaunchSmoke：启用延迟类型解析；如果没有这行代码，类型注解在导入顺序变化时更容易失败。

import json  # 新增代码+Phase104ControlledNotepadLaunchSmoke：导入 JSON 用于合同报告和 CLI 输出；如果没有这行代码，验收结果无法稳定序列化。
import os  # 新增代码+Phase104ControlledNotepadLaunchSmoke：导入 os 读取双环境门；如果没有这行代码，真实启动无法被显式控制。
import sys  # 新增代码+Phase104ControlledNotepadLaunchSmoke：导入 sys 判断平台；如果没有这行代码，非 Windows 环境可能误尝试启动 Notepad。
import time  # 新增代码+Phase104ControlledNotepadLaunchSmoke：导入 time 生成运行目录和等待超时；如果没有这行代码，多次验收证据可能互相覆盖。
from pathlib import Path  # 新增代码+Phase104ControlledNotepadLaunchSmoke：导入 Path 统一处理 Windows 路径；如果没有这行代码，受控文件路径拼接会更脆弱。
from typing import Any  # 新增代码+Phase104ControlledNotepadLaunchSmoke：导入 Any 描述动态报告字段；如果没有这行代码，公开接口边界不清楚。

try:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：优先按包路径导入项目组件；如果没有这段代码，单元测试和真实终端入口不能共享实现。
    from learning_agent.computer_use.generic_launch_backend import Phase103RecordingLaunchBackend, Phase103SubprocessLaunchBackend, WindowsControlledAppLaunchCandidate  # 修改代码+CompatSlimming：改为从统一通用启动后端复用 Phase103 启动候选；如果没有这一行，删除旧 controlled_app_launch.py 后 Phase104 真实 Notepad smoke 会导入失败。
    from learning_agent.computer_use.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # 新增代码+Phase104ControlledNotepadLaunchSmoke：复用 Computer Use memory 根；如果没有这行代码，报告证据会散落。
    from learning_agent.computer_use.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase104ControlledNotepadLaunchSmoke：复用只读窗口枚举探测真实 Notepad 窗口；如果没有这行代码，真实窗口可见性无法验证。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase104ControlledNotepadLaunchSmoke：复用原子 JSON 写入；如果没有这行代码，验收报告可能半写损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，可见终端可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.generic_launch_backend", "learning_agent.computer_use.persistent_grants", "learning_agent.computer_use.windows_backend", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 修改代码+CompatSlimming：fallback 白名单跟随统一通用启动后端；如果没有这一行，删除旧 controlled_app_launch.py 后脚本模式会把正常路径差异误报成内部错误。
        raise  # 新增代码+Phase104ControlledNotepadLaunchSmoke：重新抛出非路径类导入错误；如果没有这行代码，底层问题会被隐藏。
    from computer_use.generic_launch_backend import Phase103RecordingLaunchBackend, Phase103SubprocessLaunchBackend, WindowsControlledAppLaunchCandidate  # type: ignore  # 修改代码+CompatSlimming：脚本模式从统一启动后端导入 Phase103 候选；如果没有这一行，bat 入口删除旧文件后无法运行 Phase104。
    from computer_use.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # type: ignore  # 新增代码+Phase104ControlledNotepadLaunchSmoke：脚本模式复用默认 memory 根；如果没有这行代码，报告目录无法稳定定位。
    from computer_use.windows_backend import WindowsWindowInventoryProbe  # type: ignore  # 新增代码+Phase104ControlledNotepadLaunchSmoke：脚本模式复用窗口枚举；如果没有这行代码，真实窗口验证无法运行。
    from runtime.files import atomic_write_json  # type: ignore  # 新增代码+Phase104ControlledNotepadLaunchSmoke：脚本模式复用原子写入；如果没有这行代码，报告可能写坏。

PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_MARKER = "PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_READY"  # 新增代码+Phase104ControlledNotepadLaunchSmoke：定义 Phase104 ready marker；如果没有这行代码，真实终端验收没有稳定等待锚点。
PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_OK_TOKEN = "PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_OK"  # 新增代码+Phase104ControlledNotepadLaunchSmoke：定义 Phase104 OK token；如果没有这行代码，验收日志无法区分成功和普通输出。
PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_MODEL = "phase104_controlled_notepad_launch_smoke"  # 新增代码+Phase104ControlledNotepadLaunchSmoke：定义报告模型名；如果没有这行代码，状态矩阵无法区分当前合同版本。
PHASE104_REAL_NOTEPAD_LAUNCH_SMOKE_ENV = "LEARNING_AGENT_PHASE104_ENABLE_REAL_NOTEPAD_LAUNCH_SMOKE"  # 新增代码+Phase104ControlledNotepadLaunchSmoke：定义允许真实启动的环境门；如果没有这行代码，真实桌面动作缺少第二道开关。
PHASE104_REAL_NOTEPAD_LAUNCH_SMOKE_REQUEST_ENV = "LEARNING_AGENT_PHASE104_RUN_REAL_NOTEPAD_LAUNCH_SMOKE"  # 新增代码+Phase104ControlledNotepadLaunchSmoke：定义请求真实 smoke 的环境门；如果没有这行代码，CLI 无法表达本次要跑真实路径。
PHASE104_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase104ControlledNotepadLaunchSmoke：声明本阶段不开放无边界动作面；如果没有这行代码，能力边界容易被误读。
PHASE104_CONTROLLED_FILE_NAME = "Phase104 Controlled Notepad Launch Smoke.txt"  # 修改代码+Phase104ControlledNotepadLaunchSmoke：保留受控文件名后缀供生成唯一标题；如果没有这行代码，窗口标题匹配会失去稳定可读锚点。
DEFAULT_PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_ROOT = DEFAULT_PERSISTENT_GRANTS_ROOT.parent / "phase104_controlled_notepad_launch_smoke"  # 新增代码+Phase104ControlledNotepadLaunchSmoke：定义默认报告根目录；如果没有这行代码，验收证据没有固定落点。


def _phase104_bool_token(value: Any) -> str:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 会混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回 true 或 false 文本；如果没有这行代码，场景匹配会不稳定。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，_phase104_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。


def _phase104_env_enabled(name: str) -> bool:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，读取显式环境门；如果没有这段函数，真实启动开关逻辑会分散。
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase104ControlledNotepadLaunchSmoke：只接受明确真值；如果没有这行代码，模糊环境值可能误开启真实启动。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，_phase104_env_enabled 到此结束；如果没有这个边界说明，初学者不容易看出环境门范围。


def _phase104_request_real_smoke(explicit_value: bool | None = None) -> bool:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，判断本次是否请求真实 Notepad smoke；如果没有这段函数，测试参数和环境变量入口会漂移。
    if explicit_value is not None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：调用方显式传值时优先使用；如果没有这行代码，单元测试无法安全覆盖真实分支。
        return bool(explicit_value)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回显式请求值；如果没有这行代码，测试传参不会生效。
    return _phase104_env_enabled(PHASE104_REAL_NOTEPAD_LAUNCH_SMOKE_REQUEST_ENV)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：没有显式值时读取请求环境门；如果没有这行代码，CLI 无法请求真实路径。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，_phase104_request_real_smoke 到此结束；如果没有这个边界说明，初学者不容易看出请求门范围。


def _phase104_allow_real_gate(explicit_value: bool | None = None) -> bool:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，判断真实启动允许门是否打开；如果没有这段函数，第二道门禁会分散。
    if explicit_value is not None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：调用方显式传值时优先使用；如果没有这行代码，测试无法安全启用 fake 正向路径。
        return bool(explicit_value)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回显式允许值；如果没有这行代码，测试传参不会生效。
    return _phase104_env_enabled(PHASE104_REAL_NOTEPAD_LAUNCH_SMOKE_ENV)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：没有显式值时读取允许环境门；如果没有这行代码，真实终端无法启用 smoke。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，_phase104_allow_real_gate 到此结束；如果没有这个边界说明，初学者不容易看出允许门范围。


def _phase104_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，安全读取 pid 等整数；如果没有这段函数，坏字段会让合同崩溃。
    try:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：尝试转换整数；如果没有这行代码，字符串 pid 无法兼容。
        return int(value)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回整数值；如果没有这行代码，调用方拿不到可比较 pid。
    except (TypeError, ValueError):  # 新增代码+Phase104ControlledNotepadLaunchSmoke：捕获空值或非数字；如果没有这行代码，坏快照会中断验收。
        return int(default)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回默认值兜底；如果没有这行代码，调用方需要到处写异常处理。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，_phase104_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出整数容错范围。


def _phase104_window_key(window_identity: Any) -> str:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，统一提取窗口硬身份键；如果没有这段函数，baseline 去重和安全关闭会各自猜窗口身份。
    source = dict(window_identity) if isinstance(window_identity, dict) else {}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：只从 dict 身份中读取字段；如果没有这行代码，坏对象可能在关闭窗口前抛异常。
    window_id = str(source.get("window_id") or "")  # 修改代码+Phase104ControlledNotepadLaunchSmoke：优先读取协议窗口 id；如果没有这行代码，真实 hwnd 窗口无法形成稳定键。
    if window_id:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：有窗口 id 时直接使用；如果没有这行代码，hwnd:123 会被降级成较弱 pid 键。
        return window_id  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回窗口 id 作为硬身份；如果没有这行代码，baseline 无法准确识别同一窗口。
    hwnd = _phase104_safe_int(source.get("hwnd"))  # 修改代码+Phase104ControlledNotepadLaunchSmoke：兼容显式 hwnd 字段；如果没有这行代码，部分快照无法关闭指定窗口。
    if hwnd > 0:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：确认 hwnd 有效；如果没有这行代码，0 句柄可能被当作真实窗口。
        return f"hwnd:{hwnd}"  # 修改代码+Phase104ControlledNotepadLaunchSmoke：把 hwnd 转成协议键；如果没有这行代码，窗口身份格式会不一致。
    process_id = _phase104_safe_int(source.get("process_id"))  # 修改代码+Phase104ControlledNotepadLaunchSmoke：最后读取进程 id 兜底；如果没有这行代码，无 hwnd 的 fake 窗口无法参与比较。
    return f"pid:{process_id}" if process_id > 0 else ""  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回较弱 pid 键或空键；如果没有这行代码，调用方无法区分无身份窗口。
# 修改代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，_phase104_window_key 到此结束；如果没有这个边界说明，初学者不容易看出窗口身份范围。


def _phase104_hwnd_from_identity(window_identity: Any) -> int:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，从窗口身份提取 Win32 hwnd；如果没有这段函数，安全关闭无法定位具体窗口。
    source = dict(window_identity) if isinstance(window_identity, dict) else {}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：规整窗口身份为 dict；如果没有这行代码，非 dict 身份会让关闭逻辑崩溃。
    hwnd = _phase104_safe_int(source.get("hwnd"))  # 修改代码+Phase104ControlledNotepadLaunchSmoke：优先读取显式 hwnd；如果没有这行代码，真实快照的原始句柄无法直接使用。
    if hwnd > 0:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：有效 hwnd 直接返回；如果没有这行代码，会继续解析导致不必要的失败。
        return hwnd  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回 Win32 句柄；如果没有这行代码，PostMessage 无法指定目标窗口。
    window_id = str(source.get("window_id") or "")  # 修改代码+Phase104ControlledNotepadLaunchSmoke：读取协议窗口 id；如果没有这行代码，hwnd:123 形式无法解析。
    return _phase104_safe_int(window_id.split(":", 1)[1]) if window_id.startswith("hwnd:") and ":" in window_id else 0  # 修改代码+Phase104ControlledNotepadLaunchSmoke：从 hwnd:123 提取数字句柄；如果没有这行代码，真实窗口关闭会缺少句柄。
# 修改代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，_phase104_hwnd_from_identity 到此结束；如果没有这个边界说明，初学者不容易看出句柄解析范围。


def _phase104_process_registered(backend: Any, process_id: int) -> bool:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，确认启动 pid 来自本后端登记；如果没有这段函数，Windows 11 Notepad 代理进程快速退出会被误判为无归属。
    if process_id <= 0:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：无效 pid 直接拒绝；如果没有这行代码，0 可能被误当作已登记进程。
        return False  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回未登记；如果没有这行代码，后续清理边界会变宽。
    for process in list(getattr(backend, "processes", []) or []):  # 修改代码+Phase104ControlledNotepadLaunchSmoke：遍历后端自有进程对象；如果没有这行代码，默认 Phase103 后端无法证明启动归属。
        if _phase104_safe_int(getattr(process, "pid", 0)) == int(process_id):  # 修改代码+Phase104ControlledNotepadLaunchSmoke：按 pid 精确匹配；如果没有这行代码，可能把别的进程算成本次启动。
            return True  # 修改代码+Phase104ControlledNotepadLaunchSmoke：找到登记记录即可确认归属；如果没有这行代码，代理进程退出后真实 smoke 会误失败。
    return False  # 修改代码+Phase104ControlledNotepadLaunchSmoke：没有登记记录则拒绝；如果没有这行代码，未知进程可能被误清理。
# 修改代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，_phase104_process_registered 到此结束；如果没有这个边界说明，初学者不容易看出启动归属范围。


def _phase104_process_alive(backend: Any, process_id: int) -> bool:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，判断后端自有进程是否仍活着；如果没有这段函数，进程归属验证只能靠后端自报。
    process_alive_method = getattr(backend, "process_alive", None)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：优先读取后端自带存活检查；如果没有这行代码，未来后端无法自定义判断。
    if callable(process_alive_method):  # 新增代码+Phase104ControlledNotepadLaunchSmoke：后端提供方法时使用；如果没有这行代码，自定义后端会被忽略。
        return bool(process_alive_method(process_id))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回后端判断结果；如果没有这行代码，进程归属无法适配不同实现。
    for process in list(getattr(backend, "processes", []) or []):  # 新增代码+Phase104ControlledNotepadLaunchSmoke：遍历 Phase103 后端保存的自有进程；如果没有这行代码，默认后端无法验证进程。
        if _phase104_safe_int(getattr(process, "pid", 0)) == int(process_id):  # 新增代码+Phase104ControlledNotepadLaunchSmoke：只检查本次启动的 pid；如果没有这行代码，可能误把其他进程当自有。
            return getattr(process, "poll", lambda: 1)() is None  # 新增代码+Phase104ControlledNotepadLaunchSmoke：poll 为 None 表示仍存活；如果没有这行代码，清理前后无法验证。
    return False  # 新增代码+Phase104ControlledNotepadLaunchSmoke：没找到自有进程则返回 false；如果没有这行代码，未知进程可能被误认为可清理。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，_phase104_process_alive 到此结束；如果没有这个边界说明，初学者不容易看出进程归属范围。


def _phase104_wait_until_process_exits(backend: Any, process_id: int, timeout_seconds: float = 4.0) -> bool:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，等待自有进程退出；如果没有这段函数，cleanup 可能刚发出 terminate 就被误判成功。
    deadline = time.time() + max(0.1, float(timeout_seconds))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：计算等待截止时间；如果没有这行代码，等待可能无限循环。
    while time.time() < deadline:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：在截止前轮询进程状态；如果没有这行代码，清理状态无法等待稳定。
        if not _phase104_process_alive(backend, process_id):  # 新增代码+Phase104ControlledNotepadLaunchSmoke：检查进程是否已经退出；如果没有这行代码，残留检测没有事实来源。
            return True  # 新增代码+Phase104ControlledNotepadLaunchSmoke：退出后返回 true；如果没有这行代码，成功清理无法表达。
        time.sleep(0.1)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：短暂等待避免忙等；如果没有这行代码，循环会浪费 CPU。
    return not _phase104_process_alive(backend, process_id)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：超时后做最后一次判断；如果没有这行代码，边界时刻可能误判。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，_phase104_wait_until_process_exits 到此结束；如果没有这个边界说明，初学者不容易看出等待范围。


class Phase104VisibleWindowProbe:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：类段开始，定义真实窗口可见性探测器；如果没有这个类，真实启动只能证明进程存在不能证明窗口出现。
    def __init__(self, inventory_probe: Any | None = None) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，初始化窗口探测器；如果没有这段函数，测试无法注入 fake inventory。
        self.inventory_probe = inventory_probe if inventory_probe is not None else WindowsWindowInventoryProbe()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：默认使用项目只读窗口枚举；如果没有这行代码，真实窗口没有事实来源。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104VisibleWindowProbe.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def snapshot_window_keys(self) -> set[str]:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，读取启动前窗口硬身份基线；如果没有这段函数，Windows 11 代理窗口无法和用户已有窗口区分。
        snapshot = self.inventory_probe.snapshot()  # 修改代码+Phase104ControlledNotepadLaunchSmoke：读取当前窗口快照；如果没有这行代码，baseline 没有事实来源。
        keys: set[str] = set()  # 修改代码+Phase104ControlledNotepadLaunchSmoke：准备窗口键集合；如果没有这行代码，调用方无法高效判断新旧窗口。
        for window in list(getattr(snapshot, "windows", []) or []):  # 修改代码+Phase104ControlledNotepadLaunchSmoke：遍历快照窗口；如果没有这行代码，baseline 会一直为空。
            key = _phase104_window_key(self._window_identity(window))  # 修改代码+Phase104ControlledNotepadLaunchSmoke：把窗口转成稳定键；如果没有这行代码，真实 hwnd 和 fake 窗口无法统一比较。
            if key:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：只保存非空键；如果没有这行代码，空键会污染 baseline。
                keys.add(key)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：加入窗口键；如果没有这行代码，新窗口判断没有历史参照。
        return keys  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回启动前窗口键集合；如果没有这行代码，真实 smoke 无法传递 baseline。
    # 修改代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104VisibleWindowProbe.snapshot_window_keys 到此结束；如果没有这个边界说明，初学者不容易看出 baseline 范围。

    def wait_for_visible_window(self, process_id: int, title_hint: str, timeout_seconds: float = 8.0, baseline_window_keys: set[str] | None = None) -> dict[str, Any]:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，等待受控 Notepad 可见窗口并兼容代理 pid；如果没有这段函数，Windows 11 Notepad 新窗口会被误判失败。
        baseline_keys = set(baseline_window_keys or set())  # 修改代码+Phase104ControlledNotepadLaunchSmoke：规整启动前窗口基线；如果没有这行代码，新旧窗口判断会反复处理空值。
        deadline = time.time() + max(0.1, float(timeout_seconds))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：计算窗口等待截止时间；如果没有这行代码，查找可能无限等待。
        while time.time() < deadline:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：在超时前重复读取窗口快照；如果没有这行代码，Notepad 启动延迟会导致误失败。
            snapshot = self.inventory_probe.snapshot()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：读取只读窗口快照；如果没有这行代码，没有窗口事实来源。
            for window in list(getattr(snapshot, "windows", []) or []):  # 新增代码+Phase104ControlledNotepadLaunchSmoke：遍历窗口列表；如果没有这行代码，无法匹配目标窗口。
                identity = self._window_identity(window)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：生成脱敏窗口身份；如果没有这行代码，匹配和报告会重复散落。
                title_matches = str(title_hint).lower() in str(identity.get("title_preview", "")).lower() if title_hint else True  # 新增代码+Phase104ControlledNotepadLaunchSmoke：要求标题包含受控文件名；如果没有这行代码，可能误选用户已有 Notepad。
                process_matches = int(identity.get("process_id", 0) or 0) == int(process_id)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：要求窗口 pid 属于本次启动进程；如果没有这行代码，可能误匹配其他 Notepad。
                window_key = _phase104_window_key(identity)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：提取当前窗口硬身份键；如果没有这行代码，无法判断窗口是否是启动后新增。
                new_window_after_launch = bool(window_key and window_key not in baseline_keys)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：判断窗口是否不在启动前基线中；如果没有这行代码，代理 pid 场景只能按过严 pid 失败。
                notepad_matches = "notepad" in " ".join(str(identity.get(key, "")).lower() for key in ("app_id", "process_name", "class_name", "title_preview"))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：要求窗口身份看起来是 Notepad；如果没有这行代码，任意同标题窗口可能被放行。
                visible = bool(identity.get("visible", True))  # 修改代码+Phase104ControlledNotepadLaunchSmoke：读取窗口可见状态；如果没有这行代码，隐藏窗口可能被误认为可见 smoke。
                if title_matches and notepad_matches and visible and (process_matches or new_window_after_launch):  # 修改代码+Phase104ControlledNotepadLaunchSmoke：允许同 pid 或启动后新增的受控 Notepad 窗口；如果没有这行代码，Windows 11 代理进程会失败。
                    verified_identity = dict(identity, window_pid_matches_launch_process=process_matches, new_window_after_launch=new_window_after_launch)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：记录匹配策略；如果没有这行代码，报告无法解释为什么 pid 不同仍安全。
                    return {"visible_window_verified": True, "window_identity": verified_identity}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回可见窗口证据；如果没有这行代码，调用方无法证明窗口出现。
            time.sleep(0.2)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：短暂等待后重试；如果没有这行代码，会忙等消耗 CPU。
        return {"visible_window_verified": False, "window_identity": {}, "reason": "owned_notepad_window_not_found"}  # 新增代码+Phase104ControlledNotepadLaunchSmoke：超时返回失败证据；如果没有这行代码，调用方无法区分未找到和异常。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104VisibleWindowProbe.wait_for_visible_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口等待范围。

    def close_verified_window(self, window_identity: dict[str, Any], title_hint: str, baseline_window_keys: set[str] | None = None, timeout_seconds: float = 4.0) -> dict[str, Any]:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，只关闭已验证的受控 Notepad 窗口；如果没有这段函数，代理进程窗口可能残留在用户桌面。
        baseline_keys = set(baseline_window_keys or set())  # 修改代码+Phase104ControlledNotepadLaunchSmoke：规整启动前窗口基线；如果没有这行代码，关闭时无法避免动到已有窗口。
        identity = dict(window_identity)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：复制窗口身份避免污染报告；如果没有这行代码，调用方对象可能被关闭逻辑改写。
        window_key = _phase104_window_key(identity)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：提取待关闭窗口键；如果没有这行代码，无法判断窗口是否属于启动后新增。
        title_matches = str(title_hint).lower() in str(identity.get("title_preview", "")).lower() if title_hint else False  # 修改代码+Phase104ControlledNotepadLaunchSmoke：确认标题仍指向受控文件；如果没有这行代码，可能关闭用户其他 Notepad。
        notepad_matches = "notepad" in " ".join(str(identity.get(key, "")).lower() for key in ("app_id", "process_name", "class_name", "title_preview"))  # 修改代码+Phase104ControlledNotepadLaunchSmoke：确认窗口身份仍像 Notepad；如果没有这行代码，同标题非 Notepad 窗口可能被关闭。
        new_window_after_launch = bool(window_key and window_key not in baseline_keys)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：确认窗口不是启动前已有窗口；如果没有这行代码，可能关掉用户原本打开的窗口。
        hwnd = _phase104_hwnd_from_identity(identity)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：提取 Win32 hwnd；如果没有这行代码，无法向具体窗口发送关闭消息。
        if not (title_matches and notepad_matches and new_window_after_launch and hwnd > 0):  # 修改代码+Phase104ControlledNotepadLaunchSmoke：安全条件不齐时拒绝关闭；如果没有这行代码，清理范围会过宽。
            return {"window_cleanup_attempted": False, "window_cleanup_completed": False, "owned_window_only": False, "reason": "verified_window_close_refused_by_identity_guard"}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回拒绝摘要；如果没有这行代码，失败原因不清楚。
        try:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：尝试调用 Win32 关闭消息；如果没有这行代码，权限或平台错误会直接打断合同。
            import ctypes  # 修改代码+Phase104ControlledNotepadLaunchSmoke：局部导入 ctypes 调用 user32；如果没有这行代码，Python 无法发送 WM_CLOSE。
            user32 = ctypes.windll.user32  # type: ignore[attr-defined]  # 修改代码+Phase104ControlledNotepadLaunchSmoke：读取 user32 DLL；如果没有这行代码，无法触达窗口消息 API。
            posted = bool(user32.PostMessageW(int(hwnd), 0x0010, 0, 0))  # 修改代码+Phase104ControlledNotepadLaunchSmoke：向指定 hwnd 发送 WM_CLOSE；如果没有这行代码，代理窗口不会被收尾。
        except Exception as error:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：捕获窗口关闭异常；如果没有这行代码，清理失败会丢失结构化报告。
            return {"window_cleanup_attempted": True, "window_cleanup_completed": False, "owned_window_only": True, "reason": f"post_wm_close_failed:{type(error).__name__}"}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回关闭异常类型；如果没有这行代码，验收失败难以排查。
        deadline = time.time() + max(0.1, float(timeout_seconds))  # 修改代码+Phase104ControlledNotepadLaunchSmoke：计算等待窗口消失的截止时间；如果没有这行代码，关闭等待可能无限循环。
        while time.time() < deadline:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：在截止前轮询窗口是否消失；如果没有这行代码，刚发送关闭消息就会误判完成。
            if not self._verified_window_still_visible(window_key, title_hint):  # 修改代码+Phase104ControlledNotepadLaunchSmoke：检查目标窗口是否已经消失；如果没有这行代码，清理完成没有事实来源。
                return {"window_cleanup_attempted": True, "window_cleanup_completed": bool(posted), "owned_window_only": True}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回窗口清理成功；如果没有这行代码，调用方无法把窗口收尾纳入合同。
            time.sleep(0.1)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：短暂等待避免忙等；如果没有这行代码，轮询会浪费 CPU。
        return {"window_cleanup_attempted": True, "window_cleanup_completed": False, "owned_window_only": True, "reason": "verified_window_still_visible_after_close"}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：超时仍可见则失败；如果没有这行代码，残留窗口会被误判清理完成。
    # 修改代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104VisibleWindowProbe.close_verified_window 到此结束；如果没有这个边界说明，初学者不容易看出安全关闭范围。

    def _verified_window_still_visible(self, window_key: str, title_hint: str) -> bool:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，检查已验证窗口是否仍存在；如果没有这段函数，WM_CLOSE 后无法确认窗口收尾。
        snapshot = self.inventory_probe.snapshot()  # 修改代码+Phase104ControlledNotepadLaunchSmoke：读取最新窗口快照；如果没有这行代码，关闭结果没有事实来源。
        for window in list(getattr(snapshot, "windows", []) or []):  # 修改代码+Phase104ControlledNotepadLaunchSmoke：遍历当前窗口；如果没有这行代码，无法查找残留窗口。
            identity = self._window_identity(window)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：提取当前窗口身份；如果没有这行代码，匹配逻辑会重复散落。
            current_key = _phase104_window_key(identity)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：读取当前窗口键；如果没有这行代码，无法精确匹配同一个窗口。
            title_matches = str(title_hint).lower() in str(identity.get("title_preview", "")).lower() if title_hint else False  # 修改代码+Phase104ControlledNotepadLaunchSmoke：确认标题仍是受控文件；如果没有这行代码，可能把其他 Notepad 算作残留。
            if current_key == window_key and title_matches:  # 修改代码+Phase104ControlledNotepadLaunchSmoke：同窗口同标题仍存在才算残留；如果没有这行代码，残留判断会过宽。
                return True  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回仍可见；如果没有这行代码，调用方会误以为关闭完成。
        return False  # 修改代码+Phase104ControlledNotepadLaunchSmoke：未找到目标窗口则视为已关闭；如果没有这行代码，窗口清理永远无法成功。
    # 修改代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104VisibleWindowProbe._verified_window_still_visible 到此结束；如果没有这个边界说明，初学者不容易看出残留判断范围。

    def _window_identity(self, window: Any) -> dict[str, Any]:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，提取窗口脱敏身份；如果没有这段函数，报告可能泄露完整窗口信息或缺少 pid。
        source = dict(window) if isinstance(window, dict) else {}  # 新增代码+Phase104ControlledNotepadLaunchSmoke：兼容项目窗口快照常见 dict 形状；如果没有这行代码，fake 和真实窗口读取会分裂。
        hwnd = _phase104_safe_int(source.get("hwnd"))  # 修改代码+Phase104ControlledNotepadLaunchSmoke：读取原始 hwnd 供安全关闭使用；如果没有这行代码，window_id 为 hwnd:123 之外的快照无法关闭。
        window_id = str(source.get("window_id") or (f"hwnd:{hwnd}" if hwnd > 0 else ""))  # 修改代码+Phase104ControlledNotepadLaunchSmoke：优先保留协议 id 并兜底 hwnd；如果没有这行代码，窗口硬身份会不稳定。
        return {"app_id": str(source.get("app_id") or ""), "process_name": str(source.get("process_name") or ""), "class_name": str(source.get("class_name") or ""), "window_id": window_id, "hwnd": _phase104_hwnd_from_identity({"window_id": window_id, "hwnd": hwnd}), "process_id": _phase104_safe_int(source.get("pid") or source.get("process_id")), "title_preview": str(source.get("title_preview") or source.get("title") or ""), "visible": bool(source.get("visible", True))}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回窗口身份摘要并带 hwnd；如果没有这行代码，窗口验证和关闭没有结构化证据。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，Phase104VisibleWindowProbe._window_identity 到此结束；如果没有这个边界说明，初学者不容易看出身份字段范围。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：类段结束，Phase104VisibleWindowProbe 到此结束；如果没有这个边界说明，初学者不容易看出探测器范围。


class WindowsControlledNotepadLaunchSmoke:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：类段开始，组合 Phase103 启动、窗口验证和清理；如果没有这个类，Phase104 合同会散成脚本。
    def __init__(self, base_dir: str | Path | None = None, launch_backend: Any | None = None, window_probe: Any | None = None, platform: str | None = None) -> None:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，初始化 smoke runtime；如果没有这段函数，测试和真实终端无法注入后端。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_ROOT / f"run-{int(time.time() * 1000)}"  # 新增代码+Phase104ControlledNotepadLaunchSmoke：选择隔离运行目录；如果没有这行代码，多次 smoke 会互相污染。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：确保运行目录存在；如果没有这行代码，受控文件和报告写入会失败。
        self.platform = str(platform or sys.platform)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：保存平台名；如果没有这行代码，非 Windows 路径无法安全拒绝。
        self.launch_backend = launch_backend if launch_backend is not None else Phase103SubprocessLaunchBackend(platform=self.platform)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：默认使用 Phase103 受控 subprocess 后端；如果没有这行代码，真实启动没有最后一跳。
        self.window_probe = window_probe if window_probe is not None else Phase104VisibleWindowProbe()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：默认使用可见窗口探测器；如果没有这行代码，真实 smoke 无法确认窗口出现。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，WindowsControlledNotepadLaunchSmoke.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _controlled_file(self) -> Path:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，生成本次 Notepad 受控文件路径；如果没有这段函数，可能打开用户文件。
        controlled_dir = self.base_dir / "controlled_notepad"  # 新增代码+Phase104ControlledNotepadLaunchSmoke：定义受控目录；如果没有这行代码，测试文件会和报告混在一起。
        controlled_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：确保受控目录存在；如果没有这行代码，写目标文件会失败。
        target_file = controlled_dir / f"phase104-{int(time.time() * 1000)}-{PHASE104_CONTROLLED_FILE_NAME}"  # 修改代码+Phase104ControlledNotepadLaunchSmoke：每次生成唯一受控文件名；如果没有这行代码，历史残留窗口可能干扰新 smoke。
        target_file.write_text("Phase104 controlled Notepad launch smoke evidence.\n", encoding="utf-8")  # 新增代码+Phase104ControlledNotepadLaunchSmoke：写入只读证据文本；如果没有这行代码，Notepad 打开不存在文件可能弹确认。
        return target_file  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回受控文件路径；如果没有这行代码，启动后端没有参数。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，WindowsControlledNotepadLaunchSmoke._controlled_file 到此结束；如果没有这个边界说明，初学者不容易看出文件范围。

    def _default_off_probe(self) -> dict[str, Any]:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，证明默认关闭不会启动应用；如果没有这段函数，安全默认只能靠口头说明。
        backend = Phase103RecordingLaunchBackend()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建记录后端；如果没有这行代码，默认关闭无法检查后端调用数。
        candidate = WindowsControlledAppLaunchCandidate(launch_backend=backend)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建 Phase103 候选；如果没有这行代码，默认关闭不经过真实安全计划。
        result = candidate.launch("notepad", enable_real_launch=False)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：执行默认关闭路径；如果没有这行代码，零事件没有事实来源。
        return {"default_off_zero_events": bool(result.get("decision") == "real_app_launch_disabled_by_default" and len(backend.launches) == 0 and not result.get("real_desktop_touched")), "result": result}  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回默认关闭摘要；如果没有这行代码，报告无法证明未调用后端。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，WindowsControlledNotepadLaunchSmoke._default_off_probe 到此结束；如果没有这个边界说明，初学者不容易看出默认探测范围。

    def _unsafe_probe(self) -> dict[str, Any]:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，证明危险启动不会到达后端；如果没有这段函数，PowerShell 类目标可能缺少回归保护。
        backend = Phase103RecordingLaunchBackend()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建危险路径记录后端；如果没有这行代码，无法证明危险路径无调用。
        candidate = WindowsControlledAppLaunchCandidate(launch_backend=backend)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建 Phase103 候选；如果没有这行代码，危险检查不会复用安全计划。
        result = candidate.launch("powershell", enable_real_launch=True)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：尝试危险 powershell 启动；如果没有这行代码，高风险拒绝没有样本。
        return {"unsafe_launch_zero_events": bool(result.get("decision") == "unsafe_launch_plan_rejected" and len(backend.launches) == 0 and result.get("unsafe_launch_zero_events")), "result": result}  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回危险零事件摘要；如果没有这行代码，报告无法证明拒绝在后端前发生。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，WindowsControlledNotepadLaunchSmoke._unsafe_probe 到此结束；如果没有这个边界说明，初学者不容易看出危险探测范围。

    def run(self, real_smoke: bool | None = None, allow_real_gate: bool | None = None) -> dict[str, Any]:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，运行 Phase104 合同；如果没有这段函数，CLI 和测试没有统一入口。
        requested = _phase104_request_real_smoke(real_smoke)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：判断是否请求真实 smoke；如果没有这行代码，默认关闭和真实路径会混淆。
        allowed = _phase104_allow_real_gate(allow_real_gate)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：判断允许门是否打开；如果没有这行代码，单门可能误触真实桌面。
        default_probe = self._default_off_probe()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：收集默认关闭证据；如果没有这行代码，报告缺少安全基线。
        unsafe_probe = self._unsafe_probe()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：收集危险拒绝证据；如果没有这行代码，高风险拒绝不可验收。
        real_report = self._run_real_smoke() if requested and allowed else {"real_notepad_launch_attempted": False, "process_ownership_verified": False, "visible_window_verified": False, "cleanup_completed": False, "residual_owned_process": False, "verified_window_cleanup_completed": False, "real_desktop_touched": False, "reason": "real_smoke_not_requested_or_gate_disabled"}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：双门满足才真实启动并补齐窗口清理字段；如果没有这行代码，普通合同可能打开 Notepad 或报告缺字段。
        passed = bool(default_probe.get("default_off_zero_events") and unsafe_probe.get("unsafe_launch_zero_events") and not PHASE104_UNCONTROLLED_ACTIONS_EXPANDED and ((not requested and not real_report.get("real_desktop_touched")) or (requested and allowed and real_report.get("real_notepad_launch_attempted") and real_report.get("process_ownership_verified") and real_report.get("visible_window_verified") and real_report.get("cleanup_completed") and not real_report.get("residual_owned_process"))))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：汇总合同通过条件；如果没有这行代码，main 无法用退出码表达失败。
        report_path = self.base_dir / "reports" / "phase104_controlled_notepad_launch_smoke_report.json"  # 新增代码+Phase104ControlledNotepadLaunchSmoke：定义报告路径；如果没有这行代码，验收证据没有固定落点。
        report = {"marker": PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_MARKER, "ok_token": PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_OK_TOKEN, "model": PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_MODEL, "passed": passed, "real_smoke_requested": requested, "real_enable_gate_passed": allowed, "real_enable_gate_required": True, "default_off_zero_events": bool(default_probe.get("default_off_zero_events")), "unsafe_launch_zero_events": bool(unsafe_probe.get("unsafe_launch_zero_events")), "real_notepad_launch_attempted": bool(real_report.get("real_notepad_launch_attempted")), "process_ownership_verified": bool(real_report.get("process_ownership_verified")), "visible_window_verified": bool(real_report.get("visible_window_verified")), "cleanup_completed": bool(real_report.get("cleanup_completed")), "residual_owned_process": bool(real_report.get("residual_owned_process")), "verified_window_cleanup_completed": bool(real_report.get("verified_window_cleanup_completed")), "real_desktop_touched": bool(real_report.get("real_desktop_touched")), "uncontrolled_actions_expanded": PHASE104_UNCONTROLLED_ACTIONS_EXPANDED, "report_path": str(report_path), "default_off_report": default_probe.get("result"), "unsafe_report": unsafe_probe.get("result"), "real_smoke_report": real_report}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：构造完整报告并公开窗口清理字段；如果没有这行代码，测试和真实终端拿不到统一事实。
        atomic_write_json(report_path, report)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：原子写入报告；如果没有这行代码，失败时可能留下半个 JSON。
        return report  # 新增代码+Phase104ControlledNotepadLaunchSmoke：返回合同报告；如果没有这行代码，调用方无法读取结果。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，WindowsControlledNotepadLaunchSmoke.run 到此结束；如果没有这个边界说明，初学者不容易看出合同范围。

    def _run_real_smoke(self) -> dict[str, Any]:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，执行真实 Notepad 启动、窗口验证和清理；如果没有这段函数，Phase104 只能停留在 fake 合同。
        if not self.platform.startswith("win"):  # 新增代码+Phase104ControlledNotepadLaunchSmoke：非 Windows 直接拒绝真实路径；如果没有这行代码，跨平台会尝试 Windows exe。
            return {"real_notepad_launch_attempted": False, "process_ownership_verified": False, "visible_window_verified": False, "cleanup_completed": False, "residual_owned_process": False, "verified_window_cleanup_completed": False, "real_desktop_touched": False, "reason": "platform_not_windows"}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回平台不支持并补齐窗口清理字段；如果没有这行代码，失败原因不清楚。
        baseline_method = getattr(self.window_probe, "snapshot_window_keys", None)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：读取窗口探测器的 baseline 方法；如果没有这行代码，真实窗口新旧判断无法接入。
        baseline_window_keys = set(baseline_method() if callable(baseline_method) else set())  # 修改代码+Phase104ControlledNotepadLaunchSmoke：记录启动前已有窗口；如果没有这行代码，代理 pid 场景可能误匹配旧窗口。
        target_file = self._controlled_file()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建受控 Notepad 文件；如果没有这行代码，可能打开用户文件或无文件。
        title_hint = target_file.name  # 修改代码+Phase104ControlledNotepadLaunchSmoke：用唯一文件名作为窗口标题提示；如果没有这行代码，历史残留同名窗口可能干扰匹配。
        candidate = WindowsControlledAppLaunchCandidate(launch_backend=self.launch_backend)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建 Phase103 启动候选；如果没有这行代码，真实启动会绕过安全计划。
        launch_result = candidate.launch("notepad", enable_real_launch=True, test_file=str(target_file))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：显式启动只打开受控文件的 Notepad；如果没有这行代码，真实 smoke 没有启动动作。
        process_id = _phase104_safe_int(dict(launch_result.get("backend_result", {}) or {}).get("process_id") or launch_result.get("process_id"))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：读取后端返回的自有进程 pid；如果没有这行代码，后续窗口和清理无法按归属执行。
        attempted = bool(launch_result.get("ok") and process_id > 0 and launch_result.get("real_desktop_touched"))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：确认启动确实发生；如果没有这行代码，空启动也可能误过。
        ownership = bool(attempted and _phase104_process_registered(self.launch_backend, process_id))  # 修改代码+Phase104ControlledNotepadLaunchSmoke：确认 pid 属于本后端登记而非必须仍存活；如果没有这行代码，Windows 11 Notepad wrapper 快速退出会误失败。
        window_result = self.window_probe.wait_for_visible_window(process_id, title_hint, timeout_seconds=8.0, baseline_window_keys=baseline_window_keys) if ownership else {"visible_window_verified": False, "window_identity": {}, "reason": "launch_process_not_registered"}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：按唯一标题和启动前基线探测窗口；如果没有这行代码，可能误查用户窗口。
        cleanup_method = getattr(self.launch_backend, "cleanup", None)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：读取后端 cleanup 方法；如果没有这行代码，无法清理本次启动的进程。
        cleanup_result = cleanup_method() if callable(cleanup_method) else {"cleanup_attempted": False, "processes_cleaned": 0, "owned_process_only": False}  # 新增代码+Phase104ControlledNotepadLaunchSmoke：调用后端清理或返回失败摘要；如果没有这行代码，真实 Notepad 可能残留。
        exited = _phase104_wait_until_process_exits(self.launch_backend, process_id) if process_id > 0 else False  # 新增代码+Phase104ControlledNotepadLaunchSmoke：等待本次进程退出；如果没有这行代码，cleanup 刚触发但未完成也会误过。
        residual = bool(process_id > 0 and _phase104_process_alive(self.launch_backend, process_id))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：最终检查是否残留自有进程；如果没有这行代码，清理失败不可见。
        window_identity = dict(window_result.get("window_identity", {}) or {})  # 修改代码+Phase104ControlledNotepadLaunchSmoke：复制窗口身份用于判断是否需要额外关闭；如果没有这行代码，代理窗口清理无法读取 pid。
        window_pid_matches_process = bool(window_identity.get("window_pid_matches_launch_process", True))  # 修改代码+Phase104ControlledNotepadLaunchSmoke：读取窗口 pid 是否等于启动 pid；如果没有这行代码，代理进程残留风险不可见。
        window_cleanup_needed = bool(window_result.get("visible_window_verified") and not window_pid_matches_process)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：pid 不同的代理窗口需要额外关闭；如果没有这行代码，只清理 wrapper 会留下窗口。
        close_method = getattr(self.window_probe, "close_verified_window", None)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：读取窗口安全关闭接口；如果没有这行代码，代理窗口无法被收尾。
        window_cleanup_result = close_method(window_identity, title_hint, baseline_window_keys=baseline_window_keys, timeout_seconds=4.0) if window_cleanup_needed and callable(close_method) else {"window_cleanup_attempted": False, "window_cleanup_completed": not window_cleanup_needed, "owned_window_only": not window_cleanup_needed}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：只在需要时关闭已验证窗口；如果没有这行代码，代理窗口会残留或同 pid 路径会误关。
        verified_window_cleanup_completed = bool(window_cleanup_result.get("window_cleanup_completed"))  # 修改代码+Phase104ControlledNotepadLaunchSmoke：汇总已验证窗口清理结果；如果没有这行代码，cleanup_completed 无法覆盖窗口层面。
        cleanup_completed = bool(cleanup_result.get("cleanup_attempted") and exited and not residual and verified_window_cleanup_completed)  # 修改代码+Phase104ControlledNotepadLaunchSmoke：汇总进程和窗口双清理；如果没有这行代码，用户无法知道窗口是否收尾。
        return {"real_notepad_launch_attempted": attempted, "process_ownership_verified": ownership, "visible_window_verified": bool(window_result.get("visible_window_verified")), "cleanup_completed": cleanup_completed, "residual_owned_process": residual, "verified_window_cleanup_completed": verified_window_cleanup_completed, "real_desktop_touched": bool(launch_result.get("real_desktop_touched")), "process_id": process_id, "target_file": str(target_file), "title_hint": title_hint, "baseline_window_keys": sorted(baseline_window_keys), "launch_result": launch_result, "window_result": window_result, "cleanup_result": cleanup_result, "window_cleanup_result": window_cleanup_result}  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回真实 smoke 脱敏摘要并包含窗口清理；如果没有这行代码，CLI 和测试无法验证真实路径。
    # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，WindowsControlledNotepadLaunchSmoke._run_real_smoke 到此结束；如果没有这个边界说明，初学者不容易看出真实 smoke 范围。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：类段结束，WindowsControlledNotepadLaunchSmoke 到此结束；如果没有这个边界说明，初学者不容易看出 runtime 范围。


def run_phase104_controlled_notepad_launch_smoke_contract(base_dir: str | Path | None = None, real_smoke: bool | None = None, allow_real_gate: bool | None = None, launch_backend: Any | None = None, window_probe: Any | None = None, platform: str | None = None) -> dict[str, Any]:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，提供 Phase104 统一合同入口；如果没有这段函数，测试和终端需要手拼 runtime。
    smoke = WindowsControlledNotepadLaunchSmoke(base_dir=base_dir, launch_backend=launch_backend, window_probe=window_probe, platform=platform)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：创建 smoke runtime；如果没有这行代码，公共入口没有被测对象。
    return smoke.run(real_smoke=real_smoke, allow_real_gate=allow_real_gate)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：运行并返回合同报告；如果没有这行代码，调用方拿不到结果。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，run_phase104_controlled_notepad_launch_smoke_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同入口范围。


def phase104_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，把报告转成真实终端稳定 token 行；如果没有这段函数，验收器需要解析复杂 JSON。
    ok_token = f" {PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_OK_TOKEN}" if bool(report.get("passed")) else ""  # 新增代码+Phase104ControlledNotepadLaunchSmoke：仅通过时输出 OK token；如果没有这行代码，失败报告可能误带成功锚点。
    return f"{PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_MARKER}{ok_token} default_off_zero_events={_phase104_bool_token(report.get('default_off_zero_events'))} real_enable_gate_required={_phase104_bool_token(report.get('real_enable_gate_required'))} real_notepad_launch_attempted={_phase104_bool_token(report.get('real_notepad_launch_attempted'))} process_ownership_verified={_phase104_bool_token(report.get('process_ownership_verified'))} visible_window_verified={_phase104_bool_token(report.get('visible_window_verified'))} cleanup_completed={_phase104_bool_token(report.get('cleanup_completed'))} verified_window_cleanup_completed={_phase104_bool_token(report.get('verified_window_cleanup_completed'))} residual_owned_process={_phase104_bool_token(report.get('residual_owned_process'))} unsafe_launch_zero_events={_phase104_bool_token(report.get('unsafe_launch_zero_events'))} real_desktop_touched={_phase104_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase104_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 修改代码+Phase104ControlledNotepadLaunchSmoke：返回固定顺序 token 并加入窗口清理结果；如果没有这行代码，真实终端验收无法发现残留窗口。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，phase104_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段开始，提供命令行入口；如果没有这段函数，真实终端无法直接运行 Phase104 合同。
    _ = argv  # 新增代码+Phase104ControlledNotepadLaunchSmoke：保留 argv 扩展位；如果没有这行代码，读者可能误以为参数被遗漏。
    report = run_phase104_controlled_notepad_launch_smoke_contract()  # 新增代码+Phase104ControlledNotepadLaunchSmoke：按环境门运行合同；如果没有这行代码，CLI 没有验收事实。
    print(phase104_cli_line(report))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：打印稳定 token 行；如果没有这行代码，场景无法快速匹配成功条件。
    print(json.dumps({"report_path": report.get("report_path"), "passed": report.get("passed"), "real_notepad_launch_attempted": report.get("real_notepad_launch_attempted"), "cleanup_completed": report.get("cleanup_completed")}, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase104ControlledNotepadLaunchSmoke：打印短 JSON 方便定位证据；如果没有这行代码，失败时不容易找报告。
    print(PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_MARKER)  # 新增代码+Phase104ControlledNotepadLaunchSmoke：单独打印 marker 方便人工观察；如果没有这行代码，可见终端阶段标识不够醒目。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase104ControlledNotepadLaunchSmoke：按 passed 返回退出码；如果没有这行代码，失败合同可能被自动化误判成功。
# 新增代码+Phase104ControlledNotepadLaunchSmoke：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["DEFAULT_PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_ROOT", "PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_MARKER", "PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_MODEL", "PHASE104_CONTROLLED_NOTEPAD_LAUNCH_SMOKE_OK_TOKEN", "PHASE104_REAL_NOTEPAD_LAUNCH_SMOKE_ENV", "PHASE104_REAL_NOTEPAD_LAUNCH_SMOKE_REQUEST_ENV", "PHASE104_UNCONTROLLED_ACTIONS_EXPANDED", "Phase104VisibleWindowProbe", "WindowsControlledNotepadLaunchSmoke", "main", "phase104_cli_line", "run_phase104_controlled_notepad_launch_smoke_contract"]  # 新增代码+Phase104ControlledNotepadLaunchSmoke：限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase104ControlledNotepadLaunchSmoke：允许直接运行模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase104ControlledNotepadLaunchSmoke：用 main 返回码退出；如果没有这行代码，命令行状态不明确。
