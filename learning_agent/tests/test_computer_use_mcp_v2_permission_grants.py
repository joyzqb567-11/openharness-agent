from __future__ import annotations  # 新增代码+ClaudeCodePermissionParityTests：延迟类型注解解析；如果没有这行代码，测试导入时类型求值更容易受顺序影响。

import unittest  # 新增代码+ClaudeCodePermissionParityTests：使用标准 unittest 框架；如果没有这行代码，测试类不会被发现。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import ComputerUseMcpV2Context, dispatch_computer_use_mcp_v2_tool  # 新增代码+ClaudeCodePermissionParityTests：导入真实 runtime 和上下文；如果没有这行代码，权限测试无法覆盖分发入口。


class ComputerUseMcpV2PermissionGrantTests(unittest.TestCase):  # 新增代码+ClaudeCodePermissionParityTests：类段开始，验证 ClaudeCode 权限模型字段；如果没有这段类，app allowlist 和 grant flags 没有自动化保护。
    def test_request_access_saves_apps_grant_flags_and_sentinel_warnings(self) -> None:  # 新增代码+ClaudeCodePermissionParityTests：函数段开始，验证授权成功时保存 ClaudeCode-compatible 状态；如果没有这段测试，权限模型可能继续只保存 applications。
        prompts: list[str] = []  # 新增代码+ClaudeCodePermissionParityTests：收集权限提示文本；如果没有这行代码，无法证明 ask_permission 收到完整上下文。
        context = ComputerUseMcpV2Context(ask_permission=lambda prompt: prompts.append(prompt) or True)  # 新增代码+ClaudeCodePermissionParityTests：创建自动同意的上下文；如果没有这行代码，request_access 无法进入授权成功路径。
        arguments = {  # 新增代码+ClaudeCodePermissionParityTests：准备 ClaudeCode 风格授权输入；如果没有这段字典，测试无法覆盖 apps/grantFlags。
            "apps": [  # 新增代码+ClaudeCodePermissionParityTests：声明 app allowlist；如果没有这一行，权限层没有目标应用。
                {"displayName": "Notepad", "bundleId": "notepad.exe"},  # 新增代码+ClaudeCodePermissionParityTests：普通应用用于验证 allowlist；如果没有这一行，普通 app 路径没有覆盖。
                {"displayName": "PowerShell", "bundleId": "powershell.exe"},  # 新增代码+ClaudeCodePermissionParityTests：shell 风险应用用于验证 sentinel；如果没有这一行，风险分类没有覆盖。
            ],  # 新增代码+ClaudeCodePermissionParityTests：app allowlist 结束；如果没有这行代码，Python 列表语法不完整。
            "grantFlags": {"clipboardRead": True, "clipboardWrite": True, "systemKeyCombos": False},  # 新增代码+ClaudeCodePermissionParityTests：声明 ClaudeCode grant flags；如果没有这一行，剪贴板授权字段没有测试。
            "reason": "需要在记事本中输入测试文本",  # 新增代码+ClaudeCodePermissionParityTests：声明授权原因；如果没有这一行，提示和状态缺少申请目的。
        }  # 新增代码+ClaudeCodePermissionParityTests：授权输入结束；如果没有这行代码，Python 字典语法不完整。
        result = dispatch_computer_use_mcp_v2_tool("request_access", arguments, context)  # 新增代码+ClaudeCodePermissionParityTests：通过真实 runtime 执行授权申请；如果没有这行代码，normalizer 和 permissions 不会一起被覆盖。
        self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodePermissionParityTests：断言授权成功；如果没有这行代码，失败结果可能被后续字段断言掩盖。
        payload = result["payload"]  # 新增代码+ClaudeCodePermissionParityTests：取出成功 payload；如果没有这行代码，字段断言会重复索引。
        self.assertEqual("Notepad", payload["allowedApps"][0]["displayName"])  # 新增代码+ClaudeCodePermissionParityTests：断言普通 app 展示名保存；如果没有这行代码，allowlist 可能丢 displayName。
        self.assertEqual("powershell.exe", payload["allowedApps"][1]["bundleId"])  # 新增代码+ClaudeCodePermissionParityTests：断言风险 app bundleId 保存；如果没有这行代码，allowlist 可能丢应用身份。
        self.assertTrue(payload["grantFlags"]["clipboardRead"])  # 新增代码+ClaudeCodePermissionParityTests：断言剪贴板读授权保存；如果没有这行代码，grantFlags 可能没有写入。
        self.assertTrue(payload["grantFlags"]["clipboardWrite"])  # 新增代码+ClaudeCodePermissionParityTests：断言剪贴板写授权保存；如果没有这行代码，grantFlags 可能没有写入。
        self.assertFalse(payload["grantFlags"]["systemKeyCombos"])  # 新增代码+ClaudeCodePermissionParityTests：断言系统组合键授权保存为 false；如果没有这行代码，危险默认值可能错误。
        self.assertEqual("shell", payload["sentinelWarnings"][0]["category"])  # 新增代码+ClaudeCodePermissionParityTests：断言 PowerShell 被标记为 shell 风险；如果没有这行代码，sentinel 分类可能失效。
        self.assertEqual(payload["allowedApps"], context.allowed_apps)  # 新增代码+ClaudeCodePermissionParityTests：断言 context 保存 allowed_apps；如果没有这行代码，多轮查询会丢状态。
        self.assertEqual(payload["grantFlags"], context.grant_flags)  # 新增代码+ClaudeCodePermissionParityTests：断言 context 保存 grant_flags；如果没有这行代码，后续 clipboard 权限无法读取。
        self.assertIn("PowerShell", prompts[0])  # 新增代码+ClaudeCodePermissionParityTests：断言权限提示包含目标应用；如果没有这行代码，用户不知道授权对象。
    # 新增代码+ClaudeCodePermissionParityTests：函数段结束，test_request_access_saves_apps_grant_flags_and_sentinel_warnings 到此结束；如果没有这个边界说明，用户不容易看出授权成功测试范围。

    def test_list_granted_applications_returns_claudecode_compatible_shape(self) -> None:  # 新增代码+ClaudeCodePermissionParityTests：函数段开始，验证授权查询返回 ClaudeCode-compatible 结构；如果没有这段测试，list_granted 可能继续只返回旧 grants。
        context = ComputerUseMcpV2Context()  # 新增代码+ClaudeCodePermissionParityTests：创建默认上下文；如果没有这行代码，测试没有状态容器。
        dispatch_computer_use_mcp_v2_tool("request_access", {"apps": [{"displayName": "Notepad", "bundleId": "notepad.exe"}], "reason": "测试授权"}, context)  # 新增代码+ClaudeCodePermissionParityTests：先写入授权状态；如果没有这行代码，查询结果为空无法验证结构。
        result = dispatch_computer_use_mcp_v2_tool("list_granted_applications", {}, context)  # 新增代码+ClaudeCodePermissionParityTests：查询授权状态；如果没有这行代码，list_granted 路径没有被覆盖。
        payload = result["payload"]  # 新增代码+ClaudeCodePermissionParityTests：取出查询 payload；如果没有这行代码，字段断言会重复索引。
        self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodePermissionParityTests：断言查询成功；如果没有这行代码，失败结果可能被误读。
        self.assertEqual("Notepad", payload["allowedApps"][0]["displayName"])  # 新增代码+ClaudeCodePermissionParityTests：断言 allowedApps 返回；如果没有这行代码，ClaudeCode-compatible 字段可能缺失。
        self.assertIn("grantFlags", payload)  # 新增代码+ClaudeCodePermissionParityTests：断言 grantFlags 返回；如果没有这行代码，权限开关可能无法查询。
        self.assertIn("grants", payload)  # 新增代码+ClaudeCodePermissionParityTests：断言旧 grants 兼容返回；如果没有这行代码，历史调用方可能被破坏。
    # 新增代码+ClaudeCodePermissionParityTests：函数段结束，test_list_granted_applications_returns_claudecode_compatible_shape 到此结束；如果没有这个边界说明，用户不容易看出授权查询测试范围。

    def test_denied_access_records_denied_apps(self) -> None:  # 新增代码+ClaudeCodePermissionParityTests：函数段开始，验证用户拒绝时记录 deniedApps；如果没有这段测试，拒绝审计会丢目标应用。
        context = ComputerUseMcpV2Context(ask_permission=lambda _prompt: False)  # 新增代码+ClaudeCodePermissionParityTests：创建自动拒绝上下文；如果没有这行代码，无法覆盖拒绝路径。
        result = dispatch_computer_use_mcp_v2_tool("request_access", {"apps": [{"displayName": "PowerShell", "bundleId": "powershell.exe"}], "reason": "测试拒绝"}, context)  # 新增代码+ClaudeCodePermissionParityTests：执行被拒绝的授权申请；如果没有这行代码，deniedApps 无法写入。
        self.assertFalse(result["ok"], result)  # 新增代码+ClaudeCodePermissionParityTests：断言授权被拒绝；如果没有这行代码，拒绝路径可能误成功。
        self.assertEqual("PowerShell", context.denied_apps[0]["displayName"])  # 新增代码+ClaudeCodePermissionParityTests：断言拒绝应用被保存；如果没有这行代码，用户拒绝记录会丢目标。
        self.assertEqual("permission_denied", result["error_class"])  # 新增代码+ClaudeCodePermissionParityTests：断言错误类别稳定；如果没有这行代码，调用方无法按权限拒绝恢复。
    # 新增代码+ClaudeCodePermissionParityTests：函数段结束，test_denied_access_records_denied_apps 到此结束；如果没有这个边界说明，用户不容易看出拒绝测试范围。


if __name__ == "__main__":  # 新增代码+ClaudeCodePermissionParityTests：允许直接运行本测试文件；如果没有这行代码，手动调试不方便。
    unittest.main()  # 新增代码+ClaudeCodePermissionParityTests：启动 unittest；如果没有这行代码，直接运行不会执行测试。
