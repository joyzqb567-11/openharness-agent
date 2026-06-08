# 新增代码+Phase96ControlledPhysicalLiveSmoke：导入 json 用来检查报告里不会泄露原始输入；如果没有这行代码，隐私回归只能靠人工看日志。
import json  # 新增代码+Phase96ControlledPhysicalLiveSmoke：把嵌套报告序列化成文本；如果没有这行代码，深层字段里的敏感文本可能漏检。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：导入 tempfile 用来创建隔离验收目录；如果没有这行代码，测试会污染真实运行目录。
import tempfile  # 新增代码+Phase96ControlledPhysicalLiveSmoke：提供自动清理的临时目录；如果没有这行代码，多次测试会互相覆盖证据。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：导入 unittest 沿用项目现有测试框架；如果没有这行代码，python -m unittest 无法发现本文件。
import unittest  # 新增代码+Phase96ControlledPhysicalLiveSmoke：提供 TestCase 和断言；如果没有这行代码，红绿灯条件无法自动表达。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：导入 Path 让 Windows 路径处理更稳定；如果没有这行代码，临时目录传参容易退化成脆弱字符串。
from pathlib import Path  # 新增代码+Phase96ControlledPhysicalLiveSmoke：把临时目录转换为路径对象；如果没有这行代码，报告落点边界不够清晰。

# 新增代码+Phase96ControlledPhysicalLiveSmoke：导入 Phase96 待实现 API，这是 TDD 红灯入口；如果没有这段导入，测试不会逼出真实 live smoke 合同模块。
from learning_agent.computer_use.controlled_physical_live_smoke import (  # 新增代码+Phase96ControlledPhysicalLiveSmoke：从新模块导入公开合同；如果没有这行代码，后续 agent 只能硬编码内部路径。
    PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_MARKER,  # 新增代码+Phase96ControlledPhysicalLiveSmoke：导入 ready marker；如果没有这行代码，真实终端验收 token 无法固定。
    PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_OK_TOKEN,  # 新增代码+Phase96ControlledPhysicalLiveSmoke：导入 OK token；如果没有这行代码，成功输出标识可能漂移。
    PHASE96_REAL_SENDINPUT_LIVE_SMOKE_ENV,  # 新增代码+Phase96ControlledPhysicalLiveSmoke：导入真实派发环境门；如果没有这行代码，显式启用方式无法被测试锁定。
    PHASE96_REAL_SENDINPUT_LIVE_SMOKE_REQUEST_ENV,  # 新增代码+Phase96ControlledPhysicalLiveSmoke：导入真实 smoke 请求门；如果没有这行代码，CLI 入口请求方式无法被测试锁定。
    phase96_cli_line,  # 新增代码+Phase96ControlledPhysicalLiveSmoke：导入 CLI token 格式化函数；如果没有这行代码，真实终端输出格式无法回归保护。
    run_phase96_controlled_physical_live_smoke_contract,  # 新增代码+Phase96ControlledPhysicalLiveSmoke：导入总合同入口；如果没有这行代码，测试和验收没有统一事实源。
)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：结束导入列表；如果没有这行代码，Python 语法不完整。

# 新增代码+Phase96ControlledPhysicalLiveSmoke：类段开始，FakeWindowsLowLevelSender 模拟真实 SendInput 后端但不碰桌面；如果没有这个类，单测可能误触真实鼠标键盘。
class FakeWindowsLowLevelSender:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：定义测试后端；如果没有这行代码，Phase96 无法在红绿灯中验证真实后端识别逻辑。
    # 新增代码+Phase96ControlledPhysicalLiveSmoke：声明 fake 后端不需要原始文本；如果没有这行代码，Phase95 会按 raw text 风险拒绝测试事件。
    requires_raw_text = False  # 新增代码+Phase96ControlledPhysicalLiveSmoke：保护测试不传明文；如果没有这行代码，隐私门禁会误判为不安全。

    # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，初始化 fake 后端事件记录；如果没有这段函数，测试无法证明后端是否被调用。
    def __init__(self) -> None:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建后端实例时准备记录列表；如果没有这行代码，事件数量不可审计。
        self.events: list[dict[str, object]] = []  # 新增代码+Phase96ControlledPhysicalLiveSmoke：保存收到的低层事件副本；如果没有这行代码，Phase96 桥接是否发生不可见。
    # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，FakeWindowsLowLevelSender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，模拟真实 Windows low-level sender 返回形状；如果没有这段函数，Phase95 无法被测试为真实 backend 路径。
    def send_low_level(self, events: list[dict[str, object]]) -> dict[str, object]:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：接收低层事件；如果没有这行代码，sender 调用会失败。
        self.events.extend(dict(event) for event in events)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：复制事件到记录中；如果没有这行代码，测试不能确认事件真的到达后端。
        return {"ok": bool(events), "low_level_event_count": len(events), "sender": "windows_sendinput_low_level", "raw_text_included": False}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回真实后端标识但不声明 real_desktop_touched；如果没有这行代码，Phase96 不能逼出 Phase95 的真实后端推断缺口。
    # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，FakeWindowsLowLevelSender.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出 fake 派发范围。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：类段结束，FakeWindowsLowLevelSender 到此结束；如果没有这个边界说明，初学者不容易看出测试替身范围。

# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，返回假的 Phase58 键盘真实 smoke 成功报告；如果没有这段函数，Phase96 无法在单测中证明键盘 guard 被复用。
def fake_phase58_keyboard_smoke() -> dict[str, object]:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：定义可注入 runner；如果没有这行代码，单测会依赖真实 UIA 和真实键盘。
    return {"real_smoke": True, "safe_window_only": True, "target_guard": True, "before_after": True, "after_changed": True, "low_level_event_count": 2, "raw_text_hidden": True}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回脱敏成功摘要；如果没有这行代码，合同无法汇总键盘真实路径证据。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，fake_phase58_keyboard_smoke 到此结束；如果没有这个边界说明，初学者不容易看出 fake keyboard smoke 范围。

# 新增代码+Phase96ControlledPhysicalLiveSmoke：测试类段开始，验证 Phase96 受控物理 live smoke 合同；如果没有这个类，Phase96 可能只有实现没有回归保护。
class WindowsComputerUseControlledPhysicalLiveSmokePhase96Tests(unittest.TestCase):  # 新增代码+Phase96ControlledPhysicalLiveSmoke：定义 Phase96 测试类；如果没有这行代码，unittest 不会组织这些用例。
    # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，验证默认关闭时不触碰真实桌面；如果没有这段测试，普通运行可能误开物理派发。
    def test_phase96_default_contract_stays_safe_and_does_not_touch_desktop(self) -> None:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：定义默认安全合同测试；如果没有这行代码，默认关闭门禁没有自动保护。
        backend = FakeWindowsLowLevelSender()  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建 fake 后端；如果没有这行代码，无法确认默认关闭时后端没有被调用。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建临时目录；如果没有这行代码，报告会写进真实运行目录。
            report = run_phase96_controlled_physical_live_smoke_contract(base_dir=Path(temporary_directory), real_smoke=False, low_level_backend=backend, phase58_smoke_runner=fake_phase58_keyboard_smoke, platform="win32")  # 新增代码+Phase96ControlledPhysicalLiveSmoke：运行默认关闭合同；如果没有这行代码，断言没有事实来源。
        self.assertTrue(report["passed"])  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认默认合同通过；如果没有这行代码，失败实现可能被当成可用。
        self.assertTrue(report["default_off_zero_physical_events"])  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认默认关闭零事件；如果没有这行代码，安全默认值可能回退。
        self.assertTrue(report["unsafe_target_zero_physical_events"])  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认危险目标零事件；如果没有这行代码，终端或认证窗口风险可能漏过。
        self.assertFalse(report["real_smoke_executed"])  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认默认不跑真实 smoke；如果没有这行代码，单测可能触碰桌面。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认没有真实桌面副作用；如果没有这行代码，报告可能过度承诺。
        self.assertEqual(backend.events, [])  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认 fake 后端未收到事件；如果没有这行代码，默认关闭可能只是假装关闭。
    # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，默认安全合同测试到此结束；如果没有这个边界说明，初学者不容易看出默认门禁范围。

    # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，验证显式启用后 Phase95 能识别真实 low-level backend；如果没有这段测试，Phase95 的真实派发证据会停在 false。
    def test_phase96_explicit_real_path_marks_windows_low_level_backend_as_desktop_touch(self) -> None:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：定义真实路径推断测试；如果没有这行代码，真实 SendInput backend 标识不会被锁定。
        backend = FakeWindowsLowLevelSender()  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建 fake 真实后端；如果没有这行代码，测试会误碰真实桌面。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建隔离目录；如果没有这行代码，报告证据会污染真实运行目录。
            report = run_phase96_controlled_physical_live_smoke_contract(base_dir=Path(temporary_directory), real_smoke=True, allow_real_gate=True, low_level_backend=backend, phase58_smoke_runner=fake_phase58_keyboard_smoke, platform="win32")  # 新增代码+Phase96ControlledPhysicalLiveSmoke：显式开启合同但注入 fake 后端；如果没有这行代码，真实路径条件没有事实来源。
            report_path_exists = Path(str(report["report_path"])).exists()  # 修改代码+Phase96ControlledPhysicalLiveSmoke：在临时目录还未清理前检查报告文件；如果没有这行代码，退出 with 后目录删除会造成假失败。
        event_types = [str(event.get("type") or event.get("kind") or "") for event in backend.events]  # 新增代码+Phase96ControlledPhysicalLiveSmoke：提取事件类型；如果没有这行代码，无法确认 bridge 发送的是鼠标低层事件。
        self.assertTrue(report["passed"])  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认显式路径合同通过；如果没有这行代码，红灯失败可能被忽略。
        self.assertTrue(report["real_smoke_executed"])  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认真实路径请求被执行；如果没有这行代码，合同可能空跑。
        self.assertTrue(report["phase95_controlled_sender_reused"])  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认复用 Phase95 sender；如果没有这行代码，Phase96 可能绕开安全链路。
        self.assertTrue(report["phase95_physical_mouse_bridge"])  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认物理鼠标桥接成功；如果没有这行代码，Phase96 不能证明点击路径。
        self.assertTrue(report["phase58_keyboard_guard_reused"])  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认键盘路径复用 Phase58 guard；如果没有这行代码，键盘证据可能缺失。
        self.assertTrue(report["real_desktop_touched"])  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认真实 low-level backend 被识别为桌面副作用；如果没有这行代码，Phase95 真实派发报告仍会显示 false。
        self.assertIn("mouse_move", event_types)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认发送过鼠标移动；如果没有这行代码，bridge 可能没有真实鼠标事件。
        self.assertIn("mouse_down", event_types)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认发送过鼠标按下；如果没有这行代码，click 可能只是移动。
        self.assertIn("mouse_up", event_types)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认发送过鼠标抬起；如果没有这行代码，click 不完整。
        self.assertTrue(report_path_exists)  # 修改代码+Phase96ControlledPhysicalLiveSmoke：确认报告曾经落盘；如果没有这行代码，验收证据可能不存在。
    # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，显式真实路径测试到此结束；如果没有这个边界说明，初学者不容易看出真实 bridge 范围。

    # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，验证 CLI 行稳定且不泄露原文；如果没有这段测试，真实终端验收输出容易漂移。
    def test_phase96_cli_line_contains_tokens_and_hides_text(self) -> None:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：定义 CLI token 测试；如果没有这行代码，Rule17 场景可能匹配不到成功标记。
        backend = FakeWindowsLowLevelSender()  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建 fake 后端；如果没有这行代码，CLI 报告没有低层事件来源。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建临时目录；如果没有这行代码，CLI 测试会污染真实证据目录。
            report = run_phase96_controlled_physical_live_smoke_contract(base_dir=Path(temporary_directory), real_smoke=True, allow_real_gate=True, low_level_backend=backend, phase58_smoke_runner=fake_phase58_keyboard_smoke, platform="win32")  # 新增代码+Phase96ControlledPhysicalLiveSmoke：运行显式路径合同；如果没有这行代码，CLI 行没有输入数据。
        line = phase96_cli_line(report)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：生成 token 行；如果没有这行代码，无法检查终端输出格式。
        serialized = json.dumps(report, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：序列化报告；如果没有这行代码，嵌套明文泄露无法扫描。
        self.assertIn(PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_MARKER, line)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：检查 ready marker；如果没有这行代码，阶段锚点漂移不会被发现。
        self.assertIn(PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_OK_TOKEN, line)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：检查 OK token；如果没有这行代码，成功锚点漂移不会被发现。
        self.assertIn("phase95_physical_mouse_bridge=true", line)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：检查鼠标桥接 token；如果没有这行代码，真实物理鼠标证据可能从输出消失。
        self.assertIn("phase58_keyboard_guard_reused=true", line)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：检查键盘 guard token；如果没有这行代码，键盘证据可能从输出消失。
        self.assertIn("real_desktop_touched=true", line)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：检查真实桌面副作用 token；如果没有这行代码，Phase95 真实 backend 推断可能回退。
        self.assertIn(PHASE96_REAL_SENDINPUT_LIVE_SMOKE_ENV, serialized)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：检查环境门名称进入报告；如果没有这行代码，生产启用方式不可审计。
        self.assertIn(PHASE96_REAL_SENDINPUT_LIVE_SMOKE_REQUEST_ENV, serialized)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：检查请求门名称进入报告；如果没有这行代码，CLI 请求方式不可审计。
        self.assertNotIn("phase96-secret-text", serialized)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认测试 secret 不泄露；如果没有这行代码，隐私问题可能长期保存到 artifact。
    # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，CLI token 测试到此结束；如果没有这个边界说明，初学者不容易看出输出保护范围。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：测试类段结束，Phase96 测试类到此结束；如果没有这个边界说明，初学者不容易看出回归范围。

# 新增代码+Phase96ControlledPhysicalLiveSmoke：文件入口段开始，允许直接运行本测试文件；如果没有这段代码，人工排查时必须记完整 unittest 命令。
if __name__ == "__main__":  # 新增代码+Phase96ControlledPhysicalLiveSmoke：判断是否直接执行；如果没有这行代码，python 文件方式不会启动测试。
    unittest.main()  # 新增代码+Phase96ControlledPhysicalLiveSmoke：运行当前测试文件；如果没有这行代码，手工红绿灯循环不方便。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：文件入口段结束，直接运行路径到此结束；如果没有这个边界说明，初学者不容易看出入口范围。
