"""阶段 14 纯新架构防回流测试。"""  # 修改代码+Stage14硬清理测试: 说明本文件专门防止旧入口、旧聚合测试和旧兼容层回流；若没有这行代码，维护者不清楚本测试的纯新架构目标。
from __future__ import annotations  # 修改代码+Stage14硬清理测试: 延迟解析类型注解；若没有这行代码，测试在部分 Python 版本上更容易受定义顺序影响。
import unittest  # 修改代码+Stage14硬清理测试: 使用标准 unittest 编写防回流测试；若没有这行代码，测试发现器无法运行测试类。
from pathlib import Path  # 修改代码+Stage14硬清理测试: 用 Path 定位项目文件；若没有这行代码，测试只能硬编码 Windows 路径。


class CompatibilityCleanupTests(unittest.TestCase):  # 修改代码+Stage14硬清理测试: 聚合纯新架构防回流测试；若没有这行代码，旧入口删除规则无法被 unittest 发现。
    project_root = Path(__file__).resolve().parents[2]  # 修改代码+Stage14硬清理测试: 定位 OpenHarness-main 项目根；若没有这行代码，源码扫描无法找到被测文件。

    def test_runtime_modules_do_not_import_legacy_entry(self) -> None:  # 修改代码+Stage14硬清理测试: 检查生产模块不再导入旧 learning_agent.learning_agent；若没有这行代码，旧脚本入口依赖可能悄悄回流。
        checked_paths = [  # 修改代码+Stage14硬清理测试: 列出已经硬切的新生产模块；若没有这行代码，扫描范围不明确。
            "learning_agent/tools/catalog.py",  # 修改代码+Stage14硬清理测试: 工具目录必须走 tools.schemas；若没有这行代码，catalog 回流不会被发现。
            "learning_agent/mcp/runtime.py",  # 修改代码+Stage14硬清理测试: MCP runtime 必须走 tools.catalog 和 tools.schemas；若没有这行代码，MCP 回流不会被发现。
            "learning_agent/models/adapters.py",  # 修改代码+Stage14硬清理测试: 模型输出协议必须走 tools.schemas；若没有这行代码，模型层回流不会被发现。
            "learning_agent/app/cli.py",  # 修改代码+Stage14硬清理测试: CLI 依赖解析必须走 core.agent；若没有这行代码，app 层回流不会被发现。
            "learning_agent/__init__.py",  # 修改代码+Stage14硬清理测试: 包门面必须走新模块；若没有这行代码，包级导出回流不会被发现。
        ]  # 修改代码+Stage14硬清理测试: 结束扫描文件列表；若没有这行代码，Python 列表语法不完整。
        for relative_path in checked_paths:  # 修改代码+Stage14硬清理测试: 逐个扫描生产文件；若没有这行代码，只能检查一个文件。
            source = (self.project_root / relative_path).read_text(encoding="utf-8")  # 修改代码+Stage14硬清理测试: 读取源码文本；若没有这行代码，断言没有检查对象。
            self.assertNotIn("learning_agent.learning_agent", source, relative_path)  # 修改代码+Stage14硬清理测试: 禁止生产模块再导入旧脚本入口；若没有这行代码，纯新入口目标没有保护。

    def test_active_test_and_helper_modules_do_not_import_legacy_entry(self) -> None:  # 修改代码+Stage14硬清理测试: 检查活跃测试和辅助脚本不再依赖旧脚本入口；若没有这行代码，测试拆分后仍可能倒逼旧入口兼容。
        legacy_entry = "learning_agent" + ".learning_agent"  # 修改代码+Stage14硬清理测试: 用拼接方式表达旧入口字符串；若没有这行代码，本测试源码自身会干扰静态扫描。
        checked_paths = [  # 修改代码+Stage14硬清理测试: 列出要扫描的活跃非归档文件；若没有这行代码，测试范围不清楚。
            "learning_agent/tests/support.py",  # 修改代码+Stage14硬清理测试: 共享测试 helper 必须走新模块；若没有这行代码，旧测试支撑层回流不会被发现。
            "learning_agent/tests/test_core_run_loop.py",  # 修改代码+Stage14硬清理测试: 核心测试模块必须不再导入旧脚本入口；若没有这行代码，核心回归可能重新依赖旧入口。
            "learning_agent/tests/test_mcp_registry.py",  # 修改代码+Stage14硬清理测试: MCP 测试模块必须不再导入旧脚本入口；若没有这行代码，MCP 回归可能重新依赖旧入口。
            "learning_agent/fake_model_repl.py",  # 修改代码+Stage14硬清理测试: 假模型交互脚本必须改走新入口；若没有这行代码，开发辅助脚本仍会误导维护者。
        ]  # 修改代码+Stage14硬清理测试: 结束扫描文件列表；若没有这行代码，Python 列表语法不完整。
        for relative_path in checked_paths:  # 修改代码+Stage14硬清理测试: 逐个扫描活跃文件；若没有这行代码，只能检查一个文件。
            source = (self.project_root / relative_path).read_text(encoding="utf-8")  # 修改代码+Stage14硬清理测试: 读取活跃文件源码；若没有这行代码，断言没有检查对象。
            self.assertNotIn(legacy_entry, source, relative_path)  # 修改代码+Stage14硬清理测试: 禁止活跃文件导入旧脚本入口；若没有这行代码，纯新入口目标没有保护。

    def test_removed_legacy_entry_files_stay_deleted(self) -> None:  # 新增代码+Stage14硬清理测试: 确认旧聚合入口和旧兼容入口保持删除状态；若没有这行代码，后续维护者可能重新加回让用户困惑的文件。
        removed_paths = [  # 新增代码+Stage14硬清理测试: 列出已经硬删除的旧架构文件；若没有这行代码，删除范围没有机器可验证记录。
            "learning_agent/test_learning_agent.py",  # 新增代码+Stage14硬清理测试: 旧单文件测试聚合入口必须不存在；若没有这行代码，旧测试命令会继续误导用户。
            "learning_agent/tests/_legacy_groups.py",  # 新增代码+Stage14硬清理测试: 旧分组路由必须不存在；若没有这行代码，测试可能退回过滤大类。
            "learning_agent/tests_support/legacy_learning_agent_suite.py",  # 新增代码+Stage14硬清理测试: 旧大测试套件必须不存在；若没有这行代码，维护者仍会看到巨型历史测试文件。
            "learning_agent/acceptance_harness.py",  # 新增代码+Stage14硬清理测试: 旧根目录验收转发入口必须不存在；若没有这行代码，验收入口会继续有新旧两套。
        ]  # 新增代码+Stage14硬清理测试: 结束旧文件列表；若没有这行代码，Python 列表语法不完整。
        for relative_path in removed_paths:  # 新增代码+Stage14硬清理测试: 逐个确认旧文件不存在；若没有这行代码，只能检查一个旧文件。
            self.assertFalse((self.project_root / relative_path).exists(), relative_path)  # 新增代码+Stage14硬清理测试: 断言旧文件已删除；若没有这行代码，测试无法防止旧入口回流。

    def test_tests_do_not_import_removed_legacy_group_loader(self) -> None:  # 新增代码+Stage14硬清理测试: 确认模块化测试不再导入旧分组加载器；若没有这行代码，测试文件可能表面拆分但实际仍绕回旧路由。
        blocked_terms = ["_legacy_groups", "legacy_learning_agent_suite", "acceptance_harness"]  # 新增代码+Stage14硬清理测试: 列出测试源码中禁止出现的旧架构导入词；若没有这行代码，防回流规则没有明确目标。
        for test_file in (self.project_root / "learning_agent/tests").glob("test_*.py"):  # 新增代码+Stage14硬清理测试: 扫描所有活跃测试模块；若没有这行代码，只检查单个模块会漏掉回流。
            source = test_file.read_text(encoding="utf-8")  # 新增代码+Stage14硬清理测试: 读取测试源码；若没有这行代码，断言没有检查内容。
            for blocked_term in blocked_terms:  # 新增代码+Stage14硬清理测试: 逐个检查禁止词；若没有这行代码，只能检查一个旧词。
                if test_file.name == "test_compat_cleanup.py":  # 新增代码+Stage14硬清理测试: 当前防回流测试自身需要写出禁止词；若没有这行代码，本测试会被自己的规则误伤。
                    continue  # 新增代码+Stage14硬清理测试: 跳过当前文件的禁止词自检；若没有这行代码，防回流测试永远失败。
                self.assertNotIn(blocked_term, source, str(test_file))  # 新增代码+Stage14硬清理测试: 禁止活跃测试再引用旧加载器或旧验收入口；若没有这行代码，纯新测试结构没有保护。

    def test_builtin_catalog_uses_schema_source(self) -> None:  # 修改代码+Stage14硬清理测试: 验证 catalog 能从独立 schema 模块构建工具；若没有这行代码，常量搬迁可能只通过静态扫描。
        from learning_agent.tools.catalog import build_builtin_tool_catalog  # 修改代码+Stage14硬清理测试: 导入新 catalog 构建入口；若没有这行代码，测试无法验证工具目录。
        from learning_agent.tools.schemas import KERNEL_TOOL_NAMES, TOOL_SCHEMAS  # 修改代码+Stage14硬清理测试: 导入独立 schema 事实源；若没有这行代码，测试无法比较 schema 数量和内核工具。

        catalog = build_builtin_tool_catalog()  # 修改代码+Stage14硬清理测试: 用默认 schema 构建内置工具目录；若没有这行代码，后续断言没有实际 catalog。
        catalog_names = {tool.name for tool in catalog}  # 修改代码+Stage14硬清理测试: 汇总目录里的工具名；若没有这行代码，无法确认内核工具是否存在。
        self.assertEqual(len(TOOL_SCHEMAS), len(catalog))  # 修改代码+Stage14硬清理测试: 确认每个 schema 都进入 catalog；若没有这行代码，迁移后漏工具不会被发现。
        self.assertTrue(KERNEL_TOOL_NAMES.issubset(catalog_names))  # 修改代码+Stage14硬清理测试: 确认 read/write/edit/bash 等内核工具仍常驻；若没有这行代码，极简工具面可能被破坏。


if __name__ == "__main__":  # 修改代码+Stage14硬清理测试: 支持直接运行本测试文件；若没有这行代码，手动排查时需要额外命令。
    unittest.main()  # 修改代码+Stage14硬清理测试: 启动 unittest 主程序；若没有这行代码，直接执行文件不会运行测试。
