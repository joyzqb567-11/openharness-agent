"""提示词 token 预算辅助函数。"""  # 新增代码+PromptsSplit: 把 prompt 预算相关名字收拢到 prompts 层；如果没有这行代码，token 估算职责会继续散在 context 装配器里。
try:  # 新增代码+PromptsSplit: 优先复用包路径里的 token 估算实现；如果没有这行代码，包模式运行时本模块无法保持和 ContextAssembler 同一套算法。
    from learning_agent.prompts.context_assembler import estimate_tokens_from_text  # 新增代码+PromptsSplit: 引入当前项目既有粗略 token 估算函数；如果没有这行代码，预算模块会出现第二套算法导致报告不一致。
except ModuleNotFoundError as error:  # 新增代码+PromptsSplit: 兼容直接脚本模式下 learning_agent 包名不可用；如果没有这行代码，bat 入口可能因为新模块导入失败。
    if error.name not in {"learning_agent", "learning_agent.prompts", "learning_agent.prompts.context_assembler"}:  # 新增代码+PromptsSplit: 只允许路径缺失进入 fallback；如果没有这行代码，真实实现错误会被错误隐藏。
        raise  # 新增代码+PromptsSplit: 抛出真实导入错误；如果没有这行代码，排查 token 预算问题会更费时间。
    from prompts.context_assembler import estimate_tokens_from_text  # 新增代码+PromptsSplit: 脚本模式下从同目录包导入估算函数；如果没有这行代码，直接运行时预算模块不可用。

def clamp_prompt_soft_limit(value: int | None, *, default: int = 60000, minimum: int = 1000) -> int:  # 新增代码+PromptsSplit: 统一收口 prompt 软预算下限和默认值；如果没有这行代码，未来各调用点可能各自处理 None 和小值。
    if value is None:  # 新增代码+PromptsSplit: 处理调用方没有传预算的情况；如果没有这行代码，None 会在比较大小时触发异常。
        return default  # 新增代码+PromptsSplit: 返回默认软预算；如果没有这行代码，agent 初始化时可能拿不到可用预算。
    return max(minimum, int(value))  # 新增代码+PromptsSplit: 把预算转换为整数并限制最小值；如果没有这行代码，过小预算会让核心提示词被过早压缩。

__all__ = ["estimate_tokens_from_text", "clamp_prompt_soft_limit"]  # 新增代码+PromptsSplit: 明确 token_budget 对外名字；如果没有这行代码，后续迁移容易暴露临时辅助变量。
