import json  # 新增代码+ModelLoopComputerUse：导入 JSON 序列化工具用于把底层 desktop runtime 报告转成可断言文本；如果没有这一行，运行到 runtime adapter 测试时会因为 json 未定义而失败。
import unittest  # 新增代码+DesktopTaskAcceptance：导入 unittest 测试框架；如果没有这一行，项目现有测试命令就不能发现和运行本回归测试。
from typing import Any  # 新增代码+源码复核门禁：导入 Any 给 fake 真实执行闭环标注动态报告；如果没有这一行，新增测试里的类型标注会报错。

from learning_agent.computer_use.desktop_task_acceptance import evaluate_desktop_task_acceptance  # 新增代码+DesktopTaskAcceptance：导入桌面任务验收评估器；如果没有这一行，测试就无法验证脚本绕路会被拒绝。
from learning_agent.computer_use.desktop_task_policy import evaluate_desktop_bash_command  # 新增代码+DesktopTaskPolicy：导入 Task 3 的 bash 命令策略函数；如果没有这一行，本测试文件无法验证桌面任务期间脚本成品路线会被提前拦截。
from learning_agent.computer_use.desktop_task_router import classify_desktop_task  # 新增代码+DesktopTaskRouter：导入 Task 2 的桌面任务意图分类函数；如果没有这一行，本测试文件就无法验证自然语言 prompt 会不会进入桌面任务路线。
from learning_agent.computer_use.desktop_task_runtime import ComputerUseDesktopTaskRuntime, computer_use_full_desktop_task_runtime_cli_line  # 新增代码+DesktopTaskRuntime：导入 Task 4 桌面任务运行时和稳定终端输出函数；如果没有这一行，测试无法证明自然语言桌面任务会进入 Computer Use GUI 证据链。
from learning_agent.computer_use.drawing_primitives import build_pikachu_drag_plan, expand_drag_path_to_low_level_events  # 新增代码+DrawingPrimitives：导入 Task 6 通用绘图 primitive；如果没有这一行，本测试文件无法证明皮卡丘绘制不再藏在固定矩阵里。
from learning_agent.computer_use.generic_input_actions import Phase71RecordingInputSender, WindowsGenericInputActionRuntime  # 新增代码+DrawingPrimitives：导入通用输入 runtime 验证 drag_path 仍走身份门禁；如果没有这一行，Task 6 可能只生成计划但不接动作层。
from learning_agent.computer_use.sendinput_dispatcher import Phase47RecordingLowLevelSender, WindowsSendInputDispatcher  # 新增代码+DrawingPrimitives：导入 SendInput dispatcher 验证 drag_path 能展开到底层鼠标事件；如果没有这一行，Task 6 可能停在高层 JSON。
from learning_agent.core.agent import LearningAgent, ModelMessage, ToolCallingFakeModel  # 修改代码+DesktopTaskPolicy：导入 LearningAgent 和离线假模型用于真实 run_events 接线测试；如果没有这一行，测试只能手动设置 active，无法证明自然语言桌面任务会自动打开策略上下文。

class FakeRealExecutionLoopForAgentRoute:  # 新增代码+源码复核门禁：类段开始，给 agent 主路由测试提供安全 fake 真实执行闭环；如果没有这个类，测试只能触碰真实桌面或无法证明 real_actions=True 正向路径。
    def run_desktop_task(self, target_app: str, prompt: str) -> dict[str, Any]:  # 新增代码+源码复核门禁：函数段开始，返回真实执行形状的脱敏报告；如果没有这段函数，desktop runtime 无法调用注入闭环。
        return {"ok": True, "decision": "agent_route_real_execution_loop_used", "target_app": target_app, "prompt_length": len(prompt), "computer_use_gui_route_used": True, "owned_window_verified": True, "real_target_launch_enabled": True, "real_launch_performed": True, "backend_launch_performed": True, "process_started": True, "owned_process_registered": True, "visible_window_verified": True, "gui_action_count": 1, "low_level_event_count": 3, "real_dispatch_performed": True, "real_desktop_touched": True, "recording_mode": False, "post_action_screenshot_exists": True, "forbidden_script_generation_used": False, "bash_final_artifact_route_used": False, "forbidden_script_artifact_route_blocked": True}  # 修改代码+RealLaunchTargetSession：返回可让汇总门禁通过的真实动作和 agent 自有启动字段；如果没有这一行，agent 主路由正向测试只能证明派发，不能证明 agent 自己打开软件。
    # 新增代码+源码复核门禁：函数段结束，FakeRealExecutionLoopForAgentRoute.run_desktop_task 到此结束；如果没有这个边界说明，初学者不容易看出 fake 闭环范围。
# 新增代码+源码复核门禁：类段结束，FakeRealExecutionLoopForAgentRoute 到此结束；如果没有这个边界说明，初学者不容易看出 fake 闭环范围。


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
    def test_runtime_requires_full_mode_for_gui_task(self) -> None:  # 新增代码+DesktopTaskRuntime：函数段开始，验证 GUI 桌面任务必须先进入 full mode；如果没有这个测试，普通模式可能误触发本机 GUI 控制。
        runtime = ComputerUseDesktopTaskRuntime.for_test(full_mode=False)  # 新增代码+DesktopTaskRuntime：创建未开启 full 的测试运行时；如果没有这一行，断言没有明确的未授权场景。
        report = runtime.run_prompt("请使用本地电脑的画图软件画一个皮卡丘。", real_actions=False)  # 新增代码+DesktopTaskRuntime：用真实用户习惯的中文 prompt 运行录制模式；如果没有这一行，测试不会覆盖用户最关心的 Paint/Pikachu 入口。
        self.assertFalse(report["passed"])  # 新增代码+DesktopTaskRuntime：断言未授权时不能通过；如果没有这一行，full mode 门禁失效可能无人发现。
        self.assertEqual(report["decision"], "computer_use_full_mode_required")  # 新增代码+DesktopTaskRuntime：断言拒绝原因是需要 full mode；如果没有这一行，上层无法稳定提示用户如何开启权限。
        self.assertTrue(report["desktop_task_router_used"])  # 新增代码+DesktopTaskRuntime：断言桌面任务路由已识别该 prompt；如果没有这一行，失败可能被误解成分类器没工作。
        self.assertFalse(report["computer_use_gui_route_used"])  # 新增代码+DesktopTaskRuntime：断言未授权时不会进入 GUI 路由；如果没有这一行，未授权也可能生成动作证据。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+DesktopTaskRuntime：断言单元测试不触碰真实桌面；如果没有这一行，自动测试可能误打开本机应用。
    # 新增代码+DesktopTaskRuntime：函数段结束，test_runtime_requires_full_mode_for_gui_task 到此结束；如果没有这个边界说明，代码小白不容易看出 full mode 门禁测试范围。

    def test_runtime_builds_gui_route_evidence_in_recording_mode(self) -> None:  # 新增代码+DesktopTaskRuntime：函数段开始，验证 full mode 录制模式能生成 GUI 路由证据链；如果没有这个测试，Task 4 可能只停留在权限开关而没有运行时证据。
        runtime = ComputerUseDesktopTaskRuntime.for_test(full_mode=True)  # 新增代码+DesktopTaskRuntime：创建已开启 full 的测试运行时；如果没有这一行，正向 GUI 证据路径无法被触发。
        report = runtime.run_prompt("请使用本地电脑的画图软件画一个皮卡丘。", real_actions=False)  # 新增代码+DesktopTaskRuntime：用中文 Paint/Pikachu prompt 运行录制模式；如果没有这一行，运行时不会生成代表性绘图证据。
        cli_line = computer_use_full_desktop_task_runtime_cli_line(report)  # 新增代码+DesktopTaskRuntime：把报告转成稳定 token 行；如果没有这一行，真实终端验收无法复用同一格式。
        self.assertTrue(report["desktop_task_router_used"])  # 新增代码+DesktopTaskRuntime：断言自然语言桌面任务路由已生效；如果没有这一行，普通 prompt 可能仍绕回文本/脚本路线。
        self.assertTrue(report["computer_use_gui_route_used"])  # 新增代码+DesktopTaskRuntime：断言运行时走的是 GUI Computer Use 路由；如果没有这一行，脚本替代路线可能再次混入。
        self.assertFalse(report["forbidden_script_generation_used"])  # 新增代码+DesktopTaskRuntime：断言未使用脚本生成最终图像；如果没有这一行，之前失败根因可能复发。
        self.assertTrue(report["owned_window_verified"])  # 新增代码+DesktopTaskRuntime：断言记录型窗口身份被验证；如果没有这一行，后续 GUI 动作可能缺目标绑定。
        self.assertGreater(report["gui_action_count"], 0)  # 新增代码+DesktopTaskRuntime：断言 GUI 动作数量大于零；如果没有这一行，空动作也可能被误判为完成。
        self.assertGreater(report["low_level_event_count"], 0)  # 新增代码+DesktopTaskRuntime：断言底层事件数量大于零；如果没有这一行，真实输入链路证据可能缺失。
        self.assertIn("COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_READY", cli_line)  # 新增代码+DesktopTaskRuntime：断言稳定 ready token 出现在终端行；如果没有这一行，controller 难以识别 Task 4 输出。
        self.assertIn("COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK", cli_line)  # 新增代码+DesktopTaskRuntime：断言通过时输出 OK token；如果没有这一行，失败和成功在终端里不易区分。
        self.assertIn("computer_use_gui_route_used=true", cli_line)  # 新增代码+DesktopTaskRuntime：断言终端行明示 GUI 路由；如果没有这一行，用户看不到是否真的走 Computer Use。
        self.assertIn("forbidden_script_artifact_route_blocked=true", cli_line)  # 新增代码+DesktopTaskRuntime：断言终端行明示脚本绕路被阻断；如果没有这一行，根因修复无法被可见验收读取。
    # 新增代码+DesktopTaskRuntime：函数段结束，test_runtime_builds_gui_route_evidence_in_recording_mode 到此结束；如果没有这个边界说明，代码小白不容易看出运行时正向证据测试范围。

    def test_cli_line_exposes_agent_owned_real_launch_tokens(self) -> None:  # 新增代码+RealLaunchTargetSession：函数段开始，验证短 token 行暴露 agent 自己启动和绑定窗口证据；如果没有这个测试，真实终端验收会继续依赖长 JSON 容易误判。
        report = {"passed": True, "desktop_task_router_used": True, "natural_language_desktop_tasks_route_to_computer_use": True, "computer_use_gui_route_used": True, "forbidden_script_artifact_route_blocked": True, "full_mode_session_used": True, "owned_window_verified": True, "real_target_launch_enabled": True, "real_launch_performed": True, "backend_launch_performed": True, "process_started": True, "owned_process_registered": True, "visible_window_verified": True, "gui_action_count": 2, "low_level_event_count": 5, "real_desktop_touched": True}  # 新增代码+RealLaunchTargetSession：构造通过且包含真实启动字段的报告；如果没有这一行，CLI token 测试没有事实输入。
        cli_line = computer_use_full_desktop_task_runtime_cli_line(report)  # 新增代码+RealLaunchTargetSession：把报告转成真实终端会看到的短行；如果没有这一行，断言无法覆盖可见输出。
        self.assertIn("real_target_launch_enabled=true", cli_line)  # 新增代码+RealLaunchTargetSession：断言短行说明已要求真实启动目标；如果没有这一行，用户无法区分是否启用 agent 自己打开软件。
        self.assertIn("real_launch_performed=true", cli_line)  # 新增代码+RealLaunchTargetSession：断言短行说明确实走了真实启动；如果没有这一行，用户手动打开窗口可能再次混淆验收。
        self.assertIn("backend_launch_performed=true", cli_line)  # 新增代码+RealLaunchTargetSession：断言短行说明最后一跳 launcher 被触达；如果没有这一行，启动计划停在纸面也可能被误解。
        self.assertIn("process_started=true", cli_line)  # 新增代码+RealLaunchTargetSession：断言短行说明进程已启动；如果没有这一行，窗口身份没有 pid 基准。
        self.assertIn("owned_process_registered=true", cli_line)  # 新增代码+RealLaunchTargetSession：断言短行说明进程登记为 agent 自有；如果没有这一行，用户已有进程可能再次被误用。
        self.assertIn("visible_window_verified=true", cli_line)  # 新增代码+RealLaunchTargetSession：断言短行说明启动进程的窗口可见且已绑定；如果没有这一行，动作可能没有真实目标窗口。
    # 新增代码+RealLaunchTargetSession：函数段结束，test_cli_line_exposes_agent_owned_real_launch_tokens 到此结束；如果没有这个边界说明，代码小白不容易看出真实启动 token 覆盖范围。

    def test_runtime_real_actions_uses_injected_real_execution_loop(self) -> None:  # 新增代码+源码复核门禁：函数段开始，验证 real_actions=True 进入可注入真实执行闭环；如果没有这个测试，运行时会继续直接拒绝真实动作。
        class FakeRealExecutionLoop:  # 新增代码+源码复核门禁：类段开始，模拟已经安全验证过的真实执行闭环；如果没有这个类，单测只能触碰真实桌面。
            def run_desktop_task(self, target_app: str, prompt: str) -> dict[str, Any]:  # 新增代码+源码复核门禁：函数段开始，返回真实执行形状的报告；如果没有这段函数，desktop runtime 没有可注入接口。
                return {"ok": True, "decision": "real_desktop_task_executed_by_injected_loop", "target_app": target_app, "prompt_length": len(prompt), "computer_use_gui_route_used": True, "owned_window_verified": True, "real_target_launch_enabled": True, "real_launch_performed": True, "backend_launch_performed": True, "process_started": True, "owned_process_registered": True, "visible_window_verified": True, "gui_action_count": 1, "low_level_event_count": 3, "real_dispatch_performed": True, "real_desktop_touched": True, "recording_mode": False, "post_action_screenshot_exists": True, "forbidden_script_generation_used": False, "bash_final_artifact_route_used": False, "forbidden_script_artifact_route_blocked": True}  # 修改代码+RealLaunchTargetSession：返回脱敏真实执行和 agent 自有启动摘要；如果没有这一行，运行时无法汇总自己打开目标软件的事实。
            # 新增代码+源码复核门禁：函数段结束，FakeRealExecutionLoop.run_desktop_task 到此结束；如果没有这个边界说明，初学者不容易看出 fake loop 范围。
        # 新增代码+源码复核门禁：类段结束，FakeRealExecutionLoop 到此结束；如果没有这个边界说明，初学者不容易看出 fake loop 范围。
        runtime = ComputerUseDesktopTaskRuntime.for_test(full_mode=True)  # 新增代码+源码复核门禁：创建已开启 full 的隔离运行时；如果没有这一行，真实动作路径会被权限门禁拦住。
        runtime.real_execution_loop = FakeRealExecutionLoop()  # 新增代码+源码复核门禁：注入安全 fake 真实执行闭环；如果没有这一行，测试会依赖真实桌面。
        report = runtime.run_prompt("请使用本地电脑的画图软件画一个皮卡丘。", real_actions=True)  # 新增代码+源码复核门禁：请求真实动作路径；如果没有这一行，硬拒绝问题不会被触发。
        self.assertTrue(report["passed"])  # 新增代码+源码复核门禁：断言注入真实闭环后报告通过；如果没有这一行，局部字段成功可能掩盖整体失败。
        self.assertEqual("real_desktop_task_executed_by_injected_loop", report["decision"])  # 新增代码+源码复核门禁：断言不再返回 recording_runtime 未启用；如果没有这一行，旧硬拒绝可能悄悄复发。
        self.assertTrue(report["real_actions_supported"])  # 新增代码+源码复核门禁：断言运行时声明支持真实动作；如果没有这一行，用户看不到 real_actions 已接线。
        self.assertFalse(report["recording_mode"])  # 新增代码+源码复核门禁：断言真实路径不是录制模式；如果没有这一行，真实动作可能仍被 recording 冒充。
        self.assertTrue(report["real_desktop_touched"])  # 新增代码+源码复核门禁：断言真实动作字段被汇总；如果没有这一行，成熟矩阵拿不到真实桌面事实。
        self.assertGreater(report["low_level_event_count"], 0)  # 新增代码+源码复核门禁：断言低层事件数大于 0；如果没有这一行，真实动作可能只是口头成功。
    # 新增代码+源码复核门禁：函数段结束，test_runtime_real_actions_uses_injected_real_execution_loop 到此结束；如果没有这个边界说明，代码小白不容易看出 real_actions 测试范围。

    def test_agent_no_longer_routes_paint_prompt_to_desktop_runtime_before_model_loop(self) -> None:  # 修改代码+ModelLoopComputerUse：函数段开始，验证 agent.run 不再在模型前抢跑桌面任务；如果没有这个测试，旧 Python 分类器可能再次替模型理解用户意图。
        import tempfile  # 新增代码+DesktopTaskRuntimeRoute：导入临时目录工具隔离 agent workspace；如果没有这一行，agent.run 会写入真实项目 memory。
        from pathlib import Path  # 新增代码+DesktopTaskRuntimeRoute：导入 Path 构造 workspace 路径；如果没有这一行，路径拼接会退回脆弱字符串。

        class ModelLoopSentinelFakeModel:  # 修改代码+ModelLoopComputerUse：类段开始，定义会输出模型主循环哨兵文本的离线假模型；如果没有这个类，测试无法证明自然语言桌面任务已经交还给模型。
            def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码+DesktopTaskRuntimeRoute：模拟模型 chat 接口；如果没有这一行，LearningAgent 无法调用假模型。
                del messages, tools  # 新增代码+DesktopTaskRuntimeRoute：声明本测试不关心普通模型上下文和工具池；如果没有这一行，未使用参数会让意图不清楚。
                return ModelMessage(text="MODEL_LOOP_DESKTOP_TASK_RECEIVED")  # 修改代码+ModelLoopComputerUse：返回模型主循环哨兵文本；如果没有这一行，测试无法稳定区分模型路径和旧 runtime 抢跑路径。
        # 修改代码+ModelLoopComputerUse：类段结束，ModelLoopSentinelFakeModel 到此结束；如果没有这个边界说明，代码小白不容易看出假模型范围。

        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DesktopTaskRuntimeRoute：创建临时 workspace；如果没有这一行，测试会污染真实运行目录。
            workspace = Path(raw_dir)  # 新增代码+DesktopTaskRuntimeRoute：把临时目录转成 Path；如果没有这一行，LearningAgent 构造参数不够清楚。
            agent = LearningAgent(model=ModelLoopSentinelFakeModel(), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 修改代码+ModelLoopComputerUse：创建真实 agent 但使用模型主循环哨兵假模型；如果没有这一行，测试没有 agent.run 主体。
            runtime = ComputerUseDesktopTaskRuntime.for_test(full_mode=True)  # 修改代码+源码复核门禁：创建已开启 full 的隔离运行时；如果没有这一行，测试无法稳定模拟用户已确认 full mode。
            runtime.real_execution_loop = FakeRealExecutionLoopForAgentRoute()  # 新增代码+源码复核门禁：注入安全 fake 真实闭环；如果没有这一行，主路由改成 real_actions=True 后会正确拒绝而不是返回 OK。
            agent.desktop_task_runtime = runtime  # 修改代码+源码复核门禁：把带 fake 真实闭环的 runtime 注入 agent；如果没有这一行，agent 会创建默认未接线 runtime。
            answer = agent.run("请使用本地电脑的画图软件画一个皮卡丘。", max_turns=1)  # 新增代码+DesktopTaskRuntimeRoute：执行真实 run 入口；如果没有这一行，Task 5 接线不会被触发。
            self.assertIn("MODEL_LOOP_DESKTOP_TASK_RECEIVED", answer)  # 修改代码+ModelLoopComputerUse：断言最终答案来自模型主循环；如果没有这一行，旧 runtime 抢跑仍可能被误判成功。
            self.assertNotIn("COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK", answer)  # 修改代码+ModelLoopComputerUse：断言旧桌面任务 runtime 成功 token 没有出现；如果没有这一行，抢跑路径可能继续保留。
            self.assertNotIn("computer_use_gui_route_used=true", answer)  # 修改代码+ModelLoopComputerUse：断言旧 GUI 分流标记没有出现；如果没有这一行，测试无法防止旧路由半残留。
    # 修改代码+ModelLoopComputerUse：函数段结束，test_agent_no_longer_routes_paint_prompt_to_desktop_runtime_before_model_loop 到此结束；如果没有这个边界说明，代码小白不容易看出 agent.run 模型主循环门禁范围。

    def test_agent_full_mode_without_real_loop_is_not_preloop_runtime_claim(self) -> None:  # 修改代码+ModelLoopComputerUse：函数段开始，验证 full 模式不会再由模型前 runtime 抢跑声明结果；如果没有这个测试，旧未接线拒绝路径可能继续替模型决策。
        import tempfile  # 新增代码+源码复核门禁：导入临时目录工具隔离 agent workspace；如果没有这一行，测试会污染真实运行目录。
        from pathlib import Path  # 新增代码+源码复核门禁：导入 Path 构造 workspace 路径；如果没有这一行，LearningAgent 构造参数不够清楚。
        class ModelLoopFakeModel:  # 修改代码+ModelLoopComputerUse：类段开始，定义应该被调用的模型主循环假模型；如果没有这个类，测试无法证明旧 runtime 抢跑已被移除。
            def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码+源码复核门禁：提供模型 chat 接口；如果没有这一行，LearningAgent 无法初始化离线模型。
                del messages, tools  # 新增代码+源码复核门禁：声明本测试不使用模型输入；如果没有这一行，未使用参数意图不清楚。
                return ModelMessage(text="MODEL_LOOP_FULL_MODE_WITHOUT_REAL_LOOP_RECEIVED")  # 修改代码+ModelLoopComputerUse：返回模型主循环哨兵文本；如果没有这一行，测试无法稳定证明 prompt 交给了模型。
            # 修改代码+ModelLoopComputerUse：函数段结束，ModelLoopFakeModel.chat 到此结束；如果没有这个边界说明，初学者不容易看出 fake 模型范围。
        # 修改代码+ModelLoopComputerUse：类段结束，ModelLoopFakeModel 到此结束；如果没有这个边界说明，初学者不容易看出 fake 模型范围。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+源码复核门禁：创建临时 workspace；如果没有这一行，测试会污染真实项目 memory。
            workspace = Path(raw_dir)  # 新增代码+源码复核门禁：把临时目录转成 Path；如果没有这一行，LearningAgent 构造参数不够清楚。
            agent = LearningAgent(model=ModelLoopFakeModel(), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 修改代码+ModelLoopComputerUse：创建真实 agent 并使用应该被调用的假模型；如果没有这一行，测试没有 agent.run 主体。
            agent.desktop_task_runtime = ComputerUseDesktopTaskRuntime.for_test(full_mode=True)  # 新增代码+源码复核门禁：注入 full 已确认但未接真实执行闭环的 runtime；如果没有这一行，测试无法稳定复现当前缺口。
            answer = agent.run("请使用本地电脑的画图软件画一个皮卡丘。", max_turns=1)  # 新增代码+源码复核门禁：执行真实 run 入口；如果没有这一行，主路由行为没有事实来源。
            self.assertIn("MODEL_LOOP_FULL_MODE_WITHOUT_REAL_LOOP_RECEIVED", answer)  # 修改代码+ModelLoopComputerUse：断言最终答案来自模型主循环；如果没有这一行，旧 runtime 抢跑可能继续隐藏。
            self.assertNotIn("COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK", answer)  # 修改代码+ModelLoopComputerUse：断言旧 runtime 成熟 token 没有出现；如果没有这一行，录制或空路径可能再次冒充成熟。
            self.assertNotIn("real_actions_not_enabled_in_desktop_task_runtime", answer)  # 修改代码+ModelLoopComputerUse：断言旧未接线 runtime 拒绝文本没有抢先返回；如果没有这一行，模型主循环仍会被 Python 分流打断。
            self.assertNotIn("real_desktop_touched=false", answer)  # 修改代码+ModelLoopComputerUse：断言旧 runtime 的桌面触达字段没有冒充主答案；如果没有这一行，旧报告格式可能继续误导用户。
    # 修改代码+ModelLoopComputerUse：函数段结束，test_agent_full_mode_without_real_loop_is_not_preloop_runtime_claim 到此结束；如果没有这个边界说明，代码小白不容易看出模型主循环边界测试范围。

    def test_default_agent_runtime_injects_universal_desktop_adapter_not_paint_loop(self) -> None:  # 修改代码+UniversalDesktopAdapter：函数段开始，验证默认生产 runtime 接入通用桌面 adapter 而不是 Paint/Pikachu 专用闭环；如果没有这个测试，后续可能再次把通用入口误接到特例 loop 或空 loop。
        import tempfile  # 新增代码+UniversalLoopSlimming：导入临时目录工具隔离 agent workspace；如果没有这一行，默认 runtime 会把证据写入真实项目目录。
        from pathlib import Path  # 新增代码+UniversalLoopSlimming：导入 Path 便于构造 workspace；如果没有这一行，路径表达会退回脆弱字符串。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+UniversalLoopSlimming：创建一次性 workspace；如果没有这一行，测试可能污染用户真实 memory。
            agent = LearningAgent(model=ToolCallingFakeModel([]), workspace=Path(raw_dir), ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+UniversalLoopSlimming：创建未注入 desktop runtime 的真实 agent；如果没有这一行，无法覆盖默认生产构造路径。
            runtime = agent._desktop_task_runtime_for_current_run()  # 新增代码+UniversalLoopSlimming：调用默认 runtime 构造入口；如果没有这一行，测试只能检查静态文本而不能验证真实对象。
            loop = getattr(runtime, "real_execution_loop", None)  # 修改代码+UniversalDesktopAdapter：读取运行时真实执行闭环字段；如果没有这一行，断言无法知道默认路径是否已经接到通用 adapter。
            self.assertIsNotNone(loop)  # 修改代码+UniversalDesktopAdapter：断言默认生产路径已经有通用 adapter 入口；如果没有这一行，/computer use --full 会继续停在未接线拒绝状态。
            self.assertTrue(hasattr(loop, "run_desktop_task"))  # 新增代码+UniversalDesktopAdapter：断言 adapter 暴露 desktop runtime 需要的统一方法；如果没有这一行，runtime 可能拿到不能执行的错误对象。
            self.assertIn("UniversalDesktopExecutionLoopAdapter", type(loop).__name__)  # 新增代码+UniversalDesktopAdapter：断言默认对象是通用 adapter；如果没有这一行，旧 Paint/Pikachu 特例可能换个路径名继续混入生产链路。
            inner_loop = getattr(loop, "loop", None)  # 新增代码+RealObservationAdapter：读取 adapter 内部真正执行的 observe-plan-act-verify loop；如果没有这一行，测试只能看到外壳名字，看不到是否还接着录制观察层。
            observation_runtime = getattr(inner_loop, "observation_runtime", None)  # 新增代码+RealObservationAdapter：读取内部观察 runtime；如果没有这一行，默认路径可能继续使用录制观察而没人发现。
            self.assertIn("UniversalRealObservationFrameRuntime", type(observation_runtime).__name__)  # 新增代码+RealObservationAdapter：断言默认生产路径至少接入真实只读屏幕/窗口观察；如果没有这一行，/computer use --full 会继续只有录制证据而没有真实“眼睛”。
            self.assertIsNone(getattr(loop, "supported_paint_drawing_loop", None))  # 新增代码+UniversalLoopSlimming：断言默认 adapter 没有挂载 Paint/Pikachu/动物专用绘图桥；如果没有这一行，旧特例桥可能重新混入默认用户路径并误导后续规划器接线。
            self.assertFalse(getattr(loop, "supported_paint_drawing_enabled", True))  # 新增代码+UniversalLoopSlimming：断言默认报告状态明确显示专用绘图桥关闭；如果没有这一行，代码只检查对象名仍可能漏掉内部特例开关。
            self.assertNotIn("paint_pikachu_real_loop", str(getattr(runtime, "base_dir", "")))  # 新增代码+UniversalLoopSlimming：断言默认证据目录不再以 Paint/Pikachu 命名；如果没有这一行，路径命名仍会误导后续开发。
    # 修改代码+UniversalDesktopAdapter：函数段结束，test_default_agent_runtime_injects_universal_desktop_adapter_not_paint_loop 到此结束；如果没有这个边界说明，代码小白不容易看出默认接线门禁范围。
    def test_default_desktop_runtime_uses_universal_adapter_with_real_dispatch_shape(self) -> None:  # 修改代码+ModelLoopComputerUse：函数段开始，验证底层桌面 runtime 仍能进入通用 adapter 并识别真实派发形状；如果没有这个测试，移除 agent.run 抢跑后可能误删底层执行能力。
        import tempfile  # 新增代码+UniversalDesktopAdapter：导入临时目录工具隔离 agent workspace；如果没有这一行，测试可能污染用户真实 memory。
        from pathlib import Path  # 新增代码+UniversalDesktopAdapter：导入 Path 便于构造 workspace；如果没有这一行，路径表达会退回脆弱字符串。
        prompt = "\u8bf7\u4f7f\u7528\u672c\u5730\u7535\u8111\u7684\u753b\u56fe\u8f6f\u4ef6\u753b\u4e00\u53ea\u72ec\u89d2\u517d\u3002"  # 修改代码+FullPaintDrawingBridge：使用当前未支持的“画独角兽”中文 prompt；如果没有这一行，画猫会真实打开 Paint 而不再适合作为未派发样例。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+UniversalDesktopAdapter：创建一次性 workspace；如果没有这一行，full mode 状态会污染真实项目。
            agent = LearningAgent(model=ToolCallingFakeModel([]), workspace=Path(raw_dir), ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+UniversalDesktopAdapter：创建真实 agent 但使用离线假模型；如果没有这一行，测试不能覆盖 LearningAgent 主入口。
            runtime = agent._desktop_task_runtime_for_current_run()  # 新增代码+UniversalDesktopAdapter：取得默认 runtime 并让 agent 缓存它；如果没有这一行，无法稳定激活同一个 mode_store。
            class SafeRealShapedSendInputBackend:  # 新增代码+RealPhysicalFullMode：类段开始，用安全 fake 后端替代真实物理后端；如果没有这个类，单元测试会真的移动用户鼠标键盘。
                requires_raw_text = False  # 新增代码+RealPhysicalFullMode：声明 fake 后端不需要原始文本；如果没有这一行，受控 sender 可能按真实文本限制拒绝测试事件。
                def send_low_level(self, events: list[dict[str, object]]) -> dict[str, object]:  # 新增代码+RealPhysicalFullMode：函数段开始，模拟 Windows SendInput 后端发送低层事件；如果没有这段函数，Phase95 没有可调用后端。
                    return {"ok": True, "sender": "windows_sendinput_low_level", "low_level_event_count": len(events), "real_dispatch_performed": True, "real_desktop_touched": True, "raw_text_included": False}  # 新增代码+RealPhysicalFullMode：返回真实派发形状但不触碰桌面；如果没有这一行，测试无法安全验证顶层 real=true 汇总。
                # 新增代码+RealPhysicalFullMode：函数段结束，SafeRealShapedSendInputBackend.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出 fake 后端范围。
            # 新增代码+RealPhysicalFullMode：类段结束，SafeRealShapedSendInputBackend 到此结束；如果没有这个边界说明，初学者不容易看出 fake 后端边界。
            adapter = runtime.real_execution_loop  # 新增代码+RealPhysicalFullMode：取得默认 adapter 以替换其底层后端；如果没有这一行，测试无法避免真实物理输入副作用。
            inner_loop = adapter.loop  # 新增代码+RealPhysicalFullMode：取得 adapter 内部通用 loop；如果没有这一行，测试无法定位动作 runtime。
            action_runtime = inner_loop.action_runtime  # 新增代码+RealPhysicalFullMode：取得动作 runtime；如果没有这一行，测试无法定位受控 sender。
            from learning_agent.computer_use.universal_target_session import UniversalTargetSessionRuntime  # 修改代码+RealLaunchTargetSession：导入可注入 fake 启动后端的目标 session runtime；如果没有这一行，单元测试会真的打开 Paint。
            class SafeAgentOwnedLaunchBackend:  # 新增代码+RealLaunchTargetSession：类段开始，用安全 fake 代替生产真实启动后端；如果没有这个类，本单元测试会在开发机残留 mspaint 进程。
                def launch(self, request: object) -> dict[str, object]:  # 新增代码+RealLaunchTargetSession：函数段开始，模拟 agent 自己启动了目标进程；如果没有这段函数，目标 session 无法得到自有 pid 证据。
                    _ = request  # 新增代码+RealLaunchTargetSession：本 fake 不需要读取请求细节；如果没有这一行，读者会误以为参数遗漏。
                    return {"ok": True, "decision": "safe_agent_owned_fake_launch", "backend_launch_performed": True, "backend_launch_reaches_launcher": True, "process_started": True, "process_id": 88421, "process_executable": "mspaint.exe", "argv": ["mspaint.exe"], "command_shape": "argv_no_shell", "uses_shell_string": False, "real_desktop_touched": True, "cleanup_registered": True, "owned_process_registered": True, "low_level_event_count": 0}  # 新增代码+RealLaunchTargetSession：返回真实启动形状但不触碰桌面；如果没有这一行，测试不能证明 agent-owned launch 字段汇总。
                # 新增代码+RealLaunchTargetSession：函数段结束，SafeAgentOwnedLaunchBackend.launch 到此结束；如果没有这个边界说明，初学者不容易看出 fake 启动范围。
            # 新增代码+RealLaunchTargetSession：类段结束，SafeAgentOwnedLaunchBackend 到此结束；如果没有这个边界说明，初学者不容易看出 fake 后端范围。
            class SafeAgentOwnedWindowProbe:  # 新增代码+RealLaunchTargetSession：类段开始，用安全 fake 代替真实窗口枚举；如果没有这个类，单元测试会依赖真实桌面窗口。
                def find_owned_window(self, launch_result: dict[str, object], target_hint: str = "") -> dict[str, object]:  # 新增代码+RealLaunchTargetSession：函数段开始，按 fake pid 返回 agent-owned 窗口；如果没有这段函数，目标身份无法通过验证。
                    _ = target_hint  # 新增代码+RealLaunchTargetSession：本 fake 不需要目标提示词；如果没有这一行，读者会误以为参数遗漏。
                    return {"pid": int(launch_result.get("process_id", 0) or 0), "hwnd": 88422, "window_id": "hwnd:88422", "process_name": "mspaint.exe", "app_id": "mspaint.exe", "title_preview": "Safe Fake Paint", "title": "Safe Fake Paint", "rect": {"left": 100, "top": 120, "right": 900, "bottom": 720}}  # 新增代码+RealLaunchTargetSession：返回能通过 Phase111 身份绑定的窗口；如果没有这一行，真实启动汇总字段会保持 false。
                # 新增代码+RealLaunchTargetSession：函数段结束，SafeAgentOwnedWindowProbe.find_owned_window 到此结束；如果没有这个边界说明，初学者不容易看出 fake 窗口范围。
            # 新增代码+RealLaunchTargetSession：类段结束，SafeAgentOwnedWindowProbe 到此结束；如果没有这个边界说明，初学者不容易看出 fake probe 范围。
            action_runtime.target_runtime = UniversalTargetSessionRuntime(launch_backend=SafeAgentOwnedLaunchBackend(), window_probe=SafeAgentOwnedWindowProbe(), enable_real_launch=True)  # 修改代码+RealLaunchTargetSession：把单元测试的目标启动链换成 safe fake；如果没有这一行，测试会真实启动 Paint 并留下进程警告。
            action_runtime.low_level_sender.low_level_backend = SafeRealShapedSendInputBackend()  # 新增代码+RealPhysicalFullMode：把真实后端替换成安全 real-shaped fake；如果没有这一行，本单元测试会触碰用户真实桌面。
            request = runtime.mode_store.request_full_mode(reason="universal adapter test")  # 新增代码+UniversalDesktopAdapter：按真实 full mode 流程申请授权状态；如果没有这一行，桌面任务会被 full mode 门禁挡住。
            runtime.mode_store.confirm_full_mode(request["confirmation_token"], reason="universal adapter test")  # 新增代码+UniversalDesktopAdapter：确认 full mode 以模拟用户已经输入 /computer use --full；如果没有这一行，测试不会进入真实动作请求路径。
            report = runtime.run_prompt(prompt, real_actions=True)  # 修改代码+ModelLoopComputerUse：直接调用底层桌面 runtime 验证真实动作形状；如果没有这一行，底层 adapter 成熟度会被顶层模型主循环测试混淆。
            answer = json.dumps(report, ensure_ascii=False, sort_keys=True) + "\n" + computer_use_full_desktop_task_runtime_cli_line(report)  # 修改代码+ModelLoopComputerUse：把结构化报告转成可断言文本和终端 token 行；如果没有这一行，原有字段断言无法继续覆盖底层 runtime 输出。
            self.assertIn("universal_desktop_execution_loop_used", answer)  # 新增代码+UniversalDesktopAdapter：断言报告显示通用 adapter 已使用；如果没有这一行，默认路径可能悄悄退回空 loop。
            self.assertIn("observe_plan_act_verify_loop", answer)  # 新增代码+UniversalDesktopAdapter：断言报告显示 observe-plan-act-verify 闭环已进入；如果没有这一行，adapter 可能没有真正调用通用 loop。
            self.assertIn("real_observation_runtime_used", answer)  # 新增代码+RealObservationAdapter：断言用户路径报告真实只读 observation runtime 已被使用；如果没有这一行，终端输出可能仍把录制观察误当真实观察。
            self.assertIn("real_observation_frame_used", answer)  # 新增代码+RealObservationAdapter：断言用户路径产生了统一真实观察帧；如果没有这一行，planner/verifier 仍可能没有屏幕与窗口事实输入。
            self.assertIn("phase116_universal_real_gui_observation_frame", answer)  # 新增代码+RealObservationAdapter：断言 loop_report 内含 URG-1 真实观察帧模型名；如果没有这一行，默认链路可能只展示高层 adapter 名字。
            self.assertIn("real_actions_supported", answer)  # 新增代码+UniversalDesktopAdapter：断言报告区分已接 adapter 和未接线硬拒绝；如果没有这一行，用户看不出路径推进。
            self.assertIn("real_dispatch_performed\": true", answer)  # 修改代码+RealPhysicalFullMode：断言顶层报告识别 fake 后端的真实派发形状；如果没有这一行，真实 SendInput 成功也可能继续显示 false。
            self.assertIn("real_desktop_touched=true", answer)  # 修改代码+RealPhysicalFullMode：断言可见 token 行显示桌面已触达；如果没有这一行，真实终端验收无法确认物理动作链路。
            self.assertIn("real_launch_performed=true", answer)  # 新增代码+RealLaunchTargetSession：断言可见 token 行显示 agent 自己启动目标；如果没有这一行，用户已打开窗口可能再次造成假通过。
            self.assertIn("owned_process_registered=true", answer)  # 新增代码+RealLaunchTargetSession：断言可见 token 行显示进程登记为自有；如果没有这一行，误用用户旧进程风险无法在测试中暴露。
            self.assertIn("visible_window_verified=true", answer)  # 新增代码+RealLaunchTargetSession：断言可见 token 行显示启动窗口已绑定；如果没有这一行，启动成功但无窗口也可能被误判。
            self.assertIn("universal_desktop_execution_loop_real_dispatch_finished", answer)  # 修改代码+RealPhysicalFullMode：断言成功原因码进入真实派发完成分支；如果没有这一行，默认 full 模式仍会像只观察模式一样报边界。
            self.assertIn("COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK", answer)  # 修改代码+RealPhysicalFullMode：断言真实派发形状通过桌面任务 runtime 成功门禁；如果没有这一行，用户路径无法得到稳定完成 token。
            self.assertNotIn("paint_pikachu_real_execution_finished", answer)  # 新增代码+UniversalDesktopAdapter：断言不再走旧 Paint/Pikachu 专用决策码；如果没有这一行，旧特例可能重新混入默认路径。
            self.assertIn('"subject_specific_planning": false', answer)  # 新增代码+UniversalLoopSlimming：断言默认用户路径不会声明对象特定规划；如果没有这一行，皮卡丘/猫/大象这类特例规划可能继续伪装成通用规划。
            self.assertNotIn('"supported_paint_drawing_bridge_used": true', answer)  # 新增代码+UniversalLoopSlimming：断言默认用户路径没有使用 Paint 专用桥；如果没有这一行，真实终端输出可能再次把特例桥误看成成熟 computer use。
    # 修改代码+ModelLoopComputerUse：函数段结束，test_default_desktop_runtime_uses_universal_adapter_with_real_dispatch_shape 到此结束；如果没有这个边界说明，代码小白不容易看出顶层模型循环和底层 runtime 接线的边界。

    def test_universal_adapter_can_inject_controlled_physical_sender_without_real_desktop_touch(self) -> None:  # 新增代码+ControlledPhysicalAdapter：函数段开始，验证 full adapter 能配置受控物理 sender 并保持真实桌面零触碰；如果没有这个测试，底层 sender 虽存在但 /computer use --full 主链路仍可能接不到。
        from learning_agent.computer_use.controlled_physical_sendinput import Phase95RecordingSendInputBackend, WindowsControlledPhysicalSendInputSender  # 新增代码+ControlledPhysicalAdapter：导入 Phase95 安全 fake 后端和受控 sender；如果没有这一行，adapter 测试无法避免真实鼠标键盘副作用。
        from learning_agent.computer_use.universal_desktop_execution_loop import UniversalDesktopExecutionLoopAdapter  # 新增代码+ControlledPhysicalAdapter：导入 full 模式通用 adapter；如果没有这一行，测试只能覆盖底层 DSL 而不能覆盖用户主链。
        from learning_agent.computer_use.universal_observe_plan_act_verify import Phase119RecordingObservationRuntime  # 新增代码+ControlledPhysicalAdapter：导入安全记录观察 runtime；如果没有这一行，测试可能读取真实屏幕导致不稳定。

        backend = Phase95RecordingSendInputBackend(physical_dispatch=False)  # 新增代码+ControlledPhysicalAdapter：创建不会触碰真实桌面的 fake 后端；如果没有这一行，测试没有最后一跳调用计数。
        sender = WindowsControlledPhysicalSendInputSender(low_level_backend=backend, platform="win32", default_enable_physical_dispatch=True)  # 新增代码+ControlledPhysicalAdapter：创建显式启用但只接 fake 后端的受控 sender；如果没有这一行，adapter 只能停在 recording sender。
        adapter = UniversalDesktopExecutionLoopAdapter(observation_runtime=Phase119RecordingObservationRuntime(), controlled_physical_sender=sender)  # 新增代码+ControlledPhysicalAdapter：把受控 sender 注入 full adapter；如果没有这一行，/computer use --full 无法复用 Phase95 最后一跳。
        report = adapter.run_desktop_task("mspaint", "请使用本地电脑的画图软件画一只猫。")  # 新增代码+ControlledPhysicalAdapter：用真实用户习惯的自然语言绘图 prompt 运行 adapter；如果没有这一行，接线只停留在构造层。
        self.assertTrue(report["controlled_physical_sender_configured"])  # 新增代码+ControlledPhysicalAdapter：断言 adapter 知道受控 sender 已配置；如果没有这一行，报告无法区分 recording 路径和受控物理路径。
        self.assertTrue(report["controlled_physical_sender_used"])  # 新增代码+ControlledPhysicalAdapter：断言本次任务真的走过受控 sender；如果没有这一行，配置可能没有被 loop 消费。
        self.assertTrue(report["controlled_physical_backend_reached"])  # 新增代码+ControlledPhysicalAdapter：断言事件到达 fake 后端；如果没有这一行，最后一跳桥接可能只是表面字段。
        self.assertFalse(report["real_dispatch_performed"])  # 新增代码+ControlledPhysicalAdapter：断言 fake 后端不会被误报成真实物理派发；如果没有这一行，成熟度会被高估。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+ControlledPhysicalAdapter：断言单测没有触碰真实桌面；如果没有这一行，开发验证可能影响用户电脑。
        self.assertGreater(backend.send_count, 0)  # 新增代码+ControlledPhysicalAdapter：断言 fake 后端收到至少一次调用；如果没有这一行，受控 sender 可能没有真正执行。
    # 新增代码+ControlledPhysicalAdapter：函数段结束，test_universal_adapter_can_inject_controlled_physical_sender_without_real_desktop_touch 到此结束；如果没有这个边界说明，代码小白不容易看出 adapter 接线测试范围。
    def test_universal_adapter_extracts_house_visual_intent_without_raw_prompt_leak(self) -> None:  # 新增代码+VisualSemanticPlanner：函数段开始，验证中文自然语言 prompt 会被转成脱敏视觉意图；如果没有这个测试，planner 可能拿不到“房子”而继续画通用脸。
        from learning_agent.computer_use.universal_desktop_execution_loop import UniversalDesktopExecutionLoopAdapter  # 新增代码+VisualSemanticPlanner：导入 full 模式通用 adapter；如果没有这一行，测试无法覆盖用户真实入口的任务包装层。
        adapter = UniversalDesktopExecutionLoopAdapter()  # 新增代码+VisualSemanticPlanner：创建默认 adapter 但不运行真实桌面任务；如果没有这一行，测试没有对象可调用 `_task_from_prompt`。
        prompt = "请使用本地电脑的画图软件画一个房子。"  # 新增代码+VisualSemanticPlanner：准备真实用户习惯的中文 prompt；如果没有这一行，测试无法覆盖这次真实失败的输入形态。
        task = adapter._task_from_prompt("mspaint", prompt)  # 新增代码+VisualSemanticPlanner：调用任务包装层抽取结构化意图；如果没有这一行，adapter 是否把语义交给 planner 没有事实来源。
        self.assertEqual("house", task["visual_subject_hint"])  # 新增代码+VisualSemanticPlanner：断言房子语义被抽取；如果没有这一行，房子 prompt 会退化成未知任务。
        self.assertEqual("house", task["visual_intent"]["subject"])  # 新增代码+VisualSemanticPlanner：断言结构化 visual_intent 也记录主题；如果没有这一行，后续 planner 无法稳定读取意图。
        self.assertFalse(task["raw_prompt_included"])  # 新增代码+VisualSemanticPlanner：断言任务字典不保存原始 prompt；如果没有这一行，真实用户输入可能进入长日志。
        self.assertNotIn(prompt, str(task))  # 新增代码+VisualSemanticPlanner：断言结构化任务字符串里没有完整原文；如果没有这一行，脱敏约束可能被误破坏。
    # 新增代码+VisualSemanticPlanner：函数段结束，test_universal_adapter_extracts_house_visual_intent_without_raw_prompt_leak 到此结束；如果没有这个边界说明，代码小白不容易看出 adapter 语义抽取测试范围。
    def test_universal_adapter_extracts_generic_open_app_intent_for_notepad(self) -> None:  # 新增代码+GenericSemanticPlanner：函数段开始，验证非画图自然语言会进入通用语义 planner；如果没有这个测试，记事本任务可能继续被误当成绘图任务。
        from learning_agent.computer_use.universal_desktop_execution_loop import UniversalDesktopExecutionLoopAdapter  # 新增代码+GenericSemanticPlanner：导入 full 模式 adapter；如果没有这一行，测试无法覆盖用户真实 `/computer use --full` 后的任务包装入口。
        adapter = UniversalDesktopExecutionLoopAdapter()  # 新增代码+GenericSemanticPlanner：创建默认 adapter 且不触碰真实桌面；如果没有这一行，测试会缺少可调用对象。
        prompt = "请使用本地电脑打开记事本。"  # 新增代码+GenericSemanticPlanner：准备真实用户会输入的打开应用 prompt；如果没有这一行，测试无法覆盖非 Paint 应用的自然语言入口。
        task = adapter._task_from_prompt("notepad", prompt)  # 新增代码+GenericSemanticPlanner：把自然语言包装为通用任务；如果没有这一行，后续断言没有事实来源。
        self.assertEqual("open_app", task["semantic_intent"]["task_kind"])  # 新增代码+GenericSemanticPlanner：断言任务类型是打开应用；如果没有这一行，打开记事本可能仍被误接到绘图分支。
        self.assertEqual("notepad", task["semantic_intent"]["target_app"])  # 新增代码+GenericSemanticPlanner：断言目标应用被归一成 notepad；如果没有这一行，启动层可能拿不到可执行目标。
        self.assertFalse(task["semantic_intent"]["raw_prompt_included"])  # 新增代码+GenericSemanticPlanner：断言通用语义意图不保存原始 prompt；如果没有这一行，语义 planner 可能泄露用户原文。
        self.assertFalse(task["visual_planning_requested"])  # 新增代码+GenericSemanticPlanner：断言打开应用不是绘图规划任务；如果没有这一行，Notepad 任务可能继续生成画图动作。
        self.assertNotIn(prompt, str(task))  # 新增代码+GenericSemanticPlanner：断言任务报告不包含完整用户原文；如果没有这一行，日志隐私边界会退化。
    # 新增代码+GenericSemanticPlanner：函数段结束，test_universal_adapter_extracts_generic_open_app_intent_for_notepad 到此结束；如果没有这个边界说明，代码小白不容易看出通用语义入口测试范围。

    def test_computer_use_full_command_still_uses_terminal_command_handler(self) -> None:  # 新增代码+DesktopTaskRuntimeRoute：函数段开始，验证 /computer 命令仍由终端命令处理器负责；如果没有这个测试，Task 5 可能误把 /computer use --full 当普通 prompt 路由。
        import tempfile  # 新增代码+DesktopTaskRuntimeRoute：导入临时目录工具隔离 /computer 状态；如果没有这一行，full 请求会写入真实 memory。
        from pathlib import Path  # 新增代码+DesktopTaskRuntimeRoute：导入 Path 构造 workspace；如果没有这一行，终端命令路径不够清楚。
        from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+DesktopTaskRuntimeRoute：导入真实 /computer 命令处理器；如果没有这一行，测试不能证明交互层仍保留命令通道。

        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DesktopTaskRuntimeRoute：创建临时 workspace；如果没有这一行，命令状态会污染项目目录。
            output = run_computer_terminal_command(Path(raw_dir), "/computer use --full")  # 修改代码+FullNaturalUserFlow：执行真实用户会输入的一行 full 命令；如果没有这一行，断言没有终端输出对象。
            self.assertIn("Computer Use Mode", output)  # 修改代码+FullNaturalUserFlow：断言 full 命令仍由终端命令面板处理；如果没有这一行，/computer 命令可能被普通 prompt 路由吃掉。
            self.assertIn("full_mode=true", output)  # 新增代码+FullNaturalUserFlow：断言自然 full 命令直接进入 full；如果没有这一行，旧 token 申请流程可能回归。
            self.assertNotIn("confirm_command=/computer use --full-confirm", output)  # 修改代码+FullNaturalUserFlow：断言普通用户输出不再展示二次确认命令；如果没有这一行，用户仍会被引导到非真实习惯。
            self.assertNotIn("COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_READY", output)  # 新增代码+DesktopTaskRuntimeRoute：断言 /computer use --full 没有被桌面任务 runtime 误处理；如果没有这一行，命令和普通 prompt 边界会混乱。
    # 新增代码+DesktopTaskRuntimeRoute：函数段结束，test_computer_use_full_command_still_uses_terminal_command_handler 到此结束；如果没有这个边界说明，代码小白不容易看出 /computer 保留测试范围。

    def test_pikachu_plan_uses_drag_paths_not_image_file(self) -> None:  # 新增代码+DrawingPrimitives：函数段开始，验证皮卡丘计划由通用鼠标拖拽组成；如果没有这个测试，Task 6 可能退回直接生成图片文件的旧绕路。
        plan = build_pikachu_drag_plan(canvas_rect={"left": 100, "top": 100, "right": 900, "bottom": 700})  # 新增代码+DrawingPrimitives：构造受控画布内的皮卡丘拖拽计划；如果没有这一行，断言没有真实计划对象。
        self.assertGreaterEqual(len(plan["drag_paths"]), 12)  # 新增代码+DrawingPrimitives：断言至少十二条笔画路径；如果没有这一行，皮卡丘元素可能过少仍被当成完成。
        self.assertFalse(plan["direct_image_file_cheat"])  # 新增代码+DrawingPrimitives：断言计划没有直接图片文件作弊；如果没有这一行，System.Drawing 类绕路可能重新混入。
        self.assertIn("yellow", {path["color"] for path in plan["drag_paths"]})  # 新增代码+DrawingPrimitives：断言包含黄色主体笔画；如果没有这一行，计划可能不是皮卡丘。
        self.assertIn("black", {path["color"] for path in plan["drag_paths"]})  # 新增代码+DrawingPrimitives：断言包含黑色耳尖/眼睛笔画；如果没有这一行，关键视觉元素可能缺失。
        self.assertIn("red", {path["color"] for path in plan["drag_paths"]})  # 新增代码+DrawingPrimitives：断言包含红色脸颊笔画；如果没有这一行，皮卡丘特征不完整。
    # 新增代码+DrawingPrimitives：函数段结束，test_pikachu_plan_uses_drag_paths_not_image_file 到此结束；如果没有这个边界说明，代码小白不容易看出计划防作弊测试范围。

    def test_drag_path_expands_to_mouse_events(self) -> None:  # 新增代码+DrawingPrimitives：函数段开始，验证高层拖拽路径能展开成底层鼠标事件；如果没有这个测试，drag_path 可能只是不可执行的描述。
        events = expand_drag_path_to_low_level_events([(10, 10), (20, 20), (30, 25)])  # 新增代码+DrawingPrimitives：把三点路径展开成低层事件；如果没有这一行，断言没有事件输入。
        self.assertEqual(events[0]["type"], "mouse_move")  # 新增代码+DrawingPrimitives：断言第一步先移动到起点；如果没有这一行，拖拽可能从未知位置开始。
        self.assertIn("mouse_down", {event["type"] for event in events})  # 新增代码+DrawingPrimitives：断言包含按下鼠标；如果没有这一行，路径不会真正开始绘制。
        self.assertIn("mouse_up", {event["type"] for event in events})  # 新增代码+DrawingPrimitives：断言包含抬起鼠标；如果没有这一行，拖拽动作不会闭合。
    # 新增代码+DrawingPrimitives：函数段结束，test_drag_path_expands_to_mouse_events 到此结束；如果没有这个边界说明，代码小白不容易看出事件展开测试范围。

    def test_pikachu_drag_path_still_requires_verified_window(self) -> None:  # 新增代码+DrawingPrimitives：函数段开始，验证绘图 drag_path 仍经过已验证窗口门禁；如果没有这个测试，Task 6 可能绕过 owned window binding。
        sender = Phase71RecordingInputSender()  # 新增代码+DrawingPrimitives：创建记录型输入 sender，避免触碰真实鼠标；如果没有这一行，测试可能无法统计事件或误发真实输入。
        runtime = WindowsGenericInputActionRuntime(sender=sender)  # 新增代码+DrawingPrimitives：创建通用输入 runtime；如果没有这一行，drag_path 不会经过生产动作层。
        window = {"window_id": "hwnd:6001", "app_id": "mspaint.exe", "process_name": "mspaint.exe", "safe_to_target": True}  # 新增代码+DrawingPrimitives：构造受控 Paint 窗口摘要；如果没有这一行，动作没有目标窗口。
        identity_context = {"session_id": "task6-drawing", "window_identity": {"window_id": "hwnd:6001", "app_id": "mspaint.exe"}, "target_identity_verification": {"allowed": True, "target_identity_verified": True, "target_drift_blocks_action": False}}  # 新增代码+DrawingPrimitives：构造已验证窗口上下文；如果没有这一行，正向路径无法证明门禁可放行。
        first_path = build_pikachu_drag_plan({"left": 0, "top": 0, "right": 600, "bottom": 500})["drag_paths"][0]["points"]  # 新增代码+DrawingPrimitives：读取第一条皮卡丘拖拽路径；如果没有这一行，动作层测试不能使用真实计划输出。
        blocked = runtime.drag_path(window, first_path, require_verified_identity=True)  # 新增代码+DrawingPrimitives：缺身份时尝试拖拽；如果没有这一行，无法证明未验证窗口会被拒绝。
        allowed = runtime.drag_path(window, first_path, require_verified_identity=True, **identity_context)  # 新增代码+DrawingPrimitives：带身份时执行记录型拖拽；如果没有这一行，无法证明通用路径与门禁能配合。
        self.assertTrue(blocked["blocked"])  # 新增代码+DrawingPrimitives：断言缺身份会阻断；如果没有这一行，绘图动作可能打到错误窗口。
        self.assertFalse(allowed["blocked"])  # 新增代码+DrawingPrimitives：断言已验证身份可放行；如果没有这一行，绘图 primitive 只有拒绝没有可用路径。
        self.assertGreater(allowed["input_event_count"], 0)  # 新增代码+DrawingPrimitives：断言放行后产生记录型输入事件；如果没有这一行，拖拽可能只是空报告。
        self.assertEqual(allowed["low_level_event_count"], 0)  # 新增代码+DrawingPrimitives：断言单元测试不触碰真实低层输入；如果没有这一行，测试可能误控本机。
    # 新增代码+DrawingPrimitives：函数段结束，test_pikachu_drag_path_still_requires_verified_window 到此结束；如果没有这个边界说明，代码小白不容易看出窗口门禁测试范围。

    def test_sendinput_dispatcher_expands_drag_path_event(self) -> None:  # 新增代码+DrawingPrimitives：函数段开始，验证 SendInput dispatcher 能理解通用 drag_path 事件；如果没有这个测试，高层绘图计划无法进入最后一跳事件展开。
        sender = Phase47RecordingLowLevelSender()  # 新增代码+DrawingPrimitives：创建记录型低层 sender；如果没有这一行，测试无法读取展开后的鼠标事件。
        dispatcher = WindowsSendInputDispatcher(platform="win32", enabled=True, low_level_sender=sender, target_verifier=lambda: {"ok": True, "reason": "task6 stable target"})  # 新增代码+DrawingPrimitives：创建已启用但安全记录的 dispatcher；如果没有这一行，send 会因默认关闭而无法覆盖展开逻辑。
        result = dispatcher.send([{"type": "drag_path", "points": [{"x": 10, "y": 10}, {"x": 20, "y": 20}, {"x": 30, "y": 25}]}])  # 新增代码+DrawingPrimitives：发送通用拖拽事件；如果没有这一行，dispatcher 不会遇到 Task 6 新事件类型。
        self.assertTrue(result["ok"])  # 新增代码+DrawingPrimitives：断言 dispatcher 接受 drag_path；如果没有这一行，未知事件空跑可能不报错。
        self.assertGreaterEqual(result["low_level_event_count"], 4)  # 新增代码+DrawingPrimitives：断言展开出移动、按下、移动、抬起等事件；如果没有这一行，路径可能没有真实动作密度。
        self.assertIn("mouse_down", result["low_level_event_types"])  # 新增代码+DrawingPrimitives：断言包含鼠标按下；如果没有这一行，绘图不会开始。
        self.assertIn("mouse_up", result["low_level_event_types"])  # 新增代码+DrawingPrimitives：断言包含鼠标抬起；如果没有这一行，绘图不会结束。
    # 新增代码+DrawingPrimitives：函数段结束，test_sendinput_dispatcher_expands_drag_path_event 到此结束；如果没有这个边界说明，代码小白不容易看出 dispatcher 接线测试范围。
# 新增代码+DesktopTaskAcceptance：类段结束，WindowsComputerUseFullDesktopTaskRouterTests 到此结束；如果没有这个边界说明，代码小白不容易看出本文件测试集合已结束。


if __name__ == "__main__":  # 新增代码+DesktopTaskAcceptance：文件入口段开始，允许用户直接运行本测试文件；如果没有这一行，用户必须记住完整 unittest 模块路径。
    unittest.main()  # 新增代码+DesktopTaskAcceptance：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+DesktopTaskAcceptance：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，代码小白不容易看出脚本入口范围。
