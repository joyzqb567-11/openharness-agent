import unittest  # 新增代码+Phase21TerminalStatusUI: 引入 unittest 测试框架；如果没有这行代码，本文件无法定义可运行的测试用例。

from learning_agent.app.chrome_status_renderer import render_chrome_status  # 新增代码+Phase21TerminalStatusUI: 导入 /chrome 渲染器；如果没有这行代码，测试无法锁定 Chrome 状态页输出。
from learning_agent.app.status_renderer import render_status_snapshot  # 新增代码+Phase21TerminalStatusUI: 导入 /status 渲染器；如果没有这行代码，测试无法锁定总状态页输出。


class TerminalStatusUiPhase21Tests(unittest.TestCase):  # 新增代码+Phase21TerminalStatusUI: 定义 Phase 21 终端状态 UI 测试集合；如果没有这个类，unittest 不会发现本阶段测试。
    def test_status_renderer_adds_summary_next_command_and_recent_errors(self) -> None:  # 新增代码+Phase21TerminalStatusUI: 验证 /status 有摘要、下一步和最近问题；如果没有这个测试，状态页可能继续冗长但不可操作。
        snapshot = {  # 新增代码+Phase21TerminalStatusUI: 构造最小状态快照；如果没有这行代码，渲染器测试没有输入事实源。
            "workspace": "H:/demo",  # 新增代码+Phase21TerminalStatusUI: 提供工作区字段；如果没有这行代码，状态页 workspace 行无法稳定渲染。
            "counts": {"runs": 1, "tasks": 0, "commands": 0, "sessions": 1, "status_events": 2},  # 新增代码+Phase21TerminalStatusUI: 提供计数摘要；如果没有这行代码，状态页规模信息无法测试。
            "health": {"ok": False, "warnings": ["bridge offline"]},  # 新增代码+Phase21TerminalStatusUI: 提供健康告警；如果没有这行代码，recent errors 无法覆盖 health 来源。
            "resume": {"needs_review": True, "warnings": ["resume checkpoint stale"]},  # 新增代码+Phase21TerminalStatusUI: 提供恢复风险；如果没有这行代码，下一步提示无法覆盖人工复核场景。
            "browser": {  # 新增代码+Phase21TerminalStatusUI: 提供浏览器状态块；如果没有这行代码，/status 无法展示浏览器连接摘要。
                "provider_status": {  # 新增代码+Phase21TerminalStatusUI: 提供 provider 状态；如果没有这行代码，Chrome 连接状态无法推导。
                    "chrome_extension": {"connected": False, "paired": False, "pending_command_count": 0},  # 新增代码+Phase21TerminalStatusUI: 模拟扩展未连接未配对；如果没有这行代码，下一步不会指向 /chrome。
                    "native_host": {"connected": False, "installer_state": "registry_registered"},  # 新增代码+Phase21TerminalStatusUI: 模拟 native host 已注册但断连；如果没有这行代码，连接摘要没有 native host 维度。
                },  # 新增代码+Phase21TerminalStatusUI: 结束 provider 状态块；如果没有这行代码，测试快照结构不完整。
            },  # 新增代码+Phase21TerminalStatusUI: 结束浏览器状态块；如果没有这行代码，测试快照结构不完整。
            "status_events": [{"sequence": 7, "event_type": "error", "payload": {"message": "native bridge timeout"}}],  # 新增代码+Phase21TerminalStatusUI: 提供最近错误事件；如果没有这行代码，recent_error 行没有稳定来源。
        }  # 新增代码+Phase21TerminalStatusUI: 结束快照字典；如果没有这行代码，Python 语法不完整。
        rendered = render_status_snapshot(snapshot)  # 新增代码+Phase21TerminalStatusUI: 渲染状态页文本；如果没有这行代码，后续断言没有对象。
        self.assertIn("Status Summary", rendered)  # 新增代码+Phase21TerminalStatusUI: 断言新增摘要区存在；如果没有这行代码，/status 可能仍然缺少可扫描总览。
        self.assertIn("next=/chrome pairing-diagnose", rendered)  # 新增代码+Phase21TerminalStatusUI: 断言下一步命令明确指向 Chrome 诊断；如果没有这行代码，用户看状态后仍不知道该做什么。
        self.assertIn("recent_error=", rendered)  # 新增代码+Phase21TerminalStatusUI: 断言最近问题区存在；如果没有这行代码，错误会埋在长列表里。
        self.assertTrue(all(len(line) <= 220 for line in rendered.splitlines()))  # 新增代码+Phase21TerminalStatusUI: 限制单行长度适合可见终端截图；如果没有这行代码，状态页会被长行撑坏。

    def test_chrome_renderer_adds_summary_next_command_and_recent_issue(self) -> None:  # 新增代码+Phase21TerminalStatusUI: 验证 /chrome 有摘要、下一步和最近问题；如果没有这个测试，Chrome 状态页可能只堆字段不指导操作。
        snapshot = {  # 新增代码+Phase21TerminalStatusUI: 构造 Chrome 最小快照；如果没有这行代码，渲染器测试没有输入。
            "browser": {  # 新增代码+Phase21TerminalStatusUI: 提供浏览器区块；如果没有这行代码，Chrome 渲染器读不到 provider_status。
                "provider_status": {  # 新增代码+Phase21TerminalStatusUI: 提供 provider 状态；如果没有这行代码，Chrome 页面无法显示连接状态。
                    "providers": {"chrome_extension": {"available": False, "reason": "chrome_extension_not_paired"}},  # 新增代码+Phase21TerminalStatusUI: 模拟扩展 provider 不可用；如果没有这行代码，recent_issue 没有 provider 来源。
                    "chrome_extension": {"connected": True, "paired": False, "pending_command_count": 0, "pending_pairing_request_status": ""},  # 新增代码+Phase21TerminalStatusUI: 模拟扩展已连但未配对；如果没有这行代码，下一步不会指向 pairing-diagnose。
                    "native_host": {"connected": True, "installer_state": "registry_registered", "bridge_state_file": "bridge.json"},  # 新增代码+Phase21TerminalStatusUI: 模拟 native host 已注册且连接；如果没有这行代码，当前状态无法定位到已注册未配对。
                },  # 新增代码+Phase21TerminalStatusUI: 结束 provider 状态块；如果没有这行代码，测试快照结构不完整。
                "events": [{"event_type": "provider_error", "run_id": "run-1"}],  # 新增代码+Phase21TerminalStatusUI: 提供最近浏览器问题事件；如果没有这行代码，recent_issue 行无法覆盖事件来源。
            },  # 新增代码+Phase21TerminalStatusUI: 结束浏览器区块；如果没有这行代码，测试快照结构不完整。
        }  # 新增代码+Phase21TerminalStatusUI: 结束快照字典；如果没有这行代码，Python 语法不完整。
        rendered = render_chrome_status(snapshot)  # 新增代码+Phase21TerminalStatusUI: 渲染 /chrome 文本；如果没有这行代码，后续断言没有对象。
        self.assertIn("Chrome Summary", rendered)  # 新增代码+Phase21TerminalStatusUI: 断言 Chrome 摘要区存在；如果没有这行代码，/chrome 仍不够像成熟状态面板。
        self.assertIn("next=/chrome pairing-diagnose", rendered)  # 新增代码+Phase21TerminalStatusUI: 断言下一步命令可见；如果没有这行代码，用户要自己从字段推理配对问题。
        self.assertIn("recent_issue=", rendered)  # 新增代码+Phase21TerminalStatusUI: 断言最近问题可见；如果没有这行代码，provider 错误会被长状态淹没。
        self.assertTrue(all(len(line) <= 220 for line in rendered.splitlines()))  # 新增代码+Phase21TerminalStatusUI: 限制 /chrome 单行长度适合截图；如果没有这行代码，真实终端验收可读性会下降。


if __name__ == "__main__":  # 新增代码+Phase21TerminalStatusUI: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase21TerminalStatusUI: 启动 unittest 主函数；如果没有这行代码，直接运行文件不会执行任何测试。
