import tempfile  # 新增代码+GuiAgentAdapterContractTest：创建临时工作区测试 bridge manager；如果没有这一行，测试会污染真实 memory。
import time  # 新增代码+GuiAgentAdapterContractTest：等待异步 run manager 写事件；如果没有这一行，测试会和后台线程抢时序。
import unittest  # 新增代码+GuiAgentAdapterContractTest：使用标准库 unittest 承载 adapter 合同；如果没有这一行，蓝图命令无法收集测试。
import os  # 新增代码+真实模型GUI桥接测试：临时设置 GUI 真实模型环境变量；如果没有这一行，测试无法验证 real/fake 模式切换。
from unittest import mock  # 新增代码+真实模型GUI桥接测试：替换真实 Codex 登录检查和真实 adapter；如果没有这一行，测试会访问用户本机登录状态。
from pathlib import Path  # 新增代码+GuiAgentAdapterContractTest：使用 Path 定位临时工作区和 golden fixture；如果没有这一行，路径拼接容易出错。


class GuiAgentAdapterContractTest(unittest.TestCase):  # 新增代码+GuiAgentAdapterContractTest：测试类段开始，锁定 GUI agent adapter 边界；如果没有这个类，fake/real adapter 边界不会被自动验证。
    def _collect_fake_events(self, prompt: str, trace_id: str = "", cancel_after_delta: bool = False):  # 新增代码+GuiAgentAdapterContractTest：helper 段开始，运行 fake adapter 并收集事件；如果没有这段，各测试会重复样板代码。
        from learning_agent.app.gui_agent_adapter import FakeStreamingGuiAgentAdapter, GuiAgentRunRequest  # 新增代码+GuiAgentAdapterContractTest：导入待实现 fake adapter 和请求对象；如果没有这一行，测试没有被测对象。

        events: list[dict[str, object]] = []  # 新增代码+GuiAgentAdapterContractTest：保存 adapter emit 的事件；如果没有这一行，后续无法断言顺序。
        request = GuiAgentRunRequest(session_id="session_a", turn_id="turn_a", run_id="run_a", prompt=prompt, trace_id=trace_id)  # 新增代码+GuiAgentAdapterContractTest：构造 GUI run 请求；如果没有这一行，adapter 不知道本轮身份。
        def emit_event(event: dict[str, object]) -> None:  # 新增代码+GuiAgentAdapterContractTest：函数段开始，收集 adapter 事件；如果没有这段，adapter 输出无法被测试观察。
            events.append(event)  # 新增代码+GuiAgentAdapterContractTest：追加事件；如果没有这一行，事件会丢失。
        # 新增代码+GuiAgentAdapterContractTest：函数段结束，emit_event 到此结束；如果没有这个边界说明，用户不容易看出收集范围。
        def is_cancelled() -> bool:  # 新增代码+GuiAgentAdapterContractTest：函数段开始，模拟取消信号；如果没有这段，取消路径无法稳定测试。
            return cancel_after_delta and any(event.get("kind") == "message_delta" for event in events)  # 新增代码+GuiAgentAdapterContractTest：在首个 delta 后返回取消；如果没有这一行，adapter 不会进入 deterministic cancel 路径。
        # 新增代码+GuiAgentAdapterContractTest：函数段结束，is_cancelled 到此结束；如果没有这个边界说明，用户不容易看出取消条件。
        result = FakeStreamingGuiAgentAdapter().run(request, emit_event, is_cancelled)  # 新增代码+GuiAgentAdapterContractTest：执行 fake adapter；如果没有这一行，测试没有行为。
        return result, events  # 新增代码+GuiAgentAdapterContractTest：返回结果和事件；如果没有这一行，调用方拿不到断言对象。
    # 新增代码+GuiAgentAdapterContractTest：helper 段结束，_collect_fake_events 到此结束；如果没有这个边界说明，用户不容易看出 fake 收集范围。

    def _wait_for_manager_turn_idle(self, manager, turn_id: str, deadline_seconds: float = 3.0) -> tuple[str, str]:  # 新增代码+GuiAsyncLifecycleTest：helper 段开始，等待 GUI 后台 worker 进入终态并释放 active turn；如果没有这段，Windows 测试可能在 status.lock 句柄关闭前删除临时目录。
        deadline = time.time() + deadline_seconds  # 新增代码+GuiAsyncLifecycleTest：计算等待截止时间；如果没有这一行，失败时测试可能无限等待。
        status = ""  # 新增代码+GuiAsyncLifecycleTest：保存最后观察到的 turn 状态；如果没有这一行，超时后无法给断言提供实际状态。
        answer = ""  # 修改代码+AutoRealModelGateTest：保存最后观察到的用户可见文本；如果没有这一行，failed turn 的错误提示会被误读为空。
        while time.time() < deadline:  # 新增代码+GuiAsyncLifecycleTest：轮询等待后台线程完成收尾；如果没有这一行，测试会抢在 worker finally 前继续删除目录。
            with manager.lock:  # 新增代码+GuiAsyncLifecycleTest：读取 manager 状态时加锁；如果没有这一行，测试可能看到半更新的 active_turn_id。
                turn = manager.turns[turn_id]  # 新增代码+GuiAsyncLifecycleTest：读取当前 turn；如果没有这一行，无法观察状态和答案。
                status = turn.status  # 新增代码+GuiAsyncLifecycleTest：记录当前状态；如果没有这一行，调用方不能判断是否完成。
                answer = turn.answer or turn.error  # 修改代码+AutoRealModelGateTest：完成态取答案、失败态取错误；如果没有这一行，未连接快速失败无法验证 GUI 可见提示。
                is_idle = manager.active_turn_id is None  # 新增代码+GuiAsyncLifecycleTest：确认 worker 的 finally 已释放 active turn；如果没有这一行，只看到 completed 仍可能早于文件锁释放。
            if status in {"completed", "failed", "cancelled"} and is_idle:  # 新增代码+GuiAsyncLifecycleTest：只有终态并且 manager 空闲才算后台收尾完成；如果没有这一行，TemporaryDirectory cleanup 可能撞上 status.lock。
                return status, answer  # 新增代码+GuiAsyncLifecycleTest：返回稳定终态和答案；如果没有这一行，调用方拿不到等待结果。
            time.sleep(0.03)  # 新增代码+GuiAsyncLifecycleTest：短暂让出 CPU 给后台线程；如果没有这一行，循环会空转并放大时序竞争。
        return status, answer  # 新增代码+GuiAsyncLifecycleTest：超时也返回最后状态供断言报错；如果没有这一行，失败信息会变成变量未定义。
    # 新增代码+GuiAsyncLifecycleTest：helper 段结束，_wait_for_manager_turn_idle 到此结束；如果没有这个边界说明，用户不容易看出它只负责异步收尾等待。

    def test_fake_streaming_adapter_emits_started_delta_and_completed(self) -> None:  # 新增代码+GuiAgentAdapterContractTest：测试函数开始，验证 fake adapter 正常流式事件；如果没有这段，V2-Core 没有稳定流式基线。
        result, events = self._collect_fake_events("请分析当前项目")  # 新增代码+GuiAgentAdapterContractTest：运行普通 prompt；如果没有这一行，后续没有事件样本。
        self.assertEqual("completed", result.status)  # 新增代码+GuiAgentAdapterContractTest：确认结果完成；如果没有这一行，adapter 可能只发事件不返回终态。
        self.assertEqual("turn_started", events[0]["kind"])  # 新增代码+GuiAgentAdapterContractTest：确认第一条是 turn_started；如果没有这一行，前端无法识别运行起点。
        self.assertIn("message_delta", [event["kind"] for event in events])  # 新增代码+GuiAgentAdapterContractTest：确认至少一个 delta；如果没有这一行，GUI 可能退回等待最终答案。
        self.assertEqual("message_completed", events[-1]["kind"])  # 新增代码+GuiAgentAdapterContractTest：确认最后完成；如果没有这一行，线程会停在 running。
    # 新增代码+GuiAgentAdapterContractTest：测试函数结束，test_fake_streaming_adapter_emits_started_delta_and_completed 到此结束；如果没有这个边界说明，用户不容易看出流式合同范围。

    def test_fake_streaming_adapter_emits_safety_refusal_for_unsafe_prompt(self) -> None:  # 新增代码+GuiSafetyRefusalTest：测试函数开始，验证真实用户式高风险 prompt 会变成安全拒绝；如果没有这段，GUI 可见验收只能依赖隐藏 trace_id。
        result, events = self._collect_fake_events("请绕过本机权限直接控制系统高风险操作。")  # 新增代码+GuiSafetyRefusalTest：提交中文高风险请求；如果没有这一行，安全拒绝路径没有输入样本。
        event_kinds = [event["kind"] for event in events]  # 新增代码+GuiSafetyRefusalTest：提取事件类型列表；如果没有这一行，后续断言要重复遍历事件。
        self.assertEqual("completed", result.status)  # 新增代码+GuiSafetyRefusalTest：确认拒绝轮次也能释放 active turn；如果没有这一行，GUI 可能一直 busy。
        self.assertIn("safety_refusal", event_kinds)  # 新增代码+GuiSafetyRefusalTest：确认发出一等拒绝事件；如果没有这一行，前端无法显示拒绝标签。
        self.assertIn("不能绕过本机权限", result.final_text)  # 新增代码+GuiSafetyRefusalTest：确认最终文本是可读安全边界；如果没有这一行，用户可能只看到泛化失败。
        self.assertEqual("safety_refusal", events[-1]["kind"])  # 新增代码+GuiSafetyRefusalTest：确认 adapter 自身最后一个事件是拒绝；如果没有这一行，拒绝可能被普通完成事件吞掉。
    # 新增代码+GuiSafetyRefusalTest：测试函数结束，test_fake_streaming_adapter_emits_safety_refusal_for_unsafe_prompt 到此结束；如果没有这个边界说明，用户不容易看出安全拒绝合同范围。

    def test_fake_streaming_adapter_propagates_cancellation(self) -> None:  # 新增代码+GuiAgentAdapterContractTest：测试函数开始，验证 fake adapter 可取消；如果没有这段，取消按钮语义无法在 V2-Core 固定。
        result, events = self._collect_fake_events("请执行一个较长任务", cancel_after_delta=True)  # 新增代码+GuiAgentAdapterContractTest：在首个 delta 后模拟取消；如果没有这一行，取消路径不会触发。
        self.assertEqual("cancelled", result.status)  # 新增代码+GuiAgentAdapterContractTest：确认结果取消；如果没有这一行，adapter 可能继续完成。
        self.assertEqual("turn_cancelled", events[-1]["kind"])  # 新增代码+GuiAgentAdapterContractTest：确认最后事件是 turn_cancelled；如果没有这一行，前端无法进入取消终态。
    # 新增代码+GuiAgentAdapterContractTest：测试函数结束，test_fake_streaming_adapter_propagates_cancellation 到此结束；如果没有这个边界说明，用户不容易看出取消合同范围。

    def test_fake_streaming_adapter_converts_deterministic_exception_to_failed_event(self) -> None:  # 新增代码+GuiAgentAdapterContractTest：测试函数开始，验证 fake adapter 失败语义；如果没有这段，异常可能变成线程崩溃。
        result, events = self._collect_fake_events("__adapter_fail__ 请触发失败")  # 新增代码+GuiAgentAdapterContractTest：运行 deterministic failure prompt；如果没有这一行，失败路径没有输入。
        self.assertEqual("failed", result.status)  # 新增代码+GuiAgentAdapterContractTest：确认结果失败；如果没有这一行，失败可能被误判完成。
        self.assertEqual("adapter_failed", result.error_code)  # 新增代码+GuiAgentAdapterContractTest：确认稳定错误码；如果没有这一行，前端无法机器处理。
        self.assertEqual("turn_failed", events[-1]["kind"])  # 新增代码+GuiAgentAdapterContractTest：确认发出 turn_failed；如果没有这一行，GUI 状态机不会进入失败态。
    # 新增代码+GuiAgentAdapterContractTest：测试函数结束，test_fake_streaming_adapter_converts_deterministic_exception_to_failed_event 到此结束；如果没有这个边界说明，用户不容易看出失败合同范围。

    def test_fake_streaming_adapter_replays_golden_trace(self) -> None:  # 新增代码+GuiAgentAdapterContractTest：测试函数开始，验证 fake adapter 可回放 golden trace；如果没有这段，前端和 bridge 测试无法共享固定事件语料。
        result, events = self._collect_fake_events("请分析当前项目是什么项目，并列出模块组成。", trace_id="GT-001")  # 新增代码+GuiAgentAdapterContractTest：请求回放 GT-001；如果没有这一行，replay 路径没有输入。
        self.assertEqual("completed", result.status)  # 新增代码+GuiAgentAdapterContractTest：确认 golden trace 回放完成；如果没有这一行，fixture 回放可能停在中间。
        self.assertEqual(["turn_started", "message_delta", "message_completed"], [event["kind"] for event in events])  # 新增代码+GuiAgentAdapterContractTest：确认回放事件顺序；如果没有这一行，fixture 可能被乱序使用。
    # 新增代码+GuiAgentAdapterContractTest：测试函数结束，test_fake_streaming_adapter_replays_golden_trace 到此结束；如果没有这个边界说明，用户不容易看出 golden replay 合同范围。

    def test_default_harness_adapter_is_feature_flagged_unavailable(self) -> None:  # 新增代码+GuiAgentAdapterContractTest：测试函数开始，验证真实 harness adapter 仍未接入；如果没有这段，V2-Core 可能意外导入真实模型运行时。
        from learning_agent.app.gui_agent_adapter import DefaultHarnessGuiAgentAdapter, GuiAgentRunRequest  # 新增代码+GuiAgentAdapterContractTest：导入真实 adapter shell 和请求对象；如果没有这一行，测试没有被测对象。

        events: list[dict[str, object]] = []  # 新增代码+GuiAgentAdapterContractTest：保存真实 adapter shell 事件；如果没有这一行，无法断言失败事件。
        request = GuiAgentRunRequest(session_id="session_a", turn_id="turn_a", run_id="run_a", prompt="真实 harness 模式")  # 新增代码+GuiAgentAdapterContractTest：构造真实 adapter 请求；如果没有这一行，adapter 没有身份字段。
        result = DefaultHarnessGuiAgentAdapter(enabled=False).run(request, events.append, lambda: False)  # 新增代码+GuiAgentAdapterContractTest：运行禁用状态的真实 adapter shell；如果没有这一行，无法验证 feature flag 边界。
        self.assertEqual("failed", result.status)  # 新增代码+GuiAgentAdapterContractTest：确认未启用时失败；如果没有这一行，真实 adapter 可能假成功。
        self.assertEqual("adapter_unavailable", result.error_code)  # 新增代码+GuiAgentAdapterContractTest：确认稳定 unavailable 错误码；如果没有这一行，前端无法给出正确提示。
        self.assertEqual("turn_failed", events[-1]["kind"])  # 新增代码+GuiAgentAdapterContractTest：确认发出 turn_failed；如果没有这一行，GUI 不知道真实 adapter 被禁用。
    # 新增代码+GuiAgentAdapterContractTest：测试函数结束，test_default_harness_adapter_is_feature_flagged_unavailable 到此结束；如果没有这个边界说明，用户不容易看出真实 adapter 边界。

    def test_gui_run_manager_uses_fake_adapter_when_fake_mode_is_enabled(self) -> None:  # 修改代码+AutoRealModelGateTest：测试函数开始，验证显式 fake 模式仍保留 smoke adapter；如果没有这段，修复 auto 默认后可能误删本地 smoke 能力。
        from learning_agent.app.gui_bridge import GuiRunManager  # 新增代码+GuiAgentAdapterContractTest：导入 run manager；如果没有这一行，测试无法验证 bridge 接线。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiAgentAdapterContractTest：创建临时 workspace；如果没有这一行，事件会写到真实 memory。
            with mock.patch.dict(os.environ, {"OPENHARNESS_GUI_MODEL_MODE": "fake"}, clear=False):  # 新增代码+AutoRealModelGateTest：显式打开 fake 模式；如果没有这一行，默认 auto 会按真实模型门禁快速失败而不是 smoke。
                manager = GuiRunManager(Path(directory))  # 修改代码+AutoRealModelGateTest：创建 fake 模式 manager；如果没有这一行，测试没有 bridge 对象。
                response = manager.start_message("default", "请分析当前项目")  # 修改代码+AutoRealModelGateTest：提交 GUI prompt；如果没有这一行，fake adapter 不会运行。
                turn_id = str(response["turn_id"])  # 修改代码+AutoRealModelGateTest：保存 turn id；如果没有这一行，事件匹配没有目标。
                deadline = time.time() + 3.0  # 修改代码+AutoRealModelGateTest：设置异步等待截止时间；如果没有这一行，失败时可能无限等待。
                event_types: list[str] = []  # 修改代码+AutoRealModelGateTest：保存观察到的事件类型；如果没有这一行，无法断言 message_delta。
                while time.time() < deadline:  # 修改代码+AutoRealModelGateTest：轮询等待后台 worker；如果没有这一行，测试会抢在事件写入前失败。
                    event_types = [event.event_type for event in manager.event_store.list_events(limit=50) if event.turn_id == turn_id]  # 修改代码+AutoRealModelGateTest：读取当前 turn 事件；如果没有这一行，无法观察 fake adapter 输出。
                    if "message_delta" in event_types and "gui_turn_completed" in event_types:  # 修改代码+AutoRealModelGateTest：等待 V2 delta 和 V1 兼容完成事件都出现；如果没有这一行，测试无法证明双轨事件。
                        break  # 修改代码+AutoRealModelGateTest：满足条件后停止等待；如果没有这一行，测试会浪费时间。
                    time.sleep(0.03)  # 修改代码+AutoRealModelGateTest：短暂等待后台线程；如果没有这一行，循环会空转占 CPU。
                self._wait_for_manager_turn_idle(manager, turn_id)  # 修改代码+AutoRealModelGateTest：等待 worker finally 释放 active turn；如果没有这一行，测试目录 cleanup 可能撞上 status.lock。
        self.assertIn("message_delta", event_types)  # 修改代码+AutoRealModelGateTest：确认显式 fake 模式发出 fake streaming delta；如果没有这一行，smoke 路径可能被真实门禁误删。
        self.assertIn("gui_turn_completed", event_types)  # 新增代码+GuiAgentAdapterContractTest：确认仍保留 V1 完成事件；如果没有这一行，旧 GUI 生命周期测试会被破坏。
    # 修改代码+AutoRealModelGateTest：测试函数结束，test_gui_run_manager_uses_fake_adapter_when_fake_mode_is_enabled 到此结束；如果没有这个边界说明，用户不容易看出显式 fake smoke 的合同范围。

    def test_gui_run_manager_auto_fails_fast_when_openai_is_not_connected(self) -> None:  # 新增代码+AutoRealModelGateTest：测试函数开始，验证默认 auto 未连接时快速失败；如果没有这段，真实 GUI 会继续显示 fake streaming 假成功。
        from learning_agent.app import gui_bridge  # 新增代码+AutoRealModelGateTest：导入 bridge 模块便于替换 provider payload；如果没有这一行，测试会依赖真实本机连接状态。

        disconnected_payload = {"providers": [{"id": "openai", "connected": False, "source": "none"}]}  # 新增代码+AutoRealModelGateTest：模拟 OpenAI 未连接；如果没有这一行，测试不能复现底部模型为空的真实窗口状态。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+AutoRealModelGateTest：创建隔离 workspace；如果没有这一行，测试会污染真实 GUI memory。
            with mock.patch.dict(os.environ, {"OPENHARNESS_OPENAI_AUTH_MODE": "codex_cli"}, clear=False):  # 新增代码+AutoRealModelGateTest：保持 OpenAI provider 语义；如果没有这一行，连接来源判断可能走 mock 分支。
                os.environ.pop("OPENHARNESS_GUI_MODEL_MODE", None)  # 新增代码+AutoRealModelGateTest：保持默认 auto 模式；如果没有这一行，外部 fake/real 环境会污染测试。
                with mock.patch.object(gui_bridge, "build_provider_settings_payload", return_value=disconnected_payload):  # 新增代码+AutoRealModelGateTest：替换 provider 状态事实源；如果没有这一行，测试会读取用户真实登录状态。
                    manager = gui_bridge.GuiRunManager(Path(directory))  # 新增代码+AutoRealModelGateTest：创建 auto 模式 manager；如果没有这一行，无法验证默认桌面行为。
                    response = manager.start_message("default", "你好，未连接时不要 fake", provider_id="openai", model_id="gpt-5.5", reasoning_effort="ultra", permission_mode="full-access")  # 新增代码+AutoRealModelGateTest：提交带 OpenAI 模型上下文的 prompt；如果没有这一行，真实 adapter 门禁不会被触发。
                    turn_id = str(response["turn_id"])  # 新增代码+AutoRealModelGateTest：保存 turn id；如果没有这一行，无法读取本轮事件。
                    status, answer = self._wait_for_manager_turn_idle(manager, turn_id)  # 新增代码+AutoRealModelGateTest：等待后台 worker 快速失败并释放 active turn；如果没有这一行，断言可能抢在事件写入前执行。
                    event_types = [event.event_type for event in manager.event_store.list_events(limit=50) if event.turn_id == turn_id]  # 新增代码+AutoRealModelGateTest：读取本轮事件类型；如果没有这一行，无法确认没有启动真实模型调用。
        self.assertEqual("failed", status)  # 新增代码+AutoRealModelGateTest：确认未连接时失败；如果没有这一行，fake 成功会漏掉。
        self.assertIn("请先连接 OpenAI", answer)  # 新增代码+AutoRealModelGateTest：确认用户看到明确连接提示；如果没有这一行，错误会继续模糊或显示 fake。
        self.assertNotIn("fake streaming", answer)  # 新增代码+AutoRealModelGateTest：确认没有模拟回复文案；如果没有这一行，真实 GUI 假成功会再次回归。
        self.assertIn("turn_failed", event_types)  # 新增代码+AutoRealModelGateTest：确认事件流进入失败终态；如果没有这一行，前端无法可靠同步错误。
        self.assertNotIn("model_call_started", event_types)  # 新增代码+AutoRealModelGateTest：确认未连接时没有启动模型调用；如果没有这一行，慢请求或 codex.exe 仍可能被拉起。
    # 新增代码+AutoRealModelGateTest：测试函数结束，test_gui_run_manager_auto_fails_fast_when_openai_is_not_connected 到此结束；如果没有边界说明，用户不容易看出它锁住的是真实 GUI 未连接行为。

    def test_gui_run_manager_uses_real_adapter_when_real_model_mode_is_enabled(self) -> None:  # 新增代码+真实模型GUI桥接测试：测试函数开始，验证 real 模式会接到真实模型 adapter；如果没有这段，环境变量可能打开后仍走 fake streaming。
        from learning_agent.app import gui_bridge  # 新增代码+真实模型GUI桥接测试：导入 bridge 模块本体便于 patch 构造器；如果没有这一行，测试无法替换真实 adapter。
        from learning_agent.app.gui_agent_adapter import GuiAgentRunResult  # 新增代码+真实模型GUI桥接测试：导入 adapter 结果对象；如果没有这一行，假 adapter 无法按正式合同返回。

        adapter_calls: list[dict[str, object]] = []  # 新增代码+真实模型GUI桥接测试：记录假真实 adapter 的调用；如果没有这一行，测试无法确认 run manager 真的选中了 real adapter。

        class ConnectedStatus:  # 新增代码+真实模型GUI桥接测试：类段开始，模拟 CodexAuthStatus；如果没有这个类，测试要依赖真实 Codex CLI 登录状态。
            available = True  # 新增代码+真实模型GUI桥接测试：声明 Codex CLI 可用；如果没有这一行，provider 会被判定为缺失。
            connected = True  # 新增代码+真实模型GUI桥接测试：声明 OpenAI/Codex 已登录；如果没有这一行，real adapter 连接门禁会失败。
            message = "codex login status ok"  # 新增代码+真实模型GUI桥接测试：提供可读状态消息；如果没有这一行，provider payload 缺少诊断文本。
        # 新增代码+真实模型GUI桥接测试：类段结束，ConnectedStatus 到此结束；如果没有这个边界说明，用户不容易看出登录替身范围。

        class RecordingRealAdapter:  # 新增代码+真实模型GUI桥接测试：类段开始，替代真实模型 adapter；如果没有这个类，测试会实际调用 Codex CLI。
            def __init__(self, connected_provider_reader, model_failure_recorder=None):  # 修改代码+AutoRealModelGateTest：函数段开始，兼容真实 adapter 的失败记录器参数；如果没有这段，测试替身会因为构造签名落后而失败。
                self.connected_provider_reader = connected_provider_reader  # 新增代码+真实模型GUI桥接测试：保存连接读取器；如果没有这一行，run 时无法检查门禁。
                self.model_failure_recorder = model_failure_recorder  # 新增代码+AutoRealModelGateTest：保存但不触发失败记录器替身；如果没有这一行，构造合同不完整，后续排查不清楚参数是否传入。
            # 新增代码+真实模型GUI桥接测试：函数段结束，RecordingRealAdapter.__init__ 到此结束；如果没有这个边界说明，用户不容易看出依赖注入范围。

            def run(self, request, emit_event, _is_cancelled):  # 新增代码+真实模型GUI桥接测试：函数段开始，模拟真实 adapter 完成一次 GUI turn；如果没有这段，run manager 没有可执行对象。
                adapter_calls.append({"mode": request.mode, "connected": self.connected_provider_reader()})  # 新增代码+真实模型GUI桥接测试：记录请求模式和 provider 连接状态；如果没有这一行，测试无法证明 real 选择和门禁来源。
                emit_event({"kind": "message_delta", "payload": {"text_delta": "real bridge answer"}})  # 新增代码+真实模型GUI桥接测试：发出真实路径 delta；如果没有这一行，GUI 事件流无法证明 adapter 被调用。
                emit_event({"kind": "message_completed", "payload": {"final_text": "real bridge answer"}})  # 新增代码+真实模型GUI桥接测试：发出完成事件；如果没有这一行，前端状态机不会看到完成载荷。
                return GuiAgentRunResult(status="completed", final_text="real bridge answer")  # 新增代码+真实模型GUI桥接测试：返回完成结果；如果没有这一行，run manager 不会写入助手最终答案。
            # 新增代码+真实模型GUI桥接测试：函数段结束，RecordingRealAdapter.run 到此结束；如果没有这个边界说明，用户不容易看出假真实 adapter 行为。
        # 新增代码+真实模型GUI桥接测试：类段结束，RecordingRealAdapter 到此结束；如果没有这个边界说明，用户不容易看出 adapter 替身范围。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+真实模型GUI桥接测试：创建隔离 workspace；如果没有这一行，测试会污染真实 GUI memory。
            with mock.patch.dict(os.environ, {"OPENHARNESS_GUI_MODEL_MODE": "real", "OPENHARNESS_OPENAI_AUTH_MODE": "codex_cli"}):  # 新增代码+真实模型GUI桥接测试：打开真实模型和官方 Codex 登录模式；如果没有这一行，run manager 会继续默认 fake。
                with mock.patch.object(gui_bridge, "RealModelGuiAgentAdapter", RecordingRealAdapter):  # 新增代码+真实模型GUI桥接测试：用记录型 adapter 替代真实 adapter；如果没有这一行，测试会调用真实模型。
                    with mock.patch("learning_agent.app.gui_provider_settings.CodexAuthBridge") as bridge_cls:  # 新增代码+真实模型GUI桥接测试：替换 Codex 登录检查；如果没有这一行，测试依赖用户机器真实登录。
                        bridge_cls.return_value.login_status.return_value = ConnectedStatus()  # 新增代码+真实模型GUI桥接测试：让 provider catalog 判断已连接；如果没有这一行，连接门禁会返回 false。
                        manager = gui_bridge.GuiRunManager(Path(directory))  # 新增代码+真实模型GUI桥接测试：创建真实模式 run manager；如果没有这一行，测试没有桥接对象。
                        response = manager.start_message("default", "你好，走真实模型路径")  # 新增代码+真实模型GUI桥接测试：提交普通用户 prompt；如果没有这一行，adapter 不会运行。
                        turn_id = str(response["turn_id"])  # 新增代码+真实模型GUI桥接测试：保存 turn id；如果没有这一行，后续无法定位状态。
                        status, answer = self._wait_for_manager_turn_idle(manager, turn_id)  # 新增代码+GuiAsyncLifecycleTest：等待真实 adapter 替身完成并释放 active turn；如果没有这一行，批量测试 cleanup 可能撞上 status.lock。
        self.assertEqual("completed", status)  # 新增代码+真实模型GUI桥接测试：确认真实模式轮次完成；如果没有这一行，run manager 失败可能被忽略。
        self.assertEqual("real bridge answer", answer)  # 新增代码+真实模型GUI桥接测试：确认答案来自真实 adapter 替身；如果没有这一行，fake 文案可能误过。
        self.assertEqual([{"mode": "real", "connected": True}], adapter_calls)  # 新增代码+真实模型GUI桥接测试：确认请求 mode 为 real 且连接门禁来自 provider；如果没有这一行，桥接选择和授权门禁都没有被锁住。
    # 新增代码+真实模型GUI桥接测试：测试函数结束，test_gui_run_manager_uses_real_adapter_when_real_model_mode_is_enabled 到此结束；如果没有这个边界说明，用户不容易看出 real bridge 合同范围。

    def test_gui_run_manager_auto_uses_real_adapter_when_codex_cli_provider_is_connected(self) -> None:  # 新增代码+真实模型GUI桥接测试：测试函数开始，验证已连接 provider 时默认自动走真实 adapter；如果没有这段，用户登录成功后主聊天仍可能 fake。
        from learning_agent.app import gui_bridge  # 新增代码+真实模型GUI桥接测试：导入 bridge 模块便于 patch adapter；如果没有这一行，测试无法替换真实模型调用。
        from learning_agent.app.gui_agent_adapter import GuiAgentRunResult  # 新增代码+真实模型GUI桥接测试：导入结果对象；如果没有这一行，假 adapter 不能按合同返回。

        adapter_modes: list[str] = []  # 新增代码+真实模型GUI桥接测试：记录实际请求模式；如果没有这一行，测试不能证明 auto 模式选中了 real。

        class ConnectedStatus:  # 新增代码+真实模型GUI桥接测试：类段开始，模拟已登录 Codex 状态；如果没有这个类，测试会依赖用户本机真实登录。
            available = True  # 新增代码+真实模型GUI桥接测试：声明 Codex CLI 可用；如果没有这一行，provider source 会变成 missing。
            connected = True  # 新增代码+真实模型GUI桥接测试：声明 Codex 已连接；如果没有这一行，auto 模式不会放行真实 adapter。
            message = "codex login status ok"  # 新增代码+真实模型GUI桥接测试：提供状态文本；如果没有这一行，provider payload 缺少诊断消息。
        # 新增代码+真实模型GUI桥接测试：类段结束，ConnectedStatus 到此结束；如果没有这个边界说明，用户不容易看出登录替身范围。

        class RecordingRealAdapter:  # 新增代码+真实模型GUI桥接测试：类段开始，替代真实模型 adapter；如果没有这个类，测试会实际调用 Codex CLI。
            def __init__(self, connected_provider_reader, model_failure_recorder=None):  # 修改代码+AutoRealModelGateTest：函数段开始，兼容真实 adapter 的失败记录器参数；如果没有这段，auto/real 路由测试会卡在构造阶段。
                self.connected_provider_reader = connected_provider_reader  # 新增代码+真实模型GUI桥接测试：保存连接读取器；如果没有这一行，run 中无法证明门禁可用。
                self.model_failure_recorder = model_failure_recorder  # 新增代码+AutoRealModelGateTest：保存但不触发失败记录器；如果没有这一行，测试替身无法体现真实构造合同。
            # 新增代码+真实模型GUI桥接测试：函数段结束，RecordingRealAdapter.__init__ 到此结束；如果没有这个边界说明，用户不容易看出依赖注入范围。

            def run(self, request, emit_event, _is_cancelled):  # 新增代码+真实模型GUI桥接测试：函数段开始，模拟真实 adapter 完成；如果没有这段，manager 没有可执行对象。
                adapter_modes.append(request.mode)  # 新增代码+真实模型GUI桥接测试：记录请求 mode；如果没有这一行，auto 模式是否 real 不可见。
                self.connected_provider_reader()  # 新增代码+真实模型GUI桥接测试：执行连接读取器以覆盖 provider 门禁；如果没有这一行，测试不能证明门禁函数无异常。
                emit_event({"kind": "message_delta", "payload": {"text_delta": "auto real answer"}})  # 新增代码+真实模型GUI桥接测试：发出 delta；如果没有这一行，事件流无法显示真实路径。
                emit_event({"kind": "message_completed", "payload": {"final_text": "auto real answer"}})  # 新增代码+真实模型GUI桥接测试：发出完成事件；如果没有这一行，完成载荷不可见。
                return GuiAgentRunResult(status="completed", final_text="auto real answer")  # 新增代码+真实模型GUI桥接测试：返回完成结果；如果没有这一行，manager 无法写入答案。
            # 新增代码+真实模型GUI桥接测试：函数段结束，RecordingRealAdapter.run 到此结束；如果没有这个边界说明，用户不容易看出替身行为。
        # 新增代码+真实模型GUI桥接测试：类段结束，RecordingRealAdapter 到此结束；如果没有这个边界说明，用户不容易看出 adapter 替身范围。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+真实模型GUI桥接测试：创建隔离 workspace；如果没有这一行，测试会污染真实 GUI 状态。
            with mock.patch.dict(os.environ, {"OPENHARNESS_OPENAI_AUTH_MODE": "codex_cli"}, clear=False):  # 新增代码+真实模型GUI桥接测试：启用官方 Codex provider 模式；如果没有这一行，provider 不会返回 codex_cli source。
                os.environ.pop("OPENHARNESS_GUI_MODEL_MODE", None)  # 新增代码+真实模型GUI桥接测试：确保模型模式未显式设置；如果没有这一行，外部环境可能影响 auto 行为。
                with mock.patch.object(gui_bridge, "RealModelGuiAgentAdapter", RecordingRealAdapter):  # 新增代码+真实模型GUI桥接测试：替换真实 adapter；如果没有这一行，测试会调用真实模型。
                    with mock.patch("learning_agent.app.gui_provider_settings.CodexAuthBridge") as bridge_cls:  # 新增代码+真实模型GUI桥接测试：替换登录状态检查；如果没有这一行，测试依赖真实 Codex 登录。
                        bridge_cls.return_value.login_status.return_value = ConnectedStatus()  # 新增代码+真实模型GUI桥接测试：让 provider 显示已连接；如果没有这一行，auto 模式会保持 fake。
                        manager = gui_bridge.GuiRunManager(Path(directory))  # 新增代码+真实模型GUI桥接测试：创建 auto 模式 manager；如果没有这一行，测试没有桥接对象。
                        response = manager.start_message("default", "你好，自动真实路径")  # 新增代码+真实模型GUI桥接测试：提交 prompt；如果没有这一行，adapter 不会运行。
                        turn_id = str(response["turn_id"])  # 新增代码+真实模型GUI桥接测试：保存 turn id；如果没有这一行，无法读取结果。
                        status, _answer = self._wait_for_manager_turn_idle(manager, turn_id)  # 新增代码+GuiAsyncLifecycleTest：等待 auto 真实路径后台线程完全空闲；如果没有这一行，临时目录清理可能早于锁释放。
        self.assertEqual("completed", status)  # 新增代码+真实模型GUI桥接测试：确认 auto 模式完成；如果没有这一行，失败会被忽略。
        self.assertEqual(["real"], adapter_modes)  # 新增代码+真实模型GUI桥接测试：确认未显式设置模式但 provider 已连接时请求为 real；如果没有这一行，登录成功后仍 fake 的问题会漏掉。
    # 新增代码+真实模型GUI桥接测试：测试函数结束，test_gui_run_manager_auto_uses_real_adapter_when_codex_cli_provider_is_connected 到此结束；如果没有这个边界说明，用户不容易看出 auto real 合同范围。

    def test_gui_run_manager_auto_switches_to_real_after_provider_connects_later(self) -> None:  # 新增代码+ComposerRealModelRoutingTest：测试函数开始，验证桌面壳先启动后再 OAuth 连接也能切到真实模型；如果没有这段，用户完成 OAuth 后下一轮仍会 fake streaming。
        from learning_agent.app import gui_bridge  # 新增代码+ComposerRealModelRoutingTest：导入 bridge 模块便于替换 provider payload 和真实 adapter；如果没有这一行，测试会依赖真实桌面环境。
        from learning_agent.app.gui_agent_adapter import GuiAgentRunResult  # 新增代码+ComposerRealModelRoutingTest：导入正式结果对象；如果没有这一行，假 adapter 无法按合同返回。

        adapter_calls: list[dict[str, object]] = []  # 新增代码+ComposerRealModelRoutingTest：记录真实 adapter 调用；如果没有这一行，无法证明启动后连接触发了动态切换。
        disconnected_payload = {"providers": [{"id": "openai", "connected": False, "source": "none"}]}  # 新增代码+ComposerRealModelRoutingTest：模拟窗口刚启动时 OpenAI 未连接；如果没有这一行，测试不能复现用户先开壳再登录的路径。
        connected_payload = {"providers": [{"id": "openai", "connected": True, "source": "direct_oauth_experimental"}]}  # 新增代码+ComposerRealModelRoutingTest：模拟设置页完成 ChatGPT OAuth 后的 provider 状态；如果没有这一行，动态切换没有事实输入。

        class RecordingRealAdapter:  # 新增代码+ComposerRealModelRoutingTest：类段开始，替代真实模型 adapter；如果没有这个类，测试会真实访问 ChatGPT OAuth 后端。
            def __init__(self, connected_provider_reader, model_failure_recorder=None):  # 修改代码+AutoRealModelGateTest：函数段开始，兼容真实 adapter 的失败记录器参数；如果没有这段，动态连接测试会因为替身签名落后而失败。
                self.connected_provider_reader = connected_provider_reader  # 新增代码+ComposerRealModelRoutingTest：保存连接读取器；如果没有这一行，run 时无法确认连接门禁能看到 OpenAI。
                self.model_failure_recorder = model_failure_recorder  # 新增代码+AutoRealModelGateTest：保存失败记录器占位；如果没有这一行，构造合同不完整，后续排查不清楚参数是否传入。
            # 新增代码+ComposerRealModelRoutingTest：函数段结束，RecordingRealAdapter.__init__ 到此结束；如果没有边界说明，用户不容易看出构造范围。

            def run(self, request, emit_event, _is_cancelled):  # 新增代码+ComposerRealModelRoutingTest：函数段开始，模拟真实 adapter 完成回答；如果没有这段，manager 没有可执行真实路径。
                connected = self.connected_provider_reader("openai")  # 新增代码+ComposerRealModelRoutingTest：按 provider id 查询连接状态；如果没有这一行，测试不能锁住多 provider 后续路由边界。
                adapter_calls.append({"mode": request.mode, "provider_id": request.provider_id, "model_id": request.model_id, "connected": connected})  # 新增代码+ComposerRealModelRoutingTest：记录请求上下文；如果没有这一行，无法证明模型选择进入真实 adapter。
                emit_event({"kind": "message_delta", "payload": {"text_delta": "dynamic real answer"}})  # 新增代码+ComposerRealModelRoutingTest：发出真实路径 delta；如果没有这一行，GUI 事件流不会推进。
                emit_event({"kind": "message_completed", "payload": {"final_text": "dynamic real answer"}})  # 新增代码+ComposerRealModelRoutingTest：发出完成事件；如果没有这一行，turn 不会完成。
                return GuiAgentRunResult(status="completed", final_text="dynamic real answer")  # 新增代码+ComposerRealModelRoutingTest：返回完成结果；如果没有这一行，run manager 无法写入最终答案。
            # 新增代码+ComposerRealModelRoutingTest：函数段结束，RecordingRealAdapter.run 到此结束；如果没有边界说明，用户不容易看出替身行为。
        # 新增代码+ComposerRealModelRoutingTest：类段结束，RecordingRealAdapter 到此结束；如果没有边界说明，用户不容易看出 adapter 替身范围。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+ComposerRealModelRoutingTest：创建隔离 workspace；如果没有这一行，测试会污染真实 GUI memory。
            payloads = [connected_payload, connected_payload, connected_payload]  # 修改代码+AutoRealModelGateTest：auto 初始化不再预读 provider，只在消息执行时读取当前已连接状态；如果没有这一行，测试会把旧实现的预读行为误当合同。
            with mock.patch.dict(os.environ, {"OPENHARNESS_OPENAI_AUTH_MODE": "direct_oauth"}, clear=False):  # 新增代码+ComposerRealModelRoutingTest：启用 direct OAuth provider 语义；如果没有这一行，连接来源可能不被承认为真实模型来源。
                os.environ.pop("OPENHARNESS_GUI_MODEL_MODE", None)  # 新增代码+ComposerRealModelRoutingTest：保持默认 auto 模式；如果没有这一行，外部 real/fake 环境会污染测试。
                with mock.patch.object(gui_bridge, "build_provider_settings_payload", side_effect=payloads):  # 新增代码+ComposerRealModelRoutingTest：替换 provider 状态事实源；如果没有这一行，测试需要真实 OAuth。
                    with mock.patch.object(gui_bridge, "RealModelGuiAgentAdapter", RecordingRealAdapter):  # 新增代码+ComposerRealModelRoutingTest：替换真实模型 adapter；如果没有这一行，测试会访问真实模型。
                        manager = gui_bridge.GuiRunManager(Path(directory))  # 新增代码+ComposerRealModelRoutingTest：启动时读取未连接状态；如果没有这一行，无法复现启动后再登录。
                        self.assertEqual("auto", manager.agent_adapter_mode)  # 新增代码+ComposerRealModelRoutingTest：确认 auto 没被固化为 fake；如果没有这一行，启动后连接仍无法动态切换。
                        response = manager.start_message("default", "你好，使用刚连接的 OAuth 模型", provider_id="openai", model_id="gpt-5.5", reasoning_effort="ultra", permission_mode="full-access")  # 新增代码+ComposerRealModelRoutingTest：提交带模型选择的用户 prompt；如果没有这一行，动态切换没有触发点。
                        turn_id = str(response["turn_id"])  # 新增代码+ComposerRealModelRoutingTest：保存 turn id；如果没有这一行，后续无法等待状态。
                        status, _answer = self._wait_for_manager_turn_idle(manager, turn_id)  # 新增代码+GuiAsyncLifecycleTest：等待动态真实路由完成并释放 active turn；如果没有这一行，Windows 批量测试可能在 status.lock 释放前删除目录。
        self.assertEqual("completed", status)  # 新增代码+ComposerRealModelRoutingTest：确认动态切换后轮次完成；如果没有这一行，仍 fake 或失败的问题会漏掉。
        self.assertEqual([{"mode": "real", "provider_id": "openai", "model_id": "gpt-5.5", "connected": True}], adapter_calls)  # 新增代码+ComposerRealModelRoutingTest：确认启动后连接也会按所选 OpenAI/GPT-5.5 走真实 adapter；如果没有这一行，OAuth 后找不到真实模型路由会回归。
    # 新增代码+ComposerRealModelRoutingTest：测试函数结束，test_gui_run_manager_auto_switches_to_real_after_provider_connects_later 到此结束；如果没有边界说明，用户不容易看出覆盖的是用户真实 OAuth 后续消息路径。

    def test_gui_model_mode_accepts_explicit_auto_string(self) -> None:  # 新增代码+ComposerRealModelRoutingTest：测试函数开始，验证显式 auto 启动配置不会被误判 fake；如果没有这段，用户按文档设置 auto 时真实 OAuth 仍会 fake streaming。
        from learning_agent.app.gui_bridge import _gui_model_mode  # 新增代码+ComposerRealModelRoutingTest：导入模式解析 helper；如果没有这一行，测试无法锁住启动配置根因。

        with mock.patch.dict(os.environ, {"OPENHARNESS_GUI_MODEL_MODE": "auto"}, clear=False):  # 新增代码+ComposerRealModelRoutingTest：模拟真实启动脚本显式传入 auto；如果没有这一行，测试不能复现本轮 GUI 验收失败。
            selected_mode = _gui_model_mode()  # 新增代码+ComposerRealModelRoutingTest：读取解析后的模式；如果没有这一行，后续没有被测值。
        self.assertEqual("auto", selected_mode)  # 新增代码+ComposerRealModelRoutingTest：确认 auto 保持 auto 而不是 fake；如果没有这一行，配置回归不会被发现。
    # 新增代码+ComposerRealModelRoutingTest：测试函数结束，test_gui_model_mode_accepts_explicit_auto_string 到此结束；如果没有边界说明，用户不容易看出覆盖的是启动模式解析。
# 新增代码+GuiAgentAdapterContractTest：测试类段结束，GuiAgentAdapterContractTest 到此结束；如果没有这个边界说明，用户不容易看出本文件只测 adapter 边界。


if __name__ == "__main__":  # 新增代码+GuiAgentAdapterContractTest：允许直接运行本测试文件；如果没有这一行，手动排查时不会启动 unittest。
    unittest.main()  # 新增代码+GuiAgentAdapterContractTest：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行测试。
