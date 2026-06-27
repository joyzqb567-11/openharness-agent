import json  # 新增代码+DirectOAuthSseProbeTest：用于把 probe 安全摘要序列化后检查是否泄露敏感值；如果没有这行，测试只能检查对象字段。
import unittest  # 新增代码+DirectOAuthSseProbeTest：使用项目现有 unittest 风格；如果没有这行，pytest 不能按类收集这些合同测试。


DIRECT_OAUTH_READY_ENV = {  # 新增代码+DirectOAuthSseProbeTest：定义满足 direct OAuth SSE probe 的最小安全环境；如果没有这段，每个测试都要重复四个门禁变量。
    "OPENHARNESS_OPENAI_AUTH_MODE": "direct_oauth",  # 新增代码+DirectOAuthSseProbeTest：启用 direct OAuth 模式；如果没有这行，probe 应该保持 not_configured。
    "OPENHARNESS_OPENAI_EXPERIMENTAL": "1",  # 新增代码+DirectOAuthSseProbeTest：显式打开实验能力；如果没有这行，fast path 不能被声明。
    "OPENHARNESS_PROVIDER_SECRET_STORE": "os_encrypted",  # 新增代码+DirectOAuthSseProbeTest：要求系统加密密钥存储；如果没有这行，测试环境不满足安全条件。
    "OPENHARNESS_OPENAI_CLIENT_ID": "openharness-client-test",  # 新增代码+DirectOAuthSseProbeTest：提供 OpenHarness 自己的 client id 占位值；如果没有这行，代码可能误回退其它应用 id。
}  # 新增代码+DirectOAuthSseProbeTest：安全环境字典结束；如果没有这行，Python 字典语法不完整。


class CodexOAuthStreamingProbeTests(unittest.TestCase):  # 新增代码+DirectOAuthSseProbeTest：测试类段开始，锁定 Direct OAuth SSE fast path 的探测门禁；如果没有这个类，未验证 SSE 可能被误宣称可用。
    def test_environment_gate_requires_all_explicit_direct_oauth_conditions(self) -> None:  # 新增代码+DirectOAuthSseProbeTest：测试段开始，验证四个安全环境条件缺一不可；如果没有这段，fast path 可能在半配置状态启用。
        from learning_agent.models.adapters import direct_oauth_sse_probe_environment_ready  # 新增代码+DirectOAuthSseProbeTest：导入环境门禁函数；如果没有这行，测试没有被测目标。

        self.assertTrue(direct_oauth_sse_probe_environment_ready(DIRECT_OAUTH_READY_ENV))  # 新增代码+DirectOAuthSseProbeTest：完整环境应通过；如果没有这行，测试无法证明 happy path。
        for key in DIRECT_OAUTH_READY_ENV:  # 新增代码+DirectOAuthSseProbeTest：逐个删除必要条件；如果没有这行，无法证明缺哪一个都会失败。
            partial_env = dict(DIRECT_OAUTH_READY_ENV)  # 新增代码+DirectOAuthSseProbeTest：复制环境避免污染共享 fixture；如果没有这行，循环会互相影响。
            partial_env.pop(key)  # 新增代码+DirectOAuthSseProbeTest：移除当前条件；如果没有这行，测试不会覆盖缺失场景。
            self.assertFalse(direct_oauth_sse_probe_environment_ready(partial_env), key)  # 新增代码+DirectOAuthSseProbeTest：缺任何条件都应拒绝；如果没有这行，门禁退化无法被发现。
    # 新增代码+DirectOAuthSseProbeTest：测试段结束，test_environment_gate_requires_all_explicit_direct_oauth_conditions 到此结束；如果没有边界说明，用户不容易看出覆盖的是环境门禁。

    def test_probe_refuses_to_claim_fast_path_when_environment_is_not_configured(self) -> None:  # 新增代码+DirectOAuthSseProbeTest：测试段开始，验证即使 payload 像成功，未配置环境也不能放行；如果没有这段，文档可能误报能力。
        from learning_agent.models.adapters import probe_codex_oauth_sse_payload  # 新增代码+DirectOAuthSseProbeTest：导入 SSE probe；如果没有这行，测试没有被测函数。

        raw_stream = 'data: {"type":"response.output_text.delta","delta":"真实"}\n\n'  # 新增代码+DirectOAuthSseProbeTest：构造看起来成功的文本增量；如果没有这行，未配置场景缺少诱饵输入。
        result = probe_codex_oauth_sse_payload(raw_stream, env={})  # 新增代码+DirectOAuthSseProbeTest：在空环境下执行 probe；如果没有这行，无法检查未配置结论。
        self.assertEqual("not_configured", result.status)  # 新增代码+DirectOAuthSseProbeTest：必须返回未配置；如果没有这行，fast path 可能被误放行。
        self.assertFalse(result.available)  # 新增代码+DirectOAuthSseProbeTest：available 布尔值必须是 False；如果没有这行，UI 可能只看布尔值误判。
        self.assertEqual(("response.output_text.delta",), result.event_types)  # 新增代码+DirectOAuthSseProbeTest：仍保留事件类型摘要；如果没有这行，排查时看不到远端 shape。
    # 新增代码+DirectOAuthSseProbeTest：测试段结束，test_probe_refuses_to_claim_fast_path_when_environment_is_not_configured 到此结束；如果没有边界说明，用户不容易看出这是声明门禁。

    def test_probe_maps_unauthorized_and_forbidden_without_response_body(self) -> None:  # 新增代码+DirectOAuthSseProbeTest：测试段开始，验证 401/403 脱敏分类；如果没有这段，token 过期和权限问题可能被写入原始响应。
        from learning_agent.models.adapters import probe_codex_oauth_sse_payload  # 新增代码+DirectOAuthSseProbeTest：导入 SSE probe；如果没有这行，测试没有被测函数。

        unauthorized = probe_codex_oauth_sse_payload("", env=DIRECT_OAUTH_READY_ENV, http_status=401)  # 新增代码+DirectOAuthSseProbeTest：模拟 401；如果没有这行，未授权分支没有覆盖。
        forbidden = probe_codex_oauth_sse_payload("", env=DIRECT_OAUTH_READY_ENV, http_status=403)  # 新增代码+DirectOAuthSseProbeTest：模拟 403；如果没有这行，无权限分支没有覆盖。
        self.assertEqual("unavailable_unauthorized", unauthorized.status)  # 新增代码+DirectOAuthSseProbeTest：401 应归类为未授权；如果没有这行，登录过期提示会不准。
        self.assertEqual("http_401", unauthorized.message)  # 新增代码+DirectOAuthSseProbeTest：消息只含状态码；如果没有这行，错误体可能混入证据。
        self.assertEqual("unavailable_forbidden", forbidden.status)  # 新增代码+DirectOAuthSseProbeTest：403 应归类为无权限；如果没有这行，账号模型权限问题会模糊。
        self.assertEqual("http_403", forbidden.message)  # 新增代码+DirectOAuthSseProbeTest：消息只含状态码；如果没有这行，错误体可能泄露。
    # 新增代码+DirectOAuthSseProbeTest：测试段结束，test_probe_maps_unauthorized_and_forbidden_without_response_body 到此结束；如果没有边界说明，用户不容易看出它测的是脱敏错误。

    def test_probe_accepts_parseable_output_text_delta_and_safe_summary_has_no_raw_secret(self) -> None:  # 新增代码+DirectOAuthSseProbeTest：测试段开始，验证有真实 delta 时可用且摘要不含敏感原文；如果没有这段，成功和脱敏两件事没有锁住。
        from learning_agent.models.adapters import probe_codex_oauth_sse_payload  # 新增代码+DirectOAuthSseProbeTest：导入 SSE probe；如果没有这行，测试没有被测函数。

        raw_stream = "\n".join([  # 新增代码+DirectOAuthSseProbeTest：构造多行 SSE 样本；如果没有这行，无法模拟真实 stream。
            'data: {"type":"response.output_text.delta","delta":"secret-access-token-should-not-leak"}',  # 新增代码+DirectOAuthSseProbeTest：把敏感形态放进原始 delta；如果没有这行，无法证明摘要不复制原文。
            'data: {"type":"response.completed","response":{"output_text":"done"}}',  # 新增代码+DirectOAuthSseProbeTest：追加 completed 事件；如果没有这行，事件类型摘要不够完整。
            "data: [DONE]",  # 新增代码+DirectOAuthSseProbeTest：追加结束标记；如果没有这行，SSE 样本不像真实流。
        ])  # 新增代码+DirectOAuthSseProbeTest：SSE 样本拼接结束；如果没有这行，Python 表达式不完整。
        result = probe_codex_oauth_sse_payload(raw_stream, env=DIRECT_OAUTH_READY_ENV)  # 新增代码+DirectOAuthSseProbeTest：执行 probe；如果没有这行，无法得到结论。
        safe_json = json.dumps(result.to_safe_dict(), ensure_ascii=False)  # 新增代码+DirectOAuthSseProbeTest：序列化安全摘要；如果没有这行，无法扫描输出是否泄露原始 delta。
        self.assertTrue(result.available)  # 新增代码+DirectOAuthSseProbeTest：delta 应允许 fast path；如果没有这行，成功分支可能退化。
        self.assertEqual("available", result.status)  # 新增代码+DirectOAuthSseProbeTest：状态必须为 available；如果没有这行，布尔和状态可能不一致。
        self.assertIn("response.output_text.delta", result.event_types)  # 新增代码+DirectOAuthSseProbeTest：事件类型摘要应保留 delta；如果没有这行，证据缺少成功依据。
        self.assertNotIn("secret-access-token-should-not-leak", safe_json)  # 新增代码+DirectOAuthSseProbeTest：安全摘要不能包含原始文本；如果没有这行，证据文件可能泄露 token 形态。
    # 新增代码+DirectOAuthSseProbeTest：测试段结束，test_probe_accepts_parseable_output_text_delta_and_safe_summary_has_no_raw_secret 到此结束；如果没有边界说明，用户不容易看出这是成功和脱敏双门禁。

    def test_probe_rejects_unknown_payload_shape(self) -> None:  # 新增代码+DirectOAuthSseProbeTest：测试段开始，验证未知事件默认不放行；如果没有这段，远端协议漂移可能被当作成功。
        from learning_agent.models.adapters import probe_codex_oauth_sse_payload  # 新增代码+DirectOAuthSseProbeTest：导入 SSE probe；如果没有这行，测试没有被测函数。

        raw_stream = 'data: {"type":"response.created","response":{"id":"resp_unit_test"}}\n\n'  # 新增代码+DirectOAuthSseProbeTest：构造无输出的未知/启动事件；如果没有这行，未知 payload 没有样本。
        result = probe_codex_oauth_sse_payload(raw_stream, env=DIRECT_OAUTH_READY_ENV)  # 新增代码+DirectOAuthSseProbeTest：执行 probe；如果没有这行，无法得到未知结论。
        self.assertEqual("unavailable_unknown_payload", result.status)  # 新增代码+DirectOAuthSseProbeTest：未知 shape 必须拒绝；如果没有这行，fast path 会过度乐观。
        self.assertFalse(result.available)  # 新增代码+DirectOAuthSseProbeTest：未知 shape 不可用；如果没有这行，UI 可能误放行。
        self.assertEqual(("response.created",), result.event_types)  # 新增代码+DirectOAuthSseProbeTest：保留未知事件类型；如果没有这行，排查不知道协议漂到了哪里。
    # 新增代码+DirectOAuthSseProbeTest：测试段结束，test_probe_rejects_unknown_payload_shape 到此结束；如果没有边界说明，用户不容易看出这是保守默认。
# 新增代码+DirectOAuthSseProbeTest：测试类段结束，CodexOAuthStreamingProbeTests 到此结束；如果没有边界说明，用户不容易看出本文件只测 SSE probe。


if __name__ == "__main__":  # 新增代码+DirectOAuthSseProbeTest：允许直接运行测试文件；如果没有这行，手动排查时需要记住 unittest 命令。
    unittest.main()  # 新增代码+DirectOAuthSseProbeTest：启动 unittest；如果没有这行，直接 python 文件不会执行测试。
