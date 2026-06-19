"""测试通用目标 session 的启动后 FreshTarget 绑定。"""  # 新增代码+FreshTargetPolicyTest：说明本文件验证 universal session 层的新旧窗口识别；如果没有这一行，读者不容易知道这是通用 Computer Use 场景。
from __future__ import annotations  # 新增代码+FreshTargetPolicyTest：启用延迟类型注解；如果没有这一行，测试里的类型标注可能受导入顺序影响。

from typing import Any  # 新增代码+FreshTargetPolicyTest：导入 Any 表示 fake provider 的动态返回；如果没有这一行，测试 helper 类型边界不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.generic_launch_backend import Phase110RecordingGenericLaunchBackend  # 新增代码+FreshTargetPolicyTest：导入记录型启动后端；如果没有这一行，测试可能误触碰真实桌面。
from learning_agent.computer_use_mcp_v2.windows_runtime.universal_target_session import Phase117OwnedWindowProbe, UniversalTargetSessionRuntime  # 新增代码+FreshTargetPolicyTest：导入被测 universal session runtime；如果没有这一行，测试无法覆盖真实绑定层。


class FakeInventoryProbe:  # 新增代码+FreshTargetPolicyTest：类段开始，提供可控窗口快照；如果没有这个类，测试会依赖用户真实桌面窗口。
    def __init__(self, windows: list[dict[str, Any]]) -> None:  # 新增代码+FreshTargetPolicyTest：函数段开始，保存窗口列表；如果没有这段函数，fake probe 没有状态。
        self.windows = [dict(window) for window in windows]  # 新增代码+FreshTargetPolicyTest：复制窗口避免外部修改污染测试；如果没有这一行，断言可能受共享对象影响。
        self.snapshots_requested = 0  # 新增代码+FreshTargetPolicyTest：统计 snapshot 调用次数；如果没有这一行，测试无法确认启动前后都观察过。
    # 新增代码+FreshTargetPolicyTest：函数段结束，FakeInventoryProbe.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def snapshot(self) -> dict[str, Any]:  # 新增代码+FreshTargetPolicyTest：函数段开始，返回 fake 窗口快照；如果没有这段函数，Phase117 probe 无法读取窗口。
        self.snapshots_requested += 1  # 新增代码+FreshTargetPolicyTest：记录一次快照读取；如果没有这一行，无法证明 prelaunch 和 postlaunch 都走了 inventory。
        return {"windows": [dict(window) for window in self.windows]}  # 新增代码+FreshTargetPolicyTest：返回窗口副本列表；如果没有这一行，调用方拿不到可比较窗口。
    # 新增代码+FreshTargetPolicyTest：函数段结束，FakeInventoryProbe.snapshot 到此结束；如果没有这个边界说明，读者不容易看出快照范围。
# 新增代码+FreshTargetPolicyTest：类段结束，FakeInventoryProbe 到此结束；如果没有这个边界说明，用户不容易看出 fake inventory 范围。


def _phase108_report(target: str = "notepad") -> dict[str, Any]:  # 新增代码+FreshTargetPolicyTest：函数段开始，构造安全的 Phase108 发现报告；如果没有这段函数，runtime 会依赖真实 resolver。
    return {  # 新增代码+FreshTargetPolicyTest：返回最小安全发现报告；如果没有这一行，启动后端没有输入。
        "passed": True,  # 新增代码+FreshTargetPolicyTest：声明发现阶段通过；如果没有这一行，session_ready 会被发现层拒绝。
        "canonical_target": target,  # 新增代码+FreshTargetPolicyTest：保存规范目标名；如果没有这一行，窗口绑定缺少目标提示。
        "best_candidate_executable": f"{target}.exe",  # 新增代码+FreshTargetPolicyTest：保存可执行名；如果没有这一行，记录型启动后端无法生成进程身份。
        "dynamic_discovery_used": True,  # 新增代码+FreshTargetPolicyTest：声明使用通用发现；如果没有这一行，通用性报告会缺证据。
        "launch_plan": {  # 新增代码+FreshTargetPolicyTest：提供安全启动计划；如果没有这一行，Phase110 后端会拒绝启动。
            "safe_to_launch": True,  # 新增代码+FreshTargetPolicyTest：声明目标可安全启动；如果没有这一行，后端安全复核会失败。
            "launch_verb": "Start-Process",  # 新增代码+FreshTargetPolicyTest：声明无 shell 启动 verb；如果没有这一行，argv 后端会认为计划不完整。
            "executable": f"{target}.exe",  # 新增代码+FreshTargetPolicyTest：声明启动可执行名；如果没有这一行，记录型后端无法登记自有进程。
            "arguments": [],  # 新增代码+FreshTargetPolicyTest：声明无额外参数；如果没有这一行，后端可能收到缺省类型。
            "changes_registry": False,  # 新增代码+FreshTargetPolicyTest：声明不改注册表；如果没有这一行，安全复核会拒绝。
            "changes_system_settings": False,  # 新增代码+FreshTargetPolicyTest：声明不改系统设置；如果没有这一行，安全复核会拒绝。
            "requires_admin": False,  # 新增代码+FreshTargetPolicyTest：声明不需要管理员；如果没有这一行，安全复核会拒绝。
            "uses_shell_string": False,  # 新增代码+FreshTargetPolicyTest：声明不使用 shell 字符串；如果没有这一行，安全复核会拒绝。
            "actions_expanded": False,  # 新增代码+FreshTargetPolicyTest：声明不扩张动作面；如果没有这一行，成熟矩阵会拒绝。
        },  # 新增代码+FreshTargetPolicyTest：结束启动计划；如果没有这一行，Python 语法不完整。
    }  # 新增代码+FreshTargetPolicyTest：结束发现报告；如果没有这一行，Python 语法不完整。
# 新增代码+FreshTargetPolicyTest：函数段结束，_phase108_report 到此结束；如果没有这个边界说明，用户不容易看出发现报告范围。


def _old_notepad_window() -> dict[str, Any]:  # 新增代码+FreshTargetPolicyTest：函数段开始，构造启动前已存在的 Notepad 窗口；如果没有这段函数，旧窗口拒绝场景没有样本。
    return {  # 新增代码+FreshTargetPolicyTest：返回旧窗口字典；如果没有这一行，测试没有窗口输入。
        "app_id": "notepad.exe",  # 新增代码+FreshTargetPolicyTest：声明应用身份；如果没有这一行，FreshTarget 无法匹配 notepad。
        "process_name": "notepad.exe",  # 新增代码+FreshTargetPolicyTest：声明窗口进程名；如果没有这一行，pid 绑定缺少进程线索。
        "pid": 11001,  # 新增代码+FreshTargetPolicyTest：使用记录型后端首次启动 pid；如果没有这一行，finder 无法按 pid 命中旧窗口。
        "window_process_id": 11001,  # 新增代码+FreshTargetPolicyTest：补充窗口 pid 字段；如果没有这一行，不同模块字段读取可能不一致。
        "hwnd": 22001,  # 新增代码+FreshTargetPolicyTest：保存窗口句柄；如果没有这一行，目标身份无法验证窗口。
        "window_id": "hwnd:22001",  # 新增代码+FreshTargetPolicyTest：保存协议窗口 id；如果没有这一行，启动前后身份键无法比较。
        "title_preview": "Old user note - Notepad",  # 新增代码+FreshTargetPolicyTest：保存旧窗口标题；如果没有这一行，报告看不出这是用户旧窗口。
        "title": "Old user note - Notepad",  # 新增代码+FreshTargetPolicyTest：保存完整标题；如果没有这一行，标题哈希无法稳定生成。
    }  # 新增代码+FreshTargetPolicyTest：结束窗口字典；如果没有这一行，Python 语法不完整。
# 新增代码+FreshTargetPolicyTest：函数段结束，_old_notepad_window 到此结束；如果没有这个边界说明，用户不容易看出旧窗口样本范围。


def test_real_target_session_rejects_window_that_existed_before_launch() -> None:  # 新增代码+FreshTargetPolicyTest：函数段开始，验证真实启动绑定层拒绝旧窗口；如果没有这段测试，预检漏网仍可能接管旧窗口。
    inventory = FakeInventoryProbe([_old_notepad_window()])  # 新增代码+FreshTargetPolicyTest：准备启动前后都可见的旧窗口；如果没有这一行，FreshTarget 没有旧窗口证据。
    window_probe = Phase117OwnedWindowProbe(inventory_probe=inventory, poll_attempts=1, poll_interval_seconds=0)  # 新增代码+FreshTargetPolicyTest：创建只轮询一次的窗口查找器；如果没有这一行，测试会等待真实 GUI。
    runtime = UniversalTargetSessionRuntime(resolver=lambda raw_target, candidates=None: _phase108_report(str(raw_target)), launch_backend=Phase110RecordingGenericLaunchBackend(), window_probe=window_probe, enable_real_launch=True)  # 新增代码+FreshTargetPolicyTest：装配记录型真实启动 runtime；如果没有这一行，测试无法走 _open_real_target_session。
    report = runtime.open_target_session("notepad")  # 新增代码+FreshTargetPolicyTest：执行通用目标 session 打开流程；如果没有这一行，绑定层策略不会运行。
    assert report["session_ready"] is False  # 新增代码+FreshTargetPolicyTest：确认旧窗口绑定让 session 失败；如果没有这一行，旧窗口可能进入动作阶段。
    assert report["fresh_target_decision"] == "post_launch_target_was_preexisting_requires_relaunch_or_user_grant"  # 新增代码+FreshTargetPolicyTest：确认失败原因是启动前已存在；如果没有这一行，失败可能来自无关身份错误。
    assert report["target_window_existed_before_launch"] is True  # 新增代码+FreshTargetPolicyTest：确认报告明确标出旧窗口；如果没有这一行，用户无法知道要关闭软件。
    assert report["low_level_event_count"] == 0  # 新增代码+FreshTargetPolicyTest：确认绑定拒绝零输入事件；如果没有这一行，安全拒绝可能已触碰桌面。
    assert inventory.snapshots_requested >= 2  # 新增代码+FreshTargetPolicyTest：确认启动前和启动后都读取了快照；如果没有这一行，二次门禁可能没有事实来源。
# 新增代码+FreshTargetPolicyTest：函数段结束，test_real_target_session_rejects_window_that_existed_before_launch 到此结束；如果没有这个边界说明，用户不容易看出旧窗口拒绝范围。


def test_real_target_session_adds_controlled_resource_to_argv_launch_plan() -> None:  # 新增代码+ControlledResourceLaunchTest：函数段开始，验证受控文档资源会进入通用启动 argv；如果没有这段测试，Notepad 仍可能裸启动并恢复旧标签页。
    inventory = FakeInventoryProbe([])  # 新增代码+ControlledResourceLaunchTest：准备空窗口快照；如果没有这一行，测试可能被旧窗口 FreshTarget 拒绝打断。
    backend = Phase110RecordingGenericLaunchBackend()  # 新增代码+ControlledResourceLaunchTest：使用记录型后端避免触碰真实桌面；如果没有这一行，单元测试会真的打开应用。
    window_probe = Phase117OwnedWindowProbe(inventory_probe=inventory, poll_attempts=1, poll_interval_seconds=0)  # 新增代码+ControlledResourceLaunchTest：创建窗口查找器；如果没有这一行，runtime 无法完成真实启动路径的窗口绑定。
    controlled_path = r"C:\Users\joyzq\Desktop\1.txt"  # 新增代码+ControlledResourceLaunchTest：定义本轮受控目标文件；如果没有这一行，测试无法确认 argv 是否带上用户文件名。
    runtime = UniversalTargetSessionRuntime(resolver=lambda raw_target, candidates=None: _phase108_report(str(raw_target)), launch_backend=backend, window_probe=window_probe, enable_real_launch=True)  # 新增代码+ControlledResourceLaunchTest：装配被测 runtime；如果没有这一行，测试不会走 _open_real_target_session 和 Phase110。
    report = runtime.open_target_session("notepad", controlled_resource_path=controlled_path)  # 新增代码+ControlledResourceLaunchTest：打开 Notepad 并要求绑定桌面 1.txt；如果没有这一行，受控资源参数不会进入启动链路。
    assert backend.launches[0]["argv"] == ["notepad.exe", controlled_path]  # 新增代码+ControlledResourceLaunchTest：确认最终后端 argv 使用 Notepad 打开目标文件；如果没有这一行，裸启动回归不会被发现。
    assert report["launch_result"]["request"]["launch_plan"]["arguments"] == [controlled_path]  # 新增代码+ControlledResourceLaunchTest：确认 session 报告保留受控资源参数；如果没有这一行，验收日志无法解释为什么打开的是 1.txt。
    assert report["controlled_resource_path"] == controlled_path  # 新增代码+ControlledResourceLaunchTest：确认顶层报告回显受控资源；如果没有这一行，controller 无法把结果写入审计。
# 新增代码+ControlledResourceLaunchTest：函数段结束，test_real_target_session_adds_controlled_resource_to_argv_launch_plan 到此结束；如果没有这个边界说明，用户不容易看出 runtime 受控资源范围。
