"""learning_agent 轻量 SDK 入口。"""  # 新增代码+StatusSDK: 说明 sdk 包给外部 agent 读取状态；若没有这行代码，包职责不清楚。

from __future__ import annotations  # 新增代码+StatusSDK: 延迟解析类型注解；若没有这行代码，后续导出类型更容易受顺序影响。

from learning_agent.sdk.status import get_status_snapshot, list_status_events, watch_status_events  # 新增代码+StatusSDK: 导出状态 SDK 函数；若没有这行代码，外部调用方要知道内部文件路径。

__all__ = ["get_status_snapshot", "list_status_events", "watch_status_events"]  # 新增代码+StatusSDK: 声明公开 API；若没有这行代码，自动补全和文档不清楚可用函数。
