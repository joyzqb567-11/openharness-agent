"""Chrome 扩展只读 bridge 状态。"""  # 新增代码+ChromeExtensionStage5: 说明本文件提供 provider 可读的 bridge state；若没有这行代码，运行时边界不清楚。
from __future__ import annotations  # 新增代码+ChromeExtensionStage5: 延迟解析类型注解；若没有这行代码，类内类型引用更脆弱。

import time  # 新增代码+ChromeExtensionStage5: 记录连接和消息时间；若没有这行代码，状态无法判断新旧。
from pathlib import Path  # 新增代码+ChromeExtensionStage5: 处理 bridge 状态文件路径；若没有这行代码，路径逻辑不稳定。
from typing import Any  # 新增代码+ChromeExtensionStage5: 状态和响应使用通用 JSON 值；若没有这行代码，类型边界不清晰。
from uuid import uuid4  # 新增代码+ChromeExtensionStage6: 生成稳定且不易冲突的写动作 command_id；若没有这行代码，命令结果可能互相覆盖。

from .message_protocol import build_host_response, build_write_command  # 修改代码+ChromeExtensionStage6: 复用只读响应和写命令协议；若没有这行代码，bridge 和 host 会出现两套过滤逻辑。
from .pairing_store import ChromeExtensionPairingStore  # 新增代码+ChromeExtensionStage5: 复用配对状态持久化；若没有这行代码，连接状态无法落盘。


class ChromeExtensionBridgeState:  # 新增代码+ChromeExtensionStage5: 保存 Chrome 扩展只读连接状态；若没有这个类，provider 无法读取插件结果。
    def __init__(self, path: Path) -> None:  # 新增代码+ChromeExtensionStage5: 初始化 bridge 状态文件；若没有这行代码，调用方无法创建状态对象。
        self.store = ChromeExtensionPairingStore(Path(path))  # 新增代码+ChromeExtensionStage5: 创建文件 store；若没有这行代码，状态无法持久化。
        self.state = self.store.load()  # 新增代码+ChromeExtensionStage5: 启动时读取旧状态；若没有这行代码，host 重启后状态丢失。

    def _save(self) -> None:  # 新增代码+ChromeExtensionStage5: 保存当前状态；若没有这行代码，多处保存会重复写 store 调用。
        self.store.save(self.state)  # 新增代码+ChromeExtensionStage5: 委托 store 写文件；若没有这行代码，状态变化不会落盘。

    def _pending_list(self) -> list[dict[str, Any]]:  # 新增代码+ChromeExtensionStage6: 读取待执行命令列表并保证类型安全；若没有这行代码，坏状态可能让 provider 崩溃。
        pending = self.state.get("pending_commands", [])  # 新增代码+ChromeExtensionStage6: 从状态中读取 pending commands；若没有这行代码，命令队列没有来源。
        return pending if isinstance(pending, list) else []  # 新增代码+ChromeExtensionStage6: 非列表状态兜底为空；若没有这行代码，历史坏 JSON 会导致遍历异常。

    def _result_map(self) -> dict[str, dict[str, Any]]:  # 新增代码+ChromeExtensionStage6: 读取命令结果映射并保证类型安全；若没有这行代码，结果消费会重复写防御逻辑。
        results = self.state.get("command_results", {})  # 新增代码+ChromeExtensionStage6: 从状态中读取结果表；若没有这行代码，provider 没有结果来源。
        return results if isinstance(results, dict) else {}  # 新增代码+ChromeExtensionStage6: 非字典状态兜底为空；若没有这行代码，坏状态会导致 get 异常。

    def record_connection(self, extension_id: str) -> None:  # 新增代码+ChromeExtensionStage5: 标记扩展已连接；若没有这行代码，provider 永远不可用。
        self.state["connected"] = True  # 新增代码+ChromeExtensionStage5: 保存连接布尔值；若没有这行代码，health 无法变为可用。
        self.state["extension_id"] = str(extension_id or "")  # 新增代码+ChromeExtensionStage5: 保存扩展 id 摘要；若没有这行代码，状态无法显示连接来源。
        self.state["last_seen_at"] = int(time.time())  # 新增代码+ChromeExtensionStage5: 保存最近连接时间；若没有这行代码，状态无法判断是否陈旧。
        self._save()  # 新增代码+ChromeExtensionStage5: 立即落盘；若没有这行代码，进程重启后连接摘要丢失。

    def record_disconnect(self, reason: str = "") -> None:  # 新增代码+ChromeExtensionStage5: 标记扩展断开；若没有这行代码，断线后会误报可用。
        self.state["connected"] = False  # 新增代码+ChromeExtensionStage5: 保存断开状态；若没有这行代码，health 会继续可用。
        self.state["disconnect_reason"] = str(reason or "")  # 新增代码+ChromeExtensionStage5: 保存断开原因；若没有这行代码，用户不知道为什么不可用。
        self.state["last_seen_at"] = int(time.time())  # 新增代码+ChromeExtensionStage5: 更新时间；若没有这行代码，状态新旧不可见。
        self._save()  # 新增代码+ChromeExtensionStage5: 立即落盘；若没有这行代码，断开状态可能丢失。

    def record_pairing(self, pairing: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase2Pairing: 保存 Chrome 扩展配对摘要；如果没有这段函数，extension id/device/session 无法形成可审计连接。
        safe_pairing = self.store.save_pairing(dict(pairing or {}))  # 新增代码+Phase2Pairing: 委托 store 脱敏保存 pairing；如果没有这行代码，token/cookie 可能进入状态文件。
        self.state = self.store.load()  # 新增代码+Phase2Pairing: 重新加载落盘状态；如果没有这行代码，内存状态会和文件状态不一致。
        self.state["connected"] = True  # 新增代码+Phase2Pairing: 配对成功意味着 extension/host 有连接；如果没有这行代码，provider 仍可能显示未连接。
        self.state["extension_id"] = str(safe_pairing.get("extension_id", self.state.get("extension_id", "")) or "")  # 新增代码+Phase2Pairing: 同步 extension id 到顶层状态；如果没有这行代码，旧状态 UI 看不到扩展来源。
        self.state["last_seen_at"] = int(time.time())  # 新增代码+Phase2Pairing: 更新时间；如果没有这行代码，状态无法判断配对是否新鲜。
        pending_request = self.state.get("pending_pairing_request", {}) if isinstance(self.state.get("pending_pairing_request", {}), dict) else {}  # 新增代码+Phase15ChromePairingTrigger: 读取待配对请求；如果没有这行代码，扩展回传后 pending 状态无法关闭。
        request_id = str(safe_pairing.get("request_id", "") or "")  # 新增代码+Phase15ChromePairingTrigger: 读取扩展回传的请求 id；如果没有这行代码，无法确认本次配对对应哪次触发。
        if pending_request and (not request_id or request_id == str(pending_request.get("request_id", "") or "")):  # 新增代码+Phase15ChromePairingTrigger: 匹配请求或兼容旧扩展无 request_id；如果没有这行代码，触发后的配对会一直显示 pending。
            pending_request["status"] = "completed"  # 新增代码+Phase15ChromePairingTrigger: 标记请求已被扩展完成；如果没有这行代码，/chrome 会误报仍在等待。
            pending_request["completed_at"] = int(time.time())  # 新增代码+Phase15ChromePairingTrigger: 记录完成时间；如果没有这行代码，用户无法判断完成是否刚发生。
            pending_request["paired_session_id"] = str(safe_pairing.get("session_id", "") or "")  # 新增代码+Phase15ChromePairingTrigger: 关联完成的 session；如果没有这行代码，审计时无法把请求和 session sync 连起来。
            self.state["pending_pairing_request"] = pending_request  # 新增代码+Phase15ChromePairingTrigger: 写回更新后的请求状态；如果没有这行代码，completed 字段不会落盘。
        self._save()  # 新增代码+Phase2Pairing: 保存 connected 和 last_seen；如果没有这行代码，配对后状态可能丢失。
        return safe_pairing  # 新增代码+Phase2Pairing: 返回脱敏 pairing；如果没有这行代码，调用方无法确认保存了哪些字段。

    def start_pairing_request(self, source: str = "terminal") -> dict[str, Any]:  # 新增代码+Phase15ChromePairingTrigger: 创建待 Chrome 扩展处理的配对请求；如果没有这段函数，终端无法安全触发配对刷新。
        now = int(time.time())  # 新增代码+Phase15ChromePairingTrigger: 记录请求创建时间；如果没有这行代码，用户无法判断请求是否陈旧。
        request = {"request_id": f"chrome-pair-{now}-{uuid4().hex[:8]}", "request_nonce": uuid4().hex, "status": "pending", "source": str(source or "terminal")[:120], "created_at": now}  # 新增代码+Phase15ChromePairingTrigger: 生成可审计请求和 nonce；如果没有这行代码，扩展侧无法区分不同配对触发。
        self.state["pending_pairing_request"] = request  # 新增代码+Phase15ChromePairingTrigger: 保存待处理请求；如果没有这行代码，native host 轮询时没有请求可下发。
        self.state["last_seen_at"] = now  # 新增代码+Phase15ChromePairingTrigger: 更新时间；如果没有这行代码，状态页不知道触发刚发生。
        self._save()  # 新增代码+Phase15ChromePairingTrigger: 立即落盘；如果没有这行代码，终端确认后重启会丢失配对请求。
        return request  # 新增代码+Phase15ChromePairingTrigger: 返回请求摘要；如果没有这行代码，终端无法展示 request id 和 nonce。

    def pairing_request_summary(self) -> dict[str, Any]:  # 新增代码+Phase15ChromePairingTrigger: 返回当前配对请求摘要；如果没有这段函数，状态页和测试都要直接读内部 state。
        request = self.state.get("pending_pairing_request", {})  # 新增代码+Phase15ChromePairingTrigger: 读取请求对象；如果没有这行代码，summary 没有数据来源。
        return request if isinstance(request, dict) else {}  # 新增代码+Phase15ChromePairingTrigger: 非字典时兜底为空；如果没有这行代码，坏状态会拖垮状态 UI。

    def pending_pairing_request(self) -> dict[str, Any]:  # 新增代码+Phase15ChromePairingTrigger: 给 native host 轮询响应提供待处理请求；如果没有这段函数，扩展拿不到终端触发信号。
        request = self.pairing_request_summary()  # 新增代码+Phase15ChromePairingTrigger: 复用摘要读取；如果没有这行代码，状态读取逻辑会重复。
        return request if str(request.get("status", "") or "") == "pending" else {}  # 新增代码+Phase15ChromePairingTrigger: 只下发 pending 请求；如果没有这行代码，已完成请求会被扩展重复处理。

    def pairing_summary(self) -> dict[str, Any]:  # 新增代码+Phase2Pairing: 返回当前配对摘要；如果没有这段函数，status_text 需要直接读 store 内部结构。
        pairing = self.state.get("pairing", {})  # 新增代码+Phase2Pairing: 从内存状态读取 pairing；如果没有这行代码，summary 没有数据来源。
        if isinstance(pairing, dict):  # 新增代码+Phase2Pairing: 只接受字典 pairing；如果没有这行代码，坏状态可能传到 UI。
            return pairing  # 新增代码+Phase2Pairing: 返回配对摘要；如果没有这行代码，调用方拿不到 device/session。
        return {}  # 新增代码+Phase2Pairing: 坏状态返回空；如果没有这行代码，状态工具可能崩溃。

    def session_sync_status_text(self) -> str:  # 新增代码+Phase2Pairing: 输出 session sync 人类可读状态；如果没有这段函数，/chrome 状态无法展示配对细节。
        pairing = self.pairing_summary()  # 新增代码+Phase2Pairing: 读取配对摘要；如果没有这行代码，状态文本无法显示 device/session。
        paired = bool(pairing.get("device_id") or pairing.get("session_id") or pairing.get("extension_id"))  # 新增代码+Phase2Pairing: 判断是否已配对；如果没有这行代码，UI 只能靠 connected 猜测。
        allowed_origins = pairing.get("allowed_origins", []) if isinstance(pairing.get("allowed_origins", []), list) else []  # 新增代码+Phase2Pairing: 读取允许 origin；如果没有这行代码，状态无法说明配对边界。
        return "\n".join(["browser_extension_session_sync", f"paired={str(paired).lower()}", f"connected={str(self.connected()).lower()}", f"device_id={pairing.get('device_id', '')}", f"session_id={pairing.get('session_id', '')}", f"extension_id={pairing.get('extension_id', self.state.get('extension_id', ''))}", f"allowed_origin_count={len(allowed_origins)}", f"last_seen_at={self.state.get('last_seen_at', '')}"])  # 新增代码+Phase2Pairing: 返回稳定多行状态；如果没有这行代码，验收器无法匹配配对字段。

    def enqueue_browser_prompt(self, command_queue: Any, message: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase2Pairing: 把浏览器侧 prompt 写入 durable queue；如果没有这段函数，扩展发起任务会绕过主循环。
        safe_message = dict(message or {})  # 新增代码+Phase2Pairing: 复制输入消息；如果没有这行代码，清理过程可能修改调用方对象。
        prompt = str(safe_message.get("prompt", "") or "").strip()  # 新增代码+Phase2Pairing: 读取用户在浏览器侧输入的 prompt；如果没有这行代码，队列没有任务正文。
        if not prompt:  # 新增代码+Phase2Pairing: 空 prompt 不应入队；如果没有这行代码，主循环会收到无意义任务。
            raise RuntimeError("browser_prompt 缺少 prompt。")  # 新增代码+Phase2Pairing: 返回清楚错误；如果没有这行代码，扩展侧不知道如何修复。
        url = str(safe_message.get("url", "") or "")[:2000]  # 新增代码+Phase2Pairing: 读取页面 URL 并截断；如果没有这行代码，agent 不知道任务来自哪个页面。
        title = str(safe_message.get("title", "") or "")[:500]  # 新增代码+Phase2Pairing: 读取页面标题并截断；如果没有这行代码，任务上下文不易读。
        selected_text = str(safe_message.get("selected_text", "") or "")[:2000]  # 新增代码+Phase2Pairing: 读取选中文本并截断；如果没有这行代码，用户选区不会进入任务上下文。
        tab_id = str(safe_message.get("tab_id", "") or "")[:200]  # 新增代码+Phase2Pairing: 读取 tab id；如果没有这行代码，后续无法关联标签页。
        composed_prompt = "\n".join([prompt, "", "[Chrome 页面上下文]", f"URL: {url}", f"Title: {title}", f"Tab: {tab_id}", f"Selected: {selected_text}"]).strip()  # 新增代码+Phase2Pairing: 合成给主循环的 prompt；如果没有这行代码，页面上下文和用户意图会分离。
        command = command_queue.enqueue_prompt(composed_prompt, priority="next")  # 新增代码+Phase2Pairing: 写入 durable RuntimeCommandQueue；如果没有这行代码，浏览器任务重启后会丢失。
        self.state["last_browser_prompt_id"] = command.command_id  # 新增代码+Phase2Pairing: 保存最近 browser prompt id；如果没有这行代码，状态 UI 无法关联队列命令。
        self.state["last_browser_prompt_url"] = url  # 新增代码+Phase2Pairing: 保存最近来源 URL；如果没有这行代码，状态 UI 不知道 prompt 来自哪里。
        self.state["last_seen_at"] = int(time.time())  # 新增代码+Phase2Pairing: 更新时间；如果没有这行代码，状态无法判断 prompt 是否新鲜。
        self._save()  # 新增代码+Phase2Pairing: 落盘 prompt 摘要；如果没有这行代码，重启后状态丢失。
        return {"ok": True, "mode": "browser_prompt", "command_id": command.command_id, "url": url, "title": title}  # 新增代码+Phase2Pairing: 返回安全结果摘要；如果没有这行代码，扩展侧不知道入队是否成功。

    def update_tabs_context(self, message: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage5: 保存扩展发来的 tabs_context；若没有这行代码，provider 无 context 可读。
        response = build_host_response({"action": "tabs_context", **dict(message or {})})  # 新增代码+ChromeExtensionStage5: 用协议过滤输入；若没有这行代码，敏感字段可能进入状态。
        self.state["last_tabs_context"] = response  # 新增代码+ChromeExtensionStage5: 保存最近 tabs context；若没有这行代码，provider 无法返回标签页列表。
        self.state["last_seen_at"] = int(time.time())  # 新增代码+ChromeExtensionStage5: 更新时间；若没有这行代码，状态无法判断新旧。
        self._save()  # 新增代码+ChromeExtensionStage5: 保存到文件；若没有这行代码，context 不可恢复。
        return response  # 新增代码+ChromeExtensionStage5: 返回协议响应；若没有这行代码，调用方无法检查结果。

    def update_page_snapshot(self, message: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage5: 保存扩展发来的页面只读快照；若没有这行代码，provider 无法返回 browser_snapshot。
        response = build_host_response({"action": "read_page", **dict(message or {})})  # 新增代码+ChromeExtensionStage5: 用协议过滤页面输入；若没有这行代码，页面消息可能带入敏感字段。
        self.state["last_page_snapshot"] = response  # 新增代码+ChromeExtensionStage5: 保存最近页面快照；若没有这行代码，snapshot 工具无数据。
        self.state["last_seen_at"] = int(time.time())  # 新增代码+ChromeExtensionStage5: 更新时间；若没有这行代码，状态无法判断新旧。
        self._save()  # 新增代码+ChromeExtensionStage5: 保存到文件；若没有这行代码，snapshot 不可恢复。
        return response  # 新增代码+ChromeExtensionStage5: 返回协议响应；若没有这行代码，调用方无法检查结果。

    def enqueue_command(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage6: 把统一 browser 写工具变成等待扩展执行的命令；若没有这行代码，provider 无法把 click/type 发给插件。
        command_id = f"chrome-ext-{int(time.time() * 1000)}-{uuid4().hex[:8]}"  # 新增代码+ChromeExtensionStage6: 生成带时间前缀的 command id；若没有这行代码，动作结果无法稳定关联。
        command = build_write_command(tool_name, dict(arguments or {}), command_id=command_id)  # 新增代码+ChromeExtensionStage6: 用协议层构造安全命令；若没有这行代码，bridge 会重复映射和过滤字段。
        if not command.get("ok", False):  # 新增代码+ChromeExtensionStage6: 如果协议拒绝工具则立即停止；若没有这行代码，不支持的工具会进入 pending 队列。
            raise RuntimeError(str(command.get("error", "Chrome 插件命令构造失败。")))  # 新增代码+ChromeExtensionStage6: 抛出清楚错误；若没有这行代码，调用方会误以为命令已发送。
        command["created_at"] = int(time.time())  # 新增代码+ChromeExtensionStage6: 记录命令创建时间；若没有这行代码，状态页无法判断命令是否陈旧。
        pending = self._pending_list()  # 新增代码+ChromeExtensionStage6: 读取当前 pending 队列；若没有这行代码，会覆盖已有命令。
        pending.append(command)  # 新增代码+ChromeExtensionStage6: 把新命令追加到队列；若没有这行代码，扩展永远拉不到动作。
        self.state["pending_commands"] = pending[-100:]  # 新增代码+ChromeExtensionStage6: 限制队列长度保留最近 100 条；若没有这行代码，长期运行会无限增长。
        self.state["last_command"] = command  # 新增代码+ChromeExtensionStage6: 保存最近命令摘要；若没有这行代码，状态工具看不到刚刚发了什么。
        self.state["last_seen_at"] = int(time.time())  # 新增代码+ChromeExtensionStage6: 更新时间；若没有这行代码，状态新旧不可见。
        self._save()  # 新增代码+ChromeExtensionStage6: 立即落盘；若没有这行代码，扩展进程无法从文件看到命令。
        return command  # 新增代码+ChromeExtensionStage6: 返回命令给 provider；若没有这行代码，provider 拿不到 command_id。

    def pending_commands(self) -> list[dict[str, Any]]:  # 新增代码+ChromeExtensionStage6: 返回扩展可拉取的 pending 命令；若没有这行代码，native host 无法回复 poll_commands。
        return [dict(command) for command in self._pending_list()]  # 新增代码+ChromeExtensionStage6: 返回副本避免调用方污染内部状态；若没有这行代码，测试或 host 可能误改队列。

    def record_command_result(self, message: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage6: 保存扩展回传的写动作结果；若没有这行代码，provider 等不到 click/type 完成。
        response = build_host_response({"action": "action_result", **dict(message or {})})  # 新增代码+ChromeExtensionStage6: 用协议清理动作结果；若没有这行代码，敏感字段可能进入状态文件。
        command_id = str(response.get("command_id", "") or "")  # 新增代码+ChromeExtensionStage6: 读取结果对应的 command id；若没有这行代码，结果无法放入映射。
        if not command_id:  # 新增代码+ChromeExtensionStage6: 缺 command id 时拒绝保存；若没有这行代码，多个无 id 结果会互相覆盖。
            raise RuntimeError("Chrome 插件动作结果缺少 command_id。")  # 新增代码+ChromeExtensionStage6: 返回清楚错误；若没有这行代码，调用方不知道结果格式问题。
        results = self._result_map()  # 新增代码+ChromeExtensionStage6: 读取当前结果映射；若没有这行代码，会覆盖已有结果。
        results[command_id] = response  # 新增代码+ChromeExtensionStage6: 按 command id 保存结果；若没有这行代码，provider 无法消费结果。
        pending = [command for command in self._pending_list() if str(command.get("command_id", "")) != command_id]  # 新增代码+ChromeExtensionStage6: 从 pending 队列移除已完成命令；若没有这行代码，扩展会重复执行同一动作。
        self.state["pending_commands"] = pending  # 新增代码+ChromeExtensionStage6: 保存移除后的 pending 队列；若没有这行代码，状态不会更新。
        self.state["command_results"] = results  # 新增代码+ChromeExtensionStage6: 保存结果映射；若没有这行代码，结果无法持久化。
        self.state["last_command_result"] = response  # 新增代码+ChromeExtensionStage6: 保存最近结果摘要；若没有这行代码，状态工具无法展示最后一次动作结果。
        self.state["last_seen_at"] = int(time.time())  # 新增代码+ChromeExtensionStage6: 更新时间；若没有这行代码，状态新旧不可见。
        self._save()  # 新增代码+ChromeExtensionStage6: 立即落盘；若没有这行代码，provider 轮询不到结果。
        return response  # 新增代码+ChromeExtensionStage6: 返回清理后的结果；若没有这行代码，host 无法回复扩展。

    def consume_command_result(self, command_id: str) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage6: 读取并移除某个命令结果；若没有这行代码，provider 无法同步收尾。
        safe_command_id = str(command_id or "")  # 新增代码+ChromeExtensionStage6: 规范化 command id；若没有这行代码，None 会变成异常。
        results = self._result_map()  # 新增代码+ChromeExtensionStage6: 读取当前结果映射；若没有这行代码，消费逻辑没有数据来源。
        if safe_command_id not in results:  # 新增代码+ChromeExtensionStage6: 结果尚未到达时直接返回空；若没有这行代码，等待循环会频繁无意义写磁盘。
            return {}  # 新增代码+ChromeExtensionStage6: 空字典表示还没有结果；若没有这行代码，provider 无法区分等待中和失败结果。
        result = results.pop(safe_command_id, {})  # 新增代码+ChromeExtensionStage6: 移除并返回结果；若没有这行代码，同一结果会被重复消费。
        self.state["command_results"] = results  # 新增代码+ChromeExtensionStage6: 保存移除后的结果表；若没有这行代码，消费不会持久化。
        self._save()  # 新增代码+ChromeExtensionStage6: 立即落盘；若没有这行代码，重启后旧结果仍存在。
        return result if isinstance(result, dict) else {}  # 新增代码+ChromeExtensionStage6: 返回字典结果或空字典；若没有这行代码，坏状态会传给 provider。

    def wait_for_command_result(self, command_id: str, timeout_seconds: float) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage6: 在 provider 同步工具调用里等待扩展结果；若没有这行代码，execute_tool 只能返回“已发送”而不能证明完成。
        deadline = time.time() + max(0.01, float(timeout_seconds or 0.01))  # 新增代码+ChromeExtensionStage6: 计算等待截止时间；若没有这行代码，超时控制不稳定。
        while time.time() < deadline:  # 新增代码+ChromeExtensionStage6: 在预算内轮询结果；若没有这行代码，provider 不会等待扩展执行。
            result = self.consume_command_result(command_id)  # 新增代码+ChromeExtensionStage6: 尝试消费结果；若没有这行代码，循环没有检查目标。
            if result:  # 新增代码+ChromeExtensionStage6: 有结果时立即返回；若没有这行代码，成功也会等到超时。
                return result  # 新增代码+ChromeExtensionStage6: 返回动作结果；若没有这行代码，provider 拿不到页面反馈。
            time.sleep(0.02)  # 新增代码+ChromeExtensionStage6: 短暂休眠避免忙等；若没有这行代码，轮询会浪费 CPU。
        raise TimeoutError(f"等待 Chrome 插件命令结果超时：{command_id}")  # 新增代码+ChromeExtensionStage6: 超时后清楚失败；若没有这行代码，调用方不知道动作是否执行。

    def command_status_text(self) -> str:  # 新增代码+ChromeExtensionStage6: 输出最近命令和结果的人类可读状态；若没有这行代码，调试插件写动作只能翻 JSON。
        last_command = self.state.get("last_command", {}) if isinstance(self.state.get("last_command", {}), dict) else {}  # 新增代码+ChromeExtensionStage6: 读取最近命令；若没有这行代码，状态输出缺命令来源。
        last_result = self.state.get("last_command_result", {}) if isinstance(self.state.get("last_command_result", {}), dict) else {}  # 新增代码+ChromeExtensionStage6: 读取最近结果；若没有这行代码，状态输出缺结果。
        return "\n".join(["browser_extension_command_status", f"pending_count={len(self._pending_list())}", f"last_command_id={last_command.get('command_id', '')}", f"last_tool={last_command.get('tool_name', '')}", f"last_result_ok={str(bool(last_result.get('ok', False))).lower()}", f"last_result_tool={last_result.get('tool_name', '')}"])  # 新增代码+ChromeExtensionStage6: 返回稳定多行状态；若没有这行代码，验收器无法用文本确认命令状态。

    def tabs_context_dict(self) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage7: 返回最近 tabs context 字典；若没有这行代码，provider 无法从 bridge 取当前 URL 做权限检查。
        value = self.state.get("last_tabs_context", {})  # 新增代码+ChromeExtensionStage7: 读取最近 tabs context；若没有这行代码，权限检查没有数据来源。
        return value if isinstance(value, dict) else {}  # 新增代码+ChromeExtensionStage7: 非字典状态兜底为空；若没有这行代码，坏状态会导致 provider 崩溃。

    def active_tab_url(self) -> str:  # 新增代码+ChromeExtensionStage7: 返回当前 active tab 的 URL；若没有这行代码，未传 page_id 的权限检查无法定位 origin。
        context = self.tabs_context_dict()  # 新增代码+ChromeExtensionStage7: 读取 tabs context；若没有这行代码，后续重复取 state。
        active_tab_id = str(context.get("active_tab_id", "") or "")  # 新增代码+ChromeExtensionStage7: 读取 active tab id；若没有这行代码，无法在列表中找当前页。
        tabs = context.get("tabs", []) if isinstance(context.get("tabs", []), list) else []  # 新增代码+ChromeExtensionStage7: 读取 tabs 列表；若没有这行代码，坏状态会抛错。
        for tab in tabs:  # 新增代码+ChromeExtensionStage7: 遍历 tab 摘要；若没有这行代码，无法找到 active tab。
            if isinstance(tab, dict) and str(tab.get("tab_id", "") or "") == active_tab_id:  # 新增代码+ChromeExtensionStage7: 匹配 active tab id；若没有这行代码，可能返回错误页面 URL。
                return str(tab.get("url", "") or "")  # 新增代码+ChromeExtensionStage7: 返回 active tab URL；若没有这行代码，权限检查没有 origin。
        for tab in tabs:  # 新增代码+ChromeExtensionStage7: 没有 active id 时找 active=true 兜底；若没有这行代码，部分旧状态无法解析。
            if isinstance(tab, dict) and bool(tab.get("active", False)):  # 新增代码+ChromeExtensionStage7: 匹配 active 标记；若没有这行代码，兜底无法生效。
                return str(tab.get("url", "") or "")  # 新增代码+ChromeExtensionStage7: 返回 active 标记 URL；若没有这行代码，权限检查没有 origin。
        return ""  # 新增代码+ChromeExtensionStage7: 找不到时返回空字符串；若没有这行代码，调用方需要处理 None。

    def url_for_page_id(self, page_id: str) -> str:  # 新增代码+ChromeExtensionStage7: 根据 chrome-tab-* page_id 找 URL；若没有这行代码，指定标签页写动作无法检查正确 origin。
        safe_page_id = str(page_id or "")  # 新增代码+ChromeExtensionStage7: 规范化 page_id；若没有这行代码，None 会破坏比较。
        tabs = self.tabs_context_dict().get("tabs", []) if isinstance(self.tabs_context_dict().get("tabs", []), list) else []  # 新增代码+ChromeExtensionStage7: 读取 tabs 列表；若没有这行代码，无法按 page_id 查询。
        for tab in tabs:  # 新增代码+ChromeExtensionStage7: 遍历 tabs；若没有这行代码，查询没有候选。
            if isinstance(tab, dict) and str(tab.get("tab_id", "") or "") == safe_page_id:  # 新增代码+ChromeExtensionStage7: 匹配 provider page_id；若没有这行代码，会误用 active tab。
                return str(tab.get("url", "") or "")  # 新增代码+ChromeExtensionStage7: 返回目标 URL；若没有这行代码，权限检查没有 origin。
        return self.active_tab_url()  # 新增代码+ChromeExtensionStage7: 找不到指定 tab 时回退 active tab；若没有这行代码，省略或旧 page_id 会直接失败。

    def record_permission_event(self, event: dict[str, Any]) -> None:  # 新增代码+ChromeExtensionStage7: 保存插件权限事件摘要；若没有这行代码，状态和验收无法看到授权变化。
        events = self.state.get("permission_events", []) if isinstance(self.state.get("permission_events", []), list) else []  # 新增代码+ChromeExtensionStage7: 读取已有权限事件；若没有这行代码，会覆盖旧事件。
        events.append(dict(event or {}))  # 新增代码+ChromeExtensionStage7: 追加新事件；若没有这行代码，授权变化不会记录。
        self.state["permission_events"] = events[-100:]  # 新增代码+ChromeExtensionStage7: 仅保留最近 100 条；若没有这行代码，状态文件会无限增长。
        self._save()  # 新增代码+ChromeExtensionStage7: 立即落盘；若没有这行代码，状态工具看不到权限变化。

    def connected(self) -> bool:  # 新增代码+ChromeExtensionStage5: 返回连接状态；若没有这行代码，provider health 要重复读 state。
        return bool(self.state.get("connected", False))  # 新增代码+ChromeExtensionStage5: 规范成布尔值；若没有这行代码，字符串状态可能误判。

    def status_dict(self) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage5: 输出机器可读状态；若没有这行代码，状态工具和 provider 会重复拼字段。
        pairing = self.pairing_summary()  # 新增代码+Phase2Pairing: 读取配对摘要；如果没有这行代码，机器状态看不到 paired/device/session。
        pairing_request = self.pairing_request_summary()  # 新增代码+Phase15ChromePairingTrigger: 读取待配对请求摘要；如果没有这行代码，状态工具看不到终端触发结果。
        return {"connected": self.connected(), "extension_id": self.state.get("extension_id", ""), "last_seen_at": self.state.get("last_seen_at", ""), "tab_count": self.state.get("last_tabs_context", {}).get("tab_count", 0), "read_only": False, "pending_command_count": len(self._pending_list()), "permission_event_count": len(self.state.get("permission_events", []) if isinstance(self.state.get("permission_events", []), list) else []), "paired": bool(pairing), "device_id": pairing.get("device_id", ""), "session_id": pairing.get("session_id", ""), "last_browser_prompt_id": self.state.get("last_browser_prompt_id", ""), "pending_pairing_request_id": pairing_request.get("request_id", ""), "pending_pairing_request_status": pairing_request.get("status", ""), "pending_pairing_request_created_at": pairing_request.get("created_at", "")}  # 修改代码+Phase15ChromePairingTrigger: 状态增加配对请求字段；如果没有这行代码，/chrome 无法展示 pending 请求。

    def status_text(self) -> str:  # 新增代码+ChromeExtensionStage5: 输出人类可读状态；若没有这行代码，browser_extension_status 没有文本结果。
        status = self.status_dict()  # 新增代码+ChromeExtensionStage5: 读取统一状态字典；若没有这行代码，文本和 API 状态会分裂。
        return "\n".join(["browser_extension_status", f"provider=chrome_extension", f"connected={str(status['connected']).lower()}", f"read_only={str(status['read_only']).lower()}", f"extension_id={status['extension_id']}", f"tab_count={status['tab_count']}", f"pending_command_count={status['pending_command_count']}", f"permission_event_count={status['permission_event_count']}", f"paired={str(bool(status.get('paired', False))).lower()}", f"device_id={status.get('device_id', '')}", f"session_id={status.get('session_id', '')}", f"last_browser_prompt_id={status.get('last_browser_prompt_id', '')}", f"last_seen_at={status['last_seen_at']}"])  # 修改代码+Phase2Pairing: 返回连接、读写、命令队列、权限事件和配对状态；如果没有这行代码，用户无法判断 session sync 是否成功。

    def tabs_context_text(self) -> str:  # 新增代码+ChromeExtensionStage5: 输出 provider 格式的 tabs context；若没有这行代码，ChromeExtensionProvider 无法实现 browser_tabs_context。
        response = self.state.get("last_tabs_context", {})  # 新增代码+ChromeExtensionStage5: 读取最近 tabs context；若没有这行代码，输出没有数据来源。
        tabs = response.get("tabs", []) if isinstance(response, dict) else []  # 新增代码+ChromeExtensionStage5: 读取安全 tabs 列表；若没有这行代码，坏状态可能抛错。
        lines = ["browser_tabs_context 成功", "provider=chrome_extension", f"connected={str(self.connected()).lower()}", f"active_tab_id={response.get('active_tab_id', '') if isinstance(response, dict) else ''}", f"tab_count={len(tabs)}", "tabs:"]  # 新增代码+ChromeExtensionStage5: 准备 context 头部；若没有这行代码，输出缺少 provider 和 active tab。
        for tab in tabs:  # 新增代码+ChromeExtensionStage5: 遍历 tabs 列表；若没有这行代码，具体页面不会显示。
            lines.append(f"- tab_id={tab.get('tab_id', '')} chrome_tab_id={tab.get('chrome_tab_id', '')} active={str(bool(tab.get('active', False))).lower()} title={tab.get('title', '')} URL={tab.get('url', '')}")  # 新增代码+ChromeExtensionStage5: 输出单个 tab 摘要；若没有这行代码，用户看不到 URL 和标题。
        if not tabs:  # 新增代码+ChromeExtensionStage5: 无 tabs 时明确提示；若没有这行代码，空输出难以理解。
            lines.append("- 无可用标签页")  # 新增代码+ChromeExtensionStage5: 输出空列表提示；若没有这行代码，用户不知道是不是截断。
        return "\n".join(lines)  # 新增代码+ChromeExtensionStage5: 返回多行文本；若没有这行代码，provider 没有输出。

    def snapshot_text(self) -> str:  # 新增代码+ChromeExtensionStage5: 输出 provider 格式页面快照；若没有这行代码，ChromeExtensionProvider 无法实现 browser_snapshot。
        response = self.state.get("last_page_snapshot", {})  # 新增代码+ChromeExtensionStage5: 读取最近页面快照；若没有这行代码，snapshot 没有数据来源。
        tab = response.get("tab", {}) if isinstance(response, dict) else {}  # 新增代码+ChromeExtensionStage5: 读取 tab 摘要；若没有这行代码，页面内容缺少来源。
        visible_text = response.get("visible_text", "") if isinstance(response, dict) else ""  # 新增代码+ChromeExtensionStage5: 读取可见文本；若没有这行代码，正文摘要为空。
        return "\n".join(["browser_snapshot 成功", "provider=chrome_extension", f"tab_id={tab.get('tab_id', '')}", f"标题：{tab.get('title', '')}", f"URL：{tab.get('url', '')}", f"正文摘要：{visible_text}"])  # 新增代码+ChromeExtensionStage5: 返回只读页面摘要；若没有这行代码，用户看不到页面内容。
