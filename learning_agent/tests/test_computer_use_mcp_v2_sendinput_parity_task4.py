import ctypes  # 新增代码+ClaudeCodeParity: 导入 ctypes 用来给中键 SendInput 测试挂 fake windll；如果没有这行代码，测试无法在不碰真实桌面的情况下读取鼠标 flag。
import unittest  # 新增代码+ClaudeCodeParity: 导入 unittest 组织 Task4 回归测试；如果没有这行代码，新增测试不会被标准测试命令发现。
from typing import Any  # 新增代码+ClaudeCodeParity: 导入 Any 标注 fake 记录里的动态事件；如果没有这行代码，测试辅助类的输入边界不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.approval import WindowsComputerUseApprovalModel  # 新增代码+ClaudeCodeParity: 导入 v2 审批模型验证 hold_key 授权门；如果没有这行代码，测试可能误测旧 learning_agent.computer_use 包。
from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+ClaudeCodeParity: 导入真实低层 sender 的按钮方法；如果没有这行代码，中键 flag 回归无法覆盖最后一跳。
from learning_agent.computer_use_mcp_v2.windows_runtime.security_policy import WindowsComputerUseSecurityPolicy  # 新增代码+ClaudeCodeParity: 导入 v2 安全策略验证 hold_key 风险识别；如果没有这行代码，系统组合键策略缺口会漏过。
from learning_agent.computer_use_mcp_v2.windows_runtime.sendinput_dispatcher import Phase47RecordingLowLevelSender, WindowsSendInputDispatcher  # 新增代码+ClaudeCodeParity: 导入 v2 dispatcher 和记录型 sender；如果没有这行代码，新动作展开测试无法覆盖主链路。
from learning_agent.computer_use_mcp_v2.windows_runtime.sendinput_executor import PHASE37_HOLD_KEY_MAX_DURATION_SECONDS, WindowsSendInputExecutor  # 修改代码+ClaudeCodeParity: 同时导入 hold_key 时长上限和 executor；如果没有这行代码，测试无法锁定报告上限与真实暂停上限一致。


class Task4RecordingSendInputImplementation:  # 新增代码+ClaudeCodeParity: 类段开始，定义记录型 SendInput 实现；如果没有这个类，executor 测试只能碰真实 dispatcher 或真实桌面。
    def __init__(self) -> None:  # 新增代码+ClaudeCodeParity: 函数段开始，初始化规范事件记录；如果没有这段函数，fake 实现无法保存 executor 发来的事件。
        self.calls: list[dict[str, Any]] = []  # 新增代码+ClaudeCodeParity: 保存 executor 传入的规范事件副本；如果没有这行代码，测试无法断言 action 被转成什么事件。
    # 新增代码+ClaudeCodeParity: 函数段结束，Task4RecordingSendInputImplementation.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def send(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity: 函数段开始，模拟 dispatcher 的 send 接口；如果没有这段函数，executor 找不到可调用的底层实现。
        self.calls.extend(dict(event) for event in events)  # 新增代码+ClaudeCodeParity: 复制事件到记录列表；如果没有这行代码，后续断言可能被调用方原地修改污染。
        return {"ok": True, "event_count": len(events), "backend": "task4_recording"}  # 新增代码+ClaudeCodeParity: 返回成功摘要；如果没有这行代码，executor 无法形成成功结果。
    # 新增代码+ClaudeCodeParity: 函数段结束，Task4RecordingSendInputImplementation.send 到此结束；如果没有这个边界说明，初学者不容易看出 fake 发送范围。


class Task4FakeUser32:  # 新增代码+ClaudeCodeParity: 类段开始，定义 fake user32 用来截获 SendInput flag；如果没有这个类，中键测试会依赖真实 Windows API。
    def __init__(self) -> None:  # 新增代码+ClaudeCodeParity: 函数段开始，初始化 flag 记录；如果没有这段函数，fake user32 无法保存 SendInput 参数。
        self.flags: list[int] = []  # 新增代码+ClaudeCodeParity: 保存每次 SendInput 的 dwFlags；如果没有这行代码，测试无法证明中键没有被当成右键。
    # 新增代码+ClaudeCodeParity: 函数段结束，Task4FakeUser32.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出 fake 初始化范围。

    def SendInput(self, count: int, input_ref: Any, input_size: int) -> int:  # 新增代码+ClaudeCodeParity: 函数段开始，模拟 user32.SendInput；如果没有这段函数，低层 sender 调用会落到真实系统。
        _ = count  # 新增代码+ClaudeCodeParity: 接收但不使用事件数量参数；如果没有这行代码，读者会疑惑为什么签名和 Win32 一样却没用到。
        _ = input_size  # 新增代码+ClaudeCodeParity: 接收但不使用结构大小参数；如果没有这行代码，fake 签名不够贴近真实 API。
        self.flags.append(int(input_ref._obj.union.mi.dwFlags))  # 新增代码+ClaudeCodeParity: 从 ctypes byref 对象里读取鼠标 flag；如果没有这行代码，测试无法判断发送的是中键还是右键。
        return 1  # 新增代码+ClaudeCodeParity: 模拟成功发送一个 INPUT；如果没有这行代码，sender 会把 fake 调用当失败。
    # 新增代码+ClaudeCodeParity: 函数段结束，Task4FakeUser32.SendInput 到此结束；如果没有这个边界说明，初学者不容易看出 fake API 范围。


class Task4FakeWindll:  # 新增代码+ClaudeCodeParity: 类段开始，提供 ctypes.windll 需要的 user32 属性；如果没有这个类，测试无法替换真实 windll。
    def __init__(self, user32: Task4FakeUser32) -> None:  # 新增代码+ClaudeCodeParity: 函数段开始，绑定 fake user32；如果没有这段函数，windll 没有可用的 user32 入口。
        self.user32 = user32  # 新增代码+ClaudeCodeParity: 保存 fake user32 对象；如果没有这行代码，sender 调用 ctypes.windll.user32 会失败。
    # 新增代码+ClaudeCodeParity: 函数段结束，Task4FakeWindll.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出 windll 替身范围。


class Task4FailingKeySender(WindowsSendInputLowLevelSender):  # 新增代码+ClaudeCodeParity: 类段开始，模拟第二个 key_down 抛异常的 low-level sender；如果没有这个 fake，卡键 cleanup 测试可能误触真实桌面。
    def __init__(self) -> None:  # 新增代码+ClaudeCodeParity: 函数段开始，初始化发送记录；如果没有这段函数，测试无法知道 cleanup 是否补发 key_up。
        super().__init__(platform="win32")  # 新增代码+ClaudeCodeParity: 复用真实 sender 的事件循环但不调用系统 API；如果没有这行代码，测试对象不会拥有 send_low_level 行为。
        self.virtual_key_calls: list[dict[str, Any]] = []  # 新增代码+ClaudeCodeParity: 记录每一次虚拟键发送；如果没有这行代码，测试无法证明释放动作被尝试。
    # 新增代码+ClaudeCodeParity: 函数段结束，Task4FailingKeySender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出 fake 状态初始化范围。

    def _send_virtual_key(self, key: str, down: bool) -> bool:  # 新增代码+ClaudeCodeParity: 函数段开始，拦截真实按键发送；如果没有这段函数，测试会调用 Windows SendInput。
        self.virtual_key_calls.append({"key": key, "down": down})  # 新增代码+ClaudeCodeParity: 保存按键和方向；如果没有这行代码，cleanup 释放顺序无法断言。
        if key == "s" and down:  # 新增代码+ClaudeCodeParity: 在第二个按键按下时制造失败；如果没有这行代码，红灯测试无法复现按下后异常的卡键风险。
            raise RuntimeError("task4 simulated key_down failure")  # 新增代码+ClaudeCodeParity: 抛出受控异常；如果没有这行代码，low-level sender 的异常 cleanup 分支不会被覆盖。
        return True  # 新增代码+ClaudeCodeParity: 其他虚拟键调用都模拟成功；如果没有这行代码，测试无法区分业务异常和 fake 失败。
    # 新增代码+ClaudeCodeParity: 函数段结束，Task4FailingKeySender._send_virtual_key 到此结束；如果没有这个边界说明，初学者不容易看出 fake 发送范围。
# 新增代码+ClaudeCodeParity: 类段结束，Task4FailingKeySender 到此结束；如果没有这个边界说明，初学者不容易看出异常 cleanup fake 的完整范围。


class ComputerUseMcpV2SendInputParityTask4Tests(unittest.TestCase):  # 新增代码+ClaudeCodeParity: 类段开始，集中覆盖 Task4 的 v2 SendInput parity；如果没有这个类，新增测试不会被 unittest 组织。
    def _safe_window(self) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity: 函数段开始，提供安全窗口样本；如果没有这段函数，approval/security 测试要重复拼窗口字段。
        return {"app_id": "notepad.exe", "window_id": "hwnd:4404", "process_name": "notepad.exe", "title_preview": "Task4 Notepad"}  # 新增代码+ClaudeCodeParity: 返回普通 Notepad 风格窗口；如果没有这行代码，审批模型会因为缺少窗口目标提前拒绝。
    # 新增代码+ClaudeCodeParity: 函数段结束，_safe_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口样本范围。

    def test_v2_executor_supports_and_emits_parity_actions(self) -> None:  # 新增代码+ClaudeCodeParity: 函数段开始，验证 executor 支持并生成新动作规范事件；如果没有这个测试，新 MCP tool 到低层会继续被拒绝。
        recorder = Task4RecordingSendInputImplementation()  # 新增代码+ClaudeCodeParity: 创建记录型实现；如果没有这行代码，测试无法安全检查 executor 输出。
        executor = WindowsSendInputExecutor(platform="win32", enabled=True, sendinput_impl=recorder)  # 新增代码+ClaudeCodeParity: 创建启用但注入 fake 的 v2 executor；如果没有这行代码，动作会因真实输入关闭而拒绝。
        supported = set(executor.status()["actions_supported"])  # 新增代码+ClaudeCodeParity: 读取支持动作集合；如果没有这行代码，测试无法证明状态面暴露新能力。
        for action in {"triple_click", "mouse_down", "mouse_up", "hold_key"}:  # 新增代码+ClaudeCodeParity: 遍历 Task4 新动作；如果没有这行代码，可能只检查其中一个动作导致漏项。
            self.assertIn(action, supported)  # 新增代码+ClaudeCodeParity: 断言状态包含新动作；如果没有这行代码，controller 状态仍会误导上游。
        self.assertTrue(executor.execute("triple_click", {"x": 10, "y": 20, "button": "left"}).ok)  # 新增代码+ClaudeCodeParity: 执行三击动作；如果没有这行代码，triple_click 规范事件缺口不会暴露。
        self.assertTrue(executor.execute("mouse_down", {"x": 11, "y": 21}).ok)  # 新增代码+ClaudeCodeParity: 执行鼠标按下动作；如果没有这行代码，拖拽起手动作缺口不会暴露。
        self.assertTrue(executor.execute("mouse_up", {"x": 12, "y": 22}).ok)  # 新增代码+ClaudeCodeParity: 执行鼠标抬起动作；如果没有这行代码，拖拽收尾动作缺口不会暴露。
        self.assertTrue(executor.execute("hold_key", {"keys": ["ctrl", "s"], "duration_seconds": 0.25}).ok)  # 新增代码+ClaudeCodeParity: 执行组合键按住动作；如果没有这行代码，hold_key keys 数组路径不会被测试。
        self.assertEqual([event["type"] for event in recorder.calls], ["triple_click", "mouse_down", "mouse_up", "hold_key"])  # 新增代码+ClaudeCodeParity: 断言规范事件类型顺序；如果没有这行代码，executor 可能用旧 key/hotkey 语义掩盖问题。
        self.assertEqual(recorder.calls[-1]["keys"], ["ctrl", "s"])  # 新增代码+ClaudeCodeParity: 断言 hold_key 保留 keys 数组；如果没有这行代码，安全策略和 dispatcher 无法看到完整组合键。
        self.assertEqual(recorder.calls[-1]["duration_seconds"], 0.25)  # 新增代码+ClaudeCodeParity: 断言 hold_key 保留受限时长；如果没有这行代码，按住时间可能丢失或失控。
        self.assertFalse(executor.execute("hold_key", {"keys": []}).ok)  # 新增代码+ClaudeCodeParity: 断言空 keys 被拒绝；如果没有这行代码，底层可能收到无意义按住动作。
        self.assertEqual(PHASE37_HOLD_KEY_MAX_DURATION_SECONDS, 2.0)  # 修改代码+ClaudeCodeParity: 断言 executor 对外报告的 hold_key 上限是 2 秒；如果没有这行代码，30 秒报告和真实 pause 2 秒夹紧会再次不一致。
        self.assertFalse(executor.execute("hold_key", {"keys": ["a"], "duration_seconds": 2.5}).ok)  # 修改代码+ClaudeCodeParity: 断言超过 2 秒就拒绝；如果没有这行代码，真实桌面可能被长时间占用而报告不准确。
    # 新增代码+ClaudeCodeParity: 函数段结束，test_v2_executor_supports_and_emits_parity_actions 到此结束；如果没有这个边界说明，初学者不容易看出 executor parity 范围。

    def test_v2_dispatcher_expands_parity_actions_with_target(self) -> None:  # 新增代码+ClaudeCodeParity: 函数段开始，验证 dispatcher 展开新规范事件并保留 target；如果没有这个测试，事件到最后一跳可能丢窗口身份。
        sender = Phase47RecordingLowLevelSender()  # 新增代码+ClaudeCodeParity: 创建记录型低层 sender；如果没有这行代码，测试无法查看展开后的低层事件。
        dispatcher = WindowsSendInputDispatcher(platform="win32", enabled=True, low_level_sender=sender, target_verifier=lambda: {"ok": True, "reason": "stable"})  # 新增代码+ClaudeCodeParity: 创建启用 dispatcher；如果没有这行代码，send 会因没有 sender 或目标校验失败而拒绝。
        target = {"window_id": "hwnd:4404", "hwnd": 4404}  # 新增代码+ClaudeCodeParity: 准备目标身份；如果没有这行代码，测试无法证明 target 被传到低层事件。
        result = dispatcher.send([{"type": "triple_click", "x": 10, "y": 20, "button": "left", "target": target}, {"type": "mouse_down", "x": 11, "y": 21, "button": "left", "target": target}, {"type": "mouse_up", "x": 12, "y": 22, "button": "left", "target": target}, {"type": "hold_key", "keys": ["ctrl", "s"], "duration_seconds": 0.5, "target": target}])  # 新增代码+ClaudeCodeParity: 发送四种新规范事件；如果没有这行代码，dispatcher 新分支不会被覆盖。
        event_types = [event["type"] for event in sender.low_level_events]  # 新增代码+ClaudeCodeParity: 收集低层事件类型顺序；如果没有这行代码，测试无法确认展开结构。
        parity_event_types = event_types[2:] if event_types[:2] == ["set_foreground", "pause"] else event_types  # 修改代码+ClaudeCodeParity: 跳过已有窗口聚焦预备事件后检查新动作主体；如果没有这行代码，测试会把安全聚焦链路误判成三击展开失败。
        self.assertTrue(result["ok"])  # 新增代码+ClaudeCodeParity: 断言 dispatcher 成功发送；如果没有这行代码，低层事件断言可能来自失败残留。
        self.assertEqual(parity_event_types[:7], ["mouse_move", "mouse_down", "mouse_up", "mouse_down", "mouse_up", "mouse_down", "mouse_up"])  # 修改代码+ClaudeCodeParity: 断言三击主体展开为移动加三次按下抬起；如果没有这行代码，triple_click 可能只执行单击。
        self.assertIn("pause", parity_event_types)  # 修改代码+ClaudeCodeParity: 断言 hold_key 主体包含按住暂停；如果没有这行代码，duration_seconds 会被 dispatcher 忽略。
        self.assertEqual(parity_event_types[-5:], ["key_down", "key_down", "pause", "key_up", "key_up"])  # 修改代码+ClaudeCodeParity: 断言 hold_key 按顺序按下、逆序抬起；如果没有这行代码，组合键语义会错误。
        self.assertTrue(all(event.get("target", {}).get("window_id") == "hwnd:4404" for event in sender.low_level_events))  # 新增代码+ClaudeCodeParity: 断言所有低层事件保留 target；如果没有这行代码，target verifier 之后最后一跳审计会断链。
    # 新增代码+ClaudeCodeParity: 函数段结束，test_v2_dispatcher_expands_parity_actions_with_target 到此结束；如果没有这个边界说明，初学者不容易看出 dispatcher parity 范围。

    def test_low_level_sender_uses_middle_mouse_flags(self) -> None:  # 新增代码+ClaudeCodeParity: 函数段开始，验证中键不会误走右键 flag；如果没有这个测试，middle_click 会在真实桌面变成右键。
        fake_user32 = Task4FakeUser32()  # 新增代码+ClaudeCodeParity: 创建 fake user32 记录 flag；如果没有这行代码，测试无法观察 SendInput 参数。
        original_windll = getattr(ctypes, "windll", None)  # 新增代码+ClaudeCodeParity: 保存原 windll 以便恢复；如果没有这行代码，测试可能污染其他 ctypes 用例。
        ctypes.windll = Task4FakeWindll(fake_user32)  # type: ignore[attr-defined]  # 新增代码+ClaudeCodeParity: 临时替换 ctypes.windll；如果没有这行代码，sender 会尝试调用真实 Windows API。
        try:  # 新增代码+ClaudeCodeParity: 函数段开始，确保 fake windll 用后恢复；如果没有这段代码，异常时可能留下全局 monkeypatch。
            sender = WindowsSendInputLowLevelSender(platform="win32")  # 新增代码+ClaudeCodeParity: 创建低层 sender；如果没有这行代码，被测方法没有实例。
            self.assertTrue(sender._send_mouse_button("middle", down=True))  # 新增代码+ClaudeCodeParity: 发送中键按下；如果没有这行代码，中键 down flag 不会被验证。
            self.assertTrue(sender._send_mouse_button("middle", down=False))  # 新增代码+ClaudeCodeParity: 发送中键抬起；如果没有这行代码，中键 up flag 不会被验证。
        finally:  # 新增代码+ClaudeCodeParity: 函数段结束前恢复 ctypes.windll；如果没有这行代码，后续测试可能继续使用 fake windll。
            if original_windll is None:  # 新增代码+ClaudeCodeParity: 判断原本是否没有 windll；如果没有这行代码，非 Windows Python 上恢复逻辑会不准确。
                delattr(ctypes, "windll")  # 新增代码+ClaudeCodeParity: 删除测试临时添加的 windll；如果没有这行代码，fake 会泄漏到进程全局。
            else:  # 新增代码+ClaudeCodeParity: 处理原本存在 windll 的 Windows 环境；如果没有这行代码，Windows 上无法恢复真实对象。
                ctypes.windll = original_windll  # type: ignore[attr-defined]  # 新增代码+ClaudeCodeParity: 恢复原 ctypes.windll；如果没有这行代码，其他测试会被 fake 影响。
        self.assertEqual(fake_user32.flags, [0x0020, 0x0040])  # 新增代码+ClaudeCodeParity: 断言使用 MIDDLEDOWN/MIDDLEUP；如果没有这行代码，右键 flag 回归不会被抓住。
    # 新增代码+ClaudeCodeParity: 函数段结束，test_low_level_sender_uses_middle_mouse_flags 到此结束；如果没有这个边界说明，初学者不容易看出中键 flag 测试范围。

    def test_low_level_sender_cleans_pressed_keys_after_exception(self) -> None:  # 新增代码+ClaudeCodeParity: 函数段开始，验证 hold_key 低层异常时会尝试释放已按下按键；如果没有这个测试，卡键风险可能复发。
        sender = Task4FailingKeySender()  # 新增代码+ClaudeCodeParity: 创建不会触碰真实桌面的失败 sender；如果没有这行代码，测试无法安全复现异常。
        result = sender.send_low_level([{"type": "key_down", "key": "ctrl"}, {"type": "key_down", "key": "s"}, {"type": "pause", "seconds": 0.1}, {"type": "key_up", "key": "s"}, {"type": "key_up", "key": "ctrl"}])  # 新增代码+ClaudeCodeParity: 构造 hold_key 展开后的低层序列；如果没有这行代码，cleanup 分支没有输入事件。
        self.assertFalse(result["ok"], result)  # 新增代码+ClaudeCodeParity: 断言异常路径返回失败而不是抛出到调用方；如果没有这行代码，batch/controller 仍可能误判成功。
        self.assertTrue(result["keyboard_cleanup_attempted"], result)  # 新增代码+ClaudeCodeParity: 断言异常后尝试键盘 cleanup；如果没有这行代码，已按下键可能留在真实系统里。
        self.assertEqual(result["keyboard_cleanup_released_count"], 1)  # 新增代码+ClaudeCodeParity: 断言只释放已经成功按下的 ctrl；如果没有这行代码，cleanup 计数无法证明状态管理正确。
        self.assertEqual(sender.virtual_key_calls, [{"key": "ctrl", "down": True}, {"key": "s", "down": True}, {"key": "ctrl", "down": False}])  # 新增代码+ClaudeCodeParity: 断言 cleanup 逆序补发 key_up 且不碰未成功按下的 s；如果没有这行代码，释放顺序错误不会被发现。
    # 新增代码+ClaudeCodeParity: 函数段结束，test_low_level_sender_cleans_pressed_keys_after_exception 到此结束；如果没有这个边界说明，初学者不容易看出异常 cleanup 测试范围。

    def test_hold_key_keys_array_requires_system_combo_grant(self) -> None:  # 新增代码+ClaudeCodeParity: 函数段开始，验证 hold_key keys 数组进入审批和策略风险识别；如果没有这个测试，危险组合键会绕过 press_key 检查。
        safe_window = self._safe_window()  # 新增代码+ClaudeCodeParity: 获取安全窗口样本；如果没有这行代码，审批模型会因缺窗口而不是因权限拒绝。
        policy = WindowsComputerUseSecurityPolicy()  # 新增代码+ClaudeCodeParity: 创建 v2 安全策略；如果没有这行代码，策略层 hold_key 缺口无法测试。
        denied_policy = policy.evaluate("hold_key", {"window": safe_window, "keys": ["win", "r"]}, grant_flags={"desktopAction": True}, app_granted=True)  # 新增代码+ClaudeCodeParity: 用 Win+R 检查策略默认拒绝；如果没有这行代码，系统组合键风险不会进入策略测试。
        denied_alt_f4_policy = policy.evaluate("hold_key", {"window": safe_window, "keys": ["alt", "f4"]}, grant_flags={"desktopAction": True}, app_granted=True)  # 新增代码+ClaudeCodeParity: 用 Alt+F4 检查策略拒绝关闭窗口快捷键；如果没有这行代码，系统级关闭动作可能不需要 systemKeyCombos 授权。
        denied_meta_policy = policy.evaluate("hold_key", {"window": safe_window, "keys": ["meta", "r"]}, grant_flags={"desktopAction": True}, app_granted=True)  # 新增代码+ClaudeCodeParity: 用 meta+r 检查 win 别名风险；如果没有这行代码，跨平台别名可能绕过 Windows 系统键门禁。
        denied_super_policy = policy.evaluate("hold_key", {"window": safe_window, "keys": ["super", "r"]}, grant_flags={"desktopAction": True}, app_granted=True)  # 新增代码+ClaudeCodeParity: 用 super+r 检查 win 别名风险；如果没有这行代码，Linux 风格别名可能被误当普通组合键。
        denied_cmd_policy = policy.evaluate("hold_key", {"window": safe_window, "keys": ["cmd", "space"]}, grant_flags={"desktopAction": True}, app_granted=True)  # 新增代码+ClaudeCodeParity: 用 cmd+space 检查系统级启动器别名风险；如果没有这行代码，mac 风格别名可能绕过系统组合键授权。
        allowed_policy = policy.evaluate("hold_key", {"window": safe_window, "keys": ["ctrl", "s"]}, grant_flags={"desktopAction": True}, app_granted=True)  # 新增代码+ClaudeCodeParity: 用 Ctrl+S 检查普通组合键允许；如果没有这行代码，策略可能误伤常见应用快捷键。
        model = WindowsComputerUseApprovalModel(security_policy=policy)  # 新增代码+ClaudeCodeParity: 创建接入策略的审批模型；如果没有这行代码，controller 实际审批链不被覆盖。
        model.grant_for_session([safe_window], {"desktopAction": True, "systemKeyCombos": False}, reason="task4-hold-key")  # 新增代码+ClaudeCodeParity: 授权普通动作但关闭系统键；如果没有这行代码，审批测试没有明确 flag 边界。
        denied_model = model.evaluate("hold_key", {"window": safe_window, "keys": ["ctrl", "alt", "delete"]})  # 新增代码+ClaudeCodeParity: 用 Ctrl+Alt+Delete 检查审批拒绝；如果没有这行代码，hold_key 危险数组可能被 allowlist 放行。
        denied_alias_model = model.evaluate("hold_key", {"window": safe_window, "keys": ["cmd", "space"]})  # 新增代码+ClaudeCodeParity: 用 cmd+space 检查审批链也识别系统键别名；如果没有这行代码，策略层修复可能没有进入实际 approval。
        allowed_model = model.evaluate("hold_key", {"window": safe_window, "keys": ["ctrl", "s"]})  # 新增代码+ClaudeCodeParity: 用 Ctrl+S 检查审批允许；如果没有这行代码，普通 hold_key 可能被过度拦截。
        self.assertFalse(denied_policy["allowed"])  # 新增代码+ClaudeCodeParity: 断言策略拒绝 Win+R；如果没有这行代码，安全策略缺口不会失败。
        self.assertFalse(denied_alt_f4_policy["allowed"])  # 新增代码+ClaudeCodeParity: 断言策略拒绝 Alt+F4；如果没有这行代码，关闭窗口快捷键漏报不会失败。
        self.assertFalse(denied_meta_policy["allowed"])  # 新增代码+ClaudeCodeParity: 断言策略拒绝 meta+r；如果没有这行代码，meta 别名漏报不会失败。
        self.assertFalse(denied_super_policy["allowed"])  # 新增代码+ClaudeCodeParity: 断言策略拒绝 super+r；如果没有这行代码，super 别名漏报不会失败。
        self.assertFalse(denied_cmd_policy["allowed"])  # 新增代码+ClaudeCodeParity: 断言策略拒绝 cmd+space；如果没有这行代码，cmd 别名漏报不会失败。
        self.assertIn("systemKeyCombos", denied_policy["missing_grant_flags"])  # 新增代码+ClaudeCodeParity: 断言缺失系统键授权；如果没有这行代码，拒绝原因可能不指导用户授权。
        self.assertTrue(allowed_policy["allowed"])  # 新增代码+ClaudeCodeParity: 断言普通 Ctrl+S 通过策略；如果没有这行代码，常见保存快捷键可能被误伤。
        self.assertFalse(denied_model["allowed"])  # 新增代码+ClaudeCodeParity: 断言审批链拒绝 Ctrl+Alt+Delete；如果没有这行代码，实际 controller 风险仍会存在。
        self.assertFalse(denied_alias_model["allowed"])  # 新增代码+ClaudeCodeParity: 断言审批链拒绝 cmd+space；如果没有这行代码，approval 别名缺口不会暴露。
        self.assertIn("systemKeyCombos", denied_model["missing_grant_flags"])  # 新增代码+ClaudeCodeParity: 断言审批链报告缺少系统键授权；如果没有这行代码，用户不知道为什么 hold_key 被拒。
        self.assertIn("systemKeyCombos", denied_alias_model["missing_grant_flags"])  # 新增代码+ClaudeCodeParity: 断言别名拒绝原因仍指向 systemKeyCombos；如果没有这行代码，用户无法知道需要哪类授权。
        self.assertTrue(allowed_model["allowed"])  # 新增代码+ClaudeCodeParity: 断言审批链允许普通 Ctrl+S；如果没有这行代码，Task4 安全修复可能降低普通快捷键能力。
    # 新增代码+ClaudeCodeParity: 函数段结束，test_hold_key_keys_array_requires_system_combo_grant 到此结束；如果没有这个边界说明，初学者不容易看出 hold_key 安全测试范围。
# 新增代码+ClaudeCodeParity: 类段结束，ComputerUseMcpV2SendInputParityTask4Tests 到此结束；如果没有这个边界说明，初学者不容易看出 Task4 测试集合范围。


if __name__ == "__main__":  # 新增代码+ClaudeCodeParity: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+ClaudeCodeParity: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行任何测试。
