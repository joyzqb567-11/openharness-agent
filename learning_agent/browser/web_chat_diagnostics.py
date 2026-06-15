"""网页聊天压力测试的通用验收字段 helper。"""  # 新增代码+WebChatDiagnostics：说明本模块服务千问、元宝、ChatGPT 等同类网页聊天站点；如果没有这一行，读者可能误以为这里只是千问专用。
from __future__ import annotations  # 新增代码+WebChatDiagnostics：启用延迟类型解析；如果没有这一行，未来类型标注升级时更容易出运行时导入问题。

from typing import Any  # 新增代码+WebChatDiagnostics：导入 Any 描述外部验收报告里的动态字段；如果没有这一行，函数签名可读性较差。


WEB_CHAT_FAILURE_CLASSES = ("none", "external_block", "tool_locator_failure", "tool_send_failure", "tool_observation_failure", "unknown")  # 新增代码+WebChatDiagnostics：定义网页聊天失败分类枚举；如果没有这一行，报告会继续发散成站点专用字段。


def normalize_web_chat_failure_class(value: Any) -> str:  # 新增代码+WebChatDiagnostics：函数段开始，规范化网页聊天失败分类；如果没有这段函数，验收报告可能出现大小写或拼写漂移。
    text = str(value or "").strip().lower()  # 新增代码+WebChatDiagnostics：把输入转成小写短文本；如果没有这一行，None 或大写字段会影响判断。
    return text if text in WEB_CHAT_FAILURE_CLASSES else "unknown"  # 新增代码+WebChatDiagnostics：只允许固定枚举，否则归 unknown；如果没有这一行，验收矩阵无法稳定统计失败原因。
# 新增代码+WebChatDiagnostics：函数段结束，normalize_web_chat_failure_class 到此结束；如果没有这个边界说明，初学者不容易看出分类规范范围。


def infer_web_chat_failure_class(*, input_verified: bool, send_verified: bool, response_observed: bool, block_reason: str = "") -> str:  # 新增代码+WebChatDiagnostics：函数段开始，根据通用布尔字段推导失败类型；如果没有这段函数，报告作者需要手工猜失败分类。
    if block_reason:  # 新增代码+WebChatDiagnostics：优先把登录、验证码、风控等原因视为外部阻塞；如果没有这一行，外部环境问题会被误判成工具 bug。
        return "external_block"  # 新增代码+WebChatDiagnostics：返回外部阻塞分类；如果没有这一行，验收无法区分系统缺陷和网站限制。
    if not input_verified:  # 新增代码+WebChatDiagnostics：输入未验证时归为定位或输入工具问题；如果没有这一行，过期元素问题会被漏掉。
        return "tool_locator_failure"  # 新增代码+WebChatDiagnostics：返回定位失败分类；如果没有这一行，旧 element_id 的真实失败类型不可见。
    if not send_verified:  # 新增代码+WebChatDiagnostics：输入成功但发送未确认时归发送问题；如果没有这一行，按钮不可点和回车失败无法被单独统计。
        return "tool_send_failure"  # 新增代码+WebChatDiagnostics：返回发送失败分类；如果没有这一行，发送环节缺陷会混入未知失败。
    if not response_observed:  # 新增代码+WebChatDiagnostics：发送成功但没有观察到回复时归观察问题；如果没有这一行，模型回复慢或页面状态读不到无法区分。
        return "tool_observation_failure"  # 新增代码+WebChatDiagnostics：返回观察失败分类；如果没有这一行，后续修复方向不清楚。
    return "none"  # 新增代码+WebChatDiagnostics：全部关键门禁通过时无失败；如果没有这一行，成功报告也可能显示 unknown。
# 新增代码+WebChatDiagnostics：函数段结束，infer_web_chat_failure_class 到此结束；如果没有这个边界说明，初学者不容易看出推导范围。


def build_web_chat_report(*, provider: str, url: str, locator_recovered: bool, input_verified: bool, send_verified: bool, response_observed: bool, block_reason: str = "", failure_class: str = "") -> dict[str, Any]:  # 新增代码+WebChatDiagnostics：函数段开始，构造通用网页聊天验收报告；如果没有这段函数，后续每个站点都会新增一套字段。
    normalized_block_reason = str(block_reason or "").strip()  # 新增代码+WebChatDiagnostics：清洗外部阻塞原因；如果没有这一行，换行或空格会污染报告。
    normalized_failure = normalize_web_chat_failure_class(failure_class) if failure_class else infer_web_chat_failure_class(input_verified=input_verified, send_verified=send_verified, response_observed=response_observed, block_reason=normalized_block_reason)  # 新增代码+WebChatDiagnostics：优先使用显式分类，否则按门禁推导；如果没有这一行，报告分类不能自动一致。
    return {  # 新增代码+WebChatDiagnostics：返回统一字段字典；如果没有这一行，验收器拿不到机器可读结构。
        "web_chat_provider": str(provider or "").strip(),  # 新增代码+WebChatDiagnostics：记录站点提供方，例如 qianwen 或 chatgpt；如果没有这一行，通用字段无法区分目标站点。
        "web_chat_url": str(url or "").strip(),  # 新增代码+WebChatDiagnostics：记录站点 URL；如果没有这一行，复盘时不知道测试页面地址。
        "web_chat_locator_recovered": bool(locator_recovered),  # 新增代码+WebChatDiagnostics：记录是否恢复定位；如果没有这一行，S7 R3 无法证明 element_id 失效已被治本处理。
        "web_chat_input_verified": bool(input_verified),  # 新增代码+WebChatDiagnostics：记录输入是否真实进入输入框；如果没有这一行，工具可能假装输入成功。
        "web_chat_send_verified": bool(send_verified),  # 新增代码+WebChatDiagnostics：记录消息是否真实发送；如果没有这一行，无法区分输入成功和提交成功。
        "web_chat_response_observed": bool(response_observed),  # 新增代码+WebChatDiagnostics：记录是否观察到回复或阻塞状态；如果没有这一行，页面后续结果不可审计。
        "web_chat_failure_class": normalized_failure,  # 新增代码+WebChatDiagnostics：记录通用失败分类；如果没有这一行，成熟度判定无法聚合失败原因。
        "web_chat_block_reason": normalized_block_reason,  # 新增代码+WebChatDiagnostics：记录登录、验证码、风控等外部阻塞；如果没有这一行，外部限制会被误认为工具失败。
    }  # 新增代码+WebChatDiagnostics：结束报告字典；如果没有这一行，Python 字典语法不完整。
# 新增代码+WebChatDiagnostics：函数段结束，build_web_chat_report 到此结束；如果没有这个边界说明，初学者不容易看出报告范围。


__all__ = ["WEB_CHAT_FAILURE_CLASSES", "build_web_chat_report", "infer_web_chat_failure_class", "normalize_web_chat_failure_class"]  # 新增代码+WebChatDiagnostics：限定公开导出；如果没有这一行，外部可能误用内部常量之外的细节。
