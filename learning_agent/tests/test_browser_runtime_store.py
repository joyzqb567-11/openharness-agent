"""浏览器运行时持久化 store 测试。"""  # 新增代码+BrowserRuntimeStore: 说明本文件锁定 browser run/action/observation/event 的落盘行为；若没有这行代码，持久化能力缺口不清楚。

from __future__ import annotations  # 新增代码+BrowserRuntimeStore: 延迟解析类型注解；若没有这行代码，测试里的前向类型更容易受解释顺序影响。

from learning_agent.tests.support import *  # 新增代码+BrowserRuntimeStore: 复用 tempfile、Path 和 unittest 基类；若没有这行代码，测试会重复公共准备逻辑。


class BrowserRuntimeStoreTests(LearningAgentTestBase):  # 新增代码+BrowserRuntimeStore: 定义浏览器 runtime store 测试集合；若没有这个类，unittest 不会发现本组持久化测试。
    def test_store_persists_run_actions_observations_and_events(self) -> None:  # 新增代码+BrowserRuntimeStore: 验证 run/action/observation/event 都能落盘；若没有这行代码，浏览器任务仍可能只存在内存里。
        from learning_agent.browser.runtime_models import BrowserAction, BrowserObservation  # 新增代码+BrowserRuntimeStore: 导入协议层模型作为 store 输入；若没有这行代码，测试无法使用真实数据对象。
        from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+BrowserRuntimeStore: 导入计划新增的持久化 store；若没有这行代码，测试无法锁定公开 API。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRuntimeStore: 使用临时目录隔离落盘文件；若没有这行代码，测试会污染真实 memory 目录。
            store = BrowserRuntimeStore(Path(raw_dir))  # 新增代码+BrowserRuntimeStore: 创建隔离 browser runtime store；若没有这行代码，后续无法写入 run/event。
            browser_run = store.create_run(run_id="browser-run-1", session_id="session-1", prompt="打开页面并读取内容", metadata={"harness_run_id": "harness-1"})  # 新增代码+BrowserRuntimeStore: 创建可恢复浏览器 run；若没有这行代码，动作和观察没有根对象。
            action = BrowserAction.create(run_id=browser_run.run_id, stage_id="open-page", tool_name="browser_open", arguments={"url": "https://example.com/"}, action_id="action-1")  # 新增代码+BrowserRuntimeStore: 创建一个浏览器打开页面动作；若没有这行代码，store 无法验证 action 文件。
            action.mark_started()  # 新增代码+BrowserRuntimeStore: 标记动作开始；若没有这行代码，started 事件没有状态证据。
            store.save_action(action, event_type="browser_action_started")  # 新增代码+BrowserRuntimeStore: 保存 started 动作事件；若没有这行代码，harness event log 看不到工具开始。
            action.mark_completed(observation_id="obs-1")  # 新增代码+BrowserRuntimeStore: 标记动作完成并挂观察 id；若没有这行代码，completed 事件缺少页面证据关联。
            store.save_action(action, event_type="browser_action_completed")  # 新增代码+BrowserRuntimeStore: 保存 completed 动作事件；若没有这行代码，事件流无法确认工具收尾。
            observation = BrowserObservation(observation_id="obs-1", run_id=browser_run.run_id, stage_id="open-page", action_id=action.action_id, url="https://example.com/", title="Example Domain", visible_text="Example Domain", screenshot_path="artifacts/example.png")  # 新增代码+BrowserRuntimeStore: 创建页面观察证据；若没有这行代码，store 无法验证 observation 文件。
            store.save_observation(observation)  # 新增代码+BrowserRuntimeStore: 保存页面观察和事件；若没有这行代码，真实浏览器任务无法复验页面内容。
            loaded_run = store.load_run("browser-run-1")  # 新增代码+BrowserRuntimeStore: 从磁盘重新读取 run；若没有这行代码，无法证明进程重启可恢复。
            loaded_action = store.load_action("action-1")  # 新增代码+BrowserRuntimeStore: 从磁盘重新读取 action；若没有这行代码，无法证明工具动作可回放。
            loaded_observation = store.load_observation("obs-1")  # 新增代码+BrowserRuntimeStore: 从磁盘重新读取 observation；若没有这行代码，无法证明页面证据可复验。
            events = store.tail_events("browser-run-1", limit=10)  # 新增代码+BrowserRuntimeStore: 读取最近事件；若没有这行代码，无法证明 event log 可审计。
        self.assertEqual(loaded_run.action_ids, ["action-1"])  # 新增代码+BrowserRuntimeStore: 断言 run 自动关联动作；若没有这行代码，run/action 文件会断链。
        self.assertEqual(loaded_run.observation_ids, ["obs-1"])  # 新增代码+BrowserRuntimeStore: 断言 run 自动关联观察；若没有这行代码，run/observation 文件会断链。
        self.assertEqual(loaded_action.status, "completed")  # 新增代码+BrowserRuntimeStore: 断言动作完成状态可恢复；若没有这行代码，resume 可能重跑已完成动作。
        self.assertEqual(loaded_observation.title, "Example Domain")  # 新增代码+BrowserRuntimeStore: 断言页面证据可恢复；若没有这行代码，验收缺少事实来源。
        self.assertEqual([event["event_type"] for event in events], ["browser_run_created", "browser_action_started", "browser_action_completed", "browser_observation_recorded"])  # 新增代码+BrowserRuntimeStore: 断言事件顺序完整；若没有这行代码，harness event log 缺失不会被发现。

    def test_store_restores_completed_stages_after_restart(self) -> None:  # 新增代码+BrowserRuntimeStore: 验证中断后能知道已完成阶段；若没有这行代码，resume 可能从头重跑。
        from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+BrowserRuntimeStore: 导入持久化 store；若没有这行代码，测试无法模拟重启。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRuntimeStore: 使用临时目录模拟同一个持久化位置；若没有这行代码，测试会污染真实 memory。
            first_store = BrowserRuntimeStore(Path(raw_dir))  # 新增代码+BrowserRuntimeStore: 创建第一次进程中的 store；若没有这行代码，无法写入初始 run。
            browser_run = first_store.create_run(run_id="browser-run-2", session_id="session-2", prompt="分阶段浏览器任务")  # 新增代码+BrowserRuntimeStore: 创建分阶段 run；若没有这行代码，阶段恢复没有对象。
            browser_run.mark_running(stage_id="open-page")  # 新增代码+BrowserRuntimeStore: 标记当前阶段；若没有这行代码，恢复不知道中断位置。
            browser_run.mark_stage_completed("open-page")  # 新增代码+BrowserRuntimeStore: 标记阶段完成；若没有这行代码，重启后没有跳过依据。
            first_store.save_run(browser_run, event_type="browser_stage_completed")  # 新增代码+BrowserRuntimeStore: 保存阶段完成状态和事件；若没有这行代码，完成阶段不会落盘。
            second_store = BrowserRuntimeStore(Path(raw_dir))  # 新增代码+BrowserRuntimeStore: 模拟进程重启后的新 store；若没有这行代码，测试无法证明磁盘恢复。
            restored = second_store.load_run("browser-run-2")  # 新增代码+BrowserRuntimeStore: 从同一目录读取旧 run；若没有这行代码，恢复行为没有断言对象。
            events = second_store.tail_events("browser-run-2", limit=5)  # 新增代码+BrowserRuntimeStore: 读取重启后的事件日志；若没有这行代码，阶段完成事件无法验证。
        self.assertEqual(restored.current_stage_id, "open-page")  # 新增代码+BrowserRuntimeStore: 断言当前阶段可恢复；若没有这行代码，中断恢复位置可能丢失。
        self.assertEqual(restored.completed_stage_ids, ["open-page"])  # 新增代码+BrowserRuntimeStore: 断言已完成阶段可恢复；若没有这行代码，resume 可能重复执行。
        self.assertIn("browser_stage_completed", [event["event_type"] for event in events])  # 新增代码+BrowserRuntimeStore: 断言阶段完成事件落盘；若没有这行代码，harness 状态生态看不到阶段变化。

    def test_browser_automation_server_call_writes_runtime_run_and_events(self) -> None:  # 新增代码+BrowserRuntimeStore: 验证真实浏览器 MCP server 的公开 call 会写 browser runtime store；若没有这行代码，store 可能继续只是旁路系统。
        from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+BrowserRuntimeStore: 导入 store 用来读取 server 写出的文件；若没有这行代码，测试只能检查文件名不能检查内容。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserRuntimeStore: 导入真实浏览器 server；若没有这行代码，测试无法覆盖生产工具执行入口。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRuntimeStore: 使用临时 workspace 隔离 server 产物；若没有这行代码，测试会污染真实项目 memory。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserRuntimeStore: 创建真实 server 实例；若没有这行代码，无法通过公开 call 入口验证接入。
            def fake_wait(arguments: dict[str, object]) -> str:  # 新增代码+BrowserRuntimeStore: 用假 wait 避免测试真实 sleep 和页面依赖；若没有这行代码，单元测试会变慢且不稳定。
                self.assertEqual(arguments["milliseconds"], 1)  # 新增代码+BrowserRuntimeStore: 断言公开 call 把参数传给真实 handler；若没有这行代码，测试无法证明执行器没有绕过 handler。
                return "browser_wait 成功\npage_id=page-1"  # 新增代码+BrowserRuntimeStore: 返回成功文本让执行器进入 completed 分支；若没有这行代码，事件无法覆盖成功收尾。
            server.browser_wait = fake_wait  # 新增代码+BrowserRuntimeStore: 替换实例方法；若没有这行代码，测试会调用真实等待实现。
            result = server.call("browser_wait", {"milliseconds": 1})  # 新增代码+BrowserRuntimeStore: 通过公开工具入口执行动作；若没有这行代码，store 接入不会被触发。
            runtime_root = Path(raw_dir) / "learning_agent" / "memory" / "browser_runtime"  # 新增代码+BrowserRuntimeStore: 定位 server 应写入的 browser runtime 根目录；若没有这行代码，测试不知道在哪里找 durable run。
            stored_run_ids = sorted(path.stem for path in (runtime_root / "runs").glob("*.json"))  # 新增代码+BrowserRuntimeStore: 读取已创建的 browser run 文件名；若没有这行代码，无法断言自动创建 run。
            store = BrowserRuntimeStore(runtime_root)  # 新增代码+BrowserRuntimeStore: 用同一路径创建读取端 store；若没有这行代码，事件和 run 无法结构化读取。
            restored_run = store.load_run(stored_run_ids[0])  # 新增代码+BrowserRuntimeStore: 从磁盘恢复 server 写出的 run；若没有这行代码，无法证明文件内容有效。
            events = store.tail_events(restored_run.run_id, limit=10)  # 新增代码+BrowserRuntimeStore: 读取 server 写出的事件流；若没有这行代码，无法验证 started/completed 事件。
        self.assertIn("browser_wait 成功", result)  # 新增代码+BrowserRuntimeStore: 断言工具结果仍正常返回；若没有这行代码，store 接入可能破坏工具输出。
        self.assertEqual(len(stored_run_ids), 1)  # 新增代码+BrowserRuntimeStore: 断言一次 server call 自动创建一个 durable browser run；若没有这行代码，真实浏览器任务可能没有 run 根。
        self.assertEqual(restored_run.status, "completed")  # 新增代码+BrowserRuntimeStore: 断言动作成功后 run 也完成；若没有这行代码，状态 CLI 会误判运行中。
        self.assertEqual(restored_run.action_ids, [f"{restored_run.run_id}-action-1"])  # 新增代码+BrowserRuntimeStore: 断言 run 挂载了动作 id；若没有这行代码，run/action 会断链。
        self.assertEqual([event["event_type"] for event in events], ["browser_run_created", "browser_provider_decision", "browser_action_started", "browser_action_progress", "browser_action_completed"])  # 修改代码+BrowserProviderAdapters: 断言真实执行入口先写 provider 决策再写动作生命周期；若没有这行代码，Stage 2 provider 决策事件丢失不会被发现。

    def test_agent_mcp_browser_tool_mirrors_latest_browser_run_to_status_events(self) -> None:  # 新增代码+BrowserRuntimeStatus: 验证 agent 主循环执行浏览器 MCP 工具后能把 browser run 写进统一状态事件；若没有这行代码，store 会变成新的旁路系统。
        from learning_agent.browser.runtime_events import BROWSER_ACTION_COMPLETED, BROWSER_ACTION_STARTED  # 新增代码+BrowserRuntimeStatus: 导入动作事件常量供 fake client 写真实格式；若没有这行代码，测试事件名可能和生产不一致。
        from learning_agent.browser.runtime_models import BrowserAction  # 新增代码+BrowserRuntimeStatus: 导入动作模型供 fake client 构造动作；若没有这行代码，测试无法模拟真实 server 落盘。
        from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+BrowserRuntimeStatus: 导入 store 供 fake client 写 run，也供断言读取；若没有这行代码，测试没有事实源。
        from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+BrowserRuntimeStatus: 导入统一状态事件 store；若没有这行代码，无法断言 UI/SDK 可见事件。
        class BrowserRuntimeWritingFakeClient(FakeMcpClient):  # 新增代码+BrowserRuntimeStatus: 定义会写 browser runtime store 的 fake MCP client；若没有这个类，测试只能依赖真实浏览器 server。
            def __init__(self, workspace: Path) -> None:  # 新增代码+BrowserRuntimeStatus: 初始化 fake client 并保存 workspace；若没有这行代码，fake 不知道把 run 写到哪里。
                super().__init__(tools=[{"name": "browser_wait", "description": "Wait", "inputSchema": {"type": "object", "properties": {"milliseconds": {"type": "integer"}}, "required": ["milliseconds"]}}])  # 新增代码+BrowserRuntimeStatus: 暴露一个 browser_wait MCP 工具；若没有这行代码，registry 无法识别 mcp__browser_automation__browser_wait。
                self.workspace = workspace  # 新增代码+BrowserRuntimeStatus: 保存测试 workspace；若没有这行代码，call_tool 无法定位 memory 目录。
            def call_tool(self, name: str, arguments: dict[str, object]) -> str:  # 新增代码+BrowserRuntimeStatus: 模拟 MCP 工具调用并写 browser runtime run；若没有这行代码，agent 没有 browser run 可镜像。
                store = BrowserRuntimeStore(self.workspace / "learning_agent" / "memory" / "browser_runtime")  # 新增代码+BrowserRuntimeStatus: 使用生产约定路径创建 store；若没有这行代码，agent 后续扫描不到 run。
                browser_run = store.create_run(run_id="browser-run-agent-1", session_id="fake-session", prompt="fake browser wait")  # 新增代码+BrowserRuntimeStatus: 写入 browser_run_created；若没有这行代码，状态镜像没有 run 根。
                action = BrowserAction.create(run_id=browser_run.run_id, stage_id="browser_wait", tool_name=name, arguments=arguments, action_id="browser-run-agent-1-action-1")  # 新增代码+BrowserRuntimeStatus: 创建 fake 动作；若没有这行代码，run 没有 action 事件。
                action.mark_started()  # 新增代码+BrowserRuntimeStatus: 标记动作开始；若没有这行代码，started 事件缺少状态。
                store.save_action(action, event_type=BROWSER_ACTION_STARTED)  # 新增代码+BrowserRuntimeStatus: 写 started 事件；若没有这行代码，状态镜像无法看到工具开始。
                action.mark_completed()  # 新增代码+BrowserRuntimeStatus: 标记动作完成；若没有这行代码，completed 事件缺少完成状态。
                store.save_action(action, event_type=BROWSER_ACTION_COMPLETED)  # 新增代码+BrowserRuntimeStatus: 写 completed 事件；若没有这行代码，状态镜像无法看到工具完成。
                browser_run = store.load_run(browser_run.run_id)  # 新增代码+BrowserRuntimeStatus: 重新读取含 action id 的 run；若没有这行代码，最终保存可能覆盖 action_ids。
                browser_run.mark_completed(summary="fake browser wait completed")  # 新增代码+BrowserRuntimeStatus: 标记 fake run 完成；若没有这行代码，状态事件无法显示最终状态。
                store.save_run(browser_run)  # 新增代码+BrowserRuntimeStatus: 保存完成状态；若没有这行代码，agent 扫描到的 run 仍是 pending。
                return "browser_wait 成功"  # 新增代码+BrowserRuntimeStatus: 返回工具成功文本；若没有这行代码，agent 会认为 MCP 调用失败。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRuntimeStatus: 使用临时 workspace 隔离 memory/status；若没有这行代码，测试会污染真实状态。
            workspace = Path(raw_dir)  # 新增代码+BrowserRuntimeStatus: 把临时路径转成 Path；若没有这行代码，路径拼接不清楚。
            registry = McpToolRegistry({"browser_automation": BrowserRuntimeWritingFakeClient(workspace)})  # 新增代码+BrowserRuntimeStatus: 注册 fake browser_automation server；若没有这行代码，agent 无法调用 MCP 工具。
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry, debug_enabled=False)  # 新增代码+BrowserRuntimeStatus: 创建带 fake MCP registry 的 agent；若没有这行代码，无法覆盖主循环工具执行层。
            agent.loaded_tool_names.add("mcp__browser_automation__browser_wait")  # 新增代码+BrowserRuntimeStatus: 显式加载被测 MCP 工具，避免测试卡在 tool_search 门禁；若没有这行代码，红灯会测到加载策略而不是 browser runtime 镜像。
            result = agent._execute_tool(ToolCall(name="mcp__browser_automation__browser_wait", arguments={"milliseconds": 1}))  # 新增代码+BrowserRuntimeStatus: 直接执行浏览器 MCP 工具；若没有这行代码，agent 不会触发镜像逻辑。
            status_events = StatusEventStore(workspace / "memory" / "status").list_events()  # 新增代码+BrowserRuntimeStatus: 读取统一状态事件；若没有这行代码，无法断言 UI/SDK 是否可见。
        self.assertIn("browser_wait 成功", result)  # 新增代码+BrowserRuntimeStatus: 断言工具结果仍正常返回；若没有这行代码，镜像逻辑可能破坏 MCP 输出。
        self.assertIn("browser_runtime_event", [event.event_type for event in status_events])  # 新增代码+BrowserRuntimeStatus: 断言 browser runtime 已进入统一状态事件流；若没有这行代码，旁路系统问题不会被发现。
        mirrored_payload = next(event.payload for event in status_events if event.event_type == "browser_runtime_event")  # 新增代码+BrowserRuntimeStatus: 取出镜像事件 payload；若没有这行代码，无法验证具体 run id。
        self.assertEqual(mirrored_payload["browser_run_id"], "browser-run-agent-1")  # 新增代码+BrowserRuntimeStatus: 断言状态事件包含 browser run id；若没有这行代码，CLI/API 无法定位 browser run。
        self.assertEqual(mirrored_payload["browser_run_status"], "completed")  # 新增代码+BrowserRuntimeStatus: 断言状态事件包含 browser run 状态；若没有这行代码，状态生态无法显示完成/失败。
