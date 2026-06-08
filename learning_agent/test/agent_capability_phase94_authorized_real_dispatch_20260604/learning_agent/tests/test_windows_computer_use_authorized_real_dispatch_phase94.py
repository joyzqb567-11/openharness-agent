# 新增代码+Phase94AuthorizedRealDispatch：导入 json 是为了扫描报告里是否泄露原始 prompt 或输入文本；如果没有这行代码，隐私断言只能靠人工检查。
import json  # 新增代码+Phase94AuthorizedRealDispatch：使用 JSON 序列化报告；如果没有这行代码，嵌套字段里的明文泄露可能漏检。
# 新增代码+Phase94AuthorizedRealDispatch：导入 tempfile 是为了给每个测试分配隔离目录；如果没有这行代码，授权状态和报告会污染真实 memory 目录。
import tempfile  # 新增代码+Phase94AuthorizedRealDispatch：创建临时目录承载 grants 和 reports；如果没有这行代码，测试之间可能互相影响。
# 新增代码+Phase94AuthorizedRealDispatch：导入 unittest 是为了沿用项目现有标准测试框架；如果没有这行代码，python -m unittest 无法发现这些用例。
import unittest  # 新增代码+Phase94AuthorizedRealDispatch：提供 TestCase 和断言方法；如果没有这行代码，测试文件不能直接运行。
# 新增代码+Phase94AuthorizedRealDispatch：导入 Path 是为了稳定处理 Windows 路径；如果没有这行代码，临时目录传参会退化成脆弱字符串拼接。
from pathlib import Path  # 新增代码+Phase94AuthorizedRealDispatch：把临时路径转换为 Path 对象；如果没有这行代码，运行时接口类型覆盖不足。
# 新增代码+Phase94AuthorizedRealDispatch：导入 Phase94 待实现模块是 TDD 红灯入口；如果没有这行代码，测试不会证明新能力缺失。
from learning_agent.computer_use.authorized_real_dispatch import (  # 新增代码+Phase94AuthorizedRealDispatch：导入 Phase94 公共 API；如果没有这行代码，测试无法驱动实现。
    PHASE94_AUTHORIZED_REAL_DISPATCH_MARKER,  # 新增代码+Phase94AuthorizedRealDispatch：导入 ready marker；如果没有这行代码，终端验收 token 无法被测试锁定。
    PHASE94_AUTHORIZED_REAL_DISPATCH_OK_TOKEN,  # 新增代码+Phase94AuthorizedRealDispatch：导入 OK token；如果没有这行代码，验收成功文本可能漂移。
    PHASE94_REAL_DISPATCH_ENV,  # 新增代码+Phase94AuthorizedRealDispatch：导入真实派发环境门；如果没有这行代码，测试无法确认真实动作必须显式打开。
    Phase94RecordingLowLevelSender,  # 新增代码+Phase94AuthorizedRealDispatch：导入记录型 sender；如果没有这行代码，单测只能触碰真实鼠标键盘。
    WindowsAuthorizedRealDispatchCandidate,  # 新增代码+Phase94AuthorizedRealDispatch：导入候选适配器；如果没有这行代码，测试没有主对象。
    phase94_cli_line,  # 新增代码+Phase94AuthorizedRealDispatch：导入 CLI token 格式化函数；如果没有这行代码，真实终端输出无法稳定验收。
    run_phase94_authorized_real_dispatch_candidate_contract,  # 新增代码+Phase94AuthorizedRealDispatch：导入总合同入口；如果没有这行代码，测试和终端没有统一事实源。
)  # 新增代码+Phase94AuthorizedRealDispatch：结束导入列表；如果没有这行代码，Python 语法不完整。


# 新增代码+Phase94AuthorizedRealDispatch：类段开始，本测试类验证 Phase94 把 Phase93 recording-only 缺口推进到授权后低层派发候选；如果没有这段测试，后续实现可能仍停在口头声明。
class WindowsComputerUseAuthorizedRealDispatchPhase94Tests(unittest.TestCase):  # 新增代码+Phase94AuthorizedRealDispatch：定义 Phase94 测试类；如果没有这行代码，unittest 不会组织这些断言。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段开始，本测试验证总合同覆盖默认关闭、授权候选、拒绝路径和脱敏；如果没有这段测试，Phase94 可能只测 happy path。
    def test_phase94_contract_proves_authorized_real_dispatch_candidate(self):  # 新增代码+Phase94AuthorizedRealDispatch：定义总合同测试；如果没有这行代码，核心成功标准没有自动保护。
        # 新增代码+Phase94AuthorizedRealDispatch：创建临时目录承载 Phase94 合同输出；如果没有这行代码，测试会写入真实项目 memory。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase94AuthorizedRealDispatch：使用上下文自动清理临时目录；如果没有这行代码，测试后会残留证据文件。
            # 新增代码+Phase94AuthorizedRealDispatch：运行 Phase94 总合同；如果没有这行代码，后续断言没有事实来源。
            report = run_phase94_authorized_real_dispatch_candidate_contract(base_dir=Path(temporary_directory))  # 新增代码+Phase94AuthorizedRealDispatch：把隔离目录注入合同；如果没有这行代码，报告落点不可控。
        # 新增代码+Phase94AuthorizedRealDispatch：确认合同整体通过；如果没有这行代码，字段局部正确也可能掩盖整体失败。
        self.assertTrue(report["passed"])  # 新增代码+Phase94AuthorizedRealDispatch：断言 passed 为真；如果没有这行代码，失败实现可能被误认为可用。
        # 新增代码+Phase94AuthorizedRealDispatch：确认 ready marker 稳定；如果没有这行代码，真实终端场景无法可靠匹配阶段。
        self.assertEqual(report["marker"], PHASE94_AUTHORIZED_REAL_DISPATCH_MARKER)  # 新增代码+Phase94AuthorizedRealDispatch：检查 marker；如果没有这行代码，token 漂移不会被发现。
        # 新增代码+Phase94AuthorizedRealDispatch：确认 OK token 稳定；如果没有这行代码，验收脚本可能误判普通日志。
        self.assertEqual(report["ok_token"], PHASE94_AUTHORIZED_REAL_DISPATCH_OK_TOKEN)  # 新增代码+Phase94AuthorizedRealDispatch：检查 OK token；如果没有这行代码，成功标识没有回归保护。
        # 新增代码+Phase94AuthorizedRealDispatch：确认 Phase93 的 recording-only 缺口被候选路径覆盖；如果没有这行代码，Phase94 可能没有承接上一阶段差距。
        self.assertTrue(report["phase93_recording_gap_closed_by_candidate"])  # 新增代码+Phase94AuthorizedRealDispatch：断言 Phase93 缺口被候选层接住；如果没有这行代码，架构对齐目标不可见。
        # 新增代码+Phase94AuthorizedRealDispatch：确认授权后低层事件已经到达注入 sender；如果没有这行代码，所谓真实派发候选可能只是高层记录。
        self.assertTrue(report["authorized_low_level_dispatch_reaches_sender"])  # 新增代码+Phase94AuthorizedRealDispatch：断言低层 sender 被调用；如果没有这行代码，主链路仍可能停在 recording-only。
        # 新增代码+Phase94AuthorizedRealDispatch：确认默认不开真实物理动作；如果没有这行代码，普通运行可能误操控用户电脑。
        self.assertTrue(report["real_dispatch_default_disabled"])  # 新增代码+Phase94AuthorizedRealDispatch：断言默认禁用真实派发；如果没有这行代码，安全默认值没有保护。
        # 新增代码+Phase94AuthorizedRealDispatch：确认真实派发必须走显式环境门；如果没有这行代码，启用方式会散落且不可审计。
        self.assertEqual(report["real_dispatch_env_gate"], PHASE94_REAL_DISPATCH_ENV)  # 新增代码+Phase94AuthorizedRealDispatch：检查环境变量名；如果没有这行代码，产品开关可能漂移。
        # 新增代码+Phase94AuthorizedRealDispatch：确认合同中没有实际物理派发；如果没有这行代码，自动化测试可能触碰桌面。
        self.assertFalse(report["real_dispatch_performed"])  # 新增代码+Phase94AuthorizedRealDispatch：断言没有真实物理派发；如果没有这行代码，安全边界可能被误放宽。
        # 新增代码+Phase94AuthorizedRealDispatch：确认未授权窗口仍是零事件；如果没有这行代码，默认拒绝可能只在文案层存在。
        self.assertTrue(report["unauthorized_window_zero_events"])  # 新增代码+Phase94AuthorizedRealDispatch：断言未授权零事件；如果没有这行代码，拒绝路径副作用不会暴露。
        # 新增代码+Phase94AuthorizedRealDispatch：确认危险窗口仍是零事件；如果没有这行代码，终端或登录窗口风险可能回归。
        self.assertTrue(report["unsafe_window_zero_events"])  # 新增代码+Phase94AuthorizedRealDispatch：断言危险窗口零事件；如果没有这行代码，高风险拦截没有自动保护。
        # 新增代码+Phase94AuthorizedRealDispatch：确认目标漂移仍是零事件；如果没有这行代码，焦点切走后可能误发输入。
        self.assertTrue(report["target_drift_zero_events"])  # 新增代码+Phase94AuthorizedRealDispatch：断言漂移零事件；如果没有这行代码，目标复验缺口不会被发现。
        # 新增代码+Phase94AuthorizedRealDispatch：确认报告脱敏；如果没有这行代码，真实用户 prompt 或输入文本可能进入日志。
        self.assertTrue(report["raw_text_hidden"])  # 新增代码+Phase94AuthorizedRealDispatch：断言明文隐藏；如果没有这行代码，隐私门禁不可验证。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段结束，本测试到此完成总合同覆盖；如果没有这个边界说明，初学者不容易看出测试范围。

    # 新增代码+Phase94AuthorizedRealDispatch：函数段开始，本测试验证适配器在显式 enable 后能把低层事件交给注入 sender；如果没有这段测试，主路径可能仍不触达低层。
    def test_authorized_candidate_dispatches_low_level_events_to_injected_sender(self):  # 新增代码+Phase94AuthorizedRealDispatch：定义授权派发候选测试；如果没有这行代码，低层 sender 桥接没有单独保护。
        # 新增代码+Phase94AuthorizedRealDispatch：创建临时目录隔离授权 store；如果没有这行代码，测试授权可能污染真实会话。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase94AuthorizedRealDispatch：使用临时目录上下文；如果没有这行代码，测试状态不会自动清理。
            # 新增代码+Phase94AuthorizedRealDispatch：创建记录型低层 sender；如果没有这行代码，测试可能调用真实系统输入。
            sender = Phase94RecordingLowLevelSender()  # 新增代码+Phase94AuthorizedRealDispatch：准备安全 sender；如果没有这行代码，无法检查事件是否到达。
            # 新增代码+Phase94AuthorizedRealDispatch：创建 Phase94 runtime；如果没有这行代码，授权和派发无法组合。
            runtime = WindowsAuthorizedRealDispatchCandidate(base_dir=Path(temporary_directory), low_level_sender=sender)  # 新增代码+Phase94AuthorizedRealDispatch：注入临时目录和 sender；如果没有这行代码，测试不可控。
            # 新增代码+Phase94AuthorizedRealDispatch：构造普通授权窗口；如果没有这行代码，安全边界没有目标。
            window = runtime.contract_window()  # 新增代码+Phase94AuthorizedRealDispatch：复用合同窗口；如果没有这行代码，测试字段可能和实现不一致。
            # 新增代码+Phase94AuthorizedRealDispatch：写入短期授权；如果没有这行代码，安全边界应该拒绝所有动作。
            runtime.authorize_window(window, session_id="phase94-unit", action_scope=["click"])  # 新增代码+Phase94AuthorizedRealDispatch：授权 click 动作；如果没有这行代码，正例无法进入低层候选。
            # 新增代码+Phase94AuthorizedRealDispatch：显式请求候选派发；如果没有这行代码，默认关闭路径会返回零事件。
            result = runtime.dispatch(window, "click", {"x": 320, "y": 240}, session_id="phase94-unit", enable_real_dispatch=True)  # 新增代码+Phase94AuthorizedRealDispatch：执行授权点击候选；如果没有这行代码，sender 调用无法验证。
        # 新增代码+Phase94AuthorizedRealDispatch：确认动作成功进入候选层；如果没有这行代码，失败也可能被当成派发成功。
        self.assertTrue(result["ok"])  # 新增代码+Phase94AuthorizedRealDispatch：断言结果 ok；如果没有这行代码，适配器失败不会暴露。
        # 新增代码+Phase94AuthorizedRealDispatch：确认低层事件数量大于零；如果没有这行代码，空动作可能误报。
        self.assertGreater(result["low_level_event_count"], 0)  # 新增代码+Phase94AuthorizedRealDispatch：断言有低层事件；如果没有这行代码，候选路径可能仍是记录型高层事件。
        # 新增代码+Phase94AuthorizedRealDispatch：确认 sender 确实被调用；如果没有这行代码，事件可能只在返回值里伪造。
        self.assertEqual(sender.send_count, 1)  # 新增代码+Phase94AuthorizedRealDispatch：检查 sender 调用次数；如果没有这行代码，桥接副作用不可见。
        # 新增代码+Phase94AuthorizedRealDispatch：确认测试 sender 不代表真实物理派发；如果没有这行代码，用户会误以为单测真的控制了桌面。
        self.assertFalse(result["real_dispatch_performed"])  # 新增代码+Phase94AuthorizedRealDispatch：断言没有物理派发；如果没有这行代码，安全叙述会含混。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段结束，本测试到此完成低层 sender 桥接验证；如果没有这个边界说明，初学者不容易看出测试范围。

    # 新增代码+Phase94AuthorizedRealDispatch：函数段开始，本测试验证默认关闭时即使已授权也不会发送事件；如果没有这段测试，默认安全值可能被后续改坏。
    def test_default_disabled_path_sends_zero_low_level_events(self):  # 新增代码+Phase94AuthorizedRealDispatch：定义默认关闭测试；如果没有这行代码，安全默认值没有单独保护。
        # 新增代码+Phase94AuthorizedRealDispatch：创建临时目录隔离状态；如果没有这行代码，测试会污染真实授权文件。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase94AuthorizedRealDispatch：使用上下文自动清理；如果没有这行代码，测试文件会残留。
            # 新增代码+Phase94AuthorizedRealDispatch：创建记录型 sender；如果没有这行代码，无法确认没有调用 sender。
            sender = Phase94RecordingLowLevelSender()  # 新增代码+Phase94AuthorizedRealDispatch：准备安全 sender；如果没有这行代码，默认关闭没有观测点。
            # 新增代码+Phase94AuthorizedRealDispatch：创建 runtime；如果没有这行代码，无法组合授权与默认关闭。
            runtime = WindowsAuthorizedRealDispatchCandidate(base_dir=Path(temporary_directory), low_level_sender=sender)  # 新增代码+Phase94AuthorizedRealDispatch：注入测试依赖；如果没有这行代码，状态不可隔离。
            # 新增代码+Phase94AuthorizedRealDispatch：构造普通窗口；如果没有这行代码，授权没有目标。
            window = runtime.contract_window()  # 新增代码+Phase94AuthorizedRealDispatch：读取合同窗口；如果没有这行代码，目标字段可能漂移。
            # 新增代码+Phase94AuthorizedRealDispatch：写入授权但不打开真实派发开关；如果没有这行代码，测试无法证明“已授权也默认不发”。
            runtime.authorize_window(window, session_id="phase94-disabled", action_scope=["click"])  # 新增代码+Phase94AuthorizedRealDispatch：授权 click；如果没有这行代码，拒绝原因会变成未授权而不是默认关闭。
            # 新增代码+Phase94AuthorizedRealDispatch：执行默认关闭路径；如果没有这行代码，后续无法检查零事件。
            result = runtime.dispatch(window, "click", {"x": 320, "y": 240}, session_id="phase94-disabled", enable_real_dispatch=False)  # 新增代码+Phase94AuthorizedRealDispatch：显式保持关闭；如果没有这行代码，测试语义不清。
        # 新增代码+Phase94AuthorizedRealDispatch：确认默认关闭决策明确；如果没有这行代码，用户看不懂为什么没有执行。
        self.assertEqual(result["decision"], "real_dispatch_disabled_by_default")  # 新增代码+Phase94AuthorizedRealDispatch：检查默认关闭原因；如果没有这行代码，失败原因可能漂移。
        # 新增代码+Phase94AuthorizedRealDispatch：确认没有低层事件；如果没有这行代码，默认关闭仍可能产生副作用。
        self.assertEqual(result["low_level_event_count"], 0)  # 新增代码+Phase94AuthorizedRealDispatch：断言零事件；如果没有这行代码，安全默认值不可量化。
        # 新增代码+Phase94AuthorizedRealDispatch：确认 sender 没有被调用；如果没有这行代码，零事件可能只是结果字段伪造。
        self.assertEqual(sender.send_count, 0)  # 新增代码+Phase94AuthorizedRealDispatch：检查 sender 调用次数；如果没有这行代码，默认关闭副作用无法发现。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段结束，本测试到此完成默认关闭验证；如果没有这个边界说明，初学者不容易看出测试范围。

    # 新增代码+Phase94AuthorizedRealDispatch：函数段开始，本测试验证 CLI 行包含真实终端可匹配 token 且报告不含明文；如果没有这段测试，Rule17 场景容易漂移。
    def test_cli_line_contains_phase94_tokens_and_report_hides_text(self):  # 新增代码+Phase94AuthorizedRealDispatch：定义 CLI 与脱敏测试；如果没有这行代码，验收输出没有回归保护。
        # 新增代码+Phase94AuthorizedRealDispatch：创建临时目录隔离合同；如果没有这行代码，测试会污染真实报告目录。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase94AuthorizedRealDispatch：使用自动清理目录；如果没有这行代码，证据文件会残留。
            # 新增代码+Phase94AuthorizedRealDispatch：运行总合同；如果没有这行代码，CLI 行没有输入报告。
            report = run_phase94_authorized_real_dispatch_candidate_contract(base_dir=Path(temporary_directory))  # 新增代码+Phase94AuthorizedRealDispatch：生成报告；如果没有这行代码，token 断言没有事实源。
        # 新增代码+Phase94AuthorizedRealDispatch：生成 CLI 单行文本；如果没有这行代码，无法检查真实终端输出。
        line = phase94_cli_line(report)  # 新增代码+Phase94AuthorizedRealDispatch：格式化 token 行；如果没有这行代码，验收场景要解析 JSON。
        # 新增代码+Phase94AuthorizedRealDispatch：序列化报告做明文泄露扫描；如果没有这行代码，嵌套字段泄露可能漏检。
        serialized = json.dumps(report, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase94AuthorizedRealDispatch：转成字符串；如果没有这行代码，assertNotIn 无法覆盖整个报告。
        # 新增代码+Phase94AuthorizedRealDispatch：检查 ready marker；如果没有这行代码，真实终端无法稳定识别阶段。
        self.assertIn("PHASE94_AUTHORIZED_REAL_DISPATCH_READY", line)  # 新增代码+Phase94AuthorizedRealDispatch：断言 ready token；如果没有这行代码，输出漂移不会被发现。
        # 新增代码+Phase94AuthorizedRealDispatch：检查 OK token；如果没有这行代码，验收脚本无法确认成功。
        self.assertIn("PHASE94_AUTHORIZED_REAL_DISPATCH_OK", line)  # 新增代码+Phase94AuthorizedRealDispatch：断言 OK token；如果没有这行代码，成功标识缺少保护。
        # 新增代码+Phase94AuthorizedRealDispatch：检查低层候选 token；如果没有这行代码，Phase94 可能没有真正推进主路径。
        self.assertIn("authorized_low_level_dispatch_reaches_sender=true", line)  # 新增代码+Phase94AuthorizedRealDispatch：断言低层 sender token；如果没有这行代码，候选派发不可见。
        # 新增代码+Phase94AuthorizedRealDispatch：检查默认关闭 token；如果没有这行代码，用户可能误会普通运行会真实控制桌面。
        self.assertIn("real_dispatch_default_disabled=true", line)  # 新增代码+Phase94AuthorizedRealDispatch：断言默认关闭 token；如果没有这行代码，安全默认值不透明。
        # 新增代码+Phase94AuthorizedRealDispatch：检查未扩展无控制动作 token；如果没有这行代码，安全边界可能被误读。
        self.assertIn("uncontrolled_actions_expanded=false", line)  # 新增代码+Phase94AuthorizedRealDispatch：断言未扩展 token；如果没有这行代码，能力边界不清楚。
        # 新增代码+Phase94AuthorizedRealDispatch：确认测试密文没有进入报告；如果没有这行代码，输入文本可能长期留在验收 artifact。
        self.assertNotIn("phase94-secret-text", serialized)  # 新增代码+Phase94AuthorizedRealDispatch：断言明文缺失；如果没有这行代码，隐私泄露不会自动失败。
    # 新增代码+Phase94AuthorizedRealDispatch：函数段结束，本测试到此完成 CLI 与脱敏验证；如果没有这个边界说明，初学者不容易看出测试范围。
# 新增代码+Phase94AuthorizedRealDispatch：类段结束，Phase94 测试类到此结束；如果没有这个边界说明，初学者不容易看出测试类范围。


# 新增代码+Phase94AuthorizedRealDispatch：文件入口段开始，允许直接运行本测试文件；如果没有这段代码，人工排查时必须记完整 unittest 命令。
if __name__ == "__main__":  # 新增代码+Phase94AuthorizedRealDispatch：判断是否直接执行；如果没有这行代码，python 文件方式不会启动测试。
    # 新增代码+Phase94AuthorizedRealDispatch：启动 unittest 主程序；如果没有这行代码，直接运行文件没有任何测试输出。
    unittest.main()  # 新增代码+Phase94AuthorizedRealDispatch：运行当前文件测试；如果没有这行代码，人工红绿灯循环不方便。
# 新增代码+Phase94AuthorizedRealDispatch：文件入口段结束，直接运行路径到此结束；如果没有这个边界说明，初学者不容易看出入口范围。
