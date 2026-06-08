"""浏览器状态生态测试，锁定 Stage 11 的 CLI/SDK/API 事实源。"""  # 新增代码+BrowserStatusStage11: 说明本测试覆盖浏览器状态输出；若没有这行代码，测试目的不清楚。

from learning_agent.tests.support import *  # 新增代码+BrowserStatusStage11: 复用项目测试基础设施；若没有这行代码，临时目录和断言工具需要重复导入。

from learning_agent.browser.runtime_models import BrowserAction, BrowserObservation  # 新增代码+BrowserStatusStage11: 导入浏览器协议模型；若没有这行代码，测试无法写入真实状态。
from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+BrowserStatusStage11: 导入浏览器 store；若没有这行代码，快照没有浏览器数据源。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+BrowserStatusStage11: 导入统一状态快照；若没有这行代码，状态生态无法验证。
from learning_agent.sdk.status import get_browser_events, get_browser_runs  # 新增代码+BrowserStatusStage11: 导入 SDK 浏览器入口；若没有这行代码，外部 agent 仍要读内部文件。


class BrowserStatusStage11Tests(unittest.TestCase):  # 新增代码+BrowserStatusStage11: 定义 Stage 11 测试类；若没有这行代码，unittest 无法收集断言。
    def test_status_snapshot_and_sdk_include_browser_runtime(self) -> None:  # 新增代码+BrowserStatusStage11: 验证浏览器状态进入统一快照和 SDK；若没有这行代码，UI/SDK 会继续看不到真实浏览器运行。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+BrowserStatusStage11: 使用临时工作区；若没有这行代码，测试会污染真实 memory。
            root = Path(temp_dir)  # 新增代码+BrowserStatusStage11: 保存临时工作区根目录；若没有这行代码，路径会重复转换。
            store = BrowserRuntimeStore(root / "memory" / "browser_runtime")  # 新增代码+BrowserStatusStage11: 创建默认浏览器 store；若没有这行代码，快照聚合器找不到数据。
            store.create_run(run_id="run-1", session_id="session-1", prompt="查天气")  # 新增代码+BrowserStatusStage11: 写入浏览器 run；若没有这行代码，快照 browser.runs 为空。
            action = BrowserAction.create("run-1", "stage-1", "browser_snapshot", {})  # 新增代码+BrowserStatusStage11: 创建浏览器动作；若没有这行代码，状态缺少 action。
            action.mark_completed("obs-1")  # 新增代码+BrowserStatusStage11: 标记动作完成；若没有这行代码，状态无法展示结果。
            observation = BrowserObservation(observation_id="obs-1", run_id="run-1", stage_id="stage-1", action_id=action.action_id, url="https://example.test", visible_text="天气")  # 新增代码+BrowserStatusStage11: 创建页面观察；若没有这行代码，状态缺少 observation。
            store.save_action(action)  # 新增代码+BrowserStatusStage11: 保存动作；若没有这行代码，run/action 断链。
            store.save_observation(observation)  # 新增代码+BrowserStatusStage11: 保存观察；若没有这行代码，run/observation 断链。
            snapshot = build_status_snapshot(root)  # 新增代码+BrowserStatusStage11: 构建统一状态快照；若没有这行代码，断言没有快照对象。
            self.assertEqual(snapshot["browser"]["counts"]["runs"], 1)  # 新增代码+BrowserStatusStage11: 验证 browser 区块统计 run；若没有这行代码，状态生态可能漏浏览器任务。
            self.assertEqual(snapshot["browser"]["runs"][0]["run_id"], "run-1")  # 新增代码+BrowserStatusStage11: 验证 run 细节可见；若没有这行代码，外部 agent 无法定位浏览器任务。
            self.assertEqual(get_browser_runs(root)[0]["run_id"], "run-1")  # 新增代码+BrowserStatusStage11: 验证 SDK 浏览器 run 入口；若没有这行代码，SDK 可能仍无专用接口。
            self.assertTrue(get_browser_events(root, "run-1"))  # 新增代码+BrowserStatusStage11: 验证 SDK 浏览器事件入口；若没有这行代码，外部 agent 无法增量观察浏览器动作。
