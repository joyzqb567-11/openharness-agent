"""Stage 16 全局 StreamingToolExecutor 测试。"""  # 新增代码+Phase4StreamingExecutor: 说明本文件锁定全局工具流式执行器；若没有这行代码，维护者不知道测试保护的架构层。
from __future__ import annotations  # 新增代码+Phase4StreamingExecutor: 延迟解析类型注解；若没有这行代码，前向类型在旧解释顺序下可能出错。
from learning_agent.tests.support import *  # 新增代码+Phase4StreamingExecutor: 复用项目测试基类和 ToolCall；若没有这行代码，测试需要重复导入公共对象。

class BrowserStreamingExecutorStage16Tests(LearningAgentTestBase):  # 新增代码+Phase4StreamingExecutor: 定义 Stage 16 测试集合；若没有这个类，unittest 不会发现本阶段门禁。
    def test_streaming_executor_records_chunks_and_final_text(self) -> None:  # 新增代码+Phase4StreamingExecutor: 验证分段输出会被记录并拼成最终文本；若没有这行代码，流式工具可能只返回最后一段。
        from learning_agent.tools.streaming_executor import execute_tool_call_with_streaming  # 新增代码+Phase4StreamingExecutor: 导入生产执行入口；若没有这行代码，测试无法驱动真实实现。
        events: list[dict[str, object]] = []  # 新增代码+Phase4StreamingExecutor: 保存事件 sink 收到的 payload；若没有这行代码，无法断言事件顺序。
        tool_call = ToolCall(name="demo_stream", arguments={"x": 1}, call_id="call_stream")  # 新增代码+Phase4StreamingExecutor: 构造可追踪工具调用；若没有这行代码，执行器缺少工具名和 call_id。
        result = execute_tool_call_with_streaming(tool_call, lambda _call: iter(["A", "B"]), event_sink=events.append)  # 新增代码+Phase4StreamingExecutor: 用生成器模拟流式工具；若没有这行代码，chunk 分支没有输入样本。
        self.assertEqual(result, "AB")  # 新增代码+Phase4StreamingExecutor: 断言最终文本由所有分段拼接；若没有这行代码，分段结果丢失不会被发现。
        self.assertEqual([event["event_type"] for event in events], ["tool_started", "tool_result_chunk", "tool_result_chunk", "tool_completed"])  # 新增代码+Phase4StreamingExecutor: 断言事件顺序稳定；若没有这行代码，UI 无法可靠显示进度。
        self.assertEqual(events[1]["chunk"], "A")  # 新增代码+Phase4StreamingExecutor: 断言第一段内容被记录；若没有这行代码，chunk payload 可能为空。
        self.assertEqual(events[2]["chunk_index"], 2)  # 新增代码+Phase4StreamingExecutor: 断言第二段序号从 1 递增；若没有这行代码，前端排序会不稳定。
    def test_streaming_executor_turns_error_into_failed_event(self) -> None:  # 新增代码+Phase4StreamingExecutor: 验证工具异常被转成失败事件；若没有这行代码，一个工具失败可能打断整批执行。
        from learning_agent.tools.streaming_executor import execute_tool_call_with_streaming  # 新增代码+Phase4StreamingExecutor: 导入生产执行入口；若没有这行代码，测试无法覆盖异常路径。
        events: list[dict[str, object]] = []  # 新增代码+Phase4StreamingExecutor: 保存失败事件；若没有这行代码，无法检查 failed payload。
        tool_call = ToolCall(name="demo_fail", arguments={}, call_id="call_fail")  # 新增代码+Phase4StreamingExecutor: 构造失败工具调用；若没有这行代码，执行器缺少事件身份。
        def failing_handler(_call: ToolCall) -> str:  # 新增代码+Phase4StreamingExecutor: 定义会抛错的 handler；若没有这段函数，失败路径没有可靠输入。
            raise RuntimeError("boom")  # 新增代码+Phase4StreamingExecutor: 抛出可断言错误；若没有这行代码，failed 分支不会触发。
        result = execute_tool_call_with_streaming(tool_call, failing_handler, event_sink=events.append)  # 新增代码+Phase4StreamingExecutor: 执行失败 handler；若没有这行代码，事件列表不会产生。
        self.assertIn("demo_fail 工具执行失败：boom", result)  # 新增代码+Phase4StreamingExecutor: 断言失败文本可读；若没有这行代码，模型无法基于错误恢复。
        self.assertEqual(events[-1]["event_type"], "tool_failed")  # 新增代码+Phase4StreamingExecutor: 断言最后事件是失败；若没有这行代码，UI 可能误报完成。
        self.assertEqual(events[-1]["error"], "boom")  # 新增代码+Phase4StreamingExecutor: 断言失败原因进入 payload；若没有这行代码，排查缺少具体错误。
    def test_orchestrator_uses_streaming_executor_event_sink(self) -> None:  # 新增代码+Phase4StreamingExecutor: 验证批量 orchestrator 接入全局 executor；若没有这行代码，executor 可能只在孤立测试里存在。
        from learning_agent.tools.orchestrator import execute_tool_calls  # 新增代码+Phase4StreamingExecutor: 导入真实批量编排器；若没有这行代码，测试无法覆盖主循环路径。
        class FakeCatalogTool:  # 新增代码+Phase4StreamingExecutor: 定义最小 catalog 元数据；若没有这个类，并发安全判断缺少工具属性。
            is_read_only = False  # 新增代码+Phase4StreamingExecutor: 保守设为非只读，确保本测试走串行路径；若没有这行代码，orchestrator 可能进入并发分支。
            is_concurrency_safe = False  # 新增代码+Phase4StreamingExecutor: 保守设为不可并发；若没有这行代码，安全判断属性缺失会当 False 但意图不清楚。
        class FakeAgent:  # 新增代码+Phase4StreamingExecutor: 定义最小 agent 接收 observation；若没有这个类，orchestrator 没有 event sink 目标。
            def __init__(self) -> None:  # 新增代码+Phase4StreamingExecutor: 初始化事件列表；若没有这行代码，测试无法保存观察事件。
                self.observations: list[tuple[str, dict[str, object]]] = []  # 新增代码+Phase4StreamingExecutor: 保存 observation kind 和 payload；若没有这行代码，无法断言 executor 事件被落盘。
            def _find_catalog_tool(self, _name: str) -> FakeCatalogTool:  # 新增代码+Phase4StreamingExecutor: 提供 catalog 查询接口；若没有这行代码，orchestrator 会把工具当未知并发属性。
                return FakeCatalogTool()  # 新增代码+Phase4StreamingExecutor: 返回固定元数据；若没有这行代码，安全判断拿不到对象。
            def _record_observation(self, kind: str, payload: dict[str, object]) -> None:  # 新增代码+Phase4StreamingExecutor: 接收 streaming executor 事件；若没有这行代码，事件 sink 不会记录。
                self.observations.append((kind, payload))  # 新增代码+Phase4StreamingExecutor: 保存事件；若没有这行代码，测试无法验证集成。
        agent = FakeAgent()  # 新增代码+Phase4StreamingExecutor: 创建 fake agent；若没有这行代码，execute_tool_calls 没有运行上下文。
        calls = [ToolCall(name="demo_stream", arguments={}, call_id="call_orch")]  # 新增代码+Phase4StreamingExecutor: 构造批量工具调用列表；若没有这行代码，orchestrator 没有任务。
        outputs = execute_tool_calls(agent, calls, execute_one=lambda _call: iter(["x", "y"]))  # 新增代码+Phase4StreamingExecutor: 通过 orchestrator 执行流式结果；若没有这行代码，集成路径不会触发。
        self.assertEqual(outputs, ["xy"])  # 新增代码+Phase4StreamingExecutor: 断言 orchestrator 返回拼接结果；若没有这行代码，主循环回填可能只拿到生成器对象。
        event_types = [payload["event_type"] for kind, payload in agent.observations if kind == "streaming_tool_executor"]  # 新增代码+Phase4StreamingExecutor: 提取全局 executor 事件类型；若没有这行代码，断言会混入其他 observation。
        self.assertIn("tool_result_chunk", event_types)  # 新增代码+Phase4StreamingExecutor: 断言 chunk 事件通过 agent observation 落盘；若没有这行代码，终端 UI 看不到流式进度。
