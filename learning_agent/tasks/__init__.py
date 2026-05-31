# 新增代码+TasksSplit: tasks 包用于承载后台命令、task、team、cron 和 monitor 教学版能力；如果没有这个包，长期任务逻辑会继续散落在主文件里。
from .background import BackgroundCommand, background_command_status, drain_text_queue  # 新增代码+TasksSplit: 导出后台命令记录和输出 helper；如果没有这行代码，主 agent 和测试无法从 tasks 包复用后台命令边界。
from .cron_monitor import CronRecord, MonitorRecord, cron_monitor_max_results, cron_monitor_state, format_cron_record, format_monitor_record, monitor_result_status  # 新增代码+TasksSplit: 导出 Cron/Monitor 记录与格式化 helper；如果没有这行代码，定时和监控逻辑没有稳定包入口。
from .task_runs import BLOCKED_TASK_TOOL_NAMES, TaskRun, task_background_enabled, task_child_prompt  # 新增代码+TasksSplit: 导出子任务记录和 task 参数 helper；如果没有这行代码，子 agent 生命周期仍难以复用。
from .team import TeamMessage, TeamPeer, peer_status_from_pending_count  # 新增代码+TasksSplit: 导出教学版 team 通信记录；如果没有这行代码，peer/message 数据结构仍没有稳定入口。

__all__ = [  # 新增代码+TasksSplit: 明确 tasks 包公开 API；如果没有这行代码，外部 agent 不容易知道哪些名字可以稳定引用。
    "BackgroundCommand",  # 新增代码+TasksSplit: 公开后台命令记录；如果没有这行代码，外部无法稳定引用后台命令状态对象。
    "BLOCKED_TASK_TOOL_NAMES",  # 新增代码+TasksSplit: 公开子 agent 禁止继承工具集合；如果没有这行代码，任务权限边界难以测试。
    "CronRecord",  # 新增代码+TasksSplit: 公开定时任务记录；如果没有这行代码，cron 记录无法从包入口引用。
    "MonitorRecord",  # 新增代码+TasksSplit: 公开监控记录；如果没有这行代码，monitor 记录无法从包入口引用。
    "TaskRun",  # 新增代码+TasksSplit: 公开子任务记录；如果没有这行代码，task 生命周期无法从包入口引用。
    "TeamMessage",  # 新增代码+TasksSplit: 公开 team 消息记录；如果没有这行代码，peer inbox 数据结构无法从包入口引用。
    "TeamPeer",  # 新增代码+TasksSplit: 公开 team 成员记录；如果没有这行代码，team_create 数据结构无法从包入口引用。
    "background_command_status",  # 新增代码+TasksSplit: 公开后台命令状态格式化 helper；如果没有这行代码，状态文本仍会散在主文件。
    "cron_monitor_max_results",  # 新增代码+TasksSplit: 公开 cron/monitor 最大结果解析 helper；如果没有这行代码，列表长度规则无法复用。
    "cron_monitor_state",  # 新增代码+TasksSplit: 公开 cron/monitor 状态解析 helper；如果没有这行代码，筛选状态规则无法复用。
    "drain_text_queue",  # 新增代码+TasksSplit: 公开后台输出队列读取 helper；如果没有这行代码，后台输出读取规则无法复用。
    "format_cron_record",  # 新增代码+TasksSplit: 公开 cron 记录格式化 helper；如果没有这行代码，列表输出格式难以保持一致。
    "format_monitor_record",  # 新增代码+TasksSplit: 公开 monitor 记录格式化 helper；如果没有这行代码，列表输出格式难以保持一致。
    "monitor_result_status",  # 新增代码+TasksSplit: 公开 monitor 结果状态解析 helper；如果没有这行代码，状态标准化无法复用。
    "peer_status_from_pending_count",  # 新增代码+TasksSplit: 公开 peer 状态计算 helper；如果没有这行代码，ack 后状态更新规则会分散。
    "task_background_enabled",  # 新增代码+TasksSplit: 公开 task 后台参数解析 helper；如果没有这行代码，background 参数兼容性无法单独测试。
    "task_child_prompt",  # 新增代码+TasksSplit: 公开子 agent prompt 构造 helper；如果没有这行代码，子任务提示词边界仍藏在主文件。
]  # 新增代码+TasksSplit: 结束公开 API 列表；如果没有这行代码，Python 列表语法无法闭合。
