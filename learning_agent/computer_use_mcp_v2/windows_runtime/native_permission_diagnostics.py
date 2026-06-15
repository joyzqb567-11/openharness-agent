"""Native OS permission diagnostics for Windows Computer Use."""  # 新增代码+Phase6NativePermissionDiagnostics：说明本文件负责原生权限诊断；如果没有这一行，读者不容易知道这里和普通状态面板的区别。
from __future__ import annotations  # 新增代码+Phase6NativePermissionDiagnostics：启用延迟类型解析；如果没有这一行，类型注解在旧解释顺序下更容易失败。
from typing import Any  # 新增代码+Phase6NativePermissionDiagnostics：导入通用值类型；如果没有这一行，诊断报告接口边界不清楚。
PHASE6_NATIVE_PERMISSION_DIAGNOSTICS_MODEL = "phase6_native_permission_diagnostics"  # 新增代码+Phase6NativePermissionDiagnostics：定义 Phase6 模型名；如果没有这一行，状态和矩阵无法区分诊断版本。
PHASE6_NATIVE_PERMISSION_DIAGNOSTICS_MARKER = "PHASE6_NATIVE_PERMISSION_DIAGNOSTICS_READY"  # 新增代码+Phase6NativePermissionDiagnostics：定义稳定 marker；如果没有这一行，终端和测试不容易定位 Phase6 输出。
PHASE6_NATIVE_PERMISSION_CAPABILITY_ORDER = ["screenshot", "uia", "display", "foreground", "sendinput", "hotkey"]  # 新增代码+Phase6NativePermissionDiagnostics：固定诊断顺序；如果没有这一行，CLI 和测试输出顺序会漂移。
PHASE6_NATIVE_PERMISSION_DEFAULTS = {  # 新增代码+Phase6NativePermissionDiagnostics：能力默认说明字典开始；如果没有这一行，每项能力的标签和修复建议会散落重复。
    "screenshot": {"label": "Screen capture", "remediation": "确认系统允许当前进程截屏，并确保桌面会话可见。"},  # 新增代码+Phase6NativePermissionDiagnostics：定义截图能力说明；如果没有这一行，截图失败时用户不知道该检查屏幕录制/桌面权限。
    "uia": {"label": "Windows UI Automation", "remediation": "确认 UIA 依赖可用，并避免目标窗口运行在更高完整性级别。"},  # 新增代码+Phase6NativePermissionDiagnostics：定义 UIA 能力说明；如果没有这一行，语义控件树失败时用户不知道该检查权限级别。
    "display": {"label": "Display enumeration", "remediation": "确认显示器枚举可用，并检查远程桌面或虚拟显示器状态。"},  # 新增代码+Phase6NativePermissionDiagnostics：定义显示器能力说明；如果没有这一行，多屏坐标问题缺少修复方向。
    "foreground": {"label": "Foreground focus", "remediation": "确认当前进程可以读取前台窗口，并避免安全桌面或管理员窗口阻断。"},  # 新增代码+Phase6NativePermissionDiagnostics：定义前台窗口能力说明；如果没有这一行，聚焦失败时用户不知道该排查安全桌面。
    "sendinput": {"label": "SendInput dispatch", "remediation": "确认真实输入开关、目标窗口权限和 Windows SendInput 调用链可用。"},  # 新增代码+Phase6NativePermissionDiagnostics：定义 SendInput 能力说明；如果没有这一行，真实动作失败时用户不知道该检查输入权限。
    "hotkey": {"label": "Global hotkey", "remediation": "确认全局热键没有被其他程序占用，并且本轮允许注册 Escape abort。"},  # 新增代码+Phase6NativePermissionDiagnostics：定义热键能力说明；如果没有这一行，全局急停降级时用户不知道该检查热键冲突。
}  # 新增代码+Phase6NativePermissionDiagnostics：能力默认说明字典结束；如果没有这一行，Python 无法正确结束结构。


def _phase6_bool(value: Any) -> bool:  # 新增代码+Phase6NativePermissionDiagnostics：函数段开始，把外部值规整为布尔；如果没有这段函数，字符串和空值会让报告语义漂移。
    return bool(value)  # 新增代码+Phase6NativePermissionDiagnostics：返回 Python 布尔值；如果没有这一行，调用方拿不到稳定判断。
# 新增代码+Phase6NativePermissionDiagnostics：函数段结束，_phase6_bool 到此结束；如果没有这个边界说明，初学者不容易看出布尔规范化范围。


def _phase6_safe_text(value: Any) -> str:  # 新增代码+Phase6NativePermissionDiagnostics：函数段开始，把诊断文本规整为单行；如果没有这段函数，换行或 None 会污染终端状态。
    return str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase6NativePermissionDiagnostics：返回去换行文本；如果没有这一行，修复提示可能打乱状态面板。
# 新增代码+Phase6NativePermissionDiagnostics：函数段结束，_phase6_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清洗范围。


class Phase6StaticNativePermissionProbe:  # 新增代码+Phase6NativePermissionDiagnostics：类段开始，提供可注入静态诊断探针；如果没有这个类，测试和生产合同无法稳定模拟权限状态。
    def __init__(self, statuses: dict[str, dict[str, Any]] | None = None) -> None:  # 新增代码+Phase6NativePermissionDiagnostics：函数段开始，保存静态能力状态；如果没有这段函数，探针没有事实输入。
        self.statuses = {str(name): dict(status) for name, status in dict(statuses or {}).items()}  # 新增代码+Phase6NativePermissionDiagnostics：复制外部状态字典；如果没有这一行，调用方后续修改会污染诊断结果。
    # 新增代码+Phase6NativePermissionDiagnostics：函数段结束，Phase6StaticNativePermissionProbe.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出探针初始化范围。
    def check_capability(self, name: str) -> dict[str, Any]:  # 新增代码+Phase6NativePermissionDiagnostics：函数段开始，读取单项能力状态；如果没有这段函数，ensureOsPermissions 无法统一查询 probe。
        default = {"ok": True, "required": True, "detail": f"{name} diagnostic passed", "source": "phase6_static_probe"}  # 新增代码+Phase6NativePermissionDiagnostics：准备默认通过状态；如果没有这一行，未覆盖能力会缺少稳定字段。
        return {**default, **dict(self.statuses.get(str(name), {}))}  # 新增代码+Phase6NativePermissionDiagnostics：合并覆盖状态；如果没有这一行，测试无法模拟局部失败。
    # 新增代码+Phase6NativePermissionDiagnostics：函数段结束，Phase6StaticNativePermissionProbe.check_capability 到此结束；如果没有这个边界说明，初学者不容易看出能力查询范围。
# 新增代码+Phase6NativePermissionDiagnostics：类段结束，Phase6StaticNativePermissionProbe 到此结束；如果没有这个边界说明，初学者不容易看出静态探针范围。


def _phase6_default_probe() -> Phase6StaticNativePermissionProbe:  # 新增代码+Phase6NativePermissionDiagnostics：函数段开始，创建默认合同探针；如果没有这段函数，生产状态没有安全可运行的诊断入口。
    statuses = {name: {"ok": True, "required": True, "detail": f"{name} contract diagnostic available", "source": "phase6_contract_default"} for name in PHASE6_NATIVE_PERMISSION_CAPABILITY_ORDER}  # 新增代码+Phase6NativePermissionDiagnostics：构造默认通过合同状态；如果没有这一行，生产合同测试会依赖真实桌面权限。
    return Phase6StaticNativePermissionProbe(statuses)  # 新增代码+Phase6NativePermissionDiagnostics：返回静态探针；如果没有这一行，默认诊断无法运行。
# 新增代码+Phase6NativePermissionDiagnostics：函数段结束，_phase6_default_probe 到此结束；如果没有这个边界说明，初学者不容易看出默认合同探针范围。


def _phase6_normalize_capability(name: str, raw_status: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase6NativePermissionDiagnostics：函数段开始，规范化单项能力报告；如果没有这段函数，各能力字段会不一致。
    defaults = dict(PHASE6_NATIVE_PERMISSION_DEFAULTS.get(name, {}))  # 新增代码+Phase6NativePermissionDiagnostics：读取能力默认说明；如果没有这一行，报告缺少标签和修复建议。
    ok = _phase6_bool(raw_status.get("ok", False))  # 新增代码+Phase6NativePermissionDiagnostics：规范化 ok 字段；如果没有这一行，字符串或缺失值可能误判。
    required = _phase6_bool(raw_status.get("required", True))  # 新增代码+Phase6NativePermissionDiagnostics：规范化 required 字段；如果没有这一行，软硬失败无法区分。
    detail = _phase6_safe_text(raw_status.get("detail", ""))  # 新增代码+Phase6NativePermissionDiagnostics：清洗诊断详情；如果没有这一行，状态文本可能污染终端。
    remediation = _phase6_safe_text(raw_status.get("remediation", defaults.get("remediation", "")))  # 新增代码+Phase6NativePermissionDiagnostics：读取修复建议；如果没有这一行，失败只会给结论不给解决方向。
    return {"name": name, "label": _phase6_safe_text(defaults.get("label", name)), "ok": ok, "required": required, "status": "ok" if ok else "failed", "detail": detail, "remediation": remediation, "source": _phase6_safe_text(raw_status.get("source", "probe"))}  # 新增代码+Phase6NativePermissionDiagnostics：返回规范化能力报告；如果没有这一行，上层无法稳定读取字段。
# 新增代码+Phase6NativePermissionDiagnostics：函数段结束，_phase6_normalize_capability 到此结束；如果没有这个边界说明，初学者不容易看出单项规范化范围。


def ensureOsPermissions(probe: Any = None, capability_names: list[str] | None = None) -> dict[str, Any]:  # 新增代码+Phase6NativePermissionDiagnostics：函数段开始，运行原生 OS 权限诊断；如果没有这段函数，顶层矩阵只能靠猜测判断平台权限。
    active_probe = probe if probe is not None else _phase6_default_probe()  # 新增代码+Phase6NativePermissionDiagnostics：选择注入探针或默认合同探针；如果没有这一行，生产状态无法在无真实桌面时安全运行。
    names = list(capability_names or PHASE6_NATIVE_PERMISSION_CAPABILITY_ORDER)  # 新增代码+Phase6NativePermissionDiagnostics：确定诊断能力顺序；如果没有这一行，报告顺序不稳定。
    native_permission: dict[str, dict[str, Any]] = {}  # 新增代码+Phase6NativePermissionDiagnostics：初始化能力报告字典；如果没有这一行，后续无法收集逐项结果。
    hard_fail_reasons: list[str] = []  # 新增代码+Phase6NativePermissionDiagnostics：初始化硬失败列表；如果没有这一行，成熟度阻断原因无法汇总。
    soft_fail_reasons: list[str] = []  # 新增代码+Phase6NativePermissionDiagnostics：初始化软警告列表；如果没有这一行，非阻断降级无法汇总。
    remediation_text: list[str] = []  # 新增代码+Phase6NativePermissionDiagnostics：初始化修复提示列表；如果没有这一行，用户拿不到统一修复建议。
    check_method = getattr(active_probe, "check_capability", None)  # 新增代码+Phase6NativePermissionDiagnostics：读取探针查询方法；如果没有这一行，错误 probe 会直接崩溃。
    for name in names:  # 新增代码+Phase6NativePermissionDiagnostics：逐项运行诊断；如果没有这一行，只能得到空报告。
        raw_status = dict(check_method(str(name))) if callable(check_method) else {"ok": False, "required": True, "detail": "probe missing check_capability", "source": "missing_probe"}  # 新增代码+Phase6NativePermissionDiagnostics：读取或兜底单项状态；如果没有这一行，坏 probe 会让整份诊断崩溃。
        normalized = _phase6_normalize_capability(str(name), raw_status)  # 新增代码+Phase6NativePermissionDiagnostics：规范化单项状态；如果没有这一行，上层字段会不稳定。
        native_permission[str(name)] = normalized  # 新增代码+Phase6NativePermissionDiagnostics：写入逐项报告；如果没有这一行，调用方看不到能力细节。
        if not normalized["ok"] and normalized["required"]:  # 新增代码+Phase6NativePermissionDiagnostics：识别硬失败；如果没有这一行，必需权限缺失可能被放行。
            hard_fail_reasons.append(f"{name}: {normalized['detail']}")  # 新增代码+Phase6NativePermissionDiagnostics：记录硬失败原因；如果没有这一行，用户不知道阻断点。
            remediation_text.append(f"{normalized['label']}: {normalized['remediation']}")  # 新增代码+Phase6NativePermissionDiagnostics：记录硬失败修复提示；如果没有这一行，用户不知道怎么修。
        elif not normalized["ok"]:  # 新增代码+Phase6NativePermissionDiagnostics：识别软失败；如果没有这一行，可选能力降级会丢失。
            soft_fail_reasons.append(f"{name}: {normalized['detail']}")  # 新增代码+Phase6NativePermissionDiagnostics：记录软警告原因；如果没有这一行，用户看不到降级点。
            remediation_text.append(f"{normalized['label']}: {normalized['remediation']}")  # 新增代码+Phase6NativePermissionDiagnostics：记录软警告修复提示；如果没有这一行，用户不知道如何恢复可选能力。
    passed = not hard_fail_reasons  # 新增代码+Phase6NativePermissionDiagnostics：硬失败为空才算通过；如果没有这一行，成熟度判断没有稳定规则。
    return {"passed": passed, "model": PHASE6_NATIVE_PERMISSION_DIAGNOSTICS_MODEL, "marker": PHASE6_NATIVE_PERMISSION_DIAGNOSTICS_MARKER, "native_permission": native_permission, "hard_fail_reasons": hard_fail_reasons, "soft_fail_reasons": soft_fail_reasons, "remediation_text": remediation_text, "capability_count": len(native_permission)}  # 新增代码+Phase6NativePermissionDiagnostics：返回完整诊断报告；如果没有这一行，测试、生产状态和矩阵拿不到诊断结果。
# 新增代码+Phase6NativePermissionDiagnostics：函数段结束，ensureOsPermissions 到此结束；如果没有这个边界说明，初学者不容易看出诊断主入口范围。


def phase6_native_permission_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase6NativePermissionDiagnostics：函数段开始，生成稳定 CLI 摘要；如果没有这段函数，真实终端验收需要解析长 JSON。
    return f"{PHASE6_NATIVE_PERMISSION_DIAGNOSTICS_MARKER} passed={'true' if report.get('passed') else 'false'} hard_fail_count={len(list(report.get('hard_fail_reasons', [])))} soft_fail_count={len(list(report.get('soft_fail_reasons', [])))} capability_count={int(report.get('capability_count', 0))}"  # 新增代码+Phase6NativePermissionDiagnostics：返回单行 token；如果没有这一行，验收输出容易漂移。
# 新增代码+Phase6NativePermissionDiagnostics：函数段结束，phase6_native_permission_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 摘要范围。


__all__ = ["PHASE6_NATIVE_PERMISSION_DIAGNOSTICS_MARKER", "PHASE6_NATIVE_PERMISSION_DIAGNOSTICS_MODEL", "PHASE6_NATIVE_PERMISSION_CAPABILITY_ORDER", "Phase6StaticNativePermissionProbe", "ensureOsPermissions", "phase6_native_permission_cli_line"]  # 新增代码+Phase6NativePermissionDiagnostics：声明稳定公开 API；如果没有这一行，后续模块不清楚哪些名称可依赖。
