"Observability, permission event, and visible terminal acceptance tests."  # Stage14: this file owns the observability_acceptance test group.
from __future__ import annotations  # Stage14: keep annotations lazy after test split.
import unittest  # Stage14: keep direct unittest execution available.
from learning_agent.tests.support import *  # Stage14: import shared helpers and dependencies for copied tests.

class ObservabilityAcceptanceTests(LearningAgentTestBase):  # Stage14: unittest discovers this concrete modular test class.
    def test_acceptance_events_are_noop_without_event_log(self) -> None:  # 修改代码+Stage14硬清理: 把测试名改成新观测层 acceptance_events；若没有这行代码，维护者会误以为旧根目录验收入口仍在使用
        stream = io.StringIO()  # 新增代码+AcceptanceHarness: 创建内存输出流观察是否打印标记；若没有这行代码，测试无法确认默认静默
        event = emit_acceptance_event("agent_ready_for_user_prompt", {"workspace": "demo"}, stream=stream, environ={})  # 新增代码+AcceptanceHarness: 在没有环境变量时尝试发事件；若没有这行代码，无法证明默认是 no-op
        self.assertIsNone(event)  # 新增代码+AcceptanceHarness: 断言未配置日志路径时不生成事件对象；若没有这行代码，调用方可能误以为事件已被保存
        self.assertEqual(stream.getvalue(), "")  # 新增代码+AcceptanceHarness: 断言默认不会向终端输出机器标记；若没有这行代码，普通用户启动 agent 可能看到额外噪声
    def test_acceptance_events_emit_event_jsonl_without_stdout_noise_by_default(self) -> None:  # 修改代码+AcceptanceStdoutNoiseControl: 函数段开始，验证验收事件默认只写 JSONL 不打印到终端；若没有这段测试，用户终端可能再次出现机器 JSON 事件墙。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+AcceptanceHarness: 创建临时目录隔离事件日志；若没有这行代码，测试会污染真实工作区
            event_log_path = Path(raw_dir) / "events" / "events.jsonl"  # 新增代码+AcceptanceHarness: 指定嵌套日志路径；若没有这行代码，无法验证模块会自动创建父目录
            stream = io.StringIO()  # 新增代码+AcceptanceHarness: 创建内存终端流保存标记行；若没有这行代码，测试无法检查可见终端信号
            event = emit_acceptance_event("agent_ready_for_user_prompt", {"workspace": "demo"}, stream=stream, environ={ACCEPTANCE_EVENT_ENV_VAR: str(event_log_path)})  # 新增代码+AcceptanceHarness: 发送一条 ready 事件；若没有这行代码，协议写入路径不会被执行
            self.assertIsNotNone(event)  # 新增代码+AcceptanceHarness: 断言启用后返回事件对象；若没有这行代码，调用方无法复用事件做调试
            self.assertTrue(event_log_path.exists())  # 新增代码+AcceptanceHarness: 断言 JSONL 文件已创建；若没有这行代码，事件可能只打印没落盘
            events = self._read_acceptance_events(event_log_path)  # 新增代码+AcceptanceHarness: 读取刚写入的事件；若没有这行代码，后续断言没有结构化数据
            self.assertEqual(events[0]["schema_version"], 1)  # 新增代码+AcceptanceHarness: 断言事件协议版本稳定；若没有这行代码，后续升级无法兼容检查
            self.assertEqual(events[0]["state"], "agent_ready_for_user_prompt")  # 新增代码+AcceptanceHarness: 断言状态名正确；若没有这行代码，外部 agent 无法等待正确时机输入 prompt
            self.assertEqual(events[0]["payload"]["workspace"], "demo")  # 新增代码+AcceptanceHarness: 断言 payload 被原样保存；若没有这行代码，事件会缺少控制器需要的上下文
            self.assertEqual(stream.getvalue(), "")  # 修改代码+AcceptanceStdoutNoiseControl: 断言默认不再把机器事件打印到人类终端；若没有这行代码，真实可见终端仍会被验收 JSON 污染。
    def test_acceptance_events_stdout_marker_is_explicit_opt_in(self) -> None:  # 修改代码+AcceptanceStdoutNoiseControl: 函数段开始，验证需要终端机器标记时必须显式打开；若没有这段测试，旧控制方式可能被误删或默认噪声回归。
        with tempfile.TemporaryDirectory() as raw_dir:  # 修改代码+AcceptanceStdoutNoiseControl: 创建临时目录隔离事件日志；若没有这行代码，测试会污染真实验收目录。
            event_log_path = Path(raw_dir) / "events.jsonl"  # 修改代码+AcceptanceStdoutNoiseControl: 指定本测试事件日志路径；若没有这行代码，emit 无法进入启用状态。
            stream = io.StringIO()  # 修改代码+AcceptanceStdoutNoiseControl: 创建内存终端流；若没有这行代码，无法断言显式 stdout 标记。
            event = emit_acceptance_event("agent_ready_for_user_prompt", {"workspace": "demo"}, stream=stream, environ={ACCEPTANCE_EVENT_ENV_VAR: str(event_log_path), ACCEPTANCE_EVENT_STDOUT_ENV_VAR: "1"})  # 修改代码+AcceptanceStdoutNoiseControl: 同时启用 JSONL 和 stdout 标记；若没有这行代码，无法验证显式 opt-in 行为。
            self.assertIsNotNone(event)  # 修改代码+AcceptanceStdoutNoiseControl: 断言事件仍正常生成；若没有这行代码，stdout 开关可能破坏事件返回值。
            terminal_marker = stream.getvalue().replace(" ", "")  # 新增代码+AcceptanceHarness: 清理空格方便检查紧凑 JSON 片段；若没有这行代码，JSON 格式微调会让断言过脆
            self.assertIn(ACCEPTANCE_EVENT_MARKER_PREFIX, stream.getvalue())  # 新增代码+AcceptanceHarness: 断言终端里有机器可识别前缀；若没有这行代码，外部 agent 仍只能靠截图猜状态
            self.assertIn('"state":"agent_ready_for_user_prompt"', terminal_marker)  # 新增代码+AcceptanceHarness: 断言终端标记包含状态名；若没有这行代码，控制器无法只看终端判断 ready
    def test_terminal_permission_emits_acceptance_events(self) -> None:  # 新增代码+AcceptanceHarness: 验证真实权限输入点会发出待授权和已回答事件；若没有这行代码，可见终端自动化仍不知道何时该输入 y
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+AcceptanceHarness: 创建临时目录保存事件日志；若没有这行代码，测试会污染真实验收日志
            event_log_path = Path(raw_dir) / "events.jsonl"  # 新增代码+AcceptanceHarness: 指定本测试的事件日志文件；若没有这行代码，事件写入位置不明确
            with mock.patch.dict(os.environ, {ACCEPTANCE_EVENT_ENV_VAR: str(event_log_path), "LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS": "0"}, clear=False):  # 修改代码+AcceptanceStdoutNoiseControl: 临时启用验收日志并显式关闭危险自动授权；若没有这行代码，当前开发默认危险模式会绕过 input 导致本测试目标失真。
                with mock.patch("sys.stdout", new=io.StringIO()):  # 新增代码+AcceptanceHarness: 把测试里的终端标记收进内存；若没有这行代码，完整单测输出会混入机器事件行
                    with mock.patch("builtins.input", return_value="y") as fake_input:  # 新增代码+AcceptanceHarness: 模拟用户在真实提示处输入 y；若没有这行代码，单元测试会卡在等待人工输入
                        allowed = ask_permission_from_terminal("启动 MCP server：browser_automation")  # 新增代码+AcceptanceHarness: 调用真实终端权限函数；若没有这行代码，测试无法覆盖生产交互点
            self.assertTrue(allowed)  # 新增代码+AcceptanceHarness: 断言 y 仍然表示允许；若没有这行代码，harness 改造可能破坏原有权限语义
            fake_input.assert_called_once()  # 新增代码+AcceptanceHarness: 断言只询问了一次用户；若没有这行代码，自动化输入可能被重复消耗
            events = self._read_acceptance_events(event_log_path)  # 新增代码+AcceptanceHarness: 读取权限函数写出的事件；若没有这行代码，后续无法确认状态顺序
            self.assertEqual([event["state"] for event in events], ["permission_required", "permission_answered"])  # 新增代码+AcceptanceHarness: 断言先等待授权再记录回答；若没有这行代码，控制器无法安全安排输入时机
            self.assertEqual(events[0]["payload"]["action"], "启动 MCP server：browser_automation")  # 新增代码+AcceptanceHarness: 断言待授权事件包含动作文本；若没有这行代码，控制器不知道当前请求授权什么
            self.assertTrue(events[1]["payload"]["allowed"])  # 新增代码+AcceptanceHarness: 断言已回答事件记录允许结果；若没有这行代码，控制器无法判断 y 是否生效
    def test_acceptance_controller_files_and_scenarios_are_valid(self) -> None:  # 新增代码+AcceptanceController: 验证通用验收控制器和场景文件存在且结构正确；若没有这行代码，临时脚本容易继续复制粘贴膨胀
        controller_dir = (TEST_ROOT / "acceptance_controller")  # 新增代码+AcceptanceController: 定位 learning_agent/acceptance_controller 目录；若没有这行代码，测试无法找到新控制器入口
        controller_path = controller_dir / "controller.ps1"  # 新增代码+AcceptanceController: 定位通用 PowerShell 控制器；若没有这行代码，后续无法检查统一入口
        scenarios_dir = controller_dir / "scenarios"  # 新增代码+AcceptanceController: 定位场景目录；若没有这行代码，场景 JSON 会继续散落在测试脚本里
        readme_path = controller_dir / "README.md"  # 新增代码+AcceptanceController: 定位控制器说明文档；若没有这行代码，用户不知道如何运行新控制器
        self.assertTrue(controller_path.exists())  # 新增代码+AcceptanceController: 断言控制器脚本存在；若没有这行代码，缺脚本也可能没人发现
        self.assertTrue(readme_path.exists())  # 新增代码+AcceptanceController: 断言 README 存在；若没有这行代码，新增控制器缺少学习说明也不会失败
        scenario_names = ["smoke.json", "chongqing_weather_browser.json", "real_chrome_profile_status.json", "real_chrome_connect_public_page.json", "real_chrome_chongqing_weather_travel.json", "real_chrome_google_human_search.json", "real_chrome_natural_weather_travel.json", "real_chrome_natural_youtube_video_comments.json"]  # 修改代码+YouTube公开查询: 固定 YouTube 视频评论自然短 prompt 场景也必须交付；若没有这行代码，用户截图里的无 y 真实浏览器验收可能缺少场景保护
        for scenario_name in scenario_names:  # 新增代码+AcceptanceController: 遍历每个场景文件；若没有这行代码，只会检查其中一个场景
            scenario_path = scenarios_dir / scenario_name  # 新增代码+AcceptanceController: 拼出当前场景路径；若没有这行代码，测试无法读取具体 JSON
            self.assertTrue(scenario_path.exists())  # 新增代码+AcceptanceController: 断言场景文件存在；若没有这行代码，漏交场景不会失败
            scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+AcceptanceController: 读取并解析 UTF-8 JSON；若没有这行代码，格式错误或乱码不会被发现
            self.assertIsInstance(scenario.get("name"), str)  # 新增代码+AcceptanceController: 断言场景名是字符串；若没有这行代码，结果目录和日志命名可能不稳定
            self.assertIsInstance(scenario.get("prompt_lines"), list)  # 新增代码+AcceptanceController: 断言 prompt 使用字符串数组；若没有这行代码，长 prompt 可能回到难维护的一整行
            self.assertGreater(len(scenario["prompt_lines"]), 0)  # 新增代码+AcceptanceController: 断言 prompt 至少一行；若没有这行代码，空场景可能被误当成有效测试
            self.assertIsInstance(scenario.get("success_marker"), str)  # 新增代码+AcceptanceController: 断言有固定成功标记；若没有这行代码，控制器无法稳定确认最终回答属于本轮
            self.assertIsInstance(scenario.get("required_event_states"), list)  # 新增代码+AcceptanceController: 断言有必需事件序列；若没有这行代码，场景无法表达最低事件门槛
            self.assertIn("agent_ready_for_user_prompt", scenario["required_event_states"])  # 新增代码+AcceptanceController: 断言场景必须等待 ready；若没有这行代码，prompt 可能再次输进启动权限提示
            self.assertIn("final_answer_printed", scenario["required_event_states"])  # 新增代码+AcceptanceController: 断言场景必须等待最终回答；若没有这行代码，测试可能在模型未完成时误判
            self.assertIsInstance(scenario.get("debug_log_contains"), list)  # 新增代码+AcceptanceController: 断言有调试日志断言列表；若没有这行代码，场景无法证明工具调用或输出内容
            self.assertIsInstance(scenario.get("event_answer_contains"), list)  # 新增代码+RealChromeStatus: 断言场景必须声明最终回答预览断言；若没有这行代码，控制器可能只看日志而漏掉用户可见答案
            if "post_success_wait_seconds" in scenario:  # 新增代码+GoogleHumanVisible: 只在场景声明成功后可见停留时检查类型；若没有这行代码，演示场景可能把等待时间写错成字符串
                self.assertIsInstance(scenario.get("post_success_wait_seconds"), int)  # 新增代码+GoogleHumanVisible: 断言可见停留秒数是整数；若没有这行代码，controller 转换等待时间时可能行为不清楚
            if "max_permission_sent_count" in scenario:  # 新增代码+真实浏览器客户模式: 只在场景声明权限响应上限时检查类型；若没有这行代码，无 y 验收字段写错也不会被发现
                self.assertIsInstance(scenario.get("max_permission_sent_count"), int)  # 新增代码+真实浏览器客户模式: 断言权限响应上限是整数；若没有这行代码，controller 比较次数时可能行为不稳定
            if "permission_policy" in scenario:  # 新增代码+RealChromeConnect: 只在场景声明权限策略时检查结构；若没有这行代码，旧 smoke/天气场景会被迫补高风险权限策略
                permission_policy = scenario["permission_policy"]  # 新增代码+RealChromeConnect: 取出场景级权限策略；若没有这行代码，后续无法验证 allow/deny 白名单字段
                self.assertIn(permission_policy.get("default_response"), ("allow", "deny"))  # 新增代码+RealChromeConnect: 断言默认权限响应只能是 allow 或 deny；若没有这行代码，拼写错误会让控制器行为不可预测
                self.assertIsInstance(permission_policy.get("allow_contains"), list)  # 新增代码+RealChromeConnect: 断言允许匹配词是列表；若没有这行代码，控制器遍历策略时可能崩溃
                self.assertIsInstance(permission_policy.get("deny_contains"), list)  # 新增代码+RealChromeConnect: 断言拒绝匹配词是列表；若没有这行代码，高风险拒绝规则可能无法表达
                if "allow_tool_names" in permission_policy:  # 新增代码+StructuredPermissionLedger: 只在场景声明结构化工具白名单时检查；若没有这行代码，旧场景会被迫迁移所有策略字段
                    self.assertIsInstance(permission_policy.get("allow_tool_names"), list)  # 新增代码+StructuredPermissionLedger: 断言工具白名单是列表；若没有这行代码，controller 遍历工具名时可能崩溃
                if "deny_tool_names" in permission_policy:  # 新增代码+StructuredPermissionLedger: 只在场景声明结构化工具拒绝表时检查；若没有这行代码，旧场景会被迫增加无关字段
                    self.assertIsInstance(permission_policy.get("deny_tool_names"), list)  # 新增代码+StructuredPermissionLedger: 断言工具拒绝表是列表；若没有这行代码，高风险工具名拒绝无法稳定表达
                if "allow_url_prefixes" in permission_policy:  # 新增代码+StructuredPermissionLedger: 只在场景声明 URL 前缀白名单时检查；若没有这行代码，非浏览器场景会被迫提供 URL 规则
                    self.assertIsInstance(permission_policy.get("allow_url_prefixes"), list)  # 新增代码+StructuredPermissionLedger: 断言 URL 前缀白名单是列表；若没有这行代码，browser_open 参数校验无法稳定遍历
            if scenario_name == "real_chrome_profile_status.json":  # 新增代码+RealChromeStatus: 只对真实 Chrome 状态场景追加隐私和工具边界检查；若没有这行代码，通用场景会被迫包含真实 Chrome 专用内容
                prompt_text = "\n".join(scenario["prompt_lines"])  # 新增代码+RealChromeStatus: 合并 prompt 行便于检查关键指令；若没有这行代码，测试只能逐行写重复断言且难以维护
                debug_log_text = "\n".join(scenario["debug_log_contains"])  # 新增代码+RealChromeStatus: 合并日志断言文本便于确认工具证据；若没有这行代码，测试无法简单验证 browser_profile_status 被要求出现在日志里
                answer_text = "\n".join(scenario["event_answer_contains"])  # 新增代码+RealChromeStatus: 合并最终回答断言文本便于确认用户可见结果；若没有这行代码，测试无法保护成功标记必须出现在答案预览里
                self.assertIn("learning_agent/skills/real_chrome/SKILL.md", prompt_text)  # 新增代码+RealChromeStatus: 断言场景要求读取真实 Chrome skill；若没有这行代码，agent 可能不知道真实 Chrome 的安全流程
                self.assertIn("browser_profile_status", prompt_text)  # 新增代码+RealChromeStatus: 断言场景要求先调用 profile 状态工具；若没有这行代码，agent 可能跳过安全探针直接尝试接管浏览器
                self.assertIn("不要读取 cookies", prompt_text)  # 新增代码+RealChromeStatus: 断言场景明示不读取隐私凭据；若没有这行代码，真实 Chrome 验收可能越界触碰登录态敏感数据
                self.assertIn("browser_profile_status", debug_log_text)  # 新增代码+RealChromeStatus: 断言日志证据必须包含 profile 状态工具；若没有这行代码，场景可能只靠文字承诺而没有工具调用证据
                self.assertIn("REAL_CHROME_PROFILE_STATUS_OK", answer_text)  # 新增代码+RealChromeStatus: 断言最终回答必须包含固定成功标记；若没有这行代码，控制器难以确认本轮真实 Chrome 探针完成
            if scenario_name == "real_chrome_connect_public_page.json":  # 新增代码+RealChromeConnect: 只对真实 Chrome 公开页连接场景追加高风险边界检查；若没有这行代码，connect 场景可能缺少安全约束
                prompt_text = "\n".join(scenario["prompt_lines"])  # 新增代码+RealChromeConnect: 合并 prompt 行便于检查关键指令；若没有这行代码，测试无法集中验证连接流程
                debug_log_text = "\n".join(scenario["debug_log_contains"])  # 新增代码+RealChromeConnect: 合并日志断言文本便于确认真实连接证据；若没有这行代码，测试无法确认 connect/open/snapshot 都被要求
                answer_text = "\n".join(scenario["event_answer_contains"])  # 新增代码+RealChromeConnect: 合并最终回答断言文本便于确认用户可见标记；若没有这行代码，测试无法保护公开页验收结果
                permission_policy = scenario["permission_policy"]  # 新增代码+RealChromeConnect: 读取本场景权限策略；若没有这行代码，后续无法验证默认拒绝和白名单
                allow_text = "\n".join(permission_policy["allow_contains"])  # 新增代码+RealChromeConnect: 合并允许匹配词便于检查白名单覆盖；若没有这行代码，测试需要重复访问列表
                deny_text = "\n".join(permission_policy["deny_contains"])  # 新增代码+RealChromeConnect: 合并拒绝匹配词便于检查高风险阻断；若没有这行代码，测试无法确认 evaluate 被拒绝
                self.assertEqual(permission_policy["default_response"], "deny")  # 新增代码+RealChromeConnect: 断言 connect 场景默认拒绝未白名单权限；若没有这行代码，未知高风险工具可能被自动同意
                self.assertIn("browser_profile_status", allow_text)  # 新增代码+RealChromeConnect: 断言只读状态工具在白名单；若没有这行代码，connect 前置检查会被 controller 拒绝
                self.assertIn("browser_connect_real_chrome", allow_text)  # 新增代码+RealChromeConnect: 断言真实 Chrome connect 在本场景显式白名单；若没有这行代码，场景无法进入真实连接
                self.assertIn("browser_open", allow_text)  # 新增代码+RealChromeConnect: 断言打开公开页面工具在白名单；若没有这行代码，连接后无法访问公开测试页
                self.assertIn("browser_snapshot", allow_text)  # 新增代码+RealChromeConnect: 断言读取公开页面快照工具在白名单；若没有这行代码，场景无法确认页面内容
                self.assertIn("browser_evaluate", deny_text)  # 新增代码+RealChromeConnect: 断言页面脚本执行默认拒绝；若没有这行代码，场景可能通过 JS 读取敏感页面状态
                self.assertIn("browser_connect_real_chrome", prompt_text)  # 新增代码+RealChromeConnect: 断言 prompt 明确要求真实 Chrome 连接工具；若没有这行代码，agent 可能停在 status 阶段
                self.assertIn("confirm_real_profile=true", prompt_text)  # 新增代码+RealChromeConnect: 断言 prompt 明确高风险确认参数；若没有这行代码，connect 工具会因为缺少确认而失败
                self.assertIn("https://example.com", prompt_text)  # 新增代码+RealChromeConnect: 断言只打开公开测试页面；若没有这行代码，场景可能访问用户隐私或登录网站
                self.assertIn("不要读取 cookies", prompt_text)  # 新增代码+RealChromeConnect: 断言 connect 后仍禁止读取隐私凭据；若没有这行代码，真实 profile 测试可能越界
                self.assertIn("browser_connect_real_chrome 成功", debug_log_text)  # 新增代码+RealChromeConnect: 断言日志必须证明真实 Chrome 连接成功；若没有这行代码，场景可能只完成 status
                self.assertIn("real_chrome_connected=true", debug_log_text)  # 新增代码+RealChromeConnect: 断言日志必须包含机器可读连接成功标记；若没有这行代码，无法区分独立 Chromium 与真实 Chrome
                self.assertIn("browser_open 成功", debug_log_text)  # 新增代码+RealChromeConnect: 断言日志必须证明公开页面被打开；若没有这行代码，连接后没有实际浏览动作
                self.assertIn("browser_snapshot 成功", debug_log_text)  # 新增代码+RealChromeConnect: 断言日志必须证明公开页面快照被读取；若没有这行代码，无法确认页面内容读取链路
                self.assertIn("REAL_CHROME_CONNECT_PUBLIC_PAGE_OK", answer_text)  # 新增代码+RealChromeConnect: 断言最终回答必须包含固定成功标记；若没有这行代码，控制器难以确认本轮公开页验收完成
            if scenario_name == "real_chrome_chongqing_weather_travel.json":  # 新增代码+RealChromeWeather: 只对真实 Chrome 重庆天气攻略场景追加任务与隐私边界检查；若没有这行代码，新场景可能退化成普通浏览器或越界读取隐私
                prompt_text = "\n".join(scenario["prompt_lines"])  # 新增代码+RealChromeWeather: 合并 prompt 行便于集中检查真实 Chrome 查询流程；若没有这行代码，测试需要重复遍历每一行且容易漏断言
                debug_log_text = "\n".join(scenario["debug_log_contains"])  # 新增代码+RealChromeWeather: 合并日志断言文本便于确认真实工具调用证据；若没有这行代码，场景可能只有文字承诺没有工具链证据
                answer_text = "\n".join(scenario["event_answer_contains"])  # 新增代码+RealChromeWeather: 合并最终回答断言文本便于确认用户可见结果；若没有这行代码，控制器无法稳定确认天气攻略输出
                permission_policy = scenario["permission_policy"]  # 新增代码+RealChromeWeather: 读取本场景权限策略；若没有这行代码，后续无法验证默认拒绝和白名单边界
                allow_text = "\n".join(permission_policy["allow_contains"])  # 新增代码+RealChromeWeather: 合并允许匹配词便于检查必要工具白名单；若没有这行代码，测试无法确认真实查询链路会被放行
                deny_text = "\n".join(permission_policy["deny_contains"])  # 新增代码+RealChromeWeather: 合并拒绝匹配词便于检查高风险工具阻断；若没有这行代码，测试无法确认脚本执行和标签读取被禁止
                allow_tool_text = "\n".join(permission_policy["allow_tool_names"])  # 新增代码+StructuredPermissionLedger: 合并结构化工具白名单便于检查；若没有这行代码，测试无法确认天气场景不再靠 action 文本放行工具
                deny_tool_text = "\n".join(permission_policy["deny_tool_names"])  # 新增代码+StructuredPermissionLedger: 合并结构化工具拒绝表便于检查；若没有这行代码，测试无法确认高风险工具名被精确拒绝
                allow_url_text = "\n".join(permission_policy["allow_url_prefixes"])  # 新增代码+StructuredPermissionLedger: 合并 URL 前缀白名单便于检查；若没有这行代码，测试无法确认 browser_open 被限制到 Open-Meteo
                self.assertEqual(permission_policy["default_response"], "deny")  # 新增代码+RealChromeWeather: 断言真实 Chrome 天气场景默认拒绝未知权限；若没有这行代码，模型请求非白名单工具时可能被自动同意
                self.assertIn("启动 MCP server", allow_text)  # 修改代码+StructuredPermissionLedger: 启动 MCP 仍用文本白名单兜底；若没有这行代码，真实终端启动阶段会被默认拒绝卡住
                self.assertNotIn("browser_open", allow_text)  # 新增代码+StructuredPermissionLedger: 断言 browser_open 不再靠 action 文本放行；若没有这行代码，URL 前缀限制可能被 contains 白名单绕过
                self.assertIn("browser_profile_status", allow_tool_text)  # 修改代码+StructuredPermissionLedger: 断言只读状态工具在结构化白名单；若没有这行代码，真实 Chrome 连接前置检查会被拒绝
                self.assertIn("browser_connect_real_chrome", allow_tool_text)  # 修改代码+StructuredPermissionLedger: 断言真实 Chrome 连接工具在结构化白名单；若没有这行代码，场景无法使用桌面 Chrome
                self.assertIn("browser_open", allow_tool_text)  # 修改代码+StructuredPermissionLedger: 断言打开天气 URL 的工具在结构化白名单；若没有这行代码，agent 无法访问 Open-Meteo 页面
                self.assertIn("browser_snapshot", allow_tool_text)  # 修改代码+StructuredPermissionLedger: 断言读取天气页面快照的工具在结构化白名单；若没有这行代码，agent 无法从网页获取天气 JSON
                self.assertIn("browser_evaluate", deny_tool_text)  # 修改代码+StructuredPermissionLedger: 断言页面脚本执行工具被结构化拒绝；若没有这行代码，场景可能通过 JS 读取浏览器敏感状态
                self.assertIn("https://api.open-meteo.com/v1/forecast", allow_url_text)  # 新增代码+StructuredPermissionLedger: 断言 browser_open 只允许 Open-Meteo forecast 前缀；若没有这行代码，真实 Chrome 可能被打开到未授权网站
                self.assertIn("learning_agent/skills/real_chrome/SKILL.md", prompt_text)  # 新增代码+RealChromeWeather: 断言 prompt 要求读取真实 Chrome 规则；若没有这行代码，agent 可能不知道真实 profile 的高风险边界
                self.assertIn("browser_profile_status", prompt_text)  # 新增代码+RealChromeWeather: 断言 prompt 要求先检查 profile 状态；若没有这行代码，agent 可能跳过安全探针直接连接
                self.assertIn("browser_connect_real_chrome", prompt_text)  # 新增代码+RealChromeWeather: 断言 prompt 明确要求真实 Chrome 连接；若没有这行代码，agent 可能改用独立 Chromium 冒充
                self.assertIn("confirm_real_profile=true", prompt_text)  # 新增代码+RealChromeWeather: 断言 prompt 明确高风险确认参数；若没有这行代码，connect 工具会因缺少确认而失败
                self.assertIn("api.open-meteo.com", prompt_text)  # 新增代码+RealChromeWeather: 断言天气来源是公开 Open-Meteo URL；若没有这行代码，场景可能访问不可控搜索结果或登录站点
                self.assertIn("2026-05-31", prompt_text)  # 新增代码+RealChromeWeather: 断言 2026-05-28 的三天后日期被写死为 2026-05-31；若没有这行代码，复测时相对日期容易漂移
                self.assertIn("重庆", prompt_text)  # 新增代码+RealChromeWeather: 断言任务城市是重庆；若没有这行代码，agent 可能查询到其他城市
                self.assertIn("旅游攻略", prompt_text)  # 新增代码+RealChromeWeather: 断言最终任务包含攻略生成；若没有这行代码，场景可能只返回天气不覆盖用户目标
                self.assertIn("不要读取 cookies", prompt_text)  # 新增代码+RealChromeWeather: 断言真实 Chrome 连接后仍禁止读取隐私凭据；若没有这行代码，登录态场景可能越界
                self.assertIn("browser_connect_real_chrome 成功", debug_log_text)  # 新增代码+RealChromeWeather: 断言日志必须证明真实 Chrome 连接成功；若没有这行代码，无法区分真实 Chrome 与普通浏览器
                self.assertIn("real_chrome_connected=true", debug_log_text)  # 新增代码+RealChromeWeather: 断言日志必须包含机器可读连接成功标记；若没有这行代码，控制器无法验证真实 profile 链路
                self.assertIn("browser_open 成功", debug_log_text)  # 新增代码+RealChromeWeather: 断言日志必须证明天气 URL 被打开；若没有这行代码，agent 可能没有实际访问来源
                self.assertIn("browser_snapshot 成功", debug_log_text)  # 新增代码+RealChromeWeather: 断言日志必须证明天气 JSON 被读取；若没有这行代码，agent 可能只凭记忆生成攻略
                self.assertIn("REAL_CHROME_CHONGQING_WEATHER_TRAVEL_OK", answer_text)  # 新增代码+RealChromeWeather: 断言最终回答必须包含固定成功标记；若没有这行代码，控制器难以确认本轮真实 Chrome 天气攻略验收完成
            if scenario_name == "real_chrome_google_human_search.json":  # 新增代码+GoogleHumanVisible: 只对真实 Chrome Google 拟人搜索场景追加可见动作检查；若没有这行代码，场景可能退化成直接 URL 导航
                prompt_text = "\n".join(scenario["prompt_lines"])  # 新增代码+GoogleHumanVisible: 合并 prompt 行便于集中检查动作要求；若没有这行代码，测试需要逐行搜索且容易漏掉拟人步骤
                debug_log_text = "\n".join(scenario["debug_log_contains"])  # 新增代码+GoogleHumanVisible: 合并日志断言文本便于确认工具证据；若没有这行代码，场景可能只有口头描述没有实际点击输入
                answer_text = "\n".join(scenario["event_answer_contains"])  # 新增代码+GoogleHumanVisible: 合并最终回答断言文本便于确认用户可见结果；若没有这行代码，控制器无法稳定判断演示完成
                permission_policy = scenario["permission_policy"]  # 新增代码+GoogleHumanVisible: 读取本场景权限策略；若没有这行代码，后续无法验证工具白名单和 Google URL 边界
                allow_text = "\n".join(permission_policy["allow_contains"])  # 新增代码+GoogleHumanVisible: 合并文本白名单便于检查启动 MCP；若没有这行代码，启动权限边界无法验证
                allow_tool_text = "\n".join(permission_policy["allow_tool_names"])  # 新增代码+GoogleHumanVisible: 合并结构化工具白名单便于检查拟人动作工具；若没有这行代码，测试无法确认点击输入按键被允许
                deny_tool_text = "\n".join(permission_policy["deny_tool_names"])  # 新增代码+GoogleHumanVisible: 合并结构化拒绝工具便于检查高风险阻断；若没有这行代码，测试无法确认 evaluate/network 被拒绝
                allow_url_text = "\n".join(permission_policy["allow_url_prefixes"])  # 新增代码+GoogleHumanVisible: 合并 URL 白名单便于确认只打开 Google；若没有这行代码，browser_open 可能访问其它网站
                self.assertEqual(permission_policy["default_response"], "deny")  # 新增代码+GoogleHumanVisible: 断言 Google 演示默认拒绝未知权限；若没有这行代码，模型请求非白名单工具时可能被同意
                self.assertGreaterEqual(scenario.get("post_success_wait_seconds", 0), 15)  # 新增代码+GoogleHumanVisible: 断言成功后至少停留 15 秒方便用户肉眼观察；若没有这行代码，窗口可能一闪而过
                self.assertIn("启动 MCP server", allow_text)  # 新增代码+GoogleHumanVisible: 断言启动 MCP 权限仍可放行；若没有这行代码，真实终端启动阶段会卡住
                self.assertIn("browser_profile_status", allow_tool_text)  # 新增代码+GoogleHumanVisible: 断言 profile 状态工具在白名单；若没有这行代码，真实 Chrome 连接前置检查会被拒绝
                self.assertIn("browser_connect_real_chrome", allow_tool_text)  # 新增代码+GoogleHumanVisible: 断言真实 Chrome 连接工具在白名单；若没有这行代码，演示无法使用桌面 Chrome
                self.assertIn("browser_open", allow_tool_text)  # 新增代码+GoogleHumanVisible: 断言打开 Google 首页工具在白名单；若没有这行代码，agent 无法进入 Google
                self.assertIn("browser_snapshot", allow_tool_text)  # 新增代码+GoogleHumanVisible: 断言读取页面状态工具在白名单；若没有这行代码，agent 无法找搜索框或确认结果
                self.assertIn("browser_click", allow_tool_text)  # 新增代码+GoogleHumanVisible: 断言点击工具在白名单；若没有这行代码，无法演示点击搜索框
                self.assertIn("browser_type", allow_tool_text)  # 新增代码+GoogleHumanVisible: 断言输入工具在白名单；若没有这行代码，无法演示键入搜索词
                self.assertIn("browser_press_key", allow_tool_text)  # 新增代码+GoogleHumanVisible: 断言按键工具在白名单；若没有这行代码，无法演示按 Enter 搜索
                self.assertIn("browser_wait", allow_tool_text)  # 新增代码+GoogleHumanVisible: 断言等待工具在白名单；若没有这行代码，结果页加载可能还没完成就截图
                self.assertIn("browser_screenshot", allow_tool_text)  # 新增代码+GoogleHumanVisible: 断言截图工具在白名单；若没有这行代码，用户无法获得视觉证据
                self.assertIn("browser_evaluate", deny_tool_text)  # 新增代码+GoogleHumanVisible: 断言 JS 执行工具被拒绝；若没有这行代码，演示可能越界读取页面状态
                self.assertIn("browser_network", deny_tool_text)  # 新增代码+GoogleHumanVisible: 断言 network 工具被拒绝；若没有这行代码，演示可能读取网络请求细节
                self.assertIn("https://www.google.com", allow_url_text)  # 新增代码+GoogleHumanVisible: 断言 browser_open 只允许 Google 域名前缀；若没有这行代码，真实 Chrome 可能被打开到未授权网站
                self.assertIn("Google", prompt_text)  # 新增代码+GoogleHumanVisible: 断言 prompt 明确是 Google 演示；若没有这行代码，agent 可能跑回 Open-Meteo 稳定查询
                self.assertIn("browser_click", prompt_text)  # 新增代码+GoogleHumanVisible: 断言 prompt 明确要求点击；若没有这行代码，agent 可能直接打开搜索结果 URL
                self.assertIn("browser_type", prompt_text)  # 新增代码+GoogleHumanVisible: 断言 prompt 明确要求输入；若没有这行代码，用户看不到拟人键入动作
                self.assertIn("browser_press_key", prompt_text)  # 新增代码+GoogleHumanVisible: 断言 prompt 明确要求按 Enter；若没有这行代码，搜索提交动作可能不可见
                self.assertIn("browser_screenshot", prompt_text)  # 新增代码+GoogleHumanVisible: 断言 prompt 明确要求截图；若没有这行代码，视觉证据不会落盘
                self.assertIn("重庆 2026-05-31 天气 旅游攻略", prompt_text)  # 新增代码+GoogleHumanVisible: 断言搜索词固定；若没有这行代码，演示查询内容可能漂移
                self.assertIn("不要读取 cookies", prompt_text)  # 新增代码+GoogleHumanVisible: 断言真实 Chrome 演示仍禁止隐私读取；若没有这行代码，登录态环境可能越界
                self.assertIn("browser_click 成功", debug_log_text)  # 新增代码+GoogleHumanVisible: 断言日志必须证明点击成功；若没有这行代码，拟人演示可能没有实际点击
                self.assertIn("browser_type 成功", debug_log_text)  # 新增代码+GoogleHumanVisible: 断言日志必须证明输入成功；若没有这行代码，拟人演示可能没有实际打字
                self.assertIn("browser_press_key 成功", debug_log_text)  # 新增代码+GoogleHumanVisible: 断言日志必须证明按键成功；若没有这行代码，搜索可能没有提交
                self.assertIn("browser_screenshot 成功", debug_log_text)  # 新增代码+GoogleHumanVisible: 断言日志必须证明截图成功；若没有这行代码，用户无法复核桌面画面
                self.assertIn("REAL_CHROME_GOOGLE_HUMAN_SEARCH_OK", answer_text)  # 新增代码+GoogleHumanVisible: 断言最终回答必须包含固定成功标记；若没有这行代码，控制器难以确认 Google 拟人演示完成
            if scenario_name == "real_chrome_natural_weather_travel.json":  # 新增代码+通用真实浏览器Harness: 只对自然短 prompt 真实浏览器查询场景追加复用性检查；若没有这行代码，场景可能退化成又一个写死步骤的长 prompt
                prompt_text = "\n".join(scenario["prompt_lines"])  # 新增代码+通用真实浏览器Harness: 合并 prompt 行便于确认第一行就是用户自然需求；若没有这行代码，测试无法检查 prompt 是否足够自然
                debug_log_text = "\n".join(scenario["debug_log_contains"])  # 新增代码+通用真实浏览器Harness: 合并日志断言便于确认真实 Chrome 工具链；若没有这行代码，场景可能只看最终回答而不看真实操作证据
                answer_text = "\n".join(scenario["event_answer_contains"])  # 新增代码+通用真实浏览器Harness: 合并最终回答断言便于确认用户可见结果；若没有这行代码，验收可能漏掉真实浏览器动作摘要
                permission_policy = scenario["permission_policy"]  # 新增代码+通用真实浏览器Harness: 读取自然短 prompt 场景权限策略；若没有这行代码，后续无法验证默认拒绝和白名单
                allow_text = "\n".join(permission_policy["allow_contains"])  # 新增代码+通用真实浏览器Harness: 合并文本白名单便于检查启动 MCP；若没有这行代码，启动权限边界无法验证
                allow_tool_text = "\n".join(permission_policy["allow_tool_names"])  # 新增代码+通用真实浏览器Harness: 合并工具白名单便于确认点击输入工具被允许；若没有这行代码，场景可能无法肉眼演示搜索动作
                deny_tool_text = "\n".join(permission_policy["deny_tool_names"])  # 新增代码+通用真实浏览器Harness: 合并拒绝工具便于确认高风险读取被禁止；若没有这行代码，真实 profile 边界可能被弱化
                allow_url_text = "\n".join(permission_policy["allow_url_prefixes"])  # 新增代码+通用真实浏览器Harness: 合并 URL 白名单便于确认只打开 Google 首页；若没有这行代码，browser_open 可能访问未授权网站
                self.assertEqual(permission_policy["default_response"], "deny")  # 新增代码+通用真实浏览器Harness: 断言自然短 prompt 场景默认拒绝未知权限；若没有这行代码，模型请求非白名单工具可能被自动同意
                self.assertIn("启动 MCP server", allow_text)  # 新增代码+通用真实浏览器Harness: 断言启动 MCP 权限仍可自动放行；若没有这行代码，真实终端启动阶段可能卡住
                self.assertIn("browser_profile_status", allow_tool_text)  # 新增代码+通用真实浏览器Harness: 断言 profile 状态工具在白名单；若没有这行代码，真实 Chrome 连接前置检查无法执行
                self.assertIn("browser_connect_real_chrome", allow_tool_text)  # 新增代码+通用真实浏览器Harness: 断言真实 Chrome 连接工具在白名单；若没有这行代码，场景无法接入用户桌面 Chrome
                self.assertIn("browser_open", allow_tool_text)  # 新增代码+通用真实浏览器Harness: 断言打开 Google 首页工具在白名单；若没有这行代码，agent 无法进入搜索页面
                self.assertIn("browser_snapshot", allow_tool_text)  # 新增代码+通用真实浏览器Harness: 断言页面快照工具在白名单；若没有这行代码，agent 无法找搜索框或读取结果摘要
                self.assertIn("browser_click", allow_tool_text)  # 新增代码+通用真实浏览器Harness: 断言点击工具在白名单；若没有这行代码，用户看不到点击搜索框动作
                self.assertIn("browser_type", allow_tool_text)  # 新增代码+通用真实浏览器Harness: 断言输入工具在白名单；若没有这行代码，用户看不到拟人输入搜索词
                self.assertIn("browser_press_key", allow_tool_text)  # 新增代码+通用真实浏览器Harness: 断言按键工具在白名单；若没有这行代码，Google 搜索无法通过 Enter 提交
                self.assertIn("browser_wait", allow_tool_text)  # 新增代码+通用真实浏览器Harness: 断言等待工具在白名单；若没有这行代码，结果页可能还没加载就截图
                self.assertIn("browser_screenshot", allow_tool_text)  # 新增代码+通用真实浏览器Harness: 断言截图工具在白名单；若没有这行代码，真实浏览器动作缺少视觉证据
                self.assertIn("browser_evaluate", deny_tool_text)  # 新增代码+通用真实浏览器Harness: 断言 JS 执行工具被拒绝；若没有这行代码，场景可能越界读取页面内部状态
                self.assertIn("browser_network", deny_tool_text)  # 新增代码+通用真实浏览器Harness: 断言 network 工具被拒绝；若没有这行代码，场景可能读取网络请求细节
                self.assertIn("https://www.google.com", allow_url_text)  # 新增代码+通用真实浏览器Harness: 断言 browser_open 只允许 Google 域名前缀；若没有这行代码，真实 Chrome 可能被打开到未授权网站
                self.assertTrue(prompt_text.startswith("请使用真实浏览器，帮我查询3天后重庆的天气，并帮我做一下旅游攻略。"))  # 新增代码+通用真实浏览器Harness: 断言场景入口保留用户自然短 prompt；若没有这行代码，验收可能继续靠长工具说明作弊
                self.assertEqual(scenario.get("max_permission_sent_count"), 0)  # 新增代码+真实浏览器客户模式: 断言自然真实浏览器验收不允许任何 y/N 权限响应；若没有这行代码，客户模式可能退回多次 y 体验
                self.assertNotIn("permission_required", scenario["required_event_states"])  # 新增代码+真实浏览器客户模式: 断言自然场景不再等待权限提示；若没有这行代码，控制器仍会把 y 提示当成正常流程
                self.assertNotIn("permission_answered", scenario["required_event_states"])  # 新增代码+真实浏览器客户模式: 断言自然场景不再要求权限回答事件；若没有这行代码，测试无法证明用户不需要输入 y
                self.assertNotIn("必须使用 browser_click", prompt_text)  # 新增代码+通用真实浏览器Harness: 断言 prompt 本身不再写死点击工具步骤；若没有这行代码，无法证明通用 harness 在发挥作用
                self.assertNotIn("必须使用 browser_type", prompt_text)  # 新增代码+通用真实浏览器Harness: 断言 prompt 本身不再写死输入工具步骤；若没有这行代码，短 prompt 场景会退化成长 prompt
                self.assertIn("mcp__browser_automation__browser_profile_status", debug_log_text)  # 新增代码+通用真实浏览器Harness: 断言日志必须包含 profile 状态工具；若没有这行代码，真实 Chrome 前置检查可能漏掉
                self.assertIn("mcp__browser_automation__browser_connect_real_chrome", debug_log_text)  # 新增代码+通用真实浏览器Harness: 断言日志必须包含真实 Chrome 连接；若没有这行代码，独立浏览器冒充也可能通过
                self.assertIn("https://www.google.com", debug_log_text)  # 新增代码+通用真实浏览器Harness: 断言日志必须证明打开的是 Google；若没有这行代码，agent 可能绕到直接 API 查询
                self.assertIn("browser_click 成功", debug_log_text)  # 新增代码+通用真实浏览器Harness: 断言日志必须证明点击成功；若没有这行代码，真实可见动作可能缺失
                self.assertIn("browser_type 成功", debug_log_text)  # 新增代码+通用真实浏览器Harness: 断言日志必须证明输入成功；若没有这行代码，拟人输入动作可能缺失
                self.assertIn("browser_press_key 成功", debug_log_text)  # 新增代码+通用真实浏览器Harness: 断言日志必须证明按键成功；若没有这行代码，搜索提交可能缺失
                self.assertIn("重庆", debug_log_text)  # 新增代码+通用真实浏览器Harness: 断言日志包含用户查询城市；若没有这行代码，查询主题可能漂移
                self.assertIn("旅游攻略", debug_log_text)  # 新增代码+通用真实浏览器Harness: 断言日志包含攻略目标；若没有这行代码，最终任务可能只查天气
                self.assertIn("REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK", answer_text)  # 新增代码+通用真实浏览器Harness: 断言最终回答必须包含自然短 prompt 验收标记；若没有这行代码，控制器难以确认本轮完成
                self.assertIn("browser_screenshot", answer_text)  # 新增代码+通用真实浏览器Harness: 断言最终回答包含截图动作摘要；若没有这行代码，用户可见答案可能缺少视觉证据说明
    def test_acceptance_controller_script_uses_generic_event_protocol(self) -> None:  # 新增代码+AcceptanceController: 验证 controller.ps1 真的使用通用事件协议而不是写死单一场景；若没有这行代码，控制器可能退化成另一个专用脚本
        controller_path = (TEST_ROOT / "acceptance_controller") / "controller.ps1"  # 新增代码+AcceptanceController: 定位通用控制器脚本；若没有这行代码，测试无法读取脚本文本
        script_text = controller_path.read_text(encoding="utf-8")  # 新增代码+AcceptanceController: 按 UTF-8 读取脚本；若没有这行代码，中文注释或路径可能乱码
        self.assertIn("$ScenarioPath", script_text)  # 新增代码+AcceptanceController: 断言控制器支持外部场景路径；若没有这行代码，脚本无法复用不同场景
        self.assertIn("ConvertFrom-Json", script_text)  # 新增代码+AcceptanceController: 断言控制器从 JSON 加载场景；若没有这行代码，场景仍会硬编码在脚本里
        self.assertIn("LEARNING_AGENT_ACCEPTANCE_EVENT_LOG", script_text)  # 新增代码+AcceptanceController: 断言控制器启用 acceptance harness 事件日志；若没有这行代码，外部 agent 无法稳定观测状态
        self.assertIn("permission_required", script_text)  # 新增代码+AcceptanceController: 断言控制器处理权限事件；若没有这行代码，MCP 或工具权限会卡住
        self.assertIn("agent_ready_for_user_prompt", script_text)  # 新增代码+AcceptanceController: 断言控制器等待 ready 事件；若没有这行代码，输入时机仍然不可靠
        self.assertIn("final_answer_printed", script_text)  # 新增代码+AcceptanceController: 断言控制器等待最终回答事件；若没有这行代码，验收可能提前结束
        self.assertIn("debug_log_contains", script_text)  # 新增代码+AcceptanceController: 断言控制器读取场景里的日志断言；若没有这行代码，场景无法验证浏览器工具调用
        self.assertIn("event_payload_contains", script_text)  # 新增代码+Phase24AcceptancePayload: 断言控制器读取事件 payload 断言；若没有这行代码，/chrome 输出 false 也可能只靠状态事件误通过。
        self.assertIn("event_payload_checks", script_text)  # 新增代码+Phase24AcceptancePayload: 断言 result.json 暴露 payload 检查明细；若没有这行代码，失败时用户看不出缺哪个 true 字段。
        self.assertIn("permission_policy", script_text)  # 新增代码+RealChromeConnect: 断言控制器读取场景级权限策略；若没有这行代码，高风险 connect 场景只能继续无脑同意权限
        self.assertIn("permission_policy_decisions", script_text)  # 新增代码+RealChromeConnect: 断言控制器把权限决策写入 result.json；若没有这行代码，后续无法复盘每次 y/n 为什么发生
        self.assertIn("max_permission_sent_count", script_text)  # 新增代码+真实浏览器客户模式: 断言控制器支持权限响应次数上限；若没有这行代码，真实浏览器无 y 体验无法自动验收
        self.assertIn("permission_count_passed", script_text)  # 新增代码+真实浏览器客户模式: 断言 result 里包含权限次数断言结果；若没有这行代码，失败时无法看出是多弹了 y/N
        self.assertIn("Get-PermissionResponse", script_text)  # 新增代码+RealChromeConnect: 断言控制器通过函数计算权限响应；若没有这行代码，权限策略可能散落在主循环里难以审查
        self.assertIn("allow_tool_names", script_text)  # 新增代码+StructuredPermissionLedger: 断言控制器读取结构化工具白名单；若没有这行代码，真实 Chrome 场景仍只能靠文本 contains 放行
        self.assertIn("allow_url_prefixes", script_text)  # 新增代码+StructuredPermissionLedger: 断言控制器读取 URL 前缀白名单；若没有这行代码，browser_open 无法按参数 URL 精确限制
        self.assertIn("payload.tool_name", script_text)  # 新增代码+StructuredPermissionLedger: 断言控制器读取 permission_required 的结构化工具名；若没有这行代码，工具名白名单不会真正生效
        self.assertIn("payload.arguments", script_text)  # 新增代码+StructuredPermissionLedger: 断言控制器读取 permission_required 的结构化参数；若没有这行代码，URL 前缀限制无法检查真实参数
        self.assertIn("post_success_wait_seconds", script_text)  # 新增代码+GoogleHumanVisible: 断言控制器支持成功后可见停留；若没有这行代码，Google 演示窗口可能一闪而过
        self.assertIn("answer_text", script_text)  # 新增代码+FullAnswerEvent: 断言控制器会读取最终回答完整文本；若没有这行代码，长回答被 answer_preview 截断时会误判验收失败
        self.assertIn("$FinalAnswerText.Contains", script_text)  # 新增代码+FullAnswerEvent: 断言回答断言基于完整文本执行；若没有这行代码，Google 截图字段出现在后半段时仍会被误判缺失
        self.assertIn("GetForegroundWindow", script_text)  # 新增代码+TerminalFocusGuard: 断言控制器能读取当前前台窗口；若没有这行代码，AppActivate 假成功时 prompt 仍可能粘到 Photoshop 或浏览器
        self.assertIn("GetWindowThreadProcessId", script_text)  # 新增代码+TerminalFocusGuard: 断言控制器能确认前台窗口属于目标进程；若没有这行代码，脚本无法证明键盘输入会进真实终端
        self.assertIn("Test-AgentWindowForeground", script_text)  # 新增代码+TerminalFocusGuard: 断言控制器有专门的前台窗口校验函数；若没有这行代码，焦点检查会散落且容易再次退化
        self.assertIn("result.json", script_text)  # 新增代码+AcceptanceController: 断言控制器统一输出 result.json；若没有这行代码，外部 agent 无法用固定路径读取结果
    def test_interactive_acceptance_event_includes_full_final_answer_text(self) -> None:  # 新增代码+FullAnswerEvent: 验证真实终端最终回答事件会保存完整回答；若没有这行代码，长回答只能靠截断预览验收
        from learning_agent.observability.run_records import build_final_answer_event_payload  # 修改代码+ObservabilitySplit: 从新观测层导入最终回答 payload helper；若没有这行代码，测试仍会绑定主入口源码文本。
        payload = build_final_answer_event_payload("完整回答" * 300)  # 修改代码+ObservabilitySplit: 构造超过 500 字的回答来验证完整文本和预览；若没有这行代码，测试无法证明长回答不会被截断。
        self.assertEqual(payload["answer_text"], "完整回答" * 300)  # 修改代码+ObservabilitySplit: 断言完整回答字段保留原文；若没有这行代码，验收器只能检查预览并可能误报失败。
        self.assertEqual(payload["answer_preview"], ("完整回答" * 300)[:500])  # 修改代码+ObservabilitySplit: 断言短预览仍保留 500 字截断规则；若没有这行代码，result.json 会缺少便于快速查看的摘要。
    def test_observability_exports_acceptance_event_writer(self) -> None:  # 新增代码+ObservabilitySplit: 验证验收事件写入器已迁入 observability 层；若没有这行代码，阶段 14 可能无法证明唯一新入口是 acceptance_events。
        from learning_agent.observability.acceptance_events import emit_acceptance_event  # 新增代码+ObservabilitySplit: 从新 acceptance_events 模块导入事件写入函数；若没有这行代码，测试无法证明验收事件有独立观测层入口。
        self.assertTrue(callable(emit_acceptance_event))  # 新增代码+ObservabilitySplit: 断言导出的事件写入器可调用；若没有这行代码，导入到非函数对象也可能误通过。
    def test_permission_denial_allows_different_arguments_to_request_again(self) -> None:  # 新增代码+ToolPolicyV2: 验证同一工具换成不同清洗后参数时必须重新请求权限；若没有这行代码，拒绝 key 退化成只按工具名会误拒合法新请求
        with mock.patch.dict(os.environ, {"LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS": "0"}, clear=False):  # 修改代码+AcceptanceStdoutNoiseControl: 本测试必须走人工权限回调路径；若没有这行代码，开发期危险模式会自动放行并掩盖拒绝记忆逻辑。
            self._run_permission_denial_allows_different_arguments_to_request_again_case()  # 修改代码+AcceptanceStdoutNoiseControl: 把原用例主体放进安全模式辅助函数；若没有这行代码，环境保护范围不清楚。
    def _run_permission_denial_allows_different_arguments_to_request_again_case(self) -> None:  # 修改代码+AcceptanceStdoutNoiseControl: 函数段开始，执行不同参数拒绝记忆的真实用例主体；若没有这段代码，测试无法在显式安全模式中复用原断言。本段由公开测试方法调用，段落到断言结束。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolPolicyV2: 创建临时工作区隔离测试文件；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolPolicyV2: 把临时目录转成 Path 传给 agent；若没有这行代码，路径语义不够稳定
            fake_client = FakeMcpClient()  # 新增代码+ToolPolicyV2: 创建默认 echo MCP 工具供不同参数权限测试；若没有这行代码，无法观察第二次允许后是否真实调用
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+ToolPolicyV2: 创建含 demo server 的 MCP registry；若没有这行代码，agent 无法发现并调用目标 MCP 工具
            permission_requests: list[str] = []  # 新增代码+ToolPolicyV2: 记录权限请求文本；若没有这行代码，无法断言不同参数会重新 ask_permission
            def ask_permission(action: str) -> bool:  # 新增代码+ToolPolicyV2: 定义按参数内容控制结果的权限回调；若没有这行代码，测试无法先拒绝旧参数再允许新参数
                permission_requests.append(action)  # 新增代码+ToolPolicyV2: 保存本次权限请求；若没有这行代码，测试无法统计工具权限请求次数
                if action.startswith("启动 MCP server"):  # 新增代码+ToolPolicyV2: 判断当前请求是否只是启动 MCP server；若没有这行代码，agent 初始化阶段会被误拒绝
                    return True  # 新增代码+ToolPolicyV2: 允许启动 fake MCP server；若没有这行代码，后续工具 catalog 里不会有目标 echo 工具
                return '"different"' in action  # 新增代码+ToolPolicyV2: 只允许参数 text=different 的工具调用；若没有这行代码，第二次不同参数无法进入真实 MCP 调用路径
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=ask_permission, mcp_tool_registry=registry)  # 新增代码+ToolPolicyV2: 创建带可控权限回调的 agent；若没有这行代码，测试没有执行主体
            self._select_tool_for_test(agent, "mcp__demo__echo")  # 新增代码+ToolPolicyV2: 先加载 deferred MCP 工具；若没有这行代码，执行会停在未 select 门禁而不是权限拒绝/允许路径
            first = agent._execute_tool(ToolCall(name="mcp__demo__echo", arguments={"text": "deny"}))  # 新增代码+ToolPolicyV2: 第一次用 text=deny 触发用户拒绝并写入拒绝记忆；若没有这行代码，不会建立要对比的拒绝记录
            second = agent._execute_tool(ToolCall(name="mcp__demo__echo", arguments={"text": "different"}))  # 新增代码+ToolPolicyV2: 第二次用不同清洗后参数重新请求权限并允许执行；若没有这行代码，无法验证不同参数不会被旧拒绝误伤
            self.assertIn("拒绝", first)  # 新增代码+ToolPolicyV2: 断言第一次真实走到用户拒绝分支；若没有这行代码，测试可能没有建立拒绝记忆
            self.assertIn("called echo: different", second)  # 新增代码+ToolPolicyV2: 断言第二次不同参数获得允许并返回真实 MCP 结果；若没有这行代码，误拒不同参数不会被发现
            self.assertEqual(len([item for item in permission_requests if item.startswith("调用 MCP 工具")]), 2)  # 新增代码+ToolPolicyV2: 断言两个不同参数都各自进入工具权限询问；若没有这行代码，key 只按工具名去重会漏测
            self.assertEqual(fake_client.calls, [("echo", {"text": "different"})])  # 新增代码+ToolPolicyV2: 断言只有第二次允许的不同参数被真实转发；若没有这行代码，无法证明不同参数请求没有被拒绝记忆拦住
    def test_agent_requires_permission_before_writing_file(self) -> None:  # 作用: 测试代理在写文件前是否会请求/尊重权限；若省略: 无法覆盖权限拒绝路径
        with tempfile.TemporaryDirectory() as raw_dir:  # 作用: 为该测试创建隔离的临时目录，避免文件残留或相互影响；若省略: 可能污染工作目录
            workspace = Path(raw_dir)  # 作用: 转换为 Path 以便路径拼接与读写操作；若省略: 需手动管理字符串路径
            target_file = workspace / "blocked.txt"  # 作用: 定义预期被拒绝写入的目标路径；若省略: 无法断言文件是否被创建
            model = ToolCallingFakeModel(  # 作用: 构造一个假模型，模拟请求写文件的场景以验证权限控制
                [
                    ModelMessage(
                        text="",
                        tool_calls=[
                            ToolCall(
                                name="write_file",  # 作用: 模拟模型要求执行的工具类型为写文件；若改为其他工具，测试场景将改变
                                arguments={"path": str(target_file), "content": "不应该被写入"},  # 作用: 提供写入的路径与内容参数，直接驱动写操作请求
                            )
                        ],
                    ),
                    ModelMessage(text="写入被拒绝，我不会继续强行操作。"),  # 作用: 模拟在权限被拒绝后的模型回复，用于断言代理的输出
                ]
            )
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: False)  # 作用: 注入一个总是拒绝的权限回调以测试拒绝路径；若改为 True 写入会被允许
            answer = agent.run("请写文件")  # 作用: 触发代理流程，使其接收假模型的写入请求并执行权限检查；若省略: 无法验证权限逻辑
            self.assertIn("拒绝", answer)  # 作用: 验证代理的回答包含拒绝字样，保证向用户传达了权限被拒的状态；若省略: 不能确认代理是否对用户做出正确反馈
            self.assertFalse(target_file.exists())  # 作用: 确认目标文件未被创建，保证代理在权限被拒绝时不会执行写入副作用；若省略: 即使代理表面上拒绝也无法验证没有实际写入


if __name__ == "__main__":  # Stage14: allow running this test module directly.
    unittest.main()  # Stage14: start unittest when executed as a script.


