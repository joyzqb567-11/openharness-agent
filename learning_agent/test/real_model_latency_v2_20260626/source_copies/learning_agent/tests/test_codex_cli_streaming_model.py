import io  # 新增代码+CodexCliStreamingTest：导入 StringIO 模拟 stdout/stderr/stdin；如果没有这一行，测试只能依赖真实子进程管道。
import json  # 新增代码+CodexCliStreamingTest：导入 JSON 序列化工具；如果没有这一行，测试无法生成 output-last-message 文件内容。
import subprocess  # 新增代码+CodexCliStreamingTest：导入 TimeoutExpired 用于 fake wait 超时；如果没有这一行，测试无法模拟软终止失败。
import tempfile  # 新增代码+CodexCliStreamingTest：导入临时目录工具；如果没有这一行，测试会污染真实项目目录。
import unittest  # 新增代码+CodexCliStreamingTest：使用标准库 unittest 承载 runner 契约；如果没有这一行，pytest 无法自动收集这些测试。
from pathlib import Path  # 新增代码+CodexCliStreamingTest：导入 Path 管理临时输出文件；如果没有这一行，路径处理会退回字符串拼接。


class FakeCodexProcess:  # 新增代码+CodexCliStreamingTest：类段开始，模拟 Codex CLI 子进程；如果没有这个类，取消和 streaming 测试只能启动真实 CLI。
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int | None = 0, exited: bool | None = None, wait_times_out: bool = False) -> None:  # 新增代码+CodexCliStreamingTest：函数段开始，配置 fake 输出、退出码和 wait 行为；如果没有这段，测试不能覆盖成功、失败、卡死三类路径。
        self.stdout = io.StringIO(stdout)  # 新增代码+CodexCliStreamingTest：保存 fake stdout；如果没有这一行，runner 无法读取模拟 JSONL。
        self.stderr = io.StringIO(stderr)  # 新增代码+CodexCliStreamingTest：保存 fake stderr；如果没有这一行，runner 无法读取模拟 transport warning。
        self.stdin = io.StringIO()  # 新增代码+CodexCliStreamingTest：保存 fake stdin；如果没有这一行，runner 写 prompt 时会访问不到 stdin。
        self.returncode = 0 if exited else returncode  # 新增代码+CodexCliStreamingTest：保存退出码；如果没有这一行，poll 无法判断 fake 进程状态。
        self.wait_times_out = wait_times_out  # 新增代码+CodexCliStreamingTest：保存 wait 是否超时；如果没有这一行，强杀路径无法触发。
        self.terminated = False  # 新增代码+CodexCliStreamingTest：记录 terminate 是否被调用；如果没有这一行，测试无法确认软终止。
        self.killed = False  # 新增代码+CodexCliStreamingTest：记录 kill 是否被调用；如果没有这一行，测试无法确认强杀。
        self.drained = False  # 新增代码+CodexCliStreamingTest：记录输出是否被 drain；如果没有这一行，测试无法确认取消后清理输出。
        self.wait_calls = 0  # 新增代码+CodexCliStreamingTest：记录 wait 次数；如果没有这一行，测试无法确认 kill 后再次等待。
    # 新增代码+CodexCliStreamingTest：函数段结束，FakeCodexProcess.__init__ 到此结束；如果没有边界说明，用户不容易看出 fake 状态字段范围。

    def poll(self) -> int | None:  # 新增代码+CodexCliStreamingTest：函数段开始，模拟 subprocess.poll；如果没有这段，被测代码无法判断进程状态。
        return self.returncode  # 新增代码+CodexCliStreamingTest：返回当前退出码；如果没有这一行，poll 没有输出。
    # 新增代码+CodexCliStreamingTest：函数段结束，FakeCodexProcess.poll 到此结束；如果没有边界说明，用户不容易看出 poll 范围。

    def terminate(self) -> None:  # 新增代码+CodexCliStreamingTest：函数段开始，模拟软终止；如果没有这段，被测代码无法调用 terminate。
        self.terminated = True  # 新增代码+CodexCliStreamingTest：记录软终止已尝试；如果没有这一行，测试无法确认 cancel 行为。
        if not self.wait_times_out:  # 新增代码+CodexCliStreamingTest：软终止成功场景直接退出；如果没有这一行，成功路径会一直像超时。
            self.returncode = 0  # 新增代码+CodexCliStreamingTest：设置退出码；如果没有这一行，wait 后仍像运行中。
    # 新增代码+CodexCliStreamingTest：函数段结束，FakeCodexProcess.terminate 到此结束；如果没有边界说明，用户不容易看出软终止范围。

    def wait(self, timeout: float | None = None) -> int:  # 新增代码+CodexCliStreamingTest：函数段开始，模拟 subprocess.wait；如果没有这段，被测代码无法等待退出。
        self.wait_calls += 1  # 新增代码+CodexCliStreamingTest：记录等待次数；如果没有这一行，强杀后 wait 无法被验证。
        if self.wait_times_out and not self.killed:  # 新增代码+CodexCliStreamingTest：软终止阶段模拟超时；如果没有这一行，kill fallback 不会被触发。
            raise subprocess.TimeoutExpired(cmd="codex", timeout=timeout)  # 新增代码+CodexCliStreamingTest：抛出标准超时异常；如果没有这一行，被测代码不会进入强杀分支。
        self.returncode = self.returncode if self.returncode is not None else -9  # 新增代码+CodexCliStreamingTest：没有退出码时写入强杀退出码；如果没有这一行，wait 后状态不稳定。
        return int(self.returncode)  # 新增代码+CodexCliStreamingTest：返回退出码；如果没有这一行，wait 没有输出。
    # 新增代码+CodexCliStreamingTest：函数段结束，FakeCodexProcess.wait 到此结束；如果没有边界说明，用户不容易看出 wait 范围。

    def kill(self) -> None:  # 新增代码+CodexCliStreamingTest：函数段开始，模拟强制终止；如果没有这段，被测代码无法调用 kill。
        self.killed = True  # 新增代码+CodexCliStreamingTest：记录强杀已执行；如果没有这一行，测试无法确认 fallback。
        self.returncode = -9  # 新增代码+CodexCliStreamingTest：设置强杀退出码；如果没有这一行，进程仍像未退出。
    # 新增代码+CodexCliStreamingTest：函数段结束，FakeCodexProcess.kill 到此结束；如果没有边界说明，用户不容易看出 kill 范围。

    def drain_output(self) -> None:  # 新增代码+CodexCliStreamingTest：函数段开始，模拟清空 stdout/stderr 队列；如果没有这段，被测代码无法证明取消后会丢弃迟到输出。
        self.drained = True  # 新增代码+CodexCliStreamingTest：记录输出已清理；如果没有这一行，测试无法确认 drain 被调用。
    # 新增代码+CodexCliStreamingTest：函数段结束，FakeCodexProcess.drain_output 到此结束；如果没有边界说明，用户不容易看出 drain 范围。
# 新增代码+CodexCliStreamingTest：类段结束，FakeCodexProcess 到此结束；如果没有边界说明，用户不容易看出 fake process 覆盖范围。


class CodexCliStreamingModelCancellationTest(unittest.TestCase):  # 新增代码+CodexCliStreamingTest：测试类段开始，锁定 Codex CLI 取消契约；如果没有这个类，进程级取消容易退化成只改 UI。
    def test_cancel_terminates_process_drains_output_and_emits_events(self) -> None:  # 新增代码+CodexCliStreamingTest：测试软终止成功路径；如果没有这段，cancel 可能不会真正停止子进程。
        from learning_agent.models.codex_cli_stream import CodexCliProcessController  # 新增代码+CodexCliStreamingTest：导入被测进程控制器；如果没有这一行，测试没有执行对象。

        process = FakeCodexProcess(returncode=None)  # 新增代码+CodexCliStreamingTest：创建仍在运行的 fake 进程；如果没有这一行，测试没有目标进程。
        controller = CodexCliProcessController(process, turn_id="turn_a", provider_id="openai", model_id="gpt-5.5", cancel_timeout_seconds=3.0)  # 新增代码+CodexCliStreamingTest：创建绑定 turn/model 的控制器；如果没有这一行，取消事件没有上下文。
        events = controller.cancel(elapsed_ms=42)  # 新增代码+CodexCliStreamingTest：执行取消；如果没有这一行，被测行为不会发生。
        self.assertTrue(process.terminated)  # 新增代码+CodexCliStreamingTest：确认尝试软终止；如果没有这一行，cancel 可能只是改状态。
        self.assertFalse(process.killed)  # 新增代码+CodexCliStreamingTest：确认软终止成功时不强杀；如果没有这一行，取消可能过度杀进程。
        self.assertTrue(process.drained)  # 新增代码+CodexCliStreamingTest：确认输出队列已 drain；如果没有这一行，旧 stdout/stderr 可能继续污染 UI。
        self.assertEqual(["cancel_requested", "cancelled"], [event.phase for event in events])  # 新增代码+CodexCliStreamingTest：确认发出取消请求和取消终态事件；如果没有这一行，GUI 状态条没有完整阶段。
    # 新增代码+CodexCliStreamingTest：测试函数结束，test_cancel_terminates_process_drains_output_and_emits_events 到此结束；如果没有边界说明，用户不容易看出软终止路径。

    def test_cancel_kills_process_after_soft_timeout(self) -> None:  # 新增代码+CodexCliStreamingTest：测试软终止超时后的强杀路径；如果没有这段，卡死子进程会一直占用资源。
        from learning_agent.models.codex_cli_stream import CodexCliProcessController  # 新增代码+CodexCliStreamingTest：导入被测进程控制器；如果没有这一行，测试没有执行对象。

        process = FakeCodexProcess(returncode=None, wait_times_out=True)  # 新增代码+CodexCliStreamingTest：创建 wait 会超时的 fake 进程；如果没有这一行，强杀路径无法触发。
        controller = CodexCliProcessController(process, turn_id="turn_a", provider_id="openai", model_id="gpt-5.5", cancel_timeout_seconds=3.0)  # 新增代码+CodexCliStreamingTest：创建控制器；如果没有这一行，取消没有上下文。
        events = controller.cancel(elapsed_ms=3000)  # 新增代码+CodexCliStreamingTest：执行取消；如果没有这一行，强杀行为不会发生。
        self.assertTrue(process.terminated)  # 新增代码+CodexCliStreamingTest：确认先尝试软终止；如果没有这一行，取消会直接粗暴 kill。
        self.assertTrue(process.killed)  # 新增代码+CodexCliStreamingTest：确认超时后强杀；如果没有这一行，卡死进程不会被处理。
        self.assertGreaterEqual(process.wait_calls, 2)  # 新增代码+CodexCliStreamingTest：确认 kill 后再次等待；如果没有这一行，进程表可能残留。
        self.assertEqual("cancelled", events[-1].phase)  # 新增代码+CodexCliStreamingTest：确认最终仍发 cancelled；如果没有这一行，GUI 可能停在 cancel_requested。
    # 新增代码+CodexCliStreamingTest：测试函数结束，test_cancel_kills_process_after_soft_timeout 到此结束；如果没有边界说明，用户不容易看出强杀路径。

    def test_cancel_is_idempotent_and_already_exited_process_is_noop(self) -> None:  # 新增代码+CodexCliStreamingTest：测试重复取消和已退出进程；如果没有这段，双击取消或进程先退出可能抛异常。
        from learning_agent.models.codex_cli_stream import CodexCliProcessController  # 新增代码+CodexCliStreamingTest：导入被测进程控制器；如果没有这一行，测试没有执行对象。

        process = FakeCodexProcess(exited=True)  # 新增代码+CodexCliStreamingTest：创建已经退出的 fake 进程；如果没有这一行，no-op 路径无法覆盖。
        controller = CodexCliProcessController(process, turn_id="turn_a", provider_id="openai", model_id="gpt-5.5", cancel_timeout_seconds=3.0)  # 新增代码+CodexCliStreamingTest：创建控制器；如果没有这一行，取消没有上下文。
        first_events = controller.cancel(elapsed_ms=0)  # 新增代码+CodexCliStreamingTest：第一次取消已退出进程；如果没有这一行，no-op 行为不会发生。
        second_events = controller.cancel(elapsed_ms=1)  # 新增代码+CodexCliStreamingTest：第二次取消同一进程；如果没有这一行，幂等性没有被验证。
        self.assertFalse(process.terminated)  # 新增代码+CodexCliStreamingTest：确认已退出进程不再 terminate；如果没有这一行，cancel 可能误操作已结束进程。
        self.assertFalse(process.killed)  # 新增代码+CodexCliStreamingTest：确认已退出进程不再 kill；如果没有这一行，no-op 语义不明确。
        self.assertEqual(["cancel_requested", "cancelled"], [event.phase for event in first_events])  # 新增代码+CodexCliStreamingTest：确认第一次仍给 UI 完整终态；如果没有这一行，用户看不到取消闭合。
        self.assertEqual([], second_events)  # 新增代码+CodexCliStreamingTest：确认重复取消无事件且不崩溃；如果没有这一行，双击取消可能重复污染时间线。
    # 新增代码+CodexCliStreamingTest：测试函数结束，test_cancel_is_idempotent_and_already_exited_process_is_noop 到此结束；如果没有边界说明，用户不容易看出幂等路径。
# 新增代码+CodexCliStreamingTest：测试类段结束，CodexCliStreamingModelCancellationTest 到此结束；如果没有边界说明，用户不容易看出取消测试范围。


class CodexCliStreamingRunnerTest(unittest.TestCase):  # 新增代码+CodexCliStreamingTest：测试类段开始，锁定 Codex CLI 可观测 runner 契约；如果没有这个类，慢调用状态可能再次退化成沉默等待。
    def _runner_events(self, *, process: FakeCodexProcess, output_text: str = "", stdout_contains_token_deltas: bool = False):  # 新增代码+CodexCliStreamingTest：helper 段开始，创建 runner 并收集事件；如果没有这段，每个测试都要重复临时目录和上下文参数。
        from learning_agent.models.codex_cli_stream import CodexCliStreamingRunner  # 新增代码+CodexCliStreamingTest：导入被测 runner；如果没有这一行，测试没有执行对象。

        with tempfile.TemporaryDirectory(prefix="codex_cli_runner_test_") as raw_dir:  # 新增代码+CodexCliStreamingTest：创建临时目录；如果没有这一行，测试输出文件会污染仓库。
            output_path = Path(raw_dir) / "last_message.json"  # 新增代码+CodexCliStreamingTest：定义最终输出文件路径；如果没有这一行，runner 没有 fallback 文件。
            if output_text:  # 新增代码+CodexCliStreamingTest：只有需要最终输出时写文件；如果没有这一行，错误测试会被误写成功文件。
                output_path.write_text(json.dumps({"decision_note": "", "text": output_text, "tool_calls": []}, ensure_ascii=False), encoding="utf-8")  # 新增代码+CodexCliStreamingTest：写入结构化最终回答；如果没有这一行，no-delta fallback 没有正文。
            runner = CodexCliStreamingRunner(command=["codex", "exec", "-"], prompt="你好", output_path=output_path, cwd=raw_dir, process_factory=lambda command, cwd: process, stdout_contains_token_deltas=stdout_contains_token_deltas, timeout_seconds=30)  # 新增代码+CodexCliStreamingTest：创建可注入 fake process 的 runner；如果没有这一行，测试会启动真实 CLI。
            return list(runner.stream(turn_id="turn_test", provider_id="openai", model_id="gpt-5.5"))  # 新增代码+CodexCliStreamingTest：收集事件列表；如果没有这一行，测试无法断言阶段。
    # 新增代码+CodexCliStreamingTest：helper 段结束，_runner_events 到此结束；如果没有边界说明，用户不容易看出 runner 构造范围。

    def test_runner_external_cancel_terminates_process_before_cli_finishes(self) -> None:  # 新增代码+CodexCliCancelBridgeTest：测试函数开始，验证 GUI 外部取消能直接终止正在运行的 Codex CLI；如果没有这段，停止按钮可能只改 UI 不停进程。
        from learning_agent.models.codex_cli_stream import CodexCliStreamingRunner  # 新增代码+CodexCliCancelBridgeTest：导入被测 runner；如果没有这一行，测试没有执行对象。

        process = FakeCodexProcess(returncode=None)  # 新增代码+CodexCliCancelBridgeTest：创建仍在运行且不会自然结束的 fake 进程；如果没有这一行，取消测试没有目标。
        with tempfile.TemporaryDirectory(prefix="codex_cli_runner_cancel_test_") as raw_dir:  # 新增代码+CodexCliCancelBridgeTest：创建临时目录；如果没有这一行，测试输出文件会污染仓库。
            output_path = Path(raw_dir) / "last_message.json"  # 新增代码+CodexCliCancelBridgeTest：定义最终输出文件路径；如果没有这一行，runner 构造参数不完整。
            runner = CodexCliStreamingRunner(command=["codex", "exec", "-"], prompt="请写长回答", output_path=output_path, cwd=raw_dir, process_factory=lambda command, cwd: process, timeout_seconds=30)  # 新增代码+CodexCliCancelBridgeTest：创建带 fake 进程的 runner；如果没有这一行，测试会启动真实 Codex CLI。
            events = list(runner.stream(turn_id="turn_cancel", provider_id="openai", model_id="gpt-5.5", is_cancelled=lambda: True))  # 新增代码+CodexCliCancelBridgeTest：用一直为真的 GUI 取消信号运行；如果没有这一行，外部取消入口不会被验证。
        phases = [event.phase for event in events]  # 新增代码+CodexCliCancelBridgeTest：提取所有阶段；如果没有这一行，断言需要重复遍历事件。
        self.assertTrue(process.terminated)  # 新增代码+CodexCliCancelBridgeTest：确认 runner 调用了 terminate；如果没有这一行，取消可能没有真正停止进程。
        self.assertIn("cancel_requested", phases)  # 新增代码+CodexCliCancelBridgeTest：确认取消请求进入事件流；如果没有这一行，GUI 状态栏看不到停止已进入后端。
        self.assertIn("cancelled", phases)  # 新增代码+CodexCliCancelBridgeTest：确认取消终态进入事件流；如果没有这一行，GUI 可能一直显示 cancelling。
        self.assertNotIn("completed", phases)  # 新增代码+CodexCliCancelBridgeTest：确认取消后不会再报完成；如果没有这一行，迟到输出可能覆盖用户取消。
    # 新增代码+CodexCliCancelBridgeTest：测试函数结束，test_runner_external_cancel_terminates_process_before_cli_finishes 到此结束；如果没有边界说明，用户不容易看出它覆盖外部 GUI 取消入口。

    def test_runner_emits_websocket_timeout_from_stderr(self) -> None:  # 新增代码+CodexCliStreamingTest：测试 stderr WebSocket timeout 可见；如果没有这段，用户仍不知道两分钟慢在何处。
        process = FakeCodexProcess(stderr="WARN codex_core::responses::retry: stream disconnected - retrying sampling request\nResponses WebSocket timed out\n")  # 新增代码+CodexCliStreamingTest：构造含 timeout warning 的 fake 进程；如果没有这一行，测试没有慢调用证据输入。
        events = self._runner_events(process=process, output_text="完成")  # 新增代码+CodexCliStreamingTest：执行 runner；如果没有这一行，被测行为不会发生。
        self.assertIn("websocket_timeout", [event.phase for event in events])  # 新增代码+CodexCliStreamingTest：确认 timeout 阶段进入事件流；如果没有这一行，GUI 可能继续沉默等待。
    # 新增代码+CodexCliStreamingTest：测试函数结束，test_runner_emits_websocket_timeout_from_stderr 到此结束；如果没有边界说明，用户不容易看出 timeout 测试范围。

    def test_runner_emits_https_fallback_from_stderr(self) -> None:  # 新增代码+CodexCliStreamingTest：测试 HTTPS fallback 可见；如果没有这段，用户不知道后端已经切换传输。
        process = FakeCodexProcess(stderr="warning: Falling back from WebSockets to HTTPS transport. request timed out\n")  # 新增代码+CodexCliStreamingTest：构造含 fallback warning 的 fake 进程；如果没有这一行，测试没有传输切换输入。
        events = self._runner_events(process=process, output_text="完成")  # 新增代码+CodexCliStreamingTest：执行 runner；如果没有这一行，被测行为不会发生。
        self.assertIn("https_fallback", [event.phase for event in events])  # 新增代码+CodexCliStreamingTest：确认 fallback 阶段进入事件流；如果没有这一行，状态面板无法解释切换。
    # 新增代码+CodexCliStreamingTest：测试函数结束，test_runner_emits_https_fallback_from_stderr 到此结束；如果没有边界说明，用户不容易看出 fallback 测试范围。

    def test_runner_emits_stdout_delta_when_discovery_allows_deltas(self) -> None:  # 新增代码+CodexCliStreamingTest：测试已验证 stdout delta 时能冒泡正文；如果没有这段，未来 CLI delta 证据出现后也无法显示。
        stdout = json.dumps({"type": "response.output_text.delta", "delta": "pong"}, ensure_ascii=False) + "\n"  # 新增代码+CodexCliStreamingTest：构造标准 delta JSONL；如果没有这一行，测试没有正文增量输入。
        process = FakeCodexProcess(stdout=stdout)  # 新增代码+CodexCliStreamingTest：创建带 stdout delta 的 fake 进程；如果没有这一行，runner 没有输出来源。
        events = self._runner_events(process=process, stdout_contains_token_deltas=True)  # 新增代码+CodexCliStreamingTest：允许解析 stdout delta 并执行；如果没有这一行，门禁会按当前 discovery 禁止 delta。
        self.assertEqual(["pong"], [event.message for event in events if event.event_type == "delta"])  # 新增代码+CodexCliStreamingTest：确认 delta 正文进入事件流；如果没有这一行，聊天区可能没有流式输出。
        self.assertTrue(events[-1].metadata["token_streaming_verified"])  # 新增代码+CodexCliStreamingTest：确认完成事件标记真 delta 已验证；如果没有这一行，UI 无法区分真 token 流和最终文件 fallback。
    # 新增代码+CodexCliStreamingTest：测试函数结束，test_runner_emits_stdout_delta_when_discovery_allows_deltas 到此结束；如果没有边界说明，用户不容易看出 delta 测试范围。

    def test_runner_reads_final_output_file_when_stdout_has_no_deltas(self) -> None:  # 新增代码+CodexCliStreamingTest：测试当前 discovery 无 delta 时读取最终文件；如果没有这段，Codex CLI 成功后可能没有回答。
        stdout = json.dumps({"type": "turn.started"}, ensure_ascii=False) + "\n"  # 新增代码+CodexCliStreamingTest：构造只有生命周期事件的 stdout；如果没有这一行，测试不能证明 lifecycle 不会被误当正文。
        process = FakeCodexProcess(stdout=stdout)  # 新增代码+CodexCliStreamingTest：创建 fake 进程；如果没有这一行，runner 没有输出来源。
        events = self._runner_events(process=process, output_text="最终回答", stdout_contains_token_deltas=False)  # 新增代码+CodexCliStreamingTest：按当前 discovery 禁止 stdout delta 并提供最终文件；如果没有这一行，fallback 路径不会执行。
        self.assertEqual(["最终回答"], [event.message for event in events if event.event_type == "delta"])  # 新增代码+CodexCliStreamingTest：确认最终文件作为一次 delta 进入聊天区；如果没有这一行，用户看不到回答。
        self.assertFalse(events[-1].metadata["token_streaming_verified"])  # 新增代码+CodexCliStreamingTest：确认完成事件不声称真 token streaming；如果没有这一行，产品会误导用户。
    # 新增代码+CodexCliStreamingTest：测试函数结束，test_runner_reads_final_output_file_when_stdout_has_no_deltas 到此结束；如果没有边界说明，用户不容易看出 no-delta fallback 范围。

    def test_runner_emits_error_for_non_zero_exit(self) -> None:  # 新增代码+CodexCliStreamingTest：测试非零退出快速失败；如果没有这段，CLI 错误可能被误当完成。
        process = FakeCodexProcess(stderr="model not supported\n", returncode=2)  # 新增代码+CodexCliStreamingTest：构造失败进程；如果没有这一行，错误路径没有输入样本。
        events = self._runner_events(process=process)  # 新增代码+CodexCliStreamingTest：执行 runner；如果没有这一行，被测行为不会发生。
        self.assertEqual("error", events[-1].event_type)  # 新增代码+CodexCliStreamingTest：确认最后是错误事件；如果没有这一行，失败可能被误报成功。
        self.assertEqual("failed", events[-1].phase)  # 新增代码+CodexCliStreamingTest：确认错误阶段为 failed；如果没有这一行，前端状态机无法闭合失败。
        self.assertIn("model not supported", events[-1].message)  # 新增代码+CodexCliStreamingTest：确认 stderr 详情保留；如果没有这一行，用户无法知道模型不可用。
    # 新增代码+CodexCliStreamingTest：测试函数结束，test_runner_emits_error_for_non_zero_exit 到此结束；如果没有边界说明，用户不容易看出失败路径范围。

    def test_codex_cli_chat_model_stream_chat_uses_observable_runner(self) -> None:  # 新增代码+CodexCliStreamingTest：测试 CodexCliChatModel 已接入 streaming runner；如果没有这段，GUI 仍可能走阻塞 chat。
        from learning_agent.models.adapters import CodexCliChatModel  # 新增代码+CodexCliStreamingTest：导入真实 CLI 模型适配器；如果没有这一行，测试无法覆盖 adapter 接线。

        with tempfile.TemporaryDirectory(prefix="codex_cli_model_stream_test_") as raw_dir:  # 新增代码+CodexCliStreamingTest：创建临时工作目录；如果没有这一行，测试会污染仓库。
            def process_factory(command: list[str], cwd: Path) -> FakeCodexProcess:  # 新增代码+CodexCliStreamingTest：函数段开始，根据命令写入最终输出文件；如果没有这段，模型 stream_chat 的 output_path 无法被测试控制。
                output_index = command.index("--output-last-message") + 1  # 新增代码+CodexCliStreamingTest：定位 output-last-message 参数值；如果没有这一行，测试无法知道 runner 会读哪个文件。
                Path(command[output_index]).write_text(json.dumps({"decision_note": "", "text": "来自 runner", "tool_calls": []}, ensure_ascii=False), encoding="utf-8")  # 新增代码+CodexCliStreamingTest：写入最终回答文件；如果没有这一行，stream_chat 没有 fallback 文本。
                return FakeCodexProcess(stderr="warning: Falling back from WebSockets to HTTPS transport. request timed out\n")  # 新增代码+CodexCliStreamingTest：返回含 fallback warning 的 fake 进程；如果没有这一行，状态阶段无法被验证。
            # 新增代码+CodexCliStreamingTest：函数段结束，process_factory 到此结束；如果没有边界说明，用户不容易看出 fake 工厂范围。
            model = CodexCliChatModel(codex_command="codex", model="gpt-5.5", cwd=raw_dir, process_factory=process_factory)  # 新增代码+CodexCliStreamingTest：创建带 fake process 的 CLI 模型；如果没有这一行，测试会启动真实 Codex CLI。
            events = list(model.stream_chat([{"role": "user", "content": "你好"}], [], turn_id="turn_model", provider_id="openai", model_id="gpt-5.5"))  # 新增代码+CodexCliStreamingTest：执行 stream_chat；如果没有这一行，adapter 接线不会被验证。
        self.assertIn("https_fallback", [event.phase for event in events])  # 新增代码+CodexCliStreamingTest：确认 CLI stderr 阶段通过模型冒泡；如果没有这一行，GUI 看不到 transport fallback。
        self.assertEqual(["来自 runner"], [event.message for event in events if event.event_type == "delta"])  # 新增代码+CodexCliStreamingTest：确认最终文件文本通过 stream_chat 输出；如果没有这一行，GUI 聊天区拿不到回答。
    # 新增代码+CodexCliStreamingTest：测试函数结束，test_codex_cli_chat_model_stream_chat_uses_observable_runner 到此结束；如果没有边界说明，用户不容易看出 adapter 接线范围。

    def test_codex_cli_chat_model_stream_chat_passes_cancel_checker_to_runner(self) -> None:  # 新增代码+CodexCliCancelBridgeTest：测试函数开始，验证模型入口会把 GUI 取消信号传给 runner；如果没有这段，adapter 虽然传参但 CodexCliChatModel 可能丢掉。
        from learning_agent.models.adapters import CodexCliChatModel  # 新增代码+CodexCliCancelBridgeTest：导入真实 CLI 模型适配器；如果没有这一行，测试无法覆盖 stream_chat 接线。

        process = FakeCodexProcess(returncode=None)  # 新增代码+CodexCliCancelBridgeTest：创建仍在运行的 fake 进程；如果没有这一行，取消信号没有可终止对象。
        with tempfile.TemporaryDirectory(prefix="codex_cli_model_cancel_test_") as raw_dir:  # 新增代码+CodexCliCancelBridgeTest：创建临时工作目录；如果没有这一行，测试会污染仓库。
            model = CodexCliChatModel(codex_command="codex", model="gpt-5.5", cwd=raw_dir, process_factory=lambda command, cwd: process)  # 新增代码+CodexCliCancelBridgeTest：创建带 fake process 的 CLI 模型；如果没有这一行，测试会启动真实 Codex CLI。
            events = list(model.stream_chat([{"role": "user", "content": "请写长回答"}], [], turn_id="turn_model_cancel", provider_id="openai", model_id="gpt-5.5", is_cancelled=lambda: True))  # 新增代码+CodexCliCancelBridgeTest：执行带取消回调的 stream_chat；如果没有这一行，模型到 runner 的取消传递不会被验证。
        phases = [event.phase for event in events]  # 新增代码+CodexCliCancelBridgeTest：提取事件阶段；如果没有这一行，后续断言会重复遍历。
        self.assertTrue(process.terminated)  # 新增代码+CodexCliCancelBridgeTest：确认取消信号最终终止 fake 进程；如果没有这一行，模型入口可能吞掉取消回调。
        self.assertIn("cancelled", phases)  # 新增代码+CodexCliCancelBridgeTest：确认取消终态冒泡到模型事件；如果没有这一行，adapter 无法把 GUI 切到 cancelled。
        self.assertNotIn("completed", phases)  # 新增代码+CodexCliCancelBridgeTest：确认取消后不再发完成；如果没有这一行，GUI 可能显示“已完成”误导用户。
    # 新增代码+CodexCliCancelBridgeTest：测试函数结束，test_codex_cli_chat_model_stream_chat_passes_cancel_checker_to_runner 到此结束；如果没有边界说明，用户不容易看出模型入口取消合同。
# 新增代码+CodexCliStreamingTest：测试类段结束，CodexCliStreamingRunnerTest 到此结束；如果没有边界说明，用户不容易看出 runner 测试范围。


if __name__ == "__main__":  # 新增代码+CodexCliStreamingTest：允许直接运行本测试文件；如果没有这一行，手动排查时不会自动启动 unittest。
    unittest.main()  # 新增代码+CodexCliStreamingTest：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行测试。
