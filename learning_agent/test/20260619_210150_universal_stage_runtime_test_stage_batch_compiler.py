import inspect  # 新增代码+StageBatchCompilerTest：导入源码检查工具；如果没有这行代码，测试无法防止编译器出现应用名特判。

import pytest  # 新增代码+StageBatchCompilerTest：导入 pytest 用于异常断言；如果没有这行代码，安全拒绝路径无法测试。

from learning_agent.computer_use_mcp_v2.windows_runtime.capability_profile import AppCapabilityProfile  # 新增代码+StageBatchCompilerTest：导入能力画像模型；如果没有这行代码，测试无法构造能力输入。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_batch_compiler import compile_stage_to_batch  # 新增代码+StageBatchCompilerTest：导入阶段批编译入口；如果没有这行代码，测试无法验证编译层。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import StagePlan  # 新增代码+StageBatchCompilerTest：导入阶段计划模型；如果没有这行代码，测试无法构造阶段。


def test_text_stage_compiles_focus_and_type_batch() -> None:  # 新增代码+StageBatchCompilerTest：函数段开始，验证文本阶段编译成文本批；如果没有这个测试，文本任务仍会逐步工具循环。
    stage = StagePlan(stage_id="stage_text", stage_kind="perform_content_work", target_ref="target-a", observation_policy="before_and_after_stage", verifier={"requested_text": "hello everyone"})  # 新增代码+StageBatchCompilerTest：构造文本写入阶段；如果没有这行代码，编译器没有阶段输入。
    profile = AppCapabilityProfile(has_text_input=True)  # 新增代码+StageBatchCompilerTest：构造文本能力画像；如果没有这行代码，编译器不会选择文本批。
    batch = compile_stage_to_batch(stage, {}, profile)  # 新增代码+StageBatchCompilerTest：执行编译；如果没有这行代码，无法断言批结果。
    assert batch.batch_kind == "text_entry_batch"  # 新增代码+StageBatchCompilerTest：确认批类型是文本输入；如果没有这行代码，执行器无法按批统计。
    assert [action["type"] for action in batch.actions] == ["focus_window", "type_text"]  # 新增代码+StageBatchCompilerTest：确认包含聚焦和输入；如果没有这行代码，文本可能打到错误焦点。


def test_drawing_stage_compiles_multiple_pointer_paths() -> None:  # 新增代码+StageBatchCompilerTest：函数段开始，验证绘图阶段编译成多路径批；如果没有这个测试，复杂绘图可能只画一条线。
    stage = StagePlan(stage_id="stage_draw", stage_kind="perform_content_work", target_ref="target-a", observation_policy="before_and_after_stage")  # 新增代码+StageBatchCompilerTest：构造绘图阶段；如果没有这行代码，编译器没有绘图输入。
    profile = AppCapabilityProfile(has_canvas_like_region=True)  # 新增代码+StageBatchCompilerTest：构造画布能力画像；如果没有这行代码，编译器不会选择指针路径。
    batch = compile_stage_to_batch(stage, {"target_window": {"rect": {"width": 800, "height": 500}}}, profile)  # 新增代码+StageBatchCompilerTest：执行绘图编译并提供窗口尺寸；如果没有这行代码，路径无法按画布估算。
    assert batch.batch_kind == "pointer_path_batch"  # 新增代码+StageBatchCompilerTest：确认批类型是指针路径；如果没有这行代码，绘图执行无法批量统计。
    assert sum(1 for action in batch.actions if action["type"] == "drag_path") >= 3  # 新增代码+StageBatchCompilerTest：确认多条拖拽路径；如果没有这行代码，单线条失败会复发。


def test_commit_stage_compiles_generic_save_batch() -> None:  # 新增代码+StageBatchCompilerTest：函数段开始，验证保存阶段编译成通用保存批；如果没有这个测试，保存可能走脚本捷径。
    stage = StagePlan(stage_id="stage_save", stage_kind="commit_resource", target_ref="target-a", observation_policy="before_and_after_stage")  # 新增代码+StageBatchCompilerTest：构造保存阶段；如果没有这行代码，编译器没有提交资源输入。
    batch = compile_stage_to_batch(stage, {}, AppCapabilityProfile(supports_keyboard_shortcuts_likely=True))  # 新增代码+StageBatchCompilerTest：执行保存编译；如果没有这行代码，无法断言保存动作。
    assert batch.batch_kind == "file_save_batch"  # 新增代码+StageBatchCompilerTest：确认批类型是文件保存；如果没有这行代码，验收无法区分保存阶段。
    assert any(action["type"] == "hotkey" for action in batch.actions)  # 新增代码+StageBatchCompilerTest：确认批内使用应用内快捷键；如果没有这行代码，可能退回文件系统直写。


def test_write_stage_without_target_ref_is_refused() -> None:  # 新增代码+StageBatchCompilerTest：函数段开始，验证写阶段必须有 target_ref；如果没有这个测试，写入可能落到当前焦点窗口。
    stage = StagePlan(stage_id="stage_bad", stage_kind="perform_content_work", target_ref="", observation_policy="before_and_after_stage")  # 新增代码+StageBatchCompilerTest：构造缺目标写阶段；如果没有这行代码，安全拒绝路径无法触发。
    with pytest.raises(ValueError, match="target_ref"):  # 新增代码+StageBatchCompilerTest：期待编译器或模型抛出 target_ref 错误；如果没有这行代码，测试不会检查安全门禁。
        compile_stage_to_batch(stage, {}, AppCapabilityProfile(has_text_input=True))  # 新增代码+StageBatchCompilerTest：尝试编译危险写阶段；如果没有这行代码，异常不会发生。


def test_compiler_source_has_no_specific_application_names() -> None:  # 新增代码+StageBatchCompilerTest：函数段开始，防止编译器出现单软件分支；如果没有这个测试，架构可能悄悄偏回专项修复。
    source = inspect.getsource(compile_stage_to_batch).lower()  # 新增代码+StageBatchCompilerTest：读取编译函数源码；如果没有这行代码，无法检查硬编码应用名。
    assert "notepad" not in source and "mspaint" not in source and "paint" not in source  # 新增代码+StageBatchCompilerTest：确认没有常见专项应用名；如果没有这行代码，通用设计边界无法自动保护。
