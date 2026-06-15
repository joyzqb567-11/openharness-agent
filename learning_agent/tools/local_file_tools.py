"""本地文件、长期记忆和 todo 清单工具。"""  # 新增代码+AgentPySplitPhase12: 说明本模块承接 agent.py 里本地文件类工具；若没有这行代码，用户打开文件时不容易判断模块职责。

from __future__ import annotations  # 新增代码+AgentPySplitPhase12: 让类型注解延迟解析；若没有这行代码，复杂注解在部分运行方式下更容易提前求值出错。

import json  # 新增代码+AgentPySplitPhase12: todo_read/todo_write 需要读写 JSON；若没有这行代码，任务清单无法解析和保存。
from typing import Any  # 新增代码+AgentPySplitPhase12: 用 Any 表示传入的 LearningAgent 上下文；若没有这行代码，新模块会为了类型注解反向导入 agent.py。


def resolve_workspace_path_from_atom_tools(agent: Any, raw_path: str):  # 修改代码+AgentPyCompatWrapperRemovalL6: 函数段开始，运行时懒加载 atom_tools 的安全路径解析；若没有这段函数，删除旧路径包装后本地文件工具会断开，作者意图是避免 local_file_tools 和 atom_tools 顶层循环导入，本段到 return 为止。
    try:  # 修改代码+AgentPyCompatWrapperRemovalL6: 优先按包路径导入 atom_tools；若没有这行代码，python -m 运行时无法找到统一路径边界实现。
        import learning_agent.tools.atom_tools as atom_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL6: 读取原子工具模块里的真实路径解析函数；若没有这行代码，本地文件工具会继续依赖 agent.py 旧包装。
    except ModuleNotFoundError as error:  # 修改代码+AgentPyCompatWrapperRemovalL6: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀差异会让文件工具导入失败。
        if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.atom_tools"}:  # 修改代码+AgentPyCompatWrapperRemovalL6: 只允许路径差异进入 fallback；若没有这行代码，atom_tools 内部真实错误会被误吞。
            raise  # 修改代码+AgentPyCompatWrapperRemovalL6: 重新抛出真实导入错误；若没有这行代码，排查路径工具问题会被 fallback 遮住根因。
        import tools.atom_tools as atom_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL6: 脚本模式下导入同一个原子工具模块；若没有这行代码，bat 入口执行 read_file/write_file 会找不到路径解析。
    return atom_tools_from_tools.resolve_workspace_path(agent, raw_path)  # 修改代码+AgentPyCompatWrapperRemovalL6: 调用统一安全路径解析；若没有这行代码，../ 越界保护会丢失或重复实现。
# 修改代码+AgentPyCompatWrapperRemovalL6: 函数段结束，resolve_workspace_path_from_atom_tools 到此结束；若没有这个边界说明，用户不容易看出这里只是去包装后的路径桥。


def read_file(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase12: 函数段开始，读取工作区内文本文件；若没有这段代码，agent.py 的 _read_file 薄包装没有真实实现。
    raw_path = str(arguments.get("path", "")).strip()  # 新增代码+AgentPySplitPhase12: 从工具参数取 path 并去掉空白；若没有这行代码，空格路径和缺参路径会混在一起。
    if not raw_path:  # 新增代码+AgentPySplitPhase12: 检查模型是否提供 path；若没有这行代码，空路径可能被解析成工作区目录。
        return "read_file 失败：缺少 path 参数。"  # 新增代码+AgentPySplitPhase12: 返回可读缺参错误；若没有这行代码，模型不知道该补 path。
    path = resolve_workspace_path_from_atom_tools(agent, raw_path)  # 修改代码+AgentPyCompatWrapperRemovalL6: 直接通过 atom_tools 解析安全路径；若没有这行代码，删除旧路径包装后 read_file 会断开或失去 workspace 越界保护。
    if path is None:  # 新增代码+AgentPySplitPhase12: 判断路径是否被安全解析器拒绝；若没有这行代码，越界路径会继续执行。
        return "read_file 失败：只能读取 learning_agent 工作区内的文件。"  # 新增代码+AgentPySplitPhase12: 返回越界读取提示；若没有这行代码，用户不知道为什么不能读。
    if not path.exists():  # 新增代码+AgentPySplitPhase12: 检查目标文件是否存在；若没有这行代码，底层 FileNotFoundError 会暴露给模型。
        return f"read_file 失败：文件不存在：{path}"  # 新增代码+AgentPySplitPhase12: 返回文件不存在的可读错误；若没有这行代码，模型难以修正路径。
    if path.is_dir():  # 新增代码+AgentPySplitPhase12: 防止把目录当文件读取；若没有这行代码，读取目录会触发底层异常。
        return f"read_file 失败：不能把目录当文件读取：{path}"  # 新增代码+AgentPySplitPhase12: 返回目录类型错误；若没有这行代码，用户会看到不友好的异常。
    text = path.read_text(encoding="utf-8", errors="replace")  # 新增代码+AgentPySplitPhase12: 按 UTF-8 读取文本并替换坏字符；若没有这行代码，文件内容无法进入模型上下文。
    if len(text) > 8000:  # 新增代码+AgentPySplitPhase12: 检查内容是否过长；若没有这行代码，大文件可能撑爆模型上下文。
        return text[:8000] + "\n...[内容过长，已截断]..."  # 新增代码+AgentPySplitPhase12: 返回截断文本和提示；若没有这行代码，模型会误以为看到完整大文件。
    return text  # 新增代码+AgentPySplitPhase12: 返回完整文本；若没有这行代码，正常读取也没有结果。
# 新增代码+AgentPySplitPhase12: 函数段结束，read_file 到此结束；若没有这个边界说明，用户不容易看出本地读取逻辑已经迁到 tools 层。


def write_file(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase12: 函数段开始，写入工作区内文本文件；若没有这段代码，agent.py 的 _write_file 薄包装没有真实实现。
    raw_path = str(arguments.get("path", "")).strip()  # 新增代码+AgentPySplitPhase12: 从工具参数取 path 并清理空白；若没有这行代码，空白路径会造成误写风险。
    content = str(arguments.get("content", ""))  # 新增代码+AgentPySplitPhase12: 从工具参数取 content 并转成字符串；若没有这行代码，写入内容格式不稳定。
    if not raw_path:  # 新增代码+AgentPySplitPhase12: 检查是否提供 path；若没有这行代码，空路径可能指向工作区目录。
        return "write_file 失败：缺少 path 参数。"  # 新增代码+AgentPySplitPhase12: 返回缺参提示；若没有这行代码，模型不知道如何修正调用。
    path = resolve_workspace_path_from_atom_tools(agent, raw_path)  # 修改代码+AgentPyCompatWrapperRemovalL6: 直接通过 atom_tools 解析安全路径；若没有这行代码，删除旧路径包装后 write_file 会断开或失去 workspace 越界保护。
    if path is None:  # 新增代码+AgentPySplitPhase12: 判断路径是否越界；若没有这行代码，不安全路径会继续执行。
        return "write_file 失败：只能写入 learning_agent 工作区内的文件。"  # 新增代码+AgentPySplitPhase12: 返回安全边界错误；若没有这行代码，用户不知道为何被拒绝。
    action = f"写入文件：{path}"  # 新增代码+AgentPySplitPhase12: 构造给用户确认的动作说明；若没有这行代码，权限弹窗缺少目标文件信息。
    if not agent.ask_permission(action):  # 新增代码+AgentPySplitPhase12: 写文件前请求用户确认；若没有这行代码，agent 会绕过权限边界修改文件。
        return f"用户拒绝了操作：{action}"  # 新增代码+AgentPySplitPhase12: 返回用户拒绝结果；若没有这行代码，模型会误以为写入失败原因不明。
    path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+AgentPySplitPhase12: 确保父目录存在；若没有这行代码，新目录下写文件会失败。
    path.write_text(content, encoding="utf-8")  # 新增代码+AgentPySplitPhase12: 以 UTF-8 写入文本；若没有这行代码，内容只停留在内存里。
    return f"write_file 成功：已写入 {path}"  # 新增代码+AgentPySplitPhase12: 返回成功结果；若没有这行代码，模型无法确认文件已落盘。
# 新增代码+AgentPySplitPhase12: 函数段结束，write_file 到此结束；若没有这个边界说明，用户不容易看出写文件逻辑已经迁到 tools 层。


def append_memory(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase12: 函数段开始，追加一条长期记忆；若没有这段代码，agent.py 的 _append_memory 薄包装没有真实实现。
    text = str(arguments.get("text", "")).strip()  # 新增代码+AgentPySplitPhase12: 从参数取 text 并清理空白；若没有这行代码，空白记忆会写入 memory.md。
    if not text:  # 新增代码+AgentPySplitPhase12: 检查记忆内容是否为空；若没有这行代码，空记忆会污染长期记忆文件。
        return "append_memory 失败：缺少 text 参数。"  # 新增代码+AgentPySplitPhase12: 返回缺参提示；若没有这行代码，模型不知道需要补 text。
    action = f"追加长期记忆：{text}"  # 新增代码+AgentPySplitPhase12: 构造权限确认说明；若没有这行代码，用户无法确认要写入什么记忆。
    if not agent.ask_permission(action):  # 新增代码+AgentPySplitPhase12: 写长期记忆前请求确认；若没有这行代码，agent 会擅自保存长期记忆。
        return f"用户拒绝了操作：{action}"  # 新增代码+AgentPySplitPhase12: 返回拒绝结果；若没有这行代码，模型不知道记忆没有保存。
    with agent.memory_path.open("a", encoding="utf-8") as file:  # 新增代码+AgentPySplitPhase12: 以追加模式打开 memory.md；若没有这行代码，无法保留旧记忆并追加新条目。
        file.write(f"- {text}\n")  # 新增代码+AgentPySplitPhase12: 按 Markdown 列表格式写入记忆；若没有这行代码，新记忆不会落盘。
    return "append_memory 成功：已写入 memory.md"  # 新增代码+AgentPySplitPhase12: 返回保存成功提示；若没有这行代码，模型无法确认记忆已保存。
# 新增代码+AgentPySplitPhase12: 函数段结束，append_memory 到此结束；若没有这个边界说明，用户不容易看出长期记忆追加逻辑已经迁到 tools 层。


def todo_read(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase12: 函数段开始，读取内部任务清单；若没有这段代码，agent.py 的 _todo_read 薄包装没有真实实现。
    del arguments  # 新增代码+AgentPySplitPhase12: todo_read 当前不需要参数但保留工具签名；若没有这行代码，读者会误以为忘记处理参数。
    if not agent.todo_path.exists():  # 新增代码+AgentPySplitPhase12: 检查 todo_state.json 是否存在；若没有这行代码，第一次读取会报文件不存在。
        return "todo_read 成功：当前任务清单为空。"  # 新增代码+AgentPySplitPhase12: 返回空清单状态；若没有这行代码，模型不知道可以从空任务开始。
    try:  # 新增代码+AgentPySplitPhase12: 捕获读取和 JSON 解析错误；若没有这行代码，坏 todo 文件会中断 agent.run。
        payload = json.loads(agent.todo_path.read_text(encoding="utf-8"))  # 新增代码+AgentPySplitPhase12: 读取并解析任务清单 JSON；若没有这行代码，无法恢复持久任务状态。
    except (OSError, json.JSONDecodeError) as error:  # 新增代码+AgentPySplitPhase12: 处理磁盘错误或 JSON 格式错误；若没有这行代码，用户会看到底层异常。
        return f"todo_read 失败：无法读取 todo_state.json：{error}"  # 新增代码+AgentPySplitPhase12: 返回可读失败原因；若没有这行代码，模型无法判断清单为何不可用。
    todos = payload.get("todos", []) if isinstance(payload, dict) else []  # 新增代码+AgentPySplitPhase12: 从顶层对象取 todos 数组；若没有这行代码，工具无法兼容既定保存格式。
    if not isinstance(todos, list):  # 新增代码+AgentPySplitPhase12: 校验 todos 必须是数组；若没有这行代码，坏结构会进入后续输出。
        return "todo_read 失败：todo_state.json 中的 todos 必须是数组。"  # 新增代码+AgentPySplitPhase12: 返回结构错误；若没有这行代码，模型不知道如何修复文件。
    if not todos:  # 新增代码+AgentPySplitPhase12: 检查任务数组是否为空；若没有这行代码，空数组会输出冗长 JSON。
        return "todo_read 成功：当前任务清单为空。"  # 新增代码+AgentPySplitPhase12: 返回简洁空状态；若没有这行代码，模型可能误以为读取失败。
    return "todo_read 成功：当前任务清单如下：\n" + json.dumps({"todos": todos}, ensure_ascii=False, indent=2)  # 新增代码+AgentPySplitPhase12: 返回结构化任务清单；若没有这行代码，模型无法基于当前计划继续更新。
# 新增代码+AgentPySplitPhase12: 函数段结束，todo_read 到此结束；若没有这个边界说明，用户不容易看出 todo 读取逻辑已经迁到 tools 层。


def todo_write(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase12: 函数段开始，校验并保存内部任务清单；若没有这段代码，agent.py 的 _todo_write 薄包装没有真实实现。
    raw_todos = arguments.get("todos")  # 新增代码+AgentPySplitPhase12: 从参数中取 todos 数组；若没有这行代码，工具不知道模型提交了哪些任务。
    if not isinstance(raw_todos, list):  # 新增代码+AgentPySplitPhase12: 校验 todos 必须是数组；若没有这行代码，字符串或对象会污染任务清单。
        return "todo_write 失败：缺少 todos 数组参数。"  # 新增代码+AgentPySplitPhase12: 返回缺参或类型错误；若没有这行代码，模型无法修正参数。
    valid_statuses = {"pending", "in_progress", "completed"}  # 新增代码+AgentPySplitPhase12: 定义允许的任务状态；若没有这行代码，doing/done 等不统一状态会进入清单。
    valid_priorities = {"high", "medium", "low"}  # 新增代码+AgentPySplitPhase12: 定义允许的优先级；若没有这行代码，优先级字段会变得不一致。
    normalized_todos: list[dict[str, str]] = []  # 新增代码+AgentPySplitPhase12: 准备保存校验后的任务；若没有这行代码，无法统一补齐 id 和 priority。
    for index, raw_todo in enumerate(raw_todos, start=1):  # 新增代码+AgentPySplitPhase12: 逐条校验任务并保留序号；若没有这行代码，错误任务无法定位。
        if not isinstance(raw_todo, dict):  # 新增代码+AgentPySplitPhase12: 校验每条任务必须是对象；若没有这行代码，后续 .get 会在字符串上报错。
            return f"todo_write 失败：第 {index} 条任务必须是对象。"  # 新增代码+AgentPySplitPhase12: 返回具体条目错误；若没有这行代码，模型不知道该改哪条。
        content = str(raw_todo.get("content", "")).strip()  # 新增代码+AgentPySplitPhase12: 读取并清理任务内容；若没有这行代码，空白任务会进入清单。
        if not content:  # 新增代码+AgentPySplitPhase12: 检查任务内容是否为空；若没有这行代码，任务清单会出现不可执行空项。
            return f"todo_write 失败：第 {index} 条任务缺少 content。"  # 新增代码+AgentPySplitPhase12: 返回缺 content 的具体条目；若没有这行代码，模型难以自我修正。
        status = str(raw_todo.get("status", "")).strip()  # 新增代码+AgentPySplitPhase12: 读取并清理任务状态；若没有这行代码，无法判断任务进度是否合法。
        if status not in valid_statuses:  # 新增代码+AgentPySplitPhase12: 校验状态白名单；若没有这行代码，非法状态会污染进度。
            return f"todo_write 失败：第 {index} 条任务 status 必须是 pending/in_progress/completed。"  # 新增代码+AgentPySplitPhase12: 告诉模型合法状态值；若没有这行代码，模型不知道该改成什么。
        priority = str(raw_todo.get("priority", "medium")).strip() or "medium"  # 新增代码+AgentPySplitPhase12: 读取优先级并默认 medium；若没有这行代码，未传 priority 的任务会缺字段。
        if priority not in valid_priorities:  # 新增代码+AgentPySplitPhase12: 校验优先级白名单；若没有这行代码，自由文本优先级会让排序和阅读不稳定。
            return f"todo_write 失败：第 {index} 条任务 priority 必须是 high/medium/low。"  # 新增代码+AgentPySplitPhase12: 告诉模型合法优先级；若没有这行代码，模型难以修正错误参数。
        todo_id = str(raw_todo.get("id", "")).strip() or f"todo-{index}"  # 新增代码+AgentPySplitPhase12: 使用已有 id 或自动生成稳定 id；若没有这行代码，多轮更新难以引用同一任务。
        normalized_todos.append({"id": todo_id, "content": content, "status": status, "priority": priority})  # 新增代码+AgentPySplitPhase12: 保存规范化任务对象；若没有这行代码，校验后的任务不会进入落盘结果。
    payload = {"todos": normalized_todos}  # 新增代码+AgentPySplitPhase12: 构造统一保存对象；若没有这行代码，todo_read 不知道从哪里读取任务数组。
    agent.todo_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # 新增代码+AgentPySplitPhase12: 写入 UTF-8 JSON 清单；若没有这行代码，任务状态只存在内存里。
    return f"todo_write 成功：已保存 {len(normalized_todos)} 条任务到 todo_state.json"  # 新增代码+AgentPySplitPhase12: 返回保存数量；若没有这行代码，模型无法确认清单是否更新成功。
# 新增代码+AgentPySplitPhase12: 函数段结束，todo_write 到此结束；若没有这个边界说明，用户不容易看出 todo 写入逻辑已经迁到 tools 层。
