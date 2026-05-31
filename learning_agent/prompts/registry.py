"""提示词注册表新命名空间。"""  # 新增代码+PromptsSplit: 把 PromptRegistry 暴露到 prompts 层；若没有这个文件，外部仍只能从根目录 prompt_registry.py 导入。

try:  # 新增代码+PromptsSplit: 包运行模式下复用既有 prompt_registry 实现；若没有这行代码，新命名空间没有真实对象。
    from learning_agent.prompt_registry import PromptBlock, PromptRegistry, build_default_prompt_registry  # 新增代码+PromptsSplit: 重导出提示词块、注册表和默认构建函数；若没有这行代码，prompts.registry 无法替代旧入口。
except ModuleNotFoundError as error:  # 新增代码+PromptsSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.prompt_registry"}:  # 新增代码+PromptsSplit: 只允许目标包路径缺失时 fallback；若没有这行代码，prompt_registry 内部真实 bug 会被误吞。
        raise  # 新增代码+PromptsSplit: 重新抛出真实导入错误；若没有这行代码，排查 registry 问题会很困难。
    from prompt_registry import PromptBlock, PromptRegistry, build_default_prompt_registry  # 新增代码+PromptsSplit: 脚本模式下重导出旧入口对象；若没有这行代码，直接执行时 prompts.registry 不可用。

__all__ = ["PromptBlock", "PromptRegistry", "build_default_prompt_registry"]  # 新增代码+PromptsSplit: 明确 registry 公开 API；若没有这行代码，后续重构容易暴露临时名字。
