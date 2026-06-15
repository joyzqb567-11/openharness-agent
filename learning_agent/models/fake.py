"""测试用假模型实现，专门服务离线工具循环和单元测试。"""  # 新增代码+AgentPyPhaseKFakeModel: 说明本文件只放测试模型；若没有这行代码，读者会误以为假模型仍属于主循环职责。
from __future__ import annotations  # 新增代码+AgentPyPhaseKFakeModel: 允许类型注解延迟解析；若没有这行代码，脚本模式下类型顺序更容易引入导入问题。

from typing import Any  # 新增代码+AgentPyPhaseKFakeModel: 为 chat 参数里的通用 JSON 字典提供类型；若没有这行代码，函数签名无法表达工具 schema 的宽松结构。

try:  # 新增代码+AgentPyPhaseKFakeModel: 包运行模式下优先读取统一消息对象；若没有这行代码，假模型会重复定义 ModelMessage。
    from learning_agent.core.messages import ModelMessage  # 新增代码+AgentPyPhaseKFakeModel: 导入模型返回消息结构；若没有这行代码，假模型无法返回主循环认识的消息对象。
except ModuleNotFoundError as error:  # 新增代码+AgentPyPhaseKFakeModel: 兼容直接脚本模式缺少 learning_agent 包名前缀的情况；若没有这行代码，bat 入口或本地脚本可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.messages"}:  # 新增代码+AgentPyPhaseKFakeModel: 只允许路径前缀缺失时 fallback；若没有这行代码，真实导入 bug 会被误吞。
        raise  # 新增代码+AgentPyPhaseKFakeModel: 非路径类错误继续抛出；若没有这行代码，排查消息模块问题会很困难。
    from core.messages import ModelMessage  # 新增代码+AgentPyPhaseKFakeModel: 脚本模式下从同级 core 包导入消息结构；若没有这行代码，直接运行时假模型找不到 ModelMessage。


class ToolCallingFakeModel:  # 新增代码+AgentPyPhaseKFakeModel: 函数段开始，定义测试用假模型；若没有这个类，离线主循环测试必须调用真实模型，作者意图是让测试稳定、快速、可重复。
    def __init__(self, responses: list[ModelMessage]) -> None:  # 新增代码+AgentPyPhaseKFakeModel: 接收预设模型回复列表；若没有这行代码，测试无法安排“先调用工具再最终回答”的固定剧本。
        self._responses = responses  # 新增代码+AgentPyPhaseKFakeModel: 保存预设回复；若没有这行代码，chat 调用时没有内容可返回。
        self._index = 0  # 新增代码+AgentPyPhaseKFakeModel: 记录下一次应返回第几条回复；若没有这行代码，假模型无法按顺序推进多轮工具循环。

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelMessage:  # 新增代码+AgentPyPhaseKFakeModel: 实现 ChatModel 最小接口；若没有这段函数，LearningAgent 无法把假模型当成普通模型使用。
        del messages, tools  # 新增代码+AgentPyPhaseKFakeModel: 明确假模型不读取上下文和工具表；若没有这行代码，静态检查会误以为参数遗漏且读者会期待它做真实推理。
        if self._index >= len(self._responses):  # 新增代码+AgentPyPhaseKFakeModel: 判断预设回复是否已经用完；若没有这行代码，多调用一次会触发列表越界异常。
            return ModelMessage(text="假模型没有更多预设回答。")  # 新增代码+AgentPyPhaseKFakeModel: 返回可读兜底消息；若没有这行代码，测试失败时只会看到底层异常。
        response = self._responses[self._index]  # 新增代码+AgentPyPhaseKFakeModel: 取出本轮应返回的预设消息；若没有这行代码，chat 无法给主循环回复。
        self._index += 1  # 新增代码+AgentPyPhaseKFakeModel: 推进到下一条预设消息；若没有这行代码，工具循环会反复收到同一条回复。
        return response  # 新增代码+AgentPyPhaseKFakeModel: 把预设消息交给主循环；若没有这行代码，LearningAgent 拿不到模型结果。
    # 新增代码+AgentPyPhaseKFakeModel: 函数段结束，ToolCallingFakeModel 到此结束；若没有这个边界说明，用户不容易看出假模型只负责顺序返回预设消息。
