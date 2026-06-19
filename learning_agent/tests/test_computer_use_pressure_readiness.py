"""Computer Use 压力测试前置回归测试。"""  # 新增代码+ComputerUsePressureReadiness：说明本测试文件专门守住压力测试前的两个阻塞点；如果没有这行代码，后来的人不知道这些测试为什么存在。
from __future__ import annotations  # 新增代码+ComputerUsePressureReadiness：延迟类型注解解析；如果没有这行代码，老版本运行路径可能更早求值类型。

import json  # 新增代码+ComputerUsePressureReadiness：读取场景 JSON 并检查公开结果脱敏；如果没有这行代码，测试只能靠字符串猜测。
import unittest  # 新增代码+ComputerUsePressureReadiness：使用标准库测试框架，避免项目缺 pytest 配置时无法运行；如果没有这行代码，回归测试没有执行入口。
from pathlib import Path  # 新增代码+ComputerUsePressureReadiness：稳定定位仓库和场景目录；如果没有这行代码，测试会依赖当前工作目录。
from typing import Any  # 新增代码+ComputerUsePressureReadiness：标注测试 sender 的动态事件结构；如果没有这行代码，读者难以看出事件是字典列表。

from learning_agent.computer_use_mcp_v2.windows_runtime.sendinput_dispatcher import WindowsSendInputDispatcher  # 新增代码+ComputerUsePressureReadiness：导入被测 dispatcher；如果没有这行代码，无法验证 type_text 最后一跳。
from learning_agent.computer_use_mcp_v2.windows_runtime.sendinput_executor import WindowsSendInputExecutor  # 新增代码+ComputerUsePressureReadiness：导入被测 executor；如果没有这行代码，测试会绕过真实高层动作生成逻辑。


PROJECT_ROOT = Path(__file__).resolve().parents[2]  # 新增代码+ComputerUsePressureReadiness：从 learning_agent/tests 回到项目根目录；如果没有这行代码，场景目录在不同启动位置会找错。
SCENARIO_ROOT = PROJECT_ROOT / "learning_agent" / "acceptance_controller" / "scenarios"  # 新增代码+ComputerUsePressureReadiness：固定可见终端场景目录；如果没有这行代码，旧包路径扫描没有范围边界。
OLD_COMPUTER_USE_IMPORT = "learning_agent.computer_use."  # 新增代码+ComputerUsePressureReadiness：定义已经删除的旧包前缀；如果没有这行代码，测试里会到处硬编码同一字符串。
NEW_COMPUTER_USE_IMPORT = "learning_agent.computer_use_mcp_v2.windows_runtime."  # 新增代码+ComputerUsePressureReadiness：定义迁移后的 v2 包前缀；如果没有这行代码，测试不能确认场景指向当前源码。
MANUAL_PERMISSION_SCENARIO_KEYWORDS = {"permission_ui", "permission_denial"}  # 新增代码+ComputerUseAutoApproval：只允许专门测试权限 UI 或拒绝链路的场景保留人工 y/N；如果没有这行代码，普通压力测试会继续被反复输入 Y 拖慢。


class RawTextRequiredLowLevelSender:  # 新增代码+ComputerUsePressureReadiness：类段开始，模拟真实低层 sender 需要原文才能发送 Unicode；如果没有这个类，测试无法证明真实输入链路能拿到文字。
    requires_raw_text = True  # 新增代码+ComputerUsePressureReadiness：声明此 sender 需要原始文本；如果没有这行代码，executor 应该保持脱敏而不会把文本传下来。

    def __init__(self) -> None:  # 新增代码+ComputerUsePressureReadiness：函数段开始，初始化捕获事件列表；如果没有这段代码，测试无法查看低层收到什么。
        self.low_level_events: list[dict[str, Any]] = []  # 新增代码+ComputerUsePressureReadiness：保存低层事件副本；如果没有这行代码，断言无法确认 unicode_text 是否带 text。
    # 新增代码+ComputerUsePressureReadiness：函数段结束，RawTextRequiredLowLevelSender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def send_low_level(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+ComputerUsePressureReadiness：函数段开始，记录事件但不触碰真实桌面；如果没有这段代码，测试会误操作用户电脑。
        self.low_level_events.extend(dict(event) for event in events)  # 新增代码+ComputerUsePressureReadiness：复制每条低层事件用于断言；如果没有这行代码，事件可能被后续代码改写。
        return {"ok": True, "low_level_event_count": len(events), "sender": "raw_text_required_test_sender"}  # 新增代码+ComputerUsePressureReadiness：返回安全成功摘要且不带原文；如果没有这行代码，executor 无法形成成功结果。
    # 新增代码+ComputerUsePressureReadiness：函数段结束，RawTextRequiredLowLevelSender.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出 fake sender 范围。


class RedactedOnlyLowLevelSender:  # 新增代码+ComputerUsePressureReadiness：类段开始，模拟普通记录型 sender 不需要原文；如果没有这个类，测试不能守住非真实路径继续脱敏。
    def __init__(self) -> None:  # 新增代码+ComputerUsePressureReadiness：函数段开始，初始化捕获事件列表；如果没有这段代码，测试无法检查非真实路径是否仍然安全。
        self.low_level_events: list[dict[str, Any]] = []  # 新增代码+ComputerUsePressureReadiness：保存低层事件副本；如果没有这行代码，断言无法发现原文误传给记录型 sender。
    # 新增代码+ComputerUsePressureReadiness：函数段结束，RedactedOnlyLowLevelSender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def send_low_level(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+ComputerUsePressureReadiness：函数段开始，记录事件但不触碰真实桌面；如果没有这段代码，测试不能覆盖普通脱敏路径。
        self.low_level_events.extend(dict(event) for event in events)  # 新增代码+ComputerUsePressureReadiness：复制低层事件用于泄露检查；如果没有这行代码，测试看不到事件内容。
        return {"ok": True, "low_level_event_count": len(events), "sender": "redacted_only_test_sender"}  # 新增代码+ComputerUsePressureReadiness：返回不含原文的成功摘要；如果没有这行代码，executor 会把结果当成不稳定返回。
    # 新增代码+ComputerUsePressureReadiness：函数段结束，RedactedOnlyLowLevelSender.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出 fake sender 范围。


class ComputerUsePressureReadinessTests(unittest.TestCase):  # 新增代码+ComputerUsePressureReadiness：类段开始，集中验证压力测试前必须满足的源码条件；如果没有这个类，相关断言会散落难维护。
    def test_acceptance_scenarios_do_not_reference_deleted_computer_use_package(self) -> None:  # 新增代码+ComputerUsePressureReadiness：函数段开始，验证场景不再引用已删除旧包；如果没有这个测试，生产矩阵可能一运行就 ModuleNotFoundError。
        stale_references: list[str] = []  # 新增代码+ComputerUsePressureReadiness：收集所有旧路径命中位置；如果没有这行代码，失败时只能看到一个模糊断言。
        migrated_references = 0  # 新增代码+ComputerUsePressureReadiness：统计新路径引用数量；如果没有这行代码，测试无法确认确实迁到了 v2。
        for scenario_path in sorted(SCENARIO_ROOT.glob("*.json")):  # 新增代码+ComputerUsePressureReadiness：遍历全部场景 JSON；如果没有这行代码，只修生产矩阵会漏掉旧场景。
            payload = scenario_path.read_text(encoding="utf-8")  # 新增代码+ComputerUsePressureReadiness：读取当前场景文本；如果没有这行代码，测试无法扫描 import 字符串。
            if OLD_COMPUTER_USE_IMPORT in payload:  # 新增代码+ComputerUsePressureReadiness：检查是否仍有旧包前缀；如果没有这行代码，已删除目录引用会继续存在。
                stale_references.append(scenario_path.name)  # 新增代码+ComputerUsePressureReadiness：记录问题文件名；如果没有这行代码，修复者不知道该改哪一个场景。
            if NEW_COMPUTER_USE_IMPORT in payload:  # 新增代码+ComputerUsePressureReadiness：检查是否出现新 v2 包前缀；如果没有这行代码，机械删除旧路径也可能假通过。
                migrated_references += 1  # 新增代码+ComputerUsePressureReadiness：累计迁移后引用；如果没有这行代码，测试无法说明场景仍指向当前源码。
        self.assertEqual([], stale_references)  # 新增代码+ComputerUsePressureReadiness：要求所有旧路径清零；如果没有这行代码，压力测试仍可能抽到旧模块失败。
        self.assertGreater(migrated_references, 0)  # 新增代码+ComputerUsePressureReadiness：要求至少有一个 v2 场景引用；如果没有这行代码，测试可能在空扫描时误过。
    # 新增代码+ComputerUsePressureReadiness：函数段结束，test_acceptance_scenarios_do_not_reference_deleted_computer_use_package 到此结束；如果没有这个边界说明，初学者不容易看出旧路径门禁范围。

    def test_non_permission_ui_computer_use_scenarios_default_to_auto_approval(self) -> None:  # 新增代码+ComputerUseAutoApproval：函数段开始，验证普通 Computer Use 验收默认自动同意权限；如果没有这个测试，压力测试会重新退回每步输入 Y。
        manual_permission_leaks: list[str] = []  # 新增代码+ComputerUseAutoApproval：收集误关自动同意的普通场景名；如果没有这行代码，失败时用户不知道该改哪几个 JSON。
        for scenario_path in sorted(SCENARIO_ROOT.glob("*.json")):  # 新增代码+ComputerUseAutoApproval：遍历全部可见终端场景；如果没有这行代码，只检查单个 Paint 场景会漏掉 Notepad 或通用场景。
            scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+ComputerUseAutoApproval：读取当前场景 JSON 文本；如果没有这行代码，测试无法发现环境变量被显式设成 0。
            if "LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS" not in scenario_text:  # 新增代码+ComputerUseAutoApproval：跳过没有声明该权限变量的旧场景；如果没有这行代码，非 Computer Use 场景会被误判。
                continue  # 新增代码+ComputerUseAutoApproval：继续检查下一个场景；如果没有这行代码，旧场景会错误进入人工权限判断。
            scenario_name = scenario_path.stem.lower()  # 新增代码+ComputerUseAutoApproval：把场景名转成小写用于关键词判断；如果没有这行代码，大小写差异会让权限 UI 场景识别不稳定。
            is_manual_permission_test = any(keyword in scenario_name for keyword in MANUAL_PERMISSION_SCENARIO_KEYWORDS)  # 新增代码+ComputerUseAutoApproval：判断是否是专门测试权限弹窗的场景；如果没有这行代码，真正需要 y/N 的验收会被误改成自动同意。
            disables_auto_approval = '"LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS": "0"' in scenario_text  # 新增代码+ComputerUseAutoApproval：检测场景是否显式关闭自动同意；如果没有这行代码，测试无法抓住反复 Y 的根因。
            if disables_auto_approval and not is_manual_permission_test:  # 新增代码+ComputerUseAutoApproval：普通任务场景不允许关闭自动同意；如果没有这行代码，复杂压力测试仍会浪费大量时间在权限输入。
                manual_permission_leaks.append(scenario_path.name)  # 新增代码+ComputerUseAutoApproval：记录违规场景文件名；如果没有这行代码，修复者只能重新全目录搜索。
        self.assertEqual([], manual_permission_leaks)  # 新增代码+ComputerUseAutoApproval：要求普通 Computer Use 场景全部默认自动同意；如果没有这行代码，测试不会阻止 y/N 回归。
    # 新增代码+ComputerUseAutoApproval：函数段结束，test_non_permission_ui_computer_use_scenarios_default_to_auto_approval 到此结束；如果没有这个边界说明，初学者不容易看出默认同意门禁范围。

    def test_type_text_passes_raw_text_only_to_sender_that_requires_it(self) -> None:  # 新增代码+ComputerUsePressureReadiness：函数段开始，验证真实 sender 能拿到原文且公开结果不泄露；如果没有这个测试，type_text 可能假成功。
        secret_text = "phase-pressure-type-text-secret"  # 新增代码+ComputerUsePressureReadiness：准备不能出现在公开结果里的文本；如果没有这行代码，脱敏断言没有样本。
        sender = RawTextRequiredLowLevelSender()  # 新增代码+ComputerUsePressureReadiness：创建需要原文的低层 sender；如果没有这行代码，测试无法模拟真实 Windows Unicode 输入需求。
        dispatcher = WindowsSendInputDispatcher(platform="win32", enabled=True, low_level_sender=sender, target_verifier=lambda: {"ok": True})  # 新增代码+ComputerUsePressureReadiness：组装真实链路中的 dispatcher；如果没有这行代码，executor 不会展开到低层事件。
        executor = WindowsSendInputExecutor(platform="win32", enabled=True, sendinput_impl=dispatcher)  # 新增代码+ComputerUsePressureReadiness：组装真实链路中的 executor；如果没有这行代码，测试会跳过高层 type_text 入口。
        result = executor.execute("type_text", {"text": secret_text, "window": {"hwnd": 1234, "window_id": "hwnd:1234"}})  # 新增代码+ComputerUsePressureReadiness：执行受控文本动作；如果没有这行代码，测试没有行为样本。
        unicode_events = [event for event in sender.low_level_events if event.get("type") == "unicode_text"]  # 新增代码+ComputerUsePressureReadiness：筛出真实文本输入事件；如果没有这行代码，断言会被 set_foreground/pause 干扰。
        public_payload = json.dumps(result.data, ensure_ascii=False, sort_keys=True)  # 新增代码+ComputerUsePressureReadiness：序列化公开结果做泄露检查；如果没有这行代码，脱敏只靠人工肉眼。
        self.assertTrue(result.ok)  # 新增代码+ComputerUsePressureReadiness：确认动作链路报告成功；如果没有这行代码，后续事件断言可能掩盖执行失败。
        self.assertEqual(secret_text, unicode_events[-1].get("text"))  # 新增代码+ComputerUsePressureReadiness：确认真实 sender 收到原文；如果没有这行代码，低层会继续发送空字符串。
        self.assertNotIn(secret_text, public_payload)  # 新增代码+ComputerUsePressureReadiness：确认公开结果仍然脱敏；如果没有这行代码，修复可能把用户文本写进日志。
    # 新增代码+ComputerUsePressureReadiness：函数段结束，test_type_text_passes_raw_text_only_to_sender_that_requires_it 到此结束；如果没有这个边界说明，初学者不容易看出 raw text 门禁范围。

    def test_type_text_stays_redacted_for_sender_that_does_not_require_raw_text(self) -> None:  # 新增代码+ComputerUsePressureReadiness：函数段开始，验证普通记录型 sender 不会拿到原文；如果没有这个测试，修复可能扩大明文传播范围。
        secret_text = "phase-pressure-redacted-only-secret"  # 新增代码+ComputerUsePressureReadiness：准备不能传给普通 sender 的文本；如果没有这行代码，测试没有泄露样本。
        sender = RedactedOnlyLowLevelSender()  # 新增代码+ComputerUsePressureReadiness：创建不声明需要原文的 sender；如果没有这行代码，测试无法覆盖安全记录路径。
        dispatcher = WindowsSendInputDispatcher(platform="win32", enabled=True, low_level_sender=sender, target_verifier=lambda: {"ok": True})  # 新增代码+ComputerUsePressureReadiness：组装普通记录型 dispatcher；如果没有这行代码，事件不会进入低层列表。
        executor = WindowsSendInputExecutor(platform="win32", enabled=True, sendinput_impl=dispatcher)  # 新增代码+ComputerUsePressureReadiness：组装 executor；如果没有这行代码，无法通过真实 type_text 入口生成事件。
        result = executor.execute("type_text", {"text": secret_text})  # 新增代码+ComputerUsePressureReadiness：执行文本动作；如果没有这行代码，测试没有可检查数据。
        internal_payload = json.dumps(sender.low_level_events, ensure_ascii=False, sort_keys=True)  # 新增代码+ComputerUsePressureReadiness：序列化普通 sender 看到的事件；如果没有这行代码，无法检查是否误带原文。
        public_payload = json.dumps(result.data, ensure_ascii=False, sort_keys=True)  # 新增代码+ComputerUsePressureReadiness：序列化公开结果；如果没有这行代码，无法检查日志脱敏。
        self.assertTrue(result.ok)  # 新增代码+ComputerUsePressureReadiness：确认普通记录链路仍然可执行；如果没有这行代码，脱敏测试可能在失败路径上误过。
        self.assertNotIn(secret_text, internal_payload)  # 新增代码+ComputerUsePressureReadiness：确认普通 sender 不收到原文；如果没有这行代码，明文传播范围会失控。
        self.assertNotIn(secret_text, public_payload)  # 新增代码+ComputerUsePressureReadiness：确认公开结果不泄露原文；如果没有这行代码，日志安全没有回归保护。
    # 新增代码+ComputerUsePressureReadiness：函数段结束，test_type_text_stays_redacted_for_sender_that_does_not_require_raw_text 到此结束；如果没有这个边界说明，初学者不容易看出普通 sender 脱敏范围。


if __name__ == "__main__":  # 新增代码+ComputerUsePressureReadiness：允许直接运行本测试文件；如果没有这行代码，用户不能用 python 文件方式快速验收。
    unittest.main()  # 新增代码+ComputerUsePressureReadiness：启动 unittest；如果没有这行代码，直接运行文件不会执行任何测试。
