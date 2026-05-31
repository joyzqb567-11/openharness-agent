"""交互式终端应用层，承载真实用户可见的输入输出循环。"""  # 新增代码+AppSplit: 说明本模块负责交互终端；若没有这行代码，终端循环仍会堆在 learning_agent.py。
from __future__ import annotations  # 新增代码+AppSplit: 允许类型注解延迟解析；若没有这行代码，类型提示在部分运行顺序下可能提前求值。

from pathlib import Path  # 新增代码+AppSplit: 标注工作区路径类型；若没有这行代码，终端事件里的 workspace 来源不清楚。
from typing import Any  # 新增代码+AppSplit: 允许接收任意实现了 run 的 agent；若没有这行代码，模块会和 LearningAgent 类强耦合。

try:  # 新增代码+AppSplit: 优先按包路径导入轮次格式化和验收事件 helper；若没有这行代码，包运行模式下交互层无法复用通用能力。
    from learning_agent.core.config import format_max_turns_status  # 新增代码+AppSplit: 导入轮次状态格式化；若没有这行代码，终端启动提示无法显示当前策略。
    from learning_agent.observability.acceptance_events import emit_acceptance_event  # 新增代码+AppSplit: 导入验收事件写入器；若没有这行代码，真实终端控制器无法知道何时输入 prompt。
    from learning_agent.observability.run_records import build_final_answer_event_payload  # 新增代码+AppSplit: 导入最终回答事件 payload helper；若没有这行代码，final_answer_printed 会丢完整回答字段。
except ModuleNotFoundError as error:  # 新增代码+AppSplit: 捕获脚本模式下包路径不可用；若没有这行代码，双击 bat 时交互层可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.config", "learning_agent.observability", "learning_agent.observability.acceptance_events", "learning_agent.observability.run_records"}:  # 新增代码+AppSplit: 只允许目标路径缺失时 fallback；若没有这行代码，内部真实 bug 会被误吞。
        raise  # 新增代码+AppSplit: 重新抛出真实导入错误；若没有这行代码，观测层或配置层问题会被隐藏。
    from core.config import format_max_turns_status  # 新增代码+AppSplit: 脚本模式从同目录 core 包导入；若没有这行代码，直接运行时轮次提示会断开。
    from observability.acceptance_events import emit_acceptance_event  # 新增代码+AppSplit: 脚本模式从同目录 observability 包导入；若没有这行代码，bat 入口无法写验收事件。
    from observability.run_records import build_final_answer_event_payload  # 新增代码+AppSplit: 脚本模式导入最终回答 payload helper；若没有这行代码，真实终端最终回答事件会断开。


def run_interactive_session(agent: Any, workspace: Path, visible_tools: list[str], max_turns: int | None, prompt_soft_token_limit: int) -> None:  # 新增代码+AppSplit: 运行用户可见交互式终端循环；若没有这行代码，main 仍要承载所有交互逻辑。
    print("模型-工具循环轮次策略：" + format_max_turns_status(max_turns))  # 新增代码+AppSplit: 启动时显示当前轮次策略；若没有这行代码，用户不知道配置文件、环境变量或 CLI 是否生效。
    print(f"提示词软预算：约 {prompt_soft_token_limit} tokens")  # 新增代码+AppSplit: 启动时显示 prompt compact 预算；若没有这行代码，用户不知道当前是否会触发提示词压缩。
    print("模型当前可见工具：" + ", ".join(visible_tools))  # 新增代码+AppSplit: 显示模型本轮能看到的全部工具名；若没有这行代码，用户无法确认 web_search/fetch_url 是否进入工具列表。
    print("Learning Agent 已启动。输入 exit 或 quit 退出。")  # 新增代码+AppSplit: 显示启动提示；若没有这行代码，用户不知道终端已准备好。
    while True:  # 新增代码+AppSplit: 开始命令行交互循环；若没有这行代码，agent 只能回答一次或直接退出。
        emit_acceptance_event("agent_ready_for_user_prompt", {"workspace": str(workspace), "visible_tools": visible_tools})  # 新增代码+AppSplit: 在显示输入提示前写 ready 事件；若没有这行代码，外部 agent 无法稳定知道何时输入任务 prompt。
        user_input = input("\n你 > ").strip()  # 新增代码+AppSplit: 读取用户输入并清理空白；若没有这行代码，终端无法接收真实用户任务。
        if user_input.lower() in {"exit", "quit"}:  # 新增代码+AppSplit: 判断用户是否要退出；若没有这行代码，用户无法自然结束交互。
            print("再见。")  # 新增代码+AppSplit: 打印退出提示；若没有这行代码，用户不知道程序是否正常结束。
            return  # 新增代码+AppSplit: 结束交互函数；若没有这行代码，退出命令后仍会继续循环。
        if not user_input:  # 新增代码+AppSplit: 跳过空输入；若没有这行代码，空白回车会触发无意义模型调用。
            continue  # 新增代码+AppSplit: 等待下一次输入；若没有这行代码，空输入会继续向下执行。
        emit_acceptance_event("user_prompt_received", {"length": len(user_input), "prompt_preview": user_input[:200]})  # 新增代码+AppSplit: 记录输入长度和短预览；若没有这行代码，控制器无法确认真实终端收到的是哪条任务。
        answer = agent.run(user_input, max_turns=max_turns)  # 新增代码+AppSplit: 调用 agent 主循环生成最终回答；若没有这行代码，交互终端不会真正工作。
        print(f"\nAgent > {answer}")  # 新增代码+AppSplit: 打印最终回答给用户；若没有这行代码，用户看不到 agent 结果。
        final_answer_event_payload = build_final_answer_event_payload(answer)  # 新增代码+AppSplit: 组装最终回答验收 payload；若没有这行代码，完整 answer_text 字段会丢失。
        emit_acceptance_event("final_answer_printed", final_answer_event_payload)  # 新增代码+AppSplit: 写出最终回答事件；若没有这行代码，外部控制器无法稳定确认真实最终输出。
