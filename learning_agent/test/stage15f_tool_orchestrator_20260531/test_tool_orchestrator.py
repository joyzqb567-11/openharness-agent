"""Stage 15F 安全并发工具编排测试。"""  # 新增代码+Stage15F: 说明本文件锁定并发工具批处理行为；若没有这行代码，维护者不清楚测试边界。

from __future__ import annotations  # 新增代码+Stage15F: 延迟解析类型注解；若没有这行代码，前向引用更容易受定义顺序影响。

import threading  # 新增代码+Stage15F: 用线程事件验证并发是否真实发生；若没有这行代码，测试只能看顺序而不能证明并行。
import time  # 新增代码+Stage15F: 用短暂等待放大并发重叠窗口；若没有这行代码，线程重叠可能太快无法观察。
import unittest  # 新增代码+Stage15F: 使用项目现有 unittest 框架；若没有这行代码，测试类无法运行。

from learning_agent.core.messages import ToolCall  # 新增代码+Stage15F: 导入工具调用对象；若没有这行代码，测试无法构造批量 tool_calls。
from learning_agent.tools.orchestrator import execute_tool_calls  # 新增代码+Stage15F: 导入新增工具编排器；若没有这行代码，红灯无法证明 orchestrator 模块缺失。
from learning_agent.tools.types import AgentTool  # 新增代码+Stage15F: 导入工具元数据对象；若没有这行代码，测试无法声明哪些工具可并发。


class FakeToolAgent:  # 新增代码+Stage15F: 提供最小 agent 目录查询对象；若没有这行代码，测试需要启动完整 LearningAgent。
    def __init__(self, tools: list[AgentTool]) -> None:  # 新增代码+Stage15F: 接收测试工具元数据；若没有这行代码，fake agent 没有 catalog。
        self.tools = {tool.name: tool for tool in tools}  # 新增代码+Stage15F: 按工具名建立索引；若没有这行代码，_find_catalog_tool 无法快速返回工具。

    def _find_catalog_tool(self, tool_name: str) -> AgentTool | None:  # 新增代码+Stage15F: 模拟 LearningAgent 的 catalog 查询；若没有这行代码，编排器无法读取并发元数据。
        return self.tools.get(tool_name)  # 新增代码+Stage15F: 返回匹配工具或 None；若没有这行代码，未知工具无法按保守串行处理。


class ToolOrchestratorTests(unittest.TestCase):  # 新增代码+Stage15F: 定义并发编排测试类；若没有这行代码，测试方法没有统一容器。
    def test_safe_read_only_tools_run_concurrently_and_keep_result_order(self) -> None:  # 新增代码+Stage15F: 验证安全只读工具会并发且结果顺序稳定；若没有这行代码，Stage 15F 可能只是串行包装。
        tools = [AgentTool(name="read_a", description="", input_schema={}, is_read_only=True, is_concurrency_safe=True), AgentTool(name="read_b", description="", input_schema={}, is_read_only=True, is_concurrency_safe=True)]  # 新增代码+Stage15F: 声明两个明确安全的只读工具；若没有这行代码，编排器没有并发依据。
        agent = FakeToolAgent(tools)  # 新增代码+Stage15F: 创建 fake agent；若没有这行代码，execute_tool_calls 无法查 catalog。
        active_count = 0  # 新增代码+Stage15F: 记录当前正在执行的工具数；若没有这行代码，测试无法判断是否重叠。
        max_active_count = 0  # 新增代码+Stage15F: 记录最大并发数；若没有这行代码，测试无法断言真实并发。
        lock = threading.Lock()  # 新增代码+Stage15F: 保护计数器并发更新；若没有这行代码，线程竞争会让测试不稳定。
        both_running = threading.Event()  # 新增代码+Stage15F: 标记两个读取工具已同时进入执行区；若没有这行代码，无法让线程尽快释放等待。

        def execute_one(tool_call: ToolCall) -> str:  # 新增代码+Stage15F: 定义测试用工具执行函数；若没有这行代码，编排器没有真实工作可运行。
            nonlocal active_count, max_active_count  # 新增代码+Stage15F: 允许内部函数更新外部计数器；若没有这行代码，并发状态不会被记录。
            with lock:  # 新增代码+Stage15F: 加锁更新并发计数；若没有这行代码，多个线程会互相覆盖计数。
                active_count += 1  # 新增代码+Stage15F: 当前工具进入执行区；若没有这行代码，无法统计重叠。
                max_active_count = max(max_active_count, active_count)  # 新增代码+Stage15F: 更新最大并发值；若没有这行代码，最后无法判断是否达到 2。
                if active_count == 2:  # 新增代码+Stage15F: 两个工具同时运行时触发事件；若没有这行代码，等待线程不会提前释放。
                    both_running.set()  # 新增代码+Stage15F: 通知两个并发工具已经重叠；若没有这行代码，测试会等待到超时。
            both_running.wait(1.0)  # 新增代码+Stage15F: 等另一个工具进入执行区；若没有这行代码，线程可能太快结束导致看不到重叠。
            time.sleep(0.01)  # 新增代码+Stage15F: 保留极短重叠窗口；若没有这行代码，慢机器上 max_active 仍可能偶发不稳定。
            with lock:  # 新增代码+Stage15F: 加锁减少并发计数；若没有这行代码，计数器会被并发写坏。
                active_count -= 1  # 新增代码+Stage15F: 当前工具离开执行区；若没有这行代码，后续断言会看到错误活跃数。
            return f"result-{tool_call.name}"  # 新增代码+Stage15F: 返回带工具名的结果；若没有这行代码，无法验证顺序和对应关系。

        calls = [ToolCall(name="read_a", arguments={}), ToolCall(name="read_b", arguments={})]  # 新增代码+Stage15F: 构造两个只读调用；若没有这行代码，编排器没有批次输入。
        results = execute_tool_calls(agent, calls, execute_one=execute_one, max_concurrency=2)  # 新增代码+Stage15F: 执行并发编排；若没有这行代码，测试不会触发目标函数。
        self.assertGreaterEqual(max_active_count, 2)  # 新增代码+Stage15F: 断言两个工具确实重叠执行；若没有这行代码，串行实现也可能伪装通过。
        self.assertEqual(results, ["result-read_a", "result-read_b"])  # 新增代码+Stage15F: 断言结果按原 tool_call 顺序返回；若没有这行代码，并发完成顺序可能污染消息回填。

    def test_side_effect_tools_remain_serial(self) -> None:  # 新增代码+Stage15F: 验证副作用工具不会并发；若没有这行代码，写文件或命令可能被错误批处理。
        tools = [AgentTool(name="write_a", description="", input_schema={}, is_destructive=True), AgentTool(name="write_b", description="", input_schema={}, is_destructive=True)]  # 新增代码+Stage15F: 声明两个副作用工具；若没有这行代码，编排器无法知道它们必须串行。
        agent = FakeToolAgent(tools)  # 新增代码+Stage15F: 创建 fake agent；若没有这行代码，execute_tool_calls 无法查工具元数据。
        active_count = 0  # 新增代码+Stage15F: 记录当前执行数量；若没有这行代码，无法检测串行性。
        max_active_count = 0  # 新增代码+Stage15F: 记录最大同时执行数量；若没有这行代码，无法断言没有并发。
        lock = threading.Lock()  # 新增代码+Stage15F: 保护并发计数；若没有这行代码，线程更新不稳定。

        def execute_one(tool_call: ToolCall) -> str:  # 新增代码+Stage15F: 定义副作用工具执行函数；若没有这行代码，编排器没有实际执行体。
            nonlocal active_count, max_active_count  # 新增代码+Stage15F: 允许更新外部计数器；若没有这行代码，无法记录执行重叠。
            with lock:  # 新增代码+Stage15F: 加锁进入执行区；若没有这行代码，并发计数可能被竞争写坏。
                active_count += 1  # 新增代码+Stage15F: 标记当前工具开始执行；若没有这行代码，无法统计活跃工具。
                max_active_count = max(max_active_count, active_count)  # 新增代码+Stage15F: 更新最大活跃数；若没有这行代码，无法确认是否出现并发。
            time.sleep(0.01)  # 新增代码+Stage15F: 放大潜在并发窗口；若没有这行代码，错误并发可能因执行太快不易被观察。
            with lock:  # 新增代码+Stage15F: 加锁离开执行区；若没有这行代码，计数器可能被并发写坏。
                active_count -= 1  # 新增代码+Stage15F: 标记当前工具结束执行；若没有这行代码，活跃数无法回落。
            return tool_call.name  # 新增代码+Stage15F: 返回工具名；若没有这行代码，结果顺序无法检查。

        calls = [ToolCall(name="write_a", arguments={}), ToolCall(name="write_b", arguments={})]  # 新增代码+Stage15F: 构造两个副作用调用；若没有这行代码，串行分支没有输入。
        results = execute_tool_calls(agent, calls, execute_one=execute_one, max_concurrency=2)  # 新增代码+Stage15F: 执行编排器；若没有这行代码，测试不会触发目标行为。
        self.assertEqual(max_active_count, 1)  # 新增代码+Stage15F: 断言副作用工具没有重叠；若没有这行代码，错误并发不会被发现。
        self.assertEqual(results, ["write_a", "write_b"])  # 新增代码+Stage15F: 断言串行结果顺序稳定；若没有这行代码，消息回填可能乱序。

    def test_parallel_tool_failure_does_not_drop_other_results(self) -> None:  # 新增代码+Stage15F: 验证并发批次中单个失败不会吞掉其他结果；若没有这行代码，一个读取失败可能导致整批结果丢失。
        tools = [AgentTool(name="read_bad", description="", input_schema={}, is_read_only=True, is_concurrency_safe=True), AgentTool(name="read_ok", description="", input_schema={}, is_read_only=True, is_concurrency_safe=True)]  # 新增代码+Stage15F: 声明两个并发安全读取工具；若没有这行代码，失败分支不会走并发批次。
        agent = FakeToolAgent(tools)  # 新增代码+Stage15F: 创建 fake agent；若没有这行代码，编排器无法判断并发安全。

        def execute_one(tool_call: ToolCall) -> str:  # 新增代码+Stage15F: 定义一个会部分失败的执行函数；若没有这行代码，无法测试异常兜底。
            if tool_call.name == "read_bad":  # 新增代码+Stage15F: 指定第一个工具失败；若没有这行代码，失败分支不会触发。
                raise RuntimeError("boom")  # 新增代码+Stage15F: 抛出模拟工具错误；若没有这行代码，编排器异常处理没有输入。
            return "ok-result"  # 新增代码+Stage15F: 第二个工具正常返回；若没有这行代码，无法证明其他结果仍保留。

        calls = [ToolCall(name="read_bad", arguments={}), ToolCall(name="read_ok", arguments={})]  # 新增代码+Stage15F: 构造失败和成功两个调用；若没有这行代码，测试没有输入。
        results = execute_tool_calls(agent, calls, execute_one=execute_one, max_concurrency=2)  # 新增代码+Stage15F: 执行并发批次；若没有这行代码，异常兜底不会运行。
        self.assertIn("工具执行失败", results[0])  # 新增代码+Stage15F: 确认失败被转成结果文本；若没有这行代码，异常可能中断整个批次。
        self.assertEqual(results[1], "ok-result")  # 新增代码+Stage15F: 确认另一个工具结果未丢失；若没有这行代码，并发失败隔离无法验证。


if __name__ == "__main__":  # 新增代码+Stage15F: 支持直接运行本测试文件；若没有这行代码，单文件排查不方便。
    unittest.main()  # 新增代码+Stage15F: 直接运行时启动 unittest；若没有这行代码，python 文件本身不会执行测试。
