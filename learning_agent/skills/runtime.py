"""本地 skill 发现、列表和加载的真实运行时实现。"""  # 新增代码+AgentPyPhaseCSkillRuntime: 把 skill_list/skill_load 能力从 agent.py 拆到 skills 层；若没有这个文件，主 agent 仍会承载 skill 扫描和读取细节。

from __future__ import annotations  # 新增代码+AgentPyPhaseCSkillRuntime: 延迟解析类型注解；若没有这行代码，脚本模式下类型注解更容易受导入顺序影响。

from pathlib import Path  # 新增代码+AgentPyPhaseCSkillRuntime: skill 扫描和相对路径计算需要 Path；若没有这行代码，运行时只能用脆弱字符串拼路径。
from typing import Any  # 新增代码+AgentPyPhaseCSkillRuntime: 用 Any 表示传入的 agent 对象和 skill 元信息；若没有这行代码，新模块会为了类型注解反向导入 agent.py。

try:  # 新增代码+AgentPyPhaseCSkillRuntime: 包运行模式下导入 skill runtime 依赖；若没有这行代码，python -m 运行时无法复用已拆出的 helper。
    import learning_agent.core.run_helpers as run_helpers_from_core  # 新增代码+AgentPyPhaseCSkillRuntime: 导入 observation 记录 helper；若没有这行代码，skill_load 无法记录 skill_loaded 事件。
    import learning_agent.runtime.background_commands as background_commands_from_runtime  # 新增代码+AgentPyPhaseCSkillRuntime: 导入 max_chars 解析 helper；若没有这行代码，skill_load 的大文本截断规则会复制回本模块。
    import learning_agent.tools.search as search_tools_from_tools  # 新增代码+AgentPyPhaseCSkillRuntime: 导入搜索拆词、打分和数量限制 helper；若没有这行代码，skill_list 会重复 tool_search 逻辑。
    from learning_agent.prompts.dynamic_prompt import dynamic_prompt_skill_metadata as dynamic_prompt_skill_metadata_from_prompts  # 新增代码+AgentPyPhaseCSkillRuntime: 导入 dynamicprompt 伪 skill 元信息工厂；若没有这行代码，dynamicprompt 无法通过 skill_load 读取。
except ModuleNotFoundError as error:  # 新增代码+AgentPyPhaseCSkillRuntime: 捕获 start_oauth_agent.bat 直接脚本模式下的包路径差异；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.run_helpers", "learning_agent.runtime", "learning_agent.runtime.background_commands", "learning_agent.tools", "learning_agent.tools.search", "learning_agent.prompts", "learning_agent.prompts.dynamic_prompt"}:  # 新增代码+AgentPyPhaseCSkillRuntime: 只允许目标路径缺失时 fallback；若没有这行代码，内部真实导入错误会被误吞。
        raise  # 新增代码+AgentPyPhaseCSkillRuntime: 重新抛出真正的导入错误；若没有这行代码，排查 runtime 问题会看不到根因。
    import core.run_helpers as run_helpers_from_core  # 新增代码+AgentPyPhaseCSkillRuntime: 脚本模式下导入 observation helper；若没有这行代码，bat 入口加载 skill 后无法记录事件。
    import runtime.background_commands as background_commands_from_runtime  # 新增代码+AgentPyPhaseCSkillRuntime: 脚本模式下导入 max_chars 解析 helper；若没有这行代码，bat 入口的 skill_load 截断规则会断开。
    import tools.search as search_tools_from_tools  # 新增代码+AgentPyPhaseCSkillRuntime: 脚本模式下导入搜索 helper；若没有这行代码，bat 入口执行 skill_list 会找不到拆词和打分逻辑。
    from prompts.dynamic_prompt import dynamic_prompt_skill_metadata as dynamic_prompt_skill_metadata_from_prompts  # 新增代码+AgentPyPhaseCSkillRuntime: 脚本模式下导入 dynamicprompt 伪 skill 工厂；若没有这行代码，bat 入口无法按 skill 方式加载 dynamicprompt。


def skill_list(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseCSkillRuntime: 函数段开始，执行内置 skill_list 工具；若没有这段函数，模型无法发现本地 skills。
    query = str(arguments.get("query", "") or "").strip()  # 新增代码+AgentPyPhaseCSkillRuntime: 读取可选搜索关键词；若没有这行代码，模型无法按能力筛选 skills。
    max_results = search_tools_from_tools.tool_search_max_results(arguments.get("max_results"))  # 新增代码+AgentPyPhaseCSkillRuntime: 解析最大结果数并限制范围；若没有这行代码，skill 很多时可能撑爆上下文。
    skills = discover_skills(agent)  # 新增代码+AgentPyPhaseCSkillRuntime: 扫描工作区和包内本地 skills；若没有这行代码，列表工具没有数据来源。
    if query:  # 新增代码+AgentPyPhaseCSkillRuntime: 如果模型提供了搜索关键词；若没有这行代码，搜索和全量列表无法区分。
        terms = search_tools_from_tools.tool_search_terms(query)  # 新增代码+AgentPyPhaseCSkillRuntime: 复用工具搜索拆词逻辑；若没有这行代码，多词和大小写匹配会不稳定。
        scored_skills: list[tuple[int, dict[str, Any]]] = []  # 新增代码+AgentPyPhaseCSkillRuntime: 准备保存匹配分数和 skill；若没有这行代码，无法排序筛选结果。
        for skill in skills:  # 新增代码+AgentPyPhaseCSkillRuntime: 遍历每个本地 skill；若没有这行代码，query 不会匹配任何 skill。
            score = search_tools_from_tools.tool_search_score(terms, str(skill["name"]), str(skill["description"]), [str(skill["relative_path"])])  # 新增代码+AgentPyPhaseCSkillRuntime: 按名称、说明和路径计算相关度；若没有这行代码，搜索结果无法排序或过滤。
            if score > 0:  # 新增代码+AgentPyPhaseCSkillRuntime: 只保留有命中的 skill；若没有这行代码，搜索会返回无关说明书。
                scored_skills.append((score, skill))  # 新增代码+AgentPyPhaseCSkillRuntime: 保存命中的 skill；若没有这行代码，命中结果不会进入输出。
        scored_skills.sort(key=lambda item: (-item[0], str(item[1]["name"])))  # 新增代码+AgentPyPhaseCSkillRuntime: 按分数降序和名称升序排序；若没有这行代码，结果顺序不稳定且不够相关。
        visible_skills = [skill for _, skill in scored_skills[:max_results]]  # 新增代码+AgentPyPhaseCSkillRuntime: 截取最多 max_results 条搜索结果；若没有这行代码，大量结果可能撑爆上下文。
        total_count = len(scored_skills)  # 新增代码+AgentPyPhaseCSkillRuntime: 记录命中总数用于标题展示；若没有这行代码，模型不知道是否发生截断。
    else:  # 新增代码+AgentPyPhaseCSkillRuntime: 如果没有 query 就列出全部 skills；若没有这行代码，空 query 可能得到空结果。
        visible_skills = skills[:max_results]  # 新增代码+AgentPyPhaseCSkillRuntime: 截取最多 max_results 条全量结果；若没有这行代码，skill 很多时可能撑爆上下文。
        total_count = len(skills)  # 新增代码+AgentPyPhaseCSkillRuntime: 记录 skill 总数用于标题展示；若没有这行代码，模型不知道本地共有多少 skill。
    if not visible_skills:  # 新增代码+AgentPyPhaseCSkillRuntime: 处理没有 skill 或没有命中的情况；若没有这行代码，空结果会返回只有标题的模糊文本。
        return "skill_list 成功：没有找到匹配的本地 skills。"  # 新增代码+AgentPyPhaseCSkillRuntime: 明确告诉模型列表为空；若没有这行代码，模型可能误以为工具失败。
    lines = [f"skill_list 成功：找到 {total_count} 个 skill，显示前 {len(visible_skills)} 个。"]  # 新增代码+AgentPyPhaseCSkillRuntime: 构造结果标题；若没有这行代码，模型不知道结果数量和截断情况。
    for index, skill in enumerate(visible_skills, start=1):  # 新增代码+AgentPyPhaseCSkillRuntime: 逐条格式化 skill 信息；若没有这行代码，skill 元信息无法变成人类和模型可读文本。
        lines.append(f"{index}. {skill['name']}")  # 新增代码+AgentPyPhaseCSkillRuntime: 输出 skill 名称；若没有这行代码，模型不知道 skill_load 要传什么 name。
        lines.append(f"   说明：{skill['description'] or '(无说明)'}")  # 新增代码+AgentPyPhaseCSkillRuntime: 输出 skill 说明；若没有这行代码，模型缺少选择 skill 的语义依据。
        lines.append(f"   路径：{skill['relative_path']}")  # 新增代码+AgentPyPhaseCSkillRuntime: 输出 skill 文件相对路径；若没有这行代码，用户无法定位说明书文件。
    return "\n".join(lines)  # 新增代码+AgentPyPhaseCSkillRuntime: 返回完整 skill 列表文本；若没有这行代码，工具无法把结果交回模型。
# 新增代码+AgentPyPhaseCSkillRuntime: 函数段结束，skill_list 到此结束；若没有这个边界说明，用户不容易看出 skill 列表逻辑已经迁出 agent.py。


def skill_load(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseCSkillRuntime: 函数段开始，执行内置 skill_load 工具；若没有这段函数，模型无法读取本地 skill 说明书。
    skill_name = str(arguments.get("name", "") or "").strip()  # 新增代码+AgentPyPhaseCSkillRuntime: 读取并清理必填 skill 名称；若没有这行代码，工具不知道加载哪个 skill。
    if not skill_name:  # 新增代码+AgentPyPhaseCSkillRuntime: 检查名称是否为空；若没有这行代码，空名称会进入搜索并产生模糊错误。
        return "skill_load 失败：缺少 name 参数。"  # 新增代码+AgentPyPhaseCSkillRuntime: 返回清楚缺参错误；若没有这行代码，模型难以修正工具调用参数。
    max_chars = background_commands_from_runtime.parse_max_chars_value(arguments.get("max_chars"))  # 新增代码+AgentPyPhaseCSkillRuntime: 复用公共输出长度解析函数；若没有这行代码，大 skill 截断规则会和后台命令不一致。
    skills = discover_skills(agent)  # 新增代码+AgentPyPhaseCSkillRuntime: 扫描当前本地 skills；若没有这行代码，加载工具没有安全索引。
    selected_skill = next((skill for skill in skills if str(skill["name"]).lower() == skill_name.lower()), None)  # 新增代码+AgentPyPhaseCSkillRuntime: 按 name 大小写不敏感匹配 skill；若没有这行代码，用户大小写差异会导致加载失败。
    if selected_skill is None:  # 新增代码+AgentPyPhaseCSkillRuntime: 如果没有找到指定名称；若没有这行代码，后续会访问 None 并崩溃。
        return f"skill_load 失败：没有找到名为 {skill_name!r} 的本地 skill，请先调用 skill_list 查看可用名称。"  # 新增代码+AgentPyPhaseCSkillRuntime: 返回可恢复建议；若没有这行代码，模型不知道下一步应该列 skills。
    skill_path = selected_skill["path"]  # 新增代码+AgentPyPhaseCSkillRuntime: 取出已经发现的安全 SKILL.md 或 dynamicprompt 路径；若没有这行代码，无法读取目标说明书。
    try:  # 新增代码+AgentPyPhaseCSkillRuntime: 捕获读取 skill 文件的磁盘异常；若没有这行代码，文件损坏或权限问题会中断整个 agent。
        skill_text = skill_path.read_text(encoding="utf-8", errors="replace")  # 新增代码+AgentPyPhaseCSkillRuntime: 用 UTF-8 读取 skill 内容；若没有这行代码，模型拿不到说明书正文。
    except OSError as error:  # 新增代码+AgentPyPhaseCSkillRuntime: 处理文件读取失败；若没有这行代码，用户会看到底层异常。
        return f"skill_load 失败：无法读取 {selected_skill['relative_path']}：{error}"  # 新增代码+AgentPyPhaseCSkillRuntime: 返回清楚失败原因；若没有这行代码，模型无法解释为什么加载失败。
    truncated_text = skill_text[:max_chars]  # 新增代码+AgentPyPhaseCSkillRuntime: 按 max_chars 截断 skill 正文；若没有这行代码，大 skill 可能撑爆上下文。
    if len(skill_text) > max_chars:  # 新增代码+AgentPyPhaseCSkillRuntime: 检查正文是否被截断；若没有这行代码，模型不知道返回内容是否完整。
        truncated_text += "\n...[skill 内容过长，已截断]..."  # 新增代码+AgentPyPhaseCSkillRuntime: 添加截断提示；若没有这行代码，模型可能误以为加载了完整 skill。
    loaded_skill_name = str(selected_skill["name"])  # 新增代码+AgentPyPhaseCSkillRuntime: 保存已加载 skill 的规范名称；若没有这行代码，后续策略上下文无法知道哪个 skill 已满足。
    agent.tool_policy_context.loaded_skills.add(loaded_skill_name)  # 新增代码+AgentPyPhaseCSkillRuntime: 把原始 skill 名加入 ToolPolicy 上下文；若没有这行代码，needs_skill 工具不会因 skill_load 而解锁。
    agent.tool_policy_context.loaded_skills.add(loaded_skill_name.replace("-", "_"))  # 新增代码+AgentPyPhaseCSkillRuntime: 同时加入下划线别名以匹配 workflow gate 常用命名；若没有这行代码，real-chrome 与 real_chrome 这类名字可能对不上。
    run_helpers_from_core.record_observation(agent, "skill_loaded", {"name": loaded_skill_name, "relative_path": selected_skill["relative_path"]})  # 新增代码+AgentPyPhaseCSkillRuntime: 记录 skill 已加载事件；若没有这行代码，审计看不到 skill gate 是如何满足的。
    return f"skill_load 成功：name={selected_skill['name']}\n路径：{selected_skill['relative_path']}\n说明：{selected_skill['description'] or '(无说明)'}\n内容：\n{truncated_text}"  # 新增代码+AgentPyPhaseCSkillRuntime: 返回元信息和正文；若没有这行代码，模型无法按 skill 说明继续工作。
# 新增代码+AgentPyPhaseCSkillRuntime: 函数段结束，skill_load 到此结束；若没有这个边界说明，用户不容易看出 skill 加载逻辑已经迁出 agent.py。


def discover_skills(agent: Any) -> list[dict[str, Any]]:  # 新增代码+AgentPyPhaseCSkillRuntime: 函数段开始，扫描工作区和包内 skills 并返回元信息；若没有这段函数，skill_list 和 skill_load 会重复扫描逻辑。
    skills: list[dict[str, Any]] = []  # 新增代码+AgentPyPhaseCSkillRuntime: 准备保存扫描到的 skill 元信息；若没有这行代码，无法累积结果。
    seen_skill_names: set[str] = set()  # 新增代码+AgentPyPhaseCSkillRuntime: 记录已发现 skill 名称，优先保留工作区自定义 skill；若没有这行代码，包内和工作区同名 skill 会重复出现并让加载目标不稳定。
    for skills_root in skill_roots(agent):  # 新增代码+AgentPyPhaseCSkillRuntime: 同时扫描工作区 skills 和包内默认 skills；若没有这行代码，runtime 动态化后模型无法发现内置规则包。
        if not skills_root.exists():  # 新增代码+AgentPyPhaseCSkillRuntime: 跳过不存在的 skill 根目录；若没有这行代码，空工作区会让 skill_list 失败。
            continue  # 新增代码+AgentPyPhaseCSkillRuntime: 继续检查其它根目录；若没有这行代码，包内默认 skills 可能因工作区缺目录而无法扫描。
        if not skills_root.is_dir():  # 新增代码+AgentPyPhaseCSkillRuntime: 跳过不是目录的 skill 根路径；若没有这行代码，异常文件路径会进入 glob 并产生误导。
            continue  # 新增代码+AgentPyPhaseCSkillRuntime: 忽略坏根路径继续扫描其它来源；若没有这行代码，单个坏路径会阻断所有 skills。
        for skill_file in sorted(skills_root.glob("*/SKILL.md")):  # 新增代码+AgentPyPhaseCSkillRuntime: 扫描当前根目录的一层 skill 文件；若没有这行代码，工作区和包内规则都不会被发现。
            if not skill_file.is_file():  # 新增代码+AgentPyPhaseCSkillRuntime: 跳过非文件路径；若没有这行代码，特殊文件系统项可能让读取失败。
                continue  # 新增代码+AgentPyPhaseCSkillRuntime: 忽略异常项并继续扫描其他 skills；若没有这行代码，单个坏项会阻断列表。
            try:  # 新增代码+AgentPyPhaseCSkillRuntime: 捕获单个 skill 文件读取异常；若没有这行代码，一个坏 skill 会让全部列表失败。
                skill_text = skill_file.read_text(encoding="utf-8", errors="replace")  # 新增代码+AgentPyPhaseCSkillRuntime: 读取 SKILL.md 内容用于解析 frontmatter；若没有这行代码，无法得到 name/description。
            except OSError:  # 新增代码+AgentPyPhaseCSkillRuntime: 处理读取失败的 skill 文件；若没有这行代码，坏文件会中断扫描。
                continue  # 新增代码+AgentPyPhaseCSkillRuntime: 跳过坏 skill 并继续其他文件；若没有这行代码，用户一个损坏 skill 会影响所有 skill。
            metadata = parse_skill_metadata(skill_text)  # 新增代码+AgentPyPhaseCSkillRuntime: 从 frontmatter 提取 name/description；若没有这行代码，只能使用目录名且缺少说明。
            default_name = skill_file.parent.name  # 新增代码+AgentPyPhaseCSkillRuntime: 用目录名作为默认 skill 名；若没有这行代码，缺 name 的 skill 无法被加载。
            skill_name = str(metadata.get("name", "") or default_name).strip()  # 新增代码+AgentPyPhaseCSkillRuntime: 优先使用 metadata.name 并清理空白；若没有这行代码，名称可能为空或包含多余空格。
            if not skill_name:  # 新增代码+AgentPyPhaseCSkillRuntime: 跳过仍然没有名称的异常 skill；若没有这行代码，空名称会让 skill_load 匹配混乱。
                continue  # 新增代码+AgentPyPhaseCSkillRuntime: 忽略坏 skill 并继续扫描；若没有这行代码，空名称会进入结果列表。
            skill_key = skill_name.lower()  # 新增代码+AgentPyPhaseCSkillRuntime: 用小写名称做去重键；若没有这行代码，大小写不同的同名 skill 会重复出现。
            if skill_key in seen_skill_names:  # 新增代码+AgentPyPhaseCSkillRuntime: 如果工作区或更早根目录已经提供同名 skill；若没有这行代码，包内默认 skill 可能覆盖用户自定义 skill。
                continue  # 新增代码+AgentPyPhaseCSkillRuntime: 保留先发现的 skill 并跳过重复项；若没有这行代码，skill_load 的匹配结果会不稳定。
            seen_skill_names.add(skill_key)  # 新增代码+AgentPyPhaseCSkillRuntime: 记录该 skill 已被收录；若没有这行代码，后续重复项无法过滤。
            description = str(metadata.get("description", "") or "").strip()  # 新增代码+AgentPyPhaseCSkillRuntime: 读取并清理描述；若没有这行代码，列表缺少说明或显示 None。
            skills.append({"name": skill_name, "description": description, "path": skill_file, "relative_path": skill_relative_path(agent, skill_file)})  # 新增代码+AgentPyPhaseCSkillRuntime: 保存完整元信息；若没有这行代码，列表和加载工具拿不到目标数据。
    dynamic_prompt_skill = dynamic_prompt_skill_metadata(agent)  # 新增代码+AgentPyPhaseCSkillRuntime: 把 dynamicprompt.md 暴露成可按需加载的伪 skill；若没有这行代码，动态规则文件虽然存在但模型很难用 skill_load 找到。
    if dynamic_prompt_skill is not None:  # 新增代码+AgentPyPhaseCSkillRuntime: 只有动态提示词文件可读时才加入列表；若没有这行代码，缺失文件会在 skill_list 里显示成不可加载入口。
        dynamic_prompt_key = str(dynamic_prompt_skill["name"]).lower()  # 新增代码+AgentPyPhaseCSkillRuntime: 计算伪 skill 的去重键；若没有这行代码，用户自定义同名 skill 无法优先覆盖。
        if dynamic_prompt_key not in seen_skill_names:  # 新增代码+AgentPyPhaseCSkillRuntime: 避免和真实 dynamicprompt skill 重复；若没有这行代码，skill_load 可能命中不稳定。
            skills.append(dynamic_prompt_skill)  # 新增代码+AgentPyPhaseCSkillRuntime: 加入动态提示词伪 skill；若没有这行代码，skill_list 看不到按需运行规则索引。
    return skills  # 新增代码+AgentPyPhaseCSkillRuntime: 返回真实 skills 加 dynamicprompt 入口；若没有这行代码，调用方无法使用本地 skills。
# 新增代码+AgentPyPhaseCSkillRuntime: 函数段结束，discover_skills 到此结束；若没有这个边界说明，用户不容易看出 skill 扫描逻辑已经迁出 agent.py。


def dynamic_prompt_skill_metadata(agent: Any) -> dict[str, Any] | None:  # 新增代码+AgentPyPhaseCSkillRuntime: 函数段开始，生成 dynamicprompt.md 的 skill 元信息；若没有这段函数，动态提示词不能复用 skill_load 读取通道。
    return dynamic_prompt_skill_metadata_from_prompts(agent.dynamic_prompt_path, relative_path=skill_relative_path(agent, agent.dynamic_prompt_path))  # 新增代码+AgentPyPhaseCSkillRuntime: 委托 prompts.dynamic_prompt 生成伪 skill 元信息；若没有这行代码，dynamicprompt 的存在性和目录判断会散回 agent.py。
# 新增代码+AgentPyPhaseCSkillRuntime: 函数段结束，dynamic_prompt_skill_metadata 到此结束；若没有这个边界说明，用户不容易看出 dynamicprompt 元信息也属于 skill runtime。


def skill_roots(agent: Any) -> list[Path]:  # 新增代码+AgentPyPhaseCSkillRuntime: 函数段开始，返回按优先级扫描的 skill 根目录；若没有这段函数，skill_list 只能看工作区而无法加载包内动态规则。
    roots: list[Path] = []  # 新增代码+AgentPyPhaseCSkillRuntime: 准备保存去重后的根目录；若没有这行代码，后续无法累积工作区和包内路径。
    seen_roots: set[Path] = set()  # 新增代码+AgentPyPhaseCSkillRuntime: 记录已加入的解析路径；若没有这行代码，workspace 正好是 learning_agent 目录时会重复扫描同一 skills。
    for candidate in [agent.skills_path, Path(__file__).resolve().parent]:  # 新增代码+AgentPyPhaseCSkillRuntime: 工作区 skills 优先，再回退到 learning_agent/skills；若没有这行代码，包内默认规则 skill 无法被发现。
        try:  # 新增代码+AgentPyPhaseCSkillRuntime: 规范化路径用于去重；若没有这行代码，符号链接或相对路径可能导致重复扫描。
            resolved_candidate = candidate.resolve()  # 新增代码+AgentPyPhaseCSkillRuntime: 解析绝对路径；若没有这行代码，seen_roots 可能无法识别同一目录。
        except OSError:  # 新增代码+AgentPyPhaseCSkillRuntime: 防御路径解析失败；若没有这行代码，异常路径会打断 skill 发现。
            resolved_candidate = candidate  # 新增代码+AgentPyPhaseCSkillRuntime: 解析失败时使用原路径继续；若没有这行代码，坏路径没有可去重标识。
        if resolved_candidate in seen_roots:  # 新增代码+AgentPyPhaseCSkillRuntime: 跳过已经加入的根目录；若没有这行代码，同一路径会重复列出 skills。
            continue  # 新增代码+AgentPyPhaseCSkillRuntime: 继续检查下一个候选根；若没有这行代码，重复目录仍会被加入结果。
        seen_roots.add(resolved_candidate)  # 新增代码+AgentPyPhaseCSkillRuntime: 标记该根目录已加入；若没有这行代码，后续重复候选无法识别。
        roots.append(candidate)  # 新增代码+AgentPyPhaseCSkillRuntime: 保留原始 Path 供 glob 使用；若没有这行代码，调用方拿不到可扫描路径。
    return roots  # 新增代码+AgentPyPhaseCSkillRuntime: 返回有序根目录列表；若没有这行代码，discover_skills 无法遍历 skill 来源。
# 新增代码+AgentPyPhaseCSkillRuntime: 函数段结束，skill_roots 到此结束；若没有这个边界说明，用户不容易看出 skill 根目录逻辑已经迁出 agent.py。


def parse_skill_metadata(skill_text: str) -> dict[str, str]:  # 新增代码+AgentPyPhaseCSkillRuntime: 函数段开始，解析 SKILL.md 顶部简单 frontmatter；若没有这段函数，skill_list 无法显示 name/description。
    lines = skill_text.splitlines()  # 新增代码+AgentPyPhaseCSkillRuntime: 按行拆分 skill 文本；若没有这行代码，无法定位 frontmatter 边界。
    if not lines or lines[0].strip() != "---":  # 新增代码+AgentPyPhaseCSkillRuntime: 只有第一行是 --- 才按 frontmatter 解析；若没有这行代码，普通 Markdown 可能被误解析。
        return {}  # 新增代码+AgentPyPhaseCSkillRuntime: 没有 frontmatter 时返回空元信息；若没有这行代码，调用方无法使用默认目录名。
    metadata: dict[str, str] = {}  # 新增代码+AgentPyPhaseCSkillRuntime: 准备保存 key/value 元信息；若没有这行代码，无处累积解析结果。
    for line in lines[1:]:  # 新增代码+AgentPyPhaseCSkillRuntime: 从第二行开始读取 frontmatter 内容；若没有这行代码，会把起始 --- 当作字段。
        if line.strip() == "---":  # 新增代码+AgentPyPhaseCSkillRuntime: 遇到结束分隔符停止解析；若没有这行代码，正文里的冒号可能被误当元信息。
            break  # 新增代码+AgentPyPhaseCSkillRuntime: 结束 frontmatter 扫描；若没有这行代码，后续 Markdown 正文会污染 metadata。
        if ":" not in line:  # 新增代码+AgentPyPhaseCSkillRuntime: 跳过没有冒号的行；若没有这行代码，非 key/value 行会解析失败。
            continue  # 新增代码+AgentPyPhaseCSkillRuntime: 继续处理下一行；若没有这行代码，单个非标准行会影响后续字段。
        key, value = line.split(":", 1)  # 新增代码+AgentPyPhaseCSkillRuntime: 按第一个冒号拆分 key 和 value；若没有这行代码，description 中的冒号会被错误拆多段。
        clean_key = key.strip()  # 新增代码+AgentPyPhaseCSkillRuntime: 清理字段名空白；若没有这行代码，" name" 这类字段无法识别。
        clean_value = value.strip().strip("\"'")  # 新增代码+AgentPyPhaseCSkillRuntime: 清理字段值空白和常见引号；若没有这行代码，输出会包含多余引号。
        if clean_key:  # 新增代码+AgentPyPhaseCSkillRuntime: 只保存非空字段名；若没有这行代码，空 key 会污染 metadata。
            metadata[clean_key] = clean_value  # 新增代码+AgentPyPhaseCSkillRuntime: 保存解析出的元信息；若没有这行代码，name/description 不会返回。
    return metadata  # 新增代码+AgentPyPhaseCSkillRuntime: 返回解析结果；若没有这行代码，调用方拿不到 skill 元信息。
# 新增代码+AgentPyPhaseCSkillRuntime: 函数段结束，parse_skill_metadata 到此结束；若没有这个边界说明，用户不容易看出 frontmatter 解析逻辑已经迁出 agent.py。


def skill_relative_path(agent: Any, skill_file: Path) -> str:  # 新增代码+AgentPyPhaseCSkillRuntime: 函数段开始，把 skill 文件路径转成工作区相对文本；若没有这段函数，输出会暴露冗长绝对路径。
    try:  # 新增代码+AgentPyPhaseCSkillRuntime: 尝试计算相对路径；若没有这行代码，Windows 路径边界异常会直接抛出。
        relative_path = skill_file.resolve().relative_to(agent.workspace)  # 新增代码+AgentPyPhaseCSkillRuntime: 计算相对于工作区的路径；若没有这行代码，用户难以定位 skill 文件在项目中的位置。
    except ValueError:  # 新增代码+AgentPyPhaseCSkillRuntime: 防御路径不在工作区内的极端情况；若没有这行代码，异常路径会中断 skill 列表。
        return str(skill_file)  # 新增代码+AgentPyPhaseCSkillRuntime: 兜底返回原始路径文本；若没有这行代码，异常路径没有可展示内容。
    return relative_path.as_posix()  # 新增代码+AgentPyPhaseCSkillRuntime: 使用正斜杠输出相对路径；若没有这行代码，Windows 反斜杠会让测试和模型阅读不统一。
# 新增代码+AgentPyPhaseCSkillRuntime: 函数段结束，skill_relative_path 到此结束；若没有这个边界说明，用户不容易看出路径显示逻辑已经迁出 agent.py。
