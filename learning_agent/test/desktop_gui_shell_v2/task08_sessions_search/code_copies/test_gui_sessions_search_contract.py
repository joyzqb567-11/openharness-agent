import json  # 新增代码+DesktopGUISessionSearchTest：解析 GUI bridge JSON 响应；如果没有这行，HTTP 合同只能比较原始字节。
import tempfile  # 新增代码+DesktopGUISessionSearchTest：创建隔离工作区；如果没有这行，测试会污染真实项目 memory。
import threading  # 新增代码+DesktopGUISessionSearchTest：后台运行 HTTP server；如果没有这行，测试请求会被 serve_forever 阻塞。
import unittest  # 新增代码+DesktopGUISessionSearchTest：使用 unittest 让蓝图命令能发现测试；如果没有这行，测试不会被标准 runner 执行。
import urllib.parse  # 新增代码+DesktopGUISessionSearchTest：编码中文搜索 query；如果没有这行，URL 里的中文可能被错误解析。
import urllib.request  # 新增代码+DesktopGUISessionSearchTest：使用标准库请求本地 bridge；如果没有这行，测试需要额外依赖。
from pathlib import Path  # 新增代码+DesktopGUISessionSearchTest：使用 Path 管理临时工作区；如果没有这行，路径拼接容易出错。

from learning_agent.app.gui_bridge import GuiMessage, GuiRunManager, create_gui_bridge_server  # 新增代码+DesktopGUISessionSearchTest：导入被测 manager、消息结构和 server 工厂；如果没有这行，测试无法构造会话事实源。


class GuiSessionsSearchContractTests(unittest.TestCase):  # 新增代码+DesktopGUISessionSearchTest：测试类段开始，锁定 V2 sessions/search 合同；如果没有这个类，unittest 不会执行这些合同。
    def _seed_session(self, manager: GuiRunManager, session_id: str, user_text: str, assistant_text: str = "") -> None:  # 新增代码+DesktopGUISessionSearchTest：helper 段开始，向 manager 写入测试会话；如果没有这段，每个测试都要重复消息构造。
        session = manager._session(session_id)  # 新增代码+DesktopGUISessionSearchTest：获取或创建测试 session；如果没有这行，消息没有容器。
        session.messages.append(GuiMessage(id=f"{session_id}_user", role="user", text=user_text, turn_id=f"{session_id}_turn", status="completed"))  # 新增代码+DesktopGUISessionSearchTest：写入用户消息；如果没有这行，标题和搜索没有用户文本来源。
        session.messages.append(GuiMessage(id=f"{session_id}_assistant", role="assistant", text=assistant_text, turn_id=f"{session_id}_turn", status="completed"))  # 新增代码+DesktopGUISessionSearchTest：写入助手消息；如果没有这行，搜索片段无法覆盖回答文本。
        session.last_turn_id = f"{session_id}_turn"  # 新增代码+DesktopGUISessionSearchTest：记录最近 turn；如果没有这行，列表字段 last_turn_id 不稳定。
        manager._touch_session(session)  # 新增代码+DesktopGUISessionSearchTest：刷新更新时间；如果没有这行，排序相关断言可能依赖创建顺序。
    # 新增代码+DesktopGUISessionSearchTest：helper 段结束，_seed_session 到此结束；如果没有边界说明，初学者不易看出它只负责测试数据。

    def _start_server(self, workspace: Path):  # 新增代码+DesktopGUISessionSearchTest：helper 段开始，启动带 token 的测试 server；如果没有这个 helper，每个测试都要重复端口和线程逻辑。
        server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUISessionSearchTest：绑定随机端口并固定 token；如果没有这行，测试容易端口冲突或 token 不稳定。
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUISessionSearchTest：创建后台服务线程；如果没有这行，HTTP 请求无法同时发出。
        thread.start()  # 新增代码+DesktopGUISessionSearchTest：启动 server 线程；如果没有这行，urllib 会连接失败。
        return server  # 新增代码+DesktopGUISessionSearchTest：返回 server 供测试拼 URL 和关闭；如果没有这行，调用方拿不到端口。
    # 新增代码+DesktopGUISessionSearchTest：helper 段结束，_start_server 到此结束；如果没有边界说明，初学者不易看出它只负责启动服务。

    def _url(self, server, path: str) -> str:  # 新增代码+DesktopGUISessionSearchTest：helper 段开始，拼接 server URL；如果没有这段，随机端口读取会散落各处。
        host, port = server.server_address  # 新增代码+DesktopGUISessionSearchTest：读取真实监听地址；如果没有这行，端口 0 场景无法请求。
        return f"http://{host}:{port}{path}"  # 新增代码+DesktopGUISessionSearchTest：返回完整 URL；如果没有这行，urllib 没有目标地址。
    # 新增代码+DesktopGUISessionSearchTest：helper 段结束，_url 到此结束；如果没有边界说明，初学者不易看出它只负责拼 URL。

    def _get_json(self, server, path: str) -> dict[str, object]:  # 新增代码+DesktopGUISessionSearchTest：helper 段开始，发送带 token 的 GET；如果没有这段，sessions/search 请求会重复写法。
        request = urllib.request.Request(self._url(server, path), headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUISessionSearchTest：构造带 token 的 GET 请求；如果没有这行，安全 endpoint 会返回 401。
        with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUISessionSearchTest：发送 GET 请求；如果没有这行，测试不会读取 bridge 状态。
            return json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUISessionSearchTest：解析 JSON 响应；如果没有这行，断言无法读取字段。
    # 新增代码+DesktopGUISessionSearchTest：helper 段结束，_get_json 到此结束；如果没有边界说明，初学者不易看出它只负责 GET。

    def _post_json(self, server, path: str, payload: dict[str, object]) -> dict[str, object]:  # 新增代码+DesktopGUISessionSearchTest：helper 段开始，发送 JSON POST；如果没有这段，每个写入接口都要重复编码和 header。
        request = urllib.request.Request(self._url(server, path), data=json.dumps(payload).encode("utf-8"), method="POST", headers={"Content-Type": "application/json", "X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUISessionSearchTest：构造带 token 的 JSON 请求；如果没有这行，安全门禁会拒绝请求。
        with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUISessionSearchTest：发送请求并读取响应；如果没有这行，测试不会真正触发 endpoint。
            return json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUISessionSearchTest：返回 JSON 对象；如果没有这行，断言无法检查字段。
    # 新增代码+DesktopGUISessionSearchTest：helper 段结束，_post_json 到此结束；如果没有边界说明，初学者不易看出它只负责 POST。

    def test_sessions_list_returns_stable_fields_and_hides_archived(self) -> None:  # 新增代码+DesktopGUISessionSearchTest：测试段开始，验证 V2 sessions 默认隐藏归档并返回稳定字段；如果没有这段，侧栏合同容易退化。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUISessionSearchTest：创建临时工作区；如果没有这行，测试会写入真实 memory。
            manager = GuiRunManager(Path(directory))  # 新增代码+DesktopGUISessionSearchTest：创建隔离 manager；如果没有这行，无法直接验证 sessions_payload。
            self._seed_session(manager, "session_keep", "请总结这个项目", "这是一个 OpenHarness 桌面 GUI 项目。")  # 新增代码+DesktopGUISessionSearchTest：写入保留会话；如果没有这行，列表没有可见样本。
            self._seed_session(manager, "session_archive", "需要归档的旧会话", "这条会话应默认隐藏。")  # 新增代码+DesktopGUISessionSearchTest：写入归档候选；如果没有这行，归档隐藏无法验证。
            manager.archive_session("session_archive", archived=True)  # 新增代码+DesktopGUISessionSearchTest：归档第二个会话；如果没有这行，默认隐藏场景没有事实。
            payload = manager.sessions_payload()  # 新增代码+DesktopGUISessionSearchTest：读取默认会话列表；如果没有这行，无法断言 payload 形状。
            all_payload = manager.sessions_payload(include_archived=True)  # 新增代码+DesktopGUISessionSearchTest：读取包含归档的列表；如果没有这行，归档入口无法验证。
        self.assertEqual(payload["schema_version"], 2)  # 新增代码+DesktopGUISessionSearchTest：确认 V2 schema 版本；如果没有这行，前端无法判断合同版本。
        self.assertEqual([session["session_id"] for session in payload["sessions"]], ["session_keep"])  # 新增代码+DesktopGUISessionSearchTest：确认默认列表隐藏归档；如果没有这行，archive 退化不会被发现。
        self.assertEqual(payload["archived_count"], 1)  # 新增代码+DesktopGUISessionSearchTest：确认归档计数；如果没有这行，侧栏归档入口可能显示假数字。
        self.assertEqual({session["session_id"] for session in all_payload["sessions"]}, {"session_keep", "session_archive"})  # 新增代码+DesktopGUISessionSearchTest：确认包含归档时能找回全部会话；如果没有这行，归档视图无法工作。
        self.assertIn("请总结这个项目", payload["sessions"][0]["title"])  # 新增代码+DesktopGUISessionSearchTest：确认标题来自用户文本；如果没有这行，侧栏可能只显示 session id。
        self.assertIn("OpenHarness", payload["sessions"][0]["subtitle"])  # 新增代码+DesktopGUISessionSearchTest：确认副标题带最近摘要；如果没有这行，最近会话缺少上下文。
    # 新增代码+DesktopGUISessionSearchTest：测试段结束，sessions 列表字段合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_rename_and_archive_update_session_state(self) -> None:  # 新增代码+DesktopGUISessionSearchTest：测试段开始，验证 rename/archive 会真实更新后端状态；如果没有这段，按钮可能只有前端效果。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUISessionSearchTest：创建临时工作区；如果没有这行，测试会污染真实状态。
            manager = GuiRunManager(Path(directory))  # 新增代码+DesktopGUISessionSearchTest：创建隔离 manager；如果没有这行，无法验证写入行为。
            self._seed_session(manager, "session_alpha", "原始标题", "原始回答")  # 新增代码+DesktopGUISessionSearchTest：写入测试会话；如果没有这行，rename/archive 没有目标。
            renamed = manager.rename_session("session_alpha", "新的成熟 GUI 蓝图")  # 新增代码+DesktopGUISessionSearchTest：执行改名；如果没有这行，无法验证 title 持久字段。
            archived = manager.archive_session("session_alpha", archived=True)  # 新增代码+DesktopGUISessionSearchTest：执行归档；如果没有这行，无法验证 archived 字段。
            payload = manager.sessions_payload()  # 新增代码+DesktopGUISessionSearchTest：读取默认列表；如果没有这行，无法确认归档隐藏。
        self.assertEqual(renamed["session"]["title"], "新的成熟 GUI 蓝图")  # 新增代码+DesktopGUISessionSearchTest：确认改名结果；如果没有这行，rename 可能没有写入。
        self.assertIs(archived["archived"], True)  # 新增代码+DesktopGUISessionSearchTest：确认归档结果；如果没有这行，archive 响应可能不可信。
        self.assertEqual(payload["sessions"], [])  # 新增代码+DesktopGUISessionSearchTest：确认归档后默认列表为空；如果没有这行，侧栏仍可能显示已归档会话。
    # 新增代码+DesktopGUISessionSearchTest：测试段结束，rename/archive 状态合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_search_returns_matching_session_ids_and_message_snippets(self) -> None:  # 新增代码+DesktopGUISessionSearchTest：测试段开始，验证搜索返回 session id 和消息片段；如果没有这段，搜索可能退化成只返回标题。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUISessionSearchTest：创建临时工作区；如果没有这行，测试会污染真实状态。
            manager = GuiRunManager(Path(directory))  # 新增代码+DesktopGUISessionSearchTest：创建隔离 manager；如果没有这行，无法构造搜索事实源。
            self._seed_session(manager, "session_gui", "请做 Codex GUI 外壳", "搜索应该命中 Codex 成熟外壳片段。")  # 新增代码+DesktopGUISessionSearchTest：写入命中会话；如果没有这行，搜索没有目标文本。
            self._seed_session(manager, "session_other", "普通问题", "这条回答不应该命中。")  # 新增代码+DesktopGUISessionSearchTest：写入不命中会话；如果没有这行，无法验证过滤。
            payload = manager.search_sessions("成熟外壳")  # 新增代码+DesktopGUISessionSearchTest：执行搜索；如果没有这行，无法断言结果。
        self.assertEqual(payload["query"], "成熟外壳")  # 新增代码+DesktopGUISessionSearchTest：确认 query 原样返回；如果没有这行，前端无法对齐当前搜索词。
        self.assertEqual([result["session_id"] for result in payload["results"]], ["session_gui"])  # 新增代码+DesktopGUISessionSearchTest：确认只返回命中会话；如果没有这行，无关会话可能污染搜索结果。
        self.assertIn("成熟外壳", payload["results"][0]["snippet"])  # 新增代码+DesktopGUISessionSearchTest：确认片段包含命中文本；如果没有这行，搜索结果缺少为什么命中的解释。
    # 新增代码+DesktopGUISessionSearchTest：测试段结束，搜索结果合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_v2_http_sessions_rename_archive_and_search_routes(self) -> None:  # 新增代码+DesktopGUISessionSearchTest：测试段开始，验证真实 HTTP V2 路由；如果没有这段，manager 通过但 handler 可能没接线。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUISessionSearchTest：创建临时工作区；如果没有这行，测试会写入真实 memory。
            server = self._start_server(Path(directory))  # 新增代码+DesktopGUISessionSearchTest：启动 GUI bridge；如果没有这行，测试没有目标服务。
            try:  # 新增代码+DesktopGUISessionSearchTest：确保 server 最终关闭；如果没有这行，失败时端口会泄漏。
                self._seed_session(server.run_manager, "session_http", "HTTP 搜索原始标题", "HTTP 搜索应该返回这个片段。")  # 新增代码+DesktopGUISessionSearchTest：直接向 server manager 写入会话；如果没有这行，HTTP 列表没有样本。
                sessions = self._get_json(server, "/v2/gui/sessions")  # 新增代码+DesktopGUISessionSearchTest：请求 V2 sessions；如果没有这行，无法验证 GET 路由。
                rename = self._post_json(server, "/v2/gui/sessions/session_http/rename", {"title": "HTTP 改名标题"})  # 新增代码+DesktopGUISessionSearchTest：请求 V2 rename；如果没有这行，无法验证改名路由。
                encoded_query = urllib.parse.quote("改名标题")  # 新增代码+DesktopGUISessionSearchTest：编码中文搜索词；如果没有这行，URL query 可能不合法。
                search = self._get_json(server, f"/v2/gui/search?q={encoded_query}")  # 新增代码+DesktopGUISessionSearchTest：请求 V2 search；如果没有这行，无法验证搜索路由。
                archive = self._post_json(server, "/v2/gui/sessions/session_http/archive", {"archived": True})  # 新增代码+DesktopGUISessionSearchTest：请求 V2 archive；如果没有这行，无法验证归档路由。
                after_archive = self._get_json(server, "/v2/gui/sessions")  # 新增代码+DesktopGUISessionSearchTest：归档后再读列表；如果没有这行，无法验证默认隐藏。
            finally:  # 新增代码+DesktopGUISessionSearchTest：清理 server；如果没有这行，后台线程和端口可能残留。
                server.shutdown()  # 新增代码+DesktopGUISessionSearchTest：停止 serve_forever；如果没有这行，测试进程可能挂住。
                server.server_close()  # 新增代码+DesktopGUISessionSearchTest：释放 socket；如果没有这行，Windows 端口可能短时间占用。
        self.assertEqual(sessions["sessions"][0]["session_id"], "session_http")  # 新增代码+DesktopGUISessionSearchTest：确认 V2 sessions 返回会话；如果没有这行，GET 路由可能空跑。
        self.assertEqual(rename["session"]["title"], "HTTP 改名标题")  # 新增代码+DesktopGUISessionSearchTest：确认 HTTP rename 返回新标题；如果没有这行，POST 路由可能没调用 manager。
        self.assertEqual(search["results"][0]["session_id"], "session_http")  # 新增代码+DesktopGUISessionSearchTest：确认 HTTP search 可搜改名标题；如果没有这行，搜索和改名状态可能没有打通。
        self.assertIs(archive["archived"], True)  # 新增代码+DesktopGUISessionSearchTest：确认 HTTP archive 返回归档状态；如果没有这行，归档结果不可信。
        self.assertEqual(after_archive["sessions"], [])  # 新增代码+DesktopGUISessionSearchTest：确认归档后默认列表隐藏；如果没有这行，侧栏仍可能显示归档会话。
    # 新增代码+DesktopGUISessionSearchTest：测试段结束，HTTP V2 路由合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


if __name__ == "__main__":  # 新增代码+DesktopGUISessionSearchTest：允许直接运行本文件；如果没有这行，手动调试只能用模块命令。
    unittest.main()  # 新增代码+DesktopGUISessionSearchTest：启动 unittest runner；如果没有这行，直接运行文件不会执行测试。
