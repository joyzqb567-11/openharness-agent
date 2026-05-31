# Task Lifecycle Rule

使用场景：
- 子任务可以独立完成，且有清楚边界。
- 用户需要后台分析、审查、交接或教学式 peer 记录。

规则：
- 子任务 prompt 要包含目标、范围、输入、输出格式和停止条件。
- allowed_tools 越少越好，避免把父 agent 的所有能力传给子 agent。
- background=true 只表示后台执行任务记录，不等于无限期无人值守。
- 查询结果用 task_output；停止任务用 task_stop；管理记录用 task_list、task_get、task_update。
- team_create、send_message、list_peers、read_peer_messages、ack_peer_message、team_delete、team_start_task 是教学式通信记录，不代表真实远端协作已经发生。

关键词：task、子 agent、task_output、task_stop、task_list、task_get、task_update、team_create、send_message、list_peers、read_peer_messages、ack_peer_message、team_delete、team_start_task、background=true。
