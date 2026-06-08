"""浏览器定位引擎测试，锁定 Stage 5 的元素候选选择能力。"""  # 新增代码+BrowserLocatorStage5: 说明本测试覆盖多策略定位；若没有这行代码，测试目的不清楚。

from learning_agent.tests.support import *  # 新增代码+BrowserLocatorStage5: 复用项目测试基础设施；若没有这行代码，unittest 和临时工具需要重复导入。

from learning_agent.browser.locator import BrowserLocatorEngine  # 新增代码+BrowserLocatorStage5: 导入待实现定位引擎；若没有这行代码，测试无法驱动 Stage 5 模块。
from learning_agent.browser.runtime_models import BrowserObservation  # 新增代码+BrowserLocatorStage5: 导入稳定 observation 模型；若没有这行代码，测试会用松散字典绕过协议。


class BrowserLocatorStage5Tests(unittest.TestCase):  # 新增代码+BrowserLocatorStage5: 定义 Stage 5 测试类；若没有这行代码，unittest 无法收集断言。
    def _sample_observation(self) -> BrowserObservation:  # 新增代码+BrowserLocatorStage5: 创建统一页面观察样本；若没有这行代码，每个测试会重复构造元素。
        return BrowserObservation(  # 新增代码+BrowserLocatorStage5: 返回协议化 observation；若没有这行代码，定位引擎无法收到真实模型对象。
            observation_id="obs-1",  # 新增代码+BrowserLocatorStage5: 设置观察 id；若没有这行代码，测试对象不完整。
            run_id="run-1",  # 新增代码+BrowserLocatorStage5: 设置 run id；若没有这行代码，测试对象不完整。
            stage_id="stage-1",  # 新增代码+BrowserLocatorStage5: 设置阶段 id；若没有这行代码，测试对象不完整。
            action_id="action-1",  # 新增代码+BrowserLocatorStage5: 设置动作 id；若没有这行代码，测试对象不完整。
            visible_text="账号 登录 查询天气",  # 新增代码+BrowserLocatorStage5: 设置页面文本；若没有这行代码，near_text 分支没有上下文。
            elements=[  # 新增代码+BrowserLocatorStage5: 提供候选元素列表；若没有这行代码，定位引擎无候选可选。
                {"element_id": "account", "role": "textbox", "label": "手机号", "placeholder": "请输入手机号", "text": "", "selector": "#phone", "center_x": 10, "center_y": 20, "box": {"x": 0, "y": 0, "width": 20, "height": 20}},  # 新增代码+BrowserLocatorStage5: 手机号输入框候选；若没有这行代码，label/placeholder 测试无法命中。
                {"element_id": "login", "role": "button", "label": "登录", "text": "登录", "selector": "button.login", "center_x": 50, "center_y": 60, "box": {"x": 40, "y": 50, "width": 20, "height": 20}},  # 新增代码+BrowserLocatorStage5: 登录按钮候选；若没有这行代码，role/text 测试无法命中。
            ],  # 新增代码+BrowserLocatorStage5: 结束候选元素列表；若没有这行代码，Python 调用语法无法闭合。
        )  # 新增代码+BrowserLocatorStage5: 结束 observation 构造；若没有这行代码，测试无法返回对象。

    def test_finds_best_candidate_by_placeholder_and_label(self) -> None:  # 新增代码+BrowserLocatorStage5: 验证表单输入定位；若没有这行代码，复杂登录表单容易失败。
        engine = BrowserLocatorEngine()  # 新增代码+BrowserLocatorStage5: 创建定位引擎；若没有这行代码，测试没有执行对象。
        candidates = engine.find_candidates(self._sample_observation(), {"placeholder": "请输入手机号"})  # 新增代码+BrowserLocatorStage5: 按 placeholder 搜索；若没有这行代码，输入框定位能力无法验证。
        self.assertEqual(candidates[0].element_id, "account")  # 新增代码+BrowserLocatorStage5: 验证命中手机号输入框；若没有这行代码，定位可能选错元素。
        self.assertGreaterEqual(candidates[0].confidence, 0.8)  # 新增代码+BrowserLocatorStage5: 验证高置信度；若没有这行代码，执行器无法区分可靠候选。
        self.assertIn("placeholder", candidates[0].reason)  # 新增代码+BrowserLocatorStage5: 验证原因可解释；若没有这行代码，用户看不懂为什么选它。

    def test_role_text_and_coordinates_are_supported(self) -> None:  # 新增代码+BrowserLocatorStage5: 验证按钮文本和坐标定位；若没有这行代码，拟人点击缺少基本能力。
        engine = BrowserLocatorEngine()  # 新增代码+BrowserLocatorStage5: 创建定位引擎；若没有这行代码，测试没有执行对象。
        candidates = engine.find_candidates(self._sample_observation(), {"role": "button", "text": "登录"})  # 新增代码+BrowserLocatorStage5: 按角色和文本搜索；若没有这行代码，按钮定位能力无法验证。
        self.assertEqual(candidates[0].selector, "button.login")  # 新增代码+BrowserLocatorStage5: 验证返回可执行 selector；若没有这行代码，动作执行器无法点击。
        coordinate = engine.find_candidates(self._sample_observation(), {"coordinate": {"x": 52, "y": 61}})[0]  # 新增代码+BrowserLocatorStage5: 按坐标搜索最近元素；若没有这行代码，视觉点击无法回到 DOM 候选。
        self.assertEqual(coordinate.element_id, "login")  # 新增代码+BrowserLocatorStage5: 验证坐标命中登录按钮；若没有这行代码，坐标定位可能错误。

    def test_low_confidence_returns_empty_when_threshold_not_met(self) -> None:  # 新增代码+BrowserLocatorStage5: 验证低置信度拦截；若没有这行代码，agent 可能凭猜测乱点。
        engine = BrowserLocatorEngine(min_confidence=0.7)  # 新增代码+BrowserLocatorStage5: 创建较高门槛引擎；若没有这行代码，阈值分支不会被覆盖。
        candidates = engine.find_candidates(self._sample_observation(), {"text": "不存在"})  # 新增代码+BrowserLocatorStage5: 搜索不存在文本；若没有这行代码，空结果分支无法验证。
        self.assertEqual(candidates, [])  # 新增代码+BrowserLocatorStage5: 验证没有可靠候选时返回空；若没有这行代码，误操作风险无法被测试锁定。
