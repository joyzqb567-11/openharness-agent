"""Phase98 Computer Use 模式 session store。"""  # 新增代码+Phase98UniversalComputerUseMode：说明本文件负责 /computer use 的模式状态；如果没有这行代码，读者不知道这里是 Phase98 session 的入口。
from __future__ import annotations  # 新增代码+Phase98UniversalComputerUseMode：启用延迟类型解析；如果没有这行代码，较复杂的类型注解在旧解析顺序下更容易出错。

import hashlib  # 新增代码+Phase98UniversalComputerUseMode：导入哈希库用于脱敏 reason；如果没有这行代码，敏感原因只能原文落盘或无法关联排查。
import json  # 新增代码+Phase98UniversalComputerUseMode：导入 JSON 库读取状态文件；如果没有这行代码，store 无法恢复 current.json 和 pending_full.json。
import secrets  # 新增代码+Phase98UniversalComputerUseMode：导入安全随机库生成 full mode 确认 token；如果没有这行代码，token 容易可预测。
import time  # 新增代码+Phase98UniversalComputerUseMode：导入时间库计算 TTL；如果没有这行代码，模式无法自动过期。
from pathlib import Path  # 新增代码+Phase98UniversalComputerUseMode：导入 Path 统一处理 Windows 路径；如果没有这行代码，路径拼接会更脆弱。
from typing import Any  # 新增代码+Phase98UniversalComputerUseMode：导入 Any 描述 JSON 风格输入输出；如果没有这行代码，公开 API 的类型边界不清楚。

try:  # 新增代码+Phase98UniversalComputerUseMode：优先按包路径导入项目原子写工具；如果没有这段代码，正常包运行时不能复用安全写入。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase98UniversalComputerUseMode：复用项目原子 JSON 写入；如果没有这行代码，状态文件可能半写损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase98UniversalComputerUseMode：兼容脚本模式导入失败；如果没有这段代码，bat 入口在包名前缀缺失时会直接崩溃。
    if error.name not in {"learning_agent", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase98UniversalComputerUseMode：只兜底包路径缺失；如果没有这行代码，真实内部导入错误会被误吞。
        raise  # 新增代码+Phase98UniversalComputerUseMode：重新抛出非路径类错误；如果没有这行代码，排查 runtime.files 内部问题会很困难。
    from runtime.files import atomic_write_json  # type: ignore  # 新增代码+Phase98UniversalComputerUseMode：脚本模式复用原子 JSON 写入；如果没有这行代码，可见终端脚本可能无法保存状态。

PHASE98_COMPUTER_USE_MODE_READY = "PHASE98_COMPUTER_USE_MODE_READY"  # 新增代码+Phase98UniversalComputerUseMode：定义稳定 ready marker；如果没有这行代码，测试和终端验收没有锚点。
PHASE98_COMPUTER_USE_MODE_OK = "PHASE98_COMPUTER_USE_MODE_OK"  # 新增代码+Phase98UniversalComputerUseMode：定义稳定 OK token；如果没有这行代码，外部无法判断 Phase98 状态正常。
PHASE98_COMPUTER_USE_MODE_MODEL = "phase98_universal_computer_use_permission_mode"  # 新增代码+Phase98UniversalComputerUseMode：定义模式模型名；如果没有这行代码，状态文件缺少版本语义。
DEFAULT_MODE_SESSION_ID = "learning-agent-default-session"  # 新增代码+Phase98UniversalComputerUseMode：定义默认 session id；如果没有这行代码，调用方需要硬编码默认会话。
DEFAULT_MODE_SESSION_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "mode_sessions"  # 新增代码+Phase98UniversalComputerUseMode：定义默认持久化目录；如果没有这行代码，模式状态没有统一落盘位置。
DEFAULT_NORMAL_TTL_SECONDS = 900  # 新增代码+Phase98UniversalComputerUseMode：定义 normal/observe 默认 15 分钟 TTL；如果没有这行代码，普通授权可能无限期保留。
DEFAULT_FULL_TTL_SECONDS = 300  # 新增代码+Phase98UniversalComputerUseMode：定义 full mode 默认 5 分钟 TTL；如果没有这行代码，高风险模式可能持续过久。

NORMAL_ACTION_CLASSES = (  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，列出 normal 允许动作；如果没有这段代码，权限策略会散落在判断里。
    "observe_screen",  # 新增代码+Phase98UniversalComputerUseMode：允许观察屏幕；如果没有这行代码，normal 模式无法先看后做。
    "list_windows",  # 新增代码+Phase98UniversalComputerUseMode：允许列窗口；如果没有这行代码，normal 模式无法选择目标窗口。
    "focus_window",  # 新增代码+Phase98UniversalComputerUseMode：允许聚焦窗口；如果没有这行代码，普通应用控制缺少目标切换能力。
    "click",  # 新增代码+Phase98UniversalComputerUseMode：允许单击；如果没有这行代码，测试要求的 click 能力会缺失。
    "double_click",  # 新增代码+Phase98UniversalComputerUseMode：允许双击；如果没有这行代码，常见文件和控件打开动作缺失。
    "type_text",  # 新增代码+Phase98UniversalComputerUseMode：允许普通文本输入；如果没有这行代码，测试要求的 type_text 能力会缺失。
    "hotkey_safe",  # 新增代码+Phase98UniversalComputerUseMode：允许安全热键；如果没有这行代码，保存等常见组合键无法表达。
    "scroll",  # 新增代码+Phase98UniversalComputerUseMode：允许滚动；如果没有这行代码，长页面或列表无法浏览。
    "drag",  # 新增代码+Phase98UniversalComputerUseMode：允许拖拽；如果没有这行代码，滑块和选择区域等动作无法表达。
    "clipboard_temporary_text",  # 新增代码+Phase98UniversalComputerUseMode：允许临时剪贴板文本；如果没有这行代码，大段输入缺少可控通道。
    "save_current_document",  # 新增代码+Phase98UniversalComputerUseMode：允许保存当前文档；如果没有这行代码，普通编辑任务缺少收尾动作。
)  # 新增代码+Phase98UniversalComputerUseMode：函数段落结束，normal 动作列表到此结束；如果没有这行代码，Python 无法关闭元组。
OBSERVE_ACTION_CLASSES = ("observe_screen", "list_windows")  # 新增代码+Phase98UniversalComputerUseMode：定义 observe 只读动作；如果没有这行代码，观察模式可能误放写动作。
FULL_EXTRA_ACTION_CLASSES = ("press_key", "hotkey_risky", "launch_app", "close_window", "move_window", "resize_window")  # 新增代码+Phase98UniversalComputerUseMode：定义 full 候选高风险动作标签；如果没有这行代码，full 模式无法表达更宽动作面。
DANGEROUS_TARGET_TERMS = (  # 修改代码+Phase98UniversalComputerUseMode：函数段落开始，列出更具体的危险窗口身份关键词；如果没有这段代码，风险拦截会过宽或漏掉高风险目标。
    "powershell.exe",  # 修改代码+Phase98UniversalComputerUseMode：只拦截明确 PowerShell 进程名；如果没有这行代码，命令行高风险入口可能被误操作。
    "windows powershell",  # 修改代码+Phase98UniversalComputerUseMode：拦截明确 PowerShell 窗口标题；如果没有这行代码，只有标题没有进程名时会漏检。
    "pwsh.exe",  # 修改代码+Phase98UniversalComputerUseMode：拦截新版 PowerShell 进程名；如果没有这行代码，跨平台 PowerShell 入口会漏检。
    "cmd.exe",  # 修改代码+Phase98UniversalComputerUseMode：拦截明确 cmd 进程名而不是裸 cmd；如果没有这行代码，命令提示符可能被误操作。
    "command prompt",  # 修改代码+Phase98UniversalComputerUseMode：拦截命令提示符标题；如果没有这行代码，cmd 标题场景会漏检。
    "windows terminal",  # 修改代码+Phase98UniversalComputerUseMode：拦截明确 Windows Terminal 标题；如果没有这行代码，终端窗口可能被误输入。
    "wt.exe",  # 修改代码+Phase98UniversalComputerUseMode：拦截 Windows Terminal 进程名；如果没有这行代码，终端进程名场景会漏检。
    "administrator:",  # 修改代码+Phase98UniversalComputerUseMode：拦截标题中的管理员前缀；如果没有这行代码，高权限窗口风险不可控。
    "administrator -",  # 修改代码+Phase98UniversalComputerUseMode：拦截标题中的管理员连接格式；如果没有这行代码，高权限标题变体会漏检。
    "run as administrator",  # 修改代码+Phase98UniversalComputerUseMode：拦截以管理员运行窗口；如果没有这行代码，提权入口可能被误点。
    "user account control",  # 修改代码+Phase98UniversalComputerUseMode：拦截 UAC 全称窗口；如果没有这行代码，系统授权弹窗可能被误点。
    "uac",  # 修改代码+Phase98UniversalComputerUseMode：拦截明确 UAC 标识；如果没有这行代码，短标题授权弹窗可能漏检。
    "windows security",  # 修改代码+Phase98UniversalComputerUseMode：拦截 Windows Security 窗口；如果没有这行代码，安全设置可能被误操作。
    "windows defender",  # 修改代码+Phase98UniversalComputerUseMode：拦截 Windows Defender 窗口；如果没有这行代码，防护设置可能被误改。
    "microsoft defender",  # 修改代码+Phase98UniversalComputerUseMode：拦截 Microsoft Defender 窗口；如果没有这行代码，新标题防护窗口会漏检。
    "defender firewall",  # 修改代码+Phase98UniversalComputerUseMode：拦截 Defender 防火墙窗口；如果没有这行代码，网络安全策略可能被误改。
    "windows firewall",  # 修改代码+Phase98UniversalComputerUseMode：拦截 Windows 防火墙窗口；如果没有这行代码，防火墙配置可能被误操作。
    "registry editor",  # 修改代码+Phase98UniversalComputerUseMode：拦截注册表编辑器标题；如果没有这行代码，注册表可能被误操作。
    "regedit.exe",  # 修改代码+Phase98UniversalComputerUseMode：拦截注册表编辑器进程；如果没有这行代码，注册表进程名场景会漏检。
    "services.msc",  # 修改代码+Phase98UniversalComputerUseMode：拦截系统服务管理控制台文件名；如果没有这行代码，系统服务可能被误停。
    "windows services",  # 修改代码+Phase98UniversalComputerUseMode：拦截明确 Windows 服务标题；如果没有这行代码，服务管理窗口可能漏检。
    "password manager",  # 修改代码+Phase98UniversalComputerUseMode：拦截密码管理器窗口；如果没有这行代码，密码内容可能被误处理。
    "credential manager",  # 修改代码+Phase98UniversalComputerUseMode：拦截凭据管理器窗口；如果没有这行代码，凭据窗口可能被误操作。
    "windows credentials",  # 修改代码+Phase98UniversalComputerUseMode：拦截 Windows 凭据窗口；如果没有这行代码，系统凭据页可能漏检。
    "captcha",  # 修改代码+Phase98UniversalComputerUseMode：拦截验证码窗口标题；如果没有这行代码，验证码场景边界不清楚。
    "payment method",  # 修改代码+Phase98UniversalComputerUseMode：拦截支付方式窗口；如果没有这行代码，支付场景可能被误操作。
    "payment checkout",  # 修改代码+Phase98UniversalComputerUseMode：拦截支付结账窗口；如果没有这行代码，结账付款场景可能漏检。
    "checkout payment",  # 修改代码+Phase98UniversalComputerUseMode：拦截另一种付款标题顺序；如果没有这行代码，付款标题变体会漏检。
    "api key",  # 修改代码+Phase98UniversalComputerUseMode：拦截 API key 标题；如果没有这行代码，密钥场景可能被误操作。
    "access token",  # 修改代码+Phase98UniversalComputerUseMode：拦截访问令牌标题；如果没有这行代码，令牌隐私可能被误处理。
    "auth token",  # 修改代码+Phase98UniversalComputerUseMode：拦截认证令牌标题；如果没有这行代码，认证令牌窗口会漏检。
    "secret token",  # 修改代码+Phase98UniversalComputerUseMode：拦截秘密令牌标题；如果没有这行代码，敏感 token 场景会漏检。
    "private key",  # 修改代码+Phase98UniversalComputerUseMode：拦截 private key 标题；如果没有这行代码，私钥场景可能被误操作。
    "验证码",  # 修改代码+Phase98UniversalComputerUseMode：拦截中文验证码标题；如果没有这行代码，中文认证场景会漏检。
    "密码",  # 修改代码+Phase98UniversalComputerUseMode：拦截中文密码标题；如果没有这行代码，中文密码窗口会漏检。
    "支付",  # 修改代码+Phase98UniversalComputerUseMode：拦截中文支付标题；如果没有这行代码，中文支付场景会漏检。
    "付款",  # 修改代码+Phase98UniversalComputerUseMode：拦截中文付款标题；如果没有这行代码，中文付款场景会漏检。
    "令牌",  # 修改代码+Phase98UniversalComputerUseMode：拦截中文令牌标题；如果没有这行代码，中文 token 场景会漏检。
    "私钥",  # 修改代码+Phase98UniversalComputerUseMode：拦截中文私钥标题；如果没有这行代码，中文私钥场景会漏检。
    "管理员",  # 修改代码+Phase98UniversalComputerUseMode：拦截中文管理员标题；如果没有这行代码，中文高权限窗口会漏检。
)  # 修改代码+Phase98UniversalComputerUseMode：函数段落结束，危险关键词列表到此结束；如果没有这行代码，Python 无法关闭元组。

def _phase98_now() -> float:  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，提供可注入当前时间；如果没有这段函数，测试和 TTL 计算不易控制。
    return time.time()  # 新增代码+Phase98UniversalComputerUseMode：返回当前 Unix 秒；如果没有这行代码，状态无法计算创建和过期时间。
# 新增代码+Phase98UniversalComputerUseMode：函数段落结束，_phase98_now 到此结束；如果没有这个边界说明，初学者不容易看出时间 helper 范围。

def _phase98_reason_meta(reason: str) -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，把 reason 脱敏成元数据；如果没有这段函数，敏感 prompt 可能原文落盘。
    reason_text = str(reason or "")  # 新增代码+Phase98UniversalComputerUseMode：把输入原因转成字符串；如果没有这行代码，None 或非字符串会导致哈希不稳定。
    digest = hashlib.sha256(reason_text.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase98UniversalComputerUseMode：计算 16 位短哈希；如果没有这行代码，排查时无法关联同一原因且不能脱敏。
    return {"reason_sha256_16": digest, "reason_text_included": False}  # 新增代码+Phase98UniversalComputerUseMode：只返回脱敏字段；如果没有这行代码，调用方拿不到安全可落盘的原因信息。
# 新增代码+Phase98UniversalComputerUseMode：函数段落结束，_phase98_reason_meta 到此结束；如果没有这个边界说明，初学者不容易看出脱敏 helper 范围。

def _phase98_read_json(path: Path) -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，安全读取 JSON 字典；如果没有这段函数，多个方法会重复脆弱读取逻辑。
    if not path.exists():  # 新增代码+Phase98UniversalComputerUseMode：先判断文件是否存在；如果没有这行代码，首次启动会因为没有状态文件而报错。
        return {}  # 新增代码+Phase98UniversalComputerUseMode：不存在时返回空字典；如果没有这行代码，调用方无法用默认状态继续运行。
    try:  # 新增代码+Phase98UniversalComputerUseMode：包住读文件和解析过程；如果没有这行代码，半写 JSON 会拖垮 status。
        loaded = json.loads(path.read_text(encoding="utf-8"))  # 新增代码+Phase98UniversalComputerUseMode：按 UTF-8 读取并解析 JSON；如果没有这行代码，持久化状态无法恢复。
    except (OSError, json.JSONDecodeError):  # 新增代码+Phase98UniversalComputerUseMode：捕获磁盘读取和 JSON 损坏；如果没有这行代码，坏状态文件会阻断模式关闭。
        return {}  # 新增代码+Phase98UniversalComputerUseMode：坏文件时返回空状态；如果没有这行代码，系统无法自愈到安全默认值。
    return loaded if isinstance(loaded, dict) else {}  # 新增代码+Phase98UniversalComputerUseMode：只接受字典状态；如果没有这行代码，列表或字符串会污染后续判断。
# 新增代码+Phase98UniversalComputerUseMode：函数段落结束，_phase98_read_json 到此结束；如果没有这个边界说明，初学者不容易看出读取 helper 范围。

def _phase98_window_text(window: dict[str, Any]) -> str:  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，把窗口信息合并为风险扫描文本；如果没有这段函数，危险目标检查会漏字段。
    if not isinstance(window, dict):  # 新增代码+Phase98UniversalComputerUseMode：确认窗口参数是字典；如果没有这行代码，坏输入可能导致异常。
        return ""  # 新增代码+Phase98UniversalComputerUseMode：坏输入返回空文本；如果没有这行代码，权限判断无法容错。
    identity_fields = ("app_id", "process_name", "title_preview", "class_name")  # 修改代码+Phase98UniversalComputerUseMode：只读取稳定窗口身份字段；如果没有这行代码，按钮文本等普通内容可能造成误拦截。
    parts = [str(window.get(field, "") or "") for field in identity_fields]  # 修改代码+Phase98UniversalComputerUseMode：按白名单字段收集风险文本；如果没有这行代码，危险目标扫描会重新变宽。
    return " ".join(parts).lower()  # 修改代码+Phase98UniversalComputerUseMode：合并并小写化用于关键词匹配；如果没有这行代码，大小写差异会导致漏拦截。
# 新增代码+Phase98UniversalComputerUseMode：函数段落结束，_phase98_window_text 到此结束；如果没有这个边界说明，初学者不容易看出风险文本 helper 范围。

class ComputerUseModeSessionStore:  # 新增代码+Phase98UniversalComputerUseMode：类段落开始，管理 Computer Use 模式 session；如果没有这个类，外部没有统一 API 打开/停止/查询模式。
    def __init__(self, base_dir: str | Path | None = None, now_func: Any = _phase98_now) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，初始化状态目录和时间函数；如果没有这段函数，测试不能注入隔离目录。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_MODE_SESSION_ROOT  # 新增代码+Phase98UniversalComputerUseMode：确定状态根目录；如果没有这行代码，store 不知道读写哪里。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase98UniversalComputerUseMode：确保目录存在；如果没有这行代码，首次写 current.json 会失败。
        self.now_func = now_func  # 新增代码+Phase98UniversalComputerUseMode：保存当前时间函数；如果没有这行代码，TTL 无法使用可测试时间源。
        self.current_path = self.base_dir / "current.json"  # 新增代码+Phase98UniversalComputerUseMode：定义当前模式状态文件；如果没有这行代码，open/status/stop 不能共享状态。
        self.pending_full_path = self.base_dir / "pending_full.json"  # 新增代码+Phase98UniversalComputerUseMode：定义 full mode 待确认文件；如果没有这行代码，二次确认 token 无法持久化。
    # 新增代码+Phase98UniversalComputerUseMode：函数段落结束，ComputerUseModeSessionStore.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _now(self) -> float:  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，读取当前时间；如果没有这段函数，每处调用 now_func 都要重复类型转换。
        return float(self.now_func())  # 新增代码+Phase98UniversalComputerUseMode：返回浮点秒；如果没有这行代码，字符串时间源会破坏 TTL 运算。
    # 新增代码+Phase98UniversalComputerUseMode：函数段落结束，ComputerUseModeSessionStore._now 到此结束；如果没有这个边界说明，初学者不容易看出时间读取范围。

    def _allowed_actions_for_mode(self, mode: str) -> list[str]:  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，按模式返回允许动作；如果没有这段函数，status 和 evaluate 会重复策略。
        if mode == "observe":  # 新增代码+Phase98UniversalComputerUseMode：判断观察模式；如果没有这行代码，observe 会误用 normal 权限。
            return list(OBSERVE_ACTION_CLASSES)  # 新增代码+Phase98UniversalComputerUseMode：返回只读动作列表；如果没有这行代码，观察模式无法明确阻止写动作。
        if mode == "full":  # 新增代码+Phase98UniversalComputerUseMode：判断 full 模式；如果没有这行代码，确认后的 full 无法获得扩展动作标签。
            return list(NORMAL_ACTION_CLASSES + FULL_EXTRA_ACTION_CLASSES)  # 新增代码+Phase98UniversalComputerUseMode：返回 normal 加候选高风险动作；如果没有这行代码，full 模式和 normal 没区别。
        return list(NORMAL_ACTION_CLASSES)  # 新增代码+Phase98UniversalComputerUseMode：默认返回 normal 动作；如果没有这行代码，普通模式测试会缺少 click/type_text。
    # 新增代码+Phase98UniversalComputerUseMode：函数段落结束，ComputerUseModeSessionStore._allowed_actions_for_mode 到此结束；如果没有这个边界说明，初学者不容易看出动作策略范围。

    def _build_state(self, mode: str, reason: str, ttl_seconds: int | None, allow_full: bool = False) -> dict[str, Any]:  # 修改代码+Phase98UniversalComputerUseMode：函数段落开始，构建可落盘状态并区分直接打开和确认打开；如果没有这段函数，多个入口会写出不一致字段。
        requested_mode = str(mode or "normal")  # 修改代码+Phase98UniversalComputerUseMode：把调用方模式转成字符串；如果没有这行代码，None 或非字符串会污染状态。
        normalized_mode = requested_mode if requested_mode in {"normal", "observe"} else "normal"  # 修改代码+Phase98UniversalComputerUseMode：直接打开只允许 normal/observe；如果没有这行代码，open_mode(full) 会绕过二次确认。
        if allow_full and requested_mode == "full":  # 修改代码+Phase98UniversalComputerUseMode：只给确认成功路径放行 full；如果没有这行代码，confirm_full_mode 无法真正激活 full。
            normalized_mode = "full"  # 修改代码+Phase98UniversalComputerUseMode：把已确认请求设置成 full；如果没有这行代码，二次确认成功后仍只能得到 normal。
        default_ttl = DEFAULT_FULL_TTL_SECONDS if normalized_mode == "full" else DEFAULT_NORMAL_TTL_SECONDS  # 新增代码+Phase98UniversalComputerUseMode：按模式选择默认 TTL；如果没有这行代码，full 和 normal 风险窗口无法区分。
        ttl = int(ttl_seconds if ttl_seconds is not None else default_ttl)  # 新增代码+Phase98UniversalComputerUseMode：确定最终 TTL；如果没有这行代码，状态无法记录授权时长。
        now = self._now()  # 新增代码+Phase98UniversalComputerUseMode：读取当前时间；如果没有这行代码，created_at 和 expires_at 无法计算。
        state = {"schema_version": 1, "session_id": DEFAULT_MODE_SESSION_ID, "model": PHASE98_COMPUTER_USE_MODE_MODEL, "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK, "mode": normalized_mode, "full_mode": normalized_mode == "full", "opened": True, "stopped": False, "created_at": now, "updated_at": now, "expires_at": now + max(0, ttl), "ttl_original_seconds": max(0, ttl), "per_app_allowlist_required": False, "ordinary_apps_allowed_by_risk_policy": normalized_mode in {"normal", "full"}, "allowed_action_classes": self._allowed_actions_for_mode(normalized_mode)}  # 新增代码+Phase98UniversalComputerUseMode：写入完整模式状态；如果没有这行代码，status 缺少测试和调用方需要的核心字段。
        state.update(_phase98_reason_meta(reason))  # 新增代码+Phase98UniversalComputerUseMode：加入脱敏原因元数据；如果没有这行代码，状态无法证明没有保存原文且无法关联排查。
        return state  # 新增代码+Phase98UniversalComputerUseMode：返回完整状态；如果没有这行代码，open_mode 无法写盘。
    # 新增代码+Phase98UniversalComputerUseMode：函数段落结束，ComputerUseModeSessionStore._build_state 到此结束；如果没有这个边界说明，初学者不容易看出状态构建范围。

    def open_mode(self, mode: str = "normal", reason: str = "", ttl_seconds: int | None = None) -> dict[str, Any]:  # 修改代码+Phase98UniversalComputerUseMode：函数段落开始，只直接打开 normal/observe 模式；如果没有这段函数，用户无法启用 computer use 权限模式。
        state = self._build_state(mode, reason, ttl_seconds)  # 新增代码+Phase98UniversalComputerUseMode：构建新状态；如果没有这行代码，open_mode 会缺少统一字段。
        atomic_write_json(self.current_path, state)  # 新增代码+Phase98UniversalComputerUseMode：原子写入 current.json；如果没有这行代码，模式不会持久化。
        return dict(state)  # 新增代码+Phase98UniversalComputerUseMode：返回状态副本；如果没有这行代码，调用方不知道是否打开成功。
    # 新增代码+Phase98UniversalComputerUseMode：函数段落结束，ComputerUseModeSessionStore.open_mode 到此结束；如果没有这个边界说明，初学者不容易看出打开模式范围。

    def request_full_mode(self, reason: str = "") -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，请求 full mode 二次确认；如果没有这段函数，高风险模式可能被一步打开。
        now = self._now()  # 新增代码+Phase98UniversalComputerUseMode：读取当前时间；如果没有这行代码，pending token 无法记录创建时间。
        token = f"FULL-{secrets.token_hex(4).upper()}"  # 新增代码+Phase98UniversalComputerUseMode：生成短确认 token；如果没有这行代码，用户无法进行二次确认。
        pending = {"schema_version": 1, "model": PHASE98_COMPUTER_USE_MODE_MODEL, "confirmation_token": token, "strong_confirmation_required": True, "created_at": now, "expires_at": now + DEFAULT_FULL_TTL_SECONDS}  # 新增代码+Phase98UniversalComputerUseMode：构建待确认状态；如果没有这行代码，confirm_full_mode 没有可信依据。
        pending.update(_phase98_reason_meta(reason))  # 新增代码+Phase98UniversalComputerUseMode：加入脱敏原因元数据；如果没有这行代码，pending 文件可能缺少可审计原因哈希。
        atomic_write_json(self.pending_full_path, pending)  # 新增代码+Phase98UniversalComputerUseMode：原子写入 pending_full.json；如果没有这行代码，二次确认 token 不会持久化。
        return {"opened": False, "full_mode": False, "low_level_event_count": 0, "strong_confirmation_required": True, "confirmation_token": token, "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK}  # 修改代码+Phase98UniversalComputerUseMode：返回待确认结果且明确不打开不派发；如果没有这行代码，Task3 可能误判 request 已经提权或触发真实输入。
    # 新增代码+Phase98UniversalComputerUseMode：函数段落结束，ComputerUseModeSessionStore.request_full_mode 到此结束；如果没有这个边界说明，初学者不容易看出 full 请求范围。

    def confirm_full_mode(self, confirmation_token: str, reason: str = "") -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，用 token 确认 full mode；如果没有这段函数，二次确认流程无法完成。
        pending = _phase98_read_json(self.pending_full_path)  # 新增代码+Phase98UniversalComputerUseMode：读取待确认文件；如果没有这行代码，无法验证 token。
        pending_token = str(pending.get("confirmation_token", "") or "")  # 修改代码+Phase98UniversalComputerUseMode：读取已保存 token 并确保空值不可误匹配；如果没有这行代码，空 pending 可能被空输入绕过。
        token_matches = bool(pending_token) and pending_token == str(confirmation_token or "")  # 修改代码+Phase98UniversalComputerUseMode：比较非空 token；如果没有这行代码，错误 token 也可能打开 full。
        token_live = float(pending.get("expires_at", 0) or 0) >= self._now()  # 新增代码+Phase98UniversalComputerUseMode：检查 token 是否过期；如果没有这行代码，旧 token 可能长期有效。
        if not token_matches:  # 修改代码+Phase98UniversalComputerUseMode：优先判断 token 不匹配；如果没有这行代码，输错 token 和过期 token 会混成一个原因。
            return {"opened": False, "full_mode": False, "decision": "full_mode_confirmation_token_mismatch", "low_level_event_count": 0, "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK}  # 修改代码+Phase98UniversalComputerUseMode：返回错误 token 拒绝且零低层事件；如果没有这行代码，调用方无法准确提示且可能误以为有输入事件。
        if not token_live:  # 修改代码+Phase98UniversalComputerUseMode：单独判断 token 已过期；如果没有这行代码，过期 token 没有稳定原因码。
            return {"opened": False, "full_mode": False, "decision": "full_mode_confirmation_expired", "low_level_event_count": 0, "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK}  # 修改代码+Phase98UniversalComputerUseMode：返回过期拒绝且零低层事件；如果没有这行代码，调用方无法要求用户重新申请确认。
        opened = self._build_state("full", reason, DEFAULT_FULL_TTL_SECONDS, allow_full=True)  # 修改代码+Phase98UniversalComputerUseMode：确认通过后只从内部受控路径构建 full；如果没有这行代码，full mode 不会真正激活或会依赖不安全 open_mode。
        atomic_write_json(self.current_path, opened)  # 修改代码+Phase98UniversalComputerUseMode：原子写入已确认 full 状态；如果没有这行代码，确认成功不会持久化。
        try:  # 新增代码+Phase98UniversalComputerUseMode：尝试清理 pending 文件；如果没有这行代码，旧 token 文件会残留。
            self.pending_full_path.unlink(missing_ok=True)  # 新增代码+Phase98UniversalComputerUseMode：删除已使用 token；如果没有这行代码，token 可能被重复使用。
        except OSError:  # 新增代码+Phase98UniversalComputerUseMode：容忍清理失败；如果没有这行代码，已打开 full 后可能因清理问题误报失败。
            pass  # 新增代码+Phase98UniversalComputerUseMode：忽略清理异常；如果没有这行代码，except 语法不完整。
        return opened  # 新增代码+Phase98UniversalComputerUseMode：返回打开后的 full 状态；如果没有这行代码，调用方拿不到 opened=True。
    # 新增代码+Phase98UniversalComputerUseMode：函数段落结束，ComputerUseModeSessionStore.confirm_full_mode 到此结束；如果没有这个边界说明，初学者不容易看出 full 确认范围。

    def stop(self, reason: str = "") -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，停止当前 computer use 模式；如果没有这段函数，用户无法急停后续动作。
        state = _phase98_read_json(self.current_path) or self._build_state("normal", reason, 0)  # 新增代码+Phase98UniversalComputerUseMode：读取现有状态或创建停止用默认状态；如果没有这行代码，无 current 时 stop 会失败。
        state["mode"] = "stopped"  # 修改代码+Phase98UniversalComputerUseMode：把持久化模式明确改成 stopped；如果没有这行代码，status 可能仍误显示 normal 或 full。
        state["full_mode"] = False  # 修改代码+Phase98UniversalComputerUseMode：停止后清除 full 标记；如果没有这行代码，急停后状态可能仍显示高权限。
        state["stopped"] = True  # 新增代码+Phase98UniversalComputerUseMode：标记已停止；如果没有这行代码，后续动作不会被 computer_use_stopped 拦截。
        state["opened"] = False  # 新增代码+Phase98UniversalComputerUseMode：标记当前不再打开；如果没有这行代码，状态展示会误以为仍可用。
        state["allowed_action_classes"] = []  # 修改代码+Phase98UniversalComputerUseMode：停止后清空允许动作；如果没有这行代码，权限摘要可能还显示可点击可输入。
        state["ordinary_apps_allowed_by_risk_policy"] = False  # 修改代码+Phase98UniversalComputerUseMode：停止后关闭普通应用放行标记；如果没有这行代码，停止状态语义会和 normal 混在一起。
        state["updated_at"] = self._now()  # 新增代码+Phase98UniversalComputerUseMode：记录停止时间；如果没有这行代码，审计无法知道何时停用。
        state.update(_phase98_reason_meta(reason))  # 新增代码+Phase98UniversalComputerUseMode：保存停止原因哈希；如果没有这行代码，stop 原因无法脱敏关联。
        atomic_write_json(self.current_path, state)  # 新增代码+Phase98UniversalComputerUseMode：原子写入停止状态；如果没有这行代码，急停不会持久化。
        return {"stopped": True, "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK}  # 新增代码+Phase98UniversalComputerUseMode：返回停止摘要；如果没有这行代码，调用方无法确认 stop 已执行。
    # 新增代码+Phase98UniversalComputerUseMode：函数段落结束，ComputerUseModeSessionStore.stop 到此结束；如果没有这个边界说明，初学者不容易看出停止范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，读取当前模式状态；如果没有这段函数，终端和测试无法确认权限模式。
        state = _phase98_read_json(self.current_path)  # 新增代码+Phase98UniversalComputerUseMode：读取 current.json；如果没有这行代码，status 无法反映持久化状态。
        if not state:  # 新增代码+Phase98UniversalComputerUseMode：判断是否没有当前状态；如果没有这行代码，首次查询会缺字段。
            return {"opened": False, "stopped": False, "mode": "off", "full_mode": False, "ttl_seconds": 0, "expired": False, "per_app_allowlist_required": False, "ordinary_apps_allowed_by_risk_policy": False, "allowed_action_classes": [], "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK, "model": PHASE98_COMPUTER_USE_MODE_MODEL, "state_path": str(self.current_path)}  # 修改代码+Phase98UniversalComputerUseMode：返回清晰 off 状态而不是 stopped/expired；如果没有这行代码，首次启动会和急停或过期混淆。
        remaining = max(0, int(float(state.get("expires_at", 0) or 0) - self._now()))  # 新增代码+Phase98UniversalComputerUseMode：计算剩余 TTL 秒数；如果没有这行代码，调用方不知道授权是否快过期。
        expired = remaining <= 0  # 新增代码+Phase98UniversalComputerUseMode：计算是否过期；如果没有这行代码，过期模式可能继续被认为可用。
        mode = str(state.get("mode", "normal") or "normal")  # 新增代码+Phase98UniversalComputerUseMode：读取当前模式；如果没有这行代码，状态缺失时无法回退。
        stopped = bool(state.get("stopped")) or mode == "stopped"  # 修改代码+Phase98UniversalComputerUseMode：统一判断停止状态；如果没有这行代码，mode=stopped 可能仍被当成 normal 授权。
        result = dict(state)  # 新增代码+Phase98UniversalComputerUseMode：复制状态避免污染原对象；如果没有这行代码，后续补字段可能影响读取缓存。
        result["ttl_seconds"] = remaining  # 新增代码+Phase98UniversalComputerUseMode：写入动态剩余 TTL；如果没有这行代码，full TTL 测试无法验证小于等于 300。
        result["expired"] = expired  # 新增代码+Phase98UniversalComputerUseMode：写入过期标记；如果没有这行代码，动作评估无法清楚说明过期。
        result["stopped"] = stopped  # 修改代码+Phase98UniversalComputerUseMode：把规范化停止值写回结果；如果没有这行代码，状态消费者可能看到不一致 stopped 字段。
        result["full_mode"] = bool(mode == "full" and not expired and not stopped)  # 修改代码+Phase98UniversalComputerUseMode：只有未停用未过期的 full 才算 full_mode；如果没有这行代码，请求阶段或停止后可能被误认为 full。
        result["allowed_action_classes"] = [] if stopped or expired else self._allowed_actions_for_mode(mode)  # 修改代码+Phase98UniversalComputerUseMode：停止或过期时清空允许动作；如果没有这行代码，status 可能显示不可用模式仍可操作。
        result["marker"] = PHASE98_COMPUTER_USE_MODE_READY  # 新增代码+Phase98UniversalComputerUseMode：补齐稳定 marker；如果没有这行代码，坏旧状态可能丢失验收锚点。
        result["ok_token"] = PHASE98_COMPUTER_USE_MODE_OK  # 新增代码+Phase98UniversalComputerUseMode：补齐稳定 OK token；如果没有这行代码，坏旧状态可能丢失成功锚点。
        result["model"] = PHASE98_COMPUTER_USE_MODE_MODEL  # 新增代码+Phase98UniversalComputerUseMode：补齐模型名；如果没有这行代码，状态消费者无法识别 Phase98。
        result["state_path"] = str(self.current_path)  # 新增代码+Phase98UniversalComputerUseMode：返回状态文件路径；如果没有这行代码，排查时不清楚读的是哪个文件。
        return result  # 新增代码+Phase98UniversalComputerUseMode：返回完整状态；如果没有这行代码，调用方拿不到查询结果。
    # 新增代码+Phase98UniversalComputerUseMode：函数段落结束，ComputerUseModeSessionStore.status 到此结束；如果没有这个边界说明，初学者不容易看出查询范围。

    def permissions(self) -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，返回权限摘要；如果没有这段函数，调用方只能自己从 status 拼权限信息。
        current = self.status()  # 新增代码+Phase98UniversalComputerUseMode：复用当前状态；如果没有这行代码，permissions 可能和 status 不一致。
        return {"mode": current["mode"], "full_mode": current["full_mode"], "high_risk_requires_confirmation": True, "per_app_allowlist_required": False, "dangerous_target_terms_hidden": True, "allowed_action_classes": current["allowed_action_classes"], "stopped": current["stopped"], "expired": current["expired"], "ordinary_apps_allowed_by_risk_policy": current["ordinary_apps_allowed_by_risk_policy"], "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK}  # 修改代码+Phase98UniversalComputerUseMode：返回 Task3 渲染需要的权限摘要；如果没有这行代码，终端 UI 会缺少高风险确认、危险词隐藏和动作列表字段。
    # 新增代码+Phase98UniversalComputerUseMode：函数段落结束，ComputerUseModeSessionStore.permissions 到此结束；如果没有这个边界说明，初学者不容易看出权限摘要范围。

    def evaluate_action(self, window: dict[str, Any], action_class: str) -> dict[str, Any]:  # 新增代码+Phase98UniversalComputerUseMode：函数段落开始，评估动作是否允许；如果没有这段函数，动作层无法在发送输入前做模式拦截。
        current = self.status()  # 新增代码+Phase98UniversalComputerUseMode：读取当前状态；如果没有这行代码，动作判断没有事实来源。
        action = str(action_class or "")  # 新增代码+Phase98UniversalComputerUseMode：规范化动作名；如果没有这行代码，None 动作会导致判断异常。
        if bool(current.get("stopped")):  # 新增代码+Phase98UniversalComputerUseMode：优先检查是否已急停；如果没有这行代码，stop 后动作可能继续执行。
            return {"allowed": False, "decision": "computer_use_stopped", "low_level_event_count": 0, "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK}  # 新增代码+Phase98UniversalComputerUseMode：返回急停拒绝且零低层事件；如果没有这行代码，测试无法确认 stop 真阻断。
        if bool(current.get("expired")):  # 新增代码+Phase98UniversalComputerUseMode：检查授权是否过期；如果没有这行代码，过期模式可能继续放行动作。
            return {"allowed": False, "decision": "mode_expired", "low_level_event_count": 0, "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK}  # 修改代码+Phase98UniversalComputerUseMode：返回计划约定的过期拒绝原因码且零低层事件；如果没有这行代码，Task3/99 会和旧原因码漂移。
        target_text = _phase98_window_text(window)  # 新增代码+Phase98UniversalComputerUseMode：提取窗口风险文本；如果没有这行代码，危险目标扫描没有输入。
        if any(term in target_text for term in DANGEROUS_TARGET_TERMS):  # 新增代码+Phase98UniversalComputerUseMode：匹配危险关键词；如果没有这行代码，终端和安全窗口可能被误操作。
            return {"allowed": False, "decision": "dangerous_target_blocked", "low_level_event_count": 0, "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK}  # 修改代码+Phase98UniversalComputerUseMode：返回计划约定的危险目标拒绝原因码且零低层事件；如果没有这行代码，Task3/99 会和旧原因码漂移。
        allowed_actions = list(current.get("allowed_action_classes", []))  # 新增代码+Phase98UniversalComputerUseMode：读取当前允许动作；如果没有这行代码，无法判断动作是否在模式范围内。
        if current.get("mode") == "observe" and action not in allowed_actions:  # 新增代码+Phase98UniversalComputerUseMode：观察模式下写动作专用拒绝；如果没有这行代码，测试要求的 observe_mode_blocks_write_action 不会出现。
            return {"allowed": False, "decision": "observe_mode_blocks_write_action", "low_level_event_count": 0, "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK}  # 新增代码+Phase98UniversalComputerUseMode：返回 observe 写动作拒绝且零低层事件；如果没有这行代码，observe 模式可能误发输入。
        if action not in allowed_actions:  # 新增代码+Phase98UniversalComputerUseMode：检查动作是否不在允许列表；如果没有这行代码，未知动作可能被误放行。
            return {"allowed": False, "decision": "action_class_not_allowed_by_mode", "low_level_event_count": 0, "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK}  # 新增代码+Phase98UniversalComputerUseMode：返回动作不允许且零低层事件；如果没有这行代码，拒绝原因不可审计。
        return {"allowed": True, "decision": "allowed_by_computer_use_mode", "low_level_event_count": 0, "marker": PHASE98_COMPUTER_USE_MODE_READY, "ok_token": PHASE98_COMPUTER_USE_MODE_OK}  # 修改代码+Phase98UniversalComputerUseMode：返回计划约定的允许原因码且仍不发送真实输入；如果没有这行代码，Task3/99 会和旧原因码漂移。
    # 新增代码+Phase98UniversalComputerUseMode：函数段落结束，ComputerUseModeSessionStore.evaluate_action 到此结束；如果没有这个边界说明，初学者不容易看出动作评估范围。
# 新增代码+Phase98UniversalComputerUseMode：类段落结束，ComputerUseModeSessionStore 到此结束；如果没有这个边界说明，初学者不容易看出 store 类范围。

__all__ = ["DEFAULT_MODE_SESSION_ID", "DEFAULT_MODE_SESSION_ROOT", "PHASE98_COMPUTER_USE_MODE_MODEL", "PHASE98_COMPUTER_USE_MODE_OK", "PHASE98_COMPUTER_USE_MODE_READY", "ComputerUseModeSessionStore"]  # 新增代码+Phase98UniversalComputerUseMode：限制公开导出名称；如果没有这行代码，from 模块 import * 可能暴露内部 helper。
