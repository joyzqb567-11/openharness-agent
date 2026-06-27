"""Desktop GUI agent adapter boundary."""  # 新增代码+GuiAgentAdapter：说明本模块隔离 GUI 与真实 agent/harness；如果没有这一行，后续容易把模型运行时直接导入 GUI bridge。

from __future__ import annotations  # 新增代码+GuiAgentAdapter：启用未来注解语法；如果没有这一行，Protocol 和 dataclass 类型标注在旧行为下更容易出问题。

import json  # 新增代码+GuiAgentAdapter：读取 golden trace fixture；如果没有这一行，fake adapter 无法回放固定事件语料。
import os  # 新增代码+DirectSSEFixture：读取 OPENHARNESS_OPENAI_RUNTIME 开关；如果没有这一行，GUI adapter 无法进入 direct_sse_fixture 纵切路径。
import time  # 新增代码+DirectSseAdapter: 记录 Direct SSE 首包和总耗时诊断；如果没有这行代码，timeout/latency 事件缺少时间依据。
from dataclasses import dataclass, field  # 新增代码+GuiAgentAdapter：定义 adapter 请求和结果数据结构；如果没有这一行，边界会变成松散 dict。
from pathlib import Path  # 新增代码+GuiAgentAdapter：定位 repo 内 golden trace fixture；如果没有这一行，路径拼接容易在 Windows 上出错。
from typing import Callable, Protocol  # 新增代码+GuiAgentAdapter：定义 adapter 接口和回调类型；如果没有这一行，fake/real adapter 合同不清楚。

from learning_agent.app.gui_provider_openai_models import load_openai_model_registry, record_openai_last_known_good_model, save_openai_model_probe_result  # 新增代码+DirectSseAdapter: 复用 OpenAI 模型 registry；如果没有这行代码，模型不可用无法更新菜单状态。
from learning_agent.app.gui_provider_secret_store import make_provider_secret_store  # 新增代码+DirectSseAdapter: 复用 provider secret store 解出后端内部 token；如果没有这行代码，Direct SSE 无法读取 OAuth access token。
from learning_agent.app.gui_provider_settings import load_provider_settings  # 新增代码+DirectSseAdapter: 读取 OpenAI provider 连接状态；如果没有这行代码，adapter 不知道 provider 是否已连接。
from learning_agent.app.gui_protocol import make_event  # 新增代码+GuiAgentAdapter：复用 V2 事件生成 helper；如果没有这一行，adapter 事件形状会和协议模块分裂。
from learning_agent.models.chatgpt_codex_sse import ChatGptCodexSseClient, PostSseFunction  # 新增代码+DirectSseAdapter: 导入共享 ChatGPT Codex SSE 客户端和测试注入类型；如果没有这行代码，GUI adapter 会重新实现 HTTP/SSE。


GuiEventEmitter = Callable[[dict[str, object]], None]  # 新增代码+GuiAgentAdapter：定义事件发射回调类型；如果没有这一行，adapter 不知道如何把事件交给 bridge。
GuiCancelChecker = Callable[[], bool]  # 新增代码+GuiAgentAdapter：定义取消检查回调类型；如果没有这一行，adapter 无法和 GUI cancel 按钮协作。


@dataclass  # 新增代码+GuiAgentAdapter：自动生成请求对象初始化方法；如果没有这一行，请求字段要手写构造器。
class GuiAgentRunRequest:  # 新增代码+GuiAgentAdapter：请求类段开始，描述一次 GUI run；如果没有这个类，adapter 入参会散成多个字符串。
    session_id: str  # 新增代码+GuiAgentAdapter：保存会话 id；如果没有这一行，adapter 事件无法归属会话。
    turn_id: str  # 新增代码+GuiAgentAdapter：保存 turn id；如果没有这一行，事件无法关联消息。
    run_id: str  # 新增代码+GuiAgentAdapter：保存 run id；如果没有这一行，状态面板无法按运行聚合。
    prompt: str  # 新增代码+GuiAgentAdapter：保存用户 prompt；如果没有这一行，adapter 没有任务输入。
    workspace: str = ""  # 新增代码+DirectSseAdapter: 保存当前 workspace 路径；如果没有这行代码，adapter 无法读取 provider settings 和 secret store。
    trace_id: str = ""  # 新增代码+GuiAgentAdapter：可选 golden trace id；如果没有这一行，fake adapter 无法回放指定 GT 场景。
    mode: str = "fake"  # 新增代码+GuiAgentAdapter：保存请求模式；如果没有这一行，后续 real/fake 切换没有显式语义。
    provider_id: str = ""  # 新增代码+DirectSSEFixture：保存前端选择的 provider；如果没有这一行，后端无法证明 OpenAI 选择到达 adapter。
    model_id: str = ""  # 新增代码+DirectSSEFixture：保存前端选择的模型；如果没有这一行，direct SSE 请求无法使用用户选择模型。
    reasoning_effort: str = "high"  # 新增代码+DirectSSEFixture：保存前端选择的推理强度；如果没有这一行，后续真实请求无法继承 Codex 式努力等级。
    permission_mode: str = "full_access"  # 新增代码+DirectSSEFixture：保存前端选择的权限模式；如果没有这一行，后端无法把 GUI 权限选择传给运行时。
# 新增代码+GuiAgentAdapter：请求类段结束，GuiAgentRunRequest 到此结束；如果没有这个边界说明，用户不容易看出请求字段范围。


@dataclass  # 新增代码+GuiAgentAdapter：自动生成结果对象初始化方法；如果没有这一行，结果字段要手写构造器。
class GuiAgentRunResult:  # 新增代码+GuiAgentAdapter：结果类段开始，描述 adapter 终态；如果没有这个类，bridge 只能猜事件是否完成。
    status: str  # 新增代码+GuiAgentAdapter：保存 completed/failed/cancelled 等终态；如果没有这一行，bridge 不知道怎么同步消息状态。
    final_text: str = ""  # 新增代码+GuiAgentAdapter：保存最终文本；如果没有这一行，完成消息无法写回 session。
    error_code: str = ""  # 新增代码+GuiAgentAdapter：保存稳定错误码；如果没有这一行，前端无法机器处理 adapter 失败。
    error_message: str = ""  # 新增代码+GuiAgentAdapter：保存可读错误；如果没有这一行，用户只能看到泛化失败。
    events: list[dict[str, object]] = field(default_factory=list)  # 新增代码+GuiAgentAdapter：保存本次 run 事件副本；如果没有这一行，测试和诊断无法复盘 adapter 输出。
# 新增代码+GuiAgentAdapter：结果类段结束，GuiAgentRunResult 到此结束；如果没有这个边界说明，用户不容易看出结果字段范围。


class GuiAgentAdapter(Protocol):  # 新增代码+GuiAgentAdapter：接口段开始，定义 GUI adapter 必须实现的 run 方法；如果没有这个接口，fake 和 real adapter 容易分叉。
    def run(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, is_cancelled: GuiCancelChecker) -> GuiAgentRunResult:  # 新增代码+GuiAgentAdapter：声明 adapter run 合同；如果没有这一行，bridge 无法统一调用不同 adapter。
        ...  # 新增代码+GuiAgentAdapter：Protocol 方法占位；如果没有这一行，Python 语法不完整。
    # 新增代码+GuiAgentAdapter：接口方法段结束，run 到此结束；如果没有这个边界说明，用户不容易看出 adapter 主入口。
# 新增代码+GuiAgentAdapter：接口段结束，GuiAgentAdapter 到此结束；如果没有这个边界说明，用户不容易看出 fake/real 共同合同。


def _repo_root() -> Path:  # 新增代码+GuiAgentAdapter：函数段开始，定位仓库根目录；如果没有这段，golden fixture 路径会依赖当前工作目录。
    return Path(__file__).resolve().parents[2]  # 新增代码+GuiAgentAdapter：从 learning_agent/app 回到 repo 根；如果没有这一行，测试从别处运行会找不到 fixture。
# 新增代码+GuiAgentAdapter：函数段结束，_repo_root 到此结束；如果没有这个边界说明，用户不容易看出路径定位范围。


def _golden_fixture_path() -> Path:  # 新增代码+GuiAgentAdapter：函数段开始，返回 golden trace fixture 路径；如果没有这段，fake adapter 回放路径会散落。
    return _repo_root() / "apps" / "desktop" / "tests" / "fixtures" / "gui-v2-golden-events.json"  # 新增代码+GuiAgentAdapter：拼接 fixture 路径；如果没有这一行，GT 回放无法找到数据。
# 新增代码+GuiAgentAdapter：函数段结束，_golden_fixture_path 到此结束；如果没有这个边界说明，用户不容易看出 fixture 来源。


def _chatgpt_codex_sse_fixture_path() -> Path:  # 新增代码+DirectSSEFixture：函数段开始，定位 Task 0 的 ChatGPT Codex SSE fixture；如果没有这段，adapter 会依赖当前工作目录。
    return _repo_root() / "learning_agent" / "tests" / "fixtures" / "chatgpt_codex_sse" / "response_stream_basic.sse"  # 新增代码+DirectSSEFixture：返回脱敏 SSE 样本路径；如果没有这一行，direct_sse_fixture 无法读取黄金样本。
# 新增代码+DirectSSEFixture：函数段结束，_chatgpt_codex_sse_fixture_path 到此结束；如果没有边界说明，初学者不易看出 fixture 来源。


def _iter_sse_data_payloads(path: Path) -> list[dict[str, object]]:  # 新增代码+DirectSSEFixture：函数段开始，把 SSE data 行解析成 JSON payload；如果没有这段，fake SSE 只能靠字符串拼接。
    payloads: list[dict[str, object]] = []  # 新增代码+DirectSSEFixture：保存解析出的 SSE payload；如果没有这一行，函数没有累积结果。
    for line in path.read_text(encoding="utf-8").splitlines():  # 新增代码+DirectSSEFixture：逐行读取 fixture；如果没有这一行，无法识别多事件 SSE。
        if not line.startswith("data:"):  # 新增代码+DirectSSEFixture：只处理 SSE data 行；如果没有这一行，event 行会被当 JSON 解析失败。
            continue  # 新增代码+DirectSSEFixture：跳过非 data 行；如果没有这一行，后续会误读 event 名称。
        raw_payload = line.removeprefix("data:").strip()  # 新增代码+DirectSSEFixture：提取 data 后面的文本；如果没有这一行，JSON 字符串会带前缀。
        if raw_payload == "[DONE]":  # 新增代码+DirectSSEFixture：识别 SSE 结束哨兵；如果没有这一行，DONE 会被当 JSON 解析。
            break  # 新增代码+DirectSSEFixture：结束解析；如果没有这一行，函数会继续无意义遍历。
        parsed_payload = json.loads(raw_payload)  # 新增代码+DirectSSEFixture：解析真实形状 JSON payload；如果没有这一行，adapter 无法读取 delta/text 字段。
        if isinstance(parsed_payload, dict):  # 新增代码+DirectSSEFixture：只接受对象 payload；如果没有这一行，坏 fixture 可能污染事件。
            payloads.append(parsed_payload)  # 新增代码+DirectSSEFixture：保存当前 payload；如果没有这一行，解析结果不会返回。
    return payloads  # 新增代码+DirectSSEFixture：返回所有 JSON payload；如果没有这一行，调用方拿不到 SSE 内容。
# 新增代码+DirectSSEFixture：函数段结束，_iter_sse_data_payloads 到此结束；如果没有边界说明，初学者不易看出解析范围。


def _looks_like_safety_refusal_prompt(prompt: str) -> bool:  # 新增代码+GuiSafetyRefusal：函数段开始，识别 GUI 可见验收里的高风险请求；如果没有这段，真实用户式安全拒绝 prompt 只能靠隐藏 trace_id 触发。
    lowered_prompt = prompt.casefold()  # 新增代码+GuiSafetyRefusal：把英文提示转成大小写无关文本；如果没有这一行，Unsafe/BYPASS 这类写法可能漏判。
    refusal_markers = (  # 新增代码+GuiSafetyRefusal：集中维护安全拒绝触发词；如果没有这一段，判断条件会散落在 run 主流程里。
        "绕过本机权限",  # 新增代码+GuiSafetyRefusal：覆盖中文“绕过权限”场景；如果没有这一行，用户常见中文验收 prompt 不会触发拒绝。
        "绕过权限",  # 新增代码+GuiSafetyRefusal：覆盖较短中文表达；如果没有这一行，稍微简写的中文请求会被当成普通回答。
        "高风险操作",  # 新增代码+GuiSafetyRefusal：覆盖中文高风险操作表达；如果没有这一行，危险动作验收不能稳定出现安全拒绝。
        "直接控制系统",  # 新增代码+GuiSafetyRefusal：覆盖请求直接接管系统的中文表达；如果没有这一行，桌面控制越权语义可能漏判。
        "unsafe",  # 新增代码+GuiSafetyRefusal：覆盖英文 unsafe 触发词；如果没有这一行，英文安全拒绝验收不稳定。
        "bypass permission",  # 新增代码+GuiSafetyRefusal：覆盖英文绕过权限表达；如果没有这一行，英文用户 prompt 不能触发同一 GUI 路径。
        "bypass local permission",  # 新增代码+GuiSafetyRefusal：覆盖更具体的英文绕过本机权限表达；如果没有这一行，桌面权限绕过请求可能被误答。
    )  # 新增代码+GuiSafetyRefusal：触发词元组结束；如果没有这一行，Python 元组语法不完整。
    return any(marker in lowered_prompt for marker in refusal_markers)  # 新增代码+GuiSafetyRefusal：只要命中一个触发词就拒绝；如果没有这一行，函数不会输出判定结果。
# 新增代码+GuiSafetyRefusal：函数段结束，_looks_like_safety_refusal_prompt 到此结束；如果没有这个边界说明，用户不容易看出安全拒绝判定范围。


class FakeStreamingGuiAgentAdapter:  # 新增代码+GuiAgentAdapter：类段开始，提供 deterministic fake streaming adapter；如果没有这个类，V2-Core 会被真实模型不确定性污染。
    def __init__(self, direct_sse_post_sse: PostSseFunction | None = None, direct_sse_timeout_seconds: float = 120.0) -> None:  # 新增代码+DirectSseAdapter: 函数段开始，允许测试注入 Direct SSE 网络层；如果没有这段，adapter 测试必须真实连接 ChatGPT，本段到字段保存结束。
        self.direct_sse_post_sse = direct_sse_post_sse  # 新增代码+DirectSseAdapter: 保存可选假 SSE POST 函数；如果没有这行代码，测试无法验证 URL/header/body。
        self.direct_sse_timeout_seconds = max(float(direct_sse_timeout_seconds), 1.0)  # 新增代码+DirectSseAdapter: 保存至少 1 秒的 Direct SSE 超时；如果没有这行代码，0 或负数会让真实请求行为异常。
    # 新增代码+DirectSseAdapter: 函数段结束，FakeStreamingGuiAgentAdapter.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 direct SSE 注入点。

    def _emit(self, events: list[dict[str, object]], emit_event: GuiEventEmitter, event: dict[str, object]) -> None:  # 新增代码+GuiAgentAdapter：函数段开始，统一记录并发射事件；如果没有这段，测试和 bridge 看到的事件可能不一致。
        events.append(event)  # 新增代码+GuiAgentAdapter：保存事件副本；如果没有这一行，GuiAgentRunResult 无法复盘事件。
        emit_event(event)  # 新增代码+GuiAgentAdapter：把事件交给 bridge 或测试；如果没有这一行，UI 收不到 adapter 输出。
    # 新增代码+GuiAgentAdapter：函数段结束，FakeStreamingGuiAgentAdapter._emit 到此结束；如果没有这个边界说明，用户不容易看出发射逻辑。

    def _direct_sse_route_payload(self, request: GuiAgentRunRequest, runtime: str, codex_cli_used: bool) -> dict[str, object]:  # 新增代码+DirectSseAdapter: 函数段开始，生成 Direct SSE 路由诊断 payload；如果没有这段，runtime_path 事件字段会在多处分叉，本段到 return 结束。
        return {"provider_id": request.provider_id, "model_id": request.model_id, "runtime": runtime, "transport": "https_sse" if runtime == "direct_sse" else "codex_cli", "websocket_enabled": False if runtime == "direct_sse" else True, "codex_cli_used": codex_cli_used, "reasoning_effort": request.reasoning_effort, "permission_mode": request.permission_mode}  # 新增代码+DirectSseAdapter: 返回稳定路由摘要；如果没有这行代码，诊断面板无法确认 websocket_enabled=false。
    # 新增代码+DirectSseAdapter: 函数段结束，_direct_sse_route_payload 到此结束；如果没有边界说明，用户不容易看出它只做诊断字段。

    def _openai_auth_record(self, request: GuiAgentRunRequest) -> tuple[dict[str, object], str, str]:  # 新增代码+DirectSseAdapter: 函数段开始，读取 OpenAI OAuth 连接记录和 access token；如果没有这段，Direct SSE 无法判断 provider 是否已连接，本段到 return 结束。
        settings = load_provider_settings(request.workspace or _repo_root())  # 新增代码+DirectSseAdapter: 读取当前 workspace 的 provider settings；如果没有这行代码，连接状态没有事实源。
        auth = settings.get("auth", {}) if isinstance(settings.get("auth", {}), dict) else {}  # 新增代码+DirectSseAdapter: 安全读取 auth 区块；如果没有这行代码，坏配置会导致 adapter 崩溃。
        record = auth.get("openai", {}) if isinstance(auth.get("openai", {}), dict) else {}  # 新增代码+DirectSseAdapter: 读取 OpenAI auth 记录；如果没有这行代码，无法找到 OAuth secret_refs。
        if str(record.get("type", "")) != "oauth_real":  # 新增代码+DirectSseAdapter: 只有真实 OAuth 才允许 Direct SSE；如果没有这行代码，mock 或 API key 会被误当 ChatGPT OAuth。
            return {}, "", ""  # 新增代码+DirectSseAdapter: 未连接时返回空记录和空 token；如果没有这行代码，调用方要自己处理多种坏状态。
        secret_refs = record.get("secret_refs", {}) if isinstance(record.get("secret_refs", {}), dict) else {}  # 新增代码+DirectSseAdapter: 读取 token 引用组；如果没有这行代码，无法定位 access_token。
        access_ref = str(secret_refs.get("access_token", "") or "")  # 新增代码+DirectSseAdapter: 读取 access token 引用；如果没有这行代码，secret store 不知道解哪个 secret。
        secret_store = make_provider_secret_store(request.workspace or _repo_root())  # 新增代码+DirectSseAdapter: 创建当前 secret store；如果没有这行代码，os_encrypted/dev_json 模式无法统一读取。
        access_token = secret_store.get_secret(access_ref) if access_ref else ""  # 新增代码+DirectSseAdapter: 后端内部解出 access token；如果没有这行代码，Direct SSE 没有鉴权凭据。
        account_id = str(record.get("account_id", settings.get("selected_openai_account_id", "")) or "")  # 新增代码+DirectSseAdapter: 读取安全账号 id；如果没有这行代码，多账号请求无法写 ChatGPT-Account-Id。
        return record, access_token, account_id  # 新增代码+DirectSseAdapter: 返回连接记录、token 和账号 id；如果没有这行代码，调用方拿不到认证材料。
    # 新增代码+DirectSseAdapter: 函数段结束，_openai_auth_record 到此结束；如果没有边界说明，用户不容易看出它只在后端内部读取 token。

    def _selected_model_is_unsupported(self, request: GuiAgentRunRequest) -> bool:  # 新增代码+DirectSseAdapter: 函数段开始，判断用户选择模型是否已知不支持；如果没有这段，unsupported 模型会继续发请求浪费时间，本段到 return 结束。
        if not request.model_id.strip():  # 新增代码+DirectSseAdapter: 空模型视为不可用；如果没有这行代码，后端会把空模型发给 ChatGPT。
            return True  # 新增代码+DirectSseAdapter: 返回不可用；如果没有这行代码，调用方无法阻止空模型。
        registry = load_openai_model_registry(request.workspace or _repo_root())  # 新增代码+DirectSseAdapter: 读取模型 registry；如果没有这行代码，无法看到上次 probe 的 unsupported 状态。
        probe_results = registry.get("probe_results", {}) if isinstance(registry.get("probe_results", {}), dict) else {}  # 新增代码+DirectSseAdapter: 安全读取模型探针结果；如果没有这行代码，坏 registry 会拖垮 adapter。
        probe = probe_results.get(request.model_id, {}) if isinstance(probe_results.get(request.model_id, {}), dict) else {}  # 新增代码+DirectSseAdapter: 读取当前模型探针记录；如果没有这行代码，无法判断单个模型状态。
        return str(probe.get("state", "")) == "not_supported_for_account"  # 新增代码+DirectSseAdapter: 只有明确 unsupported 才拦截；如果没有这行代码，unknown 静态候选会被误禁用。
    # 新增代码+DirectSseAdapter: 函数段结束，_selected_model_is_unsupported 到此结束；如果没有边界说明，用户不容易看出它只做本地快速门禁。

    def _direct_sse_messages(self, request: GuiAgentRunRequest) -> list[dict[str, object]]:  # 新增代码+DirectSseAdapter: 函数段开始，构造 Direct SSE 最小 Responses input；如果没有这段，ChatGPT 后端看不到用户 prompt，本段到 return 结束。
        return [{"role": "user", "content": [{"type": "input_text", "text": request.prompt}]}]  # 新增代码+DirectSseAdapter: 返回标准 input_text 消息；如果没有这行代码，真实请求 body 会缺少输入内容。
    # 新增代码+DirectSseAdapter: 函数段结束，_direct_sse_messages 到此结束；如果没有边界说明，用户不容易看出它只做请求输入转换。

    def _direct_sse_extra_body(self, request: GuiAgentRunRequest) -> dict[str, object]:  # 新增代码+DirectSseAdapter: 函数段开始，构造 Direct SSE 附加 body 字段；如果没有这段，reasoning/权限诊断无法进入请求，本段到 return 结束。
        return {"reasoning": {"effort": request.reasoning_effort}, "metadata": {"permission_mode": request.permission_mode, "openharness_runtime": "direct_sse"}}  # 新增代码+DirectSseAdapter: 返回低敏 metadata 和 reasoning 设置；如果没有这行代码，模型调用无法反映底部菜单选择。
    # 新增代码+DirectSseAdapter: 函数段结束，_direct_sse_extra_body 到此结束；如果没有边界说明，用户不容易看出它只补充 body。

    def _run_direct_sse(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, is_cancelled: GuiCancelChecker) -> GuiAgentRunResult:  # 新增代码+DirectSseAdapter: 函数段开始，使用 ChatGPT OAuth access token 走 HTTPS/SSE；如果没有这段，GUI 仍只能 fake 或旧 Codex CLI，本段到最终 return 结束。
        events: list[dict[str, object]] = []  # 新增代码+DirectSseAdapter: 保存本轮 Direct SSE 事件副本；如果没有这行代码，测试无法复盘流式顺序。
        partial_text = ""  # 新增代码+DirectSseAdapter: 保存已到达的助手文本；如果没有这行代码，取消后无法保留 partial output。
        started_at = time.monotonic()  # 新增代码+DirectSseAdapter: 记录请求开始时间；如果没有这行代码，首包和总耗时诊断无法计算。
        route_payload = self._direct_sse_route_payload(request, "direct_sse", codex_cli_used=False)  # 新增代码+DirectSseAdapter: 构造 route 诊断；如果没有这行代码，runtime_path 事件缺少统一字段。
        self._emit(events, emit_event, make_event("runtime_path", 1, route_payload, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSseAdapter: 发出第一条 runtime_path；如果没有这行代码，GUI 无法确认没有走 WebSocket/Codex CLI。
        if request.provider_id != "openai":  # 新增代码+DirectSseAdapter: Direct SSE V3 只处理 OpenAI OAuth provider；如果没有这行代码，其他 provider 会误走 ChatGPT 后端。
            self._emit(events, emit_event, make_event("provider_not_connected", 2, {"status": "provider_not_connected", **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSseAdapter: 发出 provider 未连接事件；如果没有这行代码，GUI 只会看到泛化失败。
            return GuiAgentRunResult(status="failed", error_code="provider_not_connected", error_message="OpenAI provider 未连接。", events=events)  # 新增代码+DirectSseAdapter: 返回未连接失败；如果没有这行代码，bridge 不知道终态。
        auth_record, access_token, account_id = self._openai_auth_record(request)  # 新增代码+DirectSseAdapter: 读取真实 OAuth token 和账号；如果没有这行代码，无法创建 SSE 客户端。
        if not auth_record or not access_token:  # 新增代码+DirectSseAdapter: 连接记录或 token 缺失都算未连接；如果没有这行代码，空 token 会发到后端。
            self._emit(events, emit_event, make_event("provider_not_connected", 2, {"status": "provider_not_connected", **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSseAdapter: 发出未连接诊断；如果没有这行代码，设置问题不清楚。
            return GuiAgentRunResult(status="failed", error_code="provider_not_connected", error_message="OpenAI OAuth provider 未连接或 access token 缺失。", events=events)  # 新增代码+DirectSseAdapter: 返回失败结果；如果没有这行代码，bridge 会继续等待。
        if self._selected_model_is_unsupported(request):  # 新增代码+DirectSseAdapter: 快速拦截已知不可用模型；如果没有这行代码，用户会继续等远端错误。
            save_openai_model_probe_result(request.workspace or _repo_root(), request.model_id, "not_supported_for_account", "模型不适用于当前 ChatGPT OAuth 账号。")  # 新增代码+DirectSseAdapter: 写入模型不可用状态；如果没有这行代码，模型菜单不会更新。
            self._emit(events, emit_event, make_event("model_not_available", 2, {"status": "model_not_available", **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSseAdapter: 发出模型不可用事件；如果没有这行代码，GUI 无法给出明确提示。
            return GuiAgentRunResult(status="failed", error_code="model_not_available", error_message="所选 OpenAI/ChatGPT OAuth 模型不可用。", events=events)  # 新增代码+DirectSseAdapter: 返回失败结果；如果没有这行代码，bridge 不知道终态。
        client = ChatGptCodexSseClient(access_token=access_token, model=request.model_id, account_id=account_id, post_sse=self.direct_sse_post_sse, timeout_seconds=self.direct_sse_timeout_seconds)  # 新增代码+DirectSseAdapter: 创建共享 Direct SSE 客户端；如果没有这行代码，adapter 会重新实现 HTTP/SSE。
        stream = client.stream_responses(messages=self._direct_sse_messages(request), tools=None, extra_body=self._direct_sse_extra_body(request))  # 新增代码+DirectSseAdapter: 发起事件流生成器；如果没有这行代码，模型调用不会开始。
        first_delta_seen = False  # 新增代码+DirectSseAdapter: 记录是否已看到首个 delta；如果没有这行代码，first_byte_timeout 无法诊断。
        try:  # 新增代码+DirectSseAdapter: 捕获流式迭代异常；如果没有这行代码，worker 线程会直接崩溃。
            for model_event in stream:  # 新增代码+DirectSseAdapter: 逐个消费模型事件；如果没有这行代码，GUI 收不到增量或完成。
                if model_event.event_type == "text_delta":  # 新增代码+DirectSseAdapter: 处理文本增量；如果没有这行代码，流式文字不会显示。
                    if not first_delta_seen:  # 新增代码+DirectSseAdapter: 首个 delta 到达时记录延迟；如果没有这行代码，诊断无法计算首包。
                        first_delta_seen = True  # 新增代码+DirectSseAdapter: 标记已收到首包；如果没有这行代码，后续每个 delta 都会被当首包。
                        route_payload["first_delta_latency_ms"] = int((time.monotonic() - started_at) * 1000)  # 新增代码+DirectSseAdapter: 写入首包延迟毫秒；如果没有这行代码，性能面板没有依据。
                    partial_text += model_event.text_delta  # 新增代码+DirectSseAdapter: 累积 partial text；如果没有这行代码，取消时无法保留已显示内容。
                    self._emit(events, emit_event, make_event("message_delta", len(events) + 1, {"text_delta": model_event.text_delta, **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSseAdapter: 发出 GUI 文本增量；如果没有这行代码，前端不会实时显示。
                    if is_cancelled():  # 新增代码+DirectSseAdapter: delta 后检查取消；如果没有这行代码，用户点击取消后还会继续读流。
                        stream.close()  # 新增代码+DirectSseAdapter: 关闭生成器并触发底层 response.close；如果没有这行代码，HTTP SSE 连接可能不释放。
                        self._emit(events, emit_event, make_event("turn_cancelled", len(events) + 1, {"status": "cancelled", "partial_text": partial_text, **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSseAdapter: 发出取消事件并带 partial text；如果没有这行代码，GUI 无法显示已取消输出。
                        return GuiAgentRunResult(status="cancelled", final_text=partial_text, error_message="用户已取消 Direct SSE 运行。", events=events)  # 新增代码+DirectSseAdapter: 返回取消结果；如果没有这行代码，bridge 会误判为失败。
                    continue  # 新增代码+DirectSseAdapter: 当前 delta 已处理；如果没有这行代码，会继续落入后续分支。
                if model_event.event_type == "model_message_completed":  # 新增代码+DirectSseAdapter: 处理完成事件；如果没有这行代码，completion-before-cancel 无法保持 completed。
                    final_text = model_event.model_message.text if model_event.model_message is not None else partial_text  # 新增代码+DirectSseAdapter: 选择完整文本或 partial 兜底；如果没有这行代码，完成事件可能没有正文。
                    record_openai_last_known_good_model(request.workspace or _repo_root(), request.model_id)  # 新增代码+DirectSseAdapter: 记录真实成功模型；如果没有这行代码，last-known-good 菜单不会更新。
                    save_openai_model_probe_result(request.workspace or _repo_root(), request.model_id, "available", "Direct SSE 调用成功。")  # 新增代码+DirectSseAdapter: 保存模型可用探针状态；如果没有这行代码，菜单状态不会变绿。
                    self._emit(events, emit_event, make_event("direct_sse_completed", len(events) + 1, {"status": "completed", "total_turn_latency_ms": int((time.monotonic() - started_at) * 1000), **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSseAdapter: 发出 Direct SSE 完成诊断；如果没有这行代码，状态面板不知道直连完成。
                    self._emit(events, emit_event, make_event("message_completed", len(events) + 1, {"final_text": final_text, **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSseAdapter: 发出 GUI 完成事件；如果没有这行代码，前端消息不会进入 completed。
                    return GuiAgentRunResult(status="completed", final_text=final_text, events=events)  # 新增代码+DirectSseAdapter: 返回完成结果；如果没有这行代码，bridge 不会写回答案。
                if model_event.event_type == "model_error":  # 新增代码+DirectSseAdapter: 处理模型错误事件；如果没有这行代码，远端错误会被忽略。
                    error_status = str(model_event.raw_event.get("status", "direct_sse_failed"))  # 新增代码+DirectSseAdapter: 读取归一化错误状态；如果没有这行代码，错误事件没有稳定类型。
                    if error_status == "model_not_available":  # 新增代码+DirectSseAdapter: 识别模型不可用；如果没有这行代码，registry 无法标记 unsupported。
                        save_openai_model_probe_result(request.workspace or _repo_root(), request.model_id, "not_supported_for_account", str(model_event.raw_event.get("message", "")))  # 新增代码+DirectSseAdapter: 写入 unsupported 状态；如果没有这行代码，坏模型会继续出现在可用列表。
                    event_kind = "model_not_available" if error_status == "model_not_available" else error_status  # 新增代码+DirectSseAdapter: 选择可见事件类型；如果没有这行代码，所有错误都会叫 model_error。
                    self._emit(events, emit_event, make_event(event_kind, len(events) + 1, {**model_event.raw_event, **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSseAdapter: 发出错误事件；如果没有这行代码，GUI 诊断没有失败细节。
                    return GuiAgentRunResult(status="failed", error_code=error_status, error_message=str(model_event.raw_event.get("message", error_status)), events=events)  # 新增代码+DirectSseAdapter: 返回失败结果；如果没有这行代码，bridge 不知道终态。
        except TimeoutError as error:  # 新增代码+DirectSseAdapter: 处理 Python 显式 timeout；如果没有这行代码，timeout 会变成泛化失败。
            self._emit(events, emit_event, make_event("total_turn_timeout", len(events) + 1, {"status": "total_turn_timeout", "error": str(error), **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSseAdapter: 发出总超时事件；如果没有这行代码，诊断没有 timeout class。
            return GuiAgentRunResult(status="failed", error_code="total_turn_timeout", error_message=str(error), events=events)  # 新增代码+DirectSseAdapter: 返回超时失败；如果没有这行代码，bridge 终态不稳定。
        self._emit(events, emit_event, make_event("idle_stream_timeout", len(events) + 1, {"status": "idle_stream_timeout", **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSseAdapter: 流结束但无完成时按 idle timeout 诊断；如果没有这行代码，GUI 会看到空失败。
        return GuiAgentRunResult(status="failed", error_code="idle_stream_timeout", error_message="Direct SSE 流结束但没有 completion 事件。", events=events)  # 新增代码+DirectSseAdapter: 返回失败结果；如果没有这行代码，bridge 无法释放 active turn。
    # 新增代码+DirectSseAdapter: 函数段结束，_run_direct_sse 到此结束；如果没有边界说明，用户不容易看出真实 Direct SSE 生命周期范围。

    def _run_direct_sse_fixture(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, is_cancelled: GuiCancelChecker) -> GuiAgentRunResult:  # 新增代码+DirectSSEFixture：函数段开始，回放脱敏 ChatGPT Codex SSE 样本；如果没有这段，Task 1 无法证明 direct_sse 的 GUI streaming 管线。
        events: list[dict[str, object]] = []  # 新增代码+DirectSSEFixture：保存本次 fixture 事件；如果没有这一行，测试无法复盘 delta 顺序。
        final_text = ""  # 新增代码+DirectSSEFixture：保存 SSE done 事件里的最终文本；如果没有这一行，完成态没有可写回消息的 answer。
        route_payload = {"runtime": "direct_sse_fixture", "transport": "https_sse", "websocket_enabled": False, "codex_cli_used": False, "provider_id": request.provider_id, "model_id": request.model_id, "reasoning_effort": request.reasoning_effort, "permission_mode": request.permission_mode}  # 新增代码+DirectSSEFixture：暴露纵切路由诊断；如果没有这一行，GUI 无法确认没有走 Codex CLI/WebSocket。
        self._emit(events, emit_event, make_event("direct_sse_route_selected", 1, route_payload, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSSEFixture：发出 direct route 事件；如果没有这一行，诊断面板看不到 runtime=direct_sse_fixture。
        for sequence, payload in enumerate(_iter_sse_data_payloads(_chatgpt_codex_sse_fixture_path()), start=2):  # 新增代码+DirectSSEFixture：按 SSE payload 顺序回放；如果没有这一行，message_delta 不会来自真实形状样本。
            if is_cancelled():  # 新增代码+DirectSSEFixture：每个 SSE payload 前检查取消；如果没有这一行，长 fixture 后续无法被取消按钮中断。
                self._emit(events, emit_event, make_event("turn_cancelled", sequence, {"status": "cancelled", **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSSEFixture：发出取消事件；如果没有这一行，GUI 会停在 running。
                return GuiAgentRunResult(status="cancelled", events=events)  # 新增代码+DirectSSEFixture：返回取消结果；如果没有这一行，bridge 会继续写 completed。
            event_type = str(payload.get("type", ""))  # 新增代码+DirectSSEFixture：读取 ChatGPT SSE type；如果没有这一行，无法区分 delta/done/completed。
            if event_type == "response.output_text.delta":  # 新增代码+DirectSSEFixture：识别流式文本增量；如果没有这一行，OPENHARNESS_ 和 OK 不会分片显示。
                self._emit(events, emit_event, make_event("message_delta", sequence, {"text_delta": str(payload.get("delta", "")), **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSSEFixture：把 SSE delta 转成 GUI message_delta；如果没有这一行，前端看不到流式输出。
            elif event_type == "response.output_text.done":  # 新增代码+DirectSSEFixture：识别最终文本事件；如果没有这一行，final_text 会一直为空。
                final_text = str(payload.get("text", ""))  # 新增代码+DirectSSEFixture：保存最终文本；如果没有这一行，完成消息无法写回 OPENHARNESS_OK。
            elif event_type == "response.completed":  # 新增代码+DirectSSEFixture：识别响应完成事件；如果没有这一行，诊断无法知道 fixture 流已完成。
                self._emit(events, emit_event, make_event("direct_sse_completed", sequence, {"status": "completed", **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSSEFixture：发出 direct SSE 完成诊断；如果没有这一行，状态面板缺少 direct_sse 完成证据。
        self._emit(events, emit_event, make_event("message_completed", len(events) + 1, {"final_text": final_text, **route_payload}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSSEFixture：发出 GUI 完成事件；如果没有这一行，前端无法进入 completed 并显示最终文本。
        return GuiAgentRunResult(status="completed", final_text=final_text, events=events)  # 新增代码+DirectSSEFixture：返回完成结果；如果没有这一行，bridge 不知道要写回哪个 final_text。
    # 新增代码+DirectSSEFixture：函数段结束，_run_direct_sse_fixture 到此结束；如果没有边界说明，初学者不易看出 fixture 纵切范围。

    def _replay_trace(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, is_cancelled: GuiCancelChecker) -> GuiAgentRunResult:  # 新增代码+GuiAgentAdapter：函数段开始，回放 golden trace；如果没有这段，前端和 bridge 测试无法共享固定事件语料。
        traces = json.loads(_golden_fixture_path().read_text(encoding="utf-8"))  # 新增代码+GuiAgentAdapter：读取 JSON fixture；如果没有这一行，adapter 无法获得 GT 场景。
        trace = next((item for item in traces if item.get("id") == request.trace_id), None)  # 新增代码+GuiAgentAdapter：按 trace_id 查找场景；如果没有这一行，无法选择指定 GT。
        if not isinstance(trace, dict):  # 新增代码+GuiAgentAdapter：处理未知 trace；如果没有这一行，后续访问会报错。
            failed_event = make_event("turn_failed", 1, {"error_code": "trace_not_found", "error": f"Golden trace not found: {request.trace_id}"}, run_id=request.run_id, turn_id=request.turn_id)  # 新增代码+GuiAgentAdapter：构造 trace 缺失失败事件；如果没有这一行，未知 GT 会静默失败。
            emit_event(failed_event)  # 新增代码+GuiAgentAdapter：发出失败事件；如果没有这一行，UI 不知道回放失败。
            return GuiAgentRunResult(status="failed", error_code="trace_not_found", error_message=str(failed_event["payload"]))  # 新增代码+GuiAgentAdapter：返回失败结果；如果没有这一行，bridge 不知道终态。
        events: list[dict[str, object]] = []  # 新增代码+GuiAgentAdapter：保存回放事件；如果没有这一行，结果无法复盘。
        for raw_event in trace.get("events", []):  # 新增代码+GuiAgentAdapter：按 fixture 顺序遍历事件；如果没有这一行，回放不会发出事件。
            if is_cancelled():  # 新增代码+GuiAgentAdapter：每个事件前检查取消；如果没有这一行，回放无法响应取消。
                cancel_event = make_event("turn_cancelled", int(raw_event.get("sequence", 0)), {"status": "cancelled"}, run_id=request.run_id, turn_id=request.turn_id)  # 新增代码+GuiAgentAdapter：构造取消事件；如果没有这一行，取消没有终态事件。
                self._emit(events, emit_event, cancel_event)  # 新增代码+GuiAgentAdapter：发出取消事件；如果没有这一行，UI 无法进入取消态。
                return GuiAgentRunResult(status="cancelled", events=events)  # 新增代码+GuiAgentAdapter：返回取消结果；如果没有这一行，bridge 会继续当完成。
            event = make_event(str(raw_event.get("kind", "heartbeat")), int(raw_event.get("sequence", 0)), raw_event.get("payload", {}) if isinstance(raw_event.get("payload", {}), dict) else {}, run_id=request.run_id, turn_id=request.turn_id)  # 新增代码+GuiAgentAdapter：把 fixture 事件转成当前 run 身份；如果没有这一行，事件会带旧 turn/run。
            self._emit(events, emit_event, event)  # 新增代码+GuiAgentAdapter：发出回放事件；如果没有这一行，前端收不到 GT 事件。
        final_event = events[-1] if events else {}  # 新增代码+GuiAgentAdapter：读取最后事件；如果没有这一行，final_text 提取没有来源。
        final_payload = final_event.get("payload", {}) if isinstance(final_event.get("payload", {}), dict) else {}  # 新增代码+GuiAgentAdapter：安全读取最后 payload；如果没有这一行，坏 fixture 会拖垮回放。
        return GuiAgentRunResult(status="completed", final_text=str(final_payload.get("final_text", "")), events=events)  # 新增代码+GuiAgentAdapter：返回完成结果；如果没有这一行，bridge 不知道回放完成。
    # 新增代码+GuiAgentAdapter：函数段结束，FakeStreamingGuiAgentAdapter._replay_trace 到此结束；如果没有这个边界说明，用户不容易看出回放范围。

    def run(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, is_cancelled: GuiCancelChecker) -> GuiAgentRunResult:  # 新增代码+GuiAgentAdapter：函数段开始，执行 deterministic fake streaming；如果没有这段，V2-Core 没有稳定 adapter。
        runtime = os.environ.get("OPENHARNESS_OPENAI_RUNTIME", "").strip()  # 修改代码+DirectSseAdapter: 读取 OpenAI runtime 开关；如果没有这行代码，adapter 无法区分 fixture/direct/codex_cli 路线。
        if runtime == "direct_sse":  # 新增代码+DirectSseAdapter: 识别真实 Direct ChatGPT OAuth SSE runtime；如果没有这行代码，GUI 仍会走 fake streaming。
            return self._run_direct_sse(request, emit_event, is_cancelled)  # 新增代码+DirectSseAdapter: 执行真实 Direct SSE 路线；如果没有这行代码，OAuth 连接后也不会调用模型。
        if runtime == "codex_cli":  # 新增代码+DirectSseAdapter: 识别显式旧 Codex CLI fallback；如果没有这行代码，用户无法从诊断看到 codex_cli_used=true。
            events: list[dict[str, object]] = []  # 新增代码+DirectSseAdapter: 准备保存 codex_cli fallback 事件；如果没有这行代码，返回结果无法复盘。
            route_payload = self._direct_sse_route_payload(request, "codex_cli", codex_cli_used=True)  # 新增代码+DirectSseAdapter: 构造 codex_cli 路由诊断；如果没有这行代码，fallback 无法显式标记。
            self._emit(events, emit_event, make_event("runtime_path", 1, route_payload, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+DirectSseAdapter: 发出 codex_cli_used=true 事件；如果没有这行代码，用户无法确认旧路径被显式选择。
            return GuiAgentRunResult(status="failed", error_code="codex_cli_not_wired_for_gui_v3", error_message="Codex CLI fallback 需要显式后续接线；当前 direct_sse 才是 V3 默认真实路径。", events=events)  # 新增代码+DirectSseAdapter: 返回明确未接线失败；如果没有这行代码，GUI 会假装 fallback 已经调用。
        if runtime == "direct_sse_fixture":  # 新增代码+DirectSSEFixture：识别 Task 1 的 fixture direct SSE runtime；如果没有这一行，GUI 纵切会继续走普通 fake streaming。
            return self._run_direct_sse_fixture(request, emit_event, is_cancelled)  # 新增代码+DirectSSEFixture：执行 SSE fixture 回放；如果没有这一行，OPENHARNESS_OK 不会从 SSE 样本流出。
        if request.trace_id:  # 新增代码+GuiAgentAdapter：优先处理 golden trace 回放；如果没有这一行，指定 trace_id 会被普通回答忽略。
            return self._replay_trace(request, emit_event, is_cancelled)  # 新增代码+GuiAgentAdapter：执行 fixture 回放；如果没有这一行，GT 测试无法通过。
        events: list[dict[str, object]] = []  # 新增代码+GuiAgentAdapter：保存本次 fake 事件；如果没有这一行，结果无法复盘。
        try:  # 新增代码+GuiAgentAdapter：捕获 deterministic fake 异常；如果没有这一行，失败会变成线程崩溃。
            if "__adapter_fail__" in request.prompt or "__fail__" in request.prompt:  # 修改代码+GuiAgentAdapter：识别 fake 专用和旧生命周期失败触发词；如果没有这一行，默认 V2 路径会漏掉旧失败验收。
                raise RuntimeError("deterministic fake adapter failure")  # 新增代码+GuiAgentAdapter：抛出可控异常；如果没有这一行，失败路径没有实际异常。
            self._emit(events, emit_event, make_event("turn_started", 1, {"status": "running"}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiAgentAdapter：发出 turn_started；如果没有这一行，前端看不到运行起点。
            delta_text = f"OpenHarness Desktop 正在处理：{request.prompt}"  # 新增代码+GuiAgentAdapter：构造 deterministic delta 文本；如果没有这一行，message_delta 没有内容。
            self._emit(events, emit_event, make_event("message_delta", 2, {"text_delta": delta_text}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiAgentAdapter：发出流式文本增量；如果没有这一行，GUI 无法测试打字式输出。
            if _looks_like_safety_refusal_prompt(request.prompt):  # 新增代码+GuiSafetyRefusal：在普通流式开头后拦截高风险请求；如果没有这一行，安全拒绝不会进入真实可见 GUI 消息流。
                refusal_text = "我不能绕过本机权限或执行高风险操作；可以改为说明安全边界、权限确认流程，或生成低风险的模拟验收步骤。"  # 新增代码+GuiSafetyRefusal：构造可见安全拒绝正文；如果没有这一行，用户只会看到空的拒绝事件。
                self._emit(events, emit_event, make_event("safety_refusal", 3, {"text": refusal_text, "policy": "desktop_permission_safety"}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiSafetyRefusal：发出一等安全拒绝事件；如果没有这一行，前端无法显示拒绝标签。
                return GuiAgentRunResult(status="completed", final_text=refusal_text, events=events)  # 新增代码+GuiSafetyRefusal：以完成态结束拒绝轮次；如果没有这一行，bridge 不会释放 active turn。
            if is_cancelled():  # 新增代码+GuiAgentAdapter：delta 后检查取消；如果没有这一行，取消会等到完成后才生效。
                self._emit(events, emit_event, make_event("turn_cancelled", 3, {"status": "cancelled"}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiAgentAdapter：发出取消终态；如果没有这一行，前端无法进入 cancelled。
                return GuiAgentRunResult(status="cancelled", events=events)  # 新增代码+GuiAgentAdapter：返回取消结果；如果没有这一行，bridge 会误写 completed。
            final_text = f"OpenHarness Desktop 已完成 fake streaming 回答：{request.prompt}"  # 新增代码+GuiAgentAdapter：构造 deterministic final_text；如果没有这一行，完成消息没有正文。
            self._emit(events, emit_event, make_event("message_completed", 3, {"final_text": final_text}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiAgentAdapter：发出完成事件；如果没有这一行，前端无法进入 completed。
            return GuiAgentRunResult(status="completed", final_text=final_text, events=events)  # 新增代码+GuiAgentAdapter：返回完成结果；如果没有这一行，bridge 不知道 final_text。
        except Exception as error:  # 新增代码+GuiAgentAdapter：捕获 fake adapter 失败；如果没有这一行，异常不会变成 turn_failed。
            failed_event = make_event("turn_failed", len(events) + 1, {"status": "failed", "error_code": "adapter_failed", "error": str(error)}, run_id=request.run_id, turn_id=request.turn_id)  # 新增代码+GuiAgentAdapter：构造结构化失败事件；如果没有这一行，GUI 无法显示失败原因。
            self._emit(events, emit_event, failed_event)  # 新增代码+GuiAgentAdapter：发出失败事件；如果没有这一行，前端状态机不会进入 failed。
            return GuiAgentRunResult(status="failed", error_code="adapter_failed", error_message=str(error), events=events)  # 新增代码+GuiAgentAdapter：返回失败结果；如果没有这一行，bridge 不知道终态。
    # 新增代码+GuiAgentAdapter：函数段结束，FakeStreamingGuiAgentAdapter.run 到此结束；如果没有这个边界说明，用户不容易看出 fake 执行范围。
# 新增代码+GuiAgentAdapter：类段结束，FakeStreamingGuiAgentAdapter 到此结束；如果没有这个边界说明，用户不容易看出 fake adapter 范围。


class DefaultHarnessGuiAgentAdapter:  # 新增代码+GuiAgentAdapter：类段开始，真实 harness adapter 的 feature-flagged shell；如果没有这个类，调用方无法显式请求真实模式并得到稳定失败。
    def __init__(self, enabled: bool = False) -> None:  # 新增代码+GuiAgentAdapter：函数段开始，保存真实 adapter 是否启用；如果没有这段，真实入口可能被误用。
        self.enabled = enabled  # 新增代码+GuiAgentAdapter：保存 feature flag；如果没有这一行，禁用状态无法判断。
    # 新增代码+GuiAgentAdapter：函数段结束，DefaultHarnessGuiAgentAdapter.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def run(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, _is_cancelled: GuiCancelChecker) -> GuiAgentRunResult:  # 新增代码+GuiAgentAdapter：函数段开始，真实 harness adapter 暂不接线；如果没有这段，显式真实模式没有稳定响应。
        if not self.enabled:  # 新增代码+GuiAgentAdapter：真实 adapter 未启用时拒绝；如果没有这一行，V2-Core 可能误入真实 runtime。
            message = "Default harness GUI adapter is not enabled in V2-Core."  # 新增代码+GuiAgentAdapter：构造低敏错误信息；如果没有这一行，用户看不到为什么不可用。
            emit_event(make_event("turn_failed", 1, {"status": "failed", "error_code": "adapter_unavailable", "error": message}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiAgentAdapter：发出 adapter_unavailable 失败事件；如果没有这一行，前端无法显示真实模式被禁用。
            return GuiAgentRunResult(status="failed", error_code="adapter_unavailable", error_message=message)  # 新增代码+GuiAgentAdapter：返回稳定失败结果；如果没有这一行，bridge 不知道终态。
        message = "Default harness GUI adapter real entry point is intentionally deferred."  # 新增代码+GuiAgentAdapter：构造启用但未实现的错误；如果没有这一行，真实 adapter 仍不清楚为何失败。
        emit_event(make_event("turn_failed", 1, {"status": "failed", "error_code": "adapter_unavailable", "error": message}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiAgentAdapter：发出未实现失败事件；如果没有这一行，前端无法显示真实 adapter 未完成。
        return GuiAgentRunResult(status="failed", error_code="adapter_unavailable", error_message=message)  # 新增代码+GuiAgentAdapter：返回未实现失败结果；如果没有这一行，调用方会误以为成功。
    # 新增代码+GuiAgentAdapter：函数段结束，DefaultHarnessGuiAgentAdapter.run 到此结束；如果没有这个边界说明，用户不容易看出真实 adapter shell 范围。
# 新增代码+GuiAgentAdapter：类段结束，DefaultHarnessGuiAgentAdapter 到此结束；如果没有这个边界说明，用户不容易看出真实 adapter 仍未接线。
