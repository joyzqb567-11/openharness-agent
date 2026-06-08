"""浏览器运行时协议模型测试。"""  # 新增代码+BrowserRuntimeProtocol: 说明本文件锁定浏览器 run/action/observation 等稳定数据协议；若没有这行代码，维护者不知道这些测试服务于真实浏览器 runtime 对齐。

from __future__ import annotations  # 新增代码+BrowserRuntimeProtocol: 延迟解析类型注解；若没有这行代码，后续模型类型引用在旧解释顺序下更脆弱。

from learning_agent.tests.support import *  # 新增代码+BrowserRuntimeProtocol: 复用项目测试根目录、临时目录和 unittest 基类；若没有这行代码，测试会重复大量公共准备逻辑。


class BrowserRuntimeModelTests(LearningAgentTestBase):  # 新增代码+BrowserRuntimeProtocol: 定义浏览器运行时协议测试集合；若没有这个类，unittest 不会发现本组协议回归测试。
    def test_browser_action_redacts_sensitive_arguments_and_round_trips(self) -> None:  # 新增代码+BrowserRuntimeProtocol: 验证动作模型会脱敏并能 JSON 往返；若没有这行代码，密码可能进入 action log 且恢复失败。
        from learning_agent.browser.runtime_models import BrowserAction, redact_browser_arguments, stable_json_dumps  # 新增代码+BrowserRuntimeProtocol: 导入计划新增的动作模型和脱敏 helper；若没有这行代码，测试无法锁定公开 API。
        raw_arguments = {"selector": "#password", "text": "secret123", "secret_env_var": "LEARNING_AGENT_TEST_PASSWORD", "nested": {"token": "abc123", "normal": "ok"}, "url": "https://example.com/login"}  # 新增代码+BrowserRuntimeProtocol: 构造同时包含普通参数和敏感参数的动作入参；若没有这行代码，脱敏边界没有真实输入。
        generic_redacted = redact_browser_arguments(raw_arguments)  # 新增代码+BrowserRuntimeProtocol: 先验证通用递归脱敏 helper；若没有这行代码，嵌套 token 泄露不会被发现。
        action = BrowserAction.create(run_id="browser-run-1", stage_id="login", tool_name="browser_type_secret", arguments=raw_arguments)  # 新增代码+BrowserRuntimeProtocol: 通过工厂创建 secret 输入动作；若没有这行代码，工具级脱敏策略无法被覆盖。
        action.mark_started()  # 新增代码+BrowserRuntimeProtocol: 标记动作开始；若没有这行代码，started_at_ms 字段不会被填充。
        action.mark_completed(observation_id="obs-1")  # 新增代码+BrowserRuntimeProtocol: 标记动作完成并关联观察结果；若没有这行代码，工具结果无法回挂页面证据。
        payload = action.to_dict()  # 新增代码+BrowserRuntimeProtocol: 把动作转成可落盘字典；若没有这行代码，无法验证 JSON 持久化格式。
        restored = BrowserAction.from_dict(payload)  # 新增代码+BrowserRuntimeProtocol: 从字典恢复动作对象；若没有这行代码，进程重启恢复无法被测试。
        dumped = stable_json_dumps(payload)  # 新增代码+BrowserRuntimeProtocol: 生成稳定 JSON 文本用于检查秘密没有落盘；若没有这行代码，序列化泄露不会被发现。
        self.assertEqual(generic_redacted["nested"]["token"], "[已脱敏]")  # 新增代码+BrowserRuntimeProtocol: 断言嵌套 token 被脱敏；若没有这行代码，递归脱敏失效不会报红。
        self.assertEqual(generic_redacted["url"], "https://example.com/login")  # 新增代码+BrowserRuntimeProtocol: 断言普通 URL 不被误删；若没有这行代码，审计日志会失去必要页面线索。
        self.assertEqual(payload["arguments_redacted"]["text"], "[已脱敏]")  # 新增代码+BrowserRuntimeProtocol: 断言 secret 工具的 text 被脱敏；若没有这行代码，真实密码可能进入模型上下文。
        self.assertEqual(payload["status"], "completed")  # 新增代码+BrowserRuntimeProtocol: 断言动作完成状态稳定落盘；若没有这行代码，恢复时无法知道动作是否已完成。
        self.assertEqual(restored.action_id, action.action_id)  # 新增代码+BrowserRuntimeProtocol: 断言动作 id 往返不变；若没有这行代码，事件和动作文件会断开关联。
        self.assertNotIn("secret123", dumped)  # 新增代码+BrowserRuntimeProtocol: 断言序列化文本不含明文密码；若没有这行代码，落盘证据可能泄露秘密。
        self.assertNotIn("abc123", dumped)  # 新增代码+BrowserRuntimeProtocol: 断言序列化文本不含明文 token；若没有这行代码，嵌套秘密可能泄露。

    def test_browser_observation_records_page_evidence_and_round_trips(self) -> None:  # 新增代码+BrowserRuntimeProtocol: 验证页面观察结果能保存 URL、标题、截图和元素候选；若没有这行代码，agent 看见页面的证据无法恢复。
        from learning_agent.browser.runtime_models import BrowserObservation  # 新增代码+BrowserRuntimeProtocol: 导入计划新增的 observation 模型；若没有这行代码，测试无法锁定页面证据协议。
        observation = BrowserObservation(observation_id="obs-1", run_id="browser-run-1", stage_id="read-page", action_id="action-1", url="https://example.com/", title="Example Domain", visible_text="Example Domain visible text", screenshot_path="artifacts/example.png", console_summary="0 severe console errors", network_summary="1 document request", elements=[{"element_id": "e1", "role": "heading", "label": "Example Domain", "selector": "h1", "box": {"x": 10, "y": 20, "width": 200, "height": 40}}])  # 新增代码+BrowserRuntimeProtocol: 构造完整页面观察对象；若没有这行代码，字段覆盖会太弱。
        payload = observation.to_dict()  # 新增代码+BrowserRuntimeProtocol: 把观察结果转成可保存字典；若没有这行代码，store 无法落盘 observation。
        restored = BrowserObservation.from_dict(payload)  # 新增代码+BrowserRuntimeProtocol: 从字典恢复观察对象；若没有这行代码，resume 无法读取页面证据。
        self.assertEqual(payload["url"], "https://example.com/")  # 新增代码+BrowserRuntimeProtocol: 断言 URL 被保存；若没有这行代码，验收无法证明打开了哪个页面。
        self.assertEqual(payload["elements"][0]["box"]["width"], 200)  # 新增代码+BrowserRuntimeProtocol: 断言元素几何框被保存；若没有这行代码，视觉定位和回放缺少坐标依据。
        self.assertEqual(restored.title, "Example Domain")  # 新增代码+BrowserRuntimeProtocol: 断言标题往返不变；若没有这行代码，页面观察恢复可能丢字段。
        self.assertEqual(restored.elements[0]["selector"], "h1")  # 新增代码+BrowserRuntimeProtocol: 断言元素 selector 往返不变；若没有这行代码，定位候选恢复可能失效。

    def test_browser_run_tracks_stage_action_observation_and_terminal_status(self) -> None:  # 新增代码+BrowserRuntimeProtocol: 验证浏览器 run 能追踪阶段、动作、观察和最终状态；若没有这行代码，长任务浏览器状态无法汇总。
        from learning_agent.browser.runtime_models import BrowserRun  # 新增代码+BrowserRuntimeProtocol: 导入计划新增的 browser run 模型；若没有这行代码，测试无法覆盖 run 根对象。
        browser_run = BrowserRun(run_id="browser-run-1", session_id="session-1", prompt="查天气并做攻略")  # 新增代码+BrowserRuntimeProtocol: 创建一个真实浏览器任务 run；若没有这行代码，后续状态变化没有对象。
        browser_run.mark_running(stage_id="open-page")  # 新增代码+BrowserRuntimeProtocol: 标记 run 进入第一个阶段；若没有这行代码，状态页不知道当前跑到哪一步。
        browser_run.add_action("action-1")  # 新增代码+BrowserRuntimeProtocol: 记录动作 id；若没有这行代码，run 和 action 文件无法关联。
        browser_run.add_observation("obs-1")  # 新增代码+BrowserRuntimeProtocol: 记录 observation id；若没有这行代码，run 和页面证据无法关联。
        browser_run.mark_stage_completed("open-page")  # 新增代码+BrowserRuntimeProtocol: 标记阶段完成；若没有这行代码，中断恢复可能重复执行已完成阶段。
        browser_run.mark_completed(summary="页面内容已读取")  # 新增代码+BrowserRuntimeProtocol: 标记 run 完成并保存摘要；若没有这行代码，状态 CLI 无法显示任务结果。
        payload = browser_run.to_dict()  # 新增代码+BrowserRuntimeProtocol: 把 run 转成可落盘字典；若没有这行代码，store 无法持久化 run。
        restored = BrowserRun.from_dict(payload)  # 新增代码+BrowserRuntimeProtocol: 从字典恢复 run；若没有这行代码，进程中断后无法恢复状态。
        self.assertEqual(payload["status"], "completed")  # 新增代码+BrowserRuntimeProtocol: 断言 run 状态完成；若没有这行代码，状态机错误不会被发现。
        self.assertEqual(payload["completed_stage_ids"], ["open-page"])  # 新增代码+BrowserRuntimeProtocol: 断言完成阶段落盘；若没有这行代码，resume 无法跳过已完成阶段。
        self.assertEqual(restored.action_ids, ["action-1"])  # 新增代码+BrowserRuntimeProtocol: 断言 action id 往返不变；若没有这行代码，事件回放会断链。
        self.assertEqual(restored.observation_ids, ["obs-1"])  # 新增代码+BrowserRuntimeProtocol: 断言 observation id 往返不变；若没有这行代码，验收证据会断链。
