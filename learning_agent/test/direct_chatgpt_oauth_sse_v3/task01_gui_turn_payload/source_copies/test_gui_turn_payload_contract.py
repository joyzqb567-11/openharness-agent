import os  # 新增代码+DirectSSEPayloadTest：读取和覆盖运行时环境变量；如果没有这行，测试无法打开 direct_sse_fixture。
import tempfile  # 新增代码+DirectSSEPayloadTest：创建隔离 workspace；如果没有这行，测试会污染真实 memory。
import time  # 新增代码+DirectSSEPayloadTest：等待后台 GUI worker 完成；如果没有这行，异步断言会抢时序。
import unittest  # 新增代码+DirectSSEPayloadTest：沿用项目现有 unittest 风格；如果没有这行，测试类不会被发现。
from pathlib import Path  # 新增代码+DirectSSEPayloadTest：管理临时 workspace 路径；如果没有这行，Windows 路径拼接容易出错。
from unittest.mock import patch  # 新增代码+DirectSSEPayloadTest：安全覆盖环境变量；如果没有这行，测试会影响后续用例。


class GuiTurnPayloadContractTests(unittest.TestCase):  # 新增代码+DirectSSEPayloadTest：测试类段开始，锁定 GUI turn 结构化 payload 合同；如果没有这个类，provider/model 字段可能悄悄丢失。
    def _wait_for_terminal_turn(self, manager: object, turn_id: str) -> object:  # 新增代码+DirectSSEPayloadTest：函数段开始，等待后台 turn 进入终态；如果没有这段，测试会在 worker 完成前读取状态。
        deadline = time.time() + 4.0  # 新增代码+DirectSSEPayloadTest：设置最长等待时间；如果没有这行，worker 卡住时测试会永久挂起。
        while time.time() < deadline:  # 新增代码+DirectSSEPayloadTest：在超时前循环检查；如果没有这行，无法等待异步状态。
            with manager.lock:  # 新增代码+DirectSSEPayloadTest：按生产锁读取 turn；如果没有这行，可能读到半写状态。
                turn = manager.turns[turn_id]  # 新增代码+DirectSSEPayloadTest：读取目标 turn；如果没有这行，断言没有对象。
                if turn.status in {"completed", "failed", "cancelled"}:  # 新增代码+DirectSSEPayloadTest：识别 GUI 终态；如果没有这行，测试不知道何时停止等待。
                    return turn  # 新增代码+DirectSSEPayloadTest：返回终态 turn；如果没有这行，调用方拿不到最终状态。
            time.sleep(0.05)  # 新增代码+DirectSSEPayloadTest：短暂让出时间给后台线程；如果没有这行，循环会空转占 CPU。
        self.fail(f"GUI turn {turn_id} did not reach a terminal state.")  # 新增代码+DirectSSEPayloadTest：超时失败并带 turn id；如果没有这行，卡住时排查困难。
    # 新增代码+DirectSSEPayloadTest：函数段结束，_wait_for_terminal_turn 到此结束；如果没有边界说明，初学者不易看出它只负责等待。

    def test_invalid_optional_fields_fall_back_to_backend_defaults(self) -> None:  # 新增代码+DirectSSEPayloadTest：测试段开始，验证非法可选字段回落默认值；如果没有这段，坏前端值可能进入真实模型请求。
        from learning_agent.app.gui_bridge import GuiRunManager  # 新增代码+DirectSSEPayloadTest：导入待测 run manager；如果没有这行，测试没有后端目标。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectSSEPayloadTest：创建隔离 workspace；如果没有这行，状态事件会写入真实项目。
            manager = GuiRunManager(Path(directory))  # 新增代码+DirectSSEPayloadTest：创建隔离 GUI manager；如果没有这行，无法启动 turn。
            response = manager.start_message("conv_defaults", "hello", provider_id=None, model_id=None, reasoning_effort="wrong", permission_mode="unsafe")  # 新增代码+DirectSSEPayloadTest：提交非法可选字段；如果没有这行，默认值路径没有输入。
            turn = self._wait_for_terminal_turn(manager, str(response["turn_id"]))  # 新增代码+DirectSSEPayloadTest：等待后台完成；如果没有这行，可能读到 queued/running。
            self.assertEqual(turn.provider_id, "")  # 新增代码+DirectSSEPayloadTest：确认 provider 默认空；如果没有这行，非字符串 provider 可能变成 "None"。
            self.assertEqual(turn.model_id, "")  # 新增代码+DirectSSEPayloadTest：确认 model 默认空；如果没有这行，非字符串模型可能污染路由。
            self.assertEqual(turn.reasoning_effort, "high")  # 新增代码+DirectSSEPayloadTest：确认非法 reasoning 回落 high；如果没有这行，错误值可能发给模型 API。
            self.assertEqual(turn.permission_mode, "full_access")  # 新增代码+DirectSSEPayloadTest：确认非法权限回落 full_access；如果没有这行，错误权限值可能污染运行时。
    # 新增代码+DirectSSEPayloadTest：测试段结束，默认值合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_direct_sse_fixture_streams_selected_model_to_gui_events(self) -> None:  # 新增代码+DirectSSEPayloadTest：测试段开始，验证 selected model 进入后端并通过 SSE fixture 流式输出；如果没有这段，Task 1 纵切没有自动证据。
        from learning_agent.app.gui_bridge import GuiRunManager  # 新增代码+DirectSSEPayloadTest：导入待测 run manager；如果没有这行，测试没有后端目标。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectSSEPayloadTest：创建隔离 workspace；如果没有这行，状态事件会污染真实 memory。
            with patch.dict(os.environ, {"OPENHARNESS_OPENAI_RUNTIME": "direct_sse_fixture"}, clear=False):  # 新增代码+DirectSSEPayloadTest：打开 fixture runtime；如果没有这行，adapter 会走普通 fake streaming。
                manager = GuiRunManager(Path(directory))  # 新增代码+DirectSSEPayloadTest：创建隔离 GUI manager；如果没有这行，无法发起 turn。
                response = manager.start_message("conv_fixture", "请输出 OPENHARNESS_OK", provider_id="openai", model_id="gpt-5.5", reasoning_effort="ultra", permission_mode="full_access")  # 新增代码+DirectSSEPayloadTest：提交带选择字段的 prompt；如果没有这行，provider/model 到达后端无法验证。
                turn = self._wait_for_terminal_turn(manager, str(response["turn_id"]))  # 新增代码+DirectSSEPayloadTest：等待后台完成；如果没有这行，SSE 事件可能尚未写完。
                events = [event.to_dict() for event in manager.event_store.list_events(limit=50)]  # 新增代码+DirectSSEPayloadTest：读取状态事件事实源；如果没有这行，无法验证 GUI event stream。
        queued_payload = next(event["payload"] for event in events if event["event_type"] == "gui_turn_queued")  # 新增代码+DirectSSEPayloadTest：读取 queued 事件 payload；如果没有这行，无法证明后端收到路由字段。
        route_payload = next(event["payload"] for event in events if event["event_type"] == "direct_sse_route_selected")  # 新增代码+DirectSSEPayloadTest：读取 direct route 事件 payload；如果没有这行，无法证明 fixture runtime 已启用。
        delta_text = "".join(str(event["payload"].get("text_delta", "")) for event in events if event["event_type"] == "message_delta")  # 新增代码+DirectSSEPayloadTest：拼接流式 delta；如果没有这行，无法证明 OPENHARNESS_OK 是分片流出。
        self.assertEqual(turn.status, "completed")  # 新增代码+DirectSSEPayloadTest：确认 turn 完成；如果没有这行，失败或取消也可能被误判。
        self.assertEqual(turn.answer, "OPENHARNESS_OK")  # 新增代码+DirectSSEPayloadTest：确认最终文本来自 SSE done；如果没有这行，fixture 可能只发 delta 不写 final。
        self.assertEqual(queued_payload["provider_id"], "openai")  # 新增代码+DirectSSEPayloadTest：确认 provider 到达 queued 事件；如果没有这行，后端入口可能丢字段。
        self.assertEqual(queued_payload["model_id"], "gpt-5.5")  # 新增代码+DirectSSEPayloadTest：确认 model 到达 queued 事件；如果没有这行，模型选择无法驱动后续请求。
        self.assertEqual(route_payload["runtime"], "direct_sse_fixture")  # 新增代码+DirectSSEPayloadTest：确认 runtime 走 fixture direct SSE；如果没有这行，测试可能仍在普通 fake 路径。
        self.assertEqual(route_payload["transport"], "https_sse")  # 新增代码+DirectSSEPayloadTest：确认 transport 语义是 HTTPS SSE；如果没有这行，GUI 诊断无法区别 WebSocket。
        self.assertFalse(route_payload["websocket_enabled"])  # 新增代码+DirectSSEPayloadTest：确认 WebSocket 关闭；如果没有这行，Task 1 无法守住 V3 方向。
        self.assertFalse(route_payload["codex_cli_used"])  # 新增代码+DirectSSEPayloadTest：确认没有 Codex CLI fallback；如果没有这行，慢路径可能隐藏回归。
        self.assertEqual(delta_text, "OPENHARNESS_OK")  # 新增代码+DirectSSEPayloadTest：确认流式 delta 拼出目标文本；如果没有这行，GUI event stream 纵切没有被证明。
    # 新增代码+DirectSSEPayloadTest：测试段结束，direct SSE fixture 纵切合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


if __name__ == "__main__":  # 新增代码+DirectSSEPayloadTest：允许直接运行本测试文件；如果没有这行，手动调试需要记住 unittest 命令。
    unittest.main()  # 新增代码+DirectSSEPayloadTest：启动 unittest runner；如果没有这行，直接 python 文件不会执行测试。
