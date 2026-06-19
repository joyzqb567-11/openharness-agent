from learning_agent.computer_use_mcp_v2.windows_runtime.batch_executor import UniversalActionBatchExecutor  # 新增代码+LayeredBatchCompilerTest：导入批执行器；如果没有这行代码，测试无法验证事件上限在执行层生效。
from learning_agent.computer_use_mcp_v2.windows_runtime.capability_profile import AppCapabilityProfile  # 新增代码+LayeredBatchCompilerTest：导入能力画像；如果没有这行代码，测试无法模拟 ObservationFacts 生成的能力。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_batch_compiler import compile_stage_to_batch  # 新增代码+LayeredBatchCompilerTest：导入阶段批编译入口；如果没有这行代码，测试无法验证分层批编译。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import ActionBatch, StagePlan  # 新增代码+LayeredBatchCompilerTest：导入动作批和阶段计划模型；如果没有这行代码，测试无法构造通用输入。


class FakeLayeredTargetRuntime:  # 新增代码+LayeredBatchCompilerTest：类段开始，模拟稳定目标复核；如果没有这个类，测试可能碰到真实桌面窗口。
    def __init__(self, allowed: bool = True) -> None:  # 新增代码+LayeredBatchCompilerTest：函数段开始，配置目标是否允许动作；如果没有这段函数，测试无法切换安全状态。
        self.allowed = allowed  # 新增代码+LayeredBatchCompilerTest：保存目标复核结果；如果没有这行代码，执行器无法得到 fake 放行或拒绝。
    # 新增代码+LayeredBatchCompilerTest：函数段结束，FakeLayeredTargetRuntime.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake 初始化范围。

    def verify_before_action(self, session: dict, current_window: dict) -> dict:  # 新增代码+LayeredBatchCompilerTest：函数段开始，模拟批前目标身份复核；如果没有这段函数，执行器会走兼容缺 verifier 分支。
        return {"allowed": self.allowed, "target_identity_verified": self.allowed, "current_window": dict(current_window)}  # 新增代码+LayeredBatchCompilerTest：返回目标复核事实；如果没有这行代码，批执行器拿不到安全判断。
    # 新增代码+LayeredBatchCompilerTest：函数段结束，FakeLayeredTargetRuntime.verify_before_action 到此结束；如果没有这个边界说明，用户不容易看出目标复核范围。


class FakeHighEventActionRuntime:  # 新增代码+LayeredBatchCompilerTest：类段开始，模拟每个动作都会产生大量低层事件的动作层；如果没有这个类，事件超限无法稳定复现。
    def __init__(self) -> None:  # 新增代码+LayeredBatchCompilerTest：函数段开始，初始化 fake runtime；如果没有这段函数，测试无法统计已分发动作。
        self.target_runtime = FakeLayeredTargetRuntime()  # 新增代码+LayeredBatchCompilerTest：提供目标复核能力；如果没有这行代码，执行器无法走真实批前门禁。
        self.dispatched: list[dict] = []  # 新增代码+LayeredBatchCompilerTest：记录动作；如果没有这行代码，测试无法证明超限后剩余动作停止。
    # 新增代码+LayeredBatchCompilerTest：函数段结束，FakeHighEventActionRuntime.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake 依赖范围。

    def dispatch(self, session: dict, action: dict, current_window: dict | None = None) -> dict:  # 新增代码+LayeredBatchCompilerTest：函数段开始，模拟 primitive 执行；如果没有这段函数，批执行器没有动作出口。
        self.dispatched.append(dict(action))  # 新增代码+LayeredBatchCompilerTest：保存被执行动作；如果没有这行代码，无法断言超限截停位置。
        return {"ok": True, "decision": "fake_high_events", "low_level_event_count": 99, "current_window": dict(current_window or {})}  # 新增代码+LayeredBatchCompilerTest：返回高事件数成功；如果没有这行代码，执行器不会触发事件预算门禁。
    # 新增代码+LayeredBatchCompilerTest：函数段结束，FakeHighEventActionRuntime.dispatch 到此结束；如果没有这个边界说明，用户不容易看出 fake 执行范围。


def _perform_stage(target_ref: str = "target-a", verifier: dict | None = None) -> StagePlan:  # 新增代码+LayeredBatchCompilerTest：函数段开始，构造内容执行阶段；如果没有这段函数，测试会重复大量阶段样板。
    return StagePlan(stage_id="stage-perform", stage_kind="perform_content_work", target_ref=target_ref, observation_policy="before_and_after_stage", verifier=dict(verifier or {}))  # 新增代码+LayeredBatchCompilerTest：返回通用执行阶段；如果没有这行代码，编译器没有稳定输入。
# 新增代码+LayeredBatchCompilerTest：函数段结束，_perform_stage 到此结束；如果没有这个边界说明，用户不容易看出阶段构造范围。


def test_text_stage_compiles_from_observation_facts_into_one_text_batch() -> None:  # 新增代码+LayeredBatchCompilerTest：函数段开始，验证文本 facts 会生成单个文本批；如果没有这个测试，文本任务可能退回逐步 primitive 循环。
    facts = {"capability_profile": {"has_text_input": True, "supports_keyboard_shortcuts_likely": True, "evidence": ["facts:text_input"]}}  # 新增代码+LayeredBatchCompilerTest：构造结构化观察事实；如果没有这行代码，测试无法证明编译器不靠应用名。
    profile = AppCapabilityProfile(has_text_input=True, supports_keyboard_shortcuts_likely=True)  # 新增代码+LayeredBatchCompilerTest：构造从 facts 得到的能力画像；如果没有这行代码，编译器无法选择文本路径。
    batch = compile_stage_to_batch(_perform_stage(verifier={"requested_text": "hello everyone"}), facts, profile)  # 新增代码+LayeredBatchCompilerTest：编译文本阶段；如果没有这行代码，无法获得批结果。
    assert batch.batch_kind == "text_entry_batch"  # 新增代码+LayeredBatchCompilerTest：确认是文本输入批；如果没有这行代码，批执行路径可能错误。
    assert batch.target_ref == "target-a"  # 新增代码+LayeredBatchCompilerTest：确认写批绑定唯一 target_ref；如果没有这行代码，动作可能落到当前焦点窗口。
    assert [action["type"] for action in batch.actions] == ["focus_window", "type_text"]  # 新增代码+LayeredBatchCompilerTest：确认一次批内包含聚焦和输入；如果没有这行代码，任务仍会模型每步观察。
    assert batch.guardrails["max_low_level_events"] == 80  # 新增代码+LayeredBatchCompilerTest：确认文本批带事件预算；如果没有这行代码，执行层无法拒绝异常大批。


def test_canvas_stage_compiles_from_observation_facts_into_grouped_pointer_paths() -> None:  # 新增代码+LayeredBatchCompilerTest：函数段开始，验证画布 facts 会生成多路径批；如果没有这个测试，绘图任务可能只画一条线。
    facts = {"canvas_regions": [{"bounds": {"width": 900, "height": 600}}], "capability_profile": {"has_canvas_like_region": True, "supports_keyboard_shortcuts_likely": True}}  # 新增代码+LayeredBatchCompilerTest：构造画布观察事实；如果没有这行代码，路径无法按画布尺寸生成。
    profile = AppCapabilityProfile(has_canvas_like_region=True, supports_keyboard_shortcuts_likely=True)  # 新增代码+LayeredBatchCompilerTest：构造画布能力画像；如果没有这行代码，编译器不会选择指针批。
    batch = compile_stage_to_batch(_perform_stage(), facts, profile)  # 新增代码+LayeredBatchCompilerTest：编译绘图阶段；如果没有这行代码，无法断言批结果。
    drag_actions = [action for action in batch.actions if action.get("type") == "drag_path"]  # 新增代码+LayeredBatchCompilerTest：筛选拖拽路径动作；如果没有这行代码，测试无法统计画线规模。
    assert batch.batch_kind == "pointer_path_batch"  # 新增代码+LayeredBatchCompilerTest：确认是指针路径批；如果没有这行代码，绘图任务可能走文本批。
    assert batch.target_ref == "target-a"  # 新增代码+LayeredBatchCompilerTest：确认画布写批绑定唯一 target_ref；如果没有这行代码，多窗口绘图会不安全。
    assert len(drag_actions) >= 3  # 新增代码+LayeredBatchCompilerTest：确认生成多条路径；如果没有这行代码，复杂绘图规划仍会太小。
    assert batch.guardrails["max_low_level_events"] == 200  # 新增代码+LayeredBatchCompilerTest：确认指针批带事件预算；如果没有这行代码，拖拽异常无法截停。


def test_save_stage_compiles_into_bounded_commit_batch() -> None:  # 新增代码+LayeredBatchCompilerTest：函数段开始，验证保存阶段是有边界的提交批；如果没有这个测试，保存可能变成直接文件写入或无预算动作。
    stage = StagePlan(stage_id="stage-save", stage_kind="commit_resource", target_ref="target-a", observation_policy="before_and_after_stage")  # 新增代码+LayeredBatchCompilerTest：构造保存阶段；如果没有这行代码，编译器没有提交资源输入。
    profile = AppCapabilityProfile(has_file_save_surface=True, supports_keyboard_shortcuts_likely=True)  # 新增代码+LayeredBatchCompilerTest：构造保存能力画像；如果没有这行代码，保存批缺能力证据。
    batch = compile_stage_to_batch(stage, {"save_dialog_state": {"visible": False}}, profile)  # 新增代码+LayeredBatchCompilerTest：编译保存阶段；如果没有这行代码，无法检查保存批。
    assert batch.batch_kind == "file_save_batch"  # 新增代码+LayeredBatchCompilerTest：确认是文件保存批；如果没有这行代码，提交阶段无法区分。
    assert batch.target_ref == "target-a"  # 新增代码+LayeredBatchCompilerTest：确认保存批绑定唯一 target_ref；如果没有这行代码，Ctrl+S 可能发到错误窗口。
    assert batch.guardrails["no_direct_file_write"] is True  # 新增代码+LayeredBatchCompilerTest：确认保存必须通过应用界面；如果没有这行代码，脚本直写可能回归。
    assert batch.guardrails["max_low_level_events"] == 40  # 新增代码+LayeredBatchCompilerTest：确认保存批有低事件预算；如果没有这行代码，保存对话框异常会拖住任务。


def test_write_batches_require_exactly_one_target_ref() -> None:  # 新增代码+LayeredBatchCompilerTest：函数段开始，验证写批必须绑定一个 target_ref；如果没有这个测试，通用 Computer Use 会默认接管当前焦点。
    text_batch = compile_stage_to_batch(_perform_stage(), {}, AppCapabilityProfile(has_text_input=True))  # 新增代码+LayeredBatchCompilerTest：编译文本写批；如果没有这行代码，无法检查 target_ref。
    pointer_batch = compile_stage_to_batch(_perform_stage(), {"canvas_regions": [{"bounds": {"width": 800, "height": 500}}]}, AppCapabilityProfile(has_canvas_like_region=True))  # 新增代码+LayeredBatchCompilerTest：编译画布写批；如果没有这行代码，无法检查绘图 target_ref。
    save_batch = compile_stage_to_batch(StagePlan(stage_id="stage-save", stage_kind="commit_resource", target_ref="target-a"), {}, AppCapabilityProfile(has_file_save_surface=True))  # 新增代码+LayeredBatchCompilerTest：编译保存写批；如果没有这行代码，无法检查保存 target_ref。
    assert {text_batch.target_ref, pointer_batch.target_ref, save_batch.target_ref} == {"target-a"}  # 新增代码+LayeredBatchCompilerTest：确认所有写批只绑定同一个目标引用；如果没有这行代码，多目标写入可能混乱。


def test_executor_refuses_batches_above_configured_event_limits() -> None:  # 新增代码+LayeredBatchCompilerTest：函数段开始，验证执行器拒绝超出低层事件预算的批；如果没有这个测试，异常拖拽或输入会持续污染桌面。
    runtime = FakeHighEventActionRuntime()  # 新增代码+LayeredBatchCompilerTest：创建高事件 fake runtime；如果没有这行代码，事件超限无法触发。
    batch = ActionBatch(batch_id="batch-high", batch_kind="pointer_path_batch", target_ref="target-a", actions=({"type": "drag_path"}, {"type": "drag_path"}), guardrails={"stage_id": "stage-high", "max_low_level_events": 50})  # 新增代码+LayeredBatchCompilerTest：构造低预算批；如果没有这行代码，执行器没有超限条件。
    result = UniversalActionBatchExecutor(runtime).execute_batch({"target_ref": "target-a", "target_window": {"hwnd": 9}}, batch)  # 新增代码+LayeredBatchCompilerTest：执行高事件批；如果没有这行代码，无法读取拒绝结果。
    assert result.status == "blocked"  # 新增代码+LayeredBatchCompilerTest：确认超限是阻断而不是完成；如果没有这行代码，异常批可能被误判成功。
    assert result.evidence["decision"] == "batch_event_limit_exceeded"  # 新增代码+LayeredBatchCompilerTest：确认原因码可审计；如果没有这行代码，失败复盘不知道为什么停止。
    assert len(runtime.dispatched) == 1  # 新增代码+LayeredBatchCompilerTest：确认超限后没有继续执行第二个动作；如果没有这行代码，事件预算门禁可能只是记录不阻断。
