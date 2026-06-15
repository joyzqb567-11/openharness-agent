"""Computer Use MCP v2 架构文档合同测试。"""  # 新增代码+ComputerUseMcpV2ArchitectureDocs：说明本文件验证架构文档不会丢掉关键边界；如果没有这行代码，文档可能过期而测试不报警。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2ArchitectureDocs：延迟解析类型注解，保持测试导入稳定；如果没有这行代码，老运行方式可能提前求值类型。

import unittest  # 新增代码+ComputerUseMcpV2ArchitectureDocs：使用标准 unittest 框架；如果没有这行代码，本测试不会被发现。
from pathlib import Path  # 新增代码+ComputerUseMcpV2ArchitectureDocs：用于定位 docs 文件；如果没有这行代码，测试只能依赖脆弱字符串路径。


class ComputerUseMcpV2ArchitectureDocsTests(unittest.TestCase):  # 新增代码+ComputerUseMcpV2ArchitectureDocs：函数段开始，保护架构文档关键内容；如果没有这段测试，后续维护可能删掉重要边界说明。
    def test_architecture_doc_records_tool_surface_and_execution_boundaries(self) -> None:  # 新增代码+ComputerUseMcpV2ArchitectureDocs：验证文档包含关键工具面和执行路径；如果没有这行测试，文档可能失去防跑偏价值。
        doc_path = Path(__file__).resolve().parents[2] / "docs" / "computer_use_mcp_v2_architecture.md"  # 新增代码+ComputerUseMcpV2ArchitectureDocs：定位架构文档；如果没有这行代码，测试不知道要检查哪个文件。
        text = doc_path.read_text(encoding="utf-8")  # 新增代码+ComputerUseMcpV2ArchitectureDocs：读取文档文本；如果没有这行代码，后续断言没有输入。
        self.assertIn("17 个", text)  # 新增代码+ComputerUseMcpV2ArchitectureDocs：确认文档写明精确 17 工具面；如果没有这行代码，工具数量边界可能被淡化。
        self.assertIn("agent-side wrapper", text)  # 新增代码+ComputerUseMcpV2ArchitectureDocs：确认文档写明主执行路径；如果没有这行代码，后续可能误把 stdio callTool 当主路径。
        self.assertIn("standalone_stdio_diagnostic", text)  # 新增代码+ComputerUseMcpV2ArchitectureDocs：确认文档写明 stdio 诊断标记；如果没有这行代码，调试路径和生产路径会再次混淆。
        self.assertIn("internal_adapter_tools.py", text)  # 新增代码+ComputerUseMcpV2ArchitectureDocs：确认文档写明内部 facade；如果没有这行代码，旧能力边界容易被误解。
        self.assertIn("read", text)  # 新增代码+ComputerUseMcpV2ArchitectureDocs：确认文档提到顶层文件工具禁止进入 Computer Use 工具面；如果没有这行代码，read/write/edit 隐藏策略容易被忘掉。
        self.assertIn("bash", text)  # 新增代码+ComputerUseMcpV2ArchitectureDocs：确认文档提到 shell 工具禁止进入 Computer Use 工具面；如果没有这行代码，bash 抢桌面任务的问题可能回归。
    # 新增代码+ComputerUseMcpV2ArchitectureDocs：函数段结束，ComputerUseMcpV2ArchitectureDocsTests 到此结束；如果没有这个边界说明，用户不容易看出文档合同测试范围。


if __name__ == "__main__":  # 新增代码+ComputerUseMcpV2ArchitectureDocs：允许直接运行本测试文件；如果没有这行代码，手动调试只能通过模块名运行。
    unittest.main()  # 新增代码+ComputerUseMcpV2ArchitectureDocs：启动 unittest 主程序；如果没有这行代码，直接运行文件不会执行测试。
