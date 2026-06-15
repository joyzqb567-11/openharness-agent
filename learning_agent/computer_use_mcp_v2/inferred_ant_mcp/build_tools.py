"""Computer Use MCP v2 模型可见工具面。"""  # 新增代码+ComputerUseMcpV2：说明本文件是 v2 工具 schema 唯一事实源；如果没有这行代码，旧 schema 和新 schema 容易混用。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，运行时导入更容易受类型顺序影响。

from copy import deepcopy  # 新增代码+ComputerUseMcpV2：导入深拷贝保护全局 schema；如果没有这行代码，调用方可能污染工具定义。
from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，schema helper 边界不清楚。

COMPUTER_USE_MCP_SERVER_NAME = "computer-use"  # 新增代码+ComputerUseMcpV2：固定 MCP server 名；如果没有这行代码，registry 前缀可能和 ClaudeCode 风格不一致。
COMPUTER_USE_MCP_READY_MARKER = "COMPUTER_USE_MCP_V2_READY"  # 新增代码+ComputerUseMcpV2：固定 v2 自检 marker；如果没有这行代码，旧 server 可能冒充新 server。
COMPUTER_USE_MCP_TOOL_NAMES = (  # 新增代码+ComputerUseMcpV2：函数段开始，按用户确认顺序列出唯一可见工具；如果没有这段常量，工具面容易多出旧接口。
    "request_access",  # 新增代码+ComputerUseMcpV2：申请桌面控制权限；如果没有这一项，模型无法先请求授权。
    "observe",  # 新增代码+ComputerUseMcpV2：观察当前桌面；如果没有这一项，模型缺少 ClaudeCode 风格观察入口。
    "screenshot",  # 新增代码+ComputerUseMcpV2：获取屏幕截图；如果没有这一项，视觉任务无法起步。
    "cursor_position",  # 新增代码+ComputerUseMcpV2：读取鼠标坐标；如果没有这一项，模型无法确认指针状态。
    "mouse_move",  # 新增代码+ComputerUseMcpV2：移动鼠标；如果没有这一项，模型无法定位后再点击。
    "left_click",  # 新增代码+ComputerUseMcpV2：左键单击；如果没有这一项，模型会退回旧 click。
    "double_click",  # 新增代码+ComputerUseMcpV2：双击；如果没有这一项，文件和图标打开动作无法表达。
    "right_click",  # 新增代码+ComputerUseMcpV2：右键；如果没有这一项，上下文菜单无法操作。
    "type",  # 新增代码+ComputerUseMcpV2：输入文本；如果没有这一项，浏览器和 Office 输入任务无法执行。
    "key",  # 新增代码+ComputerUseMcpV2：按键或快捷键；如果没有这一项，Enter、Ctrl+S 等动作无法表达。
    "scroll",  # 新增代码+ComputerUseMcpV2：滚动界面；如果没有这一项，长页面无法操作。
    "wait",  # 新增代码+ComputerUseMcpV2：等待界面变化；如果没有这一项，模型会用无意义动作替代等待。
    "read_clipboard",  # 新增代码+ComputerUseMcpV2：读取剪贴板；如果没有这一项，复制结果无法检查。
    "write_clipboard",  # 新增代码+ComputerUseMcpV2：写入剪贴板；如果没有这一项，长文本输入缺少稳妥路线。
    "open_application",  # 新增代码+ComputerUseMcpV2：打开本地应用；如果没有这一项，agent-owned 启动链路会断。
    "list_granted_applications",  # 新增代码+ComputerUseMcpV2：查看授权状态；如果没有这一项，模型无法确认权限范围。
    "computer_batch",  # 新增代码+ComputerUseMcpV2：批量执行原子工具；如果没有这一项，多步桌面动作往返开销更大。
)  # 新增代码+ComputerUseMcpV2：工具名元组结束；如果没有这行代码，Python 语法不完整。
FORBIDDEN_LEGACY_RAW_TOOL_NAMES = {  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：集中保存禁止暴露、直接调用或 batch 调用的旧名/非桌面原子工具名；如果没有这组硬名单，隐藏工具可能通过记忆工具名绕过模型可见工具池。
    "click",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止旧点击别名；如果没有这一项，click 会和 left_click 同轮或同 batch 混用。
    "double_click_mouse",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止历史双击鼠标别名；如果没有这一项，double_click 会和旧名字混用。
    "right_click_mouse",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止历史右键鼠标别名；如果没有这一项，right_click 会和旧名字混用。
    "clipboard",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止旧剪贴板合并入口；如果没有这一项，read_clipboard/write_clipboard 会和旧入口混用。
    "computer_status",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止旧状态工具作为 v2 原始工具；如果没有这一项，旧四件套会通过 runtime 或 batch 回流。
    "computer_observe",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止旧观察工具作为 v2 原始工具；如果没有这一项，observe 会被旧入口竞争。
    "computer_discover",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止旧发现工具作为 v2 原始工具；如果没有这一项，发现能力会继续以旧公开接口出现。
    "computer_action",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止旧动作工具作为 v2 原始工具；如果没有这一项，旧 action 会绕开原子工具面。
    "computer_use",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止旧下划线总入口；如果没有这一项，模型可能继续调用旧聚合工具。
    "computer-use",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止旧连字符总入口；如果没有这一项，server 名和工具名会继续混淆。
    "read",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止顶层文件读取工具进入 Computer Use MCP 原始工具面；如果没有这一项，read 可能通过 batch 抢走桌面观察任务。
    "write",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止顶层文件写入工具进入 Computer Use MCP 原始工具面；如果没有这一项，write 可能被误当成桌面输入文字。
    "edit",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止顶层文件编辑工具进入 Computer Use MCP 原始工具面；如果没有这一项，edit 可能被误当成 Office 或浏览器编辑。
    "bash",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止 shell 工具名进入 Computer Use MCP 原始工具面；如果没有这一项，bash 可能绕开工具池过滤。
    "powershell",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止 PowerShell 工具名进入 Computer Use MCP 原始工具面；如果没有这一项，Windows 命令能力可能伪装成桌面工具。
    "shell",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止通用 shell 工具名进入 Computer Use MCP 原始工具面；如果没有这一项，命令执行入口可能混入。
    "run_powershell",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止历史 PowerShell 执行别名；如果没有这一项，shell 能力可能通过旧名进入 batch。
    "start_background_command",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止后台命令工具名；如果没有这一项，长命令能力可能绕过 Computer Use 隔离。
    "zoom",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止蓝图外 zoom 工具；如果没有这一项，工具面会大于用户确认范围。
    "hold_key",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止蓝图外 hold_key 工具；如果没有这一项，工具面会偏离 ClaudeCode 清单。
    "left_click_drag",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止蓝图外拖拽工具；如果没有这一项，拖拽职责会和 computer_batch 混乱。
    "middle_click",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止预留中键工具默认进入 v2；如果没有这一项，未成熟鼠标工具会回流。
    "triple_click",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止预留三击工具默认进入 v2；如果没有这一项，低频动作会抢占模型注意力。
    "left_mouse_down",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止预留左键按下工具默认进入 v2；如果没有这一项，拆分鼠标动作可能绕过安全动作。
    "left_mouse_up",  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止预留左键释放工具默认进入 v2；如果没有这一项，拆分鼠标动作可能和批量动作冲突。
}  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止工具名集合结束；如果没有这行代码，Python 集合语法不完整。
SHELL_FORBIDDEN_TOOL_NAMES = {"bash", "powershell", "shell", "run_powershell", "start_background_command"}  # 新增代码+ComputerUseMcpV2：集中保存禁止进入 Computer Use MCP 的命令类工具名；如果没有这行代码，桌面 MCP 可能被误用成命令执行入口。
SHELL_FORBIDDEN_ARGUMENT_NAMES = {"command", "powershell", "bash", "script", "executable"}  # 新增代码+ComputerUseMcpV2：集中保存禁止参数字段；如果没有这行代码，模型可能把命令塞进 batch 参数。


def _schema(properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，生成封闭对象 schema；如果没有这段函数，每个工具都要重复写 schema 样板。
    return {"type": "object", "properties": deepcopy(properties or {}), "required": list(required or []), "additionalProperties": False}  # 新增代码+ComputerUseMcpV2：返回标准 JSON Schema；如果没有这行代码，串味参数可能进入工具。
# 新增代码+ComputerUseMcpV2：函数段结束，_schema 到此结束；如果没有这个边界说明，用户不容易看出 schema helper 范围。


def _tool(name: str, description: str, properties: dict[str, Any] | None = None, required: list[str] | None = None, *, read_only: bool = False) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，生成 MCP tools/list 条目；如果没有这段函数，工具 metadata 会不一致。
    return {"name": name, "description": description, "inputSchema": _schema(properties, required), "annotations": {"readOnlyHint": bool(read_only), "destructiveHint": not bool(read_only), "openWorldHint": False}, "_meta": {"openharness/runtime": "computer_use_mcp_v2", "openharness/capability_pack": "computer_use"}}  # 新增代码+ComputerUseMcpV2：返回工具 schema 条目；如果没有这行代码，registry 无法发现工具参数和能力包。
# 新增代码+ComputerUseMcpV2：函数段结束，_tool 到此结束；如果没有这个边界说明，用户不容易看出单工具 schema 范围。


def computer_use_mcp_tools() -> list[dict[str, Any]]:  # 新增代码+ComputerUseMcpV2：函数段开始，返回 v2 工具清单副本；如果没有这段函数，server 和测试没有统一工具面入口。
    point = {"x": {"type": "integer", "description": "屏幕坐标 x。"}, "y": {"type": "integer", "description": "屏幕坐标 y。"}}  # 新增代码+ComputerUseMcpV2：复用坐标字段；如果没有这行代码，鼠标工具 schema 会重复且容易漂移。
    tools = [  # 新增代码+ComputerUseMcpV2：开始构造工具列表；如果没有这行代码，函数没有可返回内容。
        _tool("request_access", "请求受控桌面应用访问权限。", {"applications": {"type": "array", "items": {"type": "string"}}, "reason": {"type": "string"}}, ["applications", "reason"], read_only=True),  # 新增代码+ComputerUseMcpV2：定义授权申请工具；如果没有这行代码，模型无法请求控制权限。
        _tool("observe", "观察当前桌面状态。", {"reason": {"type": "string"}}, read_only=True),  # 新增代码+ComputerUseMcpV2：定义 observe 工具；如果没有这行代码，模型缺少观察入口。
        _tool("screenshot", "获取当前屏幕截图摘要。", {"reason": {"type": "string"}}, read_only=True),  # 新增代码+ComputerUseMcpV2：定义 screenshot 工具；如果没有这行代码，视觉状态无法获取。
        _tool("cursor_position", "读取当前鼠标指针位置。", {"reason": {"type": "string"}}, read_only=True),  # 新增代码+ComputerUseMcpV2：定义光标位置工具；如果没有这行代码，模型无法查询鼠标状态。
        _tool("mouse_move", "移动鼠标到指定坐标。", {**point, "reason": {"type": "string"}}, ["x", "y"]),  # 新增代码+ComputerUseMcpV2：定义移动鼠标工具；如果没有这行代码，模型无法移动指针。
        _tool("left_click", "在指定坐标执行左键单击。", {**point, "reason": {"type": "string"}}, ["x", "y"]),  # 新增代码+ComputerUseMcpV2：定义左键工具；如果没有这行代码，旧 click 会重新变成首选。
        _tool("double_click", "在指定坐标执行双击。", {**point, "reason": {"type": "string"}}, ["x", "y"]),  # 新增代码+ComputerUseMcpV2：定义双击工具；如果没有这行代码，打开类动作无法表达。
        _tool("right_click", "在指定坐标执行右键。", {**point, "reason": {"type": "string"}}, ["x", "y"]),  # 新增代码+ComputerUseMcpV2：定义右键工具；如果没有这行代码，右键菜单任务无法表达。
        _tool("type", "向当前焦点输入文本。", {"text": {"type": "string"}, "reason": {"type": "string"}}, ["text"]),  # 新增代码+ComputerUseMcpV2：定义输入文本工具；如果没有这行代码，文本输入无法表达。
        _tool("key", "按下单个按键或快捷键。", {"keys": {"type": "array", "items": {"type": "string"}}, "reason": {"type": "string"}}, ["keys"]),  # 新增代码+ComputerUseMcpV2：定义按键工具；如果没有这行代码，快捷键无法表达。
        _tool("scroll", "滚动当前界面。", {**point, "delta_y": {"type": "integer"}, "reason": {"type": "string"}}, ["x", "y", "delta_y"]),  # 新增代码+ComputerUseMcpV2：定义滚动工具；如果没有这行代码，长页面无法控制。
        _tool("wait", "等待界面变化。", {"seconds": {"type": "number"}, "reason": {"type": "string"}}, read_only=True),  # 新增代码+ComputerUseMcpV2：定义等待工具；如果没有这行代码，加载等待没有标准入口。
        _tool("read_clipboard", "读取受控剪贴板内容。", {"reason": {"type": "string"}}, read_only=True),  # 新增代码+ComputerUseMcpV2：定义读剪贴板工具；如果没有这行代码，复制检查无法表达。
        _tool("write_clipboard", "写入受控剪贴板内容。", {"text": {"type": "string"}, "reason": {"type": "string"}}, ["text"]),  # 新增代码+ComputerUseMcpV2：定义写剪贴板工具；如果没有这行代码，长文本粘贴路线不完整。
        _tool("open_application", "打开本地桌面应用。", {"app_name": {"type": "string"}, "reason": {"type": "string"}}, ["app_name"]),  # 新增代码+ComputerUseMcpV2：定义打开应用工具；如果没有这行代码，agent-owned 启动链路会断。
        _tool("list_granted_applications", "查看当前授权应用摘要。", {}, read_only=True),  # 新增代码+ComputerUseMcpV2：定义授权查询工具；如果没有这行代码，模型无法确认权限状态。
        _tool("computer_batch", "按顺序执行多个 Computer Use v2 原子工具。", {"actions": {"type": "array", "items": {"type": "object"}}, "stop_on_error": {"type": "boolean"}}, ["actions"]),  # 新增代码+ComputerUseMcpV2：定义批量工具；如果没有这行代码，多步任务往返成本更高。
    ]  # 新增代码+ComputerUseMcpV2：工具列表结束；如果没有这行代码，Python 列表语法不完整。
    return deepcopy(tools)  # 新增代码+ComputerUseMcpV2：返回副本避免全局污染；如果没有这行代码，调用方可能修改全局工具面。
# 新增代码+ComputerUseMcpV2：函数段结束，computer_use_mcp_tools 到此结束；如果没有这个边界说明，用户不容易看出工具面来源。


def assert_no_shell_surface(tools: list[dict[str, Any]] | None = None) -> bool:  # 新增代码+ComputerUseMcpV2：函数段开始，检查 v2 工具面没有命令执行入口；如果没有这段函数，自检无法阻断 shell 回归。
    names = {str(tool.get("name", "")).lower() for tool in (tools if tools is not None else computer_use_mcp_tools())}  # 新增代码+ComputerUseMcpV2：提取工具名集合；如果没有这行代码，检查只能粗糙扫全文。
    return not bool(names.intersection(SHELL_FORBIDDEN_TOOL_NAMES))  # 新增代码+ComputerUseMcpV2：确认没有命令类工具名；如果没有这行代码，bash 类工具可能混入。
# 新增代码+ComputerUseMcpV2：函数段结束，assert_no_shell_surface 到此结束；如果没有这个边界说明，用户不容易看出安全自检范围。
