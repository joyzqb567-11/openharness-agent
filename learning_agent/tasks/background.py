"""后台命令任务记录和轻量 helper。"""  # 新增代码+TasksSplit: 说明本模块承载后台命令相关的纯数据和 helper；如果没有这行代码，读文件时不容易判断模块职责。

from __future__ import annotations  # 新增代码+TasksSplit: 允许类型注解延迟解析；如果没有这行代码，某些前向类型在低版本解释器上更容易出问题。

import queue  # 新增代码+TasksSplit: 后台输出队列 helper 需要识别 queue.Empty；如果没有这行代码，非阻塞读取空队列时无法安全结束。
import subprocess  # 新增代码+TasksSplit: BackgroundCommand 需要标注真实子进程对象类型；如果没有这行代码，类型边界会退回不清楚的 Any。
import threading  # 新增代码+TasksSplit: BackgroundCommand 保存 reader 线程对象；如果没有这行代码，后台命令停止时无法表达线程字段。
from dataclasses import dataclass  # 新增代码+TasksSplit: 用 dataclass 定义只保存状态的数据对象；如果没有这行代码，记录类需要手写初始化方法。
from pathlib import Path  # 新增代码+TasksSplit: BackgroundCommand.cwd 使用 Path 表达工作目录；如果没有这行代码，路径字段只能退化为普通字符串。


@dataclass  # 新增代码+TasksSplit: 自动生成后台命令记录初始化方法；如果没有这行代码，创建记录时要手写样板代码。
class BackgroundCommand:  # 新增代码+TasksSplit: 保存一个后台命令的进程、输出队列和元数据；如果没有这行代码，read/stop 无法稳定找到目标进程。
    command_id: str  # 新增代码+TasksSplit: 保存后台命令唯一 id；如果没有这行代码，模型无法引用具体后台任务。
    command: str  # 新增代码+TasksSplit: 保存原始命令字符串；如果没有这行代码，权限提示和调试输出缺少命令内容。
    cwd: Path  # 新增代码+TasksSplit: 保存命令工作目录；如果没有这行代码，用户无法确认命令在哪个目录运行。
    label: str  # 新增代码+TasksSplit: 保存用户或模型提供的可读标签；如果没有这行代码，多后台任务更难区分。
    process: subprocess.Popen[str]  # 新增代码+TasksSplit: 保存真实子进程对象；如果没有这行代码，read/stop 无法检查状态或停止进程。
    stdout_lines: queue.Queue[str]  # 新增代码+TasksSplit: 保存 stdout 增量输出队列；如果没有这行代码，读取工具无法非阻塞拿到标准输出。
    stderr_lines: queue.Queue[str]  # 新增代码+TasksSplit: 保存 stderr 增量输出队列；如果没有这行代码，错误输出会丢失或阻塞管道。
    started_at: str  # 新增代码+TasksSplit: 保存启动时间文本；如果没有这行代码，用户难以判断后台任务运行了多久。
    stdout_thread: threading.Thread | None = None  # 新增代码+TasksSplit: 保存 stdout reader 线程便于停止时等待收尾；如果没有这行代码，Windows 临时目录可能在 reader 线程未结束时仍被占用。
    stderr_thread: threading.Thread | None = None  # 新增代码+TasksSplit: 保存 stderr reader 线程便于停止时等待收尾；如果没有这行代码，错误输出管道可能延迟释放导致测试清理失败。
    monitor_thread: threading.Thread | None = None  # 新增代码+BackgroundAutoNotify: 保存自动收尾监控线程对象；若没有这行代码，后台命令结束只能靠模型手动 read 才会写入持久状态。
    stop_requested: bool = False  # 新增代码+BackgroundAutoNotify: 记录 stop_background_command 是否已经接管停止流程；若没有这行代码，自动监控可能把用户主动停止误报成失败或完成。


def drain_text_queue(output_queue: queue.Queue[str], max_chars: int) -> str:  # 新增代码+TasksSplit: 非阻塞读取队列中的增量文本；如果没有这行代码，后台 read/stop 输出读取逻辑会继续留在主文件里。
    chunks: list[str] = []  # 新增代码+TasksSplit: 准备保存多行输出片段；如果没有这行代码，无法累积队列内容。
    total_chars = 0  # 新增代码+TasksSplit: 记录当前已收集字符数；如果没有这行代码，无法按 max_chars 截断。
    while total_chars < max_chars:  # 新增代码+TasksSplit: 在长度限制内持续取队列内容；如果没有这行代码，可能一次只读一行或无限读取。
        try:  # 新增代码+TasksSplit: get_nowait 可能在队列为空时抛 Empty；如果没有这行代码，空队列会中断为异常。
            chunk = output_queue.get_nowait()  # 新增代码+TasksSplit: 非阻塞获取一段输出；如果没有这行代码，read 工具可能卡住等待新输出。
        except queue.Empty:  # 新增代码+TasksSplit: 队列已无新增输出；如果没有这行代码，空队列无法正常结束读取。
            break  # 新增代码+TasksSplit: 停止读取并返回已收集内容；如果没有这行代码，while 循环会继续空转。
        remaining = max_chars - total_chars  # 新增代码+TasksSplit: 计算还可返回多少字符；如果没有这行代码，无法精确截断当前片段。
        chunks.append(chunk[:remaining])  # 新增代码+TasksSplit: 追加不超过剩余长度的文本；如果没有这行代码，输出片段不会进入返回值。
        total_chars += len(chunks[-1])  # 新增代码+TasksSplit: 更新已收集字符数；如果没有这行代码，长度限制不会推进。
        if len(chunk) > remaining:  # 新增代码+TasksSplit: 如果当前片段被截断；如果没有这行代码，用户看不到截断提示。
            chunks.append("\n...[后台输出过长，已截断]...")  # 新增代码+TasksSplit: 加入截断提示；如果没有这行代码，模型可能误以为输出完整。
            break  # 新增代码+TasksSplit: 截断后停止读取；如果没有这行代码，仍可能继续超过限制。
    return "".join(chunks).strip()  # 新增代码+TasksSplit: 合并输出并去掉首尾空白；如果没有这行代码，调用方拿不到可读文本。


def background_command_status(record: BackgroundCommand) -> str:  # 新增代码+TasksSplit: 统一把进程状态转成人类可读文本；如果没有这行代码，read/start/stop 状态格式容易不一致。
    return_code = record.process.poll()  # 新增代码+TasksSplit: 查询进程是否已经退出；如果没有这行代码，无法区分 running 和 exited。
    if return_code is None:  # 新增代码+TasksSplit: poll 返回 None 表示仍在运行；如果没有这行代码，运行中状态会被误判。
        return "running"  # 新增代码+TasksSplit: 返回运行中状态；如果没有这行代码，用户看不懂 None 的含义。
    return f"exited({return_code})"  # 新增代码+TasksSplit: 返回退出码状态；如果没有这行代码，命令失败或被终止的状态不清楚。
