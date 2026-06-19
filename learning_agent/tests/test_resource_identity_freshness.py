from learning_agent.computer_use_mcp_v2.windows_runtime.resource_identity import RESOURCE_USER_ACTION_REQUIRED_MARKER  # 新增代码+ResourceFreshnessTest：导入资源阻断 marker；如果没有这一行，测试无法约束旧资源恢复必须进入用户动作门禁。
from learning_agent.computer_use_mcp_v2.windows_runtime.resource_identity import build_resource_freshness  # 新增代码+ResourceFreshnessTest：导入资源新鲜度 helper；如果没有这一行，测试无法约束通用资源/文档身份判断。


def test_restored_document_resource_blocks_write_when_new_file_was_requested() -> None:  # 新增代码+ResourceFreshnessTest：函数段开始，验证请求新文件时恢复旧文档必须阻断；如果没有这段测试，agent 可能把 hello everyone 写进用户旧文档。
    report = build_resource_freshness(  # 新增代码+ResourceFreshnessTest：调用资源新鲜度判断；如果没有这一行，测试没有被测行为。
        {  # 新增代码+ResourceFreshnessTest：窗口事实字典开始；如果没有这一行，helper 没有输入窗口。
            "app_id": "notepad.exe",  # 新增代码+ResourceFreshnessTest：声明文档类应用是 Notepad；如果没有这一行，helper 无法识别文档容器。
            "process_name": "notepad.exe",  # 新增代码+ResourceFreshnessTest：补充进程名用于通用 app token 判断；如果没有这一行，部分真实窗口只靠 process_name 会漏判。
            "title_preview": "2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad",  # 新增代码+ResourceFreshnessTest：模拟 Notepad 恢复旧 md 文档标题；如果没有这一行，旧资源风险不会被触发。
            "window_id": "hwnd:4329584",  # 新增代码+ResourceFreshnessTest：提供窗口身份；如果没有这一行，报告缺少审计对象。
        },  # 新增代码+ResourceFreshnessTest：窗口事实字典结束；如果没有这一行，Python 语法不完整。
        requested_resource_hint="1.txt",  # 新增代码+ResourceFreshnessTest：声明用户要保存的新资源名；如果没有这一行，helper 不知道旧标题是否偏离目标。
        requires_new_resource=True,  # 新增代码+ResourceFreshnessTest：声明当前任务需要新空白资源；如果没有这一行，旧资源标题可能被当作普通可选证据。
    )  # 新增代码+ResourceFreshnessTest：build_resource_freshness 调用结束；如果没有这一行，Python 语法不完整。

    assert report["allowed"] is False  # 新增代码+ResourceFreshnessTest：确认旧文档恢复时不允许继续写动作；如果没有这一行，测试无法防止写入用户旧文档。
    assert report["marker"] == RESOURCE_USER_ACTION_REQUIRED_MARKER  # 新增代码+ResourceFreshnessTest：确认阻断能进入现有用户动作收敛协议；如果没有这一行，模型可能继续重试工具。
    assert report["decision"] == "restored_existing_resource_requires_new_blank_or_authorization"  # 新增代码+ResourceFreshnessTest：确认稳定决策码；如果没有这一行，验收日志无法精确解释失败原因。
    assert report["low_level_event_count"] == 0  # 新增代码+ResourceFreshnessTest：确认判断本身不会触发鼠标键盘事件；如果没有这一行，安全验收缺少零事件证据。
# 新增代码+ResourceFreshnessTest：函数段结束，test_restored_document_resource_blocks_write_when_new_file_was_requested 到此结束；如果没有这个边界说明，用户不容易看出旧资源阻断范围。


def test_blank_document_resource_is_allowed_for_new_file_task() -> None:  # 新增代码+ResourceFreshnessTest：函数段开始，验证新空白文档允许继续执行；如果没有这段测试，修复可能把正常新窗口也误挡住。
    report = build_resource_freshness(  # 新增代码+ResourceFreshnessTest：调用资源新鲜度判断；如果没有这一行，测试没有被测行为。
        {  # 新增代码+ResourceFreshnessTest：窗口事实字典开始；如果没有这一行，helper 没有输入窗口。
            "app_id": "notepad.exe",  # 新增代码+ResourceFreshnessTest：声明文档类应用；如果没有这一行，helper 不能走文档类空白识别。
            "process_name": "notepad.exe",  # 新增代码+ResourceFreshnessTest：补充进程名；如果没有这一行，真实窗口字段差异可能无法覆盖。
            "title_preview": "Untitled - Notepad",  # 新增代码+ResourceFreshnessTest：模拟新空白 Notepad 标题；如果没有这一行，允许路径没有标题依据。
            "window_id": "hwnd:1234",  # 新增代码+ResourceFreshnessTest：提供窗口身份；如果没有这一行，报告缺少审计对象。
        },  # 新增代码+ResourceFreshnessTest：窗口事实字典结束；如果没有这一行，Python 语法不完整。
        requested_resource_hint="1.txt",  # 新增代码+ResourceFreshnessTest：声明最终要保存的文件名；如果没有这一行，测试不能覆盖新文件任务。
        requires_new_resource=True,  # 新增代码+ResourceFreshnessTest：声明任务要求新空白资源；如果没有这一行，允许路径不够贴近真实压力测试。
    )  # 新增代码+ResourceFreshnessTest：build_resource_freshness 调用结束；如果没有这一行，Python 语法不完整。

    assert report["allowed"] is True  # 新增代码+ResourceFreshnessTest：确认新空白文档可以继续动作；如果没有这一行，修复会过度保守导致压力测试永远不能做。
    assert report["decision"] == "fresh_blank_resource_ready"  # 新增代码+ResourceFreshnessTest：确认稳定允许决策码；如果没有这一行，调试时无法区分新空白和已保存目标文件。
    assert report["resource_matches_hint"] is False  # 新增代码+ResourceFreshnessTest：确认空白文档还没有保存成 1.txt；如果没有这一行，报告会混淆“允许编辑”和“已是目标文件”。
# 新增代码+ResourceFreshnessTest：函数段结束，test_blank_document_resource_is_allowed_for_new_file_task 到此结束；如果没有这个边界说明，用户不容易看出新空白允许范围。
