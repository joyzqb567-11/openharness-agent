"""Computer Use session 级目标窗口注册表。"""  # 新增代码+TargetRegistryRootRemediation：说明本文件负责托管 agent-owned 窗口身份；如果没有这一行，用户不知道 S2 根因修复入口在哪里。

from __future__ import annotations  # 新增代码+TargetRegistryRootRemediation：启用延迟类型解析；如果没有这一行，类型注解在旧导入顺序下更容易出错。

from dataclasses import asdict, dataclass  # 新增代码+TargetRegistryRootRemediation：导入 dataclass 和转字典工具；如果没有这一行，target 记录需要手写大量样板代码。
from time import time  # 新增代码+TargetRegistryRootRemediation：导入时间戳函数；如果没有这一行，target 记录无法说明何时注册。
from typing import Any  # 新增代码+TargetRegistryRootRemediation：导入通用 JSON 类型；如果没有这一行，registry 接口无法表达外部窗口字典。


def _target_registry_safe_text(value: Any) -> str:  # 新增代码+TargetRegistryRootRemediation：函数段开始，把外部字段转成安全字符串；如果没有这段函数，None 或数字字段会污染 target_ref 和身份字段。
    return str(value or "").strip()  # 新增代码+TargetRegistryRootRemediation：返回去掉空白的字符串；如果没有这一行，空值和前后空格会让窗口身份不稳定。
# 新增代码+TargetRegistryRootRemediation：函数段结束，_target_registry_safe_text 到此结束；如果没有这个边界说明，新手不容易看出字符串规范范围。


def _target_registry_session_slug(session_id: Any) -> str:  # 新增代码+TargetRegistryRootRemediation：函数段开始，把 session_id 转成 target_ref 可用片段；如果没有这段函数，特殊字符可能进入 target_ref。
    raw_text = _target_registry_safe_text(session_id) or "default-session"  # 新增代码+TargetRegistryRootRemediation：读取 session 文本并提供默认值；如果没有这一行，空 session 会生成难追踪的 ref。
    safe_chars = [character if character.isalnum() or character in {"-", "_"} else "-" for character in raw_text]  # 新增代码+TargetRegistryRootRemediation：把非安全字符替换成短横线；如果没有这一行，路径符号或空格可能让日志匹配困难。
    return "".join(safe_chars).strip("-") or "default-session"  # 新增代码+TargetRegistryRootRemediation：合并字符并再次兜底；如果没有这一行，全是特殊字符的 session 会得到空 ref。
# 新增代码+TargetRegistryRootRemediation：函数段结束，_target_registry_session_slug 到此结束；如果没有这个边界说明，新手不容易看出 session 规范范围。


@dataclass(frozen=True)  # 新增代码+TargetRegistryRootRemediation：让 target 记录不可变；如果没有这一行，后续代码可能无意改写已注册窗口事实。
class TargetRecord:  # 新增代码+TargetRegistryRootRemediation：类段开始，保存一个 agent-owned target 的稳定身份；如果没有这个类，registry 只能传散乱 dict。
    target_ref: str  # 新增代码+TargetRegistryRootRemediation：保存模型可见的稳定引用；如果没有这一行，模型仍要携带原始 target_window。
    app_id: str  # 新增代码+TargetRegistryRootRemediation：保存目标应用身份；如果没有这一行，agent-owned 校验不知道窗口属于哪个应用。
    window_id: str  # 新增代码+TargetRegistryRootRemediation：保存目标窗口身份；如果没有这一行，漂移校验没有窗口键。
    window_title: str  # 新增代码+TargetRegistryRootRemediation：保存可读窗口标题；如果没有这一行，调试 S2/S4 失败时难以看懂目标。
    process_id: str  # 新增代码+TargetRegistryRootRemediation：保存进程身份文本；如果没有这一行，未来校验 pid 时没有来源。
    created_at: float  # 新增代码+TargetRegistryRootRemediation：保存注册时间戳；如果没有这一行，旧 target 和新 target 难以区分。
    source_action: str  # 新增代码+TargetRegistryRootRemediation：保存 target 来源动作；如果没有这一行，无法确认是不是 launch_app 创建的 agent-owned 目标。
    raw_window: dict[str, Any]  # 新增代码+TargetRegistryRootRemediation：保存原始窗口字典副本；如果没有这一行，controller 无法把 target_ref 解析回后端需要的 window。
# 新增代码+TargetRegistryRootRemediation：类段结束，TargetRecord 到此结束；如果没有这个边界说明，新手不容易看出 target 记录字段范围。


class ComputerUseTargetRegistry:  # 新增代码+TargetRegistryRootRemediation：类段开始，托管一个 Computer Use session 内的目标窗口；如果没有这个类，S2 仍依赖模型手动记窗口。
    def __init__(self, session_id: Any = "learning-agent-default-session") -> None:  # 新增代码+TargetRegistryRootRemediation：函数段开始，初始化 registry 的 session 身份和内存记录；如果没有这段函数，registry 没有自己的 target_ref 命名空间。
        self.session_id = _target_registry_safe_text(session_id) or "learning-agent-default-session"  # 新增代码+TargetRegistryRootRemediation：保存原始 session 文本；如果没有这一行，状态报告无法说明 registry 属于哪个会话。
        self._session_slug = _target_registry_session_slug(self.session_id)  # 新增代码+TargetRegistryRootRemediation：保存 target_ref 使用的安全 session 片段；如果没有这一行，每次注册都要重复规范化。
        self._sequence = 0  # 新增代码+TargetRegistryRootRemediation：初始化 target 序号；如果没有这一行，多个 target_ref 可能重复。
        self._targets: dict[str, TargetRecord] = {}  # 新增代码+TargetRegistryRootRemediation：保存 target_ref 到记录的映射；如果没有这一行，resolve_target_ref 无法工作。
        self._active_target_ref: str | None = None  # 新增代码+TargetRegistryRootRemediation：保存当前 active target_ref；如果没有这一行，缺失 window 时无法自动注入目标。
    # 新增代码+TargetRegistryRootRemediation：函数段结束，ComputerUseTargetRegistry.__init__ 到此结束；如果没有这个边界说明，新手不容易看出初始化范围。

    def _next_target_ref(self) -> str:  # 新增代码+TargetRegistryRootRemediation：函数段开始，生成下一个稳定 target_ref；如果没有这段函数，注册逻辑会散落拼字符串。
        self._sequence += 1  # 新增代码+TargetRegistryRootRemediation：递增 session 内序号；如果没有这一行，同一 session 的多个窗口会得到重复 ref。
        return f"cu-target-{self._session_slug}-{self._sequence:04d}"  # 新增代码+TargetRegistryRootRemediation：返回包含 session 和序号的 ref；如果没有这一行，模型拿不到稳定短引用。
    # 新增代码+TargetRegistryRootRemediation：函数段结束，_next_target_ref 到此结束；如果没有这个边界说明，新手不容易看出 ref 生成范围。

    def register_target(self, target_window: dict[str, Any], source_action: str = "launch_app") -> str:  # 新增代码+TargetRegistryRootRemediation：函数段开始，注册 launch_app 返回的 agent-owned 目标窗口；如果没有这段函数，controller 无法把 raw window 托管起来。
        raw_window = dict(target_window or {})  # 新增代码+TargetRegistryRootRemediation：复制输入窗口字典；如果没有这一行，后续外部修改会污染 registry 事实。
        target_ref = self._next_target_ref()  # 新增代码+TargetRegistryRootRemediation：生成稳定 target_ref；如果没有这一行，模型仍需要使用原始窗口字典。
        record = TargetRecord(target_ref=target_ref, app_id=_target_registry_safe_text(raw_window.get("app_id") or raw_window.get("app") or raw_window.get("target_app")), window_id=_target_registry_safe_text(raw_window.get("window_id") or raw_window.get("hwnd") or raw_window.get("id")), window_title=_target_registry_safe_text(raw_window.get("window_title") or raw_window.get("title") or raw_window.get("name")), process_id=_target_registry_safe_text(raw_window.get("process_id") or raw_window.get("pid")), created_at=time(), source_action=_target_registry_safe_text(source_action) or "launch_app", raw_window=raw_window)  # 新增代码+TargetRegistryRootRemediation：构造不可变 target 记录；如果没有这一行，registry 无法统一保存窗口身份和原始窗口。
        self._targets[target_ref] = record  # 新增代码+TargetRegistryRootRemediation：把记录写入映射；如果没有这一行，后续无法按 ref 解析。
        self._active_target_ref = target_ref  # 新增代码+TargetRegistryRootRemediation：把最新注册目标设为 active；如果没有这一行，缺失 window 的动作无法自动注入当前目标。
        return target_ref  # 新增代码+TargetRegistryRootRemediation：返回模型可见短引用；如果没有这一行，launch_app 结果无法告诉模型后续该用哪个 ref。
    # 新增代码+TargetRegistryRootRemediation：函数段结束，register_target 到此结束；如果没有这个边界说明，新手不容易看出注册范围。

    def _record_to_public_dict(self, record: TargetRecord) -> dict[str, Any]:  # 新增代码+TargetRegistryRootRemediation：函数段开始，把内部 TargetRecord 转成对外字典；如果没有这段函数，多个方法会重复 asdict 和 raw_window 合并逻辑。
        payload = asdict(record)  # 新增代码+TargetRegistryRootRemediation：把 dataclass 转为普通字典；如果没有这一行，调用方不能按 JSON 风格读取字段。
        payload["window"] = dict(record.raw_window)  # 新增代码+TargetRegistryRootRemediation：额外暴露后端可用 window 字典；如果没有这一行，controller 解析后还要猜 raw_window 字段。
        return payload  # 新增代码+TargetRegistryRootRemediation：返回公开 payload；如果没有这一行，调用方拿不到 target 记录。
    # 新增代码+TargetRegistryRootRemediation：函数段结束，_record_to_public_dict 到此结束；如果没有这个边界说明，新手不容易看出格式化范围。

    def get_active_target(self) -> dict[str, Any] | None:  # 新增代码+TargetRegistryRootRemediation：函数段开始，读取当前 active target；如果没有这段函数，controller 无法在缺失 window 时自动注入。
        if self._active_target_ref is None:  # 新增代码+TargetRegistryRootRemediation：检查是否还没有 active ref；如果没有这一行，空 registry 会发生字典查找错误。
            return None  # 新增代码+TargetRegistryRootRemediation：没有 active target 时返回 None；如果没有这一行，调用方无法区分空状态和坏状态。
        record = self._targets.get(self._active_target_ref)  # 新增代码+TargetRegistryRootRemediation：按 active ref 读取记录；如果没有这一行，active ref 无法变成 target。
        return self._record_to_public_dict(record) if record is not None else None  # 新增代码+TargetRegistryRootRemediation：返回公开字典或 None；如果没有这一行，清理后的旧 active ref 可能导致异常。
    # 新增代码+TargetRegistryRootRemediation：函数段结束，get_active_target 到此结束；如果没有这个边界说明，新手不容易看出 active target 读取范围。

    def resolve_target_ref(self, target_ref: Any) -> dict[str, Any]:  # 新增代码+TargetRegistryRootRemediation：函数段开始，把模型传入的 target_ref 解析成真实 target；如果没有这段函数，target_ref 只是无用字符串。
        safe_ref = _target_registry_safe_text(target_ref)  # 新增代码+TargetRegistryRootRemediation：规范化外部 ref；如果没有这一行，None 或空格会污染查找逻辑。
        if not safe_ref:  # 新增代码+TargetRegistryRootRemediation：检查 ref 是否为空；如果没有这一行，空 ref 会被当作普通 miss 而缺少明确原因。
            return {"ok": False, "decision": "target_ref_missing", "target_ref": safe_ref, "target": {}, "low_level_event_count": 0, "recovery_next_allowed_actions": ["observe", "launch_app"]}  # 新增代码+TargetRegistryRootRemediation：返回空 ref 结构化失败；如果没有这一行，controller 可能抛异常或继续派发。
        record = self._targets.get(safe_ref)  # 新增代码+TargetRegistryRootRemediation：按 ref 查找记录；如果没有这一行，无法判断 ref 是否存在。
        if record is None:  # 新增代码+TargetRegistryRootRemediation：检查是否找到 target；如果没有这一行，坏 ref 会继续进入成功路径。
            return {"ok": False, "decision": "target_ref_not_found", "target_ref": safe_ref, "target": {}, "low_level_event_count": 0, "recovery_next_allowed_actions": ["observe", "launch_app"]}  # 新增代码+TargetRegistryRootRemediation：返回找不到 ref 的结构化失败；如果没有这一行，旧 ref 可能触发真实低层事件。
        return {"ok": True, "decision": "resolved", "target_ref": safe_ref, "target": self._record_to_public_dict(record), "low_level_event_count": 0, "recovery_next_allowed_actions": []}  # 新增代码+TargetRegistryRootRemediation：返回成功解析结果且不触发低层事件；如果没有这一行，controller 拿不到 raw window。
    # 新增代码+TargetRegistryRootRemediation：函数段结束，resolve_target_ref 到此结束；如果没有这个边界说明，新手不容易看出解析范围。

    def clear(self) -> dict[str, Any]:  # 新增代码+TargetRegistryRootRemediation：函数段开始，清空 session 内所有 target；如果没有这段函数，cleanup 后可能继续误用旧窗口。
        cleared_count = len(self._targets)  # 新增代码+TargetRegistryRootRemediation：记录清理前数量；如果没有这一行，报告无法说明清了多少目标。
        self._targets.clear()  # 新增代码+TargetRegistryRootRemediation：删除所有 target 记录；如果没有这一行，旧窗口仍可被解析。
        self._active_target_ref = None  # 新增代码+TargetRegistryRootRemediation：清空 active ref；如果没有这一行，get_active_target 可能还指向旧窗口。
        return {"ok": True, "decision": "cleared", "session_id": self.session_id, "cleared_count": cleared_count, "low_level_event_count": 0}  # 新增代码+TargetRegistryRootRemediation：返回结构化清理报告；如果没有这一行，cleanup 无法证明 target registry 已归零。
    # 新增代码+TargetRegistryRootRemediation：函数段结束，clear 到此结束；如果没有这个边界说明，新手不容易看出清理范围。

    def snapshot(self) -> dict[str, Any]:  # 新增代码+TargetRegistryRootRemediation：函数段开始，返回当前 registry 状态快照；如果没有这段函数，status 和测试无法读取 registry 摘要。
        return {"session_id": self.session_id, "active_target_ref": self._active_target_ref or "", "target_count": len(self._targets), "targets": [self._record_to_public_dict(record) for record in self._targets.values()]}  # 新增代码+TargetRegistryRootRemediation：返回可 JSON 化状态；如果没有这一行，调试 target 托管时只能查看私有字段。
    # 新增代码+TargetRegistryRootRemediation：函数段结束，snapshot 到此结束；如果没有这个边界说明，新手不容易看出状态快照范围。
# 新增代码+TargetRegistryRootRemediation：类段结束，ComputerUseTargetRegistry 到此结束；如果没有这个边界说明，新手不容易看出 registry 代码范围。


__all__ = ["ComputerUseTargetRegistry", "TargetRecord"]  # 新增代码+TargetRegistryRootRemediation：声明稳定导出 API；如果没有这一行，后续模块不知道哪些对象可以安全导入。
