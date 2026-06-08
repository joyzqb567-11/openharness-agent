"""浏览器 provider 注册表。"""  # 新增代码+BrowserProviderRouter: 说明本文件负责 provider 健康状态查询；若没有这行代码，provider 生命周期边界不清楚。
from __future__ import annotations  # 新增代码+BrowserProviderRouter: 延迟解析类型注解；若没有这行代码，类型引用顺序更脆弱。

from .protocol import BrowserProvider, BrowserProviderHealth, BrowserProviderKind  # 修改代码+BrowserProviderAdapters: 导入 provider 协议、类型和健康状态；若没有这行代码，registry 只能记录 health 而不能返回 adapter。


class BrowserProviderRegistry:  # 新增代码+BrowserProviderRouter: 定义 provider 注册表；若没有这个类，router 只能接收散落的健康 dict。
    def __init__(self) -> None:  # 新增代码+BrowserProviderRouter: 初始化空 provider 映射；若没有这行代码，实例没有存储空间。
        self._health: dict[BrowserProviderKind, BrowserProviderHealth] = {}  # 新增代码+BrowserProviderRouter: 保存 provider 健康状态；若没有这行代码，health 查询无法工作。
        self._providers: dict[BrowserProviderKind, BrowserProvider] = {}  # 新增代码+BrowserProviderAdapters: 保存 provider adapter 对象；若没有这行代码，server 无法从 registry 取回执行器。

    def register_provider(self, provider: BrowserProvider) -> None:  # 新增代码+BrowserProviderAdapters: 注册 provider adapter 并刷新健康状态；若没有这行代码，Stage 2 adapter 只能散落在 server 字段里。
        self._providers[provider.kind] = provider  # 新增代码+BrowserProviderAdapters: 按 provider 类型保存 adapter；若没有这行代码，后续查找 provider 会失败。
        self.set_health(provider.health())  # 新增代码+BrowserProviderAdapters: 注册时同步健康状态；若没有这行代码，router 看不到 provider 当前是否可用。

    def set_health(self, health: BrowserProviderHealth) -> None:  # 新增代码+BrowserProviderRouter: 允许测试和未来 provider 更新健康状态；若没有这行代码，registry 无法记录可用 provider。
        self._health[health.kind] = health  # 新增代码+BrowserProviderRouter: 按 provider 类型保存状态；若没有这行代码，set_health 没有效果。

    def health(self, kind: BrowserProviderKind) -> BrowserProviderHealth:  # 新增代码+BrowserProviderRouter: 查询单个 provider 健康状态；若没有这行代码，router 无法统一读取状态。
        return self._health.get(kind, BrowserProviderHealth.unavailable(kind, "not_registered"))  # 新增代码+BrowserProviderRouter: 未注册 provider 返回不可用；若没有这行代码，缺插件可能被误判成功。

    def all_health(self) -> dict[BrowserProviderKind, BrowserProviderHealth]:  # 新增代码+BrowserProviderRouter: 返回健康状态副本；若没有这行代码，router 无法一次读取全部 provider。
        return dict(self._health)  # 新增代码+BrowserProviderRouter: 返回副本避免外部污染内部映射；若没有这行代码，调用方可能修改 registry 状态。

    def provider(self, kind: BrowserProviderKind) -> BrowserProvider | None:  # 新增代码+BrowserProviderAdapters: 查询单个 provider adapter；若没有这行代码，server 无法按 router 决策找到执行轨道。
        return self._providers.get(kind)  # 新增代码+BrowserProviderAdapters: 返回已注册 adapter 或 None；若没有这行代码，缺 provider 时无法安全降级。

    def all_providers(self) -> dict[BrowserProviderKind, BrowserProvider]:  # 新增代码+BrowserProviderAdapters: 返回 provider adapter 副本；若没有这行代码，状态 API 无法列出当前接入的 provider。
        return dict(self._providers)  # 新增代码+BrowserProviderAdapters: 返回副本避免调用方污染内部注册表；若没有这行代码，外部代码可能删掉 provider。
