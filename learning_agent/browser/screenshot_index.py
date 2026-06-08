"""浏览器截图索引，把图片文件和 run/stage/action 关联起来。"""  # 新增代码+BrowserObservationStage4: 说明本模块负责截图证据索引；若没有这行代码，截图索引用途不清楚。

from __future__ import annotations  # 新增代码+BrowserObservationStage4: 延迟解析类型注解；若没有这行代码，Path 类型解析更脆弱。

from pathlib import Path  # 新增代码+BrowserObservationStage4: 用 Path 处理截图和索引路径；若没有这行代码，Windows 路径处理容易出错。
from typing import Any  # 新增代码+BrowserObservationStage4: 索引行是通用 JSON 字段；若没有这行代码，类型边界不清楚。

from learning_agent.browser.runtime_models import now_ms  # 新增代码+BrowserObservationStage4: 使用统一毫秒时间戳；若没有这行代码，索引时间格式会分裂。
from learning_agent.runtime.files import append_jsonl, read_jsonl  # 新增代码+BrowserObservationStage4: 复用项目 JSONL helper；若没有这行代码，索引读写会重复实现。


class BrowserScreenshotIndex:  # 新增代码+BrowserObservationStage4: 管理截图索引 JSONL；若没有这个类，截图和动作关系会散落。
    def __init__(self, index_path: str | Path) -> None:  # 新增代码+BrowserObservationStage4: 初始化索引文件路径；若没有这行代码，调用方无法指定存储位置。
        self.index_path = Path(index_path)  # 新增代码+BrowserObservationStage4: 规范化索引路径；若没有这行代码，字符串路径后续处理不稳定。

    def record(self, run_id: str, stage_id: str, action_id: str, screenshot_path: str | Path, observation_id: str = "") -> Path:  # 新增代码+BrowserObservationStage4: 写入一条截图索引；若没有这行代码，截图无法关联任务动作。
        path = Path(screenshot_path)  # 新增代码+BrowserObservationStage4: 规范化截图路径；若没有这行代码，exists 检查和输出不稳定。
        row: dict[str, Any] = {  # 新增代码+BrowserObservationStage4: 构造索引行；若没有这行代码，append_jsonl 没有输入。
            "timestamp_ms": now_ms(),  # 新增代码+BrowserObservationStage4: 记录截图时间；若没有这行代码，多张截图无法排序。
            "run_id": str(run_id),  # 新增代码+BrowserObservationStage4: 保存 run id；若没有这行代码，截图无法归属任务。
            "stage_id": str(stage_id),  # 新增代码+BrowserObservationStage4: 保存 stage id；若没有这行代码，阶段验收无法定位截图。
            "action_id": str(action_id),  # 新增代码+BrowserObservationStage4: 保存 action id；若没有这行代码，截图无法回到具体工具调用。
            "observation_id": str(observation_id),  # 新增代码+BrowserObservationStage4: 保存可选 observation id；若没有这行代码，截图和页面文本证据难以互查。
            "screenshot_path": str(path),  # 新增代码+BrowserObservationStage4: 保存截图文件路径；若没有这行代码，肉眼复验找不到图片。
            "exists": path.exists(),  # 新增代码+BrowserObservationStage4: 保存记录时文件是否存在；若没有这行代码，坏路径不容易被发现。
        }  # 新增代码+BrowserObservationStage4: 结束索引行；若没有这行代码，Python 字典语法无法闭合。
        return append_jsonl(self.index_path, row)  # 新增代码+BrowserObservationStage4: 追加索引并返回路径；若没有这行代码，索引不会落盘。

    def tail(self, limit: int = 20) -> list[dict[str, Any]]:  # 新增代码+BrowserObservationStage4: 读取最近截图索引；若没有这行代码，状态页无法展示截图证据。
        rows = read_jsonl(self.index_path)  # 新增代码+BrowserObservationStage4: 读取索引 JSONL；若没有这行代码，函数没有数据源。
        if limit <= 0:  # 新增代码+BrowserObservationStage4: limit 非正数表示读取全部；若没有这行代码，调用方不能明确请求全量。
            return rows  # 新增代码+BrowserObservationStage4: 返回完整索引；若没有这行代码，limit<=0 没有语义。
        return rows[-limit:]  # 新增代码+BrowserObservationStage4: 返回最近 N 条；若没有这行代码，状态输出可能过长。
