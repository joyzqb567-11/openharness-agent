"""Desktop GUI agent adapter boundary."""  # 新增代码+GuiAgentAdapter：说明本模块隔离 GUI 与真实 agent/harness；如果没有这一行，后续容易把模型运行时直接导入 GUI bridge。

from __future__ import annotations  # 新增代码+GuiAgentAdapter：启用未来注解语法；如果没有这一行，Protocol 和 dataclass 类型标注在旧行为下更容易出问题。

import json  # 新增代码+GuiAgentAdapter：读取 golden trace fixture；如果没有这一行，fake adapter 无法回放固定事件语料。
import os  # 新增代码+DirectOAuthModelFactory：读取 direct OAuth 和 Codex 模型环境变量；如果没有这行代码，默认真实模型工厂无法按运行模式选择后端。
import inspect  # 新增代码+ComposerRealModelRouting：读取工厂和连接读取器签名；如果没有这一行，无法在兼容旧无参回调的同时把 GUI 模型上下文传给新回调。
import time  # 新增代码+真实模型延迟可观测性：读取单调时钟来计算阻塞式模型调用耗时；如果没有这行，GUI 状态面板无法解释真实模型等待了多久。
from dataclasses import dataclass, field  # 新增代码+GuiAgentAdapter：定义 adapter 请求和结果数据结构；如果没有这一行，边界会变成松散 dict。
from pathlib import Path  # 新增代码+GuiAgentAdapter：定位 repo 内 golden trace fixture；如果没有这一行，路径拼接容易在 Windows 上出错。
from typing import Any, Callable, Protocol  # 修改代码+真实模型GUI适配器：补充 Any 用来描述注入模型对象；如果没有这一行，真实模型 factory 的类型标注会不清楚。

from learning_agent.app.gui_protocol import make_event  # 新增代码+GuiAgentAdapter：复用 V2 事件生成 helper；如果没有这一行，adapter 事件形状会和协议模块分裂。
from learning_agent.models.streaming import ModelStreamEvent  # 新增代码+真实模型延迟可观测性：引入流式模型事件协议；如果没有这行，adapter 不能识别模型阶段、首 token 和完成事件。


GuiEventEmitter = Callable[[dict[str, object]], None]  # 新增代码+GuiAgentAdapter：定义事件发射回调类型；如果没有这一行，adapter 不知道如何把事件交给 bridge。
GuiCancelChecker = Callable[[], bool]  # 新增代码+GuiAgentAdapter：定义取消检查回调类型；如果没有这一行，adapter 无法和 GUI cancel 按钮协作。
RealModelFactory = Callable[..., Any]  # 修改代码+ComposerRealModelRouting：允许真实模型工厂接收可选 GuiAgentRunRequest；如果没有这一行，下拉模型选择无法进入模型创建过程。
ProviderConnectionReader = Callable[..., bool]  # 修改代码+ComposerRealModelRouting：允许连接读取器接收可选 provider_id；如果没有这一行，多 provider 场景只能检查固定 OpenAI。
ModelFailureRecorder = Callable[[str, str, str, str], None]  # 新增代码+ModelFailureState：定义模型失败记录回调；如果没有这一行，adapter 无法把 OAuth 模型拒绝写回 provider catalog。


@dataclass  # 新增代码+GuiAgentAdapter：自动生成请求对象初始化方法；如果没有这一行，请求字段要手写构造器。
class GuiAgentRunRequest:  # 新增代码+GuiAgentAdapter：请求类段开始，描述一次 GUI run；如果没有这个类，adapter 入参会散成多个字符串。
    session_id: str  # 新增代码+GuiAgentAdapter：保存会话 id；如果没有这一行，adapter 事件无法归属会话。
    turn_id: str  # 新增代码+GuiAgentAdapter：保存 turn id；如果没有这一行，事件无法关联消息。
    run_id: str  # 新增代码+GuiAgentAdapter：保存 run id；如果没有这一行，状态面板无法按运行聚合。
    prompt: str  # 新增代码+GuiAgentAdapter：保存用户 prompt；如果没有这一行，adapter 没有任务输入。
    trace_id: str = ""  # 新增代码+GuiAgentAdapter：可选 golden trace id；如果没有这一行，fake adapter 无法回放指定 GT 场景。
    mode: str = "fake"  # 新增代码+GuiAgentAdapter：保存请求模式；如果没有这一行，后续 real/fake 切换没有显式语义。
    provider_id: str = ""  # 新增代码+ComposerModelToolbar：保存 GUI 本轮选择的 provider；如果没有这一行，adapter 无法知道 prompt 来自哪个模型提供商。
    model_id: str = ""  # 新增代码+ComposerModelToolbar：保存 GUI 本轮选择的模型；如果没有这一行，真实模型路由无法消费用户的模型选择。
    reasoning_effort: str = ""  # 新增代码+ComposerModelToolbar：保存 GUI 本轮选择的推理强度；如果没有这一行，adapter 无法审计用户选择的是低/中/高/超高。
    permission_mode: str = ""  # 新增代码+ComposerModelToolbar：保存 GUI 本轮选择的权限模式；如果没有这一行，后端运行时不知道本轮是否为完全访问。
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


def _callable_accepts_positional_argument(callback: Callable[..., Any]) -> bool:  # 新增代码+ComposerRealModelRouting：函数段开始，判断回调是否能接收一个位置参数；如果没有这段，adapter 要么永远无参调用要么打碎旧测试替身。
    try:  # 新增代码+ComposerRealModelRouting：保护签名读取；如果没有这一行，内建函数或特殊 mock 可能让真实轮次直接失败。
        signature = inspect.signature(callback)  # 新增代码+ComposerRealModelRouting：读取 callable 的参数签名；如果没有这一行，无法安全区分新旧回调形态。
    except (TypeError, ValueError):  # 新增代码+ComposerRealModelRouting：处理没有 Python 签名的 callable；如果没有这一行，特殊对象会抛出底层异常。
        return False  # 新增代码+ComposerRealModelRouting：未知签名时保守按旧无参回调处理；如果没有这一行，兼容路径不稳定。
    for parameter in signature.parameters.values():  # 新增代码+ComposerRealModelRouting：遍历参数定义；如果没有这一行，无法识别可接收位置参数的回调。
        if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.VAR_POSITIONAL):  # 新增代码+ComposerRealModelRouting：只要能接收位置参数就允许传 request/provider；如果没有这一行，新模型工厂拿不到 GUI 上下文。
            return True  # 新增代码+ComposerRealModelRouting：确认可传一个位置参数；如果没有这一行，判断结果不会返回成功。
    return False  # 新增代码+ComposerRealModelRouting：没有可用位置参数时按旧无参调用；如果没有这一行，函数可能隐式返回 None。
# 新增代码+ComposerRealModelRouting：函数段结束，_callable_accepts_positional_argument 到此结束；如果没有边界说明，用户不容易看出它只做兼容判断。


def _callable_accepts_keyword_argument(callback: Callable[..., Any], keyword: str) -> bool:  # 新增代码+CodexCliCancelBridge：函数段开始，判断回调是否能接收指定关键字参数；如果没有这段，adapter 不能安全把取消信号传给支持它的模型。
    try:  # 新增代码+CodexCliCancelBridge：保护签名读取；如果没有这一行，内建函数或特殊 mock 可能让真实轮次直接失败。
        signature = inspect.signature(callback)  # 新增代码+CodexCliCancelBridge：读取 callable 的参数签名；如果没有这一行，无法区分新旧 stream_chat 形态。
    except (TypeError, ValueError):  # 新增代码+CodexCliCancelBridge：处理没有 Python 签名的 callable；如果没有这一行，特殊对象会抛底层异常。
        return False  # 新增代码+CodexCliCancelBridge：未知签名时保守不传额外参数；如果没有这一行，旧模型可能因为未知关键字失败。
    for parameter in signature.parameters.values():  # 新增代码+CodexCliCancelBridge：遍历所有参数定义；如果没有这一行，无法识别 keyword 或 **kwargs。
        if parameter.kind == inspect.Parameter.VAR_KEYWORD:  # 新增代码+CodexCliCancelBridge：支持 **kwargs 的 callable 可以接收任意关键字；如果没有这一行，通用适配器拿不到取消信号。
            return True  # 新增代码+CodexCliCancelBridge：确认可传关键字参数；如果没有这一行，判断结果不会返回成功。
        if parameter.name == keyword and parameter.kind in (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):  # 新增代码+CodexCliCancelBridge：识别显式声明的 is_cancelled 参数；如果没有这一行，Codex CLI 模型的取消入口不会被使用。
            return True  # 新增代码+CodexCliCancelBridge：确认可传指定关键字；如果没有这一行，判断结果不会返回成功。
    return False  # 新增代码+CodexCliCancelBridge：没有匹配参数时按旧模型处理；如果没有这一行，函数可能隐式返回 None。
# 新增代码+CodexCliCancelBridge：函数段结束，_callable_accepts_keyword_argument 到此结束；如果没有边界说明，用户不容易看出它只做兼容判断。


def _selected_model_name(request: GuiAgentRunRequest | None, fallback_env_name: str = "CODEX_MODEL", fallback_model: str = "gpt-5.5") -> str:  # 新增代码+ComposerRealModelRouting：函数段开始，从 GUI 请求优先读取模型名；如果没有这段，OAuth 真实调用只能使用环境变量固定模型。
    selected_model = str(getattr(request, "model_id", "") or "").strip() if request is not None else ""  # 新增代码+ComposerRealModelRouting：读取下拉选择的 model_id；如果没有这一行，用户刚选的模型不会进入后端。
    if selected_model:  # 新增代码+ComposerRealModelRouting：优先使用 GUI 明确选择；如果没有这一行，空字符串和有效模型无法区分。
        return selected_model  # 新增代码+ComposerRealModelRouting：返回用户选择的模型；如果没有这一行，下拉菜单无法控制真实模型。
    return os.environ.get(fallback_env_name, fallback_model).strip() or fallback_model  # 新增代码+ComposerRealModelRouting：没有 GUI 选择时回退环境变量；如果没有这一行，老启动方式会丢失默认模型。
# 新增代码+ComposerRealModelRouting：函数段结束，_selected_model_name 到此结束；如果没有边界说明，用户不容易看出模型优先级。


def _model_failure_kind_from_message(message: str) -> str:  # 新增代码+ModelFailureState：函数段开始，把真实模型错误文本归类成稳定错误种类；如果没有这段，ChatGPT OAuth 模型拒绝会被当成普通失败。
    folded_message = str(message or "").casefold()  # 新增代码+ModelFailureState：统一大小写后再匹配；如果没有这行，The/the 或 GPT/gpt 差异会导致漏判。
    unsupported_markers = ("not supported when using codex with a chatgpt account", "model is not supported", "is not supported", "unsupported model")  # 新增代码+ModelFailureState：列出 Codex/OpenAI 常见模型不支持文本；如果没有这行，错误分类没有事实依据。
    if any(marker in folded_message for marker in unsupported_markers):  # 新增代码+ModelFailureState：只要命中任一模型不支持提示就归类；如果没有这行，模型拒绝无法进入 model_unsupported。
        return "model_unsupported"  # 新增代码+ModelFailureState：返回稳定错误种类；如果没有这行，provider catalog 无法按要求保存 error_kind。
    return ""  # 新增代码+ModelFailureState：无法归类时返回空；如果没有这行，普通网络失败可能被误标成模型不可用。
# 新增代码+ModelFailureState：函数段结束，_model_failure_kind_from_message 到此结束；如果没有边界说明，用户不容易看出它只做错误分类。


def _readable_model_failure_message(request: GuiAgentRunRequest, error_kind: str, raw_message: str) -> str:  # 新增代码+ModelFailureState：函数段开始，把底层错误转成用户可读中文提示；如果没有这段，GUI 会继续显示英文 JSON 错误。
    if error_kind == "model_unsupported":  # 新增代码+ModelFailureState：处理 OAuth 账号不支持目标模型的场景；如果没有这行，用户不知道要换模型而不是继续等。
        return f"所选模型 {request.model_id or '当前模型'} 当前 ChatGPT OAuth 账号不支持，请在底部模型菜单切换可用模型。"  # 新增代码+ModelFailureState：返回明确换模型提示；如果没有这行，用户会把模型拒绝误解成网络慢。
    return str(raw_message or "真实模型调用失败。")  # 新增代码+ModelFailureState：其它错误保留原始低敏信息；如果没有这行，普通失败会丢失排查线索。
# 新增代码+ModelFailureState：函数段结束，_readable_model_failure_message 到此结束；如果没有边界说明，用户不容易看出它只改展示文案。


class GuiDirectOAuthCodexTokenStoreAdapter:  # 新增代码+DirectOAuthModelFactory：类段开始，把 GUI token store 适配成 CodexOAuthChatModel 需要的 load/save 协议；如果没有这个类，direct OAuth token 刷新不能写回 OpenHarness 加密存储。
    def __init__(self, token_store: Any | None = None, provider_id: str = "openai") -> None:  # 新增代码+DirectOAuthModelFactory：函数段开始，注入 GUI token store 和 provider id；如果没有这段代码，测试无法使用 fake store，真实运行也不知道读取哪个 provider。
        if token_store is None:  # 新增代码+DirectOAuthModelFactory：未注入时使用真实默认 token store；如果没有这行代码，真实 GUI direct OAuth 运行时没有 token 来源。
            from learning_agent.app.gui_provider_oauth_token_store import default_oauth_token_store  # 新增代码+DirectOAuthModelFactory：延迟导入默认 OS 加密 token store；如果没有这行代码，模块导入会提前触碰 Windows DPAPI 相关逻辑。

            token_store = default_oauth_token_store()  # 新增代码+DirectOAuthModelFactory：创建真实 OS 加密 token store；如果没有这行代码，适配器无法读取用户登录后的 token。
        self.token_store = token_store  # 新增代码+DirectOAuthModelFactory：保存底层 GUI token store；如果没有这行代码，load/save 无法访问实际存储。
        self.provider_id = str(provider_id or "openai").strip() or "openai"  # 新增代码+DirectOAuthModelFactory：保存 provider id 并兜底 openai；如果没有这行代码，空 provider 会导致 token 路径不稳定。
    # 新增代码+DirectOAuthModelFactory：函数段结束，GuiDirectOAuthCodexTokenStoreAdapter.__init__ 到此结束；如果没有边界说明，用户不容易看出初始化不读取 raw token。

    def load(self) -> Any | None:  # 新增代码+DirectOAuthModelFactory：函数段开始，按 CodexOAuthChatModel 协议读取 token；如果没有这段代码，模型调用前无法拿到 access/refresh token。
        from learning_agent.models.adapters import CodexOAuthTokens  # 新增代码+DirectOAuthModelFactory：延迟导入 token 数据对象避免 GUI 层启动时加载模型大模块；如果没有这行代码，load 无法返回模型期望类型。

        payload = self.token_store.get_tokens(self.provider_id)  # 新增代码+DirectOAuthModelFactory：从 GUI token store 读取后端 raw token；如果没有这行代码，direct OAuth 登录状态无法进入模型请求。
        if not payload:  # 新增代码+DirectOAuthModelFactory：处理未登录或损坏 token；如果没有这行代码，后续字段读取会抛异常。
            return None  # 新增代码+DirectOAuthModelFactory：未登录返回 None 让模型决定是否重新登录；如果没有这行代码，空 token 会被误当有效。
        return CodexOAuthTokens(access_token=str(payload.get("access_token", "")), refresh_token=str(payload.get("refresh_token", "")), expires_at=int(payload.get("expires_at") or 0), account_id=payload.get("account_id") or None, id_token=str(payload.get("id_token", "")))  # 新增代码+DirectOAuthModelFactory：把 GUI token dict 转成 Codex token 对象；如果没有这行代码，模型无法构造鉴权 header 或刷新 token。
    # 新增代码+DirectOAuthModelFactory：函数段结束，GuiDirectOAuthCodexTokenStoreAdapter.load 到此结束；如果没有边界说明，用户不容易看出 raw token 只留在后端内存。

    def save(self, tokens: Any) -> None:  # 新增代码+DirectOAuthModelFactory：函数段开始，按 CodexOAuthChatModel 协议保存刷新后的 token；如果没有这段代码，access token 刷新后不会持久化。
        self.token_store.set_tokens(self.provider_id, {"access_token": str(getattr(tokens, "access_token", "")), "refresh_token": str(getattr(tokens, "refresh_token", "")), "expires_at": int(getattr(tokens, "expires_at", 0) or 0), "account_id": getattr(tokens, "account_id", None), "id_token": str(getattr(tokens, "id_token", ""))})  # 新增代码+DirectOAuthModelFactory：把模型 token 对象写回 GUI token store；如果没有这行代码，刷新结果会丢失且下次仍用旧 token。
    # 新增代码+DirectOAuthModelFactory：函数段结束，GuiDirectOAuthCodexTokenStoreAdapter.save 到此结束；如果没有边界说明，用户不容易看出保存仍然不经过 renderer。
# 新增代码+DirectOAuthModelFactory：类段结束，GuiDirectOAuthCodexTokenStoreAdapter 到此结束；如果没有边界说明，用户不容易看出它只是协议桥。


def _int_env(name: str, default: int, minimum: int) -> int:  # 新增代码+DirectOAuthModelFactory：函数段开始，安全读取整数环境变量；如果没有这段代码，timeout 配置错误会让 GUI 启动失败。
    raw_value = os.environ.get(name, str(default)).strip()  # 新增代码+DirectOAuthModelFactory：读取原始字符串并兜底默认值；如果没有这行代码，空变量会进入 int 转换。
    try:  # 新增代码+DirectOAuthModelFactory：捕获非法数字；如果没有这行代码，用户填错环境变量会抛到 GUI。
        return max(int(raw_value), int(minimum))  # 新增代码+DirectOAuthModelFactory：返回不低于下限的整数；如果没有这行代码，超短 timeout 会制造假失败。
    except ValueError:  # 新增代码+DirectOAuthModelFactory：处理非数字配置；如果没有这行代码，错误配置无法回退。
        return int(default)  # 新增代码+DirectOAuthModelFactory：非法值回到默认值；如果没有这行代码，GUI 无法稳态启动。
# 新增代码+DirectOAuthModelFactory：函数段结束，_int_env 到此结束；如果没有边界说明，用户不容易看出它只读环境变量。


def _default_direct_oauth_model_factory(request: GuiAgentRunRequest | None = None) -> Any:  # 修改代码+ComposerRealModelRouting：函数段开始，按 GUI 请求创建 direct OAuth 的 CodexOAuthChatModel；如果没有这段代码，direct OAuth 已连接后主聊天仍不能按下拉模型调用真实后端。
    from learning_agent.app.gui_provider_openai_auth_config import build_openai_auth_config  # 新增代码+DirectOAuthModelFactory：复用 direct OAuth 三重门禁和显式 client id；如果没有这行代码，模型层可能绕过安全配置。
    from learning_agent.models.adapters import CodexOAuthChatModel  # 新增代码+DirectOAuthModelFactory：延迟导入 Codex OAuth 模型；如果没有这行代码，工厂无法创建真实模型对象。

    config = build_openai_auth_config()  # 新增代码+DirectOAuthModelFactory：读取并校验 direct OAuth 配置；如果没有这行代码，缺 client id 或非 OS 加密也可能继续运行。
    model_name = _selected_model_name(request)  # 修改代码+ComposerRealModelRouting：优先读取 GUI 底部模型下拉，其次才回退 CODEX_MODEL；如果没有这一行，用户切换 GPT-5.5/GPT-4.1 不会影响真实请求。
    oauth_timeout_seconds = _int_env("CODEX_OAUTH_TIMEOUT_SECONDS", 300, 60)  # 新增代码+DirectOAuthModelFactory：读取 OAuth 等待超时；如果没有这行代码，重新登录等待时间无法配置。
    sse_timeout_seconds = _int_env("CODEX_OAUTH_SSE_READ_TIMEOUT_SECONDS", 240, 30)  # 新增代码+DirectOAuthModelFactory：读取 Codex SSE 总超时；如果没有这行代码，真实模型流式读取可能无限等待。
    token_store = GuiDirectOAuthCodexTokenStoreAdapter()  # 新增代码+DirectOAuthModelFactory：创建 GUI token store 适配器；如果没有这行代码，模型无法读取 direct OAuth 登录 token。
    return CodexOAuthChatModel(model=model_name, token_store=token_store, oauth_timeout_seconds=oauth_timeout_seconds, sse_read_timeout_seconds=sse_timeout_seconds, client_id=config.client_id)  # 新增代码+DirectOAuthModelFactory：返回绑定 OpenHarness client id 的 Codex OAuth 模型；如果没有这行代码，refresh/token exchange 可能误用 OpenCode client id。
# 修改代码+ComposerRealModelRouting：函数段结束，_default_direct_oauth_model_factory 到此结束；如果没有边界说明，用户不容易看出它只创建模型不发请求。


def _default_real_model_factory(request: GuiAgentRunRequest | None = None) -> Any:  # 修改代码+ComposerRealModelRouting：函数段开始，按本轮 GUI 请求创建默认真实模型；如果没有这段，真实 adapter 只能靠固定环境变量决定模型。
    clean_provider_id = str(getattr(request, "provider_id", "") or "openai").strip() or "openai"  # 新增代码+ComposerRealModelRouting：读取本轮 provider 并默认 OpenAI；如果没有这一行，空 provider 会让默认路径无法兼容旧调用。
    if clean_provider_id != "openai":  # 新增代码+ComposerRealModelRouting：当前 ChatGPT OAuth V1 只支持 OpenAI provider；如果没有这一行，Google/OpenRouter 可能被误发到 OpenAI OAuth 后端。
        raise RuntimeError(f"当前真实 ChatGPT OAuth 路径只支持 OpenAI provider，收到：{clean_provider_id}")  # 新增代码+ComposerRealModelRouting：返回清晰错误；如果没有这一行，用户会误以为非 OpenAI 下拉已可真实调用。
    if os.environ.get("OPENHARNESS_OPENAI_AUTH_MODE", "mock").strip().lower() == "direct_oauth":  # 新增代码+DirectOAuthModelFactory：direct OAuth 模式下切到 CodexOAuthChatModel；如果没有这行代码，GUI 登录成功后仍会尝试 Codex CLI。
        return _default_direct_oauth_model_factory(request)  # 修改代码+ComposerRealModelRouting：返回带 GUI 模型选择的 direct OAuth 模型；如果没有这行代码，token store 适配器不会按用户下拉创建模型。
    from learning_agent.models.adapters import CodexCliChatModel  # 新增代码+真实模型GUI适配器：延迟导入 CodexCliChatModel；如果没有这一行，默认真实模式无法调用官方 Codex CLI。

    codex_command = os.environ.get("CODEX_COMMAND", "codex").strip() or "codex"  # 修改代码+ComposerRealModelRouting：保留 Codex CLI 命令仍来自环境变量；如果没有这一行，用户无法继续用自定义 codex 可执行文件。
    model_name = _selected_model_name(request)  # 修改代码+ComposerRealModelRouting：优先读取 GUI 底部选中的模型，其次回退 CODEX_MODEL；如果没有这一行，Codex CLI/OAuth 兼容路径会忽略模型下拉。
    timeout_seconds = _int_env("CODEX_TIMEOUT_SECONDS", 300, 30)  # 修改代码+ComposerRealModelRouting：保留 CLI 超时配置并防止太短；如果没有这一行，长模型调用可能被硬编码默认值影响。
    return CodexCliChatModel(codex_command=codex_command, model=model_name, cwd=_repo_root(), timeout_seconds=timeout_seconds)  # 修改代码+ComposerRealModelRouting：创建带 GUI 模型选择的 Codex CLI 模型；如果没有这一行，真实 OAuth 兼容调用无法按用户选择路由。
# 修改代码+ComposerRealModelRouting：函数段结束，_default_real_model_factory 到此结束；如果没有这个边界说明，用户不容易看出默认模型来源。


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
    def _emit(self, events: list[dict[str, object]], emit_event: GuiEventEmitter, event: dict[str, object]) -> None:  # 新增代码+GuiAgentAdapter：函数段开始，统一记录并发射事件；如果没有这段，测试和 bridge 看到的事件可能不一致。
        events.append(event)  # 新增代码+GuiAgentAdapter：保存事件副本；如果没有这一行，GuiAgentRunResult 无法复盘事件。
        emit_event(event)  # 新增代码+GuiAgentAdapter：把事件交给 bridge 或测试；如果没有这一行，UI 收不到 adapter 输出。
    # 新增代码+GuiAgentAdapter：函数段结束，FakeStreamingGuiAgentAdapter._emit 到此结束；如果没有这个边界说明，用户不容易看出发射逻辑。

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


class RealModelGuiAgentAdapter:  # 新增代码+真实模型GUI适配器：类段开始，把 GUI run 接到真实模型接口；如果没有这个类，桌面外壳只能继续 fake streaming。
    def __init__(self, model_factory: RealModelFactory | None = None, connected_provider_reader: ProviderConnectionReader | None = None, delta_chunk_size: int = 600, model_failure_recorder: ModelFailureRecorder | None = None) -> None:  # 修改代码+ModelFailureState：函数段开始，注入模型工厂、连接状态读取器和模型失败记录器；如果没有这段，真实 adapter 很难测试和把不支持模型写回 catalog。
        self.model_factory = model_factory or _default_real_model_factory  # 新增代码+真实模型GUI适配器：保存模型工厂；如果没有这一行，adapter 不知道如何创建 CodexCliChatModel。
        self.connected_provider_reader = connected_provider_reader or (lambda: False)  # 新增代码+真实模型GUI适配器：保存连接门禁读取器；如果没有这一行，未授权状态也可能触发模型调用。
        self.delta_chunk_size = max(1, int(delta_chunk_size))  # 新增代码+真实模型GUI适配器：保存流式切片大小且保证至少为 1；如果没有这一行，切片大小为 0 会导致循环异常。
        self.model_failure_recorder = model_failure_recorder  # 新增代码+ModelFailureState：保存模型失败记录回调；如果没有这一行，模型不支持错误无法进入 provider 设置事实源。
    # 新增代码+真实模型GUI适配器：函数段结束，RealModelGuiAgentAdapter.__init__ 到此结束；如果没有这个边界说明，用户不容易看出依赖注入范围。

    def _emit(self, events: list[dict[str, object]], emit_event: GuiEventEmitter, event: dict[str, object]) -> None:  # 新增代码+真实模型GUI适配器：函数段开始，统一记录并发射真实模型事件；如果没有这段，结果 events 和 GUI 收到的事件可能不一致。
        events.append(event)  # 新增代码+真实模型GUI适配器：保存事件副本；如果没有这一行，GuiAgentRunResult 无法复盘真实模型输出。
        emit_event(event)  # 新增代码+真实模型GUI适配器：把事件交给 bridge 或测试；如果没有这一行，前端收不到真实模型事件。
    # 新增代码+真实模型GUI适配器：函数段结束，RealModelGuiAgentAdapter._emit 到此结束；如果没有这个边界说明，用户不容易看出发射逻辑。

    def _text_chunks(self, text: str) -> list[str]:  # 新增代码+真实模型GUI适配器：函数段开始，把最终文本拆成 GUI 可显示的 delta；如果没有这段，真实模型只能一次性完成没有流式体验。
        if not text:  # 新增代码+真实模型GUI适配器：处理空文本回答；如果没有这一行，空回答不会产生 message_delta，前端可能缺少中间态。
            return [""]  # 新增代码+真实模型GUI适配器：为空文本保留一个空 delta；如果没有这一行，事件顺序会少掉 message_delta。
        return [text[index : index + self.delta_chunk_size] for index in range(0, len(text), self.delta_chunk_size)]  # 新增代码+真实模型GUI适配器：按固定长度切片；如果没有这一行，长回答会变成单个巨大事件。
    # 新增代码+真实模型GUI适配器：函数段结束，RealModelGuiAgentAdapter._text_chunks 到此结束；如果没有这个边界说明，用户不容易看出流式切片范围。

    def _fail(self, request: GuiAgentRunRequest, events: list[dict[str, object]], emit_event: GuiEventEmitter, sequence: int, error_code: str, message: str) -> GuiAgentRunResult:  # 新增代码+真实模型GUI适配器：函数段开始，统一返回结构化失败；如果没有这段，错误事件和结果错误码容易不一致。
        failed_event = make_event("turn_failed", sequence, {"status": "failed", "error_code": error_code, "error": message}, run_id=request.run_id, turn_id=request.turn_id)  # 新增代码+真实模型GUI适配器：构造失败事件；如果没有这一行，前端无法展示真实模型失败原因。
        self._emit(events, emit_event, failed_event)  # 新增代码+真实模型GUI适配器：发出失败事件；如果没有这一行，GUI 状态机不会进入 failed。
        return GuiAgentRunResult(status="failed", error_code=error_code, error_message=message, events=events)  # 新增代码+真实模型GUI适配器：返回失败结果；如果没有这一行，bridge 不知道真实模型轮次已经失败。
    # 新增代码+真实模型GUI适配器：函数段结束，RealModelGuiAgentAdapter._fail 到此结束；如果没有这个边界说明，用户不容易看出失败封装范围。

    def _cancel(self, request: GuiAgentRunRequest, events: list[dict[str, object]], emit_event: GuiEventEmitter, sequence: int) -> GuiAgentRunResult:  # 新增代码+真实模型GUI适配器：函数段开始，统一返回取消终态；如果没有这段，取消事件和结果状态容易分裂。
        self._emit(events, emit_event, make_event("turn_cancelled", sequence, {"status": "cancelled"}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型GUI适配器：发出取消事件；如果没有这一行，前端取消按钮不会产生可见终态。
        return GuiAgentRunResult(status="cancelled", events=events)  # 新增代码+真实模型GUI适配器：返回取消结果；如果没有这一行，bridge 可能误写 completed。
    # 新增代码+真实模型GUI适配器：函数段结束，RealModelGuiAgentAdapter._cancel 到此结束；如果没有这个边界说明，用户不容易看出取消封装范围。

    def _provider_is_connected(self, request: GuiAgentRunRequest) -> bool:  # 新增代码+ComposerRealModelRouting：函数段开始，按本轮 provider 检查真实模型连接；如果没有这段，adapter 只能检查固定 OpenAI 状态。
        provider_id = str(request.provider_id or "openai").strip() or "openai"  # 新增代码+ComposerRealModelRouting：读取 provider_id 并默认 OpenAI；如果没有这一行，旧调用的空 provider 会被误判未连接。
        if _callable_accepts_positional_argument(self.connected_provider_reader):  # 新增代码+ComposerRealModelRouting：兼容新 provider 感知读取器；如果没有这一行，多 provider 连接门禁拿不到 provider_id。
            return bool(self.connected_provider_reader(provider_id))  # 新增代码+ComposerRealModelRouting：按 provider_id 查询连接状态；如果没有这一行，非 OpenAI 选择无法被正确拒绝。
        return bool(self.connected_provider_reader())  # 新增代码+ComposerRealModelRouting：兼容旧无参读取器；如果没有这一行，已有测试和注入实现会被打碎。
    # 新增代码+ComposerRealModelRouting：函数段结束，RealModelGuiAgentAdapter._provider_is_connected 到此结束；如果没有边界说明，用户不容易看出连接门禁兼容范围。

    def _model_for_request(self, request: GuiAgentRunRequest) -> Any:  # 新增代码+ComposerRealModelRouting：函数段开始，按本轮 GUI 请求创建真实模型；如果没有这段，模型工厂无法消费底部菜单选择。
        if _callable_accepts_positional_argument(self.model_factory):  # 新增代码+ComposerRealModelRouting：识别支持 request 参数的新模型工厂；如果没有这一行，GUI model_id 永远传不到工厂。
            return self.model_factory(request)  # 新增代码+ComposerRealModelRouting：把完整请求交给模型工厂；如果没有这一行，provider/model/reasoning/permission 都会丢失。
        return self.model_factory()  # 新增代码+ComposerRealModelRouting：兼容旧无参工厂；如果没有这一行，现有测试和简单注入会失败。
    # 新增代码+ComposerRealModelRouting：函数段结束，RealModelGuiAgentAdapter._model_for_request 到此结束；如果没有边界说明，用户不容易看出模型工厂兼容范围。

    def _model_event_payload(self, request: GuiAgentRunRequest, phase: str, message: str, elapsed_ms: int, metadata: dict[str, object] | None = None) -> dict[str, object]:  # 新增代码+真实模型延迟可观测性：函数段开始，统一生成模型调用状态载荷；如果没有这段，model_call 事件会在各处分散拼字典。
        payload: dict[str, object] = {"phase": phase, "message": message, "elapsed_ms": int(elapsed_ms), "provider_id": str(request.provider_id or "openai"), "model_id": str(request.model_id or "gpt-5.5")}  # 新增代码+真实模型延迟可观测性：写入阶段、说明、耗时、provider、model；如果没有这行，前端无法确认慢在哪个阶段和哪个模型。
        if metadata:  # 新增代码+真实模型延迟可观测性：只有存在额外诊断信息时才写 metadata；如果没有这行，空 metadata 会让事件载荷更噪。
            payload["metadata"] = dict(metadata)  # 新增代码+真实模型延迟可观测性：复制诊断字段避免外部后续修改；如果没有这行，事件日志可能被调用方对象污染。
        return payload  # 新增代码+真实模型延迟可观测性：返回标准载荷；如果没有这行，调用方拿不到可发给 GUI 的 payload。
    # 新增代码+真实模型延迟可观测性：函数段结束，RealModelGuiAgentAdapter._model_event_payload 到此结束；如果没有这个边界说明，用户不容易看出模型状态载荷范围。

    def _record_model_failure(self, request: GuiAgentRunRequest, error_kind: str, message: str) -> None:  # 新增代码+ModelFailureState：函数段开始，把模型级失败交给外部持久化回调；如果没有这段，OAuth 拒绝模型后下拉菜单不会标记失败。
        if not error_kind or self.model_failure_recorder is None:  # 新增代码+ModelFailureState：没有错误种类或没有注入记录器时跳过；如果没有这行，普通失败或单测替身会被强制写配置。
            return  # 新增代码+ModelFailureState：无需记录时直接返回；如果没有这行，后续会访问空回调。
        provider_id = str(request.provider_id or "openai").strip() or "openai"  # 新增代码+ModelFailureState：清理 provider id；如果没有这行，失败记录可能写到空 provider。
        model_id = str(request.model_id or "gpt-5.5").strip() or "gpt-5.5"  # 新增代码+ModelFailureState：清理 model id；如果没有这行，失败记录可能写到空模型。
        try:  # 新增代码+ModelFailureState：保护失败记录写入；如果没有这行，记录器异常会遮蔽真正的模型错误。
            self.model_failure_recorder(provider_id, model_id, error_kind, message)  # 新增代码+ModelFailureState：调用持久化记录器；如果没有这行，provider catalog 不会知道最近失败。
        except Exception:  # 新增代码+ModelFailureState：吞掉失败记录异常；如果没有这行，磁盘写入问题会让用户看不到原始模型错误。
            return  # 新增代码+ModelFailureState：记录失败时仍让主错误流程继续；如果没有这行，函数会隐式继续但语义不清楚。
    # 新增代码+ModelFailureState：函数段结束，RealModelGuiAgentAdapter._record_model_failure 到此结束；如果没有边界说明，用户不容易看出它只负责通知外部。

    def _payload_from_stream_event(self, request: GuiAgentRunRequest, stream_event: ModelStreamEvent) -> dict[str, object]:  # 新增代码+真实模型延迟可观测性：函数段开始，把模型协议事件转成 GUI 事件载荷；如果没有这段，adapter 会重复解析 stream_event 字段。
        metadata = dict(stream_event.metadata or {})  # 新增代码+真实模型延迟可观测性：复制模型事件 metadata；如果没有这行，transport 诊断信息会丢失或被外部污染。
        metadata["model_sequence"] = stream_event.sequence  # 新增代码+真实模型延迟可观测性：记录模型内部顺序号；如果没有这行，排查乱序或丢包时缺少依据。
        metadata["model_timestamp"] = stream_event.timestamp  # 新增代码+真实模型延迟可观测性：记录模型事件时间戳；如果没有这行，前后端时间线无法对齐。
        return self._model_event_payload(request, stream_event.phase, stream_event.message, stream_event.elapsed_ms, metadata)  # 新增代码+真实模型延迟可观测性：返回统一 GUI payload；如果没有这行，stream_event 无法进入可见状态面板。
    # 新增代码+真实模型延迟可观测性：函数段结束，RealModelGuiAgentAdapter._payload_from_stream_event 到此结束；如果没有这个边界说明，用户不容易看出协议转换范围。

    def _run_streaming_model(self, request: GuiAgentRunRequest, model: Any, events: list[dict[str, object]], emit_event: GuiEventEmitter, is_cancelled: GuiCancelChecker, sequence: int) -> GuiAgentRunResult:  # 新增代码+真实模型延迟可观测性：函数段开始，消费支持 stream_chat 的真实模型；如果没有这段，GUI 无法实时看到连接、fallback、首 token 等阶段。
        final_text_parts: list[str] = []  # 新增代码+真实模型延迟可观测性：累积模型文本增量；如果没有这行，message_completed 无法写回完整回答。
        first_delta_seen = False  # 新增代码+真实模型延迟可观测性：记录首个 delta 是否已经出现；如果没有这行，首 token 指标可能重复发送。
        stream_chat = model.stream_chat  # 新增代码+CodexCliCancelBridge：保存流式聊天方法；如果没有这一行，后续无法检查它是否支持取消回调。
        stream_kwargs: dict[str, object] = {"turn_id": request.turn_id, "provider_id": str(request.provider_id or "openai"), "model_id": str(request.model_id or "gpt-5.5")}  # 新增代码+CodexCliCancelBridge：集中准备模型上下文关键字；如果没有这一行，取消参数加入时容易打散原有 turn/provider/model。
        if _callable_accepts_keyword_argument(stream_chat, "is_cancelled"):  # 新增代码+CodexCliCancelBridge：只有模型声明支持取消回调时才传入；如果没有这一行，旧测试模型和旧 provider 会因为未知参数失败。
            stream_kwargs["is_cancelled"] = is_cancelled  # 新增代码+CodexCliCancelBridge：把 GUI 取消检查函数交给模型层；如果没有这一行，Codex CLI 进程控制器收不到停止按钮信号。
        stream = stream_chat([{"role": "user", "content": request.prompt}], [], **stream_kwargs)  # 修改代码+CodexCliCancelBridge：启动后端流式聊天并携带可选取消回调；如果没有这行，真实模型事件不会进入 adapter。
        for stream_event in stream:  # 新增代码+真实模型延迟可观测性：逐个消费模型事件；如果没有这行，GUI 只能等待最终结果。
            if stream_event.turn_id != request.turn_id:  # 新增代码+真实模型延迟可观测性：丢弃不属于当前 turn 的旧事件；如果没有这行，取消后的旧 delta 可能污染新消息。
                continue  # 新增代码+真实模型延迟可观测性：跳过 stale event；如果没有这行，过滤条件不会生效。
            if is_cancelled():  # 新增代码+真实模型延迟可观测性：每个模型事件前检查 GUI 取消信号；如果没有这行，用户点击停止后仍会继续刷模型输出。
                self._emit(events, emit_event, make_event("model_call_status", sequence, self._model_event_payload(request, "cancel_requested", "用户已请求取消真实模型调用。", stream_event.elapsed_ms), run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型延迟可观测性：先发出模型取消请求状态；如果没有这行，右侧状态面板不知道停止按钮已进入后端。
                sequence += 1  # 新增代码+真实模型延迟可观测性：递增事件序号；如果没有这行，取消事件可能和状态事件共用 sequence。
                return self._cancel(request, events, emit_event, sequence)  # 新增代码+真实模型延迟可观测性：返回取消终态；如果没有这行，取消后仍可能继续完成。
            if stream_event.event_type in {"status", "metrics"}:  # 新增代码+真实模型延迟可观测性：识别模型状态或指标事件；如果没有这行，连接和 fallback 阶段不会显示。
                self._emit(events, emit_event, make_event("model_call_status", sequence, self._payload_from_stream_event(request, stream_event), run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型延迟可观测性：把模型状态转发给 GUI；如果没有这行，用户仍只能看到泛化 running。
                sequence += 1  # 新增代码+真实模型延迟可观测性：递增事件序号；如果没有这行，后续文本事件会和状态事件重号。
                continue  # 新增代码+真实模型延迟可观测性：状态事件不产生正文；如果没有这行，状态文字可能被误当回答内容。
            if stream_event.event_type == "delta":  # 新增代码+真实模型延迟可观测性：识别模型文本增量事件；如果没有这行，真实回答不会流到聊天区。
                if not first_delta_seen:  # 新增代码+真实模型延迟可观测性：只在首个 delta 到达时记录一次首 token；如果没有这行，首 token 事件会重复。
                    self._emit(events, emit_event, make_event("model_first_delta", sequence, self._payload_from_stream_event(request, stream_event), run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型延迟可观测性：发送首 token 指标事件；如果没有这行，用户无法知道等待何时真正开始出字。
                    sequence += 1  # 新增代码+真实模型延迟可观测性：递增事件序号；如果没有这行，首 token 和正文 delta 会重号。
                    first_delta_seen = True  # 新增代码+真实模型延迟可观测性：标记首 token 已发送；如果没有这行，下一段文本会再次触发 model_first_delta。
                text_delta = str(stream_event.message)  # 新增代码+真实模型延迟可观测性：把模型增量转成可显示字符串；如果没有这行，非字符串消息可能破坏前端渲染。
                final_text_parts.append(text_delta)  # 新增代码+真实模型延迟可观测性：累积最终回答；如果没有这行，完成事件拿不到完整 final_text。
                self._emit(events, emit_event, make_event("message_delta", sequence, {"text_delta": text_delta}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型延迟可观测性：把文本增量发给聊天区；如果没有这行，用户看不到模型输出。
                sequence += 1  # 新增代码+真实模型延迟可观测性：递增事件序号；如果没有这行，多个 delta 会共用 sequence。
                continue  # 新增代码+真实模型延迟可观测性：文本事件处理完继续等待下一事件；如果没有这行，后续错误/完成判断会误处理 delta。
            if stream_event.event_type == "completed":  # 新增代码+真实模型延迟可观测性：识别模型完成事件；如果没有这行，turn 会停在 running。
                final_text = "".join(final_text_parts)  # 新增代码+真实模型延迟可观测性：拼接所有 delta 为最终文本；如果没有这行，message_completed 没有完整答案。
                self._emit(events, emit_event, make_event("message_completed", sequence, {"final_text": final_text}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型延迟可观测性：发送聊天完成事件；如果没有这行，前端不会把消息置为 completed。
                sequence += 1  # 新增代码+真实模型延迟可观测性：递增事件序号；如果没有这行，模型完成事件会和消息完成事件重号。
                self._emit(events, emit_event, make_event("model_call_completed", sequence, self._payload_from_stream_event(request, stream_event), run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型延迟可观测性：发送模型调用完成诊断事件；如果没有这行，右侧状态面板无法显示总耗时。
                return GuiAgentRunResult(status="completed", final_text=final_text, events=events)  # 新增代码+真实模型延迟可观测性：返回完成结果；如果没有这行，bridge 不知道最终文本。
            if stream_event.event_type == "error":  # 新增代码+真实模型延迟可观测性：识别模型错误事件；如果没有这行，后端错误可能被当作沉默超时。
                error_kind = _model_failure_kind_from_message(stream_event.message) or "real_model_failed"  # 新增代码+ModelFailureState：把模型错误归类成稳定错误码；如果没有这行，模型不支持无法被记录成 model_unsupported。
                readable_message = _readable_model_failure_message(request, error_kind, stream_event.message)  # 新增代码+ModelFailureState：生成用户可理解的失败文案；如果没有这行，GUI 会继续显示底层英文 JSON。
                self._record_model_failure(request, error_kind if error_kind == "model_unsupported" else "", readable_message)  # 新增代码+ModelFailureState：仅把模型不支持写入 provider 设置；如果没有这行，底部菜单不会标记最近失败模型。
                failed_payload = self._payload_from_stream_event(request, stream_event)  # 新增代码+ModelFailureState：先把模型错误事件转为 GUI 载荷；如果没有这行，后续无法补 error_kind。
                failed_payload["message"] = readable_message  # 新增代码+ModelFailureState：替换成用户可读失败文案；如果没有这行，状态面板仍显示底层错误。
                failed_metadata = dict(failed_payload.get("metadata", {})) if isinstance(failed_payload.get("metadata", {}), dict) else {}  # 新增代码+ModelFailureState：安全复制 metadata；如果没有这行，补充 error_kind 可能污染共享对象或遇到坏类型。
                failed_metadata["error_kind"] = error_kind  # 新增代码+ModelFailureState：把稳定错误种类写入 metadata；如果没有这行，前端和日志无法区分模型不支持与普通失败。
                failed_payload["metadata"] = failed_metadata  # 新增代码+ModelFailureState：把更新后的 metadata 放回载荷；如果没有这行，error_kind 不会出现在事件里。
                self._emit(events, emit_event, make_event("model_call_failed", sequence, failed_payload, run_id=request.run_id, turn_id=request.turn_id))  # 修改代码+ModelFailureState：发送带 error_kind 的模型失败诊断事件；如果没有这行，GUI 只会看到泛化 turn_failed。
                sequence += 1  # 新增代码+真实模型延迟可观测性：递增事件序号；如果没有这行，turn_failed 会和 model_call_failed 重号。
                return self._fail(request, events, emit_event, sequence, error_kind, readable_message)  # 修改代码+ModelFailureState：返回稳定失败结果并保留模型不支持错误码；如果没有这行，错误事件不会闭合 turn。
        return self._fail(request, events, emit_event, sequence, "real_model_stream_ended_without_completed", "Real model stream ended before a completed event.")  # 新增代码+真实模型延迟可观测性：流结束但未完成时快速失败；如果没有这行，GUI 可能永远停在 running。
    # 新增代码+真实模型延迟可观测性：函数段结束，RealModelGuiAgentAdapter._run_streaming_model 到此结束；如果没有这个边界说明，用户不容易看出流式模型消费范围。

    def _run_blocking_model(self, request: GuiAgentRunRequest, model: Any, events: list[dict[str, object]], emit_event: GuiEventEmitter, is_cancelled: GuiCancelChecker, sequence: int) -> GuiAgentRunResult:  # 新增代码+真实模型延迟可观测性：函数段开始，兼容仍只有 chat 的阻塞式模型；如果没有这段，旧模型适配器无法提供任何等待阶段。
        call_started_at = time.monotonic()  # 新增代码+真实模型延迟可观测性：记录阻塞调用开始时间；如果没有这行，调用耗时只能靠用户肉眼估计。
        self._emit(events, emit_event, make_event("model_call_status", sequence, self._model_event_payload(request, "connecting", "正在调用阻塞式真实模型接口，等待后端响应。", 0), run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型延迟可观测性：在阻塞调用前先发状态；如果没有这行，慢请求期间 GUI 仍然没有解释。
        sequence += 1  # 新增代码+真实模型延迟可观测性：递增事件序号；如果没有这行，模型返回后的事件会和连接状态重号。
        model_message = model.chat([{"role": "user", "content": request.prompt}], [])  # 新增代码+真实模型延迟可观测性：调用旧阻塞式模型接口；如果没有这行，真实模型不会参与回答。
        elapsed_ms = int((time.monotonic() - call_started_at) * 1000)  # 新增代码+真实模型延迟可观测性：计算阻塞调用耗时；如果没有这行，完成事件无法展示等待成本。
        if is_cancelled():  # 新增代码+真实模型延迟可观测性：模型返回后再次检查取消；如果没有这行，长调用结束后可能覆盖用户取消。
            self._emit(events, emit_event, make_event("model_call_status", sequence, self._model_event_payload(request, "cancel_requested", "用户已请求取消真实模型调用。", elapsed_ms), run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型延迟可观测性：记录取消请求已到达 adapter；如果没有这行，右侧状态看不到取消原因。
            sequence += 1  # 新增代码+真实模型延迟可观测性：递增事件序号；如果没有这行，turn_cancelled 会和取消状态重号。
            return self._cancel(request, events, emit_event, sequence)  # 新增代码+真实模型延迟可观测性：返回取消终态；如果没有这行，取消后仍可能写入完成文本。
        tool_calls = getattr(model_message, "tool_calls", [])  # 新增代码+真实模型延迟可观测性：读取模型请求的工具调用；如果没有这行，未接线工具会被误当作普通回答。
        if tool_calls:  # 新增代码+真实模型延迟可观测性：V1A 仍显式拒绝工具调用；如果没有这行，模型工具调用可能被静默丢弃。
            return self._fail(request, events, emit_event, sequence, "real_model_tools_not_connected", "Real model requested tool calls, but GUI tool execution is not connected yet.")  # 新增代码+真实模型延迟可观测性：返回工具未接线失败；如果没有这行，用户会误以为工具已经执行。
        final_text = str(getattr(model_message, "text", ""))  # 新增代码+真实模型延迟可观测性：读取模型最终文本；如果没有这行，后续 delta 没有文本来源。
        error_kind = _model_failure_kind_from_message(final_text)  # 新增代码+ModelFailureState：检查阻塞式返回是否其实是模型不支持错误；如果没有这行，错误文本会被误当成成功回答。
        if error_kind:  # 新增代码+ModelFailureState：处理模型不支持错误；如果没有这行，OAuth 拒绝模型仍会写成 assistant 正文。
            readable_message = _readable_model_failure_message(request, error_kind, final_text)  # 新增代码+ModelFailureState：生成可读失败文案；如果没有这行，用户仍会看到底层英文错误。
            self._record_model_failure(request, error_kind, readable_message)  # 新增代码+ModelFailureState：把不支持模型写入 provider catalog；如果没有这行，模型菜单不会标记最近失败。
            failed_payload = self._model_event_payload(request, "failed", readable_message, elapsed_ms, {"error_kind": error_kind})  # 新增代码+ModelFailureState：构造带 error_kind 的失败诊断载荷；如果没有这行，右侧状态面板无法解释失败类型。
            self._emit(events, emit_event, make_event("model_call_failed", sequence, failed_payload, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+ModelFailureState：发送模型失败诊断事件；如果没有这行，前端只能看到 turn_failed。
            sequence += 1  # 新增代码+ModelFailureState：递增事件序号；如果没有这行，turn_failed 会和 model_call_failed 重号。
            return self._fail(request, events, emit_event, sequence, error_kind, readable_message)  # 新增代码+ModelFailureState：以模型不支持错误码闭合 turn；如果没有这行，GUI 终态无法区分普通失败。
        first_delta_seen = False  # 新增代码+真实模型延迟可观测性：记录阻塞式切片首个 delta；如果没有这行，首 token 事件无法只发一次。
        for text_delta in self._text_chunks(final_text):  # 新增代码+真实模型延迟可观测性：把最终文本拆成 GUI 增量；如果没有这行，长回答会变成单个巨大事件。
            if is_cancelled():  # 新增代码+真实模型延迟可观测性：每个切片前检查取消；如果没有这行，用户取消后仍会继续刷文本。
                return self._cancel(request, events, emit_event, sequence)  # 新增代码+真实模型延迟可观测性：返回取消终态；如果没有这行，取消后的事件流可能继续。
            if not first_delta_seen:  # 新增代码+真实模型延迟可观测性：只在第一个切片前发首 delta 诊断；如果没有这行，首 token 指标会重复。
                self._emit(events, emit_event, make_event("model_first_delta", sequence, self._model_event_payload(request, "first_delta", "阻塞式模型已返回首段文本。", elapsed_ms), run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型延迟可观测性：记录首段文本到达；如果没有这行，用户不知道等待何时结束。
                sequence += 1  # 新增代码+真实模型延迟可观测性：递增事件序号；如果没有这行，首 delta 诊断和正文 delta 会重号。
                first_delta_seen = True  # 新增代码+真实模型延迟可观测性：标记首段文本已记录；如果没有这行，每个切片都会重复首 token 事件。
            self._emit(events, emit_event, make_event("message_delta", sequence, {"text_delta": text_delta}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型延迟可观测性：发送模型文本增量；如果没有这行，聊天区看不到真实回答内容。
            sequence += 1  # 新增代码+真实模型延迟可观测性：递增事件序号；如果没有这行，多个文本事件会共用 sequence。
        self._emit(events, emit_event, make_event("message_completed", sequence, {"final_text": final_text}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型延迟可观测性：发送消息完成事件；如果没有这行，前端不会进入 completed。
        sequence += 1  # 新增代码+真实模型延迟可观测性：递增事件序号；如果没有这行，模型完成诊断会和消息完成重号。
        self._emit(events, emit_event, make_event("model_call_completed", sequence, self._model_event_payload(request, "completed", "真实模型调用完成。", elapsed_ms), run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型延迟可观测性：发送模型调用完成诊断；如果没有这行，状态面板无法展示总耗时。
        return GuiAgentRunResult(status="completed", final_text=final_text, events=events)  # 新增代码+真实模型延迟可观测性：返回完成结果；如果没有这行，bridge 不知道最终文本。
    # 新增代码+真实模型延迟可观测性：函数段结束，RealModelGuiAgentAdapter._run_blocking_model 到此结束；如果没有这个边界说明，用户不容易看出阻塞模型兼容范围。

    def run(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, is_cancelled: GuiCancelChecker) -> GuiAgentRunResult:  # 新增代码+真实模型GUI适配器：函数段开始，执行一次真实模型 GUI 轮次；如果没有这段，桌面外壳无法真正通过模型生成回答。
        events: list[dict[str, object]] = []  # 新增代码+真实模型GUI适配器：保存本次真实模型事件；如果没有这一行，结果无法复盘。
        self._emit(events, emit_event, make_event("turn_started", 1, {"status": "running", "mode": "real"}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型GUI适配器：发出真实模式启动事件；如果没有这一行，前端看不到运行起点。
        if is_cancelled():  # 新增代码+真实模型GUI适配器：模型调用前检查取消；如果没有这一行，用户取消后仍可能调用模型。
            self._emit(events, emit_event, make_event("model_call_status", 2, self._model_event_payload(request, "cancel_requested", "用户已经请求取消真实模型调用。", 0), run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型取消：在早取消时先发出可见取消请求状态；如果没有这一行，用户点击停止后右侧状态面板只会看到最终取消，看不到取消已经进入后端。
            return self._cancel(request, events, emit_event, 3)  # 修改代码+真实模型取消：取消终态顺延到状态事件之后；如果没有这一行，turn_cancelled 会和 cancel_requested 共用顺序号导致前端排序不稳定。
        try:  # 新增代码+真实模型GUI适配器：捕获连接读取和模型调用异常；如果没有这一行，真实模型错误会让后台线程崩溃。
            if not self._provider_is_connected(request):  # 修改代码+ComposerRealModelRouting：按本轮 provider 检查 OpenAI/Codex 登录状态；如果没有这一行，未连接或不支持 provider 时也会把 prompt 发给模型层。
                return self._fail(request, events, emit_event, 2, "real_model_not_connected", "请先连接 OpenAI。")  # 修改代码+ModelFailureState：未连接时用中文快速失败且不创建模型；如果没有这一行，用户会看到假成功或等到后端慢失败。
            model = self._model_for_request(request)  # 修改代码+ComposerRealModelRouting：创建带 GUI 模型上下文的真实模型对象；如果没有这一行，adapter 没有后端可调用且下拉选择会被忽略。
            sequence = 2  # 修改代码+真实模型延迟可观测性：模型调用事件从 turn_started 后开始编号；如果没有这行，新增诊断事件会和旧消息事件重号。
            self._emit(events, emit_event, make_event("model_call_started", sequence, self._model_event_payload(request, "started", "真实模型调用已开始。", 0), run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型延迟可观测性：先发模型调用开始事件；如果没有这行，GUI 无法显示真实请求已经离开 composer。
            sequence += 1  # 新增代码+真实模型延迟可观测性：递增事件序号；如果没有这行，后续状态事件会和开始事件重号。
            if callable(getattr(model, "stream_chat", None)):  # 新增代码+真实模型延迟可观测性：优先使用支持阶段事件的流式模型接口；如果没有这行，新的 streaming 协议永远不会被消费。
                return self._run_streaming_model(request, model, events, emit_event, is_cancelled, sequence)  # 新增代码+真实模型延迟可观测性：进入流式模型路径；如果没有这行，连接、fallback、首 token 状态不会实时冒泡。
            return self._run_blocking_model(request, model, events, emit_event, is_cancelled, sequence)  # 修改代码+真实模型延迟可观测性：旧 chat 模型走阻塞兼容路径；如果没有这行，现有 Codex/OAuth 适配器会无法回答。
        except Exception as error:  # 新增代码+真实模型GUI适配器：把真实模型异常转换为稳定失败；如果没有这一行，线程异常会让 GUI 看不到原因。
            return self._fail(request, events, emit_event, len(events) + 1, "real_model_failed", str(error))  # 新增代码+真实模型GUI适配器：返回真实模型失败；如果没有这一行，异常无法进入事件流和状态面板。
    # 新增代码+真实模型GUI适配器：函数段结束，RealModelGuiAgentAdapter.run 到此结束；如果没有这个边界说明，用户不容易看出真实模型主流程。
# 新增代码+真实模型GUI适配器：类段结束，RealModelGuiAgentAdapter 到此结束；如果没有这个边界说明，用户不容易看出真实 adapter 范围。


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
