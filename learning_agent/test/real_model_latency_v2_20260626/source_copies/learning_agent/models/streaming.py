from dataclasses import dataclass, field  # 新增代码+真实模型流式合同: 引入 dataclass 工具来定义不可变事件对象；如果没有这行，事件字段会变成松散字典更容易漂移。
from typing import Any, Iterable, Literal, Protocol  # 新增代码+真实模型流式合同: 引入类型工具来约束事件类型和流式模型协议；如果没有这行，调用方无法获得静态类型提示。


ModelStreamEventType = Literal["status", "delta", "error", "completed", "metrics"]  # 新增代码+真实模型流式合同: 限定后端模型事件类型；如果没有这行，前后端可能各自发明事件名导致 UI 无法识别。
ModelStreamPhase = Literal[  # 新增代码+真实模型流式合同: 类型段开始，限定模型调用阶段；如果没有这段，phase 会变成随意字符串。
    "queued",  # 新增代码+真实模型流式合同: 表示 turn 已入队；如果没有这个阶段，无法在统一状态机里描述排队。
    "started",  # 新增代码+真实模型流式合同: 表示后端已开始处理；如果没有这个阶段，无法标记模型调用起点。
    "connecting",  # 新增代码+真实模型流式合同: 表示正在连接模型或 CLI；如果没有这个阶段，用户仍只会看到泛化 running。
    "auth_checking",  # 新增代码+真实模型流式合同: 表示正在检查认证；如果没有这个阶段，OAuth 相关等待无法解释。
    "websocket_connecting",  # 新增代码+真实模型流式合同: 表示正在尝试 WebSocket；如果没有这个阶段，后续 timeout 缺少上下文。
    "websocket_timeout",  # 新增代码+真实模型流式合同: 表示 WebSocket 超时；如果没有这个阶段，用户不知道为何会 fallback。
    "https_fallback",  # 新增代码+真实模型流式合同: 表示正在切换 HTTPS fallback；如果没有这个阶段，2 分钟等待缺少可见原因。
    "streaming",  # 新增代码+真实模型流式合同: 表示正在接收模型输出；如果没有这个阶段，前端无法区分连接和输出。
    "first_delta",  # 新增代码+真实模型流式合同: 表示首个 delta 已到达；如果没有这个阶段，无法单独度量首 token。
    "completed",  # 新增代码+真实模型流式合同: 表示模型调用完成；如果没有这个阶段，右侧状态无法收尾。
    "cancel_requested",  # 新增代码+真实模型流式合同: 表示用户已请求取消；如果没有这个阶段，取消按钮没有即时反馈。
    "cancelled",  # 新增代码+真实模型流式合同: 表示后端已确认取消；如果没有这个阶段，用户不知道后台是否停止。
    "failed",  # 新增代码+真实模型流式合同: 表示模型调用失败；如果没有这个阶段，错误会和普通状态混在一起。
]  # 新增代码+真实模型流式合同: 阶段类型结束；如果没有这行，Literal 语法不完整。


@dataclass(frozen=True)  # 新增代码+真实模型流式合同: 声明事件不可变；如果没有这行，事件在传递过程中可能被误改。
class ModelStreamEvent:  # 新增代码+真实模型流式合同: 类段开始，定义后端到 GUI 的模型流事件；如果没有这段，adapter 和模型之间没有稳定合同。
    event_type: ModelStreamEventType  # 新增代码+真实模型流式合同: 保存事件类型；如果没有这行，前端无法知道这是状态、文本还是错误。
    phase: ModelStreamPhase  # 新增代码+真实模型流式合同: 保存有限状态机阶段；如果没有这行，状态显示会继续发散。
    message: str  # 新增代码+真实模型流式合同: 保存用户可见或可记录的文本；如果没有这行，状态事件没有可读内容。
    timestamp: float  # 新增代码+真实模型流式合同: 保存事件时间戳；如果没有这行，首状态和首 delta 无法度量。
    elapsed_ms: int  # 新增代码+真实模型流式合同: 保存相对耗时毫秒；如果没有这行，前端需要重复推导时间差。
    sequence: int  # 新增代码+真实模型流式合同: 保存单 turn 内顺序号；如果没有这行，事件排序和 stale delta 防护更弱。
    turn_id: str  # 新增代码+真实模型流式合同: 保存所属 turn；如果没有这行，取消后的旧事件可能进入新会话。
    provider_id: str  # 新增代码+真实模型流式合同: 保存 provider；如果没有这行，用户无法确认调用来源。
    model_id: str  # 新增代码+真实模型流式合同: 保存模型；如果没有这行，用户无法确认底部选择是否被真实使用。
    metadata: dict[str, Any] = field(default_factory=dict)  # 新增代码+真实模型流式合同: 保存脱敏诊断元数据；如果没有这行，transport 等信息只能塞进 message。


class StreamingChatModel(Protocol):  # 新增代码+真实模型流式合同: 协议段开始，定义支持真实流事件的模型接口；如果没有这段，adapter 无法用统一方式消费不同 provider。
    def stream_chat(  # 新增代码+真实模型流式合同: 方法段开始，声明流式聊天入口；如果没有这段，模型只能继续阻塞式 chat。
        self,  # 新增代码+真实模型流式合同: 当前模型实例；如果没有这行，Python 方法签名不完整。
        messages: list[dict[str, Any]],  # 新增代码+真实模型流式合同: 当前对话消息；如果没有这行，模型没有用户 prompt。
        tools: list[dict[str, Any]],  # 新增代码+真实模型流式合同: 当前可用工具 schema；如果没有这行，模型无法做工具决策。
        *,  # 新增代码+真实模型流式合同: 强制后续上下文参数使用关键字；如果没有这行，调用方容易把 turn_id/provider_id/model_id 传错顺序。
        turn_id: str,  # 新增代码+真实模型流式合同: 当前 turn id；如果没有这行，事件无法绑定到本轮。
        provider_id: str,  # 新增代码+真实模型流式合同: 当前 provider id；如果没有这行，事件无法说明调用来源。
        model_id: str,  # 新增代码+真实模型流式合同: 当前模型 id；如果没有这行，事件无法说明所选模型。
    ) -> Iterable[ModelStreamEvent]:  # 新增代码+真实模型流式合同: 返回模型事件迭代器；如果没有这行，调用方无法逐步收到状态和 delta。
        ...  # 新增代码+真实模型流式合同: Protocol 方法占位；如果没有这行，协议声明没有方法体会语法错误。
