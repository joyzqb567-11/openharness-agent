import os  # 新增代码+RealHarnessAdapterTest：读取和临时修改环境变量；如果没有这一行，bridge 真实模式开关无法测试。
import tempfile  # 新增代码+RealHarnessAdapterTest：创建隔离 workspace；如果没有这一行，测试会污染真实项目 memory。
import time  # 新增代码+RealHarnessAdapterTest：等待后台 GUI worker 完成；如果没有这一行，异步断言会和线程抢时序。
import unittest  # 新增代码+RealHarnessAdapterTest：使用标准库 unittest 编写合同测试；如果没有这一行，测试文件无法被 unittest/pytest 收集。
from pathlib import Path  # 新增代码+RealHarnessAdapterTest：用 Path 传递 workspace；如果没有这一行，Windows 路径拼接更容易出错。

from learning_agent.app.gui_agent_adapter import DefaultHarnessGuiAgentAdapter, GuiAgentRunRequest  # 新增代码+RealHarnessAdapterTest：导入 GUI adapter shell 和请求对象；如果没有这一行，测试没有被测入口。
from learning_agent.app.gui_agent_event_mapper import agent_event_to_gui_events, redact_gui_agent_payload  # 新增代码+RealHarnessAdapterTest：导入事件映射和脱敏 helper；如果没有这一行，Phase 0 合同没有覆盖。
from learning_agent.app.gui_harness_adapter import RealHarnessGuiAgentAdapter  # 新增代码+GuiToolchainReuseTest：导入真实 adapter 以直接验证 runtime_path 诊断；如果没有这一行，full_access 工具状态只能靠间接事件猜测。
from learning_agent.app.gui_model_factory import GuiModelFactoryError, build_chat_model_for_gui_request  # 新增代码+RealHarnessAdapterTest：导入模型工厂和结构化错误；如果没有这一行，Provider 未连接合同无法测试。
from learning_agent.core.events import AgentEvent  # 新增代码+RealHarnessAdapterTest：构造 core agent 事件；如果没有这一行，事件映射测试没有输入对象。
from learning_agent.core.messages import ModelMessage, ToolCall  # 修改代码+RealHarnessReadOnlyTraceTest：构造假模型回答和工具调用；如果没有这一行，真实 adapter 测试必须联网且无法请求 read_file。
from learning_agent.models.fake import ToolCallingFakeModel  # 新增代码+RealHarnessAdapterTest：使用项目已有假模型；如果没有这一行，测试无法离线跑 core 主循环。


class RealHarnessAdapterTest(unittest.TestCase):  # 新增代码+RealHarnessAdapterTest：测试类段开始，覆盖真实 GUI harness adapter 最小闭环；如果没有这个类，Phase 0/1 没有自动验收。
    def _fake_model_factory(self, _request: GuiAgentRunRequest):  # 新增代码+RealHarnessAdapterTest：函数段开始，生成离线 ChatModel；如果没有这段，adapter 测试会请求真实 OpenAI。
        return ToolCallingFakeModel([ModelMessage(text="AGENT_HARNESS_SMOKE_OK")])  # 新增代码+RealHarnessAdapterTest：返回固定最终回答；如果没有这一行，断言没有稳定文本。
    # 新增代码+RealHarnessAdapterTest：函数段结束，_fake_model_factory 到此结束；如果没有这个边界说明，用户不容易看出它只做测试模型。

    def test_event_mapper_redacts_sensitive_payload_and_workspace(self) -> None:  # 新增代码+RealHarnessAdapterTest：测试函数开始，验证 AgentEvent 脱敏；如果没有这段，token 和本机路径可能漏到 GUI。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+RealHarnessAdapterTest：创建临时 workspace；如果没有这一行，路径脱敏没有真实绝对路径样本。
            payload = {"text_delta": f"answer from {Path(directory).resolve()}", "access_token": "secret-token"}  # 新增代码+RealHarnessAdapterTest：构造含路径和 token 的 payload；如果没有这一行，脱敏规则没有覆盖敏感字段。
            redacted = redact_gui_agent_payload(payload, directory)  # 新增代码+RealHarnessAdapterTest：执行递归脱敏；如果没有这一行，后续无法断言结果。
            self.assertEqual("[redacted]", redacted["access_token"])  # 新增代码+RealHarnessAdapterTest：确认 token 字段被遮蔽；如果没有这一行，敏感键脱敏可能回退。
            self.assertIn("[workspace]", redacted["text_delta"])  # 新增代码+RealHarnessAdapterTest：确认 workspace 路径被替换；如果没有这一行，本机路径可能泄露。
            agent_event = AgentEvent(event_type="model_message_delta", run_id="agent_run", sequence=7, session_id="agent_session", payload=payload)  # 新增代码+RealHarnessAdapterTest：构造 core 流式事件；如果没有这一行，映射器没有输入。
            gui_events = agent_event_to_gui_events(agent_event, run_id="gui_run", turn_id="gui_turn", sequence_start=3, workspace=directory)  # 新增代码+RealHarnessAdapterTest：把 core 事件映射到 GUI 事件；如果没有这一行，无法验证 kind 和 sequence。
        self.assertEqual("message_delta", gui_events[0]["kind"])  # 新增代码+RealHarnessAdapterTest：确认 delta 事件映射正确；如果没有这一行，GUI 可能收不到流式文本。
        self.assertEqual(3, gui_events[0]["sequence"])  # 新增代码+RealHarnessAdapterTest：确认 sequence 使用调用方提供值；如果没有这一行，事件排序可能不稳定。
        self.assertEqual("[redacted]", gui_events[0]["payload"]["access_token"])  # 新增代码+RealHarnessAdapterTest：确认映射后仍脱敏；如果没有这一行，二次组合可能重新泄露 token。
    # 新增代码+RealHarnessAdapterTest：测试函数结束，test_event_mapper_redacts_sensitive_payload_and_workspace 到此结束；如果没有这个边界说明，用户不容易看出脱敏合同范围。

    def test_model_factory_uses_offline_test_model_when_enabled(self) -> None:  # 新增代码+RealHarnessAdapterTest：测试函数开始，验证模型工厂离线路径；如果没有这段，Phase 0 probe 会依赖真实账号。
        old_value = os.environ.get("OPENHARNESS_GUI_AGENT_TEST_MODEL")  # 新增代码+RealHarnessAdapterTest：保存旧环境变量；如果没有这一行，测试会污染后续用例。
        os.environ["OPENHARNESS_GUI_AGENT_TEST_MODEL"] = "enabled"  # 新增代码+RealHarnessAdapterTest：启用离线测试模型；如果没有这一行，工厂会检查真实 provider。
        try:  # 新增代码+RealHarnessAdapterTest：确保环境变量恢复；如果没有这一行，测试失败时会污染进程。
            request = GuiAgentRunRequest(session_id="s", turn_id="t", run_id="r", prompt="AGENT_HARNESS_SMOKE", workspace=".", provider_id="openai")  # 新增代码+RealHarnessAdapterTest：构造 GUI 请求；如果没有这一行，模型工厂没有输入。
            model = build_chat_model_for_gui_request(request)  # 新增代码+RealHarnessAdapterTest：创建 ChatModel；如果没有这一行，无法断言离线路径。
            message = model.chat([], [])  # 新增代码+RealHarnessAdapterTest：调用假模型；如果没有这一行，无法验证返回文本。
            tool_request = GuiAgentRunRequest(session_id="s", turn_id="t2", run_id="r2", prompt="READ_ONLY_TOOL_TRACE", workspace=".", provider_id="openai")  # 新增代码+GuiModelFactoryVisibleToolTrace：构造工具轨迹烟测请求；如果没有这一行，离线模型工厂不会覆盖 GUI 工具面板验收入口。
            tool_model = build_chat_model_for_gui_request(tool_request)  # 新增代码+GuiModelFactoryVisibleToolTrace：创建会先发工具调用的假模型；如果没有这一行，测试无法证明烟测 prompt 会进入工具循环。
            first_tool_message = tool_model.chat([], [])  # 新增代码+GuiModelFactoryVisibleToolTrace：读取第一轮模型输出；如果没有这一行，无法断言 read_file 工具调用确实被生成。
            final_tool_message = tool_model.chat([], [])  # 新增代码+GuiModelFactoryVisibleToolTrace：读取工具后的最终回答；如果没有这一行，无法断言两轮烟测会稳定完成。
        finally:  # 新增代码+RealHarnessAdapterTest：恢复环境变量；如果没有这一行，测试进程会留下开关。
            if old_value is None:  # 新增代码+RealHarnessAdapterTest：旧值不存在时删除变量；如果没有这一行，环境会多出测试开关。
                os.environ.pop("OPENHARNESS_GUI_AGENT_TEST_MODEL", None)  # 新增代码+RealHarnessAdapterTest：清理测试开关；如果没有这一行，后续测试会误用假模型。
            else:  # 新增代码+RealHarnessAdapterTest：旧值存在时恢复；如果没有这一行，用户原环境值会丢失。
                os.environ["OPENHARNESS_GUI_AGENT_TEST_MODEL"] = old_value  # 新增代码+RealHarnessAdapterTest：恢复原值；如果没有这一行，测试会改变外部环境。
        self.assertEqual("AGENT_HARNESS_SMOKE_OK", message.text)  # 新增代码+RealHarnessAdapterTest：确认离线模型输出固定 smoke 文本；如果没有这一行，Phase 0 probe 不可验证。
        self.assertEqual("read_file", first_tool_message.tool_calls[0].name)  # 新增代码+GuiModelFactoryVisibleToolTrace：确认第一轮离线模型请求 read_file；如果没有这一行，GUI 可见工具轨迹可能惄惄退化成纯文本。
        self.assertEqual("READ_ONLY_TOOL_TRACE_OK", final_tool_message.text)  # 新增代码+GuiModelFactoryVisibleToolTrace：确认第二轮离线模型给出稳定最终回答；如果没有这一行，工具循环完成性没有自动化证据。
    # 新增代码+RealHarnessAdapterTest：测试函数结束，test_model_factory_uses_offline_test_model_when_enabled 到此结束；如果没有这个边界说明，用户不容易看出模型工厂离线路径。

    def test_model_factory_reports_provider_not_connected_without_test_model(self) -> None:  # 新增代码+RealHarnessAdapterTest：测试函数开始，验证未连接 provider 的结构化失败；如果没有这段，GUI 会看到泛化错误。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+RealHarnessAdapterTest：创建空 workspace；如果没有这一行，真实用户配置可能影响测试。
            request = GuiAgentRunRequest(session_id="s", turn_id="t", run_id="r", prompt="hello", workspace=directory, provider_id="openai")  # 新增代码+RealHarnessAdapterTest：构造未连接 OpenAI 请求；如果没有这一行，工厂没有失败样本。
            with self.assertRaises(GuiModelFactoryError) as raised:  # 新增代码+RealHarnessAdapterTest：捕获结构化工厂错误；如果没有这一行，测试无法检查错误码。
                build_chat_model_for_gui_request(request)  # 新增代码+RealHarnessAdapterTest：执行模型工厂；如果没有这一行，不会触发未连接路径。
        self.assertEqual("provider_not_connected", raised.exception.code)  # 新增代码+RealHarnessAdapterTest：确认错误码稳定；如果没有这一行，前端无法机器处理未连接状态。
        self.assertEqual("provider_not_connected", raised.exception.event_kind)  # 新增代码+RealHarnessAdapterTest：确认建议事件类型稳定；如果没有这一行，adapter 可能只发 turn_failed。
    # 新增代码+RealHarnessAdapterTest：测试函数结束，test_model_factory_reports_provider_not_connected_without_test_model 到此结束；如果没有这个边界说明，用户不容易看出未连接合同。

    def test_default_harness_adapter_enabled_runs_learning_agent_main_loop(self) -> None:  # 新增代码+RealHarnessAdapterTest：测试函数开始，验证 enabled shell 真正调用 LearningAgent；如果没有这段，GUI 仍可能只是 fake。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+RealHarnessAdapterTest：创建隔离 workspace；如果没有这一行，LearningAgent 会写入真实 memory。
            request = GuiAgentRunRequest(session_id="session_a", turn_id="turn_a", run_id="run_a", prompt="AGENT_HARNESS_SMOKE", workspace=directory, provider_id="test-fake")  # 新增代码+RealHarnessAdapterTest：构造真实 adapter 请求；如果没有这一行，adapter 没有运行身份。
            events: list[dict[str, object]] = []  # 新增代码+RealHarnessAdapterTest：保存 adapter 发出的 GUI 事件；如果没有这一行，无法断言真实路径。
            result = DefaultHarnessGuiAgentAdapter(enabled=True, model_factory=self._fake_model_factory).run(request, events.append, lambda: False)  # 新增代码+RealHarnessAdapterTest：运行启用状态 shell；如果没有这一行，真实主循环不会被测试。
        event_kinds = [str(event.get("kind", "")) for event in events]  # 新增代码+RealHarnessAdapterTest：提取事件类型；如果没有这一行，断言会重复遍历。
        self.assertEqual("completed", result.status)  # 新增代码+RealHarnessAdapterTest：确认真实主循环完成；如果没有这一行，adapter 可能只发事件不返回终态。
        self.assertEqual("AGENT_HARNESS_SMOKE_OK", result.final_text)  # 新增代码+RealHarnessAdapterTest：确认最终文本来自 core run 返回值；如果没有这一行，GUI 可能写回空回答。
        self.assertIn("runtime_path", event_kinds)  # 新增代码+RealHarnessAdapterTest：确认第一等运行路径事件存在；如果没有这一行，验收无法证明走 agent_harness。
        self.assertIn("model_call_started", event_kinds)  # 新增代码+RealHarnessAdapterTest：确认 core 发起模型请求事件被映射；如果没有这一行，主循环证据不完整。
        self.assertIn("message_completed", event_kinds)  # 新增代码+RealHarnessAdapterTest：确认最终回答事件被映射；如果没有这一行，GUI 消息无法完成。
    # 新增代码+RealHarnessAdapterTest：测试函数结束，test_default_harness_adapter_enabled_runs_learning_agent_main_loop 到此结束；如果没有这个边界说明，用户不容易看出真实主循环合同。

    def test_default_harness_adapter_emits_read_only_tool_trace(self) -> None:  # 新增代码+RealHarnessReadOnlyTraceTest：测试函数开始，验证真实主循环能把 read_file 工具轨迹送进 GUI；如果没有这段，Phase 3 只会停在 mapper 层。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+RealHarnessReadOnlyTraceTest：创建隔离 workspace；如果没有这一行，read_file 可能读取真实项目文件。
            Path(directory, "AGENTS.md").write_text("OpenHarness read only fixture", encoding="utf-8")  # 新增代码+RealHarnessReadOnlyTraceTest：写入测试可读文件；如果没有这一行，read_file 会返回文件不存在。
            read_call = ToolCall(name="read_file", arguments={"path": "AGENTS.md"}, call_id="call_read_1")  # 新增代码+RealHarnessReadOnlyTraceTest：构造模型请求的只读工具调用；如果没有这一行，agent 不会进入工具循环。
            fake_model = ToolCallingFakeModel([ModelMessage(tool_calls=[read_call]), ModelMessage(text="READ_ONLY_TOOL_TRACE_OK")])  # 新增代码+RealHarnessReadOnlyTraceTest：安排假模型先读文件再最终回答；如果没有这一行，测试无法覆盖工具后继续回答。
            request = GuiAgentRunRequest(session_id="session_read", turn_id="turn_read", run_id="run_read", prompt="请只读 AGENTS.md", workspace=directory, provider_id="test-fake")  # 新增代码+RealHarnessReadOnlyTraceTest：构造真实 adapter 请求；如果没有这一行，adapter 没有工作区和身份。
            events: list[dict[str, object]] = []  # 新增代码+RealHarnessReadOnlyTraceTest：保存 GUI 事件；如果没有这一行，无法断言 TracePanel 输入。
            adapter = DefaultHarnessGuiAgentAdapter(enabled=True, model_factory=lambda _request: fake_model, max_turns=2, allowed_tool_names={"read_file"})  # 新增代码+RealHarnessReadOnlyTraceTest：启用真实 adapter 并只暴露 read_file；如果没有这一行，工具可能被隐藏或测试暴露过多工具。
            result = adapter.run(request, events.append, lambda: False)  # 新增代码+RealHarnessReadOnlyTraceTest：运行真实主循环；如果没有这一行，工具轨迹不会产生。
        event_kinds = [str(event.get("kind", "")) for event in events]  # 新增代码+RealHarnessReadOnlyTraceTest：提取事件类型；如果没有这一行，断言会难读。
        tool_started = next(event for event in events if event.get("kind") == "tool_started")  # 新增代码+RealHarnessReadOnlyTraceTest：找到工具开始事件；如果没有这一行，无法检查工具名。
        tool_finished = next(event for event in events if event.get("kind") == "tool_finished")  # 新增代码+RealHarnessReadOnlyTraceTest：找到工具结束事件；如果没有这一行，无法检查结果事件。
        self.assertEqual("completed", result.status)  # 新增代码+RealHarnessReadOnlyTraceTest：确认工具循环后主循环完成；如果没有这一行，工具后续回答可能中断。
        self.assertEqual("READ_ONLY_TOOL_TRACE_OK", result.final_text)  # 新增代码+RealHarnessReadOnlyTraceTest：确认最终回答来自第二轮模型；如果没有这一行，agent 可能停在工具结果。
        self.assertIn("tool_started", event_kinds)  # 新增代码+RealHarnessReadOnlyTraceTest：确认 GUI 看得到工具开始；如果没有这一行，TracePanel 没有起点。
        self.assertIn("tool_finished", event_kinds)  # 新增代码+RealHarnessReadOnlyTraceTest：确认 GUI 看得到工具结束；如果没有这一行，TracePanel 会一直 running。
        self.assertEqual("read_file", tool_started["payload"]["tool_name"])  # 新增代码+RealHarnessReadOnlyTraceTest：确认开始事件工具名正确；如果没有这一行，用户看不懂是哪种工具。
        self.assertEqual("read_file", tool_finished["payload"]["tool_name"])  # 新增代码+RealHarnessReadOnlyTraceTest：确认结束事件工具名正确；如果没有这一行，工具卡片无法合并首尾。
    # 新增代码+RealHarnessReadOnlyTraceTest：测试函数结束，test_default_harness_adapter_emits_read_only_tool_trace 到此结束；如果没有这个边界说明，用户不容易看出只读工具验收范围。

    def test_gui_run_manager_can_enter_real_harness_with_env_flags(self) -> None:  # 新增代码+RealHarnessAdapterTest：测试函数开始，验证 bridge 环境开关进入真实 adapter；如果没有这段，前端无法触发 core agent。
        from learning_agent.app.gui_bridge import GuiRunManager  # 新增代码+RealHarnessAdapterTest：延迟导入 run manager；如果没有这一行，测试无法覆盖 bridge 接线。

        old_runtime = os.environ.get("OPENHARNESS_GUI_AGENT_RUNTIME")  # 新增代码+RealHarnessAdapterTest：保存旧真实 runtime 开关；如果没有这一行，测试会污染外部环境。
        old_test_model = os.environ.get("OPENHARNESS_GUI_AGENT_TEST_MODEL")  # 新增代码+RealHarnessAdapterTest：保存旧测试模型开关；如果没有这一行，测试会污染外部环境。
        os.environ["OPENHARNESS_GUI_AGENT_RUNTIME"] = "enabled"  # 新增代码+RealHarnessAdapterTest：启用真实 harness adapter；如果没有这一行，bridge 会返回禁用 shell。
        os.environ["OPENHARNESS_GUI_AGENT_TEST_MODEL"] = "enabled"  # 新增代码+RealHarnessAdapterTest：让真实 adapter 使用离线模型；如果没有这一行，测试需要真实 OAuth。
        try:  # 新增代码+RealHarnessAdapterTest：保护环境恢复；如果没有这一行，失败会留下全局开关。
            with tempfile.TemporaryDirectory() as directory:  # 新增代码+RealHarnessAdapterTest：创建隔离 workspace；如果没有这一行，manager 会写真实 memory。
                manager = GuiRunManager(Path(directory))  # 新增代码+RealHarnessAdapterTest：创建 GUI run manager；如果没有这一行，bridge 接线没有被测对象。
                response = manager.start_message("default", "__real_harness__ AGENT_HARNESS_SMOKE", provider_id="openai")  # 新增代码+RealHarnessAdapterTest：提交真实 harness 触发 prompt；如果没有这一行，manager 默认仍走 fake。
                turn_id = str(response["turn_id"])  # 新增代码+RealHarnessAdapterTest：保存 turn id；如果没有这一行，事件过滤没有目标。
                deadline = time.time() + 8.0  # 新增代码+RealHarnessAdapterTest：设置后台等待截止；如果没有这一行，失败时可能无限等。
                event_types: list[str] = []  # 新增代码+RealHarnessAdapterTest：保存已观察事件类型；如果没有这一行，循环外无法断言。
                while time.time() < deadline:  # 新增代码+RealHarnessAdapterTest：轮询等待 worker 完成；如果没有这一行，异步事件可能还未写入。
                    event_types = [event.event_type for event in manager.event_store.list_events(limit=100) if event.turn_id == turn_id]  # 新增代码+RealHarnessAdapterTest：读取当前 turn 的事件；如果没有这一行，无法观察真实 adapter。
                    if "runtime_path" in event_types and "gui_turn_completed" in event_types:  # 新增代码+RealHarnessAdapterTest：等待真实路径和兼容完成事件都出现；如果没有这一行，测试可能过早断言。
                        break  # 新增代码+RealHarnessAdapterTest：满足条件后停止轮询；如果没有这一行，测试会浪费时间。
                    time.sleep(0.05)  # 新增代码+RealHarnessAdapterTest：短暂等待后台线程；如果没有这一行，循环会空转占 CPU。
        finally:  # 新增代码+RealHarnessAdapterTest：恢复环境变量；如果没有这一行，后续测试会受污染。
            if old_runtime is None:  # 新增代码+RealHarnessAdapterTest：旧 runtime 不存在时删除；如果没有这一行，会留下测试开关。
                os.environ.pop("OPENHARNESS_GUI_AGENT_RUNTIME", None)  # 新增代码+RealHarnessAdapterTest：清理 runtime 开关；如果没有这一行，后续普通 GUI 测试会误走真实 adapter。
            else:  # 新增代码+RealHarnessAdapterTest：旧 runtime 存在时恢复；如果没有这一行，用户原配置会丢。
                os.environ["OPENHARNESS_GUI_AGENT_RUNTIME"] = old_runtime  # 新增代码+RealHarnessAdapterTest：恢复 runtime 旧值；如果没有这一行，环境不干净。
            if old_test_model is None:  # 新增代码+RealHarnessAdapterTest：旧测试模型开关不存在时删除；如果没有这一行，会留下测试模型。
                os.environ.pop("OPENHARNESS_GUI_AGENT_TEST_MODEL", None)  # 新增代码+RealHarnessAdapterTest：清理测试模型开关；如果没有这一行，后续真实模型测试会误用假模型。
            else:  # 新增代码+RealHarnessAdapterTest：旧测试模型开关存在时恢复；如果没有这一行，用户原配置会丢。
                os.environ["OPENHARNESS_GUI_AGENT_TEST_MODEL"] = old_test_model  # 新增代码+RealHarnessAdapterTest：恢复测试模型旧值；如果没有这一行，环境不干净。
        self.assertIn("runtime_path", event_types)  # 新增代码+RealHarnessAdapterTest：确认 bridge 真实路径事件写入 status store；如果没有这一行，前端无法看到 agent_harness。
        self.assertIn("message_completed", event_types)  # 新增代码+RealHarnessAdapterTest：确认真实 adapter 的完成事件写入 status store；如果没有这一行，GUI 无法显示最终回答。
        self.assertIn("gui_turn_completed", event_types)  # 新增代码+RealHarnessAdapterTest：确认兼容生命周期完成；如果没有这一行，旧前端状态可能卡住。
    # 新增代码+RealHarnessAdapterTest：测试函数结束，test_gui_run_manager_can_enter_real_harness_with_env_flags 到此结束；如果没有这个边界说明，用户不容易看出 bridge 接线合同。

    def test_default_harness_adapter_preserves_none_as_full_tool_policy(self) -> None:  # 新增代码+GuiToolchainReuseTest：测试函数开始，确认 None 表示复用原有全量工具策略；如果没有这段，full_access 会被误收窄成空工具集。
        adapter = DefaultHarnessGuiAgentAdapter(enabled=True, allowed_tool_names=None)  # 新增代码+GuiToolchainReuseTest：创建不传白名单的真实 adapter shell；如果没有这一行，无法验证 full_access 的语义边界。
        self.assertIsNone(adapter.allowed_tool_names)  # 新增代码+GuiToolchainReuseTest：断言 None 被原样保留；如果没有这一行，GUI full_access 仍不能交给原有 catalog/policy/MCP 工具链路。
    # 新增代码+GuiToolchainReuseTest：测试函数结束，test_default_harness_adapter_preserves_none_as_full_tool_policy 到此结束；如果没有这个边界说明，用户不容易看出 full_access 合同。

    def test_runtime_payload_marks_full_tool_policy_as_tools_enabled(self) -> None:  # 新增代码+GuiToolchainReuseTest：测试函数开始，确认 runtime_path 对 full_access 诊断不再误报无工具；如果没有这段，GUI 验收会把全工具策略看成未接入。
        request = GuiAgentRunRequest(session_id="session_tools", turn_id="turn_tools", run_id="run_tools", prompt="诊断工具状态", workspace=".", provider_id="openai", permission_mode="full_access")  # 新增代码+GuiToolchainReuseTest：构造最小 GUI 请求；如果没有这一行，runtime payload 没有请求上下文。
        default_payload = RealHarnessGuiAgentAdapter()._runtime_payload(request)  # 新增代码+GuiToolchainReuseTest：读取默认无工具诊断；如果没有这一行，无法保护保守默认模式。
        full_access_payload = RealHarnessGuiAgentAdapter(allowed_tool_names=None)._runtime_payload(request)  # 新增代码+GuiToolchainReuseTest：读取显式 full_access 诊断；如果没有这一行，无法证明 None 等于原有全工具策略。
        self.assertFalse(default_payload["tools_enabled"])  # 新增代码+GuiToolchainReuseTest：确认默认省略白名单仍是无工具；如果没有这一行，Computer Use 默认门禁可能退化。
        self.assertTrue(full_access_payload["tools_enabled"])  # 新增代码+GuiToolchainReuseTest：确认显式 None 显示工具已启用；如果没有这一行，full_access 诊断会误导用户。
    # 新增代码+GuiToolchainReuseTest：测试函数结束，test_runtime_payload_marks_full_tool_policy_as_tools_enabled 到此结束；如果没有这个边界说明，用户不容易看出诊断语义。

    def test_gui_run_manager_maps_permission_modes_to_existing_tool_policy(self) -> None:  # 新增代码+GuiToolchainReuseTest：测试函数开始，验证 GUI 权限模式复用已有工具白名单；如果没有这段，权限下拉只是前端装饰。
        from learning_agent.app.gui_bridge import GuiRunManager, GuiTurn  # 新增代码+GuiToolchainReuseTest：延迟导入 manager 和 turn；如果没有这一行，测试无法覆盖真实 GUI 分叉逻辑。

        old_runtime = os.environ.get("OPENHARNESS_GUI_AGENT_RUNTIME")  # 新增代码+GuiToolchainReuseTest：保存旧 runtime 开关；如果没有这一行，测试会污染用户当前环境。
        old_default_mode = os.environ.get("OPENHARNESS_GUI_AGENT_DEFAULT_MODE")  # 新增代码+GuiToolchainReuseTest：保存旧默认 Agent Mode；如果没有这一行，测试结束后可能改变普通 GUI 行为。
        os.environ["OPENHARNESS_GUI_AGENT_RUNTIME"] = "real"  # 新增代码+GuiToolchainReuseTest：启用真实 adapter；如果没有这一行，manager 会返回禁用 shell，白名单语义没有意义。
        os.environ["OPENHARNESS_GUI_AGENT_DEFAULT_MODE"] = "agent"  # 新增代码+GuiToolchainReuseTest：让普通 prompt 也走真实 agent；如果没有这一行，测试无法验证正式 Agent Mode 入口。
        try:  # 新增代码+GuiToolchainReuseTest：保护环境变量恢复；如果没有这一行，断言失败会留下全局开关。
            with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiToolchainReuseTest：创建隔离 workspace；如果没有这一行，manager 会写入真实 memory 状态。
                Path(directory, "mcp_servers.json").write_text('{"servers":[{"name":"demo","command":"python","args":["-m","demo_mcp"]}]}', encoding="utf-8")  # 新增代码+GuiToolchainReuseTest：写入最小 MCP 配置但不启动；如果没有这一行，测试无法证明 GUI full_access 会复用现有 MCP registry。
                manager = GuiRunManager(Path(directory))  # 新增代码+GuiToolchainReuseTest：创建真实 GUI run manager；如果没有这一行，无法调用 adapter 选择逻辑。
                read_only_turn = GuiTurn(turn_id="turn_read_only", run_id="run_read_only", session_id="session", prompt="普通只读任务", permission_mode="read_only")  # 新增代码+GuiToolchainReuseTest：构造只读权限 turn；如果没有这一行，无法验证 read_only 工具边界。
                workspace_write_turn = GuiTurn(turn_id="turn_workspace_write", run_id="run_workspace_write", session_id="session", prompt="普通写入任务", permission_mode="workspace_write")  # 新增代码+GuiToolchainReuseTest：构造工作区写入权限 turn；如果没有这一行，write_file 不会被要求进入 GUI 链路。
                full_access_turn = GuiTurn(turn_id="turn_full_access", run_id="run_full_access", session_id="session", prompt="普通完全访问任务", permission_mode="full_access")  # 新增代码+GuiToolchainReuseTest：构造完全访问权限 turn；如果没有这一行，无法验证全量工具策略复用。
                read_only_adapter = manager._adapter_for_turn(read_only_turn)  # 新增代码+GuiToolchainReuseTest：读取只读模式 adapter；如果没有这一行，断言没有被测对象。
                workspace_write_adapter = manager._adapter_for_turn(workspace_write_turn)  # 新增代码+GuiToolchainReuseTest：读取工作区写入模式 adapter；如果没有这一行，无法检查写工具是否接上。
                full_access_adapter = manager._adapter_for_turn(full_access_turn)  # 新增代码+GuiToolchainReuseTest：读取完全访问模式 adapter；如果没有这一行，无法检查是否交给原工具策略。
        finally:  # 新增代码+GuiToolchainReuseTest：恢复环境变量；如果没有这一行，后续测试或真实 GUI 会继承本测试配置。
            if old_runtime is None:  # 新增代码+GuiToolchainReuseTest：判断旧 runtime 是否不存在；如果没有这一行，无法正确删除临时变量。
                os.environ.pop("OPENHARNESS_GUI_AGENT_RUNTIME", None)  # 新增代码+GuiToolchainReuseTest：删除临时 runtime 开关；如果没有这一行，测试后环境会误启真实 adapter。
            else:  # 新增代码+GuiToolchainReuseTest：旧 runtime 存在时走恢复分支；如果没有这一行，用户原配置会丢失。
                os.environ["OPENHARNESS_GUI_AGENT_RUNTIME"] = old_runtime  # 新增代码+GuiToolchainReuseTest：恢复用户原 runtime 值；如果没有这一行，环境不干净。
            if old_default_mode is None:  # 新增代码+GuiToolchainReuseTest：判断旧默认模式是否不存在；如果没有这一行，无法正确删除临时默认 Agent Mode。
                os.environ.pop("OPENHARNESS_GUI_AGENT_DEFAULT_MODE", None)  # 新增代码+GuiToolchainReuseTest：删除临时默认模式；如果没有这一行，其他测试会误走 Agent Mode。
            else:  # 新增代码+GuiToolchainReuseTest：旧默认模式存在时走恢复分支；如果没有这一行，用户原配置会丢失。
                os.environ["OPENHARNESS_GUI_AGENT_DEFAULT_MODE"] = old_default_mode  # 新增代码+GuiToolchainReuseTest：恢复用户原默认模式；如果没有这一行，环境不干净。
        self.assertEqual({"read_file", "list_dir"}, read_only_adapter.allowed_tool_names)  # 新增代码+GuiToolchainReuseTest：确认只读只开放读取和列目录；如果没有这一行，低风险模式可能暴露写工具。
        self.assertIn("write_file", workspace_write_adapter.allowed_tool_names)  # 新增代码+GuiToolchainReuseTest：确认工作区写入开放写文件工具；如果没有这一行，GUI 写入模式仍无法驱动 core 工具链路。
        self.assertIn("append_memory", workspace_write_adapter.allowed_tool_names)  # 新增代码+GuiToolchainReuseTest：确认工作区写入开放长期记忆工具；如果没有这一行，agent 无法通过 GUI 复用已有记忆写入能力。
        self.assertIsNone(full_access_adapter.allowed_tool_names)  # 新增代码+GuiToolchainReuseTest：确认完全访问不加白名单而复用原有工具策略；如果没有这一行，MCP、shell、Computer Use 等链路会被空集合误封死。
        self.assertTrue(full_access_adapter.mcp_tool_registry.has_servers())  # 新增代码+GuiToolchainReuseTest：确认 full_access adapter 挂上 workspace MCP registry；如果没有这一行，GUI 即使全权限也看不到 mcp_servers.json 外部工具链路。
    # 新增代码+GuiToolchainReuseTest：测试函数结束，test_gui_run_manager_maps_permission_modes_to_existing_tool_policy 到此结束；如果没有这个边界说明，用户不容易看出权限模式映射合同。
# 新增代码+RealHarnessAdapterTest：测试类段结束，RealHarnessAdapterTest 到此结束；如果没有这个边界说明，用户不容易看出本文件覆盖 Phase 0/1。


if __name__ == "__main__":  # 新增代码+RealHarnessAdapterTest：允许直接运行本文件；如果没有这一行，手动排查时不会启动 unittest。
    unittest.main()  # 新增代码+RealHarnessAdapterTest：执行测试主程序；如果没有这一行，直接运行文件不会跑测试。
