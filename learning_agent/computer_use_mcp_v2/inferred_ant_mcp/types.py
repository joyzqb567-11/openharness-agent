"""Computer Use MCP v2 共享类型。"""  # 新增代码+ComputerUseMcpV2：说明本文件存放跨模块数据结构；如果没有这行代码，Context 可能被重复定义。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，循环引用更容易在导入时出错。

from dataclasses import dataclass, field  # 新增代码+ComputerUseMcpV2：导入 dataclass 简化上下文对象；如果没有这行代码，Context 初始化需要手写样板代码。
from typing import Any, Callable  # 新增代码+ComputerUseMcpV2：导入通用类型和回调类型；如果没有这行代码，agent-side 绑定字段含义不清楚。


@dataclass  # 新增代码+ComputerUseMcpV2：自动生成初始化方法；如果没有这行代码，上下文字段越多越容易手写出错。
class ComputerUseMcpV2Context:  # 新增代码+ComputerUseMcpV2：类段开始，保存一次 v2 MCP 调用链共享的宿主、权限、trace 和状态；如果没有这段类，stdio server 和 agent-side wrapper 无法共享能力。
    host: Any | None = None  # 新增代码+ComputerUseMcpV2：保存 Windows 宿主适配器或测试 fake host；如果没有这一行，runtime 无法执行真实鼠标键盘或 fake 测试动作。
    ask_permission: Callable[[str], bool] | None = None  # 新增代码+ComputerUseMcpV2：保存 agent 主循环授权回调；如果没有这一行，request_access 不能复用用户确认能力。
    record_observation: Callable[[str, dict[str, Any]], None] | None = None  # 新增代码+ComputerUseMcpV2：保存观察事件回调；如果没有这一行，observe/screenshot 证据不会回到 agent。
    record_runtime_trace: Callable[[dict[str, Any]], None] | None = None  # 新增代码+ComputerUseMcpV2：保存 runtime trace 回调；如果没有这一行，工具执行链无法证明走的是 v2。
    emit_acceptance_event: Callable[[str, dict[str, Any]], None] | None = None  # 新增代码+ComputerUseMcpV2：保存可见终端验收事件回调；如果没有这一行，真实场景验收缺少事件桥。
    grants: dict[str, Any] = field(default_factory=dict)  # 新增代码+ComputerUseMcpV2：保存本会话授权摘要；如果没有这一行，list_granted_applications 没有状态来源。
    clipboard_text: str = ""  # 新增代码+ComputerUseMcpV2：保存受控内存剪贴板文本；如果没有这一行，write_clipboard/read_clipboard 无法形成最小闭环。
# 新增代码+ComputerUseMcpV2：类段结束，ComputerUseMcpV2Context 到此结束；如果没有这个边界说明，用户不容易看出 v2 上下文生命周期。

