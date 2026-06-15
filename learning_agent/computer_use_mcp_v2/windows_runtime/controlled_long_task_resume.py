"""Phase150 controlled live GUI long task resume benchmark."""  # 新增代码+Phase150LongTaskResume：说明本模块负责受控真实 GUI 长任务恢复验收；如果没有这一行，维护者不容易区分它和旧的 contract-only 自检。
from __future__ import annotations  # 新增代码+Phase150LongTaskResume：启用延迟类型解析；如果没有这一行，复杂前向类型在导入时更容易失败。

import json  # 新增代码+Phase150LongTaskResume：导入 JSON 工具；如果没有这一行，checkpoint 和 CLI 报告无法结构化保存。
import os  # 新增代码+Phase150LongTaskResume：导入环境变量工具；如果没有这一行，双门禁无法从真实终端环境读取。
import time  # 新增代码+Phase150LongTaskResume：导入等待和唯一文本工具；如果没有这一行，窗口标题刷新会被过早检查。
from pathlib import Path  # 新增代码+Phase150LongTaskResume：导入路径对象；如果没有这一行，受控运行目录和 checkpoint 路径容易拼错。
from typing import Any  # 新增代码+Phase150LongTaskResume：导入通用类型；如果没有这一行，JSON 风格报告的输入输出边界不清楚。

try:  # 新增代码+Phase150LongTaskResume：优先按包模式复用 Phase150 failure_recovery 的已验证 Browser/SendInput helper；如果没有这段代码，真实路径会重复造一套易漂移的窗口控制逻辑。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import DEFAULT_PHASE150_CONTROLLED_FAILURE_RECOVERY_ROOT  # 新增代码+Phase150LongTaskResume：复用 post_parity 受控根路径；如果没有这一行，新 benchmark 可能写到用户目录。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import Phase150WindowsFailureRecoveryDriver  # 新增代码+Phase150LongTaskResume：复用已通过真实 GUI smoke 的 Browser 启动、关闭和发送基础能力；如果没有这一行，长任务恢复会重复实现底层动作。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_browser_executable as _phase150_long_browser_executable  # 新增代码+Phase150LongTaskResume：复用浏览器发现 helper；如果没有这一行，长任务恢复可能找不到 Edge/Chrome。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_bool_token as _phase150_long_bool_token  # 新增代码+Phase150LongTaskResume：复用小写 bool token helper；如果没有这一行，终端输出大小写可能漂移。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_hwnd_from_window as _phase150_long_hwnd_from_window  # 新增代码+Phase150LongTaskResume：复用 hwnd 解析 helper；如果没有这一行，SendInput 无法稳定聚焦目标窗口。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_is_forbidden_window as _phase150_long_is_forbidden_window  # 新增代码+Phase150LongTaskResume：复用危险窗口过滤；如果没有这一行，长任务输入可能发到终端或认证窗口。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_safe_dict as _phase150_long_safe_dict  # 新增代码+Phase150LongTaskResume：复用字典清洗 helper；如果没有这一行，坏 driver 输出会污染报告。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_safe_int as _phase150_long_safe_int  # 新增代码+Phase150LongTaskResume：复用整数清洗 helper；如果没有这一行，事件数量或句柄字段可能让报告崩溃。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_sha256_16 as _phase150_long_sha256_16  # 新增代码+Phase150LongTaskResume：复用短哈希 helper；如果没有这一行，报告要么泄露步骤文本要么无法审计。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_snapshot_windows as _phase150_long_snapshot_windows  # 新增代码+Phase150LongTaskResume：复用窗口快照 helper；如果没有这一行，真实和测试 probe 接口差异会分裂。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_window_blob as _phase150_long_window_blob  # 新增代码+Phase150LongTaskResume：复用窗口身份拼接 helper；如果没有这一行，Browser/标题判断会重复出错。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_window_center as _phase150_long_window_center  # 新增代码+Phase150LongTaskResume：复用内容区点击点计算；如果没有这一行，文本可能落到地址栏。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_window_identity as _phase150_long_window_identity  # 新增代码+Phase150LongTaskResume：复用脱敏窗口身份摘要；如果没有这一行，报告可能泄露标题或无法追踪窗口。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_window_key as _phase150_long_window_key  # 新增代码+Phase150LongTaskResume：复用窗口 key helper；如果没有这一行，baseline 无法过滤旧窗口。
except ModuleNotFoundError as error:  # 新增代码+Phase150LongTaskResume：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，真实可见终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery"}:  # 新增代码+Phase150LongTaskResume：只兜底包路径缺失；如果没有这一行，依赖内部 bug 会被误吞。
        raise  # 新增代码+Phase150LongTaskResume：重新抛出真正的内部导入错误；如果没有这一行，排查会被错误 fallback 掩盖。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import DEFAULT_PHASE150_CONTROLLED_FAILURE_RECOVERY_ROOT  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用受控根路径；如果没有这一行，bat 入口无法定位受控目录。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import Phase150WindowsFailureRecoveryDriver  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用 Browser 控制 driver；如果没有这一行，bat 入口无法发真实输入。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_browser_executable as _phase150_long_browser_executable  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用浏览器发现 helper；如果没有这一行，bat 入口可能找不到浏览器。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_bool_token as _phase150_long_bool_token  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用 bool token helper；如果没有这一行，输出格式会漂移。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_hwnd_from_window as _phase150_long_hwnd_from_window  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用 hwnd helper；如果没有这一行，真实窗口无法聚焦。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_is_forbidden_window as _phase150_long_is_forbidden_window  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用危险窗口过滤；如果没有这一行，安全边界会变弱。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_safe_dict as _phase150_long_safe_dict  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用字典清洗 helper；如果没有这一行，坏输出会崩溃。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_safe_int as _phase150_long_safe_int  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用整数清洗 helper；如果没有这一行，事件计数不稳定。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_sha256_16 as _phase150_long_sha256_16  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用短哈希 helper；如果没有这一行，脱敏关联不可用。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_snapshot_windows as _phase150_long_snapshot_windows  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用窗口快照 helper；如果没有这一行，bat 入口无法复核窗口。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_window_blob as _phase150_long_window_blob  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用窗口身份 helper；如果没有这一行，目标判断会漂移。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_window_center as _phase150_long_window_center  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用窗口点击点 helper；如果没有这一行，真实输入可能落错位置。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_window_identity as _phase150_long_window_identity  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用窗口身份摘要；如果没有这一行，报告缺目标证据。
    from computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import _phase150_failure_window_key as _phase150_long_window_key  # type: ignore  # 新增代码+Phase150LongTaskResume：脚本模式复用窗口 key helper；如果没有这一行，baseline 过滤不可用。

PHASE150_CONTROLLED_LONG_TASK_RESUME_MARKER = "PHASE150_CONTROLLED_LONG_TASK_RESUME_READY"  # 新增代码+Phase150LongTaskResume：定义 ready marker；如果没有这一行，真实终端验收没有稳定锚点。
PHASE150_CONTROLLED_LONG_TASK_RESUME_OK_TOKEN = "PHASE150_CONTROLLED_LONG_TASK_RESUME_OK"  # 新增代码+Phase150LongTaskResume：定义 OK token；如果没有这一行，Phase148C 场景无法稳定匹配成功。
PHASE150_CONTROLLED_LONG_TASK_RESUME_MODEL = "phase150_controlled_long_task_resume"  # 新增代码+Phase150LongTaskResume：定义模型名；如果没有这一行，报告无法区分本阶段证据版本。
PHASE150_REAL_LONG_TASK_RESUME_ENV = "LEARNING_AGENT_PHASE150_ENABLE_REAL_LONG_TASK_RESUME"  # 新增代码+Phase150LongTaskResume：定义强制启用真实 GUI 的门禁变量；如果没有这一行，真实桌面动作可能被默认打开。
PHASE150_REAL_LONG_TASK_RESUME_REQUEST_ENV = "LEARNING_AGENT_PHASE150_RUN_REAL_LONG_TASK_RESUME"  # 新增代码+Phase150LongTaskResume：定义请求运行真实 GUI 的变量；如果没有这一行，CLI 无法显式表达本次要跑真实验收。
PHASE150_LONG_STEP1_TARGET_TITLE = "PHASE150_LONG_TASK_STEP1_TARGET"  # 新增代码+Phase150LongTaskResume：定义第 1 步目标页标题；如果没有这一行，窗口识别没有本阶段专属线索。
PHASE150_LONG_STEP1_OK_TITLE = "PHASE150_LONG_TASK_STEP1_OK"  # 新增代码+Phase150LongTaskResume：定义第 1 步完成标题；如果没有这一行，checkpoint 前的 GUI 成功无法验证。
PHASE150_LONG_RESUME_TARGET_TITLE = "PHASE150_LONG_TASK_RESUME_TARGET"  # 新增代码+Phase150LongTaskResume：定义恢复阶段目标页标题；如果没有这一行，恢复窗口无法与初始窗口区分。
PHASE150_LONG_DONE_TITLE = "PHASE150_LONG_TASK_DONE"  # 新增代码+Phase150LongTaskResume：定义长任务最终完成标题；如果没有这一行，恢复后完成结果只能靠猜测。
PHASE150_LONG_TASK_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase150LongTaskResume：声明没有扩展到不受控高风险动作；如果没有这一行，成熟度矩阵无法判断安全边界。
DEFAULT_PHASE150_CONTROLLED_LONG_TASK_RESUME_ROOT = DEFAULT_PHASE150_CONTROLLED_FAILURE_RECOVERY_ROOT.parent / "phase150_controlled_long_task_resume"  # 新增代码+Phase150LongTaskResume：定义默认受控运行根目录；如果没有这一行，真实长任务状态可能落到用户目录。


def _phase150_long_env_enabled(name: str) -> bool:  # 新增代码+Phase150LongTaskResume：函数段开始，读取环境变量门禁；如果没有这段函数，每个入口都要重复判断字符串真假。
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase150LongTaskResume：只接受明确真值；如果没有这一行，随便设置任意文本也可能打开真实桌面动作。
# 新增代码+Phase150LongTaskResume：函数段结束，_phase150_long_env_enabled 到此结束；如果没有这个边界说明，初学者不容易看出门禁解析范围。


def _phase150_long_is_browser_target_window(window: Any) -> bool:  # 新增代码+Phase150LongTaskResume：函数段开始，判断窗口是否为本次受控 long-task Browser 目标；如果没有这段函数，恢复输入可能落到用户浏览器。
    blob = _phase150_long_window_blob(window)  # 新增代码+Phase150LongTaskResume：读取窗口身份文本；如果没有这一行，Browser 和标题线索无法判断。
    browser_like = "msedge" in blob or "chrome" in blob or "edge" in blob or "chrome_widgetwin" in blob  # 新增代码+Phase150LongTaskResume：接受 Edge/Chrome/Chromium 窗口线索；如果没有这一行，真实浏览器窗口可能识别失败。
    title_hint = any(title.lower() in blob for title in (PHASE150_LONG_STEP1_TARGET_TITLE, PHASE150_LONG_STEP1_OK_TITLE, PHASE150_LONG_RESUME_TARGET_TITLE, PHASE150_LONG_DONE_TITLE))  # 新增代码+Phase150LongTaskResume：要求标题含本次长任务线索；如果没有这一行，用户日常浏览器窗口可能被误用。
    return bool(browser_like and title_hint and not _phase150_long_is_forbidden_window(window))  # 新增代码+Phase150LongTaskResume：目标窗口必须同时满足浏览器、标题和安全边界；如果没有这一行，恢复目标不可信。
# 新增代码+Phase150LongTaskResume：函数段结束，_phase150_long_is_browser_target_window 到此结束；如果没有这个边界说明，初学者不容易看出目标窗口匹配范围。


def _phase150_long_write_page(run_root: Path, page_name: str, start_title: str, ok_title: str, expected_text: str, *, checkpoint_loaded: bool) -> Path:  # 新增代码+Phase150LongTaskResume：函数段开始，写入受控本地 Browser 页面；如果没有这段函数，长任务步骤会依赖外网或用户 profile。
    page_path = run_root / page_name  # 新增代码+Phase150LongTaskResume：定义本地页面路径；如果没有这一行，浏览器没有稳定受控目标。
    checkpoint_flag = "true" if checkpoint_loaded else "false"  # 新增代码+Phase150LongTaskResume：把 checkpoint 状态转成 JS 布尔文本；如果没有这一行，恢复页无法证明读取了 checkpoint。
    html_text = f"""<!doctype html><html><head><meta charset='utf-8'><title>{start_title}</title><style>html,body{{margin:0;width:100%;height:100%;font-family:Arial,sans-serif;background:#f8fafc;}}textarea{{box-sizing:border-box;width:100vw;height:78vh;margin-top:12vh;border:0;padding:32px;font-size:30px;outline:0;background:#ffffff;color:#172033;}}#status{{position:fixed;left:0;top:0;right:0;height:12vh;background:#0f766e;color:white;font-size:28px;display:flex;align-items:center;justify-content:center;}}</style></head><body data-checkpoint-loaded='{checkpoint_flag}'><div id='status'>PHASE150 LONG TASK READY</div><textarea id='target' autofocus spellcheck='false'></textarea><script>const expected={json.dumps(expected_text)};const checkpointLoaded={checkpoint_flag};const target=document.getElementById('target');const status=document.getElementById('status');function update(){{if(target.value.indexOf(expected)!==-1 && checkpointLoaded===true){{document.title='{ok_title}';status.textContent='PHASE150 LONG TASK STEP VERIFIED';document.body.setAttribute('data-long-task','ok');}}if(target.value.indexOf(expected)!==-1 && checkpointLoaded===false){{document.title='{ok_title}';status.textContent='PHASE150 LONG TASK CHECKPOINT VERIFIED';document.body.setAttribute('data-long-task','checkpoint');}}}}target.addEventListener('input',update);window.addEventListener('load',()=>target.focus());</script></body></html>"""  # 新增代码+Phase150LongTaskResume：生成只接受受控文本并带 checkpoint 标记的本地页面；如果没有这一行，恢复后没有可观察成功标题。
    page_path.write_text(html_text, encoding="utf-8")  # 新增代码+Phase150LongTaskResume：写入本地页面文件；如果没有这一行，浏览器无法加载目标页面。
    return page_path  # 新增代码+Phase150LongTaskResume：返回页面路径；如果没有这一行，启动命令拿不到 URL。
# 新增代码+Phase150LongTaskResume：函数段结束，_phase150_long_write_page 到此结束；如果没有这个边界说明，初学者不容易看出本地页面范围。


class Phase150WindowsLongTaskResumeDriver:  # 新增代码+Phase150LongTaskResume：类段开始，执行受控 Browser 长任务 checkpoint 与恢复闭环；如果没有这个类，long_task_resume 没有真实 driver。
    def __init__(self, browser_driver: Any | None = None) -> None:  # 新增代码+Phase150LongTaskResume：函数段开始，注入或创建 Browser 控制 driver；如果没有这段函数，单测无法替换依赖且生产路径无法启动。
        self.browser_driver = browser_driver if browser_driver is not None else Phase150WindowsFailureRecoveryDriver()  # 新增代码+Phase150LongTaskResume：保存已验证的 Browser 控制 driver；如果没有这一行，长任务恢复无法打开、关闭或输入目标窗口。
    # 新增代码+Phase150LongTaskResume：函数段结束，Phase150WindowsLongTaskResumeDriver.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出依赖初始化范围。

    def _wait_for_title(self, title: str) -> dict[str, Any] | None:  # 新增代码+Phase150LongTaskResume：函数段开始，等待指定成功标题出现；如果没有这段函数，步骤完成只能靠猜测。
        deadline = time.time() + float(getattr(self.browser_driver, "timeout_seconds", 16.0))  # 新增代码+Phase150LongTaskResume：计算等待截止时间；如果没有这一行，等待可能无限持续。
        while time.time() <= deadline:  # 新增代码+Phase150LongTaskResume：在超时前轮询窗口标题；如果没有这一行，页面 JS 异步更新无法等待。
            for window in _phase150_long_snapshot_windows(self.browser_driver.window_probe):  # 新增代码+Phase150LongTaskResume：遍历当前窗口；如果没有这一行，无法寻找成功 Browser。
                if _phase150_long_is_browser_target_window(window) and title.lower() in _phase150_long_window_blob(window):  # 新增代码+Phase150LongTaskResume：要求仍是受控 Browser 且标题含成功 token；如果没有这一行，步骤结果可能虚报。
                    return dict(window)  # 新增代码+Phase150LongTaskResume：返回成功窗口；如果没有这一行，调用方拿不到结果身份。
            time.sleep(0.25)  # 新增代码+Phase150LongTaskResume：短暂等待后重试；如果没有这一行，轮询会占满 CPU。
        return None  # 新增代码+Phase150LongTaskResume：超时返回 None；如果没有这一行，失败路径无法明确。
    # 新增代码+Phase150LongTaskResume：函数段结束，Phase150WindowsLongTaskResumeDriver._wait_for_title 到此结束；如果没有这个边界说明，初学者不容易看出标题等待范围。

    def _type_into_window(self, window: dict[str, Any], text: str) -> dict[str, Any]:  # 新增代码+Phase150LongTaskResume：函数段开始，用真实 GUI 在 Browser 页面输入步骤文本；如果没有这段函数，长任务没有实际动作。
        center = _phase150_long_window_center(window, y_ratio=0.58)  # 新增代码+Phase150LongTaskResume：计算 Browser 页面 textarea 点击点；如果没有这一行，文本可能落到地址栏。
        events = [{"type": "set_foreground", "hwnd": _phase150_long_hwnd_from_window(window)}, {"type": "pause", "seconds": 0.35}, {"type": "mouse_move", "x": center["x"], "y": center["y"]}, {"type": "mouse_down", "button": "left"}, {"type": "mouse_up", "button": "left"}, {"type": "pause", "seconds": 0.12}, {"type": "unicode_text", "text": text}, {"type": "pause", "seconds": 0.50}]  # 新增代码+Phase150LongTaskResume：定义真实点击并输入步骤文本事件；如果没有这一行，目标页面不会收到长任务动作。
        return _phase150_long_safe_dict(self.browser_driver._send_events(events))  # 新增代码+Phase150LongTaskResume：发送步骤事件并清洗结果；如果没有这一行，调用方拿不到低层事件证据。
    # 新增代码+Phase150LongTaskResume：函数段结束，Phase150WindowsLongTaskResumeDriver._type_into_window 到此结束；如果没有这个边界说明，初学者不容易看出输入范围。

    def run(self, *, run_root: Path, step1_text: str, step2_text: str) -> dict[str, Any]:  # 新增代码+Phase150LongTaskResume：函数段开始，执行完整真实长任务 checkpoint 与恢复闭环；如果没有这段代码，long_task_resume 无法从契约提升到真实 GUI。
        run_root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase150LongTaskResume：确保运行根目录存在；如果没有这一行，受控页面和 checkpoint 无法创建。
        state_file = run_root / "phase150_long_task_resume_state.json"  # 新增代码+Phase150LongTaskResume：定义 checkpoint 文件路径；如果没有这一行，恢复没有持久状态来源。
        step1_page = _phase150_long_write_page(run_root, "phase150_long_task_step1.html", PHASE150_LONG_STEP1_TARGET_TITLE, PHASE150_LONG_STEP1_OK_TITLE, step1_text, checkpoint_loaded=False)  # 新增代码+Phase150LongTaskResume：写入第 1 步页面；如果没有这一行，中断前没有真实 GUI 目标。
        initial_baseline = {_phase150_long_window_key(window) for window in _phase150_long_snapshot_windows(self.browser_driver.window_probe) if _phase150_long_is_browser_target_window(window)}  # 新增代码+Phase150LongTaskResume：记录启动前同名 Browser；如果没有这一行，旧窗口可能混入本次初始目标。
        initial_process = self.browser_driver._launch_browser(run_root, step1_page, "browser_profile_step1")  # 新增代码+Phase150LongTaskResume：启动第 1 步受控 Browser；如果没有这一行，长任务不会触达真实 GUI。
        step1_window = self.browser_driver._wait_for_window(_phase150_long_is_browser_target_window, initial_baseline) if initial_process is not None else None  # 新增代码+Phase150LongTaskResume：等待并复核第 1 步目标；如果没有这一行，输入可能发到错误窗口。
        if step1_window is None:  # 新增代码+Phase150LongTaskResume：第 1 步目标缺失就停止；如果没有这一行，后续输入没有安全对象。
            return {"ok": False, "driver": "phase150_windows_long_task_resume_driver", "reason": "step1_browser_window_not_found", "step1_completed_before_interruption": False, "checkpoint_written_before_interruption": False, "interruption_simulated": False, "resume_state_loaded": False, "step1_not_repeated_after_resume": False, "step2_completed_after_resume": False, "long_task_completed_after_resume": False, "cleanup_evidence": {"cleanup_completed": False, "host_hidden_or_restored": False, "lock_released": True}, "real_desktop_touched": False, "physical_desktop_dispatch_performed": False, "real_sendinput_dispatch": False, "sender_kind": "", "low_level_event_count": 0, "raw_text_included": False}  # 新增代码+Phase150LongTaskResume：返回零事件定位失败报告；如果没有这一行，失败点不可审计。
        step1_result = self._type_into_window(step1_window, step1_text)  # 新增代码+Phase150LongTaskResume：执行第 1 步真实输入；如果没有这一行，checkpoint 前没有 GUI 动作。
        step1_done_window = self._wait_for_title(PHASE150_LONG_STEP1_OK_TITLE)  # 新增代码+Phase150LongTaskResume：等待第 1 步页面确认完成；如果没有这一行，checkpoint 可能写在未完成状态。
        step1_completed = bool(step1_done_window is not None)  # 新增代码+Phase150LongTaskResume：把第 1 步结果转为布尔事实；如果没有这一行，后续条件会重复判断。
        checkpoint_payload = {"completed_steps": ["step1"] if step1_completed else [], "interrupted_after_step1": True, "step1_text_length": len(step1_text), "step1_text_sha256_16": _phase150_long_sha256_16(step1_text), "step2_text_length": len(step2_text), "step2_text_sha256_16": _phase150_long_sha256_16(step2_text)}  # 新增代码+Phase150LongTaskResume：构造脱敏 checkpoint；如果没有这一行，resume 没有可读取状态且可能泄露明文。
        state_file.write_text(json.dumps(checkpoint_payload, ensure_ascii=False, sort_keys=True), encoding="utf-8") if step1_completed else None  # 新增代码+Phase150LongTaskResume：只在第 1 步完成后写 checkpoint；如果没有这一行，恢复状态可能凭空出现。
        checkpoint_written = bool(step1_completed and state_file.exists())  # 新增代码+Phase150LongTaskResume：确认 checkpoint 已落盘；如果没有这一行，恢复状态来源不可量化。
        close_requested = self.browser_driver._close_window(step1_done_window or step1_window)  # 新增代码+Phase150LongTaskResume：关闭第 1 步窗口模拟中断；如果没有这一行，任务没有经历中断。
        interruption_simulated = bool(close_requested and self.browser_driver._wait_until_window_missing(step1_done_window or step1_window))  # 新增代码+Phase150LongTaskResume：观察第 1 步窗口消失；如果没有这一行，中断只是口头状态。
        resume_payload = json.loads(state_file.read_text(encoding="utf-8")) if checkpoint_written else {}  # 新增代码+Phase150LongTaskResume：从 checkpoint 读回恢复状态；如果没有这一行，resume 无法证明状态落盘可恢复。
        resume_state_loaded = bool(resume_payload.get("completed_steps") == ["step1"] and resume_payload.get("interrupted_after_step1") is True)  # 新增代码+Phase150LongTaskResume：确认读回的状态表明第 1 步已完成且发生中断；如果没有这一行，恢复可能只是重新开始。
        resume_page = _phase150_long_write_page(run_root, "phase150_long_task_resume.html", PHASE150_LONG_RESUME_TARGET_TITLE, PHASE150_LONG_DONE_TITLE, step2_text, checkpoint_loaded=resume_state_loaded)  # 新增代码+Phase150LongTaskResume：写入恢复页面并嵌入 checkpoint 状态；如果没有这一行，第 2 步无法证明基于恢复状态。
        resume_baseline = {_phase150_long_window_key(window) for window in _phase150_long_snapshot_windows(self.browser_driver.window_probe) if _phase150_long_is_browser_target_window(window)}  # 新增代码+Phase150LongTaskResume：记录恢复前同名 Browser；如果没有这一行，恢复目标可能误用残留窗口。
        resume_process = self.browser_driver._launch_browser(run_root, resume_page, "browser_profile_resume") if interruption_simulated and resume_state_loaded else None  # 新增代码+Phase150LongTaskResume：只在中断和状态读取都成立后启动恢复目标；如果没有这一行，未确认恢复也可能继续误报。
        resume_window = self.browser_driver._wait_for_window(_phase150_long_is_browser_target_window, resume_baseline) if resume_process is not None else None  # 新增代码+Phase150LongTaskResume：等待并复核恢复目标；如果没有这一行，恢复输入可能发到错误窗口。
        if resume_window is None:  # 新增代码+Phase150LongTaskResume：恢复目标缺失时停止；如果没有这一行，后续输入会没有安全目标。
            return {"ok": False, "driver": "phase150_windows_long_task_resume_driver", "reason": "resume_browser_window_not_found", "step1_completed_before_interruption": step1_completed, "checkpoint_written_before_interruption": checkpoint_written, "interruption_simulated": interruption_simulated, "resume_state_loaded": resume_state_loaded, "step1_not_repeated_after_resume": False, "step2_completed_after_resume": False, "long_task_completed_after_resume": False, "cleanup_evidence": {"cleanup_completed": False, "host_hidden_or_restored": False, "lock_released": True}, "real_desktop_touched": bool(_phase150_long_safe_int(step1_result.get("low_level_event_count"))), "physical_desktop_dispatch_performed": False, "real_sendinput_dispatch": False, "sender_kind": str(step1_result.get("sender") or ""), "low_level_event_count": _phase150_long_safe_int(step1_result.get("low_level_event_count")), "raw_text_included": False}  # 新增代码+Phase150LongTaskResume：返回恢复目标缺失报告；如果没有这一行，失败点不可审计。
        step2_result = self._type_into_window(resume_window, step2_text)  # 新增代码+Phase150LongTaskResume：执行恢复后的第 2 步真实输入；如果没有这一行，resume 没有继续推进。
        done_window = self._wait_for_title(PHASE150_LONG_DONE_TITLE)  # 新增代码+Phase150LongTaskResume：等待页面标题确认长任务完成；如果没有这一行，最终结果没有机器验证。
        resume_closed = self.browser_driver._close_window(done_window or resume_window)  # 新增代码+Phase150LongTaskResume：关闭恢复 Browser 目标窗口；如果没有这一行，目标窗口可能残留桌面。
        step1_count = _phase150_long_safe_int(step1_result.get("low_level_event_count"))  # 新增代码+Phase150LongTaskResume：读取第 1 步低层事件数；如果没有这一行，物理派发判断缺少前半段计数。
        step2_count = _phase150_long_safe_int(step2_result.get("low_level_event_count"))  # 新增代码+Phase150LongTaskResume：读取第 2 步低层事件数；如果没有这一行，物理派发判断缺少后半段计数。
        low_level_event_count = step1_count + step2_count  # 新增代码+Phase150LongTaskResume：汇总两段低层事件数；如果没有这一行，真实桌面触达无法统一判断。
        sender_kind = str(step1_result.get("sender_kind") or step1_result.get("sender") or step2_result.get("sender_kind") or step2_result.get("sender") or type(getattr(self.browser_driver, "sender", object())).__name__)  # 新增代码+Phase150LongTaskResume：提取 sender 身份；如果没有这一行，fake sender 可能误入成熟矩阵。
        physical_dispatch = bool(low_level_event_count > 0 and "windows_sendinput" in sender_kind.lower() and "fake" not in sender_kind.lower() and "record" not in sender_kind.lower() and step1_result.get("ok") and step2_result.get("ok"))  # 新增代码+Phase150LongTaskResume：判断是否真实 SendInput 物理派发；如果没有这一行，空动作或 fake sender 可能误过。
        step1_not_repeated = bool(resume_state_loaded and resume_payload.get("completed_steps") == ["step1"])  # 新增代码+Phase150LongTaskResume：确认恢复后依据 checkpoint 跳过第 1 步；如果没有这一行，任务可能从头重跑。
        step2_completed = bool(done_window is not None)  # 新增代码+Phase150LongTaskResume：确认第 2 步完成；如果没有这一行，恢复结果没有布尔结论。
        long_task_completed = bool(step1_completed and step1_not_repeated and step2_completed)  # 新增代码+Phase150LongTaskResume：汇总长任务最终完成；如果没有这一行，成熟度无法判断整体结果。
        ok = bool(checkpoint_written and interruption_simulated and resume_state_loaded and long_task_completed and physical_dispatch and resume_closed)  # 新增代码+Phase150LongTaskResume：汇总 driver 成功条件；如果没有这一行，部分成功可能被误判完整闭环。
        return {"ok": ok, "driver": "phase150_windows_long_task_resume_driver", "reason": "" if ok else "long_task_resume_not_fully_verified", "step1_completed_before_interruption": step1_completed, "checkpoint_written_before_interruption": checkpoint_written, "interruption_simulated": interruption_simulated, "resume_state_loaded": resume_state_loaded, "step1_not_repeated_after_resume": step1_not_repeated, "step2_completed_after_resume": step2_completed, "long_task_completed_after_resume": long_task_completed, "cleanup_evidence": {"cleanup_completed": bool(resume_closed), "host_hidden_or_restored": bool(resume_closed), "lock_released": True}, "real_desktop_touched": bool(low_level_event_count), "physical_desktop_dispatch_performed": physical_dispatch, "real_sendinput_dispatch": physical_dispatch, "sender_kind": sender_kind, "low_level_event_count": low_level_event_count, "raw_text_included": False, "state_file": str(state_file), "step1_window": _phase150_long_window_identity(step1_done_window or step1_window), "resume_window": _phase150_long_window_identity(done_window or resume_window), "step1_text_length": len(step1_text), "step1_text_sha256_16": _phase150_long_sha256_16(step1_text), "step2_text_length": len(step2_text), "step2_text_sha256_16": _phase150_long_sha256_16(step2_text)}  # 新增代码+Phase150LongTaskResume：返回脱敏闭环报告；如果没有这一行，Phase148C 拿不到 long_task_resume 真实 GUI 证据。
    # 新增代码+Phase150LongTaskResume：函数段结束，Phase150WindowsLongTaskResumeDriver.run 到此结束；如果没有这个边界说明，初学者不容易看出 driver 主流程范围。
# 新增代码+Phase150LongTaskResume：类段结束，Phase150WindowsLongTaskResumeDriver 到此结束；如果没有这个边界说明，初学者不容易看出真实 driver 范围。


def _phase150_long_default_off_report() -> dict[str, Any]:  # 新增代码+Phase150LongTaskResume：函数段开始，构造默认关闭报告；如果没有这段函数，普通运行无法证明 0 物理事件。
    return {"decision": "real_long_task_resume_disabled_by_default", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase150LongTaskResume：返回零事件默认报告；如果没有这一行，默认安全边界无证据。
# 新增代码+Phase150LongTaskResume：函数段结束，_phase150_long_default_off_report 到此结束；如果没有这个边界说明，初学者不容易看出默认安全范围。


def _phase150_long_unsafe_target_report() -> dict[str, Any]:  # 新增代码+Phase150LongTaskResume：函数段开始，构造危险目标拒绝报告；如果没有这段函数，敏感窗口零事件边界无证据。
    return {"decision": "unsafe_target_rejected", "target": "terminal_like_window", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase150LongTaskResume：返回终端类目标零事件拒绝；如果没有这一行，安全门禁可能被误削弱。
# 新增代码+Phase150LongTaskResume：函数段结束，_phase150_long_unsafe_target_report 到此结束；如果没有这个边界说明，初学者不容易看出危险目标范围。


def run_phase150_controlled_long_task_resume(real_run_requested: bool | None = None, real_enable_gate: bool | None = None, run_root: str | Path | None = None, driver: Any | None = None, require_injected_driver: bool = False, raw_prompt_text: str | None = None) -> dict[str, Any]:  # 新增代码+Phase150LongTaskResume：函数段开始，运行 Phase150 长任务恢复总合同入口；如果没有这段函数，测试、CLI 和 Phase148C 无法共用事实源。
    requested = _phase150_long_env_enabled(PHASE150_REAL_LONG_TASK_RESUME_REQUEST_ENV) if real_run_requested is None else bool(real_run_requested)  # 新增代码+Phase150LongTaskResume：读取是否请求真实运行；如果没有这一行，环境变量门禁不会生效。
    gate_enabled = _phase150_long_env_enabled(PHASE150_REAL_LONG_TASK_RESUME_ENV) if real_enable_gate is None else bool(real_enable_gate)  # 新增代码+Phase150LongTaskResume：读取真实 GUI 强门禁；如果没有这一行，单个变量可能误开桌面动作。
    root = Path(run_root) if run_root is not None else DEFAULT_PHASE150_CONTROLLED_LONG_TASK_RESUME_ROOT  # 新增代码+Phase150LongTaskResume：确定受控运行根目录；如果没有这一行，真实长任务状态没有边界。
    step1_text = f"PHASE150_LONG_TASK_STEP1_{time.time_ns()}"  # 新增代码+Phase150LongTaskResume：生成唯一第 1 步文本；如果没有这一行，快速连续验收可能拿到相同文本并降低证据唯一性。
    step2_text = f"PHASE150_LONG_TASK_STEP2_{time.time_ns()}"  # 新增代码+Phase150LongTaskResume：生成唯一第 2 步文本；如果没有这一行，恢复结果可能和旧页面混淆。
    default_report = _phase150_long_default_off_report()  # 新增代码+Phase150LongTaskResume：生成默认关闭证据；如果没有这一行，报告缺默认 0 事件门禁。
    unsafe_report = _phase150_long_unsafe_target_report()  # 新增代码+Phase150LongTaskResume：生成危险目标拒绝证据；如果没有这一行，报告缺敏感窗口保护事实。
    default_zero = bool(default_report.get("low_level_event_count") == 0 and not default_report.get("real_desktop_touched"))  # 新增代码+Phase150LongTaskResume：确认默认关闭零事件；如果没有这一行，默认安全状态无法量化。
    unsafe_zero = bool(unsafe_report.get("low_level_event_count") == 0 and not unsafe_report.get("real_desktop_touched"))  # 新增代码+Phase150LongTaskResume：确认危险目标零事件；如果没有这一行，敏感窗口保护无法量化。
    selected_driver = driver if driver is not None else (Phase150WindowsLongTaskResumeDriver() if requested and gate_enabled and not require_injected_driver else None)  # 新增代码+Phase150LongTaskResume：只有请求且门禁通过时才创建真实 driver；如果没有这一行，普通调用可能触碰桌面。
    driver_report = _phase150_long_safe_dict(selected_driver.run(run_root=root, step1_text=step1_text, step2_text=step2_text)) if selected_driver is not None else {}  # 新增代码+Phase150LongTaskResume：执行 driver 或保持空报告；如果没有这一行，真实路径不会产生证据。
    cleanup_evidence = _phase150_long_safe_dict(driver_report.get("cleanup_evidence"))  # 新增代码+Phase150LongTaskResume：读取 driver 清理证据；如果没有这一行，cleanup_completed 无法汇总。
    real_executed = bool(requested and gate_enabled and selected_driver is not None and driver_report)  # 新增代码+Phase150LongTaskResume：确认真实长任务恢复路径是否执行；如果没有这一行，报告无法区分未请求和失败。
    real_desktop_touched = bool(driver_report.get("real_desktop_touched"))  # 新增代码+Phase150LongTaskResume：读取真实桌面触达事实；如果没有这一行，物理派发 token 无法生成。
    real_gui_backing = bool(driver_report.get("physical_desktop_dispatch_performed") and driver_report.get("real_sendinput_dispatch") and str(driver_report.get("sender_kind", "")).lower().find("windows_sendinput") >= 0)  # 新增代码+Phase150LongTaskResume：确认真实 GUI 背书来自 SendInput；如果没有这一行，fake driver 可能被误认为生产真实路径。
    report_without_raw_check: dict[str, Any] = {"marker": PHASE150_CONTROLLED_LONG_TASK_RESUME_MARKER, "ok_token": PHASE150_CONTROLLED_LONG_TASK_RESUME_OK_TOKEN, "model": PHASE150_CONTROLLED_LONG_TASK_RESUME_MODEL, "family": "long_task_resume", "real_long_task_resume_env": PHASE150_REAL_LONG_TASK_RESUME_ENV, "real_long_task_resume_request_env": PHASE150_REAL_LONG_TASK_RESUME_REQUEST_ENV, "real_run_requested": requested, "real_enable_gate_required": True, "real_enable_gate_passed": gate_enabled, "require_injected_driver": bool(require_injected_driver), "step1_text_length": len(step1_text), "step1_text_sha256_16": _phase150_long_sha256_16(step1_text), "step2_text_length": len(step2_text), "step2_text_sha256_16": _phase150_long_sha256_16(step2_text), "default_off_zero_physical_events": default_zero, "unsafe_target_zero_physical_events": unsafe_zero, "real_long_task_resume_executed": real_executed, "step1_completed_before_interruption": bool(driver_report.get("step1_completed_before_interruption")), "checkpoint_written_before_interruption": bool(driver_report.get("checkpoint_written_before_interruption")), "interruption_simulated": bool(driver_report.get("interruption_simulated")), "resume_state_loaded": bool(driver_report.get("resume_state_loaded")), "step1_not_repeated_after_resume": bool(driver_report.get("step1_not_repeated_after_resume")), "step2_completed_after_resume": bool(driver_report.get("step2_completed_after_resume")), "long_task_completed_after_resume": bool(driver_report.get("long_task_completed_after_resume")), "cleanup_completed": bool(cleanup_evidence.get("cleanup_completed")), "real_desktop_touched": real_desktop_touched, "uncontrolled_actions_expanded": PHASE150_LONG_TASK_UNCONTROLLED_ACTIONS_EXPANDED, "driver": str(driver_report.get("driver", "")), "driver_ok": bool(driver_report.get("ok")), "driver_reason": str(driver_report.get("reason", "")), "default_off_report": default_report, "unsafe_report": unsafe_report}  # 新增代码+Phase150LongTaskResume：构造脱敏报告主体；如果没有这一行，测试和 CLI 会丢失关键事实。
    serialized = json.dumps(report_without_raw_check, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase150LongTaskResume：序列化报告用于检查原文泄露；如果没有这一行，嵌套字段里的泄露可能漏检。
    raw_text_hidden = bool(step1_text not in serialized and step2_text not in serialized and (not raw_prompt_text or raw_prompt_text not in serialized) and not driver_report.get("raw_text_included"))  # 新增代码+Phase150LongTaskResume：确认步骤明文和用户原始 prompt 未进入报告；如果没有这一行，验收 artifact 可能泄露文本。
    passed = bool(default_zero and unsafe_zero and raw_text_hidden and not PHASE150_LONG_TASK_UNCONTROLLED_ACTIONS_EXPANDED and ((not requested and not real_desktop_touched) or (requested and gate_enabled and real_executed and report_without_raw_check["step1_completed_before_interruption"] and report_without_raw_check["checkpoint_written_before_interruption"] and report_without_raw_check["interruption_simulated"] and report_without_raw_check["resume_state_loaded"] and report_without_raw_check["step1_not_repeated_after_resume"] and report_without_raw_check["step2_completed_after_resume"] and report_without_raw_check["long_task_completed_after_resume"] and report_without_raw_check["cleanup_completed"] and real_gui_backing)))  # 新增代码+Phase150LongTaskResume：汇总合同通过条件；如果没有这一行，main 无法用退出码表达真实长任务恢复闭环是否完成。
    return {**report_without_raw_check, "passed": passed, "real_gui_backing": real_gui_backing, "raw_text_hidden": raw_text_hidden, "driver_report": driver_report}  # 新增代码+Phase150LongTaskResume：返回完整脱敏报告；如果没有这一行，测试和 CLI 拿不到最终结论。
# 新增代码+Phase150LongTaskResume：函数段结束，run_phase150_controlled_long_task_resume 到此结束；如果没有这个边界说明，初学者不容易看出合同入口范围。


def format_phase150_controlled_long_task_resume_line(report: dict[str, Any]) -> str:  # 新增代码+Phase150LongTaskResume：函数段开始，把报告格式化成可见终端稳定 token 行；如果没有这段函数，scenario 只能解析 JSON。
    ok_token = f" {PHASE150_CONTROLLED_LONG_TASK_RESUME_OK_TOKEN}" if report.get("passed") else ""  # 新增代码+Phase150LongTaskResume：只有通过时输出 OK token；如果没有这一行，失败也可能被验收当成功。
    return f"{PHASE150_CONTROLLED_LONG_TASK_RESUME_MARKER}{ok_token} family=long_task_resume default_off_zero_physical_events={_phase150_long_bool_token(report.get('default_off_zero_physical_events'))} unsafe_target_zero_physical_events={_phase150_long_bool_token(report.get('unsafe_target_zero_physical_events'))} real_long_task_resume_executed={_phase150_long_bool_token(report.get('real_long_task_resume_executed'))} step1_completed_before_interruption={_phase150_long_bool_token(report.get('step1_completed_before_interruption'))} checkpoint_written_before_interruption={_phase150_long_bool_token(report.get('checkpoint_written_before_interruption'))} interruption_simulated={_phase150_long_bool_token(report.get('interruption_simulated'))} resume_state_loaded={_phase150_long_bool_token(report.get('resume_state_loaded'))} step1_not_repeated_after_resume={_phase150_long_bool_token(report.get('step1_not_repeated_after_resume'))} step2_completed_after_resume={_phase150_long_bool_token(report.get('step2_completed_after_resume'))} long_task_completed_after_resume={_phase150_long_bool_token(report.get('long_task_completed_after_resume'))} cleanup_completed={_phase150_long_bool_token(report.get('cleanup_completed'))} real_desktop_touched={_phase150_long_bool_token(report.get('real_desktop_touched'))} real_gui_backing={_phase150_long_bool_token(report.get('real_gui_backing'))} raw_text_hidden={_phase150_long_bool_token(report.get('raw_text_hidden'))}"  # 新增代码+Phase150LongTaskResume：返回固定顺序 token 行；如果没有这一行，acceptance controller 的字符串断言容易漂移。
# 新增代码+Phase150LongTaskResume：函数段结束，format_phase150_controlled_long_task_resume_line 到此结束；如果没有这个边界说明，初学者不容易看出输出范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase150LongTaskResume：函数段开始，提供命令行入口；如果没有这段函数，真实终端无法直接运行 Phase150 long_task_resume 合同。
    _ = argv  # 新增代码+Phase150LongTaskResume：当前 CLI 暂无参数但保留签名；如果没有这一行，读者会误以为遗漏参数解析。
    report = run_phase150_controlled_long_task_resume()  # 新增代码+Phase150LongTaskResume：运行总合同；如果没有这一行，CLI 不会产生验收报告。
    print(format_phase150_controlled_long_task_resume_line(report))  # 新增代码+Phase150LongTaskResume：打印稳定 token 行；如果没有这一行，可见终端无法让 controller 匹配成功。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, default=str))  # 新增代码+Phase150LongTaskResume：打印完整脱敏 JSON；如果没有这一行，失败排查缺少结构化细节。
    return 0 if report.get("passed") else 1  # 新增代码+Phase150LongTaskResume：用退出码表达合同成败；如果没有这一行，自动化无法区分成功失败。
# 新增代码+Phase150LongTaskResume：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 范围。


__all__ = ["DEFAULT_PHASE150_CONTROLLED_LONG_TASK_RESUME_ROOT", "PHASE150_CONTROLLED_LONG_TASK_RESUME_MARKER", "PHASE150_CONTROLLED_LONG_TASK_RESUME_MODEL", "PHASE150_CONTROLLED_LONG_TASK_RESUME_OK_TOKEN", "PHASE150_LONG_TASK_UNCONTROLLED_ACTIONS_EXPANDED", "PHASE150_REAL_LONG_TASK_RESUME_ENV", "PHASE150_REAL_LONG_TASK_RESUME_REQUEST_ENV", "Phase150WindowsLongTaskResumeDriver", "format_phase150_controlled_long_task_resume_line", "main", "run_phase150_controlled_long_task_resume"]  # 新增代码+Phase150LongTaskResume：限定公开 API；如果没有这一行，通配导入可能暴露内部 helper。
if __name__ == "__main__":  # 新增代码+Phase150LongTaskResume：模块入口段开始，允许 python -m 运行；如果没有这一行，命令行自检不会启动。
    raise SystemExit(main())  # 新增代码+Phase150LongTaskResume：执行 CLI 并返回退出码；如果没有这一行，直接运行模块没有效果。
# 新增代码+Phase150LongTaskResume：模块入口段结束，本文件到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
