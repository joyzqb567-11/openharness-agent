"""四原子工具真实执行模块。"""  # 修改代码+AgentPyPhaseGAtomTools: 把 read/write/edit/bash 从 agent.py 搬到独立工具模块；若没有这个文件，主类会继续承载原子工具细节。

from __future__ import annotations  # 修改代码+AgentPyPhaseGAtomTools: 延迟解析类型注解，避免脚本模式导入顺序影响工具模块；若没有这行代码，部分注解在旧环境下可能提前求值失败。

import json  # 新增代码+AgentPyPhaseGAtomTools: bash 桌面任务策略拒绝时需要输出结构化 JSON；若没有这行代码，策略详情无法用中文友好的 JSON 展示。
import os  # 新增代码+AgentPyPhaseGAtomTools: bash 需要按 Windows 或类 Unix 选择命令承载程序；若没有这行代码，跨平台命令执行路径无法判断。
import subprocess  # 新增代码+AgentPyPhaseGAtomTools: bash 原子工具需要启动真实 shell 子进程；若没有这行代码，命令工具只能有入口不能真正执行。
from pathlib import Path  # 新增代码+AgentPyPhaseGAtomTools: read/edit/bash 路径边界需要 Path 对象处理绝对路径和相对路径；若没有这行代码，工作区安全解析会变脆弱。
from typing import Any  # 新增代码+AgentPyPhaseGAtomTools: 这些工具接收通用 agent 对象和模型参数；若没有这行代码，类型说明不清楚。

try:  # 修改代码+AgentPyPhaseIDynamicGate: 包运行模式下导入本地文件工具和动态提示词门禁；若没有这行代码，read/write 的真实实现会缺少依赖。
    import learning_agent.prompts.dynamic_gate as dynamic_gate_from_prompts  # 修改代码+AgentPyPhaseIDynamicGate: 直接导入动态提示词 read 门禁运行时；若没有这行代码，read_atom 还要回调 agent.py 薄包装。
    import learning_agent.tools.local_file_tools as local_file_tools_from_tools  # 新增代码+AgentPyPhaseGAtomTools: 读取正式 local_file_tools 模块；若没有这行代码，python -m 运行时 write_atom 找不到安全写入实现。
except ModuleNotFoundError as error:  # 新增代码+AgentPyPhaseGAtomTools: 兼容 start_oauth_agent.bat 直接脚本模式下没有 learning_agent 包名前缀；若没有这行代码，真实终端入口可能启动失败。
    if error.name not in {"learning_agent", "learning_agent.prompts", "learning_agent.prompts.dynamic_gate", "learning_agent.tools", "learning_agent.tools.local_file_tools"}:  # 修改代码+AgentPyPhaseIDynamicGate: 只允许包路径差异进入 fallback；若没有这行代码，dynamic_gate 或 local_file_tools 内部真实 bug 会被误吞。
        raise  # 新增代码+AgentPyPhaseGAtomTools: 重新抛出非路径类导入错误；若没有这行代码，排查工具模块问题会很困难。
    import prompts.dynamic_gate as dynamic_gate_from_prompts  # 修改代码+AgentPyPhaseIDynamicGate: 脚本模式下直接导入动态提示词门禁运行时；若没有这行代码，bat 入口 read_atom 仍会依赖 agent.py 兼容包装。
    import tools.local_file_tools as local_file_tools_from_tools  # 新增代码+AgentPyPhaseGAtomTools: 脚本模式下从同级 tools 包导入写入实现；若没有这行代码，bat 入口调用 write 会找不到实现。


def clamped_int_argument(raw_value: Any, default: int, minimum: int, maximum: int) -> int:  # 新增代码+AgentPyPhaseGAtomTools: 函数段开始，解析并限制 read/bash 的整数参数；若没有这段函数，offset、limit、timeout 这些参数会分散重复实现。
    try:  # 新增代码+AgentPyPhaseGAtomTools: 捕获模型传入字符串、None 或错误类型的情况；若没有这行代码，坏参数会让工具直接抛异常。
        value = int(raw_value) if raw_value is not None else default  # 新增代码+AgentPyPhaseGAtomTools: 有值就尝试转整数，没有值就用默认值；若没有这行代码，可选参数缺省时没有稳定行为。
    except (TypeError, ValueError):  # 新增代码+AgentPyPhaseGAtomTools: 处理无法转成整数的参数；若没有这行代码，模型一次传错数字就会中断工具调用。
        value = default  # 新增代码+AgentPyPhaseGAtomTools: 非法值回退默认值；若没有这行代码，工具缺少容错能力。
    return max(minimum, min(value, maximum))  # 新增代码+AgentPyPhaseGAtomTools: 把整数限制在最小和最大值之间；若没有这行代码，负偏移或超大超时会造成不稳定行为。
# 新增代码+AgentPyPhaseGAtomTools: 函数段结束，clamped_int_argument 到此结束；若没有这个边界说明，用户不容易看出整数保护逻辑范围。


def resolve_workspace_path(agent: Any, raw_path: str) -> Path | None:  # 新增代码+AgentPyPhaseGAtomTools: 函数段开始，把模型路径限制在 workspace 内；若没有这段函数，read/edit/bash/write 可能越界访问用户磁盘。
    workspace = agent.workspace  # 新增代码+AgentPyPhaseGAtomTools: 读取当前 agent 的工作区根目录；若没有这行代码，路径解析不知道安全边界在哪里。
    normalized_raw_path = raw_path.strip().replace("\\", "/")  # 新增代码+AgentPyPhaseGAtomTools: 统一清理空白和 Windows 反斜杠；若没有这行代码，learning_agent\skills 写法无法触发兼容分支。
    path = Path(normalized_raw_path).expanduser()  # 新增代码+AgentPyPhaseGAtomTools: 用规范化后的文本构造路径并展开 ~；若没有这行代码，后续绝对路径和相对路径判断没有对象。
    if not path.is_absolute():  # 新增代码+AgentPyPhaseGAtomTools: 如果模型给的是相对路径；若没有这行代码，相对路径不会落到当前工作区下。
        normalized_lower_path = normalized_raw_path.rstrip("/").lower()  # 新增代码+WorkspacePathCwd: 去掉尾部斜杠后统一小写；若没有这行代码，cwd=learning_agent/ 这类写法无法识别为工作区根。
        if workspace.name.lower() == "learning_agent" and normalized_lower_path == "learning_agent":  # 新增代码+WorkspacePathCwd: 工作区本身已叫 learning_agent 时，把裸 learning_agent 当作当前工作区根；若没有这行代码，bash cwd 会误变成 learning_agent/learning_agent。
            path = workspace  # 新增代码+WorkspacePathCwd: 直接使用当前 workspace 根目录；若没有这行代码，真实终端长任务会在错误目录里读写文件。
        elif workspace.name.lower() == "learning_agent" and normalized_raw_path.lower().startswith("learning_agent/"):  # 修改代码+WorkspacePathCwd: 工作区已是包目录时接受项目根风格子路径；若没有这行代码，静态提示词里的 learning_agent/skills/tool_list.md 在 CLI 下会失败。
            path = workspace / normalized_raw_path[len("learning_agent/") :]  # 新增代码+AgentPyPhaseGAtomTools: 去掉多余的 learning_agent 前缀再拼到包目录；若没有这行代码，路径会错误变成 learning_agent/learning_agent/skills。
        else:  # 新增代码+AgentPyPhaseGAtomTools: 其他相对路径仍按原有工作区相对路径处理；若没有这行代码，普通文件读取路径会丢失默认分支。
            path = workspace / path  # 新增代码+AgentPyPhaseGAtomTools: 视为相对于工作区的路径；若没有这行代码，read/write/edit 会找不到相对文件。
    resolved = path.resolve()  # 新增代码+AgentPyPhaseGAtomTools: 解析成绝对路径并消除 ..；若没有这行代码，路径越界检查可能被绕过。
    try:  # 新增代码+AgentPyPhaseGAtomTools: 检查 resolved 是否位于 workspace 内；若没有这行代码，模型可能读取或写入工作区外文件。
        resolved.relative_to(workspace)  # 新增代码+AgentPyPhaseGAtomTools: 不在工作区内会抛 ValueError；若没有这行代码，安全边界没有实际判断。
    except ValueError:  # 新增代码+AgentPyPhaseGAtomTools: 捕获越界路径；若没有这行代码，越界会抛异常而不是返回可读失败。
        return None  # 新增代码+AgentPyPhaseGAtomTools: 返回 None 表示路径不安全；若没有这行代码，调用方无法统一处理越界。
    return resolved  # 新增代码+AgentPyPhaseGAtomTools: 返回安全绝对路径；若没有这行代码，工具无法继续读写目标文件。
# 新增代码+AgentPyPhaseGAtomTools: 函数段结束，resolve_workspace_path 到此结束；若没有这个边界说明，用户不容易看出路径安全边界范围。


def rewrite_tool_result_prefix(output: str, *, old_prefix: str, new_prefix: str) -> str:  # 修改代码+AgentPyPhaseGAtomTools: 把复用旧工具实现得到的结果前缀改成原子工具名；若没有这行代码，write 调用会看到 write_file 成功这类不一致文本。
    return output.replace(old_prefix, new_prefix, 1)  # 修改代码+AgentPyPhaseGAtomTools: 只替换第一处工具名前缀；若没有这行代码，正文里出现的同名文本也可能被误改。
# 修改代码+AgentPyPhaseGAtomTools: 函数段结束，rewrite_tool_result_prefix 到此结束；若没有这个边界说明，用户不容易看出它只负责结果文案转换。


def read_atom(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseGAtomTools: 函数段开始，实现 read 原子工具；若没有这段函数，首轮 read schema 只能被看见但无法执行。
    raw_path = str(arguments.get("path", "")).strip()  # 新增代码+AgentPyPhaseGAtomTools: 从参数读取并清理 path；若没有这行代码，工具不知道要读哪个文件。
    if not raw_path:  # 新增代码+AgentPyPhaseGAtomTools: 检查模型是否提供了路径；若没有这行代码，空路径会进入路径解析产生模糊错误。
        return "read 失败：缺少 path 参数。"  # 新增代码+AgentPyPhaseGAtomTools: 返回清楚缺参错误；若没有这行代码，模型难以修正下一次调用。
    path = resolve_workspace_path(agent, raw_path)  # 新增代码+AgentPyPhaseGAtomTools: 把相对路径安全解析到工作区内；若没有这行代码，read 可能越界读取任意文件。
    if path is None:  # 新增代码+AgentPyPhaseGAtomTools: 检查路径是否越过工作区边界；若没有这行代码，用户项目外文件可能被读取。
        return "read 失败：只能读取 learning_agent 工作区内的文件。"  # 新增代码+AgentPyPhaseGAtomTools: 返回安全边界错误；若没有这行代码，模型不知道失败原因。
    if not path.exists():  # 新增代码+AgentPyPhaseGAtomTools: 检查文件是否存在；若没有这行代码，后续读取会抛出 FileNotFoundError。
        return f"read 失败：文件不存在：{path}"  # 新增代码+AgentPyPhaseGAtomTools: 返回包含路径的不存在提示；若没有这行代码，模型无法定位错路径。
    if path.is_dir():  # 新增代码+AgentPyPhaseGAtomTools: 检查路径是否是目录；若没有这行代码，目录读取会抛出不清晰异常。
        return f"read 失败：不能把目录当文件读取：{path}"  # 新增代码+AgentPyPhaseGAtomTools: 返回目录错误；若没有这行代码，模型可能继续用 read 读取目录。
    gate_message = dynamic_gate_from_prompts.dynamic_prompt_read_gate(agent, path)  # 修改代码+AgentPyPhaseIDynamicGate: 直接调用动态提示词门禁模块；若没有这行代码，真实 read 路径还会依赖 agent.py 薄包装。
    if gate_message is not None:  # 新增代码+AgentPyPhaseGAtomTools: 如果门控发现缺少父层；若没有这行代码，失败提示不会返回给模型。
        return gate_message  # 新增代码+AgentPyPhaseGAtomTools: 返回清楚的按层读取建议；若没有这行代码，read 会继续把子规则塞进上下文。
    text = path.read_text(encoding="utf-8", errors="replace")  # 新增代码+AgentPyPhaseGAtomTools: 用 UTF-8 读取文本并替换坏字符；若没有这行代码，read 拿不到文件正文。
    dynamic_gate_from_prompts.remember_dynamic_prompt_read(agent, path)  # 修改代码+AgentPyPhaseIDynamicGate: 直接调用动态提示词读后记录模块；若没有这行代码，真实 read 路径还会依赖 agent.py 薄包装。
    offset = clamped_int_argument(arguments.get("offset"), 0, 0, max(len(text), 0))  # 新增代码+AgentPyPhaseGAtomTools: 解析读取起点并限制在文件长度内；若没有这行代码，大文件局部读取不可控。
    limit = clamped_int_argument(arguments.get("limit"), 8000, 1, 20000)  # 新增代码+AgentPyPhaseGAtomTools: 解析最多返回字符数；若没有这行代码，read 可能返回过长内容。
    selected_text = text[offset : offset + limit]  # 新增代码+AgentPyPhaseGAtomTools: 截取本次要返回的文本片段；若没有这行代码，offset/limit 参数不会生效。
    if offset + limit < len(text):  # 新增代码+AgentPyPhaseGAtomTools: 判断文件后面是否还有未返回内容；若没有这行代码，模型不知道读取结果被截断。
        return selected_text + f"\n...[read 截断：offset={offset} limit={limit} total_chars={len(text)}]..."  # 新增代码+AgentPyPhaseGAtomTools: 返回片段和截断提示；若没有这行代码，模型可能误把片段当全文。
    return selected_text  # 新增代码+AgentPyPhaseGAtomTools: 返回完整或尾段文本；若没有这行代码，read 工具没有成功输出。
# 新增代码+AgentPyPhaseGAtomTools: 函数段结束，read_atom 到此结束；若没有这个边界说明，用户不容易看出读取工具的完整范围。


def write_atom(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseGAtomTools: 函数段开始，实现 write 原子工具；若没有这段函数，首轮 write schema 只能被看见但无法执行。
    output = local_file_tools_from_tools.write_file(agent, arguments)  # 新增代码+AgentPyPhaseGAtomTools: 复用本地文件模块的安全写入和权限逻辑；若没有这行代码，write 会重复实现路径校验和权限确认。
    return rewrite_tool_result_prefix(output, old_prefix="write_file", new_prefix="write")  # 新增代码+AgentPyPhaseGAtomTools: 把 write_file 文案改成 write 文案；若没有这行代码，模型会看到与调用名不一致的结果。
# 新增代码+AgentPyPhaseGAtomTools: 函数段结束，write_atom 到此结束；若没有这个边界说明，用户不容易看出写入工具只是复用 local_file_tools。


def edit_atom(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseGAtomTools: 函数段开始，实现 edit 原子工具；若没有这段函数，首轮 edit schema 只能被看见但无法执行。
    raw_path = str(arguments.get("path", "")).strip()  # 新增代码+AgentPyPhaseGAtomTools: 从参数读取并清理 path；若没有这行代码，edit 不知道要改哪个文件。
    old_text = str(arguments.get("old_text", ""))  # 新增代码+AgentPyPhaseGAtomTools: 读取要匹配的旧文本；若没有这行代码，edit 无法定位修改位置。
    new_text = str(arguments.get("new_text", ""))  # 新增代码+AgentPyPhaseGAtomTools: 读取替换后的新文本；若没有这行代码，edit 无法写入目标内容。
    replace_all = bool(arguments.get("replace_all", False))  # 新增代码+AgentPyPhaseGAtomTools: 读取是否替换所有匹配；若没有这行代码，多处匹配无法由模型明确表达。
    if not raw_path:  # 新增代码+AgentPyPhaseGAtomTools: 检查路径是否为空；若没有这行代码，空路径会进入路径解析产生模糊错误。
        return "edit 失败：缺少 path 参数。"  # 新增代码+AgentPyPhaseGAtomTools: 返回清楚缺参错误；若没有这行代码，模型难以修正调用。
    if old_text == "":  # 新增代码+AgentPyPhaseGAtomTools: 检查旧文本是否为空；若没有这行代码，空字符串替换会在每个字符间插入新内容。
        return "edit 失败：old_text 不能为空。"  # 新增代码+AgentPyPhaseGAtomTools: 返回空旧文本错误；若没有这行代码，可能造成灾难性全文修改。
    path = resolve_workspace_path(agent, raw_path)  # 新增代码+AgentPyPhaseGAtomTools: 把相对路径安全解析到工作区内；若没有这行代码，edit 可能越界修改文件。
    if path is None:  # 新增代码+AgentPyPhaseGAtomTools: 检查路径是否越过工作区边界；若没有这行代码，用户项目外文件可能被修改。
        return "edit 失败：只能编辑 learning_agent 工作区内的文件。"  # 新增代码+AgentPyPhaseGAtomTools: 返回安全边界错误；若没有这行代码，模型不知道失败原因。
    if not path.exists():  # 新增代码+AgentPyPhaseGAtomTools: 检查文件是否存在；若没有这行代码，后续读取会抛出 FileNotFoundError。
        return f"edit 失败：文件不存在：{path}"  # 新增代码+AgentPyPhaseGAtomTools: 返回包含路径的不存在提示；若没有这行代码，模型无法定位错路径。
    if path.is_dir():  # 新增代码+AgentPyPhaseGAtomTools: 检查路径是否是目录；若没有这行代码，目录读取会抛出不清晰异常。
        return f"edit 失败：不能把目录当文件编辑：{path}"  # 新增代码+AgentPyPhaseGAtomTools: 返回目录错误；若没有这行代码，模型可能继续用 edit 编辑目录。
    text = path.read_text(encoding="utf-8", errors="replace")  # 新增代码+AgentPyPhaseGAtomTools: 读取当前文件正文；若没有这行代码，edit 无法判断旧文本是否存在。
    match_count = text.count(old_text)  # 新增代码+AgentPyPhaseGAtomTools: 统计旧文本匹配次数；若没有这行代码，无法保护默认唯一替换语义。
    if match_count == 0:  # 新增代码+AgentPyPhaseGAtomTools: 检查旧文本是否存在；若没有这行代码，替换失败会被误报成功。
        return "edit 失败：没有找到 old_text。"  # 新增代码+AgentPyPhaseGAtomTools: 返回未找到提示；若没有这行代码，模型不知道应重新读取文件确认原文。
    if match_count > 1 and not replace_all:  # 新增代码+AgentPyPhaseGAtomTools: 默认拒绝多处匹配；若没有这行代码，定点编辑可能误改多个位置。
        return f"edit 失败：old_text 出现 {match_count} 次；请提供更精确片段或设置 replace_all=true。"  # 新增代码+AgentPyPhaseGAtomTools: 返回多匹配修正建议；若没有这行代码，模型难以安全继续。
    action = f"编辑文件：{path}，替换次数：{match_count if replace_all else 1}"  # 新增代码+AgentPyPhaseGAtomTools: 准备权限确认说明；若没有这行代码，用户无法核对 edit 的副作用范围。
    if not agent.ask_permission(action):  # 新增代码+AgentPyPhaseGAtomTools: 请求用户确认编辑操作；若没有这行代码，edit 会绕过写入权限边界。
        return f"用户拒绝了操作：{action}"  # 新增代码+AgentPyPhaseGAtomTools: 返回用户拒绝结果；若没有这行代码，模型可能误以为编辑已经完成。
    updated_text = text.replace(old_text, new_text) if replace_all else text.replace(old_text, new_text, 1)  # 新增代码+AgentPyPhaseGAtomTools: 根据 replace_all 执行替换；若没有这行代码，edit 不会产生新文件内容。
    path.write_text(updated_text, encoding="utf-8")  # 新增代码+AgentPyPhaseGAtomTools: 把替换后的文本写回文件；若没有这行代码，修改只存在内存里。
    return f"edit 成功：已更新 {path}，替换次数：{match_count if replace_all else 1}"  # 新增代码+AgentPyPhaseGAtomTools: 返回成功摘要；若没有这行代码，模型无法确认编辑结果。
# 新增代码+AgentPyPhaseGAtomTools: 函数段结束，edit_atom 到此结束；若没有这个边界说明，用户不容易看出编辑工具的完整范围。


def bash_atom(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseGAtomTools: 函数段开始，实现 bash 原子工具并保留桌面任务脚本制品门禁；若没有这段函数，首轮 bash schema 只能被看见但无法执行。
    command = str(arguments.get("command", "")).strip()  # 新增代码+AgentPyPhaseGAtomTools: 从参数读取并清理命令文本；若没有这行代码，bash 不知道要执行什么命令。
    if not command:  # 新增代码+AgentPyPhaseGAtomTools: 检查命令是否为空；若没有这行代码，空命令会产生模糊 shell 行为。
        return "bash 失败：缺少 command 参数。"  # 新增代码+AgentPyPhaseGAtomTools: 返回清楚缺参错误；若没有这行代码，模型难以修正调用。
    desktop_task_context = getattr(agent, "desktop_task_context", {})  # 新增代码+AgentPyPhaseGAtomTools: 读取当前 agent 的桌面任务上下文；若没有这一行，轻量测试对象或旧实例无法被安全识别为 active/inactive。
    desktop_task_active = bool(desktop_task_context.get("active", False)) if isinstance(desktop_task_context, dict) else False  # 新增代码+AgentPyPhaseGAtomTools: 只从字典上下文读取 active 布尔值；若没有这一行，异常上下文形状可能让 bash 工具崩溃。
    if desktop_task_active:  # 新增代码+AgentPyPhaseGAtomTools: 只在桌面任务激活时启用命令策略；若没有这一行，普通开发命令也会承担额外拦截逻辑。
        try:  # 新增代码+AgentPyPhaseGAtomTools: 优先按包运行模式导入策略函数；若没有这一行，start_oauth_agent.bat 和 unittest 的导入环境无法兼容处理。
            from learning_agent.computer_use_mcp_v2.windows_runtime.desktop_task_policy import evaluate_desktop_bash_command  # 新增代码+AgentPyPhaseGAtomTools: 导入桌面任务 bash 策略函数；若没有这一行，bash_atom 无法在权限请求前识别脚本最终制品路线。
        except ModuleNotFoundError as error:  # 新增代码+AgentPyPhaseGAtomTools: 兼容直接脚本运行时 learning_agent 包路径不可用的情况；若没有这一行，脚本模式可能因为包名前缀失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.desktop_task_policy"}:  # 新增代码+AgentPyPhaseGAtomTools: 只对目标包路径缺失做 fallback；若没有这一行，策略模块内部真实导入错误会被误吞。
                raise  # 新增代码+AgentPyPhaseGAtomTools: 重新抛出非目标导入错误；若没有这一行，排查策略模块内部 bug 会很困难。
            from computer_use_mcp_v2.windows_runtime.desktop_task_policy import evaluate_desktop_bash_command  # 新增代码+AgentPyPhaseGAtomTools: 脚本模式下从本地 computer_use 包导入策略函数；若没有这一行，bat 入口可能无法加载 Task 3 策略。
        desktop_policy_result = evaluate_desktop_bash_command(command=command, desktop_task_active=desktop_task_active)  # 新增代码+AgentPyPhaseGAtomTools: 在 cwd 解析、权限请求和执行命令前评估策略；若没有这一行，危险命令会继续走到真实 shell 流程。
        if not bool(desktop_policy_result.get("allowed", False)):  # 新增代码+AgentPyPhaseGAtomTools: 检查策略是否拒绝当前命令；若没有这一行，命中禁止脚本制品路线也不会被拦住。
            desktop_policy_text = json.dumps(desktop_policy_result, ensure_ascii=False, indent=2)  # 新增代码+AgentPyPhaseGAtomTools: 把结构化策略结果转成中文友好的 JSON；若没有这一行，拒绝文本缺少可复盘细节。
            return f"bash 拒绝：{desktop_policy_result.get('decision', 'desktop_task_requires_gui_route')}\n原因：{desktop_policy_result.get('reason', '')}\n策略详情：{desktop_policy_text}"  # 新增代码+AgentPyPhaseGAtomTools: 直接返回清晰拒绝，不请求权限也不执行命令；若没有这一行，脚本生成最终图片制品路线仍可能进入真实终端。
    raw_cwd = str(arguments.get("cwd", "") or "").strip()  # 新增代码+AgentPyPhaseGAtomTools: 读取可选工作目录；若没有这行代码，模型无法指定子目录执行命令。
    cwd_path = resolve_workspace_path(agent, raw_cwd) if raw_cwd else agent.workspace  # 新增代码+AgentPyPhaseGAtomTools: 将 cwd 限制在工作区内或默认根目录；若没有这行代码，命令可能在未知目录执行。
    if cwd_path is None:  # 新增代码+AgentPyPhaseGAtomTools: 检查 cwd 是否越界；若没有这行代码，bash 可能在工作区外执行命令。
        return "bash 失败：cwd 必须位于 learning_agent 工作区内。"  # 新增代码+AgentPyPhaseGAtomTools: 返回安全边界错误；若没有这行代码，模型不知道为什么命令没执行。
    if not cwd_path.exists() or not cwd_path.is_dir():  # 新增代码+AgentPyPhaseGAtomTools: 检查执行目录是否存在且为目录；若没有这行代码，subprocess 会抛出不清晰异常。
        return f"bash 失败：cwd 不存在或不是目录：{cwd_path}"  # 新增代码+AgentPyPhaseGAtomTools: 返回清楚 cwd 错误；若没有这行代码，模型无法修正路径。
    timeout_seconds = clamped_int_argument(arguments.get("timeout_seconds"), 60, 1, 300)  # 新增代码+AgentPyPhaseGAtomTools: 解析命令超时秒数；若没有这行代码，长命令可能无限等待。
    max_output_chars = clamped_int_argument(arguments.get("max_output_chars"), 8000, 1000, 20000)  # 新增代码+AgentPyPhaseGAtomTools: 解析最大输出字符数；若没有这行代码，命令输出可能撑爆上下文。
    action = f"执行命令：{command}\n工作目录：{cwd_path}"  # 新增代码+AgentPyPhaseGAtomTools: 准备权限确认说明；若没有这行代码，用户无法核对命令和执行目录。
    if not agent.ask_permission(action):  # 新增代码+AgentPyPhaseGAtomTools: 请求用户确认命令执行；若没有这行代码，bash 会绕过命令权限边界。
        return f"用户拒绝了操作：{action}"  # 新增代码+AgentPyPhaseGAtomTools: 返回用户拒绝结果；若没有这行代码，模型可能误以为命令已经执行。
    command_args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command] if os.name == "nt" else ["bash", "-lc", command]  # 新增代码+AgentPyPhaseGAtomTools: 根据系统选择命令承载程序；若没有这行代码，Windows 和类 Unix 环境无法统一执行 bash 原子工具。
    try:  # 新增代码+AgentPyPhaseGAtomTools: 捕获命令超时、shell 缺失或执行异常；若没有这行代码，bash 工具失败会冒出 Python traceback。
        result = subprocess.run(command_args, cwd=cwd_path, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_seconds)  # 新增代码+AgentPyPhaseGAtomTools: 执行命令并捕获 stdout/stderr；若没有这行代码，bash 不会真正运行命令。
    except subprocess.TimeoutExpired as error:  # 新增代码+AgentPyPhaseGAtomTools: 处理命令超过 timeout 的情况；若没有这行代码，超时命令会中断工具循环。
        stdout_text = (error.stdout or "") if isinstance(error.stdout, str) else ""  # 新增代码+AgentPyPhaseGAtomTools: 提取超时前 stdout 文本；若没有这行代码，用户看不到命令已产生的部分输出。
        stderr_text = (error.stderr or "") if isinstance(error.stderr, str) else ""  # 新增代码+AgentPyPhaseGAtomTools: 提取超时前 stderr 文本；若没有这行代码，用户看不到命令已产生的错误输出。
        combined_text = f"bash 失败：命令超过 {timeout_seconds} 秒已停止。\nstdout:\n{stdout_text}\nstderr:\n{stderr_text}"  # 新增代码+AgentPyPhaseGAtomTools: 构造超时结果；若没有这行代码，模型不知道命令为何没有完成。
        return combined_text[:max_output_chars]  # 新增代码+AgentPyPhaseGAtomTools: 截断超时输出；若没有这行代码，部分输出仍可能过长。
    except OSError as error:  # 新增代码+AgentPyPhaseGAtomTools: 处理 shell 程序缺失或启动失败；若没有这行代码，环境问题会变成 traceback。
        return f"bash 失败：无法启动命令执行器：{error}"  # 新增代码+AgentPyPhaseGAtomTools: 返回清楚环境错误；若没有这行代码，用户不知道是 shell 不可用。
    combined_text = f"bash 成功：exit_code={result.returncode}\nstdout:\n{result.stdout or ''}\nstderr:\n{result.stderr or ''}"  # 新增代码+AgentPyPhaseGAtomTools: 合并退出码和输出；若没有这行代码，模型无法根据命令结果继续推理。
    if len(combined_text) > max_output_chars:  # 新增代码+AgentPyPhaseGAtomTools: 判断命令输出是否超过返回上限；若没有这行代码，长输出会撑爆上下文。
        return combined_text[:max_output_chars] + f"\n...[bash 输出过长，已截断，原始字符数={len(combined_text)}]..."  # 新增代码+AgentPyPhaseGAtomTools: 返回截断输出和原始长度；若没有这行代码，模型会误以为看到了完整输出。
    return combined_text  # 新增代码+AgentPyPhaseGAtomTools: 返回完整命令结果；若没有这行代码，bash 工具没有成功输出。
# 新增代码+AgentPyPhaseGAtomTools: 函数段结束，bash_atom 到此结束；若没有这个边界说明，用户不容易看出命令工具的完整范围。
