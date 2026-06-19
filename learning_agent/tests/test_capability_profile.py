from learning_agent.computer_use_mcp_v2.windows_runtime.capability_profile import build_capability_profile  # 新增代码+CapabilityProfileTest：导入能力画像构建入口；如果没有这行代码，测试无法验证观察层到通用能力层的转换。


def test_editable_uia_control_sets_text_input_capability() -> None:  # 新增代码+CapabilityProfileTest：函数段开始，验证可编辑控件能识别为文本输入；如果没有这个测试，文本任务会退回应用特判。
    frame = {"uia_tree": [{"control_type": "Edit", "name": "content area", "bounds": {"width": 400, "height": 200}}]}  # 新增代码+CapabilityProfileTest：构造通用可编辑 UIA 节点；如果没有这行代码，画像没有观察输入。
    profile = build_capability_profile(frame)  # 新增代码+CapabilityProfileTest：生成能力画像；如果没有这行代码，无法断言结果。
    assert profile.has_text_input is True  # 新增代码+CapabilityProfileTest：确认文本能力为真；如果没有这行代码，文本阶段编译会缺依据。
    assert profile.unknown_capabilities is False  # 新增代码+CapabilityProfileTest：确认已识别能力后不再未知；如果没有这行代码，运行时可能误停等用户。


def test_large_visual_region_sets_canvas_capability() -> None:  # 新增代码+CapabilityProfileTest：函数段开始，验证大视觉区域能识别为画布类能力；如果没有这个测试，绘图任务会退回单软件逻辑。
    frame = {"visual_regions": [{"role": "content", "bounds": {"left": 30, "top": 40, "width": 900, "height": 620}, "blank_ratio": 0.91}]}  # 新增代码+CapabilityProfileTest：构造通用大空白区域；如果没有这行代码，画像无法识别画布候选。
    profile = build_capability_profile(frame)  # 新增代码+CapabilityProfileTest：生成能力画像；如果没有这行代码，无法读取能力。
    assert profile.has_canvas_like_region is True  # 新增代码+CapabilityProfileTest：确认画布能力为真；如果没有这行代码，绘图批无法生成。
    assert any("canvas" in item for item in profile.evidence)  # 新增代码+CapabilityProfileTest：确认短证据含画布来源；如果没有这行代码，失败时不可解释。


def test_navigation_surface_detected_from_generic_controls() -> None:  # 新增代码+CapabilityProfileTest：函数段开始，验证导航类控件组合；如果没有这个测试，浏览/搜索任务会靠应用名判断。
    frame = {"uia_elements": [{"control_type": "Edit", "name": "address search", "bounds": {"width": 500, "height": 32}}, {"control_type": "Button", "name": "go"}, {"control_type": "Button", "name": "back"}]}  # 新增代码+CapabilityProfileTest：构造地址输入和导航按钮；如果没有这行代码，画像没有导航样本。
    profile = build_capability_profile(frame)  # 新增代码+CapabilityProfileTest：生成能力画像；如果没有这行代码，无法断言导航能力。
    assert profile.has_browser_navigation_surface is True  # 新增代码+CapabilityProfileTest：确认导航表面为真；如果没有这行代码，导航批不会生成。
    assert profile.has_text_input is True  # 新增代码+CapabilityProfileTest：确认地址输入仍是文本能力；如果没有这行代码，搜索文本无法输入。


def test_empty_observation_reports_unknown_capabilities() -> None:  # 新增代码+CapabilityProfileTest：函数段开始，验证空观察进入未知能力；如果没有这个测试，未知软件可能被误判成功。
    profile = build_capability_profile({"uia_tree": [], "visual_regions": []})  # 新增代码+CapabilityProfileTest：对空观察生成画像；如果没有这行代码，未知路径无法覆盖。
    assert profile.unknown_capabilities is True  # 新增代码+CapabilityProfileTest：确认未知能力为真；如果没有这行代码，运行时不会向用户或探测阶段收敛。
    assert profile.has_text_input is False  # 新增代码+CapabilityProfileTest：确认没有伪造文本能力；如果没有这行代码，写入可能误发。
