"""Chrome 扩展配对状态文件。"""  # 新增代码+ChromeExtensionStage5: 说明本文件保存非敏感配对摘要；若没有这行代码，用户可能误以为会保存浏览器登录态。
from __future__ import annotations  # 新增代码+ChromeExtensionStage5: 延迟解析类型注解；若没有这行代码，Path 类型标注更脆弱。

import json  # 新增代码+ChromeExtensionStage5: 读写配对 JSON；若没有这行代码，状态无法持久化。
from pathlib import Path  # 新增代码+ChromeExtensionStage5: 处理状态文件路径；若没有这行代码，只能用脆弱字符串路径。
from typing import Any  # 新增代码+ChromeExtensionStage5: 状态字典需要通用 JSON 值；若没有这行代码，类型边界不清楚。


SENSITIVE_PAIRING_KEYS = {"cookie", "cookies", "token", "password", "authorization", "localstorage", "sessionstorage", "storage"}  # 新增代码+Phase2Pairing: 定义配对状态禁止保存的敏感键；如果没有这行代码，扩展可能把登录态写入磁盘。


def _is_sensitive_pairing_key(key: Any) -> bool:  # 新增代码+Phase2Pairing: 判断配对字段名是否敏感；如果没有这行代码，大小写或组合键可能绕过过滤。
    lowered = str(key or "").lower()  # 新增代码+Phase2Pairing: 字段名统一小写；如果没有这行代码，Token/PASSWORD 这类写法可能漏掉。
    return any(marker in lowered for marker in SENSITIVE_PAIRING_KEYS)  # 新增代码+Phase2Pairing: 命中任意敏感片段就过滤；如果没有这行代码，cookie/token 可能落盘。


def _safe_pairing_value(value: Any) -> Any:  # 新增代码+Phase2Pairing: 清理配对字段值；如果没有这行代码，嵌套对象可能夹带敏感信息。
    if isinstance(value, dict):  # 新增代码+Phase2Pairing: 字典需要递归过滤；如果没有这行代码，嵌套 token 会漏掉。
        return {str(key): _safe_pairing_value(item) for key, item in value.items() if not _is_sensitive_pairing_key(key)}  # 新增代码+Phase2Pairing: 删除敏感键并清理值；如果没有这行代码，配对状态会保存隐私字段。
    if isinstance(value, list):  # 新增代码+Phase2Pairing: 列表需要逐项清理；如果没有这行代码，allowed_origins 等数组无法安全保存。
        return [_safe_pairing_value(item) for item in value[:100]]  # 新增代码+Phase2Pairing: 限制最多 100 项；如果没有这行代码，恶意扩展可写超大状态文件。
    if isinstance(value, (str, int, float, bool)) or value is None:  # 新增代码+Phase2Pairing: JSON 标量可以直接保存；如果没有这行代码，普通 device_id/session_id 会被误丢。
        return str(value)[:2000] if isinstance(value, str) else value  # 新增代码+Phase2Pairing: 字符串截断；如果没有这行代码，超长选中文本可能撑大状态。
    return str(value)[:2000]  # 新增代码+Phase2Pairing: 未知对象转短文本；如果没有这行代码，JSON 写入可能失败。


class ChromeExtensionPairingStore:  # 新增代码+ChromeExtensionStage5: 管理扩展配对摘要；若没有这个类，host 连接状态会散落在文件读写里。
    def __init__(self, path: Path) -> None:  # 新增代码+ChromeExtensionStage5: 初始化配对状态路径；若没有这行代码，调用方无法创建 store。
        self.path = Path(path)  # 新增代码+ChromeExtensionStage5: 规范化路径对象；若没有这行代码，后续读写可能收到字符串。

    def load(self) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage5: 读取配对状态；若没有这行代码，provider 无法恢复连接摘要。
        if not self.path.exists():  # 新增代码+ChromeExtensionStage5: 文件不存在时返回空状态；若没有这行代码，首次启动会报错。
            return {}  # 新增代码+ChromeExtensionStage5: 返回空字典；若没有这行代码，调用方需要处理 None。
        try:  # 新增代码+ChromeExtensionStage5: 捕获 JSON 损坏；若没有这行代码，半写入文件会拖垮 host。
            data = json.loads(self.path.read_text(encoding="utf-8"))  # 新增代码+ChromeExtensionStage5: 读取并解析 JSON；若没有这行代码，状态只是文本。
        except Exception:  # 新增代码+ChromeExtensionStage5: 损坏状态走空状态；若没有这行代码，单个坏文件会阻断浏览器能力。
            return {}  # 新增代码+ChromeExtensionStage5: 返回空状态；若没有这行代码，异常会外溢。
        return data if isinstance(data, dict) else {}  # 新增代码+ChromeExtensionStage5: 只接受对象状态；若没有这行代码，数组或字符串会污染调用方。

    def save(self, state: dict[str, Any]) -> None:  # 新增代码+ChromeExtensionStage5: 保存配对状态；若没有这行代码，连接摘要无法持久化。
        self.path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+ChromeExtensionStage5: 确保目录存在；若没有这行代码，首次保存会失败。
        safe_state = {str(key): _safe_pairing_value(value) for key, value in state.items() if not _is_sensitive_pairing_key(key)}  # 修改代码+Phase2Pairing: 递归过滤敏感字段和值；如果没有这行代码，嵌套 token/cookie 仍可能落盘。
        self.path.write_text(json.dumps(safe_state, ensure_ascii=False, indent=2), encoding="utf-8")  # 新增代码+ChromeExtensionStage5: 写入 UTF-8 JSON；若没有这行代码，状态不会落盘。

    def save_pairing(self, pairing: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase2Pairing: 保存非敏感配对摘要；如果没有这行代码，bridge 需要手写配对字段过滤。
        state = self.load()  # 新增代码+Phase2Pairing: 读取已有 bridge 状态；如果没有这行代码，保存配对会覆盖 tabs/context 等旧信息。
        safe_pairing = _safe_pairing_value(dict(pairing or {}))  # 新增代码+Phase2Pairing: 清理配对 payload；如果没有这行代码，敏感字段可能进入 pairing。
        state["pairing"] = safe_pairing if isinstance(safe_pairing, dict) else {}  # 新增代码+Phase2Pairing: 写入 pairing 子对象；如果没有这行代码，状态结构不稳定。
        self.save(state)  # 新增代码+Phase2Pairing: 持久化更新后的状态；如果没有这行代码，配对只存在内存。
        return state["pairing"] if isinstance(state.get("pairing", {}), dict) else {}  # 新增代码+Phase2Pairing: 返回保存后的摘要；如果没有这行代码，调用方无法展示结果。

    def pairing_summary(self) -> dict[str, Any]:  # 新增代码+Phase2Pairing: 读取配对摘要；如果没有这行代码，状态工具无法统一获取 pairing。
        pairing = self.load().get("pairing", {})  # 新增代码+Phase2Pairing: 从状态文件读取 pairing；如果没有这行代码，summary 没有来源。
        return pairing if isinstance(pairing, dict) else {}  # 新增代码+Phase2Pairing: 非 dict 时返回空；如果没有这行代码，坏状态会让状态工具崩溃。
