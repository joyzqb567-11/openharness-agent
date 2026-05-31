"""Stage 15D 工具协议 v3 测试。"""  # 新增代码+Stage15D: 说明本文件锁定工具元数据协议；若没有这行代码，维护者不清楚测试边界。

from __future__ import annotations  # 新增代码+Stage15D: 延迟解析类型注解；若没有这行代码，前向引用更容易受定义顺序影响。

import unittest  # 新增代码+Stage15D: 使用项目现有 unittest 框架；若没有这行代码，测试类无法运行。

from learning_agent.tools.catalog import build_builtin_tool_catalog  # 新增代码+Stage15D: 导入内置工具目录构建入口；若没有这行代码，测试无法验证真实 catalog 元数据。
from learning_agent.tools.types import AgentTool  # 新增代码+Stage15D: 导入工具元数据对象；若没有这行代码，测试无法验证协议默认值。


class ToolProtocolTests(unittest.TestCase):  # 新增代码+Stage15D: 定义工具协议测试类；若没有这行代码，测试方法没有统一容器。
    def test_agent_tool_v3_defaults_are_conservative(self) -> None:  # 新增代码+Stage15D: 验证新协议默认保守；若没有这行代码，未知工具可能被错误并发或自动允许。
        tool = AgentTool(name="demo", description="demo", input_schema={"type": "object"})  # 新增代码+Stage15D: 构造最小工具对象；若没有这行代码，无法检查默认字段。
        self.assertFalse(tool.is_concurrency_safe)  # 新增代码+Stage15D: 默认不允许并发；若没有这行代码，未知副作用工具可能被并行执行。
        self.assertFalse(tool.requires_user_interaction)  # 新增代码+Stage15D: 默认不要求交互；若没有这行代码，普通只读工具可能被误判成人机交互工具。
        self.assertEqual(tool.interrupt_behavior, "block")  # 新增代码+Stage15D: 默认中断策略为阻塞；若没有这行代码，工具取消语义会不清楚。
        self.assertEqual(tool.permission_mode, "ask")  # 新增代码+Stage15D: 默认权限模式为询问；若没有这行代码，未知工具可能绕过权限层。
        self.assertEqual(tool.result_policy, "inline_or_artifact")  # 新增代码+Stage15D: 默认结果策略沿用短结果内联长结果落盘；若没有这行代码，工具结果大小处理没有统一策略。
        self.assertEqual(tool.timeout_seconds, 0.0)  # 新增代码+Stage15D: 默认不强加超时；若没有这行代码，旧工具可能因为未配置超时被错误中断。

    def test_builtin_catalog_marks_safe_read_tools_as_concurrent(self) -> None:  # 新增代码+Stage15D: 验证只读工具能标记并发安全；若没有这行代码，Stage 15F 无法可靠并发读取。
        catalog = {tool.name: tool for tool in build_builtin_tool_catalog()}  # 新增代码+Stage15D: 构造真实内置工具索引；若没有这行代码，测试无法检查实际交付 catalog。
        self.assertTrue(catalog["read"].is_read_only)  # 新增代码+Stage15D: read 必须是只读；若没有这行代码，并发调度无法识别安全读取。
        self.assertTrue(catalog["read"].is_concurrency_safe)  # 新增代码+Stage15D: read 必须允许安全并发；若没有这行代码，大项目多文件读取不能提速。
        self.assertTrue(catalog["read_file"].is_read_only)  # 新增代码+Stage15D: 兼容 read_file 也必须是只读；若没有这行代码，旧工具路径无法进入安全并发批次。
        self.assertTrue(catalog["read_file"].is_concurrency_safe)  # 新增代码+Stage15D: read_file 也必须允许安全并发；若没有这行代码，旧读取工具无法利用 Stage 15F。
        self.assertEqual(catalog["read"].permission_mode, "auto_allow")  # 新增代码+Stage15D: read 默认可自动允许；若没有这行代码，普通读取会产生不必要权限打扰。

    def test_builtin_catalog_keeps_write_edit_bash_serial(self) -> None:  # 新增代码+Stage15D: 验证副作用工具保持串行；若没有这行代码，写文件或命令可能被错误并发。
        catalog = {tool.name: tool for tool in build_builtin_tool_catalog()}  # 新增代码+Stage15D: 构造真实内置工具索引；若没有这行代码，测试无法检查实际工具元数据。
        for tool_name in ("write", "edit", "bash", "write_file"):  # 新增代码+Stage15D: 列出必须串行的副作用工具；若没有这行代码，单个断言容易漏工具。
            with self.subTest(tool_name=tool_name):  # 新增代码+Stage15D: 给每个工具独立失败上下文；若没有这行代码，失败时不清楚哪个工具元数据错了。
                self.assertFalse(catalog[tool_name].is_concurrency_safe)  # 新增代码+Stage15D: 断言副作用工具不可并发；若没有这行代码，Stage 15F 可能并行修改同一文件。
                self.assertNotEqual(catalog[tool_name].permission_mode, "auto_allow")  # 新增代码+Stage15D: 断言副作用工具不能自动允许；若没有这行代码，危险操作可能绕过用户确认。
        self.assertTrue(catalog["write"].is_destructive)  # 新增代码+Stage15D: write 标记为破坏性；若没有这行代码，权限层无法突出高风险写入。
        self.assertTrue(catalog["edit"].is_destructive)  # 新增代码+Stage15D: edit 标记为破坏性；若没有这行代码，权限层无法突出高风险编辑。


if __name__ == "__main__":  # 新增代码+Stage15D: 支持直接运行本测试文件；若没有这行代码，单文件排查不方便。
    unittest.main()  # 新增代码+Stage15D: 直接运行时启动 unittest；若没有这行代码，python 文件本身不会执行测试。
