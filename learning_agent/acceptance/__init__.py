"""真实验收复验工具包。"""  # 新增代码+验收验证器: 说明 acceptance 包负责离线复验真实验收证据；若没有这行代码，维护者不知道这个包的边界
from __future__ import annotations  # 新增代码+验收验证器: 允许类型注解延迟解析；若没有这行代码，部分类型在导入时可能提前求值

from typing import Any  # 新增代码+验收验证器: 标注惰性属性返回值；若没有这行代码，__getattr__ 类型不清楚


def __getattr__(name: str) -> Any:  # 新增代码+验收验证器: 惰性导出 verifier 函数；若没有这行代码，`python -m learning_agent.acceptance.verifier` 会因包初始化提前导入而出现 runpy 警告
    if name == "verify_acceptance_run":  # 新增代码+验收验证器: 只处理公开复验函数；若没有这行代码，未知属性也会被错误尝试导入
        from learning_agent.acceptance.verifier import verify_acceptance_run  # 新增代码+验收验证器: 在真正访问时才导入函数；若没有这行代码，包级 API 无法继续使用

        return verify_acceptance_run  # 新增代码+验收验证器: 返回复验函数；若没有这行代码，外部 `learning_agent.acceptance.verify_acceptance_run` 无法工作
    raise AttributeError(name)  # 新增代码+验收验证器: 未知属性按 Python 规范报错；若没有这行代码，拼错 API 会静默失败


__all__ = ["verify_acceptance_run"]  # 新增代码+验收验证器: 限定公开 API；若没有这行代码，后续维护者不清楚哪个函数可被稳定调用
