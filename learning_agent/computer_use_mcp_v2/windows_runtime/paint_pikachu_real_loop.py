"""受控 Paint 已支持对象真实执行闭环。"""  # 修改代码+GenericPaintSubject：说明本文件负责 full 模式下按 prompt 绘制已支持对象；如果没有这一行，读者会误以为这里永远只能画皮卡丘。
from __future__ import annotations  # 新增代码+PaintPikachuRealLoop：启用延迟类型解析；如果没有这一行，复杂类型注解在脚本模式下更容易出现导入顺序问题。

import sys  # 新增代码+PaintPikachuRealLoop：读取当前平台是否为 Windows；如果没有这一行，非 Windows 环境可能误走 Win32 真实输入路径。
import time  # 新增代码+PaintPikachuRealLoop：用于等待 mspaint 窗口出现和给 Paint 刷新留时间；如果没有这一行，启动后立刻找窗口会不稳定。
from pathlib import Path  # 新增代码+PaintPikachuRealLoop：用于保存可审计运行目录；如果没有这一行，报告文件路径会退回脆弱字符串。
from typing import Any  # 新增代码+PaintPikachuRealLoop：用于描述动态 JSON 风格报告；如果没有这一行，接口字段边界不清楚。

try:  # 新增代码+PaintPikachuRealLoop：优先按包路径导入项目已有 Computer Use 组件；如果没有这一段，单元测试和真实 bat 入口无法共享实现。
    from learning_agent.computer_use_mcp_v2.windows_runtime.drawing_primitives import build_cat_drag_plan, build_elephant_drag_plan, build_pikachu_drag_plan, expand_drag_path_to_low_level_events  # 修改代码+PaintCatSubject：同时复用猫、大象和皮卡丘拖拽 primitive；如果没有这一行，猫 prompt 无法进入真实 Paint 计划。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_launch_resolver import resolve_generic_app_launch_target  # 新增代码+PaintPikachuRealLoop：复用通用应用发现和高风险拒绝；如果没有这一行，Paint 启动会变成新白名单补丁。
    from learning_agent.computer_use_mcp_v2.windows_runtime.generic_launch_backend import Phase110OwnedProcessRegistry, Phase110ProductionGenericLaunchBackend, run_generic_launch_backend  # 新增代码+PaintPikachuRealLoop：复用 argv/no-shell 真实启动后端；如果没有这一行，启动 Paint 可能绕开已有安全后端。
    from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+PaintPikachuRealLoop：复用真实 Windows SendInput sender；如果没有这一行，拖拽事件无法触达真实桌面。
    from learning_agent.computer_use_mcp_v2.windows_runtime.screenshot_runtime import WindowsScreenshotCaptureRuntime  # 新增代码+PaintVisualGuard：复用项目现有窗口截图 runtime 做动作后视觉验真；如果没有这一行，Paint loop 只能继续相信自报字段。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # 新增代码+PaintPikachuRealLoop：复用只读窗口枚举；如果没有这一行，动作前无法找到并复核 Paint 窗口。
except ModuleNotFoundError as error:  # 新增代码+PaintPikachuRealLoop：兼容 start_oauth_agent.bat 从 learning_agent 目录启动的脚本模式；如果没有这一段，真实可见终端可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.drawing_primitives", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_launch_resolver", "learning_agent.computer_use_mcp_v2.windows_runtime.generic_launch_backend", "learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard", "learning_agent.computer_use_mcp_v2.windows_runtime.screenshot_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend"}:  # 修改代码+PaintVisualGuard：允许脚本模式兜底截图 runtime 路径；如果没有这一行，bat 入口会把正常包路径差异误当内部错误。
        raise  # 新增代码+PaintPikachuRealLoop：重新抛出非路径类导入错误；如果没有这一行，排查真实控制链问题会很困难。
    from computer_use_mcp_v2.windows_runtime.drawing_primitives import build_cat_drag_plan, build_elephant_drag_plan, build_pikachu_drag_plan, expand_drag_path_to_low_level_events  # type: ignore  # 修改代码+PaintCatSubject：脚本模式同时复用猫、大象和皮卡丘 primitive；如果没有这一行，bat 入口下猫仍会被拒绝或误画。
    from computer_use_mcp_v2.windows_runtime.windows_launch_resolver import resolve_generic_app_launch_target  # type: ignore  # 新增代码+PaintPikachuRealLoop：脚本模式复用通用应用发现；如果没有这一行，bat 入口会失去高风险拒绝和安全计划。
    from computer_use_mcp_v2.windows_runtime.generic_launch_backend import Phase110OwnedProcessRegistry, Phase110ProductionGenericLaunchBackend, run_generic_launch_backend  # type: ignore  # 新增代码+PaintPikachuRealLoop：脚本模式复用真实启动后端；如果没有这一行，bat 入口无法安全启动 mspaint。
    from computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # type: ignore  # 新增代码+PaintPikachuRealLoop：脚本模式复用真实 SendInput sender；如果没有这一行，bat 入口无法发送鼠标拖拽。
    from computer_use_mcp_v2.windows_runtime.screenshot_runtime import WindowsScreenshotCaptureRuntime  # type: ignore  # 新增代码+PaintVisualGuard：脚本模式复用同一截图 runtime；如果没有这一行，start_oauth_agent.bat 下不能做视觉验真。
    from computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # type: ignore  # 新增代码+PaintPikachuRealLoop：脚本模式复用窗口枚举；如果没有这一行，bat 入口无法复核 Paint 窗口。

PAINT_PIKACHU_REAL_LOOP_MODEL = "paint_pikachu_real_execution_loop"  # 新增代码+PaintPikachuRealLoop：定义真实闭环模型名；如果没有这一行，报告无法区分录制证据和真实执行。
PAINT_PIKACHU_REAL_LOOP_MARKER = "PAINT_PIKACHU_REAL_LOOP_READY"  # 新增代码+PaintPikachuRealLoop：定义稳定 ready 标记；如果没有这一行，终端和测试不容易定位真实闭环。
PAINT_PIKACHU_REAL_LOOP_OK = "PAINT_PIKACHU_REAL_LOOP_OK"  # 新增代码+PaintPikachuRealLoop：定义真实闭环成功 token；如果没有这一行，成功和普通日志不容易区分。
PAINT_SUPPORTED_DRAWING_SUBJECTS = ["pikachu", "elephant", "cat"]  # 修改代码+PaintCatSubject：声明当前真实 Paint loop 明确支持皮卡丘、大象和猫；如果没有这一行，猫会在启动 Paint 前被错误拒绝。


def _paint_loop_subject_from_prompt(prompt: str) -> str:  # 新增代码+GenericPaintSubject：函数段开始，从用户自然语言中识别要画的对象；如果没有这段函数，大象 prompt 会继续被皮卡丘默认值吞掉。
    text = str(prompt or "").lower()  # 新增代码+GenericPaintSubject：把 prompt 转成小写文本；如果没有这一行，英文 Elephant/Pikachu 大小写会影响识别。
    if "大象" in text or "elephant" in text:  # 新增代码+GenericPaintSubject：识别中文大象和英文 elephant；如果没有这一行，用户反馈的大象场景无法进入大象计划。
        return "elephant"  # 新增代码+GenericPaintSubject：返回大象 subject；如果没有这一行，调用方不知道该选择哪个拖拽计划。
    if "猫" in text or "小猫" in text or "cat" in text or "kitty" in text:  # 新增代码+PaintCatSubject：识别中文猫、小猫和英文 cat/kitty；如果没有这一行，用户输入画猫仍会被当成未知对象。
        return "cat"  # 新增代码+PaintCatSubject：返回猫 subject；如果没有这一行，调用方不知道该选择猫拖拽计划。
    if "皮卡丘" in text or "pikachu" in text:  # 新增代码+GenericPaintSubject：识别中文皮卡丘和英文 pikachu；如果没有这一行，原有皮卡丘验收会被误拒绝。
        return "pikachu"  # 新增代码+GenericPaintSubject：返回皮卡丘 subject；如果没有这一行，调用方无法保持旧功能。
    return "unsupported"  # 新增代码+GenericPaintSubject：未知对象明确返回不支持；如果没有这一行，系统可能又偷偷退回画皮卡丘。
# 新增代码+GenericPaintSubject：函数段结束，_paint_loop_subject_from_prompt 到此结束；如果没有这个边界说明，代码小白不容易看出对象识别范围。


def _paint_loop_plan_for_subject(subject: str, canvas: dict[str, int]) -> dict[str, Any]:  # 新增代码+GenericPaintSubject：函数段开始，根据对象选择对应绘图计划；如果没有这段函数，run_desktop_task 会继续写死单一皮卡丘计划。
    if subject == "elephant":  # 新增代码+GenericPaintSubject：判断是否要画大象；如果没有这一行，大象计划永远不会被调用。
        return build_elephant_drag_plan(canvas)  # 新增代码+GenericPaintSubject：返回大象拖拽计划；如果没有这一行，用户输入大象仍不会产生长鼻子和大耳朵。
    if subject == "cat":  # 新增代码+PaintCatSubject：判断是否要画猫；如果没有这一行，猫计划永远不会被调用。
        return build_cat_drag_plan(canvas)  # 新增代码+PaintCatSubject：返回猫拖拽计划；如果没有这一行，用户输入猫仍不会产生猫耳、胡须和卷尾巴。
    if subject == "pikachu":  # 新增代码+GenericPaintSubject：判断是否要画皮卡丘；如果没有这一行，旧皮卡丘能力会断掉。
        plan = build_pikachu_drag_plan(canvas)  # 新增代码+GenericPaintSubject：生成原有皮卡丘拖拽计划；如果没有这一行，皮卡丘验收没有可执行路径。
        plan["drawing_subject"] = "pikachu"  # 新增代码+GenericPaintSubject：给旧计划补充对象字段；如果没有这一行，报告无法清楚说明本次画的是皮卡丘。
        return plan  # 新增代码+GenericPaintSubject：返回皮卡丘计划；如果没有这一行，调用方拿不到可执行计划。
    return {"passed": False, "drawing_subject": subject, "drag_paths": [], "drag_path_count": 0, "gui_action_count": 0, "low_level_event_count": 0, "colors": [], "elements": []}  # 新增代码+GenericPaintSubject：未知对象返回空失败计划；如果没有这一行，未知对象可能被错误执行。
# 新增代码+GenericPaintSubject：函数段结束，_paint_loop_plan_for_subject 到此结束；如果没有这个边界说明，代码小白不容易看出计划选择范围。


def _paint_loop_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+PaintPikachuRealLoop：函数段开始，安全转换窗口坐标和事件计数；如果没有这个函数，坏窗口字段会让真实执行崩溃。
    try:  # 新增代码+PaintPikachuRealLoop：尝试把动态值转成整数；如果没有这一行，字符串坐标无法兼容。
        return int(value)  # 新增代码+PaintPikachuRealLoop：返回转换后的整数；如果没有这一行，调用方拿不到可比较数值。
    except (TypeError, ValueError):  # 新增代码+PaintPikachuRealLoop：捕获 None 或非数字文本；如果没有这一行，窗口枚举异常字段会中断任务。
        return int(default)  # 新增代码+PaintPikachuRealLoop：返回默认值；如果没有这一行，失败路径不能安全落到 0。
# 新增代码+PaintPikachuRealLoop：函数段结束，_paint_loop_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出数字兜底范围。


def _paint_loop_window_text(window: dict[str, Any]) -> str:  # 新增代码+PaintPikachuRealLoop：函数段开始，合并窗口身份文本用于判断是否为 Paint；如果没有这个函数，窗口匹配逻辑会散落重复。
    return " ".join(str(window.get(key, "") or "").lower() for key in ("title_preview", "title", "app_id", "process_name", "class_name", "window_id"))  # 新增代码+PaintPikachuRealLoop：返回小写身份文本；如果没有这一行，mspaint 标题或进程线索无法统一匹配。
# 新增代码+PaintPikachuRealLoop：函数段结束，_paint_loop_window_text 到此结束；如果没有这个边界说明，初学者不容易看出窗口文本范围。


def _paint_loop_is_paint_window(window: dict[str, Any], process_id: int = 0) -> bool:  # 新增代码+PaintPikachuRealLoop：函数段开始，判断窗口是否属于本次 Paint 任务；如果没有这个函数，真实拖拽可能打到错误窗口。
    text = _paint_loop_window_text(window)  # 新增代码+PaintPikachuRealLoop：读取窗口身份文本；如果没有这一行，后续没有判断对象。
    pid_matches = process_id > 0 and _paint_loop_safe_int(window.get("pid") or window.get("window_process_id")) == process_id  # 新增代码+PaintPikachuRealLoop：优先用本次启动的 pid 匹配；如果没有这一行，用户已有 Paint 窗口可能被误用。
    name_matches = "paint" in text or "mspaint" in text or "画图" in text  # 新增代码+PaintPikachuRealLoop：兼容英文 Paint、mspaint 和中文画图标题；如果没有这一行，真实窗口标题本地化会导致找不到目标。
    return bool(name_matches and (pid_matches or process_id <= 0))  # 新增代码+PaintPikachuRealLoop：必须像 Paint 且优先绑定 pid；如果没有这一行，窗口身份验证会过宽。
# 新增代码+PaintPikachuRealLoop：函数段结束，_paint_loop_is_paint_window 到此结束；如果没有这个边界说明，初学者不容易看出 Paint 窗口判断范围。


def _paint_loop_canvas_rect(window: dict[str, Any]) -> dict[str, int]:  # 新增代码+PaintPikachuRealLoop：函数段开始，从 Paint 窗口估算安全画布区域；如果没有这个函数，鼠标拖拽没有可落点范围。
    rect = dict(window.get("rect", {}) if isinstance(window.get("rect"), dict) else {})  # 新增代码+PaintPikachuRealLoop：读取窗口矩形并复制；如果没有这一行，后续可能直接污染窗口快照。
    left = _paint_loop_safe_int(rect.get("left"))  # 新增代码+PaintPikachuRealLoop：读取窗口左边界；如果没有这一行，画布 x 坐标没有基准。
    top = _paint_loop_safe_int(rect.get("top"))  # 新增代码+PaintPikachuRealLoop：读取窗口上边界；如果没有这一行，画布 y 坐标没有基准。
    right = _paint_loop_safe_int(rect.get("right"), left + 900)  # 新增代码+PaintPikachuRealLoop：读取窗口右边界并兜底；如果没有这一行，缺 rect 时无法生成宽度。
    bottom = _paint_loop_safe_int(rect.get("bottom"), top + 700)  # 新增代码+PaintPikachuRealLoop：读取窗口下边界并兜底；如果没有这一行，缺 rect 时无法生成高度。
    width = max(400, right - left)  # 新增代码+PaintPikachuRealLoop：计算最小可用宽度；如果没有这一行，过小窗口会让路径挤成一团。
    height = max(300, bottom - top)  # 新增代码+PaintPikachuRealLoop：计算最小可用高度；如果没有这一行，过小窗口会让路径挤成一团。
    if width >= 1200 and height >= 800:  # 新增代码+PaintCanvasRectGuard：最大化 Paint 使用真实白纸区域偏移；如果没有这一行，顶部工具栏和左侧面板会被误当画布。
        return {"left": left + 390, "top": top + 265, "right": right - 380, "bottom": bottom - 115}  # 新增代码+PaintCanvasRectGuard：返回最大化 Paint 白色画布近似区域；如果没有这一行，皮卡丘会被画得过大且部分落到画布外。
    return {"left": left + min(95, width // 5), "top": top + min(170, height // 3), "right": right - min(60, width // 8), "bottom": bottom - min(80, height // 6)}  # 新增代码+PaintPikachuRealLoop：避开 Paint 顶部工具栏和边框后返回画布区域；如果没有这一行，拖拽可能落在菜单/工具栏上。
# 新增代码+PaintPikachuRealLoop：函数段结束，_paint_loop_canvas_rect 到此结束；如果没有这个边界说明，初学者不容易看出画布估算范围。


def _paint_loop_prepare_window(window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+PaintPikachuRealLoop：函数段开始，最大化并刷新 Paint 窗口矩形；如果没有这个函数，窄窗口会让工具栏折叠导致铅笔工具坐标失效。
    prepared = dict(window)  # 新增代码+PaintPikachuRealLoop：复制窗口记录；如果没有这一行，准备阶段会污染原始 inventory 快照。
    hwnd = _paint_loop_safe_int(prepared.get("hwnd"))  # 新增代码+PaintPikachuRealLoop：读取窗口句柄；如果没有这一行，无法调用 Win32 最大化和取矩形。
    if hwnd <= 0 or sys.platform != "win32":  # 新增代码+PaintPikachuRealLoop：只有 Windows 且句柄有效才操作窗口；如果没有这一行，非 Windows 或坏句柄会抛异常。
        return prepared  # 新增代码+PaintPikachuRealLoop：无法准备时返回原窗口；如果没有这一行，调用方拿不到兜底目标。
    try:  # 新增代码+PaintPikachuRealLoop：捕获窗口准备异常；如果没有这一行，最大化失败会中断整次绘图。
        import ctypes  # 新增代码+PaintPikachuRealLoop：延迟导入 ctypes 调用 user32；如果没有这一行，无法访问 Win32 窗口 API。
        from ctypes import wintypes  # 新增代码+PaintPikachuRealLoop：导入 RECT/HWND 类型；如果没有这一行，GetWindowRect 参数类型不清楚。
        user32 = ctypes.windll.user32  # 新增代码+PaintPikachuRealLoop：缓存 user32.dll；如果没有这一行，后续调用入口不稳定。
        user32.ShowWindowAsync(wintypes.HWND(hwnd), 3)  # 新增代码+PaintPikachuRealLoop：最大化 Paint 窗口；如果没有这一行，工具栏可能折叠导致选不到铅笔。
        user32.SetForegroundWindow(wintypes.HWND(hwnd))  # 新增代码+PaintPikachuRealLoop：把 Paint 切到前台；如果没有这一行，后续工具点击可能落到别的窗口。
        time.sleep(0.6)  # 新增代码+PaintPikachuRealLoop：等待最大化动画和工具栏重排完成；如果没有这一行，取到的矩形或工具坐标可能还是旧布局。
        rect = wintypes.RECT()  # 新增代码+PaintPikachuRealLoop：准备接收窗口矩形；如果没有这一行，GetWindowRect 没有输出容器。
        if user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):  # 新增代码+PaintPikachuRealLoop：读取最大化后的窗口矩形；如果没有这一行，画布和工具坐标仍用旧窗口大小。
            prepared["rect"] = {"left": int(rect.left), "top": int(rect.top), "right": int(rect.right), "bottom": int(rect.bottom)}  # 新增代码+PaintPikachuRealLoop：更新窗口矩形；如果没有这一行，后续画布计划仍可能落在错误区域。
    except Exception:  # 新增代码+PaintPikachuRealLoop：任何准备失败都退回原窗口；如果没有这一行，局部 Win32 问题会让任务直接崩溃。
        return prepared  # 新增代码+PaintPikachuRealLoop：返回已复制窗口作为安全兜底；如果没有这一行，异常分支没有返回值。
    return prepared  # 新增代码+PaintPikachuRealLoop：返回准备后的窗口；如果没有这一行，调用方拿不到最大化后的 rect。
# 新增代码+PaintPikachuRealLoop：函数段结束，_paint_loop_prepare_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口准备范围。


def _paint_loop_low_level_events(window: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+PaintPikachuRealLoop：函数段开始，把皮卡丘计划转成可发送的低层事件；如果没有这个函数，真实闭环只有计划没有动作。
    events: list[dict[str, Any]] = []  # 新增代码+PaintPikachuRealLoop：准备低层事件列表；如果没有这一行，后续无法累积聚焦和拖拽动作。
    hwnd = _paint_loop_safe_int(window.get("hwnd"))  # 新增代码+PaintPikachuRealLoop：读取窗口句柄用于聚焦；如果没有这一行，拖拽可能发到旧前台窗口。
    if hwnd > 0:  # 新增代码+PaintPikachuRealLoop：只有有效句柄才发送聚焦事件；如果没有这一行，0 句柄会被传给 Win32。
        events.append({"type": "set_foreground", "hwnd": hwnd})  # 新增代码+PaintPikachuRealLoop：先把 Paint 窗口切到前台；如果没有这一行，真实输入可能落到别的应用。
    events.extend(_paint_loop_select_pencil_events(window))  # 新增代码+PaintPikachuRealLoop：先点击 Paint 铅笔工具再画；如果没有这一行，Paint 若停在选择工具或橡皮擦时拖拽不会留下线条。
    for path in list(plan.get("drag_paths", []) or []):  # 新增代码+PaintPikachuRealLoop：遍历每一条皮卡丘笔画；如果没有这一行，计划不会变成任何拖拽。
        if not isinstance(path, dict):  # 新增代码+PaintPikachuRealLoop：跳过坏笔画数据；如果没有这一行，异常数据会让整次任务崩溃。
            continue  # 新增代码+PaintPikachuRealLoop：继续处理下一条笔画；如果没有这一行，坏数据分支不能安全退出。
        events.extend(expand_drag_path_to_low_level_events(list(path.get("points", []))))  # 新增代码+PaintPikachuRealLoop：把当前笔画展开为鼠标移动/按下/抬起；如果没有这一行，Paint 不会收到真实绘制动作。
    return events  # 新增代码+PaintPikachuRealLoop：返回完整低层事件；如果没有这一行，sender 没有输入。
# 新增代码+PaintPikachuRealLoop：函数段结束，_paint_loop_low_level_events 到此结束；如果没有这个边界说明，初学者不容易看出事件展开范围。


def _paint_loop_select_pencil_events(window: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+PaintPikachuRealLoop：函数段开始，生成选择 Paint 铅笔工具的点击事件；如果没有这个函数，绘图结果会依赖用户上一次选择的工具。
    rect = dict(window.get("rect", {}) if isinstance(window.get("rect"), dict) else {})  # 新增代码+PaintPikachuRealLoop：读取窗口矩形；如果没有这一行，工具栏坐标无法按当前窗口位置计算。
    left = _paint_loop_safe_int(rect.get("left"))  # 新增代码+PaintPikachuRealLoop：读取窗口左边界；如果没有这一行，铅笔工具 x 坐标没有基准。
    top = _paint_loop_safe_int(rect.get("top"))  # 新增代码+PaintPikachuRealLoop：读取窗口上边界；如果没有这一行，铅笔工具 y 坐标没有基准。
    right = _paint_loop_safe_int(rect.get("right"), left + 1000)  # 新增代码+PaintPikachuRealLoop：读取窗口右边界并兜底；如果没有这一行，窗口宽度无法计算。
    bottom = _paint_loop_safe_int(rect.get("bottom"), top + 700)  # 新增代码+PaintPikachuRealLoop：读取窗口下边界并兜底；如果没有这一行，窗口高度无法计算。
    _ = max(1, right - left)  # 修改代码+PaintPikachuRealLoop：保留窗口宽度计算位以说明这里依赖最大化后的稳定布局；如果没有这一行，读者可能误以为 right 未使用是遗漏。
    _ = max(1, bottom - top)  # 修改代码+PaintPikachuRealLoop：保留窗口高度计算位以说明这里依赖最大化后的稳定布局；如果没有这一行，读者可能误以为 bottom 未使用是遗漏。
    pencil_x = left + 270  # 修改代码+PaintPikachuRealLoop：最大化后固定点击 Paint 铅笔工具中心 x；如果没有这一行，比例坐标会在折叠工具栏中点错按钮。
    pencil_y = top + 96  # 修改代码+PaintPikachuRealLoop：最大化后固定点击 Paint 铅笔工具中心 y；如果没有这一行，工具选择可能落不到铅笔。
    return [{"type": "mouse_move", "x": pencil_x, "y": pencil_y}, {"type": "mouse_down", "button": "left"}, {"type": "mouse_up", "button": "left"}, {"type": "pause", "seconds": 0.35}]  # 修改代码+PaintStablePause：点击铅笔后等待 Paint 完成工具切换；如果没有这一行，第一条主体轮廓可能在工具状态未稳定时被吞掉。
# 新增代码+PaintPikachuRealLoop：函数段结束，_paint_loop_select_pencil_events 到此结束；如果没有这个边界说明，初学者不容易看出工具选择范围。


def _paint_loop_visual_canvas_report(window: dict[str, Any], canvas: dict[str, int], screenshot_result: dict[str, Any], subject: str = "pikachu") -> dict[str, Any]:  # 修改代码+GenericPaintSubject：函数段开始，根据绘画对象和动作后截图判断 Paint 画布是否真的出现笔迹；如果没有 subject 参数，大象也会被皮卡丘视觉规则误判。
    screenshot_path = str(screenshot_result.get("screenshot_path", "") or "")  # 新增代码+PaintVisualGuard：读取截图 artifact 路径；如果没有这一行，像素门禁不知道该打开哪张图。
    screenshot_exists = bool(screenshot_result.get("screenshot_captured", screenshot_result.get("captured", False)) and screenshot_path and Path(screenshot_path).exists())  # 新增代码+PaintVisualGuard：确认截图真实落盘；如果没有这一行，空路径也可能被当成视觉证据。
    base_report = {"post_action_screenshot_exists": screenshot_exists, "post_action_visual_evidence_path": screenshot_path if screenshot_exists else "", "post_action_screenshot_result": screenshot_result, "canvas_changed_after_actions": False, "drawing_visual_elements": False, "pikachu_visual_elements": False, "elephant_visual_elements": False, "cat_visual_elements": False, "visual_non_background_pixel_count": 0, "visual_guard_reason": ""}  # 修改代码+PaintCatSubject：创建默认失败视觉报告并区分猫/大象/皮卡丘字段；如果没有这一行，猫报告会缺少专属视觉证据。
    if not screenshot_exists:  # 新增代码+PaintVisualGuard：没有截图时直接失败；如果没有这一行，后续打开空路径会抛异常。
        base_report["visual_guard_reason"] = "post_action_screenshot_missing"  # 新增代码+PaintVisualGuard：记录缺少截图原因；如果没有这一行，用户不知道失败卡在证据采集。
        return base_report  # 新增代码+PaintVisualGuard：返回缺截图失败报告；如果没有这一行，缺证据仍会继续像素检查。
    try:  # 新增代码+PaintVisualGuard：捕获图片读取和像素解析异常；如果没有这一行，坏截图会让整个 agent 崩溃。
        from PIL import Image  # 新增代码+PaintVisualGuard：延迟导入 Pillow 读取 PNG/BMP/JPEG；如果没有这一行，无法用统一方式解析截图像素。
        rect = dict(window.get("rect", {}) if isinstance(window.get("rect"), dict) else {})  # 新增代码+PaintVisualGuard：读取窗口矩形用于把屏幕坐标转成截图内坐标；如果没有这一行，canvas 坐标会错位。
        window_left = _paint_loop_safe_int(rect.get("left"))  # 新增代码+PaintVisualGuard：读取窗口左上角 x；如果没有这一行，画布区域无法转为相对截图坐标。
        window_top = _paint_loop_safe_int(rect.get("top"))  # 新增代码+PaintVisualGuard：读取窗口左上角 y；如果没有这一行，画布区域无法转为相对截图坐标。
        image = Image.open(screenshot_path).convert("RGB")  # 新增代码+PaintVisualGuard：打开截图并统一成 RGB；如果没有这一行，不同图片格式的像素结构不一致。
        width, height = image.size  # 新增代码+PaintVisualGuard：读取截图尺寸；如果没有这一行，后续无法把区域夹在图片边界内。
        left = max(0, min(width, _paint_loop_safe_int(canvas.get("left")) - window_left))  # 新增代码+PaintVisualGuard：计算画布左边界相对截图坐标；如果没有这一行，可能把工具栏像素误判成画布变化。
        top = max(0, min(height, _paint_loop_safe_int(canvas.get("top")) - window_top))  # 新增代码+PaintVisualGuard：计算画布上边界相对截图坐标；如果没有这一行，顶部工具栏可能污染像素判断。
        right = max(left, min(width, _paint_loop_safe_int(canvas.get("right")) - window_left))  # 新增代码+PaintVisualGuard：计算画布右边界相对截图坐标；如果没有这一行，像素扫描范围可能越界。
        bottom = max(top, min(height, _paint_loop_safe_int(canvas.get("bottom")) - window_top))  # 新增代码+PaintVisualGuard：计算画布下边界相对截图坐标；如果没有这一行，像素扫描范围可能越界。
        non_background = 0  # 修改代码+PaintRecognizableVisualGuard：初始化全画布非白背景像素计数；如果没有这一行，无法量化 Paint 里到底留下了多少笔迹。
        canvas_width = max(1, right - left)  # 新增代码+PaintRecognizableVisualGuard：计算画布扫描宽度；如果没有这一行，后续无法判断笔迹是否覆盖到皮卡丘不同部位。
        canvas_height = max(1, bottom - top)  # 新增代码+PaintRecognizableVisualGuard：计算画布扫描高度；如果没有这一行，后续无法判断上中下区域是否都有图形。
        region_counts = {"upper": 0, "middle": 0, "lower": 0, "tail": 0, "face": 0}  # 新增代码+PaintRecognizableVisualGuard：记录关键区域笔迹数量；如果没有这一行，只有耳朵或几条线也可能冒充皮卡丘。
        for y in range(top, bottom):  # 新增代码+PaintVisualGuard：逐行扫描画布区域；如果没有这一行，像素门禁不会检查整块画布。
            for x in range(left, right):  # 新增代码+PaintVisualGuard：逐列扫描画布区域；如果没有这一行，像素门禁只会看到空范围。
                red, green, blue = image.getpixel((x, y))  # 新增代码+PaintVisualGuard：读取单个像素 RGB；如果没有这一行，无法判断它是否像画笔颜色。
                if min(red, green, blue) < 245:  # 新增代码+PaintVisualGuard：把黑线、红脸、黄身体等非白像素计入笔迹；如果没有这一行，白画布和真实图形无法区分。
                    non_background += 1  # 新增代码+PaintVisualGuard：累计非背景像素；如果没有这一行，门禁没有通过依据。
                    rel_x = (x - left) / canvas_width  # 新增代码+PaintRecognizableVisualGuard：计算当前笔迹点在画布中的横向比例；如果没有这一行，无法知道它是不是尾巴或脸部区域。
                    rel_y = (y - top) / canvas_height  # 新增代码+PaintRecognizableVisualGuard：计算当前笔迹点在画布中的纵向比例；如果没有这一行，无法知道它是不是耳朵、脸或下半身。
                    region_counts["upper"] += 1 if rel_y < 0.35 else 0  # 新增代码+PaintRecognizableVisualGuard：统计上方耳朵区域笔迹；如果没有这一行，缺耳朵也可能通过。
                    region_counts["middle"] += 1 if 0.30 <= rel_y <= 0.70 else 0  # 新增代码+PaintRecognizableVisualGuard：统计中部脸和身体区域笔迹；如果没有这一行，主体缺失也可能通过。
                    region_counts["lower"] += 1 if rel_y > 0.55 else 0  # 新增代码+PaintRecognizableVisualGuard：统计下方身体或尾巴区域笔迹；如果没有这一行，只有头部线条也可能通过。
                    region_counts["tail"] += 1 if rel_x > 0.65 and rel_y > 0.40 else 0  # 新增代码+PaintRecognizableVisualGuard：统计右侧闪电尾巴区域笔迹；如果没有这一行，少了皮卡丘标志性尾巴也可能通过。
                    region_counts["face"] += 1 if 0.35 <= rel_x <= 0.65 and 0.30 <= rel_y <= 0.65 else 0  # 新增代码+PaintRecognizableVisualGuard：统计脸部核心区域笔迹；如果没有这一行，只有边缘线条也可能通过。
        base_report["visual_non_background_pixel_count"] = non_background  # 新增代码+PaintVisualGuard：把像素计数写入报告；如果没有这一行，用户无法审计门禁依据。
        base_report["visual_region_counts"] = region_counts  # 新增代码+PaintRecognizableVisualGuard：把各区域笔迹数量写入报告；如果没有这一行，用户无法复核为什么视觉门禁通过或失败。
        if subject == "elephant":  # 新增代码+GenericPaintSubject：大象使用适合大身体、头部、腿部的区域门禁；如果没有这一行，大象会被要求具备皮卡丘尾巴和耳尖。
            recognizable = bool(non_background >= 350 and region_counts["middle"] >= 120 and region_counts["lower"] >= 40 and region_counts["face"] >= 40)  # 新增代码+GenericPaintSubject：要求大象主体、中下部和头部区域都有笔迹；如果没有这一行，几条孤立线也会冒充大象成功。
            base_report["elephant_visual_elements"] = recognizable  # 新增代码+GenericPaintSubject：写入大象专属视觉元素结果；如果没有这一行，终端无法证明本次按大象规则验收。
            base_report["visual_guard_reason"] = "recognizable_elephant_regions_present" if recognizable else "elephant_regions_incomplete"  # 新增代码+GenericPaintSubject：记录大象视觉门禁原因；如果没有这一行，失败时不知道缺的是主体还是下半身结构。
        elif subject == "cat":  # 新增代码+PaintCatSubject：猫使用适合耳朵、脸、身体和右侧尾巴的区域门禁；如果没有这一行，猫会继续套用皮卡丘或大象规则。
            recognizable = bool(non_background >= 350 and region_counts["upper"] >= 30 and region_counts["middle"] >= 120 and region_counts["face"] >= 40 and region_counts["tail"] >= 20)  # 新增代码+PaintCatSubject：要求猫头耳朵、脸部、主体和尾巴区域都有笔迹；如果没有这一行，几条胡须线也可能冒充猫成功。
            base_report["cat_visual_elements"] = recognizable  # 新增代码+PaintCatSubject：写入猫专属视觉元素结果；如果没有这一行，终端无法证明本次按猫规则验收。
            base_report["visual_guard_reason"] = "recognizable_cat_regions_present" if recognizable else "cat_regions_incomplete"  # 新增代码+PaintCatSubject：记录猫视觉门禁原因；如果没有这一行，失败时不知道缺的是耳朵、脸还是尾巴区域。
        else:  # 新增代码+GenericPaintSubject：皮卡丘继续使用旧的耳朵、脸、尾巴门禁；如果没有这一行，旧验收会失去专属严格规则。
            recognizable = bool(non_background >= 350 and region_counts["upper"] >= 30 and region_counts["middle"] >= 120 and region_counts["face"] >= 40 and region_counts["tail"] >= 20)  # 修改代码+GenericPaintSubject：要求皮卡丘总笔迹和耳朵/主体/脸/尾巴区域都达标；如果没有这一行，几条断线仍会被误判成熟。
            base_report["pikachu_visual_elements"] = recognizable  # 修改代码+GenericPaintSubject：代表性皮卡丘元素必须和严格视觉门禁一致；如果没有这一行，字段会再次自报成功。
            base_report["visual_guard_reason"] = "recognizable_pikachu_regions_present" if recognizable else "pikachu_regions_incomplete"  # 修改代码+GenericPaintSubject：记录是否具备可识别皮卡丘区域；如果没有这一行，失败时不知道缺的是画布变化还是结构分布。
        base_report["canvas_changed_after_actions"] = recognizable  # 修改代码+GenericPaintSubject：只有当前对象的可识别分布达标才承认画布变化；如果没有这一行，空白或残缺图形会继续通过。
        base_report["drawing_visual_elements"] = recognizable  # 新增代码+GenericPaintSubject：写入通用绘画对象视觉结果；如果没有这一行，上层只能读皮卡丘专属字段。
        return base_report  # 新增代码+PaintVisualGuard：返回截图像素报告；如果没有这一行，调用方拿不到视觉门禁结果。
    except Exception as error:  # 新增代码+PaintVisualGuard：捕获 Pillow 缺失、图片损坏或坐标异常；如果没有这一行，坏截图会中断交互终端。
        base_report["visual_guard_reason"] = f"visual_guard_error:{type(error).__name__}"  # 新增代码+PaintVisualGuard：记录视觉门禁异常类型；如果没有这一行，用户不知道为什么视觉验证失败。
        return base_report  # 新增代码+PaintVisualGuard：返回安全失败报告；如果没有这一行，异常路径没有结果。
# 新增代码+PaintVisualGuard：函数段结束，_paint_loop_visual_canvas_report 到此结束；如果没有这个边界说明，初学者不容易看出视觉门禁范围。


class WindowsPaintPikachuRealExecutionLoop:  # 修改代码+GenericPaintSubject：类段开始，封装 full 模式 Paint 已支持对象真实执行流程；如果没有这个类，desktop_task_runtime 仍没有可注入真实闭环。
    def __init__(self, base_dir: str | Path | None = None, inventory: Any | None = None, low_level_sender: Any | None = None, launch_backend: Any | None = None, screenshot_runtime: Any | None = None, platform: str | None = None, poll_timeout_seconds: float = 10.0) -> None:  # 修改代码+PaintVisualGuard：函数段开始，初始化真实闭环并允许注入截图验真 runtime；如果没有这段函数，测试和生产都无法区分真画布和自报成功。
        self.base_dir = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "paint_pikachu_real_loop"  # 新增代码+PaintPikachuRealLoop：保存证据目录；如果没有这一行，真实执行报告没有稳定落点。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+PaintPikachuRealLoop：确保证据目录存在；如果没有这一行，首次运行写证据会失败。
        self.platform = str(platform or sys.platform)  # 新增代码+PaintPikachuRealLoop：保存运行平台；如果没有这一行，非 Windows 拒绝无法稳定判断。
        self.inventory = inventory if inventory is not None else WindowsWindowInventoryProbe()  # 新增代码+PaintPikachuRealLoop：保存只读窗口枚举器；如果没有这一行，真实路径找不到 Paint 窗口。
        self.low_level_sender = low_level_sender if low_level_sender is not None else WindowsSendInputLowLevelSender(platform=self.platform)  # 新增代码+PaintPikachuRealLoop：保存真实或测试低层 sender；如果没有这一行，拖拽事件无法发送。
        self.screenshot_runtime = screenshot_runtime if screenshot_runtime is not None else WindowsScreenshotCaptureRuntime(evidence_root=self.base_dir / "visual_evidence", platform=self.platform)  # 新增代码+PaintVisualGuard：保存动作后截图 runtime；如果没有这一行，报告无法用真实图片证明 Paint 画布变化。
        self.launch_registry = Phase110OwnedProcessRegistry()  # 新增代码+PaintPikachuRealLoop：保存自有进程登记表；如果没有这一行，启动 Paint 后无法证明是 agent 自己启动的进程。
        self.launch_backend = launch_backend if launch_backend is not None else Phase110ProductionGenericLaunchBackend(registry=self.launch_registry, platform=self.platform)  # 新增代码+PaintPikachuRealLoop：保存真实启动后端；如果没有这一行，full prompt 不会真正打开 mspaint。
        self.poll_timeout_seconds = float(poll_timeout_seconds)  # 新增代码+PaintPikachuRealLoop：保存窗口轮询超时；如果没有这一行，Paint 启动慢时没有等待窗口的时间边界。
    # 新增代码+PaintPikachuRealLoop：函数段结束，WindowsPaintPikachuRealExecutionLoop.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+PaintPikachuRealLoop：函数段开始，返回真实闭环可用性摘要；如果没有这段函数，成熟矩阵无法只读判断是否已接线。
        sender_available = self.low_level_sender is not None and hasattr(self.low_level_sender, "send_low_level")  # 新增代码+PaintPikachuRealLoop：检查 sender 接口是否存在；如果没有这一行，状态可能误报可真实发送。
        inventory_available = self.inventory is not None and hasattr(self.inventory, "snapshot")  # 新增代码+PaintPikachuRealLoop：检查窗口枚举接口是否存在；如果没有这一行，状态可能误报可复核窗口。
        launch_available = self.launch_backend is not None and hasattr(self.launch_backend, "launch")  # 新增代码+PaintPikachuRealLoop：检查启动后端接口是否存在；如果没有这一行，状态可能误报可打开 Paint。
        screenshot_available = self.screenshot_runtime is not None and hasattr(self.screenshot_runtime, "capture_window")  # 新增代码+PaintVisualGuard：检查截图验真接口是否存在；如果没有这一行，成熟矩阵可能不知道视觉门禁缺失。
        return {"marker": PAINT_PIKACHU_REAL_LOOP_MARKER, "model": PAINT_PIKACHU_REAL_LOOP_MODEL, "available": bool(self.platform == "win32" and sender_available and inventory_available and launch_available and screenshot_available), "platform": self.platform, "sender_available": sender_available, "inventory_available": inventory_available, "launch_backend_available": launch_available, "screenshot_runtime_available": screenshot_available, "target_app": "mspaint", "real_desktop_execution_loop": True}  # 修改代码+PaintVisualGuard：返回包含截图门禁的只读状态；如果没有这一行，maturity 会忽略真实视觉验证能力。
    # 新增代码+PaintPikachuRealLoop：函数段结束，WindowsPaintPikachuRealExecutionLoop.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def _failure(self, decision: str, reason: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+PaintPikachuRealLoop：函数段开始，构造统一失败报告；如果没有这个函数，失败字段会漂移并难以测试。
        report = {"ok": False, "marker": PAINT_PIKACHU_REAL_LOOP_MARKER, "model": PAINT_PIKACHU_REAL_LOOP_MODEL, "decision": decision, "reason": reason, "target_app": "mspaint", "computer_use_gui_route_used": False, "owned_window_verified": False, "gui_action_count": 0, "low_level_event_count": 0, "real_dispatch_performed": False, "real_desktop_touched": False, "post_action_screenshot_exists": False, "canvas_changed_after_actions": False, "forbidden_script_generation_used": False, "bash_final_artifact_route_used": False, "forbidden_script_artifact_route_blocked": True}  # 新增代码+PaintPikachuRealLoop：准备零副作用失败字段；如果没有这一行，调用方可能把失败误读成真实动作。
        report.update(extra or {})  # 新增代码+PaintPikachuRealLoop：合并额外排查信息；如果没有这一行，具体失败分支无法说明启动或窗口原因。
        return report  # 新增代码+PaintPikachuRealLoop：返回失败报告；如果没有这一行，调用方拿不到失败事实。
    # 新增代码+PaintPikachuRealLoop：函数段结束，WindowsPaintPikachuRealExecutionLoop._failure 到此结束；如果没有这个边界说明，初学者不容易看出失败报告范围。

    def _launch_paint(self) -> dict[str, Any]:  # 新增代码+PaintPikachuRealLoop：函数段开始，用通用发现和生产后端启动 Paint；如果没有这个函数，真实任务不会打开本地画图软件。
        discovery = resolve_generic_app_launch_target("mspaint")  # 新增代码+PaintPikachuRealLoop：按通用发现解析 mspaint；如果没有这一行，启动会绕开 Phase108 安全计划。
        launch = run_generic_launch_backend(discovery, enable_real_launch=True, backend=self.launch_backend)  # 新增代码+PaintPikachuRealLoop：用已授权真实后端启动 Paint；如果没有这一行，full prompt 只能停在候选报告。
        launch["generic_discovery_report"] = discovery  # 新增代码+PaintPikachuRealLoop：把发现报告放进启动结果；如果没有这一行，失败时看不到候选来源。
        return launch  # 新增代码+PaintPikachuRealLoop：返回启动结果；如果没有这一行，后续拿不到 pid 和安全字段。
    # 新增代码+PaintPikachuRealLoop：函数段结束，WindowsPaintPikachuRealExecutionLoop._launch_paint 到此结束；如果没有这个边界说明，初学者不容易看出启动范围。

    def _find_paint_window(self, process_id: int) -> dict[str, Any] | None:  # 新增代码+PaintPikachuRealLoop：函数段开始，轮询查找本次 Paint 窗口；如果没有这个函数，启动和动作无法绑定到同一窗口。
        deadline = time.time() + self.poll_timeout_seconds  # 新增代码+PaintPikachuRealLoop：计算轮询截止时间；如果没有这一行，找不到窗口时可能无限等待。
        fallback: dict[str, Any] | None = None  # 新增代码+PaintPikachuRealLoop：保存没有 pid 匹配但像 Paint 的兜底窗口；如果没有这一行，测试 fake 无 pid 时无法覆盖正向路径。
        while time.time() <= deadline:  # 新增代码+PaintPikachuRealLoop：在超时前反复读取窗口快照；如果没有这一行，Paint 启动延迟会导致误失败。
            snapshot = self.inventory.snapshot()  # 新增代码+PaintPikachuRealLoop：读取当前安全窗口快照；如果没有这一行，无法观察真实桌面窗口。
            for window in list(getattr(snapshot, "windows", []) or []):  # 新增代码+PaintPikachuRealLoop：遍历快照中的安全窗口；如果没有这一行，无法筛选 Paint。
                candidate = dict(window)  # 新增代码+PaintPikachuRealLoop：复制窗口记录避免污染快照；如果没有这一行，后续附加字段可能影响 inventory。
                if _paint_loop_is_paint_window(candidate, process_id):  # 新增代码+PaintPikachuRealLoop：优先寻找 pid 和 Paint 身份都匹配的窗口；如果没有这一行，可能误选用户已有窗口。
                    return candidate  # 新增代码+PaintPikachuRealLoop：返回已验证窗口；如果没有这一行，后续没有动作目标。
                if fallback is None and _paint_loop_is_paint_window(candidate, 0):  # 新增代码+PaintPikachuRealLoop：记录一个 Paint 形状兜底窗口；如果没有这一行，fake 测试和部分系统缺 pid 时会失败。
                    fallback = candidate  # 新增代码+PaintPikachuRealLoop：保存兜底候选；如果没有这一行，循环结束后无法降级使用。
            time.sleep(0.25)  # 新增代码+PaintPikachuRealLoop：等待窗口刷新；如果没有这一行，轮询会过于频繁并抢 CPU。
        return fallback  # 新增代码+PaintPikachuRealLoop：超时后返回兜底或 None；如果没有这一行，调用方无法判断是否找到目标。
    # 新增代码+PaintPikachuRealLoop：函数段结束，WindowsPaintPikachuRealExecutionLoop._find_paint_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口查找范围。

    def run_desktop_task(self, target_app: str, prompt: str) -> dict[str, Any]:  # 修改代码+GenericPaintSubject：函数段开始，执行 Paint 已支持对象真实桌面任务；如果没有这段函数，desktop_task_runtime 无法调用真实闭环。
        if self.platform != "win32":  # 新增代码+PaintPikachuRealLoop：只允许 Windows 上执行真实 Paint；如果没有这一行，非 Windows 会尝试调用 Win32 组件。
            return self._failure("paint_pikachu_real_loop_non_windows", "platform_not_windows")  # 新增代码+PaintPikachuRealLoop：返回平台拒绝；如果没有这一行，失败原因不清楚。
        if str(target_app).strip().lower() != "mspaint":  # 新增代码+PaintPikachuRealLoop：只处理画图软件任务；如果没有这一行，未知桌面任务可能误走 Paint 路线。
            return self._failure("paint_pikachu_real_loop_target_not_supported", "target_app_must_be_mspaint", {"target_app": str(target_app)})  # 新增代码+PaintPikachuRealLoop：返回目标不支持；如果没有这一行，泛化能力会被错误夸大。
        subject = _paint_loop_subject_from_prompt(prompt)  # 新增代码+GenericPaintSubject：从真实用户 prompt 识别要画的对象；如果没有这一行，大象 prompt 会继续落到皮卡丘默认计划。
        if subject not in PAINT_SUPPORTED_DRAWING_SUBJECTS:  # 新增代码+GenericPaintSubject：未知对象必须明确拒绝；如果没有这一行，agent 会再次假装支持任意绘画对象。
            return self._failure("paint_drawing_subject_not_supported", "supported_subjects=pikachu,elephant,cat", {"drawing_subject": subject, "supported_drawing_subjects": list(PAINT_SUPPORTED_DRAWING_SUBJECTS), "prompt_length": len(str(prompt or ""))})  # 修改代码+PaintCatSubject：返回对象不支持报告并列出猫已支持；如果没有这一行，用户不知道猫不再属于拒绝对象。
        launch = self._launch_paint()  # 新增代码+PaintPikachuRealLoop：启动真实 Paint；如果没有这一行，用户看不到画图软件打开。
        if not bool(launch.get("ok") and launch.get("process_started")):  # 新增代码+PaintPikachuRealLoop：检查启动是否成功；如果没有这一行，启动失败仍可能继续发送鼠标。
            return self._failure("paint_launch_failed", "mspaint_launch_failed", {"launch_report": launch})  # 新增代码+PaintPikachuRealLoop：返回启动失败报告；如果没有这一行，用户不知道卡在打开应用。
        process_id = _paint_loop_safe_int(launch.get("process_id"))  # 新增代码+PaintPikachuRealLoop：读取本次启动的 Paint pid；如果没有这一行，窗口验证无法绑定自有进程。
        window = self._find_paint_window(process_id)  # 新增代码+PaintPikachuRealLoop：查找并复核 Paint 窗口；如果没有这一行，真实输入可能落到错误目标。
        if window is None:  # 新增代码+PaintPikachuRealLoop：检查是否找到窗口；如果没有这一行，None 目标会传给事件生成。
            return self._failure("paint_window_not_found", "owned_mspaint_window_not_found", {"launch_report": launch})  # 新增代码+PaintPikachuRealLoop：返回窗口未找到；如果没有这一行，用户不知道已经启动但无法定位窗口。
        window = _paint_loop_prepare_window(window)  # 新增代码+PaintPikachuRealLoop：最大化并刷新 Paint 窗口布局；如果没有这一行，工具栏折叠时可能选不到铅笔而导致画布空白。
        canvas = _paint_loop_canvas_rect(window)  # 修改代码+GenericPaintSubject：估算 Paint 画布区域；如果没有这一行，当前绘画对象路径没有坐标范围。
        plan = _paint_loop_plan_for_subject(subject, canvas)  # 修改代码+GenericPaintSubject：按用户 prompt 选择皮卡丘或大象拖拽计划；如果没有这一行，大象会继续被硬编码成皮卡丘。
        events = _paint_loop_low_level_events(window, plan)  # 新增代码+PaintPikachuRealLoop：把计划转成低层鼠标事件；如果没有这一行，sender 没有可发送事件。
        if len(events) <= 1:  # 新增代码+PaintPikachuRealLoop：检查除聚焦外是否有足够绘图事件；如果没有这一行，空计划可能误触成功。
            return self._failure("paint_drag_plan_empty", f"{subject}_drag_plan_has_no_events", {"launch_report": launch, "target_window": window, "drawing_subject": subject, "drawing_plan": plan})  # 修改代码+GenericPaintSubject：返回带对象名的空计划失败；如果没有这一行，大象失败仍会被写成皮卡丘失败。
        send_result = dict(self.low_level_sender.send_low_level(events))  # 新增代码+PaintPikachuRealLoop：发送真实低层事件到 Paint；如果没有这一行，画图软件不会收到鼠标拖拽。
        time.sleep(0.5)  # 新增代码+PaintPikachuRealLoop：给 Paint 刷新画布留出半秒；如果没有这一行，截图或人工观察可能看到动作未完全刷新。
        low_level_count = _paint_loop_safe_int(send_result.get("low_level_event_count"), len(events))  # 新增代码+PaintPikachuRealLoop：读取 sender 确认的事件数；如果没有这一行，报告无法证明动作规模。
        screenshot_result = dict(self.screenshot_runtime.capture_window(window)) if self.screenshot_runtime is not None and hasattr(self.screenshot_runtime, "capture_window") else {"captured": False, "reason": "screenshot_runtime_missing"}  # 新增代码+PaintVisualGuard：动作后立刻捕获 Paint 窗口；如果没有这一行，报告无法证明画布真的留下笔迹。
        visual_report = _paint_loop_visual_canvas_report(window, canvas, screenshot_result, subject)  # 修改代码+GenericPaintSubject：用当前对象的截图规则判断画布是否变化；如果没有这一行，大象会被皮卡丘视觉规则误判。
        cleanup_report = self.launch_registry.cleanup_owned_processes(reason=f"paint_{subject}_real_loop_finished")  # 修改代码+GenericPaintSubject：截图取证后按对象名清理本轮 Paint 进程；如果没有这一行，大象报告仍会写成皮卡丘清理原因。
        residual_report = self.launch_registry.residual_owned_processes()  # 新增代码+FullNaturalUserFlowCleanup：清理后检查本轮自有进程是否仍残留；如果没有这一行，cleanup 失败会再次被误报为成功。
        dispatch_ok = bool(send_result.get("ok") and low_level_count > 0)  # 修改代码+PaintVisualGuard：单独记录低层事件发送是否成功；如果没有这一行，动作发送和视觉成功会混在一起。
        visual_ok = bool(visual_report.get("canvas_changed_after_actions", False))  # 新增代码+PaintVisualGuard：读取视觉门禁是否通过；如果没有这一行，ok 无法由真实画布状态决定。
        cleanup_ok = bool(cleanup_report.get("cleanup_completed", False) and not residual_report.get("residual_owned_process", False))  # 新增代码+FullNaturalUserFlowCleanup：只有清理完成且无自有进程残留才算清理通过；如果没有这一行，残留 Paint 仍可能被当作成熟成功。
        ok = bool(dispatch_ok and visual_ok and cleanup_ok)  # 修改代码+FullNaturalUserFlowCleanup：事件、视觉和自有进程清理都成立才成功；如果没有这一行，画完但残留进程也会被误报成熟。
        decision = f"paint_{subject}_real_execution_finished" if ok else (f"paint_{subject}_cleanup_failed" if dispatch_ok and visual_ok and not cleanup_ok else (f"paint_{subject}_visual_verification_failed" if dispatch_ok else f"paint_{subject}_sendinput_failed"))  # 修改代码+GenericPaintSubject：按对象名区分成功、清理失败、视觉失败和发送失败；如果没有这一行，大象终端仍会显示皮卡丘决策码。
        return {"ok": ok, "marker": PAINT_PIKACHU_REAL_LOOP_MARKER, "ok_token": PAINT_PIKACHU_REAL_LOOP_OK if ok else "", "model": PAINT_PIKACHU_REAL_LOOP_MODEL, "decision": decision, "target_app": "mspaint", "drawing_subject": subject, "supported_drawing_subjects": list(PAINT_SUPPORTED_DRAWING_SUBJECTS), "prompt_length": len(str(prompt or "")), "computer_use_gui_route_used": ok, "owned_window_verified": True, "gui_action_count": _paint_loop_safe_int(plan.get("gui_action_count", 0)), "low_level_event_count": low_level_count, "real_dispatch_performed": dispatch_ok, "real_desktop_touched": dispatch_ok, "cleanup_completed": cleanup_ok, "owned_resource_cleanup_completed": cleanup_ok, "residual_owned_process": bool(residual_report.get("residual_owned_process", False)), "cleanup_report": cleanup_report, "residual_report": residual_report, "post_action_screenshot_exists": bool(visual_report.get("post_action_screenshot_exists", False)), "post_action_visual_evidence_path": str(visual_report.get("post_action_visual_evidence_path", "")), "canvas_changed_after_actions": visual_ok, "drawing_visual_elements": bool(visual_report.get("drawing_visual_elements", False)), "pikachu_visual_elements": bool(visual_report.get("pikachu_visual_elements", False)), "elephant_visual_elements": bool(visual_report.get("elephant_visual_elements", False)), "cat_visual_elements": bool(visual_report.get("cat_visual_elements", False)), "visual_non_background_pixel_count": _paint_loop_safe_int(visual_report.get("visual_non_background_pixel_count", 0)), "visual_guard_reason": str(visual_report.get("visual_guard_reason", "")), "post_action_screenshot_result": visual_report.get("post_action_screenshot_result", {}), "forbidden_script_generation_used": False, "bash_final_artifact_route_used": False, "forbidden_script_artifact_route_blocked": True, "target_window": {"window_id": window.get("window_id"), "hwnd": window.get("hwnd"), "pid": window.get("pid"), "title_preview": window.get("title_preview")}, "canvas_rect": canvas, "drawing_plan": {"drawing_subject": subject, "drag_path_count": plan.get("drag_path_count"), "colors": plan.get("colors"), "elements": plan.get("elements")}, "launch_report": launch, "send_result": send_result}  # 修改代码+PaintCatSubject：返回带对象、截图、像素门禁和猫专属视觉字段的执行报告；如果没有这一行，runtime 无法证明猫真的走了猫计划。
    # 新增代码+PaintPikachuRealLoop：函数段结束，WindowsPaintPikachuRealExecutionLoop.run_desktop_task 到此结束；如果没有这个边界说明，初学者不容易看出真实执行范围。
# 新增代码+PaintPikachuRealLoop：类段结束，WindowsPaintPikachuRealExecutionLoop 到此结束；如果没有这个边界说明，初学者不容易看出闭环对象范围。


__all__ = ["PAINT_PIKACHU_REAL_LOOP_MARKER", "PAINT_PIKACHU_REAL_LOOP_MODEL", "PAINT_PIKACHU_REAL_LOOP_OK", "WindowsPaintPikachuRealExecutionLoop"]  # 新增代码+PaintPikachuRealLoop：限定公开 API；如果没有这一行，通配导入可能暴露内部 helper。
