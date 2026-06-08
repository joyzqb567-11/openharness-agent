"""浏览器动作回放计划器，默认只生成安全 dry-run 计划。"""  # 新增代码+BrowserReplayStage10: 说明本模块负责可复现计划；若没有这行代码，回放边界不清楚。

from __future__ import annotations  # 新增代码+BrowserReplayStage10: 延迟解析类型注解；若没有这行代码，类型引用更脆弱。

from typing import Any  # 新增代码+BrowserReplayStage10: 回放计划是通用 JSON；若没有这行代码，类型边界不清楚。

from learning_agent.browser.runtime_models import BrowserAction  # 新增代码+BrowserReplayStage10: 导入动作协议模型；若没有这行代码，计划器无法读取动作字段。
from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+BrowserReplayStage10: 导入 runtime store；若没有这行代码，计划器没有事实源。

REPLAY_BLOCKED_TOOLS = {"browser_evaluate", "browser_connect_real_chrome", "browser_disconnect_real_chrome", "browser_site_grant", "browser_flow_run"}  # 新增代码+BrowserReplayStage10: 定义禁止回放工具；若没有这行代码，高风险动作可能重复执行。
REPLAY_SECRET_TOOLS = {"browser_type_secret"}  # 新增代码+BrowserReplayStage10: 定义涉及 secret 的工具；若没有这行代码，密码输入可能进入回放计划。


class BrowserReplayPlanner:  # 新增代码+BrowserReplayStage10: 从持久动作生成安全回放计划；若没有这个类，回放只能读旧 JSONL 文本。
    def __init__(self, store: BrowserRuntimeStore) -> None:  # 新增代码+BrowserReplayStage10: 初始化计划器依赖的 store；若没有这行代码，无法指定工作区。
        self.store = store  # 新增代码+BrowserReplayStage10: 保存 runtime store；若没有这行代码，计划器无法读取 run/action。

    def build_plan(self, run_id: str) -> dict[str, Any]:  # 新增代码+BrowserReplayStage10: 为指定 run 生成 dry-run 计划；若没有这行代码，回放没有主入口。
        browser_run = self.store.load_run(run_id)  # 新增代码+BrowserReplayStage10: 读取 run 获取动作序列；若没有这行代码，计划器不知道有哪些动作。
        steps: list[dict[str, Any]] = []  # 新增代码+BrowserReplayStage10: 保存可回放步骤；若没有这行代码，函数没有返回容器。
        skipped: list[dict[str, Any]] = []  # 新增代码+BrowserReplayStage10: 保存跳过动作；若没有这行代码，用户不知道哪些动作被过滤。
        for action_id in browser_run.action_ids:  # 新增代码+BrowserReplayStage10: 按原始顺序遍历动作；若没有这行代码，回放顺序会丢失。
            try:  # 新增代码+BrowserReplayStage10: 单个动作文件可能损坏或缺失；若没有这行代码，一个坏动作会拖垮全部计划。
                action = self.store.load_action(action_id)  # 新增代码+BrowserReplayStage10: 读取动作详情；若没有这行代码，计划缺少工具名和参数。
            except FileNotFoundError:  # 新增代码+BrowserReplayStage10: 动作缺失时记录跳过；若没有这行代码，异常会中断计划。
                skipped.append({"action_id": action_id, "reason": "missing_action"})  # 新增代码+BrowserReplayStage10: 记录缺失原因；若没有这行代码，审计不透明。
                continue  # 新增代码+BrowserReplayStage10: 继续后续动作；若没有这行代码，后续安全动作也会丢失。
            decision = self._classify_action(action)  # 新增代码+BrowserReplayStage10: 判断动作是否可回放；若没有这行代码，过滤规则不会生效。
            if decision != "replay":  # 新增代码+BrowserReplayStage10: 非安全动作进入跳过列表；若没有这行代码，secret 和高风险动作可能进入 steps。
                skipped.append({"action_id": action.action_id, "tool_name": action.tool_name, "reason": decision})  # 新增代码+BrowserReplayStage10: 记录跳过原因；若没有这行代码，用户无法复盘过滤。
                continue  # 新增代码+BrowserReplayStage10: 跳过该动作；若没有这行代码，危险动作仍会加入计划。
            steps.append({"action_id": action.action_id, "tool_name": action.tool_name, "arguments": dict(action.arguments_redacted)})  # 新增代码+BrowserReplayStage10: 写入安全计划步骤；若没有这行代码，计划没有可执行信息。
        return {"run_id": run_id, "dry_run": True, "steps": steps, "skipped": skipped}  # 新增代码+BrowserReplayStage10: 返回结构化回放计划；若没有这行代码，调用方拿不到结果。

    def _classify_action(self, action: BrowserAction) -> str:  # 新增代码+BrowserReplayStage10: 判断单个动作是否可回放；若没有这行代码，过滤逻辑会塞在主循环里。
        if action.status != "completed":  # 新增代码+BrowserReplayStage10: 只允许成功动作回放；若没有这行代码，失败动作可能被重复执行。
            return "not_completed"  # 新增代码+BrowserReplayStage10: 返回失败状态原因；若没有这行代码，跳过原因不清楚。
        if action.tool_name in REPLAY_SECRET_TOOLS or "secret" in action.tool_name.lower():  # 新增代码+BrowserReplayStage10: 拦截 secret 工具；若没有这行代码，密码输入可能进入回放。
            return "secret_input_skipped"  # 新增代码+BrowserReplayStage10: 返回 secret 跳过原因；若没有这行代码，用户不知道为什么少一步。
        if action.tool_name in REPLAY_BLOCKED_TOOLS:  # 新增代码+BrowserReplayStage10: 拦截高风险工具；若没有这行代码，脚本或连接动作可能重复执行。
            return "blocked_tool"  # 新增代码+BrowserReplayStage10: 返回阻断原因；若没有这行代码，跳过不透明。
        return "replay"  # 新增代码+BrowserReplayStage10: 其余成功动作可进入 dry-run 计划；若没有这行代码，安全动作也无法复现。
