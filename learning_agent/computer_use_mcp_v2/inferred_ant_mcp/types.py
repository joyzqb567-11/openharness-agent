"""Computer Use MCP v2 共享类型。"""  # 新增代码+ComputerUseMcpV2：说明本文件存放跨模块数据结构；如果没有这行代码，Context 可能被重复定义。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，循环引用更容易在导入时出错。

from dataclasses import dataclass, field  # 新增代码+ComputerUseMcpV2：导入 dataclass 简化上下文对象；如果没有这行代码，Context 初始化需要手写样板代码。
from typing import Any, Callable  # 新增代码+ComputerUseMcpV2：导入通用类型和回调类型；如果没有这行代码，agent-side 绑定字段含义不清楚。

from .claudecode_protocol import default_grant_flags  # 新增代码+ClaudeCodePermissionParity：导入 ClaudeCode grant flags 默认值；如果没有这行代码，Context 无法稳定保存剪贴板和系统组合键授权。


@dataclass  # 新增代码+ComputerUseMcpV2：自动生成初始化方法；如果没有这行代码，上下文字段越多越容易手写出错。
class ComputerUseMcpV2Context:  # 新增代码+ComputerUseMcpV2：类段开始，保存一次 v2 MCP 调用链共享的宿主、权限、trace 和状态；如果没有这段类，stdio server 和 agent-side wrapper 无法共享能力。
    host: Any | None = None  # 新增代码+ComputerUseMcpV2：保存 Windows 宿主适配器或测试 fake host；如果没有这一行，runtime 无法执行真实鼠标键盘或 fake 测试动作。
    ask_permission: Callable[[str], bool] | None = None  # 新增代码+ComputerUseMcpV2：保存 agent 主循环授权回调；如果没有这一行，request_access 不能复用用户确认能力。
    record_observation: Callable[[str, dict[str, Any]], None] | None = None  # 新增代码+ComputerUseMcpV2：保存观察事件回调；如果没有这一行，observe/screenshot 证据不会回到 agent。
    record_runtime_trace: Callable[[dict[str, Any]], None] | None = None  # 新增代码+ComputerUseMcpV2：保存 runtime trace 回调；如果没有这一行，工具执行链无法证明走的是 v2。
    emit_acceptance_event: Callable[[str, dict[str, Any]], None] | None = None  # 新增代码+ComputerUseMcpV2：保存可见终端验收事件回调；如果没有这一行，真实场景验收缺少事件桥。
    computer_use_session_id: str = "computer-use-mcp-v2-session"  # 新增代码+ClaudeCodeLockParity：保存本轮 Computer Use 会话 id；如果没有这一行，lock/cleanup 回调不知道释放或检查哪个会话。
    check_computer_use_lock: Callable[[str], dict[str, Any]] | None = None  # 新增代码+ClaudeCodeLockParity：保存只检查锁状态的回调；如果没有这一行，request_access/list_granted 无法按 ClaudeCode 语义只检查不抢锁。
    acquire_computer_use_lock: Callable[[str], dict[str, Any]] | None = None  # 新增代码+ClaudeCodeLockParity：保存取桌面控制锁的回调；如果没有这一行，screenshot/click 等工具无法先拿独占锁再执行。
    release_computer_use_lock: Callable[[str], dict[str, Any]] | None = None  # 新增代码+ClaudeCodeLockParity：保存释放桌面控制锁的回调；如果没有这一行，turn cleanup 没有轻量释放兜底。
    cleanup_after_turn: Callable[[str], dict[str, Any]] | None = None  # 新增代码+ClaudeCodeLockParity：保存 turn 结束完整 cleanup 回调；如果没有这一行，锁释放、abort 清理和宿主窗口恢复无法统一收口。
    is_lock_held_locally: Callable[[str], bool] | None = None  # 新增代码+ClaudeCodeLockParity：保存本会话是否持锁的判断回调；如果没有这一行，debug 无法说明 acquire 后是否本地持锁。
    grants: dict[str, Any] = field(default_factory=dict)  # 新增代码+ComputerUseMcpV2：保存本会话授权摘要；如果没有这一行，list_granted_applications 没有状态来源。
    allowed_apps: list[dict[str, str]] = field(default_factory=list)  # 新增代码+ClaudeCodePermissionParity：保存 ClaudeCode 风格 app allowlist；如果没有这一行，多轮工具无法知道哪些应用已授权。
    grant_flags: dict[str, bool] = field(default_factory=default_grant_flags)  # 新增代码+ClaudeCodePermissionParity：保存剪贴板和系统组合键授权开关；如果没有这一行，权限层无法表达细粒度 grant flags。
    sentinel_warnings: list[dict[str, str]] = field(default_factory=list)  # 新增代码+ClaudeCodePermissionParity：保存高风险应用提示；如果没有这一行，PowerShell/系统设置等风险不会进入查询结果。
    denied_apps: list[dict[str, str]] = field(default_factory=list)  # 新增代码+ClaudeCodePermissionParity：保存用户拒绝的应用；如果没有这一行，拒绝路径无法被审计和恢复。
    selected_display_id: str = ""  # 新增代码+ClaudeCodeDisplayParity：保存 ClaudeCode 风格 selectedDisplayId 的内部 snake_case 状态；如果没有这一行，多显示器场景无法记住模型当前选中的屏幕。
    display_pinned_by_model: bool = False  # 新增代码+ClaudeCodeDisplayParity：保存模型是否临时固定显示器；如果没有这一行，cleanup 无法按 ClaudeCode 语义清理临时 pin。
    display_resolved_for_apps: list[dict[str, Any]] = field(default_factory=list)  # 新增代码+ClaudeCodeDisplayParity：保存 app 到 display 的解析记录；如果没有这一行，模型看不到某个应用最终落在哪块屏幕。
    last_screenshot_dims: dict[str, int] = field(default_factory=dict)  # 新增代码+ClaudeCodeDisplayParity：保存最近一次截图宽高；如果没有这一行，后续 zoom/坐标推理缺少最近截图尺寸事实。
    clipboard_text: str = ""  # 新增代码+ComputerUseMcpV2：保存受控内存剪贴板文本；如果没有这一行，write_clipboard/read_clipboard 无法形成最小闭环。
# 新增代码+ComputerUseMcpV2：类段结束，ComputerUseMcpV2Context 到此结束；如果没有这个边界说明，用户不容易看出 v2 上下文生命周期。

