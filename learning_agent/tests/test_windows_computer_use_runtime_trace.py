"Computer Use runtime trace tests."  # 新增代码+RuntimeTrace：说明本文件专门验证主循环运行时证据；如果没有这行代码，读者会不清楚这个测试和旧静态 maturity 的区别。
from __future__ import annotations  # 新增代码+RuntimeTrace：启用延迟类型注解；如果没有这行代码，部分类型在导入顺序变化时可能提前求值失败。
import json  # 新增代码+RuntimeTrace：用于解析 fake computer_discover 返回的 JSON；如果没有这行代码，测试无法像真实工具结果一样构造结构化文本。
import tempfile  # 新增代码+RuntimeTrace：用于创建临时 workspace；如果没有这行代码，测试可能污染用户真实项目目录。
import unittest  # 新增代码+RuntimeTrace：使用 Python 标准测试框架；如果没有这行代码，测试类不会被 unittest 发现。
from pathlib import Path  # 新增代码+RuntimeTrace：把临时目录转成清晰的 Path 对象；如果没有这行代码，路径处理会退回容易混淆的字符串。
from learning_agent.app.interactive import _activate_computer_use_tool_pack_for_agent  # 新增代码+RuntimeTrace：复用真实 `/computer use --full` 工具包加载入口；如果没有这行代码，测试会绕开用户实际终端路径。
from learning_agent.core.agent import LearningAgent  # 新增代码+RuntimeTrace：导入真实 agent 主循环；如果没有这行代码，测试只能验证孤立 helper。
from learning_agent.core.messages import ModelMessage, ToolCall  # 新增代码+RuntimeTrace：导入模型消息和工具调用结构；如果没有这行代码，fake 模型无法请求真实工具。


class RuntimeTraceDesktopModel:  # 新增代码+RuntimeTrace：类段开始，定义会记录工具 schema 并调用 computer_discover 的离线模型；如果没有这个类，测试可能误用真实联网模型。
    def __init__(self) -> None:  # 新增代码+RuntimeTrace：函数段开始，初始化 fake 模型状态；如果没有这段函数，测试无法记录每轮输入。
        self.index = 0  # 新增代码+RuntimeTrace：记录当前返回第几轮模型消息；如果没有这行代码，fake 模型会重复调用同一个工具。
        self.received_tool_names: list[list[str]] = []  # 新增代码+RuntimeTrace：保存每轮模型看到的工具名；如果没有这行代码，测试无法证明 schema 真进了主循环。
    # 新增代码+RuntimeTrace：函数段结束，RuntimeTraceDesktopModel.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码+RuntimeTrace：函数段开始，模拟模型主循环 chat 接口；如果没有这段函数，LearningAgent.run 无法调用 fake 模型。
        del messages  # 新增代码+RuntimeTrace：明确本 fake 模型不读取消息内容；如果没有这行代码，未使用参数会让测试意图不清楚。
        tool_names = [str(schema.get("function", {}).get("name", "")) for schema in tools if isinstance(schema.get("function", {}), dict)]  # 新增代码+RuntimeTrace：从真实 schema 中提取工具名；如果没有这行代码，模型是否看到 Computer Use 工具不可验证。
        self.received_tool_names.append(tool_names)  # 新增代码+RuntimeTrace：记录本轮工具清单；如果没有这行代码，断言只能靠 agent 内部状态猜测。
        if self.index == 0:  # 新增代码+RuntimeTrace：第一轮让模型主动调用只读 discover；如果没有这行代码，主循环不会产生工具调用和工具结果 trace。
            self.index += 1  # 新增代码+RuntimeTrace：推进到第二轮最终回答；如果没有这行代码，agent 会一直重复 discover。
            return ModelMessage(tool_calls=[ToolCall(name="computer_discover", arguments={"query": "画图", "max_results": 3})])  # 新增代码+RuntimeTrace：请求真实工具面里的应用发现工具；如果没有这行代码，测试覆盖不到工具编排器。
        return ModelMessage(text="runtime trace 已收到 discover 结果。")  # 新增代码+RuntimeTrace：第二轮返回最终文本让 run 正常结束；如果没有这行代码，测试无法稳定结束。
    # 新增代码+RuntimeTrace：函数段结束，RuntimeTraceDesktopModel.chat 到此结束；如果没有这个边界说明，读者不容易看出 fake 模型行为。
# 新增代码+RuntimeTrace：类段结束，RuntimeTraceDesktopModel 到此结束；如果没有这个边界说明，读者不容易看出测试模型范围。


class WindowsComputerUseRuntimeTraceTests(unittest.TestCase):  # 新增代码+RuntimeTrace：类段开始，集中验证 Computer Use 主循环 runtime trace；如果没有这个类，unittest 不会收集本组测试。
    def test_full_mode_model_loop_records_computer_use_runtime_trace(self) -> None:  # 新增代码+RuntimeTrace：函数段开始，验证 full 模式自然语言任务会留下模型、工具、结果三段运行证据；如果没有这个测试，后续瘦身仍可能只靠静态文件猜测。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RuntimeTrace：创建临时 workspace 隔离调试文件；如果没有这行代码，测试会污染真实项目运行记录。
            workspace = Path(raw_dir)  # 新增代码+RuntimeTrace：把临时目录转成 Path；如果没有这行代码，agent 构造参数不够清楚。
            model = RuntimeTraceDesktopModel()  # 新增代码+RuntimeTrace：创建离线 fake 模型；如果没有这行代码，测试可能调用真实 provider。
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+RuntimeTrace：创建真实 agent 并关闭调试噪音；如果没有这行代码，主循环没有被测对象。
            def fake_computer_discover(arguments: dict[str, object]) -> str:  # 新增代码+RuntimeTrace：函数段开始，用稳定假结果替代本机应用枚举；如果没有这段函数，单元测试会受用户安装的软件数量影响。
                report = {"ok": True, "query": arguments.get("query", ""), "result_count": 1, "candidates": [{"display_name": "Paint", "executable": "mspaint.exe"}]}  # 新增代码+RuntimeTrace：构造接近真实 discover 的结构化报告；如果没有这行代码，工具结果无法模拟真实 JSON。
                agent._record_observation("computer_use_discover", {"ok": True, "query": report["query"], "result_count": 1, "candidates": report["candidates"]})  # 新增代码+RuntimeTrace：保留旧观察流事件；如果没有这行代码，测试无法证明 trace 与既有 observation 兼容。
                return json.dumps(report, ensure_ascii=False)  # 新增代码+RuntimeTrace：返回 JSON 文本给模型下一轮读取；如果没有这行代码，工具编排器没有可回填结果。
            # 新增代码+RuntimeTrace：函数段结束，fake_computer_discover 到此结束；如果没有这个边界说明，读者不容易看出这里没有真实枚举应用。
            agent._computer_discover = fake_computer_discover  # 新增代码+RuntimeTrace：把 discover 替换成稳定假工具；如果没有这行代码，测试会依赖当前 Windows 机器状态。
            activation_output = _activate_computer_use_tool_pack_for_agent(agent, "/computer use --full", "Computer Use Mode\n- mode=full\n- full_mode=true\n")  # 新增代码+RuntimeTrace：模拟用户真实先输入 `/computer use --full`；如果没有这行代码，工具包不会按终端路径进入模型主循环。
            self.assertIn("model_loop_tools_loaded=true", activation_output)  # 新增代码+RuntimeTrace：确认 full 工具包已加载；如果没有这行代码，后续 trace 失败原因会不清楚。
            answer = agent.run("请使用本地电脑的画图软件画一棵树。", max_turns=2)  # 新增代码+RuntimeTrace：用真实用户自然语言任务驱动主循环；如果没有这行代码，runtime trace 没有运行样本。
            report = agent._computer_use_runtime_trace_report()  # 新增代码+RuntimeTrace：读取 agent 自己生成的 trace 汇总；如果没有这行代码，测试无法判断主循环是否留下运行证据。
            self.assertIn("runtime trace 已收到 discover 结果", answer)  # 新增代码+RuntimeTrace：断言工具结果已经回流到第二轮模型；如果没有这行代码，只看 trace 可能掩盖主循环中断。
            self.assertTrue(report["runtime_trace_available"])  # 新增代码+RuntimeTrace：断言 runtime trace 能力已开启；如果没有这行代码，缺失 trace 容器也可能被误判通过。
            self.assertTrue(report["model_request_seen"])  # 新增代码+RuntimeTrace：断言模型请求阶段被记录；如果没有这行代码，无法证明 schema 是在主循环里看到的。
            self.assertTrue(report["tool_schema_visible"])  # 新增代码+RuntimeTrace：断言 Computer Use 工具 schema 对模型可见；如果没有这行代码，模型可能根本没看到工具。
            self.assertTrue(report["tool_call_seen"])  # 新增代码+RuntimeTrace：断言模型工具调用被记录；如果没有这行代码，无法证明模型自己选择了工具。
            self.assertTrue(report["tool_result_seen"])  # 新增代码+RuntimeTrace：断言工具结果回流被记录；如果没有这行代码，无法证明结果回到了模型循环。
            self.assertIn("computer_discover", report["tools_called"])  # 新增代码+RuntimeTrace：断言 discover 工具真实经过工具调用路径；如果没有这行代码，静态 schema 暴露会被误当运行证据。
            self.assertIn("computer_discover", report["computer_tool_names_seen"])  # 新增代码+RuntimeTrace：断言工具 schema 观察也包含 discover；如果没有这行代码，schema 与调用记录可能脱节。
            self.assertGreaterEqual(report["trace_event_count"], 3)  # 新增代码+RuntimeTrace：断言至少有模型请求、工具调用、工具结果三类事件；如果没有这行代码，空壳 trace 也可能过关。
            self.assertIn("computer_discover", model.received_tool_names[0])  # 新增代码+RuntimeTrace：交叉验证 fake 模型第一轮确实看到了 discover schema；如果没有这行代码，report 可能自说自话。
    # 新增代码+RuntimeTrace：函数段结束，test_full_mode_model_loop_records_computer_use_runtime_trace 到此结束；如果没有这个边界说明，读者不容易看出测试范围。
# 新增代码+RuntimeTrace：类段结束，WindowsComputerUseRuntimeTraceTests 到此结束；如果没有这个边界说明，读者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+RuntimeTrace：文件入口段开始，允许直接运行本测试文件；如果没有这行代码，初学者必须记住 unittest 模块命令。
    unittest.main()  # 新增代码+RuntimeTrace：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
# 新增代码+RuntimeTrace：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，读者不容易看出入口范围。
