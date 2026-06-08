"""浏览器动作执行器测试，锁定 Stage 6 的串行写操作和事件流。"""  # 新增代码+BrowserActionStage6: 说明本测试覆盖动作执行协议；若没有这行代码，测试目的不清楚。

from learning_agent.tests.support import *  # 新增代码+BrowserActionStage6: 复用项目测试基础设施；若没有这行代码，临时目录和断言工具需要重复导入。

from learning_agent.browser.action_executor import BrowserActionExecutor  # 新增代码+BrowserActionStage6: 导入待实现动作执行器；若没有这行代码，测试无法驱动事件流。
from learning_agent.browser.action_policy import BrowserActionPolicy  # 新增代码+BrowserActionStage6: 导入动作策略；若没有这行代码，串行/并发分类无法验证。
from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+BrowserActionStage6: 导入真实 store；若没有这行代码，事件落盘无法验证。


class BrowserActionStage6Tests(unittest.TestCase):  # 新增代码+BrowserActionStage6: 定义 Stage 6 测试类；若没有这行代码，unittest 无法收集断言。
    def test_policy_marks_reads_concurrent_and_writes_serial(self) -> None:  # 新增代码+BrowserActionStage6: 验证工具并发策略；若没有这行代码，读写工具可能被同等并发执行。
        policy = BrowserActionPolicy()  # 新增代码+BrowserActionStage6: 创建策略对象；若没有这行代码，测试没有执行对象。
        self.assertTrue(policy.is_concurrent_safe("browser_snapshot"))  # 新增代码+BrowserActionStage6: 快照是只读操作可并发；若没有这行代码，状态页读取会被无谓串行化。
        self.assertFalse(policy.is_concurrent_safe("browser_click"))  # 新增代码+BrowserActionStage6: 点击是写操作必须串行；若没有这行代码，多个点击可能互相打架。
        self.assertTrue(policy.requires_serial("browser_type"))  # 新增代码+BrowserActionStage6: 输入是写操作必须串行；若没有这行代码，真实表单可能被并发输入污染。

    def test_executor_accepts_stable_action_id_from_runtime_store(self) -> None:  # 新增代码+BrowserActionExecutorDelegation: 锁定执行器能复用 server 分配的稳定 action_id；若没有这行代码，server 委托后会退回随机动作编号。
        executor = BrowserActionExecutor()  # 新增代码+BrowserActionExecutorDelegation: 创建内存执行器；若没有这行代码，测试没有可调用对象。
        action = executor.begin_action("run-1", "browser_wait", "browser_wait", {"milliseconds": 1}, action_id="run-1-action-1")  # 新增代码+BrowserActionExecutorDelegation: 用调用方指定 id 开始动作；若没有这行代码，无法证明 action id 不会漂移。
        self.assertEqual(action.action_id, "run-1-action-1")  # 新增代码+BrowserActionExecutorDelegation: 断言执行器保留稳定 id；若没有这行代码，后续 observation 和 action 文件可能断链。
        self.assertEqual(executor.events[-1]["action_id"], "run-1-action-1")  # 新增代码+BrowserActionExecutorDelegation: 断言事件也使用同一个 id；若没有这行代码，状态事件和动作文件可能不一致。

    def test_executor_emits_started_progress_completed_and_failed_events(self) -> None:  # 新增代码+BrowserActionStage6: 验证执行器事件生命周期；若没有这行代码，工具流式状态不可审计。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+BrowserActionStage6: 使用临时 store 隔离事件；若没有这行代码，测试会污染真实状态。
            store = BrowserRuntimeStore(Path(temp_dir) / "browser_runtime")  # 新增代码+BrowserActionStage6: 创建真实 browser store；若没有这行代码，无法验证落盘事件。
            store.create_run(run_id="run-1", session_id="session-1")  # 新增代码+BrowserActionStage6: 创建浏览器 run；若没有这行代码，action 无法挂到任务。
            executor = BrowserActionExecutor(store=store)  # 新增代码+BrowserActionStage6: 创建接入 store 的执行器；若没有这行代码，事件不会落盘。
            action = executor.begin_action("run-1", "stage-1", "browser_click", {"selector": "#ok"})  # 新增代码+BrowserActionStage6: 开始一个点击动作；若没有这行代码，后续事件没有 action id。
            executor.record_progress(action, "waiting_for_locator")  # 新增代码+BrowserActionStage6: 记录中间进度；若没有这行代码，长工具没有流式状态。
            executor.complete_action(action, observation_id="obs-1")  # 新增代码+BrowserActionStage6: 标记动作完成；若没有这行代码，完成事件不会出现。
            failed = executor.begin_action("run-1", "stage-1", "browser_type", {"selector": "#name", "text": "abc"})  # 新增代码+BrowserActionStage6: 开始第二个动作；若没有这行代码，失败分支无法验证。
            executor.fail_action(failed, "locator_not_found", "找不到元素")  # 新增代码+BrowserActionStage6: 标记失败；若没有这行代码，失败事件不可审计。
            event_types = [event["event_type"] for event in store.tail_events("run-1", limit=20)]  # 新增代码+BrowserActionStage6: 读取事件类型序列；若没有这行代码，断言没有事件输入。
            self.assertIn("browser_action_started", event_types)  # 新增代码+BrowserActionStage6: 验证 started 事件；若没有这行代码，工具开始不可见。
            self.assertIn("browser_action_progress", event_types)  # 新增代码+BrowserActionStage6: 验证 progress 事件；若没有这行代码，长工具中间状态不可见。
            self.assertIn("browser_action_completed", event_types)  # 新增代码+BrowserActionStage6: 验证 completed 事件；若没有这行代码，结果回灌缺少依据。
            self.assertIn("browser_action_failed", event_types)  # 新增代码+BrowserActionStage6: 验证 failed 事件；若没有这行代码，恢复策略没有失败证据。

    def test_executor_can_mark_interrupted_actions(self) -> None:  # 新增代码+BrowserActionStage6: 验证中断状态；若没有这行代码，进程退出后无法区别中断和失败。
        executor = BrowserActionExecutor()  # 新增代码+BrowserActionStage6: 创建内存执行器；若没有这行代码，测试没有执行对象。
        action = executor.begin_action("run-1", "stage-1", "browser_open", {"url": "https://example.test"})  # 新增代码+BrowserActionStage6: 开始动作；若没有这行代码，中断分支没有目标。
        executor.interrupt_action(action, "process_exit")  # 新增代码+BrowserActionStage6: 标记中断；若没有这行代码，动作不会进入 interrupted 状态。
        self.assertEqual(action.status, "interrupted")  # 新增代码+BrowserActionStage6: 验证动作状态；若没有这行代码，中断可能被当成失败。
        self.assertEqual(executor.events[-1]["event_type"], "browser_action_interrupted")  # 新增代码+BrowserActionStage6: 验证内存事件；若没有这行代码，无 store 模式无法被调试。

    def test_execute_action_retries_and_records_progress_events(self) -> None:  # 新增代码+BrowserActionExecuteLayer: 验证执行器能接管真实调用、重试和进度事件；若没有这行代码，executor 仍只是记录员。
        executor = BrowserActionExecutor()  # 新增代码+BrowserActionExecuteLayer: 创建内存执行器；若没有这行代码，测试没有执行对象。
        attempts = {"count": 0}  # 新增代码+BrowserActionExecuteLayer: 保存 handler 调用次数；若没有这行代码，无法证明发生了重试。
        def flaky_handler(arguments: dict[str, object]) -> str:  # 新增代码+BrowserActionExecuteLayer: 定义第一次失败第二次成功的真实 handler；若没有这行代码，重试路径没有可控输入。
            attempts["count"] += 1  # 新增代码+BrowserActionExecuteLayer: 记录当前尝试次数；若没有这行代码，断言无法知道执行几次。
            if attempts["count"] == 1:  # 新增代码+BrowserActionExecuteLayer: 第一次故意失败；若没有这行代码，retry 分支不会被覆盖。
                raise RuntimeError("timeout while waiting")  # 新增代码+BrowserActionExecuteLayer: 抛出可重试错误；若没有这行代码，执行器不会进入重试逻辑。
            return f"ok:{arguments['value']}"  # 新增代码+BrowserActionExecuteLayer: 第二次返回成功结果；若没有这行代码，完成分支没有输出。
        result, action = executor.execute_action("run-1", "stage-1", "browser_wait", {"value": "done"}, flaky_handler, action_id="run-1-action-1", attempts_limit=2, is_retryable_error=lambda error: "timeout" in str(error).lower(), classify_error=lambda error: "navigation_timeout")  # 新增代码+BrowserActionExecuteLayer: 通过执行器执行并允许一次重试；若没有这行代码，测试无法驱动新执行层入口。
        event_types = [event["event_type"] for event in executor.events]  # 新增代码+BrowserActionExecuteLayer: 收集执行器内存事件；若没有这行代码，断言无法检查进度和完成事件。
        self.assertEqual(result, "ok:done")  # 新增代码+BrowserActionExecuteLayer: 断言最终返回 handler 结果；若没有这行代码，执行层可能吞掉输出。
        self.assertEqual(action.status, "completed")  # 新增代码+BrowserActionExecuteLayer: 断言动作最终完成；若没有这行代码，重试成功后状态可能仍是 running。
        self.assertEqual(attempts["count"], 2)  # 新增代码+BrowserActionExecuteLayer: 断言确实执行了两次；若没有这行代码，重试可能没有发生。
        self.assertIn("browser_action_progress", event_types)  # 新增代码+BrowserActionExecuteLayer: 断言失败重试会写 progress；若没有这行代码，用户看不到中间恢复过程。
        self.assertEqual(event_types[-1], "browser_action_completed")  # 新增代码+BrowserActionExecuteLayer: 断言最后是完成事件；若没有这行代码，事件流收尾可能错误。

    def test_execute_action_uses_serial_lock_for_write_tools_only(self) -> None:  # 新增代码+BrowserActionExecuteLayer: 验证写工具串行、读工具不串行；若没有这行代码，并发安全边界可能被破坏。
        class RecordingLock:  # 新增代码+BrowserActionExecuteLayer: 定义可观察的锁；若没有这个类，测试无法知道是否进入串行锁。
            def __init__(self) -> None:  # 新增代码+BrowserActionExecuteLayer: 初始化锁事件列表；若没有这行代码，锁没有地方记录调用。
                self.events: list[str] = []  # 新增代码+BrowserActionExecuteLayer: 保存 enter/exit 顺序；若没有这行代码，断言没有数据来源。
            def __enter__(self) -> "RecordingLock":  # 新增代码+BrowserActionExecuteLayer: 模拟锁进入；若没有这行代码，with 语句无法使用假锁。
                self.events.append("enter")  # 新增代码+BrowserActionExecuteLayer: 记录进入锁；若没有这行代码，无法证明写工具被串行。
                return self  # 新增代码+BrowserActionExecuteLayer: 返回自身满足上下文协议；若没有这行代码，with 语义不完整。
            def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:  # 新增代码+BrowserActionExecuteLayer: 模拟锁退出；若没有这行代码，with 语句退出会失败。
                self.events.append("exit")  # 新增代码+BrowserActionExecuteLayer: 记录退出锁；若没有这行代码，无法证明锁被释放。
                return False  # 新增代码+BrowserActionExecuteLayer: 不吞异常；若没有这行代码，失败路径可能被隐藏。
        executor = BrowserActionExecutor()  # 新增代码+BrowserActionExecuteLayer: 创建执行器；若没有这行代码，测试没有执行对象。
        lock = RecordingLock()  # 新增代码+BrowserActionExecuteLayer: 创建假锁；若没有这行代码，无法观察锁行为。
        executor.write_lock = lock  # 新增代码+BrowserActionExecuteLayer: 替换执行器写锁；若没有这行代码，测试只能依赖真实线程锁不可观察。
        executor.execute_action("run-1", "stage-1", "browser_click", {}, lambda arguments: "clicked")  # 新增代码+BrowserActionExecuteLayer: 执行写工具；若没有这行代码，串行锁分支不会被触发。
        self.assertEqual(lock.events, ["enter", "exit"])  # 新增代码+BrowserActionExecuteLayer: 断言写工具使用锁；若没有这行代码，点击输入可能并发污染页面。
        lock.events.clear()  # 新增代码+BrowserActionExecuteLayer: 清空记录准备读工具断言；若没有这行代码，读工具会继承旧记录。
        executor.execute_action("run-1", "stage-1", "browser_snapshot", {}, lambda arguments: "snapshot")  # 新增代码+BrowserActionExecuteLayer: 执行只读工具；若没有这行代码，读工具不串行无法验证。
        self.assertEqual(lock.events, [])  # 新增代码+BrowserActionExecuteLayer: 断言只读工具不使用写锁；若没有这行代码，快照类读取会被无谓阻塞。

    def test_browser_server_delegates_action_lifecycle_to_executor(self) -> None:  # 新增代码+BrowserActionExecutorDelegation: 验证生产 server 的动作生命周期由执行器接管；若没有这行代码，旧 wrapper 会继续和 executor 双轨运行。
        from learning_agent.browser.runtime_models import BrowserAction  # 新增代码+BrowserActionExecutorDelegation: 导入动作模型给 spy 执行器返回真实 action；若没有这行代码，server 收尾无法使用协议对象。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserActionExecutorDelegation: 导入真实浏览器 server；若没有这行代码，测试无法覆盖生产入口。
        class RecordingExecutor(BrowserActionExecutor):  # 修改代码+BrowserActionExecuteLayer: 让 spy 继承真实执行器以获得 execute_action 入口；若没有这行代码，server 接管真实执行后旧 spy 会缺少方法而崩溃。
            def __init__(self) -> None:  # 新增代码+BrowserActionExecutorDelegation: 初始化调用记录；若没有这行代码，spy 没地方保存证据。
                super().__init__()  # 修改代码+BrowserActionExecuteLayer: 复用真实执行器的 execute_action、策略和串行锁；若没有这行代码，spy 只能记录生命周期不能执行真实 handler。
                self.calls: list[tuple[str, str]] = []  # 新增代码+BrowserActionExecutorDelegation: 保存 begin/complete/fail 调用；若没有这行代码，断言无法判断委托是否发生。
            def begin_action(self, run_id: str, stage_id: str, tool_name: str, arguments: dict[str, object] | None = None, action_id: str | None = None) -> BrowserAction:  # 新增代码+BrowserActionExecutorDelegation: 模拟执行器开始动作接口；若没有这行代码，server 无法把动作委托给 spy。
                safe_action_id = action_id or f"{run_id}-spy-action"  # 新增代码+BrowserActionExecutorDelegation: 复用 server 传入的稳定 id；若没有这行代码，测试不能证明 id 被传递。
                self.calls.append(("begin", safe_action_id))  # 新增代码+BrowserActionExecutorDelegation: 记录开始调用；若没有这行代码，委托证据会丢失。
                action = BrowserAction.create(run_id=run_id, stage_id=stage_id, tool_name=tool_name, arguments=arguments, action_id=safe_action_id)  # 新增代码+BrowserActionExecutorDelegation: 创建真实 action；若没有这行代码，server complete helper 没有对象可处理。
                action.mark_started()  # 新增代码+BrowserActionExecutorDelegation: 标记 action 已开始；若没有这行代码，动作状态和生产执行器不一致。
                return action  # 新增代码+BrowserActionExecutorDelegation: 返回 action 给 server；若没有这行代码，server 调用会拿到 None。
            def complete_action(self, action: BrowserAction, observation_id: str = "") -> BrowserAction:  # 新增代码+BrowserActionExecutorDelegation: 模拟执行器成功收尾接口；若没有这行代码，server 无法委托完成事件。
                self.calls.append(("complete", observation_id or action.action_id))  # 新增代码+BrowserActionExecutorDelegation: 记录完成调用和证据 id；若没有这行代码，无法确认 complete 走了 executor。
                action.mark_completed(observation_id=observation_id)  # 新增代码+BrowserActionExecutorDelegation: 更新动作状态；若没有这行代码，server 后续看到的 action 状态不正确。
                return action  # 新增代码+BrowserActionExecutorDelegation: 返回更新后的 action；若没有这行代码，接口和真实 executor 不一致。
            def fail_action(self, action: BrowserAction, error_type: str, error_message: str) -> BrowserAction:  # 新增代码+BrowserActionExecutorDelegation: 模拟执行器失败收尾接口；若没有这行代码，失败路径无法同样委托。
                self.calls.append(("fail", error_type))  # 新增代码+BrowserActionExecutorDelegation: 记录失败分类；若没有这行代码，失败委托无法断言。
                action.mark_failed(error_type, error_message)  # 新增代码+BrowserActionExecutorDelegation: 更新失败状态；若没有这行代码，接口和真实 executor 不一致。
                return action  # 新增代码+BrowserActionExecutorDelegation: 返回失败动作；若没有这行代码，server 容错路径可能拿不到对象。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserActionExecutorDelegation: 使用临时 workspace 隔离 runtime store；若没有这行代码，测试会污染真实项目 memory。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserActionExecutorDelegation: 创建真实 server；若没有这行代码，无法覆盖公开 call 入口。
            recorder = RecordingExecutor()  # 新增代码+BrowserActionExecutorDelegation: 创建 spy 执行器；若没有这行代码，server 没有可替换对象。
            server.browser_action_executor = recorder  # 新增代码+BrowserActionExecutorDelegation: 替换 server 执行器依赖；若没有这行代码，测试无法证明 server 是否真的委托。
            server.browser_wait = lambda arguments: "browser_wait 成功\npage_id=page-1"  # 新增代码+BrowserActionExecutorDelegation: 用假等待避免真实 sleep；若没有这行代码，测试会变慢。
            result = server.call("browser_wait", {"milliseconds": 1})  # 新增代码+BrowserActionExecutorDelegation: 通过公开入口触发生命周期；若没有这行代码，helper 不会执行。
        self.assertIn("browser_wait 成功", result)  # 新增代码+BrowserActionExecutorDelegation: 断言原工具结果仍返回；若没有这行代码，委托可能破坏工具输出。
        self.assertEqual([call_name for call_name, _ in recorder.calls], ["begin", "complete"])  # 新增代码+BrowserActionExecutorDelegation: 断言 begin 和 complete 都经过 executor；若没有这行代码，旧手写 wrapper 不会被发现。
        self.assertEqual(recorder.calls[0][1], recorder.calls[1][1])  # 新增代码+BrowserActionExecutorDelegation: 断言完成事件沿用同一个 action id；若没有这行代码，完成事件可能和开始事件断链。

    def test_browser_server_delegates_actual_tool_execution_to_executor(self) -> None:  # 新增代码+BrowserActionExecuteLayer: 验证生产 server 的真实工具调用由 executor.execute_action 接管；若没有这行代码，executor 仍不是调度员。
        from learning_agent.browser.runtime_models import BrowserAction  # 新增代码+BrowserActionExecuteLayer: 导入动作模型给 spy 执行器返回真实 action；若没有这行代码，server 无法完成测试调用。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserActionExecuteLayer: 导入真实 server；若没有这行代码，测试无法覆盖公开 call。
        class RecordingExecutionExecutor(BrowserActionExecutor):  # 新增代码+BrowserActionExecuteLayer: 继承真实执行器并记录 execute_action；若没有这个类，测试无法证明公开 call 走了新执行层。
            def __init__(self, store: BrowserRuntimeStore) -> None:  # 新增代码+BrowserActionExecuteLayer: 初始化 spy 执行器；若没有这行代码，无法传入真实 store。
                super().__init__(store=store)  # 新增代码+BrowserActionExecuteLayer: 复用真实事件落盘能力；若没有这行代码，spy 行为会偏离生产执行器。
                self.executed_tools: list[str] = []  # 新增代码+BrowserActionExecuteLayer: 保存 execute_action 调用过的工具名；若没有这行代码，断言没有证据。
            def execute_action(self, run_id: str, stage_id: str, tool_name: str, arguments: dict[str, object] | None, handler: object, **kwargs: object) -> tuple[str, BrowserAction]:  # 新增代码+BrowserActionExecuteLayer: 拦截生产调用并保持接口兼容；若没有这行代码，server 是否委托不可观察。
                self.executed_tools.append(tool_name)  # 新增代码+BrowserActionExecuteLayer: 记录被执行工具名；若没有这行代码，无法证明 browser_wait 进入 executor。
                return super().execute_action(run_id, stage_id, tool_name, arguments, handler, **kwargs)  # 新增代码+BrowserActionExecuteLayer: 继续走真实执行逻辑；若没有这行代码，测试无法同时验证功能输出。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserActionExecuteLayer: 使用临时工作区隔离 memory；若没有这行代码，测试会污染真实 runtime。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserActionExecuteLayer: 创建真实 server；若没有这行代码，公开 call 无法执行。
            recorder = RecordingExecutionExecutor(server.browser_runtime_store)  # 新增代码+BrowserActionExecuteLayer: 创建带真实 store 的执行器 spy；若没有这行代码，server 没有可替换执行器。
            server.browser_action_executor = recorder  # 新增代码+BrowserActionExecuteLayer: 替换执行器依赖；若没有这行代码，测试无法观察委托。
            server.browser_wait = lambda arguments: "browser_wait 成功\npage_id=page-1"  # 新增代码+BrowserActionExecuteLayer: 用假 wait 避免真实等待；若没有这行代码，测试变慢且不稳定。
            result = server.call("browser_wait", {"milliseconds": 1})  # 新增代码+BrowserActionExecuteLayer: 通过公开入口执行工具；若没有这行代码，新执行层不会被触发。
        self.assertEqual(recorder.executed_tools, ["browser_wait"])  # 新增代码+BrowserActionExecuteLayer: 断言工具实际执行进入 executor；若没有这行代码，server 可能继续直接调用 handler。
        self.assertIn("browser_wait 成功", result)  # 新增代码+BrowserActionExecuteLayer: 断言工具结果保持兼容；若没有这行代码，执行层可能破坏原输出。

    def test_execute_action_streams_iterable_result_chunks_as_progress(self) -> None:  # 新增代码+BrowserActionStreaming: 验证执行器能把分段工具输出写成流式进度；若没有这行代码，长工具只能等最终结果才可见。
        executor = BrowserActionExecutor()  # 新增代码+BrowserActionStreaming: 创建内存执行器；若没有这行代码，测试没有执行对象。
        chunks: list[str] = []  # 新增代码+BrowserActionStreaming: 保存回调收到的分段文本；若没有这行代码，无法证明流式结果回调触发。
        def streaming_handler(arguments: dict[str, object]) -> list[str]:  # 新增代码+BrowserActionStreaming: 定义返回分段结果的假工具；若没有这行代码，execute_action 没有流式输入。
            return [f"{arguments['prefix']}-1", f"{arguments['prefix']}-2"]  # 新增代码+BrowserActionStreaming: 返回两个文本片段；若没有这行代码，流式事件数量无法验证。
        result, action = executor.execute_action("run-1", "stage-1", "browser_snapshot", {"prefix": "chunk"}, streaming_handler, on_result_chunk=lambda current_action, chunk_index, chunk_text: chunks.append(f"{current_action.action_id}:{chunk_index}:{chunk_text}"))  # 新增代码+BrowserActionStreaming: 执行分段工具并收集 chunk 回调；若没有这行代码，测试无法驱动新流式接口。
        progress_payloads = [event["payload"] for event in executor.events if event["event_type"] == "browser_action_progress"]  # 新增代码+BrowserActionStreaming: 提取所有 progress payload；若没有这行代码，无法断言 result_chunk 事件。
        self.assertEqual(result, "chunk-1chunk-2")  # 新增代码+BrowserActionStreaming: 断言分段结果会合并成原有文本返回；若没有这行代码，MCP 兼容输出可能被破坏。
        self.assertEqual(action.status, "completed")  # 新增代码+BrowserActionStreaming: 断言流式输出后动作仍正常完成；若没有这行代码，分段路径可能漏掉 complete。
        self.assertEqual(chunks, [f"{action.action_id}:1:chunk-1", f"{action.action_id}:2:chunk-2"])  # 新增代码+BrowserActionStreaming: 断言调用方能逐段接收输出；若没有这行代码，上层 UI/SDK 无法流式展示。
        self.assertIn("result_chunk", [payload["message"] for payload in progress_payloads])  # 新增代码+BrowserActionStreaming: 断言事件流包含分段输出标记；若没有这行代码，流式事件落盘缺失不会被发现。

    def test_execute_batch_runs_concurrent_safe_read_actions_in_parallel(self) -> None:  # 新增代码+BrowserActionBatch: 验证只读浏览器动作能批量并发执行；若没有这行代码，批处理可能仍是串行空壳。
        executor = BrowserActionExecutor()  # 新增代码+BrowserActionBatch: 创建内存执行器；若没有这行代码，测试没有执行对象。
        first_started = threading.Event()  # 新增代码+BrowserActionBatch: 记录第一个 handler 已进入；若没有这行代码，无法协调并发观察。
        second_started = threading.Event()  # 新增代码+BrowserActionBatch: 记录第二个 handler 已进入；若没有这行代码，第一个 handler 无法确认并发。
        def first_handler(arguments: dict[str, object]) -> str:  # 新增代码+BrowserActionBatch: 定义第一个只读工具 handler；若没有这行代码，批量执行缺少第一个动作。
            del arguments  # 新增代码+BrowserActionBatch: 明确测试不使用参数；若没有这行代码，未使用参数意图不清楚。
            first_started.set()  # 新增代码+BrowserActionBatch: 标记第一个 handler 已启动；若没有这行代码，第二个 handler 无法证明重叠。
            if not second_started.wait(1.0):  # 新增代码+BrowserActionBatch: 等待第二个 handler 同时进入；若没有这行代码，测试无法区分并发和串行。
                raise RuntimeError("read actions did not run concurrently")  # 新增代码+BrowserActionBatch: 串行执行时明确失败；若没有这行代码，批处理串行问题可能被忽略。
            return "first"  # 新增代码+BrowserActionBatch: 返回第一个结果；若没有这行代码，结果顺序无法断言。
        def second_handler(arguments: dict[str, object]) -> str:  # 新增代码+BrowserActionBatch: 定义第二个只读工具 handler；若没有这行代码，批量执行缺少第二个动作。
            del arguments  # 新增代码+BrowserActionBatch: 明确测试不使用参数；若没有这行代码，未使用参数意图不清楚。
            self.assertTrue(first_started.wait(1.0))  # 新增代码+BrowserActionBatch: 等待第一个 handler 已启动；若没有这行代码，第二个 handler 可能抢先导致并发证据不稳定。
            second_started.set()  # 新增代码+BrowserActionBatch: 标记第二个 handler 已启动；若没有这行代码，第一个 handler 会一直等待。
            return "second"  # 新增代码+BrowserActionBatch: 返回第二个结果；若没有这行代码，结果顺序无法断言。
        results = executor.execute_batch("run-1", "stage-1", [{"tool_name": "browser_snapshot", "arguments": {}, "handler": first_handler}, {"tool_name": "browser_snapshot", "arguments": {}, "handler": second_handler}], action_id_prefix="run-1-batch")  # 新增代码+BrowserActionBatch: 执行两个并发安全的只读动作；若没有这行代码，测试无法驱动批处理入口。
        self.assertEqual([result for result, _action in results], ["first", "second"])  # 新增代码+BrowserActionBatch: 断言批处理按输入顺序返回结果；若没有这行代码，并发完成顺序可能污染上层上下文。
        self.assertTrue(all(action.status == "completed" for _result, action in results))  # 新增代码+BrowserActionBatch: 断言两个动作都完成；若没有这行代码，批处理可能只返回文本不维护 action 状态。
