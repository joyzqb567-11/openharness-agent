import base64  # 新增代码+ComputerUseBmpPng: 导入 base64 用来解码模型图片 data URL；如果没有这行代码，BMP 转 PNG 测试只能看 MIME 字符串，不能确认真实字节已经变成 PNG。
import copy  # 新增代码+ComputerUseVisionLoop：导入深拷贝工具用于保存每轮模型输入；如果没有这行代码，测试记录的 messages 可能被后续主循环修改而失真。
import json  # 新增代码+Phase41WindowsImageResults: 导入 JSON 工具用于检查 image result block 是否泄露敏感文本；如果没有这行代码，测试无法可靠审计结构化结果。
import tempfile  # 新增代码+Phase41WindowsImageResults: 导入临时目录工具隔离截图 evidence 文件；如果没有这行代码，测试会污染真实 memory 目录。
import unittest  # 新增代码+Phase41WindowsImageResults: 导入 unittest 测试框架；如果没有这行代码，本阶段测试不会被 Python 测试发现。
from pathlib import Path  # 新增代码+Phase41WindowsImageResults: 导入 Path 处理截图 artifact 路径；如果没有这行代码，路径检查会变成脆弱字符串拼接。

from learning_agent.computer_use.controller import ComputerUseController, MemoryComputerUseBackend, WindowsComputerUseBackend  # 修改代码+ObserveBeforeActionGate: 同时导入内存后端用于验证 full 模式未观察前不许动作；如果没有这行代码，测试无法证明盲目鼠标键盘会被 agent 层拦住。
from learning_agent.computer_use.evidence import PHASE41_IMAGE_RESULT_MODEL, PHASE41_WINDOWS_IMAGE_RESULTS_MARKER, PHASE41_WINDOWS_IMAGE_RESULTS_OK_TOKEN, ComputerUseEvidenceStore, collect_image_result_blocks, phase41_cli_line, run_phase41_image_results_contract  # 新增代码+Phase41WindowsImageResults: 导入 Phase41 image result 合同入口；如果没有这行代码，红灯无法证明模型可见图片块尚未补齐。
from learning_agent.computer_use.helper_client import StaticWindowObservationHelper, WindowObservationPayload  # 新增代码+Phase41WindowsImageResults: 导入静态观察 helper 和 payload；如果没有这行代码，测试无法在不碰真实桌面的情况下模拟截图。
from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase41WindowsImageResults: 导入静态窗口 inventory；如果没有这行代码，测试会依赖真实用户桌面窗口。
from learning_agent.computer_use_mcp_v2.windows_runtime.image_messages import build_computer_use_image_blocks_from_tool_output  # 修改代码+Phase41McpV2Migration: 直接导入截图回灌公共函数；如果没有这行代码，测试只能继续依赖已迁出的 agent 私有薄包装。
from learning_agent.core import run_helpers as run_helpers_from_core  # 修改代码+Phase41McpV2Migration: 导入公共 observation helper；如果没有这行代码，测试会继续调用已删除的 _record_observation 私有方法。
from learning_agent.core.agent import LearningAgent, ModelMessage, ToolCallingFakeModel  # 新增代码+Phase41WindowsImageResults: 导入真实 agent 和假模型；如果没有这行代码，无法证明图片 artifact 会进入 active_artifacts。
from learning_agent.core.messages import ToolCall  # 新增代码+ComputerUseVisionLoop：导入工具调用对象用于让假模型请求 computer_observe；如果没有这行代码，测试不能走真实模型-工具-模型闭环。


class WindowsComputerUseImageResultsPhase41Tests(unittest.TestCase):  # 新增代码+Phase41WindowsImageResults: 定义 Phase41 图片结果块测试集合；如果没有这个类，unittest 不会执行本阶段验收。
    def _raw_windows(self) -> list[dict[str, object]]:  # 新增代码+Phase41WindowsImageResults: 准备稳定静态窗口输入；如果没有这段函数，每个测试都要重复构造窗口记录。
        return [  # 新增代码+Phase41WindowsImageResults: 返回窗口列表；如果没有这行代码，测试没有可信窗口样本。
            {"hwnd": 41041, "pid": 141, "process_name": "notepad.exe", "class_name": "Notepad", "title": "记事本 - Phase41", "rect": {"left": 40, "top": 50, "right": 360, "bottom": 260}},  # 新增代码+Phase41WindowsImageResults: 提供可观察窗口和矩形；如果没有这行代码，get_window_state 没有合法目标。
        ]  # 新增代码+Phase41WindowsImageResults: 结束静态窗口列表；如果没有这行代码，Python 列表语法不完整。

    def _payload(self) -> WindowObservationPayload:  # 新增代码+Phase41WindowsImageResults: 构造包含截图和敏感 UIA 行的 payload；如果没有这段函数，测试无法验证图片块和脱敏边界。
        return WindowObservationPayload(  # 新增代码+Phase41WindowsImageResults: 返回静态窗口观察 payload；如果没有这行代码，后端没有截图输入可保存。
            screenshot_bytes=b"phase41-fake-png-bytes",  # 新增代码+Phase41WindowsImageResults: 提供假 PNG 字节证明截图 artifact 会落盘；如果没有这行代码，image result block 没有 artifact_path。
            screenshot_format="png",  # 新增代码+Phase41WindowsImageResults: 声明截图格式用于 MIME 类型映射；如果没有这行代码，模型无法知道图片类型。
            screenshot_width=320,  # 新增代码+Phase41WindowsImageResults: 提供截图宽度；如果没有这行代码，图片块尺寸字段无法验证。
            screenshot_height=210,  # 新增代码+Phase41WindowsImageResults: 提供截图高度；如果没有这行代码，图片块尺寸字段无法验证。
            accessibility_text="安全标题\npassword: phase41-secret-must-not-leak\n按钮 确定",  # 新增代码+Phase41WindowsImageResults: 提供敏感 UIA 行；如果没有这行代码，测试不能证明 image block 不携带敏感文本。
            focused_element="编辑区",  # 新增代码+Phase41WindowsImageResults: 提供焦点元素摘要；如果没有这行代码，窗口状态会缺少常规 UIA 字段。
            selected_text="安全选择文本",  # 新增代码+Phase41WindowsImageResults: 提供选中文本摘要；如果没有这行代码，状态兼容性无法覆盖。
            document_text="安全文档摘要",  # 新增代码+Phase41WindowsImageResults: 提供文档摘要；如果没有这行代码，状态兼容性无法覆盖。
            helper_name="static_phase41_helper",  # 新增代码+Phase41WindowsImageResults: 标记 helper 来源；如果没有这行代码，证据来源不可审计。
            helper_available=True,  # 新增代码+Phase41WindowsImageResults: 声明 helper 可用；如果没有这行代码，状态可能误判为无截图能力。
            helper_reason="Phase 41 static image result helper",  # 新增代码+Phase41WindowsImageResults: 提供 helper 说明；如果没有这行代码，排查截图来源会困难。
        )  # 新增代码+Phase41WindowsImageResults: 结束 payload 构造；如果没有这行代码，Python 调用语法不完整。

    def _controller(self, evidence_root: Path) -> ComputerUseController:  # 新增代码+Phase41WindowsImageResults: 构造带静态截图 helper 的控制器；如果没有这段函数，测试搭建会重复且容易漏依赖。
        inventory = StaticWindowsWindowInventory(raw_windows=self._raw_windows(), captured_at="2026-06-03T00:00:00Z")  # 新增代码+Phase41WindowsImageResults: 使用静态 inventory 固定窗口快照；如果没有这行代码，测试会随真实桌面变化。
        helper = StaticWindowObservationHelper(payloads={"hwnd:41041": self._payload()})  # 新增代码+Phase41WindowsImageResults: 把静态 payload 绑定到窗口 id；如果没有这行代码，后端拿不到截图。
        store = ComputerUseEvidenceStore(evidence_root=evidence_root)  # 新增代码+Phase41WindowsImageResults: 创建 evidence store 并指向临时目录；如果没有这行代码，截图不会落到可检查位置。
        backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=False, evidence_store=store, observation_helper=helper)  # 新增代码+Phase41WindowsImageResults: 创建只读 Windows 后端；如果没有这行代码，controller 无法返回真实窗口状态结构。
        return ComputerUseController(backend=backend)  # 新增代码+Phase41WindowsImageResults: 返回统一控制器入口；如果没有这行代码，测试绕不开生产 observe 调度。

    def test_evidence_store_builds_model_visible_image_result_block(self) -> None:  # 新增代码+Phase41WindowsImageResults: 验证 evidence store 直接生成模型可读图片结果块；如果没有这个测试，截图可能只落盘但模型看不到引用。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase41WindowsImageResults: 创建临时 evidence 目录；如果没有这行代码，测试会污染真实项目 memory。
            store = ComputerUseEvidenceStore(evidence_root=Path(raw_dir))  # 新增代码+Phase41WindowsImageResults: 构造证据仓库；如果没有这行代码，被测保存逻辑不会运行。
            evidence = store.save_window_state(window=self._raw_windows()[0], payload=self._payload(), fallback_width=320, fallback_height=210)  # 新增代码+Phase41WindowsImageResults: 保存窗口状态触发截图 artifact 和 image block；如果没有这行代码，断言没有对象。
            image_blocks = collect_image_result_blocks(evidence)  # 新增代码+Phase41WindowsImageResults: 从 evidence 中收集图片块；如果没有这行代码，无法证明通用收集器能识别 block。
            block_text = json.dumps(image_blocks, ensure_ascii=False)  # 新增代码+Phase41WindowsImageResults: 序列化图片块用于敏感词检查；如果没有这行代码，嵌套字段泄露不容易断言。

            self.assertEqual(len(image_blocks), 1)  # 新增代码+Phase41WindowsImageResults: 断言只有一张截图图片块；如果没有这行代码，缺失或重复 block 都可能漏过。
            self.assertEqual(image_blocks[0]["type"], "image_result")  # 新增代码+Phase41WindowsImageResults: 断言块类型稳定；如果没有这行代码，模型无法按协议识别图片。
            self.assertEqual(image_blocks[0]["model"], PHASE41_IMAGE_RESULT_MODEL)  # 新增代码+Phase41WindowsImageResults: 断言模型名稳定；如果没有这行代码，后续兼容性无法审计。
            self.assertEqual(image_blocks[0]["marker"], PHASE41_WINDOWS_IMAGE_RESULTS_MARKER)  # 新增代码+Phase41WindowsImageResults: 断言验收标记进入 block；如果没有这行代码，真实终端验收无法快速定位 Phase41。
            self.assertEqual(image_blocks[0]["mime_type"], "image/png")  # 新增代码+Phase41WindowsImageResults: 断言 PNG 被映射为正确 MIME；如果没有这行代码，多模态消费端可能读错格式。
            self.assertEqual(image_blocks[0]["width"], 320)  # 新增代码+Phase41WindowsImageResults: 断言图片宽度可见；如果没有这行代码，模型无法知道截图尺寸。
            self.assertEqual(image_blocks[0]["height"], 210)  # 新增代码+Phase41WindowsImageResults: 断言图片高度可见；如果没有这行代码，模型无法知道截图尺寸。
            self.assertTrue(Path(image_blocks[0]["artifact_path"]).exists())  # 新增代码+Phase41WindowsImageResults: 断言图片 artifact 真落盘；如果没有这行代码，block 可能指向假路径。
            self.assertFalse(image_blocks[0]["sensitive_text_included"])  # 新增代码+Phase41WindowsImageResults: 断言图片块声明不含 UIA 文本；如果没有这行代码，敏感边界不清楚。
            self.assertNotIn("password", block_text.lower())  # 新增代码+Phase41WindowsImageResults: 断言图片块不包含敏感 password 字样；如果没有这行代码，结构化 block 可能泄露文本。
            self.assertNotIn("phase41-secret-must-not-leak", block_text)  # 新增代码+Phase41WindowsImageResults: 断言图片块不包含敏感具体值；如果没有这行代码，脱敏失败可能漏过。

    def test_controller_text_includes_image_result_lines_without_sensitive_text(self) -> None:  # 新增代码+Phase41WindowsImageResults: 验证 controller 的文本结果包含图片引用摘要；如果没有这个测试，模型工具结果仍可能只看到原始 dict。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase41WindowsImageResults: 创建临时 evidence 目录；如果没有这行代码，测试会污染真实 memory。
            controller = self._controller(Path(raw_dir))  # 新增代码+Phase41WindowsImageResults: 构造生产控制器；如果没有这行代码，后续 observe 没有入口。
            window = controller.observe({"action": "list_windows"}).data["windows"][0]  # 新增代码+Phase41WindowsImageResults: 先获取可信 window 引用；如果没有这行代码，get_window_state 会因未知窗口失败。
            result = controller.observe({"action": "get_window_state", "window": window})  # 新增代码+Phase41WindowsImageResults: 读取窗口状态并触发 image result block；如果没有这行代码，文本输出没有数据。
            text = result.to_text("computer_observe")  # 新增代码+Phase41WindowsImageResults: 把结构化结果转换成模型可见文本；如果没有这行代码，无法检查工具返回内容。

            self.assertTrue(result.ok)  # 新增代码+Phase41WindowsImageResults: 断言窗口状态观察成功；如果没有这行代码，失败文本也可能误判包含字段。
            self.assertIn("Computer Use Image Results", text)  # 新增代码+Phase41WindowsImageResults: 断言文本有专门图片结果区块；如果没有这行代码，模型不容易稳定定位图片。
            self.assertIn("image_result_count=1", text)  # 新增代码+Phase41WindowsImageResults: 断言图片数量可读；如果没有这行代码，模型不知道有几张图。
            self.assertIn(PHASE41_WINDOWS_IMAGE_RESULTS_MARKER, text)  # 新增代码+Phase41WindowsImageResults: 断言验收标记进入文本；如果没有这行代码，真实终端验收无法确认 Phase41。
            self.assertIn(str(Path(raw_dir)), text)  # 新增代码+Phase41WindowsImageResults: 断言 artifact 路径进入文本；如果没有这行代码，模型无法引用截图文件。
            self.assertNotIn("phase41-secret-must-not-leak", text)  # 新增代码+Phase41WindowsImageResults: 断言敏感具体值不进入文本；如果没有这行代码，图片结果区可能泄露 UIA。

    def test_agent_records_computer_use_image_artifact_as_active_artifact(self) -> None:  # 新增代码+Phase41WindowsImageResults: 验证 agent 记录图片 artifact 到 active_artifacts；如果没有这个测试，长任务恢复时会丢失截图产物。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase41WindowsImageResults: 创建临时 agent 工作区；如果没有这行代码，测试会污染真实 debug_logs。
            workspace = Path(raw_dir) / "workspace"  # 新增代码+Phase41WindowsImageResults: 为 agent 准备独立工作区路径；如果没有这行代码，agent 运行目录不清晰。
            evidence_root = Path(raw_dir) / "evidence"  # 新增代码+Phase41WindowsImageResults: 为截图证据准备独立目录；如果没有这行代码，artifact 路径不好断言。
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+Phase41WindowsImageResults: 创建真实 agent 并关闭调试噪音；如果没有这行代码，无法覆盖 active_artifacts 集成。
            agent.computer_use_controller = self._controller(evidence_root)  # 新增代码+Phase41WindowsImageResults: 注入带静态截图的 Computer Use 控制器；如果没有这行代码，agent 会使用默认不可用后端。
            window = agent.computer_use_controller.observe({"action": "list_windows"}).data["windows"][0]  # 新增代码+Phase41WindowsImageResults: 获取可信窗口引用；如果没有这行代码，agent 的 observe 会查询未知窗口。
            output = agent._execute_tool(ToolCall(name="mcp__computer-use__observe", arguments={"action": "get_window_state", "window": window, "reason": "phase41 artifact registration"}))  # 修改代码+Phase41McpV2Migration: 通过模型真实可见的 v2 MCP observe 读取窗口状态；如果没有这行代码，测试会继续依赖已删除的旧私有工具入口。
            image_artifacts = [path for path in agent.active_artifacts if str(evidence_root) in path]  # 新增代码+Phase41WindowsImageResults: 筛选本次截图 artifact；如果没有这行代码，无法排除其它历史产物。
            observation_kinds = [event["kind"] for event in agent.observation_events]  # 新增代码+Phase41WindowsImageResults: 收集观察事件类型；如果没有这行代码，无法验证审计事件。

            self.assertIn("Computer Use Image Results", output)  # 新增代码+Phase41WindowsImageResults: 断言 agent 工具文本也包含图片区块；如果没有这行代码，controller 改动可能没有传到 agent。
            self.assertEqual(len(image_artifacts), 1)  # 新增代码+Phase41WindowsImageResults: 断言 active_artifacts 记录一张截图；如果没有这行代码，模型恢复上下文时找不到截图。
            self.assertTrue(Path(image_artifacts[0]).exists())  # 新增代码+Phase41WindowsImageResults: 断言登记的 artifact 路径真实存在；如果没有这行代码，active_artifacts 可能保存假路径。
            self.assertIn("computer_use_image_result", observation_kinds)  # 新增代码+Phase41WindowsImageResults: 断言图片结果登记进入 observation；如果没有这行代码，审计无法解释截图为何成为活跃产物。

    def test_agent_reinjects_computer_use_screenshot_as_model_visible_image_block(self) -> None:  # 新增代码+ComputerUseVisionLoop：函数段开始，验证截图不是只作为路径文本回灌，而是进入下一轮模型可见 image block；如果没有这个测试，/computer use --full 仍可能瞎操作而不是看屏幕。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseVisionLoop：创建临时目录隔离工作区和截图证据；如果没有这行代码，测试会污染真实项目目录。
            workspace = Path(raw_dir) / "workspace"  # 新增代码+ComputerUseVisionLoop：定义临时 agent 工作区；如果没有这行代码，agent 初始化没有安全落点。
            evidence_root = Path(raw_dir) / "evidence"  # 新增代码+ComputerUseVisionLoop：定义临时截图证据目录；如果没有这行代码，测试无法确认图片来自本轮 observe。
            controller = self._controller(evidence_root)  # 新增代码+ComputerUseVisionLoop：创建带静态截图的生产控制器；如果没有这行代码，主循环不会产生 image_result。
            window = controller.observe({"action": "list_windows"}).data["windows"][0]  # 新增代码+ComputerUseVisionLoop：先获取可信窗口引用；如果没有这行代码，get_window_state 会被窗口身份门禁拒绝。

            class RecordingVisionLoopFakeModel:  # 新增代码+ComputerUseVisionLoop：类段开始，记录每轮模型输入并在第一轮请求截图观察；如果没有这个类，测试无法证明第二轮模型真的收到图片块。
                def __init__(self) -> None:  # 新增代码+ComputerUseVisionLoop：初始化假模型状态；如果没有这段函数，测试无法区分第一轮和第二轮。
                    self.calls: list[list[dict[str, object]]] = []  # 新增代码+ComputerUseVisionLoop：保存每轮 messages 深拷贝；如果没有这行代码，断言拿不到模型实际输入。

                def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码+ComputerUseVisionLoop：模拟模型 chat 接口；如果没有这行代码，LearningAgent 主循环无法调用假模型。
                    del tools  # 新增代码+ComputerUseVisionLoop：本测试只关心消息回灌，不检查工具 schema；如果没有这行代码，未使用参数会让测试意图不清楚。
                    self.calls.append(copy.deepcopy(messages))  # 新增代码+ComputerUseVisionLoop：记录当前模型输入；如果没有这行代码，第二轮 image block 无法被检查。
                    if len(self.calls) == 1:  # 新增代码+ComputerUseVisionLoop：第一轮让模型主动请求截图；如果没有这行代码，工具循环不会产生截图结果。
                        return ModelMessage(tool_calls=[ToolCall(name="mcp__computer-use__observe", arguments={"action": "get_window_state", "window": window, "reason": "phase41 vision loop"})])  # 修改代码+Phase41McpV2Migration: 返回模型真实可见的 v2 MCP observe 调用；如果没有这行代码，执行层会按设计阻断旧 computer_observe，导致截图不会回灌。
                    return ModelMessage(text="已经收到截图。")  # 新增代码+ComputerUseVisionLoop：第二轮直接结束；如果没有这行代码，run_events 会继续等待工具调用或触发轮次停止。
            # 新增代码+ComputerUseVisionLoop：类段结束，RecordingVisionLoopFakeModel 到此结束；如果没有这个边界说明，学习者不容易看出假模型只负责记录主循环输入。

            model = RecordingVisionLoopFakeModel()  # 新增代码+ComputerUseVisionLoop：创建记录型假模型；如果没有这行代码，agent 没有可调用模型。
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+ComputerUseVisionLoop：创建真实 agent 主循环；如果没有这行代码，测试无法覆盖 run_events。
            agent.computer_use_controller = controller  # 新增代码+ComputerUseVisionLoop：注入静态截图控制器；如果没有这行代码，默认后端不会返回截图。
            events = list(agent.run_events("请观察这个窗口。", max_turns=2))  # 新增代码+ComputerUseVisionLoop：执行两轮模型-工具循环；如果没有这行代码，断言没有运行对象。
            second_messages = model.calls[1]  # 新增代码+ComputerUseVisionLoop：读取工具结果之后的第二轮模型输入；如果没有这行代码，后续只能检查第一轮普通用户消息。
            image_messages = [message for message in second_messages if isinstance(message.get("content"), list)]  # 新增代码+ComputerUseVisionLoop：筛选内容为多模态数组的消息；如果没有这行代码，图片块检查会混进普通文本消息。
            image_blocks = [block for message in image_messages for block in message["content"] if isinstance(block, dict) and block.get("type") == "image_url"]  # 新增代码+ComputerUseVisionLoop：收集 OpenAI 兼容 image_url 块；如果没有这行代码，测试无法证明像素会进入模型上下文。

            self.assertTrue(any(event.event_type == "run_completed" for event in events))  # 新增代码+ComputerUseVisionLoop：确认主循环自然结束；如果没有这行代码，后续断言可能检查半途中断状态。
            self.assertGreaterEqual(len(model.calls), 2)  # 新增代码+ComputerUseVisionLoop：确认至少发生两次模型调用；如果没有这行代码，第二轮消息断言可能越界或误判。
            self.assertTrue(image_blocks)  # 新增代码+ComputerUseVisionLoop：断言截图作为 image block 回灌；如果没有这行代码，文本路径伪视觉会继续漏过验收。
            self.assertTrue(str(image_blocks[0]["image_url"]["url"]).startswith("data:image/png;base64,"))  # 新增代码+ComputerUseVisionLoop：断言图片以 data URL 形式携带像素；如果没有这行代码，模型仍可能只收到本地路径。
            self.assertIn("Computer Use Image Results", json.dumps(second_messages, ensure_ascii=False))  # 新增代码+ComputerUseVisionLoop：断言原有文本证据仍保留；如果没有这行代码，修复可能破坏可审计文本输出。
    # 新增代码+ComputerUseVisionLoop：函数段结束，test_agent_reinjects_computer_use_screenshot_as_model_visible_image_block 到此结束；如果没有这个边界说明，用户不容易看出视觉主循环验收范围。

    def test_agent_converts_bmp_computer_use_screenshot_to_png_model_image_block(self) -> None:  # 新增代码+ComputerUseBmpPng: 函数段开始，验证 Windows BMP 截图会先转成 Responses API 支持的 PNG；如果没有这个测试，真实终端可能再次因为 image/bmp 被模型 API 拒绝。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseBmpPng: 创建临时目录保存本测试专用 BMP artifact；如果没有这行代码，测试会污染真实 evidence 目录。
            workspace = Path(raw_dir) / "workspace"  # 新增代码+ComputerUseBmpPng: 准备临时 agent 工作区；如果没有这行代码，LearningAgent 初始化没有隔离目录。
            artifact_path = Path(raw_dir) / "computer-window.bmp"  # 新增代码+ComputerUseBmpPng: 准备模拟 Windows 后端真实落盘的 BMP 截图路径；如果没有这行代码，工具输出没有可读取 artifact。
            bmp_bytes = b"BM:\x00\x00\x00\x00\x00\x00\x006\x00\x00\x00(\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x18\x00\x00\x00\x00\x00\x04\x00\x00\x00\x13\x0b\x00\x00\x13\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\x00"  # 新增代码+ComputerUseBmpPng: 写入一个最小 1x1 白色 BMP 文件字节；如果没有这行代码，测试无法复现真实 Windows BMP 截图格式。
            artifact_path.write_bytes(bmp_bytes)  # 新增代码+ComputerUseBmpPng: 把 BMP 字节落盘给生产读取逻辑使用；如果没有这行代码，模型图片块构造会因为文件不存在而跳过。
            output = "\n".join([  # 新增代码+ComputerUseBmpPng: 构造真实工具结果里 Computer Use Image Results 区块；如果没有这行代码，私有解析函数拿不到 artifact_path 和 mime_type。
                "Computer Use Image Results",  # 新增代码+ComputerUseBmpPng: 标记这是 Computer Use 截图区；如果没有这行代码，测试输入不像真实工具输出。
                "- image_result_count=1",  # 新增代码+ComputerUseBmpPng: 声明只有一张截图；如果没有这行代码，输出缺少真实证据摘要字段。
                f"- image_0_artifact_path={artifact_path}",  # 新增代码+ComputerUseBmpPng: 提供 BMP artifact 路径；如果没有这行代码，生产逻辑无法读取截图文件。
                "- image_0_mime_type=image/bmp",  # 新增代码+ComputerUseBmpPng: 明确复现 Windows observe 返回 BMP MIME 的真实失败条件；如果没有这行代码，测试不会覆盖 HTTP 400 根因。
            ])  # 新增代码+ComputerUseBmpPng: 结束工具输出文本构造；如果没有这行代码，Python 列表语法不完整。
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+ComputerUseBmpPng: 创建真实 agent 来调用生产图片块转换函数；如果没有这行代码，测试会脱离实际实现。
            image_blocks = build_computer_use_image_blocks_from_tool_output(output, record_observation=run_helpers_from_core.observation_recorder(agent))  # 修改代码+Phase41McpV2Migration: 使用公共图片回灌函数生成 image_url 块；如果没有这行代码，测试会继续要求 LearningAgent 保留旧图片薄包装。
            data_url = str(image_blocks[0]["image_url"]["url"])  # 新增代码+ComputerUseBmpPng: 取出模型会收到的 data URL；如果没有这行代码，后续无法检查 MIME 和字节。
            png_bytes = base64.b64decode(data_url.split(",", 1)[1])  # 新增代码+ComputerUseBmpPng: 解码 data URL 的实际图片字节；如果没有这行代码，测试只能看到外层字符串，不能证明发生真实转码。
            self.assertTrue(data_url.startswith("data:image/png;base64,"))  # 新增代码+ComputerUseBmpPng: 断言发给模型的是 PNG MIME；如果没有这行代码，image/bmp 会继续触发 Responses API 400。
            self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))  # 新增代码+ComputerUseBmpPng: 断言内容也是真 PNG 文件头；如果没有这行代码，代码可能只是把 BMP 假装标成 PNG。
    # 新增代码+ComputerUseBmpPng: 函数段结束，test_agent_converts_bmp_computer_use_screenshot_to_png_model_image_block 到此结束；如果没有这个边界说明，用户不容易看出 BMP 转 PNG 的验收范围。

    def test_evidence_store_normalizes_bmp_payload_to_png_artifact(self) -> None:  # 新增代码+ComputerUsePngSource: 函数段开始，验证截图源头直接保存为模型支持的 PNG；如果没有这个测试，BMP 仍可能在 evidence 层污染主循环。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUsePngSource: 创建临时 evidence 目录；如果没有这行代码，源头格式测试会污染真实运行截图。
            bmp_bytes = b"BM:\x00\x00\x00\x00\x00\x00\x006\x00\x00\x00(\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x18\x00\x00\x00\x00\x00\x04\x00\x00\x00\x13\x0b\x00\x00\x13\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\x00"  # 新增代码+ComputerUsePngSource: 准备最小 BMP 截图字节；如果没有这行代码，测试无法复现 Windows provider 返回 BMP 的真实路径。
            payload = WindowObservationPayload(screenshot_bytes=bmp_bytes, screenshot_format="bmp", screenshot_width=1, screenshot_height=1, helper_name="bmp_source_helper", helper_available=True, helper_reason="unit test bmp source")  # 新增代码+ComputerUsePngSource: 构造 BMP payload 交给 evidence 源头；如果没有这行代码，测试只会覆盖下游模型输入兜底。
            store = ComputerUseEvidenceStore(evidence_root=Path(raw_dir))  # 新增代码+ComputerUsePngSource: 创建证据仓库；如果没有这行代码，被测源头保存逻辑不会运行。
            evidence = store.save_window_state(window=self._raw_windows()[0], payload=payload, fallback_width=1, fallback_height=1)  # 新增代码+ComputerUsePngSource: 保存窗口状态并触发格式归一化；如果没有这行代码，后续断言没有真实 artifact。
            artifact_path = Path(evidence["screenshot_path"])  # 新增代码+ComputerUsePngSource: 读取源头保存出的截图路径；如果没有这行代码，测试无法检查文件后缀和字节。
            image_blocks = collect_image_result_blocks(evidence)  # 新增代码+ComputerUsePngSource: 收集模型可见图片块；如果没有这行代码，测试无法确认 block MIME 跟 artifact 同步。

            self.assertEqual(evidence["screenshot_format"], "png")  # 新增代码+ComputerUsePngSource: 断言 evidence 格式已经变成 PNG；如果没有这行代码，BMP 可能继续进入模型协议。
            self.assertEqual(artifact_path.suffix.lower(), ".png")  # 新增代码+ComputerUsePngSource: 断言落盘文件后缀是 PNG；如果没有这行代码，artifact 路径仍可能误导消费端。
            self.assertTrue(artifact_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))  # 新增代码+ComputerUsePngSource: 断言文件内容是真 PNG；如果没有这行代码，代码可能只是改后缀没有转码。
            self.assertEqual(image_blocks[0]["mime_type"], "image/png")  # 新增代码+ComputerUsePngSource: 断言图片块也声明 PNG；如果没有这行代码，模型输入层可能仍看到 image/bmp。
    # 新增代码+ComputerUsePngSource: 函数段结束，test_evidence_store_normalizes_bmp_payload_to_png_artifact 到此结束；如果没有这个边界说明，用户不容易看出源头 PNG 验收范围。

    def test_full_mode_rejects_mouse_keyboard_action_before_model_visible_observation(self) -> None:  # 新增代码+ObserveBeforeActionGate: 函数段开始，验证 full 模式没有截图观察前拒绝鼠标键盘；如果没有这个测试，模型仍可能在看不到屏幕时盲点。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ObserveBeforeActionGate: 创建临时工作区；如果没有这行代码，agent 初始化会污染真实项目目录。
            backend = MemoryComputerUseBackend(windows=[{"app_id": "mspaint", "window_id": "hwnd:9001", "title_preview": "Paint", "rect": {"left": 0, "top": 0, "right": 300, "bottom": 200}}])  # 新增代码+ObserveBeforeActionGate: 准备不会碰真实桌面的测试后端；如果没有这行代码，测试可能误触真实鼠标。
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="unused")]), workspace=Path(raw_dir), ask_permission=lambda action: (_ for _ in ()).throw(AssertionError("blind action should be rejected before permission")), debug_enabled=False)  # 新增代码+ObserveBeforeActionGate: 创建 full 模式 agent 且权限函数若被调用就失败；如果没有这行代码，测试无法证明拦截发生在权限和后端前。
            agent.computer_use_controller = ComputerUseController(backend=backend)  # 新增代码+ObserveBeforeActionGate: 注入内存控制器；如果没有这行代码，agent 会使用默认不可用后端导致测试失焦。
            agent.desktop_task_context = {"active": True, "requires_gui_actions": True}  # 新增代码+ObserveBeforeActionGate: 模拟 /computer use --full 的 GUI 任务上下文；如果没有这行代码，普通兼容工具测试会被过度拦截。
            output = agent._execute_tool(ToolCall(name="mcp__computer-use__left_click", arguments={"window": {"app_id": "mspaint", "window_id": "hwnd:9001"}, "x": 10, "y": 10, "reason": "phase41 blind action gate"}))  # 修改代码+Phase41McpV2Migration: 通过 v2 MCP 左键点击触发同一套动作门禁；如果没有这行代码，测试会继续调用已删除的旧 _computer_action。

            self.assertIn("先观察", output)  # 新增代码+ObserveBeforeActionGate: 断言返回指导模型先观察；如果没有这行代码，模型可能不知道下一步该怎么纠正。
            self.assertIn("mcp__computer-use__observe", output)  # 修改代码+Phase41McpV2Migration: 断言拒绝信息点名新的 v2 观察工具；如果没有这行代码，测试会错误要求模型继续使用旧隐藏入口。
            self.assertEqual(backend.actions, [])  # 新增代码+ObserveBeforeActionGate: 断言后端没有收到点击；如果没有这行代码，表面拒绝但实际动作的回归无法发现。
    # 新增代码+ObserveBeforeActionGate: 函数段结束，test_full_mode_rejects_mouse_keyboard_action_before_model_visible_observation 到此结束；如果没有这个边界说明，用户不容易看出盲动门禁验收范围。

    def test_full_mode_rejects_mouse_keyboard_action_before_agent_owned_launch(self) -> None:  # 新增代码+AgentOwnedLaunchGate: 函数段开始，验证本机应用 full 任务即使看过旧窗口截图，也必须先 launch_app 取得 agent-owned 窗口；如果没有这个测试，模型会继续在没打开软件前操作旧窗口。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+AgentOwnedLaunchGate: 创建临时目录隔离 agent 工作区；如果没有这行代码，测试可能污染真实项目 memory。
            backend = MemoryComputerUseBackend(windows=[{"app_id": "mspaint", "window_id": "hwnd:old-paint", "title_preview": "Old Paint", "rect": {"left": 0, "top": 0, "right": 300, "bottom": 200}}])  # 新增代码+AgentOwnedLaunchGate: 准备一个用户旧 Paint 窗口；如果没有这行代码，无法复现模型观察旧窗口后误操作的问题。
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="unused")]), workspace=Path(raw_dir), ask_permission=lambda action: (_ for _ in ()).throw(AssertionError("pre-launch action should be rejected before permission")), debug_enabled=False)  # 新增代码+AgentOwnedLaunchGate: 创建真实 agent 且权限若被调用就失败；如果没有这行代码，测试无法证明拒绝发生在真实鼠标键盘前。
            agent.computer_use_controller = ComputerUseController(backend=backend)  # 新增代码+AgentOwnedLaunchGate: 注入内存 controller；如果没有这行代码，测试会误用默认真实后端。
            agent.desktop_task_context = {"active": True, "requires_gui_actions": True, "target_app_hint": "mspaint"}  # 新增代码+AgentOwnedLaunchGate: 模拟用户要求本机画图软件的 full 任务；如果没有这行代码，agent 不知道本轮需要先绑定目标应用。
            run_helpers_from_core.record_observation(agent, "computer_use_observe", {"action": "get_window_state", "ok": True, "data": {"image_result_count": 1, "screenshot_captured": True, "state": {"image_result_count": 1, "screenshot_captured": True}}})  # 修改代码+Phase41McpV2Migration: 通过公共 helper 人工放入一次成功截图观察；如果没有这行代码，测试会继续依赖已迁出的 _record_observation 私有方法。
            output = agent._execute_tool(ToolCall(name="mcp__computer-use__left_click", arguments={"window": {"app_id": "mspaint", "window_id": "hwnd:old-paint"}, "x": 10, "y": 10, "reason": "phase41 agent-owned launch gate"}))  # 修改代码+Phase41McpV2Migration: 通过 v2 MCP 左键点击触发 agent-owned 门禁；如果没有这行代码，测试会继续调用已删除的旧 _computer_action。

            self.assertIn("launch_app", output)  # 新增代码+AgentOwnedLaunchGate: 断言纠偏信息要求先启动应用；如果没有这行代码，模型可能不知道下一步要打开软件。
            self.assertIn("agent-owned", output)  # 新增代码+AgentOwnedLaunchGate: 断言拒绝原因指向自有窗口边界；如果没有这行代码，用户无法区分旧窗口观察和新窗口绑定。
            self.assertEqual(backend.actions, [])  # 新增代码+AgentOwnedLaunchGate: 断言旧窗口没有收到鼠标动作；如果没有这行代码，表面拒绝但实际点击的回归无法发现。
    # 新增代码+AgentOwnedLaunchGate: 函数段结束，test_full_mode_rejects_mouse_keyboard_action_before_agent_owned_launch 到此结束；如果没有这个边界说明，用户不容易看出先启动再操作的验收范围。

    def test_phase41_cli_contract_and_visible_terminal_scenario_tokens(self) -> None:  # 新增代码+Phase41WindowsImageResults: 验证 CLI 合同和真实终端场景 token 稳定；如果没有这个测试，Phase41 可能无法被 start_oauth_agent.bat 验收。
        report = run_phase41_image_results_contract()  # 新增代码+Phase41WindowsImageResults: 运行 Phase41 安全自检合同；如果没有这行代码，CLI 输出没有真实依据。
        cli_line = phase41_cli_line(report)  # 新增代码+Phase41WindowsImageResults: 生成终端可复制的一行结果；如果没有这行代码，场景断言无法稳定匹配。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase41_windows_image_results.json")  # 新增代码+Phase41WindowsImageResults: 指向 Phase41 真实终端场景文件；如果没有这行代码，测试无法确认验收入口存在。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase41WindowsImageResults: 读取场景 JSON 文本；如果没有这行代码，无法检查 token 是否写进验收 prompt。

        self.assertTrue(report["artifact"])  # 新增代码+Phase41WindowsImageResults: 断言合同证明截图 artifact 存在；如果没有这行代码，OK token 可能过早出现。
        self.assertTrue(report["image_block"])  # 新增代码+Phase41WindowsImageResults: 断言合同证明 image block 存在；如果没有这行代码，模型可见图片协议可能缺失。
        self.assertTrue(report["agent_artifact"])  # 新增代码+Phase41WindowsImageResults: 断言合同证明 agent 登记 artifact；如果没有这行代码，长任务上下文仍会丢图。
        self.assertTrue(report["sensitive_text_hidden"])  # 新增代码+Phase41WindowsImageResults: 断言合同证明敏感 UIA 未泄露；如果没有这行代码，安全边界无法验收。
        self.assertIn(PHASE41_WINDOWS_IMAGE_RESULTS_OK_TOKEN, cli_line)  # 新增代码+Phase41WindowsImageResults: 断言 OK token 出现在 CLI 行；如果没有这行代码，真实终端无法快速判断成功。
        self.assertIn("actions_expanded=false", cli_line)  # 新增代码+Phase41WindowsImageResults: 断言本阶段没有扩大动作能力；如果没有这行代码，审计可能误以为 Phase41 添加了高风险动作。
        self.assertIn(PHASE41_WINDOWS_IMAGE_RESULTS_MARKER, scenario_text)  # 新增代码+Phase41WindowsImageResults: 断言场景包含成功标记；如果没有这行代码，真实终端验收无法等待正确输出。
        self.assertIn(PHASE41_WINDOWS_IMAGE_RESULTS_OK_TOKEN, scenario_text)  # 新增代码+Phase41WindowsImageResults: 断言场景包含 OK token；如果没有这行代码，验收无法证明自检成功。
        self.assertIn("actions_expanded=false", scenario_text)  # 新增代码+Phase41WindowsImageResults: 断言场景检查动作未扩大；如果没有这行代码，高风险范围变化可能漏审。


if __name__ == "__main__":  # 新增代码+Phase41WindowsImageResults: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase41WindowsImageResults: 启动 unittest 主函数；如果没有这行代码，直接运行文件不会执行任何测试。
