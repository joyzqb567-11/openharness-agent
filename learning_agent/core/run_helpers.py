"""运行 id 和 observation 记录小工具。"""  # 新增代码+AgentPySplitPhase13: 说明本模块承接 agent.py 中轻量运行记录 helper；若没有这行代码，用户打开文件时不容易判断模块职责。

from __future__ import annotations  # 新增代码+AgentPySplitPhase13: 让类型注解延迟解析；若没有这行代码，复杂注解在部分运行方式下更容易提前求值出错。

import copy  # 新增代码+AgentPySplitPhase13: observation payload 需要深拷贝防止后续被调用方污染；若没有这行代码，历史事件可能被修改。
import secrets  # 新增代码+AgentPySplitPhase13: run_id/session_id 需要随机后缀避免同秒重名；若没有这行代码，连续运行可能覆盖记录。
import time  # 新增代码+AgentPySplitPhase13: run_id/session_id 和 observation 时间都需要当前时间；若没有这行代码，记录无法排序和辨认。
from typing import Any  # 新增代码+AgentPySplitPhase13: 用 Any 表示传入的 LearningAgent 上下文；若没有这行代码，新模块会为了类型注解反向导入 agent.py。


def record_observation(agent: Any, kind: str, payload: dict[str, Any]) -> None:  # 新增代码+AgentPySplitPhase13: 函数段开始，记录工具、策略、workflow 和结果持久化观察事件；若没有这段代码，agent.py 的 旧观察薄包装 薄包装没有真实实现。
    event = {  # 新增代码+AgentPySplitPhase13: 构造固定结构的观察事件；若没有这行代码，不同调用点会各自拼不兼容字段。
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),  # 新增代码+AgentPySplitPhase13: 保存事件发生时间；若没有这行代码，后续排查无法判断事件先后。
        "kind": kind,  # 新增代码+AgentPySplitPhase13: 保存事件类型，例如 mcp_call_progress 或 tool_result_offloaded；若没有这行代码，审计方无法按类别过滤。
        "payload": copy.deepcopy(payload),  # 新增代码+AgentPySplitPhase13: 保存事件载荷深拷贝；若没有这行代码，调用方后续修改参数会污染历史观察记录。
    }  # 新增代码+AgentPySplitPhase13: 观察事件字典结束；若没有这行代码，Python 语法不完整。
    agent.observation_events.append(event)  # 新增代码+AgentPySplitPhase13: 把事件加入当前 agent 的观察流；若没有这行代码，调用方无法回看结构化事件。
    agent.observation_events = agent.observation_events[-500:]  # 新增代码+AgentPySplitPhase13: 只保留最近 500 条避免长期运行内存无限增长；若没有这行代码，长会话会不断累积观察对象。
# 新增代码+AgentPySplitPhase13: 函数段结束，record_observation 到此结束；若没有这个边界说明，用户不容易看出 observation 记录逻辑已经迁到 core helper。


def safe_record_observation(agent: Any, kind: str, payload: dict[str, Any]) -> None:  # 新增代码+AgentPySplitPhase15B2: 函数段开始，给 executor、app 和轻量测试对象提供安全 observation 写入口；若没有这段代码，删除 agent.py 的 `旧观察薄包装` 后 fake agent 缺少 observation_events 会崩溃。
    if not hasattr(agent, "observation_events"):  # 新增代码+AgentPySplitPhase15B2: 先确认对象是否有观察事件列表；若没有这行代码，简化对象会在 append 时触发 AttributeError。
        return  # 新增代码+AgentPySplitPhase15B2: 没有观察流时静默跳过；若没有这行代码，工具执行器无法兼容只实现部分字段的测试对象。
    record_observation(agent, kind, payload)  # 新增代码+AgentPySplitPhase15B2: 有观察流时复用严格记录函数；若没有这行代码，真实 agent 的结构化事件不会写入 observation_events。
# 新增代码+AgentPySplitPhase15B2: 函数段结束，safe_record_observation 到此结束；若没有这个边界说明，用户不容易看出这是删除薄包装后的兼容安全入口。


def observation_recorder(agent: Any):  # 新增代码+AgentPySplitPhase15B2: 函数段开始，返回可传给模块的 observation 回调；若没有这段代码，agent.py 删除 `旧观察薄包装` 后每个回调点都要手写 lambda。
    return lambda kind, payload: record_observation(agent, kind, payload)  # 新增代码+AgentPySplitPhase15B2: 生成绑定当前 agent 的记录函数；若没有这行代码，Computer Use 图片、trace 和动作门禁模块拿不到统一记录入口。
# 新增代码+AgentPySplitPhase15B2: 函数段结束，observation_recorder 到此结束；若没有这个边界说明，用户不容易看出回调函数是在 core helper 层生成的。


def new_debug_run_id() -> str:  # 新增代码+AgentPySplitPhase13: 函数段开始，生成单轮请求的调试编号；若没有这段代码，agent.py 的 _new_debug_run_id 薄包装没有真实实现。
    timestamp = time.strftime("%Y%m%d_%H%M%S")  # 新增代码+AgentPySplitPhase13: 用当前时间生成易读前缀；若没有这行代码，debug run 文件名不容易按时间排序。
    return f"run_{timestamp}_{secrets.token_hex(4)}"  # 新增代码+AgentPySplitPhase13: 加随机后缀避免同一秒多次请求重名；若没有这行代码，连续运行可能覆盖调试记录。
# 新增代码+AgentPySplitPhase13: 函数段结束，new_debug_run_id 到此结束；若没有这个边界说明，用户不容易看出 debug run id 逻辑已经迁到 core helper。


def new_session_id() -> str:  # 新增代码+AgentPySplitPhase13: 函数段开始，生成事件 transcript 会话编号；若没有这段代码，agent.py 的 _new_session_id 薄包装没有真实实现。
    timestamp = time.strftime("%Y%m%d_%H%M%S")  # 新增代码+AgentPySplitPhase13: 用当前时间作为可读前缀；若没有这行代码，用户难以从目录名判断会话时间。
    return f"session_{timestamp}_{secrets.token_hex(4)}"  # 新增代码+AgentPySplitPhase13: 加随机后缀避免同一秒多次运行重名；若没有这行代码，连续运行可能覆盖 transcript。
# 新增代码+AgentPySplitPhase13: 函数段结束，new_session_id 到此结束；若没有这个边界说明，用户不容易看出 session id 逻辑已经迁到 core helper。

