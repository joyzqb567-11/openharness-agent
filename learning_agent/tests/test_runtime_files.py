"""Runtime file safety regression tests."""  # 修改代码+RuntimeFileSafetyFallback验收: 说明本文件专门验证 runtime 文件写入安全；若没有这行代码，维护者不容易知道这些测试服务于真实终端验收稳定性。
from __future__ import annotations  # 修改代码+RuntimeFileSafetyFallback验收: 延迟解析类型注解以兼容不同 Python 版本；若没有这行代码，类型注解在旧解释顺序下更容易出错。
from learning_agent.tests.support import *  # 修改代码+RuntimeFileSafetyFallback验收: 复用项目测试基类、Path、tempfile 和 mock；若没有这行代码，本测试会重复大量公共准备逻辑。


class RuntimeFilesTests(LearningAgentTestBase):  # 修改代码+RuntimeFileSafetyFallback验收: 定义运行时文件工具测试类；若没有这行代码，unittest discover 不会发现本组测试。
    def test_atomic_write_text_retries_permission_error_during_replace(self) -> None:  # 修改代码+RuntimeFileSafetyFallback验收: 验证 os.replace 被 Windows 临时拒绝时会重试；若没有这行代码，可见终端验收的状态写入失败会再次回归。
        from learning_agent.runtime import files as runtime_files  # 修改代码+RuntimeFileSafetyFallback验收: 导入真实 runtime files 模块；若没有这行代码，测试无法覆盖生产 atomic_write_text。
        with tempfile.TemporaryDirectory() as raw_dir:  # 修改代码+RuntimeFileSafetyFallback验收: 创建隔离目录模拟 memory/status；若没有这行代码，测试可能污染真实状态文件。
            target_path = Path(raw_dir) / "state.json"  # 修改代码+RuntimeFileSafetyFallback验收: 准备被原子替换的目标文件；若没有这行代码，测试没有可验证输出。
            real_replace = runtime_files.os.replace  # 修改代码+RuntimeFileSafetyFallback验收: 保存原始 replace 用于第二次真正写入；若没有这行代码，mock 后无法完成成功分支。
            replace_calls = {"count": 0}  # 修改代码+RuntimeFileSafetyFallback验收: 记录 replace 被调用次数；若没有这行代码，测试无法证明发生过重试。

            def flaky_replace(source: str, destination: str) -> None:  # 修改代码+RuntimeFileSafetyFallback验收: 定义第一次失败第二次成功的 replace；若没有这行代码，测试无法稳定复现 Windows 短暂锁冲突。
                replace_calls["count"] += 1  # 修改代码+RuntimeFileSafetyFallback验收: 累加 replace 调用次数；若没有这行代码，断言不知道重试是否执行。
                if replace_calls["count"] == 1:  # 修改代码+RuntimeFileSafetyFallback验收: 第一次调用模拟拒绝访问；若没有这行代码，旧代码不会出现红灯。
                    raise PermissionError("simulated Windows sharing violation")  # 修改代码+RuntimeFileSafetyFallback验收: 抛出与真实验收相同类别的权限错误；若没有这行代码，测试不能覆盖 observed bug。
                real_replace(source, destination)  # 修改代码+RuntimeFileSafetyFallback验收: 第二次调用真实替换目标文件；若没有这行代码，测试无法验证最终内容。

            with mock.patch.object(runtime_files.os, "replace", side_effect=flaky_replace), mock.patch.object(runtime_files.time, "sleep", return_value=None) as sleep_mock:  # 修改代码+RuntimeFileSafetyFallback验收: 拦截 replace 和 sleep 保持测试快速可控；若没有这行代码，测试无法稳定制造失败和避免真实等待。
                result_path = runtime_files.atomic_write_text(target_path, "{\"ok\": true}\n")  # 修改代码+RuntimeFileSafetyFallback验收: 调用生产原子写函数；若没有这行代码，测试不会覆盖真实修复点。
            self.assertEqual(result_path, target_path)  # 修改代码+RuntimeFileSafetyFallback验收: 断言函数返回目标路径；若没有这行代码，调用方拿不到可审计写入位置的回归不会暴露。
            self.assertEqual(target_path.read_text(encoding="utf-8"), "{\"ok\": true}\n")  # 修改代码+RuntimeFileSafetyFallback验收: 断言重试后文件内容完整；若没有这行代码，只重试但写坏内容也可能通过。
            self.assertEqual(replace_calls["count"], 2)  # 修改代码+RuntimeFileSafetyFallback验收: 断言第一次失败后确实重试一次；若没有这行代码，直接成功或直接失败都不容易区分。
            sleep_mock.assert_called_once()  # 修改代码+RuntimeFileSafetyFallback验收: 断言重试前有短暂退避；若没有这行代码，高并发时可能忙等占用 CPU。

    def test_atomic_write_text_falls_back_when_replace_is_permanently_denied(self) -> None:  # 新增代码+RuntimeFileSafetyFallback验收: 验证 os.replace 被当前 Windows 工作区永久拒绝时会安全降级；若没有这行代码，Phase95 CLI 会再次被同类权限错误卡住。
        from learning_agent.runtime import files as runtime_files  # 新增代码+RuntimeFileSafetyFallback验收: 导入真实 runtime files 模块；若没有这行代码，测试无法覆盖生产 atomic_write_text。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RuntimeFileSafetyFallback验收: 创建隔离目录模拟状态落盘位置；若没有这行代码，测试可能污染真实 memory 目录。
            target_path = Path(raw_dir) / "state.json"  # 新增代码+RuntimeFileSafetyFallback验收: 准备目标状态文件路径；若没有这行代码，后续无法确认文件是否真的写成。
            replace_calls = {"count": 0}  # 新增代码+RuntimeFileSafetyFallback验收: 记录 replace 尝试次数；若没有这行代码，无法证明降级发生在所有重试之后。

            def denied_replace(source: str, destination: str) -> None:  # 新增代码+RuntimeFileSafetyFallback验收: 定义始终拒绝的 replace 替身；若没有这行代码，测试无法稳定复现真实 WinError 5。
                _ = source  # 新增代码+RuntimeFileSafetyFallback验收: 明确 source 参数在本模拟里只用于接口兼容；若没有这行代码，读者会误以为这里遗漏了源文件检查。
                _ = destination  # 新增代码+RuntimeFileSafetyFallback验收: 明确 destination 参数在本模拟里只用于接口兼容；若没有这行代码，读者会误以为这里遗漏了目标文件检查。
                replace_calls["count"] += 1  # 新增代码+RuntimeFileSafetyFallback验收: 累计 replace 调用次数；若没有这行代码，无法确认 retry 机制仍然先被完整执行。
                raise PermissionError("simulated permanent replace denial")  # 新增代码+RuntimeFileSafetyFallback验收: 模拟当前工作区持续拒绝 os.replace；若没有这行代码，红灯用例不会失败。

            with mock.patch.object(runtime_files.os, "replace", side_effect=denied_replace), mock.patch.object(runtime_files.time, "sleep", return_value=None):  # 新增代码+RuntimeFileSafetyFallback验收: 拦截 replace 和 sleep 保持测试快速稳定；若没有这行代码，测试无法稳定控制失败路径。
                result_path = runtime_files.atomic_write_text(target_path, "{\"ok\": true}\n")  # 新增代码+RuntimeFileSafetyFallback验收: 调用生产写入函数触发永久拒绝场景；若没有这行代码，测试没有实际验证对象。
            self.assertEqual(result_path, target_path)  # 新增代码+RuntimeFileSafetyFallback验收: 断言函数仍返回目标路径；若没有这行代码，调用方拿不到可审计的写入位置。
            self.assertEqual(target_path.read_text(encoding="utf-8"), "{\"ok\": true}\n")  # 新增代码+RuntimeFileSafetyFallback验收: 断言降级后内容完整落盘；若没有这行代码，写空或写坏也可能混过测试。
            self.assertEqual(replace_calls["count"], 1 + len(runtime_files.ATOMIC_REPLACE_RETRY_DELAYS_SECONDS))  # 新增代码+RuntimeFileSafetyFallback验收: 断言所有 replace 重试都先执行完；若没有这行代码，代码可能过早放弃原子路径。
            self.assertFalse(list(target_path.parent.glob(".state.json.*.tmp")))  # 新增代码+RuntimeFileSafetyFallback验收: 断言降级成功后不留下临时文件；若没有这行代码，长期运行会堆积无用状态碎片。

    def test_file_lock_can_be_reused_when_lock_file_cannot_be_deleted(self) -> None:  # 新增代码+RuntimeFileSafetyFallback验收: 验证锁文件无法删除时 FileLock 仍能释放并复用；若没有这行代码，真实终端验收会被遗留 mutex 永久卡住。
        from learning_agent.runtime import files as runtime_files  # 新增代码+RuntimeFileSafetyFallback验收: 导入真实 runtime files 模块；若没有这行代码，测试无法覆盖生产 FileLock。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RuntimeFileSafetyFallback验收: 创建隔离目录模拟 grants/status 锁路径；若没有这行代码，测试可能污染真实锁文件。
            lock_path = Path(raw_dir) / ".state.mutex"  # 新增代码+RuntimeFileSafetyFallback验收: 准备一个真实锁文件路径；若没有这行代码，测试无法验证同一路径二次加锁。
            with mock.patch.object(runtime_files.Path, "unlink", side_effect=PermissionError("simulated unlink denial")):  # 新增代码+RuntimeFileSafetyFallback验收: 模拟当前工作区拒绝删除锁文件；若没有这行代码，旧的 create/unlink 锁模型不会稳定红灯。
                with runtime_files.FileLock(lock_path, timeout_seconds=0.2):  # 新增代码+RuntimeFileSafetyFallback验收: 第一次持有并释放锁；若没有这行代码，测试无法制造遗留锁文件。
                    self.assertTrue(lock_path.exists())  # 新增代码+RuntimeFileSafetyFallback验收: 断言锁文件确实存在；若没有这行代码，复用场景没有真实前提。
                with runtime_files.FileLock(lock_path, timeout_seconds=0.2):  # 新增代码+RuntimeFileSafetyFallback验收: 第二次复用同一锁路径；若没有这行代码，无法证明遗留锁文件不会阻塞后续运行。
                    self.assertTrue(lock_path.exists())  # 新增代码+RuntimeFileSafetyFallback验收: 断言复用时锁文件仍可作为锁载体存在；若没有这行代码，测试无法证明新锁模型无需删除文件。


if __name__ == "__main__":  # 修改代码+RuntimeFileSafetyFallback验收: 允许直接运行本测试文件；若没有这行代码，单文件调试不方便。
    unittest.main()  # 修改代码+RuntimeFileSafetyFallback验收: 启动 unittest；若没有这行代码，直接执行文件不会跑测试。
