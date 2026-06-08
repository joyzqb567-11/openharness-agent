"""真实终端验收事件协议，供外部 agent 稳定观察 learning_agent 状态。"""  # 新增代码+ObservabilitySplit: 说明本模块专门承载验收事件；若没有这行代码，读代码的人不知道验收协议已经迁入观测层。
from __future__ import annotations  # 新增代码+ObservabilitySplit: 允许类型注解延迟解析；若没有这行代码，较新的类型写法在旧解释顺序下更容易出问题。

import json  # 新增代码+ObservabilitySplit: 使用标准库把事件写成 JSONL；若没有这行代码，控制器无法稳定解析事件。
import os  # 新增代码+ObservabilitySplit: 读取验收日志环境变量；若没有这行代码，外部控制器无法按需打开事件记录。
import sys  # 新增代码+ObservabilitySplit: 默认把事件标记打印到真实终端；若没有这行代码，可见终端里不会出现机器可读状态行。
import time  # 新增代码+ObservabilitySplit: 给事件补充本机时间戳；若没有这行代码，排查验收顺序时缺少时间线。
from pathlib import Path  # 新增代码+ObservabilitySplit: 使用 Path 安全处理 Windows 路径；若没有这行代码，日志路径拼接更容易出错。
from typing import Any, Mapping, TextIO  # 新增代码+ObservabilitySplit: 标注 payload、环境变量和输出流类型；若没有这行代码，后续维护者更难看懂入口参数。

ACCEPTANCE_EVENT_ENV_VAR = "LEARNING_AGENT_ACCEPTANCE_EVENT_LOG"  # 新增代码+ObservabilitySplit: 统一验收事件日志开关名；若没有这行代码，控制器和 agent 可能使用不同环境变量。
ACCEPTANCE_EVENT_MARKER_PREFIX = "::learning-agent-acceptance "  # 新增代码+ObservabilitySplit: 统一真实终端机器可读前缀；若没有这行代码，UI 自动化只能靠截图猜状态。
ACCEPTANCE_EVENT_STDOUT_ENV_VAR = "LEARNING_AGENT_ACCEPTANCE_EVENT_STDOUT"  # 修改代码+AcceptanceStdoutNoiseControl: 定义是否把验收事件同步打印到终端的显式开关；若没有这行代码，机器事件只能继续默认污染人类 UI。


def resolve_acceptance_event_log_path(environ: Mapping[str, str] | None = None) -> Path | None:  # 新增代码+ObservabilitySplit: 解析当前验收事件日志路径；若没有这行代码，事件写入函数会混杂环境读取细节。
    source_environ = os.environ if environ is None else environ  # 新增代码+ObservabilitySplit: 默认读真实环境，也允许测试传入假环境；若没有这行代码，单元测试会污染进程环境。
    raw_path = source_environ.get(ACCEPTANCE_EVENT_ENV_VAR, "").strip()  # 新增代码+ObservabilitySplit: 读取并清理日志路径文本；若没有这行代码，空格路径会导致错误写入位置。
    if not raw_path:  # 新增代码+ObservabilitySplit: 未配置路径时进入静默模式；若没有这行代码，普通用户交互会产生不必要事件文件。
        return None  # 新增代码+ObservabilitySplit: 用 None 表示验收日志未启用；若没有这行代码，调用方无法区分关闭状态和真实路径。
    return Path(raw_path).expanduser()  # 新增代码+ObservabilitySplit: 支持用户路径中的 ~ 并返回 Path；若没有这行代码，路径处理会分散到调用方。


def build_acceptance_event(state: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+ObservabilitySplit: 构造统一验收事件对象；若没有这行代码，不同调用点会手写不一致 JSON。
    event_payload = {} if payload is None else payload  # 新增代码+ObservabilitySplit: 没有 payload 时使用空字典；若没有这行代码，消费者还要处理 None 分支。
    return {  # 新增代码+ObservabilitySplit: 返回标准事件字典；若没有这行代码，调用方拿不到可写入的结构化事件。
        "schema_version": 1,  # 新增代码+ObservabilitySplit: 固定协议版本号；若没有这行代码，未来升级时无法判断兼容性。
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),  # 新增代码+ObservabilitySplit: 记录本机可读时间；若没有这行代码，排查终端时序会更难。
        "state": state,  # 新增代码+ObservabilitySplit: 保存当前 agent 状态名；若没有这行代码，外部控制器不知道该等待什么事件。
        "payload": event_payload,  # 新增代码+ObservabilitySplit: 保存状态附带信息；若没有这行代码，控制器无法确认工作区、动作或回答内容。
    }  # 新增代码+ObservabilitySplit: 结束事件字典；若没有这行代码，Python 字典语法不完整。


def acceptance_event_stdout_enabled(environ: Mapping[str, str] | None = None) -> bool:  # 修改代码+AcceptanceStdoutNoiseControl: 函数段开始，判断验收事件是否需要同步打印到终端；若没有这段代码，controller 事件会继续混进普通用户界面。本段只控制 stdout，不影响 JSONL 事件文件，段落到 return 结束。
    source_environ = os.environ if environ is None else environ  # 修改代码+AcceptanceStdoutNoiseControl: 默认读取真实环境，也允许测试传入假环境；若没有这行代码，单元测试会污染全局环境变量。
    raw_value = source_environ.get(ACCEPTANCE_EVENT_STDOUT_ENV_VAR, "").strip().lower()  # 修改代码+AcceptanceStdoutNoiseControl: 读取并规范化 stdout 开关；若没有这行代码，用户无法通过环境变量显式打开终端机器标记。
    return raw_value in {"1", "true", "yes", "y", "on"}  # 修改代码+AcceptanceStdoutNoiseControl: 只有明确真值才打印机器标记；若没有这行代码，默认仍会把 JSON 刷到人类终端。


def emit_acceptance_event(state: str, payload: dict[str, Any] | None = None, *, stream: TextIO | None = None, environ: Mapping[str, str] | None = None) -> dict[str, Any] | None:  # 新增代码+ObservabilitySplit: 写入一条验收事件并返回事件对象；若没有这行代码，外部 agent 没有统一观测入口。
    event_log_path = resolve_acceptance_event_log_path(environ)  # 新增代码+ObservabilitySplit: 根据环境变量决定是否启用日志；若没有这行代码，函数不知道应该写到哪里。
    if event_log_path is None:  # 新增代码+ObservabilitySplit: 未启用时保持完全静默；若没有这行代码，普通交互会出现不必要机器标记。
        return None  # 新增代码+ObservabilitySplit: 告诉调用方本次没有写入事件；若没有这行代码，调用方可能误判事件已落盘。
    event = build_acceptance_event(state, payload)  # 新增代码+ObservabilitySplit: 生成标准事件对象；若没有这行代码，日志和终端标记可能内容不一致。
    event_line = json.dumps(event, ensure_ascii=False, separators=(",", ":"))  # 新增代码+ObservabilitySplit: 转成紧凑 UTF-8 JSON；若没有这行代码，JSONL 文件无法被稳定解析。
    event_log_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+ObservabilitySplit: 自动创建日志父目录；若没有这行代码，嵌套路径会因目录不存在写入失败。
    with event_log_path.open("a", encoding="utf-8") as event_log:  # 新增代码+ObservabilitySplit: 追加打开日志文件；若没有这行代码，多条事件会互相覆盖或无法写入。
        event_log.write(event_line + "\n")  # 新增代码+ObservabilitySplit: 写入一行 JSONL；若没有这行代码，外部控制器读不到状态事件。
    if not acceptance_event_stdout_enabled(environ):  # 修改代码+AcceptanceStdoutNoiseControl: 默认不把机器事件打印到人类终端；若没有这行代码，用户会继续看到 `::learning-agent-acceptance` JSON 事件墙。
        return event  # 修改代码+AcceptanceStdoutNoiseControl: 只写 JSONL 后返回事件对象；若没有这行代码，关闭 stdout 时调用方拿不到事件结果。
    target_stream = sys.stdout if stream is None else stream  # 新增代码+ObservabilitySplit: 默认写真实终端，也允许测试传入内存流；若没有这行代码，测试和生产输出无法共用函数。
    target_stream.write(f"{ACCEPTANCE_EVENT_MARKER_PREFIX}{event_line}\n")  # 新增代码+ObservabilitySplit: 在可见终端打印状态标记；若没有这行代码，UI 自动化仍只能靠截图判断阶段。
    target_stream.flush()  # 新增代码+ObservabilitySplit: 立即刷新终端输出；若没有这行代码，控制器可能看不到最新状态而提前输入。
    return event  # 新增代码+ObservabilitySplit: 返回事件方便调用方或测试检查；若没有这行代码，调用方无法确认实际写入内容。
