"""持久任务输出文件管理，对齐 ClaudeCode TaskOutput。"""  # 新增代码+TaskOutput: 说明本文件负责长输出落盘、tail、delta 和清理；若没有这行代码，输出治理边界不清楚。

from __future__ import annotations  # 新增代码+TaskOutput: 延迟解析类型注解；若没有这行代码，后续返回自身类型时更容易受顺序影响。

from dataclasses import dataclass  # 新增代码+TaskOutput: 用 dataclass 表达增量读取结果；若没有这行代码，delta 结果只能用松散 dict。
from pathlib import Path  # 新增代码+TaskOutput: 用 Path 管理输出文件；若没有这行代码，Windows 路径处理更脆弱。


@dataclass  # 新增代码+TaskOutput: 自动生成 TaskOutputDelta 初始化方法；若没有这行代码，增量结果需要手写构造器。
class TaskOutputDelta:  # 新增代码+TaskOutput: 表示从某个 offset 读取到的新输出；若没有这个类，调用方不知道下一次从哪里继续。
    text: str  # 新增代码+TaskOutput: 保存本次读取到的文本；若没有这行代码，模型拿不到增量内容。
    next_offset: int  # 新增代码+TaskOutput: 保存下一次读取应使用的 offset；若没有这行代码，主 agent 会反复读取旧输出。


class TaskOutputStore:  # 新增代码+TaskOutput: 管理每个 task 的输出文件；若没有这个类，后台任务大输出只能留在内存或塞回模型。
    def __init__(self, base_dir: str | Path) -> None:  # 新增代码+TaskOutput: 初始化输出根目录；若没有这行代码，调用方无法指定存储位置。
        self.base_dir = Path(base_dir)  # 新增代码+TaskOutput: 规范化根目录为 Path；若没有这行代码，后续路径拼接不稳定。

    def output_path(self, task_id: str) -> Path:  # 新增代码+TaskOutput: 计算 task 输出文件路径；若没有这行代码，各模块会重复拼路径。
        safe_task_id = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in str(task_id))  # 新增代码+TaskOutput: 清洗 task_id 避免路径注入；若没有这行代码，奇怪 id 可能逃出输出目录。
        return self.base_dir / f"{safe_task_id}.txt"  # 新增代码+TaskOutput: 返回固定输出文件；若没有这行代码，增量读取找不到同一个文件。

    def append(self, task_id: str, text: str) -> Path:  # 新增代码+TaskOutput: 追加任务输出；若没有这行代码，后台任务进度无法落盘。
        path = self.output_path(task_id)  # 新增代码+TaskOutput: 计算输出文件路径；若没有这行代码，无法写入目标文件。
        path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+TaskOutput: 确保输出目录存在；若没有这行代码，首次追加会失败。
        with path.open("a", encoding="utf-8", newline="") as file_handle:  # 新增代码+TaskOutput: 追加模式打开输出文件；若没有这行代码，新输出会覆盖旧输出。
            file_handle.write(str(text))  # 新增代码+TaskOutput: 写入文本片段；若没有这行代码，任务输出不会保存。
        return path  # 新增代码+TaskOutput: 返回输出路径；若没有这行代码，registry 无法记录证据位置。

    def read_all(self, task_id: str) -> str:  # 新增代码+TaskOutput: 读取任务完整输出；若没有这行代码，task_get 无法展示完整结果。
        path = self.output_path(task_id)  # 新增代码+TaskOutput: 定位输出文件；若没有这行代码，读取路径可能和写入路径不一致。
        if not path.exists():  # 新增代码+TaskOutput: 没有输出时返回空字符串；若没有这行代码，未产出任务会报错。
            return ""  # 新增代码+TaskOutput: 返回空输出；若没有这行代码，调用方需要重复判断文件存在。
        return path.read_text(encoding="utf-8")  # 新增代码+TaskOutput: 读取 UTF-8 输出；若没有这行代码，调用方拿不到文本。

    def read_delta(self, task_id: str, offset: int) -> TaskOutputDelta:  # 新增代码+TaskOutput: 从指定 offset 读取新增输出；若没有这行代码，轮询只能反复读全量。
        path = self.output_path(task_id)  # 新增代码+TaskOutput: 定位输出文件；若没有这行代码，无法读取目标 task。
        if not path.exists():  # 新增代码+TaskOutput: 文件不存在时返回空增量；若没有这行代码，新任务轮询会报错。
            return TaskOutputDelta(text="", next_offset=0)  # 新增代码+TaskOutput: 空文件 offset 仍为 0；若没有这行代码，调用方无法继续轮询。
        text = path.read_text(encoding="utf-8")  # 新增代码+TaskOutput: 读取完整文本再按字符 offset 切片；若没有这行代码，增量计算没有数据。
        safe_offset = max(0, min(int(offset), len(text)))  # 新增代码+TaskOutput: 限制 offset 在有效范围；若没有这行代码，坏 offset 会产生异常或奇怪切片。
        return TaskOutputDelta(text=text[safe_offset:], next_offset=len(text))  # 新增代码+TaskOutput: 返回新增文本和新 offset；若没有这行代码，主 agent 无法增量消费。

    def tail(self, task_id: str, max_chars: int = 4000) -> str:  # 新增代码+TaskOutput: 读取输出尾部摘要；若没有这行代码，状态页可能被大输出撑爆。
        text = self.read_all(task_id)  # 新增代码+TaskOutput: 读取完整输出；若没有这行代码，tail 没有数据来源。
        limit = max(1, int(max_chars))  # 新增代码+TaskOutput: 限制至少读取 1 个字符；若没有这行代码，0 或负数会产生不可读摘要。
        return text[-limit:] if len(text) > limit else text  # 新增代码+TaskOutput: 返回最后 limit 个字符；若没有这行代码，tail 不会控制长度。

    def flush(self, task_id: str) -> Path:  # 新增代码+TaskOutput: 提供 flush 语义方便上层统一调用；若没有这行代码，TaskOutput 接口不完整。
        path = self.output_path(task_id)  # 新增代码+TaskOutput: 定位输出文件；若没有这行代码，flush 无法返回证据路径。
        path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+TaskOutput: 确保目录存在；若没有这行代码，空任务 flush 无法创建父目录。
        path.touch(exist_ok=True)  # 新增代码+TaskOutput: 确保文件存在；若没有这行代码，后续 tail/delta 可能找不到输出文件。
        return path  # 新增代码+TaskOutput: 返回输出路径；若没有这行代码，调用方无法记录 flush 位置。

    def evict(self, task_id: str) -> None:  # 新增代码+TaskOutput: 删除不再需要的任务输出；若没有这行代码，长任务输出会无限堆积。
        path = self.output_path(task_id)  # 新增代码+TaskOutput: 定位输出文件；若没有这行代码，无法删除目标文件。
        try:  # 新增代码+TaskOutput: 删除文件时容错；若没有这行代码，文件不存在会打断清理流程。
            path.unlink()  # 新增代码+TaskOutput: 删除输出文件；若没有这行代码，evict 不会生效。
        except FileNotFoundError:  # 新增代码+TaskOutput: 兼容已经被删除的输出；若没有这行代码，重复清理会报错。
            pass  # 新增代码+TaskOutput: 文件不存在视为已经清理；若没有这行代码，except 分支语法不完整。
