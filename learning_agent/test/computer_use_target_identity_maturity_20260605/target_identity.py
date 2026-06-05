"""Computer Use full 模式的目标身份绑定模型。"""  # 新增代码+TargetIdentityMaturity：说明本模块只负责把本次启动的进程和窗口绑定成可验证目标；如果没有这一行，用户不容易区分身份校验和真实桌面控制。
from __future__ import annotations  # 新增代码+TargetIdentityMaturity：启用延迟类型注解解析；如果没有这一行，互相引用的 dataclass 类型在旧路径下更容易导入失败。

import hashlib  # 新增代码+TargetIdentityMaturity：用于把进程路径和窗口标题转成短哈希；如果没有这一行，身份校验只能保存原始敏感文本。
import json  # 新增代码+TargetIdentityMaturity：用于命令行自检输出完整 JSON；如果没有这一行，失败排查只能依赖短 token。
from dataclasses import dataclass  # 新增代码+TargetIdentityMaturity：用 dataclass 表达不可变身份记录；如果没有这一行，代码会变成大量手写样板。
from typing import Any  # 新增代码+TargetIdentityMaturity：描述来自 Win32、测试和上游报告的动态字典；如果没有这一行，接口输入类型不清楚。

PHASE111_TARGET_IDENTITY_MARKER = "PHASE111_TARGET_IDENTITY_READY"  # 新增代码+TargetIdentityMaturity：定义 Task 3 ready marker；如果没有这一行，终端验收不容易稳定定位目标身份输出。
PHASE111_TARGET_IDENTITY_OK_TOKEN = "PHASE111_TARGET_IDENTITY_OK"  # 新增代码+TargetIdentityMaturity：定义 Task 3 成功 token；如果没有这一行，脚本和人工验收难以区分通过与普通输出。
PHASE111_TARGET_IDENTITY_MODEL = "phase111_target_identity_binding"  # 新增代码+TargetIdentityMaturity：定义报告模型名；如果没有这一行，最终成熟矩阵无法区分本任务和旧阶段。
PHASE111_TITLE_PREVIEW_LIMIT = 80  # 新增代码+TargetIdentityMaturity：限制窗口标题摘要长度；如果没有这一行，长标题可能污染日志和模型上下文。
PHASE111_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+TargetIdentityMaturity：声明本模块没有扩大动作权限；如果没有这一行，用户可能误以为身份绑定已经放开任意控制。


# 新增代码+TargetIdentityMaturity：函数段落开始，_phase111_bool_token 用于把布尔值输出成稳定小写 token；如果没有这个函数，CLI 文本可能因为 True/False 大小写漂移而不好验收。
def _phase111_bool_token(value: Any) -> str:  # 新增代码+TargetIdentityMaturity：定义布尔格式化 helper；如果没有这一行，多个 CLI 字段会重复写格式化逻辑。
    return "true" if bool(value) else "false"  # 新增代码+TargetIdentityMaturity：返回 true 或 false 文本；如果没有这一行，终端验收无法稳定匹配布尔结果。
# 新增代码+TargetIdentityMaturity：函数段落结束，_phase111_bool_token 到此结束；如果没有这个边界说明，用户不容易看出布尔 token helper 的范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，_phase111_safe_int 用于安全读取 pid 和 hwnd；如果没有这个函数，坏输入会让身份模块直接异常退出。
def _phase111_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+TargetIdentityMaturity：定义容错整数转换；如果没有这一行，字符串 pid/hwnd 不能稳定参与校验。
    try:  # 新增代码+TargetIdentityMaturity：尝试把输入转成 int；如果没有这一行，转换失败无法被优雅处理。
        return int(value)  # 新增代码+TargetIdentityMaturity：返回转换后的整数；如果没有这一行，调用方拿不到可比较的 pid/hwnd。
    except (TypeError, ValueError):  # 新增代码+TargetIdentityMaturity：捕获 None、空串和非数字文本；如果没有这一行，坏字段会中断整个 full 模式流程。
        return default  # 新增代码+TargetIdentityMaturity：失败时返回默认值兜底；如果没有这一行，后续无法用 0 表示缺失身份。
# 新增代码+TargetIdentityMaturity：函数段落结束，_phase111_safe_int 到此结束；如果没有这个边界说明，用户不容易看出容错转换范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，_phase111_text 用于把任意字段变成干净短文本；如果没有这个函数，None 或超长文本会污染报告。
def _phase111_text(value: Any, *, limit: int = 240) -> str:  # 新增代码+TargetIdentityMaturity：定义安全文本清理 helper；如果没有这一行，进程名和标题清理会重复散落。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+TargetIdentityMaturity：去掉换行和首尾空白；如果没有这一行，日志 token 可能被换行切碎。
    return text[:limit]  # 新增代码+TargetIdentityMaturity：限制最大长度后返回；如果没有这一行，异常长字段会撑大上下文。
# 新增代码+TargetIdentityMaturity：函数段落结束，_phase111_text 到此结束；如果没有这个边界说明，用户不容易看出文本清理范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，phase111_sha256_16 用于生成短哈希；如果没有这个函数，路径和标题只能原文比对或泄露到报告。
def phase111_sha256_16(value: Any) -> str:  # 新增代码+TargetIdentityMaturity：定义 16 位 sha256 前缀 helper；如果没有这一行，脱敏字段格式无法统一。
    text = _phase111_text(value, limit=1000).lower()  # 新增代码+TargetIdentityMaturity：清理并转小写以便稳定比对；如果没有这一行，路径大小写差异会造成假漂移。
    if not text:  # 新增代码+TargetIdentityMaturity：检查空输入；如果没有这一行，空值也会生成没有意义的哈希。
        return ""  # 新增代码+TargetIdentityMaturity：空输入返回空哈希；如果没有这一行，未知路径和真实路径无法区分。
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]  # 新增代码+TargetIdentityMaturity：返回 sha256 前 16 位；如果没有这一行，身份记录缺少可审计脱敏指纹。
# 新增代码+TargetIdentityMaturity：函数段落结束，phase111_sha256_16 到此结束；如果没有这个边界说明，用户不容易看出哈希生成范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，summarize_window_title 用于限制窗口标题可见摘要；如果没有这个函数，长标题或敏感标题会原样塞进身份报告。
def summarize_window_title(title: Any, *, limit: int = PHASE111_TITLE_PREVIEW_LIMIT) -> str:  # 新增代码+TargetIdentityMaturity：定义标题摘要 helper；如果没有这一行，窗口标题摘要没有统一入口。
    clean_title = _phase111_text(title, limit=1000)  # 新增代码+TargetIdentityMaturity：清理原始标题；如果没有这一行，标题里的换行可能破坏日志结构。
    if len(clean_title) <= limit:  # 新增代码+TargetIdentityMaturity：短标题直接保留可见摘要；如果没有这一行，所有标题都会被无意义截断。
        return clean_title  # 新增代码+TargetIdentityMaturity：返回短标题摘要；如果没有这一行，用户看不到可识别窗口名。
    return clean_title[: max(0, limit - 3)] + "..."  # 新增代码+TargetIdentityMaturity：长标题截断并加省略点；如果没有这一行，超长标题会进入上下文。
# 新增代码+TargetIdentityMaturity：函数段落结束，summarize_window_title 到此结束；如果没有这个边界说明，用户不容易看出标题摘要范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，window_title_sha256_16 用于稳定比对完整标题；如果没有这个函数，摘要相同但完整标题不同的窗口漂移不容易发现。
def window_title_sha256_16(title: Any) -> str:  # 新增代码+TargetIdentityMaturity：定义窗口标题哈希 helper；如果没有这一行，windows_backend 不能复用同一标题哈希规则。
    return phase111_sha256_16(title)  # 新增代码+TargetIdentityMaturity：复用统一短哈希；如果没有这一行，标题哈希和路径哈希规则会分裂。
# 新增代码+TargetIdentityMaturity：函数段落结束，window_title_sha256_16 到此结束；如果没有这个边界说明，用户不容易看出标题哈希范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，normalize_executable_name 用于比较应用身份；如果没有这个函数，Obsidian 和 Obsidian.exe 这类写法会误判不同。
def normalize_executable_name(value: Any) -> str:  # 新增代码+TargetIdentityMaturity：定义可执行名归一化 helper；如果没有这一行，进程名比较会到处重复。
    text = _phase111_text(value, limit=260).replace("\\", "/").strip("\"'` ").lower()  # 新增代码+TargetIdentityMaturity：清理路径分隔符、引号和大小写；如果没有这一行，路径式可执行名难以比较。
    leaf = text.rsplit("/", 1)[-1] if "/" in text else text  # 新增代码+TargetIdentityMaturity：只取最后文件名；如果没有这一行，完整路径会进入可执行名字段造成泄露风险。
    return leaf[:-4] if leaf.endswith(".exe") else leaf  # 新增代码+TargetIdentityMaturity：去掉 .exe 后缀便于比较；如果没有这一行，同一程序的两种写法会被误判。
# 新增代码+TargetIdentityMaturity：函数段落结束，normalize_executable_name 到此结束；如果没有这个边界说明，用户不容易看出可执行名归一化范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，_phase111_hash_from_source 用于读取已有哈希或生成新哈希；如果没有这个函数，不同上游字段会导致路径脱敏规则不一致。
def _phase111_hash_from_source(source: dict[str, Any], raw_key: str, hash_key: str) -> str:  # 新增代码+TargetIdentityMaturity：定义哈希字段读取 helper；如果没有这一行，窗口和进程身份会重复处理路径字段。
    existing_hash = _phase111_text(source.get(hash_key, ""), limit=64)  # 新增代码+TargetIdentityMaturity：读取上游已脱敏哈希；如果没有这一行，windows_backend 传来的哈希会被丢掉。
    if len(existing_hash) == 16 and all(character in "0123456789abcdef" for character in existing_hash.lower()):  # 新增代码+TargetIdentityMaturity：确认已有字段像 16 位十六进制哈希；如果没有这一行，普通文本可能冒充哈希。
        return existing_hash.lower()  # 新增代码+TargetIdentityMaturity：返回规范小写哈希；如果没有这一行，同一哈希大小写不同会误判漂移。
    return phase111_sha256_16(source.get(raw_key, ""))  # 新增代码+TargetIdentityMaturity：没有可信哈希时从原始字段生成；如果没有这一行，路径身份会丢失。
# 新增代码+TargetIdentityMaturity：函数段落结束，_phase111_hash_from_source 到此结束；如果没有这个边界说明，用户不容易看出哈希来源规则。


# 新增代码+TargetIdentityMaturity：类段落开始，ProcessIdentity 保存本次 agent 自己启动的进程身份；如果没有这个类，后续无法区分本次进程和用户已有进程。
@dataclass(frozen=True)  # 新增代码+TargetIdentityMaturity：让进程身份不可变；如果没有这一行，验证期间 pid 或哈希可能被误改。
class ProcessIdentity:  # 新增代码+TargetIdentityMaturity：定义进程身份结构；如果没有这一行，目标身份缺少进程侧基准。
    process_id: int  # 新增代码+TargetIdentityMaturity：保存进程 pid；如果没有这一行，窗口所属进程无法和启动结果绑定。
    process_executable: str  # 新增代码+TargetIdentityMaturity：保存脱路径后的可执行名；如果没有这一行，无法确认窗口进程和启动目标一致。
    process_path_sha256_16: str  # 新增代码+TargetIdentityMaturity：保存进程路径短哈希；如果没有这一行，路径只能明文保存或无法比对。
    owned_process_registered: bool  # 新增代码+TargetIdentityMaturity：保存进程是否登记为本 agent 自有；如果没有这一行，用户已有窗口可能被误认成自有目标。
    # 新增代码+TargetIdentityMaturity：函数段落开始，to_report 把进程身份转成安全字典；如果没有这个函数，上层报告可能直接暴露 dataclass 内部形态。
    def to_report(self) -> dict[str, Any]:  # 新增代码+TargetIdentityMaturity：定义进程身份报告接口；如果没有这一行，CLI 和矩阵无法读取稳定字段。
        return {"process_id": self.process_id, "process_executable": self.process_executable, "process_path_sha256_16": self.process_path_sha256_16, "owned_process_registered": self.owned_process_registered}  # 新增代码+TargetIdentityMaturity：返回不含原始路径的进程报告；如果没有这一行，隐私和审计字段会混在一起。
    # 新增代码+TargetIdentityMaturity：函数段落结束，ProcessIdentity.to_report 到此结束；如果没有这个边界说明，用户不容易看出进程报告范围。
# 新增代码+TargetIdentityMaturity：类段落结束，ProcessIdentity 到此结束；如果没有这个边界说明，用户不容易看出进程身份结构范围。


# 新增代码+TargetIdentityMaturity：类段落开始，WindowIdentity 保存窗口侧身份；如果没有这个类，pid、hwnd 和标题哈希无法作为一个整体校验。
@dataclass(frozen=True)  # 新增代码+TargetIdentityMaturity：让窗口身份不可变；如果没有这一行，校验前后的窗口字段可能被误改。
class WindowIdentity:  # 新增代码+TargetIdentityMaturity：定义窗口身份结构；如果没有这一行，目标身份缺少窗口侧基准。
    window_id: str  # 新增代码+TargetIdentityMaturity：保存协议窗口 id；如果没有这一行，上层无法引用该窗口。
    hwnd: int  # 新增代码+TargetIdentityMaturity：保存 Windows 窗口句柄；如果没有这一行，pid 到 hwnd 的绑定无法证明。
    window_process_id: int  # 新增代码+TargetIdentityMaturity：保存窗口所属 pid；如果没有这一行，同标题不同进程会混淆。
    process_name: str  # 新增代码+TargetIdentityMaturity：保存窗口进程名摘要；如果没有这一行，启动目标和窗口进程无法交叉验证。
    title_preview: str  # 新增代码+TargetIdentityMaturity：保存受限标题摘要；如果没有这一行，用户无法识别目标窗口。
    title_sha256_16: str  # 新增代码+TargetIdentityMaturity：保存完整标题短哈希；如果没有这一行，标题漂移无法安全比对。
    process_path_sha256_16: str  # 新增代码+TargetIdentityMaturity：保存窗口进程路径短哈希；如果没有这一行，窗口路径身份无法脱敏比对。
    # 新增代码+TargetIdentityMaturity：函数段落开始，to_report 把窗口身份转成安全字典；如果没有这个函数，调用方可能误拿原始窗口字段。
    def to_report(self) -> dict[str, Any]:  # 新增代码+TargetIdentityMaturity：定义窗口身份报告接口；如果没有这一行，CLI 和矩阵无法读取稳定字段。
        return {"window_id": self.window_id, "hwnd": self.hwnd, "window_process_id": self.window_process_id, "process_name": self.process_name, "title_preview": self.title_preview, "title_sha256_16": self.title_sha256_16, "process_path_sha256_16": self.process_path_sha256_16}  # 新增代码+TargetIdentityMaturity：返回不含原始标题和路径的窗口报告；如果没有这一行，隐私字段可能进入模型上下文。
    # 新增代码+TargetIdentityMaturity：函数段落结束，WindowIdentity.to_report 到此结束；如果没有这个边界说明，用户不容易看出窗口报告范围。
# 新增代码+TargetIdentityMaturity：类段落结束，WindowIdentity 到此结束；如果没有这个边界说明，用户不容易看出窗口身份结构范围。


# 新增代码+TargetIdentityMaturity：类段落开始，OwnedTargetIdentity 表示一个本 agent 拥有且可验证的目标；如果没有这个类，进程和窗口只能分散存在，无法形成动作前门禁。
@dataclass(frozen=True)  # 新增代码+TargetIdentityMaturity：让自有目标身份不可变；如果没有这一行，动作前后目标身份可能被误改。
class OwnedTargetIdentity:  # 新增代码+TargetIdentityMaturity：定义自有目标身份结构；如果没有这一行，full 模式没有统一目标凭证。
    process: ProcessIdentity  # 新增代码+TargetIdentityMaturity：保存进程身份；如果没有这一行，目标身份缺少 pid 基准。
    window: WindowIdentity  # 新增代码+TargetIdentityMaturity：保存窗口身份；如果没有这一行，目标身份缺少 hwnd 基准。
    process_identity_verified: bool  # 新增代码+TargetIdentityMaturity：保存进程校验结果；如果没有这一行，上层不知道是否可信任进程。
    window_identity_verified: bool  # 新增代码+TargetIdentityMaturity：保存窗口校验结果；如果没有这一行，上层不知道是否可信任窗口。
    target_identity_verified: bool  # 新增代码+TargetIdentityMaturity：保存最终目标校验结果；如果没有这一行，上层没有明确放行信号。
    target_drift_blocks_action: bool  # 新增代码+TargetIdentityMaturity：保存是否因漂移阻断动作；如果没有这一行，漂移拒绝和普通拒绝难以区分。
    user_preexisting_window_preserved: bool  # 新增代码+TargetIdentityMaturity：保存是否保护了用户已有窗口；如果没有这一行，拒绝用户窗口的原因不可见。
    decision: str  # 新增代码+TargetIdentityMaturity：保存稳定决策 token；如果没有这一行，终端和矩阵无法解释结果。
    # 新增代码+TargetIdentityMaturity：函数段落开始，to_report 生成安全目标报告；如果没有这个函数，上层可能直接序列化不适合公开的对象。
    def to_report(self) -> dict[str, Any]:  # 新增代码+TargetIdentityMaturity：定义自有目标报告接口；如果没有这一行，CLI 和矩阵无法读取稳定字段。
        return {"process": self.process.to_report(), "window": self.window.to_report(), "process_identity_verified": self.process_identity_verified, "window_identity_verified": self.window_identity_verified, "target_identity_verified": self.target_identity_verified, "target_drift_blocks_action": self.target_drift_blocks_action, "user_preexisting_window_preserved": self.user_preexisting_window_preserved, "decision": self.decision}  # 新增代码+TargetIdentityMaturity：返回不含原始路径和完整标题的目标报告；如果没有这一行，安全报告无法统一。
    # 新增代码+TargetIdentityMaturity：函数段落结束，OwnedTargetIdentity.to_report 到此结束；如果没有这个边界说明，用户不容易看出目标报告范围。
# 新增代码+TargetIdentityMaturity：类段落结束，OwnedTargetIdentity 到此结束；如果没有这个边界说明，用户不容易看出自有目标结构范围。


# 新增代码+TargetIdentityMaturity：类段落开始，TargetIdentityVerification 表示动作前的再次校验结果；如果没有这个类，目标漂移只能靠布尔值粗略表达。
@dataclass(frozen=True)  # 新增代码+TargetIdentityMaturity：让验证结果不可变；如果没有这一行，动作门禁结果可能被后续逻辑误改。
class TargetIdentityVerification:  # 新增代码+TargetIdentityMaturity：定义目标验证结果结构；如果没有这一行，动作循环没有结构化门禁结果。
    allowed: bool  # 新增代码+TargetIdentityMaturity：保存是否允许动作；如果没有这一行，上层无法直接决定是否继续。
    decision: str  # 新增代码+TargetIdentityMaturity：保存稳定决策 token；如果没有这一行，失败原因无法稳定解析。
    process_identity_verified: bool  # 新增代码+TargetIdentityMaturity：保存进程校验结果；如果没有这一行，验证报告缺少进程侧事实。
    window_identity_verified: bool  # 新增代码+TargetIdentityMaturity：保存窗口校验结果；如果没有这一行，验证报告缺少窗口侧事实。
    target_identity_verified: bool  # 新增代码+TargetIdentityMaturity：保存目标校验结果；如果没有这一行，验证报告缺少最终事实。
    target_drift_blocks_action: bool  # 新增代码+TargetIdentityMaturity：保存漂移是否阻断动作；如果没有这一行，动作循环不能安全停止。
    user_preexisting_window_preserved: bool  # 新增代码+TargetIdentityMaturity：保存是否保护用户已有窗口；如果没有这一行，用户窗口保护不可审计。
    expected: dict[str, Any]  # 新增代码+TargetIdentityMaturity：保存期望身份摘要；如果没有这一行，失败排查看不到原目标。
    current: dict[str, Any]  # 新增代码+TargetIdentityMaturity：保存当前身份摘要；如果没有这一行，失败排查看不到漂移到哪里。
    # 新增代码+TargetIdentityMaturity：函数段落开始，to_report 生成验证报告；如果没有这个函数，上层无法稳定输出动作前门禁事实。
    def to_report(self) -> dict[str, Any]:  # 新增代码+TargetIdentityMaturity：定义验证报告接口；如果没有这一行，CLI 和矩阵无法读取验证字段。
        return {"allowed": self.allowed, "decision": self.decision, "process_identity_verified": self.process_identity_verified, "window_identity_verified": self.window_identity_verified, "target_identity_verified": self.target_identity_verified, "target_drift_blocks_action": self.target_drift_blocks_action, "user_preexisting_window_preserved": self.user_preexisting_window_preserved, "expected": self.expected, "current": self.current}  # 新增代码+TargetIdentityMaturity：返回完整但脱敏的验证报告；如果没有这一行，漂移调试会缺少证据。
    # 新增代码+TargetIdentityMaturity：函数段落结束，TargetIdentityVerification.to_report 到此结束；如果没有这个边界说明，用户不容易看出验证报告范围。
# 新增代码+TargetIdentityMaturity：类段落结束，TargetIdentityVerification 到此结束；如果没有这个边界说明，用户不容易看出动作前验证结构范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，build_process_identity 从启动结果构造进程身份；如果没有这个函数，Phase110 启动报告不能进入目标绑定。
def build_process_identity(launch_result: dict[str, Any]) -> ProcessIdentity:  # 新增代码+TargetIdentityMaturity：定义进程身份构造入口；如果没有这一行，上游启动报告没有标准转换点。
    process_id = _phase111_safe_int(launch_result.get("process_id"))  # 新增代码+TargetIdentityMaturity：读取进程 pid；如果没有这一行，进程窗口绑定没有数字基准。
    executable = _phase111_text(launch_result.get("process_executable", launch_result.get("executable", "")), limit=260)  # 新增代码+TargetIdentityMaturity：读取可执行名；如果没有这一行，目标应用身份无法比较。
    process_path_hash = _phase111_hash_from_source(launch_result, "process_path", "process_path_sha256_16")  # 新增代码+TargetIdentityMaturity：生成或复用路径哈希；如果没有这一行，路径身份无法脱敏保留。
    if not process_path_hash and executable:  # 新增代码+TargetIdentityMaturity：检查是否需要用可执行名兜底生成身份哈希；如果没有这一行，记录型后端缺路径时会完全没有路径指纹。
        process_path_hash = phase111_sha256_16(executable)  # 新增代码+TargetIdentityMaturity：用可执行名生成兜底哈希；如果没有这一行，测试后端缺路径会影响身份报告完整性。
    owned = bool(launch_result.get("owned_process_registered", launch_result.get("cleanup_registered", False)))  # 新增代码+TargetIdentityMaturity：读取本进程是否由 agent 登记拥有；如果没有这一行，用户已有进程可能被误接管。
    return ProcessIdentity(process_id=process_id, process_executable=normalize_executable_name(executable), process_path_sha256_16=process_path_hash, owned_process_registered=owned)  # 新增代码+TargetIdentityMaturity：返回脱敏进程身份；如果没有这一行，上层拿不到进程身份对象。
# 新增代码+TargetIdentityMaturity：函数段落结束，build_process_identity 到此结束；如果没有这个边界说明，用户不容易看出进程身份构造范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，_window_id_hwnd 用于从窗口记录提取 hwnd；如果没有这个函数，hwnd 字段和 hwnd:xxx 字符串会分散处理。
def _window_id_hwnd(window_id: str) -> int:  # 新增代码+TargetIdentityMaturity：定义从 window_id 提取 hwnd 的 helper；如果没有这一行，窗口句柄解析会重复。
    return _phase111_safe_int(window_id.split(":", 1)[1]) if window_id.lower().startswith("hwnd:") and ":" in window_id else 0  # 新增代码+TargetIdentityMaturity：解析 hwnd:123 形式；如果没有这一行，只有 window_id 没有 hwnd 的记录无法绑定句柄。
# 新增代码+TargetIdentityMaturity：函数段落结束，_window_id_hwnd 到此结束；如果没有这个边界说明，用户不容易看出 hwnd 解析范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，build_window_identity 从窗口记录构造窗口身份；如果没有这个函数，windows_backend 和 Phase109 的窗口字段无法统一。
def build_window_identity(window: dict[str, Any]) -> WindowIdentity:  # 新增代码+TargetIdentityMaturity：定义窗口身份构造入口；如果没有这一行，上游窗口记录没有标准转换点。
    raw_window_id = _phase111_text(window.get("window_id", ""), limit=120)  # 新增代码+TargetIdentityMaturity：读取协议窗口 id；如果没有这一行，窗口引用会丢失。
    hwnd = _phase111_safe_int(window.get("hwnd", window.get("window_handle", 0))) or _window_id_hwnd(raw_window_id)  # 新增代码+TargetIdentityMaturity：读取或解析 hwnd；如果没有这一行，pid 到 hwnd 的绑定无法落地。
    window_id = raw_window_id or (f"hwnd:{hwnd}" if hwnd else "")  # 新增代码+TargetIdentityMaturity：缺 window_id 时用 hwnd 兜底；如果没有这一行，只有 hwnd 的真实窗口无法被引用。
    window_pid = _phase111_safe_int(window.get("window_process_id", window.get("pid", window.get("process_id", 0))))  # 新增代码+TargetIdentityMaturity：读取窗口所属 pid；如果没有这一行，同标题不同进程无法区分。
    process_name = _phase111_text(window.get("process_name", window.get("window_executable", window.get("app_id", ""))), limit=260)  # 新增代码+TargetIdentityMaturity：读取窗口进程名；如果没有这一行，窗口进程无法和启动进程交叉验证。
    raw_title = window.get("title_preview", window.get("title", ""))  # 新增代码+TargetIdentityMaturity：读取可见标题或原始标题；如果没有这一行，窗口标题漂移没有输入。
    title_preview = summarize_window_title(raw_title)  # 新增代码+TargetIdentityMaturity：生成受限标题摘要；如果没有这一行，长标题可能进入报告。
    title_hash = window.get("title_sha256_16") or window_title_sha256_16(raw_title)  # 新增代码+TargetIdentityMaturity：读取或生成完整标题哈希；如果没有这一行，摘要相同的漂移不容易发现。
    path_hash = _phase111_hash_from_source(window, "process_path", "process_path_sha256_16") or _phase111_text(window.get("process_path_hash", ""), limit=64)  # 新增代码+TargetIdentityMaturity：读取窗口路径哈希；如果没有这一行，窗口路径身份无法脱敏比对。
    return WindowIdentity(window_id=window_id, hwnd=hwnd, window_process_id=window_pid, process_name=normalize_executable_name(process_name), title_preview=title_preview, title_sha256_16=_phase111_text(title_hash, limit=16), process_path_sha256_16=path_hash[:16])  # 新增代码+TargetIdentityMaturity：返回脱敏窗口身份；如果没有这一行，上层拿不到窗口身份对象。
# 新增代码+TargetIdentityMaturity：函数段落结束，build_window_identity 到此结束；如果没有这个边界说明，用户不容易看出窗口身份构造范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，_phase111_identity_decision 计算首次绑定是否可信；如果没有这个函数，构建身份时的拒绝原因会分散到各处。
def _phase111_identity_decision(process: ProcessIdentity, window: WindowIdentity) -> tuple[bool, bool, bool, bool, bool, str]:  # 新增代码+TargetIdentityMaturity：定义首次绑定决策 helper；如果没有这一行，返回字段顺序和含义无法集中维护。
    process_verified = bool(process.process_id > 0 and process.owned_process_registered)  # 新增代码+TargetIdentityMaturity：确认进程有 pid 且登记为自有；如果没有这一行，用户已有进程可能被误放行。
    window_verified = bool(window.hwnd > 0 and window.window_process_id == process.process_id)  # 新增代码+TargetIdentityMaturity：确认窗口有 hwnd 且 pid 对上；如果没有这一行，目标窗口可能错绑。
    executable_verified = bool(not process.process_executable or not window.process_name or process.process_executable == window.process_name)  # 新增代码+TargetIdentityMaturity：确认可执行名兼容；如果没有这一行，错误应用可能借同 pid 测试数据通过。
    target_verified = bool(process_verified and window_verified and executable_verified)  # 新增代码+TargetIdentityMaturity：合并最终目标身份结果；如果没有这一行，上层没有单一放行字段。
    preexisting_preserved = bool(not process.owned_process_registered)  # 新增代码+TargetIdentityMaturity：未登记进程视为用户已有资源；如果没有这一行，报告无法说明保护了用户窗口。
    decision = "target_identity_verified" if target_verified else "target_identity_not_verified"  # 新增代码+TargetIdentityMaturity：准备默认决策 token；如果没有这一行，失败原因可能为空。
    if not process.owned_process_registered:  # 新增代码+TargetIdentityMaturity：优先检查自有进程登记；如果没有这一行，用户已有窗口可能走到普通 pid 错误。
        decision = "owned_process_not_registered"  # 新增代码+TargetIdentityMaturity：标记未拥有进程拒绝；如果没有这一行，上层无法给用户解释为什么保护已有窗口。
    elif process.process_id <= 0:  # 新增代码+TargetIdentityMaturity：检查 pid 缺失；如果没有这一行，0 pid 的坏数据会得到笼统拒绝。
        decision = "missing_process_identity"  # 新增代码+TargetIdentityMaturity：标记缺进程身份；如果没有这一行，排查启动后端问题会困难。
    elif window.hwnd <= 0:  # 新增代码+TargetIdentityMaturity：检查 hwnd 缺失；如果没有这一行，不能证明 pid 绑定到具体窗口。
        decision = "missing_window_handle"  # 新增代码+TargetIdentityMaturity：标记缺窗口句柄；如果没有这一行，窗口绑定失败原因不清楚。
    elif window.window_process_id != process.process_id:  # 新增代码+TargetIdentityMaturity：检查窗口 pid 是否匹配启动 pid；如果没有这一行，同标题不同进程可能通过。
        decision = "window_process_mismatch"  # 新增代码+TargetIdentityMaturity：标记窗口进程不匹配；如果没有这一行，错绑窗口难以解释。
    elif not executable_verified:  # 新增代码+TargetIdentityMaturity：检查进程名是否不兼容；如果没有这一行，错误应用可能被当成目标。
        decision = "process_name_mismatch"  # 新增代码+TargetIdentityMaturity：标记进程名不匹配；如果没有这一行，进程名漂移原因不可见。
    return process_verified, window_verified, target_verified, False, preexisting_preserved, decision  # 新增代码+TargetIdentityMaturity：返回首次绑定结果；如果没有这一行，构建函数拿不到统一判断。
# 新增代码+TargetIdentityMaturity：函数段落结束，_phase111_identity_decision 到此结束；如果没有这个边界说明，用户不容易看出首次绑定决策范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，build_owned_target_identity 把启动结果和窗口记录绑定成自有目标；如果没有这个函数，full 模式没有进入动作循环前的目标凭证。
def build_owned_target_identity(launch_result: dict[str, Any], window: dict[str, Any]) -> OwnedTargetIdentity:  # 新增代码+TargetIdentityMaturity：定义自有目标构建入口；如果没有这一行，上层不能生成目标身份。
    process = build_process_identity(launch_result)  # 新增代码+TargetIdentityMaturity：构建进程身份；如果没有这一行，目标身份缺少进程侧事实。
    window_identity = build_window_identity(window)  # 新增代码+TargetIdentityMaturity：构建窗口身份；如果没有这一行，目标身份缺少窗口侧事实。
    process_verified, window_verified, target_verified, drift_blocks, preexisting_preserved, decision = _phase111_identity_decision(process, window_identity)  # 新增代码+TargetIdentityMaturity：计算首次绑定结果；如果没有这一行，目标身份没有统一判定。
    return OwnedTargetIdentity(process=process, window=window_identity, process_identity_verified=process_verified, window_identity_verified=window_verified, target_identity_verified=target_verified, target_drift_blocks_action=drift_blocks, user_preexisting_window_preserved=preexisting_preserved, decision=decision)  # 新增代码+TargetIdentityMaturity：返回自有目标身份；如果没有这一行，上层拿不到可验证凭证。
# 新增代码+TargetIdentityMaturity：函数段落结束，build_owned_target_identity 到此结束；如果没有这个边界说明，用户不容易看出目标构建范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，verify_owned_target_identity 用于动作前重新验证目标是否仍然相同；如果没有这个函数，窗口漂移后 agent 可能继续动作。
def verify_owned_target_identity(owned: OwnedTargetIdentity, current_window: dict[str, Any]) -> TargetIdentityVerification:  # 新增代码+TargetIdentityMaturity：定义动作前目标验证入口；如果没有这一行，上层无法调用漂移门禁。
    current = build_window_identity(current_window)  # 新增代码+TargetIdentityMaturity：构建当前窗口身份；如果没有这一行，验证没有当前事实。
    expected_report = owned.to_report()  # 新增代码+TargetIdentityMaturity：保存期望目标摘要；如果没有这一行，失败报告看不到原始目标。
    current_report = current.to_report()  # 新增代码+TargetIdentityMaturity：保存当前窗口摘要；如果没有这一行，失败报告看不到漂移目标。
    if not owned.target_identity_verified:  # 新增代码+TargetIdentityMaturity：未通过首次绑定时禁止动作；如果没有这一行，坏目标可能绕过构建失败继续执行。
        return TargetIdentityVerification(allowed=False, decision=owned.decision, process_identity_verified=owned.process_identity_verified, window_identity_verified=owned.window_identity_verified, target_identity_verified=False, target_drift_blocks_action=owned.target_drift_blocks_action, user_preexisting_window_preserved=owned.user_preexisting_window_preserved, expected=expected_report, current=current_report)  # 新增代码+TargetIdentityMaturity：返回首次绑定失败结果；如果没有这一行，上层看不到拒绝原因。
    pid_same = current.window_process_id == owned.process.process_id  # 新增代码+TargetIdentityMaturity：比较当前窗口 pid 是否仍是自有进程；如果没有这一行，同标题不同进程可能被放行。
    hwnd_same = current.hwnd == owned.window.hwnd  # 新增代码+TargetIdentityMaturity：比较当前 hwnd 是否仍是原窗口；如果没有这一行，窗口切换不会被发现。
    window_id_same = current.window_id == owned.window.window_id  # 新增代码+TargetIdentityMaturity：比较协议 window_id 是否仍一致；如果没有这一行，句柄字符串漂移不容易发现。
    title_same = current.title_sha256_16 == owned.window.title_sha256_16  # 新增代码+TargetIdentityMaturity：比较完整标题哈希是否仍一致；如果没有这一行，标题漂移可能继续动作。
    path_same = bool(not current.process_path_sha256_16 or not owned.window.process_path_sha256_16 or current.process_path_sha256_16 == owned.window.process_path_sha256_16)  # 新增代码+TargetIdentityMaturity：在双方都有路径哈希时比较路径；如果没有这一行，路径换进程不容易发现。
    allowed = bool(pid_same and hwnd_same and window_id_same and title_same and path_same)  # 新增代码+TargetIdentityMaturity：合并动作前放行条件；如果没有这一行，上层没有单一 allowed 结果。
    preexisting_preserved = bool(not pid_same and current.process_name == owned.process.process_executable)  # 新增代码+TargetIdentityMaturity：同应用不同 pid 视为用户已有窗口保护；如果没有这一行，保护原因不会出现在报告里。
    decision = "target_identity_verified" if allowed else "target_drift_blocks_action"  # 新增代码+TargetIdentityMaturity：生成稳定决策 token；如果没有这一行，漂移拒绝原因不统一。
    return TargetIdentityVerification(allowed=allowed, decision=decision, process_identity_verified=owned.process_identity_verified, window_identity_verified=allowed, target_identity_verified=allowed, target_drift_blocks_action=not allowed, user_preexisting_window_preserved=preexisting_preserved, expected=expected_report, current=current_report)  # 新增代码+TargetIdentityMaturity：返回动作前验证结果；如果没有这一行，动作循环拿不到门禁事实。
# 新增代码+TargetIdentityMaturity：函数段落结束，verify_owned_target_identity 到此结束；如果没有这个边界说明，用户不容易看出动作前验证范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，run_phase111_target_identity_contract 提供无副作用自检；如果没有这个函数，测试和真实终端没有统一 Task 3 报告。
def run_phase111_target_identity_contract() -> dict[str, Any]:  # 新增代码+TargetIdentityMaturity：定义 Task 3 合同入口；如果没有这一行，CLI 无法生成成熟度事实。
    raw_path = r"C:\Users\joyzq\AppData\Local\Obsidian\Obsidian.exe"  # 新增代码+TargetIdentityMaturity：准备真实风格路径样本；如果没有这一行，路径脱敏自检没有覆盖。
    launch_result = {"process_id": 4242, "process_executable": "Obsidian.exe", "process_path": raw_path, "owned_process_registered": True}  # 新增代码+TargetIdentityMaturity：准备自有进程样本；如果没有这一行，合同没有进程基准。
    window = {"pid": 4242, "hwnd": 8801, "window_id": "hwnd:8801", "process_name": "Obsidian.exe", "process_path": raw_path, "title_preview": "Vault - Obsidian", "app_id": "Obsidian.exe"}  # 新增代码+TargetIdentityMaturity：准备可信窗口样本；如果没有这一行，合同没有窗口基准。
    drifted = {"pid": 9999, "hwnd": 8802, "window_id": "hwnd:8802", "process_name": "Obsidian.exe", "process_path": raw_path, "title_preview": "Vault - Obsidian", "app_id": "Obsidian.exe"}  # 新增代码+TargetIdentityMaturity：准备漂移窗口样本；如果没有这一行，合同无法证明同标题不同 pid 会阻断。
    preexisting_launch = {"process_id": 1111, "process_executable": "Obsidian.exe", "owned_process_registered": False}  # 新增代码+TargetIdentityMaturity：准备非自有进程样本；如果没有这一行，用户已有窗口保护没有合同证据。
    owned = build_owned_target_identity(launch_result, window)  # 新增代码+TargetIdentityMaturity：构建可信目标；如果没有这一行，合同没有成功路径。
    stable = verify_owned_target_identity(owned, window)  # 新增代码+TargetIdentityMaturity：验证稳定窗口；如果没有这一行，合同无法证明正常路径可放行。
    drift = verify_owned_target_identity(owned, drifted)  # 新增代码+TargetIdentityMaturity：验证漂移窗口；如果没有这一行，合同无法证明动作会被阻断。
    preexisting = build_owned_target_identity(preexisting_launch, dict(window, pid=1111, hwnd=8803, window_id="hwnd:8803"))  # 新增代码+TargetIdentityMaturity：验证用户已有窗口保护；如果没有这一行，合同无法证明未拥有进程会拒绝。
    report_text = json.dumps(owned.to_report(), ensure_ascii=False, sort_keys=True)  # 新增代码+TargetIdentityMaturity：序列化成功报告检查泄露；如果没有这一行，路径脱敏只靠字段名猜测。
    raw_path_not_exposed = raw_path not in report_text  # 新增代码+TargetIdentityMaturity：确认原始路径没有暴露；如果没有这一行，合同无法量化隐私保护。
    passed = bool(owned.target_identity_verified and stable.allowed and drift.target_drift_blocks_action and not drift.allowed and preexisting.user_preexisting_window_preserved and not preexisting.target_identity_verified and raw_path_not_exposed and not PHASE111_UNCONTROLLED_ACTIONS_EXPANDED)  # 新增代码+TargetIdentityMaturity：计算合同通过条件；如果没有这一行，CLI 不能用退出码表达失败。
    return {"marker": PHASE111_TARGET_IDENTITY_MARKER, "ok_token": PHASE111_TARGET_IDENTITY_OK_TOKEN, "model": PHASE111_TARGET_IDENTITY_MODEL, "passed": passed, "target_identity_model_ready": True, "process_identity_verified": owned.process_identity_verified, "window_identity_verified": owned.window_identity_verified, "target_identity_verified": owned.target_identity_verified, "target_drift_blocks_action": drift.target_drift_blocks_action, "same_title_different_pid_refused": not drift.allowed, "user_preexisting_window_preserved": preexisting.user_preexisting_window_preserved, "process_path_raw_not_exposed": raw_path_not_exposed, "real_desktop_touched": False, "uncontrolled_actions_expanded": PHASE111_UNCONTROLLED_ACTIONS_EXPANDED, "owned_report": owned.to_report(), "stable_verification": stable.to_report(), "drift_verification": drift.to_report(), "preexisting_report": preexisting.to_report()}  # 新增代码+TargetIdentityMaturity：返回完整合同报告；如果没有这一行，测试、CLI 和最终矩阵无法共享事实。
# 新增代码+TargetIdentityMaturity：函数段落结束，run_phase111_target_identity_contract 到此结束；如果没有这个边界说明，用户不容易看出合同范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，phase111_cli_line 把合同报告转成稳定 token 行；如果没有这个函数，真实终端验收只能解析复杂 JSON。
def phase111_cli_line(report: dict[str, Any]) -> str:  # 新增代码+TargetIdentityMaturity：定义 CLI 文本格式化入口；如果没有这一行，验收输出没有固定格式。
    ok_token = f" {PHASE111_TARGET_IDENTITY_OK_TOKEN}" if bool(report.get("passed", False)) else ""  # 新增代码+TargetIdentityMaturity：只在通过时追加 OK token；如果没有这一行，失败输出可能被误判成功。
    return f"{PHASE111_TARGET_IDENTITY_MARKER}{ok_token} target_identity_model_ready={_phase111_bool_token(report.get('target_identity_model_ready', False))} process_identity_verified={_phase111_bool_token(report.get('process_identity_verified', False))} window_identity_verified={_phase111_bool_token(report.get('window_identity_verified', False))} target_identity_verified={_phase111_bool_token(report.get('target_identity_verified', False))} target_drift_blocks_action={_phase111_bool_token(report.get('target_drift_blocks_action', False))} same_title_different_pid_refused={_phase111_bool_token(report.get('same_title_different_pid_refused', False))} user_preexisting_window_preserved={_phase111_bool_token(report.get('user_preexisting_window_preserved', False))} process_path_raw_not_exposed={_phase111_bool_token(report.get('process_path_raw_not_exposed', False))} real_desktop_touched={_phase111_bool_token(report.get('real_desktop_touched', False))} uncontrolled_actions_expanded={_phase111_bool_token(report.get('uncontrolled_actions_expanded', False))}"  # 新增代码+TargetIdentityMaturity：返回固定顺序 token 行；如果没有这一行，场景断言容易因输出漂移失败。
# 新增代码+TargetIdentityMaturity：函数段落结束，phase111_cli_line 到此结束；如果没有这个边界说明，用户不容易看出 CLI 输出范围。


# 新增代码+TargetIdentityMaturity：函数段落开始，main 提供命令行自检入口；如果没有这个函数，用户不能直接运行模块查看 Task 3 合同。
def main(argv: list[str] | None = None) -> int:  # 新增代码+TargetIdentityMaturity：定义 CLI main；如果没有这一行，python -m 运行没有明确入口。
    _ = argv  # 新增代码+TargetIdentityMaturity：保留未来参数扩展位；如果没有这一行，读者可能误以为 argv 被漏掉。
    report = run_phase111_target_identity_contract()  # 新增代码+TargetIdentityMaturity：运行无真实桌面副作用的合同；如果没有这一行，CLI 不会产生验收事实。
    print(phase111_cli_line(report))  # 新增代码+TargetIdentityMaturity：打印稳定 token 行；如果没有这一行，终端验收不能快速匹配。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+TargetIdentityMaturity：打印完整 JSON 便于排查；如果没有这一行，失败时只能看短 token。
    print(PHASE111_TARGET_IDENTITY_MARKER)  # 新增代码+TargetIdentityMaturity：单独打印 ready marker 便于人工观察；如果没有这一行，可见终端里不容易发现阶段标识。
    return 0 if bool(report.get("passed", False)) else 1  # 新增代码+TargetIdentityMaturity：按合同结果返回退出码；如果没有这一行，失败也可能被自动化当成成功。
# 新增代码+TargetIdentityMaturity：函数段落结束，main 到此结束；如果没有这个边界说明，用户不容易看出命令行入口范围。


__all__ = ["PHASE111_TARGET_IDENTITY_MARKER", "PHASE111_TARGET_IDENTITY_MODEL", "PHASE111_TARGET_IDENTITY_OK_TOKEN", "PHASE111_UNCONTROLLED_ACTIONS_EXPANDED", "OwnedTargetIdentity", "ProcessIdentity", "TargetIdentityVerification", "WindowIdentity", "build_owned_target_identity", "build_process_identity", "build_window_identity", "main", "normalize_executable_name", "phase111_cli_line", "phase111_sha256_16", "run_phase111_target_identity_contract", "summarize_window_title", "verify_owned_target_identity", "window_title_sha256_16"]  # 新增代码+TargetIdentityMaturity：公开 Task 3 的稳定 API；如果没有这一行，后续模块和学习备份不容易确认哪些接口是正式合同。


if __name__ == "__main__":  # 新增代码+TargetIdentityMaturity：文件入口段开始，允许直接运行模块；如果没有这一行，python -m 方式不会启动自检。
    raise SystemExit(main())  # 新增代码+TargetIdentityMaturity：用 main 的返回码退出；如果没有这一行，命令行状态不明确。
# 新增代码+TargetIdentityMaturity：文件入口段结束，直接运行模块到此结束；如果没有这个边界说明，用户不容易看出入口范围。
