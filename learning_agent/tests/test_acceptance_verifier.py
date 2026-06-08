"""独立真实验收断言验证器测试。"""  # 新增代码+验收验证器: 说明本文件专门测试可复验 verifier；若没有这行代码，测试职责不清楚
from __future__ import annotations  # 新增代码+验收验证器: 允许类型注解延迟解析；若没有这行代码，部分注解可能在导入时提前求值

import json  # 新增代码+验收验证器: 用标准库写入场景和事件 JSON；若没有这行代码，测试无法构造可复验输入
import tempfile  # 新增代码+验收验证器: 用临时目录隔离验收证据；若没有这行代码，测试会污染真实 runs 目录
import unittest  # 新增代码+验收验证器: 使用项目现有 unittest 测试框架；若没有这行代码，测试无法被 discover 运行
from pathlib import Path  # 新增代码+验收验证器: 用 Path 处理 Windows 路径；若没有这行代码，路径拼接会变得脆弱

from learning_agent.acceptance.verifier import verify_acceptance_run  # 新增代码+验收验证器: 导入待实现的独立 verifier；若没有这行代码，测试不能驱动新能力


class AcceptanceVerifierTests(unittest.TestCase):  # 新增代码+验收验证器: 定义独立 verifier 的测试类；若没有这行代码，unittest 无法发现这些用例
    def _write_json(self, path: Path, payload: dict[str, object]) -> None:  # 新增代码+验收验证器: 提供写 JSON 的小工具；若没有这行代码，每个测试都要重复编码细节
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")  # 新增代码+验收验证器: 把结构化数据写成 UTF-8 JSON；若没有这行代码，verifier 没有场景或结果文件可读

    def _write_jsonl(self, path: Path, rows: list[dict[str, object]]) -> None:  # 新增代码+验收验证器: 提供写 JSONL 的小工具；若没有这行代码，事件日志构造会重复且容易格式不一致
        path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")  # 新增代码+验收验证器: 把事件逐行写入 JSONL；若没有这行代码，verifier 无法按真实事件格式读取

    def _write_json_with_bom(self, path: Path, payload: dict[str, object]) -> None:  # 新增代码+验收验证器: 提供带 BOM 的 JSON 写入工具；若没有这行代码，无法复现 PowerShell Set-Content 的真实 result.json 编码
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8-sig")  # 新增代码+验收验证器: 用 utf-8-sig 写入 JSON；若没有这行代码，测试无法证明 verifier 兼容真实 controller 输出

    def test_verify_acceptance_run_replays_passed_smoke_evidence(self) -> None:  # 新增代码+验收验证器: 验证 verifier 能离线复验成功 run；若没有这行代码，controller 之外无法独立审计验收
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+验收验证器: 创建临时目录承载本轮假证据；若没有这行代码，测试会依赖真实历史 runs
            root = Path(raw_dir)  # 新增代码+验收验证器: 把临时目录转成 Path；若没有这行代码，后续路径拼接不方便
            run_dir = root / "run"  # 新增代码+验收验证器: 定义假运行目录；若没有这行代码，result 和事件没有统一根目录
            run_dir.mkdir()  # 新增代码+验收验证器: 创建运行目录；若没有这行代码，写证据文件会失败
            scenario_path = root / "scenario.json"  # 新增代码+验收验证器: 定义假场景文件路径；若没有这行代码，verifier 没有断言配置来源
            event_log = run_dir / "events.jsonl"  # 新增代码+验收验证器: 定义事件日志路径；若没有这行代码，verifier 无法读取状态链
            debug_log = run_dir / "latest_run_readable.md"  # 新增代码+验收验证器: 定义调试日志路径；若没有这行代码，debug_log_contains 无法被验证
            result_json = run_dir / "result.json"  # 新增代码+验收验证器: 定义 controller 结果路径；若没有这行代码，权限次数和截图索引没有来源
            startup_png = run_dir / "01_startup.png"  # 新增代码+验收验证器: 定义启动截图证据；若没有这行代码，artifact_checks 无法证明窗口启动截图存在
            prompt_png = run_dir / "02_prompt_sent.png"  # 新增代码+验收验证器: 定义 prompt 截图证据；若没有这行代码，artifact_checks 无法证明输入截图存在
            final_png = run_dir / "03_final.png"  # 新增代码+验收验证器: 定义最终截图证据；若没有这行代码，artifact_checks 无法证明最终画面存在
            startup_png.write_bytes(b"png")  # 新增代码+验收验证器: 写入启动截图占位内容；若没有这行代码，截图路径存在性检查会失败
            prompt_png.write_bytes(b"png")  # 新增代码+验收验证器: 写入 prompt 截图占位内容；若没有这行代码，prompt 截图存在性检查会失败
            final_png.write_bytes(b"png")  # 新增代码+验收验证器: 写入最终截图占位内容；若没有这行代码，最终截图存在性检查会失败
            debug_log.write_text("ACCEPTANCE_HARNESS_OK\n", encoding="utf-8")  # 新增代码+验收验证器: 写入包含成功标记的 debug log；若没有这行代码，日志断言会失败
            self._write_json(scenario_path, {"name": "smoke", "success_marker": "ACCEPTANCE_HARNESS_OK", "required_event_states": ["agent_ready_for_user_prompt", "user_prompt_received", "final_answer_printed"], "event_answer_contains": ["ACCEPTANCE_HARNESS_OK"], "debug_log_contains": ["ACCEPTANCE_HARNESS_OK"], "max_permission_sent_count": 0})  # 新增代码+验收验证器: 写入场景断言配置；若没有这行代码，verifier 不知道该检查哪些证据
            self._write_jsonl(event_log, [{"schema_version": 1, "state": "agent_ready_for_user_prompt", "payload": {}}, {"schema_version": 1, "state": "user_prompt_received", "payload": {"prompt_preview": "请只回复一行"}}, {"schema_version": 1, "state": "final_answer_printed", "payload": {"answer_text": "ACCEPTANCE_HARNESS_OK", "answer_preview": "ACCEPTANCE_HARNESS_OK"}}])  # 新增代码+验收验证器: 写入可复验事件链；若没有这行代码，状态断言和回答断言没有输入
            self._write_json(result_json, {"permission_sent_count": 0, "event_log": str(event_log), "startup_screenshot": str(startup_png), "prompt_screenshot": str(prompt_png), "final_screenshot": str(final_png), "copied_debug_log": str(debug_log), "permission_policy_decisions": []})  # 新增代码+验收验证器: 写入 controller 结果索引；若没有这行代码，verifier 无法复核权限次数和证据文件
            report = verify_acceptance_run(run_dir, scenario_path)  # 新增代码+验收验证器: 执行独立复验；若没有这行代码，测试不会触发待实现行为
            self.assertTrue(report["completed"])  # 新增代码+验收验证器: 断言整体验收通过；若没有这行代码，无法证明 verifier 会给出最终结论
            self.assertTrue(report["assertion"]["state_checks"]["final_answer_printed"])  # 新增代码+验收验证器: 断言状态检查进入报告；若没有这行代码，失败时无法定位缺哪个事件
            self.assertTrue(report["assertion"]["event_answer_checks"]["ACCEPTANCE_HARNESS_OK"])  # 新增代码+验收验证器: 断言最终回答检查进入报告；若没有这行代码，用户可见答案无法被独立审计
            self.assertTrue(report["assertion"]["debug_log_checks"]["ACCEPTANCE_HARNESS_OK"])  # 新增代码+验收验证器: 断言日志检查进入报告；若没有这行代码，工具或运行证据无法被独立审计
            self.assertTrue(report["assertion"]["artifact_checks"]["final_screenshot"])  # 新增代码+验收验证器: 断言截图证据进入报告；若没有这行代码，真实可见终端证据可能缺失仍通过

    def test_verify_acceptance_run_fails_when_answer_marker_is_missing(self) -> None:  # 新增代码+验收验证器: 验证缺少最终回答标记会失败；若没有这行代码，verifier 可能只看事件就误判通过
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+验收验证器: 创建隔离目录；若没有这行代码，失败场景会污染真实 runs
            root = Path(raw_dir)  # 新增代码+验收验证器: 把临时目录转成 Path；若没有这行代码，后续文件路径难以维护
            run_dir = root / "run"  # 新增代码+验收验证器: 定义假运行目录；若没有这行代码，失败证据没有统一位置
            run_dir.mkdir()  # 新增代码+验收验证器: 创建运行目录；若没有这行代码，写入事件会失败
            scenario_path = root / "scenario.json"  # 新增代码+验收验证器: 定义场景路径；若没有这行代码，verifier 没有断言目标
            event_log = run_dir / "events.jsonl"  # 新增代码+验收验证器: 定义事件日志路径；若没有这行代码，状态链没有来源
            debug_log = run_dir / "latest_run_readable.md"  # 新增代码+验收验证器: 定义调试日志路径；若没有这行代码，日志断言没有来源
            result_json = run_dir / "result.json"  # 新增代码+验收验证器: 定义结果文件路径；若没有这行代码，artifact 索引没有来源
            debug_log.write_text("没有目标标记\n", encoding="utf-8")  # 新增代码+验收验证器: 写入不含成功标记的日志；若没有这行代码，marker 可能从日志误通过
            self._write_json(scenario_path, {"name": "bad", "success_marker": "NEEDED", "required_event_states": ["final_answer_printed"], "event_answer_contains": ["NEEDED"], "debug_log_contains": []})  # 新增代码+验收验证器: 写入必须包含 NEEDED 的场景；若没有这行代码，失败条件不明确
            self._write_jsonl(event_log, [{"schema_version": 1, "state": "final_answer_printed", "payload": {"answer_text": "OTHER", "answer_preview": "OTHER"}}])  # 新增代码+验收验证器: 写入不含目标标记的最终回答；若没有这行代码，回答失败路径不会被触发
            self._write_json(result_json, {"permission_sent_count": 0, "event_log": str(event_log), "copied_debug_log": str(debug_log)})  # 新增代码+验收验证器: 写入最小结果索引；若没有这行代码，verifier 无法读取 event/log 位置
            report = verify_acceptance_run(run_dir, scenario_path)  # 新增代码+验收验证器: 执行失败场景复验；若没有这行代码，测试不会检查失败路径
            self.assertFalse(report["completed"])  # 新增代码+验收验证器: 断言缺少回答标记时整体失败；若没有这行代码，验收可能假通过
            self.assertFalse(report["assertion"]["event_answer_checks"]["NEEDED"])  # 新增代码+验收验证器: 断言失败原因落到回答检查；若没有这行代码，外部 agent 难以定位问题

    def test_verify_acceptance_run_reads_powershell_bom_result_json(self) -> None:  # 新增代码+验收验证器: 验证真实 PowerShell BOM JSON 可复验；若没有这行代码，controller 产物会在 CLI 复验时崩溃
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+验收验证器: 创建隔离目录；若没有这行代码，BOM 测试会污染真实 runs
            root = Path(raw_dir)  # 新增代码+验收验证器: 把临时目录转成 Path；若没有这行代码，后续路径拼接不方便
            run_dir = root / "run"  # 新增代码+验收验证器: 定义假运行目录；若没有这行代码，测试证据没有统一根目录
            run_dir.mkdir()  # 新增代码+验收验证器: 创建运行目录；若没有这行代码，写 result 和事件会失败
            scenario_path = root / "scenario.json"  # 新增代码+验收验证器: 定义场景文件；若没有这行代码，verifier 没有断言配置
            event_log = run_dir / "events.jsonl"  # 新增代码+验收验证器: 定义事件日志；若没有这行代码，状态链没有来源
            debug_log = run_dir / "latest_run_readable.md"  # 新增代码+验收验证器: 定义 debug log；若没有这行代码，日志证据没有来源
            result_json = run_dir / "result.json"  # 新增代码+验收验证器: 定义 BOM result 文件；若没有这行代码，无法复现真实 controller 编码
            for artifact_name in ["01_startup.png", "02_prompt_sent.png", "03_final.png"]:  # 新增代码+验收验证器: 遍历必须存在的截图文件名；若没有这行代码，artifact_checks 会因为缺截图失败
                (run_dir / artifact_name).write_bytes(b"png")  # 新增代码+验收验证器: 写入截图占位文件；若没有这行代码，BOM 测试无法专注验证编码兼容
            debug_log.write_text("OK\n", encoding="utf-8")  # 新增代码+验收验证器: 写入日志证据；若没有这行代码，debug log artifact 会缺失
            self._write_json(scenario_path, {"name": "bom", "success_marker": "OK", "required_event_states": ["final_answer_printed"], "event_answer_contains": ["OK"], "debug_log_contains": ["OK"]})  # 新增代码+验收验证器: 写入最小场景；若没有这行代码，verifier 不知道要检查 OK
            self._write_jsonl(event_log, [{"schema_version": 1, "state": "final_answer_printed", "payload": {"answer_text": "OK", "answer_preview": "OK"}}])  # 新增代码+验收验证器: 写入最终回答事件；若没有这行代码，回答断言没有输入
            self._write_json_with_bom(result_json, {"permission_sent_count": 0, "event_log": str(event_log), "copied_debug_log": str(debug_log), "startup_screenshot": str(run_dir / "01_startup.png"), "prompt_screenshot": str(run_dir / "02_prompt_sent.png"), "final_screenshot": str(run_dir / "03_final.png")})  # 新增代码+验收验证器: 写入带 BOM 的 result.json；若没有这行代码，无法覆盖真实失败原因
            report = verify_acceptance_run(run_dir, scenario_path)  # 新增代码+验收验证器: 执行带 BOM result 的复验；若没有这行代码，测试不会触发编码读取路径
            self.assertTrue(report["completed"])  # 新增代码+验收验证器: 断言 BOM 不影响复验通过；若没有这行代码，真实 controller 输出仍可能不可复验

    def test_verify_acceptance_run_checks_event_payload_contains(self) -> None:  # 新增代码+Phase24AcceptancePayload: 验证 verifier 会复验事件 payload 文本；若没有这段测试，/chrome 输出 false 仍可能被离线误判通过。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase24AcceptancePayload: 创建隔离目录；若没有这行代码，payload 门禁测试会污染真实验收 runs。
            root = Path(raw_dir)  # 新增代码+Phase24AcceptancePayload: 把临时目录转成 Path；若没有这行代码，后续路径拼接不稳定。
            run_dir = root / "run"  # 新增代码+Phase24AcceptancePayload: 定义假 run 目录；若没有这行代码，result 和 events 没有统一根目录。
            run_dir.mkdir()  # 新增代码+Phase24AcceptancePayload: 创建假 run 目录；若没有这行代码，写事件和截图会失败。
            scenario_path = root / "scenario.json"  # 新增代码+Phase24AcceptancePayload: 定义假场景路径；若没有这行代码，verifier 没有 event_payload_contains 配置来源。
            event_log = run_dir / "events.jsonl"  # 新增代码+Phase24AcceptancePayload: 定义事件日志路径；若没有这行代码，payload 检查没有输入。
            result_json = run_dir / "result.json"  # 新增代码+Phase24AcceptancePayload: 定义 result.json 路径；若没有这行代码，verifier 无法索引事件和截图。
            for artifact_name in ["01_startup.png", "02_prompt_sent.png", "03_final.png"]:  # 新增代码+Phase24AcceptancePayload: 遍历真实终端截图文件名；若没有这行代码，基础 artifact 检查会失败。
                (run_dir / artifact_name).write_bytes(b"png")  # 新增代码+Phase24AcceptancePayload: 写入截图占位文件；若没有这行代码，测试焦点会被截图缺失干扰。
            self._write_json(scenario_path, {"name": "chrome_payload", "success_marker": "", "required_event_states": ["chrome_status_printed"], "event_payload_contains": ["real_extension_e2e=true"]})  # 新增代码+Phase24AcceptancePayload: 写入只靠事件 payload 判定的 /chrome 场景；若没有这行代码，无法覆盖 Phase 24 门禁形态。
            self._write_json(result_json, {"permission_sent_count": 0, "event_log": str(event_log), "startup_screenshot": str(run_dir / "01_startup.png"), "prompt_screenshot": str(run_dir / "02_prompt_sent.png"), "final_screenshot": str(run_dir / "03_final.png")})  # 新增代码+Phase24AcceptancePayload: 写入 controller 结果索引；若没有这行代码，verifier 找不到事件和截图证据。
            self._write_jsonl(event_log, [{"schema_version": 1, "state": "chrome_status_printed", "payload": {"output_text": "real_extension_e2e=true"}}])  # 新增代码+Phase24AcceptancePayload: 先写入 true 输出；若没有这行代码，无法证明 payload 命中时会通过。
            passed_report = verify_acceptance_run(run_dir, scenario_path)  # 新增代码+Phase24AcceptancePayload: 复验 true payload；若没有这行代码，测试不会触发通过路径。
            self.assertTrue(passed_report["completed"])  # 新增代码+Phase24AcceptancePayload: 断言 true payload 通过；若没有这行代码，新增门禁可能误伤成功场景。
            self.assertTrue(passed_report["assertion"]["event_payload_checks"]["real_extension_e2e=true"])  # 新增代码+Phase24AcceptancePayload: 断言报告暴露 payload 检查明细；若没有这行代码，失败时不易定位缺项。
            self._write_jsonl(event_log, [{"schema_version": 1, "state": "chrome_status_printed", "payload": {"output_text": "real_extension_e2e=false"}}])  # 新增代码+Phase24AcceptancePayload: 再写入 false 输出；若没有这行代码，无法证明 false 会被拦截。
            failed_report = verify_acceptance_run(run_dir, scenario_path)  # 新增代码+Phase24AcceptancePayload: 复验 false payload；若没有这行代码，测试不会触发失败路径。
            self.assertFalse(failed_report["completed"])  # 新增代码+Phase24AcceptancePayload: 断言 false payload 会让整体验收失败；若没有这行代码，Phase 24 仍可能假通过。
            self.assertFalse(failed_report["assertion"]["event_payload_checks"]["real_extension_e2e=true"])  # 新增代码+Phase24AcceptancePayload: 断言失败原因落在 payload 检查；若没有这行代码，外部 agent 难以复盘。

    def test_verify_acceptance_run_checks_required_artifact_globs(self) -> None:  # 新增代码+BrowserRecordingStage9: 验证 verifier 能检查录制帧和 GIF 这类外部产物；若没有这行代码，Stage 9 只能靠日志说成功。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserRecordingStage9: 创建隔离项目根；若没有这行代码，glob 测试会污染真实 browser_artifacts。
            project_root = Path(raw_dir) / "project"  # 新增代码+BrowserRecordingStage9: 模拟仓库根目录；若没有这行代码，{project_root} 占位符没有稳定目标。
            scenario_dir = project_root / "learning_agent" / "acceptance_controller" / "scenarios"  # 新增代码+BrowserRecordingStage9: 模拟真实 scenario 文件位置；若没有这行代码，verifier 无法从场景路径反推项目根。
            run_dir = project_root / "learning_agent" / "acceptance_controller" / "runs" / "stage9"  # 新增代码+BrowserRecordingStage9: 模拟真实 controller run 目录；若没有这行代码，{run_dir} 占位符没有目标。
            recording_dir = project_root / "browser_artifacts" / "browser_recordings" / "stage9_glob"  # 新增代码+BrowserRecordingStage9: 模拟录制 artifact 目录；若没有这行代码，glob 没有可匹配文件。
            frame_dir = recording_dir / "frames"  # 新增代码+BrowserRecordingStage9: 定义帧目录；若没有这行代码，帧 glob 不可测试。
            scenario_dir.mkdir(parents=True)  # 新增代码+BrowserRecordingStage9: 创建场景目录；若没有这行代码，scenario JSON 无法写入。
            run_dir.mkdir(parents=True)  # 新增代码+BrowserRecordingStage9: 创建 run 目录；若没有这行代码，result/event 文件无法写入。
            frame_dir.mkdir(parents=True)  # 新增代码+BrowserRecordingStage9: 创建帧目录；若没有这行代码，帧文件无法写入。
            scenario_path = scenario_dir / "stage9.json"  # 新增代码+BrowserRecordingStage9: 定义场景路径；若没有这行代码，verifier 没有配置文件。
            event_log = run_dir / "events.jsonl"  # 新增代码+BrowserRecordingStage9: 定义事件日志路径；若没有这行代码，状态检查没有输入。
            debug_log = run_dir / "latest_run_readable.md"  # 新增代码+BrowserRecordingStage9: 定义 debug log 路径；若没有这行代码，日志检查没有输入。
            result_json = run_dir / "result.json"  # 新增代码+BrowserRecordingStage9: 定义 controller result 路径；若没有这行代码，verifier 无法索引证据。
            for artifact_name in ["01_startup.png", "02_prompt_sent.png", "03_final.png"]:  # 新增代码+BrowserRecordingStage9: 遍历 controller 固定截图；若没有这行代码，基础 artifact_checks 会失败。
                (run_dir / artifact_name).write_bytes(b"png")  # 新增代码+BrowserRecordingStage9: 写入截图占位文件；若没有这行代码，测试焦点会被基础截图缺失干扰。
            (recording_dir / "recording_manifest.json").write_text("{}", encoding="utf-8")  # 新增代码+BrowserRecordingStage9: 写入录制 manifest；若没有这行代码，manifest glob 应失败。
            (frame_dir / "frame-0001.png").write_bytes(b"png")  # 新增代码+BrowserRecordingStage9: 写入帧文件；若没有这行代码，帧 glob 应失败。
            (recording_dir / "stage9.gif").write_bytes(b"gif")  # 新增代码+BrowserRecordingStage9: 写入 GIF 文件；若没有这行代码，GIF glob 应失败。
            debug_log.write_text("STAGE9_OK\n", encoding="utf-8")  # 新增代码+BrowserRecordingStage9: 写入成功日志；若没有这行代码，debug_log_contains 会失败。
            self._write_json(scenario_path, {"name": "stage9", "success_marker": "STAGE9_OK", "required_event_states": ["final_answer_printed"], "event_answer_contains": ["STAGE9_OK"], "debug_log_contains": ["STAGE9_OK"], "required_artifact_globs": ["{project_root}/browser_artifacts/browser_recordings/stage9_glob/recording_manifest.json", "{project_root}/browser_artifacts/browser_recordings/stage9_glob/frames/*.png", "{project_root}/browser_artifacts/browser_recordings/stage9_glob/*.gif"]})  # 新增代码+BrowserRecordingStage9: 写入带 glob 门禁的场景；若没有这行代码，verifier 不知道要检查录制产物。
            self._write_jsonl(event_log, [{"schema_version": 1, "state": "final_answer_printed", "payload": {"answer_text": "STAGE9_OK", "answer_preview": "STAGE9_OK"}}])  # 新增代码+BrowserRecordingStage9: 写入最终回答事件；若没有这行代码，回答检查没有输入。
            self._write_json(result_json, {"permission_sent_count": 0, "event_log": str(event_log), "copied_debug_log": str(debug_log), "startup_screenshot": str(run_dir / "01_startup.png"), "prompt_screenshot": str(run_dir / "02_prompt_sent.png"), "final_screenshot": str(run_dir / "03_final.png")})  # 新增代码+BrowserRecordingStage9: 写入 controller 结果索引；若没有这行代码，verifier 找不到基础证据。
            report = verify_acceptance_run(run_dir, scenario_path)  # 新增代码+BrowserRecordingStage9: 执行独立复验；若没有这行代码，glob 门禁不会被触发。
            self.assertTrue(report["completed"])  # 新增代码+BrowserRecordingStage9: 断言所有 artifact glob 存在时通过；若没有这行代码，无法证明门禁可用。
            self.assertTrue(all(report["assertion"]["required_artifact_glob_checks"].values()))  # 新增代码+BrowserRecordingStage9: 断言每个 glob 都有匹配；若没有这行代码，报告可能只给总布尔值不便审计。


if __name__ == "__main__":  # 新增代码+验收验证器: 支持直接运行本测试文件；若没有这行代码，手动调试需要额外命令
    unittest.main()  # 新增代码+验收验证器: 启动 unittest 主程序；若没有这行代码，直接执行文件不会运行测试
