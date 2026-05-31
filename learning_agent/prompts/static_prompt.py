"""静态系统提示词加载。"""  # 新增代码+PromptsSplit: 把 staticprompt.md 的路径解析、兜底和占位符渲染集中到 prompts 层；若没有这个文件，提示词加载仍散在主入口。

from __future__ import annotations  # 新增代码+PromptsSplit: 延迟解析类型注解；若没有这行代码，后续扩展 Path 类型时更稳。

from pathlib import Path  # 新增代码+PromptsSplit: 使用跨平台路径对象处理提示词文件；若没有这行代码，Windows 路径拼接会更脆弱。


def _package_root() -> Path:  # 新增代码+PromptsSplit: 定位 learning_agent 包根目录；若没有这行代码，包内默认 staticprompt 路径会散落硬编码。
    return Path(__file__).resolve().parents[1]  # 新增代码+PromptsSplit: prompts/static_prompt.py 的上两级是 learning_agent 目录；若没有这行代码，默认提示词路径会算错。


def resolve_static_prompt_path(workspace: str | Path) -> Path:  # 新增代码+PromptsSplit: 统一解析 staticprompt.md 的加载路径；若没有这行代码，工作区覆盖和包内默认路径会散落在多个地方。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+PromptsSplit: 规范化工作区路径；若没有这行代码，相对路径覆盖规则会不稳定。
    workspace_static_prompt = workspace_path / "staticprompt" / "staticprompt.md"  # 新增代码+PromptsSplit: 构造用户可编辑的工作区静态提示词路径；若没有这行代码，用户无法用项目级文件覆盖默认提示词。
    if workspace_static_prompt.exists():  # 新增代码+PromptsSplit: 工作区静态文件存在时优先使用；若没有这行代码，用户自定义 staticprompt.md 会被包内默认覆盖。
        return workspace_static_prompt  # 新增代码+PromptsSplit: 返回工作区覆盖路径；若没有这行代码，覆盖优先级不会生效。
    return _package_root() / "staticprompt" / "staticprompt.md"  # 新增代码+PromptsSplit: 回退到 learning_agent 包内默认静态提示词；若没有这行代码，新安装项目没有工作区覆盖时无法启动默认规则。


def fallback_static_prompt(reason: str, *, workspace: str | Path, current_date: str) -> str:  # 新增代码+PromptsSplit: 构造静态提示词缺失时的最小兜底；若没有这行代码，坏文件会直接打断 agent。
    fallback_lines = [  # 新增代码+PromptsSplit: 用列表保存每行兜底提示词；若没有这行代码，后续无法逐行说明最小安全规则。
        "Prompt Surface Architecture v2",  # 新增代码+PromptsSplit: 保留提示词表面版本标记；若没有这行代码，用户难以判断 agent 是否仍在新架构下运行。
        "Core Identity / 核心身份：",  # 新增代码+PromptsSplit: 保留身份区块标题；若没有这行代码，兜底提示词结构会不清楚。
        "你是一个面向软件工程任务的成熟 coding agent。",  # 新增代码+PromptsSplit: 保留最小身份定义；若没有这行代码，模型缺少基本角色边界。
        "Operating Principles / 行为原则：",  # 新增代码+PromptsSplit: 保留行为原则区块标题；若没有这行代码，兜底规则会混在身份里。
        "默认使用中文；没有工具结果，不声称已经读写文件、联网、运行命令或调用外部系统。",  # 新增代码+PromptsSplit: 保留证据优先底线；若没有这行代码，坏提示词文件可能导致模型伪造执行结果。
        "在提出或进行代码修改之前，先阅读相关的代码。",  # 新增代码+PromptsSplit: 保留先读后改规则；若没有这行代码，兜底状态下也可能直接乱改文件。
        "Dynamic Runtime Rules / 动态运行规则：",  # 新增代码+PromptsSplit: 保留动态规则入口标题；若没有这行代码，模型不知道还有按需规则可加载。
        "需要具体流程时先用 read 读取 learning_agent/skills/tool_list.md，再读取对应 SKILL.md；只有确实需要细节时才继续读取 rules/*.md。",  # 新增代码+PromptsSplit: 兜底提示词也遵守三级动态规则树；若没有这行代码，静态文件损坏后模型可能直接跳进大量子规则。
        f"静态提示词文件状态：{reason}",  # 新增代码+PromptsSplit: 把缺失或损坏原因写进 system prompt；若没有这行代码，用户排查时看不到根因。
        "当前日期：",  # 新增代码+PromptsSplit: 兜底提示词也保留当前日期标签；若没有这行代码，静态提示词损坏时模型不知道下一行是日期。
        current_date,  # 新增代码+PromptsSplit: 写入调用方传入的本机当天日期；若没有这行代码，坏文件场景下 agent 仍然看不到今天的真实日期。
        "当前工作区：",  # 新增代码+PromptsSplit: 保留工作区标签；若没有这行代码，模型不知道文件操作默认位置。
        str(Path(workspace).expanduser().resolve()),  # 新增代码+PromptsSplit: 写入真实工作区路径；若没有这行代码，兜底提示词无法定位项目。
    ]  # 新增代码+PromptsSplit: 结束兜底提示词行列表；若没有这行代码，Python 列表语法不完整。
    return "\n".join(fallback_lines)  # 新增代码+PromptsSplit: 合并兜底提示词行；若没有这行代码，调用方拿不到字符串形式的 system prompt。


def read_static_prompt(static_prompt_path: str | Path, *, workspace: str | Path, current_date: str, max_chars: int = 12000) -> str:  # 新增代码+PromptsSplit: 读取 staticprompt.md 并渲染工作区和日期占位符；若没有这行代码，静态提示词文件不会真正接管系统提示词。
    prompt_path = Path(static_prompt_path)  # 新增代码+PromptsSplit: 把输入路径包装成 Path；若没有这行代码，调用方传字符串时无法使用 exists/is_dir。
    if not prompt_path.exists():  # 新增代码+PromptsSplit: 检查静态提示词文件是否存在；若没有这行代码，缺失文件会在读取时抛出底层异常。
        return fallback_static_prompt("没有找到 staticprompt/staticprompt.md。", workspace=workspace, current_date=current_date)  # 新增代码+PromptsSplit: 返回最小安全兜底提示词；若没有这行代码，文件缺失会让 agent 无法启动。
    if prompt_path.is_dir():  # 新增代码+PromptsSplit: 防止同名目录被当成提示词文件读取；若没有这行代码，目录路径会触发难懂的读取错误。
        return fallback_static_prompt("staticprompt/staticprompt.md 当前是目录，无法读取。", workspace=workspace, current_date=current_date)  # 新增代码+PromptsSplit: 用人话解释坏路径；若没有这行代码，用户不知道为什么提示词没生效。
    text = prompt_path.read_text(encoding="utf-8", errors="replace")  # 新增代码+PromptsSplit: 用 UTF-8 读取静态提示词；若没有这行代码，中文提示词无法稳定进入模型上下文。
    if not text.strip():  # 新增代码+PromptsSplit: 检查文件是否只有空白；若没有这行代码，空文件会让模型只看到记忆索引而缺少核心规则。
        return fallback_static_prompt("staticprompt/staticprompt.md 当前为空。", workspace=workspace, current_date=current_date)  # 新增代码+PromptsSplit: 空文件时仍保留最小安全边界；若没有这行代码，用户误删内容会导致 agent 行为失控。
    rendered_text = text.replace("{{CURRENT_WORKSPACE}}", str(Path(workspace).expanduser().resolve()))  # 新增代码+PromptsSplit: 替换用户可编辑模板里的当前工作区占位符；若没有这行代码，模型只会看到无效工作区模板文本。
    rendered_text = rendered_text.replace("{{CURRENT_DATE}}", current_date)  # 新增代码+PromptsSplit: 每轮把当前日期占位符替换成本机当天日期；若没有这行代码，模型会看到模板而不知道今天是哪一天。
    if len(rendered_text) > max_chars:  # 新增代码+PromptsSplit: 限制用户自定义静态提示词的极端长度；若没有这行代码，误粘大文档会重新撑爆每轮上下文。
        return rendered_text[:max_chars] + "\n...[staticprompt.md 过长，已截断]..."  # 新增代码+PromptsSplit: 返回带截断说明的安全文本；若没有这行代码，模型不知道系统提示词被截断。
    return rendered_text  # 新增代码+PromptsSplit: 返回正常渲染后的静态提示词；若没有这行代码，读取成功也不会进入 system prompt。
