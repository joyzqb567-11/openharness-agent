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
