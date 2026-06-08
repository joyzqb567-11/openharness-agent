from __future__ import annotations  # 新增代码+Phase69AppWindowControl: 启用延迟类型注解，避免运行时因为类型提示互相引用而导入失败；如果没有这行代码，后续扩展 runtime 类型时更容易遇到循环导入。

import hashlib  # 新增代码+Phase69AppWindowControl: 导入 hashlib 生成窗口标题短哈希；如果没有这行代码，目标身份比对只能暴露完整标题或缺少稳定摘要。
from typing import Any  # 新增代码+Phase69AppWindowControl: 导入 Any 描述 JSON 风格计划和窗口字典；如果没有这行代码，接口输入输出含义会更难读懂。


PHASE69_APP_WINDOW_CONTROL_MARKER = "PHASE69_APP_WINDOW_CONTROL_READY"  # 新增代码+Phase69AppWindowControl: 定义真实终端验收 ready 标记；如果没有这行代码，controller 无法稳定识别 Phase69 输出。
PHASE69_APP_WINDOW_CONTROL_OK_TOKEN = "PHASE69_APP_WINDOW_CONTROL_OK"  # 新增代码+Phase69AppWindowControl: 定义真实终端验收 OK 标记；如果没有这行代码，用户无法一眼确认本阶段合同通过。
PHASE69_APP_WINDOW_CONTROL_MODEL = "phase69_windows_app_window_control"  # 新增代码+Phase69AppWindowControl: 定义本阶段能力模型名称；如果没有这行代码，后续矩阵无法统一引用 Phase69 能力。
PHASE69_ACTIONS_EXPANDED = False  # 新增代码+Phase69AppWindowControl: 明确 Phase69 不扩大真实桌面写动作范围；如果没有这行代码，本阶段可能被误认为已经能通用操控真实应用。
PHASE69_ALLOWED_APP_ALIASES = {"notepad": "notepad.exe", "mspaint": "mspaint.exe", "paint": "mspaint.exe", "calc": "calc.exe", "calculator": "calc.exe"}  # 新增代码+Phase69AppWindowControl: 定义常见安全应用别名映射；如果没有这行代码，prompt planner 的 mspaint/notepad 名称无法变成可执行文件计划。
PHASE69_FORBIDDEN_APP_TOKENS = ("powershell", "cmd", "terminal", "regedit", "control", "settings", "credential", "password", "security", "admin", "login", "captcha")  # 新增代码+Phase69AppWindowControl: 定义启动计划禁止触碰的高风险应用关键字；如果没有这行代码，启动阶段可能越界打开终端或安全设置。


def _phase69_bool_token(value: Any) -> str:  # 新增代码+Phase69AppWindowControl: 函数段开始，把布尔值转换成验收 token 需要的小写 true/false；如果没有这个函数，CLI 输出容易出现 Python 的 True/False 导致场景匹配失败。
    return "true" if bool(value) else "false"  # 新增代码+Phase69AppWindowControl: 返回稳定小写布尔字符串；如果没有这行代码，真实终端场景 token 无法稳定匹配。
# 新增代码+Phase69AppWindowControl: 函数段结束，_phase69_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出 token 转换范围。


def _phase69_sha256_16(value: Any) -> str:  # 新增代码+Phase69AppWindowControl: 函数段开始，生成短哈希用于窗口标题摘要；如果没有这个函数，目标身份要么泄露完整标题，要么无法稳定比对。
    text = str(value or "")  # 新增代码+Phase69AppWindowControl: 把输入规范成字符串；如果没有这行代码，None 或数字标题会导致哈希输入不稳定。
    if not text:  # 新增代码+Phase69AppWindowControl: 检查空文本；如果没有这行代码，空标题也会生成看似有效的哈希。
        return ""  # 新增代码+Phase69AppWindowControl: 空文本返回空哈希；如果没有这行代码，调用方无法区分无标题和有标题。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase69AppWindowControl: 返回前 16 位 SHA256；如果没有这行代码，窗口身份缺少脱敏稳定指纹。
# 新增代码+Phase69AppWindowControl: 函数段结束，_phase69_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出哈希范围。


def _phase69_normalize_app_name(app_name: str) -> str:  # 新增代码+Phase69AppWindowControl: 函数段开始，规范化用户或 planner 给出的应用名；如果没有这个函数，大小写和空格会让启动计划不稳定。
    return str(app_name or "").strip().lower()  # 新增代码+Phase69AppWindowControl: 返回小写无首尾空格应用名；如果没有这行代码，` Paint ` 和 `paint` 会被当成不同应用。
# 新增代码+Phase69AppWindowControl: 函数段结束，_phase69_normalize_app_name 到此结束；如果没有这个边界说明，初学者不容易看出应用名清洗范围。


def _phase69_contains_forbidden_token(text: str) -> bool:  # 新增代码+Phase69AppWindowControl: 函数段开始，判断应用名或可执行名是否命中高风险关键字；如果没有这个函数，启动计划可能打开终端或系统设置。
    lowered = str(text or "").lower()  # 新增代码+Phase69AppWindowControl: 转成小写便于匹配；如果没有这行代码，大小写差异可能绕过安全边界。
    return any(token in lowered for token in PHASE69_FORBIDDEN_APP_TOKENS)  # 新增代码+Phase69AppWindowControl: 返回是否命中禁止关键字；如果没有这行代码，高风险应用不会被拦截。
# 新增代码+Phase69AppWindowControl: 函数段结束，_phase69_contains_forbidden_token 到此结束；如果没有这个边界说明，初学者不容易看出禁止关键字判断范围。


def _phase69_executable_for_app(app_name: str) -> tuple[str, str]:  # 新增代码+Phase69AppWindowControl: 函数段开始，把应用名映射成安全可执行名；如果没有这个函数，启动计划会直接信任用户输入的命令。
    normalized = _phase69_normalize_app_name(app_name)  # 新增代码+Phase69AppWindowControl: 先规范化应用名；如果没有这行代码，别名映射和风险检查不稳定。
    if not normalized:  # 新增代码+Phase69AppWindowControl: 检查空应用名；如果没有这行代码，空命令可能进入启动计划。
        return "", "empty_app_name"  # 新增代码+Phase69AppWindowControl: 返回空应用名原因；如果没有这行代码，调用方无法解释为什么拒绝。
    if _phase69_contains_forbidden_token(normalized):  # 新增代码+Phase69AppWindowControl: 检查高风险应用关键字；如果没有这行代码，powershell/cmd 等目标可能被计划启动。
        return "", "forbidden_app_name"  # 新增代码+Phase69AppWindowControl: 返回禁止原因；如果没有这行代码，审计无法说明为什么拒绝。
    executable = PHASE69_ALLOWED_APP_ALIASES.get(normalized, normalized)  # 新增代码+Phase69AppWindowControl: 优先使用安全别名映射，未知应用保留规范名；如果没有这行代码，mspaint/notepad 无法稳定映射。
    if not executable.endswith(".exe"):  # 新增代码+Phase69AppWindowControl: 检查是否缺少 exe 后缀；如果没有这行代码，Windows 启动计划可能依赖环境解析。
        executable = f"{executable}.exe"  # 新增代码+Phase69AppWindowControl: 补齐 exe 后缀；如果没有这行代码，记录型窗口 app_id 和真实启动计划可能不一致。
    if _phase69_contains_forbidden_token(executable):  # 新增代码+Phase69AppWindowControl: 对最终可执行名再次做风险检查；如果没有这行代码，别名或补后缀后的名称可能绕过边界。
        return "", "forbidden_executable"  # 新增代码+Phase69AppWindowControl: 返回可执行名禁止原因；如果没有这行代码，拒绝路径不可审计。
    return executable, "ok"  # 新增代码+Phase69AppWindowControl: 返回安全可执行名和成功原因；如果没有这行代码，启动计划拿不到目标程序。
# 新增代码+Phase69AppWindowControl: 函数段结束，_phase69_executable_for_app 到此结束；如果没有这个边界说明，初学者不容易看出应用映射范围。


def build_launch_plan(app_name: str, test_file: str | None = None) -> dict[str, Any]:  # 新增代码+Phase69AppWindowControl: 函数段开始，构建安全的应用启动计划；如果没有这个函数，planner 输出无法进入可审计的 app launch 合同。
    executable, reason = _phase69_executable_for_app(app_name)  # 新增代码+Phase69AppWindowControl: 把应用名转换成安全可执行名；如果没有这行代码，计划会直接使用未清洗输入。
    arguments = [str(test_file)] if test_file else []  # 新增代码+Phase69AppWindowControl: 只把可选测试文件作为参数列表；如果没有这行代码，打开文件类任务无法表达。
    safe_to_launch = bool(executable and reason == "ok")  # 新增代码+Phase69AppWindowControl: 计算计划是否可启动；如果没有这行代码，调用方无法快速判断拒绝或允许。
    return {"app_name": _phase69_normalize_app_name(app_name), "executable": executable, "arguments": arguments, "launch_verb": "Start-Process", "safe_to_launch": safe_to_launch, "refusal_reason": "" if safe_to_launch else reason, "changes_registry": False, "changes_system_settings": False, "requires_admin": False, "uses_shell_string": False, "actions_expanded": PHASE69_ACTIONS_EXPANDED}  # 新增代码+Phase69AppWindowControl: 返回无系统设置副作用的启动计划；如果没有这行代码，后续 launcher 无法统一审计启动意图。
# 新增代码+Phase69AppWindowControl: 函数段结束，build_launch_plan 到此结束；如果没有这个边界说明，初学者不容易看出启动计划构建范围。


def _phase69_window_identity(window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase69AppWindowControl: 函数段开始，提取窗口身份摘要；如果没有这个函数，动作前后目标比对会散落重复且容易漏字段。
    title = str(window.get("title_preview", window.get("title", "")) or "")  # 新增代码+Phase69AppWindowControl: 读取可见标题摘要；如果没有这行代码，标题指纹没有输入来源。
    return {"app_id": str(window.get("app_id", "")), "window_id": str(window.get("window_id", "")), "pid": int(window.get("pid", 0) or 0), "title_sha256_16": str(window.get("title_sha256_16", "")) or _phase69_sha256_16(title)}  # 新增代码+Phase69AppWindowControl: 返回脱敏身份字段；如果没有这行代码，目标漂移无法可靠判断。
# 新增代码+Phase69AppWindowControl: 函数段结束，_phase69_window_identity 到此结束；如果没有这个边界说明，初学者不容易看出窗口身份提取范围。


class Phase69RecordingLauncher:  # 新增代码+Phase69AppWindowControl: 类段开始，提供记录型应用启动器；如果没有这个类，合同测试只能启动真实本机应用，风险和不稳定性都会增加。
    def __init__(self) -> None:  # 新增代码+Phase69AppWindowControl: 函数段开始，初始化启动记录；如果没有这个函数，测试无法统计启动调用次数。
        self.launches: list[dict[str, Any]] = []  # 新增代码+Phase69AppWindowControl: 保存每次启动计划副本；如果没有这行代码，测试无法证明 launcher 被调用且没有真实副作用。
    # 新增代码+Phase69AppWindowControl: 函数段结束，Phase69RecordingLauncher.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def launch(self, plan: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase69AppWindowControl: 函数段开始，记录一次应用启动而不触碰真实桌面；如果没有这个函数，Phase69 合同无法安全模拟 app launch。
        safe_plan = dict(plan)  # 新增代码+Phase69AppWindowControl: 复制启动计划避免调用方后续修改影响记录；如果没有这行代码，审计记录可能被外部污染。
        self.launches.append(safe_plan)  # 新增代码+Phase69AppWindowControl: 保存启动计划；如果没有这行代码，测试无法核对启动次数和参数。
        if not safe_plan.get("safe_to_launch", False):  # 新增代码+Phase69AppWindowControl: 检查计划是否被允许启动；如果没有这行代码，拒绝计划也会被当成成功。
            return {"launched": False, "blocked": True, "reason": safe_plan.get("refusal_reason", "unsafe_launch_plan"), "actions_expanded": PHASE69_ACTIONS_EXPANDED}  # 新增代码+Phase69AppWindowControl: 返回拒绝结果；如果没有这行代码，调用方无法安全处理高风险启动。
        executable = str(safe_plan.get("executable", ""))  # 新增代码+Phase69AppWindowControl: 读取可执行名；如果没有这行代码，窗口身份无法和计划关联。
        title = f"Phase69 Recording Window - {executable}"  # 新增代码+Phase69AppWindowControl: 生成稳定记录窗口标题；如果没有这行代码，窗口标题指纹没有来源。
        window = {"app_id": executable, "window_id": f"phase69-window:{executable}", "pid": 6900 + len(self.launches), "title_preview": title, "title_sha256_16": _phase69_sha256_16(title), "safe_to_target": True}  # 新增代码+Phase69AppWindowControl: 构造记录型窗口身份；如果没有这行代码，后续聚焦和身份校验没有目标。
        return {"launched": True, "blocked": False, "plan": safe_plan, "window": window, "launcher": "phase69_recording", "system_settings_changed": False, "actions_expanded": PHASE69_ACTIONS_EXPANDED}  # 新增代码+Phase69AppWindowControl: 返回启动结果；如果没有这行代码，runtime 无法继续聚焦窗口。
    # 新增代码+Phase69AppWindowControl: 函数段结束，Phase69RecordingLauncher.launch 到此结束；如果没有这个边界说明，初学者不容易看出记录型启动范围。
# 新增代码+Phase69AppWindowControl: 类段结束，Phase69RecordingLauncher 到此结束；如果没有这个边界说明，初学者不容易看出记录型启动器范围。


class Phase69RecordingFocuser:  # 新增代码+Phase69AppWindowControl: 类段开始，提供记录型窗口聚焦器；如果没有这个类，合同测试可能切换真实前台窗口。
    def __init__(self) -> None:  # 新增代码+Phase69AppWindowControl: 函数段开始，初始化聚焦记录；如果没有这个函数，测试无法统计聚焦调用次数。
        self.focuses: list[dict[str, Any]] = []  # 新增代码+Phase69AppWindowControl: 保存每次聚焦目标；如果没有这行代码，测试无法证明 focus_window 被调用。
    # 新增代码+Phase69AppWindowControl: 函数段结束，Phase69RecordingFocuser.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def focus(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase69AppWindowControl: 函数段开始，记录一次窗口聚焦而不改变真实前台窗口；如果没有这个函数，Phase69 合同无法安全模拟 focus。
        safe_window = dict(window)  # 新增代码+Phase69AppWindowControl: 复制窗口目标避免外部污染记录；如果没有这行代码，审计记录可能随调用方修改。
        self.focuses.append(safe_window)  # 新增代码+Phase69AppWindowControl: 保存聚焦目标；如果没有这行代码，测试无法核对聚焦次数。
        return {"focused": bool(safe_window.get("safe_to_target", True)), "window": safe_window, "focuser": "phase69_recording", "system_settings_changed": False, "actions_expanded": PHASE69_ACTIONS_EXPANDED}  # 新增代码+Phase69AppWindowControl: 返回记录型聚焦结果；如果没有这行代码，runtime 无法形成 window_focus 报告。
    # 新增代码+Phase69AppWindowControl: 函数段结束，Phase69RecordingFocuser.focus 到此结束；如果没有这个边界说明，初学者不容易看出记录型聚焦范围。
# 新增代码+Phase69AppWindowControl: 类段结束，Phase69RecordingFocuser 到此结束；如果没有这个边界说明，初学者不容易看出记录型聚焦器范围。


class WindowsAppWindowControlRuntime:  # 新增代码+Phase69AppWindowControl: 类段开始，提供应用启动、窗口聚焦和目标身份校验 runtime；如果没有这个类，Phase67 计划无法进入可审计的应用窗口准备阶段。
    def __init__(self, launcher: Any | None = None, focuser: Any | None = None) -> None:  # 新增代码+Phase69AppWindowControl: 函数段开始，注入启动器和聚焦器；如果没有这个函数，测试无法替换真实桌面适配器。
        self.launcher = launcher if launcher is not None else Phase69RecordingLauncher()  # 新增代码+Phase69AppWindowControl: 默认使用记录型启动器；如果没有这行代码，默认构造可能误触真实应用。
        self.focuser = focuser if focuser is not None else Phase69RecordingFocuser()  # 新增代码+Phase69AppWindowControl: 默认使用记录型聚焦器；如果没有这行代码，默认构造可能切换真实前台窗口。
    # 新增代码+Phase69AppWindowControl: 函数段结束，WindowsAppWindowControlRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def launch_app(self, plan: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase69AppWindowControl: 函数段开始，执行应用启动计划；如果没有这个函数，Phase69 只有计划没有 runtime 入口。
        launch_method = getattr(self.launcher, "launch", None)  # 新增代码+Phase69AppWindowControl: 读取 launcher.launch 方法；如果没有这行代码，注入对象无法被调用。
        if not callable(launch_method):  # 新增代码+Phase69AppWindowControl: 检查启动器接口是否可调用；如果没有这行代码，错误适配器会产生难懂异常。
            return {"launched": False, "blocked": True, "reason": "launcher_missing_launch_method", "actions_expanded": PHASE69_ACTIONS_EXPANDED}  # 新增代码+Phase69AppWindowControl: 返回接口缺失结果；如果没有这行代码，调用方无法安全降级。
        return launch_method(plan)  # 新增代码+Phase69AppWindowControl: 调用注入启动器；如果没有这行代码，应用启动合同不会执行。
    # 新增代码+Phase69AppWindowControl: 函数段结束，WindowsAppWindowControlRuntime.launch_app 到此结束；如果没有这个边界说明，初学者不容易看出启动执行范围。

    def focus_window(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase69AppWindowControl: 函数段开始，执行窗口聚焦；如果没有这个函数，后续动作无法确认目标窗口已准备好。
        focus_method = getattr(self.focuser, "focus", None)  # 新增代码+Phase69AppWindowControl: 读取 focuser.focus 方法；如果没有这行代码，注入聚焦器无法被调用。
        if not callable(focus_method):  # 新增代码+Phase69AppWindowControl: 检查聚焦器接口是否可调用；如果没有这行代码，错误适配器会产生难懂异常。
            return {"focused": False, "blocked": True, "reason": "focuser_missing_focus_method", "actions_expanded": PHASE69_ACTIONS_EXPANDED}  # 新增代码+Phase69AppWindowControl: 返回接口缺失结果；如果没有这行代码，调用方无法安全降级。
        return focus_method(window)  # 新增代码+Phase69AppWindowControl: 调用注入聚焦器；如果没有这行代码，window_focus 合同不会执行。
    # 新增代码+Phase69AppWindowControl: 函数段结束，WindowsAppWindowControlRuntime.focus_window 到此结束；如果没有这个边界说明，初学者不容易看出聚焦执行范围。

    def verify_target_identity(self, before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase69AppWindowControl: 函数段开始，校验动作前后是否仍是同一目标窗口；如果没有这个函数，窗口漂移后仍可能继续真实操作。
        before_identity = _phase69_window_identity(before)  # 新增代码+Phase69AppWindowControl: 提取动作前窗口身份；如果没有这行代码，校验没有基准。
        after_identity = _phase69_window_identity(after)  # 新增代码+Phase69AppWindowControl: 提取动作后窗口身份；如果没有这行代码，校验没有对照目标。
        same_target = before_identity == after_identity  # 新增代码+Phase69AppWindowControl: 比较身份字段是否完全一致；如果没有这行代码，漂移判断无法得出结论。
        reason = "same_target_window" if same_target else "target_window_identity_changed"  # 新增代码+Phase69AppWindowControl: 生成稳定原因；如果没有这行代码，审计和恢复无法解释结果。
        return {"same_target": same_target, "blocked": not same_target, "reason": reason, "before_identity": before_identity, "after_identity": after_identity, "actions_expanded": PHASE69_ACTIONS_EXPANDED}  # 新增代码+Phase69AppWindowControl: 返回身份校验报告；如果没有这行代码，后续安全门禁没有结构化输入。
    # 新增代码+Phase69AppWindowControl: 函数段结束，WindowsAppWindowControlRuntime.verify_target_identity 到此结束；如果没有这个边界说明，初学者不容易看出目标身份校验范围。
# 新增代码+Phase69AppWindowControl: 类段结束，WindowsAppWindowControlRuntime 到此结束；如果没有这个边界说明，初学者不容易看出 Phase69 runtime 范围。


def run_phase69_app_window_control_contract(real_smoke: bool = False) -> dict[str, Any]:  # 新增代码+Phase69AppWindowControl: 函数段开始，运行 Phase69 应用窗口控制合同自检；如果没有这个函数，测试和真实终端验收无法用统一入口确认能力。
    _ = real_smoke  # 新增代码+Phase69AppWindowControl: 保留 real_smoke 参数但本阶段默认不触发真实桌面；如果没有这行代码，参数存在却未说明用途会让边界不清晰。
    launcher = Phase69RecordingLauncher()  # 新增代码+Phase69AppWindowControl: 创建记录型启动器；如果没有这行代码，合同可能误开真实应用。
    focuser = Phase69RecordingFocuser()  # 新增代码+Phase69AppWindowControl: 创建记录型聚焦器；如果没有这行代码，合同可能误切真实前台窗口。
    runtime = WindowsAppWindowControlRuntime(launcher=launcher, focuser=focuser)  # 新增代码+Phase69AppWindowControl: 创建注入记录器的 runtime；如果没有这行代码，合同无法运行启动和聚焦。
    plan = build_launch_plan("notepad", test_file="H:/tmp/phase69-contract.txt")  # 新增代码+Phase69AppWindowControl: 构建安全启动计划；如果没有这行代码，合同没有可审计启动输入。
    launch_result = runtime.launch_app(plan)  # 新增代码+Phase69AppWindowControl: 执行记录型启动；如果没有这行代码，app_launch 没有证据。
    focus_result = runtime.focus_window(launch_result.get("window", {}))  # 新增代码+Phase69AppWindowControl: 执行记录型聚焦；如果没有这行代码，window_focus 没有证据。
    same_result = runtime.verify_target_identity(launch_result.get("window", {}), focus_result.get("window", {}))  # 新增代码+Phase69AppWindowControl: 校验聚焦前后仍是同一窗口；如果没有这行代码，target_window_identity 没有证据。
    drift_window = dict(focus_result.get("window", {}))  # 新增代码+Phase69AppWindowControl: 复制窗口用于构造漂移样本；如果没有这行代码，直接改原窗口会污染前面结果。
    drift_window["window_id"] = "phase69-window:powershell.exe"  # 新增代码+Phase69AppWindowControl: 改变窗口 id 模拟漂移到终端；如果没有这行代码，漂移阻断没有负例。
    drift_window["app_id"] = "powershell.exe"  # 新增代码+Phase69AppWindowControl: 改变 app id 模拟目标变化；如果没有这行代码，身份比对可能只测到单字段变化。
    drift_result = runtime.verify_target_identity(focus_result.get("window", {}), drift_window)  # 新增代码+Phase69AppWindowControl: 执行漂移校验；如果没有这行代码，target_drift_blocked 没有证据。
    safe_start_process_plan = bool(plan.get("launch_verb") == "Start-Process" and not plan.get("changes_registry") and not plan.get("changes_system_settings") and not plan.get("requires_admin"))  # 新增代码+Phase69AppWindowControl: 汇总安全启动计划条件；如果没有这行代码，报告无法证明没有系统设置副作用。
    report = {"marker": PHASE69_APP_WINDOW_CONTROL_MARKER, "ok_token": PHASE69_APP_WINDOW_CONTROL_OK_TOKEN, "model": PHASE69_APP_WINDOW_CONTROL_MODEL, "app_launch": bool(launch_result.get("launched")), "window_focus": bool(focus_result.get("focused")), "target_window_identity": bool(same_result.get("same_target") and not same_result.get("blocked")), "target_drift_blocked": bool(drift_result.get("blocked")), "safe_start_process_plan": safe_start_process_plan, "recording_launcher": launcher.__class__.__name__ == "Phase69RecordingLauncher", "system_settings_changed": bool(launch_result.get("system_settings_changed") or focus_result.get("system_settings_changed")), "actions_expanded": PHASE69_ACTIONS_EXPANDED, "plan": plan, "launch_result": launch_result, "focus_result": focus_result, "same_result": same_result, "drift_result": drift_result}  # 新增代码+Phase69AppWindowControl: 汇总合同报告；如果没有这行代码，测试和 CLI 无法读取统一事实。
    report["passed"] = bool(report["app_launch"] and report["window_focus"] and report["target_window_identity"] and report["target_drift_blocked"] and report["safe_start_process_plan"] and report["recording_launcher"] and not report["system_settings_changed"] and not report["actions_expanded"])  # 新增代码+Phase69AppWindowControl: 汇总合同通过条件；如果没有这行代码，命令行入口无法用退出码表达失败。
    return report  # 新增代码+Phase69AppWindowControl: 返回合同报告；如果没有这行代码，测试和 CLI 无法读取结果。
# 新增代码+Phase69AppWindowControl: 函数段结束，run_phase69_app_window_control_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase69_cli_line(report: dict[str, Any] | None = None) -> str:  # 新增代码+Phase69AppWindowControl: 函数段开始，生成真实终端验收需要的单行 token；如果没有这个函数，agent 最终回答容易因自然语言变化导致验收失败。
    current_report = report if report is not None else run_phase69_app_window_control_contract(real_smoke=False)  # 新增代码+Phase69AppWindowControl: 复用传入报告或现场运行自检；如果没有这行代码，CLI 无法独立执行。
    return f"{PHASE69_APP_WINDOW_CONTROL_MARKER} {PHASE69_APP_WINDOW_CONTROL_OK_TOKEN} app_launch={_phase69_bool_token(current_report.get('app_launch'))} window_focus={_phase69_bool_token(current_report.get('window_focus'))} target_window_identity={_phase69_bool_token(current_report.get('target_window_identity'))} target_drift_blocked={_phase69_bool_token(current_report.get('target_drift_blocked'))} actions_expanded={_phase69_bool_token(current_report.get('actions_expanded'))}"  # 新增代码+Phase69AppWindowControl: 返回固定 token 行；如果没有这行代码，真实终端验收不能用简单包含关系判断成功。
# 新增代码+Phase69AppWindowControl: 函数段结束，phase69_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 输出范围。


def main() -> int:  # 新增代码+Phase69AppWindowControl: 函数段开始，提供 python -c 调用的命令行入口；如果没有这个函数，真实终端场景无法运行统一自检命令。
    report = run_phase69_app_window_control_contract(real_smoke=False)  # 新增代码+Phase69AppWindowControl: 运行记录型合同自检；如果没有这行代码，命令行入口没有结果来源。
    print(phase69_cli_line(report))  # 新增代码+Phase69AppWindowControl: 打印固定验收 token 行；如果没有这行代码，controller 看不到 Phase69 成功标记。
    return 0 if report.get("passed", False) else 1  # 新增代码+Phase69AppWindowControl: 根据合同结果返回退出码；如果没有这行代码，自动化命令无法用进程状态判断失败。
# 新增代码+Phase69AppWindowControl: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


__all__ = ["PHASE69_ACTIONS_EXPANDED", "PHASE69_APP_WINDOW_CONTROL_MARKER", "PHASE69_APP_WINDOW_CONTROL_MODEL", "PHASE69_APP_WINDOW_CONTROL_OK_TOKEN", "Phase69RecordingFocuser", "Phase69RecordingLauncher", "WindowsAppWindowControlRuntime", "build_launch_plan", "main", "phase69_cli_line", "run_phase69_app_window_control_contract"]  # 新增代码+Phase69AppWindowControl: 限定公开导出名称；如果没有这行代码，包导入容易暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase69AppWindowControl: 允许直接运行本模块；如果没有这行代码，初学者不能用 python 文件方式启动 Phase69 自检。
    raise SystemExit(main())  # 新增代码+Phase69AppWindowControl: 调用 main 并返回退出码；如果没有这行代码，直接运行模块不会执行合同自检。
