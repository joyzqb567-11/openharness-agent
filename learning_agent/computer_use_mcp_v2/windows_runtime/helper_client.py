"""Windows Computer Use 窗口观察 helper 合同。"""  # 新增代码+Phase29ComputerUse: 把截图和 UIA 观察来源抽象出来；如果没有这个文件，Windows 后端会直接绑定某一种截图实现而难以测试。 

from __future__ import annotations  # 新增代码+Phase29ComputerUse: 延迟解析类型注解；如果没有这行代码，旧运行路径遇到前向类型时更容易导入失败。 

from dataclasses import dataclass  # 新增代码+Phase29ComputerUse: 使用 dataclass 表达 helper 返回值；如果没有这行代码，payload 需要手写初始化样板。 
from typing import Any, Protocol  # 新增代码+Phase29ComputerUse: 引入通用窗口 dict 和 helper 协议类型；如果没有这行代码，后端依赖边界会不清楚。 


@dataclass(frozen=True)  # 新增代码+Phase29ComputerUse: 让观察 payload 不可变；如果没有这行代码，证据落盘前可能被调用方无意改写。 
class WindowObservationPayload:  # 新增代码+Phase29ComputerUse: 定义一次窗口截图/UIA 观察结果；如果没有这个类，helper 返回字段会变成松散 dict。 
    screenshot_bytes: bytes = b""  # 新增代码+Phase29ComputerUse: 保存截图原始字节；如果没有这行代码，evidence store 无法写出截图 artifact。 
    screenshot_format: str = ""  # 新增代码+Phase29ComputerUse: 保存截图格式扩展名；如果没有这行代码，截图文件无法确定后缀。 
    screenshot_width: int = 0  # 新增代码+Phase29ComputerUse: 保存截图宽度；如果没有这行代码，工具响应只能退回窗口 rect 占位。 
    screenshot_height: int = 0  # 新增代码+Phase29ComputerUse: 保存截图高度；如果没有这行代码，工具响应缺少截图尺寸证据。 
    accessibility_text: str = ""  # 新增代码+Phase29ComputerUse: 保存原始 UIA 文本输入；如果没有这行代码，后续无法生成可访问性摘要。 
    focused_element: str = ""  # 新增代码+Phase29ComputerUse: 保存焦点控件摘要；如果没有这行代码，模型无法知道当前焦点位置。 
    selected_text: str = ""  # 新增代码+Phase29ComputerUse: 保存选中文本摘要；如果没有这行代码，窗口状态缺少选择上下文。 
    document_text: str = ""  # 新增代码+Phase29ComputerUse: 保存文档级文本摘要；如果没有这行代码，窗口状态缺少正文上下文。 
    helper_name: str = "unknown"  # 新增代码+Phase29ComputerUse: 标记观察 helper 名称；如果没有这行代码，证据来源无法审计。 
    helper_available: bool = False  # 新增代码+Phase29ComputerUse: 标记 helper 是否真正可用；如果没有这行代码，状态无法区分截图失败和没有 helper。 
    helper_reason: str = ""  # 新增代码+Phase29ComputerUse: 保存 helper 状态说明；如果没有这行代码，用户不知道为什么截图或 UIA 缺失。 


class WindowObservationHelper(Protocol):  # 新增代码+Phase29ComputerUse: 定义窗口观察 helper 协议；如果没有这个协议，Windows 后端无法以统一方式调用静态 helper 和未来 native helper。 
    def status(self) -> dict[str, Any]:  # 新增代码+Phase29ComputerUse: 要求 helper 报告能力边界；如果没有这行代码，computer_status 无法显示截图/UIA helper 状态。 
        ...  # 新增代码+Phase29ComputerUse: Protocol 方法占位；如果没有这行代码，接口声明语法不完整。 

    def observe_window(self, window: dict[str, Any]) -> WindowObservationPayload:  # 新增代码+Phase29ComputerUse: 要求 helper 按窗口返回观察 payload；如果没有这行代码，get_window_state 无法获取截图/UIA 输入。 
        ...  # 新增代码+Phase29ComputerUse: Protocol 方法占位；如果没有这行代码，接口声明语法不完整。 


class NullWindowObservationHelper:  # 新增代码+Phase29ComputerUse: 定义默认不可用 helper；如果没有这个类，未配置 native helper 时后端无法优雅降级。 
    def status(self) -> dict[str, Any]:  # 新增代码+Phase29ComputerUse: 返回默认 helper 状态；如果没有这段代码，status 无法说明截图/UIA 尚未接入。 
        return {"helper": "none", "available": False, "reason": "Phase 29 helper 未配置；只能保存窗口几何 metadata，不会捕获真实截图或 UIA 文本。"}  # 新增代码+Phase29ComputerUse: 明确默认不捕获真实屏幕；如果没有这行代码，用户可能误以为已读取屏幕内容。 

    def observe_window(self, window: dict[str, Any]) -> WindowObservationPayload:  # 新增代码+Phase29ComputerUse: 返回空观察 payload；如果没有这段代码，默认后端调用 helper 时会崩溃。 
        return WindowObservationPayload(accessibility_text="Phase 29 helper 未配置；当前只保存窗口几何 metadata，不读取真实 UI Automation 文本。", helper_name="none", helper_available=False, helper_reason="未配置 Phase 29 窗口观察 helper。")  # 修改代码+Phase29ComputerUse: 返回可审计的空 payload 和 Phase 29 占位说明；如果没有这行代码，旧 Phase 28 兼容测试看不到后续 UIA 边界。 


class StaticWindowObservationHelper:  # 新增代码+Phase29ComputerUse: 定义测试和验收用静态 helper；如果没有这个类，Phase 29 测试只能依赖真实桌面截图。 
    def __init__(self, payloads: dict[str, WindowObservationPayload] | None = None, default_payload: WindowObservationPayload | None = None) -> None:  # 新增代码+Phase29ComputerUse: 初始化静态 helper 的窗口 payload 映射；如果没有这段代码，测试无法按 window_id 注入截图/UIA。 
        self.payloads = dict(payloads or {})  # 新增代码+Phase29ComputerUse: 保存 window_id 到 payload 的副本；如果没有这行代码，外部修改会污染 helper 行为。 
        self.default_payload = default_payload  # 新增代码+Phase29ComputerUse: 保存可选默认 payload；如果没有这行代码，未命中窗口时无法提供兜底观察。 

    def status(self) -> dict[str, Any]:  # 新增代码+Phase29ComputerUse: 返回静态 helper 状态；如果没有这段代码，status 测试无法确认 helper 来源。 
        return {"helper": "static_phase29_helper", "available": True, "reason": "Phase 29 静态 helper 用于测试和可见终端验收，不读取真实桌面。"}  # 新增代码+Phase29ComputerUse: 明确静态 helper 边界；如果没有这行代码，用户可能把假截图误认为真实截图。 

    def observe_window(self, window: dict[str, Any]) -> WindowObservationPayload:  # 新增代码+Phase29ComputerUse: 按窗口 id 返回静态 payload；如果没有这段代码，get_window_state 无法从测试 helper 取证据。 
        window_id = str(window.get("window_id", ""))  # 新增代码+Phase29ComputerUse: 读取窗口 id 作为映射键；如果没有这行代码，helper 无法知道目标窗口是谁。 
        payload = self.payloads.get(window_id, self.default_payload)  # 新增代码+Phase29ComputerUse: 优先取指定窗口 payload；如果没有这行代码，多窗口测试无法区分证据。 
        if payload is None:  # 新增代码+Phase29ComputerUse: 判断是否没有可用 payload；如果没有这行代码，后续会访问 None 字段。 
            return WindowObservationPayload(helper_name="static_phase29_helper", helper_available=True, helper_reason="静态 helper 没有为该窗口配置 payload。")  # 新增代码+Phase29ComputerUse: 返回空但可解释的 payload；如果没有这行代码，缺 payload 会变成异常。 
        return payload  # 新增代码+Phase29ComputerUse: 返回配置好的观察 payload；如果没有这行代码，测试无法拿到截图/UIA 数据。 
