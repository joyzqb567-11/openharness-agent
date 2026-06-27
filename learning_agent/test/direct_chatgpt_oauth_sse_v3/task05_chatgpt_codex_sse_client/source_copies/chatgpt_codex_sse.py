"""Direct ChatGPT OAuth Codex SSE 客户端。"""  # 新增代码+DirectChatGptSseClient: 这个文件集中承载 ChatGPT OAuth 直连 Codex SSE 的端点、请求头和事件解析；如果没有这行代码，GUI 直连和旧 OAuth wrapper 会继续各自维护一套易漂移逻辑。

from __future__ import annotations  # 新增代码+DirectChatGptSseClient: 延迟解析类型注解；如果没有这行代码，类内部返回类型在老解释器上更容易出错。

import copy  # 新增代码+DirectChatGptSseClient: 解析 native output item 时需要深拷贝事件对象；如果没有这行代码，回填 arguments 会污染原始调试事件。
import json  # 新增代码+DirectChatGptSseClient: SSE data payload 是 JSON；如果没有这行代码，客户端无法解析 Codex 响应。
import urllib.request  # 新增代码+DirectChatGptSseClient: 默认真实请求使用标准库 HTTP；如果没有这行代码，客户端只能在测试中工作。
from typing import Any, Callable, Iterable  # 新增代码+DirectChatGptSseClient: 导入通用类型和可注入请求函数类型；如果没有这行代码，客户端边界不清晰。

try:  # 新增代码+DirectChatGptSseClient: 包运行模式下读取统一流事件和消息对象；如果没有这行代码，GUI 事件无法复用模型层协议。
    from learning_agent.core.messages import ModelMessage  # 新增代码+DirectChatGptSseClient: 导入完整模型消息对象；如果没有这行代码，完成事件无法携带最终回答。
    from learning_agent.models.base import ModelStreamEvent  # 新增代码+DirectChatGptSseClient: 导入模型流式事件对象；如果没有这行代码，GUI adapter 无法消费统一事件流。
except ModuleNotFoundError as error:  # 新增代码+DirectChatGptSseClient: 兼容 bat 入口的脚本运行模式；如果没有这行代码，直接运行 learning_agent 时可能找不到包名。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.messages", "learning_agent.models", "learning_agent.models.base"}:  # 新增代码+DirectChatGptSseClient: 只对包路径缺失启用 fallback；如果没有这行代码，真实导入 bug 会被误吞。
        raise  # 新增代码+DirectChatGptSseClient: 重新抛出非路径类错误；如果没有这行代码，排查导入问题会很困难。
    from core.messages import ModelMessage  # type: ignore  # 新增代码+DirectChatGptSseClient: 脚本模式下从同目录 core 导入消息；如果没有这行代码，bat 入口无法构造完成事件。
    from models.base import ModelStreamEvent  # type: ignore  # 新增代码+DirectChatGptSseClient: 脚本模式下从同目录 models 导入事件；如果没有这行代码，bat 入口无法流式返回。


CHATGPT_CODEX_RESPONSES_ENDPOINT = "https://chatgpt.com/backend-api/codex/responses"  # 新增代码+DirectChatGptSseClient: 固定 ChatGPT Codex responses 端点；如果没有这行代码，旧 wrapper 和 GUI 直连可能写出不同 URL。
KNOWN_NON_TEXT_EVENT_TYPES = {  # 新增代码+DirectChatGptSseClient: 枚举已知但不直接产出文本的 SSE 事件；如果没有这行代码，正常 native/tool 事件会被误判为 endpoint drift。
    "response.created",  # 新增代码+DirectChatGptSseClient: 响应创建事件只表示请求已建立；如果没有这行代码，首个正常事件会触发错误。
    "response.in_progress",  # 新增代码+DirectChatGptSseClient: 响应进行中事件只用于状态提示；如果没有这行代码，真实流中常见状态事件会中断。
    "response.output_item.added",  # 新增代码+DirectChatGptSseClient: native output item 创建事件由完整 parser 处理；如果没有这行代码，工具调用流会被误报漂移。
    "response.output_item.done",  # 新增代码+DirectChatGptSseClient: native output item 完成事件由完整 parser 处理；如果没有这行代码，工具调用流会被误报漂移。
    "response.function_call_arguments.delta",  # 新增代码+DirectChatGptSseClient: function_call 参数分片由完整 parser 处理；如果没有这行代码，工具参数流会被误报漂移。
    "response.function_call_arguments.done",  # 新增代码+DirectChatGptSseClient: function_call 参数完成由完整 parser 处理；如果没有这行代码，工具参数完成事件会被误报漂移。
    "response.reasoning_summary_text.delta",  # 新增代码+DirectChatGptSseClient: reasoning 摘要分片暂不展示给 GUI；如果没有这行代码，合法推理摘要事件会被误判。
    "response.reasoning_summary_text.done",  # 新增代码+DirectChatGptSseClient: reasoning 摘要结束暂不展示给 GUI；如果没有这行代码，合法推理摘要结束会被误判。
}  # 新增代码+DirectChatGptSseClient: 已知非文本事件集合结束；如果没有这行代码，Python 集合语法不完整。
PostSseFunction = Callable[[str, dict[str, str], dict[str, object], float], Iterable[str | bytes]]  # 新增代码+DirectChatGptSseClient: 抽象 SSE POST 函数；如果没有这行代码，测试无法注入假网络流。


class ChatGptCodexSseClient:  # 新增代码+DirectChatGptSseClient: 函数段开始，封装 ChatGPT OAuth Codex SSE 请求和解析；如果没有这个类，GUI 真实模型链路没有可复用客户端，本段到 parse_sse_text_to_response 结束。
    def __init__(  # 新增代码+DirectChatGptSseClient: 初始化客户端实例；如果没有这个函数，调用方无法注入 token、模型和测试请求函数。
        self,  # 新增代码+DirectChatGptSseClient: 当前客户端实例；如果没有这行代码，实例方法无法访问自身状态。
        access_token: str,  # 新增代码+DirectChatGptSseClient: OAuth access token；如果没有这行代码，真实请求无法鉴权。
        model: str,  # 新增代码+DirectChatGptSseClient: 目标模型名；如果没有这行代码，服务端不知道调用哪个 ChatGPT/Codex 模型。
        account_id: str | None = None,  # 新增代码+DirectChatGptSseClient: 可选 ChatGPT 账号 id；如果没有这行代码，多账号用户可能请求到错误组织。
        post_sse: PostSseFunction | None = None,  # 新增代码+DirectChatGptSseClient: 可注入 SSE POST 函数；如果没有这行代码，单元测试必须真实联网。
        timeout_seconds: float = 120.0,  # 新增代码+DirectChatGptSseClient: 请求超时时间；如果没有这行代码，坏网络可能让 GUI 长时间卡住。
    ) -> None:  # 新增代码+DirectChatGptSseClient: 初始化函数返回 None；如果没有这行代码，类型边界不完整。
        self._access_token = access_token.strip()  # 新增代码+DirectChatGptSseClient: 清理 token 前后空白；如果没有这行代码，Authorization 可能带空格导致鉴权失败。
        self._model = model.strip() or "gpt-5.5"  # 新增代码+DirectChatGptSseClient: 保存模型并兜底 GPT-5.5；如果没有这行代码，空模型会直接发到后端。
        self._account_id = (account_id or "").strip() or None  # 新增代码+DirectChatGptSseClient: 清理账号 id 并把空值转 None；如果没有这行代码，空账号头会污染请求。
        self._post_sse = post_sse or self._default_post_sse  # 新增代码+DirectChatGptSseClient: 保存真实或测试 SSE 请求函数；如果没有这行代码，stream_responses 没有网络入口。
        self._timeout_seconds = max(float(timeout_seconds), 1.0)  # 新增代码+DirectChatGptSseClient: 保证至少 1 秒超时；如果没有这行代码，0 或负数会导致请求行为异常。

    def build_headers(self) -> dict[str, str]:  # 新增代码+DirectChatGptSseClient: 函数段开始，构造 ChatGPT Codex SSE 请求头；如果没有这个函数，header 规则会散落在 GUI 和旧 wrapper 中，本段到 return 结束。
        headers = {  # 新增代码+DirectChatGptSseClient: 准备基础请求头字典；如果没有这行代码，后续无法逐项添加 header。
            "Accept": "text/event-stream",  # 新增代码+DirectChatGptSseClient: 明确要求 SSE 响应；如果没有这行代码，后端可能返回非流式响应。
            "Authorization": f"Bearer {self._access_token}",  # 新增代码+DirectChatGptSseClient: 写入 OAuth Bearer token；如果没有这行代码，ChatGPT 后端会拒绝请求。
            "Content-Type": "application/json",  # 新增代码+DirectChatGptSseClient: 声明请求体是 JSON；如果没有这行代码，后端可能无法解析 body。
            "User-Agent": "openharness-desktop/0.1",  # 新增代码+DirectChatGptSseClient: 标记请求来源；如果没有这行代码，排查真实流量来源会更困难。
        }  # 新增代码+DirectChatGptSseClient: 基础 header 字典结束；如果没有这行代码，Python 字典语法不完整。
        if self._account_id:  # 新增代码+DirectChatGptSseClient: 只有存在账号 id 才添加账号头；如果没有这行代码，空账号头会影响后端路由。
            headers["ChatGPT-Account-Id"] = self._account_id  # 新增代码+DirectChatGptSseClient: 写入 ChatGPT 账号/组织 id；如果没有这行代码，多账号用户无法指定账号。
        return headers  # 新增代码+DirectChatGptSseClient: 返回最终请求头；如果没有这行代码，调用方拿不到 header。

    def build_body(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, extra_body: dict[str, object] | None = None) -> dict[str, object]:  # 新增代码+DirectChatGptSseClient: 函数段开始，构造最小 Codex responses 请求体；如果没有这个函数，GUI adapter 会重复拼 body，本段到 return 结束。
        body: dict[str, object] = {  # 新增代码+DirectChatGptSseClient: 准备默认请求体；如果没有这行代码，后端没有 model/input/stream 等关键字段。
            "model": self._model,  # 新增代码+DirectChatGptSseClient: 指定目标模型；如果没有这行代码，服务端无法选择模型。
            "store": False,  # 新增代码+DirectChatGptSseClient: 保持 Codex CLI 风格不存储；如果没有这行代码，请求隐私语义会和旧链路不一致。
            "stream": True,  # 新增代码+DirectChatGptSseClient: 开启 SSE 流式输出；如果没有这行代码，GUI 无法边收边显示。
            "input": messages,  # 新增代码+DirectChatGptSseClient: 传入调用方构造好的 Responses input；如果没有这行代码，模型看不到用户问题。
        }  # 新增代码+DirectChatGptSseClient: 默认请求体结束；如果没有这行代码，Python 字典语法不完整。
        if tools:  # 新增代码+DirectChatGptSseClient: 只有存在工具时才写 tools 字段；如果没有这行代码，空工具数组可能改变后端行为。
            body["tools"] = tools  # 新增代码+DirectChatGptSseClient: 写入顶层工具定义；如果没有这行代码，未来直连工具调用无法暴露给模型。
        if extra_body:  # 新增代码+DirectChatGptSseClient: 允许 GUI adapter 追加 instructions/reasoning/text 等字段；如果没有这行代码，调用方无法扩展请求。
            body.update(extra_body)  # 新增代码+DirectChatGptSseClient: 用调用方附加字段覆盖默认值；如果没有这行代码，reasoning_effort 等设置无法生效。
        body["model"] = self._model  # 新增代码+DirectChatGptSseClient: 最后锁定模型字段；如果没有这行代码，extra_body 可能误改用户选择的模型。
        body["stream"] = True  # 新增代码+DirectChatGptSseClient: 最后锁定流式字段；如果没有这行代码，extra_body 可能关闭 SSE。
        return body  # 新增代码+DirectChatGptSseClient: 返回请求体；如果没有这行代码，调用方无法发起请求。

    def stream_responses(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, extra_body: dict[str, object] | None = None) -> Iterable[ModelStreamEvent]:  # 新增代码+DirectChatGptSseClient: 函数段开始，发起真实 SSE 请求并产出模型事件；如果没有这个函数，GUI adapter 无法走 Direct SSE，本段到 yield from 结束。
        if not self._access_token:  # 新增代码+DirectChatGptSseClient: 先检查 token 是否存在；如果没有这行代码，空 token 会发到后端制造难懂 401。
            yield self._model_error_event("auth_missing", "OpenAI OAuth access token 缺失。")  # 新增代码+DirectChatGptSseClient: 返回可展示鉴权错误；如果没有这行代码，GUI 只会显示底层异常。
            return  # 新增代码+DirectChatGptSseClient: token 缺失时停止；如果没有这行代码，仍会继续尝试联网。
        body = self.build_body(messages=messages, tools=tools, extra_body=extra_body)  # 新增代码+DirectChatGptSseClient: 构造请求体；如果没有这行代码，请求函数没有 body。
        headers = self.build_headers()  # 新增代码+DirectChatGptSseClient: 构造请求头；如果没有这行代码，请求函数没有鉴权 header。
        try:  # 新增代码+DirectChatGptSseClient: 捕获网络层异常；如果没有这行代码，GUI 事件流会被异常直接打断。
            lines = self._post_sse(CHATGPT_CODEX_RESPONSES_ENDPOINT, headers, body, self._timeout_seconds)  # 新增代码+DirectChatGptSseClient: 发起 SSE POST；如果没有这行代码，客户端不会调用后端。
            yield from self.events_from_sse_lines(lines)  # 新增代码+DirectChatGptSseClient: 解析网络行并产出事件；如果没有这行代码，调用方收不到模型输出。
        except Exception as error:  # 新增代码+DirectChatGptSseClient: 捕获请求函数抛出的错误；如果没有这行代码，GUI 无法把网络错误转成事件。
            yield self._model_error_event("request_failed", str(error))  # 新增代码+DirectChatGptSseClient: 把异常转为模型错误事件；如果没有这行代码，用户看不到失败原因。

    @staticmethod  # 新增代码+DirectChatGptSseClient: 默认 POST 不依赖实例状态之外的数据；如果没有这行代码，测试调用该 helper 需要实例。
    def _default_post_sse(url: str, headers: dict[str, str], body: dict[str, object], timeout_seconds: float) -> Iterable[str | bytes]:  # 新增代码+DirectChatGptSseClient: 函数段开始，用标准库 POST 并逐行返回 SSE；如果没有这个函数，真实直连没有网络实现，本段到 while break 结束。
        raw_body = json.dumps(body, ensure_ascii=False).encode("utf-8")  # 新增代码+DirectChatGptSseClient: 把请求体编码成 UTF-8 JSON；如果没有这行代码，urllib 无法发送 dict。
        request = urllib.request.Request(url=url, data=raw_body, headers=headers, method="POST")  # 新增代码+DirectChatGptSseClient: 创建 HTTP POST 请求；如果没有这行代码，无法连接 ChatGPT 后端。
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # 新增代码+DirectChatGptSseClient: 打开 HTTP 响应流；如果没有这行代码，无法读取 SSE 行。
            while True:  # 新增代码+DirectChatGptSseClient: 循环读取直到 EOF；如果没有这行代码，只能读第一行。
                line = response.readline()  # 新增代码+DirectChatGptSseClient: 从响应中读取一行；如果没有这行代码，SSE 事件无法按边界解析。
                if not line:  # 新增代码+DirectChatGptSseClient: 服务器关闭连接时结束；如果没有这行代码，EOF 后会无限循环。
                    break  # 新增代码+DirectChatGptSseClient: 跳出读取循环；如果没有这行代码，函数无法结束。
                yield line  # 新增代码+DirectChatGptSseClient: 产出原始行给解析器；如果没有这行代码，调用方收不到任何事件。

    @classmethod  # 新增代码+DirectChatGptSseClient: 允许测试和旧 wrapper 直接解析字符串；如果没有这行代码，必须构造实例才能测试 fixture。
    def events_from_sse_text(cls, raw_stream: str) -> Iterable[ModelStreamEvent]:  # 新增代码+DirectChatGptSseClient: 函数段开始，从完整 SSE 文本产出事件；如果没有这个函数，fixture 测试会很笨重，本段到 yield from 结束。
        yield from cls.events_from_sse_lines(raw_stream.splitlines())  # 新增代码+DirectChatGptSseClient: 复用逐行解析器；如果没有这行代码，文本和网络行解析会分叉。

    @classmethod  # 新增代码+DirectChatGptSseClient: 事件解析不依赖实例 token；如果没有这行代码，旧 wrapper 不能无实例复用。
    def events_from_sse_lines(cls, lines: Iterable[str | bytes]) -> Iterable[ModelStreamEvent]:  # 新增代码+DirectChatGptSseClient: 函数段开始，把 SSE 行转换成 ModelStreamEvent；如果没有这个函数，GUI 无法增量消费 Direct SSE，本段到循环结束。
        output_chunks: list[str] = []  # 新增代码+DirectChatGptSseClient: 保存已收到的文本分片；如果没有这行代码，[DONE] 兜底无法生成完整回答。
        for payload in cls._iter_sse_data_payloads(lines):  # 新增代码+DirectChatGptSseClient: 遍历 data payload；如果没有这行代码，event/id/空行会干扰解析。
            if payload == "[DONE]":  # 新增代码+DirectChatGptSseClient: 识别 SSE 结束标记；如果没有这行代码，只发 DONE 的流无法完成。
                yield cls._completed_event("".join(output_chunks), {"status": "done_marker"})  # 新增代码+DirectChatGptSseClient: 在 DONE 时产出完成事件；如果没有这行代码，GUI 会停在 running。
                return  # 新增代码+DirectChatGptSseClient: DONE 后结束解析；如果没有这行代码，后续空行可能继续处理。
            try:  # 新增代码+DirectChatGptSseClient: 捕获坏 JSON；如果没有这行代码，端点漂移会变成底层异常。
                event = json.loads(payload)  # 新增代码+DirectChatGptSseClient: 解析 JSON 事件；如果没有这行代码，无法读取事件类型和增量文本。
            except json.JSONDecodeError:  # 新增代码+DirectChatGptSseClient: 处理不是 JSON 的 data；如果没有这行代码，漂移事件无法形成可展示错误。
                yield cls._endpoint_drift_event({"payload": payload[:500]})  # 新增代码+DirectChatGptSseClient: 报告端点漂移并截断证据；如果没有这行代码，用户不知道协议变了。
                return  # 新增代码+DirectChatGptSseClient: 漂移后停止；如果没有这行代码，坏流可能继续制造噪声。
            error_event = cls._error_event_from_payload(event)  # 新增代码+DirectChatGptSseClient: 尝试把 error payload 转为统一错误事件；如果没有这行代码，模型不可用错误无法被上层识别。
            if error_event is not None:  # 新增代码+DirectChatGptSseClient: 如果当前 payload 是错误；如果没有这行代码，错误会继续走普通事件判断。
                yield error_event  # 新增代码+DirectChatGptSseClient: 产出统一错误事件；如果没有这行代码，GUI 不知道模型不可用。
                return  # 新增代码+DirectChatGptSseClient: 错误后停止；如果没有这行代码，后续事件可能掩盖失败原因。
            event_type = str(event.get("type", "") or "")  # 新增代码+DirectChatGptSseClient: 读取事件类型；如果没有这行代码，无法分支处理 delta/done/completed。
            if event_type == "response.output_text.delta" and isinstance(event.get("delta"), str):  # 新增代码+DirectChatGptSseClient: 识别文本增量事件；如果没有这行代码，GUI 无法边输出边显示。
                delta = str(event["delta"])  # 新增代码+DirectChatGptSseClient: 提取文本分片；如果没有这行代码，事件字段访问会重复。
                output_chunks.append(delta)  # 新增代码+DirectChatGptSseClient: 记录分片用于最终完成消息；如果没有这行代码，完成事件缺少完整文本。
                yield ModelStreamEvent(event_type="text_delta", text_delta=delta, raw_event=event)  # 新增代码+DirectChatGptSseClient: 产出文本增量事件；如果没有这行代码，GUI 不会实时展示。
                continue  # 新增代码+DirectChatGptSseClient: 当前事件已处理；如果没有这行代码，会落入未知事件判断。
            if event_type == "response.output_text.done" and isinstance(event.get("text"), str):  # 新增代码+DirectChatGptSseClient: 识别完整文本完成事件；如果没有这行代码，GUI 可能等到连接关闭才完成。
                final_text = str(event["text"])  # 新增代码+DirectChatGptSseClient: 读取后端给的完整文本；如果没有这行代码，最终回答可能只用分片拼接。
                yield cls._completed_event(final_text, event)  # 新增代码+DirectChatGptSseClient: 产出完成事件；如果没有这行代码，GUI 会一直显示 running。
                return  # 新增代码+DirectChatGptSseClient: 完成后结束解析；如果没有这行代码，response.completed 会导致重复完成。
            if event_type == "response.completed" and isinstance(event.get("response"), dict):  # 新增代码+DirectChatGptSseClient: 识别完整 response 完成事件；如果没有这行代码，没有 output_text.done 的流无法完成。
                final_text = cls._extract_text_from_response(event["response"]) or "".join(output_chunks)  # 新增代码+DirectChatGptSseClient: 从完整响应或分片中得到最终文本；如果没有这行代码，完成事件没有回答文本。
                yield cls._completed_event(final_text, event)  # 新增代码+DirectChatGptSseClient: 产出完成事件；如果没有这行代码，GUI 不知道本轮结束。
                return  # 新增代码+DirectChatGptSseClient: 完成后结束解析；如果没有这行代码，后续 DONE 会重复完成。
            if event_type in KNOWN_NON_TEXT_EVENT_TYPES:  # 新增代码+DirectChatGptSseClient: 对已知非文本事件保持沉默；如果没有这行代码，正常工具/状态流会被误报。
                continue  # 新增代码+DirectChatGptSseClient: 继续等待文本或完成事件；如果没有这行代码，已知事件会落到漂移分支。
            yield cls._endpoint_drift_event(event)  # 新增代码+DirectChatGptSseClient: 未知 JSON 形状视为端点漂移；如果没有这行代码，协议变化会静默失败。
            return  # 新增代码+DirectChatGptSseClient: 漂移后停止；如果没有这行代码，GUI 可能混杂后续坏事件。
        if output_chunks:  # 新增代码+DirectChatGptSseClient: EOF 前若已经收到文本分片；如果没有这行代码，缺少 DONE 的可恢复流会丢回答。
            yield cls._completed_event("".join(output_chunks), {"status": "eof_after_delta"})  # 新增代码+DirectChatGptSseClient: 用分片兜底完成；如果没有这行代码，GUI 会停在等待状态。

    @staticmethod  # 新增代码+DirectChatGptSseClient: payload 迭代不依赖实例；如果没有这行代码，测试无法直接调用。
    def _iter_sse_data_payloads(lines: Iterable[str | bytes]) -> Iterable[str]:  # 新增代码+DirectChatGptSseClient: 函数段开始，只抽取 SSE data payload；如果没有这个函数，data/event 行处理会重复，本段到 yield 结束。
        for raw_line in lines:  # 新增代码+DirectChatGptSseClient: 遍历原始 SSE 行；如果没有这行代码，函数没有输入消费。
            line = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else str(raw_line)  # 新增代码+DirectChatGptSseClient: 把 bytes 行转成文本；如果没有这行代码，字节流无法做 startswith。
            stripped = line.strip()  # 新增代码+DirectChatGptSseClient: 去掉换行和空白；如果没有这行代码，data: 判断会被换行影响。
            if not stripped.startswith("data:"):  # 新增代码+DirectChatGptSseClient: 只处理 data 行；如果没有这行代码，event/id/retry 会被误当 payload。
                continue  # 新增代码+DirectChatGptSseClient: 跳过非 data 行；如果没有这行代码，解析器会收到无效内容。
            yield stripped.removeprefix("data:").strip()  # 新增代码+DirectChatGptSseClient: 产出去掉前缀的 payload；如果没有这行代码，JSON 前缀会导致解析失败。

    @staticmethod  # 新增代码+DirectChatGptSseClient: 错误事件构造不依赖实例；如果没有这行代码，解析测试需要无意义客户端。
    def _model_error_event(status: str, message: str, raw_event: dict[str, Any] | None = None) -> ModelStreamEvent:  # 新增代码+DirectChatGptSseClient: 函数段开始，构造统一模型错误事件；如果没有这个函数，错误 raw_event 形状会分散，本段到 return 结束。
        raw = dict(raw_event or {})  # 新增代码+DirectChatGptSseClient: 复制原始事件摘要；如果没有这行代码，调用方传入对象可能被修改。
        raw.setdefault("status", status)  # 新增代码+DirectChatGptSseClient: 写入上层可识别状态；如果没有这行代码，GUI 无法区分模型不可用和网络失败。
        raw.setdefault("message", message)  # 新增代码+DirectChatGptSseClient: 写入用户可读消息；如果没有这行代码，错误事件缺少展示文本。
        return ModelStreamEvent(event_type="model_error", raw_event=raw)  # 新增代码+DirectChatGptSseClient: 返回模型错误事件；如果没有这行代码，调用方收不到错误。

    @classmethod  # 新增代码+DirectChatGptSseClient: endpoint drift 是标准错误形态；如果没有这行代码，各处会写不同 status。
    def _endpoint_drift_event(cls, raw_event: dict[str, Any]) -> ModelStreamEvent:  # 新增代码+DirectChatGptSseClient: 函数段开始，构造端点漂移错误；如果没有这个函数，未知事件无法被稳定识别，本段到 return 结束。
        return cls._model_error_event("endpoint_drift_detected", "ChatGPT Codex SSE 端点返回了未知事件形状。", raw_event)  # 新增代码+DirectChatGptSseClient: 返回端点漂移事件；如果没有这行代码，协议变化会静默失败。

    @classmethod  # 新增代码+DirectChatGptSseClient: error payload 解析不依赖实例；如果没有这行代码，fixture 测试无法复用。
    def _error_event_from_payload(cls, event: dict[str, Any]) -> ModelStreamEvent | None:  # 新增代码+DirectChatGptSseClient: 函数段开始，把 Codex error payload 转成统一事件；如果没有这个函数，model_not_supported 无法进入模型 registry，本段到 return 结束。
        raw_error = event.get("error")  # 新增代码+DirectChatGptSseClient: 读取 error 字段；如果没有这行代码，无法判断 payload 是否为错误。
        if not isinstance(raw_error, dict):  # 新增代码+DirectChatGptSseClient: 只有对象形态 error 才处理；如果没有这行代码，字符串 error 会导致 .get 报错。
            return None  # 新增代码+DirectChatGptSseClient: 非错误 payload 返回 None；如果没有这行代码，普通事件会被误报。
        code = str(raw_error.get("code", "") or "").strip()  # 新增代码+DirectChatGptSseClient: 提取错误码；如果没有这行代码，无法识别模型不可用。
        message = str(raw_error.get("message", "") or "").strip()  # 新增代码+DirectChatGptSseClient: 提取错误消息；如果没有这行代码，GUI 没有可读失败原因。
        status = "model_not_available" if code == "model_not_supported" else "remote_error"  # 新增代码+DirectChatGptSseClient: 把后端错误码归一为上层状态；如果没有这行代码，registry 不知道模型不可用。
        raw_event = {"status": status, "code": code, "message": message, "error": raw_error}  # 新增代码+DirectChatGptSseClient: 保存错误摘要；如果没有这行代码，诊断面板缺少证据。
        return cls._model_error_event(status, message or code or "ChatGPT Codex SSE 返回错误。", raw_event)  # 新增代码+DirectChatGptSseClient: 返回统一错误事件；如果没有这行代码，调用方收不到错误。

    @staticmethod  # 新增代码+DirectChatGptSseClient: 完成事件构造不依赖实例；如果没有这行代码，测试需要构造 token。
    def _completed_event(text: str, raw_event: dict[str, Any]) -> ModelStreamEvent:  # 新增代码+DirectChatGptSseClient: 函数段开始，构造完整模型消息事件；如果没有这个函数，完成事件字段会重复拼装，本段到 return 结束。
        model_message = ModelMessage(text=text)  # 新增代码+DirectChatGptSseClient: 把最终文本包装成统一模型消息；如果没有这行代码，旧主循环无法消费完成结果。
        return ModelStreamEvent(event_type="model_message_completed", model_message=model_message, raw_event=raw_event)  # 新增代码+DirectChatGptSseClient: 返回完成事件；如果没有这行代码，GUI 不知道模型已完成。

    @staticmethod  # 新增代码+DirectChatGptSseClient: 从完整 response 提取文本不依赖实例；如果没有这行代码，completed 事件解析会散落。
    def _extract_text_from_response(response: dict[str, Any]) -> str:  # 新增代码+DirectChatGptSseClient: 函数段开始，从 Responses 完整对象提取文本；如果没有这个函数，只有 response.completed 的流会丢文本，本段到 return 结束。
        output_text = response.get("output_text")  # 新增代码+DirectChatGptSseClient: 优先读取 output_text；如果没有这行代码，标准简化字段不会被识别。
        if isinstance(output_text, str):  # 新增代码+DirectChatGptSseClient: 如果 output_text 是字符串；如果没有这行代码，非字符串会被误返回。
            return output_text  # 新增代码+DirectChatGptSseClient: 直接返回完整文本；如果没有这行代码，标准响应文本会丢失。
        output = response.get("output")  # 新增代码+DirectChatGptSseClient: 兼容 output 数组；如果没有这行代码，复杂 Responses 响应无法提取文本。
        if isinstance(output, list):  # 新增代码+DirectChatGptSseClient: 只有数组才遍历；如果没有这行代码，非数组会被误处理。
            for item in output:  # 新增代码+DirectChatGptSseClient: 遍历 output item；如果没有这行代码，无法找到 message content。
                if not isinstance(item, dict):  # 新增代码+DirectChatGptSseClient: 跳过非对象项；如果没有这行代码，坏 item 会导致 .get 报错。
                    continue  # 新增代码+DirectChatGptSseClient: 继续下一个 item；如果没有这行代码，坏 item 会中断。
                content = item.get("content")  # 新增代码+DirectChatGptSseClient: 读取 content 数组；如果没有这行代码，无法拿到 output_text。
                if not isinstance(content, list):  # 新增代码+DirectChatGptSseClient: 只有 content 数组可遍历；如果没有这行代码，字符串 content 会被误遍历。
                    continue  # 新增代码+DirectChatGptSseClient: 跳过非数组 content；如果没有这行代码，坏形态会中断。
                for content_item in content:  # 新增代码+DirectChatGptSseClient: 遍历文本块；如果没有这行代码，无法找到 text 字段。
                    if isinstance(content_item, dict) and isinstance(content_item.get("text"), str):  # 新增代码+DirectChatGptSseClient: 找到标准文本块；如果没有这行代码，图片/非文本块会被误用。
                        return str(content_item["text"])  # 新增代码+DirectChatGptSseClient: 返回文本块内容；如果没有这行代码，复杂响应文本会丢失。
        return ""  # 新增代码+DirectChatGptSseClient: 没有可提取文本时返回空字符串；如果没有这行代码，函数可能返回 None。

    @staticmethod  # 新增代码+DirectChatGptSseClient: 完整 SSE 解析不依赖实例；如果没有这行代码，旧 wrapper 无法直接委托。
    def parse_sse_text_to_response(raw_stream: str) -> dict[str, object]:  # 新增代码+DirectChatGptSseClient: 函数段开始，把完整 Codex SSE 文本解析成 Responses 风格 dict；如果没有这个函数，旧 CodexOAuthChatModel 会继续维护独立 parser，本段到 return 结束。
        output_chunks: list[str] = []  # 新增代码+DirectChatGptSseClient: 收集 output_text.delta 分片；如果没有这行代码，纯文本流无法拼成最终回答。
        output_items: list[dict[str, Any]] = []  # 新增代码+DirectChatGptSseClient: 收集 native output item；如果没有这行代码，function_call/tool_search item 会丢失。
        pending_items: dict[str, dict[str, Any]] = {}  # 新增代码+DirectChatGptSseClient: 暂存 output_item.added；如果没有这行代码，arguments delta 没有 item 容器。
        argument_chunks: dict[str, list[str]] = {}  # 新增代码+DirectChatGptSseClient: 按 item_id 收集 function_call arguments；如果没有这行代码，流式工具参数无法拼接。
        completed_response: dict[str, object] | None = None  # 新增代码+DirectChatGptSseClient: 保存 response.completed 完整响应；如果没有这行代码，没有 delta 的流没有兜底。
        model_error: dict[str, object] | None = None  # 新增代码+DirectChatGptSseClient: 保存错误响应摘要；如果没有这行代码，模型不可用 fixture 无法返回结构化错误。
        for payload in ChatGptCodexSseClient._iter_sse_data_payloads(raw_stream.splitlines()):  # 新增代码+DirectChatGptSseClient: 遍历完整 SSE 文本里的 data payload；如果没有这行代码，event 行会污染 JSON 解析。
            if not payload or payload == "[DONE]":  # 新增代码+DirectChatGptSseClient: 跳过空 payload 和 DONE；如果没有这行代码，DONE 会被当 JSON 解析。
                continue  # 新增代码+DirectChatGptSseClient: 继续下一个 payload；如果没有这行代码，结束标记会打断可恢复解析。
            try:  # 新增代码+DirectChatGptSseClient: 捕获坏 JSON；如果没有这行代码，漂移 payload 会抛出底层异常。
                event = json.loads(payload)  # 新增代码+DirectChatGptSseClient: 解析事件对象；如果没有这行代码，无法读取类型和内容。
            except json.JSONDecodeError:  # 新增代码+DirectChatGptSseClient: 处理非法 JSON；如果没有这行代码，坏 payload 无法转成 drift 证据。
                model_error = {"status": "endpoint_drift_detected", "payload": payload[:500]}  # 新增代码+DirectChatGptSseClient: 保存端点漂移摘要；如果没有这行代码，调用方无法知道协议变化。
                continue  # 新增代码+DirectChatGptSseClient: 继续扫描后续 payload；如果没有这行代码，后续可能可恢复的 completed_response 会被错过。
            error_event = ChatGptCodexSseClient._error_event_from_payload(event)  # 新增代码+DirectChatGptSseClient: 复用错误归一化逻辑；如果没有这行代码，model_not_supported 无法统一映射。
            if error_event is not None:  # 新增代码+DirectChatGptSseClient: 如果当前事件是错误；如果没有这行代码，错误 payload 会继续走普通分支。
                model_error = dict(error_event.raw_event)  # 新增代码+DirectChatGptSseClient: 保存错误 raw_event；如果没有这行代码，parse 结果没有错误详情。
                continue  # 新增代码+DirectChatGptSseClient: 错误事件后继续扫描；如果没有这行代码，可能错过服务端附加信息。
            event_type = event.get("type")  # 新增代码+DirectChatGptSseClient: 读取事件类型；如果没有这行代码，无法分支处理不同 SSE 事件。
            if event_type == "response.output_text.delta" and isinstance(event.get("delta"), str):  # 新增代码+DirectChatGptSseClient: 捕获文本增量；如果没有这行代码，纯文本响应会为空。
                output_chunks.append(str(event["delta"]))  # 新增代码+DirectChatGptSseClient: 追加文本分片；如果没有这行代码，最终 output_text 拼不出来。
            if event_type == "response.output_text.done" and isinstance(event.get("text"), str):  # 新增代码+DirectChatGptSseClient: 捕获完整文本；如果没有这行代码，后端修正后的全文会被分片覆盖。
                output_chunks = [str(event["text"])]  # 新增代码+DirectChatGptSseClient: 用完整文本覆盖分片；如果没有这行代码，最终文本可能重复或不完整。
            if event_type == "response.output_item.added" and isinstance(event.get("item"), dict):  # 新增代码+DirectChatGptSseClient: 捕获 native output item 创建；如果没有这行代码，工具调用 item 没有暂存对象。
                item = copy.deepcopy(event["item"])  # 新增代码+DirectChatGptSseClient: 复制 item 以便回填；如果没有这行代码，修改会污染事件原文。
                item_id = str(item.get("id") or event.get("item_id") or "")  # 新增代码+DirectChatGptSseClient: 读取 item id；如果没有这行代码，参数分片无法归属。
                if item_id:  # 新增代码+DirectChatGptSseClient: 只有有效 id 才暂存；如果没有这行代码，多个无 id item 会混在一起。
                    pending_items[item_id] = item  # 新增代码+DirectChatGptSseClient: 保存待完成 item；如果没有这行代码，done 缺字段时无法合并。
            if event_type == "response.function_call_arguments.delta" and isinstance(event.get("delta"), str):  # 新增代码+DirectChatGptSseClient: 捕获 function_call 参数分片；如果没有这行代码，流式工具参数会丢失。
                item_id = str(event.get("item_id") or event.get("output_item_id") or "")  # 新增代码+DirectChatGptSseClient: 读取参数所属 item id；如果没有这行代码，无法按工具调用归类。
                if item_id:  # 新增代码+DirectChatGptSseClient: 有 item id 才记录；如果没有这行代码，空 id 会污染参数表。
                    argument_chunks.setdefault(item_id, []).append(str(event["delta"]))  # 新增代码+DirectChatGptSseClient: 追加参数分片；如果没有这行代码，最终 arguments 仍为空。
            if event_type == "response.function_call_arguments.done" and isinstance(event.get("arguments"), str):  # 新增代码+DirectChatGptSseClient: 捕获完整 function_call 参数；如果没有这行代码，done 事件里的最终参数会被忽略。
                item_id = str(event.get("item_id") or event.get("output_item_id") or "")  # 新增代码+DirectChatGptSseClient: 读取完整参数所属 item id；如果没有这行代码，无法覆盖分片。
                if item_id:  # 新增代码+DirectChatGptSseClient: 有 item id 才覆盖；如果没有这行代码，坏事件可能污染空 key。
                    argument_chunks[item_id] = [str(event["arguments"])]  # 新增代码+DirectChatGptSseClient: 用完整 arguments 覆盖分片；如果没有这行代码，分片可能缺最后修正。
            if event_type == "response.output_item.done" and isinstance(event.get("item"), dict):  # 新增代码+DirectChatGptSseClient: 捕获 native output item 完成；如果没有这行代码，function_call 不会进入 output 数组。
                item = copy.deepcopy(event["item"])  # 新增代码+DirectChatGptSseClient: 复制完成 item；如果没有这行代码，回填会修改原事件。
                item_id = str(item.get("id") or event.get("item_id") or "")  # 新增代码+DirectChatGptSseClient: 读取完成 item id；如果没有这行代码，无法找到对应分片和 added 快照。
                if item_id and not item.get("arguments") and item_id in argument_chunks:  # 新增代码+DirectChatGptSseClient: 当 done item 缺 arguments 时用分片补齐；如果没有这行代码，工具参数会丢失。
                    item["arguments"] = "".join(argument_chunks[item_id])  # 新增代码+DirectChatGptSseClient: 拼接参数分片；如果没有这行代码，工具执行器拿不到完整 JSON。
                if item_id and item_id in pending_items:  # 新增代码+DirectChatGptSseClient: 如果有 added 快照则合并；如果没有这行代码，done item 缺字段时无法恢复。
                    merged_item = copy.deepcopy(pending_items[item_id])  # 新增代码+DirectChatGptSseClient: 复制 added 快照；如果没有这行代码，合并会污染暂存对象。
                    merged_item.update(item)  # 新增代码+DirectChatGptSseClient: 用 done item 覆盖最新字段；如果没有这行代码，状态/参数无法更新。
                    item = merged_item  # 新增代码+DirectChatGptSseClient: 使用合并后的 item；如果没有这行代码，合并结果不会进入 output。
                output_items.append(item)  # 新增代码+DirectChatGptSseClient: 保存完成 item；如果没有这行代码，native 分支无法读取工具调用。
            if event_type == "response.completed" and isinstance(event.get("response"), dict):  # 新增代码+DirectChatGptSseClient: 捕获完整 response；如果没有这行代码，只有 completed 的流没有兜底。
                completed_response = event["response"]  # 新增代码+DirectChatGptSseClient: 保存完整响应；如果没有这行代码，后续无法返回服务端完整对象。
        if not output_items and pending_items:  # 新增代码+DirectChatGptSseClient: 如果只有 added/delta 没有 done，则尽量兜底；如果没有这行代码，异常但可恢复的 native 流会变空。
            for item_id, item in pending_items.items():  # 新增代码+DirectChatGptSseClient: 遍历暂存 item；如果没有这行代码，无法逐个补齐。
                pending_copy = copy.deepcopy(item)  # 新增代码+DirectChatGptSseClient: 复制暂存 item；如果没有这行代码，回填会修改原对象。
                if not pending_copy.get("arguments") and item_id in argument_chunks:  # 新增代码+DirectChatGptSseClient: 缺 arguments 且有分片时补齐；如果没有这行代码，兜底 item 仍缺参数。
                    pending_copy["arguments"] = "".join(argument_chunks[item_id])  # 新增代码+DirectChatGptSseClient: 拼接参数分片；如果没有这行代码，工具调用参数为空。
                output_items.append(pending_copy)  # 新增代码+DirectChatGptSseClient: 保存兜底 item；如果没有这行代码，added-only 流仍无 output。
        final_output_text = "".join(output_chunks)  # 新增代码+DirectChatGptSseClient: 拼接最终文本；如果没有这行代码，后续无法合并 message item。
        if final_output_text and output_items:  # 新增代码+DirectChatGptSseClient: 文本和 native item 同时存在时合并；如果没有这行代码，message 占位可能吞掉最终文本。
            output_text_attached = False  # 新增代码+DirectChatGptSseClient: 记录是否已把文本放进 message item；如果没有这行代码，可能重复追加文本消息。
            for item in output_items:  # 新增代码+DirectChatGptSseClient: 遍历 native output item；如果没有这行代码，无法找到 message 容器。
                if str(item.get("type", "") or "") != "message":  # 新增代码+DirectChatGptSseClient: 只把文本放入 message；如果没有这行代码，function_call item 会被污染。
                    continue  # 新增代码+DirectChatGptSseClient: 跳过非 message item；如果没有这行代码，工具调用结构会被改坏。
                item["content"] = [{"type": "output_text", "text": final_output_text}]  # 新增代码+DirectChatGptSseClient: 写入最终文本 content；如果没有这行代码，最终回答会空白。
                if item.get("status") == "in_progress":  # 新增代码+DirectChatGptSseClient: 如果 message 仍标记进行中；如果没有这行代码，审计会误以为未完成。
                    item["status"] = "completed"  # 新增代码+DirectChatGptSseClient: 标记 message 已完成；如果没有这行代码，状态和内容不一致。
                output_text_attached = True  # 新增代码+DirectChatGptSseClient: 标记文本已合并；如果没有这行代码，后续会重复追加 message。
            if not output_text_attached:  # 新增代码+DirectChatGptSseClient: 没有 message item 时创建一个；如果没有这行代码，纯文本加 reasoning/tool item 会丢文本。
                output_items.append({"type": "message", "status": "completed", "content": [{"type": "output_text", "text": final_output_text}], "role": "assistant"})  # 新增代码+DirectChatGptSseClient: 追加标准 message item；如果没有这行代码，native parser 取不到最终回答。
        if output_items:  # 新增代码+DirectChatGptSseClient: native output item 优先返回；如果没有这行代码，工具调用会被纯文本覆盖。
            return {"output": output_items}  # 新增代码+DirectChatGptSseClient: 返回 Responses output 数组；如果没有这行代码，native tools 分支无法继续。
        if final_output_text:  # 新增代码+DirectChatGptSseClient: 如果有纯文本；如果没有这行代码，普通回答会落到 completed_response 兜底。
            return {"output_text": final_output_text}  # 新增代码+DirectChatGptSseClient: 返回最终文本；如果没有这行代码，普通回答会丢失。
        if completed_response is not None:  # 新增代码+DirectChatGptSseClient: 如果只有完整 response；如果没有这行代码，非增量响应无返回。
            return completed_response  # 新增代码+DirectChatGptSseClient: 返回完整 response；如果没有这行代码，旧 wrapper 无法兜底解析。
        if model_error is not None:  # 新增代码+DirectChatGptSseClient: 如果只有错误事件；如果没有这行代码，模型不可用 fixture 会返回空文本。
            return {"error": model_error}  # 新增代码+DirectChatGptSseClient: 返回结构化错误；如果没有这行代码，上层无法更新模型可用性。
        return {"output_text": ""}  # 新增代码+DirectChatGptSseClient: 没有任何可用内容时返回空文本；如果没有这行代码，旧 wrapper 会收到 None。


__all__ = ["CHATGPT_CODEX_RESPONSES_ENDPOINT", "ChatGptCodexSseClient"]  # 新增代码+DirectChatGptSseClient: 明确公开端点和客户端；如果没有这行代码，模块 API 边界不清楚。
