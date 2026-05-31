"""Context Assembler 用来把注册表里的提示词块按优先级装配成 system prompt。"""  # 修改代码+PromptArchitectureV1: 说明本模块负责提示词上下文装配；若没有这行代码，学习者不容易理解文件用途
from __future__ import annotations  # 修改代码+PromptArchitectureV1: 允许类型注解延迟解析；若没有这行代码，类之间互相引用时更容易遇到解析顺序问题

from dataclasses import dataclass, field  # 修改代码+PromptArchitectureV1: 使用 dataclass 简化报告对象定义；若没有这行代码，需要手写大量初始化方法
from pathlib import Path  # 修改代码+PromptArchitectureV1: 使用 Path 统一处理记忆索引来源路径；若没有这行代码，索引构建只能用脆弱字符串拼路径

try:  # 修改代码+PromptArchitectureV1: 优先按包路径导入 PromptRegistry；若没有这行代码，单元测试按包导入时无法找到注册表类型
    from learning_agent.prompt_registry import PromptBlock, PromptRegistry  # 修改代码+PromptArchitectureV1: 导入提示词块和注册表类型供 ContextAssembler 排序与压缩判定使用；若没有这行代码，装配器不知道 registry.blocks 的结构也无法识别动态块
except ModuleNotFoundError as error:  # 修改代码+PromptArchitectureV1: 捕获脚本模式下包路径不可用的导入错误；若没有这行代码，直接运行同目录脚本时会失败
    if error.name not in {"learning_agent", "learning_agent.prompt_registry"}:  # 修改代码+PromptArchitectureV1: 只允许包路径问题进入 fallback；若没有这行代码，prompt_registry 内部真实错误会被误吞
        raise  # 修改代码+PromptArchitectureV1: 重新抛出非路径问题；若没有这行代码，真实导入 bug 会被伪装成脚本模式
    from prompt_registry import PromptBlock, PromptRegistry  # 修改代码+PromptArchitectureV1: 脚本模式下从同目录导入提示词块和注册表；若没有这行代码，直接运行 learning_agent.py 相关路径时无法复用装配器和动态块判定


@dataclass  # 修改代码+PromptArchitectureV1: 自动生成加载记录对象初始化方法；若没有这行代码，记录每个 block 会需要手写样板代码
class ContextBlockLoad:  # 修改代码+PromptArchitectureV1: 定义单个提示词块的加载结果；若没有这行代码，报告无法精确说明哪些 block 被加载或压缩
    block_id: str  # 修改代码+PromptArchitectureV1: 保存提示词块唯一 ID；若没有这行代码，用户无法知道加载记录对应哪个 block
    title: str  # 修改代码+PromptArchitectureV1: 保存提示词块可读标题；若没有这行代码，报告只有 ID 不利于初学者理解
    source: str  # 修改代码+PromptArchitectureV1: 保存提示词块来源；若没有这行代码，用户无法区分内置规则、运行时文件和记忆来源
    load_policy: str  # 修改代码+PromptArchitectureV1: 保存注册表声明的加载策略；若没有这行代码，报告无法解释为什么该块应该加载
    priority: int  # 修改代码+PromptArchitectureV1: 保存排序优先级；若没有这行代码，用户无法复查装配顺序依据
    estimated_tokens: int  # 修改代码+PromptArchitectureV1: 保存该块粗略 token 估算；若没有这行代码，token budget report 没有基础数据
    loaded: bool = True  # 修改代码+PromptArchitectureV1: 标记该块是否已经加载；若没有这行代码，skipped/compacted 状态无法复用同一结构
    status: str = "loaded"  # 修改代码+PromptArchitectureV1: 保存加载状态文本；若没有这行代码，报告无法表达 loaded 之外的状态
    content_chars: int = 0  # 修改代码+PromptArchitectureV1: 保存最终纳入 prompt 的字符数；若没有这行代码，用户无法判断上下文大小来源
    note: str = ""  # 修改代码+PromptArchitectureV1: 保存额外说明；若没有这行代码，截断或压缩原因没有位置记录


@dataclass  # 修改代码+PromptArchitectureV1: 自动生成装配结果对象初始化方法；若没有这行代码，调用方需要手写结果容器
class ContextAssemblyResult:  # 修改代码+PromptArchitectureV1: 定义一次 system prompt 装配的结果；若没有这行代码，装配器只能返回裸字符串而丢失报告数据
    system_prompt: str  # 修改代码+PromptArchitectureV1: 保存装配后的完整 system prompt；若没有这行代码，LearningAgent 无法把结果发给模型
    loaded_blocks: list[ContextBlockLoad]  # 修改代码+PromptArchitectureV1: 保存所有加载块记录；若没有这行代码，last_prompt_surface_report 没有数据来源
    estimated_total_tokens: int  # 修改代码+PromptArchitectureV1: 保存所有装配文本的粗略 token 总数；若没有这行代码，预算控制没有总量
    compacted: bool = False  # 修改代码+PromptArchitectureV1: 标记本次是否发生压缩；若没有这行代码，compact 逻辑缺少结果标志


@dataclass  # 修改代码+PromptArchitectureV1: 自动生成提示词表面报告初始化方法；若没有这行代码，LearningAgent 保存报告会更繁琐
class PromptSurfaceReport:  # 修改代码+PromptArchitectureV1: 定义可被 LearningAgent.last_prompt_surface_report 保存的报告对象；若没有这行代码，测试和用户无法读取本轮加载清单
    loaded_blocks: list[ContextBlockLoad] = field(default_factory=list)  # 修改代码+PromptArchitectureV1: 保存本轮已加载提示词块列表；若没有这行代码，报告无法说明加载了哪些 block
    estimated_total_tokens: int = 0  # 修改代码+PromptArchitectureV1: 保存本轮粗略 token 总数；若没有这行代码，报告无法展示上下文预算大小
    compacted: bool = False  # 修改代码+PromptArchitectureV1: 保存本轮是否发生压缩；若没有这行代码，报告无法表达压缩状态

    @classmethod  # 修改代码+PromptArchitectureV1: 提供空报告构造入口；若没有这行代码，LearningAgent 初始化时需要知道字段默认细节
    def empty(cls) -> "PromptSurfaceReport":  # 修改代码+PromptArchitectureV1: 返回没有加载记录的报告；若没有这行代码，last_prompt_surface_report 初始值不统一
        return cls()  # 修改代码+PromptArchitectureV1: 使用默认字段创建空报告；若没有这行代码，调用方拿不到空报告对象

    def to_text(self) -> str:  # 修改代码+PromptArchitectureV1: 把报告转换为可读文本；若没有这行代码，用户或调试日志无法直接展示报告
        if not self.loaded_blocks:  # 修改代码+PromptArchitectureV1: 处理没有加载块的报告；若没有这行代码，空报告会输出误导性空列表
            return "Prompt Surface Report: no loaded blocks."  # 修改代码+PromptArchitectureV1: 返回清晰空报告说明；若没有这行代码，空报告难以理解
        lines = ["Prompt Surface Report:"]  # 修改代码+PromptArchitectureV1: 准备报告标题行；若没有这行代码，输出文本缺少开头说明
        for loaded_block in self.loaded_blocks:  # 修改代码+PromptArchitectureV1: 遍历每个加载块生成明细；若没有这行代码，报告不会列出具体 block
            note_text = f", note={loaded_block.note}" if loaded_block.note else ""  # 修改代码+PromptArchitectureV1: 有 note 时追加来源/截断/压缩说明；若没有这行代码，报告看不到索引或 compact 元数据
            lines.append(f"- {loaded_block.block_id} ({loaded_block.estimated_tokens} tokens, {loaded_block.status}{note_text})")  # 修改代码+PromptArchitectureV1: 追加块 ID、token、状态和 note；若没有这行代码，用户看不到每块加载情况
        lines.append(f"estimated_total_tokens={self.estimated_total_tokens}")  # 修改代码+PromptArchitectureV1: 追加总 token 估算；若没有这行代码，报告缺少总量
        lines.append(f"compacted={self.compacted}")  # 修改代码+PromptArchitectureV1: 追加压缩状态；若没有这行代码，报告缺少 compact 标志
        return "\n".join(lines)  # 修改代码+PromptArchitectureV1: 合并报告文本并返回；若没有这行代码，调用方拿不到可读报告


def estimate_tokens_from_text(text: str) -> int:  # 修改代码+PromptArchitectureV1: 提供第一版粗略 token 估算函数；若没有这行代码，ContextAssembler 无法计算预算
    return max(1, len(text) // 4)  # 修改代码+PromptArchitectureV1: 用字符数除以四估算 token 且最少为一；若没有这行代码，短文本可能得到 0 导致预算统计失真


def _extract_heading_lines(text: str) -> list[str]:  # 修改代码+PromptArchitectureV1: 从文本里提取 Markdown 标题作为索引导航；若没有这行代码，索引只能显示字符数而不能告诉模型文件结构
    headings: list[str] = []  # 修改代码+PromptArchitectureV1: 准备保存标题列表；若没有这行代码，后续循环没有容器可写入
    for raw_line in text.splitlines():  # 修改代码+PromptArchitectureV1: 逐行扫描文本寻找标题；若没有这行代码，无法从正文中定位 heading
        line = raw_line.strip()  # 修改代码+PromptArchitectureV1: 去掉行首尾空白后判断标题；若没有这行代码，带缩进标题可能被漏掉
        if line.startswith("#"):  # 修改代码+PromptArchitectureV1: 识别 Markdown 标题行；若没有这行代码，索引无法保留 heading 信息
            headings.append(line)  # 修改代码+PromptArchitectureV1: 把标题加入索引列表；若没有这行代码，找到的标题不会进入最终索引
    return headings[:12]  # 修改代码+PromptArchitectureV1: 最多保留 12 个标题避免索引过长；若没有这行代码，超多标题可能撑大 system prompt


def _count_stable_facts(text: str) -> int:  # 修改代码+PromptArchitectureV1: 粗略统计非空正文行作为 stable_fact_count；若没有这行代码，报告缺少可测试的记忆事实数量
    stable_lines = [line for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]  # 修改代码+PromptArchitectureV1: 只统计非空且非标题的内容行；若没有这行代码，空行和标题会让事实数量失真
    return len(stable_lines)  # 修改代码+PromptArchitectureV1: 返回稳定事实行数；若没有这行代码，调用方拿不到 stable_fact_count 数值


def _summarize_tail_lines(text: str, max_lines: int) -> list[str]:  # 修改代码+PromptArchitectureV1: 生成去重后的最新尾部摘要；若没有这行代码，重复长记忆会整段重复进入 prompt
    tail_lines = [line.strip() for line in text.splitlines() if line.strip()]  # 修改代码+PromptArchitectureV1: 收集非空尾部候选行；若没有这行代码，摘要会被空行噪声占满
    summarized: list[str] = []  # 修改代码+PromptArchitectureV1: 准备保存压缩后的尾部摘要；若没有这行代码，函数没有返回内容容器
    last_line = ""  # 修改代码+PromptArchitectureV1: 记录上一条写入行用于合并连续重复；若没有这行代码，重复 memory 行会连续出现
    repeat_count = 0  # 修改代码+PromptArchitectureV1: 记录当前连续重复次数；若没有这行代码，无法把重复内容压成计数说明
    for line in tail_lines[-max_lines * 4:]:  # 修改代码+PromptArchitectureV1: 只看靠近文件末尾的一小段；若没有这行代码，摘要生成会扫描过多尾部内容
        if line == last_line:  # 修改代码+PromptArchitectureV1: 判断是否连续重复上一行；若没有这行代码，重复行无法被压缩
            repeat_count += 1  # 修改代码+PromptArchitectureV1: 累加重复次数；若没有这行代码，最终说明不知道重复了几次
            continue  # 修改代码+PromptArchitectureV1: 跳过重复行正文；若没有这行代码，长 memory 的重复正文仍会进入 prompt
        if repeat_count > 1 and summarized:  # 修改代码+PromptArchitectureV1: 遇到新行前补写上一段重复计数；若没有这行代码，重复信息会完全丢失
            summarized[-1] = f"{summarized[-1]} (连续重复 {repeat_count} 次)"  # 修改代码+PromptArchitectureV1: 用计数说明替代多行重复；若没有这行代码，用户不知道重复内容规模
        summarized.append(line)  # 修改代码+PromptArchitectureV1: 写入新的尾部摘要行；若没有这行代码，非重复尾部内容会丢失
        last_line = line  # 修改代码+PromptArchitectureV1: 更新上一行记录；若没有这行代码，下一轮无法判断重复
        repeat_count = 1  # 修改代码+PromptArchitectureV1: 新行第一次出现计数为一；若没有这行代码，重复计数会从旧段继承导致错误
    if repeat_count > 1 and summarized:  # 修改代码+PromptArchitectureV1: 循环结束后处理最后一段重复；若没有这行代码，末尾重复计数会漏写
        summarized[-1] = f"{summarized[-1]} (连续重复 {repeat_count} 次)"  # 修改代码+PromptArchitectureV1: 把最后一段重复压缩成说明；若没有这行代码，末尾重复规模不可见
    return summarized[-max_lines:]  # 修改代码+PromptArchitectureV1: 返回限制行数后的摘要；若没有这行代码，摘要可能超过预算


def build_text_index(title: str, text: str, max_chars: int, source_path: str | Path) -> str:  # 修改代码+PromptArchitectureV1: 把单个长文本转换为可审计索引；若没有这行代码，memory 只能全文或粗截断进入 prompt
    source_text = str(source_path)  # 修改代码+PromptArchitectureV1: 把 Path 或字符串统一成展示文本；若没有这行代码，索引里的来源路径格式不稳定
    original_chars = len(text)  # 修改代码+PromptArchitectureV1: 记录原始字符数供审计；若没有这行代码，用户无法判断索引压缩了多少内容
    headings = _extract_heading_lines(text)  # 修改代码+PromptArchitectureV1: 提取标题作为结构导航；若没有这行代码，索引缺少 heading 信息
    stable_fact_count = _count_stable_facts(text)  # 修改代码+PromptArchitectureV1: 统计稳定事实行数用于报告和测试；若没有这行代码，stable_fact_count 无法显示
    tail_summary = _summarize_tail_lines(text, max_lines=8)  # 修改代码+PromptArchitectureV1: 生成最新尾部摘要；若没有这行代码，最新记忆变化无法进入索引
    heading_text = "\n".join(f"- {heading}" for heading in headings) if headings else "- 未发现 Markdown 标题"  # 修改代码+PromptArchitectureV1: 格式化标题列表；若没有这行代码，标题区块可能为空且难以理解
    tail_text = "\n".join(f"- {line}" for line in tail_summary) if tail_summary else "- 文本为空或没有可摘要内容"  # 修改代码+PromptArchitectureV1: 格式化尾部摘要；若没有这行代码，索引缺少最新内容提示
    metadata_text = f"source_path={source_text}\noriginal_chars={original_chars}\nstable_fact_count={stable_fact_count}"  # 修改代码+PromptArchitectureV1: 生成来源、原始长度和事实数量元数据；若没有这行代码，索引不可审计
    body = f"{metadata_text}\nheadings:\n{heading_text}\nlatest_tail_summary:\n{tail_text}"  # 修改代码+PromptArchitectureV1: 合并元数据、标题和尾部摘要；若没有这行代码，索引正文不会成型
    truncated = original_chars > len(body) or len(body) > max_chars  # 修改代码+PromptArchitectureV1: 判断索引是否代表压缩而非全文加载；若没有这行代码，报告可能误称全文加载
    if len(body) > max_chars:  # 修改代码+PromptArchitectureV1: 防止索引自身超过预算；若没有这行代码，极端标题或摘要仍可能撑大 prompt
        if max_chars <= 0:  # 修改代码+PromptArchitectureV1: 单独处理零预算或负预算；若没有这行代码，body[-0:] 会返回完整正文导致 included_chars 超限
            body = ""  # 修改代码+PromptArchitectureV1: 零预算时正文为空但外层元数据仍说明 included_chars=0；若没有这行代码，报告会声称加载了超预算内容
        else:  # 修改代码+PromptArchitectureV1: 处理仍有少量预算可用的截断场景；若没有这行代码，正常小预算也会被当作零预算丢光
            marker = "\n...[index truncated, full_text_loaded=false]...\n"  # 修改代码+PromptArchitectureV1: 准备明确截断标记；若没有这行代码，用户看不出索引已被压缩
            prefix = f"{metadata_text}\nheadings:\n"  # 修改代码+PromptArchitectureV1: 固定保留元数据和 headings 标签；若没有这行代码，截断后可能丢失索引入口
            tail_prefix = "latest_tail_summary:\n"  # 修改代码+PromptArchitectureV1: 固定保留尾部摘要标签；若没有这行代码，截断后可能丢失最新摘要入口
            fixed_length = len(prefix) + len(marker) + len(tail_prefix)  # 修改代码+PromptArchitectureV1: 计算固定标签开销；若没有这行代码，正文预算会算错
            if fixed_length > max_chars:  # 修改代码+PromptArchitectureV1: 处理预算连标签都放不下的极端场景；若没有这行代码，included_chars 可能继续超过 max_chars
                body = f"headings:\n{marker}{tail_prefix}"[:max_chars]  # 修改代码+PromptArchitectureV1: 退化为最小 headings 和 tail 标签并严格裁剪；若没有这行代码，极小预算仍可能超限
            else:  # 修改代码+PromptArchitectureV1: 处理预算足够放下标签和少量正文的常见截断场景；若没有这行代码，无法在 headings 和 tail 之间分配预算
                flexible_budget = max_chars - fixed_length  # 修改代码+PromptArchitectureV1: 计算可分给标题正文和尾部正文的预算；若没有这行代码，两块正文无法稳定限长
                heading_budget = min(len(heading_text), max(1, flexible_budget // 3)) if flexible_budget else 0  # 修改代码+PromptArchitectureV1: 给 headings 保留部分预算；若没有这行代码，tail 会把 headings 全部挤掉
                tail_budget = max(0, flexible_budget - heading_budget)  # 修改代码+PromptArchitectureV1: 把剩余预算分给最新尾部摘要；若没有这行代码，最新事实可能被长标题挤掉
                clipped_heading_text = heading_text[:heading_budget] if heading_budget else ""  # 修改代码+PromptArchitectureV1: 从标题开头保留结构导航；若没有这行代码，headings 标签下没有内容
                clipped_tail_text = tail_text[-tail_budget:] if tail_budget else ""  # 修改代码+PromptArchitectureV1: 从尾部保留最新内容；若没有这行代码，最新记忆事实可能被截掉
                body = f"{prefix}{clipped_heading_text}{marker}{tail_prefix}{clipped_tail_text}"  # 修改代码+PromptArchitectureV1: 组装预算内索引；若没有这行代码，修复后的索引正文无法生成
        truncated = True  # 修改代码+PromptArchitectureV1: 明确标记索引被截断；若没有这行代码，截断后仍可能被报告为完整
    included_chars = len(body)  # 修改代码+PromptArchitectureV1: 计算最终纳入索引正文长度；若没有这行代码，included_chars 无法准确展示
    estimated_tokens = estimate_tokens_from_text(body)  # 修改代码+PromptArchitectureV1: 估算索引 token 数；若没有这行代码，报告缺少预算信息
    return f"{title}\nload_mode=index\nfull_text_loaded=false\nincluded_chars={included_chars}\nestimated_tokens={estimated_tokens}\ntruncated={truncated}\n{body}"  # 修改代码+PromptArchitectureV1: 返回最终索引文本；若没有这行代码，调用方拿不到可放入 system prompt 的索引


def build_project_memory_index(files: list[tuple[Path, str]]) -> str:  # 修改代码+PromptArchitectureV1: 把 agent_memory 多文件构建成项目记忆索引；若没有这行代码，三件套无法以统一索引形式加载
    sections: list[str] = ["Project Memory Index\nlegacy_title=Project Agent Memory / 项目级上下文"]  # 修改代码+PromptArchitectureV1: 设置索引标题并保留旧标题兼容邻近回归；若没有这行代码，旧测试和用户无法确认项目记忆入口仍存在
    for file_path, missing_text in files:  # 修改代码+PromptArchitectureV1: 遍历每个记忆来源文件；若没有这行代码，context/progress/bugs 不会逐个进入索引
        if file_path.exists() and file_path.is_file():  # 修改代码+PromptArchitectureV1: 只读取真实存在的普通文件；若没有这行代码，目录或缺失路径会导致读取异常
            file_text = file_path.read_text(encoding="utf-8", errors="replace")  # 修改代码+PromptArchitectureV1: 读取当前记忆文件正文；若没有这行代码，索引无法包含该来源摘要
        else:  # 修改代码+PromptArchitectureV1: 处理文件缺失或不是普通文件的场景；若没有这行代码，缺失来源无法形成可读说明
            file_text = missing_text  # 修改代码+PromptArchitectureV1: 使用调用方提供的缺失说明作为索引内容；若没有这行代码，缺失文件不会被报告
        sections.append(build_text_index(f"Source: {file_path.name}", file_text, max_chars=220, source_path=file_path))  # 修改代码+CapabilityPacks: 把每个项目记忆来源索引预算降到 220 字符；若没有这行代码，安全关键词和记忆索引叠加时默认 system prompt 可能刚好超过方案 B 目标
    return "\n\n".join(sections)  # 修改代码+PromptArchitectureV1: 合并所有来源索引；若没有这行代码，调用方拿不到完整项目记忆索引


def build_long_term_memory_index(memory_text: str) -> str:  # 修改代码+PromptArchitectureV1: 把 memory.md 正文转换成长记忆索引；若没有这行代码，长期记忆仍会全文注入
    return build_text_index("Long-Term Memory Index", memory_text, max_chars=1000, source_path="memory.md")  # 修改代码+PromptArchitectureV1: 返回限定长度的 memory.md 索引；若没有这行代码，超长长期记忆会继续挤占 system prompt


def _extract_block_note(content: str) -> str:  # 修改代码+PromptArchitectureV1: 从索引或 compact 内容里提取报告 note；若没有这行代码，PromptSurfaceReport 无法显示审计元数据
    prefixes = ("source_path=", "original_chars=", "included_chars=", "stable_fact_count=", "truncated=", "reason=", "full_text_loaded=")  # 修改代码+PromptArchitectureV1: 定义可进入 note 的审计字段；若没有这行代码，报告会混入大量正文或漏掉 compact 字段
    note_lines = [line for line in content.splitlines() if line.startswith(prefixes)]  # 修改代码+PromptArchitectureV1: 只提取审计关键行；若没有这行代码，报告 note 会混入正文噪声
    return "; ".join(note_lines[:12])  # 修改代码+PromptArchitectureV1: 合并并限制 note 长度；若没有这行代码，报告可能被过多元数据撑长


class ContextAssembler:  # 修改代码+PromptArchitectureV1: 定义上下文装配器；若没有这行代码，提示词块无法从注册表驱动装配
    def __init__(self, registry: PromptRegistry, soft_token_limit: int = 60_000) -> None:  # 修改代码+PromptArchitectureV1: 接收软 token 预算且默认约 60K；若没有这行代码，Task 5 无法测试 compact 且默认路径不会贴近设计预算
        self.registry = registry  # 修改代码+PromptArchitectureV1: 保存注册表供装配排序使用；若没有这行代码，block 顺序和元数据来源会丢失
        self.soft_token_limit = soft_token_limit  # 新增代码+PromptArchitectureV1: 保存软预算阈值；若没有这行代码，装配器无法判断何时生成 Compact Summary

    def _can_compact_block(self, block: PromptBlock, estimated_tokens: int) -> bool:  # 新增代码+PromptArchitectureV1: 判断某个 block 是否允许被压缩；若没有这行代码，核心内置策略可能在预算紧张时被误摘要化
        if block.cache_policy != "dynamic":  # 新增代码+PromptArchitectureV1: 只允许动态来源进入 compact 候选；若没有这行代码，built_in 核心规则也可能被压缩
            return False  # 新增代码+PromptArchitectureV1: 稳定内置块保持完整加载；若没有这行代码，硬规则会丢失完整文本
        if block.source == "built_in":  # 新增代码+PromptArchitectureV1: 再次保护内置提示词来源；若没有这行代码，未来误把内置块 cache_policy 改成 dynamic 时仍可能压缩核心策略
            return False  # 新增代码+PromptArchitectureV1: 内置规则永不通过 compact 候选；若没有这行代码，工具边界和回复策略可能只剩摘要
        return estimated_tokens > block.max_tokens  # 新增代码+PromptArchitectureV1: 只有单块已经超过自身预算才压缩；若没有这行代码，小型动态上下文会被不必要摘要化

    def _compact_block_content(self, block_id: str, title: str, source: str, content: str, reason: str) -> tuple[str, str]:  # 新增代码+PromptArchitectureV1: 把超预算 block 转成可审计摘要；若没有这行代码，压缩时只能丢内容且无法说明原因
        original_chars = len(content)  # 新增代码+PromptArchitectureV1: 记录原始字符数供审计；若没有这行代码，compact 记录无法说明原文大小
        head = content[:240].strip()  # 新增代码+PromptArchitectureV1: 保留开头片段帮助识别主题；若没有这行代码，摘要只有元数据而缺少内容线索
        tail = content[-240:].strip() if original_chars > 240 else ""  # 新增代码+PromptArchitectureV1: 保留尾部片段帮助看到最新信息；若没有这行代码，压缩摘要可能丢失结尾上下文
        summary_lines = ["Compact Summary", f"block_id={block_id}", f"title={title}", f"source={source}", f"original_chars={original_chars}", "included_chars=0", "full_text_loaded=false", f"reason={reason}", "head_excerpt:", head]  # 新增代码+PromptArchitectureV1: 准备结构化摘要行；若没有这行代码，摘要无法稳定包含必须审计字段
        if tail:  # 新增代码+PromptArchitectureV1: 只在原文足够长时追加尾部摘录；若没有这行代码，短文本会重复显示同一片段
            summary_lines.extend(["tail_excerpt:", tail])  # 新增代码+PromptArchitectureV1: 写入尾部摘录；若没有这行代码，compact 可能漏掉结尾信息
        summary_text = "\n".join(summary_lines)  # 新增代码+PromptArchitectureV1: 合并摘要文本用于计算 included_chars；若没有这行代码，摘要无法进入 system prompt
        summary_text = summary_text.replace("included_chars=0", f"included_chars={len(summary_text)}", 1)  # 新增代码+PromptArchitectureV1: 写入摘要实际字符数；若没有这行代码，compact 记录的 included chars 不可信
        note = f"original_chars={original_chars}; included_chars={len(summary_text)}; reason={reason}; full_text_loaded=false"  # 新增代码+PromptArchitectureV1: 生成报告 note；若没有这行代码，PromptSurfaceReport 无法展示 compact 审计字段
        return summary_text, note  # 新增代码+PromptArchitectureV1: 返回摘要文本和报告 note；若没有这行代码，调用方拿不到压缩结果

    def assemble_static_blocks(self, block_contents: dict[str, str]) -> ContextAssemblyResult:  # 修改代码+PromptArchitectureV1: 按注册表优先级装配并在超软预算时压缩；若没有这行代码，LearningAgent 无法获得 compact 结果
        entries: list[dict[str, object]] = []  # 新增代码+PromptArchitectureV1: 保存待装配 block 的中间数据；若没有这行代码，无法先计算总预算再决定压缩
        for block in self.registry.blocks:  # 修改代码+PromptArchitectureV1: 按注册表优先级遍历 block；若没有这行代码，装配顺序会退回输入字典顺序
            content = block_contents.get(block.block_id, "")  # 修改代码+PromptArchitectureV1: 读取当前 block 内容；若没有这行代码，装配器不知道该 block 是否有文本
            if not content.strip():  # 修改代码+PromptArchitectureV1: 跳过缺失或空白内容；若没有这行代码，空 block 会污染 prompt 和报告
                continue  # 修改代码+PromptArchitectureV1: 继续检查下一个 block；若没有这行代码，空内容仍会进入预算计算
            entries.append({"block": block, "content": content, "estimated_tokens": estimate_tokens_from_text(content), "status": "loaded", "note": _extract_block_note(content)})  # 修改代码+PromptArchitectureV1: 记录内容、预算和初始状态；若没有这行代码，compact 无法基于总量调整单块
        estimated_total_tokens = sum(int(entry["estimated_tokens"]) for entry in entries)  # 新增代码+PromptArchitectureV1: 计算压缩前总 token 粗估；若没有这行代码，无法判断是否超过 soft limit
        compacted = False  # 新增代码+PromptArchitectureV1: 初始化压缩标志；若没有这行代码，result.compacted 无法准确表示状态
        if estimated_total_tokens > self.soft_token_limit:  # 新增代码+PromptArchitectureV1: 仅当总量超过软预算时触发压缩；若没有这行代码，默认行为会无故改变
            compact_candidates = [entry for entry in sorted(entries, key=lambda item: int(item["block"].priority)) if self._can_compact_block(entry["block"], int(entry["estimated_tokens"]))]  # 修改代码+PromptArchitectureV1: 只从低优先级且可压缩的动态 block 里选择候选；若没有这行代码，核心 built_in 策略会被误压缩
            for entry in compact_candidates:  # 修改代码+PromptArchitectureV1: 遍历已经过滤后的动态压缩候选；若没有这行代码，预算处理无法逐块生成 compact summary
                block = entry["block"]  # 新增代码+PromptArchitectureV1: 取出注册表 block 元数据；若没有这行代码，无法读取 id/title/source
                reason = f"soft_token_limit_exceeded:{estimated_total_tokens}>{self.soft_token_limit}"  # 新增代码+PromptArchitectureV1: 记录压缩触发原因；若没有这行代码，报告无法解释 compact 决策
                summary_text, note = self._compact_block_content(block.block_id, block.title, block.source, str(entry["content"]), reason)  # 新增代码+PromptArchitectureV1: 生成 Compact Summary；若没有这行代码，超预算 block 不会被摘要化
                estimated_total_tokens -= int(entry["estimated_tokens"])  # 新增代码+PromptArchitectureV1: 扣掉原文 token；若没有这行代码，总预算会把原文和摘要重复计算
                entry["content"] = summary_text  # 新增代码+PromptArchitectureV1: 用摘要替换原文进入 system prompt；若没有这行代码，超预算原文仍会完整加载
                entry["estimated_tokens"] = estimate_tokens_from_text(summary_text)  # 新增代码+PromptArchitectureV1: 重新估算摘要 token；若没有这行代码，报告会继续显示原文预算
                entry["status"] = "compact_summary"  # 新增代码+PromptArchitectureV1: 标记该块是 compact 摘要；若没有这行代码，报告会误称它普通加载
                entry["note"] = note  # 新增代码+PromptArchitectureV1: 保存 original/included/reason 等字段；若没有这行代码，compact 记录不完整
                estimated_total_tokens += int(entry["estimated_tokens"])  # 新增代码+PromptArchitectureV1: 加回摘要 token；若没有这行代码，总预算会被低估
                compacted = True  # 新增代码+PromptArchitectureV1: 标记本次发生压缩；若没有这行代码，result.compacted 会错误为 False
                if estimated_total_tokens <= self.soft_token_limit:  # 新增代码+PromptArchitectureV1: 预算满足后停止压缩；若没有这行代码，可能继续压缩不必要的高优先级内容
                    break  # 新增代码+PromptArchitectureV1: 退出压缩循环；若没有这行代码，预算已满足仍会处理后续 block
        prompt_parts = [str(entry["content"]) for entry in entries]  # 新增代码+PromptArchitectureV1: 收集最终进入 system prompt 的文本；若没有这行代码，调用方拿不到装配结果
        loaded_blocks: list[ContextBlockLoad] = []  # 新增代码+PromptArchitectureV1: 准备保存加载报告记录；若没有这行代码，PromptSurfaceReport 没有数据来源
        for entry in entries:  # 新增代码+PromptArchitectureV1: 遍历最终内容生成报告；若没有这行代码，压缩状态无法进入报告
            block = entry["block"]  # 新增代码+PromptArchitectureV1: 取出 block 元数据；若没有这行代码，报告无法填写 id/title/source
            content = str(entry["content"])  # 新增代码+PromptArchitectureV1: 取出最终内容用于统计字符数；若没有这行代码，content_chars 无法反映实际进入 prompt 的内容
            loaded_blocks.append(ContextBlockLoad(block_id=block.block_id, title=block.title, source=block.source, load_policy=block.load_policy, priority=block.priority, estimated_tokens=int(entry["estimated_tokens"]), status=str(entry["status"]), content_chars=len(content), note=str(entry["note"])))  # 修改代码+PromptArchitectureV1: 记录最终状态和 compact note；若没有这行代码，报告无法审计压缩结果
        system_prompt = "\n\n".join(prompt_parts)  # 修改代码+PromptArchitectureV1: 用空行连接最终 block；若没有这行代码，system prompt 无法形成完整字符串
        return ContextAssemblyResult(system_prompt=system_prompt, loaded_blocks=loaded_blocks, estimated_total_tokens=estimated_total_tokens, compacted=compacted)  # 修改代码+PromptArchitectureV1: 返回包含 compact 标志的装配结果；若没有这行代码，调用方无法知道本轮是否压缩
