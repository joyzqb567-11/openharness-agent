import importlib  # 新增代码+GenericLaunchBackendMaturity：导入动态模块加载工具；如果没有这一行，红测无法清楚暴露 generic launch backend 模块缺失。
import unittest  # 新增代码+GenericLaunchBackendMaturity：导入 unittest 测试框架；如果没有这一行，本文件不能被项目标准测试命令执行。

class WindowsComputerUseGenericLaunchBackendMaturityTests(unittest.TestCase):  # 新增代码+GenericLaunchBackendMaturity：类段开始，集中验收通用启动后端成熟边界；如果没有这个类，Task 2 的安全启动要求没有回归保护。
    def _backend_module(self):  # 新增代码+GenericLaunchBackendMaturity：函数段开始，统一加载待实现的通用启动后端模块；如果没有这个函数，每个测试都会重复导入并让失败原因分散。
        return importlib.import_module("learning_agent.computer_use.generic_launch_backend")  # 新增代码+GenericLaunchBackendMaturity：加载 generic launch backend 模块；如果没有这一行，测试无法访问请求、结果和后端类。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，_backend_module 到此结束；如果没有这个边界说明，代码小白不容易看出动态导入 helper 的范围。

    def test_default_path_does_not_call_backend_or_touch_desktop(self) -> None:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，验证默认路径不会启动真实应用；如果没有这个测试，/computer use --full 可能被误做成默认打开任意应用。
        module = self._backend_module()  # 新增代码+GenericLaunchBackendMaturity：读取通用启动后端模块；如果没有这一行，后续没有被测对象。
        backend = module.Phase110RecordingGenericLaunchBackend()  # 新增代码+GenericLaunchBackendMaturity：创建记录型后端；如果没有这一行，无法证明默认关闭时后端没有被调用。
        report = module.run_generic_launch_backend(module.phase110_contract_safe_phase108_report(), enable_real_launch=False, backend=backend)  # 新增代码+GenericLaunchBackendMaturity：用安全样本运行默认关闭路径；如果没有这一行，默认零副作用没有事实证据。
        self.assertEqual(report["decision"], "generic_real_launch_disabled_by_default")  # 新增代码+GenericLaunchBackendMaturity：断言默认拒绝进入真实后端；如果没有这一行，默认行为可能悄悄变成启动应用。
        self.assertEqual(len(backend.launches), 0)  # 新增代码+GenericLaunchBackendMaturity：断言后端调用次数为零；如果没有这一行，只看输出可能漏掉隐藏调用。
        self.assertFalse(report["process_started"])  # 新增代码+GenericLaunchBackendMaturity：断言没有进程启动；如果没有这一行，默认路径的真实副作用不可见。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+GenericLaunchBackendMaturity：断言没有触碰真实桌面；如果没有这一行，测试可能误放过后台启动。
        self.assertTrue(report["default_off_backend_not_called"])  # 新增代码+GenericLaunchBackendMaturity：断言默认关闭字段为真；如果没有这一行，终端和矩阵无法直接展示安全默认值。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，test_default_path_does_not_call_backend_or_touch_desktop 到此结束；如果没有这个边界说明，读者不容易看出默认关闭测试范围。

    def test_authorized_path_calls_backend_with_argv_not_shell_string(self) -> None:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，验证授权路径使用 argv 而不是 shell 字符串；如果没有这个测试，通用启动可能退化成高风险命令拼接。
        module = self._backend_module()  # 新增代码+GenericLaunchBackendMaturity：读取通用启动后端模块；如果没有这一行，后续无法创建记录后端。
        backend = module.Phase110RecordingGenericLaunchBackend()  # 新增代码+GenericLaunchBackendMaturity：创建记录型后端；如果没有这一行，无法检查后端收到的请求形状。
        report = module.run_generic_launch_backend(module.phase110_contract_safe_phase108_report(), enable_real_launch=True, backend=backend)  # 新增代码+GenericLaunchBackendMaturity：显式授权安全样本进入后端；如果没有这一行，argv 形状没有被验证。
        self.assertEqual(len(backend.launches), 1)  # 新增代码+GenericLaunchBackendMaturity：断言后端正好收到一次请求；如果没有这一行，多次启动或未启动都可能漏检。
        request = backend.launches[0]  # 新增代码+GenericLaunchBackendMaturity：读取记录下来的请求副本；如果没有这一行，后续无法检查 argv 细节。
        self.assertEqual(request["argv"], ["Obsidian.exe", "--phase110-safe-sample"])  # 新增代码+GenericLaunchBackendMaturity：断言 argv 数组形状固定；如果没有这一行，shell 字符串风险可能复发。
        self.assertEqual(request["command_shape"], "argv_no_shell")  # 新增代码+GenericLaunchBackendMaturity：断言命令形状不经过 shell；如果没有这一行，安全计划字段无法转化为后端约束。
        self.assertFalse(request["uses_shell_string"])  # 新增代码+GenericLaunchBackendMaturity：断言没有 shell 字符串；如果没有这一行，命令注入风险不够可测。
        self.assertTrue(report["backend_launch_reaches_launcher"])  # 新增代码+GenericLaunchBackendMaturity：断言授权请求抵达通用后端；如果没有这一行，最后一跳可能仍停在计划层。
        self.assertTrue(report["cleanup_registered"])  # 新增代码+GenericLaunchBackendMaturity：断言启动结果登记了清理责任；如果没有这一行，真实启动后可能没有收尾句柄。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，test_authorized_path_calls_backend_with_argv_not_shell_string 到此结束；如果没有这个边界说明，读者不容易看出 argv 测试范围。

    def test_unsafe_plan_refuses_before_backend_call(self) -> None:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，验证危险计划在后端调用前被拒绝；如果没有这个测试，PowerShell 或 shell 字符串可能进入真实启动层。
        module = self._backend_module()  # 新增代码+GenericLaunchBackendMaturity：读取通用启动后端模块；如果没有这一行，后续无法使用危险样本。
        backend = module.Phase110RecordingGenericLaunchBackend()  # 新增代码+GenericLaunchBackendMaturity：创建记录型后端；如果没有这一行，无法证明拒绝发生在后端调用之前。
        report = module.run_generic_launch_backend(module.phase110_contract_unsafe_phase108_report(), enable_real_launch=True, backend=backend)  # 新增代码+GenericLaunchBackendMaturity：显式请求危险样本启动；如果没有这一行，危险拒绝没有被覆盖。
        self.assertEqual(report["decision"], "unsafe_generic_launch_plan_rejected")  # 新增代码+GenericLaunchBackendMaturity：断言危险计划被拒绝；如果没有这一行，拒绝原因可能不稳定。
        self.assertEqual(len(backend.launches), 0)  # 新增代码+GenericLaunchBackendMaturity：断言后端没有被调用；如果没有这一行，危险路径可能已经产生副作用。
        self.assertTrue(report["high_risk_refused"])  # 新增代码+GenericLaunchBackendMaturity：断言高风险标志上浮；如果没有这一行，终端无法解释为什么拒绝。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+GenericLaunchBackendMaturity：断言危险拒绝零桌面副作用；如果没有这一行，拒绝也可能触碰真实桌面。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，test_unsafe_plan_refuses_before_backend_call 到此结束；如果没有这个边界说明，读者不容易看出危险拒绝测试范围。

    def test_launched_process_is_registered_as_owned(self) -> None:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，验证启动结果登记为本 agent 自有资源；如果没有这个测试，cleanup 不能区分用户原有窗口和 agent 新启动窗口。
        module = self._backend_module()  # 新增代码+GenericLaunchBackendMaturity：读取通用启动后端模块；如果没有这一行，后续无法创建 registry。
        registry = module.Phase110OwnedProcessRegistry()  # 新增代码+GenericLaunchBackendMaturity：创建自有进程登记表；如果没有这一行，测试无法检查 owned process 记录。
        backend = module.Phase110RecordingGenericLaunchBackend(registry=registry)  # 新增代码+GenericLaunchBackendMaturity：把 registry 注入记录型后端；如果没有这一行，启动和登记无法关联。
        report = module.run_generic_launch_backend(module.phase110_contract_safe_phase108_report(), enable_real_launch=True, backend=backend)  # 新增代码+GenericLaunchBackendMaturity：执行授权记录启动；如果没有这一行，registry 没有新记录。
        self.assertTrue(report["process_started"])  # 新增代码+GenericLaunchBackendMaturity：断言记录型启动生成进程身份；如果没有这一行，后续窗口绑定没有 pid 基准。
        self.assertTrue(report["owned_process_registered"])  # 新增代码+GenericLaunchBackendMaturity：断言报告里标记已登记自有进程；如果没有这一行，矩阵无法读取登记结果。
        self.assertEqual(len(registry.owned_processes), 1)  # 新增代码+GenericLaunchBackendMaturity：断言 registry 正好登记一条；如果没有这一行，重复登记或漏登记无法发现。
        self.assertEqual(registry.owned_processes[0]["process_id"], report["process_id"])  # 新增代码+GenericLaunchBackendMaturity：断言登记 pid 与报告 pid 一致；如果没有这一行，清理可能针对错误进程。
        self.assertTrue(registry.owned_processes[0]["cleanup_registered"])  # 新增代码+GenericLaunchBackendMaturity：断言登记记录带 cleanup 责任；如果没有这一行，后续 stop/abort 不知道该清理什么。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，test_launched_process_is_registered_as_owned 到此结束；如果没有这个边界说明，读者不容易看出自有资源登记测试范围。

    def test_launch_failure_returns_structured_reason(self) -> None:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，验证后端失败返回结构化原因；如果没有这个测试，启动失败会变成难懂异常或沉默失败。
        module = self._backend_module()  # 新增代码+GenericLaunchBackendMaturity：读取通用启动后端模块；如果没有这一行，后续无法创建失败后端。
        backend = module.Phase110FailingGenericLaunchBackend("simulated_create_process_failure")  # 新增代码+GenericLaunchBackendMaturity：创建可预测失败后端；如果没有这一行，失败路径只能依赖真实系统异常。
        report = module.run_generic_launch_backend(module.phase110_contract_safe_phase108_report(), enable_real_launch=True, backend=backend)  # 新增代码+GenericLaunchBackendMaturity：执行授权但失败的启动；如果没有这一行，结构化失败没有证据。
        self.assertFalse(report["ok"])  # 新增代码+GenericLaunchBackendMaturity：断言失败报告不通过；如果没有这一行，失败可能被误判成功。
        self.assertEqual(report["decision"], "generic_launch_backend_failed")  # 新增代码+GenericLaunchBackendMaturity：断言失败决策稳定；如果没有这一行，调用方难以分类处理。
        self.assertEqual(report["failure_reason"], "simulated_create_process_failure")  # 新增代码+GenericLaunchBackendMaturity：断言失败原因可读；如果没有这一行，用户无法知道启动为何失败。
        self.assertFalse(report["process_started"])  # 新增代码+GenericLaunchBackendMaturity：断言失败时没有进程身份；如果没有这一行，清理可能误以为需要关闭进程。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，test_launch_failure_returns_structured_reason 到此结束；如果没有这个边界说明，读者不容易看出失败路径测试范围。

    def test_phase109_default_backend_is_phase110_generic_backend(self) -> None:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，验证 Phase109 默认后端升级为 Task 2 的通用后端；如果没有这个测试，新后端可能孤立存在没有接入候选链路。
        module = self._backend_module()  # 新增代码+GenericLaunchBackendMaturity：读取通用启动后端模块；如果没有这一行，后续无法比对后端类型。
        phase109 = importlib.import_module("learning_agent.computer_use.generic_real_launch_candidate")  # 新增代码+GenericLaunchBackendMaturity：加载 Phase109 候选模块；如果没有这一行，测试无法验证旧链路接入新后端。
        candidate = phase109.Phase109GenericRealLaunchCandidate()  # 新增代码+GenericLaunchBackendMaturity：创建默认 Phase109 候选器；如果没有这一行，默认后端升级无法被检查。
        self.assertIsInstance(candidate.launch_backend, module.Phase110RecordingGenericLaunchBackend)  # 新增代码+GenericLaunchBackendMaturity：断言默认后端是 Phase110 记录型通用后端；如果没有这一行，新后端可能不会被真实入口复用。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，test_phase109_default_backend_is_phase110_generic_backend 到此结束；如果没有这个边界说明，读者不容易看出 Phase109 接入测试范围。
# 新增代码+GenericLaunchBackendMaturity：类段结束，WindowsComputerUseGenericLaunchBackendMaturityTests 到此结束；如果没有这个边界说明，代码小白不容易看出 Task 2 测试集合已结束。

if __name__ == "__main__":  # 新增代码+GenericLaunchBackendMaturity：文件入口段开始，允许直接运行本测试文件；如果没有这一行，用户必须记住完整 unittest 命令。
    unittest.main()  # 新增代码+GenericLaunchBackendMaturity：启动 unittest；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+GenericLaunchBackendMaturity：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，代码小白不容易看出脚本入口范围。
