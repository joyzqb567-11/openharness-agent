from learning_agent.computer_use_mcp_v2.windows_runtime.stage_planner import UniversalDesktopStagePlanner  # 新增代码+UniversalStagePlannerTest：导入通用阶段规划器；如果没有这行代码，测试无法验证 prompt 到阶段计划。


def _stage_kinds(prompt: str) -> list[str]:  # 新增代码+UniversalStagePlannerTest：函数段开始，提取规划结果里的阶段类型；如果没有这段函数，多个测试会重复遍历。
    plan = UniversalDesktopStagePlanner().plan(prompt)  # 新增代码+UniversalStagePlannerTest：生成通用阶段计划；如果没有这行代码，辅助函数没有事实来源。
    return [stage.stage_kind for stage in plan.stages]  # 新增代码+UniversalStagePlannerTest：返回阶段类型列表；如果没有这行代码，断言无法比较阶段顺序。
# 新增代码+UniversalStagePlannerTest：函数段结束，_stage_kinds 到此结束；如果没有这个边界说明，初学者不容易看出辅助范围。


def test_text_task_uses_generic_stage_sequence() -> None:  # 新增代码+UniversalStagePlannerTest：函数段开始，验证文本任务不靠具体软件名规划；如果没有这个测试，文本任务可能回到 Notepad 特判。
    plan = UniversalDesktopStagePlanner().plan("请使用本机任意可用文本编辑软件，输入 hello everyone，并保存到桌面。")  # 新增代码+UniversalStagePlannerTest：生成文本任务计划；如果没有这行代码，测试没有输入样本。
    prepare_stage = next(stage for stage in plan.stages if stage.stage_kind == "prepare_target")  # 新增代码+FreshResourceTest：提取准备阶段；如果没有这行代码，测试无法验证新资源要求进入 planner。
    perform_stage = next(stage for stage in plan.stages if stage.stage_kind == "perform_content_work")  # 新增代码+UniversalStagePlannerTest：提取执行内容阶段；如果没有这行代码，无法确认正文是否进入阶段协议。
    assert plan.task_kind == "text_entry"  # 新增代码+UniversalStagePlannerTest：确认任务类型是通用文本输入；如果没有这行代码，应用名控制器可能混入。
    assert prepare_stage.verifier["fresh_resource_required"] is True  # 新增代码+FreshResourceTest：确认文本写入目标要求新资源；如果没有这行代码，新窗口恢复旧文件时执行层不知道要先新建。
    assert perform_stage.verifier["requested_text"] == "hello everyone"  # 新增代码+UniversalStagePlannerTest：确认用户要输入的正文被抽取；如果没有这行代码，批执行器可能输入 sample text。
    assert [stage.stage_kind for stage in plan.stages] == ["prepare_target", "probe_capabilities", "perform_content_work", "commit_resource", "verify_result"]  # 新增代码+UniversalStagePlannerTest：确认通用阶段完整；如果没有这行代码，保存或验证阶段可能缺失。
    assert all("notepad" not in stage.stage_kind.lower() for stage in plan.stages)  # 新增代码+UniversalStagePlannerTest：确认阶段名不含具体软件；如果没有这行代码，架构可能退回专项路线。


def test_text_payload_extraction_ignores_later_file_write_instruction() -> None:  # 新增代码+TextPayloadTest：函数段开始，验证正文抽取不会被后续 direct file write 干扰；如果没有这个测试，Stage 批会输入错误字符。
    prompt = "Use any text editor GUI. Open a new editable window, type exactly: hello everyone. Save the file through the application's graphical interface, not via command line or direct file write)."  # 新增代码+TextPayloadTest：构造真实验收里模型会改写出的英文任务；如果没有这行代码，无法复现 requested_text 被抽成右括号的问题。
    plan = UniversalDesktopStagePlanner().plan(prompt)  # 新增代码+TextPayloadTest：生成通用阶段计划；如果没有这行代码，测试没有 planner 输出。
    perform_stage = next(stage for stage in plan.stages if stage.stage_kind == "perform_content_work")  # 新增代码+TextPayloadTest：提取内容执行阶段；如果没有这行代码，无法读取 requested_text。
    assert perform_stage.verifier["requested_text"] == "hello everyone"  # 新增代码+TextPayloadTest：确认正文是用户要输入的文本；如果没有这行代码，后续批执行可能只输入符号或说明文字。
# 新增代码+TextPayloadTest：函数段结束，test_text_payload_extraction_ignores_later_file_write_instruction 到此结束；如果没有这个边界说明，初学者不容易看出测试范围。


def test_drawing_task_uses_same_generic_stage_sequence() -> None:  # 新增代码+UniversalStagePlannerTest：函数段开始，验证绘图任务也走同一通用阶段；如果没有这个测试，绘图容易变成 Paint 专项。
    kinds = _stage_kinds("请使用本机绘图软件，绘制一个彩色人物，并保存图片。")  # 新增代码+UniversalStagePlannerTest：生成绘图任务阶段；如果没有这行代码，测试没有绘图样本。
    assert kinds == ["prepare_target", "probe_capabilities", "perform_content_work", "commit_resource", "verify_result"]  # 新增代码+UniversalStagePlannerTest：确认绘图阶段不缺保存和验证；如果没有这行代码，复杂绘图会早停。


def test_drawing_task_prepare_stage_requires_fresh_resource() -> None:  # 新增代码+FreshResourceTest：函数段开始，验证绘图任务也要求新资源；如果没有这个测试，绘图可能覆盖旧画布或旧文件。
    plan = UniversalDesktopStagePlanner().plan("请使用本机绘图软件，绘制一个彩色人物，并保存图片。")  # 新增代码+FreshResourceTest：生成绘图任务计划；如果没有这行代码，测试没有阶段输入。
    prepare_stage = next(stage for stage in plan.stages if stage.stage_kind == "prepare_target")  # 新增代码+FreshResourceTest：提取准备阶段；如果没有这行代码，无法读取 verifier。
    assert prepare_stage.verifier["fresh_resource_required"] is True  # 新增代码+FreshResourceTest：确认绘图输出也绑定新资源；如果没有这行代码，恢复的旧图像窗口会被继续使用。
# 新增代码+FreshResourceTest：函数段结束，test_drawing_task_prepare_stage_requires_fresh_resource 到此结束；如果没有这个边界说明，初学者不容易看出测试范围。


def test_navigation_task_is_generic_not_browser_controller() -> None:  # 新增代码+UniversalStagePlannerTest：函数段开始，验证导航任务不是浏览器专项控制器；如果没有这个测试，浏览任务可能硬编码某浏览器。
    plan = UniversalDesktopStagePlanner().plan("请打开本机浏览器，搜索 OpenHarness computer use，并查看结果。")  # 新增代码+UniversalStagePlannerTest：生成导航任务计划；如果没有这行代码，测试没有导航样本。
    assert plan.task_kind == "navigation"  # 新增代码+UniversalStagePlannerTest：确认任务类型是通用导航；如果没有这行代码，任务可能变成 app-specific controller。
    assert "browser_controller" not in " ".join(stage.stage_kind for stage in plan.stages)  # 新增代码+UniversalStagePlannerTest：确认没有浏览器控制器阶段名；如果没有这行代码，专项路线可能混入。


def test_multi_app_task_declares_multiple_targets_and_one_ref_per_write_stage() -> None:  # 新增代码+UniversalStagePlannerTest：函数段开始，验证多窗口任务目标分离；如果没有这个测试，多应用写入可能混到一个窗口。
    plan = UniversalDesktopStagePlanner().plan("请同时使用一个文本窗口和一个浏览窗口，把浏览到的标题整理到文本窗口。")  # 新增代码+UniversalStagePlannerTest：生成多窗口任务计划；如果没有这行代码，测试没有多目标样本。
    destination_prepare = next(stage for stage in plan.stages if stage.stage_id == "stage_003_prepare_destination")  # 新增代码+FreshResourceTest：提取写入目标准备阶段；如果没有这行代码，多窗口新资源要求无法断言。
    write_target_refs = [stage.target_ref for stage in plan.stages if stage.stage_kind == "perform_content_work"]  # 新增代码+UniversalStagePlannerTest：提取写入阶段目标；如果没有这行代码，无法验证一对一窗口绑定。
    assert plan.task_kind == "multi_app"  # 新增代码+UniversalStagePlannerTest：确认任务类型是多应用；如果没有这行代码，多目标可能被压成单目标。
    assert len(plan.targets) >= 2  # 新增代码+UniversalStagePlannerTest：确认至少两个目标描述；如果没有这行代码，多窗口需求无法表达。
    assert len(write_target_refs) == len(set(write_target_refs))  # 新增代码+UniversalStagePlannerTest：确认写阶段不共享同一个 target_ref；如果没有这行代码，写入可能打到错误窗口。
    assert destination_prepare.verifier["fresh_resource_required"] is True  # 新增代码+FreshResourceTest：确认多窗口目的窗口要求新资源；如果没有这行代码，整理内容可能写进已有文件。


def test_unknown_gui_task_ends_with_probe_or_needs_user() -> None:  # 新增代码+UniversalStagePlannerTest：函数段开始，验证未知软件不伪造成功计划；如果没有这个测试，未知 GUI 可能被盲执行。
    plan = UniversalDesktopStagePlanner().plan("请使用一个我没说名字的本地软件完成一个未知 GUI 操作。")  # 新增代码+UniversalStagePlannerTest：生成未知任务计划；如果没有这行代码，未知路径无法覆盖。
    assert plan.task_kind == "unknown_gui"  # 新增代码+UniversalStagePlannerTest：确认未知任务保持未知；如果没有这行代码，planner 可能错误归类。
    assert plan.stages[-1].stage_kind in {"probe_capabilities", "needs_user"}  # 新增代码+UniversalStagePlannerTest：确认末端是探测或请求用户；如果没有这行代码，未知任务可能伪造完成。
