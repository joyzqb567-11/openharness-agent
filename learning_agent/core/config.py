from __future__ import annotations  # 新增代码+CoreConfig: 延迟解析类型注解；如果没有这行代码，配置类型在导入顺序变化时更容易出问题。

import argparse  # 新增代码+CoreConfig: 解析命令行参数；如果没有这行代码，--max-turns、--prompt、bridge 参数无法稳定解析。
import json  # 新增代码+CoreConfig: 读取 runtime_config.json；如果没有这行代码，配置文件无法被解析。
import os  # 新增代码+CoreConfig: 读取环境变量覆盖配置；如果没有这行代码，用户无法用环境变量临时调整运行策略。
from dataclasses import dataclass  # 新增代码+CoreConfig: 定义轻量配置数据类；如果没有这行代码，配置只能用容易写错的松散字典传递。
from datetime import date  # 新增代码+CoreConfig: 生成本机本地日期；如果没有这行代码，agent 无法稳定注入当天日期。
from pathlib import Path  # 新增代码+CoreConfig: 处理跨平台路径；如果没有这行代码，runtime_config.json 路径处理容易出错。
from typing import Any  # 新增代码+CoreConfig: 接收 JSON、环境变量和 CLI 的混合输入；如果没有这行代码，解析函数类型边界不清楚。


DEFAULT_PROMPT_SOFT_TOKEN_LIMIT = 60_000  # 新增代码+CoreConfig: 定义默认 prompt 软预算；如果没有这行代码，ContextAssembler 缺少稳定默认阈值。


def get_local_iso_date() -> str:  # 新增代码+CoreConfig: 返回本机本地日历日期；如果没有这行代码，日期逻辑会继续散落在提示词渲染代码里。
    return date.today().isoformat()  # 新增代码+CoreConfig: 生成 YYYY-MM-DD 格式日期；如果没有这行代码，模型每轮无法看到真实当前日期。


@dataclass  # 新增代码+CoreConfig: 自动生成运行配置对象初始化方法；如果没有这行代码，max_turns 和 prompt 预算会继续用松散字段传递。
class AgentRuntimeConfig:  # 新增代码+CoreConfig: 保存 learning_agent 运行时策略；如果没有这个类，主循环配置缺少统一容器。
    max_turns: int | None = None  # 新增代码+CoreConfig: None 表示不按固定轮次主动停止；如果没有这行代码，容易退回写死默认轮次。
    prompt_soft_token_limit: int = DEFAULT_PROMPT_SOFT_TOKEN_LIMIT  # 新增代码+CoreConfig: 保存 prompt 软预算；如果没有这行代码，配置层无法控制 compact 阈值。


@dataclass  # 新增代码+CoreConfig: 自动生成命令行参数对象初始化方法；如果没有这行代码，CLI 参数只能用 argparse Namespace 到处传递。
class MainArgs:  # 新增代码+CoreConfig: 保存 main() 已解析的命令行参数；如果没有这个类，入口层无法清楚区分命令和覆盖项。
    command: str = ""  # 新增代码+CoreConfig: 保存 doctor、run、bridge 等命令；如果没有这行代码，main 无法区分诊断模式和聊天模式。
    max_turns: int | None = None  # 新增代码+CoreConfig: 保存命令行指定的轮次上限或无限制；如果没有这行代码，--max-turns 无法传给 agent.run。
    max_turns_is_set: bool = False  # 新增代码+CoreConfig: 记录用户是否显式传入 --max-turns；如果没有这行代码，无法区分没传和传 none。
    prompt: str = ""  # 新增代码+CoreConfig: 保存一次性 run 命令的用户输入；如果没有这行代码，CLI 无法把任务交给 agent。
    output_json: bool = False  # 新增代码+CoreConfig: 标记 CLI 是否输出 JSON；如果没有这行代码，外部控制器只能解析自然语言。
    bridge_host: str = "127.0.0.1"  # 新增代码+CoreConfig: 保存 HTTP bridge 监听地址；如果没有这行代码，bridge 缺少只绑定本机的安全默认值。
    bridge_port: int = 8765  # 新增代码+CoreConfig: 保存 HTTP bridge 监听端口；如果没有这行代码，外部控制器不知道连接哪个端口。
    bridge_token: str = ""  # 新增代码+CoreConfig: 保存可选 bridge token；如果没有这行代码，HTTP bridge 无法启用简单认证。


def parse_max_turns_value(raw_value: Any, source: str) -> int | None:  # 新增代码+CoreConfig: 把配置、环境变量或 CLI 文本解析成轮次策略；如果没有这行代码，多入口规则会不一致。
    if raw_value is None:  # 新增代码+CoreConfig: None 是无限制策略；如果没有这行代码，runtime_config.json 不能用 null 表示无限制。
        return None  # 新增代码+CoreConfig: 返回 None 交给 run() 表示不启用轮次上限；如果没有这行代码，None 会被误当错误。
    if isinstance(raw_value, bool):  # 新增代码+CoreConfig: bool 在 Python 里也是 int 子类，需要单独拒绝；如果没有这行代码，true 可能被误当成 1。
        raise ValueError(f"{source} 必须是正整数、null、none、unlimited 或 off。")  # 新增代码+CoreConfig: 给出清楚错误；如果没有这行代码，用户填错配置时难以排查。
    if isinstance(raw_value, int):  # 新增代码+CoreConfig: 支持 JSON 文件里直接写数字；如果没有这行代码，配置文件的自然写法不能使用。
        parsed_value = raw_value  # 新增代码+CoreConfig: 保存已解析整数；如果没有这行代码，后续正数校验没有变量可用。
    elif isinstance(raw_value, str):  # 新增代码+CoreConfig: 支持环境变量和 CLI 传入字符串；如果没有这行代码，--max-turns 无法工作。
        normalized_value = raw_value.strip().lower()  # 新增代码+CoreConfig: 清理空白并统一大小写；如果没有这行代码，" None " 会被误判。
        if normalized_value in {"", "none", "null", "unlimited", "off"}:  # 新增代码+CoreConfig: 允许多种易懂写法表示无限制；如果没有这行代码，用户只能记住一种写法。
            return None  # 新增代码+CoreConfig: 返回无限制策略；如果没有这行代码，显式取消轮次上限不生效。
        try:  # 新增代码+CoreConfig: 捕获非数字字符串；如果没有这行代码，int() 的原始异常对初学者不够友好。
            parsed_value = int(normalized_value)  # 新增代码+CoreConfig: 把字符串数字转为 int；如果没有这行代码，run() 会收到字符串导致逻辑错误。
        except ValueError as error:  # 新增代码+CoreConfig: 处理无法转换为整数的配置；如果没有这行代码，错误信息无法说明配置源。
            raise ValueError(f"{source} 必须是正整数、null、none、unlimited 或 off。") from error  # 新增代码+CoreConfig: 带配置源抛出可读错误；如果没有这行代码，用户不知道该改哪里。
    else:  # 新增代码+CoreConfig: 拒绝列表、对象、浮点数等不明确类型；如果没有这行代码，奇怪配置可能进入运行时。
        raise ValueError(f"{source} 必须是正整数、null、none、unlimited 或 off。")  # 新增代码+CoreConfig: 给出统一可读错误；如果没有这行代码，错误处理不一致。
    if parsed_value < 1:  # 新增代码+CoreConfig: 轮次上限必须至少为 1；如果没有这行代码，0 或负数会让 agent 一开始就停止。
        raise ValueError(f"{source} 必须大于等于 1，或写 null/none 表示不限制。")  # 新增代码+CoreConfig: 解释合法取值；如果没有这行代码，用户不知道如何表达无限制。
    return parsed_value  # 新增代码+CoreConfig: 返回合法正整数；如果没有这行代码，调用方拿不到最终轮次上限。


def parse_prompt_soft_token_limit_value(raw_value: Any, source: str) -> int:  # 新增代码+CoreConfig: 解析 prompt 软 token 预算配置；如果没有这行代码，预算配置会和轮次配置混在一起。
    parsed_value = parse_max_turns_value(raw_value, source)  # 新增代码+CoreConfig: 复用正整数解析和错误提示；如果没有这行代码，字符串数字和负数校验会重复实现。
    if parsed_value is None:  # 新增代码+CoreConfig: prompt 软预算必须是明确正整数；如果没有这行代码，ContextAssembler 会缺少可比较阈值。
        raise ValueError(f"{source} 必须是正整数 token 预算，不能写 null/none。")  # 新增代码+CoreConfig: 给出预算字段专属错误；如果没有这行代码，用户不知道要填具体数字。
    return parsed_value  # 新增代码+CoreConfig: 返回可传给 ContextAssembler 的正整数；如果没有这行代码，调用方拿不到解析后的预算。


def parse_cli_max_turns_value(raw_value: str) -> int | None:  # 新增代码+CoreConfig: 给 argparse 使用的 --max-turns 解析器；如果没有这行代码，CLI 错误不能友好展示。
    try:  # 新增代码+CoreConfig: 把通用解析错误转换成 argparse 错误；如果没有这行代码，argparse 可能显示 Python traceback。
        return parse_max_turns_value(raw_value, "--max-turns")  # 新增代码+CoreConfig: 复用统一解析规则；如果没有这行代码，CLI 与配置文件语义可能不一致。
    except ValueError as error:  # 新增代码+CoreConfig: 捕获通用解析错误；如果没有这行代码，argparse 不能优雅提示参数非法。
        raise argparse.ArgumentTypeError(str(error)) from error  # 新增代码+CoreConfig: 转成 argparse 参数错误；如果没有这行代码，用户命令行填错时体验较差。


def parse_main_args(raw_args: list[str]) -> MainArgs:  # 新增代码+CoreConfig: 解析 learning_agent.py 的命令行参数；如果没有这行代码，main 会继续手写参数逻辑。
    parser = argparse.ArgumentParser(description="启动 Learning Agent。")  # 新增代码+CoreConfig: 创建参数解析器并提供说明；如果没有这行代码，--help 无法展示可读帮助。
    parser.add_argument("command", nargs="?", default="", help="可选命令，例如 mcp-doctor 或 doctor。")  # 新增代码+CoreConfig: 保留原有 doctor 位置参数；如果没有这行代码，诊断入口会被破坏。
    parser.add_argument("--max-turns", dest="max_turns", default=None, type=parse_cli_max_turns_value, help="模型-工具循环上限；正整数表示限制，none/null/unlimited/off 表示不限制。")  # 新增代码+CoreConfig: 添加 CLI 轮次覆盖；如果没有这行代码，用户无法临时指定轮次限制。
    parser.add_argument("--prompt", dest="prompt", default="", help="一次性 run 命令要发送给 agent 的用户输入。")  # 新增代码+CoreConfig: 添加非交互式 prompt 参数；如果没有这行代码，CLI 无法直接下发任务。
    parser.add_argument("--json", dest="output_json", action="store_true", help="让 run 命令输出 JSON，方便外部控制器解析。")  # 新增代码+CoreConfig: 添加机器可读输出开关；如果没有这行代码，自动化接收需要解析自然语言。
    parser.add_argument("--bridge-host", dest="bridge_host", default="127.0.0.1", help="HTTP command bridge 监听地址，默认 127.0.0.1。")  # 新增代码+CoreConfig: 添加 bridge host 参数；如果没有这行代码，用户无法显式保持本机绑定。
    parser.add_argument("--bridge-port", dest="bridge_port", default=8765, type=int, help="HTTP command bridge 监听端口，默认 8765。")  # 新增代码+CoreConfig: 添加 bridge port 参数；如果没有这行代码，外部控制器不知道连接哪个端口。
    parser.add_argument("--bridge-token", dest="bridge_token", default=os.environ.get("LEARNING_AGENT_BRIDGE_TOKEN", ""), help="HTTP bridge 可选 token；设置后 POST 请求必须带 Bearer token。")  # 新增代码+CoreConfig: 添加 bridge token 参数并支持环境变量；如果没有这行代码，bridge 无法加简单认证。
    namespace = parser.parse_args(raw_args)  # 新增代码+CoreConfig: 执行 argparse 解析；如果没有这行代码，raw_args 不会变成结构化参数。
    max_turns_is_set = any(arg == "--max-turns" or arg.startswith("--max-turns=") for arg in raw_args)  # 新增代码+CoreConfig: 记录用户是否显式传入轮次参数；如果没有这行代码，--max-turns none 无法覆盖配置文件数字。
    command = str(namespace.command).strip().lower()  # 新增代码+CoreConfig: 规范化命令名；如果没有这行代码，Run/BRIDGE 等大小写输入会造成分支不稳定。
    prompt = str(namespace.prompt or "")  # 新增代码+CoreConfig: 统一 prompt 为字符串；如果没有这行代码，None 值可能进入 agent.run。
    if not command and prompt:  # 新增代码+CoreConfig: 用户只传 --prompt 时自动视为一次性 run；如果没有这行代码，非交互式调用会误入聊天循环。
        command = "run"  # 新增代码+CoreConfig: 设置隐式 run 命令；如果没有这行代码，main 无法进入一次性输出路径。
    return MainArgs(command=command, max_turns=namespace.max_turns, max_turns_is_set=max_turns_is_set, prompt=prompt, output_json=bool(namespace.output_json), bridge_host=str(namespace.bridge_host), bridge_port=int(namespace.bridge_port), bridge_token=str(namespace.bridge_token or ""))  # 新增代码+CoreConfig: 返回结构化 CLI 参数；如果没有这行代码，main 拿不到新增接口配置。


def load_agent_runtime_config(workspace: str | Path) -> AgentRuntimeConfig:  # 新增代码+CoreConfig: 从工作区配置文件和环境变量加载运行策略；如果没有这行代码，max_turns 只能靠代码传入。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+CoreConfig: 规范化工作区路径；如果没有这行代码，相对路径下可能找错 runtime_config.json。
    config_path = workspace_path / "runtime_config.json"  # 新增代码+CoreConfig: 约定运行配置文件名；如果没有这行代码，用户不知道在哪里配置 max_turns。
    max_turns: int | None = None  # 新增代码+CoreConfig: 默认主 Agent 不按固定轮次主动停止；如果没有这行代码，容易重新引入硬编码默认值。
    prompt_soft_token_limit = DEFAULT_PROMPT_SOFT_TOKEN_LIMIT  # 新增代码+CoreConfig: 默认使用生产 prompt 软预算；如果没有这行代码，配置缺字段时没有稳定默认值。
    if config_path.exists():  # 新增代码+CoreConfig: 只有配置文件存在时才读取；如果没有这行代码，缺省启动会因为找不到文件报错。
        try:  # 新增代码+CoreConfig: 捕获 JSON 读取和解析错误；如果没有这行代码，配置写错时错误信息不够聚焦。
            payload = json.loads(config_path.read_text(encoding="utf-8"))  # 新增代码+CoreConfig: 读取 UTF-8 JSON 配置；如果没有这行代码，配置文件不会影响运行策略。
        except (OSError, json.JSONDecodeError) as error:  # 新增代码+CoreConfig: 处理文件不可读或 JSON 格式错误；如果没有这行代码，用户会看到底层异常。
            raise ValueError(f"{config_path} 读取失败或 JSON 格式错误：{error}") from error  # 新增代码+CoreConfig: 抛出带路径的可读错误；如果没有这行代码，用户不知道哪个文件出错。
        if not isinstance(payload, dict):  # 新增代码+CoreConfig: 顶层必须是对象；如果没有这行代码，数组或字符串配置会让字段读取语义不清。
            raise ValueError(f"{config_path} 顶层必须是 JSON 对象。")  # 新增代码+CoreConfig: 给出配置结构错误；如果没有这行代码，错误原因不明确。
        if "max_turns" in payload:  # 新增代码+CoreConfig: 只在配置显式提供时解析；如果没有这行代码，缺字段会被误当错误。
            max_turns = parse_max_turns_value(payload.get("max_turns"), f"{config_path} 的 max_turns")  # 新增代码+CoreConfig: 解析文件中的 max_turns；如果没有这行代码，配置文件数字/null 都不会生效。
        if "prompt_soft_token_limit" in payload:  # 新增代码+CoreConfig: 只在配置显式提供时解析 prompt 软预算；如果没有这行代码，用户无法从 runtime_config.json 调整 compact 阈值。
            prompt_soft_token_limit = parse_prompt_soft_token_limit_value(payload.get("prompt_soft_token_limit"), f"{config_path} 的 prompt_soft_token_limit")  # 新增代码+CoreConfig: 解析文件里的 prompt 预算；如果没有这行代码，配置值不会进入运行时。
    env_max_turns = os.environ.get("LEARNING_AGENT_MAX_TURNS")  # 新增代码+CoreConfig: 读取环境变量覆盖值；如果没有这行代码，用户无法临时调整双击启动等入口的轮次策略。
    if env_max_turns is not None:  # 新增代码+CoreConfig: 只有设置环境变量时才覆盖文件值；如果没有这行代码，缺省环境会覆盖成 None。
        max_turns = parse_max_turns_value(env_max_turns, "LEARNING_AGENT_MAX_TURNS")  # 新增代码+CoreConfig: 解析环境变量；如果没有这行代码，字符串数字或 none 无法转换成运行策略。
    env_prompt_soft_token_limit = os.environ.get("LEARNING_AGENT_PROMPT_SOFT_TOKEN_LIMIT")  # 新增代码+CoreConfig: 读取 prompt 软预算环境变量覆盖值；如果没有这行代码，临时调试 compact 阈值需要改文件。
    if env_prompt_soft_token_limit is not None:  # 新增代码+CoreConfig: 只有设置环境变量时才覆盖文件预算；如果没有这行代码，未设置环境变量也可能误覆盖默认值。
        prompt_soft_token_limit = parse_prompt_soft_token_limit_value(env_prompt_soft_token_limit, "LEARNING_AGENT_PROMPT_SOFT_TOKEN_LIMIT")  # 新增代码+CoreConfig: 解析环境变量预算；如果没有这行代码，字符串预算无法进入装配器。
    return AgentRuntimeConfig(max_turns=max_turns, prompt_soft_token_limit=prompt_soft_token_limit)  # 新增代码+CoreConfig: 返回轮次策略和 prompt 软预算；如果没有这行代码，main 无法把预算传给 LearningAgent。


def resolve_run_max_turns(runtime_config: AgentRuntimeConfig, main_args: MainArgs) -> int | None:  # 新增代码+CoreConfig: 决定最终传给 agent.run 的轮次策略；如果没有这行代码，优先级会散落在 main 里。
    if main_args.max_turns_is_set:  # 新增代码+CoreConfig: CLI 显式传参优先级最高；如果没有这行代码，用户临时命令不能覆盖配置文件。
        return main_args.max_turns  # 新增代码+CoreConfig: 返回 CLI 指定的数字或 None；如果没有这行代码，--max-turns none 无法取消配置文件上限。
    return runtime_config.max_turns  # 新增代码+CoreConfig: 没有 CLI 覆盖时使用配置文件或环境变量结果；如果没有这行代码，配置层不会影响运行。


def format_max_turns_status(max_turns: int | None) -> str:  # 新增代码+CoreConfig: 把轮次策略转成人可读启动提示；如果没有这行代码，用户启动时不知道当前是否有限制。
    if max_turns is None:  # 新增代码+CoreConfig: None 表示不按固定轮次主动停止；如果没有这行代码，无限策略会被显示成空值。
        return "不按固定轮次主动停止"  # 新增代码+CoreConfig: 返回清楚中文说明；如果没有这行代码，用户不易理解 None 的含义。
    return f"最多 {max_turns} 轮模型-工具循环"  # 新增代码+CoreConfig: 返回数字上限说明；如果没有这行代码，用户无法确认配置是否生效。
