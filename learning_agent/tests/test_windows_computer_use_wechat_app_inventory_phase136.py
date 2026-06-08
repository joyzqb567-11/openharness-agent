"""微信普通应用发现与启动链路回归测试。"""  # 新增代码+WeChatLaunchRegression：说明本文件专门验证微信这种普通用户应用；如果没有这一行，后续读测试的人会不知道本文件覆盖哪个真实问题。
from __future__ import annotations  # 新增代码+WeChatLaunchRegression：启用延迟类型注解；如果没有这一行，类型注解在旧执行路径里可能增加导入顺序风险。

import tempfile  # 新增代码+WeChatLaunchRegression：创建隔离工作区测试主循环提示；如果没有这一行，测试可能污染真实 learning_agent 目录。
import unittest  # 新增代码+WeChatLaunchRegression：使用标准库测试框架；如果没有这一行，本文件无法定义可运行的回归测试。
from pathlib import Path  # 新增代码+WeChatLaunchRegression：把临时目录转成 Path；如果没有这一行，LearningAgent 初始化参数类型会不清楚。

from learning_agent.computer_use.windows_app_inventory import build_windows_app_inventory, query_windows_app_inventory  # 新增代码+WeChatLaunchRegression：导入应用清单入口验证候选融合；如果没有这一行，测试无法证明 discover 层能找到微信。
from learning_agent.computer_use.windows_launch_resolver import resolve_windows_launch_plan  # 新增代码+WeChatLaunchRegression：导入启动 resolver 验证别名能生成真实启动计划；如果没有这一行，测试只能覆盖发现不能覆盖启动。
from learning_agent.core.agent import LearningAgent  # 新增代码+WeChatLaunchRegression：导入主 Agent 以检查 full 模式主循环约束；如果没有这一行，测试无法覆盖模型提示层。
from learning_agent.core.messages import ModelMessage  # 新增代码+WeChatLaunchRegression：导入假模型返回消息结构；如果没有这一行，测试无法构造 LearningAgent 依赖。
from learning_agent.tests.test_core_run_loop import ToolCallingFakeModel  # 新增代码+WeChatLaunchRegression：复用现有假模型；如果没有这一行，测试会重复造轮子并增加维护成本。


def _wechat_candidates() -> list[dict[str, object]]:  # 新增代码+WeChatLaunchRegression：函数段开始，构造真实 Windows 上微信常见的双来源候选；如果没有这段函数，每个测试都要重复候选数据且容易写错。函数到 return 结束。
    return [  # 新增代码+WeChatLaunchRegression：返回开始菜单和 Get-StartApps 两个来源；如果没有这一行，测试无法模拟真实机器上的候选融合。
        {"display_name": "微信", "app_name": "微信", "launch_id": "微信.lnk", "launch_kind": "shortcut", "source": "start_menu", "installed_app_verified": True},  # 新增代码+WeChatLaunchRegression：模拟开始菜单快捷方式；如果没有这一行，resolver 无法验证 shortcut 后端优先级。
        {"display_name": "微信", "app_name": "微信", "launch_id": r"{6D809377-6AF0-444B-8957-A3773F02200E}\Tencent\Weixin\Weixin.exe", "launch_kind": "appx", "source": "appx_package", "installed_app_verified": True},  # 新增代码+WeChatLaunchRegression：模拟 Get-StartApps 暴露的 Weixin.exe 身份；如果没有这一行，测试无法证明英文别名应从真实系统身份合并出来。
    ]  # 新增代码+WeChatLaunchRegression：候选列表结束；如果没有这一行，Python 语法无法闭合。
# 新增代码+WeChatLaunchRegression：函数段结束，_wechat_candidates 到此结束；如果没有这个边界说明，用户不容易看出候选构造范围。


class WindowsComputerUseWeChatInventoryPhase136Tests(unittest.TestCase):  # 新增代码+WeChatLaunchRegression：类段开始，集中验证微信普通应用链路；如果没有这个类，unittest 无法自动发现这些回归测试。
    def test_inventory_merges_weixin_identity_into_wechat_shortcut_candidate(self) -> None:  # 新增代码+WeChatLaunchRegression：函数段开始，验证同名多来源会保留快捷方式并合并英文别名；如果没有这段测试，微信英文输入回归会再次漏掉。
        inventory = build_windows_app_inventory(candidates=_wechat_candidates(), include_common=False)  # 新增代码+WeChatLaunchRegression：用注入候选构建清单；如果没有这一行，测试会依赖当前电脑真实安装状态而不稳定。
        self.assertEqual(1, len(inventory))  # 新增代码+WeChatLaunchRegression：确认同名微信被去重成一个产品；如果没有这一行，多来源重复会污染模型工具清单。
        self.assertEqual("shortcut", inventory[0]["launch_kind"])  # 新增代码+WeChatLaunchRegression：确认保留更适合真实启动的开始菜单后端；如果没有这一行，低优先级来源可能覆盖可启动入口。
        self.assertIn("weixin", inventory[0].get("aliases", ()))  # 新增代码+WeChatLaunchRegression：确认从 Weixin.exe 提取英文别名；如果没有这一行，用户输入 weixin 会找不到微信。
        self.assertIn("wechat", inventory[0].get("aliases", ()))  # 新增代码+WeChatLaunchRegression：确认补齐用户更常用的英文别名；如果没有这一行，用户输入 wechat 会找不到微信。
    # 新增代码+WeChatLaunchRegression：函数段结束，test_inventory_merges_weixin_identity_into_wechat_shortcut_candidate 到此结束；如果没有这个边界说明，用户不容易看出断言范围。

    def test_query_and_resolver_accept_wechat_english_aliases(self) -> None:  # 新增代码+WeChatLaunchRegression：函数段开始，验证 discover 查询和 launch resolver 都接受英文别名；如果没有这段测试，发现层和启动层可能只修一半。
        for alias in ("wechat", "weixin"):  # 新增代码+WeChatLaunchRegression：遍历两个真实用户可能输入的英文叫法；如果没有这一行，测试只覆盖一个入口会留下盲区。
            query_result = query_windows_app_inventory(query=alias, candidates=_wechat_candidates(), include_common=False)  # 新增代码+WeChatLaunchRegression：用 alias 查询统一清单；如果没有这一行，discover 是否能找到微信没有证据。
            self.assertEqual("微信", query_result["candidates"][0]["display_name"])  # 新增代码+WeChatLaunchRegression：确认 alias 查询返回微信；如果没有这一行，模型会拿不到候选。
            launch_plan = resolve_windows_launch_plan(alias, candidates=_wechat_candidates())  # 新增代码+WeChatLaunchRegression：用 alias 解析启动计划；如果没有这一行，测试无法证明 launch_app 可执行。
            self.assertTrue(launch_plan["safe_to_launch"])  # 新增代码+WeChatLaunchRegression：确认普通微信不会被误当高风险工具拒绝；如果没有这一行，安全策略错误不会暴露。
            self.assertEqual("微信", launch_plan["display_name"])  # 新增代码+WeChatLaunchRegression：确认 resolver 选中的还是微信；如果没有这一行，别名可能误命中其他应用。
            self.assertEqual("start_menu_shortcut", launch_plan["launch_backend"])  # 新增代码+WeChatLaunchRegression：确认走真实开始菜单快捷方式后端；如果没有这一行，resolver 可能退回错误的 exe 猜测。
            self.assertEqual("微信.lnk", launch_plan["shortcut_id"])  # 新增代码+WeChatLaunchRegression：确认启动目标是可定位的快捷方式；如果没有这一行，后端没有稳定目标。
    # 新增代码+WeChatLaunchRegression：函数段结束，test_query_and_resolver_accept_wechat_english_aliases 到此结束；如果没有这个边界说明，用户不容易看出 discover/resolver 联合断言范围。

    def test_full_model_loop_harness_requires_launch_after_unique_discover_candidate(self) -> None:  # 新增代码+WeChatLaunchRegression：函数段开始，验证 full 模式提示不会让模型只 discover 后结束；如果没有这段测试，真实终端可能继续出现“找到了但不打开”的问题。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+WeChatLaunchRegression：创建临时工作区；如果没有这一行，测试可能写入真实项目运行记忆。
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="ok")]), workspace=Path(temp_dir), ask_permission=lambda _action: True, debug_enabled=False)  # 新增代码+WeChatLaunchRegression：构造最小 Agent；如果没有这一行，无法读取主循环 harness 文本。
            agent.loaded_tool_names.update({"computer_use", "computer_observe", "computer_discover", "computer_action"})  # 修改代码+WeChatLaunchRegression：模拟 full 模式已经加载完整桌面工具包；如果没有这一行，harness 会按半加载状态返回空字符串。
            agent.desktop_task_context = {"active": True, "requires_gui_actions": True, "target_app_hint": "微信", "task_goal": "open_local_app"}  # 新增代码+WeChatLaunchRegression：模拟用户要打开本机微信；如果没有这一行，harness 不会进入目标应用约束场景。
            harness = agent._build_computer_use_full_model_loop_harness_message("请打开本机电脑微信")  # 新增代码+WeChatLaunchRegression：生成 full 模式主循环提示；如果没有这一行，测试没有可检查对象。
        self.assertIn("discover 返回唯一高置信候选", harness)  # 新增代码+WeChatLaunchRegression：确认提示明确处理 discover 后的唯一候选；如果没有这一行，模型可能把发现当成最终结果。
        self.assertIn("下一轮必须使用该候选", harness)  # 新增代码+WeChatLaunchRegression：确认提示强制下一步 launch_app；如果没有这一行，模型可能继续只做观察或直接结束。
        self.assertIn("必须逐字复制 app_name", harness)  # 新增代码+WeChatLaunchRegression：确认提示阻止模型给微信这类中文 app_name 追加脏后缀；如果没有这一行，真实启动日志可能继续出现“微信.pdf???”。
    # 新增代码+WeChatLaunchRegression：函数段结束，test_full_model_loop_harness_requires_launch_after_unique_discover_candidate 到此结束；如果没有这个边界说明，用户不容易看出主循环提示断言范围。
# 新增代码+WeChatLaunchRegression：类段结束，WindowsComputerUseWeChatInventoryPhase136Tests 到此结束；如果没有这个边界说明，用户不容易看出测试类范围。


if __name__ == "__main__":  # 新增代码+WeChatLaunchRegression：允许直接运行本测试文件；如果没有这一行，用户学习时无法单独执行文件。
    unittest.main()  # 新增代码+WeChatLaunchRegression：启动 unittest；如果没有这一行，直接运行文件不会执行任何测试。
