import unittest  # 新增代码+DesktopTaskAcceptance：导入 unittest 测试框架；如果没有这一行，项目现有测试命令就不能发现和运行本回归测试。

from learning_agent.computer_use.desktop_task_acceptance import evaluate_desktop_task_acceptance  # 新增代码+DesktopTaskAcceptance：导入桌面任务验收评估器；如果没有这一行，测试就无法验证脚本绕路会被拒绝。
from learning_agent.computer_use.desktop_task_router import classify_desktop_task  # 新增代码+DesktopTaskRouter：导入 Task 2 的桌面任务意图分类函数；如果没有这一行，本测试文件就无法验证自然语言 prompt 会不会进入桌面任务路线。


class WindowsComputerUseFullDesktopTaskRouterTests(unittest.TestCase):  # 新增代码+DesktopTaskAcceptance：类段开始，集中冻结 `/computer use --full` 桌面任务路由验收；如果没有这个类，unittest 不会组织这些回归用例。
    def test_script_generated_paint_artifact_fails_desktop_task_acceptance(self) -> None:  # 新增代码+DesktopTaskAcceptance：函数段开始，验证脚本生成画图最终作品必须失败；如果没有这个测试，之前 bash/PowerShell 生成 PNG 再打开 Paint 的绕路可能复发。
        evidence = {  # 新增代码+DesktopTaskAcceptance：构造上一次真实失败路线的证据字典；如果没有这一行，评估器没有可判断的输入。
            "desktop_task_router_used": True,  # 新增代码+DesktopTaskAcceptance：声明任务已经进入桌面任务路由；如果没有这一行，测试无法区分路由缺失和脚本绕路。
            "computer_use_gui_route_used": False,  # 新增代码+DesktopTaskAcceptance：声明这次没有走 GUI 鼠标键盘路线；如果没有这一行，评估器可能误把脚本路线当成 GUI 成功。
            "tool_calls": [  # 新增代码+DesktopTaskAcceptance：记录模型实际调用过的工具；如果没有这一段，评估器无法从工具调用里识别 bash/PowerShell 绕路。
                {"tool_name": "bash", "command": "Add-Type -AssemblyName System.Drawing; Start-Process mspaint.exe pikachu_for_paint.png"}  # 新增代码+DesktopTaskAcceptance：模拟 bash 中执行 PowerShell 画图制品再打开 Paint；如果没有这一行，负向回归无法覆盖真实失败痕迹。
            ],  # 新增代码+DesktopTaskAcceptance：结束工具调用列表；如果没有这一行，证据结构不是合法 Python 字典。
            "gui_action_count": 0,  # 新增代码+DesktopTaskAcceptance：声明没有 GUI 高层动作；如果没有这一行，评估器可能看不出这是零 GUI 操作。
            "low_level_event_count": 0,  # 新增代码+DesktopTaskAcceptance：声明没有真实底层鼠标键盘事件；如果没有这一行，评估器无法证明没有 Computer Use 操作。
            "target_app": "mspaint",  # 新增代码+DesktopTaskAcceptance：声明目标应用是 Paint；如果没有这一行，测试读者不容易看出这是画图软件场景。
        }  # 新增代码+DesktopTaskAcceptance：结束负向证据字典；如果没有这一行，测试代码无法运行。
        result = evaluate_desktop_task_acceptance(evidence)  # 新增代码+DesktopTaskAcceptance：执行桌面任务验收评估；如果没有这一行，测试只是在摆数据没有验证行为。
        self.assertFalse(result["passed"])  # 新增代码+DesktopTaskAcceptance：断言脚本制品路线不能通过；如果没有这一行，绕路可能被误判成合格。
        self.assertTrue(result["forbidden_script_generation_used"])  # 新增代码+DesktopTaskAcceptance：断言检测到禁止的脚本生成最终作品；如果没有这一行，测试无法证明评估器抓到了根因。
        self.assertEqual(result["decision"], "forbidden_script_artifact_route")  # 新增代码+DesktopTaskAcceptance：断言失败原因码稳定；如果没有这一行，后续 Task 2/Task 3 无法依赖固定 decision。
    # 新增代码+DesktopTaskAcceptance：函数段结束，test_script_generated_paint_artifact_fails_desktop_task_acceptance 到此结束；如果没有这个边界说明，代码小白不容易看出负向测试范围。

    def test_complete_gui_route_passes_desktop_task_acceptance(self) -> None:  # 新增代码+DesktopTaskAcceptance：函数段开始，验证全部成熟条件满足时可以通过；如果没有这个正向测试，评估器可能只会拒绝不会接受。
        evidence = {  # 新增代码+DesktopTaskAcceptance：构造最小 GUI 成功证据；如果没有这一行，正向验收没有输入事实。
            "desktop_task_router_used": True,  # 新增代码+DesktopTaskAcceptance：声明桌面任务路由已使用；如果没有这一行，成熟条件缺少入口证明。
            "computer_use_gui_route_used": True,  # 新增代码+DesktopTaskAcceptance：声明走了 Computer Use GUI 路线；如果没有这一行，评估器无法确认没有回到普通脚本工具。
            "bash_final_artifact_route_used": False,  # 新增代码+DesktopTaskAcceptance：声明没有 bash 最终制品路线；如果没有这一行，正向证据缺少禁止路线的明确否定。
            "forbidden_script_generation_used": False,  # 新增代码+DesktopTaskAcceptance：声明没有脚本生成最终作品；如果没有这一行，正向证据不完整。
            "owned_window_verified": True,  # 新增代码+DesktopTaskAcceptance：声明目标窗口身份已验证；如果没有这一行，动作可能落到非 agent 拥有窗口。
            "gui_action_count": 3,  # 新增代码+DesktopTaskAcceptance：声明至少有一次 GUI 高层动作；如果没有这一行，评估器无法证明真实 GUI 路线被使用。
            "low_level_event_count": 6,  # 新增代码+DesktopTaskAcceptance：声明有底层鼠标键盘事件；如果没有这一行，评估器无法证明真实 Computer Use 输入发生。
            "post_action_screenshot_exists": True,  # 新增代码+DesktopTaskAcceptance：声明动作后截图存在；如果没有这一行，验收缺少可复盘视觉证据。
            "tool_calls": [],  # 新增代码+DesktopTaskAcceptance：声明没有脚本工具调用；如果没有这一行，正向测试无法证明空工具调用时不会误报绕路。
        }  # 新增代码+DesktopTaskAcceptance：结束正向证据字典；如果没有这一行，测试代码无法运行。
        result = evaluate_desktop_task_acceptance(evidence)  # 新增代码+DesktopTaskAcceptance：执行桌面任务验收评估；如果没有这一行，正向测试不会触发被测逻辑。
        self.assertTrue(result["passed"])  # 新增代码+DesktopTaskAcceptance：断言完整 GUI 路线可以通过；如果没有这一行，评估器可能过度保守导致真实 GUI 任务永远失败。
        self.assertFalse(result["forbidden_script_generation_used"])  # 新增代码+DesktopTaskAcceptance：断言正向路线没有脚本生成制品；如果没有这一行，正向结果可能带着错误风险标记。
        self.assertFalse(result["bash_final_artifact_route_used"])  # 新增代码+DesktopTaskAcceptance：断言正向路线没有 bash 最终制品；如果没有这一行，后续路由器无法区分正常 GUI 和脚本绕路。
        self.assertEqual(result["decision"], "accepted_desktop_gui_route")  # 新增代码+DesktopTaskAcceptance：断言成功原因码稳定；如果没有这一行，后续验收输出不方便匹配。
        self.assertEqual(result["missing_requirements"], [])  # 新增代码+DesktopTaskAcceptance：断言完整证据没有缺失项；如果没有这一行，正向测试可能忽略隐藏缺口。
    # 新增代码+DesktopTaskAcceptance：函数段结束，test_complete_gui_route_passes_desktop_task_acceptance 到此结束；如果没有这个边界说明，代码小白不容易看出正向测试范围。

    def test_non_dict_evidence_is_rejected_without_exception(self) -> None:  # 新增代码+DesktopTaskAcceptance：函数段开始，验证非字典 evidence 会稳定拒绝而不是崩溃；如果没有这个测试，调用方传错形状会中断整个 agent。
        result = evaluate_desktop_task_acceptance(["not-a-dict"])  # 新增代码+DesktopTaskAcceptance：传入列表模拟坏输入；如果没有这一行，测试无法覆盖 dict(evidence) 崩溃根因。
        self.assertFalse(result["passed"])  # 新增代码+DesktopTaskAcceptance：断言坏输入不能通过；如果没有这一行，异常 evidence 可能被误判为成功。
        self.assertEqual(result["decision"], "missing_desktop_task_requirements")  # 新增代码+DesktopTaskAcceptance：断言坏输入使用稳定的缺失条件决策；如果没有这一行，调用方无法区分拒绝原因。
        self.assertIsInstance(result["missing_requirements"], list)  # 新增代码+DesktopTaskAcceptance：断言缺失条件是列表；如果没有这一行，后续展示层可能拿到不可迭代字段。
        self.assertGreater(len(result["missing_requirements"]), 0)  # 新增代码+DesktopTaskAcceptance：断言坏输入会列出缺失项；如果没有这一行，用户不知道缺哪些成熟证据。
    # 新增代码+DesktopTaskAcceptance：函数段结束，test_non_dict_evidence_is_rejected_without_exception 到此结束；如果没有这个边界说明，代码小白不容易看出坏 evidence 测试范围。

    def test_non_numeric_gui_action_count_is_missing_without_exception(self) -> None:  # 新增代码+DesktopTaskAcceptance：函数段开始，验证 GUI 动作次数非数字时稳定判缺失；如果没有这个测试，字符串坏值会再次触发 ValueError。
        evidence = {  # 新增代码+DesktopTaskAcceptance：构造只有 gui_action_count 坏掉的近似完整证据；如果没有这一行，测试无法精准定位 positive_int 规则。
            "desktop_task_router_used": True,  # 新增代码+DesktopTaskAcceptance：保留桌面任务路由通过；如果没有这一行，失败原因会混入路由缺失。
            "computer_use_gui_route_used": True,  # 新增代码+DesktopTaskAcceptance：保留 GUI 路线通过；如果没有这一行，失败原因会混入 GUI 路线缺失。
            "bash_final_artifact_route_used": False,  # 新增代码+DesktopTaskAcceptance：保留 bash 制品路线为假；如果没有这一行，失败原因会混入禁止路线。
            "forbidden_script_generation_used": False,  # 新增代码+DesktopTaskAcceptance：保留禁止脚本路线为假；如果没有这一行，失败原因会混入脚本绕路。
            "owned_window_verified": True,  # 新增代码+DesktopTaskAcceptance：保留自有窗口验证通过；如果没有这一行，失败原因会混入窗口验证缺失。
            "gui_action_count": "abc",  # 新增代码+DesktopTaskAcceptance：放入非数字字符串；如果没有这一行，测试不能复现 int('abc') 崩溃。
            "low_level_event_count": 2,  # 新增代码+DesktopTaskAcceptance：保留底层事件次数有效；如果没有这一行，测试无法确认只缺 gui_action_count。
            "post_action_screenshot_exists": True,  # 新增代码+DesktopTaskAcceptance：保留动作后截图存在；如果没有这一行，失败原因会混入截图缺失。
            "tool_calls": [],  # 新增代码+DesktopTaskAcceptance：保留无脚本工具调用；如果没有这一行，测试可能被脚本检测影响。
        }  # 新增代码+DesktopTaskAcceptance：结束 GUI 坏计数证据字典；如果没有这一行，测试代码无法运行。
        result = evaluate_desktop_task_acceptance(evidence)  # 新增代码+DesktopTaskAcceptance：执行评估器；如果没有这一行，测试无法证明坏计数不再抛异常。
        self.assertFalse(result["passed"])  # 新增代码+DesktopTaskAcceptance：断言坏计数不能通过；如果没有这一行，缺少 GUI 动作证据可能被放行。
        self.assertIn("gui_action_count", result["missing_requirements"])  # 新增代码+DesktopTaskAcceptance：断言 gui_action_count 被视为缺失；如果没有这一行，positive_int 坏值可能静默通过。
        self.assertNotIn("low_level_event_count", result["missing_requirements"])  # 新增代码+DesktopTaskAcceptance：断言有效底层事件不被误判缺失；如果没有这一行，修复可能误伤正常计数字段。
    # 新增代码+DesktopTaskAcceptance：函数段结束，test_non_numeric_gui_action_count_is_missing_without_exception 到此结束；如果没有这个边界说明，代码小白不容易看出 GUI 坏计数测试范围。

    def test_non_numeric_low_level_event_count_is_missing_without_exception(self) -> None:  # 新增代码+DesktopTaskAcceptance：函数段开始，验证底层事件次数非数字时稳定判缺失；如果没有这个测试，dict/list 等坏值可能再次导致 TypeError。
        evidence = {  # 新增代码+DesktopTaskAcceptance：构造只有 low_level_event_count 坏掉的近似完整证据；如果没有这一行，测试无法精准覆盖底层事件计数字段。
            "desktop_task_router_used": True,  # 新增代码+DesktopTaskAcceptance：保留桌面任务路由通过；如果没有这一行，失败原因会混入路由缺失。
            "computer_use_gui_route_used": True,  # 新增代码+DesktopTaskAcceptance：保留 GUI 路线通过；如果没有这一行，失败原因会混入 GUI 路线缺失。
            "bash_final_artifact_route_used": False,  # 新增代码+DesktopTaskAcceptance：保留 bash 制品路线为假；如果没有这一行，失败原因会混入禁止路线。
            "forbidden_script_generation_used": False,  # 新增代码+DesktopTaskAcceptance：保留禁止脚本路线为假；如果没有这一行，失败原因会混入脚本绕路。
            "owned_window_verified": True,  # 新增代码+DesktopTaskAcceptance：保留自有窗口验证通过；如果没有这一行，失败原因会混入窗口验证缺失。
            "gui_action_count": 2,  # 新增代码+DesktopTaskAcceptance：保留 GUI 动作次数有效；如果没有这一行，测试无法确认只缺 low_level_event_count。
            "low_level_event_count": {"bad": "count"},  # 新增代码+DesktopTaskAcceptance：放入非数字字典；如果没有这一行，测试不能复现 int(dict) 崩溃风险。
            "post_action_screenshot_exists": True,  # 新增代码+DesktopTaskAcceptance：保留动作后截图存在；如果没有这一行，失败原因会混入截图缺失。
            "tool_calls": [],  # 新增代码+DesktopTaskAcceptance：保留无脚本工具调用；如果没有这一行，测试可能被脚本检测影响。
        }  # 新增代码+DesktopTaskAcceptance：结束底层事件坏计数证据字典；如果没有这一行，测试代码无法运行。
        result = evaluate_desktop_task_acceptance(evidence)  # 新增代码+DesktopTaskAcceptance：执行评估器；如果没有这一行，测试无法证明坏计数不再抛异常。
        self.assertFalse(result["passed"])  # 新增代码+DesktopTaskAcceptance：断言坏计数不能通过；如果没有这一行，缺少底层事件证据可能被放行。
        self.assertNotIn("gui_action_count", result["missing_requirements"])  # 新增代码+DesktopTaskAcceptance：断言有效 GUI 动作不被误判缺失；如果没有这一行，修复可能误伤正常计数字段。
        self.assertIn("low_level_event_count", result["missing_requirements"])  # 新增代码+DesktopTaskAcceptance：断言 low_level_event_count 被视为缺失；如果没有这一行，positive_int 坏值可能静默通过。
    # 新增代码+DesktopTaskAcceptance：函数段结束，test_non_numeric_low_level_event_count_is_missing_without_exception 到此结束；如果没有这个边界说明，代码小白不容易看出底层事件坏计数测试范围。

    def test_chinese_paint_prompt_routes_to_desktop_task(self) -> None:  # 新增代码+DesktopTaskRouter：函数段开始，验证中文“本地电脑+画图软件+画”的真实用户请求会被识别为桌面任务；如果没有这个测试，Task 2 可能漏掉用户最关心的中文 Paint 场景。
        intent = classify_desktop_task("请使用本地电脑的画图软件画一个皮卡丘。")  # 新增代码+DesktopTaskRouter：调用分类器处理中文 Paint prompt；如果没有这一行，测试就不会真正触发 Task 2 的分类逻辑。
        self.assertTrue(intent.is_desktop_task)  # 新增代码+DesktopTaskRouter：断言该 prompt 必须进入桌面任务路线；如果没有这一行，回归时可能又走回普通代码/脚本路线。
        self.assertEqual(intent.target_app_hint, "画图")  # 新增代码+DesktopTaskRouter：断言目标应用提示稳定表达为画图；如果没有这一行，后续运行层就难以知道应该优先考虑 Paint 类本地应用。
        self.assertTrue(intent.requires_gui_actions)  # 新增代码+DesktopTaskRouter：断言该任务需要 GUI 动作；如果没有这一行，系统可能错误允许脚本生成最终作品。
        self.assertFalse(intent.raw_prompt_included)  # 新增代码+DesktopTaskRouter：断言结构化结果不保存原始 prompt；如果没有这一行，用户原话可能泄漏进路由结果或日志。
    # 新增代码+DesktopTaskRouter：函数段结束，test_chinese_paint_prompt_routes_to_desktop_task 到此结束；如果没有这个边界说明，代码小白不容易看出中文正向路由测试范围。

    def test_code_question_does_not_route_to_desktop_task(self) -> None:  # 新增代码+DesktopTaskRouter：函数段开始，验证代码解释类请求不会误判成桌面任务；如果没有这个测试，普通 Python 报错问题可能被错误送去控制本地电脑。
        intent = classify_desktop_task("请解释这个 Python 函数为什么报错")  # 新增代码+DesktopTaskRouter：调用分类器处理代码报错解释 prompt；如果没有这一行，测试就无法覆盖误报保护。
        self.assertFalse(intent.is_desktop_task)  # 新增代码+DesktopTaskRouter：断言代码问题不是桌面任务；如果没有这一行，分类器可能把“报错/函数”这类开发问题误送 GUI 路线。
    # 新增代码+DesktopTaskRouter：函数段结束，test_code_question_does_not_route_to_desktop_task 到此结束；如果没有这个边界说明，代码小白不容易看出代码误报保护测试范围。

    def test_english_mspaint_prompt_routes_to_desktop_task(self) -> None:  # 新增代码+DesktopTaskRouter：函数段开始，验证英文 mspaint/desktop/draw 组合会被识别为桌面任务；如果没有这个测试，英文用户请求可能无法进入本地 GUI 路线。
        intent = classify_desktop_task("Use mspaint on this desktop to draw a simple house.")  # 新增代码+DesktopTaskRouter：调用分类器处理英文 mspaint prompt；如果没有这一行，测试无法证明英文本地应用关键词被支持。
        self.assertTrue(intent.is_desktop_task)  # 新增代码+DesktopTaskRouter：断言英文 mspaint 绘图请求是桌面任务；如果没有这一行，英文场景可能被错误留在普通 agent 路线。
        self.assertEqual(intent.target_app_hint, "mspaint")  # 新增代码+DesktopTaskRouter：断言 mspaint 目标应用提示保持稳定；如果没有这一行，后续运行层可能无法精确识别 Windows Paint 程序名。
        self.assertTrue(intent.requires_gui_actions)  # 新增代码+DesktopTaskRouter：断言英文绘图任务需要 GUI 动作；如果没有这一行，系统可能退回脚本生成图片。
        self.assertEqual(intent.task_goal, "draw_with_local_paint")  # 新增代码+DesktopTaskRouter：断言目标摘要是脱敏类型化目标；如果没有这一行，后续日志可能出现完整原始 prompt 或不稳定摘要。
    # 新增代码+DesktopTaskRouter：函数段结束，test_english_mspaint_prompt_routes_to_desktop_task 到此结束；如果没有这个边界说明，代码小白不容易看出英文正向路由测试范围。

    def test_git_test_docs_and_code_prompts_do_not_route_to_desktop_task(self) -> None:  # 新增代码+DesktopTaskRouter：函数段开始，验证 git、测试、文档、代码修改请求不会误报桌面任务；如果没有这个测试，日常开发 prompt 可能被错误送去操作本地 GUI。
        prompts = [  # 新增代码+DesktopTaskRouter：准备一组容易误报的开发类 prompt；如果没有这一行，误报保护只覆盖一个样本不够稳。
            "请修改 README 里的画图说明",  # 新增代码+DesktopTaskRouter：覆盖 README 文档修改请求；如果没有这一行，提到“画图”的文档任务可能误进桌面路线。
            "please run the unit test for the Paint helper",  # 新增代码+DesktopTaskRouter：覆盖英文单元测试请求；如果没有这一行，测试类请求可能被 paint 关键词误导。
            "git commit the desktop task router changes",  # 新增代码+DesktopTaskRouter：覆盖 git commit 请求；如果没有这一行，提交类请求可能被 desktop 关键词误导。
            "请解释这段画图代码为什么报错",  # 新增代码+DesktopTaskRouter：覆盖中文画图代码报错解释；如果没有这一行，代码解释可能因为画图二字误进 GUI 路线。
        ]  # 新增代码+DesktopTaskRouter：结束误报样本列表；如果没有这一行，测试数据结构不是合法 Python 列表。
        for prompt in prompts:  # 新增代码+DesktopTaskRouter：逐个检查误报样本；如果没有这一行，只有列表本身不会触发任何分类行为。
            with self.subTest(prompt=prompt):  # 新增代码+DesktopTaskRouter：给每个样本单独标记子测试；如果没有这一行，失败时不容易定位是哪类误报。
                intent = classify_desktop_task(prompt)  # 新增代码+DesktopTaskRouter：调用分类器处理当前误报样本；如果没有这一行，断言没有被测对象。
                self.assertFalse(intent.is_desktop_task)  # 新增代码+DesktopTaskRouter：断言开发类请求不是桌面任务；如果没有这一行，误报保护失效也不会被发现。
    # 新增代码+DesktopTaskRouter：函数段结束，test_git_test_docs_and_code_prompts_do_not_route_to_desktop_task 到此结束；如果没有这个边界说明，代码小白不容易看出误报保护测试范围。

    def test_raw_prompt_is_not_exposed_in_public_router_summary(self) -> None:  # 新增代码+DesktopTaskRouter：函数段开始，验证公开字典和字符串摘要不包含完整原始 prompt；如果没有这个测试，分类结果可能把用户原话写进结构化结果。
        raw_prompt = "Use Paint on my local computer to draw a secret yellow mascot 12345."  # 新增代码+DesktopTaskRouter：准备带有独特敏感片段的原始 prompt；如果没有这一行，测试无法检查泄漏风险。
        intent = classify_desktop_task(raw_prompt)  # 新增代码+DesktopTaskRouter：调用分类器生成结构化意图；如果没有这一行，测试没有可检查的分类结果。
        public_dict = intent.to_dict()  # 新增代码+DesktopTaskRouter：读取公开字典摘要；如果没有这一行，测试无法验证 to_dict 是否避免保存原始 prompt。
        public_summary = f"{public_dict} {intent}"  # 新增代码+DesktopTaskRouter：合并公开字典和字符串摘要做泄漏检查；如果没有这一行，__str__/__repr__ 泄漏可能漏检。
        self.assertNotIn(raw_prompt, public_summary)  # 新增代码+DesktopTaskRouter：断言完整原始 prompt 不出现在公开摘要中；如果没有这一行，隐私保护回归不会被发现。
        self.assertFalse(public_dict["raw_prompt_included"])  # 新增代码+DesktopTaskRouter：断言公开字典明确标记未包含原始 prompt；如果没有这一行，调用方无法判断结果是否脱敏。
    # 新增代码+DesktopTaskRouter：函数段结束，test_raw_prompt_is_not_exposed_in_public_router_summary 到此结束；如果没有这个边界说明，代码小白不容易看出脱敏测试范围。
# 新增代码+DesktopTaskAcceptance：类段结束，WindowsComputerUseFullDesktopTaskRouterTests 到此结束；如果没有这个边界说明，代码小白不容易看出本文件测试集合已结束。


if __name__ == "__main__":  # 新增代码+DesktopTaskAcceptance：文件入口段开始，允许用户直接运行本测试文件；如果没有这一行，用户必须记住完整 unittest 模块路径。
    unittest.main()  # 新增代码+DesktopTaskAcceptance：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+DesktopTaskAcceptance：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，代码小白不容易看出脚本入口范围。
