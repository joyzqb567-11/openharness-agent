"""高层浏览器工具 helper。"""  # 新增代码+Phase3HighLevelTools: 说明本模块负责把用户自然动作拆成底层浏览器工具；若没有这行代码，维护者不知道本文件的边界。
from __future__ import annotations  # 新增代码+Phase3HighLevelTools: 让类型注解延迟解析；若没有这行代码，未来复杂类型可能在导入时过早求值。
from typing import Any  # 新增代码+Phase3HighLevelTools: 高层工具参数来自 JSON，值类型不固定；若没有这行代码，函数签名无法清楚表达通用输入。

DEFAULT_BROWSER_SHORTCUTS: dict[str, str] = {  # 新增代码+Phase3HighLevelTools: 定义用户可用快捷键别名到 Playwright 按键名的映射；若没有这行代码，快捷键能力会散落在 server 方法里。
    "submit": "Enter",  # 新增代码+Phase3HighLevelTools: submit 表示提交当前表单；若没有这行代码，填表后无法用自然别名提交。
    "enter": "Enter",  # 新增代码+Phase3HighLevelTools: enter 兼容用户直接说回车；若没有这行代码，用户常见说法会失败。
    "escape": "Escape",  # 新增代码+Phase3HighLevelTools: escape 表示关闭弹窗或退出焦点；若没有这行代码，常见取消动作没有别名。
    "select_all": "Control+A",  # 新增代码+Phase3HighLevelTools: select_all 表示全选当前输入框内容；若没有这行代码，编辑输入框会更笨重。
    "copy": "Control+C",  # 新增代码+Phase3HighLevelTools: copy 表示复制当前选区；若没有这行代码，常见复制动作无法通过别名执行。
    "paste": "Control+V",  # 新增代码+Phase3HighLevelTools: paste 表示粘贴剪贴板内容；若没有这行代码，常见粘贴动作无法通过别名执行。
    "tab_next": "Tab",  # 新增代码+Phase3HighLevelTools: tab_next 表示移动到下一个焦点；若没有这行代码，表单字段切换需要手写底层按键。
    "tab_previous": "Shift+Tab",  # 新增代码+Phase3HighLevelTools: tab_previous 表示回到上一个焦点；若没有这行代码，反向焦点移动没有稳定别名。
    "back": "Alt+Left",  # 新增代码+Phase3HighLevelTools: back 表示浏览器后退；若没有这行代码，用户说后退时没有稳定映射。
    "forward": "Alt+Right",  # 新增代码+Phase3HighLevelTools: forward 表示浏览器前进；若没有这行代码，用户说前进时没有稳定映射。
    "reload": "Control+R",  # 新增代码+Phase3HighLevelTools: reload 表示刷新页面；若没有这行代码，刷新动作需要手写底层按键。
}  # 新增代码+Phase3HighLevelTools: 结束快捷键映射；若没有这行代码，Python 字典语法不完整。

FORM_TARGET_KEYS: tuple[str, ...] = (  # 新增代码+Phase3HighLevelTools: 定义允许透传到底层输入工具的定位和行为字段；若没有这行代码，字段过滤规则会重复分散。
    "page_id",  # 新增代码+Phase3HighLevelTools: page_id 指定目标标签页；若没有这项，批量填表无法跨标签页精确操作。
    "element_id",  # 新增代码+Phase3HighLevelTools: element_id 复用快照元素编号；若没有这项，快照定位无法进入批量填表。
    "selector",  # 新增代码+Phase3HighLevelTools: selector 支持 CSS 定位；若没有这项，工程化页面难以稳定填表。
    "label",  # 新增代码+Phase3HighLevelTools: label 支持表单标签定位；若没有这项，用户自然描述字段名不能工作。
    "clear",  # 新增代码+Phase3HighLevelTools: clear 控制是否清空旧值；若没有这项，用户不能表达追加或覆盖。
    "timeout_ms",  # 新增代码+Phase3HighLevelTools: timeout_ms 控制等待上限；若没有这项，慢表单无法调整等待时间。
)  # 新增代码+Phase3HighLevelTools: 结束透传字段元组；若没有这行代码，Python 元组语法不完整。

def _clean_text(value: Any) -> str:  # 新增代码+Phase3HighLevelTools: 把未知输入安全转成去首尾空白的字符串；若没有这段函数，多个地方会重复处理 None 和空格。
    return str(value or "").strip()  # 新增代码+Phase3HighLevelTools: None 变空串且清理空白；若没有这行代码，空值可能被当成真实字段名。

def browser_shortcut_key(shortcut_name: str) -> str:  # 新增代码+Phase3HighLevelTools: 把快捷键别名转换成 Playwright 按键名；若没有这段函数，server 和测试会各写一套映射。
    normalized_name = _clean_text(shortcut_name).lower()  # 新增代码+Phase3HighLevelTools: 统一大小写和空白；若没有这行代码，Submit 或带空格的输入会被误判。
    if normalized_name not in DEFAULT_BROWSER_SHORTCUTS:  # 新增代码+Phase3HighLevelTools: 检查别名是否受支持；若没有这行代码，未知别名可能变成空按键。
        supported_names = ", ".join(sorted(DEFAULT_BROWSER_SHORTCUTS))  # 新增代码+Phase3HighLevelTools: 生成可读支持列表；若没有这行代码，用户不知道该改成什么。
        raise ValueError(f"未知浏览器快捷键：{shortcut_name}。可用快捷键：{supported_names}")  # 新增代码+Phase3HighLevelTools: 用中文说明错误和可选值；若没有这行代码，新手只能看到底层 KeyError。
    return DEFAULT_BROWSER_SHORTCUTS[normalized_name]  # 新增代码+Phase3HighLevelTools: 返回真实按键名；若没有这行代码，高层快捷键无法交给 browser_press_key。

def format_shortcuts_list() -> str:  # 新增代码+Phase3HighLevelTools: 格式化快捷键清单给模型和用户查看；若没有这段函数，快捷键发现能力没有稳定输出。
    lines = ["browser_shortcuts_list 成功"]  # 新增代码+Phase3HighLevelTools: 输出工具成功标题；若没有这行代码，调用方难以识别结果类型。
    for shortcut_name in sorted(DEFAULT_BROWSER_SHORTCUTS):  # 新增代码+Phase3HighLevelTools: 按名称排序保证输出稳定；若没有这行代码，测试和模型解析会受字典顺序影响。
        lines.append(f"{shortcut_name}={DEFAULT_BROWSER_SHORTCUTS[shortcut_name]}")  # 新增代码+Phase3HighLevelTools: 输出 name=key 映射；若没有这行代码，用户看不到具体快捷键。
    return "\n".join(lines)  # 新增代码+Phase3HighLevelTools: 合并多行文本返回；若没有这行代码，server 无法直接返回清单。

def _field_arguments(field: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase3HighLevelTools: 从单个字段提取允许传给底层工具的参数；若没有这段函数，过滤规则会和安全意图混在一起。
    arguments: dict[str, Any] = {}  # 新增代码+Phase3HighLevelTools: 准备输出参数字典；若没有这行代码，后续没有容器保存字段。
    for key in FORM_TARGET_KEYS:  # 新增代码+Phase3HighLevelTools: 只遍历白名单字段；若没有这行代码，未知字段可能进入底层工具。
        if key in field:  # 新增代码+Phase3HighLevelTools: 只复制调用方真正传入的字段；若没有这行代码，会给底层塞入多余空字段。
            arguments[key] = field[key]  # 新增代码+Phase3HighLevelTools: 透传安全字段；若没有这行代码，定位和超时参数会丢失。
    return arguments  # 新增代码+Phase3HighLevelTools: 返回过滤后的参数；若没有这行代码，调用方拿不到结果。

def _submit_key(arguments: dict[str, Any]) -> str | None:  # 新增代码+Phase3HighLevelTools: 解析表单提交参数；若没有这段函数，submit 布尔和字符串别名会分散处理。
    submit_value = arguments.get("submit", False)  # 新增代码+Phase3HighLevelTools: 读取 submit 参数；若没有这行代码，批量填表无法知道是否提交。
    if submit_value is True:  # 新增代码+Phase3HighLevelTools: 布尔 true 表示默认回车提交；若没有这行代码，最常用提交写法不会生效。
        return browser_shortcut_key("submit")  # 新增代码+Phase3HighLevelTools: 复用快捷键映射得到 Enter；若没有这行代码，提交键规则会重复。
    if isinstance(submit_value, str) and submit_value.strip():  # 新增代码+Phase3HighLevelTools: 字符串 submit 表示指定快捷键别名；若没有这行代码，用户不能选择其他提交方式。
        return browser_shortcut_key(submit_value)  # 新增代码+Phase3HighLevelTools: 把提交别名转成按键；若没有这行代码，字符串 submit 不能执行。
    return None  # 新增代码+Phase3HighLevelTools: 未请求提交时返回空；若没有这行代码，所有填表都会意外按键。

def build_form_input_plan(arguments: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+Phase3HighLevelTools: 把批量填表请求拆成底层工具步骤；若没有这段函数，server 无法可靠复用底层工具。
    raw_fields = arguments.get("fields")  # 新增代码+Phase3HighLevelTools: 读取字段列表；若没有这行代码，函数不知道要填哪些字段。
    if not isinstance(raw_fields, list) or not raw_fields:  # 新增代码+Phase3HighLevelTools: 要求 fields 是非空列表；若没有这行代码，空任务可能被误报成功。
        raise ValueError("browser_form_input 需要非空 fields 列表。")  # 新增代码+Phase3HighLevelTools: 用中文说明参数要求；若没有这行代码，新手不知道该传什么结构。
    plan: list[dict[str, Any]] = []  # 新增代码+Phase3HighLevelTools: 准备保存底层动作计划；若没有这行代码，后续无法按顺序执行。
    for index, raw_field in enumerate(raw_fields, start=1):  # 新增代码+Phase3HighLevelTools: 按原始顺序遍历字段并保留序号；若没有这行代码，错误提示无法指出第几个字段。
        if not isinstance(raw_field, dict):  # 新增代码+Phase3HighLevelTools: 每个字段必须是对象；若没有这行代码，字符串或列表字段会导致隐晦错误。
            raise ValueError(f"fields 第 {index} 项必须是对象。")  # 新增代码+Phase3HighLevelTools: 明确指出坏字段序号；若没有这行代码，用户难以定位问题。
        text_value = raw_field.get("text")  # 新增代码+Phase3HighLevelTools: 读取普通文本输入；若没有这行代码，普通字段无法生成 browser_type。
        secret_env_var = _clean_text(raw_field.get("secret_env_var"))  # 新增代码+Phase3HighLevelTools: 读取敏感环境变量名；若没有这行代码，敏感字段无法生成 browser_type_secret。
        has_text = text_value is not None and str(text_value) != ""  # 新增代码+Phase3HighLevelTools: 判断是否提供普通文本；若没有这行代码，空字符串可能被当成有效输入。
        has_secret = bool(secret_env_var)  # 新增代码+Phase3HighLevelTools: 判断是否提供敏感变量；若没有这行代码，空变量名可能进入 secret 工具。
        if has_text == has_secret:  # 新增代码+Phase3HighLevelTools: 要求 text 和 secret_env_var 二选一；若没有这行代码，字段可能既泄露明文又走敏感路径。
            raise ValueError(f"fields 第 {index} 项必须且只能提供 text 或 secret_env_var。")  # 新增代码+Phase3HighLevelTools: 给出清楚字段级错误；若没有这行代码，坏输入会在底层才失败。
        step_arguments = _field_arguments(raw_field)  # 新增代码+Phase3HighLevelTools: 提取定位和行为参数；若没有这行代码，底层工具无法知道目标输入框。
        if has_secret:  # 新增代码+Phase3HighLevelTools: 敏感字段走 secret 工具；若没有这行代码，密码可能被当普通文本处理。
            step_arguments["secret_env_var"] = secret_env_var  # 新增代码+Phase3HighLevelTools: 只传环境变量名不传明文；若没有这行代码，底层 secret 工具无法读取值。
            plan.append({"tool_name": "browser_type_secret", "arguments": step_arguments})  # 新增代码+Phase3HighLevelTools: 加入敏感输入步骤；若没有这行代码，敏感字段不会被填写。
        else:  # 新增代码+Phase3HighLevelTools: 普通字段走普通输入工具；若没有这行代码，非敏感字段没有执行路径。
            step_arguments["text"] = str(text_value)  # 新增代码+Phase3HighLevelTools: 把普通文本转成字符串；若没有这行代码，数字输入等非字符串可能让底层不稳定。
            plan.append({"tool_name": "browser_type", "arguments": step_arguments})  # 新增代码+Phase3HighLevelTools: 加入普通输入步骤；若没有这行代码，普通字段不会被填写。
    submit_key = _submit_key(arguments)  # 新增代码+Phase3HighLevelTools: 解析可选提交动作；若没有这行代码，submit 参数会被忽略。
    if submit_key is not None:  # 新增代码+Phase3HighLevelTools: 只有请求提交时才追加按键；若没有这行代码，填表会总是按键。
        submit_arguments: dict[str, Any] = {"key": submit_key}  # 新增代码+Phase3HighLevelTools: 构造按键参数；若没有这行代码，browser_press_key 不知道要按什么。
        if "page_id" in arguments:  # 新增代码+Phase3HighLevelTools: 顶层 page_id 可用于提交动作；若没有这行代码，提交可能作用到默认页而不是指定页。
            submit_arguments["page_id"] = arguments["page_id"]  # 新增代码+Phase3HighLevelTools: 透传 page_id 给按键工具；若没有这行代码，跨页填表提交不稳定。
        plan.append({"tool_name": "browser_press_key", "arguments": submit_arguments})  # 新增代码+Phase3HighLevelTools: 追加提交按键步骤；若没有这行代码，submit=true 不会产生动作。
    return plan  # 新增代码+Phase3HighLevelTools: 返回完整有序计划；若没有这行代码，server 无法执行高层任务。
