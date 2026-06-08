"""这个测试文件集中保存模块化测试共用的 fake、helper 和路径准备逻辑。"""  # 修改代码+Stage14硬清理: 说明当前 support.py 是新测试架构的共享支撑；若没有这行代码，维护者会误以为测试仍围绕旧脚本入口展开

import json  # 新增代码: 解析调试日志 JSONL，验证 agent 是否把关键步骤写入日志；若省略: 无法读取结构化调试日志
import io  # 新增代码+AcceptanceHarness: 提供内存文本流来接收终端标记；若没有这行代码，测试只能读取真实 stdout，容易污染测试输出
import os  # 新增代码+可配置轮次: 临时设置和恢复 LEARNING_AGENT_MAX_TURNS 环境变量；若省略: 无法测试环境变量覆盖配置文件
import socket  # 新增代码+HTTP流生命周期: 使用标准库解析本地 localhost 到 IPv4 地址，避免测试服务器绑定到不确定地址；若省略: 新增 HTTP 流生命周期测试无法明确使用本机回环地址
import http.client  # 新增代码+OAuth远端断连: 使用标准库 RemoteDisconnected 复现截图里的远端关闭连接；若省略: 测试只能用普通 RuntimeError，无法贴近真实 urllib 异常
import http.server  # 新增代码+browser/search MCP测试: 启动本地 HTTP 页面给 fetch_url 读取；若省略: 测试只能依赖外网而不稳定
import sys  # 新增代码: 提供当前 Python 解释器路径给 MCP 配置测试；若省略: 测试会硬编码平台相关命令导致跨机器不稳定
import tempfile  # 作用: 提供创建临时目录/文件的工具，用于隔离文件系统副作用；若省略: 无法创建临时目录，测试会污染工作区或出错
import threading  # 新增代码+browser/search MCP测试: 在后台线程运行本地 HTTP server；若省略: 测试会阻塞在 serve_forever
import time  # 新增代码+MCP stdio client 健壮性: 测量超时测试耗时；若省略: 无法断言不响应 server 不会长时间卡住
import subprocess  # 新增代码: 构造假的 CompletedProcess，模拟 codex exec 子进程返回；若省略: 无法测试 Codex CLI 桥接模型
import unittest  # 作用: Python 内置的单元测试框架（TestCase、断言、测试运行器）；若省略: 无法定义或运行测试用例
from unittest import mock  # 新增代码+RealChrome测试: 显式导入 mock 工具；若省略: Task 2 helper 实现后 unittest.mock 可能不存在导致测试 AttributeError
from pathlib import Path  # 作用: 提供跨平台的路径操作接口（更直观的拼接/读写）；若省略: 需用字符串路径并自行处理分隔符
from datetime import date  # 新增代码+CurrentDatePrompt: 读取测试运行当天的本地日期；若没有这行代码，测试无法断言 agent 每轮看到的真实日期

TEST_ROOT = Path(__file__).resolve().parents[1]  # 修改代码+Stage14硬清理: 指向 learning_agent 包目录；若没有这行代码，模块化测试会把 staticprompt、skills 和 MCP 脚本定位到错误目录
PROJECT_ROOT = TEST_ROOT.parent  # 修改代码+Stage14硬清理: 指向 OpenHarness-main 项目根目录；若没有这行代码，模块化测试会找不到 docs、.gitignore 和仓库级文件
project_root_text = str(PROJECT_ROOT)  # 修改代码+TestsSplit: 把项目根路径转成字符串供 sys.path 使用；若没有这行代码，后续移除和插入路径会重复转换且不清楚。
if project_root_text in sys.path:  # 修改代码+TestsSplit: 如果项目根已经在搜索路径里也要先移除；若没有这行代码，它可能排在 learning_agent 目录后面而继续被遮蔽。
    sys.path.remove(project_root_text)  # 修改代码+TestsSplit: 移除旧位置的项目根路径；若没有这行代码，插入最前面后 sys.path 会出现重复项。
sys.path.insert(0, project_root_text)  # 修改代码+LegacyEntryCut: 把项目根强制放到导入搜索路径最前面；若没有这行代码，后续分层导入会找不到 learning_agent 包。
shadowed_learning_agent_module = sys.modules.get("learning_agent")  # 修改代码+TestsSplit: 检查是否已有顶层 learning_agent.py 模块遮住包名；若没有这行代码，无法修复 discover 模式的模块名冲突。
if shadowed_learning_agent_module is not None and not hasattr(shadowed_learning_agent_module, "__path__"):  # 修改代码+TestsSplit: 只清理非包模块，避免误删已经正确导入的包；若没有这行代码，正常包导入可能被破坏。
    del sys.modules["learning_agent"]  # 修改代码+LegacyEntryCut: 移除遮蔽包名的顶层模块；若没有这行代码，分层导入会继续被同名脚本误导。

from learning_agent.app.cli import format_cli_run_response  # 修改代码+LegacyEntryCut: 从 app 层导入 CLI 输出格式化函数；若没有这行代码，测试会继续依赖旧脚本入口。
from learning_agent.app.doctor import run_mcp_doctor  # 修改代码+LegacyEntryCut: 从 app doctor 入口导入诊断函数；若没有这行代码，MCP 诊断测试无法脱离旧脚本入口。
from learning_agent.app.http_bridge import create_command_bridge_server  # 修改代码+LegacyEntryCut: 从 app HTTP bridge 层导入 server 工厂；若没有这行代码，bridge 测试会继续倒逼旧入口导出。
from learning_agent.core.agent import (  # 修改代码+LegacyEntryCut: 从核心层导入 agent 主体和终端权限入口；若没有这行代码，运行循环测试没有稳定新入口。
    LearningAgent,  # 修改代码+LegacyEntryCut: 导入被测试的主 agent 类；若没有这行代码，测试无法创建和运行 agent 实例。
    ToolCallingFakeModel,  # 修改代码+LegacyEntryCut: 导入测试假模型；若没有这行代码，离线工具循环测试需要真实模型。
    ask_permission_from_terminal,  # 修改代码+LegacyEntryCut: 导入真实终端权限函数；若没有这行代码，验收事件测试无法覆盖生产交互点。
    ask_permission_from_terminal_customer_mode,  # 修改代码+LegacyEntryCut: 导入客户模式权限入口；若没有这行代码，真实浏览器无 y 体验没有生产入口测试。
)  # 修改代码+LegacyEntryCut: 结束核心层导入列表；若没有这行代码，Python 语法无法闭合。
from learning_agent.core.config import (  # 修改代码+LegacyEntryCut: 从 core.config 导入运行配置解析对象；若没有这行代码，配置测试会继续绕回旧脚本入口。
    AgentRuntimeConfig,  # 修改代码+LegacyEntryCut: 导入运行配置数据类；若没有这行代码，max_turns 配置测试无法断言字段语义。
    MainArgs,  # 修改代码+LegacyEntryCut: 导入命令行参数数据类；若没有这行代码，CLI 覆盖配置测试无法构造参数对象。
    load_agent_runtime_config,  # 修改代码+LegacyEntryCut: 导入运行配置加载函数；若没有这行代码，runtime_config.json 和环境变量测试无法执行。
    parse_main_args,  # 修改代码+LegacyEntryCut: 导入主命令行解析函数；若没有这行代码，--max-turns 参数测试无法执行。
    parse_max_turns_value,  # 修改代码+LegacyEntryCut: 导入轮次解析函数；若没有这行代码，配置层回归测试无法比较统一解析器。
    resolve_run_max_turns,  # 修改代码+LegacyEntryCut: 导入最终轮次决策函数；若没有这行代码，CLI 优先级测试无法执行。
)  # 修改代码+LegacyEntryCut: 结束配置层导入列表；若没有这行代码，Python 语法无法闭合。
from learning_agent.core.messages import ModelMessage, ToolCall  # 修改代码+LegacyEntryCut: 从 core.messages 导入统一消息对象；若没有这行代码，假模型无法构造标准响应。
from learning_agent.mcp.config import McpServerConfig, load_mcp_server_configs  # 修改代码+LegacyEntryCut: 从 MCP 配置层导入 server 配置和加载函数；若没有这行代码，MCP 配置测试无法脱离旧入口。
from learning_agent.mcp.registry import McpToolRegistry  # 修改代码+LegacyEntryCut: 从 MCP registry 层导入工具注册表；若没有这行代码，MCP 工具发现测试没有稳定入口。
from learning_agent.mcp.stdio_client import McpStdioClient  # 修改代码+LegacyEntryCut: 从 MCP stdio 层导入本地客户端；若没有这行代码，stdio client 测试没有稳定入口。
from learning_agent.models.codex_cli import CodexCliChatModel  # 修改代码+LegacyEntryCut: 从模型层导入 Codex CLI 适配器；若没有这行代码，模型测试会继续依赖旧入口。
from learning_agent.models.codex_oauth import CodexOAuthChatModel  # 修改代码+LegacyEntryCut: 从模型层导入 Codex OAuth 适配器；若没有这行代码，OAuth 模型测试会继续依赖旧入口。
from learning_agent.models.oauth_tokens import CodexOAuthTokens  # 修改代码+LegacyEntryCut: 从 token 模块导入 OAuth token 数据类；若没有这行代码，token 测试无法构造测试凭证。
from learning_agent.models.openai_chat import OpenAIChatModel  # 修改代码+LegacyEntryCut: 从模型层导入 OpenAI-compatible 适配器；若没有这行代码，默认模型测试没有稳定入口。
from learning_agent.tools.catalog import build_builtin_tool_catalog  # 修改代码+LegacyEntryCut: 从工具 catalog 层导入内置目录构建函数；若没有这行代码，工具目录测试会继续依赖旧入口。
from learning_agent.tools.schemas import TOOL_SCHEMAS  # 修改代码+LegacyEntryCut: 从工具 schema 层导入内置工具事实源；若没有这行代码，schema 测试没有稳定入口。
from learning_agent.observability.acceptance_events import (  # 新增代码+AcceptanceHarness: 导入验收事件协议入口；若没有这行代码，外部 agent 无法用测试锁定可控制接口
    ACCEPTANCE_EVENT_ENV_VAR,  # 新增代码+AcceptanceHarness: 导入环境变量名；若没有这行代码，测试会把配置入口写死成散落字符串
    ACCEPTANCE_EVENT_MARKER_PREFIX,  # 新增代码+AcceptanceHarness: 导入终端标记前缀；若没有这行代码，测试无法确认可见终端里有机器可识别状态行
    ACCEPTANCE_EVENT_STDOUT_ENV_VAR,  # 修改代码+AcceptanceStdoutNoiseControl: 导入终端机器标记显式开关；若没有这行代码，测试无法验证默认隐藏和按需打开两种模式。
    emit_acceptance_event,  # 新增代码+AcceptanceHarness: 导入事件写入函数；若没有这行代码，测试无法驱动最小验收协议
)  # 新增代码+AcceptanceHarness: 结束验收 harness 导入；若没有这行代码，Python 导入语法不完整
from learning_agent.browser_real_chrome import (  # 新增代码+RealChrome测试: 导入真实 Chrome helper；若省略: 后续测试无法驱动新 helper 模块
    BrowserSafetyPolicy,  # 新增代码+RealChrome测试: 导入安全策略类；若省略: 无法验证敏感脚本默认拒绝
    ChromeProfileManager,  # 新增代码+RealChrome测试: 导入 profile 管理器；若省略: 无法验证 Chrome 路径和 profile 路径识别
    RealChromeProfileError,  # 新增代码+RealChrome测试: 导入真实 Chrome 专用错误；若省略: 无法断言错误边界清楚
    build_chrome_debug_command,  # 新增代码+RealChrome测试: 导入启动命令构造函数；若省略: 无法验证调试端口只绑定本机
    choose_loopback_port,  # 新增代码+RealChrome测试: 导入本机端口选择函数；若省略: 无法验证端口选择避开占用
)  # 新增代码+RealChrome测试: 结束真实 Chrome helper 导入；若省略: Python 导入语法不完整
from learning_agent.tool_policy import (  # 新增代码+ToolPolicyV2: 导入独立 ToolPolicy 模块来测试策略层；若没有这行代码，测试只能绕过新模块而无法验证 Task 1 入口
    ToolPolicy,  # 新增代码+ToolPolicyV2: 导入策略决策类用于调用 decide；若没有这行代码，测试无法执行核心策略判断
    ToolPolicyContext,  # 新增代码+ToolPolicyV2: 导入策略上下文数据类用于提供 deny、skill 和 workflow 状态；若没有这行代码，测试无法构造真实策略输入
    ToolPolicyRule,  # 新增代码+ToolPolicyV2: 导入策略规则数据类用于配置拒绝规则；若没有这行代码，测试无法验证 deny rule 是否生效
)  # 新增代码+ToolPolicyV2: 结束 ToolPolicyV2 导入列表；若没有这行代码，Python 导入语法不完整

from learning_agent.prompt_registry import (  # 新增代码+PromptArchitectureV1: 导入提示词注册表模型给 Task 1 测试使用；若没有这行代码，测试无法访问新建的 Prompt Registry 入口
    PromptBlock,  # 新增代码+PromptArchitectureV1: 导入单个提示词块的数据模型；若没有这行代码，重复 block_id 的测试无法构造测试对象
    PromptLoadDecision,  # 新增代码+PromptArchitectureV1: 导入提示词加载决策模型；若没有这行代码，测试无法确认注册表模块提供计划要求的决策结构
    PromptRegistry,  # 新增代码+PromptArchitectureV1: 导入提示词注册表容器；若没有这行代码，测试无法验证重复 block_id 会被拒绝
    build_default_prompt_registry,  # 新增代码+PromptArchitectureV1: 导入默认注册表构建函数；若没有这行代码，测试无法验证默认提示词块元数据
)  # 新增代码+PromptArchitectureV1: 结束 Prompt Registry 导入列表；若没有这行代码，Python 导入语法不完整
from learning_agent.context_assembler import (  # 修改代码+PromptArchitectureV1: 导入上下文装配器和索引构建函数；若没有这行代码，Task 2/3 的排序与截断测试无法访问目标模块
    ContextAssembler,  # 修改代码+PromptArchitectureV1: 导入上下文装配器以验证 block 排序和装配结果；若没有这行代码，测试无法驱动 context_assembler 模块
    build_text_index,  # 新增代码+PromptArchitectureV1: 导入文本索引函数以验证索引截断仍保留尾部摘要；若没有这行代码，审查发现的 tail 丢失问题无法形成回归测试
)  # 修改代码+PromptArchitectureV1: 结束 Context Assembler 导入列表；若没有这行代码，Python 导入语法不完整


class FakeOAuthTokenStore:  # 新增代码: 定义测试专用的内存 token 存储，避免测试读写真实磁盘 token
    def __init__(self, tokens: CodexOAuthTokens | None) -> None:  # 新增代码: 初始化时允许传入已有 token，也允许模拟未登录状态
        self.tokens = tokens  # 新增代码: 保存当前 token，供 load 方法返回
        self.saved: list[CodexOAuthTokens] = []  # 新增代码: 记录每次 save 的 token，方便断言刷新是否发生

    def load(self) -> CodexOAuthTokens | None:  # 新增代码: 模拟真实 token store 的 load 接口
        return self.tokens  # 新增代码: 返回当前内存 token

    def save(self, tokens: CodexOAuthTokens) -> None:  # 新增代码: 模拟真实 token store 的 save 接口
        self.tokens = tokens  # 新增代码: 更新当前内存 token
        self.saved.append(tokens)  # 新增代码: 记录保存历史，便于测试检查


class RecordingToolNameFakeModel:  # 新增代码: 定义记录工具名的测试假模型；若省略: 无法验证 run 真正传给模型的 tools 内容
    def __init__(self, response: ModelMessage) -> None:  # 新增代码: 初始化假模型并接收固定响应；若省略: 测试无法控制模型最终回答
        self.response = response  # 新增代码: 保存固定响应供 chat 返回；若省略: chat 无法稳定结束 agent.run
        self.received_tool_names: list[list[str]] = []  # 新增代码: 保存每次 chat 收到的工具名列表；若省略: 测试无法断言模型实际收到哪些工具

    def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码: 模拟模型 chat 接口并记录传入工具；若省略: LearningAgent.run 无法调用这个假模型
        tool_names: list[str] = []  # 新增代码: 准备保存本次调用的工具名；若省略: 后续无法逐个收集 schema 里的 name
        for schema in tools:  # 新增代码: 遍历 agent 传给模型的工具 schema；若省略: 测试无法从真实参数中提取工具名
            function = schema.get("function", {})  # 新增代码: 取出 OpenAI-compatible schema 的 function 字段；若省略: 无法定位工具名称所在位置
            if isinstance(function, dict) and isinstance(function.get("name"), str):  # 新增代码: 确认工具名存在且是字符串；若省略: 异常 schema 可能让测试假模型崩溃
                tool_names.append(function["name"])  # 新增代码: 保存工具名；若省略: received_tool_names 会缺少本次模型收到的工具
        self.received_tool_names.append(tool_names)  # 新增代码: 记录本次 chat 的工具名快照；若省略: 测试结束后无法检查 run 的传参
        return self.response  # 新增代码: 返回固定模型消息让 agent.run 正常结束；若省略: agent.run 收不到最终回答

class SequentialRecordingToolNameFakeModel:  # 新增代码+ToolPolicyV2: 定义按顺序返回多条消息并记录每轮工具名的假模型；若没有这行代码，测试无法证明 select 后下一轮 schema 才出现新工具
    def __init__(self, responses: list[ModelMessage]) -> None:  # 新增代码+ToolPolicyV2: 初始化假模型并接收多轮预设响应；若没有这行代码，run() 测试无法模拟同批 tool_calls 后再进入下一轮
        self.responses = responses  # 新增代码+ToolPolicyV2: 保存预设模型响应列表；若没有这行代码，chat 无法按轮次返回测试需要的消息
        self.index = 0  # 新增代码+ToolPolicyV2: 记录下一次 chat 应返回第几条消息；若没有这行代码，假模型无法推进到下一轮
        self.received_tool_names: list[list[str]] = []  # 新增代码+ToolPolicyV2: 保存每次 chat 收到的工具名快照；若没有这行代码，测试无法断言下一轮工具池是否刷新

    def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码+ToolPolicyV2: 模拟模型 chat 并记录本轮可见工具；若没有这行代码，LearningAgent.run 无法调用该假模型
        del messages  # 新增代码+ToolPolicyV2: 明确本假模型不读取消息历史；若没有这行代码，未使用参数会让测试意图不够清楚
        tool_names: list[str] = []  # 新增代码+ToolPolicyV2: 准备保存本轮 schema 里的工具名；若没有这行代码，后续无法逐个收集工具
        for schema in tools:  # 新增代码+ToolPolicyV2: 遍历 agent 传给模型的每个工具 schema；若没有这行代码，测试无法观察真实工具池
            function = schema.get("function", {})  # 新增代码+ToolPolicyV2: 读取 OpenAI-compatible schema 的 function 字段；若没有这行代码，工具名所在位置找不到
            if isinstance(function, dict) and isinstance(function.get("name"), str):  # 新增代码+ToolPolicyV2: 确认工具名存在且类型正确；若没有这行代码，异常 schema 可能让测试假模型崩溃
                tool_names.append(function["name"])  # 新增代码+ToolPolicyV2: 保存当前工具名；若没有这行代码，received_tool_names 会缺少本轮工具
        self.received_tool_names.append(tool_names)  # 新增代码+ToolPolicyV2: 记录本轮模型实际收到的工具名；若没有这行代码，测试无法检查下一轮 schema 是否包含已 select 工具
        if self.index >= len(self.responses):  # 新增代码+ToolPolicyV2: 防御预设响应被用完的情况；若没有这行代码，越界会抛出不清楚的列表错误
            return ModelMessage(text="假模型没有更多预设回答。")  # 新增代码+ToolPolicyV2: 返回清楚兜底文本；若没有这行代码，测试失败时不容易定位响应数量问题
        response = self.responses[self.index]  # 新增代码+ToolPolicyV2: 取出当前轮预设响应；若没有这行代码，chat 没有消息可返回
        self.index += 1  # 新增代码+ToolPolicyV2: 推进响应指针到下一轮；若没有这行代码，run() 会反复收到同一批 tool_calls
        return response  # 新增代码+ToolPolicyV2: 返回预设消息给 LearningAgent.run；若没有这行代码，agent 无法继续工具循环


class BlockingChatFakeModel:  # 新增代码+AsyncTask: 定义会等待释放信号的测试假模型；若省略: 无法验证后台 task 是否真的不阻塞工具调用
    def __init__(self) -> None:  # 新增代码+AsyncTask: 初始化阻塞模型的同步事件；若省略: 测试无法控制 chat 何时结束
        self.started = threading.Event()  # 新增代码+AsyncTask: 记录 chat 已经被后台线程调用；若省略: 测试无法确认后台子 agent 已开始运行
        self.release = threading.Event()  # 新增代码+AsyncTask: 控制 chat 何时返回；若省略: 测试无法稳定保持任务 running 状态
        self.received_tool_names: list[list[str]] = []  # 新增代码+AsyncTask: 保存每次 chat 收到的工具名列表；若省略: 后续无法排查后台子 agent 可见工具

    def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码+AsyncTask: 模拟模型 chat 接口并短暂阻塞；若省略: LearningAgent.run 无法调用这个假模型
        tool_names: list[str] = []  # 新增代码+AsyncTask: 准备保存本次调用的工具名；若省略: 后续无法记录 tools 参数
        for schema in tools:  # 新增代码+AsyncTask: 遍历 agent 传给模型的工具 schema；若省略: 测试无法从真实参数中提取工具名
            function = schema.get("function", {})  # 新增代码+AsyncTask: 取出 OpenAI-compatible schema 的 function 字段；若省略: 无法定位工具名称所在位置
            if isinstance(function, dict) and isinstance(function.get("name"), str):  # 新增代码+AsyncTask: 确认工具名存在且是字符串；若省略: 异常 schema 可能让测试假模型崩溃
                tool_names.append(function["name"])  # 新增代码+AsyncTask: 保存工具名；若省略: received_tool_names 会缺少本次模型收到的工具
        self.received_tool_names.append(tool_names)  # 新增代码+AsyncTask: 记录本次 chat 的工具名快照；若省略: 测试结束后无法检查后台子 agent 的传参
        self.started.set()  # 新增代码+AsyncTask: 通知测试后台 chat 已经开始；若省略: 测试只能用 sleep 猜测任务是否 running
        self.release.wait(timeout=0.3)  # 新增代码+AsyncTask: 等待释放信号或短暂超时；若省略: 当前同步 task 不能稳定表现为阻塞红灯
        return ModelMessage(text="后台子任务已经结束。")  # 新增代码+AsyncTask: 返回固定子任务结果让后台线程可正常收尾；若省略: agent.run 收不到最终回答


class FakeMcpClient:  # 新增代码+MCP 工具注册表: 定义注册表测试专用假 MCP client；若省略: 测试会依赖真实子进程而无法专注验证注册表逻辑
    def __init__(self, tools: list[dict[str, object]] | None = None, result_prefix: str = "called", start_error: Exception | None = None, call_error: Exception | None = None, resources: list[dict[str, object]] | None = None, resource_text: str = "resource body", prompts: list[dict[str, object]] | None = None, prompt_text: str = "prompt body", notifications: list[dict[str, object]] | None = None) -> None:  # 修改代码+MCPLifecycleV2: 允许 fake client 同时模拟 MCP tools、resources、prompts 和 server notifications；若没有这行代码，Phase 3 无法用内存假对象测试 list_changed 生命周期
        self.tools = tools if tools is not None else self._default_tools()  # 新增代码+MCP 工具注册表: 保存 fake client 要返回的工具列表；若省略: list_tools 无法按测试场景变化
        self.result_prefix = result_prefix  # 新增代码+MCP 工具注册表: 保存结果前缀用于区分不同 fake server；若省略: 多 server 路由测试无法判断调用了哪个 client
        self.start_error = start_error  # 新增代码+MCP接入健壮性: 保存启动时要抛出的测试异常；若省略: start 失败场景只能依赖真实故障且不可控
        self.call_error = call_error  # 新增代码+MCP接入健壮性: 保存调用工具时要抛出的测试异常；若省略: call_tool 失败场景无法稳定复现
        self.resources = resources if resources is not None else []  # 新增代码+MCPResource: 保存 fake client 暴露的 MCP resources；若省略: list_resources 没有可返回的数据
        self.resource_text = resource_text  # 新增代码+MCPResource: 保存 read_resource 要返回的资源正文；若省略: 读取资源测试无法断言具体内容
        self.prompts = prompts if prompts is not None else []  # 新增代码+MCPPrompt: 保存 fake client 暴露的 MCP prompts；若省略: list_prompts 没有可返回的数据
        self.prompt_text = prompt_text  # 新增代码+MCPPrompt: 保存 get_prompt 要返回的提示词正文；若省略: 读取 prompt 测试无法断言具体内容
        self.notifications = notifications if notifications is not None else []  # 新增代码+MCPLifecycleV2: 保存 fake server 等待 agent 拉取的 JSON-RPC notifications；若没有这行代码，registry 刷新测试无法模拟 tools/list_changed 到达
        self.started = False  # 新增代码+MCP 工具注册表: 记录 start 是否被注册表调用；若省略: 无法确认注册表会启动 client
        self.start_count = 0  # 新增代码+MCP 工具注册表: 记录 start 被调用次数；若省略: 重复 start 幂等测试无法观察注册表刷新行为
        self.closed = False  # 新增代码+MCP 工具注册表: 记录 close 是否被注册表调用；若省略: 后续无法验证资源清理转发
        self.calls: list[tuple[str, dict[str, object]]] = []  # 新增代码+MCP 工具注册表: 保存工具调用历史；若省略: 无法断言前缀被剥离后调用原始工具名
        self.resource_reads: list[str] = []  # 新增代码+MCPResource: 保存资源读取历史；若省略: 测试无法确认 registry 把 uri 转发给了正确 client
        self.prompt_reads: list[tuple[str, dict[str, object]]] = []  # 新增代码+MCPPrompt: 保存 prompt 读取历史；若省略: 测试无法确认 registry 把 name 和 arguments 转发给正确 client

    def _default_tools(self) -> list[dict[str, object]]:  # 新增代码+MCP 工具注册表: 提供默认 echo 工具定义；若省略: 普通注册表测试需要重复写工具字典
        return [  # 新增代码+MCP 工具注册表: 返回单工具列表；若省略: 测试无法检查第一个 schema 的名称和 required
            {  # 新增代码+MCP 工具注册表: 定义 echo 工具对象；若省略: 注册表不会发现 echo 工具
                "name": "echo",  # 新增代码+MCP 工具注册表: 提供 MCP 原始工具名；若省略: 注册表无法生成 mcp__demo__echo 名称
                "description": "Echo text",  # 新增代码+MCP 工具注册表: 提供工具说明；若省略: 转换后的 schema 会缺少模型可读描述
                "inputSchema": {  # 新增代码+MCP 工具注册表: 提供 MCP 输入 JSON Schema；若省略: 注册表无法保留 required 等参数约束
                    "type": "object",  # 新增代码+MCP 工具注册表: 声明参数是对象；若省略: OpenAI function parameters 不够明确
                    "properties": {"text": {"type": "string"}},  # 新增代码+MCP 工具注册表: 声明 text 参数类型；若省略: 模型不知道 echo 需要什么参数
                    "required": ["text"],  # 新增代码+MCP 工具注册表: 声明 text 必填；若省略: 测试无法验证 required 被保留
                },  # 新增代码+MCP 工具注册表: 结束 inputSchema；若省略: 工具定义语法不完整
            }  # 新增代码+MCP 工具注册表: 结束 echo 工具对象；若省略: 工具列表语法不完整
        ]  # 新增代码+MCP 工具注册表: 结束工具列表；若省略: list_tools 无法返回标准列表

    def start(self) -> None:  # 新增代码+MCP 工具注册表: 模拟 MCP client 启动接口；若省略: 注册表 start 会调用不存在的方法而不是验证目标行为
        self.started = True  # 新增代码+MCP 工具注册表: 标记已经启动；若省略: list_tools 无法确认 start 已经发生
        self.start_count += 1  # 新增代码+MCP 工具注册表: 累加启动次数；若省略: 重复 start 测试无法确认注册表确实执行了刷新路径
        if self.start_error is not None:  # 新增代码+MCP接入健壮性: 如果测试配置了启动异常就抛出；若省略: registry.start 失败路径不会被红灯测试覆盖
            raise self.start_error  # 新增代码+MCP接入健壮性: 抛出可控异常模拟 MCP server 启动失败；若省略: agent 构造防崩溃逻辑没有可靠测试输入

    def list_tools(self) -> list[dict[str, object]]:  # 新增代码+MCP 工具注册表: 返回 fake MCP server 暴露的工具列表；若省略: 注册表没有输入可转换成 OpenAI schema
        return list(self.tools)  # 修改代码+MCP 工具注册表: 返回外层副本并保留嵌套对象用于深拷贝测试；若省略: 测试无法模拟调用方或注册表污染风险

    def call_tool(self, name: str, arguments: dict[str, object]) -> str:  # 新增代码+MCP 工具注册表: 模拟原始 MCP 工具调用接口；若省略: registry.call_tool 无法验证转发
        self.calls.append((name, arguments))  # 新增代码+MCP 工具注册表: 记录收到的原始工具名和参数；若省略: 无法确认前缀被正确去掉
        if self.call_error is not None:  # 新增代码+MCP接入健壮性: 如果测试配置了调用异常就抛出；若省略: MCP 工具运行失败路径无法稳定覆盖
            raise self.call_error  # 新增代码+MCP接入健壮性: 抛出可控异常模拟外部 MCP 工具失败；若省略: agent 的可读错误返回缺少测试输入
        return f"{self.result_prefix} {name}: {arguments.get('text', '')}"  # 修改代码+MCP 工具注册表: 返回带 server 标识的可断言文本；若省略: 多 server 测试无法区分路由目标

    def list_resources(self) -> list[dict[str, object]]:  # 新增代码+MCPResource: 模拟 MCP resources/list 接口；若省略: registry 无法测试资源发现
        return list(self.resources)  # 新增代码+MCPResource: 返回 resources 外层副本；若省略: 调用方可能污染 fake client 内部列表

    def read_resource(self, uri: str) -> str:  # 新增代码+MCPResource: 模拟 MCP resources/read 接口；若省略: registry 无法测试资源读取
        self.resource_reads.append(uri)  # 新增代码+MCPResource: 记录读取的 uri；若省略: 测试无法确认 uri 被正确转发
        return f"{self.resource_text}: {uri}"  # 新增代码+MCPResource: 返回包含 uri 的可断言文本；若省略: 读取结果无法区分目标资源

    def list_prompts(self) -> list[dict[str, object]]:  # 新增代码+MCPPrompt: 模拟 MCP prompts/list 接口；若省略: registry 无法测试 prompt 发现
        return list(self.prompts)  # 新增代码+MCPPrompt: 返回 prompts 外层副本；若省略: 调用方可能污染 fake client 内部列表

    def get_prompt(self, name: str, arguments: dict[str, object] | None = None) -> str:  # 新增代码+MCPPrompt: 模拟 MCP prompts/get 接口；若省略: registry 无法测试 prompt 读取
        safe_arguments = arguments or {}  # 新增代码+MCPPrompt: 把缺省参数转成空字典；若省略: 测试断言可能收到 None 而不是 MCP 常见 arguments 对象
        self.prompt_reads.append((name, safe_arguments))  # 新增代码+MCPPrompt: 记录 prompt 名和参数；若省略: 测试无法确认读取请求被正确转发
        return f"{self.prompt_text}: {name} {safe_arguments.get('topic', '')}".strip()  # 新增代码+MCPPrompt: 返回包含 prompt 名和参数的可断言文本；若省略: 读取结果无法区分目标 prompt

    def pop_notifications(self) -> list[dict[str, object]]:  # 新增代码+MCPLifecycleV2: 模拟真实 MCP client 被 registry 拉取待处理 notifications；若没有这行代码，Phase 3 只能靠真实 server 才能测试刷新
        notifications = list(self.notifications)  # 新增代码+MCPLifecycleV2: 复制当前通知队列；若没有这行代码，返回值和内部列表会共享并被调用方误改
        self.notifications.clear()  # 新增代码+MCPLifecycleV2: 拉取后清空队列，贴近一次性消费 notification 的语义；若没有这行代码，同一通知会被重复刷新多次
        return notifications  # 新增代码+MCPLifecycleV2: 返回本次拉取到的通知；若没有这行代码，registry 没有事件输入可处理

    def close(self) -> None:  # 新增代码+MCP 工具注册表: 模拟关闭 MCP client；若省略: 注册表 close 无法统一清理 client
        self.closed = True  # 新增代码+MCP 工具注册表: 标记已经关闭；若省略: 后续无法断言清理行为




class LearningAgentTestBase(unittest.TestCase):  # Stage14: shared fake/helper base for modular tests.
    def _static_prompt_file(self) -> Path:  # 新增代码+PromptFiles: 返回包内静态提示词文件路径；若没有这行代码，测试会继续把系统提示词和 Python helper 绑在一起
        return (TEST_ROOT / "staticprompt") / "staticprompt.md"  # 新增代码+PromptFiles: 约定静态提示词放在 learning_agent/staticprompt/staticprompt.md；若没有这行代码，文件化入口没有稳定测试路径
    def _dynamic_prompt_file(self) -> Path:  # 新增代码+PromptFiles: 返回包内动态提示词索引文件路径；若没有这行代码，测试会继续读取旧 runtime_instructions.md
        return (TEST_ROOT / "dynamicprompt") / "dynamicprompt.md"  # 新增代码+PromptFiles: 约定动态提示词放在 learning_agent/dynamicprompt/dynamicprompt.md；若没有这行代码，动态规则文件没有稳定测试路径
    def _skill_file(self, skill_name: str) -> Path:  # 新增代码+动态提示词分层: 返回包内某个 skill 的 SKILL.md 路径；若没有这行代码，分层测试会重复拼路径且容易写错
        return (TEST_ROOT / "skills") / skill_name / "SKILL.md"  # 新增代码+动态提示词分层: 统一定位 learning_agent/skills/<name>/SKILL.md；若没有这行代码，测试可能检查到错误目录
    def _skill_rule_file(self, skill_name: str, rule_name: str) -> Path:  # 新增代码+动态提示词分层: 返回包内某个 skill 的子规则文件路径；若没有这行代码，测试无法稳定验证第三层规则文件
        return (TEST_ROOT / "skills") / skill_name / "rules" / rule_name  # 新增代码+动态提示词分层: 统一定位 learning_agent/skills/<name>/rules/<rule>.md；若没有这行代码，子规则路径会散落在测试里
    def _project_root(self) -> Path:  # 新增代码+浏览器自动化: 返回仓库根目录供 read-based skill 测试读取真实包内 skill；若没有这行代码，测试只能复制一份提示词树而不能覆盖交付文件
        return PROJECT_ROOT  # 修改代码+Stage14硬清理: 直接返回拆分测试统一计算出的项目根；若没有这行代码，浏览器 skill 测试读取仓库文件时容易定位错误
    def _read_acceptance_events(self, event_log_path: Path) -> list[dict[str, object]]:  # 新增代码+AcceptanceHarness: 读取验收事件 JSONL 供测试断言；若没有这行代码，每个测试会重复解析逻辑且容易漏掉编码
        raw_lines = event_log_path.read_text(encoding="utf-8").splitlines()  # 新增代码+AcceptanceHarness: 按 UTF-8 读取每一行事件；若没有这行代码，中文 payload 或 Windows 默认编码可能导致解析失败
        return [json.loads(raw_line) for raw_line in raw_lines]  # 新增代码+AcceptanceHarness: 把 JSONL 每行转成字典；若没有这行代码，测试只能比较脆弱的字符串片段
    def _select_tool_for_test(self, agent: LearningAgent, tool_name: str) -> str:  # 新增代码+ToolArchitectureV2: 在测试里复用 tool_search select 加载 deferred 工具；若没有这行代码，旧 MCP 测试会继续绕过 v2 工具池契约
        return agent._execute_tool(ToolCall(name="tool_search", arguments={"query": f"select:{tool_name}"}))  # 新增代码+ToolArchitectureV2: 通过真实工具入口加载指定工具并返回结果；若没有这行代码，测试只会手改内部状态而覆盖不到 select 流程
    def _tool_call_item_schema_for_test(self, schema: dict[str, object]) -> dict[str, object]:  # 新增代码+OutputProtocolV2: 定位结构化输出里单个 tool_call 的 schema；若没有这行代码，多个测试会重复写很长路径且容易继续依赖旧共享 arguments
        properties = schema["properties"]  # 新增代码+OutputProtocolV2: 读取根 schema 的 properties；若没有这行代码，后续无法进入 tool_calls 定义
        tool_calls = properties["tool_calls"]  # 新增代码+OutputProtocolV2: 读取 tool_calls 字段 schema；若没有这行代码，测试无法定位工具调用数组
        return tool_calls["items"]  # 新增代码+OutputProtocolV2: 返回 tool_calls 数组元素 schema；若没有这行代码，测试无法检查 anyOf 分支
    def _tool_call_branch_for_name(self, schema: dict[str, object], tool_name: str) -> dict[str, object]:  # 新增代码+OutputProtocolV2: 按工具名从 anyOf 中找到对应分支；若没有这行代码，测试无法精确检查单个工具自己的参数 schema
        item_schema = self._tool_call_item_schema_for_test(schema)  # 新增代码+OutputProtocolV2: 先定位 tool_call item schema；若没有这行代码，分支查找没有输入
        branches = item_schema.get("anyOf", []) if isinstance(item_schema, dict) else []  # 新增代码+OutputProtocolV2: 安全读取 anyOf 分支列表；若没有这行代码，旧 schema 会抛出不清楚的 KeyError
        self.assertIsInstance(branches, list)  # 新增代码+OutputProtocolV2: 断言 anyOf 必须是列表；若没有这行代码，错误 schema 类型可能被后续循环掩盖
        for branch in branches:  # 新增代码+OutputProtocolV2: 遍历每个工具专属分支；若没有这行代码，无法按工具名匹配
            if not isinstance(branch, dict):  # 新增代码+OutputProtocolV2: 跳过异常非字典分支；若没有这行代码，坏分支会让测试报无关异常
                continue  # 新增代码+OutputProtocolV2: 继续检查其他分支；若没有这行代码，一个坏分支会中断查找
            branch_properties = branch.get("properties", {})  # 新增代码+OutputProtocolV2: 读取分支字段定义；若没有这行代码，无法定位 name enum
            if not isinstance(branch_properties, dict):  # 新增代码+OutputProtocolV2: 防御 properties 不是对象；若没有这行代码，后续 get 会崩溃
                continue  # 新增代码+OutputProtocolV2: 跳过坏 properties 分支；若没有这行代码，测试失败信息不聚焦
            name_schema = branch_properties.get("name", {})  # 新增代码+OutputProtocolV2: 读取分支中的工具名 schema；若没有这行代码，无法判断当前分支属于哪个工具
            if isinstance(name_schema, dict) and name_schema.get("enum") == [tool_name]:  # 新增代码+OutputProtocolV2: 通过单值 enum 匹配目标工具；若没有这行代码，测试无法找到指定工具分支
                return branch  # 新增代码+OutputProtocolV2: 返回命中的工具专属分支；若没有这行代码，调用方拿不到 arguments schema
        self.fail(f"没有找到工具 {tool_name} 的 anyOf 输出分支。")  # 新增代码+OutputProtocolV2: 找不到分支时给出清楚失败信息；若没有这行代码，测试只会返回 None 导致后续异常
    def _tool_argument_schema_for_name(self, schema: dict[str, object], tool_name: str) -> dict[str, object]:  # 新增代码+OutputProtocolV2: 读取指定工具的专属 arguments schema；若没有这行代码，测试会继续读取旧共享 arguments 路径
        branch = self._tool_call_branch_for_name(schema, tool_name)  # 新增代码+OutputProtocolV2: 找到目标工具的 anyOf 分支；若没有这行代码，无法保证参数来自正确工具
        branch_properties = branch["properties"]  # 新增代码+OutputProtocolV2: 读取分支字段定义；若没有这行代码，无法进入 arguments 字段
        return branch_properties["arguments"]  # 新增代码+OutputProtocolV2: 返回该工具自己的 arguments schema；若没有这行代码，调用方无法断言参数隔离
    def _merged_tool_argument_schema(self, schema: dict[str, object]) -> dict[str, object]:  # 新增代码+OutputProtocolV2: 给旧测试提供“所有分支参数汇总视图”；若没有这行代码，历史测试会被迫继续依赖已移除的共享 arguments schema
        item_schema = self._tool_call_item_schema_for_test(schema)  # 新增代码+OutputProtocolV2: 定位 tool_call item schema；若没有这行代码，无法读取 anyOf 分支
        merged_properties: dict[str, object] = {}  # 新增代码+OutputProtocolV2: 准备汇总每个工具参数字段；若没有这行代码，旧测试无法继续检查某个参数是否至少在某个工具分支存在
        branches = item_schema.get("anyOf", []) if isinstance(item_schema, dict) else []  # 新增代码+OutputProtocolV2: 安全读取 anyOf 分支列表；若没有这行代码，旧 schema 会触发 KeyError
        for branch in branches:  # 新增代码+OutputProtocolV2: 遍历每个工具专属分支；若没有这行代码，无法汇总所有工具参数
            if not isinstance(branch, dict):  # 新增代码+OutputProtocolV2: 跳过异常分支；若没有这行代码，坏分支会让测试报无关异常
                continue  # 新增代码+OutputProtocolV2: 继续处理其他分支；若没有这行代码，单个坏分支会影响全部测试
            branch_properties = branch.get("properties", {})  # 新增代码+OutputProtocolV2: 读取分支字段定义；若没有这行代码，无法进入 arguments
            if not isinstance(branch_properties, dict):  # 新增代码+OutputProtocolV2: 防御 properties 不是对象；若没有这行代码，后续读取会崩溃
                continue  # 新增代码+OutputProtocolV2: 跳过坏分支；若没有这行代码，测试失败信息不聚焦
            argument_schema = branch_properties.get("arguments", {})  # 新增代码+OutputProtocolV2: 读取该分支的 arguments schema；若没有这行代码，无法汇总参数
            argument_properties = argument_schema.get("properties", {}) if isinstance(argument_schema, dict) else {}  # 新增代码+OutputProtocolV2: 安全读取 arguments.properties；若没有这行代码，无参数工具会导致异常
            if isinstance(argument_properties, dict):  # 新增代码+OutputProtocolV2: 只有参数字段是字典时才合并；若没有这行代码，异常 schema 会污染测试
                merged_properties.update(argument_properties)  # 新增代码+OutputProtocolV2: 把该工具参数加入汇总视图；若没有这行代码，旧测试看不到分支内参数
        return {"type": "object", "properties": merged_properties, "required": list(merged_properties.keys()), "additionalProperties": False}  # 新增代码+OutputProtocolV2: 返回类似旧 arguments 的汇总 schema；若没有这行代码，旧断言无法复用 properties/required 路径
    def _browser_automation_server_script(self) -> Path:  # 新增代码+BrowserAutomation: 提供浏览器自动化 MCP server 脚本路径 helper；若省略: 多个测试会重复拼路径且后续改名容易漏改
        return (TEST_ROOT / "browser_automation_mcp_server.py")  # 新增代码+BrowserAutomation: 返回与测试文件同目录的目标 server 文件；若省略: 红灯测试无法准确检查待实现脚本是否存在


__all__ = [name for name in globals() if not name.startswith("__") and name != "__all__"]  # Stage14: export helper names for split test modules.

