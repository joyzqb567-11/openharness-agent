import json  # 新增代码+Phase30ComputerUseActionGate: 导入 JSON 工具用于检查审计内容是否泄露原始文本；如果没有这行代码，测试只能用脆弱的字符串拼接来判断敏感信息。
import tempfile  # 新增代码+Phase30ComputerUseActionGate: 导入临时目录工具隔离 durable lock 文件；如果没有这行代码，测试会污染真实 memory 目录。
import unittest  # 新增代码+Phase30ComputerUseActionGate: 导入 unittest 框架承载 Phase 30 行为测试；如果没有这行代码，本文件不会被自动化测试发现和执行。
from pathlib import Path  # 新增代码+Phase30ComputerUseActionGate: 导入 Path 统一处理 Windows 路径和临时目录；如果没有这行代码，锁目录拼接会变得脆弱。

from learning_agent.computer_use.controller import ComputerUseController, MemoryComputerUseBackend  # 新增代码+Phase30ComputerUseActionGate: 导入控制器和内存后端作为被测对象；如果没有这行代码，测试无法验证真实调度入口。
from learning_agent.computer_use.lock import ComputerUseLockManager  # 新增代码+Phase30ComputerUseActionGate: 导入 Phase 30 durable lock 管理器；如果没有这行代码，红灯无法证明当前缺少动作锁能力。


class WindowsComputerUseActionsPhase30Tests(unittest.TestCase):  # 新增代码+Phase30ComputerUseActionGate: 定义 Phase 30 动作门禁测试集合；如果没有这个类，unittest 不会组织这些安全行为测试。
    def _window(self) -> dict[str, object]:  # 新增代码+Phase30ComputerUseActionGate: 函数段开始，提供带 rect 的可信窗口样本；如果没有这段函数，每个测试都要重复构造窗口且容易字段不一致。
        return {"app_id": "notepad.exe", "window_id": "hwnd:3001", "title_preview": "Phase30 Notepad", "rect": {"left": 10, "top": 20, "right": 310, "bottom": 220}}  # 新增代码+Phase30ComputerUseActionGate: 返回包含窗口身份和几何信息的样本；如果没有这行代码，窗口相对坐标转换无法被测试。
    # 新增代码+Phase30ComputerUseActionGate: 函数段结束，_window 到此结束；如果没有这个边界注释，初学者不容易看出样本 helper 的范围。

    def _controller(self, lock_root: Path, session_id: str = "phase30-session") -> tuple[ComputerUseController, MemoryComputerUseBackend, ComputerUseLockManager, dict[str, object]]:  # 新增代码+Phase30ComputerUseActionGate: 函数段开始，创建带内存后端和锁管理器的控制器；如果没有这段函数，测试准备逻辑会重复且更难读。
        window = self._window()  # 新增代码+Phase30ComputerUseActionGate: 生成可信窗口样本；如果没有这行代码，后端没有可验证目标。
        backend = MemoryComputerUseBackend(windows=[window])  # 新增代码+Phase30ComputerUseActionGate: 创建只记录动作的内存后端；如果没有这行代码，测试可能误碰真实桌面。
        lock_manager = ComputerUseLockManager(base_dir=lock_root)  # 新增代码+Phase30ComputerUseActionGate: 创建隔离的 durable lock 管理器；如果没有这行代码，控制器无法判断当前会话是否持锁。
        controller = ComputerUseController(backend=backend, lock_manager=lock_manager, owner_session_id=session_id)  # 新增代码+Phase30ComputerUseActionGate: 注入后端、锁和会话身份；如果没有这行代码，测试无法覆盖 Phase 30 会话锁门禁。
        return controller, backend, lock_manager, window  # 新增代码+Phase30ComputerUseActionGate: 返回测试需要的对象；如果没有这行代码，各测试拿不到共享准备结果。
    # 新增代码+Phase30ComputerUseActionGate: 函数段结束，_controller 到此结束；如果没有这个边界注释，读者不容易分清测试准备和断言逻辑。

    def test_action_requires_current_computer_use_lock(self) -> None:  # 新增代码+Phase30ComputerUseActionGate: 函数段开始，验证没有当前锁时动作必须被拒绝；如果没有这个测试，真实桌面可能被两个会话同时控制。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase30ComputerUseActionGate: 创建临时锁目录；如果没有这行代码，测试会使用真实运行目录。
            controller, backend, _lock_manager, window = self._controller(Path(temp_dir))  # 新增代码+Phase30ComputerUseActionGate: 创建未持锁的控制器；如果没有这行代码，无法模拟缺锁场景。
            result = controller.execute({"action": "click", "confirm_desktop_control": True, "window": window, "x": 5, "y": 7})  # 新增代码+Phase30ComputerUseActionGate: 发起已确认但未持锁的点击；如果没有这行代码，门禁不会被触发。

            self.assertFalse(result.ok)  # 新增代码+Phase30ComputerUseActionGate: 断言缺锁动作失败；如果没有这行代码，测试无法证明门禁生效。
            self.assertIn("lock", result.message.lower())  # 新增代码+Phase30ComputerUseActionGate: 断言失败原因提到 lock；如果没有这行代码，用户可能看不懂为什么被拒绝。
            self.assertEqual(backend.actions, [])  # 新增代码+Phase30ComputerUseActionGate: 断言后端没有收到动作；如果没有这行代码，控制器可能表面拒绝但实际执行。
    # 新增代码+Phase30ComputerUseActionGate: 函数段结束，test_action_requires_current_computer_use_lock 到此结束；如果没有这个边界注释，初学者不容易定位测试范围。

    def test_abort_flag_blocks_next_action_before_backend(self) -> None:  # 新增代码+Phase30ComputerUseActionGate: 函数段开始，验证 abort flag 会阻止下一次动作；如果没有这个测试，紧急停止按钮可能只是摆设。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase30ComputerUseActionGate: 创建临时锁目录；如果没有这行代码，abort 文件会污染真实运行目录。
            controller, backend, lock_manager, window = self._controller(Path(temp_dir))  # 新增代码+Phase30ComputerUseActionGate: 创建控制器、后端和锁管理器；如果没有这行代码，无法模拟持锁后中止。
            lock_manager.acquire("phase30-session", owner_label="unit-test")  # 新增代码+Phase30ComputerUseActionGate: 让当前会话先持有桌面控制锁；如果没有这行代码，失败原因会变成缺锁而不是 abort。
            lock_manager.request_abort("unit test abort")  # 新增代码+Phase30ComputerUseActionGate: 写入中止标记；如果没有这行代码，控制器没有中止状态可检查。
            result = controller.execute({"action": "click", "confirm_desktop_control": True, "window": window, "x": 5, "y": 7})  # 新增代码+Phase30ComputerUseActionGate: 发起本应被 abort 拦截的点击；如果没有这行代码，abort 逻辑不会被验证。

            self.assertFalse(result.ok)  # 新增代码+Phase30ComputerUseActionGate: 断言 abort 后动作失败；如果没有这行代码，测试无法证明急停生效。
            self.assertIn("abort", result.message.lower())  # 新增代码+Phase30ComputerUseActionGate: 断言失败原因包含 abort；如果没有这行代码，用户无法从结果中知道是急停拦截。
            self.assertEqual(backend.actions, [])  # 新增代码+Phase30ComputerUseActionGate: 断言后端未收到动作；如果没有这行代码，abort 可能仍然放过真实鼠标键盘。
    # 新增代码+Phase30ComputerUseActionGate: 函数段结束，test_abort_flag_blocks_next_action_before_backend 到此结束；如果没有这个边界注释，读者不容易分清 abort 测试范围。

    def test_window_relative_coordinates_are_converted_before_backend_execute(self) -> None:  # 新增代码+Phase30ComputerUseActionGate: 函数段开始，验证窗口相对坐标会先转换成屏幕坐标；如果没有这个测试，点击可能落在错误屏幕位置。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase30ComputerUseActionGate: 创建临时锁目录；如果没有这行代码，锁状态会污染其他测试。
            controller, backend, lock_manager, window = self._controller(Path(temp_dir))  # 新增代码+Phase30ComputerUseActionGate: 创建控制器和后端；如果没有这行代码，无法观察传给后端的坐标。
            lock_manager.acquire("phase30-session", owner_label="unit-test")  # 新增代码+Phase30ComputerUseActionGate: 获取当前会话锁；如果没有这行代码，动作会在坐标转换前被拒绝。
            result = controller.execute({"action": "click", "confirm_desktop_control": True, "window": window, "x": 5, "y": 7})  # 新增代码+Phase30ComputerUseActionGate: 用窗口相对坐标请求点击；如果没有这行代码，转换逻辑不会被触发。

            self.assertTrue(result.ok)  # 新增代码+Phase30ComputerUseActionGate: 断言动作通过安全门禁；如果没有这行代码，后续坐标断言可能在失败结果上误读。
            self.assertEqual(backend.actions[0]["x"], 15)  # 新增代码+Phase30ComputerUseActionGate: 断言 x 从窗口 10+5 转成屏幕 15；如果没有这行代码，窗口相对坐标可能未转换。
            self.assertEqual(backend.actions[0]["y"], 27)  # 新增代码+Phase30ComputerUseActionGate: 断言 y 从窗口 20+7 转成屏幕 27；如果没有这行代码，点击纵坐标可能错误。
            self.assertEqual(result.data["action_evidence"]["coordinate_used"]["space"], "screen")  # 新增代码+Phase30ComputerUseActionGate: 断言结果证据说明最终使用屏幕坐标；如果没有这行代码，审计无法知道坐标空间。
            self.assertEqual(result.data["action_evidence"]["coordinate_used"]["x"], 15)  # 新增代码+Phase30ComputerUseActionGate: 断言证据里的最终 x 坐标正确；如果没有这行代码，返回结果可能和实际后端动作不一致。
            self.assertEqual(result.data["action_evidence"]["coordinate_used"]["y"], 27)  # 新增代码+Phase30ComputerUseActionGate: 断言证据里的最终 y 坐标正确；如果没有这行代码，返回结果可能遗漏实际位置。
    # 新增代码+Phase30ComputerUseActionGate: 函数段结束，test_window_relative_coordinates_are_converted_before_backend_execute 到此结束；如果没有这个边界注释，读者不容易看出坐标测试范围。

    def test_text_action_logs_never_store_raw_sensitive_text(self) -> None:  # 新增代码+Phase30ComputerUseActionGate: 函数段开始，验证文本动作日志不保存原始敏感文本；如果没有这个测试，密码或 token 可能进入审计文件。
        secret_text = "my-secret-password-123"  # 新增代码+Phase30ComputerUseActionGate: 准备敏感文本样本；如果没有这行代码，脱敏测试没有明确泄露目标。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase30ComputerUseActionGate: 创建临时锁目录；如果没有这行代码，锁状态会污染真实运行目录。
            controller, backend, lock_manager, window = self._controller(Path(temp_dir))  # 新增代码+Phase30ComputerUseActionGate: 创建控制器和内存后端；如果没有这行代码，无法检查审计和测试后端日志。
            lock_manager.acquire("phase30-session", owner_label="unit-test")  # 新增代码+Phase30ComputerUseActionGate: 获取当前会话锁；如果没有这行代码，type_text 会被缺锁门禁提前拒绝。
            result = controller.execute({"action": "type_text", "confirm_desktop_control": True, "window": window, "text": secret_text})  # 新增代码+Phase30ComputerUseActionGate: 执行文本动作；如果没有这行代码，日志脱敏不会被触发。
            serialized_logs = json.dumps({"result": result.data, "audit": controller.audit_log, "backend": backend.actions}, ensure_ascii=False)  # 新增代码+Phase30ComputerUseActionGate: 把所有可见日志序列化用于泄露检查；如果没有这行代码，检查范围会遗漏某一处。

            self.assertTrue(result.ok)  # 新增代码+Phase30ComputerUseActionGate: 断言文本动作本身成功；如果没有这行代码，脱敏测试可能只验证失败路径。
            self.assertNotIn(secret_text, serialized_logs)  # 新增代码+Phase30ComputerUseActionGate: 断言原始敏感文本没有出现在日志和结果里；如果没有这行代码，脱敏要求可能被破坏。
            self.assertEqual(result.data["action_evidence"]["text_length"], len(secret_text))  # 新增代码+Phase30ComputerUseActionGate: 断言证据只保留长度；如果没有这行代码，模型无法审计发生过文本输入。
            self.assertIn("text_sha256_16", result.data["action_evidence"])  # 新增代码+Phase30ComputerUseActionGate: 断言证据保留短哈希便于追踪同一文本；如果没有这行代码，审计无法在不泄露内容的前提下关联动作。
    # 新增代码+Phase30ComputerUseActionGate: 函数段结束，test_text_action_logs_never_store_raw_sensitive_text 到此结束；如果没有这个边界注释，读者不容易分清脱敏测试范围。

    def test_action_result_contains_action_evidence_envelope(self) -> None:  # 新增代码+Phase30ComputerUseActionGate: 函数段开始，验证动作结果携带 action evidence envelope；如果没有这个测试，后续审计链无法把结果、锁和窗口关联起来。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase30ComputerUseActionGate: 创建临时锁目录；如果没有这行代码，动作证据测试会污染真实锁状态。
            controller, _backend, lock_manager, window = self._controller(Path(temp_dir))  # 新增代码+Phase30ComputerUseActionGate: 创建控制器和锁管理器；如果没有这行代码，无法生成持锁动作结果。
            lock_manager.acquire("phase30-session", owner_label="unit-test")  # 新增代码+Phase30ComputerUseActionGate: 获取当前会话锁；如果没有这行代码，动作会被拒绝而无法产生成功证据。
            result = controller.execute({"action": "click", "confirm_desktop_control": True, "window": window, "x": 5, "y": 7})  # 新增代码+Phase30ComputerUseActionGate: 执行一次可审计点击；如果没有这行代码，证据 envelope 不会生成。
            evidence = result.data["action_evidence"]  # 新增代码+Phase30ComputerUseActionGate: 取出动作证据 envelope；如果没有这行代码，后续断言会重复索引不易读。

            self.assertTrue(result.ok)  # 新增代码+Phase30ComputerUseActionGate: 断言动作成功；如果没有这行代码，证据检查可能在失败路径上误判。
            self.assertEqual(evidence["audit_id"], result.data["audit_id"])  # 新增代码+Phase30ComputerUseActionGate: 断言 evidence 和结果审计 id 一致；如果没有这行代码，证据链会断开。
            self.assertEqual(evidence["lock_session_id"], "phase30-session")  # 新增代码+Phase30ComputerUseActionGate: 断言证据记录持锁会话；如果没有这行代码，事后无法知道谁控制了桌面。
            self.assertEqual(evidence["target_window"]["window_id"], "hwnd:3001")  # 新增代码+Phase30ComputerUseActionGate: 断言证据记录目标窗口；如果没有这行代码，动作无法回溯到具体窗口。
            self.assertEqual(evidence["policy_version"], "phase30_window_relative_action_gate_v1")  # 新增代码+Phase30ComputerUseActionGate: 断言证据记录策略版本；如果没有这行代码，未来策略变化时无法区分旧证据。
    # 新增代码+Phase30ComputerUseActionGate: 函数段结束，test_action_result_contains_action_evidence_envelope 到此结束；如果没有这个边界注释，读者不容易看出 evidence 测试范围。


if __name__ == "__main__":  # 新增代码+Phase30ComputerUseActionGate: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase30ComputerUseActionGate: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行任何测试。
