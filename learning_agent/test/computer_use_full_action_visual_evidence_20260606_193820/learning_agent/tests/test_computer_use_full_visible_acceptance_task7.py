"""Task7 严格可见终端验收配置测试。"""  # 新增代码+DesktopTaskVisibleAcceptance：说明本文件专门锁定严格可见终端场景和 controller 能力；如果没有这一行，用户不容易看出这个测试文件的学习目的。

from __future__ import annotations  # 新增代码+DesktopTaskVisibleAcceptance：启用延迟类型注解解析；如果没有这一行，后续类型写法在旧解释器下更容易出兼容问题。

import json  # 新增代码+DesktopTaskVisibleAcceptance：导入 JSON 解析标准库；如果没有这一行，测试无法读取严格场景文件。
import tempfile  # 新增代码+DesktopTaskVisibleAcceptance：导入临时目录工具；如果没有这一行，verifier 复验测试会污染真实 runs 目录。
import unittest  # 新增代码+DesktopTaskVisibleAcceptance：导入 unittest 测试框架；如果没有这一行，Python 无法发现和运行这些回归用例。
from pathlib import Path  # 新增代码+DesktopTaskVisibleAcceptance：导入 Path 处理项目路径；如果没有这一行，Windows 路径拼接会更脆弱。

from learning_agent.acceptance.verifier import verify_acceptance_run  # 新增代码+DesktopTaskVisibleAcceptance：导入离线验收复验器；如果没有这一行，测试无法证明 controller 证据可复核。


PROJECT_ROOT = Path(__file__).resolve().parents[2]  # 新增代码+DesktopTaskVisibleAcceptance：定位 OpenHarness 项目根目录；如果没有这一行，从不同 cwd 运行测试会找不到文件。
SCENARIO_PATH = PROJECT_ROOT / "learning_agent" / "acceptance_controller" / "scenarios" / "computer_use_full_paint_pikachu_strict.json"  # 新增代码+DesktopTaskVisibleAcceptance：定位 Task7 严格场景；如果没有这一行，测试没有真实场景配置来源。
CONTROLLER_PATH = PROJECT_ROOT / "learning_agent" / "acceptance_controller" / "controller.ps1"  # 新增代码+DesktopTaskVisibleAcceptance：定位真实 PowerShell controller；如果没有这一行，测试可能只验证到假路径。


class ComputerUseFullVisibleAcceptanceTask7Tests(unittest.TestCase):  # 新增代码+DesktopTaskVisibleAcceptance：类段开始，集中验证 Task7 的场景和 controller 合同；如果没有这个类，unittest 不会组织这些门禁。
    def test_strict_scenario_uses_natural_full_mode_prompt_lines(self) -> None:  # 修改代码+FullNaturalUserFlow：函数段开始，验证严格场景只输入自然 full 命令、自然语言任务和 stop；如果没有这个测试，场景可能又退回动态 token 这种非真实用户习惯。
        scenario = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))  # 新增代码+DesktopTaskVisibleAcceptance：读取并解析严格场景 JSON；如果没有这一行，场景格式错误不会被测试发现。
        self.assertTrue(scenario["multi_prompt_lines"])  # 新增代码+DesktopTaskVisibleAcceptance：断言该场景启用多轮真实输入；如果没有这一行，controller 可能继续把四行拼成一行。
        self.assertEqual(scenario["prompt_lines"][0], "/computer use --full")  # 修改代码+FullNaturalUserFlow：断言第一行就是用户自然授权 full mode；如果没有这一行，场景可能继续依赖不自然的 token 申请。
        self.assertEqual(scenario["prompt_lines"][1], "请使用本地电脑的画图软件画一个皮卡丘。")  # 修改代码+FullNaturalUserFlow：断言第二行直接是自然语言桌面任务；如果没有这一行，验收可能只开 full mode 不执行任务。
        self.assertEqual(scenario["prompt_lines"][2], "/computer stop")  # 修改代码+FullNaturalUserFlow：断言第三行执行清理；如果没有这一行，full mode 可能在验收后残留。
        self.assertEqual(scenario["capture_event_payload_regex"], {})  # 修改代码+FullNaturalUserFlow：断言严格场景不再捕获动态确认 token；如果没有这一行，controller 可能继续模拟非真实用户流程。
        self.assertNotIn("Computer Use Full Request", scenario["event_payload_contains"])  # 新增代码+FullNaturalUserFlow：断言验收不再要求旧申请面板；如果没有这一行，旧 token 面板可能悄悄变成通过条件。
        self.assertNotIn("confirmation_token=", scenario["event_payload_contains"])  # 新增代码+FullNaturalUserFlow：断言验收不再要求 token 输出；如果没有这一行，不自然确认流程可能回归。
        self.assertIn("COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK", scenario["event_answer_contains"])  # 新增代码+DesktopTaskVisibleAcceptance：断言最终回答必须包含桌面任务 OK token；如果没有这一行，只有 /computer 命令输出也可能假通过。
        self.assertIn("Computer Use Stop", scenario["event_payload_contains"])  # 新增代码+DesktopTaskVisibleAcceptance：断言 stop 输出进入门禁；如果没有这一行，验收可能不证明清理发生。
        self.assertIn("gui_action_count=[1-9][0-9]*", scenario["event_payload_regex"])  # 新增代码+DesktopTaskVisibleAcceptance：断言 GUI 动作数量必须大于 0；如果没有这一行，空动作报告可能通过。
        self.assertIn("low_level_event_count=[1-9][0-9]*", scenario["event_payload_regex"])  # 新增代码+DesktopTaskVisibleAcceptance：断言底层输入事件数量必须大于 0；如果没有这一行，只有规划没有执行证据也可能通过。
    # 修改代码+FullNaturalUserFlow：函数段结束，test_strict_scenario_uses_natural_full_mode_prompt_lines 到此结束；如果没有这个边界说明，代码小白不容易看出自然 full 场景测试范围。

    def test_controller_supports_dynamic_prompt_capture_and_regex_checks(self) -> None:  # 新增代码+DesktopTaskVisibleAcceptance：函数段开始，验证 controller 具备动态变量捕获、多轮输入和正则断言能力；如果没有这个测试，PowerShell 脚本可能被改回单 prompt。
        controller_text = CONTROLLER_PATH.read_text(encoding="utf-8")  # 新增代码+DesktopTaskVisibleAcceptance：读取 controller 文本；如果没有这一行，测试没有待检查内容。
        self.assertIn("capture_event_payload_regex", controller_text)  # 新增代码+DesktopTaskVisibleAcceptance：断言 controller 读取动态捕获配置；如果没有这一行，confirmation_token 无法被提取。
        self.assertIn("Update-CapturedPromptVariables", controller_text)  # 新增代码+DesktopTaskVisibleAcceptance：断言 controller 有捕获函数；如果没有这一行，token 捕获逻辑可能缺失。
        self.assertIn("Resolve-PromptLineVariables", controller_text)  # 修改代码+FullNaturalUserFlow：断言 controller 仍保留占位符替换能力给其它场景兼容；如果没有这一行，旧场景变量替换会退化。
        self.assertIn("MultiPromptEnabled", controller_text)  # 新增代码+DesktopTaskVisibleAcceptance：断言 controller 有多轮输入开关；如果没有这一行，旧场景和新场景无法安全区分。
        self.assertIn("PromptLineInFlightIndex", controller_text)  # 新增代码+DesktopTaskVisibleAcceptance：断言 controller 会等待上一行处理完成；如果没有这一行，四行 prompt 可能连续粘贴导致错位。
        self.assertIn("PromptLineAcknowledgedByUserPromptReceived", controller_text)  # 新增代码+NaturalPromptNoRetry: 断言自然语言行收到 user_prompt_received 后不再等待 ready 重试；如果没有这一行，长时间桌面任务会被 controller 重复输入同一句 prompt。
        self.assertIn("event_payload_regex", controller_text)  # 新增代码+DesktopTaskVisibleAcceptance：断言 controller 读取 payload 正则断言；如果没有这一行，动作数量大于 0 的门禁无法表达。
        self.assertIn("event_payload_regex_checks", controller_text)  # 新增代码+DesktopTaskVisibleAcceptance：断言 controller 把正则检查写进结果；如果没有这一行，失败时用户看不到数值门槛缺哪项。
    # 新增代码+DesktopTaskVisibleAcceptance：函数段结束，test_controller_supports_dynamic_prompt_capture_and_regex_checks 到此结束；如果没有这个边界说明，代码小白不容易看出 controller 能力测试范围。

    def test_verifier_replays_regex_payload_without_required_debug_log(self) -> None:  # 新增代码+DesktopTaskVisibleAcceptance：函数段开始，验证离线 verifier 能复核正则门禁且不强制空 debug log；如果没有这个测试，真实 controller 通过后离线复验可能误失败。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DesktopTaskVisibleAcceptance：创建隔离临时目录；如果没有这一行，假验收证据会污染项目目录。
            root = Path(raw_dir)  # 新增代码+DesktopTaskVisibleAcceptance：把临时目录转成 Path；如果没有这一行，后续路径拼接会使用脆弱字符串。
            run_dir = root / "run"  # 新增代码+DesktopTaskVisibleAcceptance：定义假 run 目录；如果没有这一行，result 和 events 没有统一位置。
            run_dir.mkdir()  # 新增代码+DesktopTaskVisibleAcceptance：创建假 run 目录；如果没有这一行，写入证据文件会失败。
            scenario_path = root / "scenario.json"  # 新增代码+DesktopTaskVisibleAcceptance：定义假场景路径；如果没有这一行，verifier 没有断言配置来源。
            event_log = run_dir / "events.jsonl"  # 新增代码+DesktopTaskVisibleAcceptance：定义事件日志路径；如果没有这一行，状态和 payload 检查没有输入。
            result_json = run_dir / "result.json"  # 新增代码+DesktopTaskVisibleAcceptance：定义 controller 结果路径；如果没有这一行，verifier 找不到证据索引。
            for artifact_name in ["01_startup.png", "02_prompt_sent.png", "03_final.png"]:  # 新增代码+DesktopTaskVisibleAcceptance：遍历真实 controller 固定截图名；如果没有这一行，基础 artifact 门禁无法通过。
                (run_dir / artifact_name).write_bytes(b"png")  # 新增代码+DesktopTaskVisibleAcceptance：写入截图占位文件；如果没有这一行，测试会被截图缺失干扰。
            scenario_payload = {"name": "regex_payload", "success_marker": "", "required_event_states": ["final_answer_printed"], "event_answer_contains": ["COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK"], "event_payload_regex": ["gui_action_count=[1-9][0-9]*", "low_level_event_count=[1-9][0-9]*"], "max_permission_sent_count": 0}  # 新增代码+DesktopTaskVisibleAcceptance：构造带正则门禁但不要求 debug log 的场景；如果没有这一行，测试无法覆盖 Task7 复验形态。
            scenario_path.write_text(json.dumps(scenario_payload, ensure_ascii=False), encoding="utf-8")  # 新增代码+DesktopTaskVisibleAcceptance：写入假场景 JSON；如果没有这一行，verifier 无法读取配置。
            event_rows = [{"schema_version": 1, "state": "final_answer_printed", "payload": {"answer_text": "COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK gui_action_count=13 low_level_event_count=81", "answer_preview": "COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK"}}]  # 新增代码+DesktopTaskVisibleAcceptance：构造包含动作数量的最终回答事件；如果没有这一行，regex 门禁没有正向样本。
            event_log.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in event_rows) + "\n", encoding="utf-8")  # 新增代码+DesktopTaskVisibleAcceptance：写入 JSONL 事件；如果没有这一行，verifier 没有事件链可读。
            result_payload = {"permission_sent_count": 0, "event_log": str(event_log), "startup_screenshot": str(run_dir / "01_startup.png"), "prompt_screenshot": str(run_dir / "02_prompt_sent.png"), "final_screenshot": str(run_dir / "03_final.png")}  # 新增代码+DesktopTaskVisibleAcceptance：构造最小 result.json 证据索引；如果没有这一行，verifier 找不到事件和截图。
            result_json.write_text(json.dumps(result_payload, ensure_ascii=False), encoding="utf-8")  # 新增代码+DesktopTaskVisibleAcceptance：写入 result.json；如果没有这一行，离线复验无法启动。
            report = verify_acceptance_run(run_dir, scenario_path)  # 新增代码+DesktopTaskVisibleAcceptance：执行离线复验；如果没有这一行，测试不会触发 verifier 新逻辑。
            self.assertTrue(report["completed"])  # 新增代码+DesktopTaskVisibleAcceptance：断言无 debug log 但事件证据完整时通过；如果没有这一行，旧误判可能复发。
            self.assertTrue(report["assertion"]["event_payload_regex_checks"]["gui_action_count=[1-9][0-9]*"])  # 新增代码+DesktopTaskVisibleAcceptance：断言 GUI 动作正则命中；如果没有这一行，正则结果可能没有进入报告。
            self.assertTrue(report["assertion"]["artifact_checks"]["debug_log"])  # 新增代码+DesktopTaskVisibleAcceptance：断言未要求 debug log 时缺文件不算失败；如果没有这一行，空日志强制门禁可能复发。
    # 新增代码+DesktopTaskVisibleAcceptance：函数段结束，test_verifier_replays_regex_payload_without_required_debug_log 到此结束；如果没有这个边界说明，代码小白不容易看出离线复验范围。


if __name__ == "__main__":  # 新增代码+DesktopTaskVisibleAcceptance：文件入口段开始，支持用户直接运行本测试文件；如果没有这一行，用户必须记住 unittest 模块路径。
    unittest.main()  # 新增代码+DesktopTaskVisibleAcceptance：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+DesktopTaskVisibleAcceptance：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，代码小白不容易看出脚本入口范围。
