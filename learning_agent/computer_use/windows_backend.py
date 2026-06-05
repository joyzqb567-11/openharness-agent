"""Windows Computer Use 只读窗口 inventory。"""  # 新增代码+Phase28ComputerUse: 把 Windows 窗口枚举逻辑从控制器拆出；如果没有这个文件，真实窗口发现会继续塞在安全控制器里。

from __future__ import annotations  # 新增代码+Phase28ComputerUse: 延迟解析类型注解；如果没有这行代码，静态 inventory 类型在旧运行路径中更容易触发导入顺序问题。

import hashlib  # 新增代码+Phase28ComputerUse: 用于把进程路径变成哈希；如果没有这行代码，后续若读取进程路径只能泄露原始本地路径。
import sys  # 新增代码+Phase28ComputerUse: 用于判断当前平台是否为 Windows；如果没有这行代码，非 Windows 环境可能误跑 Win32 API。
import time  # 新增代码+Phase28ComputerUse: 用于生成窗口观察时间戳；如果没有这行代码，窗口引用无法表达采集时间。
from dataclasses import dataclass  # 新增代码+Phase28ComputerUse: 使用 dataclass 表达窗口快照；如果没有这行代码，快照对象需要手写大量样板代码。
from typing import Any  # 新增代码+Phase28ComputerUse: 窗口原始记录来自 Win32 或测试 dict；如果没有这行代码，helper 参数类型会不清楚。

try:  # 新增代码+Phase28ComputerUse: 包运行模式下导入协议模型 helper；如果没有这行代码，窗口清理和身份键无法复用 Phase 27 合同。
    from learning_agent.computer_use.models import build_window_ref, clean_protocol_text, window_ref_identity  # 新增代码+Phase28ComputerUse: 复用窗口引用构造和文本清理；如果没有这行代码，inventory 会和 controller 使用不同身份规则。
except ModuleNotFoundError as error:  # 新增代码+Phase28ComputerUse: 捕获脚本模式下包路径不可用的情况；如果没有这行代码，start_oauth_agent.bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.models"}:  # 新增代码+Phase28ComputerUse: 只允许目标包路径缺失时 fallback；如果没有这行代码，models 内部真实 bug 会被误吞。
        raise  # 新增代码+Phase28ComputerUse: 重新抛出真实导入错误；如果没有这行代码，排查窗口协议模型问题会很困难。
    from computer_use.models import build_window_ref, clean_protocol_text, window_ref_identity  # 新增代码+Phase28ComputerUse: 脚本模式下从本地包导入 helper；如果没有这行代码，直接执行入口无法加载 inventory。

try:  # 修改代码+TargetIdentityMaturity：优先按包路径导入 Task 3 标题摘要和哈希 helper；如果没有这一段，窗口 inventory 无法给目标身份绑定提供统一脱敏字段。
    from learning_agent.computer_use.target_identity import summarize_window_title, window_title_sha256_16  # 修改代码+TargetIdentityMaturity：复用目标身份模块的标题摘要和哈希规则；如果没有这一行，windows_backend 会和动作前校验使用不同标题规则。
except ModuleNotFoundError as error:  # 修改代码+TargetIdentityMaturity：兼容 start_oauth_agent.bat 可能从 learning_agent 目录启动的脚本模式；如果没有这一行，真实可见终端入口可能因为包路径不同失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.target_identity"}:  # 修改代码+TargetIdentityMaturity：只允许包路径缺失时 fallback；如果没有这一行，target_identity 内部真实 bug 可能被误吞。
        raise  # 修改代码+TargetIdentityMaturity：重新抛出真实导入错误；如果没有这一行，目标身份模块的内部问题会很难排查。
    from computer_use.target_identity import summarize_window_title, window_title_sha256_16  # type: ignore  # 修改代码+TargetIdentityMaturity：脚本模式下从本地包导入同一 helper；如果没有这一行，双击 bat 后窗口身份字段可能不可用。


FORBIDDEN_WINDOW_TITLE_KEYWORDS: tuple[str, ...] = ("powershell", "command prompt", "cmd.exe", "windows terminal", "codex", "credential", "password", "windows security", "defender", "firewall", "privacy", "captcha", "otp", "验证码", "密码", "认证")  # 新增代码+Phase28ComputerUse: 集中列出只读 inventory 也应过滤的敏感/终端目标关键词；如果没有这行代码，模型可能拿到禁止自动化窗口的可信 id。


# 新增代码+Phase28ComputerUse: 函数段开始，phase28_utc_timestamp 用于生成窗口快照时间；如果没有这段函数，窗口引用缺少 captured_at，作者意图是让每次 observe 都有可审计时间。
def phase28_utc_timestamp() -> str:  # 新增代码+Phase28ComputerUse: 定义 UTC 时间戳 helper；如果没有这行代码，各处会重复拼接时间格式。
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())  # 新增代码+Phase28ComputerUse: 返回稳定 UTC 字符串；如果没有这行代码，窗口快照无法记录采集时间。
# 新增代码+Phase28ComputerUse: 函数段结束，phase28_utc_timestamp 到此结束；如果没有这个结束标记，用户不容易看出时间 helper 的边界。


# 新增代码+Phase28ComputerUse: 函数段开始，safe_int 用于把 Win32 原始数字安全转成 int；如果没有这段函数，坏数据会在窗口归一化时抛异常，作者意图是让 fake 和真实 probe 都能容错。
def safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase28ComputerUse: 定义安全整数转换函数；如果没有这行代码，hwnd/pid/rect 转换逻辑会散落重复。
    try:  # 新增代码+Phase28ComputerUse: 捕获无法转换的输入；如果没有这行代码，异常原始字段会让整个窗口枚举失败。
        return int(value)  # 新增代码+Phase28ComputerUse: 返回转换后的整数；如果没有这行代码，调用方拿不到数值字段。
    except (TypeError, ValueError):  # 新增代码+Phase28ComputerUse: 处理 None、空字符串或非数字文本；如果没有这行代码，坏字段会冒泡成测试/运行失败。
        return default  # 新增代码+Phase28ComputerUse: 返回默认值兜底；如果没有这行代码，调用方无法继续过滤无效窗口。
# 新增代码+Phase28ComputerUse: 函数段结束，safe_int 到此结束；如果没有这个结束标记，用户不容易看出转换 helper 的边界。


# 新增代码+Phase28ComputerUse: 函数段开始，process_path_hash 用于脱敏进程路径；如果没有这段函数，后续真实后端若读取路径会泄露用户本地目录，作者意图是只保留可比对身份而不暴露明文路径。
def process_path_hash(path_text: Any) -> str:  # 新增代码+Phase28ComputerUse: 定义进程路径哈希函数；如果没有这行代码，窗口引用无法保存脱敏进程身份。
    path = clean_protocol_text(path_text, max_length=500)  # 新增代码+Phase28ComputerUse: 清理并限制路径文本；如果没有这行代码，超长路径会污染哈希输入和日志。
    if not path:  # 新增代码+Phase28ComputerUse: 检查是否没有路径；如果没有这行代码，空路径也会生成无意义哈希。
        return ""  # 新增代码+Phase28ComputerUse: 空路径返回空哈希；如果没有这行代码，调用方无法区分未知路径和真实路径。
    return hashlib.sha256(path.lower().encode("utf-8")).hexdigest()[:16]  # 新增代码+Phase28ComputerUse: 返回短哈希便于审计比对；如果没有这行代码，进程路径无法安全参与窗口身份。
# 新增代码+Phase28ComputerUse: 函数段结束，process_path_hash 到此结束；如果没有这个结束标记，用户不容易看出脱敏路径流程。


# 新增代码+Phase28ComputerUse: 函数段开始，rect_from_raw 用于标准化窗口矩形；如果没有这段函数，截图尺寸和窗口相对坐标会缺少统一来源，作者意图是把 Win32 RECT 和测试 dict 都转成同一结构。
def rect_from_raw(raw_rect: Any) -> dict[str, int]:  # 新增代码+Phase28ComputerUse: 定义矩形归一化函数；如果没有这行代码，不同来源的 rect 字段无法统一。
    if isinstance(raw_rect, dict):  # 新增代码+Phase28ComputerUse: 处理测试和 JSON 使用的 dict 矩形；如果没有这行代码，静态 inventory 的 rect 会被当成无效。
        return {"left": safe_int(raw_rect.get("left")), "top": safe_int(raw_rect.get("top")), "right": safe_int(raw_rect.get("right")), "bottom": safe_int(raw_rect.get("bottom"))}  # 新增代码+Phase28ComputerUse: 返回标准矩形字段；如果没有这行代码，状态合同缺少窗口边界。
    if isinstance(raw_rect, (list, tuple)) and len(raw_rect) >= 4:  # 新增代码+Phase28ComputerUse: 处理 Win32 或测试传入的四元组矩形；如果没有这行代码，tuple 输入会被丢弃。
        return {"left": safe_int(raw_rect[0]), "top": safe_int(raw_rect[1]), "right": safe_int(raw_rect[2]), "bottom": safe_int(raw_rect[3])}  # 新增代码+Phase28ComputerUse: 返回四元组转换后的矩形；如果没有这行代码，真实 probe 的矩形无法进入状态。
    return {"left": 0, "top": 0, "right": 0, "bottom": 0}  # 新增代码+Phase28ComputerUse: 无效矩形返回零矩形；如果没有这行代码，调用方会在缺字段时崩溃。
# 新增代码+Phase28ComputerUse: 函数段结束，rect_from_raw 到此结束；如果没有这个结束标记，用户不容易看出矩形归一化流程。


# 新增代码+Phase28ComputerUse: 函数段开始，rect_size 用于计算窗口尺寸；如果没有这段函数，get_window_state 会重复计算宽高并容易出错，作者意图是统一窗口相对截图尺寸。
def rect_size(rect: dict[str, int]) -> tuple[int, int]:  # 新增代码+Phase28ComputerUse: 定义矩形尺寸函数；如果没有这行代码，调用方无法稳定得到宽高。
    width = max(0, safe_int(rect.get("right")) - safe_int(rect.get("left")))  # 新增代码+Phase28ComputerUse: 计算非负宽度；如果没有这行代码，异常 rect 可能产生负宽度。
    height = max(0, safe_int(rect.get("bottom")) - safe_int(rect.get("top")))  # 新增代码+Phase28ComputerUse: 计算非负高度；如果没有这行代码，异常 rect 可能产生负高度。
    return width, height  # 新增代码+Phase28ComputerUse: 返回宽高二元组；如果没有这行代码，调用方拿不到截图尺寸。
# 新增代码+Phase28ComputerUse: 函数段结束，rect_size 到此结束；如果没有这个结束标记，用户不容易看出尺寸 helper 的边界。


# 新增代码+Phase28ComputerUse: 函数段开始，is_forbidden_window_title 用于识别禁止目标；如果没有这段函数，terminal/security/Codex 窗口可能被当成可信目标，作者意图是先过滤再暴露给模型。
def is_forbidden_window_title(title: str) -> bool:  # 新增代码+Phase28ComputerUse: 定义标题禁止判断函数；如果没有这行代码，过滤逻辑没有统一入口。
    lowered = title.lower()  # 新增代码+Phase28ComputerUse: 转小写便于关键词匹配；如果没有这行代码，大小写差异会绕过过滤。
    return any(keyword in lowered for keyword in FORBIDDEN_WINDOW_TITLE_KEYWORDS)  # 新增代码+Phase28ComputerUse: 检查是否命中禁止关键词；如果没有这行代码，敏感窗口会进入可操作列表。
# 新增代码+Phase28ComputerUse: 函数段结束，is_forbidden_window_title 到此结束；如果没有这个结束标记，用户不容易看出禁止目标判断边界。


# 新增代码+Phase28ComputerUse: 函数段开始，normalize_window_record 用于把原始窗口记录变成 Phase 27 窗口引用；如果没有这段函数，fake 和真实后端会返回不同字段，作者意图是保证 app_id/window_id/title_preview/rect 合同一致。
def normalize_window_record(raw_window: dict[str, Any], captured_at: str) -> tuple[dict[str, Any] | None, str]:  # 新增代码+Phase28ComputerUse: 定义窗口归一化函数；如果没有这行代码，raw Win32 记录无法直接给模型。
    title = clean_protocol_text(raw_window.get("title_preview", raw_window.get("title", "")))  # 修改代码+Phase58RealSendInputGuard: 优先使用当前协议里的可见标题摘要并兼容原始 Win32 title；如果没有这行代码，静态快照里 title_preview 已变化但 title 仍旧时，目标漂移可能被误放行。
    if not title:  # 新增代码+Phase28ComputerUse: 过滤空标题窗口；如果没有这行代码，后台/隐藏窗口可能进入可见窗口列表。
        return None, "empty_title"  # 新增代码+Phase28ComputerUse: 返回空标题过滤原因；如果没有这行代码，过滤计数没有可解释原因。
    if is_forbidden_window_title(title):  # 新增代码+Phase28ComputerUse: 检查终端、安全和 Codex 等禁止目标；如果没有这行代码，模型可能获得不该操作的窗口 id。
        return None, "forbidden_title"  # 新增代码+Phase28ComputerUse: 返回禁止目标过滤原因；如果没有这行代码，过滤原因无法审计。
    rect = rect_from_raw(raw_window.get("rect"))  # 新增代码+Phase28ComputerUse: 标准化窗口矩形；如果没有这行代码，状态里无法给出窗口位置和尺寸。
    width, height = rect_size(rect)  # 新增代码+Phase28ComputerUse: 计算窗口尺寸；如果没有这行代码，无法过滤无效尺寸窗口。
    if width <= 0 or height <= 0:  # 新增代码+Phase28ComputerUse: 过滤零尺寸窗口；如果没有这行代码，不可见或坏窗口会进入可操作列表。
        return None, "invalid_rect"  # 新增代码+Phase28ComputerUse: 返回矩形无效过滤原因；如果没有这行代码，用户不知道窗口为何被排除。
    hwnd = safe_int(raw_window.get("hwnd", raw_window.get("window_handle")))  # 新增代码+Phase28ComputerUse: 读取窗口句柄；如果没有这行代码，window_id 缺少稳定来源。
    pid = safe_int(raw_window.get("pid", raw_window.get("process_id")))  # 新增代码+Phase28ComputerUse: 读取进程 id；如果没有这行代码，app_id 缺少兜底来源。
    process_name = clean_protocol_text(raw_window.get("process_name", ""))  # 新增代码+Phase28ComputerUse: 读取进程名；如果没有这行代码，app_id 只能使用不稳定 pid。
    class_name = clean_protocol_text(raw_window.get("class_name", ""))  # 新增代码+Phase28ComputerUse: 读取窗口类名；如果没有这行代码，缺进程名时没有更好兜底。
    app_id = clean_protocol_text(raw_window.get("app_id", "")) or process_name or (f"{class_name.lower()}:pid:{pid}" if class_name else f"pid:{pid}")  # 修改代码+Phase39WindowsCoordinates: 优先保留静态窗口或上游 probe 已给出的 app_id；如果没有这行代码，带 DPI/display 的测试窗口会被改名导致状态查询找不到目标。
    window_id = f"hwnd:{hwnd}" if hwnd else clean_protocol_text(raw_window.get("window_id", ""))  # 新增代码+Phase28ComputerUse: 构造窗口身份；如果没有这行代码，动作前无法引用该窗口。
    if not window_id:  # 新增代码+Phase28ComputerUse: 检查窗口身份是否存在；如果没有这行代码，空 window_id 会进入可信目录。
        return None, "missing_window_id"  # 新增代码+Phase28ComputerUse: 返回缺窗口 id 原因；如果没有这行代码，过滤无法解释。
    process_hash = process_path_hash(raw_window.get("process_path", ""))  # 新增代码+Phase28ComputerUse: 生成可选进程路径哈希；如果没有这行代码，后续身份校验缺少脱敏辅助字段。
    title_summary = summarize_window_title(title)  # 修改代码+TargetIdentityMaturity：把窗口标题限制成可展示摘要；如果没有这一行，超长标题可能直接进入 inventory 和模型上下文。
    title_hash = window_title_sha256_16(title)  # 修改代码+TargetIdentityMaturity：保存完整标题的短哈希用于漂移比对；如果没有这一行，标题变化只能靠不稳定的可见摘要判断。
    record = {"app_id": app_id, "window_id": window_id, "title_preview": title_summary, "title_sha256_16": title_hash, "process_path_hash": process_hash, "process_path_sha256_16": process_hash, "captured_at": captured_at, "rect": rect, "pid": pid, "window_process_id": pid, "hwnd": hwnd, "class_name": class_name, "safe_to_target": True, "target_identity_candidate": True}  # 修改代码+TargetIdentityMaturity：返回带 pid、hwnd、标题哈希和路径哈希的标准窗口记录；如果没有这一行，target_identity 无法安全绑定窗口。
    if isinstance(raw_window.get("display"), dict):  # 新增代码+Phase39WindowsCoordinates: 保留单显示器 DPI 元数据；如果没有这行代码，窗口状态会丢失缩放和显示器原点。
        record["display"] = dict(raw_window.get("display", {}))  # 新增代码+Phase39WindowsCoordinates: 复制 display 字典避免调用方后续污染快照；如果没有这行代码，坐标模型无法读取 display_id/logical_rect/physical_rect。
    if isinstance(raw_window.get("displays"), list):  # 新增代码+Phase39WindowsCoordinates: 保留多显示器候选列表；如果没有这行代码，未来真实 probe 的多屏数据无法参与选择。
        record["displays"] = [dict(display) for display in raw_window.get("displays", []) if isinstance(display, dict)]  # 新增代码+Phase39WindowsCoordinates: 只复制 dict 形式显示器记录；如果没有这行代码，坏元素可能导致坐标模型读字段失败。
    return record, ""  # 新增代码+Phase28ComputerUse: 返回有效窗口和空过滤原因；如果没有这行代码，调用方无法区分成功和过滤。
# 新增代码+Phase28ComputerUse: 函数段结束，normalize_window_record 到此结束；如果没有这个结束标记，用户不容易看出窗口归一化流程。


@dataclass(frozen=True)  # 新增代码+Phase28ComputerUse: 让窗口快照不可变；如果没有这行代码，调用方可能无意修改本次 observe 证据。
class WindowsWindowInventorySnapshot:  # 新增代码+Phase28ComputerUse: 定义一次窗口 inventory 快照；如果没有这个类，list_windows/list_apps/get_window_state 会重复处理原始数据。
    windows: list[dict[str, Any]]  # 新增代码+Phase28ComputerUse: 保存安全可暴露窗口列表；如果没有这行代码，快照没有主体数据。
    filtered_count: int  # 新增代码+Phase28ComputerUse: 保存被过滤窗口数量；如果没有这行代码，用户不知道为什么部分窗口不可见。
    captured_at: str  # 新增代码+Phase28ComputerUse: 保存快照采集时间；如果没有这行代码，窗口引用无法判断新旧。
    source: str  # 新增代码+Phase28ComputerUse: 保存快照来源；如果没有这行代码，状态无法区分静态测试和真实 Win32 probe。
    platform: str = sys.platform  # 新增代码+Phase28ComputerUse: 保存平台信息；如果没有这行代码，跨平台排查缺少环境字段。
    active_window: dict[str, Any] | None = None  # 新增代码+Phase28ComputerUse: 保存可选活动窗口；如果没有这行代码，get_active_window 无法使用快照结果。

    # 新增代码+Phase28ComputerUse: 函数段开始，apps 用于把窗口快照按应用分组；如果没有这段函数，list_apps 会重复统计，作者意图是让 list_apps 和 list_windows 使用同一快照事实。
    def apps(self) -> list[dict[str, Any]]:  # 新增代码+Phase28ComputerUse: 定义应用分组方法；如果没有这行代码，后端无法返回 list_apps。
        app_ids = sorted({str(window.get("app_id", "")) for window in self.windows if window.get("app_id")})  # 新增代码+Phase28ComputerUse: 收集并排序应用身份；如果没有这行代码，应用列表顺序不稳定。
        return [{"app_id": app_id, "window_count": sum(1 for window in self.windows if window.get("app_id") == app_id)} for app_id in app_ids]  # 新增代码+Phase28ComputerUse: 返回应用窗口数量摘要；如果没有这行代码，模型不知道每个 app 下有几个窗口。
    # 新增代码+Phase28ComputerUse: 函数段结束，apps 到此结束；如果没有这个结束标记，用户不容易看出 app 分组逻辑边界。

    # 新增代码+Phase28ComputerUse: 函数段开始，find_window 用于在快照中查找可信窗口；如果没有这段函数，get_window_state 和动作校验会重复匹配逻辑，作者意图是只按 app_id/window_id 匹配。
    def find_window(self, raw_window: Any) -> dict[str, Any] | None:  # 新增代码+Phase28ComputerUse: 定义窗口查找方法；如果没有这行代码，后端无法验证目标窗口是否来自本次快照。
        target_ref = build_window_ref(raw_window)  # 新增代码+Phase28ComputerUse: 把输入转换成协议窗口引用；如果没有这行代码，缺字段目标可能绕过校验。
        if target_ref is None:  # 新增代码+Phase28ComputerUse: 检查目标引用是否完整；如果没有这行代码，后续身份键可能崩溃。
            return None  # 新增代码+Phase28ComputerUse: 无效目标直接返回未找到；如果没有这行代码，调用方无法拒绝坏窗口。
        target_identity = window_ref_identity(target_ref)  # 新增代码+Phase28ComputerUse: 生成目标身份键；如果没有这行代码，匹配规则会散落重复。
        for window in self.windows:  # 新增代码+Phase28ComputerUse: 遍历安全窗口列表；如果没有这行代码，无法查找目标窗口。
            known_ref = build_window_ref(window)  # 新增代码+Phase28ComputerUse: 把快照窗口转成协议引用；如果没有这行代码，字段变化会影响匹配。
            if known_ref is not None and window_ref_identity(known_ref) == target_identity:  # 新增代码+Phase28ComputerUse: 比较 app_id/window_id；如果没有这行代码，标题相同的不同窗口可能混淆。
                return dict(window)  # 新增代码+Phase28ComputerUse: 返回窗口副本；如果没有这行代码，调用方可能污染快照。
        return None  # 新增代码+Phase28ComputerUse: 没找到返回 None；如果没有这行代码，未知窗口无法被拒绝。
    # 新增代码+Phase28ComputerUse: 函数段结束，find_window 到此结束；如果没有这个结束标记，用户不容易看出可信窗口匹配边界。


# 新增代码+Phase28ComputerUse: 函数段开始，build_inventory_snapshot 用于归一化原始窗口列表；如果没有这段函数，静态和真实 probe 会各自过滤窗口，作者意图是统一安全过滤和字段合同。
def build_inventory_snapshot(raw_windows: list[dict[str, Any]], *, captured_at: str | None = None, source: str = "static", active_hwnd: int | None = None) -> WindowsWindowInventorySnapshot:  # 新增代码+Phase28ComputerUse: 定义快照构造函数；如果没有这行代码，后端无法从 raw 窗口生成标准快照。
    timestamp = captured_at or phase28_utc_timestamp()  # 新增代码+Phase28ComputerUse: 使用传入时间或当前 UTC；如果没有这行代码，测试无法固定 captured_at。
    windows: list[dict[str, Any]] = []  # 新增代码+Phase28ComputerUse: 准备保存有效窗口；如果没有这行代码，归一化结果没有容器。
    filtered_count = 0  # 新增代码+Phase28ComputerUse: 初始化过滤计数；如果没有这行代码，过滤数量无法返回给用户。
    active_window: dict[str, Any] | None = None  # 新增代码+Phase28ComputerUse: 初始化活动窗口；如果没有这行代码，get_active_window 没有默认值。
    for raw_window in raw_windows:  # 新增代码+Phase28ComputerUse: 遍历原始窗口列表；如果没有这行代码，快照不会包含任何窗口。
        record, reason = normalize_window_record(raw_window, timestamp)  # 新增代码+Phase28ComputerUse: 归一化并过滤单个窗口；如果没有这行代码，安全过滤不会生效。
        if record is None:  # 新增代码+Phase28ComputerUse: 判断窗口是否被过滤；如果没有这行代码，None 会进入窗口列表。
            filtered_count += 1  # 新增代码+Phase28ComputerUse: 累加过滤数量；如果没有这行代码，用户看不到过滤规模。
            continue  # 新增代码+Phase28ComputerUse: 跳过被过滤窗口；如果没有这行代码，后续逻辑会访问 None。
        windows.append(record)  # 新增代码+Phase28ComputerUse: 保存有效窗口；如果没有这行代码，list_windows 会为空。
        if active_hwnd is not None and record.get("window_id") == f"hwnd:{active_hwnd}":  # 新增代码+Phase28ComputerUse: 判断该窗口是否活动窗口；如果没有这行代码，active_window 无法从真实句柄匹配。
            active_window = dict(record)  # 新增代码+Phase28ComputerUse: 保存活动窗口副本；如果没有这行代码，调用方可能修改快照窗口。
    if active_window is None and windows:  # 新增代码+Phase28ComputerUse: 静态测试或无活动匹配时使用第一个安全窗口；如果没有这行代码，get_active_window 在 fake 后端里不可用。
        active_window = dict(windows[0])  # 新增代码+Phase28ComputerUse: 选第一个窗口作为安全兜底；如果没有这行代码，测试需要额外指定活动窗口。
    return WindowsWindowInventorySnapshot(windows=windows, filtered_count=filtered_count, captured_at=timestamp, source=source, platform=sys.platform, active_window=active_window)  # 新增代码+Phase28ComputerUse: 返回标准窗口快照；如果没有这行代码，调用方拿不到 inventory 数据。
# 新增代码+Phase28ComputerUse: 函数段结束，build_inventory_snapshot 到此结束；如果没有这个结束标记，用户不容易看出快照构造流程。


class StaticWindowsWindowInventory:  # 新增代码+Phase28ComputerUse: 定义测试/验收用静态窗口 inventory；如果没有这个类，测试只能依赖真实桌面窗口。
    def __init__(self, raw_windows: list[dict[str, Any]], captured_at: str | None = None, source: str = "static") -> None:  # 新增代码+Phase28ComputerUse: 初始化静态 inventory；如果没有这段代码，测试无法注入窗口列表。
        self.raw_windows = [dict(window) for window in raw_windows]  # 新增代码+Phase28ComputerUse: 保存窗口记录副本；如果没有这行代码，外部修改会污染测试后端。
        self.captured_at = captured_at  # 新增代码+Phase28ComputerUse: 保存可选固定时间；如果没有这行代码，测试无法稳定断言 captured_at。
        self.source = source  # 新增代码+Phase28ComputerUse: 保存 inventory 来源；如果没有这行代码，状态无法说明这是静态后端。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase28ComputerUse: 返回静态 inventory 状态；如果没有这段代码，Windows 后端状态无法说明观察来源。
        return {"source": self.source, "platform": sys.platform, "available": True, "native_helper_available": False, "native_helper_reason": "Phase 28 使用静态/ctypes 只读 inventory；C# UIA/Windows.Graphics.Capture helper 将在 Phase 29+ 接入。"}  # 新增代码+Phase28ComputerUse: 返回 helper 边界说明；如果没有这行代码，用户会误以为完整 native helper 已接入。

    def snapshot(self) -> WindowsWindowInventorySnapshot:  # 新增代码+Phase28ComputerUse: 生成静态窗口快照；如果没有这段代码，后端无法 list_windows/list_apps。
        return build_inventory_snapshot(self.raw_windows, captured_at=self.captured_at, source=self.source)  # 新增代码+Phase28ComputerUse: 复用统一快照构造；如果没有这行代码，静态和真实过滤规则会分裂。


class WindowsWindowInventoryProbe:  # 新增代码+Phase28ComputerUse: 定义真实 Win32 只读窗口枚举 probe；如果没有这个类，Windows 后端无法实际发现窗口。
    def status(self) -> dict[str, Any]:  # 新增代码+Phase28ComputerUse: 返回真实 probe 状态；如果没有这段代码，后端状态无法说明平台和 helper 边界。
        return {"source": "windows_ctypes", "platform": sys.platform, "available": sys.platform == "win32", "native_helper_available": False, "native_helper_reason": "Phase 28 只使用 Win32 ctypes 做只读窗口枚举；C# UIA/Windows.Graphics.Capture helper 尚未接入。"}  # 新增代码+Phase28ComputerUse: 明确当前没有完整 native helper；如果没有这行代码，用户可能误判截图/UIA 已完成。

    def snapshot(self) -> WindowsWindowInventorySnapshot:  # 新增代码+Phase28ComputerUse: 枚举当前 Windows 顶层窗口并生成快照；如果没有这段代码，真实后端 observe 只能返回占位失败。
        if sys.platform != "win32":  # 新增代码+Phase28ComputerUse: 非 Windows 平台不调用 Win32 API；如果没有这行代码，Linux/macOS 测试会崩溃。
            return WindowsWindowInventorySnapshot(windows=[], filtered_count=0, captured_at=phase28_utc_timestamp(), source="windows_ctypes_unavailable", platform=sys.platform, active_window=None)  # 新增代码+Phase28ComputerUse: 返回空快照说明不可用；如果没有这行代码，跨平台状态无法优雅降级。
        raw_windows, active_hwnd = self._collect_raw_windows()  # 新增代码+Phase28ComputerUse: 调用 Win32 API 读取原始窗口；如果没有这行代码，真实后端没有窗口输入。
        return build_inventory_snapshot(raw_windows, source="windows_ctypes", active_hwnd=active_hwnd)  # 新增代码+Phase28ComputerUse: 归一化真实窗口快照；如果没有这行代码，Win32 原始数据无法给模型使用。

    def _collect_raw_windows(self) -> tuple[list[dict[str, Any]], int | None]:  # 新增代码+Phase28ComputerUse: 使用 ctypes 枚举 Win32 顶层窗口；如果没有这段代码，真实 inventory 无法读取本机窗口。
        import ctypes  # 新增代码+Phase28ComputerUse: 延迟导入 ctypes；如果没有这行代码，无法调用 user32.dll。
        from ctypes import wintypes  # 新增代码+Phase28ComputerUse: 导入 Win32 类型定义；如果没有这行代码，RECT/HWND/DWORD 类型需要手写。
        user32 = ctypes.windll.user32  # 新增代码+Phase28ComputerUse: 获取 user32 API；如果没有这行代码，窗口枚举没有系统入口。
        raw_windows: list[dict[str, Any]] = []  # 新增代码+Phase28ComputerUse: 准备保存原始窗口记录；如果没有这行代码，EnumWindows 回调没有输出容器。
        active_hwnd = safe_int(user32.GetForegroundWindow())  # 新增代码+Phase28ComputerUse: 读取当前前台窗口句柄；如果没有这行代码，get_active_window 无法基于真实焦点。
        enum_windows_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)  # 新增代码+Phase28ComputerUse: 定义 EnumWindows 回调签名；如果没有这行代码，Python 函数不能传给 Win32。

        def collect_window(hwnd: Any, lparam: Any) -> bool:  # 新增代码+Phase28ComputerUse: 定义单个窗口回调；如果没有这段代码，EnumWindows 无法把窗口逐个交给 Python。
            if not user32.IsWindowVisible(hwnd):  # 新增代码+Phase28ComputerUse: 跳过不可见窗口；如果没有这行代码，后台窗口会污染可观察列表。
                return True  # 新增代码+Phase28ComputerUse: 继续枚举下一个窗口；如果没有这行代码，遇到隐藏窗口会中断枚举。
            title_length = safe_int(user32.GetWindowTextLengthW(hwnd))  # 新增代码+Phase28ComputerUse: 读取窗口标题长度；如果没有这行代码，无法创建合适缓冲区。
            title_buffer = ctypes.create_unicode_buffer(title_length + 1)  # 新增代码+Phase28ComputerUse: 创建标题缓冲区；如果没有这行代码，无法接收窗口标题。
            user32.GetWindowTextW(hwnd, title_buffer, title_length + 1)  # 新增代码+Phase28ComputerUse: 读取窗口标题；如果没有这行代码，过滤和 title_preview 无法工作。
            class_buffer = ctypes.create_unicode_buffer(256)  # 新增代码+Phase28ComputerUse: 创建窗口类名缓冲区；如果没有这行代码，缺进程名时 app_id 缺少兜底。
            user32.GetClassNameW(hwnd, class_buffer, 256)  # 新增代码+Phase28ComputerUse: 读取窗口类名；如果没有这行代码，class_name 字段为空。
            rect = wintypes.RECT()  # 新增代码+Phase28ComputerUse: 创建 RECT 结构；如果没有这行代码，无法读取窗口边界。
            user32.GetWindowRect(hwnd, ctypes.byref(rect))  # 新增代码+Phase28ComputerUse: 读取窗口屏幕坐标；如果没有这行代码，窗口状态缺少位置和尺寸。
            pid = wintypes.DWORD()  # 新增代码+Phase28ComputerUse: 创建进程 id 输出变量；如果没有这行代码，无法读取窗口所属进程。
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))  # 新增代码+Phase28ComputerUse: 读取窗口进程 id；如果没有这行代码，app_id 只能依赖类名。
            raw_windows.append({"hwnd": safe_int(hwnd), "pid": safe_int(pid.value), "process_name": "", "class_name": class_buffer.value, "title": title_buffer.value, "rect": {"left": safe_int(rect.left), "top": safe_int(rect.top), "right": safe_int(rect.right), "bottom": safe_int(rect.bottom)}})  # 新增代码+Phase28ComputerUse: 保存原始窗口记录；如果没有这行代码，快照无法包含该窗口。
            return True  # 新增代码+Phase28ComputerUse: 返回 True 继续枚举；如果没有这行代码，EnumWindows 会提前停止。

        callback = enum_windows_proc(collect_window)  # 新增代码+Phase28ComputerUse: 保存回调对象防止被垃圾回收；如果没有这行代码，Win32 调用回调可能崩溃。
        user32.EnumWindows(callback, 0)  # 新增代码+Phase28ComputerUse: 枚举所有顶层窗口；如果没有这行代码，raw_windows 会一直为空。
        return raw_windows, active_hwnd  # 新增代码+Phase28ComputerUse: 返回原始窗口和活动句柄；如果没有这行代码，snapshot 无法继续归一化。
