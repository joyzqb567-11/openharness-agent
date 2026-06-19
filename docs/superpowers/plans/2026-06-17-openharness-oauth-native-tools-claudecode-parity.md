# OpenHarness OAuth Native Tools ClaudeCode Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 OpenHarness 在 ChatGPT OAuth 后端上对齐 ClaudeCode/Codex 风格的原生 Responses tools 链路：顶层 `tools` 真实发给模型，模型返回原生 `function_call`、`tool_search_call`、`tool_search_output`，OpenHarness 能解析、执行、回填并继续下一轮。

**Architecture:** 保留当前 `filteredTools()`、`toolToAPISchema()`、`tool_search`、`execute_tool_calls()` 等已验证链路，新增一层 OpenAI Responses 原生工具协议适配层。先让 OAuth 模型支持“双协议”：默认继续走旧 JSON 输出协议，受开关控制时走原生 Responses tools；验证稳定后再把 OAuth 模型默认切到原生协议。

**Tech Stack:** Python 3、unittest、OpenAI Responses API schema、ChatGPT OAuth 后端 `https://chatgpt.com/backend-api/codex/responses`、CodeGraph、现有 `learning_agent` 模型/工具/运行时链路、`learning_agent/start_oauth_agent.bat` 真实可见终端验收。

**Computer Use Scope:** 本蓝图只对齐 Computer Use 的“模型协议层”：工具如何进入顶层 `tools`、如何被 `tool_search/defer_loading` 发现、如何返回原生 `function_call`、截图/观察结果如何回到下一轮模型。Windows 桌面执行器、权限 UI、系统级输入输出、外部 MCP 包内部实现、macOS TCC/Swift helper 不在本蓝图内改动；这些属于另一个 Windows Computer Use 底层能力蓝图。

---

## 0. 背景证据

这份蓝图来自 2026-06-17 的实测，不是推测。

官方公开文档确认：

- `tool_search` 通过顶层 `tools` 启用，格式是 `{"type": "tool_search"}`。
- namespace 格式是 `{"type": "namespace", "name": "...", "description": "...", "tools": [...]}`。
- `defer_loading: true` 放在 namespace 内部的 function 工具上，而不是放在 namespace 自己身上。
- `tool_search` 只支持 `gpt-5.4` 及之后模型。
- 官方文档入口：`https://developers.openai.com/api/docs/guides/tools-tool-search`

本机 ChatGPT OAuth 后端实测确认：

```text
endpoint=https://chatgpt.com/backend-api/codex/responses
model=gpt-5.5
baseline_no_tools -> HTTP 200, response.completed
native_function_tool -> HTTP 200, function_call name=echo_customer_id
hosted_tool_search_namespace_defer_loading -> HTTP 200, tool_search_call + tool_search_output + function_call namespace=crm
client_tool_search -> HTTP 200, tool_search_call execution=client
```

同时也实测确认：只把原生 `tools` 字段塞进 OpenHarness 当前 OAuth 请求体还不够。当前 `CodexOAuthChatModel` 仍然用 `text.format=json_schema` 和 `_build_prompt(messages, tools)` 要求模型输出自定义 JSON，所以模型会继续返回：

```json
{"decision_note":"...","text":"...","tool_calls":[]}
```

而不是走原生 `function_call` / `tool_search_call`。所以本蓝图的关键不是“加一个字段”，而是改完整协议链路。

## 1. 当前链路地图

先用 CodeGraph 定位，后续执行任务时也必须优先用 CodeGraph 复查：

```powershell
codegraph explore "CodexOAuthChatModel _build_responses_body _build_responses_input _parse_sse_response _extract_response_text LearningAgent run_events execute_tool_calls ModelMessage ToolCall filteredTools toolToAPISchema"
```

当前关键文件和职责：

- `learning_agent/models/adapters.py`
  - `OpenAIChatModel`：API key + Chat Completions 工具链路。
  - `CodexOAuthChatModel`：ChatGPT OAuth + Codex Responses 后端。
  - `_build_responses_body()`：当前 OAuth 请求体入口。
  - `_build_responses_input()`：当前把工具 schema 塞进 prompt 文本的入口。
  - `_parse_sse_response()` / `_extract_response_text()`：当前只提取文本，不保留原生 output item。

- `learning_agent/core/messages.py`
  - `ToolCall`：OpenHarness 内部工具调用对象。
  - `ModelMessage`：当前只包含 `decision_note`、`text`、`tool_calls`，没有原生 Responses output item。

- `learning_agent/core/agent.py`
  - `run_events()` 每轮调用 `catalog_runtime.available_tool_schemas(self)` 生成工具 schema。
  - `stream_chat_events(self.model, messages, tools)` 发模型请求。
  - `model_message.tool_calls` 非空时进入工具执行。
  - 工具结果通过 `message_builders.tool_result_messages_to_dicts(...)` 回填下一轮。

- `learning_agent/tools/pool.py`
  - `filteredTools()`：ClaudeCode 风格当前可用工具过滤入口。
  - `available_tool_schemas()`：当前把工具池转成 OpenAI Chat Completions 风格 schema。
  - `toolToAPISchema()`：当前公开名字已对齐 ClaudeCode，但输出形状仍是 Chat Completions function tool。

- `learning_agent/tools/search.py`
  - 当前 `tool_search` 是 OpenHarness 自己的常驻工具。
  - 目前它不是 OpenAI Responses 原生 `{"type": "tool_search"}`。

## 2. 成功标准

功能成功：

- OAuth 模型原生协议模式下，请求体顶层包含 `tools`。
- 顶层 `tools` 至少支持三类：
  - 普通 function tool。
  - `{"type": "tool_search"}`。
  - `{"type": "namespace", "name": "...", "tools": [...]}`，并支持内部 function 的 `defer_loading: true`。
- OAuth 模型能解析 Responses SSE 中的：
  - `response.output_item.added`
  - `response.output_item.done`
  - `response.function_call_arguments.delta`
  - `response.function_call_arguments.done`
  - `response.completed`
- OAuth 模型能把原生 `function_call` 转成内部 `ToolCall`。
- Hosted `tool_search` 返回的 `tool_search_call` 和 `tool_search_output` 必须被记录到日志/事件/调试证据里。
- Client `tool_search` 可以先作为后续阶段，不阻塞 hosted 模式上线；但蓝图必须保留接口位置。
- 每一轮模型请求前都必须重新计算 `filteredTools()`、deferred 工具集合和 Responses namespace，不能只在首轮缓存一次。
- Computer Use 工具必须进入明确的 `computer_use` namespace，不能长期和 read/edit/bash/browser/planning 全部塞进一个巨大 namespace。
- Computer Use 工具结果里的截图或观察图片必须能继续进入下一轮 Responses 原生视觉输入；如果图片回填丢失，本蓝图视为失败。
- 旧 JSON 输出协议仍有回退开关，避免一次性切换导致真实终端不可用。

对齐成功：

- OpenHarness OAuth 原生工具链路和 ClaudeCode/Codex 风格一致：工具作为 API 层参数传给模型，而不是只塞进 prompt。
- `filteredTools()` 仍负责“当前可用工具”。
- `toolToAPISchema()` 仍负责“工具定义转 API schema”，但需要按目标协议输出 Responses 兼容形状。
- `tool_search` 常驻入口仍保留给旧模型/非 Responses 模式；原生 OAuth 模式使用 OpenAI Responses `{"type": "tool_search"}`。
- 原生 OAuth 模式下，OpenHarness 本地 `tool_search` 和 Responses hosted `tool_search` 不能混为一谈：hosted `tool_search` 负责模型/API 层发现 deferred schema，本地 `tool_search` 只作为旧协议或 fallback 的兼容工具。

安全成功：

- 不把外部 MCP 包内部实现纳入对齐范围。
- 不把 macOS TCC、Swift helper、`pbcopy/pbpaste` 纳入 Windows 对齐范围。
- 不在真实测试中操作用户账号、密码、支付、系统设置或私有文档。
- 任何功能修改后，最终回答前必须完成自动化测试；若涉及 agent 功能完成声明，还必须完成 `learning_agent/start_oauth_agent.bat` 真实可见终端验收。

## 3. 总体设计

### 3.1 新协议分层

新增一个独立协议层，避免把 Responses 原生协议散落到 `adapters.py` 大文件里：

```text
filteredTools()
  ↓
toolToAPISchema(tool, target="responses")
  ↓
ResponsesNativeToolPayload
  ↓
CodexOAuthChatModel._build_responses_body(...)
  ↓
ChatGPT OAuth backend / Codex Responses
  ↓
Responses output items
  ↓
ResponsesNativeOutputParser
  ↓
ModelMessage(tool_calls=[ToolCall(...)])
  ↓
execute_tool_calls()
  ↓
tool_result_messages_to_dicts()
```

### 3.2 双协议开关

新增环境变量：

```text
CODEX_OAUTH_NATIVE_TOOLS=0|1
```

默认第一阶段使用 `0`，避免破坏现有真实终端。完成测试和可见终端验收后，再单独任务改默认值。

### 3.3 原生 hosted tool_search 策略

第一阶段只做 hosted tool_search，但不能把 Computer Use 淹没在一个含义模糊的大包里：

```json
{
  "tools": [
    {
      "type": "namespace",
      "name": "core_code",
      "description": "Core OpenHarness coding tools for reading, editing, writing files, and running shell commands.",
      "tools": [
        {
          "type": "function",
          "name": "read",
          "description": "...",
          "parameters": {...}
        },
        {
          "type": "function",
          "name": "browser_click",
          "description": "...",
          "defer_loading": true,
          "parameters": {...}
        }
      ]
    },
    {
      "type": "namespace",
      "name": "computer_use",
      "description": "Windows Computer Use tools for safe desktop permission checks, observation, clipboard, and agent-owned app interaction.",
      "tools": [
        {
          "type": "function",
          "name": "request_access",
          "description": "...",
          "defer_loading": true,
          "parameters": {...}
        }
      ]
    },
    {"type": "tool_search"}
  ],
  "parallel_tool_calls": false
}
```

注意：不要把所有工具一股脑放进一个巨大 namespace。第一版至少要拆出 `computer_use` namespace；后续再继续按 capability pack 拆更多 namespace：

- `core_code`：read/write/edit/bash/tool_search。
- `browser`：浏览器工具。
- `computer_use`：Windows Computer Use 工具，至少包含 `request_access`、`list_granted_applications`、clipboard、observe/action 类工具。
- `planning`：计划/任务工具。
- `mcp`：外部 MCP 工具。

### 3.4 每轮重新判断 `filteredTools` 和 `defer_loading`

ClaudeCode 不是只在首轮计算工具可见性。它每次请求 Claude API 前都会重新判断：

```text
all tools
  ↓
isToolSearchEnabled(...)
  ↓
deferredToolNames
  ↓
filteredTools
  ↓
toolToAPISchema(..., deferLoading=willDefer(tool))
  ↓
API request tools
```

OpenHarness 必须照这个原则做：每一轮 `run_events()` 请求 OAuth 模型前，都要基于当前 agent 状态、已加载工具、pending select、scope gate、Computer Use 是否已有 agent-owned 窗口等条件，重新生成 Responses native tools。不要把 native `tools` 在 `CodexOAuthChatModel.__init__` 缓存成固定列表。

### 3.5 Hosted `tool_search` 和本地 `tool_search` 的边界

本蓝图第一阶段只要求 hosted `tool_search`：

- 请求体顶层加入 `{"type": "tool_search"}`。
- deferred function 留在 namespace 内，并带 `defer_loading: true`。
- 模型返回 `tool_search_call/tool_search_output/function_call` 时，OpenHarness 记录前两者，把 `function_call` 转成内部 `ToolCall` 执行。

本地 `learning_agent/tools/search.py` 里的 `tool_search` 暂时保留：

- 旧 JSON 协议继续用它。
- 非 Responses 模型继续用它。
- 如果未来要支持 `execution="client"` 的 Responses `tool_search_call`，再单独增加“client tool_search output 回填”任务，不和 hosted 第一阶段混做。

### 3.6 Computer Use 图片回填门禁

Computer Use 对齐不能只看文本工具调用。必须验证：

- 原生 `function_call` 可以触发 Computer Use 工具。
- Computer Use 工具返回的截图/观察图片不会被压缩流程吞掉。
- 下一轮 `_build_native_tools_input()` 能把现有 OpenHarness message 里的 `image_url` / `input_image` 转成 Responses 原生 `input_image`。
- 如果工具输出很长被 `_offload_tool_output_if_needed()` 摘要化，图片提取仍必须使用原始 `tool_output`。

如果这些条件任意一个失败，不能宣布 Computer Use native tools 对齐完成。

## 4. 文件结构

预计新增：

- `learning_agent/models/responses_native.py`
  - 负责 Responses 原生工具 schema、namespace、tool_search、SSE output item 解析。

- `learning_agent/tests/test_responses_native_tool_schema.py`
  - 测试 Chat Completions schema 能转换成 Responses function schema。
  - 测试 namespace + defer_loading + tool_search 形状。

- `learning_agent/tests/test_responses_native_output_parser.py`
  - 测试 SSE 事件解析成 `ToolCall`。
  - 测试 hosted `tool_search_call` / `tool_search_output` 被保留为证据但不当成本地工具执行。

- `learning_agent/tests/test_codex_oauth_native_tools_body.py`
  - 测试 `CodexOAuthChatModel` 在开关打开时把工具放到顶层 `tools`。
  - 测试开关关闭时仍走旧 JSON 协议。

- `learning_agent/acceptance_controller/scenarios/agent_capability_oauth_native_tools_visible_terminal.json`
  - 真实可见终端验收场景。

预计修改：

- `learning_agent/models/adapters.py`
  - `CodexOAuthChatModel` 增加 native tools 模式。
  - `_parse_sse_response()` 保留原生 output item。
  - `chat()` 根据模式选择旧 JSON parser 或新 Responses parser。

- `learning_agent/tools/types.py`
  - `toolToAPISchema()` 增加 target 参数，或新增旁路函数，避免破坏旧 Chat Completions。

- `learning_agent/tools/pool.py`
  - `available_tool_schemas()` 保留旧形状。
  - 新增 `available_responses_tool_schemas()` 或让调用方明确传 target。

- `learning_agent/tools/catalog_runtime.py`
  - 新增原生 Responses 工具池入口，仍复用 `filteredTools()`。

- `learning_agent/core/messages.py`
  - `ModelMessage` 可增加 `native_output_items` 或 `model_events` 字段，用于审计 `tool_search_call` / `tool_search_output`。

- `learning_agent/core/agent.py`
  - 不急着重写主循环。优先让 OAuth 模型把原生 function_call 转回现有 `ToolCall`，复用现有工具执行器。
  - 只在需要记录原生 output item 时增加事件 payload。

- `agent_memory/context.md`
  - 记录本次协议对齐范围。

- `agent_memory/progress.md`
  - 记录每个任务执行状态。

- `agent_memory/bugs.md`
  - 记录验证中发现的真实问题。

---

## Task 1: 冻结协议证据和范围

**Files:**
- Modify: `agent_memory/context.md`
- Modify: `agent_memory/progress.md`

- [ ] **Step 1: 记录官方和实测证据**

把以下内容追加到 `agent_memory/context.md`：

```markdown
## OAuth Native Responses Tools Parity - 2026-06-17

- 目标：让 OpenHarness OAuth 模型对齐 ClaudeCode/Codex 风格的原生 Responses tools 链路。
- 官方格式：顶层 `tools` 支持 function、namespace、tool_search；`defer_loading: true` 放在 namespace 内部 function 上。
- 本机实测：`https://chatgpt.com/backend-api/codex/responses` 在 ChatGPT OAuth token 下接受 native function、hosted tool_search、client tool_search。
- 当前缺口：OpenHarness 仍用 `text.format=json_schema` + prompt 内工具清单，让模型输出自定义 JSON，而不是原生 Responses output items。
- 边界：不处理外部 MCP 包内部实现，不处理 macOS TCC/Swift helper/pbcopy/pbpaste，不处理 API key 路线默认切换。
```

- [ ] **Step 2: 记录执行入口**

把以下内容追加到 `agent_memory/progress.md`：

```markdown
## 2026-06-17 OAuth Native Tools ClaudeCode Parity Plan

- 计划文件：`docs/superpowers/plans/2026-06-17-openharness-oauth-native-tools-claudecode-parity.md`
- 当前阶段：Task 1，冻结协议证据和范围。
- 成功标准：OAuth native tools 模式下，工具真实出现在顶层 `tools`，模型返回原生 `function_call/tool_search_call/tool_search_output`，OpenHarness 能解析并执行 function_call。
- 停止条件：真实 OAuth 后端不再接受该格式、模型版本低于 `gpt-5.4`、或真实终端验收无法完成。
```

- [ ] **Step 3: 用 CodeGraph 固定当前链路**

Run:

```powershell
codegraph explore "CodexOAuthChatModel _build_responses_body _build_responses_input _parse_sse_response _extract_response_text LearningAgent run_events execute_tool_calls ModelMessage ToolCall filteredTools toolToAPISchema"
```

Expected:

```text
Exploration:
```

- [ ] **Step 4: Commit**

```powershell
git add agent_memory/context.md agent_memory/progress.md
git commit -m "docs: record oauth native tools parity scope"
```

## Task 2: 新增 Responses 原生工具 schema 层

**Files:**
- Create: `learning_agent/models/responses_native.py`
- Create: `learning_agent/tests/test_responses_native_tool_schema.py`
- Modify: `learning_agent/tools/types.py`
- Modify: `learning_agent/tools/pool.py`
- Modify: `learning_agent/tools/catalog_runtime.py`
- Create: `learning_agent/test/oauth_native_tools_schema_20260617/...`

- [ ] **Step 1: 写失败测试**

创建 `learning_agent/tests/test_responses_native_tool_schema.py`：

```python
from __future__ import annotations

import unittest

from learning_agent.models.responses_native import (
    build_hosted_tool_search_tools_by_namespace,
    build_hosted_tool_search_tools,
    chat_completion_tool_to_responses_function,
)


class ResponsesNativeToolSchemaTests(unittest.TestCase):
    def test_chat_completion_function_tool_converts_to_responses_function(self) -> None:
        schema = {
            "type": "function",
            "function": {
                "name": "read",
                "description": "Read a file.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                    "additionalProperties": False,
                },
            },
        }

        result = chat_completion_tool_to_responses_function(schema)

        self.assertEqual(result["type"], "function")
        self.assertEqual(result["name"], "read")
        self.assertEqual(result["description"], "Read a file.")
        self.assertEqual(result["parameters"]["properties"]["path"]["type"], "string")

    def test_build_hosted_tool_search_tools_wraps_deferred_functions_in_namespace(self) -> None:
        function_tools = [
            {
                "type": "function",
                "function": {
                    "name": "read",
                    "description": "Read a file.",
                    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "browser_click",
                    "description": "Click in browser.",
                    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
                },
            },
        ]

        result = build_hosted_tool_search_tools(
            function_tools,
            namespace_name="openharness",
            deferred_tool_names={"browser_click"},
        )

        self.assertEqual(result[0]["type"], "namespace")
        self.assertEqual(result[0]["name"], "openharness")
        self.assertEqual(result[1], {"type": "tool_search"})
        deferred = [tool for tool in result[0]["tools"] if tool["name"] == "browser_click"][0]
        eager = [tool for tool in result[0]["tools"] if tool["name"] == "read"][0]
        self.assertTrue(deferred["defer_loading"])
        self.assertNotIn("defer_loading", eager)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行失败测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_responses_native_tool_schema
```

Expected:

```text
FAILED
```

失败原因应是 `learning_agent.models.responses_native` 不存在。

- [ ] **Step 3: 新增最小实现**

创建 `learning_agent/models/responses_native.py`。执行时必须按 `AGENTS.md` 要求给新增代码逐行补中文注释。核心接口必须包含：

```python
from __future__ import annotations

from typing import Any


def chat_completion_tool_to_responses_function(tool_schema: dict[str, Any]) -> dict[str, Any]:
    function_schema = tool_schema.get("function", {})
    return {
        "type": "function",
        "name": str(function_schema.get("name", "")),
        "description": str(function_schema.get("description", "")),
        "parameters": function_schema.get("parameters", {"type": "object", "properties": {}, "additionalProperties": False}),
    }


def build_hosted_tool_search_tools(
    tool_schemas: list[dict[str, Any]],
    *,
    namespace_name: str,
    deferred_tool_names: set[str],
) -> list[dict[str, Any]]:
    namespace_tools: list[dict[str, Any]] = []
    for tool_schema in tool_schemas:
        function_tool = chat_completion_tool_to_responses_function(tool_schema)
        if function_tool["name"] in deferred_tool_names:
            function_tool["defer_loading"] = True
        namespace_tools.append(function_tool)
    return [
        {
            "type": "namespace",
            "name": namespace_name,
            "description": "OpenHarness tools available to this agent turn.",
            "tools": namespace_tools,
        },
        {"type": "tool_search"},
    ]
```

- [ ] **Step 4: 跑测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_responses_native_tool_schema
```

Expected:

```text
OK
```

- [ ] **Step 5: 接入工具池但不改变默认行为**

在 `learning_agent/tools/pool.py` 或 `learning_agent/tools/catalog_runtime.py` 新增 Responses schema 入口。名字建议清晰：

```python
available_responses_tool_schemas(agent: Any) -> list[dict[str, Any]]
```

第一版可以复用旧 `available_tool_schemas(agent)` 结果，再通过 `build_hosted_tool_search_tools(...)` 包装。

- [ ] **Step 6: 备份学习副本**

把新增/修改代码另存到：

```text
learning_agent/test/oauth_native_tools_schema_20260617/
```

- [ ] **Step 7: Commit**

```powershell
git add learning_agent/models/responses_native.py learning_agent/tests/test_responses_native_tool_schema.py learning_agent/tools/types.py learning_agent/tools/pool.py learning_agent/tools/catalog_runtime.py learning_agent/test/oauth_native_tools_schema_20260617
git commit -m "feat: add responses native tool schema builder"
```

## Task 2A: 补强 Computer Use namespace 和每轮 defer 判断

**Files:**
- Modify: `learning_agent/models/responses_native.py`
- Modify: `learning_agent/tests/test_responses_native_tool_schema.py`
- Modify: `learning_agent/tools/catalog_runtime.py`
- Modify: `learning_agent/tools/pool.py`
- Create: `learning_agent/test/oauth_native_computer_use_namespace_20260617/...`

- [ ] **Step 1: 写 Computer Use namespace 失败测试**

在 `learning_agent/tests/test_responses_native_tool_schema.py` 增加测试。这个测试的目的不是执行桌面动作，而是锁定协议形状：Computer Use 工具必须进入 `computer_use` namespace，并且可延迟加载。

```python
def test_computer_use_tools_are_grouped_in_computer_use_namespace(self) -> None:
    function_tools = [
        {
            "type": "function",
            "function": {
                "name": "read",
                "description": "Read a file.",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "request_access",
                "description": "Request Windows Computer Use access.",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_granted_applications",
                "description": "List granted Windows applications.",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        },
    ]

    result = build_hosted_tool_search_tools_by_namespace(
        function_tools,
        deferred_tool_names={"request_access", "list_granted_applications"},
        namespace_for_tool=lambda name: "computer_use" if name in {"request_access", "list_granted_applications"} else "core_code",
    )

    namespaces = {item["name"]: item for item in result if item.get("type") == "namespace"}

    self.assertIn("core_code", namespaces)
    self.assertIn("computer_use", namespaces)
    self.assertEqual(result[-1], {"type": "tool_search"})
    computer_use_names = {tool["name"] for tool in namespaces["computer_use"]["tools"]}
    self.assertEqual(computer_use_names, {"request_access", "list_granted_applications"})
    for tool in namespaces["computer_use"]["tools"]:
        self.assertTrue(tool["defer_loading"])
```

- [ ] **Step 2: 运行失败测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_responses_native_tool_schema
```

Expected:

```text
FAILED
```

失败原因应是 `build_hosted_tool_search_tools_by_namespace` 不存在，或 Computer Use 工具仍被塞进单一 namespace。

- [ ] **Step 3: 实现 namespace 分组 builder**

在 `learning_agent/models/responses_native.py` 增加分组入口。执行时必须按 `AGENTS.md` 给新增代码逐行补中文注释。

核心接口：

```python
def build_hosted_tool_search_tools_by_namespace(
    tool_schemas: list[dict[str, Any]],
    *,
    deferred_tool_names: set[str],
    namespace_for_tool: Callable[[str], str],
    namespace_descriptions: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for tool_schema in tool_schemas:
        function_tool = chat_completion_tool_to_responses_function(tool_schema)
        tool_name = str(function_tool.get("name", ""))
        namespace_name = namespace_for_tool(tool_name) or "openharness"
        if tool_name in deferred_tool_names:
            function_tool["defer_loading"] = True
        buckets.setdefault(namespace_name, []).append(function_tool)

    descriptions = namespace_descriptions or {}
    native_tools: list[dict[str, Any]] = []
    for namespace_name in sorted(buckets):
        native_tools.append(
            {
                "type": "namespace",
                "name": namespace_name,
                "description": descriptions.get(namespace_name, f"OpenHarness {namespace_name} tools available to this agent turn."),
                "tools": buckets[namespace_name],
            }
        )
    native_tools.append({"type": "tool_search"})
    return native_tools
```

- [ ] **Step 4: 明确每轮动态计算，不缓存 native tools**

在 `learning_agent/tools/catalog_runtime.py` 或 `learning_agent/tools/pool.py` 的 Responses native tools 入口中写清楚：

```python
def available_responses_tool_schemas(agent: Any) -> list[dict[str, Any]]:
    current_tools = filteredTools(tool_catalog(agent), lambda tool: tool_policy_decision(agent, tool))
    current_chat_completion_schemas = available_tool_schemas(current_tools)
    deferred_tool_names = {tool.name for tool in current_tools if should_defer_in_responses_native_mode(agent, tool)}
    return build_hosted_tool_search_tools_by_namespace(
        current_chat_completion_schemas,
        deferred_tool_names=deferred_tool_names,
        namespace_for_tool=lambda name: responses_namespace_for_tool_name(agent, name),
        namespace_descriptions=responses_namespace_descriptions(),
    )
```

注意：这段伪代码中的 helper 名称可以按实际项目命名，但必须满足两件事：

- 每轮调用时重新走 `filteredTools()`。
- `computer_use` namespace 至少覆盖 `request_access`、`list_granted_applications`、clipboard、observe/action 类工具。

- [ ] **Step 5: 跑测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_responses_native_tool_schema
```

Expected:

```text
OK
```

- [ ] **Step 6: 备份学习副本**

复制新增/修改代码片段到：

```text
learning_agent/test/oauth_native_computer_use_namespace_20260617/
```

- [ ] **Step 7: Commit**

```powershell
git add learning_agent/models/responses_native.py learning_agent/tests/test_responses_native_tool_schema.py learning_agent/tools/catalog_runtime.py learning_agent/tools/pool.py learning_agent/test/oauth_native_computer_use_namespace_20260617
git commit -m "feat: group oauth native tools by namespace"
```

## Task 3: 解析 Responses 原生 output item

**Files:**
- Modify: `learning_agent/models/responses_native.py`
- Create: `learning_agent/tests/test_responses_native_output_parser.py`
- Modify: `learning_agent/core/messages.py`
- Create: `learning_agent/test/oauth_native_output_parser_20260617/...`

- [ ] **Step 1: 写失败测试**

创建 `learning_agent/tests/test_responses_native_output_parser.py`：

```python
from __future__ import annotations

import unittest

from learning_agent.models.responses_native import parse_responses_output_items_to_model_message


class ResponsesNativeOutputParserTests(unittest.TestCase):
    def test_parse_function_call_output_item_to_tool_call(self) -> None:
        output = [
            {
                "type": "function_call",
                "name": "read",
                "call_id": "call_read_1",
                "arguments": "{\"path\":\"README.md\"}",
                "status": "completed",
            }
        ]

        message = parse_responses_output_items_to_model_message(output)

        self.assertEqual(message.tool_calls[0].name, "read")
        self.assertEqual(message.tool_calls[0].call_id, "call_read_1")
        self.assertEqual(message.tool_calls[0].arguments, {"path": "README.md"})

    def test_parse_hosted_tool_search_items_keeps_native_evidence(self) -> None:
        output = [
            {"type": "tool_search_call", "execution": "server", "status": "completed", "arguments": {"paths": ["openharness"]}},
            {"type": "tool_search_output", "execution": "server", "status": "completed", "tools": []},
            {
                "type": "function_call",
                "namespace": "openharness",
                "name": "browser_click",
                "call_id": "call_click_1",
                "arguments": "{\"x\":1,\"y\":2}",
                "status": "completed",
            },
        ]

        message = parse_responses_output_items_to_model_message(output)

        self.assertEqual(message.tool_calls[0].name, "browser_click")
        self.assertEqual(message.tool_calls[0].arguments, {"x": 1, "y": 2})
        self.assertEqual(len(message.native_output_items), 3)
        self.assertEqual(message.native_output_items[0]["type"], "tool_search_call")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行失败测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_responses_native_output_parser
```

Expected:

```text
FAILED
```

失败原因应是 parser 函数或 `ModelMessage.native_output_items` 不存在。

- [ ] **Step 3: 扩展 ModelMessage**

在 `learning_agent/core/messages.py` 给 `ModelMessage` 增加字段：

```python
native_output_items: list[dict[str, Any]] = field(default_factory=list)
```

执行时每一行必须补中文注释，说明没有这行会导致原生 `tool_search_call/tool_search_output` 审计证据丢失。

- [ ] **Step 4: 实现 parser**

在 `responses_native.py` 增加：

```python
import json

from learning_agent.core.messages import ModelMessage, ToolCall


def parse_responses_output_items_to_model_message(output_items: list[dict[str, Any]]) -> ModelMessage:
    tool_calls: list[ToolCall] = []
    text_parts: list[str] = []
    for index, item in enumerate(output_items):
        if item.get("type") == "function_call":
            arguments = json.loads(str(item.get("arguments") or "{}"))
            tool_calls.append(
                ToolCall(
                    name=str(item.get("name", "")),
                    arguments=arguments if isinstance(arguments, dict) else {},
                    call_id=str(item.get("call_id", "")) or f"call_native_{index}",
                )
            )
        if item.get("type") == "message":
            for content in item.get("content", []) if isinstance(item.get("content"), list) else []:
                if isinstance(content, dict) and isinstance(content.get("text"), str):
                    text_parts.append(content["text"])
    return ModelMessage(
        decision_note="Responses native output parsed.",
        text="".join(text_parts),
        tool_calls=tool_calls,
        native_output_items=list(output_items),
    )
```

注意：`ToolCall.call_id` 必须始终是字符串。不要传 `None`，否则 `tool_result_messages_to_dicts()` 和 Responses `function_call_output` 回填可能找不到对应调用。

- [ ] **Step 5: 跑测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_responses_native_output_parser
```

Expected:

```text
OK
```

- [ ] **Step 6: 备份学习副本**

复制修改片段到：

```text
learning_agent/test/oauth_native_output_parser_20260617/
```

- [ ] **Step 7: Commit**

```powershell
git add learning_agent/models/responses_native.py learning_agent/core/messages.py learning_agent/tests/test_responses_native_output_parser.py learning_agent/test/oauth_native_output_parser_20260617
git commit -m "feat: parse responses native output items"
```

## Task 4: CodexOAuthChatModel 支持 native tools 模式

**Files:**
- Modify: `learning_agent/models/adapters.py`
- Modify: `learning_agent/models/responses_native.py`
- Create: `learning_agent/tests/test_codex_oauth_native_tools_body.py`
- Create: `learning_agent/test/oauth_native_codex_body_20260617/...`

- [ ] **Step 1: 写请求体测试**

创建 `learning_agent/tests/test_codex_oauth_native_tools_body.py`：

```python
from __future__ import annotations

import unittest

from learning_agent.models.adapters import CodexOAuthChatModel


class CodexOAuthNativeToolsBodyTests(unittest.TestCase):
    def test_native_tools_body_puts_tools_at_top_level(self) -> None:
        model = CodexOAuthChatModel(model="gpt-5.5", native_tools_enabled=True)
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "read",
                    "description": "Read a file.",
                    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
                },
            }
        ]

        body = model._build_responses_body(messages=[{"role": "user", "content": "read README"}], tools=tools)

        self.assertIn("tools", body)
        self.assertEqual(body["tools"][0]["type"], "namespace")
        self.assertEqual(body["tools"][1], {"type": "tool_search"})
        self.assertEqual(body["parallel_tool_calls"], False)
        self.assertNotEqual(body.get("text", {}).get("format", {}).get("type"), "json_schema")

    def test_native_tools_body_can_expose_computer_use_namespace(self) -> None:
        model = CodexOAuthChatModel(model="gpt-5.5", native_tools_enabled=True)
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "request_access",
                    "description": "Request Windows Computer Use access.",
                    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
                },
            }
        ]

        body = model._build_responses_body(messages=[{"role": "user", "content": "check computer use access"}], tools=tools)

        namespaces = {item["name"]: item for item in body["tools"] if item.get("type") == "namespace"}
        self.assertIn("computer_use", namespaces)
        self.assertEqual(namespaces["computer_use"]["tools"][0]["name"], "request_access")
        self.assertTrue(namespaces["computer_use"]["tools"][0]["defer_loading"])

    def test_legacy_body_keeps_json_schema_output(self) -> None:
        model = CodexOAuthChatModel(model="gpt-5.5", native_tools_enabled=False)

        body = model._build_responses_body(messages=[{"role": "user", "content": "hello"}], tools=[])

        self.assertEqual(body["text"]["format"]["type"], "json_schema")
        self.assertNotIn("tools", body)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行失败测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_codex_oauth_native_tools_body
```

Expected:

```text
FAILED
```

失败原因应是 `native_tools_enabled` 参数不存在，或 body 未包含顶层 `tools`。

- [ ] **Step 3: 给 CodexOAuthChatModel 增加开关**

在 `CodexOAuthChatModel.__init__` 增加参数：

```python
native_tools_enabled: bool | None = None
```

并保存：

```python
self._native_tools_enabled = bool(native_tools_enabled) if native_tools_enabled is not None else os.environ.get("CODEX_OAUTH_NATIVE_TOOLS", "").strip() == "1"
```

执行时每行按 AGENTS.md 补中文注释。

- [ ] **Step 4: 改 `_build_responses_body()` 分支**

旧分支保留：

```python
if not self._native_tools_enabled:
    return old_json_schema_body
```

新分支返回：

```python
return {
    "model": self._model,
    "store": False,
    "stream": True,
    "instructions": self._build_native_tools_instructions(),
    "input": self._build_native_tools_input(messages=messages),
    "tools": build_hosted_tool_search_tools(...),
    "parallel_tool_calls": False,
}
```

不要在 native 模式继续把完整工具 schema 塞入 prompt 文本。

新分支里的 `tools` 必须来自每轮最新的 Responses native 工具池，不能在 `CodexOAuthChatModel` 初始化时缓存。也就是说，`agent.py` 每轮传进来的 `tools` 是当前轮的可见工具快照，OAuth adapter 只负责把这个快照转换成 Responses native schema。

- [ ] **Step 5: 新增 native instructions**

新增 `_build_native_tools_instructions()`，核心要求：

```text
你是 OpenHarness 的 coding agent 模型层。可用工具已经通过 Responses API 顶层 tools 提供。
如果需要外部动作，请返回原生 function_call，不要输出自定义 JSON tool_calls。
如果不需要工具，请正常用文本回答。
不要声称已经执行工具。
```

- [ ] **Step 6: 跑请求体测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_codex_oauth_native_tools_body
```

Expected:

```text
OK
```

- [ ] **Step 7: 备份学习副本**

复制修改片段到：

```text
learning_agent/test/oauth_native_codex_body_20260617/
```

- [ ] **Step 8: Commit**

```powershell
git add learning_agent/models/adapters.py learning_agent/models/responses_native.py learning_agent/tests/test_codex_oauth_native_tools_body.py learning_agent/test/oauth_native_codex_body_20260617
git commit -m "feat: add codex oauth native tools request mode"
```

## Task 5: SSE 解析保留原生 output items

**Files:**
- Modify: `learning_agent/models/adapters.py`
- Modify: `learning_agent/models/responses_native.py`
- Create or Modify: `learning_agent/tests/test_models_codex_oauth.py`
- Create: `learning_agent/test/oauth_native_sse_parser_20260617/...`

- [ ] **Step 1: 写 SSE 测试**

在 `learning_agent/tests/test_models_codex_oauth.py` 或新测试文件中加入：

```python
def test_parse_sse_response_preserves_native_function_call_output() -> None:
    raw_stream = "\n".join(
        [
            'data: {"type":"response.output_item.added","item":{"type":"function_call","name":"read","call_id":"call_1","arguments":"","status":"in_progress"}}',
            'data: {"type":"response.function_call_arguments.delta","item_id":"fc_1","delta":"{\\"path\\":"}',
            'data: {"type":"response.function_call_arguments.delta","item_id":"fc_1","delta":"\\"README.md\\"}"}',
            'data: {"type":"response.function_call_arguments.done","item_id":"fc_1","arguments":"{\\"path\\":\\"README.md\\"}"}',
            'data: {"type":"response.output_item.done","item":{"type":"function_call","name":"read","call_id":"call_1","arguments":"{\\"path\\":\\"README.md\\"}","status":"completed"}}',
            'data: {"type":"response.completed","response":{"status":"completed","output":[]}}',
        ]
    )

    parsed = CodexOAuthChatModel._parse_sse_response(raw_stream)

    self.assertEqual(parsed["output"][0]["type"], "function_call")
    self.assertEqual(parsed["output"][0]["name"], "read")
    self.assertEqual(parsed["output"][0]["arguments"], '{"path":"README.md"}')
```

再加入 hosted `tool_search` 证据保留测试：

```python
def test_parse_sse_response_preserves_hosted_tool_search_items() -> None:
    raw_stream = "\n".join(
        [
            'data: {"type":"response.output_item.done","item":{"type":"tool_search_call","id":"ts_1","execution":"server","status":"completed","arguments":{"query":"computer use"}}}',
            'data: {"type":"response.output_item.done","item":{"type":"tool_search_output","id":"tso_1","execution":"server","status":"completed","tools":[{"type":"function","name":"request_access"}]}}',
            'data: {"type":"response.output_item.done","item":{"type":"function_call","namespace":"computer_use","name":"request_access","call_id":"call_cu_1","arguments":"{\\"application\\":\\"notepad\\"}","status":"completed"}}',
            'data: {"type":"response.completed","response":{"status":"completed","output":[]}}',
        ]
    )

    parsed = CodexOAuthChatModel._parse_sse_response(raw_stream)
    output_types = [item["type"] for item in parsed["output"]]

    self.assertEqual(output_types, ["tool_search_call", "tool_search_output", "function_call"])
    self.assertEqual(parsed["output"][2]["namespace"], "computer_use")
```

- [ ] **Step 2: 运行失败测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_models_codex_oauth
```

Expected:

```text
FAILED
```

当前 parser 大概率只返回 `output_text` 或 completed response，不会合成 function_call output。

- [ ] **Step 3: 修改 `_parse_sse_response()`**

解析时需要收集：

- `response.output_item.added` 的 item。
- `response.function_call_arguments.delta` 的 delta。
- `response.function_call_arguments.done` 的完整 arguments。
- `response.output_item.done` 的最终 item。
- `response.completed.response.output` 作为兜底。

建议实现小 helper：

```python
collect_responses_output_items_from_sse(raw_stream: str) -> list[dict[str, Any]]
```

放在 `responses_native.py`，让 `adapters.py` 只调用 helper，避免继续膨胀。

- [ ] **Step 4: chat() 在 native 模式使用新 parser**

在 `CodexOAuthChatModel.chat()`：

```python
if self._native_tools_enabled:
    output_items = extract_output_items(response)
    return parse_responses_output_items_to_model_message(output_items)
```

旧 JSON 修复逻辑只保留给 legacy 模式。

- [ ] **Step 5: 跑测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_models_codex_oauth learning_agent.tests.test_responses_native_output_parser
```

Expected:

```text
OK
OK
```

- [ ] **Step 6: 备份学习副本**

复制修改片段到：

```text
learning_agent/test/oauth_native_sse_parser_20260617/
```

- [ ] **Step 7: Commit**

```powershell
git add learning_agent/models/adapters.py learning_agent/models/responses_native.py learning_agent/tests/test_models_codex_oauth.py learning_agent/test/oauth_native_sse_parser_20260617
git commit -m "feat: parse native responses tool output from oauth sse"
```

## Task 6: 原生 function_call 执行和结果回填

**Files:**
- Modify: `learning_agent/core/messages.py`
- Modify: `learning_agent/core/message_builders.py`
- Modify: `learning_agent/models/adapters.py`
- Create or Modify: `learning_agent/tests/test_message_builders.py`
- Create or Modify: `learning_agent/tests/test_codex_oauth_native_tools_body.py`
- Create: `learning_agent/test/oauth_native_tool_result_messages_20260617/...`

- [ ] **Step 1: 先确认现有回填格式**

Run:

```powershell
codegraph explore "tool_result_messages_to_dicts assistant_message_to_dict tool_call_to_openai_dict ModelMessage native_output_items"
```

Expected:

```text
Exploration:
```

- [ ] **Step 2: 写回填测试**

目标：原生 function_call 被转成内部 `ToolCall` 后，现有执行器能跑；下一轮消息回填仍然能让模型理解结果。

如果 OpenAI Responses 原生回填需要 `function_call_output` item，则测试应锁定该形状：

```python
def test_native_function_call_result_can_be_converted_to_responses_input_item() -> None:
    call = ToolCall(name="read", arguments={"path": "README.md"}, call_id="call_1")

    result = native_tool_result_message_to_responses_input_item(call, "file content")

    self.assertEqual(result["type"], "function_call_output")
    self.assertEqual(result["call_id"], "call_1")
    self.assertEqual(result["output"], "file content")
```

- [ ] **Step 2B: 写 Computer Use 图片回填测试**

目标：现有主循环仍然可以先把工具结果放进 OpenAI-style messages，但 OAuth native adapter 必须在下一轮请求前把其中的图片块转成 Responses `input_image`。这个测试防止 Computer Use 截图在协议切换后丢失。

在 `learning_agent/tests/test_codex_oauth_native_tools_body.py` 增加：

```python
def test_native_tools_input_keeps_computer_use_image_result_as_input_image(self) -> None:
    model = CodexOAuthChatModel(model="gpt-5.5", native_tools_enabled=True)
    messages = [
        {
            "role": "tool",
            "tool_call_id": "call_observe_1",
            "content": [
                {"type": "text", "text": "observe returned a screenshot"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64,abc123",
                        "detail": "high",
                    },
                },
            ],
        }
    ]

    native_input = model._build_native_tools_input(messages=messages)
    content_blocks = native_input[0]["content"]

    self.assertIn({"type": "function_call_output", "call_id": "call_observe_1", "output": "observe returned a screenshot"}, content_blocks)
    self.assertIn({"type": "input_image", "image_url": "data:image/jpeg;base64,abc123", "detail": "high"}, content_blocks)
```

如果最终实现选择把 `function_call_output` 和 `input_image` 拆成多个 Responses input item，也可以调整断言；但必须同时证明文本结果和图片结果都进入 native input。

- [ ] **Step 3: 实现 native tool result builder**

新增函数位置建议在 `learning_agent/core/message_builders.py`：

```python
def native_tool_result_message_to_responses_input_item(tool_call: ToolCall, output: str) -> dict[str, Any]:
    return {
        "type": "function_call_output",
        "call_id": tool_call.call_id,
        "output": output,
    }
```

执行时每行按 AGENTS.md 补中文注释。

- [ ] **Step 4: 决定主循环暂不大改**

第一阶段不直接把 `agent.py` 的 `messages` 全部改成 Responses item。更稳妥的方式：

- OAuth native 模型内部在 `_build_native_tools_input()` 把现有 OpenAI-style messages 转换成 Responses input items。
- 对已有 `tool` role message 识别为 `function_call_output`。
- 对已有 `image_url` / `input_image` 内容块识别为 Responses `input_image`。
- 对 Computer Use 长输出落盘后的场景，文本摘要可以走 `function_call_output`，但图片提取必须继续来自原始 `tool_output` 生成的图片 message。
- 这样 `agent.py` 主循环仍可复用现有 `messages.extend(tool_result_messages_to_dicts(...))`。

- [ ] **Step 5: 跑测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_message_builders learning_agent.tests.test_responses_native_output_parser learning_agent.tests.test_codex_oauth_native_tools_body
```

Expected:

```text
OK
OK
```

- [ ] **Step 6: 备份学习副本**

复制修改片段到：

```text
learning_agent/test/oauth_native_tool_result_messages_20260617/
```

- [ ] **Step 7: Commit**

```powershell
git add learning_agent/core/message_builders.py learning_agent/models/adapters.py learning_agent/tests/test_message_builders.py learning_agent/tests/test_codex_oauth_native_tools_body.py learning_agent/test/oauth_native_tool_result_messages_20260617
git commit -m "feat: add native responses tool result message builder"
```

## Task 7: OAuth native tools 真实后端最小集成测试

**Files:**
- Create: `learning_agent/tests/test_codex_oauth_native_tools_probe.py`
- Modify: `agent_memory/progress.md`

- [ ] **Step 1: 新增可跳过的真实后端 probe**

创建测试文件，但默认跳过，必须显式设置环境变量才跑，避免普通 CI 消耗真实账号请求：

```python
from __future__ import annotations

import os
import unittest

from learning_agent.models.adapters import CodexOAuthChatModel


@unittest.skipUnless(os.environ.get("RUN_CODEX_OAUTH_NATIVE_TOOLS_PROBE") == "1", "real OAuth probe disabled")
class CodexOAuthNativeToolsProbeTests(unittest.TestCase):
    def test_oauth_backend_accepts_hosted_tool_search(self) -> None:
        model = CodexOAuthChatModel.from_env()
        model._native_tools_enabled = True
        message = model.chat(
            messages=[
                {
                    "role": "user",
                    "content": "Use hosted tool search if needed, then call the deferred Windows Computer Use request_access tool for notepad. Do not claim success unless you return a tool call.",
                }
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "request_access",
                        "description": "Request Windows Computer Use access for a safe desktop application.",
                        "parameters": {
                            "type": "object",
                            "properties": {"application": {"type": "string"}},
                            "required": ["application"],
                            "additionalProperties": False,
                        },
                    },
                }
            ],
        )
        native_types = [item.get("type") for item in message.native_output_items]
        self.assertIn("tool_search_call", native_types)
        self.assertIn("tool_search_output", native_types)
        self.assertTrue(any(call.name == "request_access" for call in message.tool_calls))
```

- [ ] **Step 2: 默认测试应跳过**

Run:

```powershell
python -m unittest learning_agent.tests.test_codex_oauth_native_tools_probe
```

Expected:

```text
OK (skipped=1)
```

- [ ] **Step 3: 手动真实 probe**

只有在本机已有 OAuth token 且用户同意时运行：

```powershell
$env:RUN_CODEX_OAUTH_NATIVE_TOOLS_PROBE="1"
$env:CODEX_OAUTH_NATIVE_TOOLS="1"
python -m unittest learning_agent.tests.test_codex_oauth_native_tools_probe
```

Expected:

```text
OK
```

如果失败，把 HTTP 状态码、截断错误、`native_output_items` 类型列表写入 `agent_memory/bugs.md`，不要猜。不要记录 access token、refresh token、id_token 或完整 Authorization header。

- [ ] **Step 4: Commit**

```powershell
git add learning_agent/tests/test_codex_oauth_native_tools_probe.py agent_memory/progress.md agent_memory/bugs.md
git commit -m "test: add guarded oauth native tools backend probe"
```

## Task 8: 真实主循环开关验收

**Files:**
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_oauth_native_tools_visible_terminal.json`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_oauth_native_computer_use_visible_terminal.json`
- Modify: `agent_memory/progress.md`
- Create: `learning_agent/test/oauth_native_visible_terminal_20260617/...`

- [ ] **Step 1: 创建真实可见终端场景**

创建 `learning_agent/acceptance_controller/scenarios/agent_capability_oauth_native_tools_visible_terminal.json`：

```json
{
  "name": "agent_capability_oauth_native_tools_visible_terminal",
  "description": "验证 OpenHarness OAuth native Responses tools 模式能通过真实可见终端执行一个安全工具任务。",
  "start_bat": "H:\\codexworkplace\\sofeware\\OpenHarness-main\\learning_agent\\start_oauth_agent.bat",
  "visible_terminal_required": true,
  "environment": {
    "CODEX_OAUTH_NATIVE_TOOLS": "1"
  },
  "prompt": "请使用当前可用工具读取项目 README 或列出当前目录中的一个安全文件名，然后最终只在确认工具真实执行后输出 OAUTH_NATIVE_TOOLS_OK。",
  "success_token": "OAUTH_NATIVE_TOOLS_OK",
  "forbidden_terms": [
    "password",
    "支付",
    "系统设置",
    "用户私有文档"
  ]
}
```

再创建 `learning_agent/acceptance_controller/scenarios/agent_capability_oauth_native_computer_use_visible_terminal.json`。这个场景只做安全权限查询或授权申请，不允许点击、输入密码、操作私有文档或改系统设置：

```json
{
  "name": "agent_capability_oauth_native_computer_use_visible_terminal",
  "description": "验证 OpenHarness OAuth native Responses tools 模式能通过 computer_use namespace 调用安全的 Windows Computer Use 权限类工具。",
  "start_bat": "H:\\codexworkplace\\sofeware\\OpenHarness-main\\learning_agent\\start_oauth_agent.bat",
  "visible_terminal_required": true,
  "environment": {
    "CODEX_OAUTH_NATIVE_TOOLS": "1"
  },
  "prompt": "请使用 Computer Use 的安全权限类工具检查或申请 notepad 的访问权限；不要点击屏幕、不要输入密码、不要改系统设置。确认工具真实返回后，最终只输出 OAUTH_NATIVE_COMPUTER_USE_OK。",
  "success_token": "OAUTH_NATIVE_COMPUTER_USE_OK",
  "forbidden_terms": [
    "password",
    "支付",
    "系统设置",
    "用户私有文档",
    "点击完成",
    "已经手动操作"
  ]
}
```

- [ ] **Step 2: 执行自动化可见终端控制器，如果项目已有该控制器**

先查现有 acceptance controller 用法：

```powershell
rg -n "visible_terminal_required|acceptance_controller|start_oauth_agent" learning_agent/acceptance_controller learning_agent/tests
```

按现有方式运行该 scenario。

- [ ] **Step 3: 如果无法自动控制真实可见终端，手动执行**

Run:

```powershell
Start-Process -FilePath "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat"
```

在真实可见终端里输入：

```text
请使用当前可用工具读取项目 README 或列出当前目录中的一个安全文件名，然后最终只在确认工具真实执行后输出 OAUTH_NATIVE_TOOLS_OK。
```

Expected visible terminal output:

```text
OAUTH_NATIVE_TOOLS_OK
```

然后在同一个真实可见终端或重新启动的真实可见终端里输入：

```text
请使用 Computer Use 的安全权限类工具检查或申请 notepad 的访问权限；不要点击屏幕、不要输入密码、不要改系统设置。确认工具真实返回后，最终只输出 OAUTH_NATIVE_COMPUTER_USE_OK。
```

Expected visible terminal output:

```text
OAUTH_NATIVE_COMPUTER_USE_OK
```

- [ ] **Step 4: 记录验收状态**

如果真实可见终端通过，追加到 `agent_memory/progress.md`：

```markdown
### OAuth native tools visible terminal acceptance

- start_bat: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`
- env: `CODEX_OAUTH_NATIVE_TOOLS=1`
- success_token: `OAUTH_NATIVE_TOOLS_OK`
- computer_use_success_token: `OAUTH_NATIVE_COMPUTER_USE_OK`
- result: passed
```

如果无法观察或无法输入真实终端，必须写：

```markdown
### OAuth native tools visible terminal acceptance

- result: not completed
- reason: 当前 Codex 环境无法打开、观察或向用户本地可见终端输入内容。
- required final wording: 真实可见终端交互验收未完成，不能声明开发完成。
```

- [ ] **Step 5: Commit**

```powershell
git add learning_agent/acceptance_controller/scenarios/agent_capability_oauth_native_tools_visible_terminal.json learning_agent/acceptance_controller/scenarios/agent_capability_oauth_native_computer_use_visible_terminal.json agent_memory/progress.md learning_agent/test/oauth_native_visible_terminal_20260617
git commit -m "test: add oauth native tools visible terminal acceptance"
```

## Task 9: 默认切换决策

**Files:**
- Modify if approved: `learning_agent/models/adapters.py`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md` if any failure remains

- [ ] **Step 1: 汇总验证结果**

运行：

```powershell
python -m unittest learning_agent.tests.test_responses_native_tool_schema learning_agent.tests.test_responses_native_output_parser learning_agent.tests.test_codex_oauth_native_tools_body learning_agent.tests.test_models_codex_oauth
python -m py_compile learning_agent/models/responses_native.py learning_agent/models/adapters.py learning_agent/core/messages.py learning_agent/core/message_builders.py
```

Expected:

```text
OK
No output from py_compile
```

- [ ] **Step 2: 判断是否默认启用 native tools**

只有同时满足以下条件，才允许把 `CODEX_OAUTH_NATIVE_TOOLS` 默认逻辑改为开启：

- 自动化测试通过。
- 真实 OAuth probe 通过。
- 真实可见终端验收通过。
- 旧 JSON 协议仍可通过开关回退。
- Computer Use namespace 可见，安全权限类工具真实可调用。
- Computer Use 图片/观察结果能回到下一轮模型视觉输入。
- Hosted `tool_search_call` 和 `tool_search_output` 已在真实后端 probe 或真实调试日志中出现。

- [ ] **Step 3: 如果全部通过，默认启用**

把：

```python
os.environ.get("CODEX_OAUTH_NATIVE_TOOLS", "").strip() == "1"
```

改成类似：

```python
os.environ.get("CODEX_OAUTH_NATIVE_TOOLS", "1").strip() != "0"
```

必须保留 `CODEX_OAUTH_NATIVE_TOOLS=0` 回退路径。

- [ ] **Step 4: 如果任何门禁失败，不默认启用**

不要硬切默认值。追加到 `agent_memory/bugs.md`：

```markdown
## OAuth native tools default switch blocked - 2026-06-17

- Blocker:
- Evidence:
- Required next step:
```

- [ ] **Step 5: Commit**

```powershell
git add learning_agent/models/adapters.py agent_memory/progress.md agent_memory/bugs.md
git commit -m "feat: enable oauth native tools by default"
```

如果未默认启用，则 commit message 使用：

```powershell
git add agent_memory/progress.md agent_memory/bugs.md
git commit -m "docs: defer oauth native tools default switch"
```

## 5. 风险和停止条件

必须停止并汇报：

- OAuth 后端返回 `400 unknown parameter tools`、`unsupported tool type tool_search`、`unsupported model` 等直接否定证据。
- 当前模型低于 `gpt-5.4`，因为官方文档说明 `tool_search` 需要 `gpt-5.4` 及之后。
- 原生模式下 Computer Use 图片回填丢失，导致模型看不到截图。
- 原生模式下 Computer Use 工具没有进入 `computer_use` namespace，或被混入一个巨大的 `openharness` namespace 后无法通过 hosted `tool_search` 稳定发现。
- 原生模式下工具结果无法被下一轮模型消费，出现反复调用同一个工具。
- 原生模式下只返回文本，没有任何 `native_output_items` 证据，导致无法证明模型走的是 Responses 原生工具链路。
- 真实可见终端无法完成验收。
- 任何 probe 意外打印 access token、refresh token、id_token 或完整 Authorization header。

必须避免：

- 不要删除旧 JSON 协议回退路径。
- 不要把 OpenHarness 自己的 `tool_search` 工具和 Responses 原生 `{"type":"tool_search"}` 混为一谈。
- 不要把所有动态工具默认都 eager 暴露；这会抵消 defer_loading 的意义。
- 不要只在首轮计算 native tools；每轮请求前必须重新计算 `filteredTools()`、deferred 工具集合和 namespace。
- 不要只测试请求体 shape，不测试真实 output item 解析。
- 不要只测 read/bash 这类核心工具；Computer Use 至少要测安全权限类工具和图片回填。
- 不要只跑 API-key OpenAI SDK；本任务目标是 ChatGPT OAuth 后端。

## 6. 最终验收清单

- [ ] 已使用 CodeGraph 复查当前链路。
- [ ] `responses_native.py` 有单元测试覆盖 schema 和 output parser。
- [ ] `CodexOAuthChatModel` 旧 JSON 协议和 native tools 协议都有测试。
- [ ] native tools 请求体顶层含 `tools`。
- [ ] native tools 每轮重新从 `filteredTools()` 当前快照生成，没有在模型初始化时缓存。
- [ ] native tools 至少拆出 `computer_use` namespace。
- [ ] hosted `tool_search` 实测能产生 `tool_search_call` 和 `tool_search_output`。
- [ ] 原生 `function_call` 能转成内部 `ToolCall` 并进入 `execute_tool_calls()`。
- [ ] 工具结果能回填下一轮模型。
- [ ] Computer Use 安全权限类工具能在 OAuth native 模式下被发现并调用。
- [ ] Computer Use 图片/观察结果能作为 Responses `input_image` 进入下一轮模型。
- [ ] `CODEX_OAUTH_NATIVE_TOOLS=0` 可以回退旧协议。
- [ ] `CODEX_OAUTH_NATIVE_TOOLS=1` 通过真实可见终端验收。
- [ ] 新增/修改代码按 AGENTS.md 每行补中文注释。
- [ ] 新增/修改代码已另存学习副本到 `learning_agent/test`。
- [ ] `agent_memory/context.md`、`progress.md`、`bugs.md` 已更新。

## 7. 自检结果

规格覆盖：

- API 层 `tools`：Task 2、Task 4。
- `tool_search / namespace / defer_loading`：Task 2、Task 2A、Task 4、Task 7。
- Computer Use namespace：Task 2A、Task 4、Task 8。
- Computer Use 图片回填：Task 6、Task 8。
- 原生 `function_call / tool_search_call / tool_search_output`：Task 3、Task 5。
- 解析器和执行器消费：Task 3、Task 6。
- 长任务防跑偏：Task 1、Task 8、Task 9。
- 排除外部 MCP 包和系统差异：第 2 节和第 5 节。

占位扫描：

- 本计划没有使用占位结论。
- 每个任务都有明确文件、测试命令、期望结果和提交点。

类型一致性：

- `ModelMessage.native_output_items` 只做审计证据，不替代 `tool_calls`。
- `ToolCall` 仍是工具执行器唯一入口。
- Responses 原生 output item 由 `responses_native.py` 转成现有内部类型，避免主循环一次性大改。
