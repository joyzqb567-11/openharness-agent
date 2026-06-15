"""LSP and REPL tool helpers extracted from LearningAgent."""  # 新增代码+AgentPySplitPhase11: 说明本文件承接 agent.py 里的 LSP 和 REPL 工具细节；若没有这行说明，代码小白很难知道这个模块为什么存在。

from __future__ import annotations  # 新增代码+AgentPySplitPhase11: 让类型注解延后解析，避免运行时过早寻找类型对象；若没有这行代码，部分类型提示可能在旧环境里提前报错。

import ast  # 新增代码+AgentPySplitPhase11: 使用 Python 标准 AST 解析源码结构；若没有这行代码，LSP 符号和诊断工具无法理解 Python 文件。
from pathlib import Path  # 新增代码+AgentPySplitPhase11: 使用 Path 表达文件路径；若没有这行代码，文件读取 helper 的返回类型和路径操作会不清楚。
from typing import Any  # 新增代码+AgentPySplitPhase11: 使用 Any 接收 LearningAgent 实例和灵活参数；若没有这行代码，新模块会被具体类导入牵出循环依赖风险。

try:  # 新增代码+AgentPySplitPhase11: 优先按包运行模式导入 ToolCall；若没有这行代码，python -m 运行时 REPL 子工具无法构造标准工具调用对象。
    from learning_agent.core.messages import ToolCall  # 新增代码+AgentPySplitPhase11: 从正式包路径导入工具调用数据结构；若没有这行代码，REPL 无法复用 agent 的工具执行入口。
except ModuleNotFoundError as error:  # 新增代码+AgentPySplitPhase11: 捕获直接运行脚本时包路径不存在的情况；若没有这行代码，bat 入口可能因为导入路径不同而失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.messages"}:  # 新增代码+AgentPySplitPhase11: 只允许路径缺失时 fallback；若没有这行代码，ToolCall 内部真实导入错误会被误吞。
        raise  # 新增代码+AgentPySplitPhase11: 重新抛出真正的内部导入错误；若没有这行代码，真实 bug 会被伪装成脚本模式兼容问题。
    from core.messages import ToolCall  # 新增代码+AgentPySplitPhase11: 脚本模式下从同目录 core 包导入 ToolCall；若没有这行代码，start_oauth_agent.bat 直接运行时 REPL 会找不到数据结构。

try:  # 修改代码+AgentPySplitPhase15B2: 包运行模式下导入不依赖 agent.py 的 max_chars 解析函数；若没有这行代码，REPL 输出截断仍会反向调用 agent.旧输出长度薄包装。
    from learning_agent.runtime.background_commands import parse_max_chars_value  # 修改代码+AgentPySplitPhase15B2: 复用统一输出长度边界；若没有这行代码，REPL 和后台命令可能出现不同截断规则。
except ModuleNotFoundError as error:  # 修改代码+AgentPySplitPhase15B2: 兼容 start_oauth_agent.bat 直接运行时没有 learning_agent 包名前缀；若没有这行代码，脚本模式下 LSP/REPL 工具可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.runtime", "learning_agent.runtime.background_commands"}:  # 修改代码+AgentPySplitPhase15B2: 只允许路径模式差异进入 fallback；若没有这行代码，runtime 内部真实 bug 会被误吞。
        raise  # 修改代码+AgentPySplitPhase15B2: 非路径问题必须继续抛出；若没有这行代码，真实导入问题会被伪装成脚本兼容问题。
    from runtime.background_commands import parse_max_chars_value  # 修改代码+AgentPySplitPhase15B2: 脚本模式下导入同一个公共解析函数；若没有这行代码，bat 入口执行 REPL 会找不到解析函数。

try:  # 修改代码+AgentPyCompatWrapperRemovalL2: 包运行模式下导入工具搜索 helper；若没有这行代码，LSP 符号数量限制还要绕回 agent.py 旧包装。
    import learning_agent.tools.search as search_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL2: 直接读取 tools.search 的 max_results 解析函数；若没有这行代码，删除旧包装后 lsp_symbols 会断开。
    import learning_agent.tools.atom_tools as atom_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL6: 导入统一 workspace 路径解析；若没有这行代码，删除 旧路径包装 后 LSP 文件读取会断开。
except ModuleNotFoundError as error:  # 修改代码+AgentPyCompatWrapperRemovalL2: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下 LSP helper 可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.search", "learning_agent.tools.atom_tools"}:  # 修改代码+AgentPyCompatWrapperRemovalL6: 允许 atom_tools 在脚本模式 fallback；若没有这行代码，bat 入口会把路径差异误判为真实导入错误。
        raise  # 修改代码+AgentPyCompatWrapperRemovalL2: 非路径错误继续抛出；若没有这行代码，真实 bug 会被伪装成脚本兼容问题。
    import tools.search as search_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL2: 脚本模式下导入同一个工具搜索 helper；若没有这行代码，bat 入口执行 LSP 工具会找不到数量限制函数。
    import tools.atom_tools as atom_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL6: 脚本模式下导入同一个路径安全模块；若没有这行代码，LSP 工具会找不到 workspace 边界实现。

def lsp_symbols(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+LSP工具: 执行 Python 文件符号读取工具；若省略: schema 暴露后仍没有实际符号读取能力
    loaded_file = lsp_python_file(agent, arguments, "lsp_symbols")  # 新增代码+LSP工具: 解析并读取工作区内 Python 文件；若省略: 符号工具会重复路径和文件校验逻辑
    if isinstance(loaded_file, str):  # 新增代码+LSP工具: 判断读取前置校验是否失败；若省略: 错误文本会被当成文件元组继续解析
        return loaded_file  # 新增代码+LSP工具: 把清楚的失败原因返回给模型；若省略: 模型不知道如何修正 path 参数
    source_path, source_text = loaded_file  # 新增代码+LSP工具: 拆出源码路径和文本；若省略: 后续 AST 解析拿不到输入
    symbols = lsp_python_symbols(agent, source_text, str(source_path), "lsp_symbols")  # 新增代码+LSP工具: 从源码中提取类、方法和函数符号；若省略: lsp_symbols 只能读文件不能理解结构
    if isinstance(symbols, str):  # 新增代码+LSP工具: 判断源码解析是否失败；若省略: 语法错误文本会被当成符号列表处理
        return symbols  # 新增代码+LSP工具: 返回语法解析失败原因；若省略: 模型看不到符号读取失败的行列信息
    max_results = search_tools_from_tools.tool_search_max_results(arguments.get("max_results"))  # 修改代码+AgentPyCompatWrapperRemovalL2: 直接复用 tools.search 的 1 到 20 结果数限制；若没有这行代码，删除 agent.py 旧包装后 lsp_symbols 会断开
    visible_symbols = symbols[:max_results]  # 新增代码+LSP工具: 截取本次返回的符号数量；若省略: max_results 参数不会生效
    relative_path = source_path.relative_to(agent.workspace).as_posix()  # 新增代码+LSP工具: 把绝对路径转成工作区相对路径；若省略: 输出会暴露更长本机绝对路径且不便阅读
    lines = [  # 新增代码+LSP工具: 准备结构化符号输出；若省略: 工具结果无法稳定被模型读取
        "lsp_symbols 成功：已读取 Python 文件符号。",  # 新增代码+LSP工具: 输出成功前缀；若省略: 调用方难以判断工具是否成功
        f"path={relative_path}",  # 新增代码+LSP工具: 输出被分析文件路径；若省略: 多文件排查时无法知道结果来自哪里
        f"symbol_count={len(symbols)}",  # 新增代码+LSP工具: 输出总符号数；若省略: 模型不知道是否发生截断
        f"returned_count={len(visible_symbols)}",  # 新增代码+LSP工具: 输出实际返回符号数；若省略: max_results 截断不透明
    ]  # 新增代码+LSP工具: 基础输出列表结束；若省略: 后续追加符号没有容器
    if visible_symbols:  # 新增代码+LSP工具: 如果存在可展示符号；若省略: 空列表和非空列表无法分支
        lines.append("符号：")  # 新增代码+LSP工具: 添加符号标题；若省略: 字段行和符号行语义不清楚
        lines.extend(lsp_symbol_line(agent, symbol) for symbol in visible_symbols)  # 新增代码+LSP工具: 格式化每个符号；若省略: 模型拿不到符号名称和行号
    else:  # 新增代码+LSP工具: 如果没有任何符号；若省略: 空文件会返回没有结尾说明的结果
        lines.append("符号：(无)")  # 新增代码+LSP工具: 明确说明没有符号；若省略: 模型可能误以为工具输出被截断
    return "\n".join(lines)  # 新增代码+LSP工具: 把符号结果列表合成最终文本；若省略: lsp_symbols 工具无法把结果交回模型。

def lsp_definition(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+LSP工具: 执行 Python 符号定义定位工具；若省略: schema 暴露后仍没有实际跳转定义能力
    symbol_name = str(arguments.get("symbol", "") or "").strip()  # 新增代码+LSP工具: 读取并清理目标符号名；若省略: 工具不知道要定位哪个定义
    if not symbol_name:  # 新增代码+LSP工具: 检查 symbol 是否为空；若省略: 空符号名会被当作合法搜索
        return "lsp_definition 失败：缺少非空 symbol 参数。"  # 新增代码+LSP工具: 返回清楚缺参错误；若省略: 模型难以补齐 symbol 参数
    loaded_file = lsp_python_file(agent, arguments, "lsp_definition")  # 新增代码+LSP工具: 解析并读取工作区内 Python 文件；若省略: 定义工具会重复路径和文件校验逻辑
    if isinstance(loaded_file, str):  # 新增代码+LSP工具: 判断读取前置校验是否失败；若省略: 错误文本会被当成文件元组继续解析
        return loaded_file  # 新增代码+LSP工具: 把清楚的失败原因返回给模型；若省略: 模型不知道如何修正 path 参数
    source_path, source_text = loaded_file  # 新增代码+LSP工具: 拆出源码路径和文本；若省略: 后续 AST 解析拿不到输入
    symbols = lsp_python_symbols(agent, source_text, str(source_path), "lsp_definition")  # 新增代码+LSP工具: 读取当前文件中的符号索引；若省略: 无法按名称查找定义
    if isinstance(symbols, str):  # 新增代码+LSP工具: 判断源码解析是否失败；若省略: 语法错误文本会被当成符号列表处理
        return symbols  # 新增代码+LSP工具: 返回语法解析失败原因；若省略: 模型看不到定义定位失败的行列信息
    matches = [symbol for symbol in symbols if str(symbol.get("name", "")) == symbol_name]  # 新增代码+LSP工具: 按符号名精确匹配定义；若省略: 工具无法筛出目标符号
    relative_path = source_path.relative_to(agent.workspace).as_posix()  # 新增代码+LSP工具: 把绝对路径转成工作区相对路径；若省略: 输出会暴露更长本机绝对路径且不便阅读
    lines = [  # 新增代码+LSP工具: 准备结构化定义输出；若省略: 工具结果无法稳定被模型读取
        "lsp_definition 成功：已定位 Python 符号定义。",  # 新增代码+LSP工具: 输出成功前缀；若省略: 调用方难以判断工具是否成功
        f"path={relative_path}",  # 新增代码+LSP工具: 输出被分析文件路径；若省略: 多文件排查时无法知道结果来自哪里
        f"symbol={symbol_name}",  # 新增代码+LSP工具: 输出目标符号名；若省略: 用户无法核对查找对象
        f"match_count={len(matches)}",  # 新增代码+LSP工具: 输出匹配数量；若省略: 模型不知道是否未找到或有多个定义
    ]  # 新增代码+LSP工具: 基础输出列表结束；若省略: 后续追加定义没有容器
    if matches:  # 新增代码+LSP工具: 如果找到了匹配定义；若省略: 找到和未找到无法分支
        lines.append("定义：")  # 新增代码+LSP工具: 添加定义标题；若省略: 字段行和定义行语义不清楚
        lines.extend(lsp_symbol_line(agent, symbol) for symbol in matches)  # 新增代码+LSP工具: 格式化每个匹配定义；若省略: 模型拿不到定义行号
    else:  # 新增代码+LSP工具: 如果没有找到匹配定义；若省略: 空结果会缺少明确说明
        lines.append("定义：(未找到)")  # 新增代码+LSP工具: 明确说明没有匹配；若省略: 模型可能误以为工具失败或输出截断
    return "\n".join(lines)  # 新增代码+LSP工具: 把定义定位结果列表合成最终文本；若省略: lsp_definition 工具无法把结果交回模型。

def lsp_diagnostics(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+LSP工具: 执行 Python 语法诊断工具；若省略: schema 暴露后仍没有实际诊断能力
    loaded_file = lsp_python_file(agent, arguments, "lsp_diagnostics")  # 新增代码+LSP工具: 解析并读取工作区内 Python 文件；若省略: 诊断工具会重复路径和文件校验逻辑
    if isinstance(loaded_file, str):  # 新增代码+LSP工具: 判断读取前置校验是否失败；若省略: 错误文本会被当成文件元组继续解析
        return loaded_file  # 新增代码+LSP工具: 把清楚的失败原因返回给模型；若省略: 模型不知道如何修正 path 参数
    source_path, source_text = loaded_file  # 新增代码+LSP工具: 拆出源码路径和文本；若省略: 后续语法解析拿不到输入
    relative_path = source_path.relative_to(agent.workspace).as_posix()  # 新增代码+LSP工具: 把绝对路径转成工作区相对路径；若省略: 输出会暴露更长本机绝对路径且不便阅读
    try:  # 新增代码+LSP工具: 使用 AST 解析触发 Python 语法检查；若省略: 诊断工具无法发现 SyntaxError
        ast.parse(source_text, filename=str(source_path))  # 新增代码+LSP工具: 解析源码但不执行源码；若省略: 诊断没有实际检查动作
    except SyntaxError as error:  # 新增代码+LSP工具: 捕获语法错误并转成 LSP 风格诊断；若省略: 语法错误会中断工具调用
        lines = [  # 新增代码+LSP工具: 准备语法错误诊断输出；若省略: 诊断结果无法稳定展示
            "lsp_diagnostics 成功：已读取 Python 语法诊断。",  # 新增代码+LSP工具: 输出成功前缀；若省略: 诊断工具语义会和工具失败混淆
            f"path={relative_path}",  # 新增代码+LSP工具: 输出被诊断文件路径；若省略: 多文件排查时无法知道结果来自哪里
            "diagnostic_count=1",  # 新增代码+LSP工具: 输出诊断数量；若省略: 模型不知道是否存在错误
            "诊断：",  # 新增代码+LSP工具: 添加诊断标题；若省略: 字段行和诊断行语义不清楚
            lsp_diagnostic_line(agent, error),  # 新增代码+LSP工具: 输出错误级别、行列和消息；若省略: 模型无法定位语法错误
        ]  # 新增代码+LSP工具: 语法错误诊断输出列表结束；若省略: 返回内容没有容器
        return "\n".join(lines)  # 新增代码+LSP工具: 返回语法错误诊断；若省略: 工具无法把诊断交回模型
    return "\n".join([  # 新增代码+LSP工具: 返回无诊断时的结构化结果；若省略: 语法正常文件没有明确成功输出
        "lsp_diagnostics 成功：已读取 Python 语法诊断。",  # 新增代码+LSP工具: 输出成功前缀；若省略: 调用方难以判断工具是否成功
        f"path={relative_path}",  # 新增代码+LSP工具: 输出被诊断文件路径；若省略: 多文件排查时无法知道结果来自哪里
        "diagnostic_count=0",  # 新增代码+LSP工具: 明确说明没有诊断；若省略: 模型可能以为空结果是工具失败
        "诊断：(无)",  # 新增代码+LSP工具: 用中文说明语法层面未发现错误；若省略: 用户看不到关闭语义
    ])  # 新增代码+LSP工具: 结束无诊断输出并返回文本；若省略: Python 语法正常时工具没有完整返回值。

def lsp_python_file(agent: Any, arguments: dict[str, Any], tool_name: str) -> tuple[Path, str] | str:  # 新增代码+LSP工具: 统一解析和读取 LSP Python 文件输入；若省略: 三个 LSP 工具会重复安全校验
    raw_path = str(arguments.get("path", "") or "").strip()  # 新增代码+LSP工具: 读取并清理 path 参数；若省略: 空白路径会进入文件系统解析
    if not raw_path:  # 新增代码+LSP工具: 检查 path 是否为空；若省略: 空路径可能误指向工作区根目录
        return f"{tool_name} 失败：缺少非空 path 参数。"  # 新增代码+LSP工具: 返回清楚缺参错误；若省略: 模型难以补齐 path 参数
    source_path = atom_tools_from_tools.resolve_workspace_path(agent, raw_path)  # 修改代码+AgentPyCompatWrapperRemovalL6: 直接通过 atom_tools 解析 LSP 文件路径；若没有这行代码，删除 旧路径包装 后 LSP 工具会断开或越界读取本机文件。
    if source_path is None:  # 新增代码+LSP工具: 判断路径是否越出工作区；若省略: None 会被当成 Path 使用并报底层错误
        return f"{tool_name} 失败：path 必须指向工作区内文件。"  # 新增代码+LSP工具: 返回工作区边界错误；若省略: 模型不知道要改成相对工作区路径
    if not source_path.exists():  # 新增代码+LSP工具: 检查目标文件是否存在；若省略: 读取不存在文件会抛异常
        return f"{tool_name} 失败：文件不存在：{raw_path}"  # 新增代码+LSP工具: 返回不存在文件错误；若省略: 模型难以修正路径拼写
    if not source_path.is_file():  # 新增代码+LSP工具: 检查目标是否为普通文件；若省略: 目录路径会被当作文件读取
        return f"{tool_name} 失败：path 必须指向文件而不是目录：{raw_path}"  # 新增代码+LSP工具: 返回目录误用错误；若省略: 模型不知道路径类型不对
    if source_path.suffix != ".py":  # 新增代码+LSP工具: 当前最小版只支持 Python 文件；若省略: 其他语言会进入 AST 解析并产生误导错误
        return f"{tool_name} 失败：当前 LSP 最小版只支持 .py 文件。"  # 新增代码+LSP工具: 明确语言范围；若省略: 模型可能误以为完整 LSP 已经支持所有语言
    try:  # 新增代码+LSP工具: 捕获读取文件时的系统错误；若省略: 权限或编码问题会中断工具调用
        source_text = source_path.read_text(encoding="utf-8", errors="replace")  # 新增代码+LSP工具: 读取 UTF-8 源码并替换坏字符；若省略: 文件内容无法进入 AST 解析
    except OSError as error:  # 新增代码+LSP工具: 捕获文件读取失败；若省略: 用户会看到底层 traceback
        return f"{tool_name} 失败：读取文件失败：{error}"  # 新增代码+LSP工具: 返回清楚读取错误；若省略: 模型不知道失败来自文件读取
    return source_path, source_text  # 新增代码+LSP工具: 返回已验证路径和源码文本；若省略: 上层 LSP 工具拿不到安全读取后的文件内容。

def lsp_python_symbols(agent: Any, source_text: str, source_name: str, tool_name: str) -> list[dict[str, Any]] | str:  # 新增代码+LSP工具: 用 AST 提取 Python 顶层类、方法和函数符号；若省略: 符号和定义工具没有共同索引
    try:  # 新增代码+LSP工具: 捕获源码语法错误；若省略: SyntaxError 会中断符号提取
        tree = ast.parse(source_text, filename=source_name)  # 新增代码+LSP工具: 解析源码为 AST 但不执行代码；若省略: 无法安全读取符号结构
    except SyntaxError as error:  # 新增代码+LSP工具: 捕获语法错误并返回可读失败；若省略: 模型看不到行列和错误消息
        return lsp_syntax_error_failure(agent, tool_name, error)  # 新增代码+LSP工具: 转成统一失败文本；若省略: 三个工具的语法错误格式会不一致
    symbols: list[dict[str, Any]] = []  # 新增代码+LSP工具: 准备保存提取到的符号；若省略: 后续无法累积结果
    for node in tree.body:  # 新增代码+LSP工具: 遍历模块顶层语句；若省略: 顶层类和函数不会被发现
        if isinstance(node, ast.ClassDef):  # 新增代码+LSP工具: 识别顶层类定义；若省略: 类符号不会出现在结果里
            symbols.append(lsp_symbol_dict(agent, "class", node.name, node, ""))  # 新增代码+LSP工具: 记录类名和行号；若省略: 模型无法定位类定义
            for child in node.body:  # 新增代码+LSP工具: 遍历类内部成员；若省略: 类方法不会被发现
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):  # 新增代码+LSP工具: 识别同步和异步方法；若省略: 方法符号不会出现在结果里
                    method_kind = "async_method" if isinstance(child, ast.AsyncFunctionDef) else "method"  # 新增代码+LSP工具: 区分异步方法和普通方法；若省略: async def 的语义会丢失
                    symbols.append(lsp_symbol_dict(agent, method_kind, child.name, child, node.name))  # 新增代码+LSP工具: 记录方法并附带所属类名；若省略: 模型难以区分方法归属
            continue  # 新增代码+LSP工具: 类节点处理完成后跳过函数分支；若省略: 类节点还会继续参与后续顶层函数判断
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):  # 新增代码+LSP工具: 识别顶层同步和异步函数；若省略: 函数符号不会出现在结果里
            function_kind = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"  # 新增代码+LSP工具: 区分异步函数和普通函数；若省略: async def 的语义会丢失
            symbols.append(lsp_symbol_dict(agent, function_kind, node.name, node, ""))  # 新增代码+LSP工具: 记录顶层函数名和行号；若省略: 模型无法定位函数定义
    return symbols  # 新增代码+LSP工具: 返回提取到的符号索引；若省略: 符号读取和定义跳转都没有可查询的数据。

def lsp_symbol_dict(agent: Any, kind: str, name: str, node: ast.AST, container: str) -> dict[str, Any]:  # 新增代码+LSP工具: 统一把 AST 节点转成符号字典；若省略: 类、方法和函数的字段格式容易不一致
    line_number = int(getattr(node, "lineno", 0) or 0)  # 新增代码+LSP工具: 读取符号起始行号；若省略: 模型无法跳到定义行
    end_line_number = int(getattr(node, "end_lineno", line_number) or line_number)  # 新增代码+LSP工具: 读取符号结束行号；若省略: 长函数范围不清楚
    return {  # 新增代码+LSP工具: 返回标准符号结构；若省略: 调用方无法稳定格式化符号
        "kind": kind,  # 新增代码+LSP工具: 保存符号类型；若省略: 模型无法区分类、方法和函数
        "name": name,  # 新增代码+LSP工具: 保存符号名称；若省略: 定义定位无法按名称匹配
        "line": line_number,  # 新增代码+LSP工具: 保存起始行号；若省略: 输出没有可跳转位置
        "end_line": end_line_number,  # 新增代码+LSP工具: 保存结束行号；若省略: 输出无法描述定义范围
        "container": container,  # 新增代码+LSP工具: 保存所属类名；若省略: 方法会和顶层函数混在一起
    }  # 新增代码+LSP工具: 结束符号字典结构；若省略: Python 语法无法闭合这个返回对象。

def lsp_symbol_line(agent: Any, symbol: dict[str, Any]) -> str:  # 新增代码+LSP工具: 把符号字典格式化成稳定单行文本；若省略: 输出格式会散落在多个工具里
    kind = str(symbol.get("kind", ""))  # 新增代码+LSP工具: 读取符号类型；若省略: 输出可能缺少 kind 字段
    name = str(symbol.get("name", ""))  # 新增代码+LSP工具: 读取符号名称；若省略: 输出可能缺少 name 字段
    line_number = int(symbol.get("line", 0) or 0)  # 新增代码+LSP工具: 读取符号起始行；若省略: 输出没有可跳转行号
    end_line_number = int(symbol.get("end_line", line_number) or line_number)  # 新增代码+LSP工具: 读取符号结束行；若省略: 输出无法展示定义范围
    container = str(symbol.get("container", "") or "")  # 新增代码+LSP工具: 读取符号容器类名；若省略: 方法归属无法显示
    base_line = f"kind={kind} name={name} line={line_number}"  # 新增代码+LSP工具: 生成符号基础字段；若省略: 模型无法稳定解析符号输出
    if container:  # 新增代码+LSP工具: 如果符号有所属类；若省略: 方法输出会缺少类名
        base_line = f"{base_line} container={container}"  # 新增代码+LSP工具: 追加容器类名且保持 line 后紧跟 container；若省略: 测试和模型难以识别方法归属
    if end_line_number and end_line_number != line_number:  # 新增代码+LSP工具: 只有多行定义才展示结束行；若省略: 单行符号也会产生噪音字段
        base_line = f"{base_line} end_line={end_line_number}"  # 新增代码+LSP工具: 追加结束行号；若省略: 多行定义范围不清楚
    return base_line  # 新增代码+LSP工具: 返回单行符号文本；若省略: 符号列表无法展示给模型和用户。

def lsp_syntax_error_failure(agent: Any, tool_name: str, error: SyntaxError) -> str:  # 新增代码+LSP工具: 把符号/定义解析失败转成统一错误文本；若省略: 语法错误失败格式会重复且不一致
    line_number = int(error.lineno or 0)  # 新增代码+LSP工具: 读取语法错误行号；若省略: 模型无法定位错误行
    column_number = int(error.offset or 0)  # 新增代码+LSP工具: 读取语法错误列号；若省略: 模型无法定位错误列
    message = str(error.msg or "语法错误")  # 新增代码+LSP工具: 读取语法错误消息；若省略: 用户看不到 Python 解析器原因
    return f"{tool_name} 失败：Python 语法解析失败。line={line_number} column={column_number} message={message}"  # 新增代码+LSP工具: 返回统一语法失败文本；若省略: 模型看不到失败行列和原因。

def lsp_diagnostic_line(agent: Any, error: SyntaxError) -> str:  # 新增代码+LSP工具: 把 SyntaxError 转成稳定诊断行；若省略: diagnostics 输出格式会和失败输出混杂
    line_number = int(error.lineno or 0)  # 新增代码+LSP工具: 读取诊断行号；若省略: 模型无法定位错误行
    column_number = int(error.offset or 0)  # 新增代码+LSP工具: 读取诊断列号；若省略: 模型无法定位错误列
    message = str(error.msg or "语法错误")  # 新增代码+LSP工具: 读取诊断消息；若省略: 用户看不到 Python 解析器原因
    return f"severity=error line={line_number} column={column_number} message={message}"  # 新增代码+LSP工具: 返回稳定诊断行；若省略: diagnostics 工具无法展示具体错误位置。

def repl(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+REPL工具: 执行安全白名单内的批量工具编排；若省略: repl schema 暴露后仍没有实际行为
    raw_calls = arguments.get("calls")  # 新增代码+REPL工具: 读取批量子调用数组；若省略: 工具无法知道要执行哪些步骤
    if not isinstance(raw_calls, list) or not raw_calls:  # 新增代码+REPL工具: 校验 calls 必须是非空数组；若省略: 空批次或错误类型会进入执行逻辑
        return "repl 失败：calls 必须是 1 到 5 个子调用对象。"  # 新增代码+REPL工具: 返回清楚的 calls 类型错误；若省略: 模型难以修正参数结构
    if len(raw_calls) > 5:  # 新增代码+REPL工具: 限制单次最多五个子调用；若省略: 批量输出可能撑爆上下文
        return "repl 失败：calls 最多 5 个子调用。"  # 新增代码+REPL工具: 返回数量上限错误；若省略: 模型不知道应该缩小批次
    allowed_tool_names = repl_allowed_tool_names(agent)  # 新增代码+REPL工具: 获取安全白名单工具集合；若省略: 无法拦截写入、命令和外部工具
    validated_calls: list[tuple[str, dict[str, Any]]] = []  # 新增代码+REPL工具: 准备保存校验后的子调用；若省略: 后续执行会重复解析原始结构
    for index, raw_call in enumerate(raw_calls, start=1):  # 新增代码+REPL工具: 逐个校验子调用并保留原始顺序；若省略: 无法定位哪一项参数错误
        if not isinstance(raw_call, dict):  # 新增代码+REPL工具: 每个子调用必须是对象；若省略: 字符串或数组会导致 .get 报错
            return f"repl 失败：第 {index} 个调用必须是对象。"  # 新增代码+REPL工具: 返回具体子调用类型错误；若省略: 模型不知道哪一项需要修正
        tool_name = str(raw_call.get("tool_name", "") or "").strip()  # 新增代码+REPL工具: 读取并清理子工具名；若省略: 空白工具名可能进入路由
        if not tool_name:  # 新增代码+REPL工具: 检查子工具名是否为空；若省略: 空工具名会变成未知工具
            return f"repl 失败：第 {index} 个调用缺少非空 tool_name。"  # 新增代码+REPL工具: 返回缺少工具名错误；若省略: 模型难以补齐子调用
        if tool_name not in allowed_tool_names:  # 新增代码+REPL工具: 拦截不在安全白名单内的工具；若省略: repl 可能执行写入、命令、MCP 或递归自身
            return f"repl 失败：第 {index} 个调用的 tool_name 不在安全白名单：{tool_name}"  # 新增代码+REPL工具: 返回白名单错误和具体工具名；若省略: 模型不知道哪个子工具被拒绝
        raw_arguments = raw_call.get("arguments", {})  # 新增代码+REPL工具: 读取子调用参数对象；若省略: 子工具无法收到 path/query 等入参
        if raw_arguments is None:  # 新增代码+REPL工具: 允许模型用 null 表示空参数；若省略: null 会被当成错误对象
            raw_arguments = {}  # 新增代码+REPL工具: 把 null 转成空字典；若省略: 后续 isinstance 校验会失败
        if not isinstance(raw_arguments, dict):  # 新增代码+REPL工具: 子调用参数必须是对象；若省略: 字符串参数会导致工具层混乱
            return f"repl 失败：第 {index} 个调用的 arguments 必须是对象。"  # 新增代码+REPL工具: 返回具体参数类型错误；若省略: 模型难以修正子调用参数
        validated_calls.append((tool_name, raw_arguments))  # 新增代码+REPL工具: 保存安全且结构正确的子调用；若省略: 后续没有可执行批次
    stop_on_error = repl_stop_on_error(agent, arguments.get("stop_on_error"))  # 新增代码+REPL工具: 解析失败即停策略；若省略: 子调用失败后的行为不明确
    max_output_chars = repl_max_output_chars(agent, arguments.get("max_output_chars"))  # 新增代码+REPL工具: 解析每个子调用输出长度上限；若省略: 长输出可能撑爆上下文
    lines = [  # 新增代码+REPL工具: 准备结构化 REPL 输出；若省略: 批量结果无法稳定阅读
        "repl 成功：已按顺序执行安全白名单内工具批次。",  # 新增代码+REPL工具: 输出成功前缀；若省略: 调用方难以判断 REPL 工具本身是否成功
        f"call_count={len(validated_calls)}",  # 新增代码+REPL工具: 输出子调用数量；若省略: 用户需要手动数结果段
        f"stop_on_error={str(stop_on_error).lower()}",  # 新增代码+REPL工具: 输出失败即停策略；若省略: 后续是否继续执行不透明
        f"max_output_chars={max_output_chars}",  # 新增代码+REPL工具: 输出每段截断上限；若省略: 长输出截断原因不清楚
        "调用结果：",  # 新增代码+REPL工具: 添加结果标题；若省略: 元信息和子调用输出容易混在一起
    ]  # 新增代码+REPL工具: 基础输出列表结束；若省略: 后续追加没有容器
    for index, (tool_name, child_arguments) in enumerate(validated_calls, start=1):  # 新增代码+REPL工具: 按原顺序执行每个子调用；若省略: REPL 不会实际批量执行
        child_output = agent._execute_tool(ToolCall(name=tool_name, arguments=child_arguments))  # 新增代码+REPL工具: 复用现有工具路由执行安全子工具；若省略: 会重复实现各工具逻辑
        child_failed = repl_child_failed(agent, child_output)  # 新增代码+REPL工具: 判断子调用输出是否表示失败；若省略: stop_on_error 无法生效
        lines.append(f"[{index}] tool_name={tool_name}")  # 新增代码+REPL工具: 输出子调用序号和工具名；若省略: 用户无法按顺序审计结果
        lines.append(f"status={'failed' if child_failed else 'ok'}")  # 新增代码+REPL工具: 输出子调用状态；若省略: 用户需要从正文猜是否失败
        lines.append(repl_truncate_output(agent, child_output, max_output_chars))  # 新增代码+REPL工具: 输出并按上限截断子调用结果；若省略: 模型拿不到证据或可能输出过长
        if child_failed and stop_on_error:  # 新增代码+REPL工具: 如果子调用失败且策略要求停止；若省略: 失败后仍会继续执行后续调用
            lines.append(f"repl 已停止：第 {index} 个子调用失败，stop_on_error=true。")  # 新增代码+REPL工具: 明确说明提前停止原因；若省略: 后续结果缺失会显得像输出截断
            break  # 新增代码+REPL工具: 停止执行剩余子调用；若省略: stop_on_error 参数不会生效
    return "\n".join(lines)  # 新增代码+REPL工具: 把批量子调用结果合成最终文本；若省略: repl 工具执行后没有可读输出。

def repl_allowed_tool_names(agent: Any) -> set[str]:  # 新增代码+REPL工具: 定义 REPL 可批量调用的安全工具白名单；若省略: REPL 无法保守限制副作用范围
    return {  # 新增代码+REPL工具: 返回只读、状态和符号类内置工具集合；若省略: 白名单没有实际内容
        "read_file",  # 新增代码+REPL工具: 允许读取工作区文本文件；若省略: REPL 无法批量做基础文件查看
        "todo_read",  # 新增代码+REPL工具: 允许读取任务清单状态；若省略: REPL 无法批量核对任务进度
        "read_background_command",  # 新增代码+REPL工具: 允许读取已启动后台命令状态和增量输出；若省略: REPL 无法批量收集运行状态
        "notebook_read",  # 新增代码+REPL工具: 允许读取 Notebook 摘要；若省略: REPL 无法批量查看 notebook cell
        "tool_search",  # 新增代码+REPL工具: 允许搜索当前可见工具；若省略: REPL 无法批量做工具发现
        "skill_list",  # 新增代码+REPL工具: 允许列出本地 skills；若省略: REPL 无法批量发现说明书
        "skill_load",  # 新增代码+REPL工具: 允许读取本地 skill 说明；若省略: REPL 无法批量加载安全本地规程
        "task_output",  # 新增代码+REPL工具: 允许读取子任务输出；若省略: REPL 无法批量查看子任务状态
        "task_list",  # 新增代码+REPL工具: 允许列出子任务状态；若省略: REPL 无法批量收集任务总览
        "task_get",  # 新增代码+REPL工具: 允许读取单个子任务详情；若省略: REPL 无法批量核对任务元信息
        "list_peers",  # 新增代码+REPL工具: 允许读取教学版 peer 总览；若省略: REPL 无法批量查看 team 状态
        "read_peer_messages",  # 新增代码+REPL工具: 允许读取 peer inbox；若省略: REPL 无法批量收集协作消息
        "lsp_symbols",  # 新增代码+REPL工具: 允许读取 Python 文件符号；若省略: REPL 无法批量做代码结构理解
        "lsp_definition",  # 新增代码+REPL工具: 允许定位 Python 符号定义；若省略: REPL 无法批量做定义跳转
        "lsp_diagnostics",  # 新增代码+REPL工具: 允许读取 Python 语法诊断；若省略: REPL 无法批量收集语法问题
        "cron_list",  # 新增代码+CronMonitor: 允许 REPL 批量读取定时任务记录列表；若省略: 模型无法把 Cron 状态查询纳入安全批量审计
    }  # 新增代码+REPL工具: 结束 REPL 安全白名单集合；若省略: Python 语法无法闭合这个集合。

def repl_stop_on_error(agent: Any, raw_value: Any) -> bool:  # 新增代码+REPL工具: 解析 REPL 子调用失败后是否停止；若省略: stop_on_error 容错逻辑会散落在主方法里
    if isinstance(raw_value, bool):  # 新增代码+REPL工具: 只有布尔值才尊重模型输入；若省略: 字符串 "false" 会被 bool() 误判为 True
        return raw_value  # 新增代码+REPL工具: 返回明确布尔输入；若省略: 模型无法关闭失败即停
    return True  # 新增代码+REPL工具: 默认失败即停，保持批量调用保守安全；若省略: 非布尔输入时 REPL 不知道是否继续执行。

def repl_max_output_chars(agent: Any, raw_value: Any) -> int:  # 新增代码+REPL工具: 解析每个子调用最大输出字符数；若省略: 输出截断策略会重复且不稳定
    parsed_value = parse_max_chars_value(raw_value)  # 修改代码+AgentPySplitPhase15B2: 直接使用公共解析函数，不再依赖 agent.py 薄包装；若没有这行代码，删除 `旧输出长度薄包装` 后 REPL 输出截断会断开。
    return min(parsed_value, 8000)  # 新增代码+REPL工具: 把单次输出上限压到 8000 字符以内；若省略: 子调用长输出可能撑爆上下文。

def repl_truncate_output(agent: Any, output: str, max_output_chars: int) -> str:  # 新增代码+REPL工具: 截断单个子调用输出；若省略: 长结果可能撑爆上下文
    if len(output) <= max_output_chars:  # 新增代码+REPL工具: 如果输出没有超过上限；若省略: 所有输出都会被无意义处理
        return output  # 新增代码+REPL工具: 原样返回短输出；若省略: 短输出可能被误截断
    return output[:max_output_chars] + "\n...[repl 子调用输出过长，已截断]..."  # 新增代码+REPL工具: 返回截断后的输出并说明已截断；若省略: 长输出没有安全收口。

def repl_child_failed(agent: Any, output: str) -> bool:  # 新增代码+REPL工具: 判断子调用文本是否表示失败；若省略: stop_on_error 无法根据工具结果停下
    first_line = output.splitlines()[0] if output.splitlines() else output  # 新增代码+REPL工具: 取第一行状态文本；若省略: 长输出中间的“失败”可能被误判
    return "失败" in first_line or first_line.startswith("未知工具") or first_line.startswith("用户拒绝")  # 新增代码+REPL工具: 用第一行判断子工具是否失败；若省略: stop_on_error 无法根据工具文本停止。


