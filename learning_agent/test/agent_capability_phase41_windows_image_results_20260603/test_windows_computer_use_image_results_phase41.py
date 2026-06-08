import json  # 新增代码+Phase41WindowsImageResults: 导入 JSON 工具用于检查 image result block 是否泄露敏感文本；如果没有这行代码，测试无法可靠审计结构化结果。
import tempfile  # 新增代码+Phase41WindowsImageResults: 导入临时目录工具隔离截图 evidence 文件；如果没有这行代码，测试会污染真实 memory 目录。
import unittest  # 新增代码+Phase41WindowsImageResults: 导入 unittest 测试框架；如果没有这行代码，本阶段测试不会被 Python 测试发现。
from pathlib import Path  # 新增代码+Phase41WindowsImageResults: 导入 Path 处理截图 artifact 路径；如果没有这行代码，路径检查会变成脆弱字符串拼接。

from learning_agent.computer_use.controller import ComputerUseController, WindowsComputerUseBackend  # 新增代码+Phase41WindowsImageResults: 导入控制器和 Windows 后端验证真实 observe 链路；如果没有这行代码，只能孤立测试 evidence。
from learning_agent.computer_use.evidence import PHASE41_IMAGE_RESULT_MODEL, PHASE41_WINDOWS_IMAGE_RESULTS_MARKER, PHASE41_WINDOWS_IMAGE_RESULTS_OK_TOKEN, ComputerUseEvidenceStore, collect_image_result_blocks, phase41_cli_line, run_phase41_image_results_contract  # 新增代码+Phase41WindowsImageResults: 导入 Phase41 image result 合同入口；如果没有这行代码，红灯无法证明模型可见图片块尚未补齐。
from learning_agent.computer_use.helper_client import StaticWindowObservationHelper, WindowObservationPayload  # 新增代码+Phase41WindowsImageResults: 导入静态观察 helper 和 payload；如果没有这行代码，测试无法在不碰真实桌面的情况下模拟截图。
from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase41WindowsImageResults: 导入静态窗口 inventory；如果没有这行代码，测试会依赖真实用户桌面窗口。
from learning_agent.core.agent import LearningAgent, ModelMessage, ToolCallingFakeModel  # 新增代码+Phase41WindowsImageResults: 导入真实 agent 和假模型；如果没有这行代码，无法证明图片 artifact 会进入 active_artifacts。


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
            output = agent._computer_observe({"action": "get_window_state", "window": window})  # 新增代码+Phase41WindowsImageResults: 通过 agent 工具入口读取窗口状态；如果没有这行代码，active_artifacts 登记逻辑不会运行。
            image_artifacts = [path for path in agent.active_artifacts if str(evidence_root) in path]  # 新增代码+Phase41WindowsImageResults: 筛选本次截图 artifact；如果没有这行代码，无法排除其它历史产物。
            observation_kinds = [event["kind"] for event in agent.observation_events]  # 新增代码+Phase41WindowsImageResults: 收集观察事件类型；如果没有这行代码，无法验证审计事件。

            self.assertIn("Computer Use Image Results", output)  # 新增代码+Phase41WindowsImageResults: 断言 agent 工具文本也包含图片区块；如果没有这行代码，controller 改动可能没有传到 agent。
            self.assertEqual(len(image_artifacts), 1)  # 新增代码+Phase41WindowsImageResults: 断言 active_artifacts 记录一张截图；如果没有这行代码，模型恢复上下文时找不到截图。
            self.assertTrue(Path(image_artifacts[0]).exists())  # 新增代码+Phase41WindowsImageResults: 断言登记的 artifact 路径真实存在；如果没有这行代码，active_artifacts 可能保存假路径。
            self.assertIn("computer_use_image_result", observation_kinds)  # 新增代码+Phase41WindowsImageResults: 断言图片结果登记进入 observation；如果没有这行代码，审计无法解释截图为何成为活跃产物。

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
