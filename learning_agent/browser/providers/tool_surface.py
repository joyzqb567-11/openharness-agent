"""浏览器 provider 工具表面规则。"""  # 新增代码+BrowserToolSurfaceStage3: 说明本文件负责模型可见工具和 provider 内部工具的边界；若没有这行代码，工具表面规则会散在 MCP、prompt 和 server 中。
from __future__ import annotations  # 新增代码+BrowserToolSurfaceStage3: 延迟解析类型注解；若没有这行代码，后续扩展类型引用更容易受导入顺序影响。

PROVIDER_SPECIFIC_PREFIXES: tuple[str, ...] = (  # 新增代码+BrowserToolSurfaceStage3: 定义禁止直接暴露给模型的 provider 专属前缀；若没有这行代码，未来插件/CDP 专属工具容易进入模型工具池。
    "chrome_extension_",  # 新增代码+BrowserToolSurfaceStage3: 插件 provider 专属命名前缀；若没有这项，chrome_extension_open 这类重复动作可能被暴露。
    "real_chrome_cdp_",  # 新增代码+BrowserToolSurfaceStage3: CDP provider 专属命名前缀；若没有这项，real_chrome_cdp_click 这类重复动作可能被暴露。
    "visible_chromium_",  # 新增代码+BrowserToolSurfaceStage3: 可见 Chromium provider 专属命名前缀；若没有这项，visible_chromium_type 这类重复动作可能被暴露。
    "cdp_real_chrome_",  # 新增代码+BrowserToolSurfaceStage3: 兼容另一种 CDP 命名前缀；若没有这项，换一种写法仍会漏进模型工具池。
)  # 新增代码+BrowserToolSurfaceStage3: 结束 provider 专属前缀集合；若没有这行代码，Python 元组语法不完整。

PROVIDER_SPECIFIC_ACTION_SUFFIXES: tuple[str, ...] = (  # 新增代码+BrowserToolSurfaceStage3: 定义和统一动作重复的 provider 专属后缀；若没有这行代码，过滤会过宽或过窄。
    "open",  # 新增代码+BrowserToolSurfaceStage3: open 应只通过 browser_open 暴露；若没有这项，provider 专属打开工具可能污染模型选择。
    "click",  # 新增代码+BrowserToolSurfaceStage3: click 应只通过 browser_click 暴露；若没有这项，模型可能在多种点击工具中选错。
    "type",  # 新增代码+BrowserToolSurfaceStage3: type 应只通过 browser_type 暴露；若没有这项，输入动作会出现多轨竞争。
    "type_text",  # 新增代码+BrowserToolSurfaceStage3: 兼容 type_text 命名；若没有这项，插件写动作可能换名绕过过滤。
    "press_key",  # 新增代码+BrowserToolSurfaceStage3: press_key 应只通过 browser_press_key 暴露；若没有这项，按键动作会出现多轨竞争。
    "snapshot",  # 新增代码+BrowserToolSurfaceStage3: snapshot 应只通过 browser_snapshot 暴露；若没有这项，读取页面会出现多轨竞争。
    "screenshot",  # 新增代码+BrowserToolSurfaceStage3: screenshot 应只通过 browser_screenshot 暴露；若没有这项，视觉证据工具会分裂。
    "tabs",  # 新增代码+BrowserToolSurfaceStage3: tabs 应只通过统一 tabs/context 工具暴露；若没有这项，标签页状态会分裂。
    "tabs_context",  # 新增代码+BrowserToolSurfaceStage3: tabs_context 应只通过统一合同暴露；若没有这项，Stage 4 可能重复出插件专属入口。
    "console",  # 新增代码+BrowserToolSurfaceStage3: console 应只通过 browser_console 暴露；若没有这项，调试信息会出现多轨竞争。
    "network",  # 新增代码+BrowserToolSurfaceStage3: network 应只通过 browser_network 暴露；若没有这项，网络观察会出现多轨竞争。
    "upload_file",  # 新增代码+BrowserToolSurfaceStage3: upload_file 应只通过 browser_upload_file 暴露；若没有这项，上传动作会出现高风险混乱。
    "close",  # 新增代码+BrowserToolSurfaceStage3: close 应只通过 browser_close 或控制入口暴露；若没有这项，关闭动作会出现多轨竞争。
    "navigate",  # 新增代码+BrowserToolSurfaceStage3: navigate 属于打开/跳转统一动作；若没有这项，插件导航工具可能绕开 browser_open。
    "scroll",  # 新增代码+BrowserToolSurfaceStage3: scroll 未来应通过统一 browser_scroll 暴露；若没有这项，插件滚动动作可能提前分裂工具面。
    "submit",  # 新增代码+BrowserToolSurfaceStage3: submit 未来应通过统一 browser_submit 暴露；若没有这项，高风险提交可能绕过统一权限。
)  # 新增代码+BrowserToolSurfaceStage3: 结束 provider 专属动作后缀集合；若没有这行代码，Python 元组语法不完整。

PROVIDER_CONTROL_TOOL_NAMES: set[str] = {  # 新增代码+BrowserToolSurfaceStage3: 定义允许存在但必须被标成高级控制入口的统一工具；若没有这行代码，连接真实 Chrome 会和普通页面动作混淆。
    "browser_connect_real_chrome",  # 新增代码+BrowserToolSurfaceStage3: 连接真实 Chrome 是 provider 控制入口；若没有这项，模型搜索时会缺少高风险提示。
    "browser_disconnect_real_chrome",  # 新增代码+BrowserToolSurfaceStage3: 断开真实 Chrome 是 provider 控制入口；若没有这项，断开动作会被误当普通关闭页面。
    "browser_profile_status",  # 新增代码+BrowserToolSurfaceStage3: profile 状态是真实 Chrome 前置控制入口；若没有这项，模型不知道它属于 provider workflow。
    "browser_provider_status",  # 新增代码+BrowserToolSurfaceStage3: provider 状态是控制/状态入口；若没有这项，Stage 8 状态工具可能缺少一致标记。
    "browser_extension_status",  # 新增代码+BrowserToolSurfaceStage3: 插件状态是控制/状态入口；若没有这项，Stage 8 插件状态工具可能缺少一致标记。
}  # 新增代码+BrowserToolSurfaceStage3: 结束 provider 控制工具集合；若没有这行代码，Python 集合语法不完整。


def normalized_browser_tool_name(tool_name: str) -> str:  # 新增代码+BrowserToolSurfaceStage3: 把 MCP 前缀工具名还原成原始浏览器工具名；若没有这行代码，mcp__browser_automation__browser_open 会无法复用分类规则。
    cleaned_name = str(tool_name or "").strip()  # 新增代码+BrowserToolSurfaceStage3: 清理空值和前后空格；若没有这行代码，None 或带空格名称会误判。
    if "__" not in cleaned_name:  # 新增代码+BrowserToolSurfaceStage3: 没有 MCP 分隔符时就是原始工具名；若没有这行代码，普通 server 工具名会被不必要拆分。
        return cleaned_name  # 新增代码+BrowserToolSurfaceStage3: 返回原始名称；若没有这行代码，无前缀工具会继续落入后续分支。
    return cleaned_name.split("__")[-1]  # 新增代码+BrowserToolSurfaceStage3: 取最后一段作为 MCP 原始工具名；若没有这行代码，分类函数会看到带 server 前缀的长名字。


def is_provider_specific_tool_name(tool_name: str) -> bool:  # 新增代码+BrowserToolSurfaceStage3: 判断工具名是否是禁止给模型看的 provider 专属重复动作；若没有这行代码，过滤逻辑会重复手写。
    normalized_name = normalized_browser_tool_name(tool_name)  # 新增代码+BrowserToolSurfaceStage3: 先去掉 MCP 前缀；若没有这行代码，MCP 工具名会漏判。
    for provider_prefix in PROVIDER_SPECIFIC_PREFIXES:  # 新增代码+BrowserToolSurfaceStage3: 遍历已知 provider 专属前缀；若没有这行代码，无法逐项判断。
        if not normalized_name.startswith(provider_prefix):  # 新增代码+BrowserToolSurfaceStage3: 当前前缀不匹配则继续；若没有这行代码，所有工具都会被错误拆后缀。
            continue  # 新增代码+BrowserToolSurfaceStage3: 跳过不匹配前缀；若没有这行代码，逻辑会继续错误判断。
        action_part = normalized_name.removeprefix(provider_prefix)  # 新增代码+BrowserToolSurfaceStage3: 去掉 provider 前缀得到动作名；若没有这行代码，无法比较 open/click/type 后缀。
        return action_part in PROVIDER_SPECIFIC_ACTION_SUFFIXES  # 新增代码+BrowserToolSurfaceStage3: 只有重复动作才判为 provider 专属工具；若没有这行代码，分类函数没有结果。
    return False  # 新增代码+BrowserToolSurfaceStage3: 没命中任何 provider 专属重复动作时返回 False；若没有这行代码，普通工具会隐式返回 None。


def is_provider_control_tool_name(tool_name: str) -> bool:  # 新增代码+BrowserToolSurfaceStage3: 判断工具是否是高级 provider 控制入口；若没有这行代码，MCP catalog 无法统一标记真实 Chrome 控制工具。
    normalized_name = normalized_browser_tool_name(tool_name)  # 新增代码+BrowserToolSurfaceStage3: 去掉 MCP 前缀后比较；若没有这行代码，mcp__ 前缀工具会漏判。
    return normalized_name in PROVIDER_CONTROL_TOOL_NAMES  # 新增代码+BrowserToolSurfaceStage3: 命中控制集合即返回 True；若没有这行代码，函数没有可用判断。


def browser_tool_surface_hint(tool_name: str) -> str:  # 新增代码+BrowserToolSurfaceStage3: 为工具目录生成给模型搜索结果看的工具表面提示；若没有这行代码，advanced/internal 语义会散在 registry。
    if is_provider_specific_tool_name(tool_name):  # 新增代码+BrowserToolSurfaceStage3: provider 专属重复动作是内部实现细节；若没有这行代码，错误工具没有清楚提示。
        return "internal provider-specific duplicate; do not expose to the model; use unified browser_* tools"  # 新增代码+BrowserToolSurfaceStage3: 返回内部工具提示；若没有这行代码，调用方不知道为何要过滤。
    if is_provider_control_tool_name(tool_name):  # 新增代码+BrowserToolSurfaceStage3: 高级控制入口允许存在但必须明确风险；若没有这行代码，真实 Chrome 控制工具没有提示。
        return "advanced provider-control; model should call unified browser_* actions and let BrowserProviderRouter choose the provider"  # 新增代码+BrowserToolSurfaceStage3: 返回高级控制提示；若没有这行代码，搜索结果不会解释单轨原则。
    return ""  # 新增代码+BrowserToolSurfaceStage3: 普通统一动作不添加额外提示；若没有这行代码，调用方会收到 None 并需要额外处理。
