"""Learning Agent 的假模型交互启动器。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT_TEXT = str(REPO_ROOT)
sys.path = [path for path in sys.path if path != REPO_ROOT_TEXT]
sys.path.insert(0, REPO_ROOT_TEXT)

from learning_agent.core.agent import LearningAgent, ToolCallingFakeModel  # 修改代码+LegacyEntryCut: 从核心层导入 agent 主类和假模型；若没有这行代码，辅助 REPL 会继续依赖旧脚本入口。
from learning_agent.core.messages import ModelMessage, ToolCall  # 修改代码+LegacyEntryCut: 从消息层导入模型消息和工具调用对象；若没有这行代码，假模型无法构造标准响应。


WORKSPACE = Path(__file__).resolve().parent
READ_TARGET = WORKSPACE / "memory.md"


def ask_permission(action: str) -> bool:
    """在终端里询问用户是否允许一次有副作用的操作。"""
    answer = input(f"\n[权限确认] {action}\n是否允许？输入 y 允许，其它拒绝：").strip().lower()
    return answer in {"y", "yes"}


def make_fake_model(prompt: str) -> ToolCallingFakeModel:
    """根据用户输入关键词，创建一个会模拟工具调用的假模型。"""
    lower = prompt.lower()

    if "记" in prompt or "memory" in lower:
        return ToolCallingFakeModel(
            [
                ModelMessage(
                    text="",
                    tool_calls=[
                        ToolCall(name="append_memory", arguments={"text": prompt}),
                    ],
                ),
                ModelMessage(text="假模型最终回答：我已经尝试把这条内容写入 memory.md。"),
            ]
        )

    if "写" in prompt or "write" in lower:
        target = WORKSPACE / "manual_fake_output.txt"
        return ToolCallingFakeModel(
            [
                ModelMessage(
                    text="",
                    tool_calls=[
                        ToolCall(
                            name="write_file",
                            arguments={
                                "path": str(target),
                                "content": "这是由假模型触发 write_file 写入的内容。",
                            },
                        ),
                    ],
                ),
                ModelMessage(text=f"假模型最终回答：我已经尝试写入文件：{target}"),
            ]
        )

    if "读" in prompt or "read" in lower:
        return ToolCallingFakeModel(
            [
                ModelMessage(
                    text="",
                    tool_calls=[
                        ToolCall(name="read_file", arguments={"path": str(READ_TARGET)}),
                    ],
                ),
                ModelMessage(text="假模型最终回答：我已经通过 read_file 工具读取了 memory.md。"),
            ]
        )

    return ToolCallingFakeModel(
        [
            ModelMessage(
                text="假模型最终回答：这次没有调用工具。你可以输入：读取文件 / 写文件 / 记住我的偏好。"
            )
        ]
    )


def run_once(prompt: str, *, allow_all: bool = False) -> str:
    """运行一轮假模型 agent，主要给自检和未来测试使用。"""
    permission = (lambda action: True) if allow_all else ask_permission
    agent = LearningAgent(model=make_fake_model(prompt), workspace=WORKSPACE, ask_permission=permission)
    return agent.run(prompt)


def run_interactive() -> None:
    """启动一个可以手动输入提示词的交互循环。"""
    print("Learning Agent 假模型交互测试已启动。")
    print("可输入：读取文件 / 写文件 / 记住我喜欢中文解释。")
    print("说明：这是测试假模型，不是真实大模型；它按关键词模拟工具调用。")
    print("输入 exit 或 quit 退出。")

    while True:
        prompt = input("\n你 > ").strip()
        if prompt.lower() in {"exit", "quit"}:
            print("已退出假模型测试。")
            break
        if not prompt:
            continue
        print("\nAgent > " + run_once(prompt))


def main() -> int:
    """解析命令行参数，并决定运行自检还是进入交互模式。"""
    parser = argparse.ArgumentParser(description="启动 Learning Agent 假模型交互测试器。")
    parser.add_argument("--self-test", action="store_true", help="只运行一次自检，不进入交互模式。")
    args = parser.parse_args()

    if args.self_test:
        answer = run_once("读取文件", allow_all=True)
        print(answer)
        return 0

    run_interactive()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
