"""Task 3 的目标身份绑定成熟度测试。"""  # 新增代码+TargetIdentityMaturity：说明本测试专门验收 pid、hwnd、标题摘要和目标漂移拦截；如果没有这一行，用户不容易看懂这个测试文件的学习目的。
from __future__ import annotations  # 新增代码+TargetIdentityMaturity：让类型注解延迟解析，避免导入顺序影响测试启动；如果没有这一行，老版本运行路径可能因为类型名提前解析而失败。

import importlib  # 新增代码+TargetIdentityMaturity：用于在测试里显式导入新模块，红灯阶段可以证明模块确实还不存在；如果没有这一行，测试不能验证 target_identity.py 的缺失。
import json  # 新增代码+TargetIdentityMaturity：用于把安全报告转成文本检查是否泄露原始路径；如果没有这一行，测试无法直观看到输出里有没有敏感路径。
import unittest  # 新增代码+TargetIdentityMaturity：提供 unittest 测试框架；如果没有这一行，当前项目的 python -m unittest 入口无法发现这些验收用例。


# 新增代码+TargetIdentityMaturity：类段落开始，TargetIdentityMaturityTest 用来覆盖蓝图 Task 3 的所有目标身份绑定要求；如果没有这个测试类，pid 到 hwnd 的绑定、路径脱敏和漂移拦截没有统一验收入口。
class TargetIdentityMaturityTest(unittest.TestCase):  # 新增代码+TargetIdentityMaturity：定义目标身份成熟度测试类；如果没有这一行，测试函数会缺少 unittest 组织边界。
    # 新增代码+TargetIdentityMaturity：函数段落开始，_identity_module 统一导入目标模块；如果没有这个 helper，每个测试都要重复导入逻辑，红灯原因也不够集中。
    def _identity_module(self):  # 新增代码+TargetIdentityMaturity：定义导入 target_identity 的 helper；如果没有这一行，测试不能复用同一个模块加载入口。
        return importlib.import_module("learning_agent.computer_use.target_identity")  # 新增代码+TargetIdentityMaturity：导入还未实现的目标身份模块；如果没有这一行，红灯阶段不能证明缺少的是 target_identity.py。
    # 新增代码+TargetIdentityMaturity：函数段落结束，_identity_module 到此结束；如果没有这个边界说明，用户不容易看出导入 helper 的范围。

    # 新增代码+TargetIdentityMaturity：函数段落开始，test_binds_pid_to_hwnd_and_hashes_process_path 验证进程和窗口能绑定且路径只保留哈希；如果没有这个测试，后续可能误操作同名窗口或泄露本机路径。
    def test_binds_pid_to_hwnd_and_hashes_process_path(self) -> None:  # 新增代码+TargetIdentityMaturity：定义 pid-hwnd 绑定与路径脱敏测试；如果没有这一行，蓝图中的前两项验收没有自动检查。
        module = self._identity_module()  # 新增代码+TargetIdentityMaturity：加载目标身份模块；如果没有这一行，测试不能调用待实现接口。
        raw_path = r"C:\Users\joyzq\AppData\Local\Obsidian\Obsidian.exe"  # 新增代码+TargetIdentityMaturity：准备一条带用户目录的真实风格路径；如果没有这一行，测试无法证明原始路径不会泄露。
        launch_result = {"process_id": 4242, "process_executable": "Obsidian.exe", "process_path": raw_path, "owned_process_registered": True}  # 新增代码+TargetIdentityMaturity：模拟本次 full 模式启动出来的自有进程；如果没有这一行，身份模块没有进程来源可以绑定。
        window = {"pid": 4242, "hwnd": 8801, "window_id": "hwnd:8801", "process_name": "Obsidian.exe", "process_path": raw_path, "title_preview": "Vault - Obsidian", "app_id": "Obsidian.exe"}  # 新增代码+TargetIdentityMaturity：模拟该进程创建出的可见窗口；如果没有这一行，身份模块无法把 pid 绑定到 hwnd。
        owned = module.build_owned_target_identity(launch_result, window)  # 新增代码+TargetIdentityMaturity：构建自有目标身份记录；如果没有这一行，测试无法检查最终身份绑定结果。
        self.assertEqual(4242, owned.process.process_id)  # 新增代码+TargetIdentityMaturity：确认进程 id 被准确记录；如果没有这一行，错误 pid 可能被误认为自有目标。
        self.assertEqual(8801, owned.window.hwnd)  # 新增代码+TargetIdentityMaturity：确认 hwnd 被准确记录；如果没有这一行，窗口句柄错绑不会被发现。
        self.assertEqual(4242, owned.window.window_process_id)  # 新增代码+TargetIdentityMaturity：确认窗口所属 pid 与启动 pid 一致；如果没有这一行，同标题窗口可能被误接管。
        self.assertTrue(owned.process_identity_verified)  # 新增代码+TargetIdentityMaturity：确认进程身份通过；如果没有这一行，未注册进程也可能进入后续动作。
        self.assertTrue(owned.window_identity_verified)  # 新增代码+TargetIdentityMaturity：确认窗口身份通过；如果没有这一行，窗口不属于该进程也可能被放行。
        self.assertTrue(owned.target_identity_verified)  # 新增代码+TargetIdentityMaturity：确认最终目标身份通过；如果没有这一行，full 模式没有最终放行信号。
        report_text = json.dumps(owned.to_report(), ensure_ascii=False, sort_keys=True)  # 新增代码+TargetIdentityMaturity：把报告转成字符串便于查找泄露；如果没有这一行，脱敏检查只能靠人工目测。
        self.assertNotIn(raw_path, report_text)  # 新增代码+TargetIdentityMaturity：确认原始本地路径不出现在报告里；如果没有这一行，隐私泄露可能没人发现。
        self.assertEqual(16, len(owned.process.process_path_sha256_16))  # 新增代码+TargetIdentityMaturity：确认进程路径哈希长度稳定；如果没有这一行，后续审计字段可能不可比对。
    # 新增代码+TargetIdentityMaturity：函数段落结束，test_binds_pid_to_hwnd_and_hashes_process_path 到此结束；如果没有这个边界说明，用户不容易定位该测试覆盖范围。

    # 新增代码+TargetIdentityMaturity：函数段落开始，test_window_title_is_summarized_not_stored_as_raw_identity_secret 验证窗口标题会摘要和哈希；如果没有这个测试，长标题或敏感标题可能原样进入身份记录。
    def test_window_title_is_summarized_not_stored_as_raw_identity_secret(self) -> None:  # 新增代码+TargetIdentityMaturity：定义标题摘要测试；如果没有这一行，蓝图中的窗口标题摘要要求没有自动检查。
        module = self._identity_module()  # 新增代码+TargetIdentityMaturity：加载目标身份模块；如果没有这一行，测试无法调用标题摘要逻辑。
        long_title = "Vault - Obsidian - " + ("very-private-note-name-" * 8)  # 新增代码+TargetIdentityMaturity：构造超长标题模拟真实笔记或文档标题；如果没有这一行，摘要逻辑不会被压力测试。
        launch_result = {"process_id": 4242, "process_executable": "Obsidian.exe", "owned_process_registered": True}  # 新增代码+TargetIdentityMaturity：准备自有启动进程；如果没有这一行，标题不能挂到可信进程上验证。
        window = {"pid": 4242, "hwnd": 8801, "window_id": "hwnd:8801", "process_name": "Obsidian.exe", "title_preview": long_title, "app_id": "Obsidian.exe"}  # 新增代码+TargetIdentityMaturity：准备带超长标题的窗口；如果没有这一行，摘要逻辑没有输入样本。
        owned = module.build_owned_target_identity(launch_result, window)  # 新增代码+TargetIdentityMaturity：生成目标身份记录；如果没有这一行，测试无法读取标题摘要字段。
        self.assertLessEqual(len(owned.window.title_preview), 80)  # 新增代码+TargetIdentityMaturity：确认可见标题摘要长度受控；如果没有这一行，长标题可能污染日志和上下文。
        self.assertNotEqual(long_title, owned.window.title_preview)  # 新增代码+TargetIdentityMaturity：确认长标题不会原样保存为身份字段；如果没有这一行，摘要逻辑可能只是名义存在。
        self.assertEqual(16, len(owned.window.title_sha256_16))  # 新增代码+TargetIdentityMaturity：确认标题哈希可用于稳定比对；如果没有这一行，漂移校验缺少安全比较依据。
    # 新增代码+TargetIdentityMaturity：函数段落结束，test_window_title_is_summarized_not_stored_as_raw_identity_secret 到此结束；如果没有这个边界说明，用户不容易区分标题测试和 pid 绑定测试。

    # 新增代码+TargetIdentityMaturity：函数段落开始，test_target_drift_blocks_action 验证目标漂移会阻断后续动作；如果没有这个测试，窗口切换后 agent 可能继续点错地方。
    def test_target_drift_blocks_action(self) -> None:  # 新增代码+TargetIdentityMaturity：定义目标漂移拦截测试；如果没有这一行，蓝图中的 target drift blocks action 没有自动检查。
        module = self._identity_module()  # 新增代码+TargetIdentityMaturity：加载目标身份模块；如果没有这一行，测试无法调用漂移校验接口。
        launch_result = {"process_id": 4242, "process_executable": "Obsidian.exe", "owned_process_registered": True}  # 新增代码+TargetIdentityMaturity：准备原始自有进程；如果没有这一行，漂移校验没有基准。
        original_window = {"pid": 4242, "hwnd": 8801, "window_id": "hwnd:8801", "process_name": "Obsidian.exe", "title_preview": "Vault - Obsidian", "app_id": "Obsidian.exe"}  # 新增代码+TargetIdentityMaturity：准备原始可信窗口；如果没有这一行，漂移校验无法建立目标身份。
        drifted_window = {"pid": 4242, "hwnd": 9901, "window_id": "hwnd:9901", "process_name": "Obsidian.exe", "title_preview": "Vault - Obsidian", "app_id": "Obsidian.exe"}  # 新增代码+TargetIdentityMaturity：准备同进程但不同 hwnd 的漂移窗口；如果没有这一行，句柄漂移不会被覆盖。
        owned = module.build_owned_target_identity(launch_result, original_window)  # 新增代码+TargetIdentityMaturity：生成原始自有目标身份；如果没有这一行，漂移验证没有 expected 对象。
        verification = module.verify_owned_target_identity(owned, drifted_window)  # 新增代码+TargetIdentityMaturity：用当前窗口验证是否仍是原目标；如果没有这一行，漂移拦截不会被触发。
        self.assertFalse(verification.allowed)  # 新增代码+TargetIdentityMaturity：确认漂移后动作不允许继续；如果没有这一行，漂移窗口可能被误放行。
        self.assertTrue(verification.target_drift_blocks_action)  # 新增代码+TargetIdentityMaturity：确认报告里明确写出漂移阻断；如果没有这一行，用户无法知道为什么被拦截。
        self.assertEqual("target_drift_blocks_action", verification.decision)  # 新增代码+TargetIdentityMaturity：确认决策 token 稳定；如果没有这一行，终端验收和上层策略不容易解析。
    # 新增代码+TargetIdentityMaturity：函数段落结束，test_target_drift_blocks_action 到此结束；如果没有这个边界说明，用户不容易看出漂移拦截测试范围。

    # 新增代码+TargetIdentityMaturity：函数段落开始，test_same_title_from_different_pid_is_not_accepted 验证同标题不同 pid 不能冒充目标；如果没有这个测试，同名窗口会成为误操作风险。
    def test_same_title_from_different_pid_is_not_accepted(self) -> None:  # 新增代码+TargetIdentityMaturity：定义同标题不同进程拒绝测试；如果没有这一行，蓝图中的同标题防混淆没有自动检查。
        module = self._identity_module()  # 新增代码+TargetIdentityMaturity：加载目标身份模块；如果没有这一行，测试无法调用身份验证接口。
        launch_result = {"process_id": 4242, "process_executable": "Obsidian.exe", "owned_process_registered": True}  # 新增代码+TargetIdentityMaturity：准备自有进程基准；如果没有这一行，测试没有可信 pid。
        original_window = {"pid": 4242, "hwnd": 8801, "window_id": "hwnd:8801", "process_name": "Obsidian.exe", "title_preview": "Same Title", "app_id": "Obsidian.exe"}  # 新增代码+TargetIdentityMaturity：准备原始窗口标题；如果没有这一行，无法构造同标题对比。
        impostor_window = {"pid": 9999, "hwnd": 8802, "window_id": "hwnd:8802", "process_name": "Obsidian.exe", "title_preview": "Same Title", "app_id": "Obsidian.exe"}  # 新增代码+TargetIdentityMaturity：准备同标题但不同 pid 的冒充窗口；如果没有这一行，风险样本不存在。
        owned = module.build_owned_target_identity(launch_result, original_window)  # 新增代码+TargetIdentityMaturity：生成可信目标身份；如果没有这一行，冒充窗口没有 expected 对照。
        verification = module.verify_owned_target_identity(owned, impostor_window)  # 新增代码+TargetIdentityMaturity：验证冒充窗口是否被拒绝；如果没有这一行，安全逻辑不会被执行。
        self.assertFalse(verification.allowed)  # 新增代码+TargetIdentityMaturity：确认同标题不同 pid 不允许动作；如果没有这一行，同名窗口混淆可能被放过。
        self.assertTrue(verification.target_drift_blocks_action)  # 新增代码+TargetIdentityMaturity：确认拒绝被记录为漂移阻断；如果没有这一行，上层无法统一处理。
        self.assertEqual("target_drift_blocks_action", verification.decision)  # 新增代码+TargetIdentityMaturity：确认决策字段稳定；如果没有这一行，自动验收难以匹配原因。
    # 新增代码+TargetIdentityMaturity：函数段落结束，test_same_title_from_different_pid_is_not_accepted 到此结束；如果没有这个边界说明，用户不容易理解同标题风险的测试边界。

    # 新增代码+TargetIdentityMaturity：函数段落开始，test_user_preexisting_same_app_window_is_not_accepted_as_owned_target 验证用户本来开的同应用窗口不能被当成自有窗口；如果没有这个测试，full 模式可能接管用户已有工作窗口。
    def test_user_preexisting_same_app_window_is_not_accepted_as_owned_target(self) -> None:  # 新增代码+TargetIdentityMaturity：定义预先存在同应用窗口保护测试；如果没有这一行，蓝图中的用户已有窗口保护没有自动检查。
        module = self._identity_module()  # 新增代码+TargetIdentityMaturity：加载目标身份模块；如果没有这一行，测试无法调用构建接口。
        launch_result = {"process_id": 1111, "process_executable": "Obsidian.exe", "owned_process_registered": False}  # 新增代码+TargetIdentityMaturity：模拟不是本次 agent 注册启动的进程；如果没有这一行，无法证明未拥有的进程会被拒绝。
        preexisting_window = {"pid": 1111, "hwnd": 8801, "window_id": "hwnd:8801", "process_name": "Obsidian.exe", "title_preview": "User Vault - Obsidian", "app_id": "Obsidian.exe"}  # 新增代码+TargetIdentityMaturity：模拟用户早就打开的同应用窗口；如果没有这一行，保护用户窗口的路径没有样本。
        owned = module.build_owned_target_identity(launch_result, preexisting_window)  # 新增代码+TargetIdentityMaturity：尝试构建自有目标身份；如果没有这一行，测试不能证明未注册进程会被拒绝。
        self.assertFalse(owned.target_identity_verified)  # 新增代码+TargetIdentityMaturity：确认未拥有窗口不会被认定为目标；如果没有这一行，用户已有窗口可能被误接管。
        self.assertTrue(owned.user_preexisting_window_preserved)  # 新增代码+TargetIdentityMaturity：确认报告明确保护了用户已有窗口；如果没有这一行，拒绝原因不够可解释。
        self.assertEqual("owned_process_not_registered", owned.decision)  # 新增代码+TargetIdentityMaturity：确认未注册进程有稳定拒绝 token；如果没有这一行，上层无法给用户清楚提示。
    # 新增代码+TargetIdentityMaturity：函数段落结束，test_user_preexisting_same_app_window_is_not_accepted_as_owned_target 到此结束；如果没有这个边界说明，用户不容易看出用户窗口保护范围。

    # 新增代码+TargetIdentityMaturity：函数段落开始，test_windows_backend_emits_target_identity_fields_for_normalized_window 验证窗口 inventory 暴露身份候选字段；如果没有这个测试，后端可能没有足够信息做 pid-hwnd 绑定。
    def test_windows_backend_emits_target_identity_fields_for_normalized_window(self) -> None:  # 新增代码+TargetIdentityMaturity：定义 windows_backend 字段验收测试；如果没有这一行，蓝图中要求修改 windows_backend 的部分没有自动检查。
        windows_backend = importlib.import_module("learning_agent.computer_use.windows_backend")  # 新增代码+TargetIdentityMaturity：导入窗口 inventory 后端；如果没有这一行，测试无法检查规范化窗口字段。
        raw_path = r"C:\Users\joyzq\AppData\Local\Obsidian\Obsidian.exe"  # 新增代码+TargetIdentityMaturity：准备原始进程路径样本；如果没有这一行，测试无法确认后端没有泄露路径。
        raw_window = {"pid": 4242, "hwnd": 8801, "process_name": "Obsidian.exe", "process_path": raw_path, "title": "Vault - Obsidian", "rect": {"left": 1, "top": 2, "right": 901, "bottom": 602}}  # 新增代码+TargetIdentityMaturity：准备一条可归一化窗口记录；如果没有这一行，后端字段测试没有输入。
        record, reason = windows_backend.normalize_window_record(raw_window, "2026-06-05T00:00:00Z")  # 新增代码+TargetIdentityMaturity：调用窗口归一化函数；如果没有这一行，测试无法读取输出字段。
        self.assertEqual("", reason)  # 修改代码+TargetIdentityMaturity：沿用 windows_backend 现有约定，用空字符串表示窗口被接受；如果没有这一行，测试会把旧接口约定误当成 Task 3 缺陷。
        self.assertIsNotNone(record)  # 新增代码+TargetIdentityMaturity：确认归一化返回了记录；如果没有这一行，字段检查可能在空对象上崩溃。
        self.assertEqual(4242, record["window_process_id"])  # 新增代码+TargetIdentityMaturity：确认后端暴露窗口所属 pid；如果没有这一行，target_identity 无法绑定 pid。
        self.assertEqual(8801, record["hwnd"])  # 新增代码+TargetIdentityMaturity：确认后端暴露 hwnd；如果没有这一行，target_identity 无法绑定窗口句柄。
        self.assertTrue(record["target_identity_candidate"])  # 新增代码+TargetIdentityMaturity：确认该窗口可作为目标身份候选；如果没有这一行，上层不知道能不能进入身份校验。
        self.assertEqual(16, len(record["title_sha256_16"]))  # 新增代码+TargetIdentityMaturity：确认标题哈希进入 inventory；如果没有这一行，后续漂移校验缺少标题比对字段。
        self.assertNotIn(raw_path, json.dumps(record, ensure_ascii=False, sort_keys=True))  # 新增代码+TargetIdentityMaturity：确认后端记录不会泄露原始路径；如果没有这一行，隐私泄露可能进入模型上下文。
    # 新增代码+TargetIdentityMaturity：函数段落结束，test_windows_backend_emits_target_identity_fields_for_normalized_window 到此结束；如果没有这个边界说明，用户不容易看出后端字段测试范围。

    # 新增代码+TargetIdentityMaturity：函数段落开始，test_phase109_launch_candidate_emits_drift_block_field 验证上游候选报告暴露 target_drift_blocks_action 字段；如果没有这个测试，Task 3 接到 Phase109 的线不完整。
    def test_phase109_launch_candidate_emits_drift_block_field(self) -> None:  # 新增代码+TargetIdentityMaturity：定义 Phase109 接线字段测试；如果没有这一行，蓝图中的 wire into launch candidate 没有自动检查。
        phase109 = importlib.import_module("learning_agent.computer_use.generic_launch_backend")  # 新增代码+TargetIdentityMaturity：导入 Phase109 通用真实启动候选；如果没有这一行，测试无法验证上游报告字段。
        report = phase109.prepare_phase109_generic_real_launch_candidate(raw_target="Obsidian", candidates=[{"display_name": "Obsidian", "executable": "Obsidian.exe", "installed_app_verified": True}], enable_real_launch=True)  # 新增代码+TargetIdentityMaturity：运行记录型显式启动候选；如果没有这一行，target_drift_blocks_action 是否上浮不可见。
        self.assertIn("target_drift_blocks_action", report)  # 新增代码+TargetIdentityMaturity：确认顶层报告有漂移阻断字段；如果没有这一行，上层动作循环无法读取阻断状态。
        self.assertFalse(report["target_drift_blocks_action"])  # 新增代码+TargetIdentityMaturity：确认稳定目标不会误报漂移；如果没有这一行，正常路径可能被错误阻断。
    # 新增代码+TargetIdentityMaturity：函数段落结束，test_phase109_launch_candidate_emits_drift_block_field 到此结束；如果没有这个边界说明，用户不容易看出 Phase109 接线范围。
# 新增代码+TargetIdentityMaturity：类段落结束，TargetIdentityMaturityTest 到此结束；如果没有这个边界说明，用户不容易看出 Task 3 测试类的完整范围。


if __name__ == "__main__":  # 新增代码+TargetIdentityMaturity：允许直接运行本测试文件；如果没有这一行，用户双击或脚本方式运行时没有入口。
    unittest.main()  # 新增代码+TargetIdentityMaturity：启动 unittest 主程序；如果没有这一行，直接运行文件时不会执行测试。
