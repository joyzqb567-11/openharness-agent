"""Phase39 Windows Computer Use 坐标模型测试。"""  # 新增代码+Phase39WindowsCoordinates: 说明本文件专门验证 DPI、多显示器和坐标换算；如果没有本测试，后续实现可能只在单显示器 100% 缩放下看似可用。
from __future__ import annotations  # 新增代码+Phase39WindowsCoordinates: 延迟解析类型注解，避免旧 Python 路径因为注解提前求值失败；如果没有这行代码，测试在某些导入顺序下更容易出错。

import json  # 新增代码+Phase39WindowsCoordinates: 用于解析验收场景 JSON；如果没有这行代码，测试无法确认真实终端场景文件是否合法。
import unittest  # 新增代码+Phase39WindowsCoordinates: 使用项目现有 unittest 框架；如果没有这行代码，测试类无法运行。
from pathlib import Path  # 新增代码+Phase39WindowsCoordinates: 用 pathlib 定位场景文件；如果没有这行代码，测试会依赖脆弱的字符串路径拼接。

from learning_agent.computer_use.action_policy import prepare_action_arguments  # 新增代码+Phase39WindowsCoordinates: 直接验证真实动作策略是否接入新坐标模型；如果没有这行代码，测试只能覆盖孤立 helper，不能证明动作会用对坐标。
from learning_agent.computer_use.controller import ComputerUseController, WindowsComputerUseBackend  # 新增代码+Phase39WindowsCoordinates: 引入控制器和 Windows 后端验证窗口状态输出；如果没有这行代码，Phase39 不能证明 observe 结果带坐标上下文。
from learning_agent.computer_use.coordinates import PHASE39_WINDOWS_COORDINATES_MARKER, PHASE39_WINDOWS_COORDINATES_OK_TOKEN, build_coordinate_context, phase39_cli_line, run_phase39_coordinates_contract  # 新增代码+Phase39WindowsCoordinates: 引入预期的新坐标 API；如果没有这行代码，红灯测试无法证明 coordinates.py 缺失。
from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase39WindowsCoordinates: 使用静态 inventory 避免测试触碰真实桌面；如果没有这行代码，测试会依赖本机窗口状态而不稳定。


PHASE39_SCENARIO_PATH = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase39_windows_coordinates.json")  # 新增代码+Phase39WindowsCoordinates: 固定真实可见终端验收场景路径；如果没有这行代码，测试无法提醒场景文件缺失。


def phase39_scaled_window() -> dict[str, object]:  # 新增代码+Phase39WindowsCoordinates: 函数段开始，构造 150% 缩放的安全窗口样本；如果没有这段函数，多个测试会重复手写复杂窗口字典。
    return {  # 新增代码+Phase39WindowsCoordinates: 返回窗口字典供坐标模型和动作策略复用；如果没有这行代码，测试数据无法集中维护。
        "app_id": "notepad.exe",  # 新增代码+Phase39WindowsCoordinates: 使用安全的记事本 app_id；如果没有这行代码，窗口身份不完整会触发目标校验失败。
        "window_id": "hwnd:3901",  # 新增代码+Phase39WindowsCoordinates: 使用稳定窗口 id；如果没有这行代码，控制器无法把请求和 inventory 里的窗口对应起来。
        "title_preview": "Phase39 Notepad",  # 新增代码+Phase39WindowsCoordinates: 提供非敏感标题；如果没有这行代码，窗口摘要可读性会下降。
        "rect": {"left": 100, "top": 50, "right": 400, "bottom": 250},  # 新增代码+Phase39WindowsCoordinates: 声明窗口逻辑坐标矩形；如果没有这行代码，无法测试窗口相对坐标换算。
        "display": {  # 新增代码+Phase39WindowsCoordinates: 声明窗口所在显示器；如果没有这行代码，DPI 缩放只能退回 1.0。
            "display_id": "primary",  # 新增代码+Phase39WindowsCoordinates: 标记主显示器；如果没有这行代码，多显示器审计里无法知道用了哪块屏幕。
            "logical_rect": {"left": 0, "top": 0, "right": 800, "bottom": 600},  # 新增代码+Phase39WindowsCoordinates: 声明逻辑显示器范围；如果没有这行代码，display-relative 坐标无法计算。
            "physical_rect": {"left": 0, "top": 0, "right": 1200, "bottom": 900},  # 新增代码+Phase39WindowsCoordinates: 声明物理像素范围；如果没有这行代码，DPI 物理坐标无法从逻辑坐标推导。
            "scale": 1.5,  # 新增代码+Phase39WindowsCoordinates: 声明 150% 缩放；如果没有这行代码，测试无法捕捉高 DPI 坐标偏移。
        },  # 新增代码+Phase39WindowsCoordinates: 结束显示器元数据；如果没有这行代码，窗口字典语法不完整。
    }  # 新增代码+Phase39WindowsCoordinates: 返回完整窗口样本；如果没有这行代码，调用方拿不到测试数据。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，phase39_scaled_window 到此结束；如果没有这个边界说明，初学者不易看出样本构造范围。


def phase39_left_monitor_window() -> dict[str, object]:  # 新增代码+Phase39WindowsCoordinates: 函数段开始，构造负坐标副屏窗口样本；如果没有这段函数，多显示器负坐标场景会缺少稳定测试数据。
    return {  # 新增代码+Phase39WindowsCoordinates: 返回左侧显示器窗口字典；如果没有这行代码，测试无法覆盖 Windows 常见的负坐标副屏。
        "app_id": "notepad.exe",  # 新增代码+Phase39WindowsCoordinates: 使用安全 app_id；如果没有这行代码，窗口引用不完整。
        "window_id": "hwnd:3902",  # 新增代码+Phase39WindowsCoordinates: 使用另一个稳定窗口 id；如果没有这行代码，多窗口测试无法区分样本。
        "title_preview": "Phase39 Left Monitor",  # 新增代码+Phase39WindowsCoordinates: 提供可读标题；如果没有这行代码，诊断输出不清楚。
        "rect": {"left": -700, "top": 100, "right": -300, "bottom": 400},  # 新增代码+Phase39WindowsCoordinates: 声明位于左侧副屏的窗口矩形；如果没有这行代码，无法验证负 x 坐标。
        "display": {  # 新增代码+Phase39WindowsCoordinates: 声明左侧显示器元数据；如果没有这行代码，模型无法知道显示器原点是负数。
            "display_id": "left-monitor",  # 新增代码+Phase39WindowsCoordinates: 标记左侧副屏；如果没有这行代码，审计无法区分显示器。
            "logical_rect": {"left": -800, "top": 0, "right": 0, "bottom": 600},  # 新增代码+Phase39WindowsCoordinates: 声明副屏逻辑范围；如果没有这行代码，display-relative 坐标会算错。
            "physical_rect": {"left": -800, "top": 0, "right": 0, "bottom": 600},  # 新增代码+Phase39WindowsCoordinates: 声明副屏物理范围；如果没有这行代码，物理坐标无法保持负屏幕原点。
            "scale": 1.0,  # 新增代码+Phase39WindowsCoordinates: 声明副屏 100% 缩放；如果没有这行代码，测试无法确认默认缩放不改变坐标。
        },  # 新增代码+Phase39WindowsCoordinates: 结束显示器元数据；如果没有这行代码，窗口字典语法不完整。
    }  # 新增代码+Phase39WindowsCoordinates: 返回完整副屏窗口样本；如果没有这行代码，调用方拿不到测试数据。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，phase39_left_monitor_window 到此结束；如果没有这个边界说明，初学者不易看出副屏样本范围。


class WindowsComputerUseCoordinatesPhase39Tests(unittest.TestCase):  # 新增代码+Phase39WindowsCoordinates: 类段开始，集中验证 Phase39 坐标模型；如果没有这个测试类，unittest 无法发现这些用例。
    def test_coordinate_model_converts_window_relative_to_physical_with_dpi(self) -> None:  # 新增代码+Phase39WindowsCoordinates: 验证 150% DPI 下窗口相对坐标会转成物理坐标；如果没有这项测试，高 DPI 点击会落错位置。
        context = build_coordinate_context(phase39_scaled_window(), 10, 20)  # 新增代码+Phase39WindowsCoordinates: 构建坐标上下文；如果没有这行代码，断言没有真实被测对象。
        self.assertEqual(context["model"], "phase39_windows_coordinate_model")  # 新增代码+Phase39WindowsCoordinates: 确认模型版本稳定；如果没有这行断言，后续审计无法知道坐标来自哪个规则。
        self.assertEqual(context["window_relative"], {"x": 10, "y": 20})  # 新增代码+Phase39WindowsCoordinates: 确认保留窗口内原始坐标；如果没有这行断言，模型可能丢失来源坐标。
        self.assertEqual(context["logical_screen"], {"x": 110, "y": 70})  # 新增代码+Phase39WindowsCoordinates: 确认逻辑屏幕坐标为窗口原点加相对坐标；如果没有这行断言，基础换算错误不会被发现。
        self.assertEqual(context["display_relative_logical"], {"x": 110, "y": 70})  # 新增代码+Phase39WindowsCoordinates: 确认主屏 display-relative 逻辑坐标；如果没有这行断言，多显示器换算边界不清楚。
        self.assertEqual(context["physical_screen"], {"x": 165, "y": 105})  # 新增代码+Phase39WindowsCoordinates: 确认 1.5 倍物理坐标；如果没有这行断言，高 DPI 坐标可能仍按 100% 输出。
        self.assertEqual(context["dpi_scale"], {"x": 1.5, "y": 1.5})  # 新增代码+Phase39WindowsCoordinates: 确认记录 DPI 缩放；如果没有这行断言，问题复盘时无法解释物理坐标来源。
        self.assertEqual(context["display"]["display_id"], "primary")  # 新增代码+Phase39WindowsCoordinates: 确认选中了主屏；如果没有这行断言，多显示器选择错误不会暴露。

    def test_coordinate_model_selects_negative_left_monitor(self) -> None:  # 新增代码+Phase39WindowsCoordinates: 验证负坐标左侧显示器；如果没有这项测试，副屏点击可能被错误夹到主屏。
        context = build_coordinate_context(phase39_left_monitor_window(), 25, 40)  # 新增代码+Phase39WindowsCoordinates: 构建左屏坐标上下文；如果没有这行代码，断言没有真实输入。
        self.assertEqual(context["display"]["display_id"], "left-monitor")  # 新增代码+Phase39WindowsCoordinates: 确认模型选择左侧显示器；如果没有这行断言，副屏选择错误不会被发现。
        self.assertEqual(context["logical_screen"], {"x": -675, "y": 140})  # 新增代码+Phase39WindowsCoordinates: 确认负屏幕逻辑坐标；如果没有这行断言，负坐标可能被错误归零。
        self.assertEqual(context["display_relative_logical"], {"x": 125, "y": 140})  # 新增代码+Phase39WindowsCoordinates: 确认相对左屏原点的坐标；如果没有这行断言，display-relative 审计会缺失。
        self.assertEqual(context["physical_screen"], {"x": -675, "y": 140})  # 新增代码+Phase39WindowsCoordinates: 确认 100% 缩放下物理坐标保持负屏幕位置；如果没有这行断言，副屏真实动作可能落到错误屏幕。

    def test_action_policy_uses_phase39_coordinate_context_and_backend_physical_coords(self) -> None:  # 新增代码+Phase39WindowsCoordinates: 验证动作策略真正使用 Phase39 坐标模型；如果没有这项测试，新 helper 可能没有接入执行链。
        prepared = prepare_action_arguments("click", {"window": phase39_scaled_window(), "x": 10, "y": 20})  # 新增代码+Phase39WindowsCoordinates: 准备一次点击动作参数；如果没有这行代码，不能证明 controller 前的策略输出。
        backend_arguments = prepared["backend_arguments"]  # 新增代码+Phase39WindowsCoordinates: 取出传给后端的最终参数；如果没有这行代码，后续断言会重复索引难以读懂。
        coordinate_used = prepared["coordinate_used"]  # 新增代码+Phase39WindowsCoordinates: 取出审计坐标；如果没有这行代码，测试不能确认 evidence 内容。
        self.assertEqual(backend_arguments["x"], 165)  # 新增代码+Phase39WindowsCoordinates: 确认后端收到物理 x；如果没有这行断言，真实点击仍可能使用逻辑 x。
        self.assertEqual(backend_arguments["y"], 105)  # 新增代码+Phase39WindowsCoordinates: 确认后端收到物理 y；如果没有这行断言，真实点击仍可能使用逻辑 y。
        self.assertEqual(backend_arguments["window_relative_x"], 10)  # 新增代码+Phase39WindowsCoordinates: 确认保留窗口相对 x；如果没有这行断言，审计无法复盘原始输入。
        self.assertEqual(backend_arguments["window_relative_y"], 20)  # 新增代码+Phase39WindowsCoordinates: 确认保留窗口相对 y；如果没有这行断言，审计无法复盘原始输入。
        self.assertEqual(coordinate_used["space"], "screen")  # 新增代码+Phase39WindowsCoordinates: 保持 Phase30 兼容字段；如果没有这行断言，旧测试和旧消费方可能被破坏。
        self.assertEqual(coordinate_used["source"], "window_relative")  # 新增代码+Phase39WindowsCoordinates: 保持坐标来源字段；如果没有这行断言，审计无法知道 x/y 是窗口内坐标。
        self.assertEqual(coordinate_used["x"], 165)  # 新增代码+Phase39WindowsCoordinates: 保持旧字段但升级为物理 x；如果没有这行断言，后端和审计可能不一致。
        self.assertEqual(coordinate_used["y"], 105)  # 新增代码+Phase39WindowsCoordinates: 保持旧字段但升级为物理 y；如果没有这行断言，后端和审计可能不一致。
        self.assertEqual(coordinate_used["model"], "phase39_windows_coordinate_model")  # 新增代码+Phase39WindowsCoordinates: 确认 evidence 标记新模型；如果没有这行断言，排查时看不出 Phase39 是否生效。
        self.assertEqual(coordinate_used["logical_screen"]["x"], 110)  # 新增代码+Phase39WindowsCoordinates: 确认审计保留逻辑 x；如果没有这行断言，高 DPI 问题无法复盘。
        self.assertEqual(coordinate_used["physical_screen"]["x"], 165)  # 新增代码+Phase39WindowsCoordinates: 确认审计保留物理 x；如果没有这行断言，真实后端坐标没有解释依据。
        self.assertEqual(coordinate_used["display_relative_logical"]["x"], 110)  # 新增代码+Phase39WindowsCoordinates: 确认审计保留 display-relative 坐标；如果没有这行断言，多显示器问题无法定位。

    def test_windows_backend_state_reports_phase39_coordinate_context(self) -> None:  # 新增代码+Phase39WindowsCoordinates: 验证 get_window_state 也会返回坐标上下文；如果没有这项测试，模型只知道截图大小不知道坐标空间。
        inventory = StaticWindowsWindowInventory([phase39_scaled_window()], captured_at="2026-06-03T00:00:00Z", source="phase39_static")  # 新增代码+Phase39WindowsCoordinates: 构建静态窗口 inventory；如果没有这行代码，测试会依赖真实桌面窗口。
        backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=False)  # 新增代码+Phase39WindowsCoordinates: 使用只读 Windows 后端；如果没有这行代码，控制器没有 observe 实现。
        controller = ComputerUseController(backend=backend)  # 新增代码+Phase39WindowsCoordinates: 用控制器走真实 observe 路由；如果没有这行代码，不能验证公开入口。
        result = controller.observe({"action": "get_window_state", "window": {"app_id": "notepad.exe", "window_id": "hwnd:3901"}})  # 新增代码+Phase39WindowsCoordinates: 请求窗口状态；如果没有这行代码，后续没有状态数据可断言。
        self.assertTrue(result.ok, result.message)  # 新增代码+Phase39WindowsCoordinates: 确认 observe 成功；如果没有这行断言，失败结果也可能被继续检查。
        context = result.data["coordinate_context"]  # 新增代码+Phase39WindowsCoordinates: 读取窗口状态里的坐标上下文；如果没有这行代码，无法确认状态字段存在。
        self.assertEqual(context["model"], "phase39_windows_coordinate_model")  # 新增代码+Phase39WindowsCoordinates: 确认窗口状态携带 Phase39 模型版本；如果没有这行断言，状态输出可能仍是旧合同。
        self.assertEqual(context["window_logical_rect"], {"left": 100, "top": 50, "right": 400, "bottom": 250})  # 新增代码+Phase39WindowsCoordinates: 确认窗口逻辑矩形保留；如果没有这行断言，截图原点和动作坐标无法对齐。
        self.assertEqual(context["window_physical_rect"], {"left": 150, "top": 75, "right": 600, "bottom": 375})  # 新增代码+Phase39WindowsCoordinates: 确认窗口物理矩形按 1.5 倍换算；如果没有这行断言，高 DPI 截图边界可能错误。
        self.assertEqual(result.data["dpi_scale"], {"x": 1.5, "y": 1.5})  # 新增代码+Phase39WindowsCoordinates: 确认顶层状态暴露 DPI 缩放；如果没有这行断言，终端状态难以快速阅读缩放信息。
        self.assertEqual(result.data["coordinate_model"], "phase39_windows_coordinate_model")  # 新增代码+Phase39WindowsCoordinates: 确认顶层状态暴露模型名；如果没有这行断言，调试输出不够直观。

    def test_phase39_cli_contract_and_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase39WindowsCoordinates: 验证 CLI 自检和验收场景 token 稳定；如果没有这项测试，真实终端验收可能找不到标记。
        report = run_phase39_coordinates_contract()  # 新增代码+Phase39WindowsCoordinates: 运行 Phase39 自检合同；如果没有这行代码，CLI 输出没有结构化来源。
        line = phase39_cli_line(report)  # 新增代码+Phase39WindowsCoordinates: 转成真实终端会打印的一行文本；如果没有这行代码，场景 token 无法稳定。
        self.assertEqual(PHASE39_WINDOWS_COORDINATES_MARKER, "PHASE39_WINDOWS_COORDINATES_READY")  # 新增代码+Phase39WindowsCoordinates: 确认阶段 marker 不漂移；如果没有这行断言，验收脚本可能失效。
        self.assertEqual(PHASE39_WINDOWS_COORDINATES_OK_TOKEN, "PHASE39_WINDOWS_COORDINATES_OK")  # 新增代码+Phase39WindowsCoordinates: 确认 OK token 不漂移；如果没有这行断言，验收脚本可能失效。
        for token in (PHASE39_WINDOWS_COORDINATES_MARKER, PHASE39_WINDOWS_COORDINATES_OK_TOKEN, "dpi=true", "multi_monitor=true", "action_policy=true", "window_state=true", "actions_expanded=false"):  # 新增代码+Phase39WindowsCoordinates: 遍历真实终端必须出现的 token；如果没有这行代码，场景断言和 CLI 输出可能不一致。
            self.assertIn(token, line)  # 新增代码+Phase39WindowsCoordinates: 确认 token 存在；如果没有这行断言，真实终端验收可能误判通过。
        self.assertTrue(report["dpi"])  # 新增代码+Phase39WindowsCoordinates: 确认自检报告 DPI 通过；如果没有这行断言，CLI 文本可能掩盖结构化失败。
        self.assertTrue(report["multi_monitor"])  # 新增代码+Phase39WindowsCoordinates: 确认自检报告多显示器通过；如果没有这行断言，副屏能力无法被证明。
        self.assertTrue(report["action_policy"])  # 新增代码+Phase39WindowsCoordinates: 确认动作策略接入通过；如果没有这行断言，helper 和执行链可能断开。
        self.assertTrue(report["window_state"])  # 新增代码+Phase39WindowsCoordinates: 确认窗口状态输出通过；如果没有这行断言，observe 路径可能漏接。
        scenario = json.loads(PHASE39_SCENARIO_PATH.read_text(encoding="utf-8"))  # 新增代码+Phase39WindowsCoordinates: 读取验收场景 JSON；如果没有这行代码，场景文件坏掉不会被单测发现。
        expected_tokens = scenario["assertions"]["output_contains"]  # 新增代码+Phase39WindowsCoordinates: 取出真实终端断言 token；如果没有这行代码，测试不能比对验收合同。
        self.assertIn(PHASE39_WINDOWS_COORDINATES_MARKER, expected_tokens)  # 新增代码+Phase39WindowsCoordinates: 确认场景要求阶段 marker；如果没有这行断言，验收可能没有检查核心标记。
        self.assertIn(PHASE39_WINDOWS_COORDINATES_OK_TOKEN, expected_tokens)  # 新增代码+Phase39WindowsCoordinates: 确认场景要求 OK token；如果没有这行断言，验收可能没有检查自检成功。
# 新增代码+Phase39WindowsCoordinates: 类段结束，WindowsComputerUseCoordinatesPhase39Tests 到此结束；如果没有这个边界说明，初学者不易看出测试范围。


if __name__ == "__main__":  # 新增代码+Phase39WindowsCoordinates: 允许直接运行本测试文件；如果没有这行代码，手动调试时只能通过 unittest 模块调用。
    unittest.main()  # 新增代码+Phase39WindowsCoordinates: 启动 unittest 主函数；如果没有这行代码，直接运行文件不会执行任何测试。
