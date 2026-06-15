"""动态提示词读取门禁和提示词文件运行时。"""  # 新增代码+AgentPyPhaseIDynamicGate: 把 dynamicprompt/staticprompt 路径读取、分层门禁和读后工具包解锁从 agent.py 移到 prompts 层；若没有这个文件，主 agent 会继续承载提示词门禁细节。

from __future__ import annotations  # 新增代码+AgentPyPhaseIDynamicGate: 延迟解析类型注解，降低脚本模式导入顺序风险；若没有这行代码，复杂注解可能提前求值失败。

from pathlib import Path  # 新增代码+AgentPyPhaseIDynamicGate: 动态提示词门禁和上下文文件读取都需要 Path 处理跨平台路径；若没有这行代码，只能用脆弱字符串拼路径。
from typing import Any  # 新增代码+AgentPyPhaseIDynamicGate: 用 Any 表示传入的 agent duck type；若没有这行代码，本模块会为了类型注解反向导入 LearningAgent。

try:  # 新增代码+AgentPyPhaseIDynamicGate: 包运行模式下导入提示词、工具策略和观察依赖；若没有这行代码，prompts 层无法承接真实门禁实现。
    import learning_agent.core.run_helpers as run_helpers_from_core  # 新增代码+AgentPyPhaseIDynamicGate: 导入 observation helper；若没有这行代码，动态 skill 解锁后无法留下审计事件。
    import learning_agent.prompts.dynamic_prompt as dynamic_prompt_from_prompts  # 新增代码+AgentPyPhaseIDynamicGate: 导入 dynamicprompt 路径和伪 skill 元信息 helper；若没有这行代码，动态规则入口会断开。
    import learning_agent.prompts.static_prompt as static_prompt_from_prompts  # 新增代码+AgentPyPhaseIDynamicGate: 导入 staticprompt 读取、兜底和路径 helper；若没有这行代码，静态提示词入口会断开。
    import learning_agent.tools.catalog_runtime as catalog_runtime_from_tools  # 新增代码+AgentPyPhaseIDynamicGate: 导入工具目录和策略运行时；若没有这行代码，读 skill 后无法按统一策略解锁工具。
    import learning_agent.tools.search as search_tools_from_tools  # 新增代码+AgentPyPhaseIDynamicGate: 导入能力包查找 helper；若没有这行代码，skill 名无法转换成具体工具列表。
    from learning_agent.core.config import get_local_iso_date  # 新增代码+AgentPyPhaseIDynamicGate: 导入本地日期 helper；若没有这行代码，staticprompt 占位符渲染无法获得当前日期。
    from learning_agent.tools.schemas import DYNAMIC_SKILL_CAPABILITY_PACKS  # 新增代码+AgentPyPhaseIDynamicGate: 导入动态 skill 到能力包的映射；若没有这行代码，读取 browser_automation 等 skill 不会解锁对应工具。
except ModuleNotFoundError as error:  # 新增代码+AgentPyPhaseIDynamicGate: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀缺失会导致启动失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.config", "learning_agent.core.run_helpers", "learning_agent.prompts", "learning_agent.prompts.dynamic_prompt", "learning_agent.prompts.static_prompt", "learning_agent.tools", "learning_agent.tools.catalog_runtime", "learning_agent.tools.search", "learning_agent.tools.schemas"}:  # 新增代码+AgentPyPhaseIDynamicGate: 只允许路径模式差异进入 fallback；若没有这行代码，内部真实导入错误会被误吞。
        raise  # 新增代码+AgentPyPhaseIDynamicGate: 重新抛出真正的导入错误；若没有这行代码，排查动态提示词问题会看不到根因。
    import core.run_helpers as run_helpers_from_core  # 新增代码+AgentPyPhaseIDynamicGate: 脚本模式下导入 observation helper；若没有这行代码，bat 入口动态 skill 解锁无法审计。
    import prompts.dynamic_prompt as dynamic_prompt_from_prompts  # 新增代码+AgentPyPhaseIDynamicGate: 脚本模式下导入 dynamicprompt helper；若没有这行代码，bat 入口动态规则路径会断开。
    import prompts.static_prompt as static_prompt_from_prompts  # 新增代码+AgentPyPhaseIDynamicGate: 脚本模式下导入 staticprompt helper；若没有这行代码，bat 入口静态提示词加载会断开。
    import tools.catalog_runtime as catalog_runtime_from_tools  # 新增代码+AgentPyPhaseIDynamicGate: 脚本模式下导入工具策略运行时；若没有这行代码，bat 入口动态 skill 解锁会断开。
    import tools.search as search_tools_from_tools  # 新增代码+AgentPyPhaseIDynamicGate: 脚本模式下导入能力包查找 helper；若没有这行代码，bat 入口无法把 skill 映射为工具。
    from core.config import get_local_iso_date  # 新增代码+AgentPyPhaseIDynamicGate: 脚本模式下导入本地日期 helper；若没有这行代码，bat 入口 staticprompt 渲染会断开。
    from tools.schemas import DYNAMIC_SKILL_CAPABILITY_PACKS  # 新增代码+AgentPyPhaseIDynamicGate: 脚本模式下导入动态 skill 映射；若没有这行代码，bat 入口读取 skill 后不会加载工具包。


def read_static_prompt(agent: Any) -> str:  # 新增代码+AgentPyPhaseIDynamicGate: 函数段开始，读取 staticprompt.md 并渲染工作区和日期；若没有这段函数，agent.py 仍要直接处理静态提示词读取。
    return static_prompt_from_prompts.read_static_prompt(agent.static_prompt_path, workspace=agent.workspace, current_date=get_local_iso_date())  # 新增代码+AgentPyPhaseIDynamicGate: 委托 static_prompt 模块读取和渲染；若没有这行代码，静态提示词正文无法进入系统提示词。
# 新增代码+AgentPyPhaseIDynamicGate: 函数段结束，read_static_prompt 到此结束；若没有这个边界说明，用户不容易看出这里只有静态提示词读取职责。


def fallback_static_prompt(agent: Any, reason: str) -> str:  # 新增代码+AgentPyPhaseIDynamicGate: 函数段开始，生成 staticprompt 缺失或损坏时的兜底提示词；若没有这段函数，坏提示词文件会打断 agent。
    return static_prompt_from_prompts.fallback_static_prompt(reason, workspace=agent.workspace, current_date=get_local_iso_date())  # 新增代码+AgentPyPhaseIDynamicGate: 委托 static_prompt 模块生成兜底文本；若没有这行代码，异常状态下没有最小安全提示词。
# 新增代码+AgentPyPhaseIDynamicGate: 函数段结束，fallback_static_prompt 到此结束；若没有这个边界说明，用户不容易看出这里只有兜底构造职责。


def resolve_static_prompt_path(agent: Any) -> Path:  # 新增代码+AgentPyPhaseIDynamicGate: 函数段开始，解析 staticprompt.md 路径；若没有这段函数，工作区覆盖和包内默认路径规则会继续留在 agent.py。
    return static_prompt_from_prompts.resolve_static_prompt_path(agent.workspace)  # 新增代码+AgentPyPhaseIDynamicGate: 委托 static_prompt 模块选择工作区或默认路径；若没有这行代码，staticprompt 路径无法稳定解析。
# 新增代码+AgentPyPhaseIDynamicGate: 函数段结束，resolve_static_prompt_path 到此结束；若没有这个边界说明，用户不容易看出这里只有路径解析职责。


def resolve_dynamic_prompt_path(agent: Any) -> Path:  # 新增代码+AgentPyPhaseIDynamicGate: 函数段开始，解析 dynamicprompt.md 路径；若没有这段函数，动态规则入口路径会继续留在 agent.py。
    return dynamic_prompt_from_prompts.resolve_dynamic_prompt_path(agent.workspace)  # 新增代码+AgentPyPhaseIDynamicGate: 委托 dynamic_prompt 模块选择工作区或默认路径；若没有这行代码，dynamicprompt 路径无法稳定解析。
# 新增代码+AgentPyPhaseIDynamicGate: 函数段结束，resolve_dynamic_prompt_path 到此结束；若没有这个边界说明，用户不容易看出这里只有动态路径解析职责。


def read_prompt_context_file(file_path: Path, max_chars: int) -> str:  # 新增代码+AgentPyPhaseIDynamicGate: 函数段开始，读取单个项目上下文文件并控制长度；若没有这段函数，三件套上下文读取会继续留在 agent.py。
    if not file_path.exists():  # 新增代码+AgentPyPhaseIDynamicGate: 检查文件是否存在；若没有这行代码，缺文件会抛底层异常而不是可读提示。
        return f"{file_path.name} 不存在。"  # 新增代码+AgentPyPhaseIDynamicGate: 返回具体缺失文件名；若没有这行代码，模型不知道哪个上下文文件少了。
    if file_path.is_dir():  # 新增代码+AgentPyPhaseIDynamicGate: 防御同名路径是目录；若没有这行代码，read_text 读取目录会崩溃。
        return f"{file_path.name} 是目录，无法读取。"  # 新增代码+AgentPyPhaseIDynamicGate: 返回目录不可读说明；若没有这行代码，用户难以理解加载失败原因。
    text = file_path.read_text(encoding="utf-8", errors="replace")  # 新增代码+AgentPyPhaseIDynamicGate: 用 UTF-8 读取上下文文件；若没有这行代码，中文项目记忆无法进入上下文。
    if len(text) <= max_chars:  # 新增代码+AgentPyPhaseIDynamicGate: 判断文件是否能完整返回；若没有这行代码，小文件也会被不必要截断。
        return text if text.strip() else f"{file_path.name} 当前为空。"  # 新增代码+AgentPyPhaseIDynamicGate: 返回原文或空文件说明；若没有这行代码，空文件会变成难以察觉的空区块。
    head_chars = max_chars // 2  # 新增代码+AgentPyPhaseIDynamicGate: 计算首部保留长度；若没有这行代码，长文件首尾摘要无法保留开头背景。
    tail_chars = max_chars - head_chars  # 新增代码+AgentPyPhaseIDynamicGate: 计算尾部保留长度；若没有这行代码，长文件首尾摘要无法保留最新记录。
    return text[:head_chars] + "\n...[项目上下文过长，已保留开头和末尾]...\n" + text[-tail_chars:]  # 新增代码+AgentPyPhaseIDynamicGate: 返回首尾摘要；若没有这行代码，长上下文要么撑爆 prompt 要么完全丢失最新进度。
# 新增代码+AgentPyPhaseIDynamicGate: 函数段结束，read_prompt_context_file 到此结束；若没有这个边界说明，用户不容易看出上下文读取范围。


def dynamic_prompt_skill_metadata(agent: Any) -> dict[str, Any] | None:  # 新增代码+AgentPyPhaseIDynamicGate: 函数段开始，生成 dynamicprompt.md 的伪 skill 元信息；若没有这段函数，旧入口无法按 skill 方式发现动态规则。
    return dynamic_prompt_from_prompts.dynamic_prompt_skill_metadata(agent.dynamic_prompt_path, relative_path=skill_relative_path(agent, agent.dynamic_prompt_path))  # 新增代码+AgentPyPhaseIDynamicGate: 委托 dynamic_prompt 模块生成元信息并复用本模块相对路径；若没有这行代码，dynamicprompt 无法出现在 skill_list。
# 新增代码+AgentPyPhaseIDynamicGate: 函数段结束，dynamic_prompt_skill_metadata 到此结束；若没有这个边界说明，用户不容易看出伪 skill 元信息范围。


def skill_relative_path(agent: Any, skill_file: Path) -> str:  # 新增代码+AgentPyPhaseIDynamicGate: 函数段开始，把提示词或 skill 文件路径转成用户可读相对路径；若没有这段函数，dynamicprompt 元信息无法显示稳定路径。
    try:  # 新增代码+AgentPyPhaseIDynamicGate: 尝试按当前 workspace 计算相对路径；若没有这行代码，工作区内文件会显示冗长绝对路径。
        return skill_file.resolve().relative_to(agent.workspace).as_posix()  # 新增代码+AgentPyPhaseIDynamicGate: 返回 POSIX 风格相对路径；若没有这行代码，Windows 反斜杠会影响提示词路径说明。
    except ValueError:  # 新增代码+AgentPyPhaseIDynamicGate: 处理包内默认文件不在当前 workspace 内的情况；若没有这行代码，relative_to 失败会抛异常。
        return str(skill_file)  # 新增代码+AgentPyPhaseIDynamicGate: 回退为原始路径文本；若没有这行代码，包内默认 dynamicprompt 无法展示路径。
# 新增代码+AgentPyPhaseIDynamicGate: 函数段结束，skill_relative_path 到此结束；若没有这个边界说明，用户不容易看出相对路径规则。


def dynamic_prompt_read_key(agent: Any, path: Path) -> str | None:  # 新增代码+AgentPyPhaseIDynamicGate: 函数段开始，把工作区内提示词路径转成稳定 key；若没有这段函数，read 门控无法知道哪些父层已经读取。
    try:  # 新增代码+AgentPyPhaseIDynamicGate: 捕获 path 不在工作区内的情况；若没有这行代码，relative_to 失败会打断普通 read。
        relative_path = path.resolve().relative_to(agent.workspace)  # 新增代码+AgentPyPhaseIDynamicGate: 计算相对工作区路径；若没有这行代码，绝对路径无法和提示词层级规则匹配。
    except ValueError:  # 新增代码+AgentPyPhaseIDynamicGate: 处理不属于当前 workspace 的路径；若没有这行代码，外部路径会产生异常。
        return None  # 新增代码+AgentPyPhaseIDynamicGate: 非工作区路径不参与动态提示词门控；若没有这行代码，普通安全错误可能被误判为提示词层级问题。
    return relative_path.as_posix().lower()  # 新增代码+AgentPyPhaseIDynamicGate: 用小写 POSIX 路径做 key；若没有这行代码，Windows 大小写和反斜杠会导致同一文件匹配不上。
# 新增代码+AgentPyPhaseIDynamicGate: 函数段结束，dynamic_prompt_read_key 到此结束；若没有这个边界说明，用户不容易看出 key 生成范围。


def dynamic_prompt_skill_base(read_key: str) -> str | None:  # 新增代码+AgentPyPhaseIDynamicGate: 函数段开始，判断路径是否属于 skills 动态提示词树；若没有这段函数，read 无法区分普通文件和分层提示词。
    if read_key.startswith("learning_agent/skills/"):  # 新增代码+AgentPyPhaseIDynamicGate: 支持项目根工作区下的 learning_agent/skills 路径；若没有这行代码，当前项目默认路径不会被门控。
        return "learning_agent/skills"  # 新增代码+AgentPyPhaseIDynamicGate: 返回项目根模式的技能根；若没有这行代码，后续无法拼出父层 key。
    if read_key.startswith("skills/"):  # 新增代码+AgentPyPhaseIDynamicGate: 支持工作区本身就是 learning_agent 包目录的路径；若没有这行代码，包目录作为工作区时分层会失效。
        return "skills"  # 新增代码+AgentPyPhaseIDynamicGate: 返回包目录模式的技能根；若没有这行代码，后续无法拼出父层 key。
    return None  # 新增代码+AgentPyPhaseIDynamicGate: 普通文件不属于动态提示词树；若没有这行代码，read 可能错误拦截代码文件。
# 新增代码+AgentPyPhaseIDynamicGate: 函数段结束，dynamic_prompt_skill_base 到此结束；若没有这个边界说明，用户不容易看出 skill 根判断范围。


def dynamic_prompt_read_gate(agent: Any, path: Path) -> str | None:  # 新增代码+AgentPyPhaseIDynamicGate: 函数段开始，检查 read 是否跳过 tool_list 或父 SKILL；若没有这段函数，三级动态提示词树只能靠模型自觉遵守。
    read_key = dynamic_prompt_read_key(agent, path)  # 新增代码+AgentPyPhaseIDynamicGate: 取得当前读取文件的稳定 key；若没有这行代码，门控没有判断对象。
    if read_key is None:  # 新增代码+AgentPyPhaseIDynamicGate: 如果路径不在 workspace 内；若没有这行代码，后续字符串判断可能拿到 None。
        return None  # 新增代码+AgentPyPhaseIDynamicGate: 非 workspace 路径交给原有边界处理；若没有这行代码，提示词门控会越权处理普通错误。
    skill_base = dynamic_prompt_skill_base(read_key)  # 新增代码+AgentPyPhaseIDynamicGate: 判断当前路径是否在 skills 动态树内；若没有这行代码，无法只门控提示词文件。
    if skill_base is None:  # 新增代码+AgentPyPhaseIDynamicGate: 普通代码、README、配置不属于动态提示词树；若没有这行代码，read 可能误拦截项目文件。
        return None  # 新增代码+AgentPyPhaseIDynamicGate: 普通文件允许按原流程读取；若没有这行代码，agent 会无法正常读代码。
    tool_list_key = f"{skill_base}/tool_list.md"  # 新增代码+AgentPyPhaseIDynamicGate: 计算第一层总索引 key；若没有这行代码，后续无法判断 tool_list 是否已读。
    if read_key == tool_list_key:  # 新增代码+AgentPyPhaseIDynamicGate: 总索引本身必须可直接读取；若没有这行代码，模型永远无法进入动态规则树。
        return None  # 新增代码+AgentPyPhaseIDynamicGate: 允许读取第一层索引；若没有这行代码，分层门控会变成死锁。
    relative_under_skills = read_key.removeprefix(f"{skill_base}/")  # 新增代码+AgentPyPhaseIDynamicGate: 取出 skills 根目录下的相对路径；若没有这行代码，无法解析 skill 名和 rules 层。
    parts = relative_under_skills.split("/")  # 新增代码+AgentPyPhaseIDynamicGate: 按路径段拆分；若没有这行代码，无法判断是否为 <skill>/SKILL.md 或 <skill>/rules/*.md。
    if len(parts) >= 2 and parts[1] == "skill.md" and tool_list_key not in agent.loaded_dynamic_prompt_paths:  # 新增代码+AgentPyPhaseIDynamicGate: 读取第二层 SKILL 前必须读第一层索引；若没有这行代码，模型可以绕过总目录直接猜 skill 路径。
        return f"read 失败：动态提示词分层要求先读取 {tool_list_key}，再读取目标 SKILL.md。"  # 新增代码+AgentPyPhaseIDynamicGate: 返回可恢复的父层提示；若没有这行代码，模型不知道下一步该读哪个文件。
    if len(parts) >= 3 and parts[1] == "rules":  # 新增代码+AgentPyPhaseIDynamicGate: 识别第三层子规则文件；若没有这行代码，rules 文件不会受父层保护。
        parent_skill_key = f"{skill_base}/{parts[0]}/skill.md"  # 新增代码+AgentPyPhaseIDynamicGate: 计算该子规则对应的父 SKILL key；若没有这行代码，无法检查第二层是否已读。
        parent_skill_path = f"{skill_base}/{parts[0]}/SKILL.md"  # 新增代码+AgentPyPhaseIDynamicGate: 准备给模型看的父 SKILL 路径；若没有这行代码，错误提示会显示小写 skill.md 不利于用户定位。
        if tool_list_key not in agent.loaded_dynamic_prompt_paths:  # 新增代码+AgentPyPhaseIDynamicGate: 子规则读取前先要求第一层索引；若没有这行代码，模型仍可直接跳进 rules 目录。
            return f"read 失败：动态提示词子规则需要先读取 {tool_list_key}，再读取 {parent_skill_path}。"  # 新增代码+AgentPyPhaseIDynamicGate: 返回第一层缺失提示；若没有这行代码，模型不知道要从总目录开始。
        if parent_skill_key not in agent.loaded_dynamic_prompt_paths:  # 新增代码+AgentPyPhaseIDynamicGate: 子规则读取前再要求第二层父 skill；若没有这行代码，模型会跳过能力边界说明。
            return f"read 失败：动态提示词子规则需要先读取 {parent_skill_path}。"  # 新增代码+AgentPyPhaseIDynamicGate: 返回第二层缺失提示；若没有这行代码，模型不知道要先读哪个父文件。
    return None  # 新增代码+AgentPyPhaseIDynamicGate: 没有违反层级时允许 read 继续；若没有这行代码，合法提示词读取会被错误拒绝。
# 新增代码+AgentPyPhaseIDynamicGate: 函数段结束，dynamic_prompt_read_gate 到此结束；若没有这个边界说明，用户不容易看出分层门禁范围。


def dynamic_skill_name_from_read_key(read_key: str) -> str:  # 新增代码+AgentPyPhaseIDynamicGate: 函数段开始，从已读取的动态提示词路径解析 skill 名；若没有这段函数，read 无法知道应该激活哪个能力包。
    skill_base = dynamic_prompt_skill_base(read_key)  # 新增代码+AgentPyPhaseIDynamicGate: 先判断路径是否属于 skills 动态提示词树；若没有这行代码，普通代码读取也可能被误当成 skill。
    if skill_base is None:  # 新增代码+AgentPyPhaseIDynamicGate: 非 skill 路径不应该触发工具解锁；若没有这行代码，读取任意文件都可能污染工具池。
        return ""  # 新增代码+AgentPyPhaseIDynamicGate: 返回空字符串表达没有 skill 名；若没有这行代码，调用方需要处理 None 分支。
    relative_under_skills = read_key.removeprefix(f"{skill_base}/")  # 新增代码+AgentPyPhaseIDynamicGate: 取得 skills 根目录下的相对路径；若没有这行代码，无法从 learning_agent/skills/browser_automation/SKILL.md 中提取 browser_automation。
    parts = relative_under_skills.split("/")  # 新增代码+AgentPyPhaseIDynamicGate: 按路径段拆分 skill 名、SKILL.md 和 rules 层；若没有这行代码，后续判断只能做脆弱字符串匹配。
    if len(parts) < 2:  # 新增代码+AgentPyPhaseIDynamicGate: tool_list.md 这类第一层索引没有第二段；若没有这行代码，读取总索引也会被误识别成 skill。
        return ""  # 新增代码+AgentPyPhaseIDynamicGate: 第一层索引不解锁具体工具包；若没有这行代码，读 tool_list 会一次性打开太多能力。
    if parts[1] not in {"skill.md", "rules"}:  # 新增代码+AgentPyPhaseIDynamicGate: 只有第二层 SKILL 或第三层 rules 才代表进入某个具体 skill；若没有这行代码，skill 目录里的杂项文件也会触发工具加载。
        return ""  # 新增代码+AgentPyPhaseIDynamicGate: 非标准动态提示词文件不触发解锁；若没有这行代码，工具池状态会难以审计。
    return parts[0].strip().lower().replace("-", "_")  # 新增代码+AgentPyPhaseIDynamicGate: 规范化 skill 名用于映射能力包；若没有这行代码，real-chrome 和 real_chrome 这类写法无法统一匹配。
# 新增代码+AgentPyPhaseIDynamicGate: 函数段结束，dynamic_skill_name_from_read_key 到此结束；若没有这个边界说明，用户不容易看出 skill 名解析范围。


def load_tools_for_dynamic_skill_read(agent: Any, read_key: str) -> None:  # 新增代码+AgentPyPhaseIDynamicGate: 函数段开始，根据已读取的动态 skill 激活对应工具包；若没有这段函数，极简 read-based 路由无法真正调用浏览器 MCP 工具。
    skill_name = dynamic_skill_name_from_read_key(read_key)  # 新增代码+AgentPyPhaseIDynamicGate: 解析当前 read 事件对应的 skill 名；若没有这行代码，后续不知道查哪个能力包映射。
    if not skill_name:  # 新增代码+AgentPyPhaseIDynamicGate: 没有具体 skill 时不做任何工具池变更；若没有这行代码，读取 tool_list 或普通文件可能误触发加载。
        return  # 新增代码+AgentPyPhaseIDynamicGate: 提前结束无关读取；若没有这行代码，空 skill 名会继续查映射造成噪声。
    pack_names = DYNAMIC_SKILL_CAPABILITY_PACKS.get(skill_name, ())  # 新增代码+AgentPyPhaseIDynamicGate: 查找该 skill 可解锁的能力包列表；若没有这行代码，浏览器 skill 和真实工具包无法建立关系。
    if not pack_names:  # 新增代码+AgentPyPhaseIDynamicGate: 没有映射的 skill 仍只作为提示词加载；若没有这行代码，普通 skill 可能因为没有工具包而报错。
        return  # 新增代码+AgentPyPhaseIDynamicGate: 对无工具包 skill 保持安静返回；若没有这行代码，动态提示词读取会产生无意义失败。
    agent.tool_policy_context.loaded_skills.add(skill_name)  # 新增代码+AgentPyPhaseIDynamicGate: 把已读 skill 记录进 ToolPolicy 上下文；若没有这行代码，real_chrome 这类 skill gate 永远不会满足。
    if skill_name == "real_chrome":  # 新增代码+AgentPyPhaseIDynamicGate: 读取 real_chrome skill 等价于用户或模型正在进入真实 Chrome 路线；若没有这行代码，普通 browser_open 可能在连接前过早可见。
        agent.real_chrome_requested = True  # 新增代码+AgentPyPhaseIDynamicGate: 启用真实 Chrome workflow 拦截普通独立浏览器动作；若没有这行代码，真实登录态需求可能误走独立 Chromium。
    loaded_names: list[str] = []  # 新增代码+AgentPyPhaseIDynamicGate: 保存本次真正加入 loaded_tool_names 的工具名；若没有这行代码，观察事件无法说明解锁了哪些工具。
    for pack_name in pack_names:  # 新增代码+AgentPyPhaseIDynamicGate: 遍历一个 skill 对应的一个或多个能力包；若没有这行代码，real_chrome 无法同时准备连接和页面操作能力。
        agent.tool_policy_context.loaded_skills.add(pack_name)  # 新增代码+AgentPyPhaseIDynamicGate: 也把能力包名记为已加载 skill 语义；若没有这行代码，skill_gate 使用包名时无法匹配。
        for tool in search_tools_from_tools.capability_pack_tools(agent, pack_name):  # 新增代码+AgentPyPhaseIDynamicGate: 遍历能力包下的全部 catalog 工具；若没有这行代码，无法把包名转换成具体 MCP 工具。
            decision = catalog_runtime_from_tools.tool_policy_decision(agent, tool)  # 新增代码+AgentPyPhaseIDynamicGate: 读取当前策略状态避免加载被 deny 的工具；若没有这行代码，read skill 会绕过统一 ToolPolicy。
            if decision.state == "blocked":  # 新增代码+AgentPyPhaseIDynamicGate: 被安全策略明确阻断的工具不能仅因读了 skill 就加入；若没有这行代码，deny 规则会被动态提示词绕开。
                continue  # 新增代码+AgentPyPhaseIDynamicGate: 跳过阻断工具并继续同包其他工具；若没有这行代码，一个 blocked 工具会影响整个包加载。
            agent.loaded_tool_names.add(tool.name)  # 新增代码+AgentPyPhaseIDynamicGate: 把允许准备的 deferred 工具加入当前工具池状态；若没有这行代码，后续模型 schema 仍看不到浏览器工具。
            loaded_names.append(tool.name)  # 新增代码+AgentPyPhaseIDynamicGate: 记录成功准备的工具名用于审计；若没有这行代码，无法回看 read skill 带来了哪些工具。
    if loaded_names:  # 新增代码+AgentPyPhaseIDynamicGate: 只有确实加载到工具时才记录观察事件；若没有这行代码，无工具包 skill 会产生噪声事件。
        run_helpers_from_core.record_observation(agent, "dynamic_skill_loaded_tools", {"skill": skill_name, "packs": list(pack_names), "tools": loaded_names})  # 新增代码+AgentPyPhaseIDynamicGate: 记录 skill 到工具包的解锁证据；若没有这行代码，真实调试时难以解释工具池为何变大。
# 新增代码+AgentPyPhaseIDynamicGate: 函数段结束，load_tools_for_dynamic_skill_read 到此结束；若没有这个边界说明，用户不容易看出工具包解锁范围。


def remember_dynamic_prompt_read(agent: Any, path: Path) -> None:  # 新增代码+AgentPyPhaseIDynamicGate: 函数段开始，在成功读取后记录动态提示词层级状态；若没有这段函数，读过父层后仍无法进入子层。
    read_key = dynamic_prompt_read_key(agent, path)  # 新增代码+AgentPyPhaseIDynamicGate: 获取成功读取文件的稳定 key；若没有这行代码，记录集合不知道该保存什么。
    if read_key is None:  # 新增代码+AgentPyPhaseIDynamicGate: 非工作区路径不记录；若没有这行代码，None 可能进入集合并污染状态。
        return  # 新增代码+AgentPyPhaseIDynamicGate: 直接结束记录流程；若没有这行代码，后续 add 会收到无意义值。
    if dynamic_prompt_skill_base(read_key) is None:  # 新增代码+AgentPyPhaseIDynamicGate: 只有 skills 动态提示词树需要记录层级；若没有这行代码，普通代码文件会污染门控状态。
        return  # 新增代码+AgentPyPhaseIDynamicGate: 普通文件不记录；若没有这行代码，集合会逐渐膨胀且难以审计。
    agent.loaded_dynamic_prompt_paths.add(read_key)  # 新增代码+AgentPyPhaseIDynamicGate: 保存已读层级 key；若没有这行代码，后续子规则无法确认父层已经加载。
    load_tools_for_dynamic_skill_read(agent, read_key)  # 新增代码+AgentPyPhaseIDynamicGate: 成功读取具体 skill 后同步准备对应工具包；若没有这行代码，浏览器自动化仍只能停留在提示词层。
# 新增代码+AgentPyPhaseIDynamicGate: 函数段结束，remember_dynamic_prompt_read 到此结束；若没有这个边界说明，用户不容易看出读后记录范围。
