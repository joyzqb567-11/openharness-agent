"Browser execution, real Chrome helper, and search chain tests."  # Stage14: this file owns the browser_harness test group.
from __future__ import annotations  # Stage14: keep annotations lazy after test split.
import unittest  # Stage14: keep direct unittest execution available.
from learning_agent.tests.support import *  # Stage14: import shared helpers and dependencies for copied tests.

class BrowserHarnessTests(LearningAgentTestBase):  # Stage14: unittest discovers this concrete modular test class.
    def test_real_chrome_skill_references_generic_search_workflow_rule(self) -> None:  # 新增代码+通用真实浏览器Harness: 验证 real_chrome skill 指向通用搜索流程子规则；若没有这行代码，模型读 skill 后不知道自然查询该怎么走
        skill_text = self._skill_file("real_chrome").read_text(encoding="utf-8")  # 新增代码+通用真实浏览器Harness: 读取真实 real_chrome SKILL.md；若没有这行代码，测试不会覆盖交付文档
        rule_path = self._skill_rule_file("real_chrome", "search_task_workflow.md")  # 新增代码+通用真实浏览器Harness: 定位计划新增的通用搜索流程规则文件；若没有这行代码，后续断言没有目标路径
        self.assertIn("search_task_workflow.md", skill_text)  # 新增代码+通用真实浏览器Harness: 断言顶层 skill 索引到通用搜索规则；若没有这行代码，模型可能只读 profile 安全规则就停下
        self.assertTrue(rule_path.exists())  # 新增代码+通用真实浏览器Harness: 断言通用搜索规则文件存在；若没有这行代码，文档索引可能指向不存在文件
        rule_text = rule_path.read_text(encoding="utf-8")  # 新增代码+通用真实浏览器Harness: 读取通用搜索规则正文；若没有这行代码，无法验证规则是否真通用
        self.assertIn("https://www.google.com/", rule_text)  # 新增代码+通用真实浏览器Harness: 断言规则要求从 Google 首页进入；若没有这行代码，真实浏览器任务可能继续直达结果页
        self.assertIn("browser_click", rule_text)  # 新增代码+通用真实浏览器Harness: 断言规则保留点击动作；若没有这行代码，用户肉眼可见交互可能缺失
        self.assertIn("browser_type", rule_text)  # 新增代码+通用真实浏览器Harness: 断言规则保留输入动作；若没有这行代码，模型可能直接拼搜索 URL
        self.assertIn("browser_press_key", rule_text)  # 新增代码+通用真实浏览器Harness: 断言规则保留按键动作；若没有这行代码，提交搜索的可见动作可能缺失
        self.assertIn("会议", rule_text)  # 新增代码+通用真实浏览器Harness: 断言规则覆盖会议查询；若没有这行代码，能力可能被写成天气专用
        self.assertIn("酒店", rule_text)  # 新增代码+通用真实浏览器Harness: 断言规则覆盖酒店查询；若没有这行代码，旅游和预订类任务可能没有复用边界
        self.assertIn("航班", rule_text)  # 新增代码+通用真实浏览器Harness: 断言规则覆盖航班查询；若没有这行代码，出行类任务可能没有复用边界
        self.assertIn("资料", rule_text)  # 新增代码+通用真实浏览器Harness: 断言规则覆盖资料查询；若没有这行代码，通用研究任务可能没有复用入口
    def test_reading_real_chrome_skill_unlocks_connect_after_profile_status(self) -> None:  # 新增代码+真实浏览器自动化: 验证真实 Chrome skill 只在 profile status 后开放 connect；若没有这行代码，真实登录态工具可能过早暴露或永远不可用
        workspace = self._project_root()  # 新增代码+真实浏览器自动化: 使用真实项目根目录读取 real_chrome skill；若没有这行代码，测试不能覆盖交付给 agent 的真实提示词路径
        fake_client = FakeMcpClient(tools=[{"name": "browser_profile_status", "description": "Status", "inputSchema": {"type": "object", "properties": {}}}, {"name": "browser_connect_real_chrome", "description": "Connect", "inputSchema": {"type": "object", "properties": {"confirm_real_profile": {"type": "boolean"}}, "required": ["confirm_real_profile"]}}], result_prefix="real_chrome_connected=true")  # 新增代码+真实浏览器自动化: 构造 profile status 和 connect 两个假工具；若没有这行代码，workflow gate 无法被稳定测试
        registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+真实浏览器自动化: 使用 browser_automation server 名触发真实 Chrome 策略映射；若没有这行代码，connect 不会带 skill/workflow gate
        agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry, debug_enabled=False)  # 新增代码+真实浏览器自动化: 创建自动授权且不写调试日志的测试 agent；若没有这行代码，无法执行 MCP workflow
        initial_tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+真实浏览器自动化: 获取初始工具池；若没有这行代码，无法确认真实 Chrome 前置状态工具是否可见
        self.assertIn("mcp__browser_automation__browser_profile_status", initial_tool_names)  # 新增代码+真实浏览器自动化: 断言只读 profile status 首轮可见；若没有这行代码，模型可能不知道先做安全检查
        self.assertNotIn("mcp__browser_automation__browser_connect_real_chrome", initial_tool_names)  # 新增代码+真实浏览器自动化: 断言 connect 首轮不可见；若没有这行代码，高风险真实 profile 连接可能直接暴露
        agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/tool_list.md"}))  # 新增代码+真实浏览器自动化: 先读取动态提示词总索引；若没有这行代码，real_chrome SKILL.md 会被层级门控拒绝
        skill_output = agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/real_chrome/SKILL.md"}))  # 新增代码+真实浏览器自动化: 读取真实 Chrome skill 以满足 skill gate；若没有这行代码，connect 不应进入加载候选
        self.assertIn("profile_safety.md", skill_output)  # 新增代码+真实浏览器自动化: 断言真实 Chrome skill 读取成功并指向安全规则；若没有这行代码，测试可能继续基于错误读取结果判断
        before_status_tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+真实浏览器自动化: 读取 skill 后但 status 前的工具池；若没有这行代码，无法验证 workflow gate 仍在生效
        self.assertNotIn("mcp__browser_automation__browser_connect_real_chrome", before_status_tool_names)  # 新增代码+真实浏览器自动化: 断言只读 skill 还不会直接开放 connect；若没有这行代码，profile status 前置要求可能失效
        status_output = agent._execute_tool(ToolCall(name="mcp__browser_automation__browser_profile_status", arguments={}))  # 新增代码+真实浏览器自动化: 执行只读 profile status 满足 workflow；若没有这行代码，connect 应该继续不可见
        self.assertIn("real_chrome_connected=true browser_profile_status", status_output)  # 新增代码+真实浏览器自动化: 断言 status 调用成功并来自 fake MCP；若没有这行代码，workflow 解锁可能基于失败结果推进
        after_status_tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+真实浏览器自动化: 读取 profile status 后的工具池；若没有这行代码，无法确认 workflow 完成后 schema 是否更新
        self.assertIn("mcp__browser_automation__browser_connect_real_chrome", after_status_tool_names)  # 新增代码+真实浏览器自动化: 断言 connect 在 skill 和 status 都满足后可见；若没有这行代码，真实浏览器功能会卡在最后一步
        connect_output = agent._execute_tool(ToolCall(name="mcp__browser_automation__browser_connect_real_chrome", arguments={"confirm_real_profile": True}))  # 新增代码+真实浏览器自动化: 调用解锁后的真实 Chrome connect；若没有这行代码，只检查可见性无法证明执行层可用
        self.assertIn("real_chrome_connected=true browser_connect_real_chrome", connect_output)  # 新增代码+真实浏览器自动化: 断言 connect 调用成功；若没有这行代码，真实场景仍可能在执行阶段失败
        self.assertEqual(fake_client.calls[-1][0], "browser_connect_real_chrome")  # 新增代码+真实浏览器自动化: 断言最终转发给 MCP 的原始工具名正确；若没有这行代码，真实 MCP server 可能无法识别请求
    def test_real_chrome_profile_manager_finds_windows_candidates(self) -> None:  # 新增代码+RealChrome测试: 验证 Windows Chrome 路径候选生成；若省略: 后续路径识别没有回归保护
        with tempfile.TemporaryDirectory() as tmp:  # 新增代码+RealChrome测试: 使用临时目录模拟 Windows 环境；若省略: 测试会依赖真实用户机器
            root = Path(tmp)  # 新增代码+RealChrome测试: 把临时目录转成 Path；若省略: 后续路径拼接会不直观
            chrome_path = root / "Program Files" / "Google" / "Chrome" / "Application" / "chrome.exe"  # 新增代码+RealChrome测试: 构造模拟 Chrome exe 路径；若省略: manager 没有可发现的 chrome.exe
            user_data_dir = root / "LocalAppData" / "Google" / "Chrome" / "User Data"  # 新增代码+RealChrome测试: 构造模拟 User Data 目录；若省略: manager 没有可发现的 profile 根目录
            chrome_path.parent.mkdir(parents=True)  # 新增代码+RealChrome测试: 创建 chrome.exe 父目录；若省略: 写入文件会失败
            chrome_path.write_text("", encoding="utf-8")  # 新增代码+RealChrome测试: 创建空 chrome.exe 测试文件；若省略: 路径存在性检查会失败
            user_data_dir.mkdir(parents=True)  # 新增代码+RealChrome测试: 创建模拟 User Data 目录；若省略: profile 路径存在性检查会失败
            manager = ChromeProfileManager(program_files=root / "Program Files", program_files_x86=root / "Program Files (x86)", local_app_data=root / "LocalAppData")  # 新增代码+RealChrome测试: 注入模拟系统路径；若省略: 测试会读取真实系统环境
            self.assertEqual(chrome_path, manager.find_chrome_path())  # 新增代码+RealChrome测试: 断言能找到模拟 chrome.exe；若省略: 路径识别回归不会暴露
            self.assertEqual(user_data_dir, manager.find_user_data_dir())  # 新增代码+RealChrome测试: 断言能找到模拟 User Data；若省略: profile 识别回归不会暴露
    def test_real_chrome_profile_manager_uses_powershell_when_python_denies_user_data(self) -> None:  # 修改代码+RealChromePathFallback测试: 验证 Python 无权 stat User Data 时会用 Test-Path 补证；若没有这行代码，真实 Chrome profile 会继续被误判缺失
        manager = ChromeProfileManager(local_app_data=Path(r"C:\Users\demo\AppData\Local"))  # 修改代码+RealChromePathFallback测试: 构造接近真实 Windows 的 LocalAppData；若没有这行代码，测试无法得到目标 User Data 候选
        expected_user_data_dir = Path(r"C:\Users\demo\AppData\Local\Google\Chrome\User Data")  # 修改代码+RealChromePathFallback测试: 保存期望返回的 User Data 路径；若没有这行代码，断言只能写成难读的内联表达式
        fallback_result = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout="true\r\n", stderr="")  # 修改代码+RealChromePathFallback测试: 模拟 PowerShell 确认目录存在；若没有这行代码，无法稳定复现本机 sandbox 权限场景
        with mock.patch("learning_agent.browser_real_chrome.Path.exists", side_effect=PermissionError("denied")):  # 修改代码+RealChromePathFallback测试: 模拟 Python Path.exists 被 Windows 拒绝；若没有这行代码，测试会依赖真实机器权限
            with mock.patch("learning_agent.browser_real_chrome.subprocess.run", return_value=fallback_result) as run_mock:  # 修改代码+RealChromePathFallback测试: 模拟 Test-Path fallback 成功并记录命令；若没有这行代码，测试无法确认 fallback 被调用
                self.assertEqual(expected_user_data_dir, manager.find_user_data_dir())  # 修改代码+RealChromePathFallback测试: 断言 fallback 确认存在后返回 User Data；若没有这行代码，误判缺失不会被测试发现
                fallback_command = run_mock.call_args.args[0]  # 修改代码+RealChromePathFallback测试: 取出 PowerShell 命令参数；若没有这行代码，无法检查命令是否安全使用 Test-Path
                fallback_command_text = " ".join(str(part) for part in fallback_command)  # 修改代码+RealChromePathFallback测试: 把命令列表转成可搜索文本；若没有这行代码，断言需要依赖列表下标细节
                self.assertIn("Test-Path", fallback_command_text)  # 修改代码+RealChromePathFallback测试: 断言使用只读路径检测；若没有这行代码，fallback 可能改成更高风险命令也不报红
                self.assertIn(str(expected_user_data_dir), fallback_command_text)  # 修改代码+RealChromePathFallback测试: 断言带空格的 User Data 路径留在被引用的脚本文本里；若没有这行代码，空格路径回归不会被发现
                self.assertNotIn("$args[0]", fallback_command_text)  # 修改代码+RealChromePathFallback测试: 断言不再依赖 powershell -Command 下不稳定的 $args 传参；若没有这行代码，真实终端环境可能再次误判目录缺失
    def test_real_chrome_profile_manager_skips_inaccessible_candidates(self) -> None:  # 修改代码+RealChrome测试: 验证无权访问且 fallback 也不能确认时诊断不崩溃；若没有这行代码，mcp-doctor 的权限拒绝回归不会稳定复现
        manager = ChromeProfileManager(local_app_data=Path(r"C:\blocked"))  # 修改代码+RealChrome测试: 构造只关心 local_app_data 的路径管理器；若没有这行代码，测试没有可调用的候选目录来源
        fallback_result = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout="", stderr="")  # 修改代码+RealChromePathFallback测试: 模拟 Test-Path 没有确认目录存在；若没有这行代码，跳过分支没有稳定输入
        with mock.patch("learning_agent.browser_real_chrome.Path.exists", side_effect=PermissionError("denied")):  # 修改代码+RealChrome测试: 模拟 Windows 对 Chrome User Data 拒绝访问；若没有这行代码，测试会依赖真实机器权限状态
            with mock.patch("learning_agent.browser_real_chrome.subprocess.run", return_value=fallback_result):  # 修改代码+RealChromePathFallback测试: 让 fallback 明确返回空结果；若没有这行代码，测试会调用真实 PowerShell
                self.assertIsNone(manager.find_user_data_dir())  # 修改代码+RealChrome测试: 断言无法确认存在时返回 None 而不是抛异常；若没有这行代码，doctor 崩溃问题无法被红灯保护
    def test_real_chrome_process_detection_reads_tasklist(self) -> None:  # 新增代码+RealChrome测试: 验证 Chrome 运行检测只依赖 tasklist 摘要；若省略: profile 锁冲突边界没有测试
        completed = subprocess.CompletedProcess(args=["tasklist"], returncode=0, stdout='"chrome.exe","1234","Console","1","100 K"\n', stderr="")  # 新增代码+RealChrome测试: 模拟 tasklist 发现 chrome.exe；若省略: 测试无法稳定模拟 Chrome 正在运行
        with mock.patch("learning_agent.browser_real_chrome.subprocess.run", return_value=completed) as run_mock:  # 修改代码+RealChrome测试: 使用显式导入的 mock 替换 subprocess.run 并保留 mock；若省略: 测试无法确认 helper 真调用了 tasklist
            manager = ChromeProfileManager()  # 新增代码+RealChrome测试: 创建默认 manager；若省略: 无法调用 chrome_is_running
            self.assertTrue(manager.chrome_is_running())  # 新增代码+RealChrome测试: 断言检测到 Chrome 正在运行；若省略: 运行检测误判不会暴露
            run_mock.assert_called_once()  # 新增代码+RealChrome测试: 断言只调用一次系统进程查询；若省略: helper 可能没有查询 tasklist 或重复查询也不暴露
            tasklist_command = run_mock.call_args.args[0]  # 新增代码+RealChrome测试: 取出传给 subprocess.run 的命令参数；若省略: 无法检查是否真的查 chrome.exe
            tasklist_command_text = tasklist_command if isinstance(tasklist_command, str) else " ".join(str(part) for part in tasklist_command)  # 新增代码+RealChrome测试: 把命令统一成可搜索文本；若省略: 字符串命令和列表命令只能兼容一种
            self.assertIn("tasklist", tasklist_command_text)  # 修改代码+RealChrome测试: 断言命令包含 tasklist；若省略: helper 可能调用了错误系统命令
            self.assertIn("IMAGENAME eq chrome.exe", tasklist_command_text)  # 修改代码+RealChrome测试: 断言 tasklist 过滤 chrome.exe；若省略: helper 可能扫描全部进程导致误判或低效
    def test_real_chrome_process_detection_falls_back_when_tasklist_is_denied(self) -> None:  # 新增代码+RealChromeTasklistFallback测试: 验证 tasklist 被系统拒绝时会用 Get-Process 复查；若省略: 真实终端验收会把 Access denied 误判为 Chrome 正在运行
        denied = subprocess.CompletedProcess(args=["tasklist"], returncode=1, stdout="", stderr="ERROR: Access denied")  # 新增代码+RealChromeTasklistFallback测试: 模拟 tasklist 在受限环境返回拒绝访问；若省略: 无法复现本轮验收失败根因
        no_chrome = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout="", stderr="")  # 新增代码+RealChromeTasklistFallback测试: 模拟 Get-Process 没有发现 chrome 进程；若省略: 无法证明 fallback 能解除误拦截
        with mock.patch("learning_agent.browser_real_chrome.subprocess.run", side_effect=[denied, no_chrome]) as run_mock:  # 新增代码+RealChromeTasklistFallback测试: 按顺序返回 tasklist 失败和 fallback 成功；若省略: 测试无法确认双层检测流程
            manager = ChromeProfileManager()  # 新增代码+RealChromeTasklistFallback测试: 创建默认 manager；若省略: 无法调用待测检测方法
            self.assertFalse(manager.chrome_is_running())  # 新增代码+RealChromeTasklistFallback测试: 断言无 Chrome 时不能因为 tasklist 失败而误报运行中；若省略: 回归不会被测试拦住
            self.assertEqual(run_mock.call_count, 2)  # 新增代码+RealChromeTasklistFallback测试: 断言先查 tasklist 再查 fallback；若省略: helper 可能没有执行补充检测
            fallback_command = run_mock.call_args_list[1].args[0]  # 新增代码+RealChromeTasklistFallback测试: 取出第二次调用命令；若省略: 无法确认 fallback 用的是 Chrome 进程检测
            fallback_command_text = " ".join(str(part) for part in fallback_command)  # 新增代码+RealChromeTasklistFallback测试: 把命令列表合成文本方便断言；若省略: 测试只能依赖不可读的列表结构
            self.assertIn("Get-Process chrome", fallback_command_text)  # 新增代码+RealChromeTasklistFallback测试: 断言 fallback 精确检查 chrome 进程；若省略: fallback 可能误查其他进程
    def test_real_chrome_diagnostic_reports_available_when_running_chrome_has_cdp(self) -> None:  # 新增代码+RealChrome已有CDP诊断: 验证已运行 Chrome 带可信 CDP 时诊断为可连接；若省略: mcp-doctor 会继续误导模型要求用户关闭 Chrome
        from learning_agent.browser_real_chrome import diagnose_real_chrome_environment  # 新增代码+RealChrome已有CDP诊断: 导入被测诊断入口；若省略: 测试无法覆盖 mcp-doctor 使用的真实函数
        with mock.patch("learning_agent.browser_real_chrome.ChromeProfileManager.find_chrome_path", return_value=Path(r"C:\Chrome\chrome.exe")):  # 新增代码+RealChrome已有CDP诊断: 模拟 Chrome 路径存在；若省略: 测试会依赖当前机器安装位置
            with mock.patch("learning_agent.browser_real_chrome.ChromeProfileManager.find_user_data_dir", return_value=Path(r"C:\Chrome\User Data")):  # 新增代码+RealChrome已有CDP诊断: 模拟 User Data 路径存在；若省略: 测试会依赖当前机器 profile 目录
                with mock.patch("learning_agent.browser_real_chrome.ChromeProfileManager.chrome_is_running", return_value=True):  # 新增代码+RealChrome已有CDP诊断: 模拟桌面 Chrome 已经运行；若省略: 无法复现验收失败边界
                    with mock.patch("learning_agent.browser_real_chrome._is_loopback_port_available", return_value=False):  # 新增代码+RealChrome已有CDP诊断: 模拟 9222 已被占用；若省略: 无法证明端口占用不一定是坏事
                        with mock.patch("learning_agent.browser_real_chrome.wait_for_cdp_endpoint", return_value=True) as cdp_mock:  # 新增代码+RealChrome已有CDP诊断: 模拟占用者就是可信 Chrome CDP；若省略: 测试仍会走旧 needs_user_action 语义
                            diagnostic = diagnose_real_chrome_environment(TEST_ROOT)  # 新增代码+RealChrome已有CDP诊断: 执行被测诊断；若省略: 后续断言没有对象来源
        self.assertEqual(diagnostic.status, "available")  # 新增代码+RealChrome已有CDP诊断: 断言已有 CDP 可直接使用；若省略: mcp-doctor 误报不会被发现
        self.assertTrue(diagnostic.chrome_running)  # 新增代码+RealChrome已有CDP诊断: 保留 Chrome 正在运行这个事实；若省略: 报告可能隐藏真实桌面状态
        self.assertFalse(diagnostic.port_available)  # 新增代码+RealChrome已有CDP诊断: 保留端口被占用这个事实；若省略: 报告会误说 9222 空闲
        self.assertTrue(any("CDP" in message for message in diagnostic.messages))  # 新增代码+RealChrome已有CDP诊断: 断言提示说明已有 CDP 可接管；若省略: 用户看不到为什么此时可用
        self.assertFalse(any("先关闭 Chrome" in message for message in diagnostic.messages))  # 新增代码+RealChrome已有CDP诊断: 断言不再误导用户关闭浏览器；若省略: 客户体验问题可能回归
        cdp_mock.assert_called_once_with(9222, timeout_seconds=1.0)  # 新增代码+RealChrome已有CDP诊断: 断言诊断检查默认 CDP 端口；若省略: 可能检查错端口还误报可用
    def test_real_chrome_debug_command_uses_loopback_only(self) -> None:  # 新增代码+RealChrome测试: 验证调试命令只绑定 127.0.0.1；若省略: debug port 可能被错误暴露
        command = build_chrome_debug_command(Path("C:/Chrome/chrome.exe"), Path("C:/Users/demo/AppData/Local/Google/Chrome/User Data"), "Default", 9333)  # 新增代码+RealChrome测试: 构造启动命令；若省略: 无法检查命令参数
        self.assertIn("--remote-debugging-address=127.0.0.1", command)  # 新增代码+RealChrome测试: 断言只绑定本机地址；若省略: 局域网暴露风险不会被测试发现
        self.assertNotIn("--remote-debugging-address=0.0.0.0", command)  # 新增代码+RealChrome测试: 断言不会绑定所有网卡；若省略: 调试端口可能暴露到局域网仍不报红
        address_args = [argument for argument in command if argument.startswith("--remote-debugging-address=")]  # 新增代码+RealChrome测试: 收集所有调试地址参数；若省略: 多个地址参数覆盖 loopback 的风险不会暴露
        self.assertEqual(["--remote-debugging-address=127.0.0.1"], address_args)  # 新增代码+RealChrome测试: 断言地址参数唯一且等于本机回环；若省略: helper 可能同时传入危险地址
        self.assertIn("--remote-debugging-port=9333", command)  # 新增代码+RealChrome测试: 断言使用指定端口；若省略: 端口参数回归不会暴露
        self.assertIn("--profile-directory=Default", command)  # 新增代码+RealChrome测试: 断言 profile 名称进入命令；若省略: 可能启动错 profile
    def test_browser_evaluate_blocks_sensitive_script_in_real_chrome_mode(self) -> None:  # 新增代码+RealChrome安全测试: 验证真实 Chrome 模式会在取页面前拒绝敏感脚本；若没有这行代码，document.cookie 可能接触真实登录态页面而不被红灯发现
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome安全测试: 导入被测浏览器自动化 server；若没有这行代码，测试无法直接调用 browser_evaluate 入口
        server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome安全测试: 创建不启动真实浏览器的 server 实例；若没有这行代码，后续没有可布置的会话状态
        server.session_mode = "real_chrome"  # 新增代码+RealChrome安全测试: 把 server 切到真实 Chrome 模式；若没有这行代码，安全策略不会按真实登录态边界执行
        server.audit_logger = mock.Mock()  # 新增代码+RealChrome安全测试: 用 fake audit logger 观察审计写入；若没有这行代码，测试可能写真实审计文件且无法断言载荷
        with mock.patch.object(server, "current_page", side_effect=AssertionError("安全检查前不应取页面")) as current_page_mock:  # 新增代码+RealChrome安全测试: 把 current_page 设为一调用就失败；若没有这行代码，测试无法证明拒绝发生在页面访问之前
            with self.assertRaisesRegex(RuntimeError, "敏感|拒绝|不允许"):  # 新增代码+RealChrome安全测试: 断言敏感脚本会以中文安全错误拒绝；若没有这行代码，错误类型或拒绝文案回归不会暴露
                server.browser_evaluate({"script": "document.cookie"})  # 新增代码+RealChrome安全测试: 调用敏感脚本入口触发拒绝；若没有这行代码，测试不会真正覆盖 browser_evaluate
        self.assertNotEqual(server.last_safety_refusal, "无")  # 新增代码+RealChrome安全测试: 断言最近安全拒绝状态被更新；若没有这行代码，状态工具可能仍说没有拒绝历史
        self.assertIn("敏感", server.last_safety_refusal)  # 新增代码+RealChrome安全测试: 断言拒绝原因说明敏感风险；若没有这行代码，用户可能看不到为什么被拦截
        server.audit_logger.record.assert_called_once()  # 新增代码+RealChrome安全测试: 断言安全拒绝会写一次审计；若没有这行代码，高风险拒绝可能没有最小留痕
        self.assertEqual(server.audit_logger.record.call_args.args[0], "safety_refusal")  # 新增代码+RealChrome安全测试: 断言审计事件名是 safety_refusal；若没有这行代码，审计分类错误不会暴露
        self.assertEqual(server.audit_logger.record.call_args.args[1]["tool_name"], "browser_evaluate")  # 新增代码+RealChrome安全测试: 断言审计只标明工具来源；若没有这行代码，后续排查不知道哪个工具触发拒绝
        self.assertIn("敏感", server.audit_logger.record.call_args.args[1]["reason"])  # 新增代码+RealChrome安全测试: 断言审计写安全原因摘要；若没有这行代码，审计可能缺少可读拒绝原因
        self.assertNotIn("document.cookie", str(server.audit_logger.record.call_args.args[1]))  # 新增代码+RealChrome安全测试: 断言审计不写脚本全文；若没有这行代码，cookie 读取脚本可能被记录到日志里
        current_page_mock.assert_not_called()  # 新增代码+RealChrome安全测试: 断言安全拒绝前没有取页面；若没有这行代码，真实页面可能已经被接触才拒绝
    def test_browser_evaluate_allows_visible_text_script_in_real_chrome_mode(self) -> None:  # 新增代码+RealChrome安全测试: 验证真实 Chrome 模式允许读取可见文本这类低风险脚本；若没有这行代码，策略可能过度拦截正常页面摘要
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome安全测试: 导入被测 server 类；若没有这行代码，无法直接测试 browser_evaluate 成功路径
        server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome安全测试: 创建 server 实例且不启动真实 Chrome；若没有这行代码，测试没有可操作对象
        server.session_mode = "real_chrome"  # 新增代码+RealChrome安全测试: 设置真实 Chrome 模式以覆盖新增安全检查分支；若没有这行代码，只会测试默认独立 Chromium 行为
        server.audit_logger = mock.Mock()  # 新增代码+RealChrome安全测试: 替换审计 logger 便于断言没有安全拒绝；若没有这行代码，测试不能稳定观察审计行为
        fake_session = mock.Mock()  # 新增代码+RealChrome安全测试: 创建 fake CDP session 避免打开真实浏览器；若没有这行代码，browser_evaluate 会尝试使用真实页面调试会话
        fake_session.send.return_value = {"result": {"value": "visible text"}}  # 新增代码+RealChrome安全测试: 模拟脚本返回可见文本；若没有这行代码，成功路径没有稳定结果可断言
        fake_page = mock.Mock()  # 新增代码+RealChrome安全测试: 创建 fake page 作为 current_page 返回值；若没有这行代码，测试需要真实 Playwright 页面
        fake_page.title.return_value = "Fake Page"  # 新增代码+RealChrome安全测试: 提供页面标题给返回文本；若没有这行代码，返回格式化会拿不到标题
        fake_page.url = "https://example.test"  # 新增代码+RealChrome安全测试: 提供安全的假 URL 摘要；若没有这行代码，返回文本缺少页面地址
        fake_page.context.new_cdp_session.return_value = fake_session  # 新增代码+RealChrome安全测试: 让 evaluate 使用 fake CDP session；若没有这行代码，测试会触发真实浏览器能力
        with mock.patch.object(server, "current_page", return_value=("page-1", fake_page)):  # 新增代码+RealChrome安全测试: mock 当前页解析避免真实浏览器；若没有这行代码，server 会尝试创建或查找真实页面
            result = server.browser_evaluate({"script": "() => document.body.innerText"})  # 新增代码+RealChrome安全测试: 执行允许脚本覆盖成功路径；若没有这行代码，无法证明低风险脚本仍可用
        self.assertIn("visible text", result)  # 新增代码+RealChrome安全测试: 断言返回结果包含可见文本；若没有这行代码，成功路径可能丢失 evaluate 返回值
        self.assertEqual(server.last_safety_refusal, "无")  # 新增代码+RealChrome安全测试: 断言允许脚本不会污染最近拒绝状态；若没有这行代码，状态工具可能误报安全拒绝
        self.assertFalse(any(call.args[0] == "safety_refusal" for call in server.audit_logger.record.call_args_list))  # 新增代码+RealChrome安全测试: 断言成功路径没有安全拒绝事件；若没有这行代码，允许脚本也可能被错误记录为拒绝
        server.audit_logger.record.assert_called_once_with("browser_tool", {"tool_name": "browser_evaluate", "details": {"page_id": "page-1", "script_allowed": True}})  # 新增代码+RealChrome安全测试: 断言成功审计只写安全摘要不写脚本全文；若没有这行代码，browser_evaluate 成功路径可能漏审计或泄露脚本
    def test_real_chrome_choose_loopback_port_skips_occupied_port(self) -> None:  # 新增代码+RealChrome测试: 验证端口选择能避开占用；若省略: 调试端口占用时可能启动失败
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 新增代码+RealChrome测试: 创建测试 socket；若省略: 无法制造端口占用
        self.addCleanup(sock.close)  # 新增代码+RealChrome测试: 注册清理 socket；若省略: 测试失败时可能占住端口
        sock.bind(("127.0.0.1", 0))  # 新增代码+RealChrome测试: 绑定本机随机端口；若省略: 没有被占用的端口
        sock.listen(1)  # 新增代码+RealChrome测试: 让端口进入监听状态；若省略: 端口可能仍被认为可用
        occupied_port = sock.getsockname()[1]  # 新增代码+RealChrome测试: 读取被占用端口号；若省略: 无法传给端口选择函数
        chosen_port = choose_loopback_port(preferred_port=occupied_port)  # 新增代码+RealChrome测试: 要求 helper 避开占用端口；若省略: 端口选择逻辑没有执行
        self.assertNotEqual(occupied_port, chosen_port)  # 新增代码+RealChrome测试: 断言没有选择已占用端口；若省略: 回归不会暴露
        self.assertIsInstance(chosen_port, int)  # 新增代码+RealChrome测试: 断言返回值是整数端口号；若省略: helper 可能返回字符串或空值导致启动命令后续才失败
        self.assertGreaterEqual(chosen_port, 1)  # 新增代码+RealChrome测试: 断言端口不小于 1；若省略: helper 可能返回 0 或负数这种不可用端口
        self.assertLessEqual(chosen_port, 65535)  # 新增代码+RealChrome测试: 断言端口不超过 TCP 最大值；若省略: helper 可能返回超范围端口导致 Chrome 启动失败
        verify_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 新增代码+RealChrome测试: 创建验证 socket；若省略: 无法证明 helper 返回端口真的可绑定
        self.addCleanup(verify_sock.close)  # 新增代码+RealChrome测试: 注册验证 socket 清理；若省略: 测试失败时可能短暂占住端口
        verify_sock.bind(("127.0.0.1", chosen_port))  # 新增代码+RealChrome测试: 真实绑定 helper 返回端口；若省略: return preferred_port + 1 这类伪实现可能误过测试
    def test_browser_connect_real_chrome_requires_confirmation(self) -> None:  # 新增代码+RealChrome确认测试: 验证没有显式确认时拒绝真实 Chrome profile；若省略: 高风险连接可能缺少回归保护
        server_script = self._browser_automation_server_script()  # 新增代码+RealChrome确认测试: 定位 browser automation MCP server 脚本；若省略: 测试无法启动真实协议入口
        client = McpStdioClient(McpServerConfig(name="browser_automation", command=sys.executable, args=[str(server_script), str(TEST_ROOT)]))  # 新增代码+RealChrome确认测试: 通过 stdio 调用被测 MCP 工具；若省略: 只能测试 Python 方法而覆盖不到 MCP 边界
        try:  # 新增代码+RealChrome确认测试: 确保测试失败时也关闭 client；若省略: MCP 子进程可能残留
            client.start()  # 新增代码+RealChrome确认测试: 启动 server 并完成 initialize；若省略: 后续 call_tool 没有通信对象
            with self.assertRaisesRegex(RuntimeError, "confirm_real_profile"):  # 新增代码+RealChrome确认测试: 断言错误必须点名 confirm_real_profile；若省略: 用户可能看不懂为什么被拒绝
                client.call_tool("browser_connect_real_chrome", {"confirm_real_profile": False})  # 新增代码+RealChrome确认测试: 故意传 false 触发确认边界；若省略: 测试不会覆盖拒绝路径
            with self.assertRaisesRegex(RuntimeError, "confirm_real_profile"):  # 新增代码+RealChrome确认测试: 断言完全省略确认参数也必须失败；若省略: 空参数调用缺少回归保护
                client.call_tool("browser_connect_real_chrome", {})  # 新增代码+RealChrome确认测试: 故意传空参数覆盖省略 confirm_real_profile；若省略: 只覆盖 false 不覆盖缺字段场景
        finally:  # 新增代码+RealChrome确认测试: 进入统一清理分支；若省略: 异常时资源不会释放
            client.close()  # 新增代码+RealChrome确认测试: 关闭 MCP client 和子进程；若省略: 后续测试可能被残留进程干扰
    def test_browser_profile_status_defaults_to_independent_chromium(self) -> None:  # 新增代码+RealChrome状态测试: 验证默认仍是独立 Chromium 模式；若省略: 默认误切真实 Chrome 的回归不会暴露
        server_script = self._browser_automation_server_script()  # 新增代码+RealChrome状态测试: 定位 browser automation MCP server 脚本；若省略: 状态测试没有被测 server
        client = McpStdioClient(McpServerConfig(name="browser_automation", command=sys.executable, args=[str(server_script), str(TEST_ROOT)]))  # 新增代码+RealChrome状态测试: 通过 stdio 启动真实 server；若省略: 无法覆盖 MCP 状态工具
        try:  # 新增代码+RealChrome状态测试: 确保 client 总能关闭；若省略: 失败路径会泄漏子进程
            client.start()  # 新增代码+RealChrome状态测试: 完成 MCP initialize；若省略: browser_profile_status 无法调用
            result = client.call_tool("browser_profile_status", {})  # 新增代码+RealChrome状态测试: 调用只读状态工具；若省略: 无法验证默认状态文本
            self.assertIn("browser_profile_status", result)  # 新增代码+RealChrome状态测试: 断言状态结果包含工具标题；若没有这行代码，返回文本可能失去来源标识让新手分不清是哪一个工具的结果
            self.assertIn("mode=independent_chromium", result)  # 新增代码+RealChrome状态测试: 断言默认模式是独立 Chromium；若省略: 真实 Chrome 可能被误设为默认
            self.assertIn("real_chrome_connected=false", result)  # 新增代码+RealChrome状态测试: 断言默认未连接真实 Chrome；若省略: 用户可能误解当前连接状态
            self.assertIn("chrome_started_by_agent=false", result)  # 新增代码+RealChrome状态测试: 断言默认没有 agent 启动的 Chrome 进程；若没有这行代码，状态工具可能漏掉是否能安全关闭进程的关键依据
            self.assertIn("endpoint=", result)  # 新增代码+RealChrome状态测试: 断言默认 endpoint 字段为空但存在；若没有这行代码，上层无法用固定字段读取连接端点
            self.assertIn("profile=", result)  # 新增代码+RealChrome状态测试: 断言默认 profile 字段为空但存在；若没有这行代码，用户无法确认状态工具没有读取真实 profile 数据
            self.assertIn("pages=0", result)  # 新增代码+RealChrome状态测试: 断言默认页面数量为 0；若没有这行代码，页面映射泄漏或计数缺失不会暴露
            self.assertIn("最近安全拒绝：无", result)  # 新增代码+RealChrome状态测试: 断言默认最近安全拒绝为无；若没有这行代码，用户无法从状态工具确认近期没有隐私拦截历史
        finally:  # 新增代码+RealChrome状态测试: 进入统一清理分支；若省略: MCP server 进程可能残留
            client.close()  # 新增代码+RealChrome状态测试: 关闭 MCP client；若省略: 测试会泄漏子进程资源
    @unittest.skipUnless(os.environ.get("LEARNING_AGENT_REAL_CHROME_TEST") == "1", "需要用户显式设置 LEARNING_AGENT_REAL_CHROME_TEST=1 并关闭 Chrome 后才运行。")  # 新增代码+ManualRealChrome门禁: 默认跳过真实 Chrome 集成测试，避免自动化误触用户日常 Chrome profile；若没有这行代码，普通测试可能启动或连接真实 Chrome
    def test_manual_real_chrome_connect_open_status_disconnect(self) -> None:  # 新增代码+ManualRealChrome门禁: 提供手动闭环验证真实 Chrome 连接、打开、状态和断开；若没有这行代码，真实 profile 集成链路缺少明确人工门禁
        server_script = self._browser_automation_server_script()  # 新增代码+ManualRealChrome门禁: 定位 browser_automation_mcp_server.py；若没有这行代码，测试无法通过 stdio 启动被测 MCP server
        client = McpStdioClient(McpServerConfig(name="browser_automation", command=sys.executable, args=[str(server_script), str(TEST_ROOT)]))  # 新增代码+ManualRealChrome门禁: 用当前 Python 启动 MCP server；若没有这行代码，测试无法走真实 MCP 协议闭环
        try:  # 新增代码+ManualRealChrome门禁: 把手动测试主体包进清理边界；若没有这行代码，测试失败时 MCP 子进程可能残留
            client.start()  # 新增代码+ManualRealChrome门禁: 完成 MCP initialize；若没有这行代码，后续工具调用没有可用连接
            connect_result = client.call_tool("browser_connect_real_chrome", {"confirm_real_profile": True})  # 新增代码+ManualRealChrome门禁: 手动确认后连接真实 Chrome；若没有这行代码，闭环无法验证真实 Chrome 连接入口
            self.assertIn("real_chrome_connected=true", connect_result)  # 新增代码+ManualRealChrome门禁: 断言连接后机器可读状态为 true；若没有这行代码，连接成功状态回归不会被发现
            open_result = client.call_tool("browser_open", {"url": "https://example.com"})  # 新增代码+ManualRealChrome门禁: 只打开公开示例站点 example.com；若没有这行代码，测试无法验证连接后还能执行普通打开页面操作
            self.assertIn("browser_open 成功", open_result)  # 新增代码+ManualRealChrome门禁: 断言打开页面工具返回成功提示；若没有这行代码，页面打开失败可能被后续状态检查掩盖
            status_result = client.call_tool("browser_profile_status", {})  # 新增代码+ManualRealChrome门禁: 只查询连接状态，不读取 cookies、localStorage、sessionStorage、token 或 password；若没有这行代码，无法确认当前模式已切到真实 Chrome
            self.assertIn("mode=real_chrome", status_result)  # 新增代码+ManualRealChrome门禁: 断言状态模式为 real_chrome；若没有这行代码，测试无法证明真实 Chrome 模式已经生效
            disconnect_result = client.call_tool("browser_disconnect_real_chrome", {"close_browser": False})  # 新增代码+ManualRealChrome门禁: 断开 CDP 但不关闭浏览器；若没有这行代码，测试可能留下连接或误关用户 Chrome
            self.assertIn("real_chrome_connected=false", disconnect_result)  # 新增代码+ManualRealChrome门禁: 断言断开后机器可读状态为 false；若没有这行代码，断开失败不会被测试发现
        finally:  # 新增代码+ManualRealChrome门禁: 无论成功失败都进入清理；若没有这行代码，异常路径可能留下 stdio server 子进程
            client.close()  # 新增代码+ManualRealChrome门禁: 关闭 MCP client 和 server 子进程；若没有这行代码，手动测试失败后可能影响后续测试
    def test_browser_disconnect_real_chrome_is_idempotent_without_connection(self) -> None:  # 新增代码+RealChrome断开测试: 验证没有真实 Chrome 连接时断开工具也安全返回；若没有这行代码，无连接调用可能报错或误启动浏览器而不被发现
        server_script = self._browser_automation_server_script()  # 新增代码+RealChrome断开测试: 定位 browser automation MCP server 脚本；若没有这行代码，测试无法启动真实协议入口
        client = McpStdioClient(McpServerConfig(name="browser_automation", command=sys.executable, args=[str(server_script), str(TEST_ROOT)]))  # 新增代码+RealChrome断开测试: 通过 stdio 启动被测 server；若没有这行代码，只测内部方法会漏掉 MCP 包装问题
        try:  # 新增代码+RealChrome断开测试: 确保测试失败时也关闭 client；若没有这行代码，MCP 子进程可能残留影响后续测试
            client.start()  # 新增代码+RealChrome断开测试: 完成 MCP initialize；若没有这行代码，后续无法调用 browser_disconnect_real_chrome
            result = client.call_tool("browser_disconnect_real_chrome", {"close_browser": False})  # 新增代码+RealChrome断开测试: 在无连接状态显式请求不关闭浏览器；若没有这行代码，幂等断开行为没有执行来源
            self.assertIn("browser_disconnect_real_chrome", result)  # 新增代码+RealChrome断开测试: 断言结果包含工具名；若没有这行代码，用户难以确认返回来自断开工具
            self.assertIn("real_chrome_connected=false", result)  # 新增代码+RealChrome断开测试: 断言无连接断开返回 false；若没有这行代码，上层无法稳定判断已处于安全断开状态
        finally:  # 新增代码+RealChrome断开测试: 统一关闭 MCP client；若没有这行代码，测试失败时可能泄漏 server 进程
            client.close()  # 新增代码+RealChrome断开测试: 释放 stdio server 子进程；若没有这行代码，后续测试可能被残留进程干扰
    def test_browser_connect_real_chrome_blocks_when_chrome_is_running_without_cdp(self) -> None:  # 修改代码+RealChrome已有CDP: 验证 Chrome 已运行但没有可信 CDP 时仍阻断连接；若省略: profile 锁冲突边界没有单元测试保护
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome运行中测试: 导入被测 server 类；若省略: 无法直接测试确认后的内部阻断逻辑
        server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome运行中测试: 创建隔离到测试目录的 server 实例；若省略: 没有可调用的 browser_connect_real_chrome 方法
        with mock.patch("learning_agent.browser_automation_mcp_server.ChromeProfileManager.chrome_is_running", return_value=True):  # 新增代码+RealChrome运行中测试: 模拟检测到 Chrome 正在运行；若省略: 测试会依赖真实用户电脑状态
            with mock.patch("learning_agent.browser_automation_mcp_server.wait_for_cdp_endpoint", return_value=False):  # 新增代码+RealChrome已有CDP: 明确模拟没有可用 CDP 端点；若省略: 测试会被开发机真实 9222 状态影响
                with mock.patch.object(server, "_connect_real_chrome_after_checks", create=True) as connect_mock:  # 修改代码+RealChrome运行中测试: 去掉 autospec 让缺失 helper 的红灯阶段也能打桩；若省略: 测试会因 mock 用法错误而不是产品行为失败
                    with self.assertRaisesRegex(RuntimeError, "Chrome 正在运行|先关闭当前 Chrome"):  # 新增代码+RealChrome运行中测试: 断言错误提示用户先关闭 Chrome；若省略: 错误文案不清楚也不会失败
                        server.browser_connect_real_chrome({"confirm_real_profile": True})  # 新增代码+RealChrome运行中测试: 传 true 越过确认边界进入运行中检查；若省略: 测试不到 Chrome 占用阻断
                    connect_mock.assert_not_called()  # 新增代码+RealChrome运行中测试: 确认阻断后没有启动真实连接；若省略: 可能一边报错一边继续碰真实 profile
    def test_browser_connect_real_chrome_attaches_when_running_chrome_has_cdp(self) -> None:  # 新增代码+RealChrome已有CDP: 验证 Chrome 已运行且 9222 已提供 CDP 时应直接接管；若省略: 真实可见 Chrome 已开调试端口仍会被误拦截
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome已有CDP: 导入被测 server 类；若省略: 测试没有真实连接入口可调用
        server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome已有CDP: 创建隔离 server 实例；若省略: 无法观察 browser_connect_real_chrome 的分支行为
        with mock.patch("learning_agent.browser_automation_mcp_server.ChromeProfileManager.chrome_is_running", return_value=True):  # 新增代码+RealChrome已有CDP: 模拟用户桌面 Chrome 已在运行；若省略: 测试会依赖当前电脑是否打开 Chrome
            with mock.patch("learning_agent.browser_automation_mcp_server.wait_for_cdp_endpoint", return_value=True) as cdp_mock:  # 新增代码+RealChrome已有CDP: 模拟 9222 已是可信 CDP 端点；若省略: 无法稳定复现这次验收失败根因
                with mock.patch.object(server, "_connect_real_chrome_after_checks", return_value="browser_connect_real_chrome 成功") as connect_mock:  # 新增代码+RealChrome已有CDP: 只观察是否进入接管分支而不真的碰用户浏览器；若省略: 单元测试会启动真实 Chrome
                    result = server.browser_connect_real_chrome({"confirm_real_profile": True})  # 新增代码+RealChrome已有CDP: 执行被测入口；若省略: 后续断言没有行为来源
        self.assertEqual(result, "browser_connect_real_chrome 成功")  # 新增代码+RealChrome已有CDP: 断言入口把接管结果返回给上层；若省略: 返回值回归不会被发现
        cdp_mock.assert_called_once_with(9222, timeout_seconds=1.0)  # 新增代码+RealChrome已有CDP: 断言检查的是默认 9222 CDP 端口；若省略: 可能误检查随机端口导致验收继续失败
        connect_mock.assert_called_once()  # 新增代码+RealChrome已有CDP: 断言已进入真实连接 helper；若省略: 测试不能证明运行中 Chrome 被允许接管
        _, connect_kwargs = connect_mock.call_args  # 新增代码+RealChrome已有CDP: 读取 helper 的关键字参数；若省略: 无法确认是否是附着已有 CDP 而非重启 Chrome
        self.assertTrue(connect_kwargs["attach_existing_cdp"])  # 新增代码+RealChrome已有CDP: 断言 helper 使用附着已有 CDP 模式；若省略: 实现可能仍尝试启动新 Chrome
        self.assertEqual(connect_kwargs["existing_debug_port"], 9222)  # 新增代码+RealChrome已有CDP: 断言传入已有 CDP 端口；若省略: 连接可能落到错误端口
    def test_browser_connect_real_chrome_rejects_non_bool_confirmation(self) -> None:  # 新增代码+RealChrome确认测试: 验证字符串和数字不能冒充确认；若省略: 宽松类型可能绕过高风险边界
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome确认测试: 导入被测 server 类；若省略: 无法直接验证运行时确认逻辑
        server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome确认测试: 创建 server 实例；若省略: 没有可调用的连接入口
        with mock.patch.object(server, "_connect_real_chrome_after_checks", create=True) as connect_mock:  # 新增代码+RealChrome确认测试: 监控非法确认不会进入连接 helper；若省略: 测试无法证明拒绝后没有继续碰真实 profile
            for bad_value in ("true", 1):  # 新增代码+RealChrome确认测试: 覆盖字符串 true 和数字 1 两种常见误传；若省略: 只测 false/缺省会漏掉宽松真值
                with self.subTest(bad_value=bad_value):  # 新增代码+RealChrome确认测试: 单独标记每个非法值；若省略: 失败时难以定位是哪种输入
                    with self.assertRaisesRegex(RuntimeError, "confirm_real_profile"):  # 新增代码+RealChrome确认测试: 断言错误仍提示确认字段；若省略: 用户可能看不懂被拒原因
                        server.browser_connect_real_chrome({"confirm_real_profile": bad_value})  # 新增代码+RealChrome确认测试: 传入非法真值尝试连接；若省略: 测试不会触发严格类型边界
            connect_mock.assert_not_called()  # 新增代码+RealChrome确认测试: 确认所有非法值都没有进入连接 helper；若省略: 拒绝后继续执行的风险不会暴露
    def test_close_all_disconnects_real_chrome_without_closing_profile(self) -> None:  # 新增代码+RealChrome关闭测试: 验证 close_all 在真实 Chrome 模式只断开 CDP；若省略: browser_close all 或 server shutdown 可能误关真实 Chrome
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome关闭测试: 导入被测 server 类；若省略: 无法直接调用 close_all
        server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome关闭测试: 创建 server 实例；若省略: 没有浏览器状态可布置
        fake_browser = mock.Mock()  # 新增代码+RealChrome关闭测试: 创建 fake browser 观察 disconnect/close 调用；若省略: 无法断言是否误关浏览器
        fake_context = mock.Mock()  # 新增代码+RealChrome关闭测试: 创建 fake context 观察 close 调用；若省略: 无法断言是否误关真实 profile 上下文
        fake_page = mock.Mock()  # 新增代码+RealChrome关闭测试: 创建 fake page 观察 page.close 调用；若省略: 无法确认真实 Chrome 标签页未被默认关闭
        fake_playwright = mock.Mock()  # 新增代码+RealChrome关闭测试: 创建 fake Playwright driver 观察 stop 调用；若省略: 无法验证 close_all 释放 CDP 驱动
        server.session_mode = "real_chrome"  # 新增代码+RealChrome关闭测试: 把 server 放入真实 Chrome 模式；若省略: close_all 会走独立 Chromium 清理路径
        server.playwright = fake_playwright  # 新增代码+RealChrome关闭测试: 注入 Playwright driver；若省略: 无法断言真实模式断开后 driver 被停止
        server.browser = fake_browser  # 新增代码+RealChrome关闭测试: 注入 fake browser；若省略: close_all 没有可断开的 CDP 连接
        server.context = fake_context  # 新增代码+RealChrome关闭测试: 注入 fake context；若省略: 无法验证 context.close 不被调用
        server.pages = {"page-1": fake_page}  # 新增代码+RealChrome关闭测试: 注入已登记页面；若省略: 无法验证页面映射会清空
        server.current_page_id = "page-1"  # 新增代码+RealChrome关闭测试: 设置当前页面；若省略: 无法验证当前页状态被复位
        server.element_refs = {"page-1": [{"id": 1}]}  # 新增代码+RealChrome关闭测试: 设置元素引用；若省略: 无法验证元素缓存被清空
        server.console_logs = [{"text": "old"}]  # 新增代码+RealChrome关闭测试: 设置控制台日志；若省略: 无法验证日志缓存被清空
        server.network_logs = [{"url": "https://example.com"}]  # 新增代码+RealChrome关闭测试: 设置网络日志；若省略: 无法验证网络缓存被清空
        server.downloads = [{"filename": "a.txt"}]  # 新增代码+RealChrome关闭测试: 设置下载记录；若省略: 无法验证下载缓存被清空
        server.real_chrome_endpoint = "http://127.0.0.1:9222"  # 新增代码+RealChrome关闭测试: 设置真实 Chrome endpoint；若省略: 无法验证 endpoint 被复位
        server.real_chrome_profile_summary = "User Data::Default"  # 新增代码+RealChrome关闭测试: 设置 profile 摘要；若省略: 无法验证 profile 摘要被复位
        server.chrome_process = mock.Mock()  # 新增代码+RealChrome关闭测试: 设置进程引用；若省略: 无法验证 Task 4 只清引用不 terminate
        server.audit_logger = mock.Mock()  # 修改代码+RealChrome关闭测试: 用 fake 审计器避免 close_all 测试写真实审计文件；若没有这行代码，单元测试可能在项目目录留下额外产物
        server.close_all()  # 新增代码+RealChrome关闭测试: 执行被测清理；若省略: 断言没有行为来源
        fake_browser.disconnect.assert_called_once()  # 新增代码+RealChrome关闭测试: 断言只断开 Playwright CDP 连接；若省略: 真实 Chrome 可能被 close 而非 disconnect
        fake_browser.close.assert_not_called()  # 新增代码+RealChrome关闭测试: 断言不默认关闭真实 Chrome browser；若省略: 误关风险不会被测试发现
        fake_context.close.assert_not_called()  # 新增代码+RealChrome关闭测试: 断言不默认关闭真实 Chrome context；若省略: 真实 profile 上下文可能被误关
        fake_page.close.assert_not_called()  # 新增代码+RealChrome关闭测试: 断言不默认关闭真实 Chrome 标签页；若省略: 用户页面可能被误关
        fake_playwright.stop.assert_called_once()  # 新增代码+RealChrome关闭测试: 断言真实模式断开后释放 Playwright driver；若省略: CDP driver 可能残留
        self.assertEqual(server.session_mode, "independent_chromium")  # 新增代码+RealChrome关闭测试: 断言清理后回到默认模式；若省略: 状态工具可能继续误报真实 Chrome
        self.assertIsNone(server.playwright)  # 新增代码+RealChrome关闭测试: 断言 Playwright driver 引用置空；若省略: 后续可能误认为旧 driver 仍可用
        self.assertIsNone(server.browser)  # 新增代码+RealChrome关闭测试: 断言 browser 引用已清空；若省略: 后续工具可能复用已断开的 CDP 对象
        self.assertIsNone(server.context)  # 新增代码+RealChrome关闭测试: 断言 context 引用已清空；若省略: 后续工具可能误用旧上下文
        self.assertEqual(server.pages, {})  # 新增代码+RealChrome关闭测试: 断言页面映射清空；若省略: 旧页面 id 会污染新会话
        self.assertIsNone(server.current_page_id)  # 新增代码+RealChrome关闭测试: 断言当前页清空；若省略: 后续默认操作可能指向旧页面
        self.assertEqual(server.element_refs, {})  # 新增代码+RealChrome关闭测试: 断言元素引用清空；若省略: 旧元素 id 会污染后续操作
        self.assertEqual(server.console_logs, [])  # 新增代码+RealChrome关闭测试: 断言控制台日志清空；若省略: 新会话可能显示旧日志
        self.assertEqual(server.network_logs, [])  # 新增代码+RealChrome关闭测试: 断言网络日志清空；若省略: 新会话可能显示旧请求
        self.assertEqual(server.downloads, [])  # 新增代码+RealChrome关闭测试: 断言下载记录清空；若省略: 新会话可能显示旧下载
        self.assertEqual(server.real_chrome_endpoint, "")  # 新增代码+RealChrome关闭测试: 断言 endpoint 摘要清空；若省略: 状态工具会显示旧端点
        self.assertEqual(server.real_chrome_profile_summary, "")  # 新增代码+RealChrome关闭测试: 断言 profile 摘要清空；若省略: 用户可能误以为仍连接旧 profile
        self.assertIsNone(server.chrome_process)  # 新增代码+RealChrome关闭测试: 断言 Task 4 清空进程引用；若省略: 后续可能误以为还能管理该进程
    def test_browser_disconnect_real_chrome_disconnects_cdp_without_closing_profile(self) -> None:  # 新增代码+RealChrome断开测试: 验证真实模式断开只断 CDP 不关用户 profile；若没有这行代码，正式断开实现可能误关真实 Chrome 而不被发现
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome断开测试: 导入被测 server 类；若没有这行代码，无法直接布置 fake 真实 Chrome 状态
        server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome断开测试: 创建 server 实例；若没有这行代码，测试没有可调用的断开方法
        fake_browser = mock.Mock()  # 新增代码+RealChrome断开测试: 创建 fake browser 观察 disconnect/close；若没有这行代码，无法证明只断开 CDP
        fake_context = mock.Mock()  # 新增代码+RealChrome断开测试: 创建 fake context 观察 close；若没有这行代码，无法证明不关闭真实 profile 上下文
        fake_page = mock.Mock()  # 新增代码+RealChrome断开测试: 创建 fake page 代表真实标签页；若没有这行代码，无法证明断开不会关闭页面
        fake_process = mock.Mock()  # 新增代码+RealChrome断开测试: 创建 fake Chrome 进程；若没有这行代码，无法证明 close_browser=false 不 terminate 进程
        fake_playwright = mock.Mock()  # 新增代码+RealChrome断开测试: 创建 fake Playwright driver；若没有这行代码，无法验证真实模式断开后释放 driver
        server.session_mode = "real_chrome"  # 新增代码+RealChrome断开测试: 把 server 放入真实 Chrome 模式；若没有这行代码，断开工具会走无连接幂等分支
        server.browser = fake_browser  # 新增代码+RealChrome断开测试: 注入可断开的 CDP browser；若没有这行代码，无法断言 browser.disconnect 被调用
        server.context = fake_context  # 新增代码+RealChrome断开测试: 注入真实 Chrome 上下文替身；若没有这行代码，无法断言 context.close 未被调用
        server.pages = {"page-1": fake_page}  # 新增代码+RealChrome断开测试: 注入页面映射；若没有这行代码，无法验证 page_count 和清理页面表
        server.current_page_id = "page-1"  # 新增代码+RealChrome断开测试: 注入当前页；若没有这行代码，无法验证当前页复位
        server.element_refs = {"page-1": [{"id": 1}]}  # 新增代码+RealChrome断开测试: 注入元素引用；若没有这行代码，旧元素 id 清理回归不会暴露
        server.real_chrome_endpoint = "http://127.0.0.1:9222"  # 新增代码+RealChrome断开测试: 注入 endpoint 摘要；若没有这行代码，无法验证断开后 endpoint 被清空
        server.real_chrome_profile_summary = "User Data::Default"  # 新增代码+RealChrome断开测试: 注入 profile 摘要；若没有这行代码，无法验证断开后 profile 被清空
        server.chrome_process = fake_process  # 新增代码+RealChrome断开测试: 注入本次 agent 启动的 Chrome 进程；若没有这行代码，无法证明默认保留进程
        server.playwright = fake_playwright  # 新增代码+RealChrome断开测试: 注入 Playwright driver；若没有这行代码，无法验证断开后 driver stop
        server.audit_logger = mock.Mock()  # 新增代码+RealChrome断开测试: 替换审计 logger 为 fake；若没有这行代码，无法断言写入了安全摘要
        result = server.browser_disconnect_real_chrome({"close_browser": False})  # 新增代码+RealChrome断开测试: 执行默认不关闭浏览器的断开；若没有这行代码，后续断言没有行为来源
        fake_browser.disconnect.assert_called_once()  # 新增代码+RealChrome断开测试: 断言调用 CDP disconnect；若没有这行代码，连接可能残留或误用 close
        fake_browser.close.assert_not_called()  # 新增代码+RealChrome断开测试: 断言不关闭真实 browser；若没有这行代码，误关 Chrome 的风险不会被测试拦住
        fake_context.close.assert_not_called()  # 新增代码+RealChrome断开测试: 断言不关闭真实 context；若没有这行代码，真实 profile 上下文可能被误关
        fake_page.close.assert_not_called()  # 新增代码+RealChrome断开测试: 断言不关闭真实标签页；若没有这行代码，用户页面可能被误关
        fake_process.terminate.assert_not_called()  # 新增代码+RealChrome断开测试: 断言 close_browser=false 不终止 Chrome；若没有这行代码，默认保留真实 Chrome 的契约没有保护
        fake_playwright.stop.assert_called_once()  # 新增代码+RealChrome断开测试: 断言真实模式断开后停止 Playwright driver；若没有这行代码，CDP driver 可能残留
        server.audit_logger.record.assert_called_once_with("disconnect_real_chrome", {"close_browser": False, "closed_browser": False, "closed_process": False, "terminated_process": False, "page_count": 1})  # 新增代码+RealChrome断开测试: 断言审计只写摘要不含敏感路径；若没有这行代码，审计可能漏记或写入敏感数据
        self.assertIn("browser_disconnect_real_chrome", result)  # 新增代码+RealChrome断开测试: 断言返回包含工具名；若没有这行代码，用户难以确认操作来源
        self.assertIn("real_chrome_connected=false", result)  # 新增代码+RealChrome断开测试: 断言断开后连接状态为 false；若没有这行代码，上层无法稳定确认安全状态
        self.assertIn("mode=independent_chromium", result)  # 新增代码+RealChrome断开测试: 断言断开后回到默认模式；若没有这行代码，状态可能继续误报真实 Chrome
        self.assertIn("closed_browser=false", result)  # 新增代码+RealChrome断开测试: 断言默认没有关闭浏览器；若没有这行代码，用户无法确认 Chrome 被保留
        self.assertEqual(server.session_mode, "independent_chromium")  # 新增代码+RealChrome断开测试: 断言内部模式复位；若没有这行代码，后续状态工具可能继续报 real_chrome
        self.assertIsNone(server.browser)  # 新增代码+RealChrome断开测试: 断言 browser 引用清空；若没有这行代码，后续工具可能复用已断开的 CDP
        self.assertIsNone(server.context)  # 新增代码+RealChrome断开测试: 断言 context 引用清空；若没有这行代码，后续工具可能误用旧上下文
        self.assertEqual(server.pages, {})  # 新增代码+RealChrome断开测试: 断言页面映射清空；若没有这行代码，旧 page_id 会污染新会话
        self.assertIsNone(server.current_page_id)  # 新增代码+RealChrome断开测试: 断言当前页清空；若没有这行代码，默认操作可能指向旧页面
        self.assertEqual(server.element_refs, {})  # 新增代码+RealChrome断开测试: 断言元素引用清空；若没有这行代码，旧元素 id 会污染后续操作
        self.assertEqual(server.real_chrome_endpoint, "")  # 新增代码+RealChrome断开测试: 断言 endpoint 摘要清空；若没有这行代码，状态会显示旧端点
        self.assertEqual(server.real_chrome_profile_summary, "")  # 新增代码+RealChrome断开测试: 断言 profile 摘要清空；若没有这行代码，用户可能误以为仍连接旧 profile
        self.assertIsNone(server.chrome_process)  # 新增代码+RealChrome断开测试: 断言进程引用清空；若没有这行代码，后续可能误以为还能管理旧进程
    def test_browser_disconnect_real_chrome_terminates_agent_chrome_only_when_requested(self) -> None:  # 新增代码+RealChrome断开测试: 验证 close_browser=true 只终止 agent 启动的 Chrome；若没有这行代码，关闭开关可能误关 context/browser 或不终止进程
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome断开测试: 导入被测 server 类；若没有这行代码，无法直接构造真实模式状态
        server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome断开测试: 创建 server 实例；若没有这行代码，测试没有断开工具可调用
        fake_browser = mock.Mock()  # 新增代码+RealChrome断开测试: 创建 fake browser；若没有这行代码，无法断言不会调用 browser.close
        fake_context = mock.Mock()  # 新增代码+RealChrome断开测试: 创建 fake context；若没有这行代码，无法断言不会调用 context.close
        fake_process = mock.Mock()  # 新增代码+RealChrome断开测试: 创建 agent 启动的 fake Chrome 进程；若没有这行代码，无法验证 terminate 条件
        server.session_mode = "real_chrome"  # 新增代码+RealChrome断开测试: 设置真实 Chrome 模式；若没有这行代码，断开工具不会进入真实断开分支
        server.browser = fake_browser  # 新增代码+RealChrome断开测试: 注入 CDP browser；若没有这行代码，无法验证 disconnect 被调用
        server.context = fake_context  # 新增代码+RealChrome断开测试: 注入 context；若没有这行代码，无法验证 context.close 未被调用
        server.pages = {}  # 新增代码+RealChrome断开测试: 设置空页面表；若没有这行代码，审计 page_count 默认值不明确
        server.chrome_process = fake_process  # 新增代码+RealChrome断开测试: 注入本次 agent 启动进程；若没有这行代码，close_browser=true 没有可终止对象
        server.playwright = mock.Mock()  # 新增代码+RealChrome断开测试: 注入 Playwright driver；若没有这行代码，无法验证清理路径完整
        server.audit_logger = mock.Mock()  # 新增代码+RealChrome断开测试: 替换审计 logger；若没有这行代码，无法断言关闭摘要被记录
        result = server.browser_disconnect_real_chrome({"close_browser": True})  # 新增代码+RealChrome断开测试: 执行明确关闭 agent Chrome 的断开；若没有这行代码，terminate 行为没有触发来源
        fake_browser.disconnect.assert_called_once()  # 新增代码+RealChrome断开测试: 断言仍优先断开 CDP；若没有这行代码，断开顺序可能退化
        fake_browser.close.assert_not_called()  # 新增代码+RealChrome断开测试: 断言不调用 browser.close；若没有这行代码，真实 Chrome 可能被 Playwright close 误关
        fake_context.close.assert_not_called()  # 新增代码+RealChrome断开测试: 断言不调用 context.close；若没有这行代码，真实 profile 上下文可能被误关
        fake_process.terminate.assert_called_once()  # 新增代码+RealChrome断开测试: 断言 close_browser=true 且有进程时才 terminate；若没有这行代码，agent 启动的 Chrome 可能残留
        server.audit_logger.record.assert_called_once_with("disconnect_real_chrome", {"close_browser": True, "closed_browser": True, "closed_process": True, "terminated_process": True, "page_count": 0})  # 新增代码+RealChrome断开测试: 断言审计记录关闭进程摘要；若没有这行代码，关闭行为缺少可追踪记录
        self.assertIn("closed_browser=true", result)  # 新增代码+RealChrome断开测试: 断言返回明确说明已关闭 agent Chrome；若没有这行代码，用户无法确认 close_browser=true 是否生效
        self.assertIsNone(server.chrome_process)  # 新增代码+RealChrome断开测试: 断言终止后进程引用清空；若没有这行代码，后续可能重复 terminate 旧进程
    def test_browser_disconnect_real_chrome_resets_state_when_cleanup_steps_raise(self) -> None:  # 新增代码+RealChrome断开异常测试: 验证断开清理步骤抛错时仍复位状态；若没有这行代码，异常路径可能留下真实 Chrome 半连接状态
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome断开异常测试: 导入被测 server 类；若没有这行代码，无法直接布置 fake 异常场景
        scenarios = ("disconnect", "terminate", "playwright_stop", "audit")  # 新增代码+RealChrome断开异常测试: 列出四个必须容忍的清理异常点；若没有这行代码，异常覆盖范围不清晰
        for scenario in scenarios:  # 新增代码+RealChrome断开异常测试: 逐个执行异常场景；若没有这行代码，只能覆盖其中一个失败来源
            with self.subTest(scenario=scenario):  # 新增代码+RealChrome断开异常测试: 给每个异常点单独显示失败上下文；若没有这行代码，失败时难以定位是哪一步
                server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome断开异常测试: 每个场景创建新 server 避免状态串扰；若没有这行代码，前一个场景清理会影响后一个场景
                fake_browser = mock.Mock()  # 新增代码+RealChrome断开异常测试: 创建 fake browser；若没有这行代码，无法模拟 disconnect 异常
                fake_context = mock.Mock()  # 新增代码+RealChrome断开异常测试: 创建 fake context；若没有这行代码，无法断言 context 引用被清空
                fake_process = mock.Mock()  # 新增代码+RealChrome断开异常测试: 创建 fake Chrome 进程；若没有这行代码，无法模拟 terminate 异常
                fake_playwright = mock.Mock()  # 新增代码+RealChrome断开异常测试: 创建 fake Playwright driver；若没有这行代码，无法模拟 stop 异常
                fake_audit_logger = mock.Mock()  # 新增代码+RealChrome断开异常测试: 创建 fake audit logger；若没有这行代码，无法模拟 audit 异常
                if scenario == "disconnect":  # 新增代码+RealChrome断开异常测试: 选择 CDP 断开异常场景；若没有这行代码，disconnect 抛错不会被覆盖
                    fake_browser.disconnect.side_effect = RuntimeError("disconnect boom")  # 新增代码+RealChrome断开异常测试: 让 browser.disconnect 抛错；若没有这行代码，无法证明该异常被吞掉且状态复位
                if scenario == "terminate":  # 新增代码+RealChrome断开异常测试: 选择进程终止异常场景；若没有这行代码，terminate 抛错不会被覆盖
                    fake_process.terminate.side_effect = RuntimeError("terminate boom")  # 新增代码+RealChrome断开异常测试: 让 process.terminate 抛错；若没有这行代码，无法证明进程异常不阻断复位
                if scenario == "playwright_stop":  # 新增代码+RealChrome断开异常测试: 选择 Playwright 停止异常场景；若没有这行代码，stop 抛错不会被覆盖
                    fake_playwright.stop.side_effect = RuntimeError("stop boom")  # 新增代码+RealChrome断开异常测试: 让 playwright.stop 抛错；若没有这行代码，无法证明 driver 异常不阻断复位
                if scenario == "audit":  # 新增代码+RealChrome断开异常测试: 选择审计写入异常场景；若没有这行代码，audit 抛错不会被覆盖
                    fake_audit_logger.record.side_effect = RuntimeError("audit boom")  # 新增代码+RealChrome断开异常测试: 让 audit_logger.record 抛错；若没有这行代码，无法证明审计失败不阻断复位
                server.session_mode = "real_chrome"  # 新增代码+RealChrome断开异常测试: 设置真实 Chrome 模式；若没有这行代码，断开工具不会进入真实清理分支
                server.browser = fake_browser  # 新增代码+RealChrome断开异常测试: 注入 fake browser；若没有这行代码，无法测试 browser 引用复位
                server.context = fake_context  # 新增代码+RealChrome断开异常测试: 注入 fake context；若没有这行代码，无法测试 context 引用复位
                server.pages = {"page-1": mock.Mock()}  # 新增代码+RealChrome断开异常测试: 注入页面映射；若没有这行代码，无法确认 pages 被清空
                server.element_refs = {"page-1": [{"id": 1}]}  # 新增代码+RealChrome断开异常测试: 注入元素引用；若没有这行代码，无法确认 element_refs 被清空
                server.current_page_id = "page-1"  # 新增代码+RealChrome断开异常测试: 注入当前页；若没有这行代码，无法确认 current_page_id 被清空
                server.playwright = fake_playwright  # 新增代码+RealChrome断开异常测试: 注入 Playwright driver；若没有这行代码，无法确认 playwright 引用被清空
                server.chrome_process = fake_process  # 新增代码+RealChrome断开异常测试: 注入 Chrome 进程；若没有这行代码，无法确认 chrome_process 引用被清空
                server.real_chrome_endpoint = "http://127.0.0.1:9222"  # 新增代码+RealChrome断开异常测试: 注入 endpoint；若没有这行代码，无法确认 endpoint 被清空
                server.real_chrome_profile_summary = "profile=Default"  # 新增代码+RealChrome断开异常测试: 注入 profile 摘要；若没有这行代码，无法确认 profile 摘要被清空
                server.audit_logger = fake_audit_logger  # 新增代码+RealChrome断开异常测试: 注入 fake audit logger；若没有这行代码，无法触发审计异常场景
                result = server.browser_disconnect_real_chrome({"close_browser": True})  # 新增代码+RealChrome断开异常测试: 执行断开并要求关闭 agent Chrome；若没有这行代码，异常路径没有行为来源
                self.assertIn("real_chrome_connected=false", result)  # 新增代码+RealChrome断开异常测试: 断言即使异常也返回未连接状态；若没有这行代码，调用方可能看不到安全结果
                self.assertEqual(server.session_mode, "independent_chromium")  # 新增代码+RealChrome断开异常测试: 断言模式复位；若没有这行代码，状态工具可能继续误报真实 Chrome
                self.assertIsNone(server.browser)  # 新增代码+RealChrome断开异常测试: 断言 browser 引用清空；若没有这行代码，已断或异常的 CDP 对象可能残留
                self.assertIsNone(server.context)  # 新增代码+RealChrome断开异常测试: 断言 context 引用清空；若没有这行代码，真实 profile 上下文引用可能残留
                self.assertIsNone(server.playwright)  # 新增代码+RealChrome断开异常测试: 断言 Playwright 引用清空；若没有这行代码，坏 driver 可能被继续复用
                self.assertIsNone(server.chrome_process)  # 新增代码+RealChrome断开异常测试: 断言进程引用清空；若没有这行代码，后续可能重复管理旧进程
                self.assertEqual(server.pages, {})  # 新增代码+RealChrome断开异常测试: 断言页面映射清空；若没有这行代码，旧 page_id 会污染新会话
                self.assertEqual(server.element_refs, {})  # 新增代码+RealChrome断开异常测试: 断言元素引用清空；若没有这行代码，旧元素 id 会污染后续操作
    def test_browser_connect_real_chrome_rejects_path_like_profile_directory_without_leaking_it(self) -> None:  # 新增代码+RealChrome隐私测试: 验证路径式 profile_directory 会被拒绝且不泄漏；若没有这行代码，用户误传完整路径可能进入 Chrome 命令、返回或审计
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome隐私测试: 导入被测 server 类；若没有这行代码，无法直接调用连接 helper
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RealChrome隐私测试: 创建临时目录提供存在的 fake 路径；若没有这行代码，测试会依赖真实机器文件
            root = Path(raw_dir)  # 新增代码+RealChrome隐私测试: 把临时目录转成 Path；若没有这行代码，后续路径拼接不直观
            chrome_path = root / "chrome.exe"  # 新增代码+RealChrome隐私测试: 构造存在的 fake Chrome 可执行文件；若没有这行代码，测试会先失败在 chrome_path 检查
            user_data_dir = root / "User Data"  # 新增代码+RealChrome隐私测试: 构造存在的 fake User Data 目录；若没有这行代码，测试会先失败在 user_data_dir 检查
            chrome_path.write_text("", encoding="utf-8")  # 新增代码+RealChrome隐私测试: 创建 fake chrome.exe 文件；若没有这行代码，路径存在性检查无法通过
            user_data_dir.mkdir()  # 新增代码+RealChrome隐私测试: 创建 fake User Data 目录；若没有这行代码，profile 根目录检查无法通过
            server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome隐私测试: 创建 server 实例；若没有这行代码，无法调用 _connect_real_chrome_after_checks
            server.audit_logger = mock.Mock()  # 新增代码+RealChrome隐私测试: 用 fake audit logger 观察是否写审计；若没有这行代码，无法断言非法输入不落审计
            manager = mock.Mock()  # 新增代码+RealChrome隐私测试: 创建 fake profile manager；若没有这行代码，helper 会尝试真实路径发现
            manager.find_chrome_path.return_value = chrome_path  # 新增代码+RealChrome隐私测试: 指定存在的 fake Chrome 路径；若没有这行代码，测试无法进入 profile_directory 校验
            manager.find_user_data_dir.return_value = user_data_dir  # 新增代码+RealChrome隐私测试: 指定存在的 fake User Data 目录；若没有这行代码，测试无法进入 profile_directory 校验
            bad_profile_directory = "C:/Users/Alice/AppData/Local/Google/Chrome/User Data/Default"  # 新增代码+RealChrome隐私测试: 准备会泄漏用户名和路径结构的非法 profile_directory；若没有这行代码，无法覆盖复审指出的风险
            with mock.patch("learning_agent.browser_automation_mcp_server.subprocess.Popen") as popen_mock:  # 新增代码+RealChrome隐私测试: 监控是否尝试启动 Chrome；若没有这行代码，非法 profile_directory 可能仍被传给 Chrome 命令
                with self.assertRaisesRegex(RuntimeError, "profile_directory|profile 目录名非法") as raised:  # 新增代码+RealChrome隐私测试: 断言非法 profile 名会清晰报错；若没有这行代码，错误可能含糊或静默启动 Chrome
                    server._connect_real_chrome_after_checks({"profile_directory": bad_profile_directory}, manager)  # 新增代码+RealChrome隐私测试: 执行非法 profile_directory 连接路径；若没有这行代码，断言没有行为来源
            popen_mock.assert_not_called()  # 新增代码+RealChrome隐私测试: 断言非法 profile_directory 不会启动 Chrome；若没有这行代码，路径式内容可能进入 Chrome 参数
            server.audit_logger.record.assert_not_called()  # 新增代码+RealChrome隐私测试: 断言非法输入不写审计；若没有这行代码，审计可能保存用户路径
            error_text = str(raised.exception)  # 新增代码+RealChrome隐私测试: 提取错误文本用于检查脱敏；若没有这行代码，无法证明错误消息没有泄漏路径
            self.assertNotIn("Alice", error_text)  # 新增代码+RealChrome隐私测试: 断言错误不泄漏用户名；若没有这行代码，清晰报错可能仍暴露隐私
            self.assertNotIn("AppData", error_text)  # 新增代码+RealChrome隐私测试: 断言错误不泄漏 Windows profile 结构；若没有这行代码，目录结构泄漏不会被发现
            self.assertNotIn("C:/", error_text)  # 新增代码+RealChrome隐私测试: 断言错误不泄漏盘符路径；若没有这行代码，完整路径可能被回显给调用方
    def test_real_chrome_connect_failure_preserves_independent_session(self) -> None:  # 新增代码+RealChrome失败测试: 验证真实 Chrome 连接失败不破坏旧独立 Chromium；若省略: 切换失败可能误伤已有会话
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome失败测试: 导入被测 server 类；若省略: 无法调用连接 helper
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RealChrome失败测试: 创建临时 Chrome 路径和 profile 目录；若省略: 测试会依赖真实电脑路径
            root = Path(raw_dir)  # 新增代码+RealChrome失败测试: 把临时目录转成 Path；若省略: 后续路径拼接不直观
            chrome_path = root / "chrome.exe"  # 新增代码+RealChrome失败测试: 构造 fake Chrome 可执行文件路径；若省略: helper 会在路径检查前失败
            user_data_dir = root / "User Data"  # 新增代码+RealChrome失败测试: 构造 fake User Data 目录；若省略: helper 会在 profile 路径检查前失败
            chrome_path.write_text("", encoding="utf-8")  # 新增代码+RealChrome失败测试: 创建 fake chrome.exe 文件；若省略: 路径存在性检查无法通过
            user_data_dir.mkdir()  # 新增代码+RealChrome失败测试: 创建 fake User Data 目录；若省略: profile 目录存在性检查无法通过
            server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome失败测试: 创建 server 实例；若省略: 没有旧会话状态可保护
            old_browser = mock.Mock()  # 新增代码+RealChrome失败测试: 创建旧独立 Chromium browser 假对象；若省略: 无法断言旧 browser 未被关闭
            old_context = mock.Mock()  # 新增代码+RealChrome失败测试: 创建旧独立 Chromium context 假对象；若省略: 无法断言旧 context 未被关闭
            old_page = mock.Mock()  # 新增代码+RealChrome失败测试: 创建旧页面假对象；若省略: 无法断言页面映射保持不变
            fake_process = mock.Mock()  # 新增代码+RealChrome失败测试: 创建本次启动的 fake Chrome 进程；若省略: 无法断言失败清理会 terminate 本次进程
            server.browser = old_browser  # 新增代码+RealChrome失败测试: 注入旧 browser；若省略: 测试无法覆盖旧会话保护
            server.context = old_context  # 新增代码+RealChrome失败测试: 注入旧 context；若省略: 测试无法覆盖旧上下文保护
            server.pages = {"page-old": old_page}  # 新增代码+RealChrome失败测试: 注入旧页面映射；若省略: 无法确认 pages 未被清空
            server.current_page_id = "page-old"  # 新增代码+RealChrome失败测试: 注入旧当前页；若省略: 无法确认 current_page_id 未被清空
            manager = mock.Mock()  # 新增代码+RealChrome失败测试: 创建 fake manager；若省略: helper 会尝试真实路径发现
            manager.find_chrome_path.return_value = chrome_path  # 新增代码+RealChrome失败测试: 指定 fake chrome.exe 路径；若省略: helper 找不到浏览器路径
            manager.find_user_data_dir.return_value = user_data_dir  # 新增代码+RealChrome失败测试: 指定 fake User Data 路径；若省略: helper 找不到 profile 目录
            with mock.patch("learning_agent.browser_automation_mcp_server.subprocess.Popen", return_value=fake_process):  # 新增代码+RealChrome失败测试: 阻止真的启动 Chrome；若省略: 测试会触碰真实进程
                with mock.patch("learning_agent.browser_automation_mcp_server.wait_for_cdp_endpoint", return_value=False):  # 新增代码+RealChrome失败测试: 模拟 CDP 未就绪失败；若省略: 测试不可控且可能等待真实端口
                    with self.assertRaisesRegex(RuntimeError, "browser_connect_real_chrome 失败"):  # 新增代码+RealChrome失败测试: 断言连接失败清晰抛出；若省略: 失败可能被静默吞掉
                        server._connect_real_chrome_after_checks({}, manager)  # 新增代码+RealChrome失败测试: 直接调用 helper 覆盖失败清理；若省略: 测试不到切换中的内部状态保护
            self.assertIs(server.browser, old_browser)  # 新增代码+RealChrome失败测试: 断言旧 browser 引用保持；若省略: 失败切换可能清空旧会话不被发现
            self.assertIs(server.context, old_context)  # 新增代码+RealChrome失败测试: 断言旧 context 引用保持；若省略: 失败切换可能破坏旧上下文不被发现
            self.assertEqual(server.pages, {"page-old": old_page})  # 新增代码+RealChrome失败测试: 断言旧页面映射保持；若省略: 失败切换清空 pages 不会暴露
            self.assertEqual(server.current_page_id, "page-old")  # 新增代码+RealChrome失败测试: 断言旧当前页保持；若省略: 失败切换清空 current_page_id 不会暴露
            old_browser.close.assert_not_called()  # 新增代码+RealChrome失败测试: 断言旧 browser 没有被关闭；若省略: 误伤独立 Chromium 进程不会暴露
            old_context.close.assert_not_called()  # 新增代码+RealChrome失败测试: 断言旧 context 没有被关闭；若省略: 误伤独立上下文不会暴露
            fake_process.terminate.assert_called_once()  # 新增代码+RealChrome失败测试: 断言只终止本次启动失败的 Chrome；若省略: 失败进程残留不会暴露
    def test_real_chrome_success_closes_old_independent_chromium(self) -> None:  # 新增代码+RealChrome成功切换测试: 验证成功切换时释放旧独立 Chromium；若省略: 旧浏览器会变成不可达残留
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome成功切换测试: 导入被测 server 类；若省略: 无法调用连接 helper
        with tempfile.TemporaryDirectory() as raw_dir:  # 修改代码+RealChrome成功切换测试: 保留临时目录只作为 server 工作区；若没有这行代码，测试可能污染项目目录
            chrome_path = Path("C:/Users/Alice/AppData/Local/Google/Chrome/Application/chrome.exe")  # 修改代码+RealChrome隐私测试: 使用含用户名和 AppData 的 fake Chrome 路径；若没有这行代码，无法证明返回和审计会脱敏本机路径
            user_data_dir = Path("C:/Users/Alice/AppData/Local/Google/Chrome/User Data")  # 修改代码+RealChrome隐私测试: 使用含用户名和 AppData 的 fake User Data 路径；若没有这行代码，profile 隐私泄漏不会被测试覆盖
            server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome成功切换测试: 创建 server 实例；若省略: 没有旧会话状态可设置
            old_browser = mock.Mock()  # 新增代码+RealChrome成功切换测试: 创建旧独立 browser；若省略: 无法断言旧 browser.close 被调用
            old_context = mock.Mock()  # 新增代码+RealChrome成功切换测试: 创建旧独立 context；若省略: 无法断言旧 context.close 被调用
            old_page = mock.Mock()  # 新增代码+RealChrome成功切换测试: 创建旧页面；若省略: 无法设置旧 pages 映射
            real_page = mock.Mock()  # 新增代码+RealChrome成功切换测试: 创建新真实 Chrome 页面；若省略: 无法验证新页面被登记
            real_browser = mock.Mock()  # 新增代码+RealChrome成功切换测试: 创建新真实 Chrome browser；若省略: 无法断言新 browser 不被 close
            real_context = mock.Mock()  # 新增代码+RealChrome成功切换测试: 创建新真实 Chrome context；若省略: 无法模拟 context.pages/on
            fake_process = mock.Mock()  # 新增代码+RealChrome成功切换测试: 创建 fake Chrome 进程；若省略: 无法断言成功后 process 被保存
            manager = mock.Mock()  # 新增代码+RealChrome成功切换测试: 创建 fake manager；若省略: helper 会尝试真实路径发现
            playwright_driver = mock.Mock()  # 新增代码+RealChrome成功切换测试: 创建 fake Playwright driver；若省略: 无法模拟 connect_over_cdp
            audit_logger = mock.Mock()  # 新增代码+RealChrome隐私测试: 创建 fake audit logger 检查审计载荷；若没有这行代码，无法证明 audit 没有写完整本机路径
            real_context.pages = [real_page]  # 新增代码+RealChrome成功切换测试: 模拟真实 Chrome 已有页面；若省略: 成功结果 pages 数量不可验证
            real_browser.contexts = [real_context]  # 新增代码+RealChrome成功切换测试: 模拟 CDP browser 提供上下文；若省略: helper 会按无 context 失败
            playwright_driver.chromium.connect_over_cdp.return_value = real_browser  # 新增代码+RealChrome成功切换测试: 模拟 Playwright 成功连接 CDP；若省略: helper 无法得到 real_browser
            manager.find_chrome_path.return_value = chrome_path  # 新增代码+RealChrome成功切换测试: 指定 fake chrome.exe 路径；若省略: helper 找不到 Chrome
            manager.find_user_data_dir.return_value = user_data_dir  # 新增代码+RealChrome成功切换测试: 指定 fake User Data 路径；若省略: helper 找不到 profile
            server.playwright = playwright_driver  # 新增代码+RealChrome成功切换测试: 复用同一个 Playwright driver；若省略: helper 会尝试启动真实 Playwright
            server.session_mode = "independent_chromium"  # 新增代码+RealChrome成功切换测试: 标记旧会话是独立 Chromium；若省略: 旧对象关闭条件不明确
            server.browser = old_browser  # 新增代码+RealChrome成功切换测试: 注入旧 browser；若省略: 无法验证旧 browser 被安全关闭
            server.context = old_context  # 新增代码+RealChrome成功切换测试: 注入旧 context；若省略: 无法验证旧 context 被安全关闭
            server.pages = {"page-old": old_page}  # 新增代码+RealChrome成功切换测试: 注入旧页面映射；若省略: 无法验证切换后 pages 被替换
            server.current_page_id = "page-old"  # 新增代码+RealChrome成功切换测试: 注入旧当前页；若省略: 无法验证当前页被新登记逻辑更新
            server.audit_logger = audit_logger  # 新增代码+RealChrome隐私测试: 注入 fake audit logger；若没有这行代码，审计断言可能读取真实文件而不稳定
            with mock.patch("learning_agent.browser_automation_mcp_server.subprocess.Popen", return_value=fake_process):  # 新增代码+RealChrome成功切换测试: 阻止真的启动 Chrome；若省略: 测试会触碰真实进程
                with mock.patch("learning_agent.browser_automation_mcp_server.wait_for_cdp_endpoint", return_value=True):  # 新增代码+RealChrome成功切换测试: 模拟 CDP 就绪；若省略: 测试会等待真实端口
                    with mock.patch("pathlib.Path.exists", return_value=True):  # 新增代码+RealChrome隐私测试: 让 fake Windows 路径通过存在性检查；若没有这行代码，测试会依赖本机是否存在 Alice 路径
                        result = server._connect_real_chrome_after_checks({"profile_directory": "Default"}, manager)  # 修改代码+RealChrome隐私测试: 显式传入 profile_directory 作为允许公开的摘要；若没有这行代码，无法断言成功输出只保留 profile 名称
            old_context.close.assert_called_once()  # 新增代码+RealChrome成功切换测试: 断言旧独立 context 被关闭；若省略: 旧 context 会不可达残留
            old_browser.close.assert_called_once()  # 新增代码+RealChrome成功切换测试: 断言旧独立 browser 被关闭；若省略: 旧 browser 进程会不可达残留
            real_browser.close.assert_not_called()  # 新增代码+RealChrome成功切换测试: 断言新真实 Chrome browser 没有被关闭；若省略: 修复可能误关新连接
            real_browser.disconnect.assert_not_called()  # 新增代码+RealChrome成功切换测试: 断言成功路径不误断开新 CDP；若省略: 新连接可能刚建立就被断开
            self.assertIn("mode=real_chrome", result)  # 新增代码+RealChrome成功切换测试: 断言返回文本说明真实 Chrome 模式；若省略: 成功输出回归不明显
            self.assertIn("profile=Default", result)  # 新增代码+RealChrome隐私测试: 断言成功输出只包含非敏感 profile 名称；若没有这行代码，完整 user_data_dir 可能继续外泄
            status_result = server.browser_profile_status({})  # 新增代码+RealChrome隐私测试: 读取连接后的状态文本；若没有这行代码，无法证明 status 的 profile 字段也已脱敏
            audit_payload = audit_logger.record.call_args.args[1]  # 新增代码+RealChrome隐私测试: 取出 connect_real_chrome 审计载荷；若没有这行代码，无法检查 audit 是否写入完整路径
            combined_text = "\n".join([result, status_result, str(audit_payload)])  # 新增代码+RealChrome隐私测试: 合并所有可能泄漏的输出文本；若没有这行代码，需要重复检查多个字符串且容易漏掉
            self.assertNotIn("Alice", combined_text)  # 新增代码+RealChrome隐私测试: 断言不泄漏 Windows 用户名；若没有这行代码，状态或审计可能暴露真实用户
            self.assertNotIn("AppData", combined_text)  # 新增代码+RealChrome隐私测试: 断言不泄漏 Windows profile 目录结构；若没有这行代码，路径结构泄漏不会暴露
            self.assertNotIn("C:/Users/Alice/AppData/Local/Google/Chrome/User Data", combined_text)  # 新增代码+RealChrome隐私测试: 断言不泄漏完整 User Data 路径；若没有这行代码，完整本机路径可能进入输出或审计
            self.assertNotIn("C:\\", combined_text)  # 新增代码+RealChrome隐私测试: 断言不输出 Windows 盘符路径；若没有这行代码，反斜杠路径泄漏可能漏测
            self.assertNotIn("/Users/", combined_text)  # 新增代码+RealChrome隐私测试: 断言不输出 macOS 用户路径样式；若没有这行代码，跨平台路径泄漏风险没有测试保护
            self.assertEqual(audit_payload["profile_directory"], "Default")  # 新增代码+RealChrome隐私测试: 断言审计只记录 profile 名称；若没有这行代码，审计字段可能丢失必要但非敏感的定位信息
            self.assertIs(audit_payload["chrome_path_detected"], True)  # 新增代码+RealChrome隐私测试: 断言审计只记录是否检测到 Chrome 路径；若没有这行代码，审计可能回退写完整 chrome_path
            self.assertIs(audit_payload["user_data_dir_detected"], True)  # 新增代码+RealChrome隐私测试: 断言审计只记录是否检测到 User Data；若没有这行代码，审计可能回退写完整 user_data_dir
            self.assertNotIn("chrome_path", audit_payload)  # 新增代码+RealChrome隐私测试: 断言审计不含完整 chrome_path 字段；若没有这行代码，本机可执行文件路径可能泄漏
            self.assertNotIn("user_data_dir", audit_payload)  # 新增代码+RealChrome隐私测试: 断言审计不含完整 user_data_dir 字段；若没有这行代码，真实 profile 根路径可能泄漏
            self.assertEqual(server.session_mode, "real_chrome")  # 新增代码+RealChrome成功切换测试: 断言状态切到真实 Chrome；若省略: 内部状态可能未切换
            self.assertIs(server.browser, real_browser)  # 新增代码+RealChrome成功切换测试: 断言 server browser 指向新真实 Chrome；若省略: 可能仍指旧 browser
            self.assertIs(server.context, real_context)  # 新增代码+RealChrome成功切换测试: 断言 server context 指向新真实 Chrome；若省略: 可能仍指旧 context
            self.assertIs(server.chrome_process, fake_process)  # 新增代码+RealChrome成功切换测试: 断言成功后保存本次 Chrome 进程引用；若省略: 后续断开无法识别进程
    def test_real_chrome_audit_failure_restores_old_independent_session(self) -> None:  # 新增代码+RealChrome事务测试: 验证准备步骤失败会恢复旧独立会话；若省略: audit/on/page 注册失败可能留下半切换状态
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome事务测试: 导入被测 server 类；若省略: 无法直接调用连接 helper
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RealChrome事务测试: 创建临时路径避免触碰真实 Chrome；若省略: 测试依赖真实机器环境
            root = Path(raw_dir)  # 新增代码+RealChrome事务测试: 转成 Path 方便拼接；若省略: 后续路径操作不直观
            chrome_path = root / "chrome.exe"  # 新增代码+RealChrome事务测试: 构造 fake Chrome 可执行文件；若省略: helper 会在路径检查失败
            user_data_dir = root / "User Data"  # 新增代码+RealChrome事务测试: 构造 fake User Data 目录；若省略: helper 会在 profile 检查失败
            chrome_path.write_text("", encoding="utf-8")  # 新增代码+RealChrome事务测试: 创建 fake chrome.exe 文件；若省略: chrome_path.exists 无法通过
            user_data_dir.mkdir()  # 新增代码+RealChrome事务测试: 创建 fake User Data 目录；若省略: user_data_dir.exists 无法通过
            server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome事务测试: 创建 server 实例；若省略: 没有旧状态可恢复
            old_browser = mock.Mock()  # 新增代码+RealChrome事务测试: 创建旧独立 browser；若省略: 无法断言旧 browser 未关闭且被恢复
            old_context = mock.Mock()  # 新增代码+RealChrome事务测试: 创建旧独立 context；若省略: 无法断言旧 context 未关闭且被恢复
            old_page = mock.Mock()  # 新增代码+RealChrome事务测试: 创建旧页面；若省略: 无法验证旧 pages 恢复
            real_page = mock.Mock()  # 新增代码+RealChrome事务测试: 创建新真实 Chrome 页面；若省略: 无法覆盖页面准备阶段
            real_browser = mock.Mock()  # 新增代码+RealChrome事务测试: 创建新真实 Chrome browser；若省略: 无法断言失败时 disconnect
            real_context = mock.Mock()  # 新增代码+RealChrome事务测试: 创建新真实 Chrome context；若省略: 无法模拟 context.on/pages
            fake_process = mock.Mock()  # 新增代码+RealChrome事务测试: 创建 fake Chrome 进程；若省略: 无法断言失败时 terminate
            manager = mock.Mock()  # 新增代码+RealChrome事务测试: 创建 fake manager；若省略: helper 会尝试真实路径发现
            playwright_driver = mock.Mock()  # 新增代码+RealChrome事务测试: 创建 fake Playwright driver；若省略: helper 会尝试真实 Playwright
            old_pages = {"page-old": old_page}  # 新增代码+RealChrome事务测试: 保存旧页面映射对象；若省略: 无法精确断言恢复内容
            old_element_refs = {"page-old": [{"id": 1}]}  # 新增代码+RealChrome事务测试: 保存旧元素引用；若省略: 无法验证 element_refs 恢复
            real_context.pages = [real_page]  # 新增代码+RealChrome事务测试: 模拟真实 Chrome 已有页面；若省略: helper 不会覆盖页面准备路径
            real_browser.contexts = [real_context]  # 新增代码+RealChrome事务测试: 模拟 CDP browser 有上下文；若省略: helper 会提前失败
            playwright_driver.chromium.connect_over_cdp.return_value = real_browser  # 新增代码+RealChrome事务测试: 模拟 CDP 连接返回 real_browser；若省略: helper 无法连接成功到准备阶段
            manager.find_chrome_path.return_value = chrome_path  # 新增代码+RealChrome事务测试: 指定 fake Chrome 路径；若省略: helper 找不到 Chrome
            manager.find_user_data_dir.return_value = user_data_dir  # 新增代码+RealChrome事务测试: 指定 fake User Data 路径；若省略: helper 找不到 profile
            server.playwright = playwright_driver  # 新增代码+RealChrome事务测试: 注入可复用 Playwright driver；若省略: helper 会尝试启动真实驱动
            server.session_mode = "independent_chromium"  # 新增代码+RealChrome事务测试: 标记旧模式为独立 Chromium；若省略: 旧对象关闭/恢复边界不明确
            server.browser = old_browser  # 新增代码+RealChrome事务测试: 注入旧 browser；若省略: 无法验证失败恢复 browser
            server.context = old_context  # 新增代码+RealChrome事务测试: 注入旧 context；若省略: 无法验证失败恢复 context
            server.pages = dict(old_pages)  # 新增代码+RealChrome事务测试: 注入旧 pages 副本；若省略: 无法验证失败恢复页面映射
            server.element_refs = dict(old_element_refs)  # 新增代码+RealChrome事务测试: 注入旧元素引用副本；若省略: 无法验证失败恢复元素引用
            server.current_page_id = "page-old"  # 新增代码+RealChrome事务测试: 注入旧当前页；若省略: 无法验证 current_page_id 恢复
            server.next_page_index = 7  # 新增代码+RealChrome事务测试: 注入旧页面编号；若省略: 无法验证 next_page_index 恢复
            server.real_chrome_endpoint = "old-endpoint"  # 新增代码+RealChrome事务测试: 注入旧 endpoint 摘要；若省略: 无法验证 endpoint 恢复
            server.real_chrome_profile_summary = "old-profile"  # 新增代码+RealChrome事务测试: 注入旧 profile 摘要；若省略: 无法验证 profile 恢复
            server.audit_logger = mock.Mock()  # 新增代码+RealChrome事务测试: 替换 audit logger 为可控 fake；若省略: 无法稳定模拟 audit 失败
            server.audit_logger.record.side_effect = RuntimeError("audit boom")  # 新增代码+RealChrome事务测试: 模拟所有准备末尾 audit 失败；若省略: 测试不会触发事务回滚
            with mock.patch("learning_agent.browser_automation_mcp_server.subprocess.Popen", return_value=fake_process):  # 新增代码+RealChrome事务测试: 阻止真的启动 Chrome；若省略: 测试会触碰真实进程
                with mock.patch("learning_agent.browser_automation_mcp_server.wait_for_cdp_endpoint", return_value=True):  # 新增代码+RealChrome事务测试: 模拟 CDP 就绪；若省略: 测试会等待真实端口
                    with self.assertRaisesRegex(RuntimeError, "browser_connect_real_chrome 失败"):  # 新增代码+RealChrome事务测试: 断言准备失败会作为连接失败抛出；若省略: 静默失败不会暴露
                        server._connect_real_chrome_after_checks({}, manager)  # 新增代码+RealChrome事务测试: 执行被测事务切换；若省略: 后续断言没有行为来源
            self.assertIs(server.browser, old_browser)  # 新增代码+RealChrome事务测试: 断言旧 browser 已恢复；若省略: 半切换状态不会暴露
            self.assertIs(server.context, old_context)  # 新增代码+RealChrome事务测试: 断言旧 context 已恢复；若省略: 半切换 context 不会暴露
            self.assertEqual(server.pages, old_pages)  # 新增代码+RealChrome事务测试: 断言旧 pages 已恢复；若省略: 页面映射被污染不会暴露
            self.assertEqual(server.element_refs, old_element_refs)  # 新增代码+RealChrome事务测试: 断言旧元素引用已恢复；若省略: 元素缓存被污染不会暴露
            self.assertEqual(server.current_page_id, "page-old")  # 新增代码+RealChrome事务测试: 断言旧当前页已恢复；若省略: 默认操作目标可能丢失
            self.assertEqual(server.next_page_index, 7)  # 新增代码+RealChrome事务测试: 断言旧页面编号已恢复；若省略: 后续 page_id 可能跳号或冲突
            self.assertEqual(server.session_mode, "independent_chromium")  # 新增代码+RealChrome事务测试: 断言失败后仍是独立 Chromium；若省略: 状态可能误报 real_chrome
            self.assertEqual(server.real_chrome_endpoint, "old-endpoint")  # 新增代码+RealChrome事务测试: 断言旧 endpoint 摘要已恢复；若省略: 状态字段可能污染
            self.assertEqual(server.real_chrome_profile_summary, "old-profile")  # 新增代码+RealChrome事务测试: 断言旧 profile 摘要已恢复；若省略: 状态字段可能污染
            old_context.close.assert_not_called()  # 新增代码+RealChrome事务测试: 断言旧 context 在失败时没有被关闭；若省略: 失败切换可能破坏旧会话
            old_browser.close.assert_not_called()  # 新增代码+RealChrome事务测试: 断言旧 browser 在失败时没有被关闭；若省略: 失败切换可能关闭旧浏览器
            real_browser.disconnect.assert_called_once()  # 新增代码+RealChrome事务测试: 断言新 real browser 失败时断开 CDP；若省略: 新连接可能残留
            real_browser.close.assert_not_called()  # 新增代码+RealChrome事务测试: 断言失败时不调用 close 误关真实 Chrome；若省略: 清理可能伤及真实 Chrome
            fake_process.terminate.assert_called_once()  # 新增代码+RealChrome事务测试: 断言本次启动进程被终止；若省略: 失败 Chrome 进程可能残留
    def test_real_chrome_pending_page_close_event_does_not_touch_old_pages(self) -> None:  # 新增代码+RealChrome事件守卫测试: 验证准备期真实页面 close 事件不会误删旧 page-1；若省略: pending callback 污染旧会话的风险不会暴露
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+RealChrome事件守卫测试: 导入被测 server 类；若省略: 无法直接调用真实 Chrome 连接 helper
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RealChrome事件守卫测试: 创建临时路径避免依赖真实 Chrome；若省略: 测试会触碰用户机器环境
            root = Path(raw_dir)  # 新增代码+RealChrome事件守卫测试: 把临时目录转成 Path；若省略: 后续 fake 路径拼接不直观
            chrome_path = root / "chrome.exe"  # 新增代码+RealChrome事件守卫测试: 构造 fake Chrome 可执行文件；若省略: helper 会在路径检查阶段失败
            user_data_dir = root / "User Data"  # 新增代码+RealChrome事件守卫测试: 构造 fake User Data 目录；若省略: helper 会在 profile 路径检查阶段失败
            chrome_path.write_text("", encoding="utf-8")  # 新增代码+RealChrome事件守卫测试: 创建 fake chrome.exe 文件；若省略: chrome_path.exists 无法通过
            user_data_dir.mkdir()  # 新增代码+RealChrome事件守卫测试: 创建 fake profile 根目录；若省略: user_data_dir.exists 无法通过
            server = BrowserAutomationServer(TEST_ROOT)  # 新增代码+RealChrome事件守卫测试: 创建 server 实例；若省略: 没有旧状态可布置
            old_browser = mock.Mock()  # 新增代码+RealChrome事件守卫测试: 创建旧独立 browser；若省略: 无法断言失败时未关闭旧 browser
            old_context = mock.Mock()  # 新增代码+RealChrome事件守卫测试: 创建旧独立 context；若省略: 无法断言失败时未关闭旧 context
            old_page = mock.Mock()  # 新增代码+RealChrome事件守卫测试: 创建旧 page-1 页面；若省略: 无法验证 close callback 是否误删同名旧页面
            real_page = mock.Mock()  # 新增代码+RealChrome事件守卫测试: 创建真实 Chrome fake 页面；若省略: 无法模拟准备期页面事件绑定
            real_browser = mock.Mock()  # 新增代码+RealChrome事件守卫测试: 创建真实 Chrome fake browser；若省略: 无法断言失败时断开新 CDP
            real_context = mock.Mock()  # 新增代码+RealChrome事件守卫测试: 创建真实 Chrome fake context；若省略: 无法模拟 pages/on 行为
            fake_process = mock.Mock()  # 新增代码+RealChrome事件守卫测试: 创建本次启动的 fake 进程；若省略: 无法断言失败时 terminate
            manager = mock.Mock()  # 新增代码+RealChrome事件守卫测试: 创建 fake profile manager；若省略: helper 会尝试真实路径发现
            playwright_driver = mock.Mock()  # 新增代码+RealChrome事件守卫测试: 创建 fake Playwright driver；若省略: helper 会尝试启动真实 Playwright
            observed_pages_during_audit: list[dict[str, object]] = []  # 修改代码+RealChrome事件守卫测试: 使用内置 object 记录 audit 前 pages 状态；若省略: 未导入 Any 会让测试在验证行为前报错
            def fire_close_immediately(event_name: str, callback: object) -> None:  # 修改代码+RealChrome事件守卫测试: 使用内置 object 避免额外导入；若省略: 测试会因类型名缺失而非产品行为失败
                if event_name == "close":  # 新增代码+RealChrome事件守卫测试: 只让 close 事件抢跑；若省略: console/request 等无关事件会干扰本测试目标
                    callback()  # 新增代码+RealChrome事件守卫测试: 立即执行 close 回调；若省略: 测试不会触发误删旧 page-1 的风险
            def audit_fails_after_observing_state(*args: object, **kwargs: object) -> None:  # 修改代码+RealChrome事件守卫测试: 使用内置 object 标注 fake audit 参数；若省略: 未导入 Any 会遮住真正红灯
                observed_pages_during_audit.append(dict(server.pages))  # 新增代码+RealChrome事件守卫测试: 保存 audit 发生时的 pages 快照；若省略: 无法证明 pending close callback 是否 no-op
                raise RuntimeError("audit boom")  # 新增代码+RealChrome事件守卫测试: 触发回滚路径；若省略: 测试会走成功切换而不是失败保护
            real_page.on.side_effect = fire_close_immediately  # 新增代码+RealChrome事件守卫测试: 让真实页面绑定 close 时立即触发回调；若省略: 风险路径不会被执行
            real_context.pages = [real_page]  # 新增代码+RealChrome事件守卫测试: 模拟真实 Chrome 已有一个页面；若省略: helper 不会绑定已有页面事件
            real_browser.contexts = [real_context]  # 新增代码+RealChrome事件守卫测试: 模拟 CDP browser 有 context；若省略: helper 会提前按无 context 失败
            playwright_driver.chromium.connect_over_cdp.return_value = real_browser  # 新增代码+RealChrome事件守卫测试: 模拟 Playwright 成功连接 CDP；若省略: helper 无法进入页面准备阶段
            manager.find_chrome_path.return_value = chrome_path  # 新增代码+RealChrome事件守卫测试: 指定 fake Chrome 路径；若省略: helper 找不到浏览器
            manager.find_user_data_dir.return_value = user_data_dir  # 新增代码+RealChrome事件守卫测试: 指定 fake User Data 路径；若省略: helper 找不到 profile
            server.playwright = playwright_driver  # 新增代码+RealChrome事件守卫测试: 注入 fake Playwright driver；若省略: helper 会启动真实 driver
            server.session_mode = "independent_chromium"  # 新增代码+RealChrome事件守卫测试: 标记旧会话为独立 Chromium；若省略: 旧对象关闭/恢复边界不明确
            server.browser = old_browser  # 新增代码+RealChrome事件守卫测试: 注入旧 browser；若省略: 无法验证旧 browser 未关闭
            server.context = old_context  # 新增代码+RealChrome事件守卫测试: 注入旧 context；若省略: 无法验证旧 context 未关闭
            server.pages = {"page-1": old_page}  # 新增代码+RealChrome事件守卫测试: 注入旧 page-1，专门覆盖同名误删风险；若省略: close callback 删除不存在 id 时风险不明显
            server.current_page_id = "page-1"  # 新增代码+RealChrome事件守卫测试: 设置旧当前页为 page-1；若省略: 无法验证 pending close 是否清空当前页
            server.audit_logger = mock.Mock()  # 新增代码+RealChrome事件守卫测试: 替换 audit logger 为可控 fake；若省略: 无法稳定触发 audit 失败
            server.audit_logger.record.side_effect = audit_fails_after_observing_state  # 新增代码+RealChrome事件守卫测试: audit 先观察再失败；若省略: 无法判断准备期污染是否发生
            with mock.patch("learning_agent.browser_automation_mcp_server.subprocess.Popen", return_value=fake_process):  # 新增代码+RealChrome事件守卫测试: 阻止真的启动 Chrome；若省略: 测试会触碰真实进程
                with mock.patch("learning_agent.browser_automation_mcp_server.wait_for_cdp_endpoint", return_value=True):  # 新增代码+RealChrome事件守卫测试: 模拟 CDP 就绪；若省略: 测试会等待真实端口
                    with self.assertRaisesRegex(RuntimeError, "browser_connect_real_chrome 失败"):  # 新增代码+RealChrome事件守卫测试: 断言 audit 失败会清晰抛出；若省略: 失败可能被吞掉
                        server._connect_real_chrome_after_checks({}, manager)  # 新增代码+RealChrome事件守卫测试: 执行准备期事件抢跑路径；若省略: 后续断言没有行为来源
            self.assertEqual(observed_pages_during_audit, [{"page-1": old_page}])  # 新增代码+RealChrome事件守卫测试: 断言 audit 前旧 page-1 没被 pending close 删掉；若省略: 只看最终回滚会漏掉准备期污染
            self.assertEqual(server.pages, {"page-1": old_page})  # 新增代码+RealChrome事件守卫测试: 断言回滚后旧页面表完整；若省略: 最终状态破坏不会暴露
            self.assertEqual(server.current_page_id, "page-1")  # 新增代码+RealChrome事件守卫测试: 断言回滚后当前页仍是旧 page-1；若省略: 默认操作目标丢失不会暴露
            self.assertEqual(server.session_mode, "independent_chromium")  # 新增代码+RealChrome事件守卫测试: 断言失败后仍是独立 Chromium；若省略: 状态误报不会暴露
            old_context.close.assert_not_called()  # 新增代码+RealChrome事件守卫测试: 断言失败时旧 context 未关闭；若省略: 旧会话被破坏不会暴露
            old_browser.close.assert_not_called()  # 新增代码+RealChrome事件守卫测试: 断言失败时旧 browser 未关闭；若省略: 旧浏览器被关闭不会暴露
            real_browser.disconnect.assert_called_once()  # 新增代码+RealChrome事件守卫测试: 断言本次 real CDP 连接被断开；若省略: 失败连接可能残留
            fake_process.terminate.assert_called_once()  # 新增代码+RealChrome事件守卫测试: 断言本次启动进程被终止；若省略: 失败 Chrome 进程可能残留
    def test_real_chrome_workflow_requires_profile_status_before_connect_and_browser_actions(self) -> None:  # 新增代码+RealChromeWorkflow: 验证真实 Chrome 工具必须先完成 profile status workflow；若没有这行代码，用户要求真实浏览器时可能仍误走独立 Chromium
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RealChromeWorkflow: 创建临时工作区隔离 agent 状态；若没有这行代码，测试可能污染真实目录
            workspace = Path(raw_dir)  # 新增代码+RealChromeWorkflow: 把临时目录转为 Path；若没有这行代码，后续构造 agent 不清晰
            fake_client = FakeMcpClient(tools=[  # 新增代码+RealChromeWorkflow: 构造只含真实 Chrome workflow 相关工具的 fake browser server；若没有这行代码，测试没有目标 MCP 工具
                {"name": "browser_profile_status", "description": "Status", "inputSchema": {"type": "object", "properties": {}}},  # 新增代码+RealChromeWorkflow: 暴露只读状态工具；若没有这行代码，workflow 没有安全前置入口
                {"name": "browser_connect_real_chrome", "description": "Connect", "inputSchema": {"type": "object", "properties": {"confirm_real_profile": {"type": "boolean"}}, "required": ["confirm_real_profile"]}},  # 新增代码+RealChromeWorkflow: 暴露真实 Chrome 连接工具；若没有这行代码，测试无法验证 skill/workflow gate
                {"name": "browser_open", "description": "Open", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},  # 新增代码+RealChromeWorkflow: 暴露普通浏览器打开工具；若没有这行代码，无法验证真实浏览器意图会拦截独立打开动作
            ], result_prefix="real_chrome_connected=true")  # 新增代码+RealChromeWorkflow: 让连接结果包含机器可读成功标记；若没有这行代码，workflow 不会推进到 connected
            registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+RealChromeWorkflow: 使用 browser_automation server 名触发真实 Chrome gate 映射；若没有这行代码，MCP 工具不会带 real_chrome gate
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+RealChromeWorkflow: 创建自动授权 agent；若没有这行代码，无法执行 fake MCP 工具
            agent.real_chrome_requested = True  # 新增代码+RealChromeWorkflow: 模拟用户明确要求真实桌面 Chrome；若没有这行代码，browser_open 不会被真实 Chrome workflow 拦截
            connect_before_status = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "select:mcp__browser_automation__browser_connect_real_chrome"}))  # 新增代码+RealChromeWorkflow: 在 status 前尝试加载 connect；若没有这行代码，无法证明 workflow gate 生效
            open_before_connect = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "select:mcp__browser_automation__browser_open"}))  # 新增代码+RealChromeWorkflow: 在 connect 前尝试加载普通打开工具；若没有这行代码，无法证明真实浏览器意图会拦住独立浏览器动作
            status_output = agent._execute_tool(ToolCall(name="mcp__browser_automation__browser_profile_status", arguments={}))  # 新增代码+RealChromeWorkflow: 执行只读状态工具满足前置 workflow；若没有这行代码，connect 不应被解锁
            connect_after_status = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "select:mcp__browser_automation__browser_connect_real_chrome"}))  # 新增代码+RealChromeWorkflow: status 后再次加载 connect；若没有这行代码，无法证明前置 workflow 会解锁连接工具
            connect_output = agent._execute_tool(ToolCall(name="mcp__browser_automation__browser_connect_real_chrome", arguments={"confirm_real_profile": True}))  # 新增代码+RealChromeWorkflow: 调用连接工具推进 connected 状态；若没有这行代码，browser_open 不会在连接后放行
            open_after_connect = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "select:mcp__browser_automation__browser_open"}))  # 新增代码+RealChromeWorkflow: 连接后再加载 browser_open；若没有这行代码，无法证明真实 Chrome workflow 完成后允许后续浏览器动作
            self.assertIn("needs_skill", connect_before_status)  # 新增代码+RealChromeWorkflow: 断言 status 前连接工具被 skill gate 拦截；若没有这行代码，高风险连接可能直接可选
            self.assertIn("needs_workflow", open_before_connect)  # 新增代码+RealChromeWorkflow: 断言真实浏览器需求下独立打开工具被 workflow 拦截；若没有这行代码，模型可能绕开真实 Chrome 连接
            self.assertIn("browser_profile_status", status_output)  # 新增代码+RealChromeWorkflow: 断言 status 工具真实执行；若没有这行代码，后续状态解锁可能是假阳性
            self.assertIn("real_chrome", agent.tool_policy_context.loaded_skills)  # 新增代码+RealChromeWorkflow: 断言 status 后 skill gate 被满足；若没有这行代码，connect 解锁依据不明确
            self.assertIn("real_chrome_profile_ready", agent.tool_policy_context.completed_workflows)  # 新增代码+RealChromeWorkflow: 断言 status 后 workflow gate 被满足；若没有这行代码，connect 解锁依据不完整
            self.assertIn("已加载", connect_after_status)  # 新增代码+RealChromeWorkflow: 断言 connect 在前置完成后可 select；若没有这行代码，真实 Chrome workflow 无法继续
            self.assertIn("real_chrome_connected=true", connect_output)  # 新增代码+RealChromeWorkflow: 断言连接结果包含成功标记；若没有这行代码，connected 状态可能没有真实来源
            self.assertIn("real_chrome_connected", agent.tool_policy_context.completed_workflows)  # 新增代码+RealChromeWorkflow: 断言连接后记录 workflow 完成；若没有这行代码，后续浏览器动作仍会被错误拦截
            self.assertIn("已加载", open_after_connect)  # 新增代码+RealChromeWorkflow: 断言真实 Chrome 已连接后普通浏览器动作可以进入工具池；若没有这行代码，连接成功后仍无法操作页面
    def test_real_chrome_request_blocks_independent_browser_until_connected(self) -> None:  # 新增代码+PromptArchitectureV1: 保留 Phase 7 计划中的回归测试名并复用真实 Chrome workflow 测试；若没有这行代码，最终验证命令会因测试名不匹配失败
        self.test_real_chrome_workflow_requires_profile_status_before_connect_and_browser_actions()  # 新增代码+PromptArchitectureV1: 调用已有完整测试逻辑避免复制一大段场景；若没有这行代码，别名测试不会真正验证独立浏览器阻断行为
    def test_runtime_instructions_mentions_real_chrome_profile_mode(self) -> None:  # 新增代码+RealChrome文档测试: 验证运行规则写清真实 Chrome profile 高风险模式；若没有这行代码，文档缺少真实登录态边界也不会让测试失败
        runtime_text = self._dynamic_prompt_file().read_text(encoding="utf-8")  # 新增代码+RealChrome文档测试: 读取模型实际会加载的运行时规则；若没有这行代码，测试无法检查真实交付文档
        expected_terms = ("browser_connect_real_chrome", "confirm_real_profile", "日常 Chrome profile", "cookies", "localStorage", "sessionStorage", "token", "browser_profile_status")  # 新增代码+RealChrome文档测试: 集中列出必须出现的安全关键词；若没有这行代码，遗漏任一关键边界都可能悄悄通过
        for expected_term in expected_terms:  # 新增代码+RealChrome文档测试: 逐个检查关键词；若没有这行代码，只能手写重复断言且不方便定位失败项
            with self.subTest(expected_term=expected_term):  # 新增代码+RealChrome文档测试: 给每个关键词单独显示失败上下文；若没有这行代码，失败时不容易知道缺了哪个词
                self.assertIn(expected_term, runtime_text)  # 新增代码+RealChrome文档测试: 断言运行规则包含该关键词；若没有这行代码，真实 Chrome 文档回归不会被自动发现
    def test_readme_explains_real_chrome_profile_mode(self) -> None:  # 新增代码+RealChrome文档测试: 验证 README 向初学者解释真实 Chrome profile 模式；若没有这行代码，用户文档漏写启用方式也不会报红
        readme_text = (TEST_ROOT / "README.md").read_text(encoding="utf-8")  # 新增代码+RealChrome文档测试: 读取用户实际会看的 README；若没有这行代码，测试无法覆盖交付说明
        expected_terms = ("browser_profiles.example.json", "browser_connect_real_chrome", "关闭当前 Chrome", "127.0.0.1", "默认不读取敏感数据", "learning_agent.py mcp-doctor")  # 新增代码+RealChrome文档测试: 集中列出 README 必须解释的入口和安全词；若没有这行代码，关键说明缺失不会被统一保护
        for expected_term in expected_terms:  # 新增代码+RealChrome文档测试: 遍历每个 README 关键词；若没有这行代码，新增关键词检查会变得重复且容易漏掉
            with self.subTest(expected_term=expected_term):  # 新增代码+RealChrome文档测试: 让失败信息指出具体缺失词；若没有这行代码，排查文档缺口会更慢
                self.assertIn(expected_term, readme_text)  # 新增代码+RealChrome文档测试: 断言 README 包含该说明；若没有这行代码，README 可读性和安全边界回归不会暴露
    def test_gap_matrix_mentions_real_chrome_login_state(self) -> None:  # 新增代码+RealChrome文档测试: 验证差距矩阵更新真实 Chrome 登录态状态；若没有这行代码，矩阵可能继续误写未实现
        matrix_text = (TEST_ROOT / "claude_code_tool_gap_matrix.md").read_text(encoding="utf-8")  # 新增代码+RealChrome文档测试: 读取 Claude Code 差距矩阵文档；若没有这行代码，测试无法检查能力状态说明
        expected_terms = ("真实 Chrome 登录态", "browser_connect_real_chrome", "confirm_real_profile")  # 新增代码+RealChrome文档测试: 列出矩阵必须点名的能力和确认参数；若没有这行代码，连接工具和确认门槛可能从文档里消失
        for expected_term in expected_terms:  # 新增代码+RealChrome文档测试: 逐项检查矩阵关键词；若没有这行代码，多个关键词无法统一覆盖
            with self.subTest(expected_term=expected_term):  # 新增代码+RealChrome文档测试: 给每个关键词独立失败上下文；若没有这行代码，定位缺失内容会不清楚
                self.assertIn(expected_term, matrix_text)  # 新增代码+RealChrome文档测试: 断言矩阵包含该关键词；若没有这行代码，差距矩阵回归不会被测试发现
    def test_gitignore_ignores_real_chrome_local_files(self) -> None:  # 新增代码+RealChrome文档测试: 验证真实 Chrome 本地配置和审计日志不会被提交；若没有这行代码，敏感本地文件可能缺少忽略保护
        project_root = PROJECT_ROOT  # 新增代码+RealChrome文档测试: 定位项目根目录；若没有这行代码，测试无法准确读取根目录 .gitignore
        gitignore_text = (project_root / ".gitignore").read_text(encoding="utf-8")  # 新增代码+RealChrome文档测试: 读取真实 .gitignore；若没有这行代码，忽略规则缺失不会被自动检查
        expected_terms = ("learning_agent/browser_profiles.json", "learning_agent/browser_artifacts/real_chrome_audit.jsonl")  # 新增代码+RealChrome文档测试: 列出必须忽略的本地文件路径；若没有这行代码，敏感 profile 配置和审计日志边界不会被统一保护
        for expected_term in expected_terms:  # 新增代码+RealChrome文档测试: 逐个检查忽略项；若没有这行代码，新增忽略规则缺失可能漏检
            with self.subTest(expected_term=expected_term):  # 新增代码+RealChrome文档测试: 让失败信息指出具体缺哪条忽略规则；若没有这行代码，排查 .gitignore 会更费劲
                self.assertIn(expected_term, gitignore_text)  # 新增代码+RealChrome文档测试: 断言 .gitignore 包含该路径；若没有这行代码，本地敏感文件可能被误提交
    def test_runtime_instructions_mentions_browser_automation_usage(self) -> None:  # 新增代码+BrowserAutomation文档: 验证运行规则写清浏览器自动化使用边界；若省略: 工具存在但模型可能不知道何时调用或避险
        runtime_text = self._dynamic_prompt_file().read_text(encoding="utf-8")  # 新增代码+BrowserAutomation文档: 读取真实 runtime_instructions.md；若省略: 测试无法覆盖模型实际会读到的运行规则
        self.assertIn("mcp__browser_automation__", runtime_text)  # 新增代码+BrowserAutomation文档: 断言运行规则提到真实浏览器自动化 MCP 工具前缀；若省略: 模型可能不知道要调用哪个工具族
        self.assertIn("mcp__browser_search__web_search", runtime_text)  # 新增代码+BrowserAutomation文档: 断言运行规则保留搜索优先场景；若省略: 模型可能把简单搜索也错误升级成打开浏览器
        self.assertIn("mcp__browser_search__fetch_url", runtime_text)  # 新增代码+BrowserAutomation文档: 断言运行规则保留普通 URL 正文读取工具；若省略: 模型可能为静态网页正文浪费真实浏览器
        self.assertIn("browser_evaluate", runtime_text)  # 新增代码+BrowserAutomation文档: 断言运行规则点名高风险 JS 工具；若省略: 执行脚本的风险边界可能被漏写
        self.assertIn("cookie", runtime_text)  # 新增代码+BrowserAutomation文档: 断言运行规则提醒不要主动读取 cookie；若省略: 脚本可能误碰登录隐私数据
        self.assertIn("localStorage", runtime_text)  # 新增代码+BrowserAutomation文档: 断言运行规则提醒不要主动读取 localStorage；若省略: token 等页面存储风险可能被忽略
        self.assertIn("sessionStorage", runtime_text)  # 新增代码+BrowserAutomation文档: 断言运行规则提醒不要主动读取 sessionStorage；若省略: 会话级敏感数据风险可能被忽略
        self.assertIn("browser_artifacts", runtime_text)  # 新增代码+BrowserAutomation文档: 断言运行规则说明截图下载等产物目录；若省略: 模型和用户可能不知道文件写到哪里
        self.assertIn("真实 Chrome", runtime_text)  # 修改代码+BrowserAutomation文档: 断言运行规则说明默认仍优先独立 Chromium，真实 Chrome 登录态只是第一版可选高风险模式且必须 confirm_real_profile=true；若省略: 用户可能误以为默认会连接真实 Chrome 或跳过显式确认


if __name__ == "__main__":  # Stage14: allow running this test module directly.
    unittest.main()  # Stage14: start unittest when executed as a script.


