# Background Commands Rule

使用场景：
- 测试、构建、开发服务器、长命令或需要持续读取输出的进程。

规则：
- 短命令直接用 `bash` 并设置合理 timeout。
- 长命令要能启动、读取输出、停止，并记录 command_id。
- 命令失败时报告 exit code、stdout、stderr 的关键证据，不要假装成功。
- 结束任务时停止不再需要的后台进程。

关键词：start_background_command、read_background_command、stop_background_command、后台命令、dev server、tests、stdout、stderr、exit_code。
