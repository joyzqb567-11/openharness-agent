"""Windows Computer Use 应用清单兼容入口。"""  # 修改代码+WindowsAppInventory：说明本文件只保留兼容 API，并把真实应用发现委托给统一 inventory；如果没有这一行，读者容易误以为这里还维护一套独立发现逻辑。
from __future__ import annotations  # 修改代码+WindowsAppInventory：启用延迟类型注解；如果没有这一行，较复杂的类型标注在旧解释路径下更容易出错。

from typing import Any  # 修改代码+WindowsAppInventory：声明 JSON 风格参数类型；如果没有这一行，公开 API 的输入含义对初学者不够清楚。

try:  # 修改代码+WindowsAppInventory：优先按包路径导入统一 Windows 应用清单层；如果没有这一行，主项目运行时无法复用唯一的应用发现入口。
    from learning_agent.computer_use.windows_app_inventory import APP_INVENTORY_MAX_COUNT, build_windows_app_inventory, format_windows_app_inventory_for_model, sanitize_inventory_display_name  # 修改代码+WindowsAppInventory：导入统一清单构建、格式化和名称清洗能力；如果没有这一行，app_names 会继续重复造轮子。
except ModuleNotFoundError as error:  # 修改代码+WindowsAppInventory：兼容 start_oauth_agent.bat 从 learning_agent 目录启动的脚本模式；如果没有这一行，真实终端入口可能因为包路径不同而导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.windows_app_inventory"}:  # 修改代码+WindowsAppInventory：只兜底包路径缺失，不吞掉 inventory 内部真实 bug；如果没有这一行，排查清单逻辑会被隐藏异常误导。
        raise  # 修改代码+WindowsAppInventory：重新抛出内部真实错误；如果没有这一行，错误会被误当成脚本路径问题。
    from computer_use.windows_app_inventory import APP_INVENTORY_MAX_COUNT, build_windows_app_inventory, format_windows_app_inventory_for_model, sanitize_inventory_display_name  # type: ignore  # 修改代码+WindowsAppInventory：脚本模式导入同一套 inventory 能力；如果没有这一行，bat 入口无法使用统一应用清单。

APP_CATALOG_MAX_COUNT = APP_INVENTORY_MAX_COUNT  # 修改代码+WindowsAppInventory：保留旧 app_names 最大数量常量名并指向新 inventory 常量；如果没有这一行，旧测试和旧调用方会因为常量消失而失败。


def _app_names_collapse_spaces(text: Any) -> str:  # 修改代码+WindowsAppInventory：函数段开始，只保留别名解析需要的空白规范化；如果没有这段函数，resolve_app_name_hint 的中文/英文匹配会被多余空格干扰。
    return " ".join(str(text or "").strip().split())  # 修改代码+WindowsAppInventory：返回压缩后的文本；如果没有这一行，同一个应用名的多空格版本会匹配失败。
# 修改代码+WindowsAppInventory：函数段结束，_app_names_collapse_spaces 到此结束；如果没有这个边界说明，用户不容易看出兼容清洗范围。


def sanitize_app_display_name(raw: Any) -> str:  # 修改代码+WindowsAppInventory：函数段开始，保留旧公开清洗函数名并委托统一 inventory；如果没有这段函数，外部旧代码会直接导入失败。
    return sanitize_inventory_display_name(raw)  # 修改代码+WindowsAppInventory：调用统一显示名清洗规则；如果没有这一行，app_names 和 inventory 会再次出现两套不一致的清洗逻辑。
# 修改代码+WindowsAppInventory：函数段结束，sanitize_app_display_name 到此结束；如果没有这个边界说明，用户不容易看出旧 API 已经变成兼容包装。


def filter_apps_for_model_description(installed: Any, include_common: bool = True, max_count: int = APP_CATALOG_MAX_COUNT) -> list[dict[str, Any]]:  # 修改代码+WindowsAppInventory：函数段开始，保留旧过滤入口并委托统一 inventory；如果没有这段函数，主循环和旧测试会找不到原有 API。
    return build_windows_app_inventory(candidates=list(installed or []), include_common=include_common, max_count=max_count)  # 修改代码+WindowsAppInventory：用统一 inventory 做清洗、去重、来源优先级和风险过滤；如果没有这一行，app_names 会继续维护重复过滤代码。
# 修改代码+WindowsAppInventory：函数段结束，filter_apps_for_model_description 到此结束；如果没有这个边界说明，用户不容易看出过滤逻辑已经统一。


def format_apps_for_model_description(apps: Any) -> str:  # 修改代码+WindowsAppInventory：函数段开始，保留旧格式化入口并委托统一 inventory；如果没有这段函数，full 主循环无法用旧函数名生成模型提示。
    return format_windows_app_inventory_for_model(list(apps or []))  # 修改代码+WindowsAppInventory：输出 ClaudeCode 风格“模型提示而非硬白名单”的应用清单；如果没有这一行，模型看不到清洗后的 app 候选说明。
# 修改代码+WindowsAppInventory：函数段结束，format_apps_for_model_description 到此结束；如果没有这个边界说明，用户不容易看出格式化逻辑已经统一。


def discover_windows_app_catalog(candidates: list[dict[str, Any]] | None = None, include_common: bool = True, max_count: int = APP_CATALOG_MAX_COUNT) -> list[dict[str, Any]]:  # 修改代码+WindowsAppInventory：函数段开始，保留旧应用发现入口并委托统一 inventory；如果没有这段函数，agent.py 的现有调用会中断。
    return build_windows_app_inventory(candidates=candidates, include_common=include_common, max_count=max_count)  # 修改代码+WindowsAppInventory：统一融合开始菜单、App Paths、卸载注册表和注入候选；如果没有这一行，真实本机应用发现会退回旧的局部实现。
# 修改代码+WindowsAppInventory：函数段结束，discover_windows_app_catalog 到此结束；如果没有这个边界说明，用户不容易看出应用发现已经只有一个入口。


def resolve_app_name_hint(target_app_hint: Any, catalog: list[dict[str, Any]] | None = None) -> str:  # 修改代码+WindowsAppInventory：函数段开始，把用户友好应用提示解析成模型可调用 app_name；如果没有这段函数，旧的应用名解析调用方会失去兼容入口。
    query = _app_names_collapse_spaces(target_app_hint).lower()  # 修改代码+WindowsAppInventory：规范化用户传入的应用提示；如果没有这一行，中文名、英文名和多空格输入会更容易匹配失败。
    if not query:  # 修改代码+WindowsAppInventory：处理空应用提示；如果没有这一行，空输入可能误命中后续候选。
        return ""  # 修改代码+WindowsAppInventory：空提示返回空启动名；如果没有这一行，调用方无法区分“没有目标应用”和“匹配到了空字符串”。
    entries = catalog if catalog is not None else discover_windows_app_catalog(include_common=True)  # 修改代码+WindowsAppInventory：优先使用传入清单，否则实时读取统一 inventory；如果没有这一行，解析层只能靠硬编码。
    for entry in entries:  # 修改代码+WindowsAppInventory：遍历候选应用；如果没有这一行，函数无法检查任何候选。
        aliases = set(str(alias).lower() for alias in entry.get("aliases", ()) if str(alias).strip())  # 修改代码+WindowsAppInventory：读取 inventory 生成的别名集合；如果没有这一行，中文“画图”等别名无法命中。
        aliases.add(str(entry.get("display_name", "")).lower())  # 修改代码+WindowsAppInventory：把显示名加入匹配范围；如果没有这一行，用户输入应用可见名称可能无法解析。
        aliases.add(str(entry.get("app_name", "")).lower())  # 修改代码+WindowsAppInventory：把 app_name 加入匹配范围；如果没有这一行，mspaint 这类短名无法解析。
        aliases.add(str(entry.get("launch_id", "")).lower())  # 修改代码+WindowsAppInventory：把统一启动标识加入匹配范围；如果没有这一行，新 inventory 的 launch_id 无法参与解析。
        aliases.add(str(entry.get("executable", "")).lower())  # 修改代码+WindowsAppInventory：兼容旧字段 executable；如果没有这一行，旧测试或旧调用方传入的候选会匹配失败。
        if query in aliases:  # 修改代码+WindowsAppInventory：检查精确别名命中；如果没有这一行，解析结果永远为空。
            return str(entry.get("app_name", "") or "").strip()  # 修改代码+WindowsAppInventory：返回稳定 app_name；如果没有这一行，调用方拿不到模型工具应传的启动名。
    return ""  # 修改代码+WindowsAppInventory：未命中时返回空；如果没有这一行，调用方可能误用上一次或默认应用。
# 修改代码+WindowsAppInventory：函数段结束，resolve_app_name_hint 到此结束；如果没有这个边界说明，用户不容易看出兼容解析范围。


__all__ = ["APP_CATALOG_MAX_COUNT", "discover_windows_app_catalog", "filter_apps_for_model_description", "format_apps_for_model_description", "resolve_app_name_hint", "sanitize_app_display_name"]  # 修改代码+WindowsAppInventory：限定公开兼容 API；如果没有这一行，通配导入会暴露内部实现并再次增加误接风险。
