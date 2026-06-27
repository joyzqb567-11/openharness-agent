import re  # 新增代码+RealModelLatencySecretGateTest：用于扫描运行证据里的敏感模式；如果没有这行，测试只能做简单字符串匹配。
import unittest  # 新增代码+RealModelLatencySecretGateTest：使用项目现有 unittest 风格；如果没有这行，pytest 不会收集这个测试类。
from pathlib import Path  # 新增代码+RealModelLatencySecretGateTest：用 Path 定位证据目录；如果没有这行，Windows 路径拼接更脆弱。


EVIDENCE_ROOT = Path("learning_agent/test/real_model_latency_v2_20260626")  # 新增代码+RealModelLatencySecretGateTest：定义本轮真实模型延迟证据根目录；如果没有这行，扫描范围会散落在测试里。
FORBIDDEN_EVIDENCE_PATTERNS = (  # 新增代码+RealModelLatencySecretGateTest：定义运行证据里绝不能出现的敏感模式；如果没有这段，OAuth code/token 泄漏不能被自动阻断。
    re.compile(r"access_token", re.IGNORECASE),  # 新增代码+RealModelLatencySecretGateTest：禁止 access token 字段名；如果没有这行，OAuth 凭证字段可能进入证据。
    re.compile(r"refresh_token", re.IGNORECASE),  # 新增代码+RealModelLatencySecretGateTest：禁止 refresh token 字段名；如果没有这行，长期凭证字段可能进入证据。
    re.compile(r"id_token", re.IGNORECASE),  # 新增代码+RealModelLatencySecretGateTest：禁止 id token 字段名；如果没有这行，身份 token 字段可能进入证据。
    re.compile(r"authorization_code", re.IGNORECASE),  # 新增代码+RealModelLatencySecretGateTest：禁止授权码字段名；如果没有这行，OAuth code 可能被记录。
    re.compile(r"Bearer\s+", re.IGNORECASE),  # 新增代码+RealModelLatencySecretGateTest：禁止 Bearer 凭证形态；如果没有这行，请求头泄漏可能漏过。
    re.compile(r"sk-[A-Za-z0-9]{12,}"),  # 新增代码+RealModelLatencySecretGateTest：禁止 OpenAI API key 形态；如果没有这行，API key 泄漏可能漏过。
    re.compile(r"cookie", re.IGNORECASE),  # 新增代码+RealModelLatencySecretGateTest：禁止 cookie 字段；如果没有这行，浏览器会话信息可能进入证据。
    re.compile(r"oauth/authorize\?response_type=code", re.IGNORECASE),  # 新增代码+RealModelLatencySecretGateTest：禁止完整 OAuth 授权 URL；如果没有这行，state/challenge 可能进入证据。
    re.compile(r"localhost:1455/auth/callback\?code=", re.IGNORECASE),  # 新增代码+RealModelLatencySecretGateTest：禁止带 code 的本地回调 URL；如果没有这行，授权 code 可能进入证据。
)  # 新增代码+RealModelLatencySecretGateTest：敏感模式列表结束；如果没有这行，Python 元组语法不完整。


class GuiModelLatencySecretRedactionTests(unittest.TestCase):  # 新增代码+RealModelLatencySecretGateTest：测试类段开始，锁定真实模型延迟证据的脱敏门禁；如果没有这个类，截图/日志证据可能意外保存凭证。
    def test_real_model_latency_evidence_contains_no_oauth_or_api_secrets(self) -> None:  # 新增代码+RealModelLatencySecretGateTest：测试段开始，扫描本轮证据目录；如果没有这段，Task 10 无自动保护。
        self.assertTrue(EVIDENCE_ROOT.exists(), f"Evidence root missing: {EVIDENCE_ROOT}")  # 新增代码+RealModelLatencySecretGateTest：确认证据目录存在；如果没有这行，空扫描会误以为通过。
        violations: list[str] = []  # 新增代码+RealModelLatencySecretGateTest：收集所有违规命中；如果没有这行，测试只能报告第一个问题。
        for path in sorted(EVIDENCE_ROOT.rglob("*")):  # 新增代码+RealModelLatencySecretGateTest：递归遍历证据目录；如果没有这行，子目录日志可能漏扫。
            if not path.is_file():  # 新增代码+RealModelLatencySecretGateTest：只扫描文件；如果没有这行，目录读取会失败。
                continue  # 新增代码+RealModelLatencySecretGateTest：跳过目录；如果没有这行，后续 read_text 会报错。
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:  # 新增代码+RealModelLatencySecretGateTest：跳过二进制截图；如果没有这行，图片 bytes 会造成误判或解码失败。
                continue  # 新增代码+RealModelLatencySecretGateTest：图片交给人工视觉检查，不做文本扫描；如果没有这行，测试可能因二进制内容失败。
            text = path.read_text(encoding="utf-8", errors="ignore")  # 新增代码+RealModelLatencySecretGateTest：以 UTF-8 宽容读取文本证据；如果没有这行，日志编码差异会中断扫描。
            for pattern in FORBIDDEN_EVIDENCE_PATTERNS:  # 新增代码+RealModelLatencySecretGateTest：逐个敏感模式扫描；如果没有这行，只能覆盖一个固定词。
                if pattern.search(text):  # 新增代码+RealModelLatencySecretGateTest：发现敏感模式即记录；如果没有这行，违规不会进入报告。
                    violations.append(f"{path}:{pattern.pattern}")  # 新增代码+RealModelLatencySecretGateTest：记录文件和模式；如果没有这行，失败时无法定位。
        self.assertEqual([], violations)  # 新增代码+RealModelLatencySecretGateTest：要求零违规；如果没有这行，测试不会真正阻断泄漏。
    # 新增代码+RealModelLatencySecretGateTest：测试段结束，test_real_model_latency_evidence_contains_no_oauth_or_api_secrets 到此结束；如果没有边界说明，用户不容易看出扫描范围。
# 新增代码+RealModelLatencySecretGateTest：测试类段结束，GuiModelLatencySecretRedactionTests 到此结束；如果没有边界说明，用户不容易看出本文件只测证据脱敏。


if __name__ == "__main__":  # 新增代码+RealModelLatencySecretGateTest：允许直接运行本文件；如果没有这行，手动排查需要记住 unittest 命令。
    unittest.main()  # 新增代码+RealModelLatencySecretGateTest：启动 unittest；如果没有这行，直接 python 文件不会执行测试。
