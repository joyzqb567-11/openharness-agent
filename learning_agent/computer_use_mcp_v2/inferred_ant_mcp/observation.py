"""Computer Use MCP v2 观察工具。"""  # 新增代码+ComputerUseMcpV2：说明本文件管理 observe/screenshot；如果没有这行代码，观察逻辑会混入动作执行。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型引用可能提前求值。

import base64  # 新增代码+ClaudeCodeContentParity：把截图字节编码为 ClaudeCode content block 可携带的 base64；如果没有这行代码，图片只能停留在文件路径。
from pathlib import Path  # 新增代码+ClaudeCodeContentParity：稳定处理 artifact_path 文件；如果没有这行代码，存在性检查和后缀 MIME 判断会变脆弱。
from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，观察结果边界不清楚。

from ..windows_runtime.coordinates import claudecode_display_state_from_payload  # 新增代码+ClaudeCodeDisplayParity：复用 Windows 坐标层的 display state 抽取器；如果没有这行代码，observation 会重复理解显示器和截图尺寸字段。
from ..windows_runtime.image_messages import MAX_COMPUTER_USE_MODEL_IMAGE_BYTES, build_computer_use_model_image_payload, extract_computer_use_image_specs_from_tool_output  # 新增代码+ClaudeCodeContentParity：复用成熟图片读取/转码/解析逻辑；如果没有这行代码，观察结果会重新造一套容易不一致的图片处理。
from .errors import error_result  # 新增代码+ClaudeCodeZoom: 导入统一失败结果用于 zoom 无 host 场景；如果没有这一行，zoom 缺宿主时只能伪装成普通 captured=false。
from .result_blocks import image_content_block, success_result, text_content_block  # 修改代码+ClaudeCodeContentParity：导入成功结果和 content block 构造器；如果没有这行代码，观察工具无法返回 ClaudeCode-compatible 图片块。
from .types import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2：导入上下文；如果没有这行代码，host 观察能力无法注入。


def _append_image_specs_from_entries(specs: list[dict[str, str]], entries: Any) -> None:  # 新增代码+ClaudeCodeContentParity：函数段开始，把 host 结构化图片列表追加到 specs；如果没有这段函数，不同 host 字段会反复写解析循环。
    if not isinstance(entries, list):  # 新增代码+ClaudeCodeContentParity：只接受列表形图片结果；如果没有这行代码，字符串或字典会被误当作可迭代图片集合。
        return  # 新增代码+ClaudeCodeContentParity：非列表时直接退出；如果没有这行代码，异常字段类型可能让观察结果崩溃。
    for entry in entries:  # 新增代码+ClaudeCodeContentParity：逐个读取图片条目；如果没有这行代码，多张截图无法进入 content blocks。
        if not isinstance(entry, dict):  # 新增代码+ClaudeCodeContentParity：只处理字典条目；如果没有这行代码，坏条目会触发属性错误。
            continue  # 新增代码+ClaudeCodeContentParity：跳过坏条目并继续后续图片；如果没有这行代码，一项坏数据会阻断全部图片。
        artifact_path = str(entry.get("artifact_path") or entry.get("path") or "")  # 新增代码+ClaudeCodeContentParity：兼容 artifact_path/path 两种命名；如果没有这行代码，不同后端产出的路径可能被漏掉。
        if not artifact_path:  # 新增代码+ClaudeCodeContentParity：没有路径就无法读取图片；如果没有这行代码，空路径会进入文件系统检查。
            continue  # 新增代码+ClaudeCodeContentParity：跳过缺路径图片；如果没有这行代码，后面会浪费一次无效读图。
        specs.append({"artifact_path": artifact_path, "mime_type": str(entry.get("mime_type") or entry.get("media_type") or "")})  # 新增代码+ClaudeCodeContentParity：保存图片路径和 MIME；如果没有这行代码，后续无法把截图转为 base64 图片块。
# 新增代码+ClaudeCodeContentParity：函数段结束，_append_image_specs_from_entries 到此结束；如果没有这个边界说明，用户不容易看出图片条目解析范围。


def _collect_image_specs_from_payload(payload: dict[str, Any]) -> list[dict[str, str]]:  # 新增代码+ClaudeCodeContentParity：函数段开始，从 host payload 收集所有可读截图引用；如果没有这段函数，screenshot/zoom 的图片只能藏在 payload 文本里。
    specs: list[dict[str, str]] = []  # 新增代码+ClaudeCodeContentParity：准备保存图片引用；如果没有这行代码，多来源图片无法合并。
    _append_image_specs_from_entries(specs, payload.get("image_results"))  # 新增代码+ClaudeCodeContentParity：读取通用 image_results 字段；如果没有这行代码，普通 observe 截图不会生成图片 content。
    _append_image_specs_from_entries(specs, payload.get("zoom_image_results"))  # 新增代码+ClaudeCodeContentParity：读取 zoom 专用图片字段；如果没有这行代码，局部放大截图可能不会进入模型。
    legacy_text = payload.get("legacy_text", "")  # 新增代码+ClaudeCodeContentParity：读取旧 adapter 的原始文本输出；如果没有这行代码，旧格式图片行无法被解析。
    if isinstance(legacy_text, str) and legacy_text:  # 新增代码+ClaudeCodeContentParity：只解析非空文本；如果没有这行代码，空文本会浪费一次解析。
        specs.extend(extract_computer_use_image_specs_from_tool_output(legacy_text))  # 新增代码+ClaudeCodeContentParity：复用旧图片行解析器；如果没有这行代码，legacy_text 中的 artifact_path 无法转成 content block。
    legacy_result = payload.get("legacy_result", {})  # 新增代码+ClaudeCodeContentParity：读取 agent-side adapter 深层结果；如果没有这行代码，嵌套 payload 的图片引用会被漏掉。
    if isinstance(legacy_result, dict):  # 新增代码+ClaudeCodeContentParity：确认深层结果是字典；如果没有这行代码，异常类型会触发属性错误。
        legacy_payload = legacy_result.get("payload", {})  # 新增代码+ClaudeCodeContentParity：读取深层 payload；如果没有这行代码，adapter 包装内的 image_results 无法递归查找。
        if isinstance(legacy_payload, dict) and legacy_payload:  # 修改代码+ClaudeCodeContentParity：只递归非空深层 payload；如果没有这行代码，默认空字典会造成无限递归。
            specs.extend(_collect_image_specs_from_payload(legacy_payload))  # 新增代码+ClaudeCodeContentParity：递归收集深层图片引用；如果没有这行代码，v2 包装下的截图路径无法进入 content。
        legacy_result_text = legacy_result.get("text", "")  # 新增代码+ClaudeCodeContentParity：读取深层 text 文本；如果没有这行代码，旧 observe 输出里的图片区仍可能漏掉。
        if isinstance(legacy_result_text, str) and legacy_result_text:  # 新增代码+ClaudeCodeContentParity：只解析非空深层文本；如果没有这行代码，空字段会浪费解析。
            specs.extend(extract_computer_use_image_specs_from_tool_output(legacy_result_text))  # 新增代码+ClaudeCodeContentParity：解析深层文本里的 artifact_path；如果没有这行代码，嵌套 legacy 结果不会有图片块。
    deduped_specs: list[dict[str, str]] = []  # 新增代码+ClaudeCodeContentParity：准备保存去重后的图片引用；如果没有这行代码，同一截图可能重复进入模型上下文。
    seen_paths: set[str] = set()  # 新增代码+ClaudeCodeContentParity：记录已经添加的路径；如果没有这行代码，去重无法工作。
    for spec in specs:  # 新增代码+ClaudeCodeContentParity：遍历所有候选图片引用；如果没有这行代码，去重列表无法生成。
        artifact_path = str(spec.get("artifact_path", "") or "")  # 新增代码+ClaudeCodeContentParity：取出候选路径；如果没有这行代码，空路径无法被过滤。
        if not artifact_path or artifact_path in seen_paths:  # 新增代码+ClaudeCodeContentParity：过滤空路径和重复路径；如果没有这行代码，图片 content 会出现重复或无效条目。
            continue  # 新增代码+ClaudeCodeContentParity：跳过不合格候选；如果没有这行代码，后续会加入坏数据。
        seen_paths.add(artifact_path)  # 新增代码+ClaudeCodeContentParity：记录已使用路径；如果没有这行代码，后续重复路径不会被识别。
        deduped_specs.append(spec)  # 新增代码+ClaudeCodeContentParity：保存去重后的图片引用；如果没有这行代码，后续无法读取图片。
    return deduped_specs  # 新增代码+ClaudeCodeContentParity：返回稳定图片引用列表；如果没有这行代码，调用方拿不到任何收集结果。
# 新增代码+ClaudeCodeContentParity：函数段结束，_collect_image_specs_from_payload 到此结束；如果没有这个边界说明，用户不容易看出图片引用收集范围。


def _content_and_debug_from_observation(tool_name: str, payload: dict[str, Any], record_observation: Any) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:  # 新增代码+ClaudeCodeContentParity：函数段开始，把观察 payload 转成 ClaudeCode content/debug；如果没有这段函数，screenshot/zoom 无法协议级返回图片。
    content_blocks: list[dict[str, Any]] = [text_content_block(f"Computer Use {tool_name} captured desktop state.")]  # 新增代码+ClaudeCodeContentParity：先生成说明文本块；如果没有这行代码，图片块缺少与工具结果的语义连接。
    debug: dict[str, Any] = {}  # 新增代码+ClaudeCodeContentParity：准备调试证据字典；如果没有这行代码，artifact_path 无处保存。
    image_count = 0  # 新增代码+ClaudeCodeContentParity：统计成功加入 content 的图片数量；如果没有这行代码，debug 无法说明实际返回了几张图片。
    recorder = record_observation if callable(record_observation) else None  # 新增代码+ClaudeCodeContentParity：只在记录器可调用时传给图片读取层；如果没有这行代码，None 或坏对象会导致读图诊断崩溃。
    for spec in _collect_image_specs_from_payload(payload):  # 新增代码+ClaudeCodeContentParity：逐张读取 payload 里的截图引用；如果没有这行代码，content 中不会有图片块。
        artifact_path = Path(str(spec.get("artifact_path", "") or ""))  # 新增代码+ClaudeCodeContentParity：把路径文本转成 Path；如果没有这行代码，图片读取 helper 无法稳定处理后缀。
        image_payload = build_computer_use_model_image_payload(artifact_path, spec.get("mime_type"), MAX_COMPUTER_USE_MODEL_IMAGE_BYTES, record_observation=recorder)  # 新增代码+ClaudeCodeContentParity：读取图片并复用 BMP 转 PNG/大小限制；如果没有这行代码，Windows 截图可能以模型不支持的格式返回。
        if image_payload is None:  # 新增代码+ClaudeCodeContentParity：处理不存在、过大、空图或转码失败；如果没有这行代码，后续解包 None 会崩溃。
            continue  # 新增代码+ClaudeCodeContentParity：跳过当前不可用图片并继续下一张；如果没有这行代码，一张坏图会阻断全部观察结果。
        image_bytes, mime_type = image_payload  # 新增代码+ClaudeCodeContentParity：取出可发送的图片字节和 MIME；如果没有这行代码，base64 编码不知道处理哪份数据。
        encoded_image = base64.b64encode(image_bytes).decode("ascii")  # 新增代码+ClaudeCodeContentParity：把图片字节转成 ASCII base64；如果没有这行代码，JSON content 不能携带二进制截图。
        content_blocks.append(image_content_block(encoded_image, mime_type))  # 新增代码+ClaudeCodeContentParity：追加 ClaudeCode-compatible 图片块；如果没有这行代码，模型仍然看不到截图像素。
        image_count += 1  # 新增代码+ClaudeCodeContentParity：累计成功图片数量；如果没有这行代码，debug 统计会不准确。
        debug.setdefault("artifact_path", str(artifact_path))  # 新增代码+ClaudeCodeContentParity：保存第一张图片原始路径用于审计；如果没有这行代码，排查时看不到截图证据落在哪里。
        debug.setdefault("mime_type", mime_type)  # 新增代码+ClaudeCodeContentParity：保存第一张图片 MIME；如果没有这行代码，排查时不知道图片是否被转码。
    if image_count <= 0:  # 新增代码+ClaudeCodeContentParity：没有成功图片时保持旧 JSON 回退；如果没有这行代码，无图观察会把 payload 隐藏成一句文本。
        return None, None  # 新增代码+ClaudeCodeContentParity：返回 None 表示调用方不要启用显式 content；如果没有这行代码，兼容回退会失效。
    debug["image_count"] = image_count  # 新增代码+ClaudeCodeContentParity：记录成功输出图片数量；如果没有这行代码，调用方难以判断 content 是否完整。
    return content_blocks, debug  # 新增代码+ClaudeCodeContentParity：返回可直接放入 success_result 的 content/debug；如果没有这行代码，观察结果无法携带图片。
# 新增代码+ClaudeCodeContentParity：函数段结束，_content_and_debug_from_observation 到此结束；如果没有这个边界说明，用户不容易看出 content/debug 构造范围。


def _context_display_state_payload(context: ComputerUseMcpV2Context) -> dict[str, Any]:  # 新增代码+ClaudeCodeDisplayParity：函数段开始，把 context 内部 snake_case display 状态转成 ClaudeCode camelCase；如果没有这段函数，多个返回点可能字段名不一致。
    return {"selectedDisplayId": context.selected_display_id, "displayPinnedByModel": bool(context.display_pinned_by_model), "displayResolvedForApps": [dict(item) for item in context.display_resolved_for_apps], "lastScreenshotDims": dict(context.last_screenshot_dims)}  # 新增代码+ClaudeCodeDisplayParity：返回模型可见 displayState；如果没有这行代码，模型端无法稳定读取四个 ClaudeCode 字段。
# 新增代码+ClaudeCodeDisplayParity：函数段结束，_context_display_state_payload 到此结束；如果没有这个边界说明，用户不容易看出 camelCase 转换范围。


def _merge_display_resolved_for_apps(context: ComputerUseMcpV2Context, resolved_for_apps: list[dict[str, Any]]) -> None:  # 新增代码+ClaudeCodeDisplayParity：函数段开始，把本次解析到的 app-display 记录合并进上下文；如果没有这段函数，多次截图会丢失已解析应用。
    seen = {(str(item.get("appId", "")), str(item.get("displayId", "")), str(item.get("windowId", ""))) for item in context.display_resolved_for_apps if isinstance(item, dict)}  # 新增代码+ClaudeCodeDisplayParity：读取已有记录的去重 key；如果没有这行代码，同一窗口可能重复进入状态。
    for item in resolved_for_apps:  # 新增代码+ClaudeCodeDisplayParity：遍历本次候选记录；如果没有这行代码，新解析结果无法合并。
        if not isinstance(item, dict):  # 新增代码+ClaudeCodeDisplayParity：只接受字典记录；如果没有这行代码，坏 payload 会污染上下文。
            continue  # 新增代码+ClaudeCodeDisplayParity：跳过非字典记录；如果没有这行代码，后续 get 会异常。
        key = (str(item.get("appId", "")), str(item.get("displayId", "")), str(item.get("windowId", "")))  # 新增代码+ClaudeCodeDisplayParity：构造 app/display/window 去重 key；如果没有这行代码，无法判断是否已记录。
        if key in seen or not key[0] or not key[1]:  # 新增代码+ClaudeCodeDisplayParity：跳过重复或缺 app/display 的记录；如果没有这行代码，displayResolvedForApps 会含噪声。
            continue  # 新增代码+ClaudeCodeDisplayParity：继续下一个候选；如果没有这行代码，无效项会进入列表。
        seen.add(key)  # 新增代码+ClaudeCodeDisplayParity：标记本记录已加入；如果没有这行代码，同批重复不会被拦截。
        context.display_resolved_for_apps.append(dict(item))  # 新增代码+ClaudeCodeDisplayParity：保存解析记录副本；如果没有这行代码，后续工具看不到 app-display 历史。
# 新增代码+ClaudeCodeDisplayParity：函数段结束，_merge_display_resolved_for_apps 到此结束；如果没有这个边界说明，用户不容易看出合并范围。


def _update_display_state_from_observation(context: ComputerUseMcpV2Context, arguments: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeDisplayParity：函数段开始，根据本次观察更新 ClaudeCode display state；如果没有这段函数，selectedDisplayId 和 lastScreenshotDims 不会跨工具保存。
    extracted_state = claudecode_display_state_from_payload(payload)  # 新增代码+ClaudeCodeDisplayParity：从 Windows payload 抽取显示器状态；如果没有这行代码，观察层无法理解 host 返回的多种字段形状。
    requested_display = str(arguments.get("selectedDisplayId", arguments.get("selected_display_id", arguments.get("display_id", ""))) or "")  # 新增代码+ClaudeCodeDisplayParity：读取模型显式请求的显示器；如果没有这行代码，模型指定屏幕时 context 不会被 pin。
    if "displayPinnedByModel" in arguments:  # 新增代码+ClaudeCodeDisplayParity：优先尊重 ClaudeCode camelCase pin 字段；如果没有这行代码，模型显式取消 pin 会被忽略。
        context.display_pinned_by_model = bool(arguments.get("displayPinnedByModel"))  # 新增代码+ClaudeCodeDisplayParity：写入显式 pin 值；如果没有这行代码，cleanup 前状态不准确。
    elif "display_pinned_by_model" in arguments:  # 新增代码+ClaudeCodeDisplayParity：兼容内部 snake_case pin 字段；如果没有这行代码，测试和旧调用无法控制 pin。
        context.display_pinned_by_model = bool(arguments.get("display_pinned_by_model"))  # 新增代码+ClaudeCodeDisplayParity：写入兼容 pin 值；如果没有这行代码，snake_case 输入会被忽略。
    elif requested_display:  # 新增代码+ClaudeCodeDisplayParity：没有显式 pin 但模型选择 display 时按临时 pin 处理；如果没有这行代码，cleanup 无法知道这个 display 是模型临时固定的。
        context.display_pinned_by_model = True  # 新增代码+ClaudeCodeDisplayParity：设置临时 pin；如果没有这行代码，ClaudeCode 的 displayPinnedByModel 语义不完整。
    extracted_display = str(extracted_state.get("selectedDisplayId", "") or "")  # 新增代码+ClaudeCodeDisplayParity：读取后端解析到的显示器；如果没有这行代码，自动 display resolve 无法回填。
    context.selected_display_id = requested_display or extracted_display or context.selected_display_id  # 新增代码+ClaudeCodeDisplayParity：优先模型选择，其次后端解析，最后保留旧值；如果没有这行代码，多步任务会丢失当前屏幕。
    extracted_dims = extracted_state.get("lastScreenshotDims") if isinstance(extracted_state.get("lastScreenshotDims"), dict) else {}  # 新增代码+ClaudeCodeDisplayParity：读取截图宽高；如果没有这行代码，宽高字段可能以坏类型写入 context。
    if extracted_dims:  # 新增代码+ClaudeCodeDisplayParity：只有拿到有效宽高才更新；如果没有这行代码，空观察可能清掉上一次有效尺寸。
        context.last_screenshot_dims = {"width": int(extracted_dims.get("width", 0)), "height": int(extracted_dims.get("height", 0))}  # 新增代码+ClaudeCodeDisplayParity：保存最近截图尺寸；如果没有这行代码，cleanup 后也无法保留 lastScreenshotDims。
    resolved_for_apps = extracted_state.get("displayResolvedForApps") if isinstance(extracted_state.get("displayResolvedForApps"), list) else []  # 新增代码+ClaudeCodeDisplayParity：读取 app-display 解析列表；如果没有这行代码，窗口落屏信息无法合并。
    _merge_display_resolved_for_apps(context, resolved_for_apps)  # 新增代码+ClaudeCodeDisplayParity：合并解析记录；如果没有这行代码，displayResolvedForApps 不会跨观察累积。
    payload["displayState"] = _context_display_state_payload(context)  # 新增代码+ClaudeCodeDisplayParity：把 ClaudeCode camelCase 状态写回本次 payload；如果没有这行代码，模型结果里看不到 display state。
    return payload["displayState"]  # 新增代码+ClaudeCodeDisplayParity：返回本次状态供测试或未来调用复用；如果没有这行代码，调用方无法直接断言更新结果。
# 新增代码+ClaudeCodeDisplayParity：函数段结束，_update_display_state_from_observation 到此结束；如果没有这个边界说明，用户不容易看出 display state 写入范围。


def observe(context: ComputerUseMcpV2Context, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，执行 observe/screenshot；如果没有这段函数，模型无法获取桌面状态。
    host_method_name = "zoom" if tool_name == "zoom" else "observe"  # 新增代码+ClaudeCodeZoom: zoom 仍是观察语义但必须调用宿主 zoom 能力；如果没有这一行，局部放大会退化成普通 observe。
    host_method = getattr(context.host, host_method_name, None) if context.host is not None else None  # 修改代码+ClaudeCodeZoom: 按工具选择 host.observe 或 host.zoom；如果没有这行代码，zoom 无法保留独立宿主接口。
    if tool_name == "zoom" and not callable(host_method):  # 新增代码+ClaudeCodeZoom: zoom 缺少宿主实现时给明确失败；如果没有这一行，局部放大会被当作普通无截图观察成功。
        result = error_result("zoom", "zoom_unavailable_without_host", error_class="host_unavailable")  # 新增代码+ClaudeCodeZoom: 构造 host 不可用错误；如果没有这一行，模型无法判断需要 Windows host 才能缩放。
        result["payload"] = {"requires_host": True, "desktop_action_performed": False}  # 新增代码+ClaudeCodeZoom: 明确 zoom 没有执行桌面副作用；如果没有这一行，验收可能误以为发生了动作。
        return result  # 新增代码+ClaudeCodeZoom: 返回 zoom 无 host 错误；如果没有这一行，函数会继续走普通 observe 兜底。
    raw_payload = host_method(arguments) if callable(host_method) else {"captured": False, "reason": "no_host_observer_bound"}  # 修改代码+ClaudeCodeZoom：先保存 host 原始观察或 zoom 结果；如果没有这一行，非字典结果会再次被 dict(...) 误转并崩溃。
    payload = dict(raw_payload) if isinstance(raw_payload, dict) else {"captured": False, "reason": "host_observer_returned_non_dict", "host_result_type": type(raw_payload).__name__}  # 修改代码+ComputerUseMcpV2HostAdapter：只接受字典结果并给非字典结果稳定摘要；如果没有这一行，旧 controller 对象会让 observe 输出非 JSON 错误。
    _update_display_state_from_observation(context, arguments, payload)  # 新增代码+ClaudeCodeDisplayParity：先更新并写回 displayState；如果没有这行代码，record_observation 和最终结果都会缺少 ClaudeCode display 字段。
    if callable(context.record_observation):  # 新增代码+ComputerUseMcpV2：检查是否存在 observation 回调；如果没有这行代码，None 回调会导致异常。
        context.record_observation("computer_use_mcp_v2_observe", payload)  # 新增代码+ComputerUseMcpV2：把观察证据写回 agent；如果没有这行代码，主循环看不到观察结果。
    content, debug = _content_and_debug_from_observation(tool_name, payload, context.record_observation)  # 新增代码+ClaudeCodeContentParity：把截图 payload 转成 ClaudeCode content/debug；如果没有这行代码，screenshot/zoom 仍只能返回 JSON 文本。
    return success_result(tool_name, payload, legacy_adapter_used=bool(payload.get("legacy_adapter_used", False)), content=content, debug=debug)  # 修改代码+ClaudeCodeContentParity：返回观察 payload 并在有图时携带图片 content；如果没有这一行，协议层图片输出无法对齐 ClaudeCode。
# 新增代码+ComputerUseMcpV2：函数段结束，observe 到此结束；如果没有这个边界说明，用户不容易看出观察范围。
