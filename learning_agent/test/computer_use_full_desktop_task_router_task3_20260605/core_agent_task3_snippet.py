# 新增代码+DesktopTaskPolicy：本文件是 core/agent.py 的 Task 3 学习片段备份；如果没有这个文件，用户需要在很长的 agent.py 里手动找本次改动。
# 修改代码+DesktopTaskPolicy：LearningAgent.__init__ 的函数段顶部注释改为说明桌面任务策略上下文；如果没有这条修改，代码小白不容易知道 `_bash_atom` 的 active 状态来自初始化字段。
# 修改代码+DesktopTaskPolicy：    def __init__(  # 修改代码+DesktopTaskPolicy：函数段开始，初始化参数保持旧调用方式并补充桌面任务策略上下文；如果没有这个函数段，agent 无法保存模型、workspace、权限和 Task 3 的 active 状态，作者意图是让 `_bash_atom` 能知道当前是否处于桌面任务，本段与 `_bash_atom` 配合到初始化字段结束。
# 新增代码+DesktopTaskPolicy：        self.desktop_task_context: dict[str, Any] = {"active": False}  # 新增代码+DesktopTaskPolicy：初始化桌面任务策略上下文，默认未激活；如果没有这一行，_bash_atom 无法判断何时必须阻止脚本生成最终图片制品。
# 修改代码+DesktopTaskPolicy：LearningAgent._bash_atom 的函数段顶部注释改为说明会先检查桌面任务脚本制品策略；如果没有这条修改，读者不容易发现 bash 执行入口新增了 GUI 路线门禁。
# 修改代码+DesktopTaskPolicy：    def _bash_atom(self, arguments: dict[str, Any]) -> str:  # 修改代码+DesktopTaskPolicy：函数段开始，实现 bash 原子工具并在桌面任务 active 时先检查脚本制品策略；如果没有这段函数，首轮 bash schema 只能被看见但无法执行，作者意图是让命令执行前先经过 Task 3 GUI 路线门禁，本函数与 desktop_task_policy 配合到 return 结束。
# 新增代码+DesktopTaskPolicy：        desktop_task_context = getattr(self, "desktop_task_context", {})  # 新增代码+DesktopTaskPolicy：读取当前 agent 的桌面任务上下文；如果没有这一行，轻量测试对象或旧实例无法被安全识别为 active/inactive。
# 新增代码+DesktopTaskPolicy：        desktop_task_active = bool(desktop_task_context.get("active", False)) if isinstance(desktop_task_context, dict) else False  # 新增代码+DesktopTaskPolicy：只从字典上下文读取 active 布尔值；如果没有这一行，异常上下文形状可能让 bash 工具崩溃。
# 新增代码+DesktopTaskPolicy：        if desktop_task_active:  # 新增代码+DesktopTaskPolicy：只在桌面任务激活时启用命令策略；如果没有这一行，普通开发命令也会承担额外拦截逻辑。
# 新增代码+DesktopTaskPolicy：            try:  # 新增代码+DesktopTaskPolicy：优先按包运行模式导入策略函数；如果没有这一行，start_oauth_agent.bat 和 unittest 的导入环境无法兼容处理。
# 新增代码+DesktopTaskPolicy：                from learning_agent.computer_use.desktop_task_policy import evaluate_desktop_bash_command  # 新增代码+DesktopTaskPolicy：导入桌面任务 bash 策略函数；如果没有这一行，_bash_atom 无法在权限请求前识别脚本最终制品路线。
# 新增代码+DesktopTaskPolicy：            except ModuleNotFoundError as error:  # 新增代码+DesktopTaskPolicy：兼容直接脚本运行时 learning_agent 包路径不可用的情况；如果没有这一行，脚本模式可能因为包名前缀失败。
# 新增代码+DesktopTaskPolicy：                if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.desktop_task_policy"}:  # 新增代码+DesktopTaskPolicy：只对目标包路径缺失做 fallback；如果没有这一行，策略模块内部真实导入错误会被误吞。
# 新增代码+DesktopTaskPolicy：                    raise  # 新增代码+DesktopTaskPolicy：重新抛出非目标导入错误；如果没有这一行，排查策略模块内部 bug 会很困难。
# 新增代码+DesktopTaskPolicy：                from computer_use.desktop_task_policy import evaluate_desktop_bash_command  # 新增代码+DesktopTaskPolicy：脚本模式下从本地 computer_use 包导入策略函数；如果没有这一行，bat 入口可能无法加载 Task 3 策略。
# 新增代码+DesktopTaskPolicy：            desktop_policy_result = evaluate_desktop_bash_command(command=command, desktop_task_active=desktop_task_active)  # 新增代码+DesktopTaskPolicy：在 cwd 解析、权限请求和执行命令前评估策略；如果没有这一行，危险命令会继续走到真实 shell 流程。
# 新增代码+DesktopTaskPolicy：            if not bool(desktop_policy_result.get("allowed", False)):  # 新增代码+DesktopTaskPolicy：检查策略是否拒绝当前命令；如果没有这一行，命中禁止脚本制品路线也不会被拦住。
# 新增代码+DesktopTaskPolicy：                desktop_policy_text = json.dumps(desktop_policy_result, ensure_ascii=False, indent=2)  # 新增代码+DesktopTaskPolicy：把结构化策略结果转成中文友好的 JSON；如果没有这一行，拒绝文本缺少可复盘细节。
# 新增代码+DesktopTaskPolicy：                return f"bash 拒绝：{desktop_policy_result.get('decision', 'desktop_task_requires_gui_route')}\n原因：{desktop_policy_result.get('reason', '')}\n策略详情：{desktop_policy_text}"  # 新增代码+DesktopTaskPolicy：直接返回清晰拒绝，不请求权限也不执行命令；如果没有这一行，脚本生成最终图片制品路线仍可能进入真实终端。
