"""教学版 cron/monitor 进程内记录和格式化 helper。"""  # 新增代码+TasksSplit: 说明本模块承载定时和监控的纯记录逻辑；如果没有这行代码，cron/monitor 边界不清楚。

from __future__ import annotations  # 新增代码+TasksSplit: 允许类型注解延迟解析；如果没有这行代码，后续扩展类型时更容易受定义顺序影响。

from dataclasses import dataclass  # 新增代码+TasksSplit: 用 dataclass 定义只保存状态的数据对象；如果没有这行代码，记录类需要手写初始化方法。
from typing import Any  # 新增代码+TasksSplit: helper 接收模型 JSON 参数的任意值；如果没有这行代码，类型标注只能省略。


@dataclass  # 新增代码+TasksSplit: 自动生成定时任务记录初始化方法；如果没有这行代码，cron_create/list/delete 只能依赖松散字典且字段容易写错。
class CronRecord:  # 新增代码+TasksSplit: 保存一个教学版进程内定时任务记录；如果没有这行代码，cron_list 和 cron_delete 无法追踪已登记任务。
    cron_id: str  # 新增代码+TasksSplit: 保存定时任务唯一 id；如果没有这行代码，cron_delete 无法引用具体记录。
    name: str  # 新增代码+TasksSplit: 保存定时任务短名称；如果没有这行代码，多个定时任务只能靠长 prompt 区分。
    schedule: str  # 新增代码+TasksSplit: 保存用户可读的触发时间说明；如果没有这行代码，用户无法知道这条记录计划何时检查。
    prompt: str  # 新增代码+TasksSplit: 保存到点时应该执行或检查的任务说明；如果没有这行代码，定时记录只有时间没有工作内容。
    stop_condition: str  # 新增代码+TasksSplit: 保存停止条件；如果没有这行代码，长期记录缺少明确收束边界。
    state: str  # 新增代码+TasksSplit: 保存 active/deleted 状态；如果没有这行代码，cron_list 无法筛选有效和已删除记录。
    created_at: str  # 新增代码+TasksSplit: 保存创建时间；如果没有这行代码，用户无法判断记录登记顺序。
    deleted_at: str = ""  # 新增代码+TasksSplit: 保存删除时间；如果没有这行代码，删除后的审计信息会丢失。


@dataclass  # 新增代码+TasksSplit: 自动生成监控记录初始化方法；如果没有这行代码，monitor 多动作工具只能依赖松散字典且字段容易写错。
class MonitorRecord:  # 新增代码+TasksSplit: 保存一个教学版进程内监控记录；如果没有这行代码，monitor list/delete/record_result 无法追踪目标。
    monitor_id: str  # 新增代码+TasksSplit: 保存监控记录唯一 id；如果没有这行代码，monitor 后续动作无法引用具体记录。
    name: str  # 新增代码+TasksSplit: 保存监控短名称；如果没有这行代码，多个监控记录难以区分。
    target: str  # 新增代码+TasksSplit: 保存要观察的目标；如果没有这行代码，监控记录不知道关注什么对象。
    condition: str  # 新增代码+TasksSplit: 保存触发或关注条件；如果没有这行代码，监控记录不知道什么情况算命中。
    check_interval: str  # 新增代码+TasksSplit: 保存检查频率说明；如果没有这行代码，用户无法知道预计多久复查一次。
    stop_condition: str  # 新增代码+TasksSplit: 保存停止监控的条件；如果没有这行代码，长期监控缺少收束边界。
    state: str  # 新增代码+TasksSplit: 保存 active/deleted 状态；如果没有这行代码，monitor list 无法筛选有效和已删除记录。
    created_at: str  # 新增代码+TasksSplit: 保存创建时间；如果没有这行代码，用户无法判断监控登记顺序。
    last_result: str = ""  # 新增代码+TasksSplit: 保存最近一次人工或工具观察结果；如果没有这行代码，monitor 无法留下检查证据。
    last_status: str = "pending"  # 新增代码+TasksSplit: 保存最近一次观察状态；如果没有这行代码，列表无法快速显示是否触发条件。
    last_checked_at: str = ""  # 新增代码+TasksSplit: 保存最近一次记录结果的时间；如果没有这行代码，用户无法判断监控结果是否新鲜。
    deleted_at: str = ""  # 新增代码+TasksSplit: 保存删除时间；如果没有这行代码，删除后的审计信息会丢失。


def cron_monitor_state(raw_value: Any) -> str:  # 新增代码+TasksSplit: 解析 Cron/Monitor 列表筛选状态；如果没有这行代码，active/deleted/all 处理会继续重复。
    state = str(raw_value or "active").strip().lower()  # 新增代码+TasksSplit: 读取状态并默认 active；如果没有这行代码，无参数列表行为不明确。
    if state in {"all", "active", "deleted"}:  # 新增代码+TasksSplit: 只接受三种稳定状态；如果没有这行代码，任意字符串会导致筛选结果迷惑。
        return state  # 新增代码+TasksSplit: 返回有效状态；如果没有这行代码，调用方拿不到标准化结果。
    return "active"  # 新增代码+TasksSplit: 非法状态回退 active；如果没有这行代码，模型一次传错会得到空列表或异常。


def cron_monitor_max_results(raw_value: Any) -> int:  # 新增代码+TasksSplit: 解析 Cron/Monitor 列表最大返回数；如果没有这行代码，输出长度控制会重复。
    try:  # 新增代码+TasksSplit: 捕获模型传入非数字值的情况；如果没有这行代码，int() 异常会中断工具调用。
        value = int(raw_value) if raw_value is not None else 10  # 新增代码+TasksSplit: None 使用默认 10，否则尝试转整数；如果没有这行代码，省略 max_results 时没有默认值。
    except (TypeError, ValueError):  # 新增代码+TasksSplit: 处理无法转成整数的参数；如果没有这行代码，坏参数会让工具崩溃。
        value = 10  # 新增代码+TasksSplit: 非法 max_results 回退默认值；如果没有这行代码，模型一次传错参数就无法继续列表。
    return max(1, min(value, 20))  # 新增代码+TasksSplit: 把结果数限制在 1 到 20；如果没有这行代码，0 或超大值会导致结果为空或撑爆上下文。


def monitor_result_status(raw_value: Any) -> str:  # 新增代码+TasksSplit: 解析 monitor 最近观察状态；如果没有这行代码，状态标准化会散落在结果记录逻辑里。
    result_status = str(raw_value or "ok").strip().lower()  # 新增代码+TasksSplit: 读取状态并默认 ok；如果没有这行代码，省略 result_status 时行为不明确。
    if result_status in {"ok", "triggered", "blocked", "error"}:  # 新增代码+TasksSplit: 只接受稳定状态集合；如果没有这行代码，列表状态可能出现任意字符串。
        return result_status  # 新增代码+TasksSplit: 返回有效状态；如果没有这行代码，调用方拿不到标准化结果。
    return "ok"  # 新增代码+TasksSplit: 非法状态回退 ok；如果没有这行代码，模型传错状态会污染记录。


def format_cron_record(record: CronRecord) -> str:  # 新增代码+TasksSplit: 把定时任务记录格式化成稳定多字段文本；如果没有这行代码，创建和列表输出格式容易不一致。
    return f"- cron_id={record.cron_id} state={record.state} name={record.name} schedule={record.schedule} created_at={record.created_at} prompt={record.prompt} stop_condition={record.stop_condition or '(未设置)'}"  # 新增代码+TasksSplit: 返回单行可审计记录；如果没有这行代码，用户无法快速查看定时任务核心字段。


def format_monitor_record(record: MonitorRecord) -> str:  # 新增代码+TasksSplit: 把监控记录格式化成稳定多字段文本；如果没有这行代码，列表输出格式容易不一致。
    return f"- monitor_id={record.monitor_id} state={record.state} name={record.name} target={record.target} condition={record.condition} check_interval={record.check_interval} last_status={record.last_status} last_checked_at={record.last_checked_at or '(未检查)'} last_result={record.last_result or '(无结果)'}"  # 新增代码+TasksSplit: 返回单行可审计记录；如果没有这行代码，用户无法快速查看监控目标和最近结果。
