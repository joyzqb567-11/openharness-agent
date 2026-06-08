import importlib  # 新增代码+Phase23AcceptanceMatrix: 导入 importlib 用来检查测试模块是否真实存在；如果没有这行代码，矩阵可能写了不存在的测试名也不会失败。
import json  # 新增代码+Phase23AcceptanceMatrix: 导入 JSON 解析器；如果没有这行代码，矩阵和 result.json 无法被机器验证。
import unittest  # 新增代码+Phase23AcceptanceMatrix: 引入 unittest 测试框架；如果没有这行代码，本文件无法定义测试用例。
from pathlib import Path  # 新增代码+Phase23AcceptanceMatrix: 使用 Path 处理仓库文件路径；如果没有这行代码，Windows 路径拼接更容易出错。


class FinalAcceptanceMatrixPhase23Tests(unittest.TestCase):  # 新增代码+Phase23AcceptanceMatrix: 定义 Phase 23 总验收矩阵测试集合；如果没有这个类，unittest 不会发现矩阵测试。
    def test_phase14_to_phase22_matrix_artifacts_are_complete_and_passed(self) -> None:  # 新增代码+Phase23AcceptanceMatrix: 验证 Phase 14-22 的测试、场景、报告、备份和真实终端验收结果；如果没有这个测试，总矩阵可能只是静态文档。
        root = Path(__file__).resolve().parents[2]  # 新增代码+Phase23AcceptanceMatrix: 定位仓库根目录；如果没有这行代码，测试无法用相对路径检查矩阵文件。
        matrix_path = root / "learning_agent" / "acceptance_controller" / "final_acceptance_matrix_phase23.json"  # 新增代码+Phase23AcceptanceMatrix: 定位 Phase 23 矩阵文件；如果没有这行代码，测试没有目标文档。
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))  # 新增代码+Phase23AcceptanceMatrix: 读取并解析矩阵 JSON；如果没有这行代码，坏 JSON 不会被发现。
        phases = matrix.get("phases", [])  # 新增代码+Phase23AcceptanceMatrix: 读取阶段列表；如果没有这行代码，后续无法逐项验证。
        self.assertEqual([item.get("phase") for item in phases], list(range(14, 23)))  # 新增代码+Phase23AcceptanceMatrix: 断言阶段必须完整覆盖 14 到 22；如果没有这行代码，漏阶段不会暴露。
        for item in phases:  # 新增代码+Phase23AcceptanceMatrix: 遍历每个阶段记录；如果没有这行代码，只会检查矩阵头部。
            phase = item.get("phase")  # 新增代码+Phase23AcceptanceMatrix: 读取阶段号用于失败提示；如果没有这行代码，断言失败时难以定位是哪一阶段。
            for module_name in item.get("tests", []):  # 新增代码+Phase23AcceptanceMatrix: 遍历阶段测试模块；如果没有这行代码，矩阵测试字段不会被验证。
                importlib.import_module(str(module_name))  # 新增代码+Phase23AcceptanceMatrix: 导入测试模块确认存在；如果没有这行代码，矩阵可能引用已删除测试。
            scenario_path = root / str(item.get("scenario", ""))  # 新增代码+Phase23AcceptanceMatrix: 计算场景文件路径；如果没有这行代码，无法验证真实终端验收入口。
            self.assertTrue(scenario_path.exists(), f"phase {phase} scenario missing")  # 新增代码+Phase23AcceptanceMatrix: 断言场景文件存在；如果没有这行代码，真实验收无法复跑。
            json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase23AcceptanceMatrix: 解析场景 JSON；如果没有这行代码，坏场景文件不会被发现。
            report_path = root / str(item.get("report", ""))  # 新增代码+Phase23AcceptanceMatrix: 计算阶段报告路径；如果没有这行代码，无法验证书面记录。
            self.assertTrue(report_path.exists(), f"phase {phase} report missing")  # 新增代码+Phase23AcceptanceMatrix: 断言阶段报告存在；如果没有这行代码，完成记录可能缺失。
            backup_dir = root / str(item.get("backup_dir", ""))  # 新增代码+Phase23AcceptanceMatrix: 计算学习备份目录；如果没有这行代码，无法验证用户学习副本是否保存。
            self.assertTrue(backup_dir.exists(), f"phase {phase} backup missing")  # 新增代码+Phase23AcceptanceMatrix: 断言备份目录存在；如果没有这行代码，规则三可能被漏执行。
            run_dir = root / str(item.get("acceptance_run", ""))  # 新增代码+Phase23AcceptanceMatrix: 计算真实终端验收 run 目录；如果没有这行代码，无法检查可见终端证据。
            self.assertTrue(run_dir.exists(), f"phase {phase} acceptance run missing")  # 新增代码+Phase23AcceptanceMatrix: 断言 run 目录存在；如果没有这行代码，真实终端验收可能只停留在口头说明。
            result_path = run_dir / "result.json"  # 新增代码+Phase23AcceptanceMatrix: 定位验收结果 JSON；如果没有这行代码，无法读取完成状态。
            result = json.loads(result_path.read_text(encoding="utf-8-sig"))  # 新增代码+Phase23AcceptanceMatrix: 读取 result.json 并兼容 BOM；如果没有这行代码，验收通过状态无法机器确认。
            expected = item.get("expected_result", {})  # 新增代码+Phase23AcceptanceMatrix: 读取矩阵里的期望结果；如果没有这行代码，断言没有标准。
            self.assertEqual(bool(result.get("completed")), bool(expected.get("completed")), f"phase {phase} completed mismatch")  # 新增代码+Phase23AcceptanceMatrix: 断言 controller 完成状态；如果没有这行代码，超时/失败 run 可能混进矩阵。
            self.assertEqual(bool(result.get("assertion", {}).get("passed")), bool(expected.get("assertion_passed")), f"phase {phase} assertion mismatch")  # 新增代码+Phase23AcceptanceMatrix: 断言场景断言通过；如果没有这行代码，只有启动成功也可能被当成验收通过。
            self.assertEqual(int(result.get("permission_sent_count", -1)), int(expected.get("permission_sent_count", -1)), f"phase {phase} permission count mismatch")  # 新增代码+Phase23AcceptanceMatrix: 断言没有意外权限发送；如果没有这行代码，高风险动作可能被隐藏。
            self.assertTrue((run_dir / "03_final.png").exists(), f"phase {phase} final screenshot missing")  # 新增代码+Phase23AcceptanceMatrix: 断言最终截图存在；如果没有这行代码，真实可见终端证据不完整。


if __name__ == "__main__":  # 新增代码+Phase23AcceptanceMatrix: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase23AcceptanceMatrix: 启动 unittest 主函数；如果没有这行代码，直接运行文件不会执行任何测试。
