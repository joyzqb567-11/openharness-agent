import importlib  # 新增代码+Phase108GenericAppDiscovery：导入动态模块加载工具；如果没有这行代码，红测无法在模块尚未存在时把缺失能力转成清楚的测试失败。
import tempfile  # 新增代码+Phase108GenericAppDiscovery：导入临时目录工具隔离命令状态；如果没有这行代码，测试会污染真实项目里的 Computer Use session 文件。
import unittest  # 新增代码+Phase108GenericAppDiscovery：导入 unittest 测试框架；如果没有这行代码，本文件不会被项目测试发现器正常执行。
from pathlib import Path  # 新增代码+Phase108GenericAppDiscovery：导入 Path 统一处理 Windows 路径；如果没有这行代码，临时 workspace 路径拼接容易出错。

from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase108GenericAppDiscovery：导入真实 `/computer` 命令入口；如果没有这行代码，测试会绕过用户实际使用的交互路径。


class WindowsComputerUseGenericAppDiscoveryPhase108Tests(unittest.TestCase):  # 新增代码+Phase108GenericAppDiscovery：类段开始，集中验证 Phase108 通用应用发现能力；如果没有这个类，Phase108 只会停留在口头设计没有回归保护。
    def _phase108_module(self):  # 新增代码+Phase108GenericAppDiscovery：函数段开始，动态读取 Phase108 模块；如果没有这段函数，模块缺失时测试会报不友好的导入错误。
        try:  # 新增代码+Phase108GenericAppDiscovery：尝试导入即将实现的新模块；如果没有这行代码，测试无法表达“Phase108 模块必须存在”的合同。
            return importlib.import_module("learning_agent.computer_use.generic_app_discovery")  # 新增代码+Phase108GenericAppDiscovery：返回通用发现模块；如果没有这行代码，后续测试拿不到被测 API。
        except ModuleNotFoundError as error:  # 新增代码+Phase108GenericAppDiscovery：捕获模块缺失错误；如果没有这行代码，红测会变成 ERROR 而不是清楚的 FAIL。
            self.fail(f"Phase108 generic app discovery module is missing: {error}")  # 新增代码+Phase108GenericAppDiscovery：用明确断言失败说明缺少模块；如果没有这行代码，初学者很难看懂红测为什么失败。
    # 新增代码+Phase108GenericAppDiscovery：函数段结束，_phase108_module 到此结束；如果没有这个边界说明，初学者不容易看出动态导入范围。

    def _confirmation_token(self, request_output: str) -> str:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，从 `/computer use --full` 输出提取 token；如果没有这段函数，测试只能硬编码动态确认码。
        for line in request_output.splitlines():  # 新增代码+Phase108GenericAppDiscovery：逐行扫描终端输出；如果没有这行代码，多行状态面板里的 token 无法稳定读取。
            if line.startswith("- confirmation_token="):  # 新增代码+Phase108GenericAppDiscovery：定位确认 token 所在行；如果没有这行代码，可能误读其他字段。
                return line.split("=", 1)[1].strip()  # 新增代码+Phase108GenericAppDiscovery：返回等号后的 token 文本；如果没有这行代码，full-confirm 命令无法构造。
        self.fail("missing confirmation token in /computer use --full output")  # 新增代码+Phase108GenericAppDiscovery：明确报告 token 缺失；如果没有这行代码，测试会以空 token 继续造成误导。
    # 新增代码+Phase108GenericAppDiscovery：函数段结束，_confirmation_token 到此结束；如果没有这个边界说明，初学者不容易看出 token 解析范围。

    def _confirm_full_mode(self, workspace: Path) -> None:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，用真实命令打开 full 模式；如果没有这段函数，测试会绕过用户必须确认的安全设计。
        request_output = run_computer_terminal_command(workspace, "/computer use --full")  # 新增代码+Phase108GenericAppDiscovery：先请求 full 模式确认 token；如果没有这行代码，后续 full-confirm 没有合法 token。
        token = self._confirmation_token(request_output)  # 新增代码+Phase108GenericAppDiscovery：从请求输出里读取动态 token；如果没有这行代码，确认命令无法使用本轮真实 token。
        confirm_output = run_computer_terminal_command(workspace, f"/computer use --full-confirm {token}")  # 新增代码+Phase108GenericAppDiscovery：按真实用户命令确认 full 模式；如果没有这行代码，launch 命令仍应被 mode gate 拒绝。
        self.assertIn("full_mode=true", confirm_output)  # 新增代码+Phase108GenericAppDiscovery：断言 full 模式确实开启；如果没有这行代码，后续测试前置状态可能是假成功。
    # 新增代码+Phase108GenericAppDiscovery：函数段结束，_confirm_full_mode 到此结束；如果没有这个边界说明，初学者不容易看出 full 确认范围。

    def test_dynamic_candidates_do_not_require_per_app_whitelist(self) -> None:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，验证动态候选发现替代逐个应用白名单；如果没有这段测试，项目可能继续靠硬编码 app 名扩展。
        module = self._phase108_module()  # 新增代码+Phase108GenericAppDiscovery：读取 Phase108 模块；如果没有这行代码，测试无法调用新通用发现 API。
        report = module.resolve_generic_app_launch_target("Obsidian", candidates=[{"display_name": "Obsidian", "executable": "Obsidian.exe", "source": "start_menu"}])  # 新增代码+Phase108GenericAppDiscovery：注入一个非内置别名的普通应用候选；如果没有这行代码，测试不能证明不需要为 Obsidian 单独写白名单。
        self.assertTrue(report["passed"])  # 新增代码+Phase108GenericAppDiscovery：断言普通候选被通用合同接受；如果没有这行代码，动态发现可能只是返回数据但不算可用。
        self.assertTrue(report["dynamic_discovery_used"])  # 新增代码+Phase108GenericAppDiscovery：断言走的是动态发现路径；如果没有这行代码，硬编码别名也可能冒充通用发现。
        self.assertFalse(report["hardcoded_app_whitelist_required"])  # 新增代码+Phase108GenericAppDiscovery：断言不需要每个 app 进白名单；如果没有这行代码，用户指出的问题会再次回到设计里。
        self.assertFalse(report["per_app_patch_required"])  # 新增代码+Phase108GenericAppDiscovery：断言新增普通 app 不需要单独补丁；如果没有这行代码，Phase108 不能证明可扩展性。
        self.assertEqual(report["best_candidate_executable"], "Obsidian.exe")  # 新增代码+Phase108GenericAppDiscovery：断言保留发现到的可执行名；如果没有这行代码，启动计划可能丢失目标身份。
        self.assertTrue(report["safe_start_process_plan"])  # 新增代码+Phase108GenericAppDiscovery：断言生成安全 Start-Process 风格计划；如果没有这行代码，普通候选可能没有可审计启动计划。
        self.assertFalse(report["real_launch_attempted"])  # 新增代码+Phase108GenericAppDiscovery：断言默认不真实启动；如果没有这行代码，自动测试可能误触碰本机桌面。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+Phase108GenericAppDiscovery：断言没有触碰真实桌面；如果没有这行代码，安全边界不可见。
    # 新增代码+Phase108GenericAppDiscovery：函数段结束，test_dynamic_candidates_do_not_require_per_app_whitelist 到此结束；如果没有这个边界说明，初学者不容易看出动态发现测试范围。

    def test_high_risk_candidate_is_refused_even_when_discovered(self) -> None:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，验证发现到高风险候选也必须拒绝；如果没有这段测试，动态发现可能把 PowerShell 当普通应用放行。
        module = self._phase108_module()  # 新增代码+Phase108GenericAppDiscovery：读取 Phase108 模块；如果没有这行代码，测试无法调用风险分类入口。
        report = module.resolve_generic_app_launch_target("PowerShell", candidates=[{"display_name": "Windows PowerShell", "executable": "powershell.exe", "source": "start_menu"}])  # 新增代码+Phase108GenericAppDiscovery：注入一个真实可能存在的高风险候选；如果没有这行代码，拒绝只覆盖文本关键词不覆盖发现结果。
        self.assertFalse(report["passed"])  # 新增代码+Phase108GenericAppDiscovery：断言高风险目标不会通过；如果没有这行代码，拒绝结果可能被误判成成功。
        self.assertTrue(report["high_risk_refused"])  # 新增代码+Phase108GenericAppDiscovery：断言拒绝原因是高风险；如果没有这行代码，安全策略字段不可审计。
        self.assertFalse(report["safe_start_process_plan"])  # 新增代码+Phase108GenericAppDiscovery：断言不会生成可启动计划；如果没有这行代码，高风险目标可能继续走到后端 launcher。
        self.assertFalse(report["real_launch_attempted"])  # 新增代码+Phase108GenericAppDiscovery：断言没有真实启动尝试；如果没有这行代码，高风险拒绝可能仍有副作用。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+Phase108GenericAppDiscovery：断言没有触碰真实桌面；如果没有这行代码，安全拒绝不可验证。
    # 新增代码+Phase108GenericAppDiscovery：函数段结束，test_high_risk_candidate_is_refused_even_when_discovered 到此结束；如果没有这个边界说明，初学者不容易看出高风险测试范围。

    def test_computer_launch_unknown_ordinary_app_uses_generic_default_off_path(self) -> None:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，验证真实 `/computer launch` 对未知普通 app 走通用默认关闭路径；如果没有这段测试，用户命令仍会被 Phase107 未知拒绝卡住。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase108GenericAppDiscovery：创建临时 workspace 隔离命令状态；如果没有这行代码，测试会写入真实项目 memory。
            workspace = Path(temp_dir)  # 新增代码+Phase108GenericAppDiscovery：保存临时 workspace 路径；如果没有这行代码，多条命令可能无法共享同一 session。
            self._confirm_full_mode(workspace)  # 新增代码+Phase108GenericAppDiscovery：先按真实流程确认 full 模式；如果没有这行代码，launch 失败可能只是权限未开。
            output = run_computer_terminal_command(workspace, "/computer launch obsidian")  # 新增代码+Phase108GenericAppDiscovery：执行用户会自然输入的未知普通应用启动命令；如果没有这行代码，测试无法覆盖真实交互入口。
        self.assertIn("PHASE108_GENERIC_APP_DISCOVERY_READY", output)  # 新增代码+Phase108GenericAppDiscovery：断言输出 Phase108 marker；如果没有这行代码，终端验收无法定位通用发现证据。
        self.assertIn("PHASE108_GENERIC_APP_DISCOVERY_OK", output)  # 新增代码+Phase108GenericAppDiscovery：断言通用默认关闭路径成功；如果没有这行代码，失败输出也可能被误读。
        self.assertIn("dynamic_discovery_used=true", output)  # 新增代码+Phase108GenericAppDiscovery：断言用户命令走动态发现合同；如果没有这行代码，硬编码别名路径可能冒充成功。
        self.assertIn("hardcoded_app_whitelist_required=false", output)  # 新增代码+Phase108GenericAppDiscovery：断言不需要硬编码 app 白名单；如果没有这行代码，Phase108 无法回应用户的核心设计问题。
        self.assertIn("per_app_patch_required=false", output)  # 新增代码+Phase108GenericAppDiscovery：断言新增普通 app 不需要逐个补丁；如果没有这行代码，可扩展性不可验证。
        self.assertIn("generic_target_default_off=true", output)  # 修改代码+Phase108GenericAppDiscovery：断言通用普通 app 被安全接收但默认不真实启动；如果没有这行代码，已安装发现和 fallback 发现不能用同一合同验收。
        self.assertIn("real_full_launch_attempted=false", output)  # 新增代码+Phase108GenericAppDiscovery：断言命令没有真实启动尝试；如果没有这行代码，自动测试可能误开本机应用。
        self.assertIn("real_desktop_touched=false", output)  # 新增代码+Phase108GenericAppDiscovery：断言没有触碰真实桌面；如果没有这行代码，安全边界不可验收。
    # 新增代码+Phase108GenericAppDiscovery：函数段结束，test_computer_launch_unknown_ordinary_app_uses_generic_default_off_path 到此结束；如果没有这个边界说明，初学者不容易看出交互入口测试范围。
# 新增代码+Phase108GenericAppDiscovery：类段结束，WindowsComputerUseGenericAppDiscoveryPhase108Tests 到此结束；如果没有这个边界说明，初学者不容易看出 Phase108 测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase108GenericAppDiscovery：文件入口段开始，允许直接运行本测试文件；如果没有这行代码，初学者必须记住完整 unittest 命令。
    unittest.main()  # 新增代码+Phase108GenericAppDiscovery：启动 unittest 执行断言；如果没有这行代码，直接运行文件不会跑任何测试。
# 新增代码+Phase108GenericAppDiscovery：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出入口范围。
