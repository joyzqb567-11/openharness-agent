import unittest  # 新增代码+ChromeTerminalUI: 引入 unittest 测试框架；若没有这行代码，本文件无法定义测试用例。

from learning_agent.app.chrome_status_renderer import render_chrome_status  # 新增代码+ChromeTerminalUI: 导入待实现的 /chrome 专用渲染器；若没有这行代码，测试无法锁定终端状态文本。


class ChromeTerminalStatusUiStage18Tests(unittest.TestCase):  # 新增代码+ChromeTerminalUI: 定义 Phase 6 的终端 Chrome 状态 UI 测试集合；若没有这段代码，新增 /chrome 命令没有自动化红线。
    def test_render_chrome_status_focuses_browser_extension_native_host_and_tab(self) -> None:  # 新增代码+ChromeTerminalUI: 验证渲染器展示浏览器关键状态；若没有这段测试，/chrome 可能退化成泛泛状态页。
        snapshot = {  # 新增代码+ChromeTerminalUI: 构造最小统一状态快照；若没有这行代码，渲染器没有输入数据。
            "browser": {  # 新增代码+ChromeTerminalUI: 提供 browser 区块；若没有这行代码，渲染器无法展示 Chrome 生态。
                "latest_run": {"run_id": "browser-run-1", "status": "completed"},  # 新增代码+ChromeTerminalUI: 提供最近浏览器 run；若没有这行代码，最近任务摘要无法验证。
                "provider_status": {  # 新增代码+ChromeTerminalUI: 提供 provider 状态；若没有这行代码，插件和 native host 状态无法验证。
                    "providers": {"chrome_extension": {"available": True, "reason": "connected"}},  # 新增代码+ChromeTerminalUI: 提供 Chrome extension provider 健康；若没有这行代码，provider 渲染无输入。
                    "chrome_extension": {"connected": True, "pending_command_count": 2, "permission_event_count": 3},  # 新增代码+ChromeTerminalUI: 提供插件连接和计数；若没有这行代码，插件摘要无法验证。
                    "native_host": {"connected": True, "bridge_state_file": "bridge.json"},  # 新增代码+ChromeTerminalUI: 提供 native host 状态；若没有这行代码，native host 摘要无法验证。
                    "tabs": {"active_tab": {"title": "Example", "url": "https://example.test/page"}},  # 新增代码+ChromeTerminalUI: 提供 active tab；若没有这行代码，当前页面摘要无法验证。
                    "permissions": {"permission_event_count": 3},  # 新增代码+ChromeTerminalUI: 提供权限事件数；若没有这行代码，权限摘要无法验证。
                },  # 新增代码+ChromeTerminalUI: provider_status 结束；若没有这行代码，Python 字典语法不完整。
                "recordings": {"recording_count": 1, "latest": {"recording_id": "rec-1", "gif_path": "run.gif"}},  # 新增代码+ChromeTerminalUI: 提供录制证据；若没有这行代码，视觉证据摘要无法验证。
            }  # 新增代码+ChromeTerminalUI: browser 区块结束；若没有这行代码，Python 字典语法不完整。
        }  # 新增代码+ChromeTerminalUI: 快照构造结束；若没有这行代码，Python 字典语法不完整。
        text = render_chrome_status(snapshot)  # 新增代码+ChromeTerminalUI: 渲染专用状态页；若没有这行代码，断言没有文本对象。
        self.assertIn("Chrome Status", text)  # 新增代码+ChromeTerminalUI: 标题必须是专用 Chrome 状态；若没有这行代码，泛状态页可能误通过。
        self.assertIn("provider=chrome_extension available=true", text)  # 新增代码+ChromeTerminalUI: provider 健康必须显示；若没有这行代码，插件轨道状态可能缺失。
        self.assertIn("native_host_connected=true", text)  # 新增代码+ChromeTerminalUI: native host 连接必须显示；若没有这行代码，安装/桥接问题不可见。
        self.assertIn("chrome_extension_connected=true", text)  # 新增代码+ChromeTerminalUI: 插件连接必须显示；若没有这行代码，配对状态不可见。
        self.assertIn("active_tab_title=Example", text)  # 新增代码+ChromeTerminalUI: 当前标签页标题必须显示；若没有这行代码，用户不知道 Chrome 停在哪个页面。
        self.assertIn("permission_event_count=3", text)  # 新增代码+ChromeTerminalUI: 权限事件数必须显示；若没有这行代码，授权状态不可审计。
        self.assertIn("latest_run_id=browser-run-1", text)  # 新增代码+ChromeTerminalUI: 最近浏览器 run 必须显示；若没有这行代码，用户无法定位任务证据。
        self.assertIn("gif_path=run.gif", text)  # 新增代码+ChromeTerminalUI: 最近录制 GIF 必须显示；若没有这行代码，视觉证据入口不可见。

    def test_render_chrome_status_handles_empty_snapshot(self) -> None:  # 新增代码+ChromeTerminalUI: 验证空状态不会崩溃；若没有这段测试，新终端命令可能在首次运行时报错。
        text = render_chrome_status({})  # 新增代码+ChromeTerminalUI: 用空快照渲染；若没有这行代码，无法覆盖空态路径。
        self.assertIn("Chrome Status", text)  # 新增代码+ChromeTerminalUI: 空态也要有标题；若没有这行代码，用户看不出命令执行了。
        self.assertIn("provider=(empty)", text)  # 新增代码+ChromeTerminalUI: 空 provider 要明确显示；若没有这行代码，用户可能误以为 UI 坏了。

    def test_render_chrome_status_guides_next_command_for_installer_states(self) -> None:  # 新增代码+Phase12ChromeStatusGuide: 验证 /chrome 会按安装状态提示下一条命令；如果没有这段测试，用户仍要猜下一步。
        not_installed_text = render_chrome_status({"browser": {"provider_status": {"native_host": {"installer_state": "not_installed"}}}})  # 新增代码+Phase12ChromeStatusGuide: 构造未安装状态；如果没有这行代码，无法验证首次使用引导。
        manifest_created_text = render_chrome_status({"browser": {"provider_status": {"native_host": {"installer_state": "manifest_created"}}}})  # 新增代码+Phase12ChromeStatusGuide: 构造已 preview 状态；如果没有这行代码，无法验证确认安装引导。
        registered_text = render_chrome_status({"browser": {"provider_status": {"native_host": {"installer_state": "registry_registered"}}}})  # 新增代码+Phase12ChromeStatusGuide: 构造已注册状态；如果没有这行代码，无法验证配对同步引导。
        self.assertIn("Chrome Guide", not_installed_text)  # 新增代码+Phase12ChromeStatusGuide: 状态页必须包含向导区；如果没有这行断言，新增引导可能消失。
        self.assertIn("/chrome install-preview", not_installed_text)  # 新增代码+Phase12ChromeStatusGuide: 未安装时应提示先预览；如果没有这行断言，小白用户不知道安全起点。
        self.assertIn("/chrome install-confirm", manifest_created_text)  # 新增代码+Phase12ChromeStatusGuide: 已生成 manifest 时应提示确认安装；如果没有这行断言，preview 后流程断开。
        self.assertIn("extension pairing", registered_text)  # 新增代码+Phase12ChromeStatusGuide: 已注册时应提示扩展配对；如果没有这行断言，安装后用户不知道进入配对/session sync。

    def test_render_chrome_status_shows_pairing_and_session_sync(self) -> None:  # 新增代码+Phase13ChromePairingGuide: 验证 /chrome 展示配对和 session sync；如果没有这段测试，已注册后的下一步仍不透明。
        snapshot = {  # 新增代码+Phase13ChromePairingGuide: 构造包含配对状态的最小快照；如果没有这行代码，渲染器没有 pairing 输入。
            "browser": {  # 新增代码+Phase13ChromePairingGuide: 提供 browser 区块；如果没有这行代码，渲染器拿不到 provider_status。
                "provider_status": {  # 新增代码+Phase13ChromePairingGuide: 提供 provider_status；如果没有这行代码，配对字段无处读取。
                    "chrome_extension": {"connected": True, "paired": True, "device_id": "device-1", "session_id": "session-1", "last_seen_at": 12345},  # 新增代码+Phase13ChromePairingGuide: 提供扩展配对摘要；如果没有这行代码，无法验证 session sync 行。
                    "native_host": {"installer_state": "registry_registered"},  # 新增代码+Phase13ChromePairingGuide: 提供已注册状态；如果没有这行代码，向导不会进入配对分支。
                }  # 新增代码+Phase13ChromePairingGuide: provider_status 结束；如果没有这行代码，字典语法不完整。
            }  # 新增代码+Phase13ChromePairingGuide: browser 区块结束；如果没有这行代码，字典语法不完整。
        }  # 新增代码+Phase13ChromePairingGuide: 快照结束；如果没有这行代码，字典语法不完整。
        text = render_chrome_status(snapshot)  # 新增代码+Phase13ChromePairingGuide: 渲染 /chrome 状态；如果没有这行代码，断言没有文本对象。
        self.assertIn("paired=true", text)  # 新增代码+Phase13ChromePairingGuide: 输出必须显示已配对；如果没有这行断言，用户不知道 extension 是否完成配对。
        self.assertIn("device_id=device-1", text)  # 新增代码+Phase13ChromePairingGuide: 输出必须显示设备 id；如果没有这行断言，用户无法定位配对设备。
        self.assertIn("session_id=session-1", text)  # 新增代码+Phase13ChromePairingGuide: 输出必须显示 session id；如果没有这行断言，session sync 不可审计。
        self.assertIn("session sync 已连接", text)  # 新增代码+Phase13ChromePairingGuide: 已配对时向导必须说明同步已连接；如果没有这行断言，用户不知道是否还要操作。


if __name__ == "__main__":  # 新增代码+ChromeTerminalUI: 允许直接运行本测试文件；若没有这行代码，初学者无法用 python 文件方式启动测试。
    unittest.main()  # 新增代码+ChromeTerminalUI: 启动 unittest 主函数；若没有这行代码，直接运行文件不会执行测试。
