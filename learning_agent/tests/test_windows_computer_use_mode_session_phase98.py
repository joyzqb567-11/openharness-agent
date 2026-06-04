import json  # 新增代码+Phase98UniversalComputerUseMode：导入 JSON 用来检查状态文件不会泄露敏感原文；如果没有这行代码，就无法验证隐私边界。
import tempfile  # 新增代码+Phase98UniversalComputerUseMode：导入临时目录用来隔离测试状态；如果没有这行代码，测试会污染真实 memory 目录。
import unittest  # 新增代码+Phase98UniversalComputerUseMode：导入 unittest 以符合项目现有测试风格；如果没有这行代码，标准测试发现机制找不到测试类。
from pathlib import Path  # 新增代码+Phase98UniversalComputerUseMode：导入 Path 统一处理 Windows 路径；如果没有这行代码，路径拼接会变脆弱。

from learning_agent.computer_use.mode_session import (  # 新增代码+Phase98UniversalComputerUseMode：导入待实现的模式 session API；如果没有这行代码，测试无法锁定公开接口。
    PHASE98_COMPUTER_USE_MODE_READY,  # 新增代码+Phase98UniversalComputerUseMode：导入 ready marker；如果没有这行代码，终端验收没有稳定锚点。
    PHASE98_COMPUTER_USE_MODE_OK,  # 新增代码+Phase98UniversalComputerUseMode：导入 OK token；如果没有这行代码，测试无法确认合同输出。
    ComputerUseModeSessionStore,  # 新增代码+Phase98UniversalComputerUseMode：导入模式 session store；如果没有这行代码，测试无法创建模式状态。
)  # 新增代码+Phase98UniversalComputerUseMode：关闭模式 session API 导入代码块；如果没有这行代码，Python 无法正确结束多行导入，测试文件会在语法或接口边界上变得不清晰。


class ComputerUseModeSessionPhase98Tests(unittest.TestCase):  # 新增代码+Phase98UniversalComputerUseMode：类段开始，集中验证 /computer use 的权限模式状态；如果没有这个类，Phase98 的核心状态没有门禁。
    def test_normal_mode_does_not_require_per_app_allowlist(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证普通模式不依赖应用白名单；如果没有这段测试，架构可能滑回 per-app allowlist。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，不同测试会共享状态文件。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，测试没有状态操作对象。
            result = store.open_mode(mode="normal", reason="打开 computer use，控制普通 Windows 应用")  # 新增代码+Phase98UniversalComputerUseMode：打开普通模式；如果没有这行代码，无法验证 normal 语义。
            status = store.status()  # 新增代码+Phase98UniversalComputerUseMode：读取当前状态；如果没有这行代码，无法确认状态已落盘。
        self.assertTrue(result["opened"])  # 新增代码+Phase98UniversalComputerUseMode：断言模式已打开；如果没有这行代码，失败结果可能被忽略。
        self.assertEqual(status["mode"], "normal")  # 新增代码+Phase98UniversalComputerUseMode：断言当前模式是 normal；如果没有这行代码，observe/full 混淆不会被发现。
        self.assertFalse(status["per_app_allowlist_required"])  # 新增代码+Phase98UniversalComputerUseMode：断言不需要应用白名单；如果没有这行代码，用户纠偏点没有自动化保护。
        self.assertTrue(status["ordinary_apps_allowed_by_risk_policy"])  # 新增代码+Phase98UniversalComputerUseMode：断言普通应用由风险策略放行；如果没有这行代码，normal mode 的产品意义不明确。
        self.assertIn("click", status["allowed_action_classes"])  # 新增代码+Phase98UniversalComputerUseMode：断言普通点击被允许；如果没有这行代码，普通控制模式可能只剩观察。
        self.assertIn("type_text", status["allowed_action_classes"])  # 新增代码+Phase98UniversalComputerUseMode：断言普通输入被允许；如果没有这行代码，普通应用无法被真实操作。
        self.assertEqual(status["marker"], PHASE98_COMPUTER_USE_MODE_READY)  # 新增代码+Phase98UniversalComputerUseMode：断言 marker 稳定；如果没有这行代码，真实终端验收会漂移。
        self.assertEqual(status["ok_token"], PHASE98_COMPUTER_USE_MODE_OK)  # 新增代码+Phase98UniversalComputerUseMode：断言 OK token 稳定；如果没有这行代码，场景断言没有成功锚点。

    def test_permissions_include_task3_rendering_fields(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 permissions 提供 Task3 渲染需要的字段；如果没有这段测试，终端渲染可能缺关键安全说明。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，权限摘要测试会污染真实 session。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，测试无法读取 permissions。
            store.open_mode(mode="normal", reason="准备展示权限摘要")  # 新增代码+Phase98UniversalComputerUseMode：打开 normal 模式；如果没有这行代码，permissions 没有活动状态可摘要。
            permissions = store.permissions()  # 新增代码+Phase98UniversalComputerUseMode：读取权限摘要；如果没有这行代码，测试无法锁定 Task3 API 字段。
        self.assertTrue(permissions["high_risk_requires_confirmation"])  # 新增代码+Phase98UniversalComputerUseMode：断言高风险需要确认；如果没有这行代码，Task3 可能漏显示 full 安全边界。
        self.assertFalse(permissions["per_app_allowlist_required"])  # 新增代码+Phase98UniversalComputerUseMode：断言不需要应用白名单；如果没有这行代码，渲染层可能误提示用户配置白名单。
        self.assertTrue(permissions["dangerous_target_terms_hidden"])  # 新增代码+Phase98UniversalComputerUseMode：断言危险关键词不外泄；如果没有这行代码，渲染层可能暴露内部拦截词表。
        self.assertEqual(permissions["mode"], "normal")  # 新增代码+Phase98UniversalComputerUseMode：断言权限摘要包含模式；如果没有这行代码，Task3 无法显示当前模式。
        self.assertFalse(permissions["full_mode"])  # 新增代码+Phase98UniversalComputerUseMode：断言权限摘要包含 full 标记；如果没有这行代码，Task3 无法显示高风险是否开启。
        self.assertIn("click", permissions["allowed_action_classes"])  # 新增代码+Phase98UniversalComputerUseMode：断言权限摘要包含允许动作；如果没有这行代码，Task3 无法列出可用动作。

    def test_request_full_mode_returns_non_dispatching_confirmation_shape(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 request_full_mode 不派发也不打开；如果没有这段测试，请求阶段可能被误当成已授权。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，pending token 会污染其它测试。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，测试无法请求 full mode。
            request = store.request_full_mode(reason="用户请求 full mode")  # 新增代码+Phase98UniversalComputerUseMode：请求 full mode token；如果没有这行代码，返回结构没有样本。
        self.assertFalse(request["opened"])  # 新增代码+Phase98UniversalComputerUseMode：断言请求阶段没有打开模式；如果没有这行代码，Task3 可能误判已开启。
        self.assertFalse(request["full_mode"])  # 新增代码+Phase98UniversalComputerUseMode：断言请求阶段没有 full 权限；如果没有这行代码，二次确认边界会变模糊。
        self.assertEqual(request["low_level_event_count"], 0)  # 新增代码+Phase98UniversalComputerUseMode：断言请求阶段没有低层事件；如果没有这行代码，安全请求可能被误解为真实操作。
        self.assertTrue(request["strong_confirmation_required"])  # 新增代码+Phase98UniversalComputerUseMode：断言需要强确认；如果没有这行代码，渲染层不会提示用户二次确认。
        self.assertTrue(request["confirmation_token"].startswith("FULL-"))  # 新增代码+Phase98UniversalComputerUseMode：断言返回确认 token；如果没有这行代码，用户无法继续 confirm 流程。

    def test_status_without_state_is_clear_off_state(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证无状态时是清晰 off 状态；如果没有这段测试，首次启动可能被误当成 stopped 或 expired。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建空目录；如果没有这行代码，测试无法模拟没有 current.json 的首次启动。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，测试无法读取 status。
            status = store.status()  # 新增代码+Phase98UniversalComputerUseMode：读取无状态 status；如果没有这行代码，默认 off 合同没有样本。
        self.assertEqual(status["mode"], "off")  # 新增代码+Phase98UniversalComputerUseMode：断言默认模式是 off；如果没有这行代码，首次启动语义可能不清楚。
        self.assertFalse(status["opened"])  # 新增代码+Phase98UniversalComputerUseMode：断言默认没有打开；如果没有这行代码，渲染层可能误显示可操作。
        self.assertFalse(status["stopped"])  # 新增代码+Phase98UniversalComputerUseMode：断言默认不是用户急停；如果没有这行代码，首次启动会和 stop 混淆。
        self.assertFalse(status["expired"])  # 新增代码+Phase98UniversalComputerUseMode：断言默认不是过期；如果没有这行代码，首次启动会和 TTL 到期混淆。
        self.assertFalse(status["full_mode"])  # 新增代码+Phase98UniversalComputerUseMode：断言默认没有 full 权限；如果没有这行代码，安全状态可能误报。
        self.assertEqual(status["allowed_action_classes"], [])  # 新增代码+Phase98UniversalComputerUseMode：断言默认没有允许动作；如果没有这行代码，无状态可能被误放行动作。
        self.assertFalse(status["per_app_allowlist_required"])  # 新增代码+Phase98UniversalComputerUseMode：断言默认不要求应用白名单；如果没有这行代码，用户可能看到错误配置提示。
        self.assertFalse(status["ordinary_apps_allowed_by_risk_policy"])  # 新增代码+Phase98UniversalComputerUseMode：断言默认不放行普通应用；如果没有这行代码，off 状态可能被误认为 normal。

    def test_observe_mode_blocks_write_actions(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证观察模式零写动作；如果没有这段测试，observe 可能误发送低层输入。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，状态会污染其它测试。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，无法打开 observe mode。
            store.open_mode(mode="observe", reason="只观察当前桌面")  # 新增代码+Phase98UniversalComputerUseMode：打开观察模式；如果没有这行代码，后续权限判断没有来源。
            decision = store.evaluate_action({"process_name": "notepad.exe"}, "type_text")  # 新增代码+Phase98UniversalComputerUseMode：评估写文本动作；如果没有这行代码，observe 拒绝没有证据。
        self.assertFalse(decision["allowed"])  # 新增代码+Phase98UniversalComputerUseMode：断言写动作被拒绝；如果没有这行代码，观察模式可能变成写模式。
        self.assertEqual(decision["decision"], "observe_mode_blocks_write_action")  # 新增代码+Phase98UniversalComputerUseMode：断言原因码稳定；如果没有这行代码，错误处理不可审计。
        self.assertEqual(decision["low_level_event_count"], 0)  # 新增代码+Phase98UniversalComputerUseMode：断言零低层事件；如果没有这行代码，拒绝后仍可能触发输入。

    def test_stop_sets_abort_and_blocks_later_actions(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 stop 会阻断后续动作；如果没有这段测试，急停可能只是显示文字。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，stop 状态会污染真实环境。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，无法打开和停止 session。
            store.open_mode(mode="normal", reason="准备控制普通应用")  # 新增代码+Phase98UniversalComputerUseMode：先打开普通模式；如果没有这行代码，stop 无法证明从活动态变为停止态。
            stop = store.stop(reason="用户输入 /computer stop")  # 新增代码+Phase98UniversalComputerUseMode：执行停止；如果没有这行代码，后续动作不会被阻断。
            status = store.status()  # 新增代码+Phase98UniversalComputerUseMode：读取停止后的持久化状态；如果没有这行代码，测试无法确认 current.json 真的变成 stopped 模式。
            decision = store.evaluate_action({"process_name": "notepad.exe"}, "click")  # 新增代码+Phase98UniversalComputerUseMode：停止后再评估点击；如果没有这行代码，无法证明停止生效。
        self.assertTrue(stop["stopped"])  # 新增代码+Phase98UniversalComputerUseMode：断言 stop 已记录；如果没有这行代码，停止失败可能被忽略。
        self.assertEqual(status["mode"], "stopped")  # 新增代码+Phase98UniversalComputerUseMode：断言 stop 会持久化 stopped 模式；如果没有这行代码，状态页可能仍误显示 normal。
        self.assertFalse(decision["allowed"])  # 新增代码+Phase98UniversalComputerUseMode：断言后续动作被拒绝；如果没有这行代码，stop 不能保护真实桌面。
        self.assertEqual(decision["decision"], "computer_use_stopped")  # 新增代码+Phase98UniversalComputerUseMode：断言稳定原因码；如果没有这行代码，用户不知道为什么被阻断。
        self.assertEqual(decision["low_level_event_count"], 0)  # 新增代码+Phase98UniversalComputerUseMode：断言没有低层事件；如果没有这行代码，急停可能只是事后报告。

    def test_evaluate_action_uses_stable_task3_decision_strings(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证动作评估原因码和计划一致；如果没有这段测试，Task3/99 可能出现原因码漂移。
        clock = {"now": 2000.0}  # 新增代码+Phase98UniversalComputerUseMode：用可变时钟模拟 TTL；如果没有这行代码，过期原因码测试需要真实等待。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，动作评估状态会污染其它测试。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir), now_func=lambda: clock["now"])  # 新增代码+Phase98UniversalComputerUseMode：注入测试时钟；如果没有这行代码，无法稳定触发过期。
            store.open_mode(mode="normal", reason="准备验证允许原因码", ttl_seconds=10)  # 新增代码+Phase98UniversalComputerUseMode：打开短 TTL normal；如果没有这行代码，动作评估没有活动模式。
            allowed = store.evaluate_action({"process_name": "notepad.exe"}, "click")  # 新增代码+Phase98UniversalComputerUseMode：评估普通允许动作；如果没有这行代码，allowed 原因码没有样本。
            dangerous = store.evaluate_action({"process_name": "powershell.exe"}, "click")  # 新增代码+Phase98UniversalComputerUseMode：评估危险目标动作；如果没有这行代码，危险目标原因码没有样本。
            clock["now"] = 2011.0  # 新增代码+Phase98UniversalComputerUseMode：推进到 TTL 过期后；如果没有这行代码，过期路径不会触发。
            expired = store.evaluate_action({"process_name": "notepad.exe"}, "click")  # 新增代码+Phase98UniversalComputerUseMode：评估过期后的动作；如果没有这行代码，mode_expired 原因码没有样本。
        self.assertEqual(allowed["decision"], "allowed_by_computer_use_mode")  # 新增代码+Phase98UniversalComputerUseMode：断言允许原因码稳定；如果没有这行代码，Task3 可能显示旧原因码。
        self.assertEqual(dangerous["decision"], "dangerous_target_blocked")  # 新增代码+Phase98UniversalComputerUseMode：断言危险目标原因码稳定；如果没有这行代码，Task3 可能显示旧原因码。
        self.assertEqual(expired["decision"], "mode_expired")  # 新增代码+Phase98UniversalComputerUseMode：断言过期原因码稳定；如果没有这行代码，Task3 可能显示旧原因码。

    def test_required_dangerous_target_terms_block_identity_fields(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 Task2 要求的危险概念会拦截身份字段；如果没有这段测试，最终规格可能再次漏掉通用词。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，危险目标测试会污染真实 session。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，测试无法打开 normal 模式。
            store.open_mode(mode="normal", reason="验证危险目标身份字段拦截")  # 新增代码+Phase98UniversalComputerUseMode：打开 normal 模式；如果没有这行代码，动作评估会处于 off 状态。
            terminal = store.evaluate_action({"process_name": "terminal"}, "click")  # 新增代码+Phase98UniversalComputerUseMode：用 process_name 覆盖 terminal；如果没有这行代码，终端通用词漏检不会被发现。
            password = store.evaluate_action({"title_preview": "password"}, "click")  # 新增代码+Phase98UniversalComputerUseMode：用 title_preview 覆盖 password；如果没有这行代码，密码通用词漏检不会被发现。
            token = store.evaluate_action({"title_preview": "token"}, "click")  # 新增代码+Phase98UniversalComputerUseMode：用 title_preview 覆盖 token；如果没有这行代码，令牌通用词漏检不会被发现。
        self.assertFalse(terminal["allowed"])  # 新增代码+Phase98UniversalComputerUseMode：断言 terminal 被拒绝；如果没有这行代码，终端窗口可能被 normal 模式误操作。
        self.assertEqual(terminal["decision"], "dangerous_target_blocked")  # 新增代码+Phase98UniversalComputerUseMode：断言 terminal 使用稳定危险目标原因码；如果没有这行代码，Task3 显示会漂移。
        self.assertEqual(terminal["low_level_event_count"], 0)  # 新增代码+Phase98UniversalComputerUseMode：断言 terminal 拒绝零低层事件；如果没有这行代码，拒绝后仍可能触发输入。
        self.assertFalse(password["allowed"])  # 新增代码+Phase98UniversalComputerUseMode：断言 password 被拒绝；如果没有这行代码，密码窗口可能被 normal 模式误操作。
        self.assertEqual(password["decision"], "dangerous_target_blocked")  # 新增代码+Phase98UniversalComputerUseMode：断言 password 使用稳定危险目标原因码；如果没有这行代码，Task3 显示会漂移。
        self.assertEqual(password["low_level_event_count"], 0)  # 新增代码+Phase98UniversalComputerUseMode：断言 password 拒绝零低层事件；如果没有这行代码，拒绝后仍可能触发输入。
        self.assertFalse(token["allowed"])  # 新增代码+Phase98UniversalComputerUseMode：断言 token 被拒绝；如果没有这行代码，令牌窗口可能被 normal 模式误操作。
        self.assertEqual(token["decision"], "dangerous_target_blocked")  # 新增代码+Phase98UniversalComputerUseMode：断言 token 使用稳定危险目标原因码；如果没有这行代码，Task3 显示会漂移。
        self.assertEqual(token["low_level_event_count"], 0)  # 新增代码+Phase98UniversalComputerUseMode：断言 token 拒绝零低层事件；如果没有这行代码，拒绝后仍可能触发输入。

    def test_full_mode_requires_confirmation_before_activation(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 full 不能单命令裸开；如果没有这段测试，最高风险模式会变成默认绕过。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，full token 会污染其它测试。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，无法请求 full mode。
            request = store.request_full_mode(reason="用户请求完全接管")  # 新增代码+Phase98UniversalComputerUseMode：请求 full 模式；如果没有这行代码，无法得到确认 token。
            before = store.status()  # 新增代码+Phase98UniversalComputerUseMode：确认请求后还未进入 full；如果没有这行代码，单命令裸开不会被发现。
            confirmed = store.confirm_full_mode(request["confirmation_token"], reason="用户二次确认 full mode")  # 新增代码+Phase98UniversalComputerUseMode：用 token 二次确认；如果没有这行代码，无法证明确认路径可用。
            after = store.status()  # 新增代码+Phase98UniversalComputerUseMode：读取确认后的状态；如果没有这行代码，full 激活结果不可见。
        self.assertFalse(before["full_mode"])  # 新增代码+Phase98UniversalComputerUseMode：断言请求阶段没有 full 权限；如果没有这行代码，风险说明可能被跳过。
        self.assertTrue(request["strong_confirmation_required"])  # 新增代码+Phase98UniversalComputerUseMode：断言需要强确认；如果没有这行代码，full 安全边界没有证据。
        self.assertTrue(confirmed["opened"])  # 新增代码+Phase98UniversalComputerUseMode：断言确认后打开；如果没有这行代码，full 确认路径可能坏掉。
        self.assertTrue(after["full_mode"])  # 新增代码+Phase98UniversalComputerUseMode：断言 full 标志为真；如果没有这行代码，状态页无法显示风险模式。
        self.assertLessEqual(after["ttl_seconds"], 300)  # 新增代码+Phase98UniversalComputerUseMode：断言 full TTL 不超过 5 分钟；如果没有这行代码，长期全权限风险不可控。

    def test_direct_open_full_mode_falls_back_to_normal(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证 open_mode 不能绕过二次确认直接打开 full；如果没有这段测试，高风险模式可能被普通入口误激活。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，direct full 回退测试会污染真实 session。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，测试无法调用 open_mode。
            result = store.open_mode(mode="full", reason="用户误输入直接打开 full mode")  # 新增代码+Phase98UniversalComputerUseMode：尝试直接打开 full；如果没有这行代码，无法覆盖 review 指出的绕过路径。
            status = store.status()  # 新增代码+Phase98UniversalComputerUseMode：读取落盘状态；如果没有这行代码，测试只能看到返回值而看不到持久化结果。
        self.assertEqual(result["mode"], "normal")  # 新增代码+Phase98UniversalComputerUseMode：断言直接 full 会回退 normal；如果没有这行代码，open_mode 可能继续绕过确认。
        self.assertFalse(result["full_mode"])  # 新增代码+Phase98UniversalComputerUseMode：断言返回值没有 full 权限；如果没有这行代码，调用方可能误拿高权限。
        self.assertEqual(status["mode"], "normal")  # 新增代码+Phase98UniversalComputerUseMode：断言落盘状态也是 normal；如果没有这行代码，current.json 可能暗中保存 full。
        self.assertFalse(status["full_mode"])  # 新增代码+Phase98UniversalComputerUseMode：断言状态查询没有 full 权限；如果没有这行代码，状态页可能误报已提权。

    def test_wrong_full_mode_confirmation_token_is_distinct_refusal(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证错误 token 有稳定拒绝码；如果没有这段测试，调用方无法区分输错和过期。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，pending token 会污染其它测试。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir))  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，测试无法请求 full token。
            request = store.request_full_mode(reason="用户请求 full mode")  # 新增代码+Phase98UniversalComputerUseMode：先生成正确 token；如果没有这行代码，错误 token 没有对照对象。
            decision = store.confirm_full_mode(f"{request['confirmation_token']}-BAD", reason="用户输错确认码")  # 新增代码+Phase98UniversalComputerUseMode：提交错误 token；如果没有这行代码，token mismatch 路径不会被覆盖。
            status = store.status()  # 新增代码+Phase98UniversalComputerUseMode：读取确认失败后的状态；如果没有这行代码，测试无法确认 full 没有被打开。
        self.assertFalse(decision["opened"])  # 新增代码+Phase98UniversalComputerUseMode：断言错误 token 不会打开模式；如果没有这行代码，确认绕过可能被忽略。
        self.assertEqual(decision["decision"], "full_mode_confirmation_token_mismatch")  # 新增代码+Phase98UniversalComputerUseMode：断言 mismatch 使用独立原因码；如果没有这行代码，调用方无法给出准确提示。
        self.assertEqual(decision["low_level_event_count"], 0)  # 新增代码+Phase98UniversalComputerUseMode：断言拒绝路径零低层事件；如果没有这行代码，安全拒绝可能仍触发真实输入。
        self.assertFalse(status["full_mode"])  # 新增代码+Phase98UniversalComputerUseMode：断言错误确认后仍不是 full；如果没有这行代码，失败路径可能暗中提权。

    def test_expired_full_mode_confirmation_token_is_distinct_refusal(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证过期 token 有稳定拒绝码；如果没有这段测试，TTL 安全边界可能退化。
        clock = {"now": 1000.0}  # 新增代码+Phase98UniversalComputerUseMode：用可变时钟控制 now_func；如果没有这行代码，测试无法稳定模拟 token 过期。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，过期 token 测试会污染真实状态。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir), now_func=lambda: clock["now"])  # 新增代码+Phase98UniversalComputerUseMode：注入测试时钟；如果没有这行代码，无法不用等待就验证过期。
            request = store.request_full_mode(reason="用户请求 full mode")  # 新增代码+Phase98UniversalComputerUseMode：生成待确认 token；如果没有这行代码，过期路径没有 pending 文件。
            clock["now"] = 1401.0  # 新增代码+Phase98UniversalComputerUseMode：把时间推进到 300 秒 TTL 之后；如果没有这行代码，token 仍会被当成有效。
            decision = store.confirm_full_mode(request["confirmation_token"], reason="用户太晚确认 full mode")  # 新增代码+Phase98UniversalComputerUseMode：提交已过期 token；如果没有这行代码，expired 路径不会被覆盖。
            status = store.status()  # 新增代码+Phase98UniversalComputerUseMode：读取确认失败后的状态；如果没有这行代码，测试无法确认过期不会提权。
        self.assertFalse(decision["opened"])  # 新增代码+Phase98UniversalComputerUseMode：断言过期 token 不会打开模式；如果没有这行代码，TTL 失效可能被忽略。
        self.assertEqual(decision["decision"], "full_mode_confirmation_expired")  # 新增代码+Phase98UniversalComputerUseMode：断言 expired 使用独立原因码；如果没有这行代码，调用方无法提示用户重新申请。
        self.assertEqual(decision["low_level_event_count"], 0)  # 新增代码+Phase98UniversalComputerUseMode：断言过期拒绝零低层事件；如果没有这行代码，拒绝过程可能不够安全。
        self.assertFalse(status["full_mode"])  # 新增代码+Phase98UniversalComputerUseMode：断言过期确认后仍不是 full；如果没有这行代码，失败路径可能暗中提权。

    def test_state_hides_sensitive_reason_text(self) -> None:  # 新增代码+Phase98UniversalComputerUseMode：函数段开始，验证状态文件不写敏感原文；如果没有这段测试，用户 prompt 可能泄露进磁盘。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase98UniversalComputerUseMode：创建隔离目录；如果没有这行代码，隐私测试会污染真实状态。
            root = Path(temp_dir)  # 新增代码+Phase98UniversalComputerUseMode：保存根路径；如果没有这行代码，后续读取文件需要重复构造路径。
            store = ComputerUseModeSessionStore(base_dir=root)  # 新增代码+Phase98UniversalComputerUseMode：创建模式 store；如果没有这行代码，无法写入状态文件。
            store.open_mode(mode="normal", reason="secret-password-123 打开 computer use")  # 新增代码+Phase98UniversalComputerUseMode：写入包含敏感词的原因；如果没有这行代码，隐私扫描没有样本。
            serialized = json.dumps(json.loads((root / "current.json").read_text(encoding="utf-8")), ensure_ascii=False)  # 新增代码+Phase98UniversalComputerUseMode：读取并序列化状态文件；如果没有这行代码，无法扫描落盘内容。
        self.assertNotIn("secret-password-123", serialized)  # 新增代码+Phase98UniversalComputerUseMode：断言敏感原文没有落盘；如果没有这行代码，状态文件可能泄露用户内容。
        self.assertIn("reason_sha256_16", serialized)  # 新增代码+Phase98UniversalComputerUseMode：断言保留脱敏哈希；如果没有这行代码，排查时无法关联用户请求。


if __name__ == "__main__":  # 新增代码+Phase98UniversalComputerUseMode：文件入口段开始，允许直接运行测试；如果没有这行代码，小白用户必须记完整 unittest 命令。
    unittest.main()  # 新增代码+Phase98UniversalComputerUseMode：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
