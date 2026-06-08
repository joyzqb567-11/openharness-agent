"""浏览器流程运行时测试，锁定 Stage 8 的阶段 checkpoint 与 resume。"""  # 新增代码+BrowserFlowStage8: 说明本测试覆盖复杂流程恢复；若没有这行代码，测试目的不清楚。

from learning_agent.tests.support import *  # 新增代码+BrowserFlowStage8: 复用项目测试基础设施；若没有这行代码，临时目录和 unittest 需要重复导入。

from learning_agent.browser.flow_runtime import BrowserFlowRuntime  # 新增代码+BrowserFlowStage8: 导入待实现流程运行时；若没有这行代码，测试无法驱动 Stage 8。
from learning_agent.browser.flow_schema import parse_browser_flow  # 新增代码+BrowserFlowStage8: 导入流程 schema 解析器；若没有这行代码，坏输入无法被规范化测试。


class BrowserFlowStage8Tests(unittest.TestCase):  # 新增代码+BrowserFlowStage8: 定义 Stage 8 测试类；若没有这行代码，unittest 无法收集断言。
    def test_flow_runtime_checkpoints_completed_stages_and_resumes(self) -> None:  # 新增代码+BrowserFlowStage8: 验证已完成阶段不会重跑；若没有这行代码，长任务恢复会重复提交表单。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+BrowserFlowStage8: 使用临时目录保存 checkpoint；若没有这行代码，测试会污染真实状态。
            flow = parse_browser_flow({"flow_id": "flow-1", "stages": [{"name": "open", "tool": "browser_open", "arguments": {"url": "https://example.test"}}, {"name": "snap", "tool": "browser_snapshot", "arguments": {}}]})  # 新增代码+BrowserFlowStage8: 解析两阶段流程；若没有这行代码，runtime 没有可执行计划。
            calls: list[str] = []  # 新增代码+BrowserFlowStage8: 记录实际执行阶段名；若没有这行代码，resume 是否跳过无法断言。
            def executor(stage):  # 新增代码+BrowserFlowStage8: 定义确定性阶段执行器；若没有这行代码，测试会依赖真实浏览器。
                calls.append(stage.name)  # 新增代码+BrowserFlowStage8: 记录阶段名；若没有这行代码，测试无法知道哪些阶段被执行。
                return f"ok:{stage.name}"  # 新增代码+BrowserFlowStage8: 返回成功文本；若没有这行代码，runtime 无法保存输出。
            runtime = BrowserFlowRuntime(Path(temp_dir))  # 新增代码+BrowserFlowStage8: 创建流程运行时；若没有这行代码，checkpoint 没有存储位置。
            first = runtime.run(flow, executor)  # 新增代码+BrowserFlowStage8: 首次执行完整流程；若没有这行代码，checkpoint 不会创建。
            second = runtime.run(flow, executor)  # 新增代码+BrowserFlowStage8: 第二次模拟 resume；若没有这行代码，跳过逻辑无法验证。
            self.assertTrue(first["completed"])  # 新增代码+BrowserFlowStage8: 验证首次完成；若没有这行代码，流程成功不受检查。
            self.assertTrue(second["completed"])  # 新增代码+BrowserFlowStage8: 验证 resume 后也完成；若没有这行代码，恢复结果不受检查。
            self.assertEqual(calls, ["open", "snap"])  # 新增代码+BrowserFlowStage8: 验证第二次没有重跑阶段；若没有这行代码，重复提交风险无法发现。
            self.assertEqual(second["skipped_stage_names"], ["open", "snap"])  # 新增代码+BrowserFlowStage8: 验证报告明确跳过阶段；若没有这行代码，用户看不懂恢复做了什么。

    def test_flow_schema_rejects_empty_stage_list(self) -> None:  # 新增代码+BrowserFlowStage8: 验证坏流程输入被拒绝；若没有这行代码，空流程可能假装成功。
        with self.assertRaises(ValueError):  # 新增代码+BrowserFlowStage8: 期待解析器抛出参数错误；若没有这行代码，坏输入不会被测试卡住。
            parse_browser_flow({"flow_id": "bad", "stages": []})  # 新增代码+BrowserFlowStage8: 传入空阶段列表；若没有这行代码，异常分支不会执行。
