from __future__ import annotations  # 新增代码+AlignmentMatrixHardening：延迟解析类型注解；如果没有这行代码，Path 等注解可能在导入时提前求值。

import tempfile  # 新增代码+AlignmentMatrixHardening：导入临时目录工具；如果没有这行代码，矩阵测试会污染真实仓库文件。
import unittest  # 新增代码+AlignmentMatrixHardening：导入 unittest 测试框架；如果没有这行代码，本文件无法声明测试用例。
from pathlib import Path  # 新增代码+AlignmentMatrixHardening：导入 Path 进行跨平台路径拼接；如果没有这行代码，临时文件路径会变成脆弱字符串。

from learning_agent.computer_use_mcp_v2.windows_runtime.claudecode_alignment_matrix import evaluate_claudecode_alignment_matrix  # 新增代码+AlignmentMatrixHardening：导入待测矩阵评估函数；如果没有这行代码，测试无法验证 CA07/CA14 判定。


class ClaudeCodeAlignmentMatrixTests(unittest.TestCase):  # 新增代码+AlignmentMatrixHardening：类段开始，集中验证 ClaudeCode 对齐矩阵关键门禁；如果没有这段类，矩阵 partial/parity 容易误报。
    def _write_text(self, root: Path, relative_path: str, text: str) -> None:  # 新增代码+AlignmentMatrixHardening：函数段开始，向临时仓库写入测试证据文件；如果没有这段 helper，每个测试都要重复 mkdir 和 write_text。
        target = root / relative_path  # 新增代码+AlignmentMatrixHardening：把相对路径挂到临时根目录；如果没有这行代码，测试文件可能写到真实仓库。
        target.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+AlignmentMatrixHardening：确保父目录存在；如果没有这行代码，首次写深层路径会失败。
        target.write_text(text, encoding="utf-8")  # 新增代码+AlignmentMatrixHardening：写入 UTF-8 文本证据；如果没有这行代码，矩阵没有源码 token 可读取。
    # 新增代码+AlignmentMatrixHardening：函数段结束，_write_text 到此结束；如果没有这个边界说明，用户不容易看出测试文件写入范围。

    def test_matrix_marks_ca07_aligned_when_both_sides_have_real_input_tokens(self) -> None:  # 新增代码+AlignmentMatrixHardening：函数段开始，验证 CA07 需要两侧真实输入 token；如果没有这段测试，CA07 可能靠文件名误报。
        with tempfile.TemporaryDirectory() as tmp:  # 新增代码+AlignmentMatrixHardening：创建临时目录；如果没有这行代码，测试会污染真实项目。
            repo_root = Path(tmp) / "openharness"  # 新增代码+AlignmentMatrixHardening：创建临时 OpenHarness 根目录；如果没有这行代码，矩阵没有独立 repo_root。
            claudecode_root = Path(tmp) / "claudecode"  # 新增代码+AlignmentMatrixHardening：创建临时 ClaudeCode 根目录；如果没有这行代码，矩阵没有独立参考源码。
            self._write_text(claudecode_root, "utils/computerUse/executor.ts", "click\nscroll\ndrag\ntype\n")  # 新增代码+AlignmentMatrixHardening：写入 ClaudeCode 输入动作 token；如果没有这行代码，CA07 参考侧会失败。
            self._write_text(repo_root, "learning_agent/computer_use_mcp_v2/windows_runtime/real_sendinput_guard.py", "SendInput\nphysical_dispatch\n")  # 新增代码+AlignmentMatrixHardening：写入 OpenHarness 真实输入 token；如果没有这行代码，CA07 OpenHarness 侧证据不足。
            self._write_text(repo_root, "learning_agent/computer_use_mcp_v2/windows_runtime/sendinput_executor.py", "real_sendinput\n")  # 新增代码+AlignmentMatrixHardening：写入 OpenHarness sendinput executor token；如果没有这行代码，CA07 缺少真实派发关键词。
            self._write_text(repo_root, "learning_agent/memory/computer_use/post_parity/phase148c_fresh_benchmark_evidence_20260613.json", "{}")  # 新增代码+AlignmentMatrixHardening：写入 CA07 维度列出的证据文件；如果没有这行代码，矩阵读取证据路径时缺文件。

            result = evaluate_claudecode_alignment_matrix(repo_root=repo_root, claudecode_root=claudecode_root)  # 新增代码+AlignmentMatrixHardening：执行矩阵评估；如果没有这行代码，测试无法得到 CA07 状态。

            ca07 = [item for item in result["dimensions"] if item["id"] == "CA07"][0]  # 新增代码+AlignmentMatrixHardening：取出 CA07 结果；如果没有这行代码，测试无法聚焦真实输入维度。
            self.assertEqual(ca07["status"], "aligned")  # 新增代码+AlignmentMatrixHardening：确认两侧 token 具备时 CA07 aligned；如果没有这行断言，矩阵可能仍误报 partial。
    # 新增代码+AlignmentMatrixHardening：函数段结束，test_matrix_marks_ca07_aligned_when_both_sides_have_real_input_tokens 到此结束；如果没有这个边界说明，用户不容易看出 CA07 测试范围。

    def test_matrix_keeps_ca14_partial_without_visible_terminal_gate(self) -> None:  # 新增代码+AlignmentMatrixHardening：函数段开始，验证没有可见终端 gate 时 CA14 只能 partial；如果没有这段测试，静态证据可能绕过规则十七。
        with tempfile.TemporaryDirectory() as tmp:  # 新增代码+AlignmentMatrixHardening：创建临时目录；如果没有这行代码，测试会污染真实项目。
            repo_root = Path(tmp) / "openharness"  # 新增代码+AlignmentMatrixHardening：创建临时 OpenHarness 根目录；如果没有这行代码，矩阵没有独立 repo_root。
            claudecode_root = Path(tmp) / "claudecode"  # 新增代码+AlignmentMatrixHardening：创建临时 ClaudeCode 根目录；如果没有这行代码，矩阵没有独立参考源码。
            self._write_text(claudecode_root, "utils/computerUse/setup.ts", "mcp__computer-use__\n")  # 新增代码+AlignmentMatrixHardening：写入 ClaudeCode MCP token；如果没有这行代码，CA14 参考侧没有证据。
            self._write_text(claudecode_root, "utils/computerUse/wrapper.tsx", "runPermissionDialog\n")  # 新增代码+AlignmentMatrixHardening：写入 ClaudeCode 权限对话 token；如果没有这行代码，CA14 参考侧不完整。

            result = evaluate_claudecode_alignment_matrix(repo_root=repo_root, claudecode_root=claudecode_root)  # 新增代码+AlignmentMatrixHardening：执行矩阵评估；如果没有这行代码，测试无法得到 CA14 状态。

            ca14 = [item for item in result["dimensions"] if item["id"] == "CA14"][0]  # 新增代码+AlignmentMatrixHardening：取出 CA14 结果；如果没有这行代码，测试无法聚焦最终可见终端维度。
            self.assertEqual(ca14["status"], "partial")  # 新增代码+AlignmentMatrixHardening：确认缺 gate 时只能 partial；如果没有这行断言，矩阵可能误升 aligned。
            self.assertFalse(result["visible_terminal_gate"])  # 新增代码+AlignmentMatrixHardening：确认总报告 visible gate 为 false；如果没有这行断言，摘要可能误导用户。
    # 新增代码+AlignmentMatrixHardening：函数段结束，test_matrix_keeps_ca14_partial_without_visible_terminal_gate 到此结束；如果没有这个边界说明，用户不容易看出 CA14 partial 测试范围。

    def test_matrix_marks_ca14_aligned_only_with_existing_visible_run_dir(self) -> None:  # 新增代码+AlignmentMatrixHardening：函数段开始，验证 CA14 需要显式 gate 和真实 run 目录；如果没有这段测试，随便传字符串可能伪造验收。
        with tempfile.TemporaryDirectory() as tmp:  # 新增代码+AlignmentMatrixHardening：创建临时目录；如果没有这行代码，测试会污染真实项目。
            repo_root = Path(tmp) / "openharness"  # 新增代码+AlignmentMatrixHardening：创建临时 OpenHarness 根目录；如果没有这行代码，矩阵没有独立 repo_root。
            claudecode_root = Path(tmp) / "claudecode"  # 新增代码+AlignmentMatrixHardening：创建临时 ClaudeCode 根目录；如果没有这行代码，矩阵没有独立参考源码。
            visible_run_dir = repo_root / "learning_agent" / "acceptance_controller" / "runs" / "visible-terminal-run"  # 新增代码+AlignmentMatrixHardening：构造真实存在的可见终端 run 目录；如果没有这行代码，CA14 不能 aligned。
            visible_run_dir.mkdir(parents=True)  # 新增代码+AlignmentMatrixHardening：创建 run 目录；如果没有这行代码，矩阵会拒绝 final_visible_run_dir。
            self._write_text(claudecode_root, "utils/computerUse/setup.ts", "mcp__computer-use__\n")  # 新增代码+AlignmentMatrixHardening：写入 ClaudeCode MCP token；如果没有这行代码，CA14 参考侧没有证据。
            self._write_text(claudecode_root, "utils/computerUse/wrapper.tsx", "runPermissionDialog\n")  # 新增代码+AlignmentMatrixHardening：写入 ClaudeCode 权限对话 token；如果没有这行代码，CA14 参考侧不完整。

            result = evaluate_claudecode_alignment_matrix(repo_root=repo_root, claudecode_root=claudecode_root, visible_terminal_gate=True, final_visible_run_dir=str(visible_run_dir))  # 新增代码+AlignmentMatrixHardening：带真实 run 目录执行矩阵；如果没有这行代码，测试无法验证最终 gate 成功路径。

            ca14 = [item for item in result["dimensions"] if item["id"] == "CA14"][0]  # 新增代码+AlignmentMatrixHardening：取出 CA14 结果；如果没有这行代码，测试无法聚焦最终可见终端维度。
            self.assertEqual(ca14["status"], "aligned")  # 新增代码+AlignmentMatrixHardening：确认真实 run 目录加显式 gate 才 aligned；如果没有这行断言，最终验收门槛可能失效。
            self.assertTrue(ca14["details"]["final_visible_run_dir_exists"])  # 新增代码+AlignmentMatrixHardening：确认细节中记录目录存在；如果没有这行断言，报告缺少可追溯证据。
    # 新增代码+AlignmentMatrixHardening：函数段结束，test_matrix_marks_ca14_aligned_only_with_existing_visible_run_dir 到此结束；如果没有这个边界说明，用户不容易看出 CA14 aligned 测试范围。

    def test_matrix_reports_platform_exclusions_without_counting_them_as_missing(self) -> None:  # 新增代码+AlignmentMatrixHardening：函数段开始，验证平台排除项只是说明而不是缺失；如果没有这段测试，macOS 差异可能被误算成 OpenHarness 缺口。
        with tempfile.TemporaryDirectory() as tmp:  # 新增代码+AlignmentMatrixHardening：创建临时目录；如果没有这行代码，测试会污染真实项目。
            repo_root = Path(tmp) / "openharness"  # 新增代码+AlignmentMatrixHardening：创建临时 OpenHarness 根目录；如果没有这行代码，矩阵没有独立 repo_root。
            claudecode_root = Path(tmp) / "claudecode"  # 新增代码+AlignmentMatrixHardening：创建临时 ClaudeCode 根目录；如果没有这行代码，矩阵没有独立参考源码。

            result = evaluate_claudecode_alignment_matrix(repo_root=repo_root, claudecode_root=claudecode_root)  # 新增代码+AlignmentMatrixHardening：执行矩阵评估；如果没有这行代码，测试无法读取排除项。

            self.assertIn("excluded_platform_differences", result)  # 新增代码+AlignmentMatrixHardening：确认报告包含排除项说明；如果没有这行断言，用户无法区分系统差异和真实缺口。
            self.assertIn("macos_tcc", result["excluded_platform_differences"])  # 新增代码+AlignmentMatrixHardening：确认 macOS TCC 被列为排除项；如果没有这行断言，TCC 可能被误当 Windows 缺失。
            self.assertEqual(result["dimension_total"], 14)  # 新增代码+AlignmentMatrixHardening：确认排除项不增加矩阵分母；如果没有这行断言，系统差异会污染 14 项对齐统计。
    # 新增代码+AlignmentMatrixHardening：函数段结束，test_matrix_reports_platform_exclusions_without_counting_them_as_missing 到此结束；如果没有这个边界说明，用户不容易看出排除项测试范围。


if __name__ == "__main__":  # 新增代码+AlignmentMatrixHardening：允许直接运行本测试文件；如果没有这行代码，手动调试时需要额外 unittest 参数。
    unittest.main()  # 新增代码+AlignmentMatrixHardening：启动 unittest 主程序；如果没有这行代码，直接运行文件不会执行测试。
