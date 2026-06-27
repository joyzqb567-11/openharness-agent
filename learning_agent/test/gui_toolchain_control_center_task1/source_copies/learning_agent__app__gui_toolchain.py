"""Desktop GUI toolchain inventory payload helpers."""  # 新增代码+DesktopGUIToolchain：说明本模块只负责 GUI 工具链清单；如果没有这行，维护者容易把它和工具执行逻辑混在一起。

from __future__ import annotations  # 新增代码+DesktopGUIToolchain：启用延迟类型解析；如果没有这行，后续类型注解在旧运行环境里更容易出错。

from datetime import UTC, datetime  # 新增代码+DesktopGUIToolchain：生成稳定 UTC 时间戳；如果没有这行，GUI 无法知道清单刷新时间。
from pathlib import Path  # 新增代码+DesktopGUIToolchain：标注 workspace 路径类型；如果没有这行，函数签名会退回不清楚的 Any。
from typing import Any  # 新增代码+DesktopGUIToolchain：标注通用 JSON payload；如果没有这行，返回结构边界不清楚。

from learning_agent.app.gui_protocol import GUI_V2_SCHEMA_VERSION  # 新增代码+DesktopGUIToolchain：复用 GUI V2 协议版本；如果没有这行，工具链端点可能和其它 V2 payload 漂移。
from learning_agent.tools.catalog import build_builtin_tool_catalog  # 新增代码+DesktopGUIToolchain：复用已有内置工具目录；如果没有这行，GUI 会被迫硬编码一份工具清单。
from learning_agent.tools.types import AgentTool  # 新增代码+DesktopGUIToolchain：复用工具元数据类型；如果没有这行，helper 无法用清晰字段读取目录。


TOOLCHAIN_GROUP_LABELS: dict[str, str] = {  # 新增代码+DesktopGUIToolchain：分组中文/英文标签表开始；如果没有这段，GUI 只能显示机器化 capability id。
    "core": "Core Tools",  # 新增代码+DesktopGUIToolchain：标记核心读写编辑工具；如果没有这行，基础工具会落入不友好的 unknown 分组。
    "file_operations": "File Operations",  # 新增代码+DesktopGUIToolchain：标记文件操作工具；如果没有这行，文件读写能力无法被用户快速识别。
    "memory": "Memory",  # 新增代码+DesktopGUIToolchain：标记记忆工具；如果没有这行，append_memory 会混在普通工具里。
    "planning": "Planning",  # 新增代码+DesktopGUIToolchain：标记计划工具；如果没有这行，todo/plan 能力不会形成产品化分区。
    "execution": "Execution",  # 新增代码+DesktopGUIToolchain：标记执行工具；如果没有这行，后台命令能力不会进入清晰分组。
    "notebook": "Notebook",  # 新增代码+DesktopGUIToolchain：标记 Notebook 工具；如果没有这行，notebook_read/edit 会缺少分区。
    "mcp": "MCP",  # 新增代码+DesktopGUIToolchain：标记 MCP 工具；如果没有这行，资源/提示/stream 能力不容易被发现。
    "delegation": "Delegation",  # 新增代码+DesktopGUIToolchain：标记子任务和 team 工具；如果没有这行，多 agent 能力会被埋在列表里。
    "diagnostics": "Diagnostics",  # 新增代码+DesktopGUIToolchain：标记诊断工具；如果没有这行，LSP/REPL 能力缺少入口感。
    "long_running_work": "Long Running Work",  # 新增代码+DesktopGUIToolchain：标记长任务工具；如果没有这行，cron/session/status 等能力不易扫描。
    "computer_use": "Computer Use",  # 新增代码+DesktopGUIToolchain：标记桌面控制工具；如果没有这行，Computer Use 工具链不会被产品化强调。
}  # 新增代码+DesktopGUIToolchain：分组标签表结束；如果没有这行，Python 字典语法不完整。

TOOLCHAIN_GROUP_ORDER: list[str] = [  # 新增代码+DesktopGUIToolchain：分组排序表开始；如果没有这段，GUI 顺序会随字典或工具顺序漂移。
    "core",  # 新增代码+DesktopGUIToolchain：核心工具排第一；如果没有这行，用户可能先看到低频工具。
    "file_operations",  # 新增代码+DesktopGUIToolchain：文件工具紧跟核心工具；如果没有这行，开发常用能力不够靠前。
    "planning",  # 新增代码+DesktopGUIToolchain：计划能力靠前；如果没有这行，长任务不跑偏相关工具不明显。
    "execution",  # 新增代码+DesktopGUIToolchain：执行能力靠前；如果没有这行，后台命令链路不易发现。
    "long_running_work",  # 新增代码+DesktopGUIToolchain：长任务能力靠前；如果没有这行，harness 相关能力不够突出。
    "computer_use",  # 新增代码+DesktopGUIToolchain：桌面控制能力靠前；如果没有这行，用户看不出 GUI 已接入真实桌面工具。
    "mcp",  # 新增代码+DesktopGUIToolchain：MCP 能力随后展示；如果没有这行，外部工具生态缺少固定位置。
    "delegation",  # 新增代码+DesktopGUIToolchain：委派能力随后展示；如果没有这行，子 agent 工具会散在后面。
    "diagnostics",  # 新增代码+DesktopGUIToolchain：诊断能力随后展示；如果没有这行，排查工具不易找到。
    "notebook",  # 新增代码+DesktopGUIToolchain：Notebook 能力随后展示；如果没有这行，notebook 工具可能漂移。
    "memory",  # 新增代码+DesktopGUIToolchain：记忆能力最后展示；如果没有这行，低频 append_memory 可能插入其它分组。
]  # 新增代码+DesktopGUIToolchain：分组排序表结束；如果没有这行，Python 列表语法不完整。


def _tool_group_id(tool: AgentTool) -> str:  # 新增代码+DesktopGUIToolchain：函数段开始，计算工具所属 GUI 分组；如果没有这段，工具分组逻辑会散落在 payload 构建里。
    return tool.capability_pack.strip() or "core"  # 新增代码+DesktopGUIToolchain：优先使用已有 capability_pack，空值归入 core；如果没有这行，未映射工具会丢失分组。
# 新增代码+DesktopGUIToolchain：函数段结束，_tool_group_id 到此结束；如果没有边界说明，初学者不易看出分组规则。


def _tool_status(tool: AgentTool) -> str:  # 新增代码+DesktopGUIToolchain：函数段开始，把工具元数据转成 GUI 状态；如果没有这段，前端只能靠布尔值猜工具可见性。
    if tool.always_load:  # 新增代码+DesktopGUIToolchain：判断工具是否首轮常驻；如果没有这行，核心工具和延迟工具无法区分。
        return "ready"  # 新增代码+DesktopGUIToolchain：常驻工具标记 ready；如果没有这行，GUI 无法显示核心能力已就绪。
    if tool.should_defer:  # 新增代码+DesktopGUIToolchain：判断工具是否延迟加载；如果没有这行，低频工具会被误认为已首轮暴露。
        return "deferred"  # 新增代码+DesktopGUIToolchain：延迟工具标记 deferred；如果没有这行，用户看不出工具可通过 tool_search 激活。
    return "available"  # 新增代码+DesktopGUIToolchain：其它工具标记 available；如果没有这行，函数可能返回 None。
# 新增代码+DesktopGUIToolchain：函数段结束，_tool_status 到此结束；如果没有边界说明，初学者不易看出状态映射范围。


def _tool_payload(tool: AgentTool) -> dict[str, Any]:  # 新增代码+DesktopGUIToolchain：函数段开始，把 AgentTool 转成 GUI 安全字段；如果没有这段，前端会直接依赖内部 dataclass。
    return {  # 新增代码+DesktopGUIToolchain：返回单个工具 payload；如果没有这行，函数无法输出 JSON 对象。
        "name": tool.name,  # 新增代码+DesktopGUIToolchain：暴露工具名；如果没有这行，GUI 列表没有主键。
        "description": tool.description,  # 新增代码+DesktopGUIToolchain：暴露工具说明；如果没有这行，用户不知道工具用途。
        "category": _tool_group_id(tool),  # 新增代码+DesktopGUIToolchain：暴露能力分组；如果没有这行，前端无法做筛选和徽标。
        "source": tool.source,  # 新增代码+DesktopGUIToolchain：暴露内置/MCP 来源；如果没有这行，用户看不出工具来自哪里。
        "available": True,  # 新增代码+DesktopGUIToolchain：标记工具在目录中可用；如果没有这行，前端无法统一渲染状态灯。
        "status": _tool_status(tool),  # 新增代码+DesktopGUIToolchain：暴露 ready/deferred/available 状态；如果没有这行，延迟加载语义不可见。
        "risk_level": tool.risk_level,  # 新增代码+DesktopGUIToolchain：暴露风险级别；如果没有这行，GUI 无法提示危险工具。
        "read_only": tool.is_read_only,  # 新增代码+DesktopGUIToolchain：暴露只读属性；如果没有这行，用户无法区分读取和写入工具。
        "destructive": tool.is_destructive,  # 新增代码+DesktopGUIToolchain：暴露破坏性属性；如果没有这行，危险写入工具不够显眼。
        "permission_mode": tool.permission_mode,  # 新增代码+DesktopGUIToolchain：暴露权限模式；如果没有这行，GUI 无法解释工具是否需要确认。
        "reuse_module": "learning_agent.tools.catalog",  # 新增代码+DesktopGUIToolchain：标记复用模块；如果没有这行，用户无法确认 GUI 没有重写工具链。
    }  # 新增代码+DesktopGUIToolchain：单工具 payload 结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIToolchain：函数段结束，_tool_payload 到此结束；如果没有边界说明，初学者不易看出字段白名单。


def _group_sort_key(group_id: str) -> tuple[int, str]:  # 新增代码+DesktopGUIToolchain：函数段开始，给工具组排序；如果没有这段，GUI 分组顺序不稳定。
    if group_id in TOOLCHAIN_GROUP_ORDER:  # 新增代码+DesktopGUIToolchain：判断是否有预设排序；如果没有这行，index 查询可能抛异常。
        return (TOOLCHAIN_GROUP_ORDER.index(group_id), group_id)  # 新增代码+DesktopGUIToolchain：返回预设顺序和名称；如果没有这行，核心分组无法靠前。
    return (len(TOOLCHAIN_GROUP_ORDER), group_id)  # 新增代码+DesktopGUIToolchain：未知分组排在最后并按名称稳定排序；如果没有这行，新能力包顺序会漂移。
# 新增代码+DesktopGUIToolchain：函数段结束，_group_sort_key 到此结束；如果没有边界说明，初学者不易看出排序规则。


def build_gui_toolchain_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIToolchain：函数段开始，构建 GUI 工具链清单；如果没有这段，前端无法读取统一工具地图。
    workspace_path = Path(workspace).resolve()  # 新增代码+DesktopGUIToolchain：规范化 workspace 路径；如果没有这行，payload 无法说明清单对应哪个项目。
    tools = build_builtin_tool_catalog()  # 新增代码+DesktopGUIToolchain：从已有内置工具目录读取工具；如果没有这行，GUI 会退回硬编码列表。
    grouped_tools: dict[str, list[dict[str, Any]]] = {}  # 新增代码+DesktopGUIToolchain：准备按能力包聚合工具；如果没有这行，后续没有容器保存分组。
    for tool in tools:  # 新增代码+DesktopGUIToolchain：遍历已有工具目录；如果没有这行，payload 会没有任何工具。
        group_id = _tool_group_id(tool)  # 新增代码+DesktopGUIToolchain：计算当前工具分组；如果没有这行，工具无法进入正确能力包。
        grouped_tools.setdefault(group_id, []).append(_tool_payload(tool))  # 新增代码+DesktopGUIToolchain：追加工具 payload；如果没有这行，分组会一直为空。
    groups = [  # 新增代码+DesktopGUIToolchain：构造前端可直接渲染的分组列表；如果没有这行，前端要自己处理字典排序。
        {  # 新增代码+DesktopGUIToolchain：单个分组 payload 开始；如果没有这行，列表项不是 JSON 对象。
            "id": group_id,  # 新增代码+DesktopGUIToolchain：暴露分组 id；如果没有这行，前端无法稳定 key。
            "label": TOOLCHAIN_GROUP_LABELS.get(group_id, group_id.replace("_", " ").title()),  # 新增代码+DesktopGUIToolchain：暴露可读标签；如果没有这行，用户只能看到机器名。
            "status": "available" if grouped_tools[group_id] else "empty",  # 新增代码+DesktopGUIToolchain：暴露分组状态；如果没有这行，空分组和可用分组不可区分。
            "tool_count": len(grouped_tools[group_id]),  # 新增代码+DesktopGUIToolchain：暴露分组工具数量；如果没有这行，面板无法显示规模。
            "reuse_module": "learning_agent.tools.catalog",  # 新增代码+DesktopGUIToolchain：标记分组来自工具目录；如果没有这行，用户看不出复用来源。
            "tools": sorted(grouped_tools[group_id], key=lambda item: str(item["name"])),  # 新增代码+DesktopGUIToolchain：按工具名稳定排序；如果没有这行，刷新后列表可能跳动。
        }  # 新增代码+DesktopGUIToolchain：单个分组 payload 结束；如果没有这行，Python 字典语法不完整。
        for group_id in sorted(grouped_tools, key=_group_sort_key)  # 新增代码+DesktopGUIToolchain：按预设顺序遍历分组；如果没有这行，列表推导没有数据来源。
    ]  # 新增代码+DesktopGUIToolchain：分组列表结束；如果没有这行，Python 列表语法不完整。
    return {  # 新增代码+DesktopGUIToolchain：返回完整 payload；如果没有这行，函数没有输出给 HTTP route。
        "ok": True,  # 新增代码+DesktopGUIToolchain：标记响应成功；如果没有这行，前端无法区分错误响应。
        "schema_version": GUI_V2_SCHEMA_VERSION,  # 新增代码+DesktopGUIToolchain：暴露 V2 schema；如果没有这行，前端无法做版本兼容。
        "workspace": str(workspace_path),  # 新增代码+DesktopGUIToolchain：暴露当前工作区；如果没有这行，用户不知道清单属于哪个项目。
        "generated_at": datetime.now(UTC).isoformat(),  # 新增代码+DesktopGUIToolchain：暴露生成时间；如果没有这行，用户不知道数据是否新鲜。
        "tool_count": len(tools),  # 新增代码+DesktopGUIToolchain：暴露总工具数量；如果没有这行，面板无法显示总体规模。
        "group_count": len(groups),  # 新增代码+DesktopGUIToolchain：暴露分组数量；如果没有这行，诊断无法快速确认分组规模。
        "groups": groups,  # 新增代码+DesktopGUIToolchain：暴露工具分组；如果没有这行，前端没有核心渲染数据。
        "status_degraded": False,  # 新增代码+DesktopGUIToolchain：标记清单未降级；如果没有这行，前端无法统一显示健康状态。
        "safe_error": "",  # 新增代码+DesktopGUIToolchain：保留安全错误字段；如果没有这行，错误状态 contract 不完整。
    }  # 新增代码+DesktopGUIToolchain：完整 payload 结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIToolchain：函数段结束，build_gui_toolchain_payload 到此结束；如果没有边界说明，初学者不易看出它只负责清单构建。
