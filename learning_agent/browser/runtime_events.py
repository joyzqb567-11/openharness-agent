"""浏览器运行时事件名常量。"""  # 新增代码+BrowserRuntimeStore: 说明本文件集中保存 browser runtime JSONL 事件名；若没有这行代码，事件协议职责不清楚。

from __future__ import annotations  # 新增代码+BrowserRuntimeStore: 延迟解析类型注解；若没有这行代码，后续扩展类型引用更容易受定义顺序影响。

BROWSER_RUN_CREATED = "browser_run_created"  # 新增代码+BrowserRuntimeStore: 表示浏览器 run 已创建；若没有这行代码，事件日志无法稳定标记任务入口。
BROWSER_RUN_SAVED = "browser_run_saved"  # 新增代码+BrowserRuntimeStore: 表示浏览器 run 状态已保存；若没有这行代码，通用保存事件缺少统一名称。
BROWSER_STAGE_COMPLETED = "browser_stage_completed"  # 新增代码+BrowserRuntimeStore: 表示浏览器阶段已完成；若没有这行代码，resume 无法从事件层看见阶段门禁。
BROWSER_ACTION_RECORDED = "browser_action_recorded"  # 新增代码+BrowserRuntimeStore: 表示浏览器动作已记录；若没有这行代码，默认动作事件名会散落。
BROWSER_ACTION_STARTED = "browser_action_started"  # 新增代码+BrowserRuntimeStore: 表示浏览器动作开始；若没有这行代码，状态生态看不到工具开始。
BROWSER_ACTION_COMPLETED = "browser_action_completed"  # 新增代码+BrowserRuntimeStore: 表示浏览器动作完成；若没有这行代码，状态生态看不到工具收尾。
BROWSER_ACTION_FAILED = "browser_action_failed"  # 新增代码+BrowserRuntimeStore: 表示浏览器动作失败；若没有这行代码，恢复管理器无法统一订阅失败。
BROWSER_OBSERVATION_RECORDED = "browser_observation_recorded"  # 新增代码+BrowserRuntimeStore: 表示页面观察结果已记录；若没有这行代码，verifier 难以找到页面证据事件。
BROWSER_PROVIDER_DECISION = "browser_provider_decision"  # 新增代码+BrowserProviderRouter: 表示浏览器 provider 路由决策已记录；若没有这行代码，状态生态无法稳定订阅 provider 选择。
BROWSER_RECORDING_STARTED = "browser_recording_started"  # 新增代码+BrowserRecordingStage9: 表示浏览器录制已经开始；若没有这行代码，事件流无法复盘何时开启视觉证据。
BROWSER_RECORDING_FRAME = "browser_recording_frame"  # 新增代码+BrowserRecordingStage9: 表示一次浏览器截图帧已保存；若没有这行代码，事件流无法追踪每个动作的视觉帧。
BROWSER_RECORDING_STOPPED = "browser_recording_stopped"  # 新增代码+BrowserRecordingStage9: 表示浏览器录制已经停止；若没有这行代码，长任务状态不知道录制是否收尾。
BROWSER_GIF_EXPORTED = "browser_gif_exported"  # 新增代码+BrowserRecordingStage9: 表示帧序列已导出 GIF；若没有这行代码，verifier 和状态页缺少可订阅导出事件。
BROWSER_RECOVERY_STOPPED = "browser_recovery_stopped"  # 新增代码+BrowserFallbackStage10: 表示连续浏览器失败已经触发停止；若没有这行代码，事件流无法审计为什么 agent 不再继续乱试。

BROWSER_RUNTIME_EVENT_TYPES = (BROWSER_RUN_CREATED, BROWSER_RUN_SAVED, BROWSER_STAGE_COMPLETED, BROWSER_ACTION_RECORDED, BROWSER_ACTION_STARTED, BROWSER_ACTION_COMPLETED, BROWSER_ACTION_FAILED, BROWSER_OBSERVATION_RECORDED, BROWSER_PROVIDER_DECISION, BROWSER_RECORDING_STARTED, BROWSER_RECORDING_FRAME, BROWSER_RECORDING_STOPPED, BROWSER_GIF_EXPORTED, BROWSER_RECOVERY_STOPPED)  # 修改代码+BrowserFallbackStage10: 暴露全部稳定事件名并加入连续失败停止事件；若没有这行代码，CLI/API 无法确认停止保护属于正式浏览器 runtime。
