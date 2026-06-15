"""Phase56 Windows real screenshot pipeline with pixel guard."""  # 新增代码+Phase56RealScreenshotPipeline: 标明本文件负责真实截图和像素验真；如果没有这行代码，读者不容易区分 Phase45 合同层和 Phase56 生产验收层。
from __future__ import annotations  # 新增代码+Phase56RealScreenshotPipeline: 启用延迟类型解析；如果没有这行代码，旧入口遇到前向类型标注时更容易导入失败。

import json  # 新增代码+Phase56RealScreenshotPipeline: 导入 JSON 用于 CLI 输出结构化报告；如果没有这行代码，真实终端失败时不易复盘。
import struct  # 新增代码+Phase56RealScreenshotPipeline: 导入 struct 解析和生成 BMP 头；如果没有这行代码，pixel guard 无法读取真实 GDI BMP 像素。
import subprocess  # 新增代码+Phase56RealScreenshotPipeline: 导入 subprocess 启动安全 Notepad 窗口；如果没有这行代码，真实 smoke 没有自有截图目标。
import sys  # 新增代码+Phase56RealScreenshotPipeline: 导入 sys 判断平台；如果没有这行代码，非 Windows 环境可能误触发 Win32 截图。
import tempfile  # 新增代码+Phase56RealScreenshotPipeline: 导入临时目录工具隔离合同自检文件；如果没有这行代码，fake 自检会污染项目目录。
import time  # 新增代码+Phase56RealScreenshotPipeline: 导入 time 轮询安全窗口出现；如果没有这行代码，Notepad 启动延迟会被误判失败。
from pathlib import Path  # 新增代码+Phase56RealScreenshotPipeline: 导入 Path 管理 evidence 和临时文件路径；如果没有这行代码，Windows 路径拼接会更脆弱。
from typing import Any  # 新增代码+Phase56RealScreenshotPipeline: 导入 Any 标注 JSON 风格结构；如果没有这行代码，协议边界不清楚。

try:  # 新增代码+Phase56RealScreenshotPipeline: 优先按包模式导入既有 Computer Use 组件；如果没有这行代码，unittest 和生产入口不能复用项目模块。
    from learning_agent.computer_use_mcp_v2.windows_runtime.evidence import ComputerUseEvidenceStore  # 新增代码+Phase56RealScreenshotPipeline: 导入 evidence store；如果没有这行代码，截图无法落盘并生成 image_result。
    from learning_agent.computer_use_mcp_v2.windows_runtime.helper_client import WindowObservationPayload  # 新增代码+Phase56RealScreenshotPipeline: 导入观察 payload；如果没有这行代码，pipeline 无法复用 Phase29/41 保存合同。
    from learning_agent.computer_use_mcp_v2.windows_runtime.native_helper import NativeWindowCaptureResult, Win32GdiWindowCaptureProvider, parse_hwnd_from_window  # 新增代码+Phase56RealScreenshotPipeline: 导入截图结果、GDI provider 和 hwnd 解析；如果没有这行代码，真实 Windows 截图链路无法工作。
    from learning_agent.computer_use_mcp_v2.windows_runtime.wgc_capture import WindowsGraphicsCaptureProvider  # 新增代码+Phase56RealScreenshotPipeline: 导入 WGC provider 合同；如果没有这行代码，Phase56 不能保持 WGC 优先策略。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase56RealScreenshotPipeline: 导入真实窗口 inventory；如果没有这行代码，safe window smoke 无法定位自有 Notepad。
except ModuleNotFoundError as error:  # 新增代码+Phase56RealScreenshotPipeline: 兼容 start_oauth_agent.bat 从 learning_agent 目录运行；如果没有这行代码，脚本模式可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.evidence", "learning_agent.computer_use_mcp_v2.windows_runtime.helper_client", "learning_agent.computer_use_mcp_v2.windows_runtime.native_helper", "learning_agent.computer_use_mcp_v2.windows_runtime.wgc_capture", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend"}:  # 新增代码+Phase56RealScreenshotPipeline: 只允许包路径缺失时 fallback；如果没有这行代码，真实内部 bug 会被误吞。
        raise  # 新增代码+Phase56RealScreenshotPipeline: 重新抛出非路径错误；如果没有这行代码，排查真实依赖问题会困难。
    from computer_use_mcp_v2.windows_runtime.evidence import ComputerUseEvidenceStore  # 新增代码+Phase56RealScreenshotPipeline: 脚本模式导入 evidence store；如果没有这行代码，bat 入口无法保存截图。
    from computer_use_mcp_v2.windows_runtime.helper_client import WindowObservationPayload  # 新增代码+Phase56RealScreenshotPipeline: 脚本模式导入 observation payload；如果没有这行代码，bat 入口无法构造证据输入。
    from computer_use_mcp_v2.windows_runtime.native_helper import NativeWindowCaptureResult, Win32GdiWindowCaptureProvider, parse_hwnd_from_window  # 新增代码+Phase56RealScreenshotPipeline: 脚本模式导入 GDI provider 和 hwnd 解析；如果没有这行代码，bat 入口无法截图。
    from computer_use_mcp_v2.windows_runtime.wgc_capture import WindowsGraphicsCaptureProvider  # 新增代码+Phase56RealScreenshotPipeline: 脚本模式导入 WGC provider；如果没有这行代码，bat 入口无法报告 WGC 优先链。
    from computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase56RealScreenshotPipeline: 脚本模式导入窗口 inventory；如果没有这行代码，bat 入口无法定位安全窗口。

PHASE56_WINDOWS_REAL_SCREENSHOT_MARKER = "PHASE56_WINDOWS_REAL_SCREENSHOT_READY"  # 新增代码+Phase56RealScreenshotPipeline: 定义 Phase56 ready marker；如果没有这行代码，真实终端验收无法稳定等待本阶段输出。
PHASE56_WINDOWS_REAL_SCREENSHOT_OK_TOKEN = "PHASE56_WINDOWS_REAL_SCREENSHOT_OK"  # 新增代码+Phase56RealScreenshotPipeline: 定义 Phase56 OK token；如果没有这行代码，debug log 无法区分运行完成和真正通过。
PHASE56_REAL_SCREENSHOT_MODEL = "phase56_windows_real_screenshot_pipeline"  # 新增代码+Phase56RealScreenshotPipeline: 定义 pipeline 模型名；如果没有这行代码，状态和 evidence 难以区分版本。
PHASE56_ACTIONS_EXPANDED = False  # 新增代码+Phase56RealScreenshotPipeline: 明确 Phase56 只读截图不扩大桌面动作；如果没有这行代码，安全边界会不透明。


def _phase56_bool_token(value: Any) -> str:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，把布尔值转成小写 token；如果没有这段函数，CLI 可能混用 True/False 和 true/false。
    return "true" if bool(value) else "false"  # 新增代码+Phase56RealScreenshotPipeline: 返回 true/false；如果没有这行代码，验收场景 token 匹配可能失败。
# 新增代码+Phase56RealScreenshotPipeline: 函数段结束，_phase56_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


def build_phase56_test_bmp(width: int, height: int, title_color: tuple[int, int, int], body_color: tuple[int, int, int], accent_color: tuple[int, int, int]) -> bytes:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，生成测试用 32-bit BMP；如果没有这段函数，pixel guard 单测需要依赖外部图片库。
    safe_width = max(1, int(width))  # 新增代码+Phase56RealScreenshotPipeline: 规范化宽度至少为 1；如果没有这行代码，坏输入会生成无效 BMP。
    safe_height = max(1, int(height))  # 新增代码+Phase56RealScreenshotPipeline: 规范化高度至少为 1；如果没有这行代码，坏输入会生成无效 BMP。
    title_height = max(1, safe_height // 5)  # 新增代码+Phase56RealScreenshotPipeline: 计算标题栏高度；如果没有这行代码，测试图没有标题区域可校验。
    rows: list[bytes] = []  # 新增代码+Phase56RealScreenshotPipeline: 准备 BMP 像素行列表；如果没有这行代码，像素数据没有容器。
    for logical_y in range(safe_height - 1, -1, -1):  # 新增代码+Phase56RealScreenshotPipeline: 以 BMP bottom-up 顺序写行；如果没有这行代码，BMP 头和像素方向不一致。
        row = bytearray()  # 新增代码+Phase56RealScreenshotPipeline: 创建当前行缓冲；如果没有这行代码，无法逐像素追加 BGRA。
        for x in range(safe_width):  # 新增代码+Phase56RealScreenshotPipeline: 遍历当前行每个像素；如果没有这行代码，行里没有像素。
            color = title_color if logical_y < title_height else body_color  # 新增代码+Phase56RealScreenshotPipeline: 标题区和正文区使用不同颜色；如果没有这行代码，标题区域可见性无法测试。
            if (logical_y < title_height and x % 17 == 0) or (logical_y >= title_height and logical_y % 19 == 0 and 10 <= x <= safe_width - 10):  # 新增代码+Phase56RealScreenshotPipeline: 加入少量强调色模拟文字/按钮；如果没有这行代码，真实有效图可能被单色规则误判。
                color = accent_color  # 新增代码+Phase56RealScreenshotPipeline: 使用强调色写入像素；如果没有这行代码，测试图颜色多样性不足。
            red, green, blue = [max(0, min(255, int(channel))) for channel in color]  # 新增代码+Phase56RealScreenshotPipeline: 限制 RGB 通道到 0-255；如果没有这行代码，坏颜色值会破坏 bytes 构造。
            row.extend(bytes((blue, green, red, 0)))  # 新增代码+Phase56RealScreenshotPipeline: 按 BGRA 顺序写像素；如果没有这行代码，BMP 颜色通道会错。
        rows.append(bytes(row))  # 新增代码+Phase56RealScreenshotPipeline: 保存当前行；如果没有这行代码，最终像素数据会缺行。
    pixel_bytes = b"".join(rows)  # 新增代码+Phase56RealScreenshotPipeline: 合并所有行像素；如果没有这行代码，BMP 文件没有完整像素区。
    file_header_size = 14  # 新增代码+Phase56RealScreenshotPipeline: BMP 文件头大小固定 14 字节；如果没有这行代码，偏移计算会魔法化。
    dib_header_size = 40  # 新增代码+Phase56RealScreenshotPipeline: 使用 BITMAPINFOHEADER 40 字节；如果没有这行代码，解析器不知道 DIB 结构。
    pixel_offset = file_header_size + dib_header_size  # 新增代码+Phase56RealScreenshotPipeline: 计算像素数据起点；如果没有这行代码，BMP 头无法指向像素区。
    file_size = pixel_offset + len(pixel_bytes)  # 新增代码+Phase56RealScreenshotPipeline: 计算文件总大小；如果没有这行代码，BMP header size 字段不可信。
    file_header = b"BM" + struct.pack("<IHHI", file_size, 0, 0, pixel_offset)  # 新增代码+Phase56RealScreenshotPipeline: 生成 BMP file header；如果没有这行代码，artifact 不能被当作 BMP 打开。
    dib_header = struct.pack("<IiiHHIIiiII", dib_header_size, safe_width, safe_height, 1, 32, 0, len(pixel_bytes), 2835, 2835, 0, 0)  # 新增代码+Phase56RealScreenshotPipeline: 生成 32-bit DIB header；如果没有这行代码，pixel guard 无法解析尺寸和位深。
    return file_header + dib_header + pixel_bytes  # 新增代码+Phase56RealScreenshotPipeline: 返回完整 BMP bytes；如果没有这行代码，测试和 fake provider 拿不到图片。
# 新增代码+Phase56RealScreenshotPipeline: 函数段结束，build_phase56_test_bmp 到此结束；如果没有这个边界说明，初学者不容易看出测试图片生成范围。


class Phase56PixelGuard:  # 新增代码+Phase56RealScreenshotPipeline: 类段开始，负责判断截图是不是可用图像；如果没有这个类，黑屏/空白/坏尺寸截图可能误过。
    def __init__(self, max_sample_pixels: int = 4096, min_unique_colors: int = 3) -> None:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，初始化采样参数；如果没有这段函数，guard 阈值无法集中管理。
        self.max_sample_pixels = max(16, int(max_sample_pixels))  # 新增代码+Phase56RealScreenshotPipeline: 保存最大采样像素数并设置下限；如果没有这行代码，大图全量扫描会浪费时间。
        self.min_unique_colors = max(2, int(min_unique_colors))  # 新增代码+Phase56RealScreenshotPipeline: 保存最少颜色数；如果没有这行代码，单色图可能误判通过。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，Phase56PixelGuard.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def inspect_bytes(self, image_bytes: bytes, image_format: str, expected_width: int = 0, expected_height: int = 0) -> dict[str, Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，分析截图 bytes；如果没有这段函数，pipeline 无法在落盘前验真。
        raw_bytes = bytes(image_bytes or b"")  # 新增代码+Phase56RealScreenshotPipeline: 复制输入 bytes；如果没有这行代码，None 或 bytearray 输入可能导致异常。
        normalized_format = str(image_format or "").lower().lstrip(".")  # 新增代码+Phase56RealScreenshotPipeline: 规范化图片格式；如果没有这行代码，BMP/bmp/.bmp 会被当成不同格式。
        if normalized_format == "bmp" or raw_bytes.startswith(b"BM"):  # 新增代码+Phase56RealScreenshotPipeline: 识别 BMP/GDI 截图；如果没有这行代码，真实 GDI 输出无法做像素级检测。
            return self._inspect_bmp(raw_bytes, int(expected_width or 0), int(expected_height or 0))  # 新增代码+Phase56RealScreenshotPipeline: 调用 BMP 解析；如果没有这行代码，BMP 只能做粗略大小判断。
        return self._base_report(False, "pixel guard 当前只对 BMP 做强像素验真。", bytes_length=len(raw_bytes), image_format=normalized_format)  # 新增代码+Phase56RealScreenshotPipeline: 非 BMP 保守失败；如果没有这行代码，未解码 PNG 可能被误当可信。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，Phase56PixelGuard.inspect_bytes 到此结束；如果没有这个边界说明，初学者不容易看出对外检测范围。

    def _base_report(self, passed: bool, reason: str, **extra: Any) -> dict[str, Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，构造统一 guard 报告；如果没有这段函数，失败和成功字段会漂移。
        report = {"passed": bool(passed), "reason": str(reason), "artifact_openable": False, "dimension_matches": False, "non_empty_pixels": False, "all_black": False, "all_white": False, "unique_color_count": 0, "title_region_visible": False, "width": 0, "height": 0, "bytes_length": 0, "image_format": ""}  # 新增代码+Phase56RealScreenshotPipeline: 设置稳定默认字段；如果没有这行代码，上层需要到处判断字段是否存在。
        report.update(extra)  # 新增代码+Phase56RealScreenshotPipeline: 合并额外分析字段；如果没有这行代码，BMP 解析结果无法写入报告。
        return report  # 新增代码+Phase56RealScreenshotPipeline: 返回 guard 报告；如果没有这行代码，调用方拿不到结构化结果。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，Phase56PixelGuard._base_report 到此结束；如果没有这个边界说明，初学者不容易看出报告构造范围。

    def _inspect_bmp(self, raw_bytes: bytes, expected_width: int, expected_height: int) -> dict[str, Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，解析 BMP 像素；如果没有这段函数，GDI 截图只能看文件存在。
        if len(raw_bytes) < 54 or not raw_bytes.startswith(b"BM"):  # 新增代码+Phase56RealScreenshotPipeline: 检查 BMP 最小头和签名；如果没有这行代码，坏文件会按像素解析崩溃。
            return self._base_report(False, "BMP 头无效。", bytes_length=len(raw_bytes), image_format="bmp")  # 新增代码+Phase56RealScreenshotPipeline: 返回头无效原因；如果没有这行代码，失败不可解释。
        pixel_offset = struct.unpack_from("<I", raw_bytes, 10)[0]  # 新增代码+Phase56RealScreenshotPipeline: 读取像素区偏移；如果没有这行代码，解析器不知道从哪开始读像素。
        dib_size = struct.unpack_from("<I", raw_bytes, 14)[0]  # 新增代码+Phase56RealScreenshotPipeline: 读取 DIB header 大小；如果没有这行代码，坏 BMP 结构不可识别。
        width = int(struct.unpack_from("<i", raw_bytes, 18)[0])  # 新增代码+Phase56RealScreenshotPipeline: 读取 BMP 宽度；如果没有这行代码，尺寸校验没有依据。
        signed_height = int(struct.unpack_from("<i", raw_bytes, 22)[0])  # 新增代码+Phase56RealScreenshotPipeline: 读取 BMP 高度；如果没有这行代码，top-down/bottom-up 方向无法判断。
        bits_per_pixel = int(struct.unpack_from("<H", raw_bytes, 28)[0])  # 新增代码+Phase56RealScreenshotPipeline: 读取位深；如果没有这行代码，像素步长无法计算。
        height = abs(signed_height)  # 新增代码+Phase56RealScreenshotPipeline: 取绝对高度；如果没有这行代码，top-down BMP 会得到负尺寸。
        if dib_size < 40 or width <= 0 or height <= 0 or bits_per_pixel not in {24, 32}:  # 新增代码+Phase56RealScreenshotPipeline: 检查 BMP 参数是否可支持；如果没有这行代码，不支持格式会产生错误采样。
            return self._base_report(False, "BMP 尺寸或位深不受支持。", bytes_length=len(raw_bytes), image_format="bmp", width=max(0, width), height=max(0, height))  # 新增代码+Phase56RealScreenshotPipeline: 返回格式不支持；如果没有这行代码，调用方不知道为何失败。
        bytes_per_pixel = bits_per_pixel // 8  # 新增代码+Phase56RealScreenshotPipeline: 计算每像素字节数；如果没有这行代码，采样偏移无法计算。
        row_stride = ((width * bits_per_pixel + 31) // 32) * 4  # 新增代码+Phase56RealScreenshotPipeline: 计算 BMP 行对齐跨度；如果没有这行代码，24-bit BMP 行尾 padding 会被读错。
        pixel_bytes_needed = pixel_offset + row_stride * height  # 新增代码+Phase56RealScreenshotPipeline: 计算像素区需要的总长度；如果没有这行代码，短文件可能越界。
        if pixel_offset <= 0 or pixel_bytes_needed > len(raw_bytes):  # 新增代码+Phase56RealScreenshotPipeline: 检查像素区是否完整；如果没有这行代码，坏 artifact 会通过头部检查。
            return self._base_report(False, "BMP 像素区不完整。", bytes_length=len(raw_bytes), image_format="bmp", width=width, height=height)  # 新增代码+Phase56RealScreenshotPipeline: 返回像素区不完整；如果没有这行代码，失败原因不明确。
        sampled_colors = self._sample_bmp_colors(raw_bytes, pixel_offset, width, height, row_stride, bytes_per_pixel, signed_height)  # 新增代码+Phase56RealScreenshotPipeline: 采样整图颜色；如果没有这行代码，黑屏/白屏无法判断。
        title_colors = self._sample_bmp_title_colors(raw_bytes, pixel_offset, width, height, row_stride, bytes_per_pixel, signed_height)  # 新增代码+Phase56RealScreenshotPipeline: 采样顶部标题区域；如果没有这行代码，标题栏可见性无法判断。
        unique_colors = set(sampled_colors)  # 新增代码+Phase56RealScreenshotPipeline: 统计整图唯一颜色；如果没有这行代码，颜色多样性无法计算。
        unique_title_colors = set(title_colors)  # 新增代码+Phase56RealScreenshotPipeline: 统计标题区域唯一颜色；如果没有这行代码，标题区域是否单调不可见。
        all_black = bool(sampled_colors) and all(color == (0, 0, 0) for color in sampled_colors)  # 新增代码+Phase56RealScreenshotPipeline: 判断是否全黑；如果没有这行代码，黑屏可能误过。
        all_white = bool(sampled_colors) and all(color == (255, 255, 255) for color in sampled_colors)  # 新增代码+Phase56RealScreenshotPipeline: 判断是否全白；如果没有这行代码，空白图可能误过。
        dimension_matches = (expected_width <= 0 or expected_width == width) and (expected_height <= 0 or expected_height == height)  # 新增代码+Phase56RealScreenshotPipeline: 检查尺寸是否符合 provider 报告；如果没有这行代码，裁剪或坏尺寸不会暴露。
        title_region_visible = len(unique_title_colors) >= 2 and height >= 40 and width >= 80  # 新增代码+Phase56RealScreenshotPipeline: 判断标题区存在颜色差异且尺寸像窗口；如果没有这行代码，纯内容裁剪也可能误过。
        passed = bool(dimension_matches and sampled_colors and not all_black and not all_white and len(unique_colors) >= self.min_unique_colors and title_region_visible)  # 新增代码+Phase56RealScreenshotPipeline: 汇总强验真条件；如果没有这行代码，失败图可能被当成功。
        reason = "pixel guard passed." if passed else "pixel guard failed: blank, monochrome, bad dimensions, or missing title region."  # 新增代码+Phase56RealScreenshotPipeline: 生成人类可读原因；如果没有这行代码，用户看不懂失败项。
        return self._base_report(passed, reason, artifact_openable=True, dimension_matches=dimension_matches, non_empty_pixels=bool(sampled_colors), all_black=all_black, all_white=all_white, unique_color_count=len(unique_colors), title_region_visible=title_region_visible, width=width, height=height, bytes_length=len(raw_bytes), image_format="bmp", bits_per_pixel=bits_per_pixel, title_unique_color_count=len(unique_title_colors))  # 新增代码+Phase56RealScreenshotPipeline: 返回完整 BMP guard 报告；如果没有这行代码，pipeline 无法带出像素证据。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，Phase56PixelGuard._inspect_bmp 到此结束；如果没有这个边界说明，初学者不容易看出 BMP 解析范围。

    def _sample_bmp_colors(self, raw_bytes: bytes, pixel_offset: int, width: int, height: int, row_stride: int, bytes_per_pixel: int, signed_height: int) -> list[tuple[int, int, int]]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，采样整图像素；如果没有这段函数，颜色检测会全量扫描大图。
        pixel_count = width * height  # 新增代码+Phase56RealScreenshotPipeline: 计算总像素；如果没有这行代码，采样步长无法确定。
        step = max(1, pixel_count // self.max_sample_pixels)  # 新增代码+Phase56RealScreenshotPipeline: 计算采样步长；如果没有这行代码，大截图可能扫描过慢。
        colors: list[tuple[int, int, int]] = []  # 新增代码+Phase56RealScreenshotPipeline: 准备颜色列表；如果没有这行代码，采样结果没有容器。
        for pixel_index in range(0, pixel_count, step):  # 新增代码+Phase56RealScreenshotPipeline: 按步长采样像素；如果没有这行代码，颜色列表永远为空。
            logical_y = pixel_index // width  # 新增代码+Phase56RealScreenshotPipeline: 计算逻辑 y；如果没有这行代码，无法定位行。
            x = pixel_index % width  # 新增代码+Phase56RealScreenshotPipeline: 计算 x；如果没有这行代码，无法定位列。
            colors.append(self._bmp_color_at(raw_bytes, pixel_offset, width, height, row_stride, bytes_per_pixel, signed_height, x, logical_y))  # 新增代码+Phase56RealScreenshotPipeline: 读取单点颜色；如果没有这行代码，采样没有实际像素。
        return colors  # 新增代码+Phase56RealScreenshotPipeline: 返回采样颜色；如果没有这行代码，调用方拿不到颜色列表。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，Phase56PixelGuard._sample_bmp_colors 到此结束；如果没有这个边界说明，初学者不容易看出整图采样范围。

    def _sample_bmp_title_colors(self, raw_bytes: bytes, pixel_offset: int, width: int, height: int, row_stride: int, bytes_per_pixel: int, signed_height: int) -> list[tuple[int, int, int]]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，采样顶部标题区域；如果没有这段函数，窗口标题栏是否被截到无法判断。
        title_height = max(1, height // 5)  # 新增代码+Phase56RealScreenshotPipeline: 取顶部 20% 作为标题区近似；如果没有这行代码，标题区域范围不稳定。
        x_step = max(1, width // 64)  # 新增代码+Phase56RealScreenshotPipeline: 控制横向采样密度；如果没有这行代码，宽窗口扫描会浪费。
        y_step = max(1, title_height // 16)  # 新增代码+Phase56RealScreenshotPipeline: 控制纵向采样密度；如果没有这行代码，标题区扫描会过密。
        colors: list[tuple[int, int, int]] = []  # 新增代码+Phase56RealScreenshotPipeline: 准备标题区颜色列表；如果没有这行代码，标题采样没有容器。
        for logical_y in range(0, title_height, y_step):  # 新增代码+Phase56RealScreenshotPipeline: 遍历标题区行；如果没有这行代码，标题区没有纵向采样。
            for x in range(0, width, x_step):  # 新增代码+Phase56RealScreenshotPipeline: 遍历标题区列；如果没有这行代码，标题区没有横向采样。
                colors.append(self._bmp_color_at(raw_bytes, pixel_offset, width, height, row_stride, bytes_per_pixel, signed_height, x, logical_y))  # 新增代码+Phase56RealScreenshotPipeline: 读取标题区单点颜色；如果没有这行代码，标题可见性无法判断。
        return colors  # 新增代码+Phase56RealScreenshotPipeline: 返回标题区颜色；如果没有这行代码，调用方拿不到标题采样结果。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，Phase56PixelGuard._sample_bmp_title_colors 到此结束；如果没有这个边界说明，初学者不容易看出标题采样范围。

    def _bmp_color_at(self, raw_bytes: bytes, pixel_offset: int, width: int, height: int, row_stride: int, bytes_per_pixel: int, signed_height: int, x: int, logical_y: int) -> tuple[int, int, int]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，读取 BMP 单点 RGB；如果没有这段函数，top-down/bottom-up 坐标会重复出错。
        stored_y = logical_y if signed_height < 0 else height - 1 - logical_y  # 新增代码+Phase56RealScreenshotPipeline: 处理 top-down 和 bottom-up BMP；如果没有这行代码，标题区会被读成底部区域。
        offset = pixel_offset + stored_y * row_stride + max(0, min(width - 1, int(x))) * bytes_per_pixel  # 新增代码+Phase56RealScreenshotPipeline: 计算像素偏移；如果没有这行代码，无法定位目标像素。
        blue = raw_bytes[offset]  # 新增代码+Phase56RealScreenshotPipeline: 读取蓝色通道；如果没有这行代码，RGB 颜色不完整。
        green = raw_bytes[offset + 1]  # 新增代码+Phase56RealScreenshotPipeline: 读取绿色通道；如果没有这行代码，RGB 颜色不完整。
        red = raw_bytes[offset + 2]  # 新增代码+Phase56RealScreenshotPipeline: 读取红色通道；如果没有这行代码，RGB 颜色不完整。
        return (int(red), int(green), int(blue))  # 新增代码+Phase56RealScreenshotPipeline: 返回 RGB 元组；如果没有这行代码，颜色统计无法进行。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，Phase56PixelGuard._bmp_color_at 到此结束；如果没有这个边界说明，初学者不容易看出单点读取范围。
# 新增代码+Phase56RealScreenshotPipeline: 类段结束，Phase56PixelGuard 到此结束；如果没有这个边界说明，初学者不容易看出像素守卫类范围。


def _provider_status(provider: Any) -> dict[str, Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，安全读取 provider.status；如果没有这段函数，坏 provider 会拖垮状态输出。
    if hasattr(provider, "status"):  # 新增代码+Phase56RealScreenshotPipeline: 检查 provider 是否有 status；如果没有这行代码，普通对象会触发 AttributeError。
        status = provider.status()  # 新增代码+Phase56RealScreenshotPipeline: 调用 provider 状态；如果没有这行代码，provider 链不可见。
        return dict(status) if isinstance(status, dict) else {}  # 新增代码+Phase56RealScreenshotPipeline: 只接受 dict 状态；如果没有这行代码，异常返回类型会污染状态。
    return {}  # 新增代码+Phase56RealScreenshotPipeline: 无 status 时返回空字典；如果没有这行代码，调用方需要自己兜底。
# 新增代码+Phase56RealScreenshotPipeline: 函数段结束，_provider_status 到此结束；如果没有这个边界说明，初学者不容易看出状态读取范围。


def _provider_name(provider: Any, fallback: str = "unknown_capture_provider") -> str:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，提取 provider 名称；如果没有这段函数，审计里的 provider 字段不稳定。
    status = _provider_status(provider)  # 新增代码+Phase56RealScreenshotPipeline: 读取 provider 状态；如果没有这行代码，无法复用 backend/name。
    return str(status.get("backend") or status.get("name") or fallback)  # 新增代码+Phase56RealScreenshotPipeline: 返回 provider 名称；如果没有这行代码，fallback 来源不可见。
# 新增代码+Phase56RealScreenshotPipeline: 函数段结束，_provider_name 到此结束；如果没有这个边界说明，初学者不容易看出名称提取范围。


def _default_phase56_providers(platform: str) -> list[Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，构造 WGC 优先、GDI 兜底 provider 链；如果没有这段函数，生产和测试入口会重复拼接。
    return [WindowsGraphicsCaptureProvider(platform=platform), Win32GdiWindowCaptureProvider(platform=platform)]  # 新增代码+Phase56RealScreenshotPipeline: 返回默认截图 provider 顺序；如果没有这行代码，Phase56 不能保持 WGC-first 策略。
# 新增代码+Phase56RealScreenshotPipeline: 函数段结束，_default_phase56_providers 到此结束；如果没有这个边界说明，初学者不容易看出默认 provider 范围。


def _coerce_capture_result(raw_result: Any, backend: str) -> NativeWindowCaptureResult:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，把 provider 输出转成统一截图结果；如果没有这段函数，WGC/GDI/fake 返回结构会分裂。
    if isinstance(raw_result, NativeWindowCaptureResult):  # 新增代码+Phase56RealScreenshotPipeline: 识别标准结果对象；如果没有这行代码，既有 provider 会被误判坏结果。
        return raw_result  # 新增代码+Phase56RealScreenshotPipeline: 原样返回标准结果；如果没有这行代码，成功截图字段可能被丢失。
    if isinstance(raw_result, dict):  # 新增代码+Phase56RealScreenshotPipeline: 支持 dict 结果；如果没有这行代码，未来外部 helper 接入成本更高。
        return NativeWindowCaptureResult(captured=bool(raw_result.get("captured", False)), screenshot_bytes=bytes(raw_result.get("screenshot_bytes", b"")), screenshot_format=str(raw_result.get("screenshot_format", "")), screenshot_width=int(raw_result.get("screenshot_width", 0) or 0), screenshot_height=int(raw_result.get("screenshot_height", 0) or 0), backend=backend, reason=str(raw_result.get("reason", "")))  # 新增代码+Phase56RealScreenshotPipeline: 将 dict 转为统一结果；如果没有这行代码，evidence store 无法稳定读字段。
    return NativeWindowCaptureResult(captured=False, backend=backend, reason="provider 返回了不支持的截图结果类型。")  # 新增代码+Phase56RealScreenshotPipeline: 不支持类型时诚实失败；如果没有这行代码，坏结果可能伪装为空成功。
# 新增代码+Phase56RealScreenshotPipeline: 函数段结束，_coerce_capture_result 到此结束；如果没有这个边界说明，初学者不容易看出结果转换范围。


class WindowsRealScreenshotPipeline:  # 新增代码+Phase56RealScreenshotPipeline: 类段开始，统一 provider 链、pixel guard 和 evidence；如果没有这个类，真实截图验收会散落。
    def __init__(self, providers: list[Any] | None = None, evidence_root: Path | str | None = None, evidence_store: Any | None = None, pixel_guard: Phase56PixelGuard | None = None, platform: str | None = None) -> None:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，初始化 pipeline；如果没有这段函数，调用方无法注入 provider 或隔离 evidence。
        self.platform = platform or sys.platform  # 新增代码+Phase56RealScreenshotPipeline: 保存平台；如果没有这行代码，非 Windows 拒绝路径无法测试。
        self.providers = list(providers) if providers is not None else _default_phase56_providers(self.platform)  # 新增代码+Phase56RealScreenshotPipeline: 保存 provider 链；如果没有这行代码，pipeline 没有截图来源。
        self.evidence_store = evidence_store or ComputerUseEvidenceStore(evidence_root=Path(evidence_root) if evidence_root is not None else None)  # 新增代码+Phase56RealScreenshotPipeline: 保存 evidence store；如果没有这行代码，截图无法写入 artifact。
        self.pixel_guard = pixel_guard or Phase56PixelGuard()  # 新增代码+Phase56RealScreenshotPipeline: 保存像素守卫；如果没有这行代码，截图成功无法验真。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，WindowsRealScreenshotPipeline.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，返回 pipeline 状态；如果没有这段函数，/computer 和 helper health 看不到 Phase56 链路。
        provider_statuses = []  # 新增代码+Phase56RealScreenshotPipeline: 准备 provider 状态列表；如果没有这行代码，状态没有容器。
        for provider in self.providers:  # 新增代码+Phase56RealScreenshotPipeline: 遍历 provider 链；如果没有这行代码，WGC/GDI 状态无法逐项展示。
            status = _provider_status(provider)  # 新增代码+Phase56RealScreenshotPipeline: 读取单个 provider 状态；如果没有这行代码，坏 provider 会中断状态。
            status.setdefault("backend", _provider_name(provider))  # 新增代码+Phase56RealScreenshotPipeline: 确保 backend 字段存在；如果没有这行代码，状态消费端不知道 provider 名。
            provider_statuses.append(status)  # 新增代码+Phase56RealScreenshotPipeline: 追加状态；如果没有这行代码，provider 状态列表会为空。
        return {"marker": PHASE56_WINDOWS_REAL_SCREENSHOT_MARKER, "model": PHASE56_REAL_SCREENSHOT_MODEL, "platform": self.platform, "provider_count": len(provider_statuses), "providers": provider_statuses, "pixel_guard": {"model": "phase56_bmp_pixel_guard", "min_unique_colors": self.pixel_guard.min_unique_colors}, "evidence_root": str(self.evidence_store.evidence_root), "actions_expanded": PHASE56_ACTIONS_EXPANDED}  # 新增代码+Phase56RealScreenshotPipeline: 返回完整状态；如果没有这行代码，截图 pipeline 没有统一事实源。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，WindowsRealScreenshotPipeline.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def _failure(self, reason: str, attempts: list[dict[str, Any]] | None = None, guard_report: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，构造失败响应；如果没有这段函数，失败分支字段会漂移。
        guard = dict(guard_report or {})  # 新增代码+Phase56RealScreenshotPipeline: 复制 guard 报告；如果没有这行代码，调用方可能修改内部对象。
        return {"marker": PHASE56_WINDOWS_REAL_SCREENSHOT_MARKER, "model": PHASE56_REAL_SCREENSHOT_MODEL, "captured": False, "provider": "", "provider_attempts": list(attempts or []), "reason": str(reason), "screenshot_captured": False, "screenshot_path": "", "screenshot_bytes_included": False, "pixel_guard": guard, "pixel_guard_passed": False, "artifact_openable": False, "image_results": [], "image_result_count": 0, "actions_expanded": PHASE56_ACTIONS_EXPANDED}  # 新增代码+Phase56RealScreenshotPipeline: 返回统一失败结构；如果没有这行代码，上层无法稳定读取失败原因。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，WindowsRealScreenshotPipeline._failure 到此结束；如果没有这个边界说明，初学者不容易看出失败响应范围。

    def _save_success(self, window: dict[str, Any], capture: NativeWindowCaptureResult, attempts: list[dict[str, Any]], guard_report: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，保存通过 pixel guard 的截图；如果没有这段函数，成功截图只能停留在内存。
        payload = WindowObservationPayload(screenshot_bytes=capture.screenshot_bytes, screenshot_format=capture.screenshot_format, screenshot_width=capture.screenshot_width, screenshot_height=capture.screenshot_height, helper_name=PHASE56_REAL_SCREENSHOT_MODEL, helper_available=True, helper_reason=f"{capture.backend}:{capture.reason}; pixel_guard={guard_report.get('reason', '')}")  # 新增代码+Phase56RealScreenshotPipeline: 构造只含截图的 observation payload；如果没有这行代码，evidence store 无法保存 artifact。
        evidence = self.evidence_store.save_window_state(window=window, payload=payload, fallback_width=capture.screenshot_width, fallback_height=capture.screenshot_height)  # 新增代码+Phase56RealScreenshotPipeline: 保存截图和 metadata；如果没有这行代码，真实验收拿不到可打开文件。
        result = dict(evidence)  # 新增代码+Phase56RealScreenshotPipeline: 复制 evidence 结果便于追加 Phase56 字段；如果没有这行代码，直接修改可能污染 store 返回值。
        result["marker"] = PHASE56_WINDOWS_REAL_SCREENSHOT_MARKER  # 新增代码+Phase56RealScreenshotPipeline: 写入 Phase56 marker；如果没有这行代码，验收无法识别本阶段输出。
        result["model"] = PHASE56_REAL_SCREENSHOT_MODEL  # 新增代码+Phase56RealScreenshotPipeline: 写入模型名；如果没有这行代码，后续兼容层无法区分协议版本。
        result["captured"] = True  # 新增代码+Phase56RealScreenshotPipeline: 标记截图成功；如果没有这行代码，上层只能猜测 screenshot_captured。
        result["provider"] = capture.backend  # 新增代码+Phase56RealScreenshotPipeline: 记录成功 provider；如果没有这行代码，审计不知道 WGC/GDI 谁成功。
        result["provider_attempts"] = list(attempts)  # 新增代码+Phase56RealScreenshotPipeline: 记录 provider 尝试链；如果没有这行代码，fallback 是否发生不可复盘。
        result["pixel_guard"] = dict(guard_report)  # 新增代码+Phase56RealScreenshotPipeline: 附加完整像素报告；如果没有这行代码，截图可信原因不可审计。
        result["pixel_guard_passed"] = bool(guard_report.get("passed"))  # 新增代码+Phase56RealScreenshotPipeline: 附加 guard 通过布尔值；如果没有这行代码，上层需要解析嵌套报告。
        result["artifact_openable"] = bool(guard_report.get("artifact_openable") and result.get("screenshot_path") and Path(str(result.get("screenshot_path"))).exists())  # 新增代码+Phase56RealScreenshotPipeline: 检查 artifact 确实存在且可解析；如果没有这行代码，路径存在和图片可用会混淆。
        result["screenshot_bytes_included"] = False  # 新增代码+Phase56RealScreenshotPipeline: 明确 JSON 不含原始 bytes；如果没有这行代码，IPC 安全边界不可见。
        result["actions_expanded"] = PHASE56_ACTIONS_EXPANDED  # 新增代码+Phase56RealScreenshotPipeline: 写入动作边界；如果没有这行代码，安全验收无法确认未扩大写动作。
        return result  # 新增代码+Phase56RealScreenshotPipeline: 返回成功摘要；如果没有这行代码，调用方拿不到截图结果。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，WindowsRealScreenshotPipeline._save_success 到此结束；如果没有这个边界说明，初学者不容易看出成功保存范围。

    def capture_window(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，对窗口执行只读截图和像素验真；如果没有这段函数，pipeline 只有状态没有行为。
        safe_window = dict(window or {})  # 新增代码+Phase56RealScreenshotPipeline: 复制窗口输入避免污染调用方对象；如果没有这行代码，后续追加字段可能改到外部状态。
        if self.platform != "win32":  # 新增代码+Phase56RealScreenshotPipeline: 非 Windows 平台拒绝真实截图；如果没有这行代码，跨平台测试会误触 Win32 API。
            return self._failure("当前平台不是 Windows，未调用真实截图 provider。")  # 新增代码+Phase56RealScreenshotPipeline: 返回平台拒绝；如果没有这行代码，用户不知道为什么没有截图。
        hwnd = parse_hwnd_from_window(safe_window)  # 新增代码+Phase56RealScreenshotPipeline: 解析窗口句柄；如果没有这行代码，provider 不知道目标窗口。
        if hwnd <= 0:  # 新增代码+Phase56RealScreenshotPipeline: 检查 hwnd 是否有效；如果没有这行代码，0 句柄可能传给系统 API。
            return self._failure("窗口句柄无效，未截图。")  # 新增代码+Phase56RealScreenshotPipeline: 返回坏 hwnd；如果没有这行代码，错误目标不可解释。
        attempts: list[dict[str, Any]] = []  # 新增代码+Phase56RealScreenshotPipeline: 准备 provider 尝试记录；如果没有这行代码，fallback 过程无法审计。
        last_guard: dict[str, Any] | None = None  # 新增代码+Phase56RealScreenshotPipeline: 保存最后一次 guard 报告；如果没有这行代码，全失败时无法解释像素失败原因。
        for provider in self.providers:  # 新增代码+Phase56RealScreenshotPipeline: 按顺序尝试 WGC/GDI provider；如果没有这行代码，只能使用单一截图来源。
            backend = _provider_name(provider)  # 新增代码+Phase56RealScreenshotPipeline: 读取 provider 名；如果没有这行代码，attempt 记录缺来源。
            try:  # 新增代码+Phase56RealScreenshotPipeline: 捕获 provider 调用异常；如果没有这行代码，权限或窗口状态异常会拖垮 agent。
                capture = _coerce_capture_result(provider.capture_window(hwnd), backend)  # 新增代码+Phase56RealScreenshotPipeline: 调用 provider 并统一结果；如果没有这行代码，截图 provider 链不会执行。
            except Exception as error:  # 新增代码+Phase56RealScreenshotPipeline: 捕获 provider 异常；如果没有这行代码，单个 provider 失败会阻止 fallback。
                capture = NativeWindowCaptureResult(captured=False, backend=backend, reason=f"provider 调用失败：{type(error).__name__}")  # 新增代码+Phase56RealScreenshotPipeline: 把异常转成失败结果；如果没有这行代码，失败原因不稳定。
            attempt = {"provider": backend, "captured": bool(capture.captured), "reason": capture.reason, "pixel_guard_passed": False}  # 新增代码+Phase56RealScreenshotPipeline: 初始化本次 provider 尝试记录；如果没有这行代码，审计看不到像素检测结果。
            if bool(capture.captured and capture.screenshot_bytes):  # 新增代码+Phase56RealScreenshotPipeline: 只有成功且有 bytes 才进入 pixel guard；如果没有这行代码，空截图可能被保存。
                last_guard = self.pixel_guard.inspect_bytes(capture.screenshot_bytes, capture.screenshot_format, expected_width=capture.screenshot_width, expected_height=capture.screenshot_height)  # 新增代码+Phase56RealScreenshotPipeline: 对截图 bytes 做像素验真；如果没有这行代码，黑屏/空白无法拦截。
                attempt["pixel_guard_passed"] = bool(last_guard.get("passed"))  # 新增代码+Phase56RealScreenshotPipeline: 记录 guard 是否通过；如果没有这行代码，attempt 不知道失败是 provider 还是像素。
                attempt["pixel_guard_reason"] = str(last_guard.get("reason", ""))  # 新增代码+Phase56RealScreenshotPipeline: 记录 guard 原因；如果没有这行代码，fallback 复盘缺少细节。
                attempts.append(attempt)  # 新增代码+Phase56RealScreenshotPipeline: 保存本次尝试；如果没有这行代码，成功前的 provider 过程不可见。
                if bool(last_guard.get("passed")):  # 新增代码+Phase56RealScreenshotPipeline: 只接受通过 guard 的截图；如果没有这行代码，空白图也会落盘。
                    return self._save_success(safe_window, capture, attempts, last_guard)  # 新增代码+Phase56RealScreenshotPipeline: 保存并返回可信截图；如果没有这行代码，成功截图无法形成 artifact。
                continue  # 新增代码+Phase56RealScreenshotPipeline: guard 失败时尝试下一个 provider；如果没有这行代码，WGC 黑屏时不会 fallback 到 GDI。
            attempts.append(attempt)  # 新增代码+Phase56RealScreenshotPipeline: 保存失败或无 bytes 的 provider 尝试；如果没有这行代码，失败链路不可见。
        return self._failure("所有截图 provider 都未产生通过 pixel guard 的窗口截图。", attempts, last_guard)  # 新增代码+Phase56RealScreenshotPipeline: 全部失败时返回统一失败；如果没有这行代码，调用方拿不到失败摘要。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，WindowsRealScreenshotPipeline.capture_window 到此结束；如果没有这个边界说明，初学者不容易看出截图流程范围。
# 新增代码+Phase56RealScreenshotPipeline: 类段结束，WindowsRealScreenshotPipeline 到此结束；如果没有这个边界说明，初学者不容易看出 pipeline 类范围。


class Phase56NotepadSafeWindowLauncher:  # 新增代码+Phase56RealScreenshotPipeline: 类段开始，启动只属于 Phase56 的安全 Notepad 窗口；如果没有这个类，真实截图 smoke 可能误选用户窗口。
    def __init__(self, marker_text: str = "LearningAgent Phase56 real screenshot smoke") -> None:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，初始化安全窗口内容；如果没有这段函数，临时文件和进程状态没有归属。
        self.marker_text = marker_text  # 新增代码+Phase56RealScreenshotPipeline: 保存写入文件的标记文本；如果没有这行代码，Notepad 内容不易识别。
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None  # 新增代码+Phase56RealScreenshotPipeline: 保存临时目录对象；如果没有这行代码，cleanup 无法删除文件。
        self._process: subprocess.Popen[Any] | None = None  # 新增代码+Phase56RealScreenshotPipeline: 保存 Notepad 进程；如果没有这行代码，cleanup 无法关闭安全窗口。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，Phase56NotepadSafeWindowLauncher.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def launch(self) -> dict[str, Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，创建临时文件并启动 Notepad；如果没有这段函数，真实 smoke 没有截图目标。
        self._temp_dir = tempfile.TemporaryDirectory(prefix="learning-agent-phase56-")  # 新增代码+Phase56RealScreenshotPipeline: 创建隔离临时目录；如果没有这行代码，测试文件可能散落到项目或用户目录。
        file_path = Path(self._temp_dir.name) / "LearningAgent-Phase56-RealScreenshotSmoke.txt"  # 新增代码+Phase56RealScreenshotPipeline: 固定临时文件名作为标题线索；如果没有这行代码，inventory 很难可靠定位窗口。
        file_path.write_text(self.marker_text + "\nPixel guard needs title and text contrast.\n", encoding="utf-8")  # 新增代码+Phase56RealScreenshotPipeline: 写入可见文本制造非空像素；如果没有这行代码，Notepad 内容可能太空白。
        self._process = subprocess.Popen(["notepad.exe", str(file_path)])  # 新增代码+Phase56RealScreenshotPipeline: 启动 Notepad 打开临时文件；如果没有这行代码，真实桌面不会出现安全窗口。
        return {"title_hint": file_path.name, "file_path": str(file_path)}  # 新增代码+Phase56RealScreenshotPipeline: 返回标题线索和文件路径；如果没有这行代码，poll 无法只找自有窗口。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，Phase56NotepadSafeWindowLauncher.launch 到此结束；如果没有这个边界说明，初学者不容易看出启动范围。

    def cleanup(self) -> bool:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，关闭 Notepad 并删除临时目录；如果没有这段函数，smoke 可能留下窗口和文件。
        cleaned = False  # 新增代码+Phase56RealScreenshotPipeline: 初始化清理状态；如果没有这行代码，返回值无法说明是否执行清理。
        process = self._process  # 新增代码+Phase56RealScreenshotPipeline: 保存进程引用；如果没有这行代码，后续会重复访问可变属性。
        if process is not None and process.poll() is None:  # 新增代码+Phase56RealScreenshotPipeline: 只关闭仍在运行的 Notepad；如果没有这行代码，已退出进程可能触发无意义错误。
            process.terminate()  # 新增代码+Phase56RealScreenshotPipeline: 请求 Notepad 正常退出；如果没有这行代码，安全窗口会残留。
            try:  # 新增代码+Phase56RealScreenshotPipeline: 捕获等待超时；如果没有这行代码，Notepad 关闭慢会中断清理。
                process.wait(timeout=3)  # 新增代码+Phase56RealScreenshotPipeline: 等待进程退出；如果没有这行代码，临时文件可能仍被占用。
            except subprocess.TimeoutExpired:  # 新增代码+Phase56RealScreenshotPipeline: 处理关闭超时；如果没有这行代码，超时窗口会残留。
                process.kill()  # 新增代码+Phase56RealScreenshotPipeline: 强制结束测试窗口；如果没有这行代码，超时后窗口仍可能残留。
                process.wait(timeout=3)  # 新增代码+Phase56RealScreenshotPipeline: 等待强制结束完成；如果没有这行代码，资源释放状态不确定。
            cleaned = True  # 新增代码+Phase56RealScreenshotPipeline: 标记已处理进程；如果没有这行代码，结果无法说明窗口已清理。
        if self._temp_dir is not None:  # 新增代码+Phase56RealScreenshotPipeline: 检查临时目录是否存在；如果没有这行代码，空 cleanup 会访问 None。
            self._temp_dir.cleanup()  # 新增代码+Phase56RealScreenshotPipeline: 删除临时目录；如果没有这行代码，磁盘会留下 smoke 文件。
            self._temp_dir = None  # 新增代码+Phase56RealScreenshotPipeline: 清空临时目录引用；如果没有这行代码，重复 cleanup 可能再次清理同一对象。
            cleaned = True  # 新增代码+Phase56RealScreenshotPipeline: 标记已清理文件；如果没有这行代码，结果可能误报未清理。
        return cleaned  # 新增代码+Phase56RealScreenshotPipeline: 返回清理状态；如果没有这行代码，smoke 报告无法审计善后。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，Phase56NotepadSafeWindowLauncher.cleanup 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。
# 新增代码+Phase56RealScreenshotPipeline: 类段结束，Phase56NotepadSafeWindowLauncher 到此结束；如果没有这个边界说明，初学者不容易看出安全窗口 launcher 范围。


def _find_phase56_safe_window(windows: list[dict[str, Any]], title_hint: str) -> dict[str, Any] | None:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，从窗口列表找自有 Notepad；如果没有这段函数，smoke 可能误选用户窗口。
    lowered_hint = str(title_hint or "").lower()  # 新增代码+Phase56RealScreenshotPipeline: 标题线索转小写；如果没有这行代码，大小写差异可能导致找不到窗口。
    for window in windows:  # 新增代码+Phase56RealScreenshotPipeline: 遍历窗口列表；如果没有这行代码，无法搜索目标窗口。
        title = str(window.get("title_preview", window.get("title", ""))).lower()  # 新增代码+Phase56RealScreenshotPipeline: 读取窗口标题摘要；如果没有这行代码，无法匹配 Notepad 文件名。
        if lowered_hint and lowered_hint in title:  # 新增代码+Phase56RealScreenshotPipeline: 只接受包含自有文件名的窗口；如果没有这行代码，可能误截图其他窗口。
            return dict(window)  # 新增代码+Phase56RealScreenshotPipeline: 返回窗口副本；如果没有这行代码，调用方可能修改 inventory 原始对象。
    return None  # 新增代码+Phase56RealScreenshotPipeline: 找不到时返回 None；如果没有这行代码，调用方无法区分未找到和异常。
# 新增代码+Phase56RealScreenshotPipeline: 函数段结束，_find_phase56_safe_window 到此结束；如果没有这个边界说明，初学者不容易看出安全窗口匹配范围。


def _poll_phase56_safe_window(inventory: Any, title_hint: str, timeout_seconds: float, poll_interval_seconds: float) -> dict[str, Any] | None:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，轮询等待 Notepad 出现；如果没有这段函数，窗口启动稍慢会误失败。
    deadline = time.time() + max(0.5, float(timeout_seconds))  # 新增代码+Phase56RealScreenshotPipeline: 计算超时截止时间；如果没有这行代码，等待可能无限持续或立即失败。
    while time.time() <= deadline:  # 新增代码+Phase56RealScreenshotPipeline: 在截止前重复检查；如果没有这行代码，异步窗口创建无法等待。
        snapshot = inventory.snapshot()  # 新增代码+Phase56RealScreenshotPipeline: 获取窗口快照；如果没有这行代码，无法看到 Notepad 是否出现。
        window = _find_phase56_safe_window(list(getattr(snapshot, "windows", []) or []), title_hint)  # 新增代码+Phase56RealScreenshotPipeline: 查找自有安全窗口；如果没有这行代码，后续截图没有可信 hwnd。
        if window is not None:  # 新增代码+Phase56RealScreenshotPipeline: 判断是否找到窗口；如果没有这行代码，找到后仍会继续等待。
            return window  # 新增代码+Phase56RealScreenshotPipeline: 返回目标窗口；如果没有这行代码，调用方拿不到 hwnd。
        time.sleep(max(0.05, float(poll_interval_seconds)))  # 新增代码+Phase56RealScreenshotPipeline: 短暂等待后重试；如果没有这行代码，轮询会占满 CPU。
    return None  # 新增代码+Phase56RealScreenshotPipeline: 超时返回未找到；如果没有这行代码，调用方无法输出定位失败。
# 新增代码+Phase56RealScreenshotPipeline: 函数段结束，_poll_phase56_safe_window 到此结束；如果没有这个边界说明，初学者不容易看出轮询范围。


def run_phase56_real_screenshot_smoke(platform: str | None = None, inventory_factory: Any | None = None, launcher: Any | None = None, evidence_root: Path | str | None = None, timeout_seconds: float = 8.0, poll_interval_seconds: float = 0.25) -> dict[str, Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，运行真实安全窗口截图 smoke；如果没有这段函数，Phase56 无法生成真实 artifact。
    current_platform = platform or sys.platform  # 新增代码+Phase56RealScreenshotPipeline: 确定平台；如果没有这行代码，测试无法注入平台。
    if current_platform != "win32":  # 新增代码+Phase56RealScreenshotPipeline: 非 Windows 直接诚实返回；如果没有这行代码，跨平台会误触 Notepad。
        return {"real_smoke": False, "platform_supported": False, "reason": "当前平台不是 Windows，未运行真实截图 smoke。", "actions_expanded": PHASE56_ACTIONS_EXPANDED}  # 新增代码+Phase56RealScreenshotPipeline: 返回平台不支持；如果没有这行代码，失败原因不清楚。
    active_launcher = launcher or Phase56NotepadSafeWindowLauncher()  # 新增代码+Phase56RealScreenshotPipeline: 没有注入时使用真实 Notepad launcher；如果没有这行代码，生产 smoke 没有默认目标。
    target = active_launcher.launch() if hasattr(active_launcher, "launch") else active_launcher()  # 新增代码+Phase56RealScreenshotPipeline: 启动或获取安全目标；如果没有这行代码，截图没有自有窗口。
    cleaned_up = False  # 新增代码+Phase56RealScreenshotPipeline: 初始化清理状态；如果没有这行代码，finally 外无法记录 cleanup。
    try:  # 新增代码+Phase56RealScreenshotPipeline: 包住真实窗口定位和截图；如果没有这行代码，异常会绕过结构化报告和清理。
        inventory = inventory_factory() if inventory_factory is not None else WindowsWindowInventoryProbe()  # 新增代码+Phase56RealScreenshotPipeline: 创建真实或注入 inventory；如果没有这行代码，无法定位窗口。
        window = _poll_phase56_safe_window(inventory, str(target.get("title_hint", "")), timeout_seconds, poll_interval_seconds)  # 新增代码+Phase56RealScreenshotPipeline: 等待自有窗口出现；如果没有这行代码，Notepad 启动延迟会误失败。
        if window is None:  # 新增代码+Phase56RealScreenshotPipeline: 检查是否找到窗口；如果没有这行代码，后续会对空窗口截图。
            return {"real_smoke": False, "platform_supported": True, "safe_window_found": False, "reason": "未找到 Phase56 自有安全窗口，未截图。", "actions_expanded": PHASE56_ACTIONS_EXPANDED}  # 新增代码+Phase56RealScreenshotPipeline: 返回未找到结果；如果没有这行代码，定位失败不可解释。
        pipeline = WindowsRealScreenshotPipeline(evidence_root=evidence_root, platform=current_platform)  # 新增代码+Phase56RealScreenshotPipeline: 创建真实 provider pipeline；如果没有这行代码，smoke 不会走 WGC/GDI 链路。
        capture = pipeline.capture_window(window)  # 新增代码+Phase56RealScreenshotPipeline: 捕获安全窗口；如果没有这行代码，real_smoke 没有截图输入。
        artifact_exists = bool(capture.get("screenshot_path") and Path(str(capture.get("screenshot_path"))).exists())  # 新增代码+Phase56RealScreenshotPipeline: 检查截图 artifact 是否真实存在；如果没有这行代码，real_smoke 可能只证明字段存在。
        real_smoke = bool(capture.get("captured") and capture.get("pixel_guard_passed") and artifact_exists)  # 新增代码+Phase56RealScreenshotPipeline: 汇总真实 smoke 成功条件；如果没有这行代码，失败图可能误报成功。
        return {"real_smoke": real_smoke, "platform_supported": True, "safe_window_found": True, "window": window, "capture": capture, "artifact": artifact_exists, "pixel_guard": bool(capture.get("pixel_guard_passed")), "provider": capture.get("provider", ""), "screenshot_path": capture.get("screenshot_path", ""), "actions_expanded": PHASE56_ACTIONS_EXPANDED}  # 新增代码+Phase56RealScreenshotPipeline: 返回真实 smoke 报告；如果没有这行代码，CLI 无法带出真实 artifact 证据。
    except Exception as error:  # 新增代码+Phase56RealScreenshotPipeline: 捕获真实 smoke 异常；如果没有这行代码，桌面权限或 Notepad 问题会让命令崩溃。
        return {"real_smoke": False, "platform_supported": True, "safe_window_found": False, "reason": f"Phase56 真实截图 smoke 异常：{type(error).__name__}", "actions_expanded": PHASE56_ACTIONS_EXPANDED}  # 新增代码+Phase56RealScreenshotPipeline: 返回异常类型但不泄露本地细节；如果没有这行代码，用户只会看到堆栈。
    finally:  # 新增代码+Phase56RealScreenshotPipeline: 无论成功失败都清理安全窗口；如果没有这行代码，Notepad 可能残留。
        if hasattr(active_launcher, "cleanup"):  # 新增代码+Phase56RealScreenshotPipeline: 检查 launcher 是否有 cleanup；如果没有这行代码，函数式 fake launcher 会触发 AttributeError。
            cleaned_up = bool(active_launcher.cleanup())  # 新增代码+Phase56RealScreenshotPipeline: 调用 cleanup 并保存结果；如果没有这行代码，清理证据无法记录。
        _ = cleaned_up  # 新增代码+Phase56RealScreenshotPipeline: 保留清理变量避免静态误报；如果没有这行代码，后续可读性会变差。
# 新增代码+Phase56RealScreenshotPipeline: 函数段结束，run_phase56_real_screenshot_smoke 到此结束；如果没有这个边界说明，初学者不容易看出真实 smoke 范围。


def run_phase56_real_screenshot_pipeline_contract(real_smoke: bool = True) -> dict[str, Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，执行 Phase56 合同自检；如果没有这段函数，CLI 和真实终端没有统一入口。
    fake_bmp = build_phase56_test_bmp(220, 140, title_color=(20, 70, 150), body_color=(245, 245, 245), accent_color=(5, 5, 5))  # 新增代码+Phase56RealScreenshotPipeline: 构造安全 fake BMP；如果没有这行代码，pixel guard 合同没有稳定输入。
    with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase56RealScreenshotPipeline: 创建临时 evidence 目录隔离 fake 合同；如果没有这行代码，自检会污染真实 evidence。
        fake_provider = _Phase56ContractProvider("win32_gdi_printwindow", fake_bmp, 220, 140)  # 新增代码+Phase56RealScreenshotPipeline: 创建 fake GDI provider；如果没有这行代码，合同测试会碰真实桌面。
        pipeline = WindowsRealScreenshotPipeline(providers=[fake_provider], evidence_root=Path(raw_dir), platform="win32")  # 新增代码+Phase56RealScreenshotPipeline: 创建 fake pipeline；如果没有这行代码，pixel_guard/artifact 没有对象。
        fake_capture = pipeline.capture_window({"window_id": "hwnd:5601", "hwnd": 5601, "title": "Phase56 Contract Window", "rect": {"left": 0, "top": 0, "right": 220, "bottom": 140}})  # 新增代码+Phase56RealScreenshotPipeline: 执行 fake 截图；如果没有这行代码，合同无输入。
        from learning_agent.computer_use_mcp_v2.windows_runtime.native_helper_v2 import WindowsNativeHelperV2Worker  # 新增代码+Phase56RealScreenshotPipeline: 延迟导入 helper v2 避免模块循环；如果没有这行代码，合同无法证明 helper v2 capture 接入。
        helper_response = WindowsNativeHelperV2Worker(screenshot_pipeline=pipeline).handle({"op": "capture_window", "window": {"window_id": "hwnd:5601", "hwnd": 5601, "title": "Phase56 Contract Window", "rect": {"left": 0, "top": 0, "right": 220, "bottom": 140}}})  # 新增代码+Phase56RealScreenshotPipeline: 通过 helper v2 协议执行截图；如果没有这行代码，out-of-process 协议摘要可能仍是占位。
        fake_pixel_guard = bool(fake_capture.get("pixel_guard_passed"))  # 新增代码+Phase56RealScreenshotPipeline: 检查 fake 截图是否通过 guard；如果没有这行代码，pixel_guard token 没依据。
        fake_artifact = bool(fake_capture.get("screenshot_path") and Path(str(fake_capture.get("screenshot_path"))).exists())  # 新增代码+Phase56RealScreenshotPipeline: 检查 fake artifact 存在；如果没有这行代码，artifact token 可能虚报。
        helper_result = helper_response.get("result", {}) if isinstance(helper_response, dict) else {}  # 新增代码+Phase56RealScreenshotPipeline: 提取 helper 响应 result；如果没有这行代码，helper_v2_capture 难以稳定判断。
        helper_v2_capture = bool(helper_response.get("ok") and helper_result.get("captured") and helper_result.get("pixel_guard_passed"))  # 新增代码+Phase56RealScreenshotPipeline: 检查 helper v2 capture 成功；如果没有这行代码，协议接入可能漏验。
        raw_payload = json.dumps({"fake_capture": fake_capture, "helper_response": helper_response}, ensure_ascii=False, default=str)  # 新增代码+Phase56RealScreenshotPipeline: 序列化可见响应检查原始 bytes；如果没有这行代码，二进制泄露无法机器验证。
        raw_bytes_hidden = '"screenshot_bytes":' not in raw_payload and "BM\\x00" not in raw_payload  # 修改代码+Phase56RealScreenshotPipeline: 只检查真正的原始截图 bytes 字段和 BMP 内容；如果没有这行代码，安全标志 screenshot_bytes_included 会被误判为泄露。
    real_report = run_phase56_real_screenshot_smoke() if real_smoke else {"real_smoke": False, "skipped": True, "actions_expanded": PHASE56_ACTIONS_EXPANDED}  # 新增代码+Phase56RealScreenshotPipeline: 根据参数执行真实 smoke；如果没有这行代码，单测无法跳过真实桌面。
    real_artifact = bool(real_report.get("artifact") and real_report.get("screenshot_path") and Path(str(real_report.get("screenshot_path"))).exists()) if real_smoke else True  # 新增代码+Phase56RealScreenshotPipeline: 检查真实 artifact 或跳过；如果没有这行代码，真实验收可能只看布尔字段。
    pixel_guard = bool(fake_pixel_guard and (not real_smoke or real_report.get("pixel_guard")))  # 新增代码+Phase56RealScreenshotPipeline: 汇总 fake 和真实 guard；如果没有这行代码，CLI 无法表达总体像素验真。
    artifact = bool(fake_artifact and real_artifact)  # 新增代码+Phase56RealScreenshotPipeline: 汇总 fake/真实 artifact；如果没有这行代码，artifact token 可能不代表真实文件。
    passed = bool(pixel_guard and artifact and helper_v2_capture and raw_bytes_hidden and (not real_smoke or real_report.get("real_smoke")) and not PHASE56_ACTIONS_EXPANDED)  # 新增代码+Phase56RealScreenshotPipeline: 汇总通过条件；如果没有这行代码，失败也可能返回成功码。
    return {"marker": PHASE56_WINDOWS_REAL_SCREENSHOT_MARKER, "ok_token": PHASE56_WINDOWS_REAL_SCREENSHOT_OK_TOKEN, "pixel_guard": pixel_guard, "artifact": artifact, "helper_v2_capture": helper_v2_capture, "real_smoke": bool(real_report.get("real_smoke", False)), "raw_bytes_hidden": raw_bytes_hidden, "actions_expanded": PHASE56_ACTIONS_EXPANDED, "passed": passed, "real_report": real_report}  # 新增代码+Phase56RealScreenshotPipeline: 返回完整合同报告；如果没有这行代码，CLI 和测试拿不到统一结果。
# 新增代码+Phase56RealScreenshotPipeline: 函数段结束，run_phase56_real_screenshot_pipeline_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


class _Phase56ContractProvider:  # 新增代码+Phase56RealScreenshotPipeline: 类段开始，定义合同自检 fake provider；如果没有这个类，自检会触碰真实桌面。
    def __init__(self, backend: str, screenshot_bytes: bytes, width: int, height: int) -> None:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，初始化 fake provider；如果没有这段函数，自检无法提供可控截图。
        self.backend = backend  # 新增代码+Phase56RealScreenshotPipeline: 保存 provider 名；如果没有这行代码，自检结果没有来源。
        self.screenshot_bytes = bytes(screenshot_bytes)  # 新增代码+Phase56RealScreenshotPipeline: 保存截图 bytes；如果没有这行代码，provider 无图可返。
        self.width = int(width)  # 新增代码+Phase56RealScreenshotPipeline: 保存宽度；如果没有这行代码，guard 尺寸校验没有输入。
        self.height = int(height)  # 新增代码+Phase56RealScreenshotPipeline: 保存高度；如果没有这行代码，guard 尺寸校验没有输入。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，_Phase56ContractProvider.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，返回 fake provider 状态；如果没有这段函数，pipeline status 缺 provider 信息。
        return {"backend": self.backend, "available": True, "reason": "phase56 contract provider", "contract_ready": True}  # 新增代码+Phase56RealScreenshotPipeline: 返回稳定状态；如果没有这行代码，自检状态字段可能缺失。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，_Phase56ContractProvider.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def capture_window(self, hwnd: int) -> NativeWindowCaptureResult:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，返回 fake 截图；如果没有这段函数，自检无法执行 capture_window。
        return NativeWindowCaptureResult(captured=True, screenshot_bytes=self.screenshot_bytes, screenshot_format="bmp", screenshot_width=self.width, screenshot_height=self.height, backend=self.backend, reason=f"phase56 contract captured {hwnd}")  # 新增代码+Phase56RealScreenshotPipeline: 返回统一截图结果；如果没有这行代码，pipeline 没有可保存图像。
    # 新增代码+Phase56RealScreenshotPipeline: 函数段结束，_Phase56ContractProvider.capture_window 到此结束；如果没有这个边界说明，初学者不容易看出 fake 截图范围。
# 新增代码+Phase56RealScreenshotPipeline: 类段结束，_Phase56ContractProvider 到此结束；如果没有这个边界说明，初学者不容易看出合同 provider 范围。


def phase56_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，把报告转成稳定 token 行；如果没有这段函数，真实终端场景要解析复杂 JSON。
    return f"{PHASE56_WINDOWS_REAL_SCREENSHOT_OK_TOKEN} pixel_guard={_phase56_bool_token(report.get('pixel_guard'))} artifact={_phase56_bool_token(report.get('artifact'))} helper_v2_capture={_phase56_bool_token(report.get('helper_v2_capture'))} real_smoke={_phase56_bool_token(report.get('real_smoke'))} raw_bytes_hidden={_phase56_bool_token(report.get('raw_bytes_hidden'))} actions_expanded={_phase56_bool_token(report.get('actions_expanded'))} marker={PHASE56_WINDOWS_REAL_SCREENSHOT_MARKER}"  # 新增代码+Phase56RealScreenshotPipeline: 返回固定顺序 token；如果没有这行代码，验收输出容易漂移。
# 新增代码+Phase56RealScreenshotPipeline: 函数段结束，phase56_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase56RealScreenshotPipeline: 函数段开始，提供命令行入口；如果没有这段函数，真实终端无法执行 Phase56 验收。
    _ = argv  # 新增代码+Phase56RealScreenshotPipeline: 保留 argv 以便未来扩展；如果没有这行代码，静态检查可能提示未使用参数。
    report = run_phase56_real_screenshot_pipeline_contract(real_smoke=True)  # 新增代码+Phase56RealScreenshotPipeline: 执行合同和真实安全窗口截图；如果没有这行代码，CLI 不会生成真实 artifact。
    print(phase56_cli_line(report))  # 新增代码+Phase56RealScreenshotPipeline: 打印稳定 token 行；如果没有这行代码，debug log 无法确认验收结果。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase56RealScreenshotPipeline: 打印结构化报告；如果没有这行代码，失败时不易定位原因。
    print(PHASE56_WINDOWS_REAL_SCREENSHOT_MARKER)  # 新增代码+Phase56RealScreenshotPipeline: 单独打印 ready marker；如果没有这行代码，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase56RealScreenshotPipeline: 根据真实验收结果返回退出码；如果没有这行代码，真实截图失败也可能被当成功。
# 新增代码+Phase56RealScreenshotPipeline: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["PHASE56_ACTIONS_EXPANDED", "PHASE56_REAL_SCREENSHOT_MODEL", "PHASE56_WINDOWS_REAL_SCREENSHOT_MARKER", "PHASE56_WINDOWS_REAL_SCREENSHOT_OK_TOKEN", "Phase56NotepadSafeWindowLauncher", "Phase56PixelGuard", "WindowsRealScreenshotPipeline", "build_phase56_test_bmp", "main", "phase56_cli_line", "run_phase56_real_screenshot_pipeline_contract", "run_phase56_real_screenshot_smoke"]  # 新增代码+Phase56RealScreenshotPipeline: 限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase56RealScreenshotPipeline: 允许直接运行模块；如果没有这行代码，python -m 不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase56RealScreenshotPipeline: 调用 main 并传递退出码；如果没有这行代码，命令行状态不明确。
