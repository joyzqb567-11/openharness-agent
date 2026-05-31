"""观测层包，集中承载 debug log、acceptance events、permission events 和运行记录。"""  # 修改代码+ObservabilitySplit: 说明 observability 包的职责；若没有这行代码，排查证据链时仍会回到主入口文件里翻找。

try:  # 修改代码+ObservabilitySplit: 优先按 learning_agent 包路径导入观测层 helper；若没有这行代码，包运行模式下导出入口不稳定。
    from learning_agent.observability.acceptance_events import emit_acceptance_event  # 修改代码+ObservabilitySplit: 包运行模式下导出验收事件写入器；若没有这行代码，外部 agent 无法直接从观测层导入核心能力。
    from learning_agent.observability.debug_log import append_debug_event_record, build_debug_event_record  # 修改代码+ObservabilitySplit: 包运行模式下导出调试日志 helper；若没有这行代码，日志写入复用点不明显。
    from learning_agent.observability.permission_events import build_permission_event_payload  # 修改代码+ObservabilitySplit: 包运行模式下导出权限 payload 构造器；若没有这行代码，权限审计解析仍会散落在调用方。
    from learning_agent.observability.run_records import build_final_answer_event_payload  # 修改代码+ObservabilitySplit: 包运行模式下导出最终回答 payload helper；若没有这行代码，验收结果字段无法被集中维护。
except ModuleNotFoundError as error:  # 修改代码+ObservabilitySplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 模式导入 observability 包会失败。
    if error.name not in {"learning_agent", "learning_agent.observability", "learning_agent.observability.acceptance_events", "learning_agent.observability.debug_log", "learning_agent.observability.permission_events", "learning_agent.observability.run_records"}:  # 修改代码+ObservabilitySplit: 只允许目标路径缺失时 fallback；若没有这行代码，观测层内部真实 bug 会被误吞。
        raise  # 修改代码+ObservabilitySplit: 重新抛出真实依赖错误；若没有这行代码，真正的导入问题会被伪装成脚本模式。
    from observability.acceptance_events import emit_acceptance_event  # 修改代码+ObservabilitySplit: 脚本模式下导出验收事件写入器；若没有这行代码，双击 bat 时观测层入口会断开。
    from observability.debug_log import append_debug_event_record, build_debug_event_record  # 修改代码+ObservabilitySplit: 脚本模式下导出调试日志 helper；若没有这行代码，直接运行时日志 helper 会找不到。
    from observability.permission_events import build_permission_event_payload  # 修改代码+ObservabilitySplit: 脚本模式下导出权限 payload 构造器；若没有这行代码，直接运行时权限审计会断开。
    from observability.run_records import build_final_answer_event_payload  # 修改代码+ObservabilitySplit: 脚本模式下导出最终回答 payload helper；若没有这行代码，真实终端最终回答事件会断开。

__all__ = [  # 修改代码+ObservabilitySplit: 明确观测层包入口导出的符号；若没有这行代码，自动文档和其他 agent 难以知道可用 API。
    "append_debug_event_record",  # 修改代码+ObservabilitySplit: 导出追加调试日志函数；若没有这行代码，外部复用时需要深入子模块。
    "build_debug_event_record",  # 修改代码+ObservabilitySplit: 导出调试记录构造函数；若没有这行代码，日志字段结构不容易复用。
    "build_final_answer_event_payload",  # 修改代码+ObservabilitySplit: 导出最终回答事件 helper；若没有这行代码，验收字段会被重复手写。
    "build_permission_event_payload",  # 修改代码+ObservabilitySplit: 导出权限事件 payload helper；若没有这行代码，权限审计解析难以统一。
    "emit_acceptance_event",  # 修改代码+ObservabilitySplit: 导出验收事件写入器；若没有这行代码，外部 agent 找不到观测层主入口。
]  # 修改代码+ObservabilitySplit: 结束导出列表；若没有这行代码，Python 列表语法不完整。
