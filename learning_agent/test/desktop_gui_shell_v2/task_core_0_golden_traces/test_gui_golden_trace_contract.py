from __future__ import annotations  # 新增代码+GoldenTraceContractTest：启用未来注解语法；如果没有这一行，后续类型标注在旧解释器行为下可能不一致。

import json  # 新增代码+GoldenTraceContractTest：读取并解析 golden trace JSON；如果没有这一行，测试只能检查文件存在，无法检查内容形状。
import unittest  # 新增代码+GoldenTraceContractTest：使用标准库 unittest 跑合同测试；如果没有这一行，蓝图指定的 unittest 命令无法收集测试。
from pathlib import Path  # 新增代码+GoldenTraceContractTest：用 Path 稳定定位 repo 内 fixture；如果没有这一行，路径拼接容易在 Windows 上出错。


_REPO_ROOT = Path(__file__).resolve().parents[2]  # 新增代码+GoldenTraceContractTest：从当前测试文件反推仓库根目录；如果没有这一行，从别的目录运行测试会找不到 fixture。
_FIXTURE_PATH = _REPO_ROOT / "apps" / "desktop" / "tests" / "fixtures" / "gui-v2-golden-events.json"  # 新增代码+GoldenTraceContractTest：集中定义 golden trace fixture 路径；如果没有这一行，每个测试都要重复硬编码路径。
_FORBIDDEN_RAW_TEXT = ("x-openharness-desktop-token", "traceback", "authorization")  # 新增代码+GoldenTraceContractTest：列出 fixture 内绝对不能出现的敏感文本；如果没有这一行，测试可能漏掉泄露词。


class GuiGoldenTraceContractTest(unittest.TestCase):  # 新增代码+GoldenTraceContractTest：测试类段开始，集中验证 GUI V2 golden trace 数据合同；如果没有这个类，unittest 不会执行这些断言。
    def _load_traces(self) -> list[dict[str, object]]:  # 新增代码+GoldenTraceContractTest：函数段开始，读取并返回所有 golden traces；如果没有这段 helper，两个测试会重复读取逻辑。
        self.assertTrue(_FIXTURE_PATH.exists(), f"missing fixture: {_FIXTURE_PATH}")  # 新增代码+GoldenTraceContractTest：先确认 fixture 文件存在；如果没有这一行，失败时只会得到难读的文件异常。
        return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))  # 新增代码+GoldenTraceContractTest：按 UTF-8 读取 JSON；如果没有这一行，中文 prompt 可能在默认编码下损坏。
    # 新增代码+GoldenTraceContractTest：函数段结束，_load_traces 到此结束；如果没有这个边界说明，用户不容易看出读取逻辑范围。

    def test_all_golden_traces_have_required_shape(self) -> None:  # 新增代码+GoldenTraceContractTest：函数段开始，验证 20 条轨迹都具备统一形状；如果没有这段测试，后续 reducer 可能收到坏数据。
        traces = self._load_traces()  # 新增代码+GoldenTraceContractTest：读取 fixture 内容；如果没有这一行，后续断言没有输入对象。
        self.assertEqual(20, len(traces))  # 新增代码+GoldenTraceContractTest：锁定 V2 蓝图要求的 20 个场景；如果没有这一行，少场景也会误过。
        expected_ids = {f"GT-{index:03d}" for index in range(1, 21)}  # 新增代码+GoldenTraceContractTest：生成 GT-001 到 GT-020 的完整 id 集；如果没有这一行，测试无法发现跳号或误命名。
        actual_ids = {str(trace["id"]) for trace in traces}  # 新增代码+GoldenTraceContractTest：收集 fixture 里的实际 id；如果没有这一行，无法验证唯一性和完整性。
        self.assertEqual(expected_ids, actual_ids)  # 新增代码+GoldenTraceContractTest：确认 id 完整且唯一；如果没有这一行，重复 id 会破坏回归报告。
        for trace in traces:  # 新增代码+GoldenTraceContractTest：逐条检查每个场景；如果没有这一行，只能检查总数，发现不了局部字段缺失。
            self.assertIsInstance(trace["name"], str)  # 新增代码+GoldenTraceContractTest：确认场景名是字符串；如果没有这一行，前端标题可能渲染失败。
            self.assertIsInstance(trace["prompt"], str)  # 新增代码+GoldenTraceContractTest：确认 prompt 是字符串；如果没有这一行，composer 回放可能收到错误类型。
            self.assertGreater(len(str(trace["prompt"])), 0)  # 新增代码+GoldenTraceContractTest：确认 prompt 不为空；如果没有这一行，空场景会让验收没有真实输入。
            self.assertIsInstance(trace["events"], list)  # 新增代码+GoldenTraceContractTest：确认 events 是数组；如果没有这一行，事件 reducer 无法遍历。
            self.assertGreater(len(trace["events"]), 0)  # 新增代码+GoldenTraceContractTest：确认每条轨迹至少有一个事件；如果没有这一行，空轨迹无法测试 GUI 行为。
            self.assertIsInstance(trace["must_not_contain"], list)  # 新增代码+GoldenTraceContractTest：确认低敏禁止词是数组；如果没有这一行，后续红线检查无法统一处理。
            for event in trace["events"]:  # 新增代码+GoldenTraceContractTest：逐个事件检查统一字段；如果没有这一行，单个坏事件可能混进 fixture。
                self.assertIsInstance(event, dict)  # 新增代码+GoldenTraceContractTest：确认事件是对象；如果没有这一行，前端 reducer 可能读取非对象崩溃。
                self.assertIn("sequence", event)  # 新增代码+GoldenTraceContractTest：确认事件有序号；如果没有这一行，流式回放无法稳定排序。
                self.assertIn("kind", event)  # 新增代码+GoldenTraceContractTest：确认事件有类型；如果没有这一行，UI 不知道该渲染哪种状态。
                self.assertIn("payload", event)  # 新增代码+GoldenTraceContractTest：确认事件有载荷；如果没有这一行，事件只有壳没有内容。
                self.assertIsInstance(event["sequence"], int)  # 新增代码+GoldenTraceContractTest：确认 sequence 是整数；如果没有这一行，排序可能按字符串错误排序。
                self.assertIsInstance(event["kind"], str)  # 新增代码+GoldenTraceContractTest：确认 kind 是字符串；如果没有这一行，状态机匹配会失败。
                self.assertIsInstance(event["payload"], dict)  # 新增代码+GoldenTraceContractTest：确认 payload 是对象；如果没有这一行，前端展开详情会失败。
    # 新增代码+GoldenTraceContractTest：函数段结束，test_all_golden_traces_have_required_shape 到此结束；如果没有这个边界说明，用户不容易看出形状测试范围。

    def test_golden_traces_do_not_store_tokens_or_tracebacks(self) -> None:  # 新增代码+GoldenTraceContractTest：函数段开始，验证 fixture 不存敏感词或原始异常词；如果没有这段测试，黄金样本本身可能成为泄露源。
        raw_text = _FIXTURE_PATH.read_text(encoding="utf-8").lower()  # 新增代码+GoldenTraceContractTest：按小写读取原始 fixture 文本；如果没有这一行，大小写变化可能绕过检查。
        for forbidden_text in _FORBIDDEN_RAW_TEXT:  # 新增代码+GoldenTraceContractTest：逐个检查禁止文本；如果没有这一行，只能写重复断言且容易漏项。
            self.assertNotIn(forbidden_text, raw_text)  # 新增代码+GoldenTraceContractTest：确认 fixture 没有保存该禁止文本；如果没有这一行，敏感词可能进入前端测试样本。
    # 新增代码+GoldenTraceContractTest：函数段结束，test_golden_traces_do_not_store_tokens_or_tracebacks 到此结束；如果没有这个边界说明，用户不容易看出低敏测试范围。
# 新增代码+GoldenTraceContractTest：测试类段结束，GuiGoldenTraceContractTest 到此结束；如果没有这个边界说明，用户不容易看出本文件只测 golden trace 合同。


if __name__ == "__main__":  # 新增代码+GoldenTraceContractTest：允许直接运行本文件；如果没有这一行，用户手动排查时只能记 unittest 模块命令。
    unittest.main()  # 新增代码+GoldenTraceContractTest：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行测试。
