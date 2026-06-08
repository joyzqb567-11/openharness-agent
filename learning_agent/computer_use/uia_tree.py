"""Windows Computer Use UIA control tree runtime."""  # 新增代码+Phase46WindowsUiaTree: 说明本文件负责结构化 UIA 控件树观察；如果没有这个文件，Phase46 只能继续返回纯文本摘要。
from __future__ import annotations  # 新增代码+Phase46WindowsUiaTree: 启用延迟类型解析；如果没有这行代码，旧运行路径遇到前向类型标注更容易导入失败。

import importlib.util  # 新增代码+Phase46WindowsUiaTree: 导入依赖探测工具；如果没有这行代码，status 无法诚实报告 uiautomation 是否存在。
import json  # 新增代码+Phase46WindowsUiaTree: 导入 JSON 用于自检时检查敏感文本是否泄露；如果没有这行代码，redacted=true 没有证据。
import sys  # 新增代码+Phase46WindowsUiaTree: 导入 sys 用于读取当前平台；如果没有这行代码，非 Windows 安全拒绝无法稳定判断。
from typing import Any  # 新增代码+Phase46WindowsUiaTree: 导入 Any 标注 UIA 对象和 JSON 风格结果；如果没有这行代码，接口边界不清楚。

try:  # 新增代码+Phase46WindowsUiaTree: 优先按包模式导入 evidence 过滤和 hwnd 解析；如果没有这行代码，unittest 和生产入口无法复用现有安全逻辑。
    from learning_agent.computer_use.evidence import SENSITIVE_ACCESSIBILITY_KEYWORDS, filter_accessibility_text  # 新增代码+Phase46WindowsUiaTree: 复用 Phase29 敏感文本过滤；如果没有这行代码，UIA 控件名称可能泄露密码或 token。
    from learning_agent.computer_use.native_helper import parse_hwnd_from_window  # 新增代码+Phase46WindowsUiaTree: 复用 Phase32 hwnd 解析；如果没有这行代码，runtime 会和窗口合同割裂。
except ModuleNotFoundError as error:  # 新增代码+Phase46WindowsUiaTree: 兼容 start_oauth_agent.bat 的脚本模式；如果没有这行代码，真实终端从 learning_agent 目录运行时可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.evidence", "learning_agent.computer_use.native_helper"}:  # 新增代码+Phase46WindowsUiaTree: 只允许目标包路径缺失时 fallback；如果没有这行代码，真实内部 bug 会被误吞。
        raise  # 新增代码+Phase46WindowsUiaTree: 重新抛出非路径类导入错误；如果没有这行代码，排查 evidence/native_helper 内部错误会困难。
    from computer_use.evidence import SENSITIVE_ACCESSIBILITY_KEYWORDS, filter_accessibility_text  # 新增代码+Phase46WindowsUiaTree: 脚本模式复用敏感文本过滤；如果没有这行代码，bat 入口无法安全脱敏。
    from computer_use.native_helper import parse_hwnd_from_window  # 新增代码+Phase46WindowsUiaTree: 脚本模式复用 hwnd 解析；如果没有这行代码，bat 入口无法识别目标窗口。

PHASE46_WINDOWS_UIA_TREE_MARKER = "PHASE46_WINDOWS_UIA_TREE_READY"  # 新增代码+Phase46WindowsUiaTree: 定义 Phase46 ready marker；如果没有这行代码，真实终端验收没有稳定等待锚点。
PHASE46_WINDOWS_UIA_TREE_OK_TOKEN = "PHASE46_WINDOWS_UIA_TREE_OK"  # 新增代码+Phase46WindowsUiaTree: 定义 Phase46 OK token；如果没有这行代码，日志无法区分运行完成和验收通过。
PHASE46_UIA_TREE_MODEL = "phase46_windows_uia_control_tree"  # 新增代码+Phase46WindowsUiaTree: 定义结构化控件树模型名；如果没有这行代码，后续状态和 evidence 难以区分版本。
PHASE46_ACTIONS_EXPANDED = False  # 新增代码+Phase46WindowsUiaTree: 明确 Phase46 只读观察不扩大动作面；如果没有这行代码，安全审计无法确认边界。


def _phase46_bool_token(value: Any) -> str:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，把布尔值转成验收友好的小写 token；如果没有这段函数，CLI token 大小写容易漂移。
    return str(bool(value)).lower()  # 新增代码+Phase46WindowsUiaTree: 返回 true/false；如果没有这行代码，场景断言可能因为 True/False 失败。
# 新增代码+Phase46WindowsUiaTree: 函数段结束，_phase46_bool_token 到此结束；如果没有这个边界说明，读者不容易看出 token 格式范围。


def _safe_int(value: Any) -> int:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，把 UIA 坐标值安全转成 int；如果没有这段函数，float/字符串坐标可能让 bounds 解析崩溃。
    try:  # 新增代码+Phase46WindowsUiaTree: 捕获无法转换的坐标；如果没有这行代码，坏 UIA 对象会中断整棵树。
        return int(value or 0)  # 新增代码+Phase46WindowsUiaTree: 返回整数坐标；如果没有这行代码，bounds 字段无法稳定比较。
    except Exception:  # 新增代码+Phase46WindowsUiaTree: 捕获所有转换异常；如果没有这行代码，动态 UIA 值可能抛错。
        return 0  # 新增代码+Phase46WindowsUiaTree: 坏坐标统一兜底为 0；如果没有这行代码，调用方需要到处兜底。
# 新增代码+Phase46WindowsUiaTree: 函数段结束，_safe_int 到此结束；如果没有这个边界说明，读者不容易看出坐标转换范围。


def _safe_bool(value: Any, default: bool = True) -> bool:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，把 UIA 启用状态安全转成 bool；如果没有这段函数，控件 enabled 字段可能不稳定。
    if value is None:  # 新增代码+Phase46WindowsUiaTree: 检查空值；如果没有这行代码，缺失 enabled 可能被误判为 False。
        return bool(default)  # 新增代码+Phase46WindowsUiaTree: 空值使用默认值；如果没有这行代码，未知状态会错误阻止点击/输入提示。
    if isinstance(value, str):  # 新增代码+Phase46WindowsUiaTree: 处理字符串布尔值；如果没有这行代码，"false" 会被 Python 当作 True。
        return value.strip().lower() not in {"0", "false", "no", "off"}  # 新增代码+Phase46WindowsUiaTree: 识别常见 false 字符串；如果没有这行代码，禁用控件可能被误报可用。
    return bool(value)  # 新增代码+Phase46WindowsUiaTree: 返回普通布尔转换；如果没有这行代码，调用方拿不到 enabled 结果。
# 新增代码+Phase46WindowsUiaTree: 函数段结束，_safe_bool 到此结束；如果没有这个边界说明，读者不容易看出布尔转换范围。


class WindowsUiaControlTreeRuntime:  # 新增代码+Phase46WindowsUiaTree: 类段开始，定义结构化 UIA 控件树运行时；如果没有这个类，Computer Use 无法返回控件节点、边界和可操作摘要。
    def __init__(self, platform: str | None = None, uia_module: Any | None = None, max_depth: int = 5, max_nodes: int = 120, max_text_length: int = 120) -> None:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，初始化平台、依赖和输出上限；如果没有这段函数，测试无法注入 fake UIA 模块和限制大窗口。
        self.platform = platform or sys.platform  # 新增代码+Phase46WindowsUiaTree: 保存平台名称；如果没有这行代码，非 Windows 拒绝路径无法稳定测试。
        self.uia_module = uia_module  # 新增代码+Phase46WindowsUiaTree: 保存可选注入模块；如果没有这行代码，自检和单测会依赖真实桌面依赖。
        self.max_depth = max(0, int(max_depth))  # 新增代码+Phase46WindowsUiaTree: 保存最大遍历深度并防止负数；如果没有这行代码，复杂控件树可能递归过深。
        self.max_nodes = max(1, int(max_nodes))  # 新增代码+Phase46WindowsUiaTree: 保存最大节点数并至少读取一个节点；如果没有这行代码，大窗口可能输出过多节点。
        self.max_text_length = max(1, int(max_text_length))  # 新增代码+Phase46WindowsUiaTree: 保存单个文本字段最大长度；如果没有这行代码，长控件名可能刷屏或泄露过多内容。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，返回 UIA 树运行时状态；如果没有这段函数，/computer 和 host 无法展示控件树能力。
        dependency_available = self.uia_module is not None or importlib.util.find_spec("uiautomation") is not None  # 新增代码+Phase46WindowsUiaTree: 探测注入模块或真实依赖；如果没有这行代码，状态无法解释为何不可用。
        available = self.platform == "win32" and dependency_available  # 新增代码+Phase46WindowsUiaTree: 只有 Windows 且有依赖才视为可用；如果没有这行代码，非 Windows 会误报可读 UIA。
        reason = "UIA 控件树运行时可用，将返回结构化控件节点。" if available else "UIA 控件树运行时不可用，未安装依赖或当前不是 Windows。"  # 新增代码+Phase46WindowsUiaTree: 生成可读状态原因；如果没有这行代码，用户不知道为什么没有树。
        return {"marker": PHASE46_WINDOWS_UIA_TREE_MARKER, "model": PHASE46_UIA_TREE_MODEL, "backend": "uiautomation_control_tree", "available": available, "reason": reason, "dependency": "uiautomation", "max_depth": self.max_depth, "max_nodes": self.max_nodes, "max_text_length": self.max_text_length, "actions_expanded": PHASE46_ACTIONS_EXPANDED}  # 新增代码+Phase46WindowsUiaTree: 返回完整状态；如果没有这行代码，状态 UI 没有统一事实源。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime.status 到此结束；如果没有这个边界说明，读者不容易看出状态范围。

    def _failure(self, reason: str) -> dict[str, Any]:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，构造统一失败结果；如果没有这段函数，失败分支会重复且字段不一致。
        return {"marker": PHASE46_WINDOWS_UIA_TREE_MARKER, "model": PHASE46_UIA_TREE_MODEL, "captured": False, "reason": str(reason), "tree": {}, "flat_nodes": [], "node_count": 0, "truncated": False, "sensitive_text_filtered": 0, "bounds_available": False, "clickable_count": 0, "editable_count": 0, "actions_expanded": PHASE46_ACTIONS_EXPANDED}  # 新增代码+Phase46WindowsUiaTree: 返回稳定失败结构；如果没有这行代码，host 和测试无法机器读取失败原因。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime._failure 到此结束；如果没有这个边界说明，读者不容易看出失败结果范围。

    def observe_window(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，读取指定窗口的结构化 UIA 控件树；如果没有这段函数，runtime 只有状态没有观察能力。
        safe_window = dict(window or {})  # 新增代码+Phase46WindowsUiaTree: 复制窗口输入避免污染调用方对象；如果没有这行代码，后续补字段可能改到外部状态。
        if self.platform != "win32":  # 新增代码+Phase46WindowsUiaTree: 非 Windows 平台拒绝读取；如果没有这行代码，跨平台测试会尝试 UIA API。
            return self._failure("当前平台不是 Windows，未读取 UIA 控件树。")  # 新增代码+Phase46WindowsUiaTree: 返回平台拒绝原因；如果没有这行代码，用户不知道为何无树。
        hwnd = parse_hwnd_from_window(safe_window)  # 新增代码+Phase46WindowsUiaTree: 解析窗口句柄；如果没有这行代码，UIA 模块不知道目标窗口。
        if hwnd <= 0:  # 新增代码+Phase46WindowsUiaTree: 检查 hwnd 是否有效；如果没有这行代码，0 句柄可能传给 UIA。
            return self._failure("窗口句柄无效，未读取 UIA 控件树。")  # 新增代码+Phase46WindowsUiaTree: 返回坏句柄原因；如果没有这行代码，错误目标不可解释。
        module = self._load_uia_module()  # 新增代码+Phase46WindowsUiaTree: 加载注入或真实 UIA 模块；如果没有这行代码，runtime 不知道如何获取根控件。
        if module is None:  # 新增代码+Phase46WindowsUiaTree: 检查依赖是否缺失；如果没有这行代码，缺依赖会变成异常。
            return self._failure("未找到 uiautomation 模块，未读取 UIA 控件树。")  # 新增代码+Phase46WindowsUiaTree: 返回缺依赖原因；如果没有这行代码，状态不可解释。
        try:  # 新增代码+Phase46WindowsUiaTree: 包住真实 UIA 读取流程；如果没有这行代码，窗口销毁或控件异常会拖垮 agent。
            root = module.ControlFromHandle(int(hwnd))  # 新增代码+Phase46WindowsUiaTree: 从窗口句柄获取 UIA 根控件；如果没有这行代码，控件树没有入口。
            state = {"count": 0, "truncated": False, "sensitive": 0, "flat_nodes": []}  # 新增代码+Phase46WindowsUiaTree: 初始化遍历状态；如果没有这行代码，节点上限和脱敏计数无法审计。
            tree = self._build_node(root, 0, "0", state)  # 新增代码+Phase46WindowsUiaTree: 有界构建结构化树；如果没有这行代码，UIA 根控件不会变成 JSON。
            flat_nodes = list(state["flat_nodes"])  # 新增代码+Phase46WindowsUiaTree: 复制扁平节点列表；如果没有这行代码，返回值可能共享内部状态。
            clickable_count = sum(1 for node in flat_nodes if node.get("clickable"))  # 新增代码+Phase46WindowsUiaTree: 统计可点击节点；如果没有这行代码，模型需要自己扫描树。
            editable_count = sum(1 for node in flat_nodes if node.get("editable"))  # 新增代码+Phase46WindowsUiaTree: 统计可输入节点；如果没有这行代码，模型需要自己判断输入目标。
            bounds_available = any(bool(node.get("bounds", {}).get("width") or node.get("bounds", {}).get("height")) for node in flat_nodes)  # 新增代码+Phase46WindowsUiaTree: 判断是否有边界框；如果没有这行代码，验收无法确认坐标信息存在。
            captured = tree is not None and bool(flat_nodes)  # 新增代码+Phase46WindowsUiaTree: 判断是否成功读到节点；如果没有这行代码，空树可能误报成功。
            reason = "UIA 控件树读取成功。" if captured else "UIA 控件树没有返回可读节点。"  # 新增代码+Phase46WindowsUiaTree: 生成可读结果原因；如果没有这行代码，空结果不易排查。
            return {"marker": PHASE46_WINDOWS_UIA_TREE_MARKER, "model": PHASE46_UIA_TREE_MODEL, "captured": captured, "reason": reason, "tree": tree or {}, "flat_nodes": flat_nodes, "node_count": len(flat_nodes), "truncated": bool(state["truncated"]), "sensitive_text_filtered": int(state["sensitive"]), "bounds_available": bounds_available, "clickable_count": clickable_count, "editable_count": editable_count, "actions_expanded": PHASE46_ACTIONS_EXPANDED}  # 新增代码+Phase46WindowsUiaTree: 返回结构化树摘要；如果没有这行代码，host 和工具拿不到统一 UIA 树结果。
        except Exception as error:  # 新增代码+Phase46WindowsUiaTree: 捕获 UIA 运行异常；如果没有这行代码，目标窗口变化会让 agent 崩溃。
            return self._failure(f"UIA 控件树读取失败：{type(error).__name__}")  # 新增代码+Phase46WindowsUiaTree: 返回异常类型；如果没有这行代码，失败原因不稳定。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime.observe_window 到此结束；如果没有这个边界说明，读者不容易看出观察流程范围。

    def _load_uia_module(self) -> Any | None:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，加载 UIA 模块；如果没有这段函数，导入逻辑会散落在 status 和 observe。
        if self.uia_module is not None:  # 新增代码+Phase46WindowsUiaTree: 优先使用注入模块；如果没有这行代码，测试无法避免真实桌面依赖。
            return self.uia_module  # 新增代码+Phase46WindowsUiaTree: 返回注入模块；如果没有这行代码，fake UIA 树无法工作。
        try:  # 新增代码+Phase46WindowsUiaTree: 捕获真实依赖导入异常；如果没有这行代码，缺依赖会在 observe 中崩溃。
            return __import__("uiautomation")  # 新增代码+Phase46WindowsUiaTree: 延迟导入真实 uiautomation；如果没有这行代码，生产环境无法使用 UIA 树。
        except Exception:  # 新增代码+Phase46WindowsUiaTree: 捕获所有导入失败；如果没有这行代码，缺依赖无法安全降级。
            return None  # 新增代码+Phase46WindowsUiaTree: 缺依赖时返回 None；如果没有这行代码，调用方不知道如何判断不可用。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime._load_uia_module 到此结束；如果没有这个边界说明，读者不容易看出依赖加载范围。

    def _build_node(self, control: Any, depth: int, node_id: str, state: dict[str, Any]) -> dict[str, Any] | None:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，有界递归构建单个节点；如果没有这段函数，控件树无法保持层级结构。
        if control is None:  # 新增代码+Phase46WindowsUiaTree: 检查空控件；如果没有这行代码，空子节点会触发属性读取异常。
            return None  # 新增代码+Phase46WindowsUiaTree: 空控件直接跳过；如果没有这行代码，树里会出现无意义节点。
        if depth > self.max_depth:  # 新增代码+Phase46WindowsUiaTree: 检查深度上限；如果没有这行代码，复杂窗口可能递归过深。
            state["truncated"] = True  # 新增代码+Phase46WindowsUiaTree: 标记因为深度被截断；如果没有这行代码，用户不知道树不完整。
            return None  # 新增代码+Phase46WindowsUiaTree: 超深节点停止读取；如果没有这行代码，max_depth 不生效。
        if int(state["count"]) >= self.max_nodes:  # 新增代码+Phase46WindowsUiaTree: 检查节点数量上限；如果没有这行代码，大窗口可能刷屏。
            state["truncated"] = True  # 新增代码+Phase46WindowsUiaTree: 标记因为数量被截断；如果没有这行代码，用户不知道输出被限制。
            return None  # 新增代码+Phase46WindowsUiaTree: 达到数量上限后停止；如果没有这行代码，max_nodes 不生效。
        node = self._format_node(control, depth, node_id, state)  # 新增代码+Phase46WindowsUiaTree: 格式化当前控件为安全节点；如果没有这行代码，UIA 对象无法进入 JSON。
        state["count"] = int(state["count"]) + 1  # 新增代码+Phase46WindowsUiaTree: 记录已读取节点数；如果没有这行代码，max_nodes 无法工作。
        flat_node = dict(node)  # 新增代码+Phase46WindowsUiaTree: 复制节点用于扁平索引；如果没有这行代码，flat_nodes 会和树节点互相污染。
        state["flat_nodes"].append(flat_node)  # 新增代码+Phase46WindowsUiaTree: 保存扁平节点；如果没有这行代码，调用方要自己递归扫描树。
        children: list[dict[str, Any]] = []  # 新增代码+Phase46WindowsUiaTree: 准备子节点容器；如果没有这行代码，树节点无法携带 children。
        for index, child in enumerate(self._children(control)):  # 新增代码+Phase46WindowsUiaTree: 遍历子控件；如果没有这行代码，树只会有根节点。
            if int(state["count"]) >= self.max_nodes:  # 新增代码+Phase46WindowsUiaTree: 每个子节点前检查数量上限；如果没有这行代码，兄弟节点过多会越界。
                state["truncated"] = True  # 新增代码+Phase46WindowsUiaTree: 标记节点数量截断；如果没有这行代码，用户不知道还有未读节点。
                break  # 新增代码+Phase46WindowsUiaTree: 达到上限后停止当前层；如果没有这行代码，max_nodes 不生效。
            child_node = self._build_node(child, depth + 1, f"{node_id}.{index}", state)  # 新增代码+Phase46WindowsUiaTree: 递归构建子节点；如果没有这行代码，层级结构无法展开。
            if child_node is not None:  # 新增代码+Phase46WindowsUiaTree: 检查子节点是否有效；如果没有这行代码，None 会进入 JSON。
                children.append(child_node)  # 新增代码+Phase46WindowsUiaTree: 保存有效子节点；如果没有这行代码，树结构会丢子节点。
        node["children"] = children  # 新增代码+Phase46WindowsUiaTree: 给当前节点挂载子节点；如果没有这行代码，返回树无法表示层级。
        return node  # 新增代码+Phase46WindowsUiaTree: 返回结构化节点；如果没有这行代码，父节点拿不到子树。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime._build_node 到此结束；如果没有这个边界说明，读者不容易看出递归范围。

    def _format_node(self, control: Any, depth: int, node_id: str, state: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，把单个 UIA 控件转成安全 JSON 节点；如果没有这段函数，控件属性会零散输出。
        name, name_filtered = self._safe_control_text(self._control_value(control, ("Name", "name", "CurrentName", "GetName")))  # 新增代码+Phase46WindowsUiaTree: 读取并脱敏控件名称；如果没有这行代码，password/token 可能进入树。
        role, role_filtered = self._safe_control_text(self._control_value(control, ("ControlTypeName", "LocalizedControlType", "control_type", "GetControlTypeName")))  # 新增代码+Phase46WindowsUiaTree: 读取并脱敏控件角色；如果没有这行代码，控件语义会丢失。
        automation_id, automation_filtered = self._safe_control_text(self._control_value(control, ("AutomationId", "automation_id", "CurrentAutomationId")))  # 新增代码+Phase46WindowsUiaTree: 读取并脱敏 automation id；如果没有这行代码，稳定定位线索会丢失。
        class_name, class_filtered = self._safe_control_text(self._control_value(control, ("ClassName", "class_name", "CurrentClassName")))  # 新增代码+Phase46WindowsUiaTree: 读取并脱敏 class name；如果没有这行代码，调试缺少控件类信息。
        state["sensitive"] = int(state["sensitive"]) + name_filtered + role_filtered + automation_filtered + class_filtered  # 新增代码+Phase46WindowsUiaTree: 累加敏感字段过滤次数；如果没有这行代码，用户无法审计脱敏发生。
        bounds = self._control_bounds(control)  # 新增代码+Phase46WindowsUiaTree: 读取控件边界框；如果没有这行代码，节点没有坐标信息。
        enabled = _safe_bool(self._raw_control_value(control, ("IsEnabled", "CurrentIsEnabled", "enabled")), True)  # 新增代码+Phase46WindowsUiaTree: 读取控件可用状态；如果没有这行代码，禁用控件也可能被建议点击。
        clickable = enabled and self._is_clickable(role, class_name, name)  # 新增代码+Phase46WindowsUiaTree: 计算可点击提示；如果没有这行代码，模型需要猜哪些节点能点击。
        editable = enabled and self._is_editable(role, class_name, name)  # 新增代码+Phase46WindowsUiaTree: 计算可输入提示；如果没有这行代码，模型需要猜哪些节点能输入。
        return {"node_id": str(node_id), "depth": int(depth), "name": name, "role": role, "automation_id": automation_id, "class_name": class_name, "bounds": bounds, "enabled": enabled, "clickable": clickable, "editable": editable}  # 新增代码+Phase46WindowsUiaTree: 返回安全节点摘要；如果没有这行代码，调用方拿不到统一字段。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime._format_node 到此结束；如果没有这个边界说明，读者不容易看出节点格式范围。

    def _safe_control_text(self, value: Any) -> tuple[str, int]:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，过滤单个控件文本字段；如果没有这段函数，敏感控件名可能进入输出。
        raw_text = str(value or "").strip()  # 新增代码+Phase46WindowsUiaTree: 规范化原始文本；如果没有这行代码，None 或对象值会污染树。
        if not raw_text:  # 新增代码+Phase46WindowsUiaTree: 检查空文本；如果没有这行代码，空字段会做无意义过滤。
            return "", 0  # 新增代码+Phase46WindowsUiaTree: 空文本返回空值和零过滤；如果没有这行代码，调用方无法区分空和敏感。
        filtered = filter_accessibility_text(raw_text, max_length=self.max_text_length)  # 新增代码+Phase46WindowsUiaTree: 复用 Phase29 过滤和截断；如果没有这行代码，UIA 树和 evidence 脱敏规则会不一致。
        if filtered.filtered_line_count > 0 or any(keyword in raw_text.lower() for keyword in SENSITIVE_ACCESSIBILITY_KEYWORDS):  # 新增代码+Phase46WindowsUiaTree: 二次检查敏感关键词；如果没有这行代码，单字段敏感文本可能因合并方式漏掉。
            return "[redacted]", max(1, filtered.filtered_line_count)  # 新增代码+Phase46WindowsUiaTree: 敏感字段只返回占位符；如果没有这行代码，具体密码/token 会泄露。
        return filtered.excerpt, 0  # 新增代码+Phase46WindowsUiaTree: 返回安全截断文本；如果没有这行代码，正常控件名也会丢失。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime._safe_control_text 到此结束；如果没有这个边界说明，读者不容易看出文本脱敏范围。

    def _control_value(self, control: Any, names: tuple[str, ...]) -> str:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，按候选属性读取控件文本；如果没有这段函数，不同 UIA 包属性差异会导致读取失败。
        value = self._raw_control_value(control, names)  # 新增代码+Phase46WindowsUiaTree: 先读取原始属性值；如果没有这行代码，字符串转换逻辑会重复。
        return str(value or "").strip()  # 新增代码+Phase46WindowsUiaTree: 统一转成去空格文本；如果没有这行代码，JSON 字段可能出现对象 repr。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime._control_value 到此结束；如果没有这个边界说明，读者不容易看出文本读取范围。

    def _raw_control_value(self, control: Any, names: tuple[str, ...]) -> Any:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，按候选属性读取原始控件值；如果没有这段函数，bounds 和 enabled 难以复用读取逻辑。
        for name in names:  # 新增代码+Phase46WindowsUiaTree: 遍历候选属性名；如果没有这行代码，runtime 只能兼容一种 UIA 对象。
            try:  # 新增代码+Phase46WindowsUiaTree: 捕获单个属性读取异常；如果没有这行代码，一个坏属性会中断整棵树。
                value = getattr(control, name)  # 新增代码+Phase46WindowsUiaTree: 读取属性或方法；如果没有这行代码，控件值无法获取。
            except Exception:  # 新增代码+Phase46WindowsUiaTree: 捕获 getattr 异常；如果没有这行代码，动态 UIA 对象可能抛错。
                continue  # 新增代码+Phase46WindowsUiaTree: 跳过坏属性继续尝试；如果没有这行代码，兼容性会变差。
            if callable(value):  # 新增代码+Phase46WindowsUiaTree: 判断属性是否是方法；如果没有这行代码，方法对象会被当成文本。
                try:  # 新增代码+Phase46WindowsUiaTree: 捕获方法调用异常；如果没有这行代码，需要参数的方法会中断读取。
                    value = value()  # 新增代码+Phase46WindowsUiaTree: 调用无参 getter；如果没有这行代码，GetName/GetChildren 风格接口无法读取。
                except TypeError:  # 新增代码+Phase46WindowsUiaTree: 捕获需要参数的方法；如果没有这行代码，不兼容 getter 会崩溃。
                    continue  # 新增代码+Phase46WindowsUiaTree: 跳过不兼容方法；如果没有这行代码，后续候选无法尝试。
                except Exception:  # 新增代码+Phase46WindowsUiaTree: 捕获 getter 运行异常；如果没有这行代码，失效控件会中断整棵树。
                    continue  # 新增代码+Phase46WindowsUiaTree: 跳过异常 getter；如果没有这行代码，读取不够稳。
            if value not in (None, ""):  # 新增代码+Phase46WindowsUiaTree: 检查值是否存在；如果没有这行代码，空属性会提前返回。
                return value  # 新增代码+Phase46WindowsUiaTree: 返回第一个可用值；如果没有这行代码，调用方拿不到控件属性。
        return None  # 新增代码+Phase46WindowsUiaTree: 没有可用值时返回 None；如果没有这行代码，调用方需要自己兜底。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime._raw_control_value 到此结束；如果没有这个边界说明，读者不容易看出原始属性读取范围。

    def _children(self, control: Any) -> list[Any]:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，读取子控件列表；如果没有这段函数，树遍历只能读取根节点。
        value = self._raw_control_value(control, ("GetChildren", "Children", "children"))  # 新增代码+Phase46WindowsUiaTree: 读取常见子控件接口；如果没有这行代码，子节点无法获取。
        try:  # 新增代码+Phase46WindowsUiaTree: 尝试把结果转为 list；如果没有这行代码，tuple/迭代器处理不统一。
            return list(value or [])  # 新增代码+Phase46WindowsUiaTree: 返回子控件副本；如果没有这行代码，调用方可能改写原始集合。
        except TypeError:  # 新增代码+Phase46WindowsUiaTree: 捕获非可迭代 children；如果没有这行代码，异常对象会中断遍历。
            return []  # 新增代码+Phase46WindowsUiaTree: 坏 children 返回空列表；如果没有这行代码，调用方需要自己兜底。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime._children 到此结束；如果没有这个边界说明，读者不容易看出子控件读取范围。

    def _control_bounds(self, control: Any) -> dict[str, int]:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，读取控件边界框；如果没有这段函数，节点没有坐标可供后续定位。
        raw_bounds = self._raw_control_value(control, ("BoundingRectangle", "CurrentBoundingRectangle", "bounding_rectangle", "Rectangle"))  # 新增代码+Phase46WindowsUiaTree: 读取常见边界属性；如果没有这行代码，真实 UIA 坐标不会进入结果。
        if isinstance(raw_bounds, dict):  # 新增代码+Phase46WindowsUiaTree: 支持 dict 形态边界；如果没有这行代码，轻量 fake provider 需要额外适配。
            left = _safe_int(raw_bounds.get("left", raw_bounds.get("Left", 0)))  # 新增代码+Phase46WindowsUiaTree: 读取 dict 左边界；如果没有这行代码，bounds.left 不稳定。
            top = _safe_int(raw_bounds.get("top", raw_bounds.get("Top", 0)))  # 新增代码+Phase46WindowsUiaTree: 读取 dict 上边界；如果没有这行代码，bounds.top 不稳定。
            right = _safe_int(raw_bounds.get("right", raw_bounds.get("Right", 0)))  # 新增代码+Phase46WindowsUiaTree: 读取 dict 右边界；如果没有这行代码，bounds.right 不稳定。
            bottom = _safe_int(raw_bounds.get("bottom", raw_bounds.get("Bottom", 0)))  # 新增代码+Phase46WindowsUiaTree: 读取 dict 下边界；如果没有这行代码，bounds.bottom 不稳定。
        elif isinstance(raw_bounds, (list, tuple)) and len(raw_bounds) >= 4:  # 新增代码+Phase46WindowsUiaTree: 支持 tuple/list 形态边界；如果没有这行代码，部分 UIA 包坐标无法解析。
            left, top, right, bottom = (_safe_int(raw_bounds[0]), _safe_int(raw_bounds[1]), _safe_int(raw_bounds[2]), _safe_int(raw_bounds[3]))  # 新增代码+Phase46WindowsUiaTree: 读取序列四边；如果没有这行代码，列表边界无法进入结果。
        else:  # 新增代码+Phase46WindowsUiaTree: 处理对象或缺失边界；如果没有这行代码，普通 BoundingRectangle 对象无法解析。
            left = _safe_int(getattr(raw_bounds, "Left", getattr(raw_bounds, "left", 0)))  # 新增代码+Phase46WindowsUiaTree: 读取对象左边界；如果没有这行代码，fake/真实矩形 x 起点缺失。
            top = _safe_int(getattr(raw_bounds, "Top", getattr(raw_bounds, "top", 0)))  # 新增代码+Phase46WindowsUiaTree: 读取对象上边界；如果没有这行代码，fake/真实矩形 y 起点缺失。
            right = _safe_int(getattr(raw_bounds, "Right", getattr(raw_bounds, "right", 0)))  # 新增代码+Phase46WindowsUiaTree: 读取对象右边界；如果没有这行代码，宽度无法计算。
            bottom = _safe_int(getattr(raw_bounds, "Bottom", getattr(raw_bounds, "bottom", 0)))  # 新增代码+Phase46WindowsUiaTree: 读取对象下边界；如果没有这行代码，高度无法计算。
        width = max(0, right - left)  # 新增代码+Phase46WindowsUiaTree: 计算宽度并防止负数；如果没有这行代码，后续定位不知道控件尺寸。
        height = max(0, bottom - top)  # 新增代码+Phase46WindowsUiaTree: 计算高度并防止负数；如果没有这行代码，后续定位不知道控件尺寸。
        return {"left": left, "top": top, "right": right, "bottom": bottom, "width": width, "height": height}  # 新增代码+Phase46WindowsUiaTree: 返回标准边界对象；如果没有这行代码，调用方需要兼容多种坐标形态。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime._control_bounds 到此结束；如果没有这个边界说明，读者不容易看出边界解析范围。

    def _is_clickable(self, role: str, class_name: str, name: str) -> bool:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，判断控件是否像可点击目标；如果没有这段函数，模型需要自己猜按钮和链接。
        text = f"{role} {class_name} {name}".lower()  # 新增代码+Phase46WindowsUiaTree: 合并控件线索为小写文本；如果没有这行代码，关键词判断会重复。
        return any(token in text for token in ("button", "hyperlink", "menuitem", "checkbox", "radio", "tabitem", "listitem"))  # 新增代码+Phase46WindowsUiaTree: 根据常见 UIA 类型判断可点击；如果没有这行代码，clickable_count 无法生成。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime._is_clickable 到此结束；如果没有这个边界说明，读者不容易看出点击提示范围。

    def _is_editable(self, role: str, class_name: str, name: str) -> bool:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，判断控件是否像可输入目标；如果没有这段函数，模型需要自己猜输入框。
        text = f"{role} {class_name} {name}".lower()  # 新增代码+Phase46WindowsUiaTree: 合并控件线索为小写文本；如果没有这行代码，关键词判断会重复。
        return any(token in text for token in ("edit", "textbox", "document", "combobox", "text area", "textarea"))  # 新增代码+Phase46WindowsUiaTree: 根据常见 UIA 类型判断可输入；如果没有这行代码，editable_count 无法生成。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，WindowsUiaControlTreeRuntime._is_editable 到此结束；如果没有这个边界说明，读者不容易看出输入提示范围。
# 新增代码+Phase46WindowsUiaTree: 类段结束，WindowsUiaControlTreeRuntime 到此结束；如果没有这个边界说明，读者不容易看出控件树 runtime 范围。


class _Phase46ContractRect:  # 新增代码+Phase46WindowsUiaTree: 类段开始，定义 CLI 自检专用矩形；如果没有这个类，自检无法证明 bounds=true。
    def __init__(self, left: int, top: int, right: int, bottom: int) -> None:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，保存矩形四边；如果没有这段函数，自检控件没有坐标。
        self.Left = left  # 新增代码+Phase46WindowsUiaTree: 保存左边界；如果没有这行代码，bounds.left 无法读取。
        self.Top = top  # 新增代码+Phase46WindowsUiaTree: 保存上边界；如果没有这行代码，bounds.top 无法读取。
        self.Right = right  # 新增代码+Phase46WindowsUiaTree: 保存右边界；如果没有这行代码，bounds.width 无法计算。
        self.Bottom = bottom  # 新增代码+Phase46WindowsUiaTree: 保存下边界；如果没有这行代码，bounds.height 无法计算。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，_Phase46ContractRect.__init__ 到此结束；如果没有这个边界说明，读者不容易看出自检矩形范围。


class _Phase46ContractControl:  # 新增代码+Phase46WindowsUiaTree: 类段开始，定义 CLI 自检专用 fake 控件；如果没有这个类，自检会触碰真实桌面。
    def __init__(self, name: str, role: str, automation_id: str, class_name: str, rect: _Phase46ContractRect, children: list["_Phase46ContractControl"] | None = None) -> None:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，初始化 fake 控件；如果没有这段函数，自检无法构造树。
        self.Name = name  # 新增代码+Phase46WindowsUiaTree: 保存控件名称；如果没有这行代码，自检无法证明 tree=true。
        self.ControlTypeName = role  # 新增代码+Phase46WindowsUiaTree: 保存控件角色；如果没有这行代码，自检无法证明 controls=true。
        self.AutomationId = automation_id  # 新增代码+Phase46WindowsUiaTree: 保存 automation id；如果没有这行代码，自检缺少定位线索。
        self.ClassName = class_name  # 新增代码+Phase46WindowsUiaTree: 保存 class name；如果没有这行代码，自检缺少控件类。
        self.BoundingRectangle = rect  # 新增代码+Phase46WindowsUiaTree: 保存边界框；如果没有这行代码，自检无法证明 bounds=true。
        self.IsEnabled = True  # 新增代码+Phase46WindowsUiaTree: 标记控件可用；如果没有这行代码，clickable/editable 判断可能受缺省影响。
        self._children = list(children or [])  # 新增代码+Phase46WindowsUiaTree: 保存子控件；如果没有这行代码，自检树无法展开。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，_Phase46ContractControl.__init__ 到此结束；如果没有这个边界说明，读者不容易看出自检控件范围。

    def GetChildren(self) -> list["_Phase46ContractControl"]:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，返回子控件；如果没有这段函数，runtime 无法遍历自检树。
        return list(self._children)  # 新增代码+Phase46WindowsUiaTree: 返回子控件副本；如果没有这行代码，自检树可能被调用方污染。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，_Phase46ContractControl.GetChildren 到此结束；如果没有这个边界说明，读者不容易看出自检子控件接口范围。


class _Phase46ContractUiaModule:  # 新增代码+Phase46WindowsUiaTree: 类段开始，定义 CLI 自检 fake UIA 模块；如果没有这个类，自检必须依赖真实 uiautomation。
    def __init__(self, root: _Phase46ContractControl) -> None:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，保存根控件；如果没有这段函数，ControlFromHandle 没有返回对象。
        self.root = root  # 新增代码+Phase46WindowsUiaTree: 保存根控件；如果没有这行代码，自检 observe_window 会失败。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，_Phase46ContractUiaModule.__init__ 到此结束；如果没有这个边界说明，读者不容易看出自检模块范围。

    def ControlFromHandle(self, hwnd: int) -> _Phase46ContractControl:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，按 hwnd 返回根控件；如果没有这段函数，runtime 没有树入口。
        return self.root  # 新增代码+Phase46WindowsUiaTree: 返回根控件；如果没有这行代码，结构化树无法生成。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，_Phase46ContractUiaModule.ControlFromHandle 到此结束；如果没有这个边界说明，读者不容易看出 hwnd 映射范围。


def _phase46_contract_module(include_secret: bool = True) -> _Phase46ContractUiaModule:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，构造安全自检 UIA 模块；如果没有这段函数，CLI 和 host 自检会重复搭树。
    save = _Phase46ContractControl("Save", "ButtonControl", "save", "Button", _Phase46ContractRect(20, 60, 120, 92))  # 新增代码+Phase46WindowsUiaTree: 创建可点击按钮；如果没有这行代码，controls=true 缺少 clickable 证据。
    editor = _Phase46ContractControl("Document", "EditControl", "editor", "Edit", _Phase46ContractRect(20, 110, 460, 260))  # 新增代码+Phase46WindowsUiaTree: 创建可输入区域；如果没有这行代码，controls=true 缺少 editable 证据。
    children = [save, editor]  # 新增代码+Phase46WindowsUiaTree: 准备基础子控件列表；如果没有这行代码，根窗口没有内容。
    if include_secret:  # 新增代码+Phase46WindowsUiaTree: 根据自检需要加入敏感节点；如果没有这行代码，redacted=true 没有输入。
        children.append(_Phase46ContractControl("password: phase46-contract-secret", "EditControl", "secret", "Edit", _Phase46ContractRect(20, 270, 460, 300)))  # 新增代码+Phase46WindowsUiaTree: 创建敏感节点；如果没有这行代码，脱敏检查无法证明有效。
    root = _Phase46ContractControl("Phase46 Root", "WindowControl", "root", "Window", _Phase46ContractRect(10, 20, 500, 320), children=children)  # 新增代码+Phase46WindowsUiaTree: 创建根窗口；如果没有这行代码，自检没有树入口。
    return _Phase46ContractUiaModule(root)  # 新增代码+Phase46WindowsUiaTree: 返回 fake UIA 模块；如果没有这行代码，runtime 自检无法运行。
# 新增代码+Phase46WindowsUiaTree: 函数段结束，_phase46_contract_module 到此结束；如果没有这个边界说明，读者不容易看出自检树构造范围。


def run_phase46_uia_tree_contract() -> dict[str, Any]:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，运行 Phase46 安全自检合同；如果没有这段函数，真实终端场景没有稳定命令入口。
    from learning_agent.computer_use.native_host import InProcessWindowsNativeHostClient, WindowsComputerUseNativeHost  # 新增代码+Phase46WindowsUiaTree: 延迟导入 native host 避免循环依赖；如果没有这行代码，自检无法证明 host observe 集成。
    window = {"window_id": "hwnd:4601", "hwnd": 4601, "title": "Phase46 Contract Window", "rect": {"left": 10, "top": 20, "right": 500, "bottom": 320}}  # 新增代码+Phase46WindowsUiaTree: 准备静态窗口引用；如果没有这行代码，runtime 无法解析 hwnd。
    runtime = WindowsUiaControlTreeRuntime(platform="win32", uia_module=_phase46_contract_module(include_secret=True), max_depth=5, max_nodes=10)  # 新增代码+Phase46WindowsUiaTree: 创建带敏感节点的 fake runtime；如果没有这行代码，tree/bounds/redacted 没有证据。
    tree_result = runtime.observe_window(window)  # 新增代码+Phase46WindowsUiaTree: 执行一次 UIA 树观察；如果没有这行代码，自检只会检查空状态。
    host_runtime = WindowsUiaControlTreeRuntime(platform="win32", uia_module=_phase46_contract_module(include_secret=False), max_depth=5, max_nodes=10)  # 新增代码+Phase46WindowsUiaTree: 创建 host 专用 runtime；如果没有这行代码，host_observe 没有独立证据。
    host = WindowsComputerUseNativeHost(platform="win32", uia_tree_runtime=host_runtime)  # 新增代码+Phase46WindowsUiaTree: 注入 UIA 树 runtime 到 native host；如果没有这行代码，Phase44 observe 不会走 Phase46 链路。
    host_observe = InProcessWindowsNativeHostClient(host).request({"op": "observe", "window": window})  # 新增代码+Phase46WindowsUiaTree: 通过 host observe 消息读取树；如果没有这行代码，集成路径不会执行。
    encoded = json.dumps(tree_result, ensure_ascii=False).lower()  # 新增代码+Phase46WindowsUiaTree: 序列化树结果用于敏感值检查；如果没有这行代码，redacted=true 没有全局证据。
    tree = bool(tree_result.get("captured") and tree_result.get("node_count", 0) >= 3)  # 新增代码+Phase46WindowsUiaTree: 检查树是否读取成功；如果没有这行代码，OK token 可能只证明模块可导入。
    bounds = bool(tree_result.get("bounds_available"))  # 新增代码+Phase46WindowsUiaTree: 检查边界框是否存在；如果没有这行代码，bounds=true 没有证据。
    controls = bool(tree_result.get("clickable_count", 0) >= 1 and tree_result.get("editable_count", 0) >= 1)  # 新增代码+Phase46WindowsUiaTree: 检查可点击和可输入摘要；如果没有这行代码，controls=true 没有证据。
    redacted = bool(tree_result.get("sensitive_text_filtered", 0) >= 1 and "phase46-contract-secret" not in encoded)  # 新增代码+Phase46WindowsUiaTree: 检查敏感文本已过滤；如果没有这行代码，密码泄露也可能通过。
    host_result = host_observe.get("result", {}) if isinstance(host_observe, dict) else {}  # 新增代码+Phase46WindowsUiaTree: 提取 host observe 结果；如果没有这行代码，host_observe=true 无法判断。
    host_ok = bool(host_observe.get("ok") and host_result.get("captured") and host_result.get("node_count", 0) >= 3)  # 新增代码+Phase46WindowsUiaTree: 检查 host 集成成功；如果没有这行代码，Phase46 可能没有接入 native host。
    return {"marker": PHASE46_WINDOWS_UIA_TREE_MARKER, "ok_token": PHASE46_WINDOWS_UIA_TREE_OK_TOKEN, "tree": tree, "bounds": bounds, "controls": controls, "redacted": redacted, "host_observe": host_ok, "actions_expanded": PHASE46_ACTIONS_EXPANDED, "tree_result": tree_result, "host_observe_result": host_observe}  # 新增代码+Phase46WindowsUiaTree: 返回完整自检报告；如果没有这行代码，CLI 和测试拿不到统一结果。
# 新增代码+Phase46WindowsUiaTree: 函数段结束，run_phase46_uia_tree_contract 到此结束；如果没有这个边界说明，读者不容易看出自检范围。


def phase46_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，把自检报告转成稳定 token 行；如果没有这段函数，验收场景需要解析完整 JSON。
    return f"{PHASE46_WINDOWS_UIA_TREE_MARKER} {PHASE46_WINDOWS_UIA_TREE_OK_TOKEN} tree={_phase46_bool_token(report.get('tree'))} bounds={_phase46_bool_token(report.get('bounds'))} controls={_phase46_bool_token(report.get('controls'))} redacted={_phase46_bool_token(report.get('redacted'))} host_observe={_phase46_bool_token(report.get('host_observe'))} actions_expanded={_phase46_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase46WindowsUiaTree: 返回固定顺序验收行；如果没有这行代码，debug log token 容易漂移。
# 新增代码+Phase46WindowsUiaTree: 函数段结束，phase46_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 格式范围。


def main() -> int:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，提供命令行自检入口；如果没有这段函数，真实终端无法执行 Phase46 验收命令。
    report = run_phase46_uia_tree_contract()  # 新增代码+Phase46WindowsUiaTree: 运行安全自检；如果没有这行代码，CLI 没有真实报告。
    print(PHASE46_WINDOWS_UIA_TREE_MARKER)  # 新增代码+Phase46WindowsUiaTree: 打印 ready marker；如果没有这行代码，验收控制器可能等不到阶段标记。
    print(phase46_cli_line(report))  # 新增代码+Phase46WindowsUiaTree: 打印固定 token 行；如果没有这行代码，debug log 无法确认通过。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase46WindowsUiaTree: 打印结构化报告；如果没有这行代码，失败时不易复盘。
    return 0 if bool(report.get("tree") and report.get("bounds") and report.get("controls") and report.get("redacted") and report.get("host_observe") and report.get("actions_expanded") is False) else 1  # 新增代码+Phase46WindowsUiaTree: 根据自检布尔值返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase46WindowsUiaTree: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出命令入口范围。


if __name__ == "__main__":  # 新增代码+Phase46WindowsUiaTree: 允许直接运行模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase46WindowsUiaTree: 使用 main 返回码退出；如果没有这行代码，命令行状态不稳定。
