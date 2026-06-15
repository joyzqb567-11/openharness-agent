"""新增代码+DailyChromeProfile: 这里集中识别浏览器 profile 意图；如果没有本文件，登录态、隔离调试和敏感数据请求会散落在各层靠猜测判断。"""
from __future__ import annotations  # 新增代码+DailyChromeProfile: 延迟解析类型注解；如果没有这行，未来类型互相引用时更容易产生导入顺序问题。

from dataclasses import dataclass, field  # 新增代码+DailyChromeProfile: 使用 dataclass 表达只读意图结果；如果没有这行，需要手写初始化代码且更容易漏字段。
from typing import Mapping, Sequence  # 新增代码+DailyChromeProfile: 引入只读映射和序列类型；如果没有这行，函数签名不能清楚说明参数边界。


DAILY_PROFILE_MARKERS: tuple[str, ...] = (  # 新增代码+DailyChromeProfile: 定义需要用户日常 Chrome 登录态的关键词；如果没有这组词，模型说“已登录”时系统仍可能误走隔离 profile。
    "我的 chrome",  # 新增代码+DailyChromeProfile: 覆盖用户常见的“我的 chrome”写法；如果没有这项，小写英文混中文的表达可能漏判。
    "我的Chrome",  # 新增代码+DailyChromeProfile: 覆盖用户常见的“我的Chrome”写法；如果没有这项，中文和英文连写时可能漏判。
    "本地 Google Chrome",  # 新增代码+DailyChromeProfile: 覆盖用户强调本地真实 Chrome 的表达；如果没有这项，真实桌面 Chrome 需求可能被当成普通浏览器。
    "当前 chrome",  # 新增代码+DailyChromeProfile: 覆盖当前 Chrome 的小写表达；如果没有这项，当前浏览器任务可能误走独立 Chromium。
    "当前Chrome",  # 新增代码+DailyChromeProfile: 覆盖当前 Chrome 的中文连写表达；如果没有这项，常见中文 prompt 可能漏判。
    "我的浏览器",  # 新增代码+DailyChromeProfile: 覆盖用户说“我的浏览器”的表达；如果没有这项，用户个人登录态边界不清楚。
    "已登录",  # 新增代码+DailyChromeProfile: 覆盖最关键的登录态词；如果没有这项，千问等账号站点会继续被误判。
    "登录态",  # 新增代码+DailyChromeProfile: 覆盖技术化的登录态表达；如果没有这项，验收 prompt 可能漏判。
    "保持登录态",  # 新增代码+DailyChromeProfile: 覆盖用户要求保持已有会话的表达；如果没有这项，系统可能错误启动干净 profile。
    "不要重新登录",  # 新增代码+DailyChromeProfile: 覆盖用户不想重新登录的表达；如果没有这项，任务会忽略保留会话的意图。
    "使用我已登录的账号",  # 新增代码+DailyChromeProfile: 覆盖账号身份继承表达；如果没有这项，账号上下文任务可能误走无账号浏览器。
    "oauth",  # 新增代码+DailyChromeProfile: 覆盖 OAuth 小写表达；如果没有这项，授权流程可能被错误放进隔离浏览器。
    "OAuth",  # 新增代码+DailyChromeProfile: 覆盖 OAuth 标准大小写表达；如果没有这项，授权流程关键字可能漏判。
    "当前标签页",  # 新增代码+DailyChromeProfile: 覆盖复用当前 tab 的表达；如果没有这项，系统可能新开隔离页面。
    "现有标签页",  # 新增代码+DailyChromeProfile: 覆盖复用已有 tab 的表达；如果没有这项，当前浏览器上下文可能丢失。
    "千问",  # 新增代码+DailyChromeProfile: 覆盖本次压力测试的中文站点名；如果没有这项，千问登录态测试容易走错 profile。
    "qianwen",  # 新增代码+DailyChromeProfile: 覆盖千问英文域名关键词；如果没有这项，URL 形式的千问需求可能漏判。
)  # 新增代码+DailyChromeProfile: 结束日常 profile 关键词集合；如果没有这行，Python 元组语法不完整。


ISOLATED_DEBUG_MARKERS: tuple[str, ...] = (  # 新增代码+DailyChromeProfile: 定义允许隔离 debug profile 的关键词；如果没有这组词，安全 smoke 测试会被误拦截。
    "隔离 debug profile",  # 新增代码+DailyChromeProfile: 覆盖用户明确要求隔离 debug profile；如果没有这项，调试场景可能被误判为日常登录态。
    "debug profile",  # 新增代码+DailyChromeProfile: 覆盖英文 debug profile；如果没有这项，工程师常用表达可能漏判。
    "干净浏览器",  # 新增代码+DailyChromeProfile: 覆盖不带登录态的干净浏览器表达；如果没有这项，公开网页 smoke 会被不必要阻断。
    "不需要登录态",  # 新增代码+DailyChromeProfile: 覆盖明确不需要登录态；如果没有这项，用户主动降风险的表达不会生效。
    "不要使用我的登录态",  # 新增代码+DailyChromeProfile: 覆盖明确不碰个人账号；如果没有这项，安全边界会被误解。
    "公开页面 smoke",  # 新增代码+DailyChromeProfile: 覆盖公开页面冒烟测试；如果没有这项，自动化健康检查会被误判。
)  # 新增代码+DailyChromeProfile: 结束隔离 debug 关键词集合；如果没有这行，Python 元组语法不完整。


SENSITIVE_SECRET_MARKERS: tuple[str, ...] = (  # 新增代码+DailyChromeProfile: 定义必须拒绝的敏感数据关键词；如果没有这组词，真实登录态接管可能被滥用于凭据导出。
    "cookie",  # 新增代码+DailyChromeProfile: 覆盖 cookie 小写表达；如果没有这项，最常见的会话凭据请求不会被拦住。
    "Cookie",  # 新增代码+DailyChromeProfile: 覆盖 Cookie 大写表达；如果没有这项，大小写变化可能绕过拒绝。
    "token",  # 新增代码+DailyChromeProfile: 覆盖 token 小写表达；如果没有这项，访问令牌请求不会被拦住。
    "Token",  # 新增代码+DailyChromeProfile: 覆盖 Token 大写表达；如果没有这项，大小写变化可能绕过拒绝。
    "密码",  # 新增代码+DailyChromeProfile: 覆盖中文密码表达；如果没有这项，账号秘密请求不会被拦住。
    "localStorage",  # 新增代码+DailyChromeProfile: 覆盖浏览器本地存储 API；如果没有这项，站点凭据可能被脚本读出。
    "sessionStorage",  # 新增代码+DailyChromeProfile: 覆盖浏览器会话存储 API；如果没有这项，会话内敏感状态可能被读出。
    "本地存储",  # 新增代码+DailyChromeProfile: 覆盖 localStorage 的中文表达；如果没有这项，中文 prompt 可能绕过拒绝。
)  # 新增代码+DailyChromeProfile: 结束敏感关键词集合；如果没有这行，Python 元组语法不完整。


@dataclass(frozen=True)  # 新增代码+DailyChromeProfile: 冻结意图对象避免下游意外改写；如果没有这行，路由层可能污染识别结果。
class DailyProfileIntent:  # 新增代码+DailyChromeProfile: 定义日常 Chrome profile 意图结果；如果没有这个类，下游只能传散乱 dict 且容易漏字段。
    requires_daily_profile: bool  # 新增代码+DailyChromeProfile: 表示是否必须接入用户日常 profile；如果没有这字段，连接层无法禁止 debug fallback。
    allows_debug_profile: bool  # 新增代码+DailyChromeProfile: 表示是否允许隔离 debug profile；如果没有这字段，公开 smoke 和登录态任务无法区分。
    profile_intent: str  # 新增代码+DailyChromeProfile: 保存机器可读意图名；如果没有这字段，事件日志和工具参数只能解析自然语言。
    requires_refusal: bool = False  # 新增代码+DailyChromeProfile: 表示是否必须拒绝请求；如果没有这字段，cookie/token 请求可能进入执行层。
    reason_codes: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+DailyChromeProfile: 保存触发原因码；如果没有这字段，排查时不知道是哪条规则命中。


def _contains_any(text: str, markers: Sequence[str]) -> bool:  # 新增代码+DailyChromeProfile: 统一判断文本是否命中任一关键词；如果没有这个函数，多处会重复写易错匹配逻辑。
    lowered = text.lower()  # 新增代码+DailyChromeProfile: 准备小写文本用于英文大小写不敏感匹配；如果没有这行，OAuth/token 等大小写变化可能漏判。
    return any(marker.lower() in lowered for marker in markers)  # 新增代码+DailyChromeProfile: 返回是否命中关键词；如果没有这行，意图识别没有实际判断结果。


def detect_profile_intent(user_input: str, tool_name: str, arguments: Mapping[str, object] | None = None) -> DailyProfileIntent:  # 新增代码+DailyChromeProfile: 把用户输入、工具名和参数合并识别 profile 意图；如果没有这函数，路由和连接层无法共享同一判断。
    text = f"{user_input or ''} {tool_name or ''} {arguments or {}}"  # 新增代码+DailyChromeProfile: 合并可见上下文做关键词匹配；如果没有这行，URL 或工具参数中的 qianwen/登录态线索可能被漏掉。
    reason_codes: list[str] = []  # 新增代码+DailyChromeProfile: 准备原因码列表；如果没有这行，后续无法向用户解释为什么这样路由。
    has_sensitive_marker = _contains_any(text, SENSITIVE_SECRET_MARKERS)  # 新增代码+DailyChromeProfile: 检测是否请求敏感凭据；如果没有这行，cookie/token 风险无法提前拦截。
    if has_sensitive_marker:  # 新增代码+DailyChromeProfile: 命中敏感数据时记录原因；如果没有这行，拒绝结果缺少审计线索。
        reason_codes.append("cookie_secret_marker")  # 新增代码+DailyChromeProfile: 写入敏感凭据原因码；如果没有这行，测试和日志无法确认拒绝来源。
    has_daily_marker = _contains_any(text, DAILY_PROFILE_MARKERS)  # 新增代码+DailyChromeProfile: 检测是否需要日常登录态；如果没有这行，登录态任务无法被识别。
    if has_daily_marker:  # 新增代码+DailyChromeProfile: 命中日常 profile 需求时记录原因；如果没有这行，路由结果缺少登录态证据。
        reason_codes.append("logged_in_marker")  # 新增代码+DailyChromeProfile: 写入登录态原因码；如果没有这行，测试和日志无法确认命中登录态规则。
    has_debug_marker = _contains_any(text, ISOLATED_DEBUG_MARKERS)  # 新增代码+DailyChromeProfile: 检测是否明确允许隔离调试；如果没有这行，安全 smoke 会被误判。
    if has_debug_marker:  # 新增代码+DailyChromeProfile: 命中隔离调试需求时记录原因；如果没有这行，调试路线缺少审计线索。
        reason_codes.append("isolated_debug_marker")  # 新增代码+DailyChromeProfile: 写入隔离调试原因码；如果没有这行，测试无法确认隔离意图被识别。
    if has_sensitive_marker:  # 新增代码+DailyChromeProfile: 敏感数据请求优先拒绝；如果没有这行，cookie/token 请求可能继续进入浏览器执行层。
        return DailyProfileIntent(requires_daily_profile=has_daily_marker, allows_debug_profile=False, profile_intent="refuse_sensitive_secret", requires_refusal=True, reason_codes=tuple(reason_codes))  # 新增代码+DailyChromeProfile: 返回拒绝意图并禁止 debug 兜底；如果没有这行，敏感请求没有统一出口。
    if has_daily_marker and not has_debug_marker:  # 新增代码+DailyChromeProfile: 登录态需求且未明确要求隔离时进入日常 profile；如果没有这行，千问登录态任务可能继续走隔离 profile。
        return DailyProfileIntent(requires_daily_profile=True, allows_debug_profile=False, profile_intent="daily_login", reason_codes=tuple(reason_codes))  # 新增代码+DailyChromeProfile: 返回日常登录态意图；如果没有这行，连接层无法硬性禁止 debug fallback。
    if has_debug_marker:  # 新增代码+DailyChromeProfile: 明确隔离调试时允许 debug profile；如果没有这行，公开 smoke 会被登录态门禁误伤。
        return DailyProfileIntent(requires_daily_profile=False, allows_debug_profile=True, profile_intent="isolated_debug", reason_codes=tuple(reason_codes))  # 新增代码+DailyChromeProfile: 返回隔离调试意图；如果没有这行，测试环境无法安全使用干净 profile。
    return DailyProfileIntent(requires_daily_profile=False, allows_debug_profile=True, profile_intent="public_or_unknown", reason_codes=tuple(reason_codes))  # 新增代码+DailyChromeProfile: 默认普通公开任务允许隔离环境；如果没有这行，未知任务没有安全默认值。
