"""浏览器验收断言引擎，复验 URL、页面文本、截图和秘密泄露。"""  # 新增代码+BrowserReplayStage10: 说明本模块负责浏览器真实验收；若没有这行代码，断言边界不清楚。

from __future__ import annotations  # 新增代码+BrowserReplayStage10: 延迟解析类型注解；若没有这行代码，类型引用更脆弱。

from pathlib import Path  # 新增代码+BrowserReplayStage10: 检查截图路径存在；若没有这行代码，截图断言无法执行。
from typing import Any  # 新增代码+BrowserReplayStage10: 断言和证据都是通用 JSON；若没有这行代码，类型边界不清楚。

from learning_agent.browser.runtime_models import BrowserAssertion, BrowserObservation  # 新增代码+BrowserReplayStage10: 复用浏览器协议模型；若没有这行代码，断言结果无法落盘。


class BrowserAssertionEngine:  # 新增代码+BrowserReplayStage10: 执行浏览器证据断言；若没有这个类，acceptance verifier 只能检查终端文本。
    def evaluate_many(self, assertions: list[dict[str, Any]], evidence: dict[str, Any]) -> dict[str, Any]:  # 新增代码+BrowserReplayStage10: 批量执行断言并汇总；若没有这行代码，场景验收无法一次检查多项。
        results = [self.evaluate(assertion, evidence).to_dict() for assertion in assertions]  # 新增代码+BrowserReplayStage10: 执行每一条断言；若没有这行代码，批量输入不会生效。
        completed = all(result.get("passed") is True for result in results)  # 新增代码+BrowserReplayStage10: 汇总是否全部通过；若没有这行代码，调用方需要重复判断。
        return {"completed": completed, "assertions": results}  # 新增代码+BrowserReplayStage10: 返回结构化报告；若没有这行代码，verifier 无法输出机器可读结果。

    def evaluate(self, assertion: dict[str, Any], evidence: dict[str, Any]) -> BrowserAssertion:  # 新增代码+BrowserReplayStage10: 执行单条浏览器断言；若没有这行代码，断言引擎没有主入口。
        assertion_type = str(assertion.get("type") or assertion.get("assertion_type") or "")  # 新增代码+BrowserReplayStage10: 读取断言类型；若没有这行代码，无法决定检查逻辑。
        expected = str(assertion.get("expected", ""))  # 新增代码+BrowserReplayStage10: 读取期望值；若没有这行代码，断言没有目标。
        observation = evidence.get("observation")  # 新增代码+BrowserReplayStage10: 读取页面观察证据；若没有这行代码，URL/文本/截图无法检查。
        if isinstance(observation, dict):  # 新增代码+BrowserReplayStage10: 兼容字典形式 observation；若没有这行代码，verifier 从 JSON 读取后无法使用。
            observation = BrowserObservation.from_dict(observation)  # 新增代码+BrowserReplayStage10: 转成协议对象；若没有这行代码，字段访问不稳定。
        if not isinstance(observation, BrowserObservation):  # 新增代码+BrowserReplayStage10: 缺 observation 时直接失败；若没有这行代码，后续属性访问会报错。
            return BrowserAssertion(assertion_type=assertion_type, expected=expected, passed=False, message="缺少 browser observation 证据。")  # 新增代码+BrowserReplayStage10: 返回清楚失败；若没有这行代码，调用方看不到原因。
        if assertion_type == "url_contains":  # 新增代码+BrowserReplayStage10: URL 包含断言；若没有这行代码，无法验收页面地址。
            return self._result(assertion_type, expected, observation.url, expected in observation.url)  # 新增代码+BrowserReplayStage10: 检查 URL；若没有这行代码，目标页面可能不正确仍通过。
        if assertion_type == "title_contains":  # 新增代码+BrowserReplayStage10: 标题包含断言；若没有这行代码，无法验收页面标题。
            return self._result(assertion_type, expected, observation.title, expected in observation.title)  # 新增代码+BrowserReplayStage10: 检查标题；若没有这行代码，页面身份缺少验证。
        if assertion_type == "visible_text_contains":  # 新增代码+BrowserReplayStage10: 可见文本包含断言；若没有这行代码，无法验收页面内容。
            return self._result(assertion_type, expected, observation.visible_text, expected in observation.visible_text)  # 新增代码+BrowserReplayStage10: 检查可见文本；若没有这行代码，页面内容可能错误仍通过。
        if assertion_type == "screenshot_exists":  # 新增代码+BrowserReplayStage10: 截图存在断言；若没有这行代码，肉眼证据文件无法验收。
            exists = bool(observation.screenshot_path) and Path(observation.screenshot_path).exists()  # 新增代码+BrowserReplayStage10: 检查截图路径存在；若没有这行代码，坏截图路径可能通过。
            return self._result(assertion_type, expected, observation.screenshot_path, exists, artifact_path=observation.screenshot_path)  # 新增代码+BrowserReplayStage10: 返回截图断言结果；若没有这行代码，报告缺少证据路径。
        if assertion_type == "secret_not_leaked":  # 新增代码+BrowserReplayStage10: 秘密不泄露断言；若没有这行代码，验收无法确认输出安全。
            leaked = expected and expected in "\n".join([observation.visible_text, observation.console_summary, observation.network_summary])  # 新增代码+BrowserReplayStage10: 检查观察文本是否含秘密；若没有这行代码，密码泄露无法发现。
            return self._result(assertion_type, expected, "leaked" if leaked else "not_leaked", not leaked)  # 新增代码+BrowserReplayStage10: 返回秘密泄露结果；若没有这行代码，安全门禁无法执行。
        if assertion_type == "console_no_severe_error":  # 新增代码+BrowserReplayStage10: console 严重错误断言；若没有这行代码，页面 JS 崩溃可能被忽略。
            lowered = observation.console_summary.lower()  # 新增代码+BrowserReplayStage10: 小写 console 摘要；若没有这行代码，大小写会影响判断。
            passed = "error" not in lowered and "uncaught" not in lowered  # 新增代码+BrowserReplayStage10: 检查常见严重错误；若没有这行代码，脚本异常可能通过验收。
            return self._result(assertion_type, expected, observation.console_summary, passed)  # 新增代码+BrowserReplayStage10: 返回 console 断言结果；若没有这行代码，调用方拿不到结果。
        return BrowserAssertion(assertion_type=assertion_type, expected=expected, actual="", passed=False, message=f"未知浏览器断言类型：{assertion_type}")  # 新增代码+BrowserReplayStage10: 未知断言直接失败；若没有这行代码，拼错断言可能误通过。

    def _result(self, assertion_type: str, expected: str, actual: str, passed: bool, artifact_path: str = "") -> BrowserAssertion:  # 新增代码+BrowserReplayStage10: 构造标准断言结果；若没有这行代码，每个分支会重复对象创建。
        message = "通过" if passed else f"期望包含 {expected!r}，实际为 {actual!r}"  # 新增代码+BrowserReplayStage10: 生成可读说明；若没有这行代码，失败后用户看不懂差异。
        return BrowserAssertion(assertion_type=assertion_type, expected=expected, actual=str(actual), passed=bool(passed), message=message, artifact_path=artifact_path)  # 新增代码+BrowserReplayStage10: 返回协议化断言；若没有这行代码，结果无法落盘。
