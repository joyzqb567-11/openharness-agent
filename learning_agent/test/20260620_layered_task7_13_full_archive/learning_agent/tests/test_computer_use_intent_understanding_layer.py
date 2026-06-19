from learning_agent.computer_use_mcp_v2.windows_runtime.intent_understanding_layer import understand_desktop_intent  # 新增代码+IntentUnderstandingLayerTest：导入意图理解入口；如果没有这行代码，测试无法覆盖新 intent 层。


def test_text_editor_prompt_extracts_payload_artifact_and_fresh_resource() -> None:  # 新增代码+IntentUnderstandingLayerTest：函数段开始，验证文本任务提取正文和保存请求；如果没有这段测试，文本任务可能继续丢正文。
    result = understand_desktop_intent("请使用本机任意文本编辑软件，新建空白文档，输入 hello everyone，并保存到桌面 openharness-layered-text.txt。")  # 新增代码+IntentUnderstandingLayerTest：构造中文文本任务；如果没有这行代码，正向文本场景无输入。
    assert result.task_kind == "text_entry"  # 新增代码+IntentUnderstandingLayerTest：确认通用文本任务类型；如果没有这行断言，planner 可能走错阶段。
    assert result.content_payloads == ("hello everyone",)  # 新增代码+IntentUnderstandingLayerTest：确认正文被抽取；如果没有这行断言，批执行器可能输入空文本。
    assert result.artifact_requests[0]["filename"] == "openharness-layered-text.txt"  # 新增代码+IntentUnderstandingLayerTest：确认文件名被抽取；如果没有这行断言，保存阶段缺产物名。
    assert result.requires_fresh_resource is True  # 新增代码+IntentUnderstandingLayerTest：确认写入任务默认要求新资源；如果没有这行断言，旧窗口可能被接管。
    # 新增代码+IntentUnderstandingLayerTest：函数段结束，test_text_editor_prompt_extracts_payload_artifact_and_fresh_resource 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_drawing_prompt_extracts_drawing_kind() -> None:  # 新增代码+IntentUnderstandingLayerTest：函数段开始，验证绘图任务归类；如果没有这段测试，绘图可能变 unknown。
    result = understand_desktop_intent("请使用本机绘图软件，绘制奥特曼图片，并渲染完成颜色。")  # 新增代码+IntentUnderstandingLayerTest：构造绘图 prompt；如果没有这行代码，绘图场景无输入。
    assert result.task_kind == "drawing"  # 新增代码+IntentUnderstandingLayerTest：确认通用绘图任务；如果没有这行断言，画布阶段不会生成。
    assert "drawing_app" in result.target_app_hints  # 新增代码+IntentUnderstandingLayerTest：确认目标提示是通用绘图软件；如果没有这行断言，启动层缺目标候选。
    assert "canvas_changed_with_visual_structure" in result.success_criteria  # 新增代码+IntentUnderstandingLayerTest：确认视觉成功标准存在；如果没有这行断言，绘图可能只看动作事件。
    # 新增代码+IntentUnderstandingLayerTest：函数段结束，test_drawing_prompt_extracts_drawing_kind 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_navigation_prompt_extracts_navigation_kind() -> None:  # 新增代码+IntentUnderstandingLayerTest：函数段开始，验证浏览/搜索任务归类；如果没有这段测试，导航任务会靠浏览器名硬编码。
    result = understand_desktop_intent("请打开本机浏览器，搜索 OpenHarness computer use，并查看结果。")  # 新增代码+IntentUnderstandingLayerTest：构造导航 prompt；如果没有这行代码，导航场景无输入。
    assert result.task_kind == "navigation"  # 新增代码+IntentUnderstandingLayerTest：确认通用导航任务；如果没有这行断言，导航阶段不会生成。
    assert "navigation_result_visible" in result.success_criteria  # 新增代码+IntentUnderstandingLayerTest：确认导航成功标准存在；如果没有这行断言，搜索可能只提交不验证。
    # 新增代码+IntentUnderstandingLayerTest：函数段结束，test_navigation_prompt_extracts_navigation_kind 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_multi_app_prompt_declares_two_targets() -> None:  # 新增代码+IntentUnderstandingLayerTest：函数段开始，验证多应用任务目标拆分；如果没有这段测试，跨窗口任务可能共用 target_ref。
    result = understand_desktop_intent("请同时使用计算器和文本编辑软件，把 123+456 的结果写入新文档。")  # 新增代码+IntentUnderstandingLayerTest：构造多应用 prompt；如果没有这行代码，多目标场景无输入。
    assert result.task_kind == "multi_app"  # 新增代码+IntentUnderstandingLayerTest：确认多应用任务；如果没有这行断言，多目标阶段不会生成。
    assert [target["target_ref"] for target in result.required_targets] == ["target_1", "target_2"]  # 新增代码+IntentUnderstandingLayerTest：确认两个目标引用；如果没有这行断言，一对一窗口绑定无法保证。
    # 新增代码+IntentUnderstandingLayerTest：函数段结束，test_multi_app_prompt_declares_two_targets 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_unknown_app_prompt_requests_clarification() -> None:  # 新增代码+IntentUnderstandingLayerTest：函数段开始，验证未知应用不盲动；如果没有这段测试，未知 GUI 可能被误操作。
    result = understand_desktop_intent("请使用一个我没说名字的本地软件完成未知操作。")  # 新增代码+IntentUnderstandingLayerTest：构造未知 prompt；如果没有这行代码，未知路径无输入。
    assert result.task_kind == "unknown_gui"  # 新增代码+IntentUnderstandingLayerTest：确认保持未知任务；如果没有这行断言，系统可能伪造执行计划。
    assert result.needs_clarification is True  # 新增代码+IntentUnderstandingLayerTest：确认需要澄清；如果没有这行断言，未知任务不会停下来。
    # 新增代码+IntentUnderstandingLayerTest：函数段结束，test_unknown_app_prompt_requests_clarification 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_single_instance_without_existing_window_grant_requires_fresh_resource() -> None:  # 新增代码+IntentUnderstandingLayerTest：函数段开始，验证未授权旧窗口时仍要求新资源；如果没有这段测试，旧窗口可能被默认接管。
    result = understand_desktop_intent("请使用只能开一个窗口的软件，新建文档并输入 hello。")  # 新增代码+IntentUnderstandingLayerTest：构造单实例未授权 prompt；如果没有这行代码，未授权场景无输入。
    assert result.allows_existing_user_window is False  # 新增代码+IntentUnderstandingLayerTest：确认没有旧窗口授权；如果没有这行断言，单实例策略可能误放行。
    assert result.requires_fresh_resource is True  # 新增代码+IntentUnderstandingLayerTest：确认仍要求新资源；如果没有这行断言，旧资源可能被接管。
    # 新增代码+IntentUnderstandingLayerTest：函数段结束，test_single_instance_without_existing_window_grant_requires_fresh_resource 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_single_instance_with_explicit_grant_allows_existing_window() -> None:  # 新增代码+IntentUnderstandingLayerTest：函数段开始，验证显式授权旧窗口可表达；如果没有这段测试，微信等单实例应用无法安全处理。
    result = understand_desktop_intent("我授权使用已有窗口，请复用已有本地软件窗口输入 hello。")  # 新增代码+IntentUnderstandingLayerTest：构造显式授权 prompt；如果没有这行代码，授权场景无输入。
    assert result.allows_existing_user_window is True  # 新增代码+IntentUnderstandingLayerTest：确认已有窗口授权被识别；如果没有这行断言，用户授权无法进入 runtime。
    assert result.requires_fresh_resource is False  # 新增代码+IntentUnderstandingLayerTest：确认授权旧窗口后不强制新资源；如果没有这行断言，单实例任务会被过度阻断。
    # 新增代码+IntentUnderstandingLayerTest：函数段结束，test_single_instance_with_explicit_grant_allows_existing_window 到此结束；如果没有这个边界说明，用户不容易看出测试范围。
