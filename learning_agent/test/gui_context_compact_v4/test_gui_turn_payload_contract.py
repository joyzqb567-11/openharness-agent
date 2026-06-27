import json  # 修改代码+GuiContextContractTest：导入 JSON 只用于把嵌套 messages 转成可搜索文本；如果没有这一行，测试无法稳定检查 Responses input 里的中文上下文。
import os  # 修改代码+GuiContextContractTest：导入 os 是为了配合 patch.dict 覆盖运行时开关；如果没有这一行，测试无法控制 Direct SSE fixture 路径。
import tempfile  # 修改代码+GuiContextContractTest：导入 tempfile 用来创建隔离 workspace；如果没有这一行，测试会污染用户真实 OpenHarness 状态目录。
import time  # 修改代码+GuiContextContractTest：导入 time 用来等待后台 GUI worker 完成；如果没有这一行，异步断言会抢在 worker 写状态前执行。
import unittest  # 修改代码+GuiContextContractTest：沿用项目已有 unittest 风格；如果没有这一行，测试类不会被标准 unittest/pytest 发现。
from pathlib import Path  # 修改代码+GuiContextContractTest：导入 Path 处理 Windows 临时路径；如果没有这一行，workspace 路径拼接容易出错。
from unittest.mock import patch  # 修改代码+GuiContextContractTest：导入 patch 用来安全覆盖环境变量；如果没有这一行，fixture runtime 会影响其它测试。


class GuiTurnPayloadContractTests(unittest.TestCase):  # 修改代码+GuiContextContractTest：测试类段开始，锁定 GUI turn 到 adapter 的 payload 合同；如果没有这个类，provider/model/context 字段可能静默丢失。
    def _wait_for_terminal_turn(self, manager: object, turn_id: str) -> object:  # 修改代码+GuiContextContractTest：函数段开始，等待后台 turn 进入终态；如果没有这段，测试会读到 queued/running 的半成品状态。
        deadline = time.time() + 4.0  # 修改代码+GuiContextContractTest：设置最多等待 4 秒；如果没有这一行，worker 卡住时测试会永久挂起。
        while time.time() < deadline:  # 修改代码+GuiContextContractTest：在超时前循环检查状态；如果没有这一行，异步 worker 没有完成机会。
            with manager.lock:  # 修改代码+GuiContextContractTest：使用生产锁读取 turns；如果没有这一行，测试可能读到并发写入中的不一致状态。
                turn = manager.turns[turn_id]  # 修改代码+GuiContextContractTest：读取目标 turn；如果没有这一行，断言没有具体对象。
                if turn.status in {"completed", "failed", "cancelled"}:  # 修改代码+GuiContextContractTest：识别 GUI 终态；如果没有这一行，测试不知道何时停止等待。
                    return turn  # 修改代码+GuiContextContractTest：返回最终 turn；如果没有这一行，调用方拿不到状态和答案。
            time.sleep(0.05)  # 修改代码+GuiContextContractTest：短暂停顿让后台线程推进；如果没有这一行，循环会空转占用 CPU。
        self.fail(f"GUI turn {turn_id} did not reach a terminal state.")  # 修改代码+GuiContextContractTest：超时后给出明确失败；如果没有这一行，卡住问题难以定位。
    # 修改代码+GuiContextContractTest：函数段结束，_wait_for_terminal_turn 到此结束；如果没有边界说明，用户不容易看出它只负责等待异步 turn。

    def test_invalid_optional_fields_fall_back_to_backend_defaults(self) -> None:  # 修改代码+GuiContextContractTest：测试段开始，验证非法可选字段会回落后端默认值；如果没有这个测试，坏前端值可能进入真实模型请求。
        from learning_agent.app.gui_bridge import GuiRunManager  # 修改代码+GuiContextContractTest：导入被测 run manager；如果没有这一行，测试没有后端目标。
        with tempfile.TemporaryDirectory() as directory:  # 修改代码+GuiContextContractTest：创建隔离 workspace；如果没有这一行，状态事件会写入真实项目。
            manager = GuiRunManager(Path(directory))  # 修改代码+GuiContextContractTest：创建 GUI manager；如果没有这一行，无法启动 turn。
            response = manager.start_message("conv_defaults", "hello", provider_id=None, model_id=None, reasoning_effort="wrong", permission_mode="unsafe")  # 修改代码+GuiContextContractTest：提交非法可选字段；如果没有这一行，默认值路径没有输入。
            turn = self._wait_for_terminal_turn(manager, str(response["turn_id"]))  # 修改代码+GuiContextContractTest：等待后台完成；如果没有这一行，可能读到 queued/running。
            self.assertEqual(turn.provider_id, "")  # 修改代码+GuiContextContractTest：确认非字符串 provider 回落为空；如果没有这一行，provider 可能变成字符串 None。
            self.assertEqual(turn.model_id, "")  # 修改代码+GuiContextContractTest：确认非字符串 model 回落为空；如果没有这一行，模型名可能污染路由。
            self.assertEqual(turn.reasoning_effort, "high")  # 修改代码+GuiContextContractTest：确认非法 reasoning 回落 high；如果没有这一行，错误枚举可能发给模型 API。
            self.assertEqual(turn.permission_mode, "full_access")  # 修改代码+GuiContextContractTest：确认非法权限回落 full_access；如果没有这一行，权限语义会被坏值污染。
    # 修改代码+GuiContextContractTest：测试段结束，默认值合同到此结束；如果没有边界说明，用户不容易看出本测试只覆盖字段清洗。

    def test_direct_sse_fixture_streams_selected_model_to_gui_events(self) -> None:  # 修改代码+GuiContextContractTest：测试段开始，验证 selected model 进入后端并通过 SSE fixture 流式输出；如果没有这个测试，模型菜单到后端的链路可能断开。
        from learning_agent.app.gui_bridge import GuiRunManager  # 修改代码+GuiContextContractTest：导入被测 run manager；如果没有这一行，测试无法覆盖 GUI bridge。
        with tempfile.TemporaryDirectory() as directory:  # 修改代码+GuiContextContractTest：创建隔离 workspace；如果没有这一行，测试会污染真实 memory。
            with patch.dict(os.environ, {"OPENHARNESS_OPENAI_RUNTIME": "direct_sse_fixture"}, clear=False):  # 修改代码+GuiContextContractTest：打开 fixture runtime；如果没有这一行，adapter 会走普通 fake streaming。
                manager = GuiRunManager(Path(directory))  # 修改代码+GuiContextContractTest：创建隔离 GUI manager；如果没有这一行，无法发起 turn。
                response = manager.start_message("conv_fixture", "请输出 OPENHARNESS_OK", provider_id="openai", model_id="gpt-5.5", reasoning_effort="ultra", permission_mode="full_access")  # 修改代码+GuiContextContractTest：提交带模型路由字段的 prompt；如果没有这一行，provider/model 到达后端无法验证。
                turn = self._wait_for_terminal_turn(manager, str(response["turn_id"]))  # 修改代码+GuiContextContractTest：等待后台完成；如果没有这一行，SSE 事件可能尚未写完。
                events = [event.to_dict() for event in manager.event_store.list_events(limit=50)]  # 修改代码+GuiContextContractTest：读取状态事件事实源；如果没有这一行，无法验证 GUI event stream。
        queued_payload = next(event["payload"] for event in events if event["event_type"] == "gui_turn_queued")  # 修改代码+GuiContextContractTest：读取 queued 事件 payload；如果没有这一行，无法证明入口收到路由字段。
        route_payload = next(event["payload"] for event in events if event["event_type"] == "direct_sse_route_selected")  # 修改代码+GuiContextContractTest：读取 direct route 事件 payload；如果没有这一行，无法证明 fixture runtime 已启用。
        delta_text = "".join(str(event["payload"].get("text_delta", "")) for event in events if event["event_type"] == "message_delta")  # 修改代码+GuiContextContractTest：拼接流式 delta；如果没有这一行，无法证明 OPENHARNESS_OK 是分片流出。
        self.assertEqual(turn.status, "completed")  # 修改代码+GuiContextContractTest：确认 turn 完成；如果没有这一行，失败或取消也可能被误判。
        self.assertEqual(turn.answer, "OPENHARNESS_OK")  # 修改代码+GuiContextContractTest：确认最终文本来自 SSE done；如果没有这一行，fixture 可能只发 delta 不写 final。
        self.assertEqual(queued_payload["provider_id"], "openai")  # 修改代码+GuiContextContractTest：确认 provider 到达 queued 事件；如果没有这一行，后端入口可能丢字段。
        self.assertEqual(queued_payload["model_id"], "gpt-5.5")  # 修改代码+GuiContextContractTest：确认 model 到达 queued 事件；如果没有这一行，模型选择无法驱动后续请求。
        self.assertEqual(route_payload["runtime"], "direct_sse_fixture")  # 修改代码+GuiContextContractTest：确认 runtime 走 fixture direct SSE；如果没有这一行，测试可能仍在 fake 路径。
        self.assertEqual(route_payload["transport"], "https_sse")  # 修改代码+GuiContextContractTest：确认 transport 是 HTTPS SSE；如果没有这一行，GUI 诊断无法区分 WebSocket。
        self.assertFalse(route_payload["websocket_enabled"])  # 修改代码+GuiContextContractTest：确认 WebSocket 关闭；如果没有这一行，慢路径回归不明显。
        self.assertFalse(route_payload["codex_cli_used"])  # 修改代码+GuiContextContractTest：确认没有 Codex CLI fallback；如果没有这一行，旧慢路径可能被隐藏。
        self.assertEqual(delta_text, "OPENHARNESS_OK")  # 修改代码+GuiContextContractTest：确认流式 delta 拼出目标文本；如果没有这一行，GUI event stream 纵切没有被证明。
    # 修改代码+GuiContextContractTest：测试段结束，Direct SSE fixture 合同到此结束；如果没有边界说明，用户不容易看出覆盖范围。

    def test_gui_manager_does_not_send_only_latest_prompt_to_adapter(self) -> None:  # 新增代码+GuiContextEvidenceLock：测试段开始，证明第二轮 GUI 请求必须带第一轮上下文；如果没有这个测试，latest-prompt-only 回归不会被发现。
        from learning_agent.app.gui_agent_adapter import GuiAgentRunResult  # 新增代码+GuiContextEvidenceLock：导入 adapter 结果对象；如果没有这一行，SpyAdapter 无法返回合法完成结果。
        from learning_agent.app.gui_bridge import GuiRunManager  # 新增代码+GuiContextEvidenceLock：导入被测 GUI run manager；如果没有这一行，测试无法覆盖真实 bridge 调用路径。
        captured_requests = []  # 新增代码+GuiContextEvidenceLock：保存 SpyAdapter 收到的请求；如果没有这一行，测试无法检查第二轮 request。

        class SpyAdapter:  # 新增代码+GuiContextEvidenceLock：类段开始，记录 bridge 传给 adapter 的请求；如果没有这个类，测试只能间接猜测 payload。
            def run(self, request, emit_event, is_cancelled):  # 新增代码+GuiContextEvidenceLock：函数段开始，模拟 adapter.run 合同；如果没有这个函数，GuiRunManager 无法执行测试 adapter。
                captured_requests.append(request)  # 新增代码+GuiContextEvidenceLock：记录真实请求对象；如果没有这一行，测试拿不到 messages 字段。
                return GuiAgentRunResult(status="completed", final_text="spy ok")  # 新增代码+GuiContextEvidenceLock：返回完成结果让 worker 收尾；如果没有这一行，turn 会卡在 running。
            # 新增代码+GuiContextEvidenceLock：函数段结束，SpyAdapter.run 到此结束；如果没有边界说明，用户不容易看出 spy 只负责记录请求。
        # 新增代码+GuiContextEvidenceLock：类段结束，SpyAdapter 到此结束；如果没有边界说明，用户不容易看出 spy 的测试范围。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiContextEvidenceLock：创建隔离 workspace；如果没有这一行，测试会污染真实项目状态。
            manager = GuiRunManager(Path(directory), agent_adapter=SpyAdapter())  # 新增代码+GuiContextEvidenceLock：用 SpyAdapter 创建 manager；如果没有这一行，测试会走默认 fake adapter 而无法捕获请求。
            first_response = manager.start_message("conv_context", "请记住测试代码 ALPHA_CONTEXT_927")  # 新增代码+GuiContextEvidenceLock：提交第一轮事实；如果没有这一行，第二轮没有可回忆上下文。
            self._wait_for_terminal_turn(manager, str(first_response["turn_id"]))  # 新增代码+GuiContextEvidenceLock：等待第一轮完成；如果没有这一行，第二轮可能在历史写入前开始。
            second_response = manager.start_message("conv_context", "刚才的测试代码是什么？")  # 新增代码+GuiContextEvidenceLock：提交第二轮追问；如果没有这一行，无法复现上下文丢失场景。
            self._wait_for_terminal_turn(manager, str(second_response["turn_id"]))  # 新增代码+GuiContextEvidenceLock：等待第二轮完成；如果没有这一行，captured_requests 可能还没写完。

        second_request = captured_requests[1]  # 新增代码+GuiContextEvidenceLock：取第二轮 adapter 请求；如果没有这一行，断言无法锁定追问请求。
        self.assertTrue(hasattr(second_request, "messages"))  # 新增代码+GuiContextEvidenceLock：要求请求对象有 messages 字段；如果没有这一行，旧 prompt-only 合同会漏过。
        joined_request_text = json.dumps(second_request.messages, ensure_ascii=False)  # 新增代码+GuiContextEvidenceLock：把 messages 转成可搜索文本；如果没有这一行，无法统一检查嵌套 content。
        self.assertIn("ALPHA_CONTEXT_927", joined_request_text)  # 新增代码+GuiContextEvidenceLock：断言第一轮事实进入第二轮请求；如果没有这一行，latest-prompt-only 缺陷不会被锁住。
        self.assertIn("刚才的测试代码是什么？", joined_request_text)  # 新增代码+GuiContextEvidenceLock：断言当前 prompt 仍在请求里；如果没有这一行，修复可能只带历史不带当前问题。
    # 新增代码+GuiContextEvidenceLock：测试段结束，证据锁到此结束；如果没有边界说明，用户不容易看出这是最新 prompt 缺陷复现测试。

    def test_gui_manager_records_privacy_safe_context_budget_event(self) -> None:  # 新增代码+GuiContextBudgetEventTest：测试段开始，验证 GUI bridge 会记录脱敏上下文预算事件；如果没有这个测试，右侧事件面板可能泄漏原始用户文本也没人发现。
        from learning_agent.app.gui_agent_adapter import GuiAgentRunResult  # 新增代码+GuiContextBudgetEventTest：导入合法 adapter 返回对象；如果没有这一行，SpyAdapter 无法让后台 worker 正常结束。
        from learning_agent.app.gui_bridge import GuiRunManager  # 新增代码+GuiContextBudgetEventTest：导入真实 GUI manager；如果没有这一行，测试无法覆盖 bridge 写事件的路径。

        class SpyAdapter:  # 新增代码+GuiContextBudgetEventTest：类段开始，用最小 adapter 避免真实网络调用；如果没有这个类，测试会依赖外部模型服务。
            def run(self, request, emit_event, is_cancelled):  # 新增代码+GuiContextBudgetEventTest：函数段开始，模拟 adapter.run 合同；如果没有这个函数，GuiRunManager 无法执行测试 adapter。
                return GuiAgentRunResult(status="completed", final_text="spy ok")  # 新增代码+GuiContextBudgetEventTest：返回完成结果；如果没有这一行，turn 会一直停在 running 或 queued。
            # 新增代码+GuiContextBudgetEventTest：函数段结束，SpyAdapter.run 到此结束；如果没有边界说明，用户不容易看出 spy 只负责完成 turn。
        # 新增代码+GuiContextBudgetEventTest：类段结束，SpyAdapter 到此结束；如果没有边界说明，用户不容易看出这里没有真实模型调用。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiContextBudgetEventTest：创建隔离 workspace；如果没有这一行，测试事件会污染用户真实 OpenHarness 状态。
            manager = GuiRunManager(Path(directory), agent_adapter=SpyAdapter())  # 新增代码+GuiContextBudgetEventTest：创建带 spy 的 manager；如果没有这一行，测试无法捕获 context_budget 事件。
            response = manager.start_message("conv_budget", "请记住测试代码 ALPHA_CONTEXT_927")  # 新增代码+GuiContextBudgetEventTest：提交包含敏感测试词的 prompt；如果没有这一行，无法验证事件 payload 是否脱敏。
            self._wait_for_terminal_turn(manager, str(response["turn_id"]))  # 新增代码+GuiContextBudgetEventTest：等待后台完成；如果没有这一行，事件可能还没写入就被断言读取。
            events = [event.to_dict() for event in manager.event_store.list_events(limit=50)]  # 新增代码+GuiContextBudgetEventTest：读取统一事件流；如果没有这一行，测试无法检查 GUI 右侧状态面板的数据来源。

        payload = next(event["payload"] for event in events if event["event_type"] == "context_budget")  # 新增代码+GuiContextBudgetEventTest：取出 context_budget payload；如果没有这一行，断言无法定位上下文预算事件。
        payload_text = json.dumps(payload, ensure_ascii=False)  # 新增代码+GuiContextBudgetEventTest：把 payload 转成可搜索文本；如果没有这一行，嵌套字段里的泄漏不容易被发现。
        self.assertIn("estimated_chars_before", payload)  # 新增代码+GuiContextBudgetEventTest：确认事件包含压缩前字符估算；如果没有这一行，GUI 缺少上下文规模证据。
        self.assertIn("estimated_chars_after", payload)  # 新增代码+GuiContextBudgetEventTest：确认事件包含压缩后字符估算；如果没有这一行，GUI 缺少压缩收益证据。
        self.assertNotIn("ALPHA_CONTEXT_927", payload_text)  # 新增代码+GuiContextBudgetEventTest：确认可见事件不泄漏原始 prompt；如果没有这一行，调试面板可能暴露用户隐私。
    # 新增代码+GuiContextBudgetEventTest：测试段结束，context_budget 脱敏事件测试到此结束；如果没有边界说明，用户不容易看出本测试只锁事件安全。


if __name__ == "__main__":  # 修改代码+GuiContextContractTest：允许直接运行本测试文件；如果没有这一行，手动调试需要记住 unittest 命令。
    unittest.main()  # 修改代码+GuiContextContractTest：启动 unittest runner；如果没有这一行，直接 python 文件不会执行测试。
