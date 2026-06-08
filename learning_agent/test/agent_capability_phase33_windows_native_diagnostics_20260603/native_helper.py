"""Windows Computer Use 只读 native 观察 helper。"""  # 新增代码+Phase32WindowsNativeHelper: 说明本文件负责只读截图和窗口文本桥接；如果没有这个文件，Phase32 无法把真实 native 观察能力接入 evidence 链。
from __future__ import annotations  # 新增代码+Phase32WindowsNativeHelper: 启用延迟类型解析；如果没有这行代码，旧运行路径下前向类型标注更容易出错。
import struct  # 新增代码+Phase32WindowsNativeHelper: 生成 BMP 文件头需要二进制打包；如果没有这行代码，Win32 截图字节无法保存成可打开图片。
import sys  # 新增代码+Phase32WindowsNativeHelper: 判断当前平台是否为 Windows；如果没有这行代码，非 Windows 环境可能误调用 Win32 API。
from dataclasses import dataclass  # 新增代码+Phase32WindowsNativeHelper: 使用 dataclass 表达 provider 结果；如果没有这行代码，截图和文本结果会变成松散 dict。
from typing import Any  # 新增代码+Phase32WindowsNativeHelper: 标注窗口 dict 和 provider 状态的通用 JSON 类型；如果没有这行代码，接口边界不清楚。

try:  # 新增代码+Phase32WindowsNativeHelper: 包运行模式下导入窗口观察 payload；如果没有这行代码，helper 无法复用 Phase29 evidence 合同。
    from learning_agent.computer_use.helper_client import WindowObservationPayload  # 新增代码+Phase32WindowsNativeHelper: 导入统一观察 payload；如果没有这行代码，Windows 后端不能直接保存 native helper 结果。
    from learning_agent.computer_use.native_diagnostics import WindowsNativeObservationDiagnostics  # 新增代码+Phase33WindowsNativeDiagnostics: 导入 native provider 诊断构建器；如果没有这行代码，helper.status 无法解释 WGC/UIA 与 fallback 差距。
except ModuleNotFoundError as error:  # 新增代码+Phase32WindowsNativeHelper: 兼容 start_oauth_agent.bat 脚本模式；如果没有这行代码，直接脚本运行可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.helper_client", "learning_agent.computer_use.native_diagnostics"}:  # 修改代码+Phase33WindowsNativeDiagnostics: 允许 native diagnostics 在脚本模式下 fallback；如果没有这行代码，bat 入口可能因新模块路径缺失而失败。
        raise  # 新增代码+Phase32WindowsNativeHelper: 重新抛出非目标导入错误；如果没有这行代码，排查内部 bug 会很困难。
    from computer_use.helper_client import WindowObservationPayload  # 新增代码+Phase32WindowsNativeHelper: 脚本模式下从本地包导入 payload；如果没有这行代码，bat 入口无法加载 native helper。
    from computer_use.native_diagnostics import WindowsNativeObservationDiagnostics  # 新增代码+Phase33WindowsNativeDiagnostics: 脚本模式下导入诊断构建器；如果没有这行代码，start_oauth_agent.bat 无法显示 Phase33 diagnostics。


@dataclass(frozen=True)  # 新增代码+Phase32WindowsNativeHelper: 让截图结果不可变；如果没有这行代码，证据落盘前可能被调用方无意改写。
class NativeWindowCaptureResult:  # 新增代码+Phase32WindowsNativeHelper: 定义 native 截图 provider 的返回结构；如果没有这个类，截图字段会散落在多个 dict 中。
    captured: bool = False  # 新增代码+Phase32WindowsNativeHelper: 标记是否真的捕获截图；如果没有这行代码，调用方无法区分失败和空截图。
    screenshot_bytes: bytes = b""  # 新增代码+Phase32WindowsNativeHelper: 保存截图字节；如果没有这行代码，evidence store 没有图片内容可写。
    screenshot_format: str = ""  # 新增代码+Phase32WindowsNativeHelper: 保存截图格式；如果没有这行代码，图片文件后缀不稳定。
    screenshot_width: int = 0  # 新增代码+Phase32WindowsNativeHelper: 保存截图宽度；如果没有这行代码，状态无法说明截图尺寸。
    screenshot_height: int = 0  # 新增代码+Phase32WindowsNativeHelper: 保存截图高度；如果没有这行代码，状态无法说明截图尺寸。
    backend: str = ""  # 新增代码+Phase32WindowsNativeHelper: 保存截图后端名称；如果没有这行代码，审计时不知道截图来自 GDI 还是 fake provider。
    reason: str = ""  # 新增代码+Phase32WindowsNativeHelper: 保存截图成功或失败原因；如果没有这行代码，用户不知道为什么没有截图。


@dataclass(frozen=True)  # 新增代码+Phase32WindowsNativeHelper: 让文本结果不可变；如果没有这行代码，文本摘要在过滤前可能被无意修改。
class NativeWindowTextResult:  # 新增代码+Phase32WindowsNativeHelper: 定义 native 文本 provider 的返回结构；如果没有这个类，文本字段会变成松散 dict。
    captured: bool = False  # 新增代码+Phase32WindowsNativeHelper: 标记是否读到窗口文本；如果没有这行代码，调用方无法区分空文本和失败。
    accessibility_text: str = ""  # 新增代码+Phase32WindowsNativeHelper: 保存原始窗口文本；如果没有这行代码，evidence store 无法生成可访问性摘要。
    focused_element: str = ""  # 新增代码+Phase32WindowsNativeHelper: 保存焦点或主标题摘要；如果没有这行代码，模型缺少焦点上下文。
    selected_text: str = ""  # 新增代码+Phase32WindowsNativeHelper: 保存选中文本摘要占位；如果没有这行代码，payload 合同字段不完整。
    document_text: str = ""  # 新增代码+Phase32WindowsNativeHelper: 保存文档级文本摘要；如果没有这行代码，窗口正文上下文无法进入 evidence。
    backend: str = ""  # 新增代码+Phase32WindowsNativeHelper: 保存文本后端名称；如果没有这行代码，审计时不知道文本来自 Win32 还是 UIA。
    reason: str = ""  # 新增代码+Phase32WindowsNativeHelper: 保存文本读取说明；如果没有这行代码，用户不知道文本为空的原因。


def parse_hwnd_from_window(window: dict[str, Any]) -> int:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，解析窗口句柄；如果没有这段函数，native helper 无法把 Phase28 window_id 转成 Win32 hwnd。
    raw_hwnd = window.get("hwnd", window.get("window_handle", 0))  # 新增代码+Phase32WindowsNativeHelper: 优先读取原始 hwnd 字段；如果没有这行代码，静态/真实 raw 窗口不能直接观察。
    if raw_hwnd:  # 新增代码+Phase32WindowsNativeHelper: 检查是否已经有 hwnd 数值；如果没有这行代码，所有窗口都只能走字符串解析。
        try:  # 新增代码+Phase32WindowsNativeHelper: 捕获坏 hwnd 值；如果没有这行代码，坏数据会让 helper 崩溃。
            return int(raw_hwnd)  # 新增代码+Phase32WindowsNativeHelper: 返回整数 hwnd；如果没有这行代码，Win32 API 无法接收句柄。
        except (TypeError, ValueError):  # 新增代码+Phase32WindowsNativeHelper: 处理非数字 hwnd；如果没有这行代码，异常会冒泡到后端。
            return 0  # 新增代码+Phase32WindowsNativeHelper: 坏 hwnd 返回 0 表示无效；如果没有这行代码，调用方无法安全拒绝。
    window_id = str(window.get("window_id", ""))  # 新增代码+Phase32WindowsNativeHelper: 读取 Phase28 标准 window_id；如果没有这行代码，helper 无法复用 `hwnd:123` 合同。
    if not window_id.startswith("hwnd:"):  # 新增代码+Phase32WindowsNativeHelper: 只接受 hwnd 前缀；如果没有这行代码，任意字符串可能被误当句柄。
        return 0  # 新增代码+Phase32WindowsNativeHelper: 非 hwnd id 返回无效；如果没有这行代码，坏窗口可能触发系统 API。
    try:  # 新增代码+Phase32WindowsNativeHelper: 捕获 hwnd 后缀解析错误；如果没有这行代码，`hwnd:abc` 会导致异常。
        return int(window_id.split(":", 1)[1])  # 新增代码+Phase32WindowsNativeHelper: 解析 `hwnd:<数字>` 后缀；如果没有这行代码，标准窗口引用无法进入 native helper。
    except (IndexError, ValueError):  # 新增代码+Phase32WindowsNativeHelper: 处理缺后缀或非数字后缀；如果没有这行代码，坏 window_id 会崩溃。
        return 0  # 新增代码+Phase32WindowsNativeHelper: 解析失败返回无效 hwnd；如果没有这行代码，调用方无法安全兜底。
# 新增代码+Phase32WindowsNativeHelper: 函数段结束，parse_hwnd_from_window 到此结束；如果没有这个边界说明，读者不容易看出 hwnd 解析范围。


def _provider_status(provider: Any) -> dict[str, Any]:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，安全读取 provider 状态；如果没有这段函数，helper.status 会重复写 hasattr 逻辑。
    if hasattr(provider, "status"):  # 新增代码+Phase32WindowsNativeHelper: 检查 provider 是否提供状态函数；如果没有这行代码，调用不存在方法会崩溃。
        status = provider.status()  # 新增代码+Phase32WindowsNativeHelper: 调用 provider 状态；如果没有这行代码，用户看不到真实截图/文本后端边界。
        return dict(status) if isinstance(status, dict) else {}  # 新增代码+Phase32WindowsNativeHelper: 确保状态是字典；如果没有这行代码，异常返回类型会污染状态页。
    return {}  # 新增代码+Phase32WindowsNativeHelper: 没有 status 时返回空状态；如果没有这行代码，调用方需要自己兜底。
# 新增代码+Phase32WindowsNativeHelper: 函数段结束，_provider_status 到此结束；如果没有这个边界说明，读者不容易看出 provider 状态读取范围。


class Win32GdiWindowCaptureProvider:  # 新增代码+Phase32WindowsNativeHelper: 定义 Win32 GDI 只读截图 provider；如果没有这个类，native helper 无法在真实 Windows 上尝试截图。
    def __init__(self, platform: str | None = None) -> None:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，初始化截图 provider 平台；如果没有这段函数，测试无法注入非 Windows 平台。
        self.platform = platform or sys.platform  # 新增代码+Phase32WindowsNativeHelper: 保存平台字符串；如果没有这行代码，provider.status 和 capture 无法稳定判断环境。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，Win32GdiWindowCaptureProvider.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，返回截图 provider 状态；如果没有这段函数，computer_status 看不到截图后端。
        return {"backend": "win32_gdi_printwindow", "available": self.platform == "win32", "reason": "Phase32 使用 Win32 GDI PrintWindow/BitBlt 只读截图；失败时会诚实返回未捕获。"}  # 新增代码+Phase32WindowsNativeHelper: 返回截图能力边界；如果没有这行代码，用户可能误以为截图永远可用。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，Win32GdiWindowCaptureProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态函数范围。

    def capture_window(self, hwnd: int) -> NativeWindowCaptureResult:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，捕获指定窗口 BMP；如果没有这段函数，真实 Windows helper 没有截图来源。
        if self.platform != "win32":  # 新增代码+Phase32WindowsNativeHelper: 非 Windows 平台拒绝调用；如果没有这行代码，跨平台测试会尝试导入 windll。
            return NativeWindowCaptureResult(backend="win32_gdi_printwindow", reason="当前平台不是 Windows，未调用截图 API。")  # 新增代码+Phase32WindowsNativeHelper: 返回平台拒绝原因；如果没有这行代码，用户不知道为何没有截图。
        if int(hwnd or 0) <= 0:  # 新增代码+Phase32WindowsNativeHelper: 检查 hwnd 是否有效；如果没有这行代码，0 句柄可能传入系统 API。
            return NativeWindowCaptureResult(backend="win32_gdi_printwindow", reason="窗口句柄无效，未截图。")  # 新增代码+Phase32WindowsNativeHelper: 返回坏句柄原因；如果没有这行代码，错误目标不易排查。
        try:  # 新增代码+Phase32WindowsNativeHelper: 包住真实 Win32 调用；如果没有这行代码，截图失败会拖垮整个 observe。
            return self._capture_window_bmp(int(hwnd))  # 新增代码+Phase32WindowsNativeHelper: 调用真实 BMP 捕获实现；如果没有这行代码，capture_window 只有空壳。
        except Exception as error:  # 新增代码+Phase32WindowsNativeHelper: 捕获系统 API 异常；如果没有这行代码，桌面权限或窗口状态异常会中断 agent。
            return NativeWindowCaptureResult(backend="win32_gdi_printwindow", reason=f"Win32 截图失败：{type(error).__name__}")  # 新增代码+Phase32WindowsNativeHelper: 返回异常类型但不泄露本地细节；如果没有这行代码，用户只看到崩溃。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，Win32GdiWindowCaptureProvider.capture_window 到此结束；如果没有这个边界说明，读者不容易看出截图入口范围。

    def _capture_window_bmp(self, hwnd: int) -> NativeWindowCaptureResult:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，用 GDI 捕获窗口 BMP；如果没有这段函数，截图 provider 无法产生真实图片字节。
        import ctypes  # 新增代码+Phase32WindowsNativeHelper: 延迟导入 ctypes；如果没有这行代码，无法调用 user32/gdi32。
        from ctypes import wintypes  # 新增代码+Phase32WindowsNativeHelper: 导入 Win32 类型；如果没有这行代码，RECT 等结构需要手写。
        user32 = ctypes.windll.user32  # 新增代码+Phase32WindowsNativeHelper: 获取 user32 API；如果没有这行代码，无法获取窗口 DC 或矩形。
        gdi32 = ctypes.windll.gdi32  # 新增代码+Phase32WindowsNativeHelper: 获取 gdi32 API；如果没有这行代码，无法创建位图和提取像素。
        rect = wintypes.RECT()  # 新增代码+Phase32WindowsNativeHelper: 创建窗口矩形结构；如果没有这行代码，无法读取窗口尺寸。
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):  # 新增代码+Phase32WindowsNativeHelper: 读取窗口屏幕矩形；如果没有这行代码，截图不知道宽高。
            return NativeWindowCaptureResult(backend="win32_gdi_printwindow", reason="GetWindowRect 失败，未截图。")  # 新增代码+Phase32WindowsNativeHelper: 返回矩形读取失败；如果没有这行代码，后续会用无效尺寸。
        width = max(0, int(rect.right) - int(rect.left))  # 新增代码+Phase32WindowsNativeHelper: 计算截图宽度；如果没有这行代码，位图宽度可能为负。
        height = max(0, int(rect.bottom) - int(rect.top))  # 新增代码+Phase32WindowsNativeHelper: 计算截图高度；如果没有这行代码，位图高度可能为负。
        if width <= 0 or height <= 0:  # 新增代码+Phase32WindowsNativeHelper: 检查窗口是否有有效尺寸；如果没有这行代码，零尺寸窗口会导致 GDI 失败。
            return NativeWindowCaptureResult(backend="win32_gdi_printwindow", reason="窗口尺寸无效，未截图。")  # 新增代码+Phase32WindowsNativeHelper: 返回尺寸无效原因；如果没有这行代码，用户不知道为何无截图。
        hdc_window = user32.GetWindowDC(hwnd)  # 新增代码+Phase32WindowsNativeHelper: 获取窗口设备上下文；如果没有这行代码，无法从窗口读取像素。
        if not hdc_window:  # 新增代码+Phase32WindowsNativeHelper: 检查 DC 是否获取成功；如果没有这行代码，后续 GDI 调用会失败。
            return NativeWindowCaptureResult(backend="win32_gdi_printwindow", reason="GetWindowDC 失败，未截图。")  # 新增代码+Phase32WindowsNativeHelper: 返回 DC 失败原因；如果没有这行代码，错误不可见。
        hdc_memory = gdi32.CreateCompatibleDC(hdc_window)  # 新增代码+Phase32WindowsNativeHelper: 创建内存 DC；如果没有这行代码，PrintWindow 没有绘制目标。
        hbitmap = gdi32.CreateCompatibleBitmap(hdc_window, width, height)  # 新增代码+Phase32WindowsNativeHelper: 创建兼容位图；如果没有这行代码，窗口像素没有保存容器。
        old_object = gdi32.SelectObject(hdc_memory, hbitmap)  # 新增代码+Phase32WindowsNativeHelper: 把位图选入内存 DC；如果没有这行代码，PrintWindow 不会写入目标位图。
        try:  # 新增代码+Phase32WindowsNativeHelper: 确保 GDI 对象最终释放；如果没有这行代码，截图可能泄露系统句柄。
            printed = bool(user32.PrintWindow(hwnd, hdc_memory, 2))  # 新增代码+Phase32WindowsNativeHelper: 优先使用 PrintWindow 捕获窗口；如果没有这行代码，被遮挡窗口可能无法截图。
            if not printed:  # 新增代码+Phase32WindowsNativeHelper: 判断 PrintWindow 是否失败；如果没有这行代码，失败时不会尝试 BitBlt 兜底。
                gdi32.BitBlt(hdc_memory, 0, 0, width, height, hdc_window, 0, 0, 0x00CC0020)  # 新增代码+Phase32WindowsNativeHelper: 用 BitBlt 兜底读取可见像素；如果没有这行代码，部分窗口截图会空。
            bitmap_info = self._build_bitmap_info(width, height)  # 新增代码+Phase32WindowsNativeHelper: 构造 DIB 读取信息；如果没有这行代码，GetDIBits 不知道像素格式。
            pixel_buffer = ctypes.create_string_buffer(width * height * 4)  # 新增代码+Phase32WindowsNativeHelper: 创建 BGRA 像素缓冲；如果没有这行代码，GetDIBits 没有输出内存。
            lines = gdi32.GetDIBits(hdc_memory, hbitmap, 0, height, pixel_buffer, ctypes.byref(bitmap_info), 0)  # 新增代码+Phase32WindowsNativeHelper: 从 HBITMAP 读取像素；如果没有这行代码，无法生成 BMP 文件。
            if int(lines) <= 0:  # 新增代码+Phase32WindowsNativeHelper: 检查像素读取是否成功；如果没有这行代码，空 buffer 也会被当成截图。
                return NativeWindowCaptureResult(backend="win32_gdi_printwindow", reason="GetDIBits 失败，未截图。")  # 新增代码+Phase32WindowsNativeHelper: 返回 DIB 读取失败；如果没有这行代码，坏截图会进入证据。
            bmp_bytes = self._build_bmp_bytes(width, height, pixel_buffer.raw)  # 新增代码+Phase32WindowsNativeHelper: 组装 BMP 文件字节；如果没有这行代码，evidence store 保存的图片不可打开。
            return NativeWindowCaptureResult(captured=True, screenshot_bytes=bmp_bytes, screenshot_format="bmp", screenshot_width=width, screenshot_height=height, backend="win32_gdi_printwindow", reason="Win32 GDI 只读截图成功。")  # 新增代码+Phase32WindowsNativeHelper: 返回真实截图结果；如果没有这行代码，helper 无法证明截图成功。
        finally:  # 新增代码+Phase32WindowsNativeHelper: 进入 GDI 清理流程；如果没有这行代码，异常时系统资源可能泄露。
            if old_object:  # 新增代码+Phase32WindowsNativeHelper: 检查旧对象是否存在；如果没有这行代码，SelectObject 可能收到空句柄。
                gdi32.SelectObject(hdc_memory, old_object)  # 新增代码+Phase32WindowsNativeHelper: 恢复旧 GDI 对象；如果没有这行代码，内存 DC 状态会被污染。
            if hbitmap:  # 新增代码+Phase32WindowsNativeHelper: 检查位图句柄是否存在；如果没有这行代码，DeleteObject 可能处理空句柄。
                gdi32.DeleteObject(hbitmap)  # 新增代码+Phase32WindowsNativeHelper: 删除位图对象；如果没有这行代码，频繁截图会泄露 GDI 对象。
            if hdc_memory:  # 新增代码+Phase32WindowsNativeHelper: 检查内存 DC 是否存在；如果没有这行代码，DeleteDC 可能处理空句柄。
                gdi32.DeleteDC(hdc_memory)  # 新增代码+Phase32WindowsNativeHelper: 删除内存 DC；如果没有这行代码，系统资源会泄露。
            user32.ReleaseDC(hwnd, hdc_window)  # 新增代码+Phase32WindowsNativeHelper: 释放窗口 DC；如果没有这行代码，窗口 DC 会泄露。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，Win32GdiWindowCaptureProvider._capture_window_bmp 到此结束；如果没有这个边界说明，读者不容易看出 GDI 截图范围。

    def _build_bitmap_info(self, width: int, height: int) -> Any:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，构造 BITMAPINFO；如果没有这段函数，GetDIBits 没有像素格式说明。
        import ctypes  # 新增代码+Phase32WindowsNativeHelper: 导入 ctypes 定义结构；如果没有这行代码，无法声明 Win32 结构体。
        class BitmapInfoHeader(ctypes.Structure):  # 新增代码+Phase32WindowsNativeHelper: 定义 BITMAPINFOHEADER 结构；如果没有这个类，GetDIBits 参数不完整。
            _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32), ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16), ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32), ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_int32), ("biYPelsPerMeter", ctypes.c_int32), ("biClrUsed", ctypes.c_uint32), ("biClrImportant", ctypes.c_uint32)]  # 新增代码+Phase32WindowsNativeHelper: 声明位图头字段；如果没有这行代码，ctypes 无法按 Win32 布局传参。
        class BitmapInfo(ctypes.Structure):  # 新增代码+Phase32WindowsNativeHelper: 定义 BITMAPINFO 结构；如果没有这个类，GetDIBits 不能接收完整信息。
            _fields_ = [("bmiHeader", BitmapInfoHeader), ("bmiColors", ctypes.c_uint32 * 3)]  # 新增代码+Phase32WindowsNativeHelper: 声明 header 和颜色表占位；如果没有这行代码，结构大小不符合预期。
        bitmap_info = BitmapInfo()  # 新增代码+Phase32WindowsNativeHelper: 创建 BITMAPINFO 实例；如果没有这行代码，后续字段没有容器。
        bitmap_info.bmiHeader.biSize = ctypes.sizeof(BitmapInfoHeader)  # 新增代码+Phase32WindowsNativeHelper: 写入 header 大小；如果没有这行代码，GetDIBits 会拒绝结构。
        bitmap_info.bmiHeader.biWidth = int(width)  # 新增代码+Phase32WindowsNativeHelper: 写入位图宽度；如果没有这行代码，像素读取宽度不明。
        bitmap_info.bmiHeader.biHeight = -int(height)  # 新增代码+Phase32WindowsNativeHelper: 使用负高度生成 top-down BMP；如果没有这行代码，截图可能上下颠倒。
        bitmap_info.bmiHeader.biPlanes = 1  # 新增代码+Phase32WindowsNativeHelper: 写入固定 plane 数；如果没有这行代码，Win32 位图格式无效。
        bitmap_info.bmiHeader.biBitCount = 32  # 新增代码+Phase32WindowsNativeHelper: 使用 32 位 BGRA 像素；如果没有这行代码，像素缓冲大小不明确。
        bitmap_info.bmiHeader.biCompression = 0  # 新增代码+Phase32WindowsNativeHelper: 使用 BI_RGB 无压缩；如果没有这行代码，BMP 解码会失败。
        bitmap_info.bmiHeader.biSizeImage = int(width) * int(height) * 4  # 新增代码+Phase32WindowsNativeHelper: 写入像素数据大小；如果没有这行代码，GetDIBits 可能无法正确填充。
        return bitmap_info  # 新增代码+Phase32WindowsNativeHelper: 返回结构供 GetDIBits 使用；如果没有这行代码，调用方拿不到 bitmap info。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，Win32GdiWindowCaptureProvider._build_bitmap_info 到此结束；如果没有这个边界说明，读者不容易看出 BITMAPINFO 构造范围。

    def _build_bmp_bytes(self, width: int, height: int, pixels: bytes) -> bytes:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，组装 BMP 文件字节；如果没有这段函数，像素数据不是标准图片文件。
        header_size = 14 + 40  # 新增代码+Phase32WindowsNativeHelper: BMP 文件头 14 字节加 DIB 头 40 字节；如果没有这行代码，像素偏移会错误。
        file_size = header_size + len(pixels)  # 新增代码+Phase32WindowsNativeHelper: 计算文件总大小；如果没有这行代码，BMP 文件头大小字段错误。
        file_header = b"BM" + struct.pack("<IHHI", file_size, 0, 0, header_size)  # 新增代码+Phase32WindowsNativeHelper: 构造 BMP 文件头；如果没有这行代码，图片查看器无法识别文件。
        dib_header = struct.pack("<IiiHHIIiiII", 40, int(width), -int(height), 1, 32, 0, len(pixels), 0, 0, 0, 0)  # 新增代码+Phase32WindowsNativeHelper: 构造 top-down 32 位 DIB 头；如果没有这行代码，像素尺寸和格式不可读。
        return file_header + dib_header + pixels  # 新增代码+Phase32WindowsNativeHelper: 返回完整 BMP 字节；如果没有这行代码，evidence store 无法保存可打开截图。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，Win32GdiWindowCaptureProvider._build_bmp_bytes 到此结束；如果没有这个边界说明，读者不容易看出 BMP 组装范围。


class Win32WindowTextProvider:  # 新增代码+Phase32WindowsNativeHelper: 定义 Win32 窗口文本 provider；如果没有这个类，native helper 只能截图不能返回文本摘要。
    def __init__(self, platform: str | None = None, max_child_windows: int = 40) -> None:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，初始化文本 provider；如果没有这段函数，测试无法控制平台和子窗口数量。
        self.platform = platform or sys.platform  # 新增代码+Phase32WindowsNativeHelper: 保存平台字符串；如果没有这行代码，provider 无法跨平台安全拒绝。
        self.max_child_windows = int(max_child_windows)  # 新增代码+Phase32WindowsNativeHelper: 限制子控件读取数量；如果没有这行代码，复杂窗口可能返回过多文本。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，Win32WindowTextProvider.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，返回文本 provider 状态；如果没有这段函数，状态页无法说明文本来源。
        return {"backend": "win32_window_text", "available": self.platform == "win32", "reason": "Phase32 先使用 Win32 标题/子控件文本 fallback；完整 UIAutomationClient 树读取留给后续阶段。"}  # 新增代码+Phase32WindowsNativeHelper: 返回文本能力边界；如果没有这行代码，用户可能误以为完整 UIA 已接入。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，Win32WindowTextProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态函数范围。

    def read_window_text(self, hwnd: int) -> NativeWindowTextResult:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，读取窗口标题和子控件文本；如果没有这段函数，native helper 没有文本摘要来源。
        if self.platform != "win32":  # 新增代码+Phase32WindowsNativeHelper: 非 Windows 平台拒绝读取；如果没有这行代码，跨平台测试会尝试 Win32 API。
            return NativeWindowTextResult(backend="win32_window_text", reason="当前平台不是 Windows，未读取窗口文本。")  # 新增代码+Phase32WindowsNativeHelper: 返回平台拒绝原因；如果没有这行代码，用户不知道为何无文本。
        if int(hwnd or 0) <= 0:  # 新增代码+Phase32WindowsNativeHelper: 检查 hwnd 是否有效；如果没有这行代码，0 句柄可能进入系统 API。
            return NativeWindowTextResult(backend="win32_window_text", reason="窗口句柄无效，未读取文本。")  # 新增代码+Phase32WindowsNativeHelper: 返回坏句柄原因；如果没有这行代码，错误不可见。
        try:  # 新增代码+Phase32WindowsNativeHelper: 包住真实 Win32 文本读取；如果没有这行代码，窗口消失时会中断 observe。
            return self._read_window_text(int(hwnd))  # 新增代码+Phase32WindowsNativeHelper: 调用真实读取实现；如果没有这行代码，read_window_text 只有空壳。
        except Exception as error:  # 新增代码+Phase32WindowsNativeHelper: 捕获系统 API 异常；如果没有这行代码，文本读取失败会让 agent 崩溃。
            return NativeWindowTextResult(backend="win32_window_text", reason=f"Win32 文本读取失败：{type(error).__name__}")  # 新增代码+Phase32WindowsNativeHelper: 返回异常类型；如果没有这行代码，用户只看到无结果。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，Win32WindowTextProvider.read_window_text 到此结束；如果没有这个边界说明，读者不容易看出文本入口范围。

    def _read_window_text(self, hwnd: int) -> NativeWindowTextResult:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，真实读取 Win32 窗口文本；如果没有这段函数，文本 provider 无法产生摘要。
        import ctypes  # 新增代码+Phase32WindowsNativeHelper: 延迟导入 ctypes；如果没有这行代码，无法调用 user32。
        from ctypes import wintypes  # 新增代码+Phase32WindowsNativeHelper: 导入 Win32 类型；如果没有这行代码，EnumChildWindows 回调签名无法定义。
        user32 = ctypes.windll.user32  # 新增代码+Phase32WindowsNativeHelper: 获取 user32 API；如果没有这行代码，窗口文本没有系统入口。
        lines: list[str] = []  # 新增代码+Phase32WindowsNativeHelper: 准备保存标题和控件文本；如果没有这行代码，读取结果没有容器。
        title = self._get_window_text(user32, hwnd)  # 新增代码+Phase32WindowsNativeHelper: 读取顶层窗口标题；如果没有这行代码，文本摘要缺少主窗口信息。
        if title:  # 新增代码+Phase32WindowsNativeHelper: 检查标题是否非空；如果没有这行代码，空标题会污染摘要。
            lines.append(f"title: {title}")  # 新增代码+Phase32WindowsNativeHelper: 保存标题行；如果没有这行代码，主窗口标题不会进入文本摘要。
        enum_child_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)  # 新增代码+Phase32WindowsNativeHelper: 定义子窗口枚举回调签名；如果没有这行代码，Python 函数不能传给 Win32。
        def collect_child(child_hwnd: Any, lparam: Any) -> bool:  # 新增代码+Phase32WindowsNativeHelper: 定义子控件回调；如果没有这段函数，无法读取按钮/输入框标题。
            if len(lines) >= self.max_child_windows:  # 新增代码+Phase32WindowsNativeHelper: 限制读取数量；如果没有这行代码，大窗口可能产生过多文本。
                return False  # 新增代码+Phase32WindowsNativeHelper: 达到上限时停止枚举；如果没有这行代码，回调会继续刷屏。
            child_text = self._get_window_text(user32, int(child_hwnd))  # 新增代码+Phase32WindowsNativeHelper: 读取子控件文本；如果没有这行代码，按钮/标签文本不会进入摘要。
            if child_text:  # 新增代码+Phase32WindowsNativeHelper: 检查子控件文本是否非空；如果没有这行代码，空行会污染摘要。
                lines.append(f"child: {child_text}")  # 新增代码+Phase32WindowsNativeHelper: 保存子控件文本；如果没有这行代码，控件摘要丢失。
            return True  # 新增代码+Phase32WindowsNativeHelper: 继续枚举后续子控件；如果没有这行代码，只能读第一个子控件。
        callback = enum_child_proc(collect_child)  # 新增代码+Phase32WindowsNativeHelper: 保存回调对象防止被回收；如果没有这行代码，Win32 回调可能崩溃。
        user32.EnumChildWindows(hwnd, callback, 0)  # 新增代码+Phase32WindowsNativeHelper: 枚举子窗口；如果没有这行代码，文本摘要只有顶层标题。
        text = "\n".join(lines)  # 新增代码+Phase32WindowsNativeHelper: 合并文本行为 UI 摘要；如果没有这行代码，payload 无法传递文本。
        captured = bool(text)  # 新增代码+Phase32WindowsNativeHelper: 判断是否读到任何文本；如果没有这行代码，调用方无法区分空结果。
        reason = "Win32 标题/子控件文本读取成功。" if captured else "窗口没有可读取的 Win32 文本。"  # 新增代码+Phase32WindowsNativeHelper: 生成可读说明；如果没有这行代码，空文本原因不清楚。
        return NativeWindowTextResult(captured=captured, accessibility_text=text, focused_element=title, selected_text="", document_text=text, backend="win32_window_text", reason=reason)  # 新增代码+Phase32WindowsNativeHelper: 返回文本读取结果；如果没有这行代码，helper 无法生成 payload。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，Win32WindowTextProvider._read_window_text 到此结束；如果没有这个边界说明，读者不容易看出真实读取范围。

    def _get_window_text(self, user32: Any, hwnd: int) -> str:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，读取单个窗口文本；如果没有这段函数，标题读取代码会重复。
        import ctypes  # 新增代码+Phase32WindowsNativeHelper: 导入 ctypes 创建缓冲区；如果没有这行代码，无法接收 Win32 字符串。
        length = max(0, int(user32.GetWindowTextLengthW(hwnd)))  # 新增代码+Phase32WindowsNativeHelper: 读取文本长度；如果没有这行代码，缓冲区大小不准确。
        if length <= 0:  # 新增代码+Phase32WindowsNativeHelper: 检查是否没有文本；如果没有这行代码，空控件仍会分配缓冲。
            return ""  # 新增代码+Phase32WindowsNativeHelper: 无文本返回空字符串；如果没有这行代码，调用方需要自己判断。
        buffer = ctypes.create_unicode_buffer(length + 1)  # 新增代码+Phase32WindowsNativeHelper: 创建 Unicode 缓冲；如果没有这行代码，GetWindowTextW 没有输出位置。
        user32.GetWindowTextW(hwnd, buffer, length + 1)  # 新增代码+Phase32WindowsNativeHelper: 读取窗口文本；如果没有这行代码，标题/控件文本为空。
        return str(buffer.value or "")  # 新增代码+Phase32WindowsNativeHelper: 返回 Python 字符串；如果没有这行代码，调用方拿不到文本。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，Win32WindowTextProvider._get_window_text 到此结束；如果没有这个边界说明，读者不容易看出单窗口文本读取范围。


class WindowsNativeWindowObservationHelper:  # 新增代码+Phase32WindowsNativeHelper: 定义 Windows native 只读观察 helper；如果没有这个类，Windows 后端无法统一调用截图和文本 provider。
    def __init__(self, capture_provider: Any | None = None, text_provider: Any | None = None, platform: str | None = None) -> None:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，初始化 native helper；如果没有这段函数，测试和生产无法注入 provider。
        self.platform = platform or sys.platform  # 新增代码+Phase32WindowsNativeHelper: 保存 helper 平台；如果没有这行代码，非 Windows 拒绝路径无法测试。
        self.capture_provider = capture_provider or Win32GdiWindowCaptureProvider(platform=self.platform)  # 新增代码+Phase32WindowsNativeHelper: 保存截图 provider；如果没有这行代码，helper 无法获取截图。
        self.text_provider = text_provider or Win32WindowTextProvider(platform=self.platform)  # 新增代码+Phase32WindowsNativeHelper: 保存文本 provider；如果没有这行代码，helper 无法获取窗口文本。
        self.diagnostics = WindowsNativeObservationDiagnostics(capture_provider=self.capture_provider, text_provider=self.text_provider, platform=self.platform)  # 新增代码+Phase33WindowsNativeDiagnostics: 保存 provider 诊断构建器；如果没有这行代码，helper.status 不能解释 WGC/UIA 与 fallback 差距。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，WindowsNativeWindowObservationHelper.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，返回 helper 状态；如果没有这段函数，computer_status 无法显示 native 观察边界。
        capture_status = _provider_status(self.capture_provider)  # 新增代码+Phase32WindowsNativeHelper: 读取截图 provider 状态；如果没有这行代码，状态页不知道截图后端是否可用。
        text_status = _provider_status(self.text_provider)  # 新增代码+Phase32WindowsNativeHelper: 读取文本 provider 状态；如果没有这行代码，状态页不知道文本后端是否可用。
        diagnostics_status = self.diagnostics.status()  # 新增代码+Phase33WindowsNativeDiagnostics: 构建 Phase33 provider 诊断；如果没有这行代码，状态页看不到 WGC/UIA 优先级和安全边界。
        available = self.platform == "win32" and (bool(capture_status.get("available", False)) or bool(text_status.get("available", False)))  # 新增代码+Phase32WindowsNativeHelper: 计算 helper 是否可用；如果没有这行代码，状态可能在非 Windows 误报可用。
        return {"helper": "windows_native_observation", "available": available, "reason": "Phase33 Windows native 只读 diagnostics 已接入；当前仍以 GDI/Win32 fallback 观察，WGC/UIA 作为首选缺口明确报告。", "capture": capture_status, "text": text_status, "diagnostics": diagnostics_status}  # 修改代码+Phase33WindowsNativeDiagnostics: 返回 helper 状态并附加诊断对象；如果没有这行代码，用户看不到 native helper 的精确差距。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，WindowsNativeWindowObservationHelper.status 到此结束；如果没有这个边界说明，读者不容易看出状态函数范围。

    def observe_window(self, window: dict[str, Any]) -> WindowObservationPayload:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，观察指定窗口；如果没有这段函数，Windows 后端无法保存 native 截图和文本。
        if self.platform != "win32":  # 新增代码+Phase32WindowsNativeHelper: 非 Windows 平台拒绝；如果没有这行代码，跨平台测试会误触发 provider。
            return WindowObservationPayload(helper_name="windows_native_observation", helper_available=False, helper_reason="当前平台不是 Windows，native helper 未读取截图或文本。")  # 新增代码+Phase32WindowsNativeHelper: 返回安全不可用 payload；如果没有这行代码，用户不知道为何没有证据。
        hwnd = parse_hwnd_from_window(window)  # 新增代码+Phase32WindowsNativeHelper: 解析窗口句柄；如果没有这行代码，provider 不知道要读取哪个窗口。
        if hwnd <= 0:  # 新增代码+Phase32WindowsNativeHelper: 检查句柄是否有效；如果没有这行代码，0 句柄可能进入系统 API。
            return WindowObservationPayload(helper_name="windows_native_observation", helper_available=False, helper_reason="窗口句柄无效，native helper 未读取截图或文本。")  # 新增代码+Phase32WindowsNativeHelper: 返回坏句柄说明；如果没有这行代码，错误目标不可解释。
        capture = self.capture_provider.capture_window(hwnd)  # 新增代码+Phase32WindowsNativeHelper: 调用截图 provider；如果没有这行代码，payload 没有截图字段。
        text = self.text_provider.read_window_text(hwnd)  # 新增代码+Phase32WindowsNativeHelper: 调用文本 provider；如果没有这行代码，payload 没有文本字段。
        helper_available = bool(capture.captured or text.captured)  # 新增代码+Phase32WindowsNativeHelper: 只要截图或文本任一成功就视为可用；如果没有这行代码，部分成功会被误报失败。
        reason = f"capture={capture.backend}:{capture.reason}; text={text.backend}:{text.reason}"  # 新增代码+Phase32WindowsNativeHelper: 合并 provider 说明；如果没有这行代码，证据来源无法排查。
        return WindowObservationPayload(screenshot_bytes=capture.screenshot_bytes, screenshot_format=capture.screenshot_format, screenshot_width=capture.screenshot_width, screenshot_height=capture.screenshot_height, accessibility_text=text.accessibility_text, focused_element=text.focused_element, selected_text=text.selected_text, document_text=text.document_text, helper_name="windows_native_observation", helper_available=helper_available, helper_reason=reason)  # 新增代码+Phase32WindowsNativeHelper: 返回统一 payload 给 evidence store；如果没有这行代码，native helper 结果无法落盘。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，WindowsNativeWindowObservationHelper.observe_window 到此结束；如果没有这个边界说明，读者不容易看出观察流程范围。
