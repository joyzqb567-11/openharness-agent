"""Computer Use session 级目标窗口注册表。"""  # 修改代码+UniversalTargetLease：说明本文件负责托管 target_ref、窗口和租约；如果没有这一行，读者不容易定位目标租约注册入口。
from __future__ import annotations  # 修改代码+UniversalTargetLease：启用延迟类型注解；如果没有这一行，复杂类型在旧导入顺序下更容易出错。

from dataclasses import asdict, dataclass  # 修改代码+UniversalTargetLease：导入 dataclass 和 asdict；如果没有这一行，目标记录需要手写大量样板转换。
from time import time  # 修改代码+UniversalTargetLease：导入时间戳函数；如果没有这一行，target 记录无法说明注册时间。
from typing import Any  # 修改代码+UniversalTargetLease：导入动态 JSON 类型；如果没有这一行，registry 无法表达工具层松散字典。
from learning_agent.computer_use_mcp_v2.windows_runtime.window_text_safety import sanitize_window_text  # 新增代码+WindowTextSafety：导入窗口文本清洗函数；如果没有这一行，registry 会把标题里的 prompt 注入原样暴露给模型。


def _target_registry_safe_text(value: Any) -> str:  # 修改代码+UniversalTargetLease：函数段开始，把外部值转成安全文本；如果没有这段函数，None 或数字字段会污染 target_ref。
    return str(value or "").strip()  # 修改代码+UniversalTargetLease：返回去除首尾空白的文本；如果没有这一行，空格和 None 会导致匹配不稳定。
# 修改代码+UniversalTargetLease：函数段结束，_target_registry_safe_text 到此结束；如果没有这个边界说明，用户不容易看出文本规范范围。


def _target_registry_session_slug(session_id: Any) -> str:  # 修改代码+UniversalTargetLease：函数段开始，把 session id 转成 target_ref 可用片段；如果没有这段函数，特殊字符可能进入 ref。
    raw_text = _target_registry_safe_text(session_id) or "default-session"  # 修改代码+UniversalTargetLease：读取 session 文本并设置默认值；如果没有这一行，空 session 会生成难追踪 ref。
    safe_chars = [character if character.isalnum() or character in {"-", "_"} else "-" for character in raw_text]  # 修改代码+UniversalTargetLease：把非安全字符替换成短横线；如果没有这一行，路径符号或空格会让日志匹配困难。
    return "".join(safe_chars).strip("-") or "default-session"  # 修改代码+UniversalTargetLease：合并字符并兜底；如果没有这一行，全特殊字符 session 会得到空 ref。
# 修改代码+UniversalTargetLease：函数段结束，_target_registry_session_slug 到此结束；如果没有这个边界说明，用户不容易看出 session 规范范围。


@dataclass(frozen=True)  # 修改代码+UniversalTargetLease：让 target 记录不可变；如果没有这一行，后续代码可能无意改写已注册窗口事实。
class TargetRecord:  # 修改代码+UniversalTargetLease：类段开始，保存一个 target_ref 对应的窗口和租约；如果没有这个类，registry 只能传散乱 dict。
    target_ref: str  # 修改代码+UniversalTargetLease：保存模型可见短引用；如果没有这一行，模型仍要携带原始 target_window。
    app_id: str  # 修改代码+UniversalTargetLease：保存目标应用身份；如果没有这一行，动作审计不知道窗口属于哪个应用。
    window_id: str  # 修改代码+UniversalTargetLease：保存目标窗口身份；如果没有这一行，漂移校验缺少窗口键。
    window_title: str  # 修改代码+UniversalTargetLease：保存可读窗口标题；如果没有这一行，调试失败时难以看懂目标。
    process_id: str  # 修改代码+UniversalTargetLease：保存进程身份文本；如果没有这一行，未来校验 pid 时没有来源。
    created_at: float  # 修改代码+UniversalTargetLease：保存注册时间戳；如果没有这一行，旧 target 和新 target 难以区分。
    source_action: str  # 修改代码+UniversalTargetLease：保存 target 来源动作；如果没有这一行，无法确认是不是 launch_app 创建的目标。
    raw_window: dict[str, Any]  # 修改代码+UniversalTargetLease：保存原始窗口字典副本；如果没有这一行，controller 无法把 target_ref 解析回后端 window。
    lease: dict[str, Any]  # 新增代码+UniversalTargetLease：保存目标租约报告；如果没有这一行，target_ref 只能还原窗口，不能证明动作前授权边界。
# 修改代码+UniversalTargetLease：类段结束，TargetRecord 到此结束；如果没有这个边界说明，用户不容易看出 target 记录字段范围。


class ComputerUseTargetRegistry:  # 修改代码+UniversalTargetLease：类段开始，托管一个 Computer Use session 内的目标；如果没有这个类，动作层仍依赖模型手动记窗口。
    def __init__(self, session_id: Any = "learning-agent-default-session") -> None:  # 修改代码+UniversalTargetLease：函数段开始，初始化 registry 状态；如果没有这段函数，registry 没有自己的 ref 命名空间。
        self.session_id = _target_registry_safe_text(session_id) or "learning-agent-default-session"  # 修改代码+UniversalTargetLease：保存 session 文本；如果没有这一行，状态报告无法说明 registry 归属。
        self._session_slug = _target_registry_session_slug(self.session_id)  # 修改代码+UniversalTargetLease：保存安全 session 片段；如果没有这一行，每次注册都要重复规范化。
        self._sequence = 0  # 修改代码+UniversalTargetLease：初始化 target 序号；如果没有这一行，多个 target_ref 可能重复。
        self._targets: dict[str, TargetRecord] = {}  # 修改代码+UniversalTargetLease：保存 target_ref 到记录的映射；如果没有这一行，resolve_target_ref 无法工作。
        self._active_target_ref: str | None = None  # 修改代码+UniversalTargetLease：保存当前 active target_ref；如果没有这一行，缺失 window 时无法自动注入目标。
    # 修改代码+UniversalTargetLease：函数段结束，ComputerUseTargetRegistry.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def _next_target_ref(self) -> str:  # 修改代码+UniversalTargetLease：函数段开始，生成下一个稳定 target_ref；如果没有这段函数，注册逻辑会散落拼字符串。
        self._sequence += 1  # 修改代码+UniversalTargetLease：递增 session 内序号；如果没有这一行，同一 session 的多个窗口会得到重复 ref。
        return f"cu-target-{self._session_slug}-{self._sequence:04d}"  # 修改代码+UniversalTargetLease：返回包含 session 和序号的 ref；如果没有这一行，模型拿不到稳定短引用。
    # 修改代码+UniversalTargetLease：函数段结束，_next_target_ref 到此结束；如果没有这个边界说明，用户不容易看出 ref 生成范围。

    def register_target(self, target_window: dict[str, Any], source_action: str = "launch_app", lease: Any | None = None) -> str:  # 修改代码+UniversalTargetLease：函数段开始，注册窗口时可同时保存租约；如果没有这个参数，动作前门禁拿不到授权来源。
        raw_window = dict(target_window or {})  # 修改代码+UniversalTargetLease：复制输入窗口字典；如果没有这一行，外部修改会污染 registry 事实。
        lease_report = lease.to_dict() if hasattr(lease, "to_dict") else dict(lease or {})  # 新增代码+UniversalTargetLease：把租约对象转成普通字典；如果没有这一行，registry 无法稳定序列化租约。
        target_ref = self._next_target_ref()  # 修改代码+UniversalTargetLease：生成稳定 target_ref；如果没有这一行，模型仍需要使用原始窗口字典。
        if lease_report and not _target_registry_safe_text(lease_report.get("target_ref")):  # 新增代码+UniversalTargetLease：检查租约是否缺少真实 ref；如果没有这一行，租约和 registry 可能对不上。
            lease_report["target_ref"] = target_ref  # 新增代码+UniversalTargetLease：把生成的 target_ref 回填进租约；如果没有这一行，后续审计无法从租约追到 registry。
        record = TargetRecord(  # 修改代码+UniversalTargetLease：构造不可变 target 记录；如果没有这一行，registry 无法统一保存窗口和租约。
            target_ref=target_ref,  # 修改代码+UniversalTargetLease：保存模型可见引用；如果没有这一行，解析时不知道记录名称。
            app_id=_target_registry_safe_text(raw_window.get("app_id") or raw_window.get("app") or raw_window.get("target_app")),  # 修改代码+UniversalTargetLease：保存应用身份；如果没有这一行，动作审计缺少应用摘要。
            window_id=_target_registry_safe_text(raw_window.get("window_id") or raw_window.get("hwnd") or raw_window.get("id")),  # 修改代码+UniversalTargetLease：保存窗口身份；如果没有这一行，漂移检查缺少窗口键。
            window_title=_target_registry_safe_text(raw_window.get("window_title") or raw_window.get("title") or raw_window.get("name")),  # 修改代码+UniversalTargetLease：保存可读标题；如果没有这一行，排查 target_ref 时看不出窗口。
            process_id=_target_registry_safe_text(raw_window.get("process_id") or raw_window.get("pid")),  # 修改代码+UniversalTargetLease：保存进程 id；如果没有这一行，租约报告缺少进程线索。
            created_at=time(),  # 修改代码+UniversalTargetLease：保存注册时间；如果没有这一行，新旧 target 难以区分。
            source_action=_target_registry_safe_text(source_action) or "launch_app",  # 修改代码+UniversalTargetLease：保存来源动作；如果没有这一行，无法判断目标是否来自 launch_app。
            raw_window=raw_window,  # 修改代码+UniversalTargetLease：保存原始窗口；如果没有这一行，后端执行时无法还原 window 参数。
            lease=lease_report,  # 新增代码+UniversalTargetLease：保存目标租约；如果没有这一行，动作前门禁无法通过 target_ref 找到租约。
        )  # 修改代码+UniversalTargetLease：结束 TargetRecord 构造；如果没有这一行，Python 语法不完整。
        self._targets[target_ref] = record  # 修改代码+UniversalTargetLease：把记录写入映射；如果没有这一行，后续无法按 ref 解析。
        self._active_target_ref = target_ref  # 修改代码+UniversalTargetLease：把最新注册目标设为 active；如果没有这一行，缺失 window 的动作无法自动注入当前目标。
        return target_ref  # 修改代码+UniversalTargetLease：返回模型可见短引用；如果没有这一行，launch_app 结果无法告诉模型后续该用哪个 ref。
    # 修改代码+UniversalTargetLease：函数段结束，register_target 到此结束；如果没有这个边界说明，用户不容易看出注册范围。

    def _record_to_public_dict(self, record: TargetRecord) -> dict[str, Any]:  # 修改代码+UniversalTargetLease：函数段开始，把内部记录转成公开字典；如果没有这段函数，多个方法会重复格式化逻辑。
        payload = asdict(record)  # 修改代码+UniversalTargetLease：把 dataclass 转为普通字典；如果没有这一行，调用方不能按 JSON 风格读取字段。
        payload["app_id"] = sanitize_window_text(record.app_id)  # 新增代码+WindowTextSafety：清洗公开应用文本；如果没有这一行，app_id 中的换行或反引号可能污染模型上下文。
        payload["window_id"] = sanitize_window_text(record.window_id)  # 新增代码+WindowTextSafety：清洗公开窗口 id 文本；如果没有这一行，异常 window_id 可能携带结构性提示符。
        payload["window_title"] = sanitize_window_text(record.window_title)  # 新增代码+WindowTextSafety：清洗公开窗口标题；如果没有这一行，窗口标题 prompt injection 会进入工具结果。
        payload["process_id"] = sanitize_window_text(record.process_id)  # 新增代码+WindowTextSafety：清洗公开进程 id 文本；如果没有这一行，坏 pid 字段可能带入不可控文本。
        safe_window = dict(record.raw_window)  # 新增代码+WindowTextSafety：复制原始窗口后再清洗公开副本；如果没有这一行，清洗会污染内部身份事实。
        for text_key in ("title", "title_preview", "window_title", "name", "app_id", "process_name"):  # 新增代码+WindowTextSafety：遍历模型可见的窗口文本字段；如果没有这一行，嵌套 window 仍可能暴露未清洗标题。
            if text_key in safe_window:  # 新增代码+WindowTextSafety：只清洗实际存在的字段；如果没有这一行，清洗会给窗口补出不必要空字段。
                safe_window[text_key] = sanitize_window_text(safe_window.get(text_key))  # 新增代码+WindowTextSafety：替换公开副本里的危险文本；如果没有这一行，raw window 标题仍可注入模型上下文。
        payload["window"] = safe_window  # 修改代码+WindowTextSafety：额外暴露已清洗的后端可用 window 字典；如果没有这一行，controller 解析后还要猜 raw_window 字段且模型可能看到未清洗文本。
        payload["lease"] = dict(record.lease)  # 新增代码+UniversalTargetLease：额外暴露目标租约；如果没有这一行，controller 解析 target_ref 后仍无法做租约门禁。
        return payload  # 修改代码+UniversalTargetLease：返回公开 payload；如果没有这一行，调用方拿不到 target 记录。
    # 修改代码+UniversalTargetLease：函数段结束，_record_to_public_dict 到此结束；如果没有这个边界说明，用户不容易看出格式化范围。

    def get_active_target(self) -> dict[str, Any] | None:  # 修改代码+UniversalTargetLease：函数段开始，读取当前 active target；如果没有这段函数，controller 无法在缺失 window 时自动注入。
        if self._active_target_ref is None:  # 修改代码+UniversalTargetLease：检查是否还没有 active ref；如果没有这一行，空 registry 会发生字典查找错误。
            return None  # 修改代码+UniversalTargetLease：没有 active target 时返回 None；如果没有这一行，调用方无法区分空状态和坏状态。
        record = self._targets.get(self._active_target_ref)  # 修改代码+UniversalTargetLease：按 active ref 读取记录；如果没有这一行，active ref 无法变成 target。
        return self._record_to_public_dict(record) if record is not None else None  # 修改代码+UniversalTargetLease：返回公开字典或 None；如果没有这一行，清理后的旧 active ref 可能导致异常。
    # 修改代码+UniversalTargetLease：函数段结束，get_active_target 到此结束；如果没有这个边界说明，用户不容易看出 active target 读取范围。

    def resolve_target_ref(self, target_ref: Any) -> dict[str, Any]:  # 修改代码+UniversalTargetLease：函数段开始，把模型传入的 target_ref 解析成真实 target；如果没有这段函数，target_ref 只是无用字符串。
        safe_ref = _target_registry_safe_text(target_ref)  # 修改代码+UniversalTargetLease：规范化外部 ref；如果没有这一行，None 或空格会污染查找逻辑。
        if not safe_ref:  # 修改代码+UniversalTargetLease：检查 ref 是否为空；如果没有这一行，空 ref 会被当作普通 miss 而缺少明确原因。
            return {"ok": False, "decision": "target_ref_missing", "target_ref": safe_ref, "target": {}, "low_level_event_count": 0, "recovery_next_allowed_actions": ["observe", "launch_app"]}  # 修改代码+UniversalTargetLease：返回空 ref 结构化失败；如果没有这一行，controller 可能抛异常或继续派发。
        record = self._targets.get(safe_ref)  # 修改代码+UniversalTargetLease：按 ref 查找记录；如果没有这一行，无法判断 ref 是否存在。
        if record is None:  # 修改代码+UniversalTargetLease：检查是否找到 target；如果没有这一行，坏 ref 会继续进入成功路径。
            return {"ok": False, "decision": "target_ref_not_found", "target_ref": safe_ref, "target": {}, "low_level_event_count": 0, "recovery_next_allowed_actions": ["observe", "launch_app"]}  # 修改代码+UniversalTargetLease：返回找不到 ref 的结构化失败；如果没有这一行，旧 ref 可能触发真实低层事件。
        return {"ok": True, "decision": "resolved", "target_ref": safe_ref, "target": self._record_to_public_dict(record), "low_level_event_count": 0, "recovery_next_allowed_actions": []}  # 修改代码+UniversalTargetLease：返回成功解析结果且不触发低层事件；如果没有这一行，controller 拿不到 raw window 和 lease。
    # 修改代码+UniversalTargetLease：函数段结束，resolve_target_ref 到此结束；如果没有这个边界说明，用户不容易看出解析范围。

    def clear(self) -> dict[str, Any]:  # 修改代码+UniversalTargetLease：函数段开始，清空 session 内所有 target；如果没有这段函数，cleanup 后可能继续误用旧窗口。
        cleared_count = len(self._targets)  # 修改代码+UniversalTargetLease：记录清理前数量；如果没有这一行，报告无法说明清了多少目标。
        self._targets.clear()  # 修改代码+UniversalTargetLease：删除所有 target 记录；如果没有这一行，旧窗口仍可被解析。
        self._active_target_ref = None  # 修改代码+UniversalTargetLease：清空 active ref；如果没有这一行，get_active_target 可能还指向旧窗口。
        return {"ok": True, "cleared": True, "decision": "cleared", "session_id": self.session_id, "cleared_count": cleared_count, "low_level_event_count": 0}  # 修改代码+UniversalTargetLease：返回结构化清理报告；如果没有这一行，cleanup 无法证明 registry 已归零。
    # 修改代码+UniversalTargetLease：函数段结束，clear 到此结束；如果没有这个边界说明，用户不容易看出清理范围。

    def snapshot(self) -> dict[str, Any]:  # 修改代码+UniversalTargetLease：函数段开始，返回当前 registry 状态快照；如果没有这段函数，status 和测试无法读取 registry 摘要。
        return {"session_id": self.session_id, "active_target_ref": self._active_target_ref or "", "target_count": len(self._targets), "targets": [self._record_to_public_dict(record) for record in self._targets.values()]}  # 修改代码+UniversalTargetLease：返回可 JSON 化状态；如果没有这一行，调试 target 托管时只能查看私有字段。
    # 修改代码+UniversalTargetLease：函数段结束，snapshot 到此结束；如果没有这个边界说明，用户不容易看出状态快照范围。
# 修改代码+UniversalTargetLease：类段结束，ComputerUseTargetRegistry 到此结束；如果没有这个边界说明，用户不容易看出 registry 范围。


__all__ = ["ComputerUseTargetRegistry", "TargetRecord"]  # 修改代码+UniversalTargetLease：声明稳定导出 API；如果没有这一行，后续模块不知道哪些对象可以安全导入。
