"""Task 4 的自有资源清理与恢复成熟度测试。"""  # 新增代码+CleanupRecoveryMaturity：说明本测试专门验收 owned resource registry；如果没有这一行，用户不容易看懂本文件为什么关注清理和残留。
from __future__ import annotations  # 新增代码+CleanupRecoveryMaturity：启用延迟类型注解解析；如果没有这一行，测试在旧导入路径下更容易被类型名影响。

import importlib  # 新增代码+CleanupRecoveryMaturity：用于显式导入待实现模块并产生清晰红灯；如果没有这一行，测试不能证明缺少 owned_resource_registry.py。
import tempfile  # 新增代码+CleanupRecoveryMaturity：用于隔离 session runtime 的锁和通知文件；如果没有这一行，测试可能污染真实用户状态。
import unittest  # 新增代码+CleanupRecoveryMaturity：提供 unittest 测试框架；如果没有这一行，项目测试发现器无法运行这些用例。
from pathlib import Path  # 新增代码+CleanupRecoveryMaturity：用于构造临时锁目录路径；如果没有这一行，session runtime 测试路径拼接会更脆弱。


# 新增代码+CleanupRecoveryMaturity：类段落开始，CleanupRecoveryMaturityTest 覆盖蓝图 Task 4 的注册、清理、保护和残留检查；如果没有这个类，清理成熟度没有集中验收入口。
class CleanupRecoveryMaturityTest(unittest.TestCase):  # 新增代码+CleanupRecoveryMaturity：定义清理恢复成熟度测试类；如果没有这一行，测试函数缺少 unittest 组织边界。
    # 新增代码+CleanupRecoveryMaturity：函数段落开始，_registry_module 统一导入自有资源注册表模块；如果没有这个 helper，每个测试都会重复导入逻辑。
    def _registry_module(self):  # 新增代码+CleanupRecoveryMaturity：定义 registry 模块导入 helper；如果没有这一行，红灯阶段不能稳定指向缺失模块。
        return importlib.import_module("learning_agent.computer_use.owned_resource_registry")  # 新增代码+CleanupRecoveryMaturity：导入还未实现的 owned_resource_registry；如果没有这一行，测试无法验证蓝图要求的新模块。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，_registry_module 到此结束；如果没有这个边界说明，用户不容易看出导入 helper 范围。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，test_register_owned_process_and_window_records_required_fields 验证进程和窗口登记字段；如果没有这个测试，注册表可能缺少 session_id、created_at 或状态字段。
    def test_register_owned_process_and_window_records_required_fields(self) -> None:  # 新增代码+CleanupRecoveryMaturity：定义登记字段测试；如果没有这一行，蓝图字段要求没有自动检查。
        module = self._registry_module()  # 新增代码+CleanupRecoveryMaturity：加载自有资源注册表模块；如果没有这一行，测试不能调用待实现 API。
        registry = module.OwnedResourceRegistry(session_id="session-a", clock=lambda: "2026-06-05T00:00:00Z")  # 新增代码+CleanupRecoveryMaturity：创建带固定时间的注册表；如果没有这一行，created_at 断言会不稳定。
        process_record = registry.register_owned_process(process_id=4242, executable="Obsidian.exe")  # 新增代码+CleanupRecoveryMaturity：登记 agent 自己启动的进程；如果没有这一行，进程清理没有登记来源。
        window_record = registry.register_owned_window(window_id="hwnd:8801", process_id=4242)  # 新增代码+CleanupRecoveryMaturity：登记该进程创建的窗口；如果没有这一行，窗口清理没有登记来源。
        self.assertEqual("session-a", process_record["session_id"])  # 新增代码+CleanupRecoveryMaturity：确认进程记录带 session_id；如果没有这一行，跨会话清理可能误扫。
        self.assertEqual(4242, process_record["process_id"])  # 新增代码+CleanupRecoveryMaturity：确认进程 pid 被保存；如果没有这一行，清理时不知道目标进程。
        self.assertEqual("", process_record["window_id"])  # 新增代码+CleanupRecoveryMaturity：确认进程记录没有伪造窗口 id；如果没有这一行，进程和窗口边界可能混乱。
        self.assertEqual("registered", process_record["cleanup_state"])  # 新增代码+CleanupRecoveryMaturity：确认初始清理状态是 registered；如果没有这一行，清理状态机不清楚。
        self.assertEqual("unchecked", process_record["residual_check_state"])  # 新增代码+CleanupRecoveryMaturity：确认初始残留检查状态是 unchecked；如果没有这一行，残留检查前后无法区分。
        self.assertEqual("2026-06-05T00:00:00Z", process_record["created_at"])  # 新增代码+CleanupRecoveryMaturity：确认创建时间被保存；如果没有这一行，审计无法排序。
        self.assertEqual("session-a", window_record["session_id"])  # 新增代码+CleanupRecoveryMaturity：确认窗口记录带 session_id；如果没有这一行，跨会话窗口可能被误清理。
        self.assertEqual("hwnd:8801", window_record["window_id"])  # 新增代码+CleanupRecoveryMaturity：确认窗口 id 被保存；如果没有这一行，窗口清理没有目标。
        self.assertEqual(4242, window_record["process_id"])  # 新增代码+CleanupRecoveryMaturity：确认窗口所属 pid 被保存；如果没有这一行，窗口和进程不能关联。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，test_register_owned_process_and_window_records_required_fields 到此结束；如果没有这个边界说明，用户不容易看出登记字段测试范围。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，test_cleanup_only_owned_resources_and_preserves_preexisting_user_windows 验证只清理自有资源；如果没有这个测试，用户已有窗口可能被误关。
    def test_cleanup_only_owned_resources_and_preserves_preexisting_user_windows(self) -> None:  # 新增代码+CleanupRecoveryMaturity：定义自有资源清理边界测试；如果没有这一行，保护用户窗口要求没有自动检查。
        module = self._registry_module()  # 新增代码+CleanupRecoveryMaturity：加载注册表模块；如果没有这一行，测试无法创建 registry。
        cleanup_calls: list[str] = []  # 新增代码+CleanupRecoveryMaturity：记录被清理的资源身份；如果没有这一行，测试无法证明只调用了自有资源清理。
        registry = module.OwnedResourceRegistry(session_id="session-a", clock=lambda: "2026-06-05T00:00:00Z")  # 新增代码+CleanupRecoveryMaturity：创建隔离注册表；如果没有这一行，清理记录没有容器。
        registry.register_owned_process(process_id=1001, executable="Obsidian.exe", cleanup_callback=lambda record: cleanup_calls.append(f"process:{record['process_id']}"))  # 新增代码+CleanupRecoveryMaturity：登记自有进程及清理回调；如果没有这一行，清理成功路径没有可观察证据。
        registry.register_owned_window(window_id="hwnd:1001", process_id=1001, cleanup_callback=lambda record: cleanup_calls.append(f"window:{record['window_id']}"))  # 新增代码+CleanupRecoveryMaturity：登记自有窗口及清理回调；如果没有这一行，窗口清理路径没有可观察证据。
        user_window = registry.register_user_preexisting_window(window_id="hwnd:2002", process_id=2002, title_preview="User Vault")  # 新增代码+CleanupRecoveryMaturity：登记用户已有窗口为受保护资源；如果没有这一行，测试无法证明预先存在窗口会被保留。
        result = registry.cleanup_owned_resources(reason="test cleanup")  # 新增代码+CleanupRecoveryMaturity：执行自有资源清理；如果没有这一行，清理边界不会被触发。
        self.assertEqual(["process:1001", "window:hwnd:1001"], cleanup_calls)  # 新增代码+CleanupRecoveryMaturity：确认只清理 agent 自有资源；如果没有这一行，误清理用户窗口不会被发现。
        self.assertTrue(result["cleanup_completed"])  # 新增代码+CleanupRecoveryMaturity：确认清理流程完成；如果没有这一行，清理状态可能只调用未汇总。
        self.assertEqual("preserved_user_resource", user_window["cleanup_state"])  # 新增代码+CleanupRecoveryMaturity：确认用户已有窗口被标记为保留；如果没有这一行，保护状态不可见。
        self.assertTrue(result["preexisting_user_windows_preserved"])  # 新增代码+CleanupRecoveryMaturity：确认汇总结果报告保护用户窗口；如果没有这一行，上层无法给用户解释。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，test_cleanup_only_owned_resources_and_preserves_preexisting_user_windows 到此结束；如果没有这个边界说明，用户不容易看出清理边界测试范围。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，test_abort_cleans_owned_resources_through_registry 验证 abort 会调用自有资源清理；如果没有这个测试，急停后可能留下 agent 自己启动的进程。
    def test_abort_cleans_owned_resources_through_registry(self) -> None:  # 新增代码+CleanupRecoveryMaturity：定义 abort 清理测试；如果没有这一行，蓝图 abort cleans owned resources 没有自动检查。
        module = self._registry_module()  # 新增代码+CleanupRecoveryMaturity：加载注册表模块；如果没有这一行，测试无法创建 registry。
        cleanup_calls: list[int] = []  # 新增代码+CleanupRecoveryMaturity：记录 abort 清理到的进程；如果没有这一行，abort 是否真正清理不可见。
        registry = module.OwnedResourceRegistry(session_id="session-a", clock=lambda: "2026-06-05T00:00:00Z")  # 新增代码+CleanupRecoveryMaturity：创建隔离注册表；如果没有这一行，abort 清理没有状态容器。
        registry.register_owned_process(process_id=3003, executable="Paint.exe", cleanup_callback=lambda record: cleanup_calls.append(record["process_id"]))  # 新增代码+CleanupRecoveryMaturity：登记自有进程及清理回调；如果没有这一行，abort 没有可清理对象。
        result = registry.abort_cleanup(reason="user abort")  # 新增代码+CleanupRecoveryMaturity：执行 abort 清理；如果没有这一行，急停路径不会触发资源清理。
        self.assertEqual([3003], cleanup_calls)  # 新增代码+CleanupRecoveryMaturity：确认 abort 清理了自有进程；如果没有这一行，急停残留风险不会被发现。
        self.assertTrue(result["cleanup_completed"])  # 新增代码+CleanupRecoveryMaturity：确认 abort 清理完成；如果没有这一行，abort 结果无法被上层判断。
        self.assertEqual("abort_cleanup_completed", result["decision"])  # 新增代码+CleanupRecoveryMaturity：确认 abort 决策 token 稳定；如果没有这一行，终端输出不易解析。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，test_abort_cleans_owned_resources_through_registry 到此结束；如果没有这个边界说明，用户不容易看出 abort 清理测试范围。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，test_residual_check_fails_if_owned_process_remains 验证残留进程会让检查失败；如果没有这个测试，清理失败可能被误报成功。
    def test_residual_check_fails_if_owned_process_remains(self) -> None:  # 新增代码+CleanupRecoveryMaturity：定义残留检查失败测试；如果没有这一行，蓝图 residual check 要求没有自动检查。
        module = self._registry_module()  # 新增代码+CleanupRecoveryMaturity：加载注册表模块；如果没有这一行，测试无法创建 registry。
        registry = module.OwnedResourceRegistry(session_id="session-a", clock=lambda: "2026-06-05T00:00:00Z")  # 新增代码+CleanupRecoveryMaturity：创建隔离注册表；如果没有这一行，残留状态没有容器。
        record = registry.register_owned_process(process_id=4004, executable="Calc.exe", residual_check_callback=lambda owned_record: True)  # 新增代码+CleanupRecoveryMaturity：登记会被报告为仍存活的进程；如果没有这一行，残留失败路径没有样本。
        result = registry.check_residuals()  # 新增代码+CleanupRecoveryMaturity：执行残留检查；如果没有这一行，残留状态不会更新。
        self.assertFalse(result["residual_check_passed"])  # 新增代码+CleanupRecoveryMaturity：确认有残留时检查失败；如果没有这一行，清理失败可能被误当成功。
        self.assertTrue(result["residual_owned_process"])  # 新增代码+CleanupRecoveryMaturity：确认报告里写明自有进程残留；如果没有这一行，上层无法触发恢复。
        self.assertEqual("residual_present", record["residual_check_state"])  # 新增代码+CleanupRecoveryMaturity：确认记录状态被更新为残留存在；如果没有这一行，审计无法定位哪个资源残留。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，test_residual_check_fails_if_owned_process_remains 到此结束；如果没有这个边界说明，用户不容易看出残留检查测试范围。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，test_session_runtime_stop_and_abort_call_owned_resource_cleanup 验证 session runtime stop/abort 会调用 registry；如果没有这个测试，注册表可能没有接到真实命令路径。
    def test_session_runtime_stop_and_abort_call_owned_resource_cleanup(self) -> None:  # 新增代码+CleanupRecoveryMaturity：定义 session runtime 接线测试；如果没有这一行，蓝图 Step 3 没有自动检查。
        module = self._registry_module()  # 新增代码+CleanupRecoveryMaturity：加载注册表模块；如果没有这一行，测试无法创建 registry。
        session_runtime = importlib.import_module("learning_agent.computer_use.session_runtime")  # 新增代码+CleanupRecoveryMaturity：导入已有 session runtime；如果没有这一行，测试无法验证 stop/abort 接线。
        lock_module = importlib.import_module("learning_agent.computer_use.lock")  # 新增代码+CleanupRecoveryMaturity：导入锁管理器；如果没有这一行，runtime 测试无法隔离锁状态。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+CleanupRecoveryMaturity：创建临时目录隔离 runtime 状态；如果没有这一行，测试可能污染真实 lock 文件。
            cleanup_calls: list[int] = []  # 新增代码+CleanupRecoveryMaturity：记录 cleanup_turn 清理到的进程；如果没有这一行，stop 是否调用 registry 不可见。
            lock_manager = lock_module.ComputerUseLockManager(base_dir=Path(temp_dir) / "locks")  # 新增代码+CleanupRecoveryMaturity：创建临时锁管理器；如果没有这一行，runtime 不能安全运行。
            registry = module.OwnedResourceRegistry(session_id="session-a", clock=lambda: "2026-06-05T00:00:00Z")  # 新增代码+CleanupRecoveryMaturity：创建和 runtime 同 session 的 registry；如果没有这一行，stop 没有自有资源状态。
            registry.register_owned_process(process_id=5005, executable="Obsidian.exe", cleanup_callback=lambda record: cleanup_calls.append(record["process_id"]))  # 新增代码+CleanupRecoveryMaturity：登记 stop 应清理的自有进程；如果没有这一行，stop 接线没有对象。
            runtime = session_runtime.WindowsComputerUseSessionRuntime(lock_manager=lock_manager, session_id="session-a", owned_resource_registry=registry)  # 新增代码+CleanupRecoveryMaturity：把 registry 注入 runtime；如果没有这一行，runtime 无法调用自有资源清理。
            stop_result = runtime.cleanup_turn(reason="computer stop")  # 新增代码+CleanupRecoveryMaturity：模拟 `/computer stop` 底层清理；如果没有这一行，stop 路径不触发。
            self.assertEqual([5005], cleanup_calls)  # 新增代码+CleanupRecoveryMaturity：确认 stop 调用了自有进程清理；如果没有这一行，stop 漏接 registry 不会被发现。
            self.assertTrue(stop_result["owned_resource_cleanup_completed"])  # 新增代码+CleanupRecoveryMaturity：确认 stop 结果上浮清理完成字段；如果没有这一行，终端看不到自有资源清理状态。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+CleanupRecoveryMaturity：为 abort 路径创建另一套隔离目录；如果没有这一行，两个路径可能共享状态互相污染。
            abort_calls: list[int] = []  # 新增代码+CleanupRecoveryMaturity：记录 abort 清理到的进程；如果没有这一行，abort 是否调用 registry 不可见。
            lock_manager = lock_module.ComputerUseLockManager(base_dir=Path(temp_dir) / "locks")  # 新增代码+CleanupRecoveryMaturity：创建 abort 专用锁管理器；如果没有这一行，abort runtime 不能安全运行。
            registry = module.OwnedResourceRegistry(session_id="session-a", clock=lambda: "2026-06-05T00:00:00Z")  # 新增代码+CleanupRecoveryMaturity：创建 abort 专用 registry；如果没有这一行，abort 没有自有资源状态。
            registry.register_owned_process(process_id=6006, executable="Paint.exe", cleanup_callback=lambda record: abort_calls.append(record["process_id"]))  # 新增代码+CleanupRecoveryMaturity：登记 abort 应清理的自有进程；如果没有这一行，abort 接线没有对象。
            runtime = session_runtime.WindowsComputerUseSessionRuntime(lock_manager=lock_manager, session_id="session-a", owned_resource_registry=registry)  # 新增代码+CleanupRecoveryMaturity：把 registry 注入 abort runtime；如果没有这一行，abort 无法调用自有资源清理。
            abort_result = runtime.request_global_abort("user abort", source="test")  # 新增代码+CleanupRecoveryMaturity：模拟用户急停；如果没有这一行，abort 清理路径不触发。
            self.assertEqual([6006], abort_calls)  # 新增代码+CleanupRecoveryMaturity：确认 abort 调用了自有进程清理；如果没有这一行，急停残留风险不会被发现。
            self.assertTrue(abort_result["owned_resource_cleanup_completed"])  # 新增代码+CleanupRecoveryMaturity：确认 abort 结果上浮清理完成字段；如果没有这一行，终端看不到急停清理状态。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，test_session_runtime_stop_and_abort_call_owned_resource_cleanup 到此结束；如果没有这个边界说明，用户不容易看出 runtime 接线测试范围。
# 新增代码+CleanupRecoveryMaturity：类段落结束，CleanupRecoveryMaturityTest 到此结束；如果没有这个边界说明，用户不容易看出 Task 4 测试集合范围。


if __name__ == "__main__":  # 新增代码+CleanupRecoveryMaturity：允许直接运行本测试文件；如果没有这一行，用户双击或脚本方式运行时没有入口。
    unittest.main()  # 新增代码+CleanupRecoveryMaturity：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行测试。
