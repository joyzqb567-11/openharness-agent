"""后台命令启动、读取、停止和自动收尾逻辑。"""  # 新增代码+AgentPySplitPhase12: 说明本模块承接后台进程运行时逻辑；若没有这行代码，用户打开文件时不容易判断模块职责。

from __future__ import annotations  # 新增代码+AgentPySplitPhase12: 让类型注解延迟解析；若没有这行代码，复杂注解在部分运行方式下更容易提前求值出错。

import os  # 新增代码+AgentPySplitPhase12: 后台命令停止逻辑需要判断 Windows 与非 Windows；若没有这行代码，进程树收束无法按系统分支处理。
import queue  # 新增代码+AgentPySplitPhase12: stdout/stderr 通过线程安全队列传给 read 工具；若没有这行代码，后台输出无法非阻塞读取。
import secrets  # 新增代码+AgentPySplitPhase12: 后台命令 id 使用随机短 token；若没有这行代码，多个后台任务容易 id 冲突。
import signal  # 新增代码+AgentPySplitPhase12: Windows 下先尝试 CTRL_BREAK_EVENT 温和停止进程组；若没有这行代码，停止只能依赖强杀。
import subprocess  # 新增代码+AgentPySplitPhase12: 启动、观察和停止后台 shell 命令都需要 subprocess；若没有这行代码，后台命令工具无法运行。
import threading  # 新增代码+AgentPySplitPhase12: 后台 stdout/stderr reader 和完成监控都需要线程；若没有这行代码，主循环会被长命令阻塞。
import time  # 新增代码+AgentPySplitPhase12: 后台命令记录需要保存启动时间；若没有这行代码，状态输出缺少时间信息。
from pathlib import Path  # 新增代码+AgentPySplitPhase12: cwd 解析返回 Path；若没有这行代码，工作目录类型边界不清楚。
from typing import Any  # 新增代码+AgentPySplitPhase12: 用 Any 表示传入的 agent 上下文；若没有这行代码，新模块会为了类型注解反向导入 agent.py。

try:  # 新增代码+AgentPySplitPhase12: 包运行模式下导入后台命令数据结构和纯 helper；若没有这行代码，runtime 模块无法复用 tasks 层的记录类型。
    from learning_agent.tasks.background import BackgroundCommand, background_command_status as task_background_command_status, drain_text_queue as task_background_drain_text_queue  # 新增代码+AgentPySplitPhase12: 导入后台命令记录、状态格式化和队列读取 helper；若没有这行代码，后台运行时会重复定义数据结构。
    import learning_agent.tools.atom_tools as atom_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL6: 导入统一 workspace 路径解析；若没有这行代码，删除 旧路径包装 后后台命令 cwd 安全边界会断开。
except ModuleNotFoundError as error:  # 新增代码+AgentPySplitPhase12: 捕获脚本模式下包路径不可用；若没有这行代码，start_oauth_agent.bat 直接运行可能找不到 learning_agent 包。
    if error.name not in {"learning_agent", "learning_agent.tasks", "learning_agent.tasks.background", "learning_agent.tools", "learning_agent.tools.atom_tools"}:  # 修改代码+AgentPyCompatWrapperRemovalL6: 允许 atom_tools 在脚本模式 fallback；若没有这行代码，bat 入口会把路径差异误判为真实导入错误。
        raise  # 新增代码+AgentPySplitPhase12: 重新抛出非路径导入错误；若没有这行代码，真实导入问题会被伪装成脚本模式。
    from tasks.background import BackgroundCommand, background_command_status as task_background_command_status, drain_text_queue as task_background_drain_text_queue  # 新增代码+AgentPySplitPhase12: 脚本模式下导入后台命令 helper；若没有这行代码，bat 入口无法加载新 runtime 模块。
    import tools.atom_tools as atom_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL6: 脚本模式下导入同一个路径安全模块；若没有这行代码，start_background_command 的 cwd 校验会断开。


def start_background_command(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase12: 函数段开始，启动后台 shell 命令并登记进程；若没有这段代码，agent.py 的 _start_background_command 薄包装没有真实实现。
    command = str(arguments.get("command", "")).strip()  # 新增代码+AgentPySplitPhase12: 读取并清理 command 参数；若没有这行代码，工具不知道要执行什么命令。
    if not command:  # 新增代码+AgentPySplitPhase12: 检查 command 是否为空；若没有这行代码，可能启动空 shell 或产生难懂错误。
        return "start_background_command 失败：缺少 command 参数。"  # 新增代码+AgentPySplitPhase12: 返回清楚缺参错误；若没有这行代码，模型难以修正调用。
    cwd_result = resolve_background_cwd(agent, arguments.get("cwd"))  # 新增代码+AgentPySplitPhase12: 解析可选 cwd 并限制在工作区内；若没有这行代码，命令可能在不受控目录运行。
    if isinstance(cwd_result, str):  # 新增代码+AgentPySplitPhase12: 判断 cwd 解析是否返回错误文本；若没有这行代码，后续会把错误当路径使用。
        return cwd_result  # 新增代码+AgentPySplitPhase12: 在权限确认前返回 cwd 错误；若没有这行代码，用户会被无效操作打扰。
    label = str(arguments.get("label", "")).strip()  # 新增代码+AgentPySplitPhase12: 读取可选标签；若没有这行代码，多后台命令难以区分。
    action = f"启动后台命令：{command}\n工作目录：{cwd_result}\n标签：{label or '(无)'}"  # 新增代码+AgentPySplitPhase12: 构造启动权限说明；若没有这行代码，用户无法核对命令、目录和标签。
    if not agent.ask_permission(action):  # 新增代码+AgentPySplitPhase12: 启动命令前请求用户确认；若没有这行代码，agent 会绕过权限边界执行本机命令。
        return f"用户拒绝了操作：{action}"  # 新增代码+AgentPySplitPhase12: 权限拒绝时返回可读结果；若没有这行代码，模型不知道命令没有启动。
    command_id = f"bg_{secrets.token_hex(6)}"  # 新增代码+AgentPySplitPhase12: 生成短且唯一的后台命令 id；若没有这行代码，read/stop 无法引用此进程。
    stdout_lines: queue.Queue[str] = queue.Queue()  # 新增代码+AgentPySplitPhase12: 创建 stdout 增量队列；若没有这行代码，标准输出无法非阻塞读取。
    stderr_lines: queue.Queue[str] = queue.Queue()  # 新增代码+AgentPySplitPhase12: 创建 stderr 增量队列；若没有这行代码，错误输出会丢失或阻塞管道。
    creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0  # 新增代码+AgentPySplitPhase12: Windows 下让后台命令拥有独立进程组；若没有这行代码，CTRL_BREAK_EVENT 无法一起停止 shell 子进程。
    try:  # 新增代码+AgentPySplitPhase12: 捕获 Popen 启动异常；若没有这行代码，命令启动失败会中断整个 agent.run。
        process = subprocess.Popen(command, shell=True, cwd=str(cwd_result), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", creationflags=creation_flags)  # 新增代码+AgentPySplitPhase12: 用系统 shell 启动后台进程并创建输出管道；若没有这行代码，后台命令不会真正运行。
    except Exception as error:  # 新增代码+AgentPySplitPhase12: 处理命令不可启动、cwd 不可用等异常；若没有这行代码，用户会看到底层堆栈或 agent 崩溃。
        return f"start_background_command 失败：{error}"  # 新增代码+AgentPySplitPhase12: 返回可读启动失败原因；若没有这行代码，模型无法解释失败。
    stdout_thread = threading.Thread(target=background_stream_reader, args=(process.stdout, stdout_lines), daemon=True)  # 新增代码+AgentPySplitPhase12: 创建 stdout reader 线程并保存对象；若没有这行代码，stop 时无法等待 stdout 管道释放。
    stderr_thread = threading.Thread(target=background_stream_reader, args=(process.stderr, stderr_lines), daemon=True)  # 新增代码+AgentPySplitPhase12: 创建 stderr reader 线程并保存对象；若没有这行代码，stop 时无法等待 stderr 管道释放。
    record = BackgroundCommand(command_id=command_id, command=command, cwd=cwd_result, label=label, process=process, stdout_lines=stdout_lines, stderr_lines=stderr_lines, started_at=time.strftime("%Y-%m-%d %H:%M:%S"), stdout_thread=stdout_thread, stderr_thread=stderr_thread)  # 新增代码+AgentPySplitPhase12: 保存后台命令完整状态和 reader 线程；若没有这行代码，read/stop 无法找到进程和输出队列。
    monitor_thread = threading.Thread(target=background_completion_monitor, args=(agent, record), daemon=True)  # 新增代码+AgentPySplitPhase12: 创建后台完成监控线程；若没有这行代码，命令退出后不会自动写入 task_registry。
    record.monitor_thread = monitor_thread  # 新增代码+AgentPySplitPhase12: 把监控线程挂到记录上便于审计；若没有这行代码，状态对象看不到谁负责自动收尾。
    agent.background_commands[command_id] = record  # 新增代码+AgentPySplitPhase12: 把记录加入 agent 内存表；若没有这行代码，command_id 返回后也无法被读取或停止。
    agent.task_registry.create_task(task_id=command_id, prompt=command, kind="background_shell", status="running", background=True, metadata={"cwd": str(cwd_result), "label": label})  # 新增代码+AgentPySplitPhase12: 把后台命令登记成持久任务；若没有这行代码，后台 shell 无法被 task poller 和状态 CLI 审计。
    stdout_thread.start()  # 新增代码+AgentPySplitPhase12: 启动 stdout reader 线程；若没有这行代码，后台命令标准输出不会进入 read 工具。
    stderr_thread.start()  # 新增代码+AgentPySplitPhase12: 启动 stderr reader 线程；若没有这行代码，后台命令错误输出不会进入 read 工具。
    monitor_thread.start()  # 新增代码+AgentPySplitPhase12: 启动自动收尾监控线程；若没有这行代码，后台命令完成后仍需要模型手动 read 才能发现结果。
    return f"start_background_command 成功：command_id={command_id}\n状态：{background_command_status(agent, record)}\n工作目录：{cwd_result}"  # 新增代码+AgentPySplitPhase12: 返回 command_id 和状态给模型；若没有这行代码，模型无法继续 read/stop。
# 新增代码+AgentPySplitPhase12: 函数段结束，start_background_command 到此结束；若没有这个边界说明，用户不容易看出启动后台命令逻辑已经迁到 runtime 层。


def resolve_background_cwd(agent: Any, raw_cwd: Any) -> Path | str:  # 新增代码+AgentPySplitPhase12: 函数段开始，解析后台命令工作目录并限制在 workspace；若没有这段代码，cwd 校验逻辑会散落在启动工具中。
    cwd_text = str(raw_cwd or "").strip()  # 新增代码+AgentPySplitPhase12: 把可选 cwd 转成清理后的字符串；若没有这行代码，None 或空白 cwd 处理不稳定。
    if not cwd_text:  # 新增代码+AgentPySplitPhase12: 判断模型是否没有提供 cwd；若没有这行代码，默认工作目录不明确。
        return agent.workspace  # 新增代码+AgentPySplitPhase12: 默认使用 agent 工作区根目录；若没有这行代码，Popen 可能继承不可预期 cwd。
    cwd_path = atom_tools_from_tools.resolve_workspace_path(agent, cwd_text)  # 修改代码+AgentPyCompatWrapperRemovalL6: 直接通过 atom_tools 解析后台命令 cwd；若没有这行代码，删除 旧路径包装 后 cwd 越界保护会失效。
    if cwd_path is None:  # 新增代码+AgentPySplitPhase12: 判断 cwd 是否在工作区内；若没有这行代码，越界目录会继续执行。
        return "start_background_command 失败：cwd 必须位于 learning_agent 工作区内。"  # 新增代码+AgentPySplitPhase12: 返回边界错误；若没有这行代码，模型不知道 cwd 为什么被拒绝。
    if not cwd_path.exists():  # 新增代码+AgentPySplitPhase12: 检查 cwd 是否存在；若没有这行代码，Popen 会抛底层找不到目录异常。
        return f"start_background_command 失败：cwd 不存在：{cwd_path}"  # 新增代码+AgentPySplitPhase12: 返回不存在路径；若没有这行代码，错误信息不够友好。
    if not cwd_path.is_dir():  # 新增代码+AgentPySplitPhase12: 检查 cwd 是否是目录；若没有这行代码，Popen 会抛难懂异常。
        return f"start_background_command 失败：cwd 不是目录：{cwd_path}"  # 新增代码+AgentPySplitPhase12: 返回类型错误；若没有这行代码，模型难以修正 cwd。
    return cwd_path  # 新增代码+AgentPySplitPhase12: 返回安全目录路径；若没有这行代码，启动工具拿不到 cwd。
# 新增代码+AgentPySplitPhase12: 函数段结束，resolve_background_cwd 到此结束；若没有这个边界说明，用户不容易看出 cwd 校验逻辑已经迁到 runtime 层。


def background_stream_reader(stream: Any, output_queue: queue.Queue[str]) -> None:  # 新增代码+AgentPySplitPhase12: 函数段开始，在线程中读取进程输出并放入队列；若没有这段代码，主线程读取会阻塞 tool loop。
    if stream is None:  # 新增代码+AgentPySplitPhase12: 防御性处理没有管道的情况；若没有这行代码，None.readline 会报错。
        return  # 新增代码+AgentPySplitPhase12: 没有流时直接结束线程；若没有这行代码，后续代码无法安全执行。
    try:  # 新增代码+AgentPySplitPhase12: 捕获读取过程中流关闭或编码异常；若没有这行代码，reader 线程异常会污染测试输出。
        for line in iter(stream.readline, ""):  # 新增代码+AgentPySplitPhase12: 持续读取直到 EOF；若没有这行代码，只能拿到一行或阻塞主流程。
            output_queue.put(line)  # 新增代码+AgentPySplitPhase12: 把每行输出放入线程安全队列；若没有这行代码，read 工具拿不到输出。
    except Exception as error:  # 新增代码+AgentPySplitPhase12: 处理读取异常；若没有这行代码，输出读取失败不会留下任何线索。
        output_queue.put(f"[后台输出读取失败：{error}]\n")  # 新增代码+AgentPySplitPhase12: 把读取错误也作为输出返回；若没有这行代码，模型无法知道输出为何中断。
    finally:  # 新增代码+AgentPySplitPhase12: 读取结束后尝试关闭流；若没有这行代码，管道句柄可能延迟释放。
        try:  # 新增代码+AgentPySplitPhase12: 捕获关闭流异常；若没有这行代码，close 失败会在线程里抛出。
            stream.close()  # 新增代码+AgentPySplitPhase12: 关闭已读完的输出流；若没有这行代码，子进程结束后句柄可能残留。
        except Exception:  # 新增代码+AgentPySplitPhase12: 忽略关闭异常；若没有这行代码，清理失败会制造无意义报错。
            pass  # 新增代码+AgentPySplitPhase12: 保持 reader 线程静默结束；若没有这行代码，except 块语法不完整。
# 新增代码+AgentPySplitPhase12: 函数段结束，background_stream_reader 到此结束；若没有这个边界说明，用户不容易看出输出读取逻辑已经迁到 runtime 层。


def background_completion_monitor(agent: Any, record: BackgroundCommand) -> None:  # 新增代码+AgentPySplitPhase12: 函数段开始，等待后台命令结束并自动写入持久任务状态；若没有这段代码，长任务完成不会主动回灌给主 agent。
    try:  # 新增代码+AgentPySplitPhase12: 捕获监控线程里的所有异常；若没有这行代码，失败时任务会永远卡在 running。
        record.process.wait()  # 新增代码+AgentPySplitPhase12: 等待真实后台进程退出；若没有这行代码，监控线程无法知道什么时候该收尾。
        join_background_reader_threads(agent, record, 1.0)  # 新增代码+AgentPySplitPhase12: 给 stdout/stderr reader 时间读完 EOF；若没有这行代码，最后几行输出可能还没进入队列。
        close_background_process_streams(agent, record.process)  # 新增代码+AgentPySplitPhase12: 关闭已结束进程的管道句柄；若没有这行代码，Windows 上句柄可能延迟释放。
        join_background_reader_threads(agent, record, 0.5)  # 新增代码+AgentPySplitPhase12: 关闭管道后再等一次 reader 收尾；若没有这行代码，输出队列可能还缺尾部内容。
        finalize_background_command_record(agent, record)  # 新增代码+AgentPySplitPhase12: 把退出码、输出和通知统一写入持久层；若没有这行代码，等待结束不会产生可审计结果。
    except Exception as error:  # 新增代码+AgentPySplitPhase12: 处理自动监控自身失败；若没有这行代码，监控异常会导致任务状态无人收束。
        try:  # 新增代码+AgentPySplitPhase12: 尝试读取当前持久任务状态；若没有这行代码，未知任务会让异常处理再次崩溃。
            current_record = agent.task_registry.get_task(record.command_id)  # 新增代码+AgentPySplitPhase12: 获取任务当前状态以避免覆盖已收束结果；若没有这行代码，可能把 stopped/completed 覆盖成 failed。
        except KeyError:  # 新增代码+AgentPySplitPhase12: 任务记录不存在时放弃监控失败写入；若没有这行代码，删除或创建失败的记录会导致线程报错。
            return  # 新增代码+AgentPySplitPhase12: 没有持久记录就安全退出；若没有这行代码，异常处理会继续访问不存在的任务。
        if current_record.status == "running" and not record.stop_requested:  # 新增代码+AgentPySplitPhase12: 只在任务仍运行且不是用户主动停止时写失败；若没有这行代码，正常 stop 可能被误报失败。
            agent.task_registry.fail_task(record.command_id, f"后台命令自动监控失败：{error}")  # 新增代码+AgentPySplitPhase12: 把监控异常变成可见失败通知；若没有这行代码，状态 CLI/API 看不到卡住原因。
# 新增代码+AgentPySplitPhase12: 函数段结束，background_completion_monitor 到此结束；若没有这个边界说明，用户不容易看出自动收尾逻辑已经迁到 runtime 层。


def finalize_background_command_record(agent: Any, record: BackgroundCommand) -> None:  # 新增代码+AgentPySplitPhase12: 函数段开始，根据后台命令最终状态更新 task_registry；若没有这段代码，read 和监控会各自写一套收尾逻辑。
    if record.stop_requested:  # 新增代码+AgentPySplitPhase12: 判断 stop_background_command 是否已经接管收尾；若没有这行代码，自动监控会和用户停止流程抢写状态。
        return  # 新增代码+AgentPySplitPhase12: 主动停止的任务交给 stop 工具写 stopped；若没有这行代码，用户停止可能被覆盖成 failed/completed。
    try:  # 新增代码+AgentPySplitPhase12: 尝试读取持久任务记录；若没有这行代码，任务不存在时会抛异常中断监控线程。
        current_record = agent.task_registry.get_task(record.command_id)  # 新增代码+AgentPySplitPhase12: 读取当前状态用于幂等判断；若没有这行代码，已完成任务可能重复通知。
    except KeyError:  # 新增代码+AgentPySplitPhase12: 持久任务不存在时安全退出；若没有这行代码，异常会让后台监控失败。
        return  # 新增代码+AgentPySplitPhase12: 没有记录时不做任何写入；若没有这行代码，后续状态更新没有目标。
    if current_record.status != "running":  # 新增代码+AgentPySplitPhase12: 只有 running 任务才允许自动收尾；若没有这行代码，stop/read 已收束的任务会被重复覆盖。
        return  # 新增代码+AgentPySplitPhase12: 已经是终态或等待输入时保持原状态；若没有这行代码，状态历史可能被改坏。
    return_code = record.process.poll()  # 新增代码+AgentPySplitPhase12: 读取进程退出码；若没有这行代码，无法区分成功完成和失败退出。
    if return_code is None:  # 新增代码+AgentPySplitPhase12: 判断进程是否其实还没退出；若没有这行代码，可能把运行中的命令提前完成。
        return  # 新增代码+AgentPySplitPhase12: 运行中的命令不收尾；若没有这行代码，后台任务状态会被提前写错。
    stdout_text = drain_text_queue(agent, record.stdout_lines, 20000)  # 新增代码+AgentPySplitPhase12: 自动收集剩余 stdout 输出；若没有这行代码，完成通知缺少命令结果。
    stderr_text = drain_text_queue(agent, record.stderr_lines, 20000)  # 新增代码+AgentPySplitPhase12: 自动收集剩余 stderr 输出；若没有这行代码，失败命令缺少错误上下文。
    combined_output = "\n".join(part for part in [stdout_text, stderr_text] if part)  # 新增代码+AgentPySplitPhase12: 合并两路输出准备落盘；若没有这行代码，任务摘要无法统一展示结果。
    if combined_output:  # 新增代码+AgentPySplitPhase12: 只有有新输出时才追加到输出文件；若没有这行代码，空命令会产生噪声记录。
        agent.task_registry.append_output(record.command_id, combined_output + "\n")  # 新增代码+AgentPySplitPhase12: 把最后输出写入 durable task output；若没有这行代码，重启后无法复查后台命令结果。
    if return_code == 0:  # 新增代码+AgentPySplitPhase12: 退出码 0 表示后台命令成功；若没有这行代码，成功命令无法和失败命令区分。
        agent.task_registry.complete_task(record.command_id, output="", usage={})  # 新增代码+AgentPySplitPhase12: 标记任务完成并生成 task_notification；若没有这行代码，下一轮模型不会自动收到完成结果。
    else:  # 新增代码+AgentPySplitPhase12: 非 0 退出码进入失败路径；若没有这行代码，失败命令可能被误报成功。
        agent.task_registry.fail_task(record.command_id, f"后台命令退出码：{return_code}")  # 新增代码+AgentPySplitPhase12: 标记任务失败并生成通知；若没有这行代码，失败状态不会自动回灌模型。
# 新增代码+AgentPySplitPhase12: 函数段结束，finalize_background_command_record 到此结束；若没有这个边界说明，用户不容易看出后台命令收尾逻辑已经迁到 runtime 层。


def read_background_command(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase12: 函数段开始，读取后台命令增量输出；若没有这段代码，agent.py 的 _read_background_command 薄包装没有真实实现。
    command_id = str(arguments.get("command_id", "")).strip()  # 新增代码+AgentPySplitPhase12: 读取要观察的 command_id；若没有这行代码，工具不知道读取哪个后台命令。
    if not command_id:  # 新增代码+AgentPySplitPhase12: 检查 command_id 是否为空；若没有这行代码，空 id 会变成未知命令错误。
        return "read_background_command 失败：缺少 command_id 参数。"  # 新增代码+AgentPySplitPhase12: 返回缺参提示；若没有这行代码，模型难以修正调用。
    record = agent.background_commands.get(command_id)  # 新增代码+AgentPySplitPhase12: 从内存表中查找后台命令；若没有这行代码，无法定位进程和输出队列。
    if record is None:  # 新增代码+AgentPySplitPhase12: 判断 id 是否不存在；若没有这行代码，后续访问 None 会报错。
        return f"read_background_command 失败：未知 command_id：{command_id}"  # 新增代码+AgentPySplitPhase12: 返回未知 id 错误；若没有这行代码，模型不知道需要重新启动或改 id。
    max_chars = parse_max_chars(agent, arguments.get("max_chars"))  # 新增代码+AgentPySplitPhase12: 解析可选最大输出字符数；若没有这行代码，长输出可能不受控。
    stdout_text = drain_text_queue(agent, record.stdout_lines, max_chars)  # 新增代码+AgentPySplitPhase12: 读取 stdout 队列里的增量文本；若没有这行代码，标准输出不会返回给模型。
    stderr_text = drain_text_queue(agent, record.stderr_lines, max_chars)  # 新增代码+AgentPySplitPhase12: 读取 stderr 队列里的增量文本；若没有这行代码，错误输出不会返回给模型。
    combined_output = "\n".join(part for part in [stdout_text, stderr_text] if part)  # 新增代码+AgentPySplitPhase12: 合并本次读取到的 stdout/stderr；若没有这行代码，后台输出无法写入统一 task output 文件。
    if combined_output:  # 新增代码+AgentPySplitPhase12: 只有有新增输出时才追加文件；若没有这行代码，空读取会制造无意义输出记录。
        agent.task_registry.append_output(command_id, combined_output + "\n")  # 新增代码+AgentPySplitPhase12: 把后台命令增量输出写入 task output；若没有这行代码，poller/status 看不到后台输出。
    if record.process.poll() is not None:  # 新增代码+AgentPySplitPhase12: 判断后台命令是否已经退出；若没有这行代码，持久任务会一直显示 running。
        final_tail = agent.task_registry.output_store.tail(command_id, max_chars=4000)  # 新增代码+AgentPySplitPhase12: 读取最终输出尾部摘要；若没有这行代码，完成通知缺少结果上下文。
        if record.process.returncode == 0:  # 新增代码+AgentPySplitPhase12: 退出码 0 视为完成；若没有这行代码，成功命令也会被误判失败。
            agent.task_registry.complete_task(command_id, output=final_tail, usage={})  # 新增代码+AgentPySplitPhase12: 持久标记后台命令完成并通知；若没有这行代码，后台命令结束不会自动回灌。
        else:  # 新增代码+AgentPySplitPhase12: 非 0 退出码视为失败；若没有这行代码，失败命令会误显示完成。
            agent.task_registry.fail_task(command_id, f"后台命令退出码：{record.process.returncode}")  # 新增代码+AgentPySplitPhase12: 持久标记后台命令失败并通知；若没有这行代码，失败状态无法审计。
    return f"read_background_command 成功：command_id={command_id}\n状态：{background_command_status(agent, record)}\nstdout:\n{stdout_text or '(无新增输出)'}\nstderr:\n{stderr_text or '(无新增输出)'}"  # 新增代码+AgentPySplitPhase12: 返回状态和增量输出；若没有这行代码，模型无法根据命令结果继续推理。
# 新增代码+AgentPySplitPhase12: 函数段结束，read_background_command 到此结束；若没有这个边界说明，用户不容易看出后台读取逻辑已经迁到 runtime 层。


def stop_background_command(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase12: 函数段开始，停止后台命令并返回最终增量输出；若没有这段代码，agent.py 的 _stop_background_command 薄包装没有真实实现。
    command_id = str(arguments.get("command_id", "")).strip()  # 新增代码+AgentPySplitPhase12: 读取要停止的 command_id；若没有这行代码，工具不知道停止哪个进程。
    if not command_id:  # 新增代码+AgentPySplitPhase12: 检查 command_id 是否为空；若没有这行代码，空 id 会变成未知命令错误。
        return "stop_background_command 失败：缺少 command_id 参数。"  # 新增代码+AgentPySplitPhase12: 返回缺参提示；若没有这行代码，模型难以修正调用。
    record = agent.background_commands.get(command_id)  # 新增代码+AgentPySplitPhase12: 查找目标后台命令记录；若没有这行代码，无法访问进程对象。
    if record is None:  # 新增代码+AgentPySplitPhase12: 判断 id 是否不存在；若没有这行代码，后续访问 None 会报错。
        return f"stop_background_command 失败：未知 command_id：{command_id}"  # 新增代码+AgentPySplitPhase12: 返回未知 id 错误；若没有这行代码，模型不知道该检查 id。
    action = f"停止后台命令：{command_id}\n命令：{record.command}\n工作目录：{record.cwd}"  # 新增代码+AgentPySplitPhase12: 构造停止权限说明；若没有这行代码，用户无法确认要停止哪个命令。
    if not agent.ask_permission(action):  # 新增代码+AgentPySplitPhase12: 停止进程前请求用户确认；若没有这行代码，agent 可能擅自停止用户关心的进程。
        return f"用户拒绝了操作：{action}"  # 新增代码+AgentPySplitPhase12: 权限拒绝时返回可读结果；若没有这行代码，模型不知道进程仍在运行。
    record.stop_requested = True  # 新增代码+AgentPySplitPhase12: 标记用户停止流程已经接管该命令；若没有这行代码，监控线程可能把 stop 误判成异常失败。
    if record.process.poll() is None:  # 新增代码+AgentPySplitPhase12: 判断进程是否仍在运行；若没有这行代码，已退出进程也会重复 terminate。
        terminate_background_process(agent, record.process)  # 新增代码+AgentPySplitPhase12: 停止整个后台进程树；若没有这行代码，Windows shell 子进程可能继续占用工作目录。
    join_background_reader_threads(agent, record, 0.5)  # 新增代码+AgentPySplitPhase12: 先给 reader 线程短暂时间自然读到 EOF；若没有这行代码，刚结束的进程输出可能还没进入队列。
    close_background_process_streams(agent, record.process)  # 新增代码+AgentPySplitPhase12: 主动关闭后台进程管道句柄；若没有这行代码，Windows 可能延迟释放和临时目录相关的子进程资源。
    join_background_reader_threads(agent, record, 1.0)  # 新增代码+AgentPySplitPhase12: 关闭管道后再次等待 reader 线程退出；若没有这行代码，测试清理临时目录时仍可能遇到句柄占用。
    stdout_text = drain_text_queue(agent, record.stdout_lines, 4000)  # 新增代码+AgentPySplitPhase12: 停止后读取剩余 stdout；若没有这行代码，最后一段输出会丢失。
    stderr_text = drain_text_queue(agent, record.stderr_lines, 4000)  # 新增代码+AgentPySplitPhase12: 停止后读取剩余 stderr；若没有这行代码，最后一段错误输出会丢失。
    combined_output = "\n".join(part for part in [stdout_text, stderr_text] if part)  # 新增代码+AgentPySplitPhase12: 合并停止时剩余输出；若没有这行代码，后台命令最后一段输出无法落盘。
    if combined_output:  # 新增代码+AgentPySplitPhase12: 有剩余输出时才追加；若没有这行代码，空停止会生成噪音记录。
        agent.task_registry.append_output(command_id, combined_output + "\n")  # 新增代码+AgentPySplitPhase12: 保存停止前最后输出；若没有这行代码，task output 会缺尾部证据。
    agent.task_registry.stop_task(command_id, "后台命令已被 stop_background_command 停止。")  # 新增代码+AgentPySplitPhase12: 把后台命令停止状态写入持久任务表；若没有这行代码，状态 CLI 仍会显示 running。
    return f"stop_background_command 成功：command_id={command_id}\n状态：{background_command_status(agent, record)}\nstdout:\n{stdout_text or '(无新增输出)'}\nstderr:\n{stderr_text or '(无新增输出)'}"  # 新增代码+AgentPySplitPhase12: 返回停止结果和最终输出；若没有这行代码，模型无法确认进程已收束。
# 新增代码+AgentPySplitPhase12: 函数段结束，stop_background_command 到此结束；若没有这个边界说明，用户不容易看出停止后台命令逻辑已经迁到 runtime 层。


def terminate_background_process(agent: Any, process: subprocess.Popen[str]) -> None:  # 新增代码+AgentPySplitPhase12: 函数段开始，终止后台进程及其子进程；若没有这段代码，shell 启动的子进程可能残留。
    del agent  # 新增代码+AgentPySplitPhase12: 当前终止逻辑只需要 process 但保留统一签名；若没有这行代码，读者会误以为遗漏 agent 上下文。
    if os.name == "nt":  # 新增代码+AgentPySplitPhase12: Windows 需要按进程树终止 shell 子进程；若没有这行代码，cmd/powershell 子进程可能继续运行。
        try:  # 新增代码+AgentPySplitPhase12: 先向独立进程组发送 Ctrl+Break；若没有这行代码，taskkill 被拒绝时只能杀外层 shell。
            process.send_signal(signal.CTRL_BREAK_EVENT)  # 新增代码+AgentPySplitPhase12: 请求 shell 和子进程一起退出；若没有这行代码，Python 子进程可能继续占用临时工作目录。
            process.wait(timeout=3)  # 新增代码+AgentPySplitPhase12: 等待 Ctrl+Break 生效；若没有这行代码，stop 可能在子进程退出前过早继续。
            return  # 新增代码+AgentPySplitPhase12: Ctrl+Break 成功后直接返回；若没有这行代码，还会继续走更强制的 taskkill 分支。
        except (OSError, ValueError, subprocess.TimeoutExpired):  # 新增代码+AgentPySplitPhase12: 处理进程已退出、信号不可用或等待超时；若没有这行代码，温和终止失败会让 stop 工具报错。
            pass  # 新增代码+AgentPySplitPhase12: 温和终止失败后继续使用后备强制路径；若没有这行代码，except 分支语法不完整。
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")  # 新增代码+AgentPySplitPhase12: 调用 taskkill 强制结束进程树；若没有这行代码，Windows 临时目录可能被子进程长期占用。
        try:  # 新增代码+AgentPySplitPhase12: 等待 Popen 记录的外层进程退出；若没有这行代码，进程句柄可能未回收。
            process.wait(timeout=3)  # 新增代码+AgentPySplitPhase12: 给系统最多 3 秒回收进程；若没有这行代码，stop 工具可能过早返回。
        except subprocess.TimeoutExpired:  # 新增代码+AgentPySplitPhase12: 如果 taskkill 后外层进程仍未退出；若没有这行代码，极端情况下会抛异常中断 stop。
            process.kill()  # 新增代码+AgentPySplitPhase12: 对外层进程再执行一次 kill；若没有这行代码，进程句柄可能继续存在。
            process.wait(timeout=3)  # 新增代码+AgentPySplitPhase12: 回收被 kill 的外层进程；若没有这行代码，可能留下句柄。
        return  # 新增代码+AgentPySplitPhase12: Windows 分支处理完成后返回；若没有这行代码，还会继续执行通用 terminate 分支。
    process.terminate()  # 新增代码+AgentPySplitPhase12: 非 Windows 平台先温和请求进程退出；若没有这行代码，长任务可能继续运行。
    try:  # 新增代码+AgentPySplitPhase12: 等待进程正常退出；若没有这行代码，terminate 后可能没有回收进程。
        process.wait(timeout=3)  # 新增代码+AgentPySplitPhase12: 给进程最多 3 秒退出；若没有这行代码，stop 工具可能无限等待。
    except subprocess.TimeoutExpired:  # 新增代码+AgentPySplitPhase12: 如果进程没有及时响应 terminate；若没有这行代码，不响应进程会卡住工具。
        process.kill()  # 新增代码+AgentPySplitPhase12: 强制结束不响应的后台进程；若没有这行代码，进程可能残留。
        process.wait(timeout=3)  # 新增代码+AgentPySplitPhase12: 回收被 kill 的进程；若没有这行代码，可能留下僵尸或句柄。
# 新增代码+AgentPySplitPhase12: 函数段结束，terminate_background_process 到此结束；若没有这个边界说明，用户不容易看出进程树停止逻辑已经迁到 runtime 层。


def close_background_process_streams(agent: Any, process: subprocess.Popen[str]) -> None:  # 新增代码+AgentPySplitPhase12: 函数段开始，关闭后台进程 stdio 管道；若没有这段代码，停止命令后 reader 线程和系统句柄可能延迟释放。
    del agent  # 新增代码+AgentPySplitPhase12: 当前关闭流逻辑只需要 process 但保留统一签名；若没有这行代码，读者会误以为遗漏 agent 上下文。
    for stream in (process.stdin, process.stdout, process.stderr):  # 新增代码+AgentPySplitPhase12: 遍历标准输入、输出和错误三个可能存在的管道；若没有这行代码，清理逻辑会遗漏某类管道。
        if stream is None or stream.closed:  # 新增代码+AgentPySplitPhase12: 跳过不存在或已经关闭的管道；若没有这行代码，重复关闭会增加无意义异常。
            continue  # 新增代码+AgentPySplitPhase12: 当前管道无需处理时进入下一个；若没有这行代码，后续 close 会作用在空对象上。
        try:  # 新增代码+AgentPySplitPhase12: 捕获关闭管道时的系统异常；若没有这行代码，单个管道关闭失败会中断 stop 工具。
            stream.close()  # 新增代码+AgentPySplitPhase12: 释放管道句柄；若没有这行代码，Windows 可能认为后台命令资源仍被占用。
        except Exception:  # 新增代码+AgentPySplitPhase12: 忽略关闭期间的低层异常；若没有这行代码，已结束进程的管道清理可能把 stop 变成失败。
            pass  # 新增代码+AgentPySplitPhase12: 保持清理过程尽力而为；若没有这行代码，except 分支语法不完整。
# 新增代码+AgentPySplitPhase12: 函数段结束，close_background_process_streams 到此结束；若没有这个边界说明，用户不容易看出管道清理逻辑已经迁到 runtime 层。


def join_background_reader_threads(agent: Any, record: BackgroundCommand, timeout_seconds: float) -> None:  # 新增代码+AgentPySplitPhase12: 函数段开始，等待后台输出 reader 线程收尾；若没有这段代码，stop 返回时线程可能仍在读取管道。
    del agent  # 新增代码+AgentPySplitPhase12: 当前 join 逻辑只需要 record 但保留统一签名；若没有这行代码，读者会误以为遗漏 agent 上下文。
    for reader_thread in (record.stdout_thread, record.stderr_thread):  # 新增代码+AgentPySplitPhase12: 同时处理 stdout 和 stderr reader；若没有这行代码，只清理一个方向的输出仍可能泄漏。
        if reader_thread is None:  # 新增代码+AgentPySplitPhase12: 兼容旧记录或启动失败时没有线程对象的情况；若没有这行代码，None 会触发属性错误。
            continue  # 新增代码+AgentPySplitPhase12: 没有线程就进入下一个；若没有这行代码，清理逻辑无法兼容空线程。
        if not reader_thread.is_alive():  # 新增代码+AgentPySplitPhase12: 已退出线程不需要等待；若没有这行代码，stop 会做多余 join。
            continue  # 新增代码+AgentPySplitPhase12: 跳过已结束线程；若没有这行代码，清理等待会增加不必要耗时。
        reader_thread.join(timeout=timeout_seconds)  # 新增代码+AgentPySplitPhase12: 等待线程在限定时间内退出；若没有这行代码，stop 工具可能在 Windows 上过早返回导致临时目录无法删除。
# 新增代码+AgentPySplitPhase12: 函数段结束，join_background_reader_threads 到此结束；若没有这个边界说明，用户不容易看出线程收尾逻辑已经迁到 runtime 层。


def parse_max_chars_value(raw_value: Any) -> int:  # 新增代码+AgentPySplitPhase15B2: 函数段开始，提供不依赖 agent 对象的输出长度解析；若没有这段代码，MCP、tasks、Notebook 和 REPL 仍要反向调用 agent.py 的薄包装。
    try:  # 新增代码+AgentPySplitPhase12: 捕获无法转成整数的输入；若没有这行代码，模型传错 max_chars 会让工具崩溃。
        value = int(raw_value) if raw_value is not None else 4000  # 新增代码+AgentPySplitPhase12: None 时使用默认 4000；若没有这行代码，未传 max_chars 时无法确定截断长度。
    except (TypeError, ValueError):  # 新增代码+AgentPySplitPhase12: 处理非数字输入；若没有这行代码，ValueError 会中断 agent.run。
        value = 4000  # 新增代码+AgentPySplitPhase12: 错误输入回退默认值；若没有这行代码，模型一次小错会导致工具失败。
    return max(200, min(value, 20000))  # 新增代码+AgentPySplitPhase12: 限制输出长度范围；若没有这行代码，过小或过大值会影响可读性或上下文安全。
# 新增代码+AgentPySplitPhase15B2: 函数段结束，parse_max_chars_value 到此结束；若没有这个边界说明，用户不容易看出共享解析函数已经脱离 agent.py。


def parse_max_chars(agent: Any, raw_value: Any) -> int:  # 新增代码+AgentPySplitPhase12: 函数段开始，解析 read_background_command 的 max_chars；若没有这段代码，输出长度控制会散落在读取逻辑中。
    del agent  # 新增代码+AgentPySplitPhase12: 当前解析逻辑不需要 agent 但保留统一签名；若没有这行代码，读者会误以为遗漏上下文。
    return parse_max_chars_value(raw_value)  # 修改代码+AgentPySplitPhase15B2: 兼容旧调用签名并复用无 agent 版本；若没有这行代码，后台命令旧入口和新公共入口会出现两套解析规则。
# 新增代码+AgentPySplitPhase12: 函数段结束，parse_max_chars 到此结束；若没有这个边界说明，用户不容易看出输出长度解析逻辑已经迁到 runtime 层。


def drain_text_queue(agent: Any, output_queue: queue.Queue[str], max_chars: int) -> str:  # 新增代码+AgentPySplitPhase12: 函数段开始，非阻塞读取队列中的增量文本；若没有这段代码，read/stop 无法复用输出读取逻辑。
    del agent  # 新增代码+AgentPySplitPhase12: 当前队列读取委托不需要 agent 但保留统一签名；若没有这行代码，读者会误以为遗漏上下文。
    return task_background_drain_text_queue(output_queue, max_chars)  # 新增代码+AgentPySplitPhase12: 委托 tasks.background 读取后台输出队列；若没有这行代码，后台输出截断规则会重复实现。
# 新增代码+AgentPySplitPhase12: 函数段结束，drain_text_queue 到此结束；若没有这个边界说明，用户不容易看出队列读取 helper 已经迁到 runtime 层。


def background_command_status(agent: Any, record: BackgroundCommand) -> str:  # 新增代码+AgentPySplitPhase12: 函数段开始，格式化后台命令状态；若没有这段代码，read/stop/start 的状态格式会在主流程里散落。
    del agent  # 新增代码+AgentPySplitPhase12: 当前状态格式化不需要 agent 但保留统一签名；若没有这行代码，读者会误以为遗漏上下文。
    return task_background_command_status(record)  # 新增代码+AgentPySplitPhase12: 委托 tasks.background 统一格式化后台进程状态；若没有这行代码，后台命令状态规则会重新堆回 core.agent。
# 新增代码+AgentPySplitPhase12: 函数段结束，background_command_status 到此结束；若没有这个边界说明，用户不容易看出状态格式化 helper 已经迁到 runtime 层。
