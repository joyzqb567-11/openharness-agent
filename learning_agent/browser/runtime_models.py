"""真实浏览器运行时的稳定数据协议模型。"""  # 新增代码+BrowserRuntimeProtocol: 说明本文件只定义可落盘、可恢复、可审计的数据对象；若没有这行代码，浏览器 runtime 边界不清楚。

from __future__ import annotations  # 新增代码+BrowserRuntimeProtocol: 延迟解析类型注解；若没有这行代码，类方法返回自身类型时更容易受定义顺序影响。

import copy  # 新增代码+BrowserRuntimeProtocol: 深拷贝字典和列表，避免调用方修改污染已保存对象；若没有这行代码，action/observation 的证据可能被外部误改。
import json  # 新增代码+BrowserRuntimeProtocol: 生成稳定 JSON 文本用于审计和测试；若没有这行代码，模型无法提供标准序列化 helper。
import secrets  # 新增代码+BrowserRuntimeProtocol: 生成短随机 id，避免多个浏览器动作撞名；若没有这行代码，调用方必须手写 action_id。
import time  # 新增代码+BrowserRuntimeProtocol: 记录毫秒时间戳；若没有这行代码，事件顺序和耗时无法审计。
from dataclasses import dataclass, field  # 新增代码+BrowserRuntimeProtocol: 用 dataclass 定义纯数据模型；若没有这行代码，协议对象需要大量手写构造器。
from typing import Any  # 新增代码+BrowserRuntimeProtocol: 浏览器事件和元素候选包含通用 JSON 字段；若没有这行代码，类型边界不清楚。

REDACTED_VALUE = "[已脱敏]"  # 新增代码+BrowserRuntimeProtocol: 定义统一脱敏占位符；若没有这行代码，不同日志会用不同文案难以审计。
SENSITIVE_KEY_MARKERS = ("password", "passwd", "secret", "token", "authorization", "cookie", "api_key", "apikey", "credential", "session")  # 新增代码+BrowserRuntimeProtocol: 定义敏感字段关键词；若没有这行代码，密码、token 和 cookie 可能进入事件日志。
SECRET_TOOL_TEXT_KEYS = ("text", "value", "input")  # 新增代码+BrowserRuntimeProtocol: 定义 secret 输入工具需要额外脱敏的常见文本键；若没有这行代码，browser_type_secret 的 text 仍会泄露。


def now_ms() -> int:  # 新增代码+BrowserRuntimeProtocol: 返回当前毫秒时间戳；若没有这行代码，多个模型会各自写时间格式。
    return int(time.time() * 1000)  # 新增代码+BrowserRuntimeProtocol: 用 Unix 毫秒方便排序和比较；若没有这行代码，状态时间线无法稳定排序。


def stable_json_dumps(payload: Any) -> str:  # 新增代码+BrowserRuntimeProtocol: 输出稳定 JSON 文本；若没有这行代码，测试和审计 diff 会受字段顺序影响。
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)  # 新增代码+BrowserRuntimeProtocol: 保留中文并按键排序；若没有这行代码，脱敏检查和落盘格式不稳定。


def _safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+BrowserRuntimeProtocol: 把未知输入安全转为字典副本；若没有这行代码，坏状态文件可能直接抛异常。
    if isinstance(value, dict):  # 新增代码+BrowserRuntimeProtocol: 只有真实字典才允许复制；若没有这行代码，字符串等异常值会污染协议对象。
        return copy.deepcopy(value)  # 新增代码+BrowserRuntimeProtocol: 返回深拷贝防止外部共享；若没有这行代码，调用方后续修改会改变模型内部状态。
    return {}  # 新增代码+BrowserRuntimeProtocol: 非字典输入回退空对象；若没有这行代码，恢复旧文件时可能崩溃。


def _safe_list(value: Any) -> list[Any]:  # 新增代码+BrowserRuntimeProtocol: 把未知输入安全转为列表副本；若没有这行代码，坏 JSON 中的非列表会破坏恢复。
    if isinstance(value, list):  # 新增代码+BrowserRuntimeProtocol: 只有真实列表才允许复制；若没有这行代码，字符串会被误当字符列表。
        return copy.deepcopy(value)  # 新增代码+BrowserRuntimeProtocol: 返回深拷贝防止外部共享；若没有这行代码，元素候选可能被调用方误改。
    return []  # 新增代码+BrowserRuntimeProtocol: 非列表输入回退空列表；若没有这行代码，缺字段恢复不稳定。


def _text(value: Any, default: str = "") -> str:  # 新增代码+BrowserRuntimeProtocol: 把未知输入安全转为字符串；若没有这行代码，旧文件缺字段会出现 None 文本。
    return default if value is None else str(value)  # 新增代码+BrowserRuntimeProtocol: None 使用默认值，其余转字符串；若没有这行代码，状态页可能显示 Python None。


def _number(value: Any, default: int = 0) -> int:  # 新增代码+BrowserRuntimeProtocol: 把未知输入安全转为整数；若没有这行代码，坏时间戳会破坏排序。
    try:  # 新增代码+BrowserRuntimeProtocol: 捕获外部输入不能转数字的情况；若没有这行代码，恢复旧状态会因单个坏字段失败。
        return int(value)  # 新增代码+BrowserRuntimeProtocol: 尽量把字符串数字恢复为整数；若没有这行代码，JSON 往返后的数字类型不稳定。
    except (TypeError, ValueError):  # 新增代码+BrowserRuntimeProtocol: 处理 None、对象或非数字字符串；若没有这行代码，异常会冒泡。
        return default  # 新增代码+BrowserRuntimeProtocol: 返回安全默认值；若没有这行代码，坏字段无法容错。


def _float_number(value: Any, default: float = 0.0) -> float:  # 新增代码+BrowserRuntimeProtocol: 把未知输入安全转为浮点数；若没有这行代码，locator 置信度恢复不稳定。
    try:  # 新增代码+BrowserRuntimeProtocol: 捕获外部输入不能转浮点的情况；若没有这行代码，坏置信度会中断恢复。
        return float(value)  # 新增代码+BrowserRuntimeProtocol: 尽量把字符串数字恢复为浮点；若没有这行代码，JSON 往返后的置信度类型不稳定。
    except (TypeError, ValueError):  # 新增代码+BrowserRuntimeProtocol: 处理 None、对象或非数字字符串；若没有这行代码，异常会冒泡。
        return default  # 新增代码+BrowserRuntimeProtocol: 返回安全默认值；若没有这行代码，坏字段无法容错。


def _is_sensitive_key(key: str) -> bool:  # 新增代码+BrowserRuntimeProtocol: 判断字段名是否像敏感信息；若没有这行代码，脱敏规则会散落在各处。
    lowered = key.lower()  # 新增代码+BrowserRuntimeProtocol: 统一小写比较；若没有这行代码，Password 或 TOKEN 可能绕过脱敏。
    return any(marker in lowered for marker in SENSITIVE_KEY_MARKERS)  # 新增代码+BrowserRuntimeProtocol: 命中任一敏感关键词即脱敏；若没有这行代码，安全字段判断不会执行。


def redact_browser_arguments(arguments: dict[str, Any] | None) -> dict[str, Any]:  # 新增代码+BrowserRuntimeProtocol: 递归脱敏浏览器工具参数；若没有这行代码，action log 可能保存账号密码。
    def redact_value(key: str, value: Any) -> Any:  # 新增代码+BrowserRuntimeProtocol: 定义递归处理单个键值的内部函数；若没有这行代码，嵌套对象脱敏会重复写逻辑。
        if _is_sensitive_key(key):  # 新增代码+BrowserRuntimeProtocol: 字段名敏感时直接隐藏值；若没有这行代码，token/password/cookie 会泄露。
            return REDACTED_VALUE  # 新增代码+BrowserRuntimeProtocol: 返回统一占位符；若没有这行代码，敏感值仍会落盘。
        if isinstance(value, dict):  # 新增代码+BrowserRuntimeProtocol: 嵌套字典需要继续递归；若没有这行代码，nested.token 会泄露。
            return {str(child_key): redact_value(str(child_key), child_value) for child_key, child_value in value.items()}  # 新增代码+BrowserRuntimeProtocol: 递归处理子字段；若没有这行代码，深层敏感参数不会被隐藏。
        if isinstance(value, list):  # 新增代码+BrowserRuntimeProtocol: 列表里的对象也可能包含敏感字段；若没有这行代码，数组形式表单值可能泄露。
            return [redact_value(key, item) for item in value]  # 新增代码+BrowserRuntimeProtocol: 保留列表结构并处理每个元素；若没有这行代码，列表参数无法安全记录。
        return copy.deepcopy(value)  # 新增代码+BrowserRuntimeProtocol: 普通值保留副本；若没有这行代码，必要的非敏感审计信息会丢失。
    return {str(key): redact_value(str(key), value) for key, value in (arguments or {}).items()}  # 新增代码+BrowserRuntimeProtocol: 返回脱敏后的新字典；若没有这行代码，调用方会拿不到结果。


def redact_secret_tool_arguments(tool_name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:  # 新增代码+BrowserRuntimeProtocol: 对 secret 输入工具做额外脱敏；若没有这行代码，browser_type_secret 的 text 会被当普通字段保存。
    redacted = redact_browser_arguments(arguments)  # 新增代码+BrowserRuntimeProtocol: 先执行通用递归脱敏；若没有这行代码，secret_env_var 和 token 不会被处理。
    if "secret" in tool_name.lower():  # 新增代码+BrowserRuntimeProtocol: 只有工具名声明 secret 时才额外隐藏文本输入；若没有这行代码，普通输入动作会丢失必要审计文本。
        for key in SECRET_TOOL_TEXT_KEYS:  # 新增代码+BrowserRuntimeProtocol: 遍历常见文本参数键；若没有这行代码，value/input 等别名可能漏掉。
            if key in redacted:  # 新增代码+BrowserRuntimeProtocol: 只处理实际存在的键；若没有这行代码，会无意义增加占位字段。
                redacted[key] = REDACTED_VALUE  # 新增代码+BrowserRuntimeProtocol: 隐藏 secret 工具的明文输入；若没有这行代码，真实密码可能进入日志。
    return redacted  # 新增代码+BrowserRuntimeProtocol: 返回工具级脱敏结果；若没有这行代码，BrowserAction 无法保存安全参数。


def _new_id(prefix: str) -> str:  # 新增代码+BrowserRuntimeProtocol: 生成带前缀的短 id；若没有这行代码，action/session/recovery id 规则会重复。
    return f"{prefix}_{secrets.token_hex(8)}"  # 新增代码+BrowserRuntimeProtocol: 用 16 位十六进制随机后缀降低碰撞；若没有这行代码，多动作可能共享 id。


@dataclass  # 新增代码+BrowserRuntimeProtocol: 自动生成 BrowserLocator 构造器；若没有这行代码，locator 对象要手写大量初始化逻辑。
class BrowserLocator:  # 新增代码+BrowserRuntimeProtocol: 表示一次定位结果或候选元素；若没有这个类，视觉/DOM 定位只能传松散字典。
    locator_type: str  # 新增代码+BrowserRuntimeProtocol: 保存定位来源类型；若没有这行代码，回放时不知道是 selector、text 还是 visual。
    value: str  # 新增代码+BrowserRuntimeProtocol: 保存定位原始值；若没有这行代码，审计无法解释为什么点这个元素。
    confidence: float = 0.0  # 新增代码+BrowserRuntimeProtocol: 保存定位置信度；若没有这行代码，低置信度点击无法被拦截或解释。
    reason: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存选择理由；若没有这行代码，失败后用户看不懂定位依据。
    selector: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存最终可执行 selector；若没有这行代码，DOM 回放无法复用定位结果。
    element_id: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存 observation 中的元素 id；若没有这行代码，定位和页面快照无法关联。
    box: dict[str, Any] = field(default_factory=dict)  # 新增代码+BrowserRuntimeProtocol: 保存元素几何框；若没有这行代码，视觉点击和截图验收缺坐标。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+BrowserRuntimeProtocol: 把定位结果转成 JSON 字典；若没有这行代码，locator 无法落盘。
        return {"locator_type": self.locator_type, "value": self.value, "confidence": self.confidence, "reason": self.reason, "selector": self.selector, "element_id": self.element_id, "box": _safe_dict(self.box)}  # 新增代码+BrowserRuntimeProtocol: 返回完整定位字段；若没有这行代码，恢复会缺少定位证据。

    @classmethod  # 新增代码+BrowserRuntimeProtocol: 提供从 JSON 字典恢复 locator 的入口；若没有这行代码，store 只能返回原始 dict。
    def from_dict(cls, payload: dict[str, Any] | None) -> "BrowserLocator":  # 新增代码+BrowserRuntimeProtocol: 从持久化 payload 恢复定位对象；若没有这行代码，旧状态读取会分散。
        safe = _safe_dict(payload)  # 新增代码+BrowserRuntimeProtocol: 对外部 payload 做字典兜底；若没有这行代码，坏数据会导致恢复崩溃。
        return cls(locator_type=_text(safe.get("locator_type")), value=_text(safe.get("value")), confidence=_float_number(safe.get("confidence")), reason=_text(safe.get("reason")), selector=_text(safe.get("selector")), element_id=_text(safe.get("element_id")), box=_safe_dict(safe.get("box")))  # 新增代码+BrowserRuntimeProtocol: 返回完整 locator 对象；若没有这行代码，定位证据无法恢复。


@dataclass  # 新增代码+BrowserRuntimeProtocol: 自动生成 BrowserObservation 构造器；若没有这行代码，页面证据对象要手写初始化。
class BrowserObservation:  # 新增代码+BrowserRuntimeProtocol: 表示 agent 看到的一次页面状态；若没有这个类，页面证据无法统一落盘和复验。
    observation_id: str  # 新增代码+BrowserRuntimeProtocol: 保存 observation 唯一编号；若没有这行代码，action 无法关联页面证据。
    run_id: str  # 新增代码+BrowserRuntimeProtocol: 保存所属浏览器 run；若没有这行代码，多任务证据会混在一起。
    stage_id: str  # 新增代码+BrowserRuntimeProtocol: 保存所属阶段；若没有这行代码，阶段验收无法找到对应页面。
    action_id: str  # 新增代码+BrowserRuntimeProtocol: 保存触发观察的动作；若没有这行代码，失败复盘不知道哪一步产生该页面。
    url: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存当前 URL；若没有这行代码，验收无法证明打开了正确页面。
    title: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存页面标题；若没有这行代码，页面状态缺少可读摘要。
    visible_text: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存可见文本摘要；若没有这行代码，模型下一轮上下文缺少页面内容。
    screenshot_path: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存截图产物路径；若没有这行代码，肉眼验收证据无法关联。
    artifact_paths: list[str] = field(default_factory=list)  # 新增代码+BrowserObservationStage4: 保存长文本等补充证据路径；若没有这行代码，超长页面内容只能被截断后丢失。
    console_summary: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存 console 摘要；若没有这行代码，页面脚本错误不容易被发现。
    network_summary: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存 network 摘要；若没有这行代码，请求失败难以复盘。
    elements: list[dict[str, Any]] = field(default_factory=list)  # 新增代码+BrowserRuntimeProtocol: 保存结构化元素候选；若没有这行代码，定位引擎只能重新猜。
    created_at_ms: int = field(default_factory=now_ms)  # 新增代码+BrowserRuntimeProtocol: 保存创建时间；若没有这行代码，多次观察无法按时间排序。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+BrowserRuntimeProtocol: 把 observation 转成 JSON 字典；若没有这行代码，页面证据无法落盘。
        return {"observation_id": self.observation_id, "run_id": self.run_id, "stage_id": self.stage_id, "action_id": self.action_id, "url": self.url, "title": self.title, "visible_text": self.visible_text, "screenshot_path": self.screenshot_path, "artifact_paths": list(self.artifact_paths), "console_summary": self.console_summary, "network_summary": self.network_summary, "elements": _safe_list(self.elements), "created_at_ms": self.created_at_ms}  # 修改代码+BrowserObservationStage4: 返回页面证据时包含补充产物路径；若没有这行代码，长文本产物无法被状态页和 verifier 找到。

    @classmethod  # 新增代码+BrowserRuntimeProtocol: 提供从 JSON 字典恢复 observation 的入口；若没有这行代码，store 需要重复解析字段。
    def from_dict(cls, payload: dict[str, Any] | None) -> "BrowserObservation":  # 新增代码+BrowserRuntimeProtocol: 从持久化 payload 恢复页面证据；若没有这行代码，进程中断后无法复验页面状态。
        safe = _safe_dict(payload)  # 新增代码+BrowserRuntimeProtocol: 对外部 payload 做字典兜底；若没有这行代码，坏状态文件会直接崩溃。
        return cls(observation_id=_text(safe.get("observation_id")), run_id=_text(safe.get("run_id")), stage_id=_text(safe.get("stage_id")), action_id=_text(safe.get("action_id")), url=_text(safe.get("url")), title=_text(safe.get("title")), visible_text=_text(safe.get("visible_text")), screenshot_path=_text(safe.get("screenshot_path")), artifact_paths=[_text(item) for item in _safe_list(safe.get("artifact_paths"))], console_summary=_text(safe.get("console_summary")), network_summary=_text(safe.get("network_summary")), elements=_safe_list(safe.get("elements")), created_at_ms=_number(safe.get("created_at_ms"), now_ms()))  # 修改代码+BrowserObservationStage4: 恢复 observation 时读取补充产物路径；若没有这行代码，进程重启后长文本证据会断链。


@dataclass  # 新增代码+BrowserRuntimeProtocol: 自动生成 BrowserAction 构造器；若没有这行代码，动作对象要手写大量初始化。
class BrowserAction:  # 新增代码+BrowserRuntimeProtocol: 表示一次浏览器工具动作；若没有这个类，工具执行只能写散落日志。
    action_id: str  # 新增代码+BrowserRuntimeProtocol: 保存动作唯一编号；若没有这行代码，事件、结果和 observation 无法关联。
    run_id: str  # 新增代码+BrowserRuntimeProtocol: 保存所属浏览器 run；若没有这行代码，多任务动作会混淆。
    stage_id: str  # 新增代码+BrowserRuntimeProtocol: 保存所属阶段；若没有这行代码，中断恢复不知道动作属于哪一步。
    tool_name: str  # 新增代码+BrowserRuntimeProtocol: 保存调用的浏览器工具名；若没有这行代码，回放无法知道执行了什么。
    arguments_redacted: dict[str, Any] = field(default_factory=dict)  # 新增代码+BrowserRuntimeProtocol: 保存脱敏后的工具参数；若没有这行代码，审计缺参数或泄露明文。
    status: str = "pending"  # 新增代码+BrowserRuntimeProtocol: 保存 pending/running/completed/failed/interrupted；若没有这行代码，状态机不可见。
    started_at_ms: int = 0  # 新增代码+BrowserRuntimeProtocol: 保存动作开始时间；若没有这行代码，工具耗时无法计算。
    finished_at_ms: int = 0  # 新增代码+BrowserRuntimeProtocol: 保存动作结束时间；若没有这行代码，卡住动作无法识别。
    error_type: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存失败分类；若没有这行代码，恢复策略无法按错误类型选择。
    error_message: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存失败说明；若没有这行代码，用户无法知道哪一步失败。
    observation_id: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存动作后的观察结果 id；若没有这行代码，工具结果和页面证据断链。

    @classmethod  # 新增代码+BrowserRuntimeProtocol: 提供带脱敏规则的动作工厂；若没有这行代码，调用方可能忘记脱敏。
    def create(cls, run_id: str, stage_id: str, tool_name: str, arguments: dict[str, Any] | None, action_id: str | None = None) -> "BrowserAction":  # 新增代码+BrowserRuntimeProtocol: 创建安全动作对象；若没有这行代码，action_id 和脱敏规则会散落在工具层。
        safe_action_id = action_id or _new_id("browser_action")  # 新增代码+BrowserRuntimeProtocol: 没传 id 时自动生成；若没有这行代码，调用方必须手写唯一 id。
        redacted_arguments = redact_secret_tool_arguments(tool_name, arguments)  # 新增代码+BrowserRuntimeProtocol: 保存前完成通用和 secret 工具脱敏；若没有这行代码，敏感参数可能落盘。
        return cls(action_id=safe_action_id, run_id=run_id, stage_id=stage_id, tool_name=tool_name, arguments_redacted=redacted_arguments)  # 新增代码+BrowserRuntimeProtocol: 返回动作对象；若没有这行代码，工厂无结果。

    def mark_started(self) -> None:  # 新增代码+BrowserRuntimeProtocol: 标记动作开始运行；若没有这行代码，执行器无法写 started 事件前后的状态。
        self.status = "running"  # 新增代码+BrowserRuntimeProtocol: 设置运行中状态；若没有这行代码，状态页无法显示工具正在执行。
        self.started_at_ms = now_ms()  # 新增代码+BrowserRuntimeProtocol: 记录开始时间；若没有这行代码，耗时和超时判断没有依据。

    def mark_completed(self, observation_id: str = "") -> None:  # 新增代码+BrowserRuntimeProtocol: 标记动作成功完成；若没有这行代码，执行器无法统一收尾。
        self.status = "completed"  # 新增代码+BrowserRuntimeProtocol: 设置完成状态；若没有这行代码，resume 可能重复执行已完成动作。
        self.finished_at_ms = now_ms()  # 新增代码+BrowserRuntimeProtocol: 记录结束时间；若没有这行代码，工具耗时无法审计。
        self.observation_id = observation_id  # 新增代码+BrowserRuntimeProtocol: 关联动作后的页面证据；若没有这行代码，验收找不到观察结果。

    def mark_failed(self, error_type: str, error_message: str) -> None:  # 新增代码+BrowserRuntimeProtocol: 标记动作失败；若没有这行代码，恢复管理器无法读取失败分类。
        self.status = "failed"  # 新增代码+BrowserRuntimeProtocol: 设置失败状态；若没有这行代码，状态页可能把失败动作当未开始。
        self.finished_at_ms = now_ms()  # 新增代码+BrowserRuntimeProtocol: 记录失败结束时间；若没有这行代码，失败耗时无法审计。
        self.error_type = error_type  # 新增代码+BrowserRuntimeProtocol: 保存失败类型；若没有这行代码，后续无法按类型恢复。
        self.error_message = error_message  # 新增代码+BrowserRuntimeProtocol: 保存失败详情；若没有这行代码，用户看不到具体错误。

    def mark_interrupted(self, error_message: str = "interrupted") -> None:  # 新增代码+BrowserRuntimeProtocol: 标记动作被用户或进程中断；若没有这行代码，恢复时无法区分失败和中断。
        self.status = "interrupted"  # 新增代码+BrowserRuntimeProtocol: 设置中断状态；若没有这行代码，queue resume 可能误判为普通失败。
        self.finished_at_ms = now_ms()  # 新增代码+BrowserRuntimeProtocol: 记录中断时间；若没有这行代码，中断证据不完整。
        self.error_type = "interrupted"  # 新增代码+BrowserRuntimeProtocol: 保存标准中断类型；若没有这行代码，恢复策略无法识别中断。
        self.error_message = error_message  # 新增代码+BrowserRuntimeProtocol: 保存中断说明；若没有这行代码，用户不知道为什么停下。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+BrowserRuntimeProtocol: 把动作转成 JSON 字典；若没有这行代码，action store 无法落盘。
        return {"action_id": self.action_id, "run_id": self.run_id, "stage_id": self.stage_id, "tool_name": self.tool_name, "arguments_redacted": _safe_dict(self.arguments_redacted), "status": self.status, "started_at_ms": self.started_at_ms, "finished_at_ms": self.finished_at_ms, "error_type": self.error_type, "error_message": self.error_message, "observation_id": self.observation_id}  # 新增代码+BrowserRuntimeProtocol: 返回完整动作字段；若没有这行代码，恢复和审计会缺数据。

    @classmethod  # 新增代码+BrowserRuntimeProtocol: 提供从 JSON 字典恢复动作的入口；若没有这行代码，store 只能返回松散 dict。
    def from_dict(cls, payload: dict[str, Any] | None) -> "BrowserAction":  # 新增代码+BrowserRuntimeProtocol: 从持久化 payload 恢复动作对象；若没有这行代码，中断恢复无法重建动作状态。
        safe = _safe_dict(payload)  # 新增代码+BrowserRuntimeProtocol: 对外部 payload 做字典兜底；若没有这行代码，坏文件会让恢复崩溃。
        return cls(action_id=_text(safe.get("action_id")), run_id=_text(safe.get("run_id")), stage_id=_text(safe.get("stage_id")), tool_name=_text(safe.get("tool_name")), arguments_redacted=_safe_dict(safe.get("arguments_redacted")), status=_text(safe.get("status"), "pending"), started_at_ms=_number(safe.get("started_at_ms")), finished_at_ms=_number(safe.get("finished_at_ms")), error_type=_text(safe.get("error_type")), error_message=_text(safe.get("error_message")), observation_id=_text(safe.get("observation_id")))  # 新增代码+BrowserRuntimeProtocol: 返回完整动作对象；若没有这行代码，动作状态无法恢复。


@dataclass  # 新增代码+BrowserRuntimeProtocol: 自动生成 BrowserTab 构造器；若没有这行代码，tab 状态对象要手写初始化。
class BrowserTab:  # 新增代码+BrowserRuntimeProtocol: 表示浏览器里的一个标签页；若没有这个类，tab registry 只能用脆弱字典。
    tab_id: str  # 新增代码+BrowserRuntimeProtocol: 保存 tab id；若没有这行代码，跨步骤无法指向同一个页面。
    url: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存 tab 当前 URL；若没有这行代码，状态页不知道每个 tab 在哪里。
    title: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存 tab 标题；若没有这行代码，用户只能看到 id。
    active: bool = False  # 新增代码+BrowserRuntimeProtocol: 标记是否当前活动页；若没有这行代码，动作目标页不清楚。
    last_seen_at_ms: int = field(default_factory=now_ms)  # 新增代码+BrowserRuntimeProtocol: 保存最近观察时间；若没有这行代码，过期 tab 难以识别。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+BrowserRuntimeProtocol: 把 tab 转成 JSON 字典；若没有这行代码，session store 无法落盘 tab。
        return {"tab_id": self.tab_id, "url": self.url, "title": self.title, "active": self.active, "last_seen_at_ms": self.last_seen_at_ms}  # 新增代码+BrowserRuntimeProtocol: 返回完整 tab 字段；若没有这行代码，session 恢复会缺信息。

    @classmethod  # 新增代码+BrowserRuntimeProtocol: 提供从 JSON 字典恢复 tab 的入口；若没有这行代码，session manager 需要重复解析字段。
    def from_dict(cls, payload: dict[str, Any] | None) -> "BrowserTab":  # 新增代码+BrowserRuntimeProtocol: 从持久化 payload 恢复 tab；若没有这行代码，tab 状态无法跨进程恢复。
        safe = _safe_dict(payload)  # 新增代码+BrowserRuntimeProtocol: 对外部 payload 做字典兜底；若没有这行代码，坏 tab 数据会中断恢复。
        return cls(tab_id=_text(safe.get("tab_id")), url=_text(safe.get("url")), title=_text(safe.get("title")), active=bool(safe.get("active", False)), last_seen_at_ms=_number(safe.get("last_seen_at_ms"), now_ms()))  # 新增代码+BrowserRuntimeProtocol: 返回完整 tab 对象；若没有这行代码，session 恢复无法知道 tab 状态。


@dataclass  # 新增代码+BrowserRuntimeProtocol: 自动生成 BrowserSession 构造器；若没有这行代码，session 状态对象要手写初始化。
class BrowserSession:  # 新增代码+BrowserRuntimeProtocol: 表示一个浏览器连接会话；若没有这个类，真实 Chrome/独立 Chromium 状态无法统一。
    session_id: str  # 新增代码+BrowserRuntimeProtocol: 保存 session 唯一编号；若没有这行代码，browser run 无法引用实际浏览器会话。
    mode: str = "independent_chromium"  # 新增代码+BrowserRuntimeProtocol: 保存 session 模式；若没有这行代码，状态页无法区分独立浏览器和真实 Chrome。
    connected: bool = False  # 新增代码+BrowserRuntimeProtocol: 保存连接状态；若没有这行代码，执行器不知道能否继续操作。
    visible: bool = False  # 新增代码+BrowserRuntimeProtocol: 保存是否肉眼可见；若没有这行代码，真实验收无法证明不是 headless。
    headless: bool = True  # 新增代码+BrowserRuntimeProtocol: 保存 headless 状态；若没有这行代码，窗口模式无法审计。
    current_tab_id: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存当前活动 tab；若没有这行代码，动作默认目标页不清楚。
    tabs: list[BrowserTab] = field(default_factory=list)  # 新增代码+BrowserRuntimeProtocol: 保存 tab 列表；若没有这行代码，多标签页面无法恢复。
    created_at_ms: int = field(default_factory=now_ms)  # 新增代码+BrowserRuntimeProtocol: 保存 session 创建时间；若没有这行代码，会话生命周期不完整。
    updated_at_ms: int = field(default_factory=now_ms)  # 新增代码+BrowserRuntimeProtocol: 保存 session 更新时间；若没有这行代码，状态页不知道信息新旧。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+BrowserRuntimeProtocol: 把 session 转成 JSON 字典；若没有这行代码，session 状态无法落盘。
        return {"session_id": self.session_id, "mode": self.mode, "connected": self.connected, "visible": self.visible, "headless": self.headless, "current_tab_id": self.current_tab_id, "tabs": [tab.to_dict() for tab in self.tabs], "created_at_ms": self.created_at_ms, "updated_at_ms": self.updated_at_ms}  # 新增代码+BrowserRuntimeProtocol: 返回完整 session 字段；若没有这行代码，恢复和状态输出会缺数据。

    @classmethod  # 新增代码+BrowserRuntimeProtocol: 提供从 JSON 字典恢复 session 的入口；若没有这行代码，session manager 需要重复解析。
    def from_dict(cls, payload: dict[str, Any] | None) -> "BrowserSession":  # 新增代码+BrowserRuntimeProtocol: 从持久化 payload 恢复 session；若没有这行代码，进程重启后不知道浏览器连接状态。
        safe = _safe_dict(payload)  # 新增代码+BrowserRuntimeProtocol: 对外部 payload 做字典兜底；若没有这行代码，坏 session 文件会直接崩溃。
        tabs = [BrowserTab.from_dict(item) for item in _safe_list(safe.get("tabs"))]  # 新增代码+BrowserRuntimeProtocol: 恢复 tab 对象列表；若没有这行代码，session 只剩松散 dict。
        return cls(session_id=_text(safe.get("session_id")), mode=_text(safe.get("mode"), "independent_chromium"), connected=bool(safe.get("connected", False)), visible=bool(safe.get("visible", False)), headless=bool(safe.get("headless", True)), current_tab_id=_text(safe.get("current_tab_id")), tabs=tabs, created_at_ms=_number(safe.get("created_at_ms"), now_ms()), updated_at_ms=_number(safe.get("updated_at_ms"), now_ms()))  # 新增代码+BrowserRuntimeProtocol: 返回完整 session 对象；若没有这行代码，会话状态无法恢复。


@dataclass  # 新增代码+BrowserRuntimeProtocol: 自动生成 BrowserRecoveryAttempt 构造器；若没有这行代码，恢复尝试对象要手写初始化。
class BrowserRecoveryAttempt:  # 新增代码+BrowserRuntimeProtocol: 表示一次失败恢复尝试；若没有这个类，恢复过程无法审计。
    recovery_id: str  # 新增代码+BrowserRuntimeProtocol: 保存恢复尝试 id；若没有这行代码，多次恢复无法区分。
    run_id: str  # 新增代码+BrowserRuntimeProtocol: 保存所属 run；若没有这行代码，恢复证据无法归档。
    action_id: str  # 新增代码+BrowserRuntimeProtocol: 保存失败动作 id；若没有这行代码，恢复不知道是修哪一步。
    error_type: str  # 新增代码+BrowserRuntimeProtocol: 保存失败分类；若没有这行代码，恢复策略无法复盘。
    strategy: str  # 新增代码+BrowserRuntimeProtocol: 保存采用的恢复策略；若没有这行代码，用户不知道系统尝试了什么。
    status: str = "pending"  # 新增代码+BrowserRuntimeProtocol: 保存恢复状态；若没有这行代码，恢复过程不可见。
    started_at_ms: int = 0  # 新增代码+BrowserRuntimeProtocol: 保存恢复开始时间；若没有这行代码，恢复耗时无法审计。
    finished_at_ms: int = 0  # 新增代码+BrowserRuntimeProtocol: 保存恢复结束时间；若没有这行代码，卡住恢复无法识别。
    message: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存恢复说明；若没有这行代码，失败后用户看不懂结果。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+BrowserRuntimeProtocol: 把恢复尝试转成 JSON 字典；若没有这行代码，恢复事件无法落盘。
        return {"recovery_id": self.recovery_id, "run_id": self.run_id, "action_id": self.action_id, "error_type": self.error_type, "strategy": self.strategy, "status": self.status, "started_at_ms": self.started_at_ms, "finished_at_ms": self.finished_at_ms, "message": self.message}  # 新增代码+BrowserRuntimeProtocol: 返回完整恢复字段；若没有这行代码，恢复审计会缺信息。

    @classmethod  # 新增代码+BrowserRuntimeProtocol: 提供从 JSON 字典恢复 recovery 的入口；若没有这行代码，store 需要重复解析字段。
    def from_dict(cls, payload: dict[str, Any] | None) -> "BrowserRecoveryAttempt":  # 新增代码+BrowserRuntimeProtocol: 从持久化 payload 恢复恢复尝试；若没有这行代码，恢复历史无法跨进程读取。
        safe = _safe_dict(payload)  # 新增代码+BrowserRuntimeProtocol: 对外部 payload 做字典兜底；若没有这行代码，坏恢复记录会中断状态页。
        return cls(recovery_id=_text(safe.get("recovery_id")), run_id=_text(safe.get("run_id")), action_id=_text(safe.get("action_id")), error_type=_text(safe.get("error_type")), strategy=_text(safe.get("strategy")), status=_text(safe.get("status"), "pending"), started_at_ms=_number(safe.get("started_at_ms")), finished_at_ms=_number(safe.get("finished_at_ms")), message=_text(safe.get("message")))  # 新增代码+BrowserRuntimeProtocol: 返回完整恢复对象；若没有这行代码，恢复历史无法恢复。


@dataclass  # 新增代码+BrowserRuntimeProtocol: 自动生成 BrowserAssertion 构造器；若没有这行代码，浏览器验收断言对象要手写初始化。
class BrowserAssertion:  # 新增代码+BrowserRuntimeProtocol: 表示一个浏览器验收断言；若没有这个类，verifier 只能读散落规则。
    assertion_type: str  # 新增代码+BrowserRuntimeProtocol: 保存断言类型；若没有这行代码，verifier 不知道检查 URL、标题还是截图。
    expected: str  # 新增代码+BrowserRuntimeProtocol: 保存期望值；若没有这行代码，断言没有目标。
    actual: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存实际值；若没有这行代码，失败后无法解释差异。
    passed: bool = False  # 新增代码+BrowserRuntimeProtocol: 保存是否通过；若没有这行代码，阶段门禁无法判断结果。
    message: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存可读说明；若没有这行代码，用户只能看到布尔值。
    artifact_path: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存相关证据路径；若没有这行代码，肉眼复验找不到截图或日志。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+BrowserRuntimeProtocol: 把断言转成 JSON 字典；若没有这行代码，验收结果无法落盘。
        return {"assertion_type": self.assertion_type, "expected": self.expected, "actual": self.actual, "passed": self.passed, "message": self.message, "artifact_path": self.artifact_path}  # 新增代码+BrowserRuntimeProtocol: 返回完整断言字段；若没有这行代码，验收报告会缺内容。

    @classmethod  # 新增代码+BrowserRuntimeProtocol: 提供从 JSON 字典恢复断言的入口；若没有这行代码，verifier 历史结果无法读取。
    def from_dict(cls, payload: dict[str, Any] | None) -> "BrowserAssertion":  # 新增代码+BrowserRuntimeProtocol: 从持久化 payload 恢复断言对象；若没有这行代码，验收结果无法跨进程恢复。
        safe = _safe_dict(payload)  # 新增代码+BrowserRuntimeProtocol: 对外部 payload 做字典兜底；若没有这行代码，坏断言记录会中断恢复。
        return cls(assertion_type=_text(safe.get("assertion_type")), expected=_text(safe.get("expected")), actual=_text(safe.get("actual")), passed=bool(safe.get("passed", False)), message=_text(safe.get("message")), artifact_path=_text(safe.get("artifact_path")))  # 新增代码+BrowserRuntimeProtocol: 返回完整断言对象；若没有这行代码，验收记录无法恢复。


@dataclass  # 新增代码+BrowserRuntimeProtocol: 自动生成 BrowserCapabilityReport 构造器；若没有这行代码，能力报告对象要手写初始化。
class BrowserCapabilityReport:  # 新增代码+BrowserRuntimeProtocol: 表示当前浏览器 runtime 能力探测结果；若没有这个类，状态生态无法统一展示能力。
    compatible: bool  # 新增代码+BrowserRuntimeProtocol: 保存是否可用；若没有这行代码，状态页无法快速判断浏览器能力是否就绪。
    capabilities: list[str] = field(default_factory=list)  # 新增代码+BrowserRuntimeProtocol: 保存能力列表；若没有这行代码，agent 不知道能否截图、读 network 或控制真实 Chrome。
    session_mode: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存 session 模式；若没有这行代码，用户看不懂当前是哪个浏览器后端。
    warnings: list[str] = field(default_factory=list)  # 新增代码+BrowserRuntimeProtocol: 保存兼容性警告；若没有这行代码，插件缺失或权限不足不会可见。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+BrowserRuntimeProtocol: 把能力报告转成 JSON 字典；若没有这行代码，status API 无法输出稳定字段。
        return {"compatible": self.compatible, "capabilities": list(self.capabilities), "session_mode": self.session_mode, "warnings": list(self.warnings)}  # 新增代码+BrowserRuntimeProtocol: 返回完整能力字段；若没有这行代码，状态生态缺少机器可读报告。

    @classmethod  # 新增代码+BrowserRuntimeProtocol: 提供从 JSON 字典恢复能力报告的入口；若没有这行代码，状态缓存无法恢复。
    def from_dict(cls, payload: dict[str, Any] | None) -> "BrowserCapabilityReport":  # 新增代码+BrowserRuntimeProtocol: 从持久化 payload 恢复能力报告；若没有这行代码，兼容性结果无法复用。
        safe = _safe_dict(payload)  # 新增代码+BrowserRuntimeProtocol: 对外部 payload 做字典兜底；若没有这行代码，坏状态文件会中断状态页。
        return cls(compatible=bool(safe.get("compatible", False)), capabilities=[_text(item) for item in _safe_list(safe.get("capabilities"))], session_mode=_text(safe.get("session_mode")), warnings=[_text(item) for item in _safe_list(safe.get("warnings"))])  # 新增代码+BrowserRuntimeProtocol: 返回完整能力报告；若没有这行代码，状态生态无法恢复能力信息。


@dataclass  # 新增代码+BrowserRuntimeProtocol: 自动生成 BrowserRun 构造器；若没有这行代码，浏览器 run 根对象要手写初始化。
class BrowserRun:  # 新增代码+BrowserRuntimeProtocol: 表示一次可恢复的真实浏览器任务；若没有这个类，浏览器长任务没有统一状态根。
    run_id: str  # 新增代码+BrowserRuntimeProtocol: 保存浏览器 run 唯一编号；若没有这行代码，事件、动作和观察无法归档到同一任务。
    session_id: str  # 新增代码+BrowserRuntimeProtocol: 保存关联浏览器 session；若没有这行代码，run 不知道由哪个浏览器连接执行。
    prompt: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存用户任务提示；若没有这行代码，恢复后不知道任务目标。
    status: str = "pending"  # 新增代码+BrowserRuntimeProtocol: 保存 pending/running/completed/failed/interrupted；若没有这行代码，状态页无法显示 run 进度。
    current_stage_id: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存当前阶段 id；若没有这行代码，中断恢复不知道停在哪一步。
    completed_stage_ids: list[str] = field(default_factory=list)  # 新增代码+BrowserRuntimeProtocol: 保存已完成阶段；若没有这行代码，resume 会重复跑已完成阶段。
    action_ids: list[str] = field(default_factory=list)  # 新增代码+BrowserRuntimeProtocol: 保存动作 id 列表；若没有这行代码，run 和 action 文件会断链。
    observation_ids: list[str] = field(default_factory=list)  # 新增代码+BrowserRuntimeProtocol: 保存观察 id 列表；若没有这行代码，run 和页面证据会断链。
    summary: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存任务摘要；若没有这行代码，状态 CLI 无法快速说明结果。
    error_type: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存 run 级失败类型；若没有这行代码，恢复策略不知道大类。
    error_message: str = ""  # 新增代码+BrowserRuntimeProtocol: 保存 run 级失败说明；若没有这行代码，用户看不到停下原因。
    metadata: dict[str, Any] = field(default_factory=dict)  # 新增代码+BrowserRuntimeProtocol: 保存扩展元数据；若没有这行代码，harness/session/run 的关联字段会无处存放。
    created_at_ms: int = field(default_factory=now_ms)  # 新增代码+BrowserRuntimeProtocol: 保存创建时间；若没有这行代码，run 时间线不完整。
    updated_at_ms: int = field(default_factory=now_ms)  # 新增代码+BrowserRuntimeProtocol: 保存更新时间；若没有这行代码，状态页无法判断信息新旧。

    def _touch(self) -> None:  # 新增代码+BrowserRuntimeProtocol: 刷新 run 更新时间；若没有这行代码，每个状态方法都要重复写 now_ms。
        self.updated_at_ms = now_ms()  # 新增代码+BrowserRuntimeProtocol: 更新毫秒时间戳；若没有这行代码，状态文件不会反映最新动作。

    def mark_running(self, stage_id: str = "") -> None:  # 新增代码+BrowserRuntimeProtocol: 标记 run 正在执行；若没有这行代码，真实浏览器任务无法进入运行状态。
        self.status = "running"  # 新增代码+BrowserRuntimeProtocol: 设置运行中状态；若没有这行代码，状态页可能仍显示 pending。
        self.current_stage_id = stage_id or self.current_stage_id  # 新增代码+BrowserRuntimeProtocol: 保存当前阶段；若没有这行代码，恢复无法定位阶段。
        self._touch()  # 新增代码+BrowserRuntimeProtocol: 刷新更新时间；若没有这行代码，状态页看不到最新进展。

    def mark_stage_completed(self, stage_id: str) -> None:  # 新增代码+BrowserRuntimeProtocol: 标记某阶段已完成；若没有这行代码，中断恢复无法跳过完成阶段。
        if stage_id and stage_id not in self.completed_stage_ids:  # 新增代码+BrowserRuntimeProtocol: 避免重复记录同一阶段；若没有这行代码，状态文件会堆重复项。
            self.completed_stage_ids.append(stage_id)  # 新增代码+BrowserRuntimeProtocol: 追加完成阶段 id；若没有这行代码，resume 没有依据。
        self._touch()  # 新增代码+BrowserRuntimeProtocol: 刷新更新时间；若没有这行代码，阶段完成时间线不更新。

    def add_action(self, action_id: str) -> None:  # 新增代码+BrowserRuntimeProtocol: 把动作 id 挂到 run；若没有这行代码，run 无法列出执行过的工具。
        if action_id and action_id not in self.action_ids:  # 新增代码+BrowserRuntimeProtocol: 避免重复记录动作；若没有这行代码，回放序列可能出现重复。
            self.action_ids.append(action_id)  # 新增代码+BrowserRuntimeProtocol: 追加动作 id；若没有这行代码，run 和 action 文件断开。
        self._touch()  # 新增代码+BrowserRuntimeProtocol: 刷新更新时间；若没有这行代码，状态页不知道 run 有新动作。

    def add_observation(self, observation_id: str) -> None:  # 新增代码+BrowserRuntimeProtocol: 把 observation id 挂到 run；若没有这行代码，run 无法列出页面证据。
        if observation_id and observation_id not in self.observation_ids:  # 新增代码+BrowserRuntimeProtocol: 避免重复记录观察；若没有这行代码，证据列表会有重复项。
            self.observation_ids.append(observation_id)  # 新增代码+BrowserRuntimeProtocol: 追加 observation id；若没有这行代码，页面证据无法汇总。
        self._touch()  # 新增代码+BrowserRuntimeProtocol: 刷新更新时间；若没有这行代码，状态页不知道有新观察。

    def mark_completed(self, summary: str = "") -> None:  # 新增代码+BrowserRuntimeProtocol: 标记 run 成功完成；若没有这行代码，状态机无法收尾。
        self.status = "completed"  # 新增代码+BrowserRuntimeProtocol: 设置完成状态；若没有这行代码，queue 可能继续重跑。
        self.summary = summary or self.summary  # 新增代码+BrowserRuntimeProtocol: 保存完成摘要；若没有这行代码，用户只能看原始事件。
        self._touch()  # 新增代码+BrowserRuntimeProtocol: 刷新更新时间；若没有这行代码，完成状态时间线不更新。

    def mark_failed(self, error_type: str, error_message: str) -> None:  # 新增代码+BrowserRuntimeProtocol: 标记 run 失败；若没有这行代码，最终失败无法稳定落盘。
        self.status = "failed"  # 新增代码+BrowserRuntimeProtocol: 设置失败状态；若没有这行代码，状态页可能误报运行中。
        self.error_type = error_type  # 新增代码+BrowserRuntimeProtocol: 保存失败分类；若没有这行代码，恢复策略无法判断原因。
        self.error_message = error_message  # 新增代码+BrowserRuntimeProtocol: 保存失败说明；若没有这行代码，用户不知道具体问题。
        self._touch()  # 新增代码+BrowserRuntimeProtocol: 刷新更新时间；若没有这行代码，失败状态时间线不更新。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+BrowserRuntimeProtocol: 把 run 转成 JSON 字典；若没有这行代码，BrowserRuntimeStore 无法落盘状态。
        return {"run_id": self.run_id, "session_id": self.session_id, "prompt": self.prompt, "status": self.status, "current_stage_id": self.current_stage_id, "completed_stage_ids": list(self.completed_stage_ids), "action_ids": list(self.action_ids), "observation_ids": list(self.observation_ids), "summary": self.summary, "error_type": self.error_type, "error_message": self.error_message, "metadata": _safe_dict(self.metadata), "created_at_ms": self.created_at_ms, "updated_at_ms": self.updated_at_ms}  # 新增代码+BrowserRuntimeProtocol: 返回完整 run 字段；若没有这行代码，持久化、CLI 和 verifier 都缺数据。

    @classmethod  # 新增代码+BrowserRuntimeProtocol: 提供从 JSON 字典恢复 run 的入口；若没有这行代码，store 只能返回 dict。
    def from_dict(cls, payload: dict[str, Any] | None) -> "BrowserRun":  # 新增代码+BrowserRuntimeProtocol: 从持久化 payload 恢复 run；若没有这行代码，进程中断后无法恢复浏览器任务。
        safe = _safe_dict(payload)  # 新增代码+BrowserRuntimeProtocol: 对外部 payload 做字典兜底；若没有这行代码，坏 run 文件会拖垮恢复。
        return cls(run_id=_text(safe.get("run_id")), session_id=_text(safe.get("session_id")), prompt=_text(safe.get("prompt")), status=_text(safe.get("status"), "pending"), current_stage_id=_text(safe.get("current_stage_id")), completed_stage_ids=[_text(item) for item in _safe_list(safe.get("completed_stage_ids"))], action_ids=[_text(item) for item in _safe_list(safe.get("action_ids"))], observation_ids=[_text(item) for item in _safe_list(safe.get("observation_ids"))], summary=_text(safe.get("summary")), error_type=_text(safe.get("error_type")), error_message=_text(safe.get("error_message")), metadata=_safe_dict(safe.get("metadata")), created_at_ms=_number(safe.get("created_at_ms"), now_ms()), updated_at_ms=_number(safe.get("updated_at_ms"), now_ms()))  # 新增代码+BrowserRuntimeProtocol: 返回完整 run 对象；若没有这行代码，浏览器 run 无法跨进程恢复。
