"""教学版 team/peer 通信记录。"""  # 新增代码+TasksSplit: 说明本模块承载 team_create/send_message/list_peers 等工具的数据结构；如果没有这行代码，team 相关记录难以快速定位。

from __future__ import annotations  # 新增代码+TasksSplit: 允许类型注解延迟解析；如果没有这行代码，列表中的 TeamMessage 标注可能受定义顺序影响。

from dataclasses import dataclass, field  # 新增代码+TasksSplit: 用 dataclass 和默认工厂定义 team 记录；如果没有这行代码，inbox 默认列表会很容易写错。


@dataclass  # 新增代码+TasksSplit: 自动生成 team 消息记录初始化方法；如果没有这行代码，send_message 只能用松散字典保存消息且容易写错字段。
class TeamMessage:  # 新增代码+TasksSplit: 保存一条发给 peer 的教学版消息；如果没有这行代码，peer inbox 无法保留可审计消息记录。
    message_id: str  # 新增代码+TasksSplit: 保存消息唯一 id；如果没有这行代码，用户和模型无法引用或审计具体消息。
    sender: str  # 新增代码+TasksSplit: 保存消息发送者名称；如果没有这行代码，peer inbox 不知道消息从哪里来。
    content: str  # 新增代码+TasksSplit: 保存消息正文；如果没有这行代码，send_message 只会改变计数但丢失真正内容。
    created_at: str  # 新增代码+TasksSplit: 保存消息创建时间；如果没有这行代码，用户难以判断消息发送顺序。
    acknowledged_at: str = ""  # 新增代码+TasksSplit: 保存消息确认处理时间；如果没有这行代码，ack_peer_message 无法区分已处理和待处理消息。
    ack_note: str = ""  # 新增代码+TasksSplit: 保存确认消息时的备注；如果没有这行代码，用户无法审计确认时留下的处理说明。


@dataclass  # 新增代码+TasksSplit: 自动生成 peer 记录初始化方法；如果没有这行代码，list_peers 只能依赖松散字典且字段容易写错。
class TeamPeer:  # 新增代码+TasksSplit: 保存一个教学版 peer/agent 登记记录；如果没有这行代码，team_create 无法留下可列出的多 agent 成员。
    peer_id: str  # 新增代码+TasksSplit: 保存 peer 唯一 id；如果没有这行代码，send_message 无法定位收件对象。
    name: str  # 新增代码+TasksSplit: 保存 peer 可读名称；如果没有这行代码，list_peers 只能显示难记 id。
    role: str  # 新增代码+TasksSplit: 保存 peer 角色，例如 explorer/worker/reviewer；如果没有这行代码，主 agent 难以按职责分配消息。
    status: str  # 新增代码+TasksSplit: 保存 peer 当前教学状态；如果没有这行代码，list_peers 无法展示 peer 是否 idle/active。
    notes: str = ""  # 新增代码+TasksSplit: 保存 peer 备注或职责边界；如果没有这行代码，team_create 无法留下交接说明。
    created_at: str = ""  # 新增代码+TasksSplit: 保存 peer 创建时间；如果没有这行代码，多 peer 场景难以判断登记顺序。
    inbox: list[TeamMessage] = field(default_factory=list)  # 新增代码+TasksSplit: 保存发给 peer 的消息队列；如果没有这行代码，send_message 无法把消息留给目标 peer。
    bound_task_id: str = ""  # 新增代码+TasksSplit: 保存 peer 当前绑定的后台 task id；如果没有这行代码，list_peers 无法从 team 视图跳转到 task_output/task_stop。
    bound_task_started_at: str = ""  # 新增代码+TasksSplit: 保存 peer 绑定后台 task 的启动时间；如果没有这行代码，用户无法判断 peer 从何时开始执行任务。


def peer_status_from_pending_count(pending_count: int) -> str:  # 新增代码+TasksSplit: 根据待确认消息数计算 peer 状态；如果没有这行代码，ack_peer_message 的状态更新规则会继续散落在主文件。
    return "active" if pending_count else "idle"  # 新增代码+TasksSplit: 有待处理消息则 active，否则 idle；如果没有这行代码，peer 状态更新会不一致。
