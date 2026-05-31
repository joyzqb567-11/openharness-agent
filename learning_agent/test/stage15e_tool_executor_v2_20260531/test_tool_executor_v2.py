"""Stage 15E Tool Executor v2 与权限 hook 测试。"""  # 新增代码+Stage15E: 说明本文件锁定工具执行器 v2 行为；若没有这行代码，维护者不清楚测试覆盖边界。

from __future__ import annotations  # 新增代码+Stage15E: 延迟解析类型注解；若没有这行代码，前向引用更容易受定义顺序影响。

import tempfile  # 新增代码+Stage15E: 创建临时工作区；若没有这行代码，测试会污染真实项目文件。
import unittest  # 新增代码+Stage15E: 使用项目现有 unittest 框架；若没有这行代码，测试类无法运行。
from pathlib import Path  # 新增代码+Stage15E: 用 Path 操作测试文件；若没有这行代码，临时路径拼接会更脆弱。

from learning_agent.core.agent import LearningAgent, ToolCallingFakeModel  # 新增代码+Stage15E: 导入真实 agent 和离线假模型；若没有这行代码，测试无法覆盖真实执行器入口。
from learning_agent.core.messages import ModelMessage, ToolCall  # 新增代码+Stage15E: 导入模型消息和工具调用对象；若没有这行代码，测试无法构造工具请求。
from learning_agent.tools.hooks import ToolHookEvent, ToolHookManager  # 新增代码+Stage15E: 导入新增 hook 管理器；若没有这行代码，红灯无法证明 hook 模块缺失。
from learning_agent.tools.permissions import ToolPermissionDecision  # 新增代码+Stage15E: 导入权限决策对象；若没有这行代码，红灯无法证明权限模块缺失。


class ToolExecutorV2Tests(unittest.TestCase):  # 新增代码+Stage15E: 定义执行器 v2 测试类；若没有这行代码，测试方法没有统一容器。
    def test_executor_records_permission_and_runs_pre_post_hooks(self) -> None:  # 新增代码+Stage15E: 验证正常工具会记录权限并运行前后 hook；若没有这行代码，hook 可能只停留在空模块。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Stage15E: 使用临时目录隔离测试；若没有这行代码，读取文件会污染真实 workspace。
            workspace = Path(raw_dir)  # 新增代码+Stage15E: 转成 Path 方便写入样例文件；若没有这行代码，路径拼接不够稳定。
            (workspace / "sample.txt").write_text("hello from hook", encoding="utf-8")  # 新增代码+Stage15E: 准备 read 工具输入文件；若没有这行代码，工具执行会因为文件不存在失败。
            hook_trace: list[tuple[str, str]] = []  # 新增代码+Stage15E: 保存 hook 调用轨迹；若没有这行代码，测试无法判断 hook 是否真的被执行。
            manager = ToolHookManager()  # 新增代码+Stage15E: 创建 hook 管理器；若没有这行代码，无法注册前后 hook。
            manager.add_hook("pre_tool_use", lambda event: hook_trace.append(("pre", event.tool_name)))  # 新增代码+Stage15E: 注册执行前 hook；若没有这行代码，pre_tool_use 分支没有测试输入。
            manager.add_hook("post_tool_use", lambda event: hook_trace.append(("post", event.result_text)))  # 新增代码+Stage15E: 注册执行后 hook；若没有这行代码，post_tool_use 分支没有测试输入。
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="unused")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+Stage15E: 创建真实 agent；若没有这行代码，无法通过真实 _execute_tool 入口验证。
            agent.tool_hooks = manager  # 新增代码+Stage15E: 注入 hook 管理器；若没有这行代码，执行器没有可运行的 hook。
            output = agent._execute_tool(ToolCall(name="read", arguments={"path": "sample.txt"}))  # 新增代码+Stage15E: 执行只读工具；若没有这行代码，hook 和权限事件都不会触发。
            self.assertIn("hello from hook", output)  # 新增代码+Stage15E: 确认工具本身仍正常返回；若没有这行代码，测试可能只验证 hook 却漏掉执行结果。
            self.assertEqual(hook_trace[0], ("pre", "read"))  # 新增代码+Stage15E: 确认 pre hook 在 read 上运行；若没有这行代码，执行前 hook 缺失不会被发现。
            self.assertEqual(hook_trace[1], ("post", "hello from hook"))  # 新增代码+Stage15E: 确认 post hook 拿到工具结果；若没有这行代码，执行后 hook 可能没有结果上下文。
            event_kinds = [event["kind"] for event in agent.observation_events]  # 新增代码+Stage15E: 收集观察事件类型；若没有这行代码，无法断言结构化事件落地。
            self.assertIn("permission_decided", event_kinds)  # 新增代码+Stage15E: 确认权限决策被记录；若没有这行代码，审计无法解释工具为什么执行。
            self.assertIn("pre_tool_use", event_kinds)  # 新增代码+Stage15E: 确认执行前 hook 被记录；若没有这行代码，hook 运行过程不可审计。
            self.assertIn("post_tool_use", event_kinds)  # 新增代码+Stage15E: 确认执行后 hook 被记录；若没有这行代码，工具成功后的观察流不完整。

    def test_permission_denied_does_not_execute_tool(self) -> None:  # 新增代码+Stage15E: 验证权限拒绝时不执行工具；若没有这行代码，deny 决策可能只是被记录但不生效。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Stage15E: 使用临时目录隔离写入测试；若没有这行代码，拒绝测试可能污染真实 workspace。
            workspace = Path(raw_dir)  # 新增代码+Stage15E: 转成 Path 方便检查文件是否存在；若没有这行代码，路径检查容易写错。
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="unused")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+Stage15E: 创建真实 agent；若没有这行代码，无法覆盖真实权限执行路径。
            catalog_tool = agent._find_catalog_tool("write")  # 新增代码+Stage15E: 找到 write 的 catalog 元数据；若没有这行代码，测试无法模拟 deny 权限模式。
            self.assertIsNotNone(catalog_tool)  # 新增代码+Stage15E: 确认 write 工具存在；若没有这行代码，后续属性设置可能对 None 报错。
            catalog_tool.permission_mode = "deny"  # 新增代码+Stage15E: 模拟策略层拒绝 write；若没有这行代码，拒绝分支没有触发条件。
            output = agent._execute_tool(ToolCall(name="write", arguments={"path": "blocked.txt", "content": "nope"}))  # 新增代码+Stage15E: 尝试执行被拒写入；若没有这行代码，无法证明拒绝会阻断工具。
            self.assertIn("权限拒绝", output)  # 新增代码+Stage15E: 确认返回文本来自权限拒绝；若没有这行代码，测试可能把其他失败误当成功。
            self.assertFalse((workspace / "blocked.txt").exists())  # 新增代码+Stage15E: 确认文件没有被写入；若没有这行代码，权限拒绝不执行的关键约束无法验证。
            event_kinds = [event["kind"] for event in agent.observation_events]  # 新增代码+Stage15E: 收集观察事件类型；若没有这行代码，无法检查拒绝事件。
            self.assertIn("permission_denied", event_kinds)  # 新增代码+Stage15E: 确认拒绝事件被记录；若没有这行代码，审计看不到工具为何没执行。

    def test_hook_error_becomes_tool_error_event(self) -> None:  # 新增代码+Stage15E: 验证 hook 报错会转成工具错误事件；若没有这行代码，hook 异常可能直接炸掉 agent。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Stage15E: 使用临时目录隔离测试；若没有这行代码，样例文件会污染真实项目。
            workspace = Path(raw_dir)  # 新增代码+Stage15E: 转成 Path 方便写文件；若没有这行代码，路径拼接不够清楚。
            (workspace / "sample.txt").write_text("content", encoding="utf-8")  # 新增代码+Stage15E: 准备 read 输入文件；若没有这行代码，测试可能失败在文件不存在而不是 hook。
            manager = ToolHookManager()  # 新增代码+Stage15E: 创建 hook 管理器；若没有这行代码，无法注册异常 hook。
            manager.add_hook("pre_tool_use", lambda event: (_ for _ in ()).throw(RuntimeError("boom")))  # 新增代码+Stage15E: 注册会抛错的 pre hook；若没有这行代码，hook 错误分支没有测试输入。
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="unused")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+Stage15E: 创建真实 agent；若没有这行代码，无法覆盖真实执行器异常兜底。
            agent.tool_hooks = manager  # 新增代码+Stage15E: 注入异常 hook 管理器；若没有这行代码，执行器不会触发 hook 错误。
            output = agent._execute_tool(ToolCall(name="read", arguments={"path": "sample.txt"}))  # 新增代码+Stage15E: 执行会触发 pre hook 的工具；若没有这行代码，错误分支不会运行。
            self.assertIn("tool hook 失败", output)  # 新增代码+Stage15E: 确认异常被转成可读工具错误；若没有这行代码，测试无法验证 agent 没崩溃。
            self.assertIn("tool_error", [event["kind"] for event in agent.observation_events])  # 新增代码+Stage15E: 确认错误事件被记录；若没有这行代码，hook 报错缺少审计证据。

    def test_permission_decision_object_has_stable_fields(self) -> None:  # 新增代码+Stage15E: 验证权限决策对象字段稳定；若没有这行代码，执行器和 hook 之间的协议可能漂移。
        decision = ToolPermissionDecision(status="auto_allow", allowed=True, reason="safe read")  # 新增代码+Stage15E: 构造最小权限决策；若没有这行代码，无法检查对象字段。
        self.assertEqual(decision.status, "auto_allow")  # 新增代码+Stage15E: 确认状态字段可读；若没有这行代码，调用方无法判断 allow/deny/ask/auto_allow。
        self.assertTrue(decision.allowed)  # 新增代码+Stage15E: 确认 allowed 字段可读；若没有这行代码，执行器无法决定是否继续执行。
        self.assertEqual(decision.reason, "safe read")  # 新增代码+Stage15E: 确认原因字段可读；若没有这行代码，审计事件无法解释决策来源。
        self.assertIsInstance(ToolHookEvent(tool_name="read", call_id="call", arguments={}), ToolHookEvent)  # 新增代码+Stage15E: 确认 hook 事件对象可构造；若没有这行代码，hook 回调没有稳定输入类型。


if __name__ == "__main__":  # 新增代码+Stage15E: 支持直接运行本测试文件；若没有这行代码，单文件排查不方便。
    unittest.main()  # 新增代码+Stage15E: 直接运行时启动 unittest；若没有这行代码，python 文件本身不会执行测试。
