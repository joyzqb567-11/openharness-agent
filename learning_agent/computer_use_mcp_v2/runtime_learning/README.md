# Computer Use Runtime Learning

新增代码+RuntimeLearning：这个目录只保存 `computer_use_mcp_v2` 内部的脱敏重复失败模式；如果没有这个目录，Computer Use 的经验会混入主 agent 记忆，后续长任务容易跑偏。

新增代码+RuntimeLearning：`patterns.jsonl` 只允许保存失败分类、修复策略、阶段标识和低敏计数；如果没有这条约束，prompt、截图、剪贴板、密码、文件正文或本机私有路径可能被错误落盘。

新增代码+RuntimeLearning：单次失败默认不写入学习文件，只有同类失败重复出现才固化；如果没有这条约束，偶发观察误差会污染通用 Computer Use 经验库。
