"""浏览器秘密库，只允许安全前缀的环境变量进入真实表单输入。"""  # 新增代码+BrowserSecretStage9: 说明本模块负责 secret ref 安全解析；若没有这行代码，秘密输入边界不清楚。

from __future__ import annotations  # 新增代码+BrowserSecretStage9: 延迟解析类型注解；若没有这行代码，类型引用更脆弱。

import os  # 新增代码+BrowserSecretStage9: 从进程环境变量读取 secret；若没有这行代码，secret ref 无法解析。
from dataclasses import dataclass  # 新增代码+BrowserSecretStage9: 用 dataclass 表达已解析 secret；若没有这行代码，需要手写容器。

from learning_agent.browser.runtime_models import REDACTED_VALUE  # 新增代码+BrowserSecretStage9: 复用统一脱敏占位符；若没有这行代码，不同模块脱敏文案会分裂。

DEFAULT_SECRET_ENV_PREFIXES = ("LEARNING_AGENT_SECRET_", "LEARNING_AGENT_TEST_", "OPENHARNESS_SECRET_")  # 新增代码+BrowserSecretStage9: 定义允许读取的环境变量前缀；若没有这行代码，模型可能读取 PATH 等无关信息。


@dataclass  # 新增代码+BrowserSecretStage9: 自动生成 secret 结果构造器；若没有这行代码，解析结果需要手写类。
class ResolvedBrowserSecret:  # 新增代码+BrowserSecretStage9: 表示一个已解析但应谨慎使用的秘密；若没有这个类，审计名和值容易混在一起。
    value: str  # 新增代码+BrowserSecretStage9: 保存真实 secret 值供输入页面；若没有这行代码，工具无法填密码。
    audit_name: str  # 新增代码+BrowserSecretStage9: 保存可落盘引用名；若没有这行代码，日志可能误写真实值。


class BrowserSecretVault:  # 新增代码+BrowserSecretStage9: 管理浏览器 secret ref；若没有这个类，秘密读取会散落在工具层。
    def __init__(self, allowed_env_prefixes: tuple[str, ...] = DEFAULT_SECRET_ENV_PREFIXES) -> None:  # 新增代码+BrowserSecretStage9: 初始化允许前缀；若没有这行代码，测试和生产无法共享规则。
        self.allowed_env_prefixes = tuple(allowed_env_prefixes)  # 新增代码+BrowserSecretStage9: 保存不可变前缀列表；若没有这行代码，外部可能意外修改规则。
        self._known_secret_values: set[str] = set()  # 新增代码+BrowserSecretStage9: 保存已解析值用于输出脱敏；若没有这行代码，页面回显密码时无法清理。

    def resolve(self, secret_ref: str) -> ResolvedBrowserSecret:  # 新增代码+BrowserSecretStage9: 解析 env:NAME 格式秘密引用；若没有这行代码，browser_type_secret 无法统一安全读取。
        ref = str(secret_ref).strip()  # 新增代码+BrowserSecretStage9: 清理引用文本；若没有这行代码，复制时的空格会导致查找失败。
        if not ref.startswith("env:"):  # 新增代码+BrowserSecretStage9: 目前只允许环境变量引用；若没有这行代码，文件路径等敏感来源可能被模型读取。
            raise PermissionError("browser secret 只支持 env: 前缀引用。")  # 新增代码+BrowserSecretStage9: 明确拒绝不支持来源；若没有这行代码，用户不知道格式。
        env_name = ref.removeprefix("env:")  # 新增代码+BrowserSecretStage9: 提取环境变量名；若没有这行代码，os.environ 会查错键。
        if not any(env_name.startswith(prefix) for prefix in self.allowed_env_prefixes):  # 新增代码+BrowserSecretStage9: 校验白名单前缀；若没有这行代码，模型可能读取 PATH、HOME 等。
            raise PermissionError("browser secret 环境变量必须使用安全前缀。")  # 新增代码+BrowserSecretStage9: 返回权限错误；若没有这行代码，拒绝原因不清楚。
        value = os.environ.get(env_name, "")  # 新增代码+BrowserSecretStage9: 读取真实 secret 值；若没有这行代码，页面无法收到敏感输入。
        if value == "":  # 新增代码+BrowserSecretStage9: 拒绝空 secret；若没有这行代码，缺配置会把表单清空还假装成功。
            raise PermissionError(f"browser secret 未找到或为空：{env_name}")  # 新增代码+BrowserSecretStage9: 只回显变量名；若没有这行代码，用户无法定位缺哪个配置。
        self._known_secret_values.add(value)  # 新增代码+BrowserSecretStage9: 登记值供后续脱敏；若没有这行代码，输出回显仍可能泄露。
        return ResolvedBrowserSecret(value=value, audit_name=f"env:{env_name}")  # 新增代码+BrowserSecretStage9: 返回真实值和审计名；若没有这行代码，调用方拿不到解析结果。

    def redact_text(self, text: str) -> str:  # 新增代码+BrowserSecretStage9: 从输出文本中移除已知 secret 值；若没有这行代码，最终回答可能泄露密码。
        redacted = str(text)  # 新增代码+BrowserSecretStage9: 复制文本用于替换；若没有这行代码，None 等输入不稳定。
        for secret_value in sorted(self._known_secret_values, key=len, reverse=True):  # 新增代码+BrowserSecretStage9: 长 secret 先替换；若没有这行代码，短值可能破坏长值匹配。
            if secret_value:  # 新增代码+BrowserSecretStage9: 跳过空值；若没有这行代码，空字符串替换会污染文本。
                redacted = redacted.replace(secret_value, REDACTED_VALUE)  # 新增代码+BrowserSecretStage9: 替换真实 secret；若没有这行代码，敏感内容会泄露。
        return redacted  # 新增代码+BrowserSecretStage9: 返回脱敏文本；若没有这行代码，调用方拿不到结果。
