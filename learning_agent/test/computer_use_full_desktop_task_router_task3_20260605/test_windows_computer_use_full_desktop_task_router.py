import unittest  # 新增代码+DesktopTaskAcceptance：导入 unittest 测试框架；如果没有这一行，项目现有测试命令就不能发现和运行本回归测试。

from learning_agent.computer_use.desktop_task_acceptance import evaluate_desktop_task_acceptance  # 新增代码+DesktopTaskAcceptance：导入桌面任务验收评估器；如果没有这一行，测试就无法验证脚本绕路会被拒绝。
from learning_agent.computer_use.desktop_task_policy import evaluate_desktop_bash_command  # 新增代码+DesktopTaskPolicy：导入 Task 3 的 bash 命令策略函数；如果没有这一行，本测试文件无法验证桌面任务期间脚本成品路线会被提前拦截。
from learning_agent.computer_use.desktop_task_router import classify_desktop_task  # 新增代码+DesktopTaskRouter：导入 Task 2 的桌面任务意图分类函数；如果没有这一行，本测试文件就无法验证自然语言 prompt 会不会进入桌面任务路线。
from learning_agent.core.agent import LearningAgent, ModelMessage, ToolCallingFakeModel  # 修改代码+DesktopTaskPolicy：导入 LearningAgent 和离线假模型用于真实 run_events 接线测试；如果没有这一行，测试只能手动设置 active，无法证明自然语言桌面任务会自动打开策略上下文。


class WindowsComputerUseFullDesktopTaskRouterTests(unittest.TestCase):  # 新增代码+DesktopTaskAcceptance：类段开始，集中冻结 `/computer use --full` 桌面任务路由验收；如果没有这个类，unittest 不会组织这些回归用例。
    # 新增代码+DesktopTaskPolicy：函数段开始，验证 System.Drawing 加图片保存再打开 Paint 的最终制品路线会被拒绝；如果没有这段测试，Task 3 的核心绕路可能再次复发，作者意图是锁住桌面任务必须走 GUI 路线，本段与 evaluate_desktop_bash_command 配合到断言结束。
    def test_policy_blocks_system_drawing_final_artifact(self) -> None:  # 新增代码+DesktopTaskPolicy：定义 System.Drawing 禁止路线测试；如果没有这一行，unittest 不会执行这条 Task 3 回归。
        result = evaluate_desktop_bash_command(  # 新增代码+DesktopTaskPolicy：调用策略函数评估危险命令；如果没有这一行，断言没有真实策略结果可检查。
            command="Add-Type -AssemblyName System.Drawing; $bmp.Save('x.png'); Start-Process mspaint.exe x.png",  # 新增代码+DesktopTaskPolicy：模拟脚本生成 PNG 并启动 Paint 的绕路命令；如果没有这一行，测试不会覆盖真实失败形态。
            desktop_task_active=True,  # 新增代码+DesktopTaskPolicy：声明当前处于桌面任务上下文；如果没有这一行，策略会按普通命令放行，测试无法验证桌面任务门禁。
        )  # 新增代码+DesktopTaskPolicy：结束策略函数调用；如果没有这一行，Python 调用语法不完整。
        self.assertFalse(result["allowed"])  # 新增代码+DesktopTaskPolicy：断言危险命令不允许执行；如果没有这一行，脚本制品路线可能被错误放行而无人发现。
        self.assertEqual(result["decision"], "desktop_task_requires_gui_route")  # 新增代码+DesktopTaskPolicy：断言拒绝码必须稳定；如果没有这一行，agent 返回文本难以被上层和测试可靠识别。
    # 新增代码+DesktopTaskPolicy：函数段结束，test_policy_blocks_system_drawing_final_artifact 到此结束；如果没有这个边界说明，代码小白不容易看出危险命令测试范围。

    # 新增代码+DesktopTaskPolicy：函数段开始，验证 where.exe mspaint 这类只读诊断命令允许执行；如果没有这段测试，策略可能过度拦截导致 agent 无法检查本地应用是否存在，作者意图是保留安全诊断，本段与 evaluate_desktop_bash_command 配合到断言结束。
    def test_policy_allows_diagnostic_where_command(self) -> None:  # 新增代码+DesktopTaskPolicy：定义 where.exe 诊断放行测试；如果没有这一行，unittest 不会覆盖安全诊断白名单。
        result = evaluate_desktop_bash_command(command="where.exe mspaint", desktop_task_active=True)  # 新增代码+DesktopTaskPolicy：评估 Windows Paint 路径查询命令；如果没有这一行，测试无法证明诊断命令在 active 状态下仍可用。
        self.assertTrue(result["allowed"])  # 新增代码+DesktopTaskPolicy：断言诊断命令允许执行；如果没有这一行，策略可能误伤只读检查而不被发现。
        self.assertEqual(result["decision"], "diagnostic_command_allowed")  # 新增代码+DesktopTaskPolicy：断言诊断放行原因码稳定；如果没有这一行，调用方无法区分白名单诊断和普通 inactive 放行。
    # 新增代码+DesktopTaskPolicy：函数段结束，test_policy_allows_diagnostic_where_command 到此结束；如果没有这个边界说明，代码小白不容易看出诊断放行测试范围。

    # 新增代码+DesktopTaskPolicy：函数段开始，验证桌面任务未激活时同样命令由策略放行；如果没有这段测试，策略可能误伤普通开发命令，作者意图是让门禁只在桌面任务上下文生效，本段与 evaluate_desktop_bash_command 配合到断言结束。
    def test_policy_inactive_allows_same_artifact_command(self) -> None:  # 新增代码+DesktopTaskPolicy：定义 inactive 放行测试；如果没有这一行，unittest 不会覆盖非桌面任务兼容性。
        result = evaluate_desktop_bash_command(  # 新增代码+DesktopTaskPolicy：调用策略函数评估同一条危险形态命令；如果没有这一行，测试无法比较 active 和 inactive 的差异。
            command="Add-Type -AssemblyName System.Drawing; $bmp.Save('x.png'); Start-Process mspaint.exe x.png",  # 新增代码+DesktopTaskPolicy：复用最终图片制品命令；如果没有这一行，inactive 测试无法证明同样命令在普通上下文不会被策略拦截。
            desktop_task_active=False,  # 新增代码+DesktopTaskPolicy：声明桌面任务未激活；如果没有这一行，策略默认可能按 active 测试导致意图不清。
        )  # 新增代码+DesktopTaskPolicy：结束策略函数调用；如果没有这一行，Python 调用语法不完整。
        self.assertTrue(result["allowed"])  # 新增代码+DesktopTaskPolicy：断言 inactive 时策略允许普通命令；如果没有这一行，普通开发命令可能被悄悄拦截。
        self.assertEqual(result["decision"], "desktop_task_policy_inactive")  # 新增代码+DesktopTaskPolicy：断言 inactive 原因码稳定；如果没有这一行，调用方无法知道放行是因为桌面任务门禁没开启。
    # 新增代码+DesktopTaskPolicy：函数段结束，test_policy_inactive_allows_same_artifact_command 到此结束；如果没有这个边界说明，代码小白不容易看出 inactive 兼容测试范围。

    # 新增代码+DesktopTaskPolicy：函数段开始，验证 Get-Command、Get-Process、tasklist 这些只读诊断命令允许执行；如果没有这段测试，策略可能阻断排查 Paint 状态所需的安全观察，作者意图是保留只读桌面诊断，本段与 evaluate_desktop_bash_command 配合到循环断言结束。
    def test_policy_allows_read_only_diagnostics(self) -> None:  # 新增代码+DesktopTaskPolicy：定义多条只读诊断放行测试；如果没有这一行，unittest 不会覆盖建议补充的诊断命令。
        commands = (  # 新增代码+DesktopTaskPolicy：准备只读诊断命令元组；如果没有这一行，循环没有输入样本。
            "Get-Command mspaint",  # 新增代码+DesktopTaskPolicy：覆盖 PowerShell 命令发现；如果没有这一项，Get-Command 可能被误拦截。
            "Get-Process mspaint",  # 新增代码+DesktopTaskPolicy：覆盖只读进程检查；如果没有这一项，进程观察可能被误拦截。
            "tasklist",  # 新增代码+DesktopTaskPolicy：覆盖 Windows 任务列表查看；如果没有这一项，基础只读窗口排查可能被误拦截。
        )  # 新增代码+DesktopTaskPolicy：结束诊断命令元组；如果没有这一行，Python 元组语法不完整。
        for command in commands:  # 新增代码+DesktopTaskPolicy：逐条检查诊断命令；如果没有这一行，只有数据不会实际触发策略。
            with self.subTest(command=command):  # 新增代码+DesktopTaskPolicy：给每条命令单独标记子测试；如果没有这一行，失败时不容易定位是哪条诊断被误拦。
                result = evaluate_desktop_bash_command(command=command, desktop_task_active=True)  # 新增代码+DesktopTaskPolicy：在 active 状态评估当前诊断命令；如果没有这一行，断言没有真实策略结果。
                self.assertTrue(result["allowed"])  # 新增代码+DesktopTaskPolicy：断言只读诊断允许执行；如果没有这一行，策略误伤不会被发现。
                self.assertEqual(result["decision"], "diagnostic_command_allowed")  # 新增代码+DesktopTaskPolicy：断言每条诊断都使用稳定白名单原因码；如果没有这一行，后续展示层无法解释为什么放行。
    # 新增代码+DesktopTaskPolicy：函数段结束，test_policy_allows_read_only_diagnostics 到此结束；如果没有这个边界说明，代码小白不容易看出多诊断测试范围。

    # 新增代码+DesktopTaskPolicy：函数段开始，验证 active 桌面任务里 shell GUI 自动化绕路会被拒绝；如果没有这段测试，模型仍可能不用 Computer Use 而直接用 SendKeys 操作桌面，作者意图是堵住非图片脚本绕路，本段与 evaluate_desktop_bash_command 配合到断言结束。
    def test_policy_blocks_shell_gui_automation_bypass(self) -> None:  # 新增代码+DesktopTaskPolicy：定义 shell GUI 自动化拒绝测试；如果没有这一行，unittest 不会覆盖 SendKeys 这类危险绕路。
        commands = (  # 修改代码+DesktopTaskPolicy：准备多条 shell GUI 自动化绕路样本；如果没有这一行，测试只能覆盖 SendKeys 单点而漏掉其它常见 Win32/API 写法。
            "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('abc')",  # 修改代码+DesktopTaskPolicy：覆盖 Windows Forms SendKeys；如果没有这一项，PowerShell 直接发键盘输入可能复发。
            "$ws = New-Object -ComObject WScript.Shell; $ws.SendKeys('abc')",  # 新增代码+DesktopTaskPolicy：覆盖 WScript.Shell SendKeys；如果没有这一项，COM 自动化发键盘可能绕过 Computer Use。
            "[NativeMethods]::keybd_event(0x41, 0, 0, 0)",  # 新增代码+DesktopTaskPolicy：覆盖 user32 keybd_event；如果没有这一项，旧 Win32 键盘 API 可能漏拦。
            "[NativeMethods]::SetCursorPos(10, 10)",  # 新增代码+DesktopTaskPolicy：覆盖 user32 SetCursorPos；如果没有这一项，shell 可以直接移动鼠标光标绕开坐标审计。
            "[NativeMethods]::SendMessage($hwnd, 0x000C, 0, 'abc')",  # 新增代码+DesktopTaskPolicy：覆盖 user32 SendMessage；如果没有这一项，shell 可以直接向窗口发消息绕开真实低层输入链。
            "[NativeMethods]::PostMessage($hwnd, 0x0100, 0x41, 0)",  # 新增代码+DesktopTaskPolicy：覆盖 user32 PostMessage；如果没有这一项，shell 可以异步向窗口发键盘消息。
            "Import-Module UIAutomation; Get-UIAWindow -Name Paint",  # 新增代码+DesktopTaskPolicy：覆盖 shell 直接加载 UIAutomation；如果没有这一项，脚本可以绕开 Computer Use 的观察-动作闭环。
        )  # 修改代码+DesktopTaskPolicy：shell GUI 自动化样本元组结束；如果没有这一行，Python 元组语法不完整。
        for command in commands:  # 新增代码+DesktopTaskPolicy：逐条验证 GUI 自动化绕路样本；如果没有这一行，表驱动数据不会实际执行。
            with self.subTest(command=command):  # 新增代码+DesktopTaskPolicy：给每条危险命令单独标记子测试；如果没有这一行，失败时不容易定位漏拦 API。
                result = evaluate_desktop_bash_command(command=command, desktop_task_active=True)  # 修改代码+DesktopTaskPolicy：在 active 状态评估当前 shell GUI 自动化命令；如果没有这一行，断言没有真实策略结果可检查。
                self.assertFalse(result["allowed"])  # 修改代码+DesktopTaskPolicy：断言 shell GUI 自动化不允许执行；如果没有这一行，直接操控桌面的脚本路线可能被错误放行。
                self.assertEqual(result["decision"], "desktop_task_requires_gui_route")  # 修改代码+DesktopTaskPolicy：断言拒绝码仍指向 GUI/Computer Use 路线；如果没有这一行，上层难以稳定识别替代路线。
    # 新增代码+DesktopTaskPolicy：函数段结束，test_policy_blocks_shell_gui_automation_bypass 到此结束；如果没有这个边界说明，代码小白不容易看出 shell GUI 自动化测试范围。

    # 新增代码+DesktopTaskPolicy：函数段开始，验证 active 桌面任务里只读图片证据查询不会被误杀；如果没有这段测试，策略可能阻断查看截图或证据文件，作者意图是只拦最终制品路线而保留只读观察，本段与 evaluate_desktop_bash_command 配合到断言结束。
    def test_policy_allows_read_only_image_file_diagnostics(self) -> None:  # 新增代码+DesktopTaskPolicy：定义图片文件只读诊断放行测试；如果没有这一行，unittest 不会覆盖审查指出的 evidence.png 误杀。
        commands = (  # 修改代码+DesktopTaskPolicy：准备多个容易被动作关键词误伤的只读图片查询；如果没有这一行，save.png/convert.png/mspaint.png 这类边界不会被锁住。
            "Get-Item .\\evidence.png",  # 修改代码+DesktopTaskPolicy：覆盖普通证据图片查询；如果没有这一项，最常见 screenshot/evidence 查询可能误杀。
            "Test-Path .\\save.png",  # 新增代码+DesktopTaskPolicy：覆盖文件名包含 save 的只读查询；如果没有这一项，动作关键词出现在文件名里会再次触发误杀。
            "Get-Item -LiteralPath .\\convert.png",  # 新增代码+DesktopTaskPolicy：覆盖 LiteralPath 和 convert 文件名；如果没有这一项，转换相关文件名会被误判成 ImageMagick/convert 动作。
            "Test-Path -Path .\\mspaint.png",  # 新增代码+DesktopTaskPolicy：覆盖 Path 参数和 mspaint 文件名；如果没有这一项，Paint 相关证据文件可能被误判成打开最终制品。
        )  # 修改代码+DesktopTaskPolicy：只读图片查询样本元组结束；如果没有这一行，Python 元组语法不完整。
        for command in commands:  # 新增代码+DesktopTaskPolicy：逐条验证只读图片诊断命令；如果没有这一行，表驱动数据不会实际执行。
            with self.subTest(command=command):  # 新增代码+DesktopTaskPolicy：给每条只读命令单独标记子测试；如果没有这一行，失败时不容易定位哪个文件名被误杀。
                result = evaluate_desktop_bash_command(command=command, desktop_task_active=True)  # 修改代码+DesktopTaskPolicy：评估当前只读查看图片文件命令；如果没有这一行，测试无法证明图片扩展名不会单独触发拒绝。
                self.assertTrue(result["allowed"])  # 修改代码+DesktopTaskPolicy：断言只读图片诊断允许执行；如果没有这一行，策略误杀仍可能存在。
                self.assertEqual(result["decision"], "diagnostic_command_allowed")  # 修改代码+DesktopTaskPolicy：断言该命令按诊断白名单放行；如果没有这一行，后续难以区分只读观察和普通 active 放行。
    # 新增代码+DesktopTaskPolicy：函数段结束，test_policy_allows_read_only_image_file_diagnostics 到此结束；如果没有这个边界说明，代码小白不容易看出图片诊断测试范围。

    # 新增代码+DesktopTaskPolicy：函数段开始，验证诊断白名单不会放行 PowerShell 子表达式或括号副作用；如果没有这段测试，危险命令可以伪装进 tasklist/Get-Item/Test-Path 参数里绕过策略，作者意图是把只读诊断限制成简单安全形状，本段与 evaluate_desktop_bash_command 配合到断言结束。
    def test_policy_blocks_diagnostic_argument_injection(self) -> None:  # 新增代码+DesktopTaskPolicy：定义诊断参数注入拒绝测试；如果没有这一行，unittest 不会覆盖 diagnostic-first 放行顺序的绕过风险。
        commands = (  # 新增代码+DesktopTaskPolicy：准备会伪装成诊断命令的 PowerShell 注入样本；如果没有这一行，审查指出的漏洞没有长期回归保护。
            "tasklist /fi $(Set-Content .\\pwn.txt hi)",  # 新增代码+DesktopTaskPolicy：覆盖 tasklist 参数里的子表达式注入；如果没有这一项，进程诊断白名单可能执行隐藏写文件。
            "Get-Item $(Set-Content .\\pwn.png hi).png",  # 新增代码+DesktopTaskPolicy：覆盖 Get-Item 路径里的子表达式注入；如果没有这一项，只读文件查询可能变成写文件。
            "Test-Path $(New-Item .\\pwn.png -ItemType File).png",  # 新增代码+DesktopTaskPolicy：覆盖 Test-Path 路径里的 New-Item 注入；如果没有这一项，路径检测可能变成创建最终制品。
            "Get-Item (Set-Content .\\pwn.png hi) .\\save.png",  # 新增代码+DesktopTaskPolicy：覆盖括号表达式注入；如果没有这一项，普通括号副作用可能绕过 diagnostic-first 顺序。
            "Get-Item `[Set-Content .\\pwn.png hi`].png",  # 新增代码+DesktopTaskPolicy：覆盖反引号和方括号混合的可疑表达式；如果没有这一项，复杂 PowerShell 语法可能进入只读白名单。
            "Get-Item .\\evidence.png; Set-Content .\\pwn.txt hi",  # 新增代码+DesktopTaskPolicy：覆盖分号追加副作用命令；如果没有这一项，诊断命令后面可以接写文件绕过策略。
            "Get-Item .\\evidence.png && Set-Content .\\pwn.txt hi",  # 新增代码+DesktopTaskPolicy：覆盖 && 追加副作用命令；如果没有这一项，诊断成功后继续执行写文件会漏拦。
            "tasklist | Set-Content .\\pwn.txt",  # 新增代码+DesktopTaskPolicy：覆盖管道把诊断输出写入文件；如果没有这一项，只读进程查询可能被变成文件写入。
            "Test-Path .\\evidence.png > .\\pwn.txt",  # 新增代码+DesktopTaskPolicy：覆盖重定向写文件；如果没有这一项，路径检测可能通过 > 产生副作用文件。
            "Get-Item .\\evidence.png\nSet-Content .\\pwn.txt hi",  # 新增代码+DesktopTaskPolicy：覆盖换行追加副作用命令；如果没有这一项，归一化后的空格会隐藏多命令风险。
        )  # 新增代码+DesktopTaskPolicy：注入样本元组结束；如果没有这一行，Python 元组语法不完整。
        for command in commands:  # 新增代码+DesktopTaskPolicy：逐条验证诊断注入样本；如果没有这一行，表驱动样本不会实际执行。
            with self.subTest(command=command):  # 新增代码+DesktopTaskPolicy：给每条注入命令单独标记子测试；如果没有这一行，失败时不容易定位哪类注入漏拦。
                result = evaluate_desktop_bash_command(command=command, desktop_task_active=True)  # 新增代码+DesktopTaskPolicy：在 active 状态评估当前伪装诊断命令；如果没有这一行，断言没有真实策略结果。
                self.assertFalse(result["allowed"])  # 新增代码+DesktopTaskPolicy：断言含子表达式或括号副作用的诊断命令不允许执行；如果没有这一行，diagnostic-first 漏洞可能复发。
                self.assertEqual(result["decision"], "desktop_task_requires_gui_route")  # 新增代码+DesktopTaskPolicy：断言拒绝码保持稳定；如果没有这一行，上层无法可靠提示必须改走 GUI/Computer Use。
    # 新增代码+DesktopTaskPolicy：函数段结束，test_policy_blocks_diagnostic_argument_injection 到此结束；如果没有这个边界说明，代码小白不容易看出诊断注入测试范围。

    # 新增代码+DesktopTaskPolicy：函数段开始，验证自然语言桌面任务进入 run_events 时会自动设置并清理 desktop task context；如果没有这段测试，真实 `/computer use --full` 后普通 prompt 仍可能永远 active=False，作者意图是锁住真实运行路径，本段与 LearningAgent.run_events 配合到断言结束。
    def test_run_events_sets_and_restores_desktop_task_context_for_prompt(self) -> None:  # 新增代码+DesktopTaskPolicy：定义真实运行路径上下文生命周期测试；如果没有这一行，unittest 不会覆盖非 monkeypatch 的 active 接线。
        import tempfile  # 新增代码+DesktopTaskPolicy：导入临时目录工具隔离 run_events 写入的 memory 文件；如果没有这一行，测试可能污染真实工作区。
        from pathlib import Path  # 新增代码+DesktopTaskPolicy：导入 Path 方便构造 workspace 路径；如果没有这一行，路径拼接会退回脆弱字符串。

        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DesktopTaskPolicy：创建临时工作区；如果没有这一行，run_events 会写入真实项目 memory。
            workspace = Path(raw_dir)  # 新增代码+DesktopTaskPolicy：把临时目录转成 Path；如果没有这一行，LearningAgent 构造参数类型不够清晰。
            captured_contexts: list[dict[str, object]] = []  # 新增代码+DesktopTaskPolicy：保存模型调用时看到的 desktop context；如果没有这一行，测试无法证明模型/工具循环期间 active 已经打开。

            class ContextRecordingFakeModel:  # 新增代码+DesktopTaskPolicy：类段开始，定义能记录 agent context 的离线假模型；如果没有这个类，测试只能调用真实模型或无法观察运行中状态。
                def __init__(self, agent: LearningAgent) -> None:  # 新增代码+DesktopTaskPolicy：初始化假模型并接收待观察 agent；如果没有这一行，fake model 不知道该读取哪个对象。
                    self.agent = agent  # 新增代码+DesktopTaskPolicy：保存 agent 引用；如果没有这一行，chat 时无法读取 desktop_task_context。

                def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码+DesktopTaskPolicy：模拟模型 chat 接口；如果没有这一行，run_events 无法调用这个假模型。
                    del messages, tools  # 新增代码+DesktopTaskPolicy：声明本测试不关心消息和工具 schema；如果没有这一行，未使用参数会让测试意图不清楚。
                    captured_contexts.append(dict(self.agent.desktop_task_context))  # 新增代码+DesktopTaskPolicy：记录模型调用时的 desktop context；如果没有这一行，测试无法证明 active 生命周期在模型前已经生效。
                    return ModelMessage(text="桌面任务上下文已检查。")  # 新增代码+DesktopTaskPolicy：返回无工具最终答案让 run_events 正常结束；如果没有这一行，事件流无法自然完成。
            # 新增代码+DesktopTaskPolicy：类段结束，ContextRecordingFakeModel 到此结束；如果没有这个边界说明，代码小白不容易看出 fake model 范围。

            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="占位")]), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+DesktopTaskPolicy：创建真实 agent 但使用离线假模型；如果没有这一行，测试没有生产 run_events 主体。
            agent.model = ContextRecordingFakeModel(agent)  # 新增代码+DesktopTaskPolicy：替换为能观察 context 的假模型；如果没有这一行，测试无法在模型调用时捕获 active 状态。
            events = list(agent.run_events("请使用本地电脑的画图软件画一个皮卡丘。", max_turns=1))  # 新增代码+DesktopTaskPolicy：用真实用户风格 prompt 运行事件流；如果没有这一行，active 接线不会被真实触发。
            completed_texts = [event.payload.get("text", "") for event in events if event.event_type == "run_completed"]  # 新增代码+DesktopTaskPolicy：收集完成事件文本；如果没有这一行，测试无法确认事件流自然结束。
            self.assertIn("桌面任务上下文已检查。", completed_texts)  # 新增代码+DesktopTaskPolicy：断言离线模型最终答案进入完成事件；如果没有这一行，测试可能在异常路径也误判通过。
            self.assertTrue(captured_contexts and bool(captured_contexts[0].get("active")))  # 新增代码+DesktopTaskPolicy：断言模型运行时 desktop task context 已经 active；如果没有这一行，审查指出的真实接线缺口不会被锁住。
            self.assertFalse(agent.desktop_task_context.get("active", True))  # 新增代码+DesktopTaskPolicy：断言 run_events 结束后 context 已恢复 inactive；如果没有这一行，下一轮普通任务可能被污染成桌面任务。
    # 新增代码+DesktopTaskPolicy：函数段结束，test_run_events_sets_and_restores_desktop_task_context_for_prompt 到此结束；如果没有这个边界说明，代码小白不容易看出上下文生命周期测试范围。

    # 新增代码+DesktopTaskPolicy：函数段开始，验证 run_events 即使模型阶段异常也会恢复 desktop task context；如果没有这段测试，异常失败后 active 可能泄漏到下一轮，作者意图是锁住 finally 清理路径，本段与 LearningAgent.run_events 配合到断言结束。
    def test_run_events_restores_desktop_task_context_after_model_failure(self) -> None:  # 新增代码+DesktopTaskPolicy：定义异常恢复生命周期测试；如果没有这一行，unittest 不会覆盖 run_failed 路径的 context 清理。
        import tempfile  # 新增代码+DesktopTaskPolicy：导入临时目录工具隔离 run_events 写入的 memory 文件；如果没有这一行，测试可能污染真实工作区。
        from pathlib import Path  # 新增代码+DesktopTaskPolicy：导入 Path 方便构造 workspace 路径；如果没有这一行，路径拼接会退回脆弱字符串。

        class FailingDesktopTaskFakeModel:  # 新增代码+DesktopTaskPolicy：类段开始，定义模型调用时故意失败的离线假模型；如果没有这个类，测试无法稳定触发 run_failed 分支。
            def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码+DesktopTaskPolicy：模拟模型 chat 接口并抛出异常；如果没有这一行，run_events 无法调用 fake model。
                del messages, tools  # 新增代码+DesktopTaskPolicy：声明本测试不关心消息和工具 schema；如果没有这一行，未使用参数会让测试意图不清楚。
                raise RuntimeError("fake model failure for desktop context cleanup")  # 新增代码+DesktopTaskPolicy：触发外层 run_failed 路径；如果没有这一行，测试无法证明异常后 finally 会恢复上下文。
        # 新增代码+DesktopTaskPolicy：类段结束，FailingDesktopTaskFakeModel 到此结束；如果没有这个边界说明，代码小白不容易看出失败模型范围。

        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DesktopTaskPolicy：创建临时工作区；如果没有这一行，run_events 会写入真实项目 memory。
            workspace = Path(raw_dir)  # 新增代码+DesktopTaskPolicy：把临时目录转成 Path；如果没有这一行，LearningAgent 构造参数类型不够清晰。
            agent = LearningAgent(model=FailingDesktopTaskFakeModel(), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+DesktopTaskPolicy：创建使用失败 fake model 的真实 agent；如果没有这一行，测试没有生产 run_events 主体。
            events = list(agent.run_events("请使用本地电脑的画图软件画一个皮卡丘。", max_turns=1))  # 新增代码+DesktopTaskPolicy：用桌面任务 prompt 触发 active 后进入失败路径；如果没有这一行，异常恢复逻辑不会被真实执行。
            self.assertIn("run_failed", {event.event_type for event in events})  # 新增代码+DesktopTaskPolicy：断言测试确实走到失败事件；如果没有这一行，正常完成也可能误判成覆盖了异常路径。
            self.assertFalse(agent.desktop_task_context.get("active", True))  # 新增代码+DesktopTaskPolicy：断言异常后 context 已恢复 inactive；如果没有这一行，失败任务会污染下一轮普通 bash 策略。
    # 新增代码+DesktopTaskPolicy：函数段结束，test_run_events_restores_desktop_task_context_after_model_failure 到此结束；如果没有这个边界说明，代码小白不容易看出异常清理测试范围。

    # 新增代码+DesktopTaskPolicy：函数段开始，验证 `_bash_atom` 在请求权限和执行命令前拦截桌面任务脚本制品路线；如果没有这段测试，策略模块通过也不能证明 agent 已接线，作者意图是防止真实命令和 ask_permission 被触发，本段与 LearningAgent._bash_atom 配合到断言结束。
    def test_agent_bash_atom_rejects_desktop_script_artifact_before_permission(self) -> None:  # 新增代码+DesktopTaskPolicy：定义 agent 集成拒绝测试；如果没有这一行，unittest 不会验证核心执行入口。
        agent = LearningAgent.__new__(LearningAgent)  # 新增代码+DesktopTaskPolicy：不调用 __init__ 构造轻量 agent；如果没有这一行，测试会初始化真实 workspace 和控制器，偏离本任务要求。
        agent.desktop_task_context = {"active": True}  # 新增代码+DesktopTaskPolicy：手动设置桌面任务上下文为 active；如果没有这一行，_bash_atom 不会进入 Task 3 策略门禁。
        agent.workspace = None  # 新增代码+DesktopTaskPolicy：把 workspace 设为 None 来证明拒绝发生在解析工作区前；如果没有这一行，测试无法确认没有依赖真实 workspace。
        agent._resolve_workspace_path = lambda raw_cwd: (_ for _ in ()).throw(AssertionError("workspace should not be resolved"))  # 新增代码+DesktopTaskPolicy：放置工作区解析哨兵；如果没有这一行，_bash_atom 可能先解析路径再拦截而测试发现不了。
        agent.ask_permission = lambda action: (_ for _ in ()).throw(AssertionError("ask_permission should not be called"))  # 新增代码+DesktopTaskPolicy：放置权限请求哨兵；如果没有这一行，测试无法证明拒绝发生在请求权限之前。
        output = agent._bash_atom(  # 新增代码+DesktopTaskPolicy：调用 bash 原子工具入口；如果没有这一行，集成测试不会触发被测 agent 代码。
            {  # 新增代码+DesktopTaskPolicy：参数字典段开始，模拟模型传入危险命令；如果没有这一行，_bash_atom 没有输入参数。
                "command": "Add-Type -AssemblyName System.Drawing; $bmp.Save('x.png'); Start-Process mspaint.exe x.png",  # 新增代码+DesktopTaskPolicy：传入脚本制品绕路命令；如果没有这一行，集成测试不会覆盖 Task 3 拒绝场景。
            }  # 新增代码+DesktopTaskPolicy：参数字典段结束；如果没有这一行，Python 字典语法不完整。
        )  # 新增代码+DesktopTaskPolicy：结束 _bash_atom 调用；如果没有这一行，Python 调用语法不完整。
        self.assertIn("desktop_task_requires_gui_route", output)  # 新增代码+DesktopTaskPolicy：断言 agent 返回清晰拒绝码；如果没有这一行，模型和用户可能看不到必须走 GUI 路线的原因。
    # 新增代码+DesktopTaskPolicy：函数段结束，test_agent_bash_atom_rejects_desktop_script_artifact_before_permission 到此结束；如果没有这个边界说明，代码小白不容易看出 agent 集成测试范围。

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

    def test_chinese_non_operational_paint_mentions_do_not_route(self) -> None:  # 新增代码+DesktopTaskRouter：函数段开始，验证中文只提到画图知识/介绍/技巧时不会进入桌面任务；如果没有这个测试，画图应用名里的单字“画”会继续制造误路由。
        prompts = [  # 新增代码+DesktopTaskRouter：准备中文非操作性画图样本；如果没有这一行，审查指出的中文误报不会被系统覆盖。
            "画图是什么软件",  # 新增代码+DesktopTaskRouter：覆盖询问软件是什么的知识问题；如果没有这一行，画图应用名可能被误当成打开或绘制动作。
            "介绍一下 Windows 画图",  # 新增代码+DesktopTaskRouter：覆盖 Windows 画图介绍请求；如果没有这一行，介绍类请求可能被误送 GUI 路线。
            "学习画图技巧",  # 新增代码+DesktopTaskRouter：覆盖学习技巧请求；如果没有这一行，学习类内容可能被误判为本地桌面操作。
            "请教我画图技巧",  # 新增代码+DesktopTaskRouter：覆盖请教技巧请求；如果没有这一行，教学类内容可能被误判为真实桌面任务。
        ]  # 新增代码+DesktopTaskRouter：结束中文非操作样本列表；如果没有这一行，测试数据结构不是合法 Python 列表。
        for prompt in prompts:  # 新增代码+DesktopTaskRouter：逐个验证中文负例；如果没有这一行，样本列表不会被实际测试。
            with self.subTest(prompt=prompt):  # 新增代码+DesktopTaskRouter：给每个中文负例单独标记子测试；如果没有这一行，失败时不容易定位具体误报句子。
                intent = classify_desktop_task(prompt)  # 新增代码+DesktopTaskRouter：调用分类器处理当前中文负例；如果没有这一行，断言没有被测分类结果。
                self.assertFalse(intent.is_desktop_task)  # 新增代码+DesktopTaskRouter：断言非操作性画图问题不是桌面任务；如果没有这一行，中文画图误报修复不会被锁住。
    # 新增代码+DesktopTaskRouter：函数段结束，test_chinese_non_operational_paint_mentions_do_not_route 到此结束；如果没有这个边界说明，代码小白不容易看出中文画图负例范围。

    def test_english_painting_and_script_mentions_do_not_route(self) -> None:  # 新增代码+DesktopTaskRouter：函数段开始，验证 painting/script 文字请求不会因为 paint 子串误入桌面任务；如果没有这个测试，英文 paint 裸子串误报会复发。
        prompts = [  # 新增代码+DesktopTaskRouter：准备英文 paint 子串误报样本；如果没有这一行，painting 相关负例不会被覆盖。
            "Tell me painting tips",  # 新增代码+DesktopTaskRouter：覆盖 painting 技巧请求；如果没有这一行，painting 里的 paint 子串可能继续触发 Paint 任务。
            "Please generate a painting script",  # 新增代码+DesktopTaskRouter：覆盖生成 painting script 请求；如果没有这一行，脚本/内容生成请求可能被误判为 GUI 操作。
        ]  # 新增代码+DesktopTaskRouter：结束英文 paint 子串负例列表；如果没有这一行，测试数据结构不是合法 Python 列表。
        for prompt in prompts:  # 新增代码+DesktopTaskRouter：逐个验证英文负例；如果没有这一行，样本列表不会被实际测试。
            with self.subTest(prompt=prompt):  # 新增代码+DesktopTaskRouter：给每个英文负例单独标记子测试；如果没有这一行，失败时不容易定位具体误报句子。
                intent = classify_desktop_task(prompt)  # 新增代码+DesktopTaskRouter：调用分类器处理当前英文负例；如果没有这一行，断言没有被测分类结果。
                self.assertFalse(intent.is_desktop_task)  # 新增代码+DesktopTaskRouter：断言 painting/script 内容请求不是桌面任务；如果没有这一行，英文 paint 子串误报修复不会被锁住。
    # 新增代码+DesktopTaskRouter：函数段结束，test_english_painting_and_script_mentions_do_not_route 到此结束；如果没有这个边界说明，代码小白不容易看出英文 paint 子串负例范围。

    def test_english_word_boundaries_avoid_contest_and_happy_substring_errors(self) -> None:  # 新增代码+DesktopTaskRouter：函数段开始，验证英文关键词按词边界匹配而不是裸子串；如果没有这个测试，test 命中 contest、app 命中 happy 的问题会复发。
        contest_intent = classify_desktop_task("Open Contest Manager on my computer")  # 新增代码+DesktopTaskRouter：调用分类器处理 Contest Manager 本地打开请求；如果没有这一行，test 子串保护误拒无法被发现。
        self.assertNotEqual(contest_intent.reason, "protected_non_desktop_development_request")  # 新增代码+DesktopTaskRouter：断言 Contest 不会被 test 子串当成开发类保护；如果没有这一行，审查指出的 Contest 阻塞问题可能继续存在。
        happy_intent = classify_desktop_task("I am happy on my computer, start a timer")  # 新增代码+DesktopTaskRouter：调用分类器处理 happy 句子；如果没有这一行，app 子串误命中无法被发现。
        self.assertFalse(happy_intent.is_desktop_task)  # 新增代码+DesktopTaskRouter：断言 happy 中的 app 不会导致桌面任务误判；如果没有这一行，普通情绪句可能被错误送去 GUI 路线。
    # 新增代码+DesktopTaskRouter：函数段结束，test_english_word_boundaries_avoid_contest_and_happy_substring_errors 到此结束；如果没有这个边界说明，代码小白不容易看出英文词边界负例范围。

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
