"""Chrome 扩展 native host 只读桥模块。"""  # 新增代码+ChromeExtensionStage5: 说明本包只提供 Stage 5 只读桥能力；若没有这行代码，维护者不知道该包边界。

from .bridge_server import ChromeExtensionBridgeState  # 新增代码+ChromeExtensionStage5: 导出 bridge 状态对象；若没有这行代码，provider 和测试需要深路径导入。
from .message_protocol import build_host_response  # 新增代码+ChromeExtensionStage5: 导出消息协议入口；若没有这行代码，外部调用方无法轻量复用协议。

__all__ = ["ChromeExtensionBridgeState", "build_host_response"]  # 新增代码+ChromeExtensionStage5: 固定公开 API；若没有这行代码，通配导入会暴露内部实现细节。
