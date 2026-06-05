import importlib  # 新增代码+ComputerUseFullMaturityContract：导入动态模块加载工具；如果没有这一行，测试就不能在契约模块缺失时清楚地暴露“还没实现”的事实。
import unittest  # 新增代码+ComputerUseFullMaturityContract：导入 unittest 测试框架；如果没有这一行，本文件就不能被项目现有测试命令正常执行。

class WindowsComputerUseFullMaturityContractTests(unittest.TestCase):  # 新增代码+ComputerUseFullMaturityContract：类段开始，集中验收 /computer use --full 成熟版产品契约；如果没有这个类，成熟边界只会停留在文档里，后续改动容易跑偏。
    def _contract_module(self):  # 新增代码+ComputerUseFullMaturityContract：函数段开始，统一加载待实现的契约模块；如果没有这个函数，每个测试都要重复导入逻辑，失败原因也会更分散。
        return importlib.import_module("learning_agent.computer_use.full_maturity_contract")  # 新增代码+ComputerUseFullMaturityContract：加载 full maturity 契约模块；如果没有这一行，测试拿不到固定 token 和安全边界常量。
    # 新增代码+ComputerUseFullMaturityContract：函数段结束，_contract_module 到此结束；如果没有这个边界说明，代码小白不容易看出动态导入 helper 的范围。

    def test_final_maturity_tokens_are_fixed(self) -> None:  # 新增代码+ComputerUseFullMaturityContract：函数段开始，验证最终成熟 marker 和 OK token 固定不漂移；如果没有这个测试，真实终端验收可能因为 token 改名而失效。
        module = self._contract_module()  # 新增代码+ComputerUseFullMaturityContract：读取契约模块；如果没有这一行，后续断言没有被测试对象。
        self.assertEqual(module.COMPUTER_USE_FULL_MATURE_MARKER, "COMPUTER_USE_FULL_MATURE_READY")  # 新增代码+ComputerUseFullMaturityContract：断言 ready marker 固定；如果没有这一行，验收脚本可能无法稳定识别成熟模式已就绪。
        self.assertEqual(module.COMPUTER_USE_FULL_MATURE_OK_TOKEN, "COMPUTER_USE_FULL_MATURE_OK")  # 新增代码+ComputerUseFullMaturityContract：断言 OK token 固定；如果没有这一行，失败输出和成功输出可能被误判。
        self.assertIn("M0_product_semantics", module.COMPUTER_USE_FULL_MATURITY_GATES)  # 新增代码+ComputerUseFullMaturityContract：确认产品语义门禁存在；如果没有这一行，full 模式可能被误做成无限权限。
        self.assertIn("M7_visible_terminal_acceptance", module.COMPUTER_USE_FULL_MATURITY_GATES)  # 新增代码+ComputerUseFullMaturityContract：确认真实可见终端验收门禁存在；如果没有这一行，单元测试可能被误当成最终交付。
    # 新增代码+ComputerUseFullMaturityContract：函数段结束，test_final_maturity_tokens_are_fixed 到此结束；如果没有这个边界说明，读者不容易看出 token 测试范围。

    def test_contract_forbids_per_app_controller_and_unlimited_permission(self) -> None:  # 新增代码+ComputerUseFullMaturityContract：函数段开始，验证成熟契约禁止逐应用 controller 和无限权限；如果没有这个测试，项目可能重新走回每个应用单独打通的老路。
        module = self._contract_module()  # 新增代码+ComputerUseFullMaturityContract：读取契约模块；如果没有这一行，后续无法检查成熟边界报告。
        report = module.run_computer_use_full_maturity_contract()  # 新增代码+ComputerUseFullMaturityContract：生成统一契约报告；如果没有这一行，测试只能检查零散常量，无法验证组合语义。
        self.assertFalse(report["per_app_controller_required"])  # 新增代码+ComputerUseFullMaturityContract：断言不需要每个应用一个 controller；如果没有这一行，通用 computer use 会被白名单设计拖垮。
        self.assertFalse(report["hardcoded_app_whitelist_required"])  # 新增代码+ComputerUseFullMaturityContract：断言不需要硬编码应用白名单；如果没有这一行，成千上万应用的扩展问题会复发。
        self.assertFalse(report["per_app_patch_required"])  # 新增代码+ComputerUseFullMaturityContract：断言不需要逐应用补丁；如果没有这一行，后续实现可能继续靠打补丁堆 Phase。
        self.assertFalse(report["full_mode_unlimited_permission"])  # 新增代码+ComputerUseFullMaturityContract：断言 full 模式不是无限权限；如果没有这一行，高风险窗口和系统工具可能被错误放开。
        self.assertIn("per_app_controller", module.COMPUTER_USE_FULL_OUT_OF_SCOPE)  # 新增代码+ComputerUseFullMaturityContract：确认逐应用 controller 被列为范围外；如果没有这一行，范围边界会变得模糊。
        self.assertIn("unlimited_permission", module.COMPUTER_USE_FULL_OUT_OF_SCOPE)  # 新增代码+ComputerUseFullMaturityContract：确认无限权限被列为范围外；如果没有这一行，用户确认可能被误解成跳过所有安全策略。
    # 新增代码+ComputerUseFullMaturityContract：函数段结束，test_contract_forbids_per_app_controller_and_unlimited_permission 到此结束；如果没有这个边界说明，读者不容易看出禁止范围测试已结束。

    def test_contract_requires_safety_and_visible_terminal_acceptance(self) -> None:  # 新增代码+ComputerUseFullMaturityContract：函数段开始，验证安全拒绝和真实可见终端验收必须保留；如果没有这个测试，成熟声明可能绕过最后的真实场景。
        module = self._contract_module()  # 新增代码+ComputerUseFullMaturityContract：读取契约模块；如果没有这一行，测试无法访问统一报告。
        report = module.run_computer_use_full_maturity_contract()  # 新增代码+ComputerUseFullMaturityContract：生成契约报告；如果没有这一行，安全门禁无法用同一份事实验证。
        self.assertTrue(report["high_risk_refusal_required"])  # 新增代码+ComputerUseFullMaturityContract：断言高风险目标仍必须拒绝；如果没有这一行，PowerShell、凭据窗口等风险目标可能被放行。
        self.assertTrue(report["credential_window_zero_events_required"])  # 新增代码+ComputerUseFullMaturityContract：断言凭据窗口零事件原则必须存在；如果没有这一行，密码和验证码窗口可能被错误操作。
        self.assertTrue(report["visible_terminal_acceptance_required"])  # 新增代码+ComputerUseFullMaturityContract：断言最终必须做真实可见终端验收；如果没有这一行，项目可能只靠单元测试宣称成熟。
        self.assertTrue(report["maturity_phase_stop_rule"])  # 新增代码+ComputerUseFullMaturityContract：断言通过 M0-M7 后停止无止境 Phase；如果没有这一行，成熟目标会继续被无限延期。
        self.assertFalse(report["uncontrolled_actions_expanded"])  # 新增代码+ComputerUseFullMaturityContract：断言没有扩张无边界动作；如果没有这一行，full 模式可能被误做成失控桌面控制。
    # 新增代码+ComputerUseFullMaturityContract：函数段结束，test_contract_requires_safety_and_visible_terminal_acceptance 到此结束；如果没有这个边界说明，读者不容易看出安全验收范围。

    def test_cli_line_contains_final_maturity_boundary(self) -> None:  # 新增代码+ComputerUseFullMaturityContract：函数段开始，验证终端输出行包含最终成熟边界 token；如果没有这个测试，真实终端验收可能缺少稳定可读的结果行。
        module = self._contract_module()  # 新增代码+ComputerUseFullMaturityContract：读取契约模块；如果没有这一行，测试无法调用 CLI 格式化函数。
        report = module.run_computer_use_full_maturity_contract()  # 新增代码+ComputerUseFullMaturityContract：生成统一契约报告；如果没有这一行，输出行没有可信事实来源。
        line = module.computer_use_full_maturity_contract_cli_line(report)  # 新增代码+ComputerUseFullMaturityContract：把契约报告转成终端 token 行；如果没有这一行，真实终端验收只能解析复杂 JSON。
        self.assertIn("COMPUTER_USE_FULL_MATURE_READY", line)  # 新增代码+ComputerUseFullMaturityContract：断言 ready marker 出现在终端行；如果没有这一行，人工观察不容易识别成熟契约。
        self.assertIn("COMPUTER_USE_FULL_MATURE_OK", line)  # 新增代码+ComputerUseFullMaturityContract：断言 OK token 出现在终端行；如果没有这一行，自动验收无法稳定判断通过。
        self.assertIn("hardcoded_app_whitelist_required=false", line)  # 新增代码+ComputerUseFullMaturityContract：断言终端行展示不需要硬编码白名单；如果没有这一行，用户关心的通用性无法直接看见。
        self.assertIn("per_app_patch_required=false", line)  # 新增代码+ComputerUseFullMaturityContract：断言终端行展示不需要逐应用补丁；如果没有这一行，最终输出不能回应用户对无限 Phase 的担心。
        self.assertIn("uncontrolled_actions_expanded=false", line)  # 新增代码+ComputerUseFullMaturityContract：断言终端行展示没有扩张失控动作；如果没有这一行，安全边界不够透明。
    # 新增代码+ComputerUseFullMaturityContract：函数段结束，test_cli_line_contains_final_maturity_boundary 到此结束；如果没有这个边界说明，读者不容易看出 CLI 输出测试范围。
# 新增代码+ComputerUseFullMaturityContract：类段结束，WindowsComputerUseFullMaturityContractTests 到此结束；如果没有这个边界说明，代码小白不容易看出成熟契约测试集合已结束。

if __name__ == "__main__":  # 新增代码+ComputerUseFullMaturityContract：文件入口段开始，允许直接运行本测试文件；如果没有这一行，用户必须记住完整 unittest 命令才能手动验证。
    unittest.main()  # 新增代码+ComputerUseFullMaturityContract：启动 unittest；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+ComputerUseFullMaturityContract：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，读者不容易看出脚本入口范围。
