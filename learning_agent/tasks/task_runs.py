"""子 agent 任务记录和轻量 helper。"""  # 新增代码+TasksSplit: 说明本模块承载 task 子 agent 生命周期的纯数据和 helper；如果没有这行代码，用户难以快速定位 task 记录定义。

from __future__ import annotations  # 新增代码+TasksSplit: 允许类型注解延迟解析；如果没有这行代码，线程等类型标注更容易受定义顺序影响。

import threading  # 新增代码+TasksSplit: TaskRun 需要保存 stop_event 和后台线程对象；如果没有这行代码，任务取消和线程字段无法类型化。
from dataclasses import dataclass  # 新增代码+TasksSplit: 用 dataclass 定义只保存状态的数据对象；如果没有这行代码，任务记录要手写初始化方法。


BLOCKED_TASK_TOOL_NAMES = {"task", "task_output", "task_stop", "task_list", "task_get", "task_update"}  # 新增代码+TasksSplit: 集中保存禁止子 agent 递归或管理父任务的工具名；如果没有这行代码，递归 task 风险会散落在主文件。


@dataclass  # 新增代码+TasksSplit: 自动生成子任务记录初始化方法；如果没有这行代码，task_output/task_stop 只能依赖松散字典且字段容易写错。
class TaskRun:  # 新增代码+TasksSplit: 保存一次 task 子 agent 运行的生命周期信息；如果没有这行代码，子任务完成后无法被查询或停止。
    task_id: str  # 新增代码+TasksSplit: 保存子任务唯一 id；如果没有这行代码，task_output/task_stop 无法定位具体子任务。
    prompt: str  # 新增代码+TasksSplit: 保存原始子任务提示词；如果没有这行代码，查询任务时无法知道它当初要做什么。
    allowed_tool_names: set[str]  # 新增代码+TasksSplit: 保存子 agent 可见工具白名单；如果没有这行代码，task_output 无法展示任务权限边界。
    max_turns: int  # 新增代码+TasksSplit: 保存子 agent 最大轮次；如果没有这行代码，查询任务时无法知道执行约束。
    status: str  # 新增代码+TasksSplit: 保存 pending/running/completed/failed/stopped 状态；如果没有这行代码，task_output 无法说明任务是否结束。
    label: str = ""  # 新增代码+TasksSplit: 保存用户或模型给子任务补充的短标签；如果没有这行代码，task_list 中多个任务只能靠长 prompt 区分。
    notes: str = ""  # 新增代码+TasksSplit: 保存任务备注或交接说明；如果没有这行代码，task_update 无法给任务留下可读管理信息。
    output: str = ""  # 新增代码+TasksSplit: 保存子 agent 最终输出；如果没有这行代码，task_output 无法读回任务结果。
    error: str = ""  # 新增代码+TasksSplit: 保存子任务失败原因；如果没有这行代码，失败任务只剩空输出不利于排查。
    created_at: str = ""  # 新增代码+TasksSplit: 保存任务创建时间；如果没有这行代码，用户无法判断任务何时启动。
    completed_at: str = ""  # 新增代码+TasksSplit: 保存任务结束时间；如果没有这行代码，用户无法判断任务何时完成或停止。
    stop_requested: bool = False  # 新增代码+TasksSplit: 保存是否收到停止请求；如果没有这行代码，task_stop 无法记录用户取消意图。
    background: bool = False  # 新增代码+TasksSplit: 标记子任务是否后台运行；如果没有这行代码，task_output 无法区分同步任务和后台任务。
    stop_event: threading.Event | None = None  # 新增代码+TasksSplit: 保存后台子任务的协作取消信号；如果没有这行代码，task_stop 无法通知正在运行的子 agent 停止。
    thread: threading.Thread | None = None  # 新增代码+TasksSplit: 保存后台线程对象；如果没有这行代码，task_stop 和测试无法观察后台子任务线程状态。


def task_background_enabled(raw_background: object) -> bool:  # 新增代码+TasksSplit: 统一解析 task.background 参数；如果没有这行代码，模型传入布尔或字符串时语义可能不一致。
    if isinstance(raw_background, bool):  # 新增代码+TasksSplit: 优先接受 JSON boolean；如果没有这行代码，标准 schema 输出的 true/false 不能稳定识别。
        return raw_background  # 新增代码+TasksSplit: 原样返回布尔值；如果没有这行代码，true 可能被错误当作 false。
    if isinstance(raw_background, str):  # 新增代码+TasksSplit: 兼容模型偶尔把布尔写成字符串；如果没有这行代码，"true" 会被当作同步执行。
        return raw_background.strip().lower() in {"true", "1", "yes", "y"}  # 新增代码+TasksSplit: 识别常见真值字符串；如果没有这行代码，CLI 或模型文本参数兼容性更差。
    return False  # 新增代码+TasksSplit: 省略或其他类型默认同步执行；如果没有这行代码，异常类型可能误触发后台任务。


def task_child_prompt(prompt: str) -> str:  # 新增代码+TasksSplit: 构造子 agent 专用 prompt；如果没有这行代码，子 agent 缺少统一执行边界说明。
    return "你是由主 agent 调起的子 agent。请只完成下面这个子任务，并在最后用简短中文 summary 返回给主 agent。\n\n子任务：\n" + prompt  # 新增代码+TasksSplit: 拼接委派说明和原始子任务；如果没有这行代码，子 agent 可能不知道输出应服务于主 agent 汇总。
