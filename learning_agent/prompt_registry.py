"""Prompt Registry 的最小数据模型。"""  # 新增代码+PromptArchitectureV1: 说明本模块只负责提示词注册表数据结构；若没有这行代码，读者不容易快速理解文件用途
from dataclasses import dataclass  # 新增代码+PromptArchitectureV1: 使用标准库 dataclass 简化不可变数据对象定义；若没有这行代码，PromptBlock 需要手写初始化方法


@dataclass(frozen=True)  # 新增代码+PromptArchitectureV1: 把提示词块定义为不可变数据对象；若没有这行代码，注册后的元数据可能被外部意外改动
class PromptBlock:  # 新增代码+PromptArchitectureV1: 定义单个提示词块的元数据结构；若没有这行代码，注册表没有统一的数据单元
    block_id: str  # 新增代码+PromptArchitectureV1: 保存提示词块唯一 ID；若没有这行代码，注册表无法识别和拒绝重复块
    title: str  # 新增代码+PromptArchitectureV1: 保存提示词块的可读标题；若没有这行代码，后续报告和调试输出缺少人能看懂的名称
    source: str  # 新增代码+PromptArchitectureV1: 保存提示词块来源；若没有这行代码，后续无法区分内置提示词、运行时文件和记忆索引
    priority: int  # 新增代码+PromptArchitectureV1: 保存提示词块优先级；若没有这行代码，注册表无法按重要程度排序
    load_policy: str  # 新增代码+PromptArchitectureV1: 保存加载策略；若没有这行代码，后续无法表达 always 或 index 这类加载方式
    max_tokens: int  # 新增代码+PromptArchitectureV1: 保存提示词块 token 预算上限；若没有这行代码，后续无法做上下文预算控制
    cache_policy: str = "stable"  # 新增代码+PromptArchitectureV1: 默认声明稳定缓存策略；若没有这行代码，内置提示词块缺少默认缓存语义
    conflict_policy: str = "current_user_request_wins"  # 新增代码+PromptArchitectureV1: 默认声明冲突时当前用户请求优先；若没有这行代码，提示词冲突时缺少明确规则
    owner: str = "core"  # 新增代码+PromptArchitectureV1: 默认声明核心团队/核心系统拥有该块；若没有这行代码，后续治理和报告缺少归属信息


@dataclass(frozen=True)  # 新增代码+PromptArchitectureV1: 把加载决策定义为不可变对象；若没有这行代码，报告和装配层只能用松散字典传递决策
class PromptLoadDecision:  # 新增代码+PromptArchitectureV1: 定义单个提示词块是否加载、压缩或跳过的决策模型；若没有这行代码，Prompt Registry 缺少计划中声明的决策结构
    block_id: str  # 新增代码+PromptArchitectureV1: 保存被决策的提示词块 ID；若没有这行代码，调用方无法知道决策属于哪个 block
    should_load: bool  # 新增代码+PromptArchitectureV1: 保存该块是否应该进入当前 prompt；若没有这行代码，装配层无法表达“可见但不加载”的状态
    status: str  # 新增代码+PromptArchitectureV1: 保存 loaded、compact_summary 或 skipped 等状态；若没有这行代码，报告无法用统一字段解释加载结果
    reason: str = ""  # 新增代码+PromptArchitectureV1: 保存决策原因；若没有这行代码，用户只能看到结果但看不到为什么这样加载


class PromptRegistry:  # 新增代码+PromptArchitectureV1: 定义提示词注册表容器；若没有这行代码，多个 PromptBlock 没有统一校验和排序入口
    def __init__(self, blocks: list[PromptBlock]) -> None:  # 新增代码+PromptArchitectureV1: 接收提示词块列表并建立注册表；若没有这行代码，调用方无法创建注册表实例
        seen_block_ids: set[str] = set()  # 新增代码+PromptArchitectureV1: 记录已经出现过的 block_id；若没有这行代码，重复 ID 无法被准确发现
        for block in blocks:  # 新增代码+PromptArchitectureV1: 遍历每个传入的提示词块做校验；若没有这行代码，注册表会直接接受未检查的数据
            if block.block_id in seen_block_ids:  # 新增代码+PromptArchitectureV1: 判断当前 block_id 是否已经出现；若没有这行代码，重复块会混进注册表
                raise ValueError(f"duplicate prompt block_id: {block.block_id}")  # 新增代码+PromptArchitectureV1: 用明确错误拒绝重复 ID；若没有这行代码，重复提示词可能导致排序和加载结果不稳定
            seen_block_ids.add(block.block_id)  # 新增代码+PromptArchitectureV1: 记录当前 block_id 已被占用；若没有这行代码，后面的重复块不会被识别
        self.blocks = sorted(blocks, key=lambda block: block.priority, reverse=True)  # 新增代码+PromptArchitectureV1: 按优先级从高到低保存块列表；若没有这行代码，提示词加载顺序可能不符合重要性


def build_default_prompt_registry() -> PromptRegistry:  # 新增代码+PromptArchitectureV1: 构建项目默认提示词注册表；若没有这行代码，测试和后续集成没有统一默认入口
    return PromptRegistry([  # 新增代码+PromptArchitectureV1: 用注册表容器包住默认块列表；若没有这行代码，默认块不会经过重复校验和排序
        PromptBlock(block_id="prompt.kernel.identity", title="Identity Kernel", source="built_in", priority=1000, load_policy="always", max_tokens=1200),  # 新增代码+PromptArchitectureV1: 注册身份内核提示词；若没有这行代码，agent 身份提示缺少注册表元数据
        PromptBlock(block_id="prompt.policy.operating", title="Operating Policy", source="built_in", priority=900, load_policy="always", max_tokens=1000),  # 新增代码+PromptArchitectureV1: 注册运行规则提示词；若没有这行代码，运行策略无法在注册表中声明
        PromptBlock(block_id="prompt.policy.context", title="Context Policy", source="built_in", priority=850, load_policy="always", max_tokens=900),  # 新增代码+PromptArchitectureV1: 注册上下文策略提示词；若没有这行代码，上下文使用规则缺少注册表元数据
        PromptBlock(block_id="prompt.policy.prompt_surface", title="Prompt Surface Policy", source="built_in", priority=820, load_policy="always", max_tokens=900),  # 新增代码+PromptArchitectureV1: 注册提示词表面策略；若没有这行代码，Prompt Surface v2 规则无法在注册表中体现
        PromptBlock(block_id="prompt.policy.tool_boundary", title="Tool Boundary Policy", source="built_in", priority=800, load_policy="always", max_tokens=800),  # 新增代码+PromptArchitectureV1: 注册工具边界策略；若没有这行代码，工具使用边界缺少注册表元数据
        PromptBlock(block_id="prompt.policy.response", title="Response Policy", source="built_in", priority=700, load_policy="always", max_tokens=700),  # 新增代码+PromptArchitectureV1: 注册回复策略提示词；若没有这行代码，回复风格和结构规则缺少注册表元数据
        PromptBlock(block_id="context.dynamic_prompt_index", title="Dynamic Prompt Index", source="dynamicprompt_file", priority=600, load_policy="on_demand", max_tokens=1200, cache_policy="dynamic"),  # 修改代码+PromptFiles: 注册按需动态提示词索引元数据而不是常驻 runtime 文件；若没有这行代码，报告层会继续把旧 runtime_instructions 误当每轮加载来源
        PromptBlock(block_id="context.long_term_memory_index", title="Long Term Memory Index", source="memory", priority=450, load_policy="index", max_tokens=700, cache_policy="dynamic"),  # 新增代码+PromptArchitectureV1: 注册长期记忆索引；若没有这行代码，memory.md 入口缺少注册表元数据
    ])  # 新增代码+PromptArchitectureV1: 结束默认块列表并返回注册表；若没有这行代码，函数语法不完整且无法返回默认注册表
