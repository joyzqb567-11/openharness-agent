from __future__ import annotations  # 新增代码+ToolPolicyV2: 让类型注解延迟解析，避免运行时因为前后声明顺序出错；若没有这行代码，复杂类型在旧环境里更容易触发解析问题
from dataclasses import dataclass, field  # 新增代码+ToolPolicyV2: 导入 dataclass 和 field 来定义轻量策略数据对象；若没有这行代码，策略上下文和结果就要手写大量样板代码
from typing import Any  # 新增代码+ToolPolicyV2: 导入 Any 来描述外部传入的工具对象；若没有这行代码，模块必须依赖具体 AgentTool 类型而产生循环导入风险


@dataclass  # 新增代码+ToolPolicyV2: 自动生成策略规则对象的初始化方法；若没有这行代码，调用方创建 allow/deny 规则会更啰嗦且容易写错字段
class ToolPolicyRule:  # 新增代码+ToolPolicyV2: 定义单条工具匹配规则；若没有这行代码，allow_rules 和 deny_rules 没有统一的数据结构
    tool_name: str = ""  # 新增代码+ToolPolicyV2: 保存要匹配的工具名，空字符串表示此字段不参与匹配；若没有这行代码，策略无法按具体工具精确拦截
    server_name: str = ""  # 新增代码+ToolPolicyV2: 保存要匹配的 MCP server 名，空字符串表示此字段不参与匹配；若没有这行代码，策略无法按外部服务来源拦截
    source: str = ""  # 新增代码+ToolPolicyV2: 保存要匹配的工具来源，空字符串表示此字段不参与匹配；若没有这行代码，策略无法区分 builtin 和 mcp 等来源


@dataclass  # 新增代码+ToolPolicyV2: 自动生成策略上下文对象的初始化方法；若没有这行代码，调用方需要手写容易共享可变默认值的字典
class ToolPolicyContext:  # 新增代码+ToolPolicyV2: 定义一次策略判断需要读取的上下文；若没有这行代码，deny、skill 和 workflow 状态会散落在多个参数里
    allow_rules: list[ToolPolicyRule] = field(default_factory=list)  # 新增代码+ToolPolicyV2: 保存允许规则列表并为每个上下文创建独立列表；若没有这行代码，后续 allow 扩展没有落点且可能误共享列表
    deny_rules: list[ToolPolicyRule] = field(default_factory=list)  # 新增代码+ToolPolicyV2: 保存拒绝规则列表并为每个上下文创建独立列表；若没有这行代码，blocked 分支无法读取用户配置
    loaded_skills: set[str] = field(default_factory=set)  # 新增代码+ToolPolicyV2: 保存已经加载的 skill 名称集合；若没有这行代码，skill_gate 无法判断是否满足
    completed_workflows: set[str] = field(default_factory=set)  # 新增代码+ToolPolicyV2: 保存已经完成的 workflow 名称集合；若没有这行代码，workflow_gate 无法判断是否满足
    non_interactive: bool = False  # 新增代码+ToolPolicyV2: 记录当前是否非交互模式，为后续权限策略预留输入；若没有这行代码，后续自动化场景无法从上下文表达交互边界


@dataclass  # 新增代码+ToolPolicyV2: 自动生成策略决策对象的初始化方法；若没有这行代码，调用方只能用不够清晰的字典传递结果
class ToolPolicyDecision:  # 新增代码+ToolPolicyV2: 定义策略判断后的统一结果；若没有这行代码，visible/selectable/executable 状态会在各处重复拼装
    state: str  # 新增代码+ToolPolicyV2: 保存策略状态，例如 blocked、needs_skill、deferred 或 loaded；若没有这行代码，调用方不知道工具当前卡在哪一步
    visible: bool  # 新增代码+ToolPolicyV2: 保存工具是否应该展示给模型；若没有这行代码，被拦截工具可能误进入模型上下文
    selectable: bool  # 新增代码+ToolPolicyV2: 保存工具是否允许通过搜索/select 被选择；若没有这行代码，deferred 和 blocked 的差异无法表达
    executable: bool  # 新增代码+ToolPolicyV2: 保存工具是否允许实际执行；若没有这行代码，展示状态和执行门禁会混在一起
    reason: str = ""  # 新增代码+ToolPolicyV2: 保存人类可读的策略原因；若没有这行代码，后续调试或提示只能看到状态而不知道原因


class ToolPolicy:  # 新增代码+ToolPolicyV2: 定义工具策略核心入口；若没有这行代码，调用方没有稳定位置执行 deny、gate 和 deferred 判断
    @staticmethod  # 新增代码+ToolPolicyV2: 声明规则匹配不需要实例状态；若没有这行代码，调用私有 helper 时会误要求创建 ToolPolicy 对象
    def _rule_matches(tool: Any, rule: ToolPolicyRule) -> bool:  # 新增代码+ToolPolicyV2: 判断单条规则是否匹配传入工具；若没有这行代码，deny 分支会重复写匹配逻辑
        checks: list[bool] = []  # 新增代码+ToolPolicyV2: 保存每个非空规则字段的比较结果；若没有这行代码，无法区分空规则和真实匹配
        if rule.tool_name:  # 新增代码+ToolPolicyV2: 只有规则写了 tool_name 才比较工具名；若没有这行代码，空 tool_name 会错误匹配所有工具
            checks.append(getattr(tool, "name", "") == rule.tool_name)  # 新增代码+ToolPolicyV2: 比较工具对象的 name 与规则工具名；若没有这行代码，deny rule 无法按具体工具生效
        if rule.server_name:  # 新增代码+ToolPolicyV2: 只有规则写了 server_name 才比较服务名；若没有这行代码，空 server_name 会错误匹配所有工具
            checks.append(getattr(tool, "server_name", "") == rule.server_name)  # 新增代码+ToolPolicyV2: 比较工具对象的 server_name 与规则服务名；若没有这行代码，策略无法按 MCP server 拦截
        if rule.source:  # 新增代码+ToolPolicyV2: 只有规则写了 source 才比较来源；若没有这行代码，空 source 会错误匹配所有工具
            checks.append(getattr(tool, "source", "") == rule.source)  # 新增代码+ToolPolicyV2: 比较工具对象的 source 与规则来源；若没有这行代码，策略无法按 builtin/mcp 来源拦截
        return bool(checks) and all(checks)  # 新增代码+ToolPolicyV2: 要求至少一个字段参与且全部命中；若没有这行代码，空规则可能变成全局拒绝或部分条件被忽略

    @staticmethod  # 新增代码+ToolPolicyV2: 声明策略决策不依赖实例状态；若没有这行代码，调用方需要无意义地实例化 ToolPolicy
    def decide(tool: Any, context: ToolPolicyContext, *, loaded: bool = False) -> ToolPolicyDecision:  # 新增代码+ToolPolicyV2: 根据工具和上下文返回统一决策；若没有这行代码，工具池和执行层没有可复用的策略入口
        for rule in context.deny_rules:  # 新增代码+ToolPolicyV2: 逐条检查拒绝规则并让 deny 优先于其他状态；若没有这行代码，被拒绝工具可能继续通过 skill 或 deferred 分支
            if ToolPolicy._rule_matches(tool, rule):  # 新增代码+ToolPolicyV2: 判断当前 deny rule 是否命中工具；若没有这行代码，拒绝规则只是被保存但不会生效
                return ToolPolicyDecision(state="blocked", visible=False, selectable=False, executable=False, reason="deny rule matched")  # 新增代码+ToolPolicyV2: 返回完全不可见、不可选、不可执行的 blocked 决策；若没有这行代码，deny 工具可能暴露给模型或执行层
        allow_rules_active = bool(context.allow_rules)  # 新增代码+ToolPolicyV2: 判断当前上下文是否启用了允许规则；若没有这行代码，allow_rules 只会被保存但不会真正限制工具范围
        allow_rule_matched = any(ToolPolicy._rule_matches(tool, rule) for rule in context.allow_rules) if allow_rules_active else True  # 新增代码+ToolPolicyV2: 只有存在 allow_rules 时才要求命中至少一条允许规则；若没有这行代码，白名单语义无法区分“未配置”和“已配置但未命中”
        if not allow_rule_matched:  # 新增代码+ToolPolicyV2: 拦截没有命中允许规则的工具；若没有这行代码，allow_rules 无法形成真正的工具白名单
            return ToolPolicyDecision(state="blocked", visible=False, selectable=False, executable=False, reason="no allow rule matched")  # 新增代码+ToolPolicyV2: 返回不可见、不可选、不可执行的白名单阻断结果；若没有这行代码，模型仍可能看到或执行未被允许的工具
        skill_gate = getattr(tool, "skill_gate", "")  # 新增代码+ToolPolicyV2: 读取工具要求的 skill gate；若没有这行代码，策略无法知道工具是否需要先加载 skill
        if skill_gate and skill_gate not in context.loaded_skills:  # 新增代码+ToolPolicyV2: 检查非空 skill gate 是否未满足；若没有这行代码，依赖 skill 的工具会过早暴露
            return ToolPolicyDecision(state="needs_skill", visible=False, selectable=False, executable=False, reason=f"missing skill: {skill_gate}")  # 新增代码+ToolPolicyV2: 返回缺 skill 的不可用决策；若没有这行代码，调用方无法提示需要先加载哪个 skill
        workflow_gate = getattr(tool, "workflow_gate", "")  # 新增代码+ToolPolicyV2: 读取工具要求的 workflow gate；若没有这行代码，策略无法知道工具是否需要先完成流程
        if workflow_gate and workflow_gate not in context.completed_workflows:  # 新增代码+ToolPolicyV2: 检查非空 workflow gate 是否未满足；若没有这行代码，需要前置流程的工具会过早暴露
            return ToolPolicyDecision(state="needs_workflow", visible=False, selectable=False, executable=False, reason=f"missing workflow: {workflow_gate}")  # 新增代码+ToolPolicyV2: 返回缺 workflow 的不可用决策；若没有这行代码，调用方无法提示需要先完成哪个流程
        should_defer = bool(getattr(tool, "should_defer", False))  # 新增代码+ToolPolicyV2: 读取并规范化工具是否延迟加载；若没有这行代码，deferred 工具无法与普通工具区分
        always_load = bool(getattr(tool, "always_load", False))  # 新增代码+ToolPolicyV2: 读取并规范化工具是否强制加载；若没有这行代码，tool_search 等入口可能被 deferred 规则误隐藏
        if should_defer and not loaded and not always_load:  # 新增代码+ToolPolicyV2: 判断未加载的 deferred 工具是否应隐藏但允许选择；若没有这行代码，外部工具会默认进入模型上下文
            return ToolPolicyDecision(state="deferred", visible=False, selectable=True, executable=False, reason="deferred until selected")  # 新增代码+ToolPolicyV2: 返回 deferred 决策并允许 select；若没有这行代码，模型无法通过搜索选择延迟工具
        return ToolPolicyDecision(state="loaded", visible=True, selectable=True, executable=True)  # 新增代码+ToolPolicyV2: 返回已加载且完全可用的决策；若没有这行代码，满足条件的工具也拿不到可见可执行状态
