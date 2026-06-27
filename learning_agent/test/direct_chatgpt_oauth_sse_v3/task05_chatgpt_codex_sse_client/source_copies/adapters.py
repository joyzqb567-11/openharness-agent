"""真实模型适配器实现。"""  # 新增代码+ModelsSplit: 这个文件承载 OpenAI、Codex CLI 和 Codex OAuth 模型实现；若没有这个文件，主入口仍会过大。

from __future__ import annotations  # 新增代码+ModelsSplit: 延迟解析类型注解；若没有这行代码，跨模块类型引用更容易受定义顺序影响。

import base64  # 新增代码+ModelsSplit: OAuth PKCE/JWT 解析需要 base64url 编解码；若没有这行代码，OAuth token 解析会失败。
import copy  # 新增代码+ModelsSplit: strict schema 构造会深拷贝参数 schema；若没有这行代码，输出协议可能污染原始工具定义。
import hashlib  # 新增代码+ModelsSplit: OAuth PKCE 需要 SHA-256 生成 code_challenge；若没有这行代码，网页登录授权无法完成。
import http.server  # 新增代码+ModelsSplit: OAuth 登录需要本地回调 HTTP 服务接收授权码；若没有这行代码，首次登录无法拿到 code。
import json  # 新增代码+ModelsSplit: 模型请求体、输出协议和 OAuth 响应都需要 JSON；若没有这行代码，模型适配器无法解析结构化数据。
import os  # 新增代码+ModelsSplit: 模型适配器需要读取环境变量和默认 token 路径；若没有这行代码，运行配置无法生效。
import secrets  # 新增代码+ModelsSplit: OAuth state 和 PKCE verifier 需要安全随机数；若没有这行代码，登录流程安全性不足。
import subprocess  # 新增代码+ModelsSplit: Codex CLI 模型需要启动 codex exec 子进程；若没有这行代码，CLI 桥接模型不可用。
import tempfile  # 新增代码+ModelsSplit: Codex CLI 模型需要临时输出 schema 和最终消息文件；若没有这行代码，结构化输出无法稳定落盘。
import time  # 新增代码+ModelsSplit: OAuth token 过期判断需要当前时间；若没有这行代码，刷新逻辑无法工作。
import urllib.error  # 新增代码+ModelsSplit: OAuth/API 请求需要区分 HTTPError、URLError 和超时；若没有这行代码，错误提示会变粗糙。
import urllib.parse  # 新增代码+ModelsSplit: OAuth URL 和表单请求体需要安全编码；若没有这行代码，授权参数可能拼错。
import urllib.request  # 新增代码+ModelsSplit: OAuth/API 直连使用标准库发送 HTTP 请求；若没有这行代码，模型无法调用远端 API。
import webbrowser  # 新增代码+ModelsSplit: 首次 OAuth 登录需要打开系统浏览器；若没有这行代码，用户无法完成网页登录。
from dataclasses import dataclass  # 新增代码+ModelsSplit: OAuth token 数据对象使用 dataclass；若没有这行代码，需要手写重复初始化逻辑。
from pathlib import Path  # 新增代码+ModelsSplit: Codex CLI cwd 和 token 文件路径需要跨平台路径对象；若没有这行代码，路径处理会更脆弱。
from typing import Any, Callable  # 新增代码+ModelsSplit: 模型适配器需要通用 JSON 类型和可注入回调类型；若没有这行代码，类型契约不清楚。

try:  # 新增代码+ModelsSplit: 包运行模式下从 core.messages 读取统一消息结构；若没有这行代码，模型适配器会重新定义消息对象。
    from learning_agent.core.messages import ModelMessage, ToolCall  # 新增代码+ModelsSplit: 导入模型输出和工具调用数据对象；若没有这行代码，模型无法返回统一协议。
except ModuleNotFoundError as error:  # 新增代码+ModelsSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.messages"}:  # 新增代码+ModelsSplit: 只允许路径缺失时 fallback；若没有这行代码，core 内部真实错误会被误吞。
        raise  # 新增代码+ModelsSplit: 重新抛出真实导入错误；若没有这行代码，排查模型适配器问题会很困难。
    from core.messages import ModelMessage, ToolCall  # 新增代码+ModelsSplit: 脚本运行模式下从同目录 core 包导入消息对象；若没有这行代码，直接执行 learning_agent.py 会找不到消息类型。

try:  # 新增代码+ToolSchemaSplit: 包运行模式下从独立 schema 模块读取默认工具清单；若没有这行代码，模型输出协议仍会依赖旧入口。
    from learning_agent.tools.schemas import TOOL_SCHEMAS as DEFAULT_TOOL_SCHEMAS  # 新增代码+ToolSchemaSplit: 导入默认内置工具 schema；若没有这行代码，_output_schema() 没有兜底工具分支。
except ModuleNotFoundError as error:  # 新增代码+ToolSchemaSplit: 捕获直接脚本运行时包路径不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.schemas"}:  # 新增代码+ToolSchemaSplit: 只允许目标路径缺失时 fallback；若没有这行代码，schema 内部真实 bug 会被误吞。
        raise  # 新增代码+ToolSchemaSplit: 重新抛出真实导入错误；若没有这行代码，模型 schema 问题会被隐藏。
    from tools.schemas import TOOL_SCHEMAS as DEFAULT_TOOL_SCHEMAS  # 新增代码+ToolSchemaSplit: 脚本模式下读取同目录 schema 模块；若没有这行代码，直接运行时 _output_schema() 没有工具定义。

try:  # 新增代码+OAuthNativeCodexBody: 包运行模式下导入 Responses 原生工具协议助手；如果没有这一行，OAuth 适配器只能继续走旧 JSON prompt 协议。
    from learning_agent.models.responses_native import build_hosted_tool_search_tools_by_namespace  # 新增代码+OAuthNativeCodexBody: 导入 namespace/tool_search 构造器；如果没有这一行，顶层 tools 无法按 ClaudeCode 风格生成。
    from learning_agent.models.responses_native import default_responses_namespace_descriptions  # 新增代码+OAuthNativeCodexBody: 导入默认 namespace 说明；如果没有这一行，模型看到的工具分组缺少语义说明。
    from learning_agent.models.responses_native import default_responses_namespace_for_tool_name  # 新增代码+OAuthNativeCodexBody: 导入按工具名分组规则；如果没有这一行，Computer Use 工具无法稳定进入 computer_use namespace。
    from learning_agent.models.responses_native import parse_responses_output_items_to_model_message  # 新增代码+OAuthNativeOutputParser: 导入原生 output item 解析器；如果没有这一行，function_call 无法进入现有工具执行器。
except ModuleNotFoundError as error:  # 新增代码+OAuthNativeCodexBody: 兼容 start_oauth_agent.bat 直接脚本模式；如果没有这一行，包名前缀缺失时会启动失败。
    if error.name not in {"learning_agent", "learning_agent.models", "learning_agent.models.responses_native"}:  # 新增代码+OAuthNativeCodexBody: 只对目标包路径缺失启用 fallback；如果没有这一行，responses_native 内部真实错误会被误吞。
        raise  # 新增代码+OAuthNativeCodexBody: 重新抛出真实导入错误；如果没有这一行，协议层 bug 会变成难查的空能力。
    from models.responses_native import build_hosted_tool_search_tools_by_namespace  # 新增代码+OAuthNativeCodexBody: 脚本模式下导入 namespace/tool_search 构造器；如果没有这一行，bat 入口无法生成 native tools。
    from models.responses_native import default_responses_namespace_descriptions  # 新增代码+OAuthNativeCodexBody: 脚本模式下导入 namespace 说明；如果没有这一行，bat 入口 native tools 缺少描述。
    from models.responses_native import default_responses_namespace_for_tool_name  # 新增代码+OAuthNativeCodexBody: 脚本模式下导入工具分组规则；如果没有这一行，bat 入口 Computer Use 分组会失败。
    from models.responses_native import parse_responses_output_items_to_model_message  # 新增代码+OAuthNativeOutputParser: 脚本模式下导入 output item 解析器；如果没有这一行，bat 入口无法消费 function_call。

try:  # 新增代码+DirectChatGptSseClient: 包运行模式下导入共享 ChatGPT Codex SSE 客户端；如果没有这行代码，旧 OAuth wrapper 会继续维护独立 endpoint/parser。
    from learning_agent.models.chatgpt_codex_sse import CHATGPT_CODEX_RESPONSES_ENDPOINT  # 新增代码+DirectChatGptSseClient: 导入唯一 Codex responses 端点常量；如果没有这行代码，旧 wrapper 和 GUI 直连端点可能漂移。
    from learning_agent.models.chatgpt_codex_sse import ChatGptCodexSseClient  # 新增代码+DirectChatGptSseClient: 导入共享 SSE parser；如果没有这行代码，旧 wrapper 无法委托新客户端。
except ModuleNotFoundError as error:  # 新增代码+DirectChatGptSseClient: 兼容 start_oauth_agent.bat 直接脚本模式；如果没有这行代码，包名前缀缺失时会启动失败。
    if error.name not in {"learning_agent", "learning_agent.models", "learning_agent.models.chatgpt_codex_sse"}:  # 新增代码+DirectChatGptSseClient: 只对目标包路径缺失启用 fallback；如果没有这行代码，客户端内部真实错误会被误吞。
        raise  # 新增代码+DirectChatGptSseClient: 重新抛出真实导入错误；如果没有这行代码，Direct SSE bug 会被隐藏。
    from models.chatgpt_codex_sse import CHATGPT_CODEX_RESPONSES_ENDPOINT  # 新增代码+DirectChatGptSseClient: 脚本模式下导入唯一端点常量；如果没有这行代码，bat 入口旧 wrapper 端点不会收敛。
    from models.chatgpt_codex_sse import ChatGptCodexSseClient  # 新增代码+DirectChatGptSseClient: 脚本模式下导入共享 SSE parser；如果没有这行代码，bat 入口旧 wrapper 仍会分叉。



class OpenAIChatModel:  # 作用: 使用官方 OpenAI-compatible API key 的真实模型适配器
    def __init__(self, model: str, api_key: str, base_url: str | None = None) -> None:  # 作用: 保存模型名、API key 和可选兼容接口地址
        self._model = model  # 作用: 保存真实模型名
        self._api_key = api_key  # 作用: 保存 API key，后续交给 OpenAI SDK
        self._base_url = base_url  # 作用: 保存可选 base_url，用于 OpenRouter/Ollama 等兼容接口

    @classmethod  # 作用: 允许通过类名从环境变量构造模型
    def from_env(cls) -> "OpenAIChatModel":  # 作用: 读取 OPENAI_API_KEY/OPENAI_MODEL/OPENAI_BASE_URL
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()  # 作用: 从环境变量读取 API key
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"  # 作用: 读取模型名，缺省用轻量模型
        base_url = os.environ.get("OPENAI_BASE_URL", "").strip() or None  # 作用: 读取可选兼容接口地址
        return cls(model=model, api_key=api_key, base_url=base_url)  # 作用: 返回配置好的 OpenAIChatModel

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelMessage:  # 作用: 调用 OpenAI SDK 并解析工具调用
        if not self._api_key:  # 作用: 如果用户没有配置 API key
            return ModelMessage(text="OpenAI API 调用失败：缺少 OPENAI_API_KEY。")  # 作用: 返回可读错误，避免程序崩溃
        try:  # 作用: 捕获 SDK 导入和请求异常
            from openai import OpenAI  # type: ignore  # 作用: 延迟导入 OpenAI SDK，让假模型测试不依赖这个包

            client = OpenAI(api_key=self._api_key, base_url=self._base_url)  # 作用: 创建 SDK 客户端
            response = client.chat.completions.create(model=self._model, messages=messages, tools=tools)  # 作用: 调用 Chat Completions 接口
            choice = response.choices[0].message  # 作用: 取第一条模型回复
            tool_calls: list[ToolCall] = []  # 作用: 准备保存解析后的内部工具调用
            for raw_call in choice.tool_calls or []:  # 作用: 遍历 SDK 返回的工具调用
                arguments = json.loads(raw_call.function.arguments or "{}")  # 作用: 把工具参数 JSON 字符串转为 dict
                tool_calls.append(ToolCall(name=raw_call.function.name, arguments=arguments, call_id=raw_call.id))  # 作用: 转换成内部 ToolCall
            return ModelMessage(text=choice.content or "", tool_calls=tool_calls)  # 作用: 返回统一的 ModelMessage
        except Exception as error:  # 作用: 捕获网络、鉴权、解析等异常
            return ModelMessage(text=f"OpenAI API 调用失败：{error}")  # 作用: 把错误返回给用户学习排查


RunCodexFunction = Callable[[list[str], str, Path], subprocess.CompletedProcess[str]]  # 作用: 抽象 codex exec 执行函数，便于测试注入假实现


class CodexCliChatModel:  # 作用: 通过本机 codex exec 调用 Codex/GPT-5.5 的旧桥接模型
    def __init__(  # 作用: 初始化 Codex CLI 桥接模型
        self,  # 作用: 当前对象
        codex_command: str,  # 作用: codex 可执行文件名或绝对路径
        model: str,  # 作用: 目标模型名，例如 gpt-5.5
        cwd: str | Path,  # 作用: codex exec 的工作目录
        run_codex: RunCodexFunction | None = None,  # 作用: 可选子进程函数，测试时替换为假函数
        timeout_seconds: int = 300,  # 作用: 子进程最长等待秒数
    ) -> None:
        self._codex_command = codex_command  # 作用: 保存 codex 命令
        self._model = model  # 作用: 保存模型名
        self._cwd = Path(cwd).expanduser().resolve()  # 作用: 规范化工作目录
        self._run_codex = run_codex or self._run_codex_process  # 作用: 保存执行函数，未注入则使用真实 subprocess
        self._timeout_seconds = timeout_seconds  # 作用: 保存超时时间
        self.last_command: list[str] = []  # 作用: 保存最近一次命令，方便测试和排查

    @classmethod  # 作用: 允许通过类名从环境变量创建桥接模型
    def from_env(cls, cwd: str | Path) -> "CodexCliChatModel":  # 作用: 读取 CODEX_COMMAND/CODEX_MODEL/CODEX_TIMEOUT_SECONDS
        command = os.environ.get("CODEX_COMMAND", "codex").strip() or "codex"  # 作用: 默认使用 PATH 里的 codex
        model = os.environ.get("CODEX_MODEL", "gpt-5.5").strip() or "gpt-5.5"  # 作用: 默认使用用户想测试的 GPT-5.5
        raw_timeout = os.environ.get("CODEX_TIMEOUT_SECONDS", "300").strip()  # 作用: 读取可选超时时间
        try:  # 作用: 捕获用户填错数字的情况
            timeout_seconds = max(int(raw_timeout), 30)  # 作用: 最少等待 30 秒，避免误填太短
        except ValueError:  # 作用: 如果环境变量不是整数
            timeout_seconds = 300  # 作用: 回退到 5 分钟
        return cls(codex_command=command, model=model, cwd=cwd, timeout_seconds=timeout_seconds)  # 作用: 返回配置好的桥接模型

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelMessage:  # 作用: 把 agent messages/tools 包装成 prompt 交给 codex exec
        prompt = self._build_prompt(messages=messages, tools=tools)  # 作用: 构造给 Codex CLI 的模型适配器提示词
        with tempfile.TemporaryDirectory(prefix="learning_agent_codex_") as raw_dir:  # 作用: 创建临时目录保存 schema 和输出文件
            temp_dir = Path(raw_dir)  # 作用: 把临时目录字符串转成 Path
            schema_path = temp_dir / "output_schema.json"  # 作用: 定义输出 schema 文件路径
            output_path = temp_dir / "last_message.json"  # 作用: 定义 codex 最终消息输出路径
            schema_path.write_text(json.dumps(self._output_schema(tools=tools), ensure_ascii=False, indent=2), encoding="utf-8")  # 修改代码+MCP参数适配: 根据当前工具列表生成严格 JSON schema；若省略 tools: MCP 的 query/url 等动态参数无法出现在模型输出格式里
            command = self._build_command(schema_path=schema_path, output_path=output_path)  # 作用: 构造 codex exec 命令数组
            self.last_command = command  # 作用: 记录命令，便于测试确认参数
            try:  # 作用: 捕获 codex 执行失败或超时
                result = self._run_codex(command, prompt, output_path)  # 作用: 执行 codex exec 并等待返回
            except Exception as error:  # 作用: 捕获 FileNotFoundError、TimeoutExpired 等异常
                return ModelMessage(text=f"Codex CLI 调用失败：{error}")  # 作用: 返回可读错误
            if result.returncode != 0:  # 作用: 如果 codex 子进程返回失败
                detail = (result.stderr or result.stdout or "").strip()  # 作用: 优先展示 stderr，没有则展示 stdout
                return ModelMessage(text=f"Codex CLI 调用失败：{detail}")  # 作用: 返回失败原因给用户
            raw_output = self._read_codex_output(output_path=output_path, fallback_stdout=result.stdout)  # 作用: 读取 codex 输出的最终 JSON
            model_message = self._parse_model_message(raw_output)  # 新增代码+模型JSON恢复: 先解析第一次模型输出；若没有这行代码，后续无法判断是否需要修复重试。
            if self._is_parse_error_message(model_message):  # 新增代码+模型JSON恢复: 识别模型输出不是合法 JSON 的情况；若没有这行代码，主循环会把格式错误当最终答案。
                repair_messages = self._messages_with_json_repair_prompt(messages)  # 新增代码+模型JSON恢复: 给同一个任务追加一次“只修输出格式”的请求；若没有这行代码，重试模型不知道要纠正什么。
                repair_prompt = self._build_prompt(messages=repair_messages, tools=tools)  # 新增代码+模型JSON恢复: 重新构造包含原任务和修复提示的 prompt；若没有这行代码，重试不会带上完整上下文。
                try:  # 新增代码+模型JSON恢复: 捕获修复重试自身的子进程异常；若没有这行代码，修复失败会覆盖原始可诊断错误。
                    repair_result = self._run_codex(command, repair_prompt, output_path)  # 新增代码+模型JSON恢复: 用相同 schema 再请求一次结构化输出；若没有这行代码，偶发 JSON 漂移没有自动恢复机会。
                except Exception:  # 新增代码+模型JSON恢复: 修复请求也抛错时保留第一次错误；若没有这行代码，用户会看到更远离根因的异常。
                    return model_message  # 新增代码+模型JSON恢复: 返回第一次解析错误作为可审计失败；若没有这行代码，函数可能继续处理不存在的修复结果。
                if repair_result.returncode == 0:  # 新增代码+模型JSON恢复: 只有修复子进程成功才读取第二次输出；若没有这行代码，失败输出可能被误当成模型 JSON。
                    repair_raw_output = self._read_codex_output(output_path=output_path, fallback_stdout=repair_result.stdout)  # 新增代码+模型JSON恢复: 读取修复重试输出；若没有这行代码，无法拿到第二次模型结果。
                    repair_message = self._parse_model_message(repair_raw_output)  # 新增代码+模型JSON恢复: 解析修复重试结果；若没有这行代码，第二次输出仍只是字符串。
                    if not self._is_parse_error_message(repair_message):  # 新增代码+模型JSON恢复: 只有第二次真正变成合法协议才采用；若没有这行代码，坏输出可能覆盖更早证据。
                        return repair_message  # 新增代码+模型JSON恢复: 返回修复后的工具调用或最终回答；若没有这行代码，自动恢复即使成功也不会生效。
            return model_message  # 修改代码+模型JSON恢复: 正常输出或修复失败时返回当前最可信消息；若没有这行代码，chat 没有稳定返回值。

    def _build_command(self, schema_path: Path, output_path: Path) -> list[str]:  # 作用: 构造 subprocess.run 可直接使用的 codex exec 参数数组
        return [  # 作用: 返回命令数组，避免 shell 字符串拼接风险
            self._codex_command,  # 作用: 第一个参数是 codex 可执行文件
            "exec",  # 作用: 使用非交互 exec 模式
            "--skip-git-repo-check",  # 作用: 允许在教学目录运行，不因 git 检查阻塞
            "--sandbox",  # 作用: 指定 Codex 自身的沙箱参数名
            "read-only",  # 作用: 让 Codex CLI 自身只读，写文件仍由 learning_agent 工具层确认后执行
            "--model",  # 作用: 指定模型参数名
            self._model,  # 作用: 模型值，通常是 gpt-5.5
            "--output-schema",  # 作用: 要求 codex 最终回答符合 JSON schema
            str(schema_path),  # 作用: 传入 schema 文件绝对路径
            "--output-last-message",  # 作用: 让 codex 把最终回答写入文件，便于稳定解析
            str(output_path),  # 作用: 传入最终回答输出文件路径
            "-",  # 作用: 从 stdin 读取 prompt，避免命令行长度限制
        ]  # 作用: 命令数组结束

    @staticmethod  # 新增代码+模型JSON恢复: 该判断不依赖实例状态，CLI 和 OAuth 两条模型链路都能复用；若没有这行代码，两个入口会重复写易漂移的字符串判断。
    def _is_parse_error_message(message: ModelMessage) -> bool:  # 新增代码+模型JSON恢复: 判断解析器是否已经把坏 JSON 包成错误文本；若没有这行代码，自动重试无法可靠触发。
        return (  # 新增代码+模型JSON恢复: 用多条件返回布尔值；若没有这行代码，调用方需要自己理解错误文本结构。
            not message.tool_calls  # 新增代码+模型JSON恢复: 只有没有工具调用时才视为格式失败；若没有这行代码，合法工具调用可能被误判。
            and message.text.startswith("Codex CLI 返回格式错误")  # 新增代码+模型JSON恢复: 匹配当前解析器给出的固定错误前缀；若没有这行代码，普通最终回答会被误触发重试。
        )  # 新增代码+模型JSON恢复: 结束布尔表达式；若没有这行代码，Python 语法不完整。

    @staticmethod  # 新增代码+模型JSON恢复: 构造修复消息不需要实例状态，OAuth 模型也可以复用；若没有这行代码，OAuth 路径只能复制一份修复提示。
    def _messages_with_json_repair_prompt(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:  # 新增代码+模型JSON恢复: 为同一任务追加一次协议修复请求；若没有这行代码，重试请求可能丢失原始用户目标。
        repair_messages = copy.deepcopy(messages)  # 新增代码+模型JSON恢复: 深拷贝原消息避免污染真实会话历史；若没有这行代码，修复提示会永久写回上层 messages。
        repair_messages.append(  # 新增代码+模型JSON恢复: 追加一条只面向模型适配器的修复请求；若没有这行代码，第二次模型调用不知道第一次失败原因。
            {  # 新增代码+模型JSON恢复: 使用普通 user 消息承载修复要求；若没有这行代码，Responses input 缺少合法消息对象。
                "role": "user",  # 新增代码+模型JSON恢复: 继续使用 user role 让模型按任务输入处理；若没有这行代码，消息格式不符合现有 prompt 构造。
                "content": "上一轮模型输出不是合法 JSON，工具没有执行。请重新完成同一个下一步决策，只输出一个合法 JSON 对象，根字段只能是 decision_note、text、tool_calls；如果需要工具，请把工具写进 tool_calls；不要解释、不要 Markdown、不要把修复说明写进 text。",  # 新增代码+模型JSON恢复: 明确这是格式修复而不是改变任务；若没有这行代码，模型可能继续输出自我纠错文字导致主循环中断。
            }  # 新增代码+模型JSON恢复: 结束修复消息对象；若没有这行代码，Python 字典语法不完整。
        )  # 新增代码+模型JSON恢复: 结束 append 调用；若没有这行代码，Python 调用语法不完整。
        return repair_messages  # 新增代码+模型JSON恢复: 返回带修复提示的消息副本；若没有这行代码，调用方拿不到重试上下文。

    def _run_codex_process(self, command: list[str], prompt: str, output_path: Path) -> subprocess.CompletedProcess[str]:  # 作用: 真实执行 codex exec 的默认函数
        del output_path  # 作用: 真实 codex 会自己写输出文件，这个参数只给测试假函数使用
        return subprocess.run(  # 作用: 启动子进程并等待完成
            command,  # 作用: 使用数组参数，避免通过 shell 解释命令
            input=prompt,  # 作用: 把完整提示词写入 stdin
            text=True,  # 作用: 使用文本模式收发 stdin/stdout/stderr
            encoding="utf-8",  # 作用: 指定 UTF-8，保证中文提示词不乱码
            errors="replace",  # 作用: 坏字符用替换符处理，避免解码异常
            stdout=subprocess.PIPE,  # 作用: 捕获 stdout，便于失败排查
            stderr=subprocess.PIPE,  # 作用: 捕获 stderr，便于失败排查
            cwd=self._cwd,  # 作用: 指定工作目录
            timeout=self._timeout_seconds,  # 作用: 限制最长等待时间
        )  # 作用: subprocess.run 调用结束

    def _build_prompt(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> str:  # 作用: 构造给 Codex CLI 的“模型适配器”提示词
        return (  # 作用: 返回完整提示词字符串
            "你是 learning_agent 的模型适配器，不是文件执行器。\n"  # 作用: 明确 Codex CLI 只负责模型推理
            "你必须根据 messages 和 tools 判断下一步应该直接回答，还是请求 learning_agent 调用工具。\n"  # 作用: 告诉模型要做工具选择
            "你必须在 decision_note 里用一句话说明本轮为什么直接回答或为什么选择这些工具；这只是给用户看的决策说明，不要写隐藏思维链。\n"  # 新增代码: 要求模型输出可学习的决策说明，但不要求暴露内部思维链
            "如果用户明确要求使用工具、真实 Chrome、桌面可见浏览器、当前浏览器或登录态，你不能用普通回答、web_search、fetch_url 或独立 Chromium 替代；必须请求对应工作流工具。\n"  # 修改代码+真实浏览器误判: 只把真实 Chrome/桌面可见/当前浏览器/登录态视为高风险真实 profile 请求；若没有这行代码，普通 real browser automation 测试会被误导到 real_chrome workflow
            "如果需要工具，请只在 tool_calls 里写工具名和参数，不要自己执行工具。\n"  # 作用: 防止模型绕过 Python 工具层
            "每个 tool_calls 条目的 arguments 只能包含该 name 对应工具 JSON schema 里的参数，不要写其他工具的参数。\n"  # 修改代码+OutputProtocolV2: 要求模型按工具名使用专属参数；若没有这行代码，模型仍会按旧共享 arguments 思路把无关参数写成 null 或混入当前工具
            "如果不需要工具，请把最终回答写入 text，并让 tool_calls 为空数组。\n"  # 作用: 规定直接回答格式
            "当你决定直接回答时，text 必须完整满足最后一条用户消息提出的所有输出要求，包括指定标题、来源、攻略、备选方案或格式约束，不要只回答其中一部分。\n"  # 新增代码+最终答案完整性: 明确最终 text 要完整覆盖用户要求；若没有这行代码，天气加攻略这类复合任务可能只返回天气
            "你只能输出一个 JSON 对象，根字段只能包含 decision_note、text、tool_calls；JSON 对象外不能输出 Markdown、解释文字或代码块，但 text 字段内可以使用用户要求的 Markdown 格式。\n\n"  # 修改代码+最终答案完整性: 区分 JSON 外层限制和 text 内部格式；若没有这行代码，模型可能误以为不能在最终回答里使用用户要求的 Markdown 标题
            f"目标模型名：{json.dumps(self._model, ensure_ascii=False)}\n\n"  # 作用: 把模型名放进 prompt，便于排查
            "可用工具 JSON schema：\n"  # 作用: 以下区域展示工具定义
            f"{json.dumps(tools, ensure_ascii=False, indent=2)}\n\n"  # 作用: 把工具 schema 序列化给模型阅读
            "当前对话 messages：\n"  # 作用: 以下区域展示当前对话历史
            f"{json.dumps(messages, ensure_ascii=False, indent=2)}\n"  # 作用: 把 messages 序列化给模型阅读
        )  # 作用: prompt 拼接结束

    @classmethod  # 修改代码+OutputProtocolV2: 输出 schema 需要按工具名生成 arguments 分支；若仍只汇总参数: 同一工具池内不同工具参数会继续串味
    def _output_schema(cls, tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:  # 修改代码+OutputProtocolV2: 根据当前工具池定义结构化输出 schema；若省略 tools 参数: 默认内置工具仍要有专属分支
        tool_call_item_schema = cls._output_tool_call_item_schema(tools)  # 新增代码+OutputProtocolV2: 为 tool_calls 数组元素生成 per-tool anyOf 分支；若没有这行代码，arguments 会继续共享一个大对象
        return {  # 作用: 返回 schema 根对象
            "type": "object",  # 作用: 最终输出必须是对象
            "properties": {  # 作用: 声明允许出现的根字段
                "decision_note": {"type": "string"},  # 新增代码: decision_note 保存给用户看的简短决策说明，帮助理解模型为什么这么做
                "text": {"type": "string"},  # 作用: text 保存最终自然语言回答
                "tool_calls": {  # 作用: tool_calls 保存模型请求的工具调用
                    "type": "array",  # 作用: tool_calls 必须是数组
                    "items": tool_call_item_schema,  # 修改代码+OutputProtocolV2: 使用按工具名分支的 item schema；若没有这行代码，模型仍会看到共享 arguments 参数池
                },  # 作用: tool_calls 字段结束
            },  # 作用: 根 properties 结束
            "required": ["decision_note", "text", "tool_calls"],  # 修改代码: 根对象必须包含 decision_note、text 和 tool_calls，保证日志总能展示决策说明
            "additionalProperties": False,  # 作用: 禁止根对象额外字段
        }  # 作用: schema 根对象结束

    @classmethod  # 新增代码+OutputProtocolV2: tool_call item schema 需要复用当前工具池；若没有这行代码，_output_schema 会继续把所有工具参数混在一个对象里
    def _output_tool_call_item_schema(cls, tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:  # 新增代码+OutputProtocolV2: 生成 tool_calls 数组元素的 anyOf 分支 schema；若没有这行代码，无法按工具名约束 arguments
        if tools is None:  # 修改代码+ToolSchemaSplit: 未传工具池时使用独立 schema 模块的默认内置工具清单；若没有这行代码，旧 _output_schema() 调用会没有工具。
            selected_tools = DEFAULT_TOOL_SCHEMAS  # 修改代码+ToolSchemaSplit: 从新事实源读取默认工具 schema；若没有这行代码，模型输出协议会重新依赖 learning_agent.py。
        else:  # 修改代码+ModelsSplit: 调用方显式传入工具池时直接使用；若没有这行代码，动态 MCP 工具参数会丢失
            selected_tools = tools  # 修改代码+ModelsSplit: 保持传入工具池优先；若没有这行代码，模型适配器会忽略当前可见工具状态
        branches: list[dict[str, Any]] = []  # 新增代码+OutputProtocolV2: 准备保存每个工具自己的调用分支；若没有这行代码，无法累积 anyOf 列表
        for tool_schema in selected_tools:  # 新增代码+OutputProtocolV2: 遍历当前工具池的每个工具 schema；若没有这行代码，schema 不会包含任何工具分支
            branch = cls._output_tool_call_branch_schema(tool_schema)  # 新增代码+OutputProtocolV2: 把单个工具 schema 转成专属 tool_call 分支；若没有这行代码，工具名和参数约束无法绑定
            if branch is not None:  # 新增代码+OutputProtocolV2: 只保留成功生成的合法分支；若没有这行代码，坏工具 schema 可能把 None 放入 anyOf
                branches.append(branch)  # 新增代码+OutputProtocolV2: 保存当前工具分支；若没有这行代码，模型看不到该工具的输出协议
        if not branches:  # 新增代码+OutputProtocolV2: 处理极端情况下没有任何合法工具的场景；若没有这行代码，anyOf 空列表会形成无效 schema
            branches.append(cls._empty_tool_call_branch_schema())  # 新增代码+OutputProtocolV2: 增加一个不可实际路由的空兜底分支；若没有这行代码，结构化输出后端可能拒绝空 anyOf
        return {"anyOf": branches}  # 新增代码+OutputProtocolV2: 返回 anyOf 分支作为 tool_calls item schema；若没有这行代码，调用方拿不到 per-tool 输出协议

    @classmethod  # 新增代码+OutputProtocolV2: 单工具分支构造需要复用严格 arguments schema helper；若没有这行代码，分支生成逻辑会堆在 _output_schema 里
    def _output_tool_call_branch_schema(cls, tool_schema: dict[str, Any]) -> dict[str, Any] | None:  # 新增代码+OutputProtocolV2: 把一个 OpenAI-compatible 工具 schema 转成工具专属调用分支；若没有这行代码，name 和 arguments 不能绑定
        function_schema = tool_schema.get("function", {}) if isinstance(tool_schema, dict) else {}  # 新增代码+OutputProtocolV2: 安全读取 function 层；若没有这行代码，畸形工具 schema 会触发异常
        if not isinstance(function_schema, dict):  # 新增代码+OutputProtocolV2: 防御 function 不是字典；若没有这行代码，后续读取 name/parameters 会崩溃
            return None  # 新增代码+OutputProtocolV2: 跳过坏工具 schema；若没有这行代码，坏工具会污染整个 response_format
        tool_name = str(function_schema.get("name", "") or "").strip()  # 新增代码+OutputProtocolV2: 读取并清理工具名；若没有这行代码，分支无法用 name enum 精确匹配
        if not tool_name:  # 新增代码+OutputProtocolV2: 没有工具名的 schema 不能生成可路由分支；若没有这行代码，模型可能输出空 name
            return None  # 新增代码+OutputProtocolV2: 跳过无名工具；若没有这行代码，执行层会收到不可路由工具调用
        parameters_schema = function_schema.get("parameters", {"type": "object"})  # 新增代码+OutputProtocolV2: 读取该工具自己的参数 schema；若没有这行代码，arguments 约束没有来源
        arguments_schema = cls._strict_tool_arguments_schema(parameters_schema)  # 新增代码+OutputProtocolV2: 把该工具参数转成 strict response_format 可接受形状；若没有这行代码，Codex 后端可能拒绝嵌套 schema
        return {  # 新增代码+OutputProtocolV2: 返回该工具自己的 tool_call 分支；若没有这行代码，anyOf 无法使用该工具
            "type": "object",  # 新增代码+OutputProtocolV2: 分支必须匹配对象形式的 tool_call；若没有这行代码，非对象也可能通过该分支
            "properties": {  # 新增代码+OutputProtocolV2: 声明 tool_call 的固定字段；若没有这行代码，name 和 arguments 没有约束容器
                "name": {"type": "string", "enum": [tool_name]},  # 新增代码+OutputProtocolV2: 用单值 enum 把分支绑定到具体工具名；若没有这行代码，其他工具可能误用该参数分支
                "arguments": arguments_schema,  # 新增代码+OutputProtocolV2: 只允许当前工具自己的参数；若没有这行代码，browser_open 仍可能收到 confirm_real_profile
            },  # 新增代码+OutputProtocolV2: 结束分支 properties；若没有这行代码，Python 字典语法不完整
            "required": ["name", "arguments"],  # 新增代码+OutputProtocolV2: 要求每个工具调用都明确工具名和参数；若没有这行代码，解析层可能收到缺字段对象
            "additionalProperties": False,  # 新增代码+OutputProtocolV2: 禁止 tool_call 级别额外字段；若没有这行代码，arguments_by_tool 等实验字段可能混入 strict 输出
        }  # 新增代码+OutputProtocolV2: 结束工具分支 schema；若没有这行代码，方法无法返回完整结构

    @classmethod  # 新增代码+OutputProtocolV2: 空工具池兜底分支独立出来便于测试和阅读；若没有这行代码，_output_tool_call_item_schema 会包含杂乱兜底字典
    def _empty_tool_call_branch_schema(cls) -> dict[str, Any]:  # 新增代码+OutputProtocolV2: 生成没有工具可用时的安全空分支；若没有这行代码，空工具池会生成非法 anyOf
        return {  # 新增代码+OutputProtocolV2: 返回不可路由但结构合法的分支；若没有这行代码，结构化输出 schema 可能被后端拒绝
            "type": "object",  # 新增代码+OutputProtocolV2: 分支仍要求对象；若没有这行代码，非对象 tool_call 可能通过
            "properties": {  # 新增代码+OutputProtocolV2: 声明兜底字段；若没有这行代码，name/arguments 没有约束容器
                "name": {"type": "string", "enum": ["__no_tools_available__"]},  # 新增代码+OutputProtocolV2: 使用不可执行工具名；若没有这行代码，空工具池可能允许真实工具名
                "arguments": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},  # 新增代码+OutputProtocolV2: 兜底参数为空对象；若没有这行代码，空分支仍可能接受任意参数
            },  # 新增代码+OutputProtocolV2: 结束兜底 properties；若没有这行代码，Python 字典语法不完整
            "required": ["name", "arguments"],  # 新增代码+OutputProtocolV2: 保持 tool_call 字段形状稳定；若没有这行代码，解析层可能收到缺字段调用
            "additionalProperties": False,  # 新增代码+OutputProtocolV2: 禁止兜底分支额外字段；若没有这行代码，空工具池仍可能携带未知数据
        }  # 新增代码+OutputProtocolV2: 结束兜底分支；若没有这行代码，方法没有返回值

    @classmethod  # 新增代码+OutputProtocolV2: 工具参数 strict 化需要区分必填和可选字段；若没有这行代码，per-tool 分支会重复旧共享参数逻辑
    def _strict_tool_arguments_schema(cls, parameters_schema: Any) -> dict[str, Any]:  # 新增代码+OutputProtocolV2: 把单个工具的参数 schema 转成 strict arguments schema；若没有这行代码，工具分支无法保证 Codex strict 兼容
        if not isinstance(parameters_schema, dict):  # 新增代码+OutputProtocolV2: 防御异常参数 schema；若没有这行代码，坏 MCP server 可能让 response_format 构建崩溃
            return {"type": "object", "properties": {}, "required": [], "additionalProperties": False}  # 新增代码+OutputProtocolV2: 坏 schema 降级为空参数对象；若没有这行代码，模型可能输出不受控参数
        raw_properties = parameters_schema.get("properties", {})  # 新增代码+OutputProtocolV2: 读取工具参数字段定义；若没有这行代码，无法为每个参数建立专属约束
        if not isinstance(raw_properties, dict):  # 新增代码+OutputProtocolV2: 开放对象或坏 properties 统一降级为空对象；若没有这行代码，additionalProperties=true 会被 Codex strict 拒绝
            return {"type": "object", "properties": {}, "required": [], "additionalProperties": False}  # 新增代码+OutputProtocolV2: 返回空参数对象；若没有这行代码，开放参数会继续污染 schema
        raw_required = parameters_schema.get("required", [])  # 新增代码+OutputProtocolV2: 读取原始必填字段列表；若没有这行代码，无法区分必填参数和可选参数
        required_names = {str(name) for name in raw_required} if isinstance(raw_required, list) else set()  # 新增代码+OutputProtocolV2: 规范化必填字段集合；若没有这行代码，可选字段会被错误要求非 null
        cleaned_properties: dict[str, Any] = {}  # 新增代码+OutputProtocolV2: 准备保存 strict 化后的参数字段；若没有这行代码，无法构造 arguments.properties
        for argument_name, argument_schema in raw_properties.items():  # 新增代码+OutputProtocolV2: 遍历该工具自己的每个参数；若没有这行代码，arguments 会缺少工具参数
            clean_name = str(argument_name).strip()  # 新增代码+OutputProtocolV2: 清理参数名；若没有这行代码，空白参数名可能进入模型协议
            if not clean_name:  # 新增代码+OutputProtocolV2: 跳过空参数名；若没有这行代码，模型可能输出无法路由的空键
                continue  # 新增代码+OutputProtocolV2: 继续处理其他参数；若没有这行代码，一个坏参数名会影响全部参数
            if clean_name in required_names:  # 新增代码+OutputProtocolV2: 原始必填参数保持非 null 约束；若没有这行代码，模型可能把必填 path/url 写成 null
                cleaned_properties[clean_name] = cls._strict_response_format_schema(copy.deepcopy(argument_schema) if isinstance(argument_schema, dict) else {})  # 新增代码+OutputProtocolV2: strict 化必填参数 schema；若没有这行代码，嵌套必填规则可能被 Codex 后端拒绝
            else:  # 新增代码+OutputProtocolV2: 原始可选参数需要允许 null 以满足 strict required-all 规则；若没有这行代码，可选 max_chars/new_tab 等字段会被强制非空
                cleaned_properties[clean_name] = cls._nullable_argument_schema(argument_schema)  # 新增代码+OutputProtocolV2: strict 化并补 null 给可选参数；若没有这行代码，可选参数缺省会破坏 strict 输出
        return {"type": "object", "properties": cleaned_properties, "required": list(cleaned_properties.keys()), "additionalProperties": False}  # 新增代码+OutputProtocolV2: 返回该工具专属 arguments schema；若没有这行代码，工具分支无法禁止其他工具参数

    @classmethod  # 新增代码+MCP参数适配: 参数收集逻辑需要被 CLI 和 OAuth 输出 schema 共同复用；若省略: 两条模型链路容易再次不一致
    def _output_argument_properties(cls, tools: list[dict[str, Any]] | None) -> dict[str, Any]:  # 新增代码+MCP参数适配: 从工具 schema 汇总模型允许输出的参数字段；若省略: MCP 参数名只能靠手工维护
        properties: dict[str, Any] = {  # 新增代码+MCP参数适配: 先保留三个内置工具参数，保证旧 read/write/memory 行为兼容；若省略: 旧内置工具可能无法继续输出参数
            "path": {"type": ["string", "null"]},  # 新增代码+MCP参数适配: path 用于 read_file/write_file；若省略: 文件工具会缺少路径参数输出位置
            "content": {"type": ["string", "null"]},  # 新增代码+MCP参数适配: content 用于 write_file；若省略: 写文件工具会缺少内容参数输出位置
            "text": {"type": ["string", "null"]},  # 新增代码+MCP参数适配: text 用于 append_memory 以及部分旧测试工具；若省略: 记忆工具会缺少文本参数输出位置
        }  # 新增代码+MCP参数适配: 内置参数初始化结束；若省略: 字典语法不完整
        for tool_schema in tools or []:  # 新增代码+MCP参数适配: 遍历当前模型可见的所有工具 schema；若省略: 动态 MCP 工具参数不会被收集
            function_schema = tool_schema.get("function", {}) if isinstance(tool_schema, dict) else {}  # 新增代码+MCP参数适配: 读取 OpenAI-compatible function 字段；若省略: 非标准工具项可能导致崩溃
            if not isinstance(function_schema, dict):  # 新增代码+MCP参数适配: 跳过畸形 function 字段；若省略: 后续 .get 可能在非字典上失败
                continue  # 新增代码+MCP参数适配: 忽略坏工具并继续处理其他工具；若省略: 单个坏 schema 会破坏全部输出 schema
            parameters_schema = function_schema.get("parameters", {})  # 新增代码+MCP参数适配: 读取工具参数 JSON Schema；若省略: 无法找到 query/url 等字段
            if not isinstance(parameters_schema, dict):  # 新增代码+MCP参数适配: 跳过非对象参数 schema；若省略: 异常 MCP server 输出会让适配器崩溃
                continue  # 新增代码+MCP参数适配: 坏参数 schema 不影响其他工具；若省略: 容错能力降低
            raw_properties = parameters_schema.get("properties", {})  # 新增代码+MCP参数适配: 读取参数字段定义；若省略: 无法枚举动态参数名
            if not isinstance(raw_properties, dict):  # 新增代码+MCP参数适配: 只接受对象形式 properties；若省略: list/null 等错误结构会导致遍历异常
                continue  # 新增代码+MCP参数适配: 跳过坏 properties；若省略: 单个坏工具影响整个模型调用
            for argument_name, argument_schema in raw_properties.items():  # 新增代码+MCP参数适配: 遍历每个动态参数名和它的 schema；若省略: query/url/max_results 不会被加入输出格式
                clean_name = str(argument_name).strip()  # 新增代码+MCP参数适配: 清理参数名两端空白；若省略: 带空白参数名会进入输出 schema
                if clean_name and clean_name not in properties:  # 新增代码+MCP参数适配: 只添加非空且未存在的参数名；若省略: 可能覆盖内置参数或加入空字段
                    properties[clean_name] = cls._nullable_argument_schema(argument_schema)  # 新增代码+MCP参数适配: 把工具参数 schema 改成可填 null 的输出 schema；若省略: 未用参数无法在严格输出中写 null
        return properties  # 新增代码+MCP参数适配: 返回完整参数字段映射；若省略: 调用方拿不到动态 schema

    @classmethod  # 修改代码+StrictSchema: 参数 schema 转换需要复用递归 strict 化 helper；若仍是 staticmethod: 无法调用 cls._strict_response_format_schema
    def _nullable_argument_schema(cls, argument_schema: Any) -> dict[str, Any]:  # 修改代码+StrictSchema: 让每个工具参数既保留原类型、递归满足 strict schema、又允许 null；若省略: Codex 后端会拒绝嵌套对象 schema
        if not isinstance(argument_schema, dict):  # 新增代码+MCP参数适配: 处理异常 MCP schema；若省略: 非字典 schema 会在 copy 或类型读取时出错
            return cls._fallback_nullable_argument_schema()  # 修改代码+StrictSchemaBareObject: 坏 schema 用 strict-safe anyOf 兜底；若没有这行代码，裸 object/array type 会被 OpenAI 拒绝。
        schema = copy.deepcopy(argument_schema)  # 新增代码+MCP参数适配: 复制原始参数 schema，避免修改工具注册表缓存；若省略: 输出 schema 转换会污染 MCP 工具 schema
        schema = cls._strict_response_format_schema(schema)  # 新增代码+StrictSchema: 递归补齐嵌套对象 required；若省略: todos.items 会因 missing id 被 Codex API 拒绝
        raw_type = schema.get("type")  # 新增代码+MCP参数适配: 读取原始 JSON Schema type；若省略: 无法判断如何加入 null
        if isinstance(raw_type, str):  # 新增代码+MCP参数适配: 处理普通单类型参数；若省略: string/integer 等参数不会自动允许 null
            if raw_type in {"object", "array"}:  # 新增代码+StrictSchemaBareObject: object/array 可空要改用 anyOf；若没有这行代码，type=["object","null"] 仍可能触发 strict 后端拒绝。
                return cls._nullable_complex_type_schema(schema, [raw_type, "null"])  # 新增代码+StrictSchemaBareObject: 用合法分支表达 object/array 或 null；若没有这行代码，metadata.type.0 这类错误会回归。
            schema["type"] = raw_type if raw_type == "null" else [raw_type, "null"]  # 新增代码+MCP参数适配: 在原类型外加入 null；若省略: 未用参数不能按严格 schema 写 null
        elif isinstance(raw_type, list):  # 新增代码+MCP参数适配: 处理已经是多类型的参数；若省略: 已有联合类型可能被覆盖
            normalized_types = [type_name for type_name in raw_type if isinstance(type_name, str)]  # 新增代码+StrictSchemaBareObject: 清理 type 数组里的异常项；若没有这行代码，坏 MCP schema 可能把非字符串带进 anyOf。
            if "object" in normalized_types or "array" in normalized_types:  # 新增代码+StrictSchemaBareObject: 识别 strict 后端不喜欢的复杂裸类型；若没有这行代码，submit.type.4 会继续出现。
                return cls._nullable_complex_type_schema(schema, normalized_types)  # 新增代码+StrictSchemaBareObject: 把复杂联合类型转换成合法 anyOf；若没有这行代码，object/array 缺 items 或 additionalProperties 会被拒绝。
            schema["type"] = raw_type if "null" in raw_type else [*raw_type, "null"]  # 新增代码+MCP参数适配: 保留原联合类型并补 null；若省略: 无关工具参数写 null 会失败
        else:  # 新增代码+MCP参数适配: 处理没有 type 的参数 schema；若省略: enum/anyOf 等复杂 schema 可能缺少可空兜底
            return cls._fallback_nullable_argument_schema(schema.get("description"))  # 修改代码+StrictSchemaBareObject: 无 type 参数用 strict-safe anyOf 兜底；若没有这行代码，submit.type.4 会继续触发 HTTP 400。
        return schema  # 新增代码+MCP参数适配: 返回可空后的参数 schema；若省略: 调用方没有可加入 properties 的结果

    @classmethod  # 新增代码+StrictSchemaBareObject: 复杂类型可空转换需要被 object、array 和联合类型共同复用；若没有这行代码，修复逻辑会散在多个分支。
    def _nullable_complex_type_schema(cls, schema: dict[str, Any], raw_types: list[str]) -> dict[str, Any]:  # 新增代码+StrictSchemaBareObject: 把包含 object/array 的 type 联合改成 strict-safe anyOf；若没有这段函数，OpenAI 会继续拒绝裸复杂类型。
        branches: list[dict[str, Any]] = []  # 新增代码+StrictSchemaBareObject: 保存 anyOf 的每个合法分支；若没有这行代码，后续无法逐个添加类型分支。
        seen_types: set[str] = set()  # 新增代码+StrictSchemaBareObject: 记录已处理的类型避免重复分支；若没有这行代码，坏 MCP schema 可能生成重复 anyOf 项。
        for type_name in raw_types:  # 新增代码+StrictSchemaBareObject: 遍历原始 type 联合中的每个类型；若没有这行代码，无法保留原 schema 允许的类型范围。
            if type_name in seen_types:  # 新增代码+StrictSchemaBareObject: 跳过重复类型；若没有这行代码，anyOf 可能出现重复分支增加 schema 噪声。
                continue  # 新增代码+StrictSchemaBareObject: 继续处理下一个类型；若没有这行代码，重复类型会继续向下生成分支。
            seen_types.add(type_name)  # 新增代码+StrictSchemaBareObject: 标记当前类型已经处理；若没有这行代码，去重逻辑无法生效。
            if type_name == "null":  # 新增代码+StrictSchemaBareObject: null 分支用于表达可选参数未使用；若没有这行代码，可选字段无法按 strict required-all 写 null。
                branches.append({"type": "null"})  # 新增代码+StrictSchemaBareObject: 添加 null 分支；若没有这行代码，模型无法输出 null 表示省略可选参数。
            elif type_name == "object":  # 新增代码+StrictSchemaBareObject: object 分支需要完整对象约束；若没有这行代码，对象参数会退化成裸字符串类型。
                object_schema = copy.deepcopy(schema)  # 新增代码+StrictSchemaBareObject: 复制原 schema 给 object 分支使用；若没有这行代码，修改分支会污染调用方 schema。
                object_schema["type"] = "object"  # 新增代码+StrictSchemaBareObject: 把 object 分支改成单一对象类型；若没有这行代码，分支仍会携带非法 type 列表。
                object_schema.setdefault("properties", {})  # 新增代码+StrictSchemaBareObject: 确保 object 分支有 properties；若没有这行代码，strict 后端会要求额外字段边界。
                object_schema.setdefault("required", [])  # 新增代码+StrictSchemaBareObject: 确保 object 分支有 required；若没有这行代码，strict 后端可能继续拒绝对象 schema。
                object_schema["additionalProperties"] = False  # 新增代码+StrictSchemaBareObject: 禁止 object 分支自由字段；若没有这行代码，OpenAI strict 会报 additionalProperties 缺失。
                branches.append(object_schema)  # 新增代码+StrictSchemaBareObject: 保存合法 object 分支；若没有这行代码，对象参数会被错误丢弃。
            elif type_name == "array":  # 新增代码+StrictSchemaBareObject: array 分支需要 items；若没有这行代码，数组参数会退化成裸类型并可能报 missing items。
                array_schema = copy.deepcopy(schema)  # 新增代码+StrictSchemaBareObject: 复制原 schema 给 array 分支使用；若没有这行代码，修改分支会污染调用方 schema。
                array_schema["type"] = "array"  # 新增代码+StrictSchemaBareObject: 把 array 分支改成单一数组类型；若没有这行代码，分支仍会携带非法 type 列表。
                if not isinstance(array_schema.get("items"), dict):  # 新增代码+StrictSchemaBareObject: 检查数组是否缺少 items；若没有这行代码，strict 后端可能报 array schema missing items。
                    array_schema["items"] = cls._fallback_array_item_schema()  # 新增代码+StrictSchemaBareObject: 给开放数组补一个安全元素 schema；若没有这行代码，缺 items 的 MCP 参数仍会被拒绝。
                branches.append(array_schema)  # 新增代码+StrictSchemaBareObject: 保存合法 array 分支；若没有这行代码，数组参数会被错误丢弃。
            elif type_name in {"string", "number", "integer", "boolean"}:  # 新增代码+StrictSchemaBareObject: 保留常见标量分支；若没有这行代码，无 type 兜底会丢掉简单值能力。
                branches.append({"type": type_name})  # 新增代码+StrictSchemaBareObject: 添加标量类型分支；若没有这行代码，模型无法输出对应简单值。
        if "null" not in seen_types:  # 新增代码+StrictSchemaBareObject: 原类型不含 null 时补可空分支；若没有这行代码，可选参数无法用 null 表示未使用。
            branches.append({"type": "null"})  # 新增代码+StrictSchemaBareObject: 添加 null 分支；若没有这行代码，strict required-all 策略会强制可选参数非空。
        nullable_schema: dict[str, Any] = {"anyOf": branches or [{"type": "null"}]}  # 新增代码+StrictSchemaBareObject: 返回 anyOf 包装 schema；若没有这行代码，调用方拿不到 strict-safe 结果。
        if isinstance(schema.get("description"), str):  # 新增代码+StrictSchemaBareObject: 保留原参数说明；若没有这行代码，模型看到的参数语义会变弱。
            nullable_schema["description"] = schema["description"]  # 新增代码+StrictSchemaBareObject: 把说明放在外层属性上；若没有这行代码，anyOf 分支可能丢失可读提示。
        return nullable_schema  # 新增代码+StrictSchemaBareObject: 返回可空复杂类型 schema；若没有这行代码，函数没有输出。

    @classmethod  # 新增代码+StrictSchemaBareObject: 无 type 参数需要一个统一 strict-safe 兜底；若没有这行代码，多个分支会重复宽泛类型逻辑。
    def _fallback_nullable_argument_schema(cls, description: Any = None) -> dict[str, Any]:  # 新增代码+StrictSchemaBareObject: 为未知参数生成可空但合法的通用 schema；若没有这段函数，坏 MCP schema 会继续污染 response_format。
        schema = cls._nullable_complex_type_schema({"type": ["string", "number", "integer", "boolean", "object", "array", "null"]}, ["string", "number", "integer", "boolean", "object", "array", "null"])  # 新增代码+StrictSchemaBareObject: 用 anyOf 表达宽泛兜底；若没有这行代码，无 type 参数无法兼容多种值。
        if isinstance(description, str):  # 新增代码+StrictSchemaBareObject: 判断原参数是否有说明；若没有这行代码，非字符串说明可能污染 schema。
            schema["description"] = description  # 新增代码+StrictSchemaBareObject: 保留原参数说明；若没有这行代码，模型难以理解未知参数用途。
        return schema  # 新增代码+StrictSchemaBareObject: 返回 strict-safe 兜底 schema；若没有这行代码，调用方拿不到结果。

    @staticmethod  # 新增代码+StrictSchemaBareObject: 开放数组 items 兜底不依赖实例状态；若没有这行代码，数组补 items 逻辑会重复。
    def _fallback_array_item_schema() -> dict[str, Any]:  # 新增代码+StrictSchemaBareObject: 生成数组元素的保守 strict-safe schema；若没有这段函数，缺 items 的数组会继续被 OpenAI 拒绝。
        return {"anyOf": [{"type": "string"}, {"type": "number"}, {"type": "integer"}, {"type": "boolean"}, {"type": "null"}]}  # 新增代码+StrictSchemaBareObject: 只允许标量或 null 元素；若没有这行代码，开放数组会缺少 items 或引入嵌套裸 object。

    @classmethod  # 新增代码+StrictSchema: 递归 schema 规范化需要在类方法之间复用；若省略: 嵌套对象 strict 规则会散落在多个地方
    def _strict_response_format_schema(cls, schema: dict[str, Any]) -> dict[str, Any]:  # 新增代码+StrictSchema: 把工具参数 schema 转成 Codex Responses strict response_format 可接受的形状；若省略: 嵌套 properties 的 required 可能不完整
        raw_properties = schema.get("properties")  # 新增代码+StrictSchema: 读取对象字段定义；若省略: 无法判断 required 应该包含哪些键
        if isinstance(raw_properties, dict):  # 新增代码+StrictSchema: 只有 properties 是对象时才按对象字段递归处理；若省略: 坏 schema 会在遍历时崩溃
            cleaned_properties: dict[str, Any] = {}  # 新增代码+StrictSchema: 准备保存递归处理后的字段 schema；若省略: 会直接修改遍历中的原字典
            for property_name, property_schema in raw_properties.items():  # 新增代码+StrictSchema: 遍历每个嵌套字段；若省略: todos.items.id 等字段不会被检查
                cleaned_properties[property_name] = cls._strict_response_format_schema(property_schema) if isinstance(property_schema, dict) else property_schema  # 新增代码+StrictSchema: 递归处理子 schema；若省略: 更深层对象仍可能缺 required
            schema["properties"] = cleaned_properties  # 新增代码+StrictSchema: 写回处理后的字段 schema；若省略: 调用方仍拿到旧嵌套结构
            schema["required"] = list(cleaned_properties.keys())  # 新增代码+StrictSchema: Codex strict schema 要求 required 覆盖 properties 全部键；若省略: 会出现 Missing 'id' 这类 400 错误
            schema["additionalProperties"] = False  # 新增代码+StrictSchema: Codex strict schema 要求对象禁止额外字段；若省略: 模型可能输出未声明参数并被后端拒绝
        else:  # 新增代码+StrictSchema: 处理没有固定 properties 的开放 object；若省略: prompt_arguments 会继续保留 additionalProperties=true
            raw_type = schema.get("type")  # 新增代码+StrictSchema: 读取 type 以判断是否仍然是 object；若省略: 无法识别 {"type":"object","additionalProperties":true}
            has_object_type = raw_type == "object" or (isinstance(raw_type, list) and "object" in raw_type)  # 新增代码+StrictSchema: 同时支持 object 和 ["object","null"]；若省略: 联合类型对象会漏检
            if has_object_type:  # 新增代码+StrictSchema: 只修正对象 schema；若省略: 字符串、数字等普通参数会被误加 properties
                schema["properties"] = {}  # 新增代码+StrictSchema: 开放对象在 strict response_format 中降级为空对象；若省略: Codex 后端会要求 additionalProperties=false
                schema["required"] = []  # 新增代码+StrictSchema: 空对象没有必填字段；若省略: strict schema 可能缺 required 数组
                schema["additionalProperties"] = False  # 新增代码+StrictSchema: 关闭自由键以满足 Codex strict schema；若省略: 当前截图的 prompt_arguments 错误会继续出现
        raw_items = schema.get("items")  # 新增代码+StrictSchema: 读取数组元素 schema；若省略: todos.items 这种数组对象不会被递归修正
        if isinstance(raw_items, dict):  # 新增代码+StrictSchema: 只有 items 是对象时才递归；若省略: 字符串形式 items 会导致类型错误
            schema["items"] = cls._strict_response_format_schema(raw_items)  # 新增代码+StrictSchema: 递归处理数组元素 schema；若省略: 截图里的 todos.items.required 仍会缺字段
        return schema  # 新增代码+StrictSchema: 返回修正后的 schema；若省略: 调用方无法拿到 strict 化结果

    @staticmethod  # 作用: 读取 codex 输出不依赖实例状态
    def _read_codex_output(output_path: Path, fallback_stdout: str) -> str:  # 作用: 优先读取 output-last-message 文件，没有则退回 stdout
        if output_path.exists():  # 作用: 如果 codex 按预期写出了最终消息文件
            return output_path.read_text(encoding="utf-8", errors="replace").strip()  # 作用: 返回文件内容
        return fallback_stdout.strip()  # 作用: 没有输出文件时退回 stdout

    @classmethod  # 作用: 允许 OAuth 适配器复用同一套解析逻辑
    def _parse_model_message(cls, raw_output: str) -> ModelMessage:  # 作用: 把模型返回的 JSON 文本转成内部 ModelMessage
        if not raw_output:  # 作用: 如果模型没有返回内容
            return ModelMessage(text="Codex CLI 没有返回最终 JSON。")  # 作用: 返回清晰错误
        try:  # 作用: 首先按严格 JSON 解析
            payload = json.loads(raw_output)  # 作用: 把 JSON 字符串转成 Python 对象
        except json.JSONDecodeError:  # 作用: 如果模型输出夹杂说明文字
            payload = cls._try_parse_embedded_json(raw_output)  # 作用: 尝试提取第一个 JSON 对象
        if not isinstance(payload, dict):  # 作用: 如果解析结果不是对象
            return ModelMessage(text=f"Codex CLI 返回格式错误：{raw_output[:1000]}")  # 作用: 返回截断内容方便排查
        decision_note = str(payload.get("decision_note", ""))  # 新增代码: 提取模型给人看的决策说明；旧输出缺失时使用空字符串兼容
        text = str(payload.get("text", ""))  # 作用: 提取 text 字段
        raw_tool_calls = payload.get("tool_calls", [])  # 作用: 提取 tool_calls 字段
        tool_calls: list[ToolCall] = []  # 作用: 准备保存内部工具调用对象
        if isinstance(raw_tool_calls, list):  # 作用: 只有数组才逐项解析
            for raw_call in raw_tool_calls:  # 作用: 遍历模型返回的每个工具调用
                if not isinstance(raw_call, dict):  # 作用: 跳过非对象坏项
                    continue  # 作用: 继续处理下一项
                name = str(raw_call.get("name", "")).strip()  # 作用: 提取工具名称
                if not name:  # 作用: 没有工具名就是无效工具调用
                    continue  # 作用: 跳过无效项
                raw_arguments = raw_call.get("arguments", None)  # 修改代码+OutputProtocolV2: 先读取标准 per-tool arguments 字段；若没有这行代码，解析器无法区分缺失参数和空参数对象
                if isinstance(raw_arguments, dict):  # 修改代码+OutputProtocolV2: 标准 arguments 对象优先；若没有这行代码，旧模型输出会被错误忽略
                    arguments = raw_arguments  # 修改代码+OutputProtocolV2: 使用模型为当前工具写出的参数对象；若没有这行代码，工具调用会丢失实际参数
                else:  # 新增代码+OutputProtocolV2: 兼容没有标准 arguments 的分支映射输出；若没有这行代码，arguments_by_tool fallback 无法使用
                    arguments_by_tool = raw_call.get("arguments_by_tool", {})  # 新增代码+OutputProtocolV2: 读取按工具名存放参数的兼容字段；若没有这行代码，未来 fallback 输出协议无法被解析
                    selected_arguments = arguments_by_tool.get(name, {}) if isinstance(arguments_by_tool, dict) else {}  # 新增代码+OutputProtocolV2: 只取当前 name 对应的参数；若没有这行代码，其他工具参数可能串入当前工具
                    arguments = selected_arguments if isinstance(selected_arguments, dict) else {}  # 新增代码+OutputProtocolV2: 非对象参数兜底为空字典；若没有这行代码，工具层可能收到 list/string 等坏参数
                cleaned_arguments = {key: value for key, value in arguments.items() if value is not None}  # 作用: 去掉严格 schema 中未使用的 null 参数
                tool_calls.append(ToolCall(name=name, arguments=cleaned_arguments))  # 作用: 创建内部 ToolCall 并保存
        return ModelMessage(decision_note=decision_note, text=text, tool_calls=tool_calls)  # 修改代码: 返回统一模型消息，并保留决策说明供日志展示

    @staticmethod  # 作用: JSON 提取不依赖实例状态
    def _try_parse_embedded_json(raw_output: str) -> Any:  # 作用: 从意外包裹说明文字的输出中尝试提取 JSON 对象
        start = raw_output.find("{")  # 作用: 找第一个左花括号
        end = raw_output.rfind("}")  # 作用: 找最后一个右花括号
        if start == -1 or end == -1 or end <= start:  # 作用: 如果没有完整 JSON 边界
            return None  # 作用: 返回 None 表示无法恢复
        try:  # 作用: 捕获截取片段仍然不是 JSON 的情况
            return json.loads(raw_output[start : end + 1])  # 作用: 解析并返回 JSON 对象
        except json.JSONDecodeError:  # 作用: 如果截取后仍解析失败
            return None  # 作用: 返回 None 表示无法恢复


@dataclass  # 作用: 自动生成 OAuth token 数据对象的初始化方法
class CodexOAuthTokens:  # 作用: 保存 Codex OAuth/API 直连模式需要的认证信息
    access_token: str  # 作用: 当前可用于请求 Codex responses 端点的短期访问 token
    refresh_token: str  # 作用: 用来刷新 access_token 的长期刷新 token
    expires_at: int  # 作用: access_token 过期时间，单位是毫秒时间戳
    account_id: str | None = None  # 作用: ChatGPT 账号/组织 id，有些请求需要放进 ChatGPT-Account-Id 请求头
    id_token: str = ""  # 作用: OpenAI OAuth 返回的 id_token，可用于解析 account_id


class CodexOAuthTokenStore:  # 作用: 负责把 OAuth token 保存到用户本机目录，而不是项目代码里
    def __init__(self, path: str | Path | None = None) -> None:  # 作用: 初始化 token store，允许测试或高级用户指定路径
        default_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "LearningAgent"  # 作用: 默认保存到用户本地应用数据目录
        self.path = Path(path).expanduser().resolve() if path else default_dir / "codex_oauth_tokens.json"  # 作用: 得到最终 token 文件路径

    @classmethod  # 作用: 允许通过类名从环境变量创建 token store
    def from_env(cls) -> "CodexOAuthTokenStore":  # 作用: 读取 CODEX_OAUTH_TOKEN_FILE
        raw_path = os.environ.get("CODEX_OAUTH_TOKEN_FILE", "").strip()  # 作用: 读取可选 token 文件路径
        return cls(path=raw_path or None)  # 作用: 有配置就用配置，没有就用默认路径

    def load(self) -> CodexOAuthTokens | None:  # 作用: 从磁盘读取 token，如果没有登录过就返回 None
        if not self.path.exists():  # 作用: 如果 token 文件不存在
            return None  # 作用: 返回 None，让模型适配器触发网页登录
        try:  # 作用: 捕获 JSON 或字段异常
            payload = json.loads(self.path.read_text(encoding="utf-8"))  # 作用: 读取并解析 token JSON 文件
            return CodexOAuthTokens(  # 作用: 把 JSON 字典转成数据对象
                access_token=str(payload.get("access_token", "")),  # 作用: 读取 access_token 字段
                refresh_token=str(payload.get("refresh_token", "")),  # 作用: 读取 refresh_token 字段
                expires_at=int(payload.get("expires_at", 0)),  # 作用: 读取 expires_at 字段，缺失视为过期
                account_id=payload.get("account_id") or None,  # 作用: 读取 account_id，空值转 None
                id_token=str(payload.get("id_token", "")),  # 作用: 读取 id_token，缺失用空字符串
            )  # 作用: token 对象创建结束
        except (OSError, ValueError, TypeError, json.JSONDecodeError):  # 作用: 捕获文件读取、类型转换和 JSON 解析错误
            return None  # 作用: 坏 token 文件按未登录处理

    def save(self, tokens: CodexOAuthTokens) -> None:  # 作用: 把最新 token 写入用户本机目录
        self.path.parent.mkdir(parents=True, exist_ok=True)  # 作用: 确保 token 文件所在目录存在
        payload = {  # 作用: 准备可序列化保存的 token 字典
            "access_token": tokens.access_token,  # 作用: 保存 access_token
            "refresh_token": tokens.refresh_token,  # 作用: 保存 refresh_token
            "expires_at": tokens.expires_at,  # 作用: 保存过期时间
            "account_id": tokens.account_id,  # 作用: 保存账号/组织 id
            "id_token": tokens.id_token,  # 作用: 保存 id_token
        }  # 作用: token 字典结束
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")  # 作用: 用 UTF-8 写入 JSON token 文件


PostJsonFunction = Callable[[str, dict[str, str], dict[str, object]], dict[str, object]]  # 作用: 抽象 HTTP POST 函数，测试时可注入假函数
LoginCallbackFunction = Callable[[], CodexOAuthTokens]  # 作用: 抽象 OAuth 登录函数，测试时可注入假函数


class CodexOAuthChatModel:  # 作用: 参考 opencode2 的 OpenAI OAuth/API 链路实现 GPT-5.5 模型适配器
    CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"  # 作用: opencode2 使用的 OpenAI Codex OAuth client id
    ISSUER = "https://auth.openai.com"  # 作用: OpenAI OAuth 授权服务器地址
    CODEX_API_ENDPOINT = CHATGPT_CODEX_RESPONSES_ENDPOINT  # 修改代码+DirectChatGptSseClient: 旧 OAuth wrapper 复用共享 Codex responses 端点；如果没有这行代码，GUI 直连和旧 wrapper 可能分别漂移。
    OAUTH_PORT = 1455  # 作用: 本地 OAuth 回调端口

    def __init__(  # 作用: 初始化 OAuth/API 直连模型适配器
        self,  # 作用: 当前对象
        model: str,  # 作用: 目标模型名，例如 gpt-5.5
        token_store: Any | None = None,  # 作用: 可注入 token store，测试时避免读写真实 token
        post_json: PostJsonFunction | None = None,  # 作用: 可注入 HTTP POST 函数，测试时避免联网
        login_callback: LoginCallbackFunction | None = None,  # 作用: 可注入登录函数，测试时避免打开浏览器
        oauth_timeout_seconds: int = 300,  # 作用: 浏览器 OAuth 最长等待时间
        sse_read_timeout_seconds: int = 240,  # 新增代码+OAuthSseDeadline: 设置 Codex Responses SSE 总读取时长；如果没有这行代码，真实终端可能一直卡在模型调用而不返回错误。
        monotonic: Callable[[], float] | None = None,  # 新增代码+OAuthSseDeadline: 允许测试注入假时钟；如果没有这行代码，SSE deadline 测试必须真实等待数分钟。
        native_tools_enabled: bool | None = None,  # 新增代码+OAuthNativeCodexBody: 允许测试和环境显式开启 Responses 原生 tools；如果没有这一行，蓝图第 4 项无法进入新协议分支。
    ) -> None:
        self._model = model  # 作用: 保存模型名
        self._token_store = token_store or CodexOAuthTokenStore.from_env()  # 作用: 保存 token store
        self._post_json = post_json or self._post_json_request  # 作用: 保存 HTTP 函数
        self._login_callback = login_callback or self._login_with_browser  # 作用: 保存登录函数
        self._oauth_timeout_seconds = oauth_timeout_seconds  # 作用: 保存登录超时时间
        self._sse_read_timeout_seconds = max(int(sse_read_timeout_seconds), 1)  # 新增代码+OAuthSseDeadline: 保存至少 1 秒的 SSE 总截止；如果没有这行代码，0 或负数会让读取器边界不稳定。
        self._monotonic = monotonic or time.monotonic  # 新增代码+OAuthSseDeadline: 保存单调时钟用于计算总截止；如果没有这行代码，系统时间调整可能影响超时判断。
        native_tools_env = os.environ.get("CODEX_OAUTH_NATIVE_TOOLS", "").strip().lower()  # 新增代码+OAuthNativeCodexBody: 读取实验开关环境变量；如果没有这一行，真实运行只能靠代码改动切换新协议。
        self._native_tools_enabled = bool(native_tools_enabled) if native_tools_enabled is not None else native_tools_env in {"1", "true", "yes", "on"}  # 新增代码+OAuthNativeCodexBody: 保存 native tools 开关并默认关闭；如果没有这一行，新旧协议无法安全并存。

    @classmethod  # 作用: 允许通过类名从环境变量创建模型
    def from_env(cls) -> "CodexOAuthChatModel":  # 作用: 读取 CODEX_MODEL 和 OAuth 超时配置
        model = os.environ.get("CODEX_MODEL", "gpt-5.5").strip() or "gpt-5.5"  # 作用: 默认使用 gpt-5.5
        raw_timeout = os.environ.get("CODEX_OAUTH_TIMEOUT_SECONDS", "300").strip()  # 作用: 读取可选 OAuth 等待秒数
        raw_sse_timeout = os.environ.get("CODEX_OAUTH_SSE_READ_TIMEOUT_SECONDS", "240").strip()  # 新增代码+OAuthSseDeadline: 读取 Codex SSE 总读取超时；如果没有这行代码，真实终端无法按场景调短卡住门禁。
        try:  # 作用: 捕获非法数字
            timeout_seconds = max(int(raw_timeout), 60)  # 作用: 至少等待 60 秒
        except ValueError:  # 作用: 如果不是数字
            timeout_seconds = 300  # 作用: 回退到 5 分钟
        try:  # 新增代码+OAuthSseDeadline: 捕获非法 SSE 超时配置；如果没有这行代码，用户填错环境变量会让 agent 启动失败。
            sse_timeout_seconds = max(int(raw_sse_timeout), 30)  # 新增代码+OAuthSseDeadline: 真实运行至少给模型 30 秒响应；如果没有这行代码，过短配置会制造大量误超时。
        except ValueError:  # 新增代码+OAuthSseDeadline: 处理非数字环境变量；如果没有这行代码，错误配置无法自动回退。
            sse_timeout_seconds = 240  # 新增代码+OAuthSseDeadline: 非法配置回到 240 秒；如果没有这行代码，默认值没有稳定兜底。
        return cls(model=model, oauth_timeout_seconds=timeout_seconds, sse_read_timeout_seconds=sse_timeout_seconds)  # 修改代码+OAuthSseDeadline: 返回同时带登录超时和 SSE 总截止的 OAuth 模型；如果没有这行代码，from_env 创建的真实模型不会启用新门禁。

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelMessage:  # 作用: 使用 OAuth token 请求 Codex Responses API
        try:  # 作用: 捕获登录、刷新、请求和解析异常
            tokens = self._get_valid_tokens()  # 作用: 获取可用 access token，必要时登录或刷新
            headers = self._build_headers(tokens)  # 作用: 构造鉴权请求头
            body = self._build_responses_body(messages=messages, tools=tools)  # 作用: 构造 Codex responses 请求体
            try:  # 新增代码+OAuth重登录: 单独捕获 Codex API 鉴权失败；若省略: 运行中 token 被服务端拒绝时只能把 401/403 直接报给用户
                response = self._post_json(self.CODEX_API_ENDPOINT, headers, body)  # 修改代码+OAuth重登录: 先用当前 token 请求 Codex 后端；若省略: 正常路径无法调用模型
            except Exception as error:  # 新增代码+OAuth重登录: 接住第一次 API 请求错误以判断是否需要重新登录；若省略: 没有机会区分鉴权失败和网络超时
                if self._is_transient_api_error(error):  # 修改代码+OAuth远端断连: timeout 或远端提前断开都先按临时网络错误重试一次；若省略: Remote end closed 会直接失败
                    response = self._post_json(self.CODEX_API_ENDPOINT, headers, body)  # 修改代码+OAuth远端断连: 用同一 token 立即重试一次模型请求；若省略: 临时断连没有自动恢复机会
                elif not self._should_relogin_after_api_error(error):  # 修改代码+OAuth远端断连: 非临时网络错误且非鉴权错误才交给外层格式化；若省略: 普通错误可能被误判为登录问题
                    raise  # 新增代码+OAuth重登录: 非鉴权错误继续交给外层格式化；若省略: timeout 等真实网络问题会被吞掉
                else:  # 修改代码+OAuth远端断连: 只有明确 401/403 等鉴权失败才进入重新登录；若省略: 远端断连分支会误触发网页登录
                    tokens = self._login_callback()  # 修改代码+OAuth远端断连: API 返回 401/403 时重新打开 OAuth 登录流程；若省略: 用户无法从登录过期中恢复
                    self._token_store.save(tokens)  # 修改代码+OAuth远端断连: 保存重新登录得到的新 token；若省略: 下次调用仍会读取旧失效 token
                    headers = self._build_headers(tokens)  # 修改代码+OAuth远端断连: 用新 token 重建鉴权请求头；若省略: 重试仍会带旧 token 失败
                    response = self._post_json(self.CODEX_API_ENDPOINT, headers, body)  # 修改代码+OAuth远端断连: 重新认证后只重试一次模型请求；若省略: 登录完成后用户本轮问题仍没有结果
            if self._native_tools_enabled:  # 新增代码+OAuthNativeOutputParser: native 模式下直接消费 Responses output items；如果没有这一行，function_call 会被旧 JSON 文本解析器误处理。
                output_items = self._extract_response_output_items(response)  # 新增代码+OAuthNativeOutputParser: 从 Codex 后端响应中取出原生 output 数组；如果没有这一行，工具调用 item 没有解析入口。
                return parse_responses_output_items_to_model_message(output_items)  # 新增代码+OAuthNativeOutputParser: 转成内部 ModelMessage 交给执行器；如果没有这一行，agent 主循环无法执行原生工具调用。
            raw_output = self._extract_response_text(response)  # 作用: 提取模型输出的 JSON 文本
            model_message = CodexCliChatModel._parse_model_message(raw_output)  # 新增代码+模型JSON恢复: 先解析 OAuth/API 第一次输出；若没有这行代码，无法区分合法工具调用和坏 JSON。
            if CodexCliChatModel._is_parse_error_message(model_message):  # 新增代码+模型JSON恢复: 检测结构化输出是否漂移成非法 JSON；若没有这行代码，真实终端会直接停在格式错误。
                repair_messages = CodexCliChatModel._messages_with_json_repair_prompt(messages)  # 新增代码+模型JSON恢复: 构造一次不污染原会话的修复消息；若没有这行代码，重试会缺少原始任务上下文。
                repair_body = self._build_responses_body(messages=repair_messages, tools=tools)  # 新增代码+模型JSON恢复: 用相同工具 schema 生成第二次请求体；若没有这行代码，模型仍可能输出当前工具池不支持的参数。
                try:  # 新增代码+模型JSON恢复: 捕获修复请求的网络或服务端异常；若没有这行代码，修复失败会掩盖第一次格式错误证据。
                    repair_response = self._post_json(self.CODEX_API_ENDPOINT, headers, repair_body)  # 新增代码+模型JSON恢复: 对同一 Codex responses 端点做一次协议修复重试；若没有这行代码，偶发非法 JSON 没有恢复机会。
                    repair_raw_output = self._extract_response_text(repair_response)  # 新增代码+模型JSON恢复: 提取第二次响应文本；若没有这行代码，无法解析修复结果。
                    repair_message = CodexCliChatModel._parse_model_message(repair_raw_output)  # 新增代码+模型JSON恢复: 把第二次响应转成内部消息；若没有这行代码，工具执行器拿不到修复后的 tool_calls。
                    if not CodexCliChatModel._is_parse_error_message(repair_message):  # 新增代码+模型JSON恢复: 只采用真正恢复成功的第二次结果；若没有这行代码，坏 JSON 会覆盖第一次证据。
                        return repair_message  # 新增代码+模型JSON恢复: 返回恢复后的工具调用或最终回答；若没有这行代码，自动修复成功也不会推进任务。
                except Exception:  # 新增代码+模型JSON恢复: 修复重试失败时保留第一次解析错误；若没有这行代码，用户会看到更远离根因的异常。
                    pass  # 新增代码+模型JSON恢复: 不吞掉主流程，只让下方返回第一次错误文本；若没有这行代码，except 块语法不完整。
            return model_message  # 修改代码+模型JSON恢复: 正常输出直接返回，修复失败则返回第一次错误供审计；若没有这行代码，OAuth chat 没有稳定返回值。
        except Exception as error:  # 作用: 捕获所有链路错误
            return ModelMessage(text=self._format_oauth_error(error))  # 修改代码+OAuth超时提示: 按错误类型返回中文说明；若省略: timeout 仍会只显示英文底层错误

    def _get_valid_tokens(self) -> CodexOAuthTokens:  # 作用: 获取可用 token，缺失就登录，快过期就刷新
        tokens = self._token_store.load()  # 作用: 从本地读取 token
        if tokens is None or not tokens.refresh_token:  # 作用: 如果未登录或缺少 refresh_token
            tokens = self._login_callback()  # 作用: 打开浏览器完成登录
            self._token_store.save(tokens)  # 作用: 保存登录得到的 token
            return tokens  # 作用: 返回新 token
        if tokens.expires_at <= self._now_ms() + 60000:  # 作用: 如果 access_token 60 秒内会过期
            tokens = self._refresh_tokens_or_login(tokens)  # 修改代码+OAuth重登录: refresh token 被拒绝时改走网页登录兜底；若省略: 登录过期会停在错误信息而不会打开浏览器
            self._token_store.save(tokens)  # 作用: 保存刷新后的 token
        return tokens  # 作用: 返回可用 token

    def _refresh_tokens_or_login(self, tokens: CodexOAuthTokens) -> CodexOAuthTokens:  # 新增代码+OAuth重登录: 封装 refresh 失败后的重新登录兜底；若省略: `_get_valid_tokens` 会混杂错误判断逻辑
        try:  # 新增代码+OAuth重登录: 先按正常路径使用 refresh token；若省略: 每次过期都会强制网页登录，体验会倒退
            return self._refresh_tokens(tokens)  # 新增代码+OAuth重登录: refresh 成功时直接返回新 token；若省略: access token 过期后无法静默续期
        except Exception as error:  # 新增代码+OAuth重登录: 捕获 refresh token 被服务端拒绝等错误；若省略: 无法兜底到网页登录
            if not self._should_relogin_after_refresh_error(error):  # 新增代码+OAuth重登录: 只对明确的 refresh 鉴权失败重新登录；若省略: 网络错误也会误触发网页登录
                raise  # 新增代码+OAuth重登录: 非登录失效问题继续向外抛出；若省略: 真实服务故障会被伪装成登录问题
            return self._login_callback()  # 新增代码+OAuth重登录: refresh token 失效时重新走浏览器认证；若省略: 用户无法自动恢复过期登录

    @staticmethod  # 新增代码+OAuth重登录: 这个判断只依赖错误文本，不需要实例状态；若省略: 调用时必须创建不必要的对象状态
    def _should_relogin_after_refresh_error(error: Exception) -> bool:  # 新增代码+OAuth重登录: 判断 refresh 失败是否代表需要重新登录；若省略: 程序无法区分 token 失效和网络故障
        error_text = str(error).lower()  # 新增代码+OAuth重登录: 统一转小写便于匹配 HTTP/OAuth 错误；若省略: 大小写不同会导致漏判
        markers = ("invalid_grant", "invalid refresh", "http 400", "http 401", "unauthorized")  # 新增代码+OAuth重登录: 列出 refresh token 失效常见信号；若省略: 无法识别服务端拒绝刷新凭证
        return any(marker in error_text for marker in markers)  # 新增代码+OAuth重登录: 任一信号命中就允许重新网页登录；若省略: refresh token 过期仍不会弹登录

    @staticmethod  # 新增代码+OAuth重登录: API 鉴权判断也只依赖错误文本；若省略: 方法会不必要地依赖实例状态
    def _should_relogin_after_api_error(error: Exception) -> bool:  # 新增代码+OAuth重登录: 判断 Codex API 错误是否值得重新登录并重试一次；若省略: API 401/403 无法自动恢复
        error_text = str(error).lower()  # 新增代码+OAuth重登录: 统一转小写匹配状态码和英文错误；若省略: 错误大小写不同会漏判
        markers = ("http 401", "http 403", "unauthorized", "forbidden", "invalid_token", "invalid bearer")  # 新增代码+OAuth重登录: 只列鉴权失败信号；若省略: 程序不知道哪些 API 错误该重新登录
        return any(marker in error_text for marker in markers)  # 新增代码+OAuth重登录: 命中鉴权信号才重新登录；若省略: 用户仍需手动处理过期登录

    def _is_transient_api_error(self, error: Exception) -> bool:  # 新增代码+OAuth远端断连: 判断 API 错误是否适合用同一 token 重试一次；若省略: timeout 和远端断连判断会分散且容易漏掉
        return self._is_timeout_error(error) or self._is_remote_closed_error(error)  # 新增代码+OAuth远端断连: 把 read timeout 与远端提前断连都视为临时网络错误；若省略: RemoteDisconnected 仍会直接失败

    def _format_oauth_error(self, error: Exception) -> str:  # 新增代码+OAuth超时提示: 把底层异常转换成用户看得懂的 OAuth/API 错误；若省略: 初学者只能看到英文异常
        raw_error = str(error)  # 新增代码+OAuth超时提示: 保留原始错误方便排查；若省略: 用户和开发者会失去底层线索
        if self._is_timeout_error(error):  # 新增代码+OAuth超时提示: 单独识别请求或响应读取超时；若省略: timeout 会继续被误解成登录过期
            return f"Codex OAuth/API 调用失败：响应读取超时。这通常是网络或 Codex 后端流式响应超时，不一定是 OAuth 登录过期；请先重试。如果后续出现 HTTP 401/403 或 invalid_grant，再重新登录。原始错误：{raw_error}"  # 新增代码+OAuth超时提示: 给出中文边界说明和原始错误；若省略: 用户不知道为什么没有弹出网页登录
        if self._is_remote_closed_error(error):  # 新增代码+OAuth远端断连: 单独识别远端提前关闭连接；若省略: 用户仍只会看到英文 Remote end closed
            return f"Codex OAuth/API 调用失败：远端连接关闭，Codex 后端或中间网络在返回响应前断开了连接；这通常是临时网络/API 连接问题，不一定是 OAuth 登录过期。系统已对首次同类错误自动重试一次；如果仍出现，请稍后重试或检查网络代理。原始错误：{raw_error}"  # 新增代码+OAuth远端断连: 给出中文边界、自动重试说明和原始错误；若省略: 用户会误以为应该弹网页登录
        return f"Codex OAuth/API 调用失败：{raw_error}"  # 新增代码+OAuth超时提示: 非超时错误保持原始信息；若省略: 其他异常会没有可读反馈

    @staticmethod  # 新增代码+OAuth超时提示: timeout 判断不依赖实例状态；若省略: 这个小工具无法在格式化函数中清晰复用
    def _is_timeout_error(error: Exception) -> bool:  # 新增代码+OAuth超时提示: 判断异常是否属于超时；若省略: 无法给截图里的 read timeout 单独提示
        error_text = str(error).lower()  # 新增代码+OAuth超时提示: 统一转小写方便匹配 timeout 文本；若省略: 不同异常文案可能漏判
        return isinstance(error, TimeoutError) or "timed out" in error_text or "timeout" in error_text  # 新增代码+OAuth超时提示: 覆盖 Python TimeoutError 和常见英文文案；若省略: `The read operation timed out` 不会被识别

    @staticmethod  # 新增代码+OAuth远端断连: 远端关闭连接判断不依赖实例状态；若省略: 格式化和重试逻辑无法复用同一个判断
    def _is_remote_closed_error(error: Exception) -> bool:  # 新增代码+OAuth远端断连: 判断异常是否属于服务端未返回响应就断开；若省略: 截图里的 Remote end closed 不会被自动重试或中文解释
        error_text = str(error).lower()  # 新增代码+OAuth远端断连: 统一转小写匹配标准库和网络层错误文案；若省略: 大小写不同可能漏判
        markers = ("remote end closed connection without response", "remote disconnected", "server disconnected", "connection reset by peer", "connection aborted")  # 新增代码+OAuth远端断连: 覆盖 urllib/http.client 常见远端断连文本；若省略: 真实网络断开形态容易漏掉
        return any(marker in error_text for marker in markers)  # 新增代码+OAuth远端断连: 任一远端断连信号命中就视为临时连接错误；若省略: 判断永远不能命中

    def _refresh_tokens(self, tokens: CodexOAuthTokens) -> CodexOAuthTokens:  # 作用: 使用 refresh_token 换新的 access_token
        payload = self._post_json(  # 作用: 请求 OAuth token 端点
            f"{self.ISSUER}/oauth/token",  # 作用: token 刷新端点
            {"Content-Type": "application/x-www-form-urlencoded"},  # 作用: token 端点要求表单编码
            {  # 作用: 刷新请求体
                "grant_type": "refresh_token",  # 作用: 指定刷新流程
                "refresh_token": tokens.refresh_token,  # 作用: 传入旧 refresh_token
                "client_id": self.CLIENT_ID,  # 作用: 传入 Codex OAuth client id
            },  # 作用: 请求体结束
        )  # 作用: HTTP POST 结束
        return self._tokens_from_response(payload, fallback_account_id=tokens.account_id)  # 作用: 转成 token 数据对象

    def _login_with_browser(self) -> CodexOAuthTokens:  # 作用: 打开浏览器完成 OpenAI OAuth 授权码流程
        pkce = self._generate_pkce()  # 作用: 生成 PKCE verifier/challenge
        state = self._generate_state()  # 作用: 生成防伪造 state
        redirect_uri = f"http://localhost:{self.OAUTH_PORT}/auth/callback"  # 作用: 构造本地回调地址
        result: dict[str, str] = {}  # 作用: 用字典接收回调里的 code/state/error

        class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):  # 作用: 定义只处理一次 OAuth 回调的本地 HTTP handler
            def log_message(self, format: str, *args: Any) -> None:  # 作用: 关闭默认访问日志，避免终端噪音
                del format, args  # 作用: 明确丢弃未使用参数

            def do_GET(self) -> None:  # 作用: 浏览器登录成功后会访问这个 GET 回调
                parsed = urllib.parse.urlparse(self.path)  # 作用: 解析回调 URL
                query = urllib.parse.parse_qs(parsed.query)  # 作用: 解析 query 参数
                result["code"] = query.get("code", [""])[0]  # 作用: 保存授权 code
                result["state"] = query.get("state", [""])[0]  # 作用: 保存回调 state
                result["error"] = query.get("error_description", query.get("error", [""]))[0]  # 作用: 保存可能的 OAuth 错误
                html = "<html><body><h1>Authorization Successful</h1><p>You can close this window.</p></body></html>"  # 作用: 准备成功页面
                if result["error"]:  # 作用: 如果 OAuth 返回错误
                    html = f"<html><body><h1>Authorization Failed</h1><pre>{result['error']}</pre></body></html>"  # 作用: 准备错误页面
                self.send_response(200)  # 作用: 返回 HTTP 200
                self.send_header("Content-Type", "text/html; charset=utf-8")  # 作用: 声明 HTML 和 UTF-8
                self.end_headers()  # 作用: 结束响应头
                self.wfile.write(html.encode("utf-8"))  # 作用: 写出响应体

        auth_url = self._build_authorize_url(redirect_uri=redirect_uri, pkce_challenge=pkce["challenge"], state=state)  # 作用: 构造授权 URL
        print(f"请在浏览器完成 OpenAI/Codex OAuth 登录：{auth_url}")  # 作用: 打印 URL，自动打开失败时可手动复制
        with http.server.HTTPServer(("localhost", self.OAUTH_PORT), OAuthCallbackHandler) as server:  # 作用: 启动本地回调服务器
            server.timeout = self._oauth_timeout_seconds  # 作用: 设置等待超时
            webbrowser.open(auth_url)  # 作用: 自动打开浏览器
            server.handle_request()  # 作用: 等待一次 OAuth 回调
        if result.get("error"):  # 作用: 如果授权返回错误
            raise RuntimeError(result["error"])  # 作用: 抛出错误给上层
        if result.get("state") != state:  # 作用: 如果 state 不匹配
            raise RuntimeError("OAuth state 不匹配，已拒绝本次登录。")  # 作用: 防止伪造回调
        if not result.get("code"):  # 作用: 如果没有拿到授权 code
            raise RuntimeError("没有收到 OAuth 授权 code，可能是登录超时或浏览器没有完成授权。")  # 作用: 给出清晰错误
        payload = self._exchange_code_for_tokens(code=result["code"], redirect_uri=redirect_uri, code_verifier=pkce["verifier"])  # 作用: 用 code 换 token
        return self._tokens_from_response(payload, fallback_account_id=None)  # 作用: 返回 token 数据对象

    def _exchange_code_for_tokens(self, code: str, redirect_uri: str, code_verifier: str) -> dict[str, object]:  # 作用: 使用授权 code 换 access/refresh token
        return self._post_json(  # 作用: 发起 token exchange 请求
            f"{self.ISSUER}/oauth/token",  # 作用: OpenAI OAuth token 端点
            {"Content-Type": "application/x-www-form-urlencoded"},  # 作用: token 端点要求表单编码
            {  # 作用: 授权码交换请求体
                "grant_type": "authorization_code",  # 作用: 指定授权码流程
                "code": code,  # 作用: 传入授权 code
                "redirect_uri": redirect_uri,  # 作用: 传入和授权 URL 一致的回调地址
                "client_id": self.CLIENT_ID,  # 作用: 传入 client id
                "code_verifier": code_verifier,  # 作用: 传入 PKCE verifier
            },  # 作用: 请求体结束
        )  # 作用: HTTP POST 结束

    def _build_headers(self, tokens: CodexOAuthTokens) -> dict[str, str]:  # 作用: 构造 Codex responses 请求头
        headers = {  # 作用: 准备基础请求头
            "authorization": f"Bearer {tokens.access_token}",  # 作用: 使用 OAuth access token 鉴权
            "Content-Type": "application/json",  # 作用: responses 端点请求体是 JSON
            "User-Agent": "learning-agent/0.1",  # 作用: 标记请求来源是教学 agent
        }  # 作用: 基础请求头结束
        if tokens.account_id:  # 作用: 如果有账号/组织 id
            headers["ChatGPT-Account-Id"] = tokens.account_id  # 作用: 带上账号头，匹配 opencode2 做法
        return headers  # 作用: 返回最终请求头

    def _build_responses_body(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, object]:  # 作用: 构造 Codex responses 请求体
        if self._native_tools_enabled:  # 新增代码+OAuthNativeCodexBody: 开启实验开关时使用顶层 tools 协议；如果没有这一行，工具仍会被塞进 prompt 而不是交给 API。
            return self._build_native_responses_body(messages=messages, tools=tools)  # 新增代码+OAuthNativeCodexBody: 返回 native Responses 请求体；如果没有这一行，新协议构造逻辑不会被调用。
        return {  # 作用: 返回 Responses API 风格请求体
            "model": self._model,  # 作用: 指定目标模型名
            "store": False,  # 作用: Codex 后端要求显式关闭存储
            "stream": True,  # 作用: Codex 后端要求显式开启流式响应
            "instructions": self._build_instructions(),  # 作用: 顶层 instructions 是 Codex 后端必需字段
            "input": self._build_responses_input(messages=messages, tools=tools),  # 作用: input 必须是 Responses 消息列表
            "text": {  # 作用: 要求模型按 JSON schema 输出
                "format": {  # 作用: 文本格式约束字段
                    "type": "json_schema",  # 作用: 指定结构化输出类型
                    "name": "learning_agent_model_message",  # 作用: 给 schema 起稳定名字
                    "schema": CodexCliChatModel._output_schema(tools=tools),  # 修改代码+MCP参数适配: 按当前工具列表生成严格输出 schema；若省略 tools: OAuth 模型仍无法输出 query/url 等 MCP 参数
                    "strict": True,  # 作用: 要求模型严格遵守 schema
                },  # 作用: format 结束
            },  # 作用: text 结束
        }  # 作用: 请求体结束

    def _build_native_responses_body(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, object]:  # 新增代码+OAuthNativeCodexBody: 函数段开始，构造 ClaudeCode/Codex 风格的 Responses 原生工具请求体；如果没有这段函数，native 开关没有真实 payload，本段到 return 字典结束。
        return {  # 新增代码+OAuthNativeCodexBody: 返回 Responses 原生 tools 请求体；如果没有这一行，调用方拿不到可发送的 body。
            "model": self._model,  # 新增代码+OAuthNativeCodexBody: 指定目标模型名；如果没有这一行，Codex 后端不知道使用哪个模型。
            "store": False,  # 新增代码+OAuthNativeCodexBody: 关闭服务端存储以保持旧链路隐私语义；如果没有这一行，请求行为会和旧 OAuth 路径不一致。
            "stream": True,  # 新增代码+OAuthNativeCodexBody: 保持 Codex 后端流式响应要求；如果没有这一行，现有 SSE 读取器不会被使用。
            "instructions": self._build_native_tools_instructions(),  # 新增代码+OAuthNativeCodexBody: 使用原生工具协议提示词；如果没有这一行，模型仍可能按旧 JSON 对象格式回答。
            "input": self._build_native_tools_input(messages=messages),  # 新增代码+OAuthNativeCodexBody: 构造不再内嵌工具 schema 的输入；如果没有这一行，原生工具和旧 prompt 会混在一起。
            "tools": self._build_native_tools(tools=tools),  # 新增代码+OAuthNativeCodexBody: 把工具放进顶层 tools；如果没有这一行，API 层 tool_search/defer_loading 无法生效。
            "include": ["reasoning.encrypted_content"],  # 新增代码+OAuthNativeReasoningCarry: store=False 时请求可续轮的 reasoning 加密内容；如果没有这一行，工具调用后的下一轮可能缺 reasoning 上下文而只返回空白 reasoning。
            "parallel_tool_calls": False,  # 新增代码+OAuthNativeCodexBody: 暂时关闭并行工具调用以匹配现有串行回填器；如果没有这一行，多工具并发可能让 tool_call_id 对不上。
        }  # 新增代码+OAuthNativeCodexBody: native 请求体结束；如果没有这一行，Python 字典语法不完整。
    # 新增代码+OAuthNativeCodexBody: 函数段结束，_build_native_responses_body 到此结束；如果没有这个边界说明，用户不容易看出新请求体范围。

    def _build_native_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:  # 新增代码+OAuthNativeCodexBody: 函数段开始，把当前 OpenAI-compatible 工具池转成 Responses 顶层 tools；如果没有这段函数，schema 转换会散落在请求体里，本段到 return native tools 结束。
        deferred_tool_names = self._native_deferred_tool_names(tools=tools)  # 新增代码+OAuthNativeCodexBody: 先计算需要 defer_loading 的工具名；如果没有这一行，Computer Use 等高风险工具会 eager 暴露。
        return build_hosted_tool_search_tools_by_namespace(  # 新增代码+OAuthNativeCodexBody: 调用集中协议助手生成 namespace + tool_search；如果没有这一行，native tools 结构容易和官方格式漂移。
            tools,  # 新增代码+OAuthNativeCodexBody: 传入当前轮可用工具 schema；如果没有这一行，模型不会看到任何可调用工具。
            deferred_tool_names=deferred_tool_names,  # 新增代码+OAuthNativeCodexBody: 传入延迟加载工具名集合；如果没有这一行，defer_loading 字段不会出现在 payload。
            namespace_for_tool=default_responses_namespace_for_tool_name,  # 新增代码+OAuthNativeCodexBody: 传入默认 namespace 分配函数；如果没有这一行，Computer Use 无法独立分组。
            namespace_descriptions=default_responses_namespace_descriptions(),  # 新增代码+OAuthNativeCodexBody: 传入 namespace 说明；如果没有这一行，模型选择工具时缺少分组含义。
        )  # 新增代码+OAuthNativeCodexBody: 结束 native tools 构造调用；如果没有这一行，Python 调用语法不完整。
    # 新增代码+OAuthNativeCodexBody: 函数段结束，_build_native_tools 到此结束；如果没有这个边界说明，用户不容易看出转换职责。

    def _native_deferred_tool_names(self, tools: list[dict[str, Any]]) -> set[str]:  # 新增代码+OAuthNativeCodexBody: 函数段开始，判断哪些工具在 native 模式要 defer_loading；如果没有这段函数，延迟加载规则会不可审计，本段到 return 集合结束。
        deferred_tool_names: set[str] = set()  # 新增代码+OAuthNativeCodexBody: 准备保存需要延迟加载的工具名；如果没有这一行，后续无法累积多个工具。
        for tool_schema in tools:  # 新增代码+OAuthNativeCodexBody: 遍历当前轮传入模型的工具 schema；如果没有这一行，无法逐个判断工具属性。
            function_schema = tool_schema.get("function", {}) if isinstance(tool_schema, dict) else {}  # 新增代码+OAuthNativeCodexBody: 读取旧格式 function 字段；如果没有这一行，工具名和 defer 标记没有来源。
            if not isinstance(function_schema, dict):  # 新增代码+OAuthNativeCodexBody: 防御坏 schema；如果没有这一行，异常工具会让 .get 调用报错。
                continue  # 新增代码+OAuthNativeCodexBody: 跳过坏 schema 保持请求体可构造；如果没有这一行，单个坏工具会阻断整轮。
            tool_name = str(function_schema.get("name", "") or "")  # 新增代码+OAuthNativeCodexBody: 提取工具名；如果没有这一行，无法判断 namespace 和 defer_loading。
            namespace_name = default_responses_namespace_for_tool_name(tool_name)  # 新增代码+OAuthNativeCodexBody: 根据工具名判断默认 namespace；如果没有这一行，Computer Use 无法自动识别。
            explicit_defer = function_schema.get("defer_loading") is True or tool_schema.get("defer_loading") is True  # 新增代码+OAuthNativeCodexBody: 兼容 schema 自带 defer 标记；如果没有这一行，未来 runtime 标记会被丢掉。
            if explicit_defer or namespace_name == "computer_use":  # 新增代码+OAuthNativeCodexBody: 显式 defer 或 Computer Use 工具都延迟加载；如果没有这一行，高风险桌面工具会首轮完整暴露。
                deferred_tool_names.add(tool_name)  # 新增代码+OAuthNativeCodexBody: 保存需要延迟加载的工具名；如果没有这一行，最终 payload 不会出现 defer_loading。
        return deferred_tool_names  # 新增代码+OAuthNativeCodexBody: 返回延迟加载工具名集合；如果没有这一行，调用方拿不到判断结果。
    # 新增代码+OAuthNativeCodexBody: 函数段结束，_native_deferred_tool_names 到此结束；如果没有这个边界说明，用户不容易看出 defer 规则。

    def _build_native_tools_instructions(self) -> str:  # 新增代码+OAuthNativeCodexBody: 函数段开始，构造 Responses 原生工具模式提示词；如果没有这段函数，模型会继续被旧 JSON 输出契约误导，本段到 return 字符串结束。
        return (  # 新增代码+OAuthNativeCodexBody: 返回面向原生 tools 的顶层 instructions；如果没有这一行，字符串无法拼接返回。
            "你是 learning_agent 的模型适配器，负责根据用户目标决定直接回答或调用顶层 tools。\n"  # 新增代码+OAuthNativeCodexBody: 定义模型职责；如果没有这一行，模型可能误以为自己要本地执行。
            "当需要外部动作时，必须使用 Responses 原生 function_call 或 hosted tool_search，不要把工具调用写成自定义 JSON 文本。\n"  # 新增代码+OAuthNativeCodexBody: 明确 native 输出契约；如果没有这一行，模型可能回到旧 tool_calls JSON。
            "如果工具带 defer_loading，请先用 tool_search 查找和加载对应工具，再调用加载后的 function。\n"  # 新增代码+OAuthNativeCodexBody: 解释 defer_loading 的使用方式；如果没有这一行，模型可能不知道延迟工具需要搜索。
            "如果用户明确要求使用桌面、窗口、剪贴板、截图或 Computer Use，请优先使用 computer_use namespace 里的工具，不要口头声称已经操作。\n"  # 新增代码+OAuthNativeCodexBody: 保护 Computer Use 真实动作边界；如果没有这一行，模型可能伪造桌面操作结果。
            "如果不需要工具，请直接输出自然语言回答；不要再输出 decision_note/text/tool_calls 这种旧 JSON 对象。"  # 新增代码+OAuthNativeCodexBody: 禁止旧 JSON 协议混入 native 模式；如果没有这一行，解析器会收到非原生结构。
        )  # 新增代码+OAuthNativeCodexBody: instructions 拼接结束；如果没有这一行，Python 表达式不完整。
    # 新增代码+OAuthNativeCodexBody: 函数段结束，_build_native_tools_instructions 到此结束；如果没有这个边界说明，用户不容易看出提示词边界。

    def _build_native_tools_input(self, messages: list[dict[str, Any]]) -> list[dict[str, object]]:  # 新增代码+OAuthNativeComputerUseImageBackfill: 函数段开始，构造 native 模式下的 Responses input；如果没有这段函数，工具结果和截图无法按原生协议回填，本段到 return input 列表结束。
        prompt_messages = self._messages_for_text_prompt(messages)  # 新增代码+OAuthNativeComputerUseImageBackfill: 复制并清洗消息里的大图 URL；如果没有这一行，base64 截图会重复进入文本 prompt。
        content_blocks: list[dict[str, object]] = [  # 新增代码+OAuthNativeComputerUseImageBackfill: 准备 Responses content blocks；如果没有这一行，文本、工具结果和图片没有容器。
            {"type": "input_text", "text": self._build_native_tools_prompt(messages=prompt_messages)}  # 新增代码+OAuthNativeComputerUseImageBackfill: 写入精简后的对话上下文；如果没有这一行，模型看不到用户目标和历史。
        ]  # 新增代码+OAuthNativeComputerUseImageBackfill: content blocks 初始列表结束；如果没有这一行，Python 列表语法不完整。
        tool_result_call_ids = self._native_tool_result_call_ids(messages)  # 新增代码+OAuthNativeReasoningCarry: 先收集本轮确实有结果的 call_id；如果没有这一行，后续可能把没有结果的 function_call 也回传成孤儿调用。
        native_output_groups_by_call_id = self._native_output_item_groups_by_call_id(messages, tool_result_call_ids)  # 新增代码+OAuthNativeReasoningCarry: 从历史 assistant 消息里取回 reasoning/tool_search/function_call 原生 item 组；如果没有这一行，工具结果会缺少官方要求的 reasoning 上下文。
        appended_native_item_keys: set[str] = set()  # 新增代码+OAuthNativeReasoningCarry: 记录已经加入 input 的原生 item；如果没有这一行，多工具结果会重复发送同一段 reasoning 或 function_call。
        input_items: list[dict[str, object]] = []  # 新增代码+OAuthNativeFunctionOutputTopLevel: 准备 Responses 顶层 input items；如果没有这一行，function_call_output 会被错误塞进 message.content。
        for message in messages:  # 新增代码+OAuthNativeComputerUseImageBackfill: 遍历原始消息以提取 tool result；如果没有这一行，function_call_output 无法生成。
            function_call_output = self._native_function_call_output_from_message(message)  # 新增代码+OAuthNativeComputerUseImageBackfill: 尝试把 tool 消息转成 function_call_output；如果没有这一行，工具结果无法和 call_id 配对。
            if function_call_output is not None:  # 新增代码+OAuthNativeComputerUseImageBackfill: 只有合法 tool result 才追加；如果没有这一行，None 会污染 content blocks。
                call_id = str(function_call_output.get("call_id", "") or "")  # 新增代码+OAuthNativeFunctionCallCarry: 读取工具结果要配对的 call_id；如果没有这一行，无法查找上一轮原生 function_call。
                native_output_group = native_output_groups_by_call_id.get(call_id)  # 新增代码+OAuthNativeReasoningCarry: 找到同 call_id 所属的原生 output item 组；如果没有这一行，无法把 reasoning 与 function_call 一起带回。
                if native_output_group is None:  # 修改代码+OAuthNativeReasoningCarry: 没有匹配原生组时不能发送原生 output；如果没有这一行，后端会报 No tool call found 或 reasoning 断链。
                    continue  # 新增代码+OAuthNativeFunctionCallCarry: 未匹配的工具结果继续保留在文本 prompt 中，不作为原生 output 发送；如果没有这一行，请求会继续被 400 拒绝。
                for native_item in native_output_group:  # 新增代码+OAuthNativeReasoningCarry: 按上一轮原生输出顺序回放 reasoning/tool_search/function_call；如果没有这一行，只会回传工具结果而丢掉模型续轮状态。
                    native_item_key = self._native_output_item_dedupe_key(native_item)  # 新增代码+OAuthNativeReasoningCarry: 为当前原生 item 生成去重键；如果没有这一行，多工具场景会重复发送同一 item。
                    if native_item_key in appended_native_item_keys:  # 新增代码+OAuthNativeReasoningCarry: 已经发送过的原生 item 不再重复发送；如果没有这一行，第二个工具结果会重复带回 reasoning 和前一个 function_call。
                        continue  # 新增代码+OAuthNativeReasoningCarry: 跳过重复原生 item；如果没有这一行，input 会出现重复上下文。
                    input_items.append(native_item)  # 修改代码+OAuthNativeReasoningCarry: 先发送 reasoning/tool_search/function_call 原生 item；如果没有这一行，function_call_output 缺少前置上下文。
                    appended_native_item_keys.add(native_item_key)  # 新增代码+OAuthNativeReasoningCarry: 标记当前原生 item 已发送；如果没有这一行，后续无法稳定去重。
                input_items.append(function_call_output)  # 修改代码+OAuthNativeFunctionOutputTopLevel: 把工具结果作为顶层 input item 回填；如果没有这一行，真实 OAuth 后端会拒绝 content 内的 function_call_output。
        content_blocks.extend(self._responses_image_inputs_from_messages(messages))  # 新增代码+OAuthNativeComputerUseImageBackfill: 复用现有图片提取逻辑追加 input_image；如果没有这一行，Computer Use 截图会从视觉通道丢失。
        input_items.append(  # 修改代码+OAuthNativeFunctionCallCarry: 把当前用户上下文放在历史 function_call/output 之后；如果没有这一行，请求体没有当前任务文本。
            {  # 新增代码+OAuthNativeComputerUseImageBackfill: user 消息对象开始；如果没有这一行，Responses input 结构不完整。
                "role": "user",  # 新增代码+OAuthNativeComputerUseImageBackfill: 使用 user role 承载当前 agent 上下文；如果没有这一行，模型后端可能不接受该 content。
                "content": content_blocks,  # 修改代码+OAuthNativeFunctionOutputTopLevel: 这里只放 input_text/input_image 等合法内容块；如果没有这一行，前面构造的文本和截图不会发送。
            }  # 新增代码+OAuthNativeComputerUseImageBackfill: user 消息对象结束；如果没有这一行，Python 字典语法不完整。
        )  # 修改代码+OAuthNativeFunctionCallCarry: 结束 append 调用；如果没有这一行，Python 调用语法不完整。
        return input_items  # 修改代码+OAuthNativeFunctionOutputTopLevel: 返回包含用户消息和顶层工具结果的 input 列表；如果没有这一行，调用方拿不到合法 Responses input。
    # 新增代码+OAuthNativeComputerUseImageBackfill: 函数段结束，_build_native_tools_input 到此结束；如果没有这个边界说明，用户不容易看出 native 输入边界。

    def _build_native_tools_prompt(self, messages: list[dict[str, Any]]) -> str:  # 修改代码+OAuthNativeContinuationPrompt: 函数段开始，为 native 模式构造 ClaudeCode 风格的续轮提示；如果没有这段函数，模型会继续看到整段 JSON 历史并容易只返回空 reasoning，本段到 return 结束。
        latest_user_text = ""  # 修改代码+OAuthNativeContinuationPrompt: 保存最后一条用户目标；如果没有这一行，工具返回后模型可能忘记最终要回答什么。
        readable_history_lines: list[str] = []  # 修改代码+OAuthNativeContinuationPrompt: 保存给模型看的轻量历史摘要；如果没有这一行，就只能继续 dump 原始 JSON。
        tool_result_count = 0  # 修改代码+OAuthNativeContinuationPrompt: 统计本轮已经回填的工具结果数量；如果没有这一行，提示里无法明确告诉模型已有真实工具输出。
        for message in messages:  # 修改代码+OAuthNativeContinuationPrompt: 遍历清洗后的消息历史；如果没有这一行，无法提取用户目标和工具结果摘要。
            if not isinstance(message, dict):  # 修改代码+OAuthNativeContinuationPrompt: 防御异常消息类型；如果没有这一行，坏消息会让提示构造在 .get 处崩溃。
                continue  # 修改代码+OAuthNativeContinuationPrompt: 跳过不可读消息；如果没有这一行，后续逻辑会处理无效对象。
            role = str(message.get("role", "") or "")  # 修改代码+OAuthNativeContinuationPrompt: 读取消息角色；如果没有这一行，摘要无法区分用户、助手和工具。
            message_text = self._native_message_text_for_prompt(message)  # 修改代码+OAuthNativeContinuationPrompt: 提取当前消息的人类可读文本；如果没有这一行，摘要会混入内部 JSON 字段。
            if role == "user" and message_text:  # 修改代码+OAuthNativeContinuationPrompt: 用户消息用于刷新最终目标；如果没有这一行，最新用户意图不会被突出。
                latest_user_text = message_text  # 修改代码+OAuthNativeContinuationPrompt: 记录最新用户目标；如果没有这一行，后续 Original user request 会为空。
            if role == "tool":  # 修改代码+OAuthNativeContinuationPrompt: 工具消息需要单独标成真实工具结果；如果没有这一行，模型可能把工具输出当普通聊天文本。
                tool_result_count += 1  # 修改代码+OAuthNativeContinuationPrompt: 累加工具结果数量；如果没有这一行，提示无法说明已经有多少个真实工具结果。
                tool_name = str(message.get("name") or "tool").strip() or "tool"  # 修改代码+OAuthNativeContinuationPrompt: 读取工具名并兜底；如果没有这一行，工具摘要缺少来源。
                call_id = str(message.get("tool_call_id") or message.get("call_id") or "").strip()  # 修改代码+OAuthNativeContinuationPrompt: 读取工具调用 id；如果没有这一行，调试时难以确认摘要对应哪个 function_call_output。
                preview = self._native_prompt_preview(message_text)  # 修改代码+OAuthNativeContinuationPrompt: 截断工具输出预览；如果没有这一行，超长文件内容可能淹没最终回答指令。
                readable_history_lines.append(f"- tool {tool_name} ({call_id or 'unknown_call'}): {preview}")  # 修改代码+OAuthNativeContinuationPrompt: 加入工具结果摘要；如果没有这一行，模型虽然收到 function_call_output，却缺少自然语言提醒。
                continue  # 修改代码+OAuthNativeContinuationPrompt: 工具消息已经处理完毕；如果没有这一行，同一条工具结果还会被普通角色摘要重复加入。
            if role in {"user", "assistant"} and message_text:  # 修改代码+OAuthNativeContinuationPrompt: 只保留用户和有文本的助手消息；如果没有这一行，空 assistant/tool 内部结构会干扰模型。
                preview = self._native_prompt_preview(message_text)  # 修改代码+OAuthNativeContinuationPrompt: 截断普通消息预览；如果没有这一行，历史摘要可能过长。
                readable_history_lines.append(f"- {role}: {preview}")  # 修改代码+OAuthNativeContinuationPrompt: 加入可读历史行；如果没有这一行，模型看不到对话脉络。
        if not latest_user_text:  # 修改代码+OAuthNativeContinuationPrompt: 处理没有用户文本的极端情况；如果没有这一行，Original user request 会变成空白。
            latest_user_text = "(no explicit user request found)"  # 修改代码+OAuthNativeContinuationPrompt: 给缺失目标一个清晰占位；如果没有这一行，模型无法判断目标缺失是 bug 还是空输入。
        if not readable_history_lines:  # 修改代码+OAuthNativeContinuationPrompt: 处理没有可读历史的极端情况；如果没有这一行，history 区块会完全空掉。
            readable_history_lines.append("- (no readable conversation history)")  # 修改代码+OAuthNativeContinuationPrompt: 放入历史占位；如果没有这一行，提示结构不完整。
        return "\n".join(  # 修改代码+OAuthNativeContinuationPrompt: 用清晰分节返回续轮提示；如果没有这一行，调用方拿不到 native 模式上下文。
            [  # 修改代码+OAuthNativeContinuationPrompt: 开始拼接提示行列表；如果没有这一行，下面多行字符串无法组成统一 prompt。
                "Native Responses continuation context.",  # 修改代码+OAuthNativeContinuationPrompt: 说明这是 Responses 原生工具续轮上下文；如果没有这一行，模型可能按首次请求理解。
                f"Model: {self._model}",  # 修改代码+OAuthNativeContinuationPrompt: 保留模型名用于调试；如果没有这一行，日志里不容易定位请求目标模型。
                "",  # 修改代码+OAuthNativeContinuationPrompt: 空行分隔标题和用户目标；如果没有这一行，提示可读性会下降。
                "Original user request:",  # 修改代码+OAuthNativeContinuationPrompt: 明确标出最终目标；如果没有这一行，模型可能只总结工具结果而忘记回答用户。
                latest_user_text,  # 修改代码+OAuthNativeContinuationPrompt: 放入最新用户目标；如果没有这一行，模型无法知道最终该输出什么。
                "",  # 修改代码+OAuthNativeContinuationPrompt: 空行分隔用户目标和工具结果说明；如果没有这一行，提示结构会粘在一起。
                "Tool results:",  # 修改代码+OAuthNativeContinuationPrompt: 明确下面解释真实工具结果；如果没有这一行，模型可能忽略上方原生 output。
                f"- {tool_result_count} real tool result(s) are provided above as Responses function_call_output input items.",  # 修改代码+OAuthNativeContinuationPrompt: 告诉模型工具结果已经按原生协议回填；如果没有这一行，模型可能重复调用同一工具或空想结果。
                "- Use those function_call_output results directly; call another tool only if the task still requires it.",  # 修改代码+OAuthNativeContinuationPrompt: 要求优先消费工具结果；如果没有这一行，模型可能陷入不必要的工具循环。
                "",  # 修改代码+OAuthNativeContinuationPrompt: 空行分隔工具说明和历史摘要；如果没有这一行，信息块边界不清楚。
                "Readable conversation summary:",  # 修改代码+OAuthNativeContinuationPrompt: 标记轻量历史摘要；如果没有这一行，模型难以理解下面列表的作用。
                *readable_history_lines,  # 修改代码+OAuthNativeContinuationPrompt: 展开历史摘要行；如果没有这一行，用户和工具输出都不会进入文本上下文。
                "",  # 修改代码+OAuthNativeContinuationPrompt: 空行分隔历史和最终指令；如果没有这一行，最终约束不够醒目。
                "If the task is satisfied, produce a non-empty final answer. Preserve any exact final marker requested by the user.",  # 修改代码+OAuthNativeContinuationPrompt: 明确要求非空最终回答并保留验收标记；如果没有这一行，真实终端仍可能出现空白最终输出。
            ]  # 修改代码+OAuthNativeContinuationPrompt: 提示行列表结束；如果没有这一行，Python 列表语法不完整。
        )  # 修改代码+OAuthNativeContinuationPrompt: join 调用结束；如果没有这一行，Python 表达式不完整。
    # 修改代码+OAuthNativeContinuationPrompt: 函数段结束，_build_native_tools_prompt 到此结束；如果没有这个边界说明，用户不容易看出续轮提示范围。

    def _native_message_text_for_prompt(self, message: dict[str, Any]) -> str:  # 修改代码+OAuthNativeContinuationPrompt: 函数段开始，把一条内部消息压成人能读的文本；如果没有这段函数，prompt 构造会继续依赖原始 JSON，本段到 return 结束。
        content = message.get("content")  # 修改代码+OAuthNativeContinuationPrompt: 读取消息内容；如果没有这一行，无法提取用户、助手或工具文本。
        if isinstance(content, str):  # 修改代码+OAuthNativeContinuationPrompt: 处理最常见的纯文本消息；如果没有这一行，字符串会被错误地走 JSON 兜底。
            return content.strip()  # 修改代码+OAuthNativeContinuationPrompt: 返回去掉首尾空白的文本；如果没有这一行，摘要可能包含大量无意义空白。
        if isinstance(content, list):  # 修改代码+OAuthNativeContinuationPrompt: 处理多模态 content 列表；如果没有这一行，截图和文本混合消息无法摘要。
            text_parts: list[str] = []  # 修改代码+OAuthNativeContinuationPrompt: 准备收集文本片段；如果没有这一行，多段文字无法合并。
            for block in content:  # 修改代码+OAuthNativeContinuationPrompt: 遍历多模态内容块；如果没有这一行，无法逐块提取文本。
                if not isinstance(block, dict):  # 修改代码+OAuthNativeContinuationPrompt: 防御异常内容块；如果没有这一行，坏块会让 .get 调用崩溃。
                    continue  # 修改代码+OAuthNativeContinuationPrompt: 跳过不可读块；如果没有这一行，后续逻辑会处理无效对象。
                block_type = str(block.get("type", "") or "")  # 修改代码+OAuthNativeContinuationPrompt: 读取内容块类型；如果没有这一行，无法区分文本和图片。
                if block_type in {"text", "input_text", "output_text"} and isinstance(block.get("text"), str):  # 修改代码+OAuthNativeContinuationPrompt: 只抽取标准文本块；如果没有这一行，图片块可能被当成文本。
                    text_parts.append(str(block["text"]).strip())  # 修改代码+OAuthNativeContinuationPrompt: 保存文本片段；如果没有这一行，多模态文字会丢失。
                if block_type in {"image_url", "input_image"}:  # 修改代码+OAuthNativeContinuationPrompt: 对图片块放入轻量占位；如果没有这一行，模型不知道历史里曾经有截图。
                    text_parts.append("[image sent as native input_image]")  # 修改代码+OAuthNativeContinuationPrompt: 用占位替代图片 URL；如果没有这一行，base64 或 URL 可能再次污染 prompt。
            return "\n".join(part for part in text_parts if part).strip()  # 修改代码+OAuthNativeContinuationPrompt: 合并非空文本片段；如果没有这一行，多模态消息没有摘要结果。
        if content is None:  # 修改代码+OAuthNativeContinuationPrompt: 处理空内容消息；如果没有这一行，None 会被 JSON 化成无意义的 null。
            return ""  # 修改代码+OAuthNativeContinuationPrompt: 空内容返回空文本；如果没有这一行，空 assistant 消息会污染摘要。
        return json.dumps(content, ensure_ascii=False)  # 修改代码+OAuthNativeContinuationPrompt: 未知内容用 JSON 兜底；如果没有这一行，异常但有价值的内容会完全丢失。
    # 修改代码+OAuthNativeContinuationPrompt: 函数段结束，_native_message_text_for_prompt 到此结束；如果没有这个边界说明，用户不容易看出消息文本提取范围。

    def _native_prompt_preview(self, text: str, limit: int = 1200) -> str:  # 修改代码+OAuthNativeContinuationPrompt: 函数段开始，截断 prompt 历史行；如果没有这段函数，大文件工具结果可能压过最终回答指令，本段到 return 结束。
        cleaned_text = " ".join(text.split())  # 修改代码+OAuthNativeContinuationPrompt: 把连续空白压成单空格；如果没有这一行，工具输出里的换行会让摘要难读。
        if len(cleaned_text) <= limit:  # 修改代码+OAuthNativeContinuationPrompt: 短文本无需截断；如果没有这一行，所有内容都会被追加省略号。
            return cleaned_text  # 修改代码+OAuthNativeContinuationPrompt: 返回完整短文本；如果没有这一行，短消息也会进入下面截断分支。
        return f"{cleaned_text[:limit]} ... [truncated]"  # 修改代码+OAuthNativeContinuationPrompt: 截断过长文本并标记；如果没有这一行，长工具结果会撑爆续轮 prompt。
    # 修改代码+OAuthNativeContinuationPrompt: 函数段结束，_native_prompt_preview 到此结束；如果没有这个边界说明，用户不容易看出截断规则范围。

    def _native_function_call_output_from_message(self, message: dict[str, Any]) -> dict[str, object] | None:  # 新增代码+OAuthNativeComputerUseImageBackfill: 函数段开始，把内部 tool 消息转换成 Responses function_call_output；如果没有这段函数，native 模式下一轮模型无法消费工具结果，本段到返回块或 None 结束。
        if not isinstance(message, dict):  # 新增代码+OAuthNativeComputerUseImageBackfill: 防御异常消息类型；如果没有这一行，坏消息会导致 .get 报错。
            return None  # 新增代码+OAuthNativeComputerUseImageBackfill: 非字典消息不生成回填；如果没有这一行，函数会继续处理无效对象。
        if message.get("role") != "tool":  # 新增代码+OAuthNativeComputerUseImageBackfill: 只处理工具结果消息；如果没有这一行，user/assistant 消息会被误包装成工具输出。
            return None  # 新增代码+OAuthNativeComputerUseImageBackfill: 非工具消息跳过；如果没有这一行，call_id 为空时会产生坏 output。
        call_id = str(message.get("tool_call_id") or message.get("call_id") or "").strip()  # 新增代码+OAuthNativeComputerUseImageBackfill: 读取内部工具调用 id；如果没有这一行，function_call_output 无法和原生调用配对。
        if not call_id:  # 新增代码+OAuthNativeComputerUseImageBackfill: 没有 call_id 就不能生成原生工具结果；如果没有这一行，API 可能收到无法配对的 output。
            return None  # 新增代码+OAuthNativeComputerUseImageBackfill: 缺 call_id 时跳过；如果没有这一行，坏工具消息会污染请求体。
        return {  # 新增代码+OAuthNativeComputerUseImageBackfill: 返回原生 function_call_output 块；如果没有这一行，工具结果不会进入 content。
            "type": "function_call_output",  # 新增代码+OAuthNativeComputerUseImageBackfill: 标记原生工具结果类型；如果没有这一行，Responses 后端无法识别这是工具返回。
            "call_id": call_id,  # 新增代码+OAuthNativeComputerUseImageBackfill: 写入要配对的调用 id；如果没有这一行，模型无法知道结果对应哪个工具调用。
            "output": self._native_tool_output_text(message.get("content")),  # 新增代码+OAuthNativeComputerUseImageBackfill: 写入文本化工具结果；如果没有这一行，模型看不到工具返回的摘要。
        }  # 新增代码+OAuthNativeComputerUseImageBackfill: function_call_output 块结束；如果没有这一行，Python 字典语法不完整。
    # 新增代码+OAuthNativeComputerUseImageBackfill: 函数段结束，_native_function_call_output_from_message 到此结束；如果没有这个边界说明，用户不容易看出工具结果转换边界。

    def _native_tool_result_call_ids(self, messages: list[dict[str, Any]]) -> set[str]:  # 新增代码+OAuthNativeReasoningCarry: 函数段开始，收集已经有工具结果的 call_id；如果没有这段函数，后续无法避免回传孤儿 function_call，本段到 return 结束。
        call_ids: set[str] = set()  # 新增代码+OAuthNativeReasoningCarry: 准备保存工具结果 call_id；如果没有这一行，循环没有累积容器。
        for message in messages:  # 新增代码+OAuthNativeReasoningCarry: 遍历消息历史；如果没有这一行，无法找到 tool 消息。
            function_call_output = self._native_function_call_output_from_message(message)  # 新增代码+OAuthNativeReasoningCarry: 复用工具结果转换入口读取 call_id；如果没有这一行，call_id 提取规则会重复且容易分叉。
            if function_call_output is None:  # 新增代码+OAuthNativeReasoningCarry: 非工具结果消息直接跳过；如果没有这一行，None 会导致后续 .get 报错。
                continue  # 新增代码+OAuthNativeReasoningCarry: 跳过无工具结果的消息；如果没有这一行，循环会继续处理无效数据。
            call_id = str(function_call_output.get("call_id", "") or "")  # 新增代码+OAuthNativeReasoningCarry: 读取工具结果对应的 call_id；如果没有这一行，集合无法建立稳定键。
            if call_id:  # 新增代码+OAuthNativeReasoningCarry: 只有非空 call_id 才可用于配对；如果没有这一行，空字符串会污染集合。
                call_ids.add(call_id)  # 新增代码+OAuthNativeReasoningCarry: 保存已完成工具结果的 call_id；如果没有这一行，后续原生组都会被判断成无结果。
        return call_ids  # 新增代码+OAuthNativeReasoningCarry: 返回 call_id 集合；如果没有这一行，调用方拿不到配对依据。
    # 新增代码+OAuthNativeReasoningCarry: 函数段结束，_native_tool_result_call_ids 到此结束；如果没有这个边界说明，用户不容易看出 call_id 收集范围。

    def _native_output_item_groups_by_call_id(self, messages: list[dict[str, Any]], tool_result_call_ids: set[str]) -> dict[str, list[dict[str, object]]]:  # 修改代码+OAuthNativeReasoningCarry: 函数段开始，按 call_id 收集上一轮原生 reasoning/tool_search/function_call item 组；如果没有这段函数，工具结果无法按官方无状态续轮要求配回 reasoning，本段到 return 结束。
        groups_by_call_id: dict[str, list[dict[str, object]]] = {}  # 修改代码+OAuthNativeReasoningCarry: 准备 call_id 到原生 item 组的索引；如果没有这一行，后续无法快速查找匹配上下文。
        for message in messages:  # 新增代码+OAuthNativeFunctionCallCarry: 遍历消息历史；如果没有这一行，无法找到 assistant 消息里的原生 item。
            if not isinstance(message, dict):  # 新增代码+OAuthNativeFunctionCallCarry: 防御异常消息类型；如果没有这一行，坏消息会导致 .get 报错。
                continue  # 新增代码+OAuthNativeFunctionCallCarry: 跳过非字典消息；如果没有这一行，后续读取字段不安全。
            raw_items = message.get("_native_output_items", [])  # 新增代码+OAuthNativeFunctionCallCarry: 读取内部保存的 Responses 原生 output items；如果没有这一行，function_call item 会被历史消息隐藏。
            if not isinstance(raw_items, list):  # 新增代码+OAuthNativeFunctionCallCarry: 确认原生 items 是列表；如果没有这一行，异常字段可能被当作可遍历对象。
                continue  # 新增代码+OAuthNativeFunctionCallCarry: 非列表直接跳过；如果没有这一行，坏字段会污染索引。
            native_group: list[dict[str, object]] = []  # 新增代码+OAuthNativeReasoningCarry: 保存当前 assistant 响应里需要回传的原生 item；如果没有这一行，reasoning 和 function_call 无法保持同组顺序。
            group_call_ids: list[str] = []  # 新增代码+OAuthNativeReasoningCarry: 记录当前原生组里哪些 function_call 有对应工具结果；如果没有这一行，构建完组后无法建立 call_id 索引。
            for item in raw_items:  # 新增代码+OAuthNativeFunctionCallCarry: 遍历每个原生 output item；如果没有这一行，无法逐个筛选 function_call。
                if not isinstance(item, dict):  # 新增代码+OAuthNativeFunctionCallCarry: 防御异常 item 类型；如果没有这一行，坏 item 会导致 .get 报错。
                    continue  # 新增代码+OAuthNativeFunctionCallCarry: 跳过非字典 item；如果没有这一行，索引构建不稳。
                item_type = str(item.get("type", "") or "")  # 新增代码+OAuthNativeReasoningCarry: 读取原生 item 类型；如果没有这一行，无法区分 reasoning、tool_search 和 function_call。
                if item_type in {"reasoning", "tool_search_call", "tool_search_output"}:  # 新增代码+OAuthNativeReasoningCarry: 保留工具调用同轮的 reasoning 和 tool_search 证据；如果没有这一行，模型下一轮会丢掉官方要求的上下文。
                    native_group.append(dict(item))  # 新增代码+OAuthNativeReasoningCarry: 把可续轮原生 item 加入当前组；如果没有这一行，回传时只有 function_call 而没有前置状态。
                    continue  # 新增代码+OAuthNativeFunctionCallCarry: 非 function_call 不进入索引；如果没有这一行，工具结果可能和错误 item 配对。
                if item_type != "function_call":  # 修改代码+OAuthNativeReasoningCarry: 其它原生 item 暂不回传；如果没有这一行，message 等最终文本 item 可能被误塞进 input。
                    continue  # 新增代码+OAuthNativeReasoningCarry: 跳过不需要回传的原生 item；如果没有这一行，未知 item 可能污染续轮请求。
                call_id = str(item.get("call_id", "") or "")  # 新增代码+OAuthNativeFunctionCallCarry: 读取原生 function_call 的 call_id；如果没有这一行，索引没有稳定键。
                if not call_id:  # 新增代码+OAuthNativeFunctionCallCarry: 没有 call_id 的 function_call 无法配对；如果没有这一行，空键会污染多个工具结果。
                    continue  # 新增代码+OAuthNativeFunctionCallCarry: 跳过无 call_id 调用；如果没有这一行，后续 output 可能误配。
                if call_id not in tool_result_call_ids:  # 新增代码+OAuthNativeReasoningCarry: 没有工具结果的调用不能回传；如果没有这一行，后端可能看到未闭合的孤儿 function_call。
                    continue  # 新增代码+OAuthNativeReasoningCarry: 跳过尚未完成的 function_call；如果没有这一行，工具结果配对会变得不安全。
                native_group.append(dict(item))  # 修改代码+OAuthNativeReasoningCarry: 保存有结果可配对的 function_call item；如果没有这一行，function_call_output 仍找不到匹配调用。
                group_call_ids.append(call_id)  # 新增代码+OAuthNativeReasoningCarry: 记录该 call_id 属于当前原生组；如果没有这一行，组构建后无法按 call_id 查回。
            if not group_call_ids:  # 新增代码+OAuthNativeReasoningCarry: 当前 assistant 响应没有可配对工具调用时不建立索引；如果没有这一行，纯 reasoning 可能被错误回传。
                continue  # 新增代码+OAuthNativeReasoningCarry: 跳过无可配对调用的原生组；如果没有这一行，groups 可能出现无意义条目。
            for call_id in group_call_ids:  # 新增代码+OAuthNativeReasoningCarry: 为组内每个 call_id 建立同一组索引；如果没有这一行，多工具结果只有第一个能找到 reasoning 组。
                groups_by_call_id[call_id] = list(native_group)  # 修改代码+OAuthNativeReasoningCarry: 保存原生 item 组副本；如果没有这一行，下一轮 input 无法按 call_id 回传完整上下文。
        return groups_by_call_id  # 修改代码+OAuthNativeReasoningCarry: 返回 call_id 到原生 item 组索引；如果没有这一行，调用方拿不到任何匹配信息。
    # 修改代码+OAuthNativeReasoningCarry: 函数段结束，_native_output_item_groups_by_call_id 到此结束；如果没有这个边界说明，用户不容易看出索引范围。

    def _native_output_item_dedupe_key(self, item: dict[str, object]) -> str:  # 新增代码+OAuthNativeReasoningCarry: 函数段开始，为原生 output item 生成稳定去重键；如果没有这段函数，多工具结果会重复回传同一原生上下文，本段到 return 结束。
        item_type = str(item.get("type", "") or "")  # 新增代码+OAuthNativeReasoningCarry: 读取 item 类型；如果没有这一行，去重键无法区分 reasoning 和 function_call。
        stable_id = str(item.get("id") or item.get("call_id") or "")  # 新增代码+OAuthNativeReasoningCarry: 优先使用 OpenAI item id 或 call_id；如果没有这一行，同一 item 多次出现不容易识别。
        if stable_id:  # 新增代码+OAuthNativeReasoningCarry: 有稳定 id 时使用轻量键；如果没有这一行，所有 item 都会走较重的 JSON 序列化。
            return f"{item_type}:{stable_id}"  # 新增代码+OAuthNativeReasoningCarry: 返回类型和 id 组成的键；如果没有这一行，不同类型同 id 可能互相误去重。
        return f"{item_type}:{json.dumps(item, ensure_ascii=False, sort_keys=True)}"  # 新增代码+OAuthNativeReasoningCarry: 无稳定 id 时用排序 JSON 兜底；如果没有这一行，罕见 item 会无法去重。
    # 新增代码+OAuthNativeReasoningCarry: 函数段结束，_native_output_item_dedupe_key 到此结束；如果没有这个边界说明，用户不容易看出去重逻辑范围。

    def _native_tool_output_text(self, content: Any) -> str:  # 新增代码+OAuthNativeComputerUseImageBackfill: 函数段开始，把内部 tool content 压成 Responses output 字符串；如果没有这段函数，多模态工具结果会把图片 JSON 当文本塞回模型，本段到 return 字符串结束。
        if isinstance(content, str):  # 新增代码+OAuthNativeComputerUseImageBackfill: 普通字符串工具结果直接使用；如果没有这一行，最常见工具输出会被 JSON 序列化成带引号文本。
            return content  # 新增代码+OAuthNativeComputerUseImageBackfill: 返回原始字符串；如果没有这一行，工具文本摘要会丢失。
        if isinstance(content, list):  # 新增代码+OAuthNativeComputerUseImageBackfill: 多模态内容需要只提取文本块；如果没有这一行，图片块会被误写进 output 文本。
            text_parts: list[str] = []  # 新增代码+OAuthNativeComputerUseImageBackfill: 准备累积文本片段；如果没有这一行，多个文本块无法合并。
            for block in content:  # 新增代码+OAuthNativeComputerUseImageBackfill: 遍历 content 块；如果没有这一行，无法逐个提取文本。
                if isinstance(block, dict) and block.get("type") in {"text", "input_text", "output_text"} and isinstance(block.get("text"), str):  # 新增代码+OAuthNativeComputerUseImageBackfill: 只接受标准文本块；如果没有这一行，图片或坏块会污染输出。
                    text_parts.append(str(block["text"]))  # 新增代码+OAuthNativeComputerUseImageBackfill: 保存文本内容；如果没有这一行，function_call_output 会变空。
            if text_parts:  # 新增代码+OAuthNativeComputerUseImageBackfill: 有文本时优先返回文本摘要；如果没有这一行，下面会把整个 content JSON 化。
                return "\n".join(text_parts)  # 新增代码+OAuthNativeComputerUseImageBackfill: 合并多段文本；如果没有这一行，模型看不到完整工具结果摘要。
        return json.dumps(content, ensure_ascii=False)  # 新增代码+OAuthNativeComputerUseImageBackfill: 兜底把未知内容 JSON 化；如果没有这一行，异常工具结果会完全丢失。
    # 新增代码+OAuthNativeComputerUseImageBackfill: 函数段结束，_native_tool_output_text 到此结束；如果没有这个边界说明，用户不容易看出文本化规则。

    def _build_instructions(self) -> str:  # 作用: 构造 Codex 后端要求的顶层 instructions
        return (  # 修改代码+PromptContextV1: 返回 Codex 后端顶层 instructions；若省略: Codex 模型不知道如何输出 learning_agent 可解析的 JSON
            "你是 learning_agent 的模型适配器，负责把成熟 coding agent 的判断转换成结构化 JSON 输出。\n"  # 修改代码+PromptContextV1: 对齐成熟 agent 身份；若省略: 适配器提示词仍停留在旧定位
            "你不是文件执行器、命令执行器或浏览器；如果需要外部动作，只能请求 learning_agent 调用工具，不要自己声称已经执行。\n"  # 修改代码+PromptContextV1: 强化工具边界；若省略: 模型可能伪造执行结果
            "你必须根据 input 里的 messages 和 tools 判断下一步应该直接回答，还是请求 learning_agent 调用工具。\n"  # 修改代码+PromptContextV1: 保留工具选择职责；若省略: 模型可能忽略工具列表
            "你必须在 decision_note 里用一句中文说明本轮为什么直接回答或为什么选择这些工具；这只是给用户看的决策说明，不要写隐藏思维链。\n"  # 修改代码+PromptContextV1: 保留可学习决策说明；若省略: 用户难以理解 agent 行动原因
            "如果用户明确要求使用工具、真实 Chrome、桌面可见浏览器、当前浏览器或登录态，你不能用普通回答、web_search、fetch_url 或独立 Chromium 替代；必须请求对应工作流工具。\n"  # 修改代码+真实浏览器误判: 只把真实 Chrome/桌面可见/当前浏览器/登录态视为高风险真实 profile 请求；若没有这行代码，普通 real browser automation 测试会被误导到 real_chrome workflow
            "如果需要工具，请只在 tool_calls 里写工具名和参数，不要自己执行工具；每个 arguments 只能包含该工具自己的参数。\n"  # 修改代码+OutputProtocolV2: 保留工具调用边界并强调专属参数；若没有这行代码，OAuth/API 模型可能继续按旧共享参数协议输出无关字段
            "工具参数必须使用对应工具 JSON schema 里的参数名；不要输出不属于当前工具的参数。\n"  # 修改代码+OutputProtocolV2: 移除旧的无关参数写 null 规则；若没有这行代码，OAuth/API 模型会同时收到新旧冲突指令并继续产生参数串味
            "如果不需要工具，请把最终回答写入 text，并让 tool_calls 为空数组。\n"  # 修改代码+PromptContextV1: 保留直接回答格式；若省略: 无工具回答可能缺少 text
            "你只能输出一个 JSON 对象，根字段只能包含 decision_note、text、tool_calls，不能输出 Markdown、解释文字或代码块。"  # 修改代码+PromptContextV1: 保留解析器契约；若省略: Python 解析层可能无法解析模型输出
        )  # 修改代码+PromptContextV1: instructions 拼接结束；若省略: Python 表达式无法闭合

    def _build_responses_input(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> list[dict[str, object]]:  # 修改代码+ComputerUseVisionLoop：函数段开始，构造 Responses API input 并保留原生图片输入；如果没有这个函数段，Computer Use 截图会退化成纯文本，作者意图是让模型主循环真正看到屏幕像素，本段到 input 列表返回结束。
        prompt_messages = self._messages_for_text_prompt(messages)  # 修改代码+ComputerUseVisionLoop：生成给文本 prompt 使用的消息副本；如果没有这一行，截图 base64 会重复塞进文本 prompt 浪费 token。
        content_blocks: list[dict[str, object]] = [  # 修改代码+ComputerUseVisionLoop：先准备 Responses content 数组；如果没有这一行，后续文本和图片块没有容器。
            {"type": "input_text", "text": self._build_prompt(messages=prompt_messages, tools=tools)}  # 修改代码+ComputerUseVisionLoop：把工具 schema 和精简后的 messages 放进文本块；如果没有这一行，模型会看不到工具清单和对话历史。
        ]  # 修改代码+ComputerUseVisionLoop：文本块列表初始化结束；如果没有这一行，Python 列表语法不完整。
        content_blocks.extend(self._responses_image_inputs_from_messages(messages))  # 修改代码+ComputerUseVisionLoop：追加从消息中提取出的原生图片块；如果没有这一行，真实截图不会进入视觉通道。
        return [  # 修改代码+ComputerUseVisionLoop：返回 Responses API 需要的 input 列表；如果没有这一行，调用方拿不到请求输入。
            {  # 修改代码+ComputerUseVisionLoop：user 消息对象开始；如果没有这一行，Responses input 结构不完整。
                "role": "user",  # 修改代码+ComputerUseVisionLoop：使用 user role 承载 agent 上下文；如果没有这一行，模型服务无法识别输入身份。
                "content": content_blocks,  # 修改代码+ComputerUseVisionLoop：把文本 prompt 和图片块一起交给模型；如果没有这一行，前面构造的多模态输入不会被发送。
            }  # 修改代码+ComputerUseVisionLoop：user 消息对象结束；如果没有这一行，Python 字典语法不完整。
        ]  # 修改代码+ComputerUseVisionLoop：Responses input 列表结束；如果没有这一行，Python 列表语法不完整。

    def _messages_for_text_prompt(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:  # 新增代码+ComputerUseVisionLoop：函数段开始，生成不携带大图 base64 的文本 prompt 消息；如果没有这个函数段，视觉截图会同时污染文本和图片通道，作者意图是让文字只描述结构、图片走视觉通道，本段到返回清洗副本结束。
        prompt_messages = copy.deepcopy(messages)  # 新增代码+ComputerUseVisionLoop：深拷贝 messages，避免清洗 prompt 时改坏主循环原始消息；如果没有这一行，后续轮次可能丢失真实图片 URL。
        for message in prompt_messages:  # 新增代码+ComputerUseVisionLoop：遍历每条消息；如果没有这一行，无法逐条清洗图片块。
            if not isinstance(message, dict):  # 新增代码+ComputerUseVisionLoop：防御异常消息类型；如果没有这一行，坏消息可能让 OAuth 请求构造崩溃。
                continue  # 新增代码+ComputerUseVisionLoop：跳过非字典消息；如果没有这一行，异常消息会继续进入 .get 调用。
            message.pop("_native_output_items", None)  # 新增代码+OAuthNativeFunctionCallCarry: 文本 prompt 不展示内部原生 item 证据；如果没有这一行，function_call JSON 会重复塞进自然语言上下文。
            content = message.get("content")  # 新增代码+ComputerUseVisionLoop：读取消息内容字段；如果没有这一行，后续无法判断是否包含图片块。
            if not isinstance(content, list):  # 新增代码+ComputerUseVisionLoop：只有多模态列表才需要清洗；如果没有这一行，字符串 content 会被当成可遍历块误处理。
                continue  # 新增代码+ComputerUseVisionLoop：跳过普通文本 content；如果没有这一行，普通消息会进入错误分支。
            for block in content:  # 新增代码+ComputerUseVisionLoop：遍历多模态内容块；如果没有这一行，无法定位 image_url 或 input_image。
                if not isinstance(block, dict):  # 新增代码+ComputerUseVisionLoop：防御异常内容块；如果没有这一行，坏块会让 .get 调用报错。
                    continue  # 新增代码+ComputerUseVisionLoop：跳过非字典块；如果没有这一行，清洗逻辑不够健壮。
                self._redact_image_block_for_text_prompt(block)  # 新增代码+ComputerUseVisionLoop：把图片块里的大 URL 替换成占位说明；如果没有这一行，base64 截图仍会塞进文本 prompt。
        return prompt_messages  # 新增代码+ComputerUseVisionLoop：返回清洗后的消息副本；如果没有这一行，_build_responses_input 无法构造轻量文本 prompt。

    def _redact_image_block_for_text_prompt(self, block: dict[str, Any]) -> None:  # 新增代码+ComputerUseVisionLoop：函数段开始，清洗单个图片内容块里的真实图片 URL；如果没有这个函数段，图片 data URL 会重复进入文本 prompt，作者意图是降低 token 噪声并保留图片存在事实，本段到函数自然结束。
        block_type = str(block.get("type", "") or "")  # 新增代码+ComputerUseVisionLoop：读取内容块类型；如果没有这一行，无法区分图片块和普通文本块。
        if block_type == "image_url":  # 新增代码+ComputerUseVisionLoop：处理 agent.py 注入的 OpenAI-compatible 图片块；如果没有这一行，Computer Use 截图不会被清洗。
            raw_image_url = block.get("image_url")  # 新增代码+ComputerUseVisionLoop：读取 image_url 字段；如果没有这一行，无法找到真实 URL 所在位置。
            if isinstance(raw_image_url, dict):  # 新增代码+ComputerUseVisionLoop：处理标准 {"url": "..."} 结构；如果没有这一行，常规图片块无法清洗。
                raw_image_url["url"] = "[image omitted from text prompt: sent as native input_image]"  # 新增代码+ComputerUseVisionLoop：用占位文本替换大图 URL；如果没有这一行，base64 会重复污染 prompt。
            else:  # 新增代码+ComputerUseVisionLoop：兼容 image_url 不是字典的异常形态；如果没有这一行，非标准块会保留大 URL。
                block["image_url"] = {"url": "[image omitted from text prompt: sent as native input_image]"}  # 新增代码+ComputerUseVisionLoop：把异常图片字段规范成占位字典；如果没有这一行，文本 prompt 仍可能泄漏图片数据。
        if block_type == "input_image":  # 新增代码+ComputerUseVisionLoop：处理已经是 Responses input_image 的块；如果没有这一行，未来复用 input_image 时仍会重复进文本。
            block["image_url"] = "[image omitted from text prompt: sent as native input_image]"  # 新增代码+ComputerUseVisionLoop：清洗 input_image 的 image_url 字段；如果没有这一行，原生图片 URL 会被 JSON 文本重复展示。

    def _responses_image_inputs_from_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, object]]:  # 新增代码+ComputerUseVisionLoop：函数段开始，从 agent messages 中提取 Responses 原生图片输入；如果没有这个函数段，工具观察截图无法送进模型视觉通道，作者意图是复用 ClaudeCode 式 image block 反馈，本段到返回图片块列表结束。
        image_inputs: list[dict[str, object]] = []  # 新增代码+ComputerUseVisionLoop：准备保存原生 input_image 块；如果没有这一行，无法累积多张截图。
        for message in messages:  # 新增代码+ComputerUseVisionLoop：遍历所有对话消息；如果没有这一行，只能处理固定位置的图片。
            if not isinstance(message, dict):  # 新增代码+ComputerUseVisionLoop：防御异常消息类型；如果没有这一行，坏消息会打断整次模型请求。
                continue  # 新增代码+ComputerUseVisionLoop：跳过非字典消息；如果没有这一行，后续 .get 调用可能报错。
            content = message.get("content")  # 新增代码+ComputerUseVisionLoop：读取消息内容；如果没有这一行，无法找到图片块所在数组。
            if not isinstance(content, list):  # 新增代码+ComputerUseVisionLoop：只从多模态 content 列表提取图片；如果没有这一行，普通字符串消息会被误遍历。
                continue  # 新增代码+ComputerUseVisionLoop：跳过普通文本消息；如果没有这一行，提取逻辑会处理错误数据形态。
            for block in content:  # 新增代码+ComputerUseVisionLoop：遍历当前消息的每个内容块；如果没有这一行，多图观察无法被逐个提取。
                if not isinstance(block, dict):  # 新增代码+ComputerUseVisionLoop：防御异常内容块；如果没有这一行，坏块会导致 .get 报错。
                    continue  # 新增代码+ComputerUseVisionLoop：跳过非字典块；如果没有这一行，异常块会中断图片提取。
                image_input = self._responses_image_input_from_block(block)  # 新增代码+ComputerUseVisionLoop：把兼容图片块转换成 Responses input_image；如果没有这一行，提取逻辑会和格式细节耦合在一起。
                if image_input is not None:  # 新增代码+ComputerUseVisionLoop：只有合法图片 URL 才追加；如果没有这一行，None 会污染 content blocks。
                    image_inputs.append(image_input)  # 新增代码+ComputerUseVisionLoop：保存当前图片输入块；如果没有这一行，模型仍然收不到这张截图。
        return image_inputs  # 新增代码+ComputerUseVisionLoop：返回所有原生图片输入；如果没有这一行，调用方无法追加图片块。

    def _responses_image_input_from_block(self, block: dict[str, Any]) -> dict[str, object] | None:  # 新增代码+ComputerUseVisionLoop：函数段开始，把单个图片内容块转换成 Responses input_image；如果没有这个函数段，image_url/input_image 兼容逻辑会散落，作者意图是让视觉输入边界集中可测，本段到返回构造结果结束。
        block_type = str(block.get("type", "") or "")  # 新增代码+ComputerUseVisionLoop：读取内容块类型；如果没有这一行，无法判断当前块是否是图片。
        raw_url = ""  # 新增代码+ComputerUseVisionLoop：初始化图片 URL；如果没有这一行，后续分支可能引用未定义变量。
        raw_detail = ""  # 新增代码+ComputerUseVisionLoop：初始化图片清晰度提示；如果没有这一行，后续无法安全保留 high/low/auto。
        if block_type == "image_url":  # 新增代码+ComputerUseVisionLoop：处理 agent 主循环使用的图片块格式；如果没有这一行，Computer Use 截图不会被提取。
            raw_image_url = block.get("image_url")  # 新增代码+ComputerUseVisionLoop：读取 image_url 字段；如果没有这一行，无法拿到 data URL。
            if isinstance(raw_image_url, dict):  # 新增代码+ComputerUseVisionLoop：处理标准字典格式；如果没有这一行，常规图片块会被跳过。
                raw_url = str(raw_image_url.get("url", "") or "").strip()  # 新增代码+ComputerUseVisionLoop：读取并清理真实图片 URL；如果没有这一行，Responses input_image 没有 image_url。
                raw_detail = str(raw_image_url.get("detail", "") or "").strip()  # 新增代码+ComputerUseVisionLoop：读取 detail 提示；如果没有这一行，high 观察精度会丢失。
            else:  # 新增代码+ComputerUseVisionLoop：兼容 image_url 直接是字符串的情况；如果没有这一行，非标准但可恢复的图片块会被丢掉。
                raw_url = str(raw_image_url or "").strip()  # 新增代码+ComputerUseVisionLoop：把字符串形态转成 URL；如果没有这一行，兼容分支拿不到图片地址。
        if block_type == "input_image":  # 新增代码+ComputerUseVisionLoop：处理已经是 Responses input_image 的内容块；如果没有这一行，未来上游直接传 input_image 时无法复用。
            raw_url = str(block.get("image_url") or block.get("url") or "").strip()  # 新增代码+ComputerUseVisionLoop：读取 input_image 的图片地址；如果没有这一行，原生图片块无法保留。
            raw_detail = str(block.get("detail", "") or "").strip()  # 新增代码+ComputerUseVisionLoop：读取 input_image 的 detail；如果没有这一行，图片清晰度提示会丢失。
        if not self._responses_image_url_is_allowed(raw_url):  # 新增代码+ComputerUseVisionLoop：只允许 data/http/https 图片 URL；如果没有这一行，空字符串或异常协议可能发给模型 API。
            return None  # 新增代码+ComputerUseVisionLoop：非法或空 URL 不生成图片块；如果没有这一行，API 请求可能因为无效 image_url 失败。
        image_input: dict[str, object] = {"type": "input_image", "image_url": raw_url}  # 新增代码+ComputerUseVisionLoop：构造 Responses 原生图片输入；如果没有这一行，模型视觉通道没有实际数据。
        if raw_detail in {"low", "high", "auto"}:  # 新增代码+ComputerUseVisionLoop：只保留 Responses 常见合法 detail 值；如果没有这一行，任意字符串可能污染请求体。
            image_input["detail"] = raw_detail  # 新增代码+ComputerUseVisionLoop：保留截图观察精度；如果没有这一行，高精度截图可能被默认降级。
        return image_input  # 新增代码+ComputerUseVisionLoop：返回转换后的图片输入；如果没有这一行，调用方拿不到可发送的 input_image。

    def _responses_image_url_is_allowed(self, raw_url: str) -> bool:  # 新增代码+ComputerUseVisionLoop：函数段开始，校验图片 URL 是否适合发给 Responses API；如果没有这个函数段，坏 URL 可能导致模型请求失败，作者意图是让视觉输入只接收明确图片来源，本段到布尔返回结束。
        if not raw_url:  # 新增代码+ComputerUseVisionLoop：拒绝空 URL；如果没有这一行，空图片会进入 API 请求。
            return False  # 新增代码+ComputerUseVisionLoop：空 URL 不允许发送；如果没有这一行，模型 API 可能返回参数错误。
        return raw_url.startswith("data:image/") or raw_url.startswith("http://") or raw_url.startswith("https://")  # 新增代码+ComputerUseVisionLoop：只允许 data 图片和网络图片 URL；如果没有这一行，本地路径或占位文本可能被误发给模型。
    def _build_prompt(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> str:  # 作用: 构造给 GPT-5.5 的模型适配器提示词
        return (  # 作用: 返回完整提示词
            f"目标模型名：{json.dumps(self._model, ensure_ascii=False)}\n\n"  # 作用: 放入模型名
            "可用工具 JSON schema：\n"  # 作用: 以下区域放工具定义
            f"{json.dumps(tools, ensure_ascii=False, indent=2)}\n\n"  # 作用: 序列化工具 schema
            "当前对话 messages：\n"  # 作用: 以下区域放历史消息
            f"{json.dumps(messages, ensure_ascii=False, indent=2)}\n"  # 作用: 序列化 messages
        )  # 作用: prompt 拼接结束

    def _tokens_from_response(self, payload: dict[str, object], fallback_account_id: str | None) -> CodexOAuthTokens:  # 作用: 把 OAuth token 响应转成数据对象
        access_token = str(payload.get("access_token", "")).strip()  # 作用: 提取 access_token
        refresh_token = str(payload.get("refresh_token", "")).strip()  # 作用: 提取 refresh_token
        id_token = str(payload.get("id_token", "")).strip()  # 作用: 提取 id_token
        if not access_token or not refresh_token:  # 作用: 如果关键 token 缺失
            raise RuntimeError("OAuth token 响应缺少 access_token 或 refresh_token。")  # 作用: 抛出清晰错误
        expires_in = int(payload.get("expires_in", 3600) or 3600)  # 作用: 提取有效期，缺失按 1 小时
        account_id = self._extract_account_id(id_token) or self._extract_account_id(access_token) or fallback_account_id  # 作用: 尝试从 JWT 中提取账号 id
        return CodexOAuthTokens(  # 作用: 返回 token 数据对象
            access_token=access_token,  # 作用: 保存 access_token
            refresh_token=refresh_token,  # 作用: 保存 refresh_token
            expires_at=self._now_ms() + expires_in * 1000,  # 作用: 计算毫秒级过期时间
            account_id=account_id,  # 作用: 保存账号 id
            id_token=id_token,  # 作用: 保存 id_token
        )  # 作用: token 数据对象结束

    def _post_json_request(self, url: str, headers: dict[str, str], body: dict[str, object]) -> dict[str, object]:  # 作用: 使用标准库执行真实 HTTP POST
        if url.endswith("/oauth/token"):  # 作用: OAuth token 端点要求表单编码
            raw_body = urllib.parse.urlencode({key: str(value) for key, value in body.items()}).encode("utf-8")  # 作用: 编码表单请求体
        else:  # 作用: 其他端点使用 JSON
            raw_body = json.dumps(body, ensure_ascii=False).encode("utf-8")  # 作用: 编码 JSON 请求体
        request = urllib.request.Request(url=url, data=raw_body, headers=headers, method="POST")  # 作用: 创建 HTTP 请求对象
        try:  # 修改代码+OAuth流读取: 捕获 HTTP 状态码错误；若省略: 4xx/5xx 会变成难懂的底层异常
            with urllib.request.urlopen(request, timeout=120) as response:  # 修改代码+OAuth流读取: 发送请求并拿到响应对象；若省略: 无法访问 Codex/OAuth HTTP 端点
                if body.get("stream") is True:  # 新增代码+OAuth流读取: 流式请求先走逐行 SSE 读取；若省略: 会继续整包 read 并可能卡住不返回
                    return self._read_sse_response_until_done(response)  # 新增代码+OAuth流读取: 读到 done 事件就返回；若省略: 真实浏览器查询前模型响应可能长期阻塞
                text = response.read().decode("utf-8", errors="replace")  # 修改代码+OAuth流读取: 非流式响应仍整包读取文本；若省略: OAuth token 等普通 JSON 响应无法解析
        except urllib.error.HTTPError as error:  # 作用: 捕获 4xx/5xx 错误
            text = error.read().decode("utf-8", errors="replace")  # 作用: 读取错误响应体
            raise RuntimeError(f"HTTP {error.code}: {text[:1000]}") from error  # 作用: 抛出带状态码和截断响应体的错误
        return json.loads(text)  # 作用: 非流式时直接解析 JSON

    def _read_sse_response_until_done(self, response: Any) -> dict[str, object]:  # 新增代码+OAuth流读取: 按行读取 Codex SSE 响应直到完成事件；若省略: stream=true 会等连接关闭导致 agent 卡住
        raw_lines: list[str] = []  # 新增代码+OAuth流读取: 收集已读取的 SSE 文本行；若省略: 后续无法复用现有 SSE 解析器
        deadline = self._monotonic() + self._sse_read_timeout_seconds  # 新增代码+OAuthSseDeadline: 计算本次 SSE 读取的总截止时间；如果没有这行代码，心跳流可以无限延长模型调用。
        while True:  # 新增代码+OAuth流读取: 持续读取 SSE 行；若省略: 只能读取第一行或完全不读取
            if self._monotonic() >= deadline:  # 新增代码+OAuthSseDeadline: 每次读下一行前检查总时长；如果没有这行代码，持续心跳或未知事件会绕过 socket timeout。
                raise TimeoutError(f"SSE stream read timed out after {self._sse_read_timeout_seconds} seconds without a completion event")  # 新增代码+OAuthSseDeadline: 抛出可被现有 OAuth timeout 文案识别的错误；如果没有这行代码，真实终端只会外部超时。
            line_bytes = response.readline()  # 新增代码+OAuth流读取: 从 HTTPResponse 读取一行；若省略: 无法在长连接里按事件边界前进
            if not line_bytes:  # 新增代码+OAuth流读取: 如果服务器关闭连接或测试替身到 EOF；若省略: 空内容会被当成一行继续循环
                break  # 新增代码+OAuth流读取: 结束读取循环；若省略: EOF 后可能进入无意义循环
            line_text = line_bytes.decode("utf-8", errors="replace") if isinstance(line_bytes, bytes) else str(line_bytes)  # 新增代码+OAuth流读取: 把字节行转成文本；若省略: SSE JSON 无法按字符串解析
            raw_lines.append(line_text)  # 新增代码+OAuth流读取: 保存当前行给统一解析器；若省略: 读到了事件也无法产出 output_text
            stripped = line_text.strip()  # 新增代码+OAuth流读取: 去掉空白方便识别 data 行；若省略: 前后空白可能影响事件判断
            if not stripped.startswith("data:"):  # 新增代码+OAuth流读取: 跳过 event、id、retry 和空行；若省略: 非 data 行会被错误拿去解析 JSON
                continue  # 新增代码+OAuth流读取: 继续等待真正 payload 行；若省略: 非 data 行会打断读取
            data = stripped.removeprefix("data:").strip()  # 新增代码+OAuth流读取: 取出 SSE payload；若省略: JSON 前缀会导致解析失败
            if data == "[DONE]":  # 新增代码+OAuth流读取: 识别 Codex SSE 结束标记；若省略: 只发 [DONE] 的流会继续等 EOF
                break  # 新增代码+OAuth流读取: 收到结束标记后停止读取；若省略: agent 会继续阻塞等待更多行
            try:  # 新增代码+OAuth流读取: 尝试解析 payload JSON；若省略: 坏事件会让整个请求失败
                event = json.loads(data)  # 新增代码+OAuth流读取: 解析 SSE 事件对象；若省略: 无法判断是否已经完成
            except json.JSONDecodeError:  # 新增代码+OAuth流读取: 忽略非 JSON data；若省略: 某些注释或兼容事件会中断请求
                continue  # 新增代码+OAuth流读取: 跳过坏事件继续读；若省略: 单个坏事件会导致模型调用失败
            event_type = event.get("type")  # 新增代码+OAuth流读取: 读取事件类型；若省略: 无法知道是不是完成事件
            if event_type in {"response.output_text.done", "response.completed"}:  # 新增代码+OAuth流读取: 完整文本或完整响应到达即可返回；若省略: 仍会等长连接关闭
                break  # 新增代码+OAuth流读取: 提前结束读取；若省略: 用户会继续看到终端无响应
        return self._parse_sse_response("".join(raw_lines))  # 新增代码+OAuth流读取: 复用现有 SSE 解析逻辑返回结构化响应；若省略: 调用方拿不到模型输出

    @staticmethod  # 作用: SSE 解析不依赖实例状态
    def _parse_sse_response(raw_stream: str) -> dict[str, object]:  # 作用: 解析 Codex Responses 流式返回
        return ChatGptCodexSseClient.parse_sse_text_to_response(raw_stream)  # 修改代码+DirectChatGptSseClient: 旧 wrapper 立即委托共享 SSE parser；如果没有这行代码，GUI 直连和旧 OAuth wrapper 会继续解析分叉。
        output_chunks: list[str] = []  # 作用: 收集 output_text.delta 文本片段
        output_items: list[dict[str, Any]] = []  # 新增代码+OAuthNativeSseParser: 收集 Responses 原生 output items；如果没有这一行，function_call/tool_search item 会被丢掉。
        pending_items: dict[str, dict[str, Any]] = {}  # 新增代码+OAuthNativeSseParser: 暂存 output_item.added 的 item；如果没有这一行，arguments delta 没有可回填对象。
        argument_chunks: dict[str, list[str]] = {}  # 新增代码+OAuthNativeSseParser: 按 item_id 收集 function_call arguments 分片；如果没有这一行，流式参数会保持空字符串。
        completed_response: dict[str, object] | None = None  # 作用: 保存 response.completed 完整响应作为兜底
        for raw_line in raw_stream.splitlines():  # 作用: 按行遍历 SSE 文本
            line = raw_line.strip()  # 作用: 去掉首尾空白
            if not line.startswith("data:"):  # 作用: 非 data 行不含事件 payload
                continue  # 作用: 跳过 event、空行等
            data = line.removeprefix("data:").strip()  # 作用: 去掉 data: 前缀
            if not data or data == "[DONE]":  # 作用: 跳过空 payload 和结束标记
                continue  # 作用: 继续处理下一行
            try:  # 作用: 捕获坏 JSON 事件
                event = json.loads(data)  # 作用: 解析事件 JSON
            except json.JSONDecodeError:  # 作用: 如果事件不是合法 JSON
                continue  # 作用: 跳过坏事件
            event_type = event.get("type")  # 作用: 读取事件类型
            if event_type == "response.output_text.delta" and isinstance(event.get("delta"), str):  # 作用: 如果是文本增量事件
                output_chunks.append(str(event["delta"]))  # 作用: 追加增量文本
            if event_type == "response.output_text.done" and isinstance(event.get("text"), str):  # 作用: 如果后端直接给完整文本
                output_chunks = [str(event["text"])]  # 修改代码+OAuthNativeSseParser: 保存完整文本而不是立刻返回；如果没有这一行，前面已收集的 native item 会被忽略。
            if event_type == "response.output_item.added" and isinstance(event.get("item"), dict):  # 新增代码+OAuthNativeSseParser: 捕获原生 output item 创建事件；如果没有这一行，后续 arguments delta 没有 item 上下文。
                item = copy.deepcopy(event["item"])  # 新增代码+OAuthNativeSseParser: 深拷贝 item 作为可修改副本；如果没有这一行，回填 arguments 可能污染事件原文。
                item_id = str(item.get("id") or event.get("item_id") or "")  # 新增代码+OAuthNativeSseParser: 读取 item id；如果没有这一行，分片参数无法按 item 归属。
                if item_id:  # 新增代码+OAuthNativeSseParser: 只有有 id 的 item 才暂存；如果没有这一行，空 key 会把多个 item 混在一起。
                    pending_items[item_id] = item  # 新增代码+OAuthNativeSseParser: 保存待完成 item；如果没有这一行，output_item.done 缺字段时无法补齐。
            if event_type == "response.function_call_arguments.delta" and isinstance(event.get("delta"), str):  # 新增代码+OAuthNativeSseParser: 捕获 function_call 参数增量；如果没有这一行，streaming 参数无法拼接。
                item_id = str(event.get("item_id") or event.get("output_item_id") or "")  # 新增代码+OAuthNativeSseParser: 读取参数所属 item id；如果没有这一行，参数分片无法归类。
                if item_id:  # 新增代码+OAuthNativeSseParser: 只有有 item_id 才记录；如果没有这一行，空 id 会把不同工具参数混在一起。
                    argument_chunks.setdefault(item_id, []).append(str(event["delta"]))  # 新增代码+OAuthNativeSseParser: 追加当前参数分片；如果没有这一行，最终 arguments 仍为空。
            if event_type == "response.function_call_arguments.done" and isinstance(event.get("arguments"), str):  # 新增代码+OAuthNativeSseParser: 捕获后端直接给完整 arguments 的事件；如果没有这一行，done 事件里的完整参数会被忽略。
                item_id = str(event.get("item_id") or event.get("output_item_id") or "")  # 新增代码+OAuthNativeSseParser: 读取完整参数所属 item id；如果没有这一行，无法覆盖前面的 delta。
                if item_id:  # 新增代码+OAuthNativeSseParser: 只有有 item_id 才覆盖；如果没有这一行，坏事件可能污染空 key。
                    argument_chunks[item_id] = [str(event["arguments"])]  # 新增代码+OAuthNativeSseParser: 用完整 arguments 覆盖分片；如果没有这一行，delta 不完整时无法以 done 为准。
            if event_type == "response.output_item.done" and isinstance(event.get("item"), dict):  # 新增代码+OAuthNativeSseParser: 捕获原生 output item 完成事件；如果没有这一行，function_call 不会进入 output 数组。
                item = copy.deepcopy(event["item"])  # 新增代码+OAuthNativeSseParser: 深拷贝完成 item 用于回填；如果没有这一行，直接修改事件对象不安全。
                item_id = str(item.get("id") or event.get("item_id") or "")  # 新增代码+OAuthNativeSseParser: 读取完成 item id；如果没有这一行，无法找到对应参数分片。
                if item_id and not item.get("arguments") and item_id in argument_chunks:  # 新增代码+OAuthNativeSseParser: 当完成 item 没带 arguments 时用分片补齐；如果没有这一行，工具参数会丢失。
                    item["arguments"] = "".join(argument_chunks[item_id])  # 新增代码+OAuthNativeSseParser: 把参数分片拼成完整 JSON 字符串；如果没有这一行，parser 会得到空参数。
                if item_id and item_id in pending_items:  # 新增代码+OAuthNativeSseParser: 如果之前有 added 快照，就合并缺失字段；如果没有这一行，done item 可能丢掉 name/call_id 等字段。
                    merged_item = copy.deepcopy(pending_items[item_id])  # 新增代码+OAuthNativeSseParser: 复制 added 快照作为合并基底；如果没有这一行，直接改 pending item 会影响调试证据。
                    merged_item.update(item)  # 新增代码+OAuthNativeSseParser: 用 done item 覆盖最新字段；如果没有这一行，状态和 arguments 不能更新到最终值。
                    item = merged_item  # 新增代码+OAuthNativeSseParser: 使用合并后的 item；如果没有这一行，合并结果不会进入 output。
                output_items.append(item)  # 新增代码+OAuthNativeSseParser: 保存完成的原生 output item；如果没有这一行，native chat 分支没有可解析输出。
            if event_type == "response.completed" and isinstance(event.get("response"), dict):  # 作用: 如果是完整响应事件
                completed_response = event["response"]  # 作用: 保存完整响应
        if not output_items and pending_items:  # 新增代码+OAuthNativeSseParser: 如果流只有 added/delta 没有 done，就尽量用暂存 item 兜底；如果没有这一行，异常但可恢复的流会变空。
            for item_id, item in pending_items.items():  # 新增代码+OAuthNativeSseParser: 遍历所有暂存 item；如果没有这一行，无法逐个补齐输出。
                pending_copy = copy.deepcopy(item)  # 新增代码+OAuthNativeSseParser: 复制暂存 item；如果没有这一行，后续回填会修改原暂存对象。
                if not pending_copy.get("arguments") and item_id in argument_chunks:  # 新增代码+OAuthNativeSseParser: 如果暂存 item 参数为空且有分片；如果没有这一行，兜底 item 仍缺参数。
                    pending_copy["arguments"] = "".join(argument_chunks[item_id])  # 新增代码+OAuthNativeSseParser: 拼接参数分片；如果没有这一行，工具执行器拿不到参数。
                output_items.append(pending_copy)  # 新增代码+OAuthNativeSseParser: 追加兜底 output item；如果没有这一行，added-only 流仍没有 output。
        final_output_text = "".join(output_chunks)  # 修改代码+OAuthNativeSseParser: 先拼出流式最终文本；如果没有这一行，后面无法把 output_text.done 合并回 message item。
        if final_output_text and output_items:  # 修改代码+OAuthNativeSseParser: 只有同时存在文本和原生 item 时才需要合并；如果没有这一行，纯文本响应会被错误改成 output 数组。
            output_text_attached = False  # 修改代码+OAuthNativeSseParser: 记录是否已经找到 message item 承载文本；如果没有这一行，后面不知道是否需要追加 message。
            for item in output_items:  # 修改代码+OAuthNativeSseParser: 遍历已经完成或兜底的原生 item；如果没有这一行，无法修复 in_progress message 占位。
                if str(item.get("type", "") or "") != "message":  # 修改代码+OAuthNativeSseParser: 只处理最终回答 message；如果没有这一行，function_call 或 reasoning 会被误写 content。
                    continue  # 修改代码+OAuthNativeSseParser: 非 message item 跳过；如果没有这一行，工具调用 item 可能被污染。
                item["content"] = [{"type": "output_text", "text": final_output_text}]  # 修改代码+OAuthNativeSseParser: 把 output_text.done 文本写入 message.content；如果没有这一行，最终回答会被空占位吞掉。
                if item.get("status") == "in_progress":  # 修改代码+OAuthNativeSseParser: 如果后端只给了 added 占位；如果没有这一行，日志里会继续显示未完成状态。
                    item["status"] = "completed"  # 修改代码+OAuthNativeSseParser: 把已拿到文本的 message 标为完成；如果没有这一行，后续审计会误以为响应还没完成。
                output_text_attached = True  # 修改代码+OAuthNativeSseParser: 标记文本已经合并；如果没有这一行，下面会重复追加 message。
            if not output_text_attached:  # 修改代码+OAuthNativeSseParser: 如果 output items 里只有 reasoning 或工具 item；如果没有这一行，最终文本仍可能无处安放。
                output_items.append({"type": "message", "status": "completed", "content": [{"type": "output_text", "text": final_output_text}], "role": "assistant"})  # 修改代码+OAuthNativeSseParser: 追加一个标准 message item 承载文本；如果没有这一行，parse_responses_output_items_to_model_message 取不到 text。
        if output_items:  # 新增代码+OAuthNativeSseParser: native output items 优先于文本输出；如果没有这一行，function_call 可能被旧文本覆盖。
            return {"output": output_items}  # 新增代码+OAuthNativeSseParser: 返回 Responses 标准 output 数组；如果没有这一行，native 分支无法读取 function_call。
        if final_output_text:  # 修改代码+OAuthNativeSseParser: 如果收集到了纯文本且没有原生 item；如果没有这一行，纯文本响应会落到 completed_response 兜底。
            return {"output_text": final_output_text}  # 修改代码+OAuthNativeSseParser: 返回拼接后的 output_text；如果没有这一行，非 native 输出文本会丢失。
        if completed_response is not None:  # 作用: 如果没有增量但有完整响应
            return completed_response  # 作用: 返回完整响应
        return {"output_text": ""}  # 作用: 没有可用文本时返回空 output_text

    @staticmethod  # 作用: 响应提取不依赖实例状态
    def _extract_response_text(response: dict[str, object]) -> str:  # 作用: 从 Responses API 返回中提取最终文本
        output_text = response.get("output_text")  # 作用: 优先读取 output_text 字段
        if isinstance(output_text, str):  # 作用: 如果 output_text 是字符串
            return output_text  # 作用: 直接返回
        output = response.get("output")  # 作用: 兼容复杂 output 数组结构
        if isinstance(output, list):  # 作用: 如果 output 是数组
            for item in output:  # 作用: 遍历输出项
                if not isinstance(item, dict):  # 作用: 跳过非对象项
                    continue  # 作用: 继续下一项
                content = item.get("content")  # 作用: 读取 content
                if not isinstance(content, list):  # 作用: 如果 content 不是数组
                    continue  # 作用: 继续下一项
                for content_item in content:  # 作用: 遍历 content 片段
                    if isinstance(content_item, dict) and isinstance(content_item.get("text"), str):  # 作用: 找到包含 text 的片段
                        return str(content_item["text"])  # 作用: 返回片段文本
        return json.dumps(response, ensure_ascii=False)  # 作用: 找不到文本时返回整个响应，方便排查

    @staticmethod  # 新增代码+OAuthNativeOutputParser: 原生 output item 提取不依赖实例状态；如果没有这一行，测试无法直接复用该小工具。
    def _extract_response_output_items(response: dict[str, object]) -> list[dict[str, Any]]:  # 新增代码+OAuthNativeOutputParser: 函数段开始，从 Codex Responses 响应中提取原生 output items；如果没有这段函数，native chat 无法消费 function_call，本段到 return 列表结束。
        output = response.get("output")  # 新增代码+OAuthNativeOutputParser: 优先读取 Responses 标准 output 数组；如果没有这一行，原生 function_call 没有来源。
        if isinstance(output, list):  # 新增代码+OAuthNativeOutputParser: 确认 output 是数组；如果没有这一行，字符串或对象会被误遍历。
            return [item for item in output if isinstance(item, dict)]  # 新增代码+OAuthNativeOutputParser: 只保留 dict output item；如果没有这一行，坏 item 会让 parser 报错。
        output_text = response.get("output_text")  # 新增代码+OAuthNativeOutputParser: 兼容后端只返回 output_text 的场景；如果没有这一行，纯文本回答会被丢失。
        if isinstance(output_text, str):  # 新增代码+OAuthNativeOutputParser: 如果 output_text 是字符串就转成 message item；如果没有这一行，native 模式无工具回答会变空。
            return [{"type": "message", "content": [{"type": "output_text", "text": output_text}]}]  # 新增代码+OAuthNativeOutputParser: 构造可被 parser 提取文本的 message item；如果没有这一行，最终回答无法返回用户。
        return []  # 新增代码+OAuthNativeOutputParser: 没有可用 output 时返回空数组；如果没有这一行，调用方会收到 None。
    # 新增代码+OAuthNativeOutputParser: 函数段结束，_extract_response_output_items 到此结束；如果没有这个边界说明，用户不容易看出响应提取规则。

    @classmethod  # 作用: 授权 URL 构造使用类级常量
    def _build_authorize_url(cls, redirect_uri: str, pkce_challenge: str, state: str) -> str:  # 作用: 构造 OpenAI OAuth 授权 URL
        params = urllib.parse.urlencode(  # 作用: 编码 query 参数
            {  # 作用: 授权参数字典
                "response_type": "code",  # 作用: 使用授权码模式
                "client_id": cls.CLIENT_ID,  # 作用: 使用 Codex OAuth client id
                "redirect_uri": redirect_uri,  # 作用: 登录成功后的本地回调地址
                "scope": "openid profile email offline_access",  # 作用: 请求用户资料和 refresh token
                "code_challenge": pkce_challenge,  # 作用: PKCE challenge
                "code_challenge_method": "S256",  # 作用: PKCE 使用 SHA-256
                "id_token_add_organizations": "true",  # 作用: 请求 id_token 带组织信息
                "codex_cli_simplified_flow": "true",  # 作用: 与 opencode2/Codex CLI 简化登录流程一致
                "state": state,  # 作用: 防 CSRF state
                "originator": "learning_agent",  # 作用: 标记发起方
            }  # 作用: 授权参数字典结束
        )  # 作用: 参数编码结束
        return f"{cls.ISSUER}/oauth/authorize?{params}"  # 作用: 返回完整授权 URL

    @staticmethod  # 作用: PKCE 生成不依赖实例状态
    def _generate_pkce() -> dict[str, str]:  # 作用: 生成 PKCE verifier 和 challenge
        verifier = secrets.token_urlsafe(64)[:86]  # 作用: 生成高熵 verifier，并限制长度
        digest = hashlib.sha256(verifier.encode("ascii")).digest()  # 作用: 对 verifier 做 SHA-256
        challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")  # 作用: 转成 base64url challenge
        return {"verifier": verifier, "challenge": challenge}  # 作用: 返回 verifier/challenge

    @staticmethod  # 作用: state 生成不依赖实例状态
    def _generate_state() -> str:  # 作用: 生成 OAuth state
        return secrets.token_urlsafe(32)  # 作用: 返回不可预测随机字符串

    @staticmethod  # 作用: JWT 解析不依赖实例状态
    def _extract_account_id(token: str) -> str | None:  # 作用: 从 JWT token 中提取 ChatGPT account id
        parts = token.split(".")  # 作用: JWT 通常由 header.payload.signature 三段组成
        if len(parts) != 3:  # 作用: 如果不是标准 JWT
            return None  # 作用: 无法解析账号 id
        payload = parts[1] + "=" * (-len(parts[1]) % 4)  # 作用: 给 base64url payload 补齐 padding
        try:  # 作用: 捕获 base64 或 JSON 解析错误
            claims = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))  # 作用: 解码 JWT payload
        except (ValueError, json.JSONDecodeError):  # 作用: 如果解析失败
            return None  # 作用: 返回 None
        auth_claim = claims.get("https://api.openai.com/auth")  # 作用: 读取 OpenAI 自定义 auth claims
        if isinstance(auth_claim, dict) and auth_claim.get("chatgpt_account_id"):  # 作用: 如果自定义 claims 有 account id
            return str(auth_claim["chatgpt_account_id"])  # 作用: 返回 account id
        if claims.get("chatgpt_account_id"):  # 作用: 如果顶层 claims 有 account id
            return str(claims["chatgpt_account_id"])  # 作用: 返回 account id
        organizations = claims.get("organizations")  # 作用: 读取组织数组作为兜底
        if isinstance(organizations, list) and organizations and isinstance(organizations[0], dict):  # 作用: 如果组织数组第一个元素是对象
            return str(organizations[0].get("id") or "") or None  # 作用: 返回第一个组织 id，空字符串转 None
        return None  # 作用: 没有任何可用账号 id

    @staticmethod  # 作用: 当前时间不依赖实例状态
    def _now_ms() -> int:  # 作用: 返回当前毫秒时间戳
        return int(time.time() * 1000)  # 作用: 把秒级 time.time 转成毫秒整数

