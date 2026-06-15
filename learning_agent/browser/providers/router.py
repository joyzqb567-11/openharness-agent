"""浏览器 provider 路由器。"""  # 修改代码+Phase19BrowserRouting: 说明本文件负责选择底层浏览器轨道；如果没有这行代码，维护者不容易判断 provider 决策入口在哪里。
from __future__ import annotations  # 修改代码+Phase19BrowserRouting: 延迟解析类型注解，避免类之间引用顺序导致导入问题；如果没有这行代码，未来增加类型时更容易产生运行时错误。

from ..intent import REAL_CHROME_INTENT_KEYWORDS  # 修改代码+Phase19BrowserRouting: 复用真实浏览器意图关键词；如果没有这行代码，router 和 intent.py 的判断规则会分裂。
from ..profile_intent import detect_profile_intent  # 新增代码+DailyChromeProfile: 复用日常 Chrome profile 意图识别；如果没有这行代码，路由层无法把“已登录/我的 Chrome”转换成可审计 metadata。
from .protocol import BrowserProviderDecision, BrowserProviderHealth, BrowserProviderKind  # 修改代码+Phase19BrowserRouting: 导入路由输入输出模型；如果没有这行代码，路由器无法返回稳定决策对象。


class BrowserProviderRouter:  # 修改代码+Phase19BrowserRouting: 定义统一 provider 选择器；如果没有这个类，模型会直接面对多条浏览器轨道而更容易选错。
    current_chrome_markers = tuple(sorted((set(REAL_CHROME_INTENT_KEYWORDS) | {"当前 chrome", "当前Chrome", "我的浏览器", "已登录", "oauth", "OAuth", "现有标签页", "当前标签页"}) - {"可见浏览器", "真实可见浏览器", "visible browser"}))  # 修改代码+Phase19BrowserRouting: 定义当前 Chrome/登录态关键词并排除普通可见浏览器表达；如果没有这行代码，登录态任务可能误走隔离 Chromium。
    cdp_markers = ("cdp", "CDP", "remote debugging", "调试端口", "browser_connect_real_chrome", "隔离 debug profile", "危险调试")  # 修改代码+Phase19BrowserRouting: 定义显式 CDP 调试关键词；如果没有这行代码，明确 CDP 请求可能被插件路线吞掉。
    local_markers = ("localhost", "127.0.0.1", "file://", "本地前端", "开发服务器")  # 修改代码+Phase19BrowserRouting: 定义本地开发关键词；如果没有这行代码，本地页面调试可能污染用户真实 Chrome。

    def decide_provider(self, user_input: str, tool_name: str, arguments: dict[str, object] | None = None, provider_health: dict[BrowserProviderKind, BrowserProviderHealth] | None = None, allow_cdp_fallback: bool = False) -> BrowserProviderDecision:  # 修改代码+Phase19BrowserRouting: 根据意图、工具名和健康状态选择 provider；如果没有这段函数，工具层无法统一防误选。
        text = f"{user_input} {tool_name} {arguments or {}}"  # 修改代码+Phase19BrowserRouting: 合并用户输入、工具名和参数供关键词判断；如果没有这行代码，URL 和显式工具名无法参与路由。
        health = dict(provider_health or {})  # 修改代码+Phase19BrowserRouting: 复制健康状态避免污染调用方对象；如果没有这行代码，路由过程可能意外改写外部状态。
        profile_intent = detect_profile_intent(user_input=user_input, tool_name=tool_name, arguments=arguments or {})  # 新增代码+DailyChromeProfile: 结构化识别日常 profile 需求；如果没有这行代码，后续连接层拿不到 requires_daily_profile 硬门禁信号。
        profile_metadata = {"daily_profile_required": profile_intent.requires_daily_profile, "allows_debug_profile": profile_intent.allows_debug_profile, "profile_intent": profile_intent.profile_intent, "profile_intent_reason_codes": list(profile_intent.reason_codes)}  # 新增代码+DailyChromeProfile: 准备写入路由事件的脱敏 metadata；如果没有这行代码，日志和下游工具无法区分日常登录态与隔离调试。
        if self._has_marker(text, self.cdp_markers):  # 修改代码+Phase19BrowserRouting: 显式 CDP 请求优先；如果没有这行代码，调试端口任务可能走错插件。
            return self._available_or_unavailable(BrowserProviderKind.REAL_CHROME_CDP, health, tool_name, "用户明确要求 CDP 或真实 Chrome 调试端口。", "real_chrome_cdp_explicit_debug")  # 修改代码+Phase19BrowserRouting: 返回 CDP 决策或明确不可用；如果没有这行代码，显式调试请求没有稳定审计结果。
        if self._has_marker(text, self.current_chrome_markers):  # 修改代码+Phase19BrowserRouting: 当前 Chrome/登录态任务进入真实浏览器优先分支；如果没有这行代码，登录态任务可能默认走隔离 Chromium。
            return self._with_profile_metadata(self._decide_current_chrome_route(tool_name, health, allow_cdp_fallback), profile_metadata)  # 修改代码+DailyChromeProfile: 当前 Chrome 决策必须携带 profile 意图；如果没有这行代码，连接层可能继续不知道本次是否禁止 debug fallback。
        if self._has_marker(text, self.local_markers):  # 修改代码+Phase19BrowserRouting: 本地开发任务优先使用隔离可见 Chromium；如果没有这行代码，本地调试可能误碰真实 Chrome。
            return self._available_or_unavailable(BrowserProviderKind.VISIBLE_CHROMIUM, health, tool_name, "本地开发或 localhost 任务默认使用隔离可见 Chromium。", "visible_chromium_local_development")  # 修改代码+Phase19BrowserRouting: 返回本地开发 provider 决策；如果没有这行代码，本地任务路线不稳定。
        return self._available_or_unavailable(BrowserProviderKind.VISIBLE_CHROMIUM, health, tool_name, "公开网页或普通浏览器任务默认使用隔离可见 Chromium。", "visible_chromium_public_web")  # 修改代码+Phase19BrowserRouting: 返回公开网页默认 provider 决策；如果没有这行代码，普通浏览任务没有安全默认路线。

    def _decide_current_chrome_route(self, tool_name: str, health: dict[BrowserProviderKind, BrowserProviderHealth], allow_cdp_fallback: bool) -> BrowserProviderDecision:  # 新增代码+Phase19BrowserRouting: 处理当前 Chrome/登录态的多 provider 决策；如果没有这段函数，插件、CDP、可见 Chromium 的优先级会散落难查。
        extension_health = health.get(BrowserProviderKind.CHROME_EXTENSION, BrowserProviderHealth.unavailable(BrowserProviderKind.CHROME_EXTENSION, "extension_health_missing"))  # 修改代码+Phase19BrowserRouting: 读取插件健康状态并给缺省不可用；如果没有这行代码，缺状态时可能误判插件可用。
        cdp_health = health.get(BrowserProviderKind.REAL_CHROME_CDP, BrowserProviderHealth.unavailable(BrowserProviderKind.REAL_CHROME_CDP, "cdp_missing"))  # 新增代码+Phase19BrowserRouting: 读取 CDP 健康状态；如果没有这行代码，插件不支持工具时不知道 CDP 是否可接管。
        visible_health = health.get(BrowserProviderKind.VISIBLE_CHROMIUM, BrowserProviderHealth.unavailable(BrowserProviderKind.VISIBLE_CHROMIUM, "visible_chromium_missing"))  # 新增代码+Phase19BrowserRouting: 读取可见 Chromium 健康状态；如果没有这行代码，真实 Chrome 路线阻断时没有最后 fallback 依据。
        if extension_health.available and self._health_supports_tool(extension_health, tool_name):  # 修改代码+Phase19BrowserRouting: 只有插件可用且支持目标工具时才选择插件；如果没有这行代码，不支持的工具会被发给插件导致失败。
            return BrowserProviderDecision(provider=BrowserProviderKind.CHROME_EXTENSION, reason="用户要求当前 Chrome、登录态或现有标签页，插件 provider 已配对且支持该工具。", tool_name=tool_name, reason_code="chrome_extension_current_browser", metadata={"supported_tool": True, "extension_paired": self._health_paired(extension_health), "supported_tools": self._supported_tools(extension_health)})  # 修改代码+Phase19BrowserRouting: 返回插件决策并记录支持证据；如果没有这行代码，事件日志看不出为什么选插件。
        if extension_health.available and not self._health_supports_tool(extension_health, tool_name):  # 新增代码+Phase19BrowserRouting: 插件可用但不支持工具时进入智能 fallback；如果没有这行代码，router 会把未知工具错误发送给插件。
            if cdp_health.available:  # 新增代码+Phase19BrowserRouting: CDP 可用时优先用真实 Chrome CDP 接管；如果没有这行代码，真实 Chrome 能力可用时仍可能退到隔离浏览器。
                return BrowserProviderDecision(provider=BrowserProviderKind.REAL_CHROME_CDP, reason="Chrome 插件已配对但不支持该工具，真实 Chrome CDP 可用，因此改走 CDP。", tool_name=tool_name, reason_code="chrome_extension_tool_unsupported_real_chrome_cdp", metadata={"fallback_from": BrowserProviderKind.CHROME_EXTENSION.value, "unsupported_tool": tool_name, "supported_tools": self._supported_tools(extension_health)})  # 新增代码+Phase19BrowserRouting: 返回 CDP fallback 决策并记录不支持的工具；如果没有这行代码，外部 agent 不知道为什么切换轨道。
            if visible_health.available:  # 新增代码+Phase19BrowserRouting: CDP 不可用但隔离可见 Chromium 可用时退到安全可见浏览器；如果没有这行代码，真实 Chrome 受阻会直接失败。
                return BrowserProviderDecision(provider=BrowserProviderKind.VISIBLE_CHROMIUM, reason="Chrome 插件不支持该工具且 CDP 不可用，因此退到隔离可见 Chromium。", tool_name=tool_name, reason_code="chrome_extension_tool_unsupported_visible_chromium", metadata={"fallback_from": BrowserProviderKind.CHROME_EXTENSION.value, "unsupported_tool": tool_name, "cdp_unavailable_reason": cdp_health.reason})  # 新增代码+Phase19BrowserRouting: 返回可见 Chromium fallback 决策并记录 CDP 阻断原因；如果没有这行代码，fallback 缺少可审计证据。
            return BrowserProviderDecision(provider=BrowserProviderKind.UNAVAILABLE, reason=f"Chrome 插件不支持工具 {tool_name}，且 CDP/可见 Chromium 都不可用。", tool_name=tool_name, reason_code="chrome_extension_tool_unsupported_no_fallback", requires_user_confirmation=True, metadata={"unavailable_provider": BrowserProviderKind.CHROME_EXTENSION.value, "unsupported_tool": tool_name, "cdp_unavailable_reason": cdp_health.reason, "visible_unavailable_reason": visible_health.reason})  # 新增代码+Phase19BrowserRouting: 所有路线都不可用时返回明确失败；如果没有这行代码，调用方可能收到模糊异常。
        fallback = BrowserProviderKind.REAL_CHROME_CDP if cdp_health.available else BrowserProviderKind.UNAVAILABLE  # 修改代码+Phase19BrowserRouting: 插件不可用时计算 CDP 是否可作为候选 fallback；如果没有这行代码，用户无法知道是否可以授权降级。
        if allow_cdp_fallback and fallback == BrowserProviderKind.REAL_CHROME_CDP:  # 修改代码+Phase19BrowserRouting: 只有显式允许时才把不可用插件降级到 CDP；如果没有这行代码，登录态任务可能静默改走高风险调试路线。
            return BrowserProviderDecision(provider=BrowserProviderKind.REAL_CHROME_CDP, reason="插件 provider 不可用，且调用方明确允许降级到 CDP。", tool_name=tool_name, reason_code="extension_unavailable_cdp_fallback_allowed", metadata={"fallback_from": BrowserProviderKind.CHROME_EXTENSION.value, "unavailable_reason": extension_health.reason, "extension_paired": self._health_paired(extension_health)})  # 修改代码+Phase19BrowserRouting: 返回授权降级决策并记录来源；如果没有这行代码，审计时不知道 CDP 是从哪个 provider 降级而来。
        return BrowserProviderDecision(provider=BrowserProviderKind.UNAVAILABLE, reason=f"用户要求当前 Chrome 或登录态，但插件 provider 不可用：{extension_health.reason}", tool_name=tool_name, reason_code="chrome_extension_unavailable_confirmation_required", fallback_provider=fallback, requires_user_confirmation=True, metadata={"unavailable_provider": BrowserProviderKind.CHROME_EXTENSION.value, "unavailable_reason": extension_health.reason, "extension_paired": self._health_paired(extension_health)})  # 修改代码+Phase19BrowserRouting: 返回需要确认的不可用决策；如果没有这行代码，插件不可用时可能发生静默高风险 fallback。

    def _available_or_unavailable(self, kind: BrowserProviderKind, health: dict[BrowserProviderKind, BrowserProviderHealth], tool_name: str, reason: str, reason_code: str) -> BrowserProviderDecision:  # 修改代码+Phase19BrowserRouting: 复用可用性判断并保留稳定 reason code；如果没有这段函数，多个分支会重复构造不可用结果。
        provider_health = health.get(kind, BrowserProviderHealth.unavailable(kind, "provider_health_missing"))  # 修改代码+Phase19BrowserRouting: 读取 provider 健康状态；如果没有这行代码，缺状态时可能误判可用。
        if provider_health.available:  # 修改代码+Phase19BrowserRouting: provider 可用时返回目标 provider；如果没有这行代码，正常路线无法执行。
            return BrowserProviderDecision(provider=kind, reason=reason, tool_name=tool_name, reason_code=reason_code)  # 修改代码+Phase19BrowserRouting: 返回成功决策和原因码；如果没有这行代码，调用方拿不到可审计 provider。
        return BrowserProviderDecision(provider=BrowserProviderKind.UNAVAILABLE, reason=f"{reason} 但 provider 不可用：{provider_health.reason}", tool_name=tool_name, reason_code=f"{reason_code}_unavailable", requires_user_confirmation=True, metadata={"unavailable_provider": kind.value, "unavailable_reason": provider_health.reason})  # 修改代码+Phase19BrowserRouting: 返回不可用决策；如果没有这行代码，失败原因不可审计。

    def _health_supports_tool(self, provider_health: BrowserProviderHealth, tool_name: str) -> bool:  # 新增代码+Phase19BrowserRouting: 根据健康 metadata 判断 provider 是否支持目标工具；如果没有这段函数，router 无法避免把工具发给不支持的 provider。
        supported_tools = self._supported_tools(provider_health)  # 新增代码+Phase19BrowserRouting: 读取健康状态里的支持工具清单；如果没有这行代码，后续判断没有数据来源。
        return not supported_tools or tool_name in supported_tools  # 新增代码+Phase19BrowserRouting: 老 provider 没有清单时保持兼容，有清单时严格匹配；如果没有这行代码，历史 provider 会被 metadata 升级误伤。

    def _supported_tools(self, provider_health: BrowserProviderHealth) -> list[str]:  # 新增代码+Phase19BrowserRouting: 标准化健康 metadata 中的 supported_tools；如果没有这段函数，router 多处分支会重复处理异常类型。
        metadata = provider_health.metadata or {}  # 新增代码+Phase19BrowserRouting: 读取 metadata 并兜底为空字典；如果没有这行代码，metadata 为 None 时会抛异常。
        value = metadata.get("supported_tools", [])  # 新增代码+Phase19BrowserRouting: 读取支持工具原始值；如果没有这行代码，无法判断工具能力。
        return [str(item) for item in value] if isinstance(value, list) else []  # 新增代码+Phase19BrowserRouting: 只接受列表并转成字符串列表；如果没有这行代码，坏 metadata 可能污染路由判断。

    def _health_paired(self, provider_health: BrowserProviderHealth) -> bool:  # 新增代码+Phase19BrowserRouting: 从健康 metadata 中读取插件配对状态；如果没有这段函数，事件 metadata 无法稳定暴露 paired 字段。
        metadata = provider_health.metadata or {}  # 新增代码+Phase19BrowserRouting: 读取 metadata 并兜底为空字典；如果没有这行代码，metadata 为 None 时会抛异常。
        return bool(metadata.get("paired", False))  # 新增代码+Phase19BrowserRouting: 返回布尔化配对状态；如果没有这行代码，事件日志可能出现不稳定类型。

    def _with_profile_metadata(self, decision: BrowserProviderDecision, profile_metadata: dict[str, object]) -> BrowserProviderDecision:  # 新增代码+DailyChromeProfile: 给当前 Chrome 决策补充 profile 意图字段；如果没有这段函数，多条 return 都要手写合并 metadata 且容易漏字段。
        merged_metadata = dict(decision.metadata or {})  # 新增代码+DailyChromeProfile: 复制原有 metadata 避免污染冻结决策对象；如果没有这行代码，原有 supported_tools 等审计字段可能被覆盖或外部改写。
        merged_metadata.update(profile_metadata)  # 新增代码+DailyChromeProfile: 合并日常 profile 意图字段；如果没有这行代码，daily_profile_required 不会出现在路由结果里。
        return BrowserProviderDecision(provider=decision.provider, reason=decision.reason, tool_name=decision.tool_name, reason_code=decision.reason_code, fallback_provider=decision.fallback_provider, requires_user_confirmation=decision.requires_user_confirmation, metadata=merged_metadata)  # 新增代码+DailyChromeProfile: 返回带合并 metadata 的新决策；如果没有这行代码，dataclass 冻结对象无法安全补字段。

    def _has_marker(self, text: str, markers: tuple[str, ...]) -> bool:  # 修改代码+Phase19BrowserRouting: 统一关键词匹配；如果没有这段函数，大小写和中英文规则会散落。
        lowered = text.lower()  # 修改代码+Phase19BrowserRouting: 转小写支持英文大小写匹配；如果没有这行代码，CDP/oauth 大小写变化可能漏判。
        return any(marker.lower() in lowered for marker in markers)  # 修改代码+Phase19BrowserRouting: 判断任一关键词命中；如果没有这行代码，意图识别永远为 false。
