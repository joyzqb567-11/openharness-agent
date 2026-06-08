"""Chrome native messaging host 入口。"""  # 修改代码+ChromeExtensionStage6: 说明本脚本既处理只读消息也处理写动作命令轮询；若没有这行代码，入口职责会被误读为只读。
from __future__ import annotations  # 新增代码+ChromeExtensionStage5: 延迟解析类型注解；若没有这行代码，脚本类型标注更脆弱。

import json  # 新增代码+ChromeExtensionStage5: 解析和输出 JSON 消息；若没有这行代码，native messaging 无法处理数据。
import struct  # 新增代码+ChromeExtensionStage5: 读写 Chrome native messaging 4 字节长度头；若没有这行代码，协议帧无法解析。
import sys  # 新增代码+ChromeExtensionStage5: 访问 stdin/stdout 二进制流；若没有这行代码，host 无法和 Chrome 通信。
from pathlib import Path  # 新增代码+ChromeExtensionStage5: 处理状态文件路径；若没有这行代码，bridge state 无法定位。

try:  # 新增代码+ChromeExtensionStage5: 包模式优先导入协议和 bridge；若没有这行代码，python -m 运行无法解析包路径。
    from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+ChromeExtensionStage5: 导入 bridge 状态；若没有这行代码，host 无法保存连接和消息。
    from learning_agent.browser_extension_host.message_protocol import build_host_response  # 修改代码+ChromeExtensionStage6: 导入 host 协议；若没有这行代码，host 会缺少安全过滤和动作结果处理。
    from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+Phase2Pairing: 导入 durable runtime queue；如果没有这行代码，浏览器侧 prompt 无法进入主循环。
except ModuleNotFoundError:  # 新增代码+ChromeExtensionStage5: 兼容直接脚本运行；若没有这行代码，Chrome 启动脚本时可能找不到 learning_agent 包。
    from bridge_server import ChromeExtensionBridgeState  # type: ignore  # 新增代码+ChromeExtensionStage5: 脚本模式导入 bridge；若没有这行代码，直接运行 host 不可用。
    from message_protocol import build_host_response  # type: ignore  # 修改代码+ChromeExtensionStage6: 脚本模式导入协议；若没有这行代码，直接运行 host 不可用。
    from runtime.command_queue import RuntimeCommandQueue  # type: ignore  # 新增代码+Phase2Pairing: 脚本模式导入 durable queue；如果没有这行代码，bat/stdio 路线无法接收浏览器 prompt。


def _read_message() -> dict[str, object] | None:  # 新增代码+ChromeExtensionStage5: 读取一帧 native message；若没有这行代码，主循环无法获得请求。
    raw_length = sys.stdin.buffer.read(4)  # 新增代码+ChromeExtensionStage5: 读取 4 字节长度头；若没有这行代码，无法知道消息大小。
    if not raw_length:  # 新增代码+ChromeExtensionStage5: EOF 时返回 None；若没有这行代码，Chrome 断开会导致死循环。
        return None  # 新增代码+ChromeExtensionStage5: 表示没有更多消息；若没有这行代码，调用方无法退出。
    message_length = struct.unpack("<I", raw_length)[0]  # 新增代码+ChromeExtensionStage5: 按 Chrome 规范解析小端长度；若没有这行代码，读取体长度会错误。
    message_bytes = sys.stdin.buffer.read(message_length)  # 新增代码+ChromeExtensionStage5: 读取完整 JSON 消息体；若没有这行代码，无法解析请求。
    return json.loads(message_bytes.decode("utf-8"))  # 新增代码+ChromeExtensionStage5: 解码 JSON 对象；若没有这行代码，host 拿不到 action。


def _write_message(message: dict[str, object]) -> None:  # 新增代码+ChromeExtensionStage5: 输出一帧 native message；若没有这行代码，Chrome 收不到响应。
    encoded = json.dumps(message, ensure_ascii=False).encode("utf-8")  # 新增代码+ChromeExtensionStage5: 把响应编码为 UTF-8 JSON；若没有这行代码，非 ASCII 文本可能损坏。
    sys.stdout.buffer.write(struct.pack("<I", len(encoded)))  # 新增代码+ChromeExtensionStage5: 写入 4 字节长度头；若没有这行代码，Chrome 无法解析响应。
    sys.stdout.buffer.write(encoded)  # 新增代码+ChromeExtensionStage5: 写入 JSON 正文；若没有这行代码，响应没有内容。
    sys.stdout.buffer.flush()  # 新增代码+ChromeExtensionStage5: 立即刷新输出；若没有这行代码，Chrome 可能一直等响应。


def main() -> int:  # 新增代码+ChromeExtensionStage5: native host 主入口；若没有这行代码，脚本只能被导入不能运行。
    state_path = Path.cwd() / "learning_agent" / "memory" / "chrome_extension_bridge.json"  # 新增代码+ChromeExtensionStage5: 默认把 bridge 状态放入项目 memory；若没有这行代码，provider 找不到 host 状态。
    bridge = ChromeExtensionBridgeState(state_path)  # 新增代码+ChromeExtensionStage5: 创建 bridge 状态对象；若没有这行代码，消息无法持久化。
    command_queue = RuntimeCommandQueue(Path.cwd() / "learning_agent" / "memory" / "runtime")  # 新增代码+Phase2Pairing: 创建浏览器 prompt 的 durable queue；如果没有这行代码，扩展发起任务不能跨进程恢复。
    bridge.record_connection(extension_id="native-host")  # 新增代码+ChromeExtensionStage5: 标记 host 已被扩展连接；若没有这行代码，provider health 仍不可用。
    while True:  # 新增代码+ChromeExtensionStage5: 持续处理 Chrome 消息；若没有这行代码，host 只能处理一条消息。
        message = _read_message()  # 新增代码+ChromeExtensionStage5: 读取下一条请求；若没有这行代码，循环没有输入。
        if message is None:  # 新增代码+ChromeExtensionStage5: Chrome 断开时退出；若没有这行代码，EOF 会继续空转。
            break  # 新增代码+ChromeExtensionStage5: 结束循环；若没有这行代码，host 不会退出。
        action = str(message.get("action", "") or "")  # 新增代码+ChromeExtensionStage6: 读取消息动作名；若没有这行代码，host 无法区分轮询命令和普通消息。
        if action == "poll_commands":  # 新增代码+ChromeExtensionStage6: 扩展主动拉取待执行命令；若没有这行代码，provider 入队后扩展永远收不到命令。
            _write_message({"ok": True, "action": "poll_commands", "commands": bridge.pending_commands(), "pairing_request": bridge.pending_pairing_request()})  # 修改代码+Phase15ChromePairingTrigger: 轮询响应同时下发待配对请求；如果没有这行代码，终端触发无法到达真实扩展。
            continue  # 新增代码+ChromeExtensionStage6: 轮询命令已响应，跳过普通协议；若没有这行代码，poll_commands 会被当未知动作拒绝。
        if action == "action_result":  # 新增代码+ChromeExtensionStage6: 扩展回传写动作结果；若没有这行代码，provider 等不到完成信号。
            response = bridge.record_command_result(message)  # 新增代码+ChromeExtensionStage6: 保存脱敏后的命令结果；若没有这行代码，动作证据不会落盘。
            _write_message(response)  # 新增代码+ChromeExtensionStage6: 把保存结果回复给扩展；若没有这行代码，扩展无法知道 host 已接收。
            continue  # 新增代码+ChromeExtensionStage6: 结果已处理，跳过只读分支；若没有这行代码，结果会被重复处理。
        if action == "pair_device":  # 新增代码+Phase2Pairing: 扩展请求保存配对信息；如果没有这行代码，device/session 身份无法进入 bridge 状态。
            pairing = bridge.record_pairing(message)  # 新增代码+Phase2Pairing: 脱敏保存配对摘要；如果没有这行代码，配对请求不会持久化。
            _write_message({"ok": True, "action": "pair_device", "pairing": pairing})  # 新增代码+Phase2Pairing: 回复配对结果；如果没有这行代码，扩展不知道配对是否成功。
            continue  # 新增代码+Phase2Pairing: 配对消息已处理；如果没有这行代码，pair_device 会落入只读协议并被拒绝。
        if action == "browser_prompt":  # 新增代码+Phase2Pairing: 扩展请求把浏览器任务推给 agent；如果没有这行代码，Chrome 侧无法发起任务。
            response = bridge.enqueue_browser_prompt(command_queue, message)  # 新增代码+Phase2Pairing: 把 prompt 写入 durable runtime queue；如果没有这行代码，任务会绕过可恢复主循环。
            _write_message(response)  # 新增代码+Phase2Pairing: 回复入队结果；如果没有这行代码，扩展不知道 command_id。
            continue  # 新增代码+Phase2Pairing: prompt 消息已处理；如果没有这行代码，browser_prompt 会被只读协议拒绝。
        response = build_host_response(message)  # 修改代码+ChromeExtensionStage6: 通过协议过滤并构造只读响应；若没有这行代码，消息可能绕过安全过滤。
        if response.get("action") == "tabs_context":  # 新增代码+ChromeExtensionStage5: tabs_context 结果需要保存；若没有这行代码，provider 读不到标签页。
            bridge.update_tabs_context(message)  # 新增代码+ChromeExtensionStage5: 保存 tabs context；若没有这行代码，状态工具缺 tab 信息。
        if response.get("action") == "read_page":  # 新增代码+ChromeExtensionStage5: read_page 结果需要保存；若没有这行代码，provider 读不到页面快照。
            bridge.update_page_snapshot(message)  # 新增代码+ChromeExtensionStage5: 保存页面快照；若没有这行代码，snapshot 工具缺内容。
        _write_message(response)  # 新增代码+ChromeExtensionStage5: 返回响应给 Chrome；若没有这行代码，扩展会一直等待。
    bridge.record_disconnect("chrome_native_host_eof")  # 新增代码+ChromeExtensionStage5: EOF 后标记断开；若没有这行代码，provider 可能继续误报 connected。
    return 0  # 新增代码+ChromeExtensionStage5: 返回成功退出码；若没有这行代码，进程状态不明确。


if __name__ == "__main__":  # 新增代码+ChromeExtensionStage5: 直接运行脚本时进入 main；若没有这行代码，Chrome 启动 host 后不会执行循环。
    raise SystemExit(main())  # 新增代码+ChromeExtensionStage5: 用 main 返回码退出；若没有这行代码，异常和退出码不可控。
