"""工具元数据类型定义。"""  # 新增代码+ToolsSplit: 把工具目录的数据结构从主入口拆出；若没有这个文件，排查工具元数据仍要翻 learning_agent.py。

from __future__ import annotations  # 新增代码+ToolsSplit: 延迟解析类型注解；若没有这行代码，后续类型引用更容易受定义顺序影响。

import copy  # 新增代码+ToolsSplit: AgentTool 需要深拷贝参数 schema；若没有这行代码，调用方可能改坏工具目录内部结构。
from dataclasses import dataclass, field  # 新增代码+ToolsSplit: 自动生成工具元数据对象初始化方法并支持列表默认值；若没有这行代码，需要手写重复构造逻辑。
from typing import Any  # 新增代码+ToolsSplit: 工具 schema 是通用 JSON 字典；若没有这行代码，类型边界会不清楚。


@dataclass  # 新增代码+ToolsSplit: 自动生成 AgentTool 元数据对象初始化方法；若没有这行代码，每个工具都要手写重复构造逻辑。
class AgentTool:  # 新增代码+ToolsSplit: 定义 v2 工具目录里的单个工具记录；若没有这行代码，系统只能传裸 schema 而无法携带来源、风险和加载策略。
    name: str  # 新增代码+ToolsSplit: 保存模型调用时使用的工具名；若没有这行代码，执行分发和目录索引都找不到稳定键。
    description: str  # 新增代码+ToolsSplit: 保存给模型和用户看的工具说明；若没有这行代码，工具目录无法解释工具用途。
    input_schema: dict[str, Any]  # 新增代码+ToolsSplit: 保存工具参数 JSON Schema；若没有这行代码，模型无法知道该传哪些参数。
    source: str = "builtin"  # 新增代码+ToolsSplit: 标记工具来自内置、MCP 或其他来源；若没有这行代码，权限和展示层无法区分工具来源。
    risk_level: str = "low"  # 新增代码+ToolsSplit: 默认把未特别标注的工具视为低风险；若没有这行代码，catalog 会出现 unknown 风险并偏离已确认设计。
    is_read_only: bool = False  # 新增代码+ToolsSplit: 标记工具是否只读；若没有这行代码，权限层无法快速识别低风险读取能力。
    is_destructive: bool = False  # 新增代码+ToolsSplit: 标记工具是否可能破坏数据；若没有这行代码，确认流程无法提前识别高风险动作。
    should_defer: bool = False  # 新增代码+ToolsSplit: 标记工具是否应该延迟加载；若没有这行代码，工具池无法控制首轮上下文体积。
    always_load: bool = False  # 新增代码+ToolsSplit: 标记工具是否必须首轮可见；若没有这行代码，核心入口可能被错误隐藏。
    permission_category: str = ""  # 新增代码+ToolsSplit: 保存权限展示类别；若没有这行代码，授权展示无法按类别组织。
    skill_gate: str = ""  # 新增代码+ToolsSplit: 保存 skill 门控名；若没有这行代码，skill 加载判断没有落点。
    workflow_gate: str = ""  # 新增代码+ToolsSplit: 保存 workflow 门控名；若没有这行代码，流程相关加载规则没有落点。
    original_name: str = ""  # 新增代码+ToolsSplit: 保存外部原始工具名；若没有这行代码，MCP 工具追踪字段会丢失。
    server_name: str = ""  # 新增代码+ToolsSplit: 保存 MCP server 名；若没有这行代码，展示和审计层无法说明工具来源 server。
    aliases: list[str] = field(default_factory=list)  # 新增代码+ToolsSplit: 保存工具别名列表；若没有这行代码，策略和搜索无法记录同一工具的其他叫法。
    search_hint: str = ""  # 新增代码+ToolsSplit: 保存搜索提示；若没有这行代码，工具检索时会丢失服务端给出的使用线索。
    input_json_schema: dict[str, Any] = field(default_factory=dict)  # 新增代码+ToolsSplit: 保存 MCP 原始 inputSchema；若没有这行代码，策略层只能看到模型包装后的参数 schema。
    output_schema: dict[str, Any] = field(default_factory=dict)  # 新增代码+ToolsSplit: 保存 MCP 原始 outputSchema；若没有这行代码，结果结构约束会在进入 AgentTool 时丢失。
    is_open_world: bool = False  # 新增代码+ToolsSplit: 标记工具是否会访问开放外部世界；若没有这行代码，网络/外部系统类工具无法被策略单独识别。
    strict: bool = False  # 新增代码+ToolsSplit: 标记工具 schema 是否要求严格模式；若没有这行代码，上游 strict 标记无法随工具元数据流转。
    max_result_size_chars: int = 20000  # 新增代码+ToolsSplit: 保存工具结果建议最大字符数；若没有这行代码，策略层没有统一默认结果大小边界。
    capability_pack: str = ""  # 新增代码+ToolsSplit: 保存工具所属能力包名称；若没有这行代码，按包加载隐藏工具会丢失分组。

    def to_model_schema(self) -> dict[str, Any]:  # 新增代码+ToolsSplit: 把 AgentTool 转回 OpenAI-compatible function schema；若没有这行代码，现有模型适配器无法继续使用工具。
        return {  # 新增代码+ToolsSplit: 返回新的 schema 字典避免调用方直接修改 AgentTool 内部字段；若没有这行代码，模型边界拿不到标准工具结构。
            "type": "function",  # 新增代码+ToolsSplit: 保持 OpenAI-compatible 工具类型；若没有这行代码，模型适配器可能无法识别这是函数工具。
            "function": {  # 新增代码+ToolsSplit: 保持 function 包装层；若没有这行代码，工具名、说明和参数会落在错误层级。
                "name": self.name,  # 新增代码+ToolsSplit: 写回工具名；若没有这行代码，模型调用结果无法路由到对应工具。
                "description": self.description,  # 新增代码+ToolsSplit: 写回工具说明；若没有这行代码，模型选择工具时会缺少语义提示。
                "parameters": copy.deepcopy(self.input_schema),  # 新增代码+ToolsSplit: 深拷贝参数 schema；若没有这行代码，调用方修改返回值会污染 catalog 内部 schema。
            },  # 新增代码+ToolsSplit: 结束 function 字典；若没有这行代码，Python 结构无法闭合。
        }  # 新增代码+ToolsSplit: 结束模型工具 schema；若没有这行代码，方法无法返回完整结构。
