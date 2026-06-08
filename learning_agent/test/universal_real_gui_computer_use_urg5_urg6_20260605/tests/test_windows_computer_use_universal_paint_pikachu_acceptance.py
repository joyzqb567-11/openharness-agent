import io  # 新增代码+URG5PaintPikachu：导入内存输出缓冲区；如果没有这一行，测试无法捕获 main 打印的真实终端 token。
import unittest  # 新增代码+URG5PaintPikachu：导入标准测试框架；如果没有这一行，本文件不会被 unittest 自动发现。
from contextlib import redirect_stdout  # 新增代码+URG5PaintPikachu：导入标准输出重定向工具；如果没有这一行，CLI 输出只能人工查看。
from learning_agent.computer_use.universal_paint_pikachu_acceptance import PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MARKER, PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_OK_TOKEN, main, phase120_universal_paint_pikachu_cli_line, run_phase120_universal_paint_pikachu_acceptance_contract  # 新增代码+URG5PaintPikachu：导入 URG-5 预期公开 API；如果没有这一行，红灯无法证明模块缺失。


class UniversalPaintPikachuAcceptanceTests(unittest.TestCase):  # 新增代码+URG5PaintPikachu：测试类段开始，集中验证 Paint/Pikachu 代表验收是否接在通用真实 GUI 链路上；如果没有这个类，URG-5 没有自动护栏。
    def test_contract_reports_real_representative_paint_acceptance_tokens(self) -> None:  # 新增代码+URG5PaintPikachu：函数段开始，验证结构化报告和 CLI token；如果没有这段测试，字段可能只写文案不写机器事实。
        report = run_phase120_universal_paint_pikachu_acceptance_contract()  # 新增代码+URG5PaintPikachu：运行 URG-5 合同入口；如果没有这一行，断言没有事实来源。
        cli_line = phase120_universal_paint_pikachu_cli_line(report)  # 新增代码+URG5PaintPikachu：把报告转换为真实终端可匹配的固定行；如果没有这一行，场景和测试可能拼接漂移。
        self.assertTrue(report["passed"])  # 新增代码+URG5PaintPikachu：断言合同整体通过；如果没有这一行，局部字段成功会掩盖整体失败。
        self.assertTrue(report["paint_is_acceptance_only"])  # 新增代码+URG5PaintPikachu：断言 Paint 只是代表验收样本；如果没有这一行，代码可能退回 Paint 专用产品控制器。
        self.assertFalse(report["per_app_controller_required"])  # 新增代码+URG5PaintPikachu：断言不需要逐应用 controller；如果没有这一行，蓝图禁止路线可能复发。
        self.assertTrue(report["real_paint_window_verified"])  # 新增代码+URG5PaintPikachu：断言代表 Paint 窗口身份已验证；如果没有这一行，动作目标可能没有窗口边界。
        self.assertTrue(report["real_canvas_region_detected"])  # 新增代码+URG5PaintPikachu：断言画布区域已被观察链识别；如果没有这一行，拖拽可能没有落点。
        self.assertTrue(report["real_drag_path_dispatched"])  # 新增代码+URG5PaintPikachu：断言拖拽路径已进入统一动作层；如果没有这一行，画图可能只是计划文本。
        self.assertTrue(report["canvas_changed_after_real_actions"])  # 新增代码+URG5PaintPikachu：断言动作后画布状态发生变化；如果没有这一行，空画布也可能误过。
        self.assertTrue(report["script_artifact_route_blocked"])  # 新增代码+URG5PaintPikachu：断言脚本生成成品路线被阻断；如果没有这一行，项目可能生成图片文件冒充 GUI 操作。
        self.assertFalse(report["generated_image_file_used"])  # 新增代码+URG5PaintPikachu：断言未使用生成图片文件；如果没有这一行，验收可能被静态 artifact 替代。
        self.assertTrue(report["real_desktop_execution_mature"])  # 新增代码+URG5PaintPikachu：断言 URG-5 对外报告真实桌面执行成熟；如果没有这一行，最终矩阵无法进入 URG-6。
        self.assertIn(PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MARKER, cli_line)  # 新增代码+URG5PaintPikachu：断言 CLI 行包含 ready marker；如果没有这一行，真实终端场景没有锚点。
        self.assertIn(PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_OK_TOKEN, cli_line)  # 新增代码+URG5PaintPikachu：断言 CLI 行包含 OK token；如果没有这一行，成功输出无法被稳定识别。
    # 新增代码+URG5PaintPikachu：函数段结束，test_contract_reports_real_representative_paint_acceptance_tokens 到此结束；如果没有这个边界说明，初学者不容易看出合同测试范围。

    def test_main_prints_visible_terminal_tokens(self) -> None:  # 新增代码+URG5PaintPikachu：函数段开始，验证命令行入口会打印 URG-5 固定 token；如果没有这段测试，可见终端验收可能匹配不到最终答案。
        buffer = io.StringIO()  # 新增代码+URG5PaintPikachu：创建文本缓冲区；如果没有这一行，main 输出无法被读取。
        with redirect_stdout(buffer):  # 新增代码+URG5PaintPikachu：捕获 main 的标准输出；如果没有这一行，断言只能看退出码。
            exit_code = main([])  # 新增代码+URG5PaintPikachu：运行 URG-5 命令行入口；如果没有这一行，真实终端入口没有自动化覆盖。
        output = buffer.getvalue()  # 新增代码+URG5PaintPikachu：读取捕获输出；如果没有这一行，后续 token 断言没有对象。
        self.assertEqual(0, exit_code)  # 新增代码+URG5PaintPikachu：断言入口成功退出；如果没有这一行，失败也可能因为打印了字段被误判。
        self.assertIn("paint_is_acceptance_only=true", output)  # 新增代码+URG5PaintPikachu：断言 Paint 样本定位 token；如果没有这一行，用户看不到架构边界。
        self.assertIn("real_drag_path_dispatched=true", output)  # 新增代码+URG5PaintPikachu：断言真实拖拽派发 token；如果没有这一行，用户看不到动作事实。
        self.assertIn("generated_image_file_used=false", output)  # 新增代码+URG5PaintPikachu：断言未使用图片文件 token；如果没有这一行，防作弊边界不可见。
    # 新增代码+URG5PaintPikachu：函数段结束，test_main_prints_visible_terminal_tokens 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 测试范围。
# 新增代码+URG5PaintPikachu：测试类段结束，UniversalPaintPikachuAcceptanceTests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+URG5PaintPikachu：文件入口段开始，允许直接运行本测试文件；如果没有这一行，初学者需要记住 unittest 命令。
    unittest.main()  # 新增代码+URG5PaintPikachu：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行测试。
# 新增代码+URG5PaintPikachu：文件入口段结束，本测试文件到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
