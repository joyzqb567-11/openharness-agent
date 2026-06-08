# 新增代码+Phase95ControlledPhysicalSendInput：导入 json 用来扫描合同报告是否泄露原始文本；如果没有这行代码，隐私回归只能靠人工看日志。
import json  # 新增代码+Phase95ControlledPhysicalSendInput：把嵌套报告序列化成字符串；如果没有这行代码，深层字段里的明文泄露可能漏检。
# 新增代码+Phase95ControlledPhysicalSendInput：导入 tempfile 用来给每次合同运行创建隔离目录；如果没有这行代码，测试会污染真实 agent_memory 或上一次验收结果。
import tempfile  # 新增代码+Phase95ControlledPhysicalSendInput：提供自动清理的临时目录；如果没有这行代码，多次运行测试时证据文件可能互相覆盖。
# 新增代码+Phase95ControlledPhysicalSendInput：导入 unittest 沿用项目现有测试框架；如果没有这行代码，python -m unittest 无法发现和执行本文件。
import unittest  # 新增代码+Phase95ControlledPhysicalSendInput：提供 TestCase 和断言方法；如果没有这行代码，测试无法表达红绿灯条件。
# 新增代码+Phase95ControlledPhysicalSendInput：导入 Path 让 Windows 路径处理更稳定；如果没有这行代码，临时目录传参容易退化成脆弱字符串拼接。
from pathlib import Path  # 新增代码+Phase95ControlledPhysicalSendInput：把临时目录转为路径对象；如果没有这行代码，合同写报告时路径边界不够清晰。
# 新增代码+Phase95ControlledPhysicalSendInput：导入 Phase95 待实现 API，这是 TDD 红灯入口；如果没有这行代码，测试不会逼出新的受控物理 sender 模块。
from learning_agent.computer_use.controlled_physical_sendinput import (  # 新增代码+Phase95ControlledPhysicalSendInput：从新模块导入公开合同；如果没有这行代码，后续 agent 只能硬编码内部实现。
    PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_MARKER,  # 新增代码+Phase95ControlledPhysicalSendInput：导入 ready marker；如果没有这行代码，真实终端验收 token 无法被测试固定。
    PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_OK_TOKEN,  # 新增代码+Phase95ControlledPhysicalSendInput：导入 OK token；如果没有这行代码，成功输出标识可能漂移。
    PHASE95_REAL_SENDINPUT_ENV,  # 新增代码+Phase95ControlledPhysicalSendInput：导入真实 SendInput 环境门；如果没有这行代码，显式启用入口无法被回归保护。
    Phase95RecordingSendInputBackend,  # 新增代码+Phase95ControlledPhysicalSendInput：导入安全记录后端；如果没有这行代码，单元测试可能误触真实鼠标键盘。
    WindowsControlledPhysicalSendInputSender,  # 新增代码+Phase95ControlledPhysicalSendInput：导入受控物理 sender 主体；如果没有这行代码，Phase95 没有可测试对象。
    phase95_cli_line,  # 新增代码+Phase95ControlledPhysicalSendInput：导入 CLI token 格式化函数；如果没有这行代码，真实终端输出格式无法被锁定。
    run_phase95_controlled_physical_sendinput_contract,  # 新增代码+Phase95ControlledPhysicalSendInput：导入总合同入口；如果没有这行代码，测试和验收没有统一事实源。
)  # 新增代码+Phase95ControlledPhysicalSendInput：结束导入列表；如果没有这行代码，Python 语法不完整。

# 新增代码+Phase95ControlledPhysicalSendInput：类段开始，本测试类验证 Phase95 是否把 Phase94 候选 sender 推进到受控物理 SendInput 适配层；如果没有这段测试，功能可能只停留在口头设计。
class WindowsComputerUseControlledPhysicalSendInputPhase95Tests(unittest.TestCase):  # 新增代码+Phase95ControlledPhysicalSendInput：定义 Phase95 测试类；如果没有这行代码，unittest 不会组织这些回归用例。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，验证总合同覆盖默认关闭、注入后端、拦截和脱敏；如果没有这段测试，Phase95 可能只验证 happy path。
    def test_phase95_contract_proves_controlled_physical_sender_bridge(self):  # 新增代码+Phase95ControlledPhysicalSendInput：定义总合同测试；如果没有这行代码，核心成功标准没有自动保护。
        # 新增代码+Phase95ControlledPhysicalSendInput：创建隔离目录承载合同报告；如果没有这行代码，测试会把证据写进真实运行目录。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase95ControlledPhysicalSendInput：使用上下文自动清理临时目录；如果没有这行代码，测试运行后会残留文件。
            # 新增代码+Phase95ControlledPhysicalSendInput：运行 Phase95 总合同；如果没有这行代码，后续断言没有事实来源。
            report = run_phase95_controlled_physical_sendinput_contract(base_dir=Path(temporary_directory))  # 新增代码+Phase95ControlledPhysicalSendInput：注入临时目录运行合同；如果没有这行代码，报告落点不可控。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认合同整体通过；如果没有这行代码，局部字段正确也可能掩盖整体失败。
        self.assertTrue(report["passed"])  # 新增代码+Phase95ControlledPhysicalSendInput：断言 passed 为真；如果没有这行代码，失败实现可能被误当作完成。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认 ready marker 稳定；如果没有这行代码，真实终端验收脚本可能等不到固定锚点。
        self.assertEqual(report["marker"], PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_MARKER)  # 新增代码+Phase95ControlledPhysicalSendInput：检查 marker；如果没有这行代码，阶段标识漂移不会被发现。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认 OK token 稳定；如果没有这行代码，成功输出可能被普通日志混淆。
        self.assertEqual(report["ok_token"], PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_OK_TOKEN)  # 新增代码+Phase95ControlledPhysicalSendInput：检查 OK token；如果没有这行代码，验收成功标识缺少保护。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认 Phase94 的授权候选链路被复用；如果没有这行代码，新 sender 可能绕开授权和目标复核。
        self.assertTrue(report["phase94_authorized_candidate_reused"])  # 新增代码+Phase95ControlledPhysicalSendInput：断言复用 Phase94；如果没有这行代码，架构对齐缺口不可见。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认受控物理 sender 已就绪；如果没有这行代码，模块可能只产出静态文案。
        self.assertTrue(report["controlled_physical_sender_ready"])  # 新增代码+Phase95ControlledPhysicalSendInput：断言 sender ready；如果没有这行代码，核心能力没有验收点。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认默认关闭时没有后端调用；如果没有这行代码，普通运行可能误碰用户桌面。
        self.assertTrue(report["default_off_zero_physical_events"])  # 新增代码+Phase95ControlledPhysicalSendInput：断言默认零物理事件；如果没有这行代码，安全默认值会失去保护。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认显式启用并注入后端时事件能到达后端；如果没有这行代码，Phase95 仍可能只是 recording-only。
        self.assertTrue(report["enabled_backend_receives_low_level_events"])  # 新增代码+Phase95ControlledPhysicalSendInput：断言注入后端收到低层事件；如果没有这行代码，物理 sender 桥接能力不成立。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认危险目标不会发送事件；如果没有这行代码，终端或认证窗口可能被误操作。
        self.assertTrue(report["unsafe_target_zero_physical_events"])  # 新增代码+Phase95ControlledPhysicalSendInput：断言危险目标零事件；如果没有这行代码，高风险窗口拦截没有自动保护。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认未知事件类型不会发送；如果没有这行代码，未来模型输出奇怪事件时可能被误放行。
        self.assertTrue(report["unsupported_event_zero_physical_events"])  # 新增代码+Phase95ControlledPhysicalSendInput：断言未知事件零发送；如果没有这行代码，事件白名单会变松。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认报告不包含原始输入文本；如果没有这行代码，用户 prompt 或输入内容可能进入验收 artifact。
        self.assertTrue(report["raw_text_hidden"])  # 新增代码+Phase95ControlledPhysicalSendInput：断言明文隐藏；如果没有这行代码，隐私门禁不可验证。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认自动化合同没有触碰真实桌面；如果没有这行代码，测试可能和真实控制混淆。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+Phase95ControlledPhysicalSendInput：断言没有真实桌面副作用；如果没有这行代码，安全叙述会含混。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认没有扩张无授权动作面；如果没有这行代码，用户可能误以为已无限制控制所有应用。
        self.assertFalse(report["uncontrolled_actions_expanded"])  # 新增代码+Phase95ControlledPhysicalSendInput：断言没有无控制扩张；如果没有这行代码，能力边界不清晰。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认环境门名称稳定；如果没有这行代码，生产启用方式会漂移。
        self.assertEqual(report["real_sendinput_env_gate"], PHASE95_REAL_SENDINPUT_ENV)  # 新增代码+Phase95ControlledPhysicalSendInput：检查 env gate；如果没有这行代码，显式开关不可审计。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，总合同测试到此结束；如果没有这个边界说明，初学者不容易看出测试范围。

    # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，验证显式启用和注入后端可以接住 Phase94 低层事件；如果没有这段测试，sender 可能永远不调用后端。
    def test_enabled_sender_calls_injected_backend_without_touching_real_desktop(self):  # 新增代码+Phase95ControlledPhysicalSendInput：定义显式启用测试；如果没有这行代码，正向桥接能力没有单独保护。
        # 新增代码+Phase95ControlledPhysicalSendInput：创建安全记录后端并让它模拟“物理后端已接收”；如果没有这行代码，测试可能依赖真实 SendInput。
        backend = Phase95RecordingSendInputBackend(physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：准备 fake 后端；如果没有这行代码，后续无法统计调用次数。
        # 新增代码+Phase95ControlledPhysicalSendInput：创建 Windows 平台下的受控 sender；如果没有这行代码，send_low_level 没有被测主体。
        sender = WindowsControlledPhysicalSendInputSender(low_level_backend=backend, platform="win32")  # 新增代码+Phase95ControlledPhysicalSendInput：注入 fake 后端；如果没有这行代码，测试可能误触默认实现。
        # 新增代码+Phase95ControlledPhysicalSendInput：构造合同安全窗口；如果没有这行代码，目标安全判断没有输入。
        window = sender.contract_window()  # 新增代码+Phase95ControlledPhysicalSendInput：获得安全目标；如果没有这行代码，事件缺少 target 身份。
        # 新增代码+Phase95ControlledPhysicalSendInput：构造 click 低层事件；如果没有这行代码，后端没有事件可接收。
        events = sender.contract_events(window, "click", {"x": 320, "y": 240})  # 新增代码+Phase95ControlledPhysicalSendInput：生成 Phase94 兼容事件；如果没有这行代码，测试不覆盖真实 sender 输入形状。
        # 新增代码+Phase95ControlledPhysicalSendInput：显式启用受控物理派发；如果没有这行代码，默认关闭会正确返回零事件而不能证明桥接。
        result = sender.send_low_level(events, enable_physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：调用 sender；如果没有这行代码，后端调用次数没有事实来源。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认 sender 返回成功；如果没有这行代码，失败路径也可能被误认为通过。
        self.assertTrue(result["ok"])  # 新增代码+Phase95ControlledPhysicalSendInput：断言发送成功；如果没有这行代码，后端调用失败不会暴露。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认后端恰好被调用一次；如果没有这行代码，重复发送或未发送都可能漏检。
        self.assertEqual(backend.send_count, 1)  # 新增代码+Phase95ControlledPhysicalSendInput：检查后端调用次数；如果没有这行代码，桥接副作用不可见。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认低层事件数量大于零；如果没有这行代码，空事件也可能被标记为成功。
        self.assertGreater(result["low_level_event_count"], 0)  # 新增代码+Phase95ControlledPhysicalSendInput：断言事件已到达；如果没有这行代码，sender 可能空跑。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认报告表达后端已接收；如果没有这行代码，调用状态可能只在 fake 对象内部。
        self.assertTrue(result["backend_dispatch_performed"])  # 新增代码+Phase95ControlledPhysicalSendInput：断言后端派发标记；如果没有这行代码，结果不方便上层审计。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认自动化测试没有真实桌面副作用；如果没有这行代码，fake 后端和真实控制可能被混淆。
        self.assertFalse(result["real_desktop_touched"])  # 新增代码+Phase95ControlledPhysicalSendInput：断言未触碰真实桌面；如果没有这行代码，测试结论会过度承诺。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，显式启用桥接测试到此结束；如果没有这个边界说明，初学者不容易看出测试范围。

    # 新增代码+ControlledPhysicalPauseBridge：函数段开始，验证通用执行 loop 常见的 pause 等待事件不会被 Phase95 sender 错误拒绝；如果没有这段测试，成熟矩阵可能再次卡在“后端没有收到事件”的假断层。
    def test_sender_allows_pause_events_from_universal_loop_to_reach_injected_backend(self):  # 新增代码+ControlledPhysicalPauseBridge：定义 pause 桥接回归测试；如果没有这行代码，set_foreground 后的稳定等待事件可能再次被白名单误杀。
        # 新增代码+ControlledPhysicalPauseBridge：创建安全记录后端用于证明最后一跳被调用；如果没有这行代码，测试无法区分 sender 通过和真实鼠标键盘副作用。
        backend = Phase95RecordingSendInputBackend(physical_dispatch=True)  # 新增代码+ControlledPhysicalPauseBridge：使用 fake 后端模拟物理接收；如果没有这行代码，单元测试可能触碰用户桌面。
        # 新增代码+ControlledPhysicalPauseBridge：创建 Windows 平台下的受控 sender；如果没有这行代码，pause 白名单没有被测主体。
        sender = WindowsControlledPhysicalSendInputSender(low_level_backend=backend, platform="win32")  # 新增代码+ControlledPhysicalPauseBridge：把 fake 后端注入 sender；如果没有这行代码，测试可能走默认真实后端。
        # 新增代码+ControlledPhysicalPauseBridge：构造合同安全窗口作为所有事件的目标；如果没有这行代码，目标安全检查会因为缺身份而拒绝。
        window = sender.contract_window()  # 新增代码+ControlledPhysicalPauseBridge：读取稳定安全窗口；如果没有这行代码，事件无法带上目标边界。
        # 新增代码+ControlledPhysicalPauseBridge：构造通用 loop 常见的聚焦、等待、移动序列；如果没有这行代码，测试不会复现 maturity 矩阵里的真实事件形状。
        events = [{"kind": "set_foreground", "hwnd": window["hwnd"], "target": window}, {"kind": "pause", "seconds": 0.01, "target": window}, {"kind": "mouse_move", "x": 320, "y": 240, "target": window}]  # 新增代码+ControlledPhysicalPauseBridge：混合 set_foreground、pause 和 mouse_move；如果没有这行代码，pause 事件不会参与 sender 验证。
        # 新增代码+ControlledPhysicalPauseBridge：显式启用受控物理派发但仍使用 fake 后端；如果没有这行代码，默认关闭会正确拒绝而无法证明 pause 是否被支持。
        result = sender.send_low_level(events, enable_physical_dispatch=True)  # 新增代码+ControlledPhysicalPauseBridge：调用 sender 发送混合低层事件；如果没有这行代码，后续断言没有事实来源。
        # 新增代码+ControlledPhysicalPauseBridge：确认 sender 没有把 pause 当成未知事件拒绝；如果没有这行代码，矩阵旧失败会重新出现。
        self.assertTrue(result["ok"])  # 新增代码+ControlledPhysicalPauseBridge：断言混合事件发送成功；如果没有这行代码，unsupported pause 回归不会失败。
        # 新增代码+ControlledPhysicalPauseBridge：确认后端确实被调用一次；如果没有这行代码，sender 可能只是在表面返回成功但没有桥到最后一跳。
        self.assertEqual(backend.send_count, 1)  # 新增代码+ControlledPhysicalPauseBridge：检查 fake 后端调用次数；如果没有这行代码，受控物理接线不可验证。
        # 新增代码+ControlledPhysicalPauseBridge：确认 pause 保留在 sender 审计事件类型里；如果没有这行代码，排查时看不到等待节奏是否经过主链路。
        self.assertIn("pause", result["event_types"])  # 新增代码+ControlledPhysicalPauseBridge：断言返回摘要包含 pause；如果没有这行代码，事件摘要可能丢失关键等待动作。
        # 新增代码+ControlledPhysicalPauseBridge：确认 fake 后端也收到 pause 类型；如果没有这行代码，最后一跳可能仍然没有覆盖通用 loop 的事件形状。
        self.assertIn("pause", [event.get("type") for event in backend.events])  # 新增代码+ControlledPhysicalPauseBridge：检查后端记录里的 type 字段；如果没有这行代码，Phase95 kind 到后端 type 的转换可能漏掉 pause。
        # 新增代码+ControlledPhysicalPauseBridge：确认测试过程没有触碰真实桌面；如果没有这行代码，用户会误把 fake 桥接验收当成真实鼠标键盘操作。
        self.assertFalse(result["real_desktop_touched"])  # 新增代码+ControlledPhysicalPauseBridge：断言无真实桌面副作用；如果没有这行代码，安全边界不可见。
    # 新增代码+ControlledPhysicalPauseBridge：函数段结束，pause 桥接测试到此结束；如果没有这个边界说明，初学者不容易看出测试范围。

    # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，验证默认关闭时即使事件有效也不调用后端；如果没有这段测试，安全默认值可能回退。
    def test_default_off_never_calls_backend_even_with_valid_events(self):  # 新增代码+Phase95ControlledPhysicalSendInput：定义默认关闭测试；如果没有这行代码，普通运行不碰桌面没有单独保障。
        # 新增代码+Phase95ControlledPhysicalSendInput：创建记录后端；如果没有这行代码，无法证明后端调用次数为零。
        backend = Phase95RecordingSendInputBackend(physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：准备 fake 后端；如果没有这行代码，默认关闭是否绕过后端不可见。
        # 新增代码+Phase95ControlledPhysicalSendInput：创建受控 sender；如果没有这行代码，默认关闭逻辑没有被测对象。
        sender = WindowsControlledPhysicalSendInputSender(low_level_backend=backend, platform="win32")  # 新增代码+Phase95ControlledPhysicalSendInput：注入 fake 后端；如果没有这行代码，测试不可控。
        # 新增代码+Phase95ControlledPhysicalSendInput：构造安全窗口；如果没有这行代码，无法生成有效低层事件。
        window = sender.contract_window()  # 新增代码+Phase95ControlledPhysicalSendInput：获得合同目标；如果没有这行代码，默认关闭测试可能变成目标失败测试。
        # 新增代码+Phase95ControlledPhysicalSendInput：构造有效 click 事件；如果没有这行代码，零发送可能只是因为事件为空。
        events = sender.contract_events(window, "click", {"x": 320, "y": 240})  # 新增代码+Phase95ControlledPhysicalSendInput：生成有效事件；如果没有这行代码，测试语义不完整。
        # 新增代码+Phase95ControlledPhysicalSendInput：在默认关闭下请求发送；如果没有这行代码，无法证明关闭门生效。
        result = sender.send_low_level(events, enable_physical_dispatch=False)  # 新增代码+Phase95ControlledPhysicalSendInput：执行默认关闭路径；如果没有这行代码，后续断言没有来源。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认决策原因清楚；如果没有这行代码，用户不知道为什么没有动作。
        self.assertEqual(result["decision"], "real_sendinput_disabled_by_default")  # 新增代码+Phase95ControlledPhysicalSendInput：检查默认关闭原因；如果没有这行代码，失败解释可能漂移。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认没有事件发送给后端；如果没有这行代码，默认关闭可能仍有副作用。
        self.assertEqual(result["low_level_event_count"], 0)  # 新增代码+Phase95ControlledPhysicalSendInput：断言零事件；如果没有这行代码，空跑和真实发送无法区分。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认后端没有被调用；如果没有这行代码，零事件字段可能被伪造。
        self.assertEqual(backend.send_count, 0)  # 新增代码+Phase95ControlledPhysicalSendInput：检查调用次数；如果没有这行代码，默认关闭的副作用不可见。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，默认关闭测试到此结束；如果没有这个边界说明，初学者不容易看出测试范围。

    # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，验证危险目标、未知事件和原始文本都会被拦截；如果没有这段测试，sender 白名单可能失效。
    def test_sender_rejects_unsafe_target_unknown_event_and_raw_text(self):  # 新增代码+Phase95ControlledPhysicalSendInput：定义拒绝路径测试；如果没有这行代码，高风险分支没有回归保护。
        # 新增代码+Phase95ControlledPhysicalSendInput：创建记录后端；如果没有这行代码，无法确认拒绝路径没有触发后端。
        backend = Phase95RecordingSendInputBackend(physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：准备 fake 后端；如果没有这行代码，拒绝副作用不可见。
        # 新增代码+Phase95ControlledPhysicalSendInput：创建受控 sender；如果没有这行代码，拒绝逻辑没有被测对象。
        sender = WindowsControlledPhysicalSendInputSender(low_level_backend=backend, platform="win32")  # 新增代码+Phase95ControlledPhysicalSendInput：注入 fake 后端；如果没有这行代码，测试不稳定。
        # 新增代码+Phase95ControlledPhysicalSendInput：构造危险终端目标事件；如果没有这行代码，危险窗口拦截没有样本。
        unsafe_event = {"type": "mouse_move", "x": 1, "y": 1, "target": {"app_id": "powershell.exe", "window_id": "hwnd:9501", "title_sha256_16": "unsafe"}}  # 新增代码+Phase95ControlledPhysicalSendInput：模拟 PowerShell 目标；如果没有这行代码，终端窗口风险不会被覆盖。
        # 新增代码+Phase95ControlledPhysicalSendInput：尝试发送危险目标事件；如果没有这行代码，危险目标拒绝没有结果。
        unsafe_result = sender.send_low_level([unsafe_event], enable_physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：执行危险目标路径；如果没有这行代码，后续断言无事实来源。
        # 新增代码+Phase95ControlledPhysicalSendInput：构造未知事件类型；如果没有这行代码，事件白名单没有负样本。
        unknown_event = {"type": "launch_process", "target": sender.contract_window()}  # 新增代码+Phase95ControlledPhysicalSendInput：模拟不支持事件；如果没有这行代码，未知命令可能被误放行。
        # 新增代码+Phase95ControlledPhysicalSendInput：尝试发送未知事件；如果没有这行代码，白名单拒绝没有结果。
        unknown_result = sender.send_low_level([unknown_event], enable_physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：执行未知事件路径；如果没有这行代码，后续断言无来源。
        # 新增代码+Phase95ControlledPhysicalSendInput：构造包含原始 text 的事件；如果没有这行代码，明文拒绝没有样本。
        raw_text_event = {"type": "keyboard_text", "text": "phase95-secret-text", "target": sender.contract_window()}  # 新增代码+Phase95ControlledPhysicalSendInput：模拟泄露明文的坏事件；如果没有这行代码，隐私门禁无法证明。
        # 新增代码+Phase95ControlledPhysicalSendInput：尝试发送明文事件；如果没有这行代码，明文拒绝没有结果。
        raw_text_result = sender.send_low_level([raw_text_event], enable_physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：执行明文事件路径；如果没有这行代码，后续断言无来源。
        # 新增代码+Phase95ControlledPhysicalSendInput：序列化三个结果扫描泄露；如果没有这行代码，嵌套字段里的 secret 可能漏检。
        serialized = json.dumps({"unsafe": unsafe_result, "unknown": unknown_result, "raw": raw_text_result}, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase95ControlledPhysicalSendInput：生成可扫描文本；如果没有这行代码，assertNotIn 无法覆盖完整结果。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认危险目标被拒绝；如果没有这行代码，终端窗口可能被误操作。
        self.assertEqual(unsafe_result["decision"], "unsafe_target_rejected")  # 新增代码+Phase95ControlledPhysicalSendInput：检查危险目标决策；如果没有这行代码，拒绝原因可能漂移。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认未知事件被拒绝；如果没有这行代码，事件白名单不受保护。
        self.assertEqual(unknown_result["decision"], "unsupported_low_level_event_rejected")  # 新增代码+Phase95ControlledPhysicalSendInput：检查未知事件决策；如果没有这行代码，未知命令可能被误放行。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认明文事件被拒绝；如果没有这行代码，隐私漏洞可能进入底层 sender。
        self.assertEqual(raw_text_result["decision"], "raw_text_event_rejected")  # 新增代码+Phase95ControlledPhysicalSendInput：检查明文拒绝决策；如果没有这行代码，文本脱敏回归不会被发现。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认三条拒绝路径都没有事件发送；如果没有这行代码，拒绝可能仍有副作用。
        self.assertEqual(backend.send_count, 0)  # 新增代码+Phase95ControlledPhysicalSendInput：断言后端零调用；如果没有这行代码，拒绝路径副作用不可见。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认明文没有进入返回结果；如果没有这行代码，隐私泄露不会自动失败。
        self.assertNotIn("phase95-secret-text", serialized)  # 新增代码+Phase95ControlledPhysicalSendInput：断言 secret 不在结果里；如果没有这行代码，报告可能长期保存用户输入。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，拒绝路径测试到此结束；如果没有这个边界说明，初学者不容易看出测试范围。

    # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，验证 CLI 单行包含真实终端验收需要的固定 token；如果没有这段测试，Rule17 场景容易漂移。
    def test_cli_line_contains_phase95_tokens_and_hides_text(self):  # 新增代码+Phase95ControlledPhysicalSendInput：定义 CLI 与脱敏测试；如果没有这行代码，终端输出没有回归保护。
        # 新增代码+Phase95ControlledPhysicalSendInput：创建隔离目录运行合同；如果没有这行代码，报告可能污染真实运行数据。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase95ControlledPhysicalSendInput：使用自动清理目录；如果没有这行代码，测试后会留下临时文件。
            # 新增代码+Phase95ControlledPhysicalSendInput：运行合同生成报告；如果没有这行代码，CLI 行没有输入数据。
            report = run_phase95_controlled_physical_sendinput_contract(base_dir=Path(temporary_directory))  # 新增代码+Phase95ControlledPhysicalSendInput：把临时目录传给合同；如果没有这行代码，报告路径不可控。
        # 新增代码+Phase95ControlledPhysicalSendInput：生成 CLI 单行；如果没有这行代码，无法检查真实终端输出格式。
        line = phase95_cli_line(report)  # 新增代码+Phase95ControlledPhysicalSendInput：格式化 token 行；如果没有这行代码，验收器需要解析复杂 JSON。
        # 新增代码+Phase95ControlledPhysicalSendInput：序列化报告做泄露扫描；如果没有这行代码，嵌套明文泄露可能漏检。
        serialized = json.dumps(report, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase95ControlledPhysicalSendInput：生成报告字符串；如果没有这行代码，assertNotIn 无法扫描完整报告。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认 ready marker 出现在 CLI 行；如果没有这行代码，真实终端验收找不到阶段锚点。
        self.assertIn("PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_READY", line)  # 新增代码+Phase95ControlledPhysicalSendInput：断言 ready token；如果没有这行代码，输出漂移不会被发现。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认 OK token 出现在 CLI 行；如果没有这行代码，验收脚本无法判定成功。
        self.assertIn("PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_OK", line)  # 新增代码+Phase95ControlledPhysicalSendInput：断言 OK token；如果没有这行代码，成功标识缺少保护。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认注入后端桥接 token 出现；如果没有这行代码，Phase95 核心能力可能从输出里消失。
        self.assertIn("enabled_backend_receives_low_level_events=true", line)  # 新增代码+Phase95ControlledPhysicalSendInput：断言后端接收 token；如果没有这行代码，终端验收不覆盖桥接能力。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认默认关闭 token 出现；如果没有这行代码，用户可能误解普通运行会直接控制桌面。
        self.assertIn("default_off_zero_physical_events=true", line)  # 新增代码+Phase95ControlledPhysicalSendInput：断言默认关闭 token；如果没有这行代码，安全默认值不透明。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认真实桌面未触碰 token 出现；如果没有这行代码，自动化合同可能被误读为真实控制验收。
        self.assertIn("real_desktop_touched=false", line)  # 新增代码+Phase95ControlledPhysicalSendInput：断言未触碰真实桌面 token；如果没有这行代码，结论容易过度承诺。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认没有扩张无授权动作面 token 出现；如果没有这行代码，能力边界不清晰。
        self.assertIn("uncontrolled_actions_expanded=false", line)  # 新增代码+Phase95ControlledPhysicalSendInput：断言未无控扩张 token；如果没有这行代码，安全边界可能被误读。
        # 新增代码+Phase95ControlledPhysicalSendInput：确认合同里的 secret 没有进入报告；如果没有这行代码，明文泄露不会被自动发现。
        self.assertNotIn("phase95-secret-text", serialized)  # 新增代码+Phase95ControlledPhysicalSendInput：断言 secret 不存在；如果没有这行代码，用户输入可能进入 artifact。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，CLI 与脱敏测试到此结束；如果没有这个边界说明，初学者不容易看出测试范围。
# 新增代码+Phase95ControlledPhysicalSendInput：类段结束，Phase95 测试类到此结束；如果没有这个边界说明，初学者不容易看出测试类范围。

# 新增代码+Phase95ControlledPhysicalSendInput：文件入口段开始，允许直接运行本测试文件；如果没有这段代码，人工排查时必须记完整 unittest 命令。
if __name__ == "__main__":  # 新增代码+Phase95ControlledPhysicalSendInput：判断是否直接执行；如果没有这行代码，python 文件方式不会启动测试。
    # 新增代码+Phase95ControlledPhysicalSendInput：启动 unittest 主程序；如果没有这行代码，直接运行文件没有任何测试输出。
    unittest.main()  # 新增代码+Phase95ControlledPhysicalSendInput：运行当前测试文件；如果没有这行代码，手工红绿灯循环不方便。
# 新增代码+Phase95ControlledPhysicalSendInput：文件入口段结束，直接运行路径到此结束；如果没有这个边界说明，初学者不容易看出入口范围。
