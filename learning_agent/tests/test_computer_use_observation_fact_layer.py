from learning_agent.computer_use_mcp_v2.windows_runtime.observation_fact_layer import build_observation_facts  # 新增代码+ObservationFactLayerTest：导入观察事实构建入口；如果没有这行代码，测试无法覆盖 observation layer。


def test_editable_text_region_is_extracted() -> None:  # 新增代码+ObservationFactLayerTest：函数段开始，验证可编辑区域提取；如果没有这段测试，文本批缺事实来源。
    facts = build_observation_facts({"target_ref": "target_1", "target_identity_verified": True, "uia_tree": [{"control_type": "Edit", "name": "content", "bounds": {"width": 500, "height": 200}}]})  # 新增代码+ObservationFactLayerTest：构造编辑控件观察；如果没有这行代码，测试无输入。
    assert facts.target_identity_verified is True  # 新增代码+ObservationFactLayerTest：确认目标身份事实保留；如果没有这行断言，批执行安全缺证据。
    assert facts.editable_regions[0]["region_kind"] == "editable"  # 新增代码+ObservationFactLayerTest：确认可编辑区域被提取；如果没有这行断言，文本任务无法定位。
    assert facts.capability_profile["has_text_input"] is True  # 新增代码+ObservationFactLayerTest：确认能力画像同步；如果没有这行断言，compiler 无法从 facts 编译文本批。
    # 新增代码+ObservationFactLayerTest：函数段结束，test_editable_text_region_is_extracted 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_canvas_like_region_is_extracted() -> None:  # 新增代码+ObservationFactLayerTest：函数段开始，验证画布区域提取；如果没有这段测试，绘图批缺事实来源。
    facts = build_observation_facts({"visual_regions": [{"role": "content", "bounds": {"width": 900, "height": 620}, "blank_ratio": 0.9}]})  # 新增代码+ObservationFactLayerTest：构造大空白视觉区域；如果没有这行代码，画布场景无输入。
    assert facts.canvas_regions[0]["region_kind"] == "canvas"  # 新增代码+ObservationFactLayerTest：确认画布区域被提取；如果没有这行断言，绘图阶段无法定位画布。
    assert facts.capability_profile["has_canvas_like_region"] is True  # 新增代码+ObservationFactLayerTest：确认画布能力为真；如果没有这行断言，绘图批不会生成。
    # 新增代码+ObservationFactLayerTest：函数段结束，test_canvas_like_region_is_extracted 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_menu_toolbar_save_and_modal_facts_are_extracted() -> None:  # 新增代码+ObservationFactLayerTest：函数段开始，验证菜单、工具栏、保存和弹窗事实；如果没有这段测试，复杂应用表面会被忽略。
    facts = build_observation_facts({"uia_elements": [{"control_type": "MenuBar", "name": "File"}, {"control_type": "ToolBar", "name": "Ribbon"}, {"control_type": "Dialog", "name": "Save As", "modal": True}, {"control_type": "Button", "name": "Save"}], "save_dialog_completed": True})  # 新增代码+ObservationFactLayerTest：构造多表面观察；如果没有这行代码，复合事实无输入。
    assert facts.menu_regions  # 新增代码+ObservationFactLayerTest：确认菜单区域存在；如果没有这行断言，菜单能力可能丢失。
    assert facts.toolbar_regions  # 新增代码+ObservationFactLayerTest：确认工具栏区域存在；如果没有这行断言，绘图工具表面可能丢失。
    assert facts.modal_dialogs  # 新增代码+ObservationFactLayerTest：确认模态对话框存在；如果没有这行断言，保存弹窗会被忽略。
    assert facts.save_dialog_state["completed"] is True  # 新增代码+ObservationFactLayerTest：确认保存完成状态；如果没有这行断言，保存 verifier 不能从 facts 通过。
    # 新增代码+ObservationFactLayerTest：函数段结束，test_menu_toolbar_save_and_modal_facts_are_extracted 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_target_drift_and_stale_user_window_are_represented() -> None:  # 新增代码+ObservationFactLayerTest：函数段开始，验证旧窗口/漂移事实不会丢；如果没有这段测试，FreshTarget 证据无法进入 facts。
    facts = build_observation_facts({"target_ref": "target_1", "target_window_existed_before_launch": True, "target_identity_verified": False})  # 新增代码+ObservationFactLayerTest：构造旧窗口观察；如果没有这行代码，旧窗口场景无输入。
    assert facts.target_window_freshness == "stale_user_owned_window"  # 新增代码+ObservationFactLayerTest：确认旧窗口新鲜度；如果没有这行断言，运行时可能默认接管旧窗口。
    assert facts.target_identity_verified is False  # 新增代码+ObservationFactLayerTest：确认身份未验证；如果没有这行断言，安全门禁可能误放行。
    # 新增代码+ObservationFactLayerTest：函数段结束，test_target_drift_and_stale_user_window_are_represented 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_fresh_agent_owned_window_is_represented() -> None:  # 新增代码+ObservationFactLayerTest：函数段开始，验证新 agent-owned 窗口事实；如果没有这段测试，新目标绑定证据可能丢失。
    facts = build_observation_facts({"target_ref": "target_1", "target_identity_verified": True, "fresh_agent_owned_window": True})  # 新增代码+ObservationFactLayerTest：构造新窗口观察；如果没有这行代码，新窗口场景无输入。
    assert facts.target_window_freshness == "fresh_agent_owned_window"  # 新增代码+ObservationFactLayerTest：确认新窗口新鲜度；如果没有这行断言，FreshTarget 成功不能被审计。
    assert facts.active_target_ref == "target_1"  # 新增代码+ObservationFactLayerTest：确认 active target_ref；如果没有这行断言，facts 不能绑定目标。
    # 新增代码+ObservationFactLayerTest：函数段结束，test_fresh_agent_owned_window_is_represented 到此结束；如果没有这个边界说明，用户不容易看出测试范围。
