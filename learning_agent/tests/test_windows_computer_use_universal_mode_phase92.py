# 新增代码+Phase92UniversalComputerUse：导入 json 是为了检查运行报告不会泄露原始 prompt；没有它就无法验证隐私门禁。
import json

# 新增代码+Phase92UniversalComputerUse：导入 tempfile 是为了给测试创建隔离目录；没有它测试会污染真实运行目录。
import tempfile

# 新增代码+Phase92UniversalComputerUse：导入 unittest 是为了使用项目现有的标准测试风格；没有它就无法被 python -m unittest 发现。
import unittest

# 新增代码+Phase92UniversalComputerUse：导入 Path 是为了稳定处理 Windows 路径；没有它路径拼接容易出错。
from pathlib import Path

# 新增代码+Phase92UniversalComputerUse：导入通用运行时是为了验证 Phase92 的核心功能；没有它就无法证明不是按应用单独写控制器。
from learning_agent.computer_use.universal_mode import (
    UniversalWindowsComputerUseRuntime,
    run_phase92_universal_windows_computer_use_contract,
)

# 新增代码+Phase92UniversalComputerUse：导入兼容层归一化函数是为了验证旧 computer_use 工具能进入新 mode；没有它 agent 入口可能无法调用新能力。
from learning_agent.computer_use.tool_surface import normalize_computer_use_compat_arguments

# 修改代码+Phase92UniversalComputerUse：导入 LearningAgent 是为了直接验证真实 agent 的 compat 路由；没有它只能证明底层函数而不能证明模型工具入口可用。
from learning_agent.core.agent import LearningAgent


# 新增代码+Phase92UniversalComputerUse：这个测试类覆盖“prompt 开启通用 Computer Use mode”的生产契约；没有这组测试就容易退回每个软件单独写控制器。
class WindowsComputerUseUniversalModePhase92Tests(unittest.TestCase):
    # 新增代码+Phase92UniversalComputerUse：这个测试验证兼容工具能把 operation=mode 路由到通用运行时；没有它用户输入 prompt 后可能仍走不到新模式。
    def test_tool_surface_routes_mode_to_single_universal_runtime(self):
        # 新增代码+Phase92UniversalComputerUse：准备一个真实用户风格的 prompt；没有它测试只会覆盖机械参数而不是用户真正会说的话。
        prompt = "打开 computer use，帮我操作一个普通 Windows 应用，但先不要真的点击。"

        # 新增代码+Phase92UniversalComputerUse：调用旧入口的归一化逻辑；没有它就无法确认对现有 agent 工具兼容。
        dispatch = normalize_computer_use_compat_arguments({"operation": "mode", "prompt": prompt})

        # 新增代码+Phase92UniversalComputerUse：确认归一化成功；没有它后续断言会把错误原因掩盖掉。
        self.assertTrue(dispatch["ok"])

        # 新增代码+Phase92UniversalComputerUse：确认路由到通用 mode，而不是 Notepad/Paint 等单应用控制器；没有它架构方向会跑偏。
        self.assertEqual(dispatch["target_tool"], "computer_use_mode")

        # 新增代码+Phase92UniversalComputerUse：确认 prompt 被传给运行时；没有它 agent 无法按用户自然语言任务规划。
        self.assertEqual(dispatch["arguments"]["prompt"], prompt)

        # 新增代码+Phase92UniversalComputerUse：确认默认不执行真实动作；没有它测试可能误触真实桌面。
        self.assertFalse(dispatch["arguments"]["real_actions"])

        # 新增代码+Phase92UniversalComputerUse：确认审计信息隐藏原文；没有它日志可能泄露用户 prompt。
        self.assertNotIn(prompt, json.dumps(dispatch["audit_arguments"], ensure_ascii=False))

        # 新增代码+Phase92UniversalComputerUse：确认审计信息保留哈希追踪；没有它排查问题时无法关联同一次用户任务。
        self.assertIn("prompt_sha256_16", dispatch["audit_arguments"])

    # 新增代码+Phase92UniversalComputerUse：这个测试验证运行时只提供一个通用控制闭环；没有它就无法防止未来又变成每个应用一套控制器。
    def test_runtime_reports_universal_prompt_to_app_contract(self):
        # 新增代码+Phase92UniversalComputerUse：创建临时目录保存运行报告；没有它测试会污染项目真实输出目录。
        with tempfile.TemporaryDirectory() as temporary_directory:
            # 新增代码+Phase92UniversalComputerUse：初始化 Phase92 通用运行时；没有它无法验证核心运行时状态。
            runtime = UniversalWindowsComputerUseRuntime(base_dir=Path(temporary_directory))

            # 新增代码+Phase92UniversalComputerUse：执行不触发真实动作的 prompt 模式；没有它测试会依赖真实桌面状态而不稳定。
            report = runtime.run_prompt("请打开 computer use，准备控制任意普通 Windows 应用。", real_actions=False)

        # 新增代码+Phase92UniversalComputerUse：确认运行成功；没有它后续能力断言可能建立在失败报告上。
        self.assertTrue(report["ok"])

        # 新增代码+Phase92UniversalComputerUse：确认是单一通用运行时；没有它无法满足“不是每个软件单独做授控功能”的要求。
        self.assertTrue(report["single_universal_runtime"])

        # 新增代码+Phase92UniversalComputerUse：确认设计目标是 prompt 到任意普通应用；没有它模式会退化成固定脚本。
        self.assertTrue(report["prompt_to_any_normal_app"])

        # 新增代码+Phase92UniversalComputerUse：确认不需要 per-app controller；没有它就违背用户要求的通用 Computer Use 架构。
        self.assertFalse(report["per_app_controller_required"])

        # 新增代码+Phase92UniversalComputerUse：确认代表性应用只是验收场景；没有它测试场景可能被误解为架构依赖。
        self.assertTrue(report["representative_apps_are_acceptance_only"])

        # 新增代码+Phase92UniversalComputerUse：确认运行时包含观察-规划-动作-验证闭环；没有它就不是 OS 级 Computer Use 的通用模型。
        self.assertTrue(report["generic_observe_plan_act_verify_loop"])

        # 新增代码+Phase92UniversalComputerUse：确认接入观察融合层；没有它 agent 无法综合窗口、OCR、鼠标、授权等状态。
        self.assertTrue(report["uses_observation_fusion"])

        # 新增代码+Phase92UniversalComputerUse：确认接入 prompt 任务规划层；没有它自然语言 prompt 无法转成可执行步骤。
        self.assertTrue(report["uses_prompt_task_planner"])

        # 新增代码+Phase92UniversalComputerUse：确认动作层是通用层；没有它仍然可能依赖某个具体应用的控制代码。
        self.assertTrue(report["uses_generic_action_layer"])

        # 新增代码+Phase92UniversalComputerUse：确认真实应用安全边界仍然存在；没有它真实桌面控制会缺少授权保护。
        self.assertTrue(report["uses_real_app_safety_boundary"])

        # 新增代码+Phase92UniversalComputerUse：确认接入生产 host adapter；没有它运行时无法连接真实 Windows 桌面桥接能力。
        self.assertTrue(report["uses_production_host_adapter"])

        # 新增代码+Phase92UniversalComputerUse：确认默认不执行真实动作；没有它测试和普通询问可能误操作本机。
        self.assertFalse(report["default_real_actions_enabled"])

    # 新增代码+Phase92UniversalComputerUse：这个测试验证 Phase92 总契约；没有它无法一次性确认安全、隐私、通用架构都达标。
    def test_phase92_contract_tokens_and_safety_gates(self):
        # 新增代码+Phase92UniversalComputerUse：创建临时目录保存契约报告；没有它报告会污染真实运行目录。
        with tempfile.TemporaryDirectory() as temporary_directory:
            # 新增代码+Phase92UniversalComputerUse：运行 Phase92 契约检查；没有它无法产生可审计的阶段验收报告。
            report = run_phase92_universal_windows_computer_use_contract(base_dir=Path(temporary_directory))

        # 新增代码+Phase92UniversalComputerUse：确认契约整体通过；没有它单个字段可能看似正常但整体门禁未满足。
        self.assertTrue(report["passed"])

        # 新增代码+Phase92UniversalComputerUse：确认 ready 标记存在；没有它真实终端验收无法用稳定 token 判断阶段能力。
        self.assertEqual(report["marker"], "PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_READY")

        # 新增代码+Phase92UniversalComputerUse：确认 ok 标记存在；没有它验收脚本无法区分普通日志和成功结果。
        self.assertEqual(report["ok_token"], "PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK")

        # 新增代码+Phase92UniversalComputerUse：确认未授权窗口不会产生低层事件；没有它安全边界可能只是在事后报告失败。
        self.assertTrue(report["unauthorized_window_zero_events"])

        # 新增代码+Phase92UniversalComputerUse：确认目标漂移会阻断动作；没有它鼠标键盘可能落到错误窗口。
        self.assertTrue(report["target_drift_blocks_action"])

        # 新增代码+Phase92UniversalComputerUse：确认原始 prompt 没有进入报告正文；没有它用户隐私会暴露在日志里。
        self.assertTrue(report["raw_text_hidden"])

        # 新增代码+Phase92UniversalComputerUse：确认不扩张无授权动作面；没有它 Phase92 可能绕过既有安全门禁。
        self.assertFalse(report["uncontrolled_actions_expanded"])

    # 新增代码+Phase92UniversalComputerUse：这个测试验证真实 Agent compat 入口能分发 mode；没有它 schema 和归一化通过也可能在 agent 层断开。
    def test_agent_compat_dispatches_mode_without_prompt_leak(self):
        # 新增代码+Phase92UniversalComputerUse：准备一个带隐私标记的 prompt；没有它无法检查 observation 日志是否泄露原文。
        prompt = "phase92-agent-secret 请打开 computer use，准备控制任意普通 Windows 应用。"

        # 修改代码+Phase92UniversalComputerUse：用 __new__ 创建轻量 LearningAgent 对象；没有它测试会启动完整 agent 运行时而变慢。
        agent = LearningAgent.__new__(LearningAgent)

        # 新增代码+Phase92UniversalComputerUse：准备保存 observation 的列表；没有它无法检查 dispatch 审计字段是否脱敏。
        observations = []

        # 新增代码+Phase92UniversalComputerUse：给轻量 Agent 注入 observation 记录函数；没有它 _computer_use_compat 会调用缺失方法。
        agent._record_observation = lambda kind, payload: observations.append((kind, payload))

        # 新增代码+Phase92UniversalComputerUse：调用真实兼容入口；没有它无法证明 operation=mode 在 agent 层可执行。
        output = LearningAgent._computer_use_compat(agent, {"operation": "mode", "prompt": prompt})

        # 新增代码+Phase92UniversalComputerUse：解析 JSON 输出；没有它只能做字符串包含判断，定位失败原因不清楚。
        report = json.loads(output)

        # 新增代码+Phase92UniversalComputerUse：确认 mode 报告成功；没有它后续断言可能建立在错误文本上。
        self.assertTrue(report["ok"])

        # 新增代码+Phase92UniversalComputerUse：确认 Agent 调到了单一通用运行时；没有它可能只是返回了占位文本。
        self.assertTrue(report["single_universal_runtime"])

        # 新增代码+Phase92UniversalComputerUse：把 observations 序列化用于隐私检查；没有它无法一次性扫描嵌套日志。
        serialized_observations = json.dumps(observations, ensure_ascii=False, default=str)

        # 新增代码+Phase92UniversalComputerUse：确认 observation 日志没有 prompt 原文；没有它用户隐私会被兼容层日志破坏。
        self.assertNotIn(prompt, serialized_observations)

        # 新增代码+Phase92UniversalComputerUse：确认 dispatch 日志仍保留 prompt 哈希；没有它排查时无法关联任务。
        self.assertIn("prompt_sha256_16", serialized_observations)


# 新增代码+Phase92UniversalComputerUse：这个入口让单文件测试可以直接运行；没有它排查时需要记住完整 unittest 命令。
if __name__ == "__main__":
    # 新增代码+Phase92UniversalComputerUse：启动 unittest 主程序；没有它直接执行文件不会跑任何测试。
    unittest.main()
