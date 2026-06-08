import importlib  # 新增代码+Phase109GenericRealLaunchCandidate：导入动态模块加载工具；如果没有这行代码，红测无法在 Phase109 模块尚未存在时给出清晰失败原因。
import tempfile  # 新增代码+Phase109GenericRealLaunchCandidate：导入临时目录工具隔离命令状态；如果没有这行代码，测试会污染真实项目里的 Computer Use session 文件。
import unittest  # 新增代码+Phase109GenericRealLaunchCandidate：导入 unittest 测试框架；如果没有这行代码，本文件不能被项目测试发现器正常执行。
from pathlib import Path  # 新增代码+Phase109GenericRealLaunchCandidate：导入 Path 统一处理 Windows 路径；如果没有这行代码，临时 workspace 路径拼接会更脆弱。

from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase109GenericRealLaunchCandidate：导入真实 `/computer` 终端命令入口；如果没有这行代码，测试会绕过用户实际使用的交互路径。


class WindowsComputerUseGenericRealLaunchCandidatePhase109Tests(unittest.TestCase):  # 新增代码+Phase109GenericRealLaunchCandidate：类段开始，集中验收 Phase109 通用真实启动候选；如果没有这个类，通用启动候选只会停在设计说明没有回归保护。
    def _phase109_module(self):  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，动态读取 Phase109 模块；如果没有这段函数，模块缺失时测试会报难懂的导入异常。
        try:  # 新增代码+Phase109GenericRealLaunchCandidate：尝试加载即将实现的新模块；如果没有这行代码，红测不能表达“模块必须存在”的合同。
            return importlib.import_module("learning_agent.computer_use.generic_real_launch_candidate")  # 新增代码+Phase109GenericRealLaunchCandidate：返回 Phase109 通用候选模块；如果没有这行代码，后续断言拿不到被测 API。
        except ModuleNotFoundError as error:  # 新增代码+Phase109GenericRealLaunchCandidate：捕获模块缺失错误；如果没有这行代码，红测会变成 ERROR 而不是清楚的 FAIL。
            self.fail(f"Phase109 generic real launch candidate module is missing: {error}")  # 新增代码+Phase109GenericRealLaunchCandidate：用明确断言说明缺少 Phase109 模块；如果没有这行代码，初学者不容易看懂失败原因。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，_phase109_module 到此结束；如果没有这个边界说明，初学者不容易看出动态导入范围。

    def _confirmation_token(self, request_output: str) -> str:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，从 full 模式请求输出提取 token；如果没有这段函数，测试只能硬编码一次性确认码。
        for line in request_output.splitlines():  # 新增代码+Phase109GenericRealLaunchCandidate：逐行扫描终端输出；如果没有这行代码，多行状态面板里的 token 无法稳定读取。
            if line.startswith("- confirmation_token="):  # 新增代码+Phase109GenericRealLaunchCandidate：定位确认 token 所在行；如果没有这行代码，可能误读其他字段。
                return line.split("=", 1)[1].strip()  # 新增代码+Phase109GenericRealLaunchCandidate：返回等号后的 token 文本；如果没有这行代码，full-confirm 命令无法构造。
        self.fail("missing confirmation token in /computer use --full output")  # 新增代码+Phase109GenericRealLaunchCandidate：明确报告 token 缺失；如果没有这行代码，测试会用空 token 继续造成误导。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，_confirmation_token 到此结束；如果没有这个边界说明，初学者不容易看出 token 解析范围。

    def _confirm_full_mode(self, workspace: Path) -> None:  # 修改代码+FullNaturalUserFlow：函数段开始，用真实用户的一行命令打开 full 模式；如果没有这段函数，交互测试会继续模拟动态 token 流程。
        full_output = run_computer_terminal_command(workspace, "/computer use --full")  # 修改代码+FullNaturalUserFlow：直接执行用户会输入的 full 命令；如果没有这行代码，launch 命令应该仍被权限门拦截。
        self.assertIn("full_mode=true", full_output)  # 修改代码+FullNaturalUserFlow：断言 full 模式确实开启；如果没有这行代码，后续启动测试的前置状态可能是假的。
        self.assertNotIn("/computer use --full-confirm", full_output)  # 新增代码+FullNaturalUserFlow：断言测试 helper 不再依赖 full-confirm；如果没有这行代码，旧流程可能回归。
    # 修改代码+FullNaturalUserFlow：函数段结束，_confirm_full_mode 到此结束；如果没有这个边界说明，初学者不容易看出自然 full 打开范围。

    def test_candidate_default_off_uses_phase108_without_per_app_patch(self) -> None:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，验证默认关闭候选复用 Phase108 且不需要逐应用补丁；如果没有这段测试，项目可能又退回每个 app 手写白名单。
        module = self._phase109_module()  # 新增代码+Phase109GenericRealLaunchCandidate：读取 Phase109 模块；如果没有这行代码，测试无法调用通用候选合同。
        report = module.run_phase109_generic_real_launch_candidate_contract()  # 新增代码+Phase109GenericRealLaunchCandidate：运行 Phase109 总合同；如果没有这行代码，默认关闭事实没有统一报告来源。
        self.assertEqual(report["marker"], "PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_READY")  # 新增代码+Phase109GenericRealLaunchCandidate：断言 ready marker 稳定；如果没有这行代码，真实终端验收无法定位 Phase109 输出。
        self.assertEqual(report["ok_token"], "PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_OK")  # 新增代码+Phase109GenericRealLaunchCandidate：断言 OK token 稳定；如果没有这行代码，失败输出可能被误当成功。
        self.assertTrue(report["passed"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言总合同通过；如果没有这行代码，子字段可能存在但整体未达标。
        self.assertTrue(report["generic_real_launch_candidate_ready"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言通用真实启动候选已就绪；如果没有这行代码，Phase109 可能只是复述 Phase108。
        self.assertTrue(report["uses_phase108_generic_discovery"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言候选基于 Phase108 动态发现；如果没有这行代码，后续实现可能绕回硬编码应用名。
        self.assertFalse(report["hardcoded_app_whitelist_required"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言不需要硬编码应用白名单；如果没有这行代码，用户指出的设计问题会复发。
        self.assertFalse(report["per_app_patch_required"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言不需要每个应用单独补丁；如果没有这行代码，通用 computer use 仍不可扩展。
        self.assertTrue(report["real_launch_default_disabled"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言真实启动默认关闭；如果没有这行代码，测试可能误触本机任意应用。
        self.assertTrue(report["default_off_backend_not_called"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言默认关闭时后端没有被调用；如果没有这行代码，默认安全只停留在口头承诺。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言合同没有触碰真实桌面；如果没有这行代码，自动测试可能打开用户本机应用。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，test_candidate_default_off_uses_phase108_without_per_app_patch 到此结束；如果没有这个边界说明，初学者不容易看出默认关闭测试范围。

    def test_recording_enabled_path_verifies_identity_and_cleanup(self) -> None:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，验证显式记录路径能走完身份校验与清理模型；如果没有这段测试，Phase109 只会有默认关闭没有真实启动准备度。
        module = self._phase109_module()  # 新增代码+Phase109GenericRealLaunchCandidate：读取 Phase109 模块；如果没有这行代码，测试无法调用记录型启用路径。
        report = module.run_phase109_generic_real_launch_candidate_contract()  # 新增代码+Phase109GenericRealLaunchCandidate：运行总合同获取记录路径证据；如果没有这行代码，身份和清理字段没有数据来源。
        self.assertTrue(report["recording_backend_reaches_launcher"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言显式记录模式会到达通用 launcher 后端；如果没有这行代码，最后一跳仍可能没有接通。
        self.assertTrue(report["process_identity_verified"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言启动进程身份被校验；如果没有这行代码，后续真实启动可能无法确认打开的是目标应用。
        self.assertTrue(report["window_identity_verified"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言窗口身份被校验；如果没有这行代码，agent 可能在错误窗口上继续操作。
        self.assertTrue(report["target_identity_verified"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言进程和窗口共同指向同一目标；如果没有这行代码，进程窗口归属关系不可审计。
        self.assertTrue(report["cleanup_completed"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言清理流程完成；如果没有这行代码，未来真实启动可能留下应用窗口。
        self.assertTrue(report["verified_window_cleanup_completed"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言窗口级清理完成；如果没有这行代码，残留窗口可能被忽略。
        self.assertTrue(report["residual_process_check_completed"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言残留进程检查完成；如果没有这行代码，清理是否彻底无法证明。
        self.assertFalse(report["residual_owned_process"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言没有本候选拥有的残留进程；如果没有这行代码，真实 smoke 后可能留下垃圾进程。
        self.assertTrue(report["high_risk_refused"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言高风险目标仍被拒绝；如果没有这行代码，通用启动候选可能放开 PowerShell。
        self.assertFalse(report["uncontrolled_actions_expanded"])  # 新增代码+Phase109GenericRealLaunchCandidate：断言没有扩张无边界动作；如果没有这行代码，full 模式可能被误读为任意控制。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，test_recording_enabled_path_verifies_identity_and_cleanup 到此结束；如果没有这个边界说明，初学者不容易看出记录路径测试范围。

    def test_interactive_launch_prints_phase109_default_off_candidate_after_full_mode(self) -> None:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，验证真实 `/computer launch` 会输出 Phase109 默认关闭证据；如果没有这段测试，模块合同可能没有接到用户命令入口。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase109GenericRealLaunchCandidate：创建临时 workspace 隔离 session 状态；如果没有这行代码，测试可能读写真实用户授权状态。
            workspace = Path(temp_dir)  # 新增代码+Phase109GenericRealLaunchCandidate：保存临时 workspace 路径；如果没有这行代码，多条命令不能共享同一 session。
            self._confirm_full_mode(workspace)  # 新增代码+Phase109GenericRealLaunchCandidate：先按真实流程确认 full 模式；如果没有这行代码，launch 输出可能只是权限拦截。
            output = run_computer_terminal_command(workspace, "/computer launch obsidian")  # 新增代码+Phase109GenericRealLaunchCandidate：执行真实用户会输入的通用应用启动命令；如果没有这行代码，测试无法覆盖交互入口。
        self.assertIn("PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_READY", output)  # 新增代码+Phase109GenericRealLaunchCandidate：断言终端输出 Phase109 ready marker；如果没有这行代码，可见终端验收无法定位新能力。
        self.assertIn("PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_OK", output)  # 新增代码+Phase109GenericRealLaunchCandidate：断言终端输出 Phase109 OK token；如果没有这行代码，失败路径可能被误读。
        self.assertIn("generic_real_launch_candidate_ready=true", output)  # 新增代码+Phase109GenericRealLaunchCandidate：断言通用真实启动候选已就绪；如果没有这行代码，输出可能只有 Phase108 发现证据。
        self.assertIn("uses_phase108_generic_discovery=true", output)  # 新增代码+Phase109GenericRealLaunchCandidate：断言交互入口复用 Phase108 发现；如果没有这行代码，用户关心的通用性没有被证明。
        self.assertIn("hardcoded_app_whitelist_required=false", output)  # 新增代码+Phase109GenericRealLaunchCandidate：断言交互入口不要求硬编码白名单；如果没有这行代码，设计可能回到逐应用授权。
        self.assertIn("per_app_patch_required=false", output)  # 新增代码+Phase109GenericRealLaunchCandidate：断言交互入口不要求逐应用补丁；如果没有这行代码，无法回应“成千上万个应用”的问题。
        self.assertIn("real_launch_default_disabled=true", output)  # 新增代码+Phase109GenericRealLaunchCandidate：断言默认不会真实启动；如果没有这行代码，测试可能误导用户以为已经打开应用。
        self.assertIn("real_desktop_touched=false", output)  # 新增代码+Phase109GenericRealLaunchCandidate：断言没有触碰真实桌面；如果没有这行代码，安全边界在真实命令里不可见。
        self.assertIn("uncontrolled_actions_expanded=false", output)  # 新增代码+Phase109GenericRealLaunchCandidate：断言没有扩张无边界动作；如果没有这行代码，/computer use --full 可能被误读成无限制控制。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，test_interactive_launch_prints_phase109_default_off_candidate_after_full_mode 到此结束；如果没有这个边界说明，初学者不容易看出交互输出测试范围。
# 新增代码+Phase109GenericRealLaunchCandidate：类段结束，WindowsComputerUseGenericRealLaunchCandidatePhase109Tests 到此结束；如果没有这个边界说明，初学者不容易看出 Phase109 测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase109GenericRealLaunchCandidate：文件入口段开始，允许直接运行本测试文件；如果没有这行代码，初学者必须记住完整 unittest 命令。
    unittest.main()  # 新增代码+Phase109GenericRealLaunchCandidate：启动 unittest 执行断言；如果没有这行代码，直接运行文件不会执行任何测试。
# 新增代码+Phase109GenericRealLaunchCandidate：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出入口范围。
