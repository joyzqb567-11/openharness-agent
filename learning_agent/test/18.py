"""通用 Computer Use 目标租约。"""  # 新增代码+UniversalTargetLease：说明本模块负责通用目标租约；如果没有这一行，读者不容易区分它和旧窗口 registry。
from __future__ import annotations  # 新增代码+UniversalTargetLease：启用延迟类型注解；如果没有这一行，复杂类型在导入阶段更容易遇到顺序问题。

import hashlib  # 新增代码+UniversalTargetLease：导入哈希库用于脱敏标题指纹；如果没有这一行，租约无法在不暴露标题的情况下追踪漂移。
import time  # 新增代码+UniversalTargetLease：导入时间模块用于租约创建时间；如果没有这一行，审计无法区分新旧目标。
from dataclasses import dataclass  # 新增代码+UniversalTargetLease：导入 dataclass 简化只读数据结构；如果没有这一行，租约报告需要手写大量样板。
from typing import Any  # 新增代码+UniversalTargetLease：导入 Any 表示工具层 JSON 风格输入；如果没有这一行，接口边界不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.target_identity import build_owned_target_identity, verify_owned_target_identity  # 新增代码+UniversalTargetLease：复用现有目标身份模型；如果没有这一行，租约会复制一套更容易漂移的 pid/hwnd 比较逻辑。


WRITE_ACTIONS_REQUIRING_LEASE = {  # 新增代码+UniversalTargetLease：定义必须持有租约的写动作集合；如果没有这一行，full mode 可能继续允许裸窗口写入。
    "click",  # 新增代码+UniversalTargetLease：点击会改变应用状态；如果没有这一项，鼠标点击可能打到用户窗口。
    "double_click",  # 新增代码+UniversalTargetLease：双击会打开或编辑对象；如果没有这一项，双击可能误触用户资料。
    "right_click",  # 新增代码+UniversalTargetLease：右键会打开上下文菜单；如果没有这一项，后续菜单操作可能漂移。
    "move_mouse",  # 新增代码+UniversalTargetLease：移动鼠标本身影响用户可见桌面；如果没有这一项，动作来源难以审计。
    "drag_path",  # 新增代码+UniversalTargetLease：拖拽会移动窗口或绘制内容；如果没有这一项，压力测试里的拖拽可能误作用旧窗口。
    "press_key",  # 新增代码+UniversalTargetLease：按键可能触发保存、全选或删除；如果没有这一项，键盘动作可能破坏用户内容。
    "key",  # 新增代码+UniversalTargetLease：兼容部分工具面使用 key 名称；如果没有这一项，同类按键可能绕过门禁。
    "type_text",  # 新增代码+UniversalTargetLease：文本输入会修改用户内容；如果没有这一项，本次 Notepad 类事故会复发。
    "scroll",  # 新增代码+UniversalTargetLease：滚动会改变当前应用状态；如果没有这一项，观察和动作上下文可能漂移。
}  # 新增代码+UniversalTargetLease：结束写动作集合；如果没有这一行，Python 语法不完整。


def _safe_text(value: Any) -> str:  # 新增代码+UniversalTargetLease：函数段开始，统一把动态值转成安全文本；如果没有这段函数，None 和数字字段会导致比较不稳定。
    return str(value or "").strip()  # 新增代码+UniversalTargetLease：返回去空白文本；如果没有这一行，空值和空格会污染租约字段。
# 新增代码+UniversalTargetLease：函数段结束，_safe_text 到此结束；如果没有这个边界说明，用户不容易看出文本规范范围。


def _safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+UniversalTargetLease：函数段开始，统一把动态对象转成字典副本；如果没有这段函数，坏输入可能让租约构造崩溃。
    return dict(value or {}) if isinstance(value, dict) else {}  # 新增代码+UniversalTargetLease：只接受字典并复制；如果没有这一行，外部可变对象可能污染租约事实。
# 新增代码+UniversalTargetLease：函数段结束，_safe_dict 到此结束；如果没有这个边界说明，用户不容易看出字典清洗范围。


def _sha256_16(value: Any) -> str:  # 新增代码+UniversalTargetLease：函数段开始，生成短哈希；如果没有这段函数，租约报告要么泄露标题要么缺少漂移指纹。
    return hashlib.sha256(_safe_text(value).encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+UniversalTargetLease：返回 16 位标题指纹；如果没有这一行，标题变化无法稳定审计。
# 新增代码+UniversalTargetLease：函数段结束，_sha256_16 到此结束；如果没有这个边界说明，用户不容易看出脱敏范围。


@dataclass(frozen=True)  # 新增代码+UniversalTargetLease：让租约对象不可变；如果没有这一行，调用方可能事后修改审计事实。
class TargetLease:  # 新增代码+UniversalTargetLease：类段开始，表示当前 session 对一个目标窗口的控制租约；如果没有这个类，target_ref 只能表示窗口，不能表示权限来源。
    session_id: str  # 新增代码+UniversalTargetLease：保存租约所属会话；如果没有这一行，多会话控制时无法隔离目标。
    target_ref: str  # 新增代码+UniversalTargetLease：保存模型可见短引用；如果没有这一行，后续动作无法稳定引用目标。
    origin: str  # 新增代码+UniversalTargetLease：保存租约来源；如果没有这一行，无法区分 agent 自启动和用户授权旧窗口。
    created_at: float  # 新增代码+UniversalTargetLease：保存创建时间；如果没有这一行，新旧租约难以审计。
    target_window: dict[str, Any]  # 新增代码+UniversalTargetLease：保存目标窗口快照；如果没有这一行，动作前没有窗口基准。
    owned_target_identity: dict[str, Any]  # 新增代码+UniversalTargetLease：保存现有身份模型报告；如果没有这一行，租约无法复用 pid/hwnd 验证事实。
    user_granted_existing_window: bool  # 新增代码+UniversalTargetLease：保存用户是否授权已有窗口；如果没有这一行，full mode 可能默认接管用户窗口。
    lease_identity_verified: bool  # 新增代码+UniversalTargetLease：保存首次租约是否可信；如果没有这一行，坏租约可能进入动作阶段。
    title_sha256_16: str  # 新增代码+UniversalTargetLease：保存标题指纹；如果没有这一行，标题漂移缺少审计线索。
    low_level_event_count: int = 0  # 新增代码+UniversalTargetLease：声明租约构建本身零低层事件；如果没有这一行，安全报告无法证明门禁无副作用。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+UniversalTargetLease：函数段开始，把租约转成 JSON 风格报告；如果没有这段函数，controller 和 registry 无法稳定落盘。
        return {  # 新增代码+UniversalTargetLease：返回租约公开字典；如果没有这一行，上层拿不到结构化结果。
            "session_id": self.session_id,  # 新增代码+UniversalTargetLease：输出会话 id；如果没有这一行，报告无法确认租约归属。
            "target_ref": self.target_ref,  # 新增代码+UniversalTargetLease：输出目标引用；如果没有这一行，后续动作无法关联租约。
            "origin": self.origin,  # 新增代码+UniversalTargetLease：输出来源；如果没有这一行，审计看不出权限来自哪里。
            "created_at": self.created_at,  # 新增代码+UniversalTargetLease：输出创建时间；如果没有这一行，旧租约无法被识别。
            "target_window": dict(self.target_window),  # 新增代码+UniversalTargetLease：输出窗口副本；如果没有这一行，动作前无法还原基准窗口。
            "owned_target_identity": dict(self.owned_target_identity),  # 新增代码+UniversalTargetLease：输出身份报告副本；如果没有这一行，漂移失败缺少证据。
            "user_granted_existing_window": self.user_granted_existing_window,  # 新增代码+UniversalTargetLease：输出用户授权状态；如果没有这一行，已有窗口授权不可审计。
            "lease_identity_verified": self.lease_identity_verified,  # 新增代码+UniversalTargetLease：输出首次验证状态；如果没有这一行，失败路径无法解释。
            "title_sha256_16": self.title_sha256_16,  # 新增代码+UniversalTargetLease：输出标题短哈希；如果没有这一行，标题漂移不可追踪。
            "low_level_event_count": self.low_level_event_count,  # 新增代码+UniversalTargetLease：输出零事件计数；如果没有这一行，门禁副作用不可证明。
        }  # 新增代码+UniversalTargetLease：结束租约报告；如果没有这一行，Python 语法不完整。
    # 新增代码+UniversalTargetLease：函数段结束，TargetLease.to_dict 到此结束；如果没有这个边界说明，用户不容易看出租约报告范围。
# 新增代码+UniversalTargetLease：类段结束，TargetLease 到此结束；如果没有这个边界说明，用户不容易看出租约结构范围。


@dataclass(frozen=True)  # 新增代码+UniversalTargetLease：让验证结果不可变；如果没有这一行，调用方可能改写安全结论。
class TargetLeaseVerification:  # 新增代码+UniversalTargetLease：类段开始，表示动作前租约验证结果；如果没有这个类，允许和拒绝会以散乱 dict 传递。
    allowed: bool  # 新增代码+UniversalTargetLease：保存是否允许动作；如果没有这一行，controller 无法统一判断。
    decision: str  # 新增代码+UniversalTargetLease：保存稳定决策 token；如果没有这一行，模型无法理解拒绝原因。
    target_drift_blocks_action: bool  # 新增代码+UniversalTargetLease：保存漂移是否阻断动作；如果没有这一行，报告无法证明错窗零事件。
    low_level_event_count: int  # 新增代码+UniversalTargetLease：保存验证阶段低层事件数；如果没有这一行，拒绝路径无法证明没有碰桌面。
    expected: dict[str, Any]  # 新增代码+UniversalTargetLease：保存期望租约摘要；如果没有这一行，失败时看不到目标基准。
    current: dict[str, Any]  # 新增代码+UniversalTargetLease：保存当前窗口摘要；如果没有这一行，失败时看不到漂移到哪里。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+UniversalTargetLease：函数段开始，把验证结果转成 JSON 字典；如果没有这段函数，controller 无法把结果放进工具输出。
        return {  # 新增代码+UniversalTargetLease：返回验证报告；如果没有这一行，上层拿不到结构化状态。
            "allowed": self.allowed,  # 新增代码+UniversalTargetLease：输出允许状态；如果没有这一行，工具结果无法判断成功失败。
            "decision": self.decision,  # 新增代码+UniversalTargetLease：输出决策 token；如果没有这一行，恢复流程缺少稳定锚点。
            "target_drift_blocks_action": self.target_drift_blocks_action,  # 新增代码+UniversalTargetLease：输出漂移阻断状态；如果没有这一行，安全矩阵无法断言。
            "low_level_event_count": self.low_level_event_count,  # 新增代码+UniversalTargetLease：输出零事件计数；如果没有这一行，拒绝副作用不可验。
            "expected": dict(self.expected),  # 新增代码+UniversalTargetLease：输出期望目标；如果没有这一行，调试无法看见原始基准。
            "current": dict(self.current),  # 新增代码+UniversalTargetLease：输出当前目标；如果没有这一行，调试无法看见漂移目标。
        }  # 新增代码+UniversalTargetLease：结束验证报告；如果没有这一行，Python 语法不完整。
    # 新增代码+UniversalTargetLease：函数段结束，TargetLeaseVerification.to_dict 到此结束；如果没有这个边界说明，用户不容易看出验证报告范围。
# 新增代码+UniversalTargetLease：类段结束，TargetLeaseVerification 到此结束；如果没有这个边界说明，用户不容易看出验证结构范围。


def build_target_lease(  # 新增代码+UniversalTargetLease：函数段开始，从启动报告和窗口构建租约；如果没有这段函数，launch_app 无法生成通用控制凭证。
    *,  # 新增代码+UniversalTargetLease：强制使用关键字参数；如果没有这一行，调用方容易把启动报告和窗口参数传反。
    session_id: Any,  # 新增代码+UniversalTargetLease：接收会话 id；如果没有这一行，租约无法绑定当前 controller。
    target_ref: Any,  # 新增代码+UniversalTargetLease：接收目标引用；如果没有这一行，租约无法和 registry 对齐。
    origin: Any,  # 新增代码+UniversalTargetLease：接收租约来源；如果没有这一行，授权策略无法分支。
    launch_result: dict[str, Any],  # 新增代码+UniversalTargetLease：接收启动事实；如果没有这一行，agent-owned 目标无法验证进程。
    target_window: dict[str, Any],  # 新增代码+UniversalTargetLease：接收窗口事实；如果没有这一行，租约无法验证窗口。
    user_granted_existing_window: bool,  # 新增代码+UniversalTargetLease：接收用户是否授权已有窗口；如果没有这一行，旧窗口可能被默认放行。
) -> TargetLease:  # 新增代码+UniversalTargetLease：声明返回 TargetLease；如果没有这一行，调用方不知道结果类型。
    safe_window = _safe_dict(target_window)  # 新增代码+UniversalTargetLease：复制窗口事实；如果没有这一行，外部修改会污染租约。
    safe_launch = _safe_dict(launch_result)  # 新增代码+UniversalTargetLease：复制启动事实；如果没有这一行，外部修改会污染身份报告。
    safe_origin = _safe_text(origin) or "unknown"  # 新增代码+UniversalTargetLease：规范来源字段；如果没有这一行，空来源会导致策略不稳定。
    owned = build_owned_target_identity(safe_launch, safe_window).to_report()  # 新增代码+UniversalTargetLease：复用现有自有目标身份模型；如果没有这一行，租约无法证明 agent-owned 窗口。
    lease_verified = bool(owned.get("target_identity_verified") if safe_origin == "agent_owned_launch" else user_granted_existing_window)  # 新增代码+UniversalTargetLease：计算首次租约是否可信；如果没有这一行，坏租约可能被动作阶段误用。
    return TargetLease(  # 新增代码+UniversalTargetLease：返回租约对象；如果没有这一行，调用方拿不到目标凭证。
        session_id=_safe_text(session_id) or "learning-agent-default-session",  # 新增代码+UniversalTargetLease：保存会话 id；如果没有这一行，租约不能绑定 controller。
        target_ref=_safe_text(target_ref),  # 新增代码+UniversalTargetLease：保存 target_ref；如果没有这一行，租约不能和 registry 对齐。
        origin=safe_origin,  # 新增代码+UniversalTargetLease：保存来源；如果没有这一行，动作前无法区分授权规则。
        created_at=time.time(),  # 新增代码+UniversalTargetLease：保存创建时间；如果没有这一行，新旧租约难以排查。
        target_window=safe_window,  # 新增代码+UniversalTargetLease：保存窗口快照；如果没有这一行，动作前验证没有基准。
        owned_target_identity=owned,  # 新增代码+UniversalTargetLease：保存身份报告；如果没有这一行，失败报告缺少证据链。
        user_granted_existing_window=bool(user_granted_existing_window),  # 新增代码+UniversalTargetLease：保存用户授权布尔值；如果没有这一行，已有窗口授权不可审计。
        lease_identity_verified=lease_verified,  # 新增代码+UniversalTargetLease：保存首次验证状态；如果没有这一行，动作前无法拒绝坏租约。
        title_sha256_16=_sha256_16(safe_window.get("title_preview") or safe_window.get("title")),  # 新增代码+UniversalTargetLease：保存标题短哈希；如果没有这一行，标题漂移缺少审计线索。
    )  # 新增代码+UniversalTargetLease：结束 TargetLease 构造；如果没有这一行，Python 语法不完整。
# 新增代码+UniversalTargetLease：函数段结束，build_target_lease 到此结束；如果没有这个边界说明，用户不容易看出租约构建范围。


def target_lease_from_dict(report: dict[str, Any]) -> TargetLease:  # 新增代码+UniversalTargetLease：函数段开始，从报告恢复租约对象；如果没有这段函数，controller 需要重复写易错转换逻辑。
    safe_report = _safe_dict(report)  # 新增代码+UniversalTargetLease：复制报告字典；如果没有这一行，坏输入可能污染恢复流程。
    return TargetLease(  # 新增代码+UniversalTargetLease：返回恢复出的租约；如果没有这一行，动作前验证无法吃 registry 报告。
        session_id=_safe_text(safe_report.get("session_id")) or "learning-agent-default-session",  # 新增代码+UniversalTargetLease：恢复会话 id；如果没有这一行，租约归属会丢失。
        target_ref=_safe_text(safe_report.get("target_ref")),  # 新增代码+UniversalTargetLease：恢复 target_ref；如果没有这一行，报告无法关联目标。
        origin=_safe_text(safe_report.get("origin")) or "unknown",  # 新增代码+UniversalTargetLease：恢复来源；如果没有这一行，授权策略无法执行。
        created_at=float(safe_report.get("created_at", 0.0) or 0.0),  # 新增代码+UniversalTargetLease：恢复创建时间；如果没有这一行，新旧租约不可审计。
        target_window=_safe_dict(safe_report.get("target_window")),  # 新增代码+UniversalTargetLease：恢复目标窗口；如果没有这一行，动作前没有期望窗口。
        owned_target_identity=_safe_dict(safe_report.get("owned_target_identity")),  # 新增代码+UniversalTargetLease：恢复身份报告；如果没有这一行，漂移验证缺少进程事实。
        user_granted_existing_window=bool(safe_report.get("user_granted_existing_window", False)),  # 新增代码+UniversalTargetLease：恢复用户授权状态；如果没有这一行，已有窗口可能被误放行。
        lease_identity_verified=bool(safe_report.get("lease_identity_verified", False)),  # 新增代码+UniversalTargetLease：恢复首次验证状态；如果没有这一行，坏租约可能继续动作。
        title_sha256_16=_safe_text(safe_report.get("title_sha256_16")),  # 新增代码+UniversalTargetLease：恢复标题哈希；如果没有这一行，标题漂移审计丢失。
        low_level_event_count=int(safe_report.get("low_level_event_count", 0) or 0),  # 新增代码+UniversalTargetLease：恢复零事件计数；如果没有这一行，报告字段不完整。
    )  # 新增代码+UniversalTargetLease：结束租约恢复；如果没有这一行，Python 语法不完整。
# 新增代码+UniversalTargetLease：函数段结束，target_lease_from_dict 到此结束；如果没有这个边界说明，用户不容易看出租约恢复范围。


def _launch_result_from_lease(lease: TargetLease) -> dict[str, Any]:  # 新增代码+UniversalTargetLease：函数段开始，从租约报告重建身份验证所需启动字段；如果没有这段函数，动作前无法复用 verify_owned_target_identity。
    process = _safe_dict(lease.owned_target_identity.get("process"))  # 新增代码+UniversalTargetLease：读取进程身份报告；如果没有这一行，pid 和 exe 无法恢复。
    return {  # 新增代码+UniversalTargetLease：返回最小启动报告；如果没有这一行，目标身份验证没有进程输入。
        "process_id": process.get("process_id"),  # 新增代码+UniversalTargetLease：恢复进程 pid；如果没有这一行，pid 漂移无法比较。
        "process_executable": process.get("process_executable"),  # 新增代码+UniversalTargetLease：恢复可执行名；如果没有这一行，进程名漂移无法比较。
        "process_path_sha256_16": process.get("process_path_sha256_16"),  # 新增代码+UniversalTargetLease：恢复路径哈希；如果没有这一行，路径漂移缺少证据。
        "owned_process_registered": True,  # 新增代码+UniversalTargetLease：声明这是已登记自有进程；如果没有这一行，自有租约会被误判为用户旧进程。
        "process_started": True,  # 新增代码+UniversalTargetLease：声明进程已启动；如果没有这一行，身份报告语义不完整。
    }  # 新增代码+UniversalTargetLease：结束启动报告；如果没有这一行，Python 语法不完整。
# 新增代码+UniversalTargetLease：函数段结束，_launch_result_from_lease 到此结束；如果没有这个边界说明，用户不容易看出内部恢复范围。


def _same_existing_window(lease: TargetLease, current_window: dict[str, Any]) -> bool:  # 新增代码+UniversalTargetLease：函数段开始，比较用户授权已有窗口是否仍是同一个；如果没有这段函数，已有窗口授权可能漂移。
    expected_window = _safe_dict(lease.target_window)  # 新增代码+UniversalTargetLease：读取租约窗口；如果没有这一行，比较没有基准。
    current = _safe_dict(current_window)  # 新增代码+UniversalTargetLease：读取当前窗口；如果没有这一行，坏输入可能导致异常。
    return bool(_safe_text(expected_window.get("window_id")) == _safe_text(current.get("window_id")) and _safe_text(expected_window.get("pid")) == _safe_text(current.get("pid")))  # 新增代码+UniversalTargetLease：同时比较 window_id 和 pid；如果没有这一行，同应用不同窗口可能被误放行。
# 新增代码+UniversalTargetLease：函数段结束，_same_existing_window 到此结束；如果没有这个边界说明，用户不容易看出已有窗口比较范围。


def verify_target_lease_before_action(  # 新增代码+UniversalTargetLease：函数段开始，动作前验证租约；如果没有这段函数，SendInput 前没有通用目标门禁。
    *,  # 新增代码+UniversalTargetLease：强制关键字参数；如果没有这一行，调用方可能把租约和窗口传反。
    lease: TargetLease,  # 新增代码+UniversalTargetLease：接收期望租约；如果没有这一行，验证没有安全基准。
    current_window: dict[str, Any],  # 新增代码+UniversalTargetLease：接收当前窗口事实；如果没有这一行，无法发现窗口漂移。
    action: Any,  # 新增代码+UniversalTargetLease：接收动作名；如果没有这一行，无法区分读动作和写动作。
) -> TargetLeaseVerification:  # 新增代码+UniversalTargetLease：声明返回验证结果；如果没有这一行，调用方不知道如何读取结果。
    action_name = _safe_text(action)  # 新增代码+UniversalTargetLease：规范动作名；如果没有这一行，空格或 None 会导致策略不稳定。
    expected = lease.to_dict()  # 新增代码+UniversalTargetLease：保存期望租约报告；如果没有这一行，失败结果缺少基准。
    current = _safe_dict(current_window)  # 新增代码+UniversalTargetLease：复制当前窗口；如果没有这一行，外部修改可能污染验证报告。
    if action_name not in WRITE_ACTIONS_REQUIRING_LEASE:  # 新增代码+UniversalTargetLease：读动作或非写动作不要求租约；如果没有这一行，截图等观察路径会被误拒绝。
        return TargetLeaseVerification(True, "target_lease_not_required", False, 0, expected, current)  # 新增代码+UniversalTargetLease：返回无需租约的允许结果；如果没有这一行，非写动作无法继续。
    if lease.origin == "user_granted_existing_window" and not lease.user_granted_existing_window:  # 新增代码+UniversalTargetLease：检查已有窗口是否缺用户授权；如果没有这一行，full mode 可能默认接管用户旧窗口。
        return TargetLeaseVerification(False, "existing_window_missing_user_grant", True, 0, expected, current)  # 新增代码+UniversalTargetLease：返回已有窗口缺授权拒绝；如果没有这一行，用户不知道需要明确授权。
    if not lease.lease_identity_verified:  # 新增代码+UniversalTargetLease：检查首次租约是否可信；如果没有这一行，坏目标可能进入动作阶段。
        return TargetLeaseVerification(False, "target_lease_not_verified", True, 0, expected, current)  # 新增代码+UniversalTargetLease：返回坏租约拒绝；如果没有这一行，失败原因不可见。
    if lease.origin == "agent_owned_launch":  # 新增代码+UniversalTargetLease：自有启动目标走现有 pid/hwnd/title 身份验证；如果没有这一行，自有目标漂移无法被严格发现。
        owned_identity = build_owned_target_identity(_launch_result_from_lease(lease), lease.target_window)  # 新增代码+UniversalTargetLease：重建自有身份对象；如果没有这一行，verify_owned_target_identity 没有输入对象。
        verification = verify_owned_target_identity(owned_identity, current).to_report()  # 新增代码+UniversalTargetLease：执行现有动作前身份验证；如果没有这一行，漂移逻辑会和已有模型分裂。
        if not bool(verification.get("allowed")):  # 新增代码+UniversalTargetLease：检查是否发生漂移；如果没有这一行，失败结果不会被转换成租约拒绝。
            return TargetLeaseVerification(False, "target_lease_drift_rejected", True, 0, expected, current)  # 新增代码+UniversalTargetLease：返回漂移拒绝且零事件；如果没有这一行，错窗可能继续输入。
    elif not _same_existing_window(lease, current):  # 新增代码+UniversalTargetLease：已有授权窗口必须仍是同一窗口；如果没有这一行，授权可能漂移到同应用其它窗口。
        return TargetLeaseVerification(False, "target_lease_drift_rejected", True, 0, expected, current)  # 新增代码+UniversalTargetLease：返回已有窗口漂移拒绝；如果没有这一行，错窗可能继续输入。
    return TargetLeaseVerification(True, "target_lease_verified", False, 0, expected, current)  # 新增代码+UniversalTargetLease：返回验证通过；如果没有这一行，正常控制路径无法继续。
# 新增代码+UniversalTargetLease：函数段结束，verify_target_lease_before_action 到此结束；如果没有这个边界说明，用户不容易看出动作前门禁范围。
