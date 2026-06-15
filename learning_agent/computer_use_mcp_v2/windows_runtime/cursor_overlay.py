"""Computer Use 鼠标来源可视标识叠加层。"""  # 新增代码+ComputerUseCursorOverlay：集中放置橙色鼠标标识逻辑；如果没有这个文件，用户只能猜测鼠标到底是不是 Computer Use 控制的。
from __future__ import annotations  # 新增代码+ComputerUseCursorOverlay：延迟解析类型注解，避免运行时因为前向引用影响旧入口；如果没有这一行，部分类型注解在旧 Python 路径下可能提前求值失败。

import math  # 新增代码+ComputerUseCursorOverlay：用于计算橙色放射线的角度；如果没有这一行，叠加层只能画静态三角形，视觉辨识度会下降。
import os  # 新增代码+ComputerUseCursorOverlay：读取开关环境变量；如果没有这一行，用户无法临时关闭叠加层排查问题。
import queue  # 新增代码+ComputerUseCursorOverlay：让真实输入线程把显示命令安全交给 UI 线程；如果没有这一行，Tk 窗口可能被跨线程直接操作而不稳定。
import sys  # 新增代码+ComputerUseCursorOverlay：判断当前是否为 Windows；如果没有这一行，非 Windows 环境可能误尝试创建 Windows 桌面叠加层。
import threading  # 新增代码+ComputerUseCursorOverlay：用后台线程承载叠加层窗口循环；如果没有这一行，鼠标动作会被 UI 主循环阻塞。
from dataclasses import dataclass, field  # 新增代码+ComputerUseCursorOverlay：用轻量状态对象记录最近显示结果；如果没有这一行，状态返回会散落成难维护的临时字典。
from typing import Any  # 新增代码+ComputerUseCursorOverlay：表达低层事件和工具返回值的通用结构；如果没有这一行，类型边界会变得含糊。

COMPUTER_USE_CURSOR_OVERLAY_ENV_VAR = "LEARNING_AGENT_COMPUTER_USE_CURSOR_OVERLAY"  # 新增代码+ComputerUseCursorOverlay：定义可关闭橙色叠加层的环境变量名；如果没有这一行，用户无法通过配置控制该功能。
COMPUTER_USE_CURSOR_OVERLAY_MARKER = "computer_use_cursor_overlay_v1"  # 新增代码+ComputerUseCursorOverlay：给执行结果打上可追踪标记；如果没有这一行，日志里无法确认本次动作是否经过叠加层包装器。
COMPUTER_USE_CURSOR_OVERLAY_FALSE_VALUES = {"0", "false", "no", "off", "disable", "disabled"}  # 新增代码+ComputerUseCursorOverlay：集中定义关闭开关的文本；如果没有这一行，关闭逻辑会分散且容易拼写不一致。
COMPUTER_USE_CURSOR_OVERLAY_MOUSE_EVENT_TYPES = {"mouse_move", "mouse_down", "mouse_up", "mouse_wheel"}  # 新增代码+ComputerUseCursorOverlay：只让真实鼠标低层事件触发标识；如果没有这一行，键盘输入也可能误显示鼠标来源标识。


def _normalise_platform(platform: str | None = None) -> str:  # 新增代码+ComputerUseCursorOverlay：函数段开始，统一平台字符串来源；如果没有这段函数，测试和真实运行会各自写平台判断。
    return platform or sys.platform  # 新增代码+ComputerUseCursorOverlay：优先使用测试注入平台，否则读取真实平台；如果没有这一行，单元测试无法稳定模拟 Windows。
# 新增代码+ComputerUseCursorOverlay：函数段结束，_normalise_platform 到此结束；如果没有这个边界说明，初学者不容易看出平台归一化范围。


def cursor_overlay_enabled(platform: str | None = None, environ: dict[str, str] | None = None) -> bool:  # 新增代码+ComputerUseCursorOverlay：函数段开始，判断叠加层是否允许启动；如果没有这段函数，开关判断会散落到发送器和 UI 类里。
    current_platform = _normalise_platform(platform)  # 新增代码+ComputerUseCursorOverlay：得到本次判断使用的平台；如果没有这一行，Windows 限定逻辑没有稳定输入。
    if current_platform != "win32":  # 新增代码+ComputerUseCursorOverlay：只在 Windows 桌面启用可见叠加层；如果没有这一行，Linux 或测试环境可能尝试打开不存在的桌面窗口。
        return False  # 新增代码+ComputerUseCursorOverlay：非 Windows 直接关闭；如果没有这一行，跨平台运行会产生无意义 UI 错误。
    source = os.environ if environ is None else environ  # 新增代码+ComputerUseCursorOverlay：选择真实环境变量或测试注入环境；如果没有这一行，测试无法验证关闭开关。
    raw_value = str(source.get(COMPUTER_USE_CURSOR_OVERLAY_ENV_VAR, "1")).strip().lower()  # 新增代码+ComputerUseCursorOverlay：读取开关值并规范化；如果没有这一行，大小写和空格会导致开关不可靠。
    return raw_value not in COMPUTER_USE_CURSOR_OVERLAY_FALSE_VALUES  # 新增代码+ComputerUseCursorOverlay：默认启用，只有明确关闭才关闭；如果没有这一行，用户看不到默认的 Computer Use 鼠标来源标识。
# 新增代码+ComputerUseCursorOverlay：函数段结束，cursor_overlay_enabled 到此结束；如果没有这个边界说明，初学者不容易看出开关判断范围。


def _point_from_event(event: dict[str, Any]) -> tuple[int, int] | None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，从单个低层事件里提取坐标；如果没有这段函数，坐标解析会在循环里重复手写。
    event_type = str(event.get("type", ""))  # 新增代码+ComputerUseCursorOverlay：读取事件类型；如果没有这一行，无法区分鼠标事件和键盘事件。
    if event_type not in COMPUTER_USE_CURSOR_OVERLAY_MOUSE_EVENT_TYPES:  # 新增代码+ComputerUseCursorOverlay：过滤非鼠标低层事件；如果没有这一行，type_text 等键盘动作也会误触发鼠标标识。
        return None  # 新增代码+ComputerUseCursorOverlay：非鼠标事件不提供坐标；如果没有这一行，后续转换可能把空值当坐标。
    raw_x = event.get("x")  # 新增代码+ComputerUseCursorOverlay：读取事件里的横坐标；如果没有这一行，叠加层不知道要贴近哪个鼠标位置。
    raw_y = event.get("y")  # 新增代码+ComputerUseCursorOverlay：读取事件里的纵坐标；如果没有这一行，叠加层无法定位到鼠标附近。
    if raw_x is None or raw_y is None:  # 新增代码+ComputerUseCursorOverlay：允许 mouse_down 等无坐标事件跳过；如果没有这一行，按钮事件可能因为缺坐标报错。
        return None  # 新增代码+ComputerUseCursorOverlay：缺坐标的鼠标事件不触发定位；如果没有这一行，叠加层可能显示在错误位置。
    try:  # 新增代码+ComputerUseCursorOverlay：保护数字转换过程；如果没有这一行，坏坐标会让真实鼠标动作一起失败。
        return int(round(float(raw_x))), int(round(float(raw_y)))  # 新增代码+ComputerUseCursorOverlay：把坐标转成窗口定位需要的整数；如果没有这一行，Tk geometry 不能稳定接受坐标。
    except (TypeError, ValueError):  # 新增代码+ComputerUseCursorOverlay：捕获无法转换的坐标；如果没有这一行，异常会穿透到底层输入执行链路。
        return None  # 新增代码+ComputerUseCursorOverlay：坏坐标只跳过标识，不影响真实动作；如果没有这一行，显示功能会变成动作执行风险点。
# 新增代码+ComputerUseCursorOverlay：函数段结束，_point_from_event 到此结束；如果没有这个边界说明，初学者不容易看出坐标解析范围。


def extract_cursor_overlay_point(events: list[dict[str, Any]]) -> tuple[int, int] | None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，从一批低层事件中取最后一个有效鼠标坐标；如果没有这段函数，包装器无法知道标识显示在哪里。
    point: tuple[int, int] | None = None  # 新增代码+ComputerUseCursorOverlay：保存最近一次有效坐标；如果没有这一行，循环结束后没有可返回的定位结果。
    for event in events:  # 新增代码+ComputerUseCursorOverlay：按顺序扫描低层事件；如果没有这一行，无法处理 click 展开的多步事件。
        if not isinstance(event, dict):  # 新增代码+ComputerUseCursorOverlay：保护调用方传入异常事件对象；如果没有这一行，非字典事件会在 get 调用时报错。
            continue  # 新增代码+ComputerUseCursorOverlay：跳过异常事件但不影响真实动作转发；如果没有这一行，单个坏事件会破坏整批显示判断。
        next_point = _point_from_event(event)  # 新增代码+ComputerUseCursorOverlay：尝试从当前事件提取坐标；如果没有这一行，无法更新叠加层位置。
        if next_point is not None:  # 新增代码+ComputerUseCursorOverlay：只接受有效坐标；如果没有这一行，后续无坐标按钮事件会覆盖掉正确位置。
            point = next_point  # 新增代码+ComputerUseCursorOverlay：记录最后一次有效坐标；如果没有这一行，drag 或 click 可能显示在起点而不是当前点。
    return point  # 新增代码+ComputerUseCursorOverlay：返回最后有效坐标或空；如果没有这一行，包装器无法决定是否显示标识。
# 新增代码+ComputerUseCursorOverlay：函数段结束，extract_cursor_overlay_point 到此结束；如果没有这个边界说明，初学者不容易看出事件扫描范围。


@dataclass  # 新增代码+ComputerUseCursorOverlay：把叠加层状态声明为数据对象；如果没有这一行，状态字段需要手写初始化和复制逻辑。
class ComputerUseCursorOverlayState:  # 新增代码+ComputerUseCursorOverlay：类段开始，保存最近一次叠加层状态；如果没有这段类，status 无法稳定说明显示情况。
    enabled: bool = False  # 新增代码+ComputerUseCursorOverlay：记录叠加层是否被允许启用；如果没有这一行，调试时看不出是平台关闭还是显示失败。
    visible_requested: bool = False  # 新增代码+ComputerUseCursorOverlay：记录最近是否请求过显示；如果没有这一行，日志里无法确认鼠标事件是否触发标识。
    last_point: dict[str, int] = field(default_factory=dict)  # 新增代码+ComputerUseCursorOverlay：保存最近显示坐标；如果没有这一行，调试时不知道标识被放到了哪里。
    last_error: str = ""  # 新增代码+ComputerUseCursorOverlay：保存最近 UI 错误；如果没有这一行，叠加层失败时只能沉默。
# 新增代码+ComputerUseCursorOverlay：类段结束，ComputerUseCursorOverlayState 到此结束；如果没有这个边界说明，初学者不容易看出状态对象范围。


class _TkCursorOverlayWindow:  # 新增代码+ComputerUseCursorOverlay：类段开始，负责真实 Windows 桌面上的可见橙色窗口；如果没有这段类，叠加层只能停留在日志层面。
    def __init__(self, size: int = 96, transparent_color: str = "white") -> None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，初始化 Tk 叠加层窗口控制器；如果没有这段函数，UI 线程没有尺寸和队列状态。
        self.size = int(size)  # 新增代码+ComputerUseCursorOverlay：保存叠加层画布尺寸；如果没有这一行，绘制和定位会缺少统一大小。
        self.transparent_color = transparent_color  # 新增代码+ComputerUseCursorOverlay：保存透明背景色；如果没有这一行，叠加层会显示成白色方块。
        self._commands: queue.Queue[dict[str, Any]] = queue.Queue()  # 新增代码+ComputerUseCursorOverlay：建立跨线程命令队列；如果没有这一行，输入线程无法安全通知 UI 显示或隐藏。
        self._thread: threading.Thread | None = None  # 新增代码+ComputerUseCursorOverlay：保存 UI 线程对象；如果没有这一行，重复动作会反复创建窗口线程。
        self._started = False  # 新增代码+ComputerUseCursorOverlay：记录 UI 线程是否已启动；如果没有这一行，每次鼠标动作都可能启动一个新窗口。
        self._last_error = ""  # 新增代码+ComputerUseCursorOverlay：保存 UI 层最近错误；如果没有这一行，status 不能解释窗口失败原因。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，_TkCursorOverlayWindow.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def start(self) -> None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，懒启动叠加层 UI 线程；如果没有这段函数，动作执行时没有窗口循环接收显示命令。
        if self._started:  # 新增代码+ComputerUseCursorOverlay：避免重复启动 UI 线程；如果没有这一行，多次动作会创建多个顶层窗口。
            return  # 新增代码+ComputerUseCursorOverlay：已经启动时直接返回；如果没有这一行，后续代码会重复创建线程。
        self._started = True  # 新增代码+ComputerUseCursorOverlay：标记线程已启动；如果没有这一行，快速连续动作可能重复进入启动流程。
        self._thread = threading.Thread(target=self._run_ui_loop, name="ComputerUseCursorOverlay", daemon=True)  # 新增代码+ComputerUseCursorOverlay：创建后台 UI 线程；如果没有这一行，Tk 主循环会阻塞真实鼠标动作。
        self._thread.start()  # 新增代码+ComputerUseCursorOverlay：启动 UI 线程；如果没有这一行，队列里的显示命令永远不会被消费。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，_TkCursorOverlayWindow.start 到此结束；如果没有这个边界说明，初学者不容易看出懒启动范围。

    def show(self, x: int, y: int, label: str) -> None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，向 UI 线程请求显示标识；如果没有这段函数，低层 sender 无法让用户看到来源提示。
        self.start()  # 新增代码+ComputerUseCursorOverlay：确保窗口线程已经启动；如果没有这一行，第一次鼠标动作不会显示标识。
        self._commands.put({"kind": "show", "x": int(x), "y": int(y), "label": str(label)})  # 新增代码+ComputerUseCursorOverlay：把显示命令放入线程安全队列；如果没有这一行，UI 线程不知道要显示到哪个坐标。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，_TkCursorOverlayWindow.show 到此结束；如果没有这个边界说明，初学者不容易看出显示请求范围。

    def hide(self) -> None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，向 UI 线程请求立即隐藏标识；如果没有这段函数，标识可能一直留在屏幕上。
        self.start()  # 新增代码+ComputerUseCursorOverlay：确保窗口线程已启动后再发隐藏命令；如果没有这一行，首次 hide 可能丢失命令状态。
        self._commands.put({"kind": "hide"})  # 新增代码+ComputerUseCursorOverlay：把隐藏命令放入队列；如果没有这一行，UI 线程不会收起叠加层。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，_TkCursorOverlayWindow.hide 到此结束；如果没有这个边界说明，初学者不容易看出隐藏请求范围。

    def hide_later(self, delay_seconds: float) -> None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，向 UI 线程请求短暂停留后隐藏；如果没有这段函数，用户可能来不及看到动作来源。
        self.start()  # 新增代码+ComputerUseCursorOverlay：确保窗口线程已经启动；如果没有这一行，延迟隐藏命令无人处理。
        self._commands.put({"kind": "hide_later", "delay_seconds": float(delay_seconds)})  # 新增代码+ComputerUseCursorOverlay：把延迟隐藏命令交给 UI 线程；如果没有这一行，显示标识会缺少自动清理。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，_TkCursorOverlayWindow.hide_later 到此结束；如果没有这个边界说明，初学者不容易看出延迟隐藏范围。

    def status(self) -> dict[str, Any]:  # 新增代码+ComputerUseCursorOverlay：函数段开始，返回 UI 窗口状态；如果没有这段函数，调试时不知道叠加层是否成功启动。
        return {"ui": "tk_click_through_overlay", "started": self._started, "last_error": self._last_error}  # 新增代码+ComputerUseCursorOverlay：返回最小可读状态；如果没有这一行，sender 结果无法说明 UI 层健康度。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，_TkCursorOverlayWindow.status 到此结束；如果没有这个边界说明，初学者不容易看出状态输出范围。

    def _run_ui_loop(self) -> None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，在后台线程运行 Tk 窗口循环；如果没有这段函数，叠加层没有真实可见窗口。
        try:  # 新增代码+ComputerUseCursorOverlay：保护 tkinter 导入；如果没有这一行，没有 Tk 的环境会让真实输入链路崩溃。
            import tkinter as tk  # 新增代码+ComputerUseCursorOverlay：导入标准库 Tk UI；如果没有这一行，无法创建轻量桌面透明窗口。
        except Exception as error:  # 新增代码+ComputerUseCursorOverlay：捕获 tkinter 不可用错误；如果没有这一行，异常会从后台线程静默或破坏流程。
            self._last_error = f"tkinter_unavailable:{error}"  # 新增代码+ComputerUseCursorOverlay：记录 UI 不可用原因；如果没有这一行，用户只能看到标识没出现却不知道原因。
            return  # 新增代码+ComputerUseCursorOverlay：UI 不可用时结束线程；如果没有这一行，后续代码会继续访问不存在的 tk。
        root = tk.Tk()  # 新增代码+ComputerUseCursorOverlay：创建隐藏根窗口；如果没有这一行，Tk 无法管理后续顶层窗口。
        root.withdraw()  # 新增代码+ComputerUseCursorOverlay：隐藏根窗口；如果没有这一行，屏幕上会多出一个无用空窗口。
        window = tk.Toplevel(root)  # 新增代码+ComputerUseCursorOverlay：创建真正显示橙色标识的顶层窗口；如果没有这一行，没有可见叠加层载体。
        window.overrideredirect(True)  # 新增代码+ComputerUseCursorOverlay：移除标题栏和边框；如果没有这一行，用户会看到普通窗口装饰而不是鼠标标识。
        window.attributes("-topmost", True)  # 新增代码+ComputerUseCursorOverlay：让标识浮在普通应用窗口之上；如果没有这一行，标识可能被目标软件挡住。
        try:  # 新增代码+ComputerUseCursorOverlay：保护 Windows 透明色设置；如果没有这一行，不支持透明属性时会影响 UI 循环。
            window.attributes("-transparentcolor", self.transparent_color)  # 新增代码+ComputerUseCursorOverlay：把白色背景变成透明；如果没有这一行，标识会带着白色方框遮挡目标。
        except Exception as error:  # 新增代码+ComputerUseCursorOverlay：捕获透明属性失败；如果没有这一行，少数 Tk 版本会直接中断叠加层。
            self._last_error = f"transparentcolor_unavailable:{error}"  # 新增代码+ComputerUseCursorOverlay：记录透明属性失败但继续运行；如果没有这一行，排查白底窗口会很困难。
        canvas = tk.Canvas(window, width=self.size, height=self.size, bg=self.transparent_color, highlightthickness=0, bd=0)  # 新增代码+ComputerUseCursorOverlay：创建无边框画布；如果没有这一行，橙色图形没有绘制区域。
        canvas.pack()  # 新增代码+ComputerUseCursorOverlay：把画布放进顶层窗口；如果没有这一行，窗口内不会显示任何图形。
        self._draw_overlay(canvas)  # 新增代码+ComputerUseCursorOverlay：绘制橙色光芒和指针；如果没有这一行，叠加层只是透明空窗口。
        self._make_click_through(window)  # 新增代码+ComputerUseCursorOverlay：让叠加层不拦截鼠标点击；如果没有这一行，标识可能挡住 Computer Use 正要点击的目标。
        window.withdraw()  # 新增代码+ComputerUseCursorOverlay：启动后先隐藏窗口；如果没有这一行，未执行动作时也会显示标识。

        def poll_commands() -> None:  # 新增代码+ComputerUseCursorOverlay：内部函数段开始，定时消费跨线程命令；如果没有这段函数，显示和隐藏命令不会生效。
            self._drain_commands(root, window)  # 新增代码+ComputerUseCursorOverlay：处理队列中所有待执行命令；如果没有这一行，UI 线程不会更新窗口状态。
            root.after(40, poll_commands)  # 新增代码+ComputerUseCursorOverlay：持续轮询队列；如果没有这一行，只有第一次命令会被处理。
        # 新增代码+ComputerUseCursorOverlay：内部函数段结束，poll_commands 到此结束；如果没有这个边界说明，初学者不容易看出队列轮询范围。

        root.after(40, poll_commands)  # 新增代码+ComputerUseCursorOverlay：安排首次队列轮询；如果没有这一行，命令消费循环不会启动。
        root.mainloop()  # 新增代码+ComputerUseCursorOverlay：进入 Tk 事件循环；如果没有这一行，窗口创建后会立刻退出。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，_TkCursorOverlayWindow._run_ui_loop 到此结束；如果没有这个边界说明，初学者不容易看出 UI 线程范围。

    def _drain_commands(self, root: Any, window: Any) -> None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，消费所有已排队 UI 命令；如果没有这段函数，跨线程 show/hide 无法落到 Tk 窗口。
        while True:  # 新增代码+ComputerUseCursorOverlay：持续取命令直到队列为空；如果没有这一行，快速连续动作可能只处理一个命令。
            try:  # 新增代码+ComputerUseCursorOverlay：保护非阻塞取队列；如果没有这一行，空队列会抛错打断 UI 轮询。
                command = self._commands.get_nowait()  # 新增代码+ComputerUseCursorOverlay：取出一个待处理命令；如果没有这一行，UI 线程拿不到输入线程发来的指令。
            except queue.Empty:  # 新增代码+ComputerUseCursorOverlay：识别队列已经为空；如果没有这一行，空队列会被当成异常。
                return  # 新增代码+ComputerUseCursorOverlay：没有命令时结束本轮处理；如果没有这一行，循环会无法退出。
            self._handle_command(root, window, command)  # 新增代码+ComputerUseCursorOverlay：执行取到的命令；如果没有这一行，命令只会被丢弃。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，_TkCursorOverlayWindow._drain_commands 到此结束；如果没有这个边界说明，初学者不容易看出命令消费范围。

    def _handle_command(self, root: Any, window: Any, command: dict[str, Any]) -> None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，把单条命令应用到窗口；如果没有这段函数，显示和隐藏逻辑会混在队列循环里。
        kind = str(command.get("kind", ""))  # 新增代码+ComputerUseCursorOverlay：读取命令类型；如果没有这一行，无法区分 show、hide 和 hide_later。
        if kind == "show":  # 新增代码+ComputerUseCursorOverlay：处理显示命令；如果没有这一行，鼠标动作不会弹出橙色标识。
            x = int(command.get("x", 0))  # 新增代码+ComputerUseCursorOverlay：读取横坐标；如果没有这一行，窗口无法贴近真实鼠标位置。
            y = int(command.get("y", 0))  # 新增代码+ComputerUseCursorOverlay：读取纵坐标；如果没有这一行，窗口无法贴近真实鼠标位置。
            left = max(0, x - int(self.size * 0.18))  # 新增代码+ComputerUseCursorOverlay：计算窗口左上角并避免负坐标；如果没有这一行，靠近屏幕边缘时窗口可能跑到屏幕外。
            top = max(0, y - int(self.size * 0.18))  # 新增代码+ComputerUseCursorOverlay：计算窗口顶部位置并避免负坐标；如果没有这一行，屏幕上边缘动作可能看不到标识。
            window.geometry(f"{self.size}x{self.size}+{left}+{top}")  # 新增代码+ComputerUseCursorOverlay：移动窗口到鼠标附近；如果没有这一行，标识会停留在旧位置。
            window.deiconify()  # 新增代码+ComputerUseCursorOverlay：显示窗口；如果没有这一行，移动位置后仍然不可见。
            window.lift()  # 新增代码+ComputerUseCursorOverlay：把窗口抬到最上层；如果没有这一行，目标应用可能遮住标识。
            return  # 新增代码+ComputerUseCursorOverlay：显示命令处理完成后退出；如果没有这一行，后续隐藏分支也会被继续检查。
        if kind == "hide":  # 新增代码+ComputerUseCursorOverlay：处理立即隐藏命令；如果没有这一行，标识无法被主动收起。
            window.withdraw()  # 新增代码+ComputerUseCursorOverlay：隐藏顶层窗口；如果没有这一行，橙色标识会残留在桌面。
            return  # 新增代码+ComputerUseCursorOverlay：隐藏命令处理完成后退出；如果没有这一行，函数会继续处理不相关分支。
        if kind == "hide_later":  # 新增代码+ComputerUseCursorOverlay：处理延迟隐藏命令；如果没有这一行，用户可能来不及看到标识或标识无法自动消失。
            delay_ms = max(50, int(float(command.get("delay_seconds", 0.55)) * 1000))  # 新增代码+ComputerUseCursorOverlay：把秒转成 Tk 需要的毫秒并设最小值；如果没有这一行，延迟可能为零导致标识一闪而过。
            root.after(delay_ms, window.withdraw)  # 新增代码+ComputerUseCursorOverlay：安排稍后隐藏窗口；如果没有这一行，标识不会自动清理。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，_TkCursorOverlayWindow._handle_command 到此结束；如果没有这个边界说明，初学者不容易看出单命令处理范围。

    def _draw_overlay(self, canvas: Any) -> None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，绘制接近附件风格的橙色鼠标标识；如果没有这段函数，叠加层没有用户能识别的图案。
        center = self.size * 0.38  # 新增代码+ComputerUseCursorOverlay：设置放射线中心位置；如果没有这一行，光芒和指针会难以对齐。
        for index in range(28):  # 新增代码+ComputerUseCursorOverlay：绘制一圈橙色放射线；如果没有这一行，标识不够醒目。
            angle = math.tau * index / 28.0  # 新增代码+ComputerUseCursorOverlay：计算当前放射线角度；如果没有这一行，每条线都会重叠。
            inner = self.size * 0.19  # 新增代码+ComputerUseCursorOverlay：设置放射线内半径；如果没有这一行，线条会穿过指针中心显得凌乱。
            outer = self.size * 0.36  # 新增代码+ComputerUseCursorOverlay：设置放射线外半径；如果没有这一行，光芒长度不稳定。
            x1 = center + math.cos(angle) * inner  # 新增代码+ComputerUseCursorOverlay：计算线条起点横坐标；如果没有这一行，无法画出环形光芒。
            y1 = center + math.sin(angle) * inner  # 新增代码+ComputerUseCursorOverlay：计算线条起点纵坐标；如果没有这一行，无法画出环形光芒。
            x2 = center + math.cos(angle) * outer  # 新增代码+ComputerUseCursorOverlay：计算线条终点横坐标；如果没有这一行，光芒无法向外扩散。
            y2 = center + math.sin(angle) * outer  # 新增代码+ComputerUseCursorOverlay：计算线条终点纵坐标；如果没有这一行，光芒无法向外扩散。
            canvas.create_line(x1, y1, x2, y2, fill="#ff9a00", width=3, capstyle="round")  # 新增代码+ComputerUseCursorOverlay：画出一条橙色光芒线；如果没有这一行，视觉提示会不明显。
        for index in range(20):  # 新增代码+ComputerUseCursorOverlay：绘制外围小点增加辨识度；如果没有这一行，图案和普通鼠标指针区分度较低。
            angle = math.tau * index / 20.0  # 新增代码+ComputerUseCursorOverlay：计算小点角度；如果没有这一行，小点无法围成一圈。
            dot_x = center + math.cos(angle) * self.size * 0.43  # 新增代码+ComputerUseCursorOverlay：计算小点横坐标；如果没有这一行，小点位置不正确。
            dot_y = center + math.sin(angle) * self.size * 0.43  # 新增代码+ComputerUseCursorOverlay：计算小点纵坐标；如果没有这一行，小点位置不正确。
            canvas.create_oval(dot_x - 2, dot_y - 2, dot_x + 2, dot_y + 2, fill="#ff9a00", outline="#ff9a00")  # 新增代码+ComputerUseCursorOverlay：画出橙色小点；如果没有这一行，附件风格的放射点会缺失。
        canvas.create_polygon(self.size * 0.25, self.size * 0.16, self.size * 0.82, self.size * 0.63, self.size * 0.55, self.size * 0.67, self.size * 0.46, self.size * 0.95, fill="#ff8500", outline="#ff5a00", width=2)  # 新增代码+ComputerUseCursorOverlay：绘制橙色指针主体；如果没有这一行，用户看不到“鼠标被控制”的核心视觉符号。
        canvas.create_polygon(self.size * 0.31, self.size * 0.24, self.size * 0.72, self.size * 0.58, self.size * 0.48, self.size * 0.60, fill="#ffb000", outline="")  # 新增代码+ComputerUseCursorOverlay：绘制指针高光面；如果没有这一行，标识会显得扁平不够醒目。
        canvas.create_polygon(self.size * 0.55, self.size * 0.67, self.size * 0.73, self.size * 0.92, self.size * 0.61, self.size * 0.96, self.size * 0.46, self.size * 0.73, fill="#ff5a00", outline="#ff5a00")  # 新增代码+ComputerUseCursorOverlay：绘制指针尾部阴影；如果没有这一行，图案不像附件里的立体橙色光标。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，_TkCursorOverlayWindow._draw_overlay 到此结束；如果没有这个边界说明，初学者不容易看出绘制范围。

    def _make_click_through(self, window: Any) -> None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，把叠加层设置为不抢焦点、不挡点击；如果没有这段函数，标识可能干扰 Computer Use 自己的鼠标动作。
        if sys.platform != "win32":  # 新增代码+ComputerUseCursorOverlay：只在 Windows 调用 Win32 扩展样式；如果没有这一行，其他平台会访问不存在的 ctypes 窗口常量。
            return  # 新增代码+ComputerUseCursorOverlay：非 Windows 不处理点击穿透；如果没有这一行，后续 Win32 调用会失败。
        try:  # 新增代码+ComputerUseCursorOverlay：保护 Win32 样式设置；如果没有这一行，个别系统调用失败会中断叠加层。
            import ctypes  # 新增代码+ComputerUseCursorOverlay：导入 Win32 API 访问工具；如果没有这一行，无法设置点击穿透样式。
            window.update_idletasks()  # 新增代码+ComputerUseCursorOverlay：确保窗口句柄已经创建；如果没有这一行，winfo_id 可能返回未准备好的句柄。
            hwnd = int(window.winfo_id())  # 新增代码+ComputerUseCursorOverlay：读取 Tk 窗口句柄；如果没有这一行，Win32 API 不知道要修改哪个窗口。
            gwl_exstyle = -20  # 新增代码+ComputerUseCursorOverlay：定义扩展样式索引；如果没有这一行，GetWindowLongW 无法读取正确样式。
            ws_ex_layered = 0x00080000  # 新增代码+ComputerUseCursorOverlay：定义分层窗口样式；如果没有这一行，透明顶层窗口行为可能不稳定。
            ws_ex_transparent = 0x00000020  # 新增代码+ComputerUseCursorOverlay：定义鼠标点击穿透样式；如果没有这一行，叠加层可能挡住目标控件。
            ws_ex_toolwindow = 0x00000080  # 新增代码+ComputerUseCursorOverlay：定义工具窗口样式；如果没有这一行，叠加层可能出现在任务栏或 Alt-Tab。
            ws_ex_noactivate = 0x08000000  # 新增代码+ComputerUseCursorOverlay：定义不激活窗口样式；如果没有这一行，显示标识可能抢走目标应用焦点。
            user32 = ctypes.windll.user32  # 新增代码+ComputerUseCursorOverlay：取得 user32 API；如果没有这一行，无法读取或写入窗口扩展样式。
            old_style = user32.GetWindowLongW(hwnd, gwl_exstyle)  # 新增代码+ComputerUseCursorOverlay：读取原有扩展样式；如果没有这一行，新样式会覆盖系统已有窗口属性。
            new_style = old_style | ws_ex_layered | ws_ex_transparent | ws_ex_toolwindow | ws_ex_noactivate  # 新增代码+ComputerUseCursorOverlay：合并点击穿透和不抢焦点样式；如果没有这一行，用户会看到但 Computer Use 点击可能被挡住。
            user32.SetWindowLongW(hwnd, gwl_exstyle, new_style)  # 新增代码+ComputerUseCursorOverlay：写回新的窗口扩展样式；如果没有这一行，点击穿透不会真正生效。
        except Exception as error:  # 新增代码+ComputerUseCursorOverlay：捕获样式设置失败；如果没有这一行，低权限或特殊桌面环境会让 UI 线程崩溃。
            self._last_error = f"click_through_unavailable:{error}"  # 新增代码+ComputerUseCursorOverlay：记录点击穿透失败原因；如果没有这一行，用户无法判断叠加层是否可能挡点击。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，_TkCursorOverlayWindow._make_click_through 到此结束；如果没有这个边界说明，初学者不容易看出 Win32 样式范围。
# 新增代码+ComputerUseCursorOverlay：类段结束，_TkCursorOverlayWindow 到此结束；如果没有这个边界说明，初学者不容易看出真实 UI 实现范围。


class ComputerUseCursorOverlayController:  # 新增代码+ComputerUseCursorOverlay：类段开始，对外提供安全的叠加层控制接口；如果没有这段类，底层 sender 会直接依赖 Tk 细节。
    def __init__(self, platform: str | None = None, environ: dict[str, str] | None = None, ui: Any | None = None, hold_seconds: float = 0.55) -> None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，初始化叠加层控制器；如果没有这段函数，包装器无法注入测试 UI 或读取开关。
        self.platform = _normalise_platform(platform)  # 新增代码+ComputerUseCursorOverlay：保存平台信息；如果没有这一行，status 无法说明为什么启用或关闭。
        self.enabled = cursor_overlay_enabled(self.platform, environ)  # 新增代码+ComputerUseCursorOverlay：按平台和环境变量判断是否启用；如果没有这一行，叠加层会无条件尝试显示。
        self.hold_seconds = max(0.05, float(hold_seconds))  # 新增代码+ComputerUseCursorOverlay：限制最短停留时间；如果没有这一行，用户可能完全看不到一闪而过的标识。
        self.ui = ui if ui is not None else (_TkCursorOverlayWindow() if self.enabled else None)  # 新增代码+ComputerUseCursorOverlay：真实启用时懒创建 UI，测试时允许注入假 UI；如果没有这一行，单元测试会打开真实窗口。
        self.state = ComputerUseCursorOverlayState(enabled=self.enabled)  # 新增代码+ComputerUseCursorOverlay：初始化可查询状态；如果没有这一行，sender 返回值没有稳定状态来源。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，ComputerUseCursorOverlayController.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出控制器初始化范围。

    def should_show_for_events(self, events: list[dict[str, Any]]) -> bool:  # 新增代码+ComputerUseCursorOverlay：函数段开始，判断本批低层事件是否应该显示标识；如果没有这段函数，包装器会把键盘事件也交给 UI。
        return self.enabled and extract_cursor_overlay_point(events) is not None  # 新增代码+ComputerUseCursorOverlay：只有启用且存在鼠标坐标才显示；如果没有这一行，标识会在不相关动作中误出现。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，ComputerUseCursorOverlayController.should_show_for_events 到此结束；如果没有这个边界说明，初学者不容易看出显示判定范围。

    def show_for_events(self, events: list[dict[str, Any]], label: str = "Computer Use") -> bool:  # 新增代码+ComputerUseCursorOverlay：函数段开始，根据低层事件显示橙色标识；如果没有这段函数，sender 需要自己解析坐标和处理 UI 错误。
        point = extract_cursor_overlay_point(events)  # 新增代码+ComputerUseCursorOverlay：从事件中找最后一个鼠标坐标；如果没有这一行，标识不知道显示位置。
        if not self.enabled or point is None or self.ui is None:  # 新增代码+ComputerUseCursorOverlay：检查开关、坐标和 UI 是否可用；如果没有这一行，关闭状态或无坐标也会触发显示错误。
            self.state.visible_requested = False  # 新增代码+ComputerUseCursorOverlay：记录本次没有请求显示；如果没有这一行，status 可能误以为最近显示过标识。
            return False  # 新增代码+ComputerUseCursorOverlay：告诉包装器本次未显示；如果没有这一行，包装器无法正确写回执行结果。
        x, y = point  # 新增代码+ComputerUseCursorOverlay：拆分坐标；如果没有这一行，后续 show 调用无法传入清晰参数。
        self.state.visible_requested = True  # 新增代码+ComputerUseCursorOverlay：记录已请求显示；如果没有这一行，执行结果缺少“确实触发可视标识”的证据。
        self.state.last_point = {"x": x, "y": y}  # 新增代码+ComputerUseCursorOverlay：保存最近坐标；如果没有这一行，调试时无法确认标识位置。
        try:  # 新增代码+ComputerUseCursorOverlay：保护 UI 显示调用；如果没有这一行，叠加层失败会影响真实鼠标动作。
            self.ui.show(x, y, label)  # 新增代码+ComputerUseCursorOverlay：向 UI 层发出显示请求；如果没有这一行，用户看不到橙色来源标识。
            return True  # 新增代码+ComputerUseCursorOverlay：告诉调用方显示请求已发出；如果没有这一行，执行结果无法标记可视提示已触发。
        except Exception as error:  # 新增代码+ComputerUseCursorOverlay：捕获 UI 显示失败；如果没有这一行，小窗口异常会让真实动作失败。
            self.state.last_error = f"show_failed:{error}"  # 新增代码+ComputerUseCursorOverlay：记录显示失败原因；如果没有这一行，用户只会看到标识缺失但没有解释。
            return False  # 新增代码+ComputerUseCursorOverlay：显示失败时保持动作链路继续；如果没有这一行，显示功能会变成鼠标执行的硬依赖。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，ComputerUseCursorOverlayController.show_for_events 到此结束；如果没有这个边界说明，初学者不容易看出显示流程范围。

    def hide_later(self) -> bool:  # 新增代码+ComputerUseCursorOverlay：函数段开始，请求叠加层短暂停留后自动隐藏；如果没有这段函数，标识可能残留或一闪而过。
        if not self.enabled or self.ui is None:  # 新增代码+ComputerUseCursorOverlay：检查 UI 是否可用；如果没有这一行，关闭状态也会尝试发隐藏命令。
            return False  # 新增代码+ComputerUseCursorOverlay：关闭状态无需隐藏；如果没有这一行，调用方无法知道本次没有实际 UI 操作。
        try:  # 新增代码+ComputerUseCursorOverlay：保护延迟隐藏调用；如果没有这一行，UI 异常会影响真实动作返回。
            self.ui.hide_later(self.hold_seconds)  # 新增代码+ComputerUseCursorOverlay：请求 UI 在短暂停留后隐藏；如果没有这一行，用户看不到足够长的来源标识。
            return True  # 新增代码+ComputerUseCursorOverlay：告诉调用方隐藏命令已发送；如果没有这一行，结果无法反映清理状态。
        except Exception as error:  # 新增代码+ComputerUseCursorOverlay：捕获隐藏失败；如果没有这一行，隐藏异常会破坏真实动作结果。
            self.state.last_error = f"hide_later_failed:{error}"  # 新增代码+ComputerUseCursorOverlay：记录隐藏失败原因；如果没有这一行，残留窗口难以排查。
            return False  # 新增代码+ComputerUseCursorOverlay：隐藏失败不影响动作完成；如果没有这一行，辅助 UI 会变成核心动作风险。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，ComputerUseCursorOverlayController.hide_later 到此结束；如果没有这个边界说明，初学者不容易看出延迟隐藏流程范围。

    def hide(self) -> bool:  # 新增代码+ComputerUseCursorOverlay：函数段开始，立即隐藏叠加层；如果没有这段函数，调试或清理时无法主动收起标识。
        if not self.enabled or self.ui is None:  # 新增代码+ComputerUseCursorOverlay：检查 UI 是否可用；如果没有这一行，关闭状态也会误调用隐藏。
            return False  # 新增代码+ComputerUseCursorOverlay：无 UI 时直接返回；如果没有这一行，调用方无法知道没有执行隐藏。
        try:  # 新增代码+ComputerUseCursorOverlay：保护立即隐藏调用；如果没有这一行，UI 异常会影响控制器状态。
            self.ui.hide()  # 新增代码+ComputerUseCursorOverlay：向 UI 层发送隐藏命令；如果没有这一行，标识无法被立刻收起。
            self.state.visible_requested = False  # 新增代码+ComputerUseCursorOverlay：更新最近显示状态；如果没有这一行，status 会继续显示最近请求过显示。
            return True  # 新增代码+ComputerUseCursorOverlay：告诉调用方隐藏成功发出；如果没有这一行，结果无法表达清理动作。
        except Exception as error:  # 新增代码+ComputerUseCursorOverlay：捕获立即隐藏失败；如果没有这一行，UI 异常会穿透到业务层。
            self.state.last_error = f"hide_failed:{error}"  # 新增代码+ComputerUseCursorOverlay：记录隐藏失败原因；如果没有这一行，无法解释残留标识。
            return False  # 新增代码+ComputerUseCursorOverlay：隐藏失败不阻塞主流程；如果没有这一行，辅助功能会影响核心工具。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，ComputerUseCursorOverlayController.hide 到此结束；如果没有这个边界说明，初学者不容易看出立即隐藏流程范围。

    def status(self) -> dict[str, Any]:  # 新增代码+ComputerUseCursorOverlay：函数段开始，返回叠加层控制器状态；如果没有这段函数，执行结果无法解释可视标识状态。
        ui_status = self.ui.status() if self.ui is not None and hasattr(self.ui, "status") else {"ui": "disabled"}  # 新增代码+ComputerUseCursorOverlay：读取 UI 层状态或说明关闭；如果没有这一行，status 会缺少底层窗口信息。
        return {"marker": COMPUTER_USE_CURSOR_OVERLAY_MARKER, "enabled": self.enabled, "visible_requested": self.state.visible_requested, "last_point": dict(self.state.last_point), "last_error": self.state.last_error, "ui": ui_status}  # 新增代码+ComputerUseCursorOverlay：返回结构化状态；如果没有这一行，日志和测试无法确认叠加层是否进入动作链路。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，ComputerUseCursorOverlayController.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。
# 新增代码+ComputerUseCursorOverlay：类段结束，ComputerUseCursorOverlayController 到此结束；如果没有这个边界说明，初学者不容易看出安全控制接口范围。


class ComputerUseCursorOverlayLowLevelSender:  # 新增代码+ComputerUseCursorOverlay：类段开始，包装真实低层 sender 并在鼠标动作时显示标识；如果没有这段类，叠加层无法挂到真实 Computer Use 输入链路。
    def __init__(self, wrapped_sender: Any, platform: str | None = None, overlay: ComputerUseCursorOverlayController | None = None) -> None:  # 新增代码+ComputerUseCursorOverlay：函数段开始，初始化低层 sender 包装器；如果没有这段函数，无法保存真实 sender 和叠加层控制器。
        self.wrapped_sender = wrapped_sender  # 新增代码+ComputerUseCursorOverlay：保存真正执行 SendInput 的 sender；如果没有这一行，包装器只能显示标识却不能执行鼠标键盘动作。
        self.platform = _normalise_platform(platform)  # 新增代码+ComputerUseCursorOverlay：保存平台信息；如果没有这一行，控制器无法按平台决定是否启用。
        self.overlay = overlay or ComputerUseCursorOverlayController(platform=self.platform)  # 新增代码+ComputerUseCursorOverlay：创建或注入叠加层控制器；如果没有这一行，鼠标动作没有可视来源提示。
        self.requires_raw_text = bool(getattr(wrapped_sender, "requires_raw_text", False))  # 新增代码+ComputerUseCursorOverlay：透传底层 sender 对原始文本的能力声明；如果没有这一行，调度层可能误判文本输入路径。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，ComputerUseCursorOverlayLowLevelSender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出包装器初始化范围。

    def send_low_level(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+ComputerUseCursorOverlay：函数段开始，显示来源标识后转发低层事件；如果没有这段函数，Computer Use 鼠标动作不会出现肉眼可见的来源提示。
        safe_events = [dict(event) for event in events]  # 新增代码+ComputerUseCursorOverlay：复制事件列表避免显示逻辑改动原始事件；如果没有这一行，包装器可能污染真实发送器收到的数据。
        overlay_requested = False  # 新增代码+ComputerUseCursorOverlay：记录本次是否请求显示标识；如果没有这一行，返回结果无法说明标识是否参与。
        if self.overlay.should_show_for_events(safe_events):  # 新增代码+ComputerUseCursorOverlay：只有真实鼠标坐标事件才触发标识；如果没有这一行，键盘动作也会误显示鼠标来源。
            overlay_requested = self.overlay.show_for_events(safe_events, label="Computer Use")  # 新增代码+ComputerUseCursorOverlay：在执行真实低层事件前显示橙色标识；如果没有这一行，用户无法提前看到 Computer Use 正在接管鼠标。
        try:  # 新增代码+ComputerUseCursorOverlay：确保无论真实 sender 成功或失败都能安排隐藏；如果没有这一行，失败动作可能留下标识。
            sender_result = self.wrapped_sender.send_low_level(safe_events)  # 新增代码+ComputerUseCursorOverlay：把低层事件交给真实 sender；如果没有这一行，Computer Use 只显示图标但不会真正点击或输入。
        finally:  # 新增代码+ComputerUseCursorOverlay：真实动作返回或抛错后都执行清理；如果没有这一行，异常场景下标识容易残留。
            if overlay_requested:  # 新增代码+ComputerUseCursorOverlay：只在确实显示过标识时安排隐藏；如果没有这一行，无 UI 动作也会产生多余隐藏命令。
                self.overlay.hide_later()  # 新增代码+ComputerUseCursorOverlay：让标识短暂停留后隐藏；如果没有这一行，用户可能看不清或者标识一直不消失。
        result = dict(sender_result) if isinstance(sender_result, dict) else {"ok": bool(sender_result), "sender_result": sender_result}  # 新增代码+ComputerUseCursorOverlay：规范化底层 sender 返回值；如果没有这一行，包装器无法追加标识字段。
        result["computer_use_cursor_overlay_marker"] = COMPUTER_USE_CURSOR_OVERLAY_MARKER  # 新增代码+ComputerUseCursorOverlay：写入包装器标记；如果没有这一行，日志里无法判断是否经过可视来源层。
        result["computer_use_cursor_overlay_requested"] = overlay_requested  # 新增代码+ComputerUseCursorOverlay：记录本次是否请求显示；如果没有这一行，测试和调试无法区分鼠标动作与键盘动作。
        result["computer_use_cursor_overlay_status"] = self.overlay.status()  # 新增代码+ComputerUseCursorOverlay：附带控制器状态；如果没有这一行，用户看不到启用、坐标和 UI 错误信息。
        return result  # 新增代码+ComputerUseCursorOverlay：返回增强后的真实 sender 结果；如果没有这一行，dispatcher 拿不到执行结果。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，ComputerUseCursorOverlayLowLevelSender.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出真实转发范围。

    def __getattr__(self, name: str) -> Any:  # 新增代码+ComputerUseCursorOverlay：函数段开始，向真实 sender 透传未知属性；如果没有这段函数，旧代码读取底层 sender 属性时可能失败。
        return getattr(self.wrapped_sender, name)  # 新增代码+ComputerUseCursorOverlay：把未知属性交给被包装 sender；如果没有这一行，包装层会破坏原 sender 的兼容性。
    # 新增代码+ComputerUseCursorOverlay：函数段结束，ComputerUseCursorOverlayLowLevelSender.__getattr__ 到此结束；如果没有这个边界说明，初学者不容易看出兼容透传范围。
# 新增代码+ComputerUseCursorOverlay：类段结束，ComputerUseCursorOverlayLowLevelSender 到此结束；如果没有这个边界说明，初学者不容易看出低层包装器范围。


__all__ = [  # 新增代码+ComputerUseCursorOverlay：声明模块公开接口；如果没有这一行，其他模块和学习副本不容易确认哪些名字可以复用。
    "COMPUTER_USE_CURSOR_OVERLAY_ENV_VAR",  # 新增代码+ComputerUseCursorOverlay：公开环境变量名；如果没有这一行，测试和文档需要硬编码字符串。
    "COMPUTER_USE_CURSOR_OVERLAY_MARKER",  # 新增代码+ComputerUseCursorOverlay：公开追踪标记；如果没有这一行，测试无法稳定断言执行结果。
    "ComputerUseCursorOverlayController",  # 新增代码+ComputerUseCursorOverlay：公开控制器；如果没有这一行，调试工具无法直接查询或注入 UI。
    "ComputerUseCursorOverlayLowLevelSender",  # 新增代码+ComputerUseCursorOverlay：公开低层 sender 包装器；如果没有这一行，controller 无法清晰导入包装器。
    "cursor_overlay_enabled",  # 新增代码+ComputerUseCursorOverlay：公开开关判断函数；如果没有这一行，测试无法验证环境变量行为。
    "extract_cursor_overlay_point",  # 新增代码+ComputerUseCursorOverlay：公开坐标提取函数；如果没有这一行，单元测试无法独立验证事件解析。
]  # 新增代码+ComputerUseCursorOverlay：公开接口列表结束；如果没有这一行，模块语法不完整。
