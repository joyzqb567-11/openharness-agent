import io  # 新增代码+FullMaturityMatrix：导入内存文本缓冲区捕获 Phase115 输出；如果没有这一行，测试无法检查一键验收打印的最终 token。
import tempfile  # 新增代码+FullMaturityMatrix：导入临时目录隔离 `/computer` 命令状态；如果没有这一行，测试会污染用户真实 full 模式记录。
import unittest  # 新增代码+FullMaturityMatrix：导入 unittest 测试框架；如果没有这一行，标准测试命令无法发现本文件。
from contextlib import redirect_stdout  # 新增代码+FullMaturityMatrix：导入 stdout 重定向工具；如果没有这一行，测试会把大量验收输出直接刷到控制台。
from pathlib import Path  # 新增代码+FullMaturityMatrix：导入 Path 统一处理 Windows 路径；如果没有这一行，临时 workspace 传参会更脆弱。

from learning_agent.app.interactive import phase115_main, run_computer_terminal_command  # 新增代码+FullMaturityMatrix：导入真实 `/computer` 终端命令入口和最终验收入口；如果没有这一行，测试会绕开用户实际输入路径。
from learning_agent.computer_use.full_maturity_matrix import computer_use_full_maturity_cli_line, run_computer_use_full_maturity_matrix  # 新增代码+FullMaturityMatrix：导入最终成熟矩阵 API；如果没有这一行，红测会证明 Task7 模块尚未实现。


class WindowsComputerUseFullMaturityMatrixTests(unittest.TestCase):  # 新增代码+FullMaturityMatrix：类段开始，集中验收 `/computer use --full` 最终成熟矩阵；如果没有这个类，蓝图 Task7 没有自动化边界。
    def assert_contains_all(self, output: str, expected_parts: list[str]) -> None:  # 新增代码+FullMaturityMatrix：函数段开始，复用多 token 断言；如果没有这段函数，测试会重复大量 assertIn 噪声。
        for expected_part in expected_parts:  # 新增代码+FullMaturityMatrix：逐个检查输出片段；如果没有这一行，测试只会覆盖一个字段而漏掉成熟合同。
            self.assertIn(expected_part, output)  # 新增代码+FullMaturityMatrix：断言当前片段存在；如果没有这一行，缺字段也可能误通过。
    # 新增代码+FullMaturityMatrix：函数段结束，assert_contains_all 到此结束；如果没有这个边界说明，初学者不容易看出断言 helper 范围。

    def _required_tokens(self) -> list[str]:  # 新增代码+FullMaturityMatrix：函数段开始，集中列出最终矩阵必须输出的 token；如果没有这段函数，多个测试的成熟字段容易漂移。
        return ["COMPUTER_USE_FULL_MATURE_READY", "product_contract=true", "generic_discovery=true", "generic_real_launch=true", "verified_window_actions=true", "cleanup_recovery=true", "high_risk_refused=true", "visible_terminal_acceptance=true", "desktop_task_router=true", "natural_language_desktop_tasks_route_to_computer_use=true", "forbidden_script_artifact_route_blocked=true", "owned_window_gui_actions_verified=true", "paint_pikachu_visible_terminal_acceptance=false", "generic_drawing_primitives=true", "desktop_task_recording_mode_acceptance=true", "universal_desktop_execution_loop_connected=true", "universal_real_observation_runtime_connected=true", "controlled_physical_sender_adapter_connected=true", "controlled_physical_backend_reached_in_injected_path=true", "controlled_physical_dispatch_default_off=true", "visual_planner_connected=true", "visual_planner_used_in_universal_loop=true", "visual_planner_mature=false", "real_desktop_execution_loop_available=true", "maturity_known_limit_real_desktop_execution=false", "maturity_known_limit_visual_planner=true", "hardcoded_app_whitelist_required=false", "per_app_patch_required=false", "uncontrolled_actions_expanded=false"]  # 修改代码+VisualPlannerLoop：最终矩阵必须显示真实执行 loop 已放开、视觉规划已接线但尚未成熟；如果没有这一行，用户看不到真实路线和视觉规划边界。
    # 新增代码+FullMaturityMatrix：函数段结束，_required_tokens 到此结束；如果没有这个边界说明，初学者不容易看出最终 token 范围。

    def _required_current_architecture_tokens(self) -> list[str]:  # 新增代码+ModelLoopMaturityMatrix：函数段开始，列出当前主循环 Computer Use 架构事实 token；如果没有这段函数，旧 Paint/Pikachu 字段会继续污染成熟度判断。
        return [  # 新增代码+ModelLoopMaturityMatrix：返回稳定 token 列表供多个测试复用；如果没有这一行，CLI 和结构化报告断言会分散漂移。
            "model_loop_semantic_planning=true",  # 新增代码+ModelLoopMaturityMatrix：要求矩阵证明用户意图由模型主循环规划；如果没有这一行，旧 Python 预分类器可能再次冒充主线。
            "model_loop_tool_schema_visible=true",  # 新增代码+ModelLoopMaturityMatrix：要求矩阵证明模型能看到 Computer Use 工具 schema；如果没有这一行，工具面是否暴露会变成口头判断。
            "model_visible_screenshot_input=true",  # 新增代码+ModelLoopMaturityMatrix：要求矩阵证明截图会以图片块回到模型；如果没有这一行，观察层是否真实进入模型会继续被误判。
            "computer_discover_tool_visible=true",  # 新增代码+ModelLoopMaturityMatrix：要求矩阵证明发现工具在工具清单里；如果没有这一行，ClaudeCode 风格先发现再选择工具的层次不可见。
            "computer_action_launch_app_available=true",  # 新增代码+ModelLoopMaturityMatrix：要求矩阵证明模型能先启动应用；如果没有这一行，画图任务可能退回未打开软件就盲动。
            "computer_action_drag_path_available=true",  # 新增代码+ModelLoopMaturityMatrix：要求矩阵证明模型能表达通用鼠标轨迹；如果没有这一行，任意绘图只能依赖旧专用桥。
            "legacy_paint_fixture_demoted=true",  # 新增代码+ModelLoopMaturityMatrix：要求矩阵明确旧 Paint fixture 已降级；如果没有这一行，后续读者会继续把皮卡丘样例当生产主线。
            "production_main_loop_not_paint_bridge=true",  # 新增代码+ModelLoopMaturityMatrix：要求矩阵证明默认生产 full 路线不是 Paint 专用桥；如果没有这一行，旧记忆会继续误判当前设计。
        ]  # 新增代码+ModelLoopMaturityMatrix：当前架构 token 列表结束；如果没有这一行，Python 列表语法不完整。
    # 新增代码+ModelLoopMaturityMatrix：函数段结束，_required_current_architecture_tokens 到此结束；如果没有这个边界说明，初学者不容易看出新架构 token 范围。

    def _required_layered_acceptance_tokens(self) -> list[str]:  # 新增代码+LayeredMaturityMatrix：函数段开始，列出通用软件 Computer Use 分层验收 token；如果没有这段函数，矩阵会继续把视觉质量缺口误写成整体失败。
        return [  # 新增代码+LayeredMaturityMatrix：返回稳定 token 列表供结构化报告、CLI 和真实终端共同复用；如果没有这一行，分层验收字段容易在多个入口漂移。
            "generic_local_software_scope=true",  # 新增代码+LayeredMaturityMatrix：要求矩阵明确范围是本机所有通用软件；如果没有这一行，后续可能继续把 Paint 当成产品中心。
            "generic_app_control_foundation_ready=true",  # 新增代码+LayeredMaturityMatrix：要求矩阵单独承认通用应用发现、启动、窗口绑定和动作基础；如果没有这一行，视觉质量失败会误伤通用软件控制基础。
            "model_loop_computer_use_foundation_ready=true",  # 新增代码+LayeredMaturityMatrix：要求矩阵单独承认模型主循环、工具 schema 和截图回流基础；如果没有这一行，主循环能力会被旧视觉字段遮住。
            "real_desktop_evidence_gate_defined=true",  # 新增代码+LayeredMaturityMatrix：要求矩阵声明真实桌面证据门禁存在；如果没有这一行，成熟度会退回只看单测或文案。
            "visual_quality_verifier_available=false",  # 新增代码+LayeredMaturityMatrix：要求矩阵诚实声明当前缺少视觉质量裁判；如果没有这一行，用户会误以为 visual_planner_mature=false 是质量评分结果。
            "visual_quality_acceptance_passed=false",  # 新增代码+LayeredMaturityMatrix：要求矩阵把视觉质量验收独立标成未通过；如果没有这一行，最终 passed=false 的原因不透明。
            "visual_correction_acceptance_available=false",  # 新增代码+LayeredMaturityMatrix：要求矩阵声明当前缺少纠偏验收协议；如果没有这一行，agent 不擦除旧图/不重画的问题无法进入顶层门禁。
            "visual_correction_acceptance_passed=false",  # 新增代码+LayeredMaturityMatrix：要求矩阵把纠偏能力独立标成未验收；如果没有这一行，纠偏缺口会被混进视觉 planner 字段。
            "visual_planner_mature_means_quality_gate_only=true",  # 新增代码+LayeredMaturityMatrix：要求矩阵说明 visual_planner_mature 只代表质量门禁；如果没有这一行，后续开发者可能误删已工作的主循环能力。
            "paint_is_representative_visual_sample_only=true",  # 新增代码+LayeredMaturityMatrix：要求矩阵说明 Paint 只是视觉压力样本；如果没有这一行，架构又可能退回画图专用功能。
            "final_maturity_blocked_by_visual_quality_acceptance=true",  # 新增代码+LayeredMaturityMatrix：要求矩阵把最终未成熟原因指向视觉质量验收缺口；如果没有这一行，passed=false 会继续不清楚。
        ]  # 新增代码+LayeredMaturityMatrix：分层验收 token 列表结束；如果没有这一行，Python 列表语法不完整。
    # 新增代码+LayeredMaturityMatrix：函数段结束，_required_layered_acceptance_tokens 到此结束；如果没有这个边界说明，初学者不容易看出分层验收 token 范围。
    def _required_source_architecture_tokens(self) -> list[str]:  # 新增代码+SourceArchitectureMaturity：函数段开始，列出源码架构审计必须在终端展示的 token；如果没有这段函数，源码审计字段容易只存在 JSON 而真实用户看不到。
        return [  # 新增代码+SourceArchitectureMaturity：返回稳定 token 列表给 CLI、命令测试和真实终端场景复用；如果没有这一行，多处断言会重复且容易漏字段。
            "computer_use_source_inventory_available=true",  # 新增代码+SourceArchitectureMaturity：要求矩阵证明已经枚举 computer_use 源码清单；如果没有这一行，用户仍无法确认是否读了全部源码文件。
            "computer_use_all_source_files_parseable=true",  # 新增代码+SourceArchitectureMaturity：要求矩阵证明所有 computer_use Python 文件都能 AST 解析；如果没有这一行，语法坏文件可能被成熟度误忽略。
            "computer_use_source_audit_coverage=true",  # 新增代码+SourceArchitectureMaturity：要求矩阵证明源码审计覆盖了枚举到的所有文件；如果没有这一行，部分文件可能漏审。
            "computer_use_architecture_layers_mapped=true",  # 新增代码+SourceArchitectureMaturity：要求矩阵证明源码已映射到架构层；如果没有这一行，文件清单只能说明数量，不能说明设计结构。
            "computer_use_required_design_layers_present=true",  # 新增代码+SourceArchitectureMaturity：要求矩阵证明必需设计层都有对应源码；如果没有这一行，关键层缺失也可能被忽略。
            "computer_use_main_chain_files_present=true",  # 新增代码+SourceArchitectureMaturity：要求矩阵证明主链路文件存在；如果没有这一行，controller/loop/observer/action 主路径缺文件时不容易暴露。
            "computer_use_legacy_pollution_scan_available=true",  # 新增代码+SourceArchitectureMaturity：要求矩阵证明已扫描历史特例污染风险；如果没有这一行，旧 Paint/Pikachu/Notepad 样例可能再次污染判断。
            "computer_use_uncategorized_source_files_count=0",  # 新增代码+SourceArchitectureMaturity：要求矩阵证明没有未归类源码文件；如果没有这一行，新文件可能游离在架构审计之外。
            "computer_use_source_audit_static_only=true",  # 新增代码+SourceArchitectureMaturity：要求矩阵诚实声明这是静态源码审计；如果没有这一行，用户可能误以为它证明了真实运行质量。
            "computer_use_source_audit_semantic_complete=false",  # 新增代码+SourceArchitectureMaturity：要求矩阵诚实声明不能证明所有语义正确；如果没有这一行，成熟度矩阵会过度承诺。
        ]  # 新增代码+SourceArchitectureMaturity：源码架构审计 token 列表结束；如果没有这一行，Python 列表语法不完整。
    # 新增代码+SourceArchitectureMaturity：函数段结束，_required_source_architecture_tokens 到此结束；如果没有这个边界说明，初学者不容易看出源码审计 token 范围。
    def _required_runtime_reachability_tokens(self) -> list[str]:  # 新增代码+RuntimeReachabilityMaturity：函数段开始，列出运行时可达性审计必须在终端展示的 token；如果没有这段函数，86 个文件会继续被误当成全部核心运行时代码。
        return [  # 新增代码+RuntimeReachabilityMaturity：返回稳定 token 列表给 CLI、命令测试和真实终端场景复用；如果没有这一行，运行时可达性字段容易只留在 JSON 里。
            "computer_use_runtime_reachability_audit_available=true",  # 新增代码+RuntimeReachabilityMaturity：要求矩阵明确提供运行时可达性审计；如果没有这一行，用户无法知道哪些文件真在主链路上。
            "windows_app_inventory_is_primary_model_discover=true",  # 新增代码+RuntimeReachabilityMaturity：要求矩阵证明模型主循环 discover 以 windows_app_inventory 为主；如果没有这一行，generic_app_discovery 可能继续被误认为主入口。
            "generic_app_discovery_is_primary_model_discover=false",  # 新增代码+RuntimeReachabilityMaturity：要求矩阵明确 generic_app_discovery 不是当前主 discover；如果没有这一行，旧 Phase108 记忆会继续污染判断。
            "generic_app_discovery_is_compatibility_wrapper=false", "generic_app_discovery_removed=true",  # 新增代码+RuntimeReachabilityMaturity：要求矩阵说明 generic_app_discovery 是兼容包装；如果没有这一行，后续瘦身可能误删仍被旧命令引用的文件。
            "computer_use_legacy_or_deprecated_risk_file_count=0",  # 新增代码+RuntimeReachabilityMaturity：要求当前静态审计没有发现完全孤立的高风险废弃文件；如果没有这一行，删除建议会缺少事实门禁。
            "computer_use_unknown_reachability_file_count=0",  # 新增代码+RuntimeReachabilityMaturity：要求没有游离在分类体系之外的 computer_use 文件；如果没有这一行，新文件可能绕过核心/历史判断。
            "computer_use_runtime_reachability_static_only=true",  # 新增代码+RuntimeReachabilityMaturity：要求矩阵声明这是静态可达性审计；如果没有这一行，用户可能误以为它等于真实运行覆盖率。
            "computer_use_runtime_reachability_semantic_complete=false",  # 新增代码+RuntimeReachabilityMaturity：要求矩阵声明不能完整证明业务语义；如果没有这一行，审计标准会再次过度承诺。
            "computer_use_runtime_trace_available=true",  # 新增代码+RuntimeTrace：要求矩阵显示 runtime trace 能力已存在；如果没有这一行，用户无法从终端确认主循环证据链已接线。
            "computer_use_runtime_trace_model_loop_hooks_present=true",  # 新增代码+RuntimeTrace：要求矩阵显示模型请求阶段 trace hook 已接；如果没有这一行，schema 可见性证据可能再次缺失。
            "computer_use_runtime_trace_tool_call_hooks_present=true",  # 新增代码+RuntimeTrace：要求矩阵显示工具调用阶段 trace hook 已接；如果没有这一行，模型实际选工具的证据可能再次缺失。
            "computer_use_runtime_trace_tool_result_hooks_present=true",  # 新增代码+RuntimeTrace：要求矩阵显示工具结果阶段 trace hook 已接；如果没有这一行，结果回流模型的证据可能再次缺失。
            "computer_use_runtime_trace_tool_internal_hooks_present=true",  # 新增代码+RuntimeTrace：要求矩阵显示 Computer Use 工具内部 trace hook 已接；如果没有这一行，discover/observe/action 内部路径仍会不透明。
            "computer_use_runtime_trace_regression_test_present=true",  # 新增代码+RuntimeTrace：要求矩阵显示 runtime trace 回归测试存在；如果没有这一行，后续改坏 trace 不容易被测试发现。
            "computer_use_runtime_trace_static_only=true",  # 新增代码+RuntimeTrace：要求矩阵声明 trace 架构报告是静态接线检查；如果没有这一行，用户可能误以为它证明真实任务质量。
            "computer_use_runtime_trace_semantic_complete=false",  # 新增代码+RuntimeTrace：要求矩阵声明 trace 接线不完整证明语义成功；如果没有这一行，成熟度会过度承诺。
        ]  # 新增代码+RuntimeReachabilityMaturity：运行时可达性 token 列表结束；如果没有这一行，Python 列表语法不完整。
    # 新增代码+RuntimeReachabilityMaturity：函数段结束，_required_runtime_reachability_tokens 到此结束；如果没有这个边界说明，初学者不容易看出运行时可达性 token 范围。

    def test_full_maturity_matrix_reports_required_fields(self) -> None:  # 新增代码+FullMaturityMatrix：函数段开始，验证结构化矩阵和 CLI 行都包含蓝图最终字段；如果没有这段测试，矩阵可能只输出部分阶段事实。
        report = run_computer_use_full_maturity_matrix()  # 新增代码+FullMaturityMatrix：运行最终成熟矩阵；如果没有这一行，断言没有结构化来源。
        cli_line = computer_use_full_maturity_cli_line(report)  # 新增代码+FullMaturityMatrix：把矩阵转成真实终端 token 行；如果没有这一行，场景验收不能复用稳定格式。
        self.assertFalse(report["passed"])  # 修改代码+UniversalLoopSlimming：断言瘦身后矩阵整体不能再宣称成熟通过；如果没有这一行，旧 OK token 会继续误导用户。
        self.assertTrue(report["product_contract"])  # 新增代码+FullMaturityMatrix：断言产品契约已冻结；如果没有这一行，full 模式边界可能再次漂移。
        self.assertTrue(report["generic_discovery"])  # 新增代码+FullMaturityMatrix：断言通用发现已就绪；如果没有这一行，项目可能退回逐应用白名单。
        self.assertTrue(report["generic_real_launch"])  # 新增代码+FullMaturityMatrix：断言通用启动后端已就绪；如果没有这一行，launch 能力可能停在候选层。
        self.assertTrue(report["verified_window_actions"])  # 新增代码+FullMaturityMatrix：断言动作需要 verified window；如果没有这一行，动作可能落到漂移窗口。
        self.assertTrue(report["cleanup_recovery"])  # 新增代码+FullMaturityMatrix：断言清理恢复已就绪；如果没有这一行，真实启动后可能留下残留进程。
        self.assertTrue(report["high_risk_refused"])  # 新增代码+FullMaturityMatrix：断言高风险目标仍拒绝；如果没有这一行，full 可能被误解成无限权限。
        self.assertTrue(report["visible_terminal_acceptance"])  # 新增代码+FullMaturityMatrix：断言最终可见终端验收项进入矩阵；如果没有这一行，自动测试可能被误当最终交付。
        self.assertTrue(report["desktop_task_router"])  # 新增代码+Task8Maturity：断言自然语言桌面任务路由已进入最终矩阵；如果没有这一行，矩阵可能不承认刚修复的根因链路。
        self.assertTrue(report["natural_language_desktop_tasks_route_to_computer_use"])  # 新增代码+Task8Maturity：断言自然语言桌面任务会走 Computer Use；如果没有这一行，用户输入皮卡丘任务仍可能被脚本路线截走。
        self.assertTrue(report["forbidden_script_artifact_route_blocked"])  # 新增代码+Task8Maturity：断言禁止脚本成品路线仍被阻断；如果没有这一行，系统可能退回“生成图片文件”的治标方案。
        self.assertTrue(report["owned_window_gui_actions_verified"])  # 新增代码+Task8Maturity：断言 GUI 动作绑定到已验证窗口；如果没有这一行，动作计数可能不是来自受控 Computer Use 窗口链。
        self.assertFalse(report["paint_pikachu_visible_terminal_acceptance"])  # 修改代码+UniversalLoopSlimming：断言 Paint/Pikachu 验收不能再算生产成熟证据；如果没有这一行，代表样例会继续冒充通用能力。
        self.assertTrue(report["generic_drawing_primitives"])  # 新增代码+Task8Maturity：断言通用拖拽绘图 primitive 已入矩阵；如果没有这一行，画图能力会继续依赖固定脚本或单场景证据。
        self.assertTrue(report["desktop_task_recording_mode_acceptance"])  # 新增代码+Task8Maturity：断言当前成熟范围是 recording-mode 桌面任务验收；如果没有这一行，用户分不清可验收能力和真实执行能力。
        self.assertTrue(report["universal_desktop_execution_loop_connected"])  # 新增代码+UniversalDesktopAdapter：断言默认生产路径已接入通用桌面 adapter；如果没有这一行，矩阵无法证明本阶段不是空 loop。
        self.assertTrue(report["universal_real_observation_runtime_connected"])  # 新增代码+RealObservationAdapter：断言默认生产路径已接入真实只读 observation runtime；如果没有这一行，矩阵无法证明本阶段已经补上真实观察层。
        self.assertTrue(report["controlled_physical_sender_adapter_connected"])  # 新增代码+ControlledPhysicalAdapter：断言受控物理 sender 已接到 adapter 可配置入口；如果没有这一行，Phase95 仍可能只是孤立模块。
        self.assertTrue(report["controlled_physical_backend_reached_in_injected_path"])  # 新增代码+ControlledPhysicalAdapter：断言注入路径能把事件送到 fake 后端；如果没有这一行，接线可能只是构造参数。
        self.assertTrue(report["controlled_physical_dispatch_default_off"])  # 新增代码+ControlledPhysicalAdapter：断言真实物理派发默认仍关闭；如果没有这一行，安全边界可能被误放开。
        self.assertTrue(report["visual_planner_connected"])  # 新增代码+VisualPlannerLoop：断言视觉规划器已经接到通用 loop；如果没有这一行，maturity 可能继续只报告静态动作复制器。
        self.assertTrue(report["visual_planner_used_in_universal_loop"])  # 新增代码+VisualPlannerLoop：断言矩阵样本实际用过视觉规划器；如果没有这一行，接线字段可能只是静态声明。
        self.assertFalse(report["visual_planner_mature"])  # 新增代码+VisualPlannerLoop：断言当前视觉规划器还不能冒充成熟任意绘图能力；如果没有这一行，用户会被过度承诺误导。
        self.assertTrue(report["real_desktop_execution_loop_available"])  # 修改代码+VisualPlannerLoop：断言真实桌面执行 loop 已放开可用；如果没有这一行，maturity 会继续把真实路线锁在 false。
        self.assertFalse(report["maturity_known_limit_real_desktop_execution"])  # 修改代码+VisualPlannerLoop：断言真实执行不再是本轮已知限制；如果没有这一行，报告会继续停在保守旧状态。
        self.assertTrue(report["maturity_known_limit_visual_planner"])  # 新增代码+VisualPlannerLoop：断言新的诚实限制转移到视觉规划成熟度；如果没有这一行，项目会把“已接线”和“已成熟”混在一起。
        self.assertFalse(report["hardcoded_app_whitelist_required"])  # 新增代码+FullMaturityMatrix：断言不需要硬编码应用白名单；如果没有这一行，用户指出的设计问题会复发。
        self.assertFalse(report["per_app_patch_required"])  # 新增代码+FullMaturityMatrix：断言不需要逐应用补丁；如果没有这一行，项目会继续无止境堆 phase。
        self.assertFalse(report["uncontrolled_actions_expanded"])  # 新增代码+FullMaturityMatrix：断言没有扩张未受控动作面；如果没有这一行，安全边界可能被误放宽。
        self.assertTrue(report["model_loop_semantic_planning"])  # 新增代码+ModelLoopMaturityMatrix：断言当前 full 语义规划在模型主循环；如果没有这一行，旧分类器抢跑问题会被矩阵漏报。
        self.assertTrue(report["model_loop_tool_schema_visible"])  # 新增代码+ModelLoopMaturityMatrix：断言模型主循环能看到 Computer Use 工具 schema；如果没有这一行，工具注册层是否接通不可见。
        self.assertTrue(report["model_visible_screenshot_input"])  # 新增代码+ModelLoopMaturityMatrix：断言真实截图可以作为图片输入回到模型；如果没有这一行，视觉观察是否进模型会继续靠猜。
        self.assertTrue(report["computer_discover_tool_visible"])  # 新增代码+ModelLoopMaturityMatrix：断言应用发现工具在模型工具面中；如果没有这一行，模型只能继续猜 app 名。
        self.assertTrue(report["computer_action_launch_app_available"])  # 新增代码+ModelLoopMaturityMatrix：断言模型能通过工具启动本机软件；如果没有这一行，full 模式会缺少第 0 步启动能力。
        self.assertTrue(report["computer_action_drag_path_available"])  # 新增代码+ModelLoopMaturityMatrix：断言模型能通过通用 drag_path 画线；如果没有这一行，任意绘图能力会被专用桥污染。
        self.assertTrue(report["legacy_paint_fixture_demoted"])  # 新增代码+ModelLoopMaturityMatrix：断言旧 Paint/Pikachu fixture 已降级；如果没有这一行，旧验收样例会继续冒充当前生产能力。
        self.assertTrue(report["production_main_loop_not_paint_bridge"])  # 新增代码+ModelLoopMaturityMatrix：断言默认生产主循环不走 Paint 专用桥；如果没有这一行，矩阵仍会误导后续判断。
        self.assertTrue(report["generic_local_software_scope"])  # 新增代码+LayeredMaturityMatrix：断言矩阵范围是本机所有通用软件；如果没有这一行，成熟度可能继续围绕 Paint 单点设计。
        self.assertTrue(report["generic_app_control_foundation_ready"])  # 新增代码+LayeredMaturityMatrix：断言通用软件控制基础独立通过；如果没有这一行，视觉质量缺口可能误伤应用发现和窗口控制结论。
        self.assertTrue(report["model_loop_computer_use_foundation_ready"])  # 新增代码+LayeredMaturityMatrix：断言模型主循环 Computer Use 基础独立通过；如果没有这一行，模型语义规划和图片回流会被旧字段遮住。
        self.assertTrue(report["real_desktop_evidence_gate_defined"])  # 新增代码+LayeredMaturityMatrix：断言真实桌面证据门禁已经定义；如果没有这一行，矩阵可能退回只靠单测判断成熟。
        self.assertFalse(report["visual_quality_verifier_available"])  # 新增代码+LayeredMaturityMatrix：断言视觉质量裁判目前不存在；如果没有这一行，用户会误以为已有树/猫/水果拼盘质量评分。
        self.assertFalse(report["visual_quality_acceptance_passed"])  # 新增代码+LayeredMaturityMatrix：断言视觉质量验收目前未通过；如果没有这一行，最终不成熟原因会继续模糊。
        self.assertFalse(report["visual_correction_acceptance_available"])  # 新增代码+LayeredMaturityMatrix：断言纠偏验收协议目前不存在；如果没有这一行，旧图残留和不擦除问题不会进入顶层门禁。
        self.assertFalse(report["visual_correction_acceptance_passed"])  # 新增代码+LayeredMaturityMatrix：断言纠偏验收目前未通过；如果没有这一行，纠偏缺口会被误写成普通视觉 planner 缺口。
        self.assertTrue(report["visual_planner_mature_means_quality_gate_only"])  # 新增代码+LayeredMaturityMatrix：断言 visual_planner_mature 只代表质量门禁；如果没有这一行，开发者可能据此错误改坏主循环。
        self.assertTrue(report["paint_is_representative_visual_sample_only"])  # 新增代码+LayeredMaturityMatrix：断言 Paint 只是代表性视觉样本；如果没有这一行，Computer Use 会被误设计成画图功能。
        self.assertTrue(report["final_maturity_blocked_by_visual_quality_acceptance"])  # 新增代码+LayeredMaturityMatrix：断言最终不成熟被视觉质量验收阻塞；如果没有这一行，passed=false 的主因不透明。
        self.assertTrue(report["computer_use_source_inventory_available"])  # 新增代码+SourceArchitectureMaturity：断言 maturity 矩阵会枚举 computer_use 源码清单；如果没有这一行，后续判断仍可能只靠旧记忆。
        self.assertGreater(report["computer_use_source_file_count"], 50)  # 新增代码+SourceArchitectureMaturity：断言源码清单覆盖当前大量 computer_use 文件；如果没有这一行，只审计少数入口文件也可能误通过。
        self.assertTrue(report["computer_use_all_source_files_parseable"])  # 新增代码+SourceArchitectureMaturity：断言所有 computer_use 源码都能被 AST 解析；如果没有这一行，语法错误文件不会进入顶层门禁。
        self.assertTrue(report["computer_use_source_audit_coverage"])  # 新增代码+SourceArchitectureMaturity：断言审计记录数量和源码文件数量一致；如果没有这一行，漏读文件不会被发现。
        self.assertTrue(report["computer_use_architecture_layers_mapped"])  # 新增代码+SourceArchitectureMaturity：断言源码文件已映射到设计层；如果没有这一行，矩阵无法检查整体结构。
        self.assertTrue(report["computer_use_required_design_layers_present"])  # 新增代码+SourceArchitectureMaturity：断言必需设计层都存在；如果没有这一行，缺少 observation/action/session 等层也可能不报错。
        self.assertTrue(report["computer_use_main_chain_files_present"])  # 新增代码+SourceArchitectureMaturity：断言通用 Computer Use 主链路文件都存在；如果没有这一行，核心路径缺文件时不容易暴露。
        self.assertTrue(report["computer_use_legacy_pollution_scan_available"])  # 新增代码+SourceArchitectureMaturity：断言矩阵提供历史特例污染扫描；如果没有这一行，旧样例文件会继续制造误判风险。
        self.assertEqual(0, report["computer_use_uncategorized_source_files_count"])  # 新增代码+SourceArchitectureMaturity：断言没有未归类源码文件；如果没有这一行，新文件可以绕过架构分层审计。
        self.assertTrue(report["computer_use_source_audit_static_only"])  # 新增代码+SourceArchitectureMaturity：断言矩阵标明这是静态审计；如果没有这一行，报告容易被过度解读。
        self.assertFalse(report["computer_use_source_audit_semantic_complete"])  # 新增代码+SourceArchitectureMaturity：断言矩阵不冒充完整语义证明；如果没有这一行，验收标准会过度承诺。
        self.assertTrue(report["computer_use_runtime_reachability_audit_available"])  # 新增代码+RuntimeReachabilityMaturity：断言矩阵已经提供运行时可达性审计；如果没有这一行，86 个文件仍会被误读为全部核心。
        self.assertTrue(report["windows_app_inventory_is_primary_model_discover"])  # 新增代码+RuntimeReachabilityMaturity：断言当前主循环 discover 入口是 windows_app_inventory；如果没有这一行，应用发现主入口会继续不清楚。
        self.assertFalse(report["generic_app_discovery_is_primary_model_discover"])  # 新增代码+RuntimeReachabilityMaturity：断言 generic_app_discovery 不是当前主循环 discover；如果没有这一行，旧兼容层可能再次被接成主入口。
        self.assertFalse(report["generic_app_discovery_is_compatibility_wrapper"])
        self.assertTrue(report["generic_app_discovery_removed"])  # 新增代码+RuntimeReachabilityMaturity：断言 generic_app_discovery 仍是兼容包装；如果没有这一行，瘦身时可能误删旧命令依赖。
        self.assertGreater(report["computer_use_active_runtime_core_file_count"], 10)  # 新增代码+RuntimeReachabilityMaturity：断言核心运行时文件数量不是空壳；如果没有这一行，审计可能只返回几个手写 token。
        self.assertGreater(report["computer_use_representative_sample_file_count"], 0)  # 新增代码+RuntimeReachabilityMaturity：断言代表样例文件被单独识别；如果没有这一行，Paint/Notepad 样例会继续污染核心判断。
        self.assertEqual(0, report["computer_use_legacy_or_deprecated_risk_file_count"])  # 新增代码+RuntimeReachabilityMaturity：断言当前没有静态证据支持立即删除的孤立高风险文件；如果没有这一行，删除建议可能变成拍脑袋。
        self.assertEqual(0, report["computer_use_unknown_reachability_file_count"])  # 新增代码+RuntimeReachabilityMaturity：断言没有未知可达性文件；如果没有这一行，新增或遗漏文件会继续漂在矩阵之外。
        self.assertTrue(report["computer_use_runtime_reachability_static_only"])  # 新增代码+RuntimeReachabilityMaturity：断言运行时可达性审计边界是静态；如果没有这一行，用户会误以为它证明真实执行质量。
        self.assertFalse(report["computer_use_runtime_reachability_semantic_complete"])  # 新增代码+RuntimeReachabilityMaturity：断言运行时可达性审计不冒充完整语义证明；如果没有这一行，矩阵可能过度承诺。
        self.assertTrue(report["computer_use_runtime_trace_available"])  # 新增代码+RuntimeTrace：断言 runtime trace 能力已进入顶层矩阵；如果没有这一行，新增 trace 可能只存在于代码里而不被 maturity 监管。
        self.assertTrue(report["computer_use_runtime_trace_model_loop_hooks_present"])  # 新增代码+RuntimeTrace：断言模型请求阶段 hook 被矩阵识别；如果没有这一行，schema 可见性证据缺失不会报警。
        self.assertTrue(report["computer_use_runtime_trace_tool_call_hooks_present"])  # 新增代码+RuntimeTrace：断言工具调用阶段 hook 被矩阵识别；如果没有这一行，模型是否调用工具仍可能靠猜。
        self.assertTrue(report["computer_use_runtime_trace_tool_result_hooks_present"])  # 新增代码+RuntimeTrace：断言工具结果阶段 hook 被矩阵识别；如果没有这一行，结果是否回流模型仍可能靠猜。
        self.assertTrue(report["computer_use_runtime_trace_tool_internal_hooks_present"])  # 新增代码+RuntimeTrace：断言工具内部 hook 被矩阵识别；如果没有这一行，discover/observe/action 内部路径仍不可查。
        self.assertTrue(report["computer_use_runtime_trace_regression_test_present"])  # 新增代码+RuntimeTrace：断言 runtime trace 回归测试存在；如果没有这一行，后续删除测试也不容易发现。
        self.assertTrue(report["computer_use_runtime_trace_static_only"])  # 新增代码+RuntimeTrace：断言 trace 架构报告边界是静态；如果没有这一行，矩阵可能过度承诺真实任务质量。
        self.assertFalse(report["computer_use_runtime_trace_semantic_complete"])  # 新增代码+RuntimeTrace：断言 trace 接线不冒充完整语义证明；如果没有这一行，用户可能误以为 trace 等于任务成熟。
        source_audit_report = report["reports"]["computer_use_source_architecture_audit"]  # 新增代码+SourceArchitectureMaturity：读取源码架构审计子报告；如果没有这一行，测试只能看到扁平 token 而不能验证结构细节。
        self.assertEqual(report["computer_use_source_file_count"], source_audit_report["source_file_count"])  # 新增代码+SourceArchitectureMaturity：断言顶层数量和子报告数量一致；如果没有这一行，CLI 和 JSON 可能互相漂移。
        self.assertIn("app_discovery", source_audit_report["layer_counts"])  # 新增代码+SourceArchitectureMaturity：断言应用发现层被识别；如果没有这一行，ClaudeCode 风格清单/发现层可能漏入其他分类。
        self.assertIn("observation", source_audit_report["layer_counts"])  # 新增代码+SourceArchitectureMaturity：断言观察层被识别；如果没有这一行，截图/UIA/观察链路缺失不容易暴露。
        self.assertIn("action_dispatch", source_audit_report["layer_counts"])  # 新增代码+SourceArchitectureMaturity：断言动作派发层被识别；如果没有这一行，鼠标键盘控制链路缺失不容易暴露。
        self.assertIn("execution_loop", source_audit_report["layer_counts"])  # 新增代码+SourceArchitectureMaturity：断言 observe-plan-act 执行循环层被识别；如果没有这一行，顶层 loop 缺失可能被忽略。
        self.assertFalse(source_audit_report["semantic_complete"])  # 新增代码+SourceArchitectureMaturity：断言子报告也明确不做完整语义证明；如果没有这一行，子报告和顶层边界可能不一致。
        reachability_report = report["reports"]["computer_use_runtime_reachability_audit"]  # 新增代码+RuntimeReachabilityMaturity：读取运行时可达性审计子报告；如果没有这一行，测试无法验证核心/兼容/样例分类细节。
        runtime_trace_report = report["reports"]["computer_use_runtime_trace_architecture"]  # 新增代码+RuntimeTrace：读取 runtime trace 架构子报告；如果没有这一行，测试只能看顶层 token 而不能验证子报告细节。
        self.assertIn("windows_app_inventory.py", reachability_report["categories"]["active_runtime_core"])  # 新增代码+RuntimeReachabilityMaturity：断言主 discover 清单文件属于核心运行时；如果没有这一行，模型主循环应用发现事实无法被锁住。
        self.assertNotIn("generic_app_discovery.py", reachability_report["categories"]["compatibility_wrapper"])
        self.assertTrue(reachability_report["generic_app_discovery_removed"])  # 新增代码+RuntimeReachabilityMaturity：断言旧 generic_app_discovery 被归为兼容包装；如果没有这一行，用户指出的误判无法形成长期门禁。
        self.assertIn("paint_pikachu_real_loop.py", reachability_report["categories"]["representative_sample"])  # 新增代码+RuntimeReachabilityMaturity：断言 Paint/Pikachu 特例被归为代表样例；如果没有这一行，旧绘图样例会继续被当生产主线。
        self.assertEqual([], reachability_report["categories"]["legacy_or_deprecated_risk"])  # 新增代码+RuntimeReachabilityMaturity：断言当前没有可直接删除的孤立废弃风险文件；如果没有这一行，瘦身删除清单会缺少证据。
        self.assertTrue(runtime_trace_report["passed"])  # 新增代码+RuntimeTrace：断言 runtime trace 架构子报告通过；如果没有这一行，顶层字段和子报告可能不一致。
        self.assertFalse(runtime_trace_report["semantic_complete"])  # 新增代码+RuntimeTrace：断言子报告不冒充语义完整证明；如果没有这一行，trace 接线可能被误读成成熟质量验收。
        visible_report = report["reports"]["paint_pikachu_visible_terminal_acceptance"]  # 修改代码+UniversalLoopSlimming：读取降级后的 Paint/Pikachu 验收子报告；如果没有这一行，测试无法确认它已从生产成熟证据中移除。
        self.assertTrue(visible_report["legacy_acceptance_fixture"])  # 新增代码+UniversalLoopSlimming：断言旧 Paint/Pikachu 证据只作为 legacy fixture 展示；如果没有这一行，后续读者可能误以为它仍是生产主线。
        self.assertFalse(visible_report["production_maturity_evidence"])  # 新增代码+UniversalLoopSlimming：断言旧 Paint/Pikachu 证据不是生产成熟证据；如果没有这一行，成熟矩阵可能继续被代表样例污染。
        self.assert_contains_all(cli_line, self._required_tokens())  # 新增代码+FullMaturityMatrix：断言 CLI 行包含所有最终 token；如果没有这一行，真实终端验收可能漏字段。
        self.assert_contains_all(cli_line, self._required_current_architecture_tokens())  # 新增代码+ModelLoopMaturityMatrix：断言 CLI 行包含当前主循环架构 token；如果没有这一行，真实终端仍会显示旧矩阵口径。
        self.assert_contains_all(cli_line, self._required_layered_acceptance_tokens())  # 新增代码+LayeredMaturityMatrix：断言 CLI 行包含分层验收 token；如果没有这一行，真实终端仍可能把视觉质量缺口误读成整体失败。
        self.assert_contains_all(cli_line, self._required_source_architecture_tokens())  # 新增代码+SourceArchitectureMaturity：断言 CLI 行包含源码架构审计 token；如果没有这一行，真实终端用户看不到是否全量读源码。
        self.assert_contains_all(cli_line, self._required_runtime_reachability_tokens())  # 新增代码+RuntimeReachabilityMaturity：断言 CLI 行包含运行时可达性 token；如果没有这一行，真实终端用户看不到哪些文件是核心或历史包袱。
        self.assertNotIn("COMPUTER_USE_FULL_MATURE_OK", cli_line)  # 新增代码+UniversalLoopSlimming：断言失败矩阵不输出 OK token；如果没有这一行，未成熟状态可能被自动验收误判通过。
    # 新增代码+FullMaturityMatrix：函数段结束，test_full_maturity_matrix_reports_required_fields 到此结束；如果没有这个边界说明，初学者不容易看出矩阵字段测试范围。

    def test_computer_maturity_command_prints_matrix_without_desktop_touch(self) -> None:  # 新增代码+FullMaturityMatrix：函数段开始，验证 `/computer maturity` 只读输出最终矩阵；如果没有这段测试，用户无法直接查看蓝图收敛结果。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+FullMaturityMatrix：创建临时 workspace 隔离状态；如果没有这一行，maturity 命令会写入真实项目 memory。
            output = run_computer_terminal_command(Path(temp_dir), "/computer maturity")  # 新增代码+FullMaturityMatrix：执行用户会输入的最终成熟矩阵命令；如果没有这一行，测试无法覆盖真实交互入口。
        self.assert_contains_all(output, self._required_tokens())  # 新增代码+FullMaturityMatrix：断言 maturity 输出包含所有最终 token；如果没有这一行，命令可能漏掉关键成熟字段。
        self.assert_contains_all(output, self._required_current_architecture_tokens())  # 新增代码+ModelLoopMaturityMatrix：断言 maturity 命令显示当前主循环架构事实；如果没有这一行，用户仍会被旧字段误导。
        self.assert_contains_all(output, self._required_layered_acceptance_tokens())  # 新增代码+LayeredMaturityMatrix：断言 maturity 命令显示分层验收事实；如果没有这一行，用户仍看不清通用软件能力与视觉质量缺口的边界。
        self.assert_contains_all(output, self._required_source_architecture_tokens())  # 新增代码+SourceArchitectureMaturity：断言 maturity 命令显示源码架构审计事实；如果没有这一行，命令输出无法回应用户“是否读了所有源码”的担心。
        self.assert_contains_all(output, self._required_runtime_reachability_tokens())  # 新增代码+RuntimeReachabilityMaturity：断言 maturity 命令显示运行时可达性事实；如果没有这一行，用户无法从终端区分核心文件和历史包袱。
        self.assert_contains_all(output, ["real_desktop_touched=false", "low_level_event_count=0"])  # 新增代码+FullMaturityMatrix：断言矩阵查询不碰真实桌面；如果没有这一行，只读状态命令可能引入副作用。
    # 新增代码+FullMaturityMatrix：函数段结束，test_computer_maturity_command_prints_matrix_without_desktop_touch 到此结束；如果没有这个边界说明，初学者不容易看出 maturity 命令测试范围。

    def test_computer_use_full_opens_without_token_and_keeps_no_desktop_side_effect(self) -> None:  # 修改代码+FullNaturalUserFlow：函数段开始，验证 `/computer use --full` 直接打开 full 且申请阶段不碰桌面；如果没有这段测试，用户路径可能退回 token 申请或误触真实桌面。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+FullMaturityMatrix：创建临时 workspace 隔离 pending token；如果没有这一行，full 请求会污染真实状态。
            output = run_computer_terminal_command(Path(temp_dir), "/computer use --full")  # 修改代码+FullNaturalUserFlow：执行真实用户会输入的一行 full 命令；如果没有这一行，测试无法覆盖用户入口。
        self.assert_contains_all(output, ["Computer Use Mode", "mode=full", "full_mode=true", "opened=true"])  # 修改代码+FullNaturalUserFlow：断言 full 命令直接打开授权状态；如果没有这一行，旧申请面板可能误通过。
        self.assertNotIn("confirmation_token=", output)  # 新增代码+FullNaturalUserFlow：断言输出不再要求动态 token；如果没有这一行，非真实用户流程可能回归。
        self.assertNotIn("/computer use --full-confirm", output)  # 新增代码+FullNaturalUserFlow：断言输出不再引导 full-confirm；如果没有这一行，新手用户仍会被旧说明误导。
        self.assert_contains_all(output, ["real_desktop_touched=false", "low_level_event_count=0"])  # 修改代码+FullNaturalUserFlow：断言开启权限本身不触碰真实桌面；如果没有这一行，申请权限可能产生副作用。
    # 修改代码+FullNaturalUserFlow：函数段结束，test_computer_use_full_opens_without_token_and_keeps_no_desktop_side_effect 到此结束；如果没有这个边界说明，初学者不容易看出自然 full 命令测试范围。

    def test_phase115_main_runs_final_command_sequence(self) -> None:  # 新增代码+FullMaturityMatrix：函数段开始，验证最终可见终端入口会跑完整命令序列并打印成熟 token；如果没有这段测试，场景可能只看矩阵不跑 launch/refusal/stop。
        buffer = io.StringIO()  # 新增代码+FullMaturityMatrix：创建输出缓冲区；如果没有这一行，测试无法读取 phase115_main 打印内容。
        with redirect_stdout(buffer):  # 新增代码+FullMaturityMatrix：捕获 phase115_main 的打印输出；如果没有这一行，断言只能依赖退出码。
            exit_code = phase115_main([])  # 新增代码+FullMaturityMatrix：运行最终验收入口；如果没有这一行，测试无法覆盖 controller 将要调用的函数。
        output = buffer.getvalue()  # 新增代码+FullMaturityMatrix：读取捕获输出；如果没有这一行，后续 token 断言没有文本来源。
        self.assertEqual(0, exit_code)  # 新增代码+FullMaturityMatrix：断言最终入口返回成功；如果没有这一行，打印 token 但退出失败也会被忽略。
        self.assert_contains_all(output, self._required_tokens())  # 修改代码+UniversalLoopSlimming：断言最终入口输出未成熟但可审计的矩阵 token；如果没有这一行，Task8 最终 answer 可能缺核心字段。
        self.assert_contains_all(output, self._required_current_architecture_tokens())  # 新增代码+ModelLoopMaturityMatrix：断言最终入口输出当前主循环架构 token；如果没有这一行，可见终端验收仍会停留在旧口径。
        self.assert_contains_all(output, self._required_layered_acceptance_tokens())  # 新增代码+LayeredMaturityMatrix：断言最终入口输出分层验收 token；如果没有这一行，最终验收仍不能解释为什么还没完全成熟。
        self.assert_contains_all(output, self._required_source_architecture_tokens())  # 新增代码+SourceArchitectureMaturity：断言最终入口输出源码架构审计 token；如果没有这一行，真实可见终端验收不会覆盖全量源码审计层。
        self.assert_contains_all(output, self._required_runtime_reachability_tokens())  # 新增代码+RuntimeReachabilityMaturity：断言最终入口输出运行时可达性 token；如果没有这一行，真实可见终端验收不会覆盖核心/历史分类。
        self.assert_contains_all(output, ["Computer Use Full Maturity", "WINDOWS_APP_LAUNCH_TARGET_READY", "high_risk_refused=true", "Computer Use Stop", "stopped=true", "real_desktop_touched=false", "low_level_event_count=0"])  # 修改代码+CompatSlimming：断言完整命令序列覆盖 maturity、统一 resolver 普通 app、高风险拒绝和 stop；如果没有这一行，最终验收可能只测了一个命令。
    # 新增代码+FullMaturityMatrix：函数段结束，test_phase115_main_runs_final_command_sequence 到此结束；如果没有这个边界说明，初学者不容易看出最终入口测试范围。
# 新增代码+FullMaturityMatrix：类段结束，WindowsComputerUseFullMaturityMatrixTests 到此结束；如果没有这个边界说明，初学者不容易看出 Task7 测试集合范围。


if __name__ == "__main__":  # 新增代码+FullMaturityMatrix：文件入口段开始，允许直接运行本测试文件；如果没有这一行，初学者必须记住完整 unittest 命令。
    unittest.main()  # 新增代码+FullMaturityMatrix：启动 unittest；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+FullMaturityMatrix：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出入口范围。
