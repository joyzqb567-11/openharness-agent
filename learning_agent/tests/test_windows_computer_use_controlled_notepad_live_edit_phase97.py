import json  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 json 用来把报告序列化后检查是否泄露原始 prompt；如果没有这一行，嵌套字段里的敏感文本可能漏检。
import tempfile  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 tempfile 用来给每个测试创建隔离目录；如果没有这一行，测试产物可能污染真实项目目录。
import unittest  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 unittest 沿用项目现有测试框架；如果没有这一行，python -m unittest 无法发现和执行这些用例。
from pathlib import Path  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 Path 统一处理 Windows 路径；如果没有这一行，路径边界检查会变成脆弱字符串拼接。

from learning_agent.computer_use.controlled_notepad_live_edit import (  # 新增代码+Phase97ControlledNotepadLiveEdit：从公开模块导入 Phase97 合同和 driver；如果没有这一段，测试可能绕过用户真正会调用的入口。
    PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_MARKER,  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 ready marker；如果没有这一行，终端验收 token 漂移不会被测试发现。
    PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK_TOKEN,  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 OK token；如果没有这一行，成功输出标识可能没有回归保护。
    PHASE97_REAL_NOTEPAD_LIVE_EDIT_ENV,  # 新增代码+Phase97ControlledNotepadLiveEdit：导入真实 Notepad 启用环境门；如果没有这一行，生产启用方式无法被审计。
    PHASE97_REAL_NOTEPAD_LIVE_EDIT_REQUEST_ENV,  # 新增代码+Phase97ControlledNotepadLiveEdit：导入真实 Notepad 请求环境门；如果没有这一行，显式请求方式无法被审计。
    Phase97WindowsNotepadLiveEditDriver,  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 Task3 要实现的可注入真实 driver；如果没有这一行，driver 安全边界不会被测试锁定。
    phase97_cli_line,  # 新增代码+Phase97ControlledNotepadLiveEdit：导入 CLI 单行格式化函数；如果没有这一行，真实终端输出格式没有回归保护。
    run_phase97_controlled_notepad_live_edit_contract,  # 新增代码+Phase97ControlledNotepadLiveEdit：导入总合同入口；如果没有这一行，测试和验收没有统一事实来源。
)  # 新增代码+Phase97ControlledNotepadLiveEdit：结束公开 API 导入列表；如果没有这一行，Python 语法不完整。
from learning_agent.computer_use.real_sendinput_guard import WindowsSendInputLowLevelSender  # 修改代码+Phase97ControlledNotepadLiveEdit：导入真实低层 sender 以验证 Ctrl+S 事件已被后端支持；如果没有这一行，key_down/key_up 可能只在 fake sender 里通过。

PHASE97_SECRET_PROMPT = "user secret prompt phase97"  # 新增代码+Phase97ControlledNotepadLiveEdit：定义敏感 prompt 样本；如果没有这一行，脱敏测试只是在检查从未输入过的文字。


def path_is_under(child: Path, parent: Path) -> bool:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，判断子路径是否留在父目录中；如果没有这段函数，target_file 可能逃出临时目录而不被发现。
    try:  # 新增代码+Phase97ControlledNotepadLiveEdit：尝试用 relative_to 做严格路径归属判断；如果没有这一行，跨盘符或转义路径会导致测试崩溃而不是返回 False。
        child.resolve().relative_to(parent.resolve())  # 新增代码+Phase97ControlledNotepadLiveEdit：确认 child 的真实路径位于 parent 下；如果没有这一行，目录逃逸风险没有事实检查。
        return True  # 新增代码+Phase97ControlledNotepadLiveEdit：路径归属成功时返回 True；如果没有这一行，合法路径也会被误判失败。
    except ValueError:  # 新增代码+Phase97ControlledNotepadLiveEdit：捕获不在父目录下的路径情况；如果没有这一行，失败路径会抛异常而不是给断言使用。
        return False  # 新增代码+Phase97ControlledNotepadLiveEdit：路径不在父目录下时返回 False；如果没有这一行，目录逃逸不能被清楚断言。


class FakePhase97NotepadDriver:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，模拟可控 Notepad 驱动且不碰真实桌面；如果没有这个类，合同单测可能误触真实 Notepad。
    def __init__(self) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，初始化 fake 调用记录；如果没有这段函数，测试无法证明默认关闭时 driver 没被调用。
        self.calls = []  # 新增代码+Phase97ControlledNotepadLiveEdit：保存每次 run 调用摘要；如果没有这一行，测试无法审计 real path 是否走到 fake driver。
        self.received_expected_text = ""  # 新增代码+Phase97ControlledNotepadLiveEdit：保存受控 expected_text 以便确认没有收到 raw prompt；如果没有这一行，隐私链路没有 driver 侧证据。

    def run(self, *, run_root: Path, expected_text: str, target_file: Path) -> dict[str, object]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，模拟 Notepad 保存受控文件；如果没有这段函数，显式门控测试无法验证保存和复查字段。
        self.received_expected_text = expected_text  # 新增代码+Phase97ControlledNotepadLiveEdit：记录 driver 收到的受控文本；如果没有这一行，无法证明输入不是用户 raw prompt。
        self.calls.append({"run_root": str(run_root), "target_file": str(target_file), "text_length": len(expected_text)})  # 新增代码+Phase97ControlledNotepadLiveEdit：只记录路径和长度不记录正文；如果没有这一行，既无法审计调用也可能泄露文本。
        target_file.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase97ControlledNotepadLiveEdit：确保目标文件目录存在；如果没有这一行，写文件会因为目录缺失失败。
        target_file.write_text(expected_text, encoding="utf-8")  # 新增代码+Phase97ControlledNotepadLiveEdit：模拟 Notepad 把受控文字保存到文件；如果没有这一行，saved_file 验证没有磁盘事实。
        return {  # 新增代码+Phase97ControlledNotepadLiveEdit：返回 fake driver 脱敏报告；如果没有这一行，合同无法合并真实路径证据。
            "ok": True,  # 新增代码+Phase97ControlledNotepadLiveEdit：声明 fake driver 执行成功；如果没有这一行，合同无法判断显式路径通过。
            "driver": "fake_phase97_notepad_driver",  # 新增代码+Phase97ControlledNotepadLiveEdit：标记报告来自 fake driver；如果没有这一行，排查时无法区分真实驱动和测试替身。
            "notepad_process_verified": True,  # 新增代码+Phase97ControlledNotepadLiveEdit：模拟已确认目标进程是 Notepad；如果没有这一行，进程身份保护没有测试字段。
            "target_rechecked_before_input": True,  # 新增代码+Phase97ControlledNotepadLiveEdit：模拟输入前复查通过；如果没有这一行，窗口切换风险没有回归字段。
            "target_rechecked_before_save": True,  # 新增代码+Phase97ControlledNotepadLiveEdit：模拟保存前复查通过；如果没有这一行，保存快捷键风险没有回归字段。
            "saved_file_exists": target_file.exists(),  # 新增代码+Phase97ControlledNotepadLiveEdit：用真实文件存在性填报告；如果没有这一行，报告可能声称保存但磁盘没有文件。
            "saved_file_sha256_16": "fakehashphase97",  # 新增代码+Phase97ControlledNotepadLiveEdit：提供脱敏短哈希占位；如果没有这一行，报告缺少内容指纹样本。
            "real_desktop_touched": True,  # 新增代码+Phase97ControlledNotepadLiveEdit：显式路径应标记触达桌面；如果没有这一行，真实副作用审计可能被误报为安全默认。
            "raw_text_included": False,  # 新增代码+Phase97ControlledNotepadLiveEdit：声明报告不包含原始文本；如果没有这一行，隐私门禁没有 driver 侧证据。
        }  # 新增代码+Phase97ControlledNotepadLiveEdit：结束 fake driver 报告字典；如果没有这一行，Python 语法不完整。


class FailingTouchingPhase97NotepadDriver:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，模拟触达桌面后失败；如果没有这个类，失败副作用保留逻辑没有主体。
    def __init__(self) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，初始化失败 driver 调用记录；如果没有这段函数，测试无法确认失败 driver 被调用。
        self.calls = []  # 新增代码+Phase97ControlledNotepadLiveEdit：保存失败 driver 调用摘要；如果没有这一行，失败路径审计没有事实来源。

    def run(self, *, run_root: Path, expected_text: str, target_file: Path) -> dict[str, object]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，模拟半执行失败；如果没有这段函数，合同无法覆盖真实桌面已触达但保存失败的情况。
        self.calls.append({"run_root": str(run_root), "target_file": str(target_file), "text_length": len(expected_text)})  # 新增代码+Phase97ControlledNotepadLiveEdit：记录调用但不写 expected_text 明文；如果没有这一行，既无法审计调用也可能泄露受控文本。
        return {  # 新增代码+Phase97ControlledNotepadLiveEdit：返回失败且触桌面的脱敏报告；如果没有这一行，合同没有半执行失败样本。
            "ok": False,  # 新增代码+Phase97ControlledNotepadLiveEdit：声明 driver 失败；如果没有这一行，合同会把失败场景误当成功。
            "driver": "failing_touching_phase97_notepad_driver",  # 新增代码+Phase97ControlledNotepadLiveEdit：标记失败 driver 身份；如果没有这一行，排查时无法区分成功 fake 与失败 fake。
            "reason": "simulated_partial_desktop_touch_without_save",  # 新增代码+Phase97ControlledNotepadLiveEdit：说明失败原因；如果没有这一行，失败报告不可读。
            "notepad_process_verified": True,  # 新增代码+Phase97ControlledNotepadLiveEdit：模拟进程验证曾通过；如果没有这一行，测试无法覆盖保存失败而不是目标验证失败。
            "target_rechecked_before_input": True,  # 新增代码+Phase97ControlledNotepadLiveEdit：模拟输入前复查已发生；如果没有这一行，失败原因会和安全复查混在一起。
            "target_rechecked_before_save": False,  # 新增代码+Phase97ControlledNotepadLiveEdit：模拟保存前未完成复查；如果没有这一行，passed 条件不够明确地失败。
            "saved_file_exists": False,  # 新增代码+Phase97ControlledNotepadLiveEdit：声明没有保存文件；如果没有这一行，保存失败样本缺少 driver 侧事实。
            "real_desktop_touched": True,  # 新增代码+Phase97ControlledNotepadLiveEdit：声明已经触碰桌面；如果没有这一行，副作用保留回归没有触发条件。
            "raw_text_included": False,  # 新增代码+Phase97ControlledNotepadLiveEdit：声明失败报告不含原始文本；如果没有这一行，失败原因可能被隐私门禁误伤。
        }  # 新增代码+Phase97ControlledNotepadLiveEdit：结束失败 driver 报告字典；如果没有这一行，Python 语法不完整。


class Phase97DriverFakeLauncher:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，提供不启动真实 Notepad 的 launcher；如果没有这个类，driver 单测可能误触用户桌面。
    def __init__(self, window: dict[str, object]) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，保存测试窗口身份；如果没有这一行，launcher 无法把受控目标交给 driver。
        self.window = dict(window)  # 新增代码+Phase97ControlledNotepadLiveEdit：复制窗口字典避免外部修改污染测试；如果没有这一行，测试输入可能被执行过程意外改写。
        self.cleanup_calls = 0  # 修改代码+Phase97ControlledNotepadLiveEdit：记录 cleanup 调用次数；如果没有这一行，测试无法证明 driver 成功或失败后会收尾 launcher。

    def launch(self, target_file: Path) -> dict[str, object]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，模拟打开受控文件；如果没有这段函数，driver 没有可注入启动入口。
        _ = target_file  # 新增代码+Phase97ControlledNotepadLiveEdit：明确 target_file 只用于启动语义不记录正文；如果没有这一行，静态阅读时看不出参数已被有意处理。
        return dict(self.window)  # 新增代码+Phase97ControlledNotepadLiveEdit：返回窗口身份副本；如果没有这一行，driver 无法继续做目标复核。

    def cleanup(self) -> None:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，模拟 launcher 清理；如果没有这段函数，driver cleanup 行为没有测试替身。
        self.cleanup_calls += 1  # 修改代码+Phase97ControlledNotepadLiveEdit：累计清理次数；如果没有这一行，测试无法判断 finally 是否真的执行。
    # 修改代码+Phase97ControlledNotepadLiveEdit：函数段结束，Phase97DriverFakeLauncher.cleanup 到此结束；如果没有这个边界说明，初学者不容易看出 fake 清理范围。


class Phase97DriverSequenceProbe:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，按顺序返回窗口快照；如果没有这个类，测试无法模拟输入前或保存前目标漂移。
    def __init__(self, windows: list[dict[str, object]]) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，保存每次复核要看到的窗口；如果没有这一行，probe 无法表达多次 recheck。
        self.windows = [dict(window) for window in windows]  # 新增代码+Phase97ControlledNotepadLiveEdit：复制所有窗口快照；如果没有这一行，调用方修改列表会污染复核序列。
        self.calls = 1  # 修改代码+Phase97ControlledNotepadLiveEdit：让 probe 从启动后的下一帧开始复核；如果没有这一行，测试会重复返回 launch 窗口而无法模拟目标漂移。

    def snapshot(self) -> object:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，返回带 windows 字段的简单快照；如果没有这段函数，driver 无法像使用真实 probe 一样读取窗口。
        index = min(self.calls, len(self.windows) - 1)  # 新增代码+Phase97ControlledNotepadLiveEdit：越界时停在最后一个快照；如果没有这一行，多余复核会让测试因索引错误崩溃。
        self.calls += 1  # 新增代码+Phase97ControlledNotepadLiveEdit：累计复核次数；如果没有这一行，测试无法确认 input/save 前都发生了复核。
        return type("Phase97Snapshot", (), {"windows": [dict(self.windows[index])]})()  # 新增代码+Phase97ControlledNotepadLiveEdit：返回最小快照对象；如果没有这一行，driver 找不到 windows 字段。


class Phase97DriverFakeFocuser:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，记录聚焦请求但不切换真实前台窗口；如果没有这个类，单测可能误调用系统焦点 API。
    def focus(self, window: dict[str, object]) -> dict[str, object]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，模拟聚焦成功；如果没有这段函数，driver 无法注入安全 focuser。
        _ = dict(window)  # 新增代码+Phase97ControlledNotepadLiveEdit：复制窗口表达已接收聚焦目标；如果没有这一行，参数使用意图不清晰。
        return {"focused": True}  # 新增代码+Phase97ControlledNotepadLiveEdit：返回聚焦成功；如果没有这一行，driver 会因为无法聚焦而提前失败。


class Phase97DriverFakeSender:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，记录输入事件但不调用 SendInput；如果没有这个类，driver 测试可能误发真实键盘事件。
    def __init__(self) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，准备事件记录容器；如果没有这一行，测试无法检查发送次数和阶段。
        self.events: list[dict[str, object]] = []  # 新增代码+Phase97ControlledNotepadLiveEdit：保存所有低层事件；如果没有这一行，零事件安全断言没有事实来源。

    def send_low_level(self, events: list[dict[str, object]]) -> dict[str, object]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，模拟低层发送；如果没有这段函数，driver 无法注入 sender。
        self.events.extend(dict(event) for event in events)  # 新增代码+Phase97ControlledNotepadLiveEdit：记录事件副本；如果没有这一行，测试无法判断是否发送了输入或保存快捷键。
        return {"ok": True, "low_level_event_count": len(events)}  # 新增代码+Phase97ControlledNotepadLiveEdit：返回发送成功摘要；如果没有这一行，driver 无法继续执行后续验证。


class Phase97InspectableLowLevelSender(WindowsSendInputLowLevelSender):  # 修改代码+Phase97ControlledNotepadLiveEdit：类段开始，测试真实 sender 的分发逻辑但不调用 Win32；如果没有这个类，按键支持只能靠肉眼审查。
    def __init__(self) -> None:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，初始化可观察 sender；如果没有这段函数，测试无法记录实际分发到哪些 helper。
        super().__init__(platform="win32")  # 修改代码+Phase97ControlledNotepadLiveEdit：强制走 Windows 分支但由子类拦截系统调用；如果没有这一行，非 Windows 测试环境会提前拒绝而覆盖不到按键分支。
        self.virtual_keys: list[tuple[str, bool]] = []  # 修改代码+Phase97ControlledNotepadLiveEdit：记录普通虚拟键事件；如果没有这一行，测试无法证明 Ctrl 和 S 真的被 sender 识别。
        self.unicode_texts: list[str] = []  # 修改代码+Phase97ControlledNotepadLiveEdit：记录 Unicode 文本调用；如果没有这一行，测试无法同时确认文本分支仍然可用。
        self.clipboard_texts: list[str] = []  # 修改代码+Phase97ControlledNotepadLiveEdit：记录剪贴板粘贴文本调用；如果没有这一行，测试无法证明 Phase97 完整文本粘贴分支可用。

    def _set_foreground(self, hwnd: int) -> bool:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，拦截聚焦调用；如果没有这段函数，测试会真的调用 SetForegroundWindow。
        return bool(hwnd)  # 修改代码+Phase97ControlledNotepadLiveEdit：有 hwnd 即视为聚焦成功；如果没有这一行，测试无法安全模拟聚焦。

    def _send_unicode_text(self, text: str) -> int:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，拦截 Unicode 输入；如果没有这段函数，测试会真的发送键盘文本。
        self.unicode_texts.append(text)  # 修改代码+Phase97ControlledNotepadLiveEdit：记录文本但不触碰系统；如果没有这一行，测试无法确认文本分支被调用。
        return len(text) * 2  # 修改代码+Phase97ControlledNotepadLiveEdit：模拟每个字符按下和抬起两个事件；如果没有这一行，sender 汇总计数会缺少文本事件。

    def _send_virtual_key(self, key: str, down: bool) -> bool:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，拦截普通按键；如果没有这段函数，测试会真的发送 Ctrl+S。
        self.virtual_keys.append((key, down))  # 修改代码+Phase97ControlledNotepadLiveEdit：记录按键名和方向；如果没有这一行，测试无法断言保存快捷键顺序。
        return True  # 修改代码+Phase97ControlledNotepadLiveEdit：模拟按键发送成功；如果没有这一行，sender 汇总会误以为按键失败。

    def _paste_clipboard_text(self, text: str) -> int:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，拦截剪贴板粘贴；如果没有这段函数，测试会真的改系统剪贴板。
        self.clipboard_texts.append(text)  # 修改代码+Phase97ControlledNotepadLiveEdit：记录粘贴文本但不触碰剪贴板；如果没有这一行，测试无法确认完整文本分支被调用。
        return 1  # 修改代码+Phase97ControlledNotepadLiveEdit：模拟一次粘贴成功；如果没有这一行，sender 汇总会误以为粘贴失败。
    # 修改代码+Phase97ControlledNotepadLiveEdit：类段结束，Phase97InspectableLowLevelSender 到此结束；如果没有这个边界说明，初学者不容易看出这个 sender 只用于安全测试。


class Phase97DriverFakeVerifier:  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，模拟磁盘保存验证；如果没有这个类，driver 单测需要真实 Notepad 写文件。
    def __init__(self) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，准备 verifier 调用记录；如果没有这一行，正向测试无法证明 driver 真走到保存验证阶段。
        self.calls: list[dict[str, object]] = []  # 新增代码+Phase97ControlledNotepadLiveEdit：保存验证调用摘要且不保存正文；如果没有这一行，测试无法审计 verifier 是否被调用。

    def verify(self, target_file: Path, expected_text: str) -> dict[str, object]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，返回脱敏验证结果；如果没有这段函数，driver 无法注入保存验证。
        self.calls.append({"target_file": str(target_file), "text_length": len(expected_text)})  # 新增代码+Phase97ControlledNotepadLiveEdit：记录验证调用但不记录 expected_text 明文；如果没有这一行，正向测试无法证明 verifier 被调用且不泄露正文。
        return {"ok": True, "saved_file_exists": True, "target_file": str(target_file), "text_length": len(expected_text), "target_file_sha256_16": "verifierhashp97"}  # 修改代码+Phase97ControlledNotepadLiveEdit：返回验证摘要且不含正文并带短哈希；如果没有这一行，driver 无法判断保存是否成功或报告缺少文件指纹。


class Phase97ControlledNotepadLiveEditTests(unittest.TestCase):  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，集中验证 Phase97 合同；如果没有这个类，合同回归没有组织入口。
    def test_default_contract_does_not_touch_desktop(self) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，验证默认关闭不触桌面；如果没有这个测试，普通运行可能误开 Notepad。
        driver = FakePhase97NotepadDriver()  # 新增代码+Phase97ControlledNotepadLiveEdit：创建 fake driver 来观察是否被调用；如果没有这一行，无法证明默认关闭没有走真实路径。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase97ControlledNotepadLiveEdit：创建隔离运行目录；如果没有这一行，报告和目标文件可能污染项目目录。
            base_dir = Path(temporary_directory)  # 新增代码+Phase97ControlledNotepadLiveEdit：保存本次合同 base_dir；如果没有这一行，后续无法检查 target_file 边界。
            report = run_phase97_controlled_notepad_live_edit_contract(base_dir=base_dir, real_edit=False, allow_real_gate=False, require_injected_driver=True, raw_prompt_text=PHASE97_SECRET_PROMPT, notepad_driver=driver)  # 新增代码+Phase97ControlledNotepadLiveEdit：运行默认关闭合同；如果没有这一行，后续断言没有事实来源。
            target_file = Path(str(report["target_file"]))  # 新增代码+Phase97ControlledNotepadLiveEdit：读取报告里的目标文件路径；如果没有这一行，默认路径边界无法被断言。
        serialized = json.dumps(report, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase97ControlledNotepadLiveEdit：序列化默认报告扫描敏感信息；如果没有这一行，嵌套泄露可能漏检。
        self.assertTrue(report["passed"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认默认合同整体通过；如果没有这一行，局部字段正确也可能掩盖整体失败。
        self.assertFalse(report["real_notepad_edit_executed"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认未执行真实 Notepad 编辑；如果没有这一行，默认关闭可能回退。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认没有触碰真实桌面；如果没有这一行，安全默认副作用不可见。
        self.assertEqual(driver.calls, [])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认 fake driver 未被调用；如果没有这一行，默认关闭可能只是报告里假装安全。
        self.assertTrue(path_is_under(target_file, base_dir))  # 新增代码+Phase97ControlledNotepadLiveEdit：确认 target_file 留在 base_dir 下；如果没有这一行，默认报告可能指向工作区外文件。
        self.assertTrue(report["default_off_zero_physical_events"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认默认关闭零物理事件；如果没有这一行，键鼠事件可能被误发。
        self.assertTrue(report["unsafe_target_zero_physical_events"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认危险目标零物理事件；如果没有这一行，危险窗口拦截没有保护点。
        self.assertNotIn(PHASE97_SECRET_PROMPT, serialized)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认敏感 prompt 不在默认报告里；如果没有这一行，默认安全路径也可能泄露用户原文。

    def test_explicit_contract_uses_injected_driver_and_sanitizes_report(self) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，验证显式门控只用注入 driver；如果没有这个测试，真实桌面路径可能绕过 fake-only 门。
        driver = FakePhase97NotepadDriver()  # 新增代码+Phase97ControlledNotepadLiveEdit：创建保存型 fake driver；如果没有这一行，显式成功路径没有安全替身。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase97ControlledNotepadLiveEdit：创建隔离运行目录；如果没有这一行，保存文件会污染项目目录。
            report = run_phase97_controlled_notepad_live_edit_contract(base_dir=Path(temporary_directory), real_edit=True, allow_real_gate=True, require_injected_driver=True, raw_prompt_text=PHASE97_SECRET_PROMPT, notepad_driver=driver)  # 新增代码+Phase97ControlledNotepadLiveEdit：运行双门打开且注入 driver 的合同；如果没有这一行，显式成功路径没有事实来源。
            saved_text = Path(str(report["target_file"])).read_text(encoding="utf-8")  # 新增代码+Phase97ControlledNotepadLiveEdit：读取保存文件验证受控文本；如果没有这一行，保存成功只能相信 driver 自报。
        line = phase97_cli_line(report)  # 新增代码+Phase97ControlledNotepadLiveEdit：生成终端验收单行 token；如果没有这一行，CLI 输出格式没有覆盖。
        serialized = json.dumps(report, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase97ControlledNotepadLiveEdit：序列化报告用于扫描明文泄露；如果没有这一行，嵌套敏感文字可能漏检。
        self.assertTrue(report["passed"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认显式合同通过；如果没有这一行，字段级断言可能掩盖整体失败。
        self.assertTrue(report["real_notepad_edit_executed"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认合同把注入 driver 成功算作显式编辑执行；如果没有这一行，执行状态可能误报。
        self.assertTrue(report["saved_file_verified"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认磁盘文件通过验证；如果没有这一行，保存证据可能缺失。
        self.assertIn(PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_MARKER, line)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认 ready marker 出现在 CLI 行；如果没有这一行，验收脚本可能找不到阶段锚点。
        self.assertIn(PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK_TOKEN, line)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认 OK token 出现在 CLI 行；如果没有这一行，成功锚点漂移不会被发现。
        self.assertIn(PHASE97_REAL_NOTEPAD_LIVE_EDIT_ENV, serialized)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认启用环境门写入报告；如果没有这一行，生产启用方式不可审计。
        self.assertIn(PHASE97_REAL_NOTEPAD_LIVE_EDIT_REQUEST_ENV, serialized)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认请求环境门写入报告；如果没有这一行，真实请求方式不可审计。
        self.assertNotIn(PHASE97_SECRET_PROMPT, serialized)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认敏感 prompt 不在报告中；如果没有这一行，隐私泄露可能长期保存到 artifact。
        self.assertNotIn(PHASE97_SECRET_PROMPT, line)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认敏感 prompt 不在 CLI 行中；如果没有这一行，真实终端可能直接打印用户原文。
        self.assertNotIn(PHASE97_SECRET_PROMPT, driver.received_expected_text)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认 driver 收到的是受控文本不是用户 prompt；如果没有这一行，输入链路可能把敏感原文送进 Notepad。
        self.assertIn("PHASE97 controlled Notepad live edit", saved_text)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认文件内容是受控验收文本；如果没有这一行，保存文件可能不是计划要求的固定内容。

    def test_failed_driver_keeps_desktop_touch_evidence(self) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，验证失败时保留触桌面证据；如果没有这个测试，半执行副作用可能被 passed 掩盖。
        driver = FailingTouchingPhase97NotepadDriver()  # 新增代码+Phase97ControlledNotepadLiveEdit：创建失败型 fake driver；如果没有这一行，失败副作用路径没有样本。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase97ControlledNotepadLiveEdit：创建隔离运行目录；如果没有这一行，失败测试产物可能污染项目。
            report = run_phase97_controlled_notepad_live_edit_contract(base_dir=Path(temporary_directory), real_edit=True, allow_real_gate=True, require_injected_driver=True, raw_prompt_text=PHASE97_SECRET_PROMPT, notepad_driver=driver)  # 新增代码+Phase97ControlledNotepadLiveEdit：运行半失败合同；如果没有这一行，后续断言没有事实来源。
        self.assertFalse(report["passed"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认半执行失败不算通过；如果没有这一行，失败可能被误报成功。
        self.assertTrue(report["real_desktop_touched"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认触桌面副作用被保留；如果没有这一行，失败后副作用可能被隐藏。
        self.assertEqual(len(driver.calls), 1)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认失败 driver 确实调用一次；如果没有这一行，失败报告可能不是 driver 产生的。


class Phase97WindowsNotepadLiveEditDriverTests(unittest.TestCase):  # 新增代码+Phase97ControlledNotepadLiveEdit：类段开始，专门验证 Task3 driver 安全边界；如果没有这个类，合同测试无法证明真实驱动行为。
    def safe_window(self) -> dict[str, object]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，构造受控 Notepad 窗口；如果没有这段函数，多个测试会重复脆弱字典。
        return {"app_id": "notepad.exe", "process_name": "notepad.exe", "class_name": "Notepad", "window_id": "hwnd:9701", "pid": 9797, "process_id": 9797, "title_preview": "phase97_controlled_notepad_live_edit.txt - Notepad", "rect": {"left": 1, "top": 1, "right": 500, "bottom": 400}}  # 修改代码+Phase97ControlledNotepadLiveEdit：返回带目标文件标题线索和 pid 的窗口；如果没有这一行，driver 无法验证 Notepad、Phase97 文件身份以及无 hwnd 场景的同进程复核。

    def unsafe_window(self) -> dict[str, object]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，构造终端类危险窗口；如果没有这段函数，拒绝路径缺少稳定样本。
        return {"app_id": "powershell.exe", "process_name": "powershell.exe", "class_name": "ConsoleWindowClass", "window_id": "hwnd:9702", "pid": 9798, "process_id": 9798, "title_preview": "Windows PowerShell", "rect": {"left": 1, "top": 1, "right": 500, "bottom": 400}}  # 修改代码+Phase97ControlledNotepadLiveEdit：返回危险窗口身份和不同 pid；如果没有这一行，非 Notepad 拒绝与 pid 漂移测试没有输入。

    def make_driver(self, windows: list[dict[str, object]], sender: Phase97DriverFakeSender) -> Phase97WindowsNotepadLiveEditDriver:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，创建完全注入式 driver；如果没有这段函数，测试容易漏掉某个真实依赖。
        return Phase97WindowsNotepadLiveEditDriver(launcher=Phase97DriverFakeLauncher(windows[0]), window_probe=Phase97DriverSequenceProbe(windows), focuser=Phase97DriverFakeFocuser(), sender=sender, verifier=Phase97DriverFakeVerifier(), recheck_attempts=1, recheck_interval_seconds=0.0)  # 修改代码+Phase97ControlledNotepadLiveEdit：返回全 fake 依赖 driver 且关闭测试轮询等待；如果没有这一行，单测可能启动真实 Notepad、SendInput 或在失败样本上慢等。

    def minimal_launched_window(self) -> dict[str, object]:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，构造默认 launcher 可能返回的无 hwnd Notepad 身份；如果没有这个函数，空 window_id 真实复核兼容性没有测试样本。
        window = self.safe_window()  # 新增代码+Phase97ControlledNotepadLiveEdit：复用安全 Notepad 字段作为基础；如果没有这一行，测试会重复一大段窗口字典。
        window["window_id"] = ""  # 新增代码+Phase97ControlledNotepadLiveEdit：清空 window_id 模拟默认 launcher 最小身份；如果没有这一行，测试无法覆盖真实 launcher 返回空 hwnd 的情况。
        window["process_id"] = window["pid"]  # 修改代码+Phase97ControlledNotepadLiveEdit：保留默认 launcher 会返回的 process_id；如果没有这一行，无 hwnd 兼容会缺少同进程证据。
        return window  # 新增代码+Phase97ControlledNotepadLiveEdit：返回无 hwnd 但有标题线索的窗口；如果没有这一行，正向测试拿不到启动窗口样本。

    def test_driver_refuses_non_notepad_target_with_zero_send_events(self) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，验证非 Notepad 目标零事件拒绝；如果没有这个测试，终端窗口可能被错误输入。
        sender = Phase97DriverFakeSender()  # 新增代码+Phase97ControlledNotepadLiveEdit：创建记录型 sender；如果没有这一行，无法证明拒绝路径没有事件。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase97ControlledNotepadLiveEdit：创建隔离目录；如果没有这一行，测试产物可能污染项目。
            report = self.make_driver([self.unsafe_window()], sender).run(run_root=Path(temporary_directory), expected_text="safe text", target_file=Path(temporary_directory) / "phase97_controlled_notepad_live_edit.txt")  # 新增代码+Phase97ControlledNotepadLiveEdit：运行危险窗口 driver；如果没有这一行，拒绝行为没有事实来源。
        self.assertFalse(report["ok"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认危险目标不成功；如果没有这一行，非 Notepad 放行不会被发现。
        self.assertEqual(report["reason"], "unsafe_or_wrong_notepad_target")  # 新增代码+Phase97ControlledNotepadLiveEdit：确认失败原因是目标身份错误；如果没有这一行，失败可能来自别的偶然原因。
        self.assertEqual(sender.events, [])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认零发送事件；如果没有这一行，表面拒绝仍可能产生副作用。

    def test_driver_rechecks_target_before_input_and_blocks_drift(self) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，验证输入前复核失败会阻断输入；如果没有这个测试，焦点漂移可能把文本发到错误窗口。
        sender = Phase97DriverFakeSender()  # 新增代码+Phase97ControlledNotepadLiveEdit：创建记录型 sender；如果没有这一行，无法证明输入前漂移没有事件。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase97ControlledNotepadLiveEdit：创建隔离目录；如果没有这一行，测试产物可能污染项目。
            report = self.make_driver([self.safe_window(), self.unsafe_window()], sender).run(run_root=Path(temporary_directory), expected_text="safe text", target_file=Path(temporary_directory) / "phase97_controlled_notepad_live_edit.txt")  # 新增代码+Phase97ControlledNotepadLiveEdit：运行输入前漂移场景；如果没有这一行，复核失败没有事实来源。
        self.assertFalse(report["ok"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认漂移导致失败；如果没有这一行，错误窗口可能被误认为成功。
        self.assertFalse(report["target_rechecked_before_input"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认输入前复核未通过；如果没有这一行，复核字段可能误报 true。
        self.assertEqual(sender.events, [])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认没有发送输入或保存事件；如果没有这一行，漂移阻断没有副作用保障。

    def test_driver_rejects_same_title_with_different_pid_when_launch_has_no_window_id(self) -> None:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，验证无 hwnd 时不能只靠标题匹配；如果没有这个测试，旧 Notepad 标题相似窗口可能被误写。
        sender = Phase97DriverFakeSender()  # 修改代码+Phase97ControlledNotepadLiveEdit：创建记录型 sender；如果没有这一行，无法证明 pid 不同的相似窗口没有收到事件。
        launched_window = self.minimal_launched_window()  # 修改代码+Phase97ControlledNotepadLiveEdit：构造无 window_id 但有 process_id 的启动窗口；如果没有这一行，测试无法模拟默认 launcher 行为。
        stale_window = self.safe_window()  # 修改代码+Phase97ControlledNotepadLiveEdit：构造标题相同的 Notepad 快照；如果没有这一行，pid 漂移没有对照样本。
        stale_window["pid"] = 1111  # 修改代码+Phase97ControlledNotepadLiveEdit：把复核窗口 pid 改成不同进程；如果没有这一行，测试不会覆盖多 Notepad 风险。
        stale_window["process_id"] = 1111  # 修改代码+Phase97ControlledNotepadLiveEdit：同步 process_id 字段；如果没有这一行，不同快照字段形态可能漏测。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 修改代码+Phase97ControlledNotepadLiveEdit：创建隔离目录；如果没有这一行，测试产物可能污染项目。
            driver = Phase97WindowsNotepadLiveEditDriver(launcher=Phase97DriverFakeLauncher(launched_window), window_probe=Phase97DriverSequenceProbe([launched_window, stale_window]), focuser=Phase97DriverFakeFocuser(), sender=sender, verifier=Phase97DriverFakeVerifier(), recheck_attempts=1, recheck_interval_seconds=0.0)  # 修改代码+Phase97ControlledNotepadLiveEdit：创建全 fake driver 并注入 pid 漂移窗口且关闭等待；如果没有这一行，后续断言没有事实来源或失败路径会慢等。
            report = driver.run(run_root=Path(temporary_directory), expected_text="safe text", target_file=Path(temporary_directory) / "phase97_controlled_notepad_live_edit.txt")  # 修改代码+Phase97ControlledNotepadLiveEdit：运行 pid 漂移场景；如果没有这一行，无法观察 driver 是否拒绝。
        self.assertFalse(report["ok"])  # 修改代码+Phase97ControlledNotepadLiveEdit：确认 pid 不同导致失败；如果没有这一行，标题相同误放行不会被发现。
        self.assertEqual(report["reason"], "target_recheck_before_input_failed")  # 修改代码+Phase97ControlledNotepadLiveEdit：确认失败发生在输入前复核；如果没有这一行，失败点可能不清楚。
        self.assertEqual(sender.events, [])  # 修改代码+Phase97ControlledNotepadLiveEdit：确认没有任何真实输入事件；如果没有这一行，拒绝路径可能仍有副作用。

    def test_driver_rechecks_target_before_save_and_stops_after_text_input(self) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，验证保存前复核失败不再发送保存快捷键；如果没有这个测试，Ctrl+S 可能发到错误窗口。
        sender = Phase97DriverFakeSender()  # 新增代码+Phase97ControlledNotepadLiveEdit：创建记录型 sender；如果没有这一行，无法检查输入后是否还发送保存。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase97ControlledNotepadLiveEdit：创建隔离目录；如果没有这一行，测试产物可能污染项目。
            report = self.make_driver([self.safe_window(), self.safe_window(), self.safe_window(), self.unsafe_window()], sender).run(run_root=Path(temporary_directory), expected_text="safe text", target_file=Path(temporary_directory) / "phase97_controlled_notepad_live_edit.txt")  # 修改代码+Phase97ControlledNotepadLiveEdit：运行保存前漂移场景并预留 baseline 快照；如果没有这一行，保存前复核没有事实来源且 baseline 会把漂移提前到输入前。
        event_types = [str(event.get("type")) for event in sender.events]  # 新增代码+Phase97ControlledNotepadLiveEdit：提取事件类型方便断言；如果没有这一行，测试需要重复遍历原始事件。
        self.assertFalse(report["ok"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认保存前漂移导致失败；如果没有这一行，保存复核失败可能被误报成功。
        self.assertTrue(report["target_rechecked_before_input"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认输入前复核通过；如果没有这一行，无法区分失败发生在保存前。
        self.assertFalse(report["target_rechecked_before_save"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认保存前复核未通过；如果没有这一行，保存前漂移字段可能误报 true。
        self.assertIn("clipboard_text", event_types)  # 修改代码+Phase97ControlledNotepadLiveEdit：确认受控文本粘贴已经发送；如果没有这一行，测试不能证明停止点发生在输入之后。
        self.assertNotIn("save_hotkey", event_types)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认没有发送保存快捷键；如果没有这一行，Ctrl+S 发错窗口的风险不被覆盖。
        self.assertNotIn("key_down", event_types)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认保存前漂移不会发送 key_down 保存事件；如果没有这一行，支持形状的 Ctrl+S 仍可能发错窗口。
        self.assertNotIn("key_up", event_types)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认保存前漂移不会发送 key_up 保存事件；如果没有这一行，保存快捷键抬键也可能发到错误窗口。

    def test_driver_positive_path_sends_supported_save_events_and_sanitizes_report(self) -> None:  # 新增代码+Phase97ControlledNotepadLiveEdit：函数段开始，验证成功路径发送文本、支持形状保存事件、调用 verifier 并脱敏；如果没有这个测试，Task3 正向行为可能只有失败边界被覆盖。
        sender = Phase97DriverFakeSender()  # 新增代码+Phase97ControlledNotepadLiveEdit：创建记录型 sender；如果没有这一行，测试无法检查文本和 Ctrl+S 事件。
        verifier = Phase97DriverFakeVerifier()  # 新增代码+Phase97ControlledNotepadLiveEdit：创建记录型 verifier；如果没有这一行，测试无法证明保存验证被调用。
        expected_text = "safe text phase97 positive secret"  # 新增代码+Phase97ControlledNotepadLiveEdit：准备受控测试文本；如果没有这一行，脱敏断言没有具体明文样本。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase97ControlledNotepadLiveEdit：创建隔离目录；如果没有这一行，测试产物可能污染项目。
            launcher = Phase97DriverFakeLauncher(self.minimal_launched_window())  # 修改代码+Phase97ControlledNotepadLiveEdit：保存 launcher 方便检查 cleanup；如果没有这一行，正向路径收尾行为没有断言对象。
            driver = Phase97WindowsNotepadLiveEditDriver(launcher=launcher, window_probe=Phase97DriverSequenceProbe([self.minimal_launched_window(), self.safe_window(), self.safe_window()]), focuser=Phase97DriverFakeFocuser(), sender=sender, verifier=verifier, recheck_attempts=1, recheck_interval_seconds=0.0)  # 修改代码+Phase97ControlledNotepadLiveEdit：创建全 fake 正向 driver 且 launcher 无 window_id 并关闭等待；如果没有这一行，测试会触碰真实桌面或漏掉空 hwnd 匹配。
            report = driver.run(run_root=Path(temporary_directory), expected_text=expected_text, target_file=Path(temporary_directory) / "phase97_controlled_notepad_live_edit.txt")  # 新增代码+Phase97ControlledNotepadLiveEdit：运行正向 driver；如果没有这一行，后续断言没有事实来源。
        event_types = [str(event.get("type")) for event in sender.events]  # 新增代码+Phase97ControlledNotepadLiveEdit：提取事件类型方便断言；如果没有这一行，测试需要重复遍历原始事件。
        key_events = [(str(event.get("type")), str(event.get("key"))) for event in sender.events if str(event.get("type")) in {"key_down", "key_up"}]  # 新增代码+Phase97ControlledNotepadLiveEdit：提取保存快捷键事件序列；如果没有这一行，无法确认 Ctrl+S 使用受支持形状。
        serialized = json.dumps(report, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase97ControlledNotepadLiveEdit：序列化报告用于检查 raw expected_text 泄露；如果没有这一行，嵌套字段泄露可能漏检。
        self.assertTrue(report["ok"])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认正向 driver 成功；如果没有这一行，成功路径回归不会被发现。
        self.assertIn("clipboard_text", event_types)  # 修改代码+Phase97ControlledNotepadLiveEdit：确认发送了受控剪贴板文本事件；如果没有这一行，driver 可能只保存不输入。
        self.assertNotIn("save_hotkey", event_types)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认不再使用未知 save_hotkey 事件；如果没有这一行，真实 sender 可能忽略保存动作。
        self.assertEqual(key_events, [("key_down", "ctrl"), ("key_down", "s"), ("key_up", "s"), ("key_up", "ctrl")])  # 新增代码+Phase97ControlledNotepadLiveEdit：确认保存快捷键使用 key_down/key_up 形状；如果没有这一行，Ctrl+S 事件顺序可能漂移。
        self.assertEqual(launcher.cleanup_calls, 1)  # 修改代码+Phase97ControlledNotepadLiveEdit：确认成功路径执行 launcher cleanup；如果没有这一行，真实 Notepad 成功后可能残留。
        self.assertEqual(len(verifier.calls), 1)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认 verifier 被调用一次；如果没有这一行，报告成功可能没有保存验证事实。
        self.assertEqual(report["expected_text_length"], len(expected_text))  # 新增代码+Phase97ControlledNotepadLiveEdit：确认报告只暴露文本长度；如果没有这一行，脱敏摘要可能缺少规模信息。
        self.assertEqual(len(str(report["expected_text_sha256_16"])), 16)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认报告包含 16 位短哈希；如果没有这一行，脱敏内容指纹可能缺失。
        self.assertNotIn(expected_text, serialized)  # 新增代码+Phase97ControlledNotepadLiveEdit：确认报告不包含 raw expected_text；如果没有这一行，成功路径可能把受控正文写进报告。

    def test_real_low_level_sender_dispatches_phase97_ctrl_s_shape(self) -> None:  # 修改代码+Phase97ControlledNotepadLiveEdit：函数段开始，验证真实 sender 已支持 Phase97 的保存事件形状；如果没有这个测试，真实路径可能只在 fake sender 里成功。
        sender = Phase97InspectableLowLevelSender()  # 修改代码+Phase97ControlledNotepadLiveEdit：创建不触系统的真实 sender 子类；如果没有这一行，测试无法安全覆盖 win32 分支。
        result = sender.send_low_level([{"type": "set_foreground", "hwnd": 9701}, {"type": "clipboard_text", "text": "x"}, {"type": "key_down", "key": "ctrl"}, {"type": "key_down", "key": "s"}, {"type": "key_up", "key": "s"}, {"type": "key_up", "key": "ctrl"}])  # 修改代码+Phase97ControlledNotepadLiveEdit：发送 Phase97 真实事件形状给 sender；如果没有这一行，后续断言没有事实来源。
        self.assertTrue(result["ok"])  # 修改代码+Phase97ControlledNotepadLiveEdit：确认 sender 汇总为成功；如果没有这一行，事件分支失效不会被发现。
        self.assertEqual(sender.virtual_keys, [("ctrl", True), ("s", True), ("s", False), ("ctrl", False)])  # 修改代码+Phase97ControlledNotepadLiveEdit：确认 Ctrl+S 按下抬起顺序被真实 sender 分发；如果没有这一行，保存快捷键可能顺序漂移。
        self.assertEqual(sender.clipboard_texts, ["x"])  # 修改代码+Phase97ControlledNotepadLiveEdit：确认剪贴板粘贴分支通过；如果没有这一行，完整文本输入可能退回不可靠逐键输入。


if __name__ == "__main__":  # 新增代码+Phase97ControlledNotepadLiveEdit：允许直接运行本测试文件；如果没有这一行，手工排查时必须记完整 unittest 模块命令。
    unittest.main()  # 新增代码+Phase97ControlledNotepadLiveEdit：运行当前文件中的 unittest 用例；如果没有这一行，直接执行文件没有任何测试输出。
