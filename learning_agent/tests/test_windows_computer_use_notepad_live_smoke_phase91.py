import json  # 新增代码+Phase91NotepadLiveSmoke：导入 JSON 用来校验真实终端场景文件格式；如果没有这行代码，场景 JSON 写坏要到验收时才暴露。
import tempfile  # 新增代码+Phase91NotepadLiveSmoke：导入临时目录工具，用来隔离 Phase91 测试文件；如果没有这行代码，测试可能污染真实项目目录。
import unittest  # 新增代码+Phase91NotepadLiveSmoke：导入 unittest，保持和现有 Phase90 测试一致；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase91NotepadLiveSmoke：导入路径工具，用来确认受控文件确实落在测试临时目录；如果没有它，测试无法可靠检查文件边界。
from unittest import mock  # 新增代码+Phase91NotepadLiveSmoke：导入 mock 用来临时清理环境变量；如果没有这行代码，开发机环境可能影响测试结果。

# 新增代码+Phase91NotepadLiveSmoke：这一行导入 Phase91 对外标记和运行时；如果没有它，测试无法验证用户终端里应该看到的稳定验收信号。
from learning_agent.computer_use.notepad_live_smoke import (
    PHASE91_REAL_NOTEPAD_SMOKE_ENV,
    PHASE91_UNCONTROLLED_ACTIONS_EXPANDED,
    PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_MARKER,
    PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_OK_TOKEN,
    WindowsNotepadLiveSmokeRuntime,
    phase91_cli_line,
    run_phase91_notepad_live_smoke_contract,
)


class WindowsComputerUseNotepadLiveSmokePhase91Tests(unittest.TestCase):  # 新增代码+Phase91NotepadLiveSmoke：类段开始，集中验证 Phase91 受控 Notepad 路径；如果没有这个类，真实软件入口没有自动化门禁。
    def test_phase91_builds_controlled_notepad_file_and_window_identity(self) -> None:  # 新增代码+Phase91NotepadLiveSmoke：函数段开始，验证受控文件和窗口身份计划；如果没有这段，真实软件入口可能误碰用户文件或系统设置。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase91NotepadLiveSmoke：使用临时目录隔离测试状态；如果没有这行代码，测试会把文件写到真实工作区。
            root = Path(temp_dir)  # 新增代码+Phase91NotepadLiveSmoke：把临时目录转成 Path；如果没有这行代码，后续路径比较会更脆弱。
            runtime = WindowsNotepadLiveSmokeRuntime(base_dir=root)  # 新增代码+Phase91NotepadLiveSmoke：创建 Phase91 运行时并限制工作目录；如果没有它，测试无法验证受控边界。
            file_plan = runtime.build_controlled_file_plan()  # 新增代码+Phase91NotepadLiveSmoke：生成受控文件计划；如果没有它，无法确认 Notepad 只操作专门测试文件。
            identity = runtime.build_dedicated_window_identity()  # 新增代码+Phase91NotepadLiveSmoke：生成专属窗口身份计划；如果没有它，调度器无法区分测试窗口和用户自己的 Notepad。
        controlled_file = Path(file_plan["file_path"])  # 新增代码+Phase91NotepadLiveSmoke：把文件路径转成 Path，方便做父目录边界判断；如果没有它，字符串比较容易漏掉路径规范化问题。
        self.assertIn(root.resolve(), controlled_file.resolve().parents)  # 新增代码+Phase91NotepadLiveSmoke：断言受控文件位于运行时根目录下；如果没有它，Notepad smoke 可能写入用户个人文件。
        self.assertFalse(file_plan["changes_registry"])  # 新增代码+Phase91NotepadLiveSmoke：断言文件计划不改注册表；如果没有它，测试无法防止 smoke 路径扩大到系统级变更。
        self.assertFalse(file_plan["changes_system_settings"])  # 新增代码+Phase91NotepadLiveSmoke：断言文件计划不改系统设置；如果没有它，真实软件测试可能越界影响电脑配置。
        self.assertFalse(file_plan["requires_admin"])  # 新增代码+Phase91NotepadLiveSmoke：断言文件计划不需要管理员权限；如果没有它，测试可能被设计成高风险操作。
        self.assertEqual(identity["app"], "notepad")  # 新增代码+Phase91NotepadLiveSmoke：确认 app 名称固定为 notepad；如果没有它，授权可能误发给其他软件。
        self.assertEqual(identity["process_name"], "notepad.exe")  # 新增代码+Phase91NotepadLiveSmoke：确认进程名是 notepad.exe；如果没有它，窗口绑定可能变成模糊标题匹配。
        self.assertTrue(identity["title_prefix"].startswith("Phase91"))  # 新增代码+Phase91NotepadLiveSmoke：确认窗口标题包含 Phase91 专属前缀；如果没有它，真实输入可能打到用户已有窗口。
        self.assertTrue(identity["controlled_window"])  # 新增代码+Phase91NotepadLiveSmoke：确认该窗口身份被标为受控窗口；如果没有它，安全边界无法知道这是测试专用对象。
    # 新增代码+Phase91NotepadLiveSmoke：函数段结束，test_phase91_builds_controlled_notepad_file_and_window_identity 到此结束；如果没有这个边界说明，初学者不容易看出测试范围。

    def test_phase91_contract_defaults_to_safe_notepad_dispatch_contract(self) -> None:  # 新增代码+Phase91NotepadLiveSmoke：函数段开始，验证默认契约不会执行真实 Notepad 输入；如果没有这段，普通测试或验收可能意外控制用户桌面。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase91NotepadLiveSmoke：使用临时目录隔离合同证据；如果没有这行代码，测试会污染真实运行目录。
            with mock.patch.dict("os.environ", {PHASE91_REAL_NOTEPAD_SMOKE_ENV: ""}, clear=False):  # 新增代码+Phase91NotepadLiveSmoke：临时清理真实 smoke 环境门禁；如果没有它，开发机环境变量可能让测试意外进入真实输入路径。
                report = run_phase91_notepad_live_smoke_contract(base_dir=Path(temp_dir))  # 新增代码+Phase91NotepadLiveSmoke：运行默认契约；如果没有它，测试无法证明 Phase91 的默认行为是安全契约模式。
        self.assertTrue(report["passed"])  # 新增代码+Phase91NotepadLiveSmoke：断言总体契约通过；如果没有它，后续字段即使错误也可能被忽略。
        self.assertTrue(report["notepad_live_smoke_ready"])  # 新增代码+Phase91NotepadLiveSmoke：确认 Notepad live smoke 入口已就绪；如果没有它，验收无法证明 Phase91 功能被加载。
        self.assertTrue(report["controlled_notepad_file_plan"])  # 新增代码+Phase91NotepadLiveSmoke：确认受控 Notepad 文件计划已就绪；如果没有它，真实软件测试可能缺少安全落点。
        self.assertTrue(report["dedicated_notepad_window_identity"])  # 新增代码+Phase91NotepadLiveSmoke：确认专属窗口身份计划已就绪；如果没有它，真实输入无法安全绑定目标窗口。
        self.assertTrue(report["phase90_dispatcher_integrated"])  # 新增代码+Phase91NotepadLiveSmoke：确认 Phase90 调度器被纳入闭环；如果没有它，Notepad 路径可能绕开统一授权系统。
        self.assertTrue(report["authorized_notepad_dispatch_contract"])  # 新增代码+Phase91NotepadLiveSmoke：确认授权后的 Notepad 契约分发成功；如果没有它，功能可能只停留在计划文档。
        self.assertTrue(report["dangerous_window_zero_events"])  # 新增代码+Phase91NotepadLiveSmoke：确认危险窗口没有产生事件；如果没有它，安全边界可能被扩大到 shell 或系统窗口。
        self.assertTrue(report["unauthorized_window_zero_events"])  # 新增代码+Phase91NotepadLiveSmoke：确认未授权窗口没有产生事件；如果没有它，授权模型就失去意义。
        self.assertTrue(report["raw_text_hidden"])  # 新增代码+Phase91NotepadLiveSmoke：确认原始输入文本没有泄漏到报告；如果没有它，日志可能暴露用户 prompt 或隐私内容。
        self.assertFalse(report["default_real_notepad_smoke_enabled"])  # 新增代码+Phase91NotepadLiveSmoke：确认默认不启用真实 Notepad smoke；如果没有它，普通验收可能误操作用户桌面。
        self.assertTrue(report["requires_explicit_notepad_env_gate"])  # 新增代码+Phase91NotepadLiveSmoke：确认真实 Notepad smoke 需要显式环境门禁；如果没有它，真实输入路径会缺少第二道确认。
        self.assertTrue(report["real_notepad_smoke_optional"])  # 新增代码+Phase91NotepadLiveSmoke：确认真实 Notepad smoke 是可选路径；如果没有它，默认契约和真实输入边界会混在一起。
        self.assertFalse(report["real_notepad_smoke_executed"])  # 新增代码+Phase91NotepadLiveSmoke：确认默认没有执行真实 Notepad smoke；如果没有它，测试无法防止意外桌面输入。
        self.assertTrue(report["cleanup_plan_ready"])  # 新增代码+Phase91NotepadLiveSmoke：确认清理计划已就绪；如果没有它，真实软件测试可能留下窗口、文件或按键状态。
        self.assertFalse(report["uncontrolled_actions_expanded"])  # 新增代码+Phase91NotepadLiveSmoke：确认 Phase91 没有扩张到不受控动作；如果没有它，后续可能把安全 contract 改成任意点击。
        self.assertFalse(PHASE91_UNCONTROLLED_ACTIONS_EXPANDED)  # 新增代码+Phase91NotepadLiveSmoke：确认模块常量也声明未扩张不受控动作；如果没有它，报告和代码边界可能不一致。
    # 新增代码+Phase91NotepadLiveSmoke：函数段结束，test_phase91_contract_defaults_to_safe_notepad_dispatch_contract 到此结束；如果没有这个边界说明，初学者不容易看出默认合同范围。

    def test_phase91_real_smoke_request_requires_explicit_env_gate(self) -> None:  # 新增代码+Phase91NotepadLiveSmoke：函数段开始，测试请求真实 smoke 但缺少环境门禁时必须拒绝；如果没有这段，单个参数就可能触发真实桌面输入。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase91NotepadLiveSmoke：使用临时目录隔离状态；如果没有这行代码，门禁失败证据可能污染真实目录。
            with mock.patch.dict("os.environ", {PHASE91_REAL_NOTEPAD_SMOKE_ENV: ""}, clear=False):  # 新增代码+Phase91NotepadLiveSmoke：确保环境门禁不存在；如果没有它，测试会受开发者本机状态影响。
                runtime = WindowsNotepadLiveSmokeRuntime(base_dir=Path(temp_dir))  # 新增代码+Phase91NotepadLiveSmoke：创建运行时；如果没有它，无法直接验证真实 smoke 门禁行为。
                report = runtime.run_contract(real_smoke=True)  # 新增代码+Phase91NotepadLiveSmoke：主动请求真实 smoke；如果没有它，测试覆盖不到危险入口。
        self.assertFalse(report["passed"])  # 新增代码+Phase91NotepadLiveSmoke：断言总体失败，因为缺少显式环境门禁；如果没有它，真实输入可能在未授权时启动。
        self.assertFalse(report["real_notepad_smoke_executed"])  # 新增代码+Phase91NotepadLiveSmoke：确认真实 smoke 没有执行；如果没有它，失败也可能已经操作过桌面。
        self.assertEqual(report["real_notepad_smoke"]["reason"], "explicit_env_gate_required")  # 新增代码+Phase91NotepadLiveSmoke：确认失败原因写清楚环境门禁缺失；如果没有它，用户难以判断为什么被拒绝。
    # 新增代码+Phase91NotepadLiveSmoke：函数段结束，test_phase91_real_smoke_request_requires_explicit_env_gate 到此结束；如果没有这个边界说明，初学者不容易看出门禁范围。

    def test_phase91_cli_line_contains_stable_tokens(self) -> None:  # 新增代码+Phase91NotepadLiveSmoke：函数段开始，测试终端输出行稳定；如果没有这段，真实可见终端验收会因为文案漂移而误判。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase91NotepadLiveSmoke：使用临时目录隔离合同状态；如果没有这行代码，CLI 行可能引用真实报告路径。
            report = run_phase91_notepad_live_smoke_contract(base_dir=Path(temp_dir))  # 新增代码+Phase91NotepadLiveSmoke：运行契约获得报告；如果没有它，CLI 行没有真实数据来源。
        line = phase91_cli_line(report)  # 新增代码+Phase91NotepadLiveSmoke：生成终端摘要；如果没有它，测试无法验证用户终端里最终看到的内容。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase91_notepad_live_smoke.json")  # 新增代码+Phase91NotepadLiveSmoke：定位 Phase91 真实终端场景文件；如果没有这行代码，场景缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase91NotepadLiveSmoke：读取场景文本；如果没有这行代码，场景 token 漏配无法被发现。
        json.loads(scenario_text)  # 新增代码+Phase91NotepadLiveSmoke：校验场景是合法 JSON；如果没有这行代码，controller 运行时才会暴露格式错误。
        self.assertIn(PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_MARKER, line)  # 新增代码+Phase91NotepadLiveSmoke：确认 ready marker 在输出中；如果没有它，acceptance_controller 找不到阶段标记。
        self.assertIn(PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_OK_TOKEN, line)  # 新增代码+Phase91NotepadLiveSmoke：确认 OK token 在输出中；如果没有它，验收无法判断 Phase91 成功。
        self.assertIn("real_notepad_smoke_executed=false", line)  # 新增代码+Phase91NotepadLiveSmoke：确认默认真实 smoke 未执行被明确打印；如果没有它，用户可能误以为已经真实操作 Notepad。
        self.assertIn("uncontrolled_actions_expanded=false", line)  # 新增代码+Phase91NotepadLiveSmoke：确认未扩张不受控动作被明确打印；如果没有它，后续安全边界变化不易被验收发现。
        expected_tokens = {PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_MARKER, PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_OK_TOKEN, "notepad_live_smoke_ready=true", "controlled_notepad_file_plan=true", "dedicated_notepad_window_identity=true", "phase90_dispatcher_integrated=true", "authorized_notepad_dispatch_contract=true", "dangerous_window_zero_events=true", "unauthorized_window_zero_events=true", "raw_text_hidden=true", "default_real_notepad_smoke_enabled=false", "requires_explicit_notepad_env_gate=true", "real_notepad_smoke_optional=true", "real_notepad_smoke_executed=false", "cleanup_plan_ready=true", "uncontrolled_actions_expanded=false"}  # 新增代码+Phase91NotepadLiveSmoke：定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase91NotepadLiveSmoke：遍历每个关键 token；如果没有这行代码，重复断言容易遗漏。
            self.assertIn(token, line)  # 新增代码+Phase91NotepadLiveSmoke：断言 CLI 输出包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase91NotepadLiveSmoke：断言真实终端场景也包含 token；如果没有这行代码，自动测试和真实验收可能不一致。
    # 新增代码+Phase91NotepadLiveSmoke：函数段结束，test_phase91_cli_line_contains_stable_tokens 到此结束；如果没有这个边界说明，初学者不容易看出 CLI token 范围。
# 新增代码+Phase91NotepadLiveSmoke：类段结束，WindowsComputerUseNotepadLiveSmokePhase91Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase91NotepadLiveSmoke：允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase91NotepadLiveSmoke：调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
