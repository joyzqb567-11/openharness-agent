新增代码+DesktopTaskVisibleAcceptance：本次 Task7 真实可见终端验收没有生成 latest_run_readable.md；如果没有这份说明，后续复盘时可能误以为日志复制遗漏。
新增代码+DesktopTaskVisibleAcceptance：验收证据已经完整写入 visible_terminal_result.json、visible_terminal_events.jsonl、01_startup.png、02_prompt_sent.png、03_final.png；如果没有这些文件，才需要重新运行 controller 场景。
新增代码+DesktopTaskVisibleAcceptance：result.json 中 assertion.passed=true，event_payload_regex_checks 中 gui_action_count 和 low_level_event_count 均为 true；如果没有这些字段，严格验收不能证明自然语言任务真的进入 GUI 动作证据链。
