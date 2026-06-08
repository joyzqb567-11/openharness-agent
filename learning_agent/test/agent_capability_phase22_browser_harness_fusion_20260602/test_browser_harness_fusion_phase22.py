import tempfile  # 新增代码+Phase22BrowserHarnessFusion: 创建隔离临时目录；如果没有这行代码，测试会污染真实 browser/harness 状态。
import unittest  # 新增代码+Phase22BrowserHarnessFusion: 引入 unittest 测试框架；如果没有这行代码，本文件无法定义测试用例。
from pathlib import Path  # 新增代码+Phase22BrowserHarnessFusion: 使用 Path 处理临时工作区路径；如果没有这行代码，路径拼接会退回脆弱字符串。

from learning_agent.app.chrome_status_renderer import render_chrome_status  # 新增代码+Phase22BrowserHarnessFusion: 导入 /chrome 渲染器；如果没有这行代码，测试无法证明 Chrome 状态暴露 harness 链接。
from learning_agent.app.status_renderer import render_status_snapshot  # 新增代码+Phase22BrowserHarnessFusion: 导入 /status 渲染器；如果没有这行代码，测试无法证明总状态暴露 harness 链接。
from learning_agent.browser.harness_integration import BrowserHarnessMirror, browser_harness_store_for_workspace  # 新增代码+Phase22BrowserHarnessFusion: 导入 browser 到 harness 投影层；如果没有这行代码，测试无法覆盖 Phase 22 融合点。
from learning_agent.browser.runtime_models import BrowserAction, BrowserRun  # 新增代码+Phase22BrowserHarnessFusion: 导入真实 browser run/action 协议模型；如果没有这行代码，测试会绕过生产数据结构。
from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+Phase22BrowserHarnessFusion: 导入 browser runtime store；如果没有这行代码，状态快照看不到测试 browser run。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+Phase22BrowserHarnessFusion: 导入统一状态快照；如果没有这行代码，UI 可见性无法验证。


class BrowserHarnessFusionPhase22Tests(unittest.TestCase):  # 新增代码+Phase22BrowserHarnessFusion: 定义 Phase 22 浏览器 harness 融合测试集合；如果没有这个类，unittest 不会发现本阶段测试。
    def test_action_evidence_is_deduplicated_and_visible_in_status_ui(self) -> None:  # 新增代码+Phase22BrowserHarnessFusion: 验证 action 证据去重并进入 /status 与 /chrome；如果没有这个测试，浏览器动作仍可能只停留在旁路 runtime。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase22BrowserHarnessFusion: 使用临时目录隔离状态文件；如果没有这行代码，测试会改动用户真实 memory。
            workspace = Path(raw_dir)  # 新增代码+Phase22BrowserHarnessFusion: 把临时目录转为 Path；如果没有这行代码，后续 store 构造会重复转换。
            browser_run = BrowserRun(run_id="browser_run_phase22", session_id="phase22", prompt="phase22 browser task")  # 新增代码+Phase22BrowserHarnessFusion: 构造真实 browser run；如果没有这行代码，mirror 没有 durable run 根。
            BrowserRuntimeStore(workspace / "memory" / "browser_runtime").save_run(browser_run)  # 新增代码+Phase22BrowserHarnessFusion: 把 browser run 写入生产 runtime store；如果没有这行代码，build_status_snapshot 的 browser.runs 会为空。
            action = BrowserAction.create(run_id=browser_run.run_id, stage_id="browser_snapshot", tool_name="browser_snapshot", arguments={"url": "https://example.test"}, action_id="phase22-action-1")  # 新增代码+Phase22BrowserHarnessFusion: 构造带稳定 id 的浏览器动作；如果没有这行代码，去重测试无法定位同一动作。
            action.mark_completed(observation_id="phase22-observation-1")  # 新增代码+Phase22BrowserHarnessFusion: 标记动作完成并关联 observation；如果没有这行代码，harness 证据缺少页面观察链接。
            mirror = BrowserHarnessMirror(workspace)  # 新增代码+Phase22BrowserHarnessFusion: 创建投影器；如果没有这行代码，浏览器 run/action 无法写入 harness。
            mirror.start_run(browser_run, "browser_snapshot")  # 新增代码+Phase22BrowserHarnessFusion: 创建同 id harness run；如果没有这行代码，action 证据没有目标 run。
            mirror.append_action_evidence(browser_run.run_id, action)  # 新增代码+Phase22BrowserHarnessFusion: 第一次同步 action 证据；如果没有这行代码，harness event 不会包含浏览器动作。
            mirror.append_action_evidence(browser_run.run_id, action)  # 新增代码+Phase22BrowserHarnessFusion: 第二次同步同一 action 证据；如果没有这行代码，无法证明 resume/retry 不重复写已完成动作。
            mirror.finish_run(browser_run, "browser_snapshot", True, "browser snapshot completed")  # 新增代码+Phase22BrowserHarnessFusion: 收尾 run 并写 verifier；如果没有这行代码，状态页看不到 passed verifier。
            events = browser_harness_store_for_workspace(workspace).read_events(browser_run.run_id)  # 新增代码+Phase22BrowserHarnessFusion: 读取 harness 事件；如果没有这行代码，无法断言 action evidence 是否落盘。
            action_events = [event for event in events if event.get("event_type") == "browser_action_evidence"]  # 新增代码+Phase22BrowserHarnessFusion: 过滤 action 证据事件；如果没有这行代码，事件计数会混入 provider/verifier。
            self.assertEqual(len(action_events), 1)  # 新增代码+Phase22BrowserHarnessFusion: 断言同一 action 只写一次；如果没有这行代码，恢复重试可能重复展示已完成动作。
            self.assertEqual(action_events[0]["payload"]["action_id"], "phase22-action-1")  # 新增代码+Phase22BrowserHarnessFusion: 断言 payload 保留 action id；如果没有这行代码，verifier 无法关联浏览器动作文件。
            self.assertEqual(action_events[0]["payload"]["observation_id"], "phase22-observation-1")  # 新增代码+Phase22BrowserHarnessFusion: 断言 payload 保留 observation id；如果没有这行代码，页面证据和动作断链。
            snapshot = build_status_snapshot(workspace)  # 新增代码+Phase22BrowserHarnessFusion: 构建统一状态快照；如果没有这行代码，无法验证 UI/SDK 可见性。
            harness_snapshot = snapshot["browser"]["runs"][0]["harness"]  # 新增代码+Phase22BrowserHarnessFusion: 读取 browser run 挂载的 harness 摘要；如果没有这行代码，后续断言没有目标对象。
            self.assertEqual(harness_snapshot["action_evidence_count"], 1)  # 新增代码+Phase22BrowserHarnessFusion: 断言快照暴露 action 证据数量；如果没有这行代码，/status 无法快速显示证据链完整度。
            self.assertEqual(harness_snapshot["latest_action_evidence"]["tool_name"], "browser_snapshot")  # 新增代码+Phase22BrowserHarnessFusion: 断言快照暴露最近动作工具名；如果没有这行代码，用户不知道 harness 证据对应哪步浏览器动作。
            status_text = render_status_snapshot(snapshot)  # 新增代码+Phase22BrowserHarnessFusion: 渲染 /status 文本；如果没有这行代码，无法验证总状态 UI。
            chrome_text = render_chrome_status(snapshot)  # 新增代码+Phase22BrowserHarnessFusion: 渲染 /chrome 文本；如果没有这行代码，无法验证 Chrome 状态 UI。
            self.assertIn("harness_run_id=browser_run_phase22", status_text)  # 新增代码+Phase22BrowserHarnessFusion: 断言 /status 显示 harness run 链接；如果没有这行代码，用户仍要手工跨目录找证据。
            self.assertIn("harness_verifier_passed=true", status_text)  # 新增代码+Phase22BrowserHarnessFusion: 断言 /status 显示 verifier 结果；如果没有这行代码，用户无法从状态页判断验收是否通过。
            self.assertIn("harness_action_evidence_count=1", chrome_text)  # 新增代码+Phase22BrowserHarnessFusion: 断言 /chrome 显示 action 证据数量；如果没有这行代码，浏览器状态页看不到 harness 融合证据。
            self.assertIn("harness_latest_action=browser_snapshot", chrome_text)  # 新增代码+Phase22BrowserHarnessFusion: 断言 /chrome 显示最近动作；如果没有这行代码，用户无法知道哪步浏览器动作已验收。


if __name__ == "__main__":  # 新增代码+Phase22BrowserHarnessFusion: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase22BrowserHarnessFusion: 启动 unittest 主函数；如果没有这行代码，直接运行文件不会执行任何测试。
