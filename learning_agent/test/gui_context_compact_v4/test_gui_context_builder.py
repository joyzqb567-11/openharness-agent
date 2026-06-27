import json  # 新增代码+GuiContextBuilderTest：导入 JSON 用来检查事件 payload 是否泄露原始聊天文本；如果没有这一行，测试无法稳定检查嵌套结构。
import tempfile  # 新增代码+GuiContextBuilderTest：导入 tempfile 用来创建隔离 workspace；如果没有这一行，测试会污染真实项目目录。
import unittest  # 新增代码+GuiContextBuilderTest：沿用项目现有 unittest 风格；如果没有这一行，pytest/unittest 无法发现本文件测试类。
from pathlib import Path  # 新增代码+GuiContextBuilderTest：导入 Path 处理 Windows 临时路径；如果没有这一行，测试中的 workspace 路径容易拼错。

from learning_agent.app.gui_context import build_gui_context_for_turn, compact_messages_to_responses_input, gui_context_limits_from_env  # 修改代码+GuiContextDirectSse400Fix：同时导入格式转换 helper；如果没有这一行，测试无法锁定 assistant 历史的 output_text 契约。


def _text_from_responses_input(messages: list[dict[str, object]]) -> str:  # 新增代码+GuiContextBuilderTest：函数段开始，把 Responses input 消息提取成普通文本；如果没有这段函数，多个测试会重复手写嵌套 content 解析。
    texts: list[str] = []  # 新增代码+GuiContextBuilderTest：准备收集每段文本；如果没有这一行，函数没有地方累积解析结果。
    for message in messages:  # 新增代码+GuiContextBuilderTest：逐条扫描模型输入消息；如果没有这一行，测试只能看到第一条消息。
        content = message.get("content", []) if isinstance(message, dict) else []  # 新增代码+GuiContextBuilderTest：防御性读取 content；如果没有这一行，坏消息结构会让测试 helper 崩溃。
        if isinstance(content, str):  # 新增代码+GuiContextBuilderTest：兼容字符串 content；如果没有这一行，旧格式消息无法被测试检查。
            texts.append(content)  # 新增代码+GuiContextBuilderTest：保存字符串 content；如果没有这一行，字符串消息会被误判为缺失。
            continue  # 新增代码+GuiContextBuilderTest：字符串 content 已处理完毕；如果没有这一行，后续 list 分支会错误处理字符串。
        for item in content if isinstance(content, list) else []:  # 新增代码+GuiContextBuilderTest：扫描 Responses input 的分片列表；如果没有这一行，input_text 分片无法被检查。
            if isinstance(item, dict):  # 新增代码+GuiContextBuilderTest：只处理字典分片；如果没有这一行，非字典分片会触发属性访问错误。
                texts.append(str(item.get("text", "")))  # 新增代码+GuiContextBuilderTest：提取 text 字段；如果没有这一行，测试看不到真实发给模型的文本。
    return "\n".join(texts)  # 新增代码+GuiContextBuilderTest：返回合并文本方便断言；如果没有这一行，调用方拿不到解析结果。
# 新增代码+GuiContextBuilderTest：函数段结束，_text_from_responses_input 到此结束；这段边界说明方便用户知道它只负责测试读取消息文本。


class GuiContextBuilderTests(unittest.TestCase):  # 新增代码+GuiContextBuilderTest：测试类段开始，锁定 GUI 会话上下文构建契约；如果没有这个类，pytest 无法组织这些行为测试。
    def test_current_prompt_appears_once_when_current_user_message_exists(self) -> None:  # 新增代码+GuiContextBuilderTest：测试段开始，确保当前用户消息已在 session 中时不会重复追加；如果没有这个测试，GUI 可能把同一句 prompt 发两遍。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiContextBuilderTest：创建隔离目录；如果没有这一行，compact artifact 可能写进真实工作区。
            result = build_gui_context_for_turn(  # 新增代码+GuiContextBuilderTest：调用待测 builder；如果没有这一行，当前 prompt 去重行为无法验证。
                session_messages=[  # 新增代码+GuiContextBuilderTest：准备模拟 GUI session 消息；如果没有这一组输入，测试没有历史上下文。
                    {"role": "user", "text": "请记住 ALPHA_CONTEXT_927", "turn_id": "turn_1", "status": "completed"},  # 新增代码+GuiContextBuilderTest：第一轮用户事实；如果没有这一行，第二轮没有可回忆内容。
                    {"role": "assistant", "text": "我记住了。", "turn_id": "turn_1", "status": "completed"},  # 新增代码+GuiContextBuilderTest：第一轮助手完成消息；如果没有这一行，助手历史保留行为无法覆盖。
                    {"role": "user", "text": "刚才的测试代码是什么？", "turn_id": "turn_2", "status": "completed"},  # 新增代码+GuiContextBuilderTest：当前用户消息已经存在于 session；如果没有这一行，测试无法证明 exact-once 去重。
                    {"role": "assistant", "text": "", "turn_id": "turn_2", "status": "running"},  # 新增代码+GuiContextBuilderTest：当前助手占位消息；如果没有这一行，测试无法确认 running 空回复不会进模型。
                ],  # 新增代码+GuiContextBuilderTest：session_messages 输入结束；如果没有这一行，Python 列表语法不完整。
                current_prompt="刚才的测试代码是什么？",  # 新增代码+GuiContextBuilderTest：传入当前 prompt；如果没有这一行，builder 不知道本轮问题。
                session_id="session_once",  # 新增代码+GuiContextBuilderTest：传入 session id 方便审计；如果没有这一行，事件 payload 缺少会话归属。
                run_id="run_once",  # 新增代码+GuiContextBuilderTest：传入 run id 方便审计；如果没有这一行，事件 payload 缺少运行归属。
                turn_id="turn_2",  # 新增代码+GuiContextBuilderTest：传入当前 turn id；如果没有这一行，builder 无法识别当前轮消息。
                workspace=Path(directory),  # 新增代码+GuiContextBuilderTest：传入隔离 workspace；如果没有这一行，compact artifact 没有安全位置。
            )  # 新增代码+GuiContextBuilderTest：builder 调用结束；如果没有这一行，函数调用语法不完整。
        joined_text = _text_from_responses_input(result.messages)  # 新增代码+GuiContextBuilderTest：提取发给模型的文本；如果没有这一行，断言要重复解析嵌套消息。
        self.assertEqual(joined_text.count("刚才的测试代码是什么？"), 1)  # 新增代码+GuiContextBuilderTest：确认当前 prompt 只出现一次；如果没有这一行，重复 prompt 回归不会失败。
        self.assertIn("ALPHA_CONTEXT_927", joined_text)  # 新增代码+GuiContextBuilderTest：确认历史事实仍在模型输入中；如果没有这一行，latest-prompt-only 回归不会失败。
        self.assertNotIn("running", joined_text)  # 新增代码+GuiContextBuilderTest：确认 running 占位状态没有作为正文进入模型；如果没有这一行，空助手占位可能污染上下文。
    # 新增代码+GuiContextBuilderTest：测试段结束，current prompt 已存在时 exact-once 契约到此结束。

    def test_current_prompt_is_appended_once_when_missing_from_session_messages(self) -> None:  # 新增代码+GuiContextBuilderTest：测试段开始，确保 session 尚未写入当前用户消息时 builder 会补齐；如果没有这个测试，异步时序可能让当前问题丢失。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiContextBuilderTest：创建隔离目录；如果没有这一行，测试文件会落到真实项目目录。
            result = build_gui_context_for_turn(  # 新增代码+GuiContextBuilderTest：调用待测 builder；如果没有这一行，补齐当前 prompt 的行为无法验证。
                session_messages=[{"role": "user", "text": "上一轮事实 BETA_MEMORY_314", "turn_id": "turn_1", "status": "completed"}],  # 新增代码+GuiContextBuilderTest：只提供历史消息；如果没有这一行，测试无法模拟当前 prompt 缺失。
                current_prompt="请复述上一轮事实。",  # 新增代码+GuiContextBuilderTest：当前 prompt 不在 session_messages 中；如果没有这一行，builder 没有可追加文本。
                session_id="session_missing",  # 新增代码+GuiContextBuilderTest：传入 session id；如果没有这一行，事件归属不可审计。
                run_id="run_missing",  # 新增代码+GuiContextBuilderTest：传入 run id；如果没有这一行，事件归属不可审计。
                turn_id="turn_2",  # 新增代码+GuiContextBuilderTest：传入当前 turn id；如果没有这一行，补齐消息无法带上轮次身份。
                workspace=Path(directory),  # 新增代码+GuiContextBuilderTest：传入隔离 workspace；如果没有这一行，compact artifact 无处可放。
            )  # 新增代码+GuiContextBuilderTest：builder 调用结束；如果没有这一行，函数调用语法不完整。
        joined_text = _text_from_responses_input(result.messages)  # 新增代码+GuiContextBuilderTest：提取模型输入文本；如果没有这一行，断言无法读取嵌套 content。
        self.assertIn("BETA_MEMORY_314", joined_text)  # 新增代码+GuiContextBuilderTest：确认历史事实没有丢失；如果没有这一行，builder 可能只发送当前 prompt。
        self.assertEqual(joined_text.count("请复述上一轮事实。"), 1)  # 新增代码+GuiContextBuilderTest：确认缺失的当前 prompt 被补齐且只补一次；如果没有这一行，当前问题可能丢失或重复。
    # 新增代码+GuiContextBuilderTest：测试段结束，当前 prompt 缺失时补齐契约到此结束。

    def test_task_state_goal_prefers_current_prompt_over_first_greeting(self) -> None:  # 新增代码+GuiContextBuilderTest：测试段开始，确保 compact 用本轮 prompt 作为任务目标；如果没有这个测试，第一句寒暄可能错误成为长期目标。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiContextBuilderTest：创建隔离目录；如果没有这一行，任务状态 artifact 可能污染真实项目。
            result = build_gui_context_for_turn(  # 新增代码+GuiContextBuilderTest：调用待测 builder；如果没有这一行，任务目标来源无法验证。
                session_messages=[  # 新增代码+GuiContextBuilderTest：准备包含寒暄和当前任务的历史；如果没有这一行，测试无法复现目标漂移。
                    {"role": "user", "text": "你好", "turn_id": "turn_1", "status": "completed"},  # 新增代码+GuiContextBuilderTest：第一句寒暄；如果没有这一行，目标漂移风险没有输入样本。
                    {"role": "assistant", "text": "你好，我在。", "turn_id": "turn_1", "status": "completed"},  # 新增代码+GuiContextBuilderTest：寒暄回复；如果没有这一行，历史对话更不真实。
                    {"role": "user", "text": "请只回答当前目标 TASK_GOAL_778", "turn_id": "turn_2", "status": "completed"},  # 新增代码+GuiContextBuilderTest：真正当前任务；如果没有这一行，builder 无法证明优先当前 prompt。
                ],  # 新增代码+GuiContextBuilderTest：session_messages 输入结束；如果没有这一行，Python 列表语法不完整。
                current_prompt="请只回答当前目标 TASK_GOAL_778",  # 新增代码+GuiContextBuilderTest：明确本轮目标；如果没有这一行，TaskState 可能回退到第一句。
                session_id="session_goal",  # 新增代码+GuiContextBuilderTest：传入 session id；如果没有这一行，TaskState 缺少会话信息。
                run_id="run_goal",  # 新增代码+GuiContextBuilderTest：传入 run id；如果没有这一行，TaskState 缺少运行信息。
                turn_id="turn_2",  # 新增代码+GuiContextBuilderTest：传入当前 turn id；如果没有这一行，TaskState 缺少轮次信息。
                workspace=Path(directory),  # 新增代码+GuiContextBuilderTest：传入隔离 workspace；如果没有这一行，artifact 路径不安全。
                max_messages=3,  # 新增代码+GuiContextBuilderTest：设置较小消息阈值促使 builder 走预算逻辑；如果没有这一行，目标摘要路径覆盖不足。
                max_chars=900,  # 新增代码+GuiContextBuilderTest：设置可视化验收级别字符阈值；如果没有这一行，阈值行为不稳定。
            )  # 新增代码+GuiContextBuilderTest：builder 调用结束；如果没有这一行，函数调用语法不完整。
        self.assertEqual(result.task_state_summary["current_goal"], "请只回答当前目标 TASK_GOAL_778")  # 新增代码+GuiContextBuilderTest：确认当前目标来自本轮 prompt；如果没有这一行，寒暄变目标的 bug 不会被锁住。
        self.assertEqual(result.task_state_summary["latest_user_input"], "请只回答当前目标 TASK_GOAL_778")  # 新增代码+GuiContextBuilderTest：确认最新用户输入也是本轮 prompt；如果没有这一行，compact 摘要可能围绕旧消息展开。
    # 新增代码+GuiContextBuilderTest：测试段结束，TaskState 当前目标契约到此结束。

    def test_gui_context_compacts_long_history_and_keeps_current_prompt(self) -> None:  # 新增代码+GuiContextBuilderTest：测试段开始，验证长历史会压缩但仍保留当前问题；如果没有这个测试，compact 可能把最重要的新问题折掉。
        long_history = []  # 新增代码+GuiContextBuilderTest：准备长历史列表；如果没有这一行，无法构造超预算输入。
        for index in range(8):  # 新增代码+GuiContextBuilderTest：生成多轮历史；如果没有这一行，消息数不会超过 max_messages。
            long_history.append({"role": "user", "text": f"历史事实 {index} LONG_CONTEXT_MARKER_{index}", "turn_id": f"turn_{index}", "status": "completed"})  # 新增代码+GuiContextBuilderTest：添加用户历史消息；如果没有这一行，compact 没有用户事实可折叠。
            long_history.append({"role": "assistant", "text": f"历史回复 {index} " + ("填充" * 60), "turn_id": f"turn_{index}", "status": "completed"})  # 新增代码+GuiContextBuilderTest：添加较长助手回复；如果没有这一行，字符预算可能不会触发。
        long_history.append({"role": "user", "text": "请回答当前问题 KEEP_CURRENT_42", "turn_id": "turn_final", "status": "completed"})  # 新增代码+GuiContextBuilderTest：添加当前用户问题；如果没有这一行，无法验证当前 prompt 保留。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiContextBuilderTest：创建隔离目录；如果没有这一行，compact artifact 可能污染真实工作区。
            result = build_gui_context_for_turn(long_history, "请回答当前问题 KEEP_CURRENT_42", "session_compact", "run_compact", "turn_final", Path(directory), max_messages=5, max_chars=900)  # 新增代码+GuiContextBuilderTest：用小阈值触发 compact；如果没有这一行，压缩行为无法验证。
        joined_text = _text_from_responses_input(result.messages)  # 新增代码+GuiContextBuilderTest：提取模型输入文本；如果没有这一行，无法确认当前 prompt 是否还在。
        self.assertTrue(result.compacted)  # 新增代码+GuiContextBuilderTest：确认长历史触发了 compact；如果没有这一行，builder 可能永远不压缩。
        self.assertLessEqual(len(result.messages), 5)  # 新增代码+GuiContextBuilderTest：确认输出消息数不超过预算；如果没有这一行，压缩结果可能仍然超长。
        self.assertIn("KEEP_CURRENT_42", joined_text)  # 新增代码+GuiContextBuilderTest：确认当前 prompt 保留；如果没有这一行，用户最新问题可能被摘要吞掉。
    # 新增代码+GuiContextBuilderTest：测试段结束，长历史 compact 契约到此结束。

    def test_gui_context_event_payload_excludes_raw_text(self) -> None:  # 新增代码+GuiContextBuilderTest：测试段开始，确认状态事件只给预算指标不泄露对话原文；如果没有这个测试，右侧状态栏可能暴露隐私文本。
        secret_text = "SECRET_RAW_TEXT_SHOULD_NOT_LEAK_556"  # 新增代码+GuiContextBuilderTest：准备敏感原文标记；如果没有这一行，测试没有可搜索的泄露信号。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiContextBuilderTest：创建隔离目录；如果没有这一行，artifact 路径不安全。
            result = build_gui_context_for_turn(  # 新增代码+GuiContextBuilderTest：调用待测 builder；如果没有这一行，事件 payload 无法生成。
                session_messages=[{"role": "user", "text": secret_text, "turn_id": "turn_1", "status": "completed"}],  # 新增代码+GuiContextBuilderTest：输入含敏感文本的历史；如果没有这一行，泄露测试没有原文来源。
                current_prompt="当前短问题",  # 新增代码+GuiContextBuilderTest：输入当前问题；如果没有这一行，builder 无法形成完整请求。
                session_id="session_event",  # 新增代码+GuiContextBuilderTest：传入 session id；如果没有这一行，事件无法归属。
                run_id="run_event",  # 新增代码+GuiContextBuilderTest：传入 run id；如果没有这一行，事件无法归属。
                turn_id="turn_2",  # 新增代码+GuiContextBuilderTest：传入当前 turn id；如果没有这一行，事件无法归属。
                workspace=Path(directory),  # 新增代码+GuiContextBuilderTest：传入隔离 workspace；如果没有这一行，artifact 路径不安全。
            )  # 新增代码+GuiContextBuilderTest：builder 调用结束；如果没有这一行，函数调用语法不完整。
        event_text = json.dumps(result.event_payload, ensure_ascii=False)  # 新增代码+GuiContextBuilderTest：把事件 payload 转成可搜索文本；如果没有这一行，无法检测嵌套泄露。
        self.assertNotIn(secret_text, event_text)  # 新增代码+GuiContextBuilderTest：确认敏感历史不进入事件；如果没有这一行，状态栏泄露不会失败。
        self.assertNotIn("当前短问题", event_text)  # 新增代码+GuiContextBuilderTest：确认当前 prompt 也不进入事件；如果没有这一行，事件可能暴露用户最新输入。
        self.assertIn("input_message_count", result.event_payload)  # 新增代码+GuiContextBuilderTest：确认事件仍有可观测指标；如果没有这一行，隐私修复可能把诊断信息也删光。
    # 新增代码+GuiContextBuilderTest：测试段结束，事件隐私契约到此结束。

    def test_gui_context_limits_from_env_respects_small_visual_qa_thresholds(self) -> None:  # 新增代码+GuiContextBuilderTest：测试段开始，确认 GUI 验收可用小阈值强制触发 compact；如果没有这个测试，人工验证很难稳定看到压缩事件。
        limits = gui_context_limits_from_env({"OPENHARNESS_GUI_CONTEXT_MAX_MESSAGES": "5", "OPENHARNESS_GUI_CONTEXT_MAX_CHARS": "900"})  # 新增代码+GuiContextBuilderTest：传入小阈值环境变量；如果没有这一行，测试无法验证配置读取。
        self.assertEqual(limits.max_messages, 5)  # 新增代码+GuiContextBuilderTest：确认消息数量阈值尊重 5；如果没有这一行，helper 可能把小阈值错误抬高。
        self.assertEqual(limits.max_chars, 900)  # 新增代码+GuiContextBuilderTest：确认字符阈值尊重 900；如果没有这一行，helper 可能无法用于真实 GUI 视觉验收。
    # 新增代码+GuiContextBuilderTest：测试段结束，环境阈值契约到此结束。

    def test_responses_input_uses_output_text_for_assistant_history(self) -> None:  # 修改代码+GuiContextDirectSse400Fix：测试段开始，确认助手历史使用官方接受的 output_text；如果没有这个测试，多轮追问会再次被 ChatGPT endpoint 400 拒绝。
        messages = [  # 修改代码+GuiContextDirectSse400Fix：准备一段含用户、助手、用户的最小多轮上下文；如果没有这一组输入，无法复现真实 GUI 追问形态。
            {"role": "user", "content": "请记住 ALPHA_CONTEXT_927"},  # 修改代码+GuiContextDirectSse400Fix：第一条用户事实必须保持 input_text；如果没有这一行，测试缺少历史事实。
            {"role": "assistant", "content": "已记住。"},  # 修改代码+GuiContextDirectSse400Fix：助手完成回复必须转成 output_text；如果没有这一行，无法覆盖本次 400 根因。
            {"role": "user", "content": "刚才的测试代码是什么？"},  # 修改代码+GuiContextDirectSse400Fix：当前追问必须继续保持 input_text；如果没有这一行，测试不是完整多轮请求。
        ]  # 修改代码+GuiContextDirectSse400Fix：多轮输入列表结束；如果没有这一行，Python 列表语法不完整。
        responses_input = compact_messages_to_responses_input(messages)  # 修改代码+GuiContextDirectSse400Fix：执行待测格式转换；如果没有这一行，断言没有对象。
        self.assertEqual(responses_input[0]["content"][0]["type"], "input_text")  # 修改代码+GuiContextDirectSse400Fix：确认用户历史仍用 input_text；如果没有这一行，修复可能误改用户消息格式。
        self.assertEqual(responses_input[1]["content"][0]["type"], "output_text")  # 修改代码+GuiContextDirectSse400Fix：确认助手历史改用 output_text；如果没有这一行，本次官方 400 根因不会被测试锁住。
        self.assertEqual(responses_input[2]["content"][0]["type"], "input_text")  # 修改代码+GuiContextDirectSse400Fix：确认当前用户追问仍用 input_text；如果没有这一行，当前 prompt 可能被错误标成助手输出。
    # 修改代码+GuiContextDirectSse400Fix：测试段结束，assistant output_text 契约到此结束。
# 新增代码+GuiContextBuilderTest：测试类段结束，GuiContextBuilderTests 到此结束；这段边界说明方便用户按类理解测试覆盖范围。


if __name__ == "__main__":  # 新增代码+GuiContextBuilderTest：允许直接运行本测试文件；如果没有这一行，手动调试需要额外记住 unittest 命令。
    unittest.main()  # 新增代码+GuiContextBuilderTest：启动 unittest runner；如果没有这一行，直接 python 文件不会执行测试。
