"""提示词表面报告的新命名空间。"""  # 新增代码+PromptsSplit: 把 PromptSurfaceReport 放到更好找的 prompts 层；如果没有这行代码，用户查验提示词加载报告仍要翻 context_assembler。
try:  # 新增代码+PromptsSplit: 优先从 prompts.context_assembler 复用报告对象；如果没有这行代码，包模式下报告类型可能和装配器返回值不一致。
    from learning_agent.prompts.context_assembler import ContextBlockLoad, PromptSurfaceReport  # 新增代码+PromptsSplit: 重导出报告相关类型；如果没有这行代码，surface_report 模块没有实际可用对象。
except ModuleNotFoundError as error:  # 新增代码+PromptsSplit: 兼容直接脚本模式下包名不可用；如果没有这行代码，bat 入口导入 prompts.surface_report 可能失败。
    if error.name not in {"learning_agent", "learning_agent.prompts", "learning_agent.prompts.context_assembler"}:  # 新增代码+PromptsSplit: 只对路径类问题 fallback；如果没有这行代码，真实 bug 会被误判成脚本模式。
        raise  # 新增代码+PromptsSplit: 保留真实导入错误；如果没有这行代码，报告层排查会缺少根因。
    from prompts.context_assembler import ContextBlockLoad, PromptSurfaceReport  # 新增代码+PromptsSplit: 脚本模式下从同目录 prompts 包导入；如果没有这行代码，直接运行时报告入口不可用。

def empty_prompt_surface_report() -> PromptSurfaceReport:  # 新增代码+PromptsSplit: 提供空报告的语义化工厂函数；如果没有这行代码，调用方需要知道 PromptSurfaceReport.empty 的内部细节。
    return PromptSurfaceReport.empty()  # 新增代码+PromptsSplit: 调用既有空报告构造方法；如果没有这行代码，首轮前读取报告会缺少统一默认值。

__all__ = ["ContextBlockLoad", "PromptSurfaceReport", "empty_prompt_surface_report"]  # 新增代码+PromptsSplit: 明确 surface_report 对外 API；如果没有这行代码，后续维护时容易把内部名字当公开接口使用。
