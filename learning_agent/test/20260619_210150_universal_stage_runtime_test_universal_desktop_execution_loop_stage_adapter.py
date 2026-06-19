from learning_agent.computer_use_mcp_v2.windows_runtime.universal_desktop_execution_loop import UniversalDesktopExecutionLoopAdapter  # 新增代码+StageTaskAdapterTest：导入 full mode adapter；如果没有这行代码，测试无法验证生产入口是否接到阶段循环。


class FakeStageTaskLoop:  # 新增代码+StageTaskAdapterTest：类段开始，模拟阶段任务循环；如果没有这个类，测试会启动真实 Windows 应用。
    def __init__(self) -> None:  # 新增代码+StageTaskAdapterTest：函数段开始，初始化调用记录；如果没有这段函数，无法确认 adapter 是否传入 prompt 和 target_hint。
        self.calls: list[tuple[str, str]] = []  # 新增代码+StageTaskAdapterTest：保存调用参数；如果没有这行代码，接线测试只能看返回值不能看调用路径。
    # 新增代码+StageTaskAdapterTest：函数段结束，FakeStageTaskLoop.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def run_desktop_task(self, prompt: str, target_hint: str = "") -> dict:  # 新增代码+StageTaskAdapterTest：函数段开始，模拟阶段任务运行；如果没有这段函数，adapter 无法调用 fake。
        self.calls.append((prompt, target_hint))  # 新增代码+StageTaskAdapterTest：记录调用参数；如果没有这行代码，测试无法确认 target_app 被作为启动提示传入。
        return {"ok": True, "decision": "desktop_task_completed", "universal_stage_task_loop_used": True, "desktop_task_plan_created": True, "stage_count": 3, "completed_stage_count": 3, "desktop_task_completed": True, "desktop_task_incomplete": False, "stage_boundary_observation_used": True, "batch_execution_used": True, "primitive_action_count": 4, "low_level_event_count": 8, "owned_window_verified": True, "target_ref_one_to_one": True, "observation_frame_count": 4}  # 新增代码+StageTaskAdapterTest：返回完整阶段成功证据；如果没有这行代码，adapter 顶层字段无法被断言。
    # 新增代码+StageTaskAdapterTest：函数段结束，FakeStageTaskLoop.run_desktop_task 到此结束；如果没有这个边界说明，初学者不容易看出 fake 运行范围。


def test_adapter_routes_production_path_through_stage_task_loop() -> None:  # 新增代码+StageTaskAdapterTest：函数段开始，验证 adapter 优先走阶段循环；如果没有这个测试，生产入口可能悄悄退回 primitive loop。
    loop = FakeStageTaskLoop()  # 新增代码+StageTaskAdapterTest：创建 fake 阶段循环；如果没有这行代码，adapter 会使用真实依赖。
    report = UniversalDesktopExecutionLoopAdapter(stage_task_loop=loop).run_desktop_task("generic_editor", "请输入 hello everyone")  # 新增代码+StageTaskAdapterTest：运行 adapter；如果没有这行代码，无法获取接线结果。
    assert loop.calls == [("请输入 hello everyone", "generic_editor")]  # 新增代码+StageTaskAdapterTest：确认 target_app 作为 target_hint 传入；如果没有这行代码，真实启动提示可能丢失。
    assert report["stage_task_loop_primary"] is True  # 新增代码+StageTaskAdapterTest：确认阶段循环是主路径；如果没有这行代码，旧 loop 回退不可见。
    assert report["universal_stage_task_loop_used"] is True  # 新增代码+StageTaskAdapterTest：确认报告保留阶段循环证据；如果没有这行代码，acceptance controller 无法匹配新字段。
    assert report["desktop_task_completed"] is True  # 新增代码+StageTaskAdapterTest：确认桌面任务完成字段透传；如果没有这行代码，final gate 不能读取结构化完成状态。
    assert report["observe_plan_act_verify_loop"] is False  # 新增代码+StageTaskAdapterTest：确认没有把旧 primitive loop 当主路径；如果没有这行代码，慢观察问题可能复发。
    assert report["gui_action_count"] == 4  # 新增代码+StageTaskAdapterTest：确认旧 GUI 动作字段兼容；如果没有这行代码，desktop_task_runtime 可能认为没有 GUI 动作。
    assert report["low_level_event_count"] == 8  # 新增代码+StageTaskAdapterTest：确认低层事件字段兼容；如果没有这行代码，验收器可能认为没有真实输入规模。
    assert report["ok"] is True  # 新增代码+StageTaskAdapterTest：确认严格成功条件通过；如果没有这行代码，adapter 可能返回结构化成功但顶层失败。
# 新增代码+StageTaskAdapterTest：函数段结束，test_adapter_routes_production_path_through_stage_task_loop 到此结束；如果没有这个边界说明，初学者不容易看出测试范围。
