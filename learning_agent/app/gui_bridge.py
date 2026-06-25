"""Desktop GUI bridge for the OpenHarness local desktop shell."""  # 新增代码+DesktopGUIBridge: 说明本模块只服务桌面 GUI；如果没有这行代码，维护者容易把它和通用 HTTP bridge 混淆。
from __future__ import annotations  # 新增代码+DesktopGUIBridge: 延迟解析类型注解；如果没有这行代码，后续类型引用更容易受导入顺序影响。

from pathlib import Path  # 新增代码+DesktopGUIBridge: 使用 Path 规范化工作区；如果没有这行代码，字符串路径处理容易分裂。
from typing import Any  # 新增代码+DesktopGUIBridge: 描述 JSON payload 的通用值；如果没有这行代码，接口类型边界不清楚。

from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+DesktopGUIBridge: 复用统一状态事实源；如果没有这行代码，GUI 会和 CLI/SDK 状态分裂。


GUI_SCHEMA_VERSION = 1  # 新增代码+DesktopGUIBridge: 固定 GUI bridge 协议版本；如果没有这行代码，前端无法判断响应兼容性。


def build_gui_bootstrap_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIBridge: 函数段开始，生成 GUI 启动首屏数据；如果没有这段函数，桌面壳需要调用多个后端端点拼状态。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUIBridge: 规范化工作区路径；如果没有这行代码，相对路径会导致前端项目身份不稳定。
    snapshot = build_status_snapshot(workspace_path)  # 新增代码+DesktopGUIBridge: 读取统一状态快照；如果没有这行代码，GUI 没有 run/task/session/browser 数据。
    return {  # 新增代码+DesktopGUIBridge: 返回稳定 JSON 对象；如果没有这行代码，前端无法渲染启动页。
        "ok": True,  # 新增代码+DesktopGUIBridge: 标记请求成功；如果没有这行代码，前端要靠异常猜测状态。
        "workspace": str(workspace_path),  # 新增代码+DesktopGUIBridge: 返回当前项目路径；如果没有这行代码，侧栏无法显示项目身份。
        "app": {"name": "OpenHarness Desktop", "schema_version": GUI_SCHEMA_VERSION},  # 新增代码+DesktopGUIBridge: 返回应用名和协议版本；如果没有这行代码，前端无法做兼容判断。
        "snapshot": snapshot,  # 新增代码+DesktopGUIBridge: 返回统一状态快照；如果没有这行代码，首屏看不到任务和会话。
        "feature_flags": {  # 新增代码+DesktopGUIBridge: 返回能力开关；如果没有这行代码，前端无法按后端能力显示 UI。
            "chat_run": True,  # 新增代码+DesktopGUIBridge: 声明可发起聊天运行；如果没有这行代码，输入框无法判断是否可用。
            "event_polling": True,  # 新增代码+DesktopGUIBridge: 声明当前使用事件轮询；如果没有这行代码，前端无法启动 watcher。
            "browser_panel": True,  # 新增代码+DesktopGUIBridge: 声明可显示浏览器状态；如果没有这行代码，浏览器面板会误隐藏。
            "computer_use_panel": True,  # 新增代码+DesktopGUIBridge: 声明可显示 Computer Use 状态；如果没有这行代码，权限面板会误隐藏。
            "streaming": False,  # 新增代码+DesktopGUIBridge: 第一阶段不声明真实流式输出；如果没有这行代码，前端可能误等 SSE。
        },  # 新增代码+DesktopGUIBridge: feature_flags 对象结束；如果没有这行代码，Python 语法不完整。
    }  # 新增代码+DesktopGUIBridge: bootstrap payload 结束；如果没有这行代码，函数没有返回值。
# 新增代码+DesktopGUIBridge: 函数段结束，build_gui_bootstrap_payload 到此结束；如果没有这个边界说明，用户不容易看出它只负责首屏数据。
