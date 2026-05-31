"""权限提示文本解析 helper，用于生成可审计的权限事件 payload。"""  # 新增代码+ObservabilitySplit: 说明本模块负责权限事件结构化；若没有这行代码，权限排查仍要翻主入口文件。
from __future__ import annotations  # 新增代码+ObservabilitySplit: 允许类型注解延迟解析；若没有这行代码，类型提示在部分运行顺序下可能提前求值。

import json  # 新增代码+ObservabilitySplit: 解析权限提示里的 JSON 参数；若没有这行代码，URL 等参数只能靠字符串猜测。
from typing import Any  # 新增代码+ObservabilitySplit: 标注通用参数字典类型；若没有这行代码，payload 结构不清楚。


def permission_line_value(lines: list[str], prefix: str) -> str:  # 新增代码+ObservabilitySplit: 从权限提示行里提取指定前缀的值；若没有这行代码，工具名和风险等级会重复手写解析。
    for line in lines:  # 新增代码+ObservabilitySplit: 遍历权限提示的每一行；若没有这行代码，函数无法找到目标字段。
        if line.startswith(prefix):  # 新增代码+ObservabilitySplit: 判断当前行是否是目标字段；若没有这行代码，所有字段都会被忽略。
            return line[len(prefix) :].strip()  # 新增代码+ObservabilitySplit: 返回前缀后的干净文本；若没有这行代码，payload 会带多余前缀和空格。
    return ""  # 新增代码+ObservabilitySplit: 找不到时返回空字符串；若没有这行代码，缺字段提示会抛异常而不是保持兼容。


def permission_arguments_text(lines: list[str]) -> str:  # 新增代码+ObservabilitySplit: 提取“参数：”后的 JSON 文本；若没有这行代码，多行参数会被截断。
    for index, line in enumerate(lines):  # 新增代码+ObservabilitySplit: 带序号遍历每一行；若没有这行代码，无法收集参数行之后的内容。
        if line.startswith("参数："):  # 新增代码+ObservabilitySplit: 定位参数起始行；若没有这行代码，函数不知道 JSON 从哪里开始。
            first_line = line[len("参数：") :].strip()  # 新增代码+ObservabilitySplit: 取出冒号后的第一段内容；若没有这行代码，JSON 文本会保留中文前缀。
            remaining_lines = [raw_line.rstrip() for raw_line in lines[index + 1 :]]  # 新增代码+ObservabilitySplit: 收集参数行之后的多行文本；若没有这行代码，格式化 JSON 会缺后半段。
            return "\n".join([first_line] + remaining_lines).strip()  # 新增代码+ObservabilitySplit: 合并为完整参数文本；若没有这行代码，controller 拿不到完整参数对象。
    return ""  # 新增代码+ObservabilitySplit: 没有参数行时返回空字符串；若没有这行代码，非工具权限会触发解析异常。


def parse_permission_arguments(argument_text: str) -> dict[str, Any]:  # 新增代码+ObservabilitySplit: 把权限参数 JSON 转成字典；若没有这行代码，URL 前缀白名单无法检查真实参数。
    if not argument_text:  # 新增代码+ObservabilitySplit: 没有参数文本时直接返回空字典；若没有这行代码，json.loads 会对空字符串报错。
        return {}  # 新增代码+ObservabilitySplit: 用空字典表达无参数；若没有这行代码，payload.arguments 类型不稳定。
    try:  # 新增代码+ObservabilitySplit: 捕获格式化异常；若没有这行代码，一次坏权限文本会中断整个 agent。
        parsed_arguments = json.loads(argument_text)  # 新增代码+ObservabilitySplit: 使用标准 JSON 解析参数；若没有这行代码，布尔值和数字会退化成字符串。
    except json.JSONDecodeError:  # 新增代码+ObservabilitySplit: 处理参数文本不是合法 JSON 的情况；若没有这行代码，异常会冒泡到终端交互。
        return {}  # 新增代码+ObservabilitySplit: 解析失败时保守返回空字典；若没有这行代码，controller 可能拿到半坏结构。
    if isinstance(parsed_arguments, dict):  # 新增代码+ObservabilitySplit: 只接受对象参数；若没有这行代码，数组或字符串会污染 payload 形状。
        return parsed_arguments  # 新增代码+ObservabilitySplit: 返回解析后的参数字典；若没有这行代码，结构化白名单没有参数可用。
    return {}  # 新增代码+ObservabilitySplit: 非对象参数统一退回空字典；若没有这行代码，后续读取 URL 等字段可能失败。


def build_permission_event_payload(action: str) -> dict[str, Any]:  # 新增代码+ObservabilitySplit: 将人类可读权限文本转成可审计 payload；若没有这行代码，外部控制器只能靠 contains 判断权限。
    payload: dict[str, Any] = {"action": action, "permission_kind": "generic", "arguments": {}}  # 新增代码+ObservabilitySplit: 初始化兼容旧字段和默认类型；若没有这行代码，旧控制器和新结构化字段无法同时存在。
    action_lines = action.strip().splitlines()  # 新增代码+ObservabilitySplit: 把权限文本拆成行；若没有这行代码，工具名、风险和参数难以分别提取。
    if action.strip().startswith("调用 MCP 工具："):  # 新增代码+ObservabilitySplit: 识别 MCP 工具调用权限；若没有这行代码，browser_open 等工具无法进入结构化审计。
        payload["permission_kind"] = "mcp_tool"  # 新增代码+ObservabilitySplit: 标记本事件是 MCP 工具权限；若没有这行代码，controller 无法区分工具调用和启动 server。
        payload["tool_name"] = permission_line_value(action_lines, "调用 MCP 工具：")  # 新增代码+ObservabilitySplit: 提取 MCP 工具名；若没有这行代码，allow_tool_names 无法精确匹配。
        payload["risk_level"] = permission_line_value(action_lines, "风险等级：")  # 新增代码+ObservabilitySplit: 提取风险等级；若没有这行代码，result.json 缺少风险分类。
        payload["risk_summary"] = permission_line_value(action_lines, "风险说明：")  # 新增代码+ObservabilitySplit: 提取风险说明；若没有这行代码，审计记录缺少为什么有风险。
        payload["arguments"] = parse_permission_arguments(permission_arguments_text(action_lines))  # 新增代码+ObservabilitySplit: 解析工具参数；若没有这行代码，URL 前缀策略不能检查真实 URL。
    elif action.strip().startswith("启动 MCP server："):  # 新增代码+ObservabilitySplit: 识别 MCP server 启动权限；若没有这行代码，启动阶段无法结构化标记权限类型。
        payload["permission_kind"] = "mcp_server_start"  # 新增代码+ObservabilitySplit: 标记本事件是 MCP server 启动；若没有这行代码，controller 只能从中文 action 猜阶段。
        server_text = action.strip()[len("启动 MCP server：") :]  # 新增代码+ObservabilitySplit: 提取 server 名文本；若没有这行代码，审计记录无法列出要启动哪些 server。
        payload["server_names"] = [name.strip() for name in server_text.split(",") if name.strip()]  # 新增代码+ObservabilitySplit: 把逗号分隔 server 名变成列表；若没有这行代码，后续分析还要重新拆字符串。
    return payload  # 新增代码+ObservabilitySplit: 返回统一 payload；若没有这行代码，权限函数拿不到结构化事件内容。
