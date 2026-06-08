"""Computer Use 终端授权草案状态。"""  # 新增代码+Phase51ComputerStatusUI: 标明本文件只管理 `/computer` 面板可见的授权草案；如果没有这行代码，用户容易误以为它直接控制后端动作审批。
from __future__ import annotations  # 新增代码+Phase51ComputerStatusUI: 启用延迟类型解析；如果没有这行代码，旧导入顺序下 Path 类型标注更容易出错。

from pathlib import Path  # 新增代码+Phase51ComputerStatusUI: 导入 Path 统一管理 Windows 路径；如果没有这行代码，授权状态文件路径会更容易拼错。
from typing import Any  # 新增代码+Phase51ComputerStatusUI: 导入 Any 描述 JSON 状态值；如果没有这行代码，状态接口类型边界不清楚。

try:  # 新增代码+Phase51ComputerStatusUI: 优先按包模式导入安全 JSON 文件工具；如果没有这行代码，终端授权文件会重复实现易错读写。
    from learning_agent.runtime.files import atomic_write_json, read_json_or_default  # 新增代码+Phase51ComputerStatusUI: 导入原子写入和容错读取；如果没有这行代码，终端 grant 文件可能半写损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase51ComputerStatusUI: 兼容 start_oauth_agent.bat 脚本模式；如果没有这行代码，真实终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase51ComputerStatusUI: 只允许目标包路径缺失时 fallback；如果没有这行代码，runtime.files 内部真实错误会被误吞。
        raise  # 新增代码+Phase51ComputerStatusUI: 重新抛出非路径导入错误；如果没有这行代码，排查文件工具问题会很困难。
    from runtime.files import atomic_write_json, read_json_or_default  # 新增代码+Phase51ComputerStatusUI: 脚本模式导入文件工具；如果没有这行代码，bat 入口无法保存 terminal grant 状态。

PHASE51_TERMINAL_GRANT_SCOPE = "terminal_ui_only"  # 新增代码+Phase51ComputerStatusUI: 明确终端 grant 只是 UI 草案状态；如果没有这行代码，用户可能误解为已绕过 controller 审批。
PHASE51_ACTIONS_EXPANDED = False  # 新增代码+Phase51ComputerStatusUI: 明确 Phase51 不扩大真实动作能力；如果没有这行代码，状态 UI 升级容易被误解成新增可执行动作。


def _safe_text(value: Any, limit: int = 120) -> str:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，规范化 app 和 flag 文本；如果没有这段函数，状态文件可能被换行或超长字符串污染。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase51ComputerStatusUI: 把任意值压成单行；如果没有这行代码，终端输出可能被用户输入打散。
    return text[:limit]  # 新增代码+Phase51ComputerStatusUI: 限制字段长度；如果没有这行代码，长 app 名可能撑爆状态面板。
# 新增代码+Phase51ComputerStatusUI: 函数段结束，_safe_text 到此结束；如果没有这个边界说明，读者不容易看出文本清理范围。


class ComputerUseTerminalGrantStore:  # 新增代码+Phase51ComputerStatusUI: 类段开始，管理 `/computer grant/revoke` 的持久状态；如果没有这个类，终端授权入口无法跨命令显示。
    def __init__(self, base_dir: str | Path) -> None:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，初始化授权状态路径；如果没有这段函数，调用方无法指定当前 workspace 的状态目录。
        self.base_dir = Path(base_dir)  # 新增代码+Phase51ComputerStatusUI: 保存状态根目录；如果没有这行代码，后续读写没有稳定目录。
        self.state_path = self.base_dir / "terminal_grants.json"  # 新增代码+Phase51ComputerStatusUI: 定义授权草案 JSON 文件路径；如果没有这行代码，grant/revoke 无法持久化。
    # 新增代码+Phase51ComputerStatusUI: 函数段结束，__init__ 到此结束；如果没有这个边界说明，读者不容易看出路径初始化范围。

    def _read_state(self) -> dict[str, Any]:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，读取授权草案状态；如果没有这段函数，每个命令都要重复容错读取。
        state = read_json_or_default(self.state_path, {})  # 新增代码+Phase51ComputerStatusUI: 容错读取 JSON；如果没有这行代码，首次运行或坏文件会让命令崩溃。
        return dict(state) if isinstance(state, dict) else {}  # 新增代码+Phase51ComputerStatusUI: 确保返回字典；如果没有这行代码，坏 JSON 类型会污染状态逻辑。
    # 新增代码+Phase51ComputerStatusUI: 函数段结束，_read_state 到此结束；如果没有这个边界说明，读者不容易看出读取范围。

    def _write_state(self, state: dict[str, Any]) -> None:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，写入授权草案状态；如果没有这段函数，grant/revoke 只能停留在内存里。
        payload = dict(state)  # 新增代码+Phase51ComputerStatusUI: 复制状态避免调用方后续修改影响写入；如果没有这行代码，传入对象可能被共享污染。
        payload["grant_scope"] = PHASE51_TERMINAL_GRANT_SCOPE  # 新增代码+Phase51ComputerStatusUI: 写入清晰授权边界；如果没有这行代码，用户看文件时不知道这不是 controller 真授权。
        payload["actions_expanded"] = PHASE51_ACTIONS_EXPANDED  # 新增代码+Phase51ComputerStatusUI: 写入动作面边界；如果没有这行代码，状态文件缺少安全说明。
        atomic_write_json(self.state_path, payload)  # 新增代码+Phase51ComputerStatusUI: 原子写入 JSON；如果没有这行代码，进程中断可能留下半个授权文件。
    # 新增代码+Phase51ComputerStatusUI: 函数段结束，_write_state 到此结束；如果没有这个边界说明，读者不容易看出写入范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，返回终端授权草案状态；如果没有这段函数，/computer status 无法显示 grant/revoke 结果。
        state = self._read_state()  # 新增代码+Phase51ComputerStatusUI: 读取当前状态；如果没有这行代码，status 没有事实来源。
        grants = dict(state.get("grants", {})) if isinstance(state.get("grants", {}), dict) else {}  # 新增代码+Phase51ComputerStatusUI: 规范化 app grant 字典；如果没有这行代码，坏 grants 会导致状态崩溃。
        grant_flags = dict(state.get("grant_flags", {})) if isinstance(state.get("grant_flags", {}), dict) else {}  # 新增代码+Phase51ComputerStatusUI: 规范化 flag 字典；如果没有这行代码，状态无法显示已记录权限。
        return {"enabled": True, "grant_scope": PHASE51_TERMINAL_GRANT_SCOPE, "granted_app_count": len(grants), "grants": grants, "grant_flags": grant_flags, "state_path": str(self.state_path), "actions_expanded": PHASE51_ACTIONS_EXPANDED}  # 新增代码+Phase51ComputerStatusUI: 返回完整终端授权摘要；如果没有这行代码，renderer 无法展示授权草案。
    # 新增代码+Phase51ComputerStatusUI: 函数段结束，status 到此结束；如果没有这个边界说明，读者不容易看出状态输出范围。

    def grant_app(self, app_key: str, flags: list[str] | None = None) -> dict[str, Any]:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，记录一个终端授权草案；如果没有这段函数，/computer grant 无法跨命令保存。
        normalized_app = _safe_text(app_key, 120).lower()  # 新增代码+Phase51ComputerStatusUI: 规范化 app key；如果没有这行代码，同一 app 可能大小写不同产生多条记录。
        if not normalized_app:  # 新增代码+Phase51ComputerStatusUI: 检查 app key 是否为空；如果没有这行代码，空授权会污染状态文件。
            return {"grant_recorded": False, "reason": "app_key 不能为空。", "grant_scope": PHASE51_TERMINAL_GRANT_SCOPE, "actions_expanded": PHASE51_ACTIONS_EXPANDED}  # 新增代码+Phase51ComputerStatusUI: 返回缺参错误；如果没有这行代码，用户不知道 grant 为什么失败。
        state = self._read_state()  # 新增代码+Phase51ComputerStatusUI: 读取现有状态；如果没有这行代码，新 grant 会覆盖所有旧记录。
        grants = dict(state.get("grants", {})) if isinstance(state.get("grants", {}), dict) else {}  # 新增代码+Phase51ComputerStatusUI: 规范化 grant 字典；如果没有这行代码，坏状态会导致写入失败。
        grant_flags = dict(state.get("grant_flags", {})) if isinstance(state.get("grant_flags", {}), dict) else {}  # 新增代码+Phase51ComputerStatusUI: 规范化 flag 字典；如果没有这行代码，flag 写入没有容器。
        clean_flags = [_safe_text(flag, 80) for flag in list(flags or []) if _safe_text(flag, 80)]  # 新增代码+Phase51ComputerStatusUI: 清理传入 flags；如果没有这行代码，空 flag 或换行会污染状态。
        grants[normalized_app] = {"app_key": normalized_app, "flags": clean_flags, "grant_scope": PHASE51_TERMINAL_GRANT_SCOPE}  # 新增代码+Phase51ComputerStatusUI: 写入 app 授权草案；如果没有这行代码，grant 命令不会留下记录。
        for flag in clean_flags:  # 新增代码+Phase51ComputerStatusUI: 遍历本次记录的 flag；如果没有这行代码，状态摘要无法显示聚合 flag。
            grant_flags[flag] = True  # 新增代码+Phase51ComputerStatusUI: 标记 flag 已在终端草案中出现；如果没有这行代码，renderer 无法显示 desktopAction 等选择。
        self._write_state({"grants": grants, "grant_flags": grant_flags})  # 新增代码+Phase51ComputerStatusUI: 持久化更新后的状态；如果没有这行代码，下一条 status 看不到 grant。
        return {"grant_recorded": True, "app_key": normalized_app, "flags": clean_flags, "status": self.status(), "grant_scope": PHASE51_TERMINAL_GRANT_SCOPE, "actions_expanded": PHASE51_ACTIONS_EXPANDED}  # 新增代码+Phase51ComputerStatusUI: 返回 grant 结果；如果没有这行代码，终端无法显示成功证据。
    # 新增代码+Phase51ComputerStatusUI: 函数段结束，grant_app 到此结束；如果没有这个边界说明，读者不容易看出 grant 写入范围。

    def revoke_app(self, app_key: str) -> dict[str, Any]:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，撤销一个终端授权草案；如果没有这段函数，/computer revoke 无法收回 UI 状态。
        normalized_app = _safe_text(app_key, 120).lower()  # 新增代码+Phase51ComputerStatusUI: 规范化 app key；如果没有这行代码，大小写不同会导致撤销失败。
        state = self._read_state()  # 新增代码+Phase51ComputerStatusUI: 读取现有状态；如果没有这行代码，revoke 不知道当前 grants。
        grants = dict(state.get("grants", {})) if isinstance(state.get("grants", {}), dict) else {}  # 新增代码+Phase51ComputerStatusUI: 规范化 grant 字典；如果没有这行代码，坏状态会导致撤销崩溃。
        revoked = normalized_app in grants  # 新增代码+Phase51ComputerStatusUI: 判断目标是否存在；如果没有这行代码，终端无法告诉用户是否真的撤销。
        if revoked:  # 新增代码+Phase51ComputerStatusUI: 只有存在时才删除；如果没有这行代码，缺失目标也会误报成功。
            grants.pop(normalized_app, None)  # 新增代码+Phase51ComputerStatusUI: 删除目标 app 授权草案；如果没有这行代码，revoke 不会改变状态。
        grant_flags: dict[str, bool] = {}  # 新增代码+Phase51ComputerStatusUI: 重新计算聚合 flags；如果没有这行代码，撤销后旧 flag 可能残留。
        for grant in grants.values():  # 新增代码+Phase51ComputerStatusUI: 遍历剩余 grants；如果没有这行代码，无法重建 flag 摘要。
            for flag in list(dict(grant).get("flags", [])) if isinstance(grant, dict) else []:  # 新增代码+Phase51ComputerStatusUI: 遍历每个 grant 的 flags；如果没有这行代码，剩余授权的 flags 会丢失。
                grant_flags[_safe_text(flag, 80)] = True  # 新增代码+Phase51ComputerStatusUI: 写入仍然存在的 flag；如果没有这行代码，status 可能错误显示没有权限草案。
        self._write_state({"grants": grants, "grant_flags": grant_flags})  # 新增代码+Phase51ComputerStatusUI: 持久化撤销后的状态；如果没有这行代码，下一条 status 仍显示旧授权。
        return {"revoked": revoked, "app_key": normalized_app, "status": self.status(), "grant_scope": PHASE51_TERMINAL_GRANT_SCOPE, "actions_expanded": PHASE51_ACTIONS_EXPANDED}  # 新增代码+Phase51ComputerStatusUI: 返回 revoke 结果；如果没有这行代码，终端无法显示撤销证据。
    # 新增代码+Phase51ComputerStatusUI: 函数段结束，revoke_app 到此结束；如果没有这个边界说明，读者不容易看出 revoke 范围。
# 新增代码+Phase51ComputerStatusUI: 类段结束，ComputerUseTerminalGrantStore 到此结束；如果没有这个边界说明，读者不容易看出终端授权状态类范围。
