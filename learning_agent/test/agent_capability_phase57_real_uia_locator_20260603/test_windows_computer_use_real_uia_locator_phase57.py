import json  # 新增代码+Phase57RealUiaLocator: 导入 JSON 用来检查 UIA 树不会泄露敏感原文；如果没有这行代码，测试无法做全局泄露扫描。
import unittest  # 新增代码+Phase57RealUiaLocator: 导入 unittest 承载 Phase57 自动化测试；如果没有这行代码，测试文件无法被标准测试命令发现和执行。
from pathlib import Path  # 新增代码+Phase57RealUiaLocator: 导入 Path 稳定读取验收场景 JSON；如果没有这行代码，Windows 路径拼接会更脆弱。
from typing import Any  # 新增代码+Phase57RealUiaLocator: 导入 Any 标注 fake provider 的 JSON 风格数据；如果没有这行代码，测试辅助类边界不清楚。

from learning_agent.computer_use.native_helper_v2 import WindowsNativeHelperV2Worker  # 新增代码+Phase57RealUiaLocator: 导入 helper v2 worker 验证 read_uia_tree 会接入 Phase57；如果没有这行代码，Phase57 可能只做独立模块而没有协议入口。
from learning_agent.computer_use.real_uia_locator import PHASE57_WINDOWS_REAL_UIA_LOCATOR_MARKER, PHASE57_WINDOWS_REAL_UIA_LOCATOR_OK_TOKEN, PowerShellUiaTreeProvider, SemanticControlLocator, WindowsRealUiaLocatorRuntime, phase57_cli_line, run_phase57_real_uia_locator_contract  # 新增代码+Phase57RealUiaLocator: 导入计划中的真实 UIA 树和语义定位入口；如果没有这行代码，红灯会证明 Phase57 生产入口尚未实现。


class FakePhase57Provider:  # 新增代码+Phase57RealUiaLocator: 类段开始，提供可控 UIA provider 供单测注入；如果没有这个类，单测会被真实桌面状态影响。
    def __init__(self, tree: dict[str, Any]) -> None:  # 新增代码+Phase57RealUiaLocator: 函数段开始，保存 fake 树；如果没有这段函数，provider 没有稳定的返回数据。
        self.tree = dict(tree)  # 新增代码+Phase57RealUiaLocator: 复制树数据避免测试外部对象被污染；如果没有这行代码，后续断言可能受共享引用影响。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，FakePhase57Provider.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，模拟真实 PowerShell UIA 后端可用；如果没有这段函数，runtime 无法判断 provider 是否可用。
        return {"available": True, "backend": "powershell_dotnet_uia", "real_provider_required": True, "actions_expanded": False}  # 新增代码+Phase57RealUiaLocator: 返回可用状态且保持只读；如果没有这行代码，runtime 可能把 fake provider 当成不可用。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，FakePhase57Provider.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def read_window_tree(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，模拟按窗口读取 UIA 树；如果没有这段函数，runtime 没有树输入。
        _ = window  # 新增代码+Phase57RealUiaLocator: 明确 fake provider 不依赖窗口内容；如果没有这行代码，读者可能误以为测试漏传窗口。
        return {"captured": True, "tree": self.tree, "backend": "powershell_dotnet_uia", "real_provider_used": True, "reason": "fake provider contract"}  # 新增代码+Phase57RealUiaLocator: 返回与真实 provider 一致的结构；如果没有这行代码，测试无法驱动清洗和定位逻辑。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，FakePhase57Provider.read_window_tree 到此结束；如果没有这个边界说明，初学者不容易看出读取范围。
# 新增代码+Phase57RealUiaLocator: 类段结束，FakePhase57Provider 到此结束；如果没有这个边界说明，初学者不容易看出 fake provider 范围。


class WindowsComputerUseRealUiaLocatorPhase57Tests(unittest.TestCase):  # 新增代码+Phase57RealUiaLocator: 类段开始，组织 Phase57 真实 UIA 树和语义定位测试；如果没有这个类，unittest 不会运行本阶段门禁。
    def _window(self) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，提供安全窗口引用；如果没有这段函数，每个测试都会重复拼接窗口数据。
        return {"window_id": "hwnd:5701", "hwnd": 5701, "title_preview": "LearningAgent-Phase57-Contract", "app_id": "notepad.exe", "rect": {"left": 10, "top": 20, "right": 620, "bottom": 420}}  # 新增代码+Phase57RealUiaLocator: 返回带 hwnd 和安全标题的窗口；如果没有这行代码，runtime 无法证明只面向自有安全窗口。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口样本范围。

    def _tree(self) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，构造带按钮、编辑区和敏感字段的 UIA 树；如果没有这段函数，测试缺少完整控件样本。
        return {"node_id": "0", "name": "LearningAgent-Phase57-Contract", "role": "Window", "automation_id": "root", "class_name": "Notepad", "bounds": {"left": 10, "top": 20, "right": 620, "bottom": 420, "width": 610, "height": 400}, "enabled": True, "clickable": False, "editable": False, "children": [{"node_id": "0.0", "name": "Save", "role": "Button", "automation_id": "save", "class_name": "Button", "bounds": {"left": 30, "top": 48, "right": 120, "bottom": 82, "width": 90, "height": 34}, "enabled": True, "clickable": True, "editable": False, "children": []}, {"node_id": "0.1", "name": "Document", "role": "Edit", "automation_id": "editor", "class_name": "Edit", "bounds": {"left": 30, "top": 90, "right": 590, "bottom": 390, "width": 560, "height": 300}, "enabled": True, "clickable": True, "editable": True, "children": []}, {"node_id": "0.2", "name": "password: phase57-secret", "role": "Edit", "automation_id": "secret", "class_name": "Edit", "bounds": {"left": 30, "top": 400, "right": 590, "bottom": 430, "width": 560, "height": 30}, "enabled": True, "clickable": True, "editable": True, "children": []}]}  # 新增代码+Phase57RealUiaLocator: 返回完整树样本；如果没有这行代码，字段完整性、脱敏和定位都没有输入。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，_tree 到此结束；如果没有这个边界说明，初学者不容易看出树样本范围。

    def test_powershell_provider_status_reports_real_uia_dependency_without_fake_success(self) -> None:  # 新增代码+Phase57RealUiaLocator: 函数段开始，验证 provider 状态来自 PowerShell/.NET UIA 探针；如果没有这个测试，依赖缺失可能被假成功掩盖。
        def fake_runner(command: list[str], timeout_seconds: float) -> dict[str, Any]:  # 新增代码+Phase57RealUiaLocator: 函数段开始，模拟 PowerShell 命令成功返回 JSON；如果没有这段函数，单测会依赖本机 PowerShell 状态。
            _ = command  # 新增代码+Phase57RealUiaLocator: 明确本 fake 不检查命令细节；如果没有这行代码，读者可能误以为遗漏断言。
            _ = timeout_seconds  # 新增代码+Phase57RealUiaLocator: 明确本 fake 不检查超时时间；如果没有这行代码，读者可能误以为遗漏参数。
            return {"returncode": 0, "stdout": "{\"available\": true, \"root_role\": \"ControlType.Pane\"}", "stderr": ""}  # 新增代码+Phase57RealUiaLocator: 模拟 .NET UIAutomationClient 可用；如果没有这行代码，provider.status 没有成功输入。
        # 新增代码+Phase57RealUiaLocator: 函数段结束，fake_runner 到此结束；如果没有这个边界说明，初学者不容易看出 fake 命令范围。
        provider = PowerShellUiaTreeProvider(platform="win32", runner=fake_runner)  # 新增代码+Phase57RealUiaLocator: 创建注入 fake runner 的 provider；如果没有这行代码，测试不能隔离真实系统。
        status = provider.status()  # 新增代码+Phase57RealUiaLocator: 读取 provider 状态；如果没有这行代码，断言没有实际结果。
        self.assertTrue(status["available"])  # 新增代码+Phase57RealUiaLocator: 断言可用状态为真；如果没有这行代码，可用性判断退化不会被发现。
        self.assertEqual(status["backend"], "powershell_dotnet_uia")  # 新增代码+Phase57RealUiaLocator: 断言后端名称稳定；如果没有这行代码，外部 agent 难以识别真实 UIA 来源。
        self.assertTrue(status["real_provider_required"])  # 新增代码+Phase57RealUiaLocator: 断言这不是 fake provider 验收；如果没有这行代码，后续矩阵可能把合同测试冒充真实能力。
        self.assertFalse(status["actions_expanded"])  # 新增代码+Phase57RealUiaLocator: 断言状态检查不扩大动作面；如果没有这行代码，只读阶段安全边界可能漂移。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，test_powershell_provider_status_reports_real_uia_dependency_without_fake_success 到此结束；如果没有这个边界说明，初学者不容易看出状态测试范围。

    def test_runtime_observe_window_returns_fields_and_redacts_sensitive_text(self) -> None:  # 新增代码+Phase57RealUiaLocator: 函数段开始，验证真实 UIA runtime 输出字段完整且脱敏；如果没有这个测试，控件树可能缺字段或泄露密码。
        runtime = WindowsRealUiaLocatorRuntime(platform="win32", provider=FakePhase57Provider(self._tree()))  # 新增代码+Phase57RealUiaLocator: 创建注入树的 runtime；如果没有这行代码，测试无法驱动 observe_window。
        result = runtime.observe_window(self._window())  # 新增代码+Phase57RealUiaLocator: 观察安全窗口 UIA 树；如果没有这行代码，断言没有实际输出。
        encoded = json.dumps(result, ensure_ascii=False).lower()  # 新增代码+Phase57RealUiaLocator: 序列化结果做全局泄露检查；如果没有这行代码，只看单字段会漏掉敏感值。
        self.assertTrue(result["captured"])  # 新增代码+Phase57RealUiaLocator: 断言树读取成功；如果没有这行代码，失败结果也可能通过后续字段检查。
        self.assertTrue(result["real_uia_tree"])  # 新增代码+Phase57RealUiaLocator: 断言结果声明真实 UIA 树；如果没有这行代码，Phase57 可能退回占位树。
        self.assertEqual(result["node_count"], 4)  # 新增代码+Phase57RealUiaLocator: 断言根、按钮、编辑区、敏感节点都被遍历；如果没有这行代码，树遍历缺节点不会暴露。
        self.assertEqual(result["flat_nodes"][1]["automation_id"], "save")  # 新增代码+Phase57RealUiaLocator: 断言 automation_id 被保留；如果没有这行代码，语义定位会少一条重要线索。
        self.assertTrue(result["flat_nodes"][2]["editable"])  # 新增代码+Phase57RealUiaLocator: 断言可编辑提示存在；如果没有这行代码，type_into_control 无法安全选择输入目标。
        self.assertTrue(result["bounds_available"])  # 新增代码+Phase57RealUiaLocator: 断言边界框可用；如果没有这行代码，后续坐标落点无法校验。
        self.assertGreaterEqual(result["sensitive_text_filtered"], 1)  # 新增代码+Phase57RealUiaLocator: 断言敏感文本至少过滤一次；如果没有这行代码，密码字段泄露可能不被发现。
        self.assertNotIn("phase57-secret", encoded)  # 新增代码+Phase57RealUiaLocator: 断言具体敏感值没有出现在任何响应里；如果没有这行代码，脱敏函数回归不会被抓住。
        self.assertFalse(result["actions_expanded"])  # 新增代码+Phase57RealUiaLocator: 断言 Phase57 仍是只读观察；如果没有这行代码，安全边界可能被误扩展。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，test_runtime_observe_window_returns_fields_and_redacts_sensitive_text 到此结束；如果没有这个边界说明，初学者不容易看出 observe 测试范围。

    def test_semantic_locator_explains_candidate_count_confidence_and_bounds(self) -> None:  # 新增代码+Phase57RealUiaLocator: 函数段开始，验证语义定位器给出可解释选择；如果没有这个测试，locator 可能只返回一个黑盒节点。
        runtime = WindowsRealUiaLocatorRuntime(platform="win32", provider=FakePhase57Provider(self._tree()))  # 新增代码+Phase57RealUiaLocator: 创建带 fake 树的 runtime；如果没有这行代码，定位器没有节点输入。
        observed = runtime.observe_window(self._window())  # 新增代码+Phase57RealUiaLocator: 获取扁平节点列表；如果没有这行代码，locator 无法运行真实数据路径。
        locator = SemanticControlLocator()  # 新增代码+Phase57RealUiaLocator: 创建语义定位器；如果没有这行代码，测试不能验证定位逻辑。
        match = locator.find(observed["flat_nodes"], {"role": "Edit", "text": "Document", "bounds": {"left": 20, "top": 80, "right": 600, "bottom": 400}})  # 新增代码+Phase57RealUiaLocator: 按角色、文本和范围查找编辑区；如果没有这行代码，复合定位能力没有测试输入。
        self.assertTrue(match["matched"])  # 新增代码+Phase57RealUiaLocator: 断言定位成功；如果没有这行代码，空结果也可能被误用。
        self.assertEqual(match["control"]["automation_id"], "editor")  # 新增代码+Phase57RealUiaLocator: 断言选中编辑区；如果没有这行代码，locator 选错节点不会暴露。
        self.assertGreaterEqual(match["confidence"], 0.75)  # 新增代码+Phase57RealUiaLocator: 断言置信度足够高；如果没有这行代码，弱匹配可能被误当确定目标。
        self.assertGreaterEqual(match["candidate_count"], 1)  # 新增代码+Phase57RealUiaLocator: 断言候选数量可见；如果没有这行代码，调试时不知道竞争节点数量。
        self.assertIn("role", match["reason"])  # 新增代码+Phase57RealUiaLocator: 断言理由包含角色线索；如果没有这行代码，解释可能退化成空话。
        self.assertFalse(match["actions_expanded"])  # 新增代码+Phase57RealUiaLocator: 断言定位不触发真实动作；如果没有这行代码，只读定位边界可能漂移。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，test_semantic_locator_explains_candidate_count_confidence_and_bounds 到此结束；如果没有这个边界说明，初学者不容易看出定位测试范围。

    def test_helper_v2_read_uia_tree_uses_phase57_runtime_summary(self) -> None:  # 新增代码+Phase57RealUiaLocator: 函数段开始，验证 helper v2 的 read_uia_tree 不再只是占位树；如果没有这个测试，协议入口可能没有升级。
        runtime = WindowsRealUiaLocatorRuntime(platform="win32", provider=FakePhase57Provider(self._tree()))  # 新增代码+Phase57RealUiaLocator: 创建 Phase57 runtime；如果没有这行代码，worker 无法注入新 UIA 能力。
        worker = WindowsNativeHelperV2Worker(uia_locator_runtime=runtime)  # 新增代码+Phase57RealUiaLocator: 把 Phase57 runtime 注入 helper v2；如果没有这行代码，read_uia_tree 仍可能走 Phase55 占位。
        response = worker.handle({"op": "read_uia_tree", "window": self._window(), "locator": {"automation_id": "editor"}})  # 新增代码+Phase57RealUiaLocator: 通过 helper 协议读取树并定位编辑区；如果没有这行代码，协议接入没有真实调用证据。
        encoded = json.dumps(response, ensure_ascii=False).lower()  # 新增代码+Phase57RealUiaLocator: 序列化响应做敏感值检查；如果没有这行代码，worker 响应泄露不易发现。
        self.assertTrue(response["ok"])  # 新增代码+Phase57RealUiaLocator: 断言 helper 响应成功；如果没有这行代码，错误 envelope 也可能被当结果读取。
        self.assertTrue(response["result"]["real_uia_tree"])  # 新增代码+Phase57RealUiaLocator: 断言 helper 返回真实 UIA 树标志；如果没有这行代码，占位树可能继续误过。
        self.assertTrue(response["result"]["semantic_locator_available"])  # 新增代码+Phase57RealUiaLocator: 断言 helper 暴露定位器可用；如果没有这行代码，高层工具不知道能否查找控件。
        self.assertTrue(response["result"]["locator"]["matched"])  # 新增代码+Phase57RealUiaLocator: 断言 locator 在 helper 路径中成功；如果没有这行代码，树和定位可能割裂。
        self.assertFalse(response["result"]["raw_text_included"])  # 新增代码+Phase57RealUiaLocator: 断言 helper 不返回原始敏感文本；如果没有这行代码，协议可能泄露 UIA 原文。
        self.assertNotIn("phase57-secret", encoded)  # 新增代码+Phase57RealUiaLocator: 断言敏感值没有出现在 helper 响应；如果没有这行代码，脱敏回归不会被发现。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，test_helper_v2_read_uia_tree_uses_phase57_runtime_summary 到此结束；如果没有这个边界说明，初学者不容易看出 helper 接入测试范围。

    def test_phase57_cli_line_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase57RealUiaLocator: 函数段开始，验证 CLI 和真实终端验收场景 token 稳定；如果没有这个测试，controller 可能漏检关键能力。
        report = run_phase57_real_uia_locator_contract(real_smoke=False)  # 新增代码+Phase57RealUiaLocator: 运行跳过真实桌面的合同自检；如果没有这行代码，单测会打开真实窗口。
        cli_line = phase57_cli_line(report)  # 新增代码+Phase57RealUiaLocator: 生成稳定 CLI token 行；如果没有这行代码，场景和命令输出无法对齐。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase57_real_uia_locator.json")  # 新增代码+Phase57RealUiaLocator: 定位 Phase57 真实终端场景；如果没有这行代码，测试无法检查验收配置。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase57RealUiaLocator: 读取场景 JSON；如果没有这行代码，场景格式或 token 漏项不会暴露。
        expected_tokens = {PHASE57_WINDOWS_REAL_UIA_LOCATOR_MARKER, PHASE57_WINDOWS_REAL_UIA_LOCATOR_OK_TOKEN, "real_uia_tree=true", "semantic_locator=true", "helper_v2_uia=true", "safe_window_only=true", "raw_text_hidden=true", "actions_expanded=false"}  # 新增代码+Phase57RealUiaLocator: 定义 CLI 和场景都必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase57RealUiaLocator: 遍历每个稳定 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase57RealUiaLocator: 断言 CLI 行包含 token；如果没有这行代码，命令输出漂移不会被发现。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase57RealUiaLocator: 断言 debug log 检查包含 token；如果没有这行代码，真实终端日志可能漏检。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase57RealUiaLocator: 断言最终回答检查包含 token；如果没有这行代码，用户可见结果可能缺证据。
        self.assertIn("real_smoke=true", scenario["debug_log_contains"])  # 新增代码+Phase57RealUiaLocator: 断言真实终端场景必须跑真实 safe-window UIA smoke；如果没有这行代码，场景可能只跑 fake 合同。
        self.assertIn("real_smoke=true", scenario["event_answer_contains"])  # 新增代码+Phase57RealUiaLocator: 断言最终回答也必须包含真实 smoke 证据；如果没有这行代码，最终验收可能缺真实能力证明。
    # 新增代码+Phase57RealUiaLocator: 函数段结束，test_phase57_cli_line_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 场景测试范围。
# 新增代码+Phase57RealUiaLocator: 类段结束，WindowsComputerUseRealUiaLocatorPhase57Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase57RealUiaLocator: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase57RealUiaLocator: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行任何测试。
