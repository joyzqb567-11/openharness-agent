"""浏览器观察引擎测试，锁定 Stage 4 的页面证据能力。"""  # 新增代码+BrowserObservationStage4: 说明本测试覆盖页面观察产物；若没有这行代码，测试目的不清楚。

from learning_agent.tests.support import *  # 新增代码+BrowserObservationStage4: 复用项目测试基础设施；若没有这行代码，临时目录和断言工具需要重复导入。

from learning_agent.browser.observation import build_browser_observation, redact_sensitive_text  # 新增代码+BrowserObservationStage4: 导入待实现观察构建器和脱敏函数；若没有这行代码，测试无法驱动 Stage 4 模块。
from learning_agent.browser.screenshot_index import BrowserScreenshotIndex  # 新增代码+BrowserObservationStage4: 导入截图索引用于验证截图能关联 run/action；若没有这行代码，截图证据会继续是孤立文件。


class BrowserObservationStage4Tests(unittest.TestCase):  # 新增代码+BrowserObservationStage4: 定义 Stage 4 单元测试类；若没有这行代码，unittest 无法收集这些断言。
    def test_observation_clips_long_text_and_writes_artifact(self) -> None:  # 新增代码+BrowserObservationStage4: 验证长页面文本会落盘成产物；若没有这行代码，大页面只能靠截断文本验收。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+BrowserObservationStage4: 使用临时目录隔离观察产物；若没有这行代码，测试会污染项目目录。
            artifact_dir = Path(temp_dir) / "artifacts"  # 新增代码+BrowserObservationStage4: 准备产物目录路径；若没有这行代码，构建器不知道长文本写到哪里。
            page_state = {  # 新增代码+BrowserObservationStage4: 构造模拟页面状态；若没有这行代码，观察构建器没有输入。
                "url": "https://example.test/weather",  # 新增代码+BrowserObservationStage4: 提供 URL 证据；若没有这行代码，observation 不能证明页面来源。
                "title": "天气页面",  # 新增代码+BrowserObservationStage4: 提供标题证据；若没有这行代码，状态摘要不完整。
                "visible_text": "武汉天气" + (" 很长" * 100),  # 新增代码+BrowserObservationStage4: 构造超长文本触发产物写入；若没有这行代码，长文本分支不会被覆盖。
                "screenshot_path": str(artifact_dir / "shot.png"),  # 新增代码+BrowserObservationStage4: 提供截图路径；若没有这行代码，截图关联能力无法验证。
                "console": [{"type": "log", "text": "Authorization: Bearer secret-token"}],  # 新增代码+BrowserObservationStage4: 提供含 token 的 console；若没有这行代码，console 脱敏缺少测试。
                "network": [{"method": "GET", "url": "https://example.test/?cookie=secret"}],  # 新增代码+BrowserObservationStage4: 提供含 cookie 的网络 URL；若没有这行代码，network 脱敏缺少测试。
                "elements": [{"id": 7, "tag": "button", "label": "提交", "selector": "button.submit", "x": 10, "y": 20, "width": 80, "height": 30}],  # 新增代码+BrowserObservationStage4: 提供元素几何信息；若没有这行代码，结构化元素分支不会被验证。
            }  # 新增代码+BrowserObservationStage4: 结束页面状态输入；若没有这行代码，Python 字典语法无法闭合。
            observation = build_browser_observation("run-1", "stage-1", "action-1", page_state, max_text_chars=12, artifact_dir=artifact_dir)  # 新增代码+BrowserObservationStage4: 构建真实 observation；若没有这行代码，测试只是在检查假对象。
            self.assertEqual(observation.run_id, "run-1")  # 新增代码+BrowserObservationStage4: 验证 run 关联；若没有这行代码，证据可能无法回到任务。
            self.assertLessEqual(len(observation.visible_text), 12)  # 新增代码+BrowserObservationStage4: 验证上下文文本被限制；若没有这行代码，工具结果仍可能撑爆模型上下文。
            self.assertEqual(len(observation.artifact_paths), 1)  # 新增代码+BrowserObservationStage4: 验证超长正文写入产物；若没有这行代码，长页面内容会丢失。
            self.assertTrue(Path(observation.artifact_paths[0]).exists())  # 新增代码+BrowserObservationStage4: 验证产物真实存在；若没有这行代码，路径可能只是空记录。
            self.assertIn("武汉天气", Path(observation.artifact_paths[0]).read_text(encoding="utf-8"))  # 新增代码+BrowserObservationStage4: 验证产物保留完整正文；若没有这行代码，长文本可能被错误截断后落盘。
            self.assertIn("[已脱敏]", observation.console_summary)  # 新增代码+BrowserObservationStage4: 验证 console 敏感信息被脱敏；若没有这行代码，token 可能泄露进日志。
            self.assertIn("[已脱敏]", observation.network_summary)  # 新增代码+BrowserObservationStage4: 验证 network 敏感信息被脱敏；若没有这行代码，cookie 可能泄露进日志。
            self.assertEqual(observation.elements[0]["element_id"], "7")  # 新增代码+BrowserObservationStage4: 验证元素 id 被规范化；若没有这行代码，locator 无法稳定引用元素。
            self.assertEqual(observation.elements[0]["center_x"], 50)  # 新增代码+BrowserObservationStage4: 验证中心点被计算；若没有这行代码，坐标点击缺少目标。

    def test_screenshot_index_links_image_to_runtime_action(self) -> None:  # 新增代码+BrowserObservationStage4: 验证截图索引保存动作关系；若没有这行代码，肉眼截图无法关联具体步骤。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+BrowserObservationStage4: 使用临时目录隔离截图索引；若没有这行代码，测试会污染真实索引。
            index = BrowserScreenshotIndex(Path(temp_dir) / "screenshots.jsonl")  # 新增代码+BrowserObservationStage4: 创建截图索引对象；若没有这行代码，无法写入截图关联记录。
            screenshot_path = Path(temp_dir) / "shot.png"  # 新增代码+BrowserObservationStage4: 准备截图路径；若没有这行代码，索引记录没有目标。
            screenshot_path.write_bytes(b"png")  # 新增代码+BrowserObservationStage4: 写一个最小占位文件；若没有这行代码，exists 检查无法证明路径有效。
            index.record("run-1", "stage-1", "action-1", screenshot_path)  # 新增代码+BrowserObservationStage4: 记录截图和运行关系；若没有这行代码，tail 查询没有数据。
            latest = index.tail(limit=1)[0]  # 新增代码+BrowserObservationStage4: 读取最近一条索引；若没有这行代码，测试无法检查落盘内容。
            self.assertEqual(latest["run_id"], "run-1")  # 新增代码+BrowserObservationStage4: 验证 run id 被保存；若没有这行代码，截图无法归属任务。
            self.assertEqual(latest["action_id"], "action-1")  # 新增代码+BrowserObservationStage4: 验证 action id 被保存；若没有这行代码，截图无法定位具体工具动作。
            self.assertTrue(latest["exists"])  # 新增代码+BrowserObservationStage4: 验证索引记录文件存在性；若没有这行代码，坏截图路径可能通过。

    def test_sensitive_text_redaction_handles_common_browser_leaks(self) -> None:  # 新增代码+BrowserObservationStage4: 验证浏览器常见泄露文本会被脱敏；若没有这行代码，日志脱敏规则容易回退。
        text = "cookie=session123 Authorization: Bearer token123 password=abc localStorage secret"  # 新增代码+BrowserObservationStage4: 构造多种敏感片段；若没有这行代码，脱敏函数缺少输入。
        redacted = redact_sensitive_text(text)  # 新增代码+BrowserObservationStage4: 执行脱敏；若没有这行代码，断言没有实际对象。
        self.assertNotIn("token123", redacted)  # 新增代码+BrowserObservationStage4: 验证 Bearer token 不泄露；若没有这行代码，授权头可能进日志。
        self.assertNotIn("abc", redacted)  # 新增代码+BrowserObservationStage4: 验证 password 值不泄露；若没有这行代码，密码可能进日志。
        self.assertIn("[已脱敏]", redacted)  # 新增代码+BrowserObservationStage4: 验证使用统一占位符；若没有这行代码，审计难以机器判断脱敏发生。
