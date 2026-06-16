"""Computer Use MCP v2 独立包合同测试。"""  # 新增代码+ComputerUseMcpV2RedTests：说明本文件专门锁定 v2 新架构；如果没有这行代码，后续读者不容易区分这是新 MCP 包合同而不是旧 computer_use 兼容测试。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2RedTests：延迟类型注解解析，避免测试导入阶段因类型顺序产生噪音；如果没有这行代码，老版本运行方式可能在导入时提前求值类型。

import unittest  # 新增代码+ComputerUseMcpV2RedTests：使用标准 unittest 框架编写红测；如果没有这行代码，测试类不会被测试运行器识别。
from pathlib import Path  # 新增代码+ComputerUseMcpV2RedTests：用 Path 精确检查包内文件结构；如果没有这行代码，文件名合同只能靠字符串拼接且容易出错。
from typing import Any  # 新增代码+ComputerUseMcpV2RedTests：给 fake host 和 trace payload 标注通用类型；如果没有这行代码，测试辅助对象的边界不清楚。

from learning_agent.computer_use_mcp_v2.claudecode_bridge.mcpServer import run_selftest  # 新增代码+ComputerUseMcpV2RedTests：导入 v2 server 自检入口；如果没有这行代码，测试无法证明 stdio server 已切到 v2 表面。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import assert_no_shell_surface, computer_use_mcp_tools  # 新增代码+ComputerUseMcpV2RedTests：导入 v2 推断 MCP 包的工具构建入口；如果没有这行代码，测试仍可能误用旧 schema。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import ComputerUseMcpV2Context, dispatch_computer_use_mcp_v2_tool  # 新增代码+ComputerUseMcpV2RedTests：导入 v2 runtime 分发入口；如果没有这行代码，测试无法确认执行路径不再依赖旧 adapter。


EXPECTED_CLAUDECODE_BRIDGE_FILES = {  # 新增代码+ComputerUseMcpV2RedTests：列出必须与 ClaudeCode 可见 computerUse 目录同名的桥接文件；如果没有这组断言，文件名同构目标会漂移。
    "appNames.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode appNames.ts；如果没有这一项，应用名映射职责会缺少固定位置。
    "cleanup.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode cleanup.ts；如果没有这一项，清理职责会散落到其他文件。
    "common.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode common.ts；如果没有这一项，共用常量和工具函数没有稳定锚点。
    "computerUseLock.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode computerUseLock.ts；如果没有这一项，桌面独占锁职责不清楚。
    "drainRunLoop.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode drainRunLoop.ts；如果没有这一项，等待 UI 事件循环的职责会缺失。
    "escHotkey.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode escHotkey.ts；如果没有这一项，紧急中止热键没有固定位置。
    "executor.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode executor.ts；如果没有这一项，真实动作执行入口会继续混在旧模块里。
    "gates.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode gates.ts；如果没有这一项，权限和门禁规则没有集中位置。
    "hostAdapter.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode hostAdapter.ts；如果没有这一项，Windows 宿主实现和 MCP 表面会耦合。
    "inputLoader.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode inputLoader.ts；如果没有这一项，输入后端加载职责没有固定锚点。
    "mcpServer.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode mcpServer.ts；如果没有这一项，stdio server 入口会继续使用旧 server 文件。
    "setup.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode setup.ts；如果没有这一项，工具面安装和能力包绑定没有固定入口。
    "swiftLoader.py",  # 新增代码+ComputerUseMcpV2RedTests：保留 ClaudeCode swiftLoader.ts 名字但在 Windows 中转到 native loader；如果没有这一项，后续对照 ClaudeCode 源码会断层。
    "toolRendering.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode toolRendering.tsx；如果没有这一项，工具结果渲染职责没有固定位置。
    "wrapper.py",  # 新增代码+ComputerUseMcpV2RedTests：对齐 ClaudeCode wrapper.tsx；如果没有这一项，agent-side 绑定入口没有固定文件。
}  # 新增代码+ComputerUseMcpV2RedTests：桥接文件集合结束；如果没有这行代码，Python 集合语法不完整。

EXPECTED_OPENHARNESS_BRIDGE_FILES = {  # 修改代码+ComputerUseMcpV2ParityTightening：单独列出 OpenHarness 专属桥接层文件；如果没有这组断言，终端命令接线会继续混在 ClaudeCode 镜像目录里。
    "terminal_commands.py",  # 修改代码+ComputerUseMcpV2ParityTightening：要求终端命令桥接文件搬到 OpenHarness 专属目录；如果没有这一项，/computer use 模式同步入口缺少新的结构锚点。
}  # 修改代码+ComputerUseMcpV2ParityTightening：OpenHarness 专属桥接文件集合结束；如果没有这行代码，Python 集合语法不完整。

EXPECTED_INFERRED_ANT_MCP_FILES = {  # 新增代码+ComputerUseMcpV2RedTests：列出缺失外部 @ant/computer-use-mcp 的推断替代文件；如果没有这组断言，推断包可能和桥接包混在一起。
    "actions.py",  # 新增代码+ComputerUseMcpV2RedTests：动作实现文件必须存在；如果没有这一项，鼠标键盘动作没有内聚位置。
    "applications.py",  # 新增代码+ComputerUseMcpV2RedTests：应用打开和授权查询文件必须存在；如果没有这一项，应用能力会散落。
    "batch.py",  # 新增代码+ComputerUseMcpV2RedTests：批量执行文件必须存在；如果没有这一项，computer_batch 会和单动作分发混杂。
    "bind_session_context.py",  # 新增代码+ComputerUseMcpV2RedTests：会话绑定文件必须存在；如果没有这一项，独立 server 无法拿到 agent 回调。
    "build_tools.py",  # 新增代码+ComputerUseMcpV2RedTests：工具 schema 构建文件必须存在；如果没有这一项，模型可见工具面没有唯一事实源。
    "clipboard.py",  # 新增代码+ComputerUseMcpV2RedTests：剪贴板文件必须存在；如果没有这一项，剪贴板权限和实现会混入动作文件。
    "coordinates.py",  # 新增代码+ComputerUseMcpV2RedTests：坐标文件必须存在；如果没有这一项，屏幕坐标校验会重复实现。
    "errors.py",  # 新增代码+ComputerUseMcpV2RedTests：错误模型文件必须存在；如果没有这一项，失败返回格式会漂移。
    "legacy_ports.py",  # 新增代码+ComputerUseMcpV2RedTests：旧接口 adapter 边界文件必须存在；如果没有这一项，旧 computer_action 可能继续直接暴露给模型。
    "observation.py",  # 新增代码+ComputerUseMcpV2RedTests：观察和截图文件必须存在；如果没有这一项，observe/screenshot 会散落。
    "permissions.py",  # 新增代码+ComputerUseMcpV2RedTests：授权文件必须存在；如果没有这一项，request_access 和 grant 状态会混到执行器。
    "result_blocks.py",  # 新增代码+ComputerUseMcpV2RedTests：结果块文件必须存在；如果没有这一项，工具输出格式会重复拼接。
    "runtime.py",  # 新增代码+ComputerUseMcpV2RedTests：运行时分发文件必须存在；如果没有这一项，agent-side 和 stdio-side 会各自分发。
    "sentinel_apps.py",  # 新增代码+ComputerUseMcpV2RedTests：哨兵应用文件必须存在；如果没有这一项，安全边界没有集中名单。
    "telemetry.py",  # 新增代码+ComputerUseMcpV2RedTests：遥测和 trace 文件必须存在；如果没有这一项，真实动作证据链会缺失。
    "types.py",  # 新增代码+ComputerUseMcpV2RedTests：类型文件必须存在；如果没有这一项，跨模块数据结构会漂移。
}  # 新增代码+ComputerUseMcpV2RedTests：推断包文件集合结束；如果没有这行代码，Python 集合语法不完整。

EXPECTED_RAW_TOOL_NAMES = {  # 新增代码+ComputerUseMcpV2RedTests：列出用户确认的 ClaudeCode 风格原子工具面；如果没有这组断言，旧别名和额外工具会重新泄漏。
    "request_access",  # 新增代码+ComputerUseMcpV2RedTests：授权申请工具必须暴露；如果没有这一项，模型无法先请求桌面控制权限。
    "observe",  # 新增代码+ComputerUseMcpV2RedTests：观察别名必须暴露；如果没有这一项，模型缺少 ClaudeCode 风格观察入口。
    "screenshot",  # 新增代码+ComputerUseMcpV2RedTests：截图工具必须暴露；如果没有这一项，模型无法获取屏幕图像。
    "cursor_position",  # 新增代码+ComputerUseMcpV2RedTests：光标位置工具必须暴露；如果没有这一项，模型无法校验鼠标当前位置。
    "mouse_move",  # 新增代码+ComputerUseMcpV2RedTests：移动鼠标工具必须暴露；如果没有这一项，模型无法先移动再点击。
    "left_click",  # 新增代码+ComputerUseMcpV2RedTests：左键点击工具必须暴露；如果没有这一项，模型会退回旧 click 名称。
    "double_click",  # 新增代码+ComputerUseMcpV2RedTests：双击工具必须暴露；如果没有这一项，常见桌面打开动作无法表达。
    "right_click",  # 新增代码+ComputerUseMcpV2RedTests：右键点击工具必须暴露；如果没有这一项，右键菜单任务无法表达。
    "middle_click",  # 新增代码+ClaudeCodeParity：中键点击工具必须作为 ClaudeCode parity 公开工具暴露；如果没有这一项，模型无法表达 ClaudeCode 已有的中键动作。
    "triple_click",  # 新增代码+ClaudeCodeParity：三击工具必须作为 ClaudeCode parity 公开工具暴露；如果没有这一项，文本段落选择等三击动作会缺少原子入口。
    "left_mouse_down",  # 新增代码+ClaudeCodeParity：左键按下工具必须作为 ClaudeCode parity 公开工具暴露；如果没有这一项，拖拽等拆分鼠标动作无法对齐 ClaudeCode 工具面。
    "left_mouse_up",  # 新增代码+ClaudeCodeParity：左键释放工具必须作为 ClaudeCode parity 公开工具暴露；如果没有这一项，按下后的释放动作无法作为独立原子工具表达。
    "type",  # 新增代码+ComputerUseMcpV2RedTests：文本输入工具必须暴露；如果没有这一项，浏览器和 Office 输入无法执行。
    "key",  # 新增代码+ComputerUseMcpV2RedTests：按键工具必须暴露；如果没有这一项，Enter、Ctrl+S 等按键无法表达。
    "hold_key",  # 新增代码+ClaudeCodeParity：按住按键工具必须作为 ClaudeCode parity 公开工具暴露；如果没有这一项，长按快捷键或按住修饰键的场景无法表达。
    "scroll",  # 新增代码+ComputerUseMcpV2RedTests：滚动工具必须暴露；如果没有这一项，长网页和文档无法操作。
    "left_click_drag",  # 新增代码+ClaudeCodeParity：左键拖拽工具必须作为 ClaudeCode parity 公开工具暴露；如果没有这一项，模型只能把拖拽拆成不稳定的多步动作。
    "zoom",  # 新增代码+ClaudeCodeParity：局部放大观察工具必须作为 ClaudeCode parity 公开工具暴露；如果没有这一项，模型无法请求细看屏幕局部区域。
    "wait",  # 新增代码+ComputerUseMcpV2RedTests：等待工具必须暴露；如果没有这一项，界面加载无法稳定等待。
    "read_clipboard",  # 新增代码+ComputerUseMcpV2RedTests：读剪贴板工具必须暴露；如果没有这一项，复制结果无法检查。
    "write_clipboard",  # 新增代码+ComputerUseMcpV2RedTests：写剪贴板工具必须暴露；如果没有这一项，长文本输入缺少稳妥路径。
    "open_application",  # 新增代码+ComputerUseMcpV2RedTests：打开应用工具必须暴露；如果没有这一项，agent-owned app 启动链路会断。
    "list_granted_applications",  # 新增代码+ComputerUseMcpV2RedTests：授权应用查询工具必须暴露；如果没有这一项，模型无法确认权限状态。
    "computer_batch",  # 新增代码+ComputerUseMcpV2RedTests：批量工具必须暴露；如果没有这一项，多步桌面动作无法合并。
}  # 新增代码+ComputerUseMcpV2RedTests：工具名集合结束；如果没有这行代码，Python 集合语法不完整。

FORBIDDEN_RAW_TOOL_NAMES = {  # 新增代码+ComputerUseMcpV2RedTests：列出 v2 工具面禁止出现的旧名和非蓝图名；如果没有这组断言，重复暴露问题会复发。
    "click",  # 新增代码+ComputerUseMcpV2RedTests：禁止旧 click 别名；如果没有这一项，left_click 和 click 会同轮混用。
    "double_click_mouse",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止历史双击鼠标别名；如果没有这一项，double_click 会和旧名字混用。
    "right_click_mouse",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止历史右键鼠标别名；如果没有这一项，right_click 会和旧名字混用。
    "clipboard",  # 新增代码+ComputerUseMcpV2RedTests：禁止旧 clipboard 合并工具；如果没有这一项，read_clipboard/write_clipboard 会和旧入口混用。
    "computer_status",  # 新增代码+ComputerUseMcpV2RedTests：禁止旧状态工具进入 MCP v2 表面；如果没有这一项，旧四件套会继续影响模型选择。
    "computer_observe",  # 新增代码+ComputerUseMcpV2RedTests：禁止旧观察工具进入 MCP v2 表面；如果没有这一项，observe 会被旧名竞争。
    "computer_discover",  # 新增代码+ComputerUseMcpV2RedTests：禁止旧发现工具进入 MCP v2 表面；如果没有这一项，发现能力会继续以旧接口暴露。
    "computer_action",  # 新增代码+ComputerUseMcpV2RedTests：禁止旧动作工具进入 MCP v2 表面；如果没有这一项，旧 action 会抢走原子工具任务。
    "computer_use",  # 新增代码+ComputerUseMcpV2RedTests：禁止旧下划线兼容入口进入 MCP v2 表面；如果没有这一项，模型仍会看到两套控制入口。
    "computer-use",  # 新增代码+ComputerUseMcpV2RedTests：禁止旧连字符兼容入口进入 MCP v2 表面；如果没有这一项，模型会混淆 server 名和工具名。
    "read",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止顶层文件读取工具作为 Computer Use MCP 原始工具；如果没有这一项，read 可能绕开模式化工具池。
    "write",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止顶层文件写入工具作为 Computer Use MCP 原始工具；如果没有这一项，write 可能被误当成桌面输入。
    "edit",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止顶层文件编辑工具作为 Computer Use MCP 原始工具；如果没有这一项，edit 可能被误当成 Office 编辑。
    "bash",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止 shell 工具名作为 Computer Use MCP 原始工具；如果没有这一项，bash 可能绕开工具面过滤。
    "powershell",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止 PowerShell 工具名作为 Computer Use MCP 原始工具；如果没有这一项，Windows 命令入口可能伪装成桌面工具。
    "shell",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止通用 shell 工具名作为 Computer Use MCP 原始工具；如果没有这一项，命令执行入口可能混入。
    "run_powershell",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止历史 PowerShell 执行别名；如果没有这一项，shell 能力可能从旧名回流。
    "start_background_command",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止后台命令工具名；如果没有这一项，长命令能力可能绕过 Computer Use 隔离。
}  # 新增代码+ComputerUseMcpV2RedTests：禁止工具名集合结束；如果没有这行代码，Python 集合语法不完整。


class ComputerUseMcpV2ContractTests(unittest.TestCase):  # 新增代码+ComputerUseMcpV2RedTests：定义 v2 合同测试类；如果没有这段代码，unittest 不会发现这些合同检查。
    # 新增代码+ComputerUseMcpV2RedTests：函数段开始，test_v2_package_structure_matches_blueprint 用真实文件系统锁定双层包结构；如果没有这段测试，后续可能把推断外部包文件混到 ClaudeCode 桥接层。
    def test_v2_package_structure_matches_blueprint(self) -> None:  # 新增代码+ComputerUseMcpV2RedTests：声明包结构测试；如果没有这一行，文件同构目标没有自动化保护。
        package_root = Path(__file__).resolve().parents[1] / "computer_use_mcp_v2"  # 新增代码+ComputerUseMcpV2RedTests：定位 v2 包根目录；如果没有这一行，测试不知道要检查哪个目录。
        bridge_files = {path.name for path in (package_root / "claudecode_bridge").glob("*.py") if path.name != "__init__.py"}  # 新增代码+ComputerUseMcpV2RedTests：读取 ClaudeCode 桥接层文件名；如果没有这一行，文件名同构不会被验证。
        inferred_files = {path.name for path in (package_root / "inferred_ant_mcp").glob("*.py") if path.name != "__init__.py"}  # 新增代码+ComputerUseMcpV2RedTests：读取推断外部 MCP 包文件名；如果没有这一行，推断包边界不会被验证。
        openharness_bridge_files = {path.name for path in (package_root / "openharness_bridge").glob("*.py") if path.name != "__init__.py"}  # 修改代码+ComputerUseMcpV2ParityTightening：读取 OpenHarness 专属桥接层文件名；如果没有这一行，terminal_commands.py 搬家目标不会被验证。
        self.assertEqual(EXPECTED_CLAUDECODE_BRIDGE_FILES, bridge_files)  # 新增代码+ComputerUseMcpV2RedTests：断言桥接层文件名完全一致；如果没有这一行，缺文件或多文件不会失败。
        self.assertEqual(EXPECTED_INFERRED_ANT_MCP_FILES, inferred_files)  # 新增代码+ComputerUseMcpV2RedTests：断言推断包文件名完全一致；如果没有这一行，外部包推断结构会漂移。
        self.assertEqual(EXPECTED_OPENHARNESS_BRIDGE_FILES, openharness_bridge_files)  # 修改代码+ComputerUseMcpV2ParityTightening：断言 OpenHarness-only 接线层单独存在；如果没有这一行，ClaudeCode mirror 和本项目扩展层会再次混用。
    # 新增代码+ComputerUseMcpV2RedTests：函数段结束，test_v2_package_structure_matches_blueprint 到此结束；如果没有这个边界说明，用户不容易看出结构测试范围。

    # 新增代码+ComputerUseMcpV2RedTests：函数段开始，test_v2_tool_surface_is_exact_and_shell_free 锁定模型可发现工具面；如果没有这段测试，旧工具或额外工具会悄悄暴露给大模型。
    def test_v2_tool_surface_is_exact_and_shell_free(self) -> None:  # 新增代码+ComputerUseMcpV2RedTests：声明工具面测试；如果没有这一行，工具名合同没有自动化保护。
        tools = computer_use_mcp_tools()  # 新增代码+ComputerUseMcpV2RedTests：读取 v2 工具 schema；如果没有这一行，测试没有生产工具面输入。
        raw_names = {str(tool.get("name", "")) for tool in tools}  # 新增代码+ComputerUseMcpV2RedTests：提取 MCP server 原始工具名；如果没有这一行，断言无法比较工具集合。
        self.assertEqual(EXPECTED_RAW_TOOL_NAMES, raw_names)  # 新增代码+ComputerUseMcpV2RedTests：断言工具面等于用户确认清单；如果没有这一行，少工具和多工具都不会失败。
        self.assertTrue(assert_no_shell_surface(tools))  # 新增代码+ComputerUseMcpV2RedTests：断言 v2 MCP 不包含 shell 表面；如果没有这一行，bash 类能力可能重新混入。
        self.assertFalse(FORBIDDEN_RAW_TOOL_NAMES.intersection(raw_names))  # 新增代码+ComputerUseMcpV2RedTests：断言旧名和蓝图外工具不出现；如果没有这一行，重复暴露风险不会被直接指出。
    # 新增代码+ComputerUseMcpV2RedTests：函数段结束，test_v2_tool_surface_is_exact_and_shell_free 到此结束；如果没有这个边界说明，用户不容易看出工具面测试范围。

    # 新增代码+ClaudeCodeParity：函数段开始，test_claudecode_parity_tool_schemas_lock_required_fields 用真实工具 schema 锁定 7 个 parity 工具的入参形状；如果没有这段测试，后续只改名字不改参数合同的漂移不会被发现。
    def test_claudecode_parity_tool_schemas_lock_required_fields(self) -> None:  # 新增代码+ClaudeCodeParity：声明 parity schema 合同测试；如果没有这一行，unittest 不会执行新增工具的 schema 形状检查。
        tools_by_name = {str(tool.get("name", "")): tool for tool in computer_use_mcp_tools()}  # 新增代码+ClaudeCodeParity：把工具列表变成按名称索引的字典；如果没有这一行，后续断言需要重复遍历并容易漏工具。
        zoom_schema = tools_by_name["zoom"]["inputSchema"]  # 新增代码+ClaudeCodeParity：读取 zoom 输入 schema；如果没有这一行，无法断言局部放大工具的必填字段。
        hold_key_schema = tools_by_name["hold_key"]["inputSchema"]  # 新增代码+ClaudeCodeParity：读取 hold_key 输入 schema；如果没有这一行，无法发现 key/keys 漂移。
        drag_schema = tools_by_name["left_click_drag"]["inputSchema"]  # 新增代码+ClaudeCodeParity：读取 left_click_drag 输入 schema；如果没有这一行，无法断言拖拽起点终点字段。
        middle_schema = tools_by_name["middle_click"]["inputSchema"]  # 新增代码+ClaudeCodeParity：读取 middle_click 输入 schema；如果没有这一行，无法断言中键坐标字段。
        triple_schema = tools_by_name["triple_click"]["inputSchema"]  # 新增代码+ClaudeCodeParity：读取 triple_click 输入 schema；如果没有这一行，无法断言三击坐标字段。
        mouse_down_schema = tools_by_name["left_mouse_down"]["inputSchema"]  # 新增代码+ClaudeCodeParity：读取 left_mouse_down 输入 schema；如果没有这一行，无法断言左键按下坐标字段。
        mouse_up_schema = tools_by_name["left_mouse_up"]["inputSchema"]  # 修改代码+ClaudeCodeParity：读取 left_mouse_up 输入 schema 并准备断言释放坐标合同；如果没有这一行，公开 schema 可能继续隐藏释放位置。
        self.assertEqual({"x", "y", "width", "height"}, set(zoom_schema["required"]))  # 新增代码+ClaudeCodeParity：断言 zoom 必填区域字段完整；如果没有这一行，width/height 可能再次变成可选导致合同漂移。
        self.assertTrue(tools_by_name["zoom"]["annotations"]["readOnlyHint"])  # 新增代码+ClaudeCodeParity：断言 zoom 是只读观察工具；如果没有这一行，安全提示可能错误标成会操作桌面。
        self.assertEqual({"keys"}, set(hold_key_schema["required"]))  # 新增代码+ClaudeCodeParity：断言 hold_key 必填 keys 数组而不是 singular key；如果没有这一行，公共合同会继续和 Windows runtime 漂移。
        self.assertEqual("array", hold_key_schema["properties"]["keys"]["type"])  # 新增代码+ClaudeCodeParity：断言 hold_key.keys 是数组；如果没有这一行，单字符串 key 漂移不会被测试发现。
        self.assertIn("duration_seconds", hold_key_schema["properties"])  # 新增代码+ClaudeCodeParity：断言 hold_key 保留可选持续时间；如果没有这一行，长按时长参数可能被误删。
        self.assertNotIn("duration_seconds", hold_key_schema["required"])  # 新增代码+ClaudeCodeParity：断言 hold_key 持续时间不是必填；如果没有这一行，模型可能被迫提供非必要时长。
        self.assertEqual({"start_x", "start_y", "end_x", "end_y"}, set(drag_schema["required"]))  # 新增代码+ClaudeCodeParity：断言拖拽必填起点终点；如果没有这一行，拖拽工具可能缺少关键坐标。
        self.assertEqual({"x", "y"}, set(middle_schema["required"]))  # 新增代码+ClaudeCodeParity：断言中键点击必填坐标；如果没有这一行，中键工具可能在没有目标点时被调用。
        self.assertEqual({"x", "y"}, set(triple_schema["required"]))  # 新增代码+ClaudeCodeParity：断言三击必填坐标；如果没有这一行，三击工具可能在没有目标点时被调用。
        self.assertEqual({"x", "y"}, set(mouse_down_schema["required"]))  # 新增代码+ClaudeCodeParity：断言左键按下必填坐标；如果没有这一行，按下动作可能缺少落点。
        self.assertEqual({"x", "y"}, set(mouse_up_schema["required"]))  # 修改代码+ClaudeCodeParity：断言左键释放必填 x/y 坐标；如果没有这一行，模型不会知道释放点且证据链会丢坐标。
        self.assertIn("reason", mouse_up_schema["properties"])  # 新增代码+ClaudeCodeParity：断言左键释放仍保留可选 reason；如果没有这一行，工具调用目的无法记录。
        for action_name in {"hold_key", "left_click_drag", "middle_click", "triple_click", "left_mouse_down", "left_mouse_up"}:  # 新增代码+ClaudeCodeParity：遍历所有非只读 parity 动作；如果没有这一行，每个动作都要手写断言且容易漏掉。
            self.assertFalse(tools_by_name[action_name]["annotations"]["readOnlyHint"], action_name)  # 新增代码+ClaudeCodeParity：断言非只读动作不能标成 readOnly；如果没有这一行，模型和安全层可能误以为动作不会改变桌面。
    # 新增代码+ClaudeCodeParity：函数段结束，test_claudecode_parity_tool_schemas_lock_required_fields 到此结束；如果没有这个边界说明，用户不容易看出 schema 合同测试范围。

    # 新增代码+ComputerUseMcpV2RedTests：函数段开始，test_v2_runtime_dispatch_marks_v2_and_avoids_legacy_adapter 验证执行路径不是旧 adapter；如果没有这段测试，工具名换了但底层仍可能走旧 computer_action。
    def test_v2_runtime_dispatch_marks_v2_and_avoids_legacy_adapter(self) -> None:  # 新增代码+ComputerUseMcpV2RedTests：声明 runtime 路由测试；如果没有这一行，执行路径合同没有自动化保护。
        trace_events: list[dict[str, Any]] = []  # 新增代码+ComputerUseMcpV2RedTests：保存 fake trace 事件；如果没有这一行，测试无法确认 runtime 写入 v2 证据。
        context = ComputerUseMcpV2Context(host=_FakeV2Host(), record_runtime_trace=trace_events.append)  # 新增代码+ComputerUseMcpV2RedTests：构造最小 v2 上下文；如果没有这一行，runtime 无法获得宿主动作和 trace 回调。
        result = dispatch_computer_use_mcp_v2_tool("mcp__computer-use__cursor_position", {}, context)  # 新增代码+ComputerUseMcpV2RedTests：用模型可见前缀名调用 v2 工具；如果没有这一行，前缀规范化不会被验证。
        self.assertTrue(result["ok"], result)  # 新增代码+ComputerUseMcpV2RedTests：断言 v2 工具执行成功；如果没有这一行，失败路径可能伪装成通过。
        self.assertEqual("computer_use_mcp_v2", result["runtime"])  # 新增代码+ComputerUseMcpV2RedTests：断言结果标记来自 v2 runtime；如果没有这一行，旧 runtime 仍可能冒充成功。
        self.assertFalse(result["legacy_adapter_used"])  # 新增代码+ComputerUseMcpV2RedTests：断言没有使用旧 adapter；如果没有这一行，v2 目标会被旧链路吞掉。
        self.assertTrue(any(event.get("runtime") == "computer_use_mcp_v2" for event in trace_events))  # 新增代码+ComputerUseMcpV2RedTests：断言 trace 也写入 v2 标记；如果没有这一行，证据链无法区分新旧执行器。
    # 新增代码+ComputerUseMcpV2RedTests：函数段结束，test_v2_runtime_dispatch_marks_v2_and_avoids_legacy_adapter 到此结束；如果没有这个边界说明，用户不容易看出路由测试范围。

    # 新增代码+ComputerUseMcpV2RedTests：函数段开始，test_v2_batch_rejects_legacy_and_alias_tools 验证批量工具不能把旧接口重新带回来；如果没有这段测试，computer_batch 可能成为旧接口后门。
    def test_v2_batch_rejects_legacy_and_alias_tools(self) -> None:  # 新增代码+ComputerUseMcpV2RedTests：声明 batch 拒绝测试；如果没有这一行，批量动作安全边界没有自动化保护。
        context = ComputerUseMcpV2Context(host=_FakeV2Host())  # 新增代码+ComputerUseMcpV2RedTests：构造最小 v2 上下文；如果没有这一行，batch 分发没有上下文对象。
        status_result = dispatch_computer_use_mcp_v2_tool("computer_batch", {"actions": [{"tool": "computer_status", "arguments": {}}]}, context)  # 新增代码+ComputerUseMcpV2RedTests：尝试从 batch 调旧状态接口；如果没有这一行，旧四件套后门不会被验证。
        click_result = dispatch_computer_use_mcp_v2_tool("computer_batch", {"actions": [{"tool": "click", "arguments": {"x": 1, "y": 2}}]}, context)  # 新增代码+ComputerUseMcpV2RedTests：尝试从 batch 调旧 click 别名；如果没有这一行，旧点击别名后门不会被验证。
        read_result = dispatch_computer_use_mcp_v2_tool("computer_batch", {"actions": [{"tool": "read", "arguments": {"path": "x.txt"}}]}, context)  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：尝试从 batch 调顶层 read；如果没有这一行，文件工具后门不会被验证。
        shell_result = dispatch_computer_use_mcp_v2_tool("computer_batch", {"actions": [{"tool": "powershell", "arguments": {"command": "whoami"}}]}, context)  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：尝试从 batch 调 PowerShell；如果没有这一行，命令工具后门不会被验证。
        self.assertFalse(status_result["ok"], status_result)  # 新增代码+ComputerUseMcpV2RedTests：断言旧状态接口被拒绝；如果没有这一行，batch 可能成功调用旧工具。
        self.assertFalse(click_result["ok"], click_result)  # 新增代码+ComputerUseMcpV2RedTests：断言旧 click 别名被拒绝；如果没有这一行，batch 可能绕过 left_click 规范。
        self.assertFalse(read_result["ok"], read_result)  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：断言顶层 read 被 batch 拒绝；如果没有这一行，文件工具可能绕过 Computer Use 工具池。
        self.assertFalse(shell_result["ok"], shell_result)  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：断言 PowerShell 被 batch 拒绝；如果没有这一行，命令工具可能绕过 Computer Use 工具池。
        self.assertIn("legacy", status_result["reason"])  # 新增代码+ComputerUseMcpV2RedTests：断言失败原因明确指出 legacy；如果没有这一行，模型难以理解为什么被拒绝。
        self.assertIn("legacy", click_result["reason"])  # 新增代码+ComputerUseMcpV2RedTests：断言旧别名失败原因明确；如果没有这一行，排查时无法快速定位别名问题。
        self.assertIn("legacy", read_result["reason"])  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：断言 read 拒绝原因明确；如果没有这一行，排查时无法快速定位文件工具混入。
        self.assertIn("legacy", shell_result["reason"])  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：断言 PowerShell 拒绝原因明确；如果没有这一行，排查时无法快速定位命令工具混入。
    # 新增代码+ComputerUseMcpV2RedTests：函数段结束，test_v2_batch_rejects_legacy_and_alias_tools 到此结束；如果没有这个边界说明，用户不容易看出 batch 安全测试范围。

    # 新增代码+ClaudeCodeParity：函数段开始，test_v2_batch_reports_failure_when_parity_step_fails 验证 batch 顶层 ok 不会掩盖 parity 步骤失败；如果没有这段测试，computer_batch 可能把失败桌面动作包装成成功。
    def test_v2_batch_reports_failure_when_parity_step_fails(self) -> None:  # 新增代码+ClaudeCodeParity：声明 batch parity 失败语义测试；如果没有这一行，unittest 不会执行顶层失败合同。
        class _FailingHoldKeyHost:  # 新增代码+ClaudeCodeParity：类段开始，模拟 hold_key host 返回失败；如果没有这个 fake，测试无法稳定制造 parity 工具失败。
            def __init__(self) -> None:  # 新增代码+ClaudeCodeParity：函数段开始，初始化调用记录；如果没有这段函数，测试无法确认 stop_on_error 是否停止后续步骤。
                self.calls: list[str] = []  # 新增代码+ClaudeCodeParity：保存被调用的方法名；如果没有这一行，batch 停止语义无法断言。
            # 新增代码+ClaudeCodeParity：函数段结束，_FailingHoldKeyHost.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake 状态范围。
            def hold_key(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，模拟新增 parity hold_key 失败；如果没有这段函数，runtime 会把 host 当成缺失能力。
                self.calls.append("hold_key")  # 新增代码+ClaudeCodeParity：记录 hold_key 已执行；如果没有这一行，测试无法证明失败来自已执行步骤。
                return {"ok": False, "reason": "task4_hold_key_rejected", "error_class": "task4_parity_failure", "arguments": dict(arguments)}  # 新增代码+ClaudeCodeParity：返回结构化失败；如果没有这一行，batch 顶层失败条件没有输入。
            # 新增代码+ClaudeCodeParity：函数段结束，_FailingHoldKeyHost.hold_key 到此结束；如果没有这个边界说明，用户不容易看出 fake 失败范围。
            def triple_click(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，提供后续步骤用于验证 stop_on_error；如果没有这段函数，无法区分停止和缺方法。
                self.calls.append("triple_click")  # 新增代码+ClaudeCodeParity：记录后续步骤执行；如果没有这一行，测试无法发现失败后仍继续执行。
                return {"ok": True, "method": "triple_click", "arguments": dict(arguments)}  # 新增代码+ClaudeCodeParity：模拟后续步骤成功；如果没有这一行，batch 继续执行时没有可观察结果。
            # 新增代码+ClaudeCodeParity：函数段结束，_FailingHoldKeyHost.triple_click 到此结束；如果没有这个边界说明，用户不容易看出 fake 后续动作范围。
        # 新增代码+ClaudeCodeParity：类段结束，_FailingHoldKeyHost 到此结束；如果没有这个边界说明，用户不容易看出 batch fake host 的完整范围。
        host = _FailingHoldKeyHost()  # 新增代码+ClaudeCodeParity：创建失败 fake host；如果没有这一行，batch 测试没有可控宿主。
        context = ComputerUseMcpV2Context(host=host)  # 新增代码+ClaudeCodeParity：把 fake host 注入 v2 runtime；如果没有这一行，步骤会走 host_required 而不是 parity 失败。
        result = dispatch_computer_use_mcp_v2_tool("computer_batch", {"actions": [{"tool": "hold_key", "arguments": {"keys": ["ctrl"], "duration_seconds": 0.1}}, {"tool": "triple_click", "arguments": {"x": 1, "y": 2}}]}, context)  # 新增代码+ClaudeCodeParity：执行先失败后成功的 batch；如果没有这一行，顶层 ok 语义没有可验证输出。
        self.assertFalse(result["ok"], result)  # 新增代码+ClaudeCodeParity：断言 batch 顶层失败；如果没有这一行，失败步骤仍会被 success_result 掩盖。
        self.assertEqual(1, result["payload"]["step_count"])  # 新增代码+ClaudeCodeParity：断言 stop_on_error 后只执行一个步骤；如果没有这一行，失败后继续真实动作的风险不会暴露。
        self.assertFalse(result["payload"]["results"][0]["ok"])  # 新增代码+ClaudeCodeParity：断言步骤明细保留原失败；如果没有这一行，用户无法看到是哪一步失败。
        self.assertEqual(["hold_key"], host.calls)  # 新增代码+ClaudeCodeParity：断言失败后没有执行 triple_click；如果没有这一行，stop_on_error 语义可能被破坏。
    # 新增代码+ClaudeCodeParity：函数段结束，test_v2_batch_reports_failure_when_parity_step_fails 到此结束；如果没有这个边界说明，用户不容易看出 batch 失败语义测试范围。

    # 新增代码+ClaudeCodeParity：函数段开始，test_mutating_actions_fail_without_host 验证没有 host 的真实桌面动作必须明确失败；如果没有这段测试，无 host 假成功会继续误导模型和用户。
    def test_mutating_actions_fail_without_host(self) -> None:  # 新增代码+ClaudeCodeParity：声明无 host 写动作失败测试；如果没有这一行，unittest 不会执行无 host 安全合同。
        result = dispatch_computer_use_mcp_v2_tool("mcp__computer-use__left_click", {"x": 1, "y": 2}, ComputerUseMcpV2Context())  # 新增代码+ClaudeCodeParity：用没有 host 的上下文调用真实左键动作；如果没有这一行，测试无法复现 noop 假成功问题。
        self.assertFalse(result["ok"], result)  # 新增代码+ClaudeCodeParity：断言写动作不能在无 host 时成功；如果没有这一行，假成功不会被测试拦住。
        self.assertEqual("host_required", result["error_class"])  # 新增代码+ClaudeCodeParity：断言失败类别是 host_required；如果没有这一行，模型无法区分缺 host 和未知工具等其他错误。
        self.assertFalse(result["payload"]["desktop_action_performed"])  # 新增代码+ClaudeCodeParity：断言没有真实桌面动作发生；如果没有这一行，失败结果可能仍让验收误判已操作桌面。
    # 新增代码+ClaudeCodeParity：函数段结束，test_mutating_actions_fail_without_host 到此结束；如果没有这个边界说明，用户不容易看出无 host 合同测试范围。

    # 新增代码+ClaudeCodeParity：函数段开始，test_new_parity_tools_dispatch_to_host_methods 验证 7 个 parity 工具都能转发到同名 host 方法；如果没有这段测试，新工具可能只暴露 schema 却不能执行。
    def test_new_parity_tools_dispatch_to_host_methods(self) -> None:  # 新增代码+ClaudeCodeParity：声明新 parity 工具 host 分发测试；如果没有这一行，unittest 不会检查新工具运行时桥接。
        host = _FakeParityHost()  # 新增代码+ClaudeCodeParity：创建记录调用顺序的 fake host；如果没有这一行，测试无法确认具体调用了哪些 host 方法。
        context = ComputerUseMcpV2Context(host=host)  # 新增代码+ClaudeCodeParity：把 fake host 注入 v2 runtime；如果没有这一行，新工具仍会走无 host 分支。
        tool_calls = [  # 新增代码+ClaudeCodeParity：按用户要求列出 7 个 parity 工具调用；如果没有这个列表，测试会散落重复代码且顺序不清楚。
            ("mcp__computer-use__zoom", {"x": 1, "y": 2, "width": 3, "height": 4}),  # 新增代码+ClaudeCodeParity：覆盖 zoom 只读工具；如果没有这一项，zoom host bridge 可能缺失。
            ("mcp__computer-use__hold_key", {"keys": ["ctrl"], "duration_seconds": 0.1}),  # 新增代码+ClaudeCodeParity：覆盖 hold_key 且使用 keys 数组；如果没有这一项，Task 1 schema 合同可能和 runtime 分发脱节。
            ("mcp__computer-use__left_click_drag", {"start_x": 1, "start_y": 2, "end_x": 3, "end_y": 4}),  # 新增代码+ClaudeCodeParity：覆盖左键拖拽工具；如果没有这一项，拖拽桥接缺失不会暴露。
            ("mcp__computer-use__middle_click", {"x": 1, "y": 2}),  # 新增代码+ClaudeCodeParity：覆盖中键点击工具；如果没有这一项，中键桥接缺失不会暴露。
            ("mcp__computer-use__triple_click", {"x": 1, "y": 2}),  # 新增代码+ClaudeCodeParity：覆盖三击工具；如果没有这一项，三击桥接缺失不会暴露。
            ("mcp__computer-use__left_mouse_down", {"x": 1, "y": 2}),  # 新增代码+ClaudeCodeParity：覆盖左键按下工具；如果没有这一项，按下桥接缺失不会暴露。
            ("mcp__computer-use__left_mouse_up", {"x": 1, "y": 2, "reason": "test-release"}),  # 修改代码+ClaudeCodeParity：按公开 schema 带坐标覆盖左键释放工具；如果没有这一项，释放桥接可能继续丢失 x/y。
        ]  # 新增代码+ClaudeCodeParity：结束 7 个 parity 工具调用清单；如果没有这一行，Python 列表语法不完整。
        results = [dispatch_computer_use_mcp_v2_tool(tool_name, arguments, context) for tool_name, arguments in tool_calls]  # 新增代码+ClaudeCodeParity：逐个通过真实 runtime 分发工具；如果没有这一行，测试只检查数据不检查运行路径。
        for result in results:  # 新增代码+ClaudeCodeParity：逐个检查工具结果；如果没有这一行，某个工具失败时不会被清晰定位。
            self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodeParity：断言每个 parity 工具都成功返回；如果没有这一行，缺桥接工具仍可能悄悄返回失败。
        self.assertEqual(["zoom", "hold_key", "left_click_drag", "middle_click", "triple_click", "left_mouse_down", "left_mouse_up"], host.calls)  # 新增代码+ClaudeCodeParity：断言 host 方法调用顺序精确匹配 7 个工具；如果没有这一行，工具可能调错方法或漏调方法。
        self.assertEqual({"x": 1, "y": 2, "reason": "test-release"}, host.arguments[-1])  # 新增代码+ClaudeCodeParity：断言 left_mouse_up 桥接到 host 时保留坐标；如果没有这一行，runtime 可能成功但悄悄丢掉释放位置。
    # 新增代码+ClaudeCodeParity：函数段结束，test_new_parity_tools_dispatch_to_host_methods 到此结束；如果没有这个边界说明，用户不容易看出 host bridge 合同测试范围。

    # 新增代码+ComputerUseMcpV2RedTests：函数段开始，test_v2_server_selftest_reports_exact_surface 验证 server 自检使用 v2 工具面；如果没有这段测试，旧 server selftest 仍可能通过。
    def test_v2_server_selftest_reports_exact_surface(self) -> None:  # 新增代码+ComputerUseMcpV2RedTests：声明 server 自检测试；如果没有这一行，server 入口合同没有自动化保护。
        report = run_selftest()  # 新增代码+ComputerUseMcpV2RedTests：运行 v2 server 自检；如果没有这一行，测试无法获得 server 报告。
        self.assertTrue(report["passed"], report)  # 新增代码+ComputerUseMcpV2RedTests：断言自检通过；如果没有这一行，失败自检可能被忽略。
        self.assertEqual("COMPUTER_USE_MCP_V2_READY", report["marker"])  # 新增代码+ComputerUseMcpV2RedTests：断言 v2 ready marker；如果没有这一行，旧 marker 可能继续冒充新 server。
        self.assertEqual(sorted(EXPECTED_RAW_TOOL_NAMES), sorted(report["tool_names"]))  # 新增代码+ComputerUseMcpV2RedTests：断言 selftest 报告精确工具名；如果没有这一行，server 报告和 schema 可能不一致。
    # 新增代码+ComputerUseMcpV2RedTests：函数段结束，test_v2_server_selftest_reports_exact_surface 到此结束；如果没有这个边界说明，用户不容易看出 selftest 范围。


class _FakeV2Host:  # 新增代码+ComputerUseMcpV2RedTests：定义 fake Windows host；如果没有这个辅助类，runtime 测试会依赖真实鼠标和桌面。
    # 新增代码+ComputerUseMcpV2RedTests：函数段开始，cursor_position 模拟读取鼠标坐标；如果没有这段函数，cursor_position 测试无法无副作用运行。
    def cursor_position(self) -> dict[str, int]:  # 新增代码+ComputerUseMcpV2RedTests：声明 fake 光标读取入口；如果没有这一行，runtime 调用 host 时会找不到方法。
        return {"x": 11, "y": 22}  # 新增代码+ComputerUseMcpV2RedTests：返回固定坐标用于断言；如果没有这一行，工具结果没有可验证数据。
    # 新增代码+ComputerUseMcpV2RedTests：函数段结束，cursor_position 到此结束；如果没有这个边界说明，用户不容易看出 fake host 范围。


class _FakeParityHost:  # 新增代码+ClaudeCodeParity：类段开始，记录 Task 2 新 parity 工具是否调到同名 host 方法；如果没有这个 fake host，测试会依赖真实桌面动作。
    def __init__(self) -> None:  # 新增代码+ClaudeCodeParity：函数段开始，初始化 fake host 调用记录；如果没有这段函数，测试无法判断调用顺序。
        self.calls: list[str] = []  # 新增代码+ClaudeCodeParity：保存已调用的方法名；如果没有这一行，host bridge 测试无法断言 7 个方法的顺序。
        self.arguments: list[dict[str, Any]] = []  # 新增代码+ClaudeCodeParity：保存每次 host 调用的参数副本；如果没有这一行，测试无法证明 left_mouse_up 坐标被真实保留。
    # 新增代码+ClaudeCodeParity：函数段结束，__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake host 状态初始化范围。

    def _record(self, method_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，统一记录 fake host 调用并返回结构化成功；如果没有这段函数，每个 fake 方法都要重复记录逻辑。
        self.calls.append(method_name)  # 新增代码+ClaudeCodeParity：记录当前被调用的方法名；如果没有这一行，测试无法证明 runtime 调到了正确 host 方法。
        self.arguments.append(dict(arguments))  # 新增代码+ClaudeCodeParity：记录参数快照用于检查坐标透传；如果没有这一行，host 调用成功也无法证明 x/y 没丢。
        return {"ok": True, "method": method_name, "arguments": dict(arguments)}  # 新增代码+ClaudeCodeParity：返回结构化成功 payload；如果没有这一行，runtime 可能把 None 当成未实现 host 方法。
    # 新增代码+ClaudeCodeParity：函数段结束，_record 到此结束；如果没有这个边界说明，用户不容易看出 fake host 记录逻辑范围。

    def zoom(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，模拟 zoom host 方法；如果没有这段函数，zoom 会被 runtime 当成无 host 实现。
        return self._record("zoom", arguments)  # 新增代码+ClaudeCodeParity：记录 zoom 调用；如果没有这一行，zoom bridge 无法产生可断言结果。
    # 新增代码+ClaudeCodeParity：函数段结束，zoom 到此结束；如果没有这个边界说明，用户不容易看出 zoom fake 方法范围。

    def hold_key(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，模拟 hold_key host 方法；如果没有这段函数，hold_key 会被 runtime 当成未知或无 host 实现。
        return self._record("hold_key", arguments)  # 新增代码+ClaudeCodeParity：记录 hold_key 调用；如果没有这一行，hold_key bridge 无法产生可断言结果。
    # 新增代码+ClaudeCodeParity：函数段结束，hold_key 到此结束；如果没有这个边界说明，用户不容易看出 hold_key fake 方法范围。

    def left_click_drag(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，模拟 left_click_drag host 方法；如果没有这段函数，拖拽工具无法证明桥接到 host。
        return self._record("left_click_drag", arguments)  # 新增代码+ClaudeCodeParity：记录 left_click_drag 调用；如果没有这一行，拖拽 bridge 无法产生可断言结果。
    # 新增代码+ClaudeCodeParity：函数段结束，left_click_drag 到此结束；如果没有这个边界说明，用户不容易看出拖拽 fake 方法范围。

    def middle_click(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，模拟 middle_click host 方法；如果没有这段函数，中键工具无法证明桥接到 host。
        return self._record("middle_click", arguments)  # 新增代码+ClaudeCodeParity：记录 middle_click 调用；如果没有这一行，中键 bridge 无法产生可断言结果。
    # 新增代码+ClaudeCodeParity：函数段结束，middle_click 到此结束；如果没有这个边界说明，用户不容易看出中键 fake 方法范围。

    def triple_click(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，模拟 triple_click host 方法；如果没有这段函数，三击工具无法证明桥接到 host。
        return self._record("triple_click", arguments)  # 新增代码+ClaudeCodeParity：记录 triple_click 调用；如果没有这一行，三击 bridge 无法产生可断言结果。
    # 新增代码+ClaudeCodeParity：函数段结束，triple_click 到此结束；如果没有这个边界说明，用户不容易看出三击 fake 方法范围。

    def left_mouse_down(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，模拟 left_mouse_down host 方法；如果没有这段函数，按下工具无法证明桥接到 host。
        return self._record("left_mouse_down", arguments)  # 新增代码+ClaudeCodeParity：记录 left_mouse_down 调用；如果没有这一行，按下 bridge 无法产生可断言结果。
    # 新增代码+ClaudeCodeParity：函数段结束，left_mouse_down 到此结束；如果没有这个边界说明，用户不容易看出按下 fake 方法范围。

    def left_mouse_up(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，模拟 left_mouse_up host 方法；如果没有这段函数，释放工具无法证明桥接到 host。
        return self._record("left_mouse_up", arguments)  # 新增代码+ClaudeCodeParity：记录 left_mouse_up 调用；如果没有这一行，释放 bridge 无法产生可断言结果。
    # 新增代码+ClaudeCodeParity：函数段结束，left_mouse_up 到此结束；如果没有这个边界说明，用户不容易看出释放 fake 方法范围。
# 新增代码+ClaudeCodeParity：类段结束，_FakeParityHost 到此结束；如果没有这个边界说明，用户不容易看出新 parity fake host 的完整范围。


if __name__ == "__main__":  # 新增代码+ComputerUseMcpV2RedTests：允许直接运行本测试文件；如果没有这一行，手动调试不方便。
    unittest.main()  # 新增代码+ComputerUseMcpV2RedTests：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行测试。
