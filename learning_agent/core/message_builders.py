"""把内部消息对象转换成模型 API 使用的 dict。"""  # 新增代码+AgentPySplitPhase8: 说明本模块负责消息格式转换；若没有这行代码，用户不容易区分 messages.py 的数据结构和这里的 API 字典构造。
from __future__ import annotations  # 新增代码+AgentPySplitPhase8: 延迟解析类型注解；若没有这行代码，类型引用在部分导入顺序下可能提前求值。

import json  # 新增代码+AgentPySplitPhase8: 用于把工具参数转成 JSON 字符串；若没有这行代码，OpenAI tool_calls 的 arguments 字段无法按协议生成。
from typing import Any, Callable  # 新增代码+AgentPySplitPhase8: Any 表示通用消息字典值，Callable 表示 Computer Use 图片消息回调；若没有这行代码，函数签名边界不清楚。

try:  # 新增代码+AgentPySplitPhase8: 优先按正式包路径导入消息数据结构；若没有这行代码，包运行模式下无法复用 ModelMessage 和 ToolCall。
    from learning_agent.core.messages import ModelMessage, ToolCall  # 新增代码+AgentPySplitPhase8: 导入内部模型消息和工具调用对象；若没有这行代码，转换函数无法表达输入类型。
except ModuleNotFoundError as error:  # 新增代码+AgentPySplitPhase8: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因包路径不同失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.messages"}:  # 新增代码+AgentPySplitPhase8: 只允许目标包路径缺失时 fallback；若没有这行代码，messages 内部真实 bug 会被误吞。
        raise  # 新增代码+AgentPySplitPhase8: 重新抛出非路径问题；若没有这行代码，真实导入错误会被伪装成脚本模式问题。
    from core.messages import ModelMessage, ToolCall  # 新增代码+AgentPySplitPhase8: 脚本模式下从同目录 core 包导入消息结构；若没有这行代码，bat 入口无法复用消息构造模块。


def assistant_message_to_dict(model_message: ModelMessage) -> dict[str, Any]:  # 新增代码+AgentPySplitPhase8: 函数段开始，把内部 ModelMessage 转成 OpenAI assistant 消息字典；若没有这段函数，agent.py 仍要保存消息协议细节。
    message: dict[str, Any] = {"role": "assistant", "content": model_message.text or None}  # 新增代码+AgentPySplitPhase8: 先写入 assistant 角色和文本内容；若没有这行代码，下一轮模型看不到上一轮 assistant 文本。
    if model_message.tool_calls:  # 新增代码+AgentPySplitPhase8: 如果模型请求了工具；若没有这行代码，工具调用消息会被当成普通文本消息。
        message["tool_calls"] = [tool_call_to_openai_dict(call) for call in model_message.tool_calls]  # 新增代码+AgentPySplitPhase8: 把每个 ToolCall 转成 OpenAI tool_calls 格式；若没有这行代码，下一轮模型无法按协议追踪工具调用。
    if model_message.native_output_items:  # 新增代码+OAuthNativeFunctionCallCarry: 如果模型返回了 Responses 原生 output items；如果没有这一行，下一轮无法判断是否应回填原生 function_call_output。
        message["_native_output_items"] = list(model_message.native_output_items)  # 新增代码+OAuthNativeFunctionCallCarry: 把原生 items 作为内部字段保存在消息历史里；如果没有这一行，function_call 与 call_id 会在工具执行后丢失。
    return message  # 新增代码+AgentPySplitPhase8: 返回可直接放入 messages 的 assistant 消息；若没有这行代码，调用方拿不到转换结果。
# 新增代码+AgentPySplitPhase8: 函数段结束，assistant_message_to_dict 到此结束；若没有这行注释，用户不容易看出 assistant 消息构造边界。


def tool_call_to_openai_dict(tool_call: ToolCall) -> dict[str, Any]:  # 新增代码+AgentPySplitPhase8: 函数段开始，把 ToolCall 转成 OpenAI tool_call 字典；若没有这段函数，工具调用协议字段会散落在 agent.py。
    return {  # 新增代码+AgentPySplitPhase8: 返回工具调用字典；若没有这行代码，函数没有输出结构。
        "id": tool_call.call_id,  # 新增代码+AgentPySplitPhase8: 保存工具调用 id；若没有这行代码，tool result 无法和这次调用配对。
        "type": "function",  # 新增代码+AgentPySplitPhase8: OpenAI 工具调用类型固定为 function；若没有这行代码，模型 API 可能不识别这条工具调用。
        "function": {  # 新增代码+AgentPySplitPhase8: function 字段保存工具名和参数；若没有这行代码，工具调用结构不符合模型协议。
            "name": tool_call.name,  # 新增代码+AgentPySplitPhase8: 保存工具名称；若没有这行代码，模型 API 不知道调用的是哪个工具。
            "arguments": json.dumps(tool_call.arguments, ensure_ascii=False),  # 新增代码+AgentPySplitPhase8: 把参数转成 JSON 字符串且保留中文；若没有这行代码，arguments 会是 dict 而不是模型协议要求的字符串。
        },  # 新增代码+AgentPySplitPhase8: function 字段结束；若没有这行代码，Python 字典语法不完整。
    }  # 新增代码+AgentPySplitPhase8: 工具调用字典结束；若没有这行代码，Python 字典语法不完整。
# 新增代码+AgentPySplitPhase8: 函数段结束，tool_call_to_openai_dict 到此结束；若没有这行注释，用户不容易看出工具调用字典构造边界。


def tool_result_to_dict(tool_call: ToolCall, output: str) -> dict[str, Any]:  # 新增代码+AgentPySplitPhase8: 函数段开始，把工具执行结果转成 OpenAI tool 消息字典；若没有这段函数，工具结果回填协议会留在 agent.py。
    return {  # 新增代码+AgentPySplitPhase8: 返回 tool 消息字典；若没有这行代码，函数没有输出结构。
        "role": "tool",  # 新增代码+AgentPySplitPhase8: role=tool 表示这是工具结果消息；若没有这行代码，下一轮模型会把结果误当成普通用户/助手消息。
        "tool_call_id": tool_call.call_id,  # 新增代码+AgentPySplitPhase8: 对应前面的工具调用 id；若没有这行代码，模型 API 无法配对调用和结果。
        "name": tool_call.name,  # 新增代码+AgentPySplitPhase8: 保存工具名称方便调试；若没有这行代码，日志和紧急排查不容易看出结果来源。
        "content": output,  # 新增代码+AgentPySplitPhase8: 保存工具结果文本；若没有这行代码，模型下一轮看不到工具执行输出。
    }  # 新增代码+AgentPySplitPhase8: tool 消息字典结束；若没有这行代码，Python 字典语法不完整。
# 新增代码+AgentPySplitPhase8: 函数段结束，tool_result_to_dict 到此结束；若没有这行注释，用户不容易看出工具结果字典构造边界。


def tool_result_messages_to_dicts(tool_call: ToolCall, output: str, image_message_builder: Callable[[ToolCall, str], dict[str, Any] | None], image_source_output: str | None = None) -> list[dict[str, Any]]:  # 修改代码+ComputerUseRawImageReinjection：函数段开始，把工具文本结果和可选图片消息组合成 messages，并允许图片从原始输出提取；若没有这段函数，长 Computer Use 结果被压缩后截图像素会丢失。
    result_messages = [tool_result_to_dict(tool_call, output)]  # 新增代码+AgentPySplitPhase8: 先保留标准 tool 文本结果以维持 tool_call_id 配对；若没有这行代码，模型工具协议会断链。
    image_lookup_output = image_source_output if image_source_output is not None else output  # 新增代码+ComputerUseRawImageReinjection：图片提取优先使用未压缩的原始工具输出；如果没有这行代码，长 observe 输出落盘后只剩摘要，模型下一轮看不到真实截图。
    image_message = image_message_builder(tool_call, image_lookup_output)  # 修改代码+ComputerUseRawImageReinjection: 通过回调尝试构造 Computer Use 图片消息；若没有这行代码，截图像素不会进入下一轮模型输入。
    if image_message is not None:  # 新增代码+AgentPySplitPhase8: 只有真实生成图片消息才追加；若没有这行代码，普通工具结果会出现空图片噪音。
        result_messages.append(image_message)  # 新增代码+AgentPySplitPhase8: 把图片消息追加到标准 tool 结果后面；若没有这行代码，模型仍只能看到文字结果。
    return result_messages  # 新增代码+AgentPySplitPhase8: 返回可直接 extend 到 messages 的消息列表；若没有这行代码，主循环拿不到组合结果。
# 新增代码+AgentPySplitPhase8: 函数段结束，tool_result_messages_to_dicts 到此结束；若没有这行注释，用户不容易看出工具结果回填边界。


def native_tool_result_message_to_responses_input_item(tool_call: ToolCall, output: str) -> dict[str, Any]:  # 新增代码+OAuthNativeToolResultMessages: 函数段开始，把内部工具结果转成 Responses function_call_output；如果没有这段函数，原生工具结果回填没有公共入口，本段到 return 字典结束。
    return {  # 新增代码+OAuthNativeToolResultMessages: 返回 Responses 原生工具结果 item；如果没有这一行，函数没有输出结构。
        "type": "function_call_output",  # 新增代码+OAuthNativeToolResultMessages: 标记这是原生函数调用结果；如果没有这一行，Responses 后端无法识别工具返回。
        "call_id": tool_call.call_id,  # 新增代码+OAuthNativeToolResultMessages: 保留模型给出的 call_id；如果没有这一行，下一轮模型无法把结果配回对应工具调用。
        "output": output,  # 新增代码+OAuthNativeToolResultMessages: 写入工具文本结果；如果没有这一行，模型看不到工具执行输出。
    }  # 新增代码+OAuthNativeToolResultMessages: function_call_output 字典结束；如果没有这一行，Python 字典语法不完整。
# 新增代码+OAuthNativeToolResultMessages: 函数段结束，native_tool_result_message_to_responses_input_item 到此结束；如果没有这个边界说明，用户不容易看出单条工具结果格式。


def native_tool_result_messages_to_responses_input_items(tool_call: ToolCall, output: str, image_message_builder: Callable[[ToolCall, str], dict[str, Any] | None], image_source_output: str | None = None) -> list[dict[str, Any]]:  # 新增代码+OAuthNativeToolResultMessages: 函数段开始，把工具文本和可选截图转成 Responses input items；如果没有这段函数，Computer Use native 回填无法复用现有图片生成器，本段到 return 列表结束。
    input_items = [native_tool_result_message_to_responses_input_item(tool_call, output)]  # 新增代码+OAuthNativeToolResultMessages: 先加入 function_call_output 保证 call_id 配对；如果没有这一行，工具结果链路会断开。
    image_lookup_output = image_source_output if image_source_output is not None else output  # 新增代码+OAuthNativeToolResultMessages: 图片提取优先使用原始工具输出；如果没有这一行，长 observe 摘要可能没有截图 data URL。
    image_message = image_message_builder(tool_call, image_lookup_output)  # 新增代码+OAuthNativeToolResultMessages: 复用现有 Computer Use 图片消息生成器；如果没有这一行，native 回填无法获得截图块。
    if image_message is not None:  # 新增代码+OAuthNativeToolResultMessages: 只有真实生成图片消息才转换；如果没有这一行，None 会导致后续遍历报错。
        input_items.extend(native_image_input_items_from_message(image_message))  # 新增代码+OAuthNativeToolResultMessages: 把 OpenAI-compatible 图片消息转换成 Responses input_image；如果没有这一行，截图不会进入视觉通道。
    return input_items  # 新增代码+OAuthNativeToolResultMessages: 返回完整 native input items；如果没有这一行，调用方拿不到结果。
# 新增代码+OAuthNativeToolResultMessages: 函数段结束，native_tool_result_messages_to_responses_input_items 到此结束；如果没有这个边界说明，用户不容易看出带图片回填范围。


def native_image_input_items_from_message(image_message: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+OAuthNativeToolResultMessages: 函数段开始，从现有图片消息提取 Responses input_image items；如果没有这段函数，图片格式转换逻辑会散落，本段到 return 列表结束。
    content = image_message.get("content") if isinstance(image_message, dict) else None  # 新增代码+OAuthNativeToolResultMessages: 读取图片消息 content；如果没有这一行，无法找到 image_url 块。
    if not isinstance(content, list):  # 新增代码+OAuthNativeToolResultMessages: 只处理 content 列表；如果没有这一行，字符串 content 会被误遍历。
        return []  # 新增代码+OAuthNativeToolResultMessages: 非列表内容没有图片 item；如果没有这一行，异常形态会继续处理并报错。
    image_items: list[dict[str, Any]] = []  # 新增代码+OAuthNativeToolResultMessages: 准备保存转换后的 input_image；如果没有这一行，无法累积多张截图。
    for block in content:  # 新增代码+OAuthNativeToolResultMessages: 遍历 content 里的每个块；如果没有这一行，无法逐个转换图片。
        if not isinstance(block, dict):  # 新增代码+OAuthNativeToolResultMessages: 防御异常块；如果没有这一行，坏块会导致 .get 报错。
            continue  # 新增代码+OAuthNativeToolResultMessages: 跳过非字典块；如果没有这一行，异常块会中断整次转换。
        image_item = native_image_input_item_from_block(block)  # 新增代码+OAuthNativeToolResultMessages: 尝试把当前块转成 input_image；如果没有这一行，转换细节会写在循环里。
        if image_item is not None:  # 新增代码+OAuthNativeToolResultMessages: 只有合法图片才追加；如果没有这一行，None 会污染结果列表。
            image_items.append(image_item)  # 新增代码+OAuthNativeToolResultMessages: 保存转换后的图片 item；如果没有这一行，模型收不到这张截图。
    return image_items  # 新增代码+OAuthNativeToolResultMessages: 返回所有图片 input items；如果没有这一行，调用方拿不到转换结果。
# 新增代码+OAuthNativeToolResultMessages: 函数段结束，native_image_input_items_from_message 到此结束；如果没有这个边界说明，用户不容易看出图片消息转换范围。


def native_image_input_item_from_block(block: dict[str, Any]) -> dict[str, Any] | None:  # 新增代码+OAuthNativeToolResultMessages: 函数段开始，把单个 image_url/input_image 块转成 Responses input_image；如果没有这段函数，截图块格式兼容会重复实现，本段到 return item 或 None 结束。
    block_type = str(block.get("type", "") or "")  # 新增代码+OAuthNativeToolResultMessages: 读取内容块类型；如果没有这一行，无法区分 image_url 和 input_image。
    raw_url = ""  # 新增代码+OAuthNativeToolResultMessages: 初始化图片 URL；如果没有这一行，后续分支可能引用未定义变量。
    raw_detail = ""  # 新增代码+OAuthNativeToolResultMessages: 初始化图片 detail；如果没有这一行，高精度提示无法安全保留。
    if block_type == "image_url":  # 新增代码+OAuthNativeToolResultMessages: 处理现有 OpenAI-compatible 图片块；如果没有这一行，Computer Use 现有截图消息不会转换。
        raw_image_url = block.get("image_url")  # 新增代码+OAuthNativeToolResultMessages: 读取 image_url 字段；如果没有这一行，拿不到截图地址。
        if isinstance(raw_image_url, dict):  # 新增代码+OAuthNativeToolResultMessages: 处理标准 {"url": "..."} 结构；如果没有这一行，常规图片块会被跳过。
            raw_url = str(raw_image_url.get("url", "") or "").strip()  # 新增代码+OAuthNativeToolResultMessages: 读取并清理 URL；如果没有这一行，input_image 没有 image_url。
            raw_detail = str(raw_image_url.get("detail", "") or "").strip()  # 新增代码+OAuthNativeToolResultMessages: 读取 detail；如果没有这一行，high/low/auto 会丢失。
        else:  # 新增代码+OAuthNativeToolResultMessages: 兼容 image_url 直接是字符串的情况；如果没有这一行，非标准但可恢复格式会丢失。
            raw_url = str(raw_image_url or "").strip()  # 新增代码+OAuthNativeToolResultMessages: 把字符串 image_url 作为 URL；如果没有这一行，兼容分支没有地址。
    if block_type == "input_image":  # 新增代码+OAuthNativeToolResultMessages: 处理已经是 Responses input_image 的块；如果没有这一行，上游直接传原生块时无法复用。
        raw_url = str(block.get("image_url") or block.get("url") or "").strip()  # 新增代码+OAuthNativeToolResultMessages: 读取原生图片地址；如果没有这一行，input_image 无法保留。
        raw_detail = str(block.get("detail", "") or "").strip()  # 新增代码+OAuthNativeToolResultMessages: 读取原生 detail；如果没有这一行，清晰度提示会丢失。
    if not native_image_url_is_allowed(raw_url):  # 新增代码+OAuthNativeToolResultMessages: 只允许明确图片 URL；如果没有这一行，空值或本地路径可能被误发给模型 API。
        return None  # 新增代码+OAuthNativeToolResultMessages: 非法图片不生成 item；如果没有这一行，请求体可能带坏 image_url。
    image_item: dict[str, Any] = {"type": "input_image", "image_url": raw_url}  # 新增代码+OAuthNativeToolResultMessages: 构造 Responses 原生图片输入；如果没有这一行，模型视觉通道没有图片。
    if raw_detail in {"low", "high", "auto"}:  # 新增代码+OAuthNativeToolResultMessages: 只保留常见合法 detail；如果没有这一行，任意字符串可能污染请求体。
        image_item["detail"] = raw_detail  # 新增代码+OAuthNativeToolResultMessages: 写入图片清晰度提示；如果没有这一行，高精度截图可能被默认降级。
    return image_item  # 新增代码+OAuthNativeToolResultMessages: 返回转换后的 input_image；如果没有这一行，调用方拿不到图片。
# 新增代码+OAuthNativeToolResultMessages: 函数段结束，native_image_input_item_from_block 到此结束；如果没有这个边界说明，用户不容易看出单块图片转换范围。


def native_image_url_is_allowed(raw_url: str) -> bool:  # 新增代码+OAuthNativeToolResultMessages: 函数段开始，校验图片 URL 是否可发送给 Responses；如果没有这段函数，坏 URL 过滤会重复且不一致，本段到 return 布尔值结束。
    if not raw_url:  # 新增代码+OAuthNativeToolResultMessages: 拒绝空 URL；如果没有这一行，空图片会进入请求体。
        return False  # 新增代码+OAuthNativeToolResultMessages: 空 URL 不允许发送；如果没有这一行，后端可能返回参数错误。
    return raw_url.startswith("data:image/") or raw_url.startswith("http://") or raw_url.startswith("https://")  # 新增代码+OAuthNativeToolResultMessages: 允许 data/http/https 图片；如果没有这一行，本地路径或占位文本可能被误发。
# 新增代码+OAuthNativeToolResultMessages: 函数段结束，native_image_url_is_allowed 到此结束；如果没有这个边界说明，用户不容易看出图片 URL 安全边界。
