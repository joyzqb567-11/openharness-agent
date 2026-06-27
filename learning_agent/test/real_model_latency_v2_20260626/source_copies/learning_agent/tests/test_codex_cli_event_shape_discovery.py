from pathlib import Path  # 新增代码+CodexCliDiscoveryTest：导入 Path 读取 discovery 证据文件；如果没有这一行，测试只能依赖字符串路径拼接。


DISCOVERY_DIR = Path("learning_agent/test/real_model_latency_v2_20260626/codex_cli_discovery")  # 新增代码+CodexCliDiscoveryTest：定义 discovery 证据目录；如果没有这一行，多个断言会重复写路径且容易写错。


def test_codex_cli_event_shape_document_records_delta_capability() -> None:  # 新增代码+CodexCliDiscoveryTest：测试函数段开始，锁定 event_shape 文档必须明确说明 delta 能力；如果没有这段测试，后续可能再次把假流式说成真 token 流式。
    text = (DISCOVERY_DIR / "event_shape.md").read_text(encoding="utf-8")  # 新增代码+CodexCliDiscoveryTest：读取事件形状报告；如果没有这一行，测试没有实际文档输入。
    assert "Does stdout contain token deltas:" in text  # 新增代码+CodexCliDiscoveryTest：确认报告回答 token delta 问题；如果没有这一行，蓝图的关键 stop condition 没有自动化保护。
    assert "Can OpenHarness show real token streaming from Codex CLI:" in text  # 新增代码+CodexCliDiscoveryTest：确认报告回答是否能展示真 token streaming；如果没有这一行，GUI 可能误导用户。
    assert "Can OpenHarness at least show transport status from Codex CLI:" in text  # 新增代码+CodexCliDiscoveryTest：确认报告回答是否能展示 CLI 状态；如果没有这一行，状态可观测性的边界不清楚。
# 新增代码+CodexCliDiscoveryTest：测试函数段结束，test_codex_cli_event_shape_document_records_delta_capability 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_codex_cli_discovery_outputs_are_sanitized_and_present() -> None:  # 新增代码+CodexCliDiscoveryTest：测试函数段开始，确认 discovery 输出文件存在且没有常见 secret 字样；如果没有这段测试，证据目录可能缺文件或泄露敏感信息。
    stdout_text = (DISCOVERY_DIR / "sanitized_stdout.jsonl").read_text(encoding="utf-8")  # 新增代码+CodexCliDiscoveryTest：读取脱敏 stdout；如果没有这一行，测试不能确认 JSONL 证据落盘。
    stderr_text = (DISCOVERY_DIR / "sanitized_stderr.txt").read_text(encoding="utf-8")  # 新增代码+CodexCliDiscoveryTest：读取脱敏 stderr；如果没有这一行，测试不能确认 warning/timeout 证据落盘。
    combined_text = stdout_text + "\n" + stderr_text  # 新增代码+CodexCliDiscoveryTest：合并文本做低成本扫描；如果没有这一行，需要对两个文件重复 secret 断言。
    assert "thread.started" in stdout_text  # 新增代码+CodexCliDiscoveryTest：确认 stdout 至少包含 Codex JSONL 生命周期事件；如果没有这一行，空文件也可能误过。
    assert "access_token" not in combined_text.lower()  # 新增代码+CodexCliDiscoveryTest：确认没有 access token 字样；如果没有这一行，敏感 OAuth 信息可能进入证据。
    assert "refresh_token" not in combined_text.lower()  # 新增代码+CodexCliDiscoveryTest：确认没有 refresh token 字样；如果没有这一行，长期凭据可能进入仓库。
    assert "bearer " not in combined_text.lower()  # 新增代码+CodexCliDiscoveryTest：确认没有 Bearer 头；如果没有这一行，认证头可能进入证据。
# 新增代码+CodexCliDiscoveryTest：测试函数段结束，test_codex_cli_discovery_outputs_are_sanitized_and_present 到此结束；如果没有这个边界说明，用户不容易看出脱敏检查范围。
