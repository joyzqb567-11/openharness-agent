"""浏览器站点权限管理，给真实 Chrome 登录态加 origin 边界。"""  # 新增代码+BrowserSecretStage9: 说明本模块负责站点级授权；若没有这行代码，权限边界不清楚。

from __future__ import annotations  # 新增代码+BrowserSecretStage9: 延迟解析类型注解；若没有这行代码，类型引用更脆弱。

from urllib.parse import urlparse  # 新增代码+BrowserSecretStage9: 解析 URL origin；若没有这行代码，origin 规范化会用脆弱字符串处理。
from typing import Any  # 新增代码+BrowserSecretStage9: to_dict 返回通用 JSON；若没有这行代码，类型边界不清楚。

SUPPORTED_SITE_PERMISSIONS = {"read", "click", "type", "submit", "upload", "console", "network"}  # 新增代码+ChromeExtensionStage7: 定义插件站点权限类型；若没有这行代码，权限名会散落且容易拼错。


def normalize_origin(url_or_origin: str) -> str:  # 新增代码+BrowserSecretStage9: 把 URL 或 origin 统一成 scheme://host[:port]；若没有这行代码，授权列表会重复或误匹配。
    text = str(url_or_origin).strip()  # 新增代码+BrowserSecretStage9: 清理输入文本；若没有这行代码，复制空格会导致解析失败。
    parsed = urlparse(text if "://" in text else f"https://{text}")  # 新增代码+BrowserSecretStage9: 兼容用户只输入域名；若没有这行代码，example.com 无法授权。
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:  # 新增代码+BrowserSecretStage9: 只允许 http/https origin；若没有这行代码，file/javascript 等危险协议可能被授权。
        raise ValueError("站点授权只支持 http/https origin。")  # 新增代码+BrowserSecretStage9: 抛出清楚错误；若没有这行代码，用户不知道格式限制。
    return f"{parsed.scheme}://{parsed.netloc}".lower()  # 新增代码+BrowserSecretStage9: 返回小写 origin；若没有这行代码，同一站点大小写可能重复。


def _normalize_permissions(permissions: list[str] | tuple[str, ...] | set[str] | str | None) -> set[str]:  # 新增代码+ChromeExtensionStage7: 规范化权限列表；若没有这行代码，字符串和列表输入会在各处分散处理。
    if permissions is None:  # 新增代码+ChromeExtensionStage7: None 表示旧兼容的全部权限；若没有这行代码，旧 grant(origin) 会失去含义。
        return set(SUPPORTED_SITE_PERMISSIONS)  # 新增代码+ChromeExtensionStage7: 返回全部支持权限；若没有这行代码，旧宽授权无法兼容。
    raw_items = [permissions] if isinstance(permissions, str) else list(permissions)  # 新增代码+ChromeExtensionStage7: 兼容单个字符串和列表；若没有这行代码，字符串会被拆成字符。
    normalized = {str(item).strip().lower() for item in raw_items if str(item).strip()}  # 新增代码+ChromeExtensionStage7: 清理权限名；若没有这行代码，大小写或空格会导致误判。
    unknown = normalized - SUPPORTED_SITE_PERMISSIONS  # 新增代码+ChromeExtensionStage7: 找出未知权限；若没有这行代码，拼错权限会静默失败。
    if unknown:  # 新增代码+ChromeExtensionStage7: 未知权限必须拒绝；若没有这行代码，授权状态会不可预测。
        raise ValueError(f"不支持的浏览器站点权限：{', '.join(sorted(unknown))}")  # 新增代码+ChromeExtensionStage7: 抛出清楚错误；若没有这行代码，用户不知道哪个权限写错。
    return normalized  # 新增代码+ChromeExtensionStage7: 返回规范权限集合；若没有这行代码，调用方拿不到结果。


class BrowserSitePermissions:  # 修改代码+ChromeExtensionStage7: 管理浏览器站点授权集合和动作级权限；若没有这个类，真实 Chrome 权限会散落在 server 字段中。
    def __init__(self, strict: bool = False, grants: list[str] | None = None, permission_grants: dict[str, list[str]] | None = None, events: list[dict[str, Any]] | None = None) -> None:  # 修改代码+ChromeExtensionStage7: 初始化严格模式、旧授权和动作级授权；若没有这行代码，调用方无法配置权限。
        self.strict = bool(strict)  # 新增代码+BrowserSecretStage9: 保存严格模式开关；若没有这行代码，授权集合无法启用。
        self.grants = {normalize_origin(item) for item in (grants or [])}  # 新增代码+BrowserSecretStage9: 规范化初始授权；若没有这行代码，持久化恢复可能含重复格式。
        self.permission_grants: dict[str, set[str]] = {origin: set(SUPPORTED_SITE_PERMISSIONS) for origin in self.grants}  # 新增代码+ChromeExtensionStage7: 旧 grants 视为全部权限；若没有这行代码，历史 grant(origin) 会只显示不生效。
        for raw_origin, raw_permissions in dict(permission_grants or {}).items():  # 新增代码+ChromeExtensionStage7: 导入已有动作级授权；若没有这行代码，持久化恢复无法保留细颗粒权限。
            origin = normalize_origin(raw_origin)  # 新增代码+ChromeExtensionStage7: 规范化 origin；若没有这行代码，同站不同写法会重复。
            self.grants.add(origin)  # 新增代码+ChromeExtensionStage7: 把 origin 加入兼容授权集合；若没有这行代码，旧状态展示看不到该站点。
            self.permission_grants[origin] = _normalize_permissions(raw_permissions)  # 新增代码+ChromeExtensionStage7: 保存动作级权限集合；若没有这行代码，权限类型不会生效。
        self.events = list(events or [])  # 新增代码+ChromeExtensionStage7: 保存权限变更事件；若没有这行代码，授权审计没有内存事实源。

    def grant(self, url_or_origin: str, permissions: list[str] | tuple[str, ...] | set[str] | str | None = None) -> str:  # 修改代码+ChromeExtensionStage7: 添加站点授权并可指定动作权限；若没有这行代码，用户无法允许目标站点。
        origin = normalize_origin(url_or_origin)  # 新增代码+BrowserSecretStage9: 规范化目标 origin；若没有这行代码，同站不同路径会重复。
        normalized_permissions = _normalize_permissions(permissions)  # 新增代码+ChromeExtensionStage7: 规范化动作权限；若没有这行代码，read/click/type 无法分开授权。
        self.grants.add(origin)  # 新增代码+BrowserSecretStage9: 写入授权集合；若没有这行代码，严格模式仍会拒绝。
        existing = self.permission_grants.setdefault(origin, set())  # 新增代码+ChromeExtensionStage7: 读取或创建该 origin 的权限集合；若没有这行代码，追加授权会覆盖旧权限。
        existing.update(normalized_permissions)  # 新增代码+ChromeExtensionStage7: 合并新增权限；若没有这行代码，多次授权不能叠加。
        self._record_event("grant", origin, normalized_permissions)  # 新增代码+ChromeExtensionStage7: 记录授权事件；若没有这行代码，审计看不到权限变化。
        return origin  # 新增代码+BrowserSecretStage9: 返回规范 origin；若没有这行代码，调用方无法展示实际授权。

    def revoke(self, url_or_origin: str, permissions: list[str] | tuple[str, ...] | set[str] | str | None = None) -> str:  # 修改代码+ChromeExtensionStage7: 移除站点授权或指定动作权限；若没有这行代码，错误授权无法撤回。
        origin = normalize_origin(url_or_origin)  # 新增代码+BrowserSecretStage9: 规范化目标 origin；若没有这行代码，撤销可能匹配不到。
        if permissions is None:  # 新增代码+ChromeExtensionStage7: 未指定权限时撤销整个 origin；若没有这行代码，旧 revoke(origin) 兼容会丢失。
            removed_permissions = set(self.permission_grants.get(origin, set()))  # 新增代码+ChromeExtensionStage7: 保存被移除权限用于审计；若没有这行代码，事件缺少权限类型。
            self.grants.discard(origin)  # 新增代码+BrowserSecretStage9: 从授权集合移除；若没有这行代码，严格模式仍会放行。
            self.permission_grants.pop(origin, None)  # 新增代码+ChromeExtensionStage7: 删除动作级权限；若没有这行代码，撤销后仍可能放行。
            self._record_event("revoke", origin, removed_permissions)  # 新增代码+ChromeExtensionStage7: 记录撤销事件；若没有这行代码，审计看不到撤销。
            return origin  # 新增代码+ChromeExtensionStage7: 返回规范 origin；若没有这行代码，旧调用方拿不到结果。
        normalized_permissions = _normalize_permissions(permissions)  # 新增代码+ChromeExtensionStage7: 规范化待撤销权限；若没有这行代码，部分撤销无法稳定执行。
        existing = self.permission_grants.setdefault(origin, set())  # 新增代码+ChromeExtensionStage7: 读取权限集合；若没有这行代码，撤销空集合会抛错。
        existing.difference_update(normalized_permissions)  # 新增代码+ChromeExtensionStage7: 移除指定权限；若没有这行代码，精细撤销不会生效。
        if not existing:  # 新增代码+ChromeExtensionStage7: 如果没有剩余权限则移除 origin；若没有这行代码，空授权站点会留在列表里误导用户。
            self.grants.discard(origin)  # 新增代码+ChromeExtensionStage7: 移除空权限 origin；若没有这行代码，状态会显示已授权但无权限。
            self.permission_grants.pop(origin, None)  # 新增代码+ChromeExtensionStage7: 删除空权限集合；若没有这行代码，to_dict 会输出空列表。
        self._record_event("revoke", origin, normalized_permissions)  # 新增代码+ChromeExtensionStage7: 记录部分撤销事件；若没有这行代码，审计不知道哪些权限被撤销。
        return origin  # 新增代码+BrowserSecretStage9: 返回规范 origin；若没有这行代码，调用方无法展示撤销对象。

    def is_allowed(self, url_or_origin: str, permission: str = "read") -> bool:  # 修改代码+ChromeExtensionStage7: 检查 URL 是否允许指定动作；若没有这行代码，read/click/type 无法分开判断。
        if not self.strict:  # 新增代码+BrowserSecretStage9: 非严格模式兼容旧行为；若没有这行代码，历史任务会突然被拒。
            return True  # 新增代码+BrowserSecretStage9: 放行所有站点；若没有这行代码，非严格模式没有意义。
        origin = normalize_origin(url_or_origin)  # 新增代码+ChromeExtensionStage7: 规范化待检查 origin；若没有这行代码，同站不同路径无法匹配。
        normalized_permission = next(iter(_normalize_permissions([permission])))  # 新增代码+ChromeExtensionStage7: 校验并规范化单个权限名；若没有这行代码，拼错权限可能被默默拒绝。
        return normalized_permission in self.permission_grants.get(origin, set())  # 修改代码+ChromeExtensionStage7: 严格模式只放行授权 origin 的指定权限；若没有这行代码，动作级权限不会生效。

    def require(self, url_or_origin: str, permission: str) -> None:  # 新增代码+ChromeExtensionStage7: 对外提供抛错式权限检查；若没有这行代码，provider 每次都要手写错误消息。
        if self.is_allowed(url_or_origin, permission):  # 新增代码+ChromeExtensionStage7: 已授权时直接返回；若没有这行代码，所有严格模式调用都会失败。
            return  # 新增代码+ChromeExtensionStage7: 授权成功无需动作；若没有这行代码，函数会继续抛错。
        origin = normalize_origin(url_or_origin)  # 新增代码+ChromeExtensionStage7: 规范化 origin 用于错误提示；若没有这行代码，提示里可能包含路径和参数。
        raise PermissionError(f"Chrome 插件站点权限拒绝：origin={origin} permission={permission}。请先调用 browser_site_grant grant 并传入 permissions。")  # 新增代码+ChromeExtensionStage7: 抛出明确修复步骤；若没有这行代码，模型不知道如何授权。

    def allowed_permissions(self, url_or_origin: str) -> list[str]:  # 新增代码+ChromeExtensionStage7: 返回某 origin 已授权权限；若没有这行代码，状态页无法展示细颗粒权限。
        origin = normalize_origin(url_or_origin)  # 新增代码+ChromeExtensionStage7: 规范化 origin；若没有这行代码，查询会重复和误匹配。
        return sorted(self.permission_grants.get(origin, set()))  # 新增代码+ChromeExtensionStage7: 返回稳定排序权限列表；若没有这行代码，状态输出不稳定。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+BrowserSecretStage9: 序列化站点权限状态；若没有这行代码，状态生态无法展示授权边界。
        return {"strict": self.strict, "grants": sorted(self.grants), "permission_grants": {origin: sorted(permissions) for origin, permissions in sorted(self.permission_grants.items())}, "events": list(self.events[-50:])}  # 修改代码+ChromeExtensionStage7: 返回 origin、动作级权限和最近事件；若没有这行代码，状态 diff 和审计不可见。

    def _record_event(self, action: str, origin: str, permissions: set[str]) -> None:  # 新增代码+ChromeExtensionStage7: 记录权限变更事件；若没有这行代码，授权审计会散落在调用方。
        self.events.append({"action": str(action), "origin": str(origin), "permissions": sorted(permissions)})  # 新增代码+ChromeExtensionStage7: 保存稳定事件字段；若没有这行代码，其他 agent 无法复盘权限变化。
