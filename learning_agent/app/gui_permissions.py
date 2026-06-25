"""Helpers for Desktop GUI permission requests and audit payloads."""  # 新增代码+DesktopGUIPermissionsV2：说明本模块只负责 GUI 权限请求规范化；如果没有这行，维护者容易把权限逻辑继续塞回 bridge。
from __future__ import annotations  # 新增代码+DesktopGUIPermissionsV2：启用延迟类型解析；如果没有这行，未来互相引用类型时更容易受定义顺序影响。

import re  # 新增代码+DesktopGUIPermissionsV2：导入正则用于脱敏本机路径和凭证；如果没有这行，权限文案只能做脆弱字符串替换。
import time  # 新增代码+DesktopGUIPermissionsV2：记录权限请求创建时间；如果没有这行，审计 payload 缺少稳定时间事实。
from typing import Any  # 新增代码+DesktopGUIPermissionsV2：标注可接收任意 payload 对象；如果没有这行，helper 边界类型不清楚。


_WINDOWS_PATH_PATTERN = re.compile(r"[A-Za-z]:\\(?:[^\s\\/:*?\"<>|]+\\)*[^\s\\/:*?\"<>|]+")  # 新增代码+DesktopGUIPermissionsV2：匹配 Windows 本机路径；如果没有这行，GUI 可能把用户私有目录展示出来。
_SECRET_REPLACEMENTS = (  # 新增代码+DesktopGUIPermissionsV2：集中列出凭证脱敏规则；如果没有这段，密钥正则会散落在多个函数里。
    (re.compile(r"sk-[A-Za-z0-9_\-]{6,}"), "[密钥已隐藏]"),  # 新增代码+DesktopGUIPermissionsV2：隐藏 OpenAI 风格密钥；如果没有这行，权限原因可能泄露 API key。
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-]+"), "Bearer [凭证已隐藏]"),  # 新增代码+DesktopGUIPermissionsV2：隐藏 bearer token；如果没有这行，风险摘要可能暴露登录凭证。
    (re.compile(r"(?i)\b(api[_-]?key\s*[:=]\s*)[^\s,;]+"), r"\1[凭证已隐藏]"),  # 新增代码+DesktopGUIPermissionsV2：隐藏 api_key 形式凭证；如果没有这行，工具参数可能把密钥直接带进 UI。
)  # 新增代码+DesktopGUIPermissionsV2：凭证脱敏规则结束；如果没有这行，元组语法不完整。
_APPROVE_DECISIONS = {"approve", "approved", "allow", "allowed", "yes", "y"}  # 新增代码+DesktopGUIPermissionsV2：定义允许决策别名；如果没有这行，前端文案或大小写变化容易被拒。
_DENY_DECISIONS = {"deny", "denied", "reject", "rejected", "no", "n"}  # 新增代码+DesktopGUIPermissionsV2：定义拒绝决策别名；如果没有这行，拒绝别名不能进入统一审计。


def redact_permission_text(value: object) -> str:  # 新增代码+DesktopGUIPermissionsV2：函数段开始，脱敏权限展示文本；如果没有这段，路径和凭证可能直接显示在 GUI。
    text = str(value or "").strip()  # 新增代码+DesktopGUIPermissionsV2：把未知输入收敛成字符串；如果没有这行，None 或对象值会破坏正则处理。
    text = _WINDOWS_PATH_PATTERN.sub("[本机路径已隐藏]", text)  # 新增代码+DesktopGUIPermissionsV2：隐藏本机路径；如果没有这行，用户目录、桌面文件名可能泄露到弹窗。
    for pattern, replacement in _SECRET_REPLACEMENTS:  # 新增代码+DesktopGUIPermissionsV2：逐条应用凭证脱敏规则；如果没有这行，只能覆盖一种密钥格式。
        text = pattern.sub(replacement, text)  # 新增代码+DesktopGUIPermissionsV2：替换当前匹配的敏感片段；如果没有这行，规则不会真正生效。
    return text  # 新增代码+DesktopGUIPermissionsV2：返回脱敏后的安全文本；如果没有这行，调用方拿不到处理结果。
# 新增代码+DesktopGUIPermissionsV2：函数段结束，redact_permission_text 到此结束；如果没有边界说明，初学者不易看出它只负责文本脱敏。


def normalize_permission_decision(decision: str) -> str:  # 新增代码+DesktopGUIPermissionsV2：函数段开始，把 GUI 决策收敛成 approve/deny；如果没有这段，审计状态会出现多种写法。
    clean_decision = decision.strip().lower()  # 新增代码+DesktopGUIPermissionsV2：清理空格并统一大小写；如果没有这行，APPROVED 这类常见输入会失败。
    if clean_decision in _APPROVE_DECISIONS:  # 新增代码+DesktopGUIPermissionsV2：识别允许别名；如果没有这行，allow/yes 不能进入允许分支。
        return "approve"  # 新增代码+DesktopGUIPermissionsV2：返回统一允许值；如果没有这行，后端状态不能稳定比较。
    if clean_decision in _DENY_DECISIONS:  # 新增代码+DesktopGUIPermissionsV2：识别拒绝别名；如果没有这行，reject/no 不能进入拒绝分支。
        return "deny"  # 新增代码+DesktopGUIPermissionsV2：返回统一拒绝值；如果没有这行，拒绝状态不能稳定比较。
    raise ValueError("bad_permission_decision")  # 新增代码+DesktopGUIPermissionsV2：抛出规范化失败；如果没有这行，非法值可能被静默当成有效决策。
# 新增代码+DesktopGUIPermissionsV2：函数段结束，normalize_permission_decision 到此结束；如果没有边界说明，初学者不易看出决策清洗范围。


def build_permission_action_summary(tool_name: str, app_name: str) -> str:  # 新增代码+DesktopGUIPermissionsV2：函数段开始，生成权限弹窗动作摘要；如果没有这段，前端要自己拼后端字段。
    clean_tool_name = tool_name.strip()  # 新增代码+DesktopGUIPermissionsV2：清理工具名；如果没有这行，弹窗可能显示多余空白。
    clean_app_name = app_name.strip() or "OpenHarness"  # 新增代码+DesktopGUIPermissionsV2：清理应用名并提供兜底；如果没有这行，摘要可能缺主语。
    if clean_tool_name:  # 新增代码+DesktopGUIPermissionsV2：判断是否有具体工具名；如果没有这行，有工具和无工具场景无法区分。
        return f"{clean_app_name} 将通过 {clean_tool_name} 继续执行"  # 新增代码+DesktopGUIPermissionsV2：返回含工具名摘要；如果没有这行，用户不知道具体工具来源。
    return f"{clean_app_name} 请求继续执行"  # 新增代码+DesktopGUIPermissionsV2：返回仅应用名摘要；如果没有这行，无工具场景没有可读摘要。
# 新增代码+DesktopGUIPermissionsV2：函数段结束，build_permission_action_summary 到此结束；如果没有边界说明，初学者不易看出摘要生成范围。


def normalize_permission_request_fields(  # 新增代码+DesktopGUIPermissionsV2：函数段开始，统一清洗权限请求字段；如果没有这段，bridge 和 future adapter 会各写一套规则。
    request_id: str,  # 新增代码+DesktopGUIPermissionsV2：接收权限请求 id；如果没有这行，前端无法定位要回答的权限。
    turn_id: str = "",  # 新增代码+DesktopGUIPermissionsV2：接收关联 turn id；如果没有这行，权限事件无法同步到消息。
    run_id: str = "",  # 新增代码+DesktopGUIPermissionsV2：接收关联 run id；如果没有这行，trace panel 无法按 run 聚合。
    session_id: str = "",  # 新增代码+DesktopGUIPermissionsV2：接收关联 session id；如果没有这行，权限事件无法归属会话。
    tool_name: str = "",  # 新增代码+DesktopGUIPermissionsV2：接收工具名；如果没有这行，用户看不到哪个工具要权限。
    app_name: str = "",  # 新增代码+DesktopGUIPermissionsV2：接收应用名；如果没有这行，弹窗缺少人类可读来源。
    reason: str = "",  # 新增代码+DesktopGUIPermissionsV2：接收请求原因；如果没有这行，用户无法判断是否允许。
    risk_summary: str = "",  # 新增代码+DesktopGUIPermissionsV2：接收风险摘要；如果没有这行，权限弹窗缺少安全上下文。
    created_at: float | None = None,  # 新增代码+DesktopGUIPermissionsV2：允许测试固定创建时间；如果没有这行，合同测试会不稳定。
) -> dict[str, Any]:  # 新增代码+DesktopGUIPermissionsV2：声明返回字典字段；如果没有这行，调用方不知道 helper 输出形状。
    clean_tool_name = tool_name.strip()  # 新增代码+DesktopGUIPermissionsV2：清理工具名；如果没有这行，payload 会保留无意义空白。
    clean_app_name = app_name.strip() or clean_tool_name or "OpenHarness"  # 新增代码+DesktopGUIPermissionsV2：确定展示来源；如果没有这行，空 app_name 会让弹窗失去主语。
    clean_reason = redact_permission_text(reason) or "后端请求继续执行需要用户确认。"  # 新增代码+DesktopGUIPermissionsV2：脱敏并兜底原因；如果没有这行，弹窗可能空白或泄露隐私。
    clean_risk_summary = redact_permission_text(risk_summary) or "请确认该操作符合你的预期。"  # 新增代码+DesktopGUIPermissionsV2：脱敏并兜底风险；如果没有这行，用户缺少判断依据。
    return {  # 新增代码+DesktopGUIPermissionsV2：返回规范化字段集合；如果没有这行，函数没有可用输出。
        "request_id": request_id.strip(),  # 新增代码+DesktopGUIPermissionsV2：保存清理后的 request_id；如果没有这行，前端回传路径可能错位。
        "turn_id": turn_id.strip(),  # 新增代码+DesktopGUIPermissionsV2：保存清理后的 turn_id；如果没有这行，权限和消息无法对齐。
        "run_id": run_id.strip(),  # 新增代码+DesktopGUIPermissionsV2：保存清理后的 run_id；如果没有这行，审计时间线缺少运行身份。
        "session_id": session_id.strip(),  # 新增代码+DesktopGUIPermissionsV2：保存清理后的 session_id；如果没有这行，会话归属不稳定。
        "tool_name": clean_tool_name,  # 新增代码+DesktopGUIPermissionsV2：保存工具名；如果没有这行，前端不能展示工具来源。
        "app_name": clean_app_name,  # 新增代码+DesktopGUIPermissionsV2：保存应用名；如果没有这行，前端不能展示应用来源。
        "action_summary": build_permission_action_summary(clean_tool_name, clean_app_name),  # 新增代码+DesktopGUIPermissionsV2：保存动作摘要；如果没有这行，前端要重复生成摘要。
        "reason": clean_reason,  # 新增代码+DesktopGUIPermissionsV2：保存脱敏原因；如果没有这行，权限弹窗缺少解释。
        "risk_summary": clean_risk_summary,  # 新增代码+DesktopGUIPermissionsV2：保存脱敏风险摘要；如果没有这行，用户缺少安全判断依据。
        "status": "pending",  # 新增代码+DesktopGUIPermissionsV2：初始状态固定 pending；如果没有这行，重复回答检查没有基准。
        "decision": "",  # 新增代码+DesktopGUIPermissionsV2：初始决策为空；如果没有这行，审计可能误判已回答。
        "decision_reason": "",  # 新增代码+DesktopGUIPermissionsV2：初始决策理由为空；如果没有这行，payload 字段形状不稳定。
        "created_at": float(created_at if created_at is not None else time.time()),  # 新增代码+DesktopGUIPermissionsV2：保存创建时间；如果没有这行，trace panel 无法按请求时间排序。
        "answered_at": 0.0,  # 新增代码+DesktopGUIPermissionsV2：初始回答时间为 0；如果没有这行，未回答和已回答难以区分。
    }  # 新增代码+DesktopGUIPermissionsV2：规范化字段集合结束；如果没有这行，字典语法不完整。
# 新增代码+DesktopGUIPermissionsV2：函数段结束，normalize_permission_request_fields 到此结束；如果没有边界说明，初学者不易看出字段清洗范围。


def permission_payload_from_request(permission: object) -> dict[str, Any]:  # 新增代码+DesktopGUIPermissionsV2：函数段开始，把权限对象转成对外事件 payload；如果没有这段，请求和回答事件字段会漂移。
    decision = str(getattr(permission, "decision", ""))  # 新增代码+DesktopGUIPermissionsV2：读取决策字段；如果没有这行，payload 无法判断是否已回答。
    payload = {  # 新增代码+DesktopGUIPermissionsV2：创建对外 payload；如果没有这行，调用方要手写字段映射。
        "request_id": str(getattr(permission, "request_id", "")),  # 新增代码+DesktopGUIPermissionsV2：输出请求 id；如果没有这行，前端无法提交决策。
        "turn_id": str(getattr(permission, "turn_id", "")),  # 新增代码+DesktopGUIPermissionsV2：输出 turn id；如果没有这行，前端无法让后端校验归属。
        "run_id": str(getattr(permission, "run_id", "")),  # 新增代码+DesktopGUIPermissionsV2：输出 run id；如果没有这行，trace panel 聚合缺字段。
        "session_id": str(getattr(permission, "session_id", "")),  # 新增代码+DesktopGUIPermissionsV2：输出 session id；如果没有这行，事件无法归属会话。
        "tool_name": str(getattr(permission, "tool_name", "")),  # 新增代码+DesktopGUIPermissionsV2：输出工具名；如果没有这行，弹窗缺少工具来源。
        "app_name": str(getattr(permission, "app_name", "")),  # 新增代码+DesktopGUIPermissionsV2：输出应用名；如果没有这行，弹窗缺少应用来源。
        "action_summary": str(getattr(permission, "action_summary", "")),  # 新增代码+DesktopGUIPermissionsV2：输出动作摘要；如果没有这行，前端要重复推断。
        "reason": redact_permission_text(getattr(permission, "reason", "")),  # 新增代码+DesktopGUIPermissionsV2：输出二次脱敏原因；如果没有这行，落盘旧数据可能绕过脱敏。
        "risk_summary": redact_permission_text(getattr(permission, "risk_summary", "")),  # 新增代码+DesktopGUIPermissionsV2：输出二次脱敏风险；如果没有这行，旧风险文案可能暴露敏感信息。
        "status": str(getattr(permission, "status", "")),  # 新增代码+DesktopGUIPermissionsV2：输出当前状态；如果没有这行，前端无法区分 pending/denied。
        "decision": decision,  # 新增代码+DesktopGUIPermissionsV2：输出决策；如果没有这行，审计事件无法复盘选择。
        "decision_reason": redact_permission_text(getattr(permission, "decision_reason", "")),  # 新增代码+DesktopGUIPermissionsV2：输出脱敏决策理由；如果没有这行，GUI 点击原因可能泄露敏感内容。
        "created_at": float(getattr(permission, "created_at", 0.0) or 0.0),  # 新增代码+DesktopGUIPermissionsV2：输出创建时间；如果没有这行，trace panel 无法排序请求。
        "answered_at": float(getattr(permission, "answered_at", 0.0) or 0.0),  # 新增代码+DesktopGUIPermissionsV2：输出回答时间；如果没有这行，无法分析用户响应延迟。
    }  # 新增代码+DesktopGUIPermissionsV2：payload 字典结束；如果没有这行，Python 语法不完整。
    if decision:  # 新增代码+DesktopGUIPermissionsV2：仅已回答时追加 approved 布尔值；如果没有这行，pending 请求会出现误导性 approved 字段。
        payload["approved"] = decision == "approve"  # 新增代码+DesktopGUIPermissionsV2：输出允许布尔值；如果没有这行，前端审计视图要自己解析字符串。
    return payload  # 新增代码+DesktopGUIPermissionsV2：返回权限事件 payload；如果没有这行，调用方拿不到统一结构。
# 新增代码+DesktopGUIPermissionsV2：函数段结束，permission_payload_from_request 到此结束；如果没有边界说明，初学者不易看出事件 payload 输出范围。
