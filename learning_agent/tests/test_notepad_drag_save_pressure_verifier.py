"""Notepad 拖动保存压力测试验证器的回归测试。"""  # 新增代码+NotepadDragSavePressure：说明本文件专门验证压力测试证据；如果没有这行，后来的人不知道这些测试守什么门。
from __future__ import annotations  # 新增代码+NotepadDragSavePressure：延迟解析类型注解；如果没有这行，部分旧 Python 运行路径更容易提前解析失败。

import json  # 新增代码+NotepadDragSavePressure：用于写入模拟 result.json；如果没有这行，测试不能构造和真实 controller 类似的证据。
import tempfile  # 新增代码+NotepadDragSavePressure：用于创建隔离临时目录；如果没有这行，测试可能污染真实桌面或仓库。
import unittest  # 新增代码+NotepadDragSavePressure：使用标准库测试框架；如果没有这行，项目缺 pytest 时无法运行测试。
from pathlib import Path  # 新增代码+NotepadDragSavePressure：用路径对象组织临时仓库、桌面和运行目录；如果没有这行，字符串拼路径容易出错。

from learning_agent.computer_use_mcp_v2.windows_runtime.notepad_drag_save_pressure_verifier import verify_notepad_drag_save_pressure  # 新增代码+NotepadDragSavePressure：导入待实现验证器；如果没有这行，测试无法驱动真实验证逻辑。


class NotepadDragSavePressureVerifierTests(unittest.TestCase):  # 新增代码+NotepadDragSavePressure：类段开始，集中验证压力测试证据门禁；如果没有这个类，相关断言会散落难维护。
    def _write_fake_run(self, root: Path, *, log_text: str) -> tuple[Path, Path]:  # 新增代码+NotepadDragSavePressure：函数段开始，构造最小 acceptance 证据；如果没有这个 helper，每个测试都要重复造目录。
        desktop = root / "Desktop"  # 新增代码+NotepadDragSavePressure：创建假的桌面目录路径；如果没有这行，测试会碰真实用户桌面。
        desktop.mkdir(parents=True)  # 新增代码+NotepadDragSavePressure：确保假桌面目录存在；如果没有这行，写 1.txt 会失败。
        (desktop / "1.txt").write_text("hello everyone\n", encoding="utf-8")  # 新增代码+NotepadDragSavePressure：写入测试目标文件；如果没有这行，通过场景无法证明内容校验。
        run_dir = root / "learning_agent" / "acceptance_controller" / "runs" / "agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260618_000000"  # 新增代码+NotepadDragSavePressure：模拟 controller 的运行目录；如果没有这行，验证器找不到最新证据。
        run_dir.mkdir(parents=True)  # 新增代码+NotepadDragSavePressure：创建模拟运行目录；如果没有这行，截图和日志无法写入。
        for name in ("01_startup.png", "02_prompt_sent.png", "03_final.png"):  # 新增代码+NotepadDragSavePressure：逐个创建三张必需截图；如果没有这行，截图门禁没有样本。
            (run_dir / name).write_bytes(b"fake-png-bytes")  # 新增代码+NotepadDragSavePressure：写入非空截图占位；如果没有这行，验证器应判截图缺失。
        (run_dir / "latest_run_readable.md").write_text(log_text, encoding="utf-8")  # 新增代码+NotepadDragSavePressure：写入可读 debug log；如果没有这行，验证器无法检查反作弊和 marker。
        (run_dir / "result.json").write_text(json.dumps({"completed": True}, ensure_ascii=False), encoding="utf-8")  # 新增代码+NotepadDragSavePressure：写入最小 result.json；如果没有这行，证据目录不像真实 controller 输出。
        return desktop, run_dir  # 新增代码+NotepadDragSavePressure：返回假桌面和运行目录；如果没有这行，测试无法把路径传给验证器。
    # 新增代码+NotepadDragSavePressure：函数段结束，_write_fake_run 到此结束；如果没有这个边界说明，初学者不容易看出造证据范围。

    def test_accepts_valid_file_screenshots_and_log_tokens(self) -> None:  # 新增代码+NotepadDragSavePressure：函数段开始，验证完整证据应通过；如果没有这个测试，验证器可能拒绝正常验收结果。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+NotepadDragSavePressure：使用临时目录隔离本测试；如果没有这行，测试会留下真实文件。
            root = Path(temp_dir)  # 新增代码+NotepadDragSavePressure：把临时目录转为 Path；如果没有这行，后续路径拼接不统一。
            log_text = "Computer Use Mode full_mode=true NOTEPAD_DRAG_SAVE_PRESSURE_OK hello everyone saved_to_desktop=true real_notepad_used=true mouse_drag_loop=true"  # 新增代码+NotepadDragSavePressure：构造成功 marker 和 full mode 日志；如果没有这行，验证器没有成功 token 可检查。
            desktop, run_dir = self._write_fake_run(root, log_text=log_text)  # 新增代码+NotepadDragSavePressure：创建完整成功证据；如果没有这行，测试没有输入样本。
            result = verify_notepad_drag_save_pressure(root, desktop_path=desktop, run_dir=run_dir)  # 新增代码+NotepadDragSavePressure：调用真实验证器；如果没有这行，测试不能证明行为。
            self.assertTrue(result["passed"])  # 新增代码+NotepadDragSavePressure：要求成功证据通过；如果没有这行，测试不会约束核心结论。
            self.assertEqual([], result["failures"])  # 新增代码+NotepadDragSavePressure：要求没有失败原因；如果没有这行，验证器可能一边失败一边标通过。
            self.assertTrue(result["file_exists"])  # 新增代码+NotepadDragSavePressure：要求文件存在字段为真；如果没有这行，报告可能漏掉桌面文件事实。
            self.assertTrue(result["content_verified"])  # 新增代码+NotepadDragSavePressure：要求内容字段为真；如果没有这行，报告可能没验证 hello everyone。
            self.assertTrue(result["screenshots_verified"])  # 新增代码+NotepadDragSavePressure：要求截图字段为真；如果没有这行，报告可能没验证真实终端证据。
    # 新增代码+NotepadDragSavePressure：函数段结束，test_accepts_valid_file_screenshots_and_log_tokens 到此结束；如果没有这个边界说明，初学者不容易看出成功样本范围。

    def test_rejects_direct_file_write_command_in_debug_log(self) -> None:  # 新增代码+NotepadDragSavePressure：函数段开始，验证直接写文件痕迹必须失败；如果没有这个测试，agent 可能绕过真实 Notepad。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+NotepadDragSavePressure：使用临时目录隔离本测试；如果没有这行，测试会污染真实环境。
            root = Path(temp_dir)  # 新增代码+NotepadDragSavePressure：把临时目录转为 Path；如果没有这行，路径接口不统一。
            log_text = "Computer Use Mode full_mode=true NOTEPAD_DRAG_SAVE_PRESSURE_OK mouse_drag_loop=true Set-Content C:\\Users\\joyzq\\Desktop\\1.txt hello everyone"  # 新增代码+NotepadDragSavePressure：构造包含直接写文件命令的日志；如果没有这行，反作弊测试没有坏样本。
            desktop, run_dir = self._write_fake_run(root, log_text=log_text)  # 新增代码+NotepadDragSavePressure：创建坏样本证据；如果没有这行，验证器没有可拒绝对象。
            result = verify_notepad_drag_save_pressure(root, desktop_path=desktop, run_dir=run_dir)  # 新增代码+NotepadDragSavePressure：调用真实验证器；如果没有这行，测试不会覆盖反作弊逻辑。
            self.assertFalse(result["passed"])  # 新增代码+NotepadDragSavePressure：要求直接写文件样本失败；如果没有这行，反作弊门禁形同虚设。
            self.assertIn("direct_file_write_detected", result["failures"])  # 新增代码+NotepadDragSavePressure：要求失败原因清楚；如果没有这行，用户无法知道为什么失败。
            self.assertFalse(result["direct_file_write_not_detected"])  # 新增代码+NotepadDragSavePressure：要求报告字段标出检测到风险；如果没有这行，机器报告会误导。
    # 新增代码+NotepadDragSavePressure：函数段结束，test_rejects_direct_file_write_command_in_debug_log 到此结束；如果没有这个边界说明，初学者不容易看出坏样本范围。


if __name__ == "__main__":  # 新增代码+NotepadDragSavePressure：允许直接运行本测试文件；如果没有这行，手动调试要记完整 unittest 命令。
    unittest.main()  # 新增代码+NotepadDragSavePressure：启动 unittest；如果没有这行，直接运行文件不会执行测试。
