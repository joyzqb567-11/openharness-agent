import importlib  # 新增代码+WindowsLaunchResolver：导入动态模块加载工具；如果没有这一行，测试无法在 resolver 尚未实现时给出清楚失败信息。
import unittest  # 新增代码+WindowsLaunchResolver：导入 unittest 测试框架；如果没有这一行，本文件不会被项目测试系统正常执行。

class WindowsComputerUseLaunchResolverPhase124Tests(unittest.TestCase):  # 新增代码+WindowsLaunchResolver：测试类开始，集中验证 Windows 多后端启动解析器；如果没有这个类，Phase124 行为没有回归保护。
    def _resolver_module(self):  # 新增代码+WindowsLaunchResolver：函数段开始，动态导入即将实现的 resolver 模块；如果没有这段函数，模块缺失会变成不友好的导入错误。
        try:  # 新增代码+WindowsLaunchResolver：尝试导入 resolver；如果没有这一行，测试无法把“缺少模块”表达成明确断言。
            return importlib.import_module("learning_agent.computer_use.windows_launch_resolver")  # 新增代码+WindowsLaunchResolver：返回 Windows 启动解析模块；如果没有这一行，后续测试拿不到被测 API。
        except ModuleNotFoundError as error:  # 新增代码+WindowsLaunchResolver：捕获模块缺失错误；如果没有这一行，红测会显示 ERROR 而不是清楚的 FAIL。
            self.fail(f"Phase124 windows_launch_resolver module is missing: {error}")  # 新增代码+WindowsLaunchResolver：把缺失模块转成明确失败；如果没有这一行，用户不容易知道应该新增哪个文件。
    # 新增代码+WindowsLaunchResolver：函数段结束，_resolver_module 到此结束；如果没有这个边界说明，用户不容易看出动态导入范围。

    def test_resolver_keeps_exe_candidate_on_argv_backend(self) -> None:  # 新增代码+WindowsLaunchResolver：函数段开始，验证 exe 候选继续走无 shell argv 后端；如果没有这段测试，旧的安全启动路径可能被误改坏。
        module = self._resolver_module()  # 新增代码+WindowsLaunchResolver：读取 resolver 模块；如果没有这一行，测试无法调用启动解析函数。
        plan = module.resolve_windows_launch_plan(candidate={"display_name": "Paint", "app_name": "mspaint", "launch_id": "mspaint.exe", "launch_kind": "exe", "source": "app_paths_registry", "installed_app_verified": True})  # 新增代码+WindowsLaunchResolver：注入真实 Paint exe 候选；如果没有这一行，测试无法证明普通 exe 仍可安全启动。
        self.assertTrue(plan["safe_to_launch"])  # 新增代码+WindowsLaunchResolver：断言 exe 计划可安全启动；如果没有这一行，resolver 可能把普通应用误拒绝。
        self.assertEqual(plan["launch_backend"], "argv_no_shell")  # 新增代码+WindowsLaunchResolver：断言 exe 使用 argv 后端；如果没有这一行，后端可能退回 shell 字符串。
        self.assertEqual(plan["executable"], "mspaint.exe")  # 新增代码+WindowsLaunchResolver：断言保留真实 exe 名；如果没有这一行，Paint 可能继续被错误猜名。
        self.assertFalse(plan["uses_shell_string"])  # 新增代码+WindowsLaunchResolver：断言不使用 shell 字符串；如果没有这一行，安全边界不可审计。
    # 新增代码+WindowsLaunchResolver：函数段结束，test_resolver_keeps_exe_candidate_on_argv_backend 到此结束；如果没有这个边界说明，用户不容易看出 exe 后端测试范围。

    def test_resolver_preserves_appx_aumid_without_exe_guess(self) -> None:  # 新增代码+WindowsLaunchResolver：函数段开始，验证 AppX/AUMID 不再被压扁成 exe 猜测；如果没有这段测试，UWP 应用会继续走错后端。
        module = self._resolver_module()  # 新增代码+WindowsLaunchResolver：读取 resolver 模块；如果没有这一行，测试无法调用启动解析函数。
        plan = module.resolve_windows_launch_plan(candidate={"display_name": "Calculator", "app_name": "calc", "launch_id": "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App", "launch_kind": "appx", "source": "appx_package", "installed_app_verified": True})  # 新增代码+WindowsLaunchResolver：注入 AppX Calculator 候选；如果没有这一行，测试无法覆盖 AUMID 入口。
        self.assertTrue(plan["safe_to_launch"])  # 新增代码+WindowsLaunchResolver：断言 AppX 计划本身是可启动身份；如果没有这一行，resolver 会误把商店应用当不可用。
        self.assertEqual(plan["launch_backend"], "appx_aumid")  # 新增代码+WindowsLaunchResolver：断言 AppX 使用 AUMID 后端；如果没有这一行，后续 launcher 不知道该用 AppsFolder/AUMID 方式。
        self.assertEqual(plan["aumid"], "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App")  # 新增代码+WindowsLaunchResolver：断言完整 AUMID 被保留；如果没有这一行，AppX 应用无法精确启动。
        self.assertEqual(plan["executable"], "")  # 新增代码+WindowsLaunchResolver：断言不再生成假的 exe；如果没有这一行，旧 bug 会继续隐藏。
    # 新增代码+WindowsLaunchResolver：函数段结束，test_resolver_preserves_appx_aumid_without_exe_guess 到此结束；如果没有这个边界说明，用户不容易看出 AppX 测试范围。

    def test_resolver_marks_shortcut_backend_without_shell_string(self) -> None:  # 新增代码+WindowsLaunchResolver：函数段开始，验证快捷方式候选被标记为 shortcut 后端；如果没有这段测试，开始菜单快捷方式会被误当 exe。
        module = self._resolver_module()  # 新增代码+WindowsLaunchResolver：读取 resolver 模块；如果没有这一行，测试无法调用启动解析函数。
        plan = module.resolve_windows_launch_plan(candidate={"display_name": "Obsidian", "app_name": "obsidian", "launch_id": "Obsidian.lnk", "launch_kind": "shortcut", "source": "start_menu", "installed_app_verified": True})  # 新增代码+WindowsLaunchResolver：注入开始菜单快捷方式候选；如果没有这一行，测试无法覆盖 shortcut 身份。
        self.assertTrue(plan["safe_to_launch"])  # 新增代码+WindowsLaunchResolver：断言快捷方式身份可进入启动计划；如果没有这一行，开始菜单应用会被误拒绝。
        self.assertEqual(plan["launch_backend"], "start_menu_shortcut")  # 新增代码+WindowsLaunchResolver：断言使用快捷方式后端；如果没有这一行，后端无法按快捷方式策略启动。
        self.assertEqual(plan["shortcut_id"], "Obsidian.lnk")  # 新增代码+WindowsLaunchResolver：断言快捷方式标识被保留；如果没有这一行，后续无法定位开始菜单入口。
        self.assertFalse(plan["uses_shell_string"])  # 新增代码+WindowsLaunchResolver：断言计划本身不暴露 shell 字符串；如果没有这一行，安全审计会退化。
    # 新增代码+WindowsLaunchResolver：函数段结束，test_resolver_marks_shortcut_backend_without_shell_string 到此结束；如果没有这个边界说明，用户不容易看出 shortcut 测试范围。

    def test_resolver_rejects_uninstall_registry_product_record(self) -> None:  # 新增代码+WindowsLaunchResolver：函数段开始，验证卸载注册表产品记录不能当启动入口；如果没有这段测试，设置页记录可能误导模型。
        module = self._resolver_module()  # 新增代码+WindowsLaunchResolver：读取 resolver 模块；如果没有这一行，测试无法调用启动解析函数。
        plan = module.resolve_windows_launch_plan(candidate={"display_name": "Some Product", "app_name": "some product", "launch_id": "Some Product", "launch_kind": "uninstall_record", "source": "uninstall_registry", "installed_app_verified": True})  # 新增代码+WindowsLaunchResolver：注入卸载注册表记录；如果没有这一行，测试无法覆盖不可启动来源。
        self.assertFalse(plan["safe_to_launch"])  # 新增代码+WindowsLaunchResolver：断言产品记录不可启动；如果没有这一行，resolver 可能把设置页记录送入真实 launcher。
        self.assertEqual(plan["refusal_reason"], "not_launchable_inventory_record")  # 新增代码+WindowsLaunchResolver：断言拒绝原因稳定；如果没有这一行，用户无法分辨是没找到还是来源不可启动。
        self.assertEqual(plan["launch_backend"], "")  # 新增代码+WindowsLaunchResolver：断言拒绝时没有后端；如果没有这一行，后端可能误尝试启动。
    # 新增代码+WindowsLaunchResolver：函数段结束，test_resolver_rejects_uninstall_registry_product_record 到此结束；如果没有这个边界说明，用户不容易看出拒绝测试范围。

    def test_phase108_uses_resolver_for_appx_candidate(self) -> None:  # 新增代码+WindowsLaunchResolver：函数段开始，验证 Phase108 已把 launch_plan 接到 resolver；如果没有这段测试，resolver 可能存在但主链路仍不用。
        phase108 = importlib.import_module("learning_agent.computer_use.windows_launch_resolver")  # 新增代码+WindowsLaunchResolver：读取 Phase108 通用发现模块；如果没有这一行，测试无法检查真实接入点。
        report = phase108.resolve_generic_app_launch_target("Calculator", candidates=[{"display_name": "Calculator", "app_name": "calc", "launch_id": "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App", "launch_kind": "appx", "source": "appx_package", "installed_app_verified": True}])  # 新增代码+WindowsLaunchResolver：通过 Phase108 注入 AppX 候选；如果没有这一行，测试无法证明主链路保留 AUMID。
        self.assertTrue(report["passed"])  # 新增代码+WindowsLaunchResolver：断言 Phase108 接受 AppX 启动身份；如果没有这一行，主链路仍可能只接受 exe。
        self.assertEqual(report["launch_plan"]["launch_backend"], "appx_aumid")  # 新增代码+WindowsLaunchResolver：断言 Phase108 计划来自 AUMID 后端；如果没有这一行，旧 build_launch_plan 仍可能悄悄生效。
        self.assertEqual(report["launch_plan"]["executable"], "")  # 新增代码+WindowsLaunchResolver：断言 Phase108 没有生成假 exe；如果没有这一行，旧 bug 会继续通过表面测试。
        self.assertEqual(report["best_candidate_launch_kind"], "appx")  # 新增代码+WindowsLaunchResolver：断言报告保留 AppX 类型；如果没有这一行，模型和调试输出仍看不出启动身份。
    # 新增代码+WindowsLaunchResolver：函数段结束，test_phase108_uses_resolver_for_appx_candidate 到此结束；如果没有这个边界说明，用户不容易看出主链路接入测试范围。

    def test_phase110_request_promotes_appx_to_non_argv_backend(self) -> None:  # 修改代码+WindowsMultiBackendLaunchExecutor：函数段开始，验证非 argv resolver 计划进入正式多后端请求；如果没有这段测试，AppX 会继续停在防误接旧状态。
        phase108 = importlib.import_module("learning_agent.computer_use.windows_launch_resolver")  # 新增代码+WindowsLaunchResolver：读取 Phase108 模块；如果没有这一行，测试无法生成真实主链路报告。
        backend = importlib.import_module("learning_agent.computer_use.generic_launch_backend")  # 新增代码+WindowsLaunchResolver：读取 Phase110 后端模块；如果没有这一行，测试无法检查 request 构造。
        report = phase108.resolve_generic_app_launch_target("Calculator", candidates=[{"display_name": "Calculator", "app_name": "calc", "launch_id": "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App", "launch_kind": "appx", "source": "appx_package", "installed_app_verified": True}])  # 新增代码+WindowsLaunchResolver：生成 AppX resolver 计划；如果没有这一行，测试无法复现非 argv 后端。
        request = backend.build_generic_launch_request(report, real_launch_authorized=True)  # 新增代码+WindowsLaunchResolver：把 Phase108 报告交给 Phase110 request 构造器；如果没有这一行，测试无法发现字段回填污染。
        self.assertEqual(request.executable, "")  # 修改代码+WindowsMultiBackendLaunchExecutor：断言非 argv 后端仍不填 executable；如果没有这一行，AppX 可能再次被 Popen 误用。
        self.assertEqual(request.argv(), [])  # 修改代码+WindowsMultiBackendLaunchExecutor：断言 AppX 请求没有 argv；如果没有这一行，非 argv 后端可能被伪装成空字符串 argv。
        self.assertEqual(request.launch_backend, "appx_aumid")  # 新增代码+WindowsMultiBackendLaunchExecutor：断言 Phase110 请求保留 AppX 后端；如果没有这一行，执行器无法选择正确 Windows API。
        self.assertTrue(backend.phase110_safe_launch_request(request))  # 修改代码+WindowsMultiBackendLaunchExecutor：断言 AppX 作为安全非 argv 后端可进入执行器；如果没有这一行，resolver 和 executor 会断层。
    # 修改代码+WindowsMultiBackendLaunchExecutor：函数段结束，test_phase110_request_promotes_appx_to_non_argv_backend 到此结束；如果没有这个边界说明，用户不容易看出 Phase110 AppX 接入测试范围。

    def test_phase108_cli_line_exposes_resolver_backend_for_visible_terminal(self) -> None:  # 新增代码+WindowsLaunchResolver：函数段开始，验证真实终端 token 行暴露 resolver 后端；如果没有这段测试，可见验收只能靠隐藏 JSON 推断。
        phase108 = importlib.import_module("learning_agent.computer_use.windows_launch_resolver")  # 新增代码+WindowsLaunchResolver：读取 Phase108 模块；如果没有这一行，测试无法调用 CLI 格式化器。
        report = phase108.resolve_generic_app_launch_target("Obsidian", candidates=[{"display_name": "Obsidian", "app_name": "obsidian", "launch_id": "Obsidian.exe", "launch_kind": "exe", "source": "start_menu", "installed_app_verified": True}])  # 新增代码+WindowsLaunchResolver：生成 exe resolver 报告；如果没有这一行，测试没有可格式化输入。
        line = phase108.phase108_cli_line(report)  # 新增代码+WindowsLaunchResolver：生成真实终端会打印的 token 行；如果没有这一行，测试无法覆盖用户可见输出。
        self.assertIn("resolver_launch_backend=argv_no_shell", line)  # 新增代码+WindowsLaunchResolver：断言输出包含 resolver 后端；如果没有这一行，终端验收无法证明不是旧 build_launch_plan。
        self.assertIn("safe_resolver_launch_plan=true", line)  # 新增代码+WindowsLaunchResolver：断言输出包含 resolver 级安全状态；如果没有这一行，终端验收无法区分计划失败和默认关闭。
    # 新增代码+WindowsLaunchResolver：函数段结束，test_phase108_cli_line_exposes_resolver_backend_for_visible_terminal 到此结束；如果没有这个边界说明，用户不容易看出终端输出测试范围。
# 新增代码+WindowsLaunchResolver：测试类结束，WindowsComputerUseLaunchResolverPhase124Tests 到此结束；如果没有这个边界说明，用户不容易看出 Phase124 测试集合范围。

if __name__ == "__main__":  # 新增代码+WindowsLaunchResolver：文件入口开始，允许直接运行本测试文件；如果没有这一行，初学者必须记完整 unittest 命令。
    unittest.main()  # 新增代码+WindowsLaunchResolver：启动 unittest 执行断言；如果没有这一行，直接运行文件不会跑任何测试。
# 新增代码+WindowsLaunchResolver：文件入口结束，直接运行测试到此结束；如果没有这个边界说明，用户不容易看出入口范围。
