"""浏览器页面观察引擎，把页面文本、元素、截图和日志统一成可复验的证据。"""  # 新增代码+BrowserObservationStage4: 说明本模块负责“agent 看到了什么”；若没有这行代码，观察引擎边界不清楚。

from __future__ import annotations  # 新增代码+BrowserObservationStage4: 延迟解析类型注解；若没有这行代码，复杂返回类型可能受定义顺序影响。

import re  # 新增代码+BrowserObservationStage4: 使用正则脱敏 cookie、token、password 等文本；若没有这行代码，只能写脆弱字符串替换。
import secrets  # 新增代码+BrowserObservationStage4: 生成 observation id 和产物文件名；若没有这行代码，多次观察可能撞名。
from pathlib import Path  # 新增代码+BrowserObservationStage4: 管理长文本产物路径；若没有这行代码，Windows 路径拼接更容易错。
from typing import Any  # 新增代码+BrowserObservationStage4: 页面状态来自浏览器 JSON，字段类型需要通用标注；若没有这行代码，类型边界不清楚。

from learning_agent.browser.runtime_models import BrowserObservation, REDACTED_VALUE  # 新增代码+BrowserObservationStage4: 复用稳定协议模型和脱敏占位符；若没有这行代码，观察结果无法落盘。
from learning_agent.runtime.files import atomic_write_text  # 新增代码+BrowserObservationStage4: 使用项目统一原子写长文本产物；若没有这行代码，崩溃可能留下半截证据。

SENSITIVE_TEXT_PATTERNS = (  # 新增代码+BrowserObservationStage4: 集中列出浏览器日志常见敏感文本模式；若没有这行代码，脱敏规则会散落。
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),  # 新增代码+BrowserObservationStage4: 匹配 Bearer token；若没有这行代码，授权头可能进入观察日志。
    re.compile(r"(?i)(cookie\s*[:=]\s*)[^\s,;]+"),  # 新增代码+BrowserObservationStage4: 匹配 cookie 值；若没有这行代码，登录态可能泄露。
    re.compile(r"(?i)(password\s*[:=]\s*)[^\s,;]+"),  # 新增代码+BrowserObservationStage4: 匹配密码字段；若没有这行代码，表单日志可能泄露密码。
    re.compile(r"(?i)(token\s*[:=]\s*)[^\s,;]+"),  # 新增代码+BrowserObservationStage4: 匹配 token 字段；若没有这行代码，普通 token 参数可能泄露。
    re.compile(r"(?i)(secret\s*[:=]\s*)[^\s,;]+"),  # 新增代码+BrowserObservationStage4: 匹配 secret 字段；若没有这行代码，密钥摘要可能泄露。
)  # 新增代码+BrowserObservationStage4: 结束敏感模式列表；若没有这行代码，Python 语法无法闭合。

SENSITIVE_URL_QUERY_KEYS = ("cookie", "token", "password", "secret", "authorization", "session")  # 新增代码+BrowserObservationStage4: 定义 URL query 中需要脱敏的键；若没有这行代码，network URL 可能泄露登录态。


def redact_sensitive_text(text: Any) -> str:  # 新增代码+BrowserObservationStage4: 脱敏浏览器日志和页面摘要文本；若没有这行代码，console/network 可能泄露敏感信息。
    redacted = "" if text is None else str(text)  # 新增代码+BrowserObservationStage4: 把任意输入转成文本；若没有这行代码，None 或数字会让正则处理不稳定。
    for pattern in SENSITIVE_TEXT_PATTERNS:  # 新增代码+BrowserObservationStage4: 逐个应用敏感模式；若没有这行代码，规则不会生效。
        redacted = pattern.sub(lambda match: match.group(1) + REDACTED_VALUE, redacted)  # 新增代码+BrowserObservationStage4: 保留字段名只隐藏值；若没有这行代码，审计会看不到泄露类型。
    for key in SENSITIVE_URL_QUERY_KEYS:  # 新增代码+BrowserObservationStage4: 处理 URL 查询参数中的敏感键；若没有这行代码，?token=... 会漏掉。
        redacted = re.sub(rf"(?i)([?&]{re.escape(key)}=)[^&#\s]+", rf"\1{REDACTED_VALUE}", redacted)  # 新增代码+BrowserObservationStage4: 只替换 query 参数值；若没有这行代码，网络摘要仍可能含 secret。
    return redacted  # 新增代码+BrowserObservationStage4: 返回脱敏文本；若没有这行代码，调用方拿不到结果。


def _text(value: Any) -> str:  # 新增代码+BrowserObservationStage4: 把未知字段转成文本；若没有这行代码，元素字段处理会重复。
    return "" if value is None else str(value)  # 新增代码+BrowserObservationStage4: None 转空串，其余转字符串；若没有这行代码，状态 JSON 可能出现 Python None 文本。


def _number(value: Any, default: int = 0) -> int:  # 新增代码+BrowserObservationStage4: 把坐标和尺寸转成整数；若没有这行代码，元素中心点计算容易报错。
    try:  # 新增代码+BrowserObservationStage4: 捕获坏坐标输入；若没有这行代码，单个坏元素会拖垮整次观察。
        return int(round(float(value)))  # 新增代码+BrowserObservationStage4: 兼容字符串和浮点坐标；若没有这行代码，浏览器 JS 返回的小数不易处理。
    except (TypeError, ValueError):  # 新增代码+BrowserObservationStage4: 处理 None 或非数字文本；若没有这行代码，异常会冒泡。
        return default  # 新增代码+BrowserObservationStage4: 坏坐标使用默认值；若没有这行代码，观察构建器不够健壮。


def normalize_browser_element(raw_element: dict[str, Any], index: int) -> dict[str, Any]:  # 新增代码+BrowserObservationStage4: 把 DOM/视觉候选统一成 locator 可读结构；若没有这行代码，定位引擎要适配多种字段名。
    element_id = _text(raw_element.get("element_id") or raw_element.get("id") or index)  # 新增代码+BrowserObservationStage4: 统一元素 id；若没有这行代码，element_id 可能在数字和字符串间漂移。
    x = _number(raw_element.get("x", raw_element.get("left", 0)))  # 新增代码+BrowserObservationStage4: 读取元素左上角 x；若没有这行代码，中心点无法从 box 计算。
    y = _number(raw_element.get("y", raw_element.get("top", 0)))  # 新增代码+BrowserObservationStage4: 读取元素左上角 y；若没有这行代码，中心点无法从 box 计算。
    width = _number(raw_element.get("width", 0))  # 新增代码+BrowserObservationStage4: 读取元素宽度；若没有这行代码，中心点和面积无法计算。
    height = _number(raw_element.get("height", 0))  # 新增代码+BrowserObservationStage4: 读取元素高度；若没有这行代码，中心点和面积无法计算。
    center_x = _number(raw_element.get("center_x"), x + width // 2)  # 新增代码+BrowserObservationStage4: 优先用浏览器中心点，否则计算；若没有这行代码，坐标点击缺少目标。
    center_y = _number(raw_element.get("center_y"), y + height // 2)  # 新增代码+BrowserObservationStage4: 优先用浏览器中心点，否则计算；若没有这行代码，坐标点击缺少目标。
    label = _text(raw_element.get("label") or raw_element.get("aria_label") or raw_element.get("name"))  # 新增代码+BrowserObservationStage4: 统一 label 字段；若没有这行代码，表单定位缺少可读名称。
    visible_text = _text(raw_element.get("text") or raw_element.get("inner_text") or label)  # 新增代码+BrowserObservationStage4: 统一元素可见文本；若没有这行代码，文本点击无法匹配。
    return {  # 新增代码+BrowserObservationStage4: 返回规范化候选元素；若没有这行代码，调用方拿不到统一结构。
        "element_id": element_id,  # 新增代码+BrowserObservationStage4: 保存稳定元素 id；若没有这行代码，action 无法引用观察元素。
        "role": _text(raw_element.get("role") or raw_element.get("tag")),  # 新增代码+BrowserObservationStage4: 保存 role 或 tag；若没有这行代码，role 定位缺少输入。
        "tag": _text(raw_element.get("tag")),  # 新增代码+BrowserObservationStage4: 保存 DOM tag；若没有这行代码，调试元素类型更困难。
        "label": label,  # 新增代码+BrowserObservationStage4: 保存可访问名称；若没有这行代码，label 定位无法工作。
        "text": visible_text,  # 新增代码+BrowserObservationStage4: 保存可见文本；若没有这行代码，文本定位无法工作。
        "placeholder": _text(raw_element.get("placeholder")),  # 新增代码+BrowserObservationStage4: 保存 placeholder；若没有这行代码，输入框定位不稳定。
        "selector": _text(raw_element.get("selector")),  # 新增代码+BrowserObservationStage4: 保存可执行 CSS selector；若没有这行代码，动作执行器无法复用候选。
        "visible": bool(raw_element.get("visible", True)),  # 新增代码+BrowserObservationStage4: 保存可见性；若没有这行代码，隐藏元素可能被误点。
        "x": x,  # 新增代码+BrowserObservationStage4: 保存左上角 x；若没有这行代码，截图定位缺少几何框。
        "y": y,  # 新增代码+BrowserObservationStage4: 保存左上角 y；若没有这行代码，截图定位缺少几何框。
        "width": width,  # 新增代码+BrowserObservationStage4: 保存宽度；若没有这行代码，候选大小不可审计。
        "height": height,  # 新增代码+BrowserObservationStage4: 保存高度；若没有这行代码，候选大小不可审计。
        "center_x": center_x,  # 新增代码+BrowserObservationStage4: 保存中心 x；若没有这行代码，拟人鼠标点击没有目标点。
        "center_y": center_y,  # 新增代码+BrowserObservationStage4: 保存中心 y；若没有这行代码，拟人鼠标点击没有目标点。
        "box": {"x": x, "y": y, "width": width, "height": height},  # 新增代码+BrowserObservationStage4: 保存标准 box；若没有这行代码，locator/replay 需要重组几何信息。
    }  # 新增代码+BrowserObservationStage4: 结束元素结构；若没有这行代码，Python 字典语法无法闭合。


def _summarize_console(entries: Any, limit: int = 20) -> str:  # 新增代码+BrowserObservationStage4: 生成 console 安全摘要；若没有这行代码，页面脚本错误不易进入证据。
    if not isinstance(entries, list):  # 新增代码+BrowserObservationStage4: 检查 console 输入是否为列表；若没有这行代码，坏字段会导致遍历异常。
        return ""  # 新增代码+BrowserObservationStage4: 非列表按空摘要处理；若没有这行代码，观察构建不够容错。
    lines: list[str] = []  # 新增代码+BrowserObservationStage4: 准备保存 console 行；若没有这行代码，函数没有返回容器。
    for entry in entries[-limit:]:  # 新增代码+BrowserObservationStage4: 只保留最近若干条；若没有这行代码，console 噪声可能撑爆状态。
        if not isinstance(entry, dict):  # 新增代码+BrowserObservationStage4: 跳过坏条目；若没有这行代码，字符串条目会访问失败。
            continue  # 新增代码+BrowserObservationStage4: 继续处理后续条目；若没有这行代码，坏条目会中断摘要。
        lines.append(f"{_text(entry.get('type'))}: {redact_sensitive_text(entry.get('text', ''))}")  # 新增代码+BrowserObservationStage4: 写入脱敏日志行；若没有这行代码，console 信息不会进入 observation。
    return "\n".join(lines)  # 新增代码+BrowserObservationStage4: 返回 console 摘要；若没有这行代码，调用方拿不到结果。


def _summarize_network(entries: Any, limit: int = 40) -> str:  # 新增代码+BrowserObservationStage4: 生成 network 安全摘要；若没有这行代码，请求失败难以复盘。
    if not isinstance(entries, list):  # 新增代码+BrowserObservationStage4: 检查 network 输入是否为列表；若没有这行代码，坏字段会导致遍历异常。
        return ""  # 新增代码+BrowserObservationStage4: 非列表按空摘要处理；若没有这行代码，观察构建不够容错。
    lines: list[str] = []  # 新增代码+BrowserObservationStage4: 准备保存 network 行；若没有这行代码，函数没有返回容器。
    for entry in entries[-limit:]:  # 新增代码+BrowserObservationStage4: 只保留最近请求；若没有这行代码，大页面请求会撑爆状态。
        if not isinstance(entry, dict):  # 新增代码+BrowserObservationStage4: 跳过坏网络条目；若没有这行代码，字符串条目会访问失败。
            continue  # 新增代码+BrowserObservationStage4: 继续处理后续条目；若没有这行代码，坏条目会中断摘要。
        method = _text(entry.get("method"))  # 新增代码+BrowserObservationStage4: 读取请求方法；若没有这行代码，网络摘要缺少动作类型。
        status = _text(entry.get("status"))  # 新增代码+BrowserObservationStage4: 读取响应状态；若没有这行代码，失败请求难以定位。
        url = redact_sensitive_text(entry.get("url", ""))  # 新增代码+BrowserObservationStage4: 脱敏 URL；若没有这行代码，query secret 可能泄露。
        lines.append(f"{method} {status} {url}".strip())  # 新增代码+BrowserObservationStage4: 写入网络摘要行；若没有这行代码，network 信息不会进入 observation。
    return "\n".join(lines)  # 新增代码+BrowserObservationStage4: 返回 network 摘要；若没有这行代码，调用方拿不到结果。


def _write_long_text_artifact(artifact_dir: Path, observation_id: str, text: str) -> str:  # 新增代码+BrowserObservationStage4: 把完整页面正文写入产物；若没有这行代码，超长页面会只剩截断摘要。
    artifact_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+BrowserObservationStage4: 确保产物目录存在；若没有这行代码，首次写文件会失败。
    path = artifact_dir / f"{observation_id}-visible-text.txt"  # 新增代码+BrowserObservationStage4: 生成稳定文本产物名；若没有这行代码，长文本证据路径不可预测。
    atomic_write_text(path, text)  # 新增代码+BrowserObservationStage4: 原子写完整正文；若没有这行代码，崩溃时可能留下半截证据。
    return str(path)  # 新增代码+BrowserObservationStage4: 返回路径文本便于 JSON 落盘；若没有这行代码，observation 不能关联产物。


def build_browser_observation(run_id: str, stage_id: str, action_id: str, page_state: dict[str, Any], max_text_chars: int = 4000, artifact_dir: str | Path | None = None) -> BrowserObservation:  # 新增代码+BrowserObservationStage4: 构建标准页面观察对象；若没有这行代码，snapshot/screenshot/console/network 会继续分散。
    observation_id = f"browser_observation_{secrets.token_hex(8)}"  # 新增代码+BrowserObservationStage4: 生成观察 id；若没有这行代码，多次观察可能互相覆盖。
    full_visible_text = _text(page_state.get("visible_text") or page_state.get("body_text"))  # 新增代码+BrowserObservationStage4: 读取完整可见文本；若没有这行代码，页面正文不会进入观察。
    artifact_paths: list[str] = []  # 新增代码+BrowserObservationStage4: 准备保存观察产物路径；若没有这行代码，长文本文件无法关联。
    safe_max_chars = max(1, int(max_text_chars))  # 新增代码+BrowserObservationStage4: 限制截断长度至少为 1；若没有这行代码，0 或负数会导致空摘要。
    visible_text = full_visible_text[:safe_max_chars]  # 新增代码+BrowserObservationStage4: 把模型上下文正文限制长度；若没有这行代码，大页面会撑爆下一轮上下文。
    if len(full_visible_text) > safe_max_chars and artifact_dir is not None:  # 新增代码+BrowserObservationStage4: 超长正文且有目录时写产物；若没有这行代码，完整正文会丢失。
        artifact_paths.append(_write_long_text_artifact(Path(artifact_dir), observation_id, full_visible_text))  # 新增代码+BrowserObservationStage4: 保存完整正文产物；若没有这行代码，verifier 无法读取长页面证据。
    raw_elements = page_state.get("elements", [])  # 新增代码+BrowserObservationStage4: 读取页面元素候选；若没有这行代码，定位引擎没有输入。
    elements = [normalize_browser_element(item, index + 1) for index, item in enumerate(raw_elements) if isinstance(item, dict)] if isinstance(raw_elements, list) else []  # 新增代码+BrowserObservationStage4: 规范化列表元素并跳过坏项；若没有这行代码，坏 DOM 数据会拖垮观察。
    observation = BrowserObservation(  # 新增代码+BrowserObservationStage4: 创建协议化 observation；若没有这行代码，store 无法保存证据。
        observation_id=observation_id,  # 新增代码+BrowserObservationStage4: 写入观察 id；若没有这行代码，证据无法被引用。
        run_id=str(run_id),  # 新增代码+BrowserObservationStage4: 写入 run id；若没有这行代码，证据无法归属浏览器任务。
        stage_id=str(stage_id),  # 新增代码+BrowserObservationStage4: 写入阶段 id；若没有这行代码，阶段验收找不到页面证据。
        action_id=str(action_id),  # 新增代码+BrowserObservationStage4: 写入动作 id；若没有这行代码，工具结果和观察会断链。
        url=_text(page_state.get("url")),  # 新增代码+BrowserObservationStage4: 写入 URL；若没有这行代码，验收无法证明访问目标页面。
        title=_text(page_state.get("title")),  # 新增代码+BrowserObservationStage4: 写入标题；若没有这行代码，页面摘要缺少人类可读信息。
        visible_text=visible_text,  # 新增代码+BrowserObservationStage4: 写入截断后的可见文本；若没有这行代码，下一轮模型看不到页面内容。
        screenshot_path=_text(page_state.get("screenshot_path")),  # 新增代码+BrowserObservationStage4: 写入截图路径；若没有这行代码，肉眼证据无法关联。
        console_summary=_summarize_console(page_state.get("console", page_state.get("console_logs", []))),  # 新增代码+BrowserObservationStage4: 写入脱敏 console 摘要；若没有这行代码，脚本错误不可审计。
        network_summary=_summarize_network(page_state.get("network", page_state.get("network_logs", []))),  # 新增代码+BrowserObservationStage4: 写入脱敏 network 摘要；若没有这行代码，请求失败不可审计。
        elements=elements,  # 新增代码+BrowserObservationStage4: 写入结构化元素；若没有这行代码，定位引擎只能重新抓页面。
        artifact_paths=artifact_paths,  # 新增代码+BrowserObservationStage4: 写入长文本产物路径；若没有这行代码，完整页面正文会和 observation 断链。
    )  # 新增代码+BrowserObservationStage4: 结束 observation 构造；若没有这行代码，Python 调用语法无法闭合。
    return observation  # 新增代码+BrowserObservationStage4: 返回可落盘证据对象；若没有这行代码，调用方拿不到结果。
