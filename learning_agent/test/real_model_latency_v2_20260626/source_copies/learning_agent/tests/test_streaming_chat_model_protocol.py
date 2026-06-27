from learning_agent.models.streaming import ModelStreamEvent  # 新增代码+真实模型流式合同: 导入待实现的流式事件类型；如果没有这行，测试无法锁定后端事件合同入口。


def test_model_stream_event_requires_phase_sequence_and_turn_context():  # 新增代码+真实模型流式合同: 测试事件必须带 phase、sequence 和 turn 上下文；如果没有这条测试，取消后的旧事件可能污染新会话。
    event = ModelStreamEvent(  # 新增代码+真实模型流式合同: 构造一条模型状态事件；如果没有这行，测试无法验证事件字段形状。
        event_type="status",  # 新增代码+真实模型流式合同: 标记这是状态事件；如果没有这行，前端无法区分状态和文本 delta。
        phase="connecting",  # 新增代码+真实模型流式合同: 标记当前阶段为连接中；如果没有这行，GUI 只能显示笼统 running。
        message="正在连接 GPT-5.5",  # 新增代码+真实模型流式合同: 保存用户可见状态文案；如果没有这行，用户仍会面对空白等待。
        timestamp=1.0,  # 新增代码+真实模型流式合同: 保存事件时间；如果没有这行，后续无法计算真实延迟。
        elapsed_ms=12,  # 新增代码+真实模型流式合同: 保存相对耗时；如果没有这行，状态面板需要自己推导耗时。
        sequence=1,  # 新增代码+真实模型流式合同: 保存单 turn 内事件顺序；如果没有这行，late delta 去重和排序更脆弱。
        turn_id="turn_1",  # 新增代码+真实模型流式合同: 保存 turn id；如果没有这行，取消后无法识别旧 turn 事件。
        provider_id="openai",  # 新增代码+真实模型流式合同: 保存 provider id；如果没有这行，前端无法展示调用来源。
        model_id="gpt-5.5",  # 新增代码+真实模型流式合同: 保存模型 id；如果没有这行，用户无法确认所选模型是否被使用。
        metadata={"transport": "codex_cli"},  # 新增代码+真实模型流式合同: 保存脱敏传输信息；如果没有这行，诊断面板无法解释 Codex CLI fallback。
    )  # 新增代码+真实模型流式合同: 事件构造结束；如果没有这行，Python 调用语法不完整。

    assert event.phase == "connecting"  # 新增代码+真实模型流式合同: 确认 phase 字段存在；如果没有这行，测试不能防止事件退化成普通字符串。
    assert event.sequence == 1  # 新增代码+真实模型流式合同: 确认 sequence 字段存在；如果没有这行，测试不能覆盖 stale event 防线。
    assert event.turn_id == "turn_1"  # 新增代码+真实模型流式合同: 确认 turn_id 字段存在；如果没有这行，测试不能保证取消隔离。
    assert event.metadata["transport"] == "codex_cli"  # 新增代码+真实模型流式合同: 确认 metadata 可承载脱敏诊断；如果没有这行，诊断信息可能散落在 message 中。
