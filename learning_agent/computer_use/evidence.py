"""Windows Computer Use 证据落盘工具。"""  # 新增代码+Phase29ComputerUse: 集中保存截图和 UIA 摘要证据；如果没有这个文件，get_window_state 只能返回内存占位，无法审计。 

from __future__ import annotations  # 新增代码+Phase29ComputerUse: 延迟解析类型注解；如果没有这行代码，旧运行入口遇到前向类型时更容易导入失败。 

import json  # 新增代码+Phase29ComputerUse: 用于写入 metadata JSON；如果没有这行代码，证据无法机器可读地落盘。 
import time  # 新增代码+Phase29ComputerUse: 用于生成证据时间戳；如果没有这行代码，证据 id 缺少时间部分。 
import uuid  # 新增代码+Phase29ComputerUse: 用于生成短随机后缀避免文件名冲突；如果没有这行代码，同一秒多次观察可能覆盖证据。 
from dataclasses import dataclass  # 新增代码+Phase29ComputerUse: 用 dataclass 表达过滤后的文本摘要；如果没有这行代码，过滤结果会变成难懂的 tuple。 
from pathlib import Path  # 新增代码+Phase29ComputerUse: 用 Path 管理证据目录和文件；如果没有这行代码，路径拼接更容易出错。 
from typing import Any  # 新增代码+Phase29ComputerUse: 支持 helper payload 和窗口 dict 的通用字段；如果没有这行代码，类型边界不清楚。 

try:  # 新增代码+Phase29ComputerUse: 包运行模式下导入文本清理 helper；如果没有这行代码，证据摘要无法复用协议清理规则。 
    from learning_agent.computer_use.models import clean_protocol_text  # 新增代码+Phase29ComputerUse: 复用 Phase 27 文本清理；如果没有这行代码，UIA 摘要可能携带换行和超长空白。 
except ModuleNotFoundError as error:  # 新增代码+Phase29ComputerUse: 捕获脚本模式下包路径不可用；如果没有这行代码，start_oauth_agent.bat 入口可能导入失败。 
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.models"}:  # 新增代码+Phase29ComputerUse: 只允许目标包路径缺失时 fallback；如果没有这行代码，真实 bug 会被误吞。 
        raise  # 新增代码+Phase29ComputerUse: 重新抛出非目标导入错误；如果没有这行代码，排查 models 内部错误会很困难。 
    from computer_use.models import clean_protocol_text  # 新增代码+Phase29ComputerUse: 脚本模式下从本地包导入清理 helper；如果没有这行代码，直接运行入口无法加载 evidence。 

try:  # 新增代码+ClaudeCodeParityScreenshot: 优先按包路径导入截图坐标映射 helper；如果没有这行代码，evidence 层无法在正常测试入口复用坐标合同。
    from learning_agent.computer_use.coordinates import SCREENSHOT_COORDINATE_MODEL, build_screenshot_coordinate_mapping  # 新增代码+ClaudeCodeParityScreenshot: 导入截图映射版本和构造函数；如果没有这行代码，result 和 metadata 无法生成 scale 元数据。
except ModuleNotFoundError as error:  # 新增代码+ClaudeCodeParityScreenshot: 捕获脚本模式下包名前缀不可用；如果没有这行代码，start_oauth_agent.bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.coordinates"}:  # 新增代码+ClaudeCodeParityScreenshot: 只允许目标坐标模块路径缺失时 fallback；如果没有这行代码，coordinates 内部真实 bug 可能被误吞。
        raise  # 新增代码+ClaudeCodeParityScreenshot: 重新抛出非目标导入错误；如果没有这行代码，截图映射问题会被隐藏成脚本路径问题。
    from computer_use.coordinates import SCREENSHOT_COORDINATE_MODEL, build_screenshot_coordinate_mapping  # 新增代码+ClaudeCodeParityScreenshot: 脚本模式导入截图坐标 helper；如果没有这行代码，直接运行 evidence.py 时无法写入映射合同。


DEFAULT_EVIDENCE_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "evidence"  # 新增代码+Phase29ComputerUse: 定义默认证据目录；如果没有这行代码，真实运行时不知道把证据保存到哪里。 
SAFE_SCREENSHOT_FORMATS = {"png", "bmp", "jpg", "jpeg"}  # 新增代码+Phase29ComputerUse: 限定允许的截图扩展名；如果没有这行代码，helper 可能传入危险或混乱的文件后缀。 
SENSITIVE_ACCESSIBILITY_KEYWORDS = ("password", "passwd", "secret", "token", "authorization", "credential", "otp", "captcha", "验证码", "密码", "密钥", "令牌", "凭据")  # 新增代码+Phase29ComputerUse: 集中定义 UIA 敏感关键词；如果没有这行代码，password/token 行可能泄露到响应和 artifact。 
PHASE41_WINDOWS_IMAGE_RESULTS_MARKER = "PHASE41_WINDOWS_IMAGE_RESULTS_READY"  # 新增代码+Phase41WindowsImageResults: 定义真实终端验收等待的固定标记；如果没有这行代码，start_oauth_agent.bat 场景无法稳定判断 Phase41 已接入。
PHASE41_WINDOWS_IMAGE_RESULTS_OK_TOKEN = "PHASE41_WINDOWS_IMAGE_RESULTS_OK"  # 新增代码+Phase41WindowsImageResults: 定义安全自检成功 token；如果没有这行代码，自动化和可见终端无法区分运行完成与真正通过。
PHASE41_IMAGE_RESULT_MODEL = "phase41_model_visible_image_results"  # 新增代码+Phase41WindowsImageResults: 定义 image_result block 的协议模型名；如果没有这行代码，后续模型消费端无法识别这个块属于哪个版本。
PHASE41_ACTIONS_EXPANDED = False  # 新增代码+Phase41WindowsImageResults: 明确 Phase41 只增加结果可见性不扩大桌面动作；如果没有这行代码，安全审计无法证明本阶段没有新增高风险能力。


@dataclass(frozen=True)  # 新增代码+Phase29ComputerUse: 让过滤结果不可变；如果没有这行代码，摘要在落盘前可能被无意修改。 
class FilteredAccessibilityText:  # 新增代码+Phase29ComputerUse: 定义过滤后的 UIA 摘要结构；如果没有这个类，调用方难以理解每个返回值含义。 
    excerpt: str  # 新增代码+Phase29ComputerUse: 保存给模型看的 bounded UIA 摘要；如果没有这行代码，响应没有可访问性文本字段。 
    truncated: bool  # 新增代码+Phase29ComputerUse: 标记摘要是否被截断；如果没有这行代码，模型不知道文本是否完整。 
    filtered_line_count: int  # 新增代码+Phase29ComputerUse: 记录被敏感词过滤的行数；如果没有这行代码，用户无法审计过滤是否发生。 


# 新增代码+Phase29ComputerUse: 函数段开始，phase29_evidence_timestamp 用于生成证据 id 时间片；如果没有这段函数，证据文件名会缺少人类可读时间，作者意图是让 evidence 文件易排序。 
def phase29_evidence_timestamp() -> str:  # 新增代码+Phase29ComputerUse: 定义证据时间戳 helper；如果没有这行代码，各处会重复写时间格式。 
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())  # 新增代码+Phase29ComputerUse: 返回适合文件名的 UTC 时间；如果没有这行代码，证据 id 可能包含不安全字符。 
# 新增代码+Phase29ComputerUse: 函数段结束，phase29_evidence_timestamp 到此结束；如果没有这个结束标记，用户不容易看出时间 helper 边界。 


# 新增代码+Phase29ComputerUse: 函数段开始，safe_screenshot_format 用于规范化截图后缀；如果没有这段函数，helper 输入可能造成奇怪文件名，作者意图是只允许常见图片扩展。 
def safe_screenshot_format(raw_format: Any) -> str:  # 新增代码+Phase29ComputerUse: 定义截图格式清理函数；如果没有这行代码，截图后缀会直接相信 helper。 
    screenshot_format = clean_protocol_text(raw_format, max_length=10).lower().lstrip(".")  # 新增代码+Phase29ComputerUse: 清理格式并移除点号；如果没有这行代码，`.PNG` 或空白格式会不稳定。 
    if screenshot_format in SAFE_SCREENSHOT_FORMATS:  # 新增代码+Phase29ComputerUse: 检查格式是否在白名单里；如果没有这行代码，未知后缀可能进入文件系统。 
        return screenshot_format  # 新增代码+Phase29ComputerUse: 返回安全格式；如果没有这行代码，白名单格式无法保留。 
    return "bin"  # 新增代码+Phase29ComputerUse: 未知格式降级为 bin；如果没有这行代码，非法格式无法安全兜底。 
# 新增代码+Phase29ComputerUse: 函数段结束，safe_screenshot_format 到此结束；如果没有这个结束标记，用户不容易看出格式清理边界。 


# 新增代码+Phase41WindowsImageResults: 函数段开始，screenshot_mime_type 用于把截图后缀转换成模型可读 MIME；如果没有这段函数，image_result block 只能给路径而不能说明图片类型，作者意图是让后续多模态消费端稳定读取截图。
def screenshot_mime_type(raw_format: Any) -> str:  # 新增代码+Phase41WindowsImageResults: 定义截图 MIME 类型映射函数；如果没有这行代码，PNG/JPEG/BMP 的类型判断会散落在多个调用点。
    screenshot_format = safe_screenshot_format(raw_format)  # 新增代码+Phase41WindowsImageResults: 复用已有安全后缀清理逻辑；如果没有这行代码，未知或危险后缀可能直接进入 MIME 映射。
    if screenshot_format == "png":  # 新增代码+Phase41WindowsImageResults: 判断 PNG 格式；如果没有这行代码，最常见截图格式会被当成未知二进制。
        return "image/png"  # 新增代码+Phase41WindowsImageResults: 返回 PNG MIME；如果没有这行代码，模型或 UI 无法按 PNG 解码。
    if screenshot_format in {"jpg", "jpeg"}:  # 新增代码+Phase41WindowsImageResults: 判断 JPEG 格式；如果没有这行代码，JPEG 截图类型会丢失。
        return "image/jpeg"  # 新增代码+Phase41WindowsImageResults: 返回 JPEG MIME；如果没有这行代码，消费端可能按错误格式处理 JPEG。
    if screenshot_format == "bmp":  # 新增代码+Phase41WindowsImageResults: 判断 BMP 格式；如果没有这行代码，Windows 原生位图截图会被当成未知二进制。
        return "image/bmp"  # 新增代码+Phase41WindowsImageResults: 返回 BMP MIME；如果没有这行代码，消费端无法正确识别 BMP。
    return "application/octet-stream"  # 新增代码+Phase41WindowsImageResults: 对未知格式使用保守二进制类型；如果没有这行代码，函数在未知输入时没有稳定兜底。
# 新增代码+Phase41WindowsImageResults: 函数段结束，screenshot_mime_type 到此结束；如果没有这个结束标记，学习者不容易看出 MIME 映射边界。


# 新增代码+ComputerUsePngSource: 函数段开始，normalize_screenshot_artifact_bytes 把 Windows provider 返回的截图源头归一成模型友好的 artifact；如果没有这段函数，BMP 会继续在 evidence 层落盘并误导后续主循环。
def normalize_screenshot_artifact_bytes(raw_bytes: bytes, raw_format: Any) -> tuple[bytes, str]:  # 新增代码+ComputerUsePngSource: 定义截图 artifact 字节归一化入口；如果没有这行代码，save_window_state 只能原样保存 helper 格式。
    screenshot_format = safe_screenshot_format(raw_format)  # 新增代码+ComputerUsePngSource: 先复用安全后缀清理；如果没有这行代码，后续转换可能相信危险或空格式。
    if not raw_bytes:  # 新增代码+ComputerUsePngSource: 无截图字节时直接返回空结果；如果没有这行代码，空 payload 会被 Pillow 当坏图片处理。
        return b"", ""  # 新增代码+ComputerUsePngSource: 返回空字节和空格式；如果没有这行代码，无截图场景会生成误导性图片格式。
    if screenshot_format != "bmp":  # 新增代码+ComputerUsePngSource: 只对模型不支持的 BMP 做源头转码；如果没有这行代码，已有 PNG/JPEG 会被无意义重编码。
        return raw_bytes, screenshot_format  # 新增代码+ComputerUsePngSource: 保留模型已支持的原始图片；如果没有这行代码，正常 PNG 截图会被错误改动。
    try:  # 新增代码+ComputerUsePngSource: 延迟导入图片库以降低普通路径启动成本；如果没有这行代码，Pillow 缺失会在模块导入阶段影响非截图功能。
        from io import BytesIO  # 新增代码+ComputerUsePngSource: 导入内存缓冲区用于读 BMP 写 PNG；如果没有这行代码，转码需要创建临时文件增加清理风险。
        from PIL import Image  # 新增代码+ComputerUsePngSource: 导入 Pillow 执行真实像素转码；如果没有这行代码，只能错误地改后缀或 MIME。
    except Exception:  # 新增代码+ComputerUsePngSource: 捕获 Pillow 不可用等环境问题；如果没有这行代码，截图保存会因可选依赖问题整体崩溃。
        return raw_bytes, screenshot_format  # 新增代码+ComputerUsePngSource: 转码能力不可用时保留原始证据以便排查；如果没有这行代码，真实截图可能直接丢失。
    try:  # 新增代码+ComputerUsePngSource: 捕获坏 BMP 或转码失败；如果没有这行代码，一张坏截图会中断整个 observe 工具。
        with Image.open(BytesIO(raw_bytes)) as image:  # 新增代码+ComputerUsePngSource: 从内存读取 BMP 像素；如果没有这行代码，函数无法理解原始 BMP 内容。
            output = BytesIO()  # 新增代码+ComputerUsePngSource: 准备 PNG 输出缓冲区；如果没有这行代码，转码后的字节没有存放位置。
            image.save(output, format="PNG")  # 新增代码+ComputerUsePngSource: 把 BMP 像素重新编码成 PNG；如果没有这行代码，模型 API 仍可能收到不支持的 BMP。
            return output.getvalue(), "png"  # 新增代码+ComputerUsePngSource: 返回真实 PNG 字节和 PNG 格式；如果没有这行代码，evidence 层不能从源头变成模型可读。
    except Exception:  # 新增代码+ComputerUsePngSource: 转码失败时兜底保留原始证据；如果没有这行代码，截图链路会因为个别坏图直接失败。
        return raw_bytes, screenshot_format  # 新增代码+ComputerUsePngSource: 返回原始 BMP 便于后续下游兜底或人工排查；如果没有这行代码，观察证据可能丢失。
# 新增代码+ComputerUsePngSource: 函数段结束，normalize_screenshot_artifact_bytes 到此结束；如果没有这个边界说明，用户不容易看出源头图片归一化范围。


# 新增代码+Phase41WindowsImageResults: 函数段开始，build_image_result_blocks 把截图 evidence 转成模型可见但不含 UIA 文本的图片块；如果没有这段函数，截图只能作为普通路径藏在 dict 里，作者意图是给模型一个稳定、低泄露风险的图片引用协议。
def build_image_result_blocks(evidence: dict[str, Any], *, source: str = "window_state") -> list[dict[str, Any]]:  # 新增代码+Phase41WindowsImageResults: 定义 image_result block 构造函数；如果没有这行代码，调用方会重复拼接图片字段。
    if not bool(evidence.get("screenshot_captured", False)):  # 新增代码+Phase41WindowsImageResults: 只有真实捕获截图时才生成 block；如果没有这行代码，无截图场景会暴露空路径误导模型。
        return []  # 新增代码+Phase41WindowsImageResults: 无截图时返回空列表；如果没有这行代码，后续代码需要处理 None 分支。
    artifact_path = clean_protocol_text(evidence.get("screenshot_path", ""), max_length=1000)  # 新增代码+Phase41WindowsImageResults: 清理截图 artifact 路径；如果没有这行代码，路径中的控制字符可能污染工具输出。
    if not artifact_path:  # 新增代码+Phase41WindowsImageResults: 检查截图路径是否存在；如果没有这行代码，block 可能指向空路径。
        return []  # 新增代码+Phase41WindowsImageResults: 没有路径时不生成 block；如果没有这行代码，模型可能尝试读取不存在的图片。
    raw_format = evidence.get("screenshot_format", Path(artifact_path).suffix.lstrip("."))  # 新增代码+Phase41WindowsImageResults: 优先用 evidence 格式并回退到文件后缀；如果没有这行代码，早期 evidence 没有格式字段时 MIME 无法推断。
    screenshot_coordinate_mapping = evidence.get("screenshot_coordinate_mapping", {}) if isinstance(evidence.get("screenshot_coordinate_mapping", {}), dict) else {}  # 新增代码+ClaudeCodeParityScreenshot: 从 evidence 读取截图坐标映射并做 dict 兜底；如果没有这行代码，image_result 无法携带模型看图时需要的 scale。
    block = {  # 新增代码+Phase41WindowsImageResults: 开始构造单张截图的 image_result block；如果没有这行代码，结构化图片引用没有容器。
        "type": "image_result",  # 新增代码+Phase41WindowsImageResults: 标记块类型；如果没有这行代码，模型无法把它和普通数据区分。
        "model": PHASE41_IMAGE_RESULT_MODEL,  # 新增代码+Phase41WindowsImageResults: 写入协议模型名；如果没有这行代码，后续迁移无法区分版本。
        "source": clean_protocol_text(source, max_length=80),  # 新增代码+Phase41WindowsImageResults: 记录图片来源；如果没有这行代码，before/after/window_state 场景无法区分。
        "artifact_path": artifact_path,  # 新增代码+Phase41WindowsImageResults: 提供可打开的本地截图路径；如果没有这行代码，模型只能知道截图存在却无法引用。
        "image_path": artifact_path,  # 新增代码+Phase41WindowsImageResults: 提供兼容命名的图片路径；如果没有这行代码，消费端需要硬编码 artifact_path。
        "mime_type": screenshot_mime_type(raw_format),  # 新增代码+Phase41WindowsImageResults: 写入 MIME 类型；如果没有这行代码，多模态端不知道如何解码图片。
        "width": int(evidence.get("screenshot_width", 0) or 0),  # 新增代码+Phase41WindowsImageResults: 写入图片宽度；如果没有这行代码，模型无法判断截图尺度。
        "height": int(evidence.get("screenshot_height", 0) or 0),  # 新增代码+Phase41WindowsImageResults: 写入图片高度；如果没有这行代码，模型无法判断截图尺度。
        "screenshot_id": clean_protocol_text(evidence.get("screenshot_id", ""), max_length=160),  # 新增代码+Phase41WindowsImageResults: 写入截图 id；如果没有这行代码，图片和 metadata 难以关联。
        "evidence_path": clean_protocol_text(evidence.get("evidence_path", ""), max_length=1000),  # 新增代码+Phase41WindowsImageResults: 写入 metadata 路径；如果没有这行代码，审计时不容易找到同一证据包。
        "sensitive_text_included": False,  # 新增代码+Phase41WindowsImageResults: 明确 image block 不包含 UIA 文本；如果没有这行代码，安全边界不透明。
        "text_redacted": True,  # 新增代码+Phase41WindowsImageResults: 明确文本被排除或脱敏；如果没有这行代码，调用方不知道是否可以安全展示 block。
        "screenshot_coordinate_model": clean_protocol_text(evidence.get("screenshot_coordinate_model", SCREENSHOT_COORDINATE_MODEL), max_length=160),  # 新增代码+ClaudeCodeParityScreenshot: 把截图映射版本放进图片块；如果没有这行代码，模型看到图片块时无法判断坐标合同版本。
        "screenshot_coordinate_mapping": screenshot_coordinate_mapping,  # 新增代码+ClaudeCodeParityScreenshot: 把窗口逻辑到截图像素的 scale 放进图片块；如果没有这行代码，后续 zoom 无法只靠 image_result 做换算。
        "marker": PHASE41_WINDOWS_IMAGE_RESULTS_MARKER,  # 新增代码+Phase41WindowsImageResults: 写入验收标记；如果没有这行代码，场景输出不容易证明 Phase41 生效。
    }  # 新增代码+Phase41WindowsImageResults: image_result block 构造结束；如果没有这行代码，Python 字典语法不完整。
    return [block]  # 新增代码+Phase41WindowsImageResults: 返回 block 列表便于未来支持 before/after 多图；如果没有这行代码，调用方拿不到构造结果。
# 新增代码+Phase41WindowsImageResults: 函数段结束，build_image_result_blocks 到此结束；如果没有这个结束标记，学习者不容易看出图片块构造边界。


# 新增代码+Phase41WindowsImageResults: 函数段开始，collect_image_result_blocks 递归收集工具结果里的 image_result block；如果没有这段函数，controller、agent 和测试会各自写一套脆弱查找逻辑，作者意图是统一模型可见图片块的提取方式。
def collect_image_result_blocks(data: Any) -> list[dict[str, Any]]:  # 新增代码+Phase41WindowsImageResults: 定义通用图片块收集器；如果没有这行代码，嵌套在 state/action_evidence 里的图片块会被漏掉。
    blocks: list[dict[str, Any]] = []  # 新增代码+Phase41WindowsImageResults: 准备收集结果列表；如果没有这行代码，递归函数没有地方保存命中的 block。
    seen_paths: set[str] = set()  # 修改代码+Phase41WindowsImageResults: 记录已收集 artifact_path 用于去重；如果没有这行代码，顶层和 state 同步的同一截图会重复显示。

    def visit(value: Any) -> None:  # 新增代码+Phase41WindowsImageResults: 定义内部递归访问函数；如果没有这段函数，嵌套 dict/list 的扫描逻辑会重复。
        if isinstance(value, dict):  # 新增代码+Phase41WindowsImageResults: 判断当前节点是否为字典；如果没有这行代码，无法识别结构化 block。
            if value.get("type") == "image_result" and value.get("artifact_path"):  # 新增代码+Phase41WindowsImageResults: 判断字典是否为有效图片块；如果没有这行代码，普通状态字段可能被误收集。
                artifact_path = str(value.get("artifact_path", "")).strip()  # 修改代码+Phase41WindowsImageResults: 读取图片路径作为去重键；如果没有这行代码，重复图片块无法稳定合并。
                if artifact_path in seen_paths:  # 修改代码+Phase41WindowsImageResults: 检查该截图是否已经收集；如果没有这行代码，同一截图会在模型文本里重复出现。
                    return  # 修改代码+Phase41WindowsImageResults: 已收集时直接返回；如果没有这行代码，重复 block 会继续进入结果列表。
                seen_paths.add(artifact_path)  # 修改代码+Phase41WindowsImageResults: 标记该截图已收集；如果没有这行代码，后续重复项无法被识别。
                blocks.append(dict(value))  # 新增代码+Phase41WindowsImageResults: 保存图片块副本；如果没有这行代码，调用方可能意外修改原始结果。
                return  # 新增代码+Phase41WindowsImageResults: 命中 block 后不再深入其内部；如果没有这行代码，同一 block 可能被重复扫描。
            for nested_value in value.values():  # 新增代码+Phase41WindowsImageResults: 遍历字典子值；如果没有这行代码，嵌套 state 里的 image_results 会被漏掉。
                visit(nested_value)  # 新增代码+Phase41WindowsImageResults: 递归检查子值；如果没有这行代码，收集器只能处理顶层 block。
        elif isinstance(value, list):  # 新增代码+Phase41WindowsImageResults: 判断当前节点是否为列表；如果没有这行代码，image_results 列表无法展开。
            for item in value:  # 新增代码+Phase41WindowsImageResults: 遍历列表项；如果没有这行代码，列表中的 block 不会被发现。
                visit(item)  # 新增代码+Phase41WindowsImageResults: 递归检查列表项；如果没有这行代码，嵌套列表无法收集。

    visit(data)  # 新增代码+Phase41WindowsImageResults: 从传入数据开始扫描；如果没有这行代码，收集器永远返回空列表。
    return blocks  # 新增代码+Phase41WindowsImageResults: 返回收集到的图片块；如果没有这行代码，调用方拿不到结果。
# 新增代码+Phase41WindowsImageResults: 函数段结束，collect_image_result_blocks 到此结束；如果没有这个结束标记，学习者不容易看出递归收集边界。


# 新增代码+Phase41WindowsImageResults: 函数段开始，format_image_result_lines 把图片块转成工具结果里的稳定短文本；如果没有这段函数，模型需要从巨大 dict 里猜截图路径，作者意图是降低 token 和误读成本。
def format_image_result_lines(image_results: list[dict[str, Any]]) -> list[str]:  # 新增代码+Phase41WindowsImageResults: 定义图片结果文本格式化函数；如果没有这行代码，controller 文本输出无法形成稳定图片区。
    if not image_results:  # 新增代码+Phase41WindowsImageResults: 无图片块时不输出图片区；如果没有这行代码，普通 observe 会多出噪音。
        return []  # 新增代码+Phase41WindowsImageResults: 返回空行列表；如果没有这行代码，调用方需要额外处理 None。
    lines = ["Computer Use Image Results", f"- image_result_count={len(image_results)}"]  # 新增代码+Phase41WindowsImageResults: 写入图片区标题和数量；如果没有这行代码，模型无法快速定位图片结果。
    for index, block in enumerate(image_results):  # 新增代码+Phase41WindowsImageResults: 遍历每个图片块；如果没有这行代码，多张截图无法逐一展示。
        width = int(block.get("width", 0) or 0)  # 新增代码+Phase41WindowsImageResults: 读取图片宽度；如果没有这行代码，尺寸行无法生成。
        height = int(block.get("height", 0) or 0)  # 新增代码+Phase41WindowsImageResults: 读取图片高度；如果没有这行代码，尺寸行无法生成。
        lines.append(f"- image_{index}_result_model={clean_protocol_text(block.get('model', ''), max_length=120)}")  # 新增代码+Phase41WindowsImageResults: 输出图片协议模型名；如果没有这行代码，终端结果无法审计 block 版本。
        lines.append(f"- image_{index}_artifact_path={clean_protocol_text(block.get('artifact_path', ''), max_length=1000)}")  # 新增代码+Phase41WindowsImageResults: 输出截图 artifact 路径；如果没有这行代码，模型无法引用图片文件。
        lines.append(f"- image_{index}_mime_type={clean_protocol_text(block.get('mime_type', ''), max_length=80)}")  # 新增代码+Phase41WindowsImageResults: 输出 MIME 类型；如果没有这行代码，消费端无法知道图片格式。
        lines.append(f"- image_{index}_size={width}x{height}")  # 新增代码+Phase41WindowsImageResults: 输出图片尺寸；如果没有这行代码，模型无法判断截图像素范围。
        lines.append(f"- image_{index}_sensitive_text_included={str(bool(block.get('sensitive_text_included', False))).lower()}")  # 新增代码+Phase41WindowsImageResults: 输出敏感文本边界；如果没有这行代码，用户不知道图片块是否含 UIA 文本。
        lines.append(f"- image_{index}_marker={clean_protocol_text(block.get('marker', ''), max_length=120)}")  # 新增代码+Phase41WindowsImageResults: 输出验收标记；如果没有这行代码，真实终端日志不容易匹配 Phase41。
    return lines  # 新增代码+Phase41WindowsImageResults: 返回格式化文本行；如果没有这行代码，controller 无法追加图片区。
# 新增代码+Phase41WindowsImageResults: 函数段结束，format_image_result_lines 到此结束；如果没有这个结束标记，学习者不容易看出文本格式化边界。


# 新增代码+Phase29ComputerUse: 函数段开始，filter_accessibility_text 用于过滤和截断 UIA 文本；如果没有这段函数，超长或敏感 UIA 会进入模型上下文，作者意图是让 UIA 只作为短摘要。 
def filter_accessibility_text(raw_text: Any, *, max_length: int = 600) -> FilteredAccessibilityText:  # 新增代码+Phase29ComputerUse: 定义 UIA 文本过滤函数；如果没有这行代码，响应和 metadata 无法统一过滤。 
    filtered_lines: list[str] = []  # 新增代码+Phase29ComputerUse: 准备保存安全行；如果没有这行代码，过滤后的文本没有容器。 
    filtered_line_count = 0  # 新增代码+Phase29ComputerUse: 初始化敏感行计数；如果没有这行代码，用户无法知道删除了多少行。 
    for line in str(raw_text or "").splitlines():  # 新增代码+Phase29ComputerUse: 按行处理原始 UIA 文本；如果没有这行代码，敏感词过滤只能粗暴处理整段文本。 
        cleaned_line = clean_protocol_text(line, max_length=max_length)  # 新增代码+Phase29ComputerUse: 清理单行并限制单行长度；如果没有这行代码，换行和控制字符会污染摘要。 
        if not cleaned_line:  # 新增代码+Phase29ComputerUse: 跳过空行；如果没有这行代码，摘要会被空白撑大。 
            continue  # 新增代码+Phase29ComputerUse: 继续下一行；如果没有这行代码，空行会进入后续敏感词判断。 
        lowered = cleaned_line.lower()  # 新增代码+Phase29ComputerUse: 转小写便于敏感词匹配；如果没有这行代码，大小写变化会绕过过滤。 
        if any(keyword in lowered for keyword in SENSITIVE_ACCESSIBILITY_KEYWORDS):  # 新增代码+Phase29ComputerUse: 检查这一行是否包含敏感关键词；如果没有这行代码，password/token 可能泄露。 
            filtered_line_count += 1  # 新增代码+Phase29ComputerUse: 记录过滤掉一行；如果没有这行代码，过滤行为无法审计。 
            continue  # 新增代码+Phase29ComputerUse: 丢弃敏感行；如果没有这行代码，敏感行仍会进入摘要。 
        filtered_lines.append(cleaned_line)  # 新增代码+Phase29ComputerUse: 保存安全行；如果没有这行代码，UIA 摘要会一直为空。 
    joined = " ".join(filtered_lines)  # 新增代码+Phase29ComputerUse: 合并安全行为单行摘要；如果没有这行代码，响应可能包含大量换行扰乱终端输出。 
    truncated = len(joined) > max_length  # 新增代码+Phase29ComputerUse: 判断摘要是否超过上限；如果没有这行代码，无法告诉用户文本是否被截断。 
    excerpt = joined[:max_length] if truncated else joined  # 新增代码+Phase29ComputerUse: 按上限截断摘要；如果没有这行代码，超长 UIA 会挤占模型上下文。 
    return FilteredAccessibilityText(excerpt=excerpt, truncated=truncated, filtered_line_count=filtered_line_count)  # 新增代码+Phase29ComputerUse: 返回过滤摘要结构；如果没有这行代码，调用方拿不到处理结果。 
# 新增代码+Phase29ComputerUse: 函数段结束，filter_accessibility_text 到此结束；如果没有这个结束标记，用户不容易看出 UIA 过滤边界。 


class ComputerUseEvidenceStore:  # 新增代码+Phase29ComputerUse: 定义 Computer Use 证据仓库；如果没有这个类，截图和 metadata 没有统一保存入口。 
    def __init__(self, evidence_root: Path | str | None = None) -> None:  # 新增代码+Phase29ComputerUse: 初始化证据根目录；如果没有这段代码，测试无法注入临时目录。 
        self.evidence_root = Path(evidence_root) if evidence_root is not None else DEFAULT_EVIDENCE_ROOT  # 新增代码+Phase29ComputerUse: 保存实际 evidence 根目录；如果没有这行代码，运行时无法定位证据文件。 

    def status(self) -> dict[str, Any]:  # 新增代码+Phase29ComputerUse: 返回证据仓库状态；如果没有这段代码，computer_status 无法展示 evidence_root。 
        return {"evidence_root": str(self.evidence_root), "evidence_mode": "window_state_artifact"}  # 新增代码+Phase29ComputerUse: 返回路径和模式；如果没有这行代码，用户不知道证据链是否接入。 

    def save_window_state(self, *, window: dict[str, Any], payload: Any, fallback_width: int, fallback_height: int) -> dict[str, Any]:  # 新增代码+Phase29ComputerUse: 保存一次窗口状态证据；如果没有这段函数，get_window_state 无法落盘截图和 metadata。 
        self.evidence_root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase29ComputerUse: 确保证据目录存在；如果没有这行代码，首次保存证据会因目录缺失失败。 
        evidence_id = f"computer-window-{phase29_evidence_timestamp()}-{uuid.uuid4().hex[:8]}"  # 新增代码+Phase29ComputerUse: 生成唯一证据 id；如果没有这行代码，多次观察无法区分。 
        screenshot_bytes = bytes(getattr(payload, "screenshot_bytes", b"") or b"")  # 新增代码+Phase29ComputerUse: 读取截图字节并兜底为空；如果没有这行代码，无截图 helper 会触发异常。 
        screenshot_format = safe_screenshot_format(getattr(payload, "screenshot_format", ""))  # 新增代码+Phase29ComputerUse: 清理截图格式；如果没有这行代码，截图文件后缀不安全。 
        screenshot_bytes, screenshot_format = normalize_screenshot_artifact_bytes(screenshot_bytes, screenshot_format)  # 新增代码+ComputerUsePngSource: 在 evidence 源头把 BMP 归一成 PNG；如果没有这行代码，模型主循环仍可能拿到不支持的 image/bmp artifact。
        screenshot_path = ""  # 新增代码+Phase29ComputerUse: 初始化截图路径为空；如果没有这行代码，无截图场景下字段会缺失。 
        if screenshot_bytes:  # 新增代码+Phase29ComputerUse: 只有 helper 真给了截图才写图片文件；如果没有这行代码，会写出无意义空截图。 
            screenshot_file = self.evidence_root / f"{evidence_id}.{screenshot_format}"  # 新增代码+Phase29ComputerUse: 构造截图文件路径；如果没有这行代码，截图字节没有保存目标。 
            screenshot_file.write_bytes(screenshot_bytes)  # 新增代码+Phase29ComputerUse: 写入截图 artifact；如果没有这行代码，截图 evidence 不会落盘。 
            screenshot_path = str(screenshot_file)  # 新增代码+Phase29ComputerUse: 保存截图路径给响应和 metadata；如果没有这行代码，用户无法打开截图证据。 
        filtered = filter_accessibility_text(getattr(payload, "accessibility_text", ""), max_length=600)  # 新增代码+Phase29ComputerUse: 过滤并截断 UIA 文本；如果没有这行代码，敏感或超长文本会进入证据。 
        focused = clean_protocol_text(getattr(payload, "focused_element", ""), max_length=160)  # 新增代码+Phase29ComputerUse: 清理焦点元素摘要；如果没有这行代码，焦点字段可能过长或带换行。 
        selected = filter_accessibility_text(getattr(payload, "selected_text", ""), max_length=160).excerpt  # 新增代码+Phase29ComputerUse: 过滤选中文本摘要；如果没有这行代码，选中文本可能泄露敏感信息。 
        document = filter_accessibility_text(getattr(payload, "document_text", ""), max_length=240).excerpt  # 新增代码+Phase29ComputerUse: 过滤文档文本摘要；如果没有这行代码，正文摘要可能过长或敏感。 
        screenshot_width = int(getattr(payload, "screenshot_width", 0) or fallback_width)  # 新增代码+Phase29ComputerUse: 优先使用 helper 截图宽度并回退 rect；如果没有这行代码，截图尺寸可能为空。 
        screenshot_height = int(getattr(payload, "screenshot_height", 0) or fallback_height)  # 新增代码+Phase29ComputerUse: 优先使用 helper 截图高度并回退 rect；如果没有这行代码，截图高度可能为空。 
        screenshot_coordinate_mapping = build_screenshot_coordinate_mapping(window, screenshot_width, screenshot_height)  # 新增代码+ClaudeCodeParityScreenshot: 生成本次截图的坐标映射；如果没有这行代码，result、image_result 和 metadata 无法共享 scale。
        metadata = {"evidence_id": evidence_id, "kind": "window_state", "window": dict(window), "helper": {"name": clean_protocol_text(getattr(payload, "helper_name", ""), max_length=120), "available": bool(getattr(payload, "helper_available", False)), "reason": clean_protocol_text(getattr(payload, "helper_reason", ""), max_length=240)}, "screenshot": {"id": evidence_id, "captured": bool(screenshot_bytes), "path": screenshot_path, "format": screenshot_format if screenshot_bytes else "", "width": screenshot_width, "height": screenshot_height}, "accessibility": {"excerpt": filtered.excerpt, "truncated": filtered.truncated, "filtered_line_count": filtered.filtered_line_count, "focused_element": focused, "selected_text_preview": selected, "document_text_preview": document}}  # 新增代码+Phase29ComputerUse: 构造安全 metadata；如果没有这行代码，截图和 UIA 摘要无法机器审计。 
        metadata["screenshot"]["coordinate_model"] = SCREENSHOT_COORDINATE_MODEL  # 新增代码+ClaudeCodeParityScreenshot: 在 screenshot 分组写入坐标映射版本；如果没有这行代码，审计时截图分组缺少 scale 合同标识。
        metadata["screenshot"]["coordinate_mapping"] = screenshot_coordinate_mapping  # 新增代码+ClaudeCodeParityScreenshot: 在 screenshot 分组写入同一份映射；如果没有这行代码，审计者需要从 result 才能查到坐标换算。
        metadata["screenshot_coordinate_model"] = SCREENSHOT_COORDINATE_MODEL  # 新增代码+ClaudeCodeParityScreenshot: 在 metadata 顶层写入坐标映射版本；如果没有这行代码，离线扫描 metadata 时不容易发现截图坐标合同。
        metadata["screenshot_coordinate_mapping"] = screenshot_coordinate_mapping  # 新增代码+ClaudeCodeParityScreenshot: 在 metadata 顶层写入坐标映射；如果没有这行代码，离线审计无法直接验证 scale。
        metadata_path = self.evidence_root / f"{evidence_id}.json"  # 新增代码+Phase29ComputerUse: 构造 metadata 文件路径；如果没有这行代码，JSON 证据没有保存目标。 
        result = {  # 修改代码+Phase41WindowsImageResults: 先构造统一返回字典再追加 image_results；如果没有这行代码，图片块无法复用已有截图和 metadata 字段。
            "evidence_id": evidence_id,  # 修改代码+Phase41WindowsImageResults: 返回 evidence id；如果没有这行代码，controller 无法关联 metadata 文件。
            "evidence_path": str(metadata_path),  # 修改代码+Phase41WindowsImageResults: 返回 metadata 路径；如果没有这行代码，image_result block 无法指向审计账本。
            "screenshot_id": evidence_id if screenshot_bytes else "",  # 修改代码+Phase41WindowsImageResults: 返回截图 id；如果没有这行代码，图片块无法关联截图文件。
            "screenshot_path": screenshot_path,  # 修改代码+Phase41WindowsImageResults: 返回截图 artifact 路径；如果没有这行代码，模型无法引用落盘截图。
            "screenshot_captured": bool(screenshot_bytes),  # 修改代码+Phase41WindowsImageResults: 返回截图是否捕获；如果没有这行代码，无截图场景可能误生成 image block。
            "screenshot_format": screenshot_format if screenshot_bytes else "",  # 新增代码+Phase41WindowsImageResults: 返回截图格式用于 MIME 映射；如果没有这行代码，image_result block 只能从后缀猜格式。
            "screenshot_width": screenshot_width,  # 修改代码+Phase41WindowsImageResults: 返回截图宽度；如果没有这行代码，图片块缺少尺寸。
            "screenshot_height": screenshot_height,  # 修改代码+Phase41WindowsImageResults: 返回截图高度；如果没有这行代码，图片块缺少尺寸。
            "accessibility_excerpt": filtered.excerpt,  # 修改代码+Phase41WindowsImageResults: 保留已脱敏 UIA 摘要；如果没有这行代码，旧的窗口状态能力会退化。
            "accessibility_truncated": filtered.truncated,  # 修改代码+Phase41WindowsImageResults: 保留 UIA 截断标记；如果没有这行代码，模型不知道摘要是否完整。
            "accessibility_filtered_line_count": filtered.filtered_line_count,  # 修改代码+Phase41WindowsImageResults: 保留敏感行过滤计数；如果没有这行代码，用户无法审计脱敏发生。
            "focused_element": focused,  # 修改代码+Phase41WindowsImageResults: 保留焦点元素摘要；如果没有这行代码，后续动作判断缺少上下文。
            "selected_text_preview": selected,  # 修改代码+Phase41WindowsImageResults: 保留选中文本摘要；如果没有这行代码，旧 UIA 合同会缺字段。
            "document_text_preview": document,  # 修改代码+Phase41WindowsImageResults: 保留文档摘要；如果没有这行代码，旧 UIA 合同会缺字段。
            "helper_name": metadata["helper"]["name"],  # 修改代码+Phase41WindowsImageResults: 返回 helper 名称；如果没有这行代码，证据来源不可见。
            "helper_available": metadata["helper"]["available"],  # 修改代码+Phase41WindowsImageResults: 返回 helper 可用状态；如果没有这行代码，调用方无法判断截图能力边界。
            "helper_reason": metadata["helper"]["reason"],  # 修改代码+Phase41WindowsImageResults: 返回 helper 原因；如果没有这行代码，失败或降级原因不清楚。
        }  # 修改代码+Phase41WindowsImageResults: 返回字典构造结束；如果没有这行代码，Python 字典语法不完整。
        result["screenshot_coordinate_model"] = SCREENSHOT_COORDINATE_MODEL  # 新增代码+ClaudeCodeParityScreenshot: 把坐标映射版本写入工具结果；如果没有这行代码，调用方无法判断 scale 字段协议版本。
        result["screenshot_coordinate_mapping"] = screenshot_coordinate_mapping  # 新增代码+ClaudeCodeParityScreenshot: 把坐标映射写入工具结果；如果没有这行代码，模型和测试无法从 result 直接换算截图坐标。
        image_results = build_image_result_blocks(result, source="window_state")  # 新增代码+Phase41WindowsImageResults: 根据截图字段生成模型可见图片块；如果没有这行代码，截图不会进入 image_result 协议。
        result["image_results"] = image_results  # 新增代码+Phase41WindowsImageResults: 把图片块放进工具响应；如果没有这行代码，controller 无法把图片块传给模型。
        result["image_result_count"] = len(image_results)  # 新增代码+Phase41WindowsImageResults: 返回图片块数量；如果没有这行代码，终端和测试无法快速确认有几张图。
        metadata["image_results"] = image_results  # 新增代码+Phase41WindowsImageResults: 把图片块也写入 metadata；如果没有这行代码，离线审计无法从证据账本看到模型引用了哪张图。
        metadata["image_result_count"] = len(image_results)  # 新增代码+Phase41WindowsImageResults: 把图片数量写入 metadata；如果没有这行代码，审计需要重新扫描 image_results 列表。
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")  # 新增代码+Phase29ComputerUse: 写入 UTF-8 JSON metadata；如果没有这行代码，证据账本不会落盘。 
        return result  # 修改代码+Phase41WindowsImageResults: 返回包含 image_results 的 bounded 字段；如果没有这行代码，controller 无法组装模型可见截图结果。


# 新增代码+Phase41WindowsImageResults: 函数段开始，run_phase41_image_results_contract 运行不触碰真实桌面的 Phase41 自检；如果没有这段函数，真实可见终端只能靠人工观察，作者意图是把截图 artifact、image block、agent artifact 和脱敏边界变成可验证合同。
def run_phase41_image_results_contract() -> dict[str, Any]:  # 新增代码+Phase41WindowsImageResults: 定义 Phase41 安全合同入口；如果没有这行代码，验收脚本无法调用统一自检。
    import tempfile  # 新增代码+Phase41WindowsImageResults: 在函数内导入临时目录工具；如果没有这行代码，自检会污染真实 evidence 目录。

    try:  # 新增代码+Phase41WindowsImageResults: 优先用包模式导入控制器和测试 helper；如果没有这行代码，模块直接运行时无法兼容不同入口。
        from learning_agent.computer_use.controller import ComputerUseController, WindowsComputerUseBackend  # 新增代码+Phase41WindowsImageResults: 导入真实 Computer Use 控制链；如果没有这行代码，自检只能验证孤立 evidence。
        from learning_agent.computer_use.helper_client import StaticWindowObservationHelper, WindowObservationPayload  # 新增代码+Phase41WindowsImageResults: 导入静态观察 helper；如果没有这行代码，自检会需要真实桌面截图。
        from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase41WindowsImageResults: 导入静态窗口 inventory；如果没有这行代码，自检会依赖用户当前窗口。
        from learning_agent.core.agent import LearningAgent, ModelMessage, ToolCallingFakeModel  # 新增代码+Phase41WindowsImageResults: 导入真实 agent 和假模型；如果没有这行代码，active_artifacts 集成无法自检。
    except ModuleNotFoundError as error:  # 新增代码+Phase41WindowsImageResults: 兼容 start_oauth_agent 脚本模式下包名前缀不可用；如果没有这行代码，bat 入口可能导入失败。
        if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.controller", "learning_agent.computer_use.helper_client", "learning_agent.computer_use.windows_backend", "learning_agent.core", "learning_agent.core.agent"}:  # 新增代码+Phase41WindowsImageResults: 只允许目标包路径缺失时 fallback；如果没有这行代码，真实内部错误会被误吞。
            raise  # 新增代码+Phase41WindowsImageResults: 重新抛出非路径类导入错误；如果没有这行代码，排查真实 bug 会很困难。
        from computer_use.controller import ComputerUseController, WindowsComputerUseBackend  # 新增代码+Phase41WindowsImageResults: 脚本模式导入 Computer Use 控制链；如果没有这行代码，直接运行 evidence.py 无法自检。
        from computer_use.helper_client import StaticWindowObservationHelper, WindowObservationPayload  # 新增代码+Phase41WindowsImageResults: 脚本模式导入静态 helper；如果没有这行代码，自检无法模拟截图。
        from computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase41WindowsImageResults: 脚本模式导入静态 inventory；如果没有这行代码，自检无法模拟窗口。
        from core.agent import LearningAgent, ModelMessage, ToolCallingFakeModel  # 新增代码+Phase41WindowsImageResults: 脚本模式导入真实 agent；如果没有这行代码，agent artifact 集成无法自检。

    with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase41WindowsImageResults: 创建临时根目录；如果没有这行代码，自检文件会留在真实项目目录。
        evidence_root = Path(raw_dir) / "evidence"  # 新增代码+Phase41WindowsImageResults: 定义临时 evidence 路径；如果没有这行代码，截图 artifact 路径不好隔离。
        workspace = Path(raw_dir) / "workspace"  # 新增代码+Phase41WindowsImageResults: 定义临时 agent 工作区；如果没有这行代码，agent 初始化会污染真实工作区。
        raw_windows = [{"hwnd": 41041, "pid": 141, "process_name": "notepad.exe", "class_name": "Notepad", "title": "Phase41 Safe Window", "rect": {"left": 40, "top": 50, "right": 360, "bottom": 260}}]  # 新增代码+Phase41WindowsImageResults: 构造静态安全窗口；如果没有这行代码，自检会读取真实桌面窗口。
        payload = WindowObservationPayload(screenshot_bytes=b"phase41-fake-png-bytes", screenshot_format="png", screenshot_width=320, screenshot_height=210, accessibility_text="safe title\npassword: phase41-secret-must-not-leak\nsafe button", focused_element="safe edit", selected_text="safe selected", document_text="safe document", helper_name="phase41_static_helper", helper_available=True, helper_reason="Phase41 selftest uses fake bytes only")  # 新增代码+Phase41WindowsImageResults: 构造含假截图和敏感行的 payload；如果没有这行代码，自检无法同时验证 artifact 和脱敏。
        store = ComputerUseEvidenceStore(evidence_root=evidence_root)  # 新增代码+Phase41WindowsImageResults: 创建证据仓库；如果没有这行代码，自检无法保存截图 artifact。
        direct_evidence = store.save_window_state(window=raw_windows[0], payload=payload, fallback_width=320, fallback_height=210)  # 新增代码+Phase41WindowsImageResults: 直接保存一次 evidence；如果没有这行代码，自检无法证明 evidence 层生成 block。
        direct_blocks = collect_image_result_blocks(direct_evidence)  # 新增代码+Phase41WindowsImageResults: 收集 evidence 层图片块；如果没有这行代码，自检无法判断 block 是否存在。
        inventory = StaticWindowsWindowInventory(raw_windows=raw_windows, captured_at="2026-06-03T00:00:00Z")  # 新增代码+Phase41WindowsImageResults: 构造静态窗口 inventory；如果没有这行代码，controller 自检会依赖真实窗口。
        helper = StaticWindowObservationHelper(payloads={"hwnd:41041": payload})  # 新增代码+Phase41WindowsImageResults: 把静态 payload 绑定到窗口；如果没有这行代码，controller 无法拿到假截图。
        backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=False, evidence_store=store, observation_helper=helper)  # 新增代码+Phase41WindowsImageResults: 创建只读 Windows 后端；如果没有这行代码，自检可能触发真实动作或缺少 observe 链路。
        controller = ComputerUseController(backend=backend)  # 新增代码+Phase41WindowsImageResults: 创建统一控制器；如果没有这行代码，自检无法覆盖生产 controller。
        window = controller.observe({"action": "list_windows"}).data["windows"][0]  # 新增代码+Phase41WindowsImageResults: 获取可信窗口引用；如果没有这行代码，get_window_state 会因未知窗口失败。
        result = controller.observe({"action": "get_window_state", "window": window})  # 新增代码+Phase41WindowsImageResults: 通过生产链读取窗口状态；如果没有这行代码，自检无法证明 controller 输出 image_results。
        result_text = result.to_text("computer_observe")  # 新增代码+Phase41WindowsImageResults: 生成模型可见工具文本；如果没有这行代码，自检无法证明图片区文本存在。
        agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+Phase41WindowsImageResults: 创建真实 agent 但不用联网模型；如果没有这行代码，active_artifacts 集成无法验证。
        agent.computer_use_controller = controller  # 新增代码+Phase41WindowsImageResults: 注入同一个只读控制器；如果没有这行代码，agent 会使用默认不可用后端。
        agent_output = agent._computer_observe({"action": "get_window_state", "window": window})  # 新增代码+Phase41WindowsImageResults: 通过 agent 工具入口读取窗口状态；如果没有这行代码，agent artifact 登记逻辑不会运行。
        artifact = bool(direct_blocks) and Path(direct_blocks[0]["artifact_path"]).exists()  # 新增代码+Phase41WindowsImageResults: 判断截图 artifact 是否真实存在；如果没有这行代码，OK token 可能只证明 block 文本存在。
        image_block = bool(collect_image_result_blocks(result.data)) and "Computer Use Image Results" in result_text  # 新增代码+Phase41WindowsImageResults: 判断 controller 是否输出图片块和图片区；如果没有这行代码，模型可见协议可能没接上。
        agent_artifact = any(str(evidence_root) in path for path in agent.active_artifacts) and "Computer Use Image Results" in agent_output  # 新增代码+Phase41WindowsImageResults: 判断 agent 是否登记截图 artifact；如果没有这行代码，长任务恢复仍可能丢图片。
        sensitive_payload = json.dumps({"direct": direct_blocks, "result": result.data, "text": result_text, "agent": agent_output}, ensure_ascii=False)  # 新增代码+Phase41WindowsImageResults: 汇总可见输出用于敏感词检查；如果没有这行代码，泄露检查无法覆盖多处输出。
        sensitive_text_hidden = "phase41-secret-must-not-leak" not in sensitive_payload  # 新增代码+Phase41WindowsImageResults: 检查敏感具体值没有外泄；如果没有这行代码，图片块可能夹带 UIA 敏感文本仍通过。
        return {"marker": PHASE41_WINDOWS_IMAGE_RESULTS_MARKER, "ok_token": PHASE41_WINDOWS_IMAGE_RESULTS_OK_TOKEN, "artifact": artifact, "image_block": image_block, "agent_artifact": agent_artifact, "sensitive_text_hidden": sensitive_text_hidden, "actions_expanded": PHASE41_ACTIONS_EXPANDED}  # 新增代码+Phase41WindowsImageResults: 返回自检报告；如果没有这行代码，CLI 行无法生成稳定布尔结果。
# 新增代码+Phase41WindowsImageResults: 函数段结束，run_phase41_image_results_contract 到此结束；如果没有这个结束标记，学习者不容易看出安全自检边界。


# 新增代码+Phase41WindowsImageResults: 函数段开始，phase41_cli_line 把自检报告压成真实终端可断言的一行；如果没有这段函数，场景需要解析复杂 JSON，作者意图是让可见终端验收更稳。
def phase41_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase41WindowsImageResults: 定义 CLI 输出格式化函数；如果没有这行代码，main 无法打印固定 token 行。
    return f"{PHASE41_WINDOWS_IMAGE_RESULTS_MARKER} {PHASE41_WINDOWS_IMAGE_RESULTS_OK_TOKEN} artifact={str(bool(report.get('artifact', False))).lower()} image_block={str(bool(report.get('image_block', False))).lower()} agent_artifact={str(bool(report.get('agent_artifact', False))).lower()} sensitive_text_hidden={str(bool(report.get('sensitive_text_hidden', False))).lower()} actions_expanded={str(bool(report.get('actions_expanded', True))).lower()}"  # 新增代码+Phase41WindowsImageResults: 返回固定顺序的一行状态；如果没有这行代码，验收 token 顺序不稳定。
# 新增代码+Phase41WindowsImageResults: 函数段结束，phase41_cli_line 到此结束；如果没有这个结束标记，学习者不容易看出 CLI 格式边界。


# 新增代码+Phase41WindowsImageResults: 函数段开始，main 提供 python -c 和模块直接调用入口；如果没有这段函数，start_oauth_agent.bat 场景无法要求 agent 运行 Phase41 自检，作者意图是让自动化和可见终端共用同一合同。
def main() -> int:  # 新增代码+Phase41WindowsImageResults: 定义命令行入口；如果没有这行代码，python 导入后无法统一退出码。
    report = run_phase41_image_results_contract()  # 新增代码+Phase41WindowsImageResults: 运行安全自检；如果没有这行代码，CLI 输出没有依据。
    passed = bool(report.get("artifact")) and bool(report.get("image_block")) and bool(report.get("agent_artifact")) and bool(report.get("sensitive_text_hidden")) and report.get("actions_expanded") is False  # 新增代码+Phase41WindowsImageResults: 汇总所有验收条件；如果没有这行代码，失败条件可能仍返回 0。
    print(PHASE41_WINDOWS_IMAGE_RESULTS_MARKER)  # 新增代码+Phase41WindowsImageResults: 先打印等待标记；如果没有这行代码，可见终端控制器可能不知道何时进入成功检查。
    print(phase41_cli_line(report))  # 新增代码+Phase41WindowsImageResults: 打印固定 token 行；如果没有这行代码，用户无法复制验收结果。
    return 0 if passed else 1  # 新增代码+Phase41WindowsImageResults: 根据自检结果返回退出码；如果没有这行代码，失败也会被终端当成成功。
# 新增代码+Phase41WindowsImageResults: 函数段结束，main 到此结束；如果没有这个结束标记，学习者不容易看出 CLI 入口边界。


if __name__ == "__main__":  # 新增代码+Phase41WindowsImageResults: 允许直接运行 evidence.py；如果没有这行代码，初学者无法手动启动 Phase41 自检。
    raise SystemExit(main())  # 新增代码+Phase41WindowsImageResults: 调用 main 并传递退出码；如果没有这行代码，直接运行文件不会执行合同。
