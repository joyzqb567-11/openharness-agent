# 源码复核门禁改动备份 2026-06-05

本文件按项目规则备份本轮新增和修改的关键代码片段，方便用户学习 `/computer use --full` 真实成熟度为什么不能只看文档或旧矩阵。

## learning_agent/core/agent.py

```python
        real_actions = True  # 修改代码+源码复核门禁：自然语言桌面任务在 full 授权后必须请求真实执行路径；如果没有这一行，agent 会继续用 recording 证据冒充真实能力。
        report = runtime.run_prompt(normalized_input, real_actions=real_actions)  # 修改代码+源码复核门禁：把桌面任务交给真实动作请求路径，runtime 会在未授权或未接线时安全拒绝；如果没有这一行，用户会误以为 /computer use --full 已经能真实操作桌面。
```

```python
        decision = str(report.get("decision", ""))  # 新增代码+源码复核门禁：读取 runtime 决策码用于选择不误导的提示文案；如果没有这一行，后续只能用模糊状态猜测原因。
        if decision == "computer_use_full_mode_required":  # 修改代码+源码复核门禁：未授权时只提示先执行 full-confirm；如果没有这一行，用户会误以为已经进入执行链路。
            guidance_line = "请先运行 /computer use --full 并按提示执行 /computer use --full-confirm <token>。"  # 修改代码+源码复核门禁：给出开启 full 的下一步；如果没有这一行，未授权失败没有可操作指引。
        elif decision == "real_actions_not_enabled_in_desktop_task_runtime":  # 新增代码+源码复核门禁：真实动作闭环未接线时单独提示；如果没有这一行，失败会被误说成录制模式证据链。
            guidance_line = "已进入真实动作请求路径，但当前 runtime 尚未接入真实桌面执行闭环，不能声明成熟完成。"  # 新增代码+源码复核门禁：明确这是能力缺口而非成功；如果没有这一行，用户会把 full 模式误读成已经能真实控制桌面。
        elif bool(report.get("passed", False)) and bool(report.get("recording_mode", False)):  # 新增代码+源码复核门禁：录制模式通过时才说录制证据链；如果没有这一行，失败路径也会被套用成功文案。
            guidance_line = "桌面任务已交给 Computer Use runtime 录制模式证据链。"  # 修改代码+源码复核门禁：保留录制模式成功说明；如果没有这一行，旧录制验收的成功语义会丢失。
        elif bool(report.get("passed", False)):  # 新增代码+源码复核门禁：非录制且通过时说明真实闭环完成本次任务；如果没有这一行，真实路径成功也会显示成录制模式。
            guidance_line = "桌面任务已交给 Computer Use runtime 真实执行闭环，并返回可复核证据。"  # 新增代码+源码复核门禁：给真实执行成功一个准确文案；如果没有这一行，用户无法区分 real 和 recording。
        else:  # 新增代码+源码复核门禁：其它失败原因走保守提示；如果没有这一行，未知失败可能没有提示文本。
            guidance_line = "Computer Use runtime 返回失败报告，请以 decision 和 report_json 为准继续排查。"  # 新增代码+源码复核门禁：让失败解释回到结构化源码事实；如果没有这一行，未知失败会被误导性文案覆盖。
```

## learning_agent/computer_use/desktop_task_runtime.py

```python
    def __init__(self, base_dir: str | Path | None = None, mode_store: ComputerUseModeSessionStore | None = None, real_execution_loop: Any | None = None) -> None:  # 修改代码+源码复核门禁：函数段开始，初始化运行时依赖并允许注入真实执行闭环；如果没有这段函数，调用方无法注入隔离证据目录和 session store。
        self.real_execution_loop = real_execution_loop  # 新增代码+源码复核门禁：保存可注入真实执行闭环，默认 None 表示不触碰桌面；如果没有这一行，real_actions=True 只能永久硬拒绝。
```

```python
        return {"marker": COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_READY, "ok_token": "", "model": COMPUTER_USE_FULL_DESKTOP_TASK_RUNTIME_MODEL, "passed": False, "decision": "", "desktop_task_router_used": bool(intent.is_desktop_task), "natural_language_desktop_tasks_route_to_computer_use": bool(intent.is_desktop_task and intent.requires_gui_actions), "computer_use_gui_route_used": False, "full_mode_session_used": full_mode_session_used, "target_app": target_app, "intent": intent.to_dict(), "real_desktop_touched": False, "real_actions_supported": False, "recording_mode": True, "forbidden_script_generation_used": False, "bash_final_artifact_route_used": False, "forbidden_script_artifact_route_blocked": True, "owned_window_verified": False, "gui_action_count": 0, "low_level_event_count": 0, "post_action_screenshot_exists": False, "tool_calls": []}  # 修改代码+源码复核门禁：失败默认不携带 OK token；如果没有这一行，report_json 会在 passed=false 时仍显示成功 token 误导用户。
```

```python
    def _real_execution_report(self, report: dict[str, Any], prompt: str, target_app: str) -> dict[str, Any]:  # 新增代码+源码复核门禁：函数段开始，调用注入的真实执行闭环并汇总报告；如果没有这段函数，real_actions=True 无法从硬拒绝推进到受控真实路径。
        loop = self.real_execution_loop  # 新增代码+源码复核门禁：读取注入的真实执行闭环；如果没有这一行，后续无法判断是否具备真实执行能力。
        if loop is None or not hasattr(loop, "run_desktop_task"):  # 新增代码+源码复核门禁：没有闭环或接口不匹配时安全拒绝；如果没有这一行，None 会导致异常或误触其它对象。
            report["decision"] = "real_actions_not_enabled_in_desktop_task_runtime"  # 修改代码+源码复核门禁：写入真实动作未接线原因码；如果没有这一行，用户看不出为什么没有真实执行。
            report["real_actions_supported"] = False  # 新增代码+源码复核门禁：声明当前实例不支持真实动作；如果没有这一行，调用方会误以为 full mode 已足够。
            return report  # 新增代码+源码复核门禁：返回零副作用报告；如果没有这一行，未接线时可能继续执行未知逻辑。
        loop_report = dict(loop.run_desktop_task(target_app=target_app, prompt=prompt))  # 新增代码+源码复核门禁：调用注入闭环并复制返回报告；如果没有这一行，real_actions=True 没有真实执行事实来源。
        report.update(loop_report)  # 新增代码+源码复核门禁：把真实闭环字段合并到桌面任务报告；如果没有这一行，最终 CLI 看不到真实动作结果。
        report["real_actions_supported"] = True  # 新增代码+源码复核门禁：声明当前实例已接入真实动作闭环；如果没有这一行，用户无法区分硬拒绝和真实执行。
        report["recording_mode"] = False  # 新增代码+源码复核门禁：真实执行路径不是录制模式；如果没有这一行，成熟度会继续混淆 recording 和 real。
        report["computer_use_gui_route_used"] = bool(loop_report.get("computer_use_gui_route_used", loop_report.get("ok", False)))  # 新增代码+源码复核门禁：汇总真实闭环是否走 GUI 路由；如果没有这一行，最终报告可能缺少 GUI route token。
        report["owned_window_verified"] = bool(loop_report.get("owned_window_verified", False))  # 新增代码+源码复核门禁：汇总目标窗口是否验证；如果没有这一行，动作可能缺少目标身份事实。
        report["gui_action_count"] = _desktop_task_runtime_safe_int(loop_report.get("gui_action_count", 0))  # 新增代码+源码复核门禁：汇总真实 GUI 动作数；如果没有这一行，成功可能没有动作规模证据。
        report["low_level_event_count"] = _desktop_task_runtime_safe_int(loop_report.get("low_level_event_count", 0))  # 新增代码+源码复核门禁：汇总真实低层事件数；如果没有这一行，真实动作可能只是口头成功。
        report["real_desktop_touched"] = bool(loop_report.get("real_desktop_touched") or loop_report.get("real_dispatch_performed"))  # 新增代码+源码复核门禁：汇总真实桌面触达事实；如果没有这一行，最终矩阵拿不到真实执行证据。
        report["forbidden_script_artifact_route_blocked"] = not bool(report.get("forbidden_script_generation_used", False) or report.get("bash_final_artifact_route_used", False))  # 新增代码+源码复核门禁：真实路径仍必须阻断脚本成品绕路；如果没有这一行，真实执行可能和脚本作弊混在一起。
        report["passed"] = bool(loop_report.get("ok") and report["computer_use_gui_route_used"] and report["owned_window_verified"] and report["low_level_event_count"] > 0 and report["real_desktop_touched"] and report["forbidden_script_artifact_route_blocked"])  # 新增代码+源码复核门禁：只有真实动作、窗口、事件和防作弊都满足才通过；如果没有这一行，局部成功会被误判成熟。
        report["ok_token"] = COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK if report["passed"] else ""  # 新增代码+源码复核门禁：只有真实执行通过才写 OK token；如果没有这一行，失败 JSON 仍可能暴露成功 token。
        report["decision"] = str(loop_report.get("decision", "real_desktop_task_execution_finished"))  # 新增代码+源码复核门禁：保留真实闭环决策码；如果没有这一行，调用方看不到真实执行的结束原因。
        return report  # 新增代码+源码复核门禁：返回完整真实执行报告；如果没有这一行，run_prompt 拿不到结果。
    # 新增代码+源码复核门禁：函数段结束，ComputerUseDesktopTaskRuntime._real_execution_report 到此结束；如果没有这个边界说明，代码小白不容易看出真实执行汇总范围。
```

```python
        checked["ok_token"] = COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK if checked["passed"] else ""  # 新增代码+源码复核门禁：只有录制验收通过才写 OK token；如果没有这一行，失败 JSON 仍可能暴露成功 token。
        if real_actions:  # 修改代码+源码复核门禁：真实动作请求进入可注入真实执行闭环；如果没有这一行，调用方可能误以为 recording runtime 会真实画图。
            return self._real_execution_report(report, prompt, target_app)  # 修改代码+源码复核门禁：有真实闭环则执行、无闭环则安全拒绝；如果没有这一行，real_actions=True 会永久停在硬拒绝。
```

## learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py

```python
from typing import Any  # 新增代码+源码复核门禁：导入 Any 给 fake 真实执行闭环标注动态报告；如果没有这一行，新增测试里的类型标注会报错。

class FakeRealExecutionLoopForAgentRoute:  # 新增代码+源码复核门禁：类段开始，给 agent 主路由测试提供安全 fake 真实执行闭环；如果没有这个类，测试只能触碰真实桌面或无法证明 real_actions=True 正向路径。
    def run_desktop_task(self, target_app: str, prompt: str) -> dict[str, Any]:  # 新增代码+源码复核门禁：函数段开始，返回真实执行形状的脱敏报告；如果没有这段函数，desktop runtime 无法调用注入闭环。
        return {"ok": True, "decision": "agent_route_real_execution_loop_used", "target_app": target_app, "prompt_length": len(prompt), "computer_use_gui_route_used": True, "owned_window_verified": True, "gui_action_count": 1, "low_level_event_count": 3, "real_dispatch_performed": True, "real_desktop_touched": True, "recording_mode": False, "post_action_screenshot_exists": True, "forbidden_script_generation_used": False, "bash_final_artifact_route_used": False, "forbidden_script_artifact_route_blocked": True}  # 新增代码+源码复核门禁：返回可让汇总门禁通过的真实动作字段；如果没有这一行，agent 主路由正向测试没有事实来源。
    # 新增代码+源码复核门禁：函数段结束，FakeRealExecutionLoopForAgentRoute.run_desktop_task 到此结束；如果没有这个边界说明，初学者不容易看出 fake 闭环范围。
# 新增代码+源码复核门禁：类段结束，FakeRealExecutionLoopForAgentRoute 到此结束；如果没有这个边界说明，初学者不容易看出 fake 闭环范围。
```

```python
    def test_agent_full_mode_without_real_loop_does_not_claim_ok(self) -> None:  # 新增代码+源码复核门禁：函数段开始，验证 full 模式但未接真实闭环时不能报成熟成功；如果没有这个测试，主 agent 可能继续用录制成功误导用户。
        import tempfile  # 新增代码+源码复核门禁：导入临时目录工具隔离 agent workspace；如果没有这一行，测试会污染真实运行目录。
        from pathlib import Path  # 新增代码+源码复核门禁：导入 Path 构造 workspace 路径；如果没有这一行，LearningAgent 构造参数不够清楚。
        class UnusedModel:  # 新增代码+源码复核门禁：类段开始，定义不应该被调用的假模型；如果没有这个类，测试无法证明桌面任务在模型前被拦截。
            def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码+源码复核门禁：提供模型 chat 接口；如果没有这一行，LearningAgent 无法初始化离线模型。
                del messages, tools  # 新增代码+源码复核门禁：声明本测试不使用模型输入；如果没有这一行，未使用参数意图不清楚。
                return ModelMessage(text="model path should not run")  # 新增代码+源码复核门禁：返回哨兵文本；如果没有这一行，模型路径被误走时没有可见标记。
            # 新增代码+源码复核门禁：函数段结束，UnusedModel.chat 到此结束；如果没有这个边界说明，初学者不容易看出 fake 模型范围。
        # 新增代码+源码复核门禁：类段结束，UnusedModel 到此结束；如果没有这个边界说明，初学者不容易看出 fake 模型范围。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+源码复核门禁：创建临时 workspace；如果没有这一行，测试会污染真实项目 memory。
            workspace = Path(raw_dir)  # 新增代码+源码复核门禁：把临时目录转成 Path；如果没有这一行，LearningAgent 构造参数不够清楚。
            agent = LearningAgent(model=UnusedModel(), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+源码复核门禁：创建真实 agent 但使用离线假模型；如果没有这一行，测试没有 agent.run 主体。
            agent.desktop_task_runtime = ComputerUseDesktopTaskRuntime.for_test(full_mode=True)  # 新增代码+源码复核门禁：注入 full 已确认但未接真实执行闭环的 runtime；如果没有这一行，测试无法稳定复现当前缺口。
            answer = agent.run("请使用本地电脑的画图软件画一个皮卡丘。", max_turns=1)  # 新增代码+源码复核门禁：执行真实 run 入口；如果没有这一行，主路由行为没有事实来源。
            self.assertNotIn("COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK", answer)  # 新增代码+源码复核门禁：断言未接真实闭环不能给 OK；如果没有这一行，录制或空路径可能再次冒充成熟。
            self.assertIn("real_actions_not_enabled_in_desktop_task_runtime", answer)  # 新增代码+源码复核门禁：断言答案暴露真实闭环未接线原因；如果没有这一行，用户无法知道缺口在哪里。
            self.assertNotIn("录制模式证据链", answer)  # 新增代码+源码复核门禁：断言真实闭环缺失时不再出现录制成功暗示；如果没有这一行，用户可能把失败文案误读成成熟完成。
            self.assertIn("real_desktop_touched=false", answer)  # 新增代码+源码复核门禁：断言未接线时没有触碰真实桌面；如果没有这一行，安全边界不可见。
            self.assertNotIn("model path should not run", answer)  # 新增代码+源码复核门禁：断言普通模型没有绕过桌面 runtime；如果没有这一行，根因路由可能退化。
    # 新增代码+源码复核门禁：函数段结束，test_agent_full_mode_without_real_loop_does_not_claim_ok 到此结束；如果没有这个边界说明，代码小白不容易看出失败门禁范围。
```

## learning_agent/computer_use/universal_action_dsl.py

本轮还新增了 `_phase118_dispatch_reports_real_dispatch(...)`，用于从 `windows_sendinput_low_level` sender 和低层事件数识别真实派发，避免真实 sender 被报告成 `real_dispatch_performed=false`。

## learning_agent/computer_use/universal_paint_pikachu_acceptance.py

本轮把 `Phase120RepresentativeRealDragSender` 明确标记为 `physical_desktop_dispatch_performed=false`，并让 Paint/Pikachu 验收只有在物理派发和真实画布变化都存在时才算真实成熟。

## learning_agent/computer_use/universal_final_maturity_matrix.py

本轮把最终矩阵从“代表性 recording 证据即可通过”改为“必须有真实窗口观察、真实 UIA/vision 定位、真实 SendInput 派发和真实验收”，所以当前源码评估结果应为未成熟，而不是完成。
