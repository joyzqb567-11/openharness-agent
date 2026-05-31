"""内置工具 schema 与能力包映射的唯一事实源。"""  # 新增代码+ToolSchemaSplit: 这个模块把工具定义从巨型 core.agent 中拆出来；若没有这行代码，维护者不知道这里为什么集中保存 schema。
from __future__ import annotations  # 新增代码+ToolSchemaSplit: 延迟解析类型注解；若没有这行代码，跨版本 Python 读取 list[dict[str, Any]] 更容易受运行时顺序影响。
from typing import Any  # 新增代码+ToolSchemaSplit: TOOL_SCHEMAS 需要通用 JSON 类型标注；若没有这行代码，schema 类型边界会变得不清楚。

TOOL_SCHEMAS: list[dict[str, Any]] = [  # 作用: 告诉真实模型当前 agent 暴露了哪些工具
    {  # 新增代码+极简工具面: 第一个原子工具 read 定义开始；若没有这段代码，模型首轮仍要依赖旧 read_file 工具名才能读取文件
        "type": "function",  # 新增代码+极简工具面: OpenAI-compatible 工具类型固定写 function；若没有这行代码，模型接口不会识别 read 是可调用工具
        "function": {  # 新增代码+极简工具面: function 容器保存 read 的名称、说明和参数；若没有这行代码，工具 schema 结构不完整
            "name": "read",  # 新增代码+极简工具面: 暴露给模型的读取原子工具名；若没有这行代码，首轮四工具集合缺少读取能力
            "description": "读取工作区内 UTF-8 文本文件；用于查看代码、提示词、skill 索引和配置文件。",  # 新增代码+极简工具面: 告诉模型 read 的适用场景；若没有这行代码，模型难以判断何时先读文件
            "parameters": {  # 新增代码+极简工具面: JSON Schema 描述 read 参数；若没有这行代码，模型不知道 read 需要哪些字段
                "type": "object",  # 新增代码+极简工具面: 约束 read 参数必须是对象；若没有这行代码，参数形状会变得模糊
                "properties": {  # 新增代码+极简工具面: 声明 read 允许的参数字段；若没有这行代码，path/offset/limit 无法进入 schema
                    "path": {"type": "string", "description": "工作区内要读取的文件路径，例如 learning_agent/skills/tool_list.md。"},  # 新增代码+极简工具面: path 指定目标文件；若没有这行代码，read 不知道读取哪个文件
                    "offset": {"type": "integer", "description": "可选，按字符偏移开始读取，默认 0。"},  # 新增代码+极简工具面: offset 支持读取长文件局部；若没有这行代码，大文件只能从头截断
                    "limit": {"type": "integer", "description": "可选，最多返回的字符数，默认 8000，最大 20000。"},  # 新增代码+极简工具面: limit 控制返回长度；若没有这行代码，读取大文件容易撑爆上下文
                },  # 新增代码+极简工具面: read 参数字段定义结束；若没有这行代码，Python 字典结构不完整
                "required": ["path"],  # 新增代码+极简工具面: read 必须提供 path；若没有这行代码，空读取请求会到工具层才失败
                "additionalProperties": False,  # 新增代码+极简工具面: 禁止 read 接收无关参数；若没有这行代码，模型可能把其他工具参数混进来
            },  # 新增代码+极简工具面: read 参数 schema 结束；若没有这行代码，工具定义不完整
        },  # 新增代码+极简工具面: read function 定义结束；若没有这行代码，工具 schema 不完整
    },  # 新增代码+极简工具面: read 工具定义结束；若没有这行代码，TOOL_SCHEMAS 列表语法不完整
    {  # 新增代码+极简工具面: 第二个原子工具 write 定义开始；若没有这段代码，模型首轮没有完整写文件能力
        "type": "function",  # 新增代码+极简工具面: OpenAI-compatible 工具类型固定写 function；若没有这行代码，模型接口不会识别 write 是可调用工具
        "function": {  # 新增代码+极简工具面: function 容器保存 write 的名称、说明和参数；若没有这行代码，工具 schema 结构不完整
            "name": "write",  # 新增代码+极简工具面: 暴露给模型的写入原子工具名；若没有这行代码，首轮四工具集合缺少写入能力
            "description": "写入或覆盖工作区内 UTF-8 文本文件；执行前工具层会请求用户确认。",  # 新增代码+极简工具面: 告诉模型 write 有副作用；若没有这行代码，模型可能把写入当成只读操作
            "parameters": {  # 新增代码+极简工具面: JSON Schema 描述 write 参数；若没有这行代码，模型不知道 write 需要路径和内容
                "type": "object",  # 新增代码+极简工具面: 约束 write 参数必须是对象；若没有这行代码，参数形状会变得模糊
                "properties": {  # 新增代码+极简工具面: 声明 write 允许的字段；若没有这行代码，path/content 无法进入 schema
                    "path": {"type": "string", "description": "工作区内要写入的文件路径。"},  # 新增代码+极简工具面: path 指定写入位置；若没有这行代码，write 不知道修改哪个文件
                    "content": {"type": "string", "description": "要写入文件的完整文本内容。"},  # 新增代码+极简工具面: content 指定完整文件正文；若没有这行代码，write 无法落盘任何内容
                },  # 新增代码+极简工具面: write 参数字段定义结束；若没有这行代码，Python 字典结构不完整
                "required": ["path", "content"],  # 新增代码+极简工具面: write 必须同时提供路径和内容；若没有这行代码，空写入可能进入工具层才失败
                "additionalProperties": False,  # 新增代码+极简工具面: 禁止 write 接收无关参数；若没有这行代码，模型可能混入 edit/bash 字段
            },  # 新增代码+极简工具面: write 参数 schema 结束；若没有这行代码，工具定义不完整
        },  # 新增代码+极简工具面: write function 定义结束；若没有这行代码，工具 schema 不完整
    },  # 新增代码+极简工具面: write 工具定义结束；若没有这行代码，TOOL_SCHEMAS 列表语法不完整
    {  # 新增代码+极简工具面: 第三个原子工具 edit 定义开始；若没有这段代码，模型首轮只能整文件覆盖而不能做定点替换
        "type": "function",  # 新增代码+极简工具面: OpenAI-compatible 工具类型固定写 function；若没有这行代码，模型接口不会识别 edit 是可调用工具
        "function": {  # 新增代码+极简工具面: function 容器保存 edit 的名称、说明和参数；若没有这行代码，工具 schema 结构不完整
            "name": "edit",  # 新增代码+极简工具面: 暴露给模型的编辑原子工具名；若没有这行代码，首轮四工具集合缺少定点编辑能力
            "description": "对工作区内文本文件执行 old_text 到 new_text 的定点替换；执行前工具层会请求用户确认。",  # 新增代码+极简工具面: 告诉模型 edit 用于小范围修改；若没有这行代码，模型可能滥用 write 覆盖整文件
            "parameters": {  # 新增代码+极简工具面: JSON Schema 描述 edit 参数；若没有这行代码，模型不知道如何表达定点替换
                "type": "object",  # 新增代码+极简工具面: 约束 edit 参数必须是对象；若没有这行代码，参数形状会变得模糊
                "properties": {  # 新增代码+极简工具面: 声明 edit 允许的字段；若没有这行代码，path/old_text/new_text 无法进入 schema
                    "path": {"type": "string", "description": "工作区内要编辑的文件路径。"},  # 新增代码+极简工具面: path 指定编辑文件；若没有这行代码，edit 不知道修改哪个文件
                    "old_text": {"type": "string", "description": "文件中必须唯一匹配或可替换的旧文本片段。"},  # 新增代码+极简工具面: old_text 指定要替换的原文；若没有这行代码，edit 无法安全定位改动位置
                    "new_text": {"type": "string", "description": "替换后的新文本片段。"},  # 新增代码+极简工具面: new_text 指定替换内容；若没有这行代码，edit 不知道要改成什么
                    "replace_all": {"type": "boolean", "description": "可选，是否替换所有匹配；默认 false，只允许唯一匹配。"},  # 新增代码+极简工具面: replace_all 控制多处替换；若没有这行代码，多匹配场景没有明确表达方式
                },  # 新增代码+极简工具面: edit 参数字段定义结束；若没有这行代码，Python 字典结构不完整
                "required": ["path", "old_text", "new_text"],  # 新增代码+极简工具面: edit 必须提供路径、旧文本和新文本；若没有这行代码，模糊编辑会到工具层才失败
                "additionalProperties": False,  # 新增代码+极简工具面: 禁止 edit 接收无关参数；若没有这行代码，模型可能混入 write/bash 字段
            },  # 新增代码+极简工具面: edit 参数 schema 结束；若没有这行代码，工具定义不完整
        },  # 新增代码+极简工具面: edit function 定义结束；若没有这行代码，工具 schema 不完整
    },  # 新增代码+极简工具面: edit 工具定义结束；若没有这行代码，TOOL_SCHEMAS 列表语法不完整
    {  # 新增代码+极简工具面: 第四个原子工具 bash 定义开始；若没有这段代码，模型首轮没有命令执行和测试能力
        "type": "function",  # 新增代码+极简工具面: OpenAI-compatible 工具类型固定写 function；若没有这行代码，模型接口不会识别 bash 是可调用工具
        "function": {  # 新增代码+极简工具面: function 容器保存 bash 的名称、说明和参数；若没有这行代码，工具 schema 结构不完整
            "name": "bash",  # 新增代码+极简工具面: 暴露给模型的命令执行原子工具名；若没有这行代码，首轮四工具集合缺少验证和命令能力
            "description": "在工作区内执行命令；Windows 环境下由 PowerShell 承载，执行前工具层会请求用户确认。",  # 新增代码+极简工具面: 说明 bash 在 Windows 上的实际承载；若没有这行代码，用户和模型可能误解底层 shell
            "parameters": {  # 新增代码+极简工具面: JSON Schema 描述 bash 参数；若没有这行代码，模型不知道命令和超时字段
                "type": "object",  # 新增代码+极简工具面: 约束 bash 参数必须是对象；若没有这行代码，参数形状会变得模糊
                "properties": {  # 新增代码+极简工具面: 声明 bash 允许的字段；若没有这行代码，command/cwd/timeout_seconds 无法进入 schema
                    "command": {"type": "string", "description": "要执行的命令文本。"},  # 新增代码+极简工具面: command 指定真实命令；若没有这行代码，bash 无法执行任何操作
                    "cwd": {"type": "string", "description": "可选，工作区内执行目录，默认工作区根目录。"},  # 新增代码+极简工具面: cwd 支持在子目录运行命令；若没有这行代码，所有命令只能在根目录执行
                    "timeout_seconds": {"type": "integer", "description": "可选，命令超时秒数，默认 60，最大 300。"},  # 新增代码+极简工具面: timeout_seconds 控制最长等待；若没有这行代码，卡住命令可能拖住 agent
                    "max_output_chars": {"type": "integer", "description": "可选，最多返回字符数，默认 8000，最大 20000。"},  # 新增代码+极简工具面: max_output_chars 控制输出长度；若没有这行代码，命令输出可能撑爆上下文
                },  # 新增代码+极简工具面: bash 参数字段定义结束；若没有这行代码，Python 字典结构不完整
                "required": ["command"],  # 新增代码+极简工具面: bash 必须提供 command；若没有这行代码，空命令会到工具层才失败
                "additionalProperties": False,  # 新增代码+极简工具面: 禁止 bash 接收无关参数；若没有这行代码，模型可能混入其他工具字段
            },  # 新增代码+极简工具面: bash 参数 schema 结束；若没有这行代码，工具定义不完整
        },  # 新增代码+极简工具面: bash function 定义结束；若没有这行代码，工具 schema 不完整
    },  # 新增代码+极简工具面: bash 工具定义结束；若没有这行代码，TOOL_SCHEMAS 列表语法不完整
    {  # 作用: 第一个工具定义开始
        "type": "function",  # 作用: OpenAI-compatible 工具类型固定写 function
        "function": {  # 作用: function 内部描述工具名称、说明和参数
            "name": "read_file",  # 作用: 工具名，模型必须用这个名字请求读取文件
            "description": "读取 learning_agent 工作区内的 UTF-8 文本文档。",  # 作用: 用自然语言帮助模型判断什么时候该用这个工具
            "parameters": {  # 作用: JSON Schema 描述工具参数
                "type": "object",  # 作用: 参数必须是对象
                "properties": {  # 作用: 声明对象允许的字段
                    "path": {"type": "string", "description": "要读取的相对路径，例如 memory.md。"},  # 作用: path 表示要读取哪个文件
                },  # 作用: properties 定义结束
                "required": ["path"],  # 作用: read_file 必须提供 path
                "additionalProperties": False,  # 作用: 不允许模型传入无关参数，减少歧义
            },  # 作用: parameters 定义结束
        },  # 作用: function 定义结束
    },  # 作用: 第一个工具定义结束
    {  # 作用: 第二个工具定义开始
        "type": "function",  # 作用: OpenAI-compatible 工具类型固定写 function
        "function": {  # 作用: function 内部描述工具名称、说明和参数
            "name": "write_file",  # 作用: 工具名，模型必须用这个名字请求写文件
            "description": "写入 learning_agent 工作区内的 UTF-8 文本文档；执行前工具层会请求用户确认。",  # 作用: 告诉模型这是有副作用工具
            "parameters": {  # 作用: JSON Schema 描述工具参数
                "type": "object",  # 作用: 参数必须是对象
                "properties": {  # 作用: 声明对象允许的字段
                    "path": {"type": "string", "description": "要写入的相对路径。"},  # 作用: path 表示目标文件
                    "content": {"type": "string", "description": "要写入文件的完整文本内容。"},  # 作用: content 表示写入内容
                },  # 作用: properties 定义结束
                "required": ["path", "content"],  # 作用: write_file 必须同时提供 path 和 content
                "additionalProperties": False,  # 作用: 不允许模型传入无关参数
            },  # 作用: parameters 定义结束
        },  # 作用: function 定义结束
    },  # 作用: 第二个工具定义结束
    {  # 作用: 第三个工具定义开始
        "type": "function",  # 作用: OpenAI-compatible 工具类型固定写 function
        "function": {  # 作用: function 内部描述工具名称、说明和参数
            "name": "append_memory",  # 作用: 工具名，模型必须用这个名字请求追加长期记忆
            "description": "把一条长期记忆追加到 memory.md；执行前工具层会请求用户确认。",  # 作用: 告诉模型这是会改变长期记忆的工具
            "parameters": {  # 作用: JSON Schema 描述工具参数
                "type": "object",  # 作用: 参数必须是对象
                "properties": {  # 作用: 声明对象允许的字段
                    "text": {"type": "string", "description": "要保存到长期记忆里的内容。"},  # 作用: text 表示记忆内容
                },  # 作用: properties 定义结束
                "required": ["text"],  # 作用: append_memory 必须提供 text
                "additionalProperties": False,  # 作用: 不允许模型传入无关参数
            },  # 作用: parameters 定义结束
        },  # 作用: function 定义结束
    },  # 作用: 第三个工具定义结束
    {  # 新增代码+PromptArchitectureV1: 注册提示词表面报告工具；若没有这行代码，模型请求查看本轮加载了哪些提示词块时会得到未知工具
        "type": "function",  # 新增代码+PromptArchitectureV1: 使用 OpenAI-compatible function 工具类型；若没有这行代码，模型工具 schema 结构不完整
        "function": {  # 新增代码+PromptArchitectureV1: 开始声明工具名称、说明和参数；若没有这行代码，工具定义没有标准 function 容器
            "name": "prompt_surface_report",  # 新增代码+PromptArchitectureV1: 定义工具名供模型调用；若没有这行代码，_execute_tool 无法匹配提示词表面报告请求
            "description": "只读报告：列出本轮真正加载进 system prompt 的提示词块、来源、加载策略、优先级、状态和粗略 token 估算；默认不输出完整提示词正文。",  # 新增代码+PromptArchitectureV1: 告诉模型该工具用于审计提示词表面；若没有这行代码，模型不知道何时使用此工具
            "parameters": {  # 新增代码+PromptArchitectureV1: 声明报告工具参数 schema；若没有这行代码，模型无法规范传入 include_block_text/include_evidence
                "type": "object",  # 新增代码+PromptArchitectureV1: 要求参数必须是对象；若没有这行代码，工具参数形状会变得不明确
                "properties": {  # 新增代码+PromptArchitectureV1: 开始列出允许的参数字段；若没有这行代码，布尔开关无法进入 schema
                    "include_block_text": {"type": "boolean", "description": "可选，默认 false；true 时允许输出已加载块正文摘要，false 时只输出元数据。"},  # 新增代码+PromptArchitectureV1: 提供正文开关；若没有这行代码，默认隐藏完整提示词正文的边界无法被模型表达
                    "include_evidence": {"type": "boolean", "description": "可选，默认 false；预留给 Evidence Ledger 报告使用。"},  # 新增代码+PromptArchitectureV1: 预留证据开关供 Task 5 扩展；若没有这行代码，下阶段调用会因额外参数被拒绝
                },  # 新增代码+PromptArchitectureV1: 结束 properties 定义；若没有这行代码，Python 字典结构不完整
                "required": [],  # 新增代码+PromptArchitectureV1: 允许无参数调用报告工具；若没有这行代码，模型可能被迫传入无意义字段
                "additionalProperties": False,  # 新增代码+PromptArchitectureV1: 禁止无关参数污染报告语义；若没有这行代码，模型乱传字段时行为不清晰
            },  # 新增代码+PromptArchitectureV1: 结束参数 schema；若没有这行代码，工具定义不完整
        },  # 新增代码+PromptArchitectureV1: 结束 function 定义；若没有这行代码，工具 schema 不完整
    },  # 新增代码+PromptArchitectureV1: 结束 prompt_surface_report 工具定义；若没有这行代码，TOOL_SCHEMAS 列表语法不完整
    {  # 新增代码+PromptArchitectureV1: 注册 token 预算报告工具；若没有这行代码，模型无法审计 prompt 和工具池预算
        "type": "function",  # 新增代码+PromptArchitectureV1: 使用 function 工具类型；若没有这行代码，模型接口无法识别这是可调用工具
        "function": {  # 新增代码+PromptArchitectureV1: 开始声明预算报告工具；若没有这行代码，工具元数据无处存放
            "name": "token_budget_report",  # 新增代码+PromptArchitectureV1: 定义工具名供模型调用；若没有这行代码，_execute_tool 无法匹配预算报告请求
            "description": "只读报告：汇总本轮 prompt blocks 粗略 token、estimated_total_tokens、当前工具池名称和工具 schema 粗略 token 估算。",  # 新增代码+PromptArchitectureV1: 告诉模型该工具用于查看预算；若没有这行代码，模型不知道此工具的用途
            "parameters": {  # 新增代码+PromptArchitectureV1: 声明预算报告参数 schema；若没有这行代码，include_tools 默认行为无法被描述
                "type": "object",  # 新增代码+PromptArchitectureV1: 要求参数必须是对象；若没有这行代码，工具参数边界不明确
                "properties": {  # 新增代码+PromptArchitectureV1: 开始列出允许的参数字段；若没有这行代码，include_tools 无法进入 schema
                    "include_tools": {"type": "boolean", "description": "可选，默认 true；是否列出当前工具池名称和工具 schema token 粗估。"},  # 新增代码+PromptArchitectureV1: 提供工具池开关；若没有这行代码，模型无法请求隐藏工具列表
                },  # 新增代码+PromptArchitectureV1: 结束 properties 定义；若没有这行代码，Python 字典结构不完整
                "required": [],  # 新增代码+PromptArchitectureV1: 允许无参数调用并使用 include_tools=true；若没有这行代码，默认预算报告不可直接调用
                "additionalProperties": False,  # 新增代码+PromptArchitectureV1: 禁止无关参数污染预算报告；若没有这行代码，错误参数可能被静默忽略
            },  # 新增代码+PromptArchitectureV1: 结束参数 schema；若没有这行代码，工具定义不完整
        },  # 新增代码+PromptArchitectureV1: 结束 function 定义；若没有这行代码，工具 schema 不完整
    },  # 新增代码+PromptArchitectureV1: 结束 token_budget_report 工具定义；若没有这行代码，TOOL_SCHEMAS 列表语法不完整
    {  # 新增代码+TodoWrite: 第四个工具定义开始，暴露读取任务清单能力；若省略: 模型无法像 Claude Code 一样查看当前计划状态
        "type": "function",  # 新增代码+TodoWrite: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TodoWrite: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "todo_read",  # 新增代码+TodoWrite: 工具名用于读取当前任务清单；若省略: 模型无法请求读取任务状态
            "description": "读取当前内部任务清单，用于长任务开始前查看已有计划和进度。",  # 新增代码+TodoWrite: 告诉模型什么时候该读任务清单；若省略: 模型可能不知道这个工具的使用场景
            "parameters": {  # 新增代码+TodoWrite: JSON Schema 描述 todo_read 参数；若省略: 结构化工具定义不完整
                "type": "object",  # 新增代码+TodoWrite: 参数必须是对象；若省略: 模型输出格式约束不明确
                "properties": {},  # 新增代码+TodoWrite: todo_read 不需要额外参数；若省略: 模型可能自造无关字段
                "required": [],  # 新增代码+TodoWrite: 声明没有必填参数；若省略: 严格 schema 可能误以为有缺失字段
                "additionalProperties": False,  # 新增代码+TodoWrite: 不允许模型传入无关参数；若省略: 参数污染会增加工具层处理歧义
            },  # 新增代码+TodoWrite: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TodoWrite: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TodoWrite: todo_read 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TodoWrite: 第五个工具定义开始，暴露写入任务清单能力；若省略: 模型无法维护长任务计划状态
        "type": "function",  # 新增代码+TodoWrite: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TodoWrite: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "todo_write",  # 新增代码+TodoWrite: 工具名用于完整覆盖当前任务清单；若省略: 模型无法请求更新任务状态
            "description": "完整写入当前内部任务清单；用于复杂任务拆解、更新 in_progress/pending/completed 状态。",  # 新增代码+TodoWrite: 告诉模型这个工具是任务管理工具；若省略: 模型可能把任务清单误当普通文件写入
            "parameters": {  # 新增代码+TodoWrite: JSON Schema 描述 todo_write 参数；若省略: 模型不知道要传 todos 数组
                "type": "object",  # 新增代码+TodoWrite: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+TodoWrite: 声明允许的参数字段；若省略: todos 参数无法进入模型输出 schema
                    "todos": {  # 新增代码+TodoWrite: todos 保存完整任务清单数组；若省略: 模型无法提交任务列表
                        "type": "array",  # 新增代码+TodoWrite: todos 必须是数组；若省略: 工具层难以区分单任务和任务列表
                        "description": "完整任务清单数组，每次调用都提交当前完整列表。",  # 新增代码+TodoWrite: 提醒模型 todo_write 是整体替换而不是追加；若省略: 模型可能只传单条导致丢失旧任务
                        "items": {  # 新增代码+TodoWrite: 定义数组中每个任务对象；若省略: 单条任务结构不受约束
                            "type": "object",  # 新增代码+TodoWrite: 每条任务必须是对象；若省略: 模型可能输出纯字符串任务
                            "properties": {  # 新增代码+TodoWrite: 声明任务对象字段；若省略: content/status/priority 无法被约束
                                "id": {"type": "string", "description": "可选任务 id；省略时工具层会自动生成。"},  # 新增代码+TodoWrite: id 方便后续稳定引用任务；若省略: 多轮更新中任务身份更容易混乱
                                "content": {"type": "string", "description": "任务内容，必须清楚描述一个可完成步骤。"},  # 新增代码+TodoWrite: content 保存任务文本；若省略: 任务没有可读目标
                                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"], "description": "任务状态。"},  # 新增代码+TodoWrite: status 限定任务进度枚举；若省略: 模型可能输出 doing/done 等工具不认识的状态
                                "priority": {"type": "string", "enum": ["high", "medium", "low"], "description": "可选优先级；省略时默认为 medium。"},  # 新增代码+TodoWrite: priority 帮助模型排序任务；若省略: 长任务缺少优先级信息
                            },  # 新增代码+TodoWrite: 任务字段定义结束；若省略: Python 字典结构不完整
                            "required": ["content", "status"],  # 新增代码+TodoWrite: 每条任务必须有内容和状态；若省略: 空任务或无状态任务可能进入清单
                            "additionalProperties": False,  # 新增代码+TodoWrite: 禁止任务对象额外字段；若省略: 模型可能写入工具层无法理解的字段
                        },  # 新增代码+TodoWrite: 单条任务 schema 结束；若省略: todos 数组定义不完整
                    },  # 新增代码+TodoWrite: todos 参数定义结束；若省略: properties 字典不完整
                },  # 新增代码+TodoWrite: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["todos"],  # 新增代码+TodoWrite: todo_write 必须提供 todos；若省略: 工具可能收到空参数却无法给出清晰约束
                "additionalProperties": False,  # 新增代码+TodoWrite: 不允许模型传入无关参数；若省略: 参数污染会增加工具层处理歧义
            },  # 新增代码+TodoWrite: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TodoWrite: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TodoWrite: todo_write 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+后台命令: 第六个工具定义开始，暴露启动后台命令能力；若省略: 模型无法启动长时间运行的测试、服务或监听任务
        "type": "function",  # 新增代码+后台命令: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+后台命令: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "start_background_command",  # 新增代码+后台命令: 工具名用于启动后台命令；若省略: 模型无法请求后台执行命令
            "description": "在工作区内启动一个后台 shell 命令，适合长时间运行的测试、开发服务或监听任务；执行前会请求用户确认。",  # 新增代码+后台命令: 告诉模型该工具适合长任务且需要权限；若省略: 模型可能误用同步工具或忽视风险
            "parameters": {  # 新增代码+后台命令: JSON Schema 描述启动参数；若省略: 模型不知道要传 command/cwd/label
                "type": "object",  # 新增代码+后台命令: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+后台命令: 声明允许的参数字段；若省略: 参数无法进入模型输出 schema
                    "command": {"type": "string", "description": "要启动的完整命令字符串。"},  # 新增代码+后台命令: command 保存真正执行的命令；若省略: 工具不知道要启动什么
                    "cwd": {"type": "string", "description": "可选工作目录，必须在 learning_agent 工作区内，省略时使用工作区根目录。"},  # 新增代码+后台命令: cwd 控制命令运行目录；若省略: 模型无法在项目子目录运行服务
                    "label": {"type": "string", "description": "可选标签，方便用户识别这个后台命令。"},  # 新增代码+后台命令: label 帮助区分多个后台任务；若省略: 多进程场景更难阅读
                },  # 新增代码+后台命令: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["command"],  # 新增代码+后台命令: 启动后台命令必须提供 command；若省略: 空命令可能进入工具层
                "additionalProperties": False,  # 新增代码+后台命令: 禁止模型传入无关参数；若省略: 参数污染会增加执行歧义
            },  # 新增代码+后台命令: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+后台命令: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+后台命令: start_background_command 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+后台命令: 第七个工具定义开始，暴露读取后台命令输出能力；若省略: 模型无法观察长任务进度
        "type": "function",  # 新增代码+后台命令: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+后台命令: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "read_background_command",  # 新增代码+后台命令: 工具名用于读取后台命令输出；若省略: 模型无法请求查看后台进程输出
            "description": "读取一个后台命令自上次读取以来的 stdout/stderr 增量输出和当前运行状态。",  # 新增代码+后台命令: 告诉模型这是观察后台任务的工具；若省略: 模型可能不知道启动后如何检查进度
            "parameters": {  # 新增代码+后台命令: JSON Schema 描述读取参数；若省略: 模型不知道要传 command_id
                "type": "object",  # 新增代码+后台命令: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+后台命令: 声明允许的参数字段；若省略: command_id/max_chars 无法进入输出 schema
                    "command_id": {"type": "string", "description": "start_background_command 返回的后台命令 id。"},  # 新增代码+后台命令: command_id 指定读取哪个进程；若省略: 工具无法定位后台任务
                    "max_chars": {"type": "integer", "description": "可选最大返回字符数，省略时默认 4000。"},  # 新增代码+后台命令: max_chars 控制输出长度；若省略: 长输出可能撑爆上下文
                },  # 新增代码+后台命令: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["command_id"],  # 新增代码+后台命令: 读取后台输出必须提供 command_id；若省略: 工具不知道读取哪个命令
                "additionalProperties": False,  # 新增代码+后台命令: 禁止模型传入无关参数；若省略: 参数污染会增加读取歧义
            },  # 新增代码+后台命令: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+后台命令: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+后台命令: read_background_command 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+后台命令: 第八个工具定义开始，暴露停止后台命令能力；若省略: 模型无法收束长时间运行的进程
        "type": "function",  # 新增代码+后台命令: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+后台命令: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "stop_background_command",  # 新增代码+后台命令: 工具名用于停止后台命令；若省略: 模型无法请求停止后台进程
            "description": "停止一个仍在运行的后台命令；执行前会请求用户确认。",  # 新增代码+后台命令: 告诉模型停止进程是需要确认的操作；若省略: 模型可能低估停止任务风险
            "parameters": {  # 新增代码+后台命令: JSON Schema 描述停止参数；若省略: 模型不知道要传 command_id
                "type": "object",  # 新增代码+后台命令: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+后台命令: 声明允许的参数字段；若省略: command_id 无法进入输出 schema
                    "command_id": {"type": "string", "description": "start_background_command 返回的后台命令 id。"},  # 新增代码+后台命令: command_id 指定停止哪个进程；若省略: 工具无法定位后台任务
                },  # 新增代码+后台命令: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["command_id"],  # 新增代码+后台命令: 停止后台命令必须提供 command_id；若省略: 工具不知道停止哪个命令
                "additionalProperties": False,  # 新增代码+后台命令: 禁止模型传入无关参数；若省略: 参数污染会增加停止歧义
            },  # 新增代码+后台命令: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+后台命令: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+后台命令: stop_background_command 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+Notebook工具: 第九个工具定义开始，暴露读取 .ipynb notebook 能力；若省略: 模型无法像 Claude Code 一样查看 Notebook cell 结构
        "type": "function",  # 新增代码+Notebook工具: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+Notebook工具: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "notebook_read",  # 新增代码+Notebook工具: 工具名用于读取 notebook 摘要或指定 cell；若省略: 模型无法请求 NotebookRead
            "description": "读取工作区内 .ipynb notebook 的 cell 摘要；可选读取指定 cell，避免把 JSON 当普通文本直接展开。",  # 新增代码+Notebook工具: 告诉模型该工具适合查看 notebook；若省略: 模型可能用普通 read_file 读出冗长 JSON
            "parameters": {  # 新增代码+Notebook工具: JSON Schema 描述读取 notebook 的参数；若省略: 模型不知道要传 path/cell_index/max_chars
                "type": "object",  # 新增代码+Notebook工具: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+Notebook工具: 声明允许的参数字段；若省略: path/cell_index/max_chars 无法进入输出 schema
                    "path": {"type": "string", "description": "要读取的 .ipynb 文件路径，必须在 learning_agent 工作区内。"},  # 新增代码+Notebook工具: path 指定 notebook 文件；若省略: 工具不知道读取哪个文件
                    "cell_index": {"type": "integer", "description": "可选 cell 索引；省略时返回所有 cell 摘要。"},  # 新增代码+Notebook工具: cell_index 支持只看单个 cell；若省略: 大 notebook 难以精确定位
                    "max_chars": {"type": "integer", "description": "可选最大返回字符数，省略时默认 4000。"},  # 新增代码+Notebook工具: max_chars 控制输出长度；若省略: 大 notebook 可能撑爆上下文
                },  # 新增代码+Notebook工具: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["path"],  # 新增代码+Notebook工具: 读取 notebook 必须提供 path；若省略: 空路径会进入工具层
                "additionalProperties": False,  # 新增代码+Notebook工具: 禁止模型传入无关参数；若省略: 参数污染会增加读取歧义
            },  # 新增代码+Notebook工具: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+Notebook工具: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+Notebook工具: notebook_read 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+Notebook工具: 第十个工具定义开始，暴露编辑 .ipynb cell source 能力；若省略: 模型无法安全修改 Notebook cell
        "type": "function",  # 新增代码+Notebook工具: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+Notebook工具: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "notebook_edit",  # 新增代码+Notebook工具: 工具名用于替换指定 cell source；若省略: 模型无法请求 NotebookEdit
            "description": "在权限确认后替换工作区内 .ipynb notebook 指定 cell 的 source；适合小范围修改已有 cell。",  # 新增代码+Notebook工具: 告诉模型该工具会修改文件且需要权限；若省略: 模型可能误以为它是只读工具
            "parameters": {  # 新增代码+Notebook工具: JSON Schema 描述编辑 notebook 的参数；若省略: 模型不知道要传 path/cell_index/source
                "type": "object",  # 新增代码+Notebook工具: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+Notebook工具: 声明允许的参数字段；若省略: 编辑参数无法进入输出 schema
                    "path": {"type": "string", "description": "要编辑的 .ipynb 文件路径，必须在 learning_agent 工作区内。"},  # 新增代码+Notebook工具: path 指定目标 notebook；若省略: 工具不知道写哪个文件
                    "cell_index": {"type": "integer", "description": "要替换 source 的 cell 索引，从 0 开始。"},  # 新增代码+Notebook工具: cell_index 指定目标 cell；若省略: 工具可能误改错误单元格
                    "source": {"type": "string", "description": "新的 cell source 文本，会按行写回 notebook JSON。"},  # 新增代码+Notebook工具: source 保存新的 cell 内容；若省略: 编辑工具没有可写内容
                },  # 新增代码+Notebook工具: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["path", "cell_index", "source"],  # 新增代码+Notebook工具: 编辑 notebook 必须提供路径、cell 索引和新内容；若省略: 半成品编辑请求可能进入工具层
                "additionalProperties": False,  # 新增代码+Notebook工具: 禁止模型传入无关参数；若省略: 参数污染会增加写入歧义
            },  # 新增代码+Notebook工具: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+Notebook工具: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+Notebook工具: notebook_edit 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+ToolSearch: 第十一个工具定义开始，暴露工具搜索能力；若省略: 工具数量变多后模型只能靠完整 schema 猜测可用工具
        "type": "function",  # 新增代码+ToolSearch: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+ToolSearch: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "tool_search",  # 新增代码+ToolSearch: 工具名用于搜索当前可见工具；若省略: 模型无法请求 ToolSearch
            "description": "按关键词搜索当前可见的内置工具和已启动 MCP 工具，返回工具名、来源、说明和参数名；适合工具很多或不确定该用哪个工具时。",  # 新增代码+ToolSearch: 告诉模型何时使用工具搜索；若省略: 模型可能继续盲目猜工具名
            "parameters": {  # 新增代码+ToolSearch: JSON Schema 描述工具搜索参数；若省略: 模型不知道要传 query/max_results
                "type": "object",  # 新增代码+ToolSearch: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+ToolSearch: 声明允许的参数字段；若省略: query/max_results 无法进入输出 schema
                    "query": {"type": "string", "description": "搜索关键词，可以是能力、工具名、MCP server 名或参数名，例如 weather、grep、Notebook。"},  # 新增代码+ToolSearch: query 保存搜索意图；若省略: 工具不知道用户想找哪类能力
                    "max_results": {"type": "integer", "description": "可选最大返回结果数，默认 10，范围 1 到 20。"},  # 新增代码+ToolSearch: max_results 控制结果数量；若省略: 工具结果可能过长或过短
                },  # 新增代码+ToolSearch: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["query"],  # 新增代码+ToolSearch: 搜索工具必须提供 query；若省略: 空搜索请求会进入工具层
                "additionalProperties": False,  # 新增代码+ToolSearch: 禁止模型传入无关参数；若省略: 参数污染会增加搜索歧义
            },  # 新增代码+ToolSearch: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+ToolSearch: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+ToolSearch: tool_search 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+MCPResource: 第十二个工具定义开始，暴露 MCP resources 列表能力；若省略: 模型无法发现 MCP server 提供的文档、schema 或上下文资源
        "type": "function",  # 新增代码+MCPResource: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+MCPResource: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "list_mcp_resources",  # 新增代码+MCPResource: 工具名用于列出已启动 MCP server 暴露的资源；若省略: 模型无法请求 resources/list
            "description": "列出已启动 MCP server 暴露的 resources，返回 server、uri、名称、mimeType 和说明；适合读取 MCP 文档、schema、上下文前先发现资源。",  # 新增代码+MCPResource: 告诉模型何时列 MCP resources；若省略: 模型可能不知道 resources 不等同于 tools
            "parameters": {  # 新增代码+MCPResource: JSON Schema 描述资源列表参数；若省略: 模型不知道可传 server/max_results
                "type": "object",  # 新增代码+MCPResource: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+MCPResource: 声明允许的参数字段；若省略: server/max_results 无法进入输出 schema
                    "server": {"type": "string", "description": "可选 MCP server 名；省略时列出所有已启动 server 的 resources。"},  # 新增代码+MCPResource: server 用于筛选资源来源；若省略: 多 server 场景无法只看目标资源
                    "max_results": {"type": "integer", "description": "可选最大返回资源数，默认 10，范围 1 到 20。"},  # 新增代码+MCPResource: max_results 控制列表长度；若省略: 资源很多时可能撑爆上下文
                },  # 新增代码+MCPResource: properties 定义结束；若省略: 参数 schema 不完整
                "required": [],  # 新增代码+MCPResource: 列资源允许不传参数；若省略: 模型可能必须填无意义字段
                "additionalProperties": False,  # 新增代码+MCPResource: 禁止模型传入无关参数；若省略: 参数污染会增加资源发现歧义
            },  # 新增代码+MCPResource: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+MCPResource: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+MCPResource: list_mcp_resources 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+MCPResource: 第十三个工具定义开始，暴露 MCP resource 读取能力；若省略: 模型即使发现资源也无法读取内容
        "type": "function",  # 新增代码+MCPResource: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+MCPResource: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "read_mcp_resource",  # 新增代码+MCPResource: 工具名用于读取指定 MCP resource；若省略: 模型无法请求 resources/read
            "description": "读取指定 MCP server 的 resource 内容；必须使用 list_mcp_resources 返回的 server 和 uri，适合读取外部文档、schema、上下文资源。",  # 新增代码+MCPResource: 告诉模型读取资源前需要 server+uri；若省略: 模型可能只传 uri 导致多 server 歧义
            "parameters": {  # 新增代码+MCPResource: JSON Schema 描述资源读取参数；若省略: 模型不知道要传 server/uri/max_chars
                "type": "object",  # 新增代码+MCPResource: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+MCPResource: 声明允许的参数字段；若省略: server/uri/max_chars 无法进入输出 schema
                    "server": {"type": "string", "description": "MCP server 名，通常来自 list_mcp_resources 结果。"},  # 新增代码+MCPResource: server 指定资源来源；若省略: registry 无法确定该向哪个 server 读取
                    "uri": {"type": "string", "description": "要读取的 MCP resource URI，通常来自 list_mcp_resources 结果。"},  # 新增代码+MCPResource: uri 指定目标资源；若省略: 工具不知道读取哪个资源
                    "max_chars": {"type": "integer", "description": "可选最大返回字符数，默认 4000，范围 200 到 20000。"},  # 新增代码+MCPResource: max_chars 控制资源正文长度；若省略: 大资源可能撑爆上下文
                },  # 新增代码+MCPResource: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["server", "uri"],  # 新增代码+MCPResource: 读取资源必须同时指定 server 和 uri；若省略: 多 server 或空 uri 会进入工具层
                "additionalProperties": False,  # 新增代码+MCPResource: 禁止模型传入无关参数；若省略: 参数污染会增加读取歧义
            },  # 新增代码+MCPResource: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+MCPResource: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+MCPResource: read_mcp_resource 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+MCPPrompt: 第十四个工具定义开始，暴露 MCP prompts 列表能力；若省略: 模型无法发现 MCP server 提供的提示词或技能说明
        "type": "function",  # 新增代码+MCPPrompt: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+MCPPrompt: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "list_mcp_prompts",  # 新增代码+MCPPrompt: 工具名用于列出已启动 MCP server 暴露的 prompts；若省略: 模型无法请求 prompts/list
            "description": "列出已启动 MCP server 暴露的 prompts，返回 server、name、说明和参数；适合读取 MCP 提示词、远程操作规程或轻量 skill 前先发现可用项。",  # 新增代码+MCPPrompt: 告诉模型何时列 MCP prompts；若省略: 模型可能不知道 prompts 不等同于 tools/resources
            "parameters": {  # 新增代码+MCPPrompt: JSON Schema 描述 prompt 列表参数；若省略: 模型不知道可传 server/max_results
                "type": "object",  # 新增代码+MCPPrompt: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+MCPPrompt: 声明允许的参数字段；若省略: server/max_results 无法进入输出 schema
                    "server": {"type": "string", "description": "可选 MCP server 名；省略时列出所有已启动 server 的 prompts。"},  # 新增代码+MCPPrompt: server 用于筛选 prompt 来源；若省略: 多 server 场景无法只看目标 prompts
                    "max_results": {"type": "integer", "description": "可选最大返回 prompt 数，默认 10，范围 1 到 20。"},  # 新增代码+MCPPrompt: max_results 控制列表长度；若省略: prompts 很多时可能撑爆上下文
                },  # 新增代码+MCPPrompt: properties 定义结束；若省略: 参数 schema 不完整
                "required": [],  # 新增代码+MCPPrompt: 列 prompts 允许不传参数；若省略: 模型可能必须填无意义字段
                "additionalProperties": False,  # 新增代码+MCPPrompt: 禁止模型传入无关参数；若省略: 参数污染会增加 prompt 发现歧义
            },  # 新增代码+MCPPrompt: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+MCPPrompt: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+MCPPrompt: list_mcp_prompts 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+MCPPrompt: 第十五个工具定义开始，暴露 MCP prompt 读取能力；若省略: 模型即使发现 prompt 也无法读取内容
        "type": "function",  # 新增代码+MCPPrompt: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+MCPPrompt: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "read_mcp_prompt",  # 新增代码+MCPPrompt: 工具名用于读取指定 MCP prompt；若省略: 模型无法请求 prompts/get
            "description": "读取指定 MCP server 的 prompt 内容；必须使用 list_mcp_prompts 返回的 server 和 name，可选传 prompt_arguments 填充 prompt 参数。",  # 新增代码+MCPPrompt: 告诉模型读取 prompt 前需要 server+name；若省略: 模型可能只传名称导致多 server 歧义
            "parameters": {  # 新增代码+MCPPrompt: JSON Schema 描述 prompt 读取参数；若省略: 模型不知道要传 server/name/prompt_arguments/max_chars
                "type": "object",  # 新增代码+MCPPrompt: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+MCPPrompt: 声明允许的参数字段；若省略: server/name/prompt_arguments/max_chars 无法进入输出 schema
                    "server": {"type": "string", "description": "MCP server 名，通常来自 list_mcp_prompts 结果。"},  # 新增代码+MCPPrompt: server 指定 prompt 来源；若省略: registry 无法确定该向哪个 server 读取
                    "name": {"type": "string", "description": "要读取的 MCP prompt 名称，通常来自 list_mcp_prompts 结果。"},  # 新增代码+MCPPrompt: name 指定目标 prompt；若省略: 工具不知道读取哪个 prompt
                    "prompt_arguments": {"type": "object", "description": "可选 prompt 参数对象；键名应来自 list_mcp_prompts 返回的 arguments。", "additionalProperties": True},  # 新增代码+MCPPrompt: prompt_arguments 传给 prompts/get；若省略: 带参数 prompt 无法填充模板
                    "max_chars": {"type": "integer", "description": "可选最大返回字符数，默认 4000，范围 200 到 20000。"},  # 新增代码+MCPPrompt: max_chars 控制 prompt 正文长度；若省略: 大 prompt 可能撑爆上下文
                },  # 新增代码+MCPPrompt: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["server", "name"],  # 新增代码+MCPPrompt: 读取 prompt 必须同时指定 server 和 name；若省略: 多 server 或空名称会进入工具层
                "additionalProperties": False,  # 新增代码+MCPPrompt: 禁止模型传入无关参数；若省略: 参数污染会增加读取歧义
            },  # 新增代码+MCPPrompt: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+MCPPrompt: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+MCPPrompt: read_mcp_prompt 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+MCPStream: 第十四个工具定义开始，暴露监听 MCP stream 能力；若省略: 模型无法主动读取远程 MCP server 的流式通知
        "type": "function",  # 新增代码+MCPStream: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+MCPStream: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "listen_mcp_stream",  # 新增代码+MCPStream: 工具名用于监听指定 MCP server 的 stream；若省略: 模型无法请求该能力
            "description": "对指定 MCP server 执行有界 GET SSE 监听；执行前会请求用户确认，并限制事件数和等待时间；这不是后台常驻监听。",  # 修改代码+MCPStream: 明确这是有界 GET SSE 监听且不是后台常驻监听；若省略: 模型可能误以为工具会长期驻留后台或无限监听
            "parameters": {  # 新增代码+MCPStream: JSON Schema 描述监听参数；若省略: 模型不知道要传 server/max_events/timeout_seconds/resume
                "type": "object",  # 新增代码+MCPStream: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+MCPStream: 声明允许的参数字段；若省略: 监听参数无法进入输出 schema
                    "server": {"type": "string", "description": "要监听的 MCP server 名。"},  # 新增代码+MCPStream: server 指定目标 MCP server；若省略: 工具不知道监听哪个外部服务
                    "max_events": {"type": "integer", "description": "可选最大读取事件数，默认 5，范围 1 到 20；非法值会回退默认值。"},  # 新增代码+MCPStream: max_events 控制最多读取几条事件；若省略: stream 可能返回过多内容
                    "timeout_seconds": {"type": "number", "description": "可选等待秒数，默认 2.0，范围 0.1 到 10.0；非法值会回退默认值。"},  # 新增代码+MCPStream: timeout_seconds 控制监听等待时间；若省略: stream 可能等待过久
                    "resume": {"type": "boolean", "description": "可选是否携带 session 续传信息，默认 true；字符串 false/0/no/off 会按 false 处理。"},  # 新增代码+MCPStream: resume 控制是否尝试续传；若省略: 模型无法关闭续传行为
                },  # 新增代码+MCPStream: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["server"],  # 新增代码+MCPStream: 监听 stream 必须提供 server；若省略: 空 server 调用会进入工具层
                "additionalProperties": False,  # 新增代码+MCPStream: 禁止模型传入无关参数；若省略: 参数污染会增加监听歧义
            },  # 新增代码+MCPStream: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+MCPStream: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+MCPStream: listen_mcp_stream 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+SkillLoad: 第十四个工具定义开始，暴露本地 skills 列表能力；若省略: 模型无法发现 workspace/skills 下有哪些可复用说明书
        "type": "function",  # 新增代码+SkillLoad: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+SkillLoad: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "skill_list",  # 新增代码+SkillLoad: 工具名用于列出本地 skills；若省略: 模型无法请求本地 skill 目录清单
            "description": "列出工作区 skills/*/SKILL.md 中定义的本地 skills，返回名称、说明和相对路径；适合需要领域规程或操作说明时先发现可用 skill。",  # 新增代码+SkillLoad: 告诉模型何时使用 skill_list；若省略: 模型可能不知道 skills 是说明书层而不是执行工具
            "parameters": {  # 新增代码+SkillLoad: JSON Schema 描述 skill 列表参数；若省略: 模型不知道可传 query/max_results
                "type": "object",  # 新增代码+SkillLoad: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+SkillLoad: 声明允许的参数字段；若省略: query/max_results 无法进入输出 schema
                    "query": {"type": "string", "description": "可选搜索关键词，可匹配 skill 名称、说明或路径；省略时列出全部本地 skills。"},  # 新增代码+SkillLoad: query 用于筛选本地 skill；若省略: skill 很多时模型难以缩小范围
                    "max_results": {"type": "integer", "description": "可选最大返回结果数，默认 10，范围 1 到 20。"},  # 新增代码+SkillLoad: max_results 控制列表长度；若省略: skill 很多时可能撑爆上下文
                },  # 新增代码+SkillLoad: properties 定义结束；若省略: 参数 schema 不完整
                "required": [],  # 新增代码+SkillLoad: 列 skills 允许不传参数；若省略: 模型可能必须填无意义字段
                "additionalProperties": False,  # 新增代码+SkillLoad: 禁止模型传入无关参数；若省略: 参数污染会增加 skill 发现歧义
            },  # 新增代码+SkillLoad: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+SkillLoad: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+SkillLoad: skill_list 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+SkillLoad: 第十五个工具定义开始，暴露本地 skill 加载能力；若省略: 模型即使发现 skill 也无法读取说明书内容
        "type": "function",  # 新增代码+SkillLoad: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+SkillLoad: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "skill_load",  # 新增代码+SkillLoad: 工具名用于加载指定本地 skill；若省略: 模型无法请求读取 SKILL.md
            "description": "按名称加载工作区本地 skill 的 SKILL.md 内容；应优先使用 skill_list 返回的 name，加载后按说明执行后续任务。",  # 新增代码+SkillLoad: 告诉模型加载 skill 后应遵循说明；若省略: 模型可能把 skill 当普通文本而不改变行为
            "parameters": {  # 新增代码+SkillLoad: JSON Schema 描述 skill 加载参数；若省略: 模型不知道要传 name/max_chars
                "type": "object",  # 新增代码+SkillLoad: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+SkillLoad: 声明允许的参数字段；若省略: name/max_chars 无法进入输出 schema
                    "name": {"type": "string", "description": "要加载的本地 skill 名称，通常来自 skill_list 结果。"},  # 新增代码+SkillLoad: name 指定目标 skill；若省略: 工具不知道加载哪个说明书
                    "max_chars": {"type": "integer", "description": "可选最大返回字符数，默认 4000，范围 200 到 20000。"},  # 新增代码+SkillLoad: max_chars 控制返回长度；若省略: 大 skill 可能撑爆上下文
                },  # 新增代码+SkillLoad: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["name"],  # 新增代码+SkillLoad: 加载 skill 必须提供名称；若省略: 空加载请求会进入工具层
                "additionalProperties": False,  # 新增代码+SkillLoad: 禁止模型传入无关参数；若省略: 参数污染会增加加载歧义
            },  # 新增代码+SkillLoad: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+SkillLoad: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+SkillLoad: skill_load 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+AskUserQuestion: 第十六个工具定义开始，暴露结构化澄清提问能力；若省略: 模型只能靠普通文本随口追问或直接猜
        "type": "function",  # 新增代码+AskUserQuestion: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+AskUserQuestion: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "ask_user_question",  # 新增代码+AskUserQuestion: 工具名用于让模型请求向用户结构化提问；若省略: 模型无法发起标准澄清动作
            "description": "当需求不清楚、存在互斥方案、缺少关键偏好或需要用户先确认范围时，输出 1 到 3 个结构化问题和选项，等待用户下一轮回答。",  # 新增代码+AskUserQuestion: 告诉模型何时使用结构化提问；若省略: 模型可能继续乱猜或问得没有格式
            "parameters": {  # 新增代码+AskUserQuestion: JSON Schema 描述结构化提问参数；若省略: 模型不知道 questions 应该长什么样
                "type": "object",  # 新增代码+AskUserQuestion: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+AskUserQuestion: 声明允许的参数字段；若省略: questions 无法进入输出 schema
                    "questions": {  # 新增代码+AskUserQuestion: questions 保存 1 到 3 个问题；若省略: 工具无法携带澄清内容
                        "type": "array",  # 新增代码+AskUserQuestion: questions 必须是数组；若省略: 多问题结构无法表达
                        "description": "要展示给用户的结构化问题数组，数量必须是 1 到 3。",  # 新增代码+AskUserQuestion: 说明问题数量限制；若省略: 模型可能一次塞入过多问题
                        "minItems": 1,  # 新增代码+AskUserQuestion: 至少需要一个问题；若省略: 空提问会进入工具层
                        "maxItems": 3,  # 新增代码+AskUserQuestion: 最多允许三个问题；若省略: 模型可能让用户一次回答太多内容
                        "items": {  # 新增代码+AskUserQuestion: 定义单个问题对象结构；若省略: 问题字段没有约束
                            "type": "object",  # 新增代码+AskUserQuestion: 每个问题必须是对象；若省略: 字符串问题无法携带 id 和选项
                            "properties": {  # 新增代码+AskUserQuestion: 声明单个问题允许的字段；若省略: id/header/question/options 无法被规范输出
                                "id": {"type": "string", "description": "问题的稳定 id，方便用户回答后模型对应到问题。"},  # 新增代码+AskUserQuestion: id 用于后续答案对齐；若省略: 多问题场景难以对应用户回复
                                "header": {"type": "string", "description": "短标题，例如 范围、风格、优先级。"},  # 新增代码+AskUserQuestion: header 用于让用户快速理解问题类别；若省略: 输出可读性下降
                                "question": {"type": "string", "description": "要问用户的一句话问题。"},  # 新增代码+AskUserQuestion: question 保存正式提问文本；若省略: 用户不知道要回答什么
                                "options": {  # 新增代码+AskUserQuestion: options 保存可选答案；若省略: 用户无法快速选择
                                    "type": "array",  # 新增代码+AskUserQuestion: options 必须是数组；若省略: 多个选项无法标准表达
                                    "description": "给用户的 2 到 4 个预设选项。",  # 新增代码+AskUserQuestion: 说明选项数量限制；若省略: 模型可能生成过多或过少选项
                                    "minItems": 2,  # 新增代码+AskUserQuestion: 至少两个选项；若省略: 单选项没有澄清意义
                                    "maxItems": 4,  # 新增代码+AskUserQuestion: 最多四个选项；若省略: 选项过多会增加用户负担
                                    "items": {  # 新增代码+AskUserQuestion: 定义单个选项对象结构；若省略: 选项字段没有约束
                                        "type": "object",  # 新增代码+AskUserQuestion: 每个选项必须是对象；若省略: 无法同时携带 label 和说明
                                        "properties": {  # 新增代码+AskUserQuestion: 声明选项允许字段；若省略: label/description 无法被规范输出
                                            "label": {"type": "string", "description": "选项短名称。"},  # 新增代码+AskUserQuestion: label 用于用户快速选择；若省略: 选项没有可见名称
                                            "description": {"type": "string", "description": "一句话说明该选项的影响或取舍。"},  # 新增代码+AskUserQuestion: description 解释选项差异；若省略: 用户难以判断该选哪个
                                        },  # 新增代码+AskUserQuestion: 选项 properties 定义结束；若省略: 参数 schema 不完整
                                        "required": ["label", "description"],  # 新增代码+AskUserQuestion: 选项必须有名称和说明；若省略: 模型可能输出空泛选项
                                        "additionalProperties": False,  # 新增代码+AskUserQuestion: 禁止选项额外字段；若省略: 参数污染会增加解析复杂度
                                    },  # 新增代码+AskUserQuestion: 单个选项 items 定义结束；若省略: options schema 不完整
                                },  # 新增代码+AskUserQuestion: options 字段定义结束；若省略: 问题 schema 不完整
                            },  # 新增代码+AskUserQuestion: 问题 properties 定义结束；若省略: 参数 schema 不完整
                            "required": ["id", "header", "question", "options"],  # 新增代码+AskUserQuestion: 每个问题必须有 id、标题、问题和选项；若省略: 工具层会收到缺字段问题
                            "additionalProperties": False,  # 新增代码+AskUserQuestion: 禁止问题对象额外字段；若省略: 参数污染会增加解析复杂度
                        },  # 新增代码+AskUserQuestion: 单个问题 items 定义结束；若省略: questions schema 不完整
                    },  # 新增代码+AskUserQuestion: questions 字段定义结束；若省略: 参数 schema 不完整
                },  # 新增代码+AskUserQuestion: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["questions"],  # 新增代码+AskUserQuestion: 调用结构化提问必须提供 questions；若省略: 空调用会进入工具层
                "additionalProperties": False,  # 新增代码+AskUserQuestion: 禁止模型传入无关参数；若省略: 参数污染会增加澄清歧义
            },  # 新增代码+AskUserQuestion: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+AskUserQuestion: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+AskUserQuestion: ask_user_question 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TaskAgent: 第十七个工具定义开始，暴露单进程子 agent 委派能力；若省略: 主 agent 无法把复杂任务拆给子任务执行
        "type": "function",  # 新增代码+TaskAgent: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TaskAgent: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "task",  # 新增代码+TaskAgent: 工具名用于启动一个子 agent 执行子任务；若省略: 模型无法请求任务委派
            "description": "把一个边界清楚的子任务交给同进程子 agent 执行；适合复杂任务拆分、只读分析、局部检查或使用 allowed_tools 限制子 agent 工具范围。",  # 新增代码+TaskAgent: 告诉模型何时使用 task；若省略: 模型可能不知道复杂任务可以委派给子 agent
            "parameters": {  # 新增代码+TaskAgent: JSON Schema 描述子 agent 参数；若省略: 模型不知道如何传 prompt/allowed_tools/max_turns
                "type": "object",  # 新增代码+TaskAgent: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 修改代码+AsyncTask: 声明允许的参数字段并加入后台执行开关；若省略: prompt/allowed_tools/max_turns/background 无法进入输出 schema
                    "prompt": {"type": "string", "description": "交给子 agent 执行的清晰子任务说明，必须包含目标和期望输出。"},  # 新增代码+TaskAgent: prompt 指定子任务内容；若省略: 子 agent 不知道要做什么
                    "allowed_tools": {  # 新增代码+TaskAgent: allowed_tools 限制子 agent 可见工具；若省略: 子 agent 可能获得不必要的工具范围
                        "type": "array",  # 新增代码+TaskAgent: allowed_tools 必须是数组；若省略: 多个工具名无法标准表达
                        "description": "可选工具白名单；省略时子 agent 默认可见除 task/task_output/task_stop/task_list/task_get/task_update 外的所有当前工具。",  # 修改代码+TaskManagement: 说明生命周期和管理工具默认不下放给子 agent；若省略: 模型不清楚子 agent 默认工具边界
                        "items": {"type": "string"},  # 新增代码+TaskAgent: 每个白名单项是工具名字符串；若省略: 工具名类型没有约束
                    },  # 新增代码+TaskAgent: allowed_tools 字段定义结束；若省略: 参数 schema 不完整
                    "max_turns": {"type": "integer", "description": "可选子 agent 最大模型-工具循环轮次，默认 3，必须大于等于 1。"},  # 新增代码+TaskAgent: max_turns 限制子 agent 执行时长；若省略: 子任务可能运行过久
                    "background": {"type": "boolean", "description": "可选；true 表示后台启动子 agent 并立即返回 task_id，省略或 false 表示保持同步执行。"},  # 新增代码+AsyncTask: 暴露后台执行开关给模型；若省略: 模型无法请求非阻塞子 agent
                },  # 新增代码+TaskAgent: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["prompt"],  # 新增代码+TaskAgent: task 必须提供 prompt；若省略: 空子任务会进入工具层
                "additionalProperties": False,  # 新增代码+TaskAgent: 禁止模型传入无关参数；若省略: 参数污染会增加子 agent 执行歧义
            },  # 新增代码+TaskAgent: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TaskAgent: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TaskAgent: task 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TaskLifecycle: 第十八个工具定义开始，暴露读取子任务输出能力；若省略: 模型无法像 Claude Code 一样二次查看子 agent 结果
        "type": "function",  # 新增代码+TaskLifecycle: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TaskLifecycle: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "task_output",  # 新增代码+TaskLifecycle: 工具名用于读取 task 子任务输出；若省略: 模型无法请求查询子任务结果
            "description": "读取已创建 task 子任务的状态、元信息和输出；适合主 agent 需要再次查看子 agent 结果时使用。",  # 新增代码+TaskLifecycle: 告诉模型何时读取子任务输出；若省略: 模型可能只依赖最初 task 返回文本
            "parameters": {  # 新增代码+TaskLifecycle: JSON Schema 描述读取子任务输出参数；若省略: 模型不知道如何传 task_id/max_chars
                "type": "object",  # 新增代码+TaskLifecycle: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+TaskLifecycle: 声明允许的参数字段；若省略: task_id/max_chars 无法进入输出 schema
                    "task_id": {"type": "string", "description": "task 工具返回的子任务 id。"},  # 新增代码+TaskLifecycle: task_id 指定要读取哪个子任务；若省略: 工具无法定位任务记录
                    "max_chars": {"type": "integer", "description": "可选最大返回字符数，省略时默认 4000。"},  # 新增代码+TaskLifecycle: max_chars 控制输出长度；若省略: 长任务输出可能撑爆上下文
                },  # 新增代码+TaskLifecycle: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["task_id"],  # 新增代码+TaskLifecycle: 读取子任务输出必须提供 task_id；若省略: 空查询会进入工具层
                "additionalProperties": False,  # 新增代码+TaskLifecycle: 禁止模型传入无关参数；若省略: 参数污染会增加查询歧义
            },  # 新增代码+TaskLifecycle: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TaskLifecycle: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TaskLifecycle: task_output 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TaskLifecycle: 第十九个工具定义开始，暴露停止子任务能力；若省略: 模型无法表达取消子 agent 任务的意图
        "type": "function",  # 新增代码+TaskLifecycle: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TaskLifecycle: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "task_stop",  # 新增代码+TaskLifecycle: 工具名用于停止或标记停止子任务；若省略: 模型无法请求停止子任务
            "description": "停止一个尚未完成的 task 子任务，或对已完成任务返回无需停止的状态说明。",  # 新增代码+TaskLifecycle: 告诉模型何时停止子任务；若省略: 模型不知道任务生命周期可以收束
            "parameters": {  # 新增代码+TaskLifecycle: JSON Schema 描述停止子任务参数；若省略: 模型不知道如何传 task_id/reason
                "type": "object",  # 新增代码+TaskLifecycle: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+TaskLifecycle: 声明允许的参数字段；若省略: task_id/reason 无法进入输出 schema
                    "task_id": {"type": "string", "description": "task 工具返回的子任务 id。"},  # 新增代码+TaskLifecycle: task_id 指定要停止哪个子任务；若省略: 工具无法定位任务记录
                    "reason": {"type": "string", "description": "可选停止原因，方便调试和用户理解。"},  # 新增代码+TaskLifecycle: reason 保存停止原因；若省略: 停止记录缺少上下文
                },  # 新增代码+TaskLifecycle: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["task_id"],  # 新增代码+TaskLifecycle: 停止子任务必须提供 task_id；若省略: 空停止请求会进入工具层
                "additionalProperties": False,  # 新增代码+TaskLifecycle: 禁止模型传入无关参数；若省略: 参数污染会增加停止歧义
            },  # 新增代码+TaskLifecycle: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TaskLifecycle: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TaskLifecycle: task_stop 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TaskManagement: 第二十个工具定义开始，暴露子任务列表能力；若省略: 主 agent 无法管理多个同步或后台子任务
        "type": "function",  # 新增代码+TaskManagement: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TaskManagement: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "task_list",  # 新增代码+TaskManagement: 工具名用于列出当前 agent 内存中的子任务；若省略: 模型无法请求任务总览
            "description": "列出当前 agent 进程内已创建的 task 子任务，可按状态筛选；适合同时存在多个同步或后台子任务时查看总览。",  # 新增代码+TaskManagement: 告诉模型何时查看任务列表；若省略: 模型可能只记得单个 task_id 而丢失多任务视图
            "parameters": {  # 新增代码+TaskManagement: JSON Schema 描述任务列表参数；若省略: 模型不知道如何传 status/max_results
                "type": "object",  # 新增代码+TaskManagement: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+TaskManagement: 声明允许的参数字段；若省略: status/max_results 无法进入输出 schema
                    "status": {"type": "string", "enum": ["all", "pending", "running", "completed", "failed", "stopped"], "description": "可选状态筛选，省略或 all 表示列出全部任务。"},  # 新增代码+TaskManagement: status 用于筛选任务进度；若省略: 多任务场景无法只看 running 或 completed
                    "max_results": {"type": "integer", "description": "可选最大返回任务数，默认 10，范围 1 到 20。"},  # 新增代码+TaskManagement: max_results 控制列表长度；若省略: 任务太多时可能撑爆上下文
                },  # 新增代码+TaskManagement: properties 定义结束；若省略: 参数 schema 不完整
                "required": [],  # 新增代码+TaskManagement: task_list 可以无参数调用；若省略: 严格 schema 可能误以为缺少必填字段
                "additionalProperties": False,  # 新增代码+TaskManagement: 禁止模型传入无关参数；若省略: 参数污染会增加筛选歧义
            },  # 新增代码+TaskManagement: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TaskManagement: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TaskManagement: task_list 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TaskManagement: 第二十一个工具定义开始，暴露单任务详情读取能力；若省略: 主 agent 只能看输出而看不到 prompt、备注和管理元信息
        "type": "function",  # 新增代码+TaskManagement: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TaskManagement: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "task_get",  # 新增代码+TaskManagement: 工具名用于读取单个子任务详情；若省略: 模型无法请求完整任务详情
            "description": "读取一个 task 子任务的完整详情，包括 prompt、状态、标签、备注、工具边界和输出摘要。",  # 新增代码+TaskManagement: 告诉模型何时读取任务详情；若省略: 模型可能误用 task_output 查管理信息
            "parameters": {  # 新增代码+TaskManagement: JSON Schema 描述任务详情参数；若省略: 模型不知道如何传 task_id/max_chars
                "type": "object",  # 新增代码+TaskManagement: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+TaskManagement: 声明允许的参数字段；若省略: task_id/max_chars 无法进入输出 schema
                    "task_id": {"type": "string", "description": "task 工具返回的子任务 id。"},  # 新增代码+TaskManagement: task_id 指定读取哪个任务；若省略: 工具无法定位任务记录
                    "max_chars": {"type": "integer", "description": "可选最大返回输出字符数，省略时默认 4000。"},  # 新增代码+TaskManagement: max_chars 控制输出摘要长度；若省略: 长输出可能撑爆上下文
                },  # 新增代码+TaskManagement: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["task_id"],  # 新增代码+TaskManagement: 读取单任务详情必须提供 task_id；若省略: 空查询会进入工具层
                "additionalProperties": False,  # 新增代码+TaskManagement: 禁止模型传入无关参数；若省略: 参数污染会增加查询歧义
            },  # 新增代码+TaskManagement: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TaskManagement: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TaskManagement: task_get 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TaskManagement: 第二十二个工具定义开始，暴露任务元信息更新能力；若省略: 主 agent 无法给任务补标签或备注
        "type": "function",  # 新增代码+TaskManagement: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TaskManagement: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "task_update",  # 新增代码+TaskManagement: 工具名用于更新任务管理元信息；若省略: 模型无法请求修改标签或备注
            "description": "更新 task 子任务的管理元信息，只允许修改 label 和 notes，不允许修改运行状态或输出。",  # 新增代码+TaskManagement: 告诉模型更新边界；若省略: 模型可能误以为可以篡改任务状态
            "parameters": {  # 新增代码+TaskManagement: JSON Schema 描述任务更新参数；若省略: 模型不知道如何传 task_id/label/notes
                "type": "object",  # 新增代码+TaskManagement: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+TaskManagement: 声明允许的参数字段；若省略: task_id/label/notes 无法进入输出 schema
                    "task_id": {"type": "string", "description": "task 工具返回的子任务 id。"},  # 新增代码+TaskManagement: task_id 指定更新哪个任务；若省略: 工具无法定位任务记录
                    "label": {"type": "string", "description": "可选短标签；传空字符串表示清空标签。"},  # 新增代码+TaskManagement: label 用于给任务起短名；若省略: 多任务列表不易扫描
                    "notes": {"type": "string", "description": "可选备注或交接说明；传空字符串表示清空备注。"},  # 新增代码+TaskManagement: notes 用于保存管理备注；若省略: 任务无法留下后续处理线索
                },  # 新增代码+TaskManagement: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["task_id"],  # 新增代码+TaskManagement: 更新任务元信息必须提供 task_id；若省略: 空更新会进入工具层
                "additionalProperties": False,  # 新增代码+TaskManagement: 禁止模型传入 status/output 等额外字段；若省略: 参数污染会让模型误以为能改生命周期
            },  # 新增代码+TaskManagement: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TaskManagement: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TaskManagement: task_update 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TeamCommunication: 第二十三个工具定义开始，暴露创建教学版 peer 能力；若省略: agent 无法登记多 agent 成员
        "type": "function",  # 新增代码+TeamCommunication: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TeamCommunication: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "team_create",  # 新增代码+TeamCommunication: 工具名用于创建教学版 peer 记录；若省略: 模型无法请求登记新 peer
            "description": "创建一个教学版 peer/agent 登记记录，不启动真实线程；适合先搭建多 agent 团队成员和职责边界。",  # 新增代码+TeamCommunication: 告诉模型该工具只登记成员不真正运行 agent；若省略: 模型可能误以为已经启动真实并行 agent
            "parameters": {  # 新增代码+TeamCommunication: JSON Schema 描述创建 peer 参数；若省略: 模型不知道如何传 name/role/notes
                "type": "object",  # 新增代码+TeamCommunication: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+TeamCommunication: 声明允许的参数字段；若省略: name/role/notes 无法进入输出 schema
                    "name": {"type": "string", "description": "peer 的可读名称，例如 资料探索员、实现工人、验证员。"},  # 新增代码+TeamCommunication: name 用于区分团队成员；若省略: list_peers 只能显示 id
                    "role": {"type": "string", "description": "peer 的角色，例如 explorer、worker、reviewer、verifier、writer。"},  # 新增代码+TeamCommunication: role 用于表达职责；若省略: 主 agent 难以按角色发送消息
                    "notes": {"type": "string", "description": "可选职责说明、边界或备注。"},  # 新增代码+TeamCommunication: notes 保存职责边界；若省略: peer 记录缺少交接说明
                },  # 新增代码+TeamCommunication: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["name"],  # 新增代码+TeamCommunication: 创建 peer 必须提供名称；若省略: 空成员会进入工具层
                "additionalProperties": False,  # 新增代码+TeamCommunication: 禁止模型传入无关参数；若省略: 参数污染会增加登记歧义
            },  # 新增代码+TeamCommunication: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TeamCommunication: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TeamCommunication: team_create 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TeamCommunication: 第二十四个工具定义开始，暴露向 peer 发送消息能力；若省略: 多 agent 成员之间无法形成消息队列
        "type": "function",  # 新增代码+TeamCommunication: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TeamCommunication: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "send_message",  # 新增代码+TeamCommunication: 工具名用于把消息放入 peer inbox；若省略: 模型无法请求发送协作消息
            "description": "向一个已登记 peer 发送教学版消息，消息会进入该 peer 的进程内 inbox；当前不会自动唤醒真实 agent。",  # 新增代码+TeamCommunication: 告诉模型这是消息队列而非真实网络发送；若省略: 模型可能误报对方已经处理消息
            "parameters": {  # 新增代码+TeamCommunication: JSON Schema 描述发送消息参数；若省略: 模型不知道如何传 peer_id/message/sender
                "type": "object",  # 新增代码+TeamCommunication: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+TeamCommunication: 声明允许的参数字段；若省略: peer_id/message/sender 无法进入输出 schema
                    "peer_id": {"type": "string", "description": "team_create 返回的目标 peer id。"},  # 新增代码+TeamCommunication: peer_id 指定收件对象；若省略: 工具无法定位目标 peer
                    "message": {"type": "string", "description": "要放入目标 peer inbox 的消息正文。"},  # 新增代码+TeamCommunication: message 保存协作内容；若省略: inbox 只有空记录没有任务信息
                    "sender": {"type": "string", "description": "可选发送者名称，省略时默认为 main。"},  # 新增代码+TeamCommunication: sender 标记消息来源；若省略: peer 不知道消息来自哪个 agent
                },  # 新增代码+TeamCommunication: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["peer_id", "message"],  # 新增代码+TeamCommunication: 发送消息必须指定目标和正文；若省略: 空消息或无目标消息会进入工具层
                "additionalProperties": False,  # 新增代码+TeamCommunication: 禁止模型传入无关参数；若省略: 参数污染会增加消息语义歧义
            },  # 新增代码+TeamCommunication: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TeamCommunication: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TeamCommunication: send_message 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TeamCommunication: 第二十五个工具定义开始，暴露列出 peer 能力；若省略: 主 agent 无法查看当前团队成员和消息状态
        "type": "function",  # 新增代码+TeamCommunication: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TeamCommunication: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "list_peers",  # 新增代码+TeamCommunication: 工具名用于查看 peer 总览；若省略: 模型无法请求团队成员列表
            "description": "列出当前 agent 进程内登记的 peer/agent 成员，显示角色、状态、备注、inbox 数量和最新消息摘要。",  # 新增代码+TeamCommunication: 告诉模型该工具适合查看团队状态；若省略: 模型可能不知道如何确认消息是否进入 inbox
            "parameters": {  # 新增代码+TeamCommunication: JSON Schema 描述列 peer 参数；若省略: 模型不知道如何传 role/status/max_results
                "type": "object",  # 新增代码+TeamCommunication: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+TeamCommunication: 声明允许的参数字段；若省略: role/status/max_results 无法进入输出 schema
                    "role": {"type": "string", "description": "可选角色筛选，省略表示不过滤角色。"},  # 新增代码+TeamCommunication: role 用于只看某类 peer；若省略: 多角色团队无法快速筛选
                    "status": {"type": "string", "description": "可选状态筛选，例如 idle、active，省略表示不过滤状态。"},  # 新增代码+TeamCommunication: status 用于只看空闲或活跃 peer；若省略: 多成员状态难以筛选
                    "max_results": {"type": "integer", "description": "可选最大返回 peer 数，默认 10，范围 1 到 20。"},  # 新增代码+TeamCommunication: max_results 控制列表长度；若省略: peer 太多时可能撑爆上下文
                },  # 新增代码+TeamCommunication: properties 定义结束；若省略: 参数 schema 不完整
                "required": [],  # 新增代码+TeamCommunication: list_peers 可以无参数调用；若省略: 严格 schema 可能误以为缺少必填字段
                "additionalProperties": False,  # 新增代码+TeamCommunication: 禁止模型传入无关参数；若省略: 参数污染会增加列表歧义
            },  # 新增代码+TeamCommunication: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TeamCommunication: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TeamCommunication: list_peers 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TeamCommunicationLifecycle: 第二十六个工具定义开始，暴露读取 peer inbox 能力；若省略: 模型只能看到消息数量却无法读取消息详情
        "type": "function",  # 新增代码+TeamCommunicationLifecycle: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TeamCommunicationLifecycle: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "read_peer_messages",  # 新增代码+TeamCommunicationLifecycle: 工具名用于读取 peer inbox；若省略: 模型无法请求查看消息内容
            "description": "读取一个已登记 peer 的进程内 inbox，默认只返回尚未确认的消息；可选择包含已确认历史。",  # 新增代码+TeamCommunicationLifecycle: 告诉模型读取默认只看待处理消息；若省略: 模型可能误解读取范围
            "parameters": {  # 新增代码+TeamCommunicationLifecycle: JSON Schema 描述读取消息参数；若省略: 模型不知道如何传 peer_id/include_acknowledged/max_results
                "type": "object",  # 新增代码+TeamCommunicationLifecycle: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+TeamCommunicationLifecycle: 声明允许的参数字段；若省略: 读取消息参数无法进入输出 schema
                    "peer_id": {"type": "string", "description": "team_create 返回的目标 peer id。"},  # 新增代码+TeamCommunicationLifecycle: peer_id 指定要读取哪个 peer 的 inbox；若省略: 工具无法定位收件箱
                    "include_acknowledged": {"type": "boolean", "description": "可选；true 表示也返回已经确认过的历史消息，默认 false。"},  # 新增代码+TeamCommunicationLifecycle: include_acknowledged 控制是否包含历史；若省略: 模型无法做审计读取
                    "max_results": {"type": "integer", "description": "可选最大返回消息数，默认 10，范围 1 到 20。"},  # 新增代码+TeamCommunicationLifecycle: max_results 控制消息列表长度；若省略: inbox 太长可能撑爆上下文
                },  # 新增代码+TeamCommunicationLifecycle: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["peer_id"],  # 新增代码+TeamCommunicationLifecycle: 读取消息必须指定 peer_id；若省略: 工具层会收到空目标
                "additionalProperties": False,  # 新增代码+TeamCommunicationLifecycle: 禁止模型传入无关参数；若省略: 参数污染会增加读取歧义
            },  # 新增代码+TeamCommunicationLifecycle: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TeamCommunicationLifecycle: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TeamCommunicationLifecycle: read_peer_messages 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TeamCommunicationLifecycle: 第二十七个工具定义开始，暴露确认 peer 消息能力；若省略: 消息只能累积，无法标记已处理
        "type": "function",  # 新增代码+TeamCommunicationLifecycle: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TeamCommunicationLifecycle: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "ack_peer_message",  # 新增代码+TeamCommunicationLifecycle: 工具名用于确认某条 peer 消息；若省略: 模型无法请求标记消息已处理
            "description": "确认某个 peer inbox 中的一条消息已经被处理，并可留下处理备注；不会删除消息，便于审计。",  # 新增代码+TeamCommunicationLifecycle: 告诉模型确认不会删除历史；若省略: 模型可能误以为 ack 会清除消息
            "parameters": {  # 新增代码+TeamCommunicationLifecycle: JSON Schema 描述确认消息参数；若省略: 模型不知道如何传 peer_id/message_id/note
                "type": "object",  # 新增代码+TeamCommunicationLifecycle: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+TeamCommunicationLifecycle: 声明允许的参数字段；若省略: 确认消息参数无法进入输出 schema
                    "peer_id": {"type": "string", "description": "team_create 返回的目标 peer id。"},  # 新增代码+TeamCommunicationLifecycle: peer_id 指定消息所属 peer；若省略: 工具无法定位收件箱
                    "message_id": {"type": "string", "description": "send_message 返回或 read_peer_messages 展示的消息 id。"},  # 新增代码+TeamCommunicationLifecycle: message_id 指定要确认哪条消息；若省略: 工具无法精确标记消息
                    "note": {"type": "string", "description": "可选确认备注，例如 已完成验证、无需处理。"},  # 新增代码+TeamCommunicationLifecycle: note 保存处理说明；若省略: 用户无法留下确认理由
                },  # 新增代码+TeamCommunicationLifecycle: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["peer_id", "message_id"],  # 新增代码+TeamCommunicationLifecycle: 确认消息必须指定 peer 和消息；若省略: 工具层会收到模糊目标
                "additionalProperties": False,  # 新增代码+TeamCommunicationLifecycle: 禁止模型传入无关参数；若省略: 参数污染会增加确认歧义
            },  # 新增代码+TeamCommunicationLifecycle: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TeamCommunicationLifecycle: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TeamCommunicationLifecycle: ack_peer_message 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TeamCommunicationLifecycle: 第二十八个工具定义开始，暴露删除教学版 peer 能力；若省略: peer 只能创建无法回收
        "type": "function",  # 新增代码+TeamCommunicationLifecycle: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TeamCommunicationLifecycle: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "team_delete",  # 新增代码+TeamCommunicationLifecycle: 工具名用于删除教学版 peer；若省略: 模型无法请求回收团队成员记录
            "description": "删除一个教学版 peer 记录和它的进程内 inbox；需要 confirm_delete=true，删除后不能恢复。",  # 新增代码+TeamCommunicationLifecycle: 告诉模型删除会丢弃进程内消息且需确认；若省略: 模型可能误删 peer
            "parameters": {  # 新增代码+TeamCommunicationLifecycle: JSON Schema 描述删除 peer 参数；若省略: 模型不知道如何传 peer_id/confirm_delete
                "type": "object",  # 新增代码+TeamCommunicationLifecycle: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+TeamCommunicationLifecycle: 声明允许的参数字段；若省略: 删除参数无法进入输出 schema
                    "peer_id": {"type": "string", "description": "team_create 返回的目标 peer id。"},  # 新增代码+TeamCommunicationLifecycle: peer_id 指定要删除的 peer；若省略: 工具无法定位目标
                    "confirm_delete": {"type": "boolean", "description": "必须显式传 true 才会删除 peer。"},  # 新增代码+TeamCommunicationLifecycle: confirm_delete 防止模型无确认删除；若省略: 删除操作风险更高
                },  # 新增代码+TeamCommunicationLifecycle: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["peer_id", "confirm_delete"],  # 新增代码+TeamCommunicationLifecycle: 删除必须指定目标并显式确认；若省略: 工具层无法安全执行删除
                "additionalProperties": False,  # 新增代码+TeamCommunicationLifecycle: 禁止模型传入无关参数；若省略: 参数污染会增加删除歧义
            },  # 新增代码+TeamCommunicationLifecycle: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TeamCommunicationLifecycle: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TeamCommunicationLifecycle: team_delete 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+TeamTaskBinding: 第二十九个工具定义开始，暴露让 peer 启动并绑定后台 task 的能力；若省略: team 记录无法和真实子任务生命周期连接
        "type": "function",  # 新增代码+TeamTaskBinding: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+TeamTaskBinding: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "team_start_task",  # 新增代码+TeamTaskBinding: 工具名用于为指定 peer 启动后台 task；若省略: 模型无法请求 peer 承接真实子任务
            "description": "为一个已登记 peer 启动后台 task，并把返回的 task_id 绑定到 peer；任务仍通过 task_output/task_stop 管理。",  # 新增代码+TeamTaskBinding: 告诉模型该工具只负责绑定 team 与 task 生命周期；若省略: 模型可能误以为 peer 会自动独立处理消息
            "parameters": {  # 新增代码+TeamTaskBinding: JSON Schema 描述 peer 启动后台 task 参数；若省略: 模型不知道如何传 peer_id/prompt/allowed_tools/max_turns
                "type": "object",  # 新增代码+TeamTaskBinding: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+TeamTaskBinding: 声明允许的参数字段；若省略: 绑定 task 参数无法进入输出 schema
                    "peer_id": {"type": "string", "description": "team_create 返回的目标 peer id。"},  # 新增代码+TeamTaskBinding: peer_id 指定哪个 peer 承接后台 task；若省略: 工具无法定位要绑定的团队成员
                    "prompt": {"type": "string", "description": "交给该 peer 的子任务目标。"},  # 新增代码+TeamTaskBinding: prompt 保存子 agent 要执行的任务；若省略: 后台 task 没有明确目标
                    "allowed_tools": {"type": "array", "description": "可选工具白名单，传给底层 task.allowed_tools。", "items": {"type": "string"}},  # 新增代码+TeamTaskBinding: allowed_tools 限制子 agent 权限；若省略: 绑定任务无法按角色收窄工具范围
                    "max_turns": {"type": "integer", "description": "可选子 agent 最大轮次，传给底层 task.max_turns。"},  # 新增代码+TeamTaskBinding: max_turns 控制绑定任务执行长度；若省略: 子任务轮次约束无法从 team_start_task 传入
                },  # 新增代码+TeamTaskBinding: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["peer_id", "prompt"],  # 新增代码+TeamTaskBinding: 启动绑定任务必须指定 peer 和目标；若省略: 工具层会收到模糊任务
                "additionalProperties": False,  # 新增代码+TeamTaskBinding: 禁止模型传入无关参数；若省略: 参数污染会增加绑定歧义
            },  # 新增代码+TeamTaskBinding: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+TeamTaskBinding: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+TeamTaskBinding: team_start_task 工具定义结束；若省略: 工具列表语法不完整
    {  # 修改代码+TeamTaskBinding: 第三十个工具定义开始，暴露进入计划模式能力；若省略: 模型无法像 Claude Code 一样先计划再执行复杂改动
        "type": "function",  # 新增代码+PlanMode: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+PlanMode: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "enter_plan_mode",  # 新增代码+PlanMode: 工具名用于进入计划模式；若省略: 模型无法请求进入只计划不执行的状态
            "description": "进入计划模式，用于复杂改动前先分析、列计划，不直接执行写入、删除、命令或外部副作用操作。",  # 新增代码+PlanMode: 告诉模型何时使用计划模式；若省略: 模型可能继续直接动手修改
            "parameters": {  # 新增代码+PlanMode: JSON Schema 描述进入计划模式的参数；若省略: 模型不知道如何传 reason/goal/steps
                "type": "object",  # 新增代码+PlanMode: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+PlanMode: 声明允许的参数字段；若省略: reason/goal/steps 无法进入输出 schema
                    "reason": {"type": "string", "description": "为什么需要先进入计划模式，例如复杂代码改动、风险较高或方案不确定。"},  # 新增代码+PlanMode: reason 保存进入计划模式原因；若省略: 用户看不到模型为什么暂停执行
                    "goal": {"type": "string", "description": "本次计划要达成的目标。"},  # 新增代码+PlanMode: goal 保存计划目标；若省略: 后续计划缺少明确方向
                    "steps": {"type": "array", "description": "可选的初步步骤列表。", "items": {"type": "string"}},  # 新增代码+PlanMode: steps 保存初步步骤；若省略: 模型无法结构化表达计划草案
                },  # 新增代码+PlanMode: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["reason", "goal"],  # 新增代码+PlanMode: 进入计划模式必须提供原因和目标；若省略: 空泛计划会进入工具层
                "additionalProperties": False,  # 新增代码+PlanMode: 禁止模型传入无关参数；若省略: 参数污染会增加计划状态歧义
            },  # 新增代码+PlanMode: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+PlanMode: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+PlanMode: enter_plan_mode 工具定义结束；若省略: 工具列表语法不完整
    {  # 修改代码+TeamTaskBinding: 第三十一个工具定义开始，暴露退出计划模式并展示计划能力；若省略: 模型进入计划模式后无法输出待确认计划
        "type": "function",  # 新增代码+PlanMode: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+PlanMode: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "exit_plan_mode",  # 新增代码+PlanMode: 工具名用于输出最终计划并等待确认；若省略: 模型无法请求结束计划阶段
            "description": "退出计划模式，输出最终执行计划并等待用户确认；用户确认前不要继续执行有副作用的工具。",  # 新增代码+PlanMode: 告诉模型退出后仍要等待用户确认；若省略: 模型可能计划后立刻执行
            "parameters": {  # 新增代码+PlanMode: JSON Schema 描述退出计划模式的参数；若省略: 模型不知道如何传 plan/steps
                "type": "object",  # 新增代码+PlanMode: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+PlanMode: 声明允许的参数字段；若省略: plan/steps 无法进入输出 schema
                    "plan": {"type": "string", "description": "要展示给用户确认的最终计划正文。"},  # 新增代码+PlanMode: plan 保存最终计划文本；若省略: 用户看不到可确认的计划
                    "steps": {"type": "array", "description": "可选的最终步骤列表。", "items": {"type": "string"}},  # 新增代码+PlanMode: steps 保存最终步骤；若省略: 计划只能是不易检查的整段文字
                },  # 新增代码+PlanMode: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["plan"],  # 新增代码+PlanMode: 退出计划模式必须提供最终计划；若省略: 空计划会进入工具层
                "additionalProperties": False,  # 新增代码+PlanMode: 禁止模型传入无关参数；若省略: 参数污染会增加计划状态歧义
            },  # 新增代码+PlanMode: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+PlanMode: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+PlanMode: exit_plan_mode 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+PlanVerification: 第三十二个工具定义开始，暴露计划执行结果验证能力；若省略: 模型无法结构化说明计划是否按步骤完成
        "type": "function",  # 新增代码+PlanVerification: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+PlanVerification: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "verify_plan_execution",  # 新增代码+PlanVerification: 工具名用于验证计划执行结果；若省略: 模型无法请求计划执行验证
            "description": "验证计划执行结果，汇总已执行步骤、证据、遗漏项和最终状态；不执行命令，只做结构化审计输出。",  # 新增代码+PlanVerification: 告诉模型该工具只做审计汇总不做副作用执行；若省略: 模型可能误以为它会自动运行测试或命令
            "parameters": {  # 新增代码+PlanVerification: JSON Schema 描述计划验证参数；若省略: 模型不知道如何传 plan/executed_steps/evidence/open_items/result
                "type": "object",  # 新增代码+PlanVerification: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+PlanVerification: 声明允许的参数字段；若省略: 验证字段无法进入输出 schema
                    "plan": {"type": "string", "description": "可选计划正文；省略时使用最近 exit_plan_mode 保存的计划。"},  # 新增代码+PlanVerification: plan 保存待验证计划；若省略: 工具无法在没有历史计划时知道验证对象
                    "executed_steps": {"type": "array", "description": "已经执行的计划步骤列表。", "items": {"type": "string"}},  # 新增代码+PlanVerification: executed_steps 保存实际完成步骤；若省略: 用户无法审计计划执行覆盖情况
                    "evidence": {"type": "array", "description": "验证证据列表，例如测试命令输出、文件路径、日志摘要。", "items": {"type": "string"}},  # 新增代码+PlanVerification: evidence 保存验证依据；若省略: 工具可能只给结论没有证据
                    "open_items": {"type": "array", "description": "尚未完成或仍有风险的事项列表。", "items": {"type": "string"}},  # 新增代码+PlanVerification: open_items 保存遗漏或风险；若省略: 未完成事项无法结构化呈现
                    "result": {"type": "string", "description": "模型对执行结果的结论，例如 verified、incomplete、blocked、failed。"},  # 新增代码+PlanVerification: result 保存模型自评状态；若省略: 工具只能从遗漏项粗略推断状态
                },  # 新增代码+PlanVerification: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["executed_steps", "evidence"],  # 新增代码+PlanVerification: 验证必须提供已执行步骤和证据；若省略: 空验证也可能被当成成功
                "additionalProperties": False,  # 新增代码+PlanVerification: 禁止模型传入无关参数；若省略: 参数污染会增加计划验证歧义
            },  # 新增代码+PlanVerification: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+PlanVerification: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+PlanVerification: verify_plan_execution 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+WorktreeIsolation: 第三十三个工具定义开始，暴露进入工作区隔离状态能力；若省略: 模型无法在大改动前声明隔离上下文
        "type": "function",  # 新增代码+WorktreeIsolation: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+WorktreeIsolation: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "enter_worktree",  # 新增代码+WorktreeIsolation: 工具名用于进入 worktree 隔离状态；若省略: 模型无法请求隔离大范围改动
            "description": "进入轻量工作区隔离状态，记录隔离目录、原因和目标；不创建真实 git worktree，也不执行文件或命令副作用。",  # 新增代码+WorktreeIsolation: 告诉模型该工具只记录状态不创建目录；若省略: 模型可能误以为真实 worktree 已经存在
            "parameters": {  # 新增代码+WorktreeIsolation: JSON Schema 描述进入隔离状态参数；若省略: 模型不知道如何传 reason/goal/worktree_path
                "type": "object",  # 新增代码+WorktreeIsolation: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+WorktreeIsolation: 声明允许的参数字段；若省略: 隔离状态字段无法进入输出 schema
                    "reason": {"type": "string", "description": "为什么需要进入工作区隔离状态，例如大范围改动、风险较高或需要保护主工作区。"},  # 新增代码+WorktreeIsolation: reason 保存进入隔离状态原因；若省略: 用户看不到为什么要隔离
                    "goal": {"type": "string", "description": "本次隔离工作要达成的目标。"},  # 新增代码+WorktreeIsolation: goal 保存隔离工作目标；若省略: 后续退出时缺少核对方向
                    "worktree_path": {"type": "string", "description": "相对工作区根目录的隔离目录路径，例如 .worktrees/feature-x；必须保持在工作区内。"},  # 新增代码+WorktreeIsolation: worktree_path 保存隔离目录意图；若省略: 模型无法说明后续改动应落在哪个隔离上下文
                },  # 新增代码+WorktreeIsolation: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["reason", "goal", "worktree_path"],  # 新增代码+WorktreeIsolation: 进入隔离状态必须提供原因、目标和路径；若省略: 隔离上下文会过于模糊
                "additionalProperties": False,  # 新增代码+WorktreeIsolation: 禁止模型传入无关参数；若省略: 参数污染会增加隔离状态歧义
            },  # 新增代码+WorktreeIsolation: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+WorktreeIsolation: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+WorktreeIsolation: enter_worktree 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+WorktreeIsolation: 第三十四个工具定义开始，暴露退出工作区隔离状态能力；若省略: 模型无法结构化交接隔离工作结果
        "type": "function",  # 新增代码+WorktreeIsolation: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+WorktreeIsolation: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "exit_worktree",  # 新增代码+WorktreeIsolation: 工具名用于退出 worktree 隔离状态；若省略: 模型无法请求结束隔离上下文
            "description": "退出轻量工作区隔离状态，汇总隔离工作结果、剩余风险和最终状态；不删除目录，也不执行 git 操作。",  # 新增代码+WorktreeIsolation: 告诉模型退出只做状态交接不做破坏性清理；若省略: 模型可能误以为工具会删除隔离目录
            "parameters": {  # 新增代码+WorktreeIsolation: JSON Schema 描述退出隔离状态参数；若省略: 模型不知道如何传 summary/open_items/result
                "type": "object",  # 新增代码+WorktreeIsolation: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+WorktreeIsolation: 声明允许的参数字段；若省略: 退出状态字段无法进入输出 schema
                    "summary": {"type": "string", "description": "隔离工作完成情况总结。"},  # 新增代码+WorktreeIsolation: summary 保存退出交接摘要；若省略: 用户不知道隔离上下文做了什么
                    "open_items": {"type": "array", "description": "尚未完成或仍有风险的事项列表。", "items": {"type": "string"}},  # 新增代码+WorktreeIsolation: open_items 保存未完成事项；若省略: 隔离工作风险无法结构化呈现
                    "result": {"type": "string", "description": "模型对隔离工作结果的结论，例如 finished、incomplete、blocked、failed。"},  # 新增代码+WorktreeIsolation: result 保存模型自评状态；若省略: 工具只能从遗漏项粗略推断状态
                },  # 新增代码+WorktreeIsolation: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["summary"],  # 新增代码+WorktreeIsolation: 退出隔离状态必须提供总结；若省略: 空交接也可能被当成成功
                "additionalProperties": False,  # 新增代码+WorktreeIsolation: 禁止模型传入无关参数；若省略: 参数污染会增加退出状态歧义
            },  # 新增代码+WorktreeIsolation: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+WorktreeIsolation: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+WorktreeIsolation: exit_worktree 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+LSP工具: 第三十五个工具定义开始，暴露 Python 文件符号读取能力；若省略: 模型无法像 coding agent 一样先看类和函数轮廓
        "type": "function",  # 新增代码+LSP工具: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+LSP工具: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "lsp_symbols",  # 新增代码+LSP工具: 工具名用于读取源码符号列表；若省略: 模型无法请求符号级代码理解
            "description": "读取工作区内 Python .py 文件的类、方法和函数符号；当前为标准库 ast 实现的 LSP 最小版，不启动真实语言服务器。",  # 新增代码+LSP工具: 告诉模型工具能力和边界；若省略: 模型可能误以为所有语言和完整 LSP 都已支持
            "parameters": {  # 新增代码+LSP工具: JSON Schema 描述符号读取参数；若省略: 模型不知道如何传 path/max_results
                "type": "object",  # 新增代码+LSP工具: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+LSP工具: 声明允许的参数字段；若省略: path/max_results 无法进入输出 schema
                    "path": {"type": "string", "description": "工作区内要分析的 Python .py 文件路径。"},  # 新增代码+LSP工具: path 指定目标文件；若省略: 工具不知道读取哪个源码文件
                    "max_results": {"type": "integer", "description": "可选最大返回符号数，默认 10，范围 1 到 20。"},  # 新增代码+LSP工具: max_results 控制输出长度；若省略: 大文件符号列表可能撑爆上下文
                },  # 新增代码+LSP工具: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["path"],  # 新增代码+LSP工具: 读取符号必须提供路径；若省略: 空路径调用会进入工具层再失败
                "additionalProperties": False,  # 新增代码+LSP工具: 禁止模型传入无关参数；若省略: 参数污染会增加工具行为歧义
            },  # 新增代码+LSP工具: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+LSP工具: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+LSP工具: lsp_symbols 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+LSP工具: 第三十六个工具定义开始，暴露 Python 符号定义定位能力；若省略: 模型无法请求跳转到定义
        "type": "function",  # 新增代码+LSP工具: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+LSP工具: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "lsp_definition",  # 新增代码+LSP工具: 工具名用于定位指定符号定义；若省略: 模型无法按名称查找定义位置
            "description": "在工作区内 Python .py 文件中按符号名定位类、方法或函数定义；当前为标准库 ast 实现的 LSP 最小版。",  # 新增代码+LSP工具: 告诉模型定义定位范围；若省略: 模型可能期待跨文件完整索引
            "parameters": {  # 新增代码+LSP工具: JSON Schema 描述定义定位参数；若省略: 模型不知道如何传 path/symbol
                "type": "object",  # 新增代码+LSP工具: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+LSP工具: 声明允许的参数字段；若省略: path/symbol 无法进入输出 schema
                    "path": {"type": "string", "description": "工作区内要分析的 Python .py 文件路径。"},  # 新增代码+LSP工具: path 指定目标文件；若省略: 工具不知道在哪个文件查找符号
                    "symbol": {"type": "string", "description": "要查找定义的类名、函数名或方法名。"},  # 新增代码+LSP工具: symbol 指定目标名称；若省略: 工具无法判断要定位哪个定义
                },  # 新增代码+LSP工具: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["path", "symbol"],  # 新增代码+LSP工具: 定义定位必须同时提供路径和符号名；若省略: 空查找会进入工具层再失败
                "additionalProperties": False,  # 新增代码+LSP工具: 禁止模型传入无关参数；若省略: 参数污染会增加工具行为歧义
            },  # 新增代码+LSP工具: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+LSP工具: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+LSP工具: lsp_definition 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+LSP工具: 第三十七个工具定义开始，暴露 Python 语法诊断能力；若省略: 模型无法像 coding agent 一样先看语法错误
        "type": "function",  # 新增代码+LSP工具: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+LSP工具: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "lsp_diagnostics",  # 新增代码+LSP工具: 工具名用于读取 Python 语法诊断；若省略: 模型无法请求诊断信息
            "description": "读取工作区内 Python .py 文件的语法诊断；当前为标准库 ast 实现的 LSP 最小版，只报告 SyntaxError 或无诊断。",  # 新增代码+LSP工具: 告诉模型诊断范围和限制；若省略: 模型可能误以为已有完整类型检查
            "parameters": {  # 新增代码+LSP工具: JSON Schema 描述诊断参数；若省略: 模型不知道如何传 path
                "type": "object",  # 新增代码+LSP工具: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+LSP工具: 声明允许的参数字段；若省略: path 无法进入输出 schema
                    "path": {"type": "string", "description": "工作区内要诊断的 Python .py 文件路径。"},  # 新增代码+LSP工具: path 指定目标文件；若省略: 工具不知道诊断哪个源码文件
                },  # 新增代码+LSP工具: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["path"],  # 新增代码+LSP工具: 诊断必须提供路径；若省略: 空路径调用会进入工具层再失败
                "additionalProperties": False,  # 新增代码+LSP工具: 禁止模型传入无关参数；若省略: 参数污染会增加工具行为歧义
            },  # 新增代码+LSP工具: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+LSP工具: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+LSP工具: lsp_diagnostics 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+REPL工具: 第三十八个工具定义开始，暴露安全批量工具编排能力；若省略: 模型无法把多次只读查询组织成可审计批次
        "type": "function",  # 新增代码+REPL工具: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+REPL工具: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "repl",  # 新增代码+REPL工具: 工具名用于执行安全白名单内的批量子调用；若省略: 模型无法请求 REPL 最小版
            "description": "按顺序批量执行安全白名单内的内置只读、状态和符号工具；当前不是任意代码执行器，不调用写入、命令、MCP 外部工具或子 agent 启动工具。",  # 新增代码+REPL工具: 告诉模型工具用途和安全边界；若省略: 模型可能误以为 repl 可以执行任意脚本
            "parameters": {  # 新增代码+REPL工具: JSON Schema 描述批量调用参数；若省略: 模型不知道如何传 calls/stop_on_error/max_output_chars
                "type": "object",  # 新增代码+REPL工具: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+REPL工具: 声明允许的参数字段；若省略: calls 等字段无法进入输出 schema
                    "calls": {  # 新增代码+REPL工具: calls 保存 1 到 5 个安全子调用；若省略: repl 没有批量步骤输入
                        "type": "array",  # 新增代码+REPL工具: calls 必须是数组；若省略: 多个子调用无法标准表达
                        "description": "要顺序执行的 1 到 5 个安全子调用，每项包含 tool_name 和 arguments。",  # 新增代码+REPL工具: 说明批量大小和子调用结构；若省略: 模型可能一次塞入过多步骤
                        "minItems": 1,  # 新增代码+REPL工具: 至少需要一个子调用；若省略: 空批次可能进入工具层
                        "maxItems": 5,  # 新增代码+REPL工具: 最多允许五个子调用；若省略: 输出可能撑爆上下文
                        "items": {  # 新增代码+REPL工具: 定义单个子调用对象；若省略: calls 内部结构不受约束
                            "type": "object",  # 新增代码+REPL工具: 每个子调用必须是对象；若省略: 字符串步骤无法携带参数
                            "properties": {  # 新增代码+REPL工具: 声明子调用允许字段；若省略: tool_name/arguments 无法被结构化约束
                                "tool_name": {"type": "string", "description": "安全白名单内的内置工具名，例如 tool_search、lsp_symbols、todo_read。"},  # 新增代码+REPL工具: tool_name 指定要执行的子工具；若省略: repl 不知道执行哪个工具
                                "arguments": {"type": "object", "description": "传给该子工具的参数对象；不需要参数时传空对象。", "additionalProperties": True},  # 新增代码+REPL工具: arguments 保存子工具入参；若省略: 子工具无法收到 path/query 等参数
                            },  # 新增代码+REPL工具: 子调用 properties 定义结束；若省略: 子调用 schema 不完整
                            "required": ["tool_name", "arguments"],  # 新增代码+REPL工具: 每个子调用必须有工具名和参数对象；若省略: 空子调用会进入工具层
                            "additionalProperties": False,  # 新增代码+REPL工具: 禁止子调用对象传入无关字段；若省略: 参数污染会增加批量执行歧义
                        },  # 新增代码+REPL工具: 单个子调用 schema 结束；若省略: calls item 定义不完整
                    },  # 新增代码+REPL工具: calls 字段定义结束；若省略: 参数 schema 不完整
                    "stop_on_error": {"type": "boolean", "description": "可选；子调用返回失败时是否停止后续调用，默认 true。"},  # 新增代码+REPL工具: stop_on_error 控制失败后是否继续；若省略: 模型无法表达批量容错策略
                    "max_output_chars": {"type": "integer", "description": "可选；每个子调用最大输出字符数，默认 4000，最大 8000。"},  # 新增代码+REPL工具: max_output_chars 控制每段输出长度；若省略: 子调用长输出可能撑爆上下文
                },  # 新增代码+REPL工具: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["calls"],  # 新增代码+REPL工具: 批量执行必须提供 calls；若省略: 空调用会进入工具层再失败
                "additionalProperties": False,  # 新增代码+REPL工具: 禁止模型传入无关参数；若省略: 参数污染会增加工具行为歧义
            },  # 新增代码+REPL工具: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+REPL工具: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+REPL工具: repl 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+CronMonitor: 第三十九个工具定义开始，暴露教学版定时任务登记能力；若省略: 模型无法记录稍后或定期检查任务
        "type": "function",  # 新增代码+CronMonitor: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+CronMonitor: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "cron_create",  # 新增代码+CronMonitor: 工具名用于创建进程内定时任务记录；若省略: 模型无法请求登记定时检查
            "description": "登记教学版进程内定时任务记录；不创建系统定时器，不自动执行，不跨进程常驻，也不发送通知。",  # 新增代码+CronMonitor: 告诉模型该工具只记录不调度；若省略: 模型可能误以为真实定时任务已启动
            "parameters": {  # 新增代码+CronMonitor: JSON Schema 描述定时任务创建参数；若省略: 模型不知道如何传 name/schedule/prompt
                "type": "object",  # 新增代码+CronMonitor: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+CronMonitor: 声明允许的参数字段；若省略: cron_create 字段无法进入输出 schema
                    "name": {"type": "string", "description": "定时任务短名称。"},  # 新增代码+CronMonitor: name 保存可读名称；若省略: 列表里多个任务难以区分
                    "schedule": {"type": "string", "description": "用户可读的触发时间说明，例如 daily 09:00、weekly Monday、after next reply。"},  # 新增代码+CronMonitor: schedule 保存触发说明；若省略: 定时记录不知道何时检查
                    "prompt": {"type": "string", "description": "到点时应该检查或执行的任务说明。"},  # 新增代码+CronMonitor: prompt 保存任务内容；若省略: 定时记录只有时间没有任务
                    "stop_condition": {"type": "string", "description": "可选停止条件，说明何时不再需要这条定时记录。"},  # 新增代码+CronMonitor: stop_condition 保存收束边界；若省略: 长期任务容易没有结束条件
                },  # 新增代码+CronMonitor: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["name", "schedule", "prompt"],  # 新增代码+CronMonitor: 创建记录必须提供名称、时间和任务；若省略: 可能登记不可执行的空任务
                "additionalProperties": False,  # 新增代码+CronMonitor: 禁止模型传入无关参数；若省略: 参数污染会增加记录语义歧义
            },  # 新增代码+CronMonitor: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+CronMonitor: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+CronMonitor: cron_create 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+CronMonitor: 第四十个工具定义开始，暴露教学版定时任务列表能力；若省略: 模型无法查看已登记的定时任务记录
        "type": "function",  # 新增代码+CronMonitor: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+CronMonitor: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "cron_list",  # 新增代码+CronMonitor: 工具名用于列出进程内定时任务记录；若省略: 模型无法请求查看 Cron 总览
            "description": "列出当前进程内登记的教学版定时任务记录；只读，不触发任何任务执行。",  # 新增代码+CronMonitor: 告诉模型该工具只读；若省略: 模型可能混淆列出和执行
            "parameters": {  # 新增代码+CronMonitor: JSON Schema 描述定时任务列表参数；若省略: 模型不知道如何筛选和限制数量
                "type": "object",  # 新增代码+CronMonitor: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+CronMonitor: 声明允许的参数字段；若省略: state/max_results 无法进入输出 schema
                    "state": {"type": "string", "enum": ["all", "active", "deleted"], "description": "可选状态筛选，默认 active。"},  # 新增代码+CronMonitor: state 避免和 task_list.status 冲突并筛选记录；若省略: 列表无法按状态过滤
                    "max_results": {"type": "integer", "description": "可选最大返回记录数，默认 10，范围 1 到 20。"},  # 新增代码+CronMonitor: max_results 控制输出长度；若省略: 大量记录可能撑爆上下文
                },  # 新增代码+CronMonitor: properties 定义结束；若省略: 参数 schema 不完整
                "required": [],  # 新增代码+CronMonitor: 列表工具允许无参数调用；若省略: 模型必须传无意义字段
                "additionalProperties": False,  # 新增代码+CronMonitor: 禁止模型传入无关参数；若省略: 参数污染会增加列表行为歧义
            },  # 新增代码+CronMonitor: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+CronMonitor: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+CronMonitor: cron_list 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+CronMonitor: 第四十一个工具定义开始，暴露教学版定时任务删除能力；若省略: 模型无法回收不再需要的定时记录
        "type": "function",  # 新增代码+CronMonitor: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+CronMonitor: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "cron_delete",  # 新增代码+CronMonitor: 工具名用于删除进程内定时任务记录；若省略: 模型无法请求回收 Cron 记录
            "description": "删除教学版进程内定时任务记录；必须 confirm_delete=true；不删除系统任务，因为本工具从不创建系统定时器。",  # 新增代码+CronMonitor: 告诉模型删除边界和确认要求；若省略: 模型可能低估删除风险或误解系统状态
            "parameters": {  # 新增代码+CronMonitor: JSON Schema 描述删除参数；若省略: 模型不知道如何传 cron_id/confirm_delete
                "type": "object",  # 新增代码+CronMonitor: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+CronMonitor: 声明允许的参数字段；若省略: 删除字段无法进入输出 schema
                    "cron_id": {"type": "string", "description": "cron_create 返回的定时任务 id。"},  # 新增代码+CronMonitor: cron_id 指定要删除的记录；若省略: 工具不知道删除哪个任务
                    "confirm_delete": {"type": "boolean", "description": "必须显式传 true 才会删除记录。"},  # 新增代码+CronMonitor: confirm_delete 提供安全确认；若省略: 模型可能误删记录
                },  # 新增代码+CronMonitor: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["cron_id"],  # 新增代码+CronMonitor: 删除必须提供目标 id；若省略: 空删除会进入工具层再失败
                "additionalProperties": False,  # 新增代码+CronMonitor: 禁止模型传入无关参数；若省略: 参数污染会增加删除歧义
            },  # 新增代码+CronMonitor: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+CronMonitor: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+CronMonitor: cron_delete 工具定义结束；若省略: 工具列表语法不完整
    {  # 新增代码+CronMonitor: 第四十二个工具定义开始，暴露教学版监控记录管理能力；若省略: 模型无法登记或更新持续观察目标
        "type": "function",  # 新增代码+CronMonitor: OpenAI-compatible 工具类型固定写 function；若省略: 模型接口不会识别这是可调用工具
        "function": {  # 新增代码+CronMonitor: function 内部描述工具名称、说明和参数；若省略: 工具缺少标准定义结构
            "name": "monitor",  # 新增代码+CronMonitor: 工具名用于管理进程内监控记录；若省略: 模型无法请求 Monitor 最小版
            "description": "管理教学版进程内监控记录，action 支持 create/list/delete/record_result；不启动真实监听器，不自动检查，不发送通知。",  # 新增代码+CronMonitor: 告诉模型多动作和安全边界；若省略: 模型可能误以为已有真实监控服务
            "parameters": {  # 新增代码+CronMonitor: JSON Schema 描述 monitor 多动作参数；若省略: 模型不知道如何传 action 和对应字段
                "type": "object",  # 新增代码+CronMonitor: 参数必须是对象；若省略: 工具调用结构不明确
                "properties": {  # 新增代码+CronMonitor: 声明允许的参数字段；若省略: monitor 字段无法进入输出 schema
                    "action": {"type": "string", "enum": ["create", "list", "delete", "record_result"], "description": "要执行的监控记录动作。"},  # 新增代码+CronMonitor: action 指定创建、列出、删除或记录结果；若省略: 单个 monitor 工具无法区分动作
                    "name": {"type": "string", "description": "创建监控时使用的短名称。"},  # 新增代码+CronMonitor: name 保存监控名称；若省略: 多个监控记录难以区分
                    "target": {"type": "string", "description": "创建监控时要观察的目标，例如测试、网页、任务、指标或文件。"},  # 新增代码+CronMonitor: target 保存观察对象；若省略: 监控记录不知道关注什么
                    "condition": {"type": "string", "description": "创建监控时的触发或关注条件。"},  # 新增代码+CronMonitor: condition 保存命中条件；若省略: 监控记录不知道什么算异常或完成
                    "check_interval": {"type": "string", "description": "可选检查频率说明，默认 manual。"},  # 新增代码+CronMonitor: check_interval 保存复查频率；若省略: 监控节奏不清楚
                    "stop_condition": {"type": "string", "description": "可选停止监控条件。"},  # 新增代码+CronMonitor: stop_condition 保存收束边界；若省略: 监控可能没有退出条件
                    "monitor_id": {"type": "string", "description": "monitor create 返回的监控记录 id。"},  # 新增代码+CronMonitor: monitor_id 指定后续动作目标；若省略: 删除或记录结果无法定位记录
                    "result": {"type": "string", "description": "record_result 动作写入的最近一次观察结果。"},  # 新增代码+CronMonitor: result 保存检查证据；若省略: monitor 无法记录最近观察内容
                    "result_status": {"type": "string", "enum": ["ok", "triggered", "blocked", "error"], "description": "record_result 动作写入的最近状态。"},  # 新增代码+CronMonitor: result_status 保存结果状态；若省略: 用户无法快速判断是否命中条件
                    "state": {"type": "string", "enum": ["all", "active", "deleted"], "description": "list 动作的可选状态筛选，默认 active。"},  # 新增代码+CronMonitor: state 筛选记录且避免与 task status 冲突；若省略: monitor list 无法过滤记录
                    "max_results": {"type": "integer", "description": "list 动作可选最大返回记录数，默认 10，范围 1 到 20。"},  # 新增代码+CronMonitor: max_results 控制列表长度；若省略: 大量监控记录可能撑爆上下文
                    "confirm_delete": {"type": "boolean", "description": "delete 动作必须显式传 true 才会删除记录。"},  # 新增代码+CronMonitor: confirm_delete 提供删除确认；若省略: 模型可能误删监控记录
                },  # 新增代码+CronMonitor: properties 定义结束；若省略: 参数 schema 不完整
                "required": ["action"],  # 新增代码+CronMonitor: monitor 必须指定动作；若省略: 工具无法判断要做什么
                "additionalProperties": False,  # 新增代码+CronMonitor: 禁止模型传入无关参数；若省略: 参数污染会增加多动作工具歧义
            },  # 新增代码+CronMonitor: parameters 定义结束；若省略: Python 字典结构不完整
        },  # 新增代码+CronMonitor: function 定义结束；若省略: 工具定义结构不完整
    },  # 新增代码+CronMonitor: monitor 工具定义结束；若省略: 工具列表语法不完整
]  # 作用: 工具 schema 列表结束


KERNEL_TOOL_NAMES: set[str] = {  # 修改代码+极简工具面: 定义首轮必须可见的四个原子工具；若没有这行代码，模型首轮工具面会继续被旧内核工具撑大
    "read",  # 新增代码+极简工具面: 保留读取原子工具；若没有这行代码，模型首轮无法读取代码、提示词和 skill 索引
    "write",  # 新增代码+极简工具面: 保留写入原子工具；若没有这行代码，模型首轮无法在确认后创建或覆盖文件
    "edit",  # 新增代码+极简工具面: 保留定点编辑原子工具；若没有这行代码，模型首轮只能用整文件覆盖完成小改动
    "bash",  # 新增代码+极简工具面: 保留命令执行原子工具；若没有这行代码，模型首轮无法运行测试、搜索或脚本命令
}  # 修改代码+极简工具面: 四原子工具集合结束；若没有这行代码，Python 集合语法不完整


DYNAMIC_SKILL_CAPABILITY_PACKS: dict[str, tuple[str, ...]] = {  # 新增代码+浏览器自动化: 定义哪些动态 skill 读取后可以解锁对应工具能力包；若没有这行代码，read-based skill 只能加载提示词不能激活真实工具
    "browser_automation": ("browser_automation",),  # 新增代码+浏览器自动化: 普通浏览器 skill 只解锁普通浏览器自动化工具包；若没有这行代码，browser_open/click 等工具读完 skill 后仍不可见
    "real_chrome": ("real_chrome", "browser_automation"),  # 新增代码+真实浏览器自动化: 真实 Chrome skill 同时准备连接工具和后续页面操作工具；若没有这行代码，连接成功后仍缺少打开、点击、截图等动作工具
}  # 新增代码+浏览器自动化: 动态 skill 到能力包映射结束；若没有这行代码，Python 字典语法不完整


BUILTIN_TOOL_CAPABILITY_PACKS: dict[str, str] = {  # 新增代码+CapabilityPacks: 定义内置工具到能力包的映射；若没有这行代码，内置工具无法按包延迟加载
    "read_file": "file_operations",  # 新增代码+CapabilityPacks: 把读取文件归入文件操作包；若没有这行代码，文件读取会缺少批量加载入口
    "write_file": "file_operations",  # 新增代码+CapabilityPacks: 把写文件归入文件操作包；若没有这行代码，文件修改工具无法随文件能力一起加载
    "append_memory": "memory",  # 新增代码+CapabilityPacks: 把长期记忆写入归入记忆包；若没有这行代码，记忆写入会继续常驻首轮工具池
    "todo_read": "planning",  # 新增代码+CapabilityPacks: 把读取任务清单归入计划包；若没有这行代码，计划流程无法一次加载任务工具
    "todo_write": "planning",  # 新增代码+CapabilityPacks: 把写入任务清单归入计划包；若没有这行代码，复杂任务进度工具会继续占用首轮 schema
    "start_background_command": "execution",  # 新增代码+CapabilityPacks: 把启动后台命令归入执行包；若没有这行代码，命令执行能力无法按需加载
    "read_background_command": "execution",  # 新增代码+CapabilityPacks: 把读取后台输出归入执行包；若没有这行代码，后台命令生命周期会被拆散
    "stop_background_command": "execution",  # 新增代码+CapabilityPacks: 把停止后台命令归入执行包；若没有这行代码，执行包缺少收尾能力
    "notebook_read": "notebook",  # 新增代码+CapabilityPacks: 把读取 Notebook 归入 notebook 包；若没有这行代码，Notebook 能力无法按需加载
    "notebook_edit": "notebook",  # 新增代码+CapabilityPacks: 把编辑 Notebook 归入 notebook 包；若没有这行代码，Notebook 修改工具会继续常驻
    "list_mcp_resources": "mcp",  # 新增代码+CapabilityPacks: 把 MCP resource 列表归入 MCP 包；若没有这行代码，MCP 资源能力无法按需加载
    "read_mcp_resource": "mcp",  # 新增代码+CapabilityPacks: 把 MCP resource 读取归入 MCP 包；若没有这行代码，MCP 读取能力会和发现能力脱节
    "list_mcp_prompts": "mcp",  # 新增代码+CapabilityPacks: 把 MCP prompt 列表归入 MCP 包；若没有这行代码，远程 prompt 能力无法按需加载
    "read_mcp_prompt": "mcp",  # 新增代码+CapabilityPacks: 把 MCP prompt 读取归入 MCP 包；若没有这行代码，远程 prompt 读取会继续首轮暴露
    "listen_mcp_stream": "mcp",  # 新增代码+CapabilityPacks: 把 MCP stream 监听归入 MCP 包；若没有这行代码，低频流能力会撑大首轮 schema
    "task": "delegation",  # 新增代码+CapabilityPacks: 把子任务启动归入委派包；若没有这行代码，子 agent 能力无法整体加载
    "task_output": "delegation",  # 新增代码+CapabilityPacks: 把子任务输出查询归入委派包；若没有这行代码，委派任务无法方便跟踪
    "task_stop": "delegation",  # 新增代码+CapabilityPacks: 把子任务停止归入委派包；若没有这行代码，委派包缺少取消能力
    "task_list": "delegation",  # 新增代码+CapabilityPacks: 把子任务列表归入委派包；若没有这行代码，多任务管理无法按包恢复
    "task_get": "delegation",  # 新增代码+CapabilityPacks: 把子任务详情归入委派包；若没有这行代码，查看子任务细节需要单独搜索
    "task_update": "delegation",  # 新增代码+CapabilityPacks: 把子任务元信息更新归入委派包；若没有这行代码，委派记录维护能力不完整
    "team_create": "delegation",  # 新增代码+CapabilityPacks: 把教学版 peer 创建归入委派包；若没有这行代码，团队协作工具会继续常驻
    "send_message": "delegation",  # 新增代码+CapabilityPacks: 把 peer 消息发送归入委派包；若没有这行代码，团队通信能力会和 peer 生命周期分离
    "list_peers": "delegation",  # 新增代码+CapabilityPacks: 把 peer 列表归入委派包；若没有这行代码，团队状态查询无法随包加载
    "read_peer_messages": "delegation",  # 新增代码+CapabilityPacks: 把 peer 消息读取归入委派包；若没有这行代码，团队 inbox 能力会继续占用首轮 schema
    "ack_peer_message": "delegation",  # 新增代码+CapabilityPacks: 把 peer 消息确认归入委派包；若没有这行代码，消息生命周期不完整
    "team_delete": "delegation",  # 新增代码+CapabilityPacks: 把 peer 删除归入委派包；若没有这行代码，团队清理能力不会随包加载
    "team_start_task": "delegation",  # 新增代码+CapabilityPacks: 把 peer 绑定后台任务归入委派包；若没有这行代码，团队任务能力会被拆散
    "enter_plan_mode": "planning",  # 新增代码+CapabilityPacks: 把进入计划模式归入计划包；若没有这行代码，复杂任务确认流程无法按包加载
    "exit_plan_mode": "planning",  # 新增代码+CapabilityPacks: 把退出计划模式归入计划包；若没有这行代码，计划确认流程不完整
    "verify_plan_execution": "planning",  # 新增代码+CapabilityPacks: 把计划执行验证归入计划包；若没有这行代码，计划包缺少收尾审计
    "enter_worktree": "planning",  # 新增代码+CapabilityPacks: 把轻量工作区隔离入口归入计划包；若没有这行代码，大范围改动准备流程会被拆散
    "exit_worktree": "planning",  # 新增代码+CapabilityPacks: 把退出隔离状态归入计划包；若没有这行代码，隔离流程缺少收尾工具
    "lsp_symbols": "diagnostics",  # 新增代码+CapabilityPacks: 把符号读取归入诊断包；若没有这行代码，代码理解工具会继续首轮暴露
    "lsp_definition": "diagnostics",  # 新增代码+CapabilityPacks: 把定义定位归入诊断包；若没有这行代码，符号跳转能力无法随诊断包加载
    "lsp_diagnostics": "diagnostics",  # 新增代码+CapabilityPacks: 把语法诊断归入诊断包；若没有这行代码，诊断包缺少错误检查能力
    "repl": "diagnostics",  # 新增代码+CapabilityPacks: 把安全批量只读编排归入诊断包；若没有这行代码，REPL 会继续占用首轮 schema
    "cron_create": "long_running_work",  # 新增代码+CapabilityPacks: 把定时任务登记归入长期工作包；若没有这行代码，低频定时能力会继续常驻
    "cron_list": "long_running_work",  # 新增代码+CapabilityPacks: 把定时任务列表归入长期工作包；若没有这行代码，长期工作记录无法查询
    "cron_delete": "long_running_work",  # 新增代码+CapabilityPacks: 把定时任务删除归入长期工作包；若没有这行代码，长期工作包缺少清理能力
    "monitor": "long_running_work",  # 新增代码+CapabilityPacks: 把监控记录归入长期工作包；若没有这行代码，监控能力会继续撑大首轮 schema
}  # 新增代码+CapabilityPacks: 能力包映射结束；若没有这行代码，Python 字典语法不完整
