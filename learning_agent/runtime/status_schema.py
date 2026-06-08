"""状态事件 v2 schema 常量，统一终端、SDK、HTTP 和工具看到的事件语言。"""  # 新增代码+StatusSchemaV2: 说明本模块专门保存状态协议常量；若没有这行代码，事件类型会继续散落各处。

from __future__ import annotations  # 新增代码+StatusSchemaV2: 延迟解析类型注解；若没有这行代码，未来添加复杂类型时更容易受顺序影响。

STATUS_SCHEMA_VERSION = 2  # 新增代码+StatusSchemaV2: 声明当前状态事件协议版本；若没有这行代码，外部 SDK 无法判断字段兼容性。

STATUS_EVENT_TYPES_V2: set[str] = {  # 新增代码+StatusSchemaV2: 集中列出 v2 推荐事件类型；若没有这行代码，调用方无法复用统一枚举。
    "run_started",  # 新增代码+StatusSchemaV2: 表示真实 run 开始；若没有这行代码，状态协议缺少运行起点。
    "run_completed",  # 新增代码+StatusSchemaV2: 表示真实 run 完成；若没有这行代码，状态协议缺少运行终点。
    "run_failed",  # 新增代码+StatusSchemaV2: 表示真实 run 失败；若没有这行代码，状态协议无法分类失败。
    "turn_accepted",  # 新增代码+StatusSchemaV2: 表示某轮用户输入已落盘；若没有这行代码，resume 无法观察安全起点。
    "model_request_started",  # 新增代码+StatusSchemaV2: 表示模型请求开始；若没有这行代码，UI 无法显示当前卡在模型阶段。
    "model_message_delta",  # 新增代码+StatusSchemaV2: 表示模型文本流增量；若没有这行代码，SDK 无法观察流式输出。
    "model_response_completed",  # 新增代码+StatusSchemaV2: 表示模型响应完成；若没有这行代码，状态协议缺少模型完成点。
    "tool_use_seen",  # 新增代码+StatusSchemaV2: 表示模型请求工具；若没有这行代码，状态生态看不到工具意图。
    "tool_result_seen",  # 新增代码+StatusSchemaV2: 表示工具结果已记录；若没有这行代码，resume 无法判断工具是否完成。
    "tool_use_summary_created",  # 新增代码+StatusSchemaV2: 表示工具摘要已生成；若没有这行代码，下一轮上下文缺少可观察摘要。
    "tombstone_created",  # 新增代码+StatusSchemaV2: 表示无效消息被标记删除；若没有这行代码，UI/SDK 不知道消息链被修复。
    "compact_started",  # 新增代码+StatusSchemaV2: 表示 compact 开始；若没有这行代码，长上下文处理缺少起点。
    "compact_completed",  # 新增代码+StatusSchemaV2: 表示 compact 完成；若没有这行代码，状态页看不到压缩结果。
    "reactive_compact_retry",  # 新增代码+StatusSchemaV2: 表示 prompt-too-long 后触发补救重试；若没有这行代码，错误恢复无法审计。
    "resume_started",  # 新增代码+StatusSchemaV2: 表示恢复流程开始；若没有这行代码，resume 生命周期缺少起点。
    "resume_completed",  # 新增代码+StatusSchemaV2: 表示恢复流程完成且安全；若没有这行代码，外部 agent 不知道可以继续。
    "resume_needs_review",  # 新增代码+StatusSchemaV2: 表示恢复需要人工复核；若没有这行代码，危险工具可能被误重跑。
    "resume_blocked",  # 新增代码+StatusSchemaV2: 表示恢复被阻断；若没有这行代码，状态页无法解释为什么不能继续。
    "verifier_result",  # 新增代码+StatusSchemaV2: 表示验收器结果；若没有这行代码，真实验收证据无法进入状态生态。
    "browser_runtime_event",  # 新增代码+BrowserRuntimeStatus: 表示浏览器 runtime run/action/event 已被主循环发现；若没有这行代码，UI/SDK 无法用统一事件类型订阅浏览器任务。
    "status_snapshot_created",  # 新增代码+StatusSchemaV2: 表示状态快照被创建；若没有这行代码，外部观察访问本身无法审计。
    "status_probe",  # 新增代码+StatusSchemaV2: 表示测试或探针事件；若没有这行代码，回归测试缺少轻量事件类型。
}  # 新增代码+StatusSchemaV2: 事件类型集合结束；若没有这行代码，Python 集合语法不完整。


def normalize_event_type(event_type: str) -> str:  # 新增代码+StatusSchemaV2: 规范化事件类型字符串；若没有这行代码，空格或 None 会污染事件日志。
    return str(event_type or "").strip()  # 新增代码+StatusSchemaV2: 返回去空白后的事件名；若没有这行代码，事件过滤会不稳定。
