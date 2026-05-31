"""本地 workspace tools MCP server，用来给 learning_agent 提供 Claude Code 高频工作区工具。"""  # 新增代码+workspace_tools: 说明这个文件提供本地工作区工具；若省略: 初学者打开文件时不容易理解它和 browser_search MCP 的区别

from __future__ import annotations  # 新增代码+workspace_tools: 允许类型注解延迟解析；若省略: 前向类型写法在部分 Python 版本里更脆弱

import difflib  # 新增代码+edit_file预览: 生成 dry_run 统一 diff 预览；若省略: edit_file 无法在不写文件时展示具体会改哪些行
import json  # 新增代码+workspace_tools: 解析和输出 MCP 使用的单行 JSON-RPC 消息；若省略: server 无法读写协议消息
import shutil  # 新增代码+workspace_tools: 查找 powershell 或 pwsh 可执行文件；若省略: run_powershell 无法跨环境定位命令解释器
import subprocess  # 新增代码+workspace_tools: 执行 PowerShell 命令并捕获输出；若省略: run_powershell 工具无法实现
import sys  # 新增代码+workspace_tools: 读取 stdin、写 stdout、读取启动参数；若省略: server 无法作为 stdio MCP 进程工作
from pathlib import Path, PurePosixPath  # 新增代码+workspace_tools: 处理工作区路径和 glob 模式片段；若省略: 路径安全检查会更脆弱
from typing import Any  # 新增代码+workspace_tools: 标注 JSON 字典和工具参数的通用类型；若省略: 类型提示会更难读


if hasattr(sys.stdin, "reconfigure"):  # 新增代码+workspace_tools: 检查 stdin 是否支持重新设置编码；若省略: 旧 Python 环境可能没有 reconfigure 方法
    sys.stdin.reconfigure(encoding="utf-8")  # 新增代码+workspace_tools: 强制 MCP 输入按 UTF-8 读取；若省略: 中文参数在 Windows 管道里可能乱码
if hasattr(sys.stdout, "reconfigure"):  # 新增代码+workspace_tools: 检查 stdout 是否支持重新设置编码；若省略: 旧 Python 环境可能没有 reconfigure 方法
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")  # 新增代码+workspace_tools: 强制 MCP 输出按 UTF-8 写出；若省略: client 解码中文 tools/list 时可能失败


WORKSPACE = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.cwd().resolve()  # 新增代码+workspace_tools: 使用启动参数指定工作区，缺省用当前目录；若省略: server 不知道应该限制在哪个目录内
MAX_FILE_BYTES = 1_000_000  # 新增代码+workspace_tools: 限制 grep 单文件读取大小；若省略: 大文件可能拖慢工具并撑爆模型上下文
DEFAULT_MAX_RESULTS = 100  # 新增代码+workspace_tools: 限制 glob/grep 默认返回数量；若省略: 大项目会一次返回过多结果
DEFAULT_READ_MAX_CHARS = 12000  # 新增代码+MCP文件工具: 限制 read_file 默认返回字符数；若省略: 读取大文件可能撑爆模型上下文
DEFAULT_COMMAND_TIMEOUT_SECONDS = 20  # 新增代码+workspace_tools: 限制 PowerShell 命令默认执行时间；若省略: 卡住的命令会让 MCP 调用长时间不返回


TOOLS: list[dict[str, Any]] = [  # 新增代码+workspace_tools: 定义 server 暴露给模型的工具列表；若省略: tools/list 无法告诉 agent 有哪些本地能力
    {  # 新增代码+workspace_tools: 定义目录列表工具对象；若省略: 模型无法枚举工作区目录
        "name": "list_dir",  # 新增代码+workspace_tools: MCP 原始工具名；若省略: agent 无法生成 mcp__workspace_tools__list_dir
        "description": "列出工作区内某个目录的直接子项，适合先了解项目结构。",  # 新增代码+workspace_tools: 告诉模型此工具用于看目录；若省略: 模型选择工具时信息不足
        "inputSchema": {  # 新增代码+workspace_tools: 声明 list_dir 参数 schema；若省略: 模型不知道该传入哪些字段
            "type": "object",  # 新增代码+workspace_tools: 声明参数整体是对象；若省略: 工具参数格式不够明确
            "properties": {  # 新增代码+workspace_tools: 列出可用参数字段；若省略: 模型无法看到字段说明
                "path": {"type": "string", "description": "要列出的工作区相对目录，默认 .。"},  # 新增代码+workspace_tools: 定义目录路径参数；若省略: 模型无法指定要查看的目录
                "max_entries": {"type": "integer", "description": "最多返回多少个条目，默认 200。"},  # 新增代码+workspace_tools: 定义最大条目数；若省略: 大目录可能返回过多内容
            },  # 新增代码+workspace_tools: properties 定义结束；若省略: JSON Schema 语法不完整
        },  # 新增代码+workspace_tools: inputSchema 定义结束；若省略: 工具定义不完整
    },  # 新增代码+workspace_tools: list_dir 工具对象结束；若省略: TOOLS 列表语法不完整
    {  # 新增代码+workspace_tools: 定义 glob 文件匹配工具对象；若省略: 模型无法按模式查找文件
        "name": "glob",  # 新增代码+workspace_tools: MCP 原始工具名；若省略: agent 无法生成 mcp__workspace_tools__glob
        "description": "按 glob 模式查找工作区文件，例如 **/*.py 或 docs/*.md，对标 Claude Code 的 Glob。",  # 新增代码+workspace_tools: 告诉模型此工具适合文件发现；若省略: 模型可能继续让用户手动提供文件名
        "inputSchema": {  # 新增代码+workspace_tools: 声明 glob 参数 schema；若省略: 模型不知道该传入 pattern
            "type": "object",  # 新增代码+workspace_tools: 声明参数整体是对象；若省略: 工具参数格式不够明确
            "properties": {  # 新增代码+workspace_tools: 列出 glob 参数字段；若省略: 模型无法看到字段说明
                "pattern": {"type": "string", "description": "工作区相对 glob 模式，默认 **/*。"},  # 新增代码+workspace_tools: 定义匹配模式；若省略: 工具不知道如何筛选文件
                "max_results": {"type": "integer", "description": "最多返回多少个结果，默认 100。"},  # 新增代码+workspace_tools: 定义最大结果数；若省略: 大项目可能返回过多文件
            },  # 新增代码+workspace_tools: properties 定义结束；若省略: JSON Schema 语法不完整
        },  # 新增代码+workspace_tools: inputSchema 定义结束；若省略: 工具定义不完整
    },  # 新增代码+workspace_tools: glob 工具对象结束；若省略: TOOLS 列表语法不完整
    {  # 新增代码+workspace_tools: 定义 grep 内容搜索工具对象；若省略: 模型无法搜索代码或文本内容
        "name": "grep",  # 新增代码+workspace_tools: MCP 原始工具名；若省略: agent 无法生成 mcp__workspace_tools__grep
        "description": "在工作区文件内容中搜索关键词，返回相对路径、行号和命中行，对标 Claude Code 的 Grep。",  # 新增代码+workspace_tools: 告诉模型此工具适合内容搜索；若省略: 模型可能低效逐个读取文件
        "inputSchema": {  # 新增代码+workspace_tools: 声明 grep 参数 schema；若省略: 模型不知道 query/pattern 字段
            "type": "object",  # 新增代码+workspace_tools: 声明参数整体是对象；若省略: 工具参数格式不够明确
            "properties": {  # 新增代码+workspace_tools: 列出 grep 参数字段；若省略: 模型无法看到字段说明
                "query": {"type": "string", "description": "要搜索的文本关键词。"},  # 新增代码+workspace_tools: 定义搜索词；若省略: 工具不知道要找什么
                "pattern": {"type": "string", "description": "限制搜索范围的 glob 模式，默认 **/*。"},  # 新增代码+workspace_tools: 定义文件范围；若省略: 搜索无法限制在特定文件类型
                "case_sensitive": {"type": "boolean", "description": "是否区分大小写，默认 false。"},  # 新增代码+workspace_tools: 定义大小写选项；若省略: 模型无法控制搜索语义
                "max_results": {"type": "integer", "description": "最多返回多少条命中，默认 100。"},  # 新增代码+workspace_tools: 定义最大命中数；若省略: 搜索结果可能过长
            },  # 新增代码+workspace_tools: properties 定义结束；若省略: JSON Schema 语法不完整
            "required": ["query"],  # 新增代码+workspace_tools: 声明 query 必填；若省略: 模型可能调用空搜索
        },  # 新增代码+workspace_tools: inputSchema 定义结束；若省略: 工具定义不完整
    },  # 新增代码+workspace_tools: grep 工具对象结束；若省略: TOOLS 列表语法不完整
    {  # 新增代码+MCP文件工具: 定义 MCP 版读取文件工具对象；若省略: 模型无法通过 workspace_tools 统一读取本地文件
        "name": "read_file",  # 新增代码+MCP文件工具: MCP 原始工具名；若省略: agent 无法生成 mcp__workspace_tools__read_file
        "description": "读取工作区内 UTF-8 文本文档，适合查看代码、配置和说明文件。",  # 新增代码+MCP文件工具: 告诉模型此工具用于只读查看文件；若省略: 模型选择工具时信息不足
        "inputSchema": {  # 新增代码+MCP文件工具: 声明 read_file 参数 schema；若省略: 模型不知道 path/max_chars 字段
            "type": "object",  # 新增代码+MCP文件工具: 声明参数整体是对象；若省略: 工具参数格式不明确
            "properties": {  # 新增代码+MCP文件工具: 列出读取文件参数字段；若省略: 模型无法看到字段说明
                "path": {"type": "string", "description": "要读取的工作区相对文件路径。"},  # 新增代码+MCP文件工具: 定义目标文件路径；若省略: 工具不知道要读取哪个文件
                "max_chars": {"type": "integer", "description": "最多返回多少字符，默认 12000。"},  # 新增代码+MCP文件工具: 定义读取截断上限；若省略: 模型无法控制返回长度
            },  # 新增代码+MCP文件工具: properties 定义结束；若省略: JSON Schema 语法不完整
            "required": ["path"],  # 新增代码+MCP文件工具: 声明 path 必填；若省略: 模型可能调用空读取
        },  # 新增代码+MCP文件工具: inputSchema 定义结束；若省略: 工具定义不完整
    },  # 新增代码+MCP文件工具: read_file 工具对象结束；若省略: TOOLS 列表语法不完整
    {  # 新增代码+MCP文件工具: 定义 MCP 版覆盖写入工具对象；若省略: 模型无法通过 workspace_tools 写已有文件
        "name": "write_file",  # 新增代码+MCP文件工具: MCP 原始工具名；若省略: agent 无法生成 mcp__workspace_tools__write_file
        "description": "覆盖写入工作区内已存在的 UTF-8 文本文档；不会创建缺失文件。",  # 新增代码+MCP文件工具: 告诉模型这是覆盖已有文件的工具；若省略: 模型可能误以为它能安全新建文件
        "inputSchema": {  # 新增代码+MCP文件工具: 声明 write_file 参数 schema；若省略: 模型不知道 path/content 字段
            "type": "object",  # 新增代码+MCP文件工具: 声明参数整体是对象；若省略: 工具参数格式不明确
            "properties": {  # 新增代码+MCP文件工具: 列出覆盖写入参数字段；若省略: 模型无法看到字段说明
                "path": {"type": "string", "description": "要覆盖写入的工作区相对文件路径，文件必须已存在。"},  # 新增代码+MCP文件工具: 定义目标文件路径；若省略: 工具不知道要写哪个文件
                "content": {"type": "string", "description": "要写入文件的完整 UTF-8 文本内容。"},  # 新增代码+MCP文件工具: 定义完整写入内容；若省略: 工具不知道要写入什么
            },  # 新增代码+MCP文件工具: properties 定义结束；若省略: JSON Schema 语法不完整
            "required": ["path", "content"],  # 新增代码+MCP文件工具: 声明 path/content 必填；若省略: 模型可能发起缺参写入
        },  # 新增代码+MCP文件工具: inputSchema 定义结束；若省略: 工具定义不完整
    },  # 新增代码+MCP文件工具: write_file 工具对象结束；若省略: TOOLS 列表语法不完整
    {  # 新增代码+MCP文件工具: 定义 MCP 版新建文件工具对象；若省略: 模型无法通过 workspace_tools 安全创建新文件
        "name": "create_file",  # 新增代码+MCP文件工具: MCP 原始工具名；若省略: agent 无法生成 mcp__workspace_tools__create_file
        "description": "创建工作区内新的 UTF-8 文本文档；如果文件已存在会拒绝覆盖。",  # 新增代码+MCP文件工具: 告诉模型此工具用于安全新建文件；若省略: 模型可能用 write_file 或 edit_file 做不合适的新建操作
        "inputSchema": {  # 新增代码+MCP文件工具: 声明 create_file 参数 schema；若省略: 模型不知道 path/content 字段
            "type": "object",  # 新增代码+MCP文件工具: 声明参数整体是对象；若省略: 工具参数格式不明确
            "properties": {  # 新增代码+MCP文件工具: 列出新建文件参数字段；若省略: 模型无法看到字段说明
                "path": {"type": "string", "description": "要创建的工作区相对文件路径，文件必须不存在。"},  # 新增代码+MCP文件工具: 定义新文件路径；若省略: 工具不知道要创建哪个文件
                "content": {"type": "string", "description": "新文件的完整 UTF-8 文本内容。"},  # 新增代码+MCP文件工具: 定义新文件内容；若省略: 工具不知道新文件写什么
            },  # 新增代码+MCP文件工具: properties 定义结束；若省略: JSON Schema 语法不完整
            "required": ["path", "content"],  # 新增代码+MCP文件工具: 声明 path/content 必填；若省略: 模型可能发起缺参创建
        },  # 新增代码+MCP文件工具: inputSchema 定义结束；若省略: 工具定义不完整
    },  # 新增代码+MCP文件工具: create_file 工具对象结束；若省略: TOOLS 列表语法不完整
    {  # 新增代码+MCP文件操作: 定义 MCP 版复制文件工具对象；若省略: 模型无法通过 workspace_tools 复制文件
        "name": "copy_file",  # 新增代码+MCP文件操作: MCP 原始工具名；若省略: agent 无法生成 mcp__workspace_tools__copy_file
        "description": "复制工作区内的单个文件到新路径；默认不覆盖已有目标，除非显式 overwrite=true。",  # 新增代码+MCP文件操作: 告诉模型复制默认安全不覆盖；若省略: 模型可能误以为复制会自动覆盖
        "inputSchema": {  # 新增代码+MCP文件操作: 声明 copy_file 参数 schema；若省略: 模型不知道 source_path/target_path 字段
            "type": "object",  # 新增代码+MCP文件操作: 声明参数整体是对象；若省略: 工具参数格式不明确
            "properties": {  # 新增代码+MCP文件操作: 列出复制文件参数字段；若省略: 模型无法看到字段说明
                "source_path": {"type": "string", "description": "要复制的工作区相对源文件路径。"},  # 新增代码+MCP文件操作: 定义复制源路径；若省略: 工具不知道复制哪个文件
                "target_path": {"type": "string", "description": "复制后的工作区相对目标文件路径。"},  # 新增代码+MCP文件操作: 定义复制目标路径；若省略: 工具不知道复制到哪里
                "overwrite": {"type": "boolean", "description": "是否允许覆盖已有目标文件，默认 false。"},  # 新增代码+MCP文件操作: 定义覆盖开关；若省略: 模型无法显式处理目标冲突
            },  # 新增代码+MCP文件操作: properties 定义结束；若省略: JSON Schema 语法不完整
            "required": ["source_path", "target_path"],  # 新增代码+MCP文件操作: 声明源路径和目标路径必填；若省略: 模型可能发起缺参复制
        },  # 新增代码+MCP文件操作: inputSchema 定义结束；若省略: 工具定义不完整
    },  # 新增代码+MCP文件操作: copy_file 工具对象结束；若省略: TOOLS 列表语法不完整
    {  # 新增代码+MCP文件操作: 定义 MCP 版移动文件工具对象；若省略: 模型无法通过 workspace_tools 移动或重命名文件
        "name": "move_file",  # 新增代码+MCP文件操作: MCP 原始工具名；若省略: agent 无法生成 mcp__workspace_tools__move_file
        "description": "移动或重命名工作区内的单个文件；默认不覆盖已有目标，除非显式 overwrite=true。",  # 新增代码+MCP文件操作: 告诉模型移动默认安全不覆盖；若省略: 模型可能误以为移动会自动覆盖
        "inputSchema": {  # 新增代码+MCP文件操作: 声明 move_file 参数 schema；若省略: 模型不知道 source_path/target_path 字段
            "type": "object",  # 新增代码+MCP文件操作: 声明参数整体是对象；若省略: 工具参数格式不明确
            "properties": {  # 新增代码+MCP文件操作: 列出移动文件参数字段；若省略: 模型无法看到字段说明
                "source_path": {"type": "string", "description": "要移动的工作区相对源文件路径。"},  # 新增代码+MCP文件操作: 定义移动源路径；若省略: 工具不知道移动哪个文件
                "target_path": {"type": "string", "description": "移动后的工作区相对目标文件路径。"},  # 新增代码+MCP文件操作: 定义移动目标路径；若省略: 工具不知道移动到哪里
                "overwrite": {"type": "boolean", "description": "是否允许覆盖已有目标文件，默认 false。"},  # 新增代码+MCP文件操作: 定义覆盖开关；若省略: 模型无法显式处理目标冲突
            },  # 新增代码+MCP文件操作: properties 定义结束；若省略: JSON Schema 语法不完整
            "required": ["source_path", "target_path"],  # 新增代码+MCP文件操作: 声明源路径和目标路径必填；若省略: 模型可能发起缺参移动
        },  # 新增代码+MCP文件操作: inputSchema 定义结束；若省略: 工具定义不完整
    },  # 新增代码+MCP文件操作: move_file 工具对象结束；若省略: TOOLS 列表语法不完整
    {  # 新增代码+MCP文件操作: 定义 MCP 版删除文件工具对象；若省略: 模型无法通过 workspace_tools 请求受控删除
        "name": "delete_file",  # 新增代码+MCP文件操作: MCP 原始工具名；若省略: agent 无法生成 mcp__workspace_tools__delete_file
        "description": "删除工作区内的单个文件；必须显式传 confirm_delete=true，不删除目录。",  # 新增代码+MCP文件操作: 告诉模型删除需要确认且只处理文件；若省略: 模型可能发起危险或模糊删除
        "inputSchema": {  # 新增代码+MCP文件操作: 声明 delete_file 参数 schema；若省略: 模型不知道 path/confirm_delete 字段
            "type": "object",  # 新增代码+MCP文件操作: 声明参数整体是对象；若省略: 工具参数格式不明确
            "properties": {  # 新增代码+MCP文件操作: 列出删除文件参数字段；若省略: 模型无法看到字段说明
                "path": {"type": "string", "description": "要删除的工作区相对文件路径。"},  # 新增代码+MCP文件操作: 定义删除目标路径；若省略: 工具不知道删除哪个文件
                "confirm_delete": {"type": "boolean", "description": "必须为 true 才会真正删除文件。"},  # 新增代码+MCP文件操作: 定义显式删除确认；若省略: 删除工具缺少二次确认门槛
            },  # 新增代码+MCP文件操作: properties 定义结束；若省略: JSON Schema 语法不完整
            "required": ["path"],  # 新增代码+MCP文件操作: 声明 path 必填；若省略: 模型可能发起空路径删除
        },  # 新增代码+MCP文件操作: inputSchema 定义结束；若省略: 工具定义不完整
    },  # 新增代码+MCP文件操作: delete_file 工具对象结束；若省略: TOOLS 列表语法不完整
    {  # 新增代码+workspace_tools: 定义 PowerShell 执行工具对象；若省略: 模型无法请求运行验证命令
        "name": "run_powershell",  # 新增代码+workspace_tools: MCP 原始工具名；若省略: agent 无法生成 mcp__workspace_tools__run_powershell
        "description": "在工作区目录内执行 PowerShell 命令，适合运行测试、查看环境或做验证；调用前仍由 agent 权限层确认。",  # 新增代码+workspace_tools: 告诉模型命令执行用途和权限边界；若省略: 模型可能误用或不知道可验证
        "inputSchema": {  # 新增代码+workspace_tools: 声明 run_powershell 参数 schema；若省略: 模型不知道 command 字段
            "type": "object",  # 新增代码+workspace_tools: 声明参数整体是对象；若省略: 工具参数格式不够明确
            "properties": {  # 新增代码+workspace_tools: 列出命令工具参数字段；若省略: 模型无法看到字段说明
                "command": {"type": "string", "description": "要执行的 PowerShell 命令。"},  # 新增代码+workspace_tools: 定义命令文本；若省略: 工具没有可执行内容
                "timeout_seconds": {"type": "integer", "description": "最长执行秒数，默认 20，最大 120。"},  # 新增代码+workspace_tools: 定义超时参数；若省略: 模型无法控制长命令
            },  # 新增代码+workspace_tools: properties 定义结束；若省略: JSON Schema 语法不完整
            "required": ["command"],  # 新增代码+workspace_tools: 声明 command 必填；若省略: 模型可能调用空命令
        },  # 新增代码+workspace_tools: inputSchema 定义结束；若省略: 工具定义不完整
    },  # 新增代码+workspace_tools: run_powershell 工具对象结束；若省略: TOOLS 列表语法不完整
    {  # 新增代码+edit_file: 定义精确文件编辑工具对象；若省略: 模型无法请求对标 Claude Code Edit 的受控文本修改
        "name": "edit_file",  # 新增代码+edit_file: MCP 原始工具名；若省略: agent 无法生成 mcp__workspace_tools__edit_file
        "description": "在工作区文本文件中精确替换文本；支持单个 old_text/new_text、多个 edits 批量替换，以及 dry_run diff 预览。",  # 新增代码+edit_file批量预览: 告诉模型此工具既能兼容单次替换也能批量预览；若省略: 模型不知道可以减少多轮调用或先预览风险
        "inputSchema": {  # 新增代码+edit_file批量预览: 声明 edit_file 参数 schema；若省略: 模型不知道 path/old_text/new_text/edits/dry_run 字段
            "type": "object",  # 新增代码+edit_file: 声明参数整体是对象；若省略: 工具参数格式不够明确
            "properties": {  # 新增代码+edit_file: 列出编辑工具参数字段；若省略: 模型无法看到字段说明
                "path": {"type": "string", "description": "要编辑的工作区相对文件路径。"},  # 新增代码+edit_file: 定义目标文件路径；若省略: 工具不知道要改哪个文件
                "old_text": {"type": "string", "description": "要被替换的原文，应该尽量包含足够上下文。"},  # 新增代码+edit_file: 定义原文片段；若省略: 工具无法定位修改位置
                "new_text": {"type": "string", "description": "替换后的新文本，可以为空字符串表示删除。"},  # 新增代码+edit_file: 定义新文本；若省略: 工具不知道要写入什么
                "replace_all": {"type": "boolean", "description": "是否替换所有匹配，默认 false；只有确认要全量替换时才使用。"},  # 新增代码+edit_file: 定义全量替换开关；若省略: 多处相同文本无法显式处理
                "edits": {  # 新增代码+edit_file批量编辑: 定义一次调用里的多段替换数组；若省略: agent 修改同一文件多处内容时仍要多轮工具调用
                    "type": "array",  # 新增代码+edit_file批量编辑: 声明 edits 必须是数组；若省略: 模型不知道可以传多个编辑项
                    "description": "可选的批量编辑数组；每项包含 old_text、new_text，可选 replace_all。",  # 新增代码+edit_file批量编辑: 解释批量编辑结构；若省略: 模型很难正确构造参数
                    "items": {  # 新增代码+edit_file批量编辑: 定义数组里每个编辑项的结构；若省略: JSON Schema 无法约束单项格式
                        "type": "object",  # 新增代码+edit_file批量编辑: 声明每个编辑项必须是对象；若省略: 模型可能传字符串或数组导致工具失败
                        "properties": {  # 新增代码+edit_file批量编辑: 列出单个编辑项允许的字段；若省略: 模型看不到 old_text/new_text 的嵌套位置
                            "old_text": {"type": "string", "description": "这一项要被替换的原文。"},  # 新增代码+edit_file批量编辑: 定义单项原文；若省略: 每个编辑项无法定位修改位置
                            "new_text": {"type": "string", "description": "这一项替换后的新文本。"},  # 新增代码+edit_file批量编辑: 定义单项新文；若省略: 每个编辑项不知道要写入什么
                            "replace_all": {"type": "boolean", "description": "这一项是否替换所有匹配，默认继承顶层 replace_all。"},  # 新增代码+edit_file批量编辑: 允许单项控制全量替换；若省略: 批量编辑里无法细分安全策略
                        },  # 新增代码+edit_file批量编辑: 单项 properties 定义结束；若省略: JSON Schema 语法不完整
                        "required": ["old_text", "new_text"],  # 新增代码+edit_file批量编辑: 声明每个编辑项必须有原文和新文；若省略: 缺字段编辑会到运行时才失败
                    },  # 新增代码+edit_file批量编辑: 单个编辑项 schema 结束；若省略: edits 数组定义不完整
                },  # 新增代码+edit_file批量编辑: edits 参数定义结束；若省略: 批量能力不会暴露给模型
                "dry_run": {"type": "boolean", "description": "为 true 时只返回 diff 预览，不写入文件。"},  # 新增代码+edit_file预览: 定义预览开关；若省略: agent 无法在写文件前先展示修改结果
            },  # 新增代码+edit_file: properties 定义结束；若省略: JSON Schema 语法不完整
            "required": ["path"],  # 新增代码+edit_file批量预览: 只强制 path，允许单次 old_text/new_text 或批量 edits 二选一；若省略: edits 模式会被旧必填项卡住
        },  # 新增代码+edit_file: inputSchema 定义结束；若省略: 工具定义不完整
    },  # 新增代码+edit_file: edit_file 工具对象结束；若省略: TOOLS 列表语法不完整
]  # 新增代码+workspace_tools: TOOLS 列表结束；若省略: Python 语法不完整


def safe_int(value: Any, default: int, minimum: int, maximum: int) -> int:  # 新增代码+workspace_tools: 把模型参数安全转换成整数范围；若省略: max_results 和 timeout 可能收到非法值导致崩溃
    try:  # 新增代码+workspace_tools: 捕获 int 转换异常；若省略: 字符串或对象参数可能让工具失败
        number = int(value)  # 新增代码+workspace_tools: 尝试把输入转成整数；若省略: 无法支持模型传来的数字字符串
    except (TypeError, ValueError):  # 新增代码+workspace_tools: 处理缺失或非数字输入；若省略: 非法参数会抛到底层
        number = default  # 新增代码+workspace_tools: 使用默认值兜底；若省略: 工具无法稳定继续
    return max(minimum, min(number, maximum))  # 新增代码+workspace_tools: 把数字限制在安全范围；若省略: 过大数值可能导致输出爆炸或命令超时过长


def workspace_relative(path: Path) -> str:  # 新增代码+workspace_tools: 把绝对路径转换成工作区相对路径；若省略: 工具输出会暴露冗长绝对路径
    return path.resolve().relative_to(WORKSPACE).as_posix()  # 新增代码+workspace_tools: 返回 POSIX 风格相对路径；若省略: Windows 反斜杠会让模型跨平台处理更困难


def resolve_workspace_path(raw_path: Any) -> Path:  # 新增代码+workspace_tools: 将模型传入路径安全解析到工作区内；若省略: list_dir 可能访问工作区外文件
    text = str(raw_path or ".").strip()  # 新增代码+workspace_tools: 将缺省路径视为当前目录并清理空白；若省略: 空路径会导致语义不清
    candidate = (WORKSPACE / text).resolve()  # 新增代码+workspace_tools: 基于工作区解析目标路径；若省略: 相对路径可能基于错误目录
    try:  # 新增代码+workspace_tools: 检查目标是否仍在工作区内；若省略: 用户可用 ../ 越界访问
        candidate.relative_to(WORKSPACE)  # 新增代码+workspace_tools: 尝试计算相对路径作为安全校验；若省略: 无法确认路径边界
    except ValueError as error:  # 新增代码+workspace_tools: 捕获路径不在工作区内的情况；若省略: 越界访问可能继续执行
        raise RuntimeError("路径必须位于工作区内。") from error  # 新增代码+workspace_tools: 返回清晰安全错误；若省略: 用户不知道为什么被拒绝
    return candidate  # 新增代码+workspace_tools: 返回安全绝对路径；若省略: 调用方拿不到解析结果


def normalize_pattern(raw_pattern: Any) -> str:  # 新增代码+workspace_tools: 规范化并校验 glob 模式；若省略: glob/grep 可能用危险或无效模式
    pattern = str(raw_pattern or "**/*").replace("\\", "/").strip()  # 新增代码+workspace_tools: 缺省搜索全部并统一分隔符；若省略: Windows 反斜杠模式可能不稳定
    pattern = pattern or "**/*"  # 新增代码+workspace_tools: 空字符串兜底为全量模式；若省略: 空模式可能没有结果
    pure = PurePosixPath(pattern)  # 新增代码+workspace_tools: 用 POSIX 路径对象检查模式片段；若省略: 手写分隔符检查更易错
    if pure.is_absolute() or ".." in pure.parts or ":" in pattern:  # 新增代码+workspace_tools: 禁止绝对路径、上级目录和盘符；若省略: glob 可能越过工作区边界
        raise RuntimeError("glob pattern 必须是工作区内的相对模式。")  # 新增代码+workspace_tools: 返回清晰模式错误；若省略: 用户难以修复无效模式
    return pattern  # 新增代码+workspace_tools: 返回安全模式；若省略: 调用方拿不到规范化结果


def iter_glob_matches(pattern: str) -> list[Path]:  # 新增代码+workspace_tools: 根据安全模式查找工作区路径；若省略: glob 和 grep 会重复实现搜索逻辑
    matches = [path for path in WORKSPACE.glob(pattern)]  # 新增代码+workspace_tools: 执行 pathlib glob 搜索；若省略: 无法找到匹配文件
    safe_matches = []  # 新增代码+workspace_tools: 准备保存仍位于工作区内的路径；若省略: 后续无法二次过滤安全边界
    for path in matches:  # 新增代码+workspace_tools: 遍历所有匹配路径；若省略: 无法过滤和排序结果
        try:  # 新增代码+workspace_tools: 逐个确认路径仍在工作区内；若省略: 特殊符号链接可能越界
            path.resolve().relative_to(WORKSPACE)  # 新增代码+workspace_tools: 用 resolve 后路径做边界检查；若省略: 符号链接安全性不足
        except ValueError:  # 新增代码+workspace_tools: 如果路径越界则跳过；若省略: 越界路径可能进入结果
            continue  # 新增代码+workspace_tools: 跳过不安全路径；若省略: 过滤分支无法继续
        safe_matches.append(path)  # 新增代码+workspace_tools: 保存安全路径；若省略: 搜索结果会丢失
    return sorted(safe_matches, key=lambda item: workspace_relative(item))  # 新增代码+workspace_tools: 按相对路径稳定排序；若省略: 输出顺序不稳定影响测试和模型理解


def format_truncation(total: int, shown: int) -> str:  # 新增代码+workspace_tools: 生成截断提示文本；若省略: 用户不知道结果是否完整
    return f"\n... 已截断，仅显示 {shown}/{total} 条结果。" if total > shown else ""  # 新增代码+workspace_tools: 只有实际截断时才提示；若省略: 输出会产生误导或缺少说明


def normalize_edit_operations(arguments: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:  # 新增代码+edit_file批量编辑: 把单次替换和 edits 数组统一成内部编辑列表；若省略: run_edit_file 会同时处理两套参数导致逻辑混乱
    raw_edits = arguments.get("edits")  # 新增代码+edit_file批量编辑: 读取可选批量编辑参数；若省略: 工具无法判断用户是否选择批量模式
    default_replace_all = bool(arguments.get("replace_all", False))  # 新增代码+edit_file批量编辑: 读取顶层 replace_all 默认值；若省略: 批量项无法继承统一替换策略
    if raw_edits is None:  # 新增代码+edit_file批量编辑: 没有 edits 时走旧版单次替换兼容路径；若省略: 旧调用 old_text/new_text 会失效
        old_text = str(arguments.get("old_text", ""))  # 新增代码+edit_file批量编辑: 读取旧版单次替换原文；若省略: 兼容路径无法定位修改位置
        new_text = str(arguments.get("new_text", ""))  # 新增代码+edit_file批量编辑: 读取旧版单次替换新文；若省略: 兼容路径不知道写入内容
        if not old_text:  # 新增代码+edit_file批量编辑: 拒绝空 old_text；若省略: 空字符串会匹配所有位置并破坏文件
            return [], "edit_file 需要非空 old_text 参数。"  # 新增代码+edit_file批量编辑: 返回旧版兼容错误；若省略: 模型难以修正缺参调用
        return [{"old_text": old_text, "new_text": new_text, "replace_all": default_replace_all}], None  # 新增代码+edit_file批量编辑: 把单次替换转成一项列表；若省略: 后续统一应用逻辑拿不到编辑项
    if not isinstance(raw_edits, list) or not raw_edits:  # 新增代码+edit_file批量编辑: 校验 edits 必须是非空数组；若省略: 空批量调用会被误认为有效编辑
        return [], "edit_file 的 edits 参数必须是非空数组。"  # 新增代码+edit_file批量编辑: 返回清楚批量参数错误；若省略: 用户不知道 edits 该怎么传
    operations: list[dict[str, Any]] = []  # 新增代码+edit_file批量编辑: 准备保存规范化后的编辑项；若省略: 无处累积批量替换任务
    for index, raw_edit in enumerate(raw_edits, start=1):  # 新增代码+edit_file批量编辑: 逐项检查批量编辑；若省略: 无法定位具体哪一项参数错误
        if not isinstance(raw_edit, dict):  # 新增代码+edit_file批量编辑: 每个编辑项必须是对象；若省略: 字符串或数组项会在 get 调用时崩溃
            return [], f"edits 第 {index} 项必须是对象。"  # 新增代码+edit_file批量编辑: 返回带序号的错误；若省略: 模型难以修正具体坏项
        old_text = str(raw_edit.get("old_text", ""))  # 新增代码+edit_file批量编辑: 读取当前项原文；若省略: 当前项无法定位修改位置
        new_text = str(raw_edit.get("new_text", ""))  # 新增代码+edit_file批量编辑: 读取当前项新文；若省略: 当前项不知道写入内容
        replace_all = bool(raw_edit.get("replace_all", default_replace_all))  # 新增代码+edit_file批量编辑: 读取当前项全量替换策略并支持继承顶层默认；若省略: 批量项无法单独控制安全行为
        if not old_text:  # 新增代码+edit_file批量编辑: 拒绝当前项空 old_text；若省略: 某个批量项可能破坏整个文件
            return [], f"edits 第 {index} 项需要非空 old_text。"  # 新增代码+edit_file批量编辑: 返回带序号的缺参错误；若省略: 模型不知道哪一项需要修正
        operations.append({"old_text": old_text, "new_text": new_text, "replace_all": replace_all})  # 新增代码+edit_file批量编辑: 保存规范化编辑项；若省略: 该项不会被执行
    return operations, None  # 新增代码+edit_file批量编辑: 返回完整编辑列表且无错误；若省略: run_edit_file 无法继续执行


def apply_edit_operations(original_text: str, operations: list[dict[str, Any]]) -> tuple[str, int, str | None]:  # 新增代码+edit_file批量编辑: 在内存中顺序应用所有替换并统计次数；若省略: 批量编辑无法保证失败时不写半成品
    updated_text = original_text  # 新增代码+edit_file批量编辑: 用原文作为逐步编辑起点；若省略: 后续替换没有可修改文本
    replaced_count = 0  # 新增代码+edit_file批量编辑: 初始化总替换次数；若省略: 工具无法报告本次修改范围
    for index, operation in enumerate(operations, start=1):  # 新增代码+edit_file批量编辑: 按用户给出的顺序逐项替换；若省略: 多段编辑无法执行
        old_text = str(operation["old_text"])  # 新增代码+edit_file批量编辑: 读取当前项原文；若省略: 当前替换无法计算匹配次数
        new_text = str(operation["new_text"])  # 新增代码+edit_file批量编辑: 读取当前项新文；若省略: 当前替换不知道替换结果
        replace_all = bool(operation["replace_all"])  # 新增代码+edit_file批量编辑: 读取当前项是否全量替换；若省略: 多匹配场景无法安全处理
        occurrences = updated_text.count(old_text)  # 新增代码+edit_file批量编辑: 统计当前文本中 old_text 出现次数；若省略: 无法判断没有匹配或多处模糊匹配
        if occurrences == 0:  # 新增代码+edit_file批量编辑: 处理当前项没有命中的情况；若省略: replace 会静默不改导致误判成功
            return updated_text, replaced_count, f"edits 第 {index} 项没有找到 old_text，文件未修改。"  # 新增代码+edit_file批量编辑: 返回失败原因且调用方不会写文件；若省略: 模型不知道需要重新读取上下文
        if occurrences > 1 and not replace_all:  # 新增代码+edit_file批量编辑: 默认拒绝当前项多处匹配；若省略: 批量编辑可能一次误改多个位置
            return updated_text, replaced_count, f"edits 第 {index} 项 old_text 出现 {occurrences} 次，文件未修改；请提供更精确 old_text，或确认后设置 replace_all=true。"  # 新增代码+edit_file批量编辑: 返回安全修正方式；若省略: 模型不知道如何继续
        updated_text = updated_text.replace(old_text, new_text) if replace_all else updated_text.replace(old_text, new_text, 1)  # 新增代码+edit_file批量编辑: 按当前项策略执行内存替换；若省略: 文件内容不会产生预期变化
        replaced_count += occurrences if replace_all else 1  # 新增代码+edit_file批量编辑: 累加实际替换次数；若省略: 批量返回的替换次数会不准确
    return updated_text, replaced_count, None  # 新增代码+edit_file批量编辑: 返回最终文本、总次数和无错误标记；若省略: 调用方拿不到编辑结果


def build_edit_diff(relative_path: str, original_text: str, updated_text: str) -> str:  # 新增代码+edit_file预览: 生成 dry_run 使用的 unified diff 文本；若省略: 预览模式只能说会修改但不能展示改哪里
    diff_lines = difflib.unified_diff(  # 新增代码+edit_file预览: 调用标准库生成逐行差异；若省略: 需要手写容易出错的 diff 算法
        original_text.splitlines(),  # 新增代码+edit_file预览: 把原文按行传给 diff；若省略: diff 无法显示删除行
        updated_text.splitlines(),  # 新增代码+edit_file预览: 把新文按行传给 diff；若省略: diff 无法显示新增行
        fromfile=f"{relative_path} (before)",  # 新增代码+edit_file预览: 标记 diff 左侧文件名；若省略: 用户不知道减号代表哪个版本
        tofile=f"{relative_path} (after)",  # 新增代码+edit_file预览: 标记 diff 右侧文件名；若省略: 用户不知道加号代表哪个版本
        lineterm="",  # 新增代码+edit_file预览: 避免 difflib 额外插入换行符；若省略: diff 输出会出现多余空行
    )  # 新增代码+edit_file预览: unified_diff 调用结束；若省略: Python 语法不完整
    return "\n".join(diff_lines)[:12000]  # 新增代码+edit_file预览: 合并并截断 diff，防止大文件预览撑爆上下文；若省略: 预览结果可能过长


def run_list_dir(arguments: dict[str, Any]) -> str:  # 新增代码+workspace_tools: 实现 list_dir 工具；若省略: 目录枚举能力无法执行
    target = resolve_workspace_path(arguments.get("path", "."))  # 新增代码+workspace_tools: 安全解析目标目录；若省略: 可能访问工作区外路径
    max_entries = safe_int(arguments.get("max_entries"), 200, 1, 1000)  # 新增代码+workspace_tools: 读取并限制最大条目数；若省略: 大目录输出可能过长
    if not target.exists():  # 新增代码+workspace_tools: 检查目录是否存在；若省略: iterdir 会抛出底层异常
        return f"目录不存在：{workspace_relative(target.parent)}/{target.name}"  # 新增代码+workspace_tools: 返回可读不存在错误；若省略: 模型难以向用户解释失败
    if not target.is_dir():  # 新增代码+workspace_tools: 检查目标是否为目录；若省略: 文件路径会触发不清晰错误
        return f"不是目录：{workspace_relative(target)}"  # 新增代码+workspace_tools: 返回可读类型错误；若省略: 用户不知道为什么不能列出
    entries = sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))  # 新增代码+workspace_tools: 目录优先并按名称排序；若省略: 输出顺序不稳定且不易扫描
    visible_entries = entries[:max_entries]  # 新增代码+workspace_tools: 根据最大条目数截断；若省略: 大目录会输出过多内容
    lines = [f"{entry.name}/" if entry.is_dir() else entry.name for entry in visible_entries]  # 新增代码+workspace_tools: 目录名追加斜杠便于识别；若省略: 模型难以区分文件和目录
    if not lines:  # 新增代码+workspace_tools: 处理空目录；若省略: 空字符串会让模型误以为工具失败
        return "目录为空。"  # 新增代码+workspace_tools: 返回清楚空目录提示；若省略: 用户不知道是否真的查过
    return "\n".join(lines) + format_truncation(len(entries), len(visible_entries))  # 新增代码+workspace_tools: 返回目录列表和必要截断提示；若省略: 工具结果无法回填给模型


def run_glob(arguments: dict[str, Any]) -> str:  # 新增代码+workspace_tools: 实现 glob 工具；若省略: 模式查找文件能力无法执行
    pattern = normalize_pattern(arguments.get("pattern", "**/*"))  # 新增代码+workspace_tools: 读取并校验 glob 模式；若省略: 模式可能越界或为空
    max_results = safe_int(arguments.get("max_results"), DEFAULT_MAX_RESULTS, 1, 1000)  # 新增代码+workspace_tools: 读取并限制最大结果数；若省略: 大项目会输出过多路径
    matches = [path for path in iter_glob_matches(pattern) if path.is_file()]  # 新增代码+workspace_tools: 只保留文件结果；若省略: grep 前置搜索和模型阅读会混入目录
    visible_matches = matches[:max_results]  # 新增代码+workspace_tools: 截断到允许数量；若省略: 输出可能过长
    if not visible_matches:  # 新增代码+workspace_tools: 处理没有匹配文件；若省略: 空输出容易被误解为工具失败
        return f"没有找到匹配文件：{pattern}"  # 新增代码+workspace_tools: 返回清楚无结果提示；若省略: 模型无法向用户解释
    lines = [workspace_relative(path) for path in visible_matches]  # 新增代码+workspace_tools: 转换为工作区相对路径；若省略: 输出会暴露冗长绝对路径
    return "\n".join(lines) + format_truncation(len(matches), len(visible_matches))  # 新增代码+workspace_tools: 返回匹配路径和截断提示；若省略: 工具结果无法回填给模型


def file_is_small_enough(path: Path) -> bool:  # 新增代码+workspace_tools: 判断文件是否适合 grep 读取；若省略: 大文件可能拖慢工具
    try:  # 新增代码+workspace_tools: 捕获 stat 异常；若省略: 权限或临时文件问题会中断整个 grep
        return path.stat().st_size <= MAX_FILE_BYTES  # 新增代码+workspace_tools: 只读取不超过限制的文件；若省略: 大文件会占用过多内存
    except OSError:  # 新增代码+workspace_tools: 处理文件状态读取失败；若省略: 单个坏文件会终止搜索
        return False  # 新增代码+workspace_tools: 状态不可读时跳过文件；若省略: grep 健壮性不足


def run_grep(arguments: dict[str, Any]) -> str:  # 新增代码+workspace_tools: 实现 grep 工具；若省略: 工作区内容搜索能力无法执行
    query = str(arguments.get("query", ""))  # 新增代码+workspace_tools: 读取搜索关键词；若省略: 工具不知道要搜索什么
    if not query:  # 新增代码+workspace_tools: 拒绝空搜索词；若省略: 空字符串会匹配所有行造成输出爆炸
        return "grep 需要 query 参数。"  # 新增代码+workspace_tools: 返回清楚参数错误；若省略: 模型难以修正调用
    pattern = normalize_pattern(arguments.get("pattern", "**/*"))  # 新增代码+workspace_tools: 读取并校验搜索范围；若省略: grep 无法限制文件集合
    case_sensitive = bool(arguments.get("case_sensitive", False))  # 新增代码+workspace_tools: 读取大小写选项；若省略: 用户无法控制搜索语义
    max_results = safe_int(arguments.get("max_results"), DEFAULT_MAX_RESULTS, 1, 1000)  # 新增代码+workspace_tools: 读取并限制最大命中数；若省略: 命中过多时会撑爆上下文
    needle = query if case_sensitive else query.lower()  # 新增代码+workspace_tools: 根据大小写选项准备比较文本；若省略: 搜索行为无法区分大小写模式
    results: list[str] = []  # 新增代码+workspace_tools: 准备保存命中结果行；若省略: 无处累积搜索结果
    total_matches = 0  # 新增代码+workspace_tools: 记录总命中数量用于截断提示；若省略: 用户不知道是否还有更多结果
    for path in iter_glob_matches(pattern):  # 新增代码+workspace_tools: 遍历匹配范围内路径；若省略: grep 没有文件可搜索
        if not path.is_file() or not file_is_small_enough(path):  # 新增代码+workspace_tools: 跳过目录和过大文件；若省略: 搜索会失败或过慢
            continue  # 新增代码+workspace_tools: 继续处理下一个路径；若省略: 过滤逻辑无法生效
        text = path.read_text(encoding="utf-8", errors="replace")  # 新增代码+workspace_tools: 以 UTF-8 容错读取文本；若省略: 中文文件或非 UTF-8 字节可能让 grep 崩溃
        for line_number, line in enumerate(text.splitlines(), start=1):  # 新增代码+workspace_tools: 按行搜索并保留行号；若省略: 命中结果无法定位
            haystack = line if case_sensitive else line.lower()  # 新增代码+workspace_tools: 根据大小写选项准备当前行；若省略: 大小写搜索不准确
            if needle not in haystack:  # 新增代码+workspace_tools: 跳过不包含关键词的行；若省略: 每一行都会被误认为命中
                continue  # 新增代码+workspace_tools: 继续下一行；若省略: 非命中行会进入结果
            total_matches += 1  # 新增代码+workspace_tools: 统计一次真实命中；若省略: 截断提示数量不准确
            if len(results) < max_results:  # 新增代码+workspace_tools: 只保存允许范围内结果；若省略: max_results 不生效
                results.append(f"{workspace_relative(path)}:{line_number}: {line.strip()}")  # 新增代码+workspace_tools: 保存相对路径、行号和命中行；若省略: 模型无法定位结果来源
    if not results:  # 新增代码+workspace_tools: 处理没有命中；若省略: 空输出容易被误解为工具失败
        return f"没有找到包含 `{query}` 的内容。"  # 新增代码+workspace_tools: 返回清楚无结果提示；若省略: 模型无法向用户解释
    return "\n".join(results) + format_truncation(total_matches, len(results))  # 新增代码+workspace_tools: 返回命中结果和截断提示；若省略: grep 结果无法回填给模型


def run_read_file(arguments: dict[str, Any]) -> str:  # 新增代码+MCP文件工具: 实现 MCP 版只读文件工具；若省略: read_file schema 存在但无法执行
    target = resolve_workspace_path(arguments.get("path", ""))  # 新增代码+MCP文件工具: 安全解析目标文件路径；若省略: 读取可能越过工作区边界
    max_chars = safe_int(arguments.get("max_chars"), DEFAULT_READ_MAX_CHARS, 1, 120000)  # 新增代码+MCP文件工具: 读取并限制最大返回字符数；若省略: 大文件内容可能撑爆模型上下文
    if not target.exists():  # 新增代码+MCP文件工具: 检查目标文件是否存在；若省略: read_text 会抛出底层异常
        return f"文件不存在：{workspace_relative(target.parent)}/{target.name}"  # 新增代码+MCP文件工具: 返回可读不存在错误；若省略: 模型难以解释读取失败
    if not target.is_file():  # 新增代码+MCP文件工具: 拒绝目录或特殊路径；若省略: 读取目录会触发不清晰错误
        return f"不是文件：{workspace_relative(target)}"  # 新增代码+MCP文件工具: 返回可读类型错误；若省略: 用户不知道为什么不能读取
    if not file_is_small_enough(target):  # 新增代码+MCP文件工具: 拒绝超过安全上限的文件；若省略: 过大文件会拖慢工具并撑爆上下文
        return f"文件过大，未读取：{workspace_relative(target)}"  # 新增代码+MCP文件工具: 返回清楚的大文件提示；若省略: 模型不知道为什么没有内容
    text = target.read_text(encoding="utf-8", errors="replace")  # 新增代码+MCP文件工具: 以 UTF-8 容错读取文本；若省略: 中文文件或异常字节可能让工具崩溃
    if not text:  # 新增代码+MCP文件工具: 处理空文件；若省略: 空字符串容易被误解为工具失败
        return "文件为空。"  # 新增代码+MCP文件工具: 明确说明文件存在但没有内容；若省略: 模型无法区分空文件和无返回
    visible_text = text[:max_chars]  # 新增代码+MCP文件工具: 按 max_chars 截断返回内容；若省略: max_chars 参数不会生效
    if len(text) > max_chars:  # 新增代码+MCP文件工具: 检查内容是否被截断；若省略: 用户不知道读取结果不完整
        return f"{visible_text}\n... 已截断，仅显示前 {max_chars}/{len(text)} 个字符。"  # 新增代码+MCP文件工具: 返回截断内容和说明；若省略: 模型可能把片段当完整文件
    return visible_text  # 新增代码+MCP文件工具: 返回完整文件文本；若省略: 读取工具没有结果


def run_write_file(arguments: dict[str, Any]) -> str:  # 新增代码+MCP文件工具: 实现 MCP 版覆盖写入已有文件工具；若省略: write_file schema 存在但无法执行
    target = resolve_workspace_path(arguments.get("path", ""))  # 新增代码+MCP文件工具: 安全解析目标文件路径；若省略: 写入可能越过工作区边界
    content = str(arguments.get("content", ""))  # 新增代码+MCP文件工具: 读取要写入的完整文本；若省略: 工具不知道写入内容
    if not target.exists():  # 新增代码+MCP文件工具: 覆盖写入前确认文件已存在；若省略: write_file 可能意外创建新文件
        return f"文件不存在：{workspace_relative(target.parent)}/{target.name}；如需新建请使用 create_file。"  # 新增代码+MCP文件工具: 返回缺失文件和正确工具提示；若省略: 模型不知道应改用 create_file
    if not target.is_file():  # 新增代码+MCP文件工具: 拒绝覆盖目录或特殊路径；若省略: 目录写入会触发不清晰错误
        return f"不是文件：{workspace_relative(target)}"  # 新增代码+MCP文件工具: 返回可读类型错误；若省略: 用户不知道为什么不能写入
    target.write_text(content, encoding="utf-8")  # 新增代码+MCP文件工具: 用 UTF-8 覆盖写入目标文件；若省略: 写入结果不会落盘
    return f"已写入：{workspace_relative(target)}\n字符数：{len(content)}"  # 新增代码+MCP文件工具: 返回写入路径和字符数；若省略: 模型无法向用户确认写入范围


def run_create_file(arguments: dict[str, Any]) -> str:  # 新增代码+MCP文件工具: 实现 MCP 版安全创建新文件工具；若省略: create_file schema 存在但无法执行
    target = resolve_workspace_path(arguments.get("path", ""))  # 新增代码+MCP文件工具: 安全解析新文件路径；若省略: 创建可能越过工作区边界
    content = str(arguments.get("content", ""))  # 新增代码+MCP文件工具: 读取新文件完整文本；若省略: 工具不知道新文件内容
    if target.exists():  # 新增代码+MCP文件工具: 创建前确认目标不存在；若省略: create_file 可能误覆盖已有文件
        return f"文件已存在：{workspace_relative(target)}；如需修改请使用 write_file 或 edit_file。"  # 新增代码+MCP文件工具: 返回拒绝覆盖和正确工具提示；若省略: 模型不知道下一步该用哪个工具
    if target.parent.exists() and not target.parent.is_dir():  # 新增代码+MCP文件工具: 检查父路径不能是文件；若省略: mkdir 会抛出底层异常
        return f"父路径不是目录：{workspace_relative(target.parent)}"  # 新增代码+MCP文件工具: 返回可读父路径错误；若省略: 用户难以理解创建失败原因
    target.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+MCP文件工具: 自动创建缺失父目录；若省略: 嵌套路径新建文件会失败
    target.write_text(content, encoding="utf-8")  # 新增代码+MCP文件工具: 用 UTF-8 写入新文件内容；若省略: 文件会存在但没有期望内容
    return f"已创建：{workspace_relative(target)}\n字符数：{len(content)}"  # 新增代码+MCP文件工具: 返回新建路径和字符数；若省略: 模型无法向用户确认创建结果


def run_copy_file(arguments: dict[str, Any]) -> str:  # 新增代码+MCP文件操作: 实现 MCP 版复制文件工具；若省略: copy_file schema 存在但无法执行
    source = resolve_workspace_path(arguments.get("source_path", ""))  # 新增代码+MCP文件操作: 安全解析源文件路径；若省略: 复制可能越过工作区边界
    target = resolve_workspace_path(arguments.get("target_path", ""))  # 新增代码+MCP文件操作: 安全解析目标文件路径；若省略: 复制目标可能越过工作区边界
    overwrite = bool(arguments.get("overwrite", False))  # 新增代码+MCP文件操作: 读取是否允许覆盖已有目标；若省略: 目标冲突无法由模型显式控制
    if not source.exists():  # 新增代码+MCP文件操作: 检查源文件是否存在；若省略: copy2 会抛出底层异常
        return f"源文件不存在：{workspace_relative(source.parent)}/{source.name}"  # 新增代码+MCP文件操作: 返回可读源文件缺失错误；若省略: 模型难以解释复制失败
    if not source.is_file():  # 新增代码+MCP文件操作: 只允许复制单个文件；若省略: 目录复制可能产生不可控范围
        return f"源路径不是文件：{workspace_relative(source)}"  # 新增代码+MCP文件操作: 返回源路径类型错误；若省略: 用户不知道为什么不能复制
    if target.exists() and not overwrite:  # 新增代码+MCP文件操作: 默认拒绝覆盖已有目标；若省略: copy_file 可能误覆盖用户文件
        return f"目标已存在，未复制：{workspace_relative(target)}；如需覆盖请设置 overwrite=true。"  # 新增代码+MCP文件操作: 返回覆盖冲突和修正方式；若省略: 模型不知道下一步怎么处理
    if target.exists() and not target.is_file():  # 新增代码+MCP文件操作: 即使允许覆盖也拒绝覆盖目录；若省略: 目录目标会触发危险或不清晰行为
        return f"目标路径不是文件：{workspace_relative(target)}"  # 新增代码+MCP文件操作: 返回目标类型错误；若省略: 用户难以理解复制失败原因
    if target.parent.exists() and not target.parent.is_dir():  # 新增代码+MCP文件操作: 检查目标父路径必须是目录；若省略: mkdir/copy2 会抛出底层异常
        return f"目标父路径不是目录：{workspace_relative(target.parent)}"  # 新增代码+MCP文件操作: 返回父路径类型错误；若省略: 模型难以解释失败原因
    target.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+MCP文件操作: 自动创建缺失父目录；若省略: 复制到嵌套路径会失败
    shutil.copy2(source, target)  # 新增代码+MCP文件操作: 执行保留元数据的文件复制；若省略: 文件不会真正复制
    return f"已复制：{workspace_relative(source)} -> {workspace_relative(target)}"  # 新增代码+MCP文件操作: 返回源路径和目标路径；若省略: 模型无法确认复制结果


def run_move_file(arguments: dict[str, Any]) -> str:  # 新增代码+MCP文件操作: 实现 MCP 版移动或重命名文件工具；若省略: move_file schema 存在但无法执行
    source = resolve_workspace_path(arguments.get("source_path", ""))  # 新增代码+MCP文件操作: 安全解析源文件路径；若省略: 移动可能越过工作区边界
    target = resolve_workspace_path(arguments.get("target_path", ""))  # 新增代码+MCP文件操作: 安全解析目标文件路径；若省略: 移动目标可能越过工作区边界
    overwrite = bool(arguments.get("overwrite", False))  # 新增代码+MCP文件操作: 读取是否允许覆盖已有目标；若省略: 目标冲突无法由模型显式控制
    if source == target:  # 新增代码+MCP文件操作: 处理源路径和目标路径相同；若省略: 同路径移动可能产生无意义操作
        return "源路径和目标路径相同，未移动。"  # 新增代码+MCP文件操作: 返回清楚无操作提示；若省略: 用户可能误以为发生了移动
    if not source.exists():  # 新增代码+MCP文件操作: 检查源文件是否存在；若省略: move 会抛出底层异常
        return f"源文件不存在：{workspace_relative(source.parent)}/{source.name}"  # 新增代码+MCP文件操作: 返回可读源文件缺失错误；若省略: 模型难以解释移动失败
    if not source.is_file():  # 新增代码+MCP文件操作: 只允许移动单个文件；若省略: 目录移动可能造成更大范围副作用
        return f"源路径不是文件：{workspace_relative(source)}"  # 新增代码+MCP文件操作: 返回源路径类型错误；若省略: 用户不知道为什么不能移动
    if target.exists() and not overwrite:  # 新增代码+MCP文件操作: 默认拒绝覆盖已有目标；若省略: move_file 可能误覆盖用户文件
        return f"目标已存在，未移动：{workspace_relative(target)}；如需覆盖请设置 overwrite=true。"  # 新增代码+MCP文件操作: 返回覆盖冲突和修正方式；若省略: 模型不知道下一步怎么处理
    if target.exists() and not target.is_file():  # 新增代码+MCP文件操作: 即使允许覆盖也拒绝覆盖目录；若省略: 目录目标会触发危险或不清晰行为
        return f"目标路径不是文件：{workspace_relative(target)}"  # 新增代码+MCP文件操作: 返回目标类型错误；若省略: 用户难以理解移动失败原因
    if target.parent.exists() and not target.parent.is_dir():  # 新增代码+MCP文件操作: 检查目标父路径必须是目录；若省略: mkdir/move 会抛出底层异常
        return f"目标父路径不是目录：{workspace_relative(target.parent)}"  # 新增代码+MCP文件操作: 返回父路径类型错误；若省略: 模型难以解释失败原因
    target.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+MCP文件操作: 自动创建缺失父目录；若省略: 移动到嵌套路径会失败
    if target.exists() and overwrite:  # 新增代码+MCP文件操作: 覆盖模式下先删除已有目标文件；若省略: Windows 上 move 覆盖行为可能不稳定
        target.unlink()  # 新增代码+MCP文件操作: 删除已有目标文件以便移动覆盖；若省略: 覆盖移动可能失败或表现不一致
    shutil.move(str(source), str(target))  # 新增代码+MCP文件操作: 执行文件移动或重命名；若省略: 文件不会真正移动
    return f"已移动：{workspace_relative(source)} -> {workspace_relative(target)}"  # 新增代码+MCP文件操作: 返回源路径和目标路径；若省略: 模型无法确认移动结果


def run_delete_file(arguments: dict[str, Any]) -> str:  # 新增代码+MCP文件操作: 实现 MCP 版受控删除文件工具；若省略: delete_file schema 存在但无法执行
    target = resolve_workspace_path(arguments.get("path", ""))  # 新增代码+MCP文件操作: 安全解析删除目标路径；若省略: 删除可能越过工作区边界
    confirm_delete = bool(arguments.get("confirm_delete", False))  # 新增代码+MCP文件操作: 读取显式删除确认参数；若省略: 删除操作缺少二次安全门槛
    if not confirm_delete:  # 新增代码+MCP文件操作: 没有确认参数时拒绝删除；若省略: 模型一次误调用就可能删除文件
        return "delete_file 需要 confirm_delete=true 才会删除文件，文件未修改。"  # 新增代码+MCP文件操作: 返回明确确认要求；若省略: 模型不知道需要怎样重新调用
    if not target.exists():  # 新增代码+MCP文件操作: 检查删除目标是否存在；若省略: unlink 会抛出底层异常
        return f"文件不存在：{workspace_relative(target.parent)}/{target.name}"  # 新增代码+MCP文件操作: 返回可读缺失错误；若省略: 用户难以理解删除失败
    if not target.is_file():  # 新增代码+MCP文件操作: 只允许删除单个文件，不删除目录；若省略: 删除范围可能不可控
        return f"不是文件：{workspace_relative(target)}"  # 新增代码+MCP文件操作: 返回目录或特殊路径错误；若省略: 用户不知道为什么拒绝删除
    target.unlink()  # 新增代码+MCP文件操作: 真正删除目标文件；若省略: delete_file 会只返回文本不产生效果
    return f"已删除：{workspace_relative(target)}"  # 新增代码+MCP文件操作: 返回删除路径；若省略: 模型无法确认删除结果


def run_powershell(arguments: dict[str, Any]) -> str:  # 新增代码+workspace_tools: 实现 PowerShell 命令执行工具；若省略: agent 无法像 Claude Code 一样请求验证命令
    command = str(arguments.get("command", "")).strip()  # 新增代码+workspace_tools: 读取命令文本并去空白；若省略: 空命令或非字符串参数会不稳定
    if not command:  # 新增代码+workspace_tools: 拒绝空命令；若省略: PowerShell 会启动但不做事造成困惑
        return "run_powershell 需要 command 参数。"  # 新增代码+workspace_tools: 返回清楚参数错误；若省略: 模型难以修正调用
    executable = shutil.which("powershell") or shutil.which("pwsh")  # 新增代码+workspace_tools: 查找 Windows PowerShell 或 PowerShell Core；若省略: 命令执行依赖硬编码路径
    if executable is None:  # 新增代码+workspace_tools: 处理环境没有 PowerShell 的情况；若省略: subprocess 会抛出底层找不到文件异常
        return "PowerShell 不可用：没有找到 powershell 或 pwsh。"  # 新增代码+workspace_tools: 返回可读环境错误；若省略: 用户不知道为什么命令不能执行
    timeout_seconds = safe_int(arguments.get("timeout_seconds"), DEFAULT_COMMAND_TIMEOUT_SECONDS, 1, 120)  # 新增代码+workspace_tools: 读取并限制命令超时；若省略: 命令可能无限运行
    try:  # 新增代码+workspace_tools: 捕获命令超时和执行异常；若省略: 命令失败会杀死 MCP server
        completed = subprocess.run(  # 新增代码+workspace_tools: 启动 PowerShell 并等待完成；若省略: 命令不会真正执行
            [executable, "-NoProfile", "-NonInteractive", "-Command", command],  # 新增代码+workspace_tools: 使用非交互参数执行用户命令；若省略: 命令可能读取配置或等待交互
            cwd=str(WORKSPACE),  # 新增代码+workspace_tools: 限定命令工作目录为工作区；若省略: 命令可能在不可预期目录运行
            capture_output=True,  # 新增代码+workspace_tools: 捕获 stdout/stderr 返回给模型；若省略: 命令输出会丢失
            text=True,  # 新增代码+workspace_tools: 使用文本模式处理输出；若省略: 需要手动解码 bytes
            encoding="utf-8",  # 新增代码+workspace_tools: 优先按 UTF-8 解码输出；若省略: 中文输出可能乱码
            errors="replace",  # 新增代码+workspace_tools: 遇到异常字节时替换而不是崩溃；若省略: 非 UTF-8 输出可能中断工具
            timeout=timeout_seconds,  # 新增代码+workspace_tools: 应用超时限制；若省略: 卡住命令会一直等待
        )  # 新增代码+workspace_tools: subprocess.run 调用结束；若省略: Python 语法不完整
    except subprocess.TimeoutExpired:  # 新增代码+workspace_tools: 处理命令超时；若省略: 超时异常会杀死 server
        return f"PowerShell 命令超时，已超过 {timeout_seconds} 秒。"  # 新增代码+workspace_tools: 返回可读超时结果；若省略: 用户不知道命令为什么没有输出
    stdout = completed.stdout.strip()  # 新增代码+workspace_tools: 清理标准输出边缘空白；若省略: 输出展示会有多余空行
    stderr = completed.stderr.strip()  # 新增代码+workspace_tools: 清理错误输出边缘空白；若省略: 错误展示会有多余空行
    parts = [f"exit_code: {completed.returncode}"]  # 新增代码+workspace_tools: 首行报告退出码；若省略: 模型无法判断命令是否成功
    if stdout:  # 新增代码+workspace_tools: 只有存在 stdout 时才添加区块；若省略: 输出会出现空 stdout 区块
        parts.append("stdout:\n" + stdout[:12000])  # 新增代码+workspace_tools: 添加并截断标准输出；若省略: 成功命令结果无法返回或过长
    if stderr:  # 新增代码+workspace_tools: 只有存在 stderr 时才添加区块；若省略: 输出会出现空 stderr 区块
        parts.append("stderr:\n" + stderr[:12000])  # 新增代码+workspace_tools: 添加并截断错误输出；若省略: 失败原因可能丢失
    return "\n\n".join(parts)  # 新增代码+workspace_tools: 合并命令执行结果；若省略: 工具没有返回文本


def run_edit_file(arguments: dict[str, Any]) -> str:  # 新增代码+edit_file: 实现精确文本替换工具；若省略: edit_file schema 存在但无法执行
    target = resolve_workspace_path(arguments.get("path", ""))  # 新增代码+edit_file: 安全解析目标文件路径；若省略: 编辑可能越过工作区边界
    dry_run = bool(arguments.get("dry_run", False))  # 新增代码+edit_file预览: 读取是否只预览不写入；若省略: agent 无法先展示 diff 再决定是否真正修改
    operations, operation_error = normalize_edit_operations(arguments)  # 新增代码+edit_file批量编辑: 统一解析单次和批量编辑参数；若省略: 新旧参数模式会互相冲突
    if operation_error is not None:  # 新增代码+edit_file批量编辑: 如果参数规范化失败则提前返回；若省略: 后续可能用空编辑列表误判成功
        return operation_error  # 新增代码+edit_file批量编辑: 把可读错误交回模型；若省略: 用户不知道如何修正参数
    if not target.exists():  # 新增代码+edit_file: 检查目标文件是否存在；若省略: read_text 会抛出底层异常
        return f"文件不存在：{workspace_relative(target.parent)}/{target.name}"  # 新增代码+edit_file: 返回可读不存在错误；若省略: 用户不知道哪个文件缺失
    if not target.is_file():  # 新增代码+edit_file: 拒绝目录或特殊路径；若省略: 目录编辑会触发不清晰错误
        return f"不是文件：{workspace_relative(target)}"  # 新增代码+edit_file: 返回可读类型错误；若省略: 模型难以解释失败
    original_text = target.read_text(encoding="utf-8")  # 新增代码+edit_file: 读取原始 UTF-8 文本；若省略: 工具无法比较和替换内容
    updated_text, replaced_count, edit_error = apply_edit_operations(original_text, operations)  # 新增代码+edit_file批量编辑: 先在内存中应用所有替换；若省略: 批量失败时可能写入半成品
    if edit_error is not None:  # 新增代码+edit_file批量编辑: 如果任一替换失败则拒绝整次写入；若省略: 用户可能得到部分修改后的文件
        return edit_error  # 新增代码+edit_file批量编辑: 返回失败原因且不写文件；若省略: 模型无法知道哪一项需要修正
    if updated_text == original_text:  # 新增代码+edit_file: 处理新旧文本相同导致无变化；若省略: 工具可能报告成功但文件没变
        return "替换后内容没有变化，文件未修改。"  # 新增代码+edit_file: 返回清楚无变化提示；若省略: 用户会误以为发生了有效编辑
    relative_path = workspace_relative(target)  # 新增代码+edit_file预览: 提前计算相对路径用于写入结果和 diff 标题；若省略: 返回信息会重复计算且不清晰
    if dry_run:  # 新增代码+edit_file预览: 预览模式只返回 diff，不触碰真实文件；若省略: dry_run 参数不会生效
        diff_text = build_edit_diff(relative_path, original_text, updated_text)  # 新增代码+edit_file预览: 生成本次预期修改的 diff；若省略: 用户看不到具体将改哪些行
        return f"预览模式：文件未修改。\n目标文件：{relative_path}\n预计替换次数：{replaced_count}\n{diff_text}"  # 新增代码+edit_file预览: 返回预览说明、目标和差异；若省略: 模型无法向用户确认修改范围
    target.write_text(updated_text, encoding="utf-8")  # 新增代码+edit_file: 将更新后的文本写回文件；若省略: 编辑结果不会持久化
    return f"已修改：{relative_path}\n替换次数：{replaced_count}"  # 新增代码+edit_file批量编辑: 返回文件路径和总替换次数；若省略: 模型无法向用户确认具体结果


def tool_result(text: str) -> dict[str, Any]:  # 新增代码+workspace_tools: 把普通文本包装成 MCP content 结果；若省略: 每个工具都要重复构造返回结构
    return {"content": [{"type": "text", "text": text}]}  # 新增代码+workspace_tools: 返回 MCP text content 格式；若省略: McpStdioClient 无法提取工具文本


def make_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:  # 新增代码+workspace_tools: 构造 JSON-RPC 成功响应；若省略: handle_message 会重复写响应结构
    return {"jsonrpc": "2.0", "id": request_id, "result": result}  # 新增代码+workspace_tools: 返回标准成功响应；若省略: client 无法匹配请求结果


def make_error(request_id: Any, code: int, message: str) -> dict[str, Any]:  # 新增代码+workspace_tools: 构造 JSON-RPC 错误响应；若省略: 协议错误无法清楚返回
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}  # 新增代码+workspace_tools: 返回标准错误对象；若省略: client 无法看到失败原因


def handle_tools_call(params: dict[str, Any]) -> dict[str, Any]:  # 新增代码+workspace_tools: 分发 MCP tools/call 到具体工具函数；若省略: server 只能列工具不能执行
    name = str(params.get("name", ""))  # 新增代码+workspace_tools: 读取原始工具名；若省略: 无法知道用户要调用哪个工具
    arguments = params.get("arguments", {})  # 新增代码+workspace_tools: 读取工具参数；若省略: 工具函数拿不到输入
    if not isinstance(arguments, dict):  # 新增代码+workspace_tools: 确保参数是对象；若省略: 工具主体可能在非字典上调用 get 崩溃
        arguments = {}  # 新增代码+workspace_tools: 非对象参数兜底为空字典；若省略: 参数错误会更难读
    if name == "list_dir":  # 新增代码+workspace_tools: 处理目录列表工具；若省略: list_dir 调用会变成未知工具
        return tool_result(run_list_dir(arguments))  # 新增代码+workspace_tools: 执行 list_dir 并包装结果；若省略: 目录列表不会返回给 agent
    if name == "glob":  # 新增代码+workspace_tools: 处理 glob 工具；若省略: glob 调用会变成未知工具
        return tool_result(run_glob(arguments))  # 新增代码+workspace_tools: 执行 glob 并包装结果；若省略: 文件匹配结果不会返回给 agent
    if name == "grep":  # 新增代码+workspace_tools: 处理 grep 工具；若省略: grep 调用会变成未知工具
        return tool_result(run_grep(arguments))  # 新增代码+workspace_tools: 执行 grep 并包装结果；若省略: 内容搜索结果不会返回给 agent
    if name == "read_file":  # 新增代码+MCP文件工具: 处理 MCP 版读取文件工具；若省略: read_file 调用会变成未知工具
        return tool_result(run_read_file(arguments))  # 新增代码+MCP文件工具: 执行读取并包装结果；若省略: 文件内容不会返回给 agent
    if name == "write_file":  # 新增代码+MCP文件工具: 处理 MCP 版覆盖写入工具；若省略: write_file 调用会变成未知工具
        return tool_result(run_write_file(arguments))  # 新增代码+MCP文件工具: 执行写入并包装结果；若省略: 写入结果不会返回给 agent
    if name == "create_file":  # 新增代码+MCP文件工具: 处理 MCP 版新建文件工具；若省略: create_file 调用会变成未知工具
        return tool_result(run_create_file(arguments))  # 新增代码+MCP文件工具: 执行创建并包装结果；若省略: 创建结果不会返回给 agent
    if name == "copy_file":  # 新增代码+MCP文件操作: 处理 MCP 版复制文件工具；若省略: copy_file 调用会变成未知工具
        return tool_result(run_copy_file(arguments))  # 新增代码+MCP文件操作: 执行复制并包装结果；若省略: 复制结果不会返回给 agent
    if name == "move_file":  # 新增代码+MCP文件操作: 处理 MCP 版移动文件工具；若省略: move_file 调用会变成未知工具
        return tool_result(run_move_file(arguments))  # 新增代码+MCP文件操作: 执行移动并包装结果；若省略: 移动结果不会返回给 agent
    if name == "delete_file":  # 新增代码+MCP文件操作: 处理 MCP 版删除文件工具；若省略: delete_file 调用会变成未知工具
        return tool_result(run_delete_file(arguments))  # 新增代码+MCP文件操作: 执行删除并包装结果；若省略: 删除结果不会返回给 agent
    if name == "run_powershell":  # 新增代码+workspace_tools: 处理 PowerShell 工具；若省略: 命令执行调用会变成未知工具
        return tool_result(run_powershell(arguments))  # 新增代码+workspace_tools: 执行命令并包装结果；若省略: 命令输出不会返回给 agent
    if name == "edit_file":  # 新增代码+edit_file: 处理精确文件编辑工具；若省略: edit_file 调用会变成未知工具
        return tool_result(run_edit_file(arguments))  # 新增代码+edit_file: 执行编辑并包装结果；若省略: 文件修改结果不会返回给 agent
    raise RuntimeError(f"未知工具：{name}")  # 新增代码+workspace_tools: 未知工具返回清晰错误；若省略: 拼错工具名时很难排查


def handle_message(message: dict[str, Any]) -> dict[str, Any] | None:  # 新增代码+workspace_tools: 处理单条 JSON-RPC 消息；若省略: 主循环无法响应 MCP 请求
    method = str(message.get("method", ""))  # 新增代码+workspace_tools: 读取 JSON-RPC 方法名；若省略: 无法分发 initialize/tools/list/tools/call
    request_id = message.get("id")  # 新增代码+workspace_tools: 读取请求 id；若省略: 响应无法和请求匹配
    params = message.get("params", {})  # 新增代码+workspace_tools: 读取请求参数；若省略: tools/call 无法拿到工具名和参数
    if method == "notifications/initialized":  # 新增代码+workspace_tools: 处理初始化完成通知；若省略: client 发通知时会收到不必要错误
        return None  # 新增代码+workspace_tools: notification 不需要响应；若省略: 会违反通知不带响应的习惯
    if method == "initialize":  # 新增代码+workspace_tools: 处理 MCP 初始化握手；若省略: LearningAgent 的 McpStdioClient 启动会失败
        return make_response(request_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "workspace_tools", "version": "0.1"}})  # 新增代码+workspace_tools: 返回工具能力和版本；若省略: client 不知道 server 支持 tools
    if method == "tools/list":  # 新增代码+workspace_tools: 处理工具列表请求；若省略: 模型永远看不到 workspace_tools 工具
        return make_response(request_id, {"tools": TOOLS})  # 新增代码+workspace_tools: 返回全部 workspace MCP 工具定义；若省略: LearningAgent 没有本地工作区工具 schema
    if method == "tools/call":  # 新增代码+workspace_tools: 处理工具调用请求；若省略: 模型选择工具后无法执行
        if not isinstance(params, dict):  # 新增代码+workspace_tools: 确认 params 是对象；若省略: 坏请求可能导致属性访问异常
            return make_error(request_id, -32602, "tools/call params 必须是对象。")  # 新增代码+workspace_tools: 返回标准参数错误；若省略: 用户看不到清晰失败原因
        try:  # 新增代码+workspace_tools: 捕获工具运行时错误并转换成 JSON-RPC 错误；若省略: server 可能直接退出
            return make_response(request_id, handle_tools_call(params))  # 新增代码+workspace_tools: 执行工具并返回成功响应；若省略: 工具结果不会回到 client
        except Exception as error:  # 新增代码+workspace_tools: 捕获列表、搜索或命令异常；若省略: 单次工具失败会杀死 MCP server
            return make_error(request_id, -32000, str(error))  # 新增代码+workspace_tools: 把异常转成可读 MCP 错误；若省略: agent 难以向用户解释失败原因
    return make_error(request_id, -32601, f"未知 MCP 方法：{method}")  # 新增代码+workspace_tools: 未知方法返回标准错误；若省略: 协议问题不易排查


def write_message(message: dict[str, Any]) -> None:  # 新增代码+workspace_tools: 向 stdout 写出 JSON-RPC 响应；若省略: 主循环需要重复序列化逻辑
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")  # 新增代码+workspace_tools: 写单行 JSON 并保留中文；若省略: client 的 readline 无法读取完整响应
    sys.stdout.flush()  # 新增代码+workspace_tools: 立即刷新 stdout；若省略: 响应可能停在缓冲区导致 client 超时


def run_server() -> None:  # 新增代码+workspace_tools: 运行 stdio MCP server 主循环；若省略: 脚本启动后不会处理任何请求
    for raw_line in sys.stdin:  # 新增代码+workspace_tools: 持续读取 client 发来的每一行 JSON-RPC；若省略: server 无法接收请求
        raw_line = raw_line.strip()  # 新增代码+workspace_tools: 去掉换行和边缘空白；若省略: 空白输入处理不整洁
        if not raw_line:  # 新增代码+workspace_tools: 跳过空行；若省略: 空输入会产生 JSON 解析错误
            continue  # 新增代码+workspace_tools: 继续等待下一条消息；若省略: 空行会进入解析流程
        try:  # 新增代码+workspace_tools: 捕获单条消息解析和处理错误；若省略: 一条坏消息会让 server 退出
            message = json.loads(raw_line)  # 新增代码+workspace_tools: 解析单行 JSON-RPC 消息；若省略: server 不知道请求内容
            response = handle_message(message)  # 新增代码+workspace_tools: 将消息交给协议处理函数；若省略: 请求不会被分发
        except Exception as error:  # 新增代码+workspace_tools: 捕获解析或处理异常；若省略: 坏消息会杀死进程
            response = make_error(None, -32700, str(error))  # 新增代码+workspace_tools: 返回 JSON-RPC 解析错误；若省略: client 只会看到进程异常
        if response is not None:  # 新增代码+workspace_tools: notification 不需要响应；若省略: None 会被写成无效 JSON 消息
            write_message(response)  # 新增代码+workspace_tools: 写出响应给 client；若省略: client 会一直等待结果


if __name__ == "__main__":  # 新增代码+workspace_tools: 允许脚本被 python 直接启动；若省略: mcp_servers.json 启动脚本时不会运行 server
    run_server()  # 新增代码+workspace_tools: 启动 MCP server 主循环；若省略: 脚本执行后会立即退出
