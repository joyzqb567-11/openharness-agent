import os  # 新增代码+AppLaunchInventoryClosure：导入环境变量工具，用来把开始菜单扫描隔离到临时目录；如果没有这一行，测试会误扫用户真实开始菜单。
import tempfile  # 新增代码+AppLaunchInventoryClosure：导入临时目录工具，用来创建不会污染项目的假开始菜单；如果没有这一行，测试样本可能写到真实工作区。
import unittest  # 新增代码+AppLaunchInventoryClosure：导入 unittest 框架，用来把发现到启动的闭环写成可回归测试；如果没有这一行，测试文件不会被标准测试运行器识别。
from pathlib import Path  # 新增代码+AppLaunchInventoryClosure：导入 Path 工具，用来安全拼接 Windows 风格目录；如果没有这一行，路径拼接容易在不同环境下出错。
from unittest.mock import patch  # 新增代码+AppLaunchInventoryClosure：导入 patch 工具，用来伪造环境变量和 PowerShell 枚举结果；如果没有这一行，测试会依赖真实机器状态。

from learning_agent.computer_use import windows_app_inventory  # 新增代码+AppLaunchInventoryClosure：导入当前应用库存模块，用真实源码验证发现层；如果没有这一行，测试无法证明 inventory 是否接通。
from learning_agent.computer_use import windows_launch_resolver  # 新增代码+AppLaunchInventoryClosure：导入当前启动 resolver，用真实源码验证启动计划；如果没有这一行，测试无法证明发现结果能被启动层消费。


class WindowsComputerUseAppLaunchInventoryClosurePhase134Tests(unittest.TestCase):  # 新增代码+AppLaunchInventoryClosure：测试类开始，集中验证普通应用从枚举到启动计划的闭环；如果没有这个类，AppX 和 shortcut 断点会继续散落在旧测试里。
    def test_start_menu_discovery_preserves_shortcut_launch_backend(self) -> None:  # 新增代码+AppLaunchInventoryClosure：函数段开始，验证开始菜单快捷方式不能再被猜成 exe；如果没有这段测试，普通应用快捷方式会继续走错启动后端。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+AppLaunchInventoryClosure：创建隔离的临时开始菜单目录；如果没有这一行，测试会污染或依赖用户真实系统菜单。
            start_menu_dir = Path(temp_dir) / "Microsoft" / "Windows" / "Start Menu" / "Programs"  # 新增代码+AppLaunchInventoryClosure：拼出 Windows 用户级开始菜单目录结构；如果没有这一行，枚举函数找不到测试快捷方式。
            start_menu_dir.mkdir(parents=True)  # 新增代码+AppLaunchInventoryClosure：创建测试开始菜单目录；如果没有这一行，写入快捷方式文件会失败。
            (start_menu_dir / "Sample Drawing App.lnk").write_text("", encoding="utf-8")  # 新增代码+AppLaunchInventoryClosure：放入一个普通应用快捷方式样本；如果没有这一行，枚举函数没有可验证的 shortcut 输入。
            fake_program_data = str(Path(temp_dir) / "empty-program-data")  # 新增代码+AppLaunchInventoryClosure：准备一个不存在的公共开始菜单目录；如果没有这一行，测试仍可能扫描真实 ProgramData。
            with patch.dict(os.environ, {"APPDATA": temp_dir, "ProgramData": fake_program_data}, clear=False):  # 新增代码+AppLaunchInventoryClosure：把开始菜单扫描限定到临时目录；如果没有这一行，测试会误读真实机器安装应用。
                entries = windows_app_inventory._inventory_discover_start_menu(max_scan=10)  # 新增代码+AppLaunchInventoryClosure：运行真实开始菜单枚举函数；如果没有这一行，无法证明发现层输出给 resolver 的类型正确。
        self.assertEqual("Sample Drawing App", entries[0]["display_name"])  # 新增代码+AppLaunchInventoryClosure：确认显示名仍是用户可读名称；如果没有这一行，模型可能看到带后缀或路径的脏名称。
        self.assertEqual("Sample Drawing App.lnk", entries[0]["launch_id"])  # 新增代码+AppLaunchInventoryClosure：确认启动标识保留快捷方式文件名；如果没有这一行，真实 launcher 无法准确定位开始菜单入口。
        self.assertEqual("shortcut", entries[0]["launch_kind"])  # 新增代码+AppLaunchInventoryClosure：确认启动类型是 shortcut 而不是 exe；如果没有这一行，resolver 会继续误走 Popen 后端。
    # 新增代码+AppLaunchInventoryClosure：函数段结束，test_start_menu_discovery_preserves_shortcut_launch_backend 到此结束；如果没有这个边界说明，用户不容易看出 shortcut 枚举测试范围。

    def test_appx_discovery_reads_start_apps_aumid_candidates(self) -> None:  # 新增代码+AppLaunchInventoryClosure：函数段开始，验证 AppX/AUMID 能从 Windows StartApps 枚举进入库存；如果没有这段测试，商店应用仍可能完全不可发现。
        completed = type("CompletedProcess", (), {"stdout": '[{"Name":"Calculator","AppID":"Microsoft.WindowsCalculator_8wekyb3d8bbwe!App"}]', "returncode": 0})()  # 新增代码+AppLaunchInventoryClosure：构造 PowerShell Get-StartApps 的 JSON 输出；如果没有这一行，测试会依赖真实 Windows 应用列表。
        with patch.object(windows_app_inventory.subprocess, "run", return_value=completed) as run_mock:  # 新增代码+AppLaunchInventoryClosure：伪造只读枚举命令结果；如果没有这一行，单元测试会真的调用 PowerShell。
            entries = windows_app_inventory._inventory_discover_appx_packages()  # 新增代码+AppLaunchInventoryClosure：执行 AppX 枚举函数；如果没有这一行，无法证明 AUMID 会进入 inventory 源。
        self.assertTrue(run_mock.called)  # 新增代码+AppLaunchInventoryClosure：确认枚举函数确实调用 StartApps 后端；如果没有这一行，测试可能只验证了假数据旁路。
        self.assertEqual("Calculator", entries[0]["display_name"])  # 新增代码+AppLaunchInventoryClosure：确认 AppX 显示名保留给模型选择；如果没有这一行，模型可能看不到用户熟悉的软件名。
        self.assertEqual("Microsoft.WindowsCalculator_8wekyb3d8bbwe!App", entries[0]["launch_id"])  # 新增代码+AppLaunchInventoryClosure：确认完整 AUMID 被保留；如果没有这一行，AppX 后端无法真实启动目标。
        self.assertEqual("appx", entries[0]["launch_kind"])  # 新增代码+AppLaunchInventoryClosure：确认 AppX 候选不会被压扁成 exe；如果没有这一行，resolver 会继续走错后端。
        self.assertEqual("appx_package", entries[0]["source"])  # 新增代码+AppLaunchInventoryClosure：确认来源是 AppX 包枚举；如果没有这一行，maturity 无法区分真实 AUMID 来源。
    # 新增代码+AppLaunchInventoryClosure：函数段结束，test_appx_discovery_reads_start_apps_aumid_candidates 到此结束；如果没有这个边界说明，用户不容易看出 AppX 枚举测试范围。

    def test_resolver_marks_appx_and_shortcut_as_phase110_supported(self) -> None:  # 新增代码+AppLaunchInventoryClosure：函数段开始，验证非 argv 后端已经被 resolver 标记为可真实执行；如果没有这段测试，旧“尚未接通”状态会继续误导 maturity。
        appx_plan = windows_launch_resolver.resolve_windows_launch_plan(candidate={"display_name": "Calculator", "app_name": "calculator", "launch_id": "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App", "launch_kind": "appx", "source": "appx_package", "installed_app_verified": True})  # 新增代码+AppLaunchInventoryClosure：生成 AppX 启动计划；如果没有这一行，测试无法覆盖 AUMID 后端支持状态。
        shortcut_plan = windows_launch_resolver.resolve_windows_launch_plan(candidate={"display_name": "Sample Drawing App", "app_name": "sampledrawingapp", "launch_id": "Sample Drawing App.lnk", "launch_kind": "shortcut", "source": "start_menu", "installed_app_verified": True})  # 新增代码+AppLaunchInventoryClosure：生成快捷方式启动计划；如果没有这一行，测试无法覆盖 shortcut 后端支持状态。
        self.assertTrue(appx_plan["phase110_backend_supported"])  # 新增代码+AppLaunchInventoryClosure：确认 AppX 后端被标记为 Phase110 已支持；如果没有这一行，报告会继续说真实启动未接通。
        self.assertEqual("supported_by_phase110_appx_aumid", appx_plan["phase110_backend_support_reason"])  # 新增代码+AppLaunchInventoryClosure：确认 AppX 支持原因指向真实 AUMID 后端；如果没有这一行，后续读报告仍无法判断接线依据。
        self.assertTrue(shortcut_plan["phase110_backend_supported"])  # 新增代码+AppLaunchInventoryClosure：确认快捷方式后端被标记为 Phase110 已支持；如果没有这一行，开始菜单普通应用仍会被误判为未接通。
        self.assertEqual("supported_by_phase110_start_menu_shortcut", shortcut_plan["phase110_backend_support_reason"])  # 新增代码+AppLaunchInventoryClosure：确认 shortcut 支持原因指向真实 ShellExecute 快捷方式后端；如果没有这一行，后续读报告仍无法判断接线依据。
    # 新增代码+AppLaunchInventoryClosure：函数段结束，test_resolver_marks_appx_and_shortcut_as_phase110_supported 到此结束；如果没有这个边界说明，用户不容易看出 resolver 支持状态测试范围。
# 新增代码+AppLaunchInventoryClosure：测试类结束，WindowsComputerUseAppLaunchInventoryClosurePhase134Tests 到此结束；如果没有这个边界说明，用户不容易看出闭环测试集合范围。


if __name__ == "__main__":  # 新增代码+AppLaunchInventoryClosure：文件入口开始，允许直接运行本测试文件；如果没有这一行，初学者必须记完整 unittest 命令。
    unittest.main()  # 新增代码+AppLaunchInventoryClosure：启动 unittest；如果没有这一行，直接执行文件不会跑任何断言。
# 新增代码+AppLaunchInventoryClosure：文件入口结束，直接运行测试到此结束；如果没有这个边界说明，用户不容易看出入口范围。
