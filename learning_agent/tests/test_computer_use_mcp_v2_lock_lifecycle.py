from __future__ import annotations  # 新增代码+ClaudeCodeLockParityTests：延迟类型注解解析；如果没有这行代码，测试导入时类型注解可能提前求值。
import tempfile  # 新增代码+ClaudeCodeLockParityTests：创建隔离锁目录；如果没有这行代码，runtime 回调测试会污染真实锁状态。
import unittest  # 新增代码+ClaudeCodeLockParityTests：使用标准 unittest 框架；如果没有这行代码，测试类不会被发现和执行。
from pathlib import Path  # 新增代码+ClaudeCodeLockParityTests：把临时目录转成 Path；如果没有这行代码，Windows lock manager 路径处理不稳定。
from typing import Any  # 新增代码+ClaudeCodeLockParityTests：用于 fake 回调的通用类型标注；如果没有这行代码，测试回调接口边界不清楚。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import ComputerUseMcpV2Context, cleanup_computer_use_mcp_v2_turn, dispatch_computer_use_mcp_v2_tool  # 新增代码+ClaudeCodeLockParityTests：导入真实 runtime 和 cleanup helper；如果没有这行代码，锁生命周期测试无法覆盖实际分发入口。
from learning_agent.computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager  # 新增代码+ClaudeCodeLockParityTests：导入真实 v2 lock manager；如果没有这行代码，底层 runtime 回调方法没有隔离事实源。
from learning_agent.computer_use_mcp_v2.windows_runtime.session_runtime import WindowsComputerUseSessionRuntime  # 新增代码+ClaudeCodeLockParityTests：导入 Windows session runtime；如果没有这行代码，无法验证底层 ClaudeCode-style lock callback 别名。


class TrackingLockCallbacks:  # 新增代码+ClaudeCodeLockParityTests：类段开始，记录 check/acquire/release/cleanup 调用顺序；如果没有这段类，测试无法证明工具是否真的按 ClaudeCode 语义碰锁。
    def __init__(self, acquire_allowed: bool = True) -> None:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，初始化 fake lock 行为；如果没有这段函数，测试无法模拟取锁成功和失败。
        self.acquire_allowed = bool(acquire_allowed)  # 新增代码+ClaudeCodeLockParityTests：保存取锁是否允许；如果没有这行代码，失败路径无法被控制。
        self.calls: list[tuple[str, str]] = []  # 新增代码+ClaudeCodeLockParityTests：保存所有锁回调调用；如果没有这行代码，测试不能断言调用顺序。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake lock 初始化范围。

    def check(self, tool_name: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，模拟只检查锁；如果没有这段函数，request_access/list_granted 无法证明不取锁。
        self.calls.append(("check", str(tool_name)))  # 新增代码+ClaudeCodeLockParityTests：记录 check 调用；如果没有这行代码，测试无法知道 defers-lock 工具是否只检查。
        return {"ok": True, "lock_backend": "fake", "checked": True}  # 新增代码+ClaudeCodeLockParityTests：返回可用锁状态；如果没有这行代码，runtime 会把检查视为不可用。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，check 到此结束；如果没有这个边界说明，用户不容易看出检查锁范围。

    def acquire(self, tool_name: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，模拟取锁；如果没有这段函数，动作类工具无法证明先取锁再执行。
        self.calls.append(("acquire", str(tool_name)))  # 新增代码+ClaudeCodeLockParityTests：记录 acquire 调用；如果没有这行代码，测试无法知道动作工具是否取锁。
        return {"acquired": self.acquire_allowed, "lock_backend": "fake", "reason": "allowed" if self.acquire_allowed else "busy"}  # 新增代码+ClaudeCodeLockParityTests：返回取锁结果；如果没有这行代码，失败阻断路径没有输入。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，acquire 到此结束；如果没有这个边界说明，用户不容易看出取锁范围。

    def release(self, reason: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，模拟释放锁；如果没有这段函数，cleanup helper 无法证明释放动作发生。
        self.calls.append(("release", str(reason)))  # 新增代码+ClaudeCodeLockParityTests：记录 release 调用；如果没有这行代码，测试无法确认 turn cleanup 释放了锁。
        return {"released": True, "lock_backend": "fake", "reason": str(reason)}  # 新增代码+ClaudeCodeLockParityTests：返回释放成功；如果没有这行代码，cleanup 结果无法表明锁已释放。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，release 到此结束；如果没有这个边界说明，用户不容易看出释放锁范围。

    def cleanup(self, reason: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，模拟 turn-end cleanup；如果没有这段函数，runtime helper 只能直接 release 而不能覆盖完整 cleanup 回调。
        self.calls.append(("cleanup", str(reason)))  # 新增代码+ClaudeCodeLockParityTests：记录 cleanup 调用；如果没有这行代码，测试无法确认使用了 cleanup_after_turn 回调。
        release_result = self.release(reason)  # 新增代码+ClaudeCodeLockParityTests：cleanup 内部释放锁；如果没有这行代码，cleanup 不会满足蓝图的 release lock 要求。
        return {"cleanup_completed": True, "release": release_result, "lock_released": bool(release_result.get("released"))}  # 新增代码+ClaudeCodeLockParityTests：返回 cleanup 摘要；如果没有这行代码，调用方无法判断清理成功。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，cleanup 到此结束；如果没有这个边界说明，用户不容易看出 turn cleanup 范围。

    def held_locally(self, tool_name: str) -> bool:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，模拟本会话是否持锁；如果没有这段函数，debug 无法体现本地持锁状态。
        self.calls.append(("held", str(tool_name)))  # 新增代码+ClaudeCodeLockParityTests：记录 held 查询；如果没有这行代码，测试无法确认 runtime 读取本地锁状态。
        return self.acquire_allowed  # 新增代码+ClaudeCodeLockParityTests：取锁成功时视为本地持锁；如果没有这行代码，debug 里 held 状态会不稳定。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，held_locally 到此结束；如果没有这个边界说明，用户不容易看出本地持锁判断范围。
# 新增代码+ClaudeCodeLockParityTests：类段结束，TrackingLockCallbacks 到此结束；如果没有这个边界说明，用户不容易看出 fake lock 范围。


class FakeHost:  # 新增代码+ClaudeCodeLockParityTests：类段开始，伪造最小 host 动作和观察能力；如果没有这段类，测试会依赖真实 Windows 桌面。
    def __init__(self) -> None:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，初始化 host 调用记录；如果没有这段函数，取锁失败时无法证明 host 没被调用。
        self.calls: list[str] = []  # 新增代码+ClaudeCodeLockParityTests：保存 host 方法调用；如果没有这行代码，测试无法确认是否触碰了桌面执行层。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake host 初始化范围。

    def observe(self, _arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，模拟 observe/screenshot；如果没有这段函数，screenshot 测试无法进入观察成功路径。
        self.calls.append("observe")  # 新增代码+ClaudeCodeLockParityTests：记录 observe 调用；如果没有这行代码，测试无法确认取锁后才观察。
        return {"captured": False, "reason": "fake"}  # 新增代码+ClaudeCodeLockParityTests：返回无图但成功的观察 payload；如果没有这行代码，测试会偏到图片 content 分支。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，observe 到此结束；如果没有这个边界说明，用户不容易看出 fake observe 范围。

    def left_click(self, _arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，模拟 left_click；如果没有这段函数，动作工具会走 host_required 失败而无法测试锁门禁。
        self.calls.append("left_click")  # 新增代码+ClaudeCodeLockParityTests：记录动作调用；如果没有这行代码，取锁失败是否阻断 host 无法验证。
        return {"ok": True, "desktop_action_performed": True}  # 新增代码+ClaudeCodeLockParityTests：返回动作成功；如果没有这行代码，runtime 无法构造成功结果。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，left_click 到此结束；如果没有这个边界说明，用户不容易看出 fake 动作范围。
# 新增代码+ClaudeCodeLockParityTests：类段结束，FakeHost 到此结束；如果没有这个边界说明，用户不容易看出 host 替身范围。


def _context_with_lock(callbacks: TrackingLockCallbacks, host: FakeHost | None = None) -> ComputerUseMcpV2Context:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，创建带锁回调的 context；如果没有这段函数，每个测试都要重复拼上下文。
    return ComputerUseMcpV2Context(host=host, ask_permission=lambda _prompt: True, check_computer_use_lock=callbacks.check, acquire_computer_use_lock=callbacks.acquire, release_computer_use_lock=callbacks.release, cleanup_after_turn=callbacks.cleanup, is_lock_held_locally=callbacks.held_locally)  # 新增代码+ClaudeCodeLockParityTests：返回真实 dataclass context；如果没有这行代码，runtime 锁字段不会被测试覆盖。
# 新增代码+ClaudeCodeLockParityTests：函数段结束，_context_with_lock 到此结束；如果没有这个边界说明，用户不容易看出 context 构造范围。


class ComputerUseMcpV2LockLifecycleTests(unittest.TestCase):  # 新增代码+ClaudeCodeLockParityTests：类段开始，验证 ClaudeCode lock lifecycle 语义；如果没有这段类，动作工具可能绕过独占锁。
    def test_request_access_checks_lock_but_does_not_acquire(self) -> None:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，验证 request_access defers lock；如果没有这段测试，授权工具可能不必要地占用桌面锁。
        callbacks = TrackingLockCallbacks()  # 新增代码+ClaudeCodeLockParityTests：创建 fake lock；如果没有这行代码，测试无法记录锁调用。
        result = dispatch_computer_use_mcp_v2_tool("request_access", {"apps": [{"displayName": "Notepad", "bundleId": "notepad.exe"}], "reason": "测试"}, _context_with_lock(callbacks))  # 新增代码+ClaudeCodeLockParityTests：执行授权申请；如果没有这行代码，defers-lock 路径没有真实输入。
        self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodeLockParityTests：断言授权成功；如果没有这行代码，失败结果可能掩盖锁断言。
        self.assertEqual([("check", "request_access")], callbacks.calls)  # 新增代码+ClaudeCodeLockParityTests：断言只 check 不 acquire；如果没有这行代码，request_access 抢锁不会被发现。
        self.assertEqual("check", result["debug"]["lock_mode"])  # 新增代码+ClaudeCodeLockParityTests：断言结果 debug 标记检查模式；如果没有这行代码，模型和审计看不到锁语义。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，test_request_access_checks_lock_but_does_not_acquire 到此结束；如果没有这个边界说明，用户不容易看出授权锁测试范围。

    def test_list_granted_applications_checks_lock_but_does_not_acquire(self) -> None:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，验证 list_granted defers lock；如果没有这段测试，查询工具可能不必要地占用桌面锁。
        callbacks = TrackingLockCallbacks()  # 新增代码+ClaudeCodeLockParityTests：创建 fake lock；如果没有这行代码，测试无法记录锁调用。
        result = dispatch_computer_use_mcp_v2_tool("list_granted_applications", {}, _context_with_lock(callbacks))  # 新增代码+ClaudeCodeLockParityTests：执行授权查询；如果没有这行代码，list_granted 锁路径没有真实输入。
        self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodeLockParityTests：断言查询成功；如果没有这行代码，失败结果可能掩盖锁断言。
        self.assertEqual([("check", "list_granted_applications")], callbacks.calls)  # 新增代码+ClaudeCodeLockParityTests：断言只 check 不 acquire；如果没有这行代码，查询工具抢锁不会被发现。
        self.assertEqual("check", result["debug"]["lock_mode"])  # 新增代码+ClaudeCodeLockParityTests：断言 debug 标记检查模式；如果没有这行代码，锁行为不可观测。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，test_list_granted_applications_checks_lock_but_does_not_acquire 到此结束；如果没有这个边界说明，用户不容易看出查询锁测试范围。

    def test_screenshot_acquires_lock_before_observe(self) -> None:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，验证 screenshot 需要 acquire lock；如果没有这段测试，观察工具可能绕过独占控制语义。
        callbacks = TrackingLockCallbacks()  # 新增代码+ClaudeCodeLockParityTests：创建 fake lock；如果没有这行代码，测试无法记录取锁。
        host = FakeHost()  # 新增代码+ClaudeCodeLockParityTests：创建 fake host；如果没有这行代码，screenshot 无法执行观察路径。
        result = dispatch_computer_use_mcp_v2_tool("screenshot", {}, _context_with_lock(callbacks, host))  # 新增代码+ClaudeCodeLockParityTests：执行 screenshot；如果没有这行代码，观察取锁路径没有真实输入。
        self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodeLockParityTests：断言截图工具成功；如果没有这行代码，后续调用顺序断言可能误读失败路径。
        self.assertEqual([("acquire", "screenshot"), ("held", "screenshot")], callbacks.calls)  # 新增代码+ClaudeCodeLockParityTests：断言先 acquire 并查询本地持锁；如果没有这行代码，观察工具绕锁不会失败。
        self.assertEqual(["observe"], host.calls)  # 新增代码+ClaudeCodeLockParityTests：断言 host 观察被调用一次；如果没有这行代码，测试不能证明取锁后继续执行。
        self.assertEqual("acquire", result["debug"]["lock_mode"])  # 新增代码+ClaudeCodeLockParityTests：断言结果 debug 标记 acquire 模式；如果没有这行代码，模型看不到工具锁语义。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，test_screenshot_acquires_lock_before_observe 到此结束；如果没有这个边界说明，用户不容易看出截图锁测试范围。

    def test_left_click_acquires_lock_before_host_action(self) -> None:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，验证真实动作需要 acquire lock；如果没有这段测试，鼠标点击可能绕过独占锁。
        callbacks = TrackingLockCallbacks()  # 新增代码+ClaudeCodeLockParityTests：创建 fake lock；如果没有这行代码，测试无法记录取锁。
        host = FakeHost()  # 新增代码+ClaudeCodeLockParityTests：创建 fake host；如果没有这行代码，left_click 无法进入成功动作路径。
        result = dispatch_computer_use_mcp_v2_tool("left_click", {"coordinate": [1, 2]}, _context_with_lock(callbacks, host))  # 新增代码+ClaudeCodeLockParityTests：执行 left_click；如果没有这行代码，动作取锁路径没有真实输入。
        self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodeLockParityTests：断言动作成功；如果没有这行代码，后续 host 调用断言可能误读失败。
        self.assertEqual([("acquire", "left_click"), ("held", "left_click")], callbacks.calls)  # 新增代码+ClaudeCodeLockParityTests：断言动作先 acquire；如果没有这行代码，鼠标动作绕锁不会失败。
        self.assertEqual(["left_click"], host.calls)  # 新增代码+ClaudeCodeLockParityTests：断言 host 动作执行；如果没有这行代码，测试不能证明取锁后继续到执行层。
        self.assertEqual("acquire", result["debug"]["lock_mode"])  # 新增代码+ClaudeCodeLockParityTests：断言 debug 标记 acquire 模式；如果没有这行代码，动作锁语义不可见。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，test_left_click_acquires_lock_before_host_action 到此结束；如果没有这个边界说明，用户不容易看出动作锁测试范围。

    def test_acquire_failure_blocks_desktop_action(self) -> None:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，验证取锁失败会阻断 host 动作；如果没有这段测试，锁被占用时仍可能点击桌面。
        callbacks = TrackingLockCallbacks(acquire_allowed=False)  # 新增代码+ClaudeCodeLockParityTests：创建取锁失败的 fake lock；如果没有这行代码，阻断路径没有输入。
        host = FakeHost()  # 新增代码+ClaudeCodeLockParityTests：创建 fake host；如果没有这行代码，无法证明 host 未被调用。
        result = dispatch_computer_use_mcp_v2_tool("left_click", {"coordinate": [1, 2]}, _context_with_lock(callbacks, host))  # 新增代码+ClaudeCodeLockParityTests：执行会被锁拒绝的动作；如果没有这行代码，失败阻断没有真实调用。
        self.assertFalse(result["ok"], result)  # 新增代码+ClaudeCodeLockParityTests：断言工具失败；如果没有这行代码，锁失败可能被误包成成功。
        self.assertEqual("computer_use_lock_unavailable", result["error_class"])  # 新增代码+ClaudeCodeLockParityTests：断言稳定错误类别；如果没有这行代码，调用方无法按锁失败恢复。
        self.assertEqual([("acquire", "left_click")], callbacks.calls)  # 新增代码+ClaudeCodeLockParityTests：断言失败后不再查 held；如果没有这行代码，阻断路径可能继续执行额外逻辑。
        self.assertEqual([], host.calls)  # 新增代码+ClaudeCodeLockParityTests：断言 host 动作未执行；如果没有这行代码，取锁失败仍触碰桌面不会被发现。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，test_acquire_failure_blocks_desktop_action 到此结束；如果没有这个边界说明，用户不容易看出失败阻断测试范围。

    def test_turn_cleanup_releases_lock(self) -> None:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，验证 turn cleanup 释放锁；如果没有这段测试，长任务结束后可能残留桌面锁。
        callbacks = TrackingLockCallbacks()  # 新增代码+ClaudeCodeLockParityTests：创建 fake lock；如果没有这行代码，cleanup 释放无法记录。
        result = cleanup_computer_use_mcp_v2_turn(_context_with_lock(callbacks), reason="unit cleanup")  # 新增代码+ClaudeCodeLockParityTests：执行 runtime cleanup helper；如果没有这行代码，turn cleanup API 没有验证。
        self.assertTrue(result["cleanup_completed"], result)  # 新增代码+ClaudeCodeLockParityTests：断言 cleanup 完成；如果没有这行代码，失败清理可能被忽略。
        self.assertIn(("cleanup", "unit cleanup"), callbacks.calls)  # 新增代码+ClaudeCodeLockParityTests：断言调用 cleanup_after_turn；如果没有这行代码，helper 可能绕过完整 cleanup 回调。
        self.assertIn(("release", "unit cleanup"), callbacks.calls)  # 新增代码+ClaudeCodeLockParityTests：断言 cleanup 内释放锁；如果没有这行代码，turn cleanup 不释放锁不会失败。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，test_turn_cleanup_releases_lock 到此结束；如果没有这个边界说明，用户不容易看出 cleanup 测试范围。

    def test_windows_session_runtime_exposes_claudecode_lock_callbacks(self) -> None:  # 新增代码+ClaudeCodeLockParityTests：函数段开始，验证底层 runtime 也暴露 facade 需要的锁回调；如果没有这段测试，绑定层可能只能依赖 lock_manager 内部细节。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+ClaudeCodeLockParityTests：创建隔离临时目录；如果没有这行代码，真实用户锁文件可能被测试改动。
            lock_manager = ComputerUseLockManager(base_dir=Path(temp_dir))  # 新增代码+ClaudeCodeLockParityTests：创建隔离 lock manager；如果没有这行代码，runtime 没有可控锁事实源。
            runtime = WindowsComputerUseSessionRuntime(lock_manager=lock_manager, session_id="unit-session")  # 新增代码+ClaudeCodeLockParityTests：创建指定 session 的 runtime；如果没有这行代码，回调方法没有测试对象。
            check = runtime.check_computer_use_lock("request_access")  # 新增代码+ClaudeCodeLockParityTests：调用只检查锁回调；如果没有这行代码，defers-lock 底层别名没有覆盖。
            acquire = runtime.acquire_computer_use_lock("screenshot")  # 新增代码+ClaudeCodeLockParityTests：调用取锁回调；如果没有这行代码，动作/观察底层别名没有覆盖。
            held = runtime.is_lock_held_locally("screenshot")  # 新增代码+ClaudeCodeLockParityTests：查询本地持锁状态；如果没有这行代码，debug 持锁字段没有事实验证。
            cleanup = runtime.cleanup_after_turn("unit cleanup")  # 新增代码+ClaudeCodeLockParityTests：调用 cleanup 别名；如果没有这行代码，turn cleanup 别名没有覆盖。
        self.assertTrue(check["ok"], check)  # 新增代码+ClaudeCodeLockParityTests：断言检查回调成功；如果没有这行代码，check 别名坏了不会失败。
        self.assertTrue(acquire["acquired"], acquire)  # 新增代码+ClaudeCodeLockParityTests：断言取锁成功；如果没有这行代码，acquire 别名坏了不会失败。
        self.assertTrue(held)  # 新增代码+ClaudeCodeLockParityTests：断言取锁后本地持锁；如果没有这行代码，has_lock 接线坏了不会失败。
        self.assertTrue(cleanup["cleanup_completed"], cleanup)  # 新增代码+ClaudeCodeLockParityTests：断言 cleanup 完成；如果没有这行代码，cleanup 别名坏了不会失败。
        self.assertTrue(cleanup["lock_released"], cleanup)  # 新增代码+ClaudeCodeLockParityTests：断言 cleanup 释放锁；如果没有这行代码，turn cleanup 不释放锁不会失败。
    # 新增代码+ClaudeCodeLockParityTests：函数段结束，test_windows_session_runtime_exposes_claudecode_lock_callbacks 到此结束；如果没有这个边界说明，用户不容易看出底层 runtime 回调测试范围。
# 新增代码+ClaudeCodeLockParityTests：类段结束，ComputerUseMcpV2LockLifecycleTests 到此结束；如果没有这个边界说明，用户不容易看出锁生命周期测试范围。


if __name__ == "__main__":  # 新增代码+ClaudeCodeLockParityTests：允许直接运行本测试文件；如果没有这行代码，手动调试不方便。
    unittest.main()  # 新增代码+ClaudeCodeLockParityTests：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
