from __future__ import annotations  # 新增代码+DirectChatGptSseClient: 让测试类型注解延迟求值；如果没有这行代码，跨版本运行更脆弱。

from pathlib import Path  # 新增代码+DirectChatGptSseClient: 使用 Path 读取 fixture；如果没有这行代码，路径拼接会更脆弱。

from learning_agent.models.adapters import CodexOAuthChatModel  # 新增代码+DirectChatGptSseClient: 导入旧 OAuth wrapper；如果没有这行代码，无法验证旧路径收敛。
from learning_agent.models.chatgpt_codex_sse import CHATGPT_CODEX_RESPONSES_ENDPOINT  # 新增代码+DirectChatGptSseClient: 导入共享端点；如果没有这行代码，无法检查端点一致性。
from learning_agent.models.chatgpt_codex_sse import ChatGptCodexSseClient  # 新增代码+DirectChatGptSseClient: 导入共享 parser；如果没有这行代码，无法检查 parser 委托。


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "chatgpt_codex_sse"  # 新增代码+DirectChatGptSseClient: 定位 SSE fixture 目录；如果没有这行代码，测试会重复硬编码路径。


def test_legacy_codex_oauth_wrapper_uses_shared_endpoint() -> None:  # 新增代码+DirectChatGptSseClient: 函数段开始，验证旧 wrapper endpoint 不再分叉；如果没有这个测试，后续改端点可能只改新客户端，本段到断言结束。
    assert CodexOAuthChatModel.CODEX_API_ENDPOINT == CHATGPT_CODEX_RESPONSES_ENDPOINT  # 新增代码+DirectChatGptSseClient: 断言旧 wrapper 复用共享端点；如果没有这行代码，旧链路可能还打旧地址。


def test_legacy_codex_oauth_wrapper_delegates_sse_parser() -> None:  # 新增代码+DirectChatGptSseClient: 函数段开始，验证旧 wrapper parser 与共享 parser 完全一致；如果没有这个测试，两个 parser 会再次漂移，本段到断言结束。
    raw_stream = (FIXTURE_DIR / "response_stream_basic.sse").read_text(encoding="utf-8")  # 新增代码+DirectChatGptSseClient: 读取基础成功流；如果没有这行代码，测试没有样本。
    legacy_result = CodexOAuthChatModel._parse_sse_response(raw_stream)  # 新增代码+DirectChatGptSseClient: 调用旧 wrapper parser；如果没有这行代码，无法验证旧入口。
    shared_result = ChatGptCodexSseClient.parse_sse_text_to_response(raw_stream)  # 新增代码+DirectChatGptSseClient: 调用共享 parser；如果没有这行代码，无法做对比。
    assert legacy_result == shared_result  # 新增代码+DirectChatGptSseClient: 断言两个入口结果一致；如果没有这行代码，旧 wrapper 仍可能分叉。
    assert legacy_result["output_text"] == "OPENHARNESS_OK"  # 新增代码+DirectChatGptSseClient: 断言旧入口仍能得到最终文本；如果没有这行代码，兼容性回归不明显。
