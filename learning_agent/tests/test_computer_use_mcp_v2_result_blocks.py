from __future__ import annotations  # 新增代码+ClaudeCodeContentParityTests：延迟类型注解解析；如果没有这行代码，测试导入时类型注解可能提前求值。
import base64  # 新增代码+ClaudeCodeContentParityTests：用于生成测试 PNG 字节；如果没有这行代码，测试无法创建真实图片 artifact。
import json  # 新增代码+ClaudeCodeContentParityTests：用于验证旧 JSON 文本回退；如果没有这行代码，无法证明兼容输出仍可解析。
import tempfile  # 新增代码+ClaudeCodeContentParityTests：用于创建临时截图文件；如果没有这行代码，测试会污染项目目录。
import unittest  # 新增代码+ClaudeCodeContentParityTests：使用标准 unittest 框架；如果没有这行代码，测试类不会被发现和执行。
from pathlib import Path  # 新增代码+ClaudeCodeContentParityTests：稳定处理临时图片路径；如果没有这行代码，Windows 路径拼接容易出错。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.result_blocks import image_content_block, mcp_content_from_result, success_result, text_content_block  # 新增代码+ClaudeCodeContentParityTests：导入结果包装函数；如果没有这行代码，无法验证 content block 协议形状。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import ComputerUseMcpV2Context, dispatch_computer_use_mcp_v2_tool  # 新增代码+ClaudeCodeContentParityTests：导入真实 runtime 分发入口；如果没有这行代码，观察链路测试无法覆盖实际调用。
from learning_agent.computer_use_mcp_v2.windows_runtime.image_messages import extract_computer_use_image_specs_from_tool_output  # 新增代码+ClaudeCodeContentParityTests：导入图片引用解析器；如果没有这行代码，debug.artifact_path 回灌无法自动验证。

SAMPLE_PNG_BYTES = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=")  # 新增代码+ClaudeCodeContentParityTests：准备一张 1x1 PNG；如果没有这行代码，测试没有可读取的真实图片。


class FakeObservationHost:  # 新增代码+ClaudeCodeContentParityTests：类段开始，伪造 Windows host 的观察返回；如果没有这段类，测试必须依赖真实桌面截图。
    def __init__(self, artifact_path: str) -> None:  # 新增代码+ClaudeCodeContentParityTests：函数段开始，保存测试截图路径；如果没有这段函数，fake host 不知道返回哪张图片。
        self.artifact_path = artifact_path  # 新增代码+ClaudeCodeContentParityTests：记录 artifact_path；如果没有这行代码，observe 返回会缺少图片路径。
    # 新增代码+ClaudeCodeContentParityTests：函数段结束，__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake host 初始化范围。

    def observe(self, _arguments: dict[str, object]) -> dict[str, object]:  # 新增代码+ClaudeCodeContentParityTests：函数段开始，模拟 host.observe；如果没有这段函数，screenshot 分发无法获得图片 payload。
        return {"captured": True, "image_results": [{"artifact_path": self.artifact_path, "mime_type": "image/png"}]}  # 新增代码+ClaudeCodeContentParityTests：返回结构化图片结果；如果没有这行代码，观察层无法生成 image content block。
    # 新增代码+ClaudeCodeContentParityTests：函数段结束，observe 到此结束；如果没有这个边界说明，用户不容易看出 fake 观察范围。
# 新增代码+ClaudeCodeContentParityTests：类段结束，FakeObservationHost 到此结束；如果没有这个边界说明，用户不容易看出测试替身范围。


class ComputerUseMcpV2ResultBlockTests(unittest.TestCase):  # 新增代码+ClaudeCodeContentParityTests：类段开始，验证 ClaudeCode-compatible 结果块；如果没有这段类，content parity 没有自动化保护。
    def test_text_and_image_content_block_shapes_match_claudecode_style(self) -> None:  # 新增代码+ClaudeCodeContentParityTests：函数段开始，验证基础 content block 结构；如果没有这段测试，helper 输出可能偏离协议。
        self.assertEqual({"type": "text", "text": "hello"}, text_content_block("hello"))  # 新增代码+ClaudeCodeContentParityTests：断言文本块字段；如果没有这行代码，text content 形状错误不会失败。
        image_block = image_content_block("abc", "image/png")  # 新增代码+ClaudeCodeContentParityTests：构造图片块；如果没有这行代码，图片 content 形状没有测试对象。
        self.assertEqual("image", image_block["type"])  # 新增代码+ClaudeCodeContentParityTests：断言图片块类型；如果没有这行代码，type 字段错误不会失败。
        self.assertEqual("base64", image_block["source"]["type"])  # 新增代码+ClaudeCodeContentParityTests：断言图片 source 类型；如果没有这行代码，ClaudeCode base64 约定可能被破坏。
        self.assertEqual("image/png", image_block["source"]["media_type"])  # 新增代码+ClaudeCodeContentParityTests：断言 MIME 字段；如果没有这行代码，模型可能按错格式解码。
        self.assertEqual("abc", image_block["source"]["data"])  # 新增代码+ClaudeCodeContentParityTests：断言 base64 数据字段；如果没有这行代码，图片数据可能被丢弃。
    # 新增代码+ClaudeCodeContentParityTests：函数段结束，test_text_and_image_content_block_shapes_match_claudecode_style 到此结束；如果没有这个边界说明，用户不容易看出 helper 形状测试范围。

    def test_mcp_content_keeps_json_fallback_without_explicit_content(self) -> None:  # 新增代码+ClaudeCodeContentParityTests：函数段开始，验证旧 JSON 文本兼容；如果没有这段测试，非截图工具可能被新 content 逻辑破坏。
        result = success_result("wait", {"waited_seconds": 0})  # 新增代码+ClaudeCodeContentParityTests：构造没有显式 content 的普通成功结果；如果没有这行代码，回退路径没有输入。
        mcp_result = mcp_content_from_result(result)  # 新增代码+ClaudeCodeContentParityTests：转换为 MCP 工具返回；如果没有这行代码，无法验证 stdio 输出。
        parsed_text = json.loads(mcp_result["content"][0]["text"])  # 新增代码+ClaudeCodeContentParityTests：解析回退 JSON 文本；如果没有这行代码，旧调用方可读性无法验证。
        self.assertEqual("wait", parsed_text["tool_name"])  # 新增代码+ClaudeCodeContentParityTests：断言旧 tool_name 仍保留；如果没有这行代码，历史审计字段丢失不会失败。
        self.assertEqual({"waited_seconds": 0}, parsed_text["payload"])  # 新增代码+ClaudeCodeContentParityTests：断言旧 payload 仍保留；如果没有这行代码，兼容输出丢数据不会失败。
    # 新增代码+ClaudeCodeContentParityTests：函数段结束，test_mcp_content_keeps_json_fallback_without_explicit_content 到此结束；如果没有这个边界说明，用户不容易看出 JSON 回退测试范围。

    def test_mcp_content_returns_explicit_content_blocks_when_present(self) -> None:  # 新增代码+ClaudeCodeContentParityTests：函数段开始，验证显式 content 优先；如果没有这段测试，图片块可能被重新包成 JSON 文本。
        content = [text_content_block("captured")]  # 新增代码+ClaudeCodeContentParityTests：准备显式 content；如果没有这行代码，优先路径没有输入。
        result = success_result("screenshot", {"captured": True}, content=content, debug={"artifact_path": "screen.png"})  # 新增代码+ClaudeCodeContentParityTests：构造带 content/debug 的成功结果；如果没有这行代码，MCP 新协议路径没有测试对象。
        mcp_result = mcp_content_from_result(result)  # 新增代码+ClaudeCodeContentParityTests：转换为 MCP 工具返回；如果没有这行代码，无法验证 content 是否直出。
        self.assertEqual(content, mcp_result["content"])  # 新增代码+ClaudeCodeContentParityTests：断言显式 content 原样返回；如果没有这行代码，MCP 层吞图片块不会失败。
    # 新增代码+ClaudeCodeContentParityTests：函数段结束，test_mcp_content_returns_explicit_content_blocks_when_present 到此结束；如果没有这个边界说明，用户不容易看出显式 content 测试范围。

    def test_screenshot_result_adds_text_image_blocks_and_debug_artifact(self) -> None:  # 新增代码+ClaudeCodeContentParityTests：函数段开始，验证真实 runtime 观察结果生成 text/image/debug；如果没有这段测试，观察链路可能只测 helper 不测分发。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+ClaudeCodeContentParityTests：创建临时目录保存测试截图；如果没有这行代码，测试文件会残留在仓库。
            artifact_path = Path(temp_dir) / "screen.png"  # 新增代码+ClaudeCodeContentParityTests：生成临时截图路径；如果没有这行代码，fake host 无法指向图片。
            artifact_path.write_bytes(SAMPLE_PNG_BYTES)  # 新增代码+ClaudeCodeContentParityTests：写入真实 PNG 文件；如果没有这行代码，观察层读图会失败。
            context = ComputerUseMcpV2Context(host=FakeObservationHost(str(artifact_path)))  # 新增代码+ClaudeCodeContentParityTests：把 fake host 注入 runtime；如果没有这行代码，screenshot 会走无 host 路径。
            result = dispatch_computer_use_mcp_v2_tool("screenshot", {}, context)  # 新增代码+ClaudeCodeContentParityTests：通过真实分发执行 screenshot；如果没有这行代码，observe 集成路径没有覆盖。
        self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodeContentParityTests：断言截图结果成功；如果没有这行代码，失败结果可能继续做字段断言。
        self.assertEqual("text", result["content"][0]["type"])  # 新增代码+ClaudeCodeContentParityTests：断言第一块是文本说明；如果没有这行代码，content 语义连接丢失不会失败。
        image_blocks = [block for block in result["content"] if block.get("type") == "image"]  # 新增代码+ClaudeCodeContentParityTests：筛选图片块；如果没有这行代码，后续断言无法定位图片。
        self.assertEqual(1, len(image_blocks))  # 新增代码+ClaudeCodeContentParityTests：断言正好有一张图片；如果没有这行代码，漏图或重复图不会失败。
        self.assertEqual("base64", image_blocks[0]["source"]["type"])  # 新增代码+ClaudeCodeContentParityTests：断言图片使用 base64 source；如果没有这行代码，ClaudeCode 图片协议可能偏离。
        self.assertEqual("image/png", image_blocks[0]["source"]["media_type"])  # 新增代码+ClaudeCodeContentParityTests：断言图片 MIME；如果没有这行代码，转码或 MIME 推断错误不会失败。
        self.assertTrue(image_blocks[0]["source"]["data"])  # 新增代码+ClaudeCodeContentParityTests：断言图片数据非空；如果没有这行代码，空图片块不会失败。
        self.assertEqual(1, result["debug"]["image_count"])  # 新增代码+ClaudeCodeContentParityTests：断言 debug 记录图片数量；如果没有这行代码，调试证据缺失不会失败。
    # 新增代码+ClaudeCodeContentParityTests：函数段结束，test_screenshot_result_adds_text_image_blocks_and_debug_artifact 到此结束；如果没有这个边界说明，用户不容易看出观察集成测试范围。

    def test_image_message_parser_reads_new_debug_artifact_path(self) -> None:  # 新增代码+ClaudeCodeContentParityTests：函数段开始，验证旧图片回灌能识别新 debug 字段；如果没有这段测试，JSON 文本链路可能看不到新截图证据。
        output = json.dumps({"debug": {"artifact_path": "C:/tmp/screen.png", "mime_type": "image/png"}})  # 新增代码+ClaudeCodeContentParityTests：构造带 debug.artifact_path 的工具文本；如果没有这行代码，解析器没有新协议输入。
        specs = extract_computer_use_image_specs_from_tool_output(output)  # 新增代码+ClaudeCodeContentParityTests：解析图片引用；如果没有这行代码，无法验证 debug 回灌。
        self.assertEqual([{"artifact_path": "C:/tmp/screen.png", "mime_type": "image/png"}], specs)  # 新增代码+ClaudeCodeContentParityTests：断言解析结果；如果没有这行代码，新 debug 字段解析错误不会失败。
    # 新增代码+ClaudeCodeContentParityTests：函数段结束，test_image_message_parser_reads_new_debug_artifact_path 到此结束；如果没有这个边界说明，用户不容易看出 debug 解析测试范围。
# 新增代码+ClaudeCodeContentParityTests：类段结束，ComputerUseMcpV2ResultBlockTests 到此结束；如果没有这个边界说明，用户不容易看出结果块测试范围。


if __name__ == "__main__":  # 新增代码+ClaudeCodeContentParityTests：允许直接运行本测试文件；如果没有这行代码，手动调试不方便。
    unittest.main()  # 新增代码+ClaudeCodeContentParityTests：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
