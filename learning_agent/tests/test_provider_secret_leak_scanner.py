import subprocess  # 新增代码+SecretLeakScannerTest：用子进程验证真实 CLI 退出码；如果没有这行，测试无法覆盖人工运行路径。
import sys  # 新增代码+SecretLeakScannerTest：获取当前 Python 解释器路径；如果没有这行，Windows 上可能调用错 Python。
import tempfile  # 新增代码+SecretLeakScannerTest：创建隔离扫描目录；如果没有这行，测试会污染真实项目文件。
import unittest  # 新增代码+SecretLeakScannerTest：沿用项目现有 unittest 风格；如果没有这行，测试类不会被发现。
from pathlib import Path  # 新增代码+SecretLeakScannerTest：跨平台处理临时文件路径；如果没有这行，路径拼接容易出错。


PROJECT_ROOT = Path(__file__).resolve().parents[2]  # 新增代码+SecretLeakScannerTest：定位仓库根目录；如果没有这行，脚本路径会随运行目录变化。
SCANNER_SCRIPT = PROJECT_ROOT / "learning_agent" / "scripts" / "assert_no_real_provider_secret_leaks.py"  # 新增代码+SecretLeakScannerTest：定位被测扫描器脚本；如果没有这行，测试无法运行真实 CLI。


class ProviderSecretLeakScannerTests(unittest.TestCase):  # 新增代码+SecretLeakScannerTest：测试类段开始，锁定结构化泄漏扫描合同；如果没有这个类，扫描器规则退化不会被发现。
    def _run_scanner(self, target: Path) -> subprocess.CompletedProcess[str]:  # 新增代码+SecretLeakScannerTest：函数段开始，运行扫描器并返回结果；如果没有这段，每个测试都会重复子进程样板。
        return subprocess.run([sys.executable, str(SCANNER_SCRIPT), str(target)], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)  # 新增代码+SecretLeakScannerTest：执行真实脚本但不自动抛错；如果没有这行，测试无法检查失败输出。
    # 新增代码+SecretLeakScannerTest：函数段结束，_run_scanner 到此结束；如果没有边界说明，初学者不易看出它只负责 CLI 调用。

    def test_safe_field_names_and_test_values_pass(self) -> None:  # 新增代码+SecretLeakScannerTest：测试段开始，确认字段名和 test_ 假值不会误报；如果没有这段，扫描器可能阻碍合法 OAuth schema。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+SecretLeakScannerTest：创建隔离目录；如果没有这行，测试文件可能留在项目里。
            target = Path(directory) / "safe.json"  # 新增代码+SecretLeakScannerTest：准备安全样本文件路径；如果没有这行，无法写入待扫文件。
            target.write_text('{"access_token":"test_access_token_value","refresh_token":"test_refresh_token_value","secret_ref":"provider:openai:oauth","authorization":"Bearer test_fake_token_value_abcdefghijklmnopqrstuvwxyz"}', encoding="utf-8")  # 新增代码+SecretLeakScannerTest：写入允许的字段名和 test_ 假值；如果没有这行，测试没有安全输入。
            result = self._run_scanner(Path(directory))  # 新增代码+SecretLeakScannerTest：扫描隔离目录；如果没有这行，断言没有实际对象。
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)  # 新增代码+SecretLeakScannerTest：确认安全内容通过；如果没有这行，误报不会被发现。
            self.assertIn("Provider secret leak scan passed.", result.stdout)  # 新增代码+SecretLeakScannerTest：确认输出蓝图成功文本；如果没有这行，人工验收字符串可能漂移。
    # 新增代码+SecretLeakScannerTest：测试段结束，安全字段名和 test_ 假值合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_real_bearer_token_fails(self) -> None:  # 新增代码+SecretLeakScannerTest：测试段开始，确认真实形状 Bearer token 会失败；如果没有这段，OAuth access token 泄漏可能漏检。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+SecretLeakScannerTest：创建隔离目录；如果没有这行，测试会污染真实文件。
            target = Path(directory) / "memory" / "gui.log"  # 新增代码+SecretLeakScannerTest：准备高风险日志路径；如果没有这行，无法模拟真实 GUI 日志。
            target.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+SecretLeakScannerTest：创建父目录；如果没有这行，写文件会失败。
            target.write_text("Authorization: Bearer abcdefghijklmnopqrstuvwxyzABCDEFGH123456", encoding="utf-8")  # 新增代码+SecretLeakScannerTest：写入真实形状 Bearer；如果没有这行，规则没有红灯样本。
            result = self._run_scanner(Path(directory))  # 新增代码+SecretLeakScannerTest：运行扫描；如果没有这行，断言不会触发。
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)  # 新增代码+SecretLeakScannerTest：确认扫描失败；如果没有这行，泄漏仍可能通过。
            self.assertIn("bearer_token", result.stdout)  # 新增代码+SecretLeakScannerTest：确认失败类型清楚；如果没有这行，排查信息可能不足。
    # 新增代码+SecretLeakScannerTest：测试段结束，Bearer token 红灯合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_real_openai_api_key_fails(self) -> None:  # 新增代码+SecretLeakScannerTest：测试段开始，确认 sk- API key 形状会失败；如果没有这段，API key 泄漏可能漏检。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+SecretLeakScannerTest：创建隔离目录；如果没有这行，测试会污染项目。
            target = Path(directory) / "provider.txt"  # 新增代码+SecretLeakScannerTest：准备待扫文本文件；如果没有这行，无法写入危险样本。
            target.write_text("api_key = sk-abcdefghijklmnopqrstuvwxyz123456", encoding="utf-8")  # 新增代码+SecretLeakScannerTest：写入真实形状 OpenAI key；如果没有这行，规则没有红灯输入。
            result = self._run_scanner(Path(directory))  # 新增代码+SecretLeakScannerTest：运行扫描；如果没有这行，断言没有结果。
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)  # 新增代码+SecretLeakScannerTest：确认扫描失败；如果没有这行，API key 泄漏会漏过。
            self.assertIn("openai_api_key", result.stdout)  # 新增代码+SecretLeakScannerTest：确认失败类型；如果没有这行，用户不知道命中原因。
    # 新增代码+SecretLeakScannerTest：测试段结束，OpenAI API key 红灯合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_jwt_like_value_fails_outside_fixtures(self) -> None:  # 新增代码+SecretLeakScannerTest：测试段开始，确认三段 JWT 形状在非 fixture 中失败；如果没有这段，id_token 泄漏可能漏检。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+SecretLeakScannerTest：创建隔离目录；如果没有这行，测试文件可能残留。
            target = Path(directory) / "diagnostics.json"  # 新增代码+SecretLeakScannerTest：准备诊断文件路径；如果没有这行，无法模拟 GUI 诊断产物。
            target.write_text("eyJabcdefghijklmnopqr.eyJabcdefghijklmnopqr.abcdefghijklmnopqrstuv", encoding="utf-8")  # 新增代码+SecretLeakScannerTest：写入 JWT 形状值；如果没有这行，JWT 规则没有红灯样本。
            result = self._run_scanner(Path(directory))  # 新增代码+SecretLeakScannerTest：运行扫描；如果没有这行，断言不会执行。
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)  # 新增代码+SecretLeakScannerTest：确认扫描失败；如果没有这行，JWT 泄漏不会被抓住。
            self.assertIn("jwt_like_token", result.stdout)  # 新增代码+SecretLeakScannerTest：确认失败类型；如果没有这行，排查信息不清楚。
    # 新增代码+SecretLeakScannerTest：测试段结束，JWT 红灯合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_jwt_like_value_is_allowed_inside_fixture_path(self) -> None:  # 新增代码+SecretLeakScannerTest：测试段开始，确认 fixture 允许真实外形假样本；如果没有这段，后续黄金 SSE 无法逼近真实结构。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+SecretLeakScannerTest：创建隔离目录；如果没有这行，测试会污染项目。
            target = Path(directory) / "tests" / "fixtures" / "sample.sse"  # 新增代码+SecretLeakScannerTest：准备 fixture 路径；如果没有这行，白名单路径无法验证。
            target.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+SecretLeakScannerTest：创建 fixture 目录；如果没有这行，写文件会失败。
            target.write_text("eyJabcdefghijklmnopqr.eyJabcdefghijklmnopqr.abcdefghijklmnopqrstuv", encoding="utf-8")  # 新增代码+SecretLeakScannerTest：写入真实外形但受控的样本；如果没有这行，fixture 例外没有输入。
            result = self._run_scanner(Path(directory))  # 新增代码+SecretLeakScannerTest：运行扫描；如果没有这行，断言没有结果。
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)  # 新增代码+SecretLeakScannerTest：确认 fixture 不误报；如果没有这行，黄金样本会阻塞开发。
    # 新增代码+SecretLeakScannerTest：测试段结束，fixture 例外合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_non_redacted_email_fails_in_memory(self) -> None:  # 新增代码+SecretLeakScannerTest：测试段开始，确认 memory 中真实邮箱失败；如果没有这段，账号发现可能泄露用户邮箱。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+SecretLeakScannerTest：创建隔离目录；如果没有这行，测试会污染真实 memory。
            target = Path(directory) / "memory" / "provider_diagnostics.log"  # 新增代码+SecretLeakScannerTest：准备高风险诊断日志；如果没有这行，无法模拟真实落盘风险。
            target.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+SecretLeakScannerTest：创建父目录；如果没有这行，写入会失败。
            target.write_text("account=user@example.test", encoding="utf-8")  # 新增代码+SecretLeakScannerTest：写入未脱敏邮箱；如果没有这行，邮箱规则没有红灯样本。
            result = self._run_scanner(Path(directory))  # 新增代码+SecretLeakScannerTest：运行扫描；如果没有这行，断言没有结果。
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)  # 新增代码+SecretLeakScannerTest：确认扫描失败；如果没有这行，邮箱泄漏会漏过。
            self.assertIn("email_address", result.stdout)  # 新增代码+SecretLeakScannerTest：确认失败类型；如果没有这行，排查不知道是邮箱问题。
    # 新增代码+SecretLeakScannerTest：测试段结束，邮箱红灯合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


if __name__ == "__main__":  # 新增代码+SecretLeakScannerTest：允许直接运行本测试文件；如果没有这行，手动调试需要记住 unittest 命令。
    unittest.main()  # 新增代码+SecretLeakScannerTest：启动 unittest runner；如果没有这行，直接 python 文件不会执行测试。
