"""提示词上下文装配器的新命名空间。"""  # 新增代码+PromptsSplit: 让 ContextAssembler 有 prompts 层入口；如果没有这行代码，后续排查 prompt 装配仍要回到根目录模块。
try:  # 新增代码+PromptsSplit: 优先按包路径复用旧实现；如果没有这行代码，包模式运行时新入口拿不到真实装配器。
    from learning_agent.context_assembler import ContextAssembler, ContextAssemblyResult, ContextBlockLoad, PromptSurfaceReport, build_long_term_memory_index, build_project_memory_index, build_text_index, estimate_tokens_from_text  # 新增代码+PromptsSplit: 重导出 context 装配相关公开对象；如果没有这行代码，prompts.context_assembler 只是空壳不能被主 agent 使用。
except ModuleNotFoundError as error:  # 新增代码+PromptsSplit: 捕获直接脚本运行时 learning_agent 包名不可用的情况；如果没有这行代码，start_oauth_agent.bat 这类脚本入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.context_assembler"}:  # 新增代码+PromptsSplit: 只对包路径缺失做 fallback；如果没有这行代码，旧实现内部的真实错误会被误吞。
        raise  # 新增代码+PromptsSplit: 重新抛出非路径类错误；如果没有这行代码，排查 context 装配 bug 时会少掉真实堆栈。
    from context_assembler import ContextAssembler, ContextAssemblyResult, ContextBlockLoad, PromptSurfaceReport, build_long_term_memory_index, build_project_memory_index, build_text_index, estimate_tokens_from_text  # 新增代码+PromptsSplit: 脚本模式下从同目录旧模块导入；如果没有这行代码，直接运行 learning_agent.py 时新入口不可用。
__all__ = ["ContextAssembler", "ContextAssemblyResult", "ContextBlockLoad", "PromptSurfaceReport", "build_long_term_memory_index", "build_project_memory_index", "build_text_index", "estimate_tokens_from_text"]  # 新增代码+PromptsSplit: 明确 prompts.context_assembler 的公开 API；如果没有这行代码，后续重构时容易误暴露临时名字。
