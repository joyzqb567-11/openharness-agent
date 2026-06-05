# ????+DesktopTaskPolicy????? Task 3 ?? learning_agent/core/agent.py ??????????????????????????? agent.py ??????????
# ????+DesktopTaskPolicy????????????????????????????????????????? Task 3 ????????

        self.desktop_task_context: dict[str, Any] = {"active": False}  # ????+DesktopTaskPolicy????????????????????????????_bash_atom ?????????????????????

    def _desktop_task_policy_context_from_prompt(self, user_input: str) -> dict[str, Any]:  # 新增代码+DesktopTaskPolicy：函数段开始，把用户自然语言 prompt 转成脱敏桌面任务策略上下文；如果没有这段函数，run_events 无法在真实模型工具循环前自动设置 active，作者意图是复用 Task 2 分类器而不保存原始 prompt，本函数与 run_events 和 _bash_atom 配合到 return 结束。
        try:  # 新增代码+DesktopTaskPolicy：优先按包运行模式导入桌面任务分类器；如果没有这一行，unittest 和包启动路径无法复用 Task 2 分类逻辑。
            from learning_agent.computer_use.desktop_task_router import classify_desktop_task  # 新增代码+DesktopTaskPolicy：导入自然语言桌面任务分类函数；如果没有这一行，策略上下文只能靠手动 monkeypatch。
        except ModuleNotFoundError as error:  # 新增代码+DesktopTaskPolicy：兼容直接脚本运行时 learning_agent 包路径不可用的情况；如果没有这一行，bat 入口可能因包名前缀失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.desktop_task_router"}:  # 新增代码+DesktopTaskPolicy：只对目标包路径缺失做 fallback；如果没有这一行，分类器内部真实 bug 会被误吞。
                raise  # 新增代码+DesktopTaskPolicy：重新抛出非目标导入错误；如果没有这一行，排查分类器内部问题会很困难。
            from computer_use.desktop_task_router import classify_desktop_task  # 新增代码+DesktopTaskPolicy：脚本模式下从本地 computer_use 包导入分类函数；如果没有这一行，start_oauth_agent.bat 可能无法加载 Task 2 分类器。
        intent = classify_desktop_task(user_input)  # 新增代码+DesktopTaskPolicy：用同一套桌面任务分类器判断当前 prompt；如果没有这一行，active 状态会和 Task 2 路由结果分裂。
        return {  # 新增代码+DesktopTaskPolicy：返回脱敏上下文字典；如果没有这一行，_bash_atom 无法从统一字段读取 active 和目标信息。
            "active": bool(intent.is_desktop_task),  # 新增代码+DesktopTaskPolicy：把是否桌面任务写入 active；如果没有这一项，bash 策略不会知道何时必须拦截脚本绕路。
            "reason": intent.reason,  # 新增代码+DesktopTaskPolicy：保存分类原因而不是原始 prompt；如果没有这一项，日志难以解释为什么开启或关闭桌面任务门禁。
            "target_app_hint": intent.target_app_hint,  # 新增代码+DesktopTaskPolicy：保存目标应用提示；如果没有这一项，后续 runtime 无法复用本次识别到的 Paint/mspaint 线索。
            "task_goal": intent.task_goal,  # 新增代码+DesktopTaskPolicy：保存脱敏任务目标摘要；如果没有这一项，后续 GUI runtime 缺少稳定目标类型。
            "requires_gui_actions": bool(intent.requires_gui_actions),  # 新增代码+DesktopTaskPolicy：保存是否需要 GUI 动作；如果没有这一项，策略无法区分本地应用观察和真正操作。
            "raw_prompt_included": bool(intent.raw_prompt_included),  # 新增代码+DesktopTaskPolicy：明确记录没有保存原始 prompt；如果没有这一项，后续审计无法确认脱敏边界。
        }  # 新增代码+DesktopTaskPolicy：上下文字典结束；如果没有这一行，Python 字典语法不完整。
    # 新增代码+DesktopTaskPolicy：函数段结束，_desktop_task_policy_context_from_prompt 到此结束；如果没有这个边界说明，代码小白不容易看出上下文构造范围。

    def _restore_desktop_task_policy_context(self, previous_context: dict[str, Any]) -> None:  # 新增代码+DesktopTaskPolicy：函数段开始，恢复 run_events 进入前的桌面任务上下文；如果没有这段函数，桌面任务 active 可能污染下一轮普通任务，作者意图是让上下文生命周期严格绑定单次 run_events，本函数与 run_events 的 finally 配合到赋值结束。
        if isinstance(previous_context, dict):  # 新增代码+DesktopTaskPolicy：只在旧上下文确实是字典时原样恢复；如果没有这一行，异常形状可能再次污染 desktop_task_context。
            self.desktop_task_context = copy.deepcopy(previous_context)  # 新增代码+DesktopTaskPolicy：深拷贝恢复旧上下文避免共享可变对象；如果没有这一行，后续修改可能影响保存的旧值。
            return  # 新增代码+DesktopTaskPolicy：恢复完成后直接返回；如果没有这一行，下面的兜底 inactive 会覆盖合法旧上下文。
        self.desktop_task_context = {"active": False}  # 新增代码+DesktopTaskPolicy：旧上下文不是字典时兜底恢复为 inactive；如果没有这一行，异常状态可能让下一轮 bash 策略崩溃。
    # 新增代码+DesktopTaskPolicy：函数段结束，_restore_desktop_task_policy_context 到此结束；如果没有这个边界说明，代码小白不容易看出上下文恢复范围。

        previous_desktop_task_context = copy.deepcopy(self.desktop_task_context) if isinstance(getattr(self, "desktop_task_context", {}), dict) else {"active": False}  # ????+DesktopTaskPolicy??????? run_events ??????????????????finally ??? active ??????
            self.desktop_task_context = self._desktop_task_policy_context_from_prompt(user_input)  # ????+DesktopTaskPolicy?????????????????? prompt ?? active???????????????? _bash_atom ??? inactive ???????
        finally:  # ????+DesktopTaskPolicy?????????? return????????????????????????active ???????????????
            self._restore_desktop_task_policy_context(previous_desktop_task_context)  # ????+DesktopTaskPolicy???? run_events ????????????????????????? bash ???????? active?

    def _bash_atom(self, arguments: dict[str, Any]) -> str:  # 修改代码+DesktopTaskPolicy：函数段开始，实现 bash 原子工具并在桌面任务 active 时先检查脚本制品策略；如果没有这段函数，首轮 bash schema 只能被看见但无法执行，作者意图是让命令执行前先经过 Task 3 GUI 路线门禁，本函数与 desktop_task_policy 配合到 return 结束。
        desktop_task_context = getattr(self, "desktop_task_context", {})  # 新增代码+DesktopTaskPolicy：读取当前 agent 的桌面任务上下文；如果没有这一行，轻量测试对象或旧实例无法被安全识别为 active/inactive。
        desktop_task_active = bool(desktop_task_context.get("active", False)) if isinstance(desktop_task_context, dict) else False  # 新增代码+DesktopTaskPolicy：只从字典上下文读取 active 布尔值；如果没有这一行，异常上下文形状可能让 bash 工具崩溃。
        if desktop_task_active:  # 新增代码+DesktopTaskPolicy：只在桌面任务激活时启用命令策略；如果没有这一行，普通开发命令也会承担额外拦截逻辑。
            try:  # 新增代码+DesktopTaskPolicy：优先按包运行模式导入策略函数；如果没有这一行，start_oauth_agent.bat 和 unittest 的导入环境无法兼容处理。
                from learning_agent.computer_use.desktop_task_policy import evaluate_desktop_bash_command  # 新增代码+DesktopTaskPolicy：导入桌面任务 bash 策略函数；如果没有这一行，_bash_atom 无法在权限请求前识别脚本最终制品路线。
            except ModuleNotFoundError as error:  # 新增代码+DesktopTaskPolicy：兼容直接脚本运行时 learning_agent 包路径不可用的情况；如果没有这一行，脚本模式可能因为包名前缀失败。
                if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.desktop_task_policy"}:  # 新增代码+DesktopTaskPolicy：只对目标包路径缺失做 fallback；如果没有这一行，策略模块内部真实导入错误会被误吞。
                    raise  # 新增代码+DesktopTaskPolicy：重新抛出非目标导入错误；如果没有这一行，排查策略模块内部 bug 会很困难。
                from computer_use.desktop_task_policy import evaluate_desktop_bash_command  # 新增代码+DesktopTaskPolicy：脚本模式下从本地 computer_use 包导入策略函数；如果没有这一行，bat 入口可能无法加载 Task 3 策略。
            desktop_policy_result = evaluate_desktop_bash_command(command=command, desktop_task_active=desktop_task_active)  # 新增代码+DesktopTaskPolicy：在 cwd 解析、权限请求和执行命令前评估策略；如果没有这一行，危险命令会继续走到真实 shell 流程。
            if not bool(desktop_policy_result.get("allowed", False)):  # 新增代码+DesktopTaskPolicy：检查策略是否拒绝当前命令；如果没有这一行，命中禁止脚本制品路线也不会被拦住。
                desktop_policy_text = json.dumps(desktop_policy_result, ensure_ascii=False, indent=2)  # 新增代码+DesktopTaskPolicy：把结构化策略结果转成中文友好的 JSON；如果没有这一行，拒绝文本缺少可复盘细节。
                return f"bash 拒绝：{desktop_policy_result.get('decision', 'desktop_task_requires_gui_route')}\n原因：{desktop_policy_result.get('reason', '')}\n策略详情：{desktop_policy_text}"  # 新增代码+DesktopTaskPolicy：直接返回清晰拒绝，不请求权限也不执行命令；如果没有这一行，脚本生成最终图片制品路线仍可能进入真实终端。
