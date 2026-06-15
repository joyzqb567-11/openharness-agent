"""Notebook 读取和编辑工具。"""  # 新增代码+AgentPySplitPhase12: 说明本模块承接 .ipynb 工具逻辑；若没有这行代码，用户打开文件时不容易判断模块职责。

from __future__ import annotations  # 新增代码+AgentPySplitPhase12: 让类型注解延迟解析；若没有这行代码，复杂注解在部分运行方式下更容易提前求值出错。

import json  # 新增代码+AgentPySplitPhase12: Notebook 本质是 JSON 文件，读取和写回都需要 json；若没有这行代码，.ipynb 无法解析和保存。
from pathlib import Path  # 新增代码+AgentPySplitPhase12: load_notebook 返回安全解析后的 Path；若没有这行代码，类型边界不清楚。
from typing import Any  # 新增代码+AgentPySplitPhase12: 用 Any 表示传入的 agent 上下文和 notebook cell 数据；若没有这行代码，新模块会反向导入 agent.py。

try:  # 修改代码+AgentPySplitPhase15B2: 包运行模式下导入不依赖 agent.py 的 max_chars 解析函数；若没有这行代码，Notebook 读取仍要反向依赖 agent.旧输出长度薄包装。
    from learning_agent.runtime.background_commands import parse_max_chars_value  # 修改代码+AgentPySplitPhase15B2: 复用 runtime 层统一截断规则；若没有这行代码，Notebook 输出长度和后台命令规则可能分叉。
    import learning_agent.tools.atom_tools as atom_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL6: 导入统一 workspace 路径解析；若没有这行代码，删除 旧路径包装 后 notebook 工具路径边界会断开。
except ModuleNotFoundError as error:  # 修改代码+AgentPySplitPhase15B2: 兼容 start_oauth_agent.bat 直接运行时没有 learning_agent 包名前缀；若没有这行代码，脚本模式下 Notebook 工具可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.runtime", "learning_agent.runtime.background_commands", "learning_agent.tools", "learning_agent.tools.atom_tools"}:  # 修改代码+AgentPyCompatWrapperRemovalL6: 允许 atom_tools 在脚本模式 fallback；若没有这行代码，bat 入口会把路径差异误判为真实导入错误。
        raise  # 修改代码+AgentPySplitPhase15B2: 非路径问题必须继续抛出；若没有这行代码，真实导入问题会被伪装成脚本兼容问题。
    from runtime.background_commands import parse_max_chars_value  # 修改代码+AgentPySplitPhase15B2: 脚本模式下导入同一个公共解析函数；若没有这行代码，bat 入口执行 notebook_read 会找不到解析函数。
    import tools.atom_tools as atom_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL6: 脚本模式下导入同一个路径安全模块；若没有这行代码，notebook_read/notebook_edit 会找不到 workspace 边界实现。


def notebook_read(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase12: 函数段开始，读取 notebook 概览或指定 cell；若没有这段代码，agent.py 的 _notebook_read 薄包装没有真实实现。
    notebook_result = load_notebook(agent, arguments.get("path"), "notebook_read")  # 新增代码+AgentPySplitPhase12: 统一加载并校验 notebook 文件；若没有这行代码，路径和 JSON 校验会重复且容易不一致。
    if isinstance(notebook_result, str):  # 新增代码+AgentPySplitPhase12: 判断加载函数是否返回错误文本；若没有这行代码，后续会把错误字符串当元组使用。
        return notebook_result  # 新增代码+AgentPySplitPhase12: 直接返回可读错误；若没有这行代码，模型无法知道读取失败原因。
    path, payload = notebook_result  # 新增代码+AgentPySplitPhase12: 拆出安全路径和 notebook JSON；若没有这行代码，后续无法访问文件和内容。
    cells = payload.get("cells")  # 新增代码+AgentPySplitPhase12: 读取 notebook 的 cells 字段；若没有这行代码，工具不知道有哪些 cell 可展示。
    if not isinstance(cells, list):  # 新增代码+AgentPySplitPhase12: 校验 cells 必须是数组；若没有这行代码，畸形 notebook 会导致遍历异常。
        return "notebook_read 失败：notebook JSON 中的 cells 必须是数组。"  # 新增代码+AgentPySplitPhase12: 返回结构错误；若没有这行代码，模型无法理解文件格式问题。
    max_chars = parse_max_chars_value(arguments.get("max_chars"))  # 修改代码+AgentPySplitPhase15B2: 直接使用公共解析函数，不再依赖 agent.py 薄包装；若没有这行代码，删除 `旧输出长度薄包装` 后 notebook_read 会断开。
    selected_cells_result = select_notebook_cells(agent, cells, arguments.get("cell_index"), "notebook_read")  # 新增代码+AgentPySplitPhase12: 根据可选 cell_index 选择展示范围；若没有这行代码，指定单 cell 的读取需求无法处理。
    if isinstance(selected_cells_result, str):  # 新增代码+AgentPySplitPhase12: 判断 cell_index 校验是否失败；若没有这行代码，错误文本会被当列表遍历。
        return selected_cells_result  # 新增代码+AgentPySplitPhase12: 返回索引错误给模型；若没有这行代码，模型无法修正参数。
    lines = [f"notebook_read 成功：{path}", f"nbformat: {payload.get('nbformat', '?')}.{payload.get('nbformat_minor', '?')}", f"cells: {len(cells)}"]  # 新增代码+AgentPySplitPhase12: 准备输出文件、版本和 cell 数量；若没有这行代码，模型缺少 notebook 总览信息。
    for cell_index, cell in selected_cells_result:  # 新增代码+AgentPySplitPhase12: 遍历要展示的 cell；若没有这行代码，工具不会输出任何 cell 内容。
        if not isinstance(cell, dict):  # 新增代码+AgentPySplitPhase12: 防御畸形 cell 不是对象的情况；若没有这行代码，后续 .get 会在非字典上报错。
            lines.append(f"cell {cell_index}: 非对象 cell，无法解析。")  # 新增代码+AgentPySplitPhase12: 把畸形 cell 报告给模型；若没有这行代码，模型不知道哪个 cell 有问题。
            continue  # 新增代码+AgentPySplitPhase12: 跳过坏 cell 并继续其他 cell；若没有这行代码，单个坏 cell 会阻断整个读取。
        cell_type = str(cell.get("cell_type", "unknown"))  # 新增代码+AgentPySplitPhase12: 读取 cell 类型；若没有这行代码，模型不知道这是 code 还是 markdown。
        source_text = notebook_source_to_text(agent, cell.get("source", ""))  # 新增代码+AgentPySplitPhase12: 把 source 字符串或行数组统一成文本；若没有这行代码，list source 会显示得很难读。
        preview = source_text.strip() or "(空 cell)"  # 新增代码+AgentPySplitPhase12: 生成可读预览并处理空 cell；若没有这行代码，空 cell 会显示成空白。
        lines.append(f"cell {cell_index}: type={cell_type}, source_chars={len(source_text)}")  # 新增代码+AgentPySplitPhase12: 输出 cell 索引、类型和长度；若没有这行代码，模型无法精确引用要编辑的 cell。
        lines.append(preview)  # 新增代码+AgentPySplitPhase12: 输出 cell 内容预览；若没有这行代码，读取工具只能看到结构看不到内容。
    output = "\n".join(lines)  # 新增代码+AgentPySplitPhase12: 合并多行输出；若没有这行代码，返回值无法一次交给模型。
    if len(output) > max_chars:  # 新增代码+AgentPySplitPhase12: 检查输出是否超过长度限制；若没有这行代码，大 notebook 可能挤爆模型上下文。
        return output[:max_chars] + "\n...[notebook 内容过长，已截断]..."  # 新增代码+AgentPySplitPhase12: 返回截断输出并提示；若没有这行代码，模型会误以为看到完整内容。
    return output  # 新增代码+AgentPySplitPhase12: 返回完整 notebook 读取结果；若没有这行代码，工具调用没有结果。
# 新增代码+AgentPySplitPhase12: 函数段结束，notebook_read 到此结束；若没有这个边界说明，用户不容易看出 Notebook 读取逻辑已经迁到 tools 层。


def notebook_edit(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase12: 函数段开始，替换指定 notebook cell 的 source；若没有这段代码，agent.py 的 _notebook_edit 薄包装没有真实实现。
    if arguments.get("source") is None:  # 新增代码+AgentPySplitPhase12: 检查是否提供新 source；若没有这行代码，None 会被写成字符串污染 notebook。
        return "notebook_edit 失败：缺少 source 参数。"  # 新增代码+AgentPySplitPhase12: 返回缺参提示；若没有这行代码，模型难以修正编辑调用。
    notebook_result = load_notebook(agent, arguments.get("path"), "notebook_edit")  # 新增代码+AgentPySplitPhase12: 统一加载并校验 notebook 文件；若没有这行代码，编辑路径安全和格式校验容易遗漏。
    if isinstance(notebook_result, str):  # 新增代码+AgentPySplitPhase12: 判断加载是否失败；若没有这行代码，后续会把错误字符串当元组使用。
        return notebook_result  # 新增代码+AgentPySplitPhase12: 直接返回加载错误；若没有这行代码，模型无法知道编辑失败原因。
    path, payload = notebook_result  # 新增代码+AgentPySplitPhase12: 拆出安全路径和 notebook JSON；若没有这行代码，后续无法定位文件和内容。
    cells = payload.get("cells")  # 新增代码+AgentPySplitPhase12: 读取 notebook cells；若没有这行代码，工具不知道能编辑哪些 cell。
    if not isinstance(cells, list):  # 新增代码+AgentPySplitPhase12: 校验 cells 必须是数组；若没有这行代码，畸形 notebook 会导致索引异常。
        return "notebook_edit 失败：notebook JSON 中的 cells 必须是数组。"  # 新增代码+AgentPySplitPhase12: 返回结构错误；若没有这行代码，模型无法理解文件格式问题。
    cell_index_result = parse_notebook_cell_index(agent, arguments.get("cell_index"), len(cells), "notebook_edit")  # 新增代码+AgentPySplitPhase12: 校验目标 cell 索引；若没有这行代码，无效索引可能导致崩溃或误改。
    if isinstance(cell_index_result, str):  # 新增代码+AgentPySplitPhase12: 判断索引解析是否失败；若没有这行代码，错误文本会被当整数使用。
        return cell_index_result  # 新增代码+AgentPySplitPhase12: 返回索引错误给模型；若没有这行代码，模型无法修正 cell_index。
    cell = cells[cell_index_result]  # 新增代码+AgentPySplitPhase12: 取出目标 cell；若没有这行代码，后续无法修改 source。
    if not isinstance(cell, dict):  # 新增代码+AgentPySplitPhase12: 校验目标 cell 必须是对象；若没有这行代码，非对象 cell 写 source 会报错。
        return f"notebook_edit 失败：cell {cell_index_result} 不是对象，无法编辑。"  # 新增代码+AgentPySplitPhase12: 返回畸形 cell 错误；若没有这行代码，模型不知道为什么不能编辑。
    source_text = str(arguments.get("source", ""))  # 新增代码+AgentPySplitPhase12: 把新 source 转成字符串；若没有这行代码，数字或布尔 source 会让写入格式不稳定。
    action = f"编辑 Notebook cell：{path}\ncell_index：{cell_index_result}\n新内容字符数：{len(source_text)}"  # 新增代码+AgentPySplitPhase12: 构造权限确认说明；若没有这行代码，用户无法核对要修改哪个 notebook 和 cell。
    if not agent.ask_permission(action):  # 新增代码+AgentPySplitPhase12: 写入 notebook 前请求用户确认；若没有这行代码，agent 会绕过权限边界修改文件。
        return f"用户拒绝了操作：{action}"  # 新增代码+AgentPySplitPhase12: 权限拒绝时返回可读结果；若没有这行代码，模型不知道文件未被修改。
    cell["source"] = notebook_text_to_source_lines(agent, source_text)  # 新增代码+AgentPySplitPhase12: 把新文本按 notebook 常用行数组格式写回；若没有这行代码，cell 内容不会被替换。
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # 新增代码+AgentPySplitPhase12: 以 UTF-8 JSON 写回 notebook；若没有这行代码，修改只存在内存里。
    return f"notebook_edit 成功：已更新 {path} 的 cell {cell_index_result}"  # 新增代码+AgentPySplitPhase12: 返回成功结果；若没有这行代码，模型无法确认编辑是否完成。
# 新增代码+AgentPySplitPhase12: 函数段结束，notebook_edit 到此结束；若没有这个边界说明，用户不容易看出 Notebook 编辑逻辑已经迁到 tools 层。


def load_notebook(agent: Any, raw_path: Any, tool_name: str) -> tuple[Path, dict[str, Any]] | str:  # 新增代码+AgentPySplitPhase12: 函数段开始，统一读取和校验 notebook 文件；若没有这段代码，read/edit 会重复路径和 JSON 校验逻辑。
    raw_path_text = str(raw_path or "").strip()  # 新增代码+AgentPySplitPhase12: 把 path 参数转成清理后的字符串；若没有这行代码，None 或空白路径处理不稳定。
    if not raw_path_text:  # 新增代码+AgentPySplitPhase12: 检查 path 是否为空；若没有这行代码，空路径会被解析成工作区目录。
        return f"{tool_name} 失败：缺少 path 参数。"  # 新增代码+AgentPySplitPhase12: 返回缺参错误；若没有这行代码，模型难以修正调用。
    path = atom_tools_from_tools.resolve_workspace_path(agent, raw_path_text)  # 修改代码+AgentPyCompatWrapperRemovalL6: 直接通过 atom_tools 解析 notebook 路径；若没有这行代码，删除 旧路径包装 后 notebook 工具会断开或允许越界路径。
    if path is None:  # 新增代码+AgentPySplitPhase12: 判断路径是否越界；若没有这行代码，工具可能读取或修改工作区外文件。
        return f"{tool_name} 失败：只能操作 learning_agent 工作区内的 .ipynb 文件。"  # 新增代码+AgentPySplitPhase12: 返回安全边界错误；若没有这行代码，模型不知道为什么被拒绝。
    if path.suffix.lower() != ".ipynb":  # 新增代码+AgentPySplitPhase12: 只允许 notebook 文件扩展名；若没有这行代码，工具可能误用于普通 JSON 或文本文件。
        return f"{tool_name} 失败：只能操作 .ipynb 文件：{path}"  # 新增代码+AgentPySplitPhase12: 返回扩展名错误；若没有这行代码，模型难以选择正确工具。
    if not path.exists():  # 新增代码+AgentPySplitPhase12: 检查文件是否存在；若没有这行代码，读取会抛底层 FileNotFoundError。
        return f"{tool_name} 失败：文件不存在：{path}"  # 新增代码+AgentPySplitPhase12: 返回不存在错误；若没有这行代码，用户会看到不友好的底层异常。
    if path.is_dir():  # 新增代码+AgentPySplitPhase12: 防止把目录当 notebook 文件；若没有这行代码，读取目录会抛底层异常。
        return f"{tool_name} 失败：不能把目录当 notebook 读取：{path}"  # 新增代码+AgentPySplitPhase12: 返回目录错误；若没有这行代码，模型难以修正 path。
    try:  # 新增代码+AgentPySplitPhase12: 捕获文件读取和 JSON 解析异常；若没有这行代码，坏 notebook 会中断整个 agent.run。
        payload = json.loads(path.read_text(encoding="utf-8"))  # 新增代码+AgentPySplitPhase12: 读取 UTF-8 notebook JSON；若没有这行代码，工具拿不到 notebook 内容。
    except (OSError, json.JSONDecodeError) as error:  # 新增代码+AgentPySplitPhase12: 处理磁盘错误和 JSON 格式错误；若没有这行代码，用户会看到 Python 堆栈。
        return f"{tool_name} 失败：无法读取 notebook JSON：{error}"  # 新增代码+AgentPySplitPhase12: 返回可读失败原因；若没有这行代码，模型无法解释为什么读取失败。
    if not isinstance(payload, dict):  # 新增代码+AgentPySplitPhase12: notebook 顶层必须是对象；若没有这行代码，list/null JSON 会让后续 .get 报错。
        return f"{tool_name} 失败：notebook JSON 顶层必须是对象。"  # 新增代码+AgentPySplitPhase12: 返回结构错误；若没有这行代码，模型不知道文件格式不对。
    return path, payload  # 新增代码+AgentPySplitPhase12: 返回安全路径和 notebook 数据；若没有这行代码，read/edit 无法继续处理。
# 新增代码+AgentPySplitPhase12: 函数段结束，load_notebook 到此结束；若没有这个边界说明，用户不容易看出 Notebook 加载校验逻辑已经迁到 tools 层。


def select_notebook_cells(agent: Any, cells: list[Any], raw_cell_index: Any, tool_name: str) -> list[tuple[int, Any]] | str:  # 新增代码+AgentPySplitPhase12: 函数段开始，根据可选索引选择 cell；若没有这段代码，notebook_read 不能复用索引校验。
    if raw_cell_index is None:  # 新增代码+AgentPySplitPhase12: 判断模型是否没有指定 cell_index；若没有这行代码，全量摘要场景无法区分。
        return list(enumerate(cells))  # 新增代码+AgentPySplitPhase12: 返回所有 cell 供摘要展示；若没有这行代码，notebook_read 默认会没有输出。
    cell_index = parse_notebook_cell_index(agent, raw_cell_index, len(cells), tool_name)  # 新增代码+AgentPySplitPhase12: 解析并校验单个 cell 索引；若没有这行代码，可能访问越界索引。
    if isinstance(cell_index, str):  # 新增代码+AgentPySplitPhase12: 判断索引解析是否失败；若没有这行代码，错误文本会被当整数使用。
        return cell_index  # 新增代码+AgentPySplitPhase12: 返回索引错误；若没有这行代码，模型无法修正参数。
    return [(cell_index, cells[cell_index])]  # 新增代码+AgentPySplitPhase12: 返回指定 cell 的二元组列表；若没有这行代码，指定单 cell 时不会输出内容。
# 新增代码+AgentPySplitPhase12: 函数段结束，select_notebook_cells 到此结束；若没有这个边界说明，用户不容易看出 cell 选择逻辑已经迁到 tools 层。


def parse_notebook_cell_index(agent: Any, raw_cell_index: Any, cell_count: int, tool_name: str) -> int | str:  # 新增代码+AgentPySplitPhase12: 函数段开始，把 cell_index 解析成安全整数；若没有这段代码，read/edit 索引校验会重复且易错。
    del agent  # 新增代码+AgentPySplitPhase12: 当前索引解析不需要 agent 但保留统一签名；若没有这行代码，读者会误以为遗漏上下文。
    try:  # 新增代码+AgentPySplitPhase12: 捕获模型传入非整数索引的情况；若没有这行代码，int 转换失败会中断 agent.run。
        cell_index = int(raw_cell_index)  # 新增代码+AgentPySplitPhase12: 把 JSON 数字或数字字符串转成 int；若没有这行代码，字符串索引无法兼容。
    except (TypeError, ValueError):  # 新增代码+AgentPySplitPhase12: 处理 None、对象或非数字字符串；若没有这行代码，错误输入会抛异常。
        return f"{tool_name} 失败：cell_index 必须是整数。"  # 新增代码+AgentPySplitPhase12: 返回索引类型错误；若没有这行代码，模型不知道如何修正。
    if cell_index < 0 or cell_index >= cell_count:  # 新增代码+AgentPySplitPhase12: 检查索引是否在 cell 数组范围内；若没有这行代码，负数或越界可能误读误改。
        return f"{tool_name} 失败：cell_index 超出范围，当前 notebook 有 {cell_count} 个 cell。"  # 新增代码+AgentPySplitPhase12: 返回范围错误和总数；若没有这行代码，模型不知道可用索引范围。
    return cell_index  # 新增代码+AgentPySplitPhase12: 返回安全 cell 索引；若没有这行代码，调用方无法定位目标 cell。
# 新增代码+AgentPySplitPhase12: 函数段结束，parse_notebook_cell_index 到此结束；若没有这个边界说明，用户不容易看出 cell 索引校验逻辑已经迁到 tools 层。


def notebook_source_to_text(agent: Any, source: Any) -> str:  # 新增代码+AgentPySplitPhase12: 函数段开始，把 notebook source 统一转成文本；若没有这段代码，list/string 两种 source 表示会导致输出不一致。
    del agent  # 新增代码+AgentPySplitPhase12: 当前 source 转换不需要 agent 但保留统一签名；若没有这行代码，读者会误以为遗漏上下文。
    if isinstance(source, list):  # 新增代码+AgentPySplitPhase12: notebook source 常见形式是字符串数组；若没有这行代码，多行 source 会显示成列表结构。
        return "".join(str(part) for part in source)  # 新增代码+AgentPySplitPhase12: 拼接每一行 source；若没有这行代码，模型看不到正常连续文本。
    if isinstance(source, str):  # 新增代码+AgentPySplitPhase12: notebook source 也可能是单个字符串；若没有这行代码，字符串 source 会走到 JSON 兜底。
        return source  # 新增代码+AgentPySplitPhase12: 原样返回字符串 source；若没有这行代码，代码内容可能被额外加引号。
    if source is None:  # 新增代码+AgentPySplitPhase12: 处理缺失或 null source；若没有这行代码，None 会显示成字符串 "None"。
        return ""  # 新增代码+AgentPySplitPhase12: 空 source 返回空文本；若没有这行代码，空 cell 可读性变差。
    return json.dumps(source, ensure_ascii=False)  # 新增代码+AgentPySplitPhase12: 兜底显示异常 source 结构；若没有这行代码，非标准 source 会完全丢失。
# 新增代码+AgentPySplitPhase12: 函数段结束，notebook_source_to_text 到此结束；若没有这个边界说明，用户不容易看出 source 文本化逻辑已经迁到 tools 层。


def notebook_text_to_source_lines(agent: Any, source_text: str) -> list[str]:  # 新增代码+AgentPySplitPhase12: 函数段开始，把编辑文本转成 notebook 常用 source 行数组；若没有这段代码，写回格式容易不稳定。
    del agent  # 新增代码+AgentPySplitPhase12: 当前文本转换不需要 agent 但保留统一签名；若没有这行代码，读者会误以为遗漏上下文。
    if source_text == "":  # 新增代码+AgentPySplitPhase12: 判断用户是否明确写入空内容；若没有这行代码，空 cell 语义不够清楚。
        return []  # 新增代码+AgentPySplitPhase12: 空 cell 用空数组表示；若没有这行代码，空字符串可能和多行格式不一致。
    return source_text.splitlines(keepends=True)  # 新增代码+AgentPySplitPhase12: 按行保留换行符写回 source；若没有这行代码，多行代码会丢失换行结构。
# 新增代码+AgentPySplitPhase12: 函数段结束，notebook_text_to_source_lines 到此结束；若没有这个边界说明，用户不容易看出 source 写回格式逻辑已经迁到 tools 层。

