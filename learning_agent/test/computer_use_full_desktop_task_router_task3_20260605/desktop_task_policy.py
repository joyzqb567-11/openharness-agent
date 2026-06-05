"""Desktop Task bash 命令策略。"""  # 新增代码+DesktopTaskPolicy：模块说明本文件只负责桌面任务期间的 bash/PowerShell 命令放行或拒绝；如果没有这一行，代码小白不容易知道本文件不是 GUI 控制器。
from __future__ import annotations  # 新增代码+DesktopTaskPolicy：启用延迟类型注解解析；如果没有这一行，未来在较复杂类型标注下更容易遇到导入顺序兼容问题。

import re  # 新增代码+DesktopTaskPolicy：导入正则模块用于识别命令里的危险脚本制品痕迹；如果没有这一行，策略只能做脆弱的裸字符串匹配。

_IMAGE_EXTENSION_PATTERN = r"\.(?:png|jpg|jpeg|bmp|gif|webp)\b"  # 新增代码+DesktopTaskPolicy：集中定义最终图片制品扩展名正则；如果没有这一行，png/jpg/webp 等绕路识别会分散且容易漏项。
_DIAGNOSTIC_INJECTION_PATTERN = r"[$`(){}\[\]]"  # 新增代码+DesktopTaskPolicy：集中定义只读诊断参数里禁止出现的 PowerShell 子表达式和括号字符；如果没有这一行，危险命令可以藏进 Get-Item/Test-Path/tasklist 参数里被误放行。
_DIAGNOSTIC_CONTROL_OPERATOR_PATTERN = r"(?:;|&&|\|\||\||<|>)"  # 新增代码+DesktopTaskPolicy：集中定义只读诊断命令里禁止出现的 shell 控制符、管道和重定向；如果没有这一行，诊断命令后面可以追加写文件等副作用。
_DIAGNOSTIC_COMMAND_PREFIX_PATTERN = r"^(?:tasklist|get-item|test-path|where(?:\.exe)?|get-command|get-process)\b"  # 新增代码+DesktopTaskPolicy：集中定义看起来像诊断命令的前缀；如果没有这一行，策略无法区分普通 active 命令和伪装成诊断的注入命令。

_DIAGNOSTIC_COMMAND_PATTERNS = (  # 新增代码+DesktopTaskPolicy：元组段开始，列出桌面任务期间允许的只读诊断命令；如果没有这个元组，agent 无法安全检查 Paint 是否存在或运行。
    r"^where(?:\.exe)?\s+mspaint(?:\.exe)?$",  # 新增代码+DesktopTaskPolicy：允许 where.exe/where 查询 mspaint 路径；如果没有这一项，agent 无法用命令确认 Paint 可执行文件位置。
    r"^get-command\s+mspaint(?:\.exe)?$",  # 新增代码+DesktopTaskPolicy：允许 PowerShell Get-Command 查询 mspaint；如果没有这一项，PowerShell 诊断路线会被误拦截。
    r"^get-process\s+(?:-name\s+)?mspaint(?:\.exe)?$",  # 新增代码+DesktopTaskPolicy：允许只读查询 mspaint 进程；如果没有这一项，agent 无法检查 Paint 是否正在运行。
    r"^tasklist(?:\s+/[a-z]+\s+[^;&|<>]+)*$",  # 新增代码+DesktopTaskPolicy：允许基础 tasklist 只读查看进程；如果没有这一项，Windows 进程诊断会被过度拦截。
    rf"^get-item\s+(?:-literalpath\s+|-path\s+)?[^;&|<>]+{_IMAGE_EXTENSION_PATTERN}$",  # 新增代码+DesktopTaskPolicy：允许只读查看单个图片证据文件是否存在；如果没有这一项，Get-Item evidence.png 会被误判成脚本最终制品路线。
    rf"^test-path\s+(?:-literalpath\s+|-path\s+)?[^;&|<>]+{_IMAGE_EXTENSION_PATTERN}$",  # 新增代码+DesktopTaskPolicy：允许只读检查图片证据路径是否存在；如果没有这一项，agent 无法安全确认截图或证据文件。
)  # 新增代码+DesktopTaskPolicy：元组段结束，只读诊断白名单到此固定；如果没有这一行，Python 元组语法不完整。

_FORBIDDEN_SCRIPT_ARTIFACT_PATTERNS = (  # 新增代码+DesktopTaskPolicy：元组段开始，列出桌面任务期间禁止的脚本最终制品路线；如果没有这个元组，脚本生成图片再打开 Paint 的失败路线会复发。
    (r"system\.drawing", "System.Drawing"),  # 新增代码+DesktopTaskPolicy：识别 .NET System.Drawing 绘图 API；如果没有这一项，PowerShell 可以继续绕过 GUI 直接画图。
    (r"(?<![a-z0-9_])pil(?![a-z0-9_])", "PIL"),  # 新增代码+DesktopTaskPolicy：识别 Python PIL/Pillow 入口；如果没有这一项，Python 图像库生成最终图片可能漏网。
    (r"image\s*magick|imagemagick", "ImageMagick"),  # 新增代码+DesktopTaskPolicy：识别 ImageMagick 名称；如果没有这一项，外部图像工具路线可能绕过 GUI。
    (r"(?<![a-z0-9_])magick(?:\.exe)?(?![a-z0-9_])", "magick"),  # 新增代码+DesktopTaskPolicy：识别 magick 命令；如果没有这一项，ImageMagick CLI 可以直接生成图片制品。
    (r"\.save\s*\(", ".Save("),  # 新增代码+DesktopTaskPolicy：识别对象 Save 调用；如果没有这一项，脚本保存图片最终作品的核心动作会漏检。
    (r"system\.windows\.forms", "System.Windows.Forms"),  # 新增代码+DesktopTaskPolicy：识别 PowerShell/.NET 直接加载 Windows Forms 的 GUI 自动化路线；如果没有这一项，脚本可以绕过 Computer Use 直接操作桌面控件。
    (r"sendkeys|sendwait", "SendKeys"),  # 新增代码+DesktopTaskPolicy：识别脚本直接发送键盘输入的路线；如果没有这一项，模型可以用 shell 模拟键盘而不是走受审计低层事件。
    (r"wscript\.shell|new-object\s+-comobject\s+wscript\.shell", "WScript.Shell"),  # 新增代码+DesktopTaskPolicy：识别 Windows 脚本宿主自动化对象；如果没有这一项，shell 可以绕过 Computer Use 直接激活窗口或发送快捷键。
    (r"uiautomation|ui\s*automation", "UIAutomation"),  # 新增代码+DesktopTaskPolicy：识别从 shell 直接调用 UI Automation 的路线；如果没有这一项，桌面操作可能绕过统一观察和动作门。
    (r"setforegroundwindow|mouse_event|sendinput|keybd_event|setcursorpos|sendmessage|postmessage", "direct GUI input API"),  # 修改代码+DesktopTaskPolicy：识别直接调用 Win32 前台窗口、鼠标、键盘和窗口消息 API 的路线；如果没有这一项，shell 可以越过 Computer Use 的目标身份和审计链。
    (rf"start-process\s+['\"]?mspaint(?:\.exe)?['\"]?\b.*{_IMAGE_EXTENSION_PATTERN}", "Start-Process mspaint image"),  # 新增代码+DesktopTaskPolicy：识别 Start-Process mspaint 带图片路径；如果没有这一项，生成图片后打开 Paint 的伪 GUI 路线会被放行。
    (rf"(?:out-file|set-content|new-item|copy-item|move-item|writeallbytes|save|python|py\s+-c|start-process|mspaint|convert)\b.*{_IMAGE_EXTENSION_PATTERN}", "final image artifact path"),  # 修改代码+DesktopTaskPolicy：只在图片扩展名和创建/保存/打开动作同时出现时判定最终制品路线；如果没有这一行，单纯 Get-Item evidence.png 会被误杀，真正生成图片的脚本仍应被拦住。
)  # 新增代码+DesktopTaskPolicy：元组段结束，禁止脚本制品规则到此固定；如果没有这一行，Python 元组语法不完整。


# 新增代码+DesktopTaskPolicy：函数段开始，统一把外部命令输入转成适合匹配的小写单行文本；如果没有这段函数，大小写、换行和多空格会让策略判断不稳定，作者意图是给所有规则提供同一份安全输入，本函数与 evaluate_desktop_bash_command 配合使用，函数段到 return 结束为止。
def _desktop_task_policy_normalize_command(command: str) -> str:  # 新增代码+DesktopTaskPolicy：定义命令归一化 helper；如果没有这一行，主函数需要重复写输入清洗逻辑。
    if not isinstance(command, str):  # 新增代码+DesktopTaskPolicy：先确认输入是字符串；如果没有这一行，None 或列表会在 strip/lower 时导致策略崩溃。
        return ""  # 新增代码+DesktopTaskPolicy：非字符串命令按空命令处理；如果没有这一行，坏输入不会稳定落到普通允许/拒绝结果。
    return " ".join(command.strip().lower().split())  # 新增代码+DesktopTaskPolicy：去首尾空白、转小写并压缩空白；如果没有这一行，同一命令换大小写或换行就可能绕过策略。
# 新增代码+DesktopTaskPolicy：函数段结束，_desktop_task_policy_normalize_command 到此结束；如果没有这个边界说明，代码小白不容易看出命令归一化范围。


# 新增代码+DesktopTaskPolicy：函数段开始，判断命令是否是允许的只读诊断；如果没有这段函数，策略无法区分安全观察和生成最终图片制品，作者意图是保留 Paint 路径和进程排查能力，本函数与 evaluate_desktop_bash_command 配合使用，函数段到 return 结束为止。
def _desktop_task_policy_is_allowed_diagnostic(normalized_command: str) -> bool:  # 新增代码+DesktopTaskPolicy：定义诊断白名单判断 helper；如果没有这一行，主函数会堆满重复正则判断。
    if re.search(_DIAGNOSTIC_INJECTION_PATTERN, normalized_command):  # 新增代码+DesktopTaskPolicy：先拒绝含 PowerShell 子表达式、括号或方括号的伪诊断命令；如果没有这一行，$(Set-Content ...) 可以藏进只读参数里绕过策略。
        return False  # 新增代码+DesktopTaskPolicy：含可执行表达式字符时不视为安全诊断；如果没有这一行，后续白名单正则会继续错误放行注入样本。
    return any(re.search(pattern, normalized_command) for pattern in _DIAGNOSTIC_COMMAND_PATTERNS)  # 新增代码+DesktopTaskPolicy：命中任一诊断正则就放行；如果没有这一行，where/Get-Command/Get-Process/tasklist 都会被当成普通命令。
# 新增代码+DesktopTaskPolicy：函数段结束，_desktop_task_policy_is_allowed_diagnostic 到此结束；如果没有这个边界说明，代码小白不容易看出诊断判断范围。


# 新增代码+DesktopTaskPolicy：函数段开始，识别伪装成只读诊断的 PowerShell 参数注入；如果没有这段函数，tasklist/Get-Item/Test-Path 前缀里的子表达式可能绕过 diagnostic-first 顺序，作者意图是把“假诊断”也作为明确拒绝原因，本函数与 evaluate_desktop_bash_command 配合到 return 结束。
def _desktop_task_policy_diagnostic_injection_matches(normalized_command: str, raw_command: str) -> list[str]:  # 修改代码+DesktopTaskPolicy：定义伪诊断注入匹配 helper并同时读取原始命令；如果没有 raw_command，换行多命令会在归一化时被隐藏。
    if not re.search(_DIAGNOSTIC_COMMAND_PREFIX_PATTERN, normalized_command):  # 新增代码+DesktopTaskPolicy：只有诊断命令前缀才进入注入判断；如果没有这一行，普通 active 命令里的括号会被过度误杀。
        return []  # 新增代码+DesktopTaskPolicy：非诊断前缀不报告诊断注入；如果没有这一行，后续判断无法区分未命中和命中。
    if "\n" in raw_command or "\r" in raw_command:  # 新增代码+DesktopTaskPolicy：识别原始命令里的换行多命令形态；如果没有这一行，Get-Item 后换行接 Set-Content 会被压缩成空格后放行。
        return ["diagnostic argument injection"]  # 新增代码+DesktopTaskPolicy：把诊断前缀里的换行副作用作为注入拒绝；如果没有这一行，多命令换行风险没有稳定原因码。
    if re.search(_DIAGNOSTIC_CONTROL_OPERATOR_PATTERN, normalized_command):  # 新增代码+DesktopTaskPolicy：识别诊断命令里的分号、&&、管道和重定向；如果没有这一行，诊断命令后追加副作用会落到普通 active 放行。
        return ["diagnostic argument injection"]  # 新增代码+DesktopTaskPolicy：把 shell 控制符作为诊断注入拒绝；如果没有这一行，用户和测试看不到拒绝根因。
    if not re.search(_DIAGNOSTIC_INJECTION_PATTERN, normalized_command):  # 新增代码+DesktopTaskPolicy：没有危险 PowerShell 表达式字符时不算注入；如果没有这一行，普通 Get-Item .\evidence.png 会被误拒绝。
        return []  # 新增代码+DesktopTaskPolicy：安全诊断形状返回空命中；如果没有这一行，后续会错误拒绝合法只读诊断。
    return ["diagnostic argument injection"]  # 新增代码+DesktopTaskPolicy：返回稳定拒绝原因；如果没有这一行，用户和测试看不到伪诊断注入被拦住的具体原因。
# 新增代码+DesktopTaskPolicy：函数段结束，_desktop_task_policy_diagnostic_injection_matches 到此结束；如果没有这个边界说明，代码小白不容易看出伪诊断注入判断范围。


# 新增代码+DesktopTaskPolicy：函数段开始，收集命令命中的禁止脚本制品规则；如果没有这段函数，主函数只能返回笼统拒绝，作者意图是让用户知道到底命中了 System.Drawing、Save 还是图片扩展名，本函数与 evaluate_desktop_bash_command 配合使用，函数段到 return 结束为止。
def _desktop_task_policy_forbidden_matches(normalized_command: str, raw_command: str) -> list[str]:  # 修改代码+DesktopTaskPolicy：定义禁止规则匹配 helper并接收原始命令；如果没有 raw_command，换行多命令注入会在归一化后被隐藏。
    matches: list[str] = []  # 新增代码+DesktopTaskPolicy：准备保存命中规则名称的列表；如果没有这一行，后续无法逐项追加匹配结果。
    matches.extend(_desktop_task_policy_diagnostic_injection_matches(normalized_command, raw_command))  # 修改代码+DesktopTaskPolicy：先把伪诊断参数注入加入禁止命中列表；如果没有 raw_command，换行注入和 shell 控制符注入会落到普通 active 放行。
    for pattern, name in _FORBIDDEN_SCRIPT_ARTIFACT_PATTERNS:  # 新增代码+DesktopTaskPolicy：逐条检查禁止脚本制品规则；如果没有这一行，规则表只是静态数据不会被实际使用。
        if re.search(pattern, normalized_command):  # 新增代码+DesktopTaskPolicy：用正则判断当前规则是否命中；如果没有这一行，策略无法发现危险命令内容。
            matches.append(name)  # 新增代码+DesktopTaskPolicy：记录命中的规则名称；如果没有这一行，拒绝结果没有可学习的原因细节。
    return matches  # 新增代码+DesktopTaskPolicy：返回全部命中规则名称；如果没有这一行，主函数拿不到禁止路线判断结果。
# 新增代码+DesktopTaskPolicy：函数段结束，_desktop_task_policy_forbidden_matches 到此结束；如果没有这个边界说明，代码小白不容易看出禁止规则匹配范围。


# 新增代码+DesktopTaskPolicy：函数段开始，评估桌面任务期间 bash/PowerShell 命令是否允许执行；如果没有这段函数，Task 3 无法在命令执行前阻止脚本生成最终图片，作者意图是让 `_bash_atom` 在请求权限前先做 GUI 路线门禁，本函数与 LearningAgent._bash_atom 配合使用，函数段到返回字典结束为止。
def evaluate_desktop_bash_command(command: str, desktop_task_active: bool) -> dict[str, object]:  # 新增代码+DesktopTaskPolicy：定义 Task 3 公开策略函数；如果没有这一行，测试和 agent 都没有稳定入口可调用。
    raw_command = command if isinstance(command, str) else ""  # 新增代码+DesktopTaskPolicy：保留原始命令用于检测换行多命令；如果没有这一行，normalize 会把换行压成空格从而隐藏风险。
    normalized_command = _desktop_task_policy_normalize_command(command)  # 新增代码+DesktopTaskPolicy：先归一化命令文本；如果没有这一行，大小写和换行会影响后续规则命中。
    active = bool(desktop_task_active)  # 新增代码+DesktopTaskPolicy：把上下文状态稳定转成布尔值；如果没有这一行，None、0、非空字符串等输入会造成结果不清晰。
    if not active:  # 新增代码+DesktopTaskPolicy：桌面任务未激活时不启用本策略门禁；如果没有这一行，普通开发命令可能被错误拦截。
        return {  # 新增代码+DesktopTaskPolicy：inactive 结果字典段开始；如果没有这一行，调用方拿不到统一结构化策略结果。
            "allowed": True,  # 新增代码+DesktopTaskPolicy：声明普通命令允许执行；如果没有这一项，调用方不知道是否可以继续走原 bash 流程。
            "decision": "desktop_task_policy_inactive",  # 新增代码+DesktopTaskPolicy：返回 inactive 稳定原因码；如果没有这一项，测试无法确认策略只在桌面任务开启时生效。
            "desktop_task_active": False,  # 新增代码+DesktopTaskPolicy：返回桌面任务未激活状态；如果没有这一项，日志里看不出为什么放行。
            "forbidden_script_artifact_route": False,  # 新增代码+DesktopTaskPolicy：声明没有因为脚本制品路线而拒绝；如果没有这一项，上层难以区分拒绝和普通放行。
            "reason": "桌面任务上下文未激活，bash 命令继续走普通权限流程。",  # 新增代码+DesktopTaskPolicy：给出用户可读解释；如果没有这一项，代码小白不容易理解 inactive 放行。
            "matched_forbidden_patterns": [],  # 新增代码+DesktopTaskPolicy：返回空命中列表保持结构稳定；如果没有这一项，调用方需要额外判空或捕获 KeyError。
        }  # 新增代码+DesktopTaskPolicy：inactive 结果字典段结束；如果没有这一行，Python 字典语法不完整。
    if _desktop_task_policy_is_allowed_diagnostic(normalized_command):  # 修改代码+DesktopTaskPolicy：先检查严格锚定的只读诊断命令再查禁止规则；如果没有这一行，Get-Item save.png 这类证据文件名会被误杀。
        return {  # 新增代码+DesktopTaskPolicy：诊断放行结果字典段开始；如果没有这一行，调用方拿不到结构化放行信息。
            "allowed": True,  # 新增代码+DesktopTaskPolicy：声明诊断命令允许执行；如果没有这一项，_bash_atom 不知道可以继续请求权限和执行。
            "decision": "diagnostic_command_allowed",  # 新增代码+DesktopTaskPolicy：返回诊断白名单原因码；如果没有这一项，测试无法稳定区分安全诊断和普通放行。
            "desktop_task_active": True,  # 新增代码+DesktopTaskPolicy：返回桌面任务已激活状态；如果没有这一项，日志里看不出这是 active 下的白名单放行。
            "forbidden_script_artifact_route": False,  # 新增代码+DesktopTaskPolicy：声明没有脚本最终制品风险；如果没有这一项，上层可能误以为诊断也属于绕路。
            "reason": "这是只读桌面诊断命令，允许用于检查本地程序或进程状态。",  # 新增代码+DesktopTaskPolicy：给出通俗放行原因；如果没有这一项，用户不容易理解为什么 active 下仍可执行。
            "matched_forbidden_patterns": [],  # 新增代码+DesktopTaskPolicy：返回空命中列表保持结构稳定；如果没有这一项，调用方需要额外处理缺字段。
        }  # 新增代码+DesktopTaskPolicy：诊断放行结果字典段结束；如果没有这一行，Python 字典语法不完整。
    forbidden_matches = _desktop_task_policy_forbidden_matches(normalized_command, raw_command)  # 修改代码+DesktopTaskPolicy：在排除严格只读诊断后查找禁止脚本和 GUI 自动化痕迹；如果没有原始命令，换行多命令会继续执行到权限请求甚至真实 shell。
    if forbidden_matches:  # 新增代码+DesktopTaskPolicy：只要命中任意禁止规则就拒绝；如果没有这一行，System.Drawing、PIL、magick、Win32 输入 API 等风险无法触发门禁。
        return {  # 新增代码+DesktopTaskPolicy：拒绝结果字典段开始；如果没有这一行，调用方拿不到结构化拒绝信息。
            "allowed": False,  # 新增代码+DesktopTaskPolicy：声明命令不允许执行；如果没有这一项，_bash_atom 可能继续请求权限和执行命令。
            "decision": "desktop_task_requires_gui_route",  # 新增代码+DesktopTaskPolicy：返回 Task 3 要求的稳定拒绝码；如果没有这一项，上层无法可靠提示必须走 GUI 路线。
            "desktop_task_active": True,  # 新增代码+DesktopTaskPolicy：返回桌面任务已激活状态；如果没有这一项，日志里看不出为什么策略生效。
            "forbidden_script_artifact_route": True,  # 新增代码+DesktopTaskPolicy：明确标记命中了脚本最终制品或 shell GUI 自动化路线；如果没有这一项，验收层难以判断拒绝根因。
            "reason": f"当前是桌面任务，命令命中禁止脚本最终制品或 shell GUI 自动化路线：{', '.join(forbidden_matches)}；请改用真实 GUI/Computer Use 路线完成。",  # 修改代码+DesktopTaskPolicy：给出通俗拒绝原因和替代方向；如果没有这一项，模型和用户不知道为什么不能继续执行。
            "matched_forbidden_patterns": forbidden_matches,  # 新增代码+DesktopTaskPolicy：返回命中的具体规则；如果没有这一项，用户无法学习是哪类脚本绕路被拦住。
        }  # 新增代码+DesktopTaskPolicy：拒绝结果字典段结束；如果没有这一行，Python 字典语法不完整。
    return {  # 新增代码+DesktopTaskPolicy：普通 active 放行结果字典段开始；如果没有这一行，未命中风险的命令没有返回路径。
        "allowed": True,  # 新增代码+DesktopTaskPolicy：声明未命中最终制品风险的命令允许继续；如果没有这一项，_bash_atom 不知道是否能进入原权限流程。
        "decision": "desktop_task_bash_command_allowed",  # 新增代码+DesktopTaskPolicy：返回普通 active 放行原因码；如果没有这一项，日志无法区分白名单诊断和普通非制品命令。
        "desktop_task_active": True,  # 新增代码+DesktopTaskPolicy：返回桌面任务已激活状态；如果没有这一项，调用方无法复盘策略生效上下文。
        "forbidden_script_artifact_route": False,  # 新增代码+DesktopTaskPolicy：声明未发现脚本最终制品路线；如果没有这一项，验收层缺少负向风险字段。
        "reason": "桌面任务上下文已激活，但命令未命中脚本最终图片制品路线。",  # 新增代码+DesktopTaskPolicy：给出普通放行解释；如果没有这一项，代码小白不容易理解 active 下为什么允许。
        "matched_forbidden_patterns": [],  # 新增代码+DesktopTaskPolicy：返回空命中列表保持结构稳定；如果没有这一项，调用方需要额外判空。
    }  # 新增代码+DesktopTaskPolicy：普通 active 放行结果字典段结束；如果没有这一行，Python 字典语法不完整。
# 新增代码+DesktopTaskPolicy：函数段结束，evaluate_desktop_bash_command 到此结束；如果没有这个边界说明，代码小白不容易看出公开策略函数范围。


__all__ = ["evaluate_desktop_bash_command"]  # 新增代码+DesktopTaskPolicy：限定公开导出策略函数；如果没有这一行，通配导入可能暴露内部 helper 并增加误用风险。
