"""Phase35 Windows real UIAutomation safe-window smoke harness."""  # 新增代码+Phase35WindowsRealUIASmoke: 说明本文件只负责真实 UIA 安全窗口 smoke；如果没有这行代码，读者不容易知道这个模块不是通用动作执行器。
from __future__ import annotations  # 新增代码+Phase35WindowsRealUIASmoke: 启用延迟类型解析；如果没有这行代码，部分类型注解在旧路径下更容易出现导入顺序问题。

import importlib.util  # 新增代码+Phase35WindowsRealUIASmoke: 用于探测 uiautomation 依赖是否安装；如果没有这行代码，模块只能靠异常猜测依赖状态。
import json  # 新增代码+Phase35WindowsRealUIASmoke: 用于 CLI 输出结构化诊断；如果没有这行代码，可见终端验收只能看散乱文本。
import subprocess  # 新增代码+Phase35WindowsRealUIASmoke: 用于启动安全 Notepad 窗口；如果没有这行代码，真实 smoke 无法创建自有测试窗口。
import sys  # 新增代码+Phase35WindowsRealUIASmoke: 用于读取当前平台；如果没有这行代码，非 Windows 环境可能误触 Windows API。
import tempfile  # 新增代码+Phase35WindowsRealUIASmoke: 用于创建隔离临时文件；如果没有这行代码，Notepad smoke 可能污染项目目录。
import time  # 新增代码+Phase35WindowsRealUIASmoke: 用于轮询安全窗口出现；如果没有这行代码，启动窗口后无法等待桌面完成枚举。
from dataclasses import asdict, dataclass, replace  # 修改代码+Phase35WindowsRealUIASmoke: 增加 replace 用来在清理后更新结果；如果没有这行代码，finally 里的 cleanup 状态无法写回不可变结果对象。
from pathlib import Path  # 新增代码+Phase35WindowsRealUIASmoke: 用 Path 管理临时文件路径；如果没有这行代码，Windows 路径拼接容易出错。
from typing import Any, Callable  # 新增代码+Phase35WindowsRealUIASmoke: 标注可注入 seam 的类型；如果没有这行代码，测试入口边界不清楚。

try:  # 新增代码+Phase35WindowsRealUIASmoke: 包住包模式导入；如果没有这行代码，start_oauth_agent.bat 的脚本路径可能导入失败。
    from learning_agent.computer_use.native_helper import NativeWindowTextResult, WindowsUiautomationTextProvider, parse_hwnd_from_window  # 新增代码+Phase35WindowsRealUIASmoke: 复用 Phase32/34 文本 provider 合同；如果没有这行代码，Phase35 会重复造一套 UIA 读取逻辑。
    from learning_agent.computer_use.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase35WindowsRealUIASmoke: 复用 Phase28 真实窗口 inventory；如果没有这行代码，safe window 查找会和生产 observe 规则不一致。
except ModuleNotFoundError as error:  # 新增代码+Phase35WindowsRealUIASmoke: 兼容直接脚本运行时包名不同的情况；如果没有这行代码，bat 入口更容易因为路径失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.native_helper", "learning_agent.computer_use.windows_backend"}:  # 新增代码+Phase35WindowsRealUIASmoke: 只吞掉预期包路径错误；如果没有这行代码，真实内部 bug 可能被误吞。
        raise  # 新增代码+Phase35WindowsRealUIASmoke: 重新抛出非路径类导入错误；如果没有这行代码，排查真实依赖问题会很困难。
    from computer_use.native_helper import NativeWindowTextResult, WindowsUiautomationTextProvider, parse_hwnd_from_window  # 新增代码+Phase35WindowsRealUIASmoke: 脚本模式下导入文本 provider；如果没有这行代码，learning_agent 目录内运行模块会失败。
    from computer_use.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase35WindowsRealUIASmoke: 脚本模式下导入真实窗口 inventory；如果没有这行代码，bat 场景无法枚举安全窗口。


PHASE35_REAL_UIA_SMOKE_MARKER = "PHASE35_WINDOWS_REAL_UIA_SMOKE_READY"  # 新增代码+Phase35WindowsRealUIASmoke: 定义 Phase35 完成标记；如果没有这行代码，可见终端验收没有稳定匹配点。
PHASE35_REAL_UIA_SMOKE_OK_TOKEN = "PHASE35_WINDOWS_REAL_UIA_SMOKE_OK"  # 新增代码+Phase35WindowsRealUIASmoke: 定义 Phase35 命令成功 token；如果没有这行代码，debug log 无法区分 smoke 输出和普通回答。
PHASE35_UIA_DEPENDENCY = "uiautomation"  # 新增代码+Phase35WindowsRealUIASmoke: 集中定义 UIA Python 包名；如果没有这行代码，依赖名称会散落且容易写错。


@dataclass(frozen=True)  # 新增代码+Phase35WindowsRealUIASmoke: 让安全窗口目标不可变；如果没有这行代码，目标标题或 cleanup 可能被无意改写。
class Phase35SafeWindowTarget:  # 新增代码+Phase35WindowsRealUIASmoke: 定义只允许 smoke 查找的安全窗口目标；如果没有这个类，harness 可能缺少“只碰自己窗口”的边界。
    title_hint: str  # 新增代码+Phase35WindowsRealUIASmoke: 保存安全窗口标题提示；如果没有这行代码，inventory 无法从桌面窗口中定位自有 Notepad。
    cleanup: Callable[[], None] | None = None  # 新增代码+Phase35WindowsRealUIASmoke: 保存清理函数；如果没有这行代码，smoke 结束后可能留下测试窗口或临时文件。


@dataclass(frozen=True)  # 新增代码+Phase35WindowsRealUIASmoke: 让 smoke 结果不可变；如果没有这行代码，验收前结果可能被调用方意外修改。
class Phase35RealUiaSmokeResult:  # 新增代码+Phase35WindowsRealUIASmoke: 定义 Phase35 smoke 的审计结果；如果没有这个类，成熟度字段会散落成难维护 dict。
    marker: str = PHASE35_REAL_UIA_SMOKE_MARKER  # 新增代码+Phase35WindowsRealUIASmoke: 保存阶段标记；如果没有这行代码，最终回答无法稳定带出验收标记。
    ok_token: str = PHASE35_REAL_UIA_SMOKE_OK_TOKEN  # 新增代码+Phase35WindowsRealUIASmoke: 保存命令成功 token；如果没有这行代码，日志验证无法确认命令真的执行。
    completed: bool = True  # 新增代码+Phase35WindowsRealUIASmoke: 表示诊断流程是否跑完；如果没有这行代码，缺依赖和崩溃会混在一起。
    platform: str = ""  # 新增代码+Phase35WindowsRealUIASmoke: 保存运行平台；如果没有这行代码，报告无法解释为什么没有触发 Windows UIA。
    platform_supported: bool = False  # 新增代码+Phase35WindowsRealUIASmoke: 标记是否为 Windows；如果没有这行代码，跨平台测试可能误认为功能失败。
    dependency: str = PHASE35_UIA_DEPENDENCY  # 新增代码+Phase35WindowsRealUIASmoke: 保存依赖名称；如果没有这行代码，用户不知道该补哪个包。
    dependency_reported: bool = True  # 新增代码+Phase35WindowsRealUIASmoke: 标记依赖状态已报告；如果没有这行代码，验收无法区分“没查依赖”和“依赖缺失”。
    dependency_available: bool = False  # 新增代码+Phase35WindowsRealUIASmoke: 标记 uiautomation 是否可用；如果没有这行代码，真实 UIA 是否具备条件不透明。
    real_uia_attempted: bool = False  # 新增代码+Phase35WindowsRealUIASmoke: 标记是否真的尝试安全窗口 UIA；如果没有这行代码，状态检查会被误当真实 smoke。
    real_uia_verified: bool = False  # 新增代码+Phase35WindowsRealUIASmoke: 标记是否读到真实 UIA 文本；如果没有这行代码，成熟度可能被虚报。
    safe_window_only: bool = True  # 新增代码+Phase35WindowsRealUIASmoke: 标记 smoke 只允许目标自有安全窗口；如果没有这行代码，验收无法证明没有扫描任意用户窗口。
    safe_window_found: bool = False  # 新增代码+Phase35WindowsRealUIASmoke: 标记是否定位到安全窗口；如果没有这行代码，定位失败无法和 provider 失败区分。
    safe_window_title: str = ""  # 新增代码+Phase35WindowsRealUIASmoke: 保存安全窗口标题；如果没有这行代码，失败时不知道查找目标是什么。
    hwnd: int = 0  # 新增代码+Phase35WindowsRealUIASmoke: 保存窗口句柄；如果没有这行代码，UIA 读取目标无法审计。
    backend: str = ""  # 新增代码+Phase35WindowsRealUIASmoke: 保存文本 provider 后端名；如果没有这行代码，结果来源不清楚。
    reason: str = ""  # 新增代码+Phase35WindowsRealUIASmoke: 保存成功或失败原因；如果没有这行代码，用户只能看到布尔值。
    fake_provider_used: bool = False  # 新增代码+Phase35WindowsRealUIASmoke: 明确生产 smoke 不用 fake 冒充真实结果；如果没有这行代码，验收可能混淆单测 seam 和真实能力。
    actions_expanded: bool = False  # 新增代码+Phase35WindowsRealUIASmoke: 明确 Phase35 不扩展鼠标键盘动作；如果没有这行代码，用户可能误以为 OS 操作已放开。
    cleaned_up: bool = False  # 新增代码+Phase35WindowsRealUIASmoke: 标记是否执行清理；如果没有这行代码，资源泄漏无法从结果中审计。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，把结果转成 JSON 友好字典；如果没有这段函数，CLI 和测试会重复转换逻辑。
        return asdict(self)  # 新增代码+Phase35WindowsRealUIASmoke: 返回 dataclass 字段字典；如果没有这行代码，调用方无法稳定序列化结果。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，Phase35RealUiaSmokeResult.to_dict 到此结束；如果没有这个边界说明，读者不容易看出序列化范围。


class Phase35NotepadSafeWindowLauncher:  # 新增代码+Phase35WindowsRealUIASmoke: 定义真实安全 Notepad 启动器；如果没有这个类，Phase35 无法在真实桌面创建自有窗口。
    def __init__(self, marker_text: str = "LearningAgent Phase35 real UIA smoke") -> None:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，初始化 Notepad smoke 参数；如果没有这段函数，临时目录和进程状态没有归属。
        self.marker_text = marker_text  # 新增代码+Phase35WindowsRealUIASmoke: 保存写入临时文件的文本；如果没有这行代码，Notepad 打开的内容不易识别。
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None  # 新增代码+Phase35WindowsRealUIASmoke: 保存临时目录对象；如果没有这行代码，cleanup 无法删除临时文件。
        self._process: subprocess.Popen[Any] | None = None  # 新增代码+Phase35WindowsRealUIASmoke: 保存 Notepad 进程；如果没有这行代码，cleanup 无法关闭测试窗口。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，Phase35NotepadSafeWindowLauncher.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def launch(self) -> Phase35SafeWindowTarget:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，创建临时文本并启动 Notepad；如果没有这段函数，真实 UIA smoke 没有安全目标。
        self._temp_dir = tempfile.TemporaryDirectory(prefix="learning-agent-phase35-")  # 新增代码+Phase35WindowsRealUIASmoke: 创建隔离临时目录；如果没有这行代码，测试文件可能散落到项目或用户目录。
        file_path = Path(self._temp_dir.name) / "LearningAgent-Phase35-RealUIASmoke.txt"  # 新增代码+Phase35WindowsRealUIASmoke: 固定临时文件名作为窗口标题线索；如果没有这行代码，inventory 很难可靠定位窗口。
        file_path.write_text(self.marker_text, encoding="utf-8")  # 新增代码+Phase35WindowsRealUIASmoke: 写入可识别文本；如果没有这行代码，Notepad 可能打开空白未命名窗口而难以定位。
        self._process = subprocess.Popen(["notepad.exe", str(file_path)])  # 新增代码+Phase35WindowsRealUIASmoke: 启动 Windows Notepad 打开临时文件；如果没有这行代码，真实桌面不会出现安全窗口。
        return Phase35SafeWindowTarget(title_hint=file_path.name, cleanup=self.cleanup)  # 新增代码+Phase35WindowsRealUIASmoke: 返回标题线索和清理函数；如果没有这行代码，harness 无法只观察自有窗口并善后。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，Phase35NotepadSafeWindowLauncher.launch 到此结束；如果没有这个边界说明，读者不容易看出启动范围。

    def cleanup(self) -> None:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，关闭 Notepad 并删除临时目录；如果没有这段函数，smoke 可能留下窗口和临时文件。
        process = self._process  # 新增代码+Phase35WindowsRealUIASmoke: 读取进程引用；如果没有这行代码，后续关闭逻辑会重复访问可变属性。
        if process is not None and process.poll() is None:  # 新增代码+Phase35WindowsRealUIASmoke: 只关闭仍在运行的 Notepad；如果没有这行代码，已退出进程可能触发无意义错误。
            process.terminate()  # 新增代码+Phase35WindowsRealUIASmoke: 请求 Notepad 正常退出；如果没有这行代码，安全窗口会残留在用户桌面。
            try:  # 新增代码+Phase35WindowsRealUIASmoke: 包住等待退出；如果没有这行代码，关闭慢时会直接抛错中断清理。
                process.wait(timeout=3)  # 新增代码+Phase35WindowsRealUIASmoke: 等待 Notepad 退出；如果没有这行代码，临时文件可能在进程占用时删除失败。
            except subprocess.TimeoutExpired:  # 新增代码+Phase35WindowsRealUIASmoke: 处理 Notepad 没及时退出；如果没有这行代码，卡住窗口会导致 smoke 清理失败。
                process.kill()  # 新增代码+Phase35WindowsRealUIASmoke: 强制结束测试窗口；如果没有这行代码，超时后窗口仍可能残留。
                process.wait(timeout=3)  # 新增代码+Phase35WindowsRealUIASmoke: 等待强制结束完成；如果没有这行代码，资源释放状态不确定。
        if self._temp_dir is not None:  # 新增代码+Phase35WindowsRealUIASmoke: 检查临时目录是否存在；如果没有这行代码，空 cleanup 会访问 None。
            self._temp_dir.cleanup()  # 新增代码+Phase35WindowsRealUIASmoke: 删除临时目录和文件；如果没有这行代码，磁盘会留下 smoke 文件。
            self._temp_dir = None  # 新增代码+Phase35WindowsRealUIASmoke: 清空临时目录引用；如果没有这行代码，重复 cleanup 可能再次清理同一对象。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，Phase35NotepadSafeWindowLauncher.cleanup 到此结束；如果没有这个边界说明，读者不容易看出清理范围。


def phase35_module_available(module_name: str) -> bool:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，探测模块是否可导入；如果没有这段函数，依赖检测无法被单元测试注入。
    return importlib.util.find_spec(module_name) is not None  # 新增代码+Phase35WindowsRealUIASmoke: 用 find_spec 检查依赖；如果没有这行代码，检测依赖可能触发模块副作用。
# 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，phase35_module_available 到此结束；如果没有这个边界说明，读者不容易看出依赖探测范围。


def phase35_dependency_status(module_available: Callable[[str], bool] | None = None, platform: str | None = None) -> dict[str, Any]:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，返回依赖与平台状态；如果没有这段函数，CLI 和 harness 会重复判断逻辑。
    current_platform = platform or sys.platform  # 新增代码+Phase35WindowsRealUIASmoke: 确定当前平台；如果没有这行代码，测试无法注入 win32/linux 场景。
    checker = module_available or phase35_module_available  # 新增代码+Phase35WindowsRealUIASmoke: 选择依赖检查函数；如果没有这行代码，单元测试无法稳定模拟依赖存在或缺失。
    dependency_available = bool(checker(PHASE35_UIA_DEPENDENCY))  # 新增代码+Phase35WindowsRealUIASmoke: 检查 uiautomation 是否存在；如果没有这行代码，Phase35 不知道能否尝试真实 UIA。
    return {"platform": current_platform, "platform_supported": current_platform == "win32", "dependency": PHASE35_UIA_DEPENDENCY, "dependency_reported": True, "dependency_available": dependency_available}  # 新增代码+Phase35WindowsRealUIASmoke: 返回稳定状态字典；如果没有这行代码，验收无法检查 dependency_reported=true。
# 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，phase35_dependency_status 到此结束；如果没有这个边界说明，读者不容易看出状态判断范围。


def _call_target_cleanup(target: Phase35SafeWindowTarget | None) -> bool:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，安全调用窗口清理函数；如果没有这段函数，清理逻辑会在多个异常路径重复。
    if target is None or target.cleanup is None:  # 新增代码+Phase35WindowsRealUIASmoke: 没有目标或没有清理函数时直接返回；如果没有这行代码，None cleanup 会导致异常。
        return False  # 新增代码+Phase35WindowsRealUIASmoke: 告诉调用方没有执行清理；如果没有这行代码，结果会误报 cleaned_up。
    try:  # 新增代码+Phase35WindowsRealUIASmoke: 包住清理调用；如果没有这行代码，清理失败会覆盖原本 smoke 诊断原因。
        target.cleanup()  # 新增代码+Phase35WindowsRealUIASmoke: 执行窗口和临时文件清理；如果没有这行代码，测试资源可能残留。
        return True  # 新增代码+Phase35WindowsRealUIASmoke: 标记清理成功调用；如果没有这行代码，结果无法反映 cleanup 已执行。
    except Exception:  # 新增代码+Phase35WindowsRealUIASmoke: 捕获清理异常；如果没有这行代码，cleanup 错误会让诊断流程崩溃。
        return False  # 新增代码+Phase35WindowsRealUIASmoke: 清理失败时诚实返回 False；如果没有这行代码，结果可能误报已清理。
# 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，_call_target_cleanup 到此结束；如果没有这个边界说明，读者不容易看出清理辅助范围。


def _launch_safe_window(launcher: Any | None) -> Phase35SafeWindowTarget:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，启动或调用注入的安全窗口 launcher；如果没有这段函数，真实和测试路径会混在主流程里。
    active_launcher = launcher or Phase35NotepadSafeWindowLauncher()  # 新增代码+Phase35WindowsRealUIASmoke: 没有注入时使用真实 Notepad launcher；如果没有这行代码，生产 smoke 没有默认行为。
    if hasattr(active_launcher, "launch"):  # 新增代码+Phase35WindowsRealUIASmoke: 支持对象式 launcher；如果没有这行代码，测试传入的 fake launcher 无法使用。
        return active_launcher.launch()  # 新增代码+Phase35WindowsRealUIASmoke: 调用对象 launch；如果没有这行代码，安全窗口目标不会被创建。
    return active_launcher()  # 新增代码+Phase35WindowsRealUIASmoke: 支持函数式 launcher；如果没有这行代码，简单函数 seam 无法注入。
# 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，_launch_safe_window 到此结束；如果没有这个边界说明，读者不容易看出 launcher 兼容范围。


def _find_safe_window(windows: list[dict[str, Any]], title_hint: str) -> dict[str, Any] | None:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，从 inventory 中查找自有安全窗口；如果没有这段函数，smoke 可能误选用户其他窗口。
    lowered_hint = title_hint.lower()  # 新增代码+Phase35WindowsRealUIASmoke: 标题线索转小写；如果没有这行代码，Notepad 标题大小写差异可能匹配失败。
    for window in windows:  # 新增代码+Phase35WindowsRealUIASmoke: 遍历当前可见窗口；如果没有这行代码，无法定位目标窗口。
        title = str(window.get("title_preview", window.get("title", ""))).lower()  # 新增代码+Phase35WindowsRealUIASmoke: 读取窗口标题；如果没有这行代码，无法和安全文件名匹配。
        if lowered_hint and lowered_hint in title:  # 新增代码+Phase35WindowsRealUIASmoke: 只接受标题包含自有文件名的窗口；如果没有这行代码，任意窗口可能被误认为目标。
            return dict(window)  # 新增代码+Phase35WindowsRealUIASmoke: 返回窗口副本；如果没有这行代码，调用方可能修改原始 snapshot。
    return None  # 新增代码+Phase35WindowsRealUIASmoke: 找不到目标时返回 None；如果没有这行代码，调用方无法区分未找到和异常。
# 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，_find_safe_window 到此结束；如果没有这个边界说明，读者不容易看出窗口匹配范围。


def _poll_for_safe_window(inventory: Any, title_hint: str, timeout_seconds: float, poll_interval_seconds: float, sleep: Callable[[float], None]) -> dict[str, Any] | None:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，轮询等待安全窗口出现；如果没有这段函数，Notepad 启动稍慢时 smoke 会误失败。
    deadline = time.time() + max(0.1, timeout_seconds)  # 新增代码+Phase35WindowsRealUIASmoke: 计算超时截止点；如果没有这行代码，等待可能无限持续或立即失败。
    while time.time() <= deadline:  # 新增代码+Phase35WindowsRealUIASmoke: 在超时前重复检查窗口；如果没有这行代码，异步窗口创建无法等待。
        snapshot = inventory.snapshot()  # 新增代码+Phase35WindowsRealUIASmoke: 获取窗口快照；如果没有这行代码，无法看到安全窗口是否出现。
        window = _find_safe_window(list(getattr(snapshot, "windows", []) or []), title_hint)  # 新增代码+Phase35WindowsRealUIASmoke: 在快照中查找自有窗口；如果没有这行代码，后续 UIA 没有可信 hwnd。
        if window is not None:  # 新增代码+Phase35WindowsRealUIASmoke: 判断是否找到安全窗口；如果没有这行代码，找到后仍会继续等待。
            return window  # 新增代码+Phase35WindowsRealUIASmoke: 返回匹配窗口；如果没有这行代码，调用方拿不到目标。
        sleep(poll_interval_seconds)  # 新增代码+Phase35WindowsRealUIASmoke: 短暂等待后重试；如果没有这行代码，轮询会占满 CPU。
    return None  # 新增代码+Phase35WindowsRealUIASmoke: 超时返回未找到；如果没有这行代码，调用方无法输出定位失败原因。
# 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，_poll_for_safe_window 到此结束；如果没有这个边界说明，读者不容易看出轮询范围。


def run_phase35_real_uia_smoke(module_available: Callable[[str], bool] | None = None, platform: str | None = None, inventory_factory: Callable[[], Any] | None = None, text_provider_factory: Callable[[], Any] | None = None, launcher: Any | None = None, timeout_seconds: float = 8.0, poll_interval_seconds: float = 0.25, sleep: Callable[[float], None] = time.sleep) -> Phase35RealUiaSmokeResult:  # 修改代码+Phase35WindowsRealUIASmoke: 函数段开始，执行 Phase35 真实 UIA 安全窗口 smoke；如果没有这段函数，项目没有可自动验收的真实 UIA 尝试入口。
    status = phase35_dependency_status(module_available=module_available, platform=platform)  # 修改代码+Phase35WindowsRealUIASmoke: 先读取平台和依赖状态；如果没有这行代码，后续可能在不具备条件时误触桌面。
    current_platform = str(status["platform"])  # 修改代码+Phase35WindowsRealUIASmoke: 保存平台字符串；如果没有这行代码，结果字段可能类型不稳定。
    if not status["platform_supported"]:  # 修改代码+Phase35WindowsRealUIASmoke: 非 Windows 平台直接停止；如果没有这行代码，Linux/macOS 测试会误调用 Windows API。
        return Phase35RealUiaSmokeResult(platform=current_platform, platform_supported=False, dependency_available=bool(status["dependency_available"]), reason="当前平台不是 Windows，Phase35 只报告状态，不触发真实 UIA。")  # 修改代码+Phase35WindowsRealUIASmoke: 返回诚实平台不支持结果；如果没有这行代码，跨平台环境会被误判为功能崩溃。
    if not status["dependency_available"]:  # 修改代码+Phase35WindowsRealUIASmoke: 缺少 uiautomation 时不启动真实窗口；如果没有这行代码，依赖缺失也可能触发不必要桌面操作。
        return Phase35RealUiaSmokeResult(platform=current_platform, platform_supported=True, dependency_available=False, reason="缺少 uiautomation 依赖，已诚实报告，未使用 fake provider 冒充真实 UIA。")  # 修改代码+Phase35WindowsRealUIASmoke: 返回依赖缺失结果；如果没有这行代码，验收可能误报真实 UIA 已完成。
    target: Phase35SafeWindowTarget | None = None  # 修改代码+Phase35WindowsRealUIASmoke: 初始化安全窗口目标；如果没有这行代码，清理时变量可能不存在。
    cleaned_up = False  # 修改代码+Phase35WindowsRealUIASmoke: 初始化清理状态；如果没有这行代码，结果无法说明是否善后。
    result = Phase35RealUiaSmokeResult(platform=current_platform, platform_supported=True, dependency_available=True, real_uia_attempted=True, reason="Phase35 真实 UIA smoke 尚未产生结果。")  # 修改代码+Phase35WindowsRealUIASmoke: 先准备保底结果；如果没有这行代码，异常路径可能没有结构化返回。
    try:  # 修改代码+Phase35WindowsRealUIASmoke: 包住真实窗口和 UIA 尝试；如果没有这行代码，异常会绕过结构化诊断。
        target = _launch_safe_window(launcher)  # 修改代码+Phase35WindowsRealUIASmoke: 启动或获取安全窗口目标；如果没有这行代码，真实 UIA 没有可信 hwnd。
        inventory = inventory_factory() if inventory_factory is not None else WindowsWindowInventoryProbe()  # 修改代码+Phase35WindowsRealUIASmoke: 创建真实或注入的窗口 inventory；如果没有这行代码，无法定位安全窗口。
        window = _poll_for_safe_window(inventory, target.title_hint, timeout_seconds, poll_interval_seconds, sleep)  # 修改代码+Phase35WindowsRealUIASmoke: 等待自有安全窗口出现；如果没有这行代码，Notepad 启动延迟会导致误失败。
        if window is None:  # 修改代码+Phase35WindowsRealUIASmoke: 检查是否找到窗口；如果没有这行代码，后续会对空目标解析 hwnd。
            result = Phase35RealUiaSmokeResult(platform=current_platform, platform_supported=True, dependency_available=True, real_uia_attempted=True, safe_window_title=target.title_hint, reason="未在真实 inventory 中找到 Phase35 自有安全窗口，未声明 UIA 已验证。")  # 修改代码+Phase35WindowsRealUIASmoke: 保存定位失败结果；如果没有这行代码，找不到窗口可能被误当 provider 失败。
        else:  # 修改代码+Phase35WindowsRealUIASmoke: 找到窗口时继续解析 hwnd；如果没有这行代码，成功路径和失败路径会混在一起。
            hwnd = parse_hwnd_from_window(window)  # 修改代码+Phase35WindowsRealUIASmoke: 从窗口引用解析 hwnd；如果没有这行代码，UIA provider 不知道读取哪个窗口。
            if hwnd <= 0:  # 修改代码+Phase35WindowsRealUIASmoke: 拒绝无效 hwnd；如果没有这行代码，0 句柄可能传入 UIA。
                result = Phase35RealUiaSmokeResult(platform=current_platform, platform_supported=True, dependency_available=True, real_uia_attempted=True, safe_window_found=True, safe_window_title=target.title_hint, reason="安全窗口 hwnd 无效，未声明 UIA 已验证。")  # 修改代码+Phase35WindowsRealUIASmoke: 保存 hwnd 无效结果；如果没有这行代码，错误目标会被误读。
            else:  # 修改代码+Phase35WindowsRealUIASmoke: hwnd 有效时才读取 UIA 文本；如果没有这行代码，坏句柄也可能进入 provider。
                provider = text_provider_factory() if text_provider_factory is not None else WindowsUiautomationTextProvider(platform=current_platform)  # 修改代码+Phase35WindowsRealUIASmoke: 创建真实或注入的 UIA 文本 provider；如果没有这行代码，无法执行控件树读取。
                text_result = provider.read_window_text(hwnd)  # 修改代码+Phase35WindowsRealUIASmoke: 读取安全窗口 UIA 文本；如果没有这行代码，Phase35 只停留在窗口枚举。
                captured = isinstance(text_result, NativeWindowTextResult) and bool(text_result.captured)  # 修改代码+Phase35WindowsRealUIASmoke: 判断 provider 是否真正捕获文本；如果没有这行代码，任意返回值都可能被当成功。
                backend = str(getattr(text_result, "backend", ""))  # 修改代码+Phase35WindowsRealUIASmoke: 读取 provider 后端名；如果没有这行代码，结果无法说明是否来自 uiautomation_client。
                reason = str(getattr(text_result, "reason", "")) or ("UIA 安全窗口 smoke 成功。" if captured else "UIA provider 未捕获文本。")  # 修改代码+Phase35WindowsRealUIASmoke: 生成可读原因；如果没有这行代码，失败时只有布尔值。
                result = Phase35RealUiaSmokeResult(platform=current_platform, platform_supported=True, dependency_available=True, real_uia_attempted=True, real_uia_verified=captured, safe_window_found=True, safe_window_title=target.title_hint, hwnd=hwnd, backend=backend, reason=reason)  # 修改代码+Phase35WindowsRealUIASmoke: 保存真实 UIA 尝试结果；如果没有这行代码，调用方拿不到验证证据。
    except Exception as error:  # 修改代码+Phase35WindowsRealUIASmoke: 捕获真实 smoke 异常；如果没有这行代码，桌面权限或 Notepad 问题会让 agent 崩溃。
        result = Phase35RealUiaSmokeResult(platform=current_platform, platform_supported=True, dependency_available=True, real_uia_attempted=True, safe_window_title=getattr(target, "title_hint", ""), reason=f"Phase35 真实 UIA smoke 异常：{type(error).__name__}")  # 修改代码+Phase35WindowsRealUIASmoke: 保存异常类型但不泄露本地细节；如果没有这行代码，用户只会看到堆栈。
    finally:  # 修改代码+Phase35WindowsRealUIASmoke: 无论成功失败都尝试清理；如果没有这行代码，测试窗口或临时文件可能残留。
        cleaned_up = _call_target_cleanup(target)  # 修改代码+Phase35WindowsRealUIASmoke: 调用清理 helper；如果没有这行代码，安全窗口生命周期没有保障。
    return replace(result, cleaned_up=cleaned_up)  # 修改代码+Phase35WindowsRealUIASmoke: 在清理后返回更新过的结果；如果没有这行代码，cleaned_up 字段会一直停留在 False。
# 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，run_phase35_real_uia_smoke 到此结束；如果没有这个边界说明，读者不容易看出 smoke 主流程范围。


def phase35_cli_line(result: Phase35RealUiaSmokeResult) -> str:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，生成可见终端验收行；如果没有这段函数，scenario 要解析大段 JSON 才能验收。
    data = result.to_dict()  # 新增代码+Phase35WindowsRealUIASmoke: 转为字典方便取字段；如果没有这行代码，格式化逻辑会直接依赖 dataclass 属性。
    return f"{PHASE35_REAL_UIA_SMOKE_OK_TOKEN} dependency_reported={str(data['dependency_reported']).lower()} fake_provider_used={str(data['fake_provider_used']).lower()} actions_expanded={str(data['actions_expanded']).lower()} safe_window_only={str(data['safe_window_only']).lower()} dependency_available={str(data['dependency_available']).lower()} real_uia_attempted={str(data['real_uia_attempted']).lower()} real_uia_verified={str(data['real_uia_verified']).lower()} marker={PHASE35_REAL_UIA_SMOKE_MARKER}"  # 新增代码+Phase35WindowsRealUIASmoke: 返回稳定 token 行；如果没有这行代码，可见终端 verifier 难以跨依赖状态检查成功。
# 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，phase35_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 行格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，提供 python -m 入口；如果没有这段函数，可见终端验收无法直接运行模块。
    _ = argv  # 新增代码+Phase35WindowsRealUIASmoke: 保留 argv 参数以便未来扩展；如果没有这行代码，静态检查可能提示未使用参数。
    result = run_phase35_real_uia_smoke()  # 新增代码+Phase35WindowsRealUIASmoke: 执行一次真实安全窗口 smoke 或依赖诊断；如果没有这行代码，CLI 不会触发 Phase35 能力。
    print(phase35_cli_line(result))  # 新增代码+Phase35WindowsRealUIASmoke: 打印稳定验收 token；如果没有这行代码，debug log 匹配不到成功证据。
    print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))  # 新增代码+Phase35WindowsRealUIASmoke: 打印结构化结果；如果没有这行代码，用户难以理解缺依赖或失败原因。
    print(PHASE35_REAL_UIA_SMOKE_MARKER)  # 新增代码+Phase35WindowsRealUIASmoke: 单独打印阶段标记；如果没有这行代码，最终回答复制时容易漏掉 marker。
    return 0 if result.completed else 1  # 新增代码+Phase35WindowsRealUIASmoke: 诊断完成即返回成功码；如果没有这行代码，诚实缺依赖会被误当命令失败。
# 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出 CLI 主入口范围。


if __name__ == "__main__":  # 新增代码+Phase35WindowsRealUIASmoke: 允许 python -m 或直接运行时执行；如果没有这行代码，模块作为脚本不会启动 main。
    raise SystemExit(main())  # 新增代码+Phase35WindowsRealUIASmoke: 用 main 返回码退出；如果没有这行代码，命令行无法表达执行状态。
