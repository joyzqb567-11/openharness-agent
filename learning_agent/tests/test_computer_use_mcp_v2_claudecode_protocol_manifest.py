from __future__ import annotations  # 新增代码+ClaudeCodeProtocolParityTests：延迟类型注解解析；如果没有这行代码，测试导入顺序变化时更容易受类型求值影响。

import unittest  # 新增代码+ClaudeCodeProtocolParityTests：使用标准 unittest 框架；如果没有这行代码，测试类不会被发现。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import FORBIDDEN_LEGACY_RAW_TOOL_NAMES, computer_use_mcp_tools  # 新增代码+ClaudeCodeProtocolParityTests：导入 public 工具 schema；如果没有这行代码，测试无法锁定模型可见协议。


class ComputerUseMcpV2ClaudeCodeProtocolManifestTests(unittest.TestCase):  # 新增代码+ClaudeCodeProtocolParityTests：类段开始，验证 ClaudeCode-compatible 工具清单和主字段；如果没有这段类，协议级对齐没有自动化门禁。
    def _tool_by_name(self) -> dict[str, dict[str, object]]:  # 新增代码+ClaudeCodeProtocolParityTests：函数段开始，按工具名索引 schema；如果没有这段函数，每个测试都要重复遍历工具列表。
        return {str(tool["name"]): tool for tool in computer_use_mcp_tools()}  # 新增代码+ClaudeCodeProtocolParityTests：返回工具名字典；如果没有这行代码，后续字段断言没有输入。
    # 新增代码+ClaudeCodeProtocolParityTests：函数段结束，_tool_by_name 到此结束；如果没有这个边界说明，用户不容易看出 schema 索引范围。

    def test_public_tool_names_match_claudecode_compatible_surface(self) -> None:  # 新增代码+ClaudeCodeProtocolParityTests：函数段开始，锁定公开工具名集合；如果没有这段测试，工具名可能悄悄增删。
        names = set(self._tool_by_name())  # 新增代码+ClaudeCodeProtocolParityTests：读取当前工具名集合；如果没有这行代码，无法和期望集合比较。
        expected_names = {  # 新增代码+ClaudeCodeProtocolParityTests：声明 ClaudeCode-compatible 公开工具集合；如果没有这段集合，测试没有清晰合同。
            "request_access",  # 新增代码+ClaudeCodeProtocolParityTests：授权申请工具必须存在；如果没有这一项，模型无法先申请桌面访问。
            "observe",  # 新增代码+ClaudeCodeProtocolParityTests：观察工具必须存在；如果没有这一项，模型缺少只读桌面状态入口。
            "screenshot",  # 新增代码+ClaudeCodeProtocolParityTests：截图工具必须存在；如果没有这一项，视觉观察无法启动。
            "cursor_position",  # 新增代码+ClaudeCodeProtocolParityTests：光标位置工具必须存在；如果没有这一项，模型无法读鼠标位置。
            "mouse_move",  # 新增代码+ClaudeCodeProtocolParityTests：鼠标移动工具必须存在；如果没有这一项，模型无法定位指针。
            "left_click",  # 新增代码+ClaudeCodeProtocolParityTests：左键单击工具必须存在；如果没有这一项，点击会回退旧名。
            "double_click",  # 新增代码+ClaudeCodeProtocolParityTests：双击工具必须存在；如果没有这一项，打开文件/图标动作缺入口。
            "right_click",  # 新增代码+ClaudeCodeProtocolParityTests：右键工具必须存在；如果没有这一项，菜单操作缺入口。
            "middle_click",  # 新增代码+ClaudeCodeProtocolParityTests：中键工具必须存在；如果没有这一项，ClaudeCode parity 工具面不完整。
            "triple_click",  # 新增代码+ClaudeCodeProtocolParityTests：三击工具必须存在；如果没有这一项，文本段选择等动作缺入口。
            "left_mouse_down",  # 新增代码+ClaudeCodeProtocolParityTests：左键按下工具必须存在；如果没有这一项，拆分式拖拽无法表达。
            "left_mouse_up",  # 新增代码+ClaudeCodeProtocolParityTests：左键释放工具必须存在；如果没有这一项，拆分式拖拽无法收尾。
            "type",  # 新增代码+ClaudeCodeProtocolParityTests：文本输入工具必须存在；如果没有这一项，应用输入缺入口。
            "key",  # 新增代码+ClaudeCodeProtocolParityTests：按键工具必须存在；如果没有这一项，快捷键缺入口。
            "hold_key",  # 新增代码+ClaudeCodeProtocolParityTests：长按工具必须存在；如果没有这一项，按住修饰键场景缺入口。
            "scroll",  # 新增代码+ClaudeCodeProtocolParityTests：滚动工具必须存在；如果没有这一项，长页面无法操作。
            "left_click_drag",  # 新增代码+ClaudeCodeProtocolParityTests：左键拖拽工具必须存在；如果没有这一项，拖拽只能靠脆弱多步组合。
            "zoom",  # 新增代码+ClaudeCodeProtocolParityTests：局部放大工具必须存在；如果没有这一项，模型无法细看区域。
            "wait",  # 新增代码+ClaudeCodeProtocolParityTests：等待工具必须存在；如果没有这一项，加载等待缺入口。
            "read_clipboard",  # 新增代码+ClaudeCodeProtocolParityTests：读剪贴板工具必须存在；如果没有这一项，复制结果无法检查。
            "write_clipboard",  # 新增代码+ClaudeCodeProtocolParityTests：写剪贴板工具必须存在；如果没有这一项，长文本输入缺稳妥路线。
            "open_application",  # 新增代码+ClaudeCodeProtocolParityTests：打开应用工具必须存在；如果没有这一项，agent-owned 启动链路会断。
            "list_granted_applications",  # 新增代码+ClaudeCodeProtocolParityTests：授权查询工具必须存在；如果没有这一项，模型无法确认权限状态。
            "computer_batch",  # 新增代码+ClaudeCodeProtocolParityTests：批量工具必须存在；如果没有这一项，多步桌面操作往返成本高。
        }  # 新增代码+ClaudeCodeProtocolParityTests：期望工具集合结束；如果没有这行代码，Python 集合语法不完整。
        self.assertEqual(names, expected_names)  # 新增代码+ClaudeCodeProtocolParityTests：断言工具名精确一致；如果没有这行代码，缺工具或多工具不会失败。
    # 新增代码+ClaudeCodeProtocolParityTests：函数段结束，test_public_tool_names_match_claudecode_compatible_surface 到此结束；如果没有这个边界说明，用户不容易看出工具名合同范围。

    def test_legacy_raw_tools_are_not_public(self) -> None:  # 新增代码+ClaudeCodeProtocolParityTests：函数段开始，确认旧 raw 工具没有公开；如果没有这段测试，旧工具可能重新泄漏。
        names = set(self._tool_by_name())  # 新增代码+ClaudeCodeProtocolParityTests：读取当前 public 工具名；如果没有这行代码，无法检查 forbidden 集合。
        self.assertFalse(names.intersection(FORBIDDEN_LEGACY_RAW_TOOL_NAMES))  # 新增代码+ClaudeCodeProtocolParityTests：断言旧名没有出现在 public schema；如果没有这行代码，legacy raw 工具回归不会失败。
    # 新增代码+ClaudeCodeProtocolParityTests：函数段结束，test_legacy_raw_tools_are_not_public 到此结束；如果没有这个边界说明，用户不容易看出 legacy 检查范围。

    def test_schema_uses_claudecode_primary_fields(self) -> None:  # 新增代码+ClaudeCodeProtocolParityTests：函数段开始，确认 schema 主字段使用 ClaudeCode 风格；如果没有这段测试，工具名对齐但参数仍会漂移。
        tools = self._tool_by_name()  # 新增代码+ClaudeCodeProtocolParityTests：按名称读取工具 schema；如果没有这行代码，字段断言没有数据来源。
        expected_fields = {  # 新增代码+ClaudeCodeProtocolParityTests：声明每个关键工具的 ClaudeCode 主字段；如果没有这段字典，字段合同会散落。
            "left_click": {"coordinate"},  # 新增代码+ClaudeCodeProtocolParityTests：左键主字段应为 coordinate；如果没有这一项，点击可能继续主推 x/y。
            "mouse_move": {"coordinate"},  # 新增代码+ClaudeCodeProtocolParityTests：鼠标移动主字段应为 coordinate；如果没有这一项，移动可能继续主推 x/y。
            "left_click_drag": {"start_coordinate", "coordinate"},  # 新增代码+ClaudeCodeProtocolParityTests：拖拽主字段应为起点和终点 coordinate；如果没有这一项，拖拽字段会和 ClaudeCode 不一致。
            "zoom": {"region"},  # 新增代码+ClaudeCodeProtocolParityTests：局部放大主字段应为 region；如果没有这一项，zoom 会继续主推 x/y/width/height。
            "scroll": {"direction", "amount"},  # 新增代码+ClaudeCodeProtocolParityTests：滚动主字段应为 direction/amount；如果没有这一项，scroll 会继续只会 delta_y。
            "hold_key": {"text", "duration"},  # 新增代码+ClaudeCodeProtocolParityTests：长按主字段应为 text/duration；如果没有这一项，hold_key 会继续只会 keys/duration_seconds。
            "open_application": {"bundle_id"},  # 新增代码+ClaudeCodeProtocolParityTests：打开应用主字段应为 bundle_id；如果没有这一项，模型会继续发 app_name。
            "request_access": {"apps", "reason"},  # 新增代码+ClaudeCodeProtocolParityTests：授权主字段应为 apps/reason；如果没有这一项，权限模型不能对齐 ClaudeCode。
            "computer_batch": {"actions"},  # 新增代码+ClaudeCodeProtocolParityTests：批量主字段应为 actions；如果没有这一项，batch 会继续依赖旧 steps。
        }  # 新增代码+ClaudeCodeProtocolParityTests：期望字段字典结束；如果没有这行代码，Python 字典语法不完整。
        for tool_name, field_names in expected_fields.items():  # 新增代码+ClaudeCodeProtocolParityTests：逐个关键工具检查字段；如果没有这行代码，断言会重复且难定位。
            properties = tools[tool_name]["inputSchema"]["properties"]  # 新增代码+ClaudeCodeProtocolParityTests：读取工具参数属性；如果没有这行代码，无法检查字段是否公开。
            self.assertTrue(field_names.issubset(properties), (tool_name, properties))  # 新增代码+ClaudeCodeProtocolParityTests：断言主字段存在；如果没有这行代码，schema parity 退化不会失败。
    # 新增代码+ClaudeCodeProtocolParityTests：函数段结束，test_schema_uses_claudecode_primary_fields 到此结束；如果没有这个边界说明，用户不容易看出 schema 字段检查范围。


if __name__ == "__main__":  # 新增代码+ClaudeCodeProtocolParityTests：允许直接运行本测试文件；如果没有这行代码，手动调试不方便。
    unittest.main()  # 新增代码+ClaudeCodeProtocolParityTests：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
