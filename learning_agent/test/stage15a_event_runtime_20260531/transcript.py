"""Stage 15A transcript 写入器。"""  # 新增代码+Stage15A: 这个文件负责把运行事件写入磁盘；若没有这个文件，事件只能留在内存里，任务中断后无法恢复。

from __future__ import annotations  # 新增代码+Stage15A: 延迟解析类型注解；若没有这行代码，未来添加前向引用时更容易受顺序影响。

from pathlib import Path  # 新增代码+Stage15A: 使用 Path 管理 session 目录和 events.jsonl；若没有这行代码，路径拼接会更容易出错。

try:  # 新增代码+Stage15A: 优先按包运行模式导入事件序列化函数；若没有这行代码，正式包导入路径无法工作。
    from learning_agent.core.events import AgentEvent, agent_event_to_json_line  # 新增代码+Stage15A: 导入事件对象和 JSONL 序列化入口；若没有这行代码，writer 无法写入统一事件格式。
except ModuleNotFoundError as error:  # 新增代码+Stage15A: 捕获直接脚本运行时包名前缀不可用的情况；若没有这行代码，bat 入口可能因为导入路径失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.events"}:  # 新增代码+Stage15A: 只允许包路径缺失时 fallback；若没有这行代码，真实导入 bug 会被误吞。
        raise  # 新增代码+Stage15A: 重新抛出真实导入错误；若没有这行代码，排查 transcript 问题会很困难。
    from core.events import AgentEvent, agent_event_to_json_line  # type: ignore  # 新增代码+Stage15A: 脚本模式下导入事件模块；若没有这行代码，直接执行入口可能找不到事件定义。


class TranscriptWriter:  # 新增代码+Stage15A: 定义 transcript 写入器；若没有这行代码，调用方没有稳定对象管理 session 事件文件。
    def __init__(self, base_dir: Path, session_id: str) -> None:  # 新增代码+Stage15A: 初始化 writer 所属目录和 session；若没有这行代码，writer 不知道事件要写到哪里。
        self.base_dir = Path(base_dir)  # 新增代码+Stage15A: 保存 transcript 根目录；若没有这行代码，后续无法创建 session 目录。
        self.session_id = session_id  # 新增代码+Stage15A: 保存会话编号；若没有这行代码，多个 session 会写到同一目录。
        self.session_dir = self.base_dir / session_id  # 新增代码+Stage15A: 计算当前 session 目录；若没有这行代码，events.jsonl 路径无法固定。
        self.events_path = self.session_dir / "events.jsonl"  # 新增代码+Stage15A: 计算事件文件路径；若没有这行代码，resume 后续不知道读取哪个文件。

    def write_event(self, event: AgentEvent) -> Path:  # 新增代码+Stage15A: 写入一条事件并返回文件路径；若没有这行代码，主循环无法把事件落盘。
        self.session_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Stage15A: 确保 session 目录存在；若没有这行代码，首次写入会因为目录缺失失败。
        with self.events_path.open("a", encoding="utf-8", newline="") as file_handle:  # 新增代码+Stage15A: 以追加模式打开 JSONL 文件；若没有这行代码，第二条事件会覆盖第一条。
            file_handle.write(agent_event_to_json_line(event))  # 新增代码+Stage15A: 写入事件 JSON 行；若没有这行代码，事件不会真正落盘。
        return self.events_path  # 新增代码+Stage15A: 返回事件文件路径；若没有这行代码，调用方无法记录 transcript 写到哪里。
