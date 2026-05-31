"""动态提示词路径与元数据辅助函数。"""  # 新增代码+PromptsSplit: 把 dynamicprompt.md 的按需入口集中到 prompts 层；若没有这个文件，动态规则路径仍散在主入口。

from __future__ import annotations  # 新增代码+PromptsSplit: 延迟解析类型注解；若没有这行代码，后续扩展 Path 类型时更稳。

from pathlib import Path  # 新增代码+PromptsSplit: 使用跨平台路径对象处理动态提示词文件；若没有这行代码，Windows 路径拼接会更脆弱。
from typing import Any  # 新增代码+PromptsSplit: 动态 prompt skill 元数据使用通用字典；若没有这行代码，类型边界不清楚。


def _package_root() -> Path:  # 新增代码+PromptsSplit: 定位 learning_agent 包根目录；若没有这行代码，包内默认 dynamicprompt 路径会散落硬编码。
    return Path(__file__).resolve().parents[1]  # 新增代码+PromptsSplit: prompts/dynamic_prompt.py 的上两级是 learning_agent 目录；若没有这行代码，默认提示词路径会算错。


def resolve_dynamic_prompt_path(workspace: str | Path) -> Path:  # 新增代码+PromptsSplit: 统一解析 dynamicprompt.md 的按需加载路径；若没有这行代码，动态规则迁移后没有可审计入口。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+PromptsSplit: 规范化工作区路径；若没有这行代码，相对路径覆盖规则会不稳定。
    workspace_dynamic_prompt = workspace_path / "dynamicprompt" / "dynamicprompt.md"  # 新增代码+PromptsSplit: 构造用户可编辑的工作区动态提示词路径；若没有这行代码，用户无法按项目覆盖动态规则索引。
    if workspace_dynamic_prompt.exists():  # 新增代码+PromptsSplit: 工作区动态文件存在时优先使用；若没有这行代码，项目级运行规则会被默认包内规则覆盖。
        return workspace_dynamic_prompt  # 新增代码+PromptsSplit: 返回工作区动态提示词路径；若没有这行代码，覆盖优先级不会生效。
    return _package_root() / "dynamicprompt" / "dynamicprompt.md"  # 新增代码+PromptsSplit: 回退到 learning_agent 包内默认动态提示词；若没有这行代码，新项目无法按需加载默认动态规则。


def dynamic_prompt_skill_metadata(dynamic_prompt_path: str | Path, *, relative_path: str) -> dict[str, Any] | None:  # 新增代码+PromptsSplit: 生成 dynamicprompt.md 的 skill 元信息；若没有这行代码，动态提示词不能复用 skill_load 读取通道。
    prompt_path = Path(dynamic_prompt_path)  # 新增代码+PromptsSplit: 把输入路径包装成 Path；若没有这行代码，调用方传字符串时无法使用 exists/is_dir。
    if not prompt_path.exists():  # 新增代码+PromptsSplit: 检查动态提示词文件是否存在；若没有这行代码，缺失路径会被暴露成坏 skill。
        return None  # 新增代码+PromptsSplit: 文件缺失时不加入 skill 列表；若没有这行代码，模型会尝试加载不存在的动态规则。
    if prompt_path.is_dir():  # 新增代码+PromptsSplit: 目录不能当成动态提示词正文；若没有这行代码，skill_load 会在读取时抛底层异常。
        return None  # 新增代码+PromptsSplit: 目录路径不加入 skill 列表；若没有这行代码，用户会看到不可加载入口。
    return {  # 新增代码+PromptsSplit: 返回和普通 skill 一致的数据结构；若没有这行代码，_skill_list/_skill_load 无法复用现有逻辑。
        "name": "dynamicprompt",  # 新增代码+PromptsSplit: 约定动态运行规则的加载名称；若没有这行代码，模型不知道 skill_load 应该传什么 name。
        "description": "加载 dynamicprompt/dynamicprompt.md 动态运行规则索引；用于按需查看工具、MCP、浏览器、计划和诊断等运行规则。",  # 新增代码+PromptsSplit: 说明何时加载动态提示词；若没有这行代码，模型难以判断这个入口和普通 skill 的区别。
        "path": prompt_path,  # 新增代码+PromptsSplit: 指向真实 dynamicprompt.md 文件；若没有这行代码，skill_load 无法读取正文。
        "relative_path": relative_path,  # 新增代码+PromptsSplit: 保存调用方计算好的相对路径；若没有这行代码，列表输出无法定位文件。
    }  # 新增代码+PromptsSplit: 结束伪 skill 元信息；若没有这行代码，Python 字典语法不完整。
