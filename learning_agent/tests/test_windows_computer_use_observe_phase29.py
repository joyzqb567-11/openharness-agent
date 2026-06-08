import json  # 新增代码+Phase29ComputerUse: 导入 JSON 解析工具用于读取 evidence metadata；如果没有这行代码，测试无法确认落盘证据内容。 
import tempfile  # 新增代码+Phase29ComputerUse: 导入临时目录工具隔离 evidence 文件；如果没有这行代码，测试会污染真实 memory 目录。 
import unittest  # 新增代码+Phase29ComputerUse: 导入 unittest 测试框架；如果没有这行代码，本文件无法定义 Phase 29 自动化测试。 
from pathlib import Path  # 新增代码+Phase29ComputerUse: 导入 Path 方便检查证据文件路径；如果没有这行代码，测试路径处理会变成脆弱字符串拼接。 

from learning_agent.computer_use.controller import ComputerUseController, WindowsComputerUseBackend  # 新增代码+Phase29ComputerUse: 导入控制器和 Windows 后端作为被测对象；如果没有这行代码，测试无法覆盖真实 observe 入口。 
from learning_agent.computer_use.evidence import ComputerUseEvidenceStore  # 新增代码+Phase29ComputerUse: 导入证据仓库期望接口；如果没有这行代码，红灯无法证明 evidence 模块缺失。 
from learning_agent.computer_use.helper_client import StaticWindowObservationHelper, WindowObservationPayload  # 新增代码+Phase29ComputerUse: 导入静态观察 helper 和 payload 合同；如果没有这行代码，测试无法在不碰真实桌面的情况下模拟截图/UIA。 
from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase29ComputerUse: 复用 Phase 28 静态窗口 inventory；如果没有这行代码，测试会依赖真实 Windows 桌面窗口。 


class WindowsComputerUseObservePhase29Tests(unittest.TestCase):  # 新增代码+Phase29ComputerUse: 定义 Phase 29 只读观察测试集合；如果没有这个类，unittest 不会发现本阶段测试。 
    def _raw_windows(self) -> list[dict[str, object]]:  # 新增代码+Phase29ComputerUse: 准备稳定的静态窗口输入；如果没有这段函数，每个测试都要重复构造窗口记录。 
        return [  # 新增代码+Phase29ComputerUse: 返回静态窗口列表；如果没有这行代码，测试没有可信窗口样本。 
            {"hwnd": 24680, "pid": 100, "process_name": "notepad.exe", "class_name": "Notepad", "title": "记事本 - Phase29", "rect": {"left": 10, "top": 20, "right": 310, "bottom": 220}},  # 新增代码+Phase29ComputerUse: 提供安全可观察窗口；如果没有这行代码，get_window_state 没有合法目标。 
        ]  # 新增代码+Phase29ComputerUse: 结束静态窗口列表；如果没有这行代码，Python 列表语法不完整。 

    def _controller_with_static_helper(self, evidence_root: Path) -> ComputerUseController:  # 新增代码+Phase29ComputerUse: 构造带静态截图/UIA helper 的控制器；如果没有这段函数，测试搭建会重复且容易漏掉依赖。 
        inventory = StaticWindowsWindowInventory(raw_windows=self._raw_windows(), captured_at="2026-06-03T00:00:00Z")  # 新增代码+Phase29ComputerUse: 使用静态 inventory 固定窗口和时间；如果没有这行代码，测试结果会随真实桌面变化。 
        payload = WindowObservationPayload(  # 新增代码+Phase29ComputerUse: 构造 helper 返回的窗口观察 payload；如果没有这段代码，后端没有截图和 UIA 输入可保存。 
            screenshot_bytes=b"phase29-fake-png-bytes",  # 新增代码+Phase29ComputerUse: 提供假截图字节证明截图 artifact 会落盘；如果没有这行代码，测试无法验证 screenshot_path。 
            screenshot_format="png",  # 新增代码+Phase29ComputerUse: 声明截图格式用于生成文件扩展名；如果没有这行代码，证据文件类型不明确。 
            screenshot_width=123,  # 新增代码+Phase29ComputerUse: 提供 helper 测得截图宽度；如果没有这行代码，测试无法确认尺寸来自 helper 而不是旧 rect 占位。 
            screenshot_height=45,  # 新增代码+Phase29ComputerUse: 提供 helper 测得截图高度；如果没有这行代码，测试无法确认截图高度合同。 
            accessibility_text="标题 安全文本\npassword: should disappear\n按钮 确定\n" + ("长文本 " * 200),  # 新增代码+Phase29ComputerUse: 提供包含敏感行和超长 UIA 的文本；如果没有这行代码，过滤和截断不会被测试覆盖。 
            focused_element="编辑框",  # 新增代码+Phase29ComputerUse: 提供焦点元素摘要；如果没有这行代码，focused_element 字段无法验证。 
            selected_text="选择的安全文本",  # 新增代码+Phase29ComputerUse: 提供选中文本摘要；如果没有这行代码，selected_text_preview 字段无法验证。 
            document_text="文档安全摘要",  # 新增代码+Phase29ComputerUse: 提供文档文本摘要；如果没有这行代码，document_text_preview 字段无法验证。 
            helper_name="static_phase29_helper",  # 新增代码+Phase29ComputerUse: 标记 helper 来源；如果没有这行代码，metadata 无法说明证据来自哪里。 
            helper_available=True,  # 新增代码+Phase29ComputerUse: 声明 helper 可用；如果没有这行代码，状态可能误判为无截图能力。 
            helper_reason="Phase 29 static helper",  # 新增代码+Phase29ComputerUse: 提供 helper 说明；如果没有这行代码，证据原因字段不清楚。 
        )  # 新增代码+Phase29ComputerUse: 结束 payload 构造；如果没有这行代码，Python 调用语法不完整。 
        helper = StaticWindowObservationHelper(payloads={"hwnd:24680": payload})  # 新增代码+Phase29ComputerUse: 用 window_id 绑定静态观察 payload；如果没有这行代码，helper 不知道给哪个窗口返回证据。 
        store = ComputerUseEvidenceStore(evidence_root=evidence_root)  # 新增代码+Phase29ComputerUse: 创建证据仓库并指向临时目录；如果没有这行代码，证据不会落到可检查位置。 
        backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=False, evidence_store=store, observation_helper=helper)  # 新增代码+Phase29ComputerUse: 创建只读 Windows 后端并注入证据能力；如果没有这行代码，测试会停留在 Phase 28 占位。 
        return ComputerUseController(backend=backend)  # 新增代码+Phase29ComputerUse: 返回统一控制器入口；如果没有这行代码，测试无法覆盖真实 computer_observe 调度路径。 

    def test_get_window_state_saves_screenshot_and_metadata_artifacts(self) -> None:  # 新增代码+Phase29ComputerUse: 验证窗口状态会保存截图和 metadata artifact；如果没有这个测试，Phase 29 可能只返回内存字段不落盘。 
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase29ComputerUse: 创建临时 evidence 根目录；如果没有这行代码，测试文件会残留在项目 memory 中。 
            controller = self._controller_with_static_helper(Path(temp_dir))  # 新增代码+Phase29ComputerUse: 构造带静态 helper 的控制器；如果没有这行代码，后续 observe 没有被测对象。 
            window = controller.observe({"action": "list_windows"}).data["windows"][0]  # 新增代码+Phase29ComputerUse: 先通过可信观察获取 window 引用；如果没有这行代码，get_window_state 会收到伪造目标。 
            state_result = controller.observe({"action": "get_window_state", "window": window})  # 新增代码+Phase29ComputerUse: 请求窗口状态；如果没有这行代码，无法触发 evidence 保存。 
            state = state_result.data["state"]  # 新增代码+Phase29ComputerUse: 取出状态主体；如果没有这行代码，断言目标不清楚。 
            metadata_path = Path(state["evidence_path"])  # 新增代码+Phase29ComputerUse: 把 evidence_path 转成 Path；如果没有这行代码，无法检查 metadata 是否存在。 
            screenshot_path = Path(state["screenshot_path"])  # 新增代码+Phase29ComputerUse: 把 screenshot_path 转成 Path；如果没有这行代码，无法检查截图 artifact 是否存在。 
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))  # 新增代码+Phase29ComputerUse: 读取 metadata JSON；如果没有这行代码，测试无法确认证据内容。 

            self.assertTrue(state_result.ok)  # 新增代码+Phase29ComputerUse: 断言窗口状态读取成功；如果没有这行代码，失败结果也可能继续检查文件。 
            self.assertTrue(metadata_path.exists())  # 新增代码+Phase29ComputerUse: 断言 metadata artifact 已落盘；如果没有这行代码，证据链缺文件也不会失败。 
            self.assertTrue(screenshot_path.exists())  # 新增代码+Phase29ComputerUse: 断言截图 artifact 已落盘；如果没有这行代码，截图保存缺失不会被发现。 
            self.assertTrue(state["screenshot_id"].startswith("computer-window-"))  # 新增代码+Phase29ComputerUse: 断言截图 id 使用稳定前缀；如果没有这行代码，后续审计无法识别 Computer Use 证据。 
            self.assertEqual(state["screenshot_width"], 123)  # 新增代码+Phase29ComputerUse: 断言状态宽度来自 helper 截图；如果没有这行代码，旧 rect 占位可能误通过。 
            self.assertEqual(state["screenshot_height"], 45)  # 新增代码+Phase29ComputerUse: 断言状态高度来自 helper 截图；如果没有这行代码，截图尺寸合同不稳定。 
            self.assertEqual(state["screenshot_origin"], {"x": 10, "y": 20})  # 新增代码+Phase29ComputerUse: 断言窗口原点仍来自可信 rect；如果没有这行代码，窗口相对坐标基础可能丢失。 
            self.assertEqual(metadata["screenshot"]["captured"], True)  # 新增代码+Phase29ComputerUse: 断言 metadata 记录截图已捕获；如果没有这行代码，metadata 可能只保存占位。 
            self.assertEqual(metadata["window"]["window_id"], "hwnd:24680")  # 新增代码+Phase29ComputerUse: 断言 metadata 关联正确窗口；如果没有这行代码，证据可能无法回溯到目标窗口。 

    def test_get_window_state_bounds_and_filters_uia_text(self) -> None:  # 新增代码+Phase29ComputerUse: 验证 UIA 文本会过滤敏感行并限制长度；如果没有这个测试，模型可能看到未过滤的 password/token 文本。 
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase29ComputerUse: 创建临时 evidence 根目录；如果没有这行代码，metadata 检查会污染真实文件。 
            controller = self._controller_with_static_helper(Path(temp_dir))  # 新增代码+Phase29ComputerUse: 构造控制器；如果没有这行代码，测试无法触发 Phase 29 helper。 
            window = controller.observe({"action": "list_windows"}).data["windows"][0]  # 新增代码+Phase29ComputerUse: 获取可信窗口引用；如果没有这行代码，状态查询目标不合法。 
            state = controller.observe({"action": "get_window_state", "window": window}).data["state"]  # 新增代码+Phase29ComputerUse: 读取窗口状态并取出摘要；如果没有这行代码，无法检查 UIA 摘要。 
            metadata = json.loads(Path(state["evidence_path"]).read_text(encoding="utf-8"))  # 新增代码+Phase29ComputerUse: 读取 metadata 验证落盘摘要也被过滤；如果没有这行代码，只能检查内存响应。 

            self.assertIn("标题 安全文本", state["accessibility_excerpt"])  # 新增代码+Phase29ComputerUse: 断言安全 UIA 文本保留；如果没有这行代码，过滤可能过度删除可用信息。 
            self.assertNotIn("password", state["accessibility_excerpt"].lower())  # 新增代码+Phase29ComputerUse: 断言响应不暴露 password 行；如果没有这行代码，敏感 UIA 可能泄露给模型。 
            self.assertLessEqual(len(state["accessibility_excerpt"]), 600)  # 新增代码+Phase29ComputerUse: 断言响应摘要有长度上限；如果没有这行代码，超长 UIA 会挤爆上下文。 
            self.assertTrue(state["accessibility_truncated"])  # 新增代码+Phase29ComputerUse: 断言截断状态可见；如果没有这行代码，模型不知道摘要不完整。 
            self.assertGreaterEqual(state["accessibility_filtered_line_count"], 1)  # 新增代码+Phase29ComputerUse: 断言过滤计数可见；如果没有这行代码，用户无法审计敏感行被移除。 
            self.assertNotIn("password", json.dumps(metadata, ensure_ascii=False).lower())  # 新增代码+Phase29ComputerUse: 断言 metadata 也不保存敏感 password 文本；如果没有这行代码，敏感内容可能从 artifact 泄露。 
            self.assertEqual(state["focused_element"], "编辑框")  # 新增代码+Phase29ComputerUse: 断言焦点元素摘要保留；如果没有这行代码，UIA 关键摘要可能丢失。 
            self.assertEqual(state["selected_text_preview"], "选择的安全文本")  # 新增代码+Phase29ComputerUse: 断言选中文本摘要保留；如果没有这行代码，后续动作判断缺上下文。 
            self.assertEqual(state["document_text_preview"], "文档安全摘要")  # 新增代码+Phase29ComputerUse: 断言文档摘要保留；如果没有这行代码，模型看不到文档级上下文。 

    def test_windows_backend_status_reports_phase29_evidence_capability(self) -> None:  # 新增代码+Phase29ComputerUse: 验证状态报告 evidence store 和 helper 边界；如果没有这个测试，用户无法从 status 判断 Phase 29 是否接入。 
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase29ComputerUse: 创建临时 evidence 根目录；如果没有这行代码，状态中的路径可能指向真实 memory。 
            controller = self._controller_with_static_helper(Path(temp_dir))  # 新增代码+Phase29ComputerUse: 构造带 evidence 能力的控制器；如果没有这行代码，状态没有被测后端。 
            status = controller.status()["backend"]  # 新增代码+Phase29ComputerUse: 读取后端状态；如果没有这行代码，无法断言 Phase 29 字段。 

            self.assertEqual(status["evidence_mode"], "window_state_artifact")  # 新增代码+Phase29ComputerUse: 断言状态显示窗口状态 artifact 模式；如果没有这行代码，状态可能仍停留在 Phase 28 inventory。 
            self.assertEqual(Path(status["evidence_root"]), Path(temp_dir))  # 新增代码+Phase29ComputerUse: 断言 evidence 根目录可见；如果没有这行代码，用户不知道证据保存在哪里。 
            self.assertTrue(status["observation_helper_available"])  # 新增代码+Phase29ComputerUse: 断言 helper 可用状态可见；如果没有这行代码，截图能力边界不透明。 
            self.assertEqual(status["observation_helper"], "static_phase29_helper")  # 新增代码+Phase29ComputerUse: 断言 helper 名称进入状态；如果没有这行代码，排查证据来源会困难。 


if __name__ == "__main__":  # 新增代码+Phase29ComputerUse: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式启动测试。 
    unittest.main()  # 新增代码+Phase29ComputerUse: 启动 unittest 主函数；如果没有这行代码，直接运行文件不会执行任何测试。 
