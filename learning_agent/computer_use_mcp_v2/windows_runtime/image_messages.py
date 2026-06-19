"""Computer Use 图片消息构造工具。"""  # 新增代码+AgentPySplitPhase1: 说明本文件只负责把桌面截图转成模型可见图片消息；如果没有这行代码，代码小白打开文件时不知道这个模块的学习入口。

from __future__ import annotations  # 新增代码+AgentPySplitPhase1: 允许类型注解延迟解析；如果没有这行代码，旧 Python 解析复杂注解时更容易受运行顺序影响。

import base64  # 新增代码+AgentPySplitPhase1: 用来把图片二进制编码成 JSON 能传输的 base64 文本；如果没有这行代码，模型消息不能直接携带截图字节。
import json  # 修改代码+McpImageReinjection: 用来解析 agent-side MCP adapter 包装后的 JSON 文本；如果没有这行代码，mcp__computer-use__observe 里的 legacy_text 截图行无法被提取。
from pathlib import Path  # 新增代码+AgentPySplitPhase1: 用 Path 稳定处理 artifact 文件路径；如果没有这行代码，路径存在性和后缀判断会变成脆弱字符串处理。
from typing import Any, Callable  # 新增代码+AgentPySplitPhase1: 导入通用类型和回调类型；如果没有这行代码，函数接口不容易看出会接收哪些数据。


RecordObservation = Callable[[str, dict[str, Any]], None]  # 新增代码+AgentPySplitPhase1: 定义观察记录回调类型；如果没有这行代码，新模块就会直接依赖 LearningAgent 类，拆分边界会变乱。

COMPUTER_USE_IMAGE_TOOL_NAMES = {"computer_observe", "computer_action", "computer_use", "computer-use"}  # 新增代码+AgentPySplitPhase1: 集中保存会产生桌面截图的旧内部工具名；如果没有这行代码，旧 adapter 的截图回灌会失去入口。
COMPUTER_USE_IMAGE_TOOL_PREFIXES = ("mcp__computer-use__",)  # 修改代码+ComputerUseMcpV2ResidualCleanup: 集中保存模型可见 Computer Use MCP 工具名前缀；如果没有这行代码，observe/screenshot/left_click 等 v2 MCP 输出不会变成模型可见图片。
MAX_COMPUTER_USE_MODEL_IMAGE_BYTES = 8 * 1024 * 1024  # 新增代码+AgentPySplitPhase1: 限制单张模型图片最大 8MB；如果没有这行代码，坏截图可能让一次模型请求体过大而失败。
COMPUTER_USE_JPEG_QUALITY = 75  # 新增代码+ComputerUseAdaptiveImage: 对齐 ClaudeCode 的 0.75 JPEG 质量；如果没有这行代码，大截图压缩质量会散落在多个保存调用里。
COMPUTER_USE_LOSSLESS_MAX_PIXELS = 1_000_000  # 新增代码+ComputerUseAdaptiveImage: 小于约百万像素的 UI 图优先保 PNG；如果没有这行代码，小字截图可能被 JPEG 压缩模糊。
COMPUTER_USE_LOSSLESS_MAX_BYTES = 1_500_000  # 新增代码+ComputerUseAdaptiveImage: 小 PNG 在 1.5MB 内原样发送；如果没有这行代码，历史 PNG artifact 会被不必要解码重写。
COMPUTER_USE_LOSSLESS_SOURCE_HINTS = ("zoom", "crop", "region")  # 新增代码+ComputerUseAdaptiveImage: 局部放大和裁剪图优先保真；如果没有这行代码，模型最需要看清文字的局部图可能被有损压缩。


# 新增代码+AgentPySplitPhase1: 函数段开始，_record_image_observation 统一写入图片处理诊断事件；如果没有这段函数，每个失败分支都要重复判断回调是否存在，代码会更乱。
def _record_image_observation(record_observation: RecordObservation | None, kind: str, payload: dict[str, Any]) -> None:  # 新增代码+AgentPySplitPhase1: 定义可选诊断记录入口；如果没有这行代码，独立模块无法把读图失败等原因交回 agent 观察日志。
    if record_observation is None:  # 新增代码+AgentPySplitPhase1: 允许单元测试或纯函数场景不提供记录器；如果没有这行代码，调用方必须伪造 LearningAgent 的记录方法。
        return  # 新增代码+AgentPySplitPhase1: 没有记录器时直接退出；如果没有这行代码，后面调用 None 会触发崩溃。
    record_observation(kind, payload)  # 新增代码+AgentPySplitPhase1: 把事件类型和细节交给外层 agent；如果没有这行代码，用户排查时不知道图片为什么没进入模型。
# 新增代码+AgentPySplitPhase1: 函数段结束，_record_image_observation 到此结束；如果没有这个边界说明，学习者不容易看出诊断记录 helper 的范围。


# 新增代码+AgentPySplitPhase1: 函数段开始，build_computer_use_image_message_from_tool_output 把 Computer Use 工具输出变成模型可见图片消息；如果没有这段函数，桌面截图只能作为文字路径存在，模型看不到像素。
def build_computer_use_image_message_from_tool_output(tool_name: str, output: str, record_observation: RecordObservation | None = None) -> dict[str, Any] | None:  # 新增代码+AgentPySplitPhase1: 定义图片消息构造入口；如果没有这行代码，agent.py 不能把旧私有函数委托给新模块。
    normalized_tool_name = str(tool_name or "").strip()  # 修改代码+McpImageReinjection: 先规范化工具名再判断旧名或 MCP 前缀；如果没有这行代码，带空白的工具名会漏过截图回灌。
    if normalized_tool_name not in COMPUTER_USE_IMAGE_TOOL_NAMES and not normalized_tool_name.startswith(COMPUTER_USE_IMAGE_TOOL_PREFIXES):  # 修改代码+McpImageReinjection: 同时接受旧内部工具和 mcp__computer-use__ 原子工具；如果没有这行代码，模型调用新 MCP observe 后下一轮仍看不到截图像素。
        return None  # 新增代码+AgentPySplitPhase1: 非 Computer Use 工具不生成图片消息；如果没有这行代码，普通工具结果会污染多模态上下文。
    image_blocks = build_computer_use_image_blocks_from_tool_output(output, record_observation=record_observation)  # 新增代码+AgentPySplitPhase1: 从工具文本里提取并编码图片块；如果没有这行代码，后续消息只有壳没有图片内容。
    if not image_blocks:  # 新增代码+AgentPySplitPhase1: 没有可用截图时不追加多模态消息；如果没有这行代码，模型上下文会出现空 user 消息噪音。
        return None  # 新增代码+AgentPySplitPhase1: 返回 None 表示保持普通文本工具结果；如果没有这行代码，调用方无法区分有图和无图。
    content_blocks: list[dict[str, Any]] = [{"type": "text", "text": f"Computer Use screenshot pixels from {tool_name}; use this image together with the preceding tool result to plan the next desktop action."}]  # 新增代码+AgentPySplitPhase1: 加一段英文说明保持原模型提示行为不变；如果没有这行代码，图片和前一条工具结果的关系会变模糊。
    content_blocks.extend(image_blocks)  # 新增代码+AgentPySplitPhase1: 把真实 image_url 图片块接到说明后面；如果没有这行代码，模型仍然收不到截图像素。
    return {"role": "user", "content": content_blocks}  # 新增代码+AgentPySplitPhase1: 返回 OpenAI 兼容的多模态 user 消息；如果没有这行代码，主循环无法把图片加入下一轮模型输入。
# 新增代码+AgentPySplitPhase1: 函数段结束，build_computer_use_image_message_from_tool_output 到此结束；如果没有这个边界说明，用户不容易看出图片消息构造范围。


def _resolve_computer_use_artifact_path(artifact_path: Path) -> Path:  # 新增代码+ComputerUseAdaptiveImagePath: 函数段开始，把旧 wrapper 文本里的漂移路径修回真实 evidence 文件；如果没有这段函数，真实 observe 可能只返回不存在的旧目录路径。
    if artifact_path.is_file():  # 新增代码+ComputerUseAdaptiveImagePath: 原路径真实存在时直接使用；如果没有这行代码，正常路径也会多做兜底推断。
        return artifact_path  # 新增代码+ComputerUseAdaptiveImagePath: 返回原始可读文件；如果没有这行代码，调用方拿不到正确路径。
    path_parts = list(artifact_path.parts)  # 新增代码+ComputerUseAdaptiveImagePath: 拆开路径片段便于识别 memory/<bucket>/evidence 结构；如果没有这行代码，Windows 反斜杠路径很难安全替换。
    evidence_indices = [index for index, part in enumerate(path_parts) if str(part).lower() == "evidence"]  # 新增代码+ComputerUseAdaptiveImagePath: 找到 evidence 目录位置；如果没有这行代码，函数不知道该替换哪一层 bucket。
    if not evidence_indices:  # 新增代码+ComputerUseAdaptiveImagePath: 没有 evidence 目录时说明不是受控截图路径；如果没有这行代码，任意路径都可能被错误改写。
        return artifact_path  # 新增代码+ComputerUseAdaptiveImagePath: 返回原路径交给上层跳过；如果没有这行代码，异常路径可能继续拼错。
    evidence_index = evidence_indices[-1]  # 新增代码+ComputerUseAdaptiveImagePath: 使用最后一个 evidence 片段贴近真实文件名位置；如果没有这行代码，深层路径可能替换到错误层级。
    if evidence_index < 1:  # 新增代码+ComputerUseAdaptiveImagePath: evidence 前面没有 bucket 时无法安全替换；如果没有这行代码，切片可能生成无意义路径。
        return artifact_path  # 新增代码+ComputerUseAdaptiveImagePath: 保守返回原路径；如果没有这行代码，坏路径会变得更难排查。
    repaired_parts = path_parts[: evidence_index - 1] + ["computer_use", "evidence", artifact_path.name]  # 新增代码+ComputerUseAdaptiveImagePath: 把旧 mcp__computer-use__computer_batch bucket 改回真实 computer_use bucket；如果没有这行代码，兜底无法找到实际 BMP。
    repaired_path = Path(*repaired_parts)  # 新增代码+ComputerUseAdaptiveImagePath: 重新组装候选路径；如果没有这行代码，后续不能检查文件是否存在。
    if repaired_path.is_file():  # 新增代码+ComputerUseAdaptiveImagePath: 只有候选真实存在才接受修复；如果没有这行代码，可能把一个坏路径换成另一个坏路径。
        return repaired_path  # 新增代码+ComputerUseAdaptiveImagePath: 返回真实 evidence 文件；如果没有这行代码，模型图片块仍会因为旧路径不存在而丢失。
    return artifact_path  # 新增代码+ComputerUseAdaptiveImagePath: 兜底失败时保留原路径由上层跳过；如果没有这行代码，函数没有稳定返回值。
# 新增代码+ComputerUseAdaptiveImagePath: 函数段结束，_resolve_computer_use_artifact_path 到此结束；如果没有这个边界说明，用户不容易看出路径修复范围。


# 新增代码+AgentPySplitPhase1: 函数段开始，build_computer_use_image_blocks_from_tool_output 把工具输出里的 image_result 行转成 image_url 块；如果没有这段函数，artifact_path 不能变成模型可读图片。
def build_computer_use_image_blocks_from_tool_output(output: str, record_observation: RecordObservation | None = None) -> list[dict[str, Any]]:  # 新增代码+AgentPySplitPhase1: 定义图片块提取入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    image_specs = extract_computer_use_image_specs_from_tool_output(output)  # 新增代码+AgentPySplitPhase1: 先解析图片路径和 MIME 元数据；如果没有这行代码，后续不知道要读取哪些截图文件。
    image_blocks: list[dict[str, Any]] = []  # 新增代码+AgentPySplitPhase1: 准备保存最终 image_url 块；如果没有这行代码，多张截图无法累积。
    for spec in image_specs:  # 新增代码+AgentPySplitPhase1: 逐张处理工具结果里的图片引用；如果没有这行代码，多图输出只能处理零张或一张。
        artifact_path = Path(str(spec.get("artifact_path", "") or ""))  # 新增代码+AgentPySplitPhase1: 把 artifact_path 转为 Path 对象；如果没有这行代码，文件存在性检查会不稳定。
        resolved_artifact_path = _resolve_computer_use_artifact_path(artifact_path)  # 新增代码+ComputerUseAdaptiveImagePath: 兼容真实 MCP observe 中历史旧目录路径；如果没有这行代码，截图会因为路径漂移无法进入模型。
        if not resolved_artifact_path.is_file():  # 修改代码+ComputerUseAdaptiveImagePath: 跳过修复后仍不存在的路径；如果没有这行代码，一个坏路径会中断整个工具循环。
            continue  # 新增代码+AgentPySplitPhase1: 继续尝试下一张截图；如果没有这行代码，后面的有效截图也会被坏路径拖累。
        if resolved_artifact_path != artifact_path:  # 新增代码+ComputerUseAdaptiveImagePath: 检测本次是否发生路径修复；如果没有这行代码，诊断日志看不到为什么旧路径还能成功。
            _record_image_observation(record_observation, "computer_use_image_artifact_path_repaired", {"artifact_path": str(artifact_path), "resolved_artifact_path": str(resolved_artifact_path)})  # 新增代码+ComputerUseAdaptiveImagePath: 记录旧路径和真实路径；如果没有这行代码，用户排查时不知道路径漂移已被兜底处理。
        image_payload = build_computer_use_model_image_payload(resolved_artifact_path, spec.get("mime_type"), MAX_COMPUTER_USE_MODEL_IMAGE_BYTES, record_observation=record_observation, image_source=spec.get("source", ""))  # 修改代码+ComputerUseAdaptiveImagePath: 读取修复后的截图并按尺寸/来源自适应输出 PNG 或 JPEG；如果没有这行代码，路径修复不会真正参与编码。
        if image_payload is None:  # 新增代码+AgentPySplitPhase1: 处理读取失败、空图、过大图或转码失败；如果没有这行代码，后续解包 None 会崩溃。
            continue  # 新增代码+AgentPySplitPhase1: 跳过当前坏图并保留其它截图机会；如果没有这行代码，一张坏图会阻断所有图片。
        image_bytes, mime_type = image_payload  # 新增代码+AgentPySplitPhase1: 取出模型兼容的图片字节和 MIME；如果没有这行代码，base64 编码不知道要处理哪份数据。
        encoded_image = base64.b64encode(image_bytes).decode("ascii")  # 新增代码+AgentPySplitPhase1: 把二进制图片变成 ASCII base64；如果没有这行代码，JSON 消息不能携带原始字节。
        image_blocks.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_image}", "detail": "high"}})  # 新增代码+AgentPySplitPhase1: 生成模型 API 兼容图片块；如果没有这行代码，模型看不到截图。
    return image_blocks  # 新增代码+AgentPySplitPhase1: 返回所有可用图片块；如果没有这行代码，调用方拿不到构造结果。
# 新增代码+AgentPySplitPhase1: 函数段结束，build_computer_use_image_blocks_from_tool_output 到此结束；如果没有这个边界说明，用户不容易看出图片块处理范围。


# 新增代码+ComputerUseAdaptiveImage: 函数段开始，should_use_lossless_model_image 判断外部模型图片是否应该保持 PNG；如果没有这段函数，JPEG/PNG 选择会散落且难以解释。
def should_use_lossless_model_image(width: int, height: int, image_source: Any = "") -> bool:  # 新增代码+ComputerUseAdaptiveImage: 定义自适应保真判断入口；如果没有这行代码，调用方无法复用同一套压缩策略。
    source_text = str(image_source or "").lower()  # 新增代码+ComputerUseAdaptiveImage: 规范化来源提示；如果没有这行代码，Zoom/zoom 大小写差异会影响策略。
    if any(token in source_text for token in COMPUTER_USE_LOSSLESS_SOURCE_HINTS):  # 新增代码+ComputerUseAdaptiveImage: 局部/放大截图优先保真；如果没有这行代码，文字密集区域可能被 JPEG 模糊。
        return True  # 新增代码+ComputerUseAdaptiveImage: 返回保真策略；如果没有这行代码，zoom/crop 提示不会生效。
    pixel_count = max(0, int(width)) * max(0, int(height))  # 新增代码+ComputerUseAdaptiveImage: 计算像素总量；如果没有这行代码，无法区分小 UI 图和全屏大图。
    return pixel_count <= COMPUTER_USE_LOSSLESS_MAX_PIXELS  # 新增代码+ComputerUseAdaptiveImage: 小图用 PNG，大图用 JPEG；如果没有这行代码，外部压缩不会随图片规模变化。
# 新增代码+ComputerUseAdaptiveImage: 函数段结束，should_use_lossless_model_image 到此结束；如果没有这个边界说明，用户不容易看出自适应判断范围。


# 新增代码+ComputerUseAdaptiveImage: 函数段开始，_encode_png_model_bytes 把图片像素编码成模型可接收的 PNG；如果没有这段函数，小图和 zoom 无法保持无损清晰。
def _encode_png_model_bytes(image: Any) -> bytes:  # 新增代码+ComputerUseAdaptiveImage: 定义 PNG 编码 helper；如果没有这行代码，PNG 保存逻辑会重复出现在多个分支。
    from io import BytesIO  # 新增代码+ComputerUseAdaptiveImage: 导入内存缓冲区；如果没有这行代码，编码必须落临时文件增加清理风险。
    buffer = BytesIO()  # 新增代码+ComputerUseAdaptiveImage: 创建内存输出容器；如果没有这行代码，Pillow 没有写出位置。
    image.save(buffer, format="PNG", optimize=True)  # 新增代码+ComputerUseAdaptiveImage: 以 PNG 无损格式保存像素；如果没有这行代码，小字截图无法保真进入模型。
    return buffer.getvalue()  # 新增代码+ComputerUseAdaptiveImage: 返回 PNG 字节；如果没有这行代码，调用方拿不到可 base64 的数据。
# 新增代码+ComputerUseAdaptiveImage: 函数段结束，_encode_png_model_bytes 到此结束；如果没有这个边界说明，用户不容易看出 PNG 编码范围。


# 新增代码+ComputerUseAdaptiveImage: 函数段开始，_encode_jpeg_model_bytes 把大截图编码成 ClaudeCode 风格 JPEG；如果没有这段函数，全屏截图会继续用较大的 PNG 传输。
def _encode_jpeg_model_bytes(image: Any) -> bytes:  # 新增代码+ComputerUseAdaptiveImage: 定义 JPEG 编码 helper；如果没有这行代码，JPEG 质量和 RGB 转换会分散。
    from io import BytesIO  # 新增代码+ComputerUseAdaptiveImage: 导入内存缓冲区；如果没有这行代码，JPEG 编码必须落临时文件。
    rgb_image = image.convert("RGB") if getattr(image, "mode", "") != "RGB" else image.copy()  # 新增代码+ComputerUseAdaptiveImage: JPEG 需要 RGB 像素；如果没有这行代码，RGBA/P 模式图片可能保存失败。
    buffer = BytesIO()  # 新增代码+ComputerUseAdaptiveImage: 创建内存输出容器；如果没有这行代码，Pillow 没有 JPEG 写出位置。
    rgb_image.save(buffer, format="JPEG", quality=COMPUTER_USE_JPEG_QUALITY, optimize=True)  # 新增代码+ComputerUseAdaptiveImage: 使用 75 质量输出 JPEG；如果没有这行代码，外部链路不能对齐 ClaudeCode 的性能取向。
    return buffer.getvalue()  # 新增代码+ComputerUseAdaptiveImage: 返回 JPEG 字节；如果没有这行代码，调用方无法生成 base64 图片块。
# 新增代码+ComputerUseAdaptiveImage: 函数段结束，_encode_jpeg_model_bytes 到此结束；如果没有这个边界说明，用户不容易看出 JPEG 编码范围。


# 新增代码+ComputerUseAdaptiveImage: 函数段开始，_encode_jpeg_with_budget 在超大截图时逐步缩小 JPEG；如果没有这段函数，极端分辨率可能仍超过模型请求上限。
def _encode_jpeg_with_budget(image: Any, max_image_bytes: int) -> bytes | None:  # 新增代码+ComputerUseAdaptiveImage: 定义预算内 JPEG 编码入口；如果没有这行代码，超大图只能直接失败。
    working_image = image  # 新增代码+ComputerUseAdaptiveImage: 保存当前待编码图片；如果没有这行代码，缩放循环没有状态。
    for _attempt in range(6):  # 新增代码+ComputerUseAdaptiveImage: 最多尝试 6 次降采样；如果没有这行代码，异常大图可能无限压缩循环。
        jpeg_bytes = _encode_jpeg_model_bytes(working_image)  # 新增代码+ComputerUseAdaptiveImage: 编码当前尺寸 JPEG；如果没有这行代码，无法检查当前尺寸是否满足预算。
        if jpeg_bytes and len(jpeg_bytes) <= max_image_bytes:  # 新增代码+ComputerUseAdaptiveImage: 检查字节数是否在模型上限内；如果没有这行代码，可能把过大图片继续发给模型。
            return jpeg_bytes  # 新增代码+ComputerUseAdaptiveImage: 返回预算内 JPEG；如果没有这行代码，成功压缩结果会被丢弃。
        width, height = getattr(working_image, "size", (0, 0))  # 新增代码+ComputerUseAdaptiveImage: 读取当前图片尺寸；如果没有这行代码，无法决定下一轮缩小到多少。
        if width <= 256 or height <= 256:  # 新增代码+ComputerUseAdaptiveImage: 防止过度缩小导致模型看不清；如果没有这行代码，超大图可能被压成不可用缩略图。
            break  # 新增代码+ComputerUseAdaptiveImage: 达到最小可用尺寸就停止；如果没有这行代码，循环会继续破坏可读性。
        new_size = (max(1, int(width * 0.75)), max(1, int(height * 0.75)))  # 新增代码+ComputerUseAdaptiveImage: 每轮缩小 25%；如果没有这行代码，无法逐步降低 JPEG 体积。
        working_image = working_image.resize(new_size)  # 新增代码+ComputerUseAdaptiveImage: 生成下一轮较小图片；如果没有这行代码，重复编码仍是同一张超大图。
    return None  # 新增代码+ComputerUseAdaptiveImage: 无法压进预算时返回 None；如果没有这行代码，调用方无法区分失败和空字节。
# 新增代码+ComputerUseAdaptiveImage: 函数段结束，_encode_jpeg_with_budget 到此结束；如果没有这个边界说明，用户不容易看出预算压缩范围。


# 新增代码+ComputerUseAdaptiveImage: 函数段开始，build_computer_use_adaptive_model_payload_from_artifact 从内部保真 artifact 生成外部模型图片；如果没有这段函数，BMP/PNG/JPEG 选择无法集中审计。
def build_computer_use_adaptive_model_payload_from_artifact(artifact_path: Path, raw_mime_type: Any, max_image_bytes: int, record_observation: RecordObservation | None = None, image_source: Any = "") -> tuple[bytes, str] | None:  # 新增代码+ComputerUseAdaptiveImage: 定义自适应模型图片入口；如果没有这行代码，模型出口无法同时支持保真和压缩。
    mime_type = normalize_computer_use_model_image_mime_type(raw_mime_type, artifact_path)  # 新增代码+ComputerUseAdaptiveImage: 规范化内部 artifact MIME；如果没有这行代码，策略不知道源图真实类型。
    try:  # 新增代码+ComputerUseAdaptiveImage: 延迟导入 Pillow；如果没有这行代码，非截图路径也会强依赖图片库。
        from PIL import Image  # 新增代码+ComputerUseAdaptiveImage: 导入图片解码器；如果没有这行代码，BMP 无法变成模型支持的 PNG/JPEG。
    except Exception as error:  # 新增代码+ComputerUseAdaptiveImage: 捕获 Pillow 不可用；如果没有这行代码，缺依赖会中断整个 agent 轮次。
        _record_image_observation(record_observation, "computer_use_adaptive_image_unavailable", {"artifact_path": str(artifact_path), "error": str(error)})  # 新增代码+ComputerUseAdaptiveImage: 记录自适应编码不可用；如果没有这行代码，用户不知道截图为什么没进模型。
        return None  # 新增代码+ComputerUseAdaptiveImage: 没有可靠解码能力就不发坏图；如果没有这行代码，BMP 可能被错误 MIME 伪装。
    try:  # 新增代码+ComputerUseAdaptiveImage: 捕获图片读取或转码错误；如果没有这行代码，坏截图会让主循环崩溃。
        with Image.open(artifact_path) as image:  # 新增代码+ComputerUseAdaptiveImage: 打开内部 artifact；如果没有这行代码，无法读取真实截图像素。
            image.load()  # 新增代码+ComputerUseAdaptiveImage: 立刻加载像素避免文件关闭后懒读取失败；如果没有这行代码，后续编码可能读不到文件。
            width, height = getattr(image, "size", (0, 0))  # 新增代码+ComputerUseAdaptiveImage: 读取截图尺寸；如果没有这行代码，自适应策略无法区分小图和大图。
            if should_use_lossless_model_image(int(width), int(height), image_source):  # 新增代码+ComputerUseAdaptiveImage: 小图或局部图优先走 PNG；如果没有这行代码，UI 文字会被不必要 JPEG 压缩。
                png_bytes = _encode_png_model_bytes(image)  # 新增代码+ComputerUseAdaptiveImage: 编码 PNG 保真载荷；如果没有这行代码，保真分支没有实际输出。
                if png_bytes and len(png_bytes) <= max_image_bytes:  # 新增代码+ComputerUseAdaptiveImage: 检查 PNG 是否满足模型上限；如果没有这行代码，过大 PNG 可能撑爆请求。
                    return png_bytes, "image/png"  # 新增代码+ComputerUseAdaptiveImage: 返回无损 PNG；如果没有这行代码，小图/zoom 会错误落到 JPEG。
                _record_image_observation(record_observation, "computer_use_png_payload_exceeded_budget", {"artifact_path": str(artifact_path), "byte_count": len(png_bytes), "max_image_bytes": max_image_bytes})  # 新增代码+ComputerUseAdaptiveImage: 记录 PNG 太大后降级 JPEG；如果没有这行代码，排查时看不到为什么保真失败。
            jpeg_bytes = _encode_jpeg_with_budget(image, max_image_bytes)  # 新增代码+ComputerUseAdaptiveImage: 大图或超预算 PNG 改用 JPEG 压缩；如果没有这行代码，全屏截图会继续走过大的无损格式。
    except Exception as error:  # 新增代码+ComputerUseAdaptiveImage: 捕获坏图片、文件被占用或编码失败；如果没有这行代码，异常会冒泡到用户任务。
        _record_image_observation(record_observation, "computer_use_adaptive_image_failed", {"artifact_path": str(artifact_path), "mime_type": mime_type, "error": str(error)})  # 新增代码+ComputerUseAdaptiveImage: 记录失败原因；如果没有这行代码，用户只能看到截图没有进入模型。
        return None  # 新增代码+ComputerUseAdaptiveImage: 转码失败时跳过该图；如果没有这行代码，后续会解包未定义结果。
    if jpeg_bytes and len(jpeg_bytes) <= max_image_bytes:  # 新增代码+ComputerUseAdaptiveImage: 检查 JPEG 压缩结果是否合格；如果没有这行代码，过大 JPEG 可能继续进入请求。
        return jpeg_bytes, "image/jpeg"  # 新增代码+ComputerUseAdaptiveImage: 返回 ClaudeCode 风格 JPEG；如果没有这行代码，大图无法缩短模型链路。
    _record_image_observation(record_observation, "computer_use_image_skipped_for_model", {"artifact_path": str(artifact_path), "byte_count": len(jpeg_bytes or b""), "max_image_bytes": max_image_bytes, "adaptive_format": "image/jpeg"})  # 新增代码+ComputerUseAdaptiveImage: 记录最终仍超预算；如果没有这行代码，用户不知道为什么无图片。
    return None  # 新增代码+ComputerUseAdaptiveImage: 无法生成合格图片时返回 None；如果没有这行代码，调用方可能发出空图片块。
# 新增代码+ComputerUseAdaptiveImage: 函数段结束，build_computer_use_adaptive_model_payload_from_artifact 到此结束；如果没有这个边界说明，用户不容易看出外部模型图片生成范围。


# 修改代码+ComputerUseAdaptiveImage: 函数段开始，build_computer_use_model_image_payload 统一把内部 artifact 变成模型支持的自适应图片载荷；如果没有这段函数，读图、限流、转码逻辑会重新塞回 agent.py。
def build_computer_use_model_image_payload(artifact_path: Path, raw_mime_type: Any, max_image_bytes: int, record_observation: RecordObservation | None = None, image_source: Any = "") -> tuple[bytes, str] | None:  # 修改代码+ComputerUseAdaptiveImage: 定义图片载荷构造函数并接收来源提示；如果没有这行代码，外层无法影响 PNG/JPEG 选择。
    mime_type = normalize_computer_use_model_image_mime_type(raw_mime_type, artifact_path)  # 修改代码+ComputerUseAdaptiveImage: 先规范化工具输出或文件后缀里的 MIME；如果没有这行代码，代码不知道是否需要转码。
    if mime_type == "image/png":  # 新增代码+ComputerUseAdaptiveImage: PNG 先走小图原样兼容分支；如果没有这行代码，历史 fake PNG 测试会被 Pillow 严格解码破坏。
        try:  # 新增代码+ComputerUseAdaptiveImage: 捕获 PNG 文件读取异常；如果没有这行代码，坏路径会直接中断主循环。
            image_bytes = artifact_path.read_bytes()  # 新增代码+ComputerUseAdaptiveImage: 读取 PNG artifact 原始字节；如果没有这行代码，无法判断是否可以原样发送。
        except OSError as error:  # 新增代码+ComputerUseAdaptiveImage: 处理文件读取失败；如果没有这行代码，底层 OSError 会直接冒泡。
            _record_image_observation(record_observation, "computer_use_image_read_failed", {"artifact_path": str(artifact_path), "error": str(error)})  # 新增代码+ComputerUseAdaptiveImage: 记录 PNG 读取失败；如果没有这行代码，用户不知道哪张图没进模型。
            return None  # 新增代码+ComputerUseAdaptiveImage: 读取失败时返回 None；如果没有这行代码，后续会继续处理不存在字节。
        if image_bytes and len(image_bytes) <= min(max_image_bytes, COMPUTER_USE_LOSSLESS_MAX_BYTES):  # 新增代码+ComputerUseAdaptiveImage: 小 PNG 保持无损原样；如果没有这行代码，UI 小字可能被无意义 JPEG 化。
            return image_bytes, "image/png"  # 新增代码+ComputerUseAdaptiveImage: 返回原始 PNG；如果没有这行代码，小图保真和旧兼容都会丢失。
        if not image_bytes:  # 新增代码+ComputerUseAdaptiveImage: 空 PNG 直接拒绝；如果没有这行代码，空图片会进入 Pillow 产生噪声异常。
            _record_image_observation(record_observation, "computer_use_image_skipped_for_model", {"artifact_path": str(artifact_path), "byte_count": 0, "max_image_bytes": max_image_bytes})  # 新增代码+ComputerUseAdaptiveImage: 记录空 PNG 被跳过；如果没有这行代码，排查时看不到原因。
            return None  # 新增代码+ComputerUseAdaptiveImage: 返回 None 表示无可用图片；如果没有这行代码，后续会编码空数据。
        return build_computer_use_adaptive_model_payload_from_artifact(artifact_path, mime_type, max_image_bytes, record_observation=record_observation, image_source=image_source)  # 新增代码+ComputerUseAdaptiveImage: 大 PNG 再进入自适应压缩；如果没有这行代码，超大 PNG 会继续撑大请求。
    if mime_type in {"image/bmp", "image/webp"}:  # 修改代码+ComputerUseAdaptiveImage: BMP/WebP 统一走自适应模型编码；如果没有这行代码，BMP 无法安全进入模型。
        return build_computer_use_adaptive_model_payload_from_artifact(artifact_path, mime_type, max_image_bytes, record_observation=record_observation, image_source=image_source)  # 新增代码+ComputerUseAdaptiveImage: 从内部保真 artifact 生成模型载荷；如果没有这行代码，BMP 无法安全进入模型。
    try:  # 新增代码+AgentPySplitPhase1: 捕获普通图片读取异常；如果没有这行代码，权限或并发写入问题会让 agent 主循环崩溃。
        image_bytes = artifact_path.read_bytes()  # 新增代码+AgentPySplitPhase1: 读取 PNG/JPEG/WebP 等模型支持图片；如果没有这行代码，无法生成 base64 data URL。
    except OSError as error:  # 新增代码+AgentPySplitPhase1: 处理文件读取失败；如果没有这行代码，底层 OSError 会直接冒泡到用户任务。
        _record_image_observation(record_observation, "computer_use_image_read_failed", {"artifact_path": str(artifact_path), "error": str(error)})  # 新增代码+AgentPySplitPhase1: 记录哪张图读失败；如果没有这行代码，排查时只能看到图片没有进入模型。
        return None  # 新增代码+AgentPySplitPhase1: 告诉调用方当前图片不可用；如果没有这行代码，失败路径会继续尝试编码不存在的字节。
    if not image_bytes or len(image_bytes) > max_image_bytes:  # 新增代码+AgentPySplitPhase1: 拒绝空图片和超大图片；如果没有这行代码，模型可能收到无效或过大的图片块。
        _record_image_observation(record_observation, "computer_use_image_skipped_for_model", {"artifact_path": str(artifact_path), "byte_count": len(image_bytes), "max_image_bytes": max_image_bytes})  # 新增代码+AgentPySplitPhase1: 记录图片被跳过的具体原因；如果没有这行代码，用户不知道为什么截图没进模型。
        return None  # 新增代码+AgentPySplitPhase1: 跳过不合格图片；如果没有这行代码，后续仍会把异常图片编码进上下文。
    return image_bytes, mime_type  # 新增代码+AgentPySplitPhase1: 返回可直接发送给模型的字节和 MIME；如果没有这行代码，调用方拿不到最终载荷。
# 新增代码+AgentPySplitPhase1: 函数段结束，build_computer_use_model_image_payload 到此结束；如果没有这个边界说明，用户不容易看出模型图片载荷处理范围。


# 新增代码+AgentPySplitPhase1: 函数段开始，extract_computer_use_image_specs_from_tool_output 从工具文本中解析图片路径和 MIME；如果没有这段函数，主循环需要理解完整工具输出格式，耦合会更重。
def extract_computer_use_image_specs_from_tool_output(output: str) -> list[dict[str, str]]:  # 新增代码+AgentPySplitPhase1: 定义 image_result 文本解析函数；如果没有这行代码，图片路径提取会散落到 agent.py。
    specs_by_index: dict[str, dict[str, str]] = {}  # 新增代码+AgentPySplitPhase1: 按 image_0/image_1 聚合字段；如果没有这行代码，路径和 MIME 无法稳定配对。
    for raw_line in str(output or "").splitlines():  # 新增代码+AgentPySplitPhase1: 逐行读取工具输出；如果没有这行代码，无法解析格式化图片区。
        line = raw_line.strip()  # 新增代码+AgentPySplitPhase1: 去掉首尾空白；如果没有这行代码，前导空格会影响字段匹配。
        if not line.startswith("- image_") or "=" not in line:  # 新增代码+AgentPySplitPhase1: 只处理图片区字段行；如果没有这行代码，普通文本可能被误解析。
            continue  # 新增代码+AgentPySplitPhase1: 跳过非图片字段；如果没有这行代码，后续字符串切分会碰到无关行。
        key, value = line[2:].split("=", 1)  # 新增代码+AgentPySplitPhase1: 拆分字段名和值；如果没有这行代码，无法取出 artifact_path 或 mime_type。
        key_parts = key.split("_")  # 新增代码+AgentPySplitPhase1: 把 image_0_artifact_path 拆成片段；如果没有这行代码，无法识别图片序号。
        if len(key_parts) < 3 or key_parts[0] != "image":  # 新增代码+AgentPySplitPhase1: 校验字段名结构；如果没有这行代码，异常字段可能污染 specs。
            continue  # 新增代码+AgentPySplitPhase1: 跳过不合规字段；如果没有这行代码，后续 index 读取可能错误。
        image_index = key_parts[1]  # 新增代码+AgentPySplitPhase1: 读取图片序号；如果没有这行代码，多张图片字段无法聚合。
        field_name = "_".join(key_parts[2:])  # 新增代码+AgentPySplitPhase1: 还原字段名后缀；如果没有这行代码，artifact_path 这类字段会被拆散。
        spec = specs_by_index.setdefault(image_index, {})  # 新增代码+AgentPySplitPhase1: 获取当前图片的聚合字典；如果没有这行代码，字段无法保存。
        if field_name in {"artifact_path", "mime_type", "source"}:  # 修改代码+ComputerUseAdaptiveImage: 保留路径、MIME 和来源提示；如果没有这行代码，zoom/crop 无法触发 PNG 保真策略。
            spec[field_name] = value.strip()  # 新增代码+AgentPySplitPhase1: 保存清理后的字段值；如果没有这行代码，路径可能带多余空白。
    line_specs = [spec for _, spec in sorted(specs_by_index.items()) if spec.get("artifact_path")]  # 修改代码+McpImageReinjection: 先保存裸文本行解析结果；如果没有这行代码，后续 JSON fallback 会覆盖已成功解析的旧工具输出。
    if line_specs:  # 修改代码+McpImageReinjection: 裸文本已找到图片时直接返回；如果没有这行代码，旧工具输出会多做不必要 JSON 解析。
        return line_specs  # 修改代码+McpImageReinjection: 返回旧格式图片引用；如果没有这行代码，旧 computer_observe 回灌会被延迟或误处理。
    try:  # 修改代码+McpImageReinjection: 尝试解析 MCP adapter 包装的 JSON 输出；如果没有这行代码，新 MCP observe 的 legacy_text 永远不会被读取。
        parsed_output = json.loads(str(output or ""))  # 修改代码+McpImageReinjection: 把工具文本解析成 JSON 对象；如果没有这行代码，payload.legacy_text 无法结构化访问。
    except (TypeError, ValueError, json.JSONDecodeError):  # 修改代码+McpImageReinjection: 非 JSON 输出仍按无图处理；如果没有这行代码，普通无图工具结果会抛异常中断主循环。
        return []  # 修改代码+McpImageReinjection: 无法解析 JSON 时返回空列表；如果没有这行代码，调用方拿不到稳定空结果。
    if isinstance(parsed_output, dict):  # 新增代码+ClaudeCodeContentParity：先读取新协议 debug 字段；如果没有这行代码，result.debug.artifact_path 里的截图路径无法回灌。
        debug = parsed_output.get("debug", {})  # 新增代码+ClaudeCodeContentParity：获取顶层 debug 信息；如果没有这行代码，artifact_path 无法结构化读取。
        if isinstance(debug, dict) and debug.get("artifact_path"):  # 新增代码+ClaudeCodeContentParity：确认 debug 里有可用截图路径；如果没有这行代码，空 debug 会被误加入图片列表。
            return [{"artifact_path": str(debug.get("artifact_path") or ""), "mime_type": str(debug.get("mime_type") or "")}]  # 新增代码+ClaudeCodeContentParity：返回新协议调试路径作为图片引用；如果没有这行代码，JSON 文本链路看不到 screenshot 像素。
    payload = parsed_output.get("payload", {}) if isinstance(parsed_output, dict) else {}  # 修改代码+McpImageReinjection: 读取 MCP 包装中的 payload；如果没有这行代码，非字典 JSON 会触发属性错误。
    nested_candidates: list[str] = []  # 新增代码+ComputerUseRawImageReinjection：收集 v2 MCP adapter 可能放置原始图片区的文本字段；如果没有这行代码，深层 legacy_result.text 里的截图路径无法进入模型。
    if isinstance(payload, dict):  # 新增代码+ComputerUseRawImageReinjection：只有 payload 是字典时才读取受控字段；如果没有这行代码，异常 JSON 结构会触发属性错误。
        legacy_text = payload.get("legacy_text", "")  # 修改代码+ComputerUseRawImageReinjection：兼容浅层 legacy_text 字段；如果没有这行代码，较早 adapter 包装输出会丢失截图。
        if isinstance(legacy_text, str) and legacy_text:  # 新增代码+ComputerUseRawImageReinjection：只收集非空字符串；如果没有这行代码，空值会造成无意义递归解析。
            nested_candidates.append(legacy_text)  # 新增代码+ComputerUseRawImageReinjection：保存浅层候选文本；如果没有这行代码，浅层输出不会被后续统一处理。
        legacy_result = payload.get("legacy_result", {})  # 新增代码+ComputerUseRawImageReinjection：读取 agent-side adapter 的深层 legacy_result；如果没有这行代码，v2 observe 的真实图片文本仍藏在包装 JSON 里。
        if isinstance(legacy_result, dict):  # 新增代码+ComputerUseRawImageReinjection：只有 legacy_result 是字典时才继续读取；如果没有这行代码，异常字段类型会打断工具循环。
            result_text = legacy_result.get("text", "")  # 新增代码+ComputerUseRawImageReinjection：读取 legacy_result.text 里的完整工具文本；如果没有这行代码，长 observe 输出中的 Computer Use Image Results 不会被解析。
            if isinstance(result_text, str) and result_text:  # 新增代码+ComputerUseRawImageReinjection：只收集非空字符串结果；如果没有这行代码，空文本会进入递归。
                nested_candidates.append(result_text)  # 新增代码+ComputerUseRawImageReinjection：保存深层 text 候选；如果没有这行代码，图片路径仍只留在文本摘要里。
            result_payload = legacy_result.get("payload", {})  # 新增代码+ComputerUseRawImageReinjection：读取 legacy_result.payload；如果没有这行代码，最内层 legacy_text 无法被发现。
            if isinstance(result_payload, dict):  # 新增代码+ComputerUseRawImageReinjection：确认内层 payload 是字典；如果没有这行代码，异常类型会触发属性错误。
                result_legacy_text = result_payload.get("legacy_text", "")  # 新增代码+ComputerUseRawImageReinjection：读取最内层 legacy_text；如果没有这行代码，agent-side adapter 的原始 observe 文本会被跳过。
                if isinstance(result_legacy_text, str) and result_legacy_text:  # 新增代码+ComputerUseRawImageReinjection：只收集非空最内层文本；如果没有这行代码，空字符串会被递归解析。
                    nested_candidates.append(result_legacy_text)  # 新增代码+ComputerUseRawImageReinjection：保存最内层候选；如果没有这行代码，v2 包装下的图片路径无法回灌。
    for nested_text in nested_candidates:  # 新增代码+ComputerUseRawImageReinjection：逐个候选尝试复用既有行解析逻辑；如果没有这行代码，收集到的嵌套文本不会真正生效。
        if nested_text == output:  # 新增代码+ComputerUseRawImageReinjection：避免同一文本无限递归；如果没有这行代码，异常包装可能造成递归循环。
            continue  # 新增代码+ComputerUseRawImageReinjection：跳过当前重复候选；如果没有这行代码，递归保护不会生效。
        nested_specs = extract_computer_use_image_specs_from_tool_output(nested_text)  # 新增代码+ComputerUseRawImageReinjection：从嵌套文本提取 artifact_path 和 MIME；如果没有这行代码，模型仍然收不到截图像素。
        if nested_specs:  # 新增代码+ComputerUseRawImageReinjection：找到图片引用后立即返回；如果没有这行代码，后续空候选可能覆盖成功结果。
            return nested_specs  # 新增代码+ComputerUseRawImageReinjection：返回 v2 包装内的图片引用；如果没有这行代码，图片块构造函数拿不到输入。
    return []  # 修改代码+McpImageReinjection: JSON 包装里也没有图片时返回空；如果没有这行代码，函数缺少稳定兜底返回。
# 新增代码+AgentPySplitPhase1: 函数段结束，extract_computer_use_image_specs_from_tool_output 到此结束；如果没有这个边界说明，用户不容易看出文本解析边界。


# 新增代码+AgentPySplitPhase1: 函数段开始，normalize_computer_use_model_image_mime_type 为模型图片块选择稳定 MIME；如果没有这段函数，data URL 类型可能为空或不被模型 API 接受。
def normalize_computer_use_model_image_mime_type(raw_mime_type: Any, artifact_path: Path) -> str:  # 新增代码+AgentPySplitPhase1: 定义 MIME 规范化函数；如果没有这行代码，图片块可能携带非法 MIME。
    mime_type = str(raw_mime_type or "").strip().lower()  # 新增代码+AgentPySplitPhase1: 清理工具输出中的 MIME；如果没有这行代码，大小写和空白会影响 API 识别。
    if mime_type in {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/bmp"}:  # 新增代码+AgentPySplitPhase1: 接受常见截图 MIME；如果没有这行代码，合法图片类型会被误改。
        return "image/jpeg" if mime_type == "image/jpg" else mime_type  # 新增代码+AgentPySplitPhase1: 把 image/jpg 规范成 image/jpeg；如果没有这行代码，部分模型 API 可能不认别名。
    suffix = artifact_path.suffix.lower().lstrip(".")  # 新增代码+AgentPySplitPhase1: 从文件后缀推断兜底类型；如果没有这行代码，缺 MIME 的旧证据无法传图。
    if suffix == "png":  # 新增代码+AgentPySplitPhase1: 识别 PNG 后缀；如果没有这行代码，PNG 证据会落到默认 JPEG。
        return "image/png"  # 新增代码+AgentPySplitPhase1: 返回 PNG MIME；如果没有这行代码，模型可能按错格式解码。
    if suffix in {"jpg", "jpeg"}:  # 新增代码+AgentPySplitPhase1: 识别 JPEG 后缀；如果没有这行代码，JPEG 证据会落到默认类型。
        return "image/jpeg"  # 新增代码+AgentPySplitPhase1: 返回 JPEG MIME；如果没有这行代码，模型可能按错格式解码。
    if suffix == "webp":  # 新增代码+AgentPySplitPhase1: 识别 WebP 后缀；如果没有这行代码，WebP 证据会落到默认类型。
        return "image/webp"  # 新增代码+AgentPySplitPhase1: 返回 WebP MIME；如果没有这行代码，模型可能按错格式解码。
    if suffix == "bmp":  # 新增代码+AgentPySplitPhase1: 识别 Windows BMP 后缀；如果没有这行代码，BMP 证据会被错误标成 JPEG。
        return "image/bmp"  # 新增代码+AgentPySplitPhase1: 返回 BMP MIME；如果没有这行代码，Windows 截图类型会丢失。
    return "image/jpeg"  # 新增代码+AgentPySplitPhase1: 未知类型使用保守常见图片 MIME；如果没有这行代码，data URL 会缺少稳定类型。
# 新增代码+AgentPySplitPhase1: 函数段结束，normalize_computer_use_model_image_mime_type 到此结束；如果没有这个边界说明，用户不容易看出 MIME 兜底范围。
