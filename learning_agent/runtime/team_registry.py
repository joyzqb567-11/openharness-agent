"""持久化 team peer 登记表，让教学版 peer 不再只活在内存里。"""  # 新增代码+DurableTeamRegistry: 说明本文件负责把 team peer 落盘；若没有这行代码，后续维护者不容易知道 team 状态从哪里恢复。
from __future__ import annotations  # 新增代码+DurableTeamRegistry: 延迟解析类型注解；若没有这行代码，类方法引用自身或复杂类型时更容易被解释顺序影响。
from pathlib import Path  # 新增代码+DurableTeamRegistry: 使用 Path 管理跨平台路径；若没有这行代码，Windows 路径拼接会更脆弱。
from typing import Any  # 新增代码+DurableTeamRegistry: JSON payload 字段是通用类型；若没有这行代码，序列化边界不够清楚。
from learning_agent.runtime.files import FileLock, atomic_write_json, read_json_or_default  # 新增代码+DurableTeamRegistry: 复用项目已有锁和原子 JSON helper；若没有这行代码，team 状态写入会缺少崩溃安全。
from learning_agent.tasks.team import TeamMessage, TeamPeer  # 新增代码+DurableTeamRegistry: 复用现有 team 数据结构；若没有这行代码，持久层会和工具层产生两套 peer 对象。

def _safe_id(raw_id: str) -> str:  # 新增代码+DurableTeamRegistry: 清理 peer_id 防止路径穿越；若没有这行代码，奇怪 id 可能逃出 registry 目录。
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in str(raw_id))  # 新增代码+DurableTeamRegistry: 只保留文件名安全字符；若没有这行代码，Windows 特殊字符会导致读写失败。

def _message_to_dict(message: TeamMessage) -> dict[str, Any]:  # 新增代码+DurableTeamRegistry: 把 TeamMessage 转成 JSON 对象；若没有这行代码，消息 inbox 无法稳定落盘。
    return {"message_id": message.message_id, "sender": message.sender, "content": message.content, "created_at": message.created_at, "acknowledged_at": message.acknowledged_at, "ack_note": message.ack_note}  # 新增代码+DurableTeamRegistry: 保存消息全部审计字段；若没有这行代码，重启后消息内容或确认状态会丢失。

def _message_from_dict(payload: dict[str, Any]) -> TeamMessage:  # 新增代码+DurableTeamRegistry: 从 JSON 对象恢复 TeamMessage；若没有这行代码，读出的消息只能是松散 dict。
    return TeamMessage(message_id=str(payload.get("message_id", "")), sender=str(payload.get("sender", "")), content=str(payload.get("content", "")), created_at=str(payload.get("created_at", "")), acknowledged_at=str(payload.get("acknowledged_at", "")), ack_note=str(payload.get("ack_note", "")))  # 新增代码+DurableTeamRegistry: 对缺失字段使用空字符串兜底；若没有这行代码，旧格式或坏字段会让恢复失败。

def _peer_to_dict(peer: TeamPeer) -> dict[str, Any]:  # 新增代码+DurableTeamRegistry: 把 TeamPeer 转成 JSON 对象；若没有这行代码，peer 状态无法跨进程保存。
    return {"peer_id": peer.peer_id, "name": peer.name, "role": peer.role, "status": peer.status, "notes": peer.notes, "created_at": peer.created_at, "inbox": [_message_to_dict(message) for message in peer.inbox], "bound_task_id": peer.bound_task_id, "bound_task_started_at": peer.bound_task_started_at}  # 新增代码+DurableTeamRegistry: 保存 peer 元信息、inbox 和绑定 task；若没有这行代码，team 视图重启后会失去上下文。

def _peer_from_dict(payload: dict[str, Any]) -> TeamPeer:  # 新增代码+DurableTeamRegistry: 从 JSON 对象恢复 TeamPeer；若没有这行代码，新 agent 无法读取旧 peer。
    raw_inbox = payload.get("inbox", [])  # 新增代码+DurableTeamRegistry: 读取 inbox 原始数组；若没有这行代码，后续无法恢复消息列表。
    inbox = [_message_from_dict(item) for item in raw_inbox if isinstance(item, dict)] if isinstance(raw_inbox, list) else []  # 新增代码+DurableTeamRegistry: 只恢复合法消息对象；若没有这行代码，坏 inbox 会拖垮整个 peer。
    return TeamPeer(peer_id=str(payload.get("peer_id", "")), name=str(payload.get("name", "")), role=str(payload.get("role", "peer")), status=str(payload.get("status", "idle")), notes=str(payload.get("notes", "")), created_at=str(payload.get("created_at", "")), inbox=inbox, bound_task_id=str(payload.get("bound_task_id", "")), bound_task_started_at=str(payload.get("bound_task_started_at", "")))  # 新增代码+DurableTeamRegistry: 恢复完整 peer 对象；若没有这行代码，工具层拿不到可继续使用的 TeamPeer。

class TeamRegistry:  # 新增代码+DurableTeamRegistry: 管理持久化 peer 文件；若没有这个类，team 工具仍只能依赖 self.team_peers 内存字典。
    def __init__(self, base_dir: str | Path) -> None:  # 新增代码+DurableTeamRegistry: 初始化 registry 根目录；若没有这行代码，调用方无法指定测试或生产存储位置。
        self.base_dir = Path(base_dir)  # 新增代码+DurableTeamRegistry: 规范化根目录为 Path；若没有这行代码，后续路径拼接不稳定。
        self.records_dir = self.base_dir / "records"  # 新增代码+DurableTeamRegistry: 约定 peer JSON 文件目录；若没有这行代码，peer 文件会散落难以审计。
        self.lock_path = self.base_dir / "team.lock"  # 新增代码+DurableTeamRegistry: 约定跨进程写入锁；若没有这行代码，多 agent 同时写 peer 时可能互相覆盖。
        self.quarantine_dir = self.base_dir / "quarantine"  # 新增代码+DurableTeamRegistry: 约定坏 JSON 隔离目录；若没有这行代码，半写 peer 文件会反复拖垮列表。
    def peer_path(self, peer_id: str) -> Path:  # 新增代码+DurableTeamRegistry: 计算单个 peer 的 JSON 路径；若没有这行代码，读写路径规则会散落各处。
        return self.records_dir / f"{_safe_id(peer_id)}.json"  # 新增代码+DurableTeamRegistry: 返回安全文件名路径；若没有这行代码，未知字符可能导致文件操作失败。
    def save_peer(self, peer: TeamPeer) -> Path:  # 新增代码+DurableTeamRegistry: 保存一个 peer 到磁盘；若没有这行代码，team_create/send/ack 的状态不会跨进程存在。
        with FileLock(self.lock_path):  # 新增代码+DurableTeamRegistry: 写入前加锁；若没有这行代码，并发写入可能产生损坏 JSON。
            return atomic_write_json(self.peer_path(peer.peer_id), _peer_to_dict(peer))  # 新增代码+DurableTeamRegistry: 原子保存 peer JSON；若没有这行代码，崩溃可能留下半写文件。
    def get_peer(self, peer_id: str) -> TeamPeer:  # 新增代码+DurableTeamRegistry: 读取单个 peer；若没有这行代码，新 agent 无法按 peer_id 找回旧 peer。
        payload = read_json_or_default(self.peer_path(peer_id), {}, quarantine_dir=self.quarantine_dir)  # 新增代码+DurableTeamRegistry: 容错读取 peer JSON；若没有这行代码，坏文件会直接抛异常。
        if not isinstance(payload, dict) or not payload:  # 新增代码+DurableTeamRegistry: 校验读取结果是否有效；若没有这行代码，空对象会伪装成真实 peer。
            raise KeyError(peer_id)  # 新增代码+DurableTeamRegistry: 未找到时抛 KeyError；若没有这行代码，调用方无法区分缺失和空字段。
        return _peer_from_dict(payload)  # 新增代码+DurableTeamRegistry: 返回恢复后的 TeamPeer；若没有这行代码，工具层拿不到可操作对象。
    def list_peers(self) -> list[TeamPeer]:  # 新增代码+DurableTeamRegistry: 列出所有持久 peer；若没有这行代码，list_peers 无法跨进程展示成员。
        if not self.records_dir.exists():  # 新增代码+DurableTeamRegistry: 首次运行目录不存在时返回空列表；若没有这行代码，空状态会报错。
            return []  # 新增代码+DurableTeamRegistry: 没有 peer 时正常返回空列表；若没有这行代码，调用方要重复写兜底逻辑。
        peers: list[TeamPeer] = []  # 新增代码+DurableTeamRegistry: 准备累计恢复出的 peer；若没有这行代码，函数没有返回容器。
        for path in sorted(self.records_dir.glob("*.json")):  # 新增代码+DurableTeamRegistry: 稳定遍历全部 peer 文件；若没有这行代码，列表顺序不稳定且无法读取全部记录。
            payload = read_json_or_default(path, {}, quarantine_dir=self.quarantine_dir)  # 新增代码+DurableTeamRegistry: 容错读取单个 peer 文件；若没有这行代码，坏 peer 会让整个列表失败。
            if isinstance(payload, dict) and payload:  # 新增代码+DurableTeamRegistry: 只处理非空 JSON 对象；若没有这行代码，空文件会污染列表。
                peers.append(_peer_from_dict(payload))  # 新增代码+DurableTeamRegistry: 加入恢复后的 peer；若没有这行代码，列表不会包含该成员。
        return peers  # 新增代码+DurableTeamRegistry: 返回全部 peer；若没有这行代码，调用方拿不到持久团队状态。
    def delete_peer(self, peer_id: str) -> TeamPeer:  # 新增代码+DurableTeamRegistry: 删除并返回一个 peer；若没有这行代码，team_delete 无法跨进程清理旧记录。
        peer = self.get_peer(peer_id)  # 新增代码+DurableTeamRegistry: 先读取 peer 供返回审计信息；若没有这行代码，删除后不知道删了谁。
        with FileLock(self.lock_path):  # 新增代码+DurableTeamRegistry: 删除时加锁；若没有这行代码，并发保存和删除可能互相踩踏。
            try:  # 新增代码+DurableTeamRegistry: 删除文件需要容错；若没有这行代码，重复删除会打断工具流程。
                self.peer_path(peer_id).unlink()  # 新增代码+DurableTeamRegistry: 删除 peer JSON；若没有这行代码，team_delete 只会删除内存不删除磁盘。
            except FileNotFoundError:  # 新增代码+DurableTeamRegistry: 兼容文件已经消失的情况；若没有这行代码，跨进程竞争会抛错。
                pass  # 新增代码+DurableTeamRegistry: 文件已不存在视为删除完成；若没有这行代码，except 分支语法不完整。
        return peer  # 新增代码+DurableTeamRegistry: 返回被删除的 peer 供工具输出；若没有这行代码，用户无法审计删除结果。
