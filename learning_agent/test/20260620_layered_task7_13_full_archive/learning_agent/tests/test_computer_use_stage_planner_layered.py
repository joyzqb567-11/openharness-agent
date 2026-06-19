from learning_agent.computer_use_mcp_v2.windows_runtime.stage_planner import UniversalDesktopStagePlanner  # 新增代码+LayeredStagePlannerTest：导入通用阶段 planner；如果没有这行代码，测试无法覆盖 intent 接线后的计划质量。


def test_complex_text_task_produces_contract_stages() -> None:  # 新增代码+LayeredStagePlannerTest：函数段开始，验证复杂文本任务产生多阶段和分层契约；如果没有这段测试，阶段质量可能退化。
    plan = UniversalDesktopStagePlanner().plan("请使用本机文本编辑软件，新建文档，输入 hello everyone，并保存到桌面 result.txt。")  # 新增代码+LayeredStagePlannerTest：构造文本任务；如果没有这行代码，测试无输入。
    assert len(plan.stages) >= 5  # 新增代码+LayeredStagePlannerTest：确认复杂任务拆成多个阶段；如果没有这行断言，任务可能退回单动作。
    assert plan.layer_skill_metadata["intent_understanding"]["layer_name"] == "intent_understanding"  # 新增代码+LayeredStagePlannerTest：确认 intent skill 元数据进入计划；如果没有这行断言，分层 prompt 可能未接线。
    assert all(stage.input_contract for stage in plan.stages)  # 新增代码+LayeredStagePlannerTest：确认每个阶段有输入契约；如果没有这行断言，执行层不知道依赖什么事实。
    assert all(stage.output_contract for stage in plan.stages)  # 新增代码+LayeredStagePlannerTest：确认每个阶段有输出契约；如果没有这行断言，验证层缺期望输出。
    assert all(stage.batch_intent for stage in plan.stages)  # 新增代码+LayeredStagePlannerTest：确认每个阶段有批意图；如果没有这行断言，批执行仍只能猜。
    # 新增代码+LayeredStagePlannerTest：函数段结束，test_complex_text_task_produces_contract_stages 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_write_stages_have_target_ref_before_execution() -> None:  # 新增代码+LayeredStagePlannerTest：函数段开始，验证写阶段必须绑定 target_ref；如果没有这段测试，写动作可能落到旧窗口。
    plan = UniversalDesktopStagePlanner().plan("请使用本机绘图软件，绘制彩色人物并保存。")  # 新增代码+LayeredStagePlannerTest：构造绘图任务；如果没有这行代码，写阶段无输入。
    write_stages = [stage for stage in plan.stages if stage.stage_kind in {"perform_content_work", "commit_resource"}]  # 新增代码+LayeredStagePlannerTest：收集写入和保存阶段；如果没有这行代码，无法验证 target_ref。
    assert write_stages  # 新增代码+LayeredStagePlannerTest：确认确实存在写阶段；如果没有这行断言，后续 all 可能空通过。
    assert all(stage.target_ref for stage in write_stages)  # 新增代码+LayeredStagePlannerTest：确认写阶段都有目标引用；如果没有这行断言，批执行安全门禁会后移。
    # 新增代码+LayeredStagePlannerTest：函数段结束，test_write_stages_have_target_ref_before_execution 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_multi_app_stages_have_explicit_target_ownership() -> None:  # 新增代码+LayeredStagePlannerTest：函数段开始，验证多应用阶段目标所有权；如果没有这段测试，跨窗口任务会混目标。
    plan = UniversalDesktopStagePlanner().plan("请同时使用计算器和文本编辑软件，把 123+456 的结果写入新文档。")  # 新增代码+LayeredStagePlannerTest：构造多应用任务；如果没有这行代码，多目标无输入。
    target_refs = {stage.target_ref for stage in plan.stages if stage.stage_kind != "needs_user"}  # 新增代码+LayeredStagePlannerTest：收集阶段目标引用；如果没有这行代码，无法看多目标覆盖。
    assert {"target_1", "target_2"}.issubset(target_refs)  # 新增代码+LayeredStagePlannerTest：确认两个目标都被阶段使用；如果没有这行断言，目标所有权可能丢失。
    assert plan.task_kind == "multi_app"  # 新增代码+LayeredStagePlannerTest：确认多应用类型；如果没有这行断言，阶段模板可能错误。
    # 新增代码+LayeredStagePlannerTest：函数段结束，test_multi_app_stages_have_explicit_target_ownership 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_unknown_app_starts_with_capability_probing_and_needs_user() -> None:  # 新增代码+LayeredStagePlannerTest：函数段开始，验证未知应用先探测并停止；如果没有这段测试，未知软件可能被盲写。
    plan = UniversalDesktopStagePlanner().plan("请使用一个我没说名字的本地软件完成未知 GUI 操作。")  # 新增代码+LayeredStagePlannerTest：构造未知任务；如果没有这行代码，未知路径无输入。
    assert plan.stages[0].stage_kind == "prepare_target"  # 新增代码+LayeredStagePlannerTest：确认先准备目标；如果没有这行断言，未知任务没有目标边界。
    assert plan.stages[1].stage_kind == "probe_capabilities"  # 新增代码+LayeredStagePlannerTest：确认第二步探测能力；如果没有这行断言，未知任务可能直接写入。
    assert plan.stages[-1].stage_kind == "needs_user"  # 新增代码+LayeredStagePlannerTest：确认最终要求用户；如果没有这行断言，未知任务可能伪成功。
    # 新增代码+LayeredStagePlannerTest：函数段结束，test_unknown_app_starts_with_capability_probing_and_needs_user 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_fresh_resource_requirement_is_generic() -> None:  # 新增代码+LayeredStagePlannerTest：函数段开始，验证新资源要求不依赖软件名；如果没有这段测试，旧文件问题会继续按应用打补丁。
    plan = UniversalDesktopStagePlanner().plan("请使用任意可写本地应用，新建空白资源并输入 `hello` 后保存。")  # 新增代码+LayeredStagePlannerTest：构造通用可写任务；如果没有这行代码，新资源泛化无输入。
    prepare = next(stage for stage in plan.stages if stage.stage_kind == "prepare_target")  # 新增代码+LayeredStagePlannerTest：提取准备阶段；如果没有这行代码，无法读取契约。
    assert prepare.verifier.get("fresh_resource_required") is True  # 新增代码+LayeredStagePlannerTest：确认新资源要求在 verifier 中；如果没有这行断言，旧资源阻断缺输入。
    assert prepare.verification_contract.get("fresh_resource_required") is True  # 新增代码+LayeredStagePlannerTest：确认新资源要求也在 verification_contract 中；如果没有这行断言，新 verifier 可能读不到。
    # 新增代码+LayeredStagePlannerTest：函数段结束，test_fresh_resource_requirement_is_generic 到此结束；如果没有这个边界说明，用户不容易看出测试范围。
