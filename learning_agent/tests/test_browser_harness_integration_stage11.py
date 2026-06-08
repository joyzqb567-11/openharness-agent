"""Stage 11 浏览器 harness 对齐测试，锁定 browser runtime 不能再是旁路系统。"""  # 新增代码+BrowserHarnessStage11: 说明本文件专门验证浏览器运行时接入长任务 harness；若没有这行代码，测试职责不清楚。
from __future__ import annotations  # 新增代码+BrowserHarnessStage11: 延迟解析类型注解；若没有这行代码，旧 Python 环境解析前向类型更容易出错。

import tempfile  # 新增代码+BrowserHarnessStage11: 创建隔离临时工作区；若没有这行代码，测试会污染真实项目 memory 目录。
import unittest  # 新增代码+BrowserHarnessStage11: 使用项目现有 unittest 测试风格；若没有这行代码，测试类无法被标准测试运行器执行。
from pathlib import Path  # 新增代码+BrowserHarnessStage11: 使用 Path 处理跨平台路径；若没有这行代码，路径拼接会退回脆弱字符串。

from learning_agent.browser.flow_runtime import BrowserFlowRuntime  # 新增代码+BrowserHarnessStage11: 导入真实流程 checkpoint 运行时；若没有这行代码，无法验证已完成 stage 不重跑。
from learning_agent.browser.flow_schema import parse_browser_flow  # 新增代码+BrowserHarnessStage11: 导入真实流程 schema 解析器；若没有这行代码，测试会绕过生产输入规范。
from learning_agent.browser.harness_integration import BrowserHarnessMirror, browser_harness_store_for_workspace  # 新增代码+BrowserHarnessStage11: 导入待实现的 browser 到 harness 投影层；若没有这行代码，测试无法证明旁路系统被统一。
from learning_agent.browser.runtime_models import BrowserRun  # 新增代码+BrowserHarnessStage11: 导入 browser run 协议对象；若没有这行代码，无法用真实数据模型驱动 mirror。
from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserHarnessStage11: 导入真实 MCP 浏览器 server；若没有这行代码，只能测 helper 而不能测生产入口。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+BrowserHarnessStage11: 导入统一状态快照；若没有这行代码，CLI/API/SDK 可见性无法验证。


class BrowserHarnessIntegrationStage11Tests(unittest.TestCase):  # 新增代码+BrowserHarnessStage11: 定义 Stage 11 测试集合；若没有这个类，unittest 无法发现这些验收断言。
    def test_browser_tool_creates_matching_harness_run_and_verifier_result(self) -> None:  # 新增代码+BrowserHarnessStage11: 验证顶层浏览器工具会自动创建 harness run；若没有这行代码，browser runtime 可能继续旁路运行。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+BrowserHarnessStage11: 使用临时目录隔离真实状态；若没有这行代码，测试会改动用户当前项目数据。
            root = Path(temp_dir)  # 新增代码+BrowserHarnessStage11: 把临时目录转为 Path；若没有这行代码，后续 store 构造会重复转换。
            server = BrowserAutomationServer(root)  # 新增代码+BrowserHarnessStage11: 创建真实浏览器 MCP server；若没有这行代码，无法覆盖 _start/_finish 生产接线。
            output = server.call("browser_provider_status", {})  # 新增代码+BrowserHarnessStage11: 调用不需要真实浏览器的状态工具触发顶层 run；若没有这行代码，harness 投影不会被生产入口驱动。
            self.assertIn("browser_provider_status", output)  # 新增代码+BrowserHarnessStage11: 确认工具正常返回状态；若没有这行代码，后续状态断言可能基于失败调用。
            browser_run_ids = server.browser_runtime_store.list_run_ids()  # 新增代码+BrowserHarnessStage11: 读取 browser runtime 生成的 run id；若没有这行代码，无法与 harness run 做同 id 对齐。
            self.assertEqual(len(browser_run_ids), 1)  # 新增代码+BrowserHarnessStage11: 确认本次测试只生成一个 browser run；若没有这行代码，后续取值可能误用历史 run。
            run_id = browser_run_ids[0]  # 新增代码+BrowserHarnessStage11: 保存 browser run id；若没有这行代码，harness 读取无法定位同一个任务。
            harness_store = browser_harness_store_for_workspace(root)  # 新增代码+BrowserHarnessStage11: 按 workspace 规则定位 harness store；若没有这行代码，项目根和包根路径会分裂。
            harness_run = harness_store.load_run(run_id)  # 新增代码+BrowserHarnessStage11: 读取同 id harness run；若没有这行代码，无法证明浏览器任务已接入 harness。
            self.assertEqual(harness_run.status, "completed")  # 新增代码+BrowserHarnessStage11: 断言 harness run 已收尾完成；若没有这行代码，状态 CLI 仍可能显示 running。
            self.assertEqual(harness_run.stages[0].status, "completed")  # 新增代码+BrowserHarnessStage11: 断言 harness stage 已完成；若没有这行代码，resume 仍可能重跑同阶段。
            self.assertTrue(harness_run.stages[0].acceptance.passed)  # 新增代码+BrowserHarnessStage11: 断言 stage verifier 通过；若没有这行代码，完成状态会缺少可审计验收。
            self.assertIn("browser_harness_projection", harness_run.stages[0].acceptance.checks)  # 新增代码+BrowserHarnessStage11: 断言 verifier checks 明确来自浏览器投影；若没有这行代码，验收结果来源不透明。
            event_types = [event.get("event_type", "") for event in harness_store.read_events(run_id)]  # 新增代码+BrowserHarnessStage11: 读取 harness event log 类型；若没有这行代码，无法验证 provider 决策是否镜像。
            self.assertIn("browser_provider_decision", event_types)  # 新增代码+BrowserHarnessStage11: 断言 provider 决策进入 harness 事件；若没有这行代码，其他 agent 无法复盘走哪条浏览器轨道。
            self.assertIn("verifier_result", event_types)  # 新增代码+BrowserHarnessStage11: 断言 verifier 结果进入 harness 事件；若没有这行代码，状态生态无法订阅验收结果。
            snapshot = build_status_snapshot(root)  # 新增代码+BrowserHarnessStage11: 构建统一状态快照；若没有这行代码，CLI/API 可见性没有被验证。
            linked_run = snapshot["browser"]["runs"][0]  # 新增代码+BrowserHarnessStage11: 读取 browser 区块里的 run；若没有这行代码，后续无法检查 harness 链接字段。
            self.assertEqual(linked_run["run_id"], run_id)  # 新增代码+BrowserHarnessStage11: 确认快照里的 browser run 是本次 run；若没有这行代码，可能误读其他状态文件。
            self.assertTrue(linked_run["harness"]["stages"][0]["acceptance"]["passed"])  # 新增代码+BrowserHarnessStage11: 断言 browser run 能直接看到 harness verifier；若没有这行代码，状态 API 仍要手工跨目录拼接。
            self.assertTrue(snapshot["browser"]["harness"]["latest_verifier"]["passed"])  # 新增代码+BrowserHarnessStage11: 断言 browser 总览暴露最新 verifier；若没有这行代码，UI/SDK 无法快速判断浏览器验收是否通过。

    def test_flow_checkpoint_resume_is_mirrored_to_harness_stages(self) -> None:  # 新增代码+BrowserHarnessStage11: 验证流程 checkpoint 和 harness stage 同步；若没有这行代码，进程中断后仍可能重复提交表单。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+BrowserHarnessStage11: 创建隔离临时目录；若没有这行代码，flow checkpoint 会污染真实 memory。
            root = Path(temp_dir)  # 新增代码+BrowserHarnessStage11: 保存临时工作区根路径；若没有这行代码，多个 store 路径会重复拼接。
            flow = parse_browser_flow({"flow_id": "flow-stage11", "stages": [{"name": "open", "tool": "browser_open", "arguments": {"url": "https://example.test"}}, {"name": "snap", "tool": "browser_snapshot", "arguments": {}}]})  # 新增代码+BrowserHarnessStage11: 构造两阶段浏览器流程；若没有这行代码，无法验证完成阶段跳过。
            runtime = BrowserFlowRuntime(root / "learning_agent" / "memory" / "browser_flows")  # 新增代码+BrowserHarnessStage11: 使用生产风格 checkpoint 目录；若没有这行代码，测试路径无法贴近真实 server。
            calls: list[str] = []  # 新增代码+BrowserHarnessStage11: 记录真实执行过的阶段名；若没有这行代码，无法断言第二轮没有重跑。
            def executor(stage):  # 新增代码+BrowserHarnessStage11: 定义确定性阶段执行器；若没有这行代码，测试会依赖真实浏览器和网络。
                calls.append(stage.name)  # 新增代码+BrowserHarnessStage11: 记录本次执行的阶段；若没有这行代码，resume 是否跳过无从判断。
                return f"ok:{stage.name}"  # 新增代码+BrowserHarnessStage11: 返回可审计阶段输出；若没有这行代码，checkpoint 缺少阶段结果。
            first_report = runtime.run(flow, executor)  # 新增代码+BrowserHarnessStage11: 首次执行流程并写 checkpoint；若没有这行代码，第二次没有历史可恢复。
            second_report = runtime.run(flow, executor)  # 新增代码+BrowserHarnessStage11: 第二次模拟进程恢复后的同流程执行；若没有这行代码，无法验证不重跑。
            browser_run = BrowserRun(run_id="browser_run_stage11_flow", session_id="stage11", prompt="browser flow stage11")  # 新增代码+BrowserHarnessStage11: 构造真实 browser run 对象；若没有这行代码，mirror 没有任务根。
            mirror = BrowserHarnessMirror(root)  # 新增代码+BrowserHarnessStage11: 创建 browser 到 harness 投影器；若没有这行代码，flow report 无法进入 harness。
            mirror.start_run(browser_run, "browser_flow_run")  # 新增代码+BrowserHarnessStage11: 创建同 id harness run；若没有这行代码，后续 flow stage 无处保存。
            mirror.sync_flow_report(browser_run.run_id, flow, first_report)  # 新增代码+BrowserHarnessStage11: 把首次流程结果写入 harness stage；若没有这行代码，harness 不知道阶段已完成。
            mirror.sync_flow_report(browser_run.run_id, flow, second_report)  # 新增代码+BrowserHarnessStage11: 把恢复跳过结果再次同步；若没有这行代码，skipped 信息不会进入审计。
            self.assertEqual(calls, ["open", "snap"])  # 新增代码+BrowserHarnessStage11: 断言第二次没有重跑已完成阶段；若没有这行代码，重复提交风险无法被测试发现。
            self.assertEqual(second_report["skipped_stage_names"], ["open", "snap"])  # 新增代码+BrowserHarnessStage11: 断言恢复报告明确列出跳过阶段；若没有这行代码，用户看不懂恢复做了什么。
            harness_run = browser_harness_store_for_workspace(root).load_run(browser_run.run_id)  # 新增代码+BrowserHarnessStage11: 读取同步后的 harness run；若没有这行代码，无法检查 stage 状态。
            stage_status = {stage.name: stage.status for stage in harness_run.stages}  # 新增代码+BrowserHarnessStage11: 建立阶段名到状态映射；若没有这行代码，断言会依赖列表顺序细节。
            self.assertEqual(stage_status, {"open": "completed", "snap": "completed"})  # 新增代码+BrowserHarnessStage11: 断言两个 flow stage 都已完成；若没有这行代码，harness resume 仍可能重跑。
            self.assertTrue(all(stage.acceptance.passed for stage in harness_run.stages))  # 新增代码+BrowserHarnessStage11: 断言所有 stage verifier 均通过；若没有这行代码，completed 状态可能没有验收依据。


if __name__ == "__main__":  # 新增代码+BrowserHarnessStage11: 支持直接运行本测试文件；若没有这行代码，人工调试必须记忆 unittest 模块路径。
    unittest.main()  # 新增代码+BrowserHarnessStage11: 启动 unittest 主程序；若没有这行代码，直接运行文件不会执行测试。
