from __future__ import annotations  # 新增代码+PermissionApprovalPrompt：延迟解析类型注解；如果没有这行代码，测试里的现代注解可能在导入时提前求值。

import unittest  # 新增代码+PermissionApprovalPrompt：导入 unittest 测试框架；如果没有这行代码，本文件无法声明测试用例。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.approval_prompt import build_computer_use_approval_prompt  # 新增代码+PermissionApprovalPrompt：导入待测审批提示构造器；如果没有这行代码，测试无法锁定 prompt 内容。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.permissions import request_access  # 新增代码+PermissionApprovalPrompt：导入 request_access；如果没有这行代码，测试无法验证拒绝路径 payload。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.types import ComputerUseMcpV2Context  # 新增代码+PermissionApprovalPrompt：导入 v2 上下文；如果没有这行代码，测试无法注入权限回调。


class ComputerUsePermissionApprovalPromptTests(unittest.TestCase):  # 新增代码+PermissionApprovalPrompt：类段开始，集中验证 Computer Use 审批提示；如果没有这段类，权限 UI 语义容易回归。
    def test_prompt_contains_apps_grant_flags_warnings_and_reason(self) -> None:  # 新增代码+PermissionApprovalPrompt：函数段开始，验证 prompt 包含关键授权信息；如果没有这段测试，用户可能看不到完整授权范围。
        prompt = build_computer_use_approval_prompt(  # 新增代码+PermissionApprovalPrompt：构造审批提示；如果没有这行代码，测试没有目标文本可检查。
            apps=[{"displayName": "PowerShell", "bundleId": "powershell.exe"}],  # 新增代码+PermissionApprovalPrompt：传入 ClaudeCode 风格 app 对象；如果没有这行代码，prompt 不会覆盖 apps 字段。
            applications=["PowerShell"],  # 新增代码+PermissionApprovalPrompt：传入旧 applications 兼容字段；如果没有这行代码，旧调用方可见信息不会被测试覆盖。
            grant_flags={"clipboardRead": True, "clipboardWrite": False},  # 新增代码+PermissionApprovalPrompt：传入细粒度授权开关；如果没有这行代码，剪贴板权限可见性不会被测试覆盖。
            sentinel_warnings=[{"category": "shell", "displayName": "PowerShell", "bundleId": "powershell.exe"}],  # 新增代码+PermissionApprovalPrompt：传入高风险应用提示；如果没有这行代码，sentinel warnings 不会出现在测试里。
            reason="需要验证安全拒绝路径",  # 新增代码+PermissionApprovalPrompt：传入申请原因；如果没有这行代码，用户为什么授权不会被测试覆盖。
        )  # 新增代码+PermissionApprovalPrompt：结束 prompt 构造调用；如果没有这行代码，Python 调用语法不完整。

        self.assertIn("PowerShell", prompt)  # 新增代码+PermissionApprovalPrompt：确认应用名可见；如果没有这行断言，用户可能不知道要授权哪个应用。
        self.assertIn("clipboardRead", prompt)  # 新增代码+PermissionApprovalPrompt：确认读取授权开关可见；如果没有这行断言，剪贴板读权限可能被隐藏。
        self.assertIn("clipboardWrite", prompt)  # 新增代码+PermissionApprovalPrompt：确认写入授权开关可见；如果没有这行断言，剪贴板写权限可能被隐藏。
        self.assertIn("shell", prompt)  # 新增代码+PermissionApprovalPrompt：确认 shell 风险分类可见；如果没有这行断言，高风险提示可能丢失。
        self.assertIn("需要验证安全拒绝路径", prompt)  # 新增代码+PermissionApprovalPrompt：确认申请原因可见；如果没有这行断言，用户不知道为什么要授权。
    # 新增代码+PermissionApprovalPrompt：函数段结束，test_prompt_contains_apps_grant_flags_warnings_and_reason 到此结束；如果没有这个边界说明，用户不容易看出 prompt 内容测试范围。

    def test_request_access_denied_result_keeps_denied_payload(self) -> None:  # 新增代码+PermissionApprovalPrompt：函数段开始，验证拒绝路径保留 denied payload；如果没有这段测试，用户拒绝后的审计信息可能丢失。
        prompts: list[str] = []  # 新增代码+PermissionApprovalPrompt：记录 ask_permission 收到的提示；如果没有这行代码，测试无法确认 request_access 使用了新 prompt。
        context = ComputerUseMcpV2Context(ask_permission=lambda prompt: prompts.append(prompt) or False)  # 新增代码+PermissionApprovalPrompt：创建总是拒绝的上下文；如果没有这行代码，拒绝路径不会被触发。

        result = request_access(  # 新增代码+PermissionApprovalPrompt：执行授权申请；如果没有这行代码，测试无法得到拒绝结果。
            context,  # 新增代码+PermissionApprovalPrompt：传入带拒绝回调的上下文；如果没有这行代码，request_access 没有状态容器。
            {  # 新增代码+PermissionApprovalPrompt：开始传入 ClaudeCode 风格授权参数；如果没有这行代码，测试无法覆盖 apps/grantFlags/reason。
                "apps": [{"displayName": "PowerShell", "bundleId": "powershell.exe"}],  # 新增代码+PermissionApprovalPrompt：申请控制 PowerShell；如果没有这行代码，风险提示和 deniedApps 没有目标。
                "grantFlags": {"clipboardRead": True},  # 新增代码+PermissionApprovalPrompt：申请剪贴板读取授权；如果没有这行代码，grantFlags 不会进入 prompt。
                "reason": "测试拒绝",  # 新增代码+PermissionApprovalPrompt：传入拒绝测试原因；如果没有这行代码，拒绝 payload 的 reason 可能为空。
            },  # 新增代码+PermissionApprovalPrompt：结束授权参数字典；如果没有这行代码，Python 字典语法不完整。
        )  # 新增代码+PermissionApprovalPrompt：结束 request_access 调用；如果没有这行代码，Python 调用语法不完整。

        self.assertFalse(result["ok"])  # 新增代码+PermissionApprovalPrompt：确认授权申请被拒绝；如果没有这行断言，拒绝回调失效也可能被忽略。
        self.assertEqual(result["error_class"], "permission_denied")  # 新增代码+PermissionApprovalPrompt：确认错误类别是权限拒绝；如果没有这行断言，模型无法稳定处理用户拒绝。
        self.assertEqual(result["payload"]["deniedApps"][0]["displayName"], "PowerShell")  # 新增代码+PermissionApprovalPrompt：确认拒绝 payload 保留目标应用；如果没有这行断言，审计不知道用户拒绝了什么。
        self.assertIn("PowerShell", prompts[0])  # 新增代码+PermissionApprovalPrompt：确认提示文本包含应用名；如果没有这行断言，新 prompt 可能没有进入 request_access。
        self.assertIn("clipboardRead", prompts[0])  # 新增代码+PermissionApprovalPrompt：确认提示文本包含 grantFlags；如果没有这行断言，细粒度授权范围可能不可见。
    # 新增代码+PermissionApprovalPrompt：函数段结束，test_request_access_denied_result_keeps_denied_payload 到此结束；如果没有这个边界说明，用户不容易看出拒绝路径测试范围。


if __name__ == "__main__":  # 新增代码+PermissionApprovalPrompt：允许直接运行本测试文件；如果没有这行代码，手动调试时需要额外 unittest 参数。
    unittest.main()  # 新增代码+PermissionApprovalPrompt：启动 unittest 主程序；如果没有这行代码，直接运行文件不会执行测试。
