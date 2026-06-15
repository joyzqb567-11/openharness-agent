"""Computer Use MCP v2 授权工具。"""  # 新增代码+ComputerUseMcpV2：说明本文件处理 request_access 和授权状态；如果没有这行代码，权限逻辑会混入动作执行。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

import json  # 新增代码+ComputerUseMcpV2：导入 JSON 用于生成授权提示；如果没有这行代码，权限说明无法稳定格式化。
from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，参数类型不清楚。

from .errors import error_result  # 新增代码+ComputerUseMcpV2：导入统一失败结果；如果没有这行代码，授权拒绝格式会漂移。
from .result_blocks import success_result  # 新增代码+ComputerUseMcpV2：导入统一成功结果；如果没有这行代码，授权成功格式会漂移。
from .types import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2：导入上下文；如果没有这行代码，权限工具拿不到回调和状态。


def request_access(context: ComputerUseMcpV2Context, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，执行授权申请；如果没有这段函数，模型无法通过 v2 请求权限。
    applications = list(arguments.get("applications", []) or [])  # 新增代码+ComputerUseMcpV2：读取应用列表；如果没有这行代码，授权状态不知道目标应用。
    reason = str(arguments.get("reason", "") or "")  # 新增代码+ComputerUseMcpV2：读取申请原因；如果没有这行代码，用户无法知道为什么要授权。
    prompt = "Computer Use v2 请求控制应用：\n" + json.dumps({"applications": applications, "reason": reason}, ensure_ascii=False, indent=2)  # 新增代码+ComputerUseMcpV2：生成用户可读授权提示；如果没有这行代码，ask_permission 缺少上下文。
    allowed = bool(context.ask_permission(prompt)) if callable(context.ask_permission) else True  # 新增代码+ComputerUseMcpV2：调用 agent 权限回调或独立模式默认记录；如果没有这行代码，授权无法进入主循环确认。
    if not allowed:  # 新增代码+ComputerUseMcpV2：检查用户是否拒绝；如果没有这行代码，拒绝也会被当成授权。
        return error_result("request_access", "user_denied_computer_use_v2_access", error_class="permission_denied")  # 新增代码+ComputerUseMcpV2：返回权限拒绝结果；如果没有这行代码，模型不知道授权没有成功。
    context.grants["applications"] = applications  # 新增代码+ComputerUseMcpV2：保存授权应用摘要；如果没有这行代码，list_granted_applications 看不到授权范围。
    context.grants["reason"] = reason  # 新增代码+ComputerUseMcpV2：保存授权原因；如果没有这行代码，审计缺少申请目的。
    return success_result("request_access", {"applications": applications, "reason": reason, "granted": True})  # 新增代码+ComputerUseMcpV2：返回授权成功摘要；如果没有这行代码，模型无法继续下一步。
# 新增代码+ComputerUseMcpV2：函数段结束，request_access 到此结束；如果没有这个边界说明，用户不容易看出授权申请范围。


def list_granted_applications(context: ComputerUseMcpV2Context) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，查询授权状态；如果没有这段函数，模型无法确认当前权限。
    return success_result("list_granted_applications", {"grants": dict(context.grants)})  # 新增代码+ComputerUseMcpV2：返回授权摘要副本；如果没有这行代码，调用方可能污染上下文。
# 新增代码+ComputerUseMcpV2：函数段结束，list_granted_applications 到此结束；如果没有这个边界说明，用户不容易看出授权查询范围。

