"""独立 Computer Use MCP 工具 schema。"""  # 新增代码+ComputerUseMCP：说明本文件只定义 MCP 工具清单；如果没有这行代码，读者很难区分 schema 和真实执行逻辑。
from __future__ import annotations  # 新增代码+ComputerUseMCP：延迟类型解析以兼容较老运行方式；如果没有这行代码，复杂类型注解可能在导入时提前求值出错。

from copy import deepcopy  # 新增代码+ComputerUseMCP：导入深拷贝工具保护全局 schema；如果没有这行代码，调用方可能污染全局工具定义。
from typing import Any  # 新增代码+ComputerUseMCP：导入通用 JSON 类型标注；如果没有这行代码，schema helper 的输入输出边界不清楚。

COMPUTER_USE_MCP_SERVER_NAME = "computer-use"  # 新增代码+ComputerUseMCP：固定 ClaudeCode 风格 server 名；如果没有这行代码，工具名前缀无法稳定为 mcp__computer-use__。
COMPUTER_USE_MCP_READY_MARKER = "COMPUTER_USE_INDEPENDENT_MCP_SERVER_READY"  # 新增代码+ComputerUseMCP：固定 selftest 标记；如果没有这行代码，验收脚本无法稳定判断 server 已可用。
COMPUTER_USE_MCP_TOOL_NAMES = (  # 新增代码+ComputerUseMCP：集中列出 MCP 暴露给模型的桌面原子工具；如果没有这行代码，测试无法检查工具面边界。
    "request_access",  # 新增代码+ComputerUseMCP：申请桌面控制授权；如果没有这行代码，模型无法先请求用户授权再动作。
    "list_granted_applications",  # 新增代码+ComputerUseMCP：查看已授权应用；如果没有这行代码，模型无法在动作前确认授权范围。
    "screenshot",  # 新增代码+ComputerUseMCP：获取屏幕观察；如果没有这行代码，模型会缺少观察-计划-动作-验证里的观察入口。
    "observe",  # 新增代码+ClaudeCodeToolSurface：提供 ClaudeCode 风格观察别名；如果没有这行代码，模型无法用 observe 作为截图/状态观察入口。
    "cursor_position",  # 新增代码+ClaudeCodeToolSurface：提供读取当前鼠标位置的只读工具；如果没有这行代码，模型无法在移动或拖拽前确认光标状态。
    "open_application",  # 新增代码+ComputerUseMCP：打开本地应用；如果没有这行代码，模型无法从 MCP 路线启动 Chrome、记事本等软件。
    "mouse_move",  # 新增代码+ComputerUseMCP：移动鼠标；如果没有这行代码，鼠标动作只能走旧兼容工具。
    "left_click",  # 新增代码+ClaudeCodeToolSurface：提供明确左键单击工具名；如果没有这行代码，模型会继续在 click 和 left_click 之间混用。
    "click",  # 新增代码+ComputerUseMCP：左键点击；如果没有这行代码，网页和桌面按钮无法通过 MCP 原子工具点击。
    "double_click",  # 新增代码+ComputerUseMCP：双击目标；如果没有这行代码，打开文件和桌面图标会缺少常用动作。
    "right_click",  # 新增代码+ComputerUseMCP：右键目标；如果没有这行代码，桌面上下文菜单类任务无法表达。
    "type",  # 新增代码+ComputerUseMCP：输入文本；如果没有这行代码，模型无法通过 MCP 写入网页输入框或文本文件。
    "key",  # 新增代码+ComputerUseMCP：按下按键组合；如果没有这行代码，Enter、Ctrl+L、Alt+Tab 等操作无法表达。
    "scroll",  # 新增代码+ComputerUseMCP：滚动页面或窗口；如果没有这行代码，长页面任务缺少移动视口能力。
    "zoom",  # 新增代码+ClaudeCodeToolSurface：提供局部放大/截图观察工具；如果没有这行代码，模型无法用标准桌面工具请求更细区域。
    "hold_key",  # 新增代码+ClaudeCodeToolSurface：提供按住按键语义入口；如果没有这行代码，快捷键和拖拽组合动作缺少表达方式。
    "left_click_drag",  # 新增代码+ClaudeCodeToolSurface：提供左键拖拽工具；如果没有这行代码，绘图、选择文本和拖动文件只能绕到旧 action。
    "wait",  # 新增代码+ComputerUseMCP：等待外部界面变化；如果没有这行代码，模型可能用无意义动作替代等待。
    "read_clipboard",  # 新增代码+ClaudeCodeToolSurface：提供只读剪贴板工具名；如果没有这行代码，模型只能调用混合读写的 clipboard。
    "write_clipboard",  # 新增代码+ClaudeCodeToolSurface：提供写剪贴板工具名；如果没有这行代码，模型无法明确表达复制前的受控写入。
    "clipboard",  # 新增代码+ComputerUseMCP：读写剪贴板的受控入口；如果没有这行代码，复制粘贴任务只能绕到旧工具。
    "middle_click",  # 新增代码+ClaudeCodeToolSurface：预留中键点击工具；如果没有这行代码，后续补齐完整鼠标表面时没有稳定合同。
    "triple_click",  # 新增代码+ClaudeCodeToolSurface：预留三击工具；如果没有这行代码，文本段落选择类动作没有明确扩展名。
    "left_mouse_down",  # 新增代码+ClaudeCodeToolSurface：预留左键按下工具；如果没有这行代码，未来低层拖拽无法表达 down/up 分离。
    "left_mouse_up",  # 新增代码+ClaudeCodeToolSurface：预留左键抬起工具；如果没有这行代码，未来低层拖拽无法表达 down/up 分离。
    "computer_batch",  # 新增代码+ComputerUseMCP：批量执行小步骤；如果没有这行代码，多步桌面动作会产生过多 MCP 往返。
)  # 新增代码+ComputerUseMCP：结束工具名元组；如果没有这行代码，Python 语法不完整。
SHELL_FORBIDDEN_TOOL_NAMES = {"bash", "powershell", "shell", "run_powershell", "start_background_command"}  # 新增代码+ComputerUseMCP：列出不得出现在 Computer Use MCP 的命令类工具名；如果没有这行代码，后续可能把 shell 当桌面工具暴露。
SHELL_FORBIDDEN_ARGUMENT_NAMES = {"command", "shell", "powershell", "bash", "script", "executable"}  # 新增代码+ComputerUseMCP：列出不得进入工具参数的命令类字段；如果没有这行代码，模型可能通过参数绕出桌面语义。


# 新增代码+ComputerUseMCP：函数段开始，_prop 生成单个 JSON Schema 属性；如果没有这段函数，下面每个字段都要重复写 type/description。
def _prop(type_name: str, description: str, **extra: Any) -> dict[str, Any]:  # 新增代码+ComputerUseMCP：声明属性 helper；如果没有这行代码，schema 字段构造会分散且难审计。
    payload = {"type": type_name, "description": description}  # 新增代码+ComputerUseMCP：写入基础类型和说明；如果没有这行代码，模型不知道字段要填什么。
    payload.update(extra)  # 新增代码+ComputerUseMCP：合并枚举、默认值等补充约束；如果没有这行代码，字段无法表达更细规则。
    return payload  # 新增代码+ComputerUseMCP：返回单个属性 schema；如果没有这行代码，调用方拿不到字段定义。
# 新增代码+ComputerUseMCP：函数段结束，_prop 到此结束；如果没有这个边界说明，初学者不容易看出属性 helper 范围。


# 新增代码+ComputerUseMCP：函数段开始，_object_schema 生成对象参数 schema；如果没有这段函数，每个工具都要重复写 type/properties/required。
def _object_schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:  # 新增代码+ComputerUseMCP：声明对象 schema helper；如果没有这行代码，工具参数结构会更难保持一致。
    return {"type": "object", "properties": deepcopy(properties), "required": list(required or []), "additionalProperties": False}  # 新增代码+ComputerUseMCP：返回封闭对象 schema；如果没有这行代码，串味参数可能进入 MCP server。
# 新增代码+ComputerUseMCP：函数段结束，_object_schema 到此结束；如果没有这个边界说明，初学者不容易看出参数封闭规则范围。


# 新增代码+ComputerUseMCP：函数段开始，_tool 生成单个 MCP tools/list 条目；如果没有这段函数，metadata 和 annotations 容易在工具之间不一致。
def _tool(name: str, description: str, input_schema: dict[str, Any], *, read_only: bool = False, always_load: bool = False) -> dict[str, Any]:  # 新增代码+ComputerUseMCP：声明工具条目 helper；如果没有这行代码，工具定义会重复且容易漏字段。
    return {  # 新增代码+ComputerUseMCP：开始返回 MCP 工具条目；如果没有这行代码，tools/list 无法获得标准对象。
        "name": name,  # 新增代码+ComputerUseMCP：写入 MCP 原始工具名；如果没有这行代码，registry 无法生成 mcp__computer-use__ 前缀名。
        "description": description,  # 新增代码+ComputerUseMCP：写入工具说明；如果没有这行代码，模型不知道何时调用该工具。
        "inputSchema": deepcopy(input_schema),  # 新增代码+ComputerUseMCP：写入输入 schema 副本；如果没有这行代码，调用方可能修改全局 schema。
        "annotations": {"readOnlyHint": bool(read_only), "destructiveHint": not bool(read_only), "openWorldHint": False},  # 新增代码+ComputerUseMCP：写入 MCP 风格风险标记；如果没有这行代码，catalog 无法区分观察和动作。
        "_meta": {"anthropic/alwaysLoad": bool(always_load), "anthropic/searchHint": "computer use desktop screen mouse keyboard application controlled visible desktop"},  # 新增代码+ComputerUseMCP：写入发现提示和首轮可见策略；如果没有这行代码，request_access 等入口不容易被发现。
    }  # 新增代码+ComputerUseMCP：结束 MCP 工具条目；如果没有这行代码，Python 字典语法不完整。
# 新增代码+ComputerUseMCP：函数段结束，_tool 到此结束；如果没有这个边界说明，初学者不容易看出工具条目构造范围。


REQUEST_ACCESS_SCHEMA = _object_schema({  # 新增代码+ComputerUseMCP：定义 request_access 参数 schema；如果没有这行代码，模型无法申请控制哪些应用。
    "applications": _prop("array", "需要控制的本地应用名称列表，例如 Google Chrome。", items={"type": "string"}),  # 新增代码+ComputerUseMCP：声明应用列表字段；如果没有这行代码，授权申请缺少目标范围。
    "reason": _prop("string", "用一句话说明为什么需要控制这些应用。"),  # 新增代码+ComputerUseMCP：声明申请原因字段；如果没有这行代码，用户看不到授权目的。
    "duration_seconds": _prop("integer", "本次授权希望持续多少秒。", default=600, minimum=1, maximum=7200),  # 新增代码+ComputerUseMCP：声明授权时长字段；如果没有这行代码，授权缺少过期边界。
    "allow_mouse": _prop("boolean", "是否需要鼠标动作。", default=True),  # 新增代码+ComputerUseMCP：声明鼠标权限位；如果没有这行代码，授权无法细分鼠标风险。
    "allow_keyboard": _prop("boolean", "是否需要键盘输入。", default=True),  # 新增代码+ComputerUseMCP：声明键盘权限位；如果没有这行代码，授权无法细分键盘风险。
    "allow_clipboard": _prop("boolean", "是否需要剪贴板读写。", default=False),  # 新增代码+ComputerUseMCP：声明剪贴板权限位；如果没有这行代码，复制粘贴风险无法单独说明。
}, ["applications", "reason"])  # 新增代码+ComputerUseMCP：设置必填字段；如果没有这行代码，空申请也可能被模型发出。
LIST_GRANTED_APPLICATIONS_SCHEMA = _object_schema({})  # 新增代码+ComputerUseMCP：定义无参数授权查询 schema；如果没有这行代码，list_granted_applications 缺少标准输入结构。
SCREENSHOT_SCHEMA = _object_schema({"reason": _prop("string", "说明截图用于哪一步观察。", default="observe desktop")})  # 新增代码+ComputerUseMCP：定义截图参数 schema；如果没有这行代码，截图缺少审计理由。
OBSERVE_SCHEMA = SCREENSHOT_SCHEMA  # 新增代码+ClaudeCodeToolSurface：observe 复用 screenshot 的只读观察参数；如果没有这行代码，observe 和 screenshot 的入参会无谓分裂。
CURSOR_POSITION_SCHEMA = _object_schema({"reason": _prop("string", "说明为什么需要读取当前鼠标位置。", default="read cursor position")})  # 新增代码+ClaudeCodeToolSurface：定义光标位置读取 schema；如果没有这行代码，cursor_position 缺少可审计理由。
OPEN_APPLICATION_SCHEMA = _object_schema({  # 新增代码+ComputerUseMCP：定义打开应用参数 schema；如果没有这行代码，模型无法声明要打开哪个本地应用。
    "app_name": _prop("string", "要打开的应用名称，例如 Google Chrome、记事本、网易云音乐。"),  # 新增代码+ComputerUseMCP：声明应用名字段；如果没有这行代码，启动动作没有目标。
    "reason": _prop("string", "说明打开该应用的任务目的。", default="open requested application"),  # 新增代码+ComputerUseMCP：声明启动原因字段；如果没有这行代码，审计无法解释为什么打开应用。
}, ["app_name"])  # 新增代码+ComputerUseMCP：设置 app_name 必填；如果没有这行代码，空启动请求可能进入 controller。
POINT_SCHEMA = {"x": _prop("integer", "屏幕坐标 x。"), "y": _prop("integer", "屏幕坐标 y。")}  # 新增代码+ComputerUseMCP：定义坐标字段片段；如果没有这行代码，鼠标类工具会重复写 x/y。
MOUSE_MOVE_SCHEMA = _object_schema({**POINT_SCHEMA, "reason": _prop("string", "说明移动鼠标的目的。", default="move pointer")}, ["x", "y"])  # 新增代码+ComputerUseMCP：定义鼠标移动 schema；如果没有这行代码，mouse_move 无法校验坐标。
CLICK_SCHEMA = _object_schema({**POINT_SCHEMA, "button": _prop("string", "鼠标按键。", enum=["left", "middle"], default="left"), "reason": _prop("string", "说明点击目的。", default="click target")}, ["x", "y"])  # 新增代码+ComputerUseMCP：定义点击 schema；如果没有这行代码，click 无法约束按键和坐标。
LEFT_CLICK_SCHEMA = _object_schema({**POINT_SCHEMA, "reason": _prop("string", "说明左键点击目的。", default="left click target")}, ["x", "y"])  # 新增代码+ClaudeCodeToolSurface：定义明确左键单击 schema；如果没有这行代码，left_click 无法和兼容 click 分开约束。
MIDDLE_CLICK_SCHEMA = _object_schema({**POINT_SCHEMA, "reason": _prop("string", "说明中键点击目的。", default="middle click target")}, ["x", "y"])  # 新增代码+ClaudeCodeToolSurface：定义中键点击 schema；如果没有这行代码，预留 middle_click 没有稳定入参合同。
DOUBLE_CLICK_SCHEMA = _object_schema({**POINT_SCHEMA, "reason": _prop("string", "说明双击目的。", default="double click target")}, ["x", "y"])  # 新增代码+ComputerUseMCP：定义双击 schema；如果没有这行代码，double_click 无法校验坐标。
TRIPLE_CLICK_SCHEMA = _object_schema({**POINT_SCHEMA, "reason": _prop("string", "说明三击目的。", default="triple click target")}, ["x", "y"])  # 新增代码+ClaudeCodeToolSurface：定义三击 schema；如果没有这行代码，triple_click 预留工具没有参数边界。
RIGHT_CLICK_SCHEMA = _object_schema({**POINT_SCHEMA, "reason": _prop("string", "说明右键目的。", default="open context menu")}, ["x", "y"])  # 新增代码+ComputerUseMCP：定义右键 schema；如果没有这行代码，right_click 无法校验坐标。
TYPE_SCHEMA = _object_schema({"text": _prop("string", "要输入到当前焦点位置的文本。"), "reason": _prop("string", "说明输入目的。", default="type text")}, ["text"])  # 新增代码+ComputerUseMCP：定义输入文本 schema；如果没有这行代码，type 无法要求文本必填。
KEY_SCHEMA = _object_schema({"keys": _prop("array", "要按下的按键序列，例如 Ctrl、L、Enter。", items={"type": "string"}), "reason": _prop("string", "说明按键目的。", default="press key")}, ["keys"])  # 新增代码+ComputerUseMCP：定义按键 schema；如果没有这行代码，key 无法表达组合键。
HOLD_KEY_SCHEMA = _object_schema({"keys": _prop("array", "要按住的按键序列，例如 Shift。", items={"type": "string"}), "duration_seconds": _prop("number", "按住持续秒数，server 会限制最大值。", default=1, minimum=0, maximum=10), "reason": _prop("string", "说明按住按键目的。", default="hold key")}, ["keys"])  # 新增代码+ClaudeCodeToolSurface：定义按住按键 schema；如果没有这行代码，hold_key 无法表达时长和按键。
SCROLL_SCHEMA = _object_schema({**POINT_SCHEMA, "delta_y": _prop("integer", "垂直滚动量，负数向下，正数向上。", default=-500), "reason": _prop("string", "说明滚动目的。", default="scroll viewport")}, ["x", "y", "delta_y"])  # 新增代码+ComputerUseMCP：定义滚动 schema；如果没有这行代码，scroll 无法校验位置和方向。
ZOOM_SCHEMA = _object_schema({"x": _prop("integer", "需要放大观察区域的左上角 x。"), "y": _prop("integer", "需要放大观察区域的左上角 y。"), "width": _prop("integer", "需要放大观察区域宽度。", default=400, minimum=1), "height": _prop("integer", "需要放大观察区域高度。", default=300, minimum=1), "reason": _prop("string", "说明放大观察目的。", default="zoom region")}, ["x", "y"])  # 新增代码+ClaudeCodeToolSurface：定义局部放大观察 schema；如果没有这行代码，zoom 无法表达区域边界。
LEFT_CLICK_DRAG_SCHEMA = _object_schema({"start_x": _prop("integer", "拖拽起点屏幕坐标 x。"), "start_y": _prop("integer", "拖拽起点屏幕坐标 y。"), "end_x": _prop("integer", "拖拽终点屏幕坐标 x。"), "end_y": _prop("integer", "拖拽终点屏幕坐标 y。"), "duration_seconds": _prop("number", "拖拽持续秒数。", default=0.5, minimum=0, maximum=10), "reason": _prop("string", "说明拖拽目的。", default="drag with left mouse button")}, ["start_x", "start_y", "end_x", "end_y"])  # 新增代码+ClaudeCodeToolSurface：定义左键拖拽 schema；如果没有这行代码，left_click_drag 无法校验起点终点。
LEFT_MOUSE_DOWN_SCHEMA = _object_schema({**POINT_SCHEMA, "reason": _prop("string", "说明左键按下目的。", default="left mouse down")}, ["x", "y"])  # 新增代码+ClaudeCodeToolSurface：定义左键按下预留 schema；如果没有这行代码，left_mouse_down 没有参数合同。
LEFT_MOUSE_UP_SCHEMA = _object_schema({**POINT_SCHEMA, "reason": _prop("string", "说明左键抬起目的。", default="left mouse up")}, ["x", "y"])  # 新增代码+ClaudeCodeToolSurface：定义左键抬起预留 schema；如果没有这行代码，left_mouse_up 没有参数合同。
WAIT_SCHEMA = _object_schema({"seconds": _prop("number", "等待秒数，server 会限制最大值。", default=1, minimum=0, maximum=30), "reason": _prop("string", "说明等待什么界面变化。", default="wait for UI")})  # 新增代码+ComputerUseMCP：定义等待 schema；如果没有这行代码，wait 缺少可审计理由和时长。
READ_CLIPBOARD_SCHEMA = _object_schema({"reason": _prop("string", "说明读取剪贴板的目的。", default="read clipboard")})  # 新增代码+ClaudeCodeToolSurface：定义只读剪贴板 schema；如果没有这行代码，read_clipboard 缺少明确入参合同。
WRITE_CLIPBOARD_SCHEMA = _object_schema({"text": _prop("string", "要写入剪贴板的文本。"), "reason": _prop("string", "说明写入剪贴板的目的。", default="write clipboard")}, ["text"])  # 新增代码+ClaudeCodeToolSurface：定义写剪贴板 schema；如果没有这行代码，write_clipboard 无法要求 text 必填。
CLIPBOARD_SCHEMA = _object_schema({"operation": _prop("string", "剪贴板操作类型。", enum=["read", "write"]), "text": _prop("string", "写入剪贴板时使用的文本。", default=""), "reason": _prop("string", "说明剪贴板用途。", default="clipboard operation")}, ["operation"])  # 新增代码+ComputerUseMCP：定义剪贴板 schema；如果没有这行代码，clipboard 无法区分读写。
BATCH_SCHEMA = _object_schema({"steps": _prop("array", "要顺序执行的 Computer Use MCP 步骤。", items={"type": "object"}), "stop_on_error": _prop("boolean", "某一步失败时是否停止后续步骤。", default=True)}, ["steps"])  # 新增代码+ComputerUseMCP：定义批量步骤 schema；如果没有这行代码，computer_batch 无法表达多步动作。

COMPUTER_USE_MCP_TOOLS = [  # 新增代码+ComputerUseMCP：生成最终 tools/list 列表；如果没有这行代码，server 启动后没有可暴露工具。
    _tool("request_access", "申请受控桌面应用访问权限，不直接执行动作。", REQUEST_ACCESS_SCHEMA, read_only=True, always_load=True),  # 新增代码+ComputerUseMCP：暴露授权申请入口；如果没有这行代码，模型无法先申请再操作。
    _tool("list_granted_applications", "查看当前 Computer Use 会话中已授权的应用范围。", LIST_GRANTED_APPLICATIONS_SCHEMA, read_only=True, always_load=True),  # 新增代码+ComputerUseMCP：暴露授权查询入口；如果没有这行代码，模型无法确认授权边界。
    _tool("screenshot", "观察当前桌面截图或截图状态。", SCREENSHOT_SCHEMA, read_only=True, always_load=True),  # 修改代码+ClaudeCodeToolSurface：截图是 Computer Use 核心观察入口并默认加载；如果没有这行代码，模型进入桌面模式后可能先盲点。
    _tool("observe", "观察当前桌面状态，等价于截图观察入口。", OBSERVE_SCHEMA, read_only=True, always_load=True),  # 新增代码+ClaudeCodeToolSurface：暴露 ClaudeCode 风格 observe 工具；如果没有这行代码，模型无法用标准观察名读取桌面。
    _tool("cursor_position", "读取当前鼠标光标位置，不移动鼠标。", CURSOR_POSITION_SCHEMA, read_only=True, always_load=True),  # 新增代码+ClaudeCodeToolSurface：暴露光标位置入口；如果没有这行代码，模型无法确认鼠标当前坐标。
    _tool("open_application", "打开一个本地桌面应用并建立目标上下文。", OPEN_APPLICATION_SCHEMA),  # 新增代码+ComputerUseMCP：暴露打开应用入口；如果没有这行代码，无法走 MCP 打开 Chrome 等软件。
    _tool("mouse_move", "移动鼠标到指定屏幕坐标。", MOUSE_MOVE_SCHEMA),  # 新增代码+ComputerUseMCP：暴露鼠标移动入口；如果没有这行代码，鼠标路径无法表达。
    _tool("left_click", "在指定屏幕坐标执行左键单击。", LEFT_CLICK_SCHEMA),  # 新增代码+ClaudeCodeToolSurface：暴露明确左键单击入口；如果没有这行代码，模型会继续混用 click。
    _tool("click", "兼容旧版点击入口；新工具面默认隐藏，请优先使用 left_click。", CLICK_SCHEMA),  # 修改代码+ClaudeCodeToolSurface：保留旧 click 兼容但不作为新表面首选；如果没有这行代码，旧测试和旧调用会断开。
    _tool("double_click", "在指定屏幕坐标执行双击。", DOUBLE_CLICK_SCHEMA),  # 新增代码+ComputerUseMCP：暴露双击入口；如果没有这行代码，文件和桌面图标操作受限。
    _tool("right_click", "在指定屏幕坐标执行右键。", RIGHT_CLICK_SCHEMA),  # 新增代码+ComputerUseMCP：暴露右键入口；如果没有这行代码，上下文菜单操作受限。
    _tool("type", "向当前焦点输入文本。", TYPE_SCHEMA),  # 新增代码+ComputerUseMCP：暴露文本输入入口；如果没有这行代码，网页或文本编辑无法写入内容。
    _tool("key", "按下单个按键或组合键。", KEY_SCHEMA),  # 新增代码+ComputerUseMCP：暴露按键入口；如果没有这行代码，回车、快捷键等无法表达。
    _tool("scroll", "在指定坐标附近滚动页面或窗口。", SCROLL_SCHEMA),  # 新增代码+ComputerUseMCP：暴露滚动入口；如果没有这行代码，长页面任务受限。
    _tool("zoom", "对指定区域执行更细粒度观察。", ZOOM_SCHEMA, read_only=True),  # 新增代码+ClaudeCodeToolSurface：暴露局部放大观察入口；如果没有这行代码，模型无法请求看清小区域。
    _tool("hold_key", "按住一个或多个按键一小段时间。", HOLD_KEY_SCHEMA),  # 新增代码+ClaudeCodeToolSurface：暴露按住按键入口；如果没有这行代码，组合操作缺少标准表达。
    _tool("left_click_drag", "按住左键从起点拖拽到终点。", LEFT_CLICK_DRAG_SCHEMA),  # 新增代码+ClaudeCodeToolSurface：暴露左键拖拽入口；如果没有这行代码，绘图和拖放任务只能绕旧 action。
    _tool("wait", "等待界面变化，避免用无意义点击代替等待。", WAIT_SCHEMA, read_only=True),  # 新增代码+ComputerUseMCP：暴露等待入口；如果没有这行代码，模型缺少显式等待动作。
    _tool("read_clipboard", "读取受控剪贴板内容。", READ_CLIPBOARD_SCHEMA, read_only=True),  # 新增代码+ClaudeCodeToolSurface：暴露只读剪贴板入口；如果没有这行代码，模型无法明确表达只读复制检查。
    _tool("write_clipboard", "写入受控剪贴板内容。", WRITE_CLIPBOARD_SCHEMA),  # 新增代码+ClaudeCodeToolSurface：暴露写剪贴板入口；如果没有这行代码，复制粘贴任务缺少清晰写入口。
    _tool("clipboard", "兼容旧版混合剪贴板入口；新工具面默认隐藏，请优先使用 read_clipboard/write_clipboard。", CLIPBOARD_SCHEMA),  # 修改代码+ClaudeCodeToolSurface：保留旧 clipboard 兼容但不作为新表面首选；如果没有这行代码，旧调用会断开。
    _tool("middle_click", "预留中键点击入口；当前后端若不支持会明确返回 unsupported。", MIDDLE_CLICK_SCHEMA),  # 新增代码+ClaudeCodeToolSurface：暴露预留中键工具合同；如果没有这行代码，后续补齐中键没有稳定名称。
    _tool("triple_click", "预留三击入口；当前后端若不支持会明确返回 unsupported。", TRIPLE_CLICK_SCHEMA),  # 新增代码+ClaudeCodeToolSurface：暴露预留三击工具合同；如果没有这行代码，文本选择扩展没有稳定名称。
    _tool("left_mouse_down", "预留左键按下入口；当前后端若不支持会明确返回 unsupported。", LEFT_MOUSE_DOWN_SCHEMA),  # 新增代码+ClaudeCodeToolSurface：暴露预留下压工具合同；如果没有这行代码，未来低层拖拽扩展没有稳定名称。
    _tool("left_mouse_up", "预留左键抬起入口；当前后端若不支持会明确返回 unsupported。", LEFT_MOUSE_UP_SCHEMA),  # 新增代码+ClaudeCodeToolSurface：暴露预留抬起工具合同；如果没有这行代码，未来低层拖拽扩展没有稳定名称。
    _tool("computer_batch", "按顺序执行多个 Computer Use MCP 步骤。", BATCH_SCHEMA),  # 新增代码+ComputerUseMCP：暴露批量入口；如果没有这行代码，多步动作需要大量往返。
]  # 新增代码+ComputerUseMCP：结束工具列表；如果没有这行代码，Python 语法不完整。


# 新增代码+ComputerUseMCP：函数段开始，computer_use_mcp_tools 返回工具清单副本；如果没有这段函数，server 和测试会共享可变全局对象。
def computer_use_mcp_tools() -> list[dict[str, Any]]:  # 新增代码+ComputerUseMCP：声明公开工具清单读取入口；如果没有这行代码，调用方只能直接拿全局变量。
    return deepcopy(COMPUTER_USE_MCP_TOOLS)  # 新增代码+ComputerUseMCP：返回深拷贝保护全局 schema；如果没有这行代码，测试或 registry 可能污染工具定义。
# 新增代码+ComputerUseMCP：函数段结束，computer_use_mcp_tools 到此结束；如果没有这个边界说明，初学者不容易看出清单读取范围。


# 新增代码+ComputerUseMCP：函数段开始，assert_no_shell_surface 检查 schema 没有命令执行入口；如果没有这段函数，bash/powershell 回归只能靠人工看。
def assert_no_shell_surface(tools: list[dict[str, Any]] | None = None) -> bool:  # 新增代码+ComputerUseMCP：声明 schema 安全自检入口；如果没有这行代码，selftest 无法复用边界检查。
    payload = tools if tools is not None else COMPUTER_USE_MCP_TOOLS  # 新增代码+ComputerUseMCP：允许调用方传入自定义工具列表；如果没有这行代码，测试 fake 清单无法复用。
    text = str(payload).lower()  # 新增代码+ComputerUseMCP：把工具清单转成小写文本便于全局扫描；如果没有这行代码，大小写变化可能漏检。
    return not any(name in text for name in SHELL_FORBIDDEN_TOOL_NAMES) and not any(f"'{name}'" in text or f'"{name}"' in text for name in SHELL_FORBIDDEN_ARGUMENT_NAMES)  # 新增代码+ComputerUseMCP：确认无 shell 工具名和命令字段；如果没有这行代码，schema 可能重新暴露命令入口。
# 新增代码+ComputerUseMCP：函数段结束，assert_no_shell_surface 到此结束；如果没有这个边界说明，初学者不容易看出安全自检范围。

# 修改代码+ComputerUseMcpV2：兼容覆盖层开始，旧 schema 文件保留路径但公开事实源切到 v2；如果没有这一段，旧文件会继续暴露 click/clipboard/zoom/hold_key/left_click_drag 等非蓝图工具。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import COMPUTER_USE_MCP_READY_MARKER as _V2_COMPUTER_USE_MCP_READY_MARKER  # 修改代码+ComputerUseMcpV2：导入 v2 ready marker；如果没有这一行，旧 selftest 可能继续报告旧 marker。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import COMPUTER_USE_MCP_SERVER_NAME as _V2_COMPUTER_USE_MCP_SERVER_NAME  # 修改代码+ComputerUseMcpV2：导入 v2 server 名；如果没有这一行，旧文件和 v2 文件可能出现 server 名漂移。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import COMPUTER_USE_MCP_TOOL_NAMES as _V2_COMPUTER_USE_MCP_TOOL_NAMES  # 修改代码+ComputerUseMcpV2：导入 v2 精确工具名元组；如果没有这一行，旧文件仍会使用包含旧接口的长名单。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import assert_no_shell_surface as _v2_assert_no_shell_surface  # 修改代码+ComputerUseMcpV2：导入 v2 shell 面检查；如果没有这一行，安全自检会检查旧清单而不是真实 v2 清单。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import computer_use_mcp_tools as _v2_computer_use_mcp_tools  # 修改代码+ComputerUseMcpV2：导入 v2 tools/list 生成函数；如果没有这一行，旧引用拿不到 v2 schema。

COMPUTER_USE_MCP_READY_MARKER = _V2_COMPUTER_USE_MCP_READY_MARKER  # 修改代码+ComputerUseMcpV2：把旧公开 marker 覆盖成 v2 marker；如果没有这一行，验收会看到旧 server 身份。
COMPUTER_USE_MCP_SERVER_NAME = _V2_COMPUTER_USE_MCP_SERVER_NAME  # 修改代码+ComputerUseMcpV2：把旧公开 server 名覆盖成 v2 server 名；如果没有这一行，registry 命名前缀可能与 v2 不一致。
COMPUTER_USE_MCP_TOOL_NAMES = _V2_COMPUTER_USE_MCP_TOOL_NAMES  # 修改代码+ComputerUseMcpV2：把旧公开工具名覆盖成蓝图 17 个工具；如果没有这一行，工具池测试会继续把旧工具当成合法。
COMPUTER_USE_MCP_TOOLS = _v2_computer_use_mcp_tools()  # 修改代码+ComputerUseMcpV2：把旧全局工具清单覆盖为 v2 清单副本；如果没有这一行，直接读取全局变量的旧代码仍会泄露旧工具。


# 修改代码+ComputerUseMcpV2：函数段开始，computer_use_mcp_tools 作为旧路径兼容函数返回 v2 清单；如果没有这段函数，导入旧函数的 registry 会继续拿到旧工具面。
def computer_use_mcp_tools() -> list[dict[str, Any]]:  # 修改代码+ComputerUseMcpV2：声明旧路径工具清单入口；如果没有这一行，调用方只能直接依赖 v2 内部包路径。
    return _v2_computer_use_mcp_tools()  # 修改代码+ComputerUseMcpV2：返回 v2 工具清单副本；如果没有这一行，旧函数不会真正切到 v2。
# 修改代码+ComputerUseMcpV2：函数段结束，computer_use_mcp_tools 到此结束；如果没有这个边界说明，用户不容易看出这是兼容转发。


# 修改代码+ComputerUseMcpV2：函数段开始，assert_no_shell_surface 作为旧路径兼容函数使用 v2 检查；如果没有这段函数，selftest 的安全判断会与 v2 工具面不一致。
def assert_no_shell_surface(tools: list[dict[str, Any]] | None = None) -> bool:  # 修改代码+ComputerUseMcpV2：声明旧路径安全自检入口；如果没有这一行，调用方需要改大量 import。
    return _v2_assert_no_shell_surface(tools)  # 修改代码+ComputerUseMcpV2：委托 v2 安全检查；如果没有这一行，旧检查可能漏掉 v2 新字段。
# 修改代码+ComputerUseMcpV2：函数段结束，assert_no_shell_surface 到此结束；如果没有这个边界说明，用户不容易看出 shell 检查已经统一。
# 修改代码+ComputerUseMcpV2：兼容覆盖层结束，旧 schema 文件到此只负责转发 v2；如果没有这一行说明，后续维护者可能又在旧清单里添加工具。
