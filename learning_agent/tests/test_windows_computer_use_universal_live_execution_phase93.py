# 新增代码+Phase93UniversalLiveExecutionGate：导入 json 是为了把报告序列化后检查原始 prompt 是否泄露；如果没有这行代码，隐私断言只能靠人工看日志。  # noqa: D100
import json  # 新增代码+Phase93UniversalLiveExecutionGate：使用 JSON 序列化嵌套报告；如果没有这行代码，raw_prompt_hidden 的自动化检查会缺少工具。

# 新增代码+Phase93UniversalLiveExecutionGate：导入 tempfile 是为了给每次测试创建隔离目录；如果没有这行代码，不同测试会互相污染运行证据。  # noqa: E402
import tempfile  # 新增代码+Phase93UniversalLiveExecutionGate：创建临时目录保存合同报告；如果没有这行代码，测试会写入真实 memory 目录。

# 新增代码+Phase93UniversalLiveExecutionGate：导入 unittest 是为了沿用项目现有标准测试框架；如果没有这行代码，python -m unittest 无法发现这些断言。  # noqa: E402
import unittest  # 新增代码+Phase93UniversalLiveExecutionGate：提供测试用例基类和断言方法；如果没有这行代码，测试文件不能运行。

# 新增代码+Phase93UniversalLiveExecutionGate：导入 Path 是为了稳定处理 Windows 路径；如果没有这行代码，临时目录拼接容易出现字符串路径错误。  # noqa: E402
from pathlib import Path  # 新增代码+Phase93UniversalLiveExecutionGate：把临时目录转成 Path 对象；如果没有这行代码，运行时接口的路径类型覆盖不足。

# 新增代码+Phase93UniversalLiveExecutionGate：从包级入口导入 Phase93 类是为了验证其他 agent 可以直接复用；如果没有这行代码，能力可能只藏在内部模块里。  # noqa: E402
from learning_agent.computer_use import UniversalWindowsLiveExecutionGate as PackageUniversalWindowsLiveExecutionGate  # 新增代码+Phase93UniversalLiveExecutionGate：检查 __init__ 导出；如果没有这行代码，包级公开 API 缺少回归保护。

# 新增代码+Phase93UniversalLiveExecutionGate：导入 Phase93 模块入口是为了锁定新阶段应提供的公开能力；如果没有这行代码，测试无法驱动生产模块实现。  # noqa: E402
from learning_agent.computer_use.universal_live_execution import (  # 新增代码+Phase93UniversalLiveExecutionGate：导入待实现的新模块；如果没有这行代码，TDD 红灯不会证明模块缺失。
    UniversalWindowsLiveExecutionGate,  # 新增代码+Phase93UniversalLiveExecutionGate：导入通用真实执行闭环门禁类；如果没有这行代码，无法测试运行时对象。
    phase93_cli_line,  # 新增代码+Phase93UniversalLiveExecutionGate：导入 CLI token 格式化函数；如果没有这行代码，真实终端验收输出没有稳定断言。
    run_phase93_universal_live_execution_gate_contract,  # 新增代码+Phase93UniversalLiveExecutionGate：导入总合同入口；如果没有这行代码，测试不能一次性验证所有门禁。
)  # 新增代码+Phase93UniversalLiveExecutionGate：结束 Phase93 导入列表；如果没有这行代码，Python 语法不完整。


# 新增代码+Phase93UniversalLiveExecutionGate：类段开始，本测试类验证 Phase93 把 Phase92 通用模式升级为统一 live execution gate；如果没有这段测试，后续实现可能退回每个软件一个控制器。  # noqa: E302
class WindowsComputerUseUniversalLiveExecutionPhase93Tests(unittest.TestCase):  # 新增代码+Phase93UniversalLiveExecutionGate：定义 Phase93 测试类；如果没有这行代码，unittest 不会组织这些断言。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，本测试验证 Phase93 合同必须使用一个通用 live loop；如果没有这段函数，架构可能再次被代表性应用带偏。  # noqa: D401
    def test_phase93_contract_uses_single_universal_live_loop(self):  # 新增代码+Phase93UniversalLiveExecutionGate：定义单一通用闭环合同测试；如果没有这行代码，核心成功标准没有自动化保护。
        # 新增代码+Phase93UniversalLiveExecutionGate：创建临时目录保存合同报告；如果没有这行代码，测试运行会污染项目真实 memory 目录。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase93UniversalLiveExecutionGate：使用临时目录上下文；如果没有这行代码，测试证据不会自动清理。
            # 新增代码+Phase93UniversalLiveExecutionGate：运行 Phase93 总合同入口；如果没有这行代码，后续断言没有真实报告来源。
            report = run_phase93_universal_live_execution_gate_contract(base_dir=Path(temporary_directory))  # 新增代码+Phase93UniversalLiveExecutionGate：把临时目录传给合同；如果没有这行代码，报告无法隔离落盘。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认总合同通过；如果没有这行代码，单个字段看似正确也可能整体门禁失败。
        self.assertTrue(report["passed"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言 passed 为真；如果没有这行代码，失败实现可能被误认为可用。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认新阶段 ready token 正确；如果没有这行代码，真实终端场景无法稳定识别阶段。
        self.assertEqual(report["marker"], "PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_READY")  # 新增代码+Phase93UniversalLiveExecutionGate：检查 ready 标记；如果没有这行代码，输出 token 可能漂移。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认新阶段 OK token 正确；如果没有这行代码，验收脚本无法区分普通日志和成功结果。
        self.assertEqual(report["ok_token"], "PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK")  # 新增代码+Phase93UniversalLiveExecutionGate：检查 OK 标记；如果没有这行代码，终端验收可能误判。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认 Phase93 复用 Phase92 通用模式；如果没有这行代码，新门禁可能绕开上一阶段的正确架构。
        self.assertTrue(report["uses_phase92_universal_runtime"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言使用 Phase92 runtime；如果没有这行代码，prompt mode 可能被重复造轮子。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认只有一个通用 live loop；如果没有这行代码，系统可能继续堆专用 app 控制器。
        self.assertTrue(report["single_universal_live_loop"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言单一闭环存在；如果没有这行代码，架构边界没有保护。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认 prompt 会进入 observe-plan-act-verify 流程；如果没有这行代码，用户 prompt 可能只返回静态状态。
        self.assertTrue(report["prompt_to_observe_plan_act_verify"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言 prompt 到闭环路径；如果没有这行代码，真实执行门禁没有闭环证据。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认不需要每个软件一个控制器；如果没有这行代码，用户明确反对的设计可能回归。
        self.assertTrue(report["no_per_app_controller"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言拒绝 per-app controller；如果没有这行代码，代表性应用可能被误当主架构。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认代表性应用只是验收样本；如果没有这行代码，Notepad/Paint 等样本会污染主设计。
        self.assertTrue(report["representative_apps_are_acceptance_only"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言样本只用于验收；如果没有这行代码，架构可能耦合具体应用。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认闭环执行器被接入；如果没有这行代码，Phase93 可能只做状态汇总而没有执行结构。
        self.assertTrue(report["uses_closed_loop_executor"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言接入 Phase68；如果没有这行代码，observe-act-verify 缺少统一引擎。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认通用动作层被接入；如果没有这行代码，真实控制会退回硬编码点击脚本。
        self.assertTrue(report["uses_generic_action_layer"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言接入 Phase70/71；如果没有这行代码，通用控制能力没有证据。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认安全边界被接入；如果没有这行代码，真实软件控制会缺少授权和危险窗口拦截。
        self.assertTrue(report["uses_real_app_safety_boundary"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言接入 Phase72；如果没有这行代码，低层发送前没有安全门。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认生产 host adapter 被接入；如果没有这行代码，Phase93 不能说明已经连接生产级桥接结构。
        self.assertTrue(report["uses_production_host_adapter"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言接入 Phase76-89；如果没有这行代码，生产控制链路缺少锚点。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认真实动作默认关闭；如果没有这行代码，普通测试或普通 prompt 可能误操作本机。
        self.assertTrue(report["real_actions_default_disabled"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言默认不发真实输入；如果没有这行代码，安全默认值没有回归保护。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认未扩张无边界动作；如果没有这行代码，阶段可能被误读为无限控制所有窗口。
        self.assertFalse(report["uncontrolled_actions_expanded"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言没有无控制扩张；如果没有这行代码，安全边界可能被误改。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，本测试到此完成单一通用 live loop 合同验证。

    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，本测试验证三类危险路径必须都是零事件；如果没有这段函数，安全门禁只会停留在口头声明。
    def test_runtime_blocks_unsafe_paths_with_zero_events(self):  # 新增代码+Phase93UniversalLiveExecutionGate：定义安全阻断测试；如果没有这行代码，未授权和漂移路径可能缺少保护。
        # 新增代码+Phase93UniversalLiveExecutionGate：创建临时目录隔离 runtime 状态；如果没有这行代码，授权记录可能互相污染。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase93UniversalLiveExecutionGate：使用临时目录上下文；如果没有这行代码，测试后会留下临时证据。
            # 新增代码+Phase93UniversalLiveExecutionGate：创建 Phase93 runtime；如果没有这行代码，无法直接检查门禁方法。
            runtime = UniversalWindowsLiveExecutionGate(base_dir=Path(temporary_directory))  # 新增代码+Phase93UniversalLiveExecutionGate：把隔离目录注入 runtime；如果没有这行代码，运行时状态不稳定。

            # 新增代码+Phase93UniversalLiveExecutionGate：执行未授权窗口检查；如果没有这行代码，默认拒绝路径没有证据。
            unauthorized = runtime.unauthorized_window_refusal()  # 新增代码+Phase93UniversalLiveExecutionGate：调用未授权拒绝方法；如果没有这行代码，未授权低层事件数无法检查。

            # 新增代码+Phase93UniversalLiveExecutionGate：执行危险窗口检查；如果没有这行代码，终端/安全/登录类窗口可能缺少拒绝证据。
            unsafe = runtime.unsafe_window_refusal()  # 新增代码+Phase93UniversalLiveExecutionGate：调用危险窗口拒绝方法；如果没有这行代码，高风险零事件无法检查。

            # 新增代码+Phase93UniversalLiveExecutionGate：执行目标漂移检查；如果没有这行代码，窗口变化后误发输入的风险没有测试。
            drift = runtime.target_drift_refusal()  # 新增代码+Phase93UniversalLiveExecutionGate：调用目标漂移拒绝方法；如果没有这行代码，漂移零事件无法检查。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认未授权窗口没有低层事件；如果没有这行代码，默认拒绝可能仍然偷偷发送输入。
        self.assertTrue(unauthorized["unauthorized_window_zero_events"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言未授权零事件；如果没有这行代码，授权门禁退化不会被发现。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认危险窗口没有低层事件；如果没有这行代码，终端或登录窗口误操作风险无法被挡住。
        self.assertTrue(unsafe["unsafe_window_zero_events"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言危险窗口零事件；如果没有这行代码，高风险拒绝缺少硬指标。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认目标漂移没有低层事件；如果没有这行代码，焦点切走后仍可能把输入打到错误窗口。
        self.assertTrue(drift["target_drift_zero_events"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言漂移零事件；如果没有这行代码，目标身份门禁没有回归保护。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，本测试到此完成零事件安全路径验证。

    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，本测试验证报告不泄露用户真实 prompt；如果没有这段函数，隐私问题可能在验收 JSON 中长期存在。
    def test_raw_prompt_is_hidden_from_phase93_report(self):  # 新增代码+Phase93UniversalLiveExecutionGate：定义隐私测试；如果没有这行代码，原始 prompt 泄露不会被自动发现。
        # 新增代码+Phase93UniversalLiveExecutionGate：准备一个带秘密标记的真实用户风格 prompt；如果没有这行代码，隐私断言没有可搜索的敏感样本。
        secret_prompt = "phase93-secret-user-prompt 请打开 computer use 控制普通 Windows 软件，但不要泄露这句话。"  # 新增代码+Phase93UniversalLiveExecutionGate：保存测试 prompt；如果没有这行代码，无法检查原文是否进入报告。

        # 新增代码+Phase93UniversalLiveExecutionGate：创建临时目录隔离 runtime 报告；如果没有这行代码，测试报告会污染真实运行目录。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase93UniversalLiveExecutionGate：使用临时目录上下文；如果没有这行代码，测试不会自动清理。
            # 新增代码+Phase93UniversalLiveExecutionGate：创建 runtime 并运行用户 prompt；如果没有这行代码，隐私检查没有真实报告。
            runtime = UniversalWindowsLiveExecutionGate(base_dir=Path(temporary_directory))  # 新增代码+Phase93UniversalLiveExecutionGate：初始化运行时；如果没有这行代码，无法调用 run_prompt。

            # 新增代码+Phase93UniversalLiveExecutionGate：执行安全合同模式的 prompt；如果没有这行代码，prompt 脱敏逻辑不会被覆盖。
            report = runtime.run_prompt(secret_prompt, request_real_actions=False)  # 新增代码+Phase93UniversalLiveExecutionGate：运行 prompt 但不请求真实动作；如果没有这行代码，测试可能误触桌面。

        # 新增代码+Phase93UniversalLiveExecutionGate：序列化报告用于全文扫描；如果没有这行代码，嵌套字段里的泄露可能被漏掉。
        serialized_report = json.dumps(report, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase93UniversalLiveExecutionGate：把报告变成字符串；如果没有这行代码，无法做简单包含检查。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认完整 prompt 没有泄露；如果没有这行代码，用户原文可能进入日志。
        self.assertNotIn(secret_prompt, serialized_report)  # 新增代码+Phase93UniversalLiveExecutionGate：断言完整原文缺失；如果没有这行代码，隐私门禁不完整。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认秘密标记没有泄露；如果没有这行代码，部分原文泄露可能逃过完整字符串检查。
        self.assertNotIn("phase93-secret-user-prompt", serialized_report)  # 新增代码+Phase93UniversalLiveExecutionGate：断言秘密片段缺失；如果没有这行代码，局部泄露无法发现。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认报告明确声明原文隐藏；如果没有这行代码，调用方无法快速理解隐私状态。
        self.assertTrue(report["raw_prompt_hidden"])  # 新增代码+Phase93UniversalLiveExecutionGate：断言隐私标记为真；如果没有这行代码，报告语义不明确。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认报告保留短哈希用于排查；如果没有这行代码，问题复盘会缺少可关联的脱敏线索。
        self.assertIn("prompt_sha256_16", report)  # 新增代码+Phase93UniversalLiveExecutionGate：检查 prompt 哈希字段；如果没有这行代码，隐私和可追踪性不能兼得。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，本测试到此完成 prompt 隐私验证。

    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，本测试验证 CLI 输出包含所有验收 token；如果没有这段函数，真实终端验收会变得脆弱。
    def test_cli_line_contains_phase93_stable_tokens_and_package_export(self):  # 新增代码+Phase93UniversalLiveExecutionGate：定义 CLI 和包导出测试；如果没有这行代码，外部调用入口没有保护。
        # 新增代码+Phase93UniversalLiveExecutionGate：创建临时目录隔离合同报告；如果没有这行代码，CLI 测试会污染项目 memory 目录。
        with tempfile.TemporaryDirectory() as temporary_directory:  # 新增代码+Phase93UniversalLiveExecutionGate：使用临时目录上下文；如果没有这行代码，测试后会留下状态。
            # 新增代码+Phase93UniversalLiveExecutionGate：生成合同报告；如果没有这行代码，CLI 格式化没有输入。
            report = run_phase93_universal_live_execution_gate_contract(base_dir=Path(temporary_directory))  # 新增代码+Phase93UniversalLiveExecutionGate：运行 Phase93 合同；如果没有这行代码，token 断言没有事实来源。

        # 新增代码+Phase93UniversalLiveExecutionGate：格式化 CLI 单行输出；如果没有这行代码，无法检查终端验收文本。
        line = phase93_cli_line(report)  # 新增代码+Phase93UniversalLiveExecutionGate：生成 token 行；如果没有这行代码，验收场景可能只能解析复杂 JSON。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认包级导出和模块类是同一个对象；如果没有这行代码，外部 agent 可能导入不到新能力。
        self.assertIs(PackageUniversalWindowsLiveExecutionGate, UniversalWindowsLiveExecutionGate)  # 新增代码+Phase93UniversalLiveExecutionGate：检查包级 API；如果没有这行代码，公开接口遗漏不会被发现。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认 ready token 在 CLI 行中；如果没有这行代码，真实终端无法快速识别新阶段。
        self.assertIn("PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_READY", line)  # 新增代码+Phase93UniversalLiveExecutionGate：检查 ready 文本；如果没有这行代码，场景匹配可能失败。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认 OK token 在 CLI 行中；如果没有这行代码，验收器无法稳定判断成功。
        self.assertIn("PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK", line)  # 新增代码+Phase93UniversalLiveExecutionGate：检查 OK 文本；如果没有这行代码，验收输出不够明确。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认单一通用闭环 token 在 CLI 行中；如果没有这行代码，用户最关心的架构方向不可见。
        self.assertIn("single_universal_live_loop=true", line)  # 新增代码+Phase93UniversalLiveExecutionGate：检查通用闭环 token；如果没有这行代码，终端输出无法证明主架构。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认无专用控制器 token 在 CLI 行中；如果没有这行代码，后续可能误解为每个软件单独适配。
        self.assertIn("no_per_app_controller=true", line)  # 新增代码+Phase93UniversalLiveExecutionGate：检查反 per-app token；如果没有这行代码，设计边界不够醒目。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认默认真实动作关闭 token 在 CLI 行中；如果没有这行代码，用户可能误以为普通运行会直接操作电脑。
        self.assertIn("real_actions_default_disabled=true", line)  # 新增代码+Phase93UniversalLiveExecutionGate：检查默认安全 token；如果没有这行代码，安全默认值不透明。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认三类拒绝都是零事件；如果没有这行代码，CLI 输出不能证明低层发送被拦住。
        self.assertIn("unauthorized_window_zero_events=true", line)  # 新增代码+Phase93UniversalLiveExecutionGate：检查未授权零事件 token；如果没有这行代码，授权拒绝不透明。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认危险窗口零事件 token 在 CLI 行中；如果没有这行代码，高风险拦截不够明确。
        self.assertIn("unsafe_window_zero_events=true", line)  # 新增代码+Phase93UniversalLiveExecutionGate：检查危险窗口零事件 token；如果没有这行代码，安全拒绝不透明。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认目标漂移零事件 token 在 CLI 行中；如果没有这行代码，目标身份保护不够明确。
        self.assertIn("target_drift_zero_events=true", line)  # 新增代码+Phase93UniversalLiveExecutionGate：检查目标漂移 token；如果没有这行代码，漂移保护不透明。

        # 新增代码+Phase93UniversalLiveExecutionGate：确认没有扩张无控制动作；如果没有这行代码，阶段边界无法从终端一眼看出。
        self.assertIn("uncontrolled_actions_expanded=false", line)  # 新增代码+Phase93UniversalLiveExecutionGate：检查未扩张 token；如果没有这行代码，安全边界容易被误读。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，本测试到此完成 CLI 与导出验证。
# 新增代码+Phase93UniversalLiveExecutionGate：类段结束，Phase93 所有测试断言到此结束。


# 新增代码+Phase93UniversalLiveExecutionGate：文件入口段开始，允许直接运行本测试文件；如果没有这段代码，排查时必须记完整 unittest 命令。
if __name__ == "__main__":  # 新增代码+Phase93UniversalLiveExecutionGate：判断是否直接执行测试文件；如果没有这行代码，直接运行文件不会启动测试。
    # 新增代码+Phase93UniversalLiveExecutionGate：启动 unittest 主程序；如果没有这行代码，直接执行文件没有任何测试输出。
    unittest.main()  # 新增代码+Phase93UniversalLiveExecutionGate：运行当前文件测试；如果没有这行代码，人工排查入口缺失。
# 新增代码+Phase93UniversalLiveExecutionGate：文件入口段结束，直接运行路径到此结束。
