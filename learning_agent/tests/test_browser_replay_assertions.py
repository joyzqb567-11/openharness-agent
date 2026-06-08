"""浏览器回放和断言测试，锁定 Stage 10 的真实验收能力。"""  # 新增代码+BrowserReplayStage10: 说明本测试覆盖回放与 verifier 断言；若没有这行代码，测试目的不清楚。

from learning_agent.tests.support import *  # 新增代码+BrowserReplayStage10: 复用项目测试基础设施；若没有这行代码，临时目录和断言工具需要重复导入。

from learning_agent.browser.assertions import BrowserAssertionEngine  # 新增代码+BrowserReplayStage10: 导入待实现断言引擎；若没有这行代码，浏览器验收规则无法测试。
from learning_agent.browser.replay import BrowserReplayPlanner  # 新增代码+BrowserReplayStage10: 导入待实现回放计划器；若没有这行代码，动作复现能力无法测试。
from learning_agent.browser.runtime_models import BrowserAction, BrowserObservation  # 新增代码+BrowserReplayStage10: 导入协议模型；若没有这行代码，测试会绕过真实数据结构。
from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+BrowserReplayStage10: 导入 runtime store；若没有这行代码，回放无法从磁盘读取真实动作。
from learning_agent.acceptance.verifier import verify_acceptance_run  # 新增代码+BrowserReplayStage10: 导入真实验收 verifier；若没有这行代码，浏览器断言无法证明接入验收门禁。


class BrowserReplayStage10Tests(unittest.TestCase):  # 新增代码+BrowserReplayStage10: 定义 Stage 10 测试类；若没有这行代码，unittest 无法收集断言。
    def test_assertion_engine_checks_browser_evidence(self) -> None:  # 新增代码+BrowserReplayStage10: 验证浏览器证据断言；若没有这行代码，验收器只能检查终端文本。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+BrowserReplayStage10: 使用临时目录保存截图；若没有这行代码，测试会污染项目产物。
            screenshot_path = Path(temp_dir) / "shot.png"  # 新增代码+BrowserReplayStage10: 准备截图路径；若没有这行代码，screenshot_exists 断言没有目标。
            screenshot_path.write_bytes(b"png")  # 新增代码+BrowserReplayStage10: 写入占位截图；若没有这行代码，截图存在断言会失败。
            observation = BrowserObservation(observation_id="obs-1", run_id="run-1", stage_id="stage-1", action_id="action-1", url="https://example.test/weather", title="天气", visible_text="鄞州区明天天气 晴", screenshot_path=str(screenshot_path))  # 新增代码+BrowserReplayStage10: 构造页面证据；若没有这行代码，断言引擎没有输入。
            engine = BrowserAssertionEngine()  # 新增代码+BrowserReplayStage10: 创建断言引擎；若没有这行代码，测试没有执行对象。
            report = engine.evaluate_many([{"type": "url_contains", "expected": "weather"}, {"type": "visible_text_contains", "expected": "鄞州区"}, {"type": "screenshot_exists", "expected": "true"}], {"observation": observation})  # 新增代码+BrowserReplayStage10: 执行多条断言；若没有这行代码，验收聚合分支不会被覆盖。
            self.assertTrue(report["completed"])  # 新增代码+BrowserReplayStage10: 验证所有断言通过；若没有这行代码，失败断言可能被忽略。
            self.assertEqual(len(report["assertions"]), 3)  # 新增代码+BrowserReplayStage10: 验证返回逐项结果；若没有这行代码，用户看不到每条验收证据。

    def test_replay_planner_skips_secret_and_blocked_tools(self) -> None:  # 新增代码+BrowserReplayStage10: 验证回放不会重复秘密输入或高风险工具；若没有这行代码，回放可能泄露密码或重复提交。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+BrowserReplayStage10: 使用临时 store；若没有这行代码，测试会污染真实浏览器记录。
            store = BrowserRuntimeStore(Path(temp_dir) / "browser_runtime")  # 新增代码+BrowserReplayStage10: 创建浏览器 runtime store；若没有这行代码，回放计划没有事实源。
            store.create_run(run_id="run-1", session_id="session-1")  # 新增代码+BrowserReplayStage10: 创建 run；若没有这行代码，动作无法关联。
            open_action = BrowserAction.create("run-1", "stage-1", "browser_open", {"url": "https://example.test"})  # 新增代码+BrowserReplayStage10: 创建可回放打开动作；若没有这行代码，计划没有正常步骤。
            open_action.mark_completed()  # 新增代码+BrowserReplayStage10: 标记动作成功；若没有这行代码，失败动作可能进入计划。
            secret_action = BrowserAction.create("run-1", "stage-1", "browser_type_secret", {"secret_env_var": "LEARNING_AGENT_SECRET_PASSWORD"})  # 新增代码+BrowserReplayStage10: 创建 secret 动作；若没有这行代码，跳过秘密分支无法验证。
            secret_action.mark_completed()  # 新增代码+BrowserReplayStage10: 标记 secret 动作成功；若没有这行代码，回放过滤原因可能混淆失败状态。
            eval_action = BrowserAction.create("run-1", "stage-1", "browser_evaluate", {"script": "document.cookie"})  # 新增代码+BrowserReplayStage10: 创建高风险脚本动作；若没有这行代码，阻断工具分支无法验证。
            eval_action.mark_completed()  # 新增代码+BrowserReplayStage10: 标记高风险动作成功；若没有这行代码，过滤原因可能混淆失败状态。
            store.save_action(open_action)  # 新增代码+BrowserReplayStage10: 保存打开动作；若没有这行代码，计划器读取不到。
            store.save_action(secret_action)  # 新增代码+BrowserReplayStage10: 保存 secret 动作；若没有这行代码，跳过 secret 无法验证。
            store.save_action(eval_action)  # 新增代码+BrowserReplayStage10: 保存 evaluate 动作；若没有这行代码，阻断分支无法验证。
            plan = BrowserReplayPlanner(store).build_plan("run-1")  # 新增代码+BrowserReplayStage10: 生成回放计划；若没有这行代码，断言没有计划对象。
            self.assertEqual([step["tool_name"] for step in plan["steps"]], ["browser_open"])  # 新增代码+BrowserReplayStage10: 验证只保留安全动作；若没有这行代码，secret/evaluate 可能进入计划。
            self.assertEqual(len(plan["skipped"]), 2)  # 新增代码+BrowserReplayStage10: 验证跳过项可审计；若没有这行代码，用户不知道哪些动作没有回放。

    def test_acceptance_verifier_uses_browser_assertions_as_gate(self) -> None:  # 新增代码+BrowserReplayStage10: 验证 acceptance verifier 纳入浏览器断言；若没有这行代码，真实页面内容错误仍可能验收通过。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+BrowserReplayStage10: 使用临时验收目录；若没有这行代码，测试会污染真实 controller runs。
            run_dir = Path(temp_dir) / "run"  # 新增代码+BrowserReplayStage10: 定义模拟验收 run 目录；若没有这行代码，证据文件没有位置。
            run_dir.mkdir()  # 新增代码+BrowserReplayStage10: 创建 run 目录；若没有这行代码，写证据文件会失败。
            screenshot_path = run_dir / "03_final.png"  # 新增代码+BrowserReplayStage10: 准备最终截图路径；若没有这行代码，artifact 检查无法通过。
            screenshot_path.write_bytes(b"png")  # 新增代码+BrowserReplayStage10: 写入占位截图；若没有这行代码，截图存在断言会失败。
            (run_dir / "01_startup.png").write_bytes(b"png")  # 新增代码+BrowserReplayStage10: 写入启动截图；若没有这行代码，基础 artifact 门禁会失败。
            (run_dir / "02_prompt_sent.png").write_bytes(b"png")  # 新增代码+BrowserReplayStage10: 写入 prompt 截图；若没有这行代码，基础 artifact 门禁会失败。
            observation = BrowserObservation(observation_id="obs-1", run_id="run-1", stage_id="stage-1", action_id="action-1", url="https://example.test/weather", visible_text="武汉三天后天气 晴", screenshot_path=str(screenshot_path))  # 新增代码+BrowserReplayStage10: 构造浏览器页面证据；若没有这行代码，浏览器断言没有输入。
            observation_path = run_dir / "observation.json"  # 新增代码+BrowserReplayStage10: 定义 observation 文件路径；若没有这行代码，场景无法引用证据。
            observation_path.write_text(json.dumps(observation.to_dict(), ensure_ascii=False), encoding="utf-8")  # 新增代码+BrowserReplayStage10: 写入 observation JSON；若没有这行代码，verifier 无法加载页面证据。
            (run_dir / "result.json").write_text(json.dumps({"event_log": "events.jsonl", "copied_debug_log": "latest_run_readable.md", "startup_screenshot": "01_startup.png", "prompt_screenshot": "02_prompt_sent.png", "final_screenshot": "03_final.png"}, ensure_ascii=False), encoding="utf-8")  # 新增代码+BrowserReplayStage10: 写入 controller 结果索引；若没有这行代码，verifier 找不到基础证据。
            (run_dir / "events.jsonl").write_text(json.dumps({"state": "final_answer_printed", "payload": {"answer_text": "任务完成 武汉"}} , ensure_ascii=False) + "\n", encoding="utf-8")  # 新增代码+BrowserReplayStage10: 写入最终回答事件；若没有这行代码，基础回答断言没有输入。
            (run_dir / "latest_run_readable.md").write_text("browser_snapshot observation_id=obs-1", encoding="utf-8")  # 新增代码+BrowserReplayStage10: 写入 debug log；若没有这行代码，日志 artifact 门禁会失败。
            scenario_path = Path(temp_dir) / "scenario.json"  # 新增代码+BrowserReplayStage10: 定义场景文件路径；若没有这行代码，verifier 没有配置来源。
            scenario_path.write_text(json.dumps({"name": "browser-verifier", "event_answer_contains": ["武汉"], "debug_log_contains": ["browser_snapshot"], "browser_observation_path": "observation.json", "browser_assertions": [{"type": "url_contains", "expected": "weather"}, {"type": "visible_text_contains", "expected": "武汉"}, {"type": "screenshot_exists", "expected": "true"}]}, ensure_ascii=False), encoding="utf-8")  # 新增代码+BrowserReplayStage10: 写入浏览器断言场景；若没有这行代码，门禁分支不会启用。
            report = verify_acceptance_run(run_dir, scenario_path)  # 新增代码+BrowserReplayStage10: 执行真实 verifier；若没有这行代码，断言没有结果。
            self.assertTrue(report["completed"])  # 新增代码+BrowserReplayStage10: 验证总门禁通过；若没有这行代码，浏览器断言可能没有纳入结果。
            self.assertTrue(report["browser_assertions"]["completed"])  # 新增代码+BrowserReplayStage10: 验证浏览器断言区块通过；若没有这行代码，报告结构可能缺失。
