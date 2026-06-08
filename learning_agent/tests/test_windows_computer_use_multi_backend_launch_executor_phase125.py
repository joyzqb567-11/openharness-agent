import importlib  # 新增代码+WindowsMultiBackendLaunchExecutor：导入动态模块加载工具；如果没有这一行，测试无法在实现缺失时准确指出哪个模块未接好多后端执行器。
import unittest  # 新增代码+WindowsMultiBackendLaunchExecutor：导入 unittest 测试框架；如果没有这一行，本测试文件不能被项目标准测试命令执行。


class Phase125FakeNativeLauncher:  # 新增代码+WindowsMultiBackendLaunchExecutor：类段开始，模拟 Windows 原生启动器；如果没有这个 fake，生产后端测试就可能真的打开用户电脑上的应用。
    def __init__(self) -> None:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，初始化 fake 调用记录；如果没有这段函数，测试无法知道后端到底调用了哪个启动分支。
        self.argv_calls: list[list[str]] = []  # 新增代码+WindowsMultiBackendLaunchExecutor：记录 argv 启动调用；如果没有这一行，测试无法证明 exe 后端没有被 AppX/shortcut 误用。
        self.appx_calls: list[str] = []  # 新增代码+WindowsMultiBackendLaunchExecutor：记录 AppX/AUMID 启动调用；如果没有这一行，测试无法证明 AUMID 进入了正确后端。
        self.shortcut_calls: list[str] = []  # 新增代码+WindowsMultiBackendLaunchExecutor：记录 shortcut 启动调用；如果没有这一行，测试无法证明开始菜单快捷方式进入了正确后端。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，Phase125FakeNativeLauncher.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake 初始化范围。

    def launch_argv(self, argv: list[str]) -> dict[str, object]:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，模拟 Win32 argv 启动；如果没有这段函数，生产后端测试无法覆盖普通 exe 分支。
        self.argv_calls.append(list(argv))  # 新增代码+WindowsMultiBackendLaunchExecutor：保存 argv 调用参数；如果没有这一行，测试无法断言 shell 字符串没有出现。
        return {"ok": True, "process_started": True, "process_id": 12501, "process_object": None}  # 新增代码+WindowsMultiBackendLaunchExecutor：返回假进程身份；如果没有这一行，生产后端无法继续登记自有进程。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，Phase125FakeNativeLauncher.launch_argv 到此结束；如果没有这个边界说明，用户不容易看出 argv fake 范围。

    def launch_appx_aumid(self, aumid: str) -> dict[str, object]:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，模拟 AppX/AUMID 启动；如果没有这段函数，测试会被迫用 explorer 或 ShellExecute 真开应用。
        self.appx_calls.append(str(aumid))  # 新增代码+WindowsMultiBackendLaunchExecutor：保存 AUMID 调用参数；如果没有这一行，测试无法证明 Calculator 没有被误当 calc.exe。
        return {"ok": True, "process_started": True, "process_id": 12502, "process_object": None}  # 新增代码+WindowsMultiBackendLaunchExecutor：返回假进程身份；如果没有这一行，生产后端无法形成统一启动报告。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，Phase125FakeNativeLauncher.launch_appx_aumid 到此结束；如果没有这个边界说明，用户不容易看出 AppX fake 范围。

    def launch_start_menu_shortcut(self, shortcut_id: str) -> dict[str, object]:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，模拟开始菜单快捷方式启动；如果没有这段函数，测试无法覆盖 shortcut 后端。
        self.shortcut_calls.append(str(shortcut_id))  # 新增代码+WindowsMultiBackendLaunchExecutor：保存快捷方式标识；如果没有这一行，测试无法证明 shortcut 没有退回 exe 猜测。
        return {"ok": True, "process_started": True, "process_id": 12503, "process_object": None}  # 新增代码+WindowsMultiBackendLaunchExecutor：返回假进程身份；如果没有这一行，生产后端无法登记自有资源。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，Phase125FakeNativeLauncher.launch_start_menu_shortcut 到此结束；如果没有这个边界说明，用户不容易看出 shortcut fake 范围。
# 新增代码+WindowsMultiBackendLaunchExecutor：类段结束，Phase125FakeNativeLauncher 到此结束；如果没有这个边界说明，用户不容易看出 fake 启动器范围。


class WindowsComputerUseMultiBackendLaunchExecutorPhase125Tests(unittest.TestCase):  # 新增代码+WindowsMultiBackendLaunchExecutor：类段开始，验证 Phase110 从单 argv 后端升级为多后端执行器；如果没有这个类，AppX/shortcut 很容易再次误接 Popen。
    def _backend_module(self):  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，统一导入 Phase110 后端模块；如果没有这段函数，模块路径变更时失败会散落在多个测试里。
        return importlib.import_module("learning_agent.computer_use.generic_launch_backend")  # 新增代码+WindowsMultiBackendLaunchExecutor：返回 generic_launch_backend 模块；如果没有这一行，测试拿不到请求和后端类。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，_backend_module 到此结束；如果没有这个边界说明，用户不容易看出模块导入范围。

    def _appx_report(self) -> dict[str, object]:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，构造 AppX/AUMID Phase108 报告样本；如果没有这段函数，每个测试都会复制一大段不利于维护。
        return {"passed": True, "canonical_target": "calc", "high_risk_refused": False, "launch_plan": {"safe_to_launch": True, "launch_backend": "appx_aumid", "launch_verb": "ShellExecuteAppUserModelId", "command_shape": "aumid_no_shell", "aumid": "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App", "executable": "", "arguments": [], "changes_registry": False, "changes_system_settings": False, "requires_admin": False, "uses_shell_string": False, "actions_expanded": False}}  # 新增代码+WindowsMultiBackendLaunchExecutor：返回安全 AppX 启动计划；如果没有这一行，测试无法表达“安全但不是 argv”的新合同。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，_appx_report 到此结束；如果没有这个边界说明，用户不容易看出 AppX 样本范围。

    def _shortcut_report(self) -> dict[str, object]:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，构造开始菜单 shortcut Phase108 报告样本；如果没有这段函数，shortcut 后端测试会重复样本结构。
        return {"passed": True, "canonical_target": "obsidian", "high_risk_refused": False, "launch_plan": {"safe_to_launch": True, "launch_backend": "start_menu_shortcut", "launch_verb": "ShellExecuteShortcut", "command_shape": "shortcut_no_shell", "shortcut_id": "Obsidian.lnk", "executable": "", "arguments": [], "changes_registry": False, "changes_system_settings": False, "requires_admin": False, "uses_shell_string": False, "actions_expanded": False}}  # 新增代码+WindowsMultiBackendLaunchExecutor：返回安全 shortcut 启动计划；如果没有这一行，测试无法证明快捷方式不再被当 exe 猜。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，_shortcut_report 到此结束；如果没有这个边界说明，用户不容易看出 shortcut 样本范围。

    def test_appx_request_is_safe_non_argv_backend(self) -> None:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，验证 AppX 请求在 Phase110 内成为安全后端；如果没有这个测试，AppX 会继续停在“不可执行”的旧边界。
        module = self._backend_module()  # 新增代码+WindowsMultiBackendLaunchExecutor：读取后端模块；如果没有这一行，后续没有被测对象。
        request = module.build_generic_launch_request(self._appx_report(), real_launch_authorized=True)  # 新增代码+WindowsMultiBackendLaunchExecutor：把 AppX 报告转换成 Phase110 请求；如果没有这一行，无法发现请求结构是否保留 AUMID。
        self.assertEqual(request.launch_backend, "appx_aumid")  # 新增代码+WindowsMultiBackendLaunchExecutor：断言请求保留 AppX 后端；如果没有这一行，执行层可能仍只知道 argv。
        self.assertEqual(request.aumid, "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App")  # 新增代码+WindowsMultiBackendLaunchExecutor：断言请求保留完整 AUMID；如果没有这一行，真实启动无法精确定位 UWP 应用。
        self.assertEqual(request.argv(), [])  # 新增代码+WindowsMultiBackendLaunchExecutor：断言 AppX 不产生 argv；如果没有这一行，非 argv 后端可能再次误进 Popen。
        self.assertTrue(module.phase110_safe_launch_request(request))  # 新增代码+WindowsMultiBackendLaunchExecutor：断言 AppX 安全计划可进入多后端执行器；如果没有这一行，resolver 做完也无法启动商店应用。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，test_appx_request_is_safe_non_argv_backend 到此结束；如果没有这个边界说明，用户不容易看出 AppX request 测试范围。

    def test_recording_backend_records_appx_without_shell_or_argv(self) -> None:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，验证记录型后端支持 AppX 合同；如果没有这个测试，自动化只能覆盖 exe 后端。
        module = self._backend_module()  # 新增代码+WindowsMultiBackendLaunchExecutor：读取后端模块；如果没有这一行，测试无法创建记录型后端。
        backend = module.Phase110RecordingGenericLaunchBackend()  # 新增代码+WindowsMultiBackendLaunchExecutor：创建记录型后端；如果没有这一行，测试无法在零副作用下检查 AppX 请求。
        report = module.run_generic_launch_backend(self._appx_report(), enable_real_launch=True, backend=backend)  # 新增代码+WindowsMultiBackendLaunchExecutor：授权 AppX 报告进入记录后端；如果没有这一行，多后端路径没有事实输出。
        self.assertEqual(len(backend.launches), 1)  # 新增代码+WindowsMultiBackendLaunchExecutor：断言后端收到一次调用；如果没有这一行，AppX 可能仍被前置拒绝。
        self.assertEqual(backend.launches[0]["launch_backend"], "appx_aumid")  # 新增代码+WindowsMultiBackendLaunchExecutor：断言记录请求后端为 AppX；如果没有这一行，记录层可能仍显示 argv。
        self.assertEqual(backend.launches[0]["argv"], [])  # 新增代码+WindowsMultiBackendLaunchExecutor：断言记录请求没有 argv；如果没有这一行，shell/argv 风险不可见。
        self.assertFalse(backend.launches[0]["uses_shell_string"])  # 新增代码+WindowsMultiBackendLaunchExecutor：断言 AppX 请求不使用 shell 字符串；如果没有这一行，安全边界无法审计。
        self.assertTrue(report["owned_process_registered"])  # 新增代码+WindowsMultiBackendLaunchExecutor：断言记录型路径仍登记自有资源；如果没有这一行，后续窗口绑定没有所有权基准。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，test_recording_backend_records_appx_without_shell_or_argv 到此结束；如果没有这个边界说明，用户不容易看出记录型 AppX 测试范围。

    def test_production_backend_dispatches_appx_to_native_launcher(self) -> None:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，验证生产后端把 AppX 分发给 AUMID 启动器；如果没有这个测试，生产路径可能继续调用 Popen。
        module = self._backend_module()  # 新增代码+WindowsMultiBackendLaunchExecutor：读取后端模块；如果没有这一行，测试无法创建生产后端。
        launcher = Phase125FakeNativeLauncher()  # 新增代码+WindowsMultiBackendLaunchExecutor：创建假原生启动器；如果没有这一行，测试可能真的打开计算器。
        backend = module.Phase110ProductionGenericLaunchBackend(platform="win32", native_launcher=launcher)  # 新增代码+WindowsMultiBackendLaunchExecutor：把 fake 注入生产后端；如果没有这一行，测试无法隔离真实 Windows API。
        report = module.run_generic_launch_backend(self._appx_report(), enable_real_launch=True, backend=backend)  # 新增代码+WindowsMultiBackendLaunchExecutor：授权 AppX 进入生产后端；如果没有这一行，无法验证真实分发路径。
        self.assertEqual(launcher.appx_calls, ["Microsoft.WindowsCalculator_8wekyb3d8bbwe!App"])  # 新增代码+WindowsMultiBackendLaunchExecutor：断言调用了 AUMID 分支；如果没有这一行，AppX 可能仍被当 exe。
        self.assertEqual(launcher.argv_calls, [])  # 新增代码+WindowsMultiBackendLaunchExecutor：断言没有调用 argv 分支；如果没有这一行，Popen 误接无法被发现。
        self.assertTrue(report["process_started"])  # 新增代码+WindowsMultiBackendLaunchExecutor：断言生产报告显示启动已发出；如果没有这一行，上层不知道是否继续找窗口。
        self.assertEqual(report["launch_backend"], "appx_aumid")  # 新增代码+WindowsMultiBackendLaunchExecutor：断言最终报告暴露真实后端；如果没有这一行，终端无法证明多后端生效。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，test_production_backend_dispatches_appx_to_native_launcher 到此结束；如果没有这个边界说明，用户不容易看出生产 AppX 测试范围。

    def test_production_backend_dispatches_shortcut_to_native_launcher(self) -> None:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，验证生产后端把 shortcut 分发给快捷方式启动器；如果没有这个测试，开始菜单应用可能继续被猜成 exe。
        module = self._backend_module()  # 新增代码+WindowsMultiBackendLaunchExecutor：读取后端模块；如果没有这一行，测试无法创建生产后端。
        launcher = Phase125FakeNativeLauncher()  # 新增代码+WindowsMultiBackendLaunchExecutor：创建假原生启动器；如果没有这一行，测试可能真的打开 Obsidian。
        backend = module.Phase110ProductionGenericLaunchBackend(platform="win32", native_launcher=launcher)  # 新增代码+WindowsMultiBackendLaunchExecutor：注入 fake launcher；如果没有这一行，无法证明分支选择。
        report = module.run_generic_launch_backend(self._shortcut_report(), enable_real_launch=True, backend=backend)  # 新增代码+WindowsMultiBackendLaunchExecutor：授权 shortcut 报告进入生产后端；如果没有这一行，shortcut 执行路径没有输出。
        self.assertEqual(launcher.shortcut_calls, ["Obsidian.lnk"])  # 新增代码+WindowsMultiBackendLaunchExecutor：断言调用了快捷方式分支；如果没有这一行，shortcut 可能被错误忽略。
        self.assertEqual(launcher.argv_calls, [])  # 新增代码+WindowsMultiBackendLaunchExecutor：断言没有退回 argv 分支；如果没有这一行，开始菜单快捷方式仍可能被 Popen 误接。
        self.assertTrue(report["process_started"])  # 新增代码+WindowsMultiBackendLaunchExecutor：断言启动请求已发出；如果没有这一行，上层无法继续做窗口绑定。
        self.assertEqual(report["launch_backend"], "start_menu_shortcut")  # 新增代码+WindowsMultiBackendLaunchExecutor：断言最终报告保留 shortcut 后端；如果没有这一行，终端验收看不出走了哪条路。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，test_production_backend_dispatches_shortcut_to_native_launcher 到此结束；如果没有这个边界说明，用户不容易看出生产 shortcut 测试范围。
# 新增代码+WindowsMultiBackendLaunchExecutor：类段结束，WindowsComputerUseMultiBackendLaunchExecutorPhase125Tests 到此结束；如果没有这个边界说明，用户不容易看出 Phase125 测试集合范围。


if __name__ == "__main__":  # 新增代码+WindowsMultiBackendLaunchExecutor：文件入口段开始，允许直接运行本测试文件；如果没有这一行，用户必须记完整 unittest 命令。
    unittest.main()  # 新增代码+WindowsMultiBackendLaunchExecutor：启动 unittest；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+WindowsMultiBackendLaunchExecutor：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，用户不容易看出脚本入口范围。
