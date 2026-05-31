"""Tool Executor v2 的 hook 事件和管理器。"""  # 新增代码+Stage15E: 把工具执行前后的扩展点独立成模块；若没有这个文件，权限审计和后续 UI hook 会继续散落在执行器里。

from __future__ import annotations  # 新增代码+Stage15E: 延迟解析类型注解；若没有这行代码，回调类型引用更容易受定义顺序影响。

import copy  # 新增代码+Stage15E: hook 事件需要深拷贝参数；若没有这行代码，回调可能改坏原始工具参数。
from dataclasses import dataclass, field  # 新增代码+Stage15E: 快速定义 hook 事件对象并支持字典默认值；若没有这行代码，需要手写重复初始化代码。
from typing import Any, Callable  # 新增代码+Stage15E: hook 回调和 JSON 风格参数需要通用类型；若没有这行代码，接口边界不清楚。


@dataclass  # 新增代码+Stage15E: 自动生成 hook 事件初始化方法；若没有这行代码，每次构造事件都要手写样板逻辑。
class ToolHookEvent:  # 新增代码+Stage15E: 表示一次工具 hook 看到的上下文；若没有这个类，hook 回调只能接收松散 dict。
    tool_name: str  # 新增代码+Stage15E: 保存工具名；若没有这行代码，hook 不知道当前拦截的是哪个工具。
    call_id: str  # 新增代码+Stage15E: 保存工具调用 id；若没有这行代码，hook 事件无法和模型 tool_call 对齐。
    arguments: dict[str, Any]  # 新增代码+Stage15E: 保存工具参数；若没有这行代码，权限和审计 hook 看不到工具输入。
    result_text: str = ""  # 新增代码+Stage15E: 保存工具结果文本；若没有这行代码，post hook 无法审计工具输出。
    error_text: str = ""  # 新增代码+Stage15E: 保存错误摘要；若没有这行代码，tool_error hook 无法拿到失败原因。
    permission_status: str = ""  # 新增代码+Stage15E: 保存权限决策状态；若没有这行代码，permission hook 不知道 allow/deny/ask/auto_allow。
    metadata: dict[str, Any] = field(default_factory=dict)  # 新增代码+Stage15E: 保存额外上下文；若没有这行代码，后续扩展只能改类字段。

    def to_payload(self) -> dict[str, Any]:  # 新增代码+Stage15E: 把 hook 事件转成可写入 observation 的 dict；若没有这行代码，执行器会重复拼装审计载荷。
        return {  # 新增代码+Stage15E: 返回新的 payload 避免外部直接修改事件对象；若没有这行代码，观察日志可能被后续回调污染。
            "tool_name": self.tool_name,  # 新增代码+Stage15E: 写入工具名；若没有这行代码，日志无法按工具过滤。
            "call_id": self.call_id,  # 新增代码+Stage15E: 写入调用 id；若没有这行代码，日志无法关联同一次工具调用。
            "arguments": copy.deepcopy(self.arguments),  # 新增代码+Stage15E: 深拷贝参数；若没有这行代码，回调或调用方可能污染历史记录。
            "result_text": self.result_text,  # 新增代码+Stage15E: 写入结果文本；若没有这行代码，post hook 审计缺少输出摘要。
            "error_text": self.error_text,  # 新增代码+Stage15E: 写入错误文本；若没有这行代码，失败事件没有原因。
            "permission_status": self.permission_status,  # 新增代码+Stage15E: 写入权限状态；若没有这行代码，权限审计缺少决策结果。
            "metadata": copy.deepcopy(self.metadata),  # 新增代码+Stage15E: 深拷贝扩展元数据；若没有这行代码，后续修改会污染 observation。
        }  # 新增代码+Stage15E: payload 字典结束；若没有这行代码，Python 语法不完整。


ToolHookCallback = Callable[[ToolHookEvent], Any]  # 新增代码+Stage15E: 定义 hook 回调签名；若没有这行代码，注册接口的输入输出不清楚。


class ToolHookManager:  # 新增代码+Stage15E: 管理不同阶段的工具 hook；若没有这个类，执行器无法统一运行 pre/post/denied/error 回调。
    def __init__(self) -> None:  # 新增代码+Stage15E: 初始化 hook 存储；若没有这行代码，管理器没有地方保存回调。
        self._hooks: dict[str, list[ToolHookCallback]] = {}  # 新增代码+Stage15E: 按 hook 名称保存回调列表；若没有这行代码，多个扩展点会混在一起。

    def add_hook(self, hook_name: str, callback: ToolHookCallback) -> None:  # 新增代码+Stage15E: 注册某个阶段的 hook；若没有这行代码，外部无法接入执行器生命周期。
        self._hooks.setdefault(hook_name, []).append(callback)  # 新增代码+Stage15E: 把回调追加到对应阶段；若没有这行代码，注册的 hook 不会被执行。

    def run_hooks(self, hook_name: str, event: ToolHookEvent) -> list[str]:  # 新增代码+Stage15E: 运行某个阶段的全部 hook 并收集错误；若没有这行代码，hook 报错可能直接中断 agent。
        errors: list[str] = []  # 新增代码+Stage15E: 保存 hook 异常文本；若没有这行代码，调用方无法知道哪些 hook 失败。
        for callback in list(self._hooks.get(hook_name, [])):  # 新增代码+Stage15E: 遍历该阶段回调快照；若没有这行代码，注册的 hook 不会运行。
            try:  # 新增代码+Stage15E: 捕获单个 hook 的异常；若没有这行代码，一个坏 hook 会拖垮整个工具执行。
                callback(event)  # 新增代码+Stage15E: 调用实际 hook；若没有这行代码，注册 hook 只是被保存但不会生效。
            except Exception as error:  # 新增代码+Stage15E: 把 hook 异常转成文本；若没有这行代码，异常会向上冒泡中断 agent。
                errors.append(str(error))  # 新增代码+Stage15E: 保存错误摘要；若没有这行代码，执行器无法生成 tool_error 观察事件。
        return errors  # 新增代码+Stage15E: 返回所有 hook 错误；若没有这行代码，调用方无法判断是否需要阻断或上报。
