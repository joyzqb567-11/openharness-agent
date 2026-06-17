"""Windows Computer Use MCP v2 系统剪贴板后端。"""  # 新增代码+ClipboardSystemBridge：说明本文件只封装剪贴板后端；如果没有这行代码，读者不容易区分协议层和 Windows 原生层。
from __future__ import annotations  # 新增代码+ClipboardSystemBridge：延迟解析类型注解；如果没有这行代码，Protocol 注解可能在导入时提前求值。

import ctypes  # 新增代码+ClipboardSystemBridge：导入 ctypes 调用 Windows 原生剪贴板 API；如果没有这行代码，Python 无法访问 Win32 剪贴板函数。
from ctypes import wintypes  # 新增代码+ClipboardSystemBridge：导入 Windows 类型别名；如果没有这行代码，句柄和布尔返回值类型会写得不清楚。
from typing import Protocol  # 新增代码+ClipboardSystemBridge：导入 Protocol 定义后端接口；如果没有这行代码，测试后端和真实后端缺少统一契约。

CF_UNICODETEXT = 13  # 新增代码+ClipboardSystemBridge：声明 Windows Unicode 文本剪贴板格式；如果没有这行代码，读写文本会用魔法数字且容易写错。
GMEM_MOVEABLE = 0x0002  # 新增代码+ClipboardSystemBridge：声明 SetClipboardData 需要的可移动全局内存标志；如果没有这行代码，Windows 可能拒绝接管写入缓冲区。


class ClipboardBackend(Protocol):  # 新增代码+ClipboardSystemBridge：类段开始，定义剪贴板后端必须具备的最小接口；如果没有这段接口，工具层无法安全替换真实/测试后端。
    backend_name: str  # 新增代码+ClipboardSystemBridge：声明后端可读名称；如果没有这行代码，结果 payload 无法说明读写来自哪个后端。

    def read_text(self) -> str:  # 新增代码+ClipboardSystemBridge：声明读取文本方法；如果没有这行代码，read_clipboard 无法对后端做统一调用。
        ...  # 新增代码+ClipboardSystemBridge：Protocol 方法占位；如果没有这行代码，接口声明语法不完整。

    def write_text(self, text: str) -> None:  # 新增代码+ClipboardSystemBridge：声明写入文本方法；如果没有这行代码，write_clipboard 无法对后端做统一调用。
        ...  # 新增代码+ClipboardSystemBridge：Protocol 方法占位；如果没有这行代码，接口声明语法不完整。
    # 新增代码+ClipboardSystemBridge：类段结束，ClipboardBackend 到此结束；如果没有这个边界说明，用户不容易看出后端契约范围。


class MemoryClipboardBackend:  # 新增代码+ClipboardSystemBridge：类段开始，提供测试专用内存剪贴板；如果没有这段类，自动化测试会被迫读写真系统剪贴板。
    backend_name = "memory_system_clipboard"  # 新增代码+ClipboardSystemBridge：标记这是内存模拟后端；如果没有这行代码，测试无法断言工具用的是安全后端。

    def __init__(self, initial_text: str = "") -> None:  # 新增代码+ClipboardSystemBridge：函数段开始，初始化内存剪贴板文本和计数器；如果没有这段函数，测试无法准备初始内容。
        self.text = str(initial_text)  # 新增代码+ClipboardSystemBridge：保存初始文本；如果没有这行代码，读取测试没有稳定内容来源。
        self.read_count = 0  # 新增代码+ClipboardSystemBridge：记录读取次数；如果没有这行代码，测试无法证明拒绝路径没有触碰后端。
        self.write_count = 0  # 新增代码+ClipboardSystemBridge：记录写入次数；如果没有这行代码，测试无法证明写入行为是否发生。
    # 新增代码+ClipboardSystemBridge：函数段结束，MemoryClipboardBackend.__init__ 到此结束；如果没有这个边界说明，用户不容易看出内存后端初始化范围。

    def read_text(self) -> str:  # 新增代码+ClipboardSystemBridge：函数段开始，从内存后端读取文本；如果没有这段函数，read_clipboard 测试无法读取模拟内容。
        self.read_count += 1  # 新增代码+ClipboardSystemBridge：累加读取次数；如果没有这行代码，拒绝路径是否读过后端无法被测试证明。
        return self.text  # 新增代码+ClipboardSystemBridge：返回当前内存文本；如果没有这行代码，读取工具拿不到内容。
    # 新增代码+ClipboardSystemBridge：函数段结束，MemoryClipboardBackend.read_text 到此结束；如果没有这个边界说明，用户不容易看出读取范围。

    def write_text(self, text: str) -> None:  # 新增代码+ClipboardSystemBridge：函数段开始，向内存后端写入文本；如果没有这段函数，write_clipboard 测试无法模拟系统写入。
        self.write_count += 1  # 新增代码+ClipboardSystemBridge：累加写入次数；如果没有这行代码，测试无法证明写入是否真的发生。
        self.text = str(text)  # 新增代码+ClipboardSystemBridge：保存写入文本；如果没有这行代码，后续读取无法读回本次写入。
    # 新增代码+ClipboardSystemBridge：函数段结束，MemoryClipboardBackend.write_text 到此结束；如果没有这个边界说明，用户不容易看出写入范围。
    # 新增代码+ClipboardSystemBridge：类段结束，MemoryClipboardBackend 到此结束；如果没有这个边界说明，用户不容易看出测试后端范围。


def _configure_windows_clipboard_api(user32: object, kernel32: object) -> None:  # 新增代码+ClipboardSystemBridge：函数段开始，声明 Win32 函数参数和返回类型；如果没有这段函数，64 位句柄可能被 ctypes 默认 int 截断。
    user32.OpenClipboard.argtypes = [wintypes.HWND]  # 新增代码+ClipboardSystemBridge：声明 OpenClipboard 接收窗口句柄；如果没有这行代码，ctypes 会按默认类型传参。
    user32.OpenClipboard.restype = wintypes.BOOL  # 新增代码+ClipboardSystemBridge：声明 OpenClipboard 返回 BOOL；如果没有这行代码，失败判断可能不稳定。
    user32.CloseClipboard.argtypes = []  # 新增代码+ClipboardSystemBridge：声明 CloseClipboard 无参数；如果没有这行代码，ctypes 会保留不清晰的默认调用签名。
    user32.CloseClipboard.restype = wintypes.BOOL  # 新增代码+ClipboardSystemBridge：声明 CloseClipboard 返回 BOOL；如果没有这行代码，调试时难以判断关闭是否失败。
    user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]  # 新增代码+ClipboardSystemBridge：声明格式检查参数；如果没有这行代码，格式 id 可能按默认类型传递。
    user32.IsClipboardFormatAvailable.restype = wintypes.BOOL  # 新增代码+ClipboardSystemBridge：声明格式检查返回 BOOL；如果没有这行代码，空剪贴板判断不稳定。
    user32.GetClipboardData.argtypes = [wintypes.UINT]  # 新增代码+ClipboardSystemBridge：声明读取剪贴板数据格式参数；如果没有这行代码，格式 id 传递不清楚。
    user32.GetClipboardData.restype = wintypes.HANDLE  # 新增代码+ClipboardSystemBridge：声明读取结果为句柄；如果没有这行代码，64 位句柄可能被截断。
    user32.EmptyClipboard.argtypes = []  # 新增代码+ClipboardSystemBridge：声明清空剪贴板无参数；如果没有这行代码，ctypes 调用签名不清楚。
    user32.EmptyClipboard.restype = wintypes.BOOL  # 新增代码+ClipboardSystemBridge：声明清空返回 BOOL；如果没有这行代码，清空失败可能被误判。
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]  # 新增代码+ClipboardSystemBridge：声明写入格式和内存句柄；如果没有这行代码，Windows 可能收到错误句柄类型。
    user32.SetClipboardData.restype = wintypes.HANDLE  # 新增代码+ClipboardSystemBridge：声明写入返回接管后的句柄；如果没有这行代码，失败判断可能不准确。
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]  # 新增代码+ClipboardSystemBridge：声明全局内存分配参数；如果没有这行代码，文本字节数可能被错误传递。
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL  # 新增代码+ClipboardSystemBridge：声明分配返回 HGLOBAL；如果没有这行代码，64 位内存句柄可能被截断。
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]  # 新增代码+ClipboardSystemBridge：声明 GlobalLock 接收 HGLOBAL；如果没有这行代码，锁定内存时句柄类型不清楚。
    kernel32.GlobalLock.restype = ctypes.c_void_p  # 新增代码+ClipboardSystemBridge：声明 GlobalLock 返回指针；如果没有这行代码，ctypes 可能截断指针。
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]  # 新增代码+ClipboardSystemBridge：声明 GlobalUnlock 接收 HGLOBAL；如果没有这行代码，解锁调用签名不清楚。
    kernel32.GlobalUnlock.restype = wintypes.BOOL  # 新增代码+ClipboardSystemBridge：声明 GlobalUnlock 返回 BOOL；如果没有这行代码，调试解锁结果不稳定。
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]  # 新增代码+ClipboardSystemBridge：声明 GlobalFree 接收 HGLOBAL；如果没有这行代码，失败清理可能传错句柄类型。
    kernel32.GlobalFree.restype = wintypes.HGLOBAL  # 新增代码+ClipboardSystemBridge：声明 GlobalFree 返回剩余句柄；如果没有这行代码，清理结果无法稳定判断。
# 新增代码+ClipboardSystemBridge：函数段结束，_configure_windows_clipboard_api 到此结束；如果没有这个边界说明，用户不容易看出 Win32 类型配置范围。


class WindowsClipboardBackend:  # 新增代码+ClipboardSystemBridge：类段开始，提供真实 Windows 系统剪贴板后端；如果没有这段类，OpenHarness 无法对齐 ClaudeCode 的真实系统剪贴板行为。
    backend_name = "windows_system_clipboard"  # 新增代码+ClipboardSystemBridge：标记这是 Windows 系统剪贴板后端；如果没有这行代码，结果 payload 无法证明使用真实系统后端。

    def _api(self) -> tuple[object, object]:  # 新增代码+ClipboardSystemBridge：函数段开始，获取并配置 user32/kernel32；如果没有这段函数，每次调用都要重复低层配置。
        user32 = ctypes.windll.user32  # 新增代码+ClipboardSystemBridge：读取 user32 动态库；如果没有这行代码，无法打开和操作 Windows 剪贴板。
        kernel32 = ctypes.windll.kernel32  # 新增代码+ClipboardSystemBridge：读取 kernel32 动态库；如果没有这行代码，无法分配和锁定全局内存。
        _configure_windows_clipboard_api(user32, kernel32)  # 新增代码+ClipboardSystemBridge：配置 Win32 函数签名；如果没有这行代码，64 位句柄和指针可能不安全。
        return user32, kernel32  # 新增代码+ClipboardSystemBridge：返回已配置的 API 对象；如果没有这行代码，读写方法拿不到底层函数。
    # 新增代码+ClipboardSystemBridge：函数段结束，WindowsClipboardBackend._api 到此结束；如果没有这个边界说明，用户不容易看出 API 获取范围。

    def read_text(self) -> str:  # 新增代码+ClipboardSystemBridge：函数段开始，读取 Windows 系统剪贴板文本；如果没有这段函数，read_clipboard 不能读取真实系统剪贴板。
        user32, kernel32 = self._api()  # 新增代码+ClipboardSystemBridge：获取已配置 Win32 API；如果没有这行代码，后续无法调用系统剪贴板函数。
        if not user32.OpenClipboard(None):  # 新增代码+ClipboardSystemBridge：尝试打开系统剪贴板；如果没有这行代码，读取时可能和其他进程并发冲突。
            raise RuntimeError("open_clipboard_failed")  # 新增代码+ClipboardSystemBridge：明确报告打开失败；如果没有这行代码，调用方只能看到空结果而不知道失败原因。
        try:  # 新增代码+ClipboardSystemBridge：进入打开剪贴板后的保护区；如果没有这行代码，异常时可能无法关闭剪贴板。
            if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):  # 新增代码+ClipboardSystemBridge：确认当前剪贴板包含 Unicode 文本；如果没有这行代码，非文本剪贴板可能被错误读取。
                return ""  # 新增代码+ClipboardSystemBridge：非文本剪贴板返回空文本；如果没有这行代码，模型会收到底层句柄错误。
            handle = user32.GetClipboardData(CF_UNICODETEXT)  # 新增代码+ClipboardSystemBridge：获取 Unicode 文本数据句柄；如果没有这行代码，无法访问剪贴板内容。
            if not handle:  # 新增代码+ClipboardSystemBridge：检查数据句柄是否存在；如果没有这行代码，空句柄会继续进入 GlobalLock。
                return ""  # 新增代码+ClipboardSystemBridge：空句柄按空文本处理；如果没有这行代码，空剪贴板会变成异常。
            pointer = kernel32.GlobalLock(handle)  # 新增代码+ClipboardSystemBridge：锁定剪贴板全局内存并取得指针；如果没有这行代码，无法安全读取文本。
            if not pointer:  # 新增代码+ClipboardSystemBridge：检查锁定是否成功；如果没有这行代码，空指针会导致读取崩溃。
                raise RuntimeError("global_lock_failed")  # 新增代码+ClipboardSystemBridge：明确报告锁定失败；如果没有这行代码，调用方无法定位系统层失败。
            try:  # 新增代码+ClipboardSystemBridge：进入锁定内存后的读取保护区；如果没有这行代码，异常时可能无法解锁内存。
                return ctypes.wstring_at(pointer)  # 新增代码+ClipboardSystemBridge：把 Windows Unicode 指针转成 Python 字符串；如果没有这行代码，工具拿不到可返回文本。
            finally:  # 新增代码+ClipboardSystemBridge：确保读取后释放锁；如果没有这行代码，系统剪贴板内存可能保持锁定。
                kernel32.GlobalUnlock(handle)  # 新增代码+ClipboardSystemBridge：解锁全局内存；如果没有这行代码，其他进程可能被影响。
        finally:  # 新增代码+ClipboardSystemBridge：确保无论成功失败都关闭剪贴板；如果没有这行代码，系统剪贴板可能被当前进程占住。
            user32.CloseClipboard()  # 新增代码+ClipboardSystemBridge：关闭系统剪贴板；如果没有这行代码，后续应用可能无法访问剪贴板。
    # 新增代码+ClipboardSystemBridge：函数段结束，WindowsClipboardBackend.read_text 到此结束；如果没有这个边界说明，用户不容易看出读取系统剪贴板范围。

    def write_text(self, text: str) -> None:  # 新增代码+ClipboardSystemBridge：函数段开始，写入 Windows 系统剪贴板文本；如果没有这段函数，write_clipboard 不能写入真实系统剪贴板。
        user32, kernel32 = self._api()  # 新增代码+ClipboardSystemBridge：获取已配置 Win32 API；如果没有这行代码，后续无法调用系统剪贴板函数。
        value = str(text)  # 新增代码+ClipboardSystemBridge：把输入规范化为字符串；如果没有这行代码，非字符串输入可能导致 unicode buffer 构造失败。
        buffer = ctypes.create_unicode_buffer(value, len(value) + 1)  # 新增代码+ClipboardSystemBridge：创建带结尾空字符的 Unicode 缓冲区；如果没有这行代码，Windows 读取文本时可能越界。
        byte_count = ctypes.sizeof(buffer)  # 新增代码+ClipboardSystemBridge：计算需要复制的字节数；如果没有这行代码，写入可能截断中文或尾部空字符。
        if not user32.OpenClipboard(None):  # 新增代码+ClipboardSystemBridge：尝试打开系统剪贴板；如果没有这行代码，写入时可能和其他进程并发冲突。
            raise RuntimeError("open_clipboard_failed")  # 新增代码+ClipboardSystemBridge：明确报告打开失败；如果没有这行代码，调用方无法知道写入没有发生。
        allocated_handle = None  # 新增代码+ClipboardSystemBridge：记录尚未交给系统的内存句柄；如果没有这行代码，失败清理无法知道该释放哪个句柄。
        try:  # 新增代码+ClipboardSystemBridge：进入打开剪贴板后的保护区；如果没有这行代码，异常时可能无法关闭剪贴板。
            if not user32.EmptyClipboard():  # 新增代码+ClipboardSystemBridge：清空当前剪贴板以准备写入新文本；如果没有这行代码，SetClipboardData 可能失败或保留旧格式。
                raise RuntimeError("empty_clipboard_failed")  # 新增代码+ClipboardSystemBridge：明确报告清空失败；如果没有这行代码，调用方无法定位系统层失败。
            allocated_handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, byte_count)  # 新增代码+ClipboardSystemBridge：分配可由 Windows 接管的全局内存；如果没有这行代码，SetClipboardData 没有可接管缓冲区。
            if not allocated_handle:  # 新增代码+ClipboardSystemBridge：检查内存分配是否成功；如果没有这行代码，空句柄会继续进入 GlobalLock。
                raise RuntimeError("global_alloc_failed")  # 新增代码+ClipboardSystemBridge：明确报告分配失败；如果没有这行代码，调用方无法知道资源不足。
            pointer = kernel32.GlobalLock(allocated_handle)  # 新增代码+ClipboardSystemBridge：锁定分配的全局内存；如果没有这行代码，无法把 Python 文本复制进去。
            if not pointer:  # 新增代码+ClipboardSystemBridge：检查锁定是否成功；如果没有这行代码，空指针会导致写入崩溃。
                kernel32.GlobalFree(allocated_handle)  # 新增代码+ClipboardSystemBridge：锁定失败时释放已分配内存；如果没有这行代码，失败路径会泄漏全局内存。
                allocated_handle = None  # 新增代码+ClipboardSystemBridge：清空句柄避免 finally 重复释放；如果没有这行代码，失败清理可能二次释放。
                raise RuntimeError("global_lock_failed")  # 新增代码+ClipboardSystemBridge：明确报告锁定失败；如果没有这行代码，调用方无法定位系统层失败。
            try:  # 新增代码+ClipboardSystemBridge：进入复制文本的保护区；如果没有这行代码，异常时可能无法解锁内存。
                ctypes.memmove(pointer, ctypes.addressof(buffer), byte_count)  # 新增代码+ClipboardSystemBridge：把 Unicode 缓冲区复制到全局内存；如果没有这行代码，剪贴板会拿到空或乱码内容。
            finally:  # 新增代码+ClipboardSystemBridge：确保复制后解锁内存；如果没有这行代码，SetClipboardData 前内存可能仍被锁住。
                kernel32.GlobalUnlock(allocated_handle)  # 新增代码+ClipboardSystemBridge：解锁全局内存；如果没有这行代码，Windows 可能无法接管数据。
            if not user32.SetClipboardData(CF_UNICODETEXT, allocated_handle):  # 新增代码+ClipboardSystemBridge：把文本内存交给 Windows 剪贴板；如果没有这行代码，系统剪贴板不会更新。
                kernel32.GlobalFree(allocated_handle)  # 新增代码+ClipboardSystemBridge：写入失败时释放未被系统接管的内存；如果没有这行代码，失败路径会泄漏内存。
                allocated_handle = None  # 新增代码+ClipboardSystemBridge：清空句柄避免 finally 重复释放；如果没有这行代码，失败清理可能二次释放。
                raise RuntimeError("set_clipboard_data_failed")  # 新增代码+ClipboardSystemBridge：明确报告设置失败；如果没有这行代码，调用方会误以为写入成功。
            allocated_handle = None  # 新增代码+ClipboardSystemBridge：写入成功后系统接管句柄；如果没有这行代码，finally 可能释放已归系统所有的内存。
        finally:  # 新增代码+ClipboardSystemBridge：确保无论成功失败都关闭剪贴板；如果没有这行代码，系统剪贴板可能被当前进程占住。
            if allocated_handle:  # 新增代码+ClipboardSystemBridge：检查是否还有未交给系统的内存；如果没有这行代码，失败路径可能泄漏内存。
                kernel32.GlobalFree(allocated_handle)  # 新增代码+ClipboardSystemBridge：释放失败路径残留内存；如果没有这行代码，系统资源会泄漏。
            user32.CloseClipboard()  # 新增代码+ClipboardSystemBridge：关闭系统剪贴板；如果没有这行代码，后续应用可能无法访问剪贴板。
    # 新增代码+ClipboardSystemBridge：函数段结束，WindowsClipboardBackend.write_text 到此结束；如果没有这个边界说明，用户不容易看出写入系统剪贴板范围。
    # 新增代码+ClipboardSystemBridge：类段结束，WindowsClipboardBackend 到此结束；如果没有这个边界说明，用户不容易看出真实后端范围。
