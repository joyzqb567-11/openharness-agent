"""Computer Use MCP v2 模型可见工具面。"""  # 新增代码+ComputerUseMcpV2：说明本文件是 v2 工具 schema 唯一事实源；如果没有这行代码，旧 schema 和新 schema 容易混用。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，运行时导入更容易受类型顺序影响。

from copy import deepcopy  # 新增代码+ComputerUseMcpV2：导入深拷贝保护全局 schema；如果没有这行代码，调用方可能污染工具定义。
from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，schema helper 边界不清楚。

from .claudecode_protocol import CLAUDECODE_ACTIONS_FIELD, CLAUDECODE_AMOUNT_FIELD, CLAUDECODE_APPS_FIELD, CLAUDECODE_BUNDLE_ID_FIELD, CLAUDECODE_COORDINATE_FIELD, CLAUDECODE_DIRECTION_FIELD, CLAUDECODE_DURATION_FIELD, CLAUDECODE_GRANT_FLAGS_FIELD, CLAUDECODE_REGION_FIELD, CLAUDECODE_START_COORDINATE_FIELD, CLAUDECODE_TEXT_FIELD  # 新增代码+ClaudeCodeProtocolParity：导入 ClaudeCode 主字段常量；如果没有这行代码，schema 字段名会继续散落硬编码。

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
    "middle_click",  # 新增代码+ClaudeCodeParity：公开 ClaudeCode parity 中键点击工具；如果没有这一项，外部 MCP 工具面会缺少中键动作。
    "triple_click",  # 新增代码+ClaudeCodeParity：公开 ClaudeCode parity 三击工具；如果没有这一项，文本段落选择等三击场景无法表达。
    "type",  # 新增代码+ComputerUseMcpV2：输入文本；如果没有这一项，浏览器和 Office 输入任务无法执行。
    "key",  # 新增代码+ComputerUseMcpV2：按键或快捷键；如果没有这一项，Enter、Ctrl+S 等动作无法表达。
    "hold_key",  # 新增代码+ClaudeCodeParity：公开 ClaudeCode parity 按住按键工具；如果没有这一项，长按键盘动作无法表达。
    "scroll",  # 新增代码+ComputerUseMcpV2：滚动界面；如果没有这一项，长页面无法操作。
    "left_click_drag",  # 新增代码+ClaudeCodeParity：公开 ClaudeCode parity 左键拖拽工具；如果没有这一项，拖拽只能依赖不稳定的多步组合。
    "zoom",  # 新增代码+ClaudeCodeParity：公开 ClaudeCode parity 局部放大工具；如果没有这一项，模型无法请求细看屏幕局部区域。
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
    "left_mouse_down",  # 修改代码+AtomicMouseTransaction：禁止模型直接调用左键按下半事务；如果没有这一项，拖拽会被拆成多轮动作并可能在中途被观察门禁打断。
    "left_mouse_up",  # 修改代码+AtomicMouseTransaction：禁止模型直接调用左键释放半事务；如果没有这一项，旧模型可通过记住工具名制造不完整拖拽状态。
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
}  # 修改代码+ComputerUseMcpV2ToolSurfaceFence：禁止工具名集合结束；如果没有这行代码，Python 集合语法不完整。
SHELL_FORBIDDEN_TOOL_NAMES = {"bash", "powershell", "shell", "run_powershell", "start_background_command"}  # 新增代码+ComputerUseMcpV2：集中保存禁止进入 Computer Use MCP 的命令类工具名；如果没有这行代码，桌面 MCP 可能被误用成命令执行入口。
SHELL_FORBIDDEN_ARGUMENT_NAMES = {"command", "powershell", "bash", "script", "executable"}  # 新增代码+ComputerUseMcpV2：集中保存禁止参数字段；如果没有这行代码，模型可能把命令塞进 batch 参数。
REQUEST_ACCESS_BASE_DESCRIPTION = "请求受控桌面应用访问权限。推荐使用 ClaudeCode 字段 apps/reason/grantFlags；兼容旧 applications。"  # 新增代码+ClaudeCodeDynamicToolsList：集中保存 request_access 静态描述；如果没有这行代码，动态 inventory 注入失败时没有稳定回退文案。


def _schema(properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，生成封闭对象 schema；如果没有这段函数，每个工具都要重复写 schema 样板。
    return {"type": "object", "properties": deepcopy(properties or {}), "required": list(required or []), "additionalProperties": False}  # 新增代码+ComputerUseMcpV2：返回标准 JSON Schema；如果没有这行代码，串味参数可能进入工具。
# 新增代码+ComputerUseMcpV2：函数段结束，_schema 到此结束；如果没有这个边界说明，用户不容易看出 schema helper 范围。


def _tool(name: str, description: str, properties: dict[str, Any] | None = None, required: list[str] | None = None, *, read_only: bool = False) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，生成 MCP tools/list 条目；如果没有这段函数，工具 metadata 会不一致。
    return {"name": name, "description": description, "inputSchema": _schema(properties, required), "annotations": {"readOnlyHint": bool(read_only), "destructiveHint": not bool(read_only), "openWorldHint": False}, "_meta": {"openharness/runtime": "computer_use_mcp_v2", "openharness/capability_pack": "computer_use"}}  # 新增代码+ComputerUseMcpV2：返回工具 schema 条目；如果没有这行代码，registry 无法发现工具参数和能力包。
# 新增代码+ComputerUseMcpV2：函数段结束，_tool 到此结束；如果没有这个边界说明，用户不容易看出单工具 schema 范围。


def _request_access_description(app_inventory_hint: str = "") -> str:  # 新增代码+ClaudeCodeDynamicToolsList：函数段开始，生成可选动态 app inventory 描述；如果没有这段函数，tools/list 的动态提示会污染静态 schema 构造。
    safe_hint = str(app_inventory_hint or "").strip()  # 新增代码+ClaudeCodeDynamicToolsList：清理动态 hint 文本；如果没有这行代码，None 或多余空白会进入工具描述。
    if not safe_hint:  # 新增代码+ClaudeCodeDynamicToolsList：没有动态候选时使用静态描述；如果没有这行代码，空 hint 会多出无意义换行。
        return REQUEST_ACCESS_BASE_DESCRIPTION  # 新增代码+ClaudeCodeDynamicToolsList：返回静态回退；如果没有这行代码，inventory 失败会让 request_access 描述为空或不稳定。
    return REQUEST_ACCESS_BASE_DESCRIPTION + "\n" + safe_hint  # 新增代码+ClaudeCodeDynamicToolsList：把安全应用候选拼到描述末尾；如果没有这行代码，模型在 request_access 前看不到 Windows 已安装应用提示。
# 新增代码+ClaudeCodeDynamicToolsList：函数段结束，_request_access_description 到此结束；如果没有这个边界说明，用户不容易看出动态描述拼接范围。


def computer_use_mcp_tools(app_inventory_hint: str = "") -> list[dict[str, Any]]:  # 修改代码+ClaudeCodeDynamicToolsList：函数段开始，返回 v2 工具清单副本并允许 tools/list 注入安全应用提示；如果没有这段函数，server 和测试没有统一工具面入口。
    point = {"x": {"type": "integer", "description": "屏幕坐标 x。"}, "y": {"type": "integer", "description": "屏幕坐标 y。"}}  # 新增代码+ComputerUseMcpV2：复用坐标字段；如果没有这行代码，鼠标工具 schema 会重复且容易漂移。
    coordinate = {CLAUDECODE_COORDINATE_FIELD: {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2, "description": "ClaudeCode 风格屏幕坐标 [x, y]；兼容旧 x/y。"}}  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 主坐标字段；如果没有这行代码，鼠标工具会继续主推 x/y。
    start_coordinate = {CLAUDECODE_START_COORDINATE_FIELD: {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2, "description": "ClaudeCode 风格拖拽起点 [x, y]；兼容旧 start_x/start_y。"}}  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 拖拽起点字段；如果没有这行代码，拖拽 schema 无法对齐 ClaudeCode。
    region = {CLAUDECODE_REGION_FIELD: {"type": "array", "items": {"type": "integer"}, "minItems": 4, "maxItems": 4, "description": "ClaudeCode 风格区域 [x, y, width, height]；兼容旧 x/y/width/height。"}}  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode zoom 区域字段；如果没有这行代码，zoom schema 会继续主推旧四字段。
    app_object = {"type": "object", "properties": {"displayName": {"type": "string"}, "bundleId": {"type": "string"}}, "required": ["displayName"], "additionalProperties": True}  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 授权 app 对象；如果没有这行代码，request_access 无法表达 displayName/bundleId。
    grant_flags = {"type": "object", "properties": {"clipboardRead": {"type": "boolean"}, "clipboardWrite": {"type": "boolean"}, "systemKeyCombos": {"type": "boolean"}}, "additionalProperties": False}  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode grant flags；如果没有这行代码，剪贴板和系统组合键权限没有 schema。
    tools = [  # 新增代码+ComputerUseMcpV2：开始构造工具列表；如果没有这行代码，函数没有可返回内容。
        _tool("request_access", _request_access_description(app_inventory_hint), {CLAUDECODE_APPS_FIELD: {"type": "array", "items": app_object}, "applications": {"type": "array", "items": {"type": "string"}}, CLAUDECODE_GRANT_FLAGS_FIELD: grant_flags, "reason": {"type": "string"}}, [CLAUDECODE_APPS_FIELD, "reason"], read_only=True),  # 修改代码+ClaudeCodeDynamicToolsList：定义 ClaudeCode 风格授权申请 schema并允许动态 app inventory 提示；如果没有这行代码，request_access.description 无法像 ClaudeCode 一样提示已安装应用。
        _tool("observe", "观察当前桌面状态。", {"reason": {"type": "string"}}, read_only=True),  # 新增代码+ComputerUseMcpV2：定义 observe 工具；如果没有这行代码，模型缺少观察入口。
        _tool("screenshot", "获取当前屏幕截图摘要。", {"reason": {"type": "string"}}, read_only=True),  # 新增代码+ComputerUseMcpV2：定义 screenshot 工具；如果没有这行代码，视觉状态无法获取。
        _tool("cursor_position", "读取当前鼠标指针位置。", {"reason": {"type": "string"}}, read_only=True),  # 新增代码+ComputerUseMcpV2：定义光标位置工具；如果没有这行代码，模型无法查询鼠标状态。
        _tool("mouse_move", "移动鼠标到指定坐标。推荐使用 coordinate: [x, y]；兼容旧 x/y。", {**coordinate, **point, "reason": {"type": "string"}}, [CLAUDECODE_COORDINATE_FIELD]),  # 修改代码+ClaudeCodeProtocolParity：定义 ClaudeCode 风格移动鼠标 schema；如果没有这行代码，模型会继续学习旧 x/y 主字段。
        _tool("left_click", "在指定坐标执行左键单击。推荐使用 coordinate: [x, y]；兼容旧 x/y。", {**coordinate, **point, "reason": {"type": "string"}}, [CLAUDECODE_COORDINATE_FIELD]),  # 修改代码+ClaudeCodeProtocolParity：定义 ClaudeCode 风格左键 schema；如果没有这行代码，旧 click/x/y 会继续成为主表达。
        _tool("double_click", "在指定坐标执行双击。推荐使用 coordinate: [x, y]；兼容旧 x/y。", {**coordinate, **point, "reason": {"type": "string"}}, [CLAUDECODE_COORDINATE_FIELD]),  # 修改代码+ClaudeCodeProtocolParity：定义 ClaudeCode 风格双击 schema；如果没有这行代码，双击字段会和 ClaudeCode 不一致。
        _tool("right_click", "在指定坐标执行右键。推荐使用 coordinate: [x, y]；兼容旧 x/y。", {**coordinate, **point, "reason": {"type": "string"}}, [CLAUDECODE_COORDINATE_FIELD]),  # 修改代码+ClaudeCodeProtocolParity：定义 ClaudeCode 风格右键 schema；如果没有这行代码，右键字段会和 ClaudeCode 不一致。
        _tool("middle_click", "在指定坐标执行中键点击。推荐使用 coordinate: [x, y]；兼容旧 x/y。", {**coordinate, **point, "reason": {"type": "string"}}, [CLAUDECODE_COORDINATE_FIELD]),  # 修改代码+ClaudeCodeProtocolParity：定义 ClaudeCode 风格中键 schema；如果没有这行代码，中键工具只有名字对齐参数不对齐。
        _tool("triple_click", "在指定坐标执行三击。推荐使用 coordinate: [x, y]；兼容旧 x/y。", {**coordinate, **point, "reason": {"type": "string"}}, [CLAUDECODE_COORDINATE_FIELD]),  # 修改代码+ClaudeCodeProtocolParity：定义 ClaudeCode 风格三击 schema；如果没有这行代码，三击工具参数会漂移。
        _tool("type", "向当前焦点输入文本。", {"text": {"type": "string"}, "reason": {"type": "string"}}, ["text"]),  # 新增代码+ComputerUseMcpV2：定义输入文本工具；如果没有这行代码，文本输入无法表达。
        _tool("key", "按下单个按键或快捷键。推荐使用 text；兼容旧 keys。", {CLAUDECODE_TEXT_FIELD: {"type": "string"}, "keys": {"type": "array", "items": {"type": "string"}}, "reason": {"type": "string"}}, [CLAUDECODE_TEXT_FIELD]),  # 修改代码+ClaudeCodeProtocolParity：定义 ClaudeCode 风格按键 schema；如果没有这行代码，key 会继续只接受 keys 数组。
        _tool("hold_key", "按住指定按键一段时间。推荐使用 text/duration；兼容旧 keys/duration_seconds。", {CLAUDECODE_TEXT_FIELD: {"type": "string"}, CLAUDECODE_DURATION_FIELD: {"type": "number"}, "keys": {"type": "array", "items": {"type": "string"}}, "duration_seconds": {"type": "number"}, "reason": {"type": "string"}}, [CLAUDECODE_TEXT_FIELD]),  # 修改代码+ClaudeCodeProtocolParity：定义 ClaudeCode 风格长按 schema；如果没有这行代码，hold_key 参数不会对齐 ClaudeCode。
        _tool("scroll", "滚动当前界面。推荐使用 direction/amount，可选 coordinate；兼容旧 x/y/delta_y。", {**coordinate, **point, CLAUDECODE_DIRECTION_FIELD: {"type": "string", "enum": ["up", "down", "left", "right"]}, CLAUDECODE_AMOUNT_FIELD: {"type": "integer"}, "delta_y": {"type": "integer"}, "reason": {"type": "string"}}, [CLAUDECODE_DIRECTION_FIELD, CLAUDECODE_AMOUNT_FIELD]),  # 修改代码+ClaudeCodeProtocolParity：定义 ClaudeCode 风格滚动 schema；如果没有这行代码，scroll 会继续只主推 delta_y。
        _tool("left_click_drag", "从起点按住左键拖拽到终点；这是唯一公开的左键拖拽事务入口，不要拆成 left_mouse_down/mouse_move/left_mouse_up。推荐使用 start_coordinate 和 coordinate；兼容旧 start_x/start_y/end_x/end_y。", {**start_coordinate, **coordinate, "start_x": {"type": "integer"}, "start_y": {"type": "integer"}, "end_x": {"type": "integer"}, "end_y": {"type": "integer"}, CLAUDECODE_DURATION_FIELD: {"type": "number"}, "duration_seconds": {"type": "number"}, "reason": {"type": "string"}}, [CLAUDECODE_START_COORDINATE_FIELD, CLAUDECODE_COORDINATE_FIELD]),  # 修改代码+AtomicMouseTransaction：把公开拖拽工具描述成单次事务入口；如果没有这行代码，模型可能继续把连续拖拽拆成会被门禁打断的半事务。
        _tool("zoom", "读取并放大指定屏幕区域。推荐使用 region: [x, y, width, height]；兼容旧 x/y/width/height。", {**region, "x": {"type": "integer"}, "y": {"type": "integer"}, "width": {"type": "integer"}, "height": {"type": "integer"}, "reason": {"type": "string"}}, [CLAUDECODE_REGION_FIELD], read_only=True),  # 修改代码+ClaudeCodeProtocolParity：定义 ClaudeCode 风格局部放大 schema；如果没有这行代码，zoom 仍只主推旧四字段。
        _tool("wait", "等待界面变化。", {"seconds": {"type": "number"}, "reason": {"type": "string"}}, read_only=True),  # 新增代码+ComputerUseMcpV2：定义等待工具；如果没有这行代码，加载等待没有标准入口。
        _tool("read_clipboard", "读取受控剪贴板内容。", {"reason": {"type": "string"}}, read_only=True),  # 新增代码+ComputerUseMcpV2：定义读剪贴板工具；如果没有这行代码，复制检查无法表达。
        _tool("write_clipboard", "写入受控剪贴板内容。", {"text": {"type": "string"}, "reason": {"type": "string"}}, ["text"]),  # 新增代码+ComputerUseMcpV2：定义写剪贴板工具；如果没有这行代码，长文本粘贴路线不完整。
        _tool("open_application", "打开本地桌面应用。推荐使用 bundle_id；兼容旧 app_name。", {CLAUDECODE_BUNDLE_ID_FIELD: {"type": "string"}, "app_name": {"type": "string"}, "reason": {"type": "string"}}, [CLAUDECODE_BUNDLE_ID_FIELD]),  # 修改代码+ClaudeCodeProtocolParity：定义 ClaudeCode 风格应用启动 schema；如果没有这行代码，open_application 会继续主推 app_name。
        _tool("list_granted_applications", "查看当前授权应用摘要。", {}, read_only=True),  # 新增代码+ComputerUseMcpV2：定义授权查询工具；如果没有这行代码，模型无法确认权限状态。
        _tool("computer_batch", "按顺序执行多个 Computer Use v2 原子工具。推荐使用 actions；兼容旧 steps。", {CLAUDECODE_ACTIONS_FIELD: {"type": "array", "items": {"type": "object"}}, "steps": {"type": "array", "items": {"type": "object"}}, "stop_on_error": {"type": "boolean"}}, [CLAUDECODE_ACTIONS_FIELD]),  # 修改代码+ClaudeCodeProtocolParity：定义 ClaudeCode 风格 batch schema；如果没有这行代码，batch 会继续只靠旧 steps/actions 混合约定。
    ]  # 新增代码+ComputerUseMcpV2：工具列表结束；如果没有这行代码，Python 列表语法不完整。
    return deepcopy(tools)  # 新增代码+ComputerUseMcpV2：返回副本避免全局污染；如果没有这行代码，调用方可能修改全局工具面。
# 新增代码+ComputerUseMcpV2：函数段结束，computer_use_mcp_tools 到此结束；如果没有这个边界说明，用户不容易看出工具面来源。


def assert_no_shell_surface(tools: list[dict[str, Any]] | None = None) -> bool:  # 新增代码+ComputerUseMcpV2：函数段开始，检查 v2 工具面没有命令执行入口；如果没有这段函数，自检无法阻断 shell 回归。
    names = {str(tool.get("name", "")).lower() for tool in (tools if tools is not None else computer_use_mcp_tools())}  # 新增代码+ComputerUseMcpV2：提取工具名集合；如果没有这行代码，检查只能粗糙扫全文。
    return not bool(names.intersection(SHELL_FORBIDDEN_TOOL_NAMES))  # 新增代码+ComputerUseMcpV2：确认没有命令类工具名；如果没有这行代码，bash 类工具可能混入。
# 新增代码+ComputerUseMcpV2：函数段结束，assert_no_shell_surface 到此结束；如果没有这个边界说明，用户不容易看出安全自检范围。
