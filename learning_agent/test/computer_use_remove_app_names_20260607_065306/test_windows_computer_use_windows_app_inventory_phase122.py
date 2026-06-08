import importlib  # 新增代码+WindowsAppInventory：导入动态模块加载工具；如果没有这一行，测试无法在新 inventory 模块缺失时给出清楚失败。
import unittest  # 新增代码+WindowsAppInventory：导入 unittest 测试框架；如果没有这一行，本文件不会被测试运行器识别。


class WindowsComputerUseWindowsAppInventoryPhase122Tests(unittest.TestCase):  # 新增代码+WindowsAppInventory：测试类开始，验证 Windows 版 ClaudeCode app inventory 设计；如果没有这个类，多源枚举架构没有回归保护。
    def _inventory_module(self):  # 新增代码+WindowsAppInventory：函数段开始，动态导入待实现 inventory 模块；如果没有这段函数，模块缺失会表现成不友好的 import error。
        try:  # 新增代码+WindowsAppInventory：尝试导入新模块；如果没有这一行，红测不能明确表达“还没有 Windows inventory 层”。
            return importlib.import_module("learning_agent.computer_use.windows_app_inventory")  # 新增代码+WindowsAppInventory：返回 Windows inventory 模块；如果没有这一行，后续测试拿不到被测 API。
        except ModuleNotFoundError as error:  # 新增代码+WindowsAppInventory：捕获模块缺失错误；如果没有这一行，失败信息不够直接。
            self.fail(f"Phase122 windows_app_inventory module is missing: {error}")  # 新增代码+WindowsAppInventory：把缺失模块转成明确失败；如果没有这一行，用户不容易知道应新增哪个文件。
    # 新增代码+WindowsAppInventory：函数段结束，_inventory_module 到此结束；如果没有这个边界说明，用户不容易看出动态导入范围。

    def test_inventory_merges_sources_dedupes_and_preserves_launch_metadata(self) -> None:  # 新增代码+WindowsAppInventory：函数段开始，验证多源融合、去重和启动元数据；如果没有这段测试，Windows inventory 可能只是另一个开始菜单扫描器。
        module = self._inventory_module()  # 新增代码+WindowsAppInventory：读取待测模块；如果没有这一行，测试无法调用统一 inventory API。
        entries = module.build_windows_app_inventory([  # 新增代码+WindowsAppInventory：传入模拟多源候选；如果没有这一行，测试无法稳定覆盖 Start Menu、App Paths、Uninstall、AppX。
            {"display_name": "Obsidian", "launch_id": "Obsidian.exe", "source": "start_menu", "launch_kind": "exe"},  # 新增代码+WindowsAppInventory：模拟可启动开始菜单候选；如果没有这一行，测试不能证明可启动项被保留。
            {"display_name": "Obsidian", "launch_id": "Obsidian.exe", "source": "uninstall_registry", "launch_kind": "uninstall_record"},  # 新增代码+WindowsAppInventory：模拟同名卸载注册表记录；如果没有这一行，测试不能证明产品记录不会覆盖可启动入口。
            {"display_name": "Calculator", "launch_id": "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App", "source": "appx_package", "launch_kind": "appx"},  # 新增代码+WindowsAppInventory：模拟 UWP/AppX 应用；如果没有这一行，测试不能证明 Windows 商店应用可进入清单。
            {"display_name": "Command Prompt", "launch_id": "cmd.exe", "source": "app_paths_registry", "launch_kind": "exe"},  # 新增代码+WindowsAppInventory：模拟高风险终端候选；如果没有这一行，测试不能证明风险分类生效。
            {"display_name": "Command line references", "launch_id": "Command line references.lnk", "source": "start_menu", "launch_kind": "shortcut"},  # 修改代码+WindowsAppInventory：模拟真实探针暴露的命令行文档入口；如果没有这一行，命令行参考资料可能继续进入普通应用清单。
            {"display_name": "Application Verifier (X64)", "launch_id": "Application Verifier (X64).lnk", "source": "start_menu", "launch_kind": "shortcut"},  # 修改代码+WindowsAppInventory：模拟真实探针暴露的调试验证工具；如果没有这一行，开发诊断工具可能继续污染模型候选。
            {"display_name": "DingTalk Official Website", "launch_id": "DingTalk Official Website.lnk", "source": "start_menu", "launch_kind": "shortcut"},  # 修改代码+WindowsAppInventory：模拟真实探针暴露的网站快捷方式；如果没有这一行，网站入口可能被当成桌面应用。
            {"display_name": "Visual Studio Installer", "launch_id": "Visual Studio Installer.lnk", "source": "start_menu", "launch_kind": "shortcut"},  # 新增代码+WindowsAppInventory：模拟安装维护入口；如果没有这一行，测试不能证明噪声分类生效。
            {"display_name": "Install Additional Tools for Node.js", "launch_id": "Install Additional Tools for Node.js.lnk", "source": "start_menu", "launch_kind": "shortcut"},  # 修改代码+WindowsAppInventory：模拟真实探针暴露的安装附加工具入口；如果没有这一行，install 类维护入口可能继续进入清单。
            {"display_name": "Task Manager", "launch_id": "Task Manager.lnk", "source": "start_menu", "launch_kind": "shortcut"},  # 修改代码+WindowsAppInventory：模拟真实验收 prompt 暴露的任务管理器入口；如果没有这一行，系统管理工具可能继续污染普通应用清单。
            {"display_name": "Python 3.14 Module Docs (64-bit)", "launch_id": "Python 3.14 Module Docs (64-bit).lnk", "source": "start_menu", "launch_kind": "shortcut"},  # 修改代码+WindowsAppInventory：模拟真实验收 prompt 暴露的文档入口；如果没有这一行，文档快捷方式可能被模型当成应用。
            {"display_name": "README", "launch_id": "README.lnk", "source": "start_menu", "launch_kind": "shortcut"},  # 修改代码+WindowsAppInventory：模拟真实验收 prompt 暴露的 README 入口；如果没有这一行，说明文件可能继续进入应用候选。
            {"display_name": "Tools for UWP Apps", "launch_id": "Tools for UWP Apps.lnk", "source": "start_menu", "launch_kind": "shortcut"},  # 修改代码+WindowsAppInventory：模拟真实验收 prompt 暴露的 SDK 工具集合入口；如果没有这一行，开发工具集合会混进普通 app 提示。
            {"display_name": "Windows Software Development Kit", "launch_id": "Windows Software Development Kit.lnk", "source": "start_menu", "launch_kind": "shortcut"},  # 修改代码+WindowsAppInventory：模拟真实验收 prompt 暴露的 SDK 产品入口；如果没有这一行，安装包/SDK 元入口可能被当成用户应用。
        ], include_common=False)  # 修改代码+WindowsAppInventory：关闭公共兜底，避免内置 Calculator 覆盖本测试注入的 AppX Calculator；如果没有这一行，测试会验证到兜底优先级而不是多源融合。
        by_name = {entry["display_name"]: entry for entry in entries}  # 新增代码+WindowsAppInventory：按显示名索引结果；如果没有这一行，断言需要重复遍历列表。
        self.assertIn("Obsidian", by_name)  # 新增代码+WindowsAppInventory：断言普通可启动应用被保留；如果没有这一行，inventory 可能误删用户应用。
        self.assertEqual(by_name["Obsidian"]["source"], "start_menu")  # 新增代码+WindowsAppInventory：断言可启动来源优先于卸载产品记录；如果没有这一行，设置页记录可能覆盖真实启动入口。
        self.assertEqual(by_name["Obsidian"]["launch_kind"], "exe")  # 新增代码+WindowsAppInventory：断言启动类型被保留；如果没有这一行，后续 resolver 不知道怎么启动。
        self.assertIn("Calculator", by_name)  # 新增代码+WindowsAppInventory：断言 AppX 应用被保留；如果没有这一行，Windows 商店应用会被漏掉。
        self.assertEqual(by_name["Calculator"]["launch_kind"], "appx")  # 新增代码+WindowsAppInventory：断言 AppX 启动类型不被改成 exe；如果没有这一行，UWP 应用启动会走错后端。
        self.assertNotIn("Command Prompt", by_name)  # 新增代码+WindowsAppInventory：断言高风险终端不进入模型可见普通清单；如果没有这一行，模型可能把终端当普通应用。
        self.assertNotIn("Command line references", by_name)  # 修改代码+WindowsAppInventory：断言命令行文档入口不进入模型可见清单；如果没有这一行，模型候选仍会混入文档链接。
        self.assertNotIn("Application Verifier (X64)", by_name)  # 修改代码+WindowsAppInventory：断言调试验证工具不进入模型可见清单；如果没有这一行，模型候选仍会混入诊断工具。
        self.assertNotIn("DingTalk Official Website", by_name)  # 修改代码+WindowsAppInventory：断言官网快捷方式不进入模型可见清单；如果没有这一行，网站链接会被误当桌面应用。
        self.assertNotIn("Visual Studio Installer", by_name)  # 新增代码+WindowsAppInventory：断言安装维护入口不进入模型可见普通清单；如果没有这一行，模型可能选择安装器而不是应用本体。
        self.assertNotIn("Install Additional Tools for Node.js", by_name)  # 修改代码+WindowsAppInventory：断言安装附加工具入口不进入模型可见清单；如果没有这一行，模型可能启动维护流程。
        self.assertNotIn("Task Manager", by_name)  # 修改代码+WindowsAppInventory：断言任务管理器不进入普通应用清单；如果没有这一行，模型可能误选系统管理入口。
        self.assertNotIn("Python 3.14 Module Docs (64-bit)", by_name)  # 修改代码+WindowsAppInventory：断言模块文档入口不进入普通应用清单；如果没有这一行，模型可能打开文档而不是应用。
        self.assertNotIn("README", by_name)  # 修改代码+WindowsAppInventory：断言 README 说明文件不进入普通应用清单；如果没有这一行，模型可能打开说明文件。
        self.assertNotIn("Tools for UWP Apps", by_name)  # 修改代码+WindowsAppInventory：断言 SDK 工具集合入口不进入普通应用清单；如果没有这一行，模型候选会继续混入元工具入口。
        self.assertNotIn("Windows Software Development Kit", by_name)  # 修改代码+WindowsAppInventory：断言 Windows SDK 元入口不进入普通应用清单；如果没有这一行，模型可能打开安装/文档集合而非用户应用。
    # 新增代码+WindowsAppInventory：函数段结束，test_inventory_merges_sources_dedupes_and_preserves_launch_metadata 到此结束；如果没有这个边界说明，用户不容易看出多源融合测试范围。

    def test_inventory_formats_claudecode_style_model_hints_without_paths(self) -> None:  # 新增代码+WindowsAppInventory：函数段开始，验证模型提示像 ClaudeCode 一样只给清洗候选；如果没有这段测试，raw path 可能泄露进 prompt。
        module = self._inventory_module()  # 新增代码+WindowsAppInventory：读取待测模块；如果没有这一行，测试无法调用格式化 API。
        text = module.format_windows_app_inventory_for_model([  # 新增代码+WindowsAppInventory：格式化模拟 inventory；如果没有这一行，测试无法检查模型可见文本。
            {"display_name": "Paint", "launch_id": "C:/Users/demo/Paint.lnk", "app_name": "mspaint", "source": "start_menu", "launch_kind": "exe", "aliases": ("画图",)},  # 新增代码+WindowsAppInventory：传入带路径的候选；如果没有这一行，测试不能证明路径会被隐藏。
        ])  # 新增代码+WindowsAppInventory：候选列表结束；如果没有这一行，Python 语法不完整。
        self.assertIn("Available desktop application candidates", text)  # 新增代码+WindowsAppInventory：断言输出有稳定标题；如果没有这一行，模型上下文不容易定位候选区域。
        self.assertIn("not a hard whitelist", text)  # 新增代码+WindowsAppInventory：断言清单只是提示不是限制；如果没有这一行，设计可能退化成硬白名单。
        self.assertIn("Paint [app_name=mspaint, launch_kind=exe, source=start_menu]", text)  # 新增代码+WindowsAppInventory：断言模型看到可启动短名和来源；如果没有这一行，模型仍可能猜错启动方式。
        self.assertNotIn("C:/Users/demo/Paint.lnk", text)  # 新增代码+WindowsAppInventory：断言原始路径不进入模型提示；如果没有这一行，用户路径可能泄露。
    # 新增代码+WindowsAppInventory：函数段结束，test_inventory_formats_claudecode_style_model_hints_without_paths 到此结束；如果没有这个边界说明，用户不容易看出模型提示测试范围。

    def test_inventory_resolves_user_app_hint_without_app_names_module(self) -> None:  # 修改代码+WindowsAppInventory：函数段开始，验证应用名解析已经归入统一 inventory；如果没有这段测试，app_names.py 删除后可能没人保护中文别名解析。
        module = self._inventory_module()  # 修改代码+WindowsAppInventory：读取统一 inventory 模块；如果没有这一行，测试无法证明新入口承担旧解析职责。
        catalog = module.build_windows_app_inventory([  # 修改代码+WindowsAppInventory：构造带中文别名的 Paint 候选；如果没有这一行，测试只能依赖真实机器环境导致不稳定。
            {"display_name": "Paint", "app_name": "mspaint", "launch_id": "mspaint.exe", "source": "start_menu", "launch_kind": "exe", "aliases": ("画图", "画图软件", "paint", "mspaint.exe")},  # 修改代码+WindowsAppInventory：提供 Paint 的别名集合；如果没有这一行，无法验证中文和 exe 别名都能解析。
        ], include_common=False)  # 修改代码+WindowsAppInventory：关闭公共兜底以便精确验证传入候选；如果没有这一行，测试可能被默认 Paint 兜底掩盖问题。
        self.assertEqual(module.resolve_windows_app_name_hint("画图", catalog), "mspaint")  # 修改代码+WindowsAppInventory：断言中文应用名解析为稳定 app_name；如果没有这一行，模型仍可能把中文名传给启动器。
        self.assertEqual(module.resolve_windows_app_name_hint("mspaint.exe", catalog), "mspaint")  # 修改代码+WindowsAppInventory：断言 exe 形式也解析为短 app_name；如果没有这一行，启动名可能在 exe 和短名之间摇摆。
        self.assertEqual(module.resolve_windows_app_name_hint("未知软件", catalog), "")  # 修改代码+WindowsAppInventory：断言未知软件不乱匹配；如果没有这一行，解析器可能误启动错误应用。
    # 修改代码+WindowsAppInventory：函数段结束，test_inventory_resolves_user_app_hint_without_app_names_module 到此结束；如果没有这个边界说明，用户不容易看出解析迁移测试范围。


if __name__ == "__main__":  # 新增代码+WindowsAppInventory：文件入口开始，允许直接运行本测试文件；如果没有这一行，初学者必须记完整 unittest 命令。
    unittest.main()  # 新增代码+WindowsAppInventory：启动 unittest；如果没有这一行，直接执行不会运行断言。
# 新增代码+WindowsAppInventory：文件入口结束，直接运行测试到此结束；如果没有这个边界说明，用户不容易看出入口范围。
