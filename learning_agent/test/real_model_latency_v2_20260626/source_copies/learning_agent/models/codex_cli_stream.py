from __future__ import annotations  # 新增代码+CodexCliStreaming：启用延迟类型注解；如果没有这一行，Windows 上部分类型引用会更容易受定义顺序影响。

import io  # 新增代码+CodexCliStreaming：导入文本流基类用于类型判断；如果没有这一行，runner 无法温和兼容 fake process 的 StringIO。
import json  # 新增代码+CodexCliStreaming：导入 JSON 解析工具；如果没有这一行，stdout JSONL delta 和最终输出 fallback 都无法解析。
import queue  # 新增代码+CodexCliStreaming：导入线程安全队列；如果没有这一行，stdout/stderr 后台读取结果无法安全交给主生成器。
import subprocess  # 新增代码+CodexCliStreaming：导入子进程 API 和 TimeoutExpired；如果没有这一行，runner 无法启动或取消 Codex CLI。
import sys  # 新增代码+CodexCliStreaming：导入平台判断；如果没有这一行，Windows 下无法安全设置 CREATE_NEW_PROCESS_GROUP。
import threading  # 新增代码+CodexCliStreaming：导入线程工具；如果没有这一行，stdout/stderr 读取会阻塞主事件流。
import time  # 新增代码+CodexCliStreaming：导入单调时钟和时间戳；如果没有这一行，模型阶段耗时无法进入 GUI 诊断。
from pathlib import Path  # 新增代码+CodexCliStreaming：导入路径对象；如果没有这一行，输出文件和工作目录处理会退回脆弱字符串。
from typing import Any, Callable, Iterable  # 新增代码+CodexCliStreaming：导入通用类型、回调和迭代器；如果没有这一行，runner 契约会不清晰。

from learning_agent.models.streaming import ModelStreamEvent  # 新增代码+CodexCliStreaming：复用统一模型流事件；如果没有这一行，GUI adapter 无法识别 CLI 阶段。


CodexProcessFactory = Callable[[list[str], Path], Any]  # 新增代码+CodexCliStreaming：定义可注入子进程工厂；如果没有这一行，测试只能启动真实 codex。
CodexOutputParser = Callable[[str], Any]  # 新增代码+CodexCliStreaming：定义最终输出解析函数；如果没有这一行，runner 不能复用 adapters.py 的 ModelMessage 解析器。
CodexCancelChecker = Callable[[], bool]  # 新增代码+CodexCliCancelBridge：定义外部取消检查回调；如果没有这一行，GUI 点击取消无法传到 Codex CLI runner。


class CodexCliProcessController:  # 新增代码+CodexCliStreaming：类段开始，集中管理 Codex CLI 子进程取消；如果没有这段，停止按钮只会改 UI 而不能停掉进程。
    def __init__(self, process: Any, *, turn_id: str, provider_id: str, model_id: str, cancel_timeout_seconds: float = 3.0) -> None:  # 新增代码+CodexCliStreaming：函数段开始，绑定进程和模型上下文；如果没有这段，取消事件无法归属到当前 turn。
        self.process = process  # 新增代码+CodexCliStreaming：保存真实或测试进程对象；如果没有这一行，cancel 无法调用 terminate、kill 或 wait。
        self.turn_id = str(turn_id)  # 新增代码+CodexCliStreaming：保存 turn id；如果没有这一行，取消事件可能污染其他轮次。
        self.provider_id = str(provider_id)  # 新增代码+CodexCliStreaming：保存 provider id；如果没有这一行，状态面板看不出取消来自哪个提供商。
        self.model_id = str(model_id)  # 新增代码+CodexCliStreaming：保存模型 id；如果没有这一行，用户无法确认被取消的是底部选中的模型。
        self.cancel_timeout_seconds = float(cancel_timeout_seconds)  # 新增代码+CodexCliStreaming：保存软终止等待秒数；如果没有这一行，卡死进程可能让 GUI 无限等待。
        self._cancelled = False  # 新增代码+CodexCliStreaming：记录是否已经取消过；如果没有这一行，重复点击停止会重复杀进程和发事件。
        self.ignore_late_output = False  # 新增代码+CodexCliStreaming：标记取消后的迟到输出需要丢弃；如果没有这一行，stdout/stderr 可能继续污染当前会话。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliProcessController.__init__ 到此结束；如果没有边界说明，用户不容易看出初始化范围。

    def _event(self, phase: str, message: str, elapsed_ms: int, sequence: int, metadata: dict[str, object] | None = None) -> ModelStreamEvent:  # 新增代码+CodexCliStreaming：函数段开始，创建取消状态事件；如果没有这段，cancel_requested 和 cancelled 会重复拼字段。
        return ModelStreamEvent("status", phase, message, time.time(), int(elapsed_ms), int(sequence), self.turn_id, self.provider_id, self.model_id, dict(metadata or {}))  # 新增代码+CodexCliStreaming：返回统一状态事件；如果没有这一行，GUI adapter 无法显示取消阶段。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliProcessController._event 到此结束；如果没有边界说明，用户不容易看出事件构造范围。

    def _process_has_exited(self) -> bool:  # 新增代码+CodexCliStreaming：函数段开始，判断子进程是否已退出；如果没有这段，取消可能误杀已经结束的进程。
        poll = getattr(self.process, "poll", None)  # 新增代码+CodexCliStreaming：读取 Popen 风格 poll 方法；如果没有这一行，fake process 和真实 Popen 无法统一处理。
        if callable(poll):  # 新增代码+CodexCliStreaming：只有 poll 可调用时才调用；如果没有这一行，特殊对象会抛属性错误。
            return poll() is not None  # 新增代码+CodexCliStreaming：poll 返回退出码表示已结束；如果没有这一行，控制器无法区分运行中和已退出。
        return getattr(self.process, "returncode", None) is not None  # 新增代码+CodexCliStreaming：没有 poll 时回退 returncode；如果没有这一行，兼容对象会被误判为运行中。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliProcessController._process_has_exited 到此结束；如果没有边界说明，用户不容易看出进程状态判断范围。

    def _terminate_running_process(self) -> tuple[bool, bool, bool]:  # 新增代码+CodexCliStreaming：函数段开始，先软终止再必要时强杀；如果没有这段，停止按钮不能真正阻断慢模型调用。
        already_exited = self._process_has_exited()  # 新增代码+CodexCliStreaming：先判断进程是否已经退出；如果没有这一行，已退出进程仍会被 terminate。
        soft_terminate_attempted = False  # 新增代码+CodexCliStreaming：记录是否尝试软终止；如果没有这一行，metadata 无法说明后端做过什么。
        forced_kill_attempted = False  # 新增代码+CodexCliStreaming：记录是否尝试强杀；如果没有这一行，超时路径没有可观察证据。
        if already_exited:  # 新增代码+CodexCliStreaming：已退出时不再操作进程；如果没有这一行，no-op 语义会被破坏。
            return already_exited, soft_terminate_attempted, forced_kill_attempted  # 新增代码+CodexCliStreaming：返回已退出状态；如果没有这一行，后续仍会访问 terminate。
        terminate = getattr(self.process, "terminate", None)  # 新增代码+CodexCliStreaming：读取软终止方法；如果没有这一行，无法优雅请求子进程退出。
        if callable(terminate):  # 新增代码+CodexCliStreaming：确认 terminate 可调用；如果没有这一行，特殊进程对象会抛属性错误。
            soft_terminate_attempted = True  # 新增代码+CodexCliStreaming：标记已尝试软终止；如果没有这一行，metadata 会误报没有做过软终止。
            terminate()  # 新增代码+CodexCliStreaming：请求子进程优雅退出；如果没有这一行，Codex CLI 可能继续占用网络请求。
        wait = getattr(self.process, "wait", None)  # 新增代码+CodexCliStreaming：读取等待退出方法；如果没有这一行，无法给软终止留出收尾时间。
        if callable(wait):  # 新增代码+CodexCliStreaming：确认 wait 可调用；如果没有这一行，特殊 fake 会抛属性错误。
            try:  # 新增代码+CodexCliStreaming：保护软终止等待；如果没有这一行，超时异常会打断取消流程。
                wait(timeout=self.cancel_timeout_seconds)  # 新增代码+CodexCliStreaming：最多等待配置秒数；如果没有这一行，取消可能无限卡住 GUI。
                return already_exited, soft_terminate_attempted, forced_kill_attempted  # 新增代码+CodexCliStreaming：软终止成功后返回；如果没有这一行，会继续走强杀分支。
            except subprocess.TimeoutExpired:  # 新增代码+CodexCliStreaming：识别软终止超时；如果没有这一行，卡死进程不会进入 kill fallback。
                forced_kill_attempted = True  # 新增代码+CodexCliStreaming：标记需要强杀；如果没有这一行，metadata 无法解释强制终止。
                kill = getattr(self.process, "kill", None)  # 新增代码+CodexCliStreaming：读取强杀方法；如果没有这一行，无法处理拒绝退出的子进程。
                if callable(kill):  # 新增代码+CodexCliStreaming：确认 kill 可调用；如果没有这一行，缺少 kill 的对象会抛异常。
                    kill()  # 新增代码+CodexCliStreaming：强制结束子进程；如果没有这一行，卡住的 Codex CLI 会拖慢后续 turn。
                try:  # 新增代码+CodexCliStreaming：保护强杀后的等待；如果没有这一行，二次等待异常会打断取消终态事件。
                    wait(timeout=self.cancel_timeout_seconds)  # 新增代码+CodexCliStreaming：等待强杀生效；如果没有这一行，进程表可能残留。
                except Exception:  # 新增代码+CodexCliStreaming：吞掉强杀后的等待异常；如果没有这一行，用户可能看不到 cancelled 终态。
                    pass  # 新增代码+CodexCliStreaming：保持取消流程继续闭合；如果没有这一行，异常处理块为空会语法错误。
        return already_exited, soft_terminate_attempted, forced_kill_attempted  # 新增代码+CodexCliStreaming：返回进程处理结果；如果没有这一行，调用方拿不到 metadata。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliProcessController._terminate_running_process 到此结束；如果没有边界说明，用户不容易看出进程终止范围。

    def _drain_output(self) -> None:  # 新增代码+CodexCliStreaming：函数段开始，清理取消后的输出队列；如果没有这段，迟到 stdout/stderr 可能继续进入 GUI。
        drain_output = getattr(self.process, "drain_output", None)  # 新增代码+CodexCliStreaming：读取测试或 runner 注入的 drain_output；如果没有这一行，输出清理没有入口。
        if callable(drain_output):  # 新增代码+CodexCliStreaming：确认 drain_output 可调用；如果没有这一行，None 会被误调用。
            drain_output()  # 新增代码+CodexCliStreaming：清理 stdout/stderr 队列；如果没有这一行，取消后旧输出可能污染下一轮。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliProcessController._drain_output 到此结束；如果没有边界说明，用户不容易看出输出清理范围。

    def cancel(self, elapsed_ms: int = 0) -> list[ModelStreamEvent]:  # 新增代码+CodexCliStreaming：函数段开始，执行幂等取消并返回可见事件；如果没有这段，GUI 停止按钮无法真正停止 CLI runner。
        if self._cancelled:  # 新增代码+CodexCliStreaming：重复取消时直接返回；如果没有这一行，双击停止会重复终止进程和重复写事件。
            return []  # 新增代码+CodexCliStreaming：幂等取消不再发新事件；如果没有这一行，时间线会出现重复取消噪声。
        self._cancelled = True  # 新增代码+CodexCliStreaming：标记控制器已取消；如果没有这一行，后续调用无法识别已经处理过。
        self.ignore_late_output = True  # 新增代码+CodexCliStreaming：告诉 runner 忽略后续迟到输出；如果没有这一行，取消后 stdout/stderr 仍可能刷到聊天区。
        events = [self._event("cancel_requested", "用户已经请求取消 Codex CLI 模型调用。", elapsed_ms, 1)]  # 新增代码+CodexCliStreaming：先发取消请求事件；如果没有这一行，前端短时间内看不到停止已进入后端。
        already_exited, soft_terminate_attempted, forced_kill_attempted = self._terminate_running_process()  # 新增代码+CodexCliStreaming：执行真实进程终止；如果没有这一行，取消按钮不会停止 Codex CLI 子进程。
        self._drain_output()  # 新增代码+CodexCliStreaming：清理输出队列；如果没有这一行，取消后的晚到输出可能继续污染 UI。
        metadata = {"process_already_exited": already_exited, "soft_terminate_attempted": soft_terminate_attempted, "forced_kill_attempted": forced_kill_attempted}  # 新增代码+CodexCliStreaming：记录低敏进程处理结果；如果没有这一行，验收无法判断后端是否真的停了进程。
        events.append(self._event("cancelled", "Codex CLI 模型调用已经取消。", elapsed_ms, 2, metadata))  # 新增代码+CodexCliStreaming：发出取消终态事件；如果没有这一行，GUI 可能一直停在 cancel_requested。
        return events  # 新增代码+CodexCliStreaming：返回取消事件列表；如果没有这一行，adapter 无法把状态转发给 GUI。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliProcessController.cancel 到此结束；如果没有边界说明，用户不容易看出取消闭环范围。
# 新增代码+CodexCliStreaming：类段结束，CodexCliProcessController 到此结束；如果没有边界说明，用户不容易看出进程控制器范围。


class CodexCliStreamingRunner:  # 新增代码+CodexCliStreaming：类段开始，负责把 Codex CLI 子进程输出转换为模型流事件；如果没有这段，GUI 仍要阻塞等待最终文件。
    def __init__(  # 新增代码+CodexCliStreaming：函数段开始，初始化可观测 CLI runner；如果没有这段，调用方无法配置命令、prompt、输出文件和测试进程工厂。
        self,  # 新增代码+CodexCliStreaming：当前 runner 实例；如果没有这一行，Python 方法签名不完整。
        *,  # 新增代码+CodexCliStreaming：强制使用关键字参数；如果没有这一行，命令和 prompt 容易被误传错位。
        command: list[str],  # 新增代码+CodexCliStreaming：保存要执行的 codex exec 命令数组；如果没有这一行，runner 不知道该启动什么。
        prompt: str,  # 新增代码+CodexCliStreaming：保存要写入 stdin 的提示词；如果没有这一行，Codex CLI 无法收到用户请求。
        output_path: Path,  # 新增代码+CodexCliStreaming：保存 output-last-message 文件路径；如果没有这一行，stdout 无 delta 时无法读取最终回答。
        cwd: str | Path,  # 新增代码+CodexCliStreaming：保存工作目录；如果没有这一行，Codex CLI 可能在错误目录运行。
        process_factory: CodexProcessFactory | None = None,  # 新增代码+CodexCliStreaming：允许测试注入 fake process；如果没有这一行，单元测试会启动真实 Codex CLI。
        stdout_contains_token_deltas: bool = False,  # 新增代码+CodexCliStreaming：记录 discovery 是否证明 stdout 有 token delta；如果没有这一行，runner 可能假装有真流式 token。
        parse_output: CodexOutputParser | None = None,  # 新增代码+CodexCliStreaming：保存最终输出解析器；如果没有这一行，adapter 不能复用已有 JSON 协议解析。
        timeout_seconds: int = 300,  # 新增代码+CodexCliStreaming：保存总超时秒数；如果没有这一行，子进程异常卡住会拖死 GUI。
        poll_interval_seconds: float = 0.02,  # 新增代码+CodexCliStreaming：保存事件轮询间隔；如果没有这一行，主循环可能忙等或响应太慢。
    ) -> None:
        self.command = list(command)  # 新增代码+CodexCliStreaming：复制命令数组；如果没有这一行，外部修改列表会影响正在运行的 runner。
        self.prompt = str(prompt)  # 新增代码+CodexCliStreaming：保存字符串 prompt；如果没有这一行，stdin 写入可能收到非字符串对象。
        self.output_path = Path(output_path)  # 新增代码+CodexCliStreaming：规范化输出路径对象；如果没有这一行，最终文件读取会更脆弱。
        self.cwd = Path(cwd).expanduser().resolve()  # 新增代码+CodexCliStreaming：规范化工作目录；如果没有这一行，Popen cwd 和测试断言可能不稳定。
        self.process_factory = process_factory  # 新增代码+CodexCliStreaming：保存可选进程工厂；如果没有这一行，测试替身不会生效。
        self.stdout_contains_token_deltas = bool(stdout_contains_token_deltas)  # 新增代码+CodexCliStreaming：保存是否允许解析 stdout delta；如果没有这一行，discovery 门禁无法约束行为。
        self.parse_output = parse_output  # 新增代码+CodexCliStreaming：保存可选输出解析器；如果没有这一行，最终 JSON 只能被当成普通文本。
        self.timeout_seconds = int(timeout_seconds)  # 新增代码+CodexCliStreaming：保存总超时；如果没有这一行，超时门禁无法执行。
        self.poll_interval_seconds = float(poll_interval_seconds)  # 新增代码+CodexCliStreaming：保存轮询间隔；如果没有这一行，队列读取等待时间无法调整。
        self.last_process_controller: CodexCliProcessController | None = None  # 新增代码+CodexCliStreaming：保存最近进程控制器；如果没有这一行，后续可见取消无法接入进程。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner.__init__ 到此结束；如果没有边界说明，用户不容易看出 runner 配置范围。

    def _elapsed_ms(self, started_at: float) -> int:  # 新增代码+CodexCliStreaming：函数段开始，计算相对耗时；如果没有这段，每个事件都要重复写时间换算。
        return int((time.monotonic() - started_at) * 1000)  # 新增代码+CodexCliStreaming：返回毫秒耗时；如果没有这一行，GUI 无法展示阶段成本。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner._elapsed_ms 到此结束；如果没有边界说明，用户不容易看出耗时计算范围。

    def _event(self, event_type: str, phase: str, message: str, started_at: float, sequence: int, turn_id: str, provider_id: str, model_id: str, metadata: dict[str, object] | None = None) -> ModelStreamEvent:  # 新增代码+CodexCliStreaming：函数段开始，统一生成模型流事件；如果没有这段，runner 各分支会重复构造字段。
        return ModelStreamEvent(event_type, phase, str(message), time.time(), self._elapsed_ms(started_at), int(sequence), str(turn_id), str(provider_id), str(model_id), dict(metadata or {}))  # 新增代码+CodexCliStreaming：返回统一事件对象；如果没有这一行，adapter 无法消费 CLI runner 输出。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner._event 到此结束；如果没有边界说明，用户不容易看出事件构造范围。

    def _start_process(self) -> Any:  # 新增代码+CodexCliStreaming：函数段开始，启动真实或 fake Codex CLI 进程；如果没有这段，stream 只能处理已经存在的进程。
        if self.process_factory is not None:  # 新增代码+CodexCliStreaming：优先使用测试注入工厂；如果没有这一行，单元测试无法避免真实网络和真实 CLI。
            return self.process_factory(list(self.command), self.cwd)  # 新增代码+CodexCliStreaming：创建 fake 或自定义进程；如果没有这一行，注入点不会生效。
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" and hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP") else 0  # 新增代码+CodexCliStreaming：Windows 下创建独立进程组；如果没有这一行，取消时更难可靠停止 CLI。
        return subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", cwd=self.cwd, creationflags=creationflags)  # 新增代码+CodexCliStreaming：用 Popen 启动而不是 subprocess.run；如果没有这一行，状态事件必须等进程结束才出现。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner._start_process 到此结束；如果没有边界说明，用户不容易看出进程启动范围。

    def _write_prompt(self, process: Any) -> None:  # 新增代码+CodexCliStreaming：函数段开始，把 prompt 写入 stdin；如果没有这段，Codex CLI 会一直等输入。
        stdin = getattr(process, "stdin", None)  # 新增代码+CodexCliStreaming：读取进程 stdin；如果没有这一行，缺少 stdin 的 fake process 无法兼容。
        if stdin is None:  # 新增代码+CodexCliStreaming：没有 stdin 时直接跳过；如果没有这一行，特殊进程对象会触发异常。
            return  # 新增代码+CodexCliStreaming：结束写入流程；如果没有这一行，后续会访问 None。
        try:  # 新增代码+CodexCliStreaming：保护 stdin 写入；如果没有这一行，BrokenPipe 会打断状态事件流。
            stdin.write(self.prompt)  # 新增代码+CodexCliStreaming：写入完整 prompt；如果没有这一行，模型收不到本轮用户输入。
            flush = getattr(stdin, "flush", None)  # 新增代码+CodexCliStreaming：读取 flush 方法；如果没有这一行，缓冲流可能不立刻发送 prompt。
            if callable(flush):  # 新增代码+CodexCliStreaming：只有 flush 存在才调用；如果没有这一行，StringIO 兼容性会变差。
                flush()  # 新增代码+CodexCliStreaming：刷新 stdin；如果没有这一行，真实子进程可能继续等待缓冲内容。
            close = getattr(stdin, "close", None)  # 新增代码+CodexCliStreaming：读取 close 方法；如果没有这一行，Codex CLI 可能不知道 stdin 已结束。
            if callable(close):  # 新增代码+CodexCliStreaming：只有 close 存在才调用；如果没有这一行，特殊 stdin 会抛属性错误。
                close()  # 新增代码+CodexCliStreaming：关闭 stdin 表示 prompt 完成；如果没有这一行，CLI 可能一直等待更多输入。
        except (BrokenPipeError, OSError, ValueError):  # 新增代码+CodexCliStreaming：吞掉进程已退出或 stdin 已关闭错误；如果没有这一行，早失败进程会隐藏真正 stderr。
            return  # 新增代码+CodexCliStreaming：保持 runner 继续读取 stderr；如果没有这一行，异常会向外中断。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner._write_prompt 到此结束；如果没有边界说明，用户不容易看出 stdin 写入范围。

    def _iter_stream_lines(self, stream: Any) -> Iterable[str]:  # 新增代码+CodexCliStreaming：函数段开始，安全遍历文本流行；如果没有这段，StringIO 和 Popen 管道处理会分散。
        if stream is None:  # 新增代码+CodexCliStreaming：没有流时返回空；如果没有这一行，缺少 stderr/stdout 的 fake process 会崩溃。
            return []  # 新增代码+CodexCliStreaming：返回空列表；如果没有这一行，调用方会尝试遍历 None。
        if isinstance(stream, io.StringIO):  # 新增代码+CodexCliStreaming：识别测试 StringIO；如果没有这一行，fake 输出仍可工作但可读性更差。
            stream.seek(0)  # 新增代码+CodexCliStreaming：把 fake 流游标移到开头；如果没有这一行，测试预置输出可能读不到。
        return stream  # 新增代码+CodexCliStreaming：返回可迭代文本流；如果没有这一行，后台 reader 没有输入源。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner._iter_stream_lines 到此结束；如果没有边界说明，用户不容易看出流兼容范围。

    def _reader_thread(self, stream: Any, source: str, output_queue: "queue.Queue[tuple[str, str | None]]") -> threading.Thread:  # 新增代码+CodexCliStreaming：函数段开始，创建 stdout/stderr 读取线程；如果没有这段，主线程会被任一管道阻塞。
        def run() -> None:  # 新增代码+CodexCliStreaming：内部函数开始，执行具体读取；如果没有这段，线程没有可运行目标。
            try:  # 新增代码+CodexCliStreaming：保护后台读取；如果没有这一行，管道异常会静默杀死线程且没有结束哨兵。
                for raw_line in self._iter_stream_lines(stream):  # 新增代码+CodexCliStreaming：逐行读取流内容；如果没有这一行，runner 无法捕获 CLI 生命周期和 warning。
                    output_queue.put((source, str(raw_line).rstrip("\r\n")))  # 新增代码+CodexCliStreaming：把来源和行内容放入队列；如果没有这一行，主生成器收不到输出。
            finally:  # 新增代码+CodexCliStreaming：无论是否异常都发送结束信号；如果没有这一行，主循环可能永远等线程完成。
                output_queue.put((source, None))  # 新增代码+CodexCliStreaming：发送当前来源已读完哨兵；如果没有这一行，runner 不知道 stdout/stderr 已结束。
        # 新增代码+CodexCliStreaming：内部函数结束，run 到此结束；如果没有边界说明，用户不容易看出后台读取范围。
        thread = threading.Thread(target=run, name=f"openharness-codex-cli-{source}", daemon=True)  # 新增代码+CodexCliStreaming：创建 daemon 线程；如果没有这一行，异常退出时后台 reader 可能阻止程序结束。
        thread.start()  # 新增代码+CodexCliStreaming：启动后台读取；如果没有这一行，队列永远不会收到 stdout/stderr。
        return thread  # 新增代码+CodexCliStreaming：返回线程对象；如果没有这一行，主循环无法检查线程是否仍活着。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner._reader_thread 到此结束；如果没有边界说明，用户不容易看出线程创建范围。

    def _phase_from_stderr(self, line: str) -> tuple[str, str] | None:  # 新增代码+CodexCliStreaming：函数段开始，把 stderr warning 映射为可见阶段；如果没有这段，WebSocket timeout 仍只藏在日志里。
        if "Responses WebSocket timed out" in line or "stream disconnected" in line:  # 新增代码+CodexCliStreaming：识别 WebSocket 超时或断流；如果没有这一行，用户不知道慢在 WebSocket 阶段。
            return "websocket_timeout", "Codex CLI WebSocket 连接超时，正在等待后续 fallback。"  # 新增代码+CodexCliStreaming：返回 timeout 阶段和说明；如果没有这一行，状态面板无法解释超时。
        if "Falling back from WebSockets to HTTPS transport" in line or "Falling back from WebSockets" in line:  # 新增代码+CodexCliStreaming：识别 HTTPS fallback；如果没有这一行，用户不知道后端已切换传输。
            return "https_fallback", "Codex CLI 已从 WebSocket 切换到 HTTPS fallback。"  # 新增代码+CodexCliStreaming：返回 fallback 阶段和说明；如果没有这一行，状态面板无法显示切换。
        return None  # 新增代码+CodexCliStreaming：其他 stderr 行不直接冒泡；如果没有这一行，普通 warning 会变成过多 UI 噪声。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner._phase_from_stderr 到此结束；如果没有边界说明，用户不容易看出 warning 映射范围。

    def _stdout_delta(self, line: str) -> str:  # 新增代码+CodexCliStreaming：函数段开始，尝试从 stdout JSONL 中提取 token delta；如果没有这段，未来发现 delta 后也无法使用。
        if not self.stdout_contains_token_deltas:  # 新增代码+CodexCliStreaming：只有 discovery 允许时才解析 token delta；如果没有这一行，当前无证据 CLI 会被误标为真流式。
            return ""  # 新增代码+CodexCliStreaming：默认不提取 delta；如果没有这一行，普通 lifecycle JSON 可能被误当正文。
        try:  # 新增代码+CodexCliStreaming：保护 JSON 解析；如果没有这一行，非 JSON stdout 会打断整个流。
            payload = json.loads(line)  # 新增代码+CodexCliStreaming：解析 stdout 行；如果没有这一行，无法读取 delta 字段。
        except json.JSONDecodeError:  # 新增代码+CodexCliStreaming：处理非 JSON 行；如果没有这一行，生命周期之外的输出会抛异常。
            return ""  # 新增代码+CodexCliStreaming：非 JSON 行不产生 delta；如果没有这一行，错误文本可能污染聊天区。
        if not isinstance(payload, dict):  # 新增代码+CodexCliStreaming：只接受对象形式事件；如果没有这一行，数组或字符串可能造成字段访问异常。
            return ""  # 新增代码+CodexCliStreaming：非对象事件不产生 delta；如果没有这一行，坏格式会继续处理。
        raw_type = str(payload.get("type", ""))  # 新增代码+CodexCliStreaming：读取事件类型；如果没有这一行，无法识别 response.output_text.delta。
        if "delta" in payload and isinstance(payload.get("delta"), str):  # 新增代码+CodexCliStreaming：优先读取标准 delta 字段；如果没有这一行，常见流式字段无法显示。
            return str(payload["delta"])  # 新增代码+CodexCliStreaming：返回文本增量；如果没有这一行，已验证 delta 会被丢弃。
        if "text_delta" in payload and isinstance(payload.get("text_delta"), str):  # 新增代码+CodexCliStreaming：兼容 text_delta 字段；如果没有这一行，另一类事件形状无法显示。
            return str(payload["text_delta"])  # 新增代码+CodexCliStreaming：返回文本增量；如果没有这一行，兼容 delta 会被丢弃。
        if raw_type.endswith(".delta") and isinstance(payload.get("message"), str):  # 新增代码+CodexCliStreaming：兼容把增量放在 message 的事件；如果没有这一行，未来 CLI 形状变化会丢字。
            return str(payload["message"])  # 新增代码+CodexCliStreaming：返回 message 增量；如果没有这一行，兼容事件不会显示。
        return ""  # 新增代码+CodexCliStreaming：未识别 delta 时返回空；如果没有这一行，函数没有稳定返回值。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner._stdout_delta 到此结束；如果没有边界说明，用户不容易看出 delta 解析范围。

    def _default_parse_output(self, raw_output: str) -> Any:  # 新增代码+CodexCliStreaming：函数段开始，提供轻量最终输出解析；如果没有这段，runner 单独测试必须依赖 adapters.py。
        try:  # 新增代码+CodexCliStreaming：保护 JSON 解析；如果没有这一行，普通文本输出会变成异常。
            payload = json.loads(raw_output)  # 新增代码+CodexCliStreaming：尝试读取 JSON 输出；如果没有这一行，无法从 text 字段拿最终回答。
        except json.JSONDecodeError:  # 新增代码+CodexCliStreaming：处理非 JSON 输出；如果没有这一行，fallback stdout 会中断。
            return raw_output  # 新增代码+CodexCliStreaming：直接返回原文本；如果没有这一行，用户看不到 CLI 最终输出。
        if isinstance(payload, dict):  # 新增代码+CodexCliStreaming：对象输出才读取 text 字段；如果没有这一行，列表输出会被误访问。
            return payload.get("text", raw_output)  # 新增代码+CodexCliStreaming：优先返回 text；如果没有这一行，结构化最终回答会连 JSON 一起显示。
        return raw_output  # 新增代码+CodexCliStreaming：非对象 JSON 回退原文；如果没有这一行，函数没有稳定返回值。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner._default_parse_output 到此结束；如果没有边界说明，用户不容易看出默认解析范围。

    def _text_from_parsed_output(self, parsed_output: Any) -> str:  # 新增代码+CodexCliStreaming：函数段开始，从解析结果取可显示文本；如果没有这段，ModelMessage 和字符串无法统一处理。
        if isinstance(parsed_output, str):  # 新增代码+CodexCliStreaming：字符串结果直接使用；如果没有这一行，默认解析结果会被误判。
            return parsed_output  # 新增代码+CodexCliStreaming：返回字符串；如果没有这一行，文本输出会丢失。
        text = getattr(parsed_output, "text", None)  # 新增代码+CodexCliStreaming：读取 ModelMessage.text；如果没有这一行，adapter 解析器结果无法显示。
        if text is not None:  # 新增代码+CodexCliStreaming：有 text 字段时使用；如果没有这一行，ModelMessage 会被转成对象字符串。
            return str(text)  # 新增代码+CodexCliStreaming：返回最终文本；如果没有这一行，GUI 聊天区拿不到回答。
        return str(parsed_output)  # 新增代码+CodexCliStreaming：兜底转字符串；如果没有这一行，未知解析对象无法显示。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner._text_from_parsed_output 到此结束；如果没有边界说明，用户不容易看出文本抽取范围。

    def _read_final_text(self, stdout_lines: list[str]) -> str:  # 新增代码+CodexCliStreaming：函数段开始，读取 output-last-message 或 stdout fallback；如果没有这段，无 delta CLI 成功后没有正文。
        raw_output = ""  # 新增代码+CodexCliStreaming：准备最终原始输出；如果没有这一行，后续分支可能引用未定义变量。
        if self.output_path.exists():  # 新增代码+CodexCliStreaming：优先读取 Codex CLI 最终输出文件；如果没有这一行，结构化输出文件会被忽略。
            raw_output = self.output_path.read_text(encoding="utf-8", errors="replace").strip()  # 新增代码+CodexCliStreaming：读取最终文件内容；如果没有这一行，GUI 无法拿到最终回答。
        elif stdout_lines:  # 新增代码+CodexCliStreaming：没有文件时退回 stdout；如果没有这一行，旧 CLI 输出方式会丢失。
            raw_output = "\n".join(stdout_lines).strip()  # 新增代码+CodexCliStreaming：拼接 stdout 行；如果没有这一行，fallback 输出会不完整。
        if not raw_output:  # 新增代码+CodexCliStreaming：没有任何最终输出时直接返回空；如果没有这一行，空输出会被解析成误导文本。
            return ""  # 新增代码+CodexCliStreaming：返回空文本；如果没有这一行，调用方无法区分无输出。
        parser = self.parse_output or self._default_parse_output  # 新增代码+CodexCliStreaming：选择调用方解析器或默认解析；如果没有这一行，adapter 的工具协议解析无法复用。
        parsed_output = parser(raw_output)  # 新增代码+CodexCliStreaming：解析最终输出；如果没有这一行，结构化 JSON 不会变成文本。
        return self._text_from_parsed_output(parsed_output).strip()  # 新增代码+CodexCliStreaming：抽取并清理最终文本；如果没有这一行，GUI 会显示多余空白或对象表示。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner._read_final_text 到此结束；如果没有边界说明，用户不容易看出最终输出读取范围。

    def _returncode(self, process: Any) -> int | None:  # 新增代码+CodexCliStreaming：函数段开始，读取进程退出码；如果没有这段，Popen 和 fake process 退出状态处理会分散。
        poll = getattr(process, "poll", None)  # 新增代码+CodexCliStreaming：读取 poll 方法；如果没有这一行，无法刷新真实 Popen 的 returncode。
        if callable(poll):  # 新增代码+CodexCliStreaming：只有 poll 可调用才执行；如果没有这一行，特殊 fake 会抛异常。
            return poll()  # 新增代码+CodexCliStreaming：返回当前退出码或 None；如果没有这一行，主循环不知道进程是否完成。
        return getattr(process, "returncode", None)  # 新增代码+CodexCliStreaming：没有 poll 时读取 returncode 字段；如果没有这一行，fake process 无法工作。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner._returncode 到此结束；如果没有边界说明，用户不容易看出退出码读取范围。

    def stream(self, *, turn_id: str, provider_id: str, model_id: str, is_cancelled: CodexCancelChecker | None = None) -> Iterable[ModelStreamEvent]:  # 修改代码+CodexCliCancelBridge：函数段开始，生成 Codex CLI 可观测事件流并接收 GUI 取消信号；如果没有这段，GUI 仍会卡在等待后端响应。
        started_at = time.monotonic()  # 新增代码+CodexCliStreaming：记录本次调用起点；如果没有这一行，阶段耗时无法计算。
        sequence = 1  # 新增代码+CodexCliStreaming：初始化模型内部事件序号；如果没有这一行，adapter 诊断无法判断模型事件顺序。
        yield self._event("status", "connecting", "正在启动 Codex CLI 模型进程。", started_at, sequence, turn_id, provider_id, model_id)  # 新增代码+CodexCliStreaming：立即发出连接状态；如果没有这一行，用户仍会在启动阶段看到沉默等待。
        sequence += 1  # 新增代码+CodexCliStreaming：递增序号；如果没有这一行，后续事件会和 connecting 重号。
        try:  # 新增代码+CodexCliStreaming：保护进程启动；如果没有这一行，FileNotFoundError 等会直接炸出 adapter。
            process = self._start_process()  # 新增代码+CodexCliStreaming：启动真实或 fake 进程；如果没有这一行，runner 没有输出来源。
        except Exception as error:  # 新增代码+CodexCliStreaming：捕获启动失败；如果没有这一行，GUI 只能看到线程异常。
            yield self._event("error", "failed", f"Codex CLI 启动失败：{error}", started_at, sequence, turn_id, provider_id, model_id)  # 新增代码+CodexCliStreaming：把启动失败转成模型错误事件；如果没有这一行，用户不知道命令不可用。
            return  # 新增代码+CodexCliStreaming：启动失败后结束；如果没有这一行，后续会访问不存在的 process。
        self.last_process_controller = CodexCliProcessController(process, turn_id=turn_id, provider_id=provider_id, model_id=model_id)  # 新增代码+CodexCliStreaming：保存取消控制器；如果没有这一行，后续无法真实停止子进程。
        self._write_prompt(process)  # 新增代码+CodexCliStreaming：写入 stdin prompt；如果没有这一行，Codex CLI 会一直等输入。
        output_queue: queue.Queue[tuple[str, str | None]] = queue.Queue()  # 新增代码+CodexCliStreaming：创建 stdout/stderr 合并队列；如果没有这一行，主循环无法统一消费输出。
        stdout_thread = self._reader_thread(getattr(process, "stdout", None), "stdout", output_queue)  # 新增代码+CodexCliStreaming：启动 stdout reader；如果没有这一行，stdout JSONL 生命周期不会被读取。
        stderr_thread = self._reader_thread(getattr(process, "stderr", None), "stderr", output_queue)  # 新增代码+CodexCliStreaming：启动 stderr reader；如果没有这一行，WebSocket timeout warning 不会被捕获。
        stdout_done = False  # 新增代码+CodexCliStreaming：记录 stdout 是否结束；如果没有这一行，主循环不知道何时收尾。
        stderr_done = False  # 新增代码+CodexCliStreaming：记录 stderr 是否结束；如果没有这一行，主循环不知道何时收尾。
        stdout_lines: list[str] = []  # 新增代码+CodexCliStreaming：保存 stdout 行用于最终 fallback；如果没有这一行，没有 output 文件时会丢失结果。
        stderr_lines: list[str] = []  # 新增代码+CodexCliStreaming：保存 stderr 行用于错误详情；如果没有这一行，非零退出没有可读原因。
        delta_seen = False  # 新增代码+CodexCliStreaming：记录是否已经发过正文 delta；如果没有这一行，最终文件可能重复发同一段回答。
        while True:  # 新增代码+CodexCliStreaming：持续读取输出直到进程和管道都结束；如果没有这一行，runner 只会处理第一条事件。
            if is_cancelled is not None and is_cancelled():  # 新增代码+CodexCliCancelBridge：每次轮询前检查 GUI 是否请求取消；如果没有这一行，Codex CLI 卡在网络等待时停止按钮不能立即生效。
                cancel_events = self.last_process_controller.cancel(self._elapsed_ms(started_at)) if self.last_process_controller else []  # 新增代码+CodexCliCancelBridge：通过进程控制器终止真实 CLI；如果没有这一行，取消只会改变 UI 状态而不停止子进程。
                for cancel_event in cancel_events:  # 新增代码+CodexCliCancelBridge：逐个转发取消阶段；如果没有这一行，状态面板看不到 cancel_requested 和 cancelled。
                    yield cancel_event  # 新增代码+CodexCliCancelBridge：把取消事件交给 adapter；如果没有这一行，GUI 不能及时闭合取消状态。
                return  # 新增代码+CodexCliCancelBridge：取消后立即结束流；如果没有这一行，迟到 stdout/stderr 可能继续污染当前 turn。
            if self.timeout_seconds > 0 and self._elapsed_ms(started_at) > self.timeout_seconds * 1000:  # 新增代码+CodexCliStreaming：检查总超时；如果没有这一行，卡死 CLI 会无限拖住 GUI。
                cancel_events = self.last_process_controller.cancel(self._elapsed_ms(started_at)) if self.last_process_controller else []  # 新增代码+CodexCliStreaming：超时时尝试真实取消进程；如果没有这一行，超时后子进程可能残留。
                for cancel_event in cancel_events:  # 新增代码+CodexCliStreaming：转发取消控制器事件；如果没有这一行，用户看不到超时后已尝试终止。
                    yield cancel_event  # 新增代码+CodexCliStreaming：发出取消事件；如果没有这一行，状态面板不会更新。
                yield self._event("error", "failed", "Codex CLI 模型调用超时。", started_at, sequence, turn_id, provider_id, model_id)  # 新增代码+CodexCliStreaming：发出超时错误；如果没有这一行，turn 可能停在 running。
                return  # 新增代码+CodexCliStreaming：超时后结束流；如果没有这一行，循环可能继续等待。
            try:  # 新增代码+CodexCliStreaming：保护队列读取；如果没有这一行，空队列超时无法作为正常轮询。
                source, line = output_queue.get(timeout=self.poll_interval_seconds)  # 新增代码+CodexCliStreaming：等待一条输出或哨兵；如果没有这一行，runner 无法实时处理子进程输出。
            except queue.Empty:  # 新增代码+CodexCliStreaming：没有新输出时检查是否可以结束；如果没有这一行，轮询间隔会抛异常。
                source = ""  # 新增代码+CodexCliStreaming：设置空来源占位；如果没有这一行，后续变量可能未定义。
                line = ""  # 新增代码+CodexCliStreaming：设置空行占位；如果没有这一行，后续变量可能未定义。
            if source == "stdout" and line is None:  # 新增代码+CodexCliStreaming：识别 stdout 结束哨兵；如果没有这一行，主循环会一直等 stdout。
                stdout_done = True  # 新增代码+CodexCliStreaming：标记 stdout 已结束；如果没有这一行，完成条件不会满足。
                continue  # 新增代码+CodexCliStreaming：哨兵不产生用户事件；如果没有这一行，None 会被当作输出处理。
            if source == "stderr" and line is None:  # 新增代码+CodexCliStreaming：识别 stderr 结束哨兵；如果没有这一行，主循环会一直等 stderr。
                stderr_done = True  # 新增代码+CodexCliStreaming：标记 stderr 已结束；如果没有这一行，完成条件不会满足。
                continue  # 新增代码+CodexCliStreaming：哨兵不产生用户事件；如果没有这一行，None 会被当作输出处理。
            if source == "stdout" and isinstance(line, str) and line:  # 新增代码+CodexCliStreaming：处理 stdout 普通行；如果没有这一行，stdout 内容不会被记录或解析。
                stdout_lines.append(line)  # 新增代码+CodexCliStreaming：保存 stdout 行；如果没有这一行，最终 fallback 可能没有内容。
                delta = self._stdout_delta(line)  # 新增代码+CodexCliStreaming：按 discovery 门禁尝试提取 delta；如果没有这一行，已验证 token delta 不会显示。
                if delta:  # 新增代码+CodexCliStreaming：只有真实 delta 才发聊天文本；如果没有这一行，空字符串会制造无意义事件。
                    phase = "first_delta" if not delta_seen else "streaming"  # 新增代码+CodexCliStreaming：首段和后续段使用不同阶段；如果没有这一行，首 token 指标无法区分。
                    delta_seen = True  # 新增代码+CodexCliStreaming：标记已经有正文；如果没有这一行，后续每段都会被当首 token。
                    yield self._event("delta", phase, delta, started_at, sequence, turn_id, provider_id, model_id, {"source": "stdout_jsonl"})  # 新增代码+CodexCliStreaming：发出真实 stdout delta；如果没有这一行，聊天区不会流式显示。
                    sequence += 1  # 新增代码+CodexCliStreaming：递增序号；如果没有这一行，多个 delta 会重号。
            if source == "stderr" and isinstance(line, str) and line:  # 新增代码+CodexCliStreaming：处理 stderr 普通行；如果没有这一行，transport warning 会被丢弃。
                stderr_lines.append(line)  # 新增代码+CodexCliStreaming：保存 stderr 行；如果没有这一行，错误详情会不完整。
                phase_message = self._phase_from_stderr(line)  # 新增代码+CodexCliStreaming：尝试映射为可见阶段；如果没有这一行，慢在哪一步仍不可见。
                if phase_message is not None:  # 新增代码+CodexCliStreaming：只有命中阶段才发状态；如果没有这一行，普通日志会刷爆 GUI。
                    phase, message = phase_message  # 新增代码+CodexCliStreaming：拆分阶段和说明；如果没有这一行，事件构造缺少字段。
                    yield self._event("status", phase, message, started_at, sequence, turn_id, provider_id, model_id, {"stderr_excerpt": line[:240]})  # 新增代码+CodexCliStreaming：发出 transport 状态；如果没有这一行，状态面板无法展示 WebSocket/fallback。
                    sequence += 1  # 新增代码+CodexCliStreaming：递增序号；如果没有这一行，阶段事件可能重号。
            process_done = self._returncode(process) is not None  # 新增代码+CodexCliStreaming：检查进程是否结束；如果没有这一行，完成条件无法判断。
            queue_empty = output_queue.empty()  # 新增代码+CodexCliStreaming：检查输出队列是否清空；如果没有这一行，可能提前结束丢最后几行。
            threads_done = stdout_done and stderr_done and not stdout_thread.is_alive() and not stderr_thread.is_alive()  # 新增代码+CodexCliStreaming：确认两个 reader 都结束；如果没有这一行，可能在 stderr 迟到前收尾。
            if process_done and queue_empty and threads_done:  # 新增代码+CodexCliStreaming：所有结束条件满足时跳出；如果没有这一行，循环不会收尾。
                break  # 新增代码+CodexCliStreaming：进入最终结果处理；如果没有这一行，while 会继续轮询。
        returncode = self._returncode(process)  # 新增代码+CodexCliStreaming：读取最终退出码；如果没有这一行，无法区分成功和失败。
        if returncode not in (0, None):  # 新增代码+CodexCliStreaming：非零退出视为模型失败；如果没有这一行，CLI 错误会被误当成功。
            detail = "\n".join(stderr_lines or stdout_lines).strip() or f"exit code {returncode}"  # 新增代码+CodexCliStreaming：生成失败详情；如果没有这一行，用户只会看到空错误。
            yield self._event("error", "failed", f"Codex CLI 调用失败：{detail[:1000]}", started_at, sequence, turn_id, provider_id, model_id, {"returncode": int(returncode)})  # 新增代码+CodexCliStreaming：发出失败事件；如果没有这一行，GUI 不会闭合失败状态。
            return  # 新增代码+CodexCliStreaming：失败后结束；如果没有这一行，后面可能继续读最终文件造成误成功。
        if not delta_seen:  # 新增代码+CodexCliStreaming：没有 stdout token delta 时读取最终输出文件；如果没有这一行，无 delta CLI 成功后不会显示回答。
            final_text = self._read_final_text(stdout_lines)  # 新增代码+CodexCliStreaming：读取最终文本；如果没有这一行，message_completed 会是空。
            if final_text:  # 新增代码+CodexCliStreaming：有文本时发一个首 delta；如果没有这一行，空输出也会制造正文事件。
                yield self._event("delta", "first_delta", final_text, started_at, sequence, turn_id, provider_id, model_id, {"source": "output_last_message", "token_streaming_verified": False})  # 新增代码+CodexCliStreaming：发出最终文件 fallback 文本；如果没有这一行，用户看不到回答。
                sequence += 1  # 新增代码+CodexCliStreaming：递增序号；如果没有这一行，completed 会和 delta 重号。
        yield self._event("completed", "completed", "Codex CLI 模型调用完成。", started_at, sequence, turn_id, provider_id, model_id, {"returncode": 0, "token_streaming_verified": bool(self.stdout_contains_token_deltas and delta_seen)})  # 新增代码+CodexCliStreaming：发出完成事件；如果没有这一行，adapter 会认为 stream 提前结束。
    # 新增代码+CodexCliStreaming：函数段结束，CodexCliStreamingRunner.stream 到此结束；如果没有边界说明，用户不容易看出 streaming 主流程。
# 新增代码+CodexCliStreaming：类段结束，CodexCliStreamingRunner 到此结束；如果没有边界说明，用户不容易看出 CLI runner 范围。
