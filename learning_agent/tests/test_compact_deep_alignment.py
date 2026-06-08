"""ClaudeCode 级 compact 深度对齐红线测试。"""  # 新增代码+DeepCompact: 说明本文件专门锁定多层 compact 与 reactive compact；若没有这行代码，维护者不清楚这些测试不是普通 compact 回归。

from __future__ import annotations  # 新增代码+DeepCompact: 延迟解析类型注解；若没有这行代码，后续类型引用更容易受导入顺序影响。

import tempfile  # 新增代码+DeepCompact: 创建隔离 artifact 目录；若没有这行代码，测试会污染真实工作区。
import unittest  # 新增代码+DeepCompact: 使用项目现有 unittest 框架；若没有这行代码，测试无法被 discover 发现。
from pathlib import Path  # 新增代码+DeepCompact: 用 Path 管理临时目录；若没有这行代码，Windows 路径拼接会更脆弱。

from learning_agent.core.compact import compact_messages_with_boundary  # 新增代码+DeepCompact: 导入待升级 compact 入口；若没有这行代码，测试无法证明现有入口是否真的多层。


class CompactDeepAlignmentTests(unittest.TestCase):  # 新增代码+DeepCompact: 定义 compact 深度对齐测试集合；若没有这行代码，测试方法没有容器。
    def test_compact_boundary_records_all_claudecode_style_layers(self) -> None:  # 新增代码+DeepCompact: 验证 compact boundary 记录 snip/micro/context/autocompact；若没有这行代码，单层摘要会再次被误判为对齐。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DeepCompact: 创建临时目录隔离 artifact；若没有这行代码，测试产物会落到真实项目。
            artifact_dir = Path(raw_dir) / "artifacts"  # 新增代码+DeepCompact: 规划完整工具输出落盘目录；若没有这行代码，长输出 snip 无法留下可审计证据。
            long_tool_output = "工具完整输出-" + ("证据" * 3000)  # 新增代码+DeepCompact: 构造超过 inline 限制的工具输出；若没有这行代码，tool_output_snip 分支不会触发。
            messages = [{"role": "system", "content": "系统规则必须保留。"}]  # 新增代码+DeepCompact: 准备消息列表并保留系统提示；若没有这行代码，compact 无法证明系统头仍在。
            messages.extend({"role": "user", "content": f"历史问题 {index}"} for index in range(12))  # 新增代码+DeepCompact: 添加足够多旧消息触发 micro/autocompact；若没有这行代码，数量阈值不会触发。
            messages.append({"role": "tool", "tool_call_id": "call-long", "name": "read", "content": long_tool_output})  # 新增代码+DeepCompact: 添加长工具输出触发 snip；若没有这行代码，artifact_paths 不会出现。
            compacted_messages, boundary = compact_messages_with_boundary(messages, session_id="session_deep", run_id="run_deep", turn_id="turn_0", max_messages=6, reason="deep_alignment", artifact_dir=artifact_dir)  # 新增代码+DeepCompact: 调用目标 compact 入口并要求写 artifact；若没有这行代码，测试不能覆盖真实 API。
            boundary_payload = boundary.to_dict()  # 新增代码+DeepCompact: 转成 JSON 友好结构；若没有这行代码，断言需要直接访问实现细节。
            stage_names = [stage.get("stage") for stage in boundary_payload.get("strategy_events", [])]  # 新增代码+DeepCompact: 提取策略阶段名；若没有这行代码，后续断言会重复遍历。
            self.assertIn("tool_output_snip", stage_names)  # 新增代码+DeepCompact: 断言长工具输出被裁剪落盘；若没有这行代码，工具结果仍可能撑爆上下文。
            self.assertIn("microcompact", stage_names)  # 新增代码+DeepCompact: 断言旧消息被微压缩；若没有这行代码，compact 仍只是保留尾部。
            self.assertIn("context_collapse", stage_names)  # 新增代码+DeepCompact: 断言产生 collapse 语义；若没有这行代码，resume 无法复用 collapse commit。
            self.assertIn("autocompact", stage_names)  # 新增代码+DeepCompact: 断言最终全局摘要发生；若没有这行代码，接近预算时不会形成稳定摘要。
            self.assertGreater(boundary_payload.get("estimated_chars_before", 0), boundary_payload.get("estimated_chars_after", 0))  # 新增代码+DeepCompact: 断言 compact 后上下文变小；若没有这行代码，策略名可能只是空标记。
            self.assertTrue(boundary_payload.get("artifact_paths"))  # 新增代码+DeepCompact: 断言完整长输出有落盘路径；若没有这行代码，原始证据可能丢失。
            self.assertTrue(Path(boundary_payload["artifact_paths"][0]).exists())  # 新增代码+DeepCompact: 断言 artifact 文件真实存在；若没有这行代码，路径可能只是假的。
            self.assertLessEqual(len(compacted_messages), 6)  # 新增代码+DeepCompact: 断言返回给模型的消息数量被控制；若没有这行代码，compact 可能只记录不生效。
            self.assertNotIn(long_tool_output, "\n".join(str(message.get("content", "")) for message in compacted_messages))  # 新增代码+DeepCompact: 断言完整长输出不再直接塞回模型；若没有这行代码，snip 没有实际保护上下文。

    def test_reactive_compact_recovers_prompt_too_long_once(self) -> None:  # 新增代码+DeepCompact: 验证 prompt-too-long 可以触发一次 reactive compact；若没有这行代码，模型上下文错误仍会直接失败。
        from learning_agent.core.reactive_compact import is_prompt_too_long_error, try_reactive_compact  # 新增代码+DeepCompact: 导入 reactive compact 入口；若没有这行代码，测试无法锁定错误恢复能力。

        messages = [{"role": "user", "content": "长上下文" * 1000} for _ in range(10)]  # 新增代码+DeepCompact: 构造会被压缩的长消息；若没有这行代码，reactive compact 无法展示效果。
        self.assertTrue(is_prompt_too_long_error(RuntimeError("context length exceeded: prompt too long")))  # 新增代码+DeepCompact: 断言常见上下文错误能识别；若没有这行代码，恢复入口可能漏掉真实错误。
        result = try_reactive_compact(messages, session_id="session_reactive", run_id="run_reactive", turn_id="turn_0", has_attempted=False)  # 新增代码+DeepCompact: 执行第一次 reactive compact；若没有这行代码，测试无法验证重试载荷。
        self.assertTrue(result.should_retry)  # 新增代码+DeepCompact: 断言第一次可重试；若没有这行代码，agent 会直接放弃。
        self.assertEqual(result.transition_reason, "reactive_compact_retry")  # 新增代码+DeepCompact: 断言事件原因对齐 ClaudeCode 语义；若没有这行代码，状态生态难以解释恢复。
        self.assertLess(len(result.messages), len(messages))  # 新增代码+DeepCompact: 断言恢复后消息减少；若没有这行代码，retry 仍可能继续超限。
        second_result = try_reactive_compact(messages, session_id="session_reactive", run_id="run_reactive", turn_id="turn_0", has_attempted=True)  # 新增代码+DeepCompact: 执行第二次尝试；若没有这行代码，无法防止无限 reactive 循环。
        self.assertFalse(second_result.should_retry)  # 新增代码+DeepCompact: 断言第二次不会无限重试；若没有这行代码，长任务可能卡死。


if __name__ == "__main__":  # 新增代码+DeepCompact: 支持直接运行本文件；若没有这行代码，单文件排查不方便。
    unittest.main()  # 新增代码+DeepCompact: 直接运行时启动 unittest；若没有这行代码，python 文件本身不会执行测试。
