"""Windows OS Computer Use 协议模型。"""  # 新增代码+Phase27ComputerUse: 把窗口身份和观察协议集中放在这里；如果没有这个文件，controller 会继续用松散 dict 传递窗口目标。

from __future__ import annotations  # 新增代码+Phase27ComputerUse: 延迟解析类型注解；如果没有这行代码，旧 Python 路径遇到前向类型时更容易导入失败。

from dataclasses import dataclass  # 新增代码+Phase27ComputerUse: 使用 dataclass 定义稳定窗口引用；如果没有这行代码，窗口结构需要手写初始化和转换样板。
from typing import Any  # 新增代码+Phase27ComputerUse: 引入通用 JSON 值类型；如果没有这行代码，协议 helper 的参数类型会不清楚。


MAX_PREVIEW_LENGTH = 160  # 新增代码+Phase27ComputerUse: 限制窗口标题等预览长度；如果没有这行代码，状态和审计输出可能泄露过长文本。


# 新增代码+Phase27ComputerUse: 函数段开始，clean_protocol_text 用于清理窗口标题等展示字段；如果没有这段函数，协议输出可能携带过长或带控制字符的文本，作者意图是让观察结果更安全、更稳定，函数与 build_window_ref 配合生成干净窗口引用。
def clean_protocol_text(value: Any, *, max_length: int = MAX_PREVIEW_LENGTH) -> str:  # 新增代码+Phase27ComputerUse: 定义文本清理函数；如果没有这行代码，窗口标题清理逻辑会散落在多个调用点。
    text = str(value or "")  # 新增代码+Phase27ComputerUse: 把任意值转成字符串并处理空值；如果没有这行代码，None 或数字标题会让后续字符串操作不稳定。
    text = " ".join(text.replace("\r", " ").replace("\n", " ").split())  # 新增代码+Phase27ComputerUse: 移除换行和多余空白；如果没有这行代码，工具返回可能被窗口标题打乱排版。
    if len(text) > max_length:  # 新增代码+Phase27ComputerUse: 检查文本是否超过预览长度；如果没有这行代码，长标题会撑大上下文和审计日志。
        return text[:max_length]  # 新增代码+Phase27ComputerUse: 截断到安全长度；如果没有这行代码，过长文本无法被限制。
    return text  # 新增代码+Phase27ComputerUse: 返回清理后的文本；如果没有这行代码，调用方拿不到规范化结果。
# 新增代码+Phase27ComputerUse: 函数段结束，clean_protocol_text 到此结束；如果没有这个结束标记，初学者很难看出这段 helper 的边界。


@dataclass(frozen=True)  # 新增代码+Phase27ComputerUse: 让窗口引用不可变；如果没有这行代码，动作执行前后窗口身份可能被误改。
class ComputerUseWindowRef:  # 新增代码+Phase27ComputerUse: 定义可被 observe/action 共享的窗口身份；如果没有这个类，未知窗口校验缺少稳定协议对象。
    app_id: str  # 新增代码+Phase27ComputerUse: 保存应用身份；如果没有这行代码，模型只能靠窗口标题猜应用，容易点错目标。
    window_id: str  # 新增代码+Phase27ComputerUse: 保存窗口身份；如果没有这行代码，同一应用多个窗口无法区分。
    title_preview: str = ""  # 新增代码+Phase27ComputerUse: 保存安全截断后的窗口标题；如果没有这行代码，用户难以判断窗口大概是谁。
    process_path_hash: str = ""  # 新增代码+Phase27ComputerUse: 保存进程路径哈希占位；如果没有这行代码，后续真实 Windows 后端无法做进程身份辅助校验。
    captured_at: str = ""  # 新增代码+Phase27ComputerUse: 保存引用采集时间占位；如果没有这行代码，后续无法判断窗口引用是否过期。

    # 新增代码+Phase27ComputerUse: 函数段开始，to_dict 用于把强类型窗口引用转回 JSON；如果没有这段函数，工具结果无法稳定序列化给模型，作者意图是让 controller/backend 都使用同一输出形状。
    def to_dict(self) -> dict[str, str]:  # 新增代码+Phase27ComputerUse: 定义窗口引用序列化方法；如果没有这行代码，调用方需要重复手写 dict。
        return {"app_id": self.app_id, "window_id": self.window_id, "title_preview": self.title_preview, "process_path_hash": self.process_path_hash, "captured_at": self.captured_at}  # 新增代码+Phase27ComputerUse: 返回公开窗口引用字段；如果没有这行代码，observe 返回会缺少稳定 JSON 结构。
    # 新增代码+Phase27ComputerUse: 函数段结束，to_dict 到此结束；如果没有这个结束标记，用户学习时不容易区分模型和 helper。


# 新增代码+Phase27ComputerUse: 函数段开始，build_window_ref 用于从模型传入的 dict 构造强类型窗口引用；如果没有这段函数，未知窗口校验会被空字段或脏字段绕过，作者意图是统一校验 app_id/window_id 两个必需身份字段。
def build_window_ref(raw_window: Any) -> ComputerUseWindowRef | None:  # 新增代码+Phase27ComputerUse: 定义窗口引用构造函数；如果没有这行代码，controller 不能把 JSON 参数转换成安全对象。
    if not isinstance(raw_window, dict):  # 新增代码+Phase27ComputerUse: 只接受对象形式的窗口引用；如果没有这行代码，字符串或列表可能误入窗口校验。
        return None  # 新增代码+Phase27ComputerUse: 非对象直接拒绝；如果没有这行代码，后续 get 调用会在错误类型上崩溃。
    app_id = clean_protocol_text(raw_window.get("app_id"))  # 新增代码+Phase27ComputerUse: 读取并清理应用身份；如果没有这行代码，app_id 可能带空白导致匹配失败。
    window_id = clean_protocol_text(raw_window.get("window_id"))  # 新增代码+Phase27ComputerUse: 读取并清理窗口身份；如果没有这行代码，window_id 可能带空白导致匹配失败。
    if not app_id or not window_id:  # 新增代码+Phase27ComputerUse: 要求两个身份字段同时存在；如果没有这行代码，半截窗口引用会被当成可信目标。
        return None  # 新增代码+Phase27ComputerUse: 身份不完整时拒绝构造；如果没有这行代码，未知窗口校验会变得含糊。
    title_preview = clean_protocol_text(raw_window.get("title_preview", raw_window.get("title", "")))  # 新增代码+Phase27ComputerUse: 兼容 title/title_preview 两种输入；如果没有这行代码，测试后端和真实后端的窗口标题字段会不一致。
    process_path_hash = clean_protocol_text(raw_window.get("process_path_hash", ""))  # 新增代码+Phase27ComputerUse: 读取进程路径哈希占位；如果没有这行代码，后续身份增强字段会丢失。
    captured_at = clean_protocol_text(raw_window.get("captured_at", ""))  # 新增代码+Phase27ComputerUse: 读取采集时间占位；如果没有这行代码，窗口引用新旧无法表达。
    return ComputerUseWindowRef(app_id=app_id, window_id=window_id, title_preview=title_preview, process_path_hash=process_path_hash, captured_at=captured_at)  # 新增代码+Phase27ComputerUse: 返回强类型窗口引用；如果没有这行代码，调用方拿不到校验后的窗口对象。
# 新增代码+Phase27ComputerUse: 函数段结束，build_window_ref 到此结束；如果没有这个结束标记，用户不容易看出窗口引用构造流程。


# 新增代码+Phase27ComputerUse: 函数段开始，window_ref_identity 用于生成窗口匹配键；如果没有这段函数，不同模块会重复拼接 app_id/window_id，作者意图是让未知窗口校验只看稳定身份字段。
def window_ref_identity(window_ref: ComputerUseWindowRef) -> tuple[str, str]:  # 新增代码+Phase27ComputerUse: 定义窗口身份键函数；如果没有这行代码，内存后端无法稳定索引窗口。
    return (window_ref.app_id, window_ref.window_id)  # 新增代码+Phase27ComputerUse: 返回应用和窗口二元组；如果没有这行代码，窗口匹配会缺少统一键。
# 新增代码+Phase27ComputerUse: 函数段结束，window_ref_identity 到此结束；如果没有这个结束标记，读者不容易知道身份键 helper 的边界。
